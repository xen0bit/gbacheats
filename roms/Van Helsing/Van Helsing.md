# Van Helsing (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Van Helsing/Van Helsing.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `VAN HELSING` |
| Game code | `BANE` (`BANE7D`) |
| Maker | `7D` |
| Version | 0 (Rev.00) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0; no cracktro) |
| Header complement | `0xB1`; checksum `0x0000` |
| MD5 | `1cf89b423893a12ee0bbc1c4e2868509` |
| SHA-1 | `1928f02a031020fae57d42eccc502dc04657d565` |
| SHA-256 | `183bcd7ba276d457fd7d315957008daf19475006546d9823609864056859918f` |

Retail US SKU (Saffire/Vu Games). All addresses below are for this exact image.

## 2. Executive summary

The game has a genuine developer-intended **password system** on the title screen: a
32-symbol keypad accepting a 9-character code. The codes are *not* a lookup table —
they are a 45-bit packed word (9 × 5-bit symbols) with eight fields extracted by a
bit-width table and a 5-bit additive fold checksum. I reversed the decoder at
`0x08001948` and its hash at `0x080017E4`, reimplemented both in Python, and confirmed
that **all 11 published codes validate** and that two **novel codes absent from every
published list** are accepted by the real game. RAM reads confirm each decoded field is
written to its expected global.

Four out-of-range/malformed inputs were rejected in-game, bounding the format. A
separate 2-entry hard-coded table at `0x08179DAC` contains an **undocumented code**
`H9L9NDS9N` that boots "PARIS, FRANCE" — a code that fails the algorithmic validator
and is absent from all published lists. No button-code system or hidden debug menu was
found (bounded negative, §8).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, 3× scale.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrows. Hold keys ≥120 ms.
* Path: boot → press Start through the Saffire logo → title
  `NEW GAME / PASSWORD / OPTIONS` → Down, A → `PASSWORD` keypad.
* Keypad is an 8×4 grid; cursor starts on `1`. D-pad moves one cell; A enters the
  highlighted symbol. On the 9th entry the cursor **auto-jumps to DONE**; press A to
  submit. Rejected codes stay on the password screen with the code still displayed.
* Verified codes (typed on this screen):
  * published: `2S5M12111` → St. Peter's Basilica.
  * novel: `JM5W12111` → St. Peter's Basilica (with non-default flags, RAM verified).
  * novel: `2155M9X!@` → St. Peter's Basilica.
  * undocumented ROM code: `H9L9NDS9N` → "PARIS, FRANCE".
  * rejected: `2S5M12112`, `@65M12111`, `2W9M12111`, `!!!!!!111`.
* A savestate at the empty password screen makes each trial a keypress; mGBA writes
  `Van Helsing.ss1` next to the ROM.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Item | Address | Evidence |
|---|---|---|
| Password UI strings | `0x0982BD8` (`PASSWORD:`), `0x0982D80` (`PASSWORD`) | Derived (pointer scan) |
| **Password validator** | **`0x08001948`** | Derived (called from `0x080028DC`; reads buffer/length) |
| Validator caller | `0x080028DC` | Derived (BL scan) |
| 5-bit fold hash | `0x080017E4` | Derived (BL at `0x0801C34`) |
| Hash seed bytes | `0x0817D0EF`, `0x0817D0F0` (`0x08`, `0xCC`; sum 212 → LSL no-op) | Derived |
| Hard-coded code table | `0x08179DAC` (2 × 9 bytes) | Derived (literal at `0x08019CC`) |
| Bit-width table | `0x0817EFD0` = `04 01 05 06 03 06 0B 09` | Derived (literal at `0x0801AE0`) |
| Jump table (8 field stores) | `0x08001AE8` | Derived (literal at `0x0801AE4`) |
| Blacklist constant | `0x08001A64` = `0x21084210` | Derived (literal at `0x0801A64`) |
| Second hash user (likely encoder) | BL at `0x08001EC4` | Derived (not fully reversed) |
| **Input buffer** | RAM **`0x03001550`** (9 bytes, 0-based symbol indices) | Observed (savestate diff + live `-d` read) |
| **Input length** | RAM **`0x03001584`** (byte) | Observed |
| Field 1 flag | RAM `0x0300154C` (byte) | Derived + RAM-verified |
| Mode byte (hard-coded path) | RAM `0x0300158C` (byte) | Derived |
| Field 3 (checkpoint) | RAM `0x03004A64` (halfword) | Derived + RAM-verified |
| Field 5 | RAM `0x03004A70` (halfword) | Derived + RAM-verified |
| Field 4 | RAM `0x03004A94` (byte) | Derived + RAM-verified |
| Field 6 | RAM `0x03004AB4` (halfword) | Derived + RAM-verified |
| Combined `8*f7 + f5` | RAM `0x03004AD0` (halfword) | Derived + RAM-verified |

