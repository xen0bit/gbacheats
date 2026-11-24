# Rocket Power: Beach Bandits (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rocket Power: Beach Bandits.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `RCKTPWRBCHBN` |
| Game code | `AR4E` (USA/Europe, E) |
| Maker code | `78` |
| Version | 0x00 (Rev.00) |
| Entry word | `0xEA00002E` → stock `0x080000C0` |
| Header complement/check | stored 0x4C / 0x0000 (non-standard but common; no trainer) |
| MD5 | `6c1de42661ca9ca859620753d8e12083` |
| SHA-1 | `7d2d12e7f85793fe787a342b00d63685a56230b6` |
| SHA-256 | `9f229c62af186e757ad99079ae353e815a461af0311f21e8800c782b99bcf46e` |

**Embedded-header scan:** exactly one Nintendo-logo hit (file 0x4 → header base `0x08000000`). No appended trainer, no multi-game pack, no patch/cracktro.

## 2. Executive summary

The game contains a **developer-intended 8-symbol password system** with an on-screen
32-character keyboard (`BCDFGHJKLMNPQRSTVWXYZ123456789!?`). There is **no hard-coded
password string table** — the three published passwords do not occur literally in the
ROM under any ASCII encoding. Instead the game *generates* validity with a two-stage
algorithm:

1. **Stage 1 (`0x0802B0B4`)** — an affine transform over GF(2): XOR a fixed 8-byte
   constant into the 8 five-bit symbol values, perform two triangular XOR passes,
   compute a 6-byte XOR checksum, and verify **10 parity bits** against a 10-byte
   mask table. Output is a 4-byte packed key written to `0x0203FB64`.
2. **Stage 2 (`0x08007DF8`, reached via the function pointer at `0x0203FB4C`)** — a
   *semantic* field decoder that unpacks `area`, `level index`, `variant` and flag bits
   and applies a compatibility table. A password can pass stage 1 and still be
   rejected here (proved with `HRZTZNPQ`, §6b).

Published codes were verified against the ROM and the emulator; a novel code
`JWR247Y!` (area 1 / index 11 / variant 1) was synthesised offline, accepted by the
game, observed on-screen, and produced a distinct level. All results are reproducible
from the address map below.

## 3. How to reproduce

- Emulator: mGBA (SDL build), 3× scale, headless `Xvfb :315`, `SDL_AUDIODRIVER=dummy`.
- Keymap: A = `x`, B = `z`, Start = `Return`, D-pad = arrow keys. Hold ~120–150 ms.
- Path: boot → press Start through intro/title/legal screens → main menu
  **NEW GAME / PASSWORD / OPTIONS** → select **PASSWORD** → 32-key keyboard.
- Entering 8 symbols triggers validation automatically. Accepted:
  `password accepted, press START to play`; rejected: `invalid password, press B to erase`.
  Press Start on acceptance to launch the level.
- Password screen is also reachable **in-game** from the pause menu
  (`PASSWORD / MAP / QUIT`).
- Precise RAM experiments used mGBA's command-line debugger (`mgba -3 -d`):
  breakpoints `b/t 0x0802B0B4` (stage 1), `b/t 0x08007FF4` (stage-2 reject),
  `b/t 0x08007FF8` (stage-2 accept); input buffer written with `w/1 0x0203FAB<i> <0x40+index>`.
  This avoids the flaky on-screen cursor and exercises the game's own validators.

Published codes verified:

| Code | Claim | ROM literal | Result |
|---|---|---|---|
| `K4DYNZ8G` | Secret Level / Eric Golem Jr. Defeated | absent | accepted; launched secret level |
| `2CX1BNYR` | The Lakes | absent | accepted (stage-1 output `23 01 0C 00`) |
| `?8H?LZGH` | Defeat Cyrax Computer | absent | accepted by offline model (`34 45 3C 00`) |

