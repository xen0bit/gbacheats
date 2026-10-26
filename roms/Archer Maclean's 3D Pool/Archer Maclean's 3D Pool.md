# Archer Maclean's 3D Pool (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Archer Maclean's 3D Pool/Archer Maclean's 3D Pool.gba` |
| Size | 1,048,576 bytes (0x100000, 1 MiB) |
| Header title | `AM 3D POOL` (0x00A0, space/NUL padded) |
| Game code | `BPLE` (0x00AC) |
| Maker code | `7U` (0x00B0) |
| Fixed byte 0xB2 | `0x96` |
| Main unit / device | `0x00` / `0x00` |
| Software version | `0x00` (Rev.00) |
| Entry branch (0x0000) | `0xEA00002E` (ARM branch to 0x080000C0) |
| Complement check | stored `0x23`, computed `0x23` |
| Header checksum (0x00BE) | `0x0000` |
| MD5 | `3443ebf753973ca24b6b21ea1916b8f0` |
| SHA-1 | `6feeab3a5da8f966755965b31a6a54719f34d2ff` |
| SHA-256 | `797028ebc9fb4636e568805d8ff7476287f29d0aeadefc156bc3da50b023f156` |

Embedded-header scan: the full 156-byte Nintendo logo was searched across all
1,048,576 bytes. There is exactly **one** hit, at file offset `0x4` (header base
`0x0`). This is a single-image cartridge, not a multi-game pack. No second GBA
header, no multiboot stub, no appended image.

## 2. Executive summary

**This ROM contains no in-game password system, no button cheat code, no hidden
developer/debug menu, and no persistent unlockable.** The only text-entry surface
is the six-slot tournament **player-name** field. The complete menu tree consists
of eight ordinary front-end items plus their submenus; all were reached and
captured. The developer-intended extras are the `8 BALL RULE EDITOR`, the
`TRICK SHOT` editor/sandbox, the `DEMO MODE` (CPU-vs-CPU demonstration), the
session-only rankings/records screens, and `CREDITS`.

The negative is bounded, not assumed:

* **Text space.** The UI text is an uncompressed ASCII script bank at
  `0x08048278`–`0x0804A07F`. It contains 376 printable strings. Whole-ROM,
  case-insensitive searches for `password`, `passwd`, `passcode`, `cheat`,
  `debug`, `secret`, `unlock`, `hidden`, `bonus`, `extra`, `enable`, `disable`
  and `level select` return **0 hits**. The only `code` hit is
  `ERROR CODE 0 NO ERROR` at `0x080495C1`, a rules-engine message. There is no
  `INVALID`/`INCORRECT`/`TRY AGAIN`/`ACCEPTED CODE` text either.
* **Literal code space.** A whole-ROM scan for NUL-delimited uppercase/digit
  strings of length 4–12 returns 37 hits: 34 are opponent names or ordinary UI
  words (including the 20 CPU names and their short forms) and 3 are incidental
  bytes (`3UD2`, `9I9H`, `MIDI`). The four audio filenames (`pianoe2.wav`,
  `pianoe4.wav`, `ClHAt.wav`, `OpHat.wav`) are lowercase and fall outside that
  pattern. There is no table of equal-length mixed alphanumeric passwords.
* **Button space.** All aligned 16-bit and 32-bit positions were scanned for runs
  of the ten GBA key masks, and the data regions were scanned for byte-per-key
  enumerations. The only ordered ten-mask array is the key-order/display
  table at `0x0804CEA0` (`L,R,Down,Up,Right,Left,Start,Select,B,A`). There is no
  sequence table. Fourteen sequences were pressed on the live main menu,
  including the Konami code and its reverse; none produced a hidden screen.
* **Published codes.** No GBA cheat/password list for this title exists
  (GameFAQs GBA entry has no cheats; VGChartz has no page; TCRF has none). The
  only published Archer Maclean passwords found are for *Super Dropzone*
  (`51853435`, `41693261`); both literals are absent from this ROM. There was
  therefore no published code to confirm, and that absence is recorded rather
  than silently omitted.

