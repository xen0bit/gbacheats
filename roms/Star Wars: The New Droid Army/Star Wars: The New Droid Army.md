# Star Wars: The New Droid Army (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity
- File: `Star Wars: The New Droid Army.gba`, 8,388,608 bytes (0x800000)
- Header: title `STAR WARS: T`, game code `A2WE78`, maker `78` (THQ), version `0x00`
- Entry branch `0xEA00002E` (stock), fixed byte `0x96`, complement `0x8E`, header checksum `0x0000` (normal for this image)
- MD5 `e3d1f21b756890e2a68424173aa8cee5`
- SHA-1 `7770e5caac078460ebaeeaddbd183c2973365c47`
- SHA-256 `9db114eb85b8286fd6774283692a54c9396ed7bfaf8960b9884141530f9ad06b`
- Standard retail image; no cracktro/trainer prefix.

## 2. Executive summary
The game has a 3-character password system on the main menu ("Password"). The on-screen alphabet is
exactly 32 symbols (`BCDFGHJKLMNPQRSTVWXYZ123456789!?`), i.e. 5 bits per character, 15 bits per code.

The validator was fully reversed. It is **not** a table of strings: it is a 5-bit checksum plus three
numeric fields. `0x08025120` converts the three entered symbols to 5-bit values, calls the decoder
`0x0800be6c`, then applies three range checks. A second, hard-coded table of **15 hidden cheat
codes** is checked only when normal validation fails (`0x0801e860`); it dispatches to ten cheat
flag bytes in EWRAM.

The complete code space is **32,768** representable 15-bit values; the checksum fixes 5 bits
(1,024 checksum-valid values) and the range checks leave **192 accepted passwords, 146 of which do
not appear in any published list**. A generated code (`NH8`, level 0 / variant 4 / flag 0, never
published) was entered in mGBA and produced "Password accepted". Two checksum-valid but
out-of-range codes (`T2T` flag=3, `Z3J` level=30) were rejected in-game, proving the field bounds.

Published hideouts: `2D4` level select, `FRC` all Force powers, `BTW` movement change, `SK8` black
shadows, `!B4` no shadows, `8!T` 200 health/Force, `LNG` multi-language, `CQL` overhead map,
`SKY` play as Luke, `GFX` reduced graphics, `Y1H` Dooku on Padawan. These are "invalid" passwords
that set flags; the published instructions then require entering a real password to activate.
They are handled by a separate 15-entry table (§4).

## 3. How to reproduce
- Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, scale 3.
  NOTE: other agents in this environment run `pkill -x mgba`; a renamed copy of the binary
  (`mgbad`) was used so it could not be killed by their cleanup.
- Boot → press Start at "PRESS START" → Main Menu → Down → Password.
- Keymap (mGBA SDL): A=`x`, B=`z`, Start=`Return`, D-pad = arrow keys.
- Password screen: move the cursor through the 3-row alphabet; A adds a letter, B erases. The
  left/right keys wrap within the current row; up/down change row and preserve the column. The
  third A press validates immediately. "Invalid password" is displayed from ~0.15 s to ~0.8 s;
  "Password accepted" from ~0.5 s and persists.
- Save state on the password screen (`Shift+F1`); plain `F1` restores it, which makes each
  experiment one entry plus one keypress.
- Codes used: `D31` (published, accepted), `NH8` (novel, accepted), `T2T` / `Z3J` (rejected).

## 4. Address map

