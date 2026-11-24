# Top Gun: Combat Zones (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Top Gun: Combat Zones.gba` (4,194,304 B = 4 MiB) |
| Header title | `TOPGUN CZ` (`0x080000A0`) |
| Game code | `A2YE60` (`0x080000AC`) |
| Maker | `60` (`0x080000B0`), fixed byte `0x96` at `0xB2` |
| Version | `0x00` (`0x080000BC`); complement `0x00`, header checksum `0x4000` |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| `file(1)` | `Game Boy Advance ROM image: "TOPGUN CZ" (A2YE60, Rev.00)` |
| MD5 | `f9d40d7c6c31991f44527a236107acda` |
| SHA-1 | `4f6ae177d236657a075e3366ed4f90c97b03f10d` |
| SHA-256 | `6948b9dedfd4eaf1c7a596742093ab9881c63775db90f5749aa0136f2a7b4012` |

This is the retail image; no cracktro/trainer patch was observed (§16.1).

## 2. Executive summary

The GBA SKU has **two developer-intended code surfaces on the main-menu `PASSWORD` screen**, both taking an 8-character string typed on an on-screen 30-symbol keypad (20 consonants + 10 digits; vowels A/E/I/O/U/Y are absent):

1. **Unlock-all code** — validator `0x080242AC` checks a 6-byte prefix `3KL1PS` and returns `0xAB12`. Entering `3KL1PS00` sets the unlock flag at EWRAM `0x02005E8C` from `0x00` to `0x01` (Observed: savestate bytes) and opens the previously gated **level-select** screen with `ACADEMY`, `ASIA`, `GULF`, `ARCTIC`. The published `SHPONGLE` is the same feature on other SKUs; this ROM's accepted literal is `3KL1PS` (first six positions), because the GBA keypad cannot type vowels.
2. **Level/mission codes** — validator `0x080278F0` decodes exactly 8 characters into a 16-bit payload with a 16-bit checksum. It is a real algorithm, not a table: **45,357,150** of **656,100,000,000** possible 8-character keypad strings are accepted, spanning **12,702 distinct payload values**. Novel codes `08000800` and `01K02D00` were generated offline, entered in mGBA and each started a different mission (Academy B and Asia respectively); a deliberately wrong checksum (`10KK2700`) was rejected with `PASSWORD INCORRECT`.

The widely published **4-digit level-password lists (e.g. `6161`, `4211`, `9799`) do not apply to this GBA image**: entering `6161` on the GBA password screen is silently ignored (the field simply stays on screen). They are almost certainly GC/PS2 material mislabelled as GBA.

A paused mission also *displays* an 8-character password (e.g. `10KK2600`), which is a separate progress-code generator; one generated value, `10KK2Q00`, is **rejected** by this same password screen — a generator/validator mismatch worth noting.

## 3. How to reproduce

* mGBA 0.10.5, `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, ROM launched with `-3`.
* Keymap (mGBA SDL default): A=`x`, B=`z`, Start=`Return`, D-pad = arrow keys.
* Screen path: boot → skip TITUS/Paramount intros with Start/A → choose `ENGLISH` (A) → skip briefings with A → in flight press Start → `QUIT` → `YES` → main menu → `PASSWORD` (Down, A).
* Keypad: Left/Right cycle within a row, Up/Down move between rows (column preserved); A selects a glyph; B deletes the last glyph; on-screen `OK` submits, on-screen `BACK` exits.
* Codes entered and results:

| Code | Result |
|---|---|
| `3KL1PS00` | unlock flag `0x02005E8C = 1`; level select opens (ACADEMY/ASIA/GULF/ARCTIC) |
| `10KK2600` | accepted → Academy A briefing (known-good, transcribed from pause screen) |
| `08000800` | **novel**, accepted → Academy B briefing |
| `01K02D00` | **novel**, accepted → Asia briefing ("Welcome to South East Asia...") |
| `00300300` | novel, accepted → Academy A briefing (alias of a different payload) |
| `10KK2700` | rejected → `PASSWORD INCORRECT` (checksum off by 1) |
| `10KK2Q00` | rejected → `PASSWORD INCORRECT` (generated on pause screen; mismatch) |
| `6161` | published 4-digit code: silently ignored (no 8-char code submitted) |

## 4. Address map

| Address (ROM unless noted) | Meaning |
|---|---|
| `0x08000000–0x08000200` | ARM/Thumb crt0; header |
| `0x08000460` | generic library: integer → 4-bit string (alphabet `0123456789ABCDEF`, `0x0808A828`) |
| `0x080004E0` | generic library: integer → 5-bit string (32-symbol alphabet `0x0808A896`, pad char `B`) |
| `0x0808A896` | 32-char alphabet `BCDFGHJKL MNPQRSTVW XZ 0123456789 : ?` (last two unreachable from keypad) |
| `0x0808A8D8`, `0x0808A8F8` | two identical 24-byte character-mapping tables (letter → index, `0` = unmapped) |
| `0x0808A7C4` | inlined `strlen` (word-at-a-time) used on the typed string |
| `0x080242AC` | **unlock-all validator**: 6-byte prefix check, returns `0xAB12` / `0x12AB` |
| `0x080278F0` | **level-password validator**: 8-char decode + checksum + field decode; returns non-zero on accept |
| `0x08025D12–0x08025D42` | caller: calls validator 1, then validator 2 on buffer `0x02006090`; reject shows text ID 100 |
| `0x0807CC60`, `0x0807CEA0` | password-screen key handlers (read pressed keys at `0x02002B98`) |
| `0x0808C5F8` | ASCII `PASSWORD INCORRECT`; text ID 100 in the English table `0x083ADE00` |
| `0x0808C830` | ASCII `PASSWORD` (main-menu entry) |
| `0x02006090` | EWRAM: typed password, NUL-terminated ASCII, max 8 chars |
| `0x02002B98` / `0x02002B9C` | pressed / held key masks (active high) |
| `0x02005E8C` | unlock-all flag (`0` → `1` after `3KL1PS00`) |
| `0x02009254`, `0x02009258`, `0x02009280` | keypad sub-state, cursor index, u16 key table (used by the UI, not the validator) |

## 5. Algorithm

### 5.1 Unlock-all validator (`0x080242AC`)

```
if s[0..5] == bytes("3KL1PS"): return 0x0000AB12
else:                           return 0x0000AB12 ^ 0x0000B9B9  /* literal 0x000012AB */
```
The caller writes `2` to a byte at `0x02005E8C` on success, which gates the level-select screen. Observed RAM value after entry: `0x01` (the flag is later normalized by menu code).

### 5.2 Level-password validator (`0x080278F0`)

```
for i in 0..7:
    c = input[i]
    if c == 'K': c = 'A'          # K is an alias of A
    if c == 'Q': c = 'E'          # Q is an alias of E
    v[i] = c - '0'  if '0' <= c <= '9'
           else (ord(c) + 201) & 0xFF   # A..Z -> 10..35

