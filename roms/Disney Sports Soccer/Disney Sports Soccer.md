# Disney Sports Soccer (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney Sports Soccer/Disney Sports Soccer.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| Header title | `DS_SOCCER_U` |
| Game code | `A6DE` (internal/debug string `GDKE`) |
| Maker code | `A4` (Konami) |
| Software version | 0x00 (Rev.00) |
| Fixed byte 0xB2 | 0x96 |
| Complement check 0xBD | 0x73 — **valid** (computed 0x73) |
| Header checksum 0xBE–0xBF | `0000` (the standard GBA value for this header; 0xBD is the real integrity byte) |
| Entry word 0x00 | `0xEA00002E` — stock branch to 0x080000C0, no cracktro |
| Nintendo logo | exactly one copy (file 0x04); no second GBA header in the image |
| MD5 | `496e1d4c049692f0ace43ec3eefc708e` |
| SHA-1 | `637e62e9173daa1e8a022c60a995070079c6fe32` |
| SHA-256 | `cb7ee4c90be3dd79d09721d3ef08459e14d6be33ab4d196a67119d8b62fa6fb1` |
| Save hardware | 512-byte EEPROM (`EEPROM_V122` at file 0x11a870; mGBA created a 512-byte `.sav`) |

No trainer/scene markers (`SUNHORS`, `CRC BANDIT`, `MODE7`, `CRACK`, `TRAINER`,
`PARADOX`, `EURASIA`, `INDEPENDENT`, `PDX`) occur anywhere in the image. The first
4 KiB is ordinary crt0 code and literal pools. This is the retail USA image.

The European release of the same game is *Disney Sports: Football*; the US
*Disney Sports: Football* is a different (American-football) game. All statements
below apply only to the hashed USA `DS_SOCCER_U` / `A6DE` image above.

## 2. Executive summary

**This ROM has no password system, no button cheat code, and no player-reachable
debug menu.** There is no user text-entry field anywhere in the game: every menu
is a list/ring selector. A whole-image search
finds **zero** occurrences of `password`, `passwd`, `passcode`, `cheat`, `secret`,
`unlock` or `hidden` in ASCII, swapped-case ASCII, UTF-16LE and UTF-16BE.

What the ROM does contain:

1. **A complete, unused KCEK development subsystem.** Strings at file
   `0xF29F0`–`0xF3B20` include `GDKE`, `AGB SYSTEM   Ver%s`, `3.00`, `BY KCEK`,
   `L+R+START       SOFT RESET`, `L+R+SELECT   MEM+DMA DEBUG`, `PAGE NO.%d`,
   `SAMPLE MENU`, the sample-page names (`EXE SAMPLE`, `OBJ_SAMPLE`, `ANI_SAMPLE`,
   `ANI3D_SAMPLE`, `CART_SAMPLE`, `EXJOY_SAMPLE`, `SIO_SAMPLE`, `JOYBUS_SAMPLE`,
   `SAVE_LOAD_SAMPLE`, `STAFF_ROLL`), the stage list `STAGE0`–`STAGE5`, the six team
   labels `MICKEY/MINNIE/DONALD/DAISY/GOOFY/PETE`, minigame labels
   (`DRIBBLE/PASS/SHOOT/CORNER/FREE_KICK/PENALTYKICK`), difficulty names and a
   live debug-print label table (`TEAM0:`, `TEAM1:`, `STAGE:`, `BALL TEAM:`,
   `LEFT SIDE:`, `CPU LEVEL:`, `SPECIAL0/1:`, `TRAP:`, `JUDGE:`, `CONTROL:`).
   The debug root page list (9 entries: `LOGO`, `TITLE`, `SELECT`, `GAME`,
   `GSELECT`, `SAMPLE`, `MINIGAME`, `TRAINING`, `PENALTYKICK`) is at ROM
   `0x08B2691C`; it is only referenced by the dev-menu renderer at `0x0800B6F4`.
   TCRF documents this menu and a "secret kart racing mode" (the `CART_SAMPLE`
   page with a Goemon sprite). It is developer content, not a player cheat.
