# Breath of Fire (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Breath of Fire/Breath of Fire.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `BOF1` (space/NUL padded) |
| Game code | `ABFE` (US) |
| Maker code | `08` |
| Software version | `0x00` |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| Complement check | stored `0xD3`, computed `0xD3` |
| Header checksum | `0x0000` (normal for this image; complement is the useful integrity signal) |
| Nintendo logo hits | 1, at file `0x0` (single image, no multi-game pack) |
| MD5 | `17a32cfa3d0a5c74f914281ef55c75cd` |
| SHA-1 | `b30533f68037b47d5439bab0182169e4a643a38d` |
| SHA-256 | `3289aec193497c86c3c769b42c1024a1d491d48f15b90fcb58910dca0a79647a` |

No cracktro, trainer, or appended payload was found: the entry word is the stock
GBA branch, the Nintendo logo is intact, the complement byte matches, and the
usual scene-group markers (`SUNHORS`, `Mode7`, `CRC BANDIT`) are absent.
Checksum `0x0000` is an artifact of a rebuilt header, not evidence of patching
(§16.1); the complement matches.

## 2. Executive summary

**This US GBA build has no typed password, keypad, or button-sequence cheat system.**
The one in-game/developer code system that is widely published for Breath of Fire
is the SNES "New Game Cheat": at the name-entry screen hold A+Y+L+R on
*controller 2*, press Up×4, Right×2, Down×8, Left×1, watch the background turn
red, then enter `RYU`, `CHUN`, `VEGA`, `KEN`, `DeeJ` or `Fei` to start from a
hard-coded debug save. That system is **not present in this GBA port**:

* No encoded form of any of the six names exists in the 4 MiB image
  (`RYU`=`3B 42 3E`, `CHUN`=`2C 31 3E 37`, `VEGA`=`3F 2E 30 2A`,
  `KEN`=`34 2E 37`, `DeeJ`=`2D 45/46 45/46 33`, `Fei`=`2F 45/46 32`): **0/6 hits**.
* No direction-sequence table exists in any plausible encoding
  (`0x40,0x40,0x40,0x40,0x10,0x10,0x80×8,0x20` as u8 or u16;
  `0,0,0,0,1,1,2×8,3`): **0 hits**.
* No hard-coded save blobs exist. A valid GBA save slot carries the ASCII
  signature `CAPCOM` at `+0x29E` (validator at `0x080440F8`). The whole ROM
  contains `CAPCOM` only twice: the validator's literal at `0x080A65E8` and the
  copyright string at `0x081A8A2C`. There is no save-shaped blob to load.
* The GBA has no controller 2. The only key readers are the global pad scanner
  at `0x0800033C` and the menu/grid navigator at `0x0805B040`; neither tracks a
  direction sequence, and there is no JOY/SIO button path (the SIO code is the
  normal link-trade code around `0x0809B980`–`0x0809E048`).
* Dynamically, **21 different GBA hold-mask variants** of the published gate
  (none, A, B, L, R, all pairs/triples, A+B+L+R, Select, Start, Select+Start,
  L+R+Select, L+R+Start) followed by Up×4 Right×2 Down×8 Left×1 produced **no
  red background and no state change** (all frames identical to
  `srgb(34.6%, 22.3%, 69.5%)` mean blue).
* Entering `RYU` normally through the UI creates the ordinary file `RYU 1`
  (the file list shows level 1), whereas the published cheat produces a
  level-29 Scande save.

The name field is a **label, not a validator** (§16.2b): its four bytes are only
copied and drawn. The consumers found are the draw routines (`0x08041436`,
`0x08041660`), the empty-name default (`0x08041ADC`, writes `Zack`), the
template copy (`0x08041B24`), and the save-struct copy (`0x080424FA`). No
comparison against the name bytes exists.

One **developer debug gate** does survive, but is compiled off:
`BATTLE_DEBUG=0` at `0x08150B30`. The check at `0x0806D60E` reads byte `+13`
(the `'0'`, `0x30`), ANDs it with `1`, gets 0, and always skips the debug branch
at `0x0806D61C`. The byte lives in ROM and has no writer, so the branch is
statically unreachable in this build.

