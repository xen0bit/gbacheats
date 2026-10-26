# 2-in-1 – Cartoon Network Block Party & Cartoon Network Speedway (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `2-in-1 - Cartoon Network - Block Party & Cartoon Network - Speedway.gba` |
| Size | 8 388 608 bytes (`0x800000`, 8 MiB) |
| MD5 | `0d750defe01da931beb8148a71be112e` |
| SHA-1 | `b0d9b18157f7e8ec139f04f9ae9508d00fa39313` |
| SHA-256 | `373e971fd47aa608616cc1e3eab725319fad2e832167a51d87308f391e87a328` |

The file is two complete 4 MiB GBA images concatenated. Scanning the whole file for the
156-byte Nintendo logo finds two headers (logo at header offset 4):

| Image | Header file offset | ROM base | Title | Game code | Maker | Version | Fixed 0x96 | Complement |
|---|---:|---:|---|---|---|---:|---:|---:|
| 0 | `0x000000` | `0x08000000` | `CNDOUBLEGAME` | `BW2E` | `5G` | 0 | `0x96` | `0x5F` |
| 1 | `0x400000` | `0x08400000` | (blank) | (blank) | `01` | 0 | `0x96` | `0xF0` |

Evidence that image 0 is a stub: its entry word at file `0x0` is `0xEA0FFFFE`
(`b 0x08400000`), i.e. the reset vector jumps straight into the second image. The second
image's entry (`0xEA00002E`) branches to `0x084000C0`.

The two halves are complete, unrelated games:

| Half | File range | Game | Engine/credits |
|---|---|---|---|
| 0 | `0x000000`–`0x3FFFFF` | **Cartoon Network Block Party** | One Man Band / Majesco; board strings at `0x26E59C`–`0x27454B` |
| 1 | `0x400000`–`0x7FFFFF` | **Cartoon Network Speedway** | DC Studios / Majesco; credits at `0x462A40`, track strings at `0x4E9A24` |

Address convention in this report: `ROM address = 0x08000000 + file offset`. A file offset
inside the second image (e.g. `0x4E9B34`) therefore becomes `0x084E9B34`.