The closest thing to a cheat is the **TRICK SHOT editor**: it lets the player
place any ball anywhere, clear the rack, and add cushions/aim aids, and the
**8 BALL RULE EDITOR** lets the player change headstring, nomination and break
cushion rules. Both are ordinary menu features, not hidden codes.

## 3. How to reproduce

### Emulator and display

* mGBA 0.10.5 SDL (`/usr/games/mgba`), 3× scale.
* `Xvfb :140 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`.
* Window client area is at `+152+162`; screenshots were cropped with
  `convert … -crop 720x480+152+162 +repage`.

### Keymap (mGBA SDL defaults, confirmed against `0x04000130`)

| GBA | Key | Active-low bit |
|---|---|---|
| A | `x` | 0 |
| B | `z` | 1 |
| Select | `BackSpace` | 2 |
| Start | `Return` | 3 |
| Right | `Right` | 4 |
| Left | `Left` | 5 |
| Up | `Up` | 6 |
| Down | `Down` | 7 |
| R | `s` | 8 |
| L | `a` | 9 |

Key presses must be held about 0.12 s (≈7 frames); a 10 ms tap is often missed.
The game debounces menu repeats. For deterministic captures, mGBA's CLI debugger
(`mgba -d`, driven through a pty) was used to advance exact frame counts and to
read `0x04000130`/RAM.

### Boot and menu path

1. Boot. The Ignition logo and the long `ARCHER MACLEAN PRESENTS` / `P O O L`
   intro run for roughly 60 s if left alone, ending in the `TITLE`/`DEMO`
   attract game.
2. Press **Start** during the intro (around 15 s / frame 900) to open the main
   menu overlay immediately. The overlay can also be toggled with **Select**
   while a table is active.
3. Main-menu cursor behaviour: it restores the last-used row. In the fresh-boot
   captures it opened on `RETURN TO TABLE`; after an earlier selection it opened
   on `SELECT TYPE OF POOL`. Always navigate from the row visibly highlighted in
   the screenshot rather than assuming row 0.

Exact paths used (A = `x`, B = `z`):

| Target screen | Path |
|---|---|
| Main menu | Start during intro, or Select on table |
| `SET POOL TYPE` | Main → `SELECT TYPE OF POOL` → A |
| `WHAT DO YOU WANT TO DO` | Main → `CHOOSE TYPE OF GAME` → A |
| `8 BALL RULE EDITOR` | Main → `EDIT 8 BALL RULES` → A |
| `EDIT TRICK SHOTS` | Main → `SET UP TRICK SHOT` → A |
| `TRICK SHOT` editor | … → `START TRICK SHOT EDITOR` → A |
| `DEMONSTRATION GAME` | Main → `ENTER DEMO MODE` → A |
| `OPTIONS` | Main → `OPTIONS` → A |
| Rankings/records | `OPTIONS` → one of the four `VIEW …` rows → A |
| `CREDITS` | Main → `CREDITS` → A |
| Title sequence | `OPTIONS` → `QUIT TO TITLE SEQUENCE` → A |
| Player-name entry | `CHOOSE TYPE OF GAME` → `SETUP ONE PLAYER MATCH` / `SETUP TWO PLAYER MATCH` / `TWO PLAYER PRACTICE` |

### Menu cursor counts (observed, used to bound the lists)

* Main menu: eight rows; eight Down presses return to the identical screen
  (pixel diff 0).
* `SET POOL TYPE`: three types + `CANCEL`; four Down presses return (diff 0).
* `WHAT DO YOU WANT TO DO`: seven entries + `CANCEL`; eight Down presses return
  to the same highlighted row.
* `OPTIONS`: five entries + `CANCEL`; six Down presses return (diff 0).
* `EDIT TRICK SHOTS`: `START TRICK SHOT EDITOR` and `CANCEL`; Up/Down toggles
  exactly these two rows.
* `DEMONSTRATION GAME`: two entries + `CANCEL`.
* `8 BALL RULE EDITOR`: three fields + `OK`; no free numeric entry.

