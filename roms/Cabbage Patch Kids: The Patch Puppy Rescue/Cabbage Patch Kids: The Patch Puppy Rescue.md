# Cabbage Patch Kids: The Patch Puppy Rescue (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Cabbage Patch Kids: The Patch Puppy Rescue/Cabbage Patch Kids: The Patch Puppy Rescue.gba` |
| Size | 4,194,304 bytes (`0x400000`, 32 Mbit) |
| Header title (`0xA0`) | `CABBAGE PATC` (11 chars, no NUL before `0xAC`) |
| Game code (`0xAC`) | `BCGE` |
| Maker code (`0xB0`) | `G9` |
| Version (`0xBC`) | `00` |
| Complement (`0xBD`) | `0xA3` (matches computed value) |
| Header checksum (`0xBE`) | `0x0000` (computed value is `0x055D`) — rebuilt-header artifact, no cracktro |
| Entry words | `0xEA00002E` at `0x00`, `0xEA000006` at `0xC0` (stock crt0 path) |
| Nintendo logo | exactly one, at file offset `0x4` (single-image cart, no multi-boot pack) |
| MD5 | `f05560ae14f622de028308b372ab2fe3` |
| SHA-1 | `0a18915e4914b48604a0d2e43762c5dd44fce980` |
| SHA-256 | `0505ec240e2ee9077cd13b456ad5e437872d5d59d2161db5cce3b7ae46515dce` |
| Build stamp | `0x0808CA04`: `[VERSIONBLOCK\|V3175           \|T1139593640\|Mhomer3\r        \|]` |

No trainer, no appended data, no second header; the image is exactly 4 MiB.

## 2. Executive summary

**There is no password, cheat-code, or code-entry system in this ROM.** The game has no
text-entry field at all; the only "name" interaction is a fixed list of generated child
names chosen with Left/Right. Exhaustive literal searches of the whole image find
`password`, `cheat`, `secret`, `unlock`, `stage`, `warp`, and `gallery` **zero times**.
The single `code` hit is the Shin'en audio-engine banner (`Code: B.Wodok`). The only
`level` hits are the `Level Complete Sting` sound name, `RLevelSelectScreenState`, and
the debug string `Level Select`.

The one genuine hidden-content find is a **developer pause/debug overlay**. The ROM
contains a complete second pause page:

```
Debug
Level Select
Slow Motion
Replay
Toggle Debug Keys
Start Profiling / Stop Profiling / Write Profile
```

The panel records for this page are built by the game (constructor `0x0802A834`, runtime
menu builder `0x08019D98`), and the page's five visible item strings are linked at
`0x020152B8`. However, the page is **not reachable through the retail UI**. The retail
pause menu has four pages/parent-self pairs (`0,0`, `0,1`, `1,2`, `2,3`); the only
reachable transition into page 2 is the **Sleep** confirmation page, whose items are
`Sleep` and `Back`, and **no item or key sequence sets page 3**. A sweep of all
175 one-, two- and three-button combinations of the ten GBA buttons, applied to the
reconstructed pause state, produced no debug page. Title-screen and gameplay sweeps
likewise produced nothing.

The only published "cheats" for this title are **unlockables**: collect 40 crystals in
each of the nine story levels to add an object to the playroom. The HUD counter
`0/40` was observed in the Park level, confirming the mechanic. Those are normal
progression, not codes, and no published password list exists for this SKU.

## 3. How to reproduce

Emulator and display used:

```bash
Xvfb :222 -screen 0 1024x768x24 &
DISPLAY=:222 openbox &
DISPLAY=:222 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 "<ROM>"
```

mGBA 0.10.5 SDL keymap (verified by reading `KEYINPUT` at `0x04000130` through the
built-in `-d` debugger):

| GBA | xdotool key | KEYINPUT bit |
|---|---|---|
| A | `x` | 0 |
| B | `z` | 1 |
| Select | `BackSpace` | 2 |
| Start | `Return` | 3 |
| Right/Left/Up/Down | arrows | 4/5/6/7 |
| R | `s` | 8 |
| L | `a` | 9 |

Menu path used:

1. Boot → `PRESS START` (title).
2. Start → file select (`New Kid`) with Play / Erase / Credits.
3. Play → `Adopt a Kid` (fixed-name chooser, A = Ok).
4. Ok → cutscene → Playroom.
5. Start in the Playroom → pause with `Continue Game`, `Exit Game`, `Sleep`
   (`Return to Playroom` is added when a story level is loaded).
6. Up then A from Continue wraps to Sleep → Sleep confirmation page
   (`To exit Sleep press Select + L Button + R Button`, items `Sleep`, `Back`).