The cart has **two independent password systems**, one per half. No save data was written
by either half during this session (the emulator's `.sav` stayed 0 bytes), and Block
Party's `RESUME GAME` goes straight to the password grid, so the passwords *are* the
save mechanism.

## 2. Executive summary

**Half 0 — Block Party (the system the prior recon pointed at).** The game has a
16-symbol, 80-bit *pause password* that is displayed in the pause menu and re-entered from
`MAIN MENU → RESUME GAME`. The entry screen is an 8×4 grid of 32 symbols
`BCDFGHJKLMNPQRSTVWXYZ0123456789^` (`^` is drawn as `?`). The whole format was recovered
from the generator (`0x08029DC4`) and the validator/decoder (`0x08029FD8`), reimplemented
in Python (`bppass.py`, section 9), and verified in mGBA:

* the pause menu of a fresh Tater Farm game produces `VJBDBBBBBC?BC?BC`;
* typing that code into the password screen restores exactly that game and the pause menu
  reproduces the same code (round trip);
* changing only the 2-bit **board field** produces codes that start boards which the
  `SELECT BOARD` menu still shows as locked:
  `ZJBDBBBBBC?BC?BC` → Extreme Cul-de-Sac, `3JBDBBBBBC?BC?BC` → Planet Johnnywood,
  `7JBDBBBBBC?BC?BC` → Katz's Creepy Castle (all three otherwise locked at boot);
* changing only the **position fields** changes the resumed game: entering
  `VJBDNBBZBC?BC?BC` (P1 position 10, P2 position 20) resumes Tater Farm and the pause
  menu then regenerates `VJBDNBBBC?BC?BC`, i.e. P1 = 10 (P2 comes back as 0; see §8).

**Half 1 — Speedway.** A second, unrelated password screen exists at
`MAIN MENU → Password`: 8 decimal digits in a wheel selector. Its encoding is fully
recovered from the validator at `0x08415E90` (called from `0x0841630A`):

* digit 1 is a **check digit**: `d1 = (d2+…+d8) mod 10`;
* the other seven digits are **permuted** (`[5,1,3,0,2,6,4]`, table `0x0300372F`) into a
  21-bit payload, most-significant first;
* the payload must be `< 2^21`; it contains the unlock counter, five award slots, two
  extra character bits and their companion flags.

The Python codec in section 9 reproduces **all 13 published codes byte-for-byte**
(e.g. `96981951` ⇄ payload `0x1E7D55`), and novel codes were generated and confirmed in
mGBA: `41330962` (payload `0x60000`: 11 characters, zero awards) and `36521748`
(payload `0x180000`: 7 characters, zero awards). Rejections are proven by a bad check
digit (`51330962`) and an out-of-range payload (`39999999`), both of which leave the
save block at `0x020009A4`/`0x02000A70` untouched.

## 3. How to reproduce

Emulator and display used (nothing else attached to the ROM):

```bash
Xvfb :101 -screen 0 1024x768x24 &
DISPLAY=:101 openbox &
cd "roms/2-in-1 - Cartoon Network - Block Party & Cartoon Network - Speedway"
DISPLAY=:101 SDL_AUDIODRIVER=dummy mgba -3 "2-in-1 - Cartoon Network - Block Party & Cartoon Network - Speedway.gba"
```

mGBA 0.10.5 SDL default keymap: **A = `x`, B = `z`, Start = `Return`, Select =
`BackSpace`, D-pad = arrows**. Hold keys ≈0.2 s; menus drop 10 ms taps.

The cart boots the multi-game shell (orange screen, two thumbnails). The **left**
thumbnail (Block Party) is selected by default; **Right** selects Speedway.

### 3.1 Block Party — display a password

1. `A` (shell) → Block Party loads.
2. `Start` at the title screen → `MAIN MENU`.
3. `A` on `NEW GAME` → `SELECT PLAYER` → `A` (accept Courage + CPU) → `MODE SELECT`
   → `A` (`QUICK PLAY`) → `SELECT BOARD` → `A` (`TATER FARM`) → intro `A`, `A`.
4. In game press `Start`: the pause menu shows `PASSWORD: <16 symbols>`.

Observed at that point: `PASSWORD: VJBDBBBBBC?BC?BC`.

### 3.2 Block Party — enter a password

1. Shell → Block Party → `Start` → `MAIN MENU`.
2. `Down`, `A` on `RESUME GAME` → `PASSWORD` grid.
3. Cursor starts on `B` (row 0, col 0). D-pad moves the cursor (8 columns × 4 rows,
   wrapping), `A` appends the selected symbol, `B` deletes the last symbol / exits at
   length 0. After the 16th symbol `A` the validator runs.
4. The grid rows are exactly the alphabet in order:

```
B C D F G H J K
L M N P Q R S T
V W X Y Z 0 1 2
3 4 5 6 7 8 9 ?
```

A ready-made typer is in section 9 (`enter.py`); it converts a code string into
D-pad/A presses.

### 3.3 Speedway — password screen

1. Shell: `Right`, `A` → Speedway boots (DC Studios logo, title).
2. `Start` → main menu with five icons. `Right` ×4 selects the green cube icon,
   which reads **`Password`**; `A` opens `PASSWORD / Enter Password`.
3. The field is 8 decimal digit wheels followed by `OK`. `Left`/`Right` move the
   caret, `Up`/`Down` increment/decrement the selected digit (the wheels animate,
   so wait ~1 s before reading a screenshot). `Right` past the last digit reaches
   `OK`, `A` submits.
4. On submit the game returns to the main menu silently whether the code is accepted or
   not; check the effect (`Single Player → Championship → Character Select`).

Entered `96981951`; Character Select then lists 11 characters (6 before).

## 4. Address map

### 4.1 Multi-game layout

| Item | File offset | ROM address |
|---|---:|---:|
| Image 0 header / Block Party | `0x000000` | `0x08000000` |
| Image 1 header / Speedway | `0x400000` | `0x08400000` |

### 4.2 Block Party password code and data

| Purpose | ROM address | Notes |
|---|---:|---|
| 32-symbol alphabet | `0x08278094` | `"BCDFGHJKLMNPQRSTVWXYZ0123456789^"`, NUL-terminated |
| `"PASSWORD: "` | `0x082780B8` | drawn by `0x0802A778` |
| Password **generator** (state → 80 bits → 16 symbols) | `0x08029DC4` | reads the live game struct, writes the bit buffer then the symbol buffer |
| Password **validator/decoder** (16 symbols → 80 bits → state) | `0x08029FD8` | returns 1 = accepted, 0 = rejected |
| Bit writer `(count, value)` MSB-first | `0x080298D4` | writes into `0x030012C0` |
| Append-one-symbol handler (A) | `0x08029934` | also calls the validator when length > 15 |
| Delete / exit handler (B) | `0x0802A4F4` | |
| Cursor up / down | `0x0802A544` / `0x0802A580` | rows 0–3, wraps |
| Cursor left / right | `0x0802A5BC` / `0x0802A5F8` | columns 0–7, wraps |
| Entry-screen handler table | `0x08029CE0` | `0x08029935, 0x0802A4F5, 0x0802A545, 0x0802A581, 0x0802A5BD, 0x0802A5F9` |
| Draw 16-symbol string + 3 pause items | `0x0802A67C` | alphabet lookup `alphabet[buf[i]]`, `^` drawn as `?` |
| Draw `"PASSWORD: "` + code line | `0x0802A778` | |
| Pause-menu screen update | `0x0802A8D8` | calls generator/draw |
| Divide helper `v / n` | `0x080314B0` | used by generator/decoder |
| Modulo helper `v % n` | `0x08031528` | |

### 4.3 Block Party RAM (IWRAM)

| Address | Size | Meaning |
|---|---:|---|
| `0x030031A0` | 16 | symbol indices 0–31 currently entered/displayed |
| `0x030012CA` | 1 | symbol count (0–16) |
| `0x030012CB` | 1 | cursor column (0–7) |
| `0x030012CC` | 1 | cursor row (0–3) |
| `0x030012C0` | 10 | packed 80-bit buffer |
| `0x030012CE` | 2 | bit position inside the buffer |
| `0x030012D0` | 4 | packed-buffer pointer (initialised to `0x030012C0`) |
| `0x03002560` | 48 | four 12-byte player records (see table 6.2) |
| `0x0300252C` | 1 | board index 0–3; also the item-nibble shift selector |
| `0x03002532` | 1 | encoded field `unk2` (2 bits) |
| `0x03002538` | 1 | encoded field `unk3` (1 bit) |

Note that `0x0300252C` doubles as the "which board's item nibble" selector: the
per-player 16-bit word at record `+0x0A` holds four 4-bit item counts, one per board.

### 4.4 Speedway (half 1) password-related addresses

| Purpose | File offset | ROM address |
|---|---:|---:|
| Localised string table header `{count=103, 1, stride=0x44}` | `0x4E9A18` | `0x084E9A18` |
| Record 0 `"Single Player"` | `0x4E9A24` | `0x084E9A24` |
| Record 4 `"Password"` | `0x4E9B34` | `0x084E9B34` |
| Record 45 `"Enter Password"` | `0x4EA618` | `0x084EA618` |
| Record 97 `"Please note new password"` | `0x4EB3E8` | `0x084EB3E8` |

String address = `0x084E9A24 + id * 0x44`.

### 4.5 Speedway password code

| Purpose | ROM address | Notes |
|---|---:|---|
| Password **validator/decoder** | `0x08415E90` | `(ctx, value, save_struct)`; returns 1 = accepted, 0 = rejected |
| Caller (builds the number, applies the result) | `0x0841630A` | builds `%08d` number from the digit bytes at `state+5…state+0xC` |
| `"%08d"` format string | `0x0841627C` | `25 30 38 64 00 00` |
| Digit permutation table (IWRAM copy) | `0x0300372F` | `05 01 03 00 02 06 04` |
| Character-index table (12 entries) | `0x08463334` | `1,10,2,3,6,7,0,8,5,11,9,4` |
| Per-character stat table (12 × u32) | `0x08463140` | `0x2EE0, 0x0FA0, 0x1770, 0x1B58, 0x55F0, …` |
| Check-digit helper | `0x0842C120` | ARM veneer; behaviour is `sum mod 10` (13/13 public codes) |

Decoded-state layout (`save+0xFC`, 0x58 bytes, cleared by the validator):

| Offset | Meaning |
|---|---|
| `+0x00…+0x04` | the five 2-bit award fields `f0…f4` |
| `+0x06` (u16) | unlock counter `n` (bits 18:15 of the payload) |
| `+0x08,+0x10,+0x18,+0x20,+0x28` | u32 flags: `f_i == 1` |
| `+0x0C,+0x14,+0x1C,+0x24,+0x2C` | u32 flags: companion bit 10…14 |
| `+0x30` | u32 flag: both character bits 19 and 20 set |
| `+0x34,+0x38,+0x3C,+0x40,+0x44` | u32 championship flags, set when `n >= 4/6/8/10/11` |
| `+0x48,+0x4C,+0x50,+0x54,+0x58` | u32 flags: `f_i != 0` |

Content mask: the 12-bit word at `0x020009A4` (save base `0x02000974 + 0x30`) is the
unlock mask; bit *i* is set for the table entries selected by bits 19/20 and `n`.

## 5. Algorithm

### 5.1 Block Party — symbol packing

The 16 symbols are converted to their alphabet indices (0–31) and written MSB-first,
5 bits each, into 10 bytes (80 bits). The bit writer is `0x080298D4`; the reader is
inlined in the validator.

```
index('B')=0, 'C'=1, 'D'=2, 'F'=3, ... 'V'=16, ... '9'=30, '^'=31
bits[0:5]   = index(symbol 0)   (bits 4..0)
bits[5:10]  = index(symbol 1)
...
bits[75:80] = index(symbol 15)
```

### 5.2 Block Party — 80-bit record

| Bits | Width | Field | Stored in / notes |
|---|---:|---|---|
| 0 | 1 | start marker, must be 1 | |
| 1–2 | 2 | **board** 0–3 | `0x0300252C` |
| 3–4 | 2 | `unk2` (observed 0) | `0x03002532` |
| 5 | 1 | `unk3` (observed 0) | `0x03002538` |
| 6 | 1 | player-2 type flag | player[1]`+1`; 0 = CPU, 1 = human/unused |
| 7 | 1 | player-3 type flag | player[2]`+1` |
| 8 | 1 | player-4 type flag | player[3]`+1` |
| 9–17 | 9 | character-selection rank | mixed radix, see 5.3 |
| 18 | 1 | middle marker, must be 1 | |
| 19–24 | 6 | P1 board position | player[0]`+3`, `0x3F` = not playing |
| 25–29 | 5 | P1 score / 5 | player[0]`+2` |
| 30–33 | 4 | P1 item count for this board | player[0]`+0x0A` nibble |
| 34–39 | 6 | P2 board position | player[1]`+3` |
| 40–44 | 5 | P2 score / 5 | player[1]`+2` |
| 45–48 | 4 | P2 item count | player[1]`+0x0A` nibble |
| 49–54 | 6 | P3 board position | player[2]`+3` |
| 55–59 | 5 | P3 score / 5 | player[2]`+2` |
| 60–63 | 4 | P3 item count | player[2]`+0x0A` nibble |
| 64–69 | 6 | P4 board position | player[3]`+3` |
| 70–74 | 5 | P4 score / 5 | player[3]`+2` |
| 75–78 | 4 | P4 item count | player[3]`+0x0A` nibble |
| 79 | 1 | end marker, must be 1 | |

Player 1's type flag is implicit 1 (it is written as a constant by the generator and
re-set by the decoder).

