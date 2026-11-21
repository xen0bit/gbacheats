# WinX Club (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/WinX Club/WinX Club.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| Header title | `WINXCLUB` |
| Game code / maker | `BWIE` / `A4` (Konami) — `file(1)` reports "WINXCLUB (BWIEA4, Rev.00)" |
| Version / fixed / main unit / device | 0x00 / 0x96 / 0x00 / 0x00 |
| Complement / header checksum | 0x49 / 0x0000 (rebuilt-header artifact, cf. guide §16.1) |
| Entry word | 0xEA00003E (ARM branch); crt0 branch at +0xC0 = 0xEA00000E |
| MD5 | `80acbed66f2f7a2fc88357f9a2028458` |
| SHA-1 | `3b3f5c633f48ac218e9da6ac78305eab9c17ab21` |
| SHA-256 | `a3d9b2461d5408f354a511716fdd586514ffe4af713e8d4e3a39e123a5151c65` |
| External CRC32 | `1D6950A3` (GameHacking.org, AGB-BWIE-USA) |

All addresses below are **file offsets**; add `0x08000000` for the GBA bus address unless stated.

## 2. Executive summary

**All published "cheat codes" for this SKU are external cheat-device codes and are out of scope.** GameHacking.org, gbadamud.blogspot, 53lu and the GameFAQs guide publish only CodeBreaker/GameShark/AR codes (e.g. `977765EC3A92` enable-Must-Be-On, `9C3D984AF5FB` infinite health, `02033C50 00000030` raw RAM patches). No in-game button code, unlock code, or debug-menu activation sequence is published for the GBA version. A PC-version debug menu is discussed on Reddit but is a different SKU (guide §16.11).

The only developer-intended secret-code surface found in the GBA image is a **4-digit trophy-case / safe puzzle password**:

* `3921` — Cloud Tower miniature trophy case (from a note on Faragonda's bookshelf).
* `0001` — Red Fountain miniature trophy case (given by Brandon during the phone date).

Both values are published in walkthroughs (GameFAQs 40418 / 65152, supercheats Q&A). They are puzzle solutions rather than cheats, but are in scope here as *passwords* (brief §Scope).

**Static reconstruction**: the game is script-driven. Its script-function table at file `0xF1D81E` holds 707 x 0x20-byte records. Two records are the safe handlers: `#AlfeaA00_Safe01_Open` (index 285, bytecode at file `0xF3D562`, 0x10 bytes) and `#AlfeaA00_Safe02_Open` (index 286, bytecode at `0xF3D66A`, 4 bytes). The corresponding dialogue lives in `TxtPackage_All.bin` (file `0xD7F128`, size `0x61B58`) in five languages; there are exactly **two** "You have entered the correct code!" strings and **no** "wrong code" string.

**Bounded negative**: exhaustive literal search of all 16,777,216 bytes found **zero** occurrences of `3921` in ASCII, u16, u32, packed BCD, or any of the 24 permutations of its digit bytes (the sole code-region permutation hit, file `0x4155B`, is inside an `lsls` instruction stream — verified by disassembly). No literal validator constant for either code exists in the image in any obvious encoding, so the accept test is data-driven (script/asset) or item-gated. The password screen itself was not reached (see §8), so **no novel accepted code was minted** and no dynamic rejection test was possible. This report does not claim a solved validator; it bounds the search and states exactly what was and was not checked.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `mgba -3 -d game.gba`. Working copy at `/tmp/opencode/winxclub/game.gba` (ROM folder left untouched).
* Verified keymap: D-pad = arrow keys, A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`. `Shift+F1`..`Shift+F4` save savestate slots; `F1`..`F4` load. Hold keys 80–150 ms (guide §16.2).
* Boot path reproduced: ~20 s Konami/ac Studios intro → title (New Game / Load Game / Options) → New Game → slot 1 → Gardenia Park (2 hearts, 0/45 fireflies). Reached in-game menu with Select; cycled tabs with R.
* mGBA CLI debugger (`-d`) was used through a PTY bridge (`/tmp/opencode/winxclub/dbgserver.py`): commands `load 1..4`, `r/4 ADDR`, `w/4 ADDR VALUE`, `status`, `dis/t`. The GDB stub (`-g`, port 2345) was tried first but answered with packet errors and was abandoned (guide §16.13 fallback).
* Savestate RAM reads: `.ss1` files are PNG with a zlib `gbAs` chunk; decompressing yields a 397,312-byte state (EWRAM at raw `0x21000`, IWRAM at raw `0x19000`). Diffed `title.ss1` vs `gardenia.ss2` to locate state changes.
* Evidence artifacts (screenshots, savestates, extracted banks, scripts) are all in `/tmp/opencode/winxclub/`, **not** in the ROM folder.

## 4. Address map

| Item | File offset | ROM address | Notes |
|---|---:|---:|---|
| Header / crt0 | 0x000000 | 0x08000000 | entry 0xEA00003E |
| Resource manifest (pack index) | 0x55CDC | 0x0855CDC | `[name NUL-padded][u32 size][u32 file offset]` entries |
| — `txtpackage_all.bin` | 0xD7F128 (size 0x61B58) | 0x08D7F128 | 5-language text bank |
| — `scriptdata.bin` | 0xF015C8 (size 0x32850) | 0x08F015C8 | compressed prefix + script structures |
| — `bgmenuwarp` | 0xF85094 (size 0x3904) | 0x08F85094 | warp-menu background asset (debug relic?) |
| — `bgmenusave`, `bgmenupuzzle`, fonts, maps | 0xF7xxxx–0xF9xxxx | 0x08F7xxxx–0x08F9xxxx | menu/UI assets |
| `mapalfea.mmstr` | 0xD13844 (size 0x6B8E4) | 0x08D13844 | Alfea map/object/text data |
| **Script-function table** | **0xF1D81E** | **0x08F1D81E** | 707 records x 0x20 bytes |
| — `#AlfeaA00_Safe01_Open` | record index 285 @ 0xF1FBBE | 0x08F1FBBE | bytecode rel 0x1FD44 → file 0xF3D562, 0x10 bytes |
| — `#AlfeaA00_Safe02_Open` | record index 286 @ 0xF1FBDE | 0x08F1FBDE | bytecode rel 0x1FE4C → file 0xF3D66A, 4 bytes |
| — `#AlfeaA00_GoCloudTower` | index 287 | 0x08F1FBFE | rel 0x1FE94, 1 byte |
| Script function dispatch table | 0x3E86C | 0x0803E86C | u32 offsets into script space |
| Safe dialogue strings | 0xD881A4, 0xD882C8, 0xD88504 | 0x08D881A4 etc. | see §6 |
| EWRAM player state (from published raw patches) | 0x033C50 etc. | 0x02033C50 | HP / help-meter / fireflies; cross-checked as EWRAM |
| IWRAM game globals | — | 0x03003400–0x03004000 | resource pointers, script state (savestate diff) |

## 5. Algorithm

**Script-function record format (derived, verified on several records):**

```
struct ScriptFunc {          // 0x20 bytes
    char name[26];           // '#' + identifier, NUL-padded
    u32  bytecode_offset;    // relative to 0xF1D81E (file) / 0x08F1D81E (ROM)
    u16  bytecode_length;    // bytes
    u16  unused;
};
```

Example: record at 0xF1FBBE — name `#AlfeaA00_Safe01_Open`, offset `0x1FD44`, length `0x10`; resolved bytecode at 0xF3D562 = `02 00 14 00 04 00 18 00 FE FF 01 00 02 00 03 00`, read as u16 words `[0x0002, 0x0014, 0x0004, 0x0018, 0xFFFE, 0x0001, 0x0002, 0x0003]`. The prefix `02 XX 04 18 FF FE` recurs in chest/dialog scripts (e.g. `#GardenA00_OpenChest01` = `[2,0x2C,4,0x18,0xFFFE]`, `#AlfeaA02_Dialog_02` = `[2,0x14,4,0x18,0xFFFE,1,2]`), i.e. a "say line / set flag" opcode chain. **No digit or password constant appears in either safe script.**

**Resource manifest format (derived):** entries are `[ASCII name, NUL-padded to 4-byte boundary][u32 size][u32 file offset]`; successive offsets are contiguous, so each file's end is `offset+size`. This is how the text bank, script data, maps, fonts and menu backgrounds are stored.

**Password hypothesis status**: the only two accepted values known are literal walkthrough data; no decoder/encoder, checksum, permutation table, key schedule or digit-tile alphabet was located. The accept test could not be modelled to the §6.3 standard, so no offline validator reimplementation is claimed.

## 6. Tables

**Published in-game passwords (the only in-scope code-like secrets found):**

| Code | Unlocks | Source | Verified in ROM? |
|---|---|---|---|
| `3921` | Cloud Tower miniature in Alfea trophy case → portal to Cloud Tower | GameFAQs 40418/65152, supercheats, Russian walkthroughs | ASCII/u16/u32/BCD/permutation search: **absent** as literal; dialogue present |
| `0001` | Red Fountain miniature in Alfea trophy case → portal to Red Fountain | GameFAQs 65152, PS2/GBA Q&A | absent as literal; `00 00 00 01` byte pattern is ubiquitous (13,793 hits) — no discriminating hit |

**Safe-related text bank entries (file offsets, five languages each):**

| Offset | English text |
|---:|---|
| 0xD881A4 | "It seems this safe requires a password to open it." |
| 0xD882C8 | "You have entered the correct code!" (Cloud Tower case) |
| 0xD88384 | "You found a miniature of Cloud Tower! Now where could this be used?" |
| 0xD88504 | "You have entered the correct code!" (Red Fountain case) |
| 0xD885BC | "You found a miniature of Red Fountain! Now where could this be used?" |
| 0xD80E44 | "- Obtain the code to the Trophy Case from Faragonda's bookshelf in her office." |
| 0xD92DB8 | "I think Faragonda keeps the code to the trophy case in a book in her office." |
| 0xDC7C3C | "You found the code to the trophy case of Cloud Tower's miniature!" |
| 0xDC8968 | "Plaque" (item name) |

**Out-of-scope published codes (recorded for completeness, deliberately not analysed):** GameShark/CB enable `977765EC3A92` / `19A95D487BDB` / `F8F32B0D6D0C`; infinite health `9C3D984AF5FB`; max health `AC3F9D6AE57E`; infinite magic `270AB5FDE416`; all items `E457E71D1069` / `241E98662D16`; all images `6F43CF1E1069` / `6456886EE504`; all spells `95219800B5C9` / `2B27D522B748` / `E56189202DC9`; all fireflies `2721B3B1A1C9`; raw patches `02033C50` (HP), `02033C51` (WinX bar), `02033C52` (helper), `02033C53` (hearts), `02033C56` (fireflies), `02047D28` (boss human mode).

**Menu enumeration (all reachable screens at game start):**

| Screen | Entries observed |
|---|---|
| Title | New Game, Load Game (3 save slots), Options |
| Options (title) | Sound, Music, Text Speed |
| In-game (Select) — exactly 4 tabs, cycled with R/L | Inventory, Magic, Objectives, Favours |

No 5th menu tab and no hidden Options entry appeared during exhaustive cycling (16 R presses with 0.8 s settles; screenshots `/tmp/opencode/winxclub/tabb1..8.png`, `montage_tabs2.png`).

## 6b. Enumeration

**Space definition (bounded by published evidence).** The in-game password surface is a **4-symbol decimal field**, digits `0`–`9`, giving `10^4 = 10,000` representable strings (`0000`–`9999`). Alphabet and field width are **inferred from the two published codes**, not from a decoded keypad UI (the screen was not reached — see §8). There is no evidence of a checksum, reserved bits, or a second longer format: the text bank has only two "correct code" outcomes, and both are followed by a miniature-item grant.

**Accepted set known from published lists:** exactly 2 values — `3921` and `0001`. Unverified PS2-era claims `3941` and `2008` were found in web Q&A snippets but are from a different SKU and were not observed in this ROM.

**Novel codes generated and confirmed in-game: NONE.** This is an honest limitation, not an omission: §0.2 requires a novel accepted code for a solved code system, but the validator was not isolated (see §8) and the entry screen was not reached. Generating an arbitrary 4-digit string and calling it a "novel code" without an accept/reject observation would be a false claim. No value outside the published pair was observed to be accepted or rejected.

**Bounds proven by rejection: NOT ACHIEVED dynamically.** The safe/password screen was never displayed, so no wrong-checksum, out-of-range, or reserved-field input could be submitted in-game. The report therefore does **not** claim the accepted set is *exactly* `{3921, 0001}` — it claims only that these are the two values published for this SKU.

**Static search bounds (what *was* counted, so the negative is bounded rather than vague):**

| Search | Space checked | Hits |
|---|---:|---:|
| `3921` as ASCII `"3921"` | 16,777,216 byte offsets | 0 |
| `3921` as u16 LE (`51 0F`) | 16,777,216 offsets | 3 (0x4D310, 0x793AC, 0x81BDC — all mid-instruction/data, none a literal pool) |
| `3921` as u32 LE (`51 0F 00 00`) | 16,777,216 offsets | 11 (compressed graphics/data, no xrefs) |
| `3921` as BCD (`39 21`) | 16,777,216 offsets | 87 (none in code 0x000000–0x0FFFFF, none in Alfea map 0xD13844–0xD7F128, none in script data 0xF015C8–0xF33E18) |
| All 24 byte-permutations of {3,9,2,1} | 16,777,216 offsets x 24 | 1 plausible-looking hit at 0x4155B — disassembled, lies in an `lsls rX, rY, #7/8/9` instruction stream (false positive) |
| `3921` as 4 u16 digits, forward or 0-based | whole ROM | 0 |
| Script-function records scanned for digit constants | 707 records (all bytecode) | 0 containing `3921` in any tested encoding |
| ASCII strings ≥5 chars scanned for password/debug keywords | 86,384 strings | safe messages and asset names only; no generator, table, or button sequence |
| Thumb `LDR [PC,#imm]` literal loads to 0x04000130 (KEYINPUT) | code 0x08000000–0x08150000 | 0 (input read is indirect) |
| Thumb literal loads of 0xF51 as a standalone word | code region | 0 |
| Distinct "correct code" / "wrong code" text strings | full text bank | 2 correct, 0 wrong |

**Debug-menu / button-code negative (bounded):** the only debug-like asset is `bgmenuwarp` (file `0xF85094`, 0x3904 bytes, manifest at `0x55F5C`) plus three ASCII code-region labels `BgMenuWarp` (`0x38C88`), `Level Initialisation` (`0x1BE70`) and `Invalid Operation` (`0x3D3D4`). All were checked for direct 32-bit pointers and for Thumb PC-relative literal loads across code 0x08000000–0x08100000: **zero word-pointers and zero LDR-literal references**. No published activation sequence exists, and the title/in-game screens enumerated above expose no hidden entry. This is a **gated-or-dead code** finding (guide §16.3 categories 2/4): the asset survives, but no reachable gate was identified. It is not proof that no gate exists — the only writer of the scene/menu-state word was not enumerated exhaustively.

## 7. Validation evidence

| Claim | Evidence type | Evidence |
|---|---|---|
| ROM identity/hashes | Observed | `file`, `md5sum`, `sha1sum`, `sha256sum`, header hexdump |
| Script table 707 records, record format | Derived | byte parse of 0xF1D81E–0xF2307E; offsets resolve to valid u16 script streams (e.g. `#GardenA00_LevelCreate` at 0xF233AA) |
| Safe scripts contain no password constant | Derived | disassembly/byte dump of 0xF3D562 (0x10 B) and 0xF3D66A (4 B) |
| Safe dialogue exists in 5 languages, 2 correct-code outcomes, 0 wrong-code | Derived | text bank scan of 0xD88100–0xD88600 |
| No literal `3921` anywhere | Derived | exhaustive byte searches + Capstone disassembly of the sole permutation hit |
| Title/in-game menu contents | Observed | screenshots `screen8.png`, `screen12.png`, `menu1.png`, `montage_tabs.png`, `montage_tabs2.png` |
| Gardenia Park boot state, 2 hearts, 0/45 fireflies | Observed | `screen13.png`, savestate `gardenia.ss2` |
| mGBA GDB stub unreliable; CLI debugger works | Observed | GDB packet errors; `dbg.py`/`dbgserver.py` `status`, `load 2`, `r/4` responses |
| `bgmenuwarp` asset has no direct code xrefs | Derived | word-pointer + LDR-literal scans (code 0x08000000–0x08100000) |
| Codes `3921`/`0001` correct | Inferred (external) | walkthroughs; **not** verified by entering them in the emulator |

## 8. Unknowns

1. **Validator location and model** — not found. The safe's accept routine may be a native keypad function called by a generic script opcode, or the GBA build may gate the case on an inventory item ("code"/"Plaque") rather than digit entry; the string "You have entered the correct code!" could be shared with the PS2 build. The GBA walkthrough phrase "Grab the password from the far left bookcase" favours the item interpretation, while the existence of two distinct correct-code lines favours digit entry. This ambiguity is unresolved and is the main blocker to §6b minting.
2. **Password screen not reached.** Reaching it requires progressing from Gardenia Park through the early game to Alfea's trophy room; navigation attempts reached the Park Attendant and shakable trees but did not obtain the Gate Key or advance the level, so no password-entry UI, RAM input buffer, or accept/reject behaviour was observed. All claims about the code space are therefore upper-bound/inferred.
3. **Exact input alphabet/terminator** — the 4-digit decimal alphabet is inferred from published codes only; no on-screen keypad glyph table was decoded.
4. **Whether a third accepted code exists** — not disproven dynamically; the exhaustive literal search makes a hard-coded third constant unlikely but cannot exclude a data-driven or algorithmic third value.
5. **Debug menu gate** — `bgmenuwarp` asset exists with no direct xrefs; the scene/menu-state writer was not exhaustively enumerated, so dead-code vs. gated-feature is not closed.
6. **Save format** — the 8 KiB EEPROM save had only a 32-byte two-block record after New Game (`00 00 00 0A F0 F0 F0 22 …`, `00 00 00 00 00 00 00 05 F0 F0 F0 27 …`); fields were not decoded, so save-based fast travel to Alfea was not attempted.

## 9. Tooling

* `file`, `xxd`, `strings -t x`, `md5sum`/`sha1sum`/`sha256sum`.
* `arm-none-eabi-objdump -M force-thumb` (literals and false-positive verification); Capstone Python binding for literal/BL/immediate scans.
* Python 3 scripts in `/tmp/opencode/winxclub/`: `key.py` (XTEST input), `dbg.py` / `dbgserver.py` (mGBA CLI-debugger PTY bridge), savestate `gbAs` zlib extractor, resource-manifest and script-record parsers.
* mGBA 0.10.5: `-3` display, `-d` CLI debugger, `-t` savestate load; Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `xdotool`, `scrot`, ImageMagick `montage`.
* Web recon: GameFAQs guides 40418 and 65152, GameHacking.org game 6448, gbadamud.blogspot, 53lu, supercheats (all treated as untrusted data; none was followed as instructions; no prompt-injection payload was encountered).

## 10. Cleanup

All analysis artifacts live in `/tmp/opencode/winxclub/`. The ROM folder `/mnt/gbacheats/roms/WinX Club/` was checked at the end and contains only `WinX Club.gba` — no `.sav`, `.ss1`–`.ss9`, or `.state` files were created there. Only this session's own PIDs were used: mGBA CLI-debugger instance (PID 826892) and Xvfb `:318` (PID 819666) were stopped by number; no `pkill`/`pkill -f` was used, and other agents' processes were left untouched.
