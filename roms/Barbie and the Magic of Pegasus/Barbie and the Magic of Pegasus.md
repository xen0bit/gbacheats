# Barbie and the Magic of Pegasus (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-26.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Barbie and the Magic of Pegasus/Barbie and the Magic of Pegasus.gba` |
| Size | 4 MiB (`0x400000`) |
| Header title | `BARBIEPEGASU` |
| Game code | `BE5E` |
| Maker code | `7D` |
| Software version | `0` |
| Entry word | `0xEA00002E` (ARM branch to `0x080000C0`) |
| Complement check | `0x6B` (computed value also `0x6B`) |
| Header checksum field | `0x0000` (as stored; computed value would be `0x9D`) |
| MD5 | `c0f3e785f1d4a48fcb2b945291a033ef` |
| SHA-1 | `36e312abfaf7b9401e9f3d5b796f4ae07a10a09a` |
| SHA-256 | `62fddf0a7587df9387d10becea0ec8e64ed5dc884dcbfad68af8834c04ade129` |

Embedded-header scan: the 156-byte Nintendo logo occurs **once**, at file
offset `0x4`; this is a single GBA image, not a multi-game cart. There is no
data after `0x400000` and no second entry word.

Patch note: the header complement check is valid but the header-checksum field
is zero (the same convention appears in other dumps in this collection, e.g.
*Army Men Advance*). Nothing else indicates a patch: the entry branch, logo,
game code, string banks, password table and validator all match a retail
layout, and no trainer/menu strings were found. The ROM was analysed as-is.

The game created a 0-byte `.sav` and exposes no `CONTINUE`; progress is carried
by the password, not by battery-backed save data.

ROM addresses below are `0x08000000 + file_offset`.

---

## 2. Executive summary

The game has one password system, and it is a **literal table**, not an
algorithm.

* Main menu → **Password** opens a four-slot screen. Each slot cycles through
  **six picture symbols** (Palace, Ollie, Wenlock, Wand, Brietta/Pegasus,
  Annika). The UI space is therefore `6^4 = 1296` inputs.
* The validator compares the four stored symbol values, byte for byte, against
  a **34-entry table of 4-byte records at `0x08141878`**
  (`0x08019240`–`0x08019264`). There is **no checksum and no arithmetic**: an
  input matches iff its four values exactly equal one of the 34 rows; 32 of
  those rows start content and 2 are dead padding rows.
* The table is laid out as **17 Easy rows + 17 Normal rows**. The first row of
  each half is a dead padding row, leaving **16 levels × 2 difficulty variants
  = 32 usable codes**. The matched row index also selects the difficulty:
  rows 1–16 write `0` to `0x030000F4` (Easy), rows 18–33 write `1` (Normal).
  Easy games have no health meter; Normal games show three hearts.
* The 16 Easy codes are exactly the 16 public GameFAQs passwords (the page
  itself says "only Easy Mode"). The 16 Normal codes are published on
  speedrun.com (and four of them on a 2019 blog). **All 32 valid level codes
  are therefore public** — exhaustive enumeration proves there is no
  unpublished level code to mint. The two padding rows are the only table
  entries absent from every published list; they match the validator but are
  inert and the screen falls back to "Incorrect Password!".
* A public list also contains one wrong code: speedrun.com's "Palace 2
  (Easy)" (`Palace, Ollie, Brietta, Palace`) is rejected by the ROM; the
  correct GameFAQs code is `Palace, Ollie, Brietta, Ollie`.

The complete symbol→value mapping, the 34-row table, the level-character map,
the exact validator and the exhaustive 1296-case result are below.

---

## 3. How to reproduce

### Emulator

```bash
sudo apt-get install -y mgba-sdl xvfb openbox xdotool scrot imagemagick
Xvfb :169 -screen 0 1280x1024x24 &
DISPLAY=:169 openbox &
DISPLAY=:169 SDL_AUDIODRIVER=dummy mgba -3 "Barbie and the Magic of Pegasus.gba" &
```

Default mGBA keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
D-pad = arrows. Hold keys ~180 ms; menus debounce, and a 10 ms tap is missed.

### Menu path (observed)

