# Dora the Explorer: Super Spies (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Dora the Explorer: Super Spies/Dora the Explorer: Super Spies.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `DORA SUPER S` |
| Game code | `BERE` |
| Maker | `9G` |
| Version | 0x00 (Rev. 00) |
| Header checksum | 0x0000; complement byte 0x6B = −(Σ bytes 0xA0..0xBC + 0x19) — **intact header, not rebuilt** |
| Entry word | `0xEA00002E` (stock crt0 branch) |
| MD5 | `1975eda7d93cdb6d0828533dd34a05a7` |
| SHA-1 | `fa51e2102ce0a0e70c5db2f8776d2237c8d7db7d` |
| SHA-256 | `9a2bf17d3bb69efe5db9a9ca89f97456a0b9a27ed522257873730aa8205370cf` |

Embedded-header scan (156-byte Nintendo logo at header+4) found **exactly one** header at file offset `0x0`; no multiboot image, no appended trainer, no patched/cracktro entry.

## 2. Executive summary

This title has a **developer-intended password system** used as a continue/progress code, exactly as the manual describes ("Continue — Choose this option to enter your password and resume a previous game"). The entry screen is reached from **Main Menu → CONTINUE** and presents 7 slots plus a 16-icon on-screen keypad (2 rows × 8 columns) and a CONFIRM button. A code is 7 symbols from a 16-symbol alphabet.

The symbols are drawn from a custom font/tile alphabet, so `strings` finds **zero** keyword hits (`password`, `cheat`, `debug`, `secret`, `unlock`, etc. all 0 matches in 33,128 extracted strings and raw-byte searches).

**Checksum (verified):** with symbols numbered in keypad order (see §6), `s0 ≡ Σ(s1..s6) (mod 16)`. All 21 published/listed codes and all independently minted accepted codes satisfy this; a 1-symbol change that breaks it is rejected in-game.

There is a **second, semantic validation layer**: the payload `s1..s6` must decode to a legal game state. A checksum-valid but semantically invalid code is rejected with "INVALID PASSWORD". This layer is not fully reversed (see §8). Two codes absent from every published list were nonetheless minted, entered on the real screen, and **accepted** (§6b).

Published codes were verified against the ROM: 3rd party cheat indexes/3rd party cheat index lists were transcribed into the symbol alphabet, and representative codes were entered in the emulator. Codes that 3rd party cheat indexes themselves flags "Confirmed Doesn't Work" (e.g. 5-2, 5-3) were confirmed **rejected** here; others (1-2, 1-3, 4-2, 5-1, 6-3, 7) were accepted.

## 3. How to reproduce

- Emulator: `mgba -3 <rom>` under `Xvfb :315` with `SDL_AUDIODRIVER=dummy`; mGBA SDL keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
- Wait for the long intro/title (≈45 s from cold boot), press **Start**, then **Down** to CONTINUE, then **A** → "ENTER PASSWORD" screen.
- Password entry: D-pad moves the blue keypad cursor over the 2×8 icon grid (and a CONFIRM row); press **A** on an icon to write it into the white-boxed slot and advance the slot; then move to CONFIRM and press **A**.
  - A working control code: `Up Plus Triangle Star Plus Triangle Frown` (published "Rainforest 1-2"); screenshot `t_known.png` shows acceptance (world map returned).
- Deterministic test setup: a savestate parked at the password screen with slot cursor = 0 is `pw_slot0.ss1` (in the work dir); `mgba -3 -t pw_slot0.ss1 <rom>` reproduces every test below. A helper script `enter_code.py` enters a space-separated symbol code and screenshots the result.
- Rejection is visible as a red **"INVALID PASSWORD"** overlay in the centre of the screen; acceptance returns to the world map / continues the game.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| crt0 entry | `0x080000C0` (ROM `0xC0`) | header disassembly (`mov r0,#0xD2; …`) |
| Joypad read routine | `0x08012730` | Thumb disassembly: `ldr r0,[pc]` → `0x04000130`, `eors r1,r0` with `0x03FF` |
| Held keys (active-high) | IWRAM `0x03005840` | stored by joypad routine |
| Pressed-this-frame | IWRAM `0x03005844` | stored by joypad routine |
| Released-this-frame | IWRAM `0x0300583C` | stored by joypad routine |
| Password slot cursor (0..6) | IWRAM `0x03000314` | GDB RAM diff: 0→1 after one symbol placement; literal xrefs at ROM `0x12824`, `0x12844` |
| Packed password copies (28-bit, s0 in high nibble) | IWRAM `0x03000068`, `0x030000D8` | found in GDB RAM dump; `M` packet write changed bytes as expected (display is drawn from a different buffer) |
| World-map screen handler | `0x08012848` | `ldrb` + `ands r5,#7` (3-bit world index), 84-byte menu record stride |
| Generic menu handlers (8-item loops) | `0x080035xx`, `0x08006Cxx`, `0x0800E3xx` | `cmp r?,#7; bls` loops |
| String data | none for UI | all text is tile-index font data; `strings` keyword search returns 0 hits |

