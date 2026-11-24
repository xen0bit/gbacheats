# Ten Pin Alley 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ten Pin Alley 2/Ten Pin Alley 2.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `TENPINALLEY2` |
| Game code | `BTPE` |
| Maker | `FS` |
| Version | 0x00 |
| Complement / checksum | 0x16 / 0x0000 (both fail the Nintendo check-sum arithmetic — typical commercial/scene header, not a modified entry point) |
| Entry word | `0xEA00002E` → stock branch to `0x080000C0`; crt0 at 0x080000C0 branches to `main` at `0x080001D1`. No cracktro/trainer observed in first 4 KiB. |
| MD5 | `45880f41cfe125320e65b76bb05edaaa` |
| SHA-1 | `bcd146d58d74f054553996bbc4319c4ff3a2ef1b` |
| SHA-256 | `3fc858042375e457392cfb09604c6f34e8732923efa3e86aad289ab0a30b6fd1` |

Engine attribution: the credits text bank prints `X2 Engine™ licensed from Sennari Games, Inc.` at ROM file offset `0x282A8`. Developer Pronto Games, publisher XS Games.

## 2. Executive summary

**Bounded negative: this SKU has no in-game/developer-intended cheat system.** There is no password/cheat code screen, no hard-coded password or cheat table, no button-sequence validator, no hidden debug menu reachable by any controller input, and no unlockable character/alley/track gated behind a code. Everything reachable is ordinary gameplay configuration exposed openly in the menus.

Evidence layers:

1. **Published recon (Observed):** no cheat list exists for the GBA SKU. GameFAQs' only guide (KeyBlade999, FAQ 65591) has no cheats section and explicitly lists L, R and Select as "N/A"; the GameFAQs cheats page has no entries and no archived snapshot. The only hits for "Ten Pin Alley 2 + codes" are PlayStation 2/Wii codes and CodeBreaker-style memory writes for other SKUs (out of scope).
2. **Text bank decoded (Observed):** the game's UI text is *not* rendered from ASCII strings in the usual `strings` sense — but it *is* stored as Latin-1 bytes in a contiguous bank at file offsets `0x27400–0x28400`, separated by NUL and `0xFF`, in five languages (English, French, Spanish, Italian, German). I decoded all **72** printable NUL-delimited strings in that bank and all **9,069** printable strings in the whole 4 MiB image. Zero occurrences, in any language or encoding (Latin-1, lowercase-folded, UTF-16LE/BE), of `pass`, `password`, `cheat`, `code`, `secret`, `debug`, `unlock`, `hidden`, `bonus`, `extra`, `develop`, `mot de passe`, `contraseña`, `codice`, `passwort`, `clave`, `truc`. The engine's message pointer table references exactly **58** distinct strings (game messages, 8 character names, 8 winner messages, credits) — none is a cheat/unlock message.
3. **Input surface (Observed):** every menu on every reachable screen exposes only normal game options; there is no character/keypad entry widget. The keyboard reader at `0x080002E0` stores active-high held buttons at `0x03004078` and freshly-pressed buttons at `0x03004080`. There are **31** code sites that read those RAM words. The button masks tested near them are only single buttons, D-pad mask `0x0FF`/`0x0C0`/`0x0F0`, the GBA soft-reset chord `0x00F` (A+B+Select+Start), and pause `0x00C` — all standard UI handling. No multi-button cheat chord exists.
4. **Button-code table scan (Derived):** exhaustive scans of every aligned `u8`, `u16` and `u32` value in the image for active-high key-mask sequences found 428 / 11 / 2 candidate runs (length ≥5, ≥3 distinct masks) respectively. **Zero** of those addresses have a 32-bit pointer or Thumb-bit pointer (`addr|1`) reference from code, so none can be a validator table.
5. **Dynamic walk (Observed):** all 14 reachable screens were visited in mGBA with screenshots. Holding L+R (2 s), L+R+Select, Select+Start, and the Konami sequence at the title screen produced no cheat acknowledgment, hidden menu, unlock dialog or flag screen. All 8 characters, all 4 alleys, all 4 jukebox tracks and all 3 pause-menu entries are available on a fresh file.

Because no validator, code table, or code-entry surface exists, §0.2's "mint a novel code" deliverable is not applicable here. Instead the negative is bounded by the counts above.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `-3` scale, keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
- Boot → Pronto Games splash → title "Press START" → Start.
- Menu path: `Practice` or `Tournament` → character select (8) → "How Many Players?" → opponent select (4) → "Which Alley?" (4) → alley cinematic → gameplay → Start for pause (Resume/Restart/Quit).
- `Options` → `Audio Options` (Music Level, SFX Level, Jukebox with 4 tracks) and `Credits` (scrolling).
- Cheat probes attempted at title: `L+R` held 2 s, `L+R+Select`, `Select+Start`, `↑↑↓↓←→←→BA`. None produced a hidden screen.
- No codes were entered because no code-entry surface exists. No GameShark/CodeBreaker/AR codes were used.