```
Title (PRESS START)
└─ Game Mode
   ├─ New Game  → Difficulty Level → Easy Mode / Normal Mode → intro
   ├─ Password  → Enter Password: four picture slots
   └─ Arcade    → Arcade Games (8 slots; only "Pegasus Coin Collect" unlocked)
```

In-game, **Start** opens the pause menu: `Continue` / `Quit` (no options
screen exists).

### Password entry mechanics (observed)

1. On the password screen the four slots show Palace and the bar reads
   *Press Start to enter Password*.
2. **Start** submits the current four symbols. Submitting the default
   (Palace×4) produces *Incorrect Password!* and places the cursor on slot 1.
3. **Up/Down** cycle the selected slot through the six symbols (mod 6);
   **Left/Right** move between slots; **Start** submits again.
4. A valid code leaves the password screen and enters the level (or its
   cutscene/map); an invalid code stays on the screen with
   *Incorrect Password!*.

Savestate `pwbase.state` used by the harness is taken immediately after step 2
(a failed submit with Palace×4, cursor on slot 1). Every code test then costs
four slot edits plus Start.

### Headless, deterministic reproduction

For enumeration and screenshots the analysis used a small `libmgba` harness
(included as `Barbie and the Magic of Pegasus - mgba_harness.c`). It loads the
ROM, runs frames, presses keys, saves/loads states, dumps memory and writes
240×160 PPM screenshots:

```bash
gcc -O2 -o harness "Barbie and the Magic of Pegasus - mgba_harness.c" -lmgba -lm
./harness "Barbie and the Magic of Pegasus.gba" script.txt
```

Script commands: `wait N`, `press KEY`, `down/up KEY`, `save/load PATH`,
`dump PATH ADDR LEN`, `peek ADDR`, `peek16 ADDR`, `shot PATH`, `enum BASE OUT`.

The full enumeration was one `enum` command over `6^4 = 1296` codes with
`pwbase.state` reloaded before each code. The decoder/table dump is included as
`Barbie and the Magic of Pegasus - password_table.py`:

```bash
python3 "Barbie and the Magic of Pegasus - password_table.py" \
        "Barbie and the Magic of Pegasus.gba" 2 2 4 3
# [2, 2, 4, 3] (26, 61, 'Normal', "level char '<' -> screen 61 (Forest 2)")
```

### Screenshots (same folder)

| File | Shows |
|---|---|
| `Barbie and the Magic of Pegasus - title.png` | title screen |
| `... - main menu.png` | Game Mode / New Game / Password / Arcade |
| `... - difficulty level.png` | Easy Mode / Normal Mode |
| `... - arcade games.png` | 8-slot arcade grid, 7 locked |
| `... - password screen.png` | four-slot password screen |
| `... - symbol alphabet.png` | the six symbols in cycle order |
| `... - normal code entered.png` | Wenlock, Wenlock, Brietta, Wand |
| `... - normal code effect Forest 2.png` | that code starts Forest 2 with 3 hearts |
| `... - rejected near miss.png` | Palace, Ollie, Brietta, Wenlock → Incorrect Password! |
| `... - published typo rejected.png` | speedrun's "Palace 2 Easy" still on the password screen |
| `... - easy vs normal hearts.png` | Easy (no HUD hearts) vs Normal (3 hearts) |
| `... - pause menu.png` | Continue / Quit |
| `... - padding code entered.png`, `... - padding code no effect.png` | dead table row 0 |

---

## 4. Address map

| File offset | ROM address | What |
|---:|---:|---|
| `0x13ED88` | `0x0813ED88` | Debug screen-name registry, 19 records `{u32 id; char name[32]}` (stride 36) |
| `0x13F22C` | `0x0813F22C` | Level/cutscene-name registry (Cloud/Forest/Glacier/Village, minigames, flying, cinemas) |
| `0x141878` | `0x08141878` | **Password table: 34 × 4 bytes** (17 Easy, 17 Normal) |
| `0x141900` | `0x08141900` | Level-character table, 17 bytes: `012/9:;8<=>?,-.+3` |
| `0x018E58` | `0x08018E58` | Password slot input handler (Up/Down, mod 6) |
| `0x019014` | `0x08019014` | Handler for table rows 0/17 (padding; sets entities from `0x0300037C`) |
| `0x019240` | `0x08019240` | Validator: 4-byte compare against `0x08141878` |
| `0x019264` | `0x08019264` | Match: success flag `0x03000016 = 1` |
| `0x01926C` | `0x0801926C` | Easy branch (row ≤ 16): `0x030000F4 = 0`, level char, `0x03000015 = 4` |
| `0x0192FC` | `0x080192FC` | Row 17 check / Normal branch (row ≥ 18): `0x030000F4 = 1` |
| `0x019380` | `0x08019380` | Compare-loop tail (index 0…33) |
| `0x024EC4` | `0x08024EC4` | `mod` helper (used as `% 6`) |

