# Ace Combat Advance (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-25.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ace Combat Advance/Ace Combat Advance.gba` |
| Size | 4 MiB (`0x400000`) |
| Header title | `ACE COMBAT` |
| Game code | `BAEE` |
| Maker code | `AF` |
| Main unit / device | `0x00` / `0x00` |
| Software version | `0` (Rev.00) |
| Entry branch | `0xEA00002E` → `0x080000C0` |
| Fixed `0xB2` | `0x96` |
| MD5 | `4e46dd3ae5c9c70c49587d093517049a` |
| SHA-1 | `856a08e8f60f817b96add5bf2f6db186bea832ef` |
| SHA-256 | `1b30008304ed8cd4434c685075d954f2a95f7aab6165540fb62e2ac35da08e6e` |

Embedded GBA-header scan: the 156-byte Nintendo logo from `0x004` was searched
across the whole file. It occurs **once**, at file offset `0x0`, so this is a
single 4 MiB image, not a multi-game pack. The ROM has no battery-save file
(`.sav` is created as 0 bytes); progress is carried by the code itself.

All addresses below are `0x08000000 + file_offset`. Findings are tied to the
SHA-256 above.

---

## 2. Executive summary

Ace Combat Advance has a **progress-password system**, reached from
`Main Menu → Enter Code`. The prior lead was correct that there is no literal
code table: the four published strings are absent from the ROM, and the game
contains a paired **encoder** and **decoder** instead.

The important correction is that the codes are **not protected by an arithmetic
checksum**. Each of the eight characters is one of 32 alphabet symbols (a 5-bit
value). The low 5 bits are bit-reversed by the ROM into a "destination byte"
whose fixed marker bits identify which field that character carries. The
validator at `0x08003340` checks only those marker bits. Once they pass, the
decoder at `0x08003480` unpacks the character back into the progress struct and
the game accepts it.

The payload is exactly 33 bits:

| Field | Bits | Meaning |
|---|---:|---|
| `A` | 12 | score ÷ 50 |
| `B` | 12 | per-mission "S rank achieved" flags (bit *i* = Mission *i*+1) |
| `c` | 4 | constant `0xC` in New Game and every published code; purpose not identified |
| `d` | 4 | missions reached (0–12; `4` = "Go to Level 5", `12` = all levels) |
| `f` | 1 | 0 in New Game and every published code; purpose not identified |

A second, derived 10-bit word at `state+0x0E` is the **aircraft-unlock
bitmask**, computed from `d` and the number of S ranks. This is what makes the
published "all levels and planes" code work.

Consequences:

* The full input space is `32^8 = 1,099,511,627,776`.
* The valid set is `2^33 = 8,589,934,592` (1 in 128 strings).
* Any valid code can be minted offline for an arbitrary score, arbitrary subset
  of mission S ranks, arbitrary mission progress and a derived aircraft set.
* Published list: three codes are valid as written. The fourth, `ZF9W9FN`, is
  only seven characters and cannot be entered; the natural eight-character
  completion `ZF9W9FN9` is accepted and produces the advertised
  all-missions/all-S state.
* Novel code `GFDJZFJL` (not in any published list) was minted, accepted by the
  emulator, and produced Mission #5 "S" only (with score 5000 and 7 aircraft)
  while Mission #6 remained without an S rating.

---

## 3. How to reproduce

### Emulator and keymap

```bash
sudo apt-get install -y mgba-sdl xvfb openbox xdotool scrot imagemagick gdb-multiarch
Xvfb :121 -screen 0 1024x768x24 &
DISPLAY=:121 openbox &
DISPLAY=:121 SDL_AUDIODRIVER=dummy mgba -3 "Ace Combat Advance.gba" &
```

Default mGBA keymap used: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. Hold keys 100–150 ms; the grid needs discrete presses.
The title screen needs about 5 s after the Namco logo.

### Menu path (observed)

```
Title → PRESS START (Return)
└─ MAIN MENU (Campaign tab)
   └─ ENTER CODE (Down from NEW GAME, A)
      └─ 8×4 symbol grid; the code is submitted automatically on the 8th pick
```

