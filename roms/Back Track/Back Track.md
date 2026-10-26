# Back Track (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Back Track/Back Track.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `BACKTRACK` (0xA0, space/NUL padded) |
| Game code | `ABKE` |
| Maker code | `5M` |
| Software version | `0x00` |
| Entry word | `0xEA00002E` |
| Nintendo logo | valid, at file `0x000004` (header base `0x000000`) |
| Embedded GBA headers | exactly **one** (whole-file scan for the 156-byte logo → one hit at `0x4`) |
| MD5 | `de6b60ee6f0de4f2f7a7fc7c8f4a1d9e` |
| SHA-1 | `be97ade09df06291e029beeffbe0aacf21db9168` |
| SHA-256 | `8878bfc3c6c5eacfc0c9e2a90d7c97068046376b93c50a5a0d5d1ec6d04eef94` |
| Save hardware | EEPROM (`EEPROM_V122` at file `0x193EC`); mGBA created a 512-byte `.sav` |

Header integrity note (observed): the stored complement byte at `0xBD` is `0x36`,
but the check over `0xA0..0xBC` yields `0x32`; `0xBE..0xBF` is `0x0000`
(reserved, as expected). The ROM boots and behaves normally, so the 4-byte
complement discrepancy is cosmetic — most likely the dump's header was touched
(tool/region patch) rather than the body being corrupt.

All addresses below are **file offset + 0x08000000 = ROM address**.

## 2. Executive summary

Back Track contains a developer console disguised as a DOS boot screen
(`Welcome to BSBODSOM / DOS Version 0.9Beta`). It is entered from the in-game
pause menu with a seven-button sequence, then asks for a password on a
letter-picker screen (A–Z, 1–17 characters). Every accepted string is compared
with `strcmp` against a small literal table; there is no checksum and no
generator.

The table has **15 entries split across two mutually exclusive contexts**,
selected by the mode argument of the console function (`0x0800E768`):

* **Cheat console** (`mode = 255`, opened by `Select, L, Right, B, L, R, Left`
  in the pause menu) — **11 commands**: `TI, GOD, MON, AMMO, WEAP, KEY, FAIL,
  ARM, HEA, FRE, COOR`.
* **In-level computer** (any other mode, i.e. the terminals found in the
  levels) — **4 commands**: `PASSWORD, JAG, VINCE, JV`.

Nine of the eleven cheat-console commands are the well-known published
passwords. **`TI` and `FAIL` are not on GameFAQs, GameSpot, jeuxvideo.com,
CodeTwink, Almar's Guides or any other published list found**, and both are
accepted by the retail ROM:
`TI` turns on a hidden numeric debug read-out in the top-left of the HUD;
`FAIL` writes `0x1FFF` to the level failsafe word.

The in-level set adds two more unpublished strings: `PASSWORD` (unlocks a
door) and `JV` (a third "secret portal", alongside the published `JAG` and
`VINCE`). They are gated off in the cheat console and could not be exercised
in-game here (see §8).

Bounds were proven in the emulator: an unknown string (`ZZZ`), a valid string
with one extra character (`GODX`), and a maximum-length string are all
rejected with no state change, and the picker physically caps input at 17
characters.

## 3. How to reproduce

### Emulator

```bash
Xvfb :152 -screen 0 1024x768x24 &
DISPLAY=:152 openbox &
DISPLAY=:152 SDL_AUDIODRIVER=dummy mgba -3 "Back Track.gba"
```

mGBA 0.10.5 (SDL). Default keymap: **A = `x`**, **B = `z`**, **L = `a`**,
**R = `s`**, **Start = `Return`**, **Select = `BackSpace`**, D-pad = arrows.
Hold 60–150 ms per press; a 10 ms tap is missed.

### Reaching the console

1. Boot. The intro space fly-by runs ~15 s, then the **Single Player Menu**
   appears (`Normal Game / Hard Game / Load Game / Game Options`,
   "Press SELECT for Multi-Player Menu").
2. `A` on **Normal Game**, wait ~6 s for Level 1.
3. `Select` → the pause **Game Menu**.
4. Type the sequence **L, Right, B, L, R, Left** (`a`, `Right`, `z`, `a`, `s`,
   `Left`). The screen becomes the **BSBODSOM DOS 0.9Beta** console.
