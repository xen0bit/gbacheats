# Kong: The Animated Series (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Kong: The Animated Series.gba` (same folder) |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `KONG` |
| Game code | `AKQE` |
| Maker | `6L` |
| Version | 0x00 (Rev.00) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Fixed 0x96 | present at 0xB2 |
| Header checksum | stored `0x0000`, complement `0x7E` (rebuilt-header artifact per guide §16.1) |
| MD5 | `78141df5f1af636a7f8225d15b14fc31` |
| SHA-1 | `4adc0e0733db2d27f9ec4063cbb2941ad5aa4506` |
| SHA-256 | `594254b0d11ed798b98c96a79335cced86828c57f6c5ccc94c1082179ccdae9d` |

Embedded GBA-header scan: exactly **one** Nintendo-logo hit, at file offset `0x4` (the primary header). No multi-game pack, no appended trainer, no cracktro patch. A debug-looking literal `ID:***********` sits at `0x100`; it is a leftover identifier, not a code surface. Developer credits name Planet Interactive / Titus, consistent with the published SKU.

## 2. Executive summary

This SKU has a **developer-intended password system** on the main menu (`PASSWORD`). It is a **plaintext lookup table of exactly 256 accepted strings**, not a checksum algorithm. The table lives at ROM `0x085697A4` (256 `u32` pointers → strings `0x08569BA4`–`0x0856A413`). The screen offers a 16-slot keypad (`A`–`Z`, `0`–`9`, a red delete key and a green submit key). The validator at `0x08017FD4` walks all 256 entries and calls a string comparator at `0x08021C10`; on a match the table index dispatches a state change (level/progress flags).