`?` is a **real 32nd symbol**, not a wildcard (the on-screen keyboard ends `! ?`).

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Stage-1 validator | `0x0802B0B4` | breakpoint, called from `0x08031A9E` |
| Stage-1 caller / dispatch | `0x08031A8C`–`0x08031B1A` | disassembly + LR `0x08031AA3` / `0x08031B0D` |
| Stage-2 validator | `0x08007DF8` | fn ptr `0x08007DF9` @ `0x0203FB4C` |
| Stage-2 success / reject | `0x08007FF8` / `0x08007FF4` | breakpoints |
| Index-bound helper | `0x08008404` (returns 26) | disassembly |
| Constant / parity-mask table | `0x0832E8B8` | literal at `0x0802B224` |
| Input buffer (8 bytes) | `0x0203FAB0` | observed `40 40 40 ...` for `BBBBBBBB` |
| Password length | `0x0203FAC0` | compared with 8 in caller |
| Stage-1 output (4 bytes) | `0x0203FB64` | observed `21 79 7C 7E` for `K4DYNZ8G` |
| Accepted flag byte | `0x0203FB6C` | 0 rejected / 1 accepted |
| Message handler pointers | `0x0203FB30` (invalid = `0x08025C31`), `0x0203FB40` (accepted = `0x08025C0D`) | RAM read |
| UI strings | instructions `0x0803C57C`, accepted `0x0803C5A8`, invalid `0x0803C5D0`, menu `0x0803C610`–`0x0803C658` | `strings -t x` + pointer scan |
| Level names / map text | `0x0803BE78`–`0x0803BEA0` (`The Lakes`, `Secret Level`, `Shore Shack`, `(LOCKED)`, `(COMPLETE)`) | `strings -t x` |

## 5. Algorithm

Alphabet (index = key position, left→right, top→bottom):

```
 0 B   1 C   2 D   3 F   4 G   5 H   6 J   7 K
 8 L   9 M  10 N  11 P  12 Q  13 R  14 S  15 T
16 V  17 W  18 X  19 Y  20 Z  21 1  22 2  23 3
24 4  25 5  26 6  27 7  28 8  29 9  30 !  31 ?
```

The buffer byte for symbol *i* is `0x40 + i` (stage 1 subtracts 0x40).

**Stage 1** (`v[0..7] = input byte − 0x40`; `T = bytes @ 0x0832E8B8`):

```
for i in 0..7:  a[i] = (v[i] XOR T[i]) & 0xFF     # T[0..7] = 0A 15 12 19 0C 16 0B 05
for k in 1..5:                                    # triangular XOR forward
    for j in 0..(7-k): a[j] ^= a[k+j]
for k in 1..5:                                    # triangular XOR backward
    for j in 0..(7-k): a[k+j] ^= a[j]
c = XOR(a[0..5])
for byte b in (a[6], a[7]):                       # 10 parity checks
    for bit p = 4 down to 0:
        require parity( T[10 + n] & c & 0x1F ) == (b >> p) & 1
        n += 1                                    # T[10..19] = 14 1A 0D 06 13 09 18 1C 0E 07
# pack a[0..6] as 5-bit groups into 4 output bytes (the 5-bit bit-stream counter
# persists across bytes; a[7] is not consumed):
acc=0; r2=0; j=0
for out_i in 0..3:
    while r2 <= 7: acc = (acc<<5) | a[j]; j++; r2 += 5
    r2 -= 8; out[out_i] = acc >> r2; acc = (acc << (32-r2)) >> (32-r2)
```

**Stage 2** (fields from the 4-byte output `o`):

```
idx     = o[0] & 0x1F       # must be < 26 (helper 0x08008404)
area    = o[1] & 0x0F       # must be <= 9
variant = (o[1] >> 4) & 7
count   = popcount(bits 2..6 of o[2]) + popcount(bits 2..6 of o[3])
tail    = popcount(bits 2..6 of o[3])
if count == 5: require area > 6; if tail == 5 require area > 8
area==9  -> idx must be 1
area==0  -> idx in {0,20} and variant==0
area==1  -> idx in {0..4,11,20}; idx>4 and idx!=11 -> variant!=0; variant<=1
area==2  -> idx in {0..4,11,20} and variant==2
area==3  -> idx<=11 or idx==20; variant in {2,3}
area==4  -> variant==4;  area==5 -> variant in {4,5}
area==6  -> variant==6;  area==7 -> variant==6;  area==8 -> variant==7
```

All conditions above were transcribed from the Thumb disassembly and cross-checked
against all three published codes plus rejected inputs.

## 6. Tables

| Symbol space | 32 symbols, 5 bits each, 8 symbols = 40-bit input |
|---|---|
| Stage-1 check | 10 linear GF(2) parity bits → 30-bit equivalent payload |
| Stage-1 accepted inputs | 32^8 / 2^10 = **1,073,741,824** |
| Stage-2 | filters on `area/index/variant/flags`; empirical pass rate ≈ 1/64 of stage-1 |
| Combined estimate | ≈ **1.6 × 10^7** accepted 8-symbol spellings (≈ 2^24) |
| Published samples | `K4DYNZ8G` → `21 79 7C 7E` (area 9, idx 1, var 7) |
| | `2CX1BNYR` → `23 01 0C 00` (area 1, idx 3, var 0) |
| | `?8H?LZGH` → `34 45 3C 00` (area 5, idx 20, var 4) |

