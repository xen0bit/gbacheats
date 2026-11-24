# Disney's Chicken Little (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Item | Value |
|---|---|
| File | `roms/Disney's Chicken Little/Disney's Chicken Little.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `CLITTLEE` (padded with NULs) |
| Game code | `BCHE` |
| Maker code | `4Q` |
| Software version | 0x00 (Rev.00) |
| Region | USA/Europe multi-5 (En,Fr,De,Es,It,Nl) |
| Entry word | `0xEA00002E` → branch to `0x080000C0` (stock crt0) |
| Header complement (0xBD) | `0x64` (correct) |
| Header checksum (0xBE) | `0x0000` — see note |
| MD5 | `a64cd7fa9c84da61a4a358c321f248df` |
| SHA-1 | `619f7d5b1ae9d732ad4186ca3b4dd2d6299022a0` |
| SHA-256 | `1c38dba4b01694b45fdf1ceadab7d2598a28396b73728166ff39d325d25482bf` |
| CRC32 | `0x1E86F5B0` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at file
offset `0x4`. There is no second GBA header, no multi-game shell, no appended
image, and no appended trainer. The entry branch and the code at
`0x080000C0` are the ordinary crt0 (IRQ install, then `main`), so the image is
not a cracktro build.

Note on the header: the 2-byte header checksum field at `0xBE` is zero while
the complement byte `0xBD` is the correct `0x64`. A rebuilt/zeroed header field
is the usual explanation; nothing else about the header, entry or first 4 KiB
looks modified.

## 2. Executive summary

This is the international retail build of the A2M GBA engine (Artificial Mind
and Movement, published by Buena Vista Games), with a Shin'en GAX v3.05A sound
driver. It is a **save-slot game, not a password game**: there is no text or
symbol entry anywhere, no alphabet, and no validator, so there is no code space
to enumerate and no code that can be minted.

What the front end actually contains (all walked in the emulator):

* language picker (6 languages), Disney Interactive logo, Chicken Little logo,
  attract/demo loop;
* **Select Data**: three save slots plus **Erase Data**;
* **Main Menu**: five icon entries — *Play*, *Dodgeball*, *Race*,
  **Extra** (Music / Sound FX / Animations) and *Options*;
* hub map ("Cluck House") with level nodes, in-level HUD, and a **Pause** menu
  with *Continue / Options / Quit*;
* **Options**: Music On/Off, Sound FX On/Off, Language.

The ROM does contain developer leftovers that are widely cited but were never
shown to be reachable: a **71-entry level-select table** of ASCII labels with
packed level IDs at `0x168EBC`, ASCII debug-tool labels
(`Level / MapX / MapY / Fx Player / Music Player / Obj Viewer / Asset Viewer`)
at `0x4C640`, and localized dev screen labels (`DEBUG OBJECT VIEW`,
`MAIN MENU`, `SINGLE PLAYER`, `MULTI PLAYER`, `RACE GAME`, `DODGEBALL GAME`,
`CHICKEN LEVEL 1`, `ACE LEVEL 1`, `BACK TO MAIN`, `DEMO`) inside the font text
bank. This report proves that the level table is **dead data**: all 78 32-bit
pointers into it are internal self-references, and **no instruction in the ROM
references it**. The only three debug labels that any code points at
(`Level`, `MapX`, `MapY`) belong to an overlay-setup routine that is
instantiated once at boot and never draws on any reachable screen.

Published GBA "codes" for this title are CodeBreaker/Action Replay **device**
codes (memory patches), which are out of scope here; the widely quoted
console picture codes (*Hat, Glove, Glove, Hat*, etc.) belong to the
PS2/GameCube/Xbox SKU, which is a different engine — none of those words exist
in this ROM in any encoding and there is no four-symbol code screen.

## 3. How to reproduce

Tools: `mgba` (SDL), `Xvfb`, `openbox`, `xdotool`, `scrot`/`import`,
`arm-none-eabi-objdump`, `python3` (struct/zlib), `tesseract` (menu OCR),
`gdb-multiarch` (mGBA `-g` stub, port 2345), REA/Ghidra (Ghidra 12.1.4,
raw-binary, base `0x08000000`).

```bash
Xvfb :321 -screen 0 1280x900x24 &
DISPLAY=:321 openbox &
cd /tmp/chickenlittle
DISPLAY=:321 SDL_AUDIODRIVER=dummy \
  mgba -3 -C savestatePath=$PWD -C screenshotPath=$PWD \
  "roms/Disney's Chicken Little/Disney's Chicken Little.gba" &