The "stored in" column is what the **generator** reads. The **decoder** is not symmetric
for the position field: it writes the 6-bit position to `player_struct + 8` (record
offset, `0x0802A35C`) instead of `+3`, which is why only player 1's position survives a
round trip in this build (see §7 and §8).

### 5.3 Character-selection rank (9 bits, 6 characters)

The four player characters are stored as ordered *distinct* picks from 6 characters
(6·5·4·3 = 360 states, fits in 9 bits).

Encoder (`0x08029DC4`), given live character ids `c0..c3` (0–5, unused = 6/7):

```
if c3 >= c2: c3 -= 1
if c3 >= c1: c3 -= 1
if c3 >= c0: c3 -= 1
if c2 >= c1: c2 -= 1
if c2 >= c0: c2 -= 1
if c1 >= c0: c1 -= 1
for each player whose position field is 0x3F: c[i] = 0     ; unused slot
rank = 120*c3 + 30*c2 + 6*c1 + c0
```

Decoder (`0x08029FD8`):

```
c0 = rank % 6 ; c1 = (rank/6) % 5 ; c2 = (rank/30) % 4 ; c3 = (rank/120) % 3
if c3 >= c2: c3 += 1
if c3 >= c1: c3 += 1
if c3 >= c0: c3 += 1
if c2 >= c1: c2 += 1
if c2 >= c0: c2 += 1
if c1 >= c0: c1 += 1
```