### Codes tested

No published code exists for this GBA title. The only published Archer Maclean
codes found (Super Dropzone, a different game) were searched literally and are
absent:

```
51853435  -> not present
41693261  -> not present
```

Button sequences pressed on the live main menu (see §6b for the full result
table): Konami, reverse Konami, Up-Up-Down-Down, Left-Right-Left-Right,
L+R+Start, L+R+Select, Start+Select, Select+Start, A+B+Select+Start, A-A-A,
B-B-B, held L+R+Select, held L+R+Start, and eight Downs. None opened a hidden
screen.

## 4. Address map

File address = `0x08000000 + file offset`.

| Item | File offset | ROM/RAM address | Notes |
|---|---:|---:|---|
| GBA header / entry | `0x000000` | `0x08000000` | ARM branch `0xEA00002E` |
| UI text/script bank | `0x048278` | `0x08048278` | 376 ASCII strings, NUL-terminated; control bytes `0xFA`–`0xFF` |
| Opponent-name table | `0x048278` | `0x08048278` | `DEMO`, `CPU`, `TITLE`, `DEMO`, then 20 CPU names + short names |
| 32-bit key-mask table | `0x048078` | `0x08048078` | `1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200` |
| 16-bit key-order table | `0x04CEA0` | `0x0804CEA0` | `L,R,Down,Up,Right,Left,Start,Select,B,A` |
| `KEYINPUT` literal | `0x008C58` | `0x08008C58` | holds `0x04000130` |
| Editor/table input code | `0x008BF0` | `0x08008BF0` | reads `0x04000130`, tests bits `0x2,0x4,0x8,0x1,0x10,0x20,…` |
| Frame tick | `0x0087F4` | `0x080087F4` | increments EWRAM counters, e.g. `0x02004AF8` |
| EWRAM frame counter | — | `0x02004AF8` | +1 per frame; not a menu index |
| IWRAM text-render buffer | — | `0x030056A0` | changes when the menu highlight redraws |
| Audio sample name 1 | `0x0A2ACC` | `0x080A2ACC` | `pianoe2.wav` |
| Audio sample name 2 | `0x0C6590` | `0x080C6590` | duplicate bank |

Main-menu label addresses (file → ROM):

| Row | Label (leading spaces trimmed) | File | ROM |
|---:|---|---:|---:|
| 0 | `SELECT TYPE OF POOL` | `0x491AA` | `0x080491AA` |
| 1 | `CHOOSE TYPE OF GAME` | `0x491C0` | `0x080491C0` |
| 2 | `EDIT 8 BALL RULES` | `0x491D6` | `0x080491D6` |
| 3 | `SET UP TRICK SHOT` | `0x491EB` | `0x080491EB` |
| 4 | `ENTER DEMO MODE` | `0x49200` | `0x08049200` |
| 5 | `OPTIONS` | `0x49214` | `0x08049214` |
| 6 | `CREDITS` | `0x49547` | `0x08049547` |
| 7 | `RETURN TO TABLE` | `0x492EA` | `0x080492EA` |

Submenu/action label addresses:

| Screen / label | File | ROM |
|---|---:|---:|
| `SET POOL TYPE` | `0x48D98` | `0x08048D98` |
| `8 BALL UK` | `0x48DA7` | `0x08048DA7` |
| `8 BALL USA` | `0x48DB2` | `0x08048DB2` |
| `9 BALL USA` | `0x48DBE` | `0x08048DBE` |
| `WHAT DO YOU WANT TO DO` | `0x48DCB` | `0x08048DCB` |
| `TWO PLAYER PRACTICE` | `0x4909E` | `0x0804909E` |
| `START ONE PLAYER GAME` | `0x490B3` | `0x080490B3` |
| `START TWO PLAYER GAME` | `0x490CA` | `0x080490CA` |
| `SETUP ONE PLAYER MATCH` | `0x490E1` | `0x080490E1` |
| `SETUP TWO PLAYER MATCH` | `0x490F9` | `0x080490F9` |
| `MULTIPLAYER TOURNAMENT` | `0x49111` | `0x08049111` |
| `8 BALL RULE EDITOR` | `0x49225` | `0x08049225` |
| `HEADSTRING OR D-LINE` | `0x49272` | `0x08049272` |
| `NOMINATE 8 BALL` | `0x4928A` | `0x0804928A` |
| `NUMBER OF BALLS TO HIT` | `0x4929E` | `0x0804929E` |
| `CUSHIONS ON BREAK` | `0x492B7` | `0x080492B7` |
| `EDIT TRICK SHOTS` | `0x4939D` | `0x0804939D` |
| `START TRICK SHOT EDITOR` | `0x4946C` | `0x0804946C` |
| `DEMONSTRATION GAME` | `0x493BA` | `0x080493BA` |
| `BEGIN DEMO FROM THE START` | `0x49511` | `0x08049511` |
| `START FROM CURRENT LAYOUT` | `0x4952C` | `0x0804952C` |
| `OPTIONS` | `0x493B0` | `0x080493B0` |
| `VIEW BEST 8 BALL RANKING` | `0x4912A` | `0x0804912A` |
| `VIEW BEST 9 BALL TIMES` | `0x49144` | `0x08049144` |
| `VIEW BEST MATCH RESULTS` | `0x4915C` | `0x0804915C` |
| `VIEW TOURNAMENT CHAMPIONS` | `0x49175` | `0x08049175` |
| `QUIT TO TITLE SEQUENCE` | `0x49557` | `0x08049557` |
| `CANCEL` (several screens) | `0x49485`/`0x4948D`/`0x49495` | `0x08049485`/`8D`/`95` |

## 5. Algorithm

**No password/validator algorithm exists in this ROM.** There is no input
buffer for a code, no `strlen`+`compare` path, no alphabet table, no checksum,
and no “invalid code” branch. The only text field is the tournament name field,
which stores the entered letters for display in match/tournament screens; it is
not compared against any table.

What the ROM does contain is a menu/UI model:

1. The front end is a linear ASCII script bank at `0x08048278`. A NUL terminates
   each string; `0x0A` is a line break; bytes `0xFA`–`0xFF` act as formatting /
   colour / position controls before a label. The eight main-menu labels are
   records in that bank (addresses above).
2. The table/editor code reads the keypad register directly. At `0x08008BF0` and
   `0x08008C84` it does `ldrh` from `0x04000130` and tests individual active-low
   bits (`0x2`, `0x4`, `0x8`, `0x1`, `0x10`, `0x20`, …). The key mask tables at
   `0x08048078` and `0x0804CEA0` describe the same ten buttons.
3. Menu movement is a row-index/selection model. The cursor wraps at the end of
   each list; the counts in §3 are the observed list sizes. Selecting a row calls
   the normal screen or starts a game. No row is gated by a hidden flag.
4. There is no sequence accumulator: no code path was found that compares a key
   against a multi-entry table, increments a progress byte on a match, and
   branches on completion. The static and dynamic button tests in §6b agree.

Pseudocode for the observed menu input (not a password validator):

```
keys = (~REG_KEYINPUT) & 0x3FF          # 0x04000130, active-low
if key_pressed(keys, DOWN): row = (row + 1) % row_count
if key_pressed(keys, UP):   row = (row - 1 + row_count) % row_count
if key_pressed(keys, A):    enter(row)
if key_pressed(keys, B):    leave_screen()
```

No `if code == table[i]` and no checksum appear anywhere near the UI strings.

## 6. Tables

### 6.1 Main menu and observed actions

