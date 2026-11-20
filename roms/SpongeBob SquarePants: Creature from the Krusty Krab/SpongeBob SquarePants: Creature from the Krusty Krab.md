# SpongeBob SquarePants: Creature from the Krusty Krab (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `SpongeBob SquarePants: Creature from the Krusty Krab.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `SPONGEBOBCKK` |
| Game code | `BQ4E78` (USA) |
| Maker | `78` (THQ) |
| Version | 0x00 (Rev.00) |
| Entry word | `EA00002E` → stock crt0 at 0x080000C0 (no scene-release cracktro) |
| Header checksum | 0x005E; complement byte 0x00 |
| MD5 | `45e6e3088c5c9006175aaf045e8795e8` |
| SHA-1 | `1ec8b5d234ecdc8fa61a5850a76d1d407dac3333` |
| SHA-256 | `d02a9c2e4032a717be4b29dc54f064bde7af3d5bb2e26c659ee7dbf0987c4203` |

Developer strings in ROM: `Developed by WayForward Technologies.` (legal screen, observed in emulator) and `WAYFORWARD` at file 0x24A38A. Audio engine: Shin'en GAX (`Code: B.Wodok` at 0x221ABE — an engine banner, **not** a cheat code).

## 2. Executive summary

**No in-game password / code-entry system exists in this GBA SKU.** Published "GBA" cheats (`SPONGE`, `PANTS`, `PATRICK`, `HOTROD`, `SPACE`, from SuperCheats) are copies of the GameCube/DS "Extras → Enter Codes" lists; none of them, nor any other code-like string, is present in the ROM under any of the ~20 encodings tested (§6b). Every reachable frontend screen was walked; there is no "Extras" door, no "Enter Codes" option, and no text bank containing those labels (§7).

**What does exist is a real developer debug menu**, statically recovered: scene id `2` builds a 15-entry "DEBUG MENU" (title at 0x080848EC, list at 0x0824A2F8), with four sibling submenus (CINEMA/CHAPTER/WORLD/MINI-GAME, 12/13/11/15 entries). Entries include `UNLOCK MINI-GAMES`, `ERASE SAVED GAMES`, `DEBUG AUDIO`. This is in-scope developer-intended hidden content, enumerated in §6 and §6b. A direct RAM patch of the scene-request byte to `2` (savestate offset 0x1B2F0 = IWRAM 0x030022F0) resets the game to the legal screen, so the retail reachability gate for that menu is **unproven** (§8).

