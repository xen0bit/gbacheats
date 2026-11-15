# Disney's Lilo & Stitch 2: Hämsterviel Havoc (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney's Lilo & Stitch 2: Hämsterviel Havoc/Disney's Lilo & Stitch 2: Hämsterviel Havoc.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `LILO&STITCH2` |
| Game code | `BLSE` (USA) |
| Maker | `4Q` |
| Version | 0x00 |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| Header complement (0xBD) | `0x4F` (valid); header checksum (0xBE) = `0x0000` — rebuilt/blank checksum, common for re-dumped images |
| MD5 | `3034c7101bceebdea95300ae9ecd7453` |
| SHA-1 | `70e0dc5a8dcdf876b5dd87a4c1bbca03b6e30148` |
| SHA-256 | `c9be397256e0535c515401b0e61a99f15f677d2504ec66e145647f41db55fa55` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at file
offset 0x4 (the primary header). There is no second GBA image, no
multi-game shell, and no appended trainer/cracktro; the first 4 KiB contain
the normal vector table and stock crt0 (`0x080000C8`…`0x080001C8`), not a
scene intro. The image is the retail USA SKU.

## 2. Executive summary

This ROM has **no reachable password, button-code or password-style unlock
system**. Every text entry point, menu and in-game screen was walked on
emulation; the only occurrences of the words *password*, *cheat* and *unlock*
in the image are (a) a block of **Nicktoons Racing leftovers** (same Climax
engine, documented by TCRF) that contains the literal `Enter Password` at
0x6DA94, and (b) the strings of a **six-entry developer cheat menu** at
0x9992C–0x999A0.

The cheat menu is real, fully implemented, and still present in retail:

```
- CHEAT MENU -
ALL CHEATS ON
UNLOCK EVERYTHING
UNLOCK ALL LEVELS
UNLOCK ALL EXPERIMENTS
INVINCIBILITY
RESET EVERYTHING
```

It is reachable only through screen id 27, and screen 27 is entered only from
the world-map screen when the gate word at **`0x03005724` is non-zero**
(`ldr r4,[0x03005724]; cmp r4,#0; bne 0x0800DCA0` at `0x0800DE04`). The
whole 8 MiB image contains exactly **two** literal references to address
`0x03005724`: one store at `0x0800DB5A` that writes **0** during map-screen
initialisation, and one read at `0x0800DEC4` for the gate. A
register-propagating scan over the whole executable region (0x0–0x80000,
Capstone, tracking `ldr =addr` plus constant `add`/`sub`/`mov`) found exactly
one store to the address — `0x0800DB5C`, value 0 — and no second writer. The
branch is therefore never taken: the menu is
**dead code** left over from the April 2004 prototype (TCRF: the prototype
had a level select with a cheat menu opened with L/R). Holding L or R on the
retail map, alone or with A/B/Select/Start, does not open it.

Because the engagement asks for a cheat surface, the menu was enumerated by
setting only the gate word in a savestate (labelled diagnostic, not an input
code): all six entries were exercised and their RAM effects measured. The
only cheat-like content a normal player can reach is the ordinary
unlockable progression (levels/experiments), which is save data, not a code.

The published first-game code (`hold R+Select and press A` on *Lilo &
Stitch* 2002) was tested on this SKU: it produces no effect and in fact
suppresses the A press. The sequel's published lists (GameFAQs/Almar's) contain
only CodeBreaker memory-edit codes, which are out of scope; no in-game
password or button-code list exists.

## 3. How to reproduce

* Emulator: mGBA 0.10.x, SDL, `-3` scale, `DISPLAY=:328`, `SDL_AUDIODRIVER=dummy`.
* Default mGBA keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrows.
* Title → `Start` → Main Menu (`Play Game`, `Options`, `Extras`).
* `Play Game` → Select Save Slot (3 slots) → Choose an icon (10 icons) →
  intro cutscene → level.
* In-game `Start` → Pause Menu (`Return to Game`, `Options`, `Exit to Map`,
  `Quit Game`). `Exit to Map` → `Yes` returns to the world map.