5. `A` on `CLI'Password Required'` → **Enter Password:**.
6. Type a code: `Up`/`Down` select a letter (held, ~10 changes/s), `Right`
   appends the current letter, `Left` deletes the last letter, `A` submits,
   `Select` cancels.
7. `Down`, `A` on `Shut Down Computer` returns to the game with the effect
   applied.

`game.ss1` (savestate, Single Player Menu) makes steps 1–2 a single load.

### Screens walked

Every menu reachable from the title was visited and screenshotted (Phase 2):

* intro/attract fly-by → **Single Player Menu**: `Normal Game`, `Hard Game`,
  `Load Game`, `Game Options`;
* **Load Game**: `Game Pak Load-Save: -Empty-`, `Temp Load-Save: -Empty-`
  (B/Select to back out);
* **Game Options**: `Brightness`, `Rotation Speed`, `In Game Music On!`;
* `Select` → **Multi Player Menu**: `Death Match`, `Matrix Assault`,
  `Current Stats`, `Game Options`;
* `Death Match` → character select (`Choose a player`, `Player Type`, `Weapon`,
  `Weight`, `Height`, "SELECT to cancel", "START or A Button to connect");
* **Current Stats**: rating, `Total Wins/Losses/Frags/Times Fragged`,
  `. Clear Stats`, `. Enter New Name`, `X Exit Stats Screen`;
* **Enter New Name** and the `Type 'OK' confirm clear:` screen — both are the
  same editor (`0x08009FAC`) as the password prompt, i.e. text entry is used
  for names and for the `OK` clear-confirmation as well;
* in gameplay, `Select` → **Game Menu**: `Load-Save Games`, `Brightness`,
  `Rotation Speed`, `In Game Music On!`;
* the hidden **BSBODSOM console**: `CLI'Password Required'`,
  `Shut Down Computer`, and the static `: RUN HELLO` prompt line;
* the **Enter Password:** picker itself.

No other text-entry field or hidden menu entry exists in these screens; the
`Game Options`/`Load Game` screens contain no input fields. This matches the
static census: the editor `0x08009FAC` is called from exactly **three** sites —
`0x0800ECF4` (console password), `0x08011852` (`Type 'OK' confirm clear:`) and
`0x080118EA` (`Enter Name:`) — i.e. the three text-entry screens listed above
and nothing else.

### Codes tested

All 11 cheat-console strings were entered through the on-screen picker and
their RAM writes and/or HUD effects recorded (§6, §6b). Published codes
`HEA, AMMO, KEY, COOR, FRE, WEAP, GOD, ARM, MON` all work as advertised.
`JAG, VINCE, JV, PASSWORD` are rejected by the cheat console because of the
mode gate (§5.4).

Every published string was also verified against the ROM bytes: `HEA AMMO KEY
COOR FRE WEAP GOD ARM MON` (GameFAQs/GameSpot/jeuxvideo) and `JAG VINCE`
(GameFAQs "Unlocking Level 10") are all present literally in the table at
`0x18CB0..0x18D1F`, so none of them is a fan invention or a typo.

## 4. Address map

### Code

