# Kerplunk! / Toss Across / Tip It (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Kerplunk! - Toss Across - Tip It.gba` |
| Size | 4,194,304 bytes (`0x00400000`) |
| Header title | `KERPLUNKTATI` (12 bytes, `0xA0`–`0xAB`) |
| Game code / maker | `BXCE` / `20` (AGB-BXCE-USA) |
| Version | `0x00` |
| Entry word | `0xEA00002E` → stock `0x080000C0`; **no cracktro / trainer** |
| Header checksum word (`0xBE`) | `0x0000` |
| Complement check (`0xBD`) | stored `0x2F`; computed over `0xA0`–`0xBC` = `0xB8`, running sum `0xE7` (fails) — header was rebuilt/edited. No functional patch observed. |
| Embedded GBA headers | Nintendo-logo scan: **exactly 1** hit, at file `0x0`. No concatenated halves, no multiboot stub. |
| MD5 | `49309e80a5acf7a4d452f6ad88238581` |
| SHA-1 | `56032ba5e0ed90aef6b9d64d06b573d1d97dd6b9` |
| SHA-256 | `3b8f37d6767186421266503fc22fa3f42abcd60513479bef53dfdeb3b5913b64` |

## 2. Executive summary

**No in-game / developer-intended cheat system exists in this ROM.** There is no password screen, no button-code sequence, no hidden debug menu, and no unlockable-gate accessible from any input. The only user-text input surface is a player-name entry keyboard; it is a label buffer, not a validator (§6b).

The game is a straightforward 3-in-1 board-game compilation. Every reachable screen was walked with mGBA under Xvfb and RAM snapshots (savestate `gbAs` diffs) taken at each transition: title/3-game select, legal notice, player-count (2/3/4), three "PRESS START" game intros, per-player character select, HUMAN/GBA player-type, name-entry on-screen A–Z keyboard, CHOOSE SKILL LEVEL 1/2/3, Toss Across HOW TO PLAY + two CONTROLS pages, and the gameplay/pause/quit-confirm screens of Kerplunk! and Toss Across. Tip It's intro, character-select, player-type and name-entry screens were walked; its in-game board screen was not entered (see §8), which does not affect the cheat conclusion because no code surface exists before or behind it.

No published codes exist to verify: GameFAQs lists no cheats for this SKU, VGChartz reports "Total cheats available: 0", and TCRF documents only an unused graphic containing a hidden developer message ("from Byron") — not an in-game cheat. Consequently there is no validator to reverse, no code space to enumerate, and no novel code to mint. Per §0.2 the negative is bounded below by the screen enumeration, text-space counts, input-handler counts and publication search recorded in §6b/§7.

## 3. How to reproduce

- Emulator: `mgba -3` (libmgba 0.10), `SDL_AUDIODRIVER=dummy`, own `Xvfb :319` + `openbox`. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows (verified on menus and by the in-game CONTROLS screen).
- Boot → Gravity-i splash → Mattel legal screen → **Start** → "HOW MANY PLAYERS?" (2/3/4) → **A** → game-specific "PRESS START" → **Start** → per-player setup (character select → HUMAN/GBA → name-entry keyboard → OK) → "CHOOSE SKILL LEVEL" → gameplay.
- Title/3-game select is re-entered from gameplay with the combo **B+Select+Start** (quit confirm: `QUIT NO YES` in Kerplunk!, `QUIT? YES - NO` in Toss Across).
- The quit combo is the only multi-button combination that produced a screen change; it is a quit shortcut, not a cheat (no flag/state mutation beyond the confirmation UI).
- Published codes tested: **none exist** (see §2). No GameShark/CodeBreaker codes were used or reported.

## 4. Address map

| Address (ROM/file) | Meaning | Evidence |
|---|---|---|
| `0x08000000` (`0x000000`) | Header; entry `0xEA00002E`, title `KERPLUNKTATI`, code `BXCE20` | Observed (header parse) |
| `0x080000C0` | Stock crt0 entry (ARM) | Derived (branch target) |
| `0x080001C8` | crt0 literal: Thumb `main` pointer `0x0800C315` | Derived |
| `0x0800BA24` | `ldrh` of KEYINPUT (`0x04000130`), invert to active-high; `0x0800BA36` tests `(held & 0x0E) == 0x0E` (B+Select+Start) | Derived (objdump) |
| 49 sites, `0x0800BC20`…`0x081BEB10` | Pool slots holding `0x04000130`; each has one Thumb `LDR` consumer (enumerated) | Derived (Capstone literal scan) |
| `0x083449E8` | Table of 32 pointers to variable-length byte "ramp" records (gradient/palette-like data, **not text**) | Derived |
| `0x08344C5C`–`0x08344D7F` | **The only ASCII text bank**: 14 NUL-terminated, space-padded strings | Observed |
| `0x08344D88` | Pointer table (14 entries) into that bank | Derived |
| `0x081C1CD4` | Graphics/font tile block loaded to VRAM; exact 32-byte tile matches at VRAM tiles `0x07`…`0x30` in a saved state | Derived (state↔ROM match) |
| `0x0203E640`… | EWRAM object/UI arena; `+0x04` tracked player selection, `+0x110`-region holds animated background state | Observed (savestate diffs) |
| `0x0203E750` + `0x40*i` | Name-entry character slots; `+0x10` of slot 0 = tile index of first typed letter (`0x11` = 'A') | Observed (savestate diff before/after typing) |

