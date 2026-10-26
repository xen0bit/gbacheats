# Backyard Football 2006 (GBA) — Reverse Engineering Report

Status: complete. Scope: in-game / developer-intended cheats only (passwords, button
codes, hidden/debug menus, unlockables). No GameShark, CodeBreaker, Action Replay or
other memory-edit codes are proposed or relied on.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Backyard Football 2006/Backyard Football 2006.gba` |
| Size | 4,194,304 bytes (0x400000, 32 Mbit) |
| Header title | `BYF 2006` |
| Game code | `BYFE` |
| Maker code | `70` |
| Software version | `0x00` |
| Entry branch (0x00) | `0xEA000030` → `0x080000C0` |
| Fixed header byte 0xB2 | `0x96` |
| MD5 | `ea7d981e25ac274adaf5ed08f505c60b` |
| SHA-1 | `53d134268d2fc973388861687e50f77cc4682941` |
| SHA-256 | `ff121d81cf5608b4522fdb11a1090a813c127d3ccfea14656ecb4ab737c7e5cf` |

Embedded-header scan: the whole image was searched for the exact 156-byte Nintendo
logo (`24 ff ae 51 …`, bytes at file `0x04`–`0x9F`). Exactly **one** occurrence was
found, at file `0x04`. This is a single-image cartridge, not a multi-game pack.

Header-integrity caveat: the stored complement check at `0xBD` is `0xFB`; the value
computed from bytes `0xA0`–`0xBC` is `0xF7`. The stored 16-bit header checksum at
`0xBE` is `0x0000`. The image therefore has a modified/invalid GBA header even
though it boots (mGBA ignores these fields). All addresses and hashes below are for
the exact SHA-256 above.

Build identification: the engine debug screen prints `Built: Jun  2 2005` and
`Host:  scameron` (ROM `0x084B1C`, `0x084B30`); the credits name Torus Games as
the developer. The game credits list "Managing Director Bill McIntosh / Producer
Greg Palstra / Lead Programmer Michael Abbott". The retail GBA release date was
Oct 18, 2005, so this is a mid-2005 build; the invalid header is consistent with a
patched/padded dump (see §8).

## 2. Executive summary

**Backyard Football 2006 (GBA) contains no in-game cheat, password, button-code or
reachable debug-menu system.** Four candidate mechanisms were checked end to end,
and all four are absent:

1. **Season coach-name codes (the Backyard Baseball 2006 mechanism).** The football
   title has a season-coach concept — a `Coaches Sign In` screen with
   `CONTINUE SEASON` / `CREATE NEW COACH` and an overwrite confirmation — but it
   **has no name-entry screen and no name field**. `CREATE NEW COACH` goes straight
   to `Difficulty Level`, then field/team/roster setup. The 512-byte EEPROM save
   contains an 80-byte season struct with no name bytes anywhere. A 4 MiB search for
   the baseball encoding (`ASCII-0x21`, `0x5E` terminator) and for fixed-slot ASCII
   name tables both return nothing usable (2 accidental runs in the strict A–Z/0–9
   form; the broad byte form yields 196 runs, none a table), so
   the nine baseball codes and the older `Walter Payton` coach-name trick have no
   entry surface here.

2. **Unlockables.** There is no unlock storage: the entire EEPROM image is 512 bytes,
   only the 8-byte ID/magic area and the 80-byte block at `0x1B0`–`0x1FF` are ever
   non-zero after play, and there is no name or flag field beyond the season struct. The
   15 stadiums split into compile-time per-mode lists (7 in Season, 8 in Exhibition,
   10 distinct, 5 never selectable), and the 12 Backyard team names are fixed data.
   The three stadium "unlockables" on GameFAQs (`Aquadome`, `Humongous Memorial
   Stadium`, `Quantum Field`) belong to Backyard Baseball 2006 — those strings do
   not exist anywhere in this ROM.

3. **Button codes.** The engine exposes one input word (`pressed` at `0x03000E68`,
   `held` at `0x03000E66`). A scan of the whole code region for contiguous 16-bit
   key-mask sequences (length ≥ 4, ≥ 3 distinct masks) finds **0** candidates. The
   only input-driven game flow is ordinary menu navigation. Konami, L+R,
   L+R+Start and a boot-time L+R+Select+Start chord were pressed in the emulator and
   produced only normal navigation.

4. **Hidden/debug menus.** A full engine debug suite survives in the ROM — root
   `Debug Screen` banner at `0x0800554C` with `Systems Menu`, `Performance Menu`
   and `Profiling Menu` sub-screens, plus an `Entity Options` entity menu. The root
   has **zero** references: no 32-bit pointer (normal or Thumb-tagged), no Thumb
   `BL`, no ARM `BL` anywhere in the 4 MiB, and its menu table at `0x083CB788` is
   also unreferenced. It is dead developer tooling.

Because there is no code surface at all, the "enumeration" deliverable is a
proof of absence: 31 screen states walked, 4 MiB of text and code searched with
counts, and every published input checked against the ROM or its only possible
entry point. Details and counts are in §6b.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL frontend), headless Xvfb. The binary on this host is
`/usr/games/mgba`. Display `:156` (1024×768×24) with `openbox`; screenshots with
ImageMagick `import -window root`.

```
Xvfb :156 -screen 0 1024x768x24 &
DISPLAY=:156 openbox &
DISPLAY=:156 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 "Backyard Football 2006.gba" &
```

Default mGBA SDL keymap used throughout:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| Start | `Return` |
| Select | `BackSpace` |
| L / R | `a` / `s` |
| D-pad | arrow keys |

Hold keys 150–250 ms. The reset hotkey (Ctrl+R) takes about 12 s to return to the
title on this host; wait for `PRESS START` before sending input, otherwise presses
are consumed by the logo screens.

### 3.1 Menu paths used

* Title → **Start** → Main menu (`PICKUP GAME`, `EXHIBITION`, `SEASON PLAY`,
  `PRACTICE`, `MULTIPLAYER` (greyed), `OPTIONS`, `PLAYER CARDS`, `CREDITS`).
* `SEASON PLAY` → `Coaches Sign In` (`CONTINUE SEASON` / `CREATE NEW COACH`) →
  `Difficulty Level` → `Select Home Field` → `Team Select` (Frontyard / Backyard
  conferences) → `Pick Players` → player card `PICK ME? YES/NO` → `Team Photos` →
  `Season Menu` (`BEGIN SEASON`, `LEAGUE STANDINGS`, `TEAM STATISTICS`,
  `TEAM STRATEGY`, `OPTIONS`, `QUIT GAME`).
* `SEASON MENU → TEAM STRATEGY` → `Time Out Options` (four playbook pages).
* `BEGIN SEASON` → matchup preview → commentary → gameplay → play call (`Start`) →
  pause (`RESUME` / `QUIT`).
* `EXHIBITION` → `Difficulty Level` → `Select Field` (SUN/RAIN) → `Leather Or Laces`
  coin toss → `Pick Players` (2-player `PLEASE WAIT FOR OPPONENT`).
* `PICKUP GAME` → `Difficulty Level` → (random field/teams) → matchup.
* `PRACTICE` → `Use saved game?` (`YES` resumes; `NO` → new-coach overwrite
  confirmation) → `Coaches Sign In` → `Difficulty Level` → `Team Select` → setup.
* `OPTIONS` (three toggles: Music, Commentary, Auto-save) and `PLAYER CARDS`
  (35 cards, L/R = PREV/NEXT) and `CREDITS` (Torus Games).

### 3.2 Exact path to the coach screen and what it does

1. Boot, press **Start**.
2. Main menu: **SEASON PLAY** (cursor starts there) → **A**. With a save present
   this opens `Coaches Sign In`; with no save it goes straight to `Difficulty Level`.
3. Choose **CREATE NEW COACH** → **A** → `Creating a new coach will overwrite your
   saved game.` / **YES** (the left button; yellow highlight defaults to `NO`) →
   **A**.
4. The game goes directly to `Difficulty Level`. There is **no name prompt at any
   point**, and `Pick Players`/`Team Photos`/`Season Menu` follow without one.

Screenshots: `shots/98_coach.png` (sign-in menu), `shots/99_createnew.png`
(overwrite confirm), `shots/102_after.png` (still the menu after `YES` on the wrong
button), `shots/103_yes.png` (YES selected), `shots/104_name.png` (result:
`Difficulty Level`, not a keyboard).

### 3.3 Absence tests performed in the emulator

| Test | Where | Result |
|---|---|---|
| Select (`BackSpace`) | main menu | tutorial info panel only (`shots/84_info.png`) |
| Konami `Up Up Down Down Left Right Left Right B A` | main menu | normal cursor movement + normal advance (`shots/87_konami.png`) |
| Hold L+R | main menu | no change (`shots/85_lr.png`) |
| Hold L+R+Start | main menu | normal `PICKUP GAME` entry (`shots/86_lrstart.png`) |
| Hold L+R+Select+Start | title/boot | normal `PICKUP GAME` entry (`shots/110_bootcombo2.png`) |
| `MULTIPLAYER` | main menu | greyed; D-pad skips it, `A` cannot open it |
| Options extra row | Options | three rows only; Down from Auto-save wraps to Music (`shots/95_opt4.png`) |
| `PICKUP GAME` with `A` ×2 | difficulty | jumps to random matchup (no team/field pick) |
| `PRACTICE` → `Use saved game?` `NO` → `CREATE NEW COACH` | practice | overwrite confirm → `Difficulty Level`; no name prompt |

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`.

