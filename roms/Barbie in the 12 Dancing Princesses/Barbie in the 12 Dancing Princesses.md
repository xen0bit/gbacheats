# Barbie in the 12 Dancing Princesses (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Barbie in the 12 Dancing Princesses.gba` |
| Size | 4,194,304 bytes (`0x400000`, 4 MiB) |
| Header title | `BARBIE12PRCS` (`0x080000A0`) |
| Game code | `BB3E` (`0x080000AC`) |
| Maker code | `52` (Activision) (`0x080000B0`) |
| Version | `00` (`0x080000BC`) |
| Complement check | stored `0xAE`, computed `0xAA` |
| Header checksum | stored `0x0000`, computed `0x00AE` |
| Entry branch | `0xEA00002E` → `0x080000C0` |
| Fixed byte `0xB2` | `0x96` |
| MD5 | `6a06b7c152538ce846fbdf523902a000` |
| SHA-1 | `fa4e69ceb8d2773bbfc1c225f3604c1f7df43cde` |
| SHA-256 | `b858e1e7c7fd6c129d7435ed447164175d2b498941c4d15dc6ffa13978c310ca` |

Embedded-header scan: exactly one copy of the 156-byte Nintendo logo, at file
offset `0x4` (header at `0x0`). This is a single GBA image, not a multi-game
pack. The header's two checksum fields are inconsistent with the rest of the
header: the complement byte contains `0xAE`, which equals the *computed header
checksum*, while the header-checksum field at `0xBE` is zero. The title, game
code, maker code, logo and entry point are intact. **Observation**; the
mismatch is consistent with a header patched/rebuilt by a tool after dumping.

## 2. Executive summary

The game exposes **Password** as a first-class entry in the Game Mode menu. The
password is not text: it is **four portrait icons**, each chosen from a ring of
**eight** (Blonde Girl, Slippers, Old Lady, Bird, Prince, Cat, Brunette Girl,
Monkey). The representable space is therefore `8^4 = 4096`.

The validator is a literal lookup. A **416-record table** of 4-byte passwords
lives at ROM `0x081275F0` (file `0x1275F0`), organised as **13 levels × 32
variants**. Records whose fourth byte is `9` are unreachable padding (the
entry ring only exposes 0–7), leaving **184 enterable codes**. All 13 publicly
documented level passwords are present and were confirmed in the emulator.
The other **171 enterable codes are absent from the verified published list**
(the only other list found, mariogba.nl, is mislabeled and partially overlaps).

Each level's 32 variants also carry a **5-bit flag field** (the record's column
index). The flags are written to game RAM at `0x030000B4`, `0x03000990` and
`0x03006C1C`. Their most visible effect is starting health: the level-11 code
`3,1,4,3` (column 31) starts the level with **six heart icons**, while the
published column-0 code `0,6,4,2` for the same level starts with none.

Novel codes were entered in mGBA and produced the expected level/state. Bounds
were proved by rejection: `0,0,0,0` and `7,7,7,7` both display
**"Incorrect Password!"** and never set the accepted-code buffer.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL under `Xvfb :170`, 3× scale, `SDL_AUDIODRIVER=dummy`.

Default SDL keymap used: **A = `x`, B = `z`, Start = `Return`**, D-pad = arrow
keys. Hold keys ~100–200 ms; the menu debounces repeated presses.

Exact path:

1. Boot → title → `PRESS START` (Start).
2. **Game Mode** → `Password` (third entry) → A.
3. **Enter Password**: four slots. Up/Down cycles the icon in the selected
   slot; Left/Right selects a slot; Start (or A) submits; B backs out.
4. On a valid code the entry screen holds briefly and then returns to **Game Mode**;
   wait ~2 s, then press **Down** once (moves the cursor from New Game to
   Continue Game) and **A**. The game starts at the level index selected by the
   password (observed for levels 1, 5, 11 and 13).
5. On an invalid code the screen prints **"Incorrect Password!"** and stays in
   the entry screen.

The emulator state used for every repeat test is `Barbie in the 12 Dancing
Princesses.ss1`, saved on the empty password screen (all four slots = Blonde
Girl). Loading it makes each experiment one code entry rather than a replay.

Menu inventory walked on `:170`: title (`PRESS START`), **Game Mode**
(New Game / Continue Game / Password / Mini-Games), **Difficulty Level**
(Easy / Normal, reached from New Game and from Continue with no save),
**Enter Password**, **Pause** (Continue / Quit), and the **Mini-Games** grid
(Butterfly Catch 1, Ribbon Race 1, Book Challenge 1). There is no Options
menu. No hidden or debug screen was reached or found; the debug scene-name
table at `0x081245EC` lists exactly these menu scenes (Title, Language, Main
Menu, Difficulty, Intro, Credits, Password, Minigames) plus the level names at
`0x081243F8`.