| Address | Role |
|---|---|
| `0x08009FAC` | Text-entry editor (name / confirm-clear / password). Args: `r0` = header mode (0 = "Enter Name:", 2 = "Type 'OK' confirm clear:", else "Enter Password:"), `r1` = max length, `r2` = buffer, `r3` = initial length |
| `0x0800A0E4`–`0x0800A21C` | Editor input loop (Up/Down letter, Right append, Left delete, A/Start accept, Select cancel) |
| `0x0800E768` | **Console/terminal function**. `r2` = mode: `255` = cheat console, otherwise in-level computer |
| `0x0800E7BE` | `mode 255 → r6 = 0x80` (the cheat-console flag) |
| `0x0800ECE6`–`0x0800ECF4` | Password prompt: `editor(x=1, maxlen=17, buf=0x02010B90, len=0)` |
| `0x0800ECFC` | Gate: `if (r6 & 0x80) → 0x0800EE74` (skips `PASSWORD/JAG/VINCE/JV`) |
| `0x0800ED12` | `strcmp(buf, "PASSWORD")` |
| `0x0800ED70` | `strcmp(buf, "JAG")` |
| `0x0800EDB8` | `strcmp(buf, "VINCE")` |
| `0x0800EE00` | `strcmp(buf, "JV")` |
| `0x0800EE60` | `"Access Denied!"` path for the in-level set |
| `0x0800EE74` | `strcmp(buf, "TI")` |
| `0x0800EE94` | `strcmp(buf, "GOD")` |
| `0x0800EEB8` | `strcmp(buf, "MON")` |
| `0x0800EED4` | `strcmp(buf, "AMMO")` |
| `0x0800EF04` | `strcmp(buf, "WEAP")` |
| `0x0800EF24` | `strcmp(buf, "KEY")` |
| `0x0800EF44` | `strcmp(buf, "FAIL")` |
| `0x0800EF64` | `strcmp(buf, "ARM")` |
| `0x0800EF80` | `strcmp(buf, "HEA")` |
| `0x0800EF9C` | `strcmp(buf, "FRE")` |
| `0x0800EFBC` | `strcmp(buf, "COOR")` |
| `0x080184E8` | `strcmp` (byte-exact, case-sensitive) |
| `0x08009D40`–`0x08009DBA` | Pause-menu **button-sequence state machine** |
| `0x08009DBA` | `bl 0x0800E768` with `r0=0, r1=0, r2=255` (open cheat console) |
| `0x08004096` | `FRE` reader (bit 3) |
| `0x0800BD78` | `MON` reader (bit 2) |
| `0x0800CBAA` | `TI` reader (bit 0), draws the numeric read-out |
| `0x0800CBD6` | `COOR` reader (bit 4) |
| `0x0800DB1E` | `GOD` reader (bit 1), zeroes incoming damage |

### Strings (literals)

| Offset | String | Used as |
|---|---|---|
| `0x1809F0` | `Welcome to BSBODSOM` | console banner |
| `0x18A04` | `DOS Version 0.9Beta` | console banner |
| `0x18A18` | `Enter Name:` | editor mode 0 |
| `0x18A24` | `Type 'OK' confirm clear:` | editor mode 2 |
| `0x18A40` | `Enter Password:` | editor password mode |
| `0x18A54`/`70`/`84`/`AA0` | `UP, DOWN, LEFT, and RIGHT` / `to select letters.` / `Press A Button to accept.` / `Press SELECT to cancel.` | help text |
| `0x18AB8`/`AC4`/`AD4` | `Save Game` / `Restart Game` / `Quit Game` | pause menu |
| `0x18C70` | `PASSWORD` | level-computer command |
| `0x18C7C` | `Door is now unlocked!` | PASSWORD response |
| `0x18C94` | `Function Already Accessed!` | repeat of a set-once command |
| `0x18CB0` | `JAG` | level-computer command |
| `0x18CB4` | `Secret portal Opened!` | JAG/VINCE/JV response |
| `0x18CCC` | `VINCE` | level-computer command |
| `0x18CD4` | `JV` | level-computer command |
| `0x18CD8` | `Access Denied!` | in-level rejection |
| `0x18CE8` | `TI` | cheat-console command |
| `0x18CEC` | `GOD` | cheat-console command |
| `0x18CF0` | `MON` | cheat-console command |
| `0x18CF4` | `AMMO` | cheat-console command |
| `0x18CFC` | `WEAP` | cheat-console command |
| `0x18D04` | `KEY` | cheat-console command |
| `0x18D08` | `FAIL` | cheat-console command |
| `0x18D10` | `ARM` | cheat-console command |
| `0x18D14` | `HEA` | cheat-console command |
| `0x18D18` | `FRE` | cheat-console command |
| `0x18D1C` | `COOR` | cheat-console command |

### RAM

| Address | Meaning |
|---|---|
| `0x02010B90` | Text buffer, 17 chars + NUL (also reused as the decimal format buffer) |
| `0x02010FA0` | Key-state array, 10 × u16, indexed by KEYINPUT bit (A,B,Select,Start,Right,Left,Up,Down,R,L). `0xFF` = held, `0x01` = released-this-frame, `0x00` = idle/consumed |
| `0x0200EA90` | Player struct: `+0x0E` armour (u16), `+0x16` health (u16), `+0x26,+0x28,+0x2A,+0x2C,+0x2E,+0x30` six ammo pools (u16), `+0x34` weapon bitmask (u16), `+0x36` keycard mask (u16), `+0x38` master card (u16) |
| `0x0200EBD0` | Level/console struct: `+0x32` failsafe word (u16), `+0x3C` secret/portal flags (u16) |
| `0x02010C30` | Debug flag word (u16): bit0 `TI`, bit1 `GOD`, bit2 `MON`, bit3 `FRE`, bit4 `COOR` |
| `0x02014A08` | Pointer to the level data block; door/portal entries at `+0xDB` (JAG), `+0xE7` (VINCE), `+0x2117` (PASSWORD), `+0x21E1` (JV) |