RAM used by the screen (values read with the harness and GDB-style peeks):

| Address | Use (observed) |
|---|---|
| `0x030029A0` | Entity array, stride `0x54`, 32 entries; password slots are type `0x51` at `+0x22` |
| `+0x13` (entity) | slot index 0–3 (which of the four columns) |
| `+0x28` (entity) | stored symbol value 0–5 (see §5.2) |
| `0x03000014` | currently selected slot (0–3) |
| `0x03002A4B`, `0x03002A9F`, `0x03002AF3` | per-slot cursor/animation bytes (slot 1–3; slot 4 follows the same 0x54 stride) |
| `0x03002A70`, `0x03002AC4`, `0x03002B18` | per-slot symbol value copies (u16, mirrored 2 bytes later; slot 4 follows the stride) |
| `0x03000015` | state: `2` = password screen/idle, `4` = accepted, level starting |
| `0x03000016` | validator success flag (1 after a table match) |
| `0x03000018` | level character (from `0x08141900`) |
| `0x030000F4` | difficulty: `0` = Easy, `1` = Normal |
| `0x0300180C`, `0x03003654` | current screen id (two copies) |
| `0x0300037C` | level id used by the row-0/17 handler (0 in retail flow) |

The screen id is a useful detector: `9` = Password Menu, `11` = Difficulty
Menu, `4` = Title, `7` = Game Mode Menu (the Arcade Menu's registry id is
`0x0C`). A submitted code changes it to the level's id (see §6.3); a rejected
code leaves it at `9`.

---

## 5. Algorithm

### 5.1 Screen and submit

`0x08019240` is the core:

```
i = 0
loop:
  if table[i][0..3] == slot_value[0..3]:
      success_flag = 1
      if i == 0: goto padding
      if i <= 16:
          difficulty = 0            # Easy
          n = i - 1
          level_char = LEVEL_CHARS[n]
          state = 4                  # start level
          return
      if i == 17: goto padding
      difficulty = 1                # Normal
      n = i - 18
      level_char = LEVEL_CHARS[n]
      state = 4
      return
  i++
  while i <= 33
reject:
  show "Incorrect Password!"
```

`table` is `0x08141878`, 34 records of four bytes; `LEVEL_CHARS` is the 17-byte
string at `0x08141900`. There is no length, alphabet or checksum arithmetic —
the comparison is four literal bytes. Values 6 and 7 (the unused 3-bit codes
of each symbol) never appear in the table and cannot be entered by the UI.

### 5.2 Symbol alphabet and stored values

The UI cycles six icons in this order (Up). The value written to the entity is
**not** the display index: it runs the other way, `value = (-display) mod 6`.
This was read directly from `0x03002A70` for all six positions.

| Display index | Icon (public name) | Stored value |
|---:|---|---:|
| 0 | Palace / Castle | 0 |
| 1 | Ollie / Ogre (bald giant) | 5 |
| 2 | Wenlock (bearded man) | 4 |
| 3 | Wand of Light (sparkle) | 3 |
| 4 | Brietta / Pegasus | 2 |
| 5 | Annika / Anika / Barbie | 1 |

Input handler `0x08018E58`: on Up, `value = (value + 1) % 6`; on Down,
`value = (value + 5) % 6` (the `% 6` call is `0x08024EC4`). It only reacts when
the entity's slot index (`+0x13`) equals the cursor (`0x03000014`).

### 5.3 Difficulty is carried by the code

