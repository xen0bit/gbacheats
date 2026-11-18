# Monster! Bass Fishing (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Monster! Bass Fishing/Monster! Bass Fishing.gba` |
| Size | 4,194,304 bytes (0x00400000) |
| Header title | `MONSTER BASS` |
| Game code | `A4BE` |
| Maker code | `7M` |
| Version | 0x00 |
| Entry word | `0xEA00002E` (stock branch to 0x080000C0) |
| Fixed 0x96 | present at 0xB2 |
| Nintendo logo hits | one, at file 0x00000004 — single retail image, no appended trainer |
| Header anomaly | complement byte at 0xBD = `0x60` (standard complement of 0xA0–0xBC = `0x79`); header checksum at 0xBE = `0x0000`. Rebuilt-header artifact; crt0 at 0xC0 is stock and code is unpatched. |
| MD5 | `b46ab3d1332497978488243d762ef5b8` |
| SHA-1 | `20b3bc7ba85f55f29d26c6e48b0e98777b9a95ad` |
| SHA-256 | `5403cf05a5f60fa18173420fc512e7278192638400bc7b788ce344e43cdd5939` |

## 2. Executive summary

The game has a **real, developer-intended password system** on the main menu. It is not a table of
preset codes: ROM functions `0x0800E460` (encoder) and `0x0800E774` (decoder/validator) implement a
**70-bit code with a 9-bit additive checksum**, carried by a 32-symbol alphabet. A code is 14
characters. It encodes a five-character angler name plus seven numeric fields (lake/tournament/
record values). The decoder validates the checksum, range-checks all 12 fields against a ROM-copied
table, writes the fields into a save-record structure, and returns to the main menu.

I reimplemented the codec in Python, generated codes absent from every published list, and confirmed
them on the real in-game screen: `638T--2JWGXY6K` (name `MONST`) was accepted and returned to MAIN
MENU; `XMFVH0T#0CV3TS` (name `AAAAA`) was also accepted. Corrupting one character to break the
checksum (`638T--2JWGXY6W`) produced the in-game `INVALID PASSWORD` screen, bounding the checksum.

No published password list exists for this SKU. TCRF carries only a CodeBreaker memory-edit code for
a crash handler, which is out of scope and is not a literal in the ROM. No hidden debug menu was
found; the only debug leftovers are crash-handler assertion strings.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, `DISPLAY=:315`, Xvfb + openbox, `-3` scale.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys.
* Path: boot → MAIN MENU (PLAY / OPTIONS / HI-SCORES / AQUARIUM / PASSWORD) → PASSWORD →
  `ENTER PASSWORD` keypad.
* Keypad indices are `row*9 + col` (verified against RAM `0x030052AF`/`0x030052B0`):
  rows 0–3 are `A..I`, `J..R`, `S..Z0`, `1..9`; row 4 cols 0–4 are `−`, `#`, delete, (reserved), accept.
  Navigate with the D-pad, press A to enter a character, press A on the green check to submit.
* **Important UI quirk:** the password buffer is *not cleared* when you leave and re-enter the
  PASSWORD screen. A full 14-character buffer silently ignores every further keypress (including
  navigation and accept). Reload a clean state or delete the old characters before trying another code.
* Screenshots: `/tmp/opencode/monsterbass/*.png` (accept proof: `novel_after.png`; rejection proof:
  `badchk_rejected.png`; keypad: `password1.png`; menus: `s1.png`, `options2.png`, `aquarium.png`,
  `hiscores_baseline.png`).
* Codec tool: `/tmp/opencode/monsterbass/pw.py` (`python3 pw.py <5-char-name> <12 fields csv>`).
  Keypad driver: `typepw.py`; savestate RAM reader: `ssdiff.py`.

## 4. Address map

### Code (ROM addresses)
| Address | Role |
|---|---|
| `0x0800E3EC` | bit writer (LSB-first into 5-bit slots, advances byte) |
| `0x0800E44C` | checksum = sum of 14 bytes |
| `0x0800E460` | **encoder** — name + state → 14-character password |
| `0x0800E6F4` | bit reader (reads high bit first, moves pointer *backwards*) |
| `0x0800E774` | **validator / decoder** — 14-char password → fields + return 0/1 |
| `0x0800E984` | keypad key dispatcher (index jump table at `0x0800E9BC`) |
| `0x0800E9D0` | accept handler; `BL 0x0800E774` at `0x0800E9D8` |
| `0x0800E9F0` | post-accept: writes decoded record into save structure (stride 0x58) |
| `0x0800EB40` | keypad update / navigation |
| `0x0800EAF6` | character append (max length 14; max check `cmp r2,#13`) |
| `0x08035538..0x08035558` | screen-state/function-pointer table (init/update/key/draw) |

