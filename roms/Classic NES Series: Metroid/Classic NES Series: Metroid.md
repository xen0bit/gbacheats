# Classic NES Series: Metroid (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Classic NES Series: Metroid/Classic NES Series: Metroid.gba` |
| Size | 1,048,576 bytes (1 MiB) |
| Header title | `NES METROID` (0xA0) |
| Game code / maker | `FMRE` / `01` (0xAC / 0xB0) |
| Version | 0 (0xBC) |
| Complement check | 0xAC (0xBD); sum(A0..BC)=0x3B, so `-(0x3B+0x19)&0xFF = 0xAC` — header body intact |
| Header checksum | 0x0000 (0xBE) — rebuilt-header artifact (§16.1), not an edit signal here |
| Entry word | `0xEA000033` (ARM `b 0x080000D4`) |
| MD5 | `7aa3d0f0c73456c7500f1628767eceb7` |
| SHA-1 | `838da11f879e2fa3ffdef95e1c6d5a54246c1846` |
| SHA-256 | `038ee8d37fadf7711fe331a0d3c96c93dd85d2b5f57fdd1575030f57ced85db4` |
| Embedded NES PRG (128 KiB, extracted from EWRAM) SHA-256 | `4ffde1064c930f177b4b1e88021bdcd4b805e2c1e59a25350ec3ec96fb0c4839` |
| Embedded NES PRG MD5 | `bc5da21da35030c4d6b00dc2689eaf57` |

**Phase 0 checks.** A scan for the 156-byte Nintendo logo found exactly one
header (file offset 0x4): this is a single-image cart, not a multi-game pack.
The entry at 0x080000D4 is a normal crt0 (`add r5,pc,#0x3C` … `swi 0x110000`);
the 0xC0–0xD3 area holds a build banner (`$ETROID_4`), not a cracktro. No
SUNHORS/Mode7/CRC-BANDIT/trainer strings and no GameShark/CodeBreaker strings
are present. The image is not compressed with the GBA BIOS LZ77 header
convention at the usual alignment; the NES payload was recovered from the
running emulator instead (see §4).

## 2. Executive summary

This is a real emulated NES Metroid inside the Classic NES Series wrapper, and
the NES password system is fully present and reachable. The 6502 image is staged
by the wrapper at GBA EWRAM `0x02000000` (128 KiB, 8 × 16 KiB MMC1 banks); NES
internal RAM is at IWRAM `0x03007200` and NES cartridge WRAM ($6000–$7FFF) is at
EWRAM `0x02030000`.

The password screen is NES state `$1F=0x18`, handler `$9147`. It shows a 5×13
grid of 65 cells. Cells 0–63 are the six-bit alphabet
`0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz?-` in order;
cell 64 (row 4, col 12) is the blank/space value 0xFF. `A` places the selected
symbol and advances the 24-cell buffer at `$699A`, `B` moves the cell cursor
back, arrows move the grid cursor, and `Start` submits.

Submission runs the decoder at `$8F60` (24 × 6 bits → 18 bytes) and the
validator at `$8DDE`. A password is accepted when

```
chk == ( sum(rotl128(data, shift)) + shift ) & 0xFF
```

where `data` is bytes 0–15, `shift` is byte 16 and `chk` byte 17. The only other
acceptance path is a hard-coded developer/debug check: the first 16 characters
equal `NARPASSWORD00000` (tile-code table `$8E07`) sets `$69B2=1` and skips the
checksum. That is the famous NARPAS SWORD debug mode; it was verified on-screen.

The published list was reproduced exactly: JUSTIN BAILEY, 999999/KKKKKK,
XXXXXX/KKKKKK, BBBBBB/AAAAAA, mMuiS1…, Ktj-…, M7-…, gunpei yokoi?, CONTINUE MY
GAMEMINIBOSS, some-1…, and the lowercase “justin bailey” all pass the ROM’s own
validator. The area field recovered from the loader also explains the published
notes: `ENGAGE RIDLEY MOTHER FUCKER` decodes to area 11, `333333…KKKKKK` to area
6, and lowercase `justin bailey` to area 14 — all checksum-valid but outside the
handled area range.