| Item | ROM address | File offset | Notes |
|---|---:|---:|---|
| Cartridge entry | `0x080000C0` | `0xC0` | ARM |
| Font charset tables | `0x0833A719`, `0x0833B601`, `0x083C5D49` | `0x33A719`, `0x33B601`, `0x3C5D49` | `0x19`–`0x5E` glyph ordering |
| Commentary text bank | `0x083BD590` | `0x3BD590` | ASCII, `SD`/`CD` speaker markers, variable length |
| Stadium name blob (15) | `0x083BF79F` | `0x3BF79F` | concatenated, no separators |
| Team name blob (43) | `0x083BFB84` | `0x3BFB84` | 31 NFL + 12 Backyard names (commentary table), concatenated |
| Player name bank | `0x0808D1F4`–`0x0808DFCC` | `0x8D1F4`–`0x8DFCC` | ASCII, NUL-terminated; starts `Achmed Khan`; contains `Custom Player` at `0x0808D418` |
| Pointer to `Custom Player` entry | `0x0808E544` | `0x8E544` | points at `0x0808D418` |
| Engine debug strings | `0x08084AC8`–`0x08084F3F` | `0x84AC8`–`0x84F3F` | `Options`, `Back`, `Systems Menu`, `Performance Menu`, `Profiling Menu`, `Debug Screen`, `Built: …`, `Host: …`, RAM/entity/frame stats |
| Debug-menu data table | `0x083CB788` | `0x3CB788` | strings `Options … Profiling Menu`, no pointer refs |
| Debug root `Debug Screen` | `0x0800554C` | `0x554C` | prints banner, 4-item menu; **0 xrefs** |
| `Systems Menu` handler | `0x08005650` | `0x5650` | 5 items, only caller is root |
| `Performance Menu` handler | `0x080057B0` | `0x57B0` | only caller is root |
| `Profiling Menu` handler | `0x080058D4` | `0x58D4` | only caller is root |
| Unreferenced check stub | `0x080055C8` | `0x55C8` | **0 xrefs** |
| Entity debug menu | `0x080756B8` | `0x756B8` | `Back` / `Flag for deletion` / `Entity Options:` (`0x083C5838`–`0x083C5861`), engine vtable reachable, not a game menu |
| Input poll (KEYINPUT) | `0x08072B20` | `0x72B20` | `pressed = (KEYINPUT ^ 0x3FF) & ~held_prev` |
| Key state struct | `0x03000E60` (RAM) | — | `+6` held (`0x03000E66`), `+8` pressed (`0x03000E68`) |
| Second key struct (link) | `0x030019D4` (RAM) | — | pressed `0x030019D4`, held `0x030019D8` |
| EEPROM library banner | `0x083C6BD0` | `0x3C6BD0` | `EEPROM_V124` |
| Save image | 512 bytes | — | magic `0x5E2A601C` at save offset 4; state `0x1B0`–`0x1FF` |