Rows 1–16 (Easy) set `0x030000F4 = 0`; rows 18–33 (Normal) set it to `1`.
This was confirmed against the difficulty menu: New Game → Easy writes `0`,
Normal writes `1`; Easy gameplay has no hearts, Normal shows three hearts
(`... - easy vs normal hearts.png`). The validator writes the difficulty from
the row index and never reads the previous value — the code itself selects it.

### 5.4 Level character

Each non-padding row also stores a character from the 17-byte table:

```
n:            0    1    2    3    4    5    6    7    8    9   10   11   12   13   14   15   16
char:        '0'  '1'  '2'  '/'  '9'  ':'  ';'  '8'  '<'  '='  '>'  '?'  ','  '-'  '.'  '+'  '3'
screen id:   49   50   40   18   58   59   39   19   61   62   38   20   45   46   37   13   (unused)
```

The character is stored at `0x03000018`; a later loader turns it into the
screen id at `0x0300180C`. The final `'3'` is never used by any table row.
The Easy and Normal halves use the same 16 characters, so the character is the
level number, not the mode.

### 5.5 Padding rows

Rows 0 and 17 (`Ollie,Ollie,Wand,Annika` and `Annika,Wand,Brietta,Palace`)
branch to `0x08019394`, which calls `0x08019014`, without setting a level
character. That routine loads entities of type `0x4E` with the id in
`0x0300037C` (0 in the retail flow), then the screen update overwrites the
state and shows the normal rejection text. In the emulator the match flag is
set (`0x03000016 = 1`) but the screen stays at id 9 and eventually displays
*Incorrect Password!*. They are dead table rows, not secret levels.

---

## 6. Tables

### 6.1 Complete password table (`0x08141878`, 34 × 4 bytes)

`raw` is the stored symbol value in table order; `display` is the icon order the
player sees. Both encodings are given so the table can be checked against the
ROM and against the UI.

| # | raw | display (player order) | half | result |
|---:|---|---|---|---|
| 0 | `5,5,3,1` | Ollie, Ollie, Wand, Annika | Easy | **padding / dead** |
| 1 | `0,5,2,5` | Palace, Ollie, Brietta, Ollie | Easy | Cloud 2 (id 49) |
| 2 | `3,2,5,0` | Wand, Brietta, Ollie, Palace | Easy | Cloud 3 (id 50) |
| 3 | `3,2,0,2` | Wand, Brietta, Palace, Brietta | Easy | CINEMA CLOUD BOSS (id 40) |
| 4 | `1,0,1,4` | Annika, Palace, Annika, Wenlock | Easy | Flying 2 (id 18) |
| 5 | `1,1,3,1` | Annika, Annika, Wand, Annika | Easy | Village 2 (id 58) |
| 6 | `1,3,0,4` | Annika, Wand, Palace, Wenlock | Easy | Village 3 (id 59) |
| 7 | `0,1,1,3` | Palace, Annika, Annika, Wand | Easy | CINEMA VILLAGE BOSS (id 39) |
| 8 | `1,0,5,3` | Annika, Palace, Ollie, Wand | Easy | Flying 3 (id 19) |
| 9 | `3,1,0,0` | Wand, Annika, Palace, Palace | Easy | Forest 2 (id 61) |
| 10 | `3,4,1,3` | Wand, Wenlock, Annika, Wand | Easy | Forest 3 (id 62) |
| 11 | `5,1,2,1` | Ollie, Annika, Brietta, Annika | Easy | CINEMA FOREST BOSS (id 38) |
| 12 | `4,3,0,5` | Wenlock, Wand, Palace, Ollie | Easy | Flying 4 (id 20) |
| 13 | `0,4,5,5` | Palace, Wenlock, Ollie, Ollie | Easy | Glacier 2 (id 45) |
| 14 | `3,4,1,1` | Wand, Wenlock, Annika, Annika | Easy | Glacier 3 (id 46) |
| 15 | `2,1,0,4` | Brietta, Annika, Palace, Wenlock | Easy | CINEMA GLACIER BOSS (id 37) |
| 16 | `0,1,1,1` | Palace, Annika, Annika, Annika | Easy | Final boss / world map (id 13) |
| 17 | `1,3,2,0` | Annika, Wand, Brietta, Palace | Normal | **padding / dead** |
| 18 | `4,2,1,5` | Wenlock, Brietta, Annika, Ollie | Normal | Cloud 2 (id 49) |
| 19 | `0,3,4,2` | Palace, Wand, Wenlock, Brietta | Normal | Cloud 3 (id 50) |
| 20 | `0,3,1,4` | Palace, Wand, Annika, Wenlock | Normal | CINEMA CLOUD BOSS (id 40) |
| 21 | `1,2,1,0` | Annika, Brietta, Annika, Palace | Normal | Flying 2 (id 18) |
| 22 | `3,0,5,0` | Wand, Palace, Ollie, Palace | Normal | Village 2 (id 58) |
| 23 | `3,2,5,4` | Wand, Brietta, Ollie, Wenlock | Normal | Village 3 (id 59) |
| 24 | `5,5,3,4` | Ollie, Ollie, Wand, Wenlock | Normal | CINEMA VILLAGE BOSS (id 39) |
| 25 | `0,5,4,3` | Palace, Ollie, Wenlock, Wand | Normal | Flying 3 (id 19) |
| 26 | `4,4,2,3` | Wenlock, Wenlock, Brietta, Wand | Normal | Forest 2 (id 61) |
| 27 | `3,0,5,1` | Wand, Palace, Ollie, Annika | Normal | Forest 3 (id 62) |
| 28 | `2,4,5,3` | Brietta, Wenlock, Ollie, Wand | Normal | CINEMA FOREST BOSS (id 38) |
| 29 | `1,4,1,3` | Annika, Wenlock, Annika, Wand | Normal | Flying 4 (id 20) |
| 30 | `4,4,5,4` | Wenlock, Wenlock, Ollie, Wenlock | Normal | Glacier 2 (id 45) |
| 31 | `2,3,2,1` | Brietta, Wand, Brietta, Annika | Normal | Glacier 3 (id 46) |
| 32 | `1,0,4,0` | Annika, Palace, Wenlock, Palace | Normal | CINEMA GLACIER BOSS (id 37) |
| 33 | `5,0,4,3` | Ollie, Palace, Wenlock, Wand | Normal | Final boss / world map (id 13) |

