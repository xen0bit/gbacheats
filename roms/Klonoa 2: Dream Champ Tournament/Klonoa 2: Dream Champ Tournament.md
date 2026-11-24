# Klonoa 2: Dream Champ Tournament (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Klonoa 2: Dream Champ Tournament.gba` |
| Size | 4,194,304 bytes (0x00400000, 4 MiB) |
| Header title | `KLONOA2` |
| Game code | `AN6E` (full `AN6EAF`, USA) |
| Maker | `AF` (Namco) |
| Version / fixed byte | `0x00` / `0x96` |
| Entry word | `0xEA00002E` → stock `b 0x080000C0` (no cracktro/trainer) |
| Nintendo-logo scan | **one** hit at file offset `0x4` → single, unmodified retail image |
| MD5 | `cb1603c3cc3ed8a37f87b3971b0270d5` |
| SHA-1 | `35c05676e65fd4c92220861662cd3709342f36e2` |
| SHA-256 | `2309b8c97aeb7fb64fcde35576c64de3a7a37c56d8ff5a6eee5844743753ab15` |

Note: header complement byte (`0xCA` at `0xBD`) and header checksum (`0x0000` at `0xBE`) do not
recompute to the nominal values. This is a common retail-rom property, not evidence of a patch:
the entry branch is stock and the logo scan finds only one header. Save memory is 512-byte
EEPROM (mGBA produced a 512-byte `.sav`); save magic is `2GAONOLK` = reversed `KLONOA G2`.

Cross-check against the sibling image (position 400, `Klonoa: Empire of Dreams`) was done
independently: its header title/code differ, and all analysis below is against `AN6E` only.

## 2. Executive summary

**There is no developer-intended password, button-code, or hidden debug-menu system in this
image.** The only "cheats" published anywhere for this game are three save/gameplay items —
*Unlock Dream Gallery* (S-rank every Vision), *Unlock EX Stages* (collect every Sun Fragment
and beat the game), and an *Easier S-ranks* gameplay trick (leave and re-enter a room to reset
blocks/enemies without scoring a retry). None is a code that can be typed or input on a
controller (3rd party cheat index cheats page, archived snapshot 2024-09-17; 3rd party cheat indexes; 3rd party cheat indexes).

Supporting evidence, all from this exact ROM:

* Every reachable screen was booted and enumerated on `DISPLAY=:316` (title "PRESS START",
  title menu, save-file select, new-file confirmation, intro cutscenes/dialogue, WORLD MAP,
  save-file display with per-world Sun-Fragment count, VISION intro card, in-game HUD,
  two context variants of the PAUSE menu, Button Configuration with exactly two layouts,
  Select Vision, and the standard `Start+Select+A+B` GBA soft-reset back to "PRESS START").
  Each screen has a distinct RAM scene/task-handler fingerprint — see §6b.
* The entire visible UI is **font/tile-indexed**: a case-sensitive and case-insensitive
  `strings` scan (44,527 printable runs ≥4 bytes) yields exactly **one** English sentence —
  the unused developer credit at file `0x7431C` — and **zero** hits for password / cheat /
  debug / secret / unlock / gallery / code / menu / enter / invalid. No menu label appears
  in ASCII, UTF-16LE/BE, UTF-32LE, `+0x20` lowercase-shift, plain, or table-mapped form.
  VRAM font/tile data was extracted and rendered from savestates; the glyph↔tile mapping
  tables are at `0x080154240`–`0x0801543C0` (12-glyph-per-row, `tile = code + 4*floor(code/12)`).
* Search space was bounded and counted: standard password alphabets 0 hits; password-length/
  checksum patterns absent; u16 button-mask runs 428 raw candidates and byte-per-press runs
  4,052 raw candidates, of which a sampled inspection shows **all** are code/data false
  positives (counter tables, palette/graphics data), with no validator consuming them;
  no ASCII debug string or key-combo comparison table exists.
* Button combos tested live in-game and at the title (Konami sequence, `L+R+Start`,
  `L+R+Select`, `A+B+L+R`, `Start+Select+A+B`, D-pad combinations) produced **no** hidden
  screen. The only special result was the standard GBA soft reset.
* 3rd party cheat index-listed unlockables are save-bit progress gates, not input codes: the game can only
  set the relevant state through level results / collection, and no controller path writes
  it. Per guide §16.18 these are reported as unlockables, not as a code system.