After a valid code the screen shows `CODE ACCEPTED` for a few seconds, applies
the state, and returns to the main menu with `CONTINUE GAME` selected.
`CONTINUE GAME` opens `SELECT MISSION`; the mission nodes and the
`( Already received an 'S' rating. )` line are the visible effect of `B`/`d`.
`RECORDS → HI SCORE` shows the score field, and the aircraft row in
`MISSION BRIEFING → AIRCRAFT SELECTION` shows the derived unlock bits.

### Entry-screen facts (observed)

* Grid is **8 columns × 4 rows**, read row-major:

  ```
  B C D F G H J K
  L M N P Q R S T
  V W X Y Z 0 - 1
  2 3 4 5 6 7 8 9
  ```

* The cursor starts on `B`. `A` selects the highlighted symbol into the next
  slot; `B` deletes the last symbol. The 8th selection triggers validation.
* Empty slots are eight underscore cells. A seven-symbol string stays on screen
  with the 8th slot blank and is **not** submitted; there is no separate
  ACCEPT key.

### Codes tested

| Code | Source | Result |
|---|---|---|
| `QF9B9F59` | GameFAQs / mirrors | accepted, all 12 missions S, score 26150, 10 aircraft |
| `GFDWGFDN` | GameFAQs / mirrors | accepted, 12 missions available, Mission #3 S, score 7200 |
| `GFD-GDNN` | GameFAQs / mirrors (`-` is a real symbol) | accepted, Missions #1–#5 only, Mission #3 S, score 5700 |
| `ZF9W9FN` | GameFAQs / mirrors | 7 chars: cannot be submitted |
| `ZF9W9FN9` | 8-char completion of the above | accepted, all 12 S, score 20100, 10 aircraft |
| `ZF9W9FNN` | alternative completion | accepted, Missions #3–#12 S, score 20100 |
| `GFDJZFJL` | **generated, novel** | accepted, Mission #5 S only, score 5000, 7 aircraft |
| `BFDJZFJL` | generated, marker violation | `WRONG CODE` |
| `GFDLGDNN` | generated, marker violation | `WRONG CODE` |

---

## 4. Address map

| Address | Kind | Description |
|---|---|---|
| `0x0807F150` | table | 32 × `u32` pointers to one-character strings; the alphabet in index order |
| `0x08021C74`–`0x08021CF0` | data | the 32 one-character ASCII strings, stored in reverse order (`9` at `0x08021C74`, `B` at `0x08021CF0`) |
| `0x081CEAE4` | data | text bank base (touched by the UI object at `+0x24`) |
| `0x081CEB45` | string | `Enter Code` |
| `0x081CEB51` | string | `Wrong Code` |
| `0x081CEB5D` | string | `Code Accepted` |
| `0x081CF4B1` | string | `Your current code: ` |
| `0x08006F80` | code | menu/screen state manager; jump table at `0x08006FE0` (23 entries) |
| `0x08007098` | code | Enter Code screen init branch: sets alphabet size `32`, length `8`, calls `0x08004C34` |
| `0x08004C34` | code | Enter Code screen construction: calls the generator, draws the 8-char current code and the 8×4 grid |
| `0x08004C98` | call | `bl 0x08003090` — generate current code into object `+0x462` |
| `0x08004CAA` | code | alphabet lookup: `buf[i]` → `0x0807F150[index*4]` → first ASCII byte |
| `0x08004D70` | code | blanks the input buffer: `obj[0x462+i] = 0x20` |
| `0x08008288`–`0x080082E2` | code | Enter Code per-frame handler: append symbol, `pos++`, `if pos==8` validate |
| `0x080082BE` | call | `bl 0x08003340` — structural validator |
| `0x080082C6` | code | valid path: `state=3`, `bl 0x08003480` |
| `0x080082DC` | code | invalid path: `state=4` → `WRONG CODE` |
| `0x08003090` | code | **encoder/generator**: progress struct → 8 symbols in object `+0x462` |
| `0x08003340` | code | **validator**: eight marker-bit tests; returns 1/0 |
| `0x08003480` | code | **decoder/apply**: unpacks symbols into progress struct, calls derived-flag updates |
| `0x080033A8` | code | `state+0x18 = min(popcount(B)/3, 3)` |
| `0x080033F4` | code | builds 10-bit aircraft-unlock mask at `state+0x0E` |
| `0x080006C8` | code | New Game reset of progress struct (sets `c=0xC` at `+0x10`) |
| `0x080076A8` | code | post-mission S-rank set: `B |= 1 << mission_index` |
| `0x080076CC` | code | post-mission `d = max(d, mission_index+1)` |
| `0x080076E4` | code | post-mission score accumulation into `+0x14` |
| `0x02000400` | RAM | UI screen object (`[0x03000000]` points here) |
| `0x02000862` | RAM | 8-byte code/input buffer = object `+0x462`; `0x20` = empty slot |
| `0x030014B0` | RAM | progress struct (see below) |

