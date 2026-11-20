# Sudoku Fever (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Sudoku Fever/Sudoku Fever.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `SUDOKU FEVER` |
| Game code / maker | `B3ZE` / `54` |
| Version / complement / checksum | `0x00` / `0x00` / `0x0061` |
| Entry word | `0xEA00002E` → branch to `0x080000C0` (stock crt0, not a patched cracktro) |
| Fixed byte `0xB2` | `0x96` (present) |
| MD5 | `836d614be32cd350de5e05a175db6da7` |
| SHA-1 | `02bbf5adad90b431da981785dbe10b273599153e` |
| SHA-256 | `e62d459fc6594c39e43f36dec0ee8a96cad3ee2f0cff96dceb3a19f76ddca739` |
| Developer / publisher | puzzle.tv / Global Star Software (Take-Two), 2006 |

The retail image is untouched (stock entry branch, non-zero header checksum). ROM content was treated strictly as data.

## 2. Executive summary

**There is no cheat-code surface in this SKU.** No password entry, no button-code matcher, no hidden/debug menu, and no unlockable flag exists. The game's "cheats" are ordinary, fully visible menu features: **Solve Puzzle**, **Reveal Square**, and the **Sudoku Solver** mode (enter any grid and have the game compute a solution). All are reachable from the normal START menu / title screen and require no code.

This is a **bounded negative**, not an absence of testing: every reachable screen was walked in mGBA, the complete ASCII UI text bank was decoded and matched to screens, every menu pointer table was dumped and counted, the 13-state screen dispatcher was enumerated, the key-input path was disassembled (simple edge detection, no sequence buffer), and the ROM was searched for password/debug/secret strings in ASCII, UTF-16LE/BE, `+0x20`-shifted ASCII, and XOR-`0xFF` — all with zero hits. Published-code recon found none (Cheat Happens explicitly says "We currently don't have any Sudoku Fever cheats or cheat codes for Game Boy Advance"; GameFAQs lists no cheats).

Reveal Square and Solve Puzzle were confirmed in-game with screenshots and savestate RAM diffs.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, `-3` scale.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
- Screen path:
  - Title → `Sudoku Classic` → difficulty (`Easy`/`Medium`/`Hard`/`Extreme`) → puzzle.
  - In puzzle: `START` → tabs `Game` / `Options` / `Preferences`.
  - `Game`: Reset Puzzle, Undo, Redo, **Solve Puzzle**, **Reveal Square**, Quit.
  - `Options`: Save, Music, Sfx, How To Play (2 pages).
  - `Preferences`: Pencil Marks, Character Select (Numbers/Letters/Symbols), Error Highlight, Background (Mountains/Pyramids/Liberty/Autumn/Tropical).
  - Title → `Sudoku Solver` → type (Classic/Eight/Mini/Junior) → blank grid → `START` → Solve Puzzle (Undo/Redo/Reveal greyed out).
- Button sequences tested on title: `L+R`, `L+R+Start`, `Start+Select`, Konami prefix (`↑↑↓↓←→←→B`), `A B A B`, `10×A`, `L+R+Start+Select`. The screen-state byte at `0x03000430` stayed `0x03` (title) or advanced to `0x04` only because a trailing `A` activated the highlighted menu item — no hidden screen.
- Savestates (`Shift+F1` save, `F1` load) were used for repeatable A/B RAM diffs; the `gbAs` PNG chunk was zlib-decompressed (guide §16.13).

## 4. Address map

| Region | Address | Meaning |
|---|---|---|
| ROM | `0x08000000` | Entry / crt0 |
| ROM | `0x08004988`–`0x08004990` | 3 tab-string pointers: Game, Options, Preferences |
| ROM | `0x08004E84`–`0x08004EB8` | 14 consecutive menu-item pointers (6 Game + 4 Options + 4 Preferences) |
| ROM | `0x08005254`–`0x0800525C` | Background pointers: Mountains, Pyramids, Liberty |
| ROM | `0x08005490`, `0x080054C8`, `0x080054D0`, `0x080054F8` | Autumn / Tropical pointers (individual code literal pools) |
| ROM | `0x080052E4`–`0x080052EC` | Character-set pointers: Numbers, Letters, Symbols |
| ROM | `0x080074FC`–`0x0800754C` | Type/difficulty header strings (CLASSIC, Easy, Classic, Select Sudoku Type, Select Difficulty) |
| ROM | `0x0801A0F0`–`0x0801A530` | Complete ASCII UI text bank (~60 strings; all decoded) |
| ROM | `0x0801A218` + `0x0A·n` | Game-type display names in 10-byte slots: CLASSIC, EIGHT, MINI, JUNIOR, SOLVER |
| ROM | `0x0801A24A` + `0x20·n` | Difficulty strings in 32-byte slots: Easy, Medium, Hard, Extreme, then the four `- Saved Game` variants |
| ROM | `0x0801A34A` + `0x0A·n` | Display names: Classic, Eight, Mini, Junior |
| ROM | `0x08006FA8` | Input poll: reads `0x04000130`, XORs with `0x03FF` (active-high), `BIC` for pressed edges |
| ROM | `0x08006FC8` | Literal `0x04000130` (KEYINPUT) |
| ROM | `0x08006FD8` | Screen-state dispatcher: copies held keys to `0x03003510`, indexes 13-state jump table |
| ROM | `0x08007008` | 13-entry jump table (12 real handlers; state 9 is a no-op idle) |
| ROM | `0x0812D960`+ | Puzzle-data bank: length-prefixed groups of `[0-9a-i]` puzzle records (see §6) |
| RAM | `0x03000430` | Screen-state byte (observed `0x03` title, `0x04` difficulty select, puzzle states higher) |
| RAM | `0x03004F60` / `0x03004F64` | Held / newly-pressed key masks (active-high) |
| RAM | `0x03003510` | Held-key copy used by screen handlers |
| RAM | `0x03000E6C` / `0x03000E70` | Next-state / current-state bytes used by handlers |
| SRAM | 512-byte `.sav` | Game save (created by playing; removed at cleanup) |

