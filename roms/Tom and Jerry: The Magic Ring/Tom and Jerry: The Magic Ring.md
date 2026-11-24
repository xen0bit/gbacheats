# Tom and Jerry: The Magic Ring (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tom and Jerry: The Magic Ring.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB), single image (one Nintendo logo at file 0x4) |
| Header title | `TOMJERRYRING` |
| Game code / maker | `ATJE` / `5L`, version 0.00 |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0` (no cracktro/trainer) |
| MD5 | `c3c7e4250ebfe4ce6020cabd42f08afe` |
| SHA-1 | `19ed73f1ea71454ed804ed758a697d5e3feda8be` |
| SHA-256 | `7c8c0864e092d2df4cecf56705b6d6939d97ded4c7b2cba720e88ed53667c119` |

Hashes also recorded in `/tmp/magicring/`. Addresses below are for this exact image.

## 2. Executive summary

The game has a **4-symbol numeric password system** reached from `Title → CONTINUE`. The on-screen keypad alphabet is exactly the digits **1–8** (no 0, no 9), so the full space is **8⁴ = 4,096** codes. The validator at `0x0801D38C` is **algorithmic**, not a lookup of the published strings: it reads the four digits back from the shadow-OAM sprite tile indices, packs them into 12 bits, applies a 2-bit XOR mask, splits the result into three fields, checks a 2-bit checksum and a 15×3 acceptance table, and on success writes the character/level globals and starts the game.

Exhaustive reimplementation of the validator gives **exactly 36 accepted codes out of 4,096 (0.88%)**. All 12 codes published on 3rd party cheat indexes decode and validate. **24 of the 36 accepted codes are absent from every published list**; one of them (`5488`, Tom with field value 1) was entered on the real screen, accepted, and RAM-verified. Two rejection classes were proven in-game: a checksum-valid code with a reserved field zero (`8111`) and a checksum-invalid code (`2111`) both return to the character-select screen.

No developer/debug menu, button sequence, hidden alphabet, or second code format was found. In-game text is font/tile-based (zero ASCII hits for `password`, `debug`, `cheat`, `level select`, etc. in 8 MiB), and the keypad handler was fully disassembled (only three actions: type digit, backspace, submit).

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL), Xvfb `:316`, openbox, `SDL_AUDIODRIVER=dummy`, `-3` scale.

Path: boot → language select (English) → title `PRESS START` → character select → move cursor **Up** to `CONTINUE` → **A** → password keypad. Keypad row is `1 2 3 4 5 6 7 8 ← ✓`; cursor wraps modulo 10; **A** types/backspaces/submits. Four red dots indicate empty slots.

Key map used: A = `x`, B = `z`, Start = `Return`, D-pad = arrow keys. Hold 90–120 ms (shorter taps are missed).

Codes tested (all typed on the real keypad):

| Code | Result | Evidence |
|---|---|---|
| `3783` | Accepted — Tom, Chapter 2 "Bareknuckle in the Park" | screenshot `code3783.png`; RAM char=1, field5=3 |
| `5488` | **Accepted — novel** — Tom, level-1 game start | `novel5488_pre.png`, `novel5488_result.png`; RAM char=1, field5=1 |
| `6718` | **Accepted — novel** — Jerry, but corrupt/unplayable level | `novel6718_result.png`, `after_start_6718.png` |
| `8111` | Rejected (checksum-valid, reserved field zero) | `rej8111_confirm.png` + `rej_8111.png` → character select |
| `2111` | Rejected (bad checksum) | `rej_2111.png` → character select |

Scripts used: `mr.py` (input/screenshot), `enter.py` (keypad driver), `decoder.py` (validator), `testrun.py`, `ramverify.py`, `gdbdrv.py`, `ssdiff.py`.

## 4. Address map

| Item | Address | Notes |
|---|---|---|
| Input reader (KEYINPUT `0x04000130`) | `0x08006E8C` | writes active-high masks to `0x0300F060` / `F460` / `F860` |
| Password-screen UI handler | `0x0801D5C4`–`0x0801D7D8` | digit/backspace/submit branches |
| **Validator** | `0x0801D38C` | called at `0x0801D784` when 4 digits entered + submit |
| Reject path | `0x0801D590` | sound `0x080088A4`, returns to character select |
| Digit count | `0x03000694` | u8, 0–4 |
| Shadow OAM base | `0x03005350` | digit sprite tileinfo cells at `+4,+12,+20,+28` |
| Digit cell 1..4 | `0x03005354/535C/5364/536C` | u16 tileinfo; tile = `0x200 + (digit−1)*0x10` |
| Blank digit tile | `0x02B0` | used for empty slots / backspace |
| Table T1 | `0x08295910` (15 B) | copied to stack+0 |
| Table T2 | `0x0829591F` (15 B) | copied to stack+16, indexed by r4 on success |
| Table T3 | `0x0829592E` (45 B) | copied to stack+32, 3 rows × 15 |
| Success globals | `0x03005340` (character), `0x030063D4` (field5), `0x03005FFC` (mode 1/2), `0x03005754` (level-ish) | written by validator |

Literal pool of the validator is at `0x0801D500`–`0x0801D53E`; `0x0801D50C` = `0x03005350` (shadow OAM), `0x0801D510` = `0xFFFFFE00`, `0x0801D514` = `0xFFFFFE0F`.

## 5. Algorithm

```python
# digits d0..d3 are 0..7 (displayed digit = value + 1)
packed = d0 | d1<<3 | d2<<6 | d3<<9          # 12 bits
r2 = packed >> 10                             # top 2 bits
v  = packed ^ (r2 * 0x155)                    # 0x155 = 0b0101010101
r6 = v & 1                                    # character: 0=Jerry, 1=Tom
r5 = (v >> 1) & 0xF                           # field written to 0x030063D4
r4 = (v >> 5) & 0x1F                          # field written to 0x03005754 area

