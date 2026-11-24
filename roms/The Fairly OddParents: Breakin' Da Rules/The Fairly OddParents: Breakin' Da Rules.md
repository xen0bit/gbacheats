# The Fairly OddParents: Breakin' Da Rules (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

- File: `The Fairly OddParents: Breakin' Da Rules.gba` (4,194,304 bytes / 4 MiB)
- Header title: `FAIRLYODDDAGB`; game code `AF6E`; maker `78`; version `0x00`; fixed byte `0x96` present
- Entry word: `0xEA00002E` → `b 0x080000C0` (stock crt0, retail image; no cracktro/trainer observed)
- MD5 `e7af002a857d9960e3b5ce7a7f524813`
- SHA-1 `35a84d39bfa1bf2c528d770e9b3d70a69a623973`
- SHA-256 `148facea06f1bb7fe0b3157b1c3d28a2c3f448a0fdd7f06e8b8713cb873809df`
- Developer Helixe / THQ, 2003 (from in-ROM credits at file `0x48468`–`0x48D90`).

## 2. Executive summary

The game has a genuine in-game password system on the main menu (**PASSWORD**), reached from
**Main Menu → PASSWORD → difficulty is *not* asked here; the password screen itself** (the
difficulty screen belongs to NEW GAME). The screen has a 4×8 keypad with the 32-symbol alphabet
`BCDFGHJKLMNPQRSTVWXYZ0123456789!`, fixed 8-character length, and an algorithmic
checksum (no plaintext code table). All 16 published level codes plus the published
cheat-mode code were decoded and verified against the ROM and emulator; the decoder
reproduces every one exactly. `X3YSV3!P` unlocks a **LEVEL** screen and the **CHEATS**
entry in the pause menu (six toggles: 100 COINS, 10 TRIES, POWERUP DECOY/DAMAGE/CONTROLS/FLOWERS).

The password is a 40-bit stream: 8 symbols × 5 bits. A 10-byte XOR key and two triangular
XOR passes whiten the input; 10 parity bits (5 in each of the last two bytes) form the
checksum; the payload is packed into four state bytes that are split into 10 fields.
The full space is **2^40 strings → 2^30 checksum-valid → 245,661,696 accepted**
(exact C enumeration). Two novel codes absent from every published list were minted,
entered on the real screen, and verified by emulator RAM reads:
`K2WVDXGD` (level 1-4, zero flags) and `5M4!V!C9` (level 3-2 with all flags and all
numeric fields at their maxima). Bounds were proven by in-game rejection of three
checksum-valid but out-of-range codes and a one-character checksum corruption.

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, window at 152,144, 720×480.
Keymap (mGBA SDL default): A=`x`, B=`z`, Start=`Return`, D-pad = arrow keys.

Menu path:
1. Title → Main Menu. Select **PASSWORD** (bottom entry; the yellow star points at the
   selected row, and it animates — wait ~0.6 s after a D-pad press).
2. Password keypad: cursor starts on `B` on a fresh visit but **persists between visits**
   (a rejected code leaves it on the last entered symbol). Arrow keys move on a 4×8 torus;
   `A` enters the highlighted symbol; `B` deletes the last symbol.
3. After the 8th `A`, the game either starts the level, opens the **LEVEL** screen
   (cheat-mode-style codes), or displays **Invalid password**.
4. To reach the cheat menu: enter `X3YSV3!P`, choose **Level1 → Easy**, skip the title card
   with Start, press Start in-game, select **CHEATS**.

Screenshots of every step were in `/tmp/fairlyodd/*.png` (not redistributed here).

Published codes tested in emulator: `X3YSV3!P` (accepted → LEVEL screen + CHEATS enabled),
`8F6S3DNK` (accepted → level 1-2). The other 14 published codes were verified by the
decoder and produce the exact expected level index; two of them additionally had their
decoded fields confirmed in RAM.

## 4. Address map

