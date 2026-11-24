# Need for Speed: Underground 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Scope: in-game / developer-intended cheats only (passwords, button codes, hidden/debug menus,
unlockables). GameShark / CodeBreaker / Action Replay memory-edit codes are out of scope and are
only mentioned to classify web hits. All conclusions below are for the exact 8 MiB image whose
hash is recorded in §1; the sibling *Need for Speed: Porsche Unleashed* was not used as evidence.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Need for Speed: Underground 2.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `NFSUG2` |
| Game code | `BNFE` (USA) |
| Maker code | `69` (Electronic Arts) |
| Version | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0) |
| Fixed `0x96` / complement / checksum | `0x96` / `0x00` / `0x0012` (header intact, not rebuilt) |
| MD5 | `b5509a24acd58ddcb3d2e251a074f494` |
| SHA-1 | `f772000fbdfb84d8d5de9f69bd9c0de551389929` |
| SHA-256 | `cf9be79fb71b89667ac4b1b24eb956deb2ec0481a454319889b66ded3dbc4ded` |

**Phase 0 embedded-header / patch scan.** Scanning all 8 MiB for the 156-byte Nintendo logo
(`24 ff ae 51 69 9a a2 21 …`) produced exactly **one** hit, at file offset `0x4` (the primary
header). No second game image, no boot selector, no appended trainer, and no cracktro patch: the
entry word is the stock `b 0x080000C0` and the first 4 KiB disassembles as a normal ARM crt0.

## 2. Executive summary

**There is no player-facing cheat system in this GBA build.** It has:

* no password/code entry screen (the only text-entry UI is the 40-glyph **profile name** editor,
  which is a label field, not a validator — §16.2b);
* no button-code table and no in-game button code (all published button codes belong to the
  GameCube/PS2/Xbox SKUs, and PC uses typed phrases; none are present in this ROM under any
  encoding tested);
* no reachable hidden/debug menu. The ROM *does* contain developer screens — a 44-entry screen
  dispatch table with two blank `MENU TUNING` screens (indices 4 and 5) and a `Placeholder` screen
  (index 10), plus a 28-byte-record event-editor data structure at `0x0878d164` — but no in-game
  input path to them was found. All 44 handlers were enumerated by probing the dispatch table with
  a savestate patch (an analysis probe only, **not** a player cheat); the reachable subset was
  walked in the emulator.

Everything that looks like an "unlock" in this game is **progression-gated save data**: cars,
tracks, parts and the `DEFI UNDERGROUND` modes are unlocked by winning events (the game literally
shows `WIN EVENTS TO UNLOCK CARS, TRACKS, & UPGRADES!` / French `GAGNE DES COURSES POUR …`).
The 9 `unlock` string hits are localization labels for those rewards, not code validators.

The negative result is bounded: every reachable screen was walked with RAM evidence, the entire
text bank and key-mask space were searched with recorded counts, and every published code family
was verified against the ROM and/or tested in the emulator.

## 3. How to reproduce

* Emulator: mGBA (SDL), `-3`, under `Xvfb :316` + `openbox`, `SDL_AUDIODRIVER=dummy`.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold 80–150 ms; short taps are missed.
* Boot path: language flag (4 flags) → PSA (`A`) → title/attract loop; press Start at the
  `PRESS START` prompt. Enter a profile name with the on-screen keypad (A selects a glyph, cursor
  to the ✓ cell bottom-right, A confirms) → buy the first car (`Nissan 240SX`, 10 pts, confirm YES)
  → main menu.
* Menu path (English): `Main Menu → Race Now → Custom Race → (mode) → (track) → race → Start=pause`;
  `Profile → Options → Audio/Settings/Language/Credits/Delete Profile`; `Garage → Upgrade →
  Visual/Performance`; `Mini Games`; `Go Underground`; `Multiplayer`.
* Screen-state RAM proof (§4) was obtained from mGBA savestates: `Shift+F<n>` saves slot n,
  `F<n>` loads; the `.ss<n>` file is a PNG whose `gbAs` chunk is zlib-compressed; decompress it to
  a raw 397,312-byte state. EWRAM starts at raw `0x21000`, IWRAM at raw `0x19000`.
