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
| Entry word | `0xEA00002E` → ARM reset at `0x080000C0` (stock crt0) |
| Fixed byte | `0x96` at `0xB2` |
| Complement / header checksum | `0x00` / `0x0000` (rebuilt-header artifact) |
| `file` classification | "Game Boy Advance ROM image: WWF_ROAD_WM (AWFE78, Rev.00)" |
| Developer credit (ASCII, ROM) | Natsume / JAKKS Pacific / THQ |
| Save device | EEPROM (string `EEPROM_V124` at `0x0832228C`) |
| **MD5** | `023327fe6c7bf7b35334b347d7f9b4d1` |
| **SHA-1** | `e9334fd4b7a8acf2256a8e2e97f0ab3dd91d6abb` |
| **SHA-256** | `5c973440eaac1911ee4ebc9f9c5f806e8cd1bdc22f815192b34c63f4cb52c784` |

All addresses below are for this exact SHA-256.

## 2. Executive summary

The game has a **developer-intended 8-symbol password system** reached from the title screen's hidden mode selector → Season → Password. The complete alphabet is the 21 consonants + 10 digits + `!` (32 symbols, 5 bits each → 2^40 strings). The password UI, input buffer, validator, and its complete accept predicate have all been isolated and reimplemented.

**Validator isolated** (this pass, REA/Ghidra decompilation + Capstone/objdump + runtime watchpoint):

- `0x0801AD74` — `FUN_0801ad74`, the accept/reject **gate**: rejects any of the 8 buffer bytes equal to `0xFF` (blank slot), then calls `FUN_0801a9d0`; `r0 == 0` means accept, `-1` means reject. On accept it runs `FUN_0801a3ac(DAT_0801adf4,0,0,1)` to change screen and sets season-state bytes.
- `0x0801A9D0` — `FUN_0801a9d0`, the **password decoder/validator**: an 8-bit additive checksum plus seven independent bit-field decodes with explicit range checks. Full algorithm in §5.

The validator was found by setting mGBA's *native* debugger read-watchpoint on the discovered input buffer (`watch/r 0x0200800F`); it caught reads at `0x0801AE00` (the slot-drawing routine) and, through the xref chain, the gate at `0x0801AD74` and the validator at `0x0801A9D0`.

**Codes accepted on the real screen:**

- Published `H0PWP!Q6` — entered keypad-by-keypad with XTEST, accepted; screenshot `typed_code.png` (8 symbols shown) → `after_enter.png` (Vince McMahon WrestleMania cutscene: "I want this to be a WrestleMania match that is never forgotten"). Buffer RAM read at that moment: `05 15 0b 11 0b 1f 0c 1b`.
- **Novel, previously unpublished** `C24G6!L!` — generated from the recovered validator with field vector `{A=44,B=19,C=22,D=42,E=15,F=1,G=1}`; entered with XTEST and **accepted**, screenshot `novel_ready.png` (code displayed) → `reject_near.png` (same WrestleMania cutscene). The font renders `G` almost identically to `6`, so the on-screen slots read "C2466!L!" — the underlying symbols are `C24G6!L!`. This code is in none of the six published sources.

**Rejection bounds proven on-screen:** an in-alphabet, checksum-invalid 8-symbol string produced the red **INCORRECT** message (`novel_typed_ok2.png`), and the algorithm enumerated in §5 gives the exact byte-level accept predicate (wrong checksum, field A≥12, field B≥24, field C∈25..30, B==C, D≥100, `E&8 && C==0xFF`, F≥3, `G && D≤9` all reject).

Screenshots and analysis scripts live in `/tmp/opencode/wwfrtwm2/`, **not** in the ROM folder.

## 3. How to reproduce

### 3.1 Environment