### Progress struct `0x030014B0`

| Offset | Size | Meaning |
|---|---:|---|
| `+0x0C` | `u16` | `B`: 12 mission S-rank flags |
| `+0x0E` | `u16` | derived 10-bit aircraft-unlock mask |
| `+0x10` | `u8` | `c` (0–15; New Game and all published codes use `0xC`) |
| `+0x14` | `u32` | score (multiple of 50; shown in `HI SCORE`) |
| `+0x18` | `u8` | derived `min(popcount(B)/3, 3)` |
| `+0x19` | `u8` | `d`: missions reached / highest mission index+1 |
| `+0x1A` | `u8` | decoder writes a copy of `d`; `0` at New Game; used as a threshold in the post-mission score update |
| `+0x1C` | 12×`u16` | per-mission best scores |
| `+0x3A` | `u8` | selected/current mission index (0-based) |
| `+0x3B` | `u8` | 0 in all tested states |
| `+0x3C` | `u8` | set to 1 by New Game reset |
| `+0x3E` | `u8` | `f`: 1-bit field carried by code symbol 2 |

`0x02000862` is reused: at screen entry it holds the generated "current code"
values (0–31), is displayed, and is then overwritten with `0x20` for input.

---

## 5. Algorithm

### 5.1 Alphabet

32 symbols, in index order (also the on-screen order):

```
index: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
char : B  C  D  F  G  H  J  K  L  M  N  P  Q  R  S  T

index:16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31
char : V  W  X  Y  Z  0  -  1  2  3  4  5  6  7  8  9
```

There is no `A`, `E`, `I`, `O`, `U` (no vowels), and no digit `1` outside
index 23. The on-screen keyboard and the ROM pointer table agree exactly.

### 5.2 Symbol layer

For each character value `k` (0–31):

```
d = reverse5(k)          # d = bit-reverse of the 5-bit value
```

`d` carries a 4-bit field plus fixed marker/position bits. The eight
destinations (before reversal) are:

| Symbol | Destination `d` from nibble `n` |
|---|---|
| 0 | `4 \| (n&3) \| ((n&0xC)<<1)` |
| 1 | `(c&1) \| (f<<1) \| ((c&0xE)<<1)` |
| 2 | `8 \| (n&7) \| ((n&8)<<1)` |
| 3 | `(n&1) \| ((n&0xE)<<1)` |
| 4 | `4 \| (n&3) \| ((n&0xC)<<1)` |
| 5 | `(n&1) \| ((n&0xE)<<1)` |
| 6 | `8 \| (n&7) \| ((n&8)<<1)` |
| 7 | `2 \| (n&1) \| ((n&0xE)<<1)` |

Field assignment: symbols 0, 3, 6 carry the high, middle and low nibbles of `A`;
symbols 2, 4, 7 carry the high, middle and low nibbles of `B`; symbol 1 carries
`c` plus the 1-bit `f`; symbol 5 carries `d`. The marker bits are exactly what
the validator tests.

### 5.2a Why the validator accepts 2^33 strings

Each destination byte carries four data bits plus one fixed marker bit, except
symbol 1, which carries the four `c` bits and the 1-bit `f` (no marker). The
fixed bit is `1` in symbols 0, 2, 4, 6 and 7, and `0` in symbols 3 and 5.
Because each symbol is a 5-bit value, each position has exactly 16 accepted
symbols except symbol 1, which accepts all 32. The product is
`16 × 32 × 16^6 = 2^33`.

### 5.3 Validator (0x08003340)

