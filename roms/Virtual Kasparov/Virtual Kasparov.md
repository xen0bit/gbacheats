# Virtual Kasparov (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Virtual Kasparov/Virtual Kasparov.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `VIRTKASPAROV` |
| Game code / maker | `AVKE` / `60` |
| Version | `0x00` |
| Entry word | `0xEA00002E` — stock ARM `b 0x080000C0` (not a cracktro) |
| MD5 | `68d45d576023082a099526d5b384dd1c` |
| SHA-1 | `f3b416a921b650cfd5c6a7f9cc6060df0f6b82ed` |
| SHA-256 | `490e24e0137e01d73ea07a0e07c8d5344b18adf6e15556e182bd671e9b465496` |

Header note (**Derived**): complement byte at `0xBD` is `0x18`; the value that makes
`sum(0xA0..0xBC)+comp==0` is `0x31`, and the 16-bit header checksum at `0xBE` is
`0x0000`. Per guide §16.1 this marks a rebuilt/edited header, but the entry branch is
stock and no appended trainer or cracktro was found. This is the `[!]` dump matched by
the published CRC32 `815B722F`.

## 2. Executive summary

**This GBA SKU has no in-game cheat code, password, or debug menu.** The result is a
*bounded negative*, not an absence of effort: the complete UI text table, the whole
4 MiB string/symbol space, all `KEYINPUT` references, and every reachable screen were
enumerated with counts (§6b). There is no code-entry surface, no alphabet/validator,
no button-code matcher, and no developer debug gate.

Everything the web calls a "cheat" for this title is one of three other things:

1. **External cheat-device codes** (GameShark/CodeBreaker: master code
   `0000850A 000A / 10000748 0007`, clock freezes at `0x0200E6D4` / `0x0200E7A4`).
   Explicitly **out of scope** and not in-game codes.
2. **Story-mode unlocks** — 23 opponents and 3 regions unlocked by beating specific
   opponents (save-bit progression, guide §16.18), not entered by any controller input.
3. **"Extra rook"** — not a code at all: it is the developer-intended **CHANGE POSITION
   board editor** (pause → CHANGE SETUP → CHANGE POSITION), which lets the player place
   an arbitrary piece (including a second rook) on any square. Reproduced in emulator
   with RAM/screen evidence (§7).

The only button combination with a special effect found in code is
`A+B+Select+Start` → soft reset (`FUN_0804857C`, `0x0804857C`); ordinary controls are
`Select` = pause, `Start+Select` = quit to main menu, `L+R` = pause/quit context action.

## 3. How to reproduce

- Emulator: mGBA 0.10.5, `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`, `mgba -3 -g <rom>`.
  Keymap verified by reading KEYINPUT from an uncompressed mGBA `.ss1` state
  (state offset `0x530`, value `0x3FF` idle):
  `A=x, B=z, L=a, R=s, Start=Return, Select=BackSpace, D-pad=arrows`.
- Hold keys 120–200 ms; short taps are missed.
- Screen path (English):
  `License → Titus splash → title → Start → main menu (STORY/QUICK START/VERSUS/TUTORIAL/OPTIONS)`.
- `QUICK START → A` → opponent carousel (31 names, 3 time controls) → `A` → board.
- `Start` then `Select` → **PAUSED** (7 items) → `CHANGE SETUP` (8 items) →
  `CHANGE POSITION` → board editor.
- In the editor: D-pad moves the 64-square cursor, **A places** a piece, **L cycles**
  the piece type, **R clears** the square. Place a rook on e4 while a1/h1 rooks remain →
  extra rook (screenshot `cycL_06.png`).