A new code was minted from the recovered format and entered through the real
on-screen grid:

```
flEEfBbb9AdIV--------m01
```

It is JUSTIN BAILEY’s 128-bit item payload with the start-area field changed
from 1 (Norfair) to 2 (Kraid’s Lair), shift 0, checksum 0x01. The game accepted
it and loaded the state (`$1E=8`, `$1D=0`, `$74=0x12`, `$69B3=1`, 58-entry item
list identical to JUSTIN BAILEY). Nothing in the published lists uses this
combination. The same code with the checksum character changed to `2`
(`…m02`) was entered on-screen and rejected: the game stayed on the password
screen with no state loaded and selected the “ERROR TRY AGAIN” string.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL, `Xvfb :252`, `DISPLAY=:252`, `SDL_AUDIODRIVER=dummy`,
3× scale. Keyboard: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, d-pad = arrow keys. Keys were held 100–200 ms.

Path to the password screen (all RAM values are from the NES address map):

1. Boot. Title screen: `$1F=0x04`. Press Start.
2. START/CONTINUE menu: `$1F=0x16`, selection byte `$0325`.
3. Press Select. `$0325` toggles 0→1 (CONTINUE).
4. Press Start. `$1F` becomes 0x18; the 24-cell password grid is up
   (`$0320`=cell index, `$0321`=row 0–4, `$0322`=column 0–12).

Typing: for each of the 24 codes, move the grid cursor to
`row = code/13, col = code%13` with arrows, press A. The buffer is written to
NES cart WRAM `$699A–$69B1` (GBA `0x0203099A`). Start submits.

Pause menu: start a new game (title → Start → START/CONTINUE with selection 0
→ Start). Normal gameplay is `$1E=3`; pressing Start switches to `$1E=5`, the
status/pause screen, and Start again returns to `$1E=3`. The frame counter `$2D`
keeps advancing on both, so this is a game screen, not a wrapper freeze.

Read RAM without a debugger: mGBA savestates (`Shift+F1`) are PNGs whose `gbAs`
chunk is zlib-compressed. For this 1 MiB ROM the 397,312-byte state has VRAM at
0x1000, IWRAM at 0x19000 and EWRAM at 0x21000. Therefore:

* NES internal RAM `$0000–$07FF` = state `0x20200–0x209FF`
* NES cart WRAM `$6000–$7FFF` = state `0x51000 + (addr-$6000)` = EWRAM `0x02030000 + (addr-$6000)`

Codes tested through the real screen: JUSTIN BAILEY, the novel code, its
one-character checksum mutant, and the NARPAS debug string.

## 4. Address map

### GBA / wrapper

| Address | Contents |
|---|---|
| `0x02000000–0x0201FFFF` | NES PRG, 128 KiB, 8 × 16 KiB banks (MMC1) |
| `0x02030000–0x02031FFF` | NES cartridge WRAM ($6000–$7FFF) — verified at `$6886`, `$699A`, `$69B2` |
| `0x03007200–0x030079FF` | NES internal 2 KiB RAM ($0000–$07FF, mirrored to $1FFF) |
| `0x03005000`-ish … | (not needed; wrapper code/data) |
| `0x080000D4` | ARM crt0 (normal, no trainer) |

The NES image is not stored contiguously in plain form in the 1 MiB GBA file
(entropy ≈ 8.0 above 0x20000; a 0x50-byte literal-with-0xFF-escapes fragment
exists at file 0x2D91). Runtime staging into EWRAM is the reliable extraction
route.

### NES 6502 (bank 0 mapped at $8000; fixed bank at $C000 = PRG file 0x1C000)