File offset ↔ ROM address: `rom_address = 0x08000000 + file_offset`.

## 5. Algorithm

**Alphabet (confirmed by successfully entering the published 1-2 code):** keypad read left-to-right, top row then bottom row:

| Value | Symbol | Value | Symbol |
|---:|---|---:|---|
| 0 | Triangle | 8 | Neutral face |
| 1 | X | 9 | Smile face |
| 2 | Up arrow | 10 | Frown face |
| 3 | Down arrow | 11 | Heart |
| 4 | Left arrow | 12 | Spiral square |
| 5 | Right arrow | 13 | Plus |
| 6 | Square | 14 | Star |
| 7 | Circle | 15 | Sun |

**Length:** exactly 7 symbols. **Checksum:** 4 bits, symbol 0 (first slot):

```
valid_checksum(s) = (s[0] == (s[1]+s[2]+s[3]+s[4]+s[5]+s[6]) & 0xF)
```

Equivalently `Σ(all seven) ≡ 2·s[0] (mod 16)`.

**Validator model (two layers):**
1. Checksum above (necessary; proven by rejection of a 1-symbol mutation).
2. Semantic decode of `s1..s6` to an in-range game state (level / progress / gadget flags). Not fully reversed — see §8. Both layers must pass for the game to leave the password screen; a failure shows "INVALID PASSWORD".

**Input semantics (§16.6):** placement is edge-triggered per A press; the slot cursor advances after each placement and the keypad cursor is a (row, col) position in a 2×8 grid plus a CONFIRM row.

## 6. Tables

**Published codes transcribed into symbol values** (all satisfy the checksum). `✓` = accepted in emulator, `✗` = rejected in emulator, `—` = not individually tested:

| Level (published label) | s0 s1 s2 s3 s4 s5 s6 | Result |
|---|---|---|
| 1-1 (default shown on fresh screen) | 3 13 1 14 13 0 10 | ✓ |
| 1-2 | 2 13 0 14 13 0 10 | ✓ |
| 1-3 | 15 13 1 14 9 0 10 | ✓ |
| 2-1 | 14 13 0 14 9 0 10 | — |
| 2-2 | 9 13 1 14 5 0 8 | — |
| 2-3 | 8 13 0 14 5 0 8 | — |
| 3-1 | 5 13 1 14 1 0 8 | — |
| 3-2 | 4 13 0 14 1 0 8 | — |
| 3-3 | 9 13 1 12 5 0 10 | — |
| 4-1 | 8 13 0 12 5 0 10 | — |
| 4-2 | 11 13 9 8 2 8 3 | ✓ |
| 4-3 | 15 13 9 8 6 10 1 | — |
| 5-1 (All Gems 2-3) | 13 13 9 8 6 8 1 | ✓ |
| 5-1 (All Gems 3-2) | 6 4 9 8 6 10 1 | — |
| 5-2 (All Gems) | 13 4 12 8 6 14 1 | ✗ (3rd party cheat indexes marks "Doesn't Work") |
| 5-3 (All Gems) | 12 4 15 8 2 14 1 | ✗ (3rd party cheat indexes marks "Doesn't Work") |
| 6-1 (All Gems) | 15 4 14 8 2 14 5 | — |
| 6-2 (All Gems) | 12 0 15 2 6 14 7 | — (3rd party cheat indexes marks "Doesn't Work") |
| 6-3 (All Gems 6-1) | 11 0 14 2 6 14 7 | ✓ |
| 6-3 (All Gems 6-2) | 13 2 14 2 6 14 7 | — |
| 7 Tico's Workshop | 14 2 14 2 6 15 7 | ✓ |

**Symbol→key map for emulator:** Triangle=`—` (keypad only), Up=`Up`, Down=`Down`, Left=`Left`, Right=`Right`, etc.; face/shape symbols are selected from the on-screen keypad, never from the controller buttons.

## 6b. Enumeration

**Space definition**

- Alphabet size: 16; length: 7 → total spellings `16^7 = 268,435,456` (2^28).
- Checksum width: 4 bits at s0 → `16^6 = 16,777,216` spellings pass the checksum (1/16 of all spellings).
- Semantic layer reduces this further to a set of states the game can decode (level/progress); exact cardinality not established (§8).

**Novel code 1 (not in 3rd party cheat indexes, or any wiki):**

```
Heart Plus Smile Star Plus Triangle Frown
= [11, 13, 9, 14, 13, 0, 10]
check: 13+9+14+13+0+10 = 59 = 0x3B -> 0xB = 11 = s0  OK
```

