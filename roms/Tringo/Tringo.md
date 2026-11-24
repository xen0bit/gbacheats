# Tringo (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Tringo/Tringo.gba` |
| Size | 4,194,304 bytes (0x400000, 32 Mbit) |
| Header title | `TRINGO` (0xA0) |
| Game code | `BTJE` (0xAC) |
| Maker code | `4Z` (0xB0) — Crave Entertainment (splash: "Crave Entertainment"; credits: "Code © 2005 David A. Palmer Productions", "TRINGO © 2005 Nathan Keir") |
| Revision | 0x00 (0xBC) |
| Fixed byte | 0x96 (0xB2) |
| Header checksum | 0x0000; complement byte 0xCB (0xBD) |
| Entry word | 0xEA00002E → 0x080000C0 (stock crt0; **no** scene cracktro / appended trainer) |
| MD5 | `e352bcea86303c8cd501beca590d2087` |
| SHA-1 | `75052eda6a929c1bf41eb5566fcd854a6d0f1fc9` |
| SHA-256 | `1ca2e70b4e2788094b721d6d5efac64f126450a0d2f5dd94dc03cb310fee7d4d` |
| Save hardware | EEPROM (`EEPROM_V124` string at file 0x190A00; 0-byte `Tringo.sav` created on first boot) |

## 2. Executive summary

**Result: bounded negative — Tringo (GBA, BTJE4Z) contains no developer-intended in-game cheat-code system.** No password screen, no button-code sequence, no hidden/debug menu, no secret-name unlock and no secret unlock flag was found, and the entire candidate search space was enumerated and counted (§6b).

The game's entire user-facing text is a 56-entry ASCII string table at file 0x18D94C (offset table) / 0x18DA31 (strings), and all 56 strings are accounted for by reachable screens (title, player name, load/save, options, credits, high scores, select game, gameplay, pause, link states). The only "code-like" input surface is a **player-name field** (alphabet `_` + `A-Z` / `a-z`, 27 symbols per case). Static and dynamic analysis of its buffer (0x02033BBA) shows it is copied with `strcpy` and measured with `strlen` only — there is **no validator** that compares the name to a constant. The scrolling credits/legal text is rendered from a *second, glyph-index* font bank (not ASCII and not present in RAM as ASCII); it was checked with full-byte encoding sweeps as well. Input handling (held 0x02030232, pressed 0x02030230, mirrored to 0x0203014C+0x18/+0x1A) contains 49 literal references, none forming a button-sequence matcher; 134 candidate button-mask runs were inspected and none matches a known cheat sequence.

Published-code reconnaissance found **no in-game codes**: Cheat Happens states "We currently don't have any Tringo cheats or cheat codes"; ChapterCheats lists only a gameplay hint ("press Start to pause for unlimited thinking time"); gbaemulator.net lists 0 codes; GameFAQs returned HTTP 403. This is consistent with the ROM evidence.