| NES address | PRG file offset | Function |
|---|---|---|
| `$8000` | `0x0000` | in-game state dispatcher (`$1F` jump table at `$802A`) |
| `$8C5E` | `0x0C5E` | submit entry: decode → validate → start |
| `$8F60` | `0x0F60` | 24 chars → 18 bytes (6-bit packer) |
| `$8FF1/$9001/$9011` | `0x0FF1/0x1001/0x1011` | group-of-four 6-bit pack helpers |
| `$8DDE` | `0x0DDE` | validator (debug check, rotate, checksum) |
| `$8E4E` | `0x0E4E` | rotate-left 128-bit payload by `shift` |
| `$8E21` | `0x0E21` | sum 17 bytes (16 data + shift) |
| `$8E07` | `0x0E07` | `NARPASSWORD00000` tile-code table |
| `$9147` | `0x1147` | password-screen handler (grid, A/B/Start) |
| `$919B–$91F8` | `0x119B–0x11F8` | grid cursor / A placement of symbol |
| `$923F–$92B3` | `0x123F–0x12B3` | arrow navigation of 5×13 grid |
| `$9998` | `0x1998` | grid row pointer table (5 × 13 bytes, then 0xFF) |
| `$9450` | (bank 0) | draw one symbol at the grid cursor |
| `$8D12/$8D3D` | `0x0D12/0x0D3D` | load decoded payload into game state |
| `$8BD4` | `0x0BD4` | expand 128-bit item bitmap into item list `$6886` |
| `$8C39` | `0x0C39` | item-table lookup for one set bit |
| `$9029` | `0x1029` | 60-entry item-pointer table (bit index → 2-byte ID) |
| `$8C7A/$8E6C` | `0x0C7A/0x0E6C` | encoder (game state → password) |
| `$92D4` | `0x12D4` | game-start initialiser after acceptance |
| `$8759` / `$8768` | `0x0759/0x0768` | “ERROR TRY AGAIN” / blank message |

### NES RAM used as evidence

| Address | Meaning |
|---|---|
| `$1D` | in-game flag (1 = game bank dispatch active) |
| `$1E` | game phase: 3 gameplay, 5 pause/status, 8 start transition; password/debug accept passes through 8 |
| `$1F` | screen/game-state index (4 title, 0x16 START/CONTINUE, 0x18 password grid) |
| `$2C` | screen message selector (non-zero selects “ERROR TRY AGAIN”) |
| `$2D` | frame counter (used to prove System Menu freeze) |
| `$0320/$0321/$0322` | password cell index / grid row / grid column |
| `$0325` | START/CONTINUE selection |
| `$0684` | password-error flag (set by the derived invalid path) |
| `$6878/$6879` | start map coordinates from payload bytes 9/10 |
| `$687B/$687C` | boss/flag bits from payload byte 15 |
| `$6886` | count of item-list entries; list at `$6887…` |
| `$699A–$69B1` | 24 password character codes |
| `$6988–$6997` | 16-byte decoded payload (after rotate) |
| `$6998` | shift byte |
| `$6999` | checksum byte |
| `$69B2` | debug (NARPAS) flag |
| `$69B3` | suitless flag (payload byte 8 bit 7) |
| `$74` | area/map field (`payload[8] & 0x3F`; low nibble is used) |

## 5. Algorithm

### 5.1 Character alphabet and packing

64 symbols per cell, six bits each, in this order:

```
index: 0 1 2 3 4 5 6 7 8 9 ... 35 36 ... 61 62 63
char : 0 1 2 3 4 5 6 7 8 9 ...  Z  a ...  z  ?  -
```

Cell 64 of the on-screen grid is the blank/space (value 0xFF), not part of the
six-bit alphabet; it injects an 8-bit value into the packer (it can alter the
preceding byte’s low bits, as documented by the format guide). All accepted
published codes use the 64-symbol alphabet plus, in some cases, real spaces
(0xFF).

Packing, exactly as `$8F60` does it (four chars → three bytes):

```
for i in 0..5:
  c0,c1,c2,c3 = c[4i],c[4i+1],c[4i+2],c[4i+3]
  b[3i+0] = (c0<<2 | c1>>4) & 0xFF
  b[3i+1] = ((c1 & 0x0F)<<4 | c2>>2) & 0xFF
  b[3i+2] = ((c2 & 0x03)<<6 | c3) & 0xFF
```

The three helpers are `$8FF1` (char<<2 | next>>4), `$9001`
((char&0xF)<<4 | next>>2) and `$9011` (three RORs, `AND #$C0`, OR next).
The `$9001` helper shifts four times, not five; using five was the one wrong
guess that had to be corrected against the ROM (it turned 0xC7 into 0xE7).