* Code/button tests used a savestate taken at the title screen (slot 9), so each trial was one
  `F9` load + the sequence + `Shift+F1` save + a RAM diff against slot 9.
* Hidden-screen probe (analysis only): patch byte `(u32*)0x030058ac + 0x412` in a saved main-menu
  state to the desired dispatch index, recompress the `gbAs` chunk, load slot 9, screenshot.

## 4. Address map

| Item | Address / value | Evidence type |
|---|---|---|
| Nintendo logo / GBA header | file `0x4` / header `0x0` | Derived (byte scan) |
| Input routine | `0x08142D38` | Derived (disassembly) |
| KEYINPUT literal | `0x04000130` at `0x08142D58` | Derived |
| Held-key word (active-high) | `0x03006708` | Derived |
| Newly-pressed word | `0x03006704` | Derived |
| Screen-state pointer | `u32 0x030058AC` → `0x02000808` | Observed (savestate RAM) |
| Screen handler index byte | `(u32*)0x030058AC + 0x412` | Observed (patch → screen change) |
| Screen dispatch table | `0x0878D8A4`, 44 Thumb pointers through `0x0878D948` | Derived |
| Main loop / transition consumer | `0x0811E020`, global `0x03005950` | Derived |
| Event-editor field labels | `0x0878D164`–`0x0878D340`, 0x1C-stride records | Derived |
| Event-editor UI cluster | `0x08123F04`–`0x08124350` | Derived |
| English text bank (ASCII) | `0x074B000`–`0x0756xxx` | Observed |
| Profile-name keypad alphabet | `1-9 0 A-Z . , ! :` + backspace + ✓ (40 glyph keys) | Observed (screen) |

Observed screen-index values (byte at `struct+0x412`): title `0x2B` (43), main menu `0x00`,
mini-games `0x0B` (11), pause `0x20` (32), custom-race setup `0x29` (41), options `0x06` (6),
language `0x09` (9). The patch probe reproduced each screen from the table entry at that index,
which validates the mapping.

## 5. Algorithm

No password validator or checksum exists to reimplement. The relevant algorithm is the input and
screen-dispatch machinery:

```c
// 0x08142D38 — called once per frame
held_old = *(u16*)0x03006708;
cur      = ~(*(volatile u16*)0x04000130) & 0xFFFF;  // active-high
pressed  = cur & ~held_old;
*(u16*)0x03006704 = pressed;   // edge-triggered
*(u16*)0x03006708 = cur;       // held

// 0x0811E020 — main loop/transition consumer (abridged)
struct = *(u32**)0x030058AC;
idx = struct[0x416] ? struct[0x415] : struct[0x412];   // signed/unsigned byte
handler = ((u32*)0x0878D8A4)[idx];
handler(/* frame context */);
```

Key masks for this engine are the standard active-high values
`A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`.

## 6. Tables

* **Screen dispatch table** at `0x0878D8A4` (44 entries). All 44 were rendered via the analysis
  probe. Reached in normal play: main menu (0), mode submenu (1), race-type list (2), track list
  (3), options (6), "500 miles" message (7/8), language (9), mini-games (11), garage/stats/parts
  (13/14), underground menus (15/19), circuit progress (16), drag list (17), race setup (18/41),
  controls (20), units (23), profile screens (24–26), drag mini-game (28), game over (29), player
  stats (30), engine tuning (31), endurance (32), multiplayer (33/34/38), high scores (35),
  precision (36), dyno (37), bonus scores (39), pause (40), title (43).
  **Not reached in normal play:** 4, 5, 10, 12, 21, 22, 42 (and 43 requires title assets).
* **Hidden developer screens:** index 4 and 5 render a header-only `MENU TUNING` screen; index 10
  renders a literal `Placeholder` screen. Their handlers live at `0x08123FE0`, `0x08123xxx`, and
  the field-label table they use is at `0x0878D164` (`Tuning`, `Event Number`, `Unlock Flag`,
  `Reward Type`, `Event Type`, `Race Type`, `Track Number`, `Catchup AI Type`, `Time Estimate`,
  `Opponent 1/2/3`, `Traffic`, `Start pos`, `Difficulty`, `Drift Multi Easy/Med/Hard`). Records are
  0x1C bytes: 16-byte ASCII label + three 32-bit parameter words.
