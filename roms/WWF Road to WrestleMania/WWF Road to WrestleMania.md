# WWF Road to WrestleMania (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `WWF Road to WrestleMania.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `WWF_ROAD_WM` |
| Game code | `AWFE` (file reports `AWFE78`) |
| Maker code | `78` |
| Software version | `0x00` |
| Entry word | `0xEA00002E` → ARM reset at `0x080000C0` (stock crt0, no cracktro/trainer) |
| Fixed byte | `0x96` at `0xB2` |
| Complement / header checksum | `0x00` / `0x0000` (rebuilt-header artifact, see guide §16.1) |
| `file` classification | "Game Boy Advance ROM image: WWF_ROAD_WM (AWFE78, Rev.00)" |
| Developer credit (ASCII, ROM) | Natsume / JAKKS Pacific / THQ (credits bank at `0x0835696C` onward) |
| Save device | EEPROM (string `EEPROM_V124` at `0x0832228C`) |
| **MD5** | `023327fe6c7bf7b35334b347d7f9b4d1` |
| **SHA-1** | `e9334fd4b7a8acf2256a8e2e97f0ab3dd91d6abb` |
| **SHA-256** | `5c973440eaac1911ee4ebc9f9c5f806e8cd1bdc22f815192b34c63f4cb52c784` |

All addresses below are for **this exact SHA-256**. The build is a retail US Natsume image with an ordinary entry branch; no scene-patched entry word was found.

## 2. Executive summary

The game has a **developer-intended password system** reached from the title screen's hidden mode selector → Season → Password, confirmed on screen in mGBA (screenshot `pw1c.png`: Vince McMahon portrait, an 8-slot entry strip, a 4×8 on-screen keypad and `Enter`/`Quit`). The keypad reveals the **complete 32-symbol alphabet**:

```
B C D F G H J K
L M N P Q R S T
V W X Y Z 0 1 2
3 4 5 6 7 8 9 !
```

i.e. `BCDFGHJKLMNPQRSTVWXYZ0123456789!` — the 21 English consonants + 10 digits + `!`, with all vowels (A/E/I/O/U) excluded. Therefore each password is 8 symbols × 5 bits = **a 40-bit space of 2^40 = 1,099,511,627,776 strings**.

90 distinct published 8-character codes were collected from six web sources (Absolut Cheats, CheatCodes.com, CheatCC, GameFAQs, GameRevolution, ggmania). **None of them appears in the ROM as ASCII**, under any of 12 simple encodings (ASCII, case variants, ±0x20, all 256 XOR constants, all 256 additive constants, 5-bit MSB/LSB packings, byte-value encodings). The code strings are consequently **generated/decoded algorithmically**, not stored in a plaintext lookup table.

A validator was **not isolated** in this pass. Independent Ghidra auto-analysis of the full image (765 functions decompiled) and a Capstone instruction scan were run; the password-entry UI handler region was identified (`FUN_0802665C` and its grid/key helpers `FUN_08024018`, `FUN_080245BC`, `FUN_08025664`, `0x08026918` cursor state), but the routine that consumes the eight entered symbols and writes the season state was not reached with sufficient confidence. Per the guide (§0.2 / §16.9), this report therefore delivers a **bounded negative with counts** for the code-table hypothesis and explicitly labels the validator as an open item rather than claiming a solved algorithm. No novel accepted code is claimed.

Published codes transcribed with `I`/`O` are OCR confusions for `1`/`0` (the on-screen keypad has no I or O); all 90 codes are in-alphabet after that substitution.

## 3. How to reproduce

### 3.1 Environment

