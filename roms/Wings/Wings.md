# Wings (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Wings/Wings.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title / code / maker | `WINGS` / `AWQE` / `5N`, version `0x00` |
| Entry branch | `0xEA00002E` (stock) |
| Header checksum | stored `0x0000`; complement byte `0x18`, expected `0x31` → header was rebuilt/edited |
| MD5 | `9003c10fd78cc0bb83c83cbbdbe03911` |
| SHA-1 | `9d50a2150ae6ee4aacb23b826344134b63f906c2` |
| SHA-256 | `4bf79da45469c20628121ec7b3cd98239bb1f3305de6529be057d99647755bf8` |

Exactly one Nintendo-logo hit (file `0x04`) — single image, not a multigame pack. Boot shows the
Cinemaware and Metro3D logos. The image is a **development/debug build**: a 50-entry process table
with surviving C function names, English/French/Spanish/German label banks, and two cheat-related
process records survive in ROM.

## 2. Executive summary

There is **no password, no button code, and no reachable in-game cheat menu in this build**. The
ROM does contain a complete, functional **developer cheat facility** — two cheat screens and a 14-field
**AI parameter editor** (life, speeds, reaction time, lock distances, fire distances, etc.) — but the
process records for both cheat screens are **orphaned**: static dispatch analysis shows no retail
input path can select either one. I reached and exercised them by writing the process-select global
from mGBA's built-in debugger (clearly labelled *debugger-forced*, not a controller path), enumerated
every field, minted a parameter combination that appears in no published list, and verified it in RAM.

The in-game surface reachable with a controller from a fresh save was walked: title → intro → main
menu (3 items) → campaign confirmation → intro text → flight → pause menu (1 item). No cheat entry
point, password field, or secret combination was found on any of them. Four web searches for
published Wings GBA codes returned no results, so the novel combination below is not from a list.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
  Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
* Controller walk: Start at title → hold through the cinematic → press A on the "PRESS START"/intro
  text → main menu. Main menu is **horizontal**: Right steps `Play campaign → Gallery → New campaign`;
  Left/Up/Down do not move it. "New campaign" → confirmation (No/Yes) → campaign intro → flight.
  Start in flight → "Pause Menu" with a single `Resume` entry.
* Debugger-forced access to the cheat screens (this is how the screens below were reached):
  1. Start `mgba -3 -d Wings.gba` from a pty; the core is paused at cycle 0.
  2. Issue `frame` ~300 times (the built-in `frame` command takes no count argument) to reach the
     intro process.
  3. Write the *next-process* global: `w/4 0x03005F4C 0x08039D08` for CheatProcess, or
     `w/4 0x03005F4C 0x08039D3C` for DogfightCheatProcess; advance a few frames, then `continue`.
  4. On DogfightCheatProcess, **Select** opens the AI parameter editor, **L** switches to
     CheatProcess, **Start** leaves the editor, **A** starts the selected mission.
* Savestate inspection: mGBA `.ss1` is a PNG with a zlib-compressed `gbAs` chunk; decompressing gives
  a 397,312-byte state with IWRAM at raw offset `0x19000`, so IWRAM address `0x03004470` is at raw
  `0x1D470`.

## 4. Address map

| Item | Address (ROM / RAM) | Evidence |
|---|---|---|
| Process record table (50 records) | `0x080399F0`–`0x0803A380` | Derived: records `{name[NUL-padded to 4], u32 selfPtr, 6 fn ptrs}` |
| CheatProcess record / ptr field | `0x08039CF8` / `0x08039D08` | Derived + observed (switch works) |
| DogfightCheatProcess record / ptr field | `0x08039D24` / `0x08039D3C` | Derived + observed |
| CheatProcess funcs | `0x08008489`, `0x08008779`(nop), `0x08008689`, `0`, `0`, `0x08008775`(nop) | Derived |
| DogfightCheat funcs | `0x08008CD1`, `0x08008C81`(nop), `0x0800877D`, `0`, `0`, `0x08008C7D`(nop) | Derived |
| Current / next / param / default process globals | `0x03005F48` / `0x03005F4C` / `0x03005F50` / `0x03005F54` | Observed in RAM and in `0x08031E9C` literals |
| Process-switch setter | `0x08031E9C(next, param)` | Derived |
| L-key handler (sets CheatProcess) | `0x08008980`; L check `0x08008C48`, call `0x08008C68` | Derived |
| AI param state machine | `0x08008CD1` (state 0 = mission select, 1 = editor) | Derived |
| AI parameter descriptor table | `0x086EC608`–`0x086EC754` (14 entries) | Derived |
| AI parameter live values | `0x0300446C`–`0x03004487` | Observed (savestate RAM read) |
| Param name strings | `0x0803F81C`–`0x0803F8CC` | Derived |
| Format strings | `0x0803F7FB` `"(%s%s  %d"`, `0x0803F808` `"%s%s  %f"` | Derived |
| Cheat-screen help strings | `0x0803AA40`–`0x0803AAEC` (`<A> start`, `<B> main menu`, `<L> main cheat`, `<SEL> AI Parameter`, `<START>`) | Derived |
| GodMode label | `0x0803B8EC` (localization bank `0x086EB...`) | Derived; no reachable menu using it found |
| Invalid-data / EEPROM strings | `0x0803C42C`–`0x0803C484` | Derived; used by `0x08008C84` error dialog |