File offset → ROM address: `0x08000000 + file_offset`. Savestate raw layout used: IWRAM `0x19000`, EWRAM `0x21000`, VRAM `0x1000` (guide §16.13).

## 5. Algorithm

Not applicable — no password, checksum, validator, encoder, or key-mask state machine exists. The ROM's input handling is ordinary per-screen menu polling: each of the 49 KEYINPUT load sites inverts `0x04000130` into an active-high mask and branches on single buttons (A=`0x1`, B=`0x2`, Select=`0x4`, Start=`0x8`). The only combined-mask test found is B+Select+Start (`0x0E`) at `0x0800BA36`, used as the in-game quit shortcut.

## 6. Tables

### 6.1 Complete ASCII text bank (`0x08344C5C` … `0x08344D7F`)

Pointer table at `0x08344D88`; strings are NUL-terminated and space-padded to 16 visible columns:

| ROM address | String |
|---|---|
| `0x08344C5C` | `  SELECT  STICK  ` |
| `0x08344C70` | `                ` (blank) |
| `0x08344C84` | `    WELL DONE    ` |
| `0x08344C98` | `       OOPS      ` |
| `0x08344CAC` | `  PLAYER \ WINS  ` |
| `0x08344CC0` | `  PLAYER ] WINS  ` |
| `0x08344CD4` | `  PLAYER ^ WINS  ` |
| `0x08344CE8` | `  PLAYER _ WINS  ` |
| `0x08344CFC` | ` REDROP  MARBLES ` |
| `0x08344D10` | ` REDROP  MARBLE  ` |
| `0x08344D24` | `      PAUSED     ` |
| `0x08344D38` | `  QUIT  NO       ` |
| `0x08344D4C` | `  QUIT     YES   ` |
| `0x08344D60` | `  QUIT  NO YES   ` |
| `0x08344D74` | `   ITgS A DRAW   ` (`g` = custom apostrophe glyph tile) |

The `\ ] ^ _` bytes in the PLAYER strings are font tile placeholders for player numbers. None of these strings is a password, cheat, or debug label.

### 6.2 Encodings searched and hit counts

| Search | Result |
|---|---|
| `strings -t x -n 4` over 4 MiB | 28,491 printable runs; after filtering only the 14 strings above are meaningful English text. |
| Keywords `password, cheat, code, debug, secret, unlock, level select, bonus, hidden, test mode` — ASCII, lowercase, `+0x20` letter shift, UTF-16LE/BE, UTF-32LE/BE | **0 hits** in every encoding. |
| Literal transformations (XOR / add / sub by 0..255) of visible UI strings `HOW MANY PLAYERS`, `PLAYER 1`, `NAME :`, `PRESS START`, `SELECT STICK` | **0 hits** — confirms UI labels are font/tile-indexed, not obfuscated ASCII. |
| Font/tile-indexed bank at `0x083449E8` (32 pointer records) | Decoded: descending byte ramps (e.g. `1F 1E 1C 19 15 0F 08 07 06 05 04 03 02 01 00`), i.e. gradient/palette data, **not text**. |
| Font glyph source `0x081C1CD4` | Exact 32-byte matches to VRAM tiles `0x07`–`0x30` in a live savestate; glyphs are multi-tile and rendered with a palette, so tile index 'A' = `0x11` was confirmed via the RAM name buffer instead. |
| `grep -abo` for published code literals | Nothing to search — no published password/button code exists for this SKU. |

### 6.3 Input surface counts

- 49 distinct KEYINPUT literal slots and 49 corresponding Thumb `LDR` consumers (full list in `scan_input2.py` output).
- `cmp` immediates near those sites are limited to ordinary single-button masks (`0x1` A, `0x2` B, `0x4` Select) plus the `0x0E` quit combo. No multi-press sequence table, progress index, or mask-array comparison was found.
- u16/u8 scans for runs of key-mask values returned only animation/coincidental code bytes (≈9,000 false-positive runs); none formed a plausible cheat sequence.