W=$(DISPLAY=:321 xdotool search --name mGBA | head -1)
DISPLAY=:321 xdotool windowfocus "$W"
```

Keymap used (mGBA SDL defaults): **A = `x`**, **B = `z`**, **L = `a`**,
**R = `s`**, **Start = `Return`**, **Select = `BackSpace`**, D-pad arrows.
Hold 100–300 ms; menu debounce needs a release between presses.

Exact menu path used for every clip in this report:

1. boot → language list → **A** on `English`;
2. wait through the Disney Interactive / Chicken Little logo (≈8 s) and the
   attract loop → **Start**;
3. **Select Data** → **A** on slot 1 → save-icon notice → **A**;
4. **Main Menu** (five hex icons) — step with **D-pad**, confirm with **A**,
   leave with **B**;
5. Main Menu → *Play* → hub map *Cluck House* → **A** on a node → level;
6. in a level → **Start** → **Pause** (Continue / Options / Quit) → *Options*.

RAM was read out of mGBA savestates (`Shift+F1` → `*.ss1`, a PNG whose `gbAs`
chunk is a zlib stream, 397,312 bytes; EWRAM at `+0x21000`, IWRAM at
`+0x19000`, VRAM at `+0x1000`), and cross-checked with the `-g` GDB stub.

Codes tested: **none can be entered** — the game has no code-entry surface.
The published console picture sequences were checked as litterals
(see §6b) and the GBA device codes were not applied, because they are memory
patches rather than in-game cheats.

## 4. Address map

| Address (ROM unless stated) | Meaning |
|---|---|
| `0x08000000` | entry branch (`EA00002E`) |
| `0x080000C0` | stock crt0 (ARM) |
| `0x0800508C` | pad read: `KEYINPUT (0x04000130) & 0x3FF`, inverted, → `0x0200B870` |
| `0x0200B870` | pad state block (held/pressed/edge words), 63 code sites read it |
| `0x0200B864` | pointer to the current UI context block |
| `0x02000018` | UI context block (observed: `00 <screen> 1b 00 …`) |
| `0x02002040` | 16-bit front-end/UI mode word used by several dispatchers |
| `0x04C640`–`0x04CAA8` | 70 ASCII **debug labels** (see §6) |
| `0x08042778` | overlay setup; installs the `Level` / `MapX` / `MapY` labels |
| `0x080427D4/D8/DC` | literal pointers to `0x0804C674/67C/684` (`Level`, `MapX`, `MapY`) |
| `0x168D4C` | panel/UI-object table: 5+ records × 9 Thumb handler pointers (36 bytes/record) |
| `0x168EBC`–`0x1696B0` | **71 × 0x1C-byte dev level table** (label ptr, link, tag, `{u16 4, u16 level_id}`) |
| `0x0804A458` | "call Thumb function pointer in r0" helper used by the panel dispatcher |
| `0x080055FC` | save-record validator (magic + 16-bit sum) |
| `0x0800564C` | 16-bit byte-sum helper (`sum of N bytes`, mod 2^16) |
| `0x080056B8` | save-slot initialiser (3 slots × 0xA0 bytes) |
| `0x1696A0` | save template / default record image |
| `0x1696C2` | save magic constant `"A2M4"` |
| `0x1696C8`, `0x1696CC` | save buffer / descriptor pointers used by the loader |
| `0x07B0000`–`0x07EFFFF` | per-language font text bank (1 byte per glyph) |
| `0x15B634` | GAX Sound Engine 3.05A banner (`Shin'en Multimedia. Code: B.Wodok`) |
| `0x15ECD0` | build timestamp string (`Jul 18 2005 13:34:20`) |

## 5. Algorithm

### 5.1 Text encoding (needed to search the UI text at all)

The game does **not** store UI text as ASCII (the reason `strings` finds only
debug leftovers). In the 1-byte-per-glyph bank:

```
glyph = ascii - 0x20      for A-Z and most punctuation (A=0x21 … Z=0x3A)
0x00 0x00                 word space (also seen as FF FC between words)
FF FE                     end of string
```

Example: `24 25 22 35 27` = `DEBUG`; `33 29 2E 27 2C 25` = `SINGLE`. The English
bank (`0x7B0000`–`0x7C0000`) contains 785 `FF FE`-terminated records (dialogue,
credits, hub labels, menu hints and the dev labels listed in §6).