## 5. Algorithm / pseudocode

```
# process dispatch (derived from 0x08031E9C and RAM globals)
next_process = 0x03005F4C        # written by 0x08031E9C(proc, param)
current      = 0x03005F48        # read by the frame dispatcher
set_process(proc, param):
    [0x03005F4C] = proc
    [0x03005F50] = param
    if proc == 0: proc = [0x03005F54]
    current = proc

# DogfightCheatProcess input handler 0x08008980
if key & 0x200:                  # L  (0x08008C48)
    [0x030044E4] = 2; set_process(0x08039D08, 0)   # -> CheatProcess (0x08008C68)
if key & 0x001:                  # A  (0x08008BD2)
    start_mission(campaign_index, mission_index, game_type)

# DogfightCheatProcess state machine 0x08008CD1
state = [0x0300241C]
if state == 0: handle_mission_select()       # 0x08008980
if state == 1: draw_ai_parameter_editor()    # 0x08008C84 + table 0x086EC608
if key & 0x004: state = 1                    # Select
if key & 0x008: state = 0                    # Start

# AI parameter descriptor entry (stride 0x20, derived from 0x086EC608..0x086EC754)
{ u32 name_ptr; u32 ram_addr; u32 min; u32 reserved; u32 max; u32 scale_type; u32 ... }
# editor: Down/Up select field, Right increments, Left decrements, Start exits.
```

## 6. Tables

### 6.1 AI parameter editor — complete field enumeration (14 entries)

| # | Label | RAM | Width | Default | Descriptor min/max (`0x086EC...`) | Displayed |
|---:|---|---|---|---|---|---|
| 1 | life | `0x0300446C` | u16 | 100 | 1 / 0xFF | `100` |
| 2 | minSpeed | `0x0300446E` | u8 | 23 | 1 / 0xFF | `23` |
| 3 | maxSpeed | `0x0300446F` | u8 | 23 | 1 / 0xFF | `23` |
| 4 | defaultSpeed | `0x03004470` | u8 | 23 | 1 / 0xFF | `23` |
| 5 | flapsTail | `0x03004471` | u8 | 12 | 1 / 0xFF | `12` |
| 6 | flapsWings | `0x03004472` | u8 | 12 | 1 / 0xFF | `12` |
| 7 | reactionTime | `0x03004474` | u16 | 6 | 6 / 600 (scale 6) | `0.09` |
| 8 | targetLockDist | `0x03004476` | u16 | 5000 | 50 / 20000 | `5000` |
| 9 | warnCrashDist | `0x03004478` | u16 | 3000 | 50 / 20000 | `3000` |
| 10 | lockCone | `0x0300447C` | u16 | 56 | 5 / 2048 (scale 9) | `5.03` |
| 11 | fireDist | `0x03004480` | u16 | 4000 | 100 / 20000 | `4000` |
| 12 | shootTime | `0x03004482` | u16 | 30 | 6 / 600 (scale 8) | `0.50` |
| 13 | shootHit | `0x03004484` | u16 | 128 | 3 / 256 | `0.50` |
| 14 | idleTime | `0x03004486` | u16 | 300 | 26 / 2560 (scale 8) | `5.00` |

Down/Up wraps after `idleTime`. Values are live bytes in IWRAM; the descriptor min/max are *not*
enforced by the editor (see §6b bound test).

### 6.2 Screens and their literal text

* CheatProcess (`0x08039D08`): `*** ALLIES ***`, `Campaign 1`, `Mission 1`, `Game type:`,
  `3D Dogfight`, `(Mission: 1)`, `<A> start`, `<B> main menu`.
* DogfightCheatProcess (`0x08039D3C`): same header but game type on one line, plus
  `<A> Start`, `<L> main cheat`, `<SEL> AI Parameter`.
* AI editor: 14 label/value pairs, `<START>` prompt bottom-right.

## 6b. Enumeration

**Space definition.** This game has no alphabetic password or code table. The developer-intended
cheat surface is a fixed 14-field parameter editor over RAM bytes/u16s; the two cheat screens select
campaign (0–9), mission (0–9) and game type (3D Dogfight / Strafing / Bombing) — the selector loops
were read at `0x08008489`–`0x0800852E` (indices clamped to `0..9`) and at `0x08008980`. Total
representable parameter states are the product of the 14 field ranges above; no published list of
any of these values exists for this SKU (four web searches returned no results).

