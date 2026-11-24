# Super Dropzone: Intergalactic Rescue Mission (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Super Dropzone: Intergalactic Rescue Mission.gba` |
| Size | 4,194,304 bytes (4 MiB / 32 Mbit) |
| Header title | `SPR DROPZONE` |
| Game code | `AZNE` |
| Maker | `7M` (fixed `0x96` present) |
| Version | 0 (Rev.00) |
| Entry word | `0xEA00002E` (stock GBA branch to `0x080000C0`; **not** a cracktro) |
| MD5 | `82f6103c5fc2315e7f11128b9940602f` |
| SHA-1 | `3acd2595dbca9802583f9de2c789db2e87561b05` |
| SHA-256 | `29594176051ca11dd4f86a52ce5f8d7fd20edf949a4d9d1a57c8439963b84504` |
| Publisher/author strings | `Ignition Entertainment LTD`, `Jim Bagley`, `Archer Maclean` (ROM `0x111E0`–`0x112CC`) |

## 2. Executive summary

The game has a **developer-intended 8-digit numeric password system** and a hidden **CHEATS menu** with five YES/NO toggles. The password system is a **pure 50-entry lookup table** (no checksum, no algorithmic generator): an 8-ASCII-digit string in the menu text buffer at RAM `0x0300002F` is compared byte-for-byte with 50 records at ROM `0x080140BE`. There is exactly **50 accepted inputs out of 10^8 decimal strings**.

- Indices 0–45 (46 codes) are level/wave progress codes: `level = index / 11`, `wave = index % 11`, computed by the ROM's own division routine at `0x08010FF0`.
- Index 46 (`51853435`) sets RAM `0x03000F54 = 1`, the **CHEATS-menu unlock flag** (verified in emulator).
- Indices 47–49 set `0x030012B4 = 0xFF`, `0x03000FA0 = 9`, `0x030041E0 = 1` respectively (all verified in emulator).
- Four further 8-digit strings follow the 50 records in ROM but are **not checked** by the validator (bounded negative, §6b).

The CHEATS menu contains five toggles stored as bytes at RAM `0x03001898[0..4]`: `1. INFINITE LIVES`, `2. INFINITE WEAPONS`, `3. LEVEL COMPLETER`, `4. SLOW CLOAK`, `5. KILL HUMANOIDS` (strings at `0x08011548`–`0x080115AC`). Selecting a row toggles bit 0 of the corresponding byte (`0x0801047A`–`0x08010490`).

No published code list could be retrieved (3rd party cheat indexes return HTTP 403, DuckDuckGo serves a bot challenge, and the web-search integration quota was exhausted). The eight codes printed in the game's own level-select table at `0x08011830` are treated as the "published-style" visible set; 42 of the 50 accepted codes — including the cheat-unlock code — are absent from it and are therefore novel relative to that visible list.

## 3. How to reproduce

### 3.1 Emulator setup
```
Xvfb :316 -screen 0 1024x768x24 &
openbox --display :316 &
DISPLAY=:316 SDL_AUDIODRIVER=dummy mgba -3 <rom.gba> &
```
mGBA SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys ~60–150 ms (short taps are missed).

### 3.2 Reaching the password screen
1. Boot and sit through the publisher splash, title card, and FMV intro (~25–40 s), or press keys to skip.
2. During gameplay press R (`s`) / Select to bring up the **Options** menu.
3. Move Down to `Password: 00000000`.
4. Press Right repeatedly to advance the digit cursor (each press extends the highlight to the next digit), then press A (`x`) to increment the highlighted digit 0→1→…→9→0. (Input is fiddly because of X key repeat; for deterministic tests the 8 bytes were written directly into a savestate — see §3.3.)
5. Select `Start New Game` and press A. The game validates the 8 digits and clears the buffer to `00000000` on acceptance.

### 3.3 Deterministic input via savestate (used for all RAM proofs)
mGBA `.ss1` files are PNG with a zlib-compressed `gbAs` chunk. Decompressed layout: IWRAM begins at raw `0x19000` (so RAM `0x03000010` → raw `0x19010`). The menu-copy of the string `   Start New Game    Password: 00000000 …` lives at `0x0801406D` and is copied to `0x03000010`; the 8 password digits are at offset 31 → raw `0x1902F`..`0x19037`.

Procedure: save a state at the Options menu, patch those 8 bytes, write a new PNG with a correct `gbAs` CRC, reload (F1), press A on `Start New Game`, save again, and read the effect flags from the new state. Scripts: `/tmp/superdropzone/ss_write.py`, `test_pw.py` (§9).

