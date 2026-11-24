# Disney's Tarzan: Return to the Jungle (GBA) — Reverse Engineering Report

Scope: in-game / developer-intended cheat surfaces only (passwords, button codes,
hidden or debug menus, unlockables). GameShark / CodeBreaker / Action Replay and
memory edits are out of scope and are only used as *evidence* about what the game
does not contain.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney's Tarzan: Return to the Jungle/Disney's Tarzan: Return to the Jungle.gba` |
| Size | 8,388,608 bytes (8 MiB, 64 Mbit) |
| Header title (0xA0) | `TARZANRTJ` |
| Game code (0xAC) | `AJGE` (USA/Europe) |
| Maker code (0xB0) | `52` |
| Version (0xBC) | 0 |
| Complement (0xBD) | `0x13` (correct: `-(sum(0xA0..0xBC)+0x19) & 0xFF`) |
| Header checksum (0xBE) | `0x0000` — normal artifact of a rebuilt header (§16.1) |
| Entry word (0x00) | `0xEA1FD03E` → `0x087F4100` (**patched**, not the retail `0xEA00002E`) |
| Nintendo logo | exactly one, at file offset 0x4 → single GBA image, no multicart |
| Save type | EEPROM 512 B (mGBA creates a 512-byte `.sav`) |
| MD5 | `ba1c3e81b227b63c2255ca44a6947784` |
| SHA-1 | `8a4da6377496f08861c38fbaa82597e0924c418a` |
| SHA-256 | `2319a06225f7586a5e1ec59de4c703e123c7ca43916555aea548eea49cfbfecc` |

### 1.1 This file is a Mode7 release, not a clean retail image

The entry word branches into an appended cracktro at file `0x7F4100`
(`0x087F4100`), 48,896 bytes of appended block (`0x7F4100..0x7FFFFF`). The last
non-zero game byte before that block is `0x775487`, so the append sits on
padding; no game data appears to be overwritten. Contents:

* `0x087F4100` — ARM stub that mirrors the stock crt0 (IRQ stack `0x03007FA0`,
  SYS stack `0x03007F00`, IRQ vector to `0x087F4154`) and calls
  `0x087FF7CC` (Thumb).
* `0x087FF7CC` — cracktro main. It initialises video/audio, then loops on
  `KEYINPUT (0x04000130) & 8` — i.e. **it waits for START** (verified in code:
  `ldr r0,=0x04000130; ldrh r0,[r0]; movs r1,#8; ands r0,r1; bne loop`).
* On START it executes `SWI 1` with `r0=0xFF` (RegisterRamReset), forces
  `DISPCNT = 0x0080`, and jumps through the literal at `0x087F4624`
  (`= 0x080000C0`) — the real cartridge entry.
* Greetz text at `0x087F41B4..0x087F4623`: `$ MODE7 $ proudly presents: @ Tarzan
  Returns @ 64Mbit \ USA Version (c) Activision ... by: Nick Burns (CCG) ...
  Released on: Oct 24th, 2002 ...`.

Observed on a real boot (screenshot): orange-slice Mode7 logo with the scrolling
credit text above. There is **no trainer menu and no cheat option**; the intro is
a boot-time greetings screen that then hands control to the unmodified game.

For analysis a copy with the stock entry restored (`word0 = 0xEA00002E`, i.e.
`b 0x080000C0`) was used and boots normally (Activision logo → Digital Eclipse
logo → intro → title). The cracktro itself jumps to `0x080000C0`, which is
independent proof that this address is the game's own entry.

The patch is therefore confined to (a) header word 0 and (b) the trailing
0xBF00-byte block. Everything cited below is inside the original image.

## 2. Executive summary

**This title has no in-game code system.** No password screen, no button-code
validator, no hidden/debug menu and no level-select cheat exists in the image.
What exists is a normal menu tree (New Game / Load Game / Options / Movies), a
save-slot editor, a pause menu, and a movie gallery that is unlocked by
collecting in-game secrets.

Evidence, summarised:

* **No password surface.** The whole localized UI label bank was dumped
  (file `0x241F8C–0x2434FF`, 350 strings × EN/FR/DE). It contains no
  `PASSWORD` / `PASSWORT` / `MOT DE PASSE` / `CODE` entry in any language, and
  the string `strings` scan over all 98,691 strings ≥4 bytes finds none either.
  There is no text-entry screen other than the 8-character save *name*.
* **The save name is a label, not a validator** (§16.2b). The name buffer is
  save-slot record `+4` (`0x02036E24`). Its readers are the slot-list renderer,
  the on-screen keyboard editor and the EEPROM serialiser; it is never compared
  against a constant.
