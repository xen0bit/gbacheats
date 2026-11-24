# Super Dodge Ball Advance (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Super Dodge Ball Advance/Super Dodge Ball Advance.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `SUPERDODGE` |
| Game code | `ADFEEB` (maker `EB`) |
| Revision | 0x00 (`file(1)`: "ADFEEB, Rev.00") |
| Fixed byte 0x96 | present at 0xB2 |
| Entry branch | `0xEA00002E` → stock crt0 at `0x080000C0` (no craketro/trainer patch) |
| MD5 | `816db888cae935e71a74a4ae6c461bee` |
| SHA-1 | `5fc95814ea7695d1301df4b545614a1ffae95218` |
| SHA-256 | `16e3d35c3282210b324295e4f836c86fcd8151d03cfd39952e32a6e1471946e1` |

Header checksum at 0xBE–0xBF is `0xC800`; complement byte check is unremarkable. The image is a
normal retail US revision, not a rebuilt/Scene-patched image.

## 2. Executive summary

**This ROM contains no in-game cheat-code system.** It has no password entry screen, no password
validator, no published or hidden button code, and no hidden/debug menu. The "cheats" published
for this title are exclusively **progression-gated save-bit unlockables** (Dream Teams A–E and
Special Championship Mode) plus out-of-scope Action Replay/GameShark codes. Publishing recon
(3rd party cheat indexes) returned only unlock conditions and
AR codes — no passwords or button sequences.

The negative is **bounded, not merely "not found"**: the entire 4 MiB image was scanned for cheat
keywords in three encodings (0 hits), all 287 Ghidra-defined strings were inventoried (0 cheat/
password/debug labels), all 216 candidate button-mask runs were classified by region (0 in code;
the single code-region hit is a 32-bit data constant inside a 15×10 team-stats table, verified by
disassembly), the complete ASCII font/text banks were decoded (no encoded password prompts), and
the only three KEYINPUT literals were disassembled (standard input handling, no secret matcher).
Nine reachable screens were walked in mGBA with screenshots.

The one positive result is the unlockable set, which lives in SRAM (`DODG` magic, 32 KiB) and is
written by the game's progression logic, not by any controller input path reachable from the
screens examined. Per guide §16.18 this is a save-bit unlock, **not** a code, and is reported as
such.

## 3. How to reproduce

- Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:318`, `mgba -3 <rom>`.
- Keymap (mGBA SDL default): A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`,
  Select = `BackSpace`, D-pad = arrow keys. Hold 50–80 ms (150 ms double-steps menus).
- Boot path observed: title (`START`) → A → DATA 1/2/3 slot select → A on a slot → story dialogue
  (many A presses) → demo/first match → manager introduction → team setup
  (Position/Formation/Data/Player Name/Team Name/Accept) → Championship match.
- Start during a match shows only a static `PAUSE` overlay (no menu options).
- No screen in this path presents a code/password field. Savestate slot 1 was kept at the
  data-slot screen to make each experiment a single `F1`.

Screenshots retained in `/tmp/superdodgeball/`: `shot_boot.png` (title),
`shot_data1_b.png` / `n03_after_a.png` (data-slot select), `w02_story_5.png` (story),
`w03_after_story.png` / `i02_ff60.png` (match), `w05_start_demo.png` (pause),
`f01_ff25.png` (manager intro), `g2_progress.png` (team setup).

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`).

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000`–`0x080000BF` | Header / ARM crt0 entry | observed bytes |
| `0x08000408`, `0x08000474` | KEYINPUT (`0x04000130`) literals in crt0 | literal scan |
| `0x0800F570` | KEYINPUT literal in input/config handler | literal scan + Thumb disasm `0x0800F500`–`0x0800F700` |
| `0x08011710` | Save-structure init; copies 6-byte `DODGE\0` magic into a heap struct | Ghidra `FUN_08011710` + xref to `0x08058C24` |
| `0x08011804`, `0x08011B78` | Save/UI state machines (SRAM header + menu state fields) | Ghidra decompilation |
| `0x0801B504` | 32-bit data constants (`0x00002020`, `0x00020080`, `0x00020088`) in a 15×10 team-stats table (not a button sequence) | Thumb disasm `0x0801B51C`: loops `r5=0..14`, `r3=0..9` |
| `0x080563A0`–`0x080564E4` | Engine debug-log strings (TCB scheduler, `err set_signal()`) | Ghidra string inventory |
| `0x08056524`–`0x08056550` | `SRAM ORG CRASH`, `SRAM ALL CRASH`, `SRAM CLEAR`, `01 01 04 01` | Ghidra string inventory |
| `0x08058C24` | `"DODGE"` — save magic string referenced by `FUN_08011710` | Ghidra xref `0x08011786` |
| `0x08058CD8`–`0x08059E34` | Plain-ASCII English dialogue / mode descriptions | `strings -t x`, Ghidra strings |
| `0x0805C4AC`, `0x0805C590` | 80-byte font glyph-remap tables | raw byte dump |
| `0x0805C5E0`, `0x0805C670` | 80-byte tile-index→ASCII font tables | raw byte dump |
| `0x0858B80`–`0x0858CD8` | Pointer table into graphics/text banks (0x0802/0x0819/0x0836 targets; no strings) | raw byte dump |