### 6.2 The 16 levels, Easy and Normal

Fan names follow GameFAQs (Easy list) and speedrun.com (Normal list). Registry
ids are the internal screen names found at `0x0813ED88`/`0x0813F22C`.

| Level | id | Easy code | Normal code |
|---|---:|---|---|
| BOSS BATTLE | 13 | Palace, Annika, Annika, Annika | Ollie, Palace, Wenlock, Wand |
| Flight A | 18 | Annika, Palace, Annika, Wenlock | Annika, Brietta, Annika, Palace |
| Flight B | 19 | Annika, Palace, Ollie, Wand | Palace, Ollie, Wenlock, Wand |
| Flight C | 20 | Wenlock, Wand, Palace, Ollie | Annika, Wenlock, Annika, Wand |
| Glacier Land C (Glacier boss) | 37 | Brietta, Annika, Palace, Wenlock | Annika, Palace, Wenlock, Palace |
| Forbidden Forest C (Forest boss) | 38 | Ollie, Annika, Brietta, Annika | Brietta, Wenlock, Ollie, Wand |
| Snow Village C (Village boss) | 39 | Palace, Annika, Annika, Wand | Ollie, Ollie, Wand, Wenlock |
| Cloud Palace C (Cloud boss) | 40 | Wand, Brietta, Palace, Brietta | Palace, Wand, Annika, Wenlock |
| Glacier Land A | 45 | Palace, Wenlock, Ollie, Ollie | Wenlock, Wenlock, Ollie, Wenlock |
| Glacier Land B | 46 | Wand, Wenlock, Annika, Annika | Brietta, Wand, Brietta, Annika |
| Cloud Palace A | 49 | Palace, Ollie, Brietta, Ollie | Wenlock, Brietta, Annika, Ollie |
| Cloud Palace B | 50 | Wand, Brietta, Ollie, Palace | Palace, Wand, Wenlock, Brietta |
| Snow Village A | 58 | Annika, Annika, Wand, Annika | Wand, Palace, Ollie, Palace |
| Snow Village B | 59 | Annika, Wand, Palace, Wenlock | Wand, Brietta, Ollie, Wenlock |
| Forbidden Forest A | 61 | Wand, Annika, Palace, Palace | Wenlock, Wenlock, Brietta, Wand |
| Forbidden Forest B | 62 | Wand, Wenlock, Annika, Wand | Wand, Palace, Ollie, Annika |