### 3.4 Codes verified in-game
| Code | Index | Observed RAM effect |
|---|---|---|
| `51853435` | 46 | `0x03000F54: 0 → 1` (CHEATS unlock); buffer cleared to `00000000` |
| `88895288` | 47 | `0x030012B4: 0 → 0x00FF` |
| `00247227` | 48 | `0x03000FA0: 5 → 9` |
| `41693261` | 49 | `0x030041E0: 0 → 1` |
| `22441687` | 37 | `0x030012A4 = 3`, `0x03002D70 = 4` (level 3, wave 4) |
| `12345678` | — | **rejected**: flags unchanged, buffer stays `12345678` |
| `36104232` | 50 (unused record) | **rejected**: flags unchanged, buffer stays `36104232` |

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08011830` – `0x0801188B` | 8 displayed level passwords, NUL-padded, 12-byte stride (plaintext ASCII) |
| `0x0801406D` | Menu template string `Start New Game / Password: 00000000 / Number Of Players: 1 / Display Hall Of Fame` (81 bytes) |
| `0x080140BE` | **Password validation table**: 50 × 8 ASCII digits (400 bytes) |
| `0x0801424E` | 4 trailing 8-digit strings (indices 50–53) — **not referenced by the validator** |
| `0x08011548`–`0x080115AC` | CHEATS menu strings: 5 cheat names, `YES`, ` NO` |
| `0x080032F8` | Validator loop (inside screen handler `0x08003068`) |
| `0x08010FF0` | Signed integer division helper (index / 11) |
| `0x080102C` | CHEATS menu / overlay screen handler; gate at `0x08010306`, draw at `0x0801037C`, toggle at `0x0801047A` |
| `0x0800ECBC` | Draws `Password For` text |
| `0x03000010` | RAM copy of menu template string (password digits at `+31`) |
| `0x03000F54` | CHEATS unlock flag (set by password 46; read at `0x08010306`) |
| `0x030012A4` | Level (index / 11) |
| `0x03002D70` | Wave (index % 11) |
| `0x030012B4` | Set to `0xFF` by password 47 |
| `0x03000FA0` | Set to `9` by password 48 (default 5) |
| `0x030041E0` | Set to `1` by password 49 |
| `0x03001898[0..4]` | Five cheat toggle bytes (bit 0 = on) |
| `0x030040CC` | Selected cheat-menu row (0–4) |
| `0x030012A0` | Input state word used by the cheat overlay (bit `0x100` opens it; bit `0x200` + cheat[4] triggers the `5. KILL HUMANOIDS` action) |

## 5. Algorithm

The validator (`0x080032F8`, Thumb):

```
input = RAM[0x0300002F .. 0x03000036]        // 8 ASCII '0'..'9'
for index in 0 .. 49:                        // cmp r5,#49 / bgt done
    match = all(input[k] == ROM[0x080140BE + index*8 + k] for k in 0..7)
    if not match: continue
    // accepted:
    if index <= 45:
        level = div(index, 11)               // BL 0x08010FF0(index, 11)
        wave  = index - 11*level
        RAM[0x030012A4] = level
        RAM[0x03002D70] = wave
        // visual "accepted" feedback, then fall through to next index
    else:
        if index == 46: RAM[0x03000F54] = 1
        if index == 47: RAM[0x030012B4] = 0xFF
        if index == 48: RAM[0x03000FA0] = 9
        if index == 49: RAM[0x030041E0] = 1
    RAM[0x0300002F .. 0x03000037] = '00000000'  // clear buffer (observed)
    // (the loop continues through all 50 records; only one can match)
```

Notes:
- Comparison is **raw byte equality** on ASCII digits; no alphabet table or checksum exists.
- On acceptance the 8-byte buffer is overwritten with `'0'` characters (loop at `0x0803366`: stores `0x30` for indices 0x1F..0x26 relative to `0x03000010`). On rejection the buffer is left untouched — a useful oracle.
- `div` is the ROM's own restoring-division routine (`0x08010FF0`), confirmed by output `37 → level 3, wave 4`.

CHEATS menu (`0x080102C` handler):
```
if RAM[0x03000F54] == 0: skip CHEATS block          // 0x08010306
if input & 0x100:                                    // 0x08010320
    row = RAM[0x030040CC] (0..4)
    if A pressed: RAM[0x03001898 + row] ^= 1          // 0x0801047A-0x08010490
    display 5 names from ROM pointer table 0x08014324,
             with YES/NO from 0x08014338 / 0x0801433C
if RAM[0x03001898+4] != 0 and input & 0x200:
    trigger 5. KILL HUMANOIDS action                  // 0x080102A0-0x080102BC