## 4. Address map

| Address (ROM) | File offset | Meaning | Evidence |
|---|---|---|---|
| `0x08000000` | `0x000000` | Entry branch `0xEA00002E` → `0x080000C0` | Observed (header dump) |
| `0x080000C0` | `0x0000C0` | Stock ARM crt0 | Derived (disassembly) |
| `0x080001D1` | `0x0001D1` | `main` (Thumb) | Derived (crt0 literal) |
| `0x080002E0` | `0x0002E0` | Keypad reader: `held = ~KEYINPUT & 0xFFFF`, `pressed = held & ~prev_held` | Derived (`0x80002E2…0x80002FE`) |
| `0x08000300` | `0x000300` | Literal `0x04000130` (KEYINPUT) | Observed |
| `0x08000304` | `0x000304` | Literal `0x03004080` (pressed) | Observed |
| `0x08000308` | `0x000308` | Literal `0x03004078` (held) | Observed |
| `0x03004078` | — | IWRAM: active-high held-button mask | Derived |
| `0x03004080` | — | IWRAM: active-high newly-pressed-button mask | Derived |
| `0x08027400–0x08028400` | `0x27400–0x28400` | Five-language Latin-1 text bank (72 strings) | Observed |
| `0x080282A8` | `0x282A8` | `X2 Engine™ licensed from Sennari Games, Inc.` | Observed |
| `0x08027424` | `0x27424` | `STRIKE!` (first of 5 gameplay messages) | Observed |
| `0x08027817` | `0x27817` | `Practice` / `Tournament` / `Options` menu strings | Observed |
| `0x080E9400–0x08013E00` | `0xE9400–0x13E00` | Engine UI/gameplay code (all 31 keypad-RAM xrefs) | Derived (Capstone scan) |

No validator, password buffer, cheat table, alphabet table or debug-gate function exists to map.

## 5. Algorithm

Not applicable — no password/codec/validator was found. The only "algorithm" relevant to the search is the engine's input pipeline:

```text
KEYINPUT (0x04000130, active-low)  ->  held  = ~KEYINPUT & 0xFFFF   @ 0x03004078
pressed = held & ~previous_held                                    @ 0x03004080
UI code reads pressed/held and branches on single-button masks only.
```

Search algorithms used (reproducible):

```text
text_bank_scan:
  for each NUL-delimited run in 0x27400..0x28400 (and whole ROM):
    decode Latin-1; case-fold; test 17 cheat-related keywords (5 languages)
button_run_scan:
  for width in {1,2,4}:
    for each aligned value v in ROM:
      if v ∈ {1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}:
        extend contiguous run; emit runs with len≥5 and ≥3 distinct masks
        for each run address: search whole ROM for ptr(addr) and ptr(addr|1)
input_xref_scan:
  for each Thumb LDR-literal in 0x08000000..0x08019000:
    if literal value ∈ {0x03004080,0x03004078}: record site
    disassemble following 0x40 bytes; census all button-range immediates
```

## 6. Tables

**Alphabet/charset:** the game's font is a bitmap glyph set; UI text is stored as Latin-1 bytes (NUL-terminated, `0xFF` as per-string language separator; accented letters 0xE9 `é`, 0xFA `ú`, 0xE4 `ä`). There is **no restricted code alphabet** (no `0-9A-Z` wheel, no symbol grid, no 5-bit/6-bit packed alphabet) anywhere in the image.

**Message pointer table (0x08027460–0x08027818, resolved):** 58 distinct strings — 5 gameplay messages (`STRIKE!`, `SPARE!`, `GUTTER BALL!`, `FOUL!`, `PRESS THE A BUTTON!`), 8 winner messages, 8 character names, `P L A Y E R` glyphs, `Please Wait`, `Now Playing:`, `Press START`, and credits. No cheat/debug/unlock record.

**Button masks (active-high):** A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200. Masks actually tested near keypad reads: 0x001, 0x002, 0x003, 0x006, 0x008, 0x009, 0x00B, 0x00C (pause), 0x00F (soft reset), 0x010, 0x01F, 0x020, 0x055, 0x080, 0x0C0, 0x0F0, 0x0FF. Multi-bit values ≥0x055 are byte/nibble masks in unrelated struct code (e.g. `movs r3,#0x55` at `0x08012478` stores a constant into a struct field), not input gates — verified by disassembly.

**Characters (all available from a fresh file):** Queenie, Flo, Candie, Chucky, Biff, Sarge, Buzz, Tango.
**Alleys (all available from a fresh file):** Bait -n- Bowl, Ten Pin Alley, Maui Bowl, Lucky Bowl.
**Jukebox tracks (all available):** Maui Bowl, Bait -n- Bowl, Ten Pin Alley, Lucky Bowl.