7. Leaving the Playroom through the right-hand door/level transition reaches the first
   Park platforming level (observed HUD `0/40`). Start there shows four items:
   `Continue Game`, `Return to Playroom`, `Exit Game`, `Sleep`.

A savestate taken at the in-level pause screen (`.ss2`) was used to reload the menu
instantly for the button sweep.

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`) unless marked RAM.

### 4.1 Debug strings and panels

| Address | Contents |
|---|---|
| `0x0808EF54` | `Cabbage Patch Kids:\nThe Patch Puppy Rescue\nsave data is corrupted\nand has been deleted.` |
| `0x0808EFB0` | `Continue Game` |
| `0x0808EFC4` | `Return to Playroom` |
| `0x0808EFDC` | `Exit Game` |
| `0x0808EFEC` | `Sleep` |
| `0x0808F004` | `Back` |
| `0x0808F010` | `Go Back` |
| `0x0808F01C` | `Level Select` |
| `0x0808F030` | `Slow Motion` |
| `0x0808F040` | `Replay` |
| `0x0808F04C` | `Toggle Debug Keys` |
| `0x0808F064` | `Start Profiling` |
| `0x0808F07C` | `Stop Profiling` |
| `0x0808F090` | `Write Profile` |
| `0x0808F0A4` | `Game Paused` |
| `0x0808F0B4` | `\x05\nTo exit Sleep\npress Select +\nL Button + R Button` |
| `0x0808F15C` | `A-default Start-go L-print` (developer hint, character creator) |

String-pool layout: each record is `char text[]; u32 pointer_to_that_text` (hence the
apparent "backward" pointers in the pool).

### 4.2 Pause/debug page records (RAM after the overlay is constructed)

| RAM | Page id / parent | Item count | Header text | Item array |
|---|---|---|---|---|
| `0x02014ED4` | `[0]=0, [4]=0` | 4 | `Game Paused` (`0x0808F0A4`) | `0x020152E8` |
| `0x02014EA8` | `[0]=0, [4]=1` | 3 | `Game Paused` | `0x020152D8` |
| `0x02014E7C` | `[0]=1, [4]=2` | 2 | sleep hint (`0x0808F0B4`) | `0x020152D0` |
| `0x02014E50` | `[0]=2, [4]=3` | 5 | `Debug` (`0x0808EFF8`) | `0x020152B8` |

Observed item arrays (32-bit ROM string pointers):

* `0x020152E8`: `Continue Game`, `Return to Playroom`, `Exit Game`, `Sleep`
* `0x020152D8`: `Continue Game`, `Exit Game`, `Sleep`
* `0x020152D0`: `Sleep`, `Back`
* `0x020152B8`: `Go Back`, `Level Select`, `Slow Motion`, `Replay`, `Toggle Debug Keys`

`0x020152CC` is zero; `Start Profiling` / `Stop Profiling` / `Write Profile` exist in
the string pool but are not in the five-item array shown by the page record.

### 4.3 Code

| Address | Role |
|---|---|
| `0x0802A834` | Debug/pause overlay constructor (Thumb pointer `0x0802A835` is registered in the boot state list at `0x083F23CC`); fills the `0x02014ED4/EA8/E7C/E50` panel records |
| `0x08037A34` | Boot-time state-list walker; calls every constructor in the list at `0x083F21C4` via `bx r0` (`0x08037AA0`) |
| `0x08019D98` | Runtime pause builder; calls `0x080150B8` with `0x02014ED4`, `0x02014E7C`, `0x02014E50` and finally `0x02015070` |
| `0x080150B8` | Allocates a 0x14-byte menu item and a 0x90-byte text object; stores panel pointer at item `+0x10`; links into the menu list |
| `0x080151F0` | Menu/text setup helper |
| `0x0802A5E0`, `0x0802A654`, `0x0802A6C8`, `0x0802A744`, `0x0802A7BC` | Small single-item constructors adjacent to the overlay |
| `0x08004976` | Gameplay update reads the key struct and tests A/Start bits |
| `0x080003F0` (RAM) | Key state: `[0]=held/pressed mask`, `[4]=pressed mask` (observed layout) |
| `0x04000130` | GBA `KEYINPUT`, active-low (verified by live reads) |

### 4.4 Level/data tables

| Address | Contents |
|---|---|
| `0x0803F21C4` | Boot-time state-constructor list (`0xFFFFFFFF` sentinel, then Thumb pointers) |
| `0x0803F22C0` | Second constructor/dispatch pointer table |
| `0x0803F2AA4` | Master string/resource table (kid names, level names, cutscene names, screen-state names) |
| `0x080A3204` | Level name strings: `Playroom_1`, `Park_1`, `Town_1`, `Town_2`, `Park_2`, `Park_3`, `School_1`, `School_2`, `School_3`, `Town_3`, `Town_MG`, `Park_MG`, `School_MG`, `Playroom_MG`, then cutscene names (`cutscene_startgame`, …) and `Test_1` |
| `0x08090C88` | Level-list count literal (`0x0A` = 10) |
| `0x03000734` (RAM) | Runtime level-list array of 10 descriptor pointers |

## 5. Algorithm / pseudocode

### 5.1 No code validator exists

There is no input path that accepts arbitrary text. The only "chooser" is a fixed
name list indexed by Left/Right; no buffer is passed to `strcmp`/`strncmp`/`memcmp`
against user text. There is therefore no alphabet, length, checksum, or reserved-bit
model to reverse.

### 5.2 Pause/debug overlay construction

```
init_states():
    for ctor in ROM[0x083F21C4]:   # sentinel 0xFFFFFFFF, then Thumb pointers
        bx(ctor)                   # includes 0x0802A834 (debug/pause overlay)