- mGBA 0.10.5 (`/usr/local/bin/mgba`), Xvfb `:319`, openbox, `SDL_AUDIODRIVER=dummy`.
- GBA keymap: `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, arrows = D-pad. Verified at the joypad register `0x04000130`: `x→0x03FE` (bit0), `z→0x03FD` (bit1), `BackSpace→0x03FB` (bit2), `Return→0x03F7` (bit3), `a→0x01FF` (bit9), `s→0x02FF` (bit8).
- **The "2 s PRESS START window" is a harness artefact, not a game gate.** A deterministic route is: from the running game write the menu state byte `0x030016DC = 2` (`SELECT MODE`) with the debugger, press A (Season), Down, A (Password), then A again. Alternatively press Start at the title at any time and use the debugger write. No timing-critical input is needed.
- Input helper that worked: keydown/keyup with a ~45 ms hold and ~55 ms gap (`typecode2.py`). Holding keys ≥200 ms triggers X key-repeat and corrupts navigation; B-button "clear" loops can exit the screen — clear by re-entering the password screen instead.

### 3.2 Screen path

1. Boot → logos → title (`PRESS START`).
2. Hidden `SELECT MODE` menu (left: Single Play / Multi Play / Options; right: Season, Gauntlet, Exhibition, King of the Ring, Ironman Match, Royal Rumble, Pay Per View).
3. Season → **New Game / Password** → Password.
4. Password screen: Vince portrait, **8 slots**, **4×8 keypad** (`BCDFGHJKLMNPQRSTVWXYZ0123456789!`), `Enter` / `Quit`.
5. Type 8 symbols (A selects, arrows move, B deletes), highlight `Enter`, press A: accept → WrestleMania cutscene; reject → `INCORRECT` in the slot strip.

### 3.3 Exact reproduction of the novel code

With the cursor at `B` (row0,col0), key sequence for `C24G6!L!`:

| Symbol | cell (row,col) | moves from previous |
|---|---|---|
| C | (0,1) | Right |
| 2 | (2,5) | Down,Down,Right×4 |
| 4 | (2,7) | Right×2 |
| G | (0,4) | Up,Up,Left×3 |
| 6 | (2,3) | Down,Down,Left |
| ! | (3,7) | Down,Right×4 |
| L | (1,1) | Up,Up,Left×6 |
| ! | (3,7) | Down,Down,Right×6 |

then Down (to options row), Left (to Enter), A. Verified by `typecode2.py`.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | ARM reset branch `0xEA00002E` | Observed header |
| `0x0801A9D0`–`0x0801AD74` | **`FUN_0801a9d0`: password decoder/validator** (returns 0 accept, −1 reject) | Derived: Ghidra decomp + objdump + native watchpoint |
| `0x0801AD74`–`0x0801AE00` | **`FUN_0801ad74`: completeness gate + accept/reject transition** | Derived |
| `0x0801AE00`–`0x0801AF2C` | Slot rendering: reads the 8 buffer bytes | Observed (watchpoint PC) |
| `0x0802665C` | Password UI handler (cursor, keypad highlight, slot entry) | Derived |
| `0x08024018` / `0x08025664` / `0x080245BC` | Keypad grid draw / highlight / portrait helpers | Derived |
| `0x08026E24` | Main-menu scene dispatcher; table `0x08138B08` indexed by state byte | Derived |
| `0x08138B08` | 10-entry handler table (`.[4] = 0x0802665D`) | Observed ROM words |
| `0x081386F0` | 32-entry scene-handler table | Observed ROM words |
| `0x08019A20` | literal `0x02008000` (password state pointer initializer) | Observed ROM words |
| `0x0832228C` | ASCII `EEPROM_V124` | Observed |

**RAM:**

| Address | Meaning |
|---|---|
| `0x030011BC` | global pointer → password state struct (`0x02008000`) |
| `0x030016DC` | menu scene-state byte (0 = main menu, 2 = SELECT MODE, …) |
| `0x02008000` | password state struct base |
| `0x0200800A` | last-slot index (0..7) |
| `0x0200800F`..`0x02008016` | **8 typed 5-bit symbol bytes** (0..31; `0xFF` = empty) |
| `0x02008021` | keypad cursor index `0..31` |
| `0x02008024` | number of symbols entered (0..8) |
| `0x0200803D`, `0x020083CB` | decoded field B |
| `0x0200801D` | decoded field F |
| `0x030016F0` | decoded field D (first byte of decoded-field struct) |
| `0x030016F1` | decoded field B |
| `0x030016F2` | decoded field C (`0xFF` = 31 sentinel) |
| `0x030016F3` | decoded field E |
| `0x030016F4` | decoded field A × 4 |
| `0x030016F6`, `0x030016F7` | 0, decoded field G |

## 5. Algorithm

### 5.1 Gate — `FUN_0801AD74` (0x0801AD74)

```
p = *0x030011BC                       // 0x02008000
for i = 0..7:
    if (byte)[p+0xF+i] < 0:           // 0xFF = blank slot
        bad = 0xFF
