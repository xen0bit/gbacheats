# Matchbox Missions: Air, Land and Sea Rescue - Emergency Response (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Matchbox Missions: Air, Land and Sea Rescue - Emergency Response.gba` |
| Size | 4,194,304 bytes (0x400000, 32 Mbit) |
| Header title | `MATCHBOXMISS` |
| Game code | `BB4E` (USA) |
| Maker | `20` |
| Version | 0 (Rev.00) |
| Entry branch | `0xEA00002E` → stock `0x080000C0` (not a scene-patched cracktro) |
| Header checksum | `0x0000`; complement byte `0x60` (computed `0x79`) |
| MD5 | `adf9efca75fad810c13a5fb3326dddd2` |
| SHA-1 | `ac9919f32220e128d3df9a6201374f16ab15e301` |
| SHA-256 | `f5fc6723dc5e43b70f60570776d347d1e4ae5f74fe50698f7afd1c85511becb2` |

Embedded-header scan: exactly **one** Nintendo-logo hit (file `0x04` → header at `0x0`). This is a single 4 MiB image, **not** a concatenated 2-in-1 / multiboot pack. The pack nature ("2 Game Pack") is implemented inside one image by a game-select variable. No patch/trainer/cracktro detected.

## 2. Executive summary

The game has a **4-digit decimal password system** (`%04d` at `0x083EE5DC`) used as its save/progress mechanism, reached from each game's main-menu item `PASSWORD`. The UI shows `ENTER PASSWORD`, `PASSWORD INCORRECT!`, `TRY AGAIN`.

The validator is **table-driven**, not algorithmic. Two 16-entry tables of 4 digits each are compared against the entered code:
- Table A at ROM `0x0830ECC0` — the `9`-prefixed set (10 entries, of which 8 are reachable).
- Table B at ROM `0x0830ED40` — the plain decimal set.

Which table indices are tested is gated by a single halfword, the game selector at IWRAM `0x03004300`:
- `0` = Emergency Response → indices 0..2 only → **3 accepted codes**.
- `1` = Air, Land & Sea Rescue → indices 3..15 → **21 accepted codes**.

On acceptance the matched table index is stored to IWRAM `0x03005BD2`; a `9`-prefixed code additionally ORs bit 15. The selected index drives the mission banner shown next.

Total space: 10,000 (0000–9999). Exactly 3 codes are accepted in game 0 and 21 in game 1; every other input is rejected. No button codes, debug menus, or other hidden cheat surfaces exist (see §8 and §6b).

**Published codes:** none found. `RESCUE99` (claimed by an AI-generated aggregator) is **absent from the ROM** and incompatible with the numeric entry widget — treated as fabricated. TCRF returned 403; the Video Games Museum cheats page was empty. The codes reported here are original findings.

## 3. How to reproduce

Emulator: mGBA (SDL) on `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, `-3 -d` (CLI debugger) with stdout unbuffered via `stdbuf -o0 -e0`. Keymap: A=`x`, B=`z`, Start=`Return`, D-pad=arrows. Hold keys ~60–80 ms (150 ms double-steps menus).

Menu path (verified):
1. License screen → **A**.
2. DSI logo (wait ~3 s) → two-game splash.
3. **Left** = Emergency Response (`0x03004300 = 0`), **Right** = Air, Land & Sea (`0x03004300 = 1`). Verified by savestate RAM read. → **A**.
4. Main menu: Down ×4 to `PASSWORD` → **A**. Screen shows `0000` / `ENTER PASSWORD`.
5. Digit entry: **Left/Right** moves the cursor (0..3), **Up** decrements a digit (`0`→`9`), **Down** increments (`9`→`0`). The selected digit blinks and can appear absent in a screenshot.
6. **A** submits. Accepted → mission banner; rejected → `PASSWORD INCORRECT! / TRY AGAIN`.

Tested examples (all entered with real button presses):
- `9128` → "MISSION TWO! PUT OUT THE FIRES" (game 1).
- `9418` → "MISSION TWO! VITAL SUPPLIES" (game 1). RAM before submit: digits `9418` at `0x03007A54`, `0x03004300=1`, `0x03005BD2=0xFFFF`; after: mission banner, `0x03005BD2` changed.
- `1246` → "MISSION EIGHT! VIOLENT STORM" (game 1).
- `3602` → accepted; matched index 11 written to `0x03005BD2` (`0x000B`). Its mission banner rendered black on the loaded state.
- Rejected: `9127`, `1234` → `PASSWORD INCORRECT! / TRY AGAIN`.

## 4. Address map

| Item | Address (ROM / RAM) | Notes |
|---|---|---|
| Password validator (main) | ROM `0x08008BBC`–`0x08008C20` | state gate, table select, 4-digit compare loop |
| Comparison loop | ROM `0x08008BF4`–`0x08008C12` | `ldrb` digit − `0x30`, `ldrh` table u16, match counter `r9` |
| Accept path | ROM `0x08008DDA`–`0x08008E20` | `strh r4,[r5]` → `0x03005BD2`; OR bit 15 when digit0 = `9` |
| Alternate table branch | ROM `0x08008E9A`–`0x08008EC4` | used when digit0 ≠ `9` → table B |
| Extended-index setup | ROM `0x08008E34` | `ip=3, r6=16` when game flag ≠ 0 |
| Table A (9-prefixed) | ROM `0x0830ECC0` (file `0x30ECC0`) | 16 × 8 bytes, 4 × u16 per entry |
| Table B (plain) | ROM `0x0830ED40` (file `0x30ED40`) | 16 × 8 bytes, 4 × u16 per entry |
| UI string bank | ROM `0x083EE48C`–`0x083EE610` | plain ASCII NUL-terminated; no font/tile decoding needed |
| `%04d` format | ROM `0x083EE5DC` | |
| `PASSWORD INCORRECT!` | ROM `0x083EE5E4` | |
| Game selector | IWRAM `0x03004300` (u16) | 0 = Emergency Response, 1 = Air/Land/Sea; set by Left/Right on splash |
| Generator/progress index | IWRAM `0x030042D0` (u16) | referenced by `NEW PASSWORD!` generator path |
| Accepted-index flag | IWRAM `0x03005BD2` (u16) | matched table index; bit 15 set for 9-prefixed codes |
| Music enable | IWRAM `0x030042E2` (u8) | toggled in Options (0→1 observed) |
| Entered-digit buffer | stack `0x03007A54` (sp+0x24) | four ASCII bytes, e.g. `39 34 31 38` = "9418"; cursor at sp+0x20 |

File offset ↔ ROM address: `ROM = 0x08000000 + file_offset` (single image, base 0).

## 5. Algorithm

Pseudocode, exact enough to reimplement (verified against disassembly and dynamic breakpoints):

```python
table_A = [4 u16 @ 0x0830ECC0 + i*8 for i in range(16)]  # 9-prefixed set
table_B = [4 u16 @ 0x0830ED40 + i*8 for i in range(16)]  # plain set

