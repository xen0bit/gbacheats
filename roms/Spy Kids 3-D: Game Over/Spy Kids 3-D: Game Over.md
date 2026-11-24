# Spy Kids 3-D: Game Over (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Spy Kids 3-D: Game Over/Spy Kids 3-D: Game Over.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `SPY KIDS III` |
| Game code | `AV3E` (Europe) |
| Maker | `4Q` |
| Version | 0 (Rev.00) |
| Complement | 0x7B; header checksum 0x0000 |
| Entry word | `0xEA00002E` — **stock branch** (not a scene cracktro/patched header) |
| MD5 | `087a7620a5c7b7f69e09fd3b97a68c2f` |
| SHA-1 | `5e722deddbac98a9206278c914a16cf9ccab7ae4` |
| SHA-256 | `dd35eaf6b201558564e231c2520b06ca62d3672bc63d26639e577e57fbfe3447` |

Runtime identity: mGBA 0.10.5 boot splash "DIGITAL ECLIPSE SOFTWARE INC", title screen "SPY KIDS 3-D GAME OVER / PRESS START". Developer is Digital Eclipse (also confirmed from the boot splash and engine strings), not the PC version's InLight Entertainment (§16.11: verified by header/engine, not by franchise name).

## 2. Executive summary

This image has **one in-game developer-intended cheat surface**: a 4-character password screen reached from the main menu (`BONUS` / `PASSWORD`). The validator is a **closed hard-coded table of exactly six 4-symbol codes**. Each accepted code unlocks one 3D anaglyph "3D Gallery" image (numbers 10–15) and permanently sets one bit in a save flag word in EWRAM.

I recovered the on-screen alphabet and the character-index mapping, disassembled the validator, enumerated all six accepted inputs, re-typed all six in the emulator and confirmed each produces its distinct 3D image, read the unlock flag in RAM, and proved rejection bounds with near-miss codes. No button-code sequence, debug menu, or second password format exists in this image: the complete strings dump and the code were searched for those surfaces and none was found.

**No published in-game password list exists for this GBA title** — all web results are Action Replay/GameShark codes (out of scope). Therefore all six codes below are novel relative to every published list; each was minted from the ROM's own table and verified in-game.

## 3. How to reproduce

- Emulator: `SDL_AUDIODRIVER=dummy mgba -3 <rom>` under Xvfb; default SDL keymap (A=`x`, B=`z`, arrows = D-pad, Start=`Return`).
- Path: Title → **Start** → Main Menu → move down to the bottom row (`BONUS` / `PASSWORD`) → **A** → "ENTER CODE" screen.
- The screen has 4 empty slots and a 5×7 on-screen keypad:
  ```
  A B C D E F G
  H I J K L M N
  O P Q R S T U
  V W X Y Z 1 2
  3 4 5 6 7 8 9
  ```