### 4.1 Save layout (observed)

Both saves written during this analysis are identical outside the 4-byte checksum
and the season struct:

```
off 0x000: xx xx xx xx 1c 60 2a 5e 00 … 00      (checksum/ID + magic 0x5E2A601C)
off 0x1B0: 11 00 00 00 00 00 00 00  <80-byte season state>
off 0x1FF: … 33 32 31                            (descending trailer)
```

No ASCII name exists in the 512-byte image, and the only non-zero bytes are the
8-byte ID/magic area (`0x000`–`0x007`) and the 80-byte block (`0x1B0`–`0x1FF`).
That is the strongest single argument against a persistent
unlock/cheat flag: there is nowhere to store one beyond the season struct.

## 5. Algorithm

### 5.1 Input pipeline

`0x08072B20` (reset wrapper at `0x08072B44`, call at `0x08072B4E`) reads the
active-low keypad register:

```c
uint16_t raw   = *(volatile uint16_t*)0x04000130;   /* active-low */
uint16_t held  = raw ^ 0x03FF;                      /* active-high */
uint16_t prev  = *(uint16_t*)0x03000E66;
*(uint16_t*)0x03000E68 = held & ~prev;              /* newly pressed */
*(uint16_t*)0x03000E66 = held;
```

Bit values are the standard GBA ones: A=0x001, B=0x002, Select=0x004, Start=0x008,
Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200. Only four literal
loads of `0x04000130` exist in the ROM (`0x080208F2`, `0x08072B20`, `0x08073A5A`,
`0x08073B10`); game code consumes the RAM word, not the register.