Only the 16 ids in the table above are reachable. The other registry entries
(first level of each world: Cloud 1, Forest 1, Glacier 1, Village 1; Flying 1;
BONUS 1–3; WENLOCK; Wenlock's Palace; MINIGAME 1–4; GYM; the CINEMA intro and
ending screens) have no password row.

### 6.3 Level character → screen id (observed)

| char | `0` | `1` | `2` | `/` | `9` | `:` | `;` | `8` | `<` | `=` | `>` | `?` | `,` | `-` | `.` | `+` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| screen id | 49 | 50 | 40 | 18 | 58 | 59 | 39 | 19 | 61 | 62 | 38 | 20 | 45 | 46 | 37 | 13 |

Ids map to the internal names at `0x0813ED88`/`0x0813F22C`:

| id | name | id | name |
|---:|---|---:|---|
| 13 | (not in registry; world map / final-boss entry) | 45 | Glacier 2 |
| 18 | Flying 2 | 46 | Glacier 3 |
| 19 | Flying 3 | 49 | Cloud 2 |
| 20 | Flying 4 | 50 | Cloud 3 |
| 37 | CINEMA GLACIER BOSS | 58 | Village 2 |
| 38 | CINEMA FOREST BOSS | 59 | Village 3 |
| 39 | CINEMA VILLAGE BOSS | 61 | Forest 2 |
| 40 | CINEMA CLOUD BOSS | 62 | Forest 3 |

### 6.4 Hidden/debug screen registry (`0x0813ED88`)

Nineteen records `{u32 id; char name[32]}` (the first is a header row `id=2`,
name `" "`):

```
0x40 GYM              0x04 TITLE            0x08 Language Menu
0x07 Game Mode Menu   0x0B Difficulty Menu  0x09 Password Menu
0x0C Arcade Menu      0x1A Arcade Debug     0x18 Cloud Palace Debug
0x1C Village Debug    0x19 Forest Debug     0x1B Glacier Debug
0x33 Wenlock's Palace 0x10 CREDITS          0x1D CINEMA DEBUG
0x0E VIVENDI          0x0F WAYFORWARD       0x0A GET PASSWORD
```

A second registry at `0x0813F22C` lists Cloud/Forest/Glacier/Village 1–3,
`MINIGAME 1`–`4`, `Flying 1`–`4`, `BONUS 1`–`3` and the CINEMA screens.
The debug names are used by a list renderer around `0x0800E300` (19-item list,
36-byte stride). **No retail input reached those screens**: see §8.

---

## 6b. Enumeration

### Space definition

* Alphabet: six symbols, display indices 0–5, stored values 0–5.
* Length: four independent slots.
* Total representable inputs: `6^4 = 1296`.
* No checksum, no reserved bits, no table lookup by hash: the table is 34
  literal 4-byte rows and the validator is exact equality. Of the 8 possible
  3-bit values per slot, only 0–5 are reachable and only 0–5 appear in the
  table.
* Usable table rows: 32 level rows (16 Easy + 16 Normal). Rows 0 and 17 are
  dead padding rows.

### Exhaustive test

All 1296 inputs were entered in the emulator core from a savestate at the
password screen, then checked for a screen-id change. The loop is one
`enum pwbase.state enum_results.txt` command; each case costs four slot edits
plus Start, about 300 frames. Results:

| Outcome | Count |
|---|---:|
| Accepted, level started | **32** |
| Matched a table row but no level (rows 0/17; screen id stayed 9) | 2 |
| Rejected (no table row) | **1262** |
| Total | 1296 |

The 32 accepted inputs are exactly the rows 1–16 and 18–33 of §6.1. Every one
of the 16 levels is reached by exactly two inputs, one Easy and one Normal.
There is no third code for any level and no unreachable table row that starts
content.

### Publication check

* **Easy:** all 16 GameFAQs codes (`Passwords (only Easy Mode)`) were mapped to
  display indices and are exactly rows 1–16. Every one is accepted by the ROM.
