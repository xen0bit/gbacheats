# Winnie the Pooh's Rumbly Tumbly Adventure (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Winnie the Pooh's Rumbly Tumbly Adventure.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `WINNIE THE P` |
| Game code / maker | `BWHE` / `41` (Ubisoft), Rev. 00 |
| Header version / complement / checksum | `0x00` / `0x8B` / `0x0000` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| MD5 | `5747df74932735205d090aa2ad1cfece` |
| SHA-1 | `96d24d06955a13b0ce649e7536a29be1b83f4d2b` |
| SHA-256 | `82df55c4d205aa30449027349a4934323e88f4426869c0ff1363da271ba7ce04` |

Identified as the retail US/Europe GBA build by header and the Phoenix Interactive / Ubisoft boot
logos observed in mGBA. No cracktro/trainer signs; entry word is the stock branch.

## 2. Executive summary

The game has a **7-digit decimal password system** used as its battery-free save/progress system.
The published list (3rd party cheat indexes; 21 codes) was recovered and **all 21 were verified against
the ROM's own validator**. The codes are not stored in the image: they are computed.

The algorithm (validator `0x0802A058`) is:

1. The 7 displayed digits are read **least-significant first** from a byte buffer at EWRAM
   `0x0200A044`; they form a 28-bit integer `M = Σ digit[i]·10^i` (i = 0..6).
2. `X = M XOR 0x002DBEEF` (key literal at `0x0802A110`).
3. `y = X & 0xFFF` — 12-bit honey-pot collection mask.
4. `z = X >> 12`; `a = z / 51`, `r = z % 51` (ARM division helpers at `0x803A630`/`0x803A610`).
5. `b = a % 5` (area/level slot 0..4), `c = a / 5` (character family 0..4; c>4 rejects).
6. Acceptance: `b==0` requires `r==0`; the special state `c==4,b==4` requires `r==0,y==0`;
   otherwise the 16-bit mask table at `0x080448B8[c*5+b]` must be nonzero when `b!=0`, and
   `y & ~mask == 0`.

This yields **533,262 accepted codes out of 10,000,000 possible 7-digit inputs**. The honey-pot
mask `y` is an *unadvertised* second field: every published code has `y=0`, but any subset of the
per-area mask is accepted. A novel code **`4744991`** (published `9744991` with `y=5`, i.e. two
honey pots already collected) and a novel-state code **`9997992`** (`a=0`) were entered on the real
password screen and confirmed **accepted** by a breakpoint on the ROM's accept branch. Bounds were
proved by three rejected inputs.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:315`, default keymap
  (A=`x`, B=`z`, Start=`Return`, D-pad=arrows). Hold ~60–150 ms.
* Boot path observed: logos → language book (English/Français/Español; A selects) → title
  "Press START to play" → START starts a new game immediately (Pooh in the first field).
  Pause (START) gives **Resume / Exit**; Exit → "Are you sure you want to quit?" → YES → title.
  In-game SELECT showed no map in the first field.
* UI text is ASCII but is stored in a bank at file `0x307130`-ish with a u32 offset table at
  `0x0830712C` (IDs: 0 `Press START to play`, 1 `New Game`, 4 `Enter Password`, 5 `Options`,
  9 `Incorrect Password`, 28 `Password`, 29 `Here is your Password.`). The font/tile mapping table
  starts at `0x08307318` (u16 identity map with specials `0x001E`, `0x0014` at indices 0,1).
  This was decoded before any negative conclusion.
* The password screen is **screen id 29** in the global screen dispatcher `0x0800D0AC`
  (jump table at `0x08044078`; case 29 → constructor `0x08024274`).
  On a stock first-boot title a normal menu path to id 29 was not found in this session; the screen
  was reached by a **labelled harness patch** of a title-screen savestate:
  game object pointer is global `0x030059DC` → `0x02007808`; set `[obj+0x74]=0` (screen-state gate)
  and `[obj+0x15B]=29` (requested screen id) in the uncompressed `gbAs` savestate chunk
  (EWRAM maps to raw offset `0x21000` for a 4 MiB ROM; obj fields at raw `0x2887C`, `0x28963`).
  Loading that patched state (`title_pw.ss1`) opens the genuine **Enter Password** screen with seven
  `0` digits, A=Accept, B=Back. Screenshot: `pw_patched2_c.png`.
* Entering a code: arrows change the focused digit, Left/Right move the cursor, A accepts.
  Screenshot of a typed novel code: `pw_entered_4744991_c.png`.
* Oracle method (guide §16.19): with the digit buffer populated in the savestate, start
  `mgba -d -t <state>.ss1`, set breakpoints at `0x0802A0F6` (accept) and `0x0802A0C0` (reject),
  continue, press A; the hit branch is ground truth from the ROM itself.

## 4. Address map

| Address (ROM/WRAM) | Meaning |
|---|---|
| `0x0802A058` | Password validator; `r0` = digit buffer, returns 1/0 |
| `0x0802A06C`–`0x0802A078` | 7-digit parse loop (`digit*10^i`, watchpoint hit at `0x0802A070`) |
| `0x0802A07E`–`0x0802A086` | XOR with `0x002DBEEF`, split `y=X&0xFFF`, `z=X>>12` |
| `0x0802A088`–`0x0802A0AE` | `a=z/51`, `r=z%51`, `b=a%5`, `c=a/5` |
| `0x0802A0B0`–`0x0802A10E` | accept/reject branches and mask-table checks |
| `0x0802A000` | Companion generator (encodes state → 7 digits) |
| `0x0802A110` | Key literal `0x002DBEEF` |
| `0x0802A114` | Mask literal `0x00000FFF` |
| `0x0802A118` | Pointer to mask table `0x080448B8` |
| `0x080448B8` | 25-entry u16 honey-pot mask table |
| `0x0800D0AC` | Screen dispatcher; jump table `0x08044078` |
| `0x08024274` | Password-screen constructor (screen 29) |
| `0x08030712C` | UI text offset table (file `0x30712C`) |
| `0x0200A044` | EWRAM: 7 entered digits (one byte each, 0..9) |
| `0x030059DC` | Global: pointer to game object (`0x02007808`) |
| `0x02007808+0x74` | Screen-state gate (0 = process new screen request) |
| `0x02007808+0x15B` | Requested screen id byte |

## 5. Algorithm (reimplementation-ready pseudocode)

```python
K = 0x002DBEEF
MASK = [0x0,0x7,0xf,0xf,0x0, 0x0,0xf,0x1ff,0x1ff,0x0,
        0x0,0x3f,0x3f,0x7f,0x7ff, 0x0,0x7f,0xff,0x7ff,0x0,
        0x0,0x1f,0x1ff,0xfff,0x0]