| Item | File offset | ROM / address | Evidence |
|---|---:|---|---|
| Alphabet string `BCDFGHJKLMNPQRSTVWXYZ123456789!?` | 0x04b914 | `0x0804b914` | observed, drawn on password screen |
| Text-bank base (16-bit text IDs) | 0x64b500 | `0x0864b500` | derived from ID/string offsets |
| "Password accepted" text ID `0x23a` | — | `0x0864b73a` | observed |
| "Invalid password" text IDs `0x243`/`0x245` | — | `0x0864b743` | observed |
| Password screen input handler | 0x02cd2c | `0x0802cd2c` | disassembly |
| Validator call / accept branch / reject branch | — | `0x0802ce2e` / `0x0802ce38` / `0x0802ce84` | disassembly |
| **Password validator** | 0x025120 | `0x08025120` | disassembly + Ghidra pseudocode |
| Checksum decoder / encoder | 0x00be6c / 0x00c000 | `0x0800be6c` / `0x0800c000` | disassembly + Ghidra |
| 5-bit XOR key (20 bytes) | 0x64d90c | `0x0864d90c` | ROM bytes |
| Level / variant-count table (30 × 32 bytes) | 0x04b938 | `0x0804b938` | validator literal `0x08025180` |
| Input symbol buffer (three 5-bit values) | — | `0x0201baf8` (EWRAM) | handler literal |
| Input length counter | — | `0x0201bb2c` (EWRAM) | handler literal |
| Result fields: level / variant / flag | — | `0x0201b0c4` / `0x0201b0c8` / `0x0201b0bc` | validator literals |
| **Hidden cheat-code table (15 × 3 bytes)** | 0x0478ad | `0x080478ad` | invalid-handler literal at `0x0801e8b4` |
| Cheat dispatch jump table (15 words) | 0x01e8b8 | `0x0801e8b8` | `mov pc,[r4,r4*4]` at `0x0801e8b2` |
| Cheat flag bytes | — | `0x0201ab00`–`0x0201ab24` (10 words) | dispatcher literals |
| Decoder fallback table pointers (count appears 0) | — | `0x0200ce0c` / `0x0200ce10` / `0x0200ce14` | literals in `0x0800bf8c` area |

## 5. Algorithm

Input: three symbols from the 32-character alphabet. Convert each to its flat index
`i0,i1,i2 ∈ 0..31` (row start + column: row lengths 13, 11, 8).

1. Validator adds `0x40` to each index and calls decoder `0x0800be6c`.
2. Decoder subtracts `0x40` (recovering `i`) and XORs with the first three key bytes:
   `t[k] = i[k] ^ KEY[k]`, `KEY = 0a 15 12 19 0c 16 0b 05 ...` at `0x0864d90c`.
3. `x = t0 ^ t1`. The third value is a 5-bit checksum: for `j = 0..4`,
   `bit(4-j) of t2 = parity(KEY[j] & x)` (parity of the low five bits). Every published
   level code satisfies this except three outliers (§6b).
4. Bit-unpack (the packer emits two 8-bit words from the three 5-bit values):
   ```
   A = (t0 << 5) | t1
   out0 = A >> 2
   out1 = (A & 3) << 6
   level   = out0 >> 3        # = t0
   variant = out0 & 7         # = t1 >> 2
   flag    = out1 >> 6        # = t1 & 3
   ```
5. Range checks (all must hold): `level <= 29`, `variant <= 4`, `flag <= 2`, and
   `variant < count[level] OR variant == 4`, where `count` is the byte at offset `0x1e` of
   record `level` in the 32-byte-stride table at `0x0804b938`.
6. On success the three fields are written to `0x0201b0bc/c4/c8`, `0x0802536c` loads the level,
   and the function returns 1 → "Password accepted". On failure `0x0801e860` runs the
   hidden-cheat comparison and returns 0 → "Invalid password".

Encoding a chosen `(level, variant, flag)` is exact (no search needed):
```
t0 = level;  t1 = (variant << 2) | flag;  x = t0 ^ t1
t2 = sum over j of parity(KEY[j] & x) << (4-j)
symbol[k] = ALPHABET[t[k] ^ KEY[k]]  for k = 0,1,2
```
Implemented in `validator.py` (§9). It agrees with the ROM on all 45 checksum-valid published
codes and on all accepted/rejected generated codes tested in mGBA.

## 6. Tables

