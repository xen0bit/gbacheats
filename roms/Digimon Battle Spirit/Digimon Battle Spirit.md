# Digimon Battle Spirit (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Digimon Battle Spirit/Digimon Battle Spirit.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title (0xA0) | `DIGIMON BTSP` |
| Game code (0xAC) | `A8SE` (USA/Europe) |
| Maker code (0xB0) | `B2` (Bandai) |
| Version (0xBC) | `00` |
| Fixed byte 0xB2 | `0x96` |
| Entry word (0x00) | `0xEA00002E` → stock ARM branch to `0x080000C0` |
| Complement (0xBD) | `0x6C` — matches the computed value over 0xA0..0xBC |
| Header checksum (0xBE) | `0x0000`; computed value would be `0x0594` |
| MD5 | `a4e3e4754c7bd16e5e2a52ee83ab2be1` |
| SHA-1 | `2ba954a54dd34b2b450d9ef718eb8a0f570b6549` |
| SHA-256 | `996de33330ac729d10d761d1901e7a335191c9503b0470569e8f294acf6618ed` |

Phase-0 notes (Observed):

* **One** GBA header in the image (Nintendo logo `24 ff ae 51 …` occurs exactly once, at file
  offset 0x4). This is a single-image cartridge, not a multi-game pack.
* Entry point and the first 4 KiB are stock crt0 code (waitstate setup, IRQ install, `0x080000C0`).
  No cracktro/trainer writer strings found (`CRC BANDIT`, `SUNHORS`, `MODE7`, `PARSEC`,
  `PARADOX`, `VENOM`, `TRSI`, `RISEN` all absent), and no appended payload: the tail of the
  image (0x380000..0x400000) is a constant `0xFF` pad (block entropy 0.72).
* The **complement byte is correct** while the **header-checksum field is zero**. Since the
  complement is derived from the same 0xA0..0xBC bytes, the header text is very likely the
  original one and only the 16-bit checksum field is zeroed. This is the "rebuilt header"
  artifact described in guide §16.1 and is not evidence of a gameplay modification. All
  analysis below was done on the hashed file above, unmodified.
* Dev banner left in the ROM: `DIMPS Ver0.72` at file 0x1F9D4 (matches the TCRF entry).
  The game is a port of the WonderSwan Color title by Dimps.

## 2. Executive summary

**This SKU has no password system, no code-entry screen and no button-code cheat.** That is a
proven negative, not an absence of looking: every screen reachable from boot was walked on
`:306` with RAM/pixel evidence, the game's entire input state structure was mapped and all 49
literal references to it enumerated, and the text/literal spaces were searched with counts
(below). The published "codes" for this title are GameShark/CodeBreaker *device* writes to RAM
and unlock-by-playing conditions — none of them is a string, table or key sequence inside this
ROM, and none is in the ROM under any encoding tested.

What the ROM *does* contain beyond the visible menus:

1. **A hidden fourth main-menu entry, `D·ARK`.** It exists in the shipped menu coordinate
   table (`0x08090B54`, five records) with Y = 0xC8 (200), which maps to root row 269+3·200 =
   869 — below the game area, which ends at root row ≈745. Moving the three following rows up
   (TCRF's patch: 0x90B5E←0x3C, 0x90B62←0x54, 0x90B66←0x6C, applied to a throw-away copy) makes
   the row labelled `D·ARK` visible; even then the cursor ring is still **three** entries
   (measured), so it can never be selected. It is the D-Ark Digivice link option, documented by
   TCRF and non-functional here.
2. **A 23-track sound test** (1..23, clamped) — the complete in-game music list.
3. **A default high-score table** (`KEN 250 / RYO 200 / LEE 150 / BUF 100`) at `0x1F9E8`,
   which the attract-mode `SCORE RANKING` screen renders live (observed: 1ST KEN 0250,
   2ND RYO 0200, 3RD LEE 0150).
4. **The only text entry in the game is `NAME ENTRY`**, a four-character high-score name
   (defaults above), not a password field: no comparison of that buffer against any constant
   exists, and its consumer is the score record (see §5.3).

The WonderSwan original's debug menu (`TEST MESSAGE / DEBUG FONT / COMPANY LOGO / TITLE DEMO /
NAME ENTRY / ENDHING / STAFF ROLL / SYNC WAIT / SYNC OK / SYNC FALSE / CANCEL`) was removed for
the GBA port: all 13 literals were searched in six encodings (ASCII, `+0x20` lowercase,
UTF-16LE, UTF-16LE lowercase, `0x380+(c-0x20)` 16-bit, `c-0x20` bytes) — **11 have no hit at
all**, and only `NAME ENTRY` (0xC1420) and `PUSH A` (0xC142B) survive because the score-name
screen genuinely uses them.

**Sequel note (queue 191, *Digimon Battle Spirit 2*):** nothing in this report was
carried over from, or assumed to apply to, the sequel. Every address, table and mask below was
read out of *this* A8SE Rev 0 image. The two titles share the Dimps engine idiom (same style of
56-byte pad struct, same 0x50-byte scene-object stride), but this report makes **no** claim that
any address matches; the sequel must be verified independently.

## 3. How to reproduce

```bash
cp "roms/Digimon Battle Spirit/Digimon Battle Spirit.gba" /tmp/opencode/digimonbs1/game.gba
Xvfb :306 -screen 0 1280x960x24 &
DISPLAY=:306 openbox &
cd /tmp/opencode/digimonbs1
DISPLAY=:306 SDL_AUDIODRIVER=dummy mgba -3 game.gba        # or: -3 -t <savestate> game.gba
W=$(DISPLAY=:306 xdotool search --name mGBA | head -1)
DISPLAY=:306 xdotool windowfocus "$W"
```

Keymap used (mGBA SDL default): **A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows**. Hold 90–120 ms per press; 0.4–0.7 s between presses (the
menus debounce and the title/attract cycle restarts if you are slow). `Shift+F1..F10` saves a
state, `F1..F10` loads; `import -window root shot.png` captures (the GL canvas is black to
`import -window`, so capture the root and crop the 720×480 viewport at +280+232).

Exact paths (all Observed):

| Screen | Path |
|---|---|
| Title | boot → logo → `PRESS START` (Start) |
| Attract | title idles into a battle demo and the `SCORE RANKING` board, then back to title |
| Main menu | Start → `1P BATTLE` / `2P BATTLE` / `OPTIONS` |
| Options | main menu → Down ×2 → A |
| Character select | main menu → A (1P) or Down+A (2P) |
| VS screen | character select → A (`BATTLE 1`, fixed pairing) |
| Battle | VS → A |
| Pause | in battle → Start (`CONTINUE` / `QUIT`) |
| 2P link wait | 2P → character select → A (`…ONE MOMENT PLEASE…`, tile text) |

Menu geometry used as a measurement instrument (root-window pixels): the highlighted row's
marker sits at `y = 269 + 3·Y` where `Y` is the record's second `u16` in the menu table. That
linear relation was confirmed by patching three table bytes and re-measuring (§6).

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`.

| Address | Kind | Contents |
|---|---|---|
| `0x080000C0` | code | stock ARM crt0 |
| `0x080118B8` | code | pad reader: builds the normalised key word, pressed/released, dx/dy, auto-repeat (see §5.1) |
| `0x080118B8`+literal pool `0x08011A68` | data | `0x03001300` (pad struct base) |
| `0x03001300` | RAM | pad struct, 56 bytes `0x03001300..0x03001337` (layout in §5.1) |
| `0x08090900`–`0x08090AEC` | code | title/menu screen init: loads tiles, builds 5 scene objects |
| `0x08090A90` | code | 5-iteration object build loop; table pointer read from `[0x03002A70]` |
| `0x08090B54` | data | **menu/object coordinate table, 5 × 4 bytes** `{u16 x, u16 y}` |
| `0x08090E58` | code | menu object update (A / UP / DOWN test, row slide) |
| `0x08090FA0` | code | menu/attract update (B test) |
| `0x080C3354`, `0x080C349C` | code | generic list-menu update: A=0x40 select, B=0x80 back, RIGHT\|LEFT=0x0A adjust value |
| `0x0808A94C`, `0x0808AA30` | code | character-select reel update (index at `0x03004740`) |
| `0x080C1434` | code | `NAME ENTRY` / `PUSH A` screen setup (text object `0x03002FA0`) |
| `0x03004740` | RAM | character-select index, 0..6 (observed 6 = GUILMON) |
| `0x020106AA` | RAM | sound-test track number, 1..0x17 (clamped both ends) |
| `0x03002A70` | RAM | pointer to `0x08090B54` (runtime, verified) |
| `0x03002A78` | RAM | first scene object (0x50-byte stride, 5 built) |
| `0x03002A60/62` | RAM | menu cursor value / wrap bound |
| `0x03002C0E` | RAM | menu row counter |
| `0x0300133C` | RAM | frame counter |
| `0x0300130A` | RAM | auto-repeat key word (pressed-or-repeated) |
| `0x0201D800` | RAM | save-block working buffer (`0x0E38` bytes cleared at boot) |
| `0x080CEF67`–`0x080CF4E4` | data | credits text block (ASCII) |
| `0x080D1348` | data | `     LINK ERROR!     ` (ASCII, never displayed on unlinked 2P attempt in this test) |

String/number table addresses (ASCII, NUL-terminated, verified by byte dump):

| Address | Text |
|---|---|
| `0x0801F9D4` | `DIMPS Ver0.72   ` |
| `0x0801F9E8` | `KEN\0` + `u16 0x00FA` + `01 01`, `RYO\0` + `0x00C8` + `00 02`, `LEE\0` + `0x0096` + `03 00`, `BUF\0` + `0x0064` + `00 00`, then `0x03001120 0x03001120` |
| `0x0801CB6C` | `    SCORE RANKING     ` (xref `0x0801CEA4`) |
| `0x080C1420` | `NAME ENTRY` (xref `0x080C14E4`) |
| `0x080C142B` | `PUSH A` (xref `0x080C14EC`) |
| `0x08089393` | `   SCORE      ` |
| `0x0833ECC8` | `      VS RECORD      ` |

### 4.1 Text encoding reality check

`strings` on this image returns 18,062 lines but the overwhelming majority are tile/sprite
noise. Filtering to "letter-ratio ≥ 85 %, ≥ 6 chars" leaves **4,259** runs; filtering again to
runs that contain ≥ 2 vowels and are ≥ 70 % letters/space leaves **≈ 400**, and every one of
those is either the credits block, the six labels above, or the six default-name prefixes
(`KIMJOY`, `KENSAN`, `ROYBOY`, `LINMON`, `SERIUS`, `QRIOUS` at 0x0C1138–0x0C12D8, entered as
incremental prefixes `K`→`KI`→`KIM`→…).

The in-game UI (`1P BATTLE`, `OPTIONS`, `TIME`, `LEVEL`, `GUILMON`, `TERSE…`) is **baked
graphics**, not text: none of those words exists as ASCII, `+0x20` lowercase, UTF-16LE,
`0x380+(c-0x20)` 16-bit codes, or `c-0x20` bytes. That is why a "no string hit" here does not
mean "no screen" (guide §11, "a half can have no text bank at all"), and it is the reason the
screen walk in §3/§6 is the primary evidence rather than the string scan.

## 5. Algorithm

### 5.1 Pad reader and the input struct (Derived, confirmed in RAM)

Entry `0x080118B8`, struct base `0x03001300`:

| Offset | Type | Meaning |
|---:|---|---|
| +0x00 | u16 | previous frame's normalised keys |
| +0x02 | u16 | normalised keys this frame |
| +0x04 | u16 | `~keys` (raw active-low copy) |
| +0x06 | u16 | pressed = keys & (keys ^ prev) |
| +0x08 | u16 | released = prev & (keys ^ prev) |
| +0x0A | u16 | auto-repeat result (pressed-or-repeated) |
| +0x0C / +0x0D | s8 | dx / dy (from LEFT/RIGHT and UP/DOWN, with opposing pairs cancelled) |
| +0x0E | u8[12] | auto-repeat delay counters (init 25) |
| +0x1A | u8[12] | auto-repeat initial-delay reload table |
| +0x26 | u8[12] | auto-repeat rate table (`4,4,4,4,1,1,1,1,4,4,4,4`) |
| +0x32 | u16 | flags: bit0 = auto-repeat enable, bit1 = dx/dy enable |
| +0x34 | u16 | repeat accumulator |

Normalisation (from `0x080118DC`), KEYINPUT is inverted first, then remapped:

```
UP 0x040 -> 0x001   RIGHT 0x010 -> 0x002   DOWN 0x080 -> 0x004   LEFT 0x020 -> 0x008
SELECT 0x004 -> 0x010   START 0x008 -> 0x020   A 0x001 -> 0x040   B 0x002 -> 0x080
R 0x100 -> 0x200       L 0x200 -> 0x800
```

This remap matters if you ever test a code you found elsewhere: the *values in ROM tables* are
in this normalised space, not the hardware bit order.

**There is no press history in the struct.** The 56 bytes are prev/keys/pressed/released/repeat
+ 12 single-byte auto-repeat timers + two 12-byte repeat tables + flags + accumulator. A
sequence matcher needs a press ring buffer and a progress index; this engine has neither, and
all 49 literal references to the struct (`0x03001302` ×5, `0x03001306` ×15, `0x0300130A` ×29) are
single-frame menu tests:

```
held   0x08015284 0x080B56A4 0x080B56B0 0x080B58E0 0x0837519C
pressed 0x0801D248 0x08081EC8 0x0808A4F0 0x080B56A8 0x080B56B4 0x080B58E4
        0x080C0408 0x080C3344 0x080D083C 0x080D13E4 0x0833F1A0 0x0833F300
        0x0833F814 0x0833F8D0 0x083751A0
repeat  0x08019018 0x08081ECC 0x08083D30 … 0x080CAC5C (29 sites)
```

The two multi-bit constants that survive review are both engine mechanics, not cheats:
`0x08375114/0x0837511C` (`tst #0x0A` → LEFT|RIGHT, then XOR both away — opposing-direction
cancellation) and `0x080C3584` (`tst #0x0A` → LEFT|RIGHT adjusts an option value).

### 5.2 Menu/object builder and the hidden row

`0x08090900` loads the title graphics and, at `0x08090A90`, builds **five** scene objects of
0x50 bytes from the table pointer held in `[0x03002A70]` (verified in a savestate: it points at
`0x08090B54`). Each iteration copies record `i`'s two `u16` into object `+0` and `+2`:

```
0x08090B54: 70 00 68 00   d0 ff 24 00   d0 ff 48 00   d0 ff 6c 00   d0 ff c8 00
            rec0          rec1          rec2          rec3          rec4
            (title logo)  (1P BATTLE)   (2P BATTLE)   (OPTIONS)     (D·ARK, off screen)
```

For records 1..4 the first `u16` is the constant `0xFFD0` (a fixed X offset) and the second is
the row position: `screen_y = 269 + 3·Y` in root pixels. The 720×480 viewport occupies root rows
232..712, so `0xC8` → 869, i.e. **157 px below the bottom of the viewport**.

Cursor ring (Observed, three measurements per state): rows 1P/2P/OPTIONS highlight at
377 / 485 / 593 and a fourth Down returns to 377 — the ring bound is 3; the 4th object is never
in it. This is what TCRF describes as "no longer selectable".

### 5.3 Text entry is a name, not a password

`0x080C1434` is the only text-entry screen. It creates a text object at `0x03002FA0` with the
ROM strings `NAME ENTRY` (`0x080C1420`) and `PUSH A` (`0x080C142B`), and the screen's own
alphabet is the four-character surname/initial field of the score record. The default records
live at `0x0801F9E8` (`KEN 250`, `RYO 200`, `LEE 150`, `BUF 100`) and the attract screen prints
them as 1ST/2ND/3RD. Guide §16.2b test: count the comparisons against the entry buffer — there
are **none**; every literal comparison in the area matches parser constants, and the buffer is
only ever copied into the score record. It is a label field, not a validator.

## 6. Tables

### 6.1 Options (Observed; all endpoints reached by rejection)

| Row | Values | Bound behaviour |
|---|---|---|
| TIME | 90, 120, 180 | Left at 90 stays 90; Right at 180 stays 180 (no wrap) |
| LEVEL | EASY, NORMAL, HARD | Left at EASY stays EASY; Right at HARD stays HARD |
| SOUND TEST | 01 … 23 (`0x01..0x17`) | Left at 01 stays 01; Right at 23 stays 23 |
| ERASE DATA | NO, YES | 2-state |
| RETURN | — | returns to the title screen (not to the main menu) |

Cross-check: with TIME = 180 the in-battle clock starts at `003:00` and read `002:51` a few
seconds in — the option is the real round timer.

### 6.2 Character reel (Observed, index verified in RAM)

`0x03004740` = 0..6, and the reel order (Down from GUILMON) is:

| index | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| name | TERRIERMON | RENAMON | VEEMON | WORMMON | AGUMON | SUKAMON | GUILMON |

Seven Down presses return to the starting character every time (period exactly 7, no blank or
`?` slot), so with a blank save the selectable set is **7** and no input can reach index ≥ 7.

### 6.3 Other enumerations

* Pause: `CONTINUE` / `QUIT`, ring of 2 (highlight 431 → 563 → 431).
* Main menu ring: 3.
* 1P flow: character select → VS (`BATTLE 1`, fixed opponent TERRIERMON for GUILMON) → battle.
  There is **no arena/stage select** in 1P; it is a fixed ladder.
* 2P flow: same character reel → a `…ONE MOMENT PLEASE…` link-wait message (no second unit).
* Sound test = 23 tracks; the three WonderSwan digivolution themes are documented as absent
  from this list (TCRF), which is consistent with the hard 23 cap.

### 6.4 Published material, verified against the ROM

| Source | Claim | ROM check |
|---|---|---|
| GameFAQs (GBA 583236) | unlockables only (BlackAgumon, Gabumon/Omnimon, Impmon, Lopmon/Kerpymon) via clears | no code string, no code screen; nothing to verify as a literal |
| GameFAQs / chaptercheats | "beat the game with 300+ D-Spirit" etc. | gameplay conditions, not inputs |
| gamehacking.org / almarsguides / libretro-database | `33002329 00FF`, `B0080D4B99D1`, `32011776 00FA` | **device** RAM writes; the literals `33002329`, `B0080D4B99D1`, `00FF`, `GameShark`, `Codebreaker` are all absent from the image |
| TCRF | D-Ark sprite values 0x90B5E/0x90B62/0x90B66 | **confirmed** — these are the low bytes of Y in records 2,3,4 of `0x08090B54`; see §6.5 |
| TCRF | `DIMPS Ver0.72` at 0x1F9D4 | **confirmed** |
| TCRF | JP stage-name/option tiles at 0x9E100 / 0x9FCA8 | 0x9E100 region is tile data; not exercised |

### 6.5 D·ARK row, as shipped and as revealed

```
as shipped : rec1 {FFD0,0024} rec2 {FFD0,0048} rec3 {FFD0,006C} rec4 {FFD0,00C8}
patched    : rec1 {FFD0,0024} rec2 {FFD0,003C} rec3 {FFD0,0054} rec4 {FFD0,006C}
```
Patch applied to a **throw-away copy** (`dtest.gba`) to identify the row; the original file was
not modified. With the patch the menu shows four boxes — `1P BATTLE`, `2P BATTLE`, `OPTIONS`,
`D·ARK` — at rows 377 / 449 / 521 / 593, and pressing Down from `OPTIONS` still returns to
`1P BATTLE` (377). The entry is displayable but not selectable, and there is no D-Ark handler
in the GBA build (the link toy feature was Japanese-WonderSwan only).

## 6b. Enumeration

**Space definition.** This title exposes *menus*, not codes. The complete representable input
surface, with the size of each axis, is:

| System | Alphabet / values | Length | Size | Reachability |
|---|---|---|---|---|
| Main menu | 3 rows | 1 | 3 | all 3 reached |
| Options | TIME 3 × LEVEL 3 × SOUND 23 × ERASE 2 | 4 | 414 | TIME/LEVEL/SOUND taken to both bounds; ERASE DATA deliberately not executed (it would wipe the save used for the rest of the walk) |
| Sound test | tracks 01..23 | 1 | 23 | 1 and 23 reached; clamp proven |
| Character reel | 7 characters | 1 | 7 | all 7 visited; wrap proven |
| Pause | 2 rows | 1 | 2 | both reached |
| D·ARK (hidden) | 1 row | 1 | 1 | **0 reachable** (ring bound 3) |
| Password / code entry | — | — | **0** | no screen, no validator, no alphabet |
| Button-code sequences | — | — | **0** | no history buffer, no mask table, no matcher |

**No novel code exists to mint, and that is the enumerated result.** There is no code space to
undersample: the only string a player can type is the 4-character high-score name, which is
compared against nothing. The §0.2 "novel value" deliverable is therefore replaced, per the
guide's negative-result rule, by: (a) the full screen/axis enumeration above with measured
bounds, (b) the census of every reference to the input state (49 literal references across 20
code sites) with the two multi-bit tests identified as engine mechanics, and (c) the two text
spaces searched (below).

**Bounds proven by rejection (Observed in the emulator):**

| Rejected input | Result |
|---|---|
| Down on `OPTIONS` (4th press) | wraps to `1P BATTLE` — the hidden `D·ARK` row cannot be entered, even when made visible by the ROM patch |
| Right on TIME at 180 / Left at 90 | stays 180 / 90 |
| Right on LEVEL at HARD / Left at EASY | stays HARD / EASY |
| Right on SOUND TEST at 23 / Left at 01 | stays 23 / 01 |
| Eighth Down on the character reel | returns to the first of 7 |
| Select at the title | only the `PRESS START` blink (no state change; 3,357 px = the blink box, everything else byte-identical) |
| Idling at the title | the attract loop cuts to the demo and to `SCORE RANKING` by itself — any pixel-diff "effect" test on the title must be taken against that drift, which is why the combo tests below rest on the code census rather than on screenshots |

**Text spaces searched (counts).** 4,194,304 bytes; `strings -n 4` → 18,062 runs; letter-ratio
filter → 4,259; English-shaped filter → ≈400, all accounted for as credits / six labels / six
name prefixes (§4.1). Keyword scan (case-insensitive): `password` 0, `pass` 0, `cheat` 0,
`code` 0, `secret` 0, `unlock` 0, `debug` 0, `hidden` 0, `bonus` 0, `extra` 0. The 13
WonderSwan debug-menu literals: 11 absent in all six encodings tested, `NAME ENTRY` and
`PUSH A` present as ASCII only — the live score-name screen.

**Button-mask space searched.** All 2-byte-aligned `u16` runs of ≥ 3 values drawn from the
normalised mask set `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}` were dumped (445 runs). Every
run of length > 3 lies inside graphics/tile data. The only code-adjacent candidate,
`0x08018CE4..0x08018D43`, is a small record table (fields 1, 0x20, 0x40, 0x23, 0x6E, 0x25,
0x1E, 0x80, 0xA0 …) sitting immediately after the object-init routine at `0x08018C80`; it does
not form a press sequence and is not referenced by any function that also reads `0x0300130A`.
Combined with §5.1 (no press history exists in the pad struct at all), the button-code space is
empty.

## 7. Validation evidence

**Observed (emulator, `:306`, mGBA, screenshots on disk in `/tmp/opencode/digimonbs1`)**

* Boot → logo → title → menu; attract loop shows the battle demo and `SCORE RANKING`
  (1ST KEN 0250 / 2ND RYO 0200 / 3RD LEE 0150).
* Main menu highlight rows 377/485/593, fourth Down wraps to 377.
* Patched copy: four visible rows at 377/449/521/593 labelled `1P BATTLE`, `2P BATTLE`,
  `OPTIONS`, `D·ARK`; Down from OPTIONS still wraps to 1P.
* Options endpoints as tabulated in §6.1, including sound test clamping at 01 and 23 and the
  180 s round timer reading `002:51` mid-round.
* Character reel: seven distinct names, period 7; `0x03004740` = 6 while GUILMON is shown.
* Pause is `CONTINUE`/`QUIT`, ring 2.
* 2P entry reaches the same reel then the `…ONE MOMENT PLEASE…` link-wait message.
* RAM reads: pad struct at `0x03001300` (56 bytes, dump in §5.1); `0x03001304` = `0x03FF`
  neutral and `0x01FF` with L held (active-low) in a savestate diff; sound-test value at
  `0x020106AA` tracking the display 01→23 and clamping.
* Save: mGBA creates a 512-byte `game.sav` (a 4 kbit EEPROM-sized part — inferred from the file
  size mGBA chose). Its first 0x40 bytes contain a byte-permuted copy of the ROM's
  `DIMPS Ver0.72` banner plus the `KEN`/`RYO`/`LEE` name-and-score bytes, so the block is
  initialised from the ROM default record rather than left blank.

**Derived (from disassembly)**

* Pad normalisation, pressed/released/repeat/dx/dy and the 12-button repeat tables (§5.1).
* Menu object build loop of 5 objects from `0x08090B54`, stride 0x50, pointer via
  `0x03002A70`.
* `NAME ENTRY`/`PUSH A` string plumbing and the absence of any comparison against the entry
  buffer.
* Absence of a press-history field anywhere in `0x03001300..0x03001337`.

**Inferred**

* Unlock characters (BlackAgumon, Lopmon, Impmon) are save-driven and are added to the reels as
  extra indices; the reel is rebuilt from the save block. Not exercised (no clear was played),
  and the save bit layout was not isolated — see §8.
* The `D·ARK` row's handler is the WonderSwan D-Ark link path and has no GBA implementation.

## 8. Unknowns

1. **Save bit layout / unlock bits.** The 512-byte EEPROM block is initialised from the ROM
   defaults and rewritten when options change, but the per-character unlock bits, the clear
   counter and the D-Spirit (300) counter were not isolated. Guide §16.18's method (enumerate
   the setter's callers) was not completed because reaching a clear costs a full ladder run;
   until that is done, the unlock conditions remain a published claim, not a ROM-verified one.
2. **`NAME ENTRY` was not exercised on screen.** Its strings, text object and default record
   table are verified; the trigger (a qualifying score) was not produced.
3. The `0x0FFD0` first field of the menu records is a fixed X offset whose exact render
   transform (`x_screen = f(0xFFD0)`) was not derived; only the Y field is proven linear.
4. `LINK ERROR!` (`0x080D1348`) has no direct pointer xref found; the 2P attempt stopped at the
   link-wait message, so the error screen itself was not displayed.
5. The sequel comparison is out of scope here; no address in this report should be assumed to
   hold for *Digimon Battle Spirit 2*.

## 9. Tooling

* `mgba` (SDL) under `Xvfb :306` + `openbox`, `SDL_AUDIODRIVER=dummy`; `xdotool` for XTEST
  input; `import -window root` + ImageMagick `convert`/`montage` for captures.
* Python 3 with Capstone 5.0.7 for the Thumb/ARM instruction scans.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 --start-address=…
  --stop-address=…` for ARM windows. (This binutils rejects `-M force-arm`; plain `-marm`
  decodes ARM and `-M force-thumb` decodes Thumb.)
* Scripts kept in `/tmp/opencode/digimonbs1`: `ident.py` (header/hash/entropy/logo scan),
  `scan_keys.py` (mask-constant scan), `ss.py` (mGBA `gbAs` savestate zlib decoder + differ),
  `peek.py` (IWRAM/EWRAM peek), `probe.py`/`probe2.py` (savestate-diff field discovery),
  `key.py` (input helper).
* Savestate fact used constantly: mGBA `.ssN` is a PNG whose `gbAs` chunk is
  `zlib`-compressed, 397,312 bytes for this ROM, with IWRAM at 0x19000 and EWRAM at 0x21000
  (guide §16.13) — this gave every RAM proof above without needing the GDB stub.

## Legal note

No ROM, graphics, music or text from the game is redistributed here; only hashes, addresses,
structure and my own measurements. The patched copy used to identify the hidden menu row was a
throw-away file used for measurement and has been deleted.