### 5.4 Decoder validation rules (`0x08029FD8`)

1. If all 16 symbols are identical → reject (blank field).
2. Bits 0, 18 and 79 must each be 1.
3. Position bound depends on the board field:
   `0x30` (48) for board 0, `0x34` (52) for board 1, `0x2C` (44) for board 2,
   `0x31` (49) for board 3; `0x3F` is always allowed (slot not on the board).
4. `score*5 <= 150` (`0x96`) for every player.
5. Players must be contiguous: scanning players 4→2, if player *i* is playing
   (character ≤ 5) then player *i-1* must also be playing.
6. A player whose position field is `0x3F` gets character id 7 (unused) regardless of
   the rank.

Return 1 = accepted (the caller sets the resume flags and starts the game);
return 0 = rejected (the screen stays).

### 5.5 Python reimplementation

```python
ALPHABET = "BCDFGHJKLMNPQRSTVWXYZ0123456789^"   # ROM 0x08278094
MAXPOS   = [0x30, 0x34, 0x2C, 0x31]

def _rank(c):                    # 4 live character ids -> mixed-radix digits
    c = list(c)
    if c[3] >= c[2]: c[3] -= 1
    if c[3] >= c[1]: c[3] -= 1
    if c[3] >= c[0]: c[3] -= 1
    if c[2] >= c[1]: c[2] -= 1
    if c[2] >= c[0]: c[2] -= 1
    if c[1] >= c[0]: c[1] -= 1
    return c

def encode(board, chars, flags, pos, score, item, unk2=0, unk3=0):
    dg = _rank(chars)
    for i in range(4):
        if pos[i] == 0x3F: dg[i] = 0          # unused slot digits are zeroed
    rank = 120*dg[3] + 30*dg[2] + 6*dg[1] + dg[0]
    bits  = "1" + f"{board:02b}" + f"{unk2:02b}" + f"{unk3:01b}"
    bits += "".join(f"{flags[i]:01b}" for i in (1,2,3))
    bits += f"{rank:09b}" + "1"
    for i in range(4):
        bits += f"{pos[i]:06b}{score[i]:05b}{item[i]:04b}"
    bits += "1"
    assert len(bits) == 80
    return "".join(ALPHABET[int(bits[i*5:i*5+5], 2)] for i in range(16))
```

The complete, tested module (encode + decode + validation) is section 9.

### 5.6 Speedway — 8-digit code

The validator receives the entered number `N` (`d1…d8` left-to-right on screen) and
formats it with `"%08d"`, so leading zeros are preserved. The parse is:

1. **Check digit.** `d1` must equal `(d2 + d3 + … + d8) mod 10`. Mismatch → return 0.
2. **Permutation.** With `p = [5,1,3,0,2,6,4]`, the remaining digits are placed as
   `digits[p[i]] = d(i+2)`.
3. **Payload.** `value = Σ digits[j] · 10^(6-j)`, i.e.

   ```
   value = 1000000·d5 + 100000·d3 + 10000·d6 + 1000·d4 + 100·d8 + 10·d2 + d7
   ```

4. **Range.** The validator computes `value >> 21`; if non-zero the code is rejected
   (`0x08415F06`). So `value < 0x200000`.
5. **Fields.** The 21 bits are unpacked as in table 6.6 and written to `save+0xFC`;
   bits 19/20 and `n` also set bits in the 12-bit content mask at `0x020009A4`.

Encoder (the inverse used by `swpass.py`):

```python
def encode(value):                     # value < 2**21
    out = [0]*9
    for d, w in ((5,1000000),(3,100000),(6,10000),(4,1000),(8,100),(2,10),(7,1)):
        out[d] = (value // w) % 10
    out[1] = sum(out[2:9]) % 10        # check digit
    return "".join(str(out[i]) for i in range(1, 9))
```

Sanity check: `encode(0x1E7D55) == "96981951"`, `encode(0x15) == "32000010"`,
`encode(1) == "10000010"`.

## 6. Tables

### 6.1 Alphabet and its 5-bit value

The entry grid is the alphabet in order, 8 per row (row-major index = `row*8+col`):

| row \ col | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| 0 | B=0 | C=1 | D=2 | F=3 | G=4 | H=5 | J=6 | K=7 |
| 1 | L=8 | M=9 | N=10 | P=11 | Q=12 | R=13 | S=14 | T=15 |
| 2 | V=16 | W=17 | X=18 | Y=19 | Z=20 | 0=21 | 1=22 | 2=23 |
| 3 | 3=24 | 4=25 | 5=26 | 6=27 | 7=28 | 8=29 | 9=30 | ?=31 (`^` in ROM) |

### 6.2 Player record (`0x03002560 + 12*i`)

| Offset | Size | Field |
|---|---:|---|
| `+0x00` | 1 | character id (0–5 playing, 7 unused) |
| `+0x01` | 1 | type flag (0 CPU, 1 human/unused); player 1 always 1 |
| `+0x02` | 1 | score (in-game value; password stores `score/5`) |
| `+0x03` | 1 | board position (`0x3F` = not on board) |
| `+0x0A` | 2 | per-board item nibbles: nibble *n* belongs to board *n* |

### 6.3 Boards (bits 1–2 of the record)

| Value | Board | Max position accepted | Evidence |
|---:|---|---:|---|
| 0 | Tater Farm | `0x30` (48) | observed: pause code, password resume |
| 1 | Extreme Cul-de-Sac | `0x34` (52) | observed: `ZJBD…` starts the locked board |
| 2 | Planet Johnnywood | `0x2C` (44) | observed: `3JBD…` starts the locked board |
| 3 | Katz's Creepy Castle | `0x31` (49) | observed: `7JBD…` starts the locked board |

