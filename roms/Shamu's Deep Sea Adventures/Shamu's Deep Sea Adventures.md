# Shamu's Deep Sea Adventures (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Shamu's Deep Sea Adventures.gba` |
| Size | 33,554,432 bytes (`0x02000000`, 32 MiB) |
| Header title | `SHAMUSADV` |
| Game code | `BBAE` (USA: `AGB-BBAE-USA`) |
| Maker | `52` |
| Version | `0x00` (Rev. 00) |
| Fixed `0x96` | present at `0xB2` |
| Complement byte | `0x34` at `0xBD` |
| Header checksum | `0x0000` at `0xBE` (benign — complement byte is non-zero) |
| Entry branch | `0xEA00002E` → stock crt0 at `0x080000C0` (unpatched) |
| MD5 | `de6656c00fbeff59e77209d0bdf03063` |
| SHA-1 | `0bca9c4dd35d02c52a5db98b2097a50ef159de32` |
| SHA-256 | `c35e3e7eb2db8101e01d5c89434fdf0dbbbced4363fbb83f757fe3c5497ec6eb` |

**Embedded-header scan (Phase 0):** the full 156-byte Nintendo logo occurs exactly **once**, at file `0x0`. There is no second GBA header, no multi-game image, no appended trainer, and no scene cracktro. The image is the retail USA revision. Save type is **512-byte EEPROM** (mGBA produced a 512-byte `game.sav`).

## 2. Executive summary

**No in-game password, cheat-code, button-code, or code-entry system exists in this GBA SKU.** This is a bounded, evidenced negative — not "not tested":