**Conclusion:** bounded negative for passwords/button codes; positive static enumeration of a debug menu system. No novel code could be minted because no validator or accepted-code space exists in this image; the bound is proven by search counts and screen enumeration rather than by a generated code.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:317` + openbox, `mgba -3 <rom>`.
* Keymap (mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 120–200 ms.
* **Focus your own window by PID** (`xdotool search --pid <pid> | tail -1`); multiple mGBA windows from other sessions share the display and `search --name mGBA | head -1` can focus the wrong game.
* Boot path observed: health & safety → legal → THQ splash → **title** (`Press Start`) → **frontend** (two doors: `GAME SELECT` | `OPTIONS`).
* `GAME SELECT` → 3 lockers with `New Game`. `OPTIONS` → horizontal carousel: an arrow/robot page, `ARCADE` (notice board), `CINEMA` (movie-theatre screen), `CREDITS` door. No other entries were reachable with LEFT/RIGHT/UP/DOWN/A.
* Button-code probes at the frontend: `L+R` (and `L+R+Start`, `L+R+Select`) **soft-reset to the health warning** — a system reset, not a cheat. Konami-style sequence, `Start+Select`, `Up×3/Down×3`, `AABBA B`, `L/L/R/R`, `R/R/L/L`, `BBAAB A`, and others produced no state change.
* Static searches used: `strings -t x`, `grep -abo`, Python byte-transform search, Thumb BL/LDR-literal scanners, `arm-none-eabi-objdump -M force-thumb`, REA/Ghidra 12.1.4 raw ARM import at base 0x08000000.

## 4. Address map

| Address (ROM) | File offset | Meaning |
|---|---|---|
| 0x08000000 | 0x000000 | `b 0x080000C0`, stock crt0 |
| 0x080848EC | 0x0848EC | `"DEBUG MENU"` (NUL-terminated ASCII) |
| 0x080848F8 | 0x0848F8 | `"MINI-GAME MENU"` |
| 0x08084908 | 0x084908 | `"CINEMA MENU"` |
| 0x08084914 | 0x084914 | `"CHAPTER MENU"` |
| 0x08084924 | 0x084924 | `"WORLD MENU"` |
| 0x0808468C | 0x08468C | `"AUDIO DEBUG"` (+ mixer diagnostic strings through 0x084760) |
| 0x080323BC | 0x0323BC | Debug-menu scene dispatcher (Thumb, `push {r4,lr}`), called from 0x0800E3AC |
| 0x08078AE8 | 0x078AE8 | Menu-list setup routine used by the dispatcher (`r0`=title ptr, `r1`=list ptr, `r2`=count) |
| 0x0824A2F8 | 0x24A2F8 | 15×0x24 debug-scene records `{u16 id, char name[34]}` |
| 0x0824A538 | 0x24A538 | World-menu list (`WORLD 01-A` …) |
| 0x0824AA48 | 0x24AA48 | Cinema-menu list (`CINEMA 01` …) |
| 0x0824B0E4 | 0x24B0E4 | Mini-game-menu list (`PLATES` …) |
| 0x0824B228 | 0x24B228 | Chapter-menu list (`CHAPTER 01` …) |
| 0x080853D4 | 0x0853D4 | Font glyph→character table (see §6) |
| 0x030001BE | — | IWRAM: dispatcher's current debug-scene id byte |
| 0x030001C0 | — | IWRAM: pointer to active debug list |
| 0x030001C8 | — | IWRAM: pointer to active menu title |
| 0x030022F0 | — | IWRAM: frontend scene-request byte (0x39 = FRONTEND observed in savestate) |

Savestate layout (mGBA 0.10.5, 8 MiB image, `gbAs` zlib chunk decompresses to 397,312 bytes): header/CPU 0x00000, VRAM ~0x10000, IWRAM 0x19000–0x20FFF, EWRAM 0x21000. The scene byte is at raw offset **0x1B2F0**.

## 5. Algorithm / model

### 5.1 Debug-menu dispatcher (derived from disassembly, evidence: 0x080323BC)

```
debug_menu(id):                      # r0 = id
  [0x030001BE] = id                  # strb at 0x80323C0
  ... baseline setup (0x08014E94, 0x0801088C, 0x080002E0) ...
  switch id:
    0x02: list=[0x0824A2F8], title="DEBUG MENU"       (0x080848EC), count=15
    0x8D: list=[0x0824AA48], title="CINEMA MENU"      (0x08084908), count=12
    0x8E: list=[0x0824B0E4], title="MINI-GAME MENU"   (0x080848F8), count=15
    0x8F: list=[0x0824B228], title="CHAPTER MENU"     (0x08084914), count=13
    0x90: list=[0x0824A538], title="WORLD MENU"       (0x08084924), count=11
    else: no menu
  call 0x08078AE8(title, list, count)
