# Stuart Little 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Stuart Little 2/Stuart Little 2.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `STUARTLITTLE` |
| Game code / maker | `ASLE` / `52` (Activision), version `0x00` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) — no cracktro/trainer patch |
| MD5 | `2170ce3d59a6f69d6d5b002088beed7c` |
| SHA-1 | `fdb6d8098340966456cd05c7babe77b5a204608c` |
| SHA-256 | `a9a97d3ac4064c79d1f1551f66ed97dc9e49bf6228a21a62233c14784b76c22b` |

Emulator: mGBA 0.10.5 SDL under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, 3× scale. Keymap: A=`x`, B=`z`, Start=`Return`, D-pad=arrows.

## 2. Executive summary

The only developer-intended in-game cheat surface in this GBA SKU is a **four-symbol numeric password** on the main menu (`PASSWORD`). The alphabet is **digits 1–8** (eight symbols, internally `0..7`), not 0–9. The accepted set is **132 of 4096** possible strings, produced by an involutive XOR scramble plus a 4-bit checksum and two range gates. Every accepted password decodes to a triple `(lives, level, flag)`; each `(lives, level)` pair has exactly two spellings that differ only in an otherwise-unused flag bit.

The complete algorithm was recovered from `0x0800FE8C` / `0x0800FDC8` / `0x0800FE10` and reimplemented offline; the model agrees with every published code except `1234` (rejected by the game) and `2800` (uses digit `0`, outside the alphabet). Two codes that appear in **no published list** were minted and accepted on the real screen with RAM confirmation: **`8713`** (`lives=7, level=5, flag=1`) and **`1367`** (`lives=4, level=1, flag=1`). Three rejection cases were verified in RAM: bad checksum (`1234`), out-of-range level (`2348`, level field = 10), and gate violation (`3488`, level field 1 but lives = 7).

No GBA button codes or hidden debug menu were found. The widely copied button sequences on 3rd party cheat indexes are explicitly labelled "Cheat Codes PS" and do not apply to this SKU. The `DEBUG_ASSERT*` strings at `0x31418`–`0x336C4` are engine instrumentation, not a user-facing cheat menu.

## 3. How to reproduce

### Reaching the screen
Boot, wait for the Activision splash and title animation (~10 s), then from
`START / OPTIONS / MULTIPLAYER / PASSWORD` press Down three times (50 ms holds —
100 ms double-steps the cursor) and A. Select `NORMAL` on the difficulty screen
if prompted. The password screen shows four slots, initially all `1`, with
Up/Down arrows above the selected slot and Left/Right to move between slots.
Down cycles `1→8→7→…→2→1`; Up cycles the other way.

### Reliable entry for arbitrary codes
The UI has a debounce quirk that makes long generated strings hard to type by
hand. For reproducible tests I set the four internal bytes directly at
`0x030023A0..A3` while the screen-update function `0x08010C30` was halted on a
breakpoint in mGBA's `-d` CLI debugger, removed the breakpoint, then pressed A
on the real screen so the game's own validator ran. Screenshots and savestates
were taken after submission. Internal digit = displayed digit − 1.