SRAM save (`.sav`, 32 KiB): magic `DODG` at 0x00; header/state fields 0x8C–0x9F; 15 team records
at 0xA0 with 0x90-byte stride (8× stat pairs + position/formation bytes each).

## 5. Algorithm

There is no code validator to reverse. The relevant algorithms are:

- **Save validation** (`FUN_08011710` / `FUN_08011804`): initialises a heap struct of size 0xABC,
  writes a 2-byte size field `0xABC`, copies the 6-byte literal `DODGE\0`, and on later runs
  verifies the same `D O D G E` prefix before accepting the save (`FUN_08011804` compares
  `local_c[0..4]` against `'D','O','D','G','E'`). This is a **save-format magic check, not a
  password validator** — its input is the SRAM buffer, never a user-typed field.
- **Font/text decoding**: dialogue is plain ASCII with control glyphs `$` (number), `#`
  (conjunction), `&`/`*` (punctuation) substituted at render time via the remap tables in §4.
  No substitution produces a code alphabet.

## 6. Tables

### 6.1 Complete string-inventory classification (Ghidra, 287 strings)

| Class | Count | Examples |
|---|---|---|
| Header title | 1 | `SUPERDODGE` |
| Engine/OS debug logs | 13 | `NO MORE TCB in _reg_last`, `SRAM CLEAR`, `err set_signal()` |
| Save magic | 1 | `DODGE` (`0x08058C24`) |
| Dialogue / mode / manager text | ~228 | `This is the Championship Mode!`, `Dream Team.`, `VERSUS`, `Score`/`Catch`/`Throw` |
| libc strings | 5 | `0123456789abcdef`, `bug in vfprintf: bad base`, `_sbrk: Heap and stack collision` |
| Tile/graphics data misread as strings | ~39 | `UUUUffffffff...` patterns at 0x080EAC59+ |
| **Password / cheat / debug-menu strings** | **0** | — |

### 6.2 Keyword scan (whole 4 MiB, 3 encodings)