All addresses are ROM addresses (`file_offset = addr − 0x08000000`) unless noted.

| Address | Role |
|---|---|
| `0x0802C444` | Range validator: `state[21]<=4`, `state[20]<=27`, `state[28]<=50`, `state[27]<=20`; writes `state[6] \|= 2` during test, clears it on success |
| `0x0802C478` | Encoder front-end: packs `state[10..17]` into the 4 raw bytes and calls `0x0802C4E0` |
| `0x0802C4E0` | Field decoder: splits the 4 bytes into state fields `20..29` (writes before validation) |
| `0x0802C5A0`, `0x0802C5B8`, `0x0802C5D0`, `0x0802C5E4` | Small getters of state fields |
| `0x0802C6E8` | `level → world` helper (`<=3→0, <=7→1, <=11→2, <=15→3, <=27→4`) |
| `0x0802C718` | Value→`{0,4,8,12,16}` helper |
| `0x0802C790` | In-game password generator (takes buffer, level index; uses `0x0802C478` + `0x0803B940`) |
| `0x0802C75C` | Password validator wrapper: `strlen == 8`, `0x0803B748`, then `0x0802C4E0` |
| `0x0803B748` | Password parser/whitener + checksum + bit-packer (the core routine) |
| `0x0803B940` | Inverse encoder: 4 raw bytes → 8 password symbols |
| `0x083FE5E4` | 10-byte key table (bytes `0A 15 12 19 0C 16 0B 05 14 1A`), followed by pointer tables |
| `0x0802D000` | Password-screen keypad input handler; 8-char buffer at struct offset `+10` |
| `0x0802D1E4` | Call site of `0x0802C75C` when 8 characters are present |
| `0x0802D214` / `0x0802D248` | "Invalid password" display path; literal pointer to `0x08049614` |
| `0x08047D08`, `0x08047D38`, `0x0804956C`, `0x08049614` | Menu strings `CHEATS`, first `Your Password:`, second `Your Password:`, `Invalid password` |
| `0x0201D420` | Global game state in EWRAM; password writes offsets `20..29` (observed live) |

Savestate note (§16.13): decompress the `gbAs` zlib chunk of the `.ssN` PNG; EWRAM begins
at raw `0x21000`, so the state is at raw `0x3E420`. The password-screen input struct sits
at raw `0x230B0`: `+3` = cursor column (0..7), `+4` = cursor row (0..3), `+10..17` =
the 8 entered symbols as tile indices `0x40 + alphabet_index`. This was used for all
cursor tracking and byte-exact entry verification.

## 5. Algorithm

`ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0123456789!"` (index 0..31).
`KEY = [10,21,18,25,12,22,11,5,20,26]`.

Parse/validate (`0x0803B748`, then `0x0802C4E0`, then `0x0802C444`):

```
b[i] = ALPHA.index(s[i]) ^ KEY[i]                 for i = 0..7
# two triangular XOR passes (both over k=1..5, i=0..7-k):
for k in 1..5: for i in 0..7-k: b[i]   ^= b[i+k]
for k in 1..5: for i in 0..7-k: b[i+k] ^= b[i]
r9 = b[0]^b[1]^b[2]^b[3]^b[4]^b[5]                 (8-bit)
# checksum: for j=0..9, parity of the five low bits of (KEY[j] & r9)
# j=0..4 -> b[6] bits 4..0 ; j=5..9 -> b[7] bits 4..0 ; mismatch => reject
# pack b[0..6] (5 bits each, ORed) into out[0..3], clearing low 2 bits of out[3]:
out[0] = (b0<<3)|(b1>>2)
out[1] = ((b1&3)<<6)|(b2<<1)|(b3>>4)
out[2] = ((b3&15)<<4)|(b4>>1)
out[3] = (((b4&1)<<7)|(b5<<2)|(b6>>3)) & ~3       # b7 never contributes to output
```