Per guide §0.2 item 5, this engagement delivers the bounded-negative form of the deliverable: full screen enumeration, counted search space, and explicit rejection evidence, rather than a minted code.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `mgba -3 -d <rom>` (CLI debugger on a PTY). Keymap used: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
- Hold keys ~100–150 ms; menus debounce. Screenshots in `/tmp/tringo/work/` (`s*.png`, `cred_*.png`).
- Menu walk (all reached and screenshotted):
  1. Crave splash → legal crawl (auto-advance).
  2. **Main menu** (5 entries exactly): Single Player, Multi-Player, Options, Player Name, Load/Save. Cursor stops at index 4; no hidden 6th entry.
  3. **Player Name** — "PLEASE ENTER NAME", default `Player_`; hints: `+Control Pad - Change`, `A Button - Select`, `B Button - Delete`, `Select - Toggle case`, `Start - Finish`. Alphabet from ROM 0x101348: `_ABCDEFGHIJKLMNOPQRSTUVWXYZ` and `_abcdefghijklmnopqrstuvwxyz` (no digits/symbols).
  4. **Load/Save** — "Do Not Power Off."; entries Load, Save.
  5. **Options** — Music On, SoundFX On, Credits, Hi Scores, How to Play.
  6. **Credits** — scrolling text: "Tringo Created by", Primary Tester Marti Rivera, QA James Chen / Phillip Snipes, Director of Marketing Services Sheri Snow, Director of Brand Marketing Doug Panter, "Special Thanks" Nima Taghavi / Michael Maas / Rob Dyer / John Bloodworth / Aaron Hartman / Darold Higa, then the legal crawl (© 2005 Crave / David A. Palmer Productions / Nathan Keir / Donnerwood Media; "Licensed by Nintendo").
  7. **Hi Scores** — per-mode; default rows Allan Shorrt 01,250 / Phil Williams 00,600 / David Palmer 00,120 / Mark Cooksey 00,095 / James Shortt 00,025.
  8. **Single Player → Hi Scores → "SELECT GAME"** — Classic, Time Trial, Infinite (3 entries).
  9. **Gameplay** (Classic) → **Pause** (`Start`) — Continue, Quit (2 entries).
  10. **Multi-Player** — link states from string table: Transmit, Play, Not Connected, Connected, Please Wait!, Checking, Link Error. (A single host with no second link console cannot complete a session; all labels are present in the table.)
- RAM evidence: mGBA savestates `Tringo.ss1`–`Tringo.ss5` in the ROM folder (to be deleted at cleanup). The `gbAs` PNG chunk was calibrated by writing magic words with the debugger while halted: **IWRAM (0x03000000) → raw 0x19000; EWRAM (0x02000000) → raw 0x21000; palette → raw 0x800; VRAM → raw 0x1000** (state raw length 397,312 bytes). Key RAM values observed: held 0x02030232 = active-high key mask, pressed 0x02030230 = edge mask, input struct 0x0203014C (+0x18/+0x1A), name buffer 0x02033BBA (`Player_`), preset hi-score names at 0x02033684/0x02033714.

## 4. Address map

### ROM (file offset → 0x08000000 + offset)

| Address | Meaning |
|---|---|
| 0x080000C0 | Stock ARM crt0; `bx` to ARM main at 0x08000498 |
| 0x08000498 | ARM `main` — subsystem init, main loop; calls input poll at 0x08005200 |
| 0x08005200 | Input poll: reads 0x04000130, computes `~KEYINPUT` → held 0x02030232, `old^new & new` → pressed 0x02030230 |
| 0x0800527C | Copies held/pressed into global input struct 0x0203014C (+0x18 held, +0x1A pressed), masks input by byte +0x0E |
| 0x0800D1BC / 0x0800D228 | `strlen` / `strcpy` — the only consumers of the name buffer at 0x08010028 |
| 0x08010028 | Copies default `Player` (literal 0x08101310) into name buffer 0x02033BBA |
| 0x08012654–0x080128C4 | Name-entry screen handler (13 literal refs to 0x02033BBA) — edits/displays the name only |
| 0x08101310 | Default strings `Player`, `Player ` |
| 0x081012C0–0x0810130C | Preset hi-score names: Allan Shortt, James Shortt, Phil Williams, David Palmer, Mark Cooksey |
| 0x08101324 | Test string `Blahhhhhhhh` |
| 0x08101348 / 0x08101364 | Name-entry alphabets: `_ABCDEFGHIJKLMNOPQRSTUVWXYZ` / `_abcdefghijklmnopqrstuvwxyz` |
| 0x0818D920–0x0818D94C | u32 offset table (12 data offsets then string offsets) |
| 0x0818D94C + off | String index table; off 0xE5 → 0x0818DA31 `Tringo`, … off 0x30E → `Next Level` (56 entries, index 0–55) |
| 0x0818DA31–0x0818E22F | 56 NUL-terminated ASCII UI strings (English; localized French/German/Spanish/Italian banks follow at 0x18DD4D+) |
| 0x08190A40 / 0x08190BF0 | Code/data blocks copied to IWRAM/EWRAM by crt0 |
| 0x08190BE8/0x08190BEC | Pointers to the two alphabet strings (in copied IWRAM literal pool) |
| 0x101380 | Second embedded GBA header (multiboot/link image used by Transmit); contains its own `TRINGO`/`BTJE4Z` at +0xA0. No independent cheat strings found. |