* **No button-code table.** Scanning every 2-byte run of key-mask values
  (`1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200`) that is *pointed at by the ROM*
  yields 5 runs of ≥3 entries; all five are data artefacts (palette words,
  graphics, the default-name `"AAA"` literal, and a 1/2/4/8 glyph table), not
  code tables. No code ANDs the key mirror `0x02000B24` with a multi-button mask
  such as `0x300`/`0x3FF`.
* **One unreferenced "Secrets Page".** The label triplet at file `0x715FD0`
  (EN `Secrets Page` @ `0x8242758`, FR `Page Cheat` @ `0x824274C`, DE
  `Cheatseite` @ `0x8242740`) is referenced **nowhere** in the 8 MiB: a byte
  scan for the triplet address finds only its own slot in the label table.
  Every label that the game actually displays has at least one pointer outside
  the table (e.g. `Game Paused` ← `0x0801D1F8`, `Movie Locked` ←
  `0x080003E0`/`0x0800065C`, `Secret Found` ← `0x08020D0A`). The patch test in
  §6b.1 proves the ASCII label bank *is* live, so the missing reference is
  meaningful: a planned secrets/cheat page that was cut before shipping.
* **Published codes are all device codes.** 3rd party cheat indexes
  lists for the GBA SKU contain only CodeBreaker codes (infinite health, unlock
  all movies, "Press Select to skip level", …). None of them is an in-game
  password or button sequence, and the ROM confirms there is no surface to enter
  one. Their existence is consistent with a game that has *no* built-in code
  system.

Deliverable under §0.2 is therefore item 5 (bounded negative): the menu space is
enumerated, the search spaces are counted, and the unused content that does exist
(the cut Secrets page, the unused `TEST 1` level label, the three unused rows in
the pause-menu icon table) is documented with addresses.

## 3. How to reproduce

Environment: Debian, `Xvfb :337 -screen 0 1024x768x24`, `openbox`, `mgba -3`,
`SDL_AUDIODRIVER=dummy`. mGBA SDL keymap used throughout:

| GBA | key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrows |

Keymap verified by act: `x` selects a menu entry, `Return` opens/closes the pause
menu, arrows move the highlight.

### 3.1 Menu path (all observed)

1. Boot → Activision logo → Digital Eclipse logo → intro cut-scene → title
   (`PRESS START`, attract demo behind it).
2. `START` → depends on timing: if the intro/attract is still running the first
   START is consumed; the next START opens the **main menu**:
   `NEW GAME / LOAD GAME / OPTIONS / MOVIES` (4 items, wraparound; there is no
   5th item).
3. `NEW GAME` → **Select Slot To Start** (3 slots: `EMPTY` or `name / n LIVES
   REMAIN / level name`). `A` on a slot → **NAME GAME** keyboard (default name
   `AAA`) → `START` → level 1 (`Teachings of Terk 1`).
4. `OPTIONS` → `SOUND ON, MUSIC ON, B BUTTON RUN, CREDITS, HIGH SCORES` (5 items;
   `Down` from the last wraps to the first — no hidden 6th row). `CREDITS` opens
   the Digital Eclipse credit roll; `HIGH SCORES` opens the score table.
5. `MOVIES` → `MOVIE 1 … MOVIE 5`. `MOVIE 1` plays on a fresh save; selecting a
   locked entry shows the centred message **`MOVIE LOCKED`**.
6. In game: `START` → **`GAME PAUSED`** + level name + `CONTINUE / QUIT` +
   `SCORE`. `QUIT` → confirm dialog `YES / NO` (default `NO`).
7. `GAME OVER` screen after quitting/losing; it returns to the attract/title.

### 3.2 Savestate RAM method (used for every RAM claim)

mGBA `.ssN` files are PNGs with a zlib `gbAs` chunk; decompressing gives 397,312
bytes for a 4 MiB state (this 8 MiB ROM produces the same layout):

```
0x00000 CPU/header   0x01000 VRAM (0x18000)   0x19000 IWRAM (0x8000)
0x21000 EWRAM (0x40000)
```

So `EWRAM[i]` = `state[0x21000 + i]` ↔ address `0x02000000 + i`. Used for every
"RAM-verified" statement below. Savestates are written by `Shift+F1..F10`,
loaded by `F1..F10`.

## 4. Address map

All file offsets; ROM address = `0x08000000 + offset`.

