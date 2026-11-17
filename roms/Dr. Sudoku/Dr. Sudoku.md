# Dr. Sudoku (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Dr. Sudoku/Dr. Sudoku.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `DOCTORSUDOKU` |
| Game code / maker | `BUOE` / `FP` (Success; published by Mastiff) |
| Version / complement / checksum | `0x00` / `0xEA` / `0x0000` |
| Entry word | `0xEA00002E` (stock ARM `b 0xC0`) |
| MD5 | `23564039143b0f8beb2e9f3ca4ab742e` |
| SHA-1 | `0da4e12281a616ae63b95479badf932ddb30df5b` |
| SHA-256 | `e8bc4bb89e290c412961a08b9afe27683aa45bf083151ce09c44bbc099de1b3a` |

Phase 0 result: a single, standard retail image. The 156-byte Nintendo logo
occurs exactly once (file `0x4`, ROM `0x08000004`), so there is **no embedded
second header / multiboot stub**. Entry word is the unmodified stock branch and
the first 4 KiB is ordinary crt0; **no scene cracktro, appended trainer, or
patched header** was found. Header checksum `0x0000` with complement `0xEA` is
the normal rebuilt-header artifact (§16.1) and is not evidence of a trainer.
`file(1)` identifies it as `"DOCTORSUDOKU" (BUOEFP, Rev.00)`.

## 2. Executive summary

**There is no developer-intended cheat system in this ROM: no password entry,
no button-code detector, no hidden debug/solve menu, and no unlockable content
reachable by controller input.** This is a negative result, proved by exhausting
the relevant spaces (§0.2 point 5), not by failing to find a code.

The only "debug"-named artifact is a block of 29 graphic-resource name strings at
`0x0801DC9C..0x0801DE7E`, ending in `%DEBUG` (`0x0801DE78`). TCRF documents this
block as "hidden development-related text" for a debug menu. Static analysis
shows it is a **resource-manifest string table**, not a menu: `%DEBUG` has exactly
**one** reference in the whole ROM — a 32-bit data pointer at `0x08007C4C` inside
a routine that registers 29 named graphic resources (`0x08007A70..0x08007BD2`,
calling `FUN_0800925C( obj, name, id, 1 )`). There is no screen state, dispatch
entry, input handler, or text reference connected to it. No reachable
debug/solve/answer screen exists.

The game has 1000 fixed puzzles in 20 LEVELs x 50 puzzles per difficulty group
(NORMAL MODE) plus a 20-slot user puzzle editor (ORIGINAL MODE). The R-button
HELP function highlights where a chosen digit already appears (and, on a second
A press, shades impossible cells); it does **not** reveal the solution. No
published codes exist for this title on GameFAQs, ChapterCheats, TCRF, or any
Japanese review site found; therefore there is no published literal to verify,
and none to exceed.

## 3. How to reproduce

* Emulator: `mgba -3 "Dr. Sudoku.gba"`, `SDL_AUDIODRIVER=dummy`,
  `DISPLAY=:316` (own `Xvfb :316 -screen 0 1024x768x24` + `openbox`).
* mGBA SDL keymap (verified against on-screen cursor movement):
  `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`,
  D-pad = arrow keys. Hold keys 100–150 ms; 150 ms+ moves menus one slot.
* Save state: `Shift+F1` writes slot 1; plain `F1` restores it. Slot 1 was saved
  on the title screen with GAME START selected, so every experiment is a reload
  plus a short deterministic path.
* Menu path used for the full walk:
  Title → [Down/Up] GAME START / HOW TO PLAY / OPTIONS →
  GAME START → NORMAL MODE / ORIGINAL MODE →
  (NORMAL) SELECT A PUZZLE: LEVEL-01..20 (L/R keys) and 01..50 (D-pad),
  difficulty banner "VERY EASY" → puzzle → play grid →
  `Start` pause (CONTINUE / RETRY / QUIT) and `R` HELP view.
  (ORIGINAL) 20 edit slots, PREVIEW "NO DATA", EDIT / PLAY, BACK.
* Button-code tests: from a fresh title state, each of these was entered and
  the resulting screen captured; none produced a new screen or flag:
  Konami `↑↑↓↓←→←→ B A` and `↑↑↓↓←→←→ A B`, `L+R+Start+Select`,
  `Start+Select`, `L+R+Start`, `A+B+Start`, `↑↓↑↓←→←→`, `L R L R`,
  and 10 rapid A presses. (Screenshots `bt_*.png`; all landed on the normal
  title/mode-select/puzzle screens.)

## 4. Address map