### 5.2 Validation

```
decode(c[24]) -> b[18]                 # §5.1
data = b[0..15]; shift = b[16]; chk = b[17]

if c[0..15] == codes("NARPASSWORD00000"):
    $69B2 = 1; return ACCEPT           # debug path, checksum ignored

# $8E4E: rotate the 128-bit array in place, left, `shift` times
# bit 7 of $6988 wraps to bit 0 of $6997; bits 7 of $6997..$6989
# shift into bit 0 of the next lower byte.
data = rotl_rom(data, shift)

if ((sum(data) + shift) & 0xFF) == chk: return ACCEPT
else: return REJECT                    # screen shows "ERROR TRY AGAIN"
```

`$8E4E` is a rotate, not a plain shift: `$00` saves byte 15, the 16 bytes are
`ROL`ed from byte 15 down to byte 0, then `$00` is `ROL`ed with the carry out of
byte 0 and stored back to byte 15. Byte order is $6988 = byte 0.

### 5.3 Encoding (inverse, used to mint codes)

Pick `shift` (0 is legal and simplest). Store `data` such that the validator’s
left rotation recovers the desired payload. With `shift=0`:

```
checksum = sum(payload[0..15]) & 0xFF
bytes18  = payload[0..15] || 0x00 || checksum
pack each three bytes into four chars (inverse of §5.1)
```

With a non-zero shift the stored 16 bytes must be the right-rotation of the
desired payload by the same amount; the 4096-string enumeration in §6b shows
the 16 different shift encodings of one 16-byte prefix, exactly one per shift
value.

### 5.4 Effect of the decoded payload

`$8D12` uses payload byte 8: bit 7 → `$69B3` (suitless), bits 0–5 → `$74`
(area/map). Bytes 9,10 → `$6878/$6879` (start coordinates). Bytes 11–14 →
`$687D–$6880`. Byte 15 bits 7/6/5/4 → `$687B` bit7/bit0 and `$687C` bit7/bit2.
Bytes 0–7 (plus bits 60–63) are a 128-bit item bitmap; `$8BD4` scans the first
60 bits and appends a 16-bit item-list entry per set bit using the pointer table
at `$9029` (60 entries). `$8D3D` derives the energy-tank count from
`$687B/$687C`.

## 6. Tables

### 6.1 Password grid (`$9998`, PRG file 0x1998)

Five row pointers, each 13 bytes:

```
row0: 00 01 02 03 04 05 06 07 08 09 0A 0B 0C
row1: 0D 0E 0F 10 11 12 13 14 15 16 17 18 19
row2: 1A 1B 1C 1D 1E 1F 20 21 22 23 24 25 26
row3: 27 28 29 2A 2B 2C 2D 2E 2F 30 31 32 33
row4: 34 35 36 37 38 39 3A 3B 3C 3D 3E 3F FF
```

So the grid is simply alphabet index = `row*13 + col`; the 65th cell is 0xFF.
The on-screen glyph of index N is the game font tile N
(`0–9`, `A–Z`, `a–z`, `?`, `-`).

### 6.2 Debug password table (`$8E07`)

```
17 0A 1B 19 0A 1C 1C 20 18 1B 0D 00 00 00 00 00
 N  A  R  P  A  S  S  W  O  R  D  0  0  0  0  0
```

The comparison is over 16 characters; the last eight cells are free. This is
the NARPASSWORD00000 debug password (NARPAS SWORD0 … in the published spelling).

### 6.3 Item pointer table (`$9029`)

60 two-byte entries, one per item bit. First entries:
`4E10 4B26 E528 8228 2723 252B 2503 692A 0327 6323 E229 E215 2E21 4E26 2F26 4C2B …`
Full names of all 60 items were not assigned (see §8); the bits themselves are
directly observable in the 128-bit payload and in the item-list count.

### 6.4 Field summary