| # | Label | Action observed |
|---:|---|---|
| 0 | `SELECT TYPE OF POOL` | Opens `SET POOL TYPE` |
| 1 | `CHOOSE TYPE OF GAME` | Opens `WHAT DO YOU WANT TO DO` |
| 2 | `EDIT 8 BALL RULES` | Opens `8 BALL RULE EDITOR` |
| 3 | `SET UP TRICK SHOT` | Opens `EDIT TRICK SHOTS` |
| 4 | `ENTER DEMO MODE` | Opens `DEMONSTRATION GAME` |
| 5 | `OPTIONS` | Opens `OPTIONS` |
| 6 | `CREDITS` | Shows Ignition / Archer Maclean / Adrian Scotney / Steve Cowell credits |
| 7 | `RETURN TO TABLE` | Closes the overlay, returns to the table |

### 6.2 Pool types

| Entry | Header after selection |
|---|---|
| `8 BALL UK` | `UK   8 BALL   PUB` |
| `8 BALL USA` | `USA  8 BALL   BAR` |
| `9 BALL USA` | `USA  9 BALL   PRO` |
| `CANCEL` | Returns to main menu |

### 6.3 Game-type menu

`TWO PLAYER PRACTICE`, `START ONE PLAYER GAME`, `START TWO PLAYER GAME`,
`SETUP ONE PLAYER MATCH`, `SETUP TWO PLAYER MATCH`, `MULTIPLAYER TOURNAMENT`,
`CANCEL`. The setup entries lead to the name-entry screen (`ENTER NAME 1-`,
`ENTER NAME 2-`, `SET GAMES IN MATCH`), which is the only text-entry surface in
the game. It is a six-slot player name, not a code.

### 6.4 Rule editor

Three fields, each with a fixed option set:

| Field | Options |
|---|---|
| `HEADSTRING OR D-LINE` | `HS`, `DL` |
| `NOMINATE 8 BALL` | `YES`, `NO` |
| `NUMBER OF BALLS TO HIT CUSHIONS ON BREAK` | `1`, `2`, `3`, `4` |

No free numeric entry and no hidden fourth field; `OK` accepts and returns.

### 6.5 Trick-shot screen

`EDIT TRICK SHOTS` with an initially empty list (15 numbered slots exist in the
text bank, `1`–`15`, for user-created shots), plus `START TRICK SHOT EDITOR` and
`CANCEL`. The editor itself is a table sandbox: the top palette offers balls
`1`–`8`, cue ball, `CLR`, rack/cushion/aim tools, and the instruction
`PLACE ANY BALL`. Start hides/shows the palette; it is the normal editor, not a
debug menu.

### 6.6 Demo mode

`DEMONSTRATION GAME`: `BEGIN DEMO FROM THE START`, `START FROM CURRENT LAYOUT`,
`CANCEL`. Running it produces the header `DEMO … CPU` and a continuous
CPU-vs-CPU game with `PRESS START TO EXIT`. This is a developer demonstration
feature exposed in the retail menu.

### 6.7 Key masks

Standard GBA `KEYINPUT` (active-low), as used by the ROM:

| Button | Bit | Active-low value | Active-high mask |
|---|---:|---:|---:|
| A | 0 | `0x3FE` | `0x001` |
| B | 1 | `0x3FD` | `0x002` |
| Select | 2 | `0x3FB` | `0x004` |
| Start | 3 | `0x3F7` | `0x008` |
| Right | 4 | `0x3EF` | `0x010` |
| Left | 5 | `0x3DF` | `0x020` |
| Up | 6 | `0x3BF` | `0x040` |
| Down | 7 | `0x37F` | `0x080` |
| R | 8 | `0x2FF` | `0x100` |
| L | 9 | `0x1FF` | `0x200` |

`0x0804CEA0` stores the active-high masks in the order
`L,R,Down,Up,Right,Left,Start,Select,B,A`; `0x08048078` stores
`1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200` as 32-bit words.

### 6.8 Static search counts

