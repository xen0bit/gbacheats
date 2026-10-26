# All Grown Up!: Express Yourself (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-25.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/All Grown Up!: Express Yourself/All Grown Up!: Express Yourself.gba` |
| Size | 4 MiB (`0x400000`) |
| Header title | `ALLGROWNUPEY` |
| Game code | `BALE` |
| Maker code | `78` |
| Software version | `0` |
| Main unit / device | `0` / `0` |
| MD5 | `f65689e9a4506871363898d439783847` |
| SHA-1 | `c7938a9c8f3c7282b94714ad0e53619bf8b190ad` |
| SHA-256 | `012d25b1a507a8cbc75fe95589708f143ade823f5e19f587af80e0a22cbf0788` |

Addresses below are `0x08000000 + file_offset`.

### Header and embedded-header scan

* Complement check at `0xBD` = `0x25`; recomputed as
  `chk = 0; for i=0xA0..0xBC: chk -= rom[i]; chk = (chk - 0x19) & 0xFF`
  gives `0x25` (valid).
* `0xBE`–`0xBF` are the **reserved area** and are zero-filled, which is the
  required value. (The workflow guide's header table labels this pair "header
  checksum"; GBATEK defines it as reserved, and the real header check is the
  `0xBD` complement byte. The zero here is correct, not a dump error.)
* The 156-byte Nintendo logo was scanned across the whole 4 MiB image. There is
  **exactly one** hit, at file offset `0x4`, i.e. one GBA header at `0x0`.
  This is a single-game image, not a multi-game pack or concatenation.
* Entry word at `0x0` = `0xEA0EA459`. Decoded as an ARM branch this targets
  `0x0803A16C`, not the common `0x080000C0`; the conventional crt0 is present
  at `0x080000C0` and the ROM boots normally in mGBA. The first word is
  recorded here as nonstandard for this dump.

Save media: mGBA produced a **512-byte `.sav`**, i.e. EEPROM-512 class. The
save layout itself was not reversed (not needed for this question).

---

## 2. Executive summary

**This build has no password, code-entry, or button-cheat system.** All six
main-menu screens were walked, including every sub-screen and the in-game pause
menu. No screen accepts a code; the only free-text input in the whole game is
the PDA profile name/phone editor. Keyword, literal-table, pointer-table and
key-mask scans found no validator, table or sequence. Published cheat sources
contain no in-game codes for this title (GameFAQs lists only GameShark/
CodeBreaker memory codes; VGChartz reports 0 cheats; TCRF documents only unused
debug text and gives no access method).

What *is* shipped and developer-intended is the **Options sound test**:

* **Music Test** — 38 values, `00`–`37`, wrapping in both directions.
  The 38 values correspond in count and order to the ROM's 38-entry
  BGM/screen-name list (`Rocket mini game` … `Title bgm`). This exposes all 38
  tracks from the start, while the Customize music selector has only 15 slots
  at this save — a shipped developer shortcut around the unlock progression.
* **SFX Test** — 60 values, `00`–`59`, wrapping in both directions.
  The ROM's debug SFX name block has 53 names and a `001`–`057` index strip;
  IDs `53`–`59` are accepted by the shipped menu but have no name entry.
* **`???????`** — a locked fourth row, inferred to be the Credits viewer
  documented in the manual ("view the credits once they have been unlocked").
* **MUSIC/SFX** — an on/off toggle.

The ROM also contains an **unused debug asset viewer**: seven modes
(`GAME BG`, `GAME ANI`, `GAME ANI W/BG`, `GAME BGM`, `GAME SFX`, `EDIT BG`,
`EDIT OBJ`) and a build date `07/23/2004`, with 32 area names, 81 animation
names, 38 BGM/screen names and a 53-name SFX list. The menu's rendering and
navigation code exists, but its visibility byte (`task+0xAD4`) is never set by
any input path found in this build; the only reference to the renderer comes
from a boot-time task record. It is present as data/code, not reachable from
the retail UI. This matches TCRF's classification as unused text.

Because no code system exists, the guide's "mint a novel code" requirement is
replaced by the negative-result proof in §6b: all menus enumerated, all text/
button spaces searched with counts, and the only hidden menu (Options sound
test) fully enumerated with its wraparound bounds proven in the emulator.

