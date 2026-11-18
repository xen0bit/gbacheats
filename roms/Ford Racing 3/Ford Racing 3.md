# Ford Racing 3 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ford Racing 3/Ford Racing 3.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `FORDRACING3` |
| Game code | `BF3E` |
| Maker | `7N` |
| Revision | 0x00 |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0; **no cracktro/patched entry**) |
| Complement / checksum | 0xBA / 0x0000 (rebuilt-header artifact, §16.1) |
| Embedded headers | **1** Nintendo-logo hit at file 0x0 — no multiboot sub-image, no appended trainer |
| MD5 | `a3b2dd184e80764a1a3c0d7799089327` |
| SHA-1 | `fa323718777c3ec1b323341d35d83859f103450f` |
| SHA-256 | `e63e4de1cff312d13ca536af89b41d3e8577c17840ac0f3739e64993ff5bbb2c` |

## 2. Executive summary

Ford Racing 3 (GBA) has a **developer-intended in-game password system** on the
main menu (`ENTER PASSWORD`). It is algorithmic, not a plaintext table: a
6-symbol password over a 64-symbol on-screen alphabet is validated by a
permutation + CRC-8-like checksum + bit-packed field check at ROM
`0x08018E6C`. Accepted codes unlock cars/tracks/competitions (the string bank
contains `PASSWORD ACCEPTED`, `FOCUS RALLY CAR IS NOW AVAILABLE`,
`TAURUS STOCK CAR IS NOW AVAILABLE`, `NEW CAR COLLECTED`,
`CHALLENGE UNLOCKED`).

The system was fully reversed. A baseline code `****M*` (see §6 for the
glyph notation) was generated from the ROM's own decoder and confirmed
**accepted in the emulator** (validator return 1 via the GDB oracle; on the real
screen entry returns to the main menu). A **novel code not in any published
list**, `****U*`, was minted by setting a previously unset unlock bit, accepted
by the oracle and by the real screen, and **RAM-verified** to change unlock
state `0x030000E4` from `0x00` to `0x01` (§6b). Bounds were proven by rejection:
a one-symbol checksum change and the published `B7BBxB` both return 0.

Published web codes were located and verified against the ROM: none appear as
literals; `B7BBxB` passes the checksum but **fails both range limits**, so it is
a bad/unverifiable submission (§7).

## 3. How to reproduce

- Emulator: mGBA (SDL build), `SDL_AUDIODRIVER=dummy`, Xvfb `:319`, 3× scale.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold ~120–200 ms per press (§16.2 double-step caution).
- Menu path: boot → Start through warning/legal/attract → **MAIN MENU** →
  `ENTER PASSWORD`. On the password screen a 4×16 symbol grid is navigated with
  the D-pad; **A** appends the highlighted symbol, **B/Select** delete, and the
  validator runs **automatically when the 6th symbol is entered** (call site
  `0x0800E282`: `count = [0x03007070]+1; if count > 5: bl 0x08018E6C;
  if r0 != 0: bl 0x080190F8` (accept handler)).
- Screens walked with evidence (screenshots + savestate RAM snapshots kept in
  `/tmp/opencode/ford3/work/`): DSI/Ford logo splash, warning, legal text,
  "PRESS START" attract, MAIN MENU, in-race HUD, PAUSE (`CONTINUE / RESTART /
  QUIT RACE`), quit-confirm (`NO/YES`), race-results banner, and ENTER PASSWORD.
- Codes tested: published `B7BBxB` (rejected), ROM-generated `****M*`
  (accepted), novel `****U*` (accepted).

Oracle reproduction (guide §16.19): set an execution breakpoint at
`0x0800E286` (one instruction after `bl 0x08018E6C`), enter any 6 symbols via
the real UI, read `r0` at the breakpoint — `1` = accepted, `0` = rejected. This
uses the ROM's own validator, so no decoder reimplementation is needed for
ground truth.

## 4. Address map