| Search | Space | Hits | Classification |
|---|---|---:|---|
| `strings -n 3` | whole ROM | 15,966 lines | mostly tile/audio bytes; UI text bank is 376 strings |
| `password` | whole ROM, case-insensitive | 0 | — |
| `passwd` / `passcode` | whole ROM | 0 | — |
| `cheat` | whole ROM | 0 | — |
| `debug` | whole ROM | 0 | — |
| `secret` | whole ROM | 0 | — |
| `unlock` / `hidden` | whole ROM | 0 | — |
| `bonus` / `extra` / `enable` / `disable` / `level select` | whole ROM | 0 | — |
| `code` | whole ROM | 1 | `ERROR CODE 0 NO ERROR` at `0x080495C1` |
| `INVALID` / `INCORRECT` / `TRY AGAIN` / `ACCEPTED` | whole ROM | 0 | only gameplay `NOT VALID IN 9 BALL` |
| NUL-delimited `[A-Z0-9]{4,12}` | whole ROM | 37 | 34 opponent names / short names / UI words; 3 incidental (`3UD2`, `9I9H`, `MIDI`) |
| 16-bit key-mask runs ≥4 | whole ROM | 60 | only ordered ten-mask array at `0x0804CEA0`; others are data/code coincidences |
| 32-bit key-mask runs ≥3 | whole ROM | 6 | bitmask tables / short fragments |
| byte-per-key runs ≥4, 0–9, `0xFF`-terminated, data region | `0x48000`–`0x100000` | 20 rodata candidates | geometry/tile data (e.g. `0x4A9D3`, `0x4B339`), not button sequences |
| valid GBA LZ77 blocks (`0x10` header) | whole ROM | 0 | no compressed text bank |

The text bank contains no code-entry label, no “ENTER CODE”, no “PASSWORD”, and
no rejection message. This is the strongest static evidence that no code
validator exists: a validator without an invalid-input message and without a
single code alphabet/label is not a validator.

## 6b. Enumeration

### Space definition

| Quantity | Value |
|---|---|
| Password/code alphabets | none |
| Code lengths | 0 |
| Code table entries | 0 |
| Checksum width/position | none |
| Reserved/gate bits | none |
| Representable code values | **0** |

There is no code space to enumerate: no input buffer is allocated for a code, no
character set is mapped, and no comparison table or arithmetic check exists.
`6b` therefore reports the enumeration of the two adjacent spaces that *do*
exist — the menu action space and the button space — and the exact bounds of the
negative.

### Menu action space (complete)

| Level | Entries | Count |
|---|---|---:|
| Main menu | 8 rows (table above) | 8 |
| `SET POOL TYPE` | 3 types + `CANCEL` | 4 |
| `WHAT DO YOU WANT TO DO` | 7 entries + `CANCEL` | 8 |
| `8 BALL RULE EDITOR` | 3 fields (2/2/4 options) + `OK` | 4 controls |
| `EDIT TRICK SHOTS` | `START TRICK SHOT EDITOR`, `CANCEL`; 15 empty user slots | 2 + 15 slots |
| `DEMONSTRATION GAME` | 2 entries + `CANCEL` | 3 |
| `OPTIONS` | 5 views + `CANCEL` | 6 |
| `CREDITS` | one screen | 1 |
| Name entry | 6-slot player name + match settings | 1 |

**Total reachable menu/action entries: 8 + 4 + 8 + 4 + 2 + 3 + 6 + 1 + 1 = 37**
(including cancel rows, the rule-editor controls and the empty trick-shot slot
area). Every menu screen and every label was reached and captured; the
game-start entries were sampled (two-player practice, one-player game,
tournament/match setup) and lead to the table or to the name-entry screen, not to
a cheat screen. The list sizes are confirmed by cursor wrap (main 8→0, pool 4→0,
options 6→0, choose 8→same row) and by the Up/Down toggle on the two-row
trick-shot screen.

No menu entry is hidden or conditional: there is no extra row after the eighth
main item (eight Downs returns to the identical image, diff 0), and the
submenus wrap at their visible end.

### Button space

* Ten buttons: A, B, Select, Start, Right, Left, Up, Down, R, L.
* Static scan: no multi-entry sequence table anywhere in the ROM. The only
  ordered ten-mask array is the key-order table at `0x0804CEA0`; it is a
  display/sound ordering, not a code (it sits next to code that writes
  sound-effect IDs and is not referenced as an input sequence).