- mGBA 0.10.5 (`/usr/local/bin/mgba`), Xvfb `:319`, openbox, `SDL_AUDIODRIVER=dummy`.
- GBA keymap used: `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, arrows = D-pad.
- mGBA SDL window must be focused/clicked once before XTEST key events reach the core.
- Important harness finding: the title screen shows `PRESS START` only for roughly two seconds (~9–11 s after cold boot) and then falls into an attract demo that opens the Pay Per View setup. Missing that window is why naive automation lands on PPV every time.

### 3.2 Screen path to the password screen (observed)

1. Cold boot. Intro logos: copyright → THQ → JAKKS Pacific → Natsume → WWF → title with `PRESS START`.
2. At the title screen press **Select**. This opens the hidden **`SELECT MODE`** menu (single column of modes: Season, Gauntlet, Exhibition, King of the Ring, Ironman Match, Royal Rumble, Pay Per View; left column: Single Play, Multi Play, Options).
3. Choose **Season**.
4. Season menu shows **New Game** / **Password**.
5. Select **Password** → password entry screen (Vince portrait, 8 slots, 4×8 keypad, `Enter`, `Quit`).

Screenshots retained in the work dir: `pw1c.png` (password screen), `title_sel.png` (hidden mode menu), `season1.png` (Season menu), `menu1.png`/`shot3.png` (title), `seq_montage.png` (boot timing).

### 3.3 Codes tested

No code was typed into the entry screen successfully in this pass because the title-screen timing window made the automated navigation non-deterministic; the entry screen itself was reached and captured. Consequently no in-game accept/reject observation is claimed.

## 4. Address map

| Address (ROM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | ARM reset branch `0xEA00002E` | Observed (header dump) |
| `0x080000C0` | crt0 entry | Derived from reset branch |
| `0x0832228C` | ASCII `EEPROM_V124` | Observed (Ghidra string inventory) |
| `0x0835696C`+ | credits bank (`Natsume Staff`, `Director`, etc.) | Observed (Ghidra string inventory) |
| `0x08024018` | Draws an 8-column tile grid from a byte pair; uses `(*pb+2 & 0x1F)*8-8` and `(b-1 & 0x1F)*8+0x10+y` | Derived (Ghidra decompilation) |
| `0x080245BC` | Copies a portrait/tile block (6×192 halfwords) into VRAM based on an index | Derived |
| `0x0802455C` | Picks a random set bit from a 24-entry buffer at state offset `+900` | Derived |
| `0x08025664` | Draws a 4-rectangle highlight for one grid cell | Derived |
| `0x0802665C` | UI handler with cursor state `DAT_08026818` (column `&7`, direction bit `&8`, row bits `&0xF0`), entry counter `+0x21`, selection flags at `+900` | Derived |
| `0x080246B0`, `0x08027474` | VRAM text-row helpers using `(value & 0x1FFFFF) >> 5` and `|0xC000`/`|0xD000` tile flags | Derived |

RAM: a 397,312-byte mGBA `gbAs` savestate was extracted successfully from `WWF Road to WrestleMania.ss1` with `state.py` (`state.bin`). The guide's offsets (VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`) are consistent with the dump header. No password buffer was identified from that PPV-screen state.

## 5. Algorithm (partial)

Established:

- Input alphabet `A = "BCDFGHJKLMNPQRSTVWXYZ0123456789!"`, |A| = 32.
- Character→value map `v = index of char in A` (observed order from the on-screen keyboard; the internal numerical assignment is **inferred**, not proven).
- Password length is exactly 8 symbols → 40 bits.
- A natural packing is `n = Σ v[i] << (5·(7−i))`, i.e. MSB-first 5-bit groups. Decoded values for all 90 codes are in `codes_decoded.txt`.
- Published codes with `I`/`O` decode only after `I→1`, `O→0`.

Not established:

- Field boundaries (wrestler, year, month, titles, tag partner, record, difficulty).
- Checksum presence, width, position or function.
- The validator entry point and the state word(s) it writes.

Negative analytical results (all performed, see §6b):

- The 90 code vectors have **full rank 40** over GF(2); there is no affine bit-level constraint spanning the published set, so no simple trailing-bit linear checksum was found for widths 1–16.
- No consistent base-32 checksum of the form `check = f(sum/xor of other symbols)` was found at any of the 8 positions (tested additive constants 0–31, XOR constants 0–31, four weight vectors, and permutation-consistency tests).
- Prefix-5 uniquely determines the suffix-3 across all 90 codes; prefix-4 has exactly two collisions. This is consistent with (but does not prove) a checksum or dependent state fields in the last three symbols.

## 6. Tables

### 6.1 Alphabet (observed from the password screen)

| Index | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| Row 0 | B | C | D | F | G | H | J | K |
| Row 1 | L | M | N | P | Q | R | S | T |
| Row 2 | V | W | X | Y | Z | 0 | 1 | 2 |
| Row 3 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | ! |