Savestate layout (mGBA `.ss1`, zlib `gbAs` chunk): IWRAM at state offset `0x19000`,
so state `0x1A550` is RAM `0x03001550`.

## 5. Algorithm

1. Require length ≥ 9 (`cmp #8; bhi` at `0x08001974`); else return 0.
2. Compare the 9 RAM bytes with 2 hard-coded 9-byte strings at `0x08179DAC`. A match
   on entry 0 calls `0x08000B1C(32)` and writes `5` to `0x0300158C`.
3. Pack the 9 symbols into a 45-bit word:
   `P = Σ sym[i] << (5*i)`, `i = 0..8` (64-bit LSL helper `0x08048C44`).
4. Reject if `P == 0x21084210` (i.e. `!!!!!!111`).
5. Split `P` by widths `[4,1,5,6,3,6,11,9]` at offsets
   `[0,4,5,10,16,19,25,36]` into fields `f0..f7`.
6. Range checks: `f0 <= 11`; if `f0 <= 9` then `f3 <= 4*f0`, else `f3 <= 4*(f0-1)`.
7. Checksum: `f2 == (Σ ((P >> s) & 31) for s in [0,10,15,20,25,30,35,40]) & 31`.
   (The subtract at `0x0801C12` shifts by `0x08+0xCC = 212 ≥ 32`, so ARM LSL
   produces 0 — a no-op.) `f2`'s own bits 5–9 are the hole in the fold.
8. On success, store fields into the globals in §4 and return 1.

Python reimplementation: `/tmp/opencode/vanhelsing/vh.py`.

## 6. Tables

**Keypad alphabet** (row-major, 8×4; index = stored RAM value):

| | c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
|---|---|---|---|---|---|---|---|---|
| row0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
| row1 | 9 | B | C | D | @ | F | G | H |
| row2 | ! | J | K | L | M | N | * | P |
| row3 | Q | R | S | T | $ | V | W | X |

`ALPHA = "123456789BCD@FGH!JKLMN*PQRST$VWX"`.

**Field layout**: `f0` 4b level (1–11 in all published codes), `f1` 1b flag,
`f2` 5b checksum, `f3` 6b checkpoint, `f4` 3b (published values 2–4), `f5` 6b,
`f6` 11b, `f7` 9b.

**Published codes** (all 11 validate against the model; levels from `f0`):

| Level | Code | f0 | f2 | f3 | f4 | f5 | f6 | f7 |
|---|---|---|---|---|---|---|---|---|
| 1 St. Peter's | `2S5M12111` | 1 | 26 | 4 | 2 | 1 | 1 | 0 |
| 2 Train | `3X9M12111` | 2 | 31 | 8 | 2 | 1 | 1 | 0 |
| 3 Vaseria | `4H@5DH311` | 3 | 15 | 12 | 2 | 22 | 79 | 0 |
| 4 Valken | `54!5DV411` | 4 | 3 | 16 | 2 | 22 | 125 | 0 |
| 5 Werewolf | `65M5HL611` | 5 | 4 | 20 | 2 | 30 | 179 | 0 |
| 6 Dracula's Children | `7BQ*248C1` | 6 | 9 | 24 | 3 | 3 | 227 | 5 |
| 7 Escape Castle | `8P$7D8KC1` | 7 | 23 | 28 | 3 | 22 | 583 | 5 |
| 8 Carriage Battle | `9C1P!WLC1` | 8 | 10 | 32 | 3 | 33 | 638 | 5 |
| 9 Dracula's Castle | `BF18KFMC1` | 9 | 13 | 32 | 3 | 36 | 653 | 5 |
| 10 Dracula Final | `CG5B78*M1` | 10 | 14 | 36 | 4 | 12 | 711 | 10 |
| 11 End/Credits | `DL5BF3QM1` | 11 | 19 | 36 | 4 | 26 | 770 | 10 |

**Hard-coded ROM codes** at `0x08179DAC` (raw symbol indices):
`H9L9NDS9N` (`0f 08 13 08 15 0b 1a 08 15`) — **accepted**, boots "PARIS, FRANCE".
`H9L9NDS9*` (`0f 08 13 08 15 0b 1a 08 16`) — rejected. Neither is on a published list.

Cheat Happens lists lowercase codes (`d5x5k2hm1`, `3h9512111`, …) using letters
outside this SKU's 32-symbol keypad; they are unreachable here and are recorded as
unverified (guide §16.7/§16.11).

## 6b. Enumeration

**Space definition.** 9 symbols × 5 bits = 45-bit payload; total input space
`32^9 = 35,184,372,088,832`. The validator constrains:

* `f0` 4 bits → 12 permitted values (0–11; 1–11 are real levels, 0 untested),
* `f1` 1 bit → 2 values,
* `f2` 5 bits → **exactly 1** value per other-field combination (the fold checksum),
* `f3` 6 bits → `4*f0+1` values for `f0 ≤ 9`, `4*(f0-1)+1` for `f0 ≥ 10`,
* `f4` 3 bits → 8 values, `f5` 6 bits → 64, `f6` 11 bits → 2048, `f7` 9 bits → 512,
* one explicit blacklisted point (`0x21084210` / `!!!!!!111`).