Published codes tested in-emulator: `5,5,1,4` (2-A), `5,2,3,7` (2-B),
`0,0,4,6` (8), `0,6,4,2` (7-A). All were accepted and produced their level's
start scene.

### 3.1 Reconnaissance and published-code verification

`strings -t x -n 4` yields 52,756 ASCII runs. Keyword counts (case-insensitive)
and their classification:

| Keyword | Hits | Classification |
|---|---:|---|
| `password` | 1 | `PASSWORD` at `0x1246EC`, a **scene-name table** entry (id 8), not UI text |
| `code` | 1 | `Shin'en Multimedia. Code: B.Wodok` at `0x12374E`, GAX sound-engine banner (false positive) |
| `level` | 6 | one audio sample name `levelcomplete01`, five `*Level Designers` credit lines |
| `cheat` | 0 | — |
| `debug` | 0 | — |
| `secret` | 0 | — |
| `unlock` | 0 | — |

There is no `debug`, `test`, `option`, `sound test` or `cheat` string anywhere
in the image, so no text-driven debug/options menu exists. The visible UI text
("Game Mode", "Enter Password", "Incorrect Password!") is drawn from tile
graphics, which is why a string search does not find it.

Literal search for each of the 13 published 4-icon codes found all 13 as
4-byte records inside the table at `0x081275F0`; none is absent.

Button-code search: a scan for runs of 3+ little-endian halfwords matching
single GBA key masks (`A,B,Select,Start,Right,Left,Up,Down,R,L`) produced 445
raw hits, and an 8-bit variant produced 9,866; every inspected hit lies in
code, font or audio data and none is a sequence table with a progress index or
an action dispatch. The icon password is the only developer code system in this
ROM.

## 4. Address map

File offset ↔ ROM address is `+0x08000000`; all addresses below are ROM/RAM
addresses.

| Address | Kind | Meaning |
|---|---|---|
| `0x08014DE4` | code | password-scene init/update entry |
| `0x08014F68` | code | failure/reset path (clears slot entities, sets state 3) |
| `0x08015100`–`0x0801519E` | code | icon cycling (Down: 0–6 → +1, 7 → 0; Up: 0 → 7, else −1) |
| `0x080151AA`–`0x08015202` | code | Left/Right slot selection (0–3, wraps) |
| `0x08015206`–`0x0801539A` | code | submit/validator (A **or** Start) |
| `0x080154F0`–`0x0801565C` | code | flag/level derivation after a match |
| `0x081275F0` | data | **416 × 4-byte password table** (ends `0x08127C6F`) |
| `0x08127C70` | data | 13 bytes, one music track ID per level |
| `0x081243F8` | data | level-name table (`{u32 id; char name[32]}`) |
| `0x081245EC` | data | menu-scene name table (`PASSWORD` id 8 at `0x081246EC`) |
| `0x08127C80`, `0x08127CA0` | data | ASCII `*Barbie` / `*12 Dancing Princesses` build strings |

RAM (IWRAM):

| Address | Size | Meaning |
|---|---|---|
| `0x03002970` | 40 × `0x54` | entity array; password slots are type `10` at `+0x22` |
| `0x03002998` | u16 | slot 1 icon value (`entity[0] + 0x28`) |
| `0x030029EC` | u16 | slot 2 icon value |
| `0x03002A40` | u16 | slot 3 icon value |
| `0x03002A94` | u16 | slot 4 icon value |
| `0x03002968` | u16 | key-input mirror (A=1, B=2, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80) |
| `0x03000354` | 4 bytes | accepted code buffer (`FF FF FF FF` when empty) |
| `0x030004C8` | u8 | selected level number = `row + 1` |
| `0x03006D54` | u16 | table count, set to `416` by the scene init |
| `0x03006D58` | u8 | music track ID = `table_music[row]` |
| `0x03006D5C` | u8 | selected slot (0–3) |
| `0x03006D60` | u8 | "code found" flag |
| `0x03006D64` | u8 | screen state (1 input, 2 success animation, 3 reset) |
| `0x030000B4` | u8 | flag bit 0 |
| `0x03000990` | u32 | bit 2 = "row ≠ 0 used"; bit 29 = flag bit 1; bit 13 observed after column 31 |
| `0x03006C1C` | 4 bytes | bytes 1–3, bit 2 = flag bits 2–4 |
| `0x03006BA8` | u8 | `3 + popcount(column & 0x1C)`; equals drawn heart count in the column-31 test |