---

## 3. How to reproduce

### Emulator and tools

```bash
Xvfb :131 -screen 0 1024x768x24 &
DISPLAY=:131 openbox &
DISPLAY=:131 SDL_AUDIODRIVER=dummy mgba -3 \
  "roms/All Grown Up!: Express Yourself/All Grown Up!: Express Yourself.gba" &
```

mGBA 0.10.5 (`/usr/games/mgba`). Default SDL keymap used throughout:
A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. Keys were held 200–350 ms; menu transitions take 1–3 s.

The emulator was run on a private display (`:131`) with its own Xvfb and
openbox. No other display or emulator process was touched.

### Menu paths (all observed)

```
Title (Start)
└─ NEW GAME / CONTINUE            (CONTINUE loads the existing 512-byte save)
   └─ CONTENTS — six icons, 3×2:
      top row:    STORY CHASE | MINI-GAMES | CUSTOMIZE
      bottom row: PDA         | ACCESSORIZE | OPTIONS
```

Navigation is spatial: Left/Right within a row, Up/Down between rows. `B`
backs out one level; `B` at the main menu returns to the title screen.

```
STORY CHASE → corkboard with a NEW envelope → A
             → context menu: ENTER | EXIT | CLASS PAPER | CONTINUE
             → ENTER → mission dialogue → mission ("MISSION START")
Pause (Start in a mission) → NOTEBOOK | To Main Street | Quit
```

`MINI-GAMES`, `CUSTOMIZE`, `PDA`, `ACCESSORIZE` and `OPTIONS` each open the
screens documented in §6. The in-game `NOTEBOOK` opens a blank two-page
notebook at this save (no entries collected yet).

### Sound-test reproduction (bounds)

From a save that has passed the title:

```
CONTINUE → main menu → Down (PDA) → Right (Accessorize) → Right (Options) → A
```

* `MUSIC TEST` starts at `00`. Pressing Right at `37` wraps to `00`;
  pressing Left at `00` wraps to `37`.
* Select `SFX TEST` with Down. Pressing Right at `59` wraps to `00`;
  pressing Left at `00` wraps to `59`.
* `???????` does not open with A at this save (credits not yet unlocked).
* `MUSIC/SFX` toggles ON/OFF with A (or Left/Right).

Observed screenshots in this folder:

| File | State |
|---|---|
| `All Grown Up! Express Yourself - main menu.png` | six-icon CONTENTS menu |
| `All Grown Up! Express Yourself - options sound test.png` | Options, Music 00 / SFX 00 / ??????? / ON |
| `All Grown Up! Express Yourself - music test 37.png` | Music Test = 37 (last value) |
| `All Grown Up! Express Yourself - sfx test 59.png` | SFX Test = 59 (last value) |
| `All Grown Up! Express Yourself - minigame select.png` | Mini-Game Select, entry 1 |
| `All Grown Up! Express Yourself - customize.png` | Customize, three counters |
| `All Grown Up! Express Yourself - pda keyboard.png` | PDA profile name keyboard |
| `All Grown Up! Express Yourself - accessorize.png` | Accessorize grid |
| `All Grown Up! Express Yourself - pause menu.png` | in-game pause menu |
| `All Grown Up! Express Yourself - story chase board.png` | Story Chase corkboard |

### Button-combination tests (all negative)

Tested in the emulator; no screen change other than the normal button effect:

| Where | Combination | Result |
|---|---|---|
| Main menu | L+R+Select (held 2 s) | no change |
| Main menu | L+R+Start (held 2 s) | no change |
| Main menu | A+B+Select | B backed out to title (normal) |
| Title | Select | no change |
| Title | L+R+Select (held 1.5 s) | no change |
| Title | L+R+Start (held 2 s) | no change |
| Title | Konami sequence U U D D L R L R B A | final A opened the main menu; no debug screen |
| Options | Select | no change |
| Options | L+R+Select | no change |
| Options | L / R | scrolls the decorative bottom strip only |
| Boot | Select held for the first 8 s of a fresh boot | normal intro and title; no debug overlay |