### 6.4 Verified Block Party codes

All were entered on the real password screen and their effect observed in mGBA.

| Code (as typed; `?` = index 31) | board | players | effect |
|---|---:|---|---|
| `VJBDBBBBBC?BC?BC` | 0 | Courage, Johnny (CPU), 2 empty | resumes the exact Tater Farm game the pause menu encoded; pause menu shows the same code again |
| `VJBDNBBZBC?BC?BC` | 0 | Courage, Johnny, P1 position 10, P2 position 20 | resumes Tater Farm; the pause menu afterwards shows `VJBDNBBBC?BC?BC`, i.e. P1 = 10 (P2 came back as 0 — see §8) |
| `ZJBDBBBBBC?BC?BC` | 1 | Courage, Johnny | starts Extreme Cul-de-Sac (locked in the menu) |
| `3JBDBBBBBC?BC?BC` | 2 | Courage, Johnny | starts Planet Johnnywood (locked in the menu) |
| `7JBDBBBBBC?BC?BC` | 3 | Courage, Johnny | starts Katz's Creepy Castle (locked in the menu) |

**Character ids (all six exercised).** A one-character code was generated for each id
(`VSBxBBC?BC?BC?BC`, player 1 only) and the resumed board was screenshot; the in-game HUD
portrait and board sprite were matched to the `CHARACTER SELECT` portraits/names:

| id | Character | Evidence |
|---:|---|---|
| 0 | Courage | pink dog on the board (`VSBDBBC?BC?BC?BC`) |
| 1 | Eddy | round-faced boy, yellow shirt (`VSBJBBC?BC?BC?BC`) |
| 2 | Sarah | orange-haired girl, pink top (`VSBNBBC?BC?BC?BC`) |
| 3 | Cow | cow sprite (`VSBSBBC?BC?BC?BC`) |
| 4 | Chicken | white bird with red comb (`VSBXBBC?BC?BC?BC`) |
| 5 | Johnny Bravo | blonde with sunglasses (`VSB1BBC?BC?BC?BC`) |

Note that the `SELECT PLAYER` screen lists them in the order Courage, Johnny Bravo,
Chicken, Cow, Sarah, Eddy — i.e. ids `0,5,4,3,2,1` — so the menu order is *not* the id
order. The id order is the one the 9-bit rank encodes.

### 6.5 Speedway published codes

Collected from Vizzed (full page, live) and GameFAQs/CheatHappens snippets (GameFAQs
returned 403 to automated fetch; only snippets were available). **None of these strings
occurs in the ROM image** (literal search), so the codes are computed, not stored.

| Code | Listed effect |
|---|---|
| `12761357` | Farm Frolics |
| `25731079` | Muriel / Down on the Farm |
| `38611791` | Edopolis |
| `52681314` | Johnny 2x4 |
| `68851752` | Scary Speedway |
| `81821475` | Little Suzy / Desert Drive |
| `84891097` | Hot Rod Johnny |
| `98761719` | Alpine Antics / Swanky |
| `10000010` | Cartoon Speedway trophy |
| `32000010` | Fender Bender Frenzy trophy |
| `50000050` | ACME Axel Award trophy |
| `34711154` | All championships won |
| `96981951` | **Unlock Everything — verified in mGBA** |

### 6.6 Speedway decoded field table

Payload bits (all 13 published codes decode as follows; `n` is printed in decimal):

| Code | Payload | f0 | f1 | f2 | f3 | f4 | 10 | 11 | 12 | 13 | 14 | n | 19 | 20 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `10000010` | `0x00001` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `50000050` | `0x00005` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `32000010` | `0x00015` | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `52681314` | `0x190015` | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 1 |
| `38611791` | `0x198015` | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 1 | 1 |
| `25731079` | `0x1A0015` | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 1 | 1 |
| `34711154` | `0x1A1D55` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 4 | 1 | 1 |
| `12761357` | `0x1A8015` | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 1 | 1 |
| `98761719` | `0x1B1D55` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 6 | 1 | 1 |
| `84891097` | `0x1B9D55` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 7 | 1 | 1 |
| `81821475` | `0x1C1D55` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 8 | 1 | 1 |
| `68851752` | `0x1C9D55` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 9 | 1 | 1 |
| `96981951` | `0x1E7D55` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 12 | 1 | 1 |

Field semantics established from the validator and from in-game effects:

* **Characters** — bits 18:15 (`n`) select `table[2..n]`, bits 19 and 20 add
  `table[0]=1` and `table[1]=10`, where `table = 0x08463334`. Verified by roster counts:
  fresh boot = 6 characters; `n=12` without bits 19/20 = 11; `n=12` with them = 12;
  bits 19+20 alone (`n=0`) = 7; `n=3` = 6.
* **Awards / trophies** — the five 2-bit fields `f0…f4` plus companion bits 10…14. The
  three published award codes are cumulative prefixes of this bit set:
  `10000010` (`f0`) = Cartoon Speedway Trophy, `50000050` (`f0,f1`) = ACME Axel Award,
  `32000010` (`f0,f1,f2`) = Fender Bender Frenzy Trophy. Each field also raises the
  matching flag at `save+0x08/+0x10/+0x18/+0x20/+0x28` (value 1) and `+0x48…+0x58`
  (non-zero).
* **Championships** — derived from `n`: `save+0x34/+0x38/+0x3C/+0x40/+0x44` are set when
  `n >= 4/6/8/10/11` (`0x08416006`–`0x0841601C`). "All Championships Won" (`0x1A1D55`) has
  `n=4`, the first threshold.
* **Tracks** — not a separate field: the same 12-entry table indexes the 12-bit content
  mask at `0x020009A4`, which is the shared unlock mask (verified for the character
  roster; the track select reads the same save block).