### 5.2 Coach/profile flow

```
main menu -> SEASON PLAY
  -> "Coaches Sign In"
       CONTINUE SEASON   -> load EEPROM season, go to Season Menu (or resume game)
       CREATE NEW COACH  -> confirm overwrite -> Difficulty Level -> field ->
                            team -> roster -> Team Photos -> Season Menu
```

There is no character buffer, length byte, alphabet table or comparator anywhere in
that path. The save struct is fixed-width; creating a "new coach" simply rewrites
`0x1B0`–`0x1FF`.

### 5.3 Why the accepted-code set is empty

For a code system to exist, the game needs (a) an input surface that collects
characters or a button sequence, (b) a comparison/decoder, and (c) an effect. None
of the three exists:

* no screen in the walk accepts characters (the only text-like prompt is the
  YES/NO overwrite confirmation);
* no fixed-slot or NUL/`0x5E`-terminated code table exists (§6b.3);
* no contiguous key-mask sequence exists in the code region;
* the engine debug menus that could have been the effect are unreachable.

### 5.4 Search procedure used for the negative result

1. `strings -t x -n 4` over the whole image (39,894 strings).
2. Case-sensitive `count()` for 25 case/variant probes (23 unique terms) of
   cheat-related keywords (all zero except `Debug`).
3. Baseball-style table scan: runs of `ASCII-0x21` terminated by `0x5E`.
4. Fixed-slot ASCII table scan: ≥ 4 equal-length NUL-terminated strings with a
   constant stride (0–4 pad bytes) anywhere in the image.
5. Named-pointer-array scan: arrays of 5–12 u32 pointers to equal-length uppercase
   NUL-terminated strings (the exact shape of the baseball coach-name table).
6. Thumb/ARM `BL`/`BLX` and 32-bit pointer scans for the debug root and its
   sub-menus.
