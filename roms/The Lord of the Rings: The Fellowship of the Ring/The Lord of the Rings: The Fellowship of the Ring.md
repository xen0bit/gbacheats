# The Lord of the Rings: The Fellowship of the Ring (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Lord of the Rings: The Fellowship of the Ring.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `UNIVERSLOTR` |
| Game code | `ALOE7D` |
| Maker code | `7D` |
| Version | `0x00` (Rev. 00) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0` — retail/crt0 image, not a patched cracktro) |
| MD5 | `644712a277e801997624cece31b661a9` |
| SHA-1 | `4b77ba458b593ca35166e9a9792792ac92e263df` |
| SHA-256 | `ef7529eacc8f68eb0df423e2d6e369ae5d29ee6f70c5d30cefd32c039ee325f0` |
| Engine string | `program code by stevej@wiped.net 25/07/2002 03:00` @ file `0x61A9C` (Wiped! Interactive) |
| Save | EEPROM, 8192-byte `.sav` created by mGBA; OPTIONS → ERASE SAVE GAME confirms battery save |

## 2. Executive summary

**No player-facing password, cheat code, button code, or unlockable exists in this SKU.** The game's
reachable surfaces are: title (NEW GAME / OPTIONS), OPTIONS (MUSIC, SOUND EFFECTS, ERASE SAVE GAME,
CREDITS, MAIN MENU), character select, and normal gameplay with an inventory/status/command pause
menu. No password-entry screen, no code alphabet, and no cheat-validator exists on any of them.

**A full developer debug menu *is* present but is unreachable from in-game input.** Its ASCII text
bank at `0x0805D000–0x0805DA10` and its renderer/dispatcher functions at `0x08007Exx–0x0800A6xx`
implement 11 screens (main HUD, entity list/data/script, maintask, world vars, object list, vars,
flags, debug toggles) with a 10-entry main menu. The debug task's entry point is `0x08007F2C`.
Evidence that it is dead/beta code (§16.3 case 2):

- **Zero** Thumb `BL` call sites to `0x08007F2C` in the entire 8 MiB (full ROM BL scan).
- Exactly **one** 4-byte reference to its Thumb pointer `0x08007F2D` — a data slot at file
  `0x5F5F4` (`0x0805F5F4`) embedded in a data table, not executable code.
- A software breakpoint at `0x08007F2C` **never fired** across an extensive input walk (title,
  options, credits, character select, intro cutscene, gameplay, all tested combos). A control
  breakpoint at the key-reader `0x08003064` fired immediately, proving the breakpoint mechanism.

The only global button combo in the game is the standard GBA soft reset (A+B+Select+Start held),
implemented at `0x08003098`. Forcing the debug task from the debugger was attempted; because the
task requires the game's live task manager/area state, an out-of-context call produced a white
screen (crash), not a usable menu. The debug screens are therefore enumerated **statically** below,
and the in-game negative is proven by counts + a live breakpoint.

## 3. How to reproduce

- mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `-3` scale, default SDL keymap
  (A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows).
- Boot → press Start → title `NEW GAME / OPTIONS`; OPTIONS has 5 items; NEW GAME → character
  select → gameplay (dialogue/cutscene → free roam).
- Input walk: every reachable menu item was selected and every screen screenshotted; 14
  simultaneous key combos were pressed on the title screen and 14 more in-game (L+R+Start,
  L+R+Select, L+R+A, L+R+B, L+R+Up/Down, Start+Select, Select+A/B, A+B, L+R+Start+Select,
  L+R+A+B, Select+Up, R+A, plus 6 in-game variants). No debug screen appeared.
- Debugger: `mgba -d` command-line debugger (`b/t 0x08007F2C`, `c`) used for the breakpoint
  negative; `b/t 0x08003064` as positive control.

## 4. Address map

| Address (ROM) | File off | Meaning |
|---|---|---|
| `0x08003064` | `0x003064` | Key reader: `ldrh` KEYINPUT `0x04000130`, `mvn`, mask 16-bit → active-high keys stored at `0x030008C0`; pressed `0x03000CE8`; previous `0x03000D80`. A\|B\|Select\|Start held → `0x0801FD14` (SoftReset, BIOS `svc 1`/`svc 0`). |
| `0x08007F2C` | `0x007F2C` | Debug main-menu task creator / entry point (Thumb; pointer `0x08007F2D`). |
| `0x08008028` | `0x008028` | Literal pool → main debug string table (`0x0805D028`, `0x0805D048`, … stride `0x20`). |
| `0x08008048` | `0x008048` | Debug action wrapper → `BL 0x0800A474`. |
| `0x08008054` | `0x008054` | Debug action (entity/area setter). |
| `0x08008DFC` | `0x008DFC` | Debug menu renderer: builds a 12-row menu, 20-byte record stride, reads selected index at struct `+0x20`. |
| `0x080097A0`–`0x08009878` | `0x0097A0`– | Debug menu action handlers (page up/down, select, back, toggles). |
| `0x08009C00`– | `0x009C00`– | Debug toggle helpers (`eor` bits `0x100`, `0x200` … into RAM word `0x03000E7C`). |
| `0x0800A3AC/3D8/474` | `0x00A3AC`… | Debug print/assert helpers — called 71× from normal game code (logging only, not activation). |
| `0x0805D000`–`0x0805DA10` | `0x05D000`– | Debug ASCII string bank (all screens). |
| `0x0805F5F4` | `0x05F5F4` | Data slot containing `0x08007F2D` (debug task Thumb pointer) — the only xref to the task. |
| `0x030008C0` / `0x03000CE8` / `0x03000D80` | — | EWRAM key state: current(active-high) / pressed / previous. |
| `0x03000E7C` | — | Debug toggle bitfield in EWRAM. |

## 5. Algorithm

There is no validator/algorithm to reverse — the "cheat surface" is a stateful debug overlay, not a
code system. The only input algorithm is the key reader:

```
keys = ~KEYINPUT & 0xFFFF                 # active-high: A=1 B=2 Sel=4 Start=8 Rgt=10 Lft=20 Up=40 Dn=80 R=100 L=200
pressed = keys & ~prev
prev = keys
if (keys & 0x000F) == 0x000F:             # A + B + Select + Start
    if [0x02000000] == 0: [0x02000000] = 1; SoftReset(0xFF)