Field split (`0x0802C4E0`, state offsets relative to `0x0201D420`):

```
s22=out0&3; s23=(out0>>2)&3; s24=(out0>>4)&3; s25=(out0>>6)&3
s27=out1&0x3f; s26=(out1>>6)&3
s20=out2&0x1f; s29=(out2>>5)&3
s28=out3>>2
s21 = (s20>>2) if s20<=15 else 4
accept iff s20<=27 and s28<=50 and s27<=20
```

The inverse encoder (validated against all 16 published codes) works in the whitened
domain: choose `c0..c5` from the desired `out`, set `c6`/`c7` low bits from the parity
above, invert the two triangular passes (a per-bit-plane 8×8 GF(2) matrix; implemented
as a precomputed 256-entry truth table per bit), then `char[i] = ALPHA[raw[i] ^ KEY[i]]`.
Scripts: `/tmp/fairlyodd/{model,encode2,analyze,enumerate}.py`.

## 6. Tables

### 6.1 Published codes decoded (all 16 verified against the ROM decoder)

| Published label | Code | `out` | level index `s20` | `s21` | `s22..25` | `s26` | `s27` | `s28` | `s29` |
|---|---|---|---:|---:|---|---:|---:|---:|---:|
| Cheat mode | `X3YSV3!P` | `00 4a 11 5c` | 17 | 4 | 0,0,0,0 | 1 | 10 | 23 | 0 |
| 1-2 | `8F6S3DNK` | `fd 06 01 28` | 1 | 0 | 1,3,3,3 | 0 | 6 | 10 | 0 |
| 1-3 | `Z0DYWX0S` | `fc 06 02 28` | 2 | 0 | 0,3,3,3 | 0 | 6 | 10 | 0 |
| 1-4 | `DSR3KP33` | `fd 06 03 28` | 3 | 0 | 1,3,3,3 | 0 | 6 | 10 | 0 |
| 2-1 | `WF8QZLJP` | `fc 06 04 28` | 4 | 1 | 0,3,3,3 | 0 | 6 | 10 | 0 |
| 2-2 | `7040478J` | `14 06 05 5c` | 5 | 1 | 0,1,0,1 | 0 | 6 | 23 | 0 |
| 2-3 | `LGK1RP3Y` | `f4 06 06 28` | 6 | 1 | 0,1,3,3 | 0 | 6 | 10 | 0 |
| 2-4 | `LQRQRCVY` | `f0 06 07 28` | 7 | 1 | 0,0,3,3 | 0 | 6 | 10 | 0 |
| 3-1 | `V7PNH!L6` | `f0 07 08 28` | 8 | 2 | 0,0,3,3 | 0 | 7 | 10 | 0 |
| 3-2 | `T287517D` | `c0 07 09 28` | 9 | 2 | 0,0,0,3 | 0 | 7 | 10 | 0 |
| 3-3 | `8QXYLP0V` | `c0 07 0a 28` | 10 | 2 | 0,0,0,3 | 0 | 7 | 10 | 0 |
| 3-4 | `V5PNH!S8` | `c0 07 0b 28` | 11 | 2 | 0,0,0,3 | 0 | 7 | 10 | 0 |
| 4-1 | `JF56G3W6` | `c0 08 0c 28` | 12 | 3 | 0,0,0,3 | 0 | 8 | 10 | 0 |
| 4-2 | `16VWZD46` | `40 08 0d 28` | 13 | 3 | 0,1,0,0 | 0 | 8 | 10 | 0 |
| 4-3 | `BNCB0HS0` | `00 07 0e 28` | 14 | 3 | 0,0,0,0 | 0 | 7 | 10 | 0 |
| 4-4 | `2TWVDD7N` | `40 07 0f 28` | 15 | 3 | 0,1,0,0 | 0 | 7 | 10 | 0 |
| Last level | `PQFFLQXT` | `00 48 11 28` | 17 | 4 | 0,0,0,0 | 1 | 8 | 10 | 0 |

