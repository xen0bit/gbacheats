# Antz Extreme Racing (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Antz Extreme Racing/Antz Extreme Racing.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `ANTZ RACING` (`41 4E 54 5A 20 52 41 43 49 4E 47 00`) |
| Game code | `ANUE` (USA) |
| Maker code | `7N` |
| Version | 0 (Rev.00) |
| Fixed byte 0xB2 | 0x96 |
| Entry word | `EA000030` (ARM `b 0x080000C0`) |
| Complement check 0xBD | stored 0x92, computed 0x92 (valid) |
| MD5 | `c33cd0b752e2305becd03604dbd90293` |
| SHA-1 | `ad6ded0f643457d652292bb97e30b1ad442e41da` |
| SHA-256 | `9bf8c74c87b57205f03501648d297fc9cab6c24f1a5c2be6cddc8db842e7d564` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once
(file 0x4), so this is a single GBA image, not a multi-game pack. No second
header, no boot shell.

Save: mGBA created a 0-byte `.sav` during the session and the game never wrote
save data; progress is carried by the password (Observed).

## 2. Executive summary

The game has a **9-symbol, 32-symbol-alphabet password system** (menu item
`PASSWORD`). The published codes are nine characters long, and the entry
screen holds nine symbols; the format is a full save-state code, not just a
level list.

* Alphabet: `0123456789BCDFGHJKLMNPQRSTVWXZ/*` (vowels removed) — 32 symbols,
  5 bits each, 9 positions = **45 bits**, 32^9 = 35,184,372,088,832 strings.
* The 45 bits are passed through a fixed invertible affine transform over
  GF(2) (linear bit mixing plus a fixed XOR mask) into a 48-bit buffer, then
  validated by `0x08326004`:
  * a 4-bit XOR/fold checksum (1/16 of strings);
  * a 20-bit payload `V` decoded as a mixed-radix number with radices
    `2,5,7,12,7,50,2` (space 588,000);
  * a 21-bit "opened items" list that must be a non-decreasing prefix
    followed by zeros;
  * range checks linking the fields.
* Accepted strings: **1,655,267,328** (4.70e-5 of the 45-bit space).
* Field meaning (proved on the `Password Contents` screen):
  `f16` = Termite-mode flag (7 shows "Termites Activated" and enables the 7th
  character), `f20` = opened-levels count (8..12), `char` = player
  (0 Z, 1 BALA, 2 WEAVER, 3 AZTECA, 4 MANDIBLE, 5 CUTTER, 6 TERMITE),
  `level` = level index 0..11 (displayed 1..12), `f24` = garage-item set
  (table of 7 masks), `tokens` = 0..98 in steps of 2, `f32` = 0 or 4
  (effect not identified).
* Published GameFAQs list = 12 level codes. All 12 are accepted by the ROM,
  but they only ever use `f16=6`, player Z, item set 255, 98 tokens,
  `f32=0`, and the zero item list. The "Level 13" entry is mislabelled: it
  decodes to **LEVEL 1, Opened Levels 12**.
* Novel, unpublished codes were generated and entered in mGBA, e.g.
  `HT*WW*PZN` → TERMITE / LEVEL 6 / Opened 12 / 0 tokens / item set 42 /
  "Termites Activated", and `7VKWSMPMX` (the maximum payload, 587,999).
* Two hard-coded developer passwords exist and are **chained**:
  `*CL3M3NT` (8 symbols; clears the entry buffer) then `*M4M1K0` (7 symbols;
  shows a developer photo). Neither appears in any published list.
* Bounds were proven in-game by rejection: 588,000 payload (one past max),
  `char >= f16`, `level > opened`, unsorted item list, corrupted checksum.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL, headless X.

```bash
Xvfb :139 -screen 0 1024x768x24 &
DISPLAY=:139 openbox &
DISPLAY=:139 SDL_AUDIODRIVER=dummy mgba -3 "Antz Extreme Racing.gba" &
```

mGBA SDL keymap used: **A = x**, **B = z**, **Start = Return**, D-pad =
arrow keys (all verified in-game); **Select = BackSpace** per the mGBA
default (not needed). Hold keys 60–120 ms; the menus repeat while a direction
is held, so use short taps for single steps.

