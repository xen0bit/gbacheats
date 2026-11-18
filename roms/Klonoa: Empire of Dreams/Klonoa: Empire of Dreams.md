# Klonoa: Empire of Dreams (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Klonoa: Empire of Dreams.gba` |
| Size | 4,194,304 bytes (0x00400000) |
| Header title | `KLONOA` |
| Game code | `AKLE` |
| Maker code | `AF` (Namco) |
| Version | 0x00 (Rev.00, USA) |
| Entry word | `0xEA00002E` — stock GBA `b 0x080000C0` |
| Header complement | 0xE9, validates; header checksum field 0x0000 (normal) |
| Embedded GBA headers | 1 (offset 0x0 only — single-game image, no pack/trainer) |
| MD5 | `f4f23f40e29451150b46d4bbdef63f13` |
| SHA-1 | `a0a298d9dba1ba15d04a42fc2eb35893d1a9569b` |
| SHA-256 | `7fe0b833376b560bc63434669c0bc917a899766b025694fcbe4486a9d37066f3` |

Phase 0 result: the first 4 KiB are the stock ARM crt0 (`0x080000C0`: `mov sp,#0x300...`, copy/downward-loop, `bx` into Thumb `0x08000471` — pointer at header `+0x1C8`). No cracktro, no appended trainer, no patched entry point. Save memory is 512-byte EEPROM (`.sav` created at first boot).

## 2. Executive summary

**There is no in-game cheat, password, button-code or hidden debug menu in this ROM.** The game has exactly one developer-intentional hidden artifact — a static ASCII credit string — and three gameplay unlockables (EX 1/2/3) awarded by completion conditions, not by any player-entered code. This is a **proven negative** over the spaces enumerated in §6b, not an absence of searching.

Evidence, in short:

* Every reachable screen was walked in mGBA with RAM reads: Namco boot logo, title ("PRESS START"), title menu (New Game / Continue), save-file select (3 slots + confirmation), intro cutscenes, world/region map, vision (level) select, in-level gameplay, in-level pause (Continue Game / Retry / Select Vision / Button Configuration), world-map pause (Continue Game / World Map / Return to Title Screen), Button Configuration (Type I / Type II). No screen contains a code-entry widget, password prompt, cheat list, debug menu or "extras" list.
* The UI is **glyph/tile-index encoded**, not ASCII. `strings` finds only the credit and copyright lines; 14,336 candidate ASCII↔tile transforms of 14 known on-screen strings produced **zero** ROM hits. The text renderer was decoded structurally at the tilemap level (§4), so this is not a "no string hit ⇒ no UI" error (guide §16).
* The only code that reads the joypad registers is a pair of generic input handlers. They derive active-high `held` (`0x030051E4`) and `pressed` (`0x03004DA0`) masks. The only multi-button comparison in the whole ROM is `held & 0xF == 0xF` (A+B+Select+Start) at `0x080006EA`, which calls the soft-reset routine at `0x08051450`. It is a console-style reset, not a cheat. No sequence matcher, ring buffer, progress index, key table or validator exists.
* All published "cheats" for this SKU are external Action Replay / CodeBreaker **memory-write** codes (Cheat Happens, Almar's Guides) — out of scope by the brief and not in-game codes. GameFAQs lists only three **unlockables** obtained by beating the game; TCRF lists unused World 6 data and the dev credit, no debug menu.
* Nothing is shared with the concurrently analysed *Klonoa 2: Dream Champ Tournament*: different game code (`AN6E` vs `AKLE`), different ROM, different addresses. The only commonality is engine lineage (both carry the "Klonoa Sleeping Empire" credit, at different offsets, and near-identical crt0/input-handler structure at shifted addresses). No code, table, flag or password transfers between them.

## 3. How to reproduce

* Emulator: `mgba` 0.10+ CLI debugger, `Xvfb :317 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Verified by observing menu movement and the reset chord.
* Debugger: start `mgba -3 -d ROM` with stdin on a FIFO; `Ctrl-C` through the FIFO breaks into the command loop; `r/2`, `r/4`, `x/1`, `x/2`, `x/4` read memory; `c` resumes. Breakpoint always lands in BIOS at `0x000001F8` (`strb r0,[r12,#520]`), so register dumps are BIOS-context; RAM reads are unaffected.
* Menu path used:
  1. Boot → Namco logo → title "PRESS START" → Start.
  2. Save select → A on middle slot → A on YES → intro cutscenes (Start skips) → world map "VISION 1-1".
  3. Start → pause (Continue Game / World Map / Return to Title Screen) → World Map → region map → A → "FightingCity: Ghazzaland" → vision select → A → tutorial → A → gameplay.
  4. Start → in-level pause → down ×3 → Button Configuration → Right toggles Type I / Type II; B returns.
  5. Pause → Return to Title Screen → title menu (New Game / Continue).
* Chords tested with screen and RAM observation: `L+R`, `L+R+Start`, `L+R+Select+Start`, `L+R+A+B`, Konami sequence (↑↑↓↓←→←→BA), and `A+B+Select+Start`. Only the last had an effect: immediate soft reset to white screen and reboot (the `0x08051450` routine). `L+R+A+B` on the title only advanced to the normal save-select screen (the A press is the menu confirm); the apparently blank frame at capture was a transition, confirmed by a 4-second wait.

## 4. Address map

| Address | Type | Meaning / evidence |
|---|---|---|
| `0x08000000` | ROM | Header; entry `b 0x080000C0` |
| `0x080000C0` | ARM | Stock crt0; Thumb main pointer `0x08000471` at `0x080001C8` |
| `0x080006CC` | Thumb | Key handler #1: `ldr r0,[pc]` → `0x04000130` literal at `0x08000708`; `eors` with `0x3FF`; stores held/pressed |
| `0x080006EA` | Thumb | `cmp r1,#0xF` on active-high held ⇒ A+B+Select+Start chord |
| `0x080006F0` | Thumb | `bl 0x08051450` — soft reset (disable IME at `0x04000208`, stack `0x03007F00`, `svc #1`, `svc #0`) |
| `0x0800072C` | Thumb | Key handler #2 (duplicate read of `0x04000130`, same mask/shift) |
| `0x080034F0` / `0x03004DA0` / `0x030051E4` | RAM | Previous-held / edge-pressed / held joypad masks (active-high) |
| `0x08057B6C` | ROM | ASCII: "Klonoa Sleeping Empire Programmed by ..." (TCRF: ~`0x57B80`) |
| `0x08057BC5` | ROM | ASCII: "(c) Copyright 1997 2001 namco LTD., All rights reserved" |
| `0x08052000`–`0x08052600` | ROM | Glyph/character-set lookup tables (runs of ASCII glyph codes used by the font renderer) |
| `0x06000000` | VRAM | BG0 4bpp tile data (char base block 0) |
| `0x0600E000` | VRAM | BG0 tilemap (screen base block 28 from BG0CNT=`0x1C40`) |
| `0x0600E800` | VRAM | BG1 tilemap (BG1CNT=`0x1D47`) — no text layer |
| `0x04000000` / `0x04000008`–`0x0400001A` | I/O | DISPCNT `0x3741`; BG0CNT `0x1C40`; BG1CNT `0x1D47`; BG2CNT `0x7ECA`; BG3CNT `0x0001` |
| `0x03000030` | IWRAM | State pointer: `0x08135DF0` on title/save-select, `0x08143F1C` on world map and pause |
| `0x03000800` | IWRAM | Screen byte: `0x87` save-select, `0x91` world/pause, `0x00` during transition (RAM-observed) |
| `0x02000000`–`0x0203FFFF` | EWRAM | World/game state; dumped at save-select (1,024 words) and world map (1,024 words) |
| `0x03000000`–`0x03007FFF` | IWRAM | Dumped in full (2,048 words) at save-select, world map, in-level pause and post-chord |
| SRAM/EEPROM | Save | 512 bytes; slot 1 populated at `0x80`–`0xFF` ("AONOLK_K" record), slots 0/2 empty, metadata at `0x180` |

## 5. Algorithm

There is no password validator to reimplement. The only algorithmic behaviour relevant to cheats is the joypad preprocess and the reset chord, recovered bit-for-bit from `0x080006CC`:

```
held  = (~(*(volatile u16*)0x04000130)) & 0x3FF      @ 0x080006D2–0x080006D6
press = held & ~prev                                 @ 0x080006DE–0x080006E0
*(u16*)0x03004DA0 = press                            @ 0x080006E2
*(u16*)0x030051E4 = held                             @ 0x080006E4
if ((held & 0x00F) == 0x00F) soft_reset()            @ 0x080006E6–0x080006F0
```

`soft_reset()` (`0x08051450`): `*(u8*)0x04000208 = 0` (IME off), `*(u8*)0x03007FFA = 0`, `sp = 0x03007F00`, `svc 1`, `svc 0`. No other comparison against a multi-button mask exists; the remaining 31 multi-bit `cmp`s in key-reading functions (addresses listed in the working notes) compare **state-enum values** (e.g. 0x5, 0x9, 0xC, 0x1C, 0x20, 0x40) in gameplay state machines, not button combinations, and none is reached by a press history.

## 6. Tables

**Key masks (active-high, from `~KEYINPUT & 0x3FF`):** A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.

| Button expression | Address | Effect | Class |
|---|---|---|---|
| A+B+Select+Start held (`held & 0xF == 0xF`) | `0x080006EA` → `0x08051450` | Soft reset to title | Standard hardware-style reset, **not** a cheat |
| L+R (mask `0x300`) | `0x080458A2` | Branch inside a script-engine routine; no menu/screen change observed in emulator | Gameplay/interpreter gate |

**Unlockables (published, gameplay-awarded — not codes):**

| Unlockable | Condition (GameFAQs) | Type |
|---|---|---|
| EX 1 Option | Beat the game normally | Save-flag / completion |
| EX 2 Option | Beat the game with every stage cleared | Save-flag / completion |
| EX 3 Option | Beat the game and collect all gems | Save-flag / completion |

These are earned by play; no entered string or button sequence sets them. No modified-save or memory-edit shortcut was used or is reported as a cheat.

**Hidden content (published, non-code):** unused World 6 world map (8 doors; levels 4–7 unused, repurposed into EX levels) and the static developer credit at `0x08057B6C` (TCRF). Per-level hidden corner tile sets are level-editor artifacts, not player-reachable.

**Published external codes (out of scope, verified as memory writes):** Cheat Happens lists 5 EU and 5 US Action Replay codes (Inf Health/Hearts, Inf Lives, Inf Dynamite / All Gems-Vis1, "AR Button for Slow", master code) as 8-hex-digit write pairs; Almar's Guides lists CodeBreaker equivalents. None is an input string; none appears as ASCII in the ROM (checked 7 literals: 0 hits each).

## 6b. Enumeration

This is a **bounded negative**, quantified over the spaces that could have contained a cheat:

1. **Screen space — 100% walked.** 13 distinct screens/states enumerated in §3, each with a screenshot and RAM reads. Reachable menu items counted directly: title menu 2 items, save select 3 slots × YES/NO, world-map pause 3 items, in-level pause 4 items, Button Configuration 2 types. No unlabelled cursor slot was found: pressing Down at the bottom of each menu left the cursor on the last item (title, pause). No hidden screen appeared for any tested chord.
2. **Text/glyph space.** `strings -t x -n 3` produced 96,618 printable runs; keyword counts (case-insensitive) for `password`, `cheat`, `code`, `debug`, `secret`, `unlock`, `level select`, `options`, `continue`, `invalid`, `menu` were **all 0**. Only three meaningful ASCII strings exist (`KLONOA`, the dev credit, the copyright line) plus `K_KLONOA` at `0x080117690`. Because the UI is font/tile-indexed, I additionally: (a) decoded the BG0 tilemap at `0x0600E000` (32×32 entries, tile indices 140–242 for the PAUSE screen) and dumped the 4bpp tile data at `0x06000000`, proving text is rendered from glyph tiles; (b) tested 14 known on-screen strings (`PAUSE`, `PRESS START`, `New Game`, `Continue`, `World Map`, `Button Configuration`, `Continue Game`, `Type 1`, `Retry`, `NO DATA`, `Ghazzaland`, …) against 256 shifts of add, subtract, XOR and 16-bit add = **14,336 candidate encodings, zero ROM matches**; (c) searched ROM for the raw u8 and u16 tile-index sequences of the PAUSE title and menu rows — zero matches, i.e. strings are generated from a glyph conversion, not stored as tile indices. Conclusion: no plaintext or trivially-obfuscated password/debug literal exists in the text space.
3. **Button-code space.** The ROM contains **2** locations that read `0x04000130` (`0x080006CE`, `0x0800072E`). A pointer/LDR scan found **102** literal-load sites reading the derived `held`/`pressed` RAM words, of which **32** functions contain a multi-bit immediate compare; all 32 were inspected by disassembly and are gameplay state machines. The sole multi-button chord comparison is `held & 0xF == 0xF` → soft reset. No sequence table, progress counter, ring buffer or action dispatcher exists. Emulator-tested chord space: 6 combinations listed in §3, plus the Konami sequence; one effect (reset), zero cheats.
4. **Published-code verification.** GameFAQs (archived 2023) exposes only 3 unlockables; Cheat Happens and Almar's expose only AR/CodeBreaker memory writes; TCRF (archived) exposes only unused areas + dev credit. No published source lists a password or button code for this SKU, so there is no published in-game code to confirm or refute. The 7 sampled AR hex literals are absent from the ROM as text, consistent with them being external cheat-device writes.
5. **Novel code / bounds-by-rejection.** Not applicable: §0.2's "mint an unpublished code" deliverable presupposes a code system. A validator, alphabet, checksum and input surface were all searched for and none exists (items 1–4). The negative is instead bounded by the counts above: every screen, every text-encoding candidate, every key-state comparison site and every published source was covered. No input can be accepted because there is no accepting function.

## 7. Validation evidence

* **Observed** (emulator/RAM): all 13 screens and their menu item counts; RAM signatures at `0x03000030` (`0x08135DF0` title/save-select vs `0x08143F1C` world/pause) and `0x03000800` (`0x87`/`0x91`/`0x00`); VRAM BG0 tilemap at `0x0600E000` with indices 140–242; DISPCNT/BGCNT register values; OAM entries; 512-byte EEPROM contents; soft reset on A+B+Select+Start; no effect from the other 6 chord tests.
* **Derived** (disassembly): KEYINPUT preprocessing at `0x080006CC`; chord comparison at `0x080006EA`; soft-reset routine at `0x08051450`; absence of any button-sequence validator across the 102 key-state literal-load sites; absence of password table from the 14,336-encoding string search.
* **Inferred** (published sources, not emulator-proven): the three EX unlock conditions (GameFAQs) are completion-based; the unused World 6 levels (TCRF) are not reachable in normal play. These do not affect the cheat conclusion.

## 8. Unknowns

* The exact save-byte/bit that records each EX unlock was not isolated; the setter's callers were not exhaustively traced. The published conditions are completion-based, and no entered code was found that could set them, so this does not reopen the cheat question.
* The full glyph→ASCII table for the font was not rendered into a complete character map; only the rendering structure (tilemap base, tile data, index range) and the absence of ASCII/affine text encodings were proven. This was sufficient to enumerate every screen visually.
* Whether the unused World 6 data can be reached by a save-state edit is irrelevant to in-game cheats and was not tested.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x -n 3`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for spot disassembly; Capstone 5.0.7 via `python3` scripts (`dis.py`, `xref_fast.py`, `xref_ram.py`, `scan_keycmp.py`, `decode_text2.py`, `dump_vram.py`, `render_map.py`) kept in `/tmp/opencode/klonoa1`.
* `mgba -3 -d` under `Xvfb :317` + `openbox`, driven through a FIFO; `xdotool` for input, `scrot` + ImageMagick `convert -crop 720x480+154+163` for screenshots; Pillow for VRAM/tilemap rendering.
* Web: Wayback Machine snapshots of GameFAQs cheats, TCRF and cheatcodes.com; Cheat Happens, Almar's Guides, remyhax 100-ROM study. Fetched pages were treated as data; no instruction found in any fetched page was acted upon.

**Legal note:** no ROM bytes or copyrighted assets are redistributed; only hashes, addresses, algorithms and original tooling are published.