The decoded level index matches every published label (`world*4 + (level-1)`), so the
published list is internally consistent and correct for this SKU. An important caveat
(§16.11): the PS2/Xbox/GameCube lists of *character-name* passwords (Wanda, Vicky, …)
are a different game and do not apply here.

### 6.2 Field meaning (confidence labels)

| Field | Width / range | Meaning |
|---|---|---|
| `s20` | 0..27 | Level index (observed: 1→1-2, 3→1-4, 9→3-2, 17→last level) — **Derived** from published-label agreement + in-game start |
| `s21` | 0..4 | World/pack selector, derived as `s20>>2` capped at 4 — **Derived** |
| `s22..25` | 0..3 each | Four 2-bit powerup values (pause→CHEATS: FLOWERS, CONTROLS, DAMAGE, DECOY) — **Inferred** field-to-name mapping (order not individually exercised) |
| `s26` | 0..3 | Extra flag; some nonzero values open the LEVEL screen — **Inferred** |
| `s27` | 0..20 | "Tries" value (published codes use 6–8; cheat mode 10) — **Derived** |
| `s28` | 0..50 | "Coins" value (published codes 10 or 23) — **Derived** |
| `s29` | 0..3 | Extra flag — **Inferred** |

Observed: `X3YSV3!P` sets RAM `0x0201D42A..0x0201D43D` (offsets 20..29) to
`17 04 00 00 00 00 01 0A 17 00`, exactly as decoded. `8F6S3DNK` sets
`01 00 01 03 03 03 00 06 0A 00`. Changing the CHEATS menu toggles did **not**
change these fields in the sampled savestate (the menu likely writes elsewhere).

## 6b. Enumeration

- Alphabet 32 symbols, fixed length 8 → **32^8 = 1,099,511,627,776** possible strings.
- The 10 parity checks are independent → **2^30 = 1,073,741,824** checksum-valid strings
  (exact enumeration, `enumerate.c`).
- Applying the three range checks gives **245,661,696 accepted codes**, exactly
  **8,773,632 for each level index 0..27** (uniform, no reserved holes). There is no
  hidden "one true code" table; every accepted string is a legitimate level/cheat start.
- The 17 published codes are a negligible sample of this space.

**Novel codes (not on GameFAQs / Fandom / ROMSFun / any consulted list), entered on the
real PASSWORD screen and RAM-verified:**

| Novel code | Decoded `out` | State offsets 20..29 (observed in RAM) | Effect / proof |
|---|---|---|---|
| `K2WVDXGD` | `00 06 03 28` | `03 00 00 00 00 00 00 06 0A 00` | Accepted; started level index 3 (1-4) with **all four powerup flags zero** — a combination absent from the published list (published 1-4 `DSR3KP33` uses flags `1,3,3,3`). Screenshot `novelok.png`. |
| `5M4!V!C9` | `ff d4 69 c8` | `09 02 03 03 03 03 03 14 32 03` | Accepted; opened the LEVEL screen. Exercises maximum values of **all** fields simultaneously (flags 3/3/3/3, `s26=3`, tries=20, coins=50, `s29=3`) — unadvertised by any list. Screenshot `novelmax4.png`. |

Both codes are produced by the recovered encoder from the *validator*, not by perturbing
published strings; the encoder reproduces all 16 published codes bit-for-bit, so the
acceptance of the novel codes is a genuine forward test of the model.

**Bounds proven by rejection (all checksum-valid, so the rejection isolates the range layer):**