2. **The documented `L+R+START` / `L+R+SELECT` combos do nothing.** Both were
   tried simultaneously at boot, on the title, on the PLAYMODE menu and in a
   match. `Start` alone opens PLAYMODE (from the title) or the pause menu (in a
   match); the L+R prefix changes nothing and no reset occurs. `L+R+SELECT`
   produces no screen and no RAM change in any of those states.
3. **TCRF's RAM gate does not reproduce.** TCRF says `02000430:02` enables the
   debug menu. In this image `0x02000430` is the low byte of a 0x44-byte-stride
   scene/object array based at `0x02000400` (initialised at `0x08001D08`), and it
   behaves as the **current scene id**, not an input flag: 1 at boot, 3 on the
   title/menu, 4 in PLAYMODE/stadium select, 7 in the attract demo, 14 in the
   in-game demo. Patching it to 2 at boot, on the title, and in PLAYMODE is
   overwritten by the game and opens no menu (three states tested). The sibling
   claim `0x02000270` is a gate is also false here: it is `0x00` at boot, title,
   PLAYMODE and match setup, and the 4-byte literal `0x02000270` occurs **0**
   times in the image.
4. **The published "GBA" code is the GameCube code.** Search results for
   GameFAQs' GBA cheats page and a Japanese cheat blog both return
   *Y, Y, Y, Y, Y, B, A, Y* for unlimited magic (the archived 2021 GBA cheats
   page itself has no cheats). The GBA has no Y button; the sequence is the
   GameCube pad code (the GameCube release has the same "unlimited magic"
   cheat). VGChartz lists 0 cheats for the GBA SKU. The literal `YYYYYBAY`
   occurs 0 times in the ROM. GBA-feasible re-mappings
   (`Select×5,B,A,Select` and `L×5,B,A,L`) were pressed on the title: no
   transition and no confirmation screen.
5. **Unlockables are save-progress flags, not codes.** On an empty save:
   Challenge Cup offers only LEVEL 1 (Right/Down cannot advance it); the item
   grid shows 32 cells over 2 pages but only items 01 `PHOENIX` and 20
   `THUNDER STORM` responded to input; Dream Cup brackets six teams with byes;
   the six-team and six-stadium rings wrap at six. The Japanese wiki's
   "All-Star Pete Team" unlock is a GameCube roster entry; the GBA team ring has
   no seventh team.

The negative is bounded, not assumed: §6b lists the menu surface walked, the
text/button search spaces with counts, every published claim tested, and the
in-game rejections that bound the spaces.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (`mgba -3`), Xvfb `:316`, openbox, `SDL_AUDIODRIVER=dummy`.

```
Xvfb :316 -screen 0 1024x768x24 &
DISPLAY=:316 openbox &
DISPLAY=:316 SDL_AUDIODRIVER=dummy mgba -3 "Disney Sports Soccer.gba" &
```

