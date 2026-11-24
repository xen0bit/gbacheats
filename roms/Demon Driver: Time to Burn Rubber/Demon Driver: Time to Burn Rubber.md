# Demon Driver: Time to Burn Rubber (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Demon Driver: Time to Burn Rubber/Demon Driver: Time to Burn Rubber.gba` |
| Size | 4,194,304 bytes (4 MiB / 32 Mbit) |
| Header title (`0xA0`) | `DEMON DRIVER` |
| Game code (`0xAC`) | `A9AE` |
| Maker code (`0xB0`) | `7M` |
| Software version (`0xBC`) | `00` |
| Entry word (`0x00`) | `0xEA00002E` → stock ARM branch to `0x080000C0` |
| Fixed byte (`0xB2`) | `0x96` |
| Complement (`0xBD`) | `0x6E` (matches the computed value) |
| Header checksum (`0xBE`) | `0x0000` |
| MD5 | `6129c86f94b5c7ed3c725cf2af593e56` |
| SHA-1 | `9dfe428843a22363ad8cc8ea0f818e439ef62f39` |
| SHA-256 | `8a42982d68f2dbea42a4cf4ccefe1f9149de5329bf1ab7beb333acf0d736c57e` |

Phase 0 checks:

* The 156-byte Nintendo logo occurs exactly once, at file offset `0x4` (header at `0x0`). This is a single GBA image, not a multi-game pack.
* The entry word is the retail `EA00002E`; the first 4 KiB contains no cracktro/trainer strings (`mode7`, `sunhors`, `crc bandit`, `trainer` all absent). No patch or trainer was found.
* The header checksum word at `0xBE` is zero (a rebuilt-header artifact), but the complement at `0xBD` is self-consistent (`0x6E`). No execution change was made.
* Tail of the image is `0xFF` padding. The emulator creates a 0-byte `.sav`; the game uses **passwords**, not battery save (confirmed by the absence of a save menu and by the password screen).

## 2. Executive summary

The game has a complete, developer-intended 20-character password system reachable from the main menu (`PASSWORD`). It is not a table of fixed codes: the ROM contains an **encoder/validator pair** over a 32-symbol alphabet with a keyed 5-bit transform, an 84-bit payload split into 14 bounded fields, and a 16-bit checksum.

* Alphabet (32 symbols): `WRTYPSDFGHJKLZXCVBNM0123456789-#`
* Key (20 bytes): `53 E9 01 23 EF 0D 23 AF CF 40 23 EE 68 C0 23 9F 23 ED 34 33`
* Payload: 14 fields, widths `5,5,6,6,6,6,6,6,6,7,7,2,8,8` (records 0–13), total 84 bits.
* Checksum: 16 bits at the tail of the 100-bit stream; valid iff `checksum == sum(transformed bytes with the checksum bits cleared)`.
* Validator: `0x0800AE00`. Input handler: `0x0800D8B0`. Tables: alphabet `0x083B0EF4`, key `0x083B0ED4`, field records `0x08055E54`.
* The validator is reimplemented offline (Unicorn and a pure-Python model). The encoder regenerates the game’s own generated password **exactly**, and the validator agrees with the game’s screen on accepted and rejected inputs.

Results:

* The only published GBA password found (GameFAQs, `MHXZUZYCCWFJ4RMTY81M`, “last race”) is **rejected by this ROM**: it contains `U`, which is not in the 32-symbol alphabet, its literal is absent from the image, and the emulator shows `INVALID PASSWORD`.
* A **novel** code absent from every published list, `NHLYCZYCCWCXGDY#YM0M`, was typed on the real password screen and accepted: the game goes to `SELECT TRACK` → `CHINA` → `GREAT WALL RUN` (0.568 km, record 40.25). RAM shows the decoded track field `0x1F` at `0x03005051`.
* A second, game-generated password, `0HLYCZYCCWCXGDY#YT0M` (produced by the tournament after one race), was decoded, re-encoded byte-for-byte by the recovered model, and re-entered; it resumes at `FRANCE` / `CITY LIMITS`.
* Bounds are proven by on-screen rejection: a checksum-valid code with field 1 = 20 (max 19) and a code with a corrupted checksum both produce `INVALID PASSWORD`; offline the ROM validator also rejects field 9 = 97 (max 96) and field 2 = 39 (max 38).
* No debug/cheat/secret/unlock strings exist (`strings -a -n 4` over the whole image: `cheat` 0, `debug` 0, `secret` 0, `unlock` 0, `hidden` 0, `bonus` 0; `password` appears only in the one UI text blob). The password screen is the only code surface.

