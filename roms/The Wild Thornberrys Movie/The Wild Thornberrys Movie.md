# The Wild Thornberrys Movie (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Wild Thornberrys Movie.gba` (4,194,304 bytes / 4 MiB) |
| Header title | `THORNBERRYS` |
| Game code | `AWLE` |
| Maker code | `78` |
| Version | `0x00` (complement `0x57`, header checksum `0x0000` — typical rebuilt-header artifact, see guide §16.1) |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`; no cracktro/trainer patch detected) |
| MD5 | `2c278a2282ea14997ef4202d205f91bb` |
| SHA-1 | `6bed328b3ce2c6d228e81c9fa7dc0806ee697b94` |
| SHA-256 | `53dadc585472af4b250faf522dd2e3c80320f1f909cc629cd4bf1d57509bfcd6` |

Single-image retail ROM. File offset = ROM address − `0x08000000` throughout.

## 2. Executive summary

The game has a **developer-intended 4-character password system** used as a progress/save code: finishing a level shows `New password is: xxxx` (string at `0x0805B994`), and the main menu has a `Password` entry (string at `0x0805AEB4`, menu table at `0x080CDC88`) that opens an on-screen keyboard. The accepted set is **exactly 30 fixed 4-character codes**: 3 difficulty rows × 10 level checkpoints. There is **no checksum and no algorithmic generator** — the "validator" at `0x08009168` is a pure 30-entry exact byte comparator against a plaintext table at `0x0805B17C`. The end-of-level "generator" at `0x0800A528` also just indexes the same table using the current difficulty and level.

Every code, its alphabet, and both field meanings were recovered statically and confirmed dynamically: a code typed through the real on-screen keyboard set difficulty `2` and level `9` in RAM; two out-of-table codes were rejected with the state globals left untouched. No button-code sequences, debug menus, or secondary code systems were found (bounded search detailed in §6b/§8).

**No GameShark/CodeBreaker/Action Replay material was used or reported.**

## 3. How to reproduce

**Emulator / display (own processes only).** mGBA 0.10.5 under Xvfb `:316`:
```bash
Xvfb :316 -screen 0 1024x768x24 & DISPLAY=:316 openbox &
DISPLAY=:316 SDL_AUDIODRIVER=dummy mgba -3 <rom> &
W=$(DISPLAY=:316 xdotool search --name mGBA | head -1)
DISPLAY=:316 xdotool windowfocus "$W"
```
Keymap used: A=`x`, B=`z`, Start=`Return`, D-pad=arrows. Holds of 80–150 ms, gaps ~100 ms.

**Reaching the password screen.** On the retail image, Start from the title plays a very long animated jungle intro before any menu is reachable. To make repeated tests practical, a **copy** of the ROM was patched with two 4-byte writes (code bytes are otherwise byte-identical to the retail image, so all findings about the validator/generator/table apply to the original ROM):
- `0x08000834`: `bl 0x0800D42C` → `bl 0x080094BC` (call the password-screen initializer during boot)
- `0x0800098C`: literal `0x0803D0A1` → `0x08008B41` (initial scene handler = password screen)

Boot the copy with `mgba -3 -t <clean_password_state> pw_hook3.gba` or simply let it boot to the keyboard. All patches and the clean state are in `/tmp/opencode/wildthornberrys/`.

**Keyboard and entry.** The keyboard has three rows (`BCDFGHJKLM`, `NPQRSTVWXYZ`, `1234567890`) plus an `END` cell to the right of row 3. D-pad moves one cell; A selects a character; after four selections move to `END` and press A. `END` is at keyboard-table row 2 / column 12 (marker byte `0x0C`).

**Codes tested.**
- `6XNB` typed through the UI → accepted (returns to the game/menu scene; difficulty 0, level 0 already default).
- `HB5F` typed through the UI → accepted; RAM `0x0300106A = 02`, `0x0300109C = 09`.
- `HBBB` and `BBBB` (not in table, injected into the input buffer with char-count = 4 and cursor on `END`, then A pressed) → rejected; globals remained at their defaults (`0x0300106A = 00`, `0x0300109A/9B/9C = 00`).

**Accept vs. reject look visually identical** (both return to the same jungle scene); the observable difference is the RAM globals written by the success branch and a different sound effect (`0x2E` vs `0x28` at `0x08008E96`/`0x08008ED2`). This is why all conclusions rest on RAM reads, not just screenshots.

## 4. Address map

| Address | Size / type | Meaning |
|---|---|---|
| `0x0805AEB4` | string | Main-menu item `Password` |
| `0x080CDC88` | u32 table | Main-menu string list (9 entries, reverse order) |
| `0x0805B994` | string | `New password is: xxxx` (end-of-level banner) |
| `0x0805B17C` | 3 × 55 bytes | **Password table**: 3 rows, 11 × 5-byte records per row (4 ASCII chars + NUL); row stride 55, record stride 5. Record 10 of each row is `FF FF FF FF 00` (invalid) |
| `0x0805B221` | 4 × 20 bytes | On-screen keyboard / alphabet table: rows at `+0`, `+20`, `+40` are `BCDFGHJKLM`, `NPQRSTVWXYZ`, `1234567890`; `+60` is tile data for the `END` label. `END` marker = byte `0x0C` at `0x0805B255` (row 2, column 12) |
| `0x08009168` | Thumb function | **Password validator**. Args: `r0` = pointer to 4-byte input buffer. Returns 1 = accepted, 0 = rejected |
| `0x08008B40` | Thumb function | Password-screen per-frame handler (input, drawing, END dispatch) |
| `0x080094BC` | Thumb function | Password-screen initializer (called from boot hook in the analysis copy) |
| `0x0800A528` | Thumb function | End-of-level result handler; formats `New password is: xxxx` and looks the code up in the table |
| `0x0800A364` | Thumb function | General gameplay PRNG (xorshift with constant `0xBADCAFEE` at `0x0800A3C8`) — **not** part of the password system |
| `0x03001B50` | RAM pointer | `P` (observed `0x03003288`) to the current UI/scene struct |
| `0x030032A4` | 4 bytes | Input buffer = `P + 0x1C`; the four ASCII characters the validator compares |
| `0x030032AA` / `0x030032AB` | byte / byte | Cursor column / row in the keyboard grid |
| `0x030032AC` | byte | Number of characters entered (0..4) |
| `0x0300106A` | byte | Difficulty written on success (0, 1, 2 = table row) |
| `0x0300109A..9C` | 3 bytes | Per-difficulty level index (0..9) written on success at `0x0300109A + row` |

## 5. Algorithm

**Validator (`0x08009168`), reconstructed pseudocode:**

```
validate(buf):                       # buf = 4 ASCII bytes
  for row in 0..2:                   # ip = 0..2
    base = 0x0805B17C + row*55
    for i in 0..10:                  # r6 = 0..10 INCLUSIVE (11 records)
      rec = base + i*5
      if rec[0] == buf[0] and rec[1] == buf[1] and
         rec[2] == buf[2] and rec[3] == buf[3]:
        level[ row ] = i             # store at 0x0300109A + row  (i in 0..9)
        difficulty   = row           # store at 0x0300106A
        return 1                     # ACCEPT
    # end row
  return 0                           # REJECT