The key read is `ldrh` from `0x03002968`: A = bit 0, Start = bit 3. The submit
test is `(keys & 1) || (keys & 8)` at `0x0801520A`–`0x0801521C`.

## 5. Algorithm

### 5.1 Entry-screen model

```
icons[0..7] in ring order:
  0 Blonde Girl, 1 Slippers, 2 Old Lady, 3 Bird,
  4 Prince, 5 Cat, 6 Brunette Girl, 7 Monkey

slot[0..3] : u16, initial 0, each independently cycles 0..7
selected   : 0..3
Down: slot[selected] = (slot[selected] == 7) ? 0 : slot[selected] + 1
Up  : slot[selected] = (slot[selected] == 0) ? 7 : slot[selected] - 1
Right/Left: selected = (selected ± 1) & 3
```

### 5.2 Validator

```python
TABLE = rom[0x1275F0 : 0x1275F0 + 416*4]   # 416 records, level-major
def submit(slot):
    for i in range(416):                    # count = u16 at 0x03006D54
        rec = TABLE[4*i : 4*i+4]
        if rec == bytes(slot):              # all four bytes, exact
            row, col = divmod(i, 32)
            ram[0x03006D60] = 1             # found
            ram[0x03000354:0x03000358] = rec
            ram[0x030004C8] = row + 1       # level number 1..13
            ram[0x03006D58] = MUSIC[row]    # 0x08127C70 + row
            ram[0x030000B4] = col & 1
            set_bit(0x03000990, 29, (col >> 1) & 1)
            set_bit(0x03006C1C+1, 2, (col >> 2) & 1)
            set_bit(0x03006C1C+2, 2, (col >> 3) & 1)
            set_bit(0x03006C1C+3, 2, (col >> 4) & 1)
            if row != 0:
                set_bit(0x03000990, 2, 1)
            ram[0x03006BA8] = 3 + popcount(col & 0x1C)
            return ACCEPT
    return REJECT                           # "Incorrect Password!"
```

The match test is a plain byte-for-byte comparison (`0x08015298`–`0x080152AE`);
there is no per-character arithmetic, checksum or wildcard in the validator.
`0x09` is a literal byte and cannot match any slot value 0–7.

### 5.3 Why `9` appears in the table

Every one of the 232 occurrences of `0x09` is in the **fourth** byte of a
record. Records `…,9` are unused variants. The entry screen's ring has only
eight symbols, so those records are unreachable through the UI. This is the
table's own "empty" marker, not a wildcard.

## 6. Tables

### 6.1 Icon ring (observed, then confirmed against every published code)

| Index | Icon | Published name (gamegenie/supercheats) |
|---:|---|---|
| 0 | Blonde girl, pink dress, blonde bun | Blonde Girl |
| 1 | Pink ballet slippers | Slippers / Ballet Shoes |
| 2 | Grey-haired woman | Old Lady / Rowena |
| 3 | Yellow-and-blue parrot | Bird / Felix |
| 4 | Brown-haired young man, dark outfit | Prince / Derek |
| 5 | Orange cat | Cat / Twyla |
| 6 | Brown ponytail, purple dress | Brunette Girl |
| 7 | Grey monkey | Monkey / Brutus |

The first four symbols are identical for every record; only the fourth varies.

### 6.2 Level map

| Row | Level | Records | Enterable | Published code (index/col) |
|---:|---|---:|---:|---|
| 0 | 2-A | 32 | 4 | `5,5,1,4` (0/0) |
| 1 | 2-B | 32 | 4 | `5,2,3,7` (34/2) |
| 2 | 3-A | 32 | 8 | `2,1,1,1` (66/2) |
| 3 | 3-B | 32 | 8 | `0,0,7,0` (96/0) |
| 4 | 4-A | 32 | 8 | `2,6,5,6` (128/0) |
| 5 | 4-B | 32 | 8 | `7,4,0,3` (160/0) |
| 6 | 5-A | 32 | 8 | `2,3,1,7` (194/2) |
| 7 | 5-B | 32 | 8 | `6,3,0,2` (224/0) |
| 8 | 6-A | 32 | 16 | `4,7,0,2` (256/0) |
| 9 | 6-B | 32 | 16 | `6,5,2,1` (288/0) |
| 10 | 7-A | 32 | 32 | `0,6,4,2` (320/0) |
| 11 | 7-B | 32 | 32 | `7,5,0,2` (352/0) |
| 12 | 8 | 32 | 32 | `0,0,4,6` (384/0) |