| Offset / address | What |
|---|---|
| `0x0` | header (patched entry word `0xEA1FD03E`) |
| `0x7F4100` (`0x087F4100`) | Mode7 cracktro (ARM stub + Thumb main `0x087FF7CC`) |
| `0x7F4624` | cracktro literal `0x080000C0` (hand-off target) |
| `0x241F8C–0x2434FF` | localized UI label bank, 350 strings (EN/FR/DE) |
| `0x241DC0` | main-menu/audio label pool: `0x087160FC` New Game, `0x08716108` Load Game, `0x08716114` Options, `0x08716120` Movies, `0x0871618C` Sound On, `0x08716198` Sound Off, `0x087161A4` Music On, `0x087161B0` Music Off |
| `0x241EA8` | dialog-label pool: `0x08715FF4` Copy, `0x08716138` Cancel, `0x08716168` Yes, `0x08716174` No |
| `0x241E8C` | literal `"AAA"` (default save name) |
| `0x715A20` | **level table**, 21 records × 0x28 bytes; `+0x00` = name triplet, `+0x08/+0x0C/+0x14/+0x18/+0x1C` = graphics/map pointers, `+0x20/+0x22` = flags |
| `0x715EA4` | **UI label triplet table** (EN,FR,DE per label, 12 bytes each) |
| `0x715FD0` | the unused `Secrets Page` / `Page Cheat` / `Cheatseite` triplet |
| `0x7166F8` + `0x71774C` | dialogue-line pointer arrays (cut-scene lines) |
| `0x241C14–0x24Axxx` | debug/printf bank (`Keychoose=%d menu=%d`, `Pickmovie`, `Resumegame levelnum=%d`, `MOVIES RELOCKED`, `Secret Found`, …) |
| `0x0802695C` | options handler reads the menu id and debug-prints `"Keychoose=%d menu=%d"` |
| `0x0801D120–0x0801D266` | pause-menu draw list; text `Continue` (triplet `0x087161F8`) and `Quit` (`0x08716204`); jump table `0x0801D220` with **5** icon rows |
| `0x08020D0A` | "Secret Found" handler (prints triplet `0x08716048`, bumps a counter) |
| `0x0802848C` | `RELOCK MOVIES` triplet use in the movie module (debug print path) |
| `0x08027E84`, `0x080283A8`, `0x080284B4` | `MOVIES RELOCKED` debug print sites |
| `0x02000B20` (RAM) | UI/menu id byte |
| `0x02000B24` (RAM) | key mirror (u16); 58 read sites |
| `0x02000B0C` (RAM) | UI state word; bit 2 used for highlight colour |
| `0x020020B0+0x67..0x6B` (RAM) | pause-menu icon-row enable bytes (all `0` in every state tested) |
| `0x02036E14` (RAM) | current level index (level 1 = `1` on a new save) |
| `0x02036E20` (RAM) | save-slot array, 24-byte records; name at `+4` (8 chars) |
| `0x0203BE6C` (RAM) | language index (0 = English at boot) |

## 5. Algorithm

There is no validator to reimplement. The cheat-relevant models are:

### 5.1 Menu/state model

```
state_byte  = EWRAM 0x02000B20          ; menu id, read by every screen handler
key_mirror  = u16 EWRAM 0x02000B24      ; active-low copy of KEYINPUT
ui_word     = u32 EWRAM 0x02000B0C      ; bit2 = "highlight/dim" flag

each screen handler:
    if (key_mirror & UP)    idx = (idx == 0) ? last : idx-1
    if (key_mirror & DOWN)  idx = (idx == last) ? 0 : idx+1
    if (key_mirror & A)     dispatch(idx)
    if (key_mirror & B)     back()
```

Screen handlers never test L (`0x200`), R (`0x100`) or Select (`0x4`) for
navigation, and no site combines key bits into a multi-button mask.

### 5.2 Unlockable model (movies)

* 5 movies, drawn as `"Movie" + ' ' + itoa(n+1)` from triplet `0x087162E8` and
  the space literal `0x08241DFC` (`0x08026E5E–0x08026EB8`).
* A fresh save has movie 1 playable and movies 2–5 reporting `MOVIE LOCKED`
  (observed). The unlock state is part of the save/EEPROM payload, i.e. the
  classic save-bit unlock described in §16.18, not an input code.
* The movie module also contains a developer **relock** path that prints
  `MOVIES RELOCKED` (`0x08027E84`) and has a `RELOCK MOVIES` label
  (`0x0802848C`). No caller reachable from controller input was found for it.

## 6. Tables

### 6.1 Level table (`0x715A20`, stride 0x28, 21 entries)