| Field | Bits/bytes | Effect |
|---|---|---|
| item bitmap | payload[0..7] + bits 60–63 | item list `$6886/$6887…` |
| area | payload[8] bits 0–5 → `$74` | map/start area; low nibble used |
| suitless | payload[8] bit 7 | `$69B3` |
| coordinates | payload[9], payload[10] | `$6878`, `$6879` |
| aux | payload[11..14] | `$687D–$6880` |
| flags | payload[15] bits 7/6/5/4 | `$687B/$687C` (boss/flag bits) |
| shift | byte 16 | rotation count for validation |
| checksum | byte 17 | `sum(rotl(data,shift))+shift mod 256` |

### 6.5 Published codes checked against the ROM

All were run through the ROM’s own `$8F60/$8DDE` code (py65) and the result
compared with the published label. “Area” is `payload[8] & 0x0F`.

| Published | Normalised 24 chars | Result | Area |
|---|---|---|---|
| JUSTIN BAILEY ------ ------ | `JUSTINBAILEY------------` | accepted | 1 (Norfair) |
| 000000 000020 000000 000020 | `000000000020000000000020` | accepted | 0 (Brinstar) |
| 999999 999999 KKKKKK KKKKKK | `999999999999KKKKKKKKKKKK` | accepted | 2 (Kraid) |
| XXXXXX XXXXXX KKKKKK KKKKKK | `XXXXXXXXXXXXKKKKKKKKKKKK` | accepted | 3 (Tourian) |
| BBBBBB BBBBBB BBBBBB AAAAAA | `BBBBBBBBBBBBBBBBBBAAAAAA` | accepted | 2 |
| mMuiS1 II6-GE Jls?h0 m00WRM | `mMuiS1II6-GEJls?h0m00WRM` | accepted | 3 (Tourian) |
| Ktj-tPPj-mS3--y00000y00a | `Ktj-tPPj-mS3--y00000y00a` | accepted | 3 (Tourian) |
| M7-t-- ---u?0 2T--t0 E000bI | `M7-t-----u?02T--t0E000bI` | accepted (OCR variant) | 3 |
| gunpei yokoi? X11111 XXXXXX | `gunpeiyokoi?X11111XXXXXX` | accepted | 1 (Norfair) |
| CONTIN UE_MY_ GAMEMI NIBOSS | `CONTINUE MY GAMEMINIBOSS` (spaces) | accepted | 0 (Brinstar) |
| some-1 set-up us-the B0MB11 | `some-1set-upus-theB0MB11` | accepted | 0 |
| 333333 333333 KKKKKK KKKKKK | `333333333333KKKKKKKKKKKK` | accepted (checksum only) | 6 — out of range |
| ENGAGE RIDLEY MOTHER FUCKER | `ENGAGERIDLEYMOTHERFUCKER` | accepted (checksum only) | 11 — out of range |
| justin bailey ------ ------ | `justinbailey------------` | accepted (checksum only) | 14 — out of range |
| NARPAS SWORD0 000000 000000 | `NARPASSWORD0000000000000` | debug accept (`$69B2=1`) | n/a |

The three out-of-range codes are exactly the ones the published notes describe
as “returns to title”/“glitchy”: the validator has no semantic range layer,
only the checksum and the NARPAS special case.

## 6b. Enumeration

**Space definition.** Per cell the canonical alphabet is 64 symbols
(6 bits, §6.1), so the canonical 24-cell space is

```
64^24 = 2^144 = 22,300,745,198,530,623,141,535,718,272,648,361,505,980,416
```

The on-screen grid additionally exposes one blank cell (0xFF) per position, so
the literal UI string space is `65^24`; the blank value is not a 6-bit symbol and
injects an 8-bit value into the packer, so the 64-symbol space above is the
bijective, enumerable one. Length is fixed: 24 cells, 144 bits, 18 bytes; there
is no shorter or longer valid input path (the validator reads exactly 18 bytes).

**Checksum-accepted set.** For any fixed 136 bits (16 data bytes + shift), the
comparison against byte 17 accepts exactly one of the 256 possible byte-17
values. Byte 17 is fully reachable: `((c22&3)<<6)|c23` spans 0–255. Therefore

```
accepted by checksum = 2^136 = 87,112,285,931,760,246,646,623,899,502,532,662,132,736
i.e. 1/256 of the 64-symbol space
```

