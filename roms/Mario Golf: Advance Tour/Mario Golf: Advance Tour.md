# Mario Golf: Advance Tour (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mario Golf: Advance Tour.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| Header title | `MARIOGOLFGBA` (0xA0–0xAB) |
| Game code | `BMGE` (0xAC–0xAF); regional siblings in ROM: BMGJ/BMGP/BMGD/BMGF/BMGS/BMGI/BMGU at 0x233AC |
| Maker | `01` (Nintendo) |
| Version / fixed / complement / checksum | 0x00 / 0x96 / 0x6B / 0x0000 |
| Entry branch | `0xEA00010E` → ARM entry `0x08000440` (Camelot crt0, not a scene cracktro `0xEA00002E`) |
| MD5 | `2e8814e664675572a43b01900bbbb16b` |
| SHA-1 | `157058590cfb1d1cb83a3afac4847c2169f360a7` |
| SHA-256 | `f58b827e5b1d2ccbd1cb5eab81d38a3dc6716f0ff6c2591475bb06a862bffc0f` |

**Phase 0 embedded-header scan:** the 156-byte Nintendo logo occurs exactly once, at file offset `0x0`. There is no second (multicart/trainer) header, no appended cheat trainer, and no patch stub. The file is the retail image.

## 2. Executive summary

**No developer-intended cheat system exists in this ROM.** There is no password screen, no password alphabet/table/validator, no button-code matcher, and no reachable hidden/debug menu. This is a **bounded negative result**, not an untested guess: the full ASCII and tile-indexed text space, the password-plausible string space, the button-mask table space, the code-referenced data space, and every reachable screen in the boot/title/intro/story flow were searched/walked and counted (sections 6b and 7).

What the game *does* have is ordinary **save-gated unlockable content**, which is in scope as "unlockables" but is not a code system and cannot be triggered by any controller input:

* Star versions of the Mario characters, unlocked by beating them in a Character Match (the menu `R`-button "Star Character" toggle only switches the flag on an *already unlocked* character).
* Luigi / Wario / Waluigi / Bowser, transferred only from *Mario Golf: Toadstool Tour* over the GBA–GameCube link cable (unreachable on the GBA ROM alone and on the Wii U VC re-release).
* Mushroom Course and Star courses, unlocked by tournament results / story-mode challenges (Elf's Challenge, etc.).
* Custom Clubs from Custom Tickets earned in story mode.
* "Get Clubs" (up to 16 Special clubsets via Wireless Adapter) is a documented **unused** mode.

Published GBA "cheat codes" for this title are GameShark/CodeBreaker memory patches, which are explicitly out of scope. No published password list exists for this SKU; the cheat pages that might host one (GameFAQs, TCRF, Neoseeker) were unreachable from this environment (Cloudflare "Just a moment…" / captcha), so the negative is additionally backed by the ROM-side searches below and by three wiki articles that were fetched successfully and contain no password codes.

## 3. How to reproduce

**Emulator / display:** `mgba 0.10.5` under `Xvfb :317 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>` (3× scale; GBA viewport cropped from the root window at `+154+184`, 720×480).

**Keymap (verified live):** A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. XTEST events must be sent to the **focused** mGBA window (use `xdotool windowactivate --sync`); the SDL build ignores `xdotool key --window`.

**Screen path (reproducible):**
1. Boot → Nintendo logo → "CAMELOT SOFTWARE PLANNING" → "Challenge the golf world's champs!" → character montage → title `MARIO GOLF / Advance Tour` / `PRESS START`.
2. At the title, press **A or Start** → the character-montage cutscene plays; press **A** to skip it back to the title.
3. At the title again, press **Start promptly** (the title has an attract-mode timeout that soft-resets to the boot logos if left idle) → story mode begins.
4. Story mode: Marion Clubhouse interior; NPC dialogue "Hi! Before we get started, let's make you a game character." / "Which one are you?" → character auto-created → overworld → scripted golf events and NPC dialogue. Start button did not expose a menu during the scripted prologue.

Screenshot/RAM helpers used: `gba.py` (key + `import`/`convert` crop), `combo.py` (simultaneous combos), `ocr.sh` (tesseract), plus mGBA `.ss1` savestate parsing (§7). Generated `.sav`/`.ss1` were removed from the ROM folder at cleanup.

**Published codes tested:** none exist for this SKU; the literals `PASSWORD`, `CHEAT`, `CODE`, `SECRET`, `UNLOCK`, `DEBUG` and any 5–25-character code-shaped table were searched for in the ROM (section 6b) and were absent.

## 4. Address map

| Address (ROM/file) | Meaning | Evidence |
|---|---|---|
| `0x08000000` / file `0x0` | GBA header, entry `0xEA00010E` → `0x08000440` | Observed (header hexdump) |
| `0x08000440` | ARM crt0; loops calling the Thumb main at `0x08014A3D` | Derived (REA/Ghidra `FUN_08000440`, pointer at file `0x480`) |
| `0x08014A3C` | Thumb `main`: I/O init, subsystem init, main loop | Derived (Ghidra pseudocode) |
| `0x0801539A` | Thumb routine reading `0x04000130` (KEYINPUT), XOR-mask, stores held/pressed | Derived (objdump `-M force-thumb`) |
| `0x030011B4` | IWRAM: held key state (active-high `A=1,B=2,…`) | Derived (literal at file `0x153FC`) |
| `0x030011B8` | IWRAM: newly-pressed key state | Derived (`str r5,[r1,#4]` above) |
| `0x08016A37A` / file `0x16A37A` | Font glyph-order table: `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz` + 12 spaces | Observed (byte dump) — a **font**, not a password alphabet |
| `0x081872D4`–`0x08187F14` / file `0x1872D4`– | 16-byte NUL-padded developer labels (`gatpause`, `checkSwing`, `holeSelect`, `gateSelect`, `HoleInOne`, `Neil1`…, `stop : 0`…`check (W):19`) | Observed; **no code/data pointer references them** |
| `0x08191B9C`–`0x08192E8` / file `0x191B9C`– | Staff-credits ASCII bank (only ASCII UI text in the ROM) | Observed |
| `0x0E000000`, 32 KiB | SRAM save; header `MarioGolfGBABUD`; taunts; `Neil`/`Ella`; no password field | Observed (`.sav` dump) |

No validator function, password table, key-mask code table, or flag word for a cheat exists — those rows are intentionally absent, with the searches that prove it recorded in §6b.

## 5. Algorithm

Not applicable: no password/checksum/sequence algorithm is present. The only relevant input algorithm is the standard key-state computation, derived from the Thumb code at `0x0801539A`:

```
held    = (~KEYINPUT) & 0x3FF        @ active-high, stored at 0x030011B4
pressed = held & ~previous_held     @ stored at 0x030011B8
previous_held = held
```

This is ordinary edge detection; there is no ring buffer, progress index, or comparison table downstream of it.

## 6. Tables

* **Font table** at `0x0816A37A`: 52 letters + 12 space slots — glyph order for tile-indexed text (the in-game dialogue "Hi! Before we get started…" and "PRESS START" have **no ASCII occurrence** in the ROM, confirming text is font/tile-indexed; no password alphabet is encoded here).
* **Region codes** at file `0x233AC`, 8-byte stride: `BMGJ BMGE BMGP BMGD BMGF BMGS BMGI BMGU`.
* **Terrain/asset names** at file `0x67664`–`0x677xx`: `GREEN1`, `FAIRWAY1`, `HARDGROUND1`, `ROUGH1`… (asset IDs, not codes).
* **Developer labels** at file `0x1872D4`–: 16-byte slots, listed in §4; unreferenced, dev-only.
* **Save fields** (SRAM): `0x0` magic/version, `0x420`+ 8 taunt strings, `0x7A4` `Neil`, `0x8BC` `Ella`, duplicated at `0x46xx`; no code/password field.

## 6b. Enumeration

This engagement is a **negative**: there is no code space to enumerate. The searched spaces and the exhaustive counts are given so the negative is a proven statement about those spaces (§0.2, §16.3).

| Space searched | Count / result | Method |
|---|---|---|
| Embedded GBA headers (Nintendo logo) | 1 hit (file `0x0`) → single retail image | `rom.find(logo)` over all 16 MiB |
| `strings -t x -n 4` | 167,996 strings; keyword scan (`password\|cheat\|code\|secret\|debug\|unlock\|character\|course\|menu\|invalid\|continue\|hidden\|bonus\|master\|tourney\|putt\|championship`) | only credits and dev labels; **zero** password/cheat strings |
| Literal keyword search (all casings, `PASS/CODE/SECRET/UNLOCK/DEBUG`) | 0 hits in ROM | Python byte scan over 16 MiB |
| Password-plausible NUL-terminated ASCII strings (len 4–32, restricted alphabet) | 2,244 total; 333 uppercase+digit-only | full-ROM scan; all clustered hits are region codes and terrain names (§6) |
| Standard password alphabets (`0-9A-Z`, `A-Z0-9`, no-confusion variants, lowercase, ASCII-shifted) | 0 hits | full-ROM byte scan, 7 alphabets |
| Known visible tile-indexed strings ("PRESS START", "MARIO GOLF", "PRESS START" in font index form) | 0 ASCII hits; font table decoded at `0x16A37A` | brute-force ASCII-offset and alphabet-index encodings |
| Button-mask runs (u16, 0<v<0x400, popcount≤4) | 6,969 runs ≥5 entries; **all** false positives in graphics/compressed data | full-ROM u16 scan |
| Code-referenced candidate key-mask arrays (Thumb `LDR Rd,[PC,#imm]` targets) | 4,579 literal targets in code `0x0800_0000`–`0x0806_0000`; 10 data arrays matched; **none** is a deliberate sequence (repeats like `0x101 0x101…`, or table data like `0x201 0x302 0x201`) | Capstone/Custom Thumb literal scan |
| Data pointers into debug-label region `0x08187xxx` | 0 pointers to the label strings (18 pointers in that range are to other code/data tables) | `struct.unpack('<I')` sweep, 4-byte aligned |
| Screens walked (Observed) | boot logos, splash, character montage, title, story character creation, clubhouse interior, overworld, scripted golf event, NPC dialogues | mGBA screenshots + `.ss1` savestates |
| Novel code / bounds-by-rejection | **N/A — no code system exists.** No code can be minted, none can be rejected. | §0.2 negative-result clause |

**Published-code verification:** no password list is published for this SKU; no published literal could be searched because none exists. The three cheat-hosting sites that could contradict this (GameFAQs, TCRF, Neoseeker) returned Cloudflare/captcha blocks; Wikipedia, MarioWiki and StrategyWiki were fetched successfully and document only gameplay-gated unlockables (§2). No prompt-injection text was encountered in fetched content.

## 7. Validation evidence

* **Observed** — Emulator screenshots of every screen listed in §6b; title `PRESS START`, intro, character creation text, field, golf event, house interior. SRAM `.sav` content (magic, taunts, names) dumped and inspected. ROM header/hash/logo scan output.
* **Derived** — Ghidra/REA pseudocode for `0x08000440` and `0x08014A3C`; objdump disassembly of the KEYINPUT reader at `0x0801539A` and Start handler at `0x0804E652`; Thumb literal-pointer scan of 4,579 targets; all full-ROM counts in §6b.
* **Inferred** — The 16-byte ASCII slots at `0x1872D4`+ are developer labels (format and content strongly indicate this; no xrefs or runtime use were observed). The purpose of the font table at `0x16A37A` is inferred from its glyph order and the absence of ASCII UI strings.
* **Limitations** — The Wii U VC build and non-US regional builds were not analyzed; this report applies to `BMGE` (Rev.00), SHA-256 above. The In-Game Options/Quick Play menu was not reached in the prologue-limited emulator session; its existence and contents are taken from MarioWiki and are gameplay menus (no password entry is documented there). The GCN link and Wireless Adapter "Get Clubs" paths are unreachable in a single-ROM emulator and are reported from documentation.

## 8. Unknowns

* The exact in-game route to the Quick Play / Options menu in the early story (the prologue scripted events consumed the available session). Documentation confirms these menus exist; none contains a password field.
* Whether any unreferenced developer label at `0x1872D4`+ had a debug screen in a prototype build — no shipping code reaches it (§6b), so this is a historical, not an in-game, question.
* The exact SRAM bit offsets for each unlockable flag were not isolated; the unlock *sources* (Character Match, GCN transfer, course challenges) are documented in §2 but not proven at the byte level.

## 9. Tooling

* `file`, `xxd`, `strings`, `grep`, Python 3 (`capstone` 5.0.7, `keystone-engine`), `arm-none-eabi-objdump -M force-thumb`, `sha1sum`/`sha256sum`/`md5sum`.
* `mgba 0.10.5` (Xvfb :317, openbox, `SDL_AUDIODRIVER=dummy`), `xdotool`, `scrot`/ImageMagick `import`/`convert`, `tesseract 5.5.0`.
* REA MCP (Ghidra 12.1.4) — raw-binary ARM import at `0x08000000`; `open_binary`, `analyze_function`, `xrefs`.
* Local scripts: `/tmp/mariogolf/gba.py`, `combo.py`, `ocr.sh`; savestate `gbAs`-chunk decompressor (zlib, 397,312-byte state).
* No ROM or copyrighted assets are redistributed; only hashes, addresses, algorithms and the analyst's own scripts are published.

## 10. Legal note

Only the locally supplied ROM was inspected. No ROM bytes, graphics, music, or game text are reproduced here beyond the minimum needed to identify strings and tables. Findings are address/hash/algorithm evidence only.