* Map screen: D-pad moves the circular cursor between the 7 level nodes;
  `A` enters the highlighted node.

Cheat-menu diagnostic (no controller input reaches it):

1. Reach the world map.
2. In any savestate editor, write `0x00000001` to IWRAM `0x03005724`
   (or take the supplied state and patch it; see §9).
3. Move to a level node and press `A`. The purple `- CHEAT MENU -` screen
   appears instead of the level.
4. Up/Down wrap 0↔5; `A` activates; `B` does nothing; after activation the
   screen closes back to the map.

Published code test: at the Main Menu with the cursor on `Play Game`, hold
R (`s`) + Select (`BackSpace`) and press A (`x`). Observed: the menu does not
advance (the A press is swallowed); no 99-lives state appears. This is the
only in-game code published for the preceding game and it is not implemented
here.

## 4. Address map

| Address | Size | Meaning |
|---|---|---|
| `0x0806CE84` | 4×N | screen-handler table (Thumb pointers; low bit set) |
| `0x0806CEF0` | 4 | table entry **27** = `0x0800E769` → cheat-menu screen `0x0800E768` |
| `0x0800DCA0` | — | gate-taken block: stores 26 to `0x03005ECC`, returns screen id **27** |
| `0x0800DE04` | — | gate read: `ldr r4,[0x03005724]; cmp r4,#0; bne 0x0800DCA0` |
| `0x0800DB5A` | — | only writer of the gate: `str r4,[0x03005724]` with `r4=0` |
| `0x03005724` | 4 | cheat-menu gate word (IWRAM, BSS; default 0) |
| `0x0800E768` | — | cheat-menu screen: init, draw, input loop (returns to map) |
| `0x0800EAA8` | — | cheat-menu renderer (title + 6 rows) |
| `0x030057A0` | 4 | cheat-menu selected index (0…5), wrap-around |
| `0x03001444`…`0x03001458` | 6×4 | row label pointers, initialised from ROM `0x7AD478` |
| `0x7AD478` | 0x20 | six label pointers (`0x08099990`, `0x0809997C`, `0x08099968`, `0x08099950`, `0x08099940`, `0x0809992C`) |
| `0x080999A0` | — | `- CHEAT MENU -` |
| `0x08099990` | — | `ALL CHEATS ON` |
| `0x0809997C` | — | `UNLOCK EVERYTHING` |
| `0x08099968` | — | `UNLOCK ALL LEVELS` |
| `0x08099950` | — | `UNLOCK ALL EXPERIMENTS` |
| `0x08099940` | — | `INVINCIBILITY` |
| `0x0809992C` | — | `RESET EVERYTHING` |
| `0x030012C0` | 8 | level-unlock array #1 (default `00 00 00 00 01 00 00 00`) |
| `0x03001300` | 8 | level-unlock array #2, set together with #1 by `UNLOCK ALL LEVELS` |
| `0x030012FB` | 1 | “all experiments” flag |
| `0x030012FE` | 1 | “invincibility” flag |
| `0x0800DB24`…`0x0800DB44` | — | map-screen init that clears `0x03001420`…`0x03001438` and the gate |
| `0x0806D960` | 4×N | global UI label-pointer table (contains both Lilo 2 and Nicktoons leftovers) |
| `0x6D7E8` | — | start of Nicktoons Racing leftover text (TCRF-confirmed) |
| `0x6DA94` | — | `Enter Password` — Nicktoons Racing leftover, no Lilo 2 menu uses it |

crt0 initialises IWRAM from ROM in three blocks (`0x0800010C`…`0x08000138`):
`0x087AC03C→0x03000000` (0xC48 bytes), `0x087ACC84→0x03000C48` (0x968),
`0x087AD5EC→0x030015B0` (0x3FD4). The cheat-label array at `0x7AD478` is part
of the second block (`0x087ACC84 + 0x7F4`), so the row pointers are in place
before any menu runs.

## 5. Algorithm

### 5.1 Map screen → cheat menu gate

