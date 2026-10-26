# Bionicle: Maze of Shadows (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Bionicle: Maze of Shadows.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title (`0xA0`) | `BIONICLE` |
| Game code (`0xAC`) | `BILE` |
| Maker code (`0xB0`) | `78` |
| Software version (`0xBC`) | `0` |
| Fixed byte `0xB2` | `0x96` (valid) |
| Complement check (`0xBD`) | `0x81` — computed `0x81`, valid |
| Header checksum (`0xBE`) | stored `0x0000`; over `0xA0..0xBC` it computes to `0x9A`. The same "zero stored checksum" pattern appears in other dumps of this collection, so it is a dump/tool artefact and **not** treated as a patch. |
| Entry word (`0x00`) | `0xEA00002E` → ARM branch to `0x080000C0` |
| MD5 | `f4f51f42af0fcf96a1c33705f7f5ce08` |
| SHA-1 | `34edcd0c8e951533d9b4641dfaefe2c762ded019` |
| SHA-256 | `392489956f8d64f6d9e8e287e40eb4bbf4c45adf54060d02e7f7fef598f8ccb3` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at file `0x4` (i.e. one GBA header at `0x0`). This is a single-cartridge image, not a multi-game pack. The image is exactly 8 MiB; its final 256 bytes are zero padding. No trainer/patcher strings were found.

## 2. Executive summary

This ROM contains **no password system, no button cheat code and no player-reachable cheat menu**. The word "password" appears **zero** times in the whole ROM; "secret" and "level select" also appear zero times.

It does contain a **hidden developer level-select**, left in the front end:

* A generic menu-page container uses screen id `13`. The page index lives at `0x020011D8`.
* Page `0` at screen `13` is an **uninitialised/fallback page**, and that fallback is a two-stage developer warp menu:
  * first a list of **Level1 … Level6**,
  * then a per-level list of **Part1 … Part5 / EndScene**.
* Normal code enters screen 13 with page `25`, `27`, `29`, `30` or `31` (endings, options, …). **No code path enters screen 13 with page 0**, so the menu is not reachable through the player-visible menu graph. The only public route is the RAM write published on TCRF (`020011D4 0D`), which this report reproduces.
* The warp menu is real and complete: all 24 entries (4+3+4+4+3+6) were selected in the emulator and every one produced playable content (a map/spawn or a cutscene).

The published lists were checked and are consistent with this: TCRF documents only the RAM code, VGChartz lists **0 cheats**, and the GameShark/CodeBreaker sets on Neoseeker/GameFAQs are memory-edit codes (explicitly out of scope for this engagement).

An unrelated 16-symbol alphabet exists in the ROM (`BDFGHIKPRSTVWXYZ`) and is used by an in-game message widget that renders a 16-cell symbol picker; it is not reachable from any front-end menu and is not a password system for cheats (see §8).

## 3. How to reproduce

### Emulator and keymap

```
Xvfb :185 -screen 0 1024x768x24 &
DISPLAY=:185 openbox &
DISPLAY=:185 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 game.gba &
```

mGBA SDL default keys: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows. The ROM must be launched from a copy (`/tmp/opencode/mazeofshadows/game.gba`) so generated saves stay out of the ROM folder.

### Walking the normally reachable menus (all observed)

1. Boot → legal screen → LEGO → THQ → Razorback → language select (English/Deutsch) → title (`Press START`).
2. `Start`, `Start` → main menu (screen id `10`): `Story Mode`, `Battle Mode`, `Tunnel Flight Challenge`, `Multiplayer` (greyed), `Options`.
3. `Options` → `Effects Volume`, `Music Volume`, `Credits` (screen id `13`, page `31`). The third item scrolls the credits; the credits end on a "Game Over / You Win / Thank you for playing!" page (screen `13`, page `25`).
4. `Story Mode` → `New Game` (id `11`) → `Are you sure? No / New Game` (id `12`) → story cutscene → gameplay.
5. `Battle Mode` → `Battle 1` (id `14`), then battle sub-screens.
6. `Tunnel Flight Challenge` → `Enter your name` (id `16`), `Tunnel Flight Best` (id `17`).
7. In gameplay, `Start` opens the pause menu: `USE ITEM`, `VIEW TOA METRU`, `RAHI CHRONICLE`, `RESTART LEVEL`, `QUIT`; each was opened and screenshotted. `QUIT → YES` returns to the main menu.
8. Screen-id sweep: forcing each front-end id `0..31` (id at `0x020011D4`, phase `0x020012D0=2`), plus the ids reached by normal transitions (`32..36`), enumerated the whole front end: legal/logo/title/language/credits/main menu/New Game/confirm/menu-page container/Battle/Tunnel Flight/name entry/best/Game Over/save/volume/character splash. No other hidden screen exists.