```

## 6. Tables

### 6.1 All 50 accepted passwords (ROM `0x080140BE`, 8 ASCII digits each)

| idx | code | idx | code | idx | code | idx | code | idx | code |
|---:|---|---:|---|---:|---|---:|---|---:|---|
| 0 | 53387081 | 10 | 37670561 | 20 | 02085365 | 30 | 65480763 | 40 | 88005584 |
| 1 | 18808555 | 11 | 94379929 | 21 | 04721006 | 31 | 16269804 | 41 | 22729666 |
| 2 | 66465147 | 12 | 13955392 | 22 | 23419131 | 32 | 93161096 | 42 | 49769614 |
| 3 | 43761694 | 13 | 34168831 | 23 | 02195811 | 33 | 67448422 | 43 | 41201018 |
| 4 | 46482808 | 14 | 37741453 | 24 | 68715429 | 34 | 66056495 | 44 | 82741602 |
| 5 | 66001383 | 15 | 41258610 | 25 | 63446447 | 35 | 03296263 | 45 | 87780397 |
| 6 | 67616192 | 16 | 63238301 | 26 | 06774889 | 36 | 31675479 | 46 | 51853435 |
| 7 | 14740378 | 17 | 32606521 | 27 | 38836985 | 37 | 22441687 | 47 | 88895288 |
| 8 | 80398368 | 18 | 28424423 | 28 | 56646566 | 38 | 44667034 | 48 | 00247227 |
| 9 | 81455848 | 19 | 51488039 | 29 | 86761016 | 39 | 19763023 | 49 | 41693261 |

### 6.2 The 8 visible level-select codes (ROM `0x08011830`) and their indices

| Code | idx | level (`idx/11`) | wave (`idx%11`) |
|---|---:|---:|---:|
| 53387081 | 0 | 0 | 0 |
| 46482808 | 4 | 0 | 4 |
| 94379929 | 11 | 1 | 0 |
| 41258610 | 15 | 1 | 4 |
| 23419131 | 22 | 2 | 0 |
| 06774889 | 26 | 2 | 4 |
| 67448422 | 33 | 3 | 0 |
| 22441687 | 37 | 3 | 4 |

These are a sparse subset of the 46 progress codes (levels 0–3 sampled at waves 0 and 4).

### 6.3 Cheat toggle table

| Row | String (ROM) | RAM byte | Verified effect |
|---:|---|---|---|
| 0 | `1. INFINITE LIVES` (`0x08011594`) | `0x03001898+0` | toggle read by game code (label only; not individually exercised) |
| 1 | `2. INFINITE WEAPONS` (`0x08011580`) | `+1` | toggle read by game code |
| 2 | `3. LEVEL COMPLETER` (`0x0801156C`) | `+2` | toggle read by game code |
| 3 | `4. SLOW CLOAK` (`0x0801155C`) | `+3` | toggle read by game code |
| 4 | `5. KILL HUMANOIDS` (`0x08011548`) | `+4` | toggle + L (`input & 0x200`) triggers action at `0x080102A0` |

## 6b. Enumeration

**Space definition.** Alphabet = decimal digits `0`–`9` (10 symbols), fixed length 8, no checksum, no reserved bits. Representable inputs = 10^8 = 100,000,000. Accepted set = **exactly 50 strings**, enumerated exhaustively from the validator's own table in §6.1. The validator's loop bound (`cmp r5,#49; bgt` at `0x0803408`) and the 400-byte table stride were both checked against the ROM bytes, so the accepted set is closed.

**Validator model.** A byte-for-byte string comparison. A reimplementation is: `accepted = (input_string in TABLE_50)`. This model agrees with the ROM on all 7 tested inputs (5 accepted, 2 rejected) and explains the buffer-clearing side effect on acceptance.

**Novel codes (absent from the 8 visible/published-style codes in §6.2).** 42 of the 50 accepted strings are not in the visible level-select list. The following were generated from the ROM table, absent from that list, entered in the emulator, and RAM-verified:

- `51853435` (idx 46) — unadvertised cheat-unlock code. **In-game proof:** password visible on the Options screen, then after `Start New Game`, RAM `0x03000F54` changed `0 → 1` (savestate read); this is the gate at `0x08010306` that enables the CHEATS menu overlay. Screenshot: `patched_pw_crop.png` (password on screen), `valid2_crop.png` (game started).
- `88895288` (idx 47), `00247227` (idx 48), `41693261` (idx 49) — three further unadvertised codes, each with a distinct RAM effect (§3.4).
- `22441687` (idx 37) — one of the 8 visible codes, used to confirm the `level=idx/11`, `wave=idx%11` decoder (observed `level 3, wave 4`).