Independent corroboration: the addresses the ROM's own `AMMO`/`WEAP`/`KEY`
write (`0x0200EAB6..C0`, `0x0200EAC4`, `0x0200EAC6`) are exactly the addresses
used by the published CodeBreaker "Infinite Ammo / Have All Weapons / Have All
Cards" codes, which confirms the struct layout from a second direction.

### Recon counts (Phase 1)

`strings -t x -n 4 Back Track.gba` → **56,944** printable runs. Keyword scan
(case-insensitive): `password` 4, `secret` 2, `unlock` 6, `level` 4, `select`
6, `menu` 7, and **`cheat` 0, `code` 0, `debug` 0**. Classification of the
`password` hits: `0x18A40` `Enter Password:` (the picker header), `0x18BA0`
` . CLI'Password Required'` (console menu item), `0x18C70` `PASSWORD` (a
command literal), and `0x2ED8C3` `%'Password is password, oh Nelly, I'm` —
story/credits text, **not** a code. The `secret` hits are `0x18CB4`
`Secret portal Opened!` (command response) and `0x2ED60E` `Secret Base on Dark
Side of` — again story text. The only real code table is the fifteen literals
in the string bank at `0x18CB0..0x18D1F` (interleaved with their response
messages, which is why the strings are not contiguous); no ASCII password
alphabet exists anywhere in the ROM (the picker generates A–Z itself).

## 5. Algorithm

### 5.1 Entry (button sequence)

The pause-menu handler contains a tolerant 6-state machine
(`0x08009D40`–`0x08009DBA`). It compares *released-this-frame* (`== 1`) keys
against a growing state:

```
state = 0
on L      : state = 4 if state == 3 else 1
on Right  : state = 2 if state == 1 else state - 1
on B      : state = 3 if state == 2 else state - 1
on R      : state = 5 if state == 4 else state - 2
on Left   : if state == 5: state = 0; open_console(mode = 255)
```

so `L, Right, B, L, R, Left` is required; each wrong press walks the state
back rather than resetting it. `Select` is only the key that opens the pause
menu in the first place.

There is **no button-mask table** anywhere in the ROM: searching for the
sequence as `u16` masks (`0x0004, 0x0200, 0x0010, 0x0002, 0x0200, 0x0100,
0x0020`), as active-low masks, as one byte per press, and as bit indices
(`2,9,4,1,9,8,5`) returns nothing. The "table" is this chain of per-press
comparisons at `0x08009D40..0x08009DB8`.

### 5.2 Letter picker

* Alphabet is exactly `A`–`Z` (0x41–0x5A). Up saturates at `Z`, Down at `A`;
  no lowercase, digits or punctuation are reachable from the password prompt
  (space 0x20 is stored internally as 0x5B and is never reachable by
  incrementing from `Z`).
* Length 1–17; `Right` copies the current last character and appends it
  (`0x0800A184` append path, bounds-checked against `maxlen`), `Left` removes
  the last character while length > 1.
* `A`/`Start` accept, `Select` cancels — but the caller **ignores the return
  value** and compares the buffer either way, so cancelling a non-empty string
  still validates it.
* The string is NUL-terminated in place; with `r3 = 0` the editor seeds
  `buffer[0] = 'A'` and length 1, which is why every prompt starts on `A`.

### 5.3 Validation