```
map_screen():                       ; screen id 26, entry 0x0800DAE8
    ...
    *(u32*)0x03005724 = 0;          ; 0x0800DB5A  (r4 was zeroed at 0x0800DB26)
    *(u32*)0x03005730 = 0x514;
    ... initialise map, draw ...
    do {                            ; 0x0800DECC input loop
        vblank();
        selected = map_cursor();    ; 0x0800DF14, returns 1 when A selects a node
        draw_map();
    } while (selected == 0);
    if (*(u32*)0x03005724 != 0) {   ; 0x0800DE04/08 — never true in retail
        *(u32*)0x03005ECC = 26;     ; 0x0800DCA0
        return 27;                  ; screen table index 27 = cheat menu
    }
    return 23;                      ; normal level start
```

### 5.2 Cheat-menu screen

```
cheat_menu():                       ; 0x0800E768, table index 27
    disable_irq(); video_init(); load_map_background();
    *(u32*)0x030057A0 = 0;          ; selection
    for (;;) {
        vblank();
        if (menu_input()) break;    ; 0x0800EA34; updates 0x030057A0, wraps
        draw();
    }
    return *(u32*)0x03005ECC;       ; 26 = back to map
```

`draw()` (`0x0800EAA8`) loads `0x080999A0` (`- CHEAT MENU -`) and iterates
six rows from `0x03001444`, highlighting the row equal to `0x030057A0`.

### 5.3 Menu item effects

`A` dispatches on the selected index and writes the shared save-state block;
the changes were measured by diffing IWRAM between a savestate taken on the
menu and one taken immediately after activation (one item per run, reloading
the baseline each time):

| # | Label | Effect (IWRAM) |
|---|---|---|
| 0 | `ALL CHEATS ON` | `0x030012C0..C7 = FF×8`; `0x03001300..07 = FF×8`; `0x030012FB = 1`; `0x030012FE = 1` |
| 1 | `UNLOCK EVERYTHING` | `0x030012C0..C7 = FF×8`; `0x03001300..07 = FF×8`; `0x030012FB = 1` |
| 2 | `UNLOCK ALL LEVELS` | `0x030012C0..C7 = FF×8`; `0x03001300..07 = FF×8` |
| 3 | `UNLOCK ALL EXPERIMENTS` | `0x030012FB = 1` |
| 4 | `INVINCIBILITY` | `0x030012FE = 1` |
| 5 | `RESET EVERYTHING` | restores `0x030012C0..C7` and `0x03001300..07` to the default `00 00 00 00 01 00 00 00` |

Observable results: after item 0/1/2 the world map immediately shows the full
set of level nodes (one large node before, several additional white node
markers after); item 3 produces no map change; item 4 produces no map change;
item 5 removes the extra nodes again. The unlock arrays are RAM-only in this build: after
`Quit Game` back to the title and a fresh `Play Game`, the `Extras` menu still
contains only `High Scores` and `Credits`, i.e. the cheat did not persist to
EEPROM.

## 6. Tables

### 6.1 Cheat-menu labels and index

| Index | Label | ROM address |
|---:|---|---|
| 0 | `ALL CHEATS ON` | `0x08099990` |
| 1 | `UNLOCK EVERYTHING` | `0x0809997C` |
| 2 | `UNLOCK ALL LEVELS` | `0x08099968` |
| 3 | `UNLOCK ALL EXPERIMENTS` | `0x08099950` |
| 4 | `INVINCIBILITY` | `0x08099940` |
| 5 | `RESET EVERYTHING` | `0x0809992C` |

The row array at ROM `0x7AD478` also contains two earlier strings at
`0x080998FC` (` QUEST  PLAY`) and `0x080998EC` (`SCORE  ATTACK`) that are part
of the same dead descriptor but are not drawn: the renderer starts at
`0x03001444`, i.e. at the third pointer.

### 6.2 Screen-table neighbours (context for the dead menu)