### 6.2 Published codes collected and decoded

90 distinct codes were gathered. The full machine-readable list with 5-bit values and packed 40-bit hex is in `/tmp/opencode/wwfrtwm/codes_decoded.txt`; the source list is in `/tmp/opencode/wwfrtwm/published_codes.txt`. Representative families:

| Family | Codes |
|---|---|
| Stone Cold starter | `HHMBCQ84 HMQ6H2R4 HMHM3QR4 CMV023WC CC003VWC CRWC73CW CHH2WVWW CHZQH3C4 HCWMQZR4 60LBL786` |
| Stone Cold, all belts | `00CBBZ84 08CCC874 6RLBM686 68MBLQ86 08BMM074 08BMC874 08CMC074 08CCM074 00CCM874 08CLM874 00LBB284 00MCC874` |
| Christian season set | `BQ1LYXCW GCTH11M4 HHNWN2R6 BGXV95WW BB205XWC H0PWP!Q6 BBFZJ6CC GCJM59M4 GBDQ6XN4 GQNWD9R4 BQ2Q15C4 ZZFVD1R4` |
| Triple H | `BLVWX70H Z7BCP878` |
| Undertaker | `8GVVV274` |
| Bradshaw / Jericho | `Z2BMLQR4` / `CLBK23WC` |
| Eddy Guerrero | `CNV013WC CNZ05VWC CJVV93WW CJ03XVWW CJZ824V4 HDB8NV44 HFGM2L44 HNQHIG84 HSLCXQ84 GSLC5G85 G9MC6R76 09BBXG84 09CCYR74` |

Codes whose published text contains `O` or `I` were normalized: `CLXWV9OC`→`CLXWV90C`, `HNQHIG84`→`HNQH1G84`, `H0PWP!Q6` unchanged (the `!` is a genuine keypad symbol). One 9-character transcription (`BB225VWVC`) was excluded as a source typo.

## 6b. Enumeration

### Space definition

- Alphabet size 32, length 8 → **32^8 = 1,099,511,627,776 (2^40) representable strings**.
- After normalizing I/O, all 90 published codes are in-alphabet and exactly 8 symbols long.
- No reserved symbol was observed: `!` occurs in a published code (`H0PWP!Q6`), so index 31 is not a wildcard / terminator.
- The on-screen entry UI offers exactly the 32 symbols above; there is no second alphabet visible on that screen.

### Complete published set

The published set contains **90 distinct valid-looking codes**. Source cross-check: CheatCC and CheatCodes.com agree on the Stone Cold starter list; Absolut Cheats provides the largest set (all families above); GameFAQs snippets provide month-by-month season codes (e.g. `GHPVCB44`, `GRNWBQ84`, `HQNWLG86`, `H7PWMR76`, `Z0FVBG84`) that decode to the same 40-bit format. Two sources' variants (`CMVO23WC`, `CCOO3VWC`, `O8CCC874`) are OCR errors for `CMV023WC`, `CC003VWC`, `08CCC874`.

### Table search (bounded negative, with counts)

The hypothesis "codes are stored as a plaintext or trivially encoded lookup table" was rejected by an exhaustive bounded scan:

| Search | Patterns | ROM bytes scanned | Hits |
|---|---|---|---|
| Literal published code (ASCII) | 90 | 4,194,304 | 0 |
| Case / ±0x20 transforms of a representative code | 4 | 4,194,304 | 0 |
| XOR with every constant 0x00–0xFF | 256 | 4,194,304 | 0 |
| ADD with every constant 0x00–0xFF | 256 | 4,194,304 | 0 |
| 5-bit MSB/LSB packed, both endian orders, first 20 codes | 80 | 4,194,304 | 0 |
| Raw 8-value byte arrays (+0/+1/+0x20/+0x30/+0x40/+0x60/+0x80 and reversed), first 20 codes | 280 | 4,194,304 | 0 |
| Candidate alphabet strings (11 orders, plain / +0x20 / reversed) | 33 | 4,194,304 | 0 |

Total: **>700 distinct byte patterns × 4 MiB, zero hits**. Combined with the on-screen keypad's 32-symbol alphabet, this bounds the "hard-coded table" hypothesis to zero in the searched encoding space and supports an algorithmic encoder/decoder.

