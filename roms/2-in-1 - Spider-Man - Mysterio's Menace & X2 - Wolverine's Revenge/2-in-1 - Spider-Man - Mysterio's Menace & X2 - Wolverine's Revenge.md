# 2-in-1 — Spider-Man: Mysterio's Menace & X2: Wolverine's Revenge (GBA) — Reverse Engineering Report

## 1. Target identity

| Item | Value |
|---|---|
| File | `2-in-1 - Spider-Man - Mysterio's Menace & X2 - Wolverine's Revenge.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| MD5 | `2b5e0ffa2eb716e2600282842c915fc0` |
| SHA-1 | `50c0f0531c0eef9109fbd8424b1067534582316a` |
| SHA-256 | `f980ba7a26aa6b59fddbb1badd343acd22350222f1f7a2864a46a8e3db309939` |
| Container header title | `SPIDEYMM X2` |
| Container game code / maker / version | `BX2E` / `52` / 0 |
| Header checksum byte | `0xC7` (valid) |

### Embedded GBA headers (Nintendo-logo scan)

The standard 156-byte Nintendo logo occurs at three places. Each hit is at
`header+4`, so the images and their bases are:

| Header file offset | Load base | Title (A0) | Code (AC) | Maker | Entry word |
|---:|---:|---|---|---|---|
| `0x000000` | `0x08000000` | `SPIDEYMM X2` | `BX2E` | `52` | `0xEA00002E` |
| `0x020000` | `0x08020000` | `SPIDERMAN MM` | `ASEE` | `52` | `0xEA00002E` |
| `0x800000` | `0x08800000` | `X2 WOLVERINE` | `AWVE` | `52` | `0xEA00002E` |

Image extents: the pack shell occupies `0x0`–`0x1FFFF`, Spider-Man:
`0x20000`–`0x7FFFFF`, X2: `0x800000`–`0xFFFFFF`. All three carry the same
Nintendo logo (SHA-1 `17daa0fe…b6613b48ee`) and a normal ARM crt0.

**Addressing rule used throughout:** `ROM address = 0x08000000 + file offset`.
For the X2 half that means a file offset `0x8xxxxx` is referred to as
`0x088xxxxx`; for Spider-Man, file `0x2xxxx` is `0x0802xxxx`.

---

## 2. Executive summary

The pack contains two complete games with two unrelated cheat surfaces.

**X2: Wolverine's Revenge (base `0x08800000`)** has a real, working,
in-game button-code system on the **SELECT A SLOT** screen. It is a seven-key
circular buffer gated by the L shoulder button. Five codes are registered; they
are exactly the five publicly documented Slot Select codes. The only state the
public lists do not mention is a sixth action slot (`id 2`) whose string pointer
is `NULL`: the action's reader still exists at `0x08820734`, but no input can
reach it. The “level skip / cheats / level select / acts / danger / level names”
strings are *not* a reachable menu in this pack: they belong to an unfinished
debug menu selected by RAM byte `0x020038CD` (values `0x05`, `0x0A`, `0x0B`),
and no intended input writes those values. This agrees with TCRF, which
documents those screens as memory-write-only unused content.

**Spider-Man: Mysterio's Menace (base `0x08020000`)** has a 5-character,
25-bit checksum password system. The alphabet is
`bcdfghjklmnpqrstvwxyz0123456789-` (32 symbols, stored lowercase; the game draws
capitals). The ROM validator is split into three functions that reproduce the
published checks exactly: a five-bit parity block, a difficulty mask
(`0x8208`, `0x0200`, `0x0008`), and level-consistency tests. Of the 2^25
packed values, **86,016** pass all three checks. 24 of the 25 codes collected
from the published lists (GameFAQs plus the community encoder/decoder) decode
and re-encode exactly; the 25th (`CRDT5`, “view the credits”) fails all three
checks and is either special-cased elsewhere or wrong for this revision — it is
recorded here as unverified.

The one gap in this engagement is that the Spider-Man **password entry UI**
could not be reached by intended input in this 2-in-1 build. The screen and its
input loop exist (`0x08023FE4`, `0x08021868`), but the menu action that opens
them (`action 7`, returned for the Select key at `0x0803DE34`) is never
returned. The menu engine that contains that action is not the engine used by
the pack’s menus: on the main menu, difficulty menu, in-game pause, four-item
level/pause menu, and save/load screens, Select is consumed as *cursor down*
first, and the cursor moves. This is consistent with a deliberate removal of
the password entry from the 2-in-1 build (the hint text, validator, display
screen and alphabet were all left in place). The password model and generated
codes are therefore ROM-verified but not keypad-entered; this is stated
explicitly in §7 and §8 rather than rounded up. The standalone `ASEE` release
may still expose the same screen, but that ROM was not part of this target.

The in-game verification that *was* obtained is the X2 code system: the
public “100 Lives” code was entered on SELECT A SLOT and the HUD changed from
`x8` to `x99` (screenshot `shots/26_hud2.png`, §7). An undocumented trigger
string for the same branch (a two-Left prefix before the seven Rights) was also
accepted, which shows the public lists describe only the shortest trigger, not
the whole input space.

---

## 3. How to reproduce

### Emulator and keymap

mGBA SDL 0.10.5 under Xvfb `:115`, 3× scale:

```bash
Xvfb :115 -screen 0 1280x900x24 &
DISPLAY=:115 openbox &
cd "roms/2-in-1 - Spider-Man - Mysterio's Menace & X2 - Wolverine's Revenge"
DISPLAY=:115 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 \
  "2-in-1 - Spider-Man - Mysterio's Menace & X2 - Wolverine's Revenge.gba" &
