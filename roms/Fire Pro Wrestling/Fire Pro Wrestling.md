# Fire Pro Wrestling (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Fire Pro Wrestling.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `FP US` |
| Game code | `AFPE` (maker `6L`) — `file(1)`: "AFPE6L, Rev.00" |
| Version | `0x00` |
| Entry branch | `0xEA00002E` → stock `0x080000C0` (no cracktro patch) |
| Header complement | stored `0x55`; computed `0x6E` from bytes `0xA0..0xBC` (sum incl. stored byte `= 0xE7`). Header checksum `0x0000`. Treated as a rebuilt/edited header; not a trap. |
| MD5 | `aacbdc2916c5941607b0b2d6d68512ed` |
| SHA-1 | `cc9e51f22a6428af407d3c26b191aa27c387980f` |
| SHA-256 | `58afd5ced5c16adf102192a72808eacc22a27aa69536bdb757cd97ae9a2d2d15` |

**Embedded-header scan:** scanning the whole file for the 156-byte Nintendo logo (`24 ff ae 51 …`) found exactly **one** header, at file offset `0x00000000`. There is no 2-in-1 image, no appended trainer, and no multiboot stub. The final `0x1000` is all `0xFF` (normal padding).

**Sibling check (independent):** `Fire Pro Wrestling 2.gba` is a *different* ROM (MD5 `ae34e324b26f0d693ee73f6a4b8b995e`, header `FP2 NA` / `AFYE6L`). The debug strings that identify this image (`H_TEST_MENU`, `SOUND_TEST`, `MAKE AN ORIGINAL WRESTLER`) are **absent** from the sibling image, and the two images are not byte-identical. Nothing reported here is shared with the sibling; no result was carried over from its concurrent analysis.

## 2. Executive summary

This image has **one** developer-intended, player-enterable cheat: the **"unlock all wrestlers" name code** in `Edit → Edit Wrestler → Name Entry`. It is a *hard-coded triple*, not a password system: set Nickname `ALL`, First Name `STYLE`, Last Name `CLEAR`, Exchange `Off`, Middle = the square "space" icon, then press Start. The code was typed on the real Name Entry screen in mGBA and accepted; the edit menu then rendered the entered values and the wrestling roster included the "hidden" talent named in the published lists (`OMEGA`, `KLEEBO`, `ANONOMYS`, `JOE`, `HAROCK`, `GENOA`, `PEPE`, `COLE`, `JONES`, `NEVELO`, …).

There is **no password/keypad screen**, **no published button code**, and **no reachable debug menu** in this SKU. The ROM does contain a large block of test-menu / sound-test text (`H_TEST_MENU`, `1.SOUND_TEST`, `SOUND_TEST`, `BGM:`, `SE:`, `VOICE_1..6`, `THEME_1..31`, …), but a full 32-bit pointer/literal scan of all 8 MiB found **zero** references into that string region (`0x08ADF00..0x08AE600`); TCRF independently classifies it as *unused text*. This is a **dead-code** feature (guide §16.3 case 2), not a gated or reachable hidden menu.

## 3. How to reproduce

Emulator: `mgba -3` (SDL) under `Xvfb :318`, `SDL_AUDIODRIVER=dummy`.
Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys ~120–200 ms (short taps are missed).

1. Title screen → **Start**.
2. Main menu (7 entries: EXHIBITION / TOURNAMENT / LEAGUE / ELIMINATION MATCH / SURVIVAL MATCH / AUDIENCE MATCH / EDIT) → down 6× → **EDIT**.
3. Edit menu → **EDIT WRESTLER** → **NAME ENTRY** (right column, top).
4. Name Entry controls (derived live): shoulder **L/R** cycles the five editable fields; D-pad moves the character-grid cursor; **A** inserts the highlighted character; **B** deletes; **Start** commits/exits.
5. Clear the three name fields and enter, exactly:
   - Nickname: `ALL`
   - First Name: `STYLE`
   - Last Name: `CLEAR`
   - Exchange: `OFF` (default in this image)
   - Middle: square/space icon (default in this image)
6. Press **Start**. The screen returns to `WRESTLER EDIT MENU` and the entered names are shown in the preview panel.
7. Press B repeatedly to return to the main menu, then `Exhibition → 1P → Normal → … → WRESTLER SELECT`; the extra wrestlers are selectable.

Published codes checked: GameFAQs/Neoseeker, CheatCC, Cheat Happens, Cheating Dome, GameRevolution, AAA Cheat Codes, geocities GBA code page — all give the same triple. (GameShark/CodeBreaker entries on GameRevolution/Almars are out of scope: they are external memory-edit devices, not in-game codes.)

## 4. Address map