Exact menu path:

1. Title screen `Press START` → `Return`.
2. Main menu: `QUICK RACE / 4 SEASONS / HEAD TO HEAD / GAME LINK / OPTIONS /
   PASSWORD`. Press `Down` five times, then `x`.
3. Password screen: 8-column × 4-row symbol grid and **nine** entry slots at
   the bottom. The highlighted symbol is previewed in the next slot.
   * arrows move the cursor (row wrap by ±8, column wrap by ±1);
   * `x` commits the highlighted symbol and advances;
   * `z` deletes the last symbol; `z` with an empty buffer exits to the menu;
   * `Return` does nothing here.
4. Enter **nine** symbols. The 9th `x` both commits the last symbol and runs
   the validator. A valid code shows `Password Contents`; `x` returns to the
   menu. An invalid code shows `INVALID PASSWORD!` and clears the entry.
5. Developer gate: enter `*CL3M3NT` (8 symbols). The 8th `x` clears the entry
   buffer (stage 1, no message). Then enter `*M4M1K0` (7 symbols); the 7th
   `x` shows the developer photo. `x` again returns to the menu.
6. To see the effect of a code: after `Password Contents`, `x` → main menu →
   `Up` to `4 SEASONS` → `x` → `CONTINUE` → `x` → `NEXT RACE`/`GARAGE`.

Screens walked (screenshots taken during the session; filenames in
`/tmp/opencode/antz/`): boot/legal, title, main menu, password entry,
published-code contents, novel-code contents, invalid-password screen,
developer photo, `4 SEASONS` (CONTINUE/NEW GAME), `NEXT RACE`/`GARAGE`,
`QUICK RACE` vehicle select, character switch (Z/BALA stats), Head-to-Head
versus screen, race intro/countdown/HUD, `OPTIONS` (sound, music, difficulty,
credits), credits, `GAME LINK` waiting room, and the in-race `PAUSE`
(`RESUME`/`QUIT`).

## 4. Address map

All addresses are ROM addresses; file offset = ROM address − 0x08000000.

| ROM address | File offset | Contents |
|---|---|---|
| `0x080000C0` | 0xC0 | ARM crt0 / entry |
| `0x08329518` | 0x329518 | alphabet string `0123456789BCDFGHJKLMNPQRSTVWXZ/*` (32 bytes, NUL) |
| `0x08329506` | 0x329506 | developer code 1, 8 bytes `7F 15 1B 6B 14 69 15 08`, XOR key `0x55+i` |
| `0x0832950E` | 0x32950E | developer code 2, 7 bytes `68 0E 70 08 77 0C 78`, XOR key `0x42+i` |
| `0x08329693` | 0x329693 | 7-byte item-mask table `2A 54 7F A9 D4 FE FF` = 42,84,127,169,212,254,255 |
| `0x0832969C` | 0x32969C | radix table (u32×7 + 0): `2,5,7,12,7,50,2` |
| `0x08321A9E` | 0x321A9E | password screen input/update function (grid, entry, dev-code gate, draw, call validator) |
| `0x08321EE4` | 0x321EE4 | password screen init (called from `0x08320D3E`) |
| `0x083257FC` | 0x3257FC | pack 9 symbols → 45 bits into a 48-bit buffer |
| `0x08325ACC` | 0x325ACC | fixed affine obfuscation (bit permutation + XOR) of the buffer |
| `0x08326004` | 0x326004 | **password validator** (returns 1 = valid, 0 = invalid) |
| `0x08326F34` | 0x326F34 | unsigned quotient helper |
| `0x08326FAC` | 0x326FAC | unsigned modulo helper |
| `0x08328810` | 0x328810 | memcpy helper |

RAM (from the validator, Observed with a Unicorn harness and confirmed by the
on-screen result):

| RAM | Meaning |
|---|---|
| `0x03002E10` | 18-byte decoded-progress struct (see §6) |
| `0x03000B74` | halfword flag OR-ed with `f32` |
| `0x03002DBC` | radix-table index (reset to 0 at entry) |
| `0x03000664` | result flag written by the caller (1 or 2) |