```
cheat = (mode == 255)                    ; console entry puts 0x80 in r6
buf = prompt_letters(maxlen = 17)        ; 0x0800ECE6
if !cheat:                               ; 0x0800ECFC tests r6 bit 7
    if strcmp(buf, "PASSWORD") == 0: unlock_door();            return
    if strcmp(buf, "JAG")      == 0: secret_portal(bit 1, 0xDB);  return
    if strcmp(buf, "VINCE")    == 0: secret_portal(bit 2, 0xE7);  return
    if strcmp(buf, "JV")       == 0: secret_portal(bit 3, 0x21E1);return
    print("Access Denied!"); return
if strcmp(buf, "TI")   == 0: flags ^= 0x0001; return
if strcmp(buf, "GOD")  == 0: flags ^= 0x0002; return
if strcmp(buf, "MON")  == 0: flags ^= 0x0004; return
if strcmp(buf, "AMMO") == 0: ammo[0..5] = 80,60,30,15,12,9; return
if strcmp(buf, "WEAP") == 0: weapons = 0x01FF; return
if strcmp(buf, "KEY")  == 0: keycards = 0x7F; master = 1; return
if strcmp(buf, "FAIL") == 0: failsafe = 0x1FFF; return
if strcmp(buf, "ARM")  == 0: armour = 150; return
if strcmp(buf, "HEA")  == 0: health = 200; return
if strcmp(buf, "FRE")  == 0: flags ^= 0x0008; return
if strcmp(buf, "COOR") == 0: flags ^= 0x0010; return
```

`strcmp` is the byte-exact libc-style routine at `0x080184E8`, so matching is
case-sensitive and exact-length.

### 5.4 The context gate

`0x0800E7BE` turns a console `mode == 255` into `r6 = 0x80`;
`0x0800ECFC` tests that bit and jumps straight to the `TI` comparison, so the
four in-level commands are unreachable from the pause-menu console (and the
eleven cheat commands are unreachable from the level computers). This was
confirmed dynamically: `JAG`, `VINCE` and `JV` typed at the cheat console
produced no message and no state change, while `TI`/`GOD`/… did.

### 5.5 Effects

* `GOD` — bit 1 is tested by the damage routine at `0x0800DB1E`; if set the
  incoming damage is forced to 0 (also used as "invincible" by the level-9
  failsafe path).
* `MON` — bit 2 gates the radar-mode branch at `0x0800BD78`.
* `FRE` — bit 3 gates a call at `0x08004096` that suppresses enemy updates.
* `COOR` — bit 4 gates the coordinate overlay at `0x0800CBD6`.
* `TI` — bit 0 gates `0x0800CBAA`, which computes
  `v = [0x02010F8C] - [0x02009FE4]`, clamps to 99, formats it into
  `0x02010B90` and prints it at the top-left of the HUD. Both counters rise
  together; at Level 1 start the difference is 3.
* `HEA`/`ARM`/`AMMO`/`WEAP`/`KEY` write fixed values into the player struct.
* `FAIL` writes `0x1FFF` to the level failsafe word `0x0200EC02`.
* `PASSWORD`/`JAG`/`VINCE`/`JV` set one bit each in `0x0200EC0C` and patch a
  byte of the current level block (`*(u8*)([0x02014A08] + off) = 6`, with a
  `> 0x57 → −22` fixup), printing `Door is now unlocked!` /
  `Secret portal Opened!`.

## 6. Tables

### 6.1 Cheat console (`mode 255`) — 11 accepted strings

| # | String | Effect | RAM write (before → after) | Published? |
|---|---|---|---|---|
| 1 | `TI` | toggles top-left numeric debug read-out | `0x02010C30` bit 0 toggled | **NO** |
| 2 | `GOD` | invincibility (damage forced to 0) | `0x02010C30` bit 1 toggled | yes |
| 3 | `MON` | radar mode | `0x02010C30` bit 2 toggled | yes |
| 4 | `AMMO` | all six ammo pools | `0x0200EAB6..C0` = 0x50,0x3C,0x1E,0x0F,0x0C,0x09 | yes |
| 5 | `WEAP` | all weapons | `0x0200EAC4` = 0x01FF | yes |
| 6 | `KEY` | all keycards | `0x0200EAC6` = 0x007F, `0x0200EAC8` = 0x0001 | yes |
| 7 | `FAIL` | disables the self-destruct failsafe | `0x0200EC02` = 0x1FFF | **NO** |
| 8 | `ARM` | full armour | `0x0200EA9E` = 0x0096 (150) | yes |
| 9 | `HEA` | 200 health | `0x0200EAA6` = 0x00C8 (200) | yes |
| 10 | `FRE` | freeze enemies | `0x02010C30` bit 3 toggled | yes |
| 11 | `COOR` | coordinate display | `0x02010C30` bit 4 toggled | yes |

### 6.2 In-level computer (any other mode) — 4 accepted strings