### Scripts (in work dir `/tmp/stuart2`)
* `model.py` — Python validator/enumerator (exact reimplementation).
* `run2.py` — set digits via CLI debugger, submit on screen, screenshot, save state.
* `ssdiff.py`, `ssdiff2.py`, `ssdump.py` — mGBA `gbAs` savestate decompression and RAM diff.
* `scansfx.py`, `ptrscan.py` — Capstone/pointer scans used to locate the validator.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x0800FDC8` | In-place XOR scramble `T` (also used to undo itself) |
| `0x0800FDF4` | Clear password buffer / outputs |
| `0x0800FE10` | Encoder: game state → four digits (called with arg `8` from `0x0801179C`) |
| `0x0800FE8C` | **Validator/decoder** (arg `8` from screen at `0x08010CDC`) |
| `0x08010C30` | Password screen update function (input, validation request, result) |
| `0x08010CDA`–`0x08010D14` | Submit result: correct → SFX 87, timer `0x78`; incorrect → SFX 86, timer `0x3C` |
| `0x030023A0..A3` | Four entered digits, internal `0..7` |
| `0x030023A6` (u16) | Decoded `lives` field (`a`) |
| `0x030023A8` (u16) | Decoded `level` field (`v`) |
| `0x030023AA` (u8) | Decoded `flag` field |
| `0x030023AB` (u8) | Valid flag: 1 = accepted |
| `0x030023AC` (u16) | Result timer (counts down) |
| `0x030001F0` | Pointer to the game-state base (`0x02009608` in all runs) |
| `0x02009748` | `base+0x140` — `lives` written by validator (matches published "Infinite Lives 82009748 0009") |
| `0x02009784` | `base+0x17C` — `level` written by validator |
| `0x02009730` | `base+0x128` — `flag` written by validator |
| `0x08031418` / `0x08031438` | `correct_password.raw` / `incorrect_password.raw` asset paths |
| `0x0277060`–`0x0277078` | Audio asset records: ID `0x56`=incorrect, `0x57`=correct |

## 5. Algorithm

Let the four entered bytes (internal values `0..7`; on-screen digit = byte + 1) be
`p[0..3]`. Constant salt `K = 8`.

**Step 1 — scramble** (`T`, `0x0800FDC8`), applied in place:

```
p[0] ^= p[3] & 5
p[1] ^= p[3] & 3
p[2] ^= p[3] & 6
p[3] unchanged
```

`T` is an involution: the validator applies it again at `0x0800FED8` to restore
the player's digits after decoding. Let `(a,b,c,d) = T(p)`.

**Step 2 — decode fields and check:**

```
checksum_expected = (2*d + (c & 1))                 # r5
checksum_computed = (8 + a + b + ((c & 6) >> 1)) & 15   # r4
lives  = a                                          # -> 0x030023A6
level  = b + ((c & 4) << 1) + 1                      # -> 0x030023A8
flag   = (c & 2) >> 1                                # -> 0x030023AA
```

Accept iff all of:

1. `checksum_computed == checksum_expected`
2. `level <= 9`
3. `level <= 2` implies `lives <= 5`
4. `level <= 4` implies `lives <= 6` (for `level > 4` no lives bound)

On accept, the game writes the three fields to the state block, sets the valid
flag and plays SFX 87; on reject it leaves the state untouched, clears the
valid flag and plays SFX 86. Encoder `0x0800FE10` computes the inverse from
`(lives & 7, [base+0x178]-1, [base+0x128])` with the same salt and scramble.

## 6. Tables

Published level codes verified against the model / emulator (all accepted):

| Published label | Code | Decoded (lives, level, flag) |
|---|---|---|
| L1 | 1377 | (4, 1, 0) |
| L2 | 1487 | (4, 2, 0) |
| L3 | 2278 | (4, 3, 0) |
| L4 | 6366 | (0, 4, 0) |
| L5 | 6787 | (1, 5, 0) |
| L6 | 5778 | (1, 6, 0) |
| L7 | 5688 | (1, 7, 0) |
| L8 | 6678 | (0, 7, 0) |
| L9 | 6588 | (0, 8, 0) |
| L10 | 6216 | (0, 9, 0) |
| L11 | 7614 | (7, 7, 1) |
| L12 | 7421 | (6, 4, 0) |

Other published strings accepted by the model: `7266, 1458, 8166, 2358, 1378,
7177, 2268, 1288, 5822, 7533, 2428, 8161`. Two publications are wrong for this
SKU: `1234` fails the checksum (confirmed rejected in emulator) and `2800`
contains digit `0`, which the on-screen alphabet cannot represent.

## 6b. Enumeration

**Space.** Alphabet size 8, length 4 → `8^4 = 4096` representable inputs.
Fields: `lives = a ∈ 0..7`, `level = v = b + 2*(c&4) + 1 ∈ 1..16`, `flag ∈ {0,1}`.
The checksum is 4 bits; the three outputs are derived from the same four
digits, so the code is fully determined by `(a, b, c, d)` up to the scramble.

**Closed-form accepted set.** Running the ROM's own validator over all 4096
inputs gives exactly **132 accepted codes**. The set is exactly:

* `level ∈ {1,2}`: `lives ∈ 0..5` → 6 combinations
* `level ∈ {3,4}`: `lives ∈ 0..6` → 7 combinations
* `level ∈ {5,6,7,8,9}`: `lives ∈ 0..7` → 40 combinations

= 66 `(lives, level)` pairs, each with **2 aliases** (flag 0 and flag 1) =
**132 codes**. No other input passes. The flag bit is written to game state but
does not change the selected level, so the 2-code alias pairs are
behaviourally near-identical (§16.4b of the guide).

**Novel codes (absent from every published list), accepted in-game:**

| Code | Decoded fields | Evidence |
|---|---|---|
| **`8713`** | `(lives=7, level=5, flag=1)` | Accepted on the real password screen. RAM after submit: `0x030023AB=01`, digits `07 06 00 02`, `0x02009748=7`, `0x02009784=5`, `0x02009730=1`. Produced the same level-5 cutscene ("Mrs. Little is in the kitchen washing dishes. Oh no!") as published `6787`, but with unadvertised lives=7 and flag=1. |
| **`1367`** | `(lives=4, level=1, flag=1)` | Accepted. RAM: valid flag `01`, digits `00 02 05 06`, `lives=4`, `level=1`, `flag=1`. This is the unpublished flag-1 twin of published `1377` (flag=0). |

Screenshots: `8713_t3_crop.png`, `8713_L20_crop.png`, `1367_t2/t3_crop.png`,
`6787_t3_crop.png`, `1487_t3_crop.png` in `/tmp/stuart2`.

**Bounds proven by rejection** (each submitted on the real screen after setting
the buffer; RAM read from a savestate 6 s later):

| Input | Why it must fail | Result |
|---|---|---|
| `1234` | checksum mismatch | `0x030023AB = 0`, fields unchanged (`lives` stayed 5), no level transition |
| `2348` | checksum passes but `level = 10 > 9` | `0x030023AB = 0`, no transition |
| `3488` | checksum passes, `level = 1`, but `lives = 7 > 5` | `0x030023AB = 0`, no transition |

These pin both layers: the checksum and the `lives`/`level` range gates.

## 7. Validation evidence

* **Derived (disassembly):** validator, scramble, encoder, constants, field
  addresses, and all accept/reject branches at the addresses in §4/§5.
* **Observed (emulator + RAM):** published `1487` accepted → lives 4, level 2,
  level-2 school cutscene; published `6787` accepted → level 5 kitchen
  cutscene; novel `8713` and `1367` accepted with predicted fields; three
  rejected inputs leave the valid flag at 0. Digit cycling and the 1–8
  alphabet were observed directly on the password screen.
* **Inferred:** `base+0x140` is lives (strongly supported by the published
  CodeBreaker address `82009748` and by the value written by every accepted
  code); `level` is the value written to `base+0x17C` and matches published
  level labels for levels 1–7, while labels 8–12 correspond to `(level, lives)`
  combinations rather than a simple level index.

## 8. Unknowns

* The exact gameplay purpose of the `flag` field (`base+0x128`) was not
  isolated; it splits every `(lives, level)` pair into two accepted spellings.
* Published labels for levels 8–12 do not correspond monotonically to the
  decoded `level` field; the mapping from `(lives, level)` to the game's
  internal stage index was not fully traced past the intro cutscenes.
* The "NEW PASSWORD" generator path (`0x0800FE10` from `0x0801179C`) was
  located and its salt confirmed (`8`), but its on-screen menu entry was not
  reached during menu walking.

## 9. Tooling

`strings`, `xxd`, `grep`, Python `capstone`, `arm-none-eabi-objdump
-M force-thumb`, mGBA 0.10.5 (`-3`, `-d`, `-t`, `-g`), Xvfb, openbox,
`xdotool`, `scrot`, ImageMagick, `gdb-multiarch` (GDB stub port 2345 was
occupied by another process, so mGBA's stub-free `-d` CLI debugger was used).
Savestates were decoded by extracting the zlib-compressed `gbAs` PNG chunk.

No ROM data or copyrighted assets are reproduced in this report; only
addresses, hashes, algorithms and self-generated codes are published.