## 5. Algorithm

### 5.1 Symbols → 45 bits → obfuscated 48-bit buffer

`0x083257FC` converts each symbol to its alphabet index 0..31 (linear search)
and packs the 9 five-bit values into a 48-bit buffer. `0x08325ACC` then applies
a fixed **invertible affine map over GF(2)**. The combined map is exactly:

```
P = C ^ XOR_{i=0..8, k=0..4, bit k of symbol[i] set} D[i][k]

C = 0x0895663852CE

D[0] = C0000        100000       30            5000          800000000000
D[1] = 400000000000 C00000       5000000       200000000     4000000
D[2] = A000000       500          A00           1000          A0000000
D[3] = 10           200000000000 C000000000    80000000      1
D[4] = C0           100          20000         80400000000   80000000000
D[5] = 40000        8000000      100040000000  2000          40
D[6] = 300000       400000       A000          10000         3
D[7] = 300000000    200          4             C             3000000000
D[8] = 800000000    10000000     2000000000    40000000      8000000000
```

`P` is 48 bits (bytes P0..P5); the top two bytes are always 0. The map has
rank 45, so the 45 symbol bits and the 45 validator-relevant bits are in
one-to-one correspondence.

### 5.2 Validator (`0x08326004`)

```
b0 = bswap32(P[0..3])            # byte-reversed 32-bit word
b1 = bswap32(P[4..7])
B  = b0 | (b1 << 32)             # 64-bit "logical" bitstream

# 1) 4-bit checksum (checked first in the ROM)
c = P0 ^ P1 ^ P2 ^ P3 ^ P4 ^ (P5 & 0x80)
c = ((c & 0xC0) >> 3) ^ c
c = ((c & 0x0F) ^ (c >> 4)) & 0x0F
if c != ((b1 >> 19) & 0x0F): reject

# 2) payload
Vraw = (b0 >> 12) & 0xFFFFF          # B bits 12..31
V    = Vraw ^ 0x237D2 if (Vraw & 1) else Vraw
if V > 587999: reject                # 0x8F8DF

# 3) mixed-radix decode
for r in [2, 5, 7, 12, 7, 50, 2]:
    d[j] = V % r ; V //= r
f16   = d0 + 6            # 6 or 7
f20   = d1 + 8            # 8..12 (opened levels)
char  = d2                # 0..6 (player)
level = d3                # 0..11 (displayed level = level+1)
items = TABLE[d4]         # TABLE = 42,84,127,169,212,254,255
tokens= d5 * 2            # 0..98 even
f32   = d6 * 4            # 0 or 4

# 4) cross-field checks
if not (char < f16): reject
if level > f20: reject
if level == 0 and f20 == 8:
    if not (char == 0 and items == 255 and tokens == 0): reject

# 5) 21-bit opened-item list (bits 20..40 of B), 7 × 3 bits
list[i] = (b0 >> (9 - 3*i)) & 7            for i = 0..3
list[i] = (b1 >> (29 - 3*(i-4))) & 7       for i = 4..6
# accept only: a non-decreasing run of non-zero values, then zeros to the end
if list is not of that form: reject

# 6) success
store f16, f20, char, level, items, tokens, list[0..6], f32 into 0x03002E10
return 1
```

Note the two independent bit meanings: `V` occupies `b0` bits 12..31, while
`list[0..3]` occupies `b0` bits 0..11 and `list[4..6]` occupies `b1` bits
23..31. The stored checksum is `b1` bits 19..22. Together these are exactly
the 45 constrained bits.

### 5.3 Developer gate (inside `0x08321A9E`)

Before the generic validator, the screen has two literal comparisons:

* when 8 symbols have been entered (`pos == 8`) and stage 0, compare the
  8-byte entry with `0x08329506` XOR `(0x55+i)` → `*CL3M3NT`. On match:
  stage = 1, entry buffer cleared to `_`, cursor reset.
* when stage 1 and 7 symbols have been entered (`pos == 7`), compare with
  `0x0832950E` XOR `(0x42+i)` → `*M4M1K0`. On match: `sl = 0x58`, fade to
  black, return screen state 0x58 (the developer-photo screen).