A complete, coherent tournament password restores a stable screen. Synthetic codes that pass the validator but encode an empty/incoherent progress state are accepted and then transition to a black screen (DISPCNT mode 4, BG2 on; IWRAM churn continues and the sampled PC is in the IWRAM sound/mixer code, but nothing is drawn). That is reported as a bounded unknown, not as a rejection.

## 3. How to reproduce

Emulator: mGBA 0.10.5 under `Xvfb :290` (1024×768×24), `SDL_AUDIODRIVER=dummy`, `mgba -3`. Default SDL keymap:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Menu path to the password screen:

1. Boot → press Start (`Return`) → `MAIN MENU`.
2. Select `PASSWORD` (second item) → `ENTER PASSWORD`.

The entry screen is a 9×5 grid:

```
A B C D E F G H I
J K L M N O P Q R
S T U V W X Y Z 0
1 2 3 4 5 6 7 8 9
- # + x ✓
```

* D-pad moves the cursor; the grid wraps at all four edges (row 0 ↑ → row 4; column 0 ← → column 8).
* `A` selects the highlighted cell and appends its character; the field holds exactly 20 characters.
* `+` is backspace, `x` cancels to the main menu, `✓` submits.
* Pressing `✓` with an invalid string shows `INVALID PASSWORD`; pressing Start returns to the entry screen with the string intact.

Codes tested in this work:

| Code | Source | Result |
|---|---|---|
| `MHRYCZYCCWYXGWY#YZ0M` | generated (all fields 0) | accepted; black transition |
| `0HRYCZYCCWYXGWY#MZ0M` | generated (field 0 = 1) | accepted; black transition |
| `NHLYCZYCCWCXGDY#YM0M` | generated (field 0 = 31) | **accepted; CHINA / GREAT WALL RUN** |
| `0HLYCZYCCWCXGDY#YT0M` | game-generated after tournament race | **accepted; FRANCE / CITY LIMITS** |
| `MHXZUZYCCWFJ4RMTY81M` | GameFAQs published | `INVALID PASSWORD` |
| `09LYCZYCCWCXGDY#Y00M` | generated, field 1 = 20 (> 19) | `INVALID PASSWORD` |
| `NHLYCZYCCWCXGDY#YM0W` | novel code with last char changed | `INVALID PASSWORD` |

## 4. Address map

`file_offset = ROM_address - 0x08000000`.

| Address | Kind | Description |
|---|---|---|
| `0x0800AE00` | Thumb function | Password validator/decoder. Called from `0x0800D90C` with `r0 = 0x03002EFC`. Returns `1` accepted, `0` invalid. |
| `0x0800D8B0` | Thumb function | Password-screen input handler (grid cursor, character mapping, backspace, submit). |
| `0x0800D90A` | call site | `ldr r0,=0x03002EFC; bl 0x0800AE00`. |
| `0x083B0ED4` (file `0x3B0ED4`) | 20-byte table | Transform key. |
| `0x083B0EF4` (file `0x3B0EF4`) | 32-byte table | Password alphabet: `WRTYPSDFGHJKLZXCVBNM0123456789-#`. |
| `0x08055E54` (file `0x55E54`) | 14 × 7-byte records | Field table: `{u8 width, u8 max, u32 RAM_destination, u8 pad}`. |
| `0x0835D9F4` (file `0x35D9F4`) | ASCII text bank | Concatenated UI text. `MAIN MENU` `0x35DE19`, `PASSWORD` `0x35DE32`, `ENTER PASSWORD` `0x35DE3E`, `INVALID PASSWORD` `0x35DE5F`, `NEW PASSWORD` `0x35DE6F`. |

RAM (IWRAM `0x03000000`–`0x03007FFF`):