valid = ((r6 + r5 + r4) & 3) == r2 \
        and r5 != 0 and 0 < r4 <= 14 and r4 != 6 \
        and (T3[r4] == r5 or T3[15 + r4] == r5)
```

On reject the game plays a sound and returns to character select. On accept it writes the globals, calls `0x08003D4` with `T2[r4]`, and starts a game (full routine at `0x0801D48A`–`0x0801D4F4`). The digit read-back is `tile = tileinfo & 0x3FF; digit = ((tile - 0x200) >> 4) & 7`.

## 6. Tables

```
T1 @0x08295910: 00 06 09 0C 0F 12 15 18 1B 1E 21 24 27 2A 2D
T2 @0x0829591F: 00 0C 0C 0C 0B 0B 15 0D 07 06 06 09 0E 0A 06
T3 @0x0829592E (3 rows of 15):
row0: 00 01 01 01 01 03 15 04 04 05 06 08 09 09 05
row1: 00 01 02 02 02 03 15 07 07 05 06 08 09 09 05
row2: 00 01 0F 0F 0F 0F 15 0E 0E 05 06 08 09 0F 0F
```
T3 entries of `0x15` (21) are unrepresentable by the 4-bit r5 and make that r4 row unusable.

## 6b. Enumeration

**Space definition.** Alphabet 8 symbols (`1`–`8`), length 4, no separators, no checksum character: **8⁴ = 4,096** representable inputs. Keypad physically offers exactly these 8 digits plus backspace and submit (no 0/9 — confirmed by font decode and by walking every keypad cell). Packing is 3 bits per digit = 12 payload bits; r2 is the top 2 bits and doubles as the 2-bit checksum target; r6/r5/r4 are 1/4/5-bit fields, of which r5 and r4 are range/table constrained.

**Validator model.** `decoder.py` reimplements the ROM routine bit-for-bit. It accepts all 12 published codes and rejects the two bounds-test codes, as observed in the emulator.

**Complete accepted set (36 codes).** `1111` is *not* accepted (verified as `r4==0` rejection). The accepted codes, with `(char, field5, field4)`:

```
4121(1,1,2)  5121(0,2,2)* 3521(0,1,3)  7531(0,3,5)* 2641(1,4,7)  1251(0,4,8)
8251(1,7,8)  5261(0,6,10) 2761(1,8,11) 4281(1,5,14) 1413(1,6,10) 5423(1,4,8)*
8143(0,9,12)* 1353(1,2,2) 2753(0,2,3)* 7753(1,1,3)  8383(0,1,4)  3783(1,3,5)*
2616(1,1,4)  7616(0,2,4)* 5126(0,7,7)* 1236(0,1,1)* 8246(1,2,3)  1456(0,9,13)
2856(1,9,12) 1176(0,5,9)  6718(0,5,14) 5228(1,9,13) 8238(0,8,11)* 5348(1,5,9)*
2748(0,7,8)  1358(1,7,7)  8358(0,4,7)  3868(1,2,4)  6878(0,1,2)* 5488(1,1,1)
```
`*` = appears in a published list (12 codes). **24 codes are novel** (not on 3rd party cheat indexes).

**Novel code proven in game.** `5488` → `(char=1, field5=1, field4=1)`: no published list gives Tom a level-1 code (published Tom codes begin at `3783` / Chapter 2). Entered on the keypad (`novel5488_pre.png`), accepted (`novel5488_result.png` — "Now Tom, you keep an eye on this magic ring…"), and RAM-verified: `0x03005340=0x01`, `0x030063D4=0x01`, `0x03005FFC=0x02`. A published control `3783` gave `0x03005340=0x01`, `0x030063D4=0x03`, confirming the decoder's field assignment. A second novel code, `6718` (`char=0, field5=5, field4=14`), is accepted (Jerry game starts) but loads corrupt level graphics — an accepted-but-unplayable combination, documented rather than counted as a useful unlock.

**Bounds proven by in-game rejection.**
- `8111` — passes the 2-bit checksum but has reserved field `r4=0`; typed correctly (`rej8111_confirm.png`) and rejected → character select (`rej_8111.png`). This proves the `r4 != 0` gate.
- `2111` — fails the checksum; rejected → character select (`rej_2111.png`).
- `1111` — checksum-valid but `r5=0` and `r4=0`; rejected.
- Digits `0` and `9` do not exist on the keypad (8 cells only), so 8⁴ is a hard input bound, not merely a validator bound.

**Counting argument.** With 4,096 inputs enumerated by the reimplemented validator, 988 are checksum-valid-but-table/range-invalid, 3,072 fail the checksum, and 36 pass everything. The 12 published codes are a subset of those 36; there is no hidden table beyond them.

## 7. Validation evidence

- **Observed:** all screenshots listed in §3; RAM reads via mGBA GDB stub (`ram_5488`, `ram_3783`); savestate diffs locating the digit cells at `0x03005354..0x0300536C`; OAM decode showing tile `0x200+(digit−1)*0x10`.
- **Derived:** validator algorithm, tables, field extraction and accept/reject branches from Thumb disassembly of `0x0801D38C` and `0x0801D5C4..0x0801D7D8`; the 36-code set from running the reimplementation over all 4,096 inputs.
- **Inferred:** `r6` is the character selector (Tom=1/Jerry=0) and `r5` the level field — supported by RAM writes and by published level labels, but the exact in-game semantic name of `r4` was not established. The article's "Chapter 2" for `3783` is observed; the mapping of other `r4` values to chapter names was not exhaustively played.

## 8. Unknowns

- `r4`'s exact meaning and the role of `T2[r4]` in level selection; `T1` is copied to the stack but no consumer was identified in the success path.
- Why `6718` (and other high-`r4` accepted codes) produce corrupt level graphics — probably `T2[r4]` pointing outside the level table, not proven.
- No debug menu or button code was found; bounded negative only (no ASCII debug strings in 8 MiB, three-option character-select ring, keypad handler has three actions). Game text is tile-based, so string absence alone is not conclusive — the negative rests on the full screen walk plus the complete keypad-handler disassembly.

## 9. Tooling

`/tmp/magicring/`: `decoder.py` (validator + exhaustive enumeration), `enter.py`/`mr.py` (deterministic keypad driver and 720×480 viewport capture), `testrun.py`/`ramverify.py`/`gdbdrv.py` (GDB stub harness), `ssdiff.py` (mGBA `gbAs` savestate diff), plus screenshots. Environment: Xvfb :316 + openbox, mGBA 0.10.5 SDL, `SDL_AUDIODRIVER=dummy`; tools otherwise as supplied (gdb-multiarch, arm-none-eabi-objdump, scrot, ImageMagick). No ROM or copyrighted assets are redistributed — addresses, hashes, algorithms and own scripts only.