The generic validator is not called on these two paths.

## 6. Tables

### 6.1 Alphabet (32 symbols, values 0..31)

```
0 1 2 3 4 5 6 7 8 9 B C D F G H J K L M N P Q R S T V W X Z / *
```

The on-screen grid is 8 columns × 4 rows, row-major in this order. The
alphabet is stored ASCII at `0x08329518`.

### 6.2 Radices and decoded field space (588,000)

| Digit | Radix | Field | Values |
|---|---:|---|---|
| d0 | 2 | f16 | 6 (normal), 7 (Termites Activated; enables char 6) |
| d1 | 5 | f20 | 8,9,10,11,12 = "Opened Levels" |
| d2 | 7 | char | 0 Z, 1 BALA, 2 WEAVER, 3 AZTECA, 4 MANDIBLE, 5 CUTTER, 6 TERMITE |
| d3 | 12 | level | 0..11; displayed LEVEL 1..12 |
| d4 | 7 | items | 42, 84, 127, 169, 212, 254, 255 (garage item set) |
| d5 | 50 | tokens | 0,2,...,98 |
| d6 | 2 | f32 | 0 or 4 (effect not identified) |

`V = d0 + 2·d1 + 10·d2 + 70·d3 + 840·d4 + 5880·d5 + 294000·d6`, and
`Vraw = V` if `V` is even, else `V ^ 0x237D2`.

### 6.3 Decoded progress struct (RAM `0x03002E10`)

| Offset | Field |
|---:|---|
| +2 | f20 (opened levels) |
| +3 | f16 (6/7) |
| +4 | character index |
| +5 | level index |
| +6 | tokens (0..98) |
| +7 | item-set mask (42..255) |
| +8..+14 | up to 7 opened-item IDs (non-decreasing, zero-padded) |
| +16 | f32 (0/4) |

The caller (`0x08321E6C`) writes 1 or 2 to `0x03000664` depending on whether
`f20==8 && level==0`, then returns the screen state.

### 6.4 Published codes (GameFAQs / fandom / supercheats), verified in ROM

All 12 are accepted by `0x08326004` (Unicorn) and by the emulator UI.

| Published label | Code | V | char | level | opened | items | tokens | list |
|---|---|---:|---|---:|---:|---:|---:|---|
| Level 2 | `CVWVC/4ZN` | 293230 | Z | 2 | 8 | 255 | 98 | [2,0,0,0,0,0,0] |
| Level 3 | `9SZVCW7*X` | 293300 | Z | 3 | 8 | 255 | 98 | [0,...] |
| Level 4 | `CV*VT*6*N` | 293370 | Z | 4 | 8 | 255 | 98 | [0,...] |
| Level 5 | `9SMSCL5*X` | 293440 | Z | 5 | 8 | 255 | 98 | [2,0,...] |
| Level 6 | `CSPS9Q6ZN` | 293510 | Z | 6 | 8 | 255 | 98 | [2,0,...] |
| Level 7 | `9WRVWL5ZX` | 293580 | Z | 7 | 8 | 255 | 98 | [2,0,...] |
| Level 8 | `CSTSCR4*N` | 293650 | Z | 8 | 8 | 255 | 98 | [0,...] |
| Level 9 | `8VWVTL7*X` | 293720 | Z | 9 | 8 | 255 | 98 | [4,0,...] |
| Level 10 | `9TZVTQ5*N` | 293792 | Z | 10 | 9 | 255 | 98 | [2,0,...] |
| Level 11 | `9V*SCQ7*N` | 293864 | Z | 11 | 10 | 255 | 98 | [2,0,...] |
| Level 12 | `1TTSWV5ZX` | 293936 | Z | 12 | 11 | 255 | 98 | [2,0,...] |
| "Level 13" | `9STVCV5ZX` | 293168 | Z | **1** | **12** | 255 | 98 | [2,0,...] |

The last row is a published-list error: the code displays **LEVEL 1,
Opened Levels 12**, not level 13. There is no level-13 value in the radix-12
level field.

### 6.5 Developer passwords