```

The mGBA SDL default keymap was confirmed by disassembling
`mSDLInitBindingsGBA` in `/usr/games/mgba`:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `Backspace` |
| D-pad | arrow keys |

Use 120–200 ms holds; the menus debounce.

### X2 button codes (reproducible, verified)

1. Boot the pack; choose **X2: Wolverine's Revenge** on the pack shell
   (Right, A).
2. At the title, press Start; at SELECT A SLOT (the slot/file screen):
3. **Hold L (`a`)** and press **Right seven times**. The LIVES field in the
   slot preview changes from `8` to `99` immediately (the code writes 100; the
   preview shows the post-decrement value). Screenshot: `shots/26_hud2.png`
   (in-level HUD shows `x99` after starting the slot).
4. The other four codes are entered the same way (hold L, then the sequence in
   §6).

An undocumented trigger for the same 100-lives branch: hold L, press
**Left, Left, Right, Right, Right, Right, Right, Right, Right** (the two Lefts
fall out of the seven-key window). Accepted; same effect.

### Spider-Man password path

Intended path, as documented by the in-game hint
(`0x083A47B0`: “dinner time? press select in-game for your password.”), is
Select in-game. In this build that opens the **status/equipment screen**, not a
password screen; the password screen code path is documented in §5 but is not
reachable through the menus tested (§7, negative result). The published
passwords can be checked against the ROM model with the supplied script
`bin/smm_pw.py`; no ROM patching is required.

---

## 4. Address map

### 4.1 X2 half (base `0x08800000`)

| Address | Meaning |
|---:|---|
| `0x0880813C` | Per-frame cheat effects: flag1 → lives = 100; flag3 → OR six power-up bits |
| `0x088081C4` | Button recorder: appends one character to the 7-byte ring buffer, gated by L |
| `0x08807F94` | Cheat checker: builds the chronological 7-char window, compares against six registered strings |
| `0x0880829C` | Cheat object initializer; registers the five live strings |
| `0x0880820C` | `obj->slot[id] = string_ptr` (id×4) |
| `0x08808218` | Read flag byte `obj[0x1C + id]` |
| `0x0880022C` | `strcmp` trampoline into IWRAM (`0x03000570`) |
| `0x0200003C` | RAM pointer to the cheat object (allocated once at boot) |
| `0x02003D14` | Cheat object in EWRAM (observed live) |
| `0x02000650` | Held-key state (active-high); `+0` held, `+4` newly pressed |
| `0x02000651` | Bit 1 = L held → recorder gate |
| `0x08831D08` | Registered sequence strings (`rlrlrlr`, `rrrrrrr`, `rudrlss`, `sluddud`, `dudduds`) |
| `0x08835E98` | Debug-menu labels (`level skip`, `cheats`, `level select`, `act 1..8`, `danger 1..8`, level names) |
| `0x0883D7C0` | Level-skip menu descriptor (`next section`, `slow motion`, `super jump`, `power up!`) |
| `0x0883D7D0` | Level-skip item labels |
| `0x020038CD` | Debug menu selector byte (TCRF: `05` select-controls, `0A` level skip, `0B` sleep) |

Cheat object layout (all fields confirmed live at `0x02003D14`):

```
+0x00  void* slot[0]      (NULL)
+0x04  char* slot[1]      -> "rrrrrrr"      action 1 (100 lives)
+0x08  void* slot[2]      (NULL)            action 2 (orphan)
+0x0C  char* slot[3]      -> "rlrlrlr"      action 3 (power-ups)
+0x10  char* slot[4]      -> "rudrlss"      action 4 (regeneration)
+0x14  char* slot[5]      -> "sluddud"      action 5 (double jump)
+0x18  char* slot[6]      -> "dudduds"      action 6 (invincibility)
+0x1C  u8 flag[0]         (unused)
+0x1D  u8 flag[1]         100 lives
+0x1E  u8 flag[2]         orphan action
+0x1F  u8 flag[3]         all power-ups
+0x20  u8 flag[4]         regeneration
+0x21  u8 flag[5]         infinite double jump
+0x22  u8 flag[6]         invincibility
+0x24  u32 write index (0..6)
+0x28  char window[7]     initial "-------"
+0x2F  NUL
```

### 4.2 Spider-Man half (base `0x08020000`)

| Address | Meaning |
|---:|---|
| `0x08023600`–`0x080237AA` | Five parity equations (bits 1,11,20,4,3→0; 2,7,20,8,15→5; 10,16,20,4,15→18; 0,12,17,23,9→21; 5,18,19,6,3→24) |
| `0x0802474C` | `check_levels` (bits 23,22,6,8,13,4,14) |
| `0x08024798` | `check_difficulty` (`n & 0x8208` ∈ {`0x8208`,`0x0200`,`0x0008`}) |
| `0x080237EC` | Full decode/apply: checks, decodes fields into the progress object, stores difficulty at `+0x94`, secondary value at `+0x98` |
| `0x080247C0` | Extracts the 2-bit difficulty/selector from `n` |
| `0x08023C58` | Secondary field extractor |
| `0x08023FE4` | Password display screen (5 chars from the current progress value) |
| `0x08021868` | Password editor loop (menu ids 5..8 = cancel / file 1..3) |
| `0x08021768` | Apply password to a file slot; calls `0x080237EC` |
| `0x0803DE34` | Menu handler: Select (bit 2) requests action 7 |
| `0x08039…` / menu walk | Title, main, difficulty, save/load, pause, status |
| `0x0839BCF8` | Password alphabet ASCII: `bcdfghjklmnpqrstvwxyz0123456789-` |
| `0x083A4030` | UI string `password: ` |
| `0x083A3F9C` | UI string `@ - accept   & - backspace` |
| `0x083A3E14` | UI string `password` (unused main-menu label in this build) |
| `0x083A47B0` | UI hint: `dinner time?  press select in-game for your password.` |
| `0x083A5360` | Text-ID pointer table base (id 0 = NULL, id 1 = `new game`, …, id 39 = `password: `) |

---

## 5. Algorithm

### 5.1 X2 button codes

The engine turns every handled button into one character and calls
`0x088081C4(obj, char)`:

| char | Button |
|---|---|
| `a` | A |
| `b` | B |
| `s` | Select |
| `t` | Start |
| `r`/`l`/`u`/`d` | Right/Left/Up/Down |
| `R`/`L` | shoulder buttons |

`0x088081C4` first checks `0x02000651 & 2`, i.e. **L must be held**. If it is,
the character is stored at `obj+0x28+index`, index increments modulo 7, and
`0x08807F94` runs.

`0x08807F94` copies the seven bytes starting at `index` in chronological order
into a NUL-terminated stack buffer and compares that buffer with each non-NULL
`slot[i]` string using `strcmp` (`0x0880022C`). On a match it sets
`obj[0x1C+i] = 1`. Consequences:

* the public “hold L, press X” notation is exact: the L press itself is in the
  buffer but is shifted out by the following seven keys;
* **any prefix is allowed**; only the last seven characters matter, so there are
  infinitely many input strings per action, not one;
* uppercase `L`/`R` inside the seven-key window never match, because all five
  registered strings are lowercase.

`0x0880813C` then consumes the flags:

* flag 1: `*(u32*)(0x02000084 + 0x38) = 100` (lives);
* flag 3: sets bits 1,2,4,8,16,32 at `*(0x02000090)+0x3C` (six power-ups);
* flags 4/5/6: polled at `0x088249FE`, `0x088207F6`, `0x08813602`
  (regeneration / double-jump reset / invincibility).

Flag 2 has a reader at `0x08820734` but its slot is `NULL`, so no input sets it.

### 5.2 Spider-Man password

Alphabet (32):

```
index  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
char   b  c  d  f  g  h  j  k  l  m  n  p  q  r  s  t
index 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31
char   v  w  x  y  z  0  1  2  3  4  5  6  7  8  9  -
```

Packing is little-endian 5 bits per character:

```
n = sum(index(c[i]) << (5*i)), i = 0..4
```

The ROM display loop at `0x08024036` performs the inverse
(`alphabet[(n >> 5*i) & 31]`), and the editor/apply path reads the same 25-bit
value. The three validators, reproduced exactly:

```
check_secondary(n):
  b0  == b1 ^ b11 ^ b20 ^ b4 ^ b3
  b5  == b2 ^ b7  ^ b20 ^ b8 ^ b15
  b18 == b10^ b16 ^ b20 ^ b4 ^ b15
  b21 == b0 ^ b12 ^ b17 ^ b23 ^ b9
  b24 == b5 ^ b18 ^ b19 ^ b6 ^ b3