7. Contiguous key-mask run scan (u16) restricted to the code region
   `0x000000`–`0x085000`.
8. Emulator walk of every menu state plus four button-combination tests.

## 6. Tables

### 6.1 Stadiums (15; 10 player-selectable)

The 15 names are one concatenated ASCII blob at `0x083BF79F`. The Season and
Exhibition lists were both cycled to the wrap point in the emulator.

| Stadium | Season list | Exhibition list | Observed use |
|---|---|---|---|
| Cactus Gulch | yes (index 0) | no | season home field |
| Zoo | yes | yes | both |
| Sandy Flats | yes | yes | both |
| Drive In | yes | yes | both |
| Chinatown | yes | yes | both |
| Airport | yes | yes | both |
| Tropical Gardens | yes | no | season |
| Dmitri Dome | no | yes (index 0) | exhibition; CPU home |
| Dirt Yards | no | yes | exhibition |
| Phillips Phield | no | yes | exhibition; CPU home |
| Emerald Lakes Marina | no | no | commentary only |
| GigantiCorp King-Size Dome | no | no | commentary/story (Cereal Bowl) |
| Metro Civic Playgrounds | no | no | commentary only |
| Playground Commons | no | no | commentary only |
| Rocky Vista | no | no | commentary only |

Screenshots: `shots/m_f1.png`–`shots/m_f3.png` (Season, 7 entries, wraps after
Tropical Gardens), `shots/m_ef1.png`–`shots/m_ef2.png` (Exhibition, 8 entries,
wraps after Phillips Phield). The GameFAQs "unlock" names `Aquadome Stadium`,
`Humongous Memorial Stadium` and `Quantum Field` are **not in this ROM**
(`grep -abo` = 0 hits for each), so that published table is Backyard Baseball 2006
content pasted onto the football page.

### 6.2 Backyard team names (12 in data)

`0x083BFB84`, concatenated:

`Cheezy Blitz`, `Flea Flickers`, `Fumble Bees`, `Humongous Melon Heads`,
`Labrador Receivers`, `Lime Backers`, `Passing Pirates`, `Potato Sackers`,
`Rushing Rhinos`, `Slimy Geckos`, `TD Rexes`, `Turf Herders`.

`Team Select` contains 40 slots (2 conferences × 4 rows × 5 columns): 32 NFL
franchise entries plus **8** mascot teams in the fifth column. The eight observed
in Team Select were `Rushing Rhinos`, `Cheezy Blitz`, `Potato Sackers`,
`Humongous Melon Heads`, `Turf Herders`, `Fumble Bees`, `Lime Backers` and
`Flea Flickers` (`shots/m_front.png`, `shots/m_back.png`). The remaining four names
still appear in the text bank and can serve as CPU/season teams; they were not seen
as player-selectable entries. They are data/CPU teams, not unlockables (§8).

### 6.3 Player cards (35, no locked slots)

`Player Cards` cycles alphabetically and wraps with no greyed, `?` or silhouette
entry:

1 Achmed Khan, 2 Ahman Green, 3 Amir Khan, 4 Angela Delvecchio, 5 Annie Frazier,
6 Ashley Webber, 7 Brian Urlacher, 8 Dante Robinson, 9 Daunte Culpepper,
10 Dmitri Petrovich, 11 Donovan McNabb, 12 Ernie Steele, 13 Jocinda Smith,
14 Kiesha Phillips, 15 Kimmy Eckman, 16 LaDainian Tomlinson, 17 Lisa Crocket,
18 Luanne Lui, 19 Maria Luna, 20 Marky Dubois, 21 Marvin Harrison,
22 Matt Hasselbeck, 23 Michael Strahan, 24 Michael Vick, 25 Pablo Sanchez,
26 Pete Wheeler, 27 Peyton Manning, 28 Priest Holmes, 29 Reese Worthington,
30 Ricky Johnson, 31 Sidney Webber, 32 Tom Brady, 33 Tony Delvecchio,
34 Tony Gonzalez, 35 Torry Holt.