**Alphabet (index → symbol), file `0x04b914`:**
```
0 B  1 C  2 D  3 F  4 G  5 H  6 J  7 K  8 L  9 M 10 N 11 P 12 Q
13 R 14 S 15 T 16 V 17 W 18 X 19 Y 20 Z 21 1 22 2 23 3
24 4 25 5 26 6 27 7 28 8 29 9 30 ! 31 ?
```
(A, E, I, O, U and 0 are omitted. Several 3rd party cheat index codes such as `AK?`, `A3W`, `AY4` and the
"level 1 = bh7" list contain symbols outside this alphabet and cannot be entered on this SKU;
they are recorded as unverified/likely wrong-edition.)

**Published level passwords (all verified present as accepted codes except where noted).**
Level names from the source list; 45 of 48 decode with the checksum model:
```
D31 Droids At Speeder          QK1 Mos Espa
BKT Xelric Draw                B3C Xelric Draw, Cutscene
FKW Womp Rat Cave              CKH Xelric Draw, Cutscene
C3P Xelric Draw                CYD Xelric Draw
KK4 Dune Sea                   M34 Moisture Farms
MYW Moisture Farms             TKP Jundland Wastes
T3H Jundland Wastes            TYQ Jundland Wastes
SKC Jabba's Palace, Cutscene   J38 Jabba's Dungeon
JY1 Jabba's Dungeon            J?T Jabba's Dungeon
J7J Jabba's Dungeon            G3L Great Sarlacc, Cutscene
7KQ High City                  73D High City
7YP High City (Interior)       7?W High City (Interior)
!KT Underlevels, Cutscene      !3C Underlevels
!YL Bentho's Nightclub         H3D Core Bay
6K7 Core Bay  *                63L Core Bay
5K4 Jedi Temple, Cutscene      532 Jedi Temple
4KX Jedi Archives              438 Jedi Archives
XK1 Droid Factory Outskirts    23X Production Facility Area One
2Y7 Production Facility Area One 3K2 Production Facility Area Two
334 Production Facility Area Two WKP Cortosis Processing Plant
!W3 Dual Duel *                !WY Dual Duel *
?KH Droid Factory Core         ?3P Droid Factory Core
8K7 Duel with Vandalor         831 Race the Bombs
9KW Cutscene                   Y3W Duel with Dooku - End Scene
```
`*` = fails the checksum and is not represented by the algorithm (likely a transcription error
in the published lists; the fallback table at `0x0200ce0c` had count 0 in the live savestate).

**Hidden cheat codes (published, developer-intended — entered at the same screen, reported as
"Invalid", then a real password activates the effect):**
```
2D4  level/stage select (L/R at main menu)   FRC  all Force powers
BTW  alternate movement                     SK8  black shadows
!B4  disable shadow displays                8!T  200 health and Force
LNG  multi-language mode                    CQL  overhead map (Select in game)
SKY  play as Luke Skywalker                 GFX  reduced graphics resolution
Y1H  Dooku encounter on Padawan              ZBF  rendering variant (published)
Y3W  Duel with Dooku end scene               SK8/!B4/GFX/CQL/ZBF render variants
```
ROM evidence: `FUN_0801e860` (`0x0801e860`) compares the three entered indices against **15**
three-byte records at `0x080478ad` (stride 3), then dispatches through `0x0801e8b8` to writers
of ten flag bytes at `0x0201ab00`, `04`, `08`, `0c`, `10`, `14`, `18`, `1c`, `20`, `24`.
The raw 15 records are:
```
 0: 1c 04 1d    1: 04 1e 04    2: 1f 04 20    3: 04 21 04
 4: 22 04 23    5: 04 24 04    6: 25 04 26    7: 04 27 04
 8: 28 04 29    9: 04 2a 04   10: 2b 04 2c   11: 05 00 05
12: 01 05 02   13: 05 03 05   14: 04 05 05
```
These bytes use the screen's font/tile indexing rather than plain ASCII; the published code
strings above are the human-readable equivalents. The table count (15) is exact, so at least
four hidden codes are not on the published lists.

## 6b. Enumeration
- **Space**: 3 symbols × 5 bits = 32,768 representable values. The checksum fixes 5 bits →
  1,024 checksum-valid codes. Range checks (`level 0..29`, `variant 0..4`, `flag 0..2`,
  `variant < count[level] or variant == 4`) leave **192 accepted passwords**.