def validate(digits, game_flag):          # digits = 4 ints 0..9, from ASCII-'0'
    ip, r6 = (0, 3) if game_flag == 0 else (3, 16)
    r4 = ip
    while r4 != r6:
        tab = table_A if digits[0] == 9 else table_B
        if all(digits[i] == tab[r4][i] for i in range(4)):
            store_index(r4)                       # 0x03005BD2 (u16)
            if digits[0] == 9: set_bit15()
            return ACCEPT
        r4 += 1
    return REJECT                                  # PASSWORD INCORRECT! / TRY AGAIN
```

Key details:
- The `'9'` check at `0x08008BD6` is **not** a validity gate — it **selects which table** is used. This was the main trap: an early model that treated it as a reject gate produced only 8 codes and missed the 13 plain decimal codes.
- The comparison is `(ASCII_digit - 0x30) == u16_table_value`; table values are 0..9.
- The loop compares all four digits; a single match counter `r9 == 4` triggers the accept path at `0x08008DDA`.
- A rejected code falls through to `0x08008C20`, which draws the failure screen.
- No checksum, PRNG, XOR, or arithmetic encoding exists — the system is a pure lookup, so exhaustive enumeration is exact.

## 6. Tables

**Table A @ `0x0830ECC0`** (index: code):
```
 0: 0246   1: 1460   2: 2602   3: 9128   4: 9673   5: 9418   6: 9920   7: 9451
 8: 9002   9: 9338  10: 9460  11: 3602  12: 4351  13: 5573  14: 6715  15: 7137
```
(Indices 11–15 have first digit 3–7 and are never reached in the digit0=9 branch; their values coincide with table B.)

**Table B @ `0x0830ED40`**:
```
 0: 0246   1: 1460   2: 2602   3: 3024   4: 4135   5: 5357   6: 6571   7: 7713
 8: 0024   9: 1246  10: 2460  11: 3602  12: 4351  13: 5573  14: 6715  15: 7137