| Address | Size | Description |
|---|---|---|
| `0x03002EFC` | 20 + NUL | Typed password buffer (ASCII). |
| `0x03002F22` | 1 | Current string length (0–20). |
| `0x03005090` | 4 | Pointer to the buffer (`0x03002EFC`). |
| `0x03005094` | 1 | Maximum length, `20` (`0x14`). |
| `0x0300508D` | 1 | Cursor column, 0–8. |
| `0x0300508E` | 1 | Cursor row, 0–4. |
| `0x03004F50` | 20 | Decoded 5-bit symbol buffer (transformed in place). |
| `0x03001840` | 20 | RAM copy of the key. |
| `0x03001860` | 32 | RAM copy of the alphabet. |
| `0x03001880` | 1 | Checksum seed, computed once from the field table (`0x10`). |
| `0x03005051` | 1 | Field 0 destination (track index). |
| `0x030050A4` | 1 | Field 1 destination. |
| `0x03004EC0`–`0x03004EC6` | 7 | Fields 2–8 destinations. |
| `0x03004EBC` | 1 | Field 9 destination. |
| `0x030050A3` | 1 | Field 10 destination. |
| `0x030050A6` | 1 | Field 11 destination. |
| `0x03004EC7` | 1 | Field 12 destination. |
| `0x03004EC8` | 1 | Field 13 destination. |

The screen state byte checked around submission is `0x03002FD0`; during the password screen it is `0x12` (18).

## 5. Algorithm

### 5.1 Field table (`0x08055E54`)

| Rec | Width | Max | RAM destination | Meaning (confidence) |
|---:|---:|---:|---|---|
| 0 | 5 | 31 | `0x03005051` | track index (Observed: 0=Brazil Rain Forest Ring, 1=France City Limits, 2=Arctic Grand Stand, 31=China Great Wall Run) |
| 1 | 5 | 19 | `0x030050A4` | car/colour index (Inferred) |
| 2 | 6 | 38 | `0x03004EC0` | tournament progress byte (Inferred; 11 in the natural code) |
| 3 | 6 | 38 | `0x03004EC1` | unknown |
| 4 | 6 | 38 | `0x03004EC2` | unknown |
| 5 | 6 | 38 | `0x03004EC3` | unknown |
| 6 | 6 | 38 | `0x03004EC4` | unknown |
| 7 | 6 | 38 | `0x03004EC5` | unknown |
| 8 | 6 | 38 | `0x03004EC6` | unknown |
| 9 | 7 | 96 | `0x03004EBC` | points/credits byte (Inferred; 3 after one race) |
| 10 | 7 | 96 | `0x030050A3` | unknown |
| 11 | 2 | 3 | `0x030050A6` | class/mode (Inferred; 3 in the natural code) |
| 12 | 8 | 255 | `0x03004EC7` | unknown |
| 13 | 8 | 255 | `0x03004EC8` | unknown |

Seed: the ROM sums byte 0 of each of the 14 records (the widths) and computes `seed = (100 - sum) & 0xFF`. The 14 widths sum to 84, so `seed = 16` (`0x10`). The seed is computed once and stored at `0x03001880`; the validator treats it as “checksum width + 8”.

### 5.2 Validation (reimplementation of `0x0800AE00`)

```python
def validate(pw20):
    if seed == 0:                       # seed = 0x10 here
        s = sum(rom8[0x55E54 + 7*i] for i in range(14))
        seed = (100 - s) & 0xFF
    # 1. alphabet lookup
    idx = []
    for ch in pw20:
        j = ALPHA.find(ch)              # ALPHA = "WRTYPSDFGHJKLZXCVBNM0123456789-#"
        if j < 0: return 0              # includes A,E,I,O,Q,U and all action cells
        idx.append(j)
    # 2. keyed 5-bit transform
    v = [0]*20
    for i in range(20):
        if i % 2 == 0: v[i] = (idx[i] - KEY[i]) & 0x1F
        else:          v[i] = (idx[i] ^ KEY[i]) & 0x1F
    # 3. read 16 checksum bits from the tail, MSB-first inside each 5-bit group
    pos, bit = 19, 4
    def read_bits_clear(n):             # checksum pass: ROM clears each bit
        nonlocal pos, bit
        out = 0
        for _ in range(n):
            out = (out << 1) | ((v[pos] >> bit) & 1)
            v[pos] &= ~(1 << bit)
            bit -= 1
            if bit < 0:
                bit, pos = 4, pos - 1
        return out
    def peek_bits(n):                   # field passes: read only, no clearing
        nonlocal pos, bit
        out = 0
        for _ in range(n):
            out = (out << 1) | ((v[pos] >> bit) & 1)
            bit -= 1
            if bit < 0:
                bit, pos = 4, pos - 1
        return out
    checksum = (read_bits_clear(seed - 8) << 8) | read_bits_clear(8)
    # 4. checksum is over the payload-only bytes (checksum bits now zero)
    if checksum != sum(v):
        if seed != 0: return 0          # ((1 << seed) - 1) & 1
    # 5. range-check pass (records 13..0), then rewind
    saved = (pos, bit)
    for rec in range(13, -1, -1):
        val = peek_bits(REC[rec].width)
        if val > REC[rec].max: return 0
    # 6. write pass (same bit position)
    pos, bit = saved
    for rec in range(13, -1, -1):
        val = peek_bits(REC[rec].width)
        ram8[REC[rec].ptr] = val
    return 1
```