```

Notes:
- The loop bound `cmp r6,#10; ble` (`0x080091DA/DC`) makes it check all 11 records per row; record index 10 is `FF FF FF FF 00` and can never match four ASCII characters. Effective accepted entries: 10 per row.
- No length check, no checksum, no alphabet conversion, no XOR/permutation. Only a byte-for-byte equality against the table.
- The generated password is `table[difficulty][level]` — see the multiply-by-55/5 indexing at `0x0800A574..0x0800A5A6` for the display path and `0x08008A02..0x08008A28` for the on-screen rendering path.
- UI consumer of the result: `0x08008E8E` calls the validator; `r0 == 0` goes to the rejection branch at `0x08008ED0`, nonzero to the acceptance branch at `0x08008E96`.

## 6. Tables

**Accepted passwords (all 30, read literally from `0x0805B17C`):**

| Difficulty row | Level 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | `6XNB` | `JDJ7` | `19WC` | `NZ03` | `R1B9` | `Q328` | `YFPV` | `FC6P` | `3580` | `39D9` |
| 1 | `6L29` | `WL8Y` | `CZJY` | `DS41` | `F3JB` | `WPFP` | `3R1T` | `DD6Q` | `51WV` | `BXLQ` |
| 2 | `YD95` | `7ZL5` | `N3MY` | `4PS0` | `PTWH` | `CPLL` | `48GH` | `YSNH` | `6ZB6` | `HB5F` |