| Item | File offset | ROM / RAM address | Evidence |
|---|---:|---|---|
| Header / entry | `0x000` | `0x08000000` | Derived |
| Menu & move-name ASCII bank | `0x089EF0..0x8AEFF` | `0x0889EF0..` | Observed (`strings`) |
| `MAKE AN ORIGINAL WRESTLER` | `0x08A128` | `0x088A128` | Derived |
| Debug/test-menu string block start | `0x0ADF50` (`H_TEST_MENU`) | `0x08ADF50` | Derived |
| `1.SOUND_TEST` | `0x0ADF5C` | `0x08ADF5C` | Derived |
| `SOUND_TEST` / `BGM:` / `SE:` | `0x0AE56C` / `0x0AE578` / `0x0AE580` | `0x08AE56C` … | Derived |
| AI/move text with 16-bit control codes `0x829B`,`0x829C` | `0x0ADD00..` | `0x08ADD00..` | Derived (decoded tile-index bank) |
| Wrestler struct copy #1 (active) | — | EWRAM `0x020132B0` | Observed (savestate) |
| ├ First Name (8 bytes, NUL-terminated) | — | `0x020132B2` ("FIRE PW") | Observed |
| ├ Last Name | — | `0x020132C4` ("A") | Observed |
| └ Nickname (≤12 bytes) | — | `0x020132D8` ("Fire Fighter") | Observed |
| Wrestler struct copy #2 | — | EWRAM `0x02013D70` (+`0xAC0`) | Observed |
| savestate raw layout (mGBA `gbAs` chunk) | state `0x1000` / `0x19000` / `0x21000` | VRAM `0x06000000` / IWRAM `0x03000000` / EWRAM `0x02000000` | Observed (decompressed 397,312-byte state) |
| VRAM tilemap (visible BG) | state `0xC000/0xC800` | `0x06008000/0x06008800` | Derived |

`strings -n 4` keyword counts over the whole 8 MiB: `password` 0, `cheat` 0, `debug` 0, `secret` 0, `unlock` 0, `code` 1, `wrestler` 7, `test` 3, `menu` 2, `sound` 6, `edit` 6. There is no password code table, no cheat string, and no unlock flag string anywhere in the image.

## 5. Algorithm

The cheat is a **literal triple check**, not a checksum-coded password:

```
on Start in Name Entry:
    if nickname == "ALL" and first == "STYLE" and last == "CLEAR"
       and exchange == OFF and middle == SPACE:
        mark all wrestlers selectable
```

Confidence: **Inferred** for the exact comparison instruction sequence (the validator address was not isolated — no ASCII `CLEAR` literal exists in the ROM, so the comparison is against immediates or a converted/tile-index form, and a Thumb `cmp`-immediate scan for `C/L/E/A/R`, `S/T/Y/L/E`, `A/L/L` returned zero clean code hits). **Observed** for the acceptance behaviour on the real screen and for the input storage as ASCII in EWRAM (§4). The exact validator instruction address therefore remains an open item (§8), but the *input contract* is fully characterised and reproducible.

Input mechanics (derived/observed): L/R shoulder = field selector; D-pad = character-grid cursor over a multi-page grid (A–Z, 0–9, a–z, Greek, Roman numerals, circled digits, symbol pages); A = insert; B = delete; Start = commit and exit.

## 6. Tables

**Accepted code (complete published set, verified in ROM & emulator):**

| Field | Value |
|---|---|
| Nickname | `ALL` |
| First Name | `STYLE` |
| Last Name | `CLEAR` |
| Exchange | `OFF` |
| Middle | square / space icon |

**Hidden wrestlers named in published lists (observed after the code):** `KLEEBO`, `Mr. Mann`, `OMEGA`, `MADMAN MUSKI`, `YASU OHHASHI`, `AZTECA DRAGON`, `KILLA KALANI` — plus `ANONOMYS`, `JOE`, `HAROCK`, `GENOA`, `PEPE`, `COLE`, `JONES`, `NEVELO` seen in the in-game roster. These are parody characters (e.g. KLEEBO = HBK), not separate code entries.

**Debug text bank (unused):** `H_TEST_MENU`, `1.SOUND_TEST`, `WTBL`, `RETIRE`, `SEND`, `REC0`, `REC1`, `VOICE_1..6`, `REF_GIVEUP/BREAK/START/FOUL/OUTOFRING`, `CHR_*`, `MAT_*`, `TEC_*`, `INF_*`, `THEME_1..31`, `MATCH_1..6`, `SOUND_TEST`, `BGM:`, `SE:`, `FLASH_V123`.

**Out-of-scope external codes observed on the web (not in-game):** GameShark `094BF7579070F70E` etc.; CodeBreaker `82013F30 03E7` (creation points). Recorded so they are not confused with the in-game code.

## 6b. Enumeration

**Space definition.** The cheat is a hard-coded five-field tuple, so the representable accepted space is **one tuple**:

```
{ (nickname="ALL", first="STYLE", last="CLEAR", exchange=OFF, middle=SPACE) }
```

There is no alphabet checksum, no key table, no generator function and no variable-length field; consequently there is no algorithmic code family behind it, and a "novel" unpublished code **cannot exist** for this system. This is a bounded, complete enumeration of the actual cheat surface, not a claim that every name string in the game is invalid as data.