* **Normal:** all 16 speedrun.com Normal codes are exactly rows 18–33. The 2019
  PrinceWatercress blog's four codes (`Wenlock,Pegasus,Annika,Ollie`;
  `Castle,Wand,Wenlock,Pegasus`; `Castle,Wand,Annika,Wenlock`;
  `Annika,Pegasus,Annika,Castle`) are the Normal variants of Cloud A, Cloud B,
  Cloud C and Flight A.
* Therefore **all 32 valid level codes are published**. No unpublished level
  code exists, and none can be minted: the space is closed at 32 and the
  exhaustive test above is the proof.

The public lists are not error-free:

| Published as | Actual result |
|---|---|
| speedrun.com "Palace 2 (Easy)": Palace, Ollie, Brietta, Palace | **rejected** — not in the table (screen id stayed 9; `... - published typo rejected.png`) |
| speedrun.com "Ice 2 (Easy)" and "Ice 3 (Easy)" are both Wand, Wenlock, Annika, Annika | duplicate; the real Glacier 2 Easy is Palace, Wenlock, Ollie, Ollie |
| speedrun.com "Final Boss (Easy)": Palace, Annika ×4 (five symbols) | five entries is impossible; the ROM code is Palace, Annika, Annika, Annika |

The GameFAQs Easy list has no errors: 16/16 accepted.

### The only unpublished table entries

Rows 0 and 17 match the validator (success flag `0x03000016 = 1` at
`0x08019264`) but branch to the dead handler and produce no level. They appear
in no published list. Entered in the emulator:

| Input | Observable result |
|---|---|
| Ollie, Ollie, Wand, Annika (row 0) | remains on password screen; no level; eventual `Incorrect Password!` |
| Annika, Wand, Brietta, Palace (row 17) | same |

They are documented for completeness, not offered as usable shortcuts. A novel
*playable* code does not exist in this ROM.

### Bounds proven by rejection