## 6b. Enumeration

### Block Party

* **Alphabet / length:** 32 symbols (`BCDFGHJKLMNPQRSTVWXYZ0123456789^`), fixed 16
  symbols. Raw string space = `32^16` = `2^80` ≈ 1.21·10^24.
* **Structural constraints:** bit 0, bit 18 and bit 79 must be 1 (3 fixed bits → /8);
  the 9-bit character rank only accepts 360 of 512 values (6·5·4·3); each position is
  bounded per board (`0x30/0x34/0x2C/0x31`, plus `0x3F` for "not playing"); each score
  is ≤ 30 (raw) so that `score·5 ≤ 150`; players must be contiguous.
* **Effective space:** for each board, `360 · 8 · 4 · 2 · ((pos_max+2)·31·16)^4`, i.e.

  | board | positions accepted | codes |
  |---|---:|---:|
  | 0 | 50 (`0..0x30` + `0x3F`) | 8.72·10^21 (2^72.9) |
  | 1 | 54 | 1.19·10^22 (2^73.3) |
  | 2 | 46 | 6.24·10^21 (2^72.4) |
  | 3 | 51 | 9.43·10^21 (2^73.0) |

  Total ≈ 3.63·10^22 (2^74.9) before the "players must be contiguous" rule prunes a
  minority. The *published* Block Party code space is empty — no Block Party code appears
  on GameFAQs, Vizzed, TCRF or any wiki, because every code describes one save state.
* **Novel codes generated and confirmed:** `VJC5BBBBBC?BC?BC` (characters Sarah+Cow,
  round-trips), `VSBSBBC?BC?BC?BC` (Cow), `VSBXBBC?BC?BC?BC` (Chicken),
  `VSB1BBC?BC?BC?BC` (Johnny Bravo), `VSBDBBC?BC?BC?BC` (Courage),
  `VSBJBBC?BC?BC?BC` (Eddy), `VSBNBBC?BC?BC?BC` (Sarah),
  `VSBFVBC?BC?BC?BC` (position 48 on board 0, the maximum).
* **Bounds proven by rejection:** `VSBFWBC?BC?BC?BC` has position 49 on board 0 (bound
  48). The entry buffer was read back from a savestate after 15 symbols
  (`"VSBFWBC^BC^BC^B"`), the 16th symbol was entered, and the game stayed on the
  `PASSWORD` screen with the buffer cleared (count 0) instead of starting the board. The
  control `VSBFVBC?BC?BC?BC` (position 48) starts the board.
  The decoder's first check (`0x08029FE2`) additionally rejects any code whose 16 symbols
  are identical.

### Speedway

* **Alphabet / length:** decimal digits, fixed 8. Raw string space = `10^8` = 100 000 000.
* **Structural constraints:** digit 1 is `(sum of digits 2…8) mod 10` (÷10), and the
  21-bit payload must be `< 0x200000`. Each 7-digit payload maps bijectively to one
  8-digit string, so exactly **2 097 152** codes are structurally valid.
* **Field space:** 2^21 payloads = `n` (4 bits, values 0–15, 12 meaningful) × `f0…f4`
  (2 bits each) × bits 10–14 (5 bits) × bits 19/20 (2 bits).
* **Novel codes generated and confirmed:**
  * `41330962` (payload `0x60000`: `n=12`, no award bits) — `CHARACTER SELECT` shows 11
    characters, i.e. maximum progress **without** any trophy. No published list contains
    this value, and no published code has `n=12` with a zero award field.
  * `36521748` (payload `0x180000`: bits 19+20 only, `n=0`) — 7 characters with zero
    progress. Again absent from every published list.
* **Bounds proven by rejection:**
  * `51330962` — same payload as `41330962` but check digit 5 instead of 4. Submitted;
    the save block stayed zero (`0x020009A4 = 0x0000`, `0x02000A70` all zero) and the
    character roster stayed at 6.
  * `39999999` — check digit valid (`3 = 63 mod 10`) but payload 9 999 999 ≥ 2^21.
    Submitted; same zero save block, roster unchanged.
  * Control `41330962` — accepted, mask `0x020009A4` becomes non-zero and the roster
    grows to 11.

## 7. Validation evidence

### Observed (emulator)

* Shell menu on boot shows both games; the cart boots from the second image and launches
  Block Party from image 0.
* Block Party pause menu on a fresh Tater Farm game displays
  `PASSWORD: VJBDBBBBBC?BC?BC`.
* Entering `VJBDBBBBBC?BC?BC` at `RESUME GAME` returns to the Tater Farm intro, then to
  the board with Courage and Johnny; pressing `Start` shows the identical password again.
* Entering `ZJBDBBBBBC?BC?BC` shows the `EXTREME CUL-DE-SAC` intro and starts that board,
  although `SELECT BOARD` only offers Tater Farm before the code.
* `3JBDBBBBBC?BC?BC` → `PLANET JOHNNYWOOD` intro; `7JBDBBBBBC?BC?BC` →
  `KATZ'S CREEPY CASTLE` intro.
* Editing the savestate's live position byte (`0x03002563`, P1 `+3`) to 7 and re-opening
  the pause menu changes the displayed password's 6-bit field to 7 (`VJBDKBBB…`),
  proving the generator reads that byte. Editing `0x0300256F` (P2 `+3`) to 5 likewise
  changes P2's field (`…BBH…`).
* Speedway: entering `96981951` at the Password screen and then opening
  `Single Player → Championship → Character Select` shows 12 characters (fresh boot shows
  6 plus six `?` slots).
* Speedway novel code `41330962` → `CHARACTER SELECT` shows 11 characters and **no**
  award flags; `36521748` → 7 characters, no award flags.