Keys (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad arrows. Hold 60–150 ms; menus debounce and ignore
presses during fades, so wait 1–3 s after each transition.

Menu paths used (all observed):

| Screen | Path |
|---|---|
| Title | boot → attract → `PRESS START` |
| PLAYMODE | title → Start. `SINGLEPLAY / MULTIPLAY / ITEM / STATUS / OPTION` |
| GAMEMODE | PLAYMODE → SINGLEPLAY. `EXHIBITION / DREAM CUP / CHALLENGE CUP / MINI GAME / TRAINING / SPECTATOR MODE` |
| Exhibition | GAMEMODE → EXHIBITION → TEAM SELECT (home) → TEAM SELECT (away) → ITEM SELECT (home) → ITEM SELECT (away) → STADIUM SELECT → matchup card → DSN intro → kickoff |
| Dream Cup | GAMEMODE → DREAM CUP → NEW GAME → TEAM SELECT → ITEM SELECT → LEVEL SETTING (1/2/3 stars) → six-team bracket |
| Challenge Cup | GAMEMODE → CHALLENGE CUP → TEAM SELECT → ITEM SELECT → `Select a level.` (LEVEL 1 only on empty save) |
| Mini Game | GAMEMODE → MINI GAME. `GOAL SHOT / DRIBBLE / PASS / FREE KICK / CORNER KICK / PENALTY KICK` |
| Training / Spectator | GAMEMODE → TRAINING or SPECTATOR MODE → team/item/stadium flow |
| Multiplay | PLAYMODE → MULTIPLAY → "Checking number of linked GBA units…" (link-gated) |
| Item | PLAYMODE → ITEM → "View items received." → 2 pages × 16 cells |
| Status | PLAYMODE → STATUS → `MINI GAME SCORE` / `PLAY DATA` |
| Option | PLAYMODE → OPTION. BGM, Time Display, Trap, Extra Time, PK, Foul, Referee, Save&Exit, Reset Game Data |
| Pause | in match → Start. `CONTINUE / RETRY / EXIT` |

RAM reads without a debugger: save an mGBA state (`Shift+F1..F9`). The `.ssN`
file is a PNG; the `gbAs` chunk is zlib data and the raw state is 397,312 bytes,
with EWRAM at raw offset `0x21000` (verified: EWRAM `0x02000430` is raw
`0x21430`). `state_edit.py` (§9) rewrites one byte and rebuilds the PNG/chunk
CRCs; `F1..F9` reloads it. All RAM-write experiments below are savestate patching
used as debugger evidence, not offered as cheats.

## 4. Address map

ROM address = `0x08000000 + file offset`.

| Address | Contents |
|---|---|
| `0x000000`–`0x0000FF` | GBA header, stock ARM branch, valid complement, one logo |
| `0x000CD0`–`0x000D28` | key reader: `ldrh` from `0x04000130`, computes held/new-press/release |
| `0x0000D08` | key-state base literal (`0x02003070`), offsets `0x397C/0x397E/0x3980/0x3984/0x39A4` |
| `0x0001D08` | init of the 0x44-byte-stride object/scene array at `0x02000400` (count in `0x02006D10`, end pointer in `0x02006DDC`) |
| `0x0001E14` | clear loop for the word table at `0x02006D20` |
| `0x0001E60` / `0x0001EE4` / `0x0001F78` | object create/insert/delete routines (0x44-byte records; +0x18 function, +0x1C parent, +0x20 next, +0x24 child) |
| `0x00029CC` / `0x00028F0` | root task tick / task teardown |
| `0x000A131`–`0x000A551` | 7 debug page handlers (pointed to by `0x08B26900`) |
| `0x000B4C4` | debug text printer (tile string → screen) |
| `0x000B520` | debug page object constructor (writes page table `0x08B26AC8`) |
| `0x000B6F4` | debug root renderer: `AGB SYSTEM Ver3.00 BY KCEK`, `L+R+START`, `L+R+SELECT`, then builds the 9-entry page list (size `0x24` at `0x0800B756`) |
| `0x000C374` | debug overlay renderer for the live print table at `0x000F2DA4` |
| `0x000C4F0` / `0x000C550` | debug list builder / menu-object setup |
| `0x00F29F0` | `GDKE`, `PENALTYKICK`, `TRAINING`, `MINIGAME`, `SAMPLE`, `GSELECT`, `GAME`, `SELECT`, `TITLE`, `LOGO`, `STAFF_ROLL` |
| `0x00F2A4C` | sample page labels (`SAVE_LOAD_SAMPLE`, `JOYBUS_SAMPLE`, `SIO_SAMPLE`, `EXJOY_SAMPLE`, `CART_SAMPLE`, `ANI3D_SAMPLE`, `ANI_SAMPLE`, `OBJ_SAMPLE`, `EXE SAMPLE`) |
| `0x00F2AD8` | minigame/technique labels `DRIBBLE`, `PASS`, `SHOOT`, `CORNER`, `FREE_KICK`; `STAGE5`–`STAGE0`; six team labels; difficulty labels |
| `0x00F2DA4` | live debug print records, 0x14 bytes each: `{char* label, u32 width, u32 ram_addr, u32 format, u32 name_array}` — e.g. `TEAM0:`→`0x020095F8`, `STAGE:`→`0x020095FC`, `CPU LEVEL:`→`0x0200960B`, `JUDGE:`→`0x0200770D` |
| `0x00F307C` | `AGB SYSTEM   Ver%s`, `3.00`, `BY KCEK`, `L+R+START       SOFT RESET`, `L+R+SELECT   MEM+DMA DEBUG`, `PAGE NO.%d` |
| `0x00F3550` | `SAMPLE MENU`, `0. ITEM0`–`4. ITEM4`, `PUSHING %d FRAME`, `PUSH START TO FADE OUT`, `PUSH SELECT TO FADE IN` |
| `0x00F3AF0` | `EEPROM SAVE`, `  SRAM SAVE`, `SAVE LOAD ERROR`, `SAVE START_BUTTON`, `LOAD SELECT_BUTTON`, `FORMAT L_BUTTON` |
| `0x08B26900` | 7 debug page handler pointers (Thumb) |
| `0x08B2691C` | 9 debug root page label pointers (the list built by `0x0800B6F4`) |
| `0x08B26AC8` | debug page descriptor table, 3 words × 10 rows (constructor/destructor/draw) |
| `0x08B26608` | pointer to the debug page constructor `0x0800B521` inside a larger screen-handler pointer table |
| `0x02000400` | base of the 0x44-byte object/scene array (0x80 slots) |
| `0x02000430` | scene/mode id byte (TCRF's "debug" address) — 1 boot, 3 title/menu, 4 PLAYMODE/stadium, 7 attract, 14 demo |
| `0x02000270` | all-zero; no literal reference; not a gate |
| `0x02003070` | input/state base; `+0x397C` new press, `+0x397E` previous held, `+0x3980` release, `+0x3984`/`+0x39A4` copies used by game code |
| `0x020095E8`–`0x02009621` | debug print fields (team ids, stage, ball team, side, CPU level, specials, trap, judge, control, levels) |

## 5. Algorithm

### 5.1 No validator exists

There is no function that reads a user text buffer and compares it with a code:
no `PASSWORD`/`CODE` prompt exists in any encoding, and the only keyboard-like
table in the image is the font's ASCII→tile map (`0x11A6C0`, `0x11A750`), used for
drawing all UI text. No screen in §6b accepts typed characters. The negative is a
property of the *absence of an input surface*, not of a missed comparison.

### 5.2 Scene id and the TCRF address

`0x08001D08` initialises an array at `0x02000400` of `0x80` records, stride
`0x44` (`base + n*0x44`, end pointer at `0x02006DDC`). `0x02000430` is record 0,
offset `+0x30`. In every savestate examined the value tracks the current screen:

| State | `0x02000430` |
|---|---|
| 1.2 s after boot (logo/intro) | `0x01` |
| title / menu | `0x03` |
| PLAYMODE and stadium select | `0x04` |
| attract "Demo" match | `0x07` |
| in-game demo variant | `0x0E` |

Writing `0x02` there (savestate patch, verified read-back) does not change the
screen at boot, on the title, or in PLAYMODE; the scene manager rewrites the byte
at the next transition. Therefore it is an **output** (current scene), not the
input gate TCRF's memory code assumes, and it cannot open the debug menu in this
build. `0x02000270` is zero in all of those states and the literal is absent.

### 5.3 Developer menu (present, unreachable)

The root renderer `0x0800B6F4` prints the AGB SYSTEM banner and then builds a
9-entry list from the pointer array at `0x08B2691C`. The page descriptor table at
`0x08B26AC8` supplies ten 3-word rows (constructor / destructor / draw). The
constructor is `0x0800B520`; its page object is what the root list would
instantiate. No BL or literal reference reaches `0x0800B6F4` or `0x0800C374` from
the retail screens: the only references to the menu tables are inside the dev
subsystem itself (`0x08B26608` → `0x0800B521`, `0x08B2691C` → literal at
`0x0800B7CC`). The subsystem is linked but has no entry from any player-reachable
scene in this image.

### 5.4 Input path

The frame loop's key reader (`0x0800CD0`) computes active-high `new_press`,
`held` and `release` from `0x04000130` and stores them at `0x020069EC`,
`0x020069EE`, `0x020069F0` (plus copies at `0x020069F4` and `0x02006A14`).
Game code reads the copy at base `0x02003070 + 0x39A4` and tests individual bits
(e.g. `ands #0x40` = Up, `ands #0x08` = Start in the stadium/menu code). No
sequence matcher, history ring or per-press counter was found (see §6b.1).

## 6. Tables

### 6.1 Screens and option domains (observed)

| Set | Entries |
|---|---|
| PLAYMODE | SINGLEPLAY, MULTIPLAY, ITEM, STATUS, OPTION (5) |
| GAMEMODE | EXHIBITION, DREAM CUP, CHALLENGE CUP, MINI GAME, TRAINING, SPECTATOR MODE (6) |
| Teams (ring wraps at 6) | SUPER STARS, CHARMERS, SEADUCKS, BELLES, SPACENUTS, STEAMROLLERS |
| Stadiums (ring wraps at 6) | Metro Garden, Great Sun Stadium, Lotus Field, Eagle Summit, Azul Centennial, Stade du Chateau |
| Stadium LEVEL | 1–4 stars (default 2) |
| Stadium TIME | 1, 3, 5, 7, 10 min |
| Dream Cup level | LEVEL1 SINGLE STAR, LEVEL2 DOUBLE STAR, LEVEL3 TRIPLE STAR |
| Dream Cup bracket | 6 teams, two byes (SEADUCKS vs STEAMROLLERS, SPACE NUTS vs CHARMERS, BELLES vs SUPER STARS) |
| Challenge Cup level | LEVEL 1 only on empty save; Right/Down rejected |
| Mini Game | GOAL SHOT, DRIBBLE, PASS, FREE KICK, CORNER KICK, PENALTY KICK (6) |
| Item grid | PAGE 1: 01–16, PAGE 2: 17–32; on an empty save only 01 PHOENIX (Hot Shot Lv.1) and 20 THUNDER STORM (Lightning Fury Lv.1) responded to input; the other 30 cells never became selectable under Up/Down/Left/Right on either page |
| Options | BGM, Time Display, Trap, Extra Time, PK, Foul, Referee (7 toggles) + Save&Exit, Reset Game Data |
| Pause | CONTINUE, RETRY, EXIT (3) |
| Status | MINI GAME SCORE (6 events), PLAY DATA (PLAY TIME, TOTAL SCORE, WINNING PERCENTAGE, CONSECUTIVE VICTORY, NEXT) |

Ranking defaults (GOAL SHOT) are **OSA 5000 / 4000 / 3000 / 2000 / 1000** for
1st–5th — a developer placeholder (`OSA` = Osaka), like the `KONAMI` defaults in
*Disney Sports Basketball*. No published list mentions this.

### 6.2 Debug menu structure (static; developer content)

Root labels (`0x08B2691C`, 9): `LOGO`, `TITLE`, `SELECT`, `GAME`, `GSELECT`,
`SAMPLE`, `MINIGAME`, `TRAINING`, `PENALTYKICK`.

Sample pages (`0x08B26940` onward): `EXE SAMPLE`, `OBJ_SAMPLE`, `ANI_SAMPLE`,
`ANI3D_SAMPLE`, `CART_SAMPLE`, `EXJOY_SAMPLE`, `SIO_SAMPLE`, `JOYBUS_SAMPLE`,
`SAVE_LOAD_SAMPLE`, then `STAFF_ROLL`. TCRF's descriptions (from its own
research, not re-verified here because the menu is unreachable) are: sprite-limit
demo, Donald object test, animation tests, 3D Pluto/basketball demo, a Goemon-kart
physics sandbox ("secret kart racing mode"), external-joypad and SIO/Joybus tests,
and an EEPROM save test.

Handler pointers (`0x08B26900`, 7): `0x0800A131`, `0x0800A17D`, `0x0800A209`,
`0x0800A30D`, `0x0800A3D9`, `0x0800A4C5`, `0x0800A551`. The exact label→handler
mapping was not proven (the list is built by pointer and the menu is not
reachable); the addresses are recorded for a future revision comparison.

Page descriptor table (`0x08B26AC8`, 10 rows × 3 words) begins with
`0x08002389, 0x080022CD, 0x0800B569` then `0x0800B68D, 0x0800C4ED,
0x0800B705`, alternating row terminators `0x0800232D`.

Debug print table (`0x08B26998` name arrays, records at `0x00F2DA4`):

| Label | RAM | Name array |
|---|---|---|
| `TEAM0:` | `0x020095F8` | `0x08B26998` (MICKEY…PETE) |
| `TEAM1:` | `0x020095FA` | `0x08B26998` |
| `STAGE:` | `0x020095FC` | `0x08B2697C` (STAGE0–5) |
| `BALL TEAM:` | `0x020095FE` | `0x08B269C0` (TEAM0/1) |
| `LEFT SIDE:` | `0x02009600` | `0x08B269C0` |
| `CPU LEVEL:` | `0x0200960B` | `0x08B269CC` (EASY/NORMAL/HARD) |
| `SPECIAL0/1:` | `0x02009614/16` | `0x08B26A14` (NOTHING…WIPE) |
| `TRAP:` | `0x020095E8` | `0x08B26A84` (MANUAL/AUTO) |
| `JUDGE:` | `0x0200770D` | `0x08B26A90` (NO FOUL/LOOSE/STRICT) |
| `CONTROL:` | `0x02009604` | `0x08B26AA0` (CPU ONLY/PLAYABLE) |
| `TYPE:` | `0x02009621` | `0x08B26A60` (FOUL2PK/EXTEND) |
| `CTRL:` | `0x0200961F` | `0x08B26A70` (1P VS CPU … 1P VS 2P) |
| `G LEVEL:` | `0x0200960B` | `0x08B269CC` |
| `M LEVEL:` | `0x02009620` | `0x08B26AAC` (LEVEL1–5) |

## 6b. Enumeration

### 6b.1 Space definition

**There is no code space: 0 alphabets, 0 lengths, 0 checksums, 0 validators.**
The engagement therefore enumerates the menu/debug surface and states every
search space that was checked, so the absence is a proven statement about those
spaces.

| Space | Size | Result |
|---|---|---|
| Typed-character screens | 0 | no password/name/code entry anywhere in the walk |
| Whole-image strings (`strings -n 4`) | 163,120 lines | 0 `password/passwd/passcode/cheat/code/secret/unlock/hidden` (ASCII, swap-case, UTF-16LE/BE); 1 `DEBUG` (the AGB SYSTEM banner) |
| `strings -n 4` keyword hits | 1 (`L+R+SELECT   MEM+DMA DEBUG`) | dev banner only; no validator, table or alphabet |
| Text-entry key tables | font map only (`0x11A6C0`, `0x11A750`) | used by the global text renderer, not by an input field |
| Button-mask runs, u16, ≥4 consecutive | 523 runs | inspected by class; all are code/data noise or single-bit padding, not press tables |
| Button-mask runs, u8, ≥4 consecutive | 7,152 runs | ditto (instruction bytes dominate) |
| Same-mask runs, u16, ≥4 repeats | 499 runs | no `[X,X,X,X,X, B, A, X]` sequence; closest is a 5×`0x0001` animation-curve table at `0x0E9B8A`, not a matcher |
| Published GBA codes | 1 claim (GameFAQs/Japanese blog `YYYYYBAY`) | GameCube pad code; literal absent; GBA has no Y |
| Published GBA code databases | GameFAQs (0 real GBA cheats), VGChartz (0), TCRF (debug/RAM only) | nothing else to test |
| Menus/screens walked | 28 distinct screens/submenus | listed in §3 |
| Hidden/debug menu | 9 root pages + 9 sample pages + option domains | enumerated in §6.2; no player entry |
| TCRF RAM gate | 2 addresses | `0x02000430` inert/overwritten; `0x02000270` zero and unreferenced |

### 6b.2 Novel/unpublished results

No code can be minted because no validator exists. The novel, publishable
results of this pass are:

1. **The TCRF gate is not a gate in USA Rev.00.** `0x02000430` is a scene id
   (1/3/4/7/14 observed) written by the scene manager; a patched `2` is
   overwritten and opens no screen at boot, title, PLAYMODE or attract demo.
   This corrects a widely repeated memory-code claim.
2. **`0x02000270` is not a Soccer gate either.** It is zero at boot, title,
   PLAYMODE and match setup, and the literal occurs zero times.
3. **The debug menu's complete page list is in the ROM** (`0x08B2691C`,
   `0x08B26AC8`), including the `CART_SAMPLE` "secret kart" page, the EEPROM/SIO
   sample set and the stage/team/difficulty tables — all linked but with no
   reachable entry.
