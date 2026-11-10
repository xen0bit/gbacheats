# Cartoon Network: Block Party (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Cartoon Network: Block Party/Cartoon Network: Block Party.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title (0xA0) | `CNBLOCKPARTY` |
| Game code (0xAC) | `AC9E` |
| Maker code (0xB0) | `5G` |
| Software version (0xBC) | `0x00` (Rev.00) |
| Fixed 0x96 (0xB2) | present |
| Entry word (0x00) | `0xEA00002E` → branch to `0x080000C0` (stock crt0) |
| Header checksum (0xBE) | `0x0000` |
| Complement byte (0xBD) | `0x47` (standard formula gives `0x46`) |
| MD5 | `fc244be5e2a8b811ea2b2e0101d64a6e` |
| SHA-1 | `5e1ae3428c528755dc9c58e28df349bf58b17a45` |
| SHA-256 | `42edf0804c7b11fd2077d1488078bc85f09aa0cafa7a6d565d6b2ef9c4d4baba` |
| Save type | SRAM (a `.sav` is created) |

**Phase 0 / patch check.** The 156-byte Nintendo logo occurs exactly once, at file
`0x04` (header base `0x0`); there is no second embedded GBA header. The entry word is
the stock `b 0x080000C0`. The crt0 at `0x080000C0` is the normal ARM startup
(`mov r0,#0x12; bic r0,r0,#0x29; ldr r13,[pc,#0x28]; …`). **No cracktro, trainer, or
patched entry point.**