* Speedway rejections: `51330962` (bad check digit) and `39999999` (payload ≥ 2^21) both
  return to the main menu with the save block untouched — savestates show
  `0x020009A4 = 0x0000` and `0x02000A70` all zero, identical to the pre-entry state.
* Block Party rejection: after 15 symbols the entry buffer was read from a savestate as
  `"VSBFWBC^BC^BC^B"`, the 16th symbol (`C`, giving position 49 on board 0) was appended,
  and the game **stayed on the `PASSWORD` screen** with the buffer cleared (count 0).
  The control code with position 48 (`VSBFVBC?BC?BC?BC`) starts the board.
* Block Party character ids: one-character codes `VSBDBB…`, `VSBJB…`, `VSNB…`, `VSBSB…`,
  `VSBXB…`, `VSB1B…` resume with Courage, Eddy, Sarah, Cow, Chicken and Johnny Bravo
  respectively (HUD portrait + board sprite matched to the `SELECT PLAYER` portraits).

### Derived (instruction-level)

* 5 bits per symbol, MSB-first, 16 symbols = 80 bits (`0x080298D4`, `0x08029FD8`).
* Field widths/bits of section 5.2 from the decoder's read sizes and the generator's
  write sizes; confirmed by reproducing the observed code byte-for-byte from the decoded
  fields.
* Character rank base 6/5/4/3 from `%6, /6%5, /30&3, /120%3` in `0x08029FD8` and the
  inverse in `0x08029DC4`.
* Board bounds (`0x30/0x34/0x2C/0x31`) from the four compares in `0x08029FD8`.
* Score is stored divided by 5: encoder `value / 5` via `0x080314B0`, decoder
  `value * 5` via `lsls/adds`, with the bound `<= 0x96` (150).
* Item nibble selection `(u16 >> (4*board)) & 0xF`: encoder at `0x08029F2A`, decoder at
  `0x0802A43E`.
* Unused-slot handling: generator zeroes the mixed-radix digit and forces position
  `0x3F`; decoder sets character 7 when position is `0x3F`.
* Speedway check digit: the validator sums the seven payload digits (`0x08415EB6`–
  `0x08415ECA`), calls `0x0842C120` and compares the result with digit 1
  (`0x08415EF4`). All 13 published codes satisfy `d1 = sum mod 10`, and the two
  deliberately wrong check digits are rejected, so the function is `sum mod 10`.
* Speedway digit permutation from the indirect store `digits[table[i]] = d(i+2)` with
  `table` loaded from `0x0300372F` (= `5,1,3,0,2,6,4`).
* Speedway payload weights from the multiply/accumulate loop at `0x08415ECC`–`0x08415EEA`
  (×10 each step, digits consumed in reverse index order).
* Speedway range check: `value >> 21 != 0 → return 0` (`0x08415F06`).
* Speedway award/character unpacking: `0x08415F0E`–`0x0841601C` (see tables 4.5 and 6.6).

### Inferred

* `score` is the board's money/tater counter (board 1's win text is "three trophies and
  50 dollars" and only 5-bit×5 values are representable); `item` is the board's
  collectible count (porkbutts/trophies/items/spiders). Both were not read from a HUD.
* `unk2` (2 bits) and `unk3` (1 bit) are saved but were 0 in every state observed.
* The labels attached to the Speedway award slots (which named trophy belongs to each of
  `f0…f5`) follow the three published award codes; the remaining two slots have no
  published description.
* The Speedway track list is filtered by the same 12-bit content mask at `0x020009A4`:
  the mask is verified for the character roster, and the track select reads the same save
  block, but the individual track entries were not enumerated screen-by-screen.

## 8. Unknowns

* `unk2`/`unk3` semantics (always 0 in the tested game states: Tater Farm resume and
  fresh games).
* The exact in-game wording of each Speedway award slot `f3`/`f4` (no published code
  exercises them alone).
* Players 2–4 positions do not survive a round trip in this build. The decoder writes the
  6-bit position to record offset `+8` (`0x0802A35C`, `strb r3,[r0,#8]` with
  `r0 = 0x03002560 + 12*i`), while the generator reads the live position from record
  offset `+3` (`0x08029F0E`). Observed: `VSBDNBBZBC?BC?BC` (P1 = 10, P2 = 20) resumed and
  the pause menu regenerated `VSBDNBBBC?BC?BC`, i.e. P1 = 10 but P2 = 0; RAM after the
  decode showed P2's value 20 at `0x03002574` (record `+8`) while `0x0300256F` (record
  `+3`) was still 0; P1's 10 had also reached `0x03002563` (record `+3`). Player-1
  position, board, characters and type flags are unaffected.
* The exact wording/effect of a fully "won" code (all four porkbutts etc.) was not tested.

## 9. Tooling

All scripts are in `/tmp/opencode/cn` (disposable). mGBA 0.10.5 (`/usr/games/mgba`),
`arm-none-eabi-objdump`, Capstone 5.0.7, Xvfb + openbox + xdotool + scrot.

### `bppass.py` — Block Party codec (encode/decode/validate)