Total 416 records; 184 enterable; 13 published.

### 6.3 Music table (`0x08127C70`)

`18 1C 18 26 18 2E 18 4C 18 30 18 3B 3F` (13 bytes, one per row).

### 6.4 Flag field (per-column)

| Record column bit | Destination |
|---|---|
| bit 0 | `0x030000B4` byte |
| bit 1 | `0x03000990` bit 29 |
| bit 2 | `0x03006C1C[1]` bit 2 |
| bit 3 | `0x03006C1C[2]` bit 2 |
| bit 4 | `0x03006C1C[3]` bit 2 |
| count of bits 2–4 | `0x03006BA8 = 3 + count` |

## 6b. Enumeration

**Space definition.** Four slots, each an 8-symbol ring: `8^4 = 4096`
representable inputs. The lookup table contains 416 records (13 × 32). Exactly
**184** records use only symbols 0–7 and are therefore enterable; the other 232
end in the unreachable `9`. Of the 184, **13** are in the verified published
list and **171** are not; the examples below also avoid the mislabeled
mariogba.nl variants. All 184 are distinct (no duplicate code maps to two
levels).

**Published list.** Recovered from GameGenie, SuperCheats and ChapterCheats;
all three agree on the 13 codes above. GameFAQs and Neoseeker returned HTTP
403; an `archive.org` replay returned HTTP 400. The `mariogba.nl` list uses
character names and does **not** agree with the ROM table (e.g. its "Level 3"
code `Rowena, Felix, Ballet Shoes, Brutus` = `2,3,1,7` is record 194, i.e. the
**level-7** row, not level 3). It is recorded as **unverified/unreliable** for
this ROM.

**Novel codes (not in any published list we found).** One per level; the five marked ★
were entered in mGBA and the effect screenshotted.

| Level | Index | Code (slot 1–4) | Icons | Evidence |
|---|---:|---|---|---|
| 2-A | 1 | `4,4,5,4` ★ | Prince, Prince, Cat, Prince | accepted; Continue starts level 1 / Golden Pavilion opening (`10-novel-4454-level1.png`) |
| 2-B | 32 | `1,2,0,5` | Slippers, Old Lady, Blonde Girl, Cat | table-derived |
| 3-A | 64 | `3,0,2,0` | Bird, Blonde Girl, Old Lady, Blonde Girl | table-derived |
| 3-B | 97 | `1,2,2,1` | Slippers, Old Lady, Old Lady, Slippers | table-derived |
| 4-A | 129 | `1,4,6,4` ★ | Slippers, Prince, Brunette Girl, Prince | accepted; starts level 5 with **3 hearts** (`11-novel-1464-level5.png`) |
| 4-B | 161 | `3,5,7,6` | Bird, Cat, Monkey, Brunette Girl | table-derived |
| 5-A | 193 | `2,1,1,7` | Old Lady, Slippers, Slippers, Monkey | table-derived |
| 5-B | 225 | `2,1,3,0` | Old Lady, Slippers, Bird, Blonde Girl | table-derived |
| 6-A | 257 | `1,5,4,6` | Slippers, Cat, Prince, Brunette Girl | table-derived |
| 6-B | 290 | `4,7,4,0` | Prince, Monkey, Prince, Blonde Girl | table-derived |
| 7-A | 321 | `0,4,3,6` | Blonde Girl, Prince, Bird, Brunette Girl | table-derived |
| 7-B | 353 | `3,4,7,3` | Bird, Prince, Monkey, Bird | table-derived |
| 8 | 385 | `5,5,6,4` ★ | Cat, Cat, Brunette Girl, Prince | accepted; starts level 13 (8) at the same castle corridor as published `0,0,4,6` (`12-novel-5564-level8.png`) |

Two further **column-31** codes were entered to exercise the flag field:

| Level | Index | Code | Icons | Observed effect |
|---|---:|---|---|---|
| 7-A | 351 | `3,1,4,3` ★ | Bird, Slippers, Prince, Bird | starts level 11 with **six heart icons** (`13-novel-3143-level11.png`), while published col-0 `0,6,4,2` on the same level shows **none** (`14-published-7a.png`) |
| 8 | 415 | `5,6,2,4` ★ | Cat, Brunette Girl, Old Lady, Prince | accepted; RAM flags read back `B4=01`, `0990=0x20002004`, `06C1C=00 04 04 04`, `06BA8=06`, `0354=05 06 02 04`, `04C8=0D` — all five column bits set (`17-novel-5624-level13.png`) |