```

No alphabets, mask sequences, checksums, or password generators exist in the image. Searches run:
literal known-code search (no candidate), `strings` keyword sweep over the full ROM, editable
ASCII search for password/cheat/debug/enter/invalid across all localized banks, Konami-code byte
patterns (active-high `u16`, active-low `u16`, packed `u8`/`u32`, and reversed) — all zero hits.

## 6. Tables

### 6.1 Reachable screens (all walked, screenshots in work dir)
Title (NEW GAME, OPTIONS), OPTIONS (MUSIC ON, SOUND EFFECTS ON, ERASE SAVE GAME, CREDITS, MAIN
MENU), erase-confirm, credits, character select, gameplay/dialogue, pause/inventory. No hidden or
unlabeled entry appeared on any of them.

### 6.2 Developer debug menu — static enumeration (strings @ `0x0805D000`+)
| # | Screen | Header string | Offset |
|---|---|---|---|
| 1 | Main HUD | `LoTR v20020616a - pre beta`, `X:xxxx Y:xxxx E:xx G:xx S:xx`, `Area xxx {} ~start Entry xx {}` | `0x5D028` |
| 2 | Main menu items | `~redraw map`, `~item list`, `~main tasks`, `~object list`, `~area data`, `~entity list`, `~debug toggles`, `~var list`, `~flag list`, `back` | `0x5D090`–`0x5DA08` |
| 3 | Entity list | `LOTR v2102 entity list page {}` | `0x5D128` |
| 4 | Entity data | `LOTR v2102 entity data page` | `0x5D1A8` |
| 5 | Entity script | `LOTR v2102 entity script page` | `0x5D408` |
| 6 | Maintask | `LOTR v2102 maintask` | `0x5D4C8` |
| 7 | World vars | `LOTR v2102 world vars` | `0x5D588` |
| 8 | Object list | `LOTR v2102 object list` | `0x5D608` |
| 9 | LOTR vars | `LOTR vars` | `0x5D6C8` |
| 10 | LOTR flags | `LOTR flags` | `0x5D708` |
| 11 | Debug toggles | `LoTR debug toggles`, `show stats / game control`, `~raster`, `~coord`, `~waypoints`, `~entran`, `~collide`, `back` | `0x5D948`–`0x5DA08` |

Menu renderers' literal pools: `0x08008028`, `0x080081B8`, `0x08008328`, `0x080084D8`,
`0x08008660`, `0x080087EC`, `0x08008968`, `0x08008AEC`, `0x08008CD4`, `0x08008FB8` (one per
screen). Text is plain NUL-terminated ASCII (not tile-index encoded — `strings` finds every label).

## 6b. Enumeration

**Code space / search space.** This SKU defines no password or button-code space. The relevant
space is the *activation* of the debug overlay:

- PDK held-combos from {A,B,Select,Start,L,R,Up,Down}: 14 distinct simultaneous combos on title
  + 14 in-game; a further 13 on-title combos including 3/4-key and soft-reset variants; boot-hold
  L+R for 6 s. **0/41 produced the debug screen.**
- Sequential codes: Konami-code family (4 encodings × 2 orders) — **0 hits in the 8 MiB image**.
- Password space: **none** — no entry UI, no alphabet, no validator, no literal code table.
- Reachable menu space: title 2 items, OPTIONS 5 items, character select, gameplay pause — **all
  walked; 0 hidden entries**.

**Validator/oracle counts.** Thumb BL references to debug task `0x08007F2C`: **0**. Direct
32-bit pointers to `0x08007F2D`: **1** (data slot `0x0805F5F4`). Live breakpoint at `0x08007F2C`:
**0 hits** after full input walk; positive-control breakpoint at `0x08003064`: **1 hit**. These
three independent counts bound the negative: no reachable input path invokes the debug task in
this build.

**Novel codes.** Not applicable — no code format exists to mint from, and the only discoverable
cheat surface (the debug menu) fails the reachability test. No code is claimed as accepted.
An out-of-context debugger call to `0x08007F2D` was attempted and produced a white screen (crash)
rather than a menu, consistent with dead beta code requiring live task-manager state; this is
reported as a *derived* observation, not an accepted in-game code.

**Bounds proven by rejection.** The only accepted global input predicate in the ROM is
`(keys & 0xF) == 0xF` (A+B+Select+Start) → soft reset; every other tested combo was rejected by
observation (no screen change, no debug flag, no breakpoint hit). The debug menu is therefore a
**bounded dead-feature negative**, not "not tested".

## 7. Validation evidence

- **Observed**: title/options/credits/character-select/gameplay screens (screenshots); 41 combo
  attempts with no debug screen; breakpoint at `0x08007F2C` never hit; control breakpoint at
  `0x08003064` hit immediately; forced PC-write crash.
- **Derived**: key-reader semantics and soft-reset predicate from disassembly at `0x08003064`;
  debug-menu screen tables and item strings from `0x0805D000`+; zero BL callers from full-ROM
  BL scan; menu renderer structure at `0x08008DFC`.
- **Inferred**: debug menu is leftover pre-beta code (build string `v20020616a - pre beta`) whose
  task was never wired into a reachable input path in the retail build. The data slot at
  `0x0805F5F4` is the only surviving xref.

## 8. Unknowns

- Whether the data table at `0x0805ECxx–0x080610xx` (records containing `0x0805F5F4`) is an
  area/script descriptor that some unreachable area would use to spawn the debug task; no retail
  input path reached it in this walk, and force-calling the task crashed, so this remains open.
- Exact purpose of the unrelated debug print/assert helpers (`0x0800A3AC/3D8/474`) called from
  normal code — logging only, not cheats.
- No web-published code list could be retrieved (search integration returned no results;
  GameFAQs returned HTTP 403), so "no published codes" is unverified externally — but the ROM
  contains no password/cheat surface under any encoding searched.

## 9. Tooling

`strings`, `xxd`, `grep`, Python 3 (struct/capstone scanners: `findptr.py`, `scanptr.py`,
`blfind.py`, `blmap.py`, `ldrscan.py`, `keyscan.py`, `combos.py`, `titlecombos.py`, `bp_test.py`,
`bp_verify.py`, `force3.py`), `arm-none-eabi-objdump -M force-thumb`, mGBA 0.10.5 (`-g` GDB stub
found unresponsive; `-d` command-line debugger used instead), Xvfb `:319` + openbox, xdotool,
scrot/ImageMagick. All work files under `/tmp/lotr fellowship/`.

No ROM or copyrighted assets are redistributed; only addresses, hashes, and findings are published.