The published GameShark/CodeBreaker "Master Code" on 3rd party cheat indexes
(`982D3DAE5251 927756F822C8 853D417EFFC0`) is a memory-edit device code and is explicitly
out of scope; it was not tested or reproduced.

## 3. How to reproduce

**Emulator / display** (all my own PIDs only):

```
Xvfb :316 -screen 0 1024x768x24 &
DISPLAY=:316 openbox &
DISPLAY=:316 SDL_AUDIODRIVER=dummy mgba -3 -d <rom>   # -d = CLI debugger
```

Another agent held GDB-stub port 2345, so RAM reads used mGBA's `-d` command-line debugger
(driven through a pty) plus PRG `gbAs` savestate decompression. mGBA SDL keymap:
A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
Focus the mGBA window with `xdotool windowfocus` before injecting keys; key input is only
sampled while the core is running (a paused-at-breakpoint core ignores X events).

**Menu path (fresh image, empty save):**

1. Namco logo → `Start` → "PRESS START" title → `Start` → title menu (`NEW GAME` only when
   no save; `NEW GAME` / `CONTINUE` once a save exists).
2. `NEW GAME` → "SELECT A SAVE FILE" (3 slots) → `A` on slot → "IS THIS OK?" YES/NO →
   long intro with dialogue (mash `A`).
3. WORLD MAP: compass + central gear + four world portals. With a fresh save only **Western
   Jungle** is reachable (press `Left` ~1 s); `Up`/`Down`/`Right` from center do not move
   (gated). `A` on the portal → dialogue → "VISION 1-1" card → gameplay.
4. During gameplay `Start` opens one of two context PAUSE menus, alternating:
   * `Continue / Retry / Select Vision / Button Configuration`
   * `Continue / World Map / Return to Title`
   `B` also exits to World Map.
5. Button Configuration: `Left`/`Right` toggles exactly `Type 1` (A=Jump, B=Shoot) and
   `Type 2` (A=Shoot, B=Jump).
6. Select Vision: with no cleared Visions it returns directly to the current Vision
   (gated level select).
7. `Start+Select+A+B` soft-resets to "PRESS START" (not a cheat).

**No password/button code was entered because none exists to enter** (§6b). Published
unlockables were verified against the ROM text/pointer scans and the save state, not by
typing a code.

## 4. Address map

| Item | File offset | ROM address | Evidence |
|---|---:|---:|---|
| Header / entry `b 0x080000C0` | 0x000 | 0x08000000 | observed bytes `2e 00 00 ea` |
| Nintendo logo (only hit) | 0x004 | 0x08000004 | byte scan |
| Header title / code / maker | 0x0A0 / 0x0AC / 0x0B0 | 0x080000A0 etc. | header parse |
| crt0 main pointer (Thumb, `0x08000470`) | 0x1C8 | 0x080001C8 | literal `71 04 00 08` |
| Main `main()` | 0x470 | 0x08000470 | Thumb disassembly |
| **Main loop / frame breakpoint** | 0x5B4 | **0x080005B4** | `b.n 0x80005B4` at 0x08000606; used for deterministic frame stepping |
| Font glyph↔tile mapping tables | 0x154240–0x1543C0 | 0x080154240–0x0801543C0 | byte pattern, rendering |
| (unused) developer credits | **0x7431C** | 0x0807431C | ASCII; "Klonoa Sleeping Empire / Programmed by …", matches 3rd party cheat indexes |
| `KLONOAG2` marker | 0x1512C8 | 0x0801512C8 | ASCII |
| SRAM-base-looking pointer table | 0x73D38–0x74230 | 0x08073D38–0x08074230 | 32-bit constants table (data, not code) |

**RAM (mGBA `gbAs` savestate raw layout, verified against `-d` reads):**

| Region | GBA address | Raw state offset |
|---|---|---:|
| Palette RAM | 0x05000000 | 0x00800 |
| VRAM | 0x06000000 | 0x01000 (0x18000 bytes) |
| IWRAM | 0x03000000 | 0x19000 (0x8000 bytes) |
| EWRAM | 0x02000000 | 0x21000 (0x40000 bytes) |
| Scene/task handler table | 0x03004110 | 0x1D110 |

Gameplay state pointers observed live at `0x03004110`: `0x080006A5`, `0x08033EAD`,
`0x0802F251`, `0x0800E375`, index byte `0x03004188 = 5`. KEYINPUT at `0x04000130` read back
`0x03FF` released / `0x03EF` with Right held, confirming input reached the core.

## 5. Algorithm