Screenshots: `shots/m_pc1.png`, `shots/m_pc2.png` (name crops for all 35 plus the
wrap back to Achmed Khan).

### 6.4 Dead engine debug menus

| Entry | Address | Items | Status |
|---|---|---|---|
| `Debug Screen` root | `0x0800554C` | Systems / Performance / Profiling (+ Back) | 0 refs |
| `Systems Menu` | `0x08005650` | 5 items (RAM stats, message system, entity allocator, frame rate, …) | only caller root |
| `Performance Menu` | `0x080057B0` | engine timing | only caller root |
| `Profiling Menu` | `0x080058D4` | system timer table | only caller root |
| `Entity Options` | `0x080756B8` | Back / Flag for deletion / Entity Options | engine vtable only |

The debug root's menu table at `0x083CB788` holds the strings
`Options`, `Back`, `Systems Menu`, `Performance Menu`, `Profiling Menu`, `Back`,
`Slow RAM`, `Fast RAM`, `Message System`, … and has no pointer references.
`0x080055C8` (an unreferenced helper) is likewise dead.

### 6.5 Published inputs and their verification status

| Published input | Source | Verification | Result |
|---|---|---|---|
| `BABYBEAR` … `ATLANTIS` (9 coach names) | Backyard Baseball 2006 (sibling product) | literal search in football ROM | Not present (0 hits for both plain and `ASCII-0x21`/`0x5E` forms); no name-entry surface |
| `Walter Payton` as coach name | GameFAQs, original Backyard Football (GBA, 2002) | only possible entry point (`Coaches Sign In → CREATE NEW COACH`) | No name prompt; flow goes to `Difficulty Level` |
| `MRCLANKY` (Dummies Team) | GameFAQs, Backyard Football (PC) | same entry point | Same: no input surface |
| `Aquadome Stadium` | GameFAQs GBA 929549, archived 2016-09-02 | ROM string search | Not in ROM (0 hits); table is baseball data |
| `Humongous Memorial Stadium` ("Go to the Playoffs") | same | ROM string search + stadium lists | Not in ROM; no such stadium in either list |
| `Quantum Field` ("Win a Championship season") | same | ROM string search + save-size analysis | Not in ROM; no unlock storage exists |

GameFAQs' own metadata says "3 cheat codes and secrets"; the archived page contains
exactly those three *unlockable* rows and no code entry.

## 6b. Enumeration

### 6b.1 Space definitions

| Candidate system | Alphabet / unit | Length | Space | Accepted values |
|---|---|---|---|---|
| Coach-name codes | no input surface | — | 0 | **0** |
| Alphanumeric password | no keyboard screen in any of the 31 states | — | 0 | **0** |
| Button sequence | 10 buttons (A,B,Select,Start,Right,Left,Up,Down,R,L), active-high masks | any | 2^10 per frame; sequence space unbounded | **0 tables found** |
| Debug menu | — | — | 5 engine menus | **0 reachable** |
| Unlock flags | — | — | 512-byte EEPROM, 80-byte struct | **0 flags present** |
| Fixed-slot name table | ASCII, len 4–12, stride 5–16 | ≥4 entries | scanned 4 MiB | **0 tables** |
| `ASCII-0x21`/`0x5E` table | 0x20–0x39 + terminator | ≥4 chars | scanned 4 MiB | **2 accidental runs** (`YCSGCCCOCCC`, `CCCFFCCF`), neither a table |

The accepted set is therefore empty: there are no "valid" inputs to enumerate, and
no code can be minted because no decoder exists.

### 6b.2 Novel codes

None. There is no code to generate and no screen at which to enter one. The
nearest positive deliverables are the **content enumerations** that a code system
would normally bypass:

* all 15 stadiums and their per-mode availability (§6.1);
* all 35 player cards, in order, with no locked entry (§6.3);
* the 12 Backyard team names and the 8 that are selectable (§6.2);
* the 5 dead developer menus and their item lists (§6.4).