| Stage | Input | Length | Effect |
|---|---|---:|---|
| 1 | `*CL3M3NT` | 8 | clears the entry buffer, arms stage 2 |
| 2 | `*M4M1K0` | 7 | fade + developer photo (two people, Japanese shop front) |

Source bytes: `7F 15 1B 6B 14 69 15 08` at 0x329506 (XOR `0x55+i`);
`68 0E 70 08 77 0C 78` at 0x32950E (XOR `0x42+i`). The second code alone does
nothing; stage 1 is required.

## 6b. Enumeration

### Space definition

* Alphabet 32 symbols, length 9: **32^9 = 35,184,372,088,832** strings
  (45 bits, 2^45).
* Packing + obfuscation is a bijection on 45 bits (rank 45), so no string
  aliases.
* Checksum: 4 bits, `b1` bits 19..22; valid fraction 1/16 →
  **2,199,023,255,552** checksum-passing strings.
* Payload `V`: 20 bits, 588,000 representable values. After the field/range
  checks (`char < f16`, `level <= f20`, the level-1/8-opened special case)
  **482,304** values remain.
* Opened-item list: 21 bits, 7 values 0..7; the validator admits only a
  non-decreasing non-zero prefix followed by zeros →
  `Σ_{k=0..7} C(6+k,k)` = **3,432** patterns.
* Accepted strings = 482,304 × 3,432 = **1,655,267,328**
  (≈2^30.6, 4.70e-5 of all strings). Each accepted `(V, list)` pair has
  exactly one checksum and therefore exactly one code.

Published coverage: 12 of 1,655,267,328 accepted strings (7.2e-9). All 12
use `f16=6`, player Z, items 255, 98 tokens, f32=0; only level, opened-level
count and the item list vary.

### Novel codes (none appear in any published list) — entered in mGBA

| Code | Decoded state | Screen evidence |
|---|---|---|
| `HT*WW*PZN` | TERMITE, LEVEL 6, Opened 12, 0 tokens, item set 42, f32=4, **Termites Activated** | `pw_novel_termite.png` |
| `7VKWSMPMX` | V=587,999 (maximum), TERMITE, LEVEL 12, Opened 12, 98 tokens, f32=4, Termites Activated | `pw_max.png` |
| `9WWVTW7ZX` | BALA (character never used by the published list) | `pw_sl1.png` |
| `7VZTCRP*N` | Z + **Termites Activated** (f16=7 alone) | `pw_f16_7_sl0.png` |
| `CS*8THLWN` | 0 tokens (published list always 98) | `pw_f28_0.png` |
| `3WP8WR0*N` | item set 42 (published list always 255); item icons change | `pw_f24a.png` |
| `9TZ8WCKWX` | level 1, 8 opened, 0 tokens (the only legal level-1/8-opened form) | `pw_special_ok.png` |

`HT*WW*PZN` also survives the round-trip into gameplay: after `x` → main menu
→ `4 SEASONS` → `CONTINUE` → `NEXT RACE`, the HUD shows **00** in the token
counter (f28=0) and the Termite mode is active (`novel_race*.png`).

### Bounds proven by in-game rejection

| Code | Why it must fail | Result |
|---|---|---|
| `9SRSVW5MX` | `V = 588,000` (one past the 0..587,999 range) | `INVALID PASSWORD!` |
| `CVZS9*6*N` | `char=6` with `f16=6` (`char < f16` fails) | `INVALID PASSWORD!` |
| `3VTVT*6ZN` | `level=11` (displayed 12) with only 8 opened (`level > f20`) | `INVALID PASSWORD!` |
| `CWWSHV4ZN` | item list `[3,1,0,...]` is decreasing | `INVALID PASSWORD!` |
| `CVWVC/4ZM` | one symbol changed from a valid code → checksum fails | `INVALID PASSWORD!` |

`9STVCV5ZX` (published "Level 13") is accepted but displays LEVEL 1 /
Opened Levels 12 — an in-game proof of the published-list error.

### Negative results (bounded)