| # | Name (EN) |
|---|---|
| 0 | Teachings of Terk 1 |
| 1 | Jungle Gym |
| 2 | Top Of The Jungle |
| 3 | Jungle Pursuit |
| 4 | Swimming Lessons |
| 5 | Rescue Terk |
| 6 | Teachings of Terk 2 |
| 7 | Tree Village |
| 8 | Into The Ruins |
| 9 | Lost City Of Opar |
| 10 | Temple Of Queen La |
| 11 | Find Jane |
| 12 | Above The Trees |
| 13 | Unwelcome Visitors |
| 14 | Tarzan's Perilous Path |
| 15 | Into The Depths |
| 16 | Shipwreck |
| 17 | Ancient Railway |
| 18 | The Path To Pellucidar |
| 19 | Pellucidar |
| 20 | Save The Eggs |

`0x715D68` (immediately after the table) holds the triplet for a **22nd label,
`TEST 1`** (`0x824244C`, all three languages), plus `help` (`0x8242454`). No
level record references it: the table ends at index 20. It is a leftover test
level label.

### 6.2 Key-mask set used by the engine

`A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80,
R=0x100, L=0x200` (standard active-low GBA mask, confirmed by the menu code
testing `0x40`/`0x80` for Up/Down and `1`/`2` for A/B).

### 6.3 Unused content found

| Item | Address | Status |
|---|---|---|
| `Secrets Page` / `Page Cheat` / `Cheatseite` | triplet `0x715FD0` | zero references in image → cut page |
| `TEST 1` level label | `0x715D68` → `0x824244C` | not in level table → unused |
| pause-menu icon rows 2–4 | jump table `0x0801D220` (5 entries) | enable bytes `0x02002119–0x0200211B` never set; only rows 0/1 drawn |
| `RELOCK MOVIES` action | `0x0802848C` | developer path, no controller caller |

## 6b. Enumeration

### 6b.1 Which spaces were searched, and how large they are

| Space | Size searched | Method | Result |
|---|---|---|---|
| ASCII strings | 98,691 strings ≥4 bytes | `strings -t x -n 4` + `grep -i` for password/cheat/code/debug/secret/unlock/level/passwort/passe | 0 password/code strings; 1 `Cheatseite`+1 `Page Cheat`+1 `Secrets Page`; `SECRETS`, `Secret Found`, `Secret Gefunden`, `Secret Trouve` |
| Localized UI labels | 350 strings × 3 languages (`0x241F8C–0x2434FF`) | full dump + classification | only cheat-ish label is the unused Secrets Page triplet |
| Label triplets | 4,352 file bytes (`0x715EA4–0x7172F4`) | byte scan for every triplet address outside the table | every displayed label has ≥1 pointer; `0x715FD0` has **0** |
| Button-code tables | all 4,194,304 2-byte offsets | 432 runs of ≥3 key masks; of those 5 are pointer-referenced | none is a code sequence (palette words, graphics, `"AAA"` literal, 1/2/4/8 glyph table) |
| Multi-button masks | 58 key-mirror read sites | disassembled 40 instructions after each literal load | no `AND`/`CMP` with `0x300`, `0x30C`, `0x3FF` or any L/R/Select combination |
| Published code literals | 11 CodeBreaker codes from 3rd party cheat indexes | searching the ROM for each token/address | codes are device memory patches; no in-game equivalent exists |
| Hidden screens | main menu, options, movies, slot select, name entry, pause, quit confirm, credits, high scores | navigated and screenshotted; combos pressed at title and main menu | no additional screen |

### 6b.2 How the "label is live" test was done (patch experiment)

To prove that the ASCII label bank is the string source actually rendered (and
therefore that a missing reference is meaningful), a copy was patched:

```
file 0x242B8C  "New Game" -> "XEW GAME"
```

Booting the patched copy and pressing START on the title shows the main menu with
**`XEW GAME`**. The same bank supplies `LOAD GAME`, `OPTIONS`, `MOVIES` and the
audio toggles (pool `0x0241DC0`), so an unreferenced entry in this bank is
unreachable text, not dead storage used by another mechanism.

### 6b.3 Button-combo sweep (negative, dynamic)

Pressed at the title screen and at the main menu, each held ~180 ms, screen
captured afterwards:

`Select`, `L`, `R`, `L+R`, `L+R+Start`, `L+R+Select`, `A+B+Start+Select`,
`B+Select`, `Up+Select`, `Down+Select`.

No new screen, no changed label, no new sound. (`A+B+Start+Select` is not a
reset on this title; only the Start press inside it opens the menu.)