`r0` points at the 8-byte input buffer. The whole routine is:

```
if (s[0] & 0xE4) != 0x04: return 0
if (s[1] & 0xE0) != 0x00: return 0
if (s[2] & 0xE2) != 0x02: return 0
if (s[3] & 0xE8) != 0x00: return 0
if (s[4] & 0xE4) != 0x04: return 0
if (s[5] & 0xE8) != 0x00: return 0
if (s[6] & 0xE2) != 0x02: return 0
if (s[7] & 0xE8) != 0x08: return 0
return 1
```

There is **no arithmetic checksum, no XOR key, and no code table**. The 8-bit
marker pattern is the entire integrity check. Per position the number of
accepted symbols is `16, 32, 16, 16, 16, 16, 16, 16`, giving `32 * 16^7 = 2^33`
valid strings.

### 5.4 Decoder (0x08003480)

After reversing each symbol back to `d`, it extracts nibbles:

```
def nobble(t, d):
    if t == 'A': return (d & 3) | ((d >> 1) & 0xC)     # low two + high two
    if t == 'M': return (d & 1) | ((d >> 1) & 0xE)     # bit0 + bits1-3
    if t == 'B': return (d & 7) | ((d >> 1) & 8)       # low three + bit3
    if t == 'L': return (d & 1) | ((d >> 1) & 0xE)     # same as M
    if t == 'C': return (d & 1) | ((d >> 1) & 0xE)     # same as M

Ahi  = nobble('A', d0)     c = nobble('C', d1)     f = (d1 >> 1) & 1
Bhi  = nobble('B', d2)     Amid = nobble('M', d3)
Bmid = nobble('A', d4)     d = nobble('M', d5)
Alo  = nobble('B', d6)     Blo = nobble('L', d7)

A = (Ahi << 8)  | (Amid << 4)  | Alo
B = (Bhi << 8)  | (Bmid << 4)  | Blo

state[0x14] = A * 50
state[0x0C] = B
state[0x10] = c
state[0x19] = d
state[0x1A] = d
state[0x3E] = f
```

Then it calls the two derived-flag routines:

```
state[0x18] = min(popcount(B) / 3, 3)

state[0x0E] = 1
if d != 0:            state[0x0E] |= 0x002
if d > 1:             state[0x0E] |= 0x004
if d > 3:             state[0x0E] |= 0x008
if d > 5:             state[0x0E] |= 0x010
if d > 7:             state[0x0E] |= 0x020
if B != 0:            state[0x0E] |= 0x040
if state[0x18] != 0:  state[0x0E] |= 0x080
if state[0x18] > 1:   state[0x0E] |= 0x100
if state[0x18] > 2:   state[0x0E] |= 0x200
```

The low 10 bits of `state[0x0E]` are the aircraft-unlock bitmask. This is
confirmed by the aircraft row: `0x3FF` → 10 lit aircraft, `0x07F` → 7 lit,
`0x001` (New Game) → 1 lit.

### 5.5 Encoder (0x08003090)

The encoder is the exact inverse and is what fills `Your current code:`:

```
A = (score // 50) & 0xFFF
B = B & 0xFFF
Ahi, Amid, Alo = (A >> 8) & 0xF, (A >> 4) & 0xF, A & 0xF
Bhi, Bmid, Blo = (B >> 8) & 0xF, (B >> 4) & 0xF, B & 0xF

d0 = 4 | (Ahi & 3) | ((Ahi & 0xC) << 1)
d1 = (c & 1) | ((f & 1) << 1) | ((c & 0xE) << 1)
d2 = 8 | (Bhi & 7) | ((Bhi & 8) << 1)
d3 = (Amid & 1) | ((Amid & 0xE) << 1)
d4 = 4 | (Bmid & 3) | ((Bmid & 0xC) << 1)
d5 = (d & 1) | ((d & 0xE) << 1)
d6 = 8 | (Alo & 7) | ((Alo & 8) << 1)
d7 = 2 | (Blo & 1) | ((Blo & 0xE) << 1)

symbol[i] = reverse5(d[i])
code = alphabet[symbol[0]] + ... + alphabet[symbol[7]]
```