4. **The published "GBA" unlimited-magic code is the GameCube code.**
   `Y,Y,Y,Y,Y,B,A,Y` cannot be entered on a GBA; the GBA re-mappings tried
   produced no confirmation.
5. **The shipped GOAL SHOT ranking defaults are `OSA` 5000–1000**, developer
   placeholders not in any published list.
6. **The GBA roster is exactly six teams**; the "All-Star Pete Team" unlock in
   Japanese cheat pages belongs to the GameCube roster. The GBA team ring wraps
   at six, with no seventh entry.

### 6b.3 Published codes/claims tested

| Claim | Source | Test | Result |
|---|---|---|---|
| `Y×5, B, A, Y` = unlimited magic | GameFAQs GBA cheats page; Japanese blog | literal search; GBA has no Y; pressed `Select×5,B,A,Select` and `L×5,B,A,L` on the title | **rejected**: the sequence is the GameCube pad code and cannot be typed on a GBA; re-mapped sequences produced no transition |
| GBA has 4 cheat codes | GameFAQs page count on some mirrors | page content | the four codes belong to the GameCube entry; the archived 2021 GBA cheats page has none |
| GBA cheats: 0 | VGChartz GBA cheats page | page content | confirmed (0) |
| `02000430:02` enables debug menu | TCRF | savestate patch at boot, title, PLAYMODE, demo; read-back | **inert**; byte is a scene id and is rewritten |
| `02000270:07` type gate | sibling Basketball report / TCRF lineage | savestate read at four states; literal scan | **zero/unreferenced**; not a gate here |
| `L+R+START` soft reset | in-ROM string `0x0F30A0` | simultaneous hold at boot, title, PLAYMODE and in match | behaves exactly like `Start` alone (PLAYMODE / pause menu); **no soft reset** |
| `L+R+SELECT` MEM+DMA debug | in-ROM string `0x0F30BC` | simultaneous hold at boot/title/PLAYMODE/in match | **inert** (no screen, no RAM change) |
| All-Star Pete Team unlock | Japanese cheat wiki | team ring observed | **GameCube-only**; GBA ring has 6 and wraps |
| Hidden teams/Imperials/Wolfgangs | Japanese wiki | team ring and debug labels | GC-only teams; GBA has six (MICKEY…PETE) |
| Unlock items by Challenge Cup | in-game text "Defeat other teams to win items!" | item grid on empty save | consistent: only 2 of 32 cells responded to input |