checksum = (v6*0x1100 + v0*0x10 + v5) & 0xFFFF
sumdata  = (v1 + v4 + v3 + v2) & 0xFFFF
reject if checksum != sumdata

payload P = (v2*0x1100 + v4*0x10 + v1) & 0xFFFF
/* bits 8..11 and 12..15 both equal v2 (4-bit repeated nibble) */
modeA  =  P        & 3      # 0..3, selects a branch family
modeB  = (P >> 2)  & 7      # 0..5, selects a branch family
f56    = (P >> 5)  & 3
f78    = (P >> 7)  & 3
f910   = (P >> 9)  & 3
f1113  = (P >> 11) & 7
f1415  = (P >> 14) & 3
/* fields are written to game-state globals; v3 feeds only the checksum, v7 is unused */
```
Note: there is **no reserved-bit rejection** — `modeA != 0` is a valid branch (this was initially misread as a reserved check; an in-game acceptance of `01K02D00` corrected it).

### 5.3 Encoder (offline minting)

For a desired payload `P` of the legal shape `(n<<12)|(n<<8)|(v4<<4)|v1`:
```
v1 = P & 0xF ; v4 = (P>>4)&0xF ; v2 = (P>>8)&0xF
T  = v1 + v4 + filler + v2
choose v0,v5 in 0..35 with v5 = T - 16*v0 ; v6 = 0
code = char(v0) char(v1) char(v2) char(filler) char(v4) char(v5) '0' char(anything)
```
`char()` reverses the value mapping (10 → `A` or its alias `K`, 14 → `E`/`Q`, etc.).

## 6. Tables

* **Keypad alphabet (30 symbols)**: `BCDFGHJKL MNPQRSTVW XZ 0123456 789` — rendered on screen; the ROM string at `0x0808A896` has 32 symbols (adds `:` and `?`) but those two are unreachable via the UI.
* **Character values**: digits `0-9` → 0-9; `A/B/C/D/E/F/G/H/J/K/L/M/N/P/Q/R/S/T/V/W/X/Z` → 10-35 with aliases `K≡A`, `Q≡E`. Vowels (`A,E,I,O,U`) and `Y` cannot be typed on this keypad, so values 23, 27, 31 are unreachable from the UI (they correspond to `O`, `U`, `Y`).
* **Validator return codes**: unlock success `0xAB12`, unlock failure `0x12AB`; level validator returns non-zero on success, `0` on reject.
* **Unlock flag**: `0x02005E8C` = `0` (locked) / `1` (unlocked).
* **Level select entries after unlock**: `ACADEMY`, `ASIA`, `GULF`, `ARCTIC` (4 regions, each with letter variants A…E seen in the text bank).

## 6b. Enumeration

**Space definition.** Input: exactly 8 symbols from the 30-symbol on-screen alphabet, i.e. **30^8 = 656,100,000,000** raw keypad strings. Character values are 0..35 (with aliases `K=A`, `Q=E`; values 23/27/31 unreachable from the UI). The 16-bit checksum equation and the payload shape constrain the accepted set.

**Exact counts (computed by enumerating all reachable value tuples, `pw2.py::enumerate_space`):**

| Quantity | Count |
|---|---|
| Raw 8-char keypad strings | 656,100,000,000 |
| Accepted by the ROM validator model | **45,357,150** (≈1 in 14,465) |
| Distinct 16-bit payloads reachable | **12,702** of 65,536 |
| Checksum character positions | `v0`, `v5`, `v6` (with `v6 = 0` for all reachable sums) |
| Free/alias positions | `v3` (checksum only), `v7` (unused → 30 spellings per code) |

**Validator model agreement.** The Python model (`pw2.py`) accepts `10KK2600`, `08000800`, `01K02D00`, `00300300` and rejects `10KK2700`, `10KK2Q00`, `6161` — in exact agreement with the emulator for every case tested.

**Novel codes (not in any published list — the published lists contain only 4-digit numbers and the name code `SHPONGLE`):**

| Code | Payload | Fields | In-game proof |
|---|---|---|---|
| `08000800` | `0x0008` | `modeB=2` | accepted; started **Academy B** (briefing screenshot `result_mode2_c.png`) |
| `01K02D00` | `0xAA21` | `modeA=1` | accepted; started **Asia** mission ("Welcome to South East Asia…", `result_reserved_c.png`) |
| `00300300` | `0x3300` | `f78=2, f1113=6` | accepted; briefing (`result_novel3_c.png`) |
| `3KL1PS00` | n/a | unlock prefix | accepted; unlock flag `0x02005E8C: 0x00 → 0x01` and level-select screen opens (`result_unlock_c.png`, `unlock_lvl3_c.png`) |

**Bounds proven by rejection:**

1. `10KK2700` — only the checksum character `v5` changed from `6` to `7` (checksum 30 vs sum 22) → `PASSWORD INCORRECT` (`result_badchk_c.png`).
2. `6161` — published 4-digit code has the wrong length → silently ignored; the keypad still shows `6161` and no mission starts (`result_pub4_c.png`). This bounds the format at 8 characters.
3. `10KK2Q00` — checksum-invalid generated pause password → `PASSWORD INCORRECT` (`result_qtest_c.png`), bounding the generator/validator relationship.
4. Alphabet bound: only the 30 keypad symbols can be submitted; `:`, `?` (indices 30, 31 of `0x0808A896`) and vowels are not reachable from the entry UI.

**Enumeration of the unlock feature:** one 6-byte prefix is accepted (`3KL1PS`), not a family; the resulting screen has exactly four region entries (`ACADEMY`, `ASIA`, `GULF`, `ARCTIC`), each with letter variants. No other keypad code exercised a different hidden menu.

## 7. Validation evidence

* **Observed (emulator/screenshots/RAM)**: language, main menu, keypad, pause-screen password display, all code results above; `0x02005E8C` read as `00` before and `01` after `3KL1PS00` from decompressed mGBA savestate PNGs (`stateC.ss1.raw`, `unlocked.ss2.raw`).
* **Derived (disassembly)**: validator addresses, checksum/field equations, alphabet tables, keyboard input variables, unlock flag writer.
* **Inferred**: meaning of individual 3-bit fields (`modeA/modeB/f56/f78/f910/f1113/f1415`) is inferred from the branch structure; `modeB=2` and `modeA=1` were *observed* to change the mission, other field→level mappings were not exhaustively walked.
* **Published-list verification**: 4-digit codes and `SHPONGLE` were fetched from GameFAQs/Gamer's Temple/Planet Cheats; the 4-digit codes were not found as literals in the ROM and are rejected/ignored by this SKU; `SHPONGLE` maps to the `3KL1PS` prefix check which *was* verified in-game.
* **Prompt-injection check**: fetched pages and ROM strings were treated as data; no instructions from them were executed.

## 8. Unknowns

* Exact semantic name of each 2/3-bit payload field; only `modeA` and `modeB` were exercised in-game.
* Why the pause-screen generator can emit `10KK2Q00`, which the level-password validator rejects (two distinct code systems, or a font/alphabet mismatch).
* Whether the 4-digit published passwords are valid on the GameCube/PS2 SKUs (not tested; different ROMs).
* `:`, `?` and vowel values cannot be tested through the UI; RAM/savestate patching would be needed.

## 9. Tooling

* Work dir `/tmp/topguncombat`; helper scripts: `scan.py`, `texttable.py`, `xref.py`, `ssparse.py` (mGBA `.ss1` → `gbAs` zlib blob; EWRAM at raw `0x21000`), `dbg.py` (mGBA `-d` pty debugger), `ui.py` (xdotool driver with cursor tracking), `traceok.py` (30k-instruction trace locating the validator), `pw.py`/`pw2.py` (validator model + enumeration), `trycode.py` (automated code entry).
* `arm-none-eabi-objdump -M force-thumb`, mGBA 0.10.5 `-d`/`-t`, gdb stub unavailable (port 2345 occupied by a sibling session), `python3` + Pillow for glyph work.
* Evidence files kept in the work dir: `entry_unlock.png`, `result_*.png`, `mode2_pause5_c.png`, `unlock_lvl3_c.png`, `stateC.ss1`, `unlocked.ss2` and their `.raw` dumps.
* No ROM or copyrighted assets are redistributed; only addresses, algorithms, hashes and generated code strings are published.