**Novel combination generated and entered (no published list).** Through the AI editor on the
debugger-reached DogfightCheatProcess screen I set
`minSpeed = 30, maxSpeed = 31, defaultSpeed = 15` (shipped defaults are `23, 23, 23`).
Evidence: screenshot `/tmp/wings/novelc.png`; savestate RAM readback
`0x0300446E = 0x1E (30)`, `0x0300446F = 0x1F (31)`, `0x03004470 low byte = 0x0F (15)`.
All three values were produced by controller input (D-pad) on the game's own editor screen; the
screen was opened by a debugger-forced process switch because no retail path exists (below).

**Bounds proven by rejection / clamping tests.**

* Lower bound: 25 × Left on `defaultSpeed` drove it to `0`; the UI displayed `0` and RAM read
  `0x03004470 = 0x00` (screenshot `/tmp/wings/boundc.png`). The descriptor's declared
  minimum is `1`, so the editor does **not** enforce that minimum — a real, bounded finding.
* Upper bound: a 3-second Right hold incremented `defaultSpeed` from 0 to 19
  (`/tmp/wings/upperc.png`); no clamp was reached within the tested range.
* Wrong-screen input: pressing L on CheatProcess (the screen reached by L from DogfightCheatProcess)
  produced no change (`/tmp/wings/cpLc.png`) — the L handler belongs only to
  DogfightCheatProcess, confirming the two screens are distinct code paths.

**Bounded negative — retail reachability (counts).**

* 50 process records in the table at `0x080399F0`–`0x0803A380`.
* `CheatProcess` ptr field `0x08039D08` occurs as a literal **exactly 1×** in code: `0x08008C78`,
  inside function `0x08008980`.
* Function `0x08008980` has **exactly 1** BL caller: `0x08008CE4`, inside DogfightCheatProcess's
  init `0x08008CD1`.
* `DogfightCheatProcess` ptr field `0x08039D3C` has **0** external literal references (only its own
  self-pointer in the record).
* Therefore neither cheat screen can be selected by any controller input in this build: they are
  **dead/orphaned code**, not a gated feature with a discoverable key. This is a bounded
  "no system reachable" result, not "not tested".

**Screen walk enumeration (Retail).** Title `PRESS START`; cinematic + Wright-Brothers text;
main menu items exactly `Play campaign`, `Gallery`, `New campaign` (Right-steps, leftmost/rightmost
clamp); `New campaign` confirmation `No/Yes` with the erase warning; campaign intro text; briefing;
in-flight HUD; Pause Menu with exactly `Resume`. `Gallery` was seen as a menu label but not entered;
the full campaign/pilot/post-mission tree was traversed only far enough to confirm no cheat entry.
No password prompt, code table, or cheat option exists on any walked screen.

## 7. Validation evidence

* **Observed** — emulator screenshots (`boot_crop.png`, `m2c.png` title, `m4c.png` main menu,
  `p1c.png` pause, `cp0c.png` CheatProcess, `dog0c.png` DogfightCheatProcess, `dogSelc.png` AI editor,
  `novelc.png`, `boundc.png`, `upperc.png`); savestate RAM reads of `0x0300446C`–`0x03004487`;
  live process pointer `0x03005F48` reading `0x08039ACC` (Intro), `0x08039D08`, `0x08039D3C`
  after each forced switch.
* **Derived** — process record layout; L/A/Select/Start key masks and handler addresses; process
  globals; AI descriptor table; L-handler call graph; bounded-negative counts.
* **Inferred** — the `GodMode` label at `0x0803B8EC` is a menu item in a localization bank, but no
  reachable menu using it was found; whether a different retail SKU or a prototype build wires the
  cheat screens cannot be determined from this single image.

## 8. Unknowns

* Whether any later campaign state (after clearing a campaign / unlocking Gallery content) exposes
  a route to the cheat screens — the process-pointer call graph says no, but not every late-game
  screen was played to completion.
* Effect of each AI parameter on actual airborne AI behaviour was not played out; only the editor
  state and RAM writes were verified.
* `GodMode`'s owning menu and effect; EEPROM error strings suggest a save path not exercised here.
* Header complement mismatch (`0x18` vs expected `0x31`) indicates a modified header; the original
  retail revision could not be confirmed from the image alone.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `strings -t x`, Python (`struct`, `zlib` for savestate RAM),
`capstone` (Thumb disassembly scans), `arm-none-eabi-objdump -M force-thumb`, mGBA 0.10.5 with
Xvfb `:317` + openbox, `xdotool` XTEST input, `scrot`/ImageMagick screenshots, mGBA built-in `-d`
debugger driven through a Python `pty` (`frame`, `r/4`, `w/4`, `continue`). All scripts and evidence
were kept in `/tmp/wings/`; no ROM or extracted assets are published here.

**Cleanup:** all spawned processes (Xvfb `:317`, mGBA debugger sessions) terminated by PID;
`Wings.sav` and `Wings.ss1` removed from the ROM folder.