**Bounds proven by rejection.**
- `12345678` (well-formed 8-digit string, not in the table) → rejected: `0x03000F54` stayed `0`, level/wave stayed `0`, and the input buffer was **not** cleared (`12345678` still present). This proves a checksum-free exact-match system rather than a range/checksum validator.
- `36104232` — one of the four 8-digit strings physically present at ROM `0x0801424E` but beyond the loop bound (index 50) → rejected identically. This proves the accepted table size is **exactly 50**, not 54.
- Any string of length ≠ 8, or containing a non-digit, cannot be entered through the on-screen field and matches no 8-byte record; the comparator has no shorter/longer branch (single fixed 8-iteration loop).

**Button codes / hidden menus.** No button-sequence table was found. The only hidden UI surface is the CHEATS menu, whose gate is a password-set RAM flag (`0x03000F54`), not a button code. A `5. KILL HUMANOIDS` action requires cheat[4] ON plus `input & 0x200` (`0x080102A0`), i.e. an in-game action, not a code entry path. Every reachable screen walked in the emulator: publisher splash → legal screen → title → FMV intro → GET READY → gameplay → Options menu (4 items: Start New Game / Password / Number Of Players / Display Hall Of Fame) → Hall Of Fame (reachable but not exhaustively catalogued, see §8). No 5th Options item or undocumented menu entry appeared with the unlock flag set.

## 7. Validation evidence

- **Derived (disassembly):** validator loop `0x080032F8`–`0x0803322`; table base/size from literal `0x08033C0 = 0x080140BE` and loop bound `49`; special-case stores `0x0803328`–`0x080334E`; buffer clear at `0x0803366`; division helper `0x08010FF0`; CHEATS menu strings/gates/toggle at `0x08010306`/`0x0801037C`/`0x0801047A`.
- **Observed (emulator + savestate RAM reads):** table of 50 codes (ROM bytes); password displayed on Options screen after savestate injection; `51853435` → `0x03000F54=1`; `88895288` → `0x030012B4=0xFF`; `00247227` → `0x03000FA0=9`; `41693261` → `0x030041E0=1`; `22441687` → level 3 / wave 4; `12345678` and `36104232` rejected with buffer not cleared. Screenshots stored in `/tmp/superdropzone/`.
- **Inferred (not fully exercised):** the semantic names of `0x030012B4`, `0x03000FA0`, `0x030041E0` beyond their observed values; the in-game visual effect of each of the five cheat toggles (only the menu structure and one action path were traced). The CHEATS overlay itself was not captured on screen — its gate and rendering code were proven statically and the gate flag was RAM-verified, but the overlay screen was not reached through the controller in the available session (labelled as a gap, not a negative claim).
- **Web recon:** all direct fetches (3rd party cheat indexes) returned 403; DuckDuckGo returned a CAPTCHA; the search integration was quota-limited. Published lists were therefore not independently verified. ROM text was treated strictly as data; no fetched content was followed as instructions.

## 8. Unknowns

- The full in-game semantics of the three non-progress special flags (`0x030012B4`, `0x03000FA0`, `0x030041E0`) were not traced to their final consumers (candidate literal pools at `0x800F530`/`0x800F540` are data; the corresponding LDR sites were not fully followed).
- The CHEATS selection overlay was not displayed on screen; only its unlock flag and code path were verified. A future analyst should find the scene that calls `0x0801002C` from `0x08003DE2` (a level/continue setup routine) and capture it there with `0x03000F54=1`.
- The Hall Of Fame screen was reached in principle but not exhaustively walked.
- Four trailing 8-digit strings at `0x0801424E` are unreachable by this validator; their original purpose is unknown.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for Thumb disassembly.
- Capstone 5.0.7 scripts: `scan_ptrs.py` (32-bit literal pointers), `scan_ldr2.py`/`scan_ldr3.py` (Thumb `LDR Rd,[PC,#imm]` literal resolution), `scan_bl.py` (Thumb BL target scan).
- Python zlib/struct savestate tools: `ss_write.py` (patch 8 password bytes in `.ss1`), `test_pw.py` (batch patch → reload → submit → read RAM), `ss_patch.py` (inspect).
- mGBA 0.10.5 under Xvfb :316 + openbox, `SDL_AUDIODRIVER=dummy`; screenshots via `scrot` + `convert` crop to the 720×480 viewport.
- All analysis artifacts were in `/tmp/superdropzone/`; no ROM or copyrighted assets are redistributed by this report.

## 10. Legal note

Only hashes, addresses, algorithms, and self-derived code strings are published. The ROM itself and extracted graphics/audio are not redistributed.