### 6b.4 Bounds proven by rejection

* **Wrong published code**: the literal `YYYYYBAY` is absent (count 0); the GBA
  has no Y, so the published sequence is unreachable by construction. GBA
  re-mappings on the title produced no screen change or transition.
* **TCRF gate**: `0x02000430 = 2` at boot, title and PLAYMODE produced no menu;
  the value was observed reverting to the scene id. `0x02000270` is zero.
* **Challenge Cup**: Right and Down on `LEVEL 1` do not advance it on an empty
  save (rejection of levels >1 until the save advances).
* **Item grid**: on an empty save only 01 and 20 responded; Up/Down cycled those
  two, and Up/Down/Left/Right on both pages never reached cells 02–19 or 21–32.
  This bounds the owned-item set.
* **Team/stadium rings**: six Right presses return to the starting entry
  (SUPER STARS → … → STEAMROLLERS → SUPER STARS; Stade du Chateau → Metro
  Garden); no seventh entry exists.
* **Options**: no hidden rows; the OPTION list is the seven toggles plus
  Save&Exit and Reset Game Data.
* **Debug banner combos**: `L+R+START` and `L+R+SELECT` held simultaneously in
  four states produced no debug surface and no DMA/memory view.

## 7. Validation evidence

**Observed (emulator, screenshots and savestate RAM reads):**