**Bounds proved by rejection.** `0,0,0,0` (Blonde×4), `7,7,7,7`
(Monkey×4) and `3,3,3,6` are absent from the 416-record table. Submitting each
shows **"Incorrect Password!"** and leaves `0x03000354` at its previous value
(`FF FF FF FF` on a fresh state); the level variable is not written. The
unreachable `9` records are a hard format bound: the ring cannot produce `9`
(observed ring cycles 0→7→0), so 232 table records are not expressible through
the UI.

Screenshots: `15-reject-0000.png`, `16-reject-7777.png`.

## 7. Validation evidence

**Observed (emulator):**

* Title, Game Mode, Password entry, Difficulty, Pause, Mini-Games screens all
  reached with the key sequence in §3.
* Icon ring order and animation (eight portraits, wrap at both ends).
* Published `5,5,1,4`, `5,2,3,7`, `0,0,4,6`, `0,6,4,2` accepted and started
  their level's scene.
* Novel `4,4,5,4`, `1,4,6,4`, `5,5,6,4`, `3,1,4,3`, `5,6,2,4` accepted;
  `5,5,6,4` produced the same start scene as published `0,0,4,6`.
* Heart HUD: 3 hearts at level 5 column 0; 0 hearts at level 11 column 0;
  6 hearts at level 11 column 31 (pixel-counted red heart runs at x =
  4,37,70,103,136,169).
* `0,0,0,0`, `7,7,7,7`, `3,3,3,6` → "Incorrect Password!".
* RAM reads after `5,6,2,4` matched the flag model exactly.

**Derived (disassembly):**

* Table base/count/record size and the `row = index >> 5`,
  `column = index & 31` split (`0x08015610`).
* Flag writes at `0x0801552A`–`0x0801560E`.
* Level number at `0x030004C8 = row + 1`, music at `0x03006D58`.
* Exact-match comparison, no checksum (`0x08015298`–`0x080152AE`).
* Icon cycling bounds and slot selection (`0x08015100`–`0x08015202`).

**Inferred:**

* The five column bits are developer health/ability grants. The heart-count
  match (`0x03006BA8 = 6` and six drawn hearts) is strong for the count, but
  the individual meaning of bits 0–4 is not named by any string or obvious
  consumer.
* The visible scenes are the game's level-index starts; the report does not
  claim the internal level names beyond the published row labels.

## 8. Unknowns

* Exact semantics of each individual flag bit (`0x030000B4`, `0x03000990`
  bit 29, `0x03006C1C[1..3] bit 2`). The aggregate count controls the heart
  HUD; the per-bit split was not traced to a consumer.
* Origin of `0x03000990` bit 13 (observed set after the column-31 code; not
  produced by the `0x080154F0` flag writer).
* Why level 11 column 0 draws no hearts although `0x03006BA8 = 3`; possibly a
  separate "HUD enabled" state set by the level script.
* No battery save was produced during testing (`.sav` stayed 0 bytes). The
  observed password path is in-session: the level selection at `0x030004C8`
  and the immediate start are proven, while any save-file round trip is outside
  the exercised path.
* The header checksum mismatch is consistent with a patch, but the patch's
  origin/tool is not identified.

## 9. Tooling

* `mGBA 0.10.5` (SDL) on `Xvfb :170`, `openbox`, `scrot`, ImageMagick.
* `arm-none-eabi-objdump -D -b binary -m armv4t -M force-thumb` for the
  validator/flag functions.
* GDB stub (`mgba -g`, `gdb-multiarch`) for RAM reads of the four slot values,
  the accepted-code buffer and the flag words. Watchpoints located the slot
  write path (`0x0801513A`) and the slot read (`0x080046D2`).
* `evidence/password_enum.py` — reads the 416-record table, prints the 184
  enterable codes, one novel code per level and the flag model. Run:
  `python3 password_enum.py "Barbie in the 12 Dancing Princesses.gba"`.
* Evidence images in `evidence/` (title, menus, published starts, novel-code
  starts, both rejections).

Reproducibility note: the password scene is deterministic and the `.ss1`
state at the empty entry screen makes every test repeatable without replaying
the intro.

## 10. Legal note

No ROM, extracted graphics, audio or game text is redistributed here. The
report contains addresses, algorithms, hashes and short UI labels; the
screenshots are evidence of observed emulator states. The ROM itself remains
the user's file.