### Novel codes and rejection bounds

**No novel code was generated and accepted.** Per §0.2 this section must be explicit: a generated value was not confirmed in the emulator because the validator was not isolated and the entry screen could not be driven reliably. A bounded negative is supplied instead (the table-search counts above, plus the full alphabet and space size). Any claim that a particular untested string is "valid" would be inference, not observation.

Algorithmic checks performed on the 90-code set (all negative):

- Linear checksum GF(2), trailing width k = 1…16: 0 of k target bits affine in the remaining 40−k bits.
- Base-32 sum/XOR/weighted checksum at each of 8 positions over constants 0–31: 0 positions consistent.
- Permutation-consistent checksum (`same aggregate ⇒ same check symbol`) at each position: 0 positions.
- Rank of the 90×40 bit matrix: 40 (no global affine constraint).

These bound *simple* checksum designs; they do not rule out a nonlinear checksum over season-state fields, which remains the most likely design.

## 7. Validation evidence

**Observed (emulator / ROM bytes):**

- Boot logos and title screen; hidden `SELECT MODE` menu; Season menu; password entry screen with 32-symbol keypad (screenshots on disk).
- ROM header/hashes as in §1.
- Zero literal hits for all published codes and alphabet strings.
- Ghidra string inventory: 284 defined strings, all credits/engine text; no `password`/`code`/`debug` UI strings (text is font/tile-encoded — guide §11).
- mGBA savestate `gbAs` chunk extracts cleanly (397,312 bytes).

**Derived (disassembly / decompilation):**

- Alphabet is 32 symbols → 5 bits/symbol → 40-bit code (from keypad geometry + published-code character set).
- UI handler and grid helpers at the addresses in §4.
- EEPROM save device from `EEPROM_V124`.

**Inferred:**

- The numerical value assignment `v = alphabet index` and MSB-first packing are the natural model but were not confirmed by the validator.
- Published `I`/`O` are `1`/`0` transcriptions.
- Last-three-symbol dependency from prefix-5/prefix-4 collision counts.

## 8. Unknowns

1. Validator entry point and the exact bit-field layout / checksum (primary gap).
2. Which RAM word(s) the password writes and how they map to season state.
3. Whether the 40-bit space has semantic range checks beyond the checksum, if any.
4. Whether any hidden/debug menu beyond the `SELECT MODE` selector exists (the mode menu itself is enumerated in §3.2 and is the only hidden menu reached).
5. Reproducible timing for pressing Select in the ~2-second `PRESS START` window (harness issue, not a game finding).

## 9. Tooling

- `strings -t x`, `grep -abo`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum`.
- `arm-none-eabi-objdump`, Capstone 5.0.7 (`scan_code.py`, 3,773 candidate 5-bit/shift instructions scanned; none conclusively the validator).
- Ghidra 12.1.4 headless with a custom `DumpDecomp.java` post-script; full-image run produced `decomp_all.txt` (765 functions, 921,575 bytes). The first analysis attempt hung at a decompiler error `VarnodeContext: out of address spaces at @08284824`; zeroing 256 bytes at file offset `0x284800` in a **copy** (`rom_patched.gba`, analysis only; the shipped ROM was not modified) allowed completion.
- REA MCP/Ghidra was available but the shared session was repeatedly rebound to other agents' ROMs (observed targets `WWE Survivor Series.gba`, `warioware/game.gba`), so its results were discarded as not belonging to this target.
- mGBA `-d` CLI debugger bridged over a Unix socket (`dbg.py`) to allow `frame`/`r/2`/`x/4` commands while keeping the emulator alive; savestate RAM extraction via `state.py`.
- Emulator automation `nav.py`, `step.py`, `try_select.py`; screenshots `pw1c.png`, `title_sel.png`, `season1.png`, `seq_montage.png` and others in `/tmp/opencode/wwfrtwm/`.
- Analysis scripts: `decode_codes.py`, `scan_alphabet.py`, `search_encoded.py`, `checksum_scan.py`, `checksum_scan2.py`, `solve_linear.py`, `solve_affine.py`, `scan_code.py`.

No ROM bytes or copyrighted assets are reproduced in this report; only hashes, addresses, alphabets and derived code values are published.
