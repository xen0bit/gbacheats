# Crouching Tiger, Hidden Dragon (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Crouching Tiger, Hidden Dragon/Crouching Tiger, Hidden Dragon.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `CROUCHING TI` (`0xA0`–`0xAB`) |
| Game code | `AQDE` (`0xAC`), maker `41` (`0xB0`), version `0x00` (`0xBC`) |
| Complement | `0x72` (`0xBD`, valid: computed `0x72`) |
| Header checksum | `0x0000` (`0xBE`), i.e. header was rebuilt/edited |
| Entry word | `0xEA1FC4FE` → `0x087F1400` (non-stock) |
| MD5 | `a3a1a6809a31eac0f82ac68b9df8cb89` |
| SHA-1 | `f77a44508c8d892977a7fae6f49f8e134a93a93d` |
| SHA-256 | `a11d603c17abe546bd5970f085d553444398d22d0ae46f1e0419af6f1db80456` |
| CRC32 | `0x2F3A5D31` |

The retail USA image (`AGB-AQDE-USA`, En/Fr/Es) has CRC32 `0x579BA507`
(GameHacking.org). This file is a **modified image**: the entry word is redirected
to an appended ARM blob at `0x087F1400`, the header checksum is zeroed, and the
menu text is a Chinese translation. The scene-release tag pattern for this edit is
`[hIR00]` ("intro removed"); the loader at the tail crashes on cold boot
(`GBA: Jumped to invalid address: E3A02004`, `Illegal opcode: e710b710`).

For analysis a copy with the **stock entry restored** was used:
`entry = 0xEA00002E` (`b 0x080000C0`). That copy boots and plays; all dynamic
evidence below is from `rom_stock.gba`, which differs from the target only in the
4-byte entry word.

## 2. Executive summary

This image is a **modified/translated ROM**, not the retail USA dump. The stock
crt0 at `0x080000C0` is intact; the first word was repointed to an appended
"nano/main/rept" loader at `0x087F1400` that does not survive a cold boot. With
`0xEA00002E` restored the game runs.