| # | String | Effect | RAM write | Published? |
|---|---|---|---|---|
| 1 | `PASSWORD` | unlocks a door | `0x0200EC0C` bit 0 set; `[0x02014A08]+0x2117` patched | **NO** (not in any typed-code list) |
| 2 | `JAG` | "secret portal" (lower level-10 portal, per published guide) | `0x0200EC0C` bit 1 set; `+0xDB` patched | yes |
| 3 | `VINCE` | "secret portal" (upper level-10 portal, per published guide) | `0x0200EC0C` bit 2 set; `+0xE7` patched | yes |
| 4 | `JV` | third secret portal (script effect not exercised) | `0x0200EC0C` bit 3 set; `+0x21E1` patched | **NO** |

Setting an already-set bit prints `Function Already Accessed!`.

### 6.3 Debug flag word `0x02010C30`

| Bit | Mask | Command | Reader |
|---|---|---|---|
| 0 | `0x0001` | `TI` | `0x0800CBAA` |
| 1 | `0x0002` | `GOD` | `0x0800DB1E` |
| 2 | `0x0004` | `MON` | `0x0800BD78` |
| 3 | `0x0008` | `FRE` | `0x08004096` |
| 4 | `0x0010` | `COOR` | `0x0800CBD6` |

## 6b. Enumeration

### Space definition

| Property | Value |
|---|---|
| Alphabet | 26 symbols, `A`–`Z` only |
| Length | 1–17 characters (hard cap in the editor, `0x0800A184`) |
| Total representable strings | `Σ 26^k, k=1..17` = **1,179,180,408,000,556,754,576,342** (≈ 1.18 × 10²⁴) |
| Checksum | none |
| Reserved characters | none reachable (space/0x5B unreachable from the picker) |
| Accepted strings | **15** (11 cheat-console + 4 in-level), all listed in §6 |
| Table size | 15 literals; no generator, no second format |

Because validation is `strcmp` against a fixed literal list, enumeration is
exact: the accepted set *is* the table, and the table has 15 entries. There is
no algorithmic password layer, no checksum, and no hidden alphabet (the PC
version's lowercase `aa` trigger has no GBA equivalent as text; the GBA gate
is the button sequence).

### Novel codes (present in the ROM, absent from every published list)

Neither `TI` nor `FAIL` appears in the GameFAQs/GameSpot password list, the
jeuxvideo.com list, CodeTwink, Almar's Guides, the CodeBreaker/GameShark
archives, or the GameFAQs "Unlocking Level 10" note (which lists only `JAG`
and `VINCE`).

**(a) `TI` — accepted, effect visible:**
entered through the picker at the cheat console. `0x02010C30` goes
`0x0000 → 0x0001`, and after `Shut Down Computer` the HUD gains a numeric
read-out in the top-left corner (`3` at Level 1 start). Screenshot:
`Back Track - TI debug overlay.png`. This is an undocumented developer
read-out; its source word is `[0x02010F8C] − [0x02009FE4]` clamped to 99
(observed `0x0B5F − 0x0B5C = 3`, formatted to `"3"` at `0x02010B90`).

**(b) `FAIL` — accepted, state change in RAM:**
`0x0200EC02` goes `0x0000 → 0x1FFF` (the self-destruct failsafe word), with no
message and no HUD change — consistent with the level script reading that word
only in the Level 9 failsafe sequence.

`TI` was entered in four separate sessions and reproduced identically, and
toggles off on a second entry (flag `0x0001 → 0x0000`); `GOD` shows the same
toggle behaviour (`0x0002 → 0x0000`), as do `MON`/`FRE`/`COOR`.
`FAIL` was entered twice in separate sessions and both times wrote
`0x0200EC02 = 0x1FFF`.

Two further unpublished strings exist in the *in-level* context:
`PASSWORD` and `JV` (§6.2). They are statically proven (literal + comparison +
write target) but are gated off in the cheat console and were not exercised
in-game; see §8.

### Bounds proven by rejection (all run at the same console)

| Input | Result |
|---|---|
| `ZZZ` (not in table) | returns to the console, no flag/player/level write (all three words read back unchanged) |
| `GODX` (valid code + 1 char) | rejected; `0x02010C30` stays `0x0000` — matching is exact-length, not prefix |
| 17 × `A` (maximum length) | buffer stops growing at 17; submitting leaves all state unchanged |
| 18th character | physically impossible: `Right` does nothing at length 17 |
| lowercase (`god`) | not expressible in the picker (alphabet is `A`–`Z`, Up saturates at `Z`, Down at `A`) |
| `JAG`, `VINCE`, `JV`, `PASSWORD` at the cheat console | rejected — the mode gate skips the in-level block |
| `HEA` positive control | `0x0200EAA6` `0x64 → 0xC8`, HUD shows `200` |