These are recorded as tested negatives, not as proof that no sequence exists in
every possible revision; the static search below is the primary bound.

### Published sources consulted

| Source | Content relevant here |
|---|---|
| `https://tcrf.net/All_Grown_Up!:_Express_Yourself` | Lists the debug menu text/area/animation/BGM/SFX names and build date; no access method given |
| `https://gamefaqs.gamespot.com/gba/925094-all-grown-up-express-yourself/cheats` | GameShark and CodeBreaker memory codes only; no passwords/secrets (direct fetch 403; content from search-result snippets) |
| `https://www.vgchartz.com/game/14961/all-grown-up-express-yourself/cheats` | "Total cheats available: 0" |
| `https://www.videogamemanual.com/gba/All%20Grown%20Up!%20-%20Express%20Yourself%20(USA).pdf` | Six main-menu choices; documents the Options music/SFX test and unlockable credits; no codes |

---

## 4. Address map

| Address / range | Meaning |
|---|---|
| `0x04000130` | GBA `KEYINPUT` (active-low) |
| `0x08000AE4` | Input update: reads `KEYINPUT`, builds pressed/held/released |
| `0x03002160` | Key-state struct base used by all game code |
| `0x03002160` +0 | pressed edge bits (active-high) |
| `0x03002160` +2 | held bits |
| `0x03002160` +4 | released bits |
| `0x03002160` +8 | packed direction/repeat state |
| `0x0201C000` | Sound-state base |
| `0x0201C21A` | u16 current BGM ID (UI value + 1); observed `0x18`/`0x19` ↔ UI `23`/`24` |
| `0x0807738F` | Area-name table, 32 records × 19 bytes (`Town area 1` … `Shopping mall 9`) |
| `0x08077625` | Debug mode labels, 7 records × 16 bytes (`GAME BG` … `EDIT OBJ`) |
| `0x080776AA` | Build date string `07/23/2004` |
| `0x080779C0` | Animation-name table, 81 names in 23-byte records (grouped per character) |
| `0x0807879E` | BGM/screen-name table, 38 records × 26 bytes (`Rocket mini game` … `Title bgm`) |
| `0x08078C30` | SFX index strip `001…057`; name block starts `0x08078CE5`, 53 names |
| `0x08043CB4` | Debug-viewer renderer: draws mode labels + selected name |
| `0x0804476C` | Debug-viewer page dispatcher (8 pages, page byte `+0xA8C`) |
| `0x080448BC` | Page navigation: Up/Down move page, A/Start accept |
| `0x080436FC` | Debug-viewer task update; calls `0x0804476C` when `[task+0xAD4] == 1` |
| `0x081CCB20` | Task/script record; pointer `0x080436FD` stored at `0x081CCB5C` |
| `0x081A5900` | Boot-time script/task table; entry 20 = `0x081CCB24` |
| `0x0801E08`, `0x0801D14` | Called by the sound-test state machine at `0x080022A4` when the selection changes; individual roles not separately proven |

Key masks (active-high, from `0x03002160`):
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200`.

---

## 5. Algorithm

### 5.1 Code/password validator

There is none. No function reads a code buffer, no alphabet table is used for
comparison, and no return value maps to an unlock. In the reachable UI the only
text-input surface is the PDA profile editor, whose keyboard writes a name/phone
string into the save; it is not compared against any constant.

### 5.2 Options sound test (shipped developer test)

The two numeric fields are closed-ring byte selectors:

```text
music_id: 0..37          (38 values)
  Right: music_id = (music_id + 1) mod 38
  Left : music_id = (music_id + 37) mod 38

sfx_id:   0..59          (60 values)
  Right: sfx_id = (sfx_id + 1) mod 60
  Left : sfx_id = (sfx_id + 59) mod 60