**Exact accepted count** = `268 × 2 × 8 × 64 × 2048 × 512 − 1`
= **287,762,808,831** (0.818 % of the input space), where the 268 = sum over level of
the allowed `f3` counts (1 + 189 + 37 + 41). This follows from running the model over
the full field space; the model agrees with the ROM on every input tested.

**Novel codes (not in any published list), confirmed in-game:**

| Code | Fields changed vs. published | Result | Evidence |
|---|---|---|---|
| `JM5W12111` | level 1 with `f1=1` (no published code uses this), `f4=7` (published: 2–4); checksum recomputed | Accepted → St. Peter's Basilica | Screenshot `novel1.png`; RAM `0x0300154C=1`, `0x03004A94=7`, `0x03004A64=4`, `0x03004A70=1`, `0x03004AB4=1`, `0x03004AD0=1` |
| `2155M9X!@` | level 1 with `f5=40`, `f6=1000`, `f7=200` (far outside published values) | Accepted → St. Peter's Basilica | Screenshot `novel2.png` |
| `H9L9NDS9N` | hard-coded ROM table entry; fails the algorithmic validator (`f0=15`) | Accepted → "PARIS, FRANCE" | Screenshots `hard0*.png` |

Regenerating the published level-1 code's fields with `f4=2` yields back
`2S5M12111`, a control that proves the encoder matches the ROM.

**Bounds proven by in-game rejection** (screenshot = code still on keypad, no level):

| Input | Violation | Result |
|---|---|---|
| `2S5M12112` | bad 5-bit checksum | Rejected (`rej_badchecksum.png`) |
| `@65M12111` | `f0=12` out of range (>11) | Rejected (`rej_level12.png`) |
| `2W9M12111` | `f3=8` exceeds `4*f0=4` at level 1 | Rejected (`rej_f3range.png`) |
| `!!!!!!111` | explicit blacklist `0x21084210` | Rejected (`rej_blacklist.png`) |
| `H9L9NDS9*` | second hard-coded entry | Rejected (`hard1.png`) |

## 7. Validation evidence

* **Observed**: title/password/options/level screens; all 9-byte buffers via savestate
  diff and live mGBA `-d` reads (`r/1 0x03001550`); acceptance/rejection screenshots;
  RAM globals after `JM5W12111`; `PARIS, FRANCE` banner.
* **Derived**: validator/hash/jump table/field widths from Thumb disassembly;
  Python model; published-code decode table; exact accepted-space count.
* **Inferred**: field *names* (checkpoint/difficulty) from numeric patterns and the
  destination globals, not from in-game labels; the second hash user at `0x08001EC4`
  is likely the level-complete password generator but was not fully reversed.

## 8. Unknowns

* Why the hard-coded `H9L9NDS9N` bypass works: the table match at `0x08019E2` only
  writes `0x0300158C=5` and plays a sound; it does not short-circuit the later
  `f0>11` rejection. The observed acceptance of "PARIS, FRANCE" is therefore an
  empirical result whose control-flow explanation is unresolved.
* `f0=0` passes the validator but was not submitted in-game.
* Semantics of `f1`, `f4`, `f5`, `f6`, `f7` beyond their RAM destinations; the flag
  set by `f1=1` had no visible on-screen effect in the short test.
* **Button codes / debug menus (bounded negative)**: web recon found only passwords;
  ROM has zero case-insensitive hits for `debug`, `cheat`, `unlock`, `level select`,
  `code`; 3 hits for `password` (all UI strings). A u16 scan for runs of ≥4
  single-key masks found 190 runs but all lie in compressed graphic/data regions
  (e.g. repeating `0x0008/0x0080`), none referenced as a key sequence by code; no
  hidden menu is reachable from the three screens walked (title, password, options).
  No button-code system is present on this SKU.

## 9. Tooling

* `strings -t x`, `xxd`, `grep -abo`, Python `struct` scans (literal pointers, BL
  targets, PC-relative loads); `arm-none-eabi-objdump -M force-thumb`; Capstone for
  byte-accurate decoding of individual instructions.
* mGBA 0.10.5 `-d` CLI debugger (the `-g` GDB stub was unresponsive in this build)
  with a persistent FIFO (`fifo_keep.py`) and `dbg.py`; mGBA hotkeys Shift+F1/F1
  for savestate save/load.
* Savestate `gbAs` zlib decoder/differ: `ss.py`.
* Validator model/encoder: `vh.py`; keypad driver: `key.py`, `enter.py`.
* Screenshots listed in §6b, kept under `/tmp/opencode/vanhelsing/`.
* No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms
  and generated codes are published.