### Tables copied to IWRAM at boot (from savestate, confirmed by ROM literals)
| Address | Contents |
|---|---|
| `0x0300140E` | alphabet[32] = `WRTYPSDFGHJKLZXCVBNM0123456789-#` |
| `0x030013EE` | key[14] = `63 85 3B 29 D7 11 22 FF 74 AF 50 57 68 C0` |
| `0x030050F0` | field table, 12 records of 8 bytes `{u8 bits, u8 max, u16 pad, u32 dest}` |
| `0x03005150` | 14-byte scratch / bit buffer |
| `0x03005294` | 5-character decoded name string |

### RAM state observed
| Address | Role |
|---|---|
| `0x0300529B` | password input buffer, 14 bytes (ASCII) |
| `0x030052AF` / `0x030052B0` | keypad cursor column / row |
| `0x030052B1` | password length |
| `0x030052AA..AE` | five name values (1..38) |
| `0x03002C2C`, `0x03002C14`, `0x0300529A`, `0x03004E70..73` | seven decoded field destinations |
| `0x03001370` | accept scratch flag, cleared by `0x0800E9D2` |

### Text / data banks
| Address | Contents |
|---|---|
| `0x0803CD91` | English string bank: `New Game`, `PASSWORD`, `INVALID PASSWORD`, `NEW PASSWORD`, `SECRET LAKE`, lake/lure names, `CREDITS` |
| `0x08033CC0..0x08033F90` | lake definitions (CRYSTAL LAKE, FOUNTAIN CREEK, OXBOW LAGOON, DEVILS LAKE, BLACKWATER POND, SPIRIT LAKE, `????`) |
| `0x080176C0..0x08017760` | debug/assert strings (`Invalid colour depth`, `stop code missing`, `Language not found!`, `There is not Detection code for this mode of operation`) |

## 5. Algorithm

### Decoder `0x0800E774(r0 = buffer) -> r0 (0 reject, 1 accept)`
1. For `i = 0..13`: find `v = alphabet.index(buffer[i])`; if not found (`v > 31`) → reject.
   `scratch[i] = v`.
2. For each `i`: even `i` → `scratch[i] = (scratch[i] − key[i]) & 0x1F`;
   odd `i` → `scratch[i] = (scratch[i] XOR key[i]) & 0x1F`.
3. Bit reader starts at `scratch[13]`, bit 4, and walks **backwards** through bytes and bits 4→0.
   Read 9 bits (first 1, then 8) as the checksum. Bits are cleared as read.
4. `expected = sum(scratch[0..11]) + (scratch[12] & 1)` (the 61 field bits). Compare with the
   9-bit checksum; mismatch → reject.
5. Walk the 12-entry field table in **reverse order** (entries 11..0). For each, read `bits` bits
   from the bitstream, check `value <= max`, store to the entry's destination pointer.
6. Convert the five name values to ASCII (`1..10 → '0'..'9'`, `11..36 → 'A'..'Z'`, `37 → '#'`,
   `38 → '−'`) and write the 5-character name. Return 1.

### Encoder `0x0800E460` (inverse)
1. Map five name characters to values (`'0'..'9'→1..10`, `'A'..'Z'→11..36`, `'#'→37`, `'−'→38`).
2. Write the 12 field values **in table order** with the bit writer (forward, 5-bit slots).
3. Append `sum(scratch) & 0xFF` then bit 8 of the sum (9 bits total).
4. Apply the key: even `i` → `(scratch[i] + key[i]) & 0x1F`; odd `i` → `(scratch[i] ^ key[i]) & 0x1F`.
5. Map each 5-bit value through the alphabet to produce the 14-character password.

Python reimplementation (`pw.py`) round-trips and agrees with the ROM on accepted/rejected inputs.

## 6. Tables

### Alphabet (32 symbols, index = 5-bit value)
`W R T Y P S D F G H J K L Z X C V B N M 0 1 2 3 4 5 6 7 8 9 − #`

### Key (14 bytes, applied to character index 0..13)
`63 85 3B 29 D7 11 22 FF 74 AF 50 57 68 C0`

### Field table (encoder write order; decoder reads 11→0)
| # | bits | max | destination | presumed meaning |
|---:|---:|---:|---|---|
| 0 | 6 | 38 | `0x030052AA` | name char 1 value |
| 1 | 6 | 38 | `0x030052AB` | name char 2 value |
| 2 | 6 | 38 | `0x030052AC` | name char 3 value |
| 3 | 6 | 38 | `0x030052AD` | name char 4 value |
| 4 | 6 | 38 | `0x030052AE` | name char 5 value |
| 5 | 4 | 8 | `0x03002C2C` | small selector |
| 6 | 3 | 5 | `0x03002C14` | small selector |
| 7 | 1 | 1 | `0x0300529A` | boolean flag |
| 8 | 7 | 78 | `0x03004E70` | record field A |
| 9 | 4 | 15 | `0x03004E71` | record field B |
| 10 | 7 | 78 | `0x03004E72` | record field C |
| 11 | 5 | 20 | `0x03004E73` | record field D |