```

Pressing Right/Left starts/stops the corresponding BGM/SFX through the sound
engine. The displayed value is `music_id`/`sfx_id` as a two-digit decimal.
Observed wraps prove the modulus: `37→00` on Right and `00→37` on Left for
music; `59→00` on Right and `00→59` on Left for SFX.

The music selector's 38 values match the 38-entry BGM/screen-name table at
`0x0807879E`; the ID-to-name order is inferred from the matching count and the
debug viewer's use of the same table (audio was not captured, so the mapping is
not claimed as heard). The SFX selector has 60 values while the debug SFX name
block has 53 names; IDs `53`–`59` are therefore unnamed extras accepted by the
menu.

### 5.3 Debug asset viewer (present, not reachable)

Intended model, derived from the renderer and the name tables:

```text
mode = 0..6                    # GAME BG .. EDIT OBJ
page = 0..7                    # navigation page + seven modes
index[mode] selects a record from:
   mode 0 "GAME BG"      -> area-name table (32)
   mode 1 "GAME ANI"     -> animation-name table (81)
   mode 2 "GAME ANI W/BG"-> same animation table
   mode 3 "GAME BGM"     -> BGM/screen table (38)
   mode 4 "GAME SFX"     -> SFX name block (53 names)
   mode 5 "EDIT BG"      -> editor background selection
   mode 6 "EDIT OBJ"     -> editor object selection
renderer draws the selected name and the build date.
```

The viewer is wired as a boot-time task (`0x081A5900` entry 20 →
`0x081CCB20`), and its update only calls the renderer when the byte at
`task+0xAD4` is 1. Static reference closure:

* `0x08077625` (mode labels) is referenced only at `0x080440B8`, inside the
  renderer `0x08043CB4`.
* `0x08043CB4` is called only from `0x0804478A`, inside the page dispatcher
  `0x0804476C`.
* `0x0804476C` is called only from `0x0804371C`, inside the task update
  `0x080436FC`.
* `0x080436FC` appears as a function pointer only at `0x081CCB5C`, inside the
  task record reached from the boot script table.

No key-state consumer (the 214 literal references to `0x03002160`) reaches
this chain, and no menu walked in the emulator opened it. The visibility byte
is not set by any input path found. This is the basis for "unused/unreachable"
in this build.

---

## 6. Tables

### 6.1 Main menu (CONTENTS), six entries

| Position | Icon | Label |
|---|---|---|
| top-left | Angelica photo | `STORY CHASE` |
| top-middle | TV/console | `MINI-GAMES` |
| top-right | claw/jukebox machine | `CUSTOMIZE` |
| bottom-left | laptop | `PDA` |
| bottom-middle | treasure chest | `ACCESSORIZE` |
| bottom-right | wrench/screwdriver | `OPTIONS` |

### 6.2 Mini-Game Select (8 entries; 1 unlocked at this save)

| # | Name | State |
|---|---|---|
| 1 | Angelica Ball Toss | unlocked |
| 2 | Chuckie Picture Mix | LOCKED |
| 3 | Phil Rafting Rush | LOCKED |
| 4 | Kimi Burger Toss | LOCKED |
| 5 | Dil Blast Off | LOCKED |
| 6 | Susie Susie Says | LOCKED |
| 7 | Tommy ACTION! | LOCKED |
| 8 | 2P Battle (`MULTI PLAYER`) | LOCKED |

The manual says eight mini-games, three with a two-player challenge mode; the
eighth entry is the multiplayer selector.

### 6.3 Unlock / collection counters (observed)

| Screen | Counters |
|---|---|
| CUSTOMIZE — music | `01/15` … `15/15` |
| CUSTOMIZE — wallpaper/background | `01/15` … `15/15` |
| CUSTOMIZE — character | `01/25` … `25/25`; locked entries draw a `?` silhouette |
| ACCESSORIZE | 8 accessory slots, all `unknown`; plus `LINK` |
| OPTIONS — `???????` | locked at this save; inferred Credits viewer |

### 6.4 Options menu

| Row | Values |
|---|---|
| `MUSIC TEST` | `00`–`37` (38) |
| `SFX TEST` | `00`–`59` (60) |
| `???????` | locked (A has no effect) |
| `MUSIC/SFX` | `ON` / `OFF` |

### 6.5 Music Test ID table (38, ROM order at `0x0807879E`)

```text
00 Rocket mini game          19 Camera Boy
01 Volleyball                20 Slide Puzzle
02 Staff roll                21 X-treme Rafting
03 Edit menu ragrats1        22 Midnight Delivery
04 Edit menu oriental        23 Hamburger Panic
05 Edit menu classic         24 Fashion Cordinator
06 Edit menu pop_3           25 Humming Expert 3
07 Edit menu pop_2           26 Humming Expert 2
08 Edit menu pop_1           27 Humming Expert 1
09 Edit menu Kimi Screen     28 Pause Menu
10 Edit menu Susie Screen    29 Town
11 Edit menu Lil Screen      30 School
12 Edit menu Phil Screen     31 Forest
13 Edit menu Dil Screen      32 Residential Area
14 Edit menu Chuckie Screen  33 Main Street
15 Edit menu Tommy Screen    34 Game clear
16 Edit menu Angelica Screen 35 Game over
17 Result Screen             36 Main menu
18 Mission, Mini-Game Menu   37 Title bgm
```

IDs `00`–`02` are the three "special" animations/tracks; `03`–`16` are the
fourteen Edit-menu themes; `17` onward are results, mission/menu, mini-game,
area, and title music. This order is read from the 26-byte records.

### 6.6 Debug-viewer data (unused)

| Table | Address | Records |
|---|---|---|
| Area names | `0x0807738F` | 32 (`Town area 1` … `Shopping mall 9`) |
| Mode labels | `0x08077625` | 7 (`GAME BG`, `GAME ANI`, `GAME ANI W/BG`, `GAME BGM`, `GAME SFX`, `EDIT BG`, `EDIT OBJ`) |
| Build date | `0x080776AA` | `07/23/2004` |
| Animation names | `0x080779C0` | 81 names in 21 character groups (Angelica 16, Tommy 4, Kimi 3, Lil 3, Phil 4, Dil 4, Susie 2, Chuckie 4, Sagi 2, Spike 3, Harold 3, Savannah 4, Shone 4, Jastin 3, Nicol 4, Jii 4, Bigfoot 3, Teacher woman 3, Teacher man 3, Chuckie fat 2, Chuckie mot 3) |
| BGM/screen names | `0x0807879E` | 38 (same list as §6.5) |
| SFX names | `0x08078C30` | index strip `001`–`057`; 53 names (`Start` … `Result screen`) |

The area table is 19 bytes/record; the BGM table 26 bytes/record; animation
records are 23 bytes with inter-group padding. The SFX block is a text blob of
variable-width, space-padded names; its exact per-ID mapping was not needed and
is not claimed.

The 32 area entries, in ROM order, are: `Town area 1`–`Town area 5`;
`Forest area 1`–`Forest area 3`; `Room Dill`, `Room Kimi`, `Garden Party`,
`Room Phil`, `Room Susie`; `School area 1`–`School area 10`;
`Shopping mall 1`–`Shopping mall 9`.

### 6.7 PDA name keyboard (the only text entry)

The profile editor's keyboard is an 8-column grid containing `A`–`Z`, `a`–`z`,
`0`–`9`, and the punctuation `. , ' " - / : ; ( ) & % + = × ÷`, with an `End`
key. It writes the profile name/phone fields; it is not an alphabet for a code
and no comparison routine consumes its buffer.