Generated by taking published 1-2's payload and replacing s2 (0→9), then recomputing s0. Entered on the real password screen; **accepted** (returned to world map). Screenshot: `s2_9.png`. This exact 7-symbol combination appears in no published list.

**Novel code 2 (independent confirmation):**

```
Circle Plus Smile Star Smile Triangle Frown
= [7, 13, 9, 14, 9, 0, 10]
check: 13+9+14+9+0+10 = 55 = 0x37 -> 0x7 = 7 = s0  OK
```

Entered on the real screen; **accepted**. Screenshot: `bt_novel2.png`.

**Bounds proven by rejection**

| Test | Code / change | Result |
|---|---|---|
| Wrong checksum | Accepted novel 1 with s0 changed 11→10: `Frown Plus Smile Star Plus Triangle Frown` = `[10,13,9,14,13,0,10]` | **REJECTED** ("INVALID PASSWORD") — proves the 4-bit checksum is mandatory |
| Out-of-range field (s2) | `[4,13,2,14,13,0,10]` (`Left Plus Up Star Plus Triangle Frown`), checksum valid, s2=2 | **REJECTED** — proves semantic range check on the payload |
| Out-of-range field (s2) | `[5,13,3,14,13,0,10]`, s2=3 | **REJECTED** |
| Out-of-range field (s2) | `[0,13,14,14,13,0,10]`, s2=14 | **REJECTED** |
| Out-of-range field (s2) | `[7,13,5,14,13,0,10]`, s2=5 | **REJECTED** |
| Out-of-range field (s1) | s1 ∈ {0,2,4,8} with 1-2 payload | **REJECTED**; only s1=13 works with that payload |
| Out-of-range field (s3) | s3=10 with 1-2 payload | **REJECTED**; s3 ∈ {2,8,12,14} accepted with same payload |
| Published bad code | 5-2 `Plus Left Spiral Neutral Square Star X` | **REJECTED** (matches 3rd party cheat indexes "Confirmed Doesn't Work") |
| Published bad code | 5-3 `Spiral Left Sun Neutral Up Star X` | **REJECTED** (matches 3rd party cheat indexes "Confirmed Doesn't Work") |

The accepted/rejected boundary on s1/s2/s3 depends on the *combination* of fields (a value rejected with one payload is accepted in a published code with a different payload), so the semantic layer decodes a compound state rather than checking fields independently.

## 7. Validation evidence

- **Observed:** all screenshots (title, main menu, options, pause, level-select, world map, password screen, INVALID PASSWORD overlay); 1-2 code accepted; two novel codes accepted; 9 rejection cases; RAM dumps through the GDB remote protocol; slot cursor 0→1 RAM diff.
- **Derived:** checksum equation `s0 = Σ(s1..s6) mod 16`, solved with Z3 from published codes and re-verified against all 21 listed codes and both minted codes; symbol→nibble mapping from keypad layout, confirmed by entering a published code; joypad variable addresses from Thumb disassembly at `0x08012730`.
- **Inferred:** the second (semantic) validation layer exists and decodes a compound level/progress state; its exact field layout is unresolved. The exact level index loaded by the two novel codes was not read back (the world-map return is the observed effect).

## 8. Unknowns

- The exact semantic decoder for `s1..s6` (field widths, level index, gem/gadget bit layout) was not recovered; Ghidra/REA decompilation of the password screen handler was not completed in this session. A validator model that predicts *all* accepted spellings offline is therefore incomplete (checksum layer complete; semantic layer empirical only).
- The precise level/episode and gem/gadget state granted by the two novel codes (acceptance and world-map return are proven; the decoded state was not read from RAM).
- The validator function's ROM address and the display-buffer address for the 7 slots were not identified; static scans for a `cmp #7` + `ldrb` checksum loop produced only generic 8-item menu handlers.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm -M force-thumb` (joypad and menu disassembly).
- `capstone` 5.0.7 (candidate checksum-loop scans).
- `z3-solver` (checksum equation solving and symbol-mapping constraints).
- mGBA SDL under `Xvfb :315` + `openbox`; `xdotool` XTEST key events; `import`/`convert` for screenshots; ImageMagick `mean.r` over the overlay region as an accept/reject detector (>0.75 ⇒ INVALID).
- Raw GDB remote protocol client over mGBA's `-g` stub (`m`/`M` packets) for RAM reads/writes (the stock `gdb-multiarch` client hit stub-negotiation errors; raw packets worked).
- mGBA savestates (`gbAs` PNG chunk, zlib-decompressed to a 397,312-byte raw state) for RAM diffing and deterministic test setup (`pw_slot0.ss1`).
- Web: 3rd party cheat index cheats page, 3rd party cheat index cheats page, PrinceWatercress playthrough blog, 3rd party cheat indexes scanned manual (OCR via `tesseract`).

## 10. Legal note

No ROM, graphics, audio, or extracted game assets are redistributed here. Only hashes, addresses, algorithms, and original test codes are published.