## 5. Algorithm

No password validator exists to reverse. The relevant algorithms are:

**Input handling (Derived — disassembly at `0x08006FA8`):**
```
held_active = ~KEYINPUT & 0x03FF
pressed     = held_active & ~previous_held
store pressed at 0x03004F64; store held_active at 0x03004F60
copy held_active to 0x03003510
state = *(u8*)0x03000430
if state <= 12: pc = jumptable[state]   // 0x08007008 + 4*state
```
Each screen handler reads the held copy and ANDs a single button mask (e.g. `1` = A at `0x08070E8`) with an edge check. No buffer, history, counter, or multi-button comparison exists anywhere in the input path.

**Puzzle data bank (Derived — byte structure at `0x0812D960`+):** records are runs of the 19-symbol alphabet `[0-9a-i]` followed by a small count byte `n`; the run length is `n × cells` where `cells ∈ {81, 64, 36, 16}` for the 9×9/8×8/6×6/4×4 grids. Examples: 162 chars + `0x02` = 2×81; 486 + `0x06` = 6×81; 384 + `0x06` = 6×64; 80 + `0x05` = 5×16. This is puzzle storage, **not** a user-entered code format.

## 6. Tables

**Menu inventories (Observed on screen + Derived from pointer tables):**

| Screen | Items | Count |
|---|---|---|
| Title | Sudoku Classic, Sudoku Eight, Sudoku Mini, Sudoku Junior, Sudoku Solver | 5 |
| Difficulty | Easy, Medium, Hard, Extreme | 4 (+4 `Saved Game` variants in text bank, not observed because no explicit save was made) |
| START → Game | Reset Puzzle, Undo, Redo, Solve Puzzle, Reveal Square, Quit | 6 |
| START → Options | Save, Music, Sfx, How To Play | 4 |
| START → Preferences | Pencil Marks, Character Select, Error Highlight, Background | 4 |
| Character Select | Numbers, Letters, Symbols | 3 |
| Background | Mountains, Pyramids, Liberty, Autumn, Tropical | 5 |
| Solver → type | Classic, Eight, Mini, Junior | 4 |
| How To Play (Solver) | 2 pages (A Exit, L/R Change Page) | 2 |

**Key masks (Derived):** active-high `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`. No multi-press mask table exists.

**Text bank:** ~60 strings, all plain NUL-terminated ASCII at `0x0801A0FC`–`0x0801A52B`; keywords `password`, `cheat`, `debug`, `secret`, `unlock`, `code`, `level select` — **zero hits**. RADriver audio diagnostics at `0x08012C1F`–`0x08012C2D` are the only other English strings.

## 6b. Enumeration

**Code space: empty. No code system exists in this ROM.** Consequently there is no alphabet, length, checksum, field layout, or validator to enumerate, and no novel code can be minted — this is a *proven* negative (guide §0.2 "negative results bounded"), not an untested one.

**Counts that bound the negative:**

| Search space | Count | Result |
|---|---|---|
| Reachable title modes | 5 | All entered; no hidden 6th entry |
| Title ring size (observed wrap) | 5 | `Down×5` returns to item 1 |
| Difficulty entries | 4 (+4 saved variants) | All strings accounted for in text bank |
| Screen-state dispatcher entries | 13 | 12 handlers, 1 idle; no hidden screen state |
| Menu-item pointers in table `0x08004E84` | 14 | Exactly matches 6+4+4 seen on screen |
| Background entries / Character-set entries | 5 / 3 | Exactly match screen; no unlabelled rows |
| UI strings in text bank | ~60 | Every one matched to a visible screen or dialog |
| Password/cheat/debug/unlock keyword hits (ASCII) | 0 | — |
| Same keywords in UTF-16LE, UTF-16BE, `+0x20` shift, XOR `0xFF` | 0 | — |
| Konami mask-sequence byte pattern `[40 40 80 80 20 10 20 10 02 01]` | 0 | No button-code table |
| Published codes (Cheat Happens, GameFAQs, Wikipedia, fan wikis) | 0 | Recon found none; nothing to verify |
| Button sequences pressed on title | 7 | No state change beyond normal menu activation |