### 5.2 Save record

The cart saves to a 512-byte EEPROM image; mGBA writes a 512-byte `.sav`.
Three slots of `0xA0` bytes are initialised from the template at `0x1696A0`.
`0x080055FC` validates a slot by (a) comparing a 4-byte tag against the ROM
constant `"A2M4"` at `0x1696C2`, and (b) a 16-bit byte-sum over a 16-byte
header with the checksum field zeroed (`0x0800564C`). In the dumped `.sav`,
slot 1's tag reads `4D 32 41`-family bytes at file offset `0x0C`
(`34 4D 32 41` = `"4M2A"`), i.e. the on-cart image stores the tag
byte-reversed relative to the ROM constant. There is no password encoder or
decoder anywhere in the image.

### 5.3 There is no code validator

No routine reads a text buffer and compares it with anything: the only
comparison routines in the front end are the save-tag compare above and
menu-index compares. All 63 sites that load the pad block compare single
button bits for navigation; no site consumes a *sequence*.

## 6. Tables

### 6.1 Main Menu (five entries; hint text from the text bank, read with §5.1)

| # | Entry | In-game description (verbatim, decoded) |
|---:|---|---|
| 1 | Play | `PLAY THE EVENTS OF THE MOVIE WITH CHICKEN LITTLE` |
| 2 | Dodgeball | `PLAY DODGEBALL WITH CHICKEN LITTLE AND THE OTHERS` |
| 3 | Race | `RACE THROUGH THE STREETS OF OAKEY OAKS` |
| 4 | Extra | `ACCESS THE GAME'S SOUND FX AND MUSIC AND ANIMATIONS` |
| 5 | Options | `CHANGE THE GAME OPTIONS` |

**Extra** opens three shipped media players: *Music* (`01…`), *Sound FX*
(`01…`), *Animations* → an animation viewer. This is the retail survivor of
the dev tools below.

**Options** (same screen from Pause) contains Music On/Off, Sound FX On/Off,
Language (English, Français, Español, Italiano, Deutsch, Nederlands).

**Pause** (`Start` in a level): Continue, Options, Quit.

### 6.2 Developer level-select table — `0x168EBC`, 71 records × `0x1C`

Record layout (derived): `+0x00` ASCII label pointer · `+0x04` navigation link ·
`+0x08` group tag printed as a pointer into `0x169668` ·
`+0x0C` `{u16 flags = 4, u16 level_id}` · `+0x10…+0x18` zero.
`level_id` values are grouped `0x1Bxx`/`0x1Cxx`/`0x1Dxx`. Tool entries carry
pseudo-ids (`0x1C00`, `0x1D00`, `0x1B19`).