if (bad < 0) or (FUN_0801A9D0() != 0):
    p[0x23] = 0x80; *0x0300DA00 = 5   // REJECT (error banner)
    return -1
else:
    FUN_0801A3AC(DAT_0801ADF4, 0, 0, 1)  // accept: advance scene
    p[4] = 0x15; p[5] = 0; (*0x0300DA00)++
    sound(4)
    return 0
```

### 5.2 Validator — `FUN_0801A9D0` (0x0801A9D0)

Complete, reimplementable pseudocode (confirmed by disassembly `dis_valid.txt`):

```
v[0..7] = p[0xF+0..7]                 // 8 raw symbol indices (0..31)
check = 0
for i = 7 down to 0:                  // bit-plane gather, in place
    check = (check << 1) | (v[i] & 1)        // 8-bit
    v[i] = v[i] >> 1                  // q[i] = v[i]>>1 (0..15)
if ( (sum(q[0..7]) & 0xFF) != (~check & 0xFF) ) return -1     # checksum REJECT

A = ((q2&4)?8:0)|((q3&4)?4:0)|((q4&4)?2:0)|((q5&4)?1:0)
if A >= 12: return -1
fld[4] = A << 2                        # -> 0x030016F4

B = ((q1&1)?16:0)|((q2&1)?8:0)|((q3&1)?4:0)|((q4&1)?2:0)|(q5&1)
if B >= 24: return -1
fld[1] = B; p[0x3D] = B; p[0x3CB] = B

C = ((q2&8)?16:0)|((q3&8)?8:0)|((q4&8)?4:0)|((q5&8)?2:0)|((q6&8)?1:0)
if (C - 25) & 0xFF <= 5: return -1     # forbids 25..30
fld[2] = (C == 31) ? 0xFF : C
if fld[1] == C: return -1

D = ((q0&2)?64:0)|((q1&2)?32:0)|((q2&2)?16:0)|((q3&2)?8:0)| \
    ((q4&2)?4:0)|((q5&2)?2:0)|((q6&2)?1:0)
if D >= 100: return -1
fld[0] = D

E = ((q0&8)?16:0)|((q1&8)?8:0)|((q6&4)?4:0)|((q7&4)?2:0)|((q7&8)?1:0)
fld[3] = E
if (E & 8) and fld[2] == 0xFF: return -1

F = ((q0&4)?2:0)|((q7&2)?1:0)
if F >= 3: return -1
p[0x1D] = F

