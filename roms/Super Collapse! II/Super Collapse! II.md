# Super Collapse! II (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Super Collapse! II/Super Collapse! II.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `SUPER CLPSE2` |
| Game code / maker | `BCLE` / `5G` |
| Version | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`, **not** a cracktro) |
| `file` id | Game Boy Advance ROM image "SUPER CLPSE2" (BCLE5G, Rev.00) |
| MD5 | `4529b2bfb0b9a2303c45bfc7f15f466e` |
| SHA-1 | `72b62b363d04a363908d5428549e84f37db6c397` |
| SHA-256 | `616925f77728c3c2eaa5874a22f46e45bd2c433a2b552aba4b7cfb6ba0638f28` |

Header oddity (Observed): complement byte is `0x67` while `sum(0xA0..0xBC)=0x80` implies `0x80`; header checksum is `0x0000`. This is the signature of a rebuilt/edited header (title truncation). The first 4 KiB is normal ARM code, so the ROM image itself was analysed as-is.

## 2. Executive summary

The game has a **table-driven 5-character "Continue Code" / "Puzzle Password" system**, not an arithmetic checksum. The ROM contains exactly **220** NUL-terminated 5-character codes at `0x0800DA54` (6-byte stride, ending `0x0800DF7C`). The validator at `0x08000944` compares the 5-byte input buffer at `0x03000108` against the subset of that table selected by the current mode byte at `0x03000322` (0=Classic, 1=Relapse, 2=Strategy, 3=Puzzle). On a match it writes a level index and difficulty flags into the game-state struct at `0x03001764`.

**All 219 codes on the GameFAQs list are present verbatim in the ROM table, and one table entry is not on any published list: `GDHWP` (= Puzzle 1, index 120).** It was entered in the Puzzle Password screen, accepted, and started Puzzle 1 with the expected RAM state (§6b).

A second, entirely separate developer secret exists: the hardcoded 5-letter string **`YAWER`**, compared byte-by-byte *before* the table scan. It plays sound effect 5 and sets a private flag at `0x0300032C` to 1, but it is **not** a table entry, so the UI still reports `INVALID CONTINUE CODE`. No web source mentions it (search negative). Its downstream effect is gated by additional game-state bits and remains unresolved (§8).

No button-code sequence, debug menu, or other hidden code surface was found on any reachable screen.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (SDL), Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
* Hold keys ~60–70 ms; 150 ms double-steps the code-entry cursor.
* Boot → Start (splash) → Start → **main menu** (`START A NEW GAME` / EASY / HARD / `CONTINUE CODE` with 5 slots).
* Enter a code: Down moves to slot 1, Up/Down cycles the character (`A`..`Z`,`0`..`9`, wrapping), Right advances slot, A on `ENTER` submits.
* Mode selection: play any game, Start → `QUIT GAME` → **SELECT MODE** (CLASSIC / RELAPSE / STRATEGY / PUZZLE / SOUND / HELP). Select PUZZLE → `PLAY PUZZLE # 1` / `PUZZLE PASSWORD`.
* Savestates: `Shift+F<n>` saves, `F<n>` loads. mGBA `.ss*.png` carries a zlib `gbAs` chunk; decompressed state is 397,312 bytes with IWRAM at offset `0x19000` (= `0x03000000`) and EWRAM at `0x21000`. Input buffer was located by diffing snapshots after changing one character: `0x03000108`.
* Codes exercised in-game: `TJQNL` (published, accepted), `2W9CH` (published, accepted), `GDHWP` (unpublished, accepted), `YAWER` (hidden flag), `AAAAA`, `TJQNL`-in-Puzzle, `GDHWP`-in-Classic (all rejected as expected).

## 4. Address map

### ROM (file offset = ROM addr − `0x08000000`)