### Reaching the hidden developer level select (analysis procedure, not a game cheat)

This is how the evidence below was produced. It is a debugger write, not something the retail game offers.

1. Reach the main menu (screen id `10`; page `0x020011D8` is still `0`, because the main menu does not set a page).
2. In the mGBA CLI debugger (`mgba -d`):
   ```
   w/1 0x020011d4 0x0d      # screen id = 13
   w/1 0x020012d0 0x02      # ask the screen manager to (re)enter the screen
   ```
   (advance a few frames)
3. The fallback page for screen 13 is the developer warp menu: `Level1 … Level6`.
4. `Up`/`Down` select a level, `A` (or `Start`) opens that level's part list, `Up`/`Down` choose a part, `A` loads it, `B`/`Select` backs out.

The published TCRF code is the same first write (`write byte 0x0D to 0x020011D4`). On this engine the byte alone does not force an already-loaded screen to re-enter; the phase byte `0x020012D0 = 2` (or an equivalent screen transition) is required. This document reports that dependency rather than hiding it.

### Codes/sequences tested

| Input tested | Where | Result |
|---|---|---|
| `L,L,R,L,Select,Start,A` (2003 *Bionicle* GBA secret menu) | main menu | rejected — `A` simply confirms `Story Mode`; screen id became `37`, no debug menu |
| `L,L,R,L,Select,Start` | main menu | rejected — `Start` confirms `Story Mode` |
| `L,R,L,R,L,R` | main menu | rejected (screen id remained `10`) |
| `Select,Start,A` | main menu | rejected (`Start` confirms) |
| `L,L,R,R,L,L` | main menu | rejected (screen id remained `10`) |
| Konami (`Up,Up,Down,Down,Left,Right,Left,Right,B,A`) | main menu | rejected (`A` confirms `Story Mode`) |
| TCRF `020011D4 = 0x0D` | main menu | **accepted** (with phase nudge) → developer level select |

