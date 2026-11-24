# It's Mr. Pants (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/It's Mr. Pants/It's Mr. Pants.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `ITS MR PANTS` |
| Game code / maker | `BPIE` / `78` (Europe) |
| Version / complement / checksum | `0x00` / `0x6D` / `0x0000` |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| Fixed `0x96` | present at `0xB2` |
| MD5 | `86f3a374af80e633531c538d9aeaf396` |
| SHA-1 | `c49742f964a698ccce0520e24368a9d425a29b4d` |
| SHA-256 | `359823f0b3884fe8e30025443ed04265417f9350acc303affeb4900adc5b4c7e` |

**Phase 0 / embedded-header scan:** scanned all 4 MiB for the 156-byte Nintendo
logo; exactly **one** GBA header exists (file offset `0x0`, title `ITS MR PANTS`,
code `BPIE`, stock entry word). **No appended trainer, no second header, no
cracktro patch.** The header checksum is `0x0000`, which is normal for a rebuilt
header; the complement byte `0x6D` is intact.

Notable build identity (file offsets / ROM addresses):
- `0x169F11` / `0x08169F11`:
  `********** IT'S MR PANTS - Build_PJM_20040917_1651 - Testing V7.7a - Paul Machacek - Rare Ltd - No Comms, Eeprom V124, Paul's old HDMA reset **********`
- `0x161594` / `0x08161594`: `THQ TESTING TEAM` (credit roll)
- `0x16179A` / `0x0816179A`: debug symbol/assertion strings (`c_suSaves.c`,
  `_suSaves_SetPuzAttempts250`, `c_glLanguage.c _glLanguage_GetText`, etc.)

This is a **developer testing build** of the retail game, not a patched ROM.

## 2. Executive summary

**There is no in-game password system, no button-code cheat, and no reachable
hidden/debug menu in this ROM.** The game's "cheats" in every published list are
achievement-driven **unlockables** (beat mode X at difficulty Y to unlock mode Z
or a trophy/postcard), which are EEPROM save-bit state, not a code system.

The evidence is a closed negative, not an absence of searching:

1. **Text space fully decoded.** All UI text lives in one 301-entry pointer table
   at `0x0816AF5C`–`0x0816B410`, pointing into an ASCII message bank at
   `0x0815F808`–`0x08161650`. Every entry was dumped and decoded (§6). There is
   no `PASSWORD`, `CHEAT`, `CODE`, `SECRET CODE`, `DEBUG MENU`, `WARP`, or level
   code string anywhere in the 4 MiB (`strings -t x -n 4`, 44,881 lines,
   keyword-classified). The one input field (name entry) uses the alphabet
   ` ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` at `0x08160EF8` and is a high-score /
   save-slot **label**, not a validator (no comparison against the entry buffer
   outside the entry handler; no PASSWORD string).
2. **Button space searched.** The only input-driven special branches in the
   whole ROM are the two standard reset combinations in the input driver at
   `0x0813E048` (all of A+B+Select+Start, and the same on the link player's key
   word). No Konami-style or other cheat sequence exists as a key-mask table:
   6 common sequences × 3 encodings (active-high u16/u32, active-low u16) = 18
   literal searches, **0 hits**. Three sequences plus the reset combo were
   pressed in the emulator on the title screen; none opened a hidden screen (the
   reset combo soft-resets to the save-slot selector).
3. **Every reachable screen was walked** with frame-accurate input and a full
   RAM savestate captured at each one (§3, §7): boot/THQ/Rare splashes, title,
   name entry, save-slot select, 4-entry main menu, skill select, puzzle intro /
   play / help / pause / fail, Scores, Art Gallery, Save Slots, and the
   repeatedly-press-<>- Easter egg. No hidden entry appeared on any of them.
4. **Developer leftovers were found but are unreachable.** The puzzle-name table
   at `0x0815EEC0` (11-byte records) contains three test level names at indices
   257–259 (`TEST MED`, `TEST HAR`, `TEST EAS`), past the valid puzzle range.
   `_suSaves_SetPuzAttempts250` at `0x08147FEC` asserts `1 <= puzzle_index <= 250`,
   so indices 257–259 can never be selected. The crash debugger documented by
   3rd party cheat indexes only appears on a fault, not through controller input.