```

Game-flag gate: `0x03004300 == 0` → indices 0,1,2 only; `!= 0` → indices 3..15.

Observed index → banner map (partial): idx 3 → Mission Two "Put Out The Fires"; idx 5 → Mission Two "Vital Supplies"; idx 9 → Mission Eight "Violent Storm"; idx 11 → accepted (black banner on the loaded savestate).

## 6b. Enumeration

**Space size:** 4 decimal digits = 10,000 values (0000–9999). No alphabet beyond `0`–`9`; no length variants; no checksum field; no reserved bits.

**Exhaustive result** (validator model run over all 10,000 inputs for both game flags; the model was derived from, and spot-checked against, the ROM's own comparison loop):

- `game_flag = 0` (Emergency Response): **3 accepted** — `0246`, `1460`, `2602` (table B indices 0–2).
- `game_flag = 1` (Air, Land & Sea Rescue): **21 accepted**:
  - table A (digit0 = 9): `9002`, `9128`, `9338`, `9418`, `9451`, `9460`, `9673`, `9920`
  - table B (digit0 ≠ 9): `0024`, `1246`, `2460`, `3024`, `3602`, `4135`, `4351`, `5357`, `5573`, `6571`, `6715`, `7137`, `7713`

**Novel codes (in no published list — no published list exists for this title):** `9128`, `9418`, `1246`, `3602` were each generated from the recovered tables and **accepted on the real in-game screen** with real button presses; §3 records the banners and RAM proof for `9418` (digits `9418` at `0x03007A54`, flag `0x03004300=1`, progress flag changed from `0xFFFF`) and `3602` (progress flag `0x000B`). `9128` was additionally accepted while the game flag was forced to 1 in the debugger, and again through the normal UI.

**Bounds proven by rejection:**
- `9127` (correct table-A prefix, wrong final digit) → `PASSWORD INCORRECT! / TRY AGAIN` in game 1.
- `1234` (well-formed but absent from both tables) → `PASSWORD INCORRECT! / TRY AGAIN` in game 1.
- `9128` entered in game 0 (flag 0, so only indices 0–2 are checked) → `PASSWORD INCORRECT! / TRY AGAIN`.
- The exhaustive model proves the remaining 9,976/9,979 values are rejected for each flag; the spot checks above confirm the model's boundary behaviour on the real screen.

## 7. Validation evidence

- **Observed** (emulator): license/DSI/splash, both main menus, options toggles, "CHASED CAR" vehicle screen, pause menu, password entry and accept/reject banners; `0x03004300` = 0 (Left) / 1 (Right) from decompressed mGBA `gbAs` savestate chunks; digit buffer `9418` at `0x03007A54`; progress flag `0x03005BD2` = `0xFFFF` before and changed after acceptance; `0x000B` after `3602`; music byte `0x030042E2` 0→1 on toggle.
- **Derived** (disassembly + live breakpoints): table bases `0x0830ECC0` / `0x0830ED40` confirmed at breakpoint `0x08008BF6` (`r1 = 0x0830ECC0`, `r4 = index`, match counter `r9` 0→1→2→3); accept writes `0x03005BD2`; alternate branch `0x08008E9A` loads `0x0830ED40`; state gate `cmp [0x03004300],#0` at `0x08008BC0`.
- **Inferred**: `0x030042D0` is the generator/progress index used by the `NEW PASSWORD!` path (static only — that screen was not reached, see §8). The renderer blinks the selected digit, which is why screenshots sometimes show only three of four digits.
- **Negative surfaces (bounded):** `strings` over the whole 4 MiB found zero occurrences of `debug`, `secret`, `hidden`, `unlock`, `cheat`, `level select`, `gameshark`, `codebreaker`. Raw key-mask scans for Konami, `L,R,U,D`, `Start,Select,A,B`, `L,Start,R` (u16 active-high) found zero hits. All UI text is plain NUL-terminated ASCII (`0x083EE48C`–`0x083EE610`), so no font/tile-indexed text bank needed decoding. Pause menu and both main menus expose only the documented items.

## 8. Unknowns

- The `NEW PASSWORD! / PRESS A BUTTON` generator screen (strings at `0x083EE5AC`, `0x083EE5BC`; code path `0x08008CA2` reading table B at `(index+3)*8`) was not reached in the emulator — reaching it requires completing a mission, which was not done. Its exact trigger is inferred, not observed.
- The mission banner for table index 11 (`3602`) rendered black on the loaded savestate; whether this is a genuine "no mission" state or a savestate artifact was not isolated. The code was nevertheless accepted and wrote the correct index.
- Difficulty-variable RAM address was not isolated (Right on DIFFICULTY produced no IWRAM/EWRAM delta in the sampled range); the label cycles in the menu but the underlying byte was not pinned.
- Header complement byte (`0x60` stored vs `0x79` computed) and checksum `0x0000` are noted but not fully explained; they did not affect behaviour.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep`.
- Python 3 + `capstone` 5.0.7 for literal/xref scanning; `arm-none-eabi-objdump -M force-thumb` for disassembly.
- mGBA SDL (`/usr/local/bin/mgba`) with `-3 -d`, `stdbuf -o0 -e0`, on a private `Xvfb :318` + `openbox`; CLI debugger driven through a persistent FIFO feeder; mGBA `gbAs` savestate chunks decompressed with Python `zlib` for RAM reads (IWRAM at raw offset `0x19000`).
- Helper scripts in `/tmp/matchboxmissions/`: `model.py`, `model2.py`, `xref.py`, `readstate.py`, `dumptables.py`, `ptrscan.py`.
- No GameShark/CodeBreaker/memory-edit codes were used as findings; debugger writes were used only to trace the validator and were always followed by real UI entry. Screenshots are kept on disk in `/tmp/matchboxmissions/` and are not attached.

**Legal note:** No ROM bytes, graphics, audio, or game assets are redistributed here — only hashes, addresses, algorithms, and original code values.