## 6b. Enumeration

This engagement is a **bounded negative**, so the enumeration is the enumeration of the *search space*, not of generated codes.

| Space checked | Size scanned | Result |
|---|---|---|
| Printable Latin-1 strings, text bank `0x27400–0x28400` | 72 strings | 0 cheat/password/debug keywords (17 terms × 5 languages) |
| Printable Latin-1 strings, entire ROM | 9,069 strings | 0 cheat/password/debug keywords |
| UTF-16LE / UTF-16BE `cheat`, `password`, `debug`, `secret` | 4 MiB × 2 encodings | 0 hits |
| Engine message-pointer table | 58 distinct strings | 0 cheat/unlock/debug messages |
| Aligned active-high mask runs, width 1 (u8) | 428 candidates (len≥5, ≥3 distinct) | 0 with any code pointer xref |
| Aligned mask runs, width 2 (u16) | 11 candidates | 0 with any code pointer xref |
| Aligned mask runs, width 4 (u32) | 2 candidates | 0 with any code pointer xref |
| Thumb LDR-literal xrefs to keypad RAM | 31 code sites | 0 undocumented cheat chords; only UI single-button masks + soft-reset 0xF + pause 0xC |
| Reachable screens walked in mGBA | 14 screens | 0 code-entry surfaces, 0 hidden menus, 0 locked characters/alleys/tracks |
| Probes at title screen | 4 (L+R hold, L+R+Select, Select+Start, Konami) | 0 cheat acknowledgements |

**Novel codes:** none exist to mint. There is no validator to reverse and no code space to enumerate; any claimed "novel code" would be a fabricated artifact of the analysis, not a real in-game input.

**Rejection bounds:** not applicable — no code can be accepted or rejected because no validator exists. The closest bounded rejection test is the dynamic probe: four classic cheat inputs were entered on the game's own title screen and produced no state change (screenshots `32_LR_held.png`, `32_Sel_Start.png`, `32_konami.png` in the work dir).

**Code space size:** 0 accepted strings, 0 accepted button sequences (beyond ordinary menu controls), 0 hidden menu states reachable from controller input.

## 7. Validation evidence

- **Observed:** ROM header/hashes; stock entry branch; 72-string decoded text bank with 5 languages; zero keyword hits across 3 encodings; 58 resolved message-table strings; mGBA screenshots of all 14 screens; 4 cheat probes with no effect; 0-byte `.sav` after early play.
- **Derived:** keypad reader at `0x080002E0` and RAM addresses `0x03004078`/`0x03004080` from Thumb disassembly; 31 input-RAM xref sites and their immediate-mask census from Capstone; zero pointer xrefs to candidate button-run addresses; menu dispatch uses only visible entries.
- **Inferred:** winner/results screens exist as text (`"<character> wins the tournament!"`) but were not reached by completing a full 10-frame tournament; they are ordinary game flow, not cheat content. The header complement/checksum mismatch is a scene-release artifact, not evidence of a modified game (the entry branch and crt0 are stock).

## 8. Unknowns

- A full 10-frame tournament was not played to completion, so the end-of-tournament results screen was not observed directly (its strings are in the bank). No cheat content is associated with it.
- Language selection mechanism was not located; the five-language bank exists but no in-game language menu was found. This is a localization detail, not a cheat surface.
- SRAM write behavior after a completed match was not examined; the 0-byte `.sav` shows no progress data exists at the title/early screens.
- No REA/Ghidra decompilation was used: the shared REA session was busy importing another agent's target (Drill Dozer) and timed out. All conclusions rest on direct byte/string scans, Capstone/objdump disassembly and emulator observation.

## 9. Tooling

- `objdump`/`arm-none-eabi-objdump -M force-thumb` for targeted disassembly; Python 3 + Capstone for literal-load/xref and instruction-immediate scans.
- Scripts in work dir `/tmp/tenpin2/`: `key.py`, `scan_buttons.py`, `keypad_xrefs.py`, `scan_input_cmp.py`, `input_mask_census.py`, `probe_codes.py`.
- Screenshots in work dir: `00_title.png` … `32_*.png` (title, menus, character/alley/player selects, gameplay, pause, jukebox, credits, cheat probes). None are stored in the ROM folder.
- Fetched web data treated strictly as data: GameFAQs FAQ via Wayback (`20181231083932`), GameFAQs cheats page (no snapshot exists), search-result snippets. No instructions found in fetched content were followed.

## 10. Legal note

No ROM bytes, extracted graphics, music or game text are redistributed here. Only hashes, addresses, counts and original observations are published.

## 11. Cleanup

All mGBA/Xvfb/openbox processes started for this engagement were terminated by PID; the emulator artifacts (`Ten Pin Alley 2.sav`) were removed from the ROM folder. No `INDEX.md` or guide edits were made (coordinator rule).
