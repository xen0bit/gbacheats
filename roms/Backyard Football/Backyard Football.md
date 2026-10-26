# Backyard Football (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Backyard Football/Backyard Football.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`) |
| Header title (`0xA0`) | `BACKYARDFBL` + `0x00` |
| Game code (`0xAC`) | `AYFE` |
| Maker (`0xB0`) | `70` |
| Version (`0xBC`) | `00` |
| Fixed `0xB2` | `0x96` ✔ |
| Entry (`0x00`) | `0xEA000030` → ARM branch to `0x080000C8` |
| Header complement (`0xBD`) | `0xB0` (computed `0xB0` over `0xA0..0xBC`) ✔ |
| Reserved `0xBE..0xBF` | `0x0000` |
| MD5 | `9085dd5a5ef4b2820a838c375301fec2` |
| SHA-1 | `d44ef8eb521838ff013904b74d214c17e3e1c801` |
| SHA-256 | `bf7ed436176eaf4543670213bbf812fee22a37cf44f018c27fc828a41b0dc2d8` |

Embedded-header scan (156-byte Nintendo logo `24 FF AE 51 …` searched as an
exact match at every byte offset of the whole 4 MiB):

* `0x000000` — the single game header (title `BACKYARDFBL`, code `AYFE`, ver 00).
* **No other logo hit**, therefore no concatenated second game image, no
  multiboot/link-cable child image, and no "2-in-1" shell.
* No patch/trainer: the entry word is the stock `b 0x080000C8`, the logo and
  complement check are unmodified, and the entry lands on the normal crt0
  (`mov r0,#0x12; msr CPSR_c,r0; ldr sp,[pc,#-20]` with the SP literals at
  `0x080000C0`/`C4`).

Verified with `md5sum`, `sha1sum`, `sha256sum`, `xxd -l 0x200`, and a Python
logo scan; nothing in the image advertises a modified build.

## 2. Executive summary

**This build has no password system, no button-code ("cheat") system, and no
reachable debug menu.** It is a single-region retail AYFE image; all of the
cheat content published for *Backyard Football* is for the PC, Mac and GameCube
versions (typed codes / a "cheats screen") or is GameShark/CodeBreaker memory
patching for the GBA, which is outside the requested scope.

What the ROM does contain, and what this report documents:

* **An unreachable developer statistics module.** Strings for a `Debug Screen`,
  `Systems Menu`, `Performance Menu`, `Profiling Menu`, `Slow RAM`, `Fast RAM`,
  `Message System`, `Entity Allocator`, frame-rate stats and a 12-system
  profiler live at `0x0807D520`–`0x0807DAC8`, with the build stamp
  `Built: Jun 26 2002` / `Host:  scameron` / `14:13:43`. The code that draws it
  is a complete Thumb function at `0x080055F0` plus its sub-pages. **No
  instruction in the 4 MiB image calls it, no literal or table points to it, and
  a breakpoint on it never fires during a full menu walk.** It is dead code in
  this build, not a hidden menu behind a button gate.
* **No code-entry UI of any kind.** There is no keyboard, no character grid, no
  password field. The only name-like control in the game is the custom-player
  *nickname*, which is chosen from a fixed 232-entry list at `0x08084208`
  (LEFT/RIGHT cycles the list); nothing is ever typed.