| Address | Meaning | Evidence |
|---|---|---|
| `0x0800DA54` – `0x0800DF7B` | Password table: 220 × `{char[5], 0x00}` | Derived from validator indexing; literal search of all published codes |
| `0x0800DF7C` | Table end pointer (stored into `0x03001BA0` at `0x0800676C`) | Derived |
| `0x08000944` | Validator start (function ~`0x08000930`–`0x0800A64`) | Derived from disassembly |
| `0x0800094C` – `0x08000968` | Five literal compares for secret `YAWER` (`59 41 57 45 52`) | Derived |
| `0x08000970` | `BL 0x08008D14(5,128,8)` — secret sound effect | Derived |
| `0x08000974` – `0x08000978` | `strb 1` to `0x0300032C` (secret flag) | Derived |
| `0x0800097A` – `0x0800099C` | Mode→range selection from `0x03000322` | Derived |
| `0x080009B4` – `0x0800A60` | 5-byte compare loop over table entries | Derived |
| `0x0800A02` – `0x0800A18` | Hard branch: `flags \|= 3`, level `= 5*(off-19)` | Derived |
| `0x0800A30` – `0x0800A42` | Easy branch: `flags = (flags\|1)&~3`, level `= 5*(off+1)` | Derived |
| `0x0800A44` – `0x0800A58` | Puzzle branch: `flags &= ~3`, level `= off` | Derived |
| `0x0800A64` | Failure path (invalid-code handling) | Derived |
| `0x08002C40` – `0x08002E98` | Generator: derive table index from (mode, difficulty, level) and copy the 5 chars into `0x03000108` | Derived |
| `0x0800A018`, `0x0800A090` | `udiv` / `umod` helpers used by the generator | Derived |
| `0x0800CE4`, `0x08001C40` | Input alphabet conversion: `A-Z → 0..25`, `0-9 → 26..35` | Derived |
| `0x08003940`, `0x08003BBC`, `0x08004280`, `0x080044D6`, `0x08006D6C` | Readers/writer of the YAWER flag `0x0300032C` | Derived |

Literal pools used by the validator: `0x0800A1C = 0x03000108` (input), `0x0800A20 = 0x0300032C` (secret flag), `0x0800A24 = 0x03000322` (mode), `0x0800A28 = 0x0800DA54` (table), `0x0800A2C = 0x03001764` (game state).

### RAM

| Address | Meaning |
|---|---|
| `0x03000108` | 5-byte input buffer, default `AAAAA` (Observed) |
| `0x03000322` | Mode byte: 0 Classic, 1 Relapse, 2 Strategy, 3 Puzzle (Observed on all four setup screens) |
| `0x0300032C` | YAWER secret flag, 0/1 (Observed: `00 → 01`) |
| `0x0300176C` (= state+8) | Level index written by validator (Observed) |
| `0x0300177E` (= state+26) | Difficulty flags: bit0 Easy, bit1 Hard; Puzzle clears both (Observed `0x84 → 0x80`) |
| `0x03001BA0` | Table end pointer `0x0800DF7C` (Derived) |

## 5. Algorithm

### 5.1 Input conversion (entry UI)

```
A..Z (0x41..0x5A) -> 0..25
0..9 (0x30..0x39) -> 26..35
```
The on-screen alphabet therefore has 36 symbols; the *table* alphabet is narrower (§6).

### 5.2 Validator (`0x08000944`), pseudocode

```
input = byte[5] @ 0x03000108
if input == "YAWER":                      # hardcoded developer secret
    sound(5, 0x80, 8)
    byte[0x0300032C] = 1                  # private flag, NOT a continue code

mode = byte[0x03000322]
lo,hi = {0:(0,40), 1:(40,80), 2:(80,120), 3:(120,220)}[mode]

for i in range(lo,hi):
    if input == table[i][0:5]:            # 5 inline byte compares
        state = 0x03001764
        if mode == 3:                     # Puzzle
            byte[state+26] &= ~3
            u16[state+8] = i - 120
        else:
            off = i - lo
            if off <= 19:                 # Easy half of the 40-entry group
                u16[state+8] = 5 * (off + 1)
                byte[state+26] = (byte[state+26] | 1) & ~3
            else:                         # Hard half
                u16[state+8] = 5 * (off - 19)
                byte[state+26] |= 3
        return success                    # start selected level
return failure                            # INVALID CONTINUE CODE
```

The `5*(off+1)` stored level displays as `LEVEL 6` for `off=0`; the display adds 1 to the stored index (Observed with `TJQNL`).

### 5.3 Generator (`0x08002C40` region) — inverse of the table lookup