check_difficulty(n):
  (n & 0x8208) in {0x8208, 0x0200, 0x0008}

check_levels(n):
  if b23 and (n & 0x400110) != 0x400000: reject
  if b22 and b6: reject
  if !b8 and !b13: reject
  if !b4 and !b14: reject
```

Fields decoded by `0x080237EC` (bit → field, `^1` = inverted):

| Field | Bit(s) |
|---|---|
| belt | 1 |
| left wrist container | 2 |
| right wrist container | 7 ^ 1 |
| thermal suit | 10 ^ 1 |
| armor suit | 11 ^ 1 |
| electric suit | 12 ^ 1 |
| symbiote suit | 16 |
| web compressor | 17 |
| fluid upgrade | 19 |
| heavy impact | 20 |
| difficulty (0 easy, 1 normal, 2 super hero) | 3^1 (bit0), 9^1 (bit1) |
| empire metals | 14 |
| downtown | 6 ^ 1 |
| pier 54 | 13 |
| chemcorp | 4 ^ 1 |
| nightclub | 22 |
| museum | 8 ^ 1 |
| amusement park | 23 |

`encode()` is the exact inverse, setting the five parity bits in ROM order after
the payload bits.

---

## 6. Tables

### 6.1 X2 registered button codes

| Action | id | Trigger after holding L | Effect |
|---|---:|---|---|
| 100 lives | 1 | `r r r r r r r` | lives = 100 |
| (orphan) | 2 | none (slot NULL) | flag exists; reader `0x08820734`, no trigger |
| All power-ups | 3 | `r l r l r l r` | six power-up bits |
| Regenerate with claws extended | 4 | `r u d r l s s` | flag 4 |
| Infinite double jump | 5 | `s l u d d u d` | flag 5 |
| Invincibility | 6 | `d u d d u d s` | flag 6 |

All five strings are at `0x08831D08`/`D10`/`D18`/`D20`/`D28`; they match the
public GameFAQs Slot Select list exactly.

### 6.2 Spider-Man published codes vs. the ROM model

`bin/smm_pw.py` checks every published code. 24 pass and round-trip through
`decode`/`encode`:

`080ZG, 4-KMD, 7V84Z, C0-LQ, CV-L1, HV37K, JV31-, JV33R, JV37H, RV8WJ,
SP1DY, TW3-K, TW3-R, VV-BG, W70ZZ, W7HV1, W7HZZ, Z787K, ZV3Z0, ZV7Z2,
ZV87K, TB31T, TB31H, TB370`

`CRDT5` is published as “view the credits” but fails the parity, difficulty and
level checks (`n = 0x1A789A1`). It is not the normal 25-bit format or is
special-cased in a branch not found by a literal scan; it is **not** claimed as
verified.

### 6.3 Generated novel codes (not on GameFAQs/TCRF/VGChartz)

| Code | Fields | Why novel |
|---|---|---|
| **`TB778`** | difficulty 2 (Super Hero), all levels complete, all upgrades, belt + both wrists, **electric suit off, symbiote suit off** | no published code has Super Hero + all levels + no electric suit; `TB370` keeps the electric suit and `SP1DY` does not complete the levels |
| **`L03-T`** | difficulty 0 (Easy), all levels complete, all three suits + symbiote, all upgrades, **no belt and no wrist containers** | published Easy all-levels codes (`TW3-K`/`TW3-R`) include all three containers |

Rejection examples (format cannot express these):

| Test | Value | Result |
|---|---|---|
| Single-bit corruption of `SP1DY` | `TP1DY` | rejected by `check_secondary` (bit 0 parity) |
| Difficulty mask violation | `BBBBB` (`n & 0x8208 = 0`) | rejected by `check_difficulty` |
| Level-consistency violation | any `n` with bit 8 = bit 13 = 0 | rejected by `check_levels` |

## 6b. Enumeration

### X2

* **Space:** seven recorded key characters over the 10 accepted symbols
  (`a b s t r l u d R L`) = 10^7 = **10,000,000 windows**; only **5**
  registered strings are live, plus one orphan slot that no window can match
  (`NULL`). Therefore the action set is exactly 5, not 6.
* **Novel input:** the public lists give one trigger per action; the checker
  matches only the last seven characters, so any prefix works. Verified
  undocumented form of the 100-lives branch:
  **hold L, press Left, Left, Right×7**. The prefix scrolls out of the window and
  the branch fires (HUD `x99`, `shots/26_hud2.png`).
* **Bounds by rejection:** a window that matches none of the five strings
  (e.g. hold L, press Up×7) leaves all flags zero and the LIVES field at `8`.
  The orphan id 2 cannot be triggered because its string pointer is `NULL`;
  this is a *structural* negative, not a missing test.
* **Debug menus:** entries enumerated from the ROM: root labels
  `level skip`, `cheats`, `level select`; level-select lists `act 1..8`,
  `danger 1..8`, and the nine level names (`canadian wilderness` … `magneto's
  lair`); level-skip entries `next section`, `slow motion`, `super jump`,
  `power up!`. Selector byte `0x020038CD`; documented values `0x05`, `0x0A`,
  `0x0B` (TCRF). No intended input writes it; every menu in both halves was
  walked and no debug entry appeared. This is the bounded negative for the
  “cheat menu” lead.

### Spider-Man

* **Space:** 5 symbols × 5 bits = **2^25 = 33,554,432** packed values.
  Parity (5 bits) + difficulty mask + level consistency leave **86,016**
  accepted values (0.256%). The alphabet has 32 symbols; the keypad cannot
  express any symbol outside `bcdfghjklmnpqrstvwxyz0123456789-`.
* **Novel values:** `TB778` and `L03-T` above; both pass all three ROM checks
  and are absent from every published list checked.
* **Bounds by rejection:** `TP1DY` (one bit flipped from `SP1DY`), `BBBBB`
  (difficulty mask), and any value with bits 8 and 13 both zero are rejected by
  the reimplemented ROM checks. The *entry UI* is the limiting factor; see §7.

---

## 7. Validation evidence

### Observed (emulator)

* Booted the pack in mGBA on `:115`; the choose-a-game shell shows both covers;
  both halves boot (Spider-Man: Marvel/VV/Mysterio; X2: Activision/X2 title).
* X2: SELECT A SLOT screen, slot preview `LIVES: 8`.
* X2: hold L + Right×7 on SELECT A SLOT → slot preview jumped; starting the
  level shows HUD **`x99`** (`shots/26_hud2.png`). This is the public
  “100 Lives” code.
* X2: hold L + Left,Left,Right×7 also accepted (undocumented prefix).
* X2: all normal menus walked: title, slot select, select mode (Easy/Normal/
  Super Hero), in-game pause (Resume/Sound/Quit), power-ups panel, “GAME
  PAUSED” screen, level-complete/pause screen (Replay Level/Save Game/Return to
  Map/Quit Game), map screen, save/load screens, music/sound submenu. No cheat
  menu, no level skip, no character/act select.
* X2: **LEVEL SELECT** (acts 1–8 for the current level) *is* reachable from
  Start during the level-intro/“REVENGE AWAKENING” splash and lets the player
  warp between acts of that level. It is not the debug “level skip” screen of
  TCRF (which is titled LEVEL SKIP and has NEXT SECTION/SLOW MOTION/SUPER
  JUMP/POWER UP!). Screenshot `shots/10_act3.png`.
* Spider-Man: main menu, difficulty, map, in-level status (Select), pause,
  save/load screens walked; Select opens the status/equipment panel in-level
  and the SAVE GAME screen on the map, never a password keypad.
* Spider-Man: pressing Select on every menu moves the cursor down, including
  the difficulty menu, the four-item pause menu, and the save/load screens.

### Derived (instruction-level)

* X2 recorder/checker/effects, object layout, five sequence strings, orphan id 2,
  L-gate, and the “last seven characters only” semantics.
* X2 debug menus are data + a RAM selector; no writer of `0x020038CD` was found
  in code reachable from input. TCRF independently reports they are memory-write
  only (`020038CD:05/0A/0B`).
* Spider-Man password alphabet, packing, parity, difficulty and level checks,
  field decode, and the 86,016-value count.
* Spider-Man menu action 7 (password screen) is requested by Select in
  `0x0803DE34`, but every observed menu consumes Select as cursor-down first;
  the password screen is therefore not reachable in this build by the tested
  input paths. This is a negative about the *tested menu space*, and it is why
  the generated Spider-Man codes are ROM-validated but not keypad-entered.

### Inferred

* The orphan X2 id 2 is a removed sixth cheat: its flag reader survives at
  `0x08820734` but its string slot was never populated.
* The 2-in-1 pack does not add a cheat menu of its own; the shell only selects
  between the two unchanged images.
* `CRDT5` is likely a special-cased credits password or a code for another
  revision; it is not part of the normal 25-bit space.

---

## 8. Unknowns

* **Spider-Man password entry UI:** not reached. The code path exists
  (`0x08023FE4`/`0x08021868`) and the hint tells the player to press Select
  in-game, but Select is consumed as cursor-down on every menu tested. A
  different build, a button combination, or a later-game save state may expose
  it; this pack’s tested paths do not. The generated codes `TB778` / `L03-T`
  are consequently ROM-validated, not keypad-confirmed.
* **`CRDT5`:** rejected by the normal validator; the credits trigger was not
  isolated.
* **X2 debug menu selector:** the exact writer of `0x020038CD` was not located
  statically (the struct has no absolute literal). The negative rests on the
  full menu walk, the absence of any in-game label, and TCRF’s memory-write
  documentation.
* X2 flag 2’s effect: reader at `0x08820734` writes a value from `0x083EA40`
  into `+0xA8`; the semantic name of the removed action is unknown.

---

## 9. Tooling

All scripts are in `/tmp/opencode/spidermm/bin/` (not part of the repo):

| Script | Use |
|---|---|
| `scan_headers.py` | Nintendo-logo scan / embedded header dump |
| `ptrscan.py` | 32-bit pointer search (with Thumb-bit variant) |
| `ldrlit.py` | fast Thumb PC-relative literal-load search |
| `blscan.py` | Thumb BL target scan |
| `scan_btn.py` | button-mask pattern search |
| `smm_pw.py` | Spider-Man password model: check/decode/encode/enumerate |
| `keys.py` | xdotool key helper for `:115` |
| `dbg_driver.py` | pty driver for mGBA’s `-d` command-line debugger |

Screenshots are in `/tmp/opencode/spidermm/shots/`; the key ones are
`00_boot_000.png` (shell), `05_x2_menu_g.png` (SELECT A SLOT),
`26_hud2_g.png` (100-lives HUD `x99`), `10_act3_g.png` (reachable in-level act
select), `41_sm_pw_g.png` (Spider-Man status panel), `85_save_g.png`
(save screen), `94_4menu_g.png` (four-item pause).

No ROM, extracted art, music or text is redistributed here; only addresses,
algorithms, hashes and generated codes are published.

---

## 10. Bottom line

* **X2 in-game cheats:** five working Slot Select codes, enumerated with their
  action ids, effects, string addresses and the L-gate; verified 100 Lives in
  the emulator; the sixth (id 2) is structurally unreachable.
* **X2 hidden/debug menu:** exists only as unused data/selector; no intended
  input path in the 2-in-1 build. The reachable “LEVEL SELECT” from the level
  intro is a different, working act-warp screen, not the TCRF LEVEL SKIP menu.
* **Spider-Man passwords:** algorithm fully recovered (alphabet, 25-bit packing,
  five parity equations, difficulty mask, level checks), 86,016 valid values,
  24/25 published codes verified, two novel codes generated (`TB778`, `L03-T`),
  rejection bounds proved offline. Entry through the retail keypad was not
  reachable in this pack and is reported as the one open item.