---

## 6b. Enumeration

### Space definition

| Space | Size | Notes |
|---|---:|---|
| In-game passwords / codes | **0** | no entry screen, no validator, no literal table |
| Button-code sequences | **0 found** | no referenced mask table; no sequence check in walked screens |
| Music Test | **38** | `00`–`37`, closed ring |
| SFX Test | **60** | `00`–`59`, closed ring; 53 named + 7 unnamed |
| Mini-games | **8** | 1 unlocked, 7 locked at this save |
| Customize | **55** | 15 music + 15 wallpapers + 25 characters |
| Accessorize | **9** | 8 accessories + LINK |
| Credits | **1** | locked `???????` row |

### Novel / unpublished selections entered in-game

No published list documents this game's sound test or its last IDs. Two values
outside any documented list were selected and screenshotted:

1. **Music Test `37`** — the last music value, matching `Title bgm` in the
   38-entry table. Reached by `Left` from `00` (wrap) and by counting up from
   `00`; screenshot `music test 37.png` shows `MUSIC TEST ►37◄`.
2. **SFX Test `59`** — the last SFX value, two past the highest value in the
   `001`–`057` index strip and outside the 53-name SFX block. Reached by
   `Left` from `00` (wrap); screenshot `sfx test 59.png` shows
   `SFX TEST ►59◄`. The menu accepts the value without a crash or a name.