| Input | Expected if bounds are right | Observed |
|---|---|---|
| Palace, Ollie, Brietta, Wenlock (near-miss of Cloud A: last symbol changed) | rejected | `Incorrect Password!` (`... - rejected near miss.png`) |
| Palace ×4 (default / all-zero) | rejected | `Incorrect Password!` |
| Palace, Ollie, Brietta, Palace (speedrun's published "Palace 2 Easy") | not in table | `Incorrect Password!` |
| all other 1262 inputs | rejected | screen id stayed 9 for every one |

The near-miss is the strongest bound: changing exactly one symbol of a valid
code (`Ollie` → `Wenlock` in slot 4) is rejected, so the validator really is
exact-match on all four bytes, not a prefix/range check.

The "Incorrect Password!" banner is drawn late and does not stay on screen
forever, so every case was classified by machine state: a start changes
`0x0300180C` away from `9`; a rejection leaves `0x0300180C = 9`. Spot checks of
`0x03000015` agreed with that classification (`4` after a start, `2` after a
rejection).

---

## 7. Validation evidence

### Observed (emulator screenshots, RAM reads)

* Title, main menu, difficulty menu, Arcade grid, password screen and pause
  menu were walked and captured (`... - title.png`, `- main menu.png`,
  `- difficulty level.png`, `- arcade games.png`, `- password screen.png`,
  `- pause menu.png`).
* The six-symbol cycle and the stored values: Up from Palace writes `0` then
  `5, 4, 3, 2, 1` to `0x03002A70`; the sixth press returns to `0`.
* Easy and Normal codes for the same level both enter the same level id but
  differ in `0x030000F4` (0 vs 1) and in the health HUD (no hearts vs three
  hearts) — `... - easy vs normal hearts.png`.
* `Wenlock, Wenlock, Brietta, Wand` accepted; starts Forest 2 with three hearts
  (`... - normal code entered.png`, `- normal code effect Forest 2.png`).
* Near-miss rejection (`... - rejected near miss.png`).
* Exhaustive 1296-case result: 32 level starts, 2 inert table matches, 1262
  no-match rejections (the 32 results are listed in §6.1).
* Padding row 0 entered: no transition (`... - padding code entered.png`,
  `- padding code no effect.png`); match flag `0x03000016 = 1` read at 20 frames
  after Start, vs `0` for a non-table code.

### Derived (instruction sequence proves the behaviour)

* Table location and size: `0x08019238` loads `0x08141878`; the compare loop at
  `0x08019240`–`0x08019264` reads four bytes per record and branches on the
  match index.
* Difficulty: `0x08019276` writes 0 to `0x030000F4` for rows ≤ 16;
  `0x08019302` writes 1 for rows ≥ 18. `0x080192FC` special-cases row 17.
* Level character: `0x0801927E`/`0x0801930E` read `0x08141900[index-1]` (Easy)
  or `0x08141900[index-18]` (Normal) and store it at `0x03000018`.
* Input arithmetic: `0x08018E88` calls the `% 6` helper on Up; Down adds 5.
* Pause/level path: state values `2` (password), `4` (accepted), flag `0`/`1`
  at `0x03000016`.

### Inferred

* `0x03000018` is the level *number* character; a not-yet-reversed loader maps
  it to the screen id in §6.3.
* Rows 0/17 are deliberate 17th padding rows (one per half) that were never
  given a level; the dead `0x08019014` handler is still called.
* The 17th character `'3'` of `0x08141900` belongs to a level that was cut or
  never wired into the table.

---

## 8. Unknowns

* **Debug menu reachability.** The 19-entry screen registry and the list
  renderer exist, but no retail input reached them. Tested and rejected:
  Select+Start at the title; L+R+Start at the title; Select+A, L+R+A and
  L+R+Select+A on the main menu; holding L+R+Select from boot; the Konami
  sequence at the title; Select/L/R on the password screen and on the Arcade
  grid. The screens may be compiled in but gated by a build flag or a save
  byte. The `Arcade Debug` / `GET PASSWORD` labels remain unreached.
* **Arcade unlock conditions.** Only `Pegasus Coin Collect` is unlocked on a
  fresh boot; the other seven cells are locked and show "This game is still
  locked!". The unlock rule (finish a level, collect coins, or a save flag) was
  not reversed; no password targets the arcade ids.
* **Level-character loader.** The step from `0x03000018` to the final screen id
  was measured (the table in §6.3) but the loader table itself was not located.
* **Header checksum** is stored as 0. The complement check is valid and the
  game runs; no evidence of a gameplay patch, but the dump is not
  header-checksum-clean.
* **Other revisions/regions** may differ; all findings are tied to the SHA-256
  above.

---

## 9. Tooling

Installed/used: `mgba-sdl 0.10.5`, `libmgba-dev 0.10.5`, `Xvfb`, `openbox`,
`xdotool`, `scrot`, ImageMagick, `binutils-arm-none-eabi`, `gdb-multiarch`,
Python 3 + Capstone 5.0.7.

Files shipped with this report:

| File | Purpose |
|---|---|
| `Barbie and the Magic of Pegasus - mgba_harness.c` | deterministic libmgba driver (frames, keys, savestates, RAM dumps, 240×160 screenshots, `enum` loop) |
| `Barbie and the Magic of Pegasus - password_table.py` | dumps the 34-row table, decodes a four-symbol input, re-runs the 1296-case enumeration |
| `Barbie and the Magic of Pegasus - *.png` | the screenshots listed in §3 |

Build and run the harness:

```bash
gcc -O2 -o harness "Barbie and the Magic of Pegasus - mgba_harness.c" -lmgba -lm
./harness "Barbie and the Magic of Pegasus.gba" s_nav.txt
```

Example script (`s_nav.txt`) that reaches the screen and enters
`Wenlock, Wenlock, Brietta, Wand`:

```
wait 1000
press START
wait 400
press DOWN
press A
wait 200
press START
wait 90
press UP
press UP
press RIGHT
press UP
press UP
press RIGHT
press UP
press UP
press UP
press UP
press RIGHT
press UP
press UP
press UP
press START
wait 400
shot forest2.ppm
```

The three-argument decoder run is in §3; it prints the table and the hop from
display symbols to level id without the emulator.

---

## 10. Legal note

No ROM, graphics, music or game text is redistributed with this report. The
screenshots are small menu/gameplay captures made for evidence; the table
addresses, algorithms and the two short scripts are original analysis. The ROM
remains the property of its rights holders.