* Title, PLAYMODE (5), GAMEMODE (6), both TEAM SELECT screens (6-team ring,
  wraps), both ITEM SELECT screens (32 cells, 2 pages), STADIUM SELECT
  (6-stadium ring; LEVEL 1–4; TIME 1/3/5/7/10), Dream Cup NEW/LOAD, team, item,
  LEVEL SETTING (3), six-team bracket, Challenge Cup team/item/LEVEL 1,
  MINI GAME (6), TRAINING, SPECTATOR MODE, MULTIPLAY link check, ITEM viewer
  (2 pages), STATUS, MINI GAME SCORE (6), GOAL SHOT ranking `OSA 5000…1000`,
  PLAY DATA (4 counters), OPTION (7 toggles + 2 commands), pause
  (`CONTINUE/RETRY/EXIT`), and a played Exhibition kickoff (SUPER STARS vs
  CHARMERS, Stade du Chateau).
* `0x02000430` read from savestates: 1 (boot), 3 (title/menu), 4
  (PLAYMODE/stadium), 7 (attract demo), 14 (demo variant). Patching it to 2 at
  three states produced no screen change and the game rewrote it.
* `0x02000270`, `0x02000274`, `0x02000278` read as `0x00` in five states.
* `L+R+SELECT` and `L+R+START` simultaneous holds: no effect at boot/title/
  PLAYMODE; in a match `L+R+SELECT` is inert and `L+R+START` only opens the
  normal pause menu (no reset).