The stage-1 constant table (ROM `0x0832E8B8`):

```
XOR[0..7]  = 0A 15 12 19 0C 16 0B 05
MASK[0..9] = 14 1A 0D 06 13 09 18 1C 0E 07
```

## 6b. Enumeration

**Space** — 32^8 = 1,099,511,627,776 possible 8-symbol strings. Stage 1 accepts
exactly 2^30 of them (verified empirically: 194/200,000 random codes ≈ 2^−10).
Stage 2 removes roughly another 6 bits (3/194 sampled), leaving ≈ 1.65 × 10^7
accepted spellings.

**Novel code, absent from every published list:**

```
JWR247Y!   -> stage-1 output CB 91 0C FA (area=1, idx=11, variant=1)
```

* Generated with the offline encoder/solver (seed 20261119), not found on
  GameFAQs, VGChartz, TCRF, SuperCheats, Planet Cheats or GameGenie.
* Entered by writing `46 51 4D 56 58 5B 53 5E` to `0x0203FAB0..B7` at the stage-1
  breakpoint; stage 1 produced `CB 91 0C FA` at `0x0203FB64` (RAM read).
* Stage-2 **success path** breakpoint `0x08007FF8` hit with `r0 = 1`.
* On-screen result: `password accepted, press START to play`; accepted flag
  `0x0203FB6C = 0x01` (RAM read).
* Pressing Start launched a **distinct level** (orange/lava stage with a
  skateboarding character, 5 rockets in HUD) — screenshot `novel_effect.png`.
  This exercises an unadvertised area/index/variant combination.

**Bounds proven by rejection:**

| Test | Result |
|---|---|
| `BBBBBBBB` (all index 0) | `invalid password`; stage-1 parity check fails |
| `LLLLLLLL` (all index 8) | `invalid password` |
| `HRZTZNPQ` — stage-1 **valid**, output `21 41 79 D5` | stage 2 rejects it: `invalid password` (checksum-valid but semantically out of range) |
| `idx >= 26` / `area > 9` / incompatible `variant` | rejected by stage-2 field checks |

These demonstrate both layers separately: a wrong check fails stage 1, and a
correct check with an impossible field combination fails stage 2.

## 7. Validation evidence

- **Observed** (emulator, display :315): title/menu/password/options/map/pause screens;
  `password accepted` and `invalid password` messages; accepted flag `0x0203FB6C`
  changing 0→1; distinct levels launched by `K4DYNZ8G` and `JWR247Y!`; stage-1 output
  bytes at `0x0203FB64`; breakpoint hits at `0x0802B0B4`, `0x08007DF8`, `0x08007FF8`.
- **Derived** (disassembly): both validators, the constant/mask table, the packing
  routine, the field-compatibility table, and the GF(2) linearity.
- **Inferred**: exact narrative meaning of `area`/`variant` field names; `0x0203FB4C`
  is installed as a function pointer by earlier game code not fully traced.
- Fetched web pages were treated strictly as data; one CodeBreaker page contained
  memory-edit codes, which are out of scope and were not used.

## 8. Unknowns

- Precise human-readable names for `area` / `variant` / `idx` fields; the field
  decoder writes them into a state struct at `0x0200B1A0+` but no labels exist.
- Whether every one of the ≈16.5M accepted spellings maps to a distinct game state
  (aliasing is likely: unused flag bits exist).
- The on-screen cursor navigation was unreliable under XTEST; all deterministic
  input for this analysis was therefore delivered by writing the RAM input buffer
  at the validator breakpoint, which still executes the game's own validators.
- `?8H?LZGH` was validated by the offline model and ROM disassembly, not re-entered
  in the emulator during this session.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for validator disassembly.
- Python 3 + `validator.py`, `validator2.py`, `gen_novel.py` (GF(2) model, encoder,
  enumeration; scripts in `/tmp/rocketpower/`).
- mGBA `-d` command-line debugger on `Xvfb :315` for breakpoints, RAM reads/writes;
  `xdotool` for input; `scrot` for screenshots (kept in `/tmp/rocketpower/`).
- `strings -t x`, `grep -abo`, `xxd`, `sha*sum` for Phase 0/1.

No ROM, graphics, or copyrighted text are redistributed here — only addresses,
hashes, algorithms and original generated examples.