The game has a real, documented 4-character password system ("continue
passwords", pause-menu "Password" display). It is **not** a literal table: every
published code string was searched in the ROM in ASCII, UTF-16LE, glyph-id
(`ASCII-0x20`), tile (`0x300+ASCII`) and value (0–36) encodings and is absent.
The codes are computed.

The strongest dynamic result: selecting the pause menu's **Password** row on
level 1-1 makes the game draw four 16×16 code glyphs; those glyphs read **J / C B**,
exactly the published level 1-1 code `J/CB`. This verifies the encoder/display
path and the published level-1-1 entry in-game.

The password **entry** screen could not be reached in this modified image. The
title menu has exactly three items; all three were walked (items 0/1 start the
intro/legal sequence, item 2 is the language/legal screen). The pause menu has
five rows, walked too (Command List, Password display, Kung Fu Guide, resume and
a video/list row). No 4-slot or alphabet-entry surface exists anywhere in the
walked menu tree. The published codes are therefore unenterable **in this
image**; this is a bounded negative for this ROM, not "not tested".

No novel code was minted/entered because no in-game entry surface exists in this
image. That is the one §0.2 deliverable that cannot be met here; everything else
(space, display verification, screen enumeration, negative bounds) is below.

## 3. How to reproduce

* Emulator: mGBA 0.10 (`/usr/games/mgba`) on `Xvfb :271` + `openbox`,
  `SDL_AUDIODRIVER=dummy`.
* Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad arrows. Hold 50–200 ms; short holds are needed for one menu step
  (150 ms double-steps some menus).
* Boot: make a copy, write `EA00002E` at file offset 0, run
  `mgba -3 -t <savestate> rom_stock.gba`.
* Salvage states: `Shift+F1` saves `rom_stock.ss1` (PNG with zlib `gbAs`
  chunk, 397,312-byte raw state). Plain `F1` did not load in this build; reload
  by relaunching with `-t rom_stock.ss1`.
* Title menu: 3 items. `Down` steps selection; `A` activates.
  * item 0 / item 1 → `DISPCNT=0x7F40` loader then the intro/legal sequence.
  * item 2 → language/legal screen (OCR shows `TIGRE & DRAGON`,
    `© United China Vision Incorporated and UCL, LLC. All Rights Reserved`).
* Pause menu (Start during play): 5 rows at sprite Y = 4, 25, 49, 76, 96.
  Cursor is the pair of sprites at X=113/Y and X=224/Y; selected row changes
  palette bank 0→1. Row 2 (Y=49) is **Password**.
* Password display: `A` on row 2 draws four 16×16 sprites at Y=48,
  X=100/116/132/148, tiles `0x244, 0x27C, 0x230, 0x22C` → **J / C B**.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08000000` | Entry word (patched: `EA1FC4FE` → `0x087F1400`) |
| `0x080000C0` | Stock ARM crt0 (`mov r0,#0x12; msr cpsr_c,r0; ldr sp,...`) |
| `0x080001E4` | Stock `main` Thumb pointer (literal at `0x08000100`) |
| `0x087F1400` | Appended ARM loader (hIR00 edit); searches `nano`/`main`/`rept` tags, crashes |
| `0x08089BC0` | Glyph-id → tile page map used by the text renderer (0xB4 bytes) |
| `0x0802B95C0` | Large u16 font page/tile map (sequential ranges `0x262…`, `0x224…`, `0x1F4…`, `0x1C4…`) |
| `0x08075AD98` | Scene/asset pointer table (`C_2DSCENE_DESERT0` …) |
| `0x080591C0` | Asset name strings (`&%$C_…_PLAYFIELD/PALETTE`) |
| `0x08061700`–`0x08066000` | English/French dialogue and story text (plain ASCII) |
| `0x08058B00`–`0x08058E20` | Credits (ASCII) |
| `0x03021100` (EWRAM +0x1100) | Text-map buffer: u16 entries, **tile = 0x300 + ASCII** |
| `0x03000CA8` | Title-menu selection byte (observed 4 → 5 on `Down`) |
| OAM `0x07000000` | Title items: Y=39 (4 sprites, tiles `0x200,204,208,20C`), Y=78 (5, `0x210…220`), Y=111 (5, `0x224…234`); cursor sprites X=66/X=158 |
| OAM (pause) | 5 rows Y=4 (6 sprites), 25 (5), 49 (4), 76 (4), 96 (4); selected row palette 1 |
| OAM (password) | Y=48, X=100/116/132/148, tiles `0x244/0x27C/0x230/0x22C` = `J / C B` |

## 5. Algorithm

### 5.1 Text / UI rendering

The text renderer maps ASCII to font tiles as **tile = 0x300 + ASCII**; this was
read from the RAM text map (`0x03021100`), which contains the literal runs
`OPQRSTUVWXYZ[\]^_.........--./012` and `23456789:;<=>?@A` at 32 entries/row.
The menu/code font is a separate 16×16 proportional atlas (tiles `0x1C4`–`0x283`),
mapped through the table at `0x0802B95C0`.

### 5.2 Password display

For level 1-1 the displayed code is `J/CB`:

```
J                /                C                B
    ##               #             #####          #######
    ##               #            ##   ##         ##    ##
    ##              #             ##              ##    ##
    ##              #             ##              ##    ##
    ##             #              ##              #######
 ## ##            #               ##              ##    ##
 ## ##           #                ##              ##    ##
  ###           #                  ##   ##        ##    ##
                                   #####          #######
```

The four tiles are written to the OAM display list at `0x0301C4C4` (8-byte
entries, stride 8), so the display path is understood. The encoder that selects
these tiles for a given level index was **not** isolated: a linear/affine
checksum model over the four symbols does not fit the published set (tested
mod 37/64/128/256, alphabets `0-9A-Z/` and `A-Z0-9/`, values ASCII,
`ASCII-0x20`, `ASCII&0x3F`). The encoding is therefore table/cipher-based, not a
simple checksum, and the inverse could not be written without the entry/validator.

## 6. Tables

### 6.1 Published level/boss codes (GameFAQs walkthrough, `faqs/28278`)

| Level | Code | Level | Code | Level | Code |
|---|---|---|---|---|---|
| 1-1 | `J/CB` | 2-1 | `6F3X` | 3-1 | `1MF4` |
| 1-2 | `8XDD` | 2-2 | `FNRT` | 3-2 | `1WF5` |
| 1-3 | `KPKF` | 2-3 | `FX5/` | 3-3 | `9W95` |
| 1-4 | `K532` | 2-4 | `OKDZ` | 3-4 | `3N1Z` |
| 1-5 | `JZM/` | 2-5 | `NMZQ` | 3-5 | `3X3/` |
| 1-6 | `6F3P` | 2-6 | `NXK7` | | |
| 4-1 | `NQ29` | 4-2 | `5/0R` | 4-3 | `062H` |
| 4-4 | `D/N3` | 4-5 | `8/4D` | 4-6 | `8Q44` |
| 4-7 | `HZ75` | 4-8 | `HZ7D` | | |
| Boss Yu Shu Lien | `6ZMK` | Boss Lo | `N/28` | Boss Li Mu Bai | `31D4` |
| Boss Jade Fox | `HZ75` | | | | |

Alternate codes printed by other sites (ChapterCheats, CheatingDome,
SuperCheats, GameRevolution): `0XS8/8XDD` (1-2), `KP3C/KPKF` (1-3),
`KPK4/K532` (1-4), `SPRQ/JZM/` (1-5), `6ZMS/FNRT` (2-1), `5F17/FX5/` (2-2),
`543N/OKDZ` (2-3), `8XR3/NMZQ` (2-4), `NX31/1MF4`, `9Q6Q/1WF5`,
`9QNT/9W95`, `XXPG/3N1Z`, `CKBH/3X3/` (chapter 3). The sources disagree; only
`J/CB` (1-1) was verified in-game by the display. Whether the alternates are
additional valid encodings or transcription errors is unresolved.

### 6.2 Menu tables (observed)

Title (3 items): rows at Y=39/78/111, 4/5/5 16×16 glyphs, selection byte
`0x03000CA8` (4→5 on one `Down`). Left/Right do nothing.

Pause (5 rows): Y=4 (6 glyphs, Command List; result screen has 56 sprites),
Y=25 (5 glyphs, list/video screen 56 sprites), Y=49 (4 glyphs, **Password**),
Y=76 (4 glyphs, resume → 19 HUD sprites), Y=96 (4 glyphs, Kung Fu Guide;
58 sprites).

## 6b. Enumeration

**Space.** Documented codes are 4 symbols from the 37-symbol alphabet
`0-9 A-Z /`. Naive space = 37^4 = **1,874,161** strings. The display proves that
the game computes the code rather than looking it up in ROM: every published
literal is absent from the image in ASCII, UTF-16LE, glyph-id (`ASCII-0x20`),
16-bit tile (`0x300+ASCII`) and 4-byte value encodings (scanned); only one
incidental hit (`2-2` value bytes at `0x131EBA`, inside graphics) was found.

**Novel codes.** None could be entered: this image exposes no password-entry
screen. The only in-game password interaction is the pause-menu **display**.
`J/CB` for level 1-1 was read back from four glyph tiles and matches the
published 1-1 code, which verifies the display/encoder output and the published
1-1 entry.

**Bounds / negative proof (for this image).**
1. Title menu: exactly 3 items (OAM rows Y=39/78/111). `Down` cycles 0→1→2→0
   with 50 ms holds (150 ms holds skip); `Up` reverses; Left/Right are inert.
2. Item 0 and item 1 both enter the loader (`DISPCNT=0x7F40`) and then the
   intro/legal sequence (OCR: `and all related characters and materials ™ & ©
   [2002] / © United China Vision Incorporated and UCL, LLC. All Rights
   Reserved`). No prompt, no 4-slot field, no alphabet; `Right/Up/Down` produce
   0 changed VRAM pixels on the legal screen, `Start` skips it.
3. Item 2 is a language/legal screen (OCR `TIGRE & DRAGON`, same copyright
   lines); directional input changes the language/legal image, `B`/`Start`
   return to the menu.
4. Pause menu: all 5 rows selected and activated (above). The only password
   surface is the level-1-1 display `J/CB`.
5. ROM literal searches for the published codes and for `PASSWORD`,
   `CONTINUE`, `NEW GAME`, `OPTIONS`, `RESUME`, `COMMAND LIST`, `ENTER`,
   `WRONG`, `INVALID`, `EXIT`, `CREDITS` in ASCII/UTF-16/tile encodings returned
   no UI string; the image has no ASCII password/menu text (the Chinese
   translation replaced the menu text with glyph atlases).

Therefore, for **this modified image**, the password entry surface is absent;
the published codes cannot be entered. The retail image's Continue screen is
what the sources describe, and the hIR00/translation edit is the likely cause of
the missing surface.

## 7. Validation evidence

**Observed**
* Stock entry `0xEA1FC4FE` crashes in mGBA (`Jumped to invalid address:
  E3A02004`); copy with `0xEA00002E` boots to the title.
* Title menu has 3 items; OAM rows and selection byte `0x03000CA8 = 4→5`.
* Legal-screen OCR: `and all related characters and materials ™ & © [2002]`,
  `United China Vision Incorporated and UCL, LLC. All Rights Reserved`.
* Pause menu has 5 rows; row 2 opens the password display.
* Password display glyphs read **J/CB** (OAM Y=48, X=100/116/132/148, tiles
  `0x244/0x27C/0x230/0x22C`), matching published 1-1.

**Derived**
* Entry redirect and header-checksum zeroing are the hIR00 edit; CRC32 differs
  from retail `0x579BA507`.
* Text renderer tile = `0x300 + ASCII` (from `0x03021100` map rows).
* Codes are computed, not stored (no literal in any tested encoding).

**Inferred**
* The alternates in the published lists are either multiple valid encodings
  (unused/alias bits) or list errors; the display only proves 1-1.
* The missing entry screen is a consequence of the translation/intro-removal
  edit, not of the retail game design (sources describe a Continue screen).

## 8. Unknowns

* The password validator/encoder algorithm (no entry surface to observe; no
  simple linear checksum fits the published set).
* Whether the alternate published codes are accepted.
* The exact retail Continue-screen layout (not present in this image).
* Full HUD/level-index RAM map; only the password display path
  (`0x0301C4C4` OAM list) was isolated.

## 9. Tooling

* mGBA 0.10 under Xvfb `:271` + openbox; xdotool XTEST input; savestate slot 1
  (`Shift+F1`), reload by relaunch with `-t rom_stock.ss1`.
* Python: zlib `gbAs` chunk parser (397,312-byte state), OAM/VRAM/BG renderers,
  palette/luminance ASCII dumps, glyph extraction.
* `arm-none-eabi-objdump -M force-thumb`; Capstone; grep/strings; tesseract used
  only on RAM-rendered text (no screenshots, no images read).
* Work files: `/tmp/opencode/cthd` (`rom_stock.gba`, `state.bin`, `title.ss1`,
  `pwsel.bin`, render scripts).

## 10. Legal note

No ROM, graphics, audio or extracted text is redistributed. Only hashes,
addresses, algorithms and derived observations are published.