| Item | ROM / RAM address | Notes |
|---|---|---|
| Password validator / encoder | `0x08018E6C` (Thumb) | called only from `0x0800E282` |
| Password decoder | `0x08018DE8` (Thumb) | packed state → 6 symbols; called from `0x0800E3C8`, `0x801740C`, `0x80184DE` |
| Accept handler | `0x080190F8` (Thumb) | applies unlock flags, writes global state |
| CRC-8 table (256 B) | `0x08029998` | `t[1]=0x07, t[2]=0x0E` … (CRC-8 poly 0x07) |
| Checksum helper | `0x0800CAEC` (Thumb) | `acc=0; for c in data: acc = table[acc ^ c]; return acc` |
| Range constants | `0x080190D4` = `0x0003FFFE`, `0x080190D8` = `0x000007FE` | max for r6 / r7 |
| Input buffer (6 B) | IWRAM `0x03007078` | holds 6 symbol indices 0–63 (Observed via savestate diff) |
| Input count byte | IWRAM `0x03007070` | increments per A press; validator runs when >5 |
| Unlock state (packed) | IWRAM `0x030000E4`, `0x030000F0` | r6/r7 payload of the decoder |
| Text bank (ASCII) | `0x080F7363`–`0x080FD000` | `ENTER PASSWORD` @ `0x080F747E`, `PASSWORD ACCEPTED` @ `0x080F7850`, unlock strings @ `0x080FB7EB`/`0x080FB88D` |
| Shin'en audio banner | `0x080EBFC5` | `Code: B.Wodok` — audio-engine string, not a cheat (§11) |

## 5. Algorithm

Alphabet (64 symbols, grid order row-major 4×16):
`A-Z` (indices 0–25), `0-9` (26–35), `a-z` (36–61), `*` (62, orange star),
`?` (63). Symbol indices are stored directly in the 6-byte input buffer.

Validation of input `p[0..5]` (each 0–63), transcribed from `0x08018E6C`:

1. Permute into a local 6-byte array `s`:
   `s = [p4, p5, p2, p3, p0, p1]`.
2. For `i=1,2,3`: `s[i] = (s[i] XOR 0x3E) & 0x3F`.
   For `i=4,5`: `s[i] = (s[i] XOR 0x3E) & 0x3F`, then `r7 &= 0xFFFF`.
3. `r6 = ((s1) | (s2<<6) | (s3<<12))`  — 18-bit field (4 groups × ~4.5 bits).
   `r7 = (s4 | (s5<<6))`  — 11-bit field (5 groups).
4. `check = crc8(s[1..5])`; `checkbyte = (check >> 2) & 0x3F`.
   Require `checkbyte == s[0]` (= `p[4]`).
5. Require `r6 <= 0x0003FFFE` and `r7 <= 0x000007FE`.
6. A chain of ~20 conditional bit-implication checks on `r7` then `r6`
   (`0x8018F00`–`0x8019090`): for each mask pair A/B, if `(field & A)` then
   `r4/r5 = field & B`; at the end both `r4` and `r5` must be nonzero.
   These enforce a valid unlock combination (e.g. dependent car/track/competition bits).
7. On success `bl 0x080190F8`: write unlock flags/state and return to main menu.

The decoder `0x08018DE8` is the inverse: given packed fields `(v1,v2)` at
`0x030000E4/F0`, it produces the 6 symbol indices (including the CRC checkbyte)
that the validator will accept. This is the generator used to mint codes below.

Pseudocode (verified against the validator oracle):

```python
T = rom[0x29998:0x29998+256]
def crc8(d):
    a = 0
    for c in d: a = T[a ^ c]
    return a
def encode(v1, v2):           # v1 <= 0x3FFFE, v2 <= 0x7FE
    d = [0]*6
    for i in (1,2,3): d[i] = ((v1 >> (6*(i-1))) & 63) ^ 62
    for i in (4,5):   d[i] = ((v2 >> (6*(i-4))) & 63) ^ 62
    cb = (crc8(d[1:6]) >> 2) & 63
    return [d[4], d[5], d[3], d[2], cb, d[1]]   # output permutation
```

## 6. Tables

- Alphabet indices: `A`=0 … `Z`=25, `0`=26 … `9`=35, `a`=36 … `z`=61,
  `*`=62 (star glyph), `?`=63. The small grid font renders several letters in
  a stylised way (`A` looks like `?`, `E` like `:`, `O` like `!`), so glyph
  appearance is not a reliable index guide — the **buffer bytes are** (read via
  savestate diff: entering grid indices `2,3,4,5,6,7` wrote `02 03 04 05 06 07`
  at `0x03007078`).
- Check byte: symbol index at `p[4]`; equals `(crc8(p5,p2,p3,p0,p1) >> 2) & 63`.
- Field payloads: 18 bits (`r6`) from `p[5],p[2],p[3]`; 11 bits (`r7`) from
  `p[0],p[1]`, each 6-bit slice XOR 0x3E.
- CRC-8 polynomial 0x07 table at `0x08029998`.

Accepted / rejected examples (oracle r0):

| Code (grid symbols) | Indices | r0 | Why |
|---|---|---|---|
| `****M*` | 62,62,62,62,12,62 | **1** | baseline, state (0,0) |
| `****U*` | 62,62,62,62,20,63 | **1** | novel, state (1,0) |
| `****N*` | 62,62,62,62,13,62 | 0 | wrong check byte (M→N) |
| `B7BBxB` | 1,33,1,1,59,1 | 0 | CRC passes but r6=0x3FFFF>0x3FFFE and r7=0x7FF>0x7FE |