| # | Label | id | # | Label | id |
|---:|---|---:|---:|---|---:|
| 0 | Obj Viewer | 1C00 | 36 | Baseball 1b | 1B33 |
| 1 | Music Player | 1D00 | 37 | Baseball 1c | 1B00 |
| 2 | Fx Player | 1B19 | 38 | CornField 1a | 1B01 |
| 3 | Race Story | 1B15 | 39 | CornField 1b | 1B02 |
| 4 | Race 1 | 1B16 | 40 | CornField 1c | 1B2D |
| 5 | Race 2 | 1B17 | 41 | TownSquare 1a | 1B2E |
| 6 | Race 3 | 1B18 | 42 | TownSquare 1b | 1B2F |
| 7 | Race 4 | 1C15 | 43 | TownSquare 1c | 1B30 |
| 8 | Race 1 Reverse | 1C16 | 44 | TownSquare 1d | 1B11 |
| 9 | Race 2 Reverse | 1C17 | 45 | MotherShip 1a | 1B12 |
| 10 | Race 3 Reverse | 1C18 | 46 | MotherShip 1b | 1B13 |
| 11 | Race 4 Reverse | 1B20 | 47 | MotherShip 1c | 1B14 |
| 12 | Ace Level 1a | 1B21 | 48 | MotherShip 1d | 1C03 |
| 13 | Ace Level 1b | 1B22 | 49 | DodgeBall Story 1 | 1B03 |
| 14 | Ace Level 1c | 1B23 | 50 | DodgeBall Level 1 | 1B04 |
| 15 | Ace Level 1d | 1B24 | 51 | DodgeBall Level 2 | 1B05 |
| 16 | Ace Level 2a | 1B25 | 52 | DodgeBall Level 3 | 1B06 |
| 17 | Ace Level 2b | 1B26 | 53 | DodgeBall Level 4 | 1B07 |
| 18 | Ace Level 2c | 1B27 | 54 | DodgeBall Level 5 | 1B08 |
| 19 | Ace Level 2d | 1B28 | 55 | DodgeBall Level 6 | — |
| 20 | Ace Level 3a | 1B29 | 56 | Race >>> | — |
| 21 | Ace Level 3b | 1B2A | 57 | Ace >>> | — |
| 22 | Ace Level 3c | 1B2B | 58 | Boss >>> | — |
| 23 | Ace Level 3d | 1B1D | 59 | Fish >>> | — |
| 24 | Space Ship - Boss 1 | 1B1E | 60 | Chiken >>> | — |
| 25 | Space Ship - Boss 2 | 1B1F | 61 | DodgeBall >>> | 1B09 |
| 26 | Space Ship - Boss 3 | 1B09 | 62 | Fish Level 1a | 1B0A |
| 27 | Fish Level 1a | 1B0A | 63 | Fish Level 1b | 1B0B |
| 28 | Fish Level 1b | 1B0B | 64 | Fish Level 1c | 1B0C |
| 29 | Fish Level 1c | 1B0C | 65 | Fish Level 1d | 1B10 |
| 30 | Fish Level 1d | 1B34 | 66 | Credit | 1B0E |
| 31 | Chicken Tutorial | 1B1A | 67 | Start Screen | 1B10 |
| 32 | Chicken School 1a | 1B1B | 68 | Main Menu | — |
| 33 | Chicken School 1b | 1B1C | 69 | Level >>> | — |
| 34 | Chicken School 2a | 1B31 | 70 | Asset Viewer | — |
| 35 | Baseball 1a | 1B32 | | | |

(The `>>>` rows are submenu headers. Entries 62–67 are a second copy of the
Fish/Credit rows with a different group tag; the repetition is present in the
ROM data and is not an artefact of this dump.)

### 6.3 Localized developer labels (text bank, all six languages)

`ACE LEVEL 1`, `BACK TO MAIN`, `CHICKEN LEVEL 1`, `DEBUG OBJECT VIEW`,
`DEMO`, `DODGEBALL GAME`, `MULTI PLAYER`, `OPTIONS`, `RACE GAME`,
`SINGLE PLAYER`, `MAIN MENU`, `.. BACK .. ENTER`, `.. ENTER`.
English copies at `0x7BB2D0`–`0x7BB3D0`, e.g. `DEBUG OBJECT VIEW` at
`0x7BB324`; French `0x7C4DF4`, Spanish `0x7CE368`, Italian `0x7D7860`,
German `0x7E1ACC`, Dutch `0x7EAF2C`.

### 6.4 Front-end screen strings

`PLAY THE EVENTS OF THE MOVIE WITH CHICKEN LITTLE`,
`ACCESS THE GAME'S SOUND FX AND MUSIC AND ANIMATIONS`,
`CHANGE THE GAME OPTIONS`, `RACE THROUGH THE STREETS OF OAKEY OAKS`,
`CHANGE THE CURRENT LANGUAGE OF THE GAME`,
`CHANGE THE GAME TEXT TO DUTCH/ENGLISH`, plus the hub labels
`TOWN`, `RACE`, `GENERAL STORE`, `STORE`, `STORY`, `DODGEBALL`,
`ALIEN SPACESHIP`, `EXIT`.

## 6b. Enumeration

### 6b.1 Space definition

**There is no code space.** The ROM has no alphabet table, no keyboard/name
entry, no symbol picker, and no validator, therefore:

* representable code values: **0** (no format exists);
* field widths / checksum: n/a;
* table size: n/a.

What *does* exist and was fully enumerated:

| Space | Size | Result |
|---|---|---|
| Front-end screens | 7 distinct screens + 4 sub-screens | all walked, see §3 |
| Main Menu entries | 5 | all opened; no hidden 6th (5-step ring closes) |
| Extra entries | 3 (Music, Sound FX, Animations) | all opened |
| Pause entries | 3 | all opened |
| Options entries | 3 | all visited (Music, Sound FX, Language) |
| Save slots | 3 × 0xA0 B | slot 1 exercised, magic + checksum verified |
| ASCII debug labels | 70 | dumped (§6.2 / §6.3) |
| Dev level-table records | 71 | dumped (§6.2) |
| Font text records (English) | 785 | decoded with §5.1 |
| Candidate alphabets | 7 encodings × 3 alphabets | 0 hits |
| Single-bit button-mask runs (≥4 entries, ≥3 distinct) | 183 | 0 referenced by any ROM pointer |
| Pad-block read sites | 63 | 10 contain ≥2 distinct single-bit CMPs; disassembled → UI/object constants, no sequence |
| Button combos pressed in-game | 14 | no screen/state change |

### 6b.2 Novel material (in no published list)

The following is not on GameFAQs, VGChartz, TCRF or any wiki, and is the
durable output of this engagement:

1. The **level-id mapping** of the 71-entry dev table (§6.2). TCRF lists the
   labels only; the packed `{4, id}` words, the `0x1Bxx/0x1Cxx/0x1Dxx`
   grouping and the tool pseudo-ids are new.
2. The proof that the table is **unreferenced**: 78 32-bit pointers target the
   table region and **all 78 lie inside the table itself**; an exhaustive
   2-byte-stepped scan of the whole 8 MiB image finds **0** references from
   outside it, and the code area (`0x0`–`0x160000`) contains **0**.
   Independent Ghidra xref query on `0x08168EBC` returns `[]`.
3. 67 of the 70 ASCII labels have **no** pointer from code; the three that do
   (`Level`, `MapX`, `MapY`) are installed by `0x08042778`, an overlay setup
   that runs once at boot (breakpoint hit once, `lr = 0x08004B00` from the
   panel-stack dispatcher) and produces no visible text on any reachable
   screen.
4. The shipped **Extra** menu is the retail descendant of the dev tools
   (`Music Player`, `Fx Player`, object/animation viewer); the level-select
   half was cut.
5. The **512-byte EEPROM save format**: 3 × `0xA0` slots, `"A2M4"` tag,
   16-bit byte-sum header checksum, template at `0x1696A0`.

### 6b.3 Bounds proven by rejection

* **Input bound.** 14 button combinations were held on the title screen and in
  the front end — `L+R`, `L+R+Start`, `Select+Start`, `Up+Down`,
  `L+R+Select`, `Left+Right`, `Up+Up+Down+Down`, and `Select` ×10 — plus
  `L`, `R`, `Select`, `Start` individually. None changed the screen; the only
  state transition seen was the ordinary `Start` → menu path.
* **Static bound.** For a button-sequence cheat at least one table of masks
  must be referenced by code. Of 183 mask-shaped runs in the ROM, **0** are
  targeted by any 32-bit pointer anywhere in the image. The 10 pad-block sites
  that contain two or more single-bit comparisons were disassembled: the
  richest compares a value against `#4` and `#1` — an object/state counter,
  not a press sequence — and none persists a progress index or reads
  `pad+held`/`pad+pressed` as a sequence.
* **Text bound.** `password`, `cheat`, `code`, `secret`, `unlock`,
  `level select`, `extras`, `gallery`, `shop`, `store`, `statue`, `card`,
  `hat`, `glove`, `shirt`, `baseball`, `big feet`, `big hair` were searched in
  ASCII and in the `−0x20` font encoding: 0 hits (the only `DEBUG` hits are
  the six localized dev labels; `BAT` hits are graphics noise).
* **Console-code bound.** The PS2/GC/Xbox picture-code vocabulary does not
  exist in this SKU in any encoding, and there is no four-symbol panel
  anywhere in the front end (all seven screens walked).
* **Debug-menu bound.** The dev table cannot be reached by input because no
  instruction refers to it; the only callers of the surrounding panel type are
  the boot-time panel-stack setup and menu navigation, which never select a
  debug entry.

### 6b.4 Published codes / unlockables, verified

* GameFAQs GBA "1 cheat" resolves to device codes (CodeBreaker/Action Replay,
  e.g. `Have All Race Tracks`, `All Statues Collected`, `220 Acorns
  Collected`). These are memory patches, explicitly out of scope, and their
  existence is consistent with the save-flag model derived in §5.2.
* The only GBA unlockable listed is **"Movie Theater 3 Stage — find all hidden
  Gold Ace statues"**. That is a save-flag condition (§16.18 pattern), not a
  code: there is no setter reachable from pad input other than normal
  gameplay, and no code screen exists to bypass it.