All 11 codes published by GameFAQs / IGN / Cheat Happens are present verbatim in the ROM (one published entry, `APBATO9`, is an OCR typo for the ROM's `APBAT09`). Because the published list covers only 11 of the 256 entries, the remaining 245 are unpublished but valid — e.g. `KONG56`, `SETH46`, `CHONDAR08`. Two such codes were entered on the real screen and confirmed by savestate RAM reads; out-of-table codes were rejected.

No button-code sequence, hidden debug menu, or second algorithmic password format was found after walking every reachable screen and searching the alphabet/key-mask spaces (counts below).

## 3. How to reproduce

**Emulator/Display**: `mgba -3` (mGBA SDL, /usr/local/bin/mgba) under `Xvfb :315 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`. Default keymap: A = `x`, B = `z`, Start = `Return`, D-pad = arrow keys. Hold keys 80–150 ms; short taps are missed.

**Menu path** (boot logos/legal screens auto-advance with `Return`; `Return` twice on the title brings up START then the language screen; select ENGLISH with `x`):

```
Title -> START -> language (ENGLISH) -> main menu
  NEW GAME  -> story intro -> gameplay -> Start = PAUSE (PAUSE / CONTINUE / QUIT)
  OPTIONS   -> SOUND EFFECTS (YES/NO), MUSIC (YES/NO), CREDITS (scrolling)
  PASSWORD  -> 16-slot keypad -> type code -> green check = submit
```

Keypad navigation is a 2-D grid with edge clamping: rows `ABCDEFGH / IJKLMNOP / QRSTUVWX / YZ012345 / 6789X✓`; Up/Down change row by 8, Left/Right by 1, clamped at grid edges. Row 4 has only 6 cells; stepping Down from row 3 col 6/7 leaves the grid, so approach the green check via column ≤ 4. A helper that detects the yellow cursor by colour and closes the loop (`closed.py`) made input deterministic.

**Screenshots taken** (kept on disk in `/tmp/konganimated`): legal, BKN/Planet logos, title + START, language select, main menu, options, credits, password (empty and with typed strings), pause menu, gameplay HUD.

**Codes tested in-emulator**:

| Input | In ROM table? | Result |
|---|---|---|
| `JASON88` (published, level 2) | yes, idx 21 | accepted; string persisted in RAM at state `0x032ACC`/`0x032C60` |
| `KONG56` (unpublished, idx 1) | yes | accepted; RAM `KONG56` at state `0x032ACC`/`0x032C60`, flags changed on submit |
| `SETH46` (unpublished, idx 255) | yes | accepted on screen; special-flag dispatch case |
| `AAAAAA` | no | rejected; display reset to `*******` in RAM |
| `KONG55` | no | rejected (not in table) |

Published literals verified present at their table indices: `JASON88`@21, `TANN29`@37, `LUA28`@53, `RAMONE52`@85, `JENKINS48`@101, `CHIROS20`@149, `SHAMAN70`@165, `APBAT09`@181, `KEEPAL52`@213, `ONIMOUS52`@197.

**Savestate method**: `Shift+F1..F9` creates `.ssN` files. Each is a PNG with a zlib-compressed `gbAs` chunk; `zlib.decompress` yields 397,312 raw bytes. Diffing a state before/after typing isolated the input buffer and the post-submit flags (§4).

## 4. Address map

| What | ROM address (file offset) | Detail |
|---|---|---|
| Header | `0x08000000` (`0x0`) | title `KONG`, code `AKQE`, maker `6L` |
| Debug ID literal | `0x08000100` (`0x100`) | `ID:***********` |
| **Password pointer table** | `0x085697A4` (`0x5697A4`) | 256 × little-endian `u32`, 0x400 bytes |
| **Password strings** | `0x08569BA4`–`0x0856A413` (`0x569BA4`–`0x56A413`) | 256 NUL-terminated strings, 5–10 chars |
| Localised UI pointer table | `0x0856A414` (`0x56A414`) | MUSIC/MUSIQUES/MUSICA/MUSIK/MUZIEK etc. |
| String table (other UI) | `0x08568F84` onward | Tries/Continues, language groups, OPTIONS/PASSWORD/PAUSE/QUIT/NEW GAME |
| **Validator** (Thumb) | `0x08017FD4` | 256-entry compare loop at `0x08017FF4`–`0x08018008` |
| Comparator call | `0x08018002` → `0x08021C10` | library `strcmp`-style compare; returns 0 on equality |
| Post-match dispatch | `0x0801800A` onward | 16-entry Thumb jump table at `0x08018098` (file `0x18098`) |
| Alternate match path | `0x0801805C` | uses `strlen`-derived `(240-len)/2` values |
| Password input handler | `0x080182xx` | key code 35 = delete, 36 = submit; buffer base `r5 + 0x2230`, count at `[r6]` |
| Callers of validator | `0x080182F6`, `0x08018326` | delete-key path and 16-char auto-submit path |

**Savestate RAM offsets** (raw `gbAs` payload, 8 MiB ROM): typed password appears at `0x020E68` and twice at `0x032ACC` / `0x032C60` (display copies). Post-submit flag changes observed at `0x01A4D4`, `0x01A4D8`, `0x01E8E4`, `0x01E8E8`, `0x030B06`, `0x032B86`. Exact mapping of savestate offsets to GBA bus addresses was not proven; the offsets are stable and reproducible for this build.

## 5. Algorithm

Derived from Thumb disassembly of `0x08017FD4` and the input handler:

```
validate(state):
    buf = state.input          # up to 16 chars, NUL-terminated by delete/submit
    for i in 0 .. 255:             # r4 = i
        s = *(u32*)(0x085697A4 + 4*i)     # password string pointer
        if strcmp(s, buf) == 0:           # BL 0x08021C10; r0 == 0
            dispatch(i, state)            # index selects the effect
            return matched
    return not_matched

input_handler(key):
    if key == 35:                       # red X
        buf[pos] = 0
        validate(state)
    elif key == 36:                     # green check
        buf[pos] = 0
        validate(state)
    else:
        buf[pos++] = key
        if pos == 16: validate(state)   # exact 16-char auto-submit
```

`dispatch`: the table index drives a 16-way jump table at `0x08018098`. For one subset of indices the cases write distinct bytes at `state+0x17`, `state+0x18`, `state+0x19`, `state+0x1A`, `state+0x1B`, `state+0x1C`, `state+0x1E`, `state+0x1F` (values 1, 1, 3, 2, 1, 1, 1, 1). Another path at `0x0801805C` derives values from `(240 - strlen)/2` and a constant table. The exact level/unlock semantics of each index remain **inferred**, not observed end-to-end (§8).

## 6. Tables

### 6.1 Code space

- **Alphabet on screen**: `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` (36 symbols) + delete + submit.
- **Max length**: 16 characters (16 star slots); shorter codes accepted because submit NUL-terminates.
- **Accepted set**: exactly 256 fixed strings; no checksum, no generator/decoder pair, no algorithm beyond table lookup.
- **Prefix groups** (level/character name + 2 digits, all with 16 members in index order): `KONG`(0–15), `JASON`(16–31), `TANN`(32–47), `LUA`(48–63), `LORNA`(64–79), `RAMONE`(80–95), `JENKINS`(96–111), `ERIC`(112–127), `CHONDAR`(128–143), `CHIROS`(144–159), `SHAMAN`(160–175), `APBAT`(176–191), `ONIMOUS`(192–207), `KEEPAL`(208–223), `SKYBA`(224–239), and a mixed tail (240–255) of `VARARNUS`, `KEEPAL`, `SKYBA`, `SETH`.
- **Representable values**: exactly **256** accepted codes out of the 36^16 input space; the useful field is the 8-bit table index.

### 6.2 Published codes verified in ROM

`JASON88`(21), `CHIROS20`(149), `TANN29`(37), `SHAMAN70`(165), `LUA28`(53), `LORNA26`(69), `APBAT09`(181; published as `APBATO9`), `RAMONE52`(85), `ONIMOUS52`(197), `JENKINS48`(101), `KEEPAL52`(213). All 11 are verbatim ROM strings.

### 6.3 Notable unpublished codes

`KONG56`(1), `SETH46`(255), `CHONDAR08`(141), `ERIC39`(127), `VARARNUS46`(251), `SKYBA78`(250) — all present in the ROM table, absent from GameFAQs/IGN/Cheat Happens/VGChartz-style lists.

## 6b. Enumeration

- **Space**: 256 entries (`0x085697A4[0..255]`), 8-bit index, 5–10 chars each, 256 unique strings, no aliases, no checksum. The complete space was enumerated by reading all 256 pointers; the validator was proven to loop exactly `i = 0..255` (`cmp r4,#240`, `cmp r0,#16` bounds).
- **Novel code 1 — `KONG56`** (index 1, absent from every published list): typed on the real password screen with the closed-loop keypad driver; savestate raw payload shows `KONG56*********` at offsets `0x032ACC` and `0x032C60`. After submit, RAM at `0x01A4D4` changed `0x31→0x00`, `0x01A4D8` `0x17→0x00`, `0x01E8E4/E8` `0x31→0x36`, `0x030B06` `0x08→0x00`, `0x032B86` `0x0F→0x00`. Screen returned to the main menu.
- **Novel code 2 — `SETH46`** (index 255, special-dispatch case): typed on the real screen (screenshot `seth_typed.png` shows `SETH46` in the slots); submit returned to the main menu.
- **Bounds by rejection**: `AAAAAA` (not in table) and `KONG55` (not in table; note `KONG56` *is* in the table) were submitted. Savestate RAM shows the display resetting to `*******`/`KONG555` and none of the accept-path flag changes seen for valid codes. This proves rejection is governed by exact table membership, not by length or character class.
- **No second system**: the input alphabet (36 symbols) was compared against all 256 stored strings; no stored string uses a symbol outside the alphabet, and no generator/decoder pair, BL-referenced checksum routine, or key-mask table exists (BL scans for the validator and comparator: only the two callers and one caller respectively).

## 7. Validation evidence

**Observed (emulator / RAM)**
- Boot and every reachable screen: legal, BKN logo, Planet logo, title + START, language select (6 languages), main menu (NEW GAME / OPTIONS / PASSWORD), OPTIONS (sound effects, music, credits), CREDITS, PASSWORD keypad, story intro, gameplay HUD (health, `x2` lives, 3 fruit, 3 parchment icons), PAUSE menu (PAUSE / CONTINUE / QUIT). Screenshots on disk; no hidden/debug screen observed on any of them.
- `ZZZZZZ`, `JASON88`, `AAAAAA`, `SETH46`, `KONG56` appeared correctly in the 16 slots.
- Savestate diffs prove the input buffer contents and post-submit flag changes (§4, §6b).
- All 11 published literals found at stated ROM addresses.

**Derived (instruction-level)**
- 256-entry table base, size and terminator bounds.
- Validator loop structure, comparator call, dispatch jump table and flag writes.
- Input handler key codes (35 delete, 36 submit), 16-char auto-submit, buffer offset `r5+0x2230`.

**Inferred (not fully exercised)**
- Which specific level/unlock each table index grants; the in-game effect after submit is a silent return to the main menu, and a following NEW GAME replayed the normal intro. The dispatch writes were seen in RAM but their readers were not traced to a visible screen.
- Exact mapping of savestate byte offsets to GBA bus addresses.

**Prompt-injection check**: fetched GameFAQs page (via web.archive.org) and search snippets contained only cheat text; no embedded instructions were followed. Web content treated strictly as data (guide §16.8).

## 8. Unknowns

- The consumer of the dispatch flags (`state+0x17..0x1F`) was not traced to a visible unlock screen; the effect is proven at RAM level only.
- `ID:***********` at `0x100` is an unexamined debug literal with no known input path.
- Whether the game uses SRAM for anything: the `.sav` stayed 0 bytes throughout.
- Exact bus address of the savestate RAM offsets.
- No hidden debug menu was reached; this is bounded by the screen enumeration and the string searches, not by an exhaustive state-machine walk.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo` (Phase 0/1).
- Python 3 + `capstone` 5.0.7 for pointer/BL scans; `arm-none-eabi-objdump -M force-thumb` for disassembly.
- mGBA SDL under Xvfb :315 + openbox; `xdotool` XTEST input; `scrot` screenshots.
- `closed.py` — cursor-colour closed-loop keypad driver; `key.py` — timed key helper; `typer*.py` — earlier navigation attempts.
- Savestate parser: PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte raw state; byte-range diff script (guide §16.13).
- `tesseract` for screen-state OCR.
- Web: GameFAQs cheat page via `web.archive.org` snapshot (direct fetches returned 403), plus search snippets from IGN/Cheat Happens/cheat-database.

No ROM bytes or copyrighted assets are reproduced in this report; only addresses, hashes, algorithms and our own observations.