Notes:

* The checksum is 16 bits, not a simple character sum. It is the first 16 bits read from the tail; the bytes it occupies are cleared before the sum, so the check is `C == sum(v[0..15]) + (v[16] & 0x0F)`.
* The field bitstream starts immediately after those 16 bits (`v[16]` bit 3) and is read backwards through the symbols, MSB-first within each 5-bit group.
* Field order is records 13 → 0. The first (range-check) pass and the second (write) pass read the same bits; only the checksum extraction clears bits.
* Return `0` is mapped by the screen to `INVALID PASSWORD`; return `1` proceeds.

### 5.3 Encoding (inverse)

```python
def encode(fields):                     # fields[0..13], each <= REC[i].max
    R = []
    for rec in range(13, -1, -1):       # extraction order
        R += bits(fields[rec], REC[rec].width)   # MSB-first
    assert len(R) == 84
    for C in range(1 << 16):            # exactly one solution in practice
        T = bits(C, 16) + R             # 100 bits, read order
        v = [0]*20
        for i in range(20):
            v[19-i] = int(T[5*i:5*i+5], 2)   # 5 bits per symbol, tail first
        if C == sum(v[0:16]) + (v[16] & 0x0F):
            idx = [(v[i] + KEY[i]) & 0x1F if i % 2 == 0
                   else (v[i] ^ KEY[i]) & 0x1F for i in range(20)]
            return ''.join(ALPHA[j] for j in idx)
```

This encoder regenerated the game’s own tournament password `0HLYCZYCCWCXGDY#YT0M` exactly from its decoded fields, which is the strongest check that the bit order and checksum model are correct.

### 5.4 Why the published code fails

`MHXZUZYCCWFJ4RMTY81M` contains `U`. `U` is not in the 32-symbol alphabet, so the lookup at the top of the validator returns 0 before any checksum work. The literal is also absent from the 4 MiB image. This is not a checksum typo in our model: the published string cannot be represented by this ROM’s alphabet at all.

## 6. Tables

### 6.1 Alphabet and key

```
ALPHA = W R T Y P S D F G H J K L Z X C V B N M 0 1 2 3 4 5 6 7 8 9 - #
index   0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31
KEY   = 53 E9 01 23 EF 0D 23 AF CF 40 23 EE 68 C0 23 9F 23 ED 34 33
```

The UI grid displays `A`–`Z`, `0`–`9`, `-`, `#`, `+`, `x`, `✓`. The six letters `A E I O Q U` and the three action cells (`+`, `x`, `✓`) are **not** password symbols; a 20-character string that uses any of them is rejected. The valid symbols are the 20 letters present in `ALPHA`, all ten digits, `-` and `#`.

### 6.2 Verified codes

| Code | Fields (rec 0..13) | In-game result |
|---|---|---|
| `NHLYCZYCCWCXGDY#YM0M` | `31,0,11,0,0,0,0,0,0,3,0,3,0,0` | `SELECT TRACK` → `CHINA` / `GREAT WALL RUN` (0.568 km, record 40.25) |
| `0HLYCZYCCWCXGDY#YT0M` | `1,0,11,0,0,0,0,0,0,3,0,3,0,0` | `SELECT TRACK` → `FRANCE` / `CITY LIMITS` (0.269 km, record 19.21) |
| `MHRYCZYCCWYXGWY#YZ0M` | all zeros | accepted; black transition |
| `09LYCZYCCWCXGDY#Y00M` | field 1 = 20 | `INVALID PASSWORD` |
| `NHLYCZYCCWCXGDY#YM0W` | corrupted checksum | `INVALID PASSWORD` |