These are menu selections, not memory writes; nothing was patched or forced.

### Bounds proven by rejection/wrap

The UI has no free-text code field, so the relevant bound is the selector ring.
All four boundaries were exercised in the emulator:

| Test | Result |
|---|---|
| Music `37` + Right | `00` (wrap; screenshot sequence `m37` → `m00`) |
| Music `00` + Left | `37` (wrap) |
| SFX `59` + Right | `00` (wrap; `sfx57` → `58` → `59` → `00`) |
| SFX `00` + Left | `59` (wrap) |

An out-of-range value cannot be entered: the selector is a closed ring and
there is no keyboard/code field to reject. The only text keyboard in the
reachable UI (PDA name/phone) accepts a name string, not a code; there is no
comparison of that buffer against any constant in the ROM.

### Negative result for codes

* **Screens walked:** title; NEW GAME/CONTINUE; CONTENTS (6/6);
  STORY CHASE board + context menu; mission dialogue; in-game pause;
  NOTEBOOK; MINI-GAMES (8/8 entries, locked states); CUSTOMIZE (3 categories);
  PDA (profile, name keyboard, friends grid); ACCESSORIZE; OPTIONS (4 rows).
  That is every menu reachable from the main menu at this save. There is **no
  gallery screen**: the six CONTENTS entries above are exhaustive, and the
  closest collection screens are CUSTOMIZE and ACCESSORIZE.
* **Text search:** `strings -t x -n 4` produced **36,430** strings. Keywords
  `password`, `passwd`, `cheat`, `debug`, `unlock`, `gallery`, `code`, `enter`,
  `invalid` each returned **0** case-insensitive hits; `secret` returned **1**,
  inside story dialogue ("They were keeping it secret though"). There is no
  ASCII `PASSWORD`, `CODE`, `DEBUG`, `SECRET`, `UNLOCK` or `ENTER CODE` literal
  (all 0 exact-uppercase hits). Visible UI labels are tile graphics, not ASCII:
  `CONTENTS`, `STORY CHASE`, `OPTIONS`, `NEW GAME`, `CONTINUE` all have 0
  literal ASCII hits.
* **Button space:** a full-ROM scan for u16 arrays of single-bit key masks
  (length ≥ 4) found **348** raw runs. Only **1** is referenced by a 32-bit
  pointer: the pointer word at `0x08004430` targets `0x0806E73C`, which is the
  `20 00 40 00 20 00 40 00` data immediately after the `MultiSioSync010214`
  serial string. It is not a sequence table and no code reads it as one.
  Referenced mask tables matching a button code: **0**.
* **Validator space:** no code buffer, alphabet table, strcmp loop,
  checksum constant, or length branch for a password was found. The Options
  sound test is the only numeric "test" UI; it is an index ring, not a
  validator.
* **Published codes tested:** no in-game code exists to test. GameFAQs'
  cheats page for this title contains only **GameShark/CodeBreaker** memory
  codes (excluded by scope); VGChartz reports **0 cheats**; TCRF documents only
  the unused debug text and gives no access method; the manual documents the
  Options sound test/credits but no codes.

---

## 7. Validation evidence

### Observed (emulator screenshots/state)

* Title, NEW GAME/CONTINUE, CONTENTS six-icon menu, Story Chase board,
  mission context menu, mission start, in-game pause menu.
* Mini-Game Select with eight entries; entry 1 unlocked, entries 2–8 `LOCKED`.
* Customize counters `01/15`, `01/15`, `01/25` (and selectable locked `?`
  character at `25/25`).
* PDA profile screen, 8-column name keyboard, friends grid.
* Accessorize 3×3 grid: eight `unknown` slots + `LINK`.
* Options: `MUSIC TEST`, `SFX TEST`, locked `???????`, `MUSIC/SFX ON`.
* Music selector values `00`, `23`, `24`, `36`, `37`; `37→00` and `00→37`.
* SFX selector values `00`, `56`, `57`, `59`; `59→00` and `00→59`.
* All button-combination tests in §3 produced no debug screen.