```
mode != 3:
    base = {0:0, 1:40, 2:80}[mode] + (20 if (state[26] & 2) else 0)
    assert level % 5 == 0 and level <= 100
    i = (base - 1 + level/5) & 0xFFFF      # udiv helper 0x0800A018
mode == 3:
    assert level <= 99
    i = (level + 120) & 0xFFFF
copy table[i][0:5] -> 0x03000108
```

This proves the table is a **permutation of (mode, difficulty, level)** and that no arithmetic checksum exists: acceptance is exact membership in the 220 strings.

## 6. Tables

### 6.1 Table layout (220 entries, 6 bytes each, `0x0800DA54`)

| Indices | Mode | Difficulty | Display levels / puzzles |
|---:|---|---|---|
| 0–19 | Classic | Easy | 6, 11, …, 101 |
| 20–39 | Classic | Hard | 6, 11, …, 101 |
| 40–59 | Relapse | Easy | 6, 11, …, 101 |
| 60–79 | Relapse | Hard | 6, 11, …, 101 |
| 80–99 | Strategy | Easy | 6, 11, …, 101 |
| 100–119 | Strategy | Hard | 6, 11, …, 101 |
| 120–219 | Puzzle | — | Puzzle 1 … 100 |

Examples (all ROM-verified): index 0 `TJQNL` (Classic Easy L6), index 20 `2W9CH` (Classic Hard L6), index 40 `JKWPG` (Relapse Easy L6), index 80 `FXWMW` (Strategy Easy L6), index 120 `GDHWP` (Puzzle 1), index 219 `DX4YK` (Puzzle 100).

### 6.2 Alphabets

* Input keyboard: 36 symbols `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`.
* Password table uses 26 of them: `2 3 4 5 6 7 9 C D F G H J K L M N P Q R S T V W X Y` (no vowels, no `0`,`1`,`8`,`Z`,`I`,`O`,`A`,`B`,`E`,`U`). Derived by character histogram over all 220 entries; `strings` finds no alphabet literal because text is stored as font/tile indices, and the ASCII-looking codes are a separate plaintext table.

### 6.3 Flag bits at `0x0300177E`

| Bit | Meaning |
|---:|---|
| 0 | Easy difficulty selected by code |
| 1 | Hard difficulty selected by code |
| 2 | Read by the generator to add 20 to the base index; not set by any code path in the validator |

### 6.4 Published-list verification

219 published data rows recovered from an archived GameFAQs cheats page (Wayback snapshot `20181126051549`). **All 219 appear verbatim in the ROM table; no published code is missing from the ROM.** One ROM entry has no published counterpart (§6b).

## 6b. Enumeration

### Space definition

* Input space: `36^5 = 60,466,176` possible 5-slot strings.
* Accepted continue codes: **exactly 220** — one per table entry, and the validator scans only the 40-entry (or 100-entry for Puzzle) window selected by the mode byte. There is no checksum, no wildcard, no alias: the table strings are unique (220/220 distinct).
* Secret inputs: exactly 1 hardcoded string (`YAWER`) outside the table; it sets a flag but is **not** accepted as a continue code.
* Field space: 6 mode/difficulty groups × 20 levels (display 6–101 step 5) + 100 puzzles = 220.

### Novel codes (absent from every published list)

1. **`GDHWP`** — table index 120, Puzzle 1. This is the single ROM-table entry that is not among the 219 GameFAQs codes (verified by set difference: ROM−published = `{GDHWP}`, published−ROM = `{}`). Entered on the **Puzzle Password** screen (mode byte `0x03000322 = 03`, Observed). Result: **accepted**, launched Puzzle mode with `PUZZLE NAME "Collapse!"`, `LEVEL 1`, `ATTEMPTS 1` (screenshot `s15.png`). RAM after entry: mode `03`, `0x0300177E` `0x84 → 0x80` (bits 1 & 2 cleared), input buffer `0x47` (`'G'`), state level field consistent with puzzle 1. Screenshot before submission: `s14.png`.
2. **`YAWER`** — hardcoded secret in the validator, not in the table and not found by web search. Entered on the main menu (screenshot `s6.png`): plays sound index 5 and sets `0x0300032C: 00 → 01` (Observed by savestate diff, slot 1 vs slot 3), then the UI shows `INVALID CONTINUE CODE` (screenshot `s7.png`) because it is not a table entry. A pixel-level diff of the main menu before/after (AE = 0) shows **no visible menu change**; the flag's consumer is gated by other state bits (§8). It is a real developer-intended hidden input, but not a usable continue code.

