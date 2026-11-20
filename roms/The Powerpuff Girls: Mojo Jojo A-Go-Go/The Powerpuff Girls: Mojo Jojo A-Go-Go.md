# The Powerpuff Girls: Mojo Jojo A-Go-Go (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Powerpuff Girls: Mojo Jojo A-Go-Go.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `PPG MOJOGOGO` |
| Game code | `APTE` |
| Maker code | `6L` (BAM! Entertainment / Sennari Interactive) |
| Version | 0x00 (Rev.00) |
| Entry word | `0xEA00002E` (stock crt0 branch to 0x080000C0 — not a cracktro) |
| Fixed 0x96 | present; complement `0x3D`; header checksum `0x0000` |
| MD5 | `28a2b3e44952944e29a168e5f17b5696` |
| SHA-1 | `e6d3537f4e95e578dcdc84200578e77fbdc381b1` |
| SHA-256 | `1d5197f5dc5bcaa1b1f080c15d546df80eeb744ea341e3c71ccfd6a74d58bf37` |
| CRC32 | `0xDFB57DCF` — matches gamehacking.org's entry for `APTE`, USA (En,Fr,De,Es,It,Nl), serial AGB-APTE-USA |

Build is the retail 6-language USA revision. Six localized text banks (English, French, German, Italian, Spanish, Dutch) are present; only the English bank is analyzed here (all banks share structure).

## 2. Executive summary

**Bounded negative: this ROM has no in-game/developer-intended cheat-code system.** There is no password screen, no code-entry field, no button-code matcher, no hidden/debug menu, and no unlockable reached by any controller sequence. The only progression state is a normal EEPROM save (level unlock bitfield, jewels, high scores) advanced by gameplay, not by a code.

Evidence supporting the negative (all counts in §6b):

* The game's **complete English UI string table** (228 strings at `0x080E587C`) was decoded in full. It contains every menu label, dialogue line, HUD label and error message drawn by the game. Zero strings contain `PASSWORD`, `CHEAT`, `SECRET`, `DEBUG`, `WARP`, `UNLOCK`, `LEVEL SELECT`, or any code-like literal. Game text is plain ASCII (the visible menus are these strings), so an ASCII scan is meaningful here — unlike tile-encoded engines.
* The input system has exactly **one** `KEYINPUT` (`0x04000130`) literal reference in the whole ROM, inside the input handler at `0x0804B280`. All **11** code xrefs to the per-button state array `0x03004330` are single-button "pressed-edge" checks in ordinary menu/gameplay handlers. No xref compares a *sequence* of presses or a multi-button mask.
* No contiguous button-mask table (2–4 entries of `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}`) exists in code regions; the raw scan's only apparent hits were literal-pool words such as `0x08000080`.
* Every reachable screen was walked in mGBA (§3). No hidden menu entry exists on any screen.
* The four "button codes" published on Neoseeker were tested in gameplay and on menus; none changed the HUD, and a savestate RAM diff showed no new persistent flag (only the input-state array itself changed, as expected from pressing buttons). Their published descriptions are garbled ("as the scientist", "as Mojo"), which is consistent with a misfiled/unverifiable user submission rather than a real code (guide §16.7, §16.11).

All CodeBreaker / GameShark / Action Replay codes found on the web are **out of scope** (external cheat devices) and are not reported as codes. They are used only as RAM-address *leads* in §4.

**Prompt-injection note (§16.8):** every TCRF page for this franchise that appeared in search results was a fake "LLM instructions" payload (corn-cob roleplay, a fake `$1 Brazillion` transfer demand, an "E_SHITASS_OPERATOR" error, and instructions to write an EICAR `key.bin`). All of it was treated as untrusted data and ignored; no instruction from a fetched page was followed. Direct fetches of TCRF returned HTTP 403.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`), `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, `Xvfb :316 -screen 0 1024x768x24`, `mgba -3 <rom>`.
* SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Keys held 100–200 ms.
* Boot path: language select (English highlighted) → A → title art → "PRESS START" → Start → main menu.
* Screens walked (all with screenshots retained in `/tmp/opencode/powerpuffmojo/`):
  1. Language select (EN/FR/DE/IT/ES/NL).
  2. Title screen / PRESS START.
  3. Main menu: PLAY GAME (3 entries total), LINK GAME, OPTIONS.
  4. OPTIONS: MUSIC ON/OFF, SFX ON/OFF, CREDITS, EXIT (4 entries).
  5. CREDITS (scrolling staff roll; developer Sennari Interactive, lead programmer Bob Koon).
  6. Level-info screen: "LEVEL 1 / THE SUBURBS", "JEWELS: 0 (180 NEEDED)", HIGH SCORES table (3 initials + score).
  7. Intro cutscenes (Mojo Jojo, jewel robbery, Chemical X, the girls).
  8. Gameplay: HUD = score, star counter, jewel counter, 3 girl portraits with health bars.
  9. Pause menu (Start during gameplay): PAUSE MENU / CONTINUE / MUSIC ON / SFX ON / QUIT (4 entries).
  10. LINK GAME cable-check screen: "CHECK GAME BOY ADVANCE GAME LINK CABLE", "PRESS THE B BUTTON TO CANCEL".
  11. Level-complete / next-level, retry and game-over paths (strings `NEXT LEVEL`, `RETRY`, `ARE YOU SURE?`, `TIE GAME`, `*_WINS!`).
