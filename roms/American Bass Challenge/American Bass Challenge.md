# American Bass Challenge (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `American Bass Challenge.gba` |
| Size | 4,194,304 bytes (`0x400000`, 32 Mbit) |
| Header title | `AMERICA_BASS` |
| Game code | `AABE` |
| Maker code | `41` (Ubisoft) |
| Software version | `0x00` (Rev.00) |
| Fixed byte `0xB2` | `0x96` |
| Entry word | `0xEA00002E` → `0x080000C0` |
| MD5 | `61d4355a0731c3150c36b5a704173c70` |
| SHA-1 | `1fc03cca393ddbc633d309aae95b42c89e4d0e96` |
| SHA-256 | `294e7c34a9d2ee37bc005368fcc268dfdc0dfaaade8adddae5d25e2fa33ee418` |

Header-integrity note (observed): complement byte `0xBD` is `0x69` and the stored
header checksum at `0xBE` is `0x0000`; the recomputed complement is `0xAD` and the
recomputed checksum is `0xFA69`. The ROM nevertheless boots in mGBA 0.10.5. This is
recorded as a dump/header anomaly, not as game behaviour.

Embedded-header scan (full 156-byte Nintendo logo): three header copies exist:

| File offset | Title | Code | Entry |
|---:|---|---|---|
| `0x000000` | `AMERICA_BASS` | `AABE` | `0xEA00002E` |
| `0x29F5F8` | `AMERICA_BASS` | `AABE` | `0xEA00002E` |
| `0x2A1254` | `AMERICA_BASS` | `AABE` | `0xEA00002E` |

All three have the same title/code, so this is not a multi-game pack. The two later
copies sit next to a small multiboot/link image area (see `BLACKBASSADVANCE` at
`0x2E268`) and are treated as a copied/secondary image, not a second game.

## 2. Executive summary

This is a save-based fishing game (three save slots, 8 KiB `.sav`); it has **no
password or serial-code system**. The developer-intended cheat surface is entirely
button-driven:

1. **Boot debug gate.** At the Ubisoft/Starfish logo, enter
   `Select, Up, Down, A, Left, Start`. A hidden debug sound-test screen appears
   after the logo. The checker is a generic NUL-terminated key-mask sequence task;
   its table is `04 40 80 01 20 08 00` at `0x0829F18C`, and it sets
   `0x03002240 = 0xA5`.
2. **Undocumented L modifier.** The published instruction omits a second gate at
   `0x080003F2`: if `0x03002240 == 0xA5` *and* L is held at that moment, bit 31 of
   `0x0300223C` is set. That bit enables a **debug parameter editor** which is then
   reached in-game by `Select` → `CAST`. Without the L modifier, `CAST` behaves
   normally (tutorial cast); with it, the editor opens (`LURE_NO`, `TEMP`,
   `LURE_COL`, `FILL`, `FMAP_NO`, `M_KIND`, `WEATHER`, `PLAYER`, `HOUR`, `MINUTE`,
   `SEC`, `ADVICE`).
3. **Second undocumented combination.** With `0x03002240 == 0xA5`, pressing
   **B + L** during gameplay opens a second developer menu:
   `STAGE, PLAYER KIND, PLAYER COLOR, WEATHER, HOUR, MINUTE, STAGE INITIAL,
   BA ARE DISP, MESSAGE DEBUG 1, MESSAGE DEBUG 2, SAVELOAD CHECK, RANKING CHECK,
   ENDING CHECK`. `RANKING CHECK` was executed and displays a 20-entry hex table
   with `[A] RANKING / [B] QUIT` and `RANK 29`.
4. **Sound test at the title.** Holding **L + R + A** at the `PRESS START`
   prompt opens the normal sound test. This is independent of the boot sequence.
5. **Published "All Fish Are Bass" code** (`Up, Up, Down, Left, Left, Right`) could
   not be confirmed. No occurrence of that sequence exists in the ROM in any
   byte/u16 permutation or active-low encoding, and entering it at the save-slot
   menu produced no observable change. It is reported as unverified for this
   build; the debug codes above are verified.

## 3. How to reproduce

Emulator: mGBA SDL 0.10.5 (`/usr/games/mgba`), 3× scale.

```bash
Xvfb :135 -screen 0 1024x768x24 &
DISPLAY=:135 openbox &
DISPLAY=:135 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 \
  "/mnt/gbacheats/roms/American Bass Challenge/American Bass Challenge.gba" &
```