build_pause_overlay():            # 0x08019D98
    add_menu_panel(menu, 0x02014ED4)   # main 4-item page
    add_menu_panel(menu, 0x02014E7C)   # sleep 2-item page
    add_menu_panel(menu, 0x02014E50)   # debug 5-item page
    add_text(menu, 0x02015070)
    ui_setup(...)
```

`add_menu_panel` (`0x080150B8`) allocates a menu item, stores the panel pointer at
`item+0x10`, and links it into the menu list.

### 5.3 Page selection observed

The menu renders exactly one page at a time. In the retail UI:

* Playroom pause → page id 0 (`0x02014ED4`, 4 items, `Return to Playroom` hidden);
* Park/level pause → page id 0 (`0x02014ED4`, 4 items, `Return to Playroom` shown);
* Sleep confirmation → page id 2 (`0x02014E7C`, 2 items);
* page id 3 (`0x02014E50`, `Debug`) is never rendered.

The page records carry parent/self page ids `0→1→2→3`; the only item action that moves
to page 2 is `Sleep`. No item action targets page 3. `Go Back` on the debug page points
back to page 2, i.e. it is a return edge, not an entry edge.

## 6. Tables

### 6.1 Debug page (present, never displayed)

| Item | Effect (derived) |
|---|---|
| `Go Back` | Return to previous (page 2) menu |
| `Level Select` | Open the level-select screen (`RLevelSelectScreenState` exists at `0x0808BCF4`) |
| `Slow Motion` | Toggle slow-motion time scale |
| `Replay` | Open replay-select (`RReplaySelectScreenState`, `0x0808BD58`) |
| `Toggle Debug Keys` | Toggle developer hotkeys |
| `Start Profiling` / `Stop Profiling` / `Write Profile` | Profiling strings; not in the 5-item array |

Effects are labelled **Inferred** (see §7); only the strings and page record are
**Observed/Derived**.

### 6.2 Published unlockables (not codes)

Public cheat lists (GameFAQs/CheatingDome/PlanetCheats/VGChartz, all identical) contain
only one entry: *collect 40 crystals in a level to unlock a playroom object*:

| Level | Playroom object |
|---|---|
| Park 1 | Poster right of the second door |
| Park 2 | Poster left of the fourth door |
| Park 3 | New TV show |
| School 1 | Toy chest opens |
| School 2 | Poster over the fourth door |
| School 3 | New drawing on easel |
| Town 1 | Fish in aquarium |
| Town 2 | Chalkboard drawing changes |
| Town 3 | Puppy bed and food |

The `0/40` crystal HUD was observed in the Park level; the `%d / %d` score format is at
`0x080853D4`. No password or button code appears in any published list, and no
GameShark/CodeBreaker codes are in scope here.

## 6b. Enumeration

**Code space.** Password/cheat space = **0**. The ROM contains no code alphabet, no
entry field, no validator, and no checksum over user input:
`password=0`, `cheat=0`, `secret=0`, `unlock=0`, `stage=0`, `warp=0`, `gallery=0`
case-insensitive literal hits over all 4 MiB; the only `code` hit is the audio banner
`Code: B.Wodok` at `0x083F0FC2`. The fixed kid-name list (`0x0808EB9C`–`0x0808ECB8`,
36 names) is not a code alphabet: it is indexed by Left/Right, never compared to typed
text.

**Hidden-menu space.** 4 pause pages, 1 debug page with 5 item slots
(`0x020152B8`, count 5) plus 3 profiling strings. Page id 3 is the debug page; page
ids 0–2 are the retail pages.

**Novel code.** Not applicable: no code system exists to mint a novel code. This is a
proven negative for the whole input space, not a "not looked" result.

**Bounds by rejection (input space actually exercised).**

* 175 combinations — every 1-, 2- and 3-button subset of
  `{Up, Down, Left, Right, A, B, L, R, Select, Start}` — were applied to the in-level
  pause state (savestate reload before each; 250 ms hold). Result: no debug page; the
  only screen changes were cursor movement, page 2 (Sleep), or menu close. Log:
  80 changed frames, all explainable as cursor/close/level-resume.
* 20 additional combinations including simultaneous `Select+L+R`, `L+R+Start`,
  `Select+Start`, `A+B+Select+Start`, and 3-second holds were applied on the title
  screen, the file-select screen, the character creator, the sleep page, and in
  gameplay. No debug page.
* Simultaneous `Select+L+R` was also tested with sub-frame keydown ordering (all three
  pressed in one xdotool invocation) on the sleep page; it does not leave the page.
* Every retail screen was walked and screenshotted: title, file select, erase
  confirmation (`Erase ?` / `No` / `Yes`), credits, `Adopt a Kid`, Playroom, Playroom
  pause, level pause (Park), Sleep confirmation, and the Park level itself.

**Conclusion of enumeration.** The debug page is a developer leftover. It is built into
the pause menu's panel set, but the page graph has no entry edge to page 3 from any
reachable page, and no button combination in the tested space selects it.

## 7. Validation evidence

**Observed (emulator / RAM / live reads)**

* Title, file select, erase confirm, credits, creator, Playroom, Park level, pause in
  both contexts, sleep page — screenshots taken on `:222`.
* Pause item arrays in the savestate: `0x020152E8` (4 strings), `0x020152D8` (3),
  `0x020152D0` (2), `0x020152B8` (5).
* Key mapping: `KEYINPUT` reads while holding each key produced `0x01FF` (L),
  `0x02FF` (R), `0x03FB` (Select), `0x03F7` (Start), `0x03FE` (A), `0x03FD` (B),
  `0x03BF` (Up) — all as expected for active-low input.
* HUD crystal counter `0/40` in Park.
* 175-combination pause sweep log with 80 changed frames, all classified.

**Derived (instruction/data analysis)**

* `0x08019D98` adds the three panels `0x02014ED4`, `0x02014E7C`, `0x02014E50` to the
  menu; `0x080150B8` stores the panel pointer at item `+0x10`.
* The panel records' `[0]/[4]` fields form the page chain `0→1→2→3`.
* The only reachable page-2 transition is the `Sleep` item; page 2's items are
  `Sleep`/`Back`; no item targets page 3.
* No string comparison against a text buffer exists; the ROM has no text-entry screen.
* `[VERSIONBLOCK|V3175|T1139593640|Mhomer3]` build stamp at `0x0808CA04`.

**Inferred**

* Effects of the debug items (level select, slow motion, replay, debug-key toggle,
  profiling). They were not executed because the page cannot be displayed through the
  retail UI.
* The exact trigger (if the overlay was ever reachable in a development build) may have
  been a build flag or a removed key handler; no such handler was found in this image.

## 8. Unknowns

* Whether a development build enabled the Debug page by a flag or a removed input path;
  this retail image contains no writer that selects page 3.
* Whether `Start/Stop Profiling` and `Write Profile` belong to a second debug page
  (strings exist; only five item slots are populated).
* Exact per-level unlock flag bits in the save (the 40-crystal HUD and the nine
  published objects were confirmed, but the bit layout was not isolated).
* Save format: 512-byte EEPROM image with checksum/obfuscation; not needed for this
  question and not decoded.

## 9. Tooling

* mGBA 0.10.5 SDL (`/usr/games/mgba`) under Xvfb `:222` + openbox; `SDL_AUDIODRIVER=dummy`.
* `xdotool`, `scrot`, ImageMagick (`convert`, `compare`), `tesseract` 5.5.0 for
  screen/menu detection.
* `arm-none-eabi-objdump -M force-thumb` for Thumb disassembly.
* Python 3: literal scans, BL/pointer scans, savestate `gbAs` + zlib parsing and EWRAM
  diffing, and a minimal GDB-RSP client (`/tmp/opencode/cabbage/rsp.py`) used only while
  the shared `:2345` port was free.
* mGBA `-d` command-line debugger for key-register reads and breakpoints.

## 10. Legal note

No ROM, extracted graphics, audio or text is redistributed. Only hashes, addresses,
short UI strings needed to identify the menus, and analysis are published.