**Debug set.** The first 16 cells fixed to `NARPASSWORD00000` (96 bits) plus any
eight cells: `64^8 = 281,474,976,710,656` strings accepted regardless of the
checksum (with the 65-symbol UI, `65^8 = 318,644,812,890,625`). The overlap with
the checksum set is `2^40 = 1,099,511,627,776` strings (16 shift encodings per
fixed 36-bit tail). Distinct accepted canonical strings:

```
2^136 + 2^48 - 2^40 = 87,112,285,931,760,246,646,623,899,782,908,127,215,616
```

**Exact slice enumeration (ROM code as oracle).** With the 22-character prefix
`flEEfBbb9AdIV--------m` fixed, all 64 × 64 = 4096 completions of the last two
cells were run through the ROM’s actual `$8F60/$8DDE` code:

```
4096 tested, 16 accepted, 0 disagreements with the reimplementation
accepted set = one completion per shift value 0..15 (1/256 exactly)
```

The 16 accepted strings are all valid spellings of the prefix payload with
different shift encodings, e.g.

```
flEEfBbb9AdIV--------m01   (shift 0)
flEEfBbb9AdIV--------m4G
flEEfBbb9AdIV--------m8g
flEEfBbb9AdIV--------mDX
flEEfBbb9AdIV--------mJA
flEEfBbb9AdIV--------mMR
...
```

**Additional enumerations.**