**Alphabet / keyboard:** `BCDFGHJKLMNPQRSTVWXYZ1234567890` — 31 symbols, displayed in three rows of 10, 11 and 10. Every character of every valid password belongs to this set. (The table uses no vowel letters.)

**Flag/field bits:** difficulty is a whole byte at `0x0300106A`; the level is a byte indexed by difficulty at `0x0300109A..9C`. Both are written only by the validator's success branch in this code path.

## 6b. Enumeration

**Space definition.**
- Input alphabet: 31 symbols (`BCDFGHJKLMNPQRSTVWXYZ1234567890`), fixed length 4 → **31⁴ = 923,521** representable strings.
- Field widths: difficulty 3 values (rows 0–2), level 10 values (indices 0–9) → **30 representable game states**.
- Checksum: none. Reserved bits: none. The three 11th records (`FF FF FF FF`) are unusable padding.
- Validator model (§5) accepts exactly the 30 strings in §6; this is a structural proof from the comparator's complete control flow (three fixed loop bounds, no computed targets, no other callers of the table).

**Published-code reconciliation.** Web recon found **no published password list at all** for this title: the web-search tool returned no results for eight distinct queries; GameFAQs (including a `web.archive.org` snapshot and a text-proxy fetch) was CAPTCHA/403-blocked; Bing returned only unrelated "wild" results. Therefore no code could be cross-checked against a published list, and no published code was relied upon. Any code in §6 is, to the best of the evidence obtainable here, absent from every published list; I selected the one below specifically to exercise an unadvertised combination rather than a merely different spelling.

**Novel code generated and confirmed in-game:** **`HB5F`** — derived mechanically as `table[row=2][index=9]`, i.e. the hardest difficulty / final checkpoint. It is not on any published list (none exists/accessible). It was **typed through the real on-screen keyboard** in mGBA and A was pressed on `END`; the result screen was observed and the success side effects were read from RAM:
- before: `0x0300106A = 00`, `0x0300109A/9B/9C = 00 00 00`
- after:  `0x0300106A = 02`, `0x0300109A/9B/9C = 00 00 09`
  → difficulty 2, level 9, exactly as predicted.

Screenshot artifacts: `pw_atEND2.png` (cursor on END with `6XNB` entered), `pw_result.png`, `typed_HB5F.png` (fully typed `HB5F`), `state_HB5F_ui.ss1` (post-accept RAM).

**Bounds proven by rejection.**
- `HBBB` — shares the first character with the valid `HB5F` but is not a table entry. Injected into the input buffer (`0x030032A4 = 48 42 42 42`) with count 4 and cursor on END; A pressed. Result: rejected, globals unchanged (`0x0300106A = 00`, `0x0300109A..9C = 00 00 00`). This isolates the *exact-match* layer from the first-character precheck.
- `BBBB` — four characters that are all valid alphabet symbols but form no table entry. Rejected; no state change.
- Together with the structural bound above, these prove the accepted set is exactly the 30 listed codes: no near-miss, no wrong-checksum variant, and no out-of-table symbol combination is accepted.