Keymap used (mGBA default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys. Hold each key 70–150 ms; the game polls
once per frame.

### 3.1 Boot debug + sound test

1. Watch the Ubisoft logo. About 1.5 s after reset/launch, press and release
   `BackSpace, Up, Down, x, Left, Return` (70 ms hold, 50 ms gap).
2. Keep holding `a` (L) for ~1.5 s starting immediately after the last press.
3. The logo fades into the debug sound test
   (`evidence/boot_debug_soundtest.png`). Use `Down` to `EXIT`, then
   `Start + A` to continue.

A wrong last button (e.g. `B` instead of `Start`) does **not** open the sound test
(`evidence/reject_wrong_last_button.png`).

### 3.2 Title sound test

Wait for `PRESS START`, then hold `L + R + A` (`a`, `s`, `x`) for ~0.8 s.
The normal sound test opens (`evidence/title_LRA_soundtest.png`). Exit with
`Down` then `A`.

### 3.3 In-game debug parameter editor (CAST)

1. Perform 3.1 including the L hold.
2. Exit the sound test and start a save (or create one: slot → name → gender →
   arm → style → register).
3. Choose `PRACTICE` (or `TOURNAMENT`), start the stage, press `Start` twice to
   start the clock, then `Select` → `CAST`.
4. The numeric editor appears instead of the tutorial cast
   (`evidence/cast_debug_editor.png`). Up/Down select a field, Left/Right change
   its value, `B` exits.

### 3.4 Stage/Player debug menu (B+L)

In the same A5-armed session, while in gameplay, press **B + L** (`z` + `a`) for
~0.6 s. The 13-entry menu opens (`evidence/BL_stage_menu.png`). `ACT`/`A` executes
the selected entry; `B` exits. `RANKING CHECK` was executed
(`evidence/ranking_check.png`).

## 4. Address map

| Address | Size | Meaning |
|---|---:|---|
| `0x0800046C` | Thumb func | Generic key-sequence task. Reads `0x02021DD8`, compares each byte to a NUL-terminated ROM table; on match sets `0x03002240 = 0xA5`. |
| `0x0829F18C` | 7 bytes | Boot code table: `04 40 80 01 20 08 00` = Select, Up, Down, A, Left, Start, terminator. |
| `0x0800034C` | Thumb func | Logo-state handler; registers the sequence task. |
| `0x08000434` | literal | Thumb pointer `0x0800046D` to the task. |
| `0x080003F2` | Thumb | L-modifier gate: if `[0x03002240]==0xA5` and `(keys & 0x200)`, OR `0x80000000` into `0x0300223C`. |
| `0x03002240` | byte | Boot-sequence flag (`0xA5` on success). |
| `0x0300223C` | word | Debug capability flags; bit 31 = parameter-editor enable. |
| `0x08000520` | Thumb func | Keypad IRQ/handler: reads `0x04000130`, builds key-state words. |
| `0x0802B214` | 16 × u16 | Direction remap table (identity for single directions). |
| `0x02021DD8` | u16 | Held-key word compared by the debug code. |
| `0x08015E54` | Thumb func | In-game debug-key dispatcher, called every frame from `0x0801605C`. |
| `0x08015E58` | Thumb | A5 gate (`cmp r0,#0xA5`). |
| `0x08015E60` | Thumb | `B+L` test (`keys & 0x0202 == 0x0202`) → menu. |
| `0x08015E90` | Thumb | `B+R` test (`keys & 0x0102 == 0x0102`) → state 7. |
| `0x08015EC4` | Thumb | `A+R` test (`keys & 0x0101 == 0x0101`) → debug counter/state writes. |
| `0x08014B74` | Thumb func | Builds the Stage/Player menu from `0x08331F4` + `0x0833290`. |
| `0x08331F4` | ASCII table | Stage/Player menu labels (`Stage`, `Player Kind`, … `Ending Check`). |
| `0x0833290` | structure | Per-entry parameter/limit table for the Stage/Player menu. |
| `0x0834F74` | ASCII bank | Numeric editor format strings (`LURE_NO = %2X`, … `ADVICE = ON`). |
| `0x082B8FC` | ASCII | `DEBUG MODE` |
| `0x082B918` | ASCII | `SOUND TEST` text block. |
| `0x02021D48` | u16 | “pressed this frame” key word. |
| `0x02021DA0` | u16 | Raw/held key word. |
| `0x02021DD0` | u16 | Key-repeat delay counters. |

The game’s save is `American Bass Challenge.sav` (8192 bytes); the three slots are
shown as I/II/III. There is no SRAM/EEPROM password path in the UI.

## 5. Algorithm

### 5.1 Boot sequence validator (`0x0800046C`)

```
seq  = ROM[0x0829F18C]          ; 04 40 80 01 20 08 00
i    = 0
flag = 0x03002240 = 0
loop:
    wait for [0x02021DD8] != 0          ; a press
    if [0x02021DD8] == seq[i]:
        i++
        if seq[i] == 0:
            [0x03002240] = 0xA5
            call 0x0800136C([0x03000BD8])
            return
    else:
        i = 0                            ; wrong press restarts
```

Only an exact 8-bit-mask match advances. L/R are outside the compared byte, which
is why L is a separate gate.

### 5.2 L modifier (`0x080003F2`)

```
if [0x03002240] == 0xA5 and ([0x02021DD8] & 0x0200):
    [0x0300223C] |= 0x80000000
```

This bit is what the pause→CAST path tests before opening the numeric editor.

### 5.3 In-game debug dispatcher (`0x08015E54`)

```
if [0x03002240] != 0xA5: return
if (keys & 0x0202) == 0x0202:      ; B+L
    call 0x080157FC()
    call 0x08014B74()              ; build Stage/Player menu
    state = 4
if (keys & 0x0102) == 0x0102:      ; B+R
    clear low bits of [0x02023FBC]; state = 7
if (keys & 0x0101) == 0x0101:      ; A+R
    [0x02023620+4]=1; [..+5]=1; [..+6]=0; increment counter
```

## 6. Tables

### 6.1 GBA key masks used by the validators

`A=0x01, B=0x02, Select=0x04, Start=0x08, Right=0x10, Left=0x20, Up=0x40,
Down=0x80, R=0x100, L=0x200` (active-high after `~KEYINPUT & 0x3FF`).

### 6.2 Boot code

`04 40 80 01 20 08` = **Select, Up, Down, A, Left, Start**.

### 6.3 Sound tests

| Entry | Combination | Result |
|---|---|---|
| Logo sequence | Select, Up, Down, A, Left, Start | Debug sound test (with MP0–MP4 rows) |
| `PRESS START` | L + R + A | Normal sound test |

### 6.4 Numeric debug editor (pause → CAST, bit-31 armed)

| Field | Observed value/format | Notes |
|---|---|---|
| `LURE_NO` | `%2X` | Right increments (00→01 observed). |
| `TEMP` | `%2X` (A0) | Temperature seed. |
| `LURE_COL` | `NL` / `AP` | Lure colour. |
| `FILL` | `OFF` / `ON` | Livewell fill. |
| `FMAP_NO` | `%2X` (04) | Fishing-map id. |
| `M_KIND` | `%2X` (01) | Model/kind. |
| `WEATHER` | `%2X` (01) | Weather. |
| `PLAYER` | `%2X` (00) | Player kind. |
| `HOUR` | `%2X` (07) | Time. |
| `MINUTE` | `%2X` (03) | Time. |
| `SEC` | `%2X` (20) | Time. |
| `ADVICE` | `OFF` / `ON` | Advisor display. |

### 6.5 Stage/Player debug menu (B+L, A5 armed)

Labels in ROM order (`0x08331F4`):

1. `STAGE`
2. `PLAYER KIND`
3. `PLAYER COLOR`
4. `WEATHER`
5. `HOUR`
6. `MINUTE`
7. `STAGE INITIAL`
8. `BA ARE DISP`
9. `MESSAGE DEBUG 1`
10. `MESSAGE DEBUG 2`
11. `SAVELOAD CHECK`
12. `RANKING CHECK`
13. `ENDING CHECK`

`RANKING CHECK` was executed: it draws entries `00`–`13` with hex values and
`[A] RANKING / [B] QUIT`, plus `RANK 29`. `SAVELOAD CHECK` returned to the stage
start (observed).

## 6b. Enumeration

### 6b.1 Space definition

* **Alphabet:** the 8 one-button press masks `{0x01,0x02,0x04,0x08,0x10,0x20,
  0x40,0x80}`. L (`0x200`) and R (`0x100`) are not representable in the 8-bit
  sequence table.
* **Length:** exactly 6 presses, NUL-terminated in the table.
* **Representable boot sequences:** `8^6 = 262,144`.
* **Accepted:** exactly **1** (`Select, Up, Down, A, Left, Start`).
* **Modifier:** a separate boolean L gate at `0x080003F2`, so the full input space
  is `262,144 × 2 = 524,288` (sequence, L-held) pairs. Two are accepted in the
  sense that both enter the sound test, but only the L pair additionally sets
  `0x0300223C` bit 31.
* **Sound test:** one 3-button simultaneous combination (`L+R+A`) out of the 56
  possible 3-button subsets of 8 face/direction buttons (or 120 of 10 including
  L/R); only the documented one is wired.

### 6b.2 Novel (unpublished) codes / combinations

1. **`Select, Up, Down, A, Left, Start` + hold L** — the published text names only
   the six-press sequence. Holding L is an undocumented modifier that enables the
   numeric debug editor. Verified: with L the pause→CAST path opens the editor
   (`evidence/cast_debug_editor.png`); without L the same path shows the normal
   tutorial cast. This is the code-space analogue of “a code in no published
   list”.
2. **`B + L` in gameplay** — not published anywhere. With the A5 flag armed it
   opens the 13-entry Stage/Player menu (`evidence/BL_stage_menu.png`).

Both were entered in mGBA and the effects were screenshotted.

### 6b.3 Bounds proven by rejection

| Test | Expected by model | Observed |
|---|---|---|
| Boot: `Select, Up, Down, A, Left, B` (wrong 6th) | reject | No sound test; title screen follows (`evidence/reject_wrong_last_button.png`). |
| Boot: correct sequence, no L | sound test only | Pause→CAST shows normal tutorial cast; no numeric editor. |
| Boot: correct sequence + L | sound test + bit 31 | Pause→CAST opens numeric editor. |
| `B+L` at the save/mode menu | no effect (handler is gameplay-only) | No menu in either armed or unarmed session. |
| `B+L` in gameplay without A5 | reject (gate at `0x08015E58`) | No menu; derived from the gate and consistent with the mode-menu test. |
| Published “All Fish Are Bass” `Up, Up, Down, Left, Left, Right` | accepted if implemented | No visible/audible confirmation at the save-slot menu; no matching table/literal in ROM. Recorded as unverified. |

## 7. Validation evidence

**Observed (emulator screenshots):**

* Boot sequence → debug sound test (`evidence/boot_debug_soundtest.png`).
* L+R+A at `PRESS START` → normal sound test
  (`evidence/title_LRA_soundtest.png`).
* Boot sequence + L → pause→CAST numeric editor
  (`evidence/cast_debug_editor.png`); boot sequence without L → normal cast.
* B+L in-game → 13-entry menu (`evidence/BL_stage_menu.png`).
* `RANKING CHECK` → ranking hex table (`evidence/ranking_check.png`).
* Wrong last button → no sound test
  (`evidence/reject_wrong_last_button.png`).

**Derived (disassembly):**

* `0x0800046C` is the sequence comparator; table `0x0829F18C`; flag `0x03002240`.
* `0x080003F2` implements the L gate and bit-31 write.
* `0x08015E54` implements the A5 gate and B+L / B+R / A+R branches.
* `0x08014B74` builds the menu from `0x08331F4` and `0x0833290`.

**Inferred:**

* Exact field limits of the numeric editor (only `LURE_NO 00→01`, and the listed
  initial values, were exercised).
* Purpose of the two embedded header copies.
* `B+R` and `A+R` runtime effects (branches decoded, not exercised).
* The published All-Fish code is likely absent from this US build (no data match,
  no observed effect).

## 8. Unknowns

* Whether the “All Fish Are Bass” code exists in another regional build; it is not
  represented in this ROM.
* Full numeric ranges and all visible effects of every numeric-editor field.
* `0x03000BD8` (value passed to `0x0800136C` when the boot sequence completes) and
  the exact visual state it selects.
* The intended purpose of the second/third header copies and the
  `BLACKBASSADVANCE` multiboot area.
* Header checksum/complement mismatch (possibly a patched dump).

## 9. Tooling

* `mGBA` 0.10.5 SDL, `Xvfb :135`, `openbox`, `scrot`, `xdotool`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python 3 + Capstone for BL/pointer/literal scans; a small `strings`/byte-pattern
  scanner for the key tables; mGBA savestates + zlib parsing for RAM layout checks.
* Working directory: `/tmp/opencode/bass` (scans, screenshots, helper `key.py`).
* Evidence copies: `roms/American Bass Challenge/evidence/`.

## Legal note

No ROM, extracted graphics, audio, or text bank is redistributed. All images in
`evidence/` are emulator screenshots of the analyst’s own play session.