* **Earned unlockables only.** Pablo Sanchez (`SECRET WEAPON`) exists as a
  player card and roster record; on a fresh save the Player Select pool cycles
  14 named players plus `Custom Player` (whose portrait is the `"?"` card) and
  **does not offer Pablo**. The published unlock ("beat the game on any
  difficulty") is a play-through trigger, not an input code.
* **Published codes verified absent.** Every PC/Mac/GameCube code literal
  (`MRCLANKY`, `superkid`, `sharpeye`, `whatatackle`, `moreplays`,
  `superspeed`, `GHOST`, `Walter Payton`) occurs **0 times** in the ROM
  (case-insensitive), and the GBA build has no screen on which they could be
  entered.

The whole documented search space is enumerated in §6b: **0 password tables,
0 button tables, 0 valid entry points.** The negative is bounded by explicit
counts over the entire 4 MiB image and by emulator/GDB evidence, not by
"couldn't find it".

## 3. How to reproduce

Emulator and display used for this session:

```bash
Xvfb :157 -screen 0 1024x768x24 &
DISPLAY=:157 openbox &
DISPLAY=:157 SDL_AUDIODRIVER=dummy mgba -3 "Backyard Football.gba" &
```

mGBA 0.10.5 (SDL). Default keymap used: **A=`x`, B=`z`, L=`a`, R=`s`,
Start=`Return`, Select=`BackSpace`, D-pad=arrows**. Hold keys 100–300 ms;
menus need a release between presses. Screenshots via `scrot`, cropped
`720x480+153+164`.

Boot path (≈12 s, no input): *Licensed by Nintendo* → *Infogrames* →
*Humongous* copyright → *NFL* notice → *Torus Games* → title
(`PRESS START`) → main menu.

Complete reachable menu map (every entry opened):

```
title (PRESS START)
└─ main menu (8 items)
   ├─ PICKUP GAME   → Difficulty Level → random matchup → commentary → play
   │                   └─ Start in play → PAUSE (RESUME / QUIT)
   ├─ EXHIBITION    → Difficulty → Team Select → Field Select (weather)
   │                   → Leather Or Laces → Player Card (PICK ME?) → Player Select
   │                   → Team Photos → matchup → commentary → play
   ├─ SEASON PLAY   → Difficulty → Select Home Field → Team Select → Player Select
   │                   → Team Photos → Season Menu
   │                   └─ BEGIN SEASON / LEAGUE STANDINGS / TEAM STATISTICS /
   │                      TEAM STRATEGY / OPTIONS / QUIT GAME
   ├─ PRACTICE      → Team Select → Player Select → Practice Setup
   │                   (OFFENSIVE/DEFENSIVE, START ON OWN/OPP + yard + down)
   │                   → playbook → play
   ├─ MULTIPLAYER   → "Waiting..." (link cable; no menu)
   ├─ OPTIONS       → MUSIC / COMMENTARY / AUTO-SAVE AFTER EVERY GAME
   ├─ PLAYER CARDS  → card browser (L/R NEXT/PREV), all cards incl. Pablo
   └─ CREDITS       → scrolling credits
```

Other screens reached: SELECT-INFO panels (opened on the main menu, difficulty,
practice and season screens); PLAYER CARD `PICK ME? YES/NO`; CUSTOM PLAYER
editor (NICKNAME list, HAIR, HAIR COLOR, BODY) and `Add Skill Points`; TEAM
PHOTOS; in-play PLAYBOOK; TIME OUT OPTIONS (`TEAM STRATEGY`, `CHANGE
OFFENSE/DEFENSE/KICKING/KICK RET. PLAYBOOK`, `QUIT GAME`).

Savestate used for repeated tests: `Backyard Football.ss1`, saved on the Pickup
matchup screen. mGBA 0.10.5 savestates are PNGs whose `gbAs` chunk is a zlib
stream of 397,312 bytes:

```
0x00000–0x19000  VRAM / palette / OAM / I/O
0x19000–0x21000  IWRAM  (0x03000000–0x03007FFF)
0x21000–0x61000  EWRAM  (0x02000000–0x0203FFFF)
```

`state.py` in the tooling directory extracts this and maps `0x03xxxxxx` /
`0x02xxxxxx` to the correct offset.

### Tested inputs / negative controls

| Input | Where | Result |
|---|---|---|
| `L+R+Start+Select` held 1 s | boot logos, title | no change; no debug screen |
| `L+R+Select`, `L+R+Start`, `A+B+Start+Select` | title, main, options, pause | no change |
| `Up Up Down Down A` (`uudda`) | matchup screen | starts game normally; no cheat state |
| `Down Up Down Up A` (`dudua`) | matchup screen | no effect |
| `Select Select B B Start` (`ssbbt`) | matchup screen | no effect |
| `Up Up Left Right B A` (`uulrba`) | matchup screen | no effect |
| 8-press `Up Up Down Down Up Up Down Down` | matchup screen | no input-letter buffer created (see §6b) |
| `MRCLANKY`, `superkid`, `sharpeye`, `whatatackle`, `moreplays`, `superspeed`, `GHOST`, `Walter Payton` | not present in ROM; no text-entry screen exists | not enterable |

The four `uudda`-family sequences were tested because the sibling GBA title
*Backyard Basketball* uses a 17-entry ASCII table matched with `strstr` on its
pre-game screen. They are **not** in this ROM in any encoding (§6b), and the
game's behaviour is unchanged.

## 4. Address map

File offset → ROM address is `0x08000000 + offset`. All code is Thumb unless
noted. Verified with `arm-none-eabi-objdump -M force-thumb`, Capstone, and
Ghidra 12.1.4 (REA).

### 4.1 Dead debug module (present, unreferenced)

| Symbol | ROM address | File offset | Notes |
|---|---:|---:|---|
| Debug string block | `0x0807D520`–`0x0807DAC8` | `0x7D520` | all labels, format strings, build stamp |
| Debug label pointer array | `0x0803F9E58` | `0x3F9E58` | 15 × `u32` string pointers (pages/items), zero terminator |
| Debug root draw/update | `0x080055F0` | `0x55F0` | 98 bytes, 9 basic blocks; prints `Debug Screen`, `Built`, `Host`, separator; creates menu object `0x030019E0` |
| Debug dispatch | `0x080056F4` | `0x56F4` | switch on menu result 0..4; jump table `0x08005720` |
| Systems Menu page | `0x08005854` | `0x5854` | Slow RAM / Fast RAM / Message System / Entity Allocator |
| Profiling page | `0x08005978` | `0x5978` | profiler bars + `Show raw numbers` |
| Aux page handlers | `0x08005724`, `0x08005738`, `0x08005790`, `0x080057C8`, `0x080057E4` | | page bodies reached only from the dispatch |
| Menu object | `0x030019E0` | IWRAM | written only inside the debug module |
| Menu label pointer | `0x030019E4` | IWRAM | |
| Build stamp | `0x0807D58C` / `0x0807DAC0` | | `Jun 26 2002`, `14:13:43`, host `scameron` |

**Reference audit.** `u32` scans over all 4 MiB for `0x080055F0` and
`0x080055F1`: 0 hits. Thumb `BL`/`BLX` scan to `0x080055F0`: 0. Ghidra
`xrefs(0x0807D57C)` → only `0x080055F8` (the function's own literal pool);
`procedure_callers(0x080055F0)` → `[]` (complete). `u32` scan for any pointer
into `0x0803F9C00`–`0x0803FA000` (the label array's page): 0 hits. The module
cannot be entered in this build; there is no gate to find.

### 4.2 Engine input path (used by every menu, not a cheat)

| Symbol | ROM address | Notes |
|---|---:|---|
| Keypad read / edge detect | `0x0806B82C` | `held = ~*(u16*)0x04000130 & 0x3FF`; `pressed = held & ~last` |
| Input state struct | `0x03000E48` | `+6` = last held, `+8` = newly pressed (u16) |
| Per-frame idle hit | `0x0806ECE0` | used as a GDB control breakpoint |

### 4.3 Roster / card data

| Symbol | ROM address | Notes |
|---|---:|---|
| Name list (232 NUL-terminated names) | `0x08084208`–`0x08085038` | index 0 `Custom player`, then players alphabetically |
| Player record table | `0x0808503C` | stride `0x28`; record 0 = Achmed, …, 40 = `Custom player` |
| Pablo Sanchez name | `0x080843AC` | record #26 at `0x0808544C` |
| Card display name `SECRET WEAPON` | tile-drawn, not ASCII | rendered on Pablo's card |
| Fresh EEPROM save | `Backyard Football.sav` | 512 bytes; checksum `0x9C622A5E` at `+0x04`; rest zero |

The `0x28` record is `{u32 name_ptr; 34 bytes stats/ids; u16 0}`. Records 0–40
are the primary roster (Achmed … Vicki Kawaguchi, then `Custom player`); the
name list continues to `Bobby Mcbobbins` for the nickname chooser. The Player
Select pool observed in play is a 14-name subset of that roster plus
`Custom player` (§6b).

## 5. Algorithm

### 5.1 There is no code validator

No function in the ROM reads a player-entered string and compares it against a
table: there is no text-entry screen, and the image contains no ASCII code
table, no key-mask sequence table, and no ASCII button recorder (all three
searched exhaustively in §6b). The only input history in the engine is the
one-frame `last`/`pressed` word at `0x03000E48`, which every menu uses for
normal navigation. This is the significant algorithmic finding, and it is
stated as a bounded negative in §6b rather than as an inference.

### 5.2 What a would-be debug gate would have to do

For completeness, the unreachable module's control flow is:

```
FUN_080055F0(arg):
    menu_begin()                          # 0x0806B1D4
    text(0x0807D57C)                      # "Debug Screen\n"
    text(0x0807D58C)                      # "Built: Jun 26 2002\n"
    text(0x0807D5A0)                      # "Host:  scameron\n"
    text(0x0807D5B4)                      # separator
    create menu at *0x030019E0, item list 0x030019E4
    switch (menu_input(..., 4)):          # 0x0806B3C8, 4 items
        1 -> FUN_080056F4(arg)            # Options dispatch
        2 -> FUN_08005854(arg)            # Systems Menu
        3 -> FUN_08005978(arg)            # Profiling Menu
        0 -> exit                         # Back
```

`FUN_080056F4` is the nested dispatcher (jump table `0x08005720`); the
Systems/Performance/Profiling pages are plain stats screens: the only state
change anywhere in the module is `Reset Frame Rate`, which clears the frame
counters. There is no give-item, unlock, level-select or flag-setting action.

### 5.3 Input edge detection (whole game)

```
held    = (~*(u16*)0x04000130) & 0x03FF
pressed = held & ~(*(u16*)0x03000E48 + 6)
*(u16*)(0x03000E48 + 6) = held
*(u16*)(0x03000E48 + 8) = pressed
```

Nothing in this path stores ASCII button letters. Unlike *Backyard Basketball*
(which appends `'a'`,`'b'`,`'d'`,… to `0x030007F0` and runs `strstr`), this
build has no recorder and no buffer.

## 6. Tables

### 6.1 Debug menu contents (unreachable; enumerated from the ROM)

Root page (`0x0807D57C`): title `Debug Screen`, `Built: Jun 26 2002`,
`Host:  scameron`, separator; the menu is created with **4 rows** and
`FUN_080055F0` dispatches results 1/2/3 to the three sub-pages, 0 = Back. The
label pool at `0x0803F9E58` holds `Options`, `Back`, `Systems Menu`,
`Performance Menu`, `Profiling Menu`.

| Page | Entries | Effect |
|---|---|---|
| Systems Menu (`0x08005854`) | Slow RAM, Fast RAM, Message System, Entity Allocator, Back | prints `Available/Largest Block/Used Blocks/Free Blocks`, `BSS Size/Free Stack`, `Max Listeners: (Unavailable)`, `Max Blocks/Blocks/Max Memory/Memory`; read-only |
| Performance Menu | Reset Frame Rate, Frame Rate, Back | `Reset Frame Rate` clears avg/min/longest counters and prints `Frame Rate Reset`; `Frame Rate` prints `Avg Rate/Frame Rate/Min Rate/Longest Frame` |
| Profiling Menu (`0x08005978`) | Show raw numbers, Back | prints per-system bars for `MAIN_LOOP`, `AI_SYSTEM`, `Z_ORDERER`, `MAP_SYSTEM`, `SPRITE_SYSTEM_ENGINE`, `SPRITE_SYSTEM_UPDATES`, `SOUND_SYSTEM`, `CAMERA`, `LINK_SYSTEM_SEND`, `LINK_SYSTEM_RECEIVE`, `PLAYER_CONTROL_HUMAN`, `GAME_ENTITY_MANAGER`, `PLAYERS`, `BALL`, `COLLISIONS`, `PLAYER_COLLISIONS`; `Show raw numbers` toggles percentage vs raw display |

There is no cheat entry, no unlock toggle and no flag write. The menu is a
profiling overlay from the developer build (`Host: scameron`, Torus Games).

### 6.2 Reachable menu item counts

| Screen | Items |
|---|---|
| Main menu | 8 |
| Options | 3 |
| Difficulty Level | 3 presets + 3 toggles (Power-ups, Fatigue, Turnovers) |
| Team Select | 2 conferences × 4 divisions × 5 teams = 40 |
| Field Select | 10 stadiums + SUN/RAIN |
| Matchup | 4 read-only fields |
| Pause | 2 |
| Time Out Options | 6 |
| Season Menu | 6 |
| Practice Setup | 3 controls |
| Player Cards | card browser (L/R), Pablo Sanchez included |
| Player Select | 14 named entries + `Custom Player` (the `"?"` portrait) in the observed cycle; Pablo Sanchez not offered on a fresh save |

### 6.3 Published codes (verification)

| Source | Platform | Code | Present in GBA ROM? |
|---|---|---|---|
| GameFAQs GBA page | PC | `sharpeye`, `whatatackle`, `MRCLANKY`, `moreplays`, `superspeed` | **no** (0 hits) |
| GameFAQs GBA page | Mac | `superkid`, `sharpeye`, `whatatackle`, `superspeed`, `moreplays`, `MRCLANKY` | **no** (0 hits) |
| GameFAQs GBA page | GameCube | `GHOST` | **no** (0 hits) |
| GameFAQs GBA page | unlockable | Walter Payton as coach name | **no** (0 hits) |
| SuperCheats / GameHacking / Almar's | GBA | GameShark/CodeBreaker (P1/P2 score, quarter, time, first down, etc.) | memory-patch codes, out of scope |

No published list contains a GBA in-game password, button combination or
debug-menu code. The GBA "Cheats" page defers entirely to PC/Mac/GameCube
entries.

Sources checked (2026-10): GameFAQs GBA cheats page (PC/Mac/GameCube entries
shown above), SuperCheats *Backyard Football* GBA codes (GameShark only),
GameHacking.org `game/3898` and Almar's CodeBreaker page (GameBreaker/
CodeBreaker only), the SuperCheats FAQ (controls/menu walkthrough), and the TCRF
mirror `tcrf.tiago.zip` page for *Backyard Football (GBA)*, which documents the
same debug text at `0x7D520` with no reachability claim. No GBA password list,
button-code list or debug-menu code exists on any of them.

## 6b. Enumeration

**Space definition.** There is no code system in this build. Stated exactly:

* Alphabets: **none**. No character set is read from the player anywhere.
* Lengths: **none**. No length check exists (no `strlen`→`cmp` path on input).
* Checksums / bitfields / reserved bits: **none**.
* Tables: **0** password/button tables. The number of representable codes is
  **0**.
* Entry points: **0**. The only password-like screen in the sibling title
  (*Backyard Basketball*) does not exist here.

**Search space actually covered (counts over the whole 4,194,304-byte file).**

| Search | Space | Result |
|---|---|---|
| `strings -t x -n 4` | 37,794 ASCII strings | inventory |
| `password`, `passcode`, `pass word` | case-insensitive, whole file | **0 / 0 / 0** |
| `cheat`, `cheats` | whole file | **0 / 0** |
| `unlock`, `hidden`, `bonus`, `extras`, `level select`, `sound test` | whole file | **0** each |
| `secret` | whole file | **0** (Pablo's nickname `SECRET WEAPON` is tile-drawn, not ASCII) |
| `debug` | whole file | **1** (`Debug Screen`, `0x7D57C`) |
| `code` | whole file | **2**, both commentary prose (`0x3EF268`, `0x3EF46F`) |
| NUL-delimited pure-lowercase tokens len 3–12 | whole file | **435**, all graphics/text noise; 3 are in the button alphabet (`vvv`, `mam`, `tsd`) and none is a table |
| Basketball-style 17 × 10 table footprint at file `0x133E90` | 170 bytes | `uudda` etc. **absent**; region is graphics |
| `uudda`, `UUDDA`, UTF-16, u16-mask variants of the four Basketball codes | whole file | **0** each |
| Any run of ≥5 `u16` key masks (`1,2,4,8,10,20,40,80,100,200`) | every 2-byte offset | **2**, both 5–6 entries and not code tables (`0x89390`, `0x257F28`) |
| `u32` pointer to the debug root (even/odd) | whole file | **0** |
| Thumb `BL`/`BLX` to the debug root | every 2-byte offset | **0** |
| Ghidra callers of the debug root | complete | **0** |
| `u32` pointer into the debug label array page | whole file | **0** |
| PC/Mac/GameCube code literals (§6.3) | whole file, case-insensitive | **0** each |

**Dynamic bounds.**

* GDB stub on `:2345` with breakpoints at `0x080055F0`, `0x080056F4`,
  `0x08005854`, `0x08005978`; control breakpoint at `0x0806ECE0` fired
  every frame (proving the mechanism works). During boot, title, main menu,
  every submenu, the Pickup matchup (including the four Basketball sequences)
  and the in-game pause, the debug breakpoints fired **0 times**.
* Savestate RAM diff: baseline at the matchup screen vs after
  `Up Up Down Down Up Up Down Down`: no new lowercase run anywhere in IWRAM or
  EWRAM; the 32 bytes sampled at `0x030007F0` (the Basketball recorder buffer)
  are all `0x00` before and after. There is no button-letter history to match
  against.

**"Novel input" equivalent.** The unpublished content is the debug module.
It is proven unreachable rather than merely undocumented:

| Attempt | Why it is out of bounds | Observed |
|---|---|---|
| 14 button-combination attempts (5 distinct), including `L+R+Start+Select` | the debug module has no caller/reference | screen never changes; BP never fires |
| Use a PC/Mac code as a name | no text entry; nickname is a fixed list of 232 names | only LEFT/RIGHT cycling; literal absent from ROM |

Because there is no validator, there is no in-game "accept/reject" event to
report. The equivalent bound is structural: **the module has zero incoming
edges** (BL 0, BLX 0, `u32` pointer 0, Ghidra callers 0), so no sequence of
inputs can reach it, and the GDB run confirms no hit while every reachable
screen is exercised.

**What *is* novel in this report (not on GameFAQs/TCRF).** TCRF documents the
debug *text* at `0x7D520`; this report adds the module's address map
(`0x080055F0` root, `0x080056F4` dispatcher, `0x08005854`/`0x08005978` pages,
`0x0803F9E58` label array), the exact entry list and effects, and the proof
that no instruction, literal or table in the retail build reaches it. That is
the defensible answer to "is there a hidden menu?" for this exact ROM.

**Unlockables (not code-driven).**

| Content | Evidence | State on a fresh save |
|---|---|---|
| Pablo Sanchez, card nickname `SECRET WEAPON` | name `0x080843AC`, record `0x0808544C`, card browser | card visible; **not** in the observed Player Select cycle |
| Dirt Yards stadium | Field Select / pickup stadium list | selectable (observed) |
| Published trigger | "Beat the game on any difficulty" (fan lists) | play-through, not an input code |

The Player Select `"?"` portrait is the `Custom Player` entry (pressing A on it
opens the CUSTOM PLAYER editor, `m2_c.png`), not a locked card.

## 7. Validation evidence

**Observed (emulator — screenshots in `/tmp/opencode/bf/`):**

* Boot sequence and title (`bootgrid.png`), main menu (`t21_c.png`), every
  submenu listed in §3, options (`u4_c.png`), difficulty (`s2_c.png`), matchup
  (`s06_pickup2_c.png`, `s22_c.png`), commentary (`y9_c.png`), play
  (`s09_c.png`), pause (`s20_c.png`), Time Out Options (`q1_c.png`), Team
  Select (`s24_season3_c.png`), Field Select (`t04_c.png`), Leather Or Laces
  (`t05_c.png`), practice setup (`t28_c.png`), multiplayer wait (`t31_c.png`),
  player cards (`t33_c.png`), credits (`t51_c.png`), season menu
  (`s11_c.png`), custom player editor (`m2_c.png`), skill points (`m3_c.png`).
* Player Select pool: 41 `DOWN` steps from Achmed cycled a 14-name set —
  Achmed Khan, Annie Frazier, Brett Favre, Donovan McNabb, Jeff Garcia,
  Jocinda Smith, Kiesha Phillips, Luanne Lui, Michael Vick, Pete Wheeler,
  Rich Gannon, Ronny Dobbs, Stephanie Morgan, Vicki Kawaguchi — plus
  `Custom Player`; Pablo Sanchez was not among the names shown
  (`k5`–`k10`, `selnames.png`).
* No typed-name screen exists in any of the above paths.
* Breakpoints: control `0x0806ECE0` hit per frame; debug BPs never.

**Derived (disassembly / Ghidra):**

* Debug module boundaries, string references and dead-code status (§4.1).
* Input edge detector and absence of an ASCII recorder (§5.3).
* Roster/name/record tables and Pablo's record (§4.3).
* Search counts (§6b).

**Inferred:**

* Pablo Sanchez is the developer-unlockable player named in the published
  lists: his card and record exist, but the fresh-save Player Select pool does
  not offer him. The unlock trigger is a play-through, not an input.
* The NFL-player records (Brett Favre, Donovan McNabb, Jeff Garcia, Michael
  Vick, Rich Gannon) are part of the same pool; how the pool is assembled per
  team was not traced.

## 8. Unknowns

* The exact save-byte flags that a completed play-through would set (the fresh
  512-byte EEPROM contains only a checksum).
* How the per-team Player Select pool is assembled from the 41 record-table
  entries; the observed 14-name cycle is evidence, not a derivation.
* Why the debug module was linked into the retail build: most likely the same
  Torus engine source built without the developer-entry define; the binary
  contains no gate or reference, so this is not testable inside the ROM.
* Whether a debug-build variant of AYFE had the module wired to the pause menu
  (plausible, but not present here).

## 9. Tooling

* `Xvfb :157`, `openbox`, `mgba 0.10.5` (SDL), `xdotool`, `scrot`,
  ImageMagick, `arm-none-eabi-objdump` (binutils-arm-none-eabi),
  `gdb-multiarch` (mGBA GDB stub on `:2345`), Python 3 (`zlib`, `struct`,
  Capstone), Ghidra 12.1.4 via the REA MCP provider.
* Scripts (all in `/tmp/opencode/bf/`): `keys.py` / `combo.py` (xdotool key
  driver with hold/release), `shot.sh` (scrot + 720×480 crop), `state.py`
  (mGBA `gbAs` zlib savestate reader with `0x03/0x02` address mapping),
  `dbg.gdb` / `test2.gdb` (breakpoint scripts).
* Savestates: `Backyard Football.ss1` (pickup matchup), `.ss2`–`.ss6`
  (scratch/diffs).
* Screenshots: `/tmp/opencode/bf/*.png` (cropped `*_c.png`), notably
  `bootgrid.png`, `t21_c.png`, `u4_c.png`, `s2_c.png`, `s06_pickup2_c.png`,
  `s20_c.png`, `q1_c.png`, `s24_season3_c.png`, `t33_c.png`, `k6_c.png`,
  `m2_c.png`.

**Legal:** no ROM, graphics, music or extracted text is redistributed here;
only hashes, addresses, algorithms, counts and my own console strings.