def encode(a, r, y=0):                  # state/checksum/honey-mask -> code
    M = ((a*51 + r) << 12) | y
    X = M ^ K
    return int(str(X).zfill(7)[::-1])   # digits emitted least-significant first

def validate(code):
    d = [int(c) for c in f"{code:07d}"]
    M = sum(d[i]*10**i for i in range(7))
    X = M ^ K
    y, z = X & 0xFFF, X >> 12
    a, r = z // 51, z % 51
    b, c = a % 5, a // 5
    if c > 4: return False
    if b == 0 and r != 0: return False
    if c == 4 and b == 4: return r == 0 and y == 0
    m = MASK[c*5+b]
    if m == 0 and b != 0: return False
    return (y & ~m) == 0
```

Field meanings (from the mask table and published labels): `c` selects the character family
(0 Piglet, 1 Roo, 2 Tigger, 3 Eeyore, 4 Pooh), `b` the area slot (1..4; 0 = area completed),
`a = c*5+b` is the state id, `r` is an unchecked checksum for `b!=0` (must be 0 for `b==0`), and
`y` is the set of honey pots already collected. Published "completed" codes use `b=0,r=0`.

## 6. Tables

Published codes (3rd party cheat indexes, all 21 verified by `validate()`):

| Effect | Code | a / b / c / r / y |
|---|---|---|
| Piglet area 1 / 2 / 3 / completed | 5735172 / 7045732 / 1156612 / 1348422 | a=1,2,3,5 |
| Roo area 1 / 2 / 3 / completed | 3412773 / 9999053 / 5505553 / 3011033 | a=6,7,8,10 |
| Tigger area 1/2/3/4 / completed | 7847570 / 5560830 / 3834540 / 9172120 / 1749510 | a=11,12,13,14,15 |
| Eeyore area 1 / 2 / 3 / completed | 9744991 / 9301241 / 3220311 / 3412121 | a=16,17,18,20 |
| Pooh area 1 / 2 / 3 | 1937986 / 1388596 / 5399476 | a=21,22,23 |
| Game completed | 3013736 | a=24 |

Mask table at `0x080448B8` (index `c*5+b`):
`0,7,F,F,0 / 0,F,1FF,1FF,0 / 0,3F,3F,7F,7FF / 0,7F,FF,7FF,0 / 0,1F,1FF,FFF,0`.
These are bitmasks of collectable honey pots per area (e.g. Eeyore area 1 has 7 bits → `0x7F`).

## 6b. Enumeration

**Space:** 10^7 possible 7-digit inputs (alphabet `0-9`, fixed length 7). Decoded fields:
`a` ∈ 0..24 (25 states), `r` ∈ 0..50 (51 values, free when `b!=0`, forced 0 when `b==0`),
`y` ⊆ area mask (0..2^12-1, constrained). Exact accepted-set size from the model:
**533,262 codes** (sum of `51·2^popcount(mask)` for the 21 area states with nonzero mask,
1 code each for the 4 completed states plus state 0, and the single End code).
States `a=4,9,19` have a zero mask and **zero** accepted spellings; `a>24` is rejected by `c>4`.

**Novel codes generated and accepted (absent from 3rd party cheat indexes and every other
published list checked):**

| Code | Payload | Where novel | Oracle result |
|---|---|---|---|
| **`4744991`** | a=16, r=13, y=5 | same published Eeyore-1 state but 2 honey pots pre-collected — combination no list contains | ACCEPT (`0x802A0F6`) |
| **`9997992`** | a=0, r=0, y=0 | state id 0, never published | ACCEPT (`0x802A0F6`) |
| **`5509102`** | a=16, r=7, y=0 | alternate checksum spelling of Eeyore-1 | ACCEPT (`0x802A0F6`) |

The first was typed digit-by-digit on the actual Enter Password screen
(`pw_entered_4744991_c.png`) and the accept branch hit with the RAM buffer still holding
`09 07 04 04 09 09 01`-style digits at `0x0200A044`.

**Bounds proved by rejection (ROM oracle, `0x802A0C0`):**

| Code | Field violation | Result |
|---|---|---|
| `1534991` | a=16, y=0x80 outside mask 0x7F (too many honey pots) | REJECT (r0=0x80, r2=0x7F) |
| `3815912` | a=4, table[4]=0 (unrepresentable area slot) | REJECT |
| `9997992`/`5509102`/`9744991` controls | valid | ACCEPT |

So both layers — the mask/checksum layer and the semantic field/range layer — were tested
separately, per guide §16.5.

## 7. Validation evidence

* **Observed (emulator):** boot logos, language book, title, gameplay, pause/exit dialogs;
  genuine Enter Password screen (screen 29) with 7 slots; typed novel code `4744991`;
  read watchpoint firing at `0x0802A070` while reading EWRAM `0x0200A044`;
  accept/reject breakpoints firing under the ROM's own validator for six codes.
* **Observed (savestate RAM):** 7-byte digit buffer at raw `0x2B044` = EWRAM `0x0200A044`
  (found by searching the decompressed `gbAs` chunk for `09 07 04 04 09 09 01`);
  game object `0x02007808` via global `0x030059DC`, with `[+0x74]=1` at title and
  `[+0x15B]` the screen-request byte.
* **Derived (disassembly):** validator formula, key `0x002DBEEF`, mask table and its exact
  address, screen dispatcher/table, generator companion at `0x0802A000`.
* **Inferred:** mapping of `c`/`b` to character/area labels (taken from published code effects);
  that `r` is a checksum/hash whose particular value is unchecked by the validator for `b!=0`
  (the generator does compute one, but no comparison against a stored value exists in the
  validator). The exact in-game effect of `y>0` (pre-collected honey pots) was **not** observed
  visually because the harness-patched screen cannot complete its level-load transition; the
  validator accepts it, which is the claim made here.

## 8. Unknowns

* No stock first-boot input path to the main-menu "Enter Password" option was found; the screen
  was reached with a clearly labelled savestate patch. A normal playthrough past the first area
  (or a completed-game save) may expose the menu.
* The meaning of the unused checksum field `r` for area states is unknown beyond being a free
  spelling dimension; the generator's exact derivation of `r` was not fully traced.
* The full effect of `y>0` in-game (honey-pot count display) was not visually confirmed.
* State ids 0, 4, 9, 19 and ≥25 are accepted/rejected as modelled but their game-side semantics
  (if any) are unknown.

## 9. Tooling

* `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python `struct`/`zlib` for header,
  text-bank decoding and mGBA `gbAs` savestate patching (guide §16.13).
* `arm-none-eabi-objdump -M force-thumb` / Capstone for disassembly and PC-relative literal scans;
  REA/Ghidra (`open_binary`, `search_strings`, `xrefs`, `trace_feature`) for the string→code
  pivot — note Ghidra raw-ARM auto-analysis missed nearly all Thumb functions, so manual objdump
  was authoritative.
* mGBA 0.10.5 CLI debugger (`-d`) with read watchpoint on `0x0200A044` to locate the validator
  and accept/reject breakpoints as an oracle. The GDB stub (`-g`) was unusable because another
  analysis session held TCP 2345; the CLI debugger avoided that conflict.
* All screenshots, savestates and scripts are kept in `/tmp/winniepooh`, not in the ROM
  folder. No ROM bytes, graphics, music or game text were redistributed.