* **Unlockables (progression, not codes):** 14 named cars in the text bank
  (`Nissan 240SX`, `Nissan 350Z`, `Mazda RX-7`, `Toyota Celica`, `Mitsubishi Lancer EVO VIII`,
  `Audi TT`, `VW Golf GTI`, `Toyota Supra`, `Mitsubishi Eclipse GSX`, `Lexus IS300`,
  `Subaru Impreza WRX STi`, `Mazda RX-8`, `Nissan Skyline`, plus generic `CAR 1`–`CAR 20` labels),
  tracks (`CITYHALL 1-5`, `AIRPORT 1-5`, `DOCKS 1-5`, `FREEWAY 1-5`, `STADIUM 1-5`,
  `FAIRGROUNDS 1-5`, `THE ARCHWAY 1-5`, `INDUSTRIAL TOUR 1-5`, plus drag/drift variants),
  and part bonuses (`TURBO BONUS`, `WHEEL BONUS`, `SHOCK BONUS`, `NITROUS BONUS`, `EXHAUST
  BONUS`, `ENGINE BONUS`, `DRIVE BONUS`, `CONTROLS BONUS`, `CHASSIS BONUS`, `BRAKES BONUS`).
  Gate messages: `TRACK IS LOCKED`, `CAR IS LOCKED`, `PART IS LOCKED`, `EVENT IS LOCKED`,
  `WIN EVENTS TO UNLOCK CARS, TRACKS, & UPGRADES!`, `YOU HAVE DRIVEN OVER 500 MILES!`.

## 6b. Enumeration

**Code space: empty (0 codes).** There is no alphabet+checksum system and no button-code table to
enumerate, so §0.2's "mint a novel code" deliverable does not apply. The equivalent negative
results are bounded as follows:

1. **Screen/action space fully enumerated.** 44/44 dispatch handlers probed; 31 reached in normal
   play and walked in the emulator with a screenshot each. The 13 others were rendered by the
   analysis probe: 4, 5 (`MENU TUNING`), 10 (`Placeholder`), 12, 21, 22, 27, 29, 34, 38, 42, 43
   and the second 500-miles variant. No hidden menu item appeared on any reachable screen, and no
   undocumented action branch exists in the input dispatcher (0x08142D38 only produces held/pressed
   words; it does not test sequences).
2. **Text space searched, with counts** (`strings -t x -n 4`, case-insensitive):
   `password` 0, `cheat` 0, `code` 0, `debug` 0, `secret` 0, `hidden` 0, `level select` 0,
   `enter code` 0, `unlock` 9 (all `TEXT_*Unlock` / `NFS CAR UNLOCKED` / `YOU HAVE UNLOCKED`
   reward labels). The ASCII bank `0x074B000`–`0x0756xxx` was dumped and read; the debug field
   labels at `0x0878D164` were decoded as font-indexed/ASCII field names, not input prompts.
3. **Button space searched, with counts.** Published console sequences were packed as u16-LE,
   u16-BE, u8, and each reversed, in active-high and active-low form — 6 sequences × 8 forms =
   48 literal searches, **0 hits**. A whole-ROM scan for runs of ≥6 consecutive non-zero GBA key
   masks found 8 candidate u16 runs, all in data/audio tables (e.g. `0x045090`, `0x78C17B`), none
   a plausible code table. Key consumers: the two globals `0x03006704/08` are read by ordinary
   menu/gameplay code; no sequence-comparison loop was found.
4. **Published codes tested.** 3rd party cheat indexes' GBA page lists **no button codes** (only "complete Go
   Underground" and "100% game" unlockables); the NFS wiki explicitly assigns button codes to
   GC/PS2/Xbox and typed phrases to PC. The 12 PC phrases (`regmybank`, `ordermybaby`,
   `regmebaby`, `needperformance1`, `gimmevisual1`, `opendoors`, `yodogg`, `wannacapone`,
   `shinestreetbright`, `gottahavebk`, `needmybestbuy`, `regmybaby`) were searched in ASCII,
   uppercase, `+0x20`, `-0x20`, UTF-16LE, UTF-16BE and XOR-0xFF: **all absent**. GBA
   CodeBreaker/Action Replay entries (3rd party cheat indexes) are memory-edit
   codes and are out of scope by the brief; they are not in-game cheats.