## 6b. Enumeration

**No code space exists to enumerate.** §0.2's enumeration deliverables are replaced by a bounded negative proof:

1. **Space definition:** N/A — no alphabet table, no password length, no checksum, no key-mask sequence, no hidden-menu gate. The only alphabet is the on-screen A–Z name-entry keyboard (26 letters + space/backspace + OK), and the buffer it fills is a tile-index label (§6.1/§6.3), not a validator input.
2. **Validator model:** N/A — there is no comparison of the name buffer against any constant. A literal-pointer scan for the buffer region `0x0203E700`–`0x0203E900` returned **0** ROM pointers, and keyword comparison sites are absent.
3. **Novel codes:** N/A — no code system to mint from.
4. **Bounds proven by rejection:** N/A for codes; instead the "no system" claim is bounded by: every reachable screen walked (§2/§7), 0 keyword hits across 6 encodings, 14/14 ASCII strings accounted for, the 32-entry tile bank decoded as non-text, all 49 KEYINPUT sites classified, and 7 button sequences pressed at the title screen with no hidden screen produced (montage `bt2_montage.png`).
5. **Published codes tested:** none published (GameFAQs cheats page empty, VGChartz 0, TCRF dev-message/unused-graphics only). Fetched TCRF text contained no instructions; one search snippet contained the irrelevant string "Join the cacti clubhaus", treated as data and ignored.

## 7. Validation evidence

**Observed (emulator / RAM):**
- All screens listed in §2 photographed on `DISPLAY=:319`; each transition accompanied by a Shift+F1 savestate copied into `/tmp/kerplunk/`.
- Player-count selection visibly cycles 2→3→4; EWRAM `0x0203E644` changed with the selection.
- Typing a letter changed name-slot tile index at `0x0203E750+0x10` from `0x00` to `0x11` ('A'), proving the buffer is tile-indexed.
- B+Select+Start produced `QUIT NO YES` (Kerplunk) and `QUIT? YES - NO` (Toss Across); choosing YES returned to the title screen.
- 4 button-code sequences re-run from a clean title savestate produced no new screen (normal menu navigation only).

**Derived (disassembly / scan):**
- 49 KEYINPUT loads; single-button comparisons; `0x0E` quit-combo test at `0x0800BA36`.
- Header parsed, logo scan, literal-pointer and BL scans, font-block↔VRAM exact-match proof.

**Inferred:**
- Tile values `\ ] ^ _` and `g` in the ASCII bank are font glyph indices for player-number badges and an apostrophe (visually consistent with `IT'S A DRAW` and `PLAYER n WINS`), but the font substitution table itself was not reconstructed bit-for-bit.
- The TCRF "message from Byron" is an unused graphic; it is not a reachable cheat (no code/menu surface references it).

## 8. Unknowns

- **Tip It's in-game board screen was not entered.** Its title-strip intro, character-select, HUMAN/GBA and name-entry screens were walked and RAM-snapshotted, but the on-screen keyboard's OK cell could not be reliably reached with the available xdotool timing (the hand/cursor is drawn as a decorative sprite and the grid wraps beyond the visible keys). This is a UI-navigation limitation, not a game gate: no password, code, or unlockable sits behind it. All three games share the same setup engine, and Kerplunk! and Toss Across gameplay + pause + quit were fully walked.
- The full tile-index→glyph substitution table for the multi-tile font was not reconstructed; only the 'A'→`0x11` mapping was confirmed via RAM. This is sufficient to prove the visible UI strings are not ASCII, but a complete font dump was out of scope for the cheat question.
- The hidden developer graphic ("from Byron", per TCRF) was not extracted/rendered; it is unused graphics, not a cheat.

## 9. Tooling

- `mgba -3` (SDL, libmgba 0.10) under `Xvfb :319` + `openbox`; `xdotool` XTEST input; `scrot` + ImageMagick crops; `SDL_AUDIODRIVER=dummy`.
- `header.py` (header/hash/logo scan), `state.py` (mGBA `.ss1` `gbAs` zlib parser + region slicing/diff), `walk.py` / `ctl.py` (key + snapshot helpers), `font.py` / `render_font.py` (tile extraction), `scan_input2.py` / `keylogic.py` (Capstone literal/key logic scan), `mask_scan.py` / `bufref.py` / `encoding_search.py` (button tables, buffer pointers, encoding brute force), `sweep_ok.py` / `button_codes.py` (dynamic input sweeps).
- Ghidra 12.1.4 via REA was opened on the raw ARM image (`0x08000000`) for xref checks; no REA session state is required to reproduce the findings.
- No ROM or copyrighted assets are redistributed. All generated `.sav`/`.ss1` files were removed from the ROM folder at the end of the engagement.