The six button sequences were tested at the main menu, the only free-cursor screen where such a code would normally live; none of them produced a new screen or wrote screen id 13. The title, Options, Battle, Tunnel Flight and pause screens were walked normally and expose no extra branch.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x020011D4` | Current screen/mode id (byte used by the front-end dispatcher). Observed values: `10` main menu, `13` menu-page container, `37+` in-game/cutscene, `74/86` late-game scenes. |
| `0x020011D8` | Page id inside the screen-page container (`0` = uninitialised/fallback; `25`, `27`, `29`, `30`, `31` = real pages). |
| `0x020012D0` | Screen phase/state byte. `2` makes the front end re-enter/initialise the current screen. |
| `0x020011CC` | Page data pointer (e.g. `0x0846602C` for the "Thank you" page). |
| `0x08466080` | Table of 28-byte page/screen layout records, indexed by `0x020011D4` (entry 13 at `0x084661EC`). |
| `0x08462E1C` | ASCII `"DEBUG SELECT"` (file `0x462E1C`). |
| `0x08462E2C` | ASCII `"DEBUG Battles ON"` (file `0x462E2C`). |
| `0x08462E40` | ASCII `"DEBUG Battles OFF"` (file `0x462E40`). |
| `0x08462E64` | `"Part1"`, then `Part2…Part5`, `EndScene` (`0x08462EB4`). |
| `0x08462E6C` | `"Level1"`, then `Level2…Level6` (`0x08462EC0`). |
| `0x08462EE8` | 16-symbol alphabet `"BDFGHIKPRSTVWXYZ"` (file `0x462EE8`). |
| `0x08035FBC` | Generic message/panel renderer. Its state/type branch at `0x08036018` draws the 16-symbol alphabet grid from `0x08462EE8` (index loop 0..15). |
| `0x08038FFC` | Part-select handler: requires screen id `13`, page `0x020011D8` in `25..34`, selection `1..5`; jump table at `0x0803902C` (5 entries). |
| `0x08038308` | 10-entry page jump table (page ids `25..34`). |
| `0x080028B4` | Transition code that writes screen `13` **and** page `25`. |
| `0x0800174C` | Transition code that writes screen `13` **and** page `27`. |
| `0x0800294E` | Transition code that writes screen `13` **and** page `30`. |
| `0x08002A00` | Transition code that writes screen `13` **and** page `29`. |
| `0x08002A72` | Transition code that writes screen `13` **and** page `27`. |
| `0x0800093C` | Dead "BIONICLE check": compares four bytes at `0x0008AC00` with `B,I,L,E`. The literal pool word is `0x0008AC00`, not the cartridge header/game-code `0x080000AC`, so the comparison can never match the intended string and the function returns 0. |
| `0x08047A68` | Input tick (key edge detection), called once per frame. |
| `0x080008AE` | Main loop idle point (useful debugger anchor). |

## 5. Algorithm / pseudocode

### Screen dispatch and the fallback page

```
screen = u8[0x020011D4]
page   = u8[0x020011D8]
phase  = u8[0x020012D0]

# front-end transition helpers always set a real page:
enter_screen(13, page) where page in {25, 27, 29, 30, 31}   # observed pages

# forcing only the screen id, while page is still 0, lands on the fallback page
if screen == 13 and page == 0:
    draw_debug_level_list()        # Level1..Level6
```

The front end begins with `page = 0` (the main menu never writes a page). That is why a single forced `screen = 13` shows the developer list instead of any legitimate page.

### Developer level select

```
levels = ["Level1","Level2","Level3","Level4","Level5","Level6"]
parts  = {
  "Level1": ["Part1","Part2","Part3","Part4"],
  "Level2": ["Part1","Part2","Part3"],
  "Level3": ["Part1","Part2","Part3","Part4"],
  "Level4": ["Part1","Part2","Part3","Part4"],
  "Level5": ["Part1","Part2","Part3"],
  "Level6": ["Part1","Part2","Part3","Part4","Part5","EndScene"],
}

Up/Down: cursor = clamp(cursor +/- 1, first, last)   # observed: no wrap
A or Start: if list is the level list -> open parts[level]
            else                     -> load(level, part)