Note `score // 50`: the game only stores score in multiples of 50; entering a
code always restores `A*50`, so scores that are not multiples of 50 cannot be
represented.

### 5.6 Reference Python implementation

```python
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0-123456789"
IDX = {c: i for i, c in enumerate(ALPHA)}
TYPE = ['A', 'C', 'B', 'M', 'A', 'M', 'B', 'L']

def rev5(x):
    return sum(((x >> i) & 1) << (4 - i) for i in range(5))

def _dest(t, n, f=0):
    if t == 'A': return 4 | (n & 3) | ((n & 0xC) << 1)
    if t == 'M': return (n & 1) | ((n & 0xE) << 1)
    if t == 'B': return 8 | (n & 7) | ((n & 8) << 1)
    if t == 'L': return 2 | (n & 1) | ((n & 0xE) << 1)
    if t == 'C': return (n & 1) | ((f & 1) << 1) | ((n & 0xE) << 1)

def _undest(t, d):
    if t == 'A': return (d & 3) | ((d >> 1) & 0xC)
    if t == 'M': return (d & 1) | ((d >> 1) & 0xE)
    if t == 'B': return (d & 7) | ((d >> 1) & 8)
    if t in 'LC': return (d & 1) | ((d >> 1) & 0xE)

def encode(A, B, c=12, d=0, f=0):
    nib = [A >> 8, (A >> 4) & 0xF, A & 0xF,
           B >> 8, (B >> 4) & 0xF, B & 0xF]
    ns = [nib[0], c, nib[3], nib[1], nib[4], d, nib[2], nib[5]]
    return ''.join(ALPHA[rev5(_dest(t, n, f))] for t, n in zip(TYPE, ns))

def decode(code):
    s = [IDX[ch] for ch in code]
    if len(s) != 8: raise ValueError("8 symbols required")
    d = [rev5(x) for x in s]
    A = (_undest('A', d[0]) << 8) | (_undest('M', d[3]) << 4) | _undest('B', d[6])
    B = (_undest('B', d[2]) << 8) | (_undest('A', d[4]) << 4) | _undest('L', d[7])
    return dict(A=A, B=B, c=_undest('C', d[1]), d=_undest('M', d[5]),
                f=(d[1] >> 1) & 1, score=A * 50)

def markers_ok(code):
    s = [IDX[ch] for ch in code]
    return ((s[0] & 0xE4) == 0x04 and (s[1] & 0xE0) == 0x00 and
            (s[2] & 0xE2) == 0x02 and (s[3] & 0xE8) == 0x00 and
            (s[4] & 0xE4) == 0x04 and (s[5] & 0xE8) == 0x00 and
            (s[6] & 0xE2) == 0x02 and (s[7] & 0xE8) == 0x08)
```

This implementation was cross-checked against the ROM by emulating both
`0x08003090` and `0x08003480` with Unicorn on 300 random states and 300 random
8-symbol buffers: zero mismatches.

---

## 6. Tables

### 6.1 Published codes (GameFAQs archive, 2022-01-27; replicated by mirrors)

| Claim | Published | Decoded state | In-game result |
|---|---|---|---|
| All levels and planes with S rank on every mission | `QF9B9F59` | `A=523` (score 26150), `B=0xFFF`, `d=12`, `c=12`, `f=0` | accepted; all 12 missions S; 10 aircraft; HI SCORE 26150 |
| Get all levels | `GFDWGFDN` | `A=144` (7200), `B=0x004`, `d=12`, `c=12`, `f=0` | accepted; 12 missions available; only Mission #3 S |
| Go to Level 5 | `GFD-GDNN` | `A=114` (5700), `B=0x004`, `d=4`, `c=12`, `f=0` | accepted; Missions #1–#5 only; Mission #3 S |
| Unlock Everything | `ZF9W9FN` (7 chars) | — | not enterable (see §6.2) |
| Unlock Everything (reconstructed) | `ZF9W9FN9` | `A=402` (20100), `B=0xFFF`, `d=12`, `c=12`, `f=0` | accepted; all 12 missions S; 10 aircraft |

The `-` in `GFD-GDNN` is not punctuation: it is alphabet index 22, a real
symbol on the grid. All published codes are absent as literal byte strings in
the ROM, as expected for an algorithmic encoder; the corrected `ZF9W9FN9` and
the generated `GFDJZFJL` are likewise not in the ROM.

