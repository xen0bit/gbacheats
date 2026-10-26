# Army Men Advance (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-25.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Army Men Advance/Army Men Advance.gba` |
| Size | 4 MiB (`0x400000`) |
| Header title | `ARMY MEN ADV` |
| Game code | `ASAE` |
| Maker code | `5H` |
| Software version | `0` |
| Entry word | `0xEA00002E` (ARM branch to `0x080000C0`) |
| Complement check | `0x86` (computed value also `0x86`) |
| Header checksum field | `0x0000` (as stored; the file's complement check is valid) |
| MD5 | `30ff69a44658fcf2cc381736403e74ef` |
| SHA-1 | `43cd22c8e5832790b0cdbdcf0e11859021747342` |
| SHA-256 | `d49331d145b3a191b2844a06e803d3894804f7541a9d623a039b1e4ea84dac97` |

Embedded-header scan: the 156-byte Nintendo logo occurs **once**, at file
offset `0x4`; this is a single GBA image, not a multi-game cart.

`mGBA` created a 0-byte `Army Men Advance.sav` during play and it remained
empty; the game exposes no `CONTINUE` option. Progress is carried by the
password, not by battery-backed save data.

ROM addresses below are `0x08000000 + file_offset`.

---

## 2. Executive summary

*Army Men Advance* has a single, **algorithmic** level-password system.

The screen offers an eight-character code. The entry device is a ring of
**22 symbols**:

```
B C D F G H J K L M N P Q R S T V W X Y Z !
```

There is no plaintext table of accepted password strings anywhere in the ROM:
all 31 distinct literals recovered from public lists (`NQRDGTPB`, `HJRDCHMC`,
`FSSSMHMB`, …) are absent from the 4 MiB image. The validator is arithmetic:

1. Each symbol is converted to a 5-bit index (B=0 … Z=20, `!`=21).
2. Each index is XORed with an eight-byte key (`07 02 03 09 0A 0B 08 0E`).
3. The low nibbles of the resulting bytes are checked:
   `v0 == (45 − v2 − v5 − v7) mod 16`.
4. On success the game decodes:
   * `level = 16 − v5` (1–12 in retail content),
   * `character = 15 − v7` (0 = Sarge, 1 = Vicki).
5. `v0` is the 4-bit check nibble; `v1`, `v2`, `v3`, `v4`, `v6` are free filler
   (`v2` feeds the check, but can be chosen freely).

Consequences proved in the emulator:

* A public code (`NQRDGTPB`, Vicki level 12) is accepted and opens
  `SELECT LEVEL` with all twelve levels available.
* A **new** code, `HJRDCGMB`, decodes to **Vicki level 1** — a state absent
  from every published list (published Vicki codes start at level 2). It was
  accepted and played: the female sprite appears in “Tan Army Jail”.
* The filler is genuinely free: `NDRMNTLB`, `NFRMNTLB`, `MDSMNTLB` and
  `N!RMNTLB` all decode to the same Vicki level-12 state and are all accepted.
  `N!RMNTLB` also proves `!` is a real, enterable symbol.
* A checksum-broken code (`NQRDGTPC`) shows **INVALID**; a level-16 Vicki code
  (`MDRMNPLB`) is also rejected because the required check nibble (17) cannot
  be represented.
* Level 13 is *representable and accepted*, but there is no level-13 content:
  the selector draws its cursor below “LEVEL 12”, and starting it produces an
  out-of-bounds briefing (German text from the wrong bank). The content bound
  is 12; the format itself can express levels beyond 12 (§6b).

The published lists are therefore shortcuts, and two different published code
families can describe the same state. The space is large:
`22^8 = 54,875,873,536` strings, of which `3,435,129,984` pass the checksum.
The 24 real `(level, character)` states account for `513,489,152` of those,
i.e. each real state has between 13.1 and 30.0 million valid spellings.

---

## 3. How to reproduce

### Emulator

```bash
Xvfb :141 -screen 0 1024x768x24 &
DISPLAY=:141 openbox &
DISPLAY=:141 SDL_AUDIODRIVER=dummy mgba -3 "Army Men Advance.gba" &
```

`mGBA` SDL default keymap (verified on the title menu and password ring):

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

mGBA savestates: `Shift+F1` saves slot 1, `F1` loads it. A title-menu state was
used throughout so each test began at the menu rather than the 3DO logo.

### Menu path (observed)

First boot goes:

```
3DO logo
└─ SELECT LANGUAGE (ENGLISH)
   └─ intro text (A/Start advances)
      └─ SELECT character (Sarge / Vicki)
         └─ MISSION BRIEFING → objectives → gameplay
```

The **title menu** with `NEW GAME / PASSWORD / OPTIONS` appears after quitting a
game:

```
gameplay → Start (pause) → DOWN → QUIT GAME → A
   └─ title menu
      ├─ NEW GAME
      ├─ PASSWORD   ← target
      └─ OPTIONS → SOUND (ON/OFF), DIFFICULTY (EASY/MEDIUM/HARD), CREDITS
```

Password entry:

* left/right rotates the 22-symbol ring one position per discrete tap;
* A appends the symbol under the fixed crosshair to the bottom-left buffer;
* B deletes the last symbol; B on an empty buffer exits to the title menu;
* after eight symbols, A validates. Valid → `SELECT LEVEL`; invalid →
  `INVALID` and the code disappears.

**Input-timing pitfall:** holding a direction repeats the rotation and produces
non-deterministic positions. Reliable entry uses a ~20 ms key-down followed by
a ≥0.5 s settle; the ring index can be read from RAM between presses (see §4).
A 2–3 minute code entry is normal with this timing.

### Codes exercised (observed in mGBA)

| Input | Decoded fields (reconstructed) | Observed result | Screenshot |
|---|---|---|---|
| `NQRDGTPB` | level 12, Vicki | `SELECT LEVEL`; all levels 1–12 reachable | `Army Men Advance - public code NQRDGTPB entered.png`, `Army Men Advance - all levels unlocked.png` |
| `QGQNRTPC` | level 12, Sarge | `SELECT LEVEL`, level 12 selected | — |
| `FSSSMHMB` | level 2, Vicki | `SELECT LEVEL`, level 2 (Training Camp); 3/4 dimmed | `Army Men Advance - published alt code FSSSMHMB level 2.png` |
| `HJRDCGMB` | level 1, Vicki | `SELECT LEVEL`, level 1; played level 1 as Vicki | `Army Men Advance - novel code HJRDCGMB level 1.png`, `... Vicki gameplay.png` |
| `NDRMNTLB` | level 12, Vicki (all filler 0) | `SELECT LEVEL`, level 12 | — |
| `NFRMNTLB` | level 12, Vicki (v1=1) | `SELECT LEVEL`, level 12 | — |
| `MDSMNTLB` | level 12, Vicki (v2=13) | `SELECT LEVEL`, level 12 | — |
| `N!RMNTLB` | level 12, Vicki (`!` filler) | `SELECT LEVEL`, level 12 | `Army Men Advance - novel code N!RMNTLB.png` |
| `NQRDGTPC` | checksum broken | `INVALID` | `Army Men Advance - bad checksum INVALID.png` |
| `MDRMNPLB` | level 16, Vicki (unrepresentable check) | `INVALID` | — |
| `NQRDGLPC` | level 13, Sarge | selector cursor below level 12; starting it gives an out-of-bounds German briefing | `Army Men Advance - level 13 out of range.png` |
| `MQRDGTPF` | level 12, character code 2 | accepted; level 12 selected (no third character) | — |

---

## 4. Address map

### ROM

| File offset | ROM address | What |
|---:|---:|---|
| `0x2B3F5` | `0x0802B3F5` | `PASSWORD#` (English title-menu string) |
| `0x2B60B` | `0x0802B60B` | `DELETE#` |
| `0x2B621` | `0x0802B621` | `ENTER PASSWORD#` |
| `0x2B631` | `0x0802B631` | `BACK#` |
| `0x2B655` | `0x0802B655` | `    INVALID    #` |
| `0x2BE0D` | `0x0802BE0D` | `SELECT LEVEL#`, level-name bank |
| `0x2BE4E` | `0x0802BE4E` | level names 1–12 (`TAN ARMY JAIL` … `AREA 41-RETURN`) |
| `0x30719` | `0x08030719` | `BCDFGHJKLMNPQRSTVWXYZ!#\0` (23-symbol string) |
| `0x3071A` | `0x0803071A` | alphabet literal loaded by the checksum block (starts `C`; see §8) |
| `0x3BCF5C` | `0x083BCF5C` | eight-byte XOR key `07 02 03 09 0A 0B 08 0E` |
| `0x06A6C` | `0x08006A6C` | password checksum block (symbol loop + nibble packing) |
| `0x06B0E` | `0x08006B0E` | check comparison: `(r3 & 0xF) == (45 − v2 − v5 − v7)` |
| `0x06B14` | `0x08006B14` | successful result: stores `15 − v5` (level−1) at `[sp,#44]` |
| `0x06CEC` | `0x08006CEC` | commit eight input chars to `0x02020888`, append `#` |
| `0x06D18` | `0x08006D18` | set up the 22 ring sprites |
| `0x2B78A` | `0x0802B78A` | mission briefings (English bank; useful for the out-of-range check) |

### RAM (observed from mGBA savestates)

| Address | Use |
|---|---|
| `0x02020888` | eight-character entry buffer; `#` written at `+8` (`0x02020890`) |
| `0x020208AC` | ring selection index, observed 0–21; one discrete Right/Left tap changes it by ±1 |
| `0x02020844` | entry length/cursor-related byte (2→3 while testing; not fully named) |
| `0x03000E5C` | screen/menu state byte referenced by the password handler |
| `0x03001060` | key-input word read by the handler (`ldrh`) |
| `0x03001074` | pointer used while drawing the ring text |

The buffer at `0x02020888` was confirmed by entering a code, saving a state and
searching the decompressed EWRAM for the exact eight characters followed by
`#`.

---

## 5. Algorithm

### 5.1 Symbol values and key

```
ALPHABET = "BCDFGHJKLMNPQRSTVWXYZ!"      # 22 enterable symbols
KEY      = [0x07,0x02,0x03,0x09,0x0A,0x0B,0x08,0x0E]
v[i]     = ALPHABET.index(code[i]) XOR KEY[i]     # i = 0..7
```

The entry wheel offers 22 symbol positions in this order (the 22nd, `!`, is
drawn as a narrow bar and is easy to miss). The ROM string at `0x08030719` also
contains `#` as a 23rd byte; it is the terminator/pad and is not reachable from
the wheel (the wheel index wraps 21 → 0).

### 5.2 Checksum

The checksum block at `0x08006A6C` packs the eight nibbles into a 32-bit word
`v7<<28 | v6<<24 | v5<<20 | v4<<16 | v3<<12 | v2<<8 | v1<<4 | v0` and then
computes:

```c
uint8_t check = (45 - (v[2] & 15) - (v[5] & 15) - (v[7] & 15)) & 15;
if ((v[0] & 15) != check) return 0xFF;      /* rejected */
return 15 - (v[5] & 15);                    /* accepted: level - 1 */
```

The constant 45 is `15+15+15`; the assembly literally computes
`(15−v7) + (15−v5) + (15−v2)` and compares it with `v0`.

The dead-looking sequence at `0x08006AFC`–`0x08006B0C`
(`0x4D2 * sum | 0x1234`, shifted left 16) can never produce zero, so that
branch is an obfuscated no-op; the real comparison is the following
`ands r3,r6` / `cmp r3,r2` at `0x08006B0E`.

### 5.3 Field decode

After a successful check:

```
level     = 16 - (v[5] & 15)       # 1..12 real content
character = 15 - (v[7] & 15)       # 0 = Sarge, 1 = Vicki
```

`v[1]`, `v[2]`, `v[3]`, `v[4]`, `v[6]` are unrestricted filler. `v[0]` is the
check nibble and is recomputed.

### 5.4 Encoder

```python
def encode(level, character, v1=0, v2=14, v3=0, v4=0, v6=0):
    v5 = (16 - level) & 15
    v7 = (15 - character) & 15
    v0 = 45 - v2 - v5 - v7
    if not 0 <= v0 <= 15:
        return None                 # unrepresentable (e.g. level 16 Vicki)
    v = [v0, v1, v2, v3, v4, v5, v6, v7]
    return "".join(ALPHABET[(v[i] ^ KEY[i])] for i in range(8))
```

`v2 = 14` is the convention used by almost every published code; when `v2 = 14`,
`v0 = level + character`, which is why those codes have the third character `R`
(`v2 = 14 → index 13 = 'R'`). The published “all levels for Sarge” code
`QGQNRTPC` is the exception (`v2 = 15`, third character `Q`), and our
`MDSMNTLB` uses `v2 = 13` (third character `S`). `v2` is not checked on its own.

### 5.5 Worked examples

`NQRDGTPB`:

```
indices  N=10 Q=12 R=13 D=2 G=4 T=15 P=11 B=0
v        13   14   14   11 14  4     3    14
check    45 - 14 - 4 - 14 = 13 = v0     → accept
level    16 - 4  = 12
char     15 - 14 = 1 (Vicki)
```

`NQRDGTPC` (last symbol `B`→`C`):

```
v7 = 1 XOR 14 = 15; v0 = 13
45 - 14 - 4 - 15 = 12 ≠ 13               → INVALID (observed)
```

---

## 6. Tables

### 6.1 XOR key (`0x083BCF5C`)

| i | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| key | `07` | `02` | `03` | `09` | `0A` | `0B` | `08` | `0E` |

### 6.2 Alphabet

```
index  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21
char   B  C  D  F  G  H  J  K  L  M  N  P  Q  R  S  T  V  W  X  Y  Z  !
```

The vowels A/E/I/O/U are omitted (21 consonants); `!` is the 22nd symbol.
`#` is present in the ROM string as index 22 but is not selectable.

### 6.3 Published codes, decoded

Primary list (GameFAQs / CheatCC / RetroMaggedon). All 23 unique codes pass the
reconstructed checksum.

| Code | Level | Character | Notes |
|---|---:|---|---|
| `HJRDCHMC` | 2 | Sarge | |
| `GGRSGJMC` | 3 | Sarge | |
| `FSRSMKMC` | 4 | Sarge | |
| `DQRNBBMC` | 5 | Sarge | |
| `CSRJGCMC` | 6 | Sarge | |
| `BQRDMDPC` | 7 | Sarge | |
| `TJRDQFPC` | 8 | Sarge | |
| `SGRSCQPC` | 9 | Sarge | |
| `RJRNLRPC` | 10 | Sarge | |
| `QGRNRSPC` | 11 | Sarge | |
| `PSRJCTPC` | 12 | Sarge | |
| `GGRSGHMB` | 2 | Vicki | |
| `FSRSMJMB` | 3 | Vicki | |
| `DQRNBKMB` | 4 | Vicki | |
| `CSRJGBMB` | 5 | Vicki | |
| `BQRDMCPB` | 6 | Vicki | |
| `TJRDQDPB` | 7 | Vicki | |
| `SGRSCFPB` | 8 | Vicki | |
| `RJRNLQPB` | 9 | Vicki | |
| `QGRNRRPB` | 10 | Vicki | |
| `PSRJCSPB` | 11 | Vicki | |
| `NQRDGTPB` | 12 | Vicki | also “all levels for Vicki” |
| `QGQNRTPC` | 12 | Sarge | “all levels for Sarge” |

A second published family (world-of-nintendo) uses different filler for the
same Vicki levels 2–9. All eight pass the checksum; `FSSSMHMB` was entered in
the emulator and produced level 2.

Source access: GameFAQs' cheat page returned HTTP 403 to direct fetches, so its
list was recovered from search snippets; CheatCC, RetroMaggedon and
world-of-nintendo served the lists directly. TCRF's `Talk:Army Men Advance`
page returned a Cloudflare challenge, and a VGChartz site search returned no
password page. The 31 codes in this section are the union of the sources that
did respond.

| Code | Level | Character |
|---|---:|---|
| `FSSSMHMB` | 2 | Vicki |
| `DQSNBJMB` | 3 | Vicki |
| `CSSJGKMB` | 4 | Vicki |
| `BQSDMBPB` | 5 | Vicki |
| `TJSDQCPB` | 6 | Vicki |
| `SGSSCDPB` | 7 | Vicki |
| `RJSNLFPB` | 8 | Vicki |
| `QGSNRQPB` | 9 | Vicki |

### 6.4 Level names

| Level | Name |
|---:|---|
| 1 | TAN ARMY JAIL |
| 2 | TRAINING CAMP |
| 3 | AREA 41 |
| 4 | HANGAR 13 |
| 5 | BEDROOM |
| 6 | HALLWAY |
| 7 | BATHROOM |
| 8 | IN THE BATH |
| 9 | PATIO |
| 10 | GARAGE |
| 11 | GREEN CAMP |
| 12 | AREA 41-RETURN |

The names are stored in the `SELECT LEVEL` bank at `0x0802BE0D`; the observed
selector agrees with this order.

### 6.5 Field layout

| Symbol position (0-based) | Nibble | Role |
|---:|---|---|
| 0 | `v0` | 4-bit checksum |
| 1 | `v1` | filler |
| 2 | `v2` | filler + checksum input |
| 3 | `v3` | filler |
| 4 | `v4` | filler |
| 5 | `v5` | `16 − level` |
| 6 | `v6` | filler |
| 7 | `v7` | `15 − character` |

There are no reserved bits in the input alphabet; the only non-enterable symbol
is `#`.

---

## 6b. Enumeration

### Space definition

* Alphabet: 22 symbols (`B C D F G H J K L M N P Q R S T V W X Y Z !`).
* Length: exactly 8 symbols.
* Raw space: `22^8 = 54,875,873,536`.
* Check: one nibble (`v0`), 4 bits, computed from `v2`, `v5`, `v7`.
* Payload fields: level (4 bits at `v5`), character (4 bits at `v7`), five
  filler nibbles (`v1`, `v2`, `v3`, `v4`, `v6`).

Exact count of checksum-accepted strings (computed from the 22-symbol →
nibble distribution of each key byte):

```
accepted = 3,435,129,984
```
(about 1 in 16 of the raw space).

Nibble states: 256 `(level, character)` pairs (`level = 16−v5`, `char =
15−v7`), of which 24 have retail content (levels 1–12 × characters 0/1).
Those 24 states account for **513,489,152** accepted strings; per-state counts
range from **13,118,336** to **29,984,768**. The published 23 codes are
therefore a negligible, arbitrary subset of the spellings of 24 states.

### Novel codes (not in any published list)

| Code | Decoded state | In-game proof |
|---|---|---|
| `HJRDCGMB` | level 1, Vicki | accepted; `SELECT LEVEL` shows level 1; level 1 played as the female character (`... novel code HJRDCGMB Vicki gameplay.png`) |
| `NDRMNTLB` | level 12, Vicki, all filler 0 | accepted; `SELECT LEVEL` level 12 |
| `NFRMNTLB` | level 12, Vicki, `v1=1` | accepted; level 12 |
| `MDSMNTLB` | level 12, Vicki, `v2=13` | accepted; level 12 |
| `N!RMNTLB` | level 12, Vicki, `!` filler | accepted; level 12 — proves `!` is enterable |

`HJRDCGMB` is the headline result: every published list begins Vicki at level
2, so level 1 Vicki was not reachable from any published code. The code was
generated from the reconstructed format and entered through the normal ring;
the game accepted it and started “Tan Army Jail” with Vicki.

`armymen_pw.py` (this folder) reproduces the format:

```bash
python3 armymen_pw.py decode NQRDGTPB HJRDCGMB NQRDGTPC
python3 armymen_pw.py make 1 1        # -> HDRMNGLB (another level-1 Vicki code)
python3 armymen_pw.py make 12 1 0 13 0 0 0   # -> MDSMNTLB
```

### Bounds proved by rejection

| Test | Value | Result |
|---|---|---|
| Wrong checksum | `NQRDGTPC` | `INVALID` (observed) |
| Level 16 Vicki | `MDRMNPLB` | `INVALID` (observed); the check would need 17, outside a nibble |
| Level 13 Sarge (checksum-valid) | `NQRDGLPC` | accepted into `SELECT LEVEL`, but cursor is below level 12; starting it gives an out-of-bounds German briefing |
| Character code 2 | `MQRDGTPF` | accepted into `SELECT LEVEL` at level 12; there is no third character |
| Empty/short entry | 0–7 symbols | A only appends; no validation occurs until eight symbols are present |

The arithmetic gives a representability bound. Substituting the fields,
`v0 = 14 − v2 + level + character`, and `v0` must be 0–15. With the published
convention `v2 = 14` this is `level + character ≤ 15`. Since `v2` is free, the
absolute maximum is `level + character ≤ 16` at `v2 = 15`: Sarge level 16 and
Vicki level 15 are representable by the arithmetic but lie outside the
twelve-entry content table; the level-13 test shows how out-of-range levels
behave. Vicki level 16 (`level + character = 17`) has no valid check nibble and
was rejected. Retail content stops at level 12 regardless.

### Button-code / debug-menu search (negative)

The only cheat-like system found is the password. The text search over the
whole ROM (`strings -n 4`, 33,133 lines) gives:

| Keyword | Hits | Classification |
|---|---:|---|
| `password` | 11 | password-screen UI in five languages |
| `code` | 14 | mission text (“CODE CARDS”, “CRACK THE CODE”, “ALIEN CODE”) |
| `debug` | 0 | — |
| `cheat` | 0 | — |
| `secret` | 2 | mission text “SECRET BASE” (EN/ES) |
| `unlock` | 0 | — |
| `mission` | 31 | briefing/objective text |
| `gallery`, `sound test`, `level select` | 0 | — |

A u16 key-mask scan (single-button masks `01,02,04,08,10,20,40,80,100,200`)
found no Konami sequence in either polarity and no `ABBA`, `ABAB`, `UUDD`,
`LLRR` or `UUDDLR` sequence in code space. The 1,242 raw runs of consecutive
single-button-mask values are dominated by graphics/tile data; the one
pointer-referenced run at `0x08030C2C` is an OAM X/Y offset table used at
`0x0800A08A` to place sprites, not a cheat sequence. No hidden/debug menu text
or button gate was found.

### Published-code verification

* All 31 distinct literals from the public lists are **absent** from the ROM,
  confirming an algorithmic generator rather than a stored table.
* All 23 primary codes and all 8 second-family codes satisfy the reconstructed
  checksum.
* `NQRDGTPB`, `QGQNRTPC` and `FSSSMHMB` were entered in the emulator and
  produced the predicted screens; `NQRDGTPB` also unlocked all twelve levels.

---

## 7. Validation evidence

**Observed (emulator screenshots / RAM reads)**

* Title menu, password ring, `SELECT LEVEL`, `INVALID`, options, pause menu,
  level-1 Vicki gameplay.
* `NQRDGTPB` → all levels; `FSSSMHMB` → level 2; `HJRDCGMB` → level 1 Vicki.
* `NQRDGTPC` → `INVALID`; `MDRMNPLB` → `INVALID`.
* `NQRDGLPC` → cursor below level 12; starting it → out-of-bounds German
  briefing.
* `MQRDGTPF` → level 12 (character code 2 accepted).
* Buffer `0x02020888` contains the typed eight characters + `#`; ring index
  `0x020208AC` moves ±1 per discrete tap.
* The `.sav` file is 0 bytes after play.

**Derived (disassembly / arithmetic)**

* The XOR key, the 22-symbol mapping, the checksum formula, and the
  `level = 16−v5`, `character = 15−v7` field extraction.
* The acceptance bound `level + character ≤ 16` (≤15 with the conventional
  `v2 = 14`).
* The exact space counts in §6b.
* The checksum block is at `0x08006A6C`; the comparison is at `0x08006B0E`;
  the successful path stores `level−1` at `[sp,#44]`.

**Inferred**

* `v1`, `v2`, `v3`, `v4`, `v6` are progress/cosmetic filler that the validator
  ignores. Five different filler values produced the same level-12 state, but
  their effect on any *other* game variable (e.g. completed missions) was not
  isolated.
* The level-13 German briefing is an out-of-bounds text-bank read caused by a
  level index beyond the twelve-entry table.
* The character field is 4 bits; values >1 are accepted by the checksum but
  have no real character art.

---

## 8. Unknowns

* **Alphabet-table off-by-one.** The checksum block loads the literal
  `0x0803071A`, whose first byte is `C`, and its search loop covers the 20
  letters `C…Z`. Yet the emulator accepts `B` (and `!`) and the arithmetic
  matches an alphabet starting at `B` (`B=0 … Z=20, !=21`). The block may be
  shared with a second screen, or a runtime alias may exist that was not
  located. The *empirical* mapping is proven by accepted codes; the exact
  symbol→index path in that block is not fully reconciled.
* **Meaning of the filler nibbles.** They are not validated, but whether the
  generator uses them for mission flags, difficulty, score, or a checksum of
  another field is unknown. The generator (“NEW PASSWORD” after a mission) was
  not located.
* **Difficulty.** `v2` is free and does not appear to change the decoded
  level/character. No test established whether any filler nibble changes the
  OPTIONS difficulty; all tested codes left the level selector unchanged.
* **Character values >1.** `v7` values 13–15 pass the check and reach the level
  selector; the in-game character mapping for those values was not established.
* **Level 13+ content.** The selector and briefing dereference out-of-range
  data; the exact crash/hang boundary is left to a future pass.
* The exact caller that consumes the validator result and writes the global
  level/character words was not isolated; the level-select screen was used as
  the behavioral oracle.

---

## 9. Tooling

| Tool / file | Purpose |
|---|---|
| `armymen_pw.py` (this folder) | Encoder, decoder, checksum verifier and field table for the 8-symbol format |
| `arm-none-eabi-objdump` | Thumb disassembly of `0x08006A6C`–`0x08006D20` and the UI bank |
| mGBA SDL 0.10.5 | Emulator; `Shift+F1` / `F1` savestates |
| Xvfb, openbox, xdotool, scrot/ImageMagick | Headless display, input, screenshots |
| Python zlib savestate parser | Extracts EWRAM/IWRAM from mGBA `.ss` PNG `gbAs` chunks; used to read the input buffer and ring index |
| `strings -t x`, literal/pointer scans | Recon; proved the published codes are not stored |

Screenshots in this folder:

* `Army Men Advance - title menu.png`
* `Army Men Advance - password ring.png`
* `Army Men Advance - public code NQRDGTPB entered.png`
* `Army Men Advance - all levels unlocked.png`
* `Army Men Advance - novel code HJRDCGMB level 1.png`
* `Army Men Advance - novel code HJRDCGMB Vicki gameplay.png`
* `Army Men Advance - novel code N!RMNTLB.png`
* `Army Men Advance - published alt code FSSSMHMB level 2.png`
* `Army Men Advance - bad checksum INVALID.png`
* `Army Men Advance - level 13 out of range.png`
* `Army Men Advance - options.png`

`Army Men Advance.ss1`–`.ss3` are emulator artifacts (git-ignored) and can be
deleted; the screenshots and `armymen_pw.py` are the durable evidence.

---

## 10. Legal note

No ROM, graphics, music or extended game text is redistributed here. Only
addresses, the algorithm, short identifiers, and screenshots produced from a
locally owned ROM are included.