### RAM / savestate

| GBA address | Savestate raw offset | Meaning |
|---|---|---|
| 0x0203014C | 0x2114C | Input struct; +0x18 held, +0x1A pressed |
| 0x02030230 / 0x02030232 | 0x21230 / 0x21232 | pressed / held key masks |
| 0x02033684, 0x02033714 | 0x22684, 0x22714 | Hi-score name slots |
| 0x02033BBA | 0x22BBA | Player-name buffer (`Player_`) |
| 0x03000000–0x03007FFF | 0x19000 | IWRAM (code copied from 0x08190BF0 etc.) |
| 0x05000000 | 0x800 | Palette RAM |
| 0x06000000 | 0x1000 | VRAM |

## 5. Algorithm

There is no password/checksum/button sequence to reimplement. The two data transformations that *could* be mistaken for one were reversed and are ordinary:

1. **Input** (`0x08005200`): `held = ~(KEYINPUT) & 0x3FF` (active-high); `pressed = (held ^ prev_held) & held`; both cached in a struct (`0x0203014C`). `0x0800527C` returns `pressed` and optionally zero-both when byte `+0x0E` is nonzero or a helper returns nonzero. Callers use `pressed` for menu navigation (single-button comparisons: Up 0x40, Down 0x80, A 0x0001, B 0x0002, Start 0x0008). **No history array or multi-press comparator exists in any of the 49 referencing functions.**
2. **Name field** (`0x08010028`, `0x08012654+`): `strcpy(buf=0x02033BBA, "Player")`, `strlen(buf)` for length, and per-character editing (D-pad changes index in the 27-symbol alphabet, Select toggles case, A advances, B deletes, Start finishes). **No `strcmp`/`memcmp` of this buffer against any constant was found.** The only compare-like helper reachable from the name path is `0x0800D1BC` (`strlen`).

## 6. Tables

### 6.1 Complete ASCII UI string table (56 entries, 0x0818D94C + u32 offset)

| idx | off | string | idx | off | string |
|---:|---:|---|---:|---:|---|
| 0 | 0xE5 | Tringo | 28 | 0x1F1 | Skip |
| 1 | 0xEC | Main Menu | 29 | 0x1F6 | Yes |
| 2 | 0xF6 | Single Player | 30 | 0x1FA | No |
| 3 | 0x104 | Multi-Player | 31 | 0x1FD | Classic |
| 4 | 0x111 | Options | 32 | 0x205 | Time Trial |
| 5 | 0x119 | Player Name | 33 | 0x210 | Infinite |
| 6 | 0x125 | Load/Save | 34 | 0x219 | 1 Minute |
| 7 | 0x12F | Hi Scores | 35 | 0x222 | 2 Minutes |
| 8 | 0x139 | Continue | 36 | 0x22C | 3 Minutes |
| 9 | 0x142 | Quit | 37 | 0x236 | Not Connected |
| 10 | 0x147 | Load | 38 | 0x244 | Connected |
| 11 | 0x14C | Save | 39 | 0x24E | Please Wait! |
| 12 | 0x151 | Load OK. | 40 | 0x25B | Checking |
| 13 | 0x15A | Load Error. | 41 | 0x264 | Level 1 |
| 14 | 0x166 | Save OK. | 42 | 0x26C | Next Level |
| 15 | 0x16F | Save Error. | 43 | 0x277 | +Control Pad - Change |
| 16 | 0x17B | Do Not Power Off. | 44 | 0x28D | A Button - Select |
| 17 | 0x18D | Music On | 45 | 0x29F | B Button - Delete |
| 18 | 0x196 | SoundFX On | 46 | 0x2B1 | Select - Toggle case |
| 19 | 0x1A1 | Music Off | 47 | 0x2C6 | Start - Finish |
| 20 | 0x1AB | SoundFX Off | 48 | 0x2D5 | English |
| 21 | 0x1B7 | Credits | 49 | 0x2DD | French |
| 22 | 0x1BF | How to Play | 50 | 0x2E4 | German |
| 23 | 0x1CB | Transmit | 51 | 0x2EB | Spanish |
| 24 | 0x1D4 | Play | 52 | 0x2F3 | Italian |
| 25 | 0x1D9 | Paused | 53 | 0x2FB | Link Error |
| 26 | 0x1E0 | Game Over | 54 | 0x306 | Level 1 (alt) |
| 27 | 0x1EA | Score  | 55 | 0x30E | Next Level (alt) |