* Dynamic tests on the live main menu (image diff against the baseline menu):

| Sequence | Pixels changed | Result |
|---|---:|---|
| Up Up Down Down | 0 | no change |
| Left Right Left Right | 0 | no change |
| L + R + Start | 0 | no change |
| L + R + Select | 0 | no change |
| Start + Select | 0 | no change |
| Select + Start | 0 | no change |
| Hold L+R+Select for 90 frames | 0 | no change |
| Hold L+R+Start for 90 frames | 0 | no change |
| Down ×8 | 0 | menu wraps; no hidden row |
| Konami (U U D D L R L R B A) | 291,987 | A activated the normally highlighted menu row; resulting screen is the ordinary table |
| Reverse Konami (A B R L R L D D U U) | 294,903 | normal menu activation |
| A + B + Select + Start | 294,903 | normal menu activation/close |
| A A A | 294,903 | normal menu activation/close |
| B B B | 294,903 | normal cancel/close |

The five large diffs are explained by the final A/B selecting or closing the
currently highlighted ordinary menu row; the resulting screens were inspected and
are the normal table or main menu, not a hidden screen. No sequence produced a
new label, a counter, a flag change, or an unlock.

### Published codes

* GameFAQs GBA entry `919006` has no cheats content. Direct fetch returns HTTP
  403; Wayback CDX returns no snapshots for the `/cheats` URL; the GameFAQs
  franchise listing links no cheats page for the GBA entry.
* VGChartz has no cheats page for this game; no TCRF page was found.
* The only published Archer Maclean passwords located belong to *Super Dropzone*
  (SNES/GBA): `51853435` and `41693261`. Both are absent from this ROM
  (literal search returns `-1`).
* Therefore the number of published codes available to test is **0**, and no
  published code was accepted/rejected because none exists for this title.

### Bounds proven by rejection

* A code cannot be expressed because there is no entry surface; the only text
  field is the six-slot player name, and it has no comparison table.
* Menu values cannot be set outside their visible option sets: the rule editor
  accepts only `HS/DL`, `YES/NO`, `1/2/3/4`; there is no free numeric entry.
* Button sequences that do not correspond to a menu action leave the screen
  pixel-identical (diff 0 above); sequences that do end in A/B perform only the
  visible ordinary action.
* The main menu has exactly eight rows by wrap test; adding a ninth hidden row
  would break the eight-Down identity.

**Conclusion of 6b:** the code space is empty (0 representable values), the menu
space is fully enumerated (37 reachable entries), the button space is bounded by
the ten-mask scan plus 14 live sequences, and the published-code set is empty.
No novel code can be minted because there is no validator to accept one; the
negative is a property of the ROM, not a gap in testing.

## 7. Validation evidence

### Observed (emulator screenshots)

All captures are in `/tmp/opencode/pool/shots/` (720×480 GBA viewport crops):

| File | Shows |
|---|---|
| `03_title_crop.png`, `59_normal3_crop.png` | `ARCHER MACLEAN PRESENTS P O O L` intro and `TITLE`/`DEMO` attract table |
| `04_after_start_crop.png`, `80_walk_base_crop.png` | main menu, eight rows |
| `37_sel_type_a_crop.png`, `a7_pooltype_menu_crop.png` | `SET POOL TYPE` (3 types + cancel) |
| `39_8balluk_table_crop.png`, `a8_8ballusa_crop.png`, `a9_9ballusa_crop.png` | UK/PUB, USA/BAR and USA/PRO headers after type selection |
| `b0_choose_type_crop.png` | `WHAT DO YOU WANT TO DO` (7 + cancel) |
| `93_rule_editor_crop.png`, `a5_rule_left_crop.png` | `8 BALL RULE EDITOR` and field selection |
| `9b_trick_menu_crop.png`, `a1`–`a3` | `EDIT TRICK SHOTS` two-row list and toggle |
| `9d_trick_editor_crop.png` | `TRICK SHOT` sandbox, `PLACE ANY BALL`, palette |
| `82_enter_5_crop.png`, `9a_demo_start_crop.png` | demo menu and running `DEMO`/`CPU` game |
| `24_options_crop.png`, `91_optview_1`–`4_crop.png` | `OPTIONS` and the four empty records screens |
| `97_opt_quit_sel_crop.png`, `98_title_after_quit_crop.png` | `QUIT TO TITLE SEQUENCE` selection and title sequence |
| `31_credits_crop.png`, `32_credits2_crop.png` | credits |
| `b2_after_setup1_crop.png`, `cw_oneplayer_run_crop.png` | name-entry / match-setup screens (only text input) |
| `bt_konami_crop.png`, `bt_aaa_crop.png` | button-test endpoints: ordinary table, no hidden screen |
| `wrap_main_b8_crop.png`, `wrap_pool_*`, `wrap_options_*` | cursor wrap / list-size proofs |