Published codes tested: the 3rd party cheat indexes "cheats" are unlock conditions,
not typable codes; their message strings were verified present in the ROM
(§6, unlock table). The single published Easter egg ("on the save menu,
repeatedly press < or >") was exercised in the emulator and does cycle the
slot icons (the narrator voice itself is inaudible under `SDL_AUDIODRIVER=dummy`).
GameShark/CodeBreaker codes on 3rd party cheat indexes are memory-edit codes and are out
of scope (not tested).

## 3. How to reproduce

**Emulator / display (this run):** `Xvfb :319 -screen 0 1024x768x24`,
`DISPLAY=:319 openbox`, `SDL_AUDIODRIVER=dummy`,
`mgba -d -3 "roms/It's Mr. Pants/It's Mr. Pants.gba"` under a pty.

**Why `-d`:** mGBA's CLI debugger (`-d`) accepts `frame`, `r/1|r/2|r/4 ADDR`,
`w/*`, `save N`/`load N`, breakpoints and watchpoints on a pty. This build's GDB
stub (`-g`) accepted no connections and the normal SDL window dropped XTEST key
events while free-running, so all screens were reached with **frame-accurate
input**: hold the key with `xdotool keydown`, issue N `frame` commands, release
the key, advance a few more frames, then screenshot and save a state. `KEYINPUT`
at `0x04000130` was verified active-low (`0x3FF` released, `0x03F7` with Start
held), so the XTEST keyboard path is proven, not assumed.

**Keymap (mGBA SDL defaults):** A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys.

**Exact path to each screen (all reproduced on :319):**

| Screen | Path |
|---|---|
| Boot splashes | power on; ~180+120 frames auto-advance THQ → Rare → title |
| Title | boot finished; "PRESS START" |
| Save-slot select | from title press **A** (or press A+B+Start+Select reset combo), wait ~1 s |
| Name entry | highlight an empty slot, press **Start**; press **Start** again to accept |
| Main menu (4 entries) | after name entry; Puzzle / Wipeout / Marathon / Options, cycle with **Left/Right** |
| Skill select (3 entries) | main menu → Puzzle (or Wipeout/Marathon) → **A**; Easy / Medium / `Replay Puzzles?` (Hard & Special locked) |
| Puzzle intro → gameplay | skill select → **A** → title card → **A** to start |
| Help text | in gameplay press **Start** once; **B** to dismiss |
| Pause menu | in gameplay press **Start**; Continue / Colors / Shapes / Quit |
| Puzzle fail | pause → Quit (or fail a puzzle) |
| Options submenu (3 entries) | main menu → Options → **A**; Scores / Art Gallery / Save Slots |
| Scores | Options → Scores → **A** (~60 frames to render) |
| Art Gallery | Options → Art Gallery → **A** (Left/Right = picture, L/R = category) |
| Save Slots + Easter egg | Options → Save Slots → **A**; press Left/Right repeatedly |
| Language screen | **not reachable from any menu** on this build (see §8) |

**Button-code tests on title:** Konami (`U U D D L R L R B A`), `L R U D B A`,
`U D L R B A` — no effect. `A+B+Start+Select` held → soft reset to save-slot
screen (the documented reset combo, not a cheat).

## 4. Address map

| Address (ROM) | File offset | Meaning |
|---|---|---|
| `0x08000000` | `0x0` | Header; entry branch `0xEA00002E` |
| `0x0813E048` | `0x13E048` | Input driver: reads `0x04000130`, builds held/pressed masks, reset-combo checks |
| `0x0813E0B4` | `0x13E0B4` | Literal `0x04000130` (KEYINPUT); only occurrence in ROM |
| `0x0813E0B8` | `0x13E0B8` | Literal `0x3FF` (10-bit key mask) |
| `0x0813E0BC/B4/C0` | `0x13E0BC..` | Pointers to key globals `0x0200F54/58/50/4C` |
| `0x0813A180` | `0x13A180` | Returns screen/mode byte at `0x0200A55` |
| `0x08139194` | `0x139194` | Screen-reset routine called by reset combos |
| `0x0815EEC0` | `0x15EEC0` | Puzzle-name table, 11-byte stride, ≥260 entries; indices 257–259 = `TEST MED/HAR/EAS` |
| `0x0815F808` | `0x15F808` | Start of concatenated ASCII message bank |
| `0x08160EF8` | `0x160EF8` | Name-entry alphabet `" ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"` |
| `0x081615A8`–`0x08161720` | `0x1615A8`.. | Copyright, Rare splash, EEPROM error, credits, debug build text |
| `0x08161724` / `0x08161728` | `0x161724/28` | Data descriptor: pointers to message table `0x0816AF5C` and puzzle-name table `0x0815EEC0`, plus stride `11` |
| `0x0816AF5C`–`0x0816B410` | `0x16AF5C`.. | **Message pointer table: exactly 301 entries**, all decoded (§6) |
| `0x08147FEC` | `0x147FEC` | `_suSaves_SetPuzAttempts250(index, attempts)` — asserts `1<=index<=250` |
| `0x08148058` | `0x148058` | `_suSaves_GetPuzAttempts250(index)` — asserts `1<=index<=251`, `251` returns 0 |
| `0x08169F11` | `0x169F11` | Build/version banner ("Testing V7.7a") |

**RAM (from savestate `gbAs` chunks and live debugger reads):**
- `0x0200F4C` = previous held keys; `0x0200F50` = newly pressed keys;
  `0x0200F54` = combined key word; `0x0200F58` = active-high held keys (10-bit);
  `0x0200A55` = screen/mode byte.
- `0x04000130` = KEYINPUT, active-low (observed `0x3FF` / `0x03F7`).
- mGBA `.ssN` savestates: PNG with `gbAs` zlib chunk → 397,312-byte raw state;
  VRAM at raw `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000` (guide §16.13).

## 5. Algorithm

No password algorithm exists. The relevant algorithms are:

**Input sampling (0x0813E048), derived from disassembly:**
```
held10   = 0x3FF & ~KEYINPUT                 # active-high, A=1..L=0x200
player0  = read_link_keys(0) & 0x3FF
combined = held10 | (player0 << 10)
pressed  = combined & ~previous_combined
previous = combined
if screen_mode(0x0200A55) not in {2,4}:
    if (combined & 0x00F) == 0x00F:    soft_reset(2)   # A+B+Select+Start
    if (combined & 0x3C00) == 0x3C00:  soft_reset(2)   # same via link player
```
No other key mask is compared in the driver.

**Save-bit unlock model (derived from strings + code):** each unlockable is a
flag/byte in the EEPROM save slot, set by a gameplay achievement (survive N
minutes, clear N puzzles, beat mode X). The message table contains the exact
unlock announcements (§6). `_suSaves_SetPuzAttempts250` bounds puzzle index to
`1..250`, which — together with the 25/50/75/100 puzzle counts shown in-game —
closes the 3 TEST-name entries at table indices 257–259 out of reach.

**Name entry (0x08160EF8):** a 37-character alphabet used to type a 5-character
player label for high scores/save slots. Test for a "text field is not a
password field" (guide §16.2b): the message table has no comparison target and
the field's only consumers are the score/save screens. No validator.

## 6. Tables

**Message table** (`0x0816AF5C`, 301 entries). Highlights (all 301 dumped; no
code/password/debug-menu entry):

| ID | String | Role |
|---:|---|---|
| 0–14 | gallery prize messages ("CLEAR 5 PUZZLES TO EARN THIS PICTURE" …) | unlockable gallery |
| 15–18 | `EASY`, `MEDIUM`, `HARD`, `SPECIAL` | skill levels |
| 33–39 | hard/special level unlock announcements | **unlockables** |
| 54 | ` IS MR PANTS SECRET SHAPE` | secret shape reward |
| 62–66 | `CONTINUE`, `COLORS`, `SHAPES`, `QUIT`, `PAUSED` | pause menu (all 4 entries walked) |
| 77–78 | `ITS MR PANTSQUAKE`, `MRS PIES REVENGE …` | minigame descriptions |
| 93–104 | bronze→platinum trophy announcements | **unlockables** |
| 140–152 | `SELECT A GAME`, `SAVED GAMES`, 6 mode descriptions, `PLAY THE GAMES` | game-select text |
| 156–161 | `OPTIONS`, `SCORES`, `ART GALLERY`, `WASH YOUR PANTS…` | Options menu |
| 163–179 | `GUEST`, `PLAY`, `CHANGE NAME`, `WASH PANTS`, `ERASE HISCORES`, `ENTER YOUR NAME`, alphabet, `REPLAY PUZZLES?` | save/name screens |
| 185–189 | `SELECT YOUR LANGUAGE`, `SAVE SLOTS`, `LANGUAGES`, `YES`, `NO` | language UI (screen not reached) |
| 190–264 | `MARAPANTS` … `MUDDLE`, credits names, `THQ TESTING TEAM` | themes/credits |
| 265–300 | Rare/THQ staff names | credits |

**Puzzle-name table** (`0x0815EEC0`, 11-byte records): indices 0–256 normal
names; **257=`TEST MED`**, **258=`TEST HAR`**, **259=`TEST EAS`** (file offsets
`0x15F9CB`, `0x15F9D6`, `0x15F9E1`). These three are developer test levels,
outside the valid 1..250 puzzle index domain — cut/unreachable content, not a
cheat.

**Published "cheats" verified in ROM** (3rd party cheat indexes 2026-02-03 capture; all are
unlock conditions, none is a typable code):

| Published unlock | ROM verification |
|---|---|
| Hard Marathon/Puzzle/Wipeout Mode | strings at `0x0815FE2C`, `0x0815FF94`, `0x0815FED8`; Hard entries hidden in skill select until unlocked (observed) |
| Special modes + Funky Special Level | strings at `0x0815FE84`, `0x0815FF34`, `0x0815FFE4`, `0x08160034` |
| Bronze/Silver/Gold/Platinum trophies (3 tracks) | strings at `0x08160620`–`0x08160978` (12 announcements) |
| Art-gallery pictures every 5 puzzles | strings at `0x0815FC38`–`0x0815FD74`; gallery screen walked |
| Save-menu Easter egg (< > repeatedly) | exercised on Save Slots screen; icon cycles (audio not verifiable with dummy driver) |
| GameShark/CodeBreaker codes (3rd party cheat indexes) | memory-edit codes, out of scope; not tested, recorded here |

**Prompt-injection check:** web content fetched (3rd party cheat indexes archive, 3rd party cheat indexes
Prerelease, search snippets) contained no embedded instructions or injection
payloads; all were treated as data. No fetched page was acted upon.

## 6b. Enumeration

This is a **negative-result engagement**: there is no code space to enumerate.
The negative is bounded by the following exhaustive searches and counts.

**Text / code spaces searched and counts**

| Space | Size | Result |
|---|---|---|
| Whole-ROM strings (`strings -t x -n 4`) | 44,881 lines | 0 password/cheat/code/debug-menu strings; all keyword hits classified (audio-engine asserts, gallery/unlock text, name alphabet, credits) |
| Message pointer table | 301 entries (`0x0816AF5C`–`0x0816B410`) | 100% decoded; 0 code/password/debug entries |
| Puzzle-name table | 260 entries (`0x0815EEC0`, 11-byte stride) | 3 dev test names (257–259), unreachable (index bound 250) |
| Name-entry alphabet | 37 symbols (`0x08160EF8`) | label, not a validator; no comparison target |
| KEYINPUT literal references | 1 (`0x0813E0B4`) → 1 reader (`0x0813E04C`) | only reset-combo branches found |
| Key-mask literal searches | 6 sequences × 3 encodings = 18 searches | 0 hits for any cheat sequence |
| Common sequence prefixes searched as u16/u32 | Konami (8 & 10 press), `U D L R`, `L D R U`, `L R Start`, `L R Select` | 0 hits |

**Button spaces tested dynamically (title screen)**

| Input | Observed effect |
|---|---|
| `U U D D L R L R B A` (Konami) | no change; title remains |
| `L R U D B A` | no change |
| `U D L R B A` | no change |
| `A+B+Start+Select` held 4 frames | soft reset → save-slot screen (reset combo, not a cheat) |
| Save Slots: Left/Right ×24 | slot icon cycles (published Easter egg); no hidden screen |

**Novel code / bounds:** not applicable — no accepted-input set exists. By
contrast with a code system, there is no encoder to mint from and no checksum to
prove bounds against. The closest analogue, the puzzle-index domain, *was*
bounded: `SetPuzAttempts250` accepts only `1..250` (assert at `0x0814801E`),
and the three out-of-range TEST names cannot be selected in the skill/puzzle
select UI (only 25 Easy / 50 Medium entries are offered on a fresh save; Hard
75 and Special 100 are unlock-gated). The published unlock conditions were
verified as present strings, and a fresh save was observed to have Hard/Special
locked — i.e., the gates are real save-bit state, not bypassable input.

**Screens enumerated (15, each with a `gbAs` RAM savestate in
`/tmp/mrpants/states/`):** boot white, THQ splash, Rare splash, title,
name entry, save-slot select, main menu, skill select, puzzle title card, puzzle
gameplay, puzzle help, pause menu, puzzle fail, Options submenu, Scores, Art
Gallery, Save Slots. (Splashes and consecutive sub-screens count separately;
the full state files and matching `shots/*_c.png` crops are the RAM evidence.)

## 7. Validation evidence

- **Observed (emulator):** every screen in §3 reached with frame-accurate input;
  `KEYINPUT` `0x3FF`/`0x03F7` via debugger; 15+ savestates captured (raw RAM);
  Konami-family sequences had no effect; reset combo soft-resets to slot select;
  Left/Right Easter egg cycles slot icons; Hard/Special skill entries hidden on
  a fresh save; Art Gallery/Scores/Save Slots screens rendered.
- **Derived (disassembly / static):** input driver at `0x0813E048` and its only
  special branches; `SetPuzAttempts250` bounds `1..250`; puzzle-name table
  stride 11 and the three TEST names at 257–259; full 301-entry message table;
  name alphabet at `0x08160EF8` has no validator consumer.
- **Inferred (not fully exercised):** the narrator voice of the Save Slots
  Easter egg (audio disabled); whether the language-select screen has a trigger
  on this build (its strings exist but no menu path was found); the exact visual
  result of intentionally forcing the crash debugger (3rd party cheat indexes document it, but it
  is not reachable by controller input).

## 8. Unknowns

1. The `LANGUAGES` / `SELECT YOUR LANGUAGE` UI (`0x08160FE4`/`0x08160FE4` region)
   was never reached from any walked menu; it may be region/locale-gated or
   compiled in without a reachable caller on this Testing build. It is not a
   cheat surface.
2. The crash debugger appears only on a fault (per 3rd party cheat indexes); it was not triggered
   deliberately because doing so requires corrupting emulator RAM rather than
   controller input.
3. Narrator audio for the Save Slots Easter egg could not be heard with the
   dummy audio driver; only the visual icon cycling was verified.
4. The three `TEST` puzzle names are unreachable through the UI and the
   `1..250` save-index bound; whether a corrupted EEPROM could surface them was
   not tested (out of scope: memory editing, not an in-game cheat).

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for raw ROM disassembly.
- Python 3 + Capstone 5.0.7 (`capstone.CS_MODE_THUMB`) for PC-relative literal
  scans, BL-target scans and the KEYINPUT xref search.
- Custom helpers in `/tmp/mrpants/`: `mgba_daemon.py` (persistent mGBA
  `-d` pty controller on a Unix socket), `dbg.py`, `walk.py` (frame-accurate
  keypress helper), `state.py` / `loadstate.py` (savestate `gbAs` capture/reload),
  `key.py`.
- `strings -t x`, `xxd`, `grep`, `scrot` + ImageMagick `convert` (720×480 crop at
  `+152+171`), `xdotool` XTEST input on `DISPLAY=:319`.
- Web sources (archived): 3rd party cheat index cheats page (2026-02-03 capture), 3rd party cheat indexes Prerelease pages for It's Mr. Pants.

**Legal note:** no ROM bytes, graphics, music or extracted game assets are
reproduced in this report; only hashes, addresses, algorithms and the analyst's
own tooling/observations.