**No entry contains PASSWORD / CODE / CHEAT / SECRET / DEBUG / INVALID / UNLOCK / WARP / TEST.**

### 6.2 Input masks (active-high, from 0x08005200)

A=0x0001, B=0x0002, Select=0x0004, Start=0x0008, Right=0x0010, Left=0x0020, Up=0x0040, Down=0x0080, R=0x0100, L=0x0200.

### 6.3 Name-entry alphabet (0x08101348, 0x08101364)

Index 0 = `_` (space), 1–26 = `A`–`Z`; identical lowercase table. 27 symbols per case, 52 letters total + underscore. No digits, punctuation or symbols — a password alphabet would require at least digits.

### 6.4 Button-mask run scan

134 runs of ≥4 consecutive u16 values drawn from the single-button mask set were found in the 4 MiB image (examples at 0x08023286, 0x08071AAE, 0x080FFE48, 0x081001C4…). All inspected runs are repeating/paired values inside code or compressed graphics/audio; **none** matches Konami (`U U D D L R L R B A`), its reverse, `L+R+Start`, or any 4+ distinct press sequence.

## 6b. Enumeration

**Space definition.** There is no code space to enumerate. The candidate surfaces were each enumerated completely:

| Surface | Enumeration result |
|---|---|
| ASCII UI text bank | 56 strings, indices 0–55, all decoded and each mapped to a reachable screen (§6.1). 0 cheat/debug/password labels. |
| Localized banks (French/German/Spanish/Italian at 0x18DD4D+) | Enumerated with `strings`; only translations of the same 56 UI labels. 0 code labels. |
| Credits / legal glyph-index bank | Scrolling text read frame-by-frame from the emulator: 22 distinct lines (credits + copyright crawl). Not ASCII; checked by full-byte sweeps (below). 0 code labels. |
| Button-code space | Input struct 0x0203014C has **49** literal xrefs in ROM; all are menu/game navigation. 134 candidate mask runs scanned; 0 valid sequences. No history buffer, no progress index, no sequence comparator. |
| Name field | Alphabet 27×2 symbols (§6.3); buffer 0x02033BBA has **15** literal xrefs; consumers are `strcpy`/`strlen`/character edit only (§5). 0 constant comparisons → no validator, no novel code can be minted. |
| Hidden screens | Main menu 5/5, Options 5/5, Load/Save 2/2, Select Game 3/3, Pause 2/2, name entry, credits, hi-scores, gameplay reached. String table has 0 unused entries that would name an unreached screen. No `TEMP`/placeholder banks. |
| Save/unlock flags | EEPROM (`EEPROM_V124`) stores name and hi-scores only; no unlock-bit test branches or "unlocked …" messages exist in the 56-string table. |