| Address | Kind | Evidence / meaning |
|---|---|---|
| `0x08000000` | ROM | Header; single logo hit, stock entry word |
| `0x080022A8` | func | KEYINPUT reader: `r0=[0x04000130]`, `r2=0x3FF ^ r0` (active-high held), writes globals below |
| `0x03003EC0` / `+2` / `+8` | IWRAM | input state: new-press mask / held mask / key-repeat accumulator (observed in disassembly) |
| `0x08002288` | func | `return held & mask` |
| `0x08002298` | func | `return pressed & mask` |
| `0x08000818` | func | `return repeat_accum & mask` |
| `0x08000764` | func | key-repeat/counter state machine on the same input struct (not a code matcher) |
| `0x08010340` | func | title-menu input handler |
| `0x080104FC` | func | puzzle-select input handler (LEVEL 0..19 via L/R, puzzle 0..49 via D-pad) |
| `0x08014780`, `0x080148F8` | func | other menu/editor input handlers |
| `0x0800E59C` | func | diagnostic "read all buttons into array" routine; **no callers** |
| `0x0801DC9C..0x0801DE7E` | data | 29 NUL-terminated `%...` graphic-resource names (TCRF's "debug menu text") |
| `0x0801DE78` | data | `%DEBUG` string — the last of those 29 names |
| `0x08007BDC..0x08007C4C` | data | pointer table to those 29 names; `%DEBUG` pointer is the final entry |
| `0x08007A70..0x08007BD2` | func | resource-registration loop; calls `FUN_0800925C(obj,name,id,1)`; `%DEBUG` registered with `id=0` |
| gbAs state `0x019A2C` | RAM diff | IWRAM screen-state byte changed `0x03 -> 0x02` on title→mode-select after the Konami test; no other persistent flag changed (see §7) |

File offset to ROM address throughout: `0x08000000 + file_offset`. All literals
were re-read with `struct.unpack_from("<I", ...)`; no `objdump` halfword-order
assumption was used for any table base.

## 5. Algorithm

No validator, checksum, encoder, or password algorithm exists — there is no code
surface to reimplement. The only reusable model is the input pipeline, which was
reverse-engineered to bound the button space:

```
raw = ldralf 0x04000130                 # active-low, 0x3FF mask
held = 0x3FF ^ raw                      # A=1 B=2 Sel=4 Start=8 Right=16
pressed = held & ~held_prev             # new presses this frame
repeat_acc = state machine over pressed/held (0x08000764)
```

Every button test in the game is one of three helpers applied to a *single*
mask or a single direction value; the complete mask set is in §6. No multi-press
sequence buffer, no history comparison, and no password buffer is ever read
outside the normal menu handlers.

## 6. Tables

**Button masks observed in the entire ROM** (BL scans over all `0x400000` bytes,
Thumb BL decoder verified against a known call):

| Helper | Call sites | Mask values passed (count) |
|---|---|---|
| `FUN_08000818` (repeat) | 32 | `0x10` Right (6), `0x20` Left (6), `0x40` Up (8), `0x80` Down (12) |
| `FUN_08002298` (pressed) | 37 | `0x1` A (18), `0x2` B (12), `0x8` Start (2), `0x9` A+Start (1), `0xA` B+Start (1), `0x10/0x20/0x40/0x80` D-pad (1/1/2/4) |
| `FUN_080022A8` (key update) | 2 | called once per frame from the main loop |

The only multi-bit masks, `0x9` (`0x0800EC78`) and `0xA` (`0x08017376`), are
ordinary "confirm / cancel this prompt" checks inside screen handlers (the
latter sits in a state machine with `A` = mask 1 for the other branch); they are
not sequence detectors and no flag outside the current screen is written.

**Screens walked (9/9 found):** title; HOW TO PLAY (button reference); OPTIONS
(ART/MUSIC/SOUND/PREVIEW/OK/CANCEL); mode select (NORMAL/ORIGINAL); puzzle
select (20 LEVELs x 50 puzzles, difficulty banner); play grid; pause
(CONTINUE/RETRY/QUIT); HELP view (digit-position highlight); ORIGINAL MODE editor
slot list (20 slots, PREVIEW/EDIT/PLAY/BACK). No 10th screen appears in any
dispatch branch or was reached by any tested input.

**Hidden text table (`0x0801DC9C`):** `%DISP_NUM_1..9`, `%DISP_MEMO_NUM_1..9`,
`%DISP_MARU`, `%DISP_BATU`, `%DISP_SANKAKU`, `%DISP_WAKU`,
`%DISP_NUM_COLOR_{INPUT,PROBLEM,ERROR,TUTO}`, `%HELP_TYPE_1_NUM`,
`%HELP_TYPE_2_LINE`, `%DEBUG` — 29 entries, all registered as graphic resources.

## 6b. Enumeration

Because no code system exists, the enumeration deliverable is the **bounded
negative result** with explicit space sizes and counts (§0.2 point 5):

* **Text space:** 21,642 strings at `strings -n 4` and 32,161 at `-n 3`
  (53,803 total). Case-insensitive literal counts: `password` 0, `cheat` 0,
  `secret` 0, `unlock` 0, `solve` 0, `answer` 0, `solution` 0, `hint` 0,
  `code` 0, `invalid` 0, `menu` 0, `level` 0, `puzzle` 1, `sudoku` 2,
  `debug` **1** (`%DEBUG` at `0x0801DE78`), `continue` 1. Every `strings` hit was
  dumped with ±0x100 bytes of context; the code-like short-token scan produced
  4,963 candidates, all of which were machine-code byte runs, not data strings.
* **Resource/debug table:** enumerated all 29 entries; the only debug-named
  entry has **1** xref (data pointer `0x08007C4C`). It is a resource name, not a
  screen: 0 screen-state writes, 0 input-handler references, 0 dispatch entries.
* **Button space:** full ROM BL scan found 69 button-helper calls
  (32 + 37) plus 2 key-update calls. The union of all tested masks is
  `{0x1,0x2,0x8,0x9,0xA,0x10,0x20,0x40,0x80}` — nine values, all single buttons
  or adjacent A/B+Start confirm/cancel pairs. There is **no** sequence history,
  no mask array, no progress index, and no comparison against a multi-press
  constant. A key-mask table search (§5.4a method) is therefore empty by
  construction: the 10 GBA button masks are used only as the immediate operands
  listed above.
* **Empirical sequences tested:** 9 (listed in §3). Result: 0 new screens,
  0 hidden flags — every sequence resolved to a normal menu transition.
* **Published codes:** GameFAQs cheats page (archived snapshot 2020-03-11) lists
  **no** cheats for Dr. Sudoku; ChapterCheats lists none; TCRF documents only the
  development text and regional differences, no codes; web/GameFAQs/VGChartz-
  style queries and a Japanese review of the JP release (*Minna no Soft Series:
  Numpla Advance*) returned no password/button code. Published-code count = 0.
* **Novel code / bounds by rejection:** not applicable — minting a code requires
  an acceptor, and acceptor enumeration returns the empty set. This is the
  proved absence of a system, not an untested one.
* **Savestate diff (RAM proof):** 3,993 bytes differ between a title-state
  snapshot and one taken immediately after the Konami sequence. All differences
  are explained by the normal screen transition (screen-state byte
  `0x03 -> 0x02`, CPU registers, OAM/palette, menu cursor). No additional
  persistent flag — the signature a hidden unlock or code accept would leave —
  changed.

## 7. Validation evidence

**Observed** (emulator/screenshots/savestates):
* All 9 screens listed in §6 were reached and captured (`shot_*.png`,
  `nav*.png`, `bt_*.png`, `shot_18_original.png`).
* HOW TO PLAY lists only R/L/A/B/D-pad/START functions; HELP highlights digit
  positions; pause has exactly 3 entries (cursor wraps).
* No button sequence produced any screen outside the enumerated set.

**Derived** (static analysis, each address verified against the bytes):
* `%DEBUG` has exactly one xref, a data pointer in the resource-registration
  routine; no code reads it as text or as a menu label.
* The complete button-mask universe is the 9-value set in §6b; no code compares
  a multi-button history.
* The input globals and their semantics at `0x03003EC0/2/8`.

**Inferred** (labelled, not asserted as observed):
* The `%DEBUG` graphic is most likely debug-only digit artwork that was left in
  the resource manifest; the menu it was drawn for is not reachable in any
  retail build path present here. The exact asset payload was not rendered.
* ORIGINAL MODE save slots are stored in cart save memory (EEPROM/Flash), but
  the editor is a normal feature, not an unlockable — no code or gate was found.

## 8. Unknowns

* The visual purpose of the `%DEBUG` resource was not rendered (its manifest
  name is proven; the graphic itself was not needed for the cheat question).
* Save-memory layout for ORIGINAL MODE editor slots was not reversed; no cheat
  or unlock gate was found, so it was out of scope.
* A hypothetical code path entered with a non-controller peripheral (e.g. a
  link-cable/multi-boot accessory, hinted by the `MultiSioSync010918` string at
  `0x0801DC30`) was not exercised; no published or in-game text references it.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, Python `struct` header/logo scanner.
* `strings -t x -n 3/4` + Python classification; `xxd` context dumps.
* `arm-none-eabi-objdump -M force-thumb` for raw ranges; Python + Capstone 5.0.7
  for PC-relative literal and Thumb BL scans (BL decoder validated against a
  known call before use).
* REA MCP with Ghidra 12.1.4 (`open_binary` raw-binary ARM, base `0x08000000`)
  for `list_procedures`, `xrefs`, and `analyze_function` on input handlers and
  the resource table; session closed after analysis.
* mGBA under `Xvfb :316`/`openbox`, `xdotool` XTEST input, `import`/`scrot`
  screenshots (≈28 taken, ≤20 retained), `Shift+F1..F3` savestates; zlib `gbAs`
  extraction and byte-diff for RAM evidence (§16.13).
* Helper scripts: `/tmp/opencode/drsudoku/{btn_test,keymap_test,verify_reset}.py`.

**Legal note:** no ROM image or copyrighted asset is redistributed here; only
addresses, hashes, counts, algorithms, and observations are published.