- Move the cursor with the D-pad (Right = next column, Down = next row), press **A** to append a character. The code auto-submits on the 4th character. Valid → a 3D image appears; invalid → the header reads "INVALID!".
- Codes tested (all accepted): `KZ15`, `OZ23`, `JX21`, `ZR19`, `XK12`, `VX14`.
- Rejection tests (all "INVALID!"): `AAAA`, `KZ14` (one character off a valid code), `LZ15` (one character off a valid code).

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`) unless marked RAM.

| Address | Meaning | Evidence |
|---|---|---|
| `0x0807B084` | Base of the menu text bank (NUL-terminated strings) | Derived (pointer at `0x087F88DC`) |
| `0x0807B11C` | `"ENTER CODE"` string | Derived (u32 pointer at `0x0800F2A0`) |
| `0x0807B128` | `"INVALID!"` string | Derived (u32 pointer at `0x0800F3A0`) |
| `0x0807B1F4` | `"PASSWORD"` string | Derived (u32 pointer at `0x0800FCB4`) |
| `0x0807B20C` | Keyboard glyph/tile table (`0x4000`, `0x4001`, …) | Derived (u32 pointer at `0x0801021C`) |
| `0x0800EFEC` | Cursor (row, col) → character index mapper | Derived (BL at `0x0800F190`) |
| `0x0800F000` | **Password validator** — 6-entry closed table | Derived (BL at `0x0800F1AE`); observed accepts/rejects |
| `0x0800F0D0`–`0x0800F3C8` | Password screen input/render function | Derived |
| `0x0800F1AC` | Success path: sets save bit, calls gallery viewer | Derived (disassembly) |
| `0x08006D90` | 3D gallery image viewer (`r0` = validator return) | Derived (BL at `0x0800F1CA`) |
| `0x02000AD4` (EWRAM) | Unlock flag word; bit `N` set for code returning `N` | **Observed** via savestate diff: `0x0` → `0x200` after `KZ15` |
| `0x080311E4` | `"3D GALLERY"` string (in-game text bank) | Derived (`strings`) |
| `0x08031304` | `"LEVEL SELECT"` string (normal in-game menu, not a cheat) | Derived (u32 pointer at `0x080019C0`) |

Savestate layout used (§16.13): mGBA `.ss1` is a PNG with a zlib `gbAs` chunk; the 397,312-byte raw state maps IWRAM `0x03000000` → raw `0x19000` and EWRAM `0x02000000` → raw `0x21000`.

## 5. Algorithm

### 5.1 Character indexing (`0x0800EFEC`)

```
index = row * 7 + col        ; r0 = row (r7), r1 = col (sl)
if index > 25: index += 1    ; index 26 is skipped
return index
```

So the 35 keypad cells map to indices `{0..25, 27..35}`. Index 26 is unrepresentable.

### 5.2 Validator (`0x0800F000`)

The function receives `r0 = pointer to four 32-bit character indices`. It performs six unconditional comparison chains; each chain checks all four positions and returns a small integer on a full match. If no chain matches it returns `-1`.

```
if a==10 and b==25 and c==27 and d==31: return 9
if a==14 and b==25 and c==28 and d==29: return 10
if a==9  and b==23 and c==28 and d==27: return 11
if a==25 and b==17 and c==27 and d==35: return 12
if a==23 and b==10 and c==27 and d==28: return 13
if a==21 and b==23 and c==27 and d==30: return 14
return -1
```

### 5.3 Success effect (`0x0800F1AC`)

```
ret = validator(code)
if ret == -1: show "INVALID!"; keep code slots; return
save_word |= (1 << ret)          ; EWRAM 0x02000AD4
gallery_viewer(ret)              ; 0x08006D90 — shows image ret+1
clear the four slots; reset input count
```

The viewer adds 1 to the return for display (`0x08006D9C`: `r0 = r6 + 1`), which is why code 1 (ret 9) shows image **10**.

## 6. Tables

### 6.1 The complete accepted set

| # | Character indices | Code | Return | Save bit | Gallery image | In-game result |
|---|---|---|---|---|---|---|
| 1 | 10, 25, 27, 31 | `KZ15` | 9 | 9 (0x200) | 10 | Spy Kids 3-D logo (anaglyph) |
| 2 | 14, 25, 28, 29 | `OZ23` | 10 | 10 (0x400) | 11 | Futuristic motorcycle |
| 3 | 9, 23, 28, 27 | `JX21` | 11 | 11 (0x800) | 12 | Yellow/green racing cycle |
| 4 | 25, 17, 27, 35 | `ZR19` | 12 | 12 (0x1000) | 13 | Red hover-bike |
| 5 | 23, 10, 27, 28 | `XK12` | 13 | 13 (0x2000) | 14 | White robot |
| 6 | 21, 23, 27, 30 | `VX14` | 14 | 14 (0x4000) | 15 | Round droid/robot |

### 6.2 Index → character map (from the on-screen keypad)

| Index | Char | Index | Char | Index | Char |
|---|---|---|---|---|---|
| 0–25 | `A`–`Z` | 27 | `1` | 31 | `5` |
| 28 | `2` | 32 | `6` | 33 | `7` |
| 29 | `3` | 34 | `8` | 35 | `9` |
| 30 | `4` | 26 | *(unused — skipped by mapper)* | | |

## 6b. Enumeration

**Space definition.** The input surface is exactly 4 characters drawn from a 35-symbol alphabet (`A`–`Z`, `1`–`9`). Representable spellings: `35^4 = 1,500,625`. The game's internal character index set is `{0..25} ∪ {27..35}` (35 values; index 26 is unreachable — proved by the `if index > 25: index += 1` instruction at `0x0800EFF4–0x0800EFF8`). There is no checksum, no field layout, and no generator: this is a plain lookup table.

**Validator model.** Reimplemented exactly as shown in §5.2. It agrees with the ROM on all six accepted codes and on the three rejected near-misses below. Because the validator is a sequence of six fixed comparisons followed by `return -1`, the accepted set is **provably closed at six** by disassembly (§16.9: the complete accept set is enumerated from the code itself, not inferred from a partial table).

**Novel codes.** No published list of in-game passwords exists for this SKU: every web result (Cheat Happens, GBAtemp CHT databases, ROMSFUN save) is an Action Replay/GameShark code or a completed save, all excluded by scope. All six codes above were therefore minted from the ROM's own validator table and entered on the real screen; all six were accepted and produced their distinct gallery image. Evidence: `verify_KZ15.png`, `verify_OZ23.png`, `verify_JX21.png`, `verify_ZR19.png`, `verify_XK12.png`, `verify_VX14.png` (montage: `montage_codes.png`).

**Bounds proven by rejection.** Three inputs that the format can spell but the table does not accept were entered and all produced "INVALID!":
- `AAAA` (no code has repeated first character) — `reject_AAAA.png`
- `KZ14` (final index 32 instead of 31 — single-character near-miss of an accepted code) — `reject_KZ14.png`
- `LZ15` (first index 11 instead of 10 — single-character near-miss) — `reject_LZ15.png`

This proves the table is exact in all four positions and that there is no algorithmic/checksum bypass: a one-step change in any field is rejected. The index-26 hole is a bound of the input alphabet, not of the table (no accepted tuple contains 26).

**RAM proof of effect.** Savestate diff at EWRAM `0x02000AD4`: base `0x00000000` (no bits) → after `KZ15` `0x00000200` (bit 9 only), matching `1 << 9` from the success path at `0x0800F1C0–0x0800F1C6`.

## 7. Validation evidence

- **Observed** (emulator): title/menu walk; "ENTER CODE" and "INVALID!" screens; all six codes accepted with six distinct anaglyph images numbered 10–15; three near-miss codes rejected; save flag word `0x0 → 0x200` after `KZ15`.
- **Derived** (disassembly): character-index formula at `0x0800EFEC`; six-entry validator at `0x0800F000`; bit-set and gallery call at `0x0800F1AC`; image number = return + 1 at `0x08006D90`. Pointer xrefs for all UI strings.
- **Inferred** (low confidence): the remaining gallery images (1–9) are presumably the in-game artwork items mentioned in reviews; not exercised because they require gameplay collection, not a code. Not reported as a cheat.
- **Bounded negative**: 67,355 strings in the full ROM dump were searched case-insensitively for `password|cheat|debug|secret|code|unlock|bonus|level select`; the only cheat-related hits are the password-screen strings and normal in-game menu/credit strings. No debug menu, button-code sequence, or second validator was found. Web recon found only device codes (excluded). This is a "no system beyond the one found" result for the searched space, not an untested absence.

## 8. Unknowns

- Whether gallery images 1–9 have any code-based shortcut (none found; the six codes unlock only 10–15).
- The exact fate of save-bit words beyond bit 14 at `0x02000AD4` (bits 0–8 and 15+ were not observed to change).
- No second SKU was compared; addresses are for the `AV3E` European build only. The sibling "Spy Kids 3-D" analysis was not used as evidence.

## 9. Tooling

- `mgba` 0.10.5 (SDL, `-3`, headless under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`); `xdotool` for input (50 ms taps to avoid key-repeat double-stepping), `scrot` for captures.
- `arm-none-eabi-objdump -M force-thumb` for raw Thumb disassembly; Python + `struct` for pointer scans; Python `zlib` to extract the `gbAs` chunk from mGBA `.ss1` savestates for RAM diffs.
- Helper scripts in `/tmp/spykids3d/`: `enter_code.py` (navigates the keypad from the index map), `verify_all.py`, `reject_tests.py`, `ptrscan.py`, `textscan.py`, `bankscan.py`.
- Screenshots in `/tmp/spykids3d/` as named above. No copyrighted game assets are reproduced in this report.

## 10. Legal note

Only addresses, hashes, algorithms, and the six short character codes are published. No ROM data, graphics, or audio were extracted into the report.