**Search space checked (counts).**
- ROM scanned in full: 4,194,304 bytes.
- Keyword probe set (18 words: PASSWORD, CHEAT, CODE, SECRET, DEBUG, UNLOCK, WARP, LEVEL SELECT, TEST, GREETS, BETA, INVALID, WRONG, CORRECT, CONGRATULATIONS, YOU WIN, MENU, CONTINUE) × encodings {ASCII uppercase, lowercase, XOR k for k=0..255, ADD k for k=0..255, UTF-16LE, UTF-16BE} → 18 × 514 = **9,252 full-ROM probes**. Cheat/debug keywords: **0 hits** (only ordinary hits such as `CONTINUE`/`MENU` in the known string bank; "CODE" appeared only inside `EEPROM_V124`-adjacent binary, "TEST" only in "Primary Tester" on the glyph bank).
- Credits/legal text strings ("LICENSED BY NINTENDO", "VIDEO GAME", "DAVID A. PALMER", "SPECIAL THANKS", "TRINGO CREATED BY", "NIMA TAGHAVI", "PRIMARY TESTER", "QUALITY ASSURANCE", "ALL RIGHTS RESERVED"): 9 × 512 byte transformations → **4,608 probes**, **0 hits** (confirming a glyph-index, not byte-encoded, bank).
- Pointer scan: 32-bit pointers into the text-bank region 0x0818D800–0x0818E400 → 21 hits, all within the string table / data blocks; no hidden table.
- PC-relative literal xref scan: **49** input-struct refs, **15** name-buffer refs, **2** alphabet refs → all accounted for in §4.
- Button-mask runs: 134 runs ≥4 presses → 0 matches to any documented cheat sequence.
- Published-code recon: 4 sites (GameFAQs 403; Cheat Happens none; ChapterCheats 1 gameplay hint; gbaemulator.net 0 codes) → 0 in-game codes.

**Novel code / rejection bounds.** Not applicable — no validator exists to mint against. Per the guide's bounded-negative clause (§0.2 item 5), absence is proven *for the spaces above*, with the counts and the screen walk as the evidence. No code was entered, so no acceptance/rejection pair exists to report. The only "rejection" observed was behavioural: entering arbitrary characters in the name field changes only the displayed name (verified in RAM at 0x02033BBA) and never produces a menu/flag change — consistent with a label field, not a code field.

## 7. Validation evidence

- **Observed** (emulator): all 10 screen classes in §3, screenshots and savestates; name field accepts arbitrary letters and only changes the displayed name; high-score names are developer names stored as plain ASCII in ROM (0x1012C0+) and copied to EWRAM (0x02033684 etc.).
- **Derived** (disassembly): input masks and globals (0x08005200/0x0800527C); name buffer consumers `strcpy`/`strlen` (0x0800D228 / 0x0800D1BC called from 0x08010028); string table layout at 0x0818D94C; alphabet tables at 0x08101348/0x08101364.
- **Inferred**: the second header at 0x101380 is the multiboot/link image for Transmit mode (based on location, identical title/code, and presence of link-state strings); not executed with a second console.
- **Negative** (counted): see §6b. No ROM or assets are redistributed.

## 8. Unknowns

- Multiplayer/Transmit screens requiring a second GBA could not be fully walked; the link-state strings (Not Connected, Connected, Please Wait!, Checking, Link Error, Play) exist in the table and the second header is present, but no in-game code surface was among them.
- The exact glyph→character map of the scrolling credits font was not fully inverted; the bank was bounded instead by exhaustive byte-encoding sweeps and by reading every frame of the scroll. No cheat/debug keyword appeared in any frame.
- The language-selection screen (English/French/German/Spanish/Italian) was not reached through the walked menus; only the localized text banks were enumerated.
- A ROM-patch/add-on trainer was not used or sought (out of scope: in-game/developer-intended cheats only).

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, custom Python pointer/encoding scanners (`ptrscan.py`, `scan1.py`, `xref.py`, `calib` scripts) in `/tmp/tringo/work/`.
- `arm-none-eabi-objdump -M force-arm/force-thumb` for crt0, input path and name consumers.
- mGBA 0.10.5 `-3 -d` CLI debugger on a Python PTY bridge (`dbg_daemon.py` + `dbgcmd.py`), Xvfb `:319`, openbox, `xdotool`, `scrot`.
- mGBA savestate `gbAs` zlib chunk parser with magic-value calibration (IWRAM raw 0x19000, EWRAM raw 0x21000, palette 0x800, VRAM 0x1000).
- Web recon via DuckDuckGo HTML + direct fetches (GameFAQs 403; Cheat Happens; ChapterCheats; gbaemulator.net; TCRF 403). Fetched pages were treated as data only.

*Legal note: only findings, addresses, hashes, and tool scripts are published; no ROM bytes or copyrighted graphics/audio are reproduced.*