22 keywords (`PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `WARP`, `UNLOCK`, `MASTER`, `GALLERY`,
`SOUND TEST`, `MUSIC TEST`, `BGM TEST`, `LEVEL SELECT`, `STAGE SELECT`, `EXTRA`, `CODE`, `ENTER`,
`INVALID`, `CORRECT`, `CONGRATULATIONS`, `TROPHY`, `HIDDEN`, `DODGE`-adjacent variants) × 3
encodings (ASCII, ASCII+0x20, UTF-16LE) → **0 hits** (apart from the known `DODGE` magic itself).

### 6.3 Alphabet scan

Six standard password alphabets searched (`A-Z`, `0-9A-Z`, `a-z`, `A-Z0-9`, `23456789`,
`BCDFGHJKLMNPQRSTVWXYZ`) → only four `23456789` substrings, all inside the ASCII font table
(`0x0805C532`, `0x0805C600`) or a libc table (`0x08CC942`, `0x08CC95E`). No password alphabet.

### 6.4 Button-mask scan

216 runs of ≥3 consecutive u16 values from the GBA key-mask set
`{0x001,0x002,0x004,0x008,0x010,0x020,0x040,0x080,0x100,0x200}` (and active-low complements):
1 in code (`0x0801B504`, shown in §4 to be data), 16 in the text/font bank, 51 in graphics,
148 in compressed/later data. No run has the structure of a cheat sequence table.

### 6.5 Unlockable set (published + ROM-corroborated)

| Unlockable | Condition (3rd party cheat indexes) | ROM corroboration |
|---|---|---|
| Special Championship Mode | Beat Championship Mode | `0x08059C20` "Special Championship mode&" |
| Dream Team C / Iron Men | Beat Championship Mode (first completion) | `0x08059320` "Dream Team." |
| Dream Teams B/A/D/E (Rockets, Shooters, etc.) | Beat Special Championship 1st/2nd/3rd/4th time | `0x08059550` "Congratulations!", `0x0805932C` "Your next opponent is a" |
| Initial 4 Dream Teams | Beat first team twice in 1st place, then keep playing Special Championship | `0x08059C54` "Do you have what it takes to win the championship?" |
| Team manager (Sara/Alys/Jenny/Masumi) | Random on save initialisation | strings at `0x080599E4`/`0x08059A04`/`0x08059A24`/`0x08059B8C` |

Save evidence: fresh vs progressed `.sav` differ in only 4 bytes
(`0x8C: 03→02`, `0x90B: EB→EA`, `0x1BB0: 03→02`, `0x242F: EB→EA`) — progression state is a
handful of header/record bytes, consistent with save-bit unlockables and inconsistent with a
code-entry buffer.

## 6b. Enumeration

**Code-space definition:** none exists. There is no alphabet, length, checksum, field width, or
code table to enumerate. The search space actually checked is therefore the whole ROM:

| Space checked | Size | Result |
|---|---|---|
| Raw bytes, 3 encodings × 22 cheat keywords | 4,194,304 × 3 × 22 comparisons | 0 cheat-related hits |
| Ghidra-defined string inventory | 287 strings | 0 cheat/password/debug labels; fully classified in §6.1 |
| Password alphabet literals | 6 patterns × 4 MiB | 0 password alphabets (font/libc only) |
| Button-mask runs | 4 MiB scanned at 2-byte alignment; 216 candidates | 0 in executable code; 1 code-region candidate disproved by disassembly |
| KEYINPUT sites | 3 literal occurrences, all disassembled | 0 secret-combination matchers |
| Font/tile text banks | `0x08058CD8`–`0x08059E34` + 4 remap tables | 0 encoded password prompts; all text decoded as dialogue/UI |
| Reachable screens | 9 distinct screens walked (§3) | 0 code-entry surfaces |

**Novel code / mint-and-enter:** not applicable — there is no validator to mint a code for, and
no published code list exists for this SKU (all published "cheats" are progression unlocks or
out-of-scope AR codes). Per the task's alternative, this section gives the bounded negative with
counts above.

**Bounds proven by rejection:** no rejection test could be performed because no entry UI exists.
This is reported as an absence of the surface, not as an untested code.

**Unlockable enumeration (the positive set):** 6 unlockable items are enumerated in §6.5 with
their published conditions and ROM string addresses. Their setter is the game's progression logic
(save written after matches); no controller-input path to those state bytes was found on any
walked screen. Five Dream Team bytes sit at save offset 0x90–0x94 (observed value `03` on both
fresh and progressed saves), but completing a championship was not performed, so their exact
bit/byte semantics remain **unknown** (§8) rather than claimed.

## 7. Validation evidence

- **Observed**: 9 screens walked in mGBA with screenshots (§3); save file written by the emulator
  and diffed; `strings`/`xxd` byte dumps; Ghidra string/function inventories.
- **Derived**: Ghidra decompilation of `FUN_08011710`/`FUN_08011804` proves the `DODGE` check is
  a save-magic comparison, not a user-code validator; `objdump -M force-thumb` at
  `0x0801B504` proves the only code-region "button-mask run" is data constants.
- **Inferred**: unlockable conditions are taken from published sources and corroborated by
  mode-description strings, but the actual win→flag write path was not executed end to end.

## 8. Unknowns

- Config, Initialize, Versus and Exhibition screens were not reached; they appear gated behind
  completing the introductory Championship flow (guide §16.3: gated feature, not dead code).
- Exact save-byte/bit encoding of the five Dream Team unlock flags and the Special-mode flag
  (candidate region 0x8C–0x9F) was not proven by executing a full unlock.
- The 15×10 table at `0x0801B50C` is interpreted as team stats from its loop shape; individual
  column meanings were not decoded.
- No exhaustive keyboard-combination test was run on every screen; the negative rests on the
  static KEYINPUT-site scan plus the screen walk.

## 9. Tooling

- `strings -t x -n 4/5/6`, `grep -abo`, `xxd`, Python 3 byte-pattern scanners
  (`/tmp/superdodgeball/scan.py`).
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
- Capstone 5.0.7 (available; final scans used objdump/REA instead).
- Ghidra 12.1.4 via REA MCP (`open_binary` raw-binary/ARM/0x08000000; `binary_overview`,
  `list_strings`, `list_procedures`, `xrefs`, `procedure_info`, `procedure_pseudo_code`,
  `close_binary`).
- mGBA 0.10.5 under Xvfb `:318` + openbox; `xdotool` XTEST input helper
  (`/tmp/superdodgeball/sdb.py`); `scrot` screenshots.
- GDB stub (`-g`) was attempted but returned protocol packet errors (guide §16.13); analysis
  used static evidence and save-file diffs instead.

## 10. Legal note

No ROM image, extracted graphics, or copyrighted assets are redistributed here. Only hashes,
addresses, algorithms, and the analyst's own scan scripts/screenshots are recorded.