1. There is no code-entry surface. Every reachable screen was walked in mGBA with RAM/savestate evidence (§3, §7). The only menu tree is: title → PLAY (3 save slots) / OPTIONS (2 toggles) / CONTROLS (2 configurations) / CREDITS / ART GALLERY. In-game START shows a transient level timer; no pause menu, level select, or code prompt was reachable.
2. A full string inventory (GNU `strings` over all 32 MiB, plus Ghidra's defined-string inventory) contains **zero** occurrences of `password`, `passcode`, `cheat`, `unlock`, `enter code`, or any literal code string in any encoding. The only "code"-like hits are the C++ RTTI names `N10SecretCode6PuzzleE` and libstdc++ `codecvt` symbols. `SecretCode::Puzzle` is one of **185** gameplay object classes (siblings: `GearPuzzle::Puzzle`, `MicPuzzle`, `TreasureChestPuzzle`) — the in-game "align the blocks" puzzle described by the dialogue at `0x09BBD830`/`0x09BBCA6C`, not a cheat validator.
3. The game's visible UI labels are **font/tile-indexed**, not ASCII (`strings` finds no `PLAY`, `OPTIONS`, `NEW GAME`, etc.). They were decoded by rendering/screenshot and by tracing the font system (error string at `0x09BBC574`, font routine literal at `0x0807645C`). No decoded label is a password/code entry. The ASCII text bank at `0x09BB0000–0x09BC0000` (1,781 strings) is dialogue, credits, and a small set of HUD/unlock strings (`CHALLENGE MODE`, `AVAILABLE`, `LEVEL`, `TABLETS`, `NEEDED`); none is a prompt to enter a code.
4. Twelve common GBA debug button combinations were pressed on the title screen with a restored baseline savestate each time; none opened a hidden screen (§6b).
5. The only developer-intended unlockables are **progress-gated**: the ART GALLERY photos (all "NOT AVAILABLE" on a fresh save) and a `CHALLENGE MODE` availability flag. These are save-bit unlocks driven by play (treasure chests / tablets), not codes. Per guide §16.18 they are reported as unlockables, not cheats.

**Verified published codes:** none exist for this GBA SKU. VGChartz lists "Total cheats available: 0"; GameFAQs has no cheats page content for GBA ID 929545; Video Games Museum's GBA cheats page is empty. The many Action Replay MAX / CodeBreaker results found by web search are for the **PS2** version (`B4336FA9…`, `F0487C36…` etc.) — cheat-device codes for another platform, out of scope and not present in this ROM.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`), `SDL_AUDIODRIVER=dummy`, display `:316`, `Xvfb :316 -screen 0 1024x768x24`, `openbox`, `mgba -3 game.gba`.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Menu navigation required ~90 ms holds with ~350 ms gaps; shorter taps were dropped.
- Boot path: legal screen → title menu. Menu path walked (each with a saved `.ss1` and screenshot, see §7):
  1. `PLAY` → 3 save slots (`NEW GAME` ×3, `NO SAVE`, `CANCEL`) → selecting slot 1 twice starts the game.
  2. `OPTIONS` → `SOUND ON`, `MUSIC ON` (2 toggles).
  3. `CONTROLS` → `CONFIGURATION A` ↔ `CONFIGURATION B` (2 pages, arrow navigation; wraps).
  4. `CREDITS` → scrolling value credits.
  5. `ART GALLERY` → vertically scrolling list, every entry reads `NOT AVAILABLE`; A on a locked entry displays the default Shamu image with no prompt.
  6. In-game:START → transient `00:00:17` level timer, then normal play. No pause menu appeared.
- RAM observation method: mGBA savestates are PNGs with a zlib `gbAs` chunk; decompressing yields a 397,312-byte state with **IWRAM at `0x19000`** and **EWRAM at `0x21000`** (guide §16.13). Each screen above has a corresponding `.ss1` in `/tmp/opencode/shamu/`.
- GDB stub note: `mgba -g` halts at PC=0 until `continue` is sent by a GDB client; the free-running menu walk used states instead. No validator was found to call as an oracle (§16.19) because no validator exists.

## 4. Address map

| Item | ROM / file address | Notes |
|---|---|---|
| Header | `0x08000000` (`0x0`) | stock, single image |
| ASCII dialogue/credits bank | `0x09BB0000–0x09BC0000` | 1,781 strings; story text, credits, HUD fragments |
| Font error string | `0x09BBC574` | "Invalid character, check your aFontInfo error character index…" |
| Font routine literal xref | `0x0807645C` (file `0x7645C`) | pointer to the font error string |
| `CHALLENGE MODE` string | `0x09BBC534` | xref at `0x08031768` (literal pool) |
| `AVAILABLE` string | `0x09BBC544` | xref at `0x0803176C` |
| `LEVEL` / `TABLETS` / `NEEDED` strings | `0x09BBC514` / `0x09BBC52C` / `0x09BBC524` | HUD/unlock text, pool at `0x0803175C` |
| RTTI region | `0x09BBF000–0x09BC5000` | 185 class names (Itanium ABI) |
| `SecretCode::Puzzle` name | `0x09BC0B70` | typeinfo `0x09BC0B48`; primary vtable address point `0x09BC0B20` with 5 code refs |
| `PauseScreen` name | `0x09BC30F8` | typeinfo `0x09BC30D0`; vtable `0x09BC30A4` with 5 code refs |
| `Menu` name | `0x09BC017C` | typeinfo `0x09BC0154`; vtable `0x09BC012C` with 5 code refs |
| `CDebug`/`ADebug`/`CCConsole` names | `0x09BBF71C` / `0x09BBF724` / `0x09BBF7A8` | debug-support classes compiled in; vtable refs exist (see §8) |
| Screen dispatcher | `FUN_08032300` (entry `0x08032300`) | `switch(param_2)` over scene IDs; case `0xE` calls `FUN_08030b5c`; case `0x85` loops 52 entries (gallery-sized) |
| `CHALLENGE MODE` screen builder | `FUN_08030b5c` (contains `0x080312AC`) | constructs ~52 text widgets; called only from `0x08032300` case `0xE` |
| Save RAM | EEPROM 512 B | progress bits (photos/tablets/challenge flag) |

## 5. Algorithm

Not applicable — there is no validator, checksum, password alphabet, key table, or button matcher in this SKU. The "algorithm" is ordinary progress gating: play levels, collect Atlantis tablets and treasure chests, and unlock flags in the 512-byte EEPROM. The only reverse-engineered logic is the scene dispatcher (`FUN_08032300`) and the unlock/notice screen builder (`FUN_08030b5c`), neither of which reads a user-entered code.

## 6. Tables

**Menu tree (complete, from §3 walk):**

| Screen | Entries | Encoded text form |
|---|---|---|
| Title | PLAY, OPTIONS, CONTROLS, CREDITS, ART GALLERY (5) | font/tile-indexed |
| PLAY submenu | 3 save slots + CANCEL + "NO SAVE" slot label | font/tile-indexed |
| OPTIONS | SOUND ON/OFF, MUSIC ON/OFF (2) | font/tile-indexed |
| CONTROLS | CONFIGURATION A, CONFIGURATION B (2 pages) | font/tile-indexed |
| CREDITS | scrolling names | ASCII bank `0x09BBC100–` |
| ART GALLERY | scrolling list of `NOT AVAILABLE` entries | font/tile-indexed |
| In-game | HUD + transient timer on START | tile graphics |

**Class inventory (complete RTTI name set, 185 names):** assembled from `0x09BBF000–0x09BC5000`. Relevant groups: puzzles (`SecretCode::Puzzle`, `GearPuzzle::Puzzle`, `MicPuzzle`, `TreasureChestPuzzle`, `Puzzle`), UI (`Menu`, `PauseScreen`, `HUD`, `Minimap`, `Objectives`), debug support (`CDebug`, `ADebug`, `Debug`, `CConsole`, `CSystemWarning`, …), and ~150 level entities. **No** `Password`, `Cheat`, `Code`, `CodeEntry`, `Unlock`, or `LevelSelect` class exists.

**ASCII text-bank hits classified (18 keyword hits from `strings`):** 3 `menu_tablet1/2` pairs (resource names), 15 story/narration strings (dialogue), 1 RTTI `N10SecretCode6PuzzleE`, 1 `6CDebug`, 1 `5Debug`, 1 `6ADebug`, 1 `4Menu`, 5 libstdc++ `codecvt`/`St…` names. Zero code/password hits.

## 6b. Enumeration

This section states the searched spaces and their counts, so the negative is a statement about those spaces (guide §0.2 point 5).

**A. Code/password space — EMPTY.**
- Alphabet/length/table/checksum/validator: **none exist**. There is no input alphabet, no literal code table, no comparison routine, no flag word written by a code, and no code-entry screen. Therefore the representable code set has **cardinality 0**.
- Static counts: 131,000 ASCII strings (`strings -n 4`) + Ghidra's complete defined-string inventory searched for `password|passcode|cheat|secret|unlock|debug|challenge|code` → 11 hits total; all are (a) the RTTI `SecretCode::Puzzle`, (b) C++ `codecvt` symbols, (c) the narrative string containing "secret of the Atlantis Tablets", (d) `CHALLENGE MODE`/`challenge` graphics assets. **0 code literals.**
- Literal-test counts: `PLAY`, `OPTIONS`, `CONTROLS`, `ART GALLERY`, `NEW GAME`, `NOT AVAILABLE`, `CONFIGURATION` have **0** ASCII occurrences; simple index/UTF-16 encodings of `PLAY` etc. also **0** (the UI is font/tile-indexed and was decoded from rendered screens instead).
- Button-code space: **0 tables**. The ROM contains **0** occurrences of the literal `0x04000130` (KEYINPUT) and **0** ARM `cmp`/`tst` immediates equal to standard key masks (`0x300` L+R, `0x00C` Select+Start, `0x003` A+B, …) in code. Twelve (12) combos were pressed at the title with baseline restore: `L+R+Start`, `L+R+Select`, `Select+Start`, `A+B+Select+Start`, `L+R+A+B`, `L+R+A`, `L+R+B`, `D-pad+A+B`, `R+A+B`, `L+A+B`, `Start+A`, `Start+B` → **0 hidden screens** (all non-navigating combos differed from baseline by only ~2,295 anti-aliasing pixels; combos containing A merely navigated the menu).
- Published-code space: **0 GBA codes** across VGChartz, GameFAQs, Video Games Museum, and TCRF; the PS2 cheat-device codes found are for a different platform and are not in the ROM.

**B. Unlockable space — progress-gated, enumerated.**
- ART GALLERY: the scene-dispatch case `0x85` loops **52** times (`local_64 < 0x34`) building gallery widgets; the on-screen list scrolls to a bottom stop with the scrollbar at maximum. On the analysed fresh save **all sampled entries read `NOT AVAILABLE`** (screens `gallery2`, `gal_down1..8`, `gal_end10..40`). A on a locked entry shows the default image only — no code prompt.
- `CHALLENGE MODE`: strings at `0x09BBC534`/`0x09BBC544` form an availability notice, built by `FUN_08030b5c` (called only from dispatcher case `0xE`). It is an unlock/notice flag in progress state, not a code gate.
- Unlock setter surface: per §16.18, these are bits in the 512-byte EEPROM written by play progress (tablets/chests). No setter is reachable from any controller code that resembles a code entry; this is ordinary progression.

**C. Novel code minting — NOT APPLICABLE.**
Because the code space is empty (A), no code can be minted, and none can be accepted/rejected in-game. Per the guide's "negative results bounded" clause (§0.2 point 5), the deliverable here is the counted negative above rather than a generated code. **No code is claimed.**

**D. Bounds proven by rejection:** there is no format to express an out-of-range field or bad checksum. The closest bounded rejection tests are: (i) all 12 button combos rejected by the title screen (no hidden screen), and (ii) A on every sampled locked gallery entry rejected with `NOT AVAILABLE` retained (no unlock). These prove the absence of the two plausible cheat surfaces.

## 7. Validation evidence

Labels follow the guide (Observed / Derived / Inferred).

- **Observed** — ROM header, hashes, single logo hit, 32 MiB size, 512-byte save (filesystem + `xxd`).
- **Observed** — six title-menu screens and their submenus, captured with screenshots and saved states: `menu_main.ss1`, `play_submenu.ss1`, `options2.ss1`, `controls_screen2.ss1` + `config_1_c.png`/`config_2_c.png`, `credits_screen2.ss1`, `gallery2.ss1`, `gal_end40_c.png`; in-game `ingame_base.ss1`, `pause_screen.ss1`, `pz1_c.png`. EWRAM/IWRAM layout of states verified at `0x21000`/`0x19000`.
- **Observed** — 12 title combos produced no hidden screen (`combo_*_c.png` compared with `compare -metric AE` against `menu_main_c.png`).
- **Observed** — README of web sources: VGChartz "0 cheats"; GameFAQs GBA 929545 has no cheats; VGM GBA cheats page empty. Fetched pages were treated as data; no prompt-injection payload was encountered.
- **Derived** — RTTI class inventory (185 names) and vtable/xref counts from `objdump` + Ghidra; string inventory from `strings` + `rea.search_strings`; scene dispatcher and screen builder from Ghidra pseudocode (`FUN_08032300`, `FUN_08030b5c`).
- **Derived** — `SecretCode::Puzzle` identified as a level puzzle from its class siblings and the in-game dialogue ("Solve the puzzle by lining up the puzzle pieces correctly", `0x09BBCA6C`).
- **Inferred** — the `CHALLENGE MODE` notice is triggered by tablet/progress thresholds (HUD strings `LEVEL`, `TABLETS`, `NEEDED`, `AVAILABLE` co-located in the literal pool at `0x0803175C`); the exact threshold was not exercised in-game.
- **Inferred** — the `CDebug`/`ADebug`/`CCConsole` classes are engine-level debug support retained in the retail build; no retail input path to them was found, but this was not proven exhaustively across all 141 scene IDs (see §8).

## 8. Unknowns

- The retail game has ~141 scene IDs (`0x0`–`0x8D`) in `FUN_08032300`; screens reachable only after story completion (e.g. the actual `CHALLENGE MODE` gameplay screen, ending/100%-completion screens) were not reached on a fresh save. Their existence does not imply a code surface, but they were not walked.
- `CDebug` (12-entry vtable, five constructor refs), `ADebug` and `CCConsole` are compiled in. A button-combo gate into a debug menu was not found in the spaces searched (12 combos, key-literal/xref scan), but a scene-id-based or save-flag-based gate was not exhaustively disproven. This is a bounded partial unknown, not a claim that a debug menu exists.
- Pressing START during the opening tutorial displayed a transient `00:00:17` timer rather than a pause menu; a pause screen class exists, so the exact trigger/timing of the retail pause screen remains unconfirmed.
- The font→tile mapping for the stylised menu font was not reconstructed as a numeric table; font-indexed labels were decoded by rendering them (screenshots) and by locating the font subsystem (`0x09BBC574`, `0x0807645C`). This is sufficient to show no code-entry label exists on any walked screen.

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo` for Phase 0/1.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-arm/-M force-thumb` for literal pools, vtables and dispatch code.
- Custom Python scripts in `/tmp/opencode/shamu/`: `phase0.py` (header/logo scan), `rtti.py`/`rtti2.py`/`vtable.py`/`xrefs.py` (RTTI + vtable + pointer scans), `scan.py`/`keyscan.py`/`fontdecode.py` (string/encoding/key-mask scans), `emu.py`/`walk.py`/`combos.py` (input + screenshots), `ss.py`/`diff.py` (savestate `gbAs` zlib decode + IWRAM/EWRAM RAM diffs).
- Ghidra 12.1.4 via REA MCP (`open_binary`, `search_strings`, `procedure_pseudo_code`, `procedure_callers`) for the string inventory and scene dispatcher pseudocode.
- Web sources: VGChartz cheats page, GameFAQs GBA 929545, Video Games Museum GBA cheats page, web search archive results. Content treated strictly as data.

## 10. Legal note

No ROM image, extracted graphics, music, or game text assets are redistributed by this report. Only hashes, addresses, algorithms, counts, and the analyst's own scripts/screenshots are recorded.

## 11. Cleanup

All analyst processes were stopped by their own PIDs (never `pkill`): mGBA, Xvfb `:316`, and openbox were killed by the PIDs recorded in `/tmp/opencode/shamu/*.pid`. Generated `game.sav`/`game.ss*` and all screenshots/scripts were kept in `/tmp/opencode/shamu/` (a copy of the ROM was used for emulation); **no `.sav`/`.ss*` files were created in the ROM folder** — the report file is the only artifact written there.