* Title `Select×5,B,A,Select` and `L×5,B,A,L`: no screen change.
* Item select: Down from `01 PHOENIX` moved the cursor to page 2 `20 THUNDER
  STORM`; Up returned to 01; Left/Right did not change the cell; the remaining
  30 cells stayed grey.

**Derived (disassembly/tables):**

* Key reader and the three key-state words; `0x02003070` base and offsets.
* 0x44-byte object/scene array and the `0x02000430` field.
* Debug root label array, handler array, page descriptor table, sample labels,
  stage/team/difficulty tables and the live debug print table.
* No BL/pointer path from the retail screens to `0x0800B6F4` (debug root) or
  `0x0800C374` (overlay).

**Inferred:**

* TCRF's `02000430:02` was authored against a different revision/layout in
  which the same byte offset is a "next screen" input; in this USA build it is
  the current-scene output.
* The five/six debug handlers' label mapping (7 pointers for 9 labels) is not
  fully resolved because the menu cannot be entered from gameplay.

## 8. Unknowns

* Whether a JP/EU revision has a working `02000430:02` entry or a different
  scene-id layout; only USA Rev.00 was tested.
* Exact label→handler mapping inside the debug root (7 pointers, 9 labels).
* Visual effects of the debug sample pages were not exercised (unreachable);
  their names and TCRF's descriptions are the only evidence.
* Complete EEPROM save-record layout and the Challenge-Cup/item unlock bit
  positions were not decoded byte-for-byte; only the resulting selectable sets
  were observed.
* Whether the `NEXT` prompt on PLAY DATA has a second page in a progressed save
  (it did not advance on an empty save).

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* Python 3 for literal/pointer scans; `strings -t x`, `xxd`, `grep -abo`
* `state_edit.py` — read/patch mGBA `.ssN` PNG `gbAs` chunks (zlib) and rebuild
  chunk CRCs; EWRAM at raw `0x21000`
* `keys.py` — xdotool key/screenshot helper (60–150 ms holds, 0.3–3 s gaps)
* ImageMagick `import`/`convert`/`montage`; mGBA 0.10.5; Xvfb `:316`
* The ROM image was never modified.

## 10. Legal note

No ROM, graphics, music or extracted game text is redistributed. Only hashes,
addresses, table layouts and the analyst's own observations are recorded here.