```python
#!/usr/bin/env python3
ALPHABET = "BCDFGHJKLMNPQRSTVWXYZ0123456789^"   # ROM 0x08278094
MAXPOS   = [0x30, 0x34, 0x2C, 0x31]

def _unrank(c):                 # rank digits -> character ids (decoder)
    c = list(c)
    if c[3] >= c[2]: c[3] += 1
    if c[3] >= c[1]: c[3] += 1
    if c[3] >= c[0]: c[3] += 1
    if c[2] >= c[1]: c[2] += 1
    if c[2] >= c[0]: c[2] += 1
    if c[1] >= c[0]: c[1] += 1
    return c

def _rank(c):                   # character ids -> rank digits (encoder)
    c = list(c)
    if c[3] >= c[2]: c[3] -= 1
    if c[3] >= c[1]: c[3] -= 1
    if c[3] >= c[0]: c[3] -= 1
    if c[2] >= c[1]: c[2] -= 1
    if c[2] >= c[0]: c[2] -= 1
    if c[1] >= c[0]: c[1] -= 1
    return c

def encode(board, chars, flags, pos, score, item, unk2=0, unk3=0):
    dg = _rank(chars)
    for i in range(4):
        if pos[i] == 0x3F: dg[i] = 0
    rank = 120*dg[3] + 30*dg[2] + 6*dg[1] + dg[0]
    b  = "1" + f"{board:02b}" + f"{unk2:02b}" + f"{unk3:01b}"
    b += "".join(f"{flags[i]:01b}" for i in (1, 2, 3))
    b += f"{rank:09b}" + "1"
    for i in range(4):
        b += f"{pos[i]:06b}{score[i]:05b}{item[i]:04b}"
    b += "1"
    assert len(b) == 80
    return "".join(ALPHABET[int(b[i*5:i*5+5], 2)] for i in range(16))

def decode(code):
    code = code.replace("?", "^")
    bits = "".join(f"{ALPHABET.index(c):05b}" for c in code)
    p = 0
    def rd(n):
        nonlocal p
        v = int(bits[p:p+n], 2); p += n; return v
    if len(code) != 16: raise ValueError("need 16 symbols")
    if rd(1) != 1: raise ValueError("start marker")
    board = rd(2); unk2 = rd(2); unk3 = rd(1)
    flags = [1] + [rd(1) for _ in range(3)]
    rank = rd(9)
    if rd(1) != 1: raise ValueError("middle marker")
    pos, score, item = [], [], []
    for _ in range(4):
        pos.append(rd(6)); score.append(rd(5)*5); item.append(rd(4))
    if rd(1) != 1: raise ValueError("end marker")
    chars = _unrank([rank % 6, (rank//6) % 5, (rank//30) % 4, (rank//120) % 3])
    for i in range(4):
        if pos[i] == 0x3F: chars[i] = 7
        elif pos[i] > MAXPOS[board]: raise ValueError("position range")
        if score[i] > 150: raise ValueError("score range")
    return dict(board=board, unk2=unk2, unk3=unk3, flags=flags,
                chars=chars, pos=pos, score=score, item=item)

if __name__ == "__main__":
    print(encode(0, [0,1,7,7], [1,0,1,1], [0,0,63,63], [0,0,0,0], [0,0,0,0]))
    # -> VJBDBBBBBC^BC^BC   (the pause-menu code of a fresh Tater Farm game)
```

### `swpass.py` — Speedway codec (encode/decode/validate)

```python
#!/usr/bin/env python3
"""Cartoon Network Speedway 8-digit password codec.
Validator: Thumb 0x08415E90; check digit 0x0842C120; permutation at IWRAM 0x0300372F."""

def encode(value):
    """21-bit payload -> 8-digit code (digit 1 = checksum)."""
    if not 0 <= value < (1 << 21):
        raise ValueError("value out of 21-bit range")
    out = [0] * 9
    for d, w in ((5, 1000000), (3, 100000), (6, 10000), (4, 1000),
                 (8, 100), (2, 10), (7, 1)):
        out[d] = (value // w) % 10
    out[1] = sum(out[2:9]) % 10
    return "".join(str(out[i]) for i in range(1, 9))

def decode(code):
    """8-digit code -> (payload, fields)."""
    if len(code) != 8 or not code.isdigit():
        raise ValueError("need 8 digits")
    d = [int(c) for c in code]
    if d[0] != sum(d[1:]) % 10:
        raise ValueError("checksum mismatch")
    v = (1000000*d[4] + 100000*d[2] + 10000*d[5] + 1000*d[3]
         + 100*d[7] + 10*d[1] + d[6])
    if v >> 21:
        raise ValueError("value out of range")
    return v, dict(f0=v & 3, f1=(v >> 2) & 3, f2=(v >> 4) & 3,
                   f3=(v >> 6) & 3, f4=(v >> 8) & 3,
                   b10=(v >> 10) & 1, b11=(v >> 11) & 1, b12=(v >> 12) & 1,
                   b13=(v >> 13) & 1, b14=(v >> 14) & 1,
                   n=(v >> 15) & 15, b19=(v >> 19) & 1, b20=(v >> 20) & 1)

if __name__ == "__main__":
    assert encode(0x1E7D55) == "96981951"
    assert encode(0x15) == "32000010"
    print(encode(0x60000))      # 41330962  (novel: 11 characters, no awards)
```

### `enter.py` — Block Party grid typer

```python
# maps a code string to D-pad + A presses for mGBA (A = x)
alpha = "BCDFGHJKLMNPQRSTVWXYZ0123456789^"
r = c = 0
for ch in code:
    tr, tc = divmod(alpha.index(ch), 8)
    while r != tr: press("Down" if (tr-r) % 4 <= (r-tr) % 4 else "Up"); r = (r+1)%4
    while c != tc: press("Right" if (tc-c) % 8 <= (c-tc) % 8 else "Left"); c = (c+1)%8
    press("x")
```

### Other helpers used

* `tdis.py` — Capstone Thumb/ARM disassembler with PC-relative literal resolution.
* `xref.py` — BL-target and 32-bit pointer scans.
* `patchstate.py` — decompress an mGBA `.ss` PNG (`gbAs` chunk), patch IWRAM, recompress
  and rewrite the PNG; used to edit `0x03002563`/`0x0300256F` for the generator probes.
* `dbgd.py` — drives `mgba -d` through a pty (register/memory read, breakpoints,
  watchpoints) when the GDB stub port was occupied.

Legal note: no ROM, graphic, audio or text asset is reproduced here; only addresses,
algorithms and codes this analysis produced.