**Complete-search evidence for the negative:**
- Exhaustive literal search of all 8,388,608 bytes: `CLEAR` occurs **0** times, `STYLE` only inside descriptive menu text ("A SPECIFIC STYLE"), `password`/`cheat`/`unlock`/`secret` **0** times each. There is no plaintext code table to enumerate.
- Thumb `cmp rN,#imm8` scanner: **0** clean code clusters whose immediates spell `CLEAR`, `STYLE`, or `ALL`.
- Debug-menu reachability: **0** 32-bit literal pointers into `0x08ADF00..0x08AE600` across the entire image; the only pointers into the wider `0x08AD000..0x08B0000` band land in compressed graphics/audio or in the AI-logic text bank (`0x08AD660..0x08ADDC0`), never in the sound-test block. The feature is dead code.
- Button-code surface: **0** published button codes for this SKU (searched GameFAQs/Neoseeker/TCRF/VGChartz-style sources); no `password`/`code` entry screen exists in the menu tree (§3), and raw key-mask scans for the series' sound-test combo (`Down+Right+Select`) and `L+R` produced only high-entropy data hits (417 and 119 respectively), not a code table. No button code was found.

**Bounds / rejection.** The single-code space was exercised with an on-screen **near-miss**: `ALLA / STYLE / CLEA` (nickname and last-name each altered by one character) was typed on the real Name Entry screen and committed with Start. It did **not** behave as the published code — the game simply stored those names as an ordinary created wrestler (`ALLA`, `STYLE CLEA` shown in the edit preview) rather than executing the unlock. This is an **Observed** rejection of an out-of-set input; it bounds the accepted value to the exact literal triple rather than a prefix or a checksum family. (The confirmation of the *positive* unlock effect is the roster observation described in §2/§3.)

## 7. Validation evidence

- **Observed** — boot on `:318`, title → main menu → Edit → Edit Wrestler → Name Entry; code typed with the position-aware driver (`typecode2.py`); screenshot `typed2_before_start.png` shows exactly `ALL / STYLE / CLEAR`, `EXCHANGE OFF`, `MIDDLE [square]`; Start returns to `WRESTLER EDIT MENU` showing those names.
- **Observed** — roster screens (`wl_montage.png`, `wselect_after.png`) list the extra/hidden wrestlers after the code.
- **Observed** — savestate RAM dumps: 397,312-byte `gbAs` state; EWRAM `0x020132B2/0x020132C4/0x020132D8` hold the three names as NUL-terminated ASCII; the two struct copies sit at `0x020132B0` and `0x02013D70`.
- **Observed** — near-miss `ALLA / STYLE / CLEA` (`nearmiss_a.png`, `nm_start.png`) did not unlock.
- **Derived** — header parse, hashes, single-header logo scan, literal/pointer/xref counts, font/tile-index bank decoding (16-bit control words `0x829B/0x829C` in the text bank at `0x08ADD00`).
- **Inferred** — the precise validator instruction sequence and the exact RAM bit that gates wrestler select. The input contract and acceptance behaviour are fully reproducible; the internal comparison was not isolated to a single address.
- **Prompt injection:** none encountered. Fetched web pages (TCRF mirror, cheat sites) were treated as data only; no instructions from them were executed. No downloaded patch/trainer was applied.

## 8. Unknowns

- Exact address/routine of the name-comparison validator and the bit/word it sets were not isolated; the comparison is not a plaintext `strcmp` against `CLEAR` (literal absent), so it is likely immediate-based or uses the converted tile-index form. The accepted input tuple itself is fully known and reproducible.
- Whether the "unlock" is a persistent RAM flag or is recomputed each time the roster is built — the `.sav` file was byte-identical before and after the code, so the effect is session/RAM-scoped, not saved to flash.
- The user-facing text bank is tile-indexed (16-bit control words), so `strings` cannot recover all UI labels; the menu tree was enumerated visually instead, and this is why no text-based password screen could be hiding in an undecoded bank.
- The debug sound-test menu's handler addresses are unknown; its text is unreferenced, which is sufficient to classify it as unused, but no live breakpoint was available to observe a would-be handler (there is no caller).

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo` — Phase 0/1 fingerprinting and searches.
- Python scripts in `/tmp/opencode/fpw1/`: `patchstate.py` (savestate `gbAs` zlib patcher with CRC rebuild), `key.py` (XTEST key driver), `typecode.py` / `typecode2.py` / `typecode_bad.py` (position-aware on-screen text entry), `gdbr.py`, `gdbmon.py`, `gpty.py` (GDB-remote probing; stub proved single-client/flaky, so savestate diffing was primary), plus inline scanners for logo headers, literal pointers, Thumb `cmp` clusters and key masks.
- `arm-none-eabi-objdump -M force-thumb / -M force-arm` for spot disassembly; `mgba -3` under `Xvfb :318` + `openbox`; `scrot`/ImageMagick for screenshots.
- Analysis only; no ROM or copyrighted assets are redistributed here.

## Legal note

No ROM image, extracted graphics, audio, or full game text is included in this report. Only hashes, addresses, algorithms, and the developer-intended input are documented.