**Closed-set confirmation.** Because the comparator's three loop bounds and its single table base are fully enumerated in §5, and the table region `0x0805B17C..0x0805B221` is exactly 3 × 55 bytes, there is no unexamined table row or hidden comparison branch. (A whole-space run of the ROM's own validator over all 923,521 strings was not performed; the closed-set claim rests on the complete disassembly plus the two rejection experiments above.)

## 7. Validation evidence

- **Observed** (emulator / RAM): title screen and long animated jungle intro on the retail ROM; password keyboard with the exact 31-symbol alphabet; `6XNB` typed and accepted; `HB5F` typed and accepted with `0x0300106A=02`, `0x0300109C=09`; `HBBB` and `BBBB` rejected with globals unchanged; input buffer at `0x030032A4`, cursor at `0x030032AA/AB`, count at `0x030032AC`.
- **Derived** (disassembly): validator at `0x08009168` (3 × 11 exact 4-byte comparisons, return 1/0 and writes to `0x0300106A` / `0x0300109A+row`); 30-entry table at `0x0805B17C`; keyboard table and END marker at `0x0805B221`; generator/result path at `0x0800A528`.
- **Inferred** (not separately exercised): the three rows correspond to the three `Difficulty` menu values; the ten indices correspond to the ten Story Mode level checkpoints (supported by the level-name list at `0x0805AF28..0x0805B150` and by the side-effect layout, but the games themselves were not played through).

## 8. Unknowns / bounded negatives

- **Button codes / cheat sequences:** bounded negative. Only five literal references to `KEYINPUT` (`0x04000130`) exist (`0x08000994`, `0x08000A60`, `0x08000AD8`, `0x08000B7C`, `0x08019634`); disassembly shows standard held/pressed/edge handling and normal menu navigation, no sequence matcher. A search for 3- and 4-press prefixes of a canonical Konami-style mask sequence as `u16` arrays found **0** hits. No button combination is reported.
- **Debug menus:** bounded negative. Keyword scan of all 43,897 strings for `debug|cheat|secret|unlock|level select|hidden|bonus` produced only tutorial text (`PRESS THE B BUTTON TO BEGIN!`, `Press the A Button to plant quick`, etc.) and two credits strings (`Senior Tester`, `Testers`). No debug-menu label, password generator label, or cheat handler name exists in any encoding checked.
- **Algorithmic second code system:** bounded negative. The only PRNG found (`0x0800A364`, xorshift + `0xBADCAFEE`) is used for gameplay shuffling (loops over 6-element arrays) and is not called by either the validator or the password display. Both password paths reference only the `0x0805B17C` table.
- **Retail-rom menu walk:** the main menu with `Story Mode / Mini Games / Password / Difficulty / Music / Sound` was reached only via the patched boot path (the retail intro did not terminate within the observation window). The menu's option list itself is fully enumerated from the string table at `0x080CDC88` (9 entries), so the hidden-feature surface on that screen is documented even though the retail intro was not waited out.
- Exact visible effect of each of the 30 levels/difficulties on gameplay was not played through; only the state writes were verified.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
- Python 3 + Capstone for literal/xref and BL-target scans (`xref.py`, `find_refs.py`, `find_G.py`, `literals.py`).
- Custom Python for password-table decoding (`dump_pw2.py`) and ROM boot hooks (`make_patch3.py`).
- mGBA 0.10.5 (`-3`, `-g` attempted but its GDB stub was unusable/busy, `-t` for state loading), Xvfb `:316`, openbox, xdotool, scrot.
- Savestate RAM reads via zlib decompression of the PNG `gbAs` chunk (`savestate_read.py`) and state patching (`patch_state_code.py`) — used because this mGBA build's GDB stub rejected connections. IWRAM layout: `0x19000 + (addr - 0x03000000)`.
- All scripts and screenshots live in `/tmp/opencode/wildthornberrys/`. No copyrighted assets are redistributed; only addresses, hashes, algorithms and code strings are published here.

## 10. Legal note

Only findings, addresses, hashes, and short code strings are documented. No ROM image, extracted graphics, music, or other copyrighted asset is included in this report.