5. **Dynamic rejection.** At the title screen, 7 published/console-derived sequences
   (`bank200`, two `bank1000` mappings, `bestbuy`, `bk`, `circuit`, plus a novel `L R L R U D U D`),
   the Konami code, and 7 classic GBA combos (`L+R+Start`, `L+R+A+B+Start`, `Select+Start`,
   `L/R+Up`, `L/R+Down`) were entered from a saved title state and diffed against a no-input
   control. The control changed 686 bytes (animation noise); the sequences changed 400–438 bytes
   with **no distinctive persistent flag** and produced **identical screenshots**. Combos that
   included Start simply left the title screen (52,545-byte state change), not a code effect.
   Result: all tested codes rejected; no code accepted.

## 7. Validation evidence

* **Observed** (emulator/savestate): every screen in §3/§6; the 44-handler contact sheet; the
  profile-name keypad and its 40 glyphs; title-screen code trials and their RAM diffs; screen-index
  bytes `0/6/9/11/32/41/43` at `struct+0x412`; the `Placeholder` and `MENU TUNING` probe renders.
* **Derived** (disassembly/byte scan): single clean header and stock entry; input routine
  `0x08142D38` and globals `0x03006704/08`; dispatch table `0x0878D8A4` and main loop
  `0x0811E020`; event-editor records at `0x0878D164`; 48/48 published-sequence literal misses;
  12/12 PC-phrase misses across 7 encodings; 0 string keyword hits for password/cheat/code/debug.
* **Inferred** (not proven): that indices 4/5/10/12/21/22/42 are permanently unreachable in
  normal play. They were never entered by any menu navigation or button sequence tried; an
  exhaustive proof would require enumerating every writer of `0x03005950` and `struct+0x412`,
  which was not completed. They are labelled inferred, not observed-unreachable.
* **Prompt-injection check:** fetched cheat pages (3rd party cheat indexes, NFS wiki, 3rd party cheat indexes, underground2.com, NFSMods) were treated as data. One page contained an unrelated block
  of "CodeBreaker codes … ALL Skaters / Mini Games" copy belonging to a different Tony Hawk title;
  it was ignored as misattributed data, not followed. No fetched page contained instructions that
  were acted upon.

## 8. Unknowns

* Whether any of the unreached dispatch indices (4, 5, 10, 12, 21, 22, 42) has an in-game trigger
  that was not tried (e.g. a very long or context-gated button sequence). The savestate patch used
  to view them is a RAM edit, not a player input, so it is **not** presented as a cheat.
* The precise semantics of the three 32-bit parameter words in each 0x1C-byte event-editor record
  at `0x0878D164` (the fields were identified by their labels; the value encodings were not
  decoded because the screen is unreachable).
* A handful of unlabelled/black dispatch entries (42, 43-without-title-assets) were not given a
  gameplay meaning.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all
  disassembly; Capstone 5.0.7 for literal/BL/register-tracking scans; `strings -t x`, `grep -abo`,
  `xxd`, Python `struct` for byte scans.
* mGBA (SDL) `-3` under `Xvfb :316` + `openbox`; `xdotool` XTEST input; `scrot` + ImageMagick
  `convert`/`montage` for screenshots and the 44-screen contact sheet.
* `ui.py` (input/screenshot helper), `detect.py` (title-screen pixel detector), `savediff.py`
  (savestate `gbAs` zlib reader + EWRAM/IWRAM diff), `btntest.py` (code trial harness),
  `patchstate.py` (analysis-only dispatch-index probe), `screenstate.py` (screen-index reader).
  All scripts were in `/tmp/nfsu2/`.
* Installed/used from the base toolchain: binutils-arm-none-eabi, mGBA, Xvfb, openbox, xdotool,
  scrot, ImageMagick, Python 3 with capstone/keystone. No additional packages were required.

## 10. Legal note

No ROM image, extracted graphics, music or game text is redistributed here. Only hashes, file
offsets, addresses, algorithms and original analysis scripts are published.