### 6b.4 Why there is no "novel code" here

§0.2 item 3 (mint an unpublished code) requires a code space. The measurements
above define the space as **empty**:

* text codes: alphabet = the save-name keyboard (A–Z, 0–9, space), length 8, but
  the buffer has no comparison consumer → 0 accepted "codes";
* button codes: no sequence table and no multi-button comparison → 0 sequences
  with an action;
* menu codes: every reachable menu row was walked (4 + 5 + 5 + 3 + 2 + 2 = 21
  rows, all listed in §3.1) and no row is input-gated.

The corresponding §0.2 deliverable is the bounded negative, with the unused
content in §6.3 as the substantive result.

## 7. Validation evidence

**Observed (emulator, screenshots/RAM)**
* Mode7 intro screen and its `Game supplied by: Nick Burns (CCG) / Released on:
  Oct 24th, 2002` text; START then hands off to the stock boot (Activision logo).
* Main menu 4 rows; options 5 rows with wraparound; movies 5 rows; `MOVIE 1`
  plays, locked rows print `MOVIE LOCKED`; pause = `GAME PAUSED / CONTINUE /
  QUIT / SCORE`; quit confirm `YES/NO`.
* Patched `"XEW GAME"` renders in the main menu (label bank is live).
* RAM: `0x02036E14 = 1` (level index) on a new save; slot record at
  `0x02036E20` contains name `AAA` at `+4`; `0x020020B0+0x67..0x6B` all zero at
  the pause screen; `0x0203BE6C = 0` (English).
* Savestate diffs: the attract/menu background animates continuously (≈3.4 KB
  EWRAM / 5 KB VRAM change per 0.4 s with no input), which is why the combo
  sweep was judged visually rather than by pixel/state diff.

**Derived (disassembly)**
* Cracktro control flow: START wait → `SWI 1` (RAM reset) → `bx 0x080000C0`.
* Pause menu uses label triplets `0x087161F8`/`0x08716204` and a 5-entry icon
  jump table at `0x0801D220`; enable bytes never set.
* `0x0802695C` reads the menu id and calls the debug printf
  `"Keychoose=%d menu=%d"`; the debug/printf bank is compiled into the retail
  image but has no key/UI entry point.
* No ROM word equals any triplet address for `Secrets Page`; every displayed
  label has at least one such word.

**Inferred**
* Movies 2–5 unlock from collected secrets (the "Secret Found" counter at the
  `0x08020D0A` handler) — the trigger threshold was not isolated.
* The `Secrets Page` string was intended as the title of a page listing collected
  secrets/cheats and was cut before shipping (label bank retained, no code path).
* Language is selected outside the visible menus (3-language bank present, no
  language row in Options).

## 8. Unknowns

* The mechanism that reaches the main-menu label pool at `0x0241DC0` was not
  identified: neither a Thumb LDR-literal, an ARM LDR-literal, nor an `ADD
  pc` reaches it, and no 32-bit word in the ROM equals its address. The patch
  test proves the pool's *strings* are what get rendered, so this is a tooling
  blind spot (likely a computed table base), not a dead table.
* Exact unlock condition and save bit positions for movies 2–5 were not
  isolated; only the displayed `MOVIE LOCKED` state and the presence of a relock
  path were confirmed.
* `TEST 1` (`0x824244C`) was not made reachable; no writer of a level index of 21
  exists in code (the level table has 21 records, indices 0–20).
* Whether the PAL/EU revisions share these addresses — only the `AJGE` USA/Europe
  image above was analysed.

## 9. Tooling

* `mgba` (SDL) 3× under `Xvfb :337` + `openbox`, `SDL_AUDIODRIVER=dummy`,
  `xdotool` for input, `scrot`/ImageMagick for captures.
* `arm-none-eabi-objdump -M force-thumb/-M force-arm` and Capstone 5.0.7 for
  targeted disassembly (`dis.py` helper resolving PC-relative literals to
  strings), a hand-written Thumb `BL` scanner and Thumb/ARM `LDR`-literal
  scanners (`ldrscan.py`, `blscan.py`).
* `ram.py`-style savestate reader: PNG `gbAs` chunk → `zlib.decompress` →
  EWRAM/VRAM/IWRAM windows.
* Artifacts (not shipped): `clean.gba` (entry restored), `test_name.gba`
  (label patch test), `orig.gba` (byte copy of the target), savestates, scripts.

## 10. Legal note

No ROM, graphics, music or text extract is redistributed here. Only addresses,
hashes, sizes, short label strings needed to identify UI elements, and the
analysis itself are published.