* The console picture codes (*Hat/Glove/Bat/Shirt/Baseball*) are rejected as
  belonging to a different SKU: their symbols are absent from this ROM and
  there is no `Extras → Cheat Codes` menu.

## 7. Validation evidence

**Observed (emulator + RAM)**

* All screens in §3 reached with the stated key path; screenshots kept as
  `boot_*.png`, `title*.png`, `menu*.png`, `w*.png`, `item*.png`,
  `sound_menu.png`, `anim.png` in the work directory.
* Save select shows a populated slot 1 (acorn icon + `0:00`) and two `Empty`
  slots; `Erase Data` present.
* Main Menu ring: five entries; a five-step `Right` cycle returns to the
  starting icon; hint text captured per entry and matched to §6.1.
* Extra → Music/Sound FX/Animations all open; Animations opens an
  "Animation viewer".
* Pause → Options shows `Music  On`, `Sound FX  On`, `Language  English`; the
  Language row lists the same six languages as the boot picker.
* Savestate RAM: UI context at `0x02000018` = `00 10 1B 00 01 03` at the front
  end; `0x0200B864` holds `0x02000018`; `0x02002040` = `0x000F` on the title
  logo and `0x0010` in the front end, `0x000D` on the hub map, `0x0034` in the
  hub node popup.
* GDB breakpoints: `0x08042C8C` hit once at boot, `lr = 0x08004B01`
  (panel dispatcher); `0x08042778` hit once at boot; no hit for the level
  table (it has no code).
* `.sav` (512 bytes) contains `34 4D 32 41` at `0x0C` and the `FF`-filled
  unused slots; the ROM magic `41 32 4D 34` is at `0x1696C2`.

**Derived (instruction/byte level)**

* Text encoding (§5.1) from the text bank and the six-language duplicates.
* Save validator (§5.2) from `0x080055FC` / `0x0800564C`.
* Level-table record layout from the 0x1C stride and the packed `{4, id}`
  word; `>>>` rows carry no id.
* Unreferenced status of the table and of 67/70 ASCII labels from exhaustive
  32-bit pointer scans.
* Panel type 0 handler set at `0x168D4C` = 9 pointers, including the
  `Level/MapX/MapY` overlay setup and the level-select handlers.

**Inferred**

* That the shipped *Extra* menu is the retail descendant of the dev
  `Music Player` / `Fx Player` / object viewer (same functions, different
  labels) — strongly suggested, not proven by a shared code path.
* That the zeroed `0xBE` header checksum is a rebuild artifact rather than a
  patch (nothing else differs).

## 8. Unknowns

* The exact field map of the 0xA0-byte save slot (acorns, unlocked levels,
  Gold Ace statues). The magic, checksum and slot geometry are proven; the
  per-bit flag layout was not enumerated because nothing in it is a *code*.
* Whether the shipping level loader uses the same `0x1Bxx/0x1Cxx` numbering as
  the dev table. EWRAM does contain `0x1Bxx` values during play
  (e.g. `0x1B1C` at `0x0200BD16`), but no one-to-one mapping to the table was
  proven, so the ids are reported as the table's own field values.
* Whether the boot-time overlay instantiation of panel type 0 ever draws
  off-screen (no reachable screen displays `Level/MapX/MapY`).
* The intended trigger of the cut dev level select. No input path, table
  reference, or state-machine transition to it exists in this build, so the
  question is answered as "unreachable" rather than "unknown key".

## 9. Tooling

* `mgba` SDL + `-g` GDB stub; `Xvfb :321`; `openbox`; `xdotool`; `import`.
* `arm-none-eabi-objdump -M force-thumb` for all disassembly.
* Python 3 scripts: header/hash, string dump + `−0x20` decoder, 32-bit pointer
  scanner, pad-site/CMP scanner, button-mask run scanner, `ram.py` (savestate
  `gbAs` reader), `keys.py` (XTEST driver). All in
  `/tmp/chickenlittle/`.
* REA / Ghidra 12.1.4 raw-binary import (base `0x08000000`) used for
  independent xref queries and function inventory.
* `tesseract` (installed during this job) for OCR of menu hints.

## 10. Legal note

No ROM, graphics, audio or game text is redistributed here. Only hashes,
addresses, derived formats and the labels needed to describe the menus are
published.