### Derived (instruction/tables)

* Key-state struct at `0x03002160`; masks A=1 … L=0x200; input routine at
  `0x08000AE4`.
* Sound-test ring sizes 38 and 60 from the observed wraps; 38 matches the
  38-record BGM table exactly.
* Debug-viewer reference closure (§5.3) and the presence of 32 area names,
  81 animation names, 38 BGM/screen names, 53 SFX names, 7 mode labels and the
  build date.
* No referenced u16 key-mask table; no password validator (static scans).

### Inferred (not directly exercised)

* `???????` is the Credits viewer (manual: credits unlockable; it is the only
  locked Options row).
* Music Test ID order equals the BGM table order; the counts match, but audio
  was not captured (SDL audio dummy), so playback itself is not claimed.
* Debug-viewer mode behavior (`GAME BG` shows a background, `GAME ANI` plays an
  animation, etc.) from the labels and the tables; the menu was never opened.
* Debug-viewer unreachability: based on the reference closure and the negative
  input tests, not on a debugger watchpoint on `task+0xAD4`.

---

## 8. Unknowns

* Whether a different revision/region (e.g. the PAL build) wires the debug
  viewer to an input gate. This USA Rev.00 image shows none.
* An inline (non-table) button sequence implemented as a chain of per-frame
  `cmp`/`and` checks cannot be excluded by a whole-ROM table scan. The negative
  for button codes is bounded by: the 348 candidate u16 mask runs (0 meaningful
  references), the debug-viewer reference closure, and the combinations tested
  in §3.
* The exact per-ID mapping of SFX `53`–`59`; the ROM name block has 53 names
  and the menu exposes 60 IDs, but the extra IDs have no names to compare.
* The real label behind `???????` (tile graphics, not ASCII). Credits is the
  manual-supported inference, not a decoded string.
* Whether the 38 music IDs are in the same order as the name table (count
  match only; audio not captured).
* Save flags for credits/mini-game unlocks were not reversed; the 512-byte
  EEPROM save layout is out of scope for this question.

---

## 9. Tooling

* `mgba` 0.10.5 (`/usr/games/mgba`), SDL, `-3` scale, private `Xvfb :131` +
  `openbox`, `xdotool`, ImageMagick `import`/`convert`.
* `arm-none-eabi-objdump -D -b binary -marm -M force-thumb` for raw Thumb.
* Python 3 scripts in `/tmp/opencode/allgrownup/`:
  * `phase0.py` — header, hashes, complement/checksum, Nintendo-logo scan.
  * `ptr.py` / inline scanners — 32-bit literal-pointer searches.
  * BL-target scanner — call-site recovery for `0x08043CB4`, `0x0804476C`,
    `0x080436FC`, etc.
  * u16 single-bit-mask sequence scanner — 348 raw runs, 1 pointer reference.
  * `statediff.py` — reads mGBA PNG savestates (`gbAs` chunk + zlib),
    decompresses the 397,312-byte state and diffs two nearby states to locate
    the BGM ID at `0x0201C21A`.
* mGBA savestates (`*.ss1`) are PNG screenshots with a zlib-compressed `gbAs`
  state chunk; they were used only for navigation, not for memory edits.

### Legal note

No ROM, extracted graphics, music, or text is redistributed. The screenshots
in this folder are menu-state evidence only (title/menu labels and counters),
captured from the locally owned ROM; no sprite sheets or audio were extracted.

---

## 10. Summary answer

For this exact ROM (`SHA-256 012d25b1…0788`): **no password, code, or button
cheat system exists in the retail build.** The developer-intended hidden
surface is the shipped Options sound test (38 music IDs, 60 SFX IDs, wrapping,
plus a locked row inferred to be credits) and the normal unlockables (8 mini-games,
15/15/25 customization items, 8 accessories). The ROM also contains an unused
debug asset viewer with area/animation/BGM/SFX lists and build date
`07/23/2004`; its code is present but no input path in this build sets its
visibility byte.