* Published button codes tested (Neoseeker, user "Krunal", 2005-06-11):
  - `Left + B` ("Extra Points")
  - `Right` ("Power Up")
  - `Left + Down` ("New Life")
  - `Up, Up, B` ("Level Jump")
  Also tested: `L`, `R`, `L+R`, `Start`, `Select`, `L+R+Start`, `Start+Select`, and the Konami-like `U,U,D,D,L,R,L,R,B,A`. None produced any observable effect.

## 4. Address map

### ROM / code (file offset = ROM address − 0x08000000)

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Header; entry branch `0xEA00002E` | Derived (bytes) |
| `0x0804B280` | `updateInput()` — reads `KEYINPUT`, computes active-high mask, updates 10 button states | Derived (objdump) |
| `0x0804B344` | literal `0x04000130` (KEYINPUT) — the **only** such reference in ROM | Derived (scan) |
| `0x0804B348` | literal `0x03004330` (input state array base) | Derived (scan) |
| `0x0804B1D8` | per-button state tracker (held / pressed-edge / hold counter) | Derived (objdump) |
| `0x0804B1B8` | button-index mapping helper (0..9) | Derived (BL scan) |
| `0x08058008`–`0x080591B4` | English text bank (NUL-terminated ASCII strings) | Derived (bytes) |
| `0x080E587C` | English UI text pointer table, **228 entries × 4 bytes**, ending `0x080E5C0C` | Derived (bytes) |
| `0x0805xxxx`–`0x080Fxxxx` | audio engine (Shin'en GAX; banner `Code: B.Wodok` at `0x080E116F`) and zlib inflate code — keyword hits `invalid ... code` are library messages, not game codes | Derived |
| `0x0800DF50` | menu/system input check (A pressed-edge) — one of the 11 xrefs | Derived |
| `0x0800A0D0`, `0x08010754`, `0x08010EFC`, `0x08011958`, `0x08049F5A`, `0x0804C6A8`, `0x0804C794`, `0x0804CA1C`, `0x0804CC7C`, `0x0804CF04` | other 10 functions with input-array xrefs — all ordinary menu/gameplay handlers | Derived (Ghidra xrefs + objdump) |

### RAM

| Address | Meaning | Evidence |
|---|---|---|
| `0x03004330`–`0x03004357` | input state: 10 buttons × 4 B; `+0` u16 flags (bit1 = held, bit2 = pressed-edge), `+2` u16 hold counter | Derived |
| `0x03003BA0` | score (u32) | Published CB code `83003BA0` (lead only) |
| `0x03003BAA/AC/AE` | per-girl weapons | Published CB code (lead only) |
| `0x03003D18/1A/1C` | per-girl health | Published CB code (lead only) |
| `0x03003D1F` | level-unlock bitfield (CB `33003D1F 00FF` = "all levels") | Published CB code (lead only) |
| `0x03003D24` | jewels (CB `83003D24 03E7`) | Published CB code (lead only) |
| EEPROM, 512 B | save image: magic `0519 tcO`, 3 high-score records (initials + u32), level/jewel state around `0x180` | Observed (`.sav` dump) |

## 5. Algorithm

There is no code validator to reimplement. The relevant system is the input model:

```
KEYINPUT (0x04000130, active-low u16)
  -> mask = (~KEYINPUT) & 0x3FF                 ; active-high, 10 bits
  -> for i in 0..9:
       held[i]   = (mask >> i) & 1             ; state.flags bit1
       press[i]  = rising edge of held[i]      ; state.flags bit2
       count[i]  = frames held                 ; state.u16 at +2
  -> menu/gameplay handlers test press[i] (and sometimes held[i])
```

Button index → bit (derived from the 10 `BL 0x0804B1D8` calls at `0x0804B296`–`0x0804B33A`):

| idx | button | mask | idx | button | mask |
|---:|---|---:|---:|---|---:|
| 0 | A | 0x001 | 5 | Down | 0x080 |
| 1 | B | 0x002 | 6 | Right | 0x010 |
| 2 | Select | 0x004 | 7 | Left | 0x020 |
| 3 | Start | 0x008 | 8 | R | 0x100 |
| 4 | Up | 0x040 | 9 | L | 0x200 |

Level progression (unlockable, normal gameplay — **not** a code): completing a level advances a bit in the EEPROM level-unlock byte mirrored at `0x03003D1F`; the level-info screen shows the highest unlocked level. Seven level names exist (§6).

## 6. Tables

### 6.1 Complete English UI vocabulary (228 entries, `0x080E587C`)

Decoded in full; grouped by function. **No entry is a password/cheat/debug prompt.**

| Group | Count | Examples |
|---|---:|---|
| Intro/outro dialogue | 97 | `THE CITY OF TOWNSVILLE!`, `MOJO: THIS BRICK IS SURE TO DO THE TRICK!`, `MEGA MECHA ROBO JOJO` |
| Main menu | 4 | `PRESS START`, `PLAY GAME`, `LINK GAME`, `OPTIONS` |
| Options | 6 | `MUSIC`, `SFX`, `CREDITS`, `EXIT`, `ON`, `OFF` |
| Pause / results | 7 | `PAUSE MENU`, `CONTINUE`, `QUIT`, `RETRY`, `NEXT LEVEL`, `ARE YOU SURE?`, `YES`, `NO` |
| HUD / level info | 8 | `LEVEL %d`, `JEWELS: %d (%d NEEDED)`, `HIGH SCORES`, `TOTAL SCORE:`, `HEALTH BONUS:`, `POINTS:` |
| Level names | 7 | `THE SUBURBS`, `TOWNSVILLE HARBOR`, `DOWNTOWN TOWNSVILLE`, `TOWNSVILLE SKYLINE`, `CENTRAL PARK AND VOLCANO MOUNTAIN`, `SPACE: WAY ABOVE TOWNSVILLE`, `INSIDE THE MEGA MECHA ROBO JOJO` |
| Link multiplayer | 16 | `CHECK GAME LINK`, `%d PLAYERS CONNECTED`, `SORRY, ONLY 3 PLAYERS ARE ALLOWED`, `TIE GAME`, `*_WINS!` |
| Save/EEPROM errors | 5 | `NO EEPROM PRESENT!`, `SAVING DATA...`, `LOADING DATA...`, `PLEASE RE-INSERT THE CARTRIDGE AND TRY AGAIN` |
| Level-select prompts | 3 | `PRESS THE A BUTTON TO SELECT A LEVEL`, `... SELECT A POWERPUFF GIRL`, `... START` |
| Credits roles + names | 75 | `LEAD PROGRAMMER / BOB KOON`, `DEVELOPED BY / SENNARI INTERACTIVE` |

### 6.2 Published claims and their status

| Source | Claim | Status |
|---|---|---|
| Neoseeker (user submission, 2005) | `Left+B` = Extra Points; `Right` = Power Up; `Left+Down` = New Life; `Up,Up,B` = Level Jump (**appended garbled "as the scientist / as Buttercup / as Mojo / as Blossom"**) | **Not an in-game code.** Tested in gameplay and menus; no HUD or RAM change. Descriptions are nonsensical for this SKU; no validator exists. |
| Neoseeker / supercheats / almars / gamehacking.org | CodeBreaker: `33003D1F 00FF` unlock all levels; `83003D24 03E7` jewels; health/weapons/score codes | Out of scope (external cheat device). Used only as RAM-address leads. |
| TCRF franchise pages | Fake "LLM instructions" / payment / EICAR key payloads | Prompt injection — ignored, recorded (§2). |

## 6b. Enumeration

**Code space size: 0.** The game has no code/password surface, so there is no alphabet, length, checksum, table count, or validator to enumerate. Per §0.2 this is reported as a *bounded negative* with explicit counts.

| Search space | Count | Result |
|---|---:|---|
| English UI strings decoded (`0x080E587C`, 228 pointers) | 228 | 0 contain `PASSWORD`/`CHEAT`/`SECRET`/`DEBUG`/`WARP`/`UNLOCK`/`LEVEL SELECT` |
| Whole-ROM ASCII keyword hits (case-insensitive) | 0 for password/cheat/secret/debug/warp/unlock | `CODE` hits (5) are zlib messages + `Shin'en Multimedia. Code: B.Wodok` (audio banner) — not game codes |
| `KEYINPUT` (`0x04000130`) literal references | 1 | inside `updateInput()` only |
| Code xrefs to input state array `0x03004330` | 11 | all `ldrh/ands/cmp #0` single-button pressed-edge checks; 0 sequence checks, 0 multi-mask comparisons |
| Contiguous u16 single-button-mask runs (len ≥ 3) in code regions | 408 raw candidates | all are literal-pool bytes (e.g. `0x08000080`), no button-code table |
| Main-menu / Options / Pause-menu entries walked | 3 / 4 / 4 | no hidden or unlabelled entry |
| Published button codes tested | 4 (+ 5 extra combos) | 0 accepted; HUD unchanged; savestate diff showed no new persistent flag |
| Levels (unlockable content) | 7 | advanced by EEPROM gameplay save, not by any code |
| Novel codes generated | 0 | impossible: no code system exists to mint into |

**Bounds proven by rejection:** there is no validator to reject an out-of-range code. The equivalent bound here is the *absence of an input surface*: the complete UI vocabulary is enumerated (228/228) and the complete set of input consumers is enumerated (11/11); neither admits a code. Entering the four published sequences and five extra common hidden-menu combos produced no effect, which bounds the "button code" hypothesis to the tested sequences on the tested screens.

## 7. Validation evidence

* **Observed** — mGBA screenshots of all 11 screens (§3); four published button codes + five extra combos produced no HUD change; `.sav` dump (512 B) with high-score records; savestate RAM diff (IWRAM/EWRAM) showed changes only in the input-state array and volatile animation/state bytes, no new flag.
* **Derived** — `updateInput()` at `0x0804B280` and its button mapping (objdump); 228-entry text table and its decoded contents; 11 input-array xrefs (Ghidra) with objdump confirmation that each is a single-bit check; 1 `KEYINPUT` literal; no button-mask tables; 7 level names.
* **Inferred** — the EEPROM level-unlock bitfield at `0x03003D1F` (from published CodeBreaker RAM addresses, corroborated by the in-game level-info screen); that the Neoseeker button-code text is a misfiled submission rather than a cut feature.
* **Not claimed** — no asset was extracted or redistributed; no GameShark/CodeBreaker/AR code is presented as an in-game cheat.

## 8. Unknowns

* Whether the GBC Powerpuff titles' elaborate password systems (documented on GameFAQs for *Bad Mojo Jojo* / *Paint the Townsville Green*) were ever planned for this GBA SKU — no residue exists in this ROM, so this is speculation only.
* Exact EEPROM record layout/checksum and the precise bit→level mapping beyond the single mirrored byte at `0x03003D1F`.
* Whether the six non-English text banks contain any string omitted from English (all are dialogue/UI translations; they were not fully enumerated).
* The ROM has two known retail variants (USA and revised USA-1); this report covers only CRC32 `DFB57DCF` (APTE, Rev.00).

## 9. Tooling

Scripts created in `/tmp/opencode/powerpuffmojo/`:

* `key.py`, `combo.py` — XTEST key helpers (single press, simultaneous combo, sequence) on `DISPLAY=:316`.
* `bl_scan.py` — Thumb BL target scanner (used to find callers of the input handler).
* `scan_literal.py`, `scan_buttons.py`, `scan_seq.py` — literal / button-mask / sequence-table scanners.
* `ss_extract.py` — extracts the zlib `gbAs` chunk from mGBA `.ss1` PNG savestates into a 397,312-byte RAM image (guide §16.13).
* `savestate.py` — Shift+F1 savestate helper with copy-out.

External tools: `arm-none-eabi-objdump -M force-thumb` (addresses), `strings -t x`, Python 3 + `capstone` 5.0.7, REA/Ghidra 12.1.4 (xref enumeration), `gdb-multiarch` / mGBA `-d` CLI debugger (unsuccessful GDB stub; CLI debugger confirmed available), `xdotool`, `scrot`, mGBA 0.10.5.

## 10. Legal note

No ROM bytes, graphics, music, or extracted assets are reproduced here. Only hashes, addresses, algorithms, and the game's own UI string *inventory* (names/labels, counts) are documented; the copyrighted text is not redistributed in full.