The first code is the novel deliverable: it is not in any published list (GameFAQs lists only the last-race password; TCRF has no page for this title; no wiki password list was found). It exercises a track (China/Great Wall Run) that the published list does not mention.

## 6b. Enumeration

**Space definition**

* Alphabet: 32 symbols, fixed length 20 → `32^20 = 1,267,650,600,228,229,401,496,703,205,376` (≈ 1.27 × 10³⁰, 2¹⁰⁰).
* Checksum: 16 bits → about `2^84 = 19,342,813,113,834,066,795,298,816` (≈ 1.93 × 10²⁵) strings pass the checksum alone.
* Semantic field space (bounded values from the record table):

```
32 (rec0) × 20 (rec1) × 39^7 (rec2..8) × 97^2 (rec9,10) × 4 (rec11)
          × 256^2 (rec12,13)
= 216,628,510,531,082,004,725,760  (≈ 2.166 × 10²³)
```

In the read-order stream the first 16 bits are the checksum (the last 3.2 symbols of the printed code) and the following 84 bits are the payload. The encoder searches the 16-bit checksum and found a solution for every tested tuple, including all boundary values below, and reproduced the game’s own generated password exactly; the tested field-to-code mapping is one-to-one in practice.

**Novel codes and in-game proof**

1. `NHLYCZYCCWCXGDY#YM0M` — field 0 = 31 (track 31), other fields from the game’s own post-race state. Typed character by character on the real `ENTER PASSWORD` screen (the typed buffer was read back from RAM as exactly that 20-character string), then `✓`:
   * screen: `SELECT TRACK` / `CHINA` / `GREAT WALL RUN` / `0.568KM` / record `40.25`;
   * RAM: `0x03005051 = 0x1F` (decoded field 0 = 31), `0x03004EBC = 0x03` (field 9), `0x03004EC0 = 0x0B` (field 2).
2. `0HLYCZYCCWCXGDY#YT0M` — generated by the game itself after one tournament race (screen `NEW PASSWORD`), read out of `0x03002EFC`. Decoding gives fields `rec0=1, rec2=11, rec9=3, rec11=3`; re-encoding those fields with the recovered model reproduces the exact string. Re-entering it (patched buffer, same screen + submit) produces `SELECT TRACK` / `FRANCE` / `CITY LIMITS`.
3. `MHRYCZYCCWYXGWY#YZ0M` (all-zero fields) and `0HRYCZYCCWYXGWY#MZ0M` (field 0 = 1) are also accepted by the validator and leave the password screen, but the game then transitions to a black screen; see §8.

**Bounds proven by rejection**

| Test | Encoded value | ROM validator | Emulator screen |
|---|---|---|---|
| Field 1 over max | `09LYCZYCCWCXGDY#Y00M`, rec1 = 20 > 19 | return 0 | `INVALID PASSWORD` |
| Field 9 over max | rec9 = 97 > 96 (offline) | return 0 | (same range-check path) |
| Field 2 over max | rec2 = 39 > 38 (offline) | return 0 | (same range-check path) |
| Checksum corrupt | `NHLYCZYCCWCXGDY#YM0W` | return 0 | `INVALID PASSWORD` |
| Published code | `MHXZUZYCCWFJ4RMTY81M` (contains `U`) | return 0 at alphabet lookup | `INVALID PASSWORD` |
| Boundary accepted | rec1 = 19, rec9 = 96, rec2 = 38 (offline) | return 1 | n/a |

The recorded boundary values from the ROM validator are: rec1 19 accepted / 20 rejected; rec9 96 accepted / 97 rejected; rec2 38 accepted / 39 rejected.

**Out-of-scope memory-edit codes**

Published CodeBreaker/GameShark codes for this title exist (cash, damage, temperature, tyre grip, starting lap, opponent positions). They are RAM-write codes, not in-game passwords, so they were not used as evidence and are not enumerated here. They are recorded only to make the scope boundary explicit.

**Negative search (bounded absence of a second system)**