* One-cell sweep: fixed 23-character prefix, all 64 values of the last cell →
  exactly 1 accepted (`…m01`'s `1`).
* Random sweep: 1500 uniformly random 24-character strings → 3 accepted
  (0.2 %, consistent with 1/256), 0 disagreements with the reimplementation.
* Debug sweep: `NARPASSWORD00000` + 40 random 8-character tails → 40/40
  accepted, `$69B2=1` in every case.
* Published-list sweep: §6.5 (all published codes decode to their advertised
  area or to the documented out-of-range behaviour).

**Novel code (entered on the real screen).**

```
flEEfBbb9AdIV--------m01
```

Decoded payload `a6 f3 8e a4 b9 65 24 a9 d2 7f ff ff ff ff ff ff`,
shift 0, checksum 0x01. It is JUSTIN BAILEY’s item payload with the start-area
nibble changed 1 → 2 (Norfair → Kraid’s Lair). No fetched published list
contains it (searches included StrategyWiki, Metroid Fandom, Metroid Database,
GameFAQs’ password-format guide, retrogameindex and archived cheat pages).

Observed state after starting from this code:

```
$1D=0x00  $1E=0x08  $1F=0x18
$74=0x12  $69B3=0x01  $69B2=0x00
$6878=0x7F $6879=0xFF
$6886=58 (item-list entries, identical to JUSTIN BAILEY)
```

**Bounds proven by rejection.**

```
flEEfBbb9AdIV--------m02   (same payload, checksum character 1 -> 2)
```

The ROM validator returns carry=1 (reject). Entered on-screen through the same
24-cell grid, the game did **not** start:

```
$1D=0x01  $1E=0x00  $1F=0x18
$74=0xDA  $69B2=0x00
$6886=0 (empty item list)
$2C != 0  -> $9147 selects the $8759 string "ERROR TRY AGAIN"
```

By contrast the one-character-different valid code produced
`$1D=0, $1E=8, $74=0x12, $6886=58`. This is the checksum layer’s bound. The
semantic layer is deliberately absent: area values 6, 11 and 14 are accepted by
the checksum and only fail later in the game (published codes confirm title
return/glitches); the ROM’s `$8D12` masks the area but never range-checks it.

**Space size statement.** Canonical: 2^144 strings, 2^136 checksum-accepted,
2^48 debug-accepted, overlap 2^40. The password system has no table of accepted
strings: it is a pure checksum over a 128-bit payload plus the one hard-coded
debug prefix.

## 7. Validation evidence

**Observed (emulator RAM, no screenshots).**

* Password grid is live: selecting cell (row 1, col 6) = code 0x13 and pressing
  A wrote `0x13` into the 24-cell buffer at `$699A` (GBA `0x0203099A`); `$0320`
  advanced. This ties the NES addresses to the GBA memory map.
* JUSTIN BAILEY accepted from the real grid: `$1D=0, $1E=8, $74=0x11,
  $69B3=1, $6886=58`.
* Novel code `flEEfBbb9AdIV--------m01` accepted: `$74=0x12` (area 2),
  `$69B3=1`, `$6886=58`, `$1D=0, $1E=8`; same item list as JUSTIN BAILEY.
* Mutant `…m02` rejected: `$1D=1, $1E=0, $74=0xDA, $6886=0`, `$2C != 0`
  (ERROR TRY AGAIN branch). The 4096-slice and 1500-random offline runs show
  the same accept/reject boundary.
* NARPAS debug accepted from the real grid: `$69B2=1`, `$1D=0, $1E=8`.
* Pause menu reached in a new game: gameplay `$1E=3` → Start → `$1E=5`
  (status/pause screen) → Start → `$1E=3`. `$2D` advances throughout.
* Wrapper System Menu: holding L+R froze NES execution (frame counter `$2D`
  stayed 0x83 over 2 s) and changed the GBA VRAM (1072 bytes); B closed it and
  `$2D` resumed (0xDE → 0x69). L alone and R alone did not freeze the NES.
* Wrapper reset: Start+Select+A+B reset the NES (ZP re-initialised, `$1F` went
  from 0x18 to 0x03, `$2D=0xD1`).

**Derived (disassembly + ROM execution).**

* Packer, rotate, checksum and debug table are exact; the Python model agrees
  with the ROM’s own validator on all 4096 slice strings and 1500 random
  strings (0 mismatches).
* Area numbering 0 Brinstar / 1 Norfair / 2 Kraid / 3 Tourian is derived from
  the published codes’ decoded payloads and the loader (`$8D12`).
* The out-of-range published codes (areas 6/11/14) confirm there is no semantic
  range check in the validator.

**Inferred.**

* Individual item-bit names for all 60 bits (the pointer table is dumped, but
  each pointer was not traced to an item name).
* Exact wrapper System Menu UI text/options (verified by execution freeze and
  VRAM change; the menu text was not decoded).
* Exact GBA-side compression/patch format of the embedded NES image.

## 8. Unknowns

* The 60-entry item-pointer table at `$9029` is dumped, but only the aggregate
  effect (item-list count and the JUSTIN BAILEY set) is named; a per-bit item
  name map would require tracing each pointer into the item-pickup code.
* The wrapper’s System Menu state variable was not located; the menu was
  verified behaviourally (NES frozen, VRAM changed, B resumes).
* The GBA image stores the NES payload in a transformed form (partial literal
  match at 0x2D91); the exact container is not named.
* The exact failure store that produces `$2C != 0` on a checksum rejection was
  not isolated to a single instruction (the observed `$0684` value did not match
  the `$8C69` path in every trial). The accept/reject boundary itself is proven
  both in-ROM and in-game.

## 9. Tooling

* mGBA 0.10.5 SDL under Xvfb :252 / openbox; xdotool for input; no screenshots
  used (RAM/savestate evidence only).
* Python 3.13 + `py65` (6502 MPU) as the ROM-code oracle; Capstone 5.0.7 and
  `arm-none-eabi-objdump` for ARM/Thumb checks.
* Custom scripts in `/tmp/opencode/cnesmetroid/`:
  `ss.py` (gbAs PNG/zlib state extractor), `readram.py`, `oracle.py`
  (loads the extracted PRG into py65 and calls `$8F60`/`$8DDE`),
  `gen.py` (pack/rotate/encode/decode), `metpwd.py`, `type_pwd.py`
  (grid navigation + real key injection), `drive.py`, `enum2.py`, `enum3.py`,
  `enum4.py` (enumerations), `ewram.bin` (extracted 128 KiB NES PRG).
* Key extraction step: savestate at the password screen, `gbAs` chunk
  zlib-decompressed; EWRAM at state 0x21000 holds the staged NES PRG at
  GBA 0x02000000 and cart WRAM at 0x02030000.

## Legal note

No ROM, extracted graphics, music or copyrighted text is redistributed here.
Only hashes, addresses, the algorithm, and codes generated by this analysis are
published.