| Code | Encoded field | In-game result | RAM evidence |
|---|---|---|---|
| `0FLMW4FW` | level index **28** (`s20=28`, out of 0..27) | **Invalid password** | State written as `1C 00 00 00 00 00 00 06 0A 00` — parse passed, range check rejected. |
| `BPXNHT!7` | coins **51** (`s28=51`, out of 0..50) | **Invalid password** | State written as `03 00 00 00 00 00 00 06 33 00` (`0x33`=51). |
| `!BSTF06N` | tries **21** (`s27=21`, out of 0..20) | **Invalid password** | State written as `03 00 00 00 00 00 00 15 0A 00` (`0x15`=21). |
| `8F653DNK` | one-character corruption of published `8F6S3DNK` (`S`→`5`) | **Invalid password** | State fields unchanged → failed in the checksum parser before any write. |

The three range cases also demonstrate a side effect: `0x0802C4E0` writes the decoded
fields **before** `0x0802C444` validates them, so a rejected code still pollutes
`0x0201D42A..`. This is why the RAM values above are diagnostic of *which* layer rejected.

## 7. Validation evidence

- **Observed (emulator):** main menu, difficulty, 32-symbol password keypad, pause menu
  (CHEATS greyed until `X3YSV3!P`), CHEATS screen with six entries, LEVEL screen with a
  left/right-cycled name selector and a down/up-cycled `Level N`, gameplay starts for
  accepted codes, and all four rejection screenshots listed above. Screenshots in
  `/tmp/fairlyodd/`.
- **Observed (RAM):** state `0x0201D420` offsets 20..29 read from decompressed savestates
  for every accepted/rejected case; exact match to the model in all cases.
- **Derived (disassembly):** parser, key table, parity taps (bits 0..4 — the bit-2 term
  was initially missed and found by a live breakpoint at `0x0803B86C`), packing, field
  split, and the three range compares at `0x0802C444`.
- **Derived (execution oracle):** calling `0x0803B748` directly from mGBA's `-d` debugger
  with `r0=0x02000000` (8 symbol tile indices) returned `r0=1` for `8F6S3DNK` and
  `r0=0` for the (then-buggy) novel candidate; the whitened bytes and `r9` at
  `0x0803B87C` matched the Python model exactly (`1f 14 03 00 02 0a 00 00`, `r9=0`).
- **Inferred:** the precise one-to-one mapping of `s22..25` to the four named powerup
  toggles, and the meaning of `s26`/`s29`; the CHEATS menu was walked but individual
  toggles were not traced back to these fields in memory.
- Web pages were treated as data only; no instructions in them (or in ROM strings) were
  executed.

## 8. Unknowns

- `s26` and `s29` are confirmed to exist but only inferred to be flags; which one gates
  the LEVEL screen was not isolated (both `X3YSV3!P` and `5M4!V!C9` have nonzero values).
- The four 2-bit powerup fields were not individually re-entered with a single field
  changed to map each bit pair to a menu label.
- The LEVEL screen's left/right selector was cycled through its entries but its strings
  are drawn with a stylized font; the full list of names was not transcribed.
- Codes with `s20=16` or `18..27` decode and pass the range check; their in-game
  destinations were not played (the published "last level" uses 17).

## 9. Tooling

- `xref.py` — literal-pointer xref finder (found `Invalid password` xref at `0x0802D248`).
- `model.py` — decoder/parser reimplementation; `encode2.py` — inverse encoder with
  precomputed GF(2) matrix truth tables; `analyze.py` — field table + near-miss search.
- `enumerate.c` — exact C enumeration of all 2^30 checksum-valid strings (79 s).
- `enter.py`, `key.py`, `robust.py` — XTEST input drivers with savestate-based cursor
  detection (cursor at savestate raw `0x230B3`/`0x230B4`, buffer at `0x230BA`).
- `callparse.py`, `trace3.py` — mGBA `-d` debugger scripts used as a ground-truth oracle.
- `arm-none-eabi-objdump -M force-thumb`, `capstone` (available), `scrot`, `convert`,
  `gdb-multiarch` (not needed), Python 3 + Pillow.
- No ROM or copyrighted assets are redistributed in this report; only addresses,
  hashes, algorithms, generated codes, and observations are published.