* Button-code system: no sequence table was found. The pause menu has exactly
  two actions (`RESUME`, `QUIT`), the main menu six, options four; the only
  input-sequence comparisons in the password code are the two developer
  passwords. A raw scan for u16 runs of ≥4 controller masks
  (1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200) found 18 runs, all in
  data/compressed regions, not in menu code; the Konami sequence and
  `UUDD` have zero hits as u16 or u8, and `BBAA` has no u16 hit (only
  coincidental u8 byte runs in data).
* No hidden/debug menu was found beyond the developer photo. The password
  screen is the only cheat entry point; `OPTIONS` has no secret item and the
  pause menu has no cheat branch.
* `strings` found only one English `PASSWORD` literal (file 0x2997D, inside
  `OINK\0OPZPASSWORD...`) and one German `PASSWORT` (0xBC0). The UI text
  bank is not plain NUL-terminated ASCII; it is a compressed/serialized pool
  whose literal runs survive as fragments. All UI claims above were checked
  on screen, not inferred from the string pool.

## 7. Validation evidence

**Observed (emulator / ROM execution):**

* All 12 published codes accepted by `0x08326004` under Unicorn; three
  (`CVWVC/4ZN`, `9TZVTQ5*N`, `9STVCV5ZX`) were also entered through the UI,
  and `Password Contents` was reproduced.
* Novel codes `HT*WW*PZN`, `7VKWSMPMX`, `9WWVTW7ZX`, `7VZTCRP*N`,
  `CS*8THLWN`, `3WP8WR0*N`, `9TZ8WCKWX` accepted through the UI with the
  displayed fields listed above.
* Rejections listed in §6b show `INVALID PASSWORD!`.
* Developer sequence `*CL3M3NT` → `*M4M1K0` shows the developer photo.
* `9STVCV5ZX` shows LEVEL 1 / Opened 12.
* Python model agrees with the ROM validator on 80 generated valid codes,
  800 random strings and 21 targeted strings (0 mismatches).
* Menus/screens enumerated in §3, including pause and link waiting room.

**Derived (instruction sequence):**

* 9-symbol length (pack loop `i <= 8`), 32-symbol alphabet, 4-bit checksum,
  mixed-radix decode, 21-bit list check, affine map (rank 45), developer
  comparisons.
* Published list is not literal in the ROM; the codes are algorithmic, so
  absence from the ROM is expected.

**Inferred:**

* `f32` (0/4) has no visible effect on `Password Contents` or the token/item
  display; its consumer was not isolated.
* The seven item IDs are garage upgrades (changing the list changes the
  icons on `Password Contents`; the garage screen shows seven upgrade slots),
  but the exact ID-to-upgrade mapping was not exhaustively proven.

## 8. Unknowns

* Meaning/consumer of `f32` (0 vs 4).
* Exact semantics of the 21-bit opened-item list beyond "non-decreasing set";
  the list is displayed as icons and persisted in the progress struct.
* The UI-text compression format (only its existence and readable fragments
  were used).
* Whether `f16=7`/TERMITE is a legitimate late-game unlock or a developer
  leftover; the string "Termites Activated" and the 7th character are only
  reachable through this password field in the tested build.
* No in-game save was observed; whether the cartridge uses EEPROM/Flash
  outside the password path was not proven.

## 9. Tooling

* `Xvfb`, `openbox`, `mGBA 0.10.5` (SDL), `xdotool`, `ImageMagick` for
  headless capture and input; `arm-none-eabi-objdump -M force-thumb` for
  Thumb disassembly.
* Python 3 + `unicorn` 2.1.4: created a ROM/RAM harness and executed
  `0x08326004`, `0x083257FC`, `0x08325ACC`, `0x08326F34`, `0x08326FAC`
  directly from the ROM (no reimplementation guesswork for the bit layer).
* Scripts used (in `/tmp/opencode/antz/`):
  `emu.py` (Unicorn harness), `val.py`/`val2.py` (validator probes),
  `trace.py` (pipeline/field tracing), `model.py`/`affine9.json` (affine
  basis extraction), `vmodel9.py` (full Python validator, 0 mismatches),
  `gen.py` (GF(2) encoder/mint), `drive.py`/`enter.py`/`tap.py` (input and
  screenshots).
* No ROM, graphics, music or extracted text is redistributed here; all
  evidence is addresses, algorithms and screenshots taken locally.