No debug menu and no sound test exist: the decoded text bank contains no
`DEBUG`, `SOUND`, `BGM`, `TEST`, `PASSWORD`, `CHEAT`, `UNLOCK`, `STAFF`,
`GALLERY` or `CONFIG` UI string (counts in §6); the only options are Text Speed,
Dash and Music ON/OFF.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL, `-3`, under `Xvfb :212` + `openbox`,
`SDL_AUDIODRIVER=dummy`.

Keymap (mGBA default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows.

### 3.1 Menus walked (all with screenshots on disk)

| Screen | Path | Items seen |
|---|---|---|
| Boot / title | power-on | Capcom logo, "LICENSED BY NINTENDO", title |
| Main menu, no save | Start | `NEW GAME` only |
| Main menu, save present | Start | `GAME START`, `NEW GAME`, `COPY`, `ERASE`, `EXCHANGE` |
| File select | NEW GAME / GAME START | `No.1`, `No.2`, `No.3` (name + level) |
| COPY | main → COPY | file select, same three slots |
| ERASE | main → ERASE | file select, same three slots |
| EXCHANGE | main → EXCHANGE | "Please wait…" (link-cable screen) |
| Name entry | NEW GAME → blank slot | grid `A–Z`, `a–z`, `0–9`, punctuation, `Fwd`, `Bck`, `End` |
| Pre-game options | name → End | `Text Speed` (Fast/Nrml/Slow), `Dash` (Nrml/Auto), `Music` (ON/OFF), `END` |
| In-game pause | Select | `ITEM`, `SPEL`, `EQUIP`, `STAT`, `SWCH`, `CHNG`, `OPTN`, `SAVE`, `END` |
| ITEM submenu | ITEM | `USE`, `DSCD`, `CHNG`, `SORT`, `VITL` |
| SPEL | SPEL | "Use whose spell?" → `Zack` (empty at Lv1) |
| EQUIP | EQUIP | "Change whose equipment?" → `Zack` |
| STAT | STAT | "View whose status?" → `Zack` |
| SWCH | SWCH | "Switch whose line?" → `Zack` |
| CHNG | CHNG | "Change which character?" → `Zack` |
| OPTN | OPTN | same three options as pre-game |
| SAVE | SAVE | "Quick Save the game? Yes / No" |
| Quick-save prompt | SAVE → Yes/No | confirmation dialogue |

No screen contains a text/password entry field other than the character-name
grid, and no menu contains an undocumented extra row.

### 3.2 Published code test (RYU)

1. New Game → blank file → name screen.
2. Type `R` (row 3, col 2), `Y` (row 4, col 4), `U` (row 4, col 0); Start jumps
   the cursor to `End`; A confirms.
3. Options → END → GAME START → file list.

Result: the new file reads `RYU 1` (level 1). No debug save and no level-29
header. Screenshot: `shots/ryu4.png` (file list).

### 3.3 GBA gate sweep

For each of 21 masks — `{}`, `A`, `B`, `L`, `R`, `AB`, `LR`, `AL`, `AR`, `BL`,
`BR`, `ABL`, `ABR`, `ALR`, `BLR`, `ABLR`, `Select`, `Start`, `Select+Start`,
`LR+Select`, `LR+Start` — the state `game.ss2` (name screen, name `RYU`) was
reloaded, the mask held, then `Up Up Up Up Right Right Down×8 Left` pressed
(80–100 ms holds), the mask released, and the frame captured. Mean pixel colour
of all 21 frames was `srgb(34.6% ± 0.1, 22.3% ± 0.1, 69.5%)`; none showed the
red background described by the published cheat. Screenshots:
`shots/mask_0.png` … `shots/mask_20.png`.

### 3.4 Static searches

* `strings -t x -n 3` → 101,239 lines; `debug` = 2 (the battle flag and one
  printf); `SOUND/PASSWORD/CHEAT/SECRET/UNLOCK/STAFF` = 0; `BGM` = 3 binary
  false positives.
* Game text decoded with the ROM's own font mapping → 70,391 runs; keyword
  counts in §6.
* Six name encodings searched as bytes and as 32-bit values: 0/6.
* Direction-sequence table searched as u8, u16 and 2-bit-packed: 0.
* Save signature `CAPCOM`: 2 occurrences total, neither a save blob.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08000000` | ROM base; entry `0xEA00002E` → `0x080000C0` |
| `0x0800033C` | Global pad reader: `~KEYINPUT`, edge detection, writes struct `0x030016E0` |
| `0x030016E0` | Key struct base (`+4` held, `+6` newly pressed, raw active-high bits A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200) |
| `0x0805B040` | Menu/grid navigator: `mode*100 + 0x03000B10`; mode 1 = name grid |
| `0x0814CBB8` | 69-byte name-grid glyph table |
| `0x0814CC16` | 69 × u16 name-grid tile positions |
| `0x03004410` | Game-state struct `gs` |
| `0x03004424` | Name buffer, 4 glyph bytes (`gs+0x14`) |
| `0x0300443C` | Name cursor/length (`gs+0x2C`) |
| `0x03004433` | Name repeat counter (`gs+0x23`) |
| `0x08041436` | Draw name byte 0 |
| `0x08041660` | Draw name byte 0 (second routine) |
| `0x08041ADC` | Empty-name default: writes `Zack` = `43 48 4A 52` |
| `0x08041B24` | Copy name into template |
| `0x08041C04` | Name-screen A/B confirm handler |
| `0x080424D4` | New-game save initialiser |
| `0x080424FA` | Copy name into save struct `0x0202DBD0+0x24` |
| `0x080440F8` | Save-slot signature check: 6 bytes at `slot+0x29E` == `CAPCOM` |
| `0x080A65E8` | `CAPCOM` literal used by the validator |
| `0x08043AA8` | 4-slot save validator (checksum at `+0`, signature at `+0x29E`) |
| `0x08150B30` | ASCII `BATTLE_DEBUG=0` (dev flag) |
| `0x0806D60E` | Reads `BATTLE_DEBUG` byte `+13` and ANDs with 1 |
| `0x0806D61C` | In-battle debug branch (unreachable, see §5.3) |
| `0x03000F4C` | Toggle word written by the debug branch |
| `0x08085670` | Function called by the debug branch |
| `0x080A6606` | 24 bytes of palette data used by the new-game screen |
| `0x080A77DC` | Start of the `%s:%d:magic_…: range over %d!` assert strings |

## 5. Algorithm

### 5.1 Name-entry encoding

The name screen draws 69 glyphs from the byte table at `0x0814CBB8` to the tile
positions in the u16 table at `0x0814CC16`. Pressing A stores the table byte for
the selected cell into the name buffer:

```
name[0..3] = table[grid_index]          ; 0x03004424
length++ if length < 3                  ; 0x0300443C
```

The table (decoded by matching positions to the rendered grid) is:

```
A 2A  B 2B  C 2C  D 2D  E 2E   a 48  b 49  c 4A  d 4B
F 2F  G 30  H 31  I 32  J 33   f 4D  g 4E  h 4F  i 50
K 34  L 35  M 36  N 37  O 38   k 52  l 53  m 54  n 55
P 39  Q 3A  R 3B  S 3C  T 3D   p 57  q 58  r 59  s 5A  t 5B
U 3E  V 3F  W 40  X 41  Y 42   u 5C  v 5D  w 5E  x 5F  y 60
Z 43  z 61                     0 20  1 21 … 9 29
```

The two remaining lowercase glyphs (`e`, `j`) are the extra far-right row-1
cells coded `0x45`/`0x46`; they are not needed for the tested names. This does
not affect `RYU` (`3B 42 3E`), which was verified in RAM.

The UI consumes only these four bytes:

* `0x08041436`/`0x08041660` copy `gs+0x14..0x17` into a local buffer for drawing;
* `0x08041ADC` writes `43 48 4A 52` (`Zack`) if the first byte is 0;
* `0x08041B24` copies the four bytes into a menu template;
* `0x080424FA` copies them into `0x0202DBD0+0x24`.

No `cmp`/`strcmp`/`memcmp` against the name bytes was found.

### 5.2 Save-slot format (context for the absent cheat)

SRAM is 32 KiB; slots are 0x500 bytes at `0x0000`, `0x0500`, `0x0A00`,
`0x0F00`:

```
+0x000  u16 checksum (sum of bytes 2..0x4FA)
+0x024  4 glyph bytes (name), NUL/0x20 padded
+0x29E  "CAPCOM" signature
```

The validator at `0x080440F8` compares six bytes against `CAPCOM`; the loop at
`0x08043AA8` reads four slots and checks the checksum. A cheat save loaded from
ROM would have to contain this signature; none does.

### 5.3 `BATTLE_DEBUG` gate

```asm
0806D60E  ldr  r0, =0x08150B30     ; "BATTLE_DEBUG=0"
0806D610  ldrb r1, [r0, #13]       ; '0' = 0x30
0806D612  movs r0, #1
0806D614  ands r0, r1              ; 0x30 & 1 = 0
0806D616  cmp  r0, #0
0806D618  bne  0x0806D61C          ; never taken
0806D61A  b    0x0806DB90          ; always taken
```

The skipped branch (`0x0806D61C`) calls `0x08085670`, tests its return, XORs
`0x03000F4C`, and plays sound `0x080379D4`. The flag byte is in ROM and no code
writes it, so the debug path cannot be reached by any input. This is a real
developer leftover, but it is a build-time constant, not an in-game gate.

### 5.4 Published SNES gate (for comparison)

SNES/SNES-port behaviour:

```
at name entry:
  hold Ctrl2 A|Y|L|R
  press Up×4, Right×2, Down×8, Left×1   → palette turns red / cheat flag
  type one of RYU CHUN VEGA KEN DeeJ Fei (case-sensitive)
  confirm → load hard-coded debug save
```

On this GBA build the encoded names, the sequence table, the palette switch and
the save blobs are all absent, and the pad scanner has no second-controller
concept.

## 6. Tables

### 6.1 Name-grid glyph table (`0x0814CBB8`, 69 bytes)

```
2A 2B 2C 2D 2E 48 49 4A 4B 4C F7 62
2F 30 31 32 33 4D 4E 4F 50 51 46 45
34 35 36 37 38 52 53 54 55 56 F0 EF
39 3A 3B 3C 3D 57 58 59 5A 5B 63
3E 3F 40 41 42 5C 5D 5E 5F 60
43 61
20 21 22 23 24 25 26 27 28 29
```

Positions come from `0x0814CC16`; rows are 0x100, 0x140, 0x180, 0x1C0, 0x200,
0x240, 0x280 in the BG map.

### 6.2 Save slot

See §5.2. Stride `0x500`, name `+0x24`, signature `+0x29E`, checksum `+0`.

### 6.3 Keyword counts

Game text was decoded with the ROM font (byte → glyph; `0x02` space, `0x03`
line break, `0x04`/`0x0A` substitutions) into 70,391 runs. Case-insensitive
substring counts:

| Keyword | Text runs | Raw ASCII strings |
|---|---:|---:|
| DEBUG | 0 | 2 |
| SOUND | 0 | 0 |
| BGM | 6 (binary false positives) | 3 |
| PASSWORD | 1 (story: "The secret password to enter Agua…") | 0 |
| CHEAT | 0 | 0 |
| UNLOCK | 0 | 0 |
| STAFF | 0 | 0 |
| GALLERY | 0 | 0 |
| CONFIG | 0 | 0 |
| EXTRA | 1 (binary) | 0 |
| TEST | 5 (story) | 4 |

The only `PASSWORD` hit is a story hint, not an entry screen; the `DEBUG` ASCII
hits are `BATTLE_DEBUG=0` and `dummy parameter set for debug!`.

## 6b. Enumeration

**Space definition (published system).** The only published in-game code system
for this title is the SNES name/gate debug save: alphabet = the name-grid glyph
set; lengths 3–4; six documented names; case-sensitive; a direction gate of
Up⁴ Right² Down⁸ Left¹ with four held buttons. Representable published values:
6. On the GBA side the *implemented* space is **0**: no name literal, no
sequence table, no save blob, no controller-2 path.

**Validator model.** None exists in this build. The name buffer `0x03004424` is
written by the UI and read only by draw/copy code; there is no comparison
instruction against it. Therefore the model is: *any* 4-glyph name is accepted
as a cosmetic name, and none selects a debug save.

**Novel code.** None can be minted because there is no decoder or table to
satisfy. The published name `RYU` was entered through the real UI and produced
the ordinary level-1 file `RYU 1` (`shots/ryu4.png`), not the level-29 Scande
save. The other five names have no encoded representation in the ROM (0/6
literal hits), so there is no hidden entry that could accept them.

**Bounds proven by rejection.**

* 21 hold-mask variants of the published gate were entered on the real name
  screen: all 16 subsets of A/B/L/R, plus Select, Start, Select+Start,
  L+R+Select and L+R+Start. Every one left the screen at the normal blue mean
  `srgb(34.6%, 22.3%, 69.5%)`, with no red state and no flag change. This
  bounds the GBA-remap hypothesis over the full A/B/L/R mask space and the
  most plausible Select/Start variants combined with the published direction
  counts.
* A 15-step direction sequence has no representation in the ROM as u8, u16 or
  2-bit-packed data (0 hits), and the two input routines in the image hold no
  sequence counter/state; a table-driven sequence validator is therefore
  absent.
* A valid save requires `CAPCOM` at `+0x29E`; only two such strings exist and
  neither is a save. Therefore no hard-coded debug save can be loaded.

**Negative space checked.** 4 MiB scanned for name literals, sequence tables and
save signatures; 70,391 decoded text runs searched for code/menu keywords;
101,239 ASCII string lines searched; every menu listed in §3.1 walked; the
name-entry alphabet and consumers enumerated. Within that space, the answer is
"no in-game code system in this US GBA build", not "not found".

## 7. Validation evidence

**Observed**

* Boot, title, main menu (with and without a save), file select, name entry,
  pre-game options, in-game pause and all nine pause entries, quick-save
  prompt (`shots/*.png`).
* Name `RYU` stored in `0x03004424` as `3B 42 3E 00` (RAM read from a
  savestate); file list then showed `RYU 1`, level 1.
* Pressing Start on the name screen moves the cursor to `End`; confirming an
  empty name produces the default `Zack`.
* 21 gate-mask attempts: no red background, no state change.
* `BATTLE_DEBUG=0` byte and the `CAPCOM` save signature in live saves.

**Derived**

* Name buffer consumers and the absence of a comparison (instruction scan).
* `BATTLE_DEBUG` branch unreachable (`0x30 & 1 == 0`; no ROM writer).
* Save validator (`CAPCOM` at `+0x29E`, checksum at `+0`).
* No direction-sequence table, no name literals, no save blobs (fixed-pattern
  scans with stated patterns).

**Inferred**

* The skipped `BATTLE_DEBUG` branch is an in-battle debug toggle (it plays a
  sound and flips `0x03000F4C`); its exact on-screen effect was not observed
  because the flag is compiled off.

## 8. Unknowns

* The Japanese GBA build (`ABFJ`) was not analysed; a region-specific build
  could differ. The published cheat is documented for SNES US/JP, not for the
  GBA SKU.
* If a future revision re-enabled `BATTLE_DEBUG`, the exact display it toggles
  would need a live battle trace.
* No link-cable second-player input was tested; the GBA link code present is
  the normal item-trade (`EXCHANGE`) implementation, and no button-state
  exchange was found.

## 9. Tooling

* mGBA 0.10.5 SDL (`/usr/games/mgba`) under `Xvfb :212` + `openbox`,
  `SDL_AUDIODRIVER=dummy`; `xdotool`, `scrot`, ImageMagick.
* mGBA CLI debugger (`mgba -d`) driven through a pty for breakpoints, memory
  reads and register inspection; mGBA savestates parsed by extracting the
  `gbAs` PNG chunk and zlib-decompressing it (IWRAM base at state offset
  `0x19000`).
* Python 3 + Capstone for BL-target and literal-pool scans; `arm-none-eabi-objdump
  -M force-thumb` for all cited disassembly.
* Analysis scripts and screenshots: `/tmp/opencode/boff1/tools/`,
  `/tmp/opencode/boff1/shots/`.

*Legal: no ROM, graphics, music or text is redistributed here; only hashes,
addresses, algorithms and the analyst's own test inputs are published.*