The header checksum field is `0x0000` and the complement byte is one higher than the
standard formula produces. This is a **collection-wide dump artifact**, not a
game-specific patch: all 25 ROMs sampled from `roms/` (e.g. *Castlevania: Aria of
Sorrow*, *Kingdom Hearts: Chain of Memories*, *Banjo-Kazooie: Grunty's Revenge*)
show the same `stored = computed + 1` complement and a zeroed checksum field. The
entry point and crt0 are stock, so the game image itself is unmodified.

## 2. Executive summary

The game has a **16-character password system** reached from the main menu with
`RESUME GAME`. The on-screen keyboard is a 4 × 8 grid of 32 symbols:

```
B C D F G H J K
L M N P Q R S T
V W X Y Z 0 1 2
3 4 5 6 7 8 9 ?
```

The ROM alphabet table is `BCDFGHJKLMNPQRSTVWXYZ0123456789^` (file `0x278094`). The
last symbol is stored as `^` (0x5E) but **drawn as `?`** (the display code at
`0x08029A3C` / `0x0802A6CC` rewrites `0x5E` to `0x3F`). This is why every published
code contains `?`.

Each character carries 5 bits, so a password is an 80-bit structure. The bits are
packed MSB-first into a 10-byte buffer. The layout is:

| Bits | Width | Field |
|---:|---:|---|
| 0 | 1 | constant `1` |
| 1–2 | 2 | **A** — board index (0…3) |
| 3–4 | 2 | **B** — flag | 
| 5 | 1 | **C** — flag |
| 6–8 | 3 | **b1** — player flags (entries 1…3 byte 1) |
| 9–17 | 9 | **mixed** — combinatorial encoding of 4 player values |
| 18 | 1 | constant `1` |
| 19–78 | 60 | 4 × 15 bits: **f6** (6) + **f5** (5) + **f4** (4) |
| 79 | 1 | constant `1` |

The validator is a decoder at `0x08029FD8`; the matching encoder (game state →
password) is at `0x08029DC4`. There is **no checksum**: validity comes from three
constant bits plus per-field range checks and a wildcard-suffix rule.

All four published tournament passwords were checked. Three are correct 16-character
codes; the fourth (Extreme Cul-De-Sac) is published 15 characters and is rejected. The
pattern-consistent 16-character correction is accepted and loads the correct board.

A novel, unpublished password was minted from the reversed format, entered on the
real password screen, and accepted; the pause menu re-displays it, proving the game
state matches. Bounds were proven by in-game rejection of constant-bit flips,
out-of-range fields, wrong lengths, and all-identical passwords.

## 3. How to reproduce

**Emulator.** mGBA 0.10.5 (`mgba-sdl`, binary `/usr/games/mgba`), `SDL_AUDIODRIVER=dummy`,
`-3` scale, under `Xvfb`. Default SDL keymap:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Hold keys 100–300 ms; the menus debounce.

**Menu path to the password screen.**

1. Title screen → `Start`.
2. Main menu → `Down` once (cursor on `RESUME GAME`) → `A`.
3. Password screen: 4 × 8 grid, cursor starts on `B` (top-left). D-pad moves,
   `A` appends the highlighted symbol, `B` deletes the last symbol (pressing `B`
   with an empty buffer returns to the main menu), `Start` submits.
4. On success the screen dims and the board intro appears.

**Codes tested (all on the `RESUME GAME` screen):**

| Code | Result |
|---|---|
| `71BDBBBBBC?BC?BC` | accepted → Katz's Creepy Castle |
| `31BDBBBBBC?BC?BC` | accepted → Planet Johnnywood |
| `V1BDBBBBBC?BC?BC` | accepted → The Tater Farm |
| `01BDBBBBBC?BC?BC` | accepted → Extreme Cul-De-Sac |
| `1N4DBDDBGH?JK?LM` | **accepted (novel)** → Extreme Cul-De-Sac, altered state |
| `6?Q9CN9DZC?9T?BW` | **accepted (novel)** → Planet Johnnywood, altered state |
| `Y?Q9B99B9??9??9?` | **accepted (novel)** → The Tater Farm, max fields |

## 4. Address map

ROM base `0x08000000`; file offset `f` ↔ ROM `0x08000000 + f`.

| Object | ROM address | File offset | Notes |
|---|---|---|---|
| Alphabet table | `0x08278094` | `0x278094` | `BCDFGHJKLMNPQRSTVWXYZ0123456789^` (NUL-padded) |
| `"PASSWORD: "` string | `0x082780B8` | `0x2780B8` | drawn by the password screen |
| Password screen draw | `0x0802A778` | `0x2A778` | also calls encoder + display |
| Password screen state machine | `0x0802A8D8` | `0x2A8D8` | reads input command `0x03002490+0x99` |
| **Encoder** (state → password) | `0x08029DC4` | `0x29DC4` | builds the 80-bit buffer |
| **Bit writer** | `0x080298D4` | `0x298D4` | `bitwrite(nbits, value)`, MSB-first |
| **Decoder / validator** | `0x08029FD8` | `0x29FD8` | 1254 bytes; validates and applies |
| Char-append handler | `0x08029934` | `0x29934` | writes `alphabet[row*8+col]`; calls decoder after 16 |
| Delete handler | `0x0802A4F4` | `0x2A4F4` | `B` key |
| Grid row/col handlers | `0x0802A544`/`0x2A580`/`0x2A5BC`/`0x2A5F8` | | row 0…3, col 0…7 |
| Display (maps `^`→`?`) | `0x08029A3C`, `0x0802A6CC` | | |
| Player-entry update blocks | `0x0800048C`, `0x4E8`, `0x54C`, `0x5B0` | | per-player, read `0x03002560` |

**RAM (all in EWRAM/IWRAM):**

| Address | Meaning |
|---|---|
| `0x030031A0` | password buffer, 16 bytes + NUL |
| `0x030012C0` | 80-bit pack buffer (10 bytes) |
| `0x030012CE` | bit position into the pack buffer |
| `0x030012D0` | pack buffer pointer (set to `0x030012C0`) |
| `0x03002560` | 4 player entries × 12 bytes (decoder output / encoder input) |
| `0x03002490` | game state; `+0x9C` = A, `+0xA2` = B, `+0xA8` = C |
| `0x0300252C` | **mode = board index A** (drives f6 limits and f4 shift) |
| `0x030012CA` | password buffer index (0…15) |
| `0x030012CC` | grid row (0…3) |
| `0x030012CB` | grid column (0…7) |

## 5. Algorithm

### 5.1 Bit packing

`bitwrite(n, v)` at `0x080298D4` writes `n` bits of `v`, MSB-first, into the byte
buffer at `0x030012C0`, starting at bit position `[0x030012CE]`. When the bit position
reaches a byte boundary the target byte is cleared first. The decoder reads bits with
the same MSB-first order.

### 5.2 Encoder (`0x08029DC4`)

```
local[0..3] = entry[i].byte0                       # 0x03002560 + i*12
# sorting network (in place, <= comparisons)
if local[2] <= local[3]: local[3] -= 1
if local[1] <= local[3]: local[3] -= 1
if local[0] <= local[3]: local[3] -= 1
if local[1] <= local[2]: local[2] -= 1
if local[0] <= local[2]: local[2] -= 1
if local[0] <= local[1]: local[1] -= 1
for i in 0..3:
    if local[i] > 5: local[i] = 0; entry[i].byte3 = 0x3F   # wildcard
mixed = local[1]*6 + local[0] + local[2]*30 + local[3]*120

bitwrite(1, 1)
bitwrite(2, A)          # 0x03002490+0x9C
bitwrite(2, B)          # 0x03002490+0xA2
bitwrite(1, C)          # 0x03002490+0xA8
bitwrite(1, entry[1].byte1)
bitwrite(1, entry[2].byte1)
bitwrite(1, entry[3].byte1)
bitwrite(9, mixed)
bitwrite(1, 1)
for i in 0..3:
    bitwrite(6, entry[i].byte3)
    bitwrite(5, entry[i].byte2 // 5)
    bitwrite(4, (entry[i].byte10_11 >> (4*mode)) & 0xF)
bitwrite(1, 1)
# pack 16 x 5 bits MSB-first into 0x030031A0, NUL at index 16
```

### 5.3 Decoder / validator (`0x08029FD8`)

```
if all 16 chars identical: return REJECT
zero bit buffer; bitpos = 0
for i in 0..15:  bitwrite(5, alphabet_index(char[i]))       # '?' -> index 31
bitpos = 0
if read(1) != 1: return REJECT
A = read(2); B = read(2); C = read(1)
b1[0..2] = read(1) x3
mixed = read(9)
if read(1) != 1: return REJECT
for i in 0..3:
    f6[i] = read(6); f5[i] = read(5); f4[i] = read(4)
if read(1) != 1: return REJECT

# mixed-radix decode + inverse sorting network
a = [mixed % 6, (mixed//6) % 5, (mixed//30) % 4, (mixed//120) % 3]
if a[2] <= a[3]: a[3] += 1
if a[1] <= a[3]: a[3] += 1
if a[0] <= a[3]: a[3] += 1
if a[1] <= a[2]: a[2] += 1
if a[0] <= a[2]: a[2] += 1
if a[0] <= a[1]: a[1] += 1

# range checks (mode = board index A)
for i in 0..3:
    if f6[i] > LIMIT[A] and f6[i] != 0x3F: return REJECT
    if f5[i] > 30: return REJECT
    entry[i].byte8   = f6[i]
    entry[i].byte2   = f5[i] * 5
    entry[i].byte10_11 = f4[i] << (4*mode)
    entry[i].byte1   = b1[i-1] (entries 1..3); entry[0].byte1 = 1

# wildcard suffix rule: a wildcard (byte0 = 7) may not precede a non-wildcard
for i in 0..3:
    if entry[i].byte8 == 0x3F: entry[i].byte0 = 7
    else:                       entry[i].byte0 = a[i]
for i in 3 down to 1:
    if entry[i].byte0 <= 5 and entry[i-1].byte0 > 5: return REJECT

game_state[0x9C] = A; game_state[0xA2] = B; game_state[0xA8] = C
return ACCEPT
```

`LIMIT = [48, 52, 44, 49]` for boards 0…3 (proven in-game, see §6b).

### 5.4 On-screen character mapping

`alphabet_index(c)`: `?` → 31, otherwise the index of `c` in
`BCDFGHJKLMNPQRSTVWXYZ0123456789^`. The display substitutes `?` for `^`.

## 6. Tables

### 6.1 Published tournament passwords (GameFAQs)

| Board | A | Published | Verified |
|---|---:|---|---|
| The Tater Farm | 0 | `V1BDBBBBBC?BC?BC` | accepted |
| Extreme Cul-De-Sac | 1 | `01BDCBBBC?BC?BC` **(15 chars)** | **rejected** (length) |
| Planet Johnnywood | 2 | `31BDBBBBBC?BC?BC` | accepted |
| Katz's Creepy Castle | 3 | `71BDBBBBBC?BC?BC` | accepted |

The published Extreme Cul-De-Sac code is one character short. Two 16-character
completions are accepted by the validator:

* `01BDBBBBBC?BC?BC` — pattern-consistent with the other three codes; decodes to
  `A=1,B=1,C=1,b1=[0,1,1],mixed=0,f6=[0,0,63,63],f5=[0,0,0,0],f4=[0,0,0,0]`.
  Loads Extreme Cul-De-Sac with the same "clean tournament" state as the others.
* `01BDCBBBC?BC?BC0` — the published string with `0` appended; decodes to a
  different player state (`f6=[1,0,32,32]`, `f5=[0,1,1,1]`, `f4=[0,15,15,10]`).
  Also loads Extreme Cul-De-Sac.

The first is the intended correction (the other three published codes all use the
`X1BDBBBBBC?BC?BC` pattern).

### 6.2 Field values of the verified codes

| Code | A | B | C | b1 | mixed | f6 | f5 | f4 |
|---|---:|---:|---:|---|---:|---|---|---|
| `V1BDBBBBBC?BC?BC` | 0 | 0 | 1 | [0,1,1] | 0 | [0,0,63,63] | [0,0,0,0] | [0,0,0,0] |
| `01BDBBBBBC?BC?BC` | 1 | 1 | 1 | [0,1,1] | 0 | [0,0,63,63] | [0,0,0,0] | [0,0,0,0] |
| `31BDBBBBBC?BC?BC` | 2 | 0 | 1 | [0,1,1] | 0 | [0,0,63,63] | [0,0,0,0] | [0,0,0,0] |
| `71BDBBBBBC?BC?BC` | 3 | 0 | 1 | [0,1,1] | 0 | [0,0,63,63] | [0,0,0,0] | [0,0,0,0] |
| `1N4DBDDBGH?JK?LM` | 1 | 2 | 0 | [1,0,1] | 200 | [0,0,63,63] | [2,4,6,8] | [1,2,3,4] |
| `6?Q9CN9DZC?9T?BW` | 2 | 3 | 1 | [1,1,1] | 359 | [1,2,63,63] | [10,20,30,0] | [15,0,7,8] |
| `Y?Q9B99B9??9??9?` | 0 | 3 | 1 | [1,1,1] | 359 | [0,0,63,63] | [30,30,30,30] | [15,15,15,15] |

### 6.3 Per-board 6-bit limits (observed)

| Board A | Name | f6 limit (hex) | boundary test |
|---:|---|---:|---|
| 0 | The Tater Farm | 48 (`0x30`) | 48 accepted, 49 rejected |
| 1 | Extreme Cul-De-Sac | 52 (`0x34`) | 52 accepted, 53 rejected |
| 2 | Planet Johnnywood | 44 (`0x2C`) | 44 accepted, 45 rejected |
| 3 | Katz's Creepy Castle | 49 (`0x31`) | 49 accepted, 50 rejected |

`0x3F` (63) is always accepted and is the **wildcard** (decoder sets player byte 0
to 7). Wildcards may only occupy a suffix of the four entries.

## 6b. Enumeration

**Space definition.** 16 symbols from a 32-symbol alphabet = `32^16 = 2^80 =
1,208,925,819,614,629,174,706,176` possible strings.

**Free bits.** 80 bits total; bits 0, 18 and 79 are fixed constants, leaving 77 free
bits (`2^77`).

**Validator model.** See §5.3. The accepted set is exactly:

* `A` ∈ {0,1,2,3} (4)
* `B` ∈ {0,1,2,3} (4)
* `C` ∈ {0,1} (2)
* `b1` ∈ {0,1}³ (8)
* `mixed` ∈ {0…511} (512 encodings, **360 distinct** — `mixed ≡ mixed mod 360`)
* `f6` — 4 values, each `0…LIMIT[A]` or the wildcard `0x3F`, with all wildcards in a
  suffix: `F(A) = Σ_{k=0..4} (LIMIT[A]+1)^(4-k)`
* `f5` — 4 values, each `0…30` (31⁴)
* `f4` — 4 values, each `0…15` (16⁴)

**Exact counts.**

| Board | LIMIT | F(A) | Valid passwords | Distinct states |
|---:|---:|---:|---:|---:|
| 0 | 48 | 5,884,901 | 11,671,207,816,829,555,703,808 | 8,206,317,996,208,281,354,240 |
| 1 | 52 | 8,042,221 | 15,949,704,608,432,802,234,368 | 11,214,636,052,804,314,071,040 |
| 2 | 44 | 4,193,821 | 8,317,379,755,000,796,807,168 | 5,848,157,640,234,935,255,040 |
| 3 | 49 | 6,377,551 | 12,648,254,079,963,137,835,008 | 8,893,303,649,974,081,290,240 |
| **Total** | | | **48,586,546,260,226,292,580,352** | **34,162,415,339,221,611,970,560** |

Total valid ≈ `2^75.45`; distinct states ≈ `2^74.87`; **4.019 %** of the 16-symbol
space is accepted.

**Novel codes (not in any published list).** GameFAQs, Wikipedia, StrategyWiki and
Cheat Happens list only the four tournament passwords (and codes for the *Cartoon
Network Speedway* companion game, which do not apply to this SKU). The following were
generated from the reversed format, are absent from every published list, and were
**entered and accepted on the real password screen**:

| Novel code | Board | Fields exercised | In-game proof |
|---|---|---|---|
| `1N4DBDDBGH?JK?LM` | Extreme Cul-De-Sac | B=2, C=0, b1=[1,0,1], mixed=200, f5=[2,4,6,8], f4=[1,2,3,4] | board intro shown; pause menu re-displays the same code |
| `6?Q9CN9DZC?9T?BW` | Planet Johnnywood | B=3, b1=[1,1,1], mixed=359, f6=[1,2,63,63], f5=[10,20,30,0], f4=[15,0,7,8] | board intro shown |
| `Y?Q9B99B9??9??9?` | The Tater Farm | B=3, mixed=359, f5=[30,30,30,30], f4=[15,15,15,15] (all maxima) | board intro shown |

The pause-menu `PASSWORD:` line re-displays the entered code for `1N4DBDDBGH?JK?LM`,
which proves the game applied those exact field values and re-encoded them.

**Alias proof.** `Z2RDBBBBBC?BC?BC` (mixed = 360) is accepted, and the pause menu
re-displays it as `Z1BDBBBBBC?BC?BC` (mixed = 0). The 9-bit mixed field therefore has
360 distinct values; 152 of the 512 encodings are aliases.

**Bounds proven by rejection (all entered in-game on the password screen).**

| Test | Code | Result |
|---|---|---|
| constant bit 0 flipped | `Q1BDBBBBBC?BC?BC` | rejected (screen unchanged) |
| constant bit 18 flipped | `71BBBBBBBC?BC?BC` | rejected |
| constant bit 79 flipped | `71BDBBBBBC?BC?BB` | rejected |
| all 16 chars identical | `BBBBBBBBBBBBBBBB` | rejected |
| f6 out of range (board 3, 50 > 49) | `71BFXBBBBC?BC?BC` | rejected |
| f5 out of range (31 > 30) | `71BDB?BBBC?BC?BC` | rejected |
| length 15 (published typo) | `01BDCBBBC?BC?BC` | rejected |
| length 17 | `71BDBBBBBC?BC?BCB` | rejected |
| board-0 f6 boundary | `V1BFVBBBBC?BC?BC` (48) / `V1BFWBBBBC?BC?BC` (49) | accepted / rejected |
| board-1 f6 boundary | `Z1BFZBBBBC?BC?BC` (52) / `Z1BF0BBBBC?BC?BC` (53) | accepted / rejected |
| board-2 f6 boundary | `31BFQBBBBC?BC?BC` (44) / `31BFRBBBBC?BC?BC` (45) | accepted / rejected |
| board-3 f6 boundary | `71BFWBBBBC?BC?BC` (49) / `71BFXBBBBC?BC?BC` (50) | accepted / rejected |
| f5 boundary | `Z1BDB9BBBC?BC?BC` (30) | accepted |
| f4 boundary | `Z1BDBB9BBC?BC?BC` (15) | accepted |

## 7. Validation evidence

**Observed (emulator, mGBA 0.10.5).**

* **Menu walk.** Title (`PRESS START`; only Start advances — L/R/Select/A/B/d-pad
  combos all left the title unchanged) → main menu (`NEW GAME`, `RESUME GAME`,
  `OPTIONS`, `GAME ROOM`, `CREDITS`) → `RESUME GAME` → password grid (32 symbols,
  `^` drawn as `?`).
* **OPTIONS:** `SFX VOL`, `SONG VOL`, `SFX TEST`, `SONG TEST` (no cheat entry).
* **GAME ROOM:** 14 minigames, wrapping — `GREASED PORKBUTTS`, `AIM FOR THE FENCES`,
  `H2 UH OH`, `STRIKE A POSE`, `ZOMBEAT THE CLOCK`, `BACKYARD BOOGIE`, `FISH FRENZY`,
  `GRAND PRIX`, `SKATIN' THE U`, `HIDE N' SEEK`, `WEREMOLE WALTZ`, `FREAKY FIREPLACE`,
  `SNATCH-A-BAT`, `COLD CASH WORKOUT`.
* **CREDITS:** standard Majesco Sales credits (no cheat entry).
* **NEW GAME:** `SELECT PLAYER` (roster: `COURAGE`, `EDDY`, `SARAH`, `COW`, `CHICKEN`,
  `JOHNNY BRAVO`, `COMPUTER PLAYER`) → `MODE SELECT` (`QUICK PLAY` / `TOURNAMENT`) →
  board intro (`QUICK PLAY` started The Tater Farm).
* **Pause menu:** `RESUME GAME`, `OPTIONS`, `EXIT GAME`, plus a `PASSWORD:` line that
  re-displays the current tournament password.
* No debug/cheat strings exist in the image (`DEBUG`, `CHEAT`, `SECRET`, `UNLOCK`,
  `HACK` are absent; the only `TEST` hit is `LEAD TESTERS` in the credits). No
  button-mask code table was found near the title screen or input handler.
* All four published codes were entered; three loaded the boards named on GameFAQs,
  the 15-character fourth did nothing.
* The corrected Extreme code and three novel codes were accepted and produced the
  board intro for the selected board.
* The pause menu re-displayed the entered novel code, and re-displayed mixed=360 as
  mixed=0 (alias).
* Every rejection in §6b left the password screen unchanged.

**Derived (disassembly).**

* Alphabet table at `0x08278094`; `^`→`?` display rewrite at `0x08029A3C`/`0x0802A6CC`.
* Encoder `0x08029DC4` and bit writer `0x080298D4` produce exactly the 80-bit layout.
* Decoder `0x08029FD8` checks the three constant bits, the per-board f6 limits, the
  f5 ≤ 30 rule, and the wildcard-suffix rule.
* The mode used by the decoder equals the board index A (proven by the f6 boundary
  tests, which only pass when the limit matches A).
* The 14-entry `GAME ROOM` list, the options screen and the credits screen contain no
  cheat entry point; the title screen responds only to Start.

**Inferred (not fully exercised).**

* The exact gameplay meaning of B, C, b1, f6, f5, f4. A is the board index with high
  confidence (four values → four boards, observed). f5 is a 0…150 value in steps of 5
  and f6 is a per-board count with board-dependent maxima; both are stored per player.
  The mixed field is a combinatorial encoding of four 0…7 player values.

## 8. Unknowns

* The precise semantics of B, C and b1 (they change the resulting board state, but no
  labelled effect was isolated).
* The precise semantics of f6/f5/f4 (player state fields; the board HUD did not
  change in the limited tests performed).
* Where the mode byte `0x0300252C` is written (it equals A at decode time; the writer
  was not located).
* Whether the mixed-field aliases (152 values) are reachable through the on-screen
  keyboard in combination with the other fields — they are reachable in principle
  because the decoder accepts them.

## 9. Tooling

* `mgba-sdl` 0.10.5 (`/usr/games/mgba`), `Xvfb`, `xdotool`, `scrot`, ImageMagick.
* `arm-none-eabi-objdump` (`-M force-thumb`) for raw Thumb disassembly.
* `gdb-multiarch` against mGBA's `-g` stub (used for memory inspection; ROM
  breakpoints did not fire reliably, so static disassembly was used for the
  validator).
* Python 3 for the codec, pointer/BL scans, and enumeration.
* Analysis scripts and screenshots: `/tmp/opencode/cnblockparty/`
  (`pwcodec.py` = reference decoder/encoder, `enumerate.py` = space counts,
  `harness2.py` = savestate-driven in-game tests, `phase0.py`, `recon_strings.py`,
  `blscan.py`, `ramscan.py`, `debugscan.py`).

## Legal note

No ROM, asset, or copyrighted graphic is redistributed by this report. Addresses,
algorithms, hashes, the password format, and independently generated codes are
published; screenshots were taken only as local analysis evidence.