```

The caller at 0x0800E374–0x0800E3B0 loads the byte at 0x030022F0 and passes it as `id`. `0x030001BD` holds the selected-item index; the sibling handler at 0x080324F0 processes menu selection.

### 5.2 Password validator

**None found.** There is no function that compares a user-entered character buffer against stored code constants: no code table exists in ROM (§6b), no "Enter Codes" UI text exists in any encoding (§7), and no accepted-code space can be defined. Therefore no encoder/decoder can be reimplemented and no novel code can be minted. This is a *bounded negative*, not an untested guess.

## 6. Tables

### 6.1 Font glyph→character table at 0x080853D4 (observed bytes)

| Glyph range | Characters |
|---|---|
| 0x00–0x0C | `A`–`M` |
| 0x10–0x1C | `N`–`Z` |
| 0x20–0x2C | `a`–`m` |
| 0x30–0x3C | `n`–`z` |
| 0x40–0x4D | `01234567890.,?` (note duplicated `0`) |
| 0x50–0x54 | `!-+:;` |

Rows are separated by three NUL bytes, and accented glyph pairs (`0xC0 0xE0`, etc.) follow at 0x0808542C. This table is referenced from 0x080382FC / 0x080383C4 (font/character-sheet rendering). It is **not** a code alphabet: encoding the published codes with it produced zero ROM hits.

### 6.2 Debug scene-name records at 0x0824A2F8 (15 entries, stride 0x24)

| # | Address | id | Name |
|---:|---|---|---|
| 1 | 0x0824A2F8 | 0x0F32 | HEALTH |
| 2 | 0x0824A31C | 0x0F2E | LEGAL |
| 3 | 0x0824A340 | 0x0F30 | THQ |
| 4 | 0x0824A364 | 0x0F2F | NICK |
| 5 | 0x0824A388 | 0x0F31 | WAYFORWARD |
| 6 | 0x0824A3AC | 0x0F3B | TITLE |
| 7 | 0x0824A3D0 | 0x0F39 | FRONTEND |
| 8 | 0x0824A3F4 | 0x0F28 | ARCADE |
| 9 | 0x0824A418 | 0x0F92 | ERASE SAVED GAMES |
| 10 | 0x0824A43C | 0x0F93 | UNLOCK MINI-GAMES |
| 11 | 0x0824A460 | 0x0F91 | DEBUG AUDIO |
| 12 | 0x0824A484 | 0x0F8D | CINEMA MENU |
| 13 | 0x0824A4A8 | 0x0F8E | CHAPTER MENU |
| 14 | 0x0824A4CC | 0x0F90 | MINI-GAME MENU |
| 15 | 0x0824A4F0 | 0x0F8F | WORLD MENU |

Record 16 at 0x0824A514 is a `0x00FF` terminator — the list is exactly 15 entries, matching the `count=15` constant in the dispatcher (Derived + cross-checked).

### 6.3 Published codes and ROM verification

| Code | Published effect (source) | ROM literal hits |
|---|---|---|
| SPONGE | Punk SpongeBob (SuperCheats GBA) | only in story text at 0x24B03C, 0x25D154… — not a code table |
| PANTS | SpongeBob Plankton (SuperCheats GBA) | lowercase `pants` in 7 language text blocks (stride 0x4340), not a code table |
| PATRICK | Patrick Tux (SuperCheats GBA) | only story text |
| HOTROD | new vehicle (SuperCheats GBA / GC / DS) | lowercase `hotrod` at 0xE417F is a credit string `"hotrod skydive" © Martin Schioele`; others story text |
| SPACE | new ship (GC/DS; GBA page lists it) | lowercase `space` at 0x26599A/0x2659E9, story text |
| GUDGEON, PORKPIE, GASSY, HOVER, PILOT, ROCFISH, BRAIN, LASER | GC/DS/PS2/Wii lists | **absent in every encoding tried** |

Verdict: none is a developer-intended GBA code in this image; the GBA SuperCheats list is inherited from the console version (guide §16.11).

## 6b. Enumeration

### 6b.1 Password/code space — bounded negative with counts

**Claim:** the representable code space is empty for this SKU (0 accepted codes; 0-byte input surface).

Evidence and counts:

1. **Screen space (Observed).** 11 distinct screens were reached and screenshotted: health warning, legal, THQ splash, title, frontend Game Select|Options, save-slot locker screen, options arrow page, ARCADE, CINEMA, CREDITS door, plus in-game title/press-start. No password keyboard, code field, "Extras", or "Activate Bonus Items" control exists on any of them. Reachable-input enumeration: LEFT/RIGHT/UP/DOWN/A/B/Start/Select were applied on every screen; the only hidden behaviour was L+R = soft reset.
2. **Text-bank space (Observed).** Whole-ROM case-insensitive `strings -n 3` for `password|cheat|code|secret|unlock|bonus|enter|extra` produced **5** keyword hits: `Patty Extra large` (food name), `AUDIO DEBUG`, `DEBUG MENU`, `UNLOCK MINI-GAMES`, `un extra` (French story text). There is **no** `ENTER CODES`, `EXTRAS`, `BONUS`, or `INVALID` label. Because the engine's other UI labels (`DEBUG MENU`, `CINEMA MENU`, …) are plain ASCII, a code-entry screen would have left an ASCII label; none does.
3. **Code-table space (Derived/Observed).** 13 published codes were probed with **~530 transformations each** (≈6,900 literal searches): raw ASCII upper/lower/title-case, reversed, UTF-16LE/BE, XOR 0–255, ADD 0–255, SUB 0–255, bit-reverse, 5-bit packed (A=0 and A=1), 6-bit packed, font-glyph indices from 0x080853D4 with deltas −3…+3, and fixed-byte interleaving gaps 1–8. **Zero** code-table-shaped hits. The few incidental ASCII hits were verified by dumping ±0x40 bytes and are story text, credits, or food names, not password records.
4. **Hard-coded string inventory (Derived).** Regex extraction over the first 3 MiB found **20** NUL-terminated uppercase-only 4–10-letter strings in code regions (e.g. `DEBUG`, `PAUSE`, `SITH`, `DFVF`) and ~50 alphanumeric candidates. None is 4–8 characters drawn from a cheat-code alphabet in a pointer table. No fixed-stride record structure of code strings exists.
5. **Validator space (Inferred, bounded).** No `strcmp`/`memcmp` site compares a user buffer against a code constant: there is no user character buffer outside the save-name/frontend path, and no input handler with a 4–8 character bound plus comparison loop was found in the frontend scene range.

Because the accepted set is empty, **no novel code can be generated and no rejection test on a code can be performed**. Per §0.2 this is reported as a proven bounded negative rather than an untested absence. The closest in-scope positive result is the debug menu below.

### 6b.2 Hidden debug-menu space — positive enumeration

* **Space definition:** 5 menu scenes (`0x02`, `0x8D`, `0x8E`, `0x8F`, `0x90`); list counts 15/12/15/13/11 = **66 selectable entries** in total, all statically enumerated via their `{u16 id, char[34]}` records (§6.2 gives the 15 core entries; the four lists at 0x0824A538/0x0824AA48/0x0824B0E4/0x0824B228 give the rest).
* **Generator/oracle:** the dispatcher itself (0x080323BC) is a perfect oracle for which list/title/count each id selects; its five dispatch arms were read instruction-by-instruction, so the set of menu scenes is closed at five.
* **Novel combination:** the 15-entry core list is not published anywhere for the GBA SKU; `ERASE SAVED GAMES`, `UNLOCK MINI-GAMES` and `DEBUG AUDIO` are undocumented developer entries. They are reported as statically observed, **not** as runtime-confirmed selections.
* **Bounds proven by rejection:** writing `2` into the scene-request byte (IWRAM 0x030022F0, savestate raw 0x1B2F0) and reloading resets the game to the legal screen; the patched state was verified to contain `0x02` at that offset. This bounds *direct state injection* as a non-working path and is recorded as Unknown for retail reachability (§8).

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| ROM identity/hashes | Observed | `file`, `md5sum`, `sha1sum`, `sha256sum`, header dump |
| Stock crt0, not a scene release | Derived | entry word `EA00002E`, first 0x200 bytes match standard crt0 |
| Published codes absent as table | Observed | ~6,900 literal searches, 0 code-table hits; incidental hits dumped and reclassified |
| No code-entry UI text | Observed | whole-ROM `strings` keyword scan = 5 hits, none UI labels |
| All reachable screens enumerated | Observed | 11 screenshots in `/tmp/opencode/spongekrusty3/` |
| L+R = soft reset | Observed | frontend L+R → health & safety screen (screenshot `combo_changed_L_R.png`) |
| Debug menu exists, 15 core entries | Derived | 0x080323BC disassembly + literal pool + 15 valid 0x24-stride records + 0x00FF terminator |
| Four submenu lists/counts | Derived | 0x080323C0–0x080324D2 disassembly, literals resolved with Python `struct.unpack_from` |
| Direct scene-byte patch resets game | Observed | patched savestate verified `0x02` at 0x1B2F0; reload → legal screen |
| Font glyph table | Observed | bytes at 0x080853D4 dumped; xrefs at 0x080382FC/0x080383C4 |

## 8. Unknowns

1. **Retail gate for the debug menu.** The caller at 0x0800E3AC passes the byte at 0x030022F0 to the dispatcher, but 133 code sites reference that variable and the complete setter path was not reduced to a single input predicate. Direct savestate injection of `2` resets the game, so no claim is made that any button sequence reaches it. This is a **gated-feature unknown**, not a denial.
2. Whether `UNLOCK MINI-GAMES` or `ERASE SAVED GAMES` can be activated from the retail frontend at all (no runtime execution of the menu was achieved).
3. Content of the four submenus beyond their list bases and counts (names are present in ROM but were not individually transcribed here).
4. Whether a different regional SKU (e.g. Europe) contains a code screen absent from `BQ4E78`.

## 9. Tooling

* `/tmp/opencode/spongekrusty3/key.py` — PID-targeted XTEST key sender (correcting for multiple mGBA windows).
* Python 3 + Capstone 5.0.7 — literal-pool scanner, BL scanner, byte-transform code search, savestate PNG/`gbAs` parser and patcher.
* `arm-none-eabi-objdump -M force-thumb` — disassembly of 0x080323BC and 0x0800E374.
* REA MCP / Ghidra 12.1.4 — raw ARM import at 0x08000000 for cross-checking (auto-analysis treats several Thumb ranges as data; manual objdump was authoritative).
* mGBA 0.10.5 savestates (`st_main.ss1`, `st_opt.ss2`, `patched_debug.ss1`) and screenshots retained in the work directory.
* No ROM or copyrighted asset is redistributed by this report.

## 10. Legal note

Only addresses, hashes, algorithms, and tool scripts are published. No game graphics, music, or full text banks are reproduced.