| Index | Entry |
|---:|---|
| 24 | `0x0800CF31` |
| 25 | `0x0800D11D` |
| 26 | `0x0800DAE9` — world map (contains the gate check) |
| 27 | `0x0800E769` — `- CHEAT MENU -` |
| 28 | `0x00000000` (unused) |
| 29 | `0x080026D5` |

### 6.3 Nicktoons Racing leftover block (retail, unused)

`0x6D7E8` onwards contains the whole Nicktoons Racing front-end label set
(`PICKLES PARKWAY`, `SAFARI SPEEDWAY`, `BIKINI BOTTOM BLOWOUT`, `CUP 1..3`,
`SELECT RACE`, `SELECT TRACK`, `SELECT CUP`, …) followed at `0x6DA38` by
`Reset Saves`, `Select Save Slot`, `Test Level`, `Level 2`, `Level 1`,
`Driving Demo`, `Platform Demo`, **`Enter Password`**, `New Game`,
`Single Player`, `Battle`, `Versus`. These labels are pointers inside the
shared UI label table (`0x6D960` base, entries `0x6DA00`…`0x6DA2C`); no Lilo 2
screen references them. `Enter Password` therefore does **not** denote a
password entry screen in this game.

## 6b. Enumeration

### Space definition

* **Password space: none.** The game has no password entry screen, no input
  alphabet, no length check and no validator. The singular `Enter Password`
  literal at `0x6DA94` belongs to the Nicktoons Racing leftover block
  (0x6D7E8–0x6DC4C) and is not referenced by any reachable screen.
* **Button-code space: none found.** A scan for contiguous tables of 4 or
  more 16-bit button masks (A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20,
  Up=0x40, Down=0x80, R=0x100, L=0x200) in the executable region returned
  **0 tables in 0x0–0x50000** (the first mask-like run in the image is at
  `0x6D4A8`, inside data). The on-screen menus use edge-triggered navigation,
  not sequences.
* **Hidden-menu space: one screen.** Screen id 27, six entries, enumerated in
  §5.3. It is gated by `0x03005724`.

### Why the hidden menu is in no published list

GameFAQs, Almar's and the CodeBreaker mirrors publish only memory-edit codes
for this SKU (e.g. `32009E86 0006` infinite health); none mention a cheat
menu. TCRF documents only the leftover text and the unused level icon, not
the menu. The menu exists in the image and was exercised here; its gate makes
it unreachable on a retail cart without a memory edit.

### Bounds proven by rejection

* **Gate value.** Exact 4-byte search over all 8,388,608 bytes of the image
  finds the address `0x03005724` at exactly two offsets: `0xDBF8` and
  `0xDEC4`. `0xDBF8` is the literal used by the store at `0x0800DB5A`
  (`str r4,[r0]`, `r4=0`); `0xDEC4` is the literal used by the gate load at
  `0x0800DE04`. A register-propagating Capstone scan of 0x0–0x80000 for
  constants loaded from literal pools followed by constant `add`/`sub`/`mov`
  and a store found **one** store to `0x03005724` (`0x0800DB5C`, value 0)
  and no other. The branch at `0x0800DE0A` is unreachable from retail input.
* **Dynamic confirmation.** A breakpoint at `0x0800DE04` was hit on world-map
  entry with `r4=0x03005724` and `[0x03005724]=0x00000000`; the normal
  `return 23` path ran and the selected level started.
* **Input rejection.** On the world map, every single button and the
  combinations `L+R`, `L+Select`, `R+Select`, `L+R+Select`, `A+B`, `L+A`,
  `R+A`, `L+R+A`, `L+R+Select+A`, `Select`, `Start`, `B` left the menu closed
  and entered the level normally (the gate was still 0). At the Main Menu the
  first game's published `R+Select+A` was rejected (A swallowed).
* **Menu value bounds.** On the cheat screen, `Up` from index 0 wraps to 5 and
  `Down` from index 5 wraps to 0; indices outside 0…5 cannot be selected.
  `RESET EVERYTHING` was run on a state with both unlock arrays set to
  `FF×8` and returned them to `00 00 00 00 01 00 00 00`, proving the reset
  path and the default bit pattern.