## 6b. Enumeration

**Space definition.** 14 characters × 5 bits = 70 bits total. Layout = 9-bit checksum + 61 payload
bits (five 6-bit name values + 4+3+1+7+4+7+5 = 31 bits of state fields). The name alphabet is 1..38
(38 values), and each state field is range-checked against the table above. Number of distinct
payloads = `38^5 × 9 × 6 × 2 × 79 × 16 × 79 × 21 ≈ 1.79 × 10^16`; each has exactly one checksum
encoding, so the accepted set is ~1.8×10^16 of the 2^70 possible 14-character strings. All 32
alphabet symbols are permitted in every position except that the checksum and field ranges constrain
the decoded values; out-of-alphabet characters (`A`, `E`, `I`, `O`, `Q`, `U`) are rejected at step 1.

**Validator model.** Implemented exactly in `pw.py`; `decode()` cross-checks checksum and all field
bounds. It accepts every generated code and rejects single-character corruptions.

**Novel codes (not on any published list — none exists for this SKU):**

| Code | Encoded name | Encoded fields | In-game result |
|---|---|---|---|
| `638T--2JWGXY6K` | `MONST` | `0,0,0,0,0,4,3,1,50,7,60,10` | **Accepted** — screen transitioned from `ENTER PASSWORD` back to MAIN MENU (`novel_after.png`) |
| `XMFVH0T#0CV3TS` | `AAAAA` | all zero | **Accepted** — no `INVALID PASSWORD`; no visible flag change because all fields decode to the existing values |

**Bounds proven by rejection:**

| Code | Change | Result |
|---|---|---|
| `638T--2JWGXY6W` | single character changed → checksum fails | `INVALID PASSWORD` (`badchk_rejected.png`) |
| `AAAAAAAAAAAAAA` | `A` is not in the 32-symbol alphabet | `INVALID PASSWORD` (`test14A_after.png`) |
| `XMFVH0T#0CV3T` | 13 characters (truncated) | `INVALID PASSWORD` (`test13_after.png`) |

## 7. Validation evidence

* **Observed** (emulator/savestate): all screens in §3; input buffer at `0x0300529B`, length at
  `0x030052B1`, cursor at `0x030052AF/B0`; alphabet, key and field table read from decompressed
  `.ssN` `gbAs` chunks; valid novel code returning to MAIN MENU; three rejection cases.
* **Derived** (disassembly): full decoder/encoder, checksum, key schedule, bit order, field bounds,
  jump-table mapping of the accept key, post-accept save-record write at `0x0800E9F0`.
* **Inferred**: semantic labels of fields 5–11 (the decoder only proves bit widths and maxima);
  the post-accept record write at `0x0800E9F0` strongly suggests the code injects a ghost/tournament
  record, but the exact visible destination screen was not isolated.
* **Published codes**: web search found no password list. GameFAQs cheats page returns HTTP 403;
  archived TCRF (`Monster!_Bass_Fishing`) documents only `CodeBreaker 03002C00:08` (crash-handler
  debug flag — a memory-edit code, out of scope, and `0x03002C00` does not appear as a literal in
  this ROM). No fetched page contained instructions that were followed.

## 8. Unknowns

* Exact semantic meaning of the seven state fields; only widths/bounds are proven.
* The visible in-game effect of an accepted code beyond the screen transition and save-record write
  (candidate: injected hi-score/ghost entry). No save file persisted because the `.sav` was removed
  during cleanup.
* Debug gate `0x03002C00` (TCRF CodeBreaker code) was not activated — it requires memory editing,
  which is outside the in-game-cheat scope.
* Fully exhaustive enumeration of lake/tournament submenus was not completed; the main menu, options,
  credits, password, play-mode select, hi-scores, aquarium, and the in-game lake map/fishing screen
  were walked and RAM-verified.

## 9. Tooling

* Python 3 with `capstone` 5.0.7 and `keystone-engine`; `arm-none-eabi-objdump -M force-thumb`.
* mGBA 0.10.5 under Xvfb `:315` + openbox; `xdotool`, `scrot`, ImageMagick.
* mGBA `.ssN` savestates are PNGs with a zlib-compressed `gbAs` chunk; `ssdiff.py` decompresses it
  (397,312 bytes) and maps state offset `0x19000 + (RAM − 0x03000000)` to IWRAM.
* GDB stub and `-d` CLI debugger were attempted; the GDB stub proved unreliable (packet errors),
  so all RAM evidence came from savestate diffs.
* Scripts written: `pw.py`, `typepw.py`, `ui.py`, `ssdiff.py`, `lit.py` (all in `/tmp/opencode/monsterbass/`).

Legal note: no ROM bytes or copyrighted assets are reproduced here; only addresses, hashes, tables of
algorithmic constants, and original tooling are published.