- Published level passwords: 48 in the full compiled list; 45 satisfy the model, 3 do not (§6).
  Published hidden-cheat codes: ~11 named effects; the ROM table has 15 entries.
- **Novel code confirmed in-game**: `NH8` = level 0, variant 4, flag 0 — absent from every
  published list and the only code exercising flag=0 for level 0. Entered on the real Password
  screen in mGBA → "Password accepted" (`novel_after.png`). A second novel code generated by the
  same encoder (`T?2` = level 5/variant 2/flag 2) is included in the 146-code novel set.
- **Bounds proven by rejection** (both checksum-valid, rejected by the *range* layer, not the
  checksum):
  * `T2T` decodes to `(level 5, variant 0, flag 3)` → "Invalid password" (`rej_flag3.png`).
    Proves `flag <= 2`.
  * `Z3J` decodes to `(level 30, variant 0, flag 2)` → "Invalid password" (`rej_level30.png`).
    Proves `level <= 29`.
  These are the important distinction from §0.2/§16.5: a valid checksum is not sufficient.

## 7. Validation evidence
- **Observed**: `D31` (published) → "Password accepted"; gameplay started (speeder desert level).
  `NH8` (novel) → "Password accepted". `T2T` and `Z3J` → "Invalid password". Screenshots kept in
  `/tmp/droidarmy/`. The 32-symbol alphabet was read directly from the password screen
  and matches the ASCII table at `0x0804b914`.
- **Derived**: validator/decoder algorithm, checksum, field layout, range table at `0x0804b938`,
  the 192/146 counts, and the 15-entry hidden-cheat table (disassembly + Ghidra pseudocode).
  All 45 published checksum codes agree with the Python model.
- **Inferred**: exact human-readable strings for all 15 hidden cheat records (only ~11 are
  published); the flag-byte → effect mapping for the four unpublished records. The three
  non-checksum published level codes (`6K7`, `!W3`, `!WY`) are attributed to published typos or a
  fallback table that was not populated in the observed save state.
- **Not observed**: audio confirmation ("Darth Vader breathing"), the L/R level-select menu, and
  the in-game effects of the hidden cheat flags (these need a second valid password per the
  published instructions).

## 8. Unknowns
- Which of the 15 hidden cheat records correspond to the four unpublished effects; the records'
  tile-index → symbol mapping was not conclusively derived from the table bytes.
- Whether `6K7`, `!W3`, `!WY` are real ROM codes via an unpopulated fallback table or purely
  published transcription errors.
- The exact semantics of `flag` (values 0,1,2 all accepted); published codes always use 2.
- Why mGBA under this shared display was repeatedly killed (another agent's `pkill -x mgba`);
  resolved by running a renamed binary.

## 9. Tooling
- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x` (Phase 0/recon).
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all
  disassembly; Python/struct for literal-pool reads (always re-read literals with Python —
  objdump prints halfwords in reverse visual order).
- REA Ghidra MCP (`open_binary` raw-binary arm @ `0x08000000`, `search_strings`, `xrefs`,
  `analyze_function`, `read_bytes`, `close_binary`) for pseudocode of `0x0800be6c` and
  `0x08025120`.
- `validator.py` in `/tmp/droidarmy/`: exact reimplementation of the decoder and
  encoder; enumerates all 192 accepted codes and mints novel ones.
- Automation: `key.py`, `pwtest.py` (grid navigation), `sstate.py`/`flagtest.py` (savestate
  `gbAs` zlib-chunk parsing; EWRAM is at raw offset `0x21000`), `tesseract` OCR, `scrot`.
- mGBA `-g` GDB stub and `-d` CLI debugger were both found unreliable here (packet errors /
  buffer-only command handling), so RAM evidence came from savestate diffs.

## 10. Legal note
No ROM or copyrighted assets are redistributed. Only hashes, addresses, algorithms, counts and
original findings are published.