### 6b.3 Bounds proven by rejection / absence

| Bound | Probe | Count / result |
|---|---|---|
| No password/cheat keyword anywhere | case-sensitive `count()` on 25 case/variant probes (23 unique terms) over 4,194,304 bytes | 0 for `password`, `PASSWORD`, `cheat`, `CHEAT`, `code`, `CODE`, `secret`, `SECRET`, `unlock`, `UNLOCK`, `un-lock`, `Un-lock`, `coach`, `COACH`, `debug`, `DEBUG`, `manager`, `Manager`, `enter name`, `ENTER NAME`, `name entry`, `test`, `Test`; 1 for `Debug` (`Debug Screen`) |
| No fixed-slot name/code table | ASCII, ≥4 equal-length NUL strings, stride len+1…len+5, whole ROM | **0** |
| No baseball-style encoded table | `ASCII-0x21` + `0x5E`, ≥4 chars, whole ROM | **2** runs, both 5+ non-code garbage |
| No coach-name pointer array | 5–12 u32 pointers to equal-length uppercase NUL strings | **0** (the only equal-length pointer arrays are the engine profiling labels `AI_SYSTEM`, `Z_ORDERER`, … at `0x5A10`) |
| No button-code table | contiguous u16 masks, ≥4 entries, ≥3 distinct, code region `0x0`–`0x85000` | **0** |
| No debug-menu reachability | 32-bit normal/Thumb pointer + Thumb BL + ARM BL scans for `0x0800554C`, `0x08005650`, `0x080057B0`, `0x080058D4`, `0x080055C8` | **0** (sub-menus have only the root as caller) |
| No unlock storage | 512-byte EEPROM image after play | only `0x000`–`0x007` and `0x1B0`–`0x1FF` non-zero; no name bytes |
| No hidden options row | Options screen, 4× Down | cursor wraps after Auto-save |
| No multiplayer entry | greyed item | D-pad skips; A cannot open |
| No button combo | Konami / L+R / L+R+Start / L+R+Select+Start | normal navigation only |

These are two-sided bounds: the *format* cannot be expressed (no alphabet, no
keyboard, no mask table) and the *effect* cannot be reached (debug code has no
xrefs; no flags are stored).

### 6b.4 Screens walked (31 states)

Title / legal, main menu, main-menu info, difficulty, Season home field (7),
Exhibition field (8) + SUN/RAIN, coin toss (`Leather Or Laces`), team select
(both conferences, 40 slots), team info, pick players (scroll top→bottom),
player-card `PICK ME?`, team photos, season menu, league standings, team
statistics, time-out options, options, quit-game, quit-and-save confirm,
quit-without-save confirm, coaches sign-in, overwrite confirm, practice
`Use saved game?`, pre-game commentary, matchup preview, gameplay, play call,
pause (`RESUME`/`QUIT`), player cards (35), credits, `PLEASE WAIT FOR OPPONENT`.

## 7. Validation evidence

**Observed (emulator screenshots / direct file reads)**

* SHA-256/MD5/SHA-1 and header fields read from the file; single Nintendo-logo hit
  at `0x04`.
* `Coaches Sign In` → `CREATE NEW COACH` → overwrite `YES` → `Difficulty Level`,
  with no name screen (`shots/98_coach.png` … `shots/104_name.png`).
* All 7 Season stadiums and all 8 Exhibition stadiums cycled to the wrap point.
* All 35 player cards cycled; wrap from Torry Holt to Achmed Khan.
* Options has exactly 3 rows; `MULTIPLAYER` is skipped by navigation.
* Konami, L+R, L+R+Start and boot-time L+R+Select+Start produced normal navigation
  only.
* EEPROM image is 512 bytes; only `0x000`–`0x007` and `0x1B0`–`0x1FF` ever hold
  non-zero data.

**Derived (instruction/table analysis)**

* Input is centralised: `pressed = (KEYINPUT ^ 0x3FF) & ~held_prev` at
  `0x08072B20`; only four `0x04000130` literal loads exist.