B or Select: back / exit
```

The part handler at `0x08038FFC` additionally range-checks the page (`0x020011D8` in `25..34`) and a selection index `1..5`, which matches the real page ids used by the normal menus.

## 6. Tables

### Front-end screen ids observed (`0x020011D4`)

| id | Screen | id | Screen |
|---:|---|---:|---|
| 0 | legal/copyright | 16 | `Enter your name` (Tunnel Flight) |
| 1 | legal/copyright (2) | 17 | `Tunnel Flight Best` |
| 2 | LEGO logo | 18 | `Game Over / Battles 0` |
| 3 | THQ logo | 19 | Game Over |
| 4 | Razorback logo | 20 | Game Over |
| 5 | language select (English/Deutsch) | 21 | `Battle Mode / Tunnel Flight Challenge` |
| 6 | title (English) | 22 | `Connecting. Please wait…` (link) |
| 7 | title (German) | 23 | `Game Over / You Win` |
| 8 | credits (page 1) | 24 | `Game Over / You Lose` |
| 9 | credits (page 2, Razorback) | 25 | `Begin Battle` ×3 |
| 10 | **main menu** | 26 | results (`Tunnel Flight Time`) |
| 11 | `New Game` | 27 | `Tunnel Flight Best / Tunnel -1` |
| 12 | `Are you sure? No / New Game` | 28 | `Now saving. Do not turn off power!` |
| 13 | **menu-page container** (Options / debug fallback / endings) | 29 | `Music Volume` |
| 14 | `Battle 1` | 30 | `Effects Volume` |
| 15 | `Battle 1` (second battle screen) | 31 | MATAU character splash |
| | | 32–36 | story/mode setup screens |

### Debug level-select space (24 entries)

| Level | Entries | Count |
|---|---|---:|
| Level1 | Part1–Part4 | 4 |
| Level2 | Part1–Part3 | 3 |
| Level3 | Part1–Part4 | 4 |
| Level4 | Part1–Part4 | 4 |
| Level5 | Part1–Part3 | 3 |
| Level6 | Part1–Part5, EndScene | 6 |
| **Total** | | **24** |

### 16-symbol alphabet

`BDFGHIKPRSTVWXYZ` (16 symbols, file `0x462EE8`). Rendered by the message widget at `0x08036018` as a 16-cell grid. No front-end screen exposes this grid; the only text-entry screen in the front end is the Tunnel Flight name entry (A–Z / 0–9 / `_`). No validator or code table for this alphabet was found in the front end (see §8).

## 6b. Enumeration

**Space definition.** The hidden menu is a finite selector, not a text code: 6 levels × the part list of that level = **24 representable entries** (4+3+4+4+3+6). There is no checksum and no input alphabet; the "code" is the ordered pair (level, part). The level list ends at `Level6`; each part list ends at its own last label (Part4, Part3 or EndScene).

**Novel / unpublished entries executed.** TCRF's page only shows the Level list and a `Part1…Part4` page. The following entries do not appear in any published list and were generated and entered in the emulator:

| Selection | Effect (observed) | Evidence |
|---|---|---|
| Level 5 → Part 3 | loads the late-game ice/rock area with the green Toa | screenshot `enum_5_3c.png` |
| Level 6 → Part 5 | loads the sealed-door chamber; walking up triggers the six-Toa dialogue scene ("A POWER … MOVEMENT. SOMETHING IS IN THERE, I'M SURE OF IT.") | `enum_6_5c.png`, `door1c.png`–`door3c.png` |
| Level 6 → EndScene | loads the ending tableau with all six Toa Metru, then the ending text | `enum_6_6c.png` |

**All 24 entries were selected**; every one produced a playable area or cutscene. The screenshot set `enum_<level>_<part>c.png` also includes the out-of-range `Down` presses, which clamp to the last entry of the list.

**Bounds proven by rejection (in-game clamp).**

* Enter `Level1` → `A` → part list. Pressing `Down` moves `Part1 → Part2 → Part3 → Part4`; a fifth `Down` leaves `Part4` highlighted (no Part5, no wrap). Screenshot `b_L2_*.png` shows the same clamp on `Level2` (three entries, repeated `Down` stays on `Part3`).
* Level list: `Down` stops on `Level6`; there is no `Level7`. Screenshot `lv6c.png` / `b_L6_*.png`.
* `Level6` part list: `Down` stops on `EndScene`; a further `Down` leaves `EndScene` highlighted. Screenshot `bounds.png`.

**Attempts to reach it in-game (negative, bounded).**

* 81,090 `strings -t x -n 4` lines were scanned: `password` 0 hits, `secret` 0, `level select` 0, `sound test` 0, `cheat` 1 (dialogue "…you cheated me of…"), `debug` 3 (the `DEBUG SELECT` / `DEBUG Battles ON` / `OFF` block), `unlock` 1 (a link error, "Handle already unlocked").
* No key-mask cheat table was identified. A full-ROM scan for u16 runs of the GBA key masks (`1,2,4,8,0x10,…,0x200`) returned 836 raw candidates, dominated by small numeric data; none could be paired with a comparison loop that produces a cheat action. A literal search for the 2003 *Bionicle* sequence (`L,L,R,L,Select,Start,A`) as u16, u32, byte-index form and active-low form returned **zero** hits.
* The six reconstructed/published button sequences were pressed at the main menu (the only free-cursor screen where such a code would normally live); all were rejected (table in §3).
* Screen-id sweep `0..31` plus the normally reached `32..36`, and page inspection: the five screen-13 writers located in the front-end code (`0x08000000–0x08003000`) supply page `25`, `27`, `29` or `30`, and normal navigation also reaches page `31` (Options). **No located writer supplies page 0**, therefore the fallback (developer) page is unreachable through the menu flow that was enumerated.

## 7. Validation evidence

**Observed (emulator screenshots / debugger reads)**

* Main menu id `10`, page `0`; Options id `13`, page `31`; credits-end "Thank you" id `13`, page `25`.
* Forcing id `13` with page `0` displays `Level1…Level6`; the first `A` opens `Part1…Part4`; `Down` moves the highlight; `A` loads the selected area; `B` returns.
* Level/part counts from the actual lists: 4, 3, 4, 4, 3, 6.
* Level6 Part5 loads the sealed door chamber and the six-Toa dialogue; Level6 EndScene loads the ending tableau.
* All 24 entries produced playable content; list ends clamp without wrap.
* Six button sequences and the 2003 *Bionicle* sequence produce no debug screen.

**Derived (instruction sequences)**

* Screen/page/phase model (`0x020011D4`, `0x020011D8`, `0x020012D0`) and the five screen-13 writers located in the front end (`0x0800174C`, `0x080028B4`, `0x0800294E`, `0x08002A00`, `0x08002A72`) — none writes page 0.
* Page tables at `0x08038308` (10 entries) and `0x0803902C` (5 entries) confirm the page range `25..34` and the five-part selection.
* The literal-pool word at `0x08000960` is `0x0008AC00`, not `0x080000AC`; the dead "BILE" comparison therefore reads unrelated bytes and cannot succeed.
* The alphabet grid is built from `0x08462EE8` by the loop at `0x08036018`.

**Inferred**

* The `DEBUG Battles ON/OFF` strings belong to the same developer text block as `DEBUG SELECT` but no reachable page renders them; they are most likely a removed developer toggle (no code path was found that displays them).
* The 16-symbol alphabet is a rune/door-code alphabet used by an in-game message widget; the widget was not exercised inside a live door, so this is labelled inferred.

## 8. Unknowns

* The door-code gameplay UI (16-symbol alphabet) was not opened at a live door; therefore its code length, per-door table and validator remain unproven. Nothing in the front end or in the string/table scans ties it to a cheat or password system.
* `DEBUG SELECT` and `DEBUG Battles ON/OFF` are never displayed by the fallback page that was reached; whether a separate developer page (with the battle-rate toggle) still exists as dead data was not proven either way.
* Exact map ids for each of the 24 warp entries are not tabulated: the engine does not keep the level id in `0x020011D4` after a part load (it stays `13` for most parts), and the cutscene/map id changes with timing. The screenshots are the definitive evidence of the effect.

## 9. Tooling

* `binutils-arm-none-eabi` (`arm-none-eabi-objdump -M force-thumb`) for raw Thumb disassembly.
* Capstone 5.0.7 for pointer/literal scans; Python 3 `struct`/`zlib`.
* mGBA 0.10.5 SDL under `Xvfb :185` + `openbox`; `xdotool` for input, `scrot`/ImageMagick for screenshots.
* mGBA's built-in command-line debugger (`mgba -d`) was the key tool: `w/1`, `r/1`, `frame`, `save 1`, `load 1`, `watch/w`, `watch/r`. It allowed exact screen-id/page reads and savestate anchoring of the debug menu.
* Analysis artifacts (not shipped with the ROM): `/tmp/opencode/mazeofshadows/` contains the scanner (`scan.py`, `findset.py`), the debugger controller (`ctl.py`), the disassembly dumps (`core.txt`, `dis_036000.txt`, `dis_debug.txt`), and the screenshots referenced above (`cmp13c.png`, `plists.png`, `bounds.png`, `enum_*c.png`, `walk_*c.png`, `u03c.png`, `t01c.png`, `c9_0c.png`).

## Legal note

No ROM, graphics, audio or text from the game is redistributed with this report. Hashes, addresses, algorithms and the analyst's own generated menu selections are published; screenshots, where referenced, are emulator captures kept as analysis artifacts.