**Developer-intended helpers (not codes, but the only cheat-like features):**
- **Reveal Square** — Observed: one empty cell was filled with the correct symbol; USED COUNT for that symbol incremented `4→5`. RAM evidence: savestate diff `ss1`→`ss2`, EWRAM `0x02000034` changed `0x1D→0x1E` (counter), plus IWRAM/EWRAM state updates.
- **Solve Puzzle** — Observed: a partially filled Classic/Hard grid was completed with a valid solution. RAM evidence: savestate diff `ss3`→`ss4`, 1,043 IWRAM bytes and 20 EWRAM bytes changed (pencil-mark/candidate flags at `0x03003521`+ cleared `0x01→0x00`; grid/solution state updated).
- **Sudoku Solver** — Observed: blank grid accepts arbitrary givens and computes a solution; Undo/Redo/Reveal are disabled in this mode.
- **Character Select / Background / Pencil Marks / Error Highlight** — cosmetic preferences, fully enumerated.

**Rejection bounds (the closest equivalent for a code-less game):** out-of-band button sequences were rejected — `L+R`, `L+R+Start`, `Start+Select`, Konami prefix, `A B A B`, `10×A`, `L+R+Start+Select` never produced a new screen or flag; only a final `A` on the title activated the highlighted normal menu item. No input path other than grid entry and menu selection reads the keypad.

## 7. Validation evidence

- **Observed** (screenshots in `/tmp/opencode/sudokufever/`): `s03_title`, `s06_classic_difficulty`, `s07_puzzle_easy`, `s08_pause_menu`, `s09_options_tab`, `s10_preferences_tab`, `s11_character_select`, `s12_background` (Symbols selected), `s15_bg_submenu`, `s25b_solver`, `s26_solver_grid`, `s27b_solver_menu`, `s28_howtoplay`, `s37_solve_confirm`, `s38_solved`, `s24b_konami`, `tc_lr`, `tc_konami_noA`.
- **Observed** (RAM): screen-state byte `0x03000430` = `0x03` on title, `0x04` on difficulty select; savestate diffs for Reveal Square and Solve Puzzle above.
- **Derived** (static): all string pointers, menu tables, input routine, 13-state dispatcher, jump table, puzzle-data bank structure.
- **Inferred**: the four `- Saved Game` difficulty variants at `0x0801A24A + 0x20·(4..7)` are reachable only after an explicit Save; they were decoded from the text bank but not displayed (no save was made before the final difficulty-menu check). This does not affect the code-surface conclusion.

## 8. Unknowns

- Exact decoding of the 19-symbol `[0-9a-i]` puzzle-data alphabet was not required for the cheat question; its record framing (length-prefix + cell count) was established, the per-symbol semantics were not.
- The four `Saved Game` difficulty rows were not rendered on screen (explicit Save was never selected during the walk).
- Only the Solver's 2-page HELP was paged; other puzzle types' HELP text was read from the text bank at `0x08012CD8`–`0x08012D5C` rather than paged individually.
- No attempt was made to modify SRAM or use an external cheat device; both are out of scope.

## 9. Tooling

- `mgba` 0.10.5 (`-3`, `-g`, `-d` tried), Xvfb `:316`, openbox, xdotool, scrot, ImageMagick `convert`.
- `arm-none-eabi-objdump -M force-thumb` for input/dispatcher disassembly; Capstone 5.0.7 for PC-relative literal scans.
- Python 3 scripts (in `/tmp/opencode/sudokufever/`): `ssread.py` (zlib-decompress mGBA `gbAs` savestate chunk, read state bytes), `key.sh`, `shot.sh`, `testcode.sh`, plus one-off pointer/string/keyword scans.
- ROM hashes with `md5sum`/`sha1sum`/`sha256sum`; `strings -t x`, `xxd`, `grep`.

**Cleanup:** my mGBA (PID 374977), Xvfb (369983) and openbox (369984) were killed by PID number; `Sudoku Fever.sav` and `Sudoku Fever.ss1`–`.ss4` were removed from the ROM folder, leaving only the `.gba` (and this report). No `pkill`/`pkill -f` was used.

**Legal note:** no ROM image or extracted copyrighted asset is reproduced here; only hashes, addresses, algorithms, and original observations are published.