### Derived (from ROM bytes/disassembly)

* Text bank layout and control-byte behaviour: from the contiguous
  NUL-terminated records at `0x08048278`–`0x0804A07F`.
* Key masks and direct `0x04000130` reads: from the literal at `0x08008C58` and
  the `ldrh`/`ands` sequence at `0x08008BF0`/`0x08008C84`.
* Absence of a sequence table: exhaustive 16/32-bit mask-run scan and
  byte-enumeration scan over the whole 1 MiB.
* Absence of a compressed text bank: no valid GBA LZ77 header in the image.
* Absence of save hardware access: no LDR literal for `0x0E000000`/`0x0D000000`;
  the emulator’s `.sav` remains 0 bytes and the record screens are empty on a
  cold boot.

### Inferred

* `DEMO`, `CPU` and `TITLE` in the name table are special demo/attract labels, not
  player-selectable cheat names.
* The 15 numbered strings are user trick-shot slots, because the list is empty on
  a cold boot and the editor exposes no preloaded shots.
* The Amiga-era magazine “cheat” articles for the 1992 game are gameplay hints
  and do not apply to this 2003 GBA port; no corresponding keys or tables exist
  in this image.

## 8. Unknowns

* The full script-VM opcode set was not decoded; the result rests on the text
  bank, the menu action space, and the key-mask/sequence scans. A hidden branch
  that produces **no new text and no visible change** and is not reachable by any
  of the scanned key-mask sequences is outside those bounds; the button-space
  scan and the 14 live sequences bound it as far as the observable surface goes.
* The purpose of the three leading name-table entries (`DEMO`, `CPU`, `TITLE`) is
  inferred from their use in the attract/demo header; no name check was found.
* Record-screen persistence: the tables are empty on cold boot and no save access
  was found. Their expected lifetime is session-only, inferred from the missing
  save pointer and the 0-byte `.sav`.
* Trick-shot slot storage: the 15 slots are empty on cold boot and no save access
  was found; they are expected to be in-session slots.

None of these unknowns is a code/password validator: the ROM has no code-entry
screen, no code alphabet, no code table, and no invalid-code message.

## 9. Tooling

* `mgba` 0.10.5 SDL, `Xvfb :140`, `openbox`, `scrot`, ImageMagick `convert` /
  `compare`, `xdotool`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for the input/editor and frame-tick ranges.
* Python 3 + Capstone 5.0.7 for literal-load, key-mask and byte-enumeration
  scans.
* `mgba -d` CLI debugger driven over a Python pty (`/tmp/opencode/pool/dbgctl.py`)
  for deterministic frame stepping, `0x04000130` verification and RAM dumps.
  GDB stub port 2345 was already occupied by another analysis session; the CLI
  debugger was used instead, without touching that session.
* Scripts: `/tmp/opencode/pool/` — `dbgctl.py`, `probe*.py`, `walk*.py`,
  `buttontest.py`, `wraptest*.py`, `choosewalk*.py`; scans were inline Python.

### Legal note

No ROM, extracted graphics, audio, or text bank is redistributed. The report
contains addresses, hashes, menu labels, and observations only. Screenshots are
local emulator captures used as evidence and are not part of the repository
artifact.