### 6.2 The seven-character `ZF9W9FN`

`ZF9W9FN` has only seven symbols. The entry screen accepts a code only when the
8th symbol is chosen (`0x080082B6`: `pos == 8`), so the published string cannot
be submitted as written; after seven picks the 8th slot remains blank (`0x20`).

The natural eight-character completion that keeps the seven published
characters and satisfies the advertised "Unlock Everything" state is
`ZF9W9FN9`:

| Candidate | Decoded state | Matches description? |
|---|---|---|
| `ZF9W9FN9` | `B=0xFFF` (all 12 S), `d=12`, score 20100 | yes — all missions S |
| `ZF9W9FNN` | `B=0xFF4` (Missions #3–#12 S), `d=12`, score 20100 | no — first two missions lack S |

Both 8-character candidates are structurally valid and accepted by the game;
`ZF9W9FN9` is the one that reproduces the published claim. This is a
transcription error in the public list (one trailing character lost), not a
different algorithm.

### 6.3 Published/new code field values

| Code | A | score | B | d | c | f | Source |
|---|---:|---:|---:|---:|---:|---:|---|
| `QF9B9F59` | 523 | 26150 | `0xFFF` | 12 | 12 | 0 | public |
| `GFDWGFDN` | 144 | 7200 | `0x004` | 12 | 12 | 0 | public |
| `GFD-GDNN` | 114 | 5700 | `0x004` | 4 | 12 | 0 | public |
| `ZF9W9FN9` | 402 | 20100 | `0xFFF` | 12 | 12 | 0 | public + 1 char |
| `GFDJZFJL` | 100 | 5000 | `0x010` | 12 | 12 | 0 | **novel** |
| `GFDBGBDL` | 0 | 0 | `0` | 0 | 12 | 0 | New Game default |
| `GFDBGFDL` | 0 | 0 | `0` | 12 | 12 | 0 | all missions, no S |
| `GF9B9FD9` | 0 | 0 | `0xFFF` | 12 | 12 | 0 | all missions S, score 0 |

`GFDBGBDL` was confirmed as the "Your current code" on a fresh New Game before
any code was entered; it is the encoder output for the New Game state.

---

## 6b. Enumeration

### Space and valid-set size

| Quantity | Value |
|---|---:|
| Alphabet size | 32 |
| Code length | 8 |
| Total strings | `32^8` = **1,099,511,627,776** |
| Valid strings (marker test) | `2^33` = **8,589,934,592** |
| Acceptance ratio | 1 / 128 |
| Payload bits | 12 (`A`) + 12 (`B`) + 4 (`c`) + 4 (`d`) + 1 (`f`) = **33** |
| Score values | 4096 (`A` 0–4095, score `A*50` 0–204750) |
| Mission-S masks | 4096 (`B` 0–4095) |
| `d` values | 16 representable; 0–12 meaningful, 13–15 saturate |
| `c`, `f` | 16 × 2; purposes not identified |

The valid set is exactly the 33-bit state tuple: for every `(A, B, c, d, f)`
there is one valid string, and every valid string maps back to one tuple. This
is a bijection, not a hash.

### Novel code minted and confirmed

**`GFDJZFJL`** — `A=100` (score 5000), `B=0x010` (Mission #5 S only),
`d=12` (all 12 missions), `c=12`, `f=0`.

* Not present in any published list; a web search for the literal string
  returns no results, and it is not one of the GameFAQs/VGChartz/TCRF/mirror
  codes.
* Entered in mGBA: `CODE ACCEPTED` observed; the game returned to the main menu.
* State read back from `0x030014B0`: `B=0x0010`, score `0x1388` (5000),
  `c=0x0C`, `d=12`, derived aircraft mask `0x007F`.
* `SELECT MISSION → MISSION #5` shows
  `( Already received an 'S' rating. )`; `MISSION #6` shows no such line.
* `RECORDS → HI SCORE` shows `Player 5000`.
* Re-entering the Enter Code screen displays `Your current code: GFDJZFJL`,
  proving the encoder round-trips the exact state.
* Aircraft row shows 7 lit aircraft (derived mask `0x7F`), versus 10 for
  `QF9B9F59` (`0x3FF`).

This exercises a combination the published list does not contain: a single
specific S rank (mission 5) with all missions already available and a
non-published score.

### Bounds: rejected inputs and saturation

| Input | Violation | Observed result |
|---|---|---|
| `BFDJZFJL` | symbol 0 = `B` (0x00); `0x00 & 0xE4 = 0 ≠ 4` (destination bit 2 clear) | `WRONG CODE`, input cleared, return to menu |
| `GFDLGDNN` | symbol 3 = `L` (0x08); `0x08 & 0xE8 = 8 ≠ 0` (destination bit 1 set) | `WRONG CODE`, input cleared, return to menu |
| `ZF9W9FN` (7 chars) | 8th slot remains `0x20`; the game never calls the validator until 8 symbols are picked | stays on the Enter Code screen with one blank slot; cannot be submitted |
| `d=15` (`GFDBG1DL`) | 4-bit field is representable; no range check exists in `0x08003340` | **accepted**: state `+0x19=0x0F`, `+0x1A=0x0F`, mask `0x3F`; `SELECT MISSION` still shows all 12 missions (saturated) |

The format has no separate "out-of-range field" rejection because the field
widths are exactly the marker-valid symbol sets; 0–15 is the complete
representable range for `c`/`d`, and 0–4095 for `A`/`B`. The only way to make an
unrepresentable value is to violate a marker bit, which is the rejection shown
above. `d=15` is accepted by the code path (the validator never reads `d`), and
`0x080076CC` clamps progress to the 12 real missions.

### Published list reproduction

| Public code | Reproduced by codec | In-game |
|---|---|---|
| `QF9B9F59` | yes | accepted |
| `GFDWGFDN` | yes | accepted |
| `GFD-GDNN` | yes | accepted |
| `ZF9W9FN` | no (7 chars, unrepresentable) | not enterable |
| `ZF9W9FN9` (completion) | yes | accepted |

The codec agrees with the ROM for all three enterable published codes, plus the
seven-character string's most plausible completion. The only public-list
discrepancy is the truncated `ZF9W9FN`; it is a typo/lost character, not an
algorithm mismatch.

---

## 7. Validation evidence

### Observed (emulator / memory)

* `Enter Code` screen, 8×4 alphabet grid, `Your current code:` line, `WRONG
  CODE` and `CODE ACCEPTED` messages.
* `QF9B9F59` → `SELECT MISSION` shows all 12 nodes lit; Mission #12
  `'FINALE'` shows `( Already received an 'S' rating. )`; `HI SCORE` shows
  26150; aircraft row shows 10 lit aircraft.
* `GFDWGFDN` → all 12 mission nodes lit, no S line on Mission #12.
* `GFD-GDNN` → only Missions #1–#5 lit; cursor starts on Mission #5; Mission #3
  shows the S line.
* `GFDJZFJL` → `CODE ACCEPTED`; state read back as `B=0x10`, score 5000,
  `d=12`, derived mask `0x7F`; Mission #5 S, Mission #6 no S; HI SCORE 5000;
  re-entered screen shows `Your current code: GFDJZFJL`.
* `BFDJZFJL` and `GFDLGDNN` → `WRONG CODE`.
* `GFDBG1DL` (`d=15`) → accepted; state read back `+0x19=0x0F`,
  `+0x1A=0x0F`, aircraft mask `0x3F`; `SELECT MISSION` shows all 12 missions
  (the field saturates rather than being rejected).
* Seven-symbol `ZF9W9FN` → 7 filled slots, 8th blank, no submission.
* GDB reads of `0x030014B0` after each code match the decoder output exactly.
  After `QF9B9F59`: `+0x0C=0x0FFF`, `+0x0E=0x03FF`, `+0x10=0x0C`,
  `+0x14=0x00006626` (26150), `+0x18=3`, `+0x19=0x0C`, `+0x1A=0x0C`.
* GDB read of `0x02000862` is the 8-byte code buffer; setting a hardware
  watchpoint on it hit at `0x080030B6` inside the generator, confirming the
  buffer identity.

### Derived (disassembly)

* Alphabet table and index order (`0x0807F150`).
* Generator `0x08003090`, validator `0x08003340`, decoder `0x08003480`.
* Marker masks and the 33-bit payload layout.
* Derived aircraft mask at `state+0x0E` (`0x080033F4`) and the
  `popcount(B)/3` term (`0x080033A8`).
* Post-mission updates: `B |= 1<<mission` at `0x080076A8`,
  `d = max(d, mission+1)` at `0x080076CC`,
  `score += ...` at `0x080076E4`.
* New Game reset sets `c=0x0C` at `0x080006E6`.

### Inferred

* `c=0x0C` and `f=0` are format/version-like constants. The validator's masks
  do not constrain `c` or `f` (symbol 1 is accepted for all 32 values), and no
  reader outside the codec was found in the inspected UI/gameplay paths. They
  are preserved exactly by the codec.
* `ZF9W9FN9` is the intended 8-character form of the public `ZF9W9FN` because
  it preserves all seven published characters and produces the advertised
  all-missions/all-S state. The exact lost character is inferred, not proven
  from a second independent source.

---

## 8. Unknowns

* Meaning of `c` (`state+0x10`) and `f` (`state+0x3E`). `c` is `0x0C` in New
  Game and every published code; `f` is 0 in all of them. Both are preserved
  through encode/decode. No menu or gameplay reader was identified; they may be
  format constants or reserved fields.
* Whether the game ever rejects a structurally valid code for a non-format
  reason. No such check was found: the only validator called on submit is
  `0x08003340`, and the decoder applies every field unconditionally.
* The exact per-mission score formula in `0x080076E4` (the `×10` scaling and the
  `state+0x38` current-mission score) was read but not fully exercised.
* `c`/`f` variations were not entered in the emulator; their behavior is
  inferred from the validator and the codec round-trip only. `d=15` **was**
  entered and is stored/accepted unchanged; it saturates the mission list.

---

## 9. Tooling

* `mgba-sdl` 0.10.5 under `Xvfb :121` + `openbox`; `xdotool` for input;
  `scrot` + ImageMagick for screenshots.
* `gdb-multiarch` connected to mGBA's stub (`mgba -g`, port 2345), driven
  through a persistent `tmux` session; EWRAM/IWRAM dumps and hardware
  watchpoint on `0x02000862`.
* Python 3 + `capstone` for Thumb scans, `unicorn` 2.1.4 for instruction-level
  emulation of `0x08003090` / `0x08003340` / `0x08003480` (used to verify the
  pure-Python codec against the ROM, 300 random encode + 300 random decode
  trials, zero mismatches).
* `codec.py` (the reference implementation in §5.6) plus a small `enter.py`
  driver that navigates the 8×4 grid.
* `emu.py` maps ROM/EWRAM/IWRAM/I-O into Unicorn and runs the three routines
  with a fake return address on the stack.
* Evidence screenshots captured during the session include the Enter Code
  screen, the S-rank mission line, the aircraft row, `HI SCORE`, `CODE
  ACCEPTED` and `WRONG CODE`; they are analysis artifacts, not ROM assets.

### Legal

No ROM, graphics, music, or game text is redistributed here. Addresses,
algorithm, hashes and the reference codec are original analysis output.

---

## 10. Summary of the answer

* The "Enter Code" screen is a real, developer-intended progress-password
  system.
* Alphabet: `BCDFGHJKLMNPQRSTVWXYZ0-123456789` (32 symbols; no vowels).
* Length: 8 symbols; 5 bits each; each symbol is bit-reversed into a
  position-tagged byte.
* Payload: 33 bits — 12-bit score/50, 12-bit S-rank mask, 4-bit `c`, 4-bit
  mission progress `d`, 1-bit `f`.
* Integrity: marker-bit tests only; no arithmetic checksum.
* Space: `32^8`; valid: `2^33` (1/128).
* Published list reproduced, except `ZF9W9FN` is a 7-character truncation; its
  accepted completion is `ZF9W9FN9`.
* Novel code `GFDJZFJL` was minted, accepted, and produced Mission #5 S only,
  score 5000, 7 aircraft; `BFDJZFJL` and `GFDLGDNN` were rejected with
  `WRONG CODE`.