* Whole-image `strings -a -n 4` produced 39,238 lines.
* Counts over that set: `cheat` 0, `debug` 0, `secret` 0, `unlock` 0, `hidden` 0, `bonus` 0. `password` occurs on exactly one line, the UI text blob at `0x35DBBC`–`0x35E07E`.
* Pointer searches for the password buffer (`0x03002EFC`), alphabet (`0x083B0EF4`), key (`0x083B0ED4`) and field table (`0x08055E54`), plus a Thumb BL scan for the validator, found one validator (`0x0800AE00`) and one input handler (`0x0800D8B0`); no second alphabet or second entry screen was found.
* All menu screens were walked: title, main menu (`PLAY`, `PASSWORD`, `OPTIONS`, `HI-SCORES`), race type (`QUICK RACE`, `TOURNAMENT`, `LINKPLAY`, `BACK`), enter name, select track, select car, race HUD, pause (`CONTINUE`, `QUIT`), race result, race again (`YES`, `NO`, `BACK`), new password, points standing, options (`MUSIC`, `SFX`, `CREDITS`, `BACK`), hi-scores (`CHRIS 80`, `IZZY 64`, `FRED 48`, `HELEN 32`), invalid password. No debug or hidden menu was observed.

## 7. Validation evidence

**Observed (emulator screenshots / RAM reads)**

* Typed 20-character novel code accepted, `SELECT TRACK` China/Great Wall Run; RAM read `0x03005051 = 0x1F`, `0x03004EBC = 0x03`, `0x03004EC0 = 0x0B`.
* Game-generated tournament password displayed on `NEW PASSWORD` and found at `0x03002EFC`; re-entry resumes France/City Limits.
* `INVALID PASSWORD` for the published code, for a valid-checksum/over-max field 1 code, and for a corrupted-checksum code.
* Cursor RAM at `0x0300508D`/`0x0300508E` and the 20-byte buffer at `0x03002EFC` tracked exactly while typing; this is how the input sequence was verified.
* No debug/cheat/secret strings in the full-image string scan.

**Derived (instruction-level)**

* Validator disassembly at `0x0800AE00` (Thumb) and input handler at `0x0800D8B0`.
* Field table at `0x08055E54`, alphabet at `0x083B0EF4`, key at `0x083B0ED4`.
* Checksum equation and bit order reimplemented; encoder produces the game’s own password exactly.
* Offline Unicorn emulation of `0x0800AE00` agrees with the Python model on random field tuples and on every boundary tested (rec1 19/20, rec2 38/39, rec9 96/97, rec0 31).

**Inferred**

* Meanings of fields 1–13 except the demonstrated track field. The max values and the natural code suggest field 1 is a car/colour index, field 2 a tournament progress byte, field 9 a points/credits byte, and field 11 a class/mode.
* The black-screen transition for synthetic zero-progress codes is caused by an incoherent progress state, but the exact gate was not isolated.

## 8. Unknowns

* Field semantics for records 1–13 (only record 0 is proven, by changing it and observing the track).
* The exact gate that makes an all-zero/incoherent progress password transition to a black screen while a real tournament password reaches `SELECT TRACK`. The validator accepts both; the difference is in the later game-state use, not the password check.
* The origin of the published GameFAQs string: it is not representable in this ROM’s alphabet. It may be from a different build, may be a transcription error, or may be fabricated; it is recorded as rejected, not as a working code.
* The `CREDITS` screen was not examined in detail (it is not a cheat surface).
* No debug menu exists in the string space or in the walked menus; the conclusion is bounded to this 4 MiB image.

## 9. Tooling

* mGBA 0.10.5, Xvfb `:290`, openbox, xdotool, ImageMagick `import`/`convert`.
* `arm-none-eabi-objdump -M force-thumb` for the validator/handler.
* Python 3 + Unicorn 2.1.4: `ucv.py` emulates `0x0800AE00` with the game’s IWRAM snapshot; `pwcode.py` implements the decoder/encoder and field table; `typeseq.py` drives the real grid with per-character RAM verification; `rdram.py` reads mGBA `.ssN` savestates (`gbAs` zlib chunk, IWRAM at `0x19000`); `patchstate.py` builds test states; `trycode.py` loads a patched state and submits it.
* Working directory: `/tmp/demondriver`.

## 10. Legal note

No ROM, graphics, music, or other copyrighted assets are redistributed here. Only hashes, addresses, algorithms, field tables, and short factual UI labels are reported.