### Bounds proved by rejection (all Observed in emulator)

| Test | Screen / mode | Result | Bound proved |
|---|---|---|---|
| `AAAAA` | Puzzle password (mode 3) | `INVALID CONTINUE CODE` (`rej_aaa.png`) | Not a table member; vowels/outside table alphabet rejected |
| `TJQNL` (table idx 0, Classic Easy L6) | Puzzle password (mode 3) | `INVALID CONTINUE CODE` (`rej_classic_in_puzzle.png`) | Mode gating: Classic codes unreadable in Puzzle window |
| `GDHWP` (table idx 120, Puzzle 1) | Main menu (mode 0) | `INVALID CONTINUE CODE` (`rej_puzzle_in_classic.png`) | Mode gating: Puzzle codes unreadable in Classic window |
| `TJQNL` | Main menu (mode 0) | Accepted → Classic `LEVEL 6` (`rej_classic_ok.png`) | Validator model confirmed against published code |
| `2W9CH` (idx 20, Classic Hard L6) | Main menu (mode 0) | Accepted → Classic `LEVEL 6`, dark board (`rej_digit_hard.png`) | Hard-half branch and digit inputs confirmed |
| `YAWER` | Main menu (mode 0) | `INVALID CONTINUE CODE` + hidden flag set | Secret is not a table member |

### Button-code / hidden-menu negative

No button-code system was found. Recon found no published button sequences for this SKU; a raw scan for the Konami mask sequence (active-high and active-low 16-bit masks) returned zero hits; the four mode/setup screens, title, pause, volume and validation dialogs were all walked with the mode byte read from RAM at each. No undocumented menu entry or reaction appeared. This is a *bounded no-system* result for the walked surfaces, not a claim about untested in-play states.

## 7. Validation evidence

* **Observed**: hashes/header; all 220 table strings; every published code present; mode byte `00/01/02/03` on the four setup screens; input buffer `0x03000108` located by savestate diff; GDHWP accepted with the Puzzle-1 screen and RAM flags; YAWER flag `00→01`; all six acceptance/rejection outcomes above; pixel-identical main menu before/after YAWER.
* **Derived**: validator pseudocode and mode ranges from Thumb disassembly at `0x08000944`–`0x0800A64`; generator index formula from `0x08002C66`–`0x08002D28`; alphabet mapping from `0x0800CE4`/`0x08001C40`; table stride and bounds from the literal `0x0800DA54`/`0x0800DF7C` and the ×6 addressing in the compare loop.
* **Inferred**: YAWER's sound call is a "secret found" cue (the same helper plays a sound when a block has value `-1` elsewhere); exact callers of the validator/generator are state-machine dispatch entries with no direct BL or pointer found.

## 8. Unknowns

* The downstream *visible* effect of the YAWER flag `0x0300032C` is unresolved. It is read at `0x08003940`, `0x08003BBC`, `0x08004280`, `0x080044D6` (each time gated by additional state bits) and cleared at `0x08006D6C` on init. No menu change was observed. A longer play session with the flag set would be needed to isolate it.
* No direct BL or function-pointer xref to the validator (`~0x08000930`) or generator (`~0x08002C40`) was found; they are presumably reached through computed state-machine dispatch, so the exact UI event that invokes the generator (continue-code display after a loss/level clear) was not exercised.
* The header complement/checksum mismatch is consistent with an edited header; the original title bytes are unknown.
* HELP screen contents were not exhaustively transcribed (no code-related content found on the screens that were walked).

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep -abo`
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for validator/generator disassembly; Capstone/Python for PC-relative literal and BL scans
* Python 3 for header parse, table enumeration, published-list set difference, and savestate `gbAs` zlib decompression
* mGBA 0.10.5 SDL, Xvfb `:319`, openbox, xdotool, scrot; savestate RAM diffing (guide §16.13) because the GDB stub was unreliable in this build
* Evidence files were kept in `/tmp/supercollapse2/` (`s*.png`, `rej_*.png`, `screen_*.png`, `gfaqs_arch.html`, helper scripts). No ROM or copyrighted assets are redistributed by this report.