## 6b. Enumeration

- **Space definition**: 6 symbols × 64 values = 64^6 = 68,719,476,736 raw
  spellings. The validator's structure means a code is determined by an
  18-bit payload (max 0x3FFFE), an 11-bit payload (max 0x7FE), a 6-bit check
  byte derived from the other five symbols, and the bit-implication layer
  (step 6). Representable accepted states are therefore bounded by
  `0x3FFFE × 0x7FE ≈ 5.2×10^8` payload combinations before the implication
  filter; each has exactly one spelling (its check byte is forced).
- **Validator model**: §5 pseudocode agrees with the ROM on accepted and
  rejected inputs (cross-checked against the oracle for the four rows in §6).
- **Novel code minted**: `****U*` (indices `62,62,62,62,20,63`), produced by
  decoding state `v1=0x0001, v2=0x0000`. It appears on no published list
  (chaptercheats lists only `B7BBxB` and a star-symbol description;
  supercheats lists `Xstar(*)B?k7`). Oracle r0=1; entering it on the real
  password screen returned to the main menu, and a savestate diff showed
  IWRAM `0x030000E4: 0x00 → 0x01` and `0x030000F6: 0x01 → 0x21`, proving a
  different unlock state from the baseline code.
- **Bounds proven by rejection**: (a) changing only the check symbol
  `M`(12)→`N`(13) in the accepted baseline gives r0=0; (b) the published
  `B7BBxB` has r6=0x3FFFF (one above the 0x3FFFE limit) and r7=0x7FF (one
  above 0x7FE) and gives r0=0. Both were driven through the ROM validator.

## 7. Validation evidence

- **Observed**: boot/screens/screenshots; buffer bytes at `0x03007078`
  (savestate diff, §4); oracle r0 values for four codes; main-menu return on
  acceptance; RAM diff `0x030000E4` 0x00→0x01 for the novel code.
- **Derived**: validator/encoder algorithm, CRC table base (`0x08029998`,
  corrected from an initial endianness slip `0x08029899`), field widths,
  range constants, permutation, decoder inverse, call site `0x0800E282`.
- **Inferred**: semantic meaning of individual `r6`/`r7` bits (car / track /
  competition / challenge categories) — the accept handler at `0x080190F8`
  writes several flag words, but individual bits were not each mapped to a
  specific unlock message. The exact visible message (`PASSWORD ACCEPTED`) was
  not captured because the screen transition to the main menu happens within
  one frame; acceptance is evidenced by the menu return, oracle r0, and RAM diff.
- **Published codes** (fetched as data; no instructions from fetched pages were
  followed): chaptercheats `B7BBxB` ("Unlock Everything") and
  `v gold star w gold star = gold star`; supercheats `Xstar(*)B?k7`. None occur
  as literals in the ROM under ASCII, case-shift, +/−1, XOR, 6-bit packing or
  index encodings, confirming an algorithmic validator. `B7BBxB` specifically
  fails the ROM's range checks — probably a transcription error in the list.
  A GameFAQs cheats archive was located via CDX but Wayback returned HTTP 429;
  a Super Cheats Q&A comment claims GBA codes are bogus — that claim is
  contradicted by the ROM evidence above (a real validator exists and accepts
  generated codes). Web sources contained no prompt-injection instructions.

## 8. Unknowns

- Exact per-bit mapping of the 18-bit/11-bit payload to specific cars, tracks,
  race types and competitions (the accept handler sets them, but each bit was
  not individually observed on a selection screen).
- The complete set of bit-implication constraints in step 6 was transcribed
  into a working model but not formally minimised; the accepted set is smaller
  than the raw `(0x3FFFE × 0x7FE)` payload rectangle.
- Save-device persistence: the `.sav` file is 0 bytes; unlocks appear to be
  held in IWRAM and written by the accept handler; long-term save format not
  examined.

## 9. Tooling

- `strings -t x`, `grep`, `xxd`, `arm-none-eabi-objdump -M force-thumb`
  (validator/encoder/checksum disassembly), Python 3 (CRC/decoder model),
  Capstone-style PC-relative literal scans, custom RSP client for mGBA's GDB
  stub, mGBA savestate `gbAs` zlib reader (`ss.py`) for RAM evidence,
  REA/Ghidra 12.1.4 (raw ARM load; auto-analysis found only 269 ARM procedures
  and gave no string xrefs — Thumb bodies were decoded with objdump instead).
- No ROM or copyrighted assets are redistributed; only addresses, hashes and
  the reimplemented algorithm are published.