Screenshots: `Back Track - 17 character cap.png`, `Back Track - HEA 200
health.png`, `Back Track - ARM 150 armor.png`.

## 7. Validation evidence

**Observed (emulator + memory reads)**

* The console opens only with `Select` then `L, Right, B, L, R, Left`; a wrong
  press does not open it.
* Password screen: initial buffer `A`, alphabet `A–Z`, cap 17 (length history
  `1→2→…→17`, then blocked).
* `GOD` → `0x02010C30 = 0x0002`; second `GOD` → `0x0000`.
* `MON` → `0x0004`; `FRE` → `0x0008`; `COOR` → `0x0010`; `TI` → `0x0001`.
* `HEA` → `0x0200EAA6 = 200` and the HUD reads `200`.
* `ARM` → `0x0200EA9E = 150` and an armour `150` appears in the HUD.
* `AMMO` → `0x0200EAB6..C0 = 80,60,30,15,12,9`.
* `WEAP` → `0x0200EAC4 = 0x01FF`; `KEY` → `0x0200EAC6 = 0x007F`,
  `0x0200EAC8 = 0x0001`.
* `FAIL` → `0x0200EC02 = 0x1FFF`.
* `JAG`/`VINCE`/`JV`/`PASSWORD`/`ZZZ`/`GODX` → no state change.
* `TI` adds the top-left read-out (`3`), and `0x020149B8 = 3`,
  `0x02010B90 = "3"`.

**Derived (instruction sequence)**

* The 15-entry `strcmp` chain, its order, and the `r6 & 0x80` mode gate.
* The button-sequence state machine and its tolerance.
* The editor's alphabet/cap and the 15 write targets.
* `GOD` = damage zeroing at `0x0800DB1E`; `MON`/`FRE`/`COOR` branches.

**Inferred**

* `TI`'s displayed quantity is a developer counter; the two source words rise
  together and only their 3-unit offset is visible at Level 1 start, so the
  field name is not proven.
* The exact scripted consequence of `0x0200EC02 = 0x1FFF` and of the
  `[0x02014A08]+…` portal-byte patches (Level 9 geometry).

## 8. Unknowns

* The in-level computer (`mode != 255`) was not reached in gameplay; `JAG`,
  `VINCE`, `JV` and `PASSWORD` are proven statically and proven *rejected* at
  the cheat console, but their in-level acceptance was not reproduced on
  screen. The published route (Level 9 computer) is consistent with the mode
  gate found in the code.
* The semantic of the `TI` read-out and of the `FAIL` failsafe word inside the
  level scripts.
* The header complement mismatch noted in §1 (cosmetic; the ROM runs).

## 9. Tooling

* mGBA 0.10.5 (SDL) under `Xvfb :152` + `openbox`; `xdotool` for input;
  ImageMagick for crops.
* **mGBA's command-line debugger (`mgba -d`) driven over a pty** was the
  memory sensor: `x/1`, `x/2`, `x/4` reads, `c` to resume, `Ctrl-C` to break.
  (The GDB stub in this build leaves the CPU halted at PC=0 and refuses
  `detach`, so the CLI debugger was used instead.)
* `arm-none-eabi-objdump -D -b binary -marm -M force-thumb`,
  `strings -t x`, `grep -abo`, Capstone 5.0.7 for literal-pool scans.
* Analysis scripts in `/tmp/opencode/backtrack/`: `phase0.py` (hashes/header/
  logo scan), `flow.py` + `type.py` (debugger driver, navigation, verified
  letter entry with RAM feedback), `one.py`/`toggle.py`/`hud2.py` (per-code
  tests and screenshots), `len_test.py` (17-char bound), `tival2.py`
  (`TI` read-out source).
* Savestate `game.ss1` at the Single Player Menu for reproducible re-entry.

## 10. Legal note

No ROM, extracted graphics, music or text from the game is redistributed here.
Only addresses, algorithms, short code strings, and screenshots of menu/UI
states taken from a legally held copy are documented.