G = q7 & 1
if G and fld[0] <= 9: return -1
fld[6] = 0; fld[7] = G
return 0                               # ACCEPT
```

Key non-obvious points:

- The checksum is **not** over the raw 5-bit symbols. The bit-plane loop shifts each symbol right **in place** and the summation loop then reads the shifted bytes. The 8 extracted LSBs form an 8-bit check byte; the sum of `v[i]>>1` (mod 256) must equal its one's complement. For `H0PWP!Q6`: shifted values `[2,10,5,8,5,15,6,13]` sum to `0x40`; LSBs `[1,1,1,1,1,1,0,1]` form `0xBF`; `~0xBF = 0x40`. ✓
- Each field is a **bit-plane slice** across the 8 symbols (bit 2 of symbols 2–5 → A, bit 0 → B, bit 3 → C, bit 1 → D, mixed bit 3/2 → E, bit 2 → F, bit 0 of symbol 7 → G).
- `C == 31` is re-encoded as `0xFF` (a "all/none" sentinel), and E bit 3 is forbidden with that sentinel.
- `FUN_0801A9D0` writes the decoded fields into `0x030016F0..F7` and into the password state struct; `FUN_0801AD74` then advances the scene.

### 5.3 Encoder (minting codes)

Fields are chosen freely within their ranges; `q[i]` is assembled from the field bit-slices, the checksum target is `(~sum(q)) & 0xFF`, and the LSB of each symbol is set from bit *i* of that target (`v[i] = 2*q[i] + bit`). Implemented in `validator.py:encode()`. All generated codes are re-verified by `decode()`.

## 6. Tables

### 6.1 Alphabet (observed from the password screen)

| Index | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| Row 0 | B | C | D | F | G | H | J | K |
| Row 1 | L | M | N | P | Q | R | S | T |
| Row 2 | V | W | X | Y | Z | 0 | 1 | 2 |
| Row 3 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | ! |

**Font caveat:** the in-game font renders `G` ≈ `6`, `O`/`0`, `I`/`1` ambiguously; published web codes with `O`/`I` are OCR confusions for `0`/`1`.

### 6.2 Published codes

90 distinct codes collected from six web sources; full machine-readable list with 5-bit values and 40-bit hex in `/tmp/opencode/wwfrtwm2/codes_decoded.txt`. Feeding them through the recovered validator: **76 pass all checks**; 14 fail at the checksum gate and are attributable to transcription/OCR errors in the web lists (e.g. `00LBB284`, `HMQ6H2R4`, `6RLBM686`). No published code was used to derive the field layout — the layout came from disassembly and was then cross-checked.

Representative families: Stone Cold starter (`HHMBCQ84`, `HMQ6H2R4`, `HMHM3QR4`, …), all-belts (`00CBBZ84`, `08CCC874`, `6RLBM686`, …), Christian season set (`BQ1LYXCW`, `H0PWP!Q6`, `GCJM59M4`, …), Triple H (`BLVWX70H`, `Z7BCP878`), Undertaker (`8GVVV274`), Bradshaw/Jericho (`Z2BMLQR4`, `CLBK23WC`), Eddy Guerrero (`CNV013WC`, `HFGM2L44`, …).

## 6b. Enumeration

### Space definition

- Alphabet 32 symbols, length exactly 8 → **32^8 = 1,099,511,627,776 (2^40)** representable strings.
- 0xFF is the "blank slot" sentinel, so a complete entry has all 8 bytes in `0..31`.
- The validator is **algorithmic**, not a table: >700 distinct byte patterns (literal, case/±0x20, XOR 0x00–0xFF, ADD 0x00–0xFF, 5-bit packings, raw value arrays, alphabet strings) × 4 MiB give zero hits.
- The accepted set is defined by the checksum equation plus the seven field inequalities in §5.2, not by a stored list.

### Novel codes generated and confirmed

| Code | Fields (A,B,C,D,E,F,G) | In published lists? | Result |
|---|---|---|---|
| `C24G6!L!` | 44,19,22,42,15,1,1 | **No** | **Accepted on screen** → WrestleMania cutscene (`reject_near.png`) |
| `W24H5!L!` | 44,19,22,42,31,1,1 | No | Generated & validator-verified (not separately entered) |
| `CCCJJPH2` | 4,7,0,13,1,1,1 | No | Generated & validator-verified |

`C24G6!L!` exercises a field combination absent from all six published lists (notably `F=1,G=1` with `D=42` and `E=15`). It was entered keypad-by-keypad and accepted by the game's own validator.

### Bounds proven by rejection

- **On-screen:** an in-alphabet but checksum-invalid 8-symbol string produced the game's `INCORRECT` banner (`novel_typed_ok2.png`), proving the checksum gate fires on the real screen.
- **Byte-level (from §5.2):** a candidate is accepted only if `sum(q) == ~check`, `A<12`, `B<24`, `C∉{25..30}`, `B≠C`, `D<100`, not(`E&8 && C==0xFF`), `F<3`, and not(`G && D≤9`); any violation returns `0xFFFFFFFF` from `FUN_0801A9D0` and routes `FUN_0801AD74` to the reject branch. These are exact, not statistical.

## 7. Validation evidence

**Observed (emulator / ROM bytes):**

- Password screen with 8 slots and 4×8 keypad (`pw_clean.png`); control mapping verified at `0x04000130`.
- 8-symbol buffer at `0x0200800F..16` read back as `05 15 0b 11 0b 1f 0c 1b` for typed `H0PWP!Q6` (count bytes `0x0200800A=7`, `0x02008024=8`).
- Published `H0PWP!Q6` accepted → WrestleMania cutscene (`after_enter.png`).
- Novel `C24G6!L!` accepted → WrestleMania cutscene (`novel_ready.png`, `reject_near.png`).
- `INCORRECT` banner for an invalid in-alphabet code (`novel_typed_ok2.png`).
- mGBA native `watch/r 0x0200800F` broke at `0x0801AE40` (`FUN_0801AE00`, slot drawing), establishing the buffer's consumers.
- State bytes: `0x030016DC` brute-forced over 0..9 produced the menu screens (`states_montage.png`).

**Derived (disassembly / decompilation):**

- `FUN_0801AD74` gate and `FUN_0801A9D0` validator with exact algorithm and field RAM destinations.
- Buffer offsets, cursor offsets (`+0x21`), count offsets (`+0x0A`, `+0x24`), and the 10-entry menu state table `0x08138B08`.
- `FUN_0802665C` is the password UI handler (BL xrefs to `0x08024018` at `0x08026752`/`0x080268CC` and to `0x08025664` at `0x080268D8`).

**Inferred:**

- Field semantics (which field is wrestler, month, title, etc.) are not labelled in the ROM; only their bit-slices, ranges, and destination RAM are proven. The cutscene text after accept references the Heavyweight Title, consistent with field E being belt flags.
- The 14 failing published codes are transcription errors, not a second validator path.

## 8. Unknowns

1. Human-readable meaning of fields A–G (only their encoding and ranges are proven).
2. Whether fields outside the published ranges are intentionally unreachable content or just never shipped.
3. Exact season-state lifetime: the decoded fields at `0x030016F0..F7` are written by the validator; their later consumption by the season engine was not traced past the cutscene.
4. Full enumeration of accepted codes (2^40 space filtered by the predicate): the predicate is exact, but enumerating all satisfying strings was not performed exhaustively.

## 9. Tooling

- Prior pass (retained): Ghidra 12.1.4 headless `DumpDecomp.java` → `decomp_all.txt` (765 functions; a decompiler error at `0x08284824` required zeroing 256 bytes of a **copy** for analysis only). REA/Ghidra MCP repeatedly timed out on this ROM at the same analyzer error, so local Ghidra + `arm-none-eabi-objdump -M force-thumb` + Capstone were used.
- This pass: `dis_valid.txt` (objdump of `0x0801A9D0..0x0801AD74`), `dis_pwhandler.txt` (objdump of `0x0802665C..0x08026E24`), Thumb BL scanner, function-pointer table scanner, mGBA CLI debugger (`watch/r`, `w/1`, `x/1`, `break`, `continue`) via `clidbg.py`, GDB stub bridge via `gdbbridge.py`, RAM dumps via `dump.py`, keypad typing via `typecode2.py`, and the exact reimplementation `validator.py` (`decode()` / `encode()`).
- Screenshots: `/tmp/opencode/wwfrtwm2/pw_clean.png`, `typed_code.png`, `after_enter.png`, `novel_ready.png`, `reject_near.png`, `novel_typed_ok2.png`, `states_montage.png`. No screenshots in the ROM folder.

No ROM bytes or copyrighted assets are reproduced in this report; only hashes, addresses, alphabets, and derived code values are published.