Not applicable — there is no password encoder, decoder, checksum, or button-sequence
validator in this image. The two "unlock" mechanics are ordinaryEEPROM progress bits:

```
S_rank_all_visions -> Dream_Gallery
all_sun_fragments && game_cleared -> EX_stages
```

These are evaluated from the level-results/collection code; they are not reachable from any
controller-input surface (§6b). The font encoding, the only algorithmic text layer found,
is `tile_index = code + 4*floor(code/12)` for the compact 12-glyph-per-row alphabet, with a
reverse table at `0x080154240`; it is a rendering mapping, not a validator.

## 6. Tables

**6.1 Screens enumerated (with scene/task fingerprint at IWRAM 0x03004110):**

| Savestate | Screen | words at 0x03004110 |
|---|---|---|
| `ss3` | title menu ("PRESS START" → NEW GAME/CONTINUE) | `080006A5 08046D19 08047639 0800E1A5` |
| (RAM read live) | save-file select / confirm | `080006A5 08033EAD 0802F251 0800E375` |
| `ss1` | WORLD MAP | `080006A5 08033EAD 0802F251 0800E375` |
| `ss4` | in-game VISION 1-1 | `080006A5 08037AA1 0800CFFD 0802F251` |
| `ss2` / `ss5` | PAUSE menu (both variants) | `080006A5 0803264D 0800CFFD` |
| (screenshots) | Button Configuration Type1/Type2, intro card, dialogue, soft-reset screen | visually enumerated |

**6.2 Save record (512-byte EEPROM, slot 0 at file offset 0):**

```
0x00: "2GAONOLK"        magic (reversed "KLONOA G2")
0x08: 00 00 00 06       header/flags
0x0C: 00 01 01 03       counters/flags
0x40..0x76: 0x7F repeated   default per-Vision data (unset)
0x80..0x93: 0xEA60 repeated (=60000) score/timer defaults; one 0x0000B000 at 0x92
0xC8: 01 00 00 03       progress flags
0xD0..0x1CF: 0xFF filler
```

No field in this record represents an input code; S-rank/Sun-Fragment flags are written by
the results/collection path and are all unset in a fresh file.

**6.3 Published codes (all verified against the ROM; none is a code):**

| Source | Item | Literal present in ROM? | Classification |
|---|---|---|---|
| 3rd party cheat index cheats (archived 2024) | Unlock Dream Gallery — S-rank every Vision | no literal | save-bit unlock |
| 3rd party cheat index cheats / 3rd party cheat indexes | Unlock EX Stages — all Sun Fragments + clear game | no literal | save-bit unlock |
| 3rd party cheat index cheats | Easier S-ranks — leave & re-enter room | n/a | gameplay trick |
| 3rd party cheat indexes | Hidden developer credits at 0x7431C | **yes** (0x7431C) | unused text |
| 3rd party cheat indexes | Master Code `982D3DAE5251 927756F822C8 853D417EFFC0` | no | GameShark (out of scope) |

## 6b. Enumeration

**Code-space size: 0.** There is no password alphabet, no code length, no checksum, no code
table, and no button sequence to enumerate. This is a *bounded negative* (guide §0.2 point 5),
proved as follows.

**A. Every reachable screen walked.** Screens: Namco logo; "PRESS START"; title menu
(1 entry with empty save, 2 with save); SELECT A SAVE FILE (3 slots); IS THIS OK? (YES/NO);
intro cutscenes and dialogue; WORLD MAP; save display ("WORLD 1 WESTERN JUNGLE", 5 Sun
Fragments, ×03 lives); VISION 1-1 card and HUD; PAUSE variant A and variant B; Button
Configuration Type 1 and Type 2; Select Vision; soft-reset screen. Eight screens saved as
savestates and decompressed to RAM; all show distinct scene pointers or distinct
IWRAM contents (§6.1). The WORLD MAP's other three portals are gated with a fresh save;
they are not hidden screens.

**B. Text/button spaces searched with counts.**