* The debug suite root `0x0800554C` and gate stub `0x080055C8` have zero
  references (pointer, Thumb BL, ARM BL); the `Systems`/`Performance`/`Profiling`
  handlers are called only from the root.
* The debug menu table at `0x083CB788` has zero pointer references.
* Zero fixed-slot ASCII tables and zero equal-length code-pointer arrays exist.
* The 23-unique-term keyword count is zero for every cheat-related term.

**Inferred**

* The five always-unselectable stadiums are story venues (GigantiCorp is named in
  commentary as the Super Colossal Cereal Bowl), not unlockables.
* The four Backyard names that are not in Team Select are CPU/league teams; they
  are never player-selectable in the menus walked.
* The `Custom player` label at `0x0808A9E0` belongs to a removed create-a-player
  feature: its string is pointed to only by `0x083CB7F0`, which has zero
  references.
* The invalid header checksum/complement indicate this image was patched or padded
  after mastering; mGBA boots it regardless.

## 8. Unknowns

* Whether a prototype/dev cartridge of this build wires the `Debug Screen` /
  `Entity Options` menus to a key gate. In this image they have no caller.
* Whether finishing a season changes the stadium list. No per-stadium flag byte
  exists in the 512-byte image: only 73 bytes are ever non-zero, all inside the
  8-byte ID/magic area and the 80-byte season block, and the Season/Exhibition
  lists are fixed 7/8-entry sets. No unlock path was found in code or data.
* The exact 4 Backyard team names that are never player-selectable. By elimination
  against the 12-name bank and the observed Team Select set they are
  `Labrador Receivers`, `Passing Pirates`, `Slimy Geckos` and `TD Rexes`; two of
  the eight divisions were read directly from League Standings.
* The purpose of the 80-byte season struct's individual fields.
* Whether the retail Oct-2005 GBA ROM differs from this Jun-2005 build (all
  findings are for SHA-256 `ff121d81…c7e5cf`).

## 9. Tooling

* mGBA 0.10.5 SDL (`/usr/games/mgba`), `-3`, `SDL_AUDIODRIVER=dummy`.
* Xvfb `:156` (1024×768×24) + openbox; `xdotool` for input; ImageMagick `import`
  / `convert` / `montage` for screenshots and contact sheets.
* Python 3: `phase0.py` (hashes/header/logo scan), `strings -t x` dumps,
  `audit.py` (keyword counts, encoded/fixed-slot table scans, u16 mask runs,
  xrefs), `scan_buttons.py`, `scan_enc.py`, `keyinput_scan.py`,
  `key.py`/`chord.py` (input helpers).
* `arm-none-eabi-objdump` + Capstone for the debug-menu and input routines.

Key artefacts live in `/tmp/opencode/bf2006`: `shots/` (numbered screenshots and
the `m_*.png` contact sheets), `strings4.txt`, `sav_with_season.bin` and `bf.sav`.

## 10. Reproduction checklist

- [x] Hash/header the ROM; exact SHA-256 recorded; single-image logo scan.
- [x] Record the patched header fields (complement/checksum).
- [x] `strings` recon and keyword classification (23 unique terms, 1 debug hit).
- [x] Web search + archived GameFAQs page; all published inputs checked.
- [x] Boot on a private display; walk title, main, all modes, options, extras,
      season path, coach sign-in, gameplay, pause, credits.
- [x] Search for the baseball coach-name encoding and fixed-slot tables (0 found).
- [x] Search for button-mask sequences (0 found).
- [x] Locate and prove the engine debug menus unreachable (0 xrefs).
- [x] Test Konami / L+R / L+R+Start / boot chord in the emulator.
- [x] Prove the save has no unlock/name storage.
- [x] Write this report next to the ROM.
- [x] Stop only this session's mGBA/Xvfb/openbox processes by PID.

Legal note: no ROM, extracted graphics, music or other copyrighted assets are
redistributed here. Only hashes, addresses, algorithms, short developer-authored
strings and my own screenshots/notes are published.