### Negative space checked (counts)

* `strings -n 3` keyword counts over the whole image: `password` = 1
  (`0x6DA94`, leftover), `cheat` = 2 (`ALL CHEATS ON`, `- CHEAT MENU -`),
  `debug` = 0, `secret` = 0, `unlock` = 3 (the three UNLOCK labels),
  `level select` = 0, `sound test` = 0.
* Screens walked: title, Main Menu (3 items), Options (2), Extras (2), Save
  Slot (3), Icon Select (10), Pause Menu (4), world map (7 nodes), cheat menu
  (6 entries, diagnostic only). No password screen, no level-select screen,
  no debug keypad.
* Published in-game code tested: `R+Select+A` (Lilo & Stitch 2002) → no
  effect. Published CodeBreaker entries are memory writes and out of scope.

## 7. Validation evidence

**Observed**

* Hashes/header/entry word and the single header occurrence (§1).
* All retail menus, the world map and the in-game pause menu (§3).
* The cheat menu screen, its six labels, wrap-around selection, and the
  immediate map change after items 0/1/2 (§5.3, screenshots taken).
* IWRAM diffs for each of the six menu items, listing the exact bytes changed
  (§5.3).
* Gate word equal to 0 at the `0x0800DE04` breakpoint while the map was live.
* The `Extras` menu still showing only `High Scores` and `Credits` after the
  cheat arrays were set and the game was quit back to the title.
* The published first-game `R+Select+A` being rejected (menu does not advance).

**Derived**

* Screen 27 is entered only by `0x0800DCA0`, whose only caller is the gate
  branch at `0x0800DE0A`; the screen-table entry 27 is `0x0800E769`.
* `0x03005724` has exactly one writer in the image and it stores 0, so no code
  path can open the menu. This is a closed negative for the retail build.
* The six row pointers are initialised by the crt0 `.data` copy; the menu
  therefore survives into retail intentionally as data + code, not as a
  runtime-generated screen.

**Inferred**

* `0x030012C0` and `0x03001300` are two 8-byte level-unlock arrays (both are
  filled by `UNLOCK ALL LEVELS`); the map-icon change and the default `01` at
  offset +4 support this, but the exact level-to-bit mapping is not labelled
  by the ROM.
* `0x030012FE` is the invincibility flag (the menu label and the `ALL CHEATS
  ON` superset agree); the damage routine that reads it was not isolated.

## 8. Unknowns

* The specific reader of `0x030012FE` (damage code) was not located; no
  literal reference to the address exists, so it is reached through a RAM
  pointer. Damage immunity is inferred from the label, not exercised against
  an enemy.
* The exact level-to-bit mapping of the two 8-byte unlock arrays is not proven;
  both are set by `UNLOCK ALL LEVELS`, and the visible effect is the expanded
  set of map nodes.
* The cheat block was not found to be persisted to the 512-byte EEPROM save;
  a fresh boot did not show the extra `Extras` entries. Whether the prototype
  wrote it to save is outside this image.
* `0x00860F10` (TCRF's unused-level-icon address) is larger than this 8 MiB
  file; it could not be reproduced as a file offset here and is treated as an
  unverified external note.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* Python 3 + Capstone 5.0.7 for literal-pointer and instruction scans
* `strings -t x`, `xxd`, `grep`
* mGBA 0.10.x (SDL) under `Xvfb :328` + `openbox`
* mGBA GDB stub (`mgba -g`) with `gdb-multiarch` for the gate breakpoint
* mGBA savestates parsed as PNG `gbAs` chunks (zlib) for RAM diffs; a small
  re-packer was used to set the gate word in a copy of a state
* Scripts (working directory `/tmp/opencode/lilo2`):
  `drive.py` (X11 input/screenshots), `ss.py` (savestate extractor),
  `patch_ss.py` (savestate patcher), `emu_dbg.py`/`gdb_driver.py`
  (debugger drivers)

Legal note: no ROM, graphics, music or game text is redistributed here; only
addresses, hashes, algorithms and short UI strings necessary for
reproduction are reported.