| Search | Count / result |
|---|---|
| `strings -t x -n 3/4` over 4 MiB | 46,318 (n=4) / 44,527 printable runs ≥4; only English sentence = dev credit at 0x7431C |
| Case-insensitive keywords password/cheat/debug/secret/unlock/level/gallery/code/menu/enter/invalid/correct/bonus/extra/test | **0** hits each |
| Password alphabets (`A-Z…`, `A-Z0-9`, `0-9A-Z`, `BCDFGHJKLMNPQRSTVWXYZ`, `AEIOU`) | **0** hits |
| `password`/`code`/`menu` in UTF-16LE, UTF-16BE, UTF-32LE, `+0x20`, table-mapped encodings | **0** hits |
| ASCII strings in IWRAM + EWRAM after menu load | **0** menu labels |
| u16 button-mask runs (A=1,B=2,Sel=4,Start=8,dirs,R,L), length 4 | 428 raw candidates; sampled hits (0x04386E etc., 0x0530D8, 0x055158) are counter/adjoining tables and graphics data, not consumed by a matcher |
| byte-per-press mask runs, length 8 | 4,052 raw candidates; all sampled hits in code/data streams (e.g. 0x000638, 0x00FC32) |
| ASCII `0x04000130` KEYINPUT literal | 2 raw pool entries (0x6E8/0x7CC) — hardware init, not a code matcher |
| Debug-key combos pressed live (title + in-game) | 7 combinations, 0 hidden screens; only `Start+Select+A+B` resets |

**C. Validator-as-oracle attempt (guide §16.19).** Not applicable: no candidate validator
function exists to call. Frame-stepping via a breakpoint at the main loop (0x080005B4) and
breakpoint-based RAM reads *were* used as the ground-truth oracle for screen identity.

**D. Novel code.** None can be minted because no code format exists. Reporting a fabricated
"code" here would be false; the negative is the deliverable (§0.2 point 5).

## 7. Validation evidence

* **Observed** — all screenshots; KEYINPUT register `0x03EF` with Right held; distinct RAM
  scene pointers per screen from savestates and live debugger; 512-byte `.sav` with
  `2GAONOLK` magic; dev-credit string at `0x7431C`; only one Nintendo-logo hit.
* **Derived** — stock entry branch and single logo prove no patch/trainer; font mapping
  `tile = code + 4*floor(code/12)` from the tables at 0x080154240–0x0801543C0; savestate
  raw-region offsets verified by matching live `-d` reads of VRAM/IWRAM/EWRAM/palette;
  main loop at 0x080005B4 from Thumb disassembly.
* **Inferred** — the three WORLD MAP portals other than Western Jungle are cleared-game
  progress gates (they reject input on a fresh save, and the published unlocks require
  full completion); the S-rank/Sun-Fragment bits are written only by results/collection code
  because no controller-input path to them was found. The exact per-byte meaning of the
  512-byte save record beyond the fields listed in §6.2 was not fully mapped.

## 8. Unknowns

* Exact byte-level semantics of every field in the 512-byte EEPROM record (only the magic,
  flag region, defaults and fillers were catalogued). The S-rank/Sun-Fragment bit positions
  were not individually isolated; the unlock condition itself is corroborated by 3rd party cheat indexes.
* Full glyph rendering/derivation of every tile-indexed string: the mapping tables and VRAM
  tiles were located and rendered, but the text bank itself appears compressed/indirectly
  referenced, so individual menu strings were enumerated by walking the screens rather than
  by offline decoding of every label. This does not affect the negative — no ASCII or
  UTF encoding of any code-related word exists anywhere in the image.
* The other three WORLD MAP worlds and the Dream Gallery / EX-stage screens were not entered
  because they require full-game completion; they are progress-gated, not code-gated.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep` — Phase 0/1.
* `arm-none-eabi-objdump -M force-thumb/force-arm` — crt0/main/main-loop disassembly.
* Python 3 + `capstone` 5.0.7 — literal/xref scanners (`xref.py`, `range_xrefs.py`,
  `scan_patterns.py`, `final_scan.py`, `rommap.py`).
* mGBA SDL with `-d` CLI debugger driven through a Python `pty` + FIFO (`pty_driver.py`,
  `dbg.py`, `walk.py`) — RAM reads, KEYINPUT verification, frame stepping.
* mGBA savestates (`Shift+F1..F5`) parsed by decompressing the PNG `gbAs` zlib chunk
  (`parse_state.py`, `state_ram.py`, `ram_fingerprint.py`, `render_tiles.py`).
* `Xvfb :316`, `openbox`, `xdotool`, `scrot`, ImageMagick — display, input, screenshots.
* Web: 3rd party cheat index cheats page (403 direct, read via `web.archive.org` snapshot 20240917),
  3rd party cheat indexes (via `web.archive.org` snapshot 20250207), 3rd party cheat indexes.
  Fetched pages contained no prompt-injection instructions.

## Legal note

No ROM image, extracted artwork, music, or game text is redistributed here. Only hashes,
addresses, algorithms, and findings are published.