- Save artifacts (`Virtual Kasparov.sav`, `.ss1`) were created by mGBA in the ROM folder
  during testing and were **removed** at the end (cleanup §below).

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x080000C0` | Real crt0/main after stock entry branch | Derived |
| `0x08000678` | Main game loop; decompiled | Derived (REA) |
| `0x08000690` | literal `0x04000130` (KEYINPUT) in main loop | Derived |
| `0x08000834`, `0x08002358`, `0x0800EBBC`, `0x0801DF50` | other four KEYINPUT literals | Derived |
| `0x0804857C` | soft-reset helper (`A+B+Select+Start` → `swi 1; swi 0`) | Derived (REA) |
| `0x0804F758` | opponent-name table, 31 NUL-terminated names | Observed |
| `0x0805F000..0x0805FDFx` | localised UI text bank (5 languages) | Observed |
| `0x08029A3C` | master UI string-pointer table, 5 language blocks × 72 slots | Observed/Derived |
| `0x08342560` | tutorial script "@Code des symboles" (FEN notation commands) | Observed |
| `0x0E000000` | SRAM, 512 bytes, 3 save slots at `+0x00`, `+0xA0`, `+0x140` | Observed |

No validator, alphabet table, checksum routine, code table, or debug flag word exists.

## 5. Algorithm

Not applicable — there is no code/password algorithm to reverse. The nearest
developer-intended systems are:

- **Menu engine**: screens index the pointer table at `0x08029A3C` by language and item
  number; item counts were confirmed by walking each ring (§6b).
- **Position editor**: direct board mutation — D-pad selects one of 64 squares, A writes
  the currently selected piece id, L/R move that id through the piece set (including
  empty). There is no legality or piece-count check on placement; this is the mechanism
  behind the published "extra rook" trick.
- **Story unlocks**: save bits in the 512-byte SRAM record, set by match-win paths;
  no controller input path writes them (consistent with guide §16.18).

## 6. Tables

### 6.1 Master UI table (0x08029A3C)
Five consecutive language blocks (EN, FR, ES, DE, IT) of 72 pointer slots each
(360 slots total). English block starts `0x08029A3C`; French `0x08029B5C`; Spanish
`0x08029C7C`; German `0x08029D9C`; Italian `0x08029EBC`. Complete label inventory:
`GAME SELECT, MAIN MENU, OPTIONS, LANGUAGE SELECT, PAUSED, SAVE LOAD GAME, SAVE GAME,
LOAD GAME, CHANGE SETUP, QUIT GAME, STORY, QUICK START, VERSUS, TUTORIAL, MUSIC,
EFFECTS, LANGUAGES, CREDITS, ENGLISH, FRAN]AIS, ESPA<OL, DEUTSCH, ITALIANO, CHESSBOARD,
CHESSBOARD SELECT, 2D VIEW, 3D VIEW, BEGINNER'S MODE, INDICATORS, CLOCKS, YES, NO, SAVE,
LOAD, CHANGE POSITION, WHITE/BLACK TO MOVE, WHITE/BLACK KINGSIDE/QUEENSIDE, OK, CANCEL,
MULTIPLAYER MODE, SINGLE PAK LINK, DRAW, WHITE/BLACK WINS, ROTATE BOARD, PLEASE WAIT...,
CONNECTION LOST, WHITE, BLACK, CUSTOM, DEFENSIVE, AGRESSIVE, CARELESS, CONCENTRATE,
AMATEUR, MASTER, BACK`. **Keyword hits for PASSWORD / CHEAT / DEBUG / SECRET / UNLOCK /
ENTER CODE / KEY / CODE: 0 across all 360 slots.**

### 6.2 Screen item counts (walked)
| Screen | Items | Observed |
|---|---|---|
| Main menu | 5 | STORY, QUICK START, VERSUS, TUTORIAL, OPTIONS |
| OPTIONS | 4 | MUSIC, EFFECTS, LANGUAGES, CREDITS (Down×6 wraps) |
| LANGUAGE SELECT | 5 | EN, FR, ES, DE, IT |
| PAUSED | 7 | CHESSBOARD, BEGINNER'S MODE, INDICATORS, CLOCKS, ROTATE BOARD, CHANGE SETUP, QUIT GAME |
| CHANGE SETUP | 8 | CHANGE POSITION, WHITE TO MOVE, 4× castling toggle, OK, CANCEL |
| Position editor | 64 squares | arbitrary piece placement |
| Opponent carousel | 31 + 3 | 31 names at `0x0804F758`; time controls `5/10/20 Mn` at `0x0804F984` |
| Save/name screen | 3 slots | inline name edit, A clears to `-`, B cancels |

### 6.3 Button semantics
| Input | Effect | Evidence |
|---|---|---|
| `A+B+Select+Start` | soft reset (`0x0804857C`) | Derived (REA pseudocode) |
| `Select` (in game) | opens PAUSED | Observed |
| `Start` then `Select` | opens PAUSED (with black transition frame) | Observed |
| `Start+Select` | quit current game → main menu | Observed |
| `L+R` | pause/quit context action; title combos do nothing but advance splash | Observed |

### 6.4 SRAM (512 bytes)
`0x00..0x9F`, `0xA0..0x13F`, `0x140..0x1DF` = three game slots. Names are stored as
character-reversed UTF-16 (` WENEMAG` = "NEW GAME"), a known save-encoding quirk
(guide §16.4). Progression region is padded `0xFF`; slot trailers at `0xA6` (`EE EE`)
and `0x146` (`DD DD`) look like checksums/markers.

## 6b. Enumeration

**Code space: empty.** There are zero in-game codes, zero password alphabets, zero
validators and zero debug menus. There is therefore no code to mint and no checksum to
bound; the required §0.2 deliverable is discharged as a *bounded negative with counts*.

Counts that bound the negative:

| Search space | Count | Result |
|---|---|---|
| Master UI string slots (5×72) | 360 | 0 code/password/debug/secret/unlock/cheat labels |
| REA string objects | 1,904 | only 2 "code" strings, both chess-notation glossary ("CODE DES SYMBOLES", "CODE VAN DE SYMBOLEN"); 1 tutorial FEN script block |
| REA procedures | 689 | 0 names matching debug/cheat/code/password/secret |
| Literal `DEBUG`/`PASSWORD`/`CHEAT`/`SECRET`/`UNLOCK`/`ENTER CODE` in 4 MiB | 0 hits each | no hidden entry text in any encoding searched (ASCII, +0x20 noted but no such bank found) |
| `KEYINPUT` (`0x04000130`) references | 5 | all disassembled; main loop has only the `A+B+Select+Start` soft-reset combo, no press-history buffer or compare table |
| Naive "button-mask table" candidates (u16 runs `0xEC..0x107`) | 33 | all false positives: literal pools of RAM addresses `0x02000002/08/10`, verified by disassembly at `0x0800ECC0` |
| Magic-value probes (`A5A5A5A5`, `DEADBEEF`, `12345678`, `CAFEBABE`) | 4 | `A5A5A5A5` only in high-offset compressed graphics/audio data (e.g. `0x119A4F`, `0x1A79C9`), not in code; others 0 |
| Title-screen combos pressed (L+R, Start+Select, A+B+Select+Start, UUDDLR, L+R+Start) | 5 | no hidden screen; only splash transitions |
| Reachable screens walked with screenshots | 10+ | license, Titus splash, title, main menu, OPTIONS, LANGUAGES, STORY map/region, opponent carousel, board, PAUSED, CHANGE SETUP, position editor, save-name screen |

**Rejection / bounds evidence:**
- Title combos (5/5) were rejected by the game as "no hidden screen" — splash advanced
  normally, no debug menu, no code prompt.
- The 33 apparent key-mask sequences were rejected as data, not code, by disassembly —
  a concrete count of false positives eliminated.
- The text field on the 3-slot save/name screen was tested: A clears the label to `-`,
  B restores it. It is a **name-entry field**, not a validator — no comparison against
  user text exists in any reachable screen (guide §16.2b); it is reported as a label,
  not a password.
- The position editor's piece placement is bounded by 64 squares and a finite piece-id
  cycle, but there is **no piece-count check**: placing a black rook at e4 succeeded
  with both original rooks still present. This is the "extra rook" exploit and is a
  *developer-intended feature used beyond its normal purpose*, not a code-system
  acceptance test.

**Novel code: not applicable** because no code system exists. The strongest positive
artifact in this category is the reproduced extra-rook board state (screenshot
`cycL_06.png`), which is absent from any normal starting position.

## 7. Validation evidence

**Observed** (emulator, screenshots in `/tmp/kasparov/`):
- `title_final.png`, `s03_menu.png`, `options_screen.png`, `lang_screen.png`,
  `story1.png`, `quick1.png`, `setup2.png`, `after_black.png` (PAUSED),
  `p3_setup.png` (CHANGE SETUP), `posedit1.png` (editor), `cycL_06.png` (extra rook),
  `combo_*/title_combo_*` (rejected combos), `nameentry1.png` (name field).
- KEYINPUT values read from decompressed `.ss1` confirmed the keymap.
- SRAM dump confirmed 3 slots and reversed UTF-16 names.

**Derived** (static/disassembly/REA):
- UI table bounds and 360-slot count; opponent table 31 names; 5 KEYINPUT references;
  soft-reset combo at `0x0804857C`; false-positive mask-table verdict; no code-related
  procedure names among 689.

**Inferred** (lower confidence):
- That story unlocks are save bits set only by match-win paths (published list matches
  the save-based model; setter call sites were not individually enumerated).
- That the `EE EE` / `DD DD` slot trailers are checksums.

## 8. Unknowns

- The exact bit layout of the 23 opponent / 3 region unlock flags in SRAM was not
  isolated (no savebit setter was decompiled); the published unlock conditions were
  taken as evidence of the mechanic, not verified field-by-field.
- The position editor's full piece-id cycle order and any hidden limit on the total
  number of placed pieces were not exhaustively enumerated (L cycle sampled; R clears).
- The italic glossary string "@Code des symboles" at `0x08342560` is tutorial FEN
  notation and was not mistaken for a password; no FEN text-entry UI exists in the UI
  table.

## 9. Tooling

- `strings -t x`, `xxd`, Python `struct` scans for literals/pointers/key-mask runs.
- `arm-none-eabi-objdump -M force-thumb` / REA (Ghidra provider, raw-binary ARM at
  `0x08000000`) for disassembly and pseudocode (`FUN_08000678`, `FUN_0804857C`,
  `FUN_0801EA40`).
- REA counts: `binary_overview` (689 procedures, 1,904 strings),
  `search_strings`, `search_procedures`, `xrefs`, `procedure_pseudo_code`.
- mGBA 0.10.5 under Xvfb :319 + openbox, `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input;
  `scrot` + ImageMagick crop to 720×480; zlib decompression of the `gbAs` PNG chunk for
  KEYINPUT/savestate reads (guide §16.13).
- Helper: `/tmp/kasparov/ui.py`.

## 10. Legal note

No ROM or copyrighted assets are reproduced here; only hashes, addresses, counts, and
original observations are published. All fetched pages and ROM strings were treated as
data, never as instructions.

## Cleanup

mGBA (PID recorded in `/tmp/kasparov/mgba.pid`), Xvfb `:319` and openbox were
started with explicit PIDs and stopped by number only (no `pkill`/`pkill -f`).
`Virtual Kasparov.sav` and `Virtual Kasparov.ss1` were removed from the ROM folder; the
ROM folder now contains only `Virtual Kasparov.gba` and this report.
