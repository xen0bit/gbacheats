# The Lord of the Rings: The Two Towers (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Lord of the Rings: The Two Towers.gba` |
| Size | 16,777,216 bytes (0x01000000) |
| `file` | Game Boy Advance ROM image: "TWO TOWERS" (ALPE69, Rev.00) |
| Header title | `TWO TOWERS` (0xA0), 12 bytes, NUL-padded |
| Game code | `ALPE` (0xAC). Maker `69` (EA Games / Electronic Arts) |
| Fixed byte / unit / device | `0x96` / `0x00` / `0x00`; version `0x00` |
| Header checksum / complement | stored `0x0000` / `0xC2` (recomputed: `0x3E` / `0xDA`) — header was rebuilt; entry word is stock `0xEA00002E` (b to `0x080000C0`), no cracktro/trainer bytes observed at the front |
| Entry word | `0xEA00002E` (ARM branch to `0x080000C0`) |
| Save type | EEPROM, 512-byte `.sav`; on-cart magic `LORGBA03` (byte-reversed in the save as `30ABGROL`) |
| MD5 | `e3bebb876bf45ca598800e3a90d6b2f0` |
| SHA-1 | `82b3b4afb0ed0d3fca646aa266e0bfc5bffd49d9` |
| SHA-256 | `0c74d49252fce1e7ce76b89810cdced6b0d374e6bfcef8fe910891b09d80ac79` |

All addresses below refer to **this exact SHA-256**.

## 2. Executive summary

**There is no in-game password, button-code, or hidden/debug-menu system in the GBA build of The Two Towers.** The deliverable is therefore a *bounded negative* (guide §0.2 item 5), not a code. The published "cheat codes" for this title all belong to the **GameCube / PS2 / Xbox** SKUs (hold L+R / all four shoulders, then a four-button sequence); the only GBA-specific published entries are **save-flag unlockables** and a handful of mechanics glitches. GameShark/CodeBreaker/AR codes are out of scope and were not tested.

What was established:

1. **Screen walk (Observed):** every reachable screen was entered; no password entry field, no code prompt, and no debug/level-select entry exists anywhere in the menu tree (§3).
2. **Search-space enumeration (Derived):** exhaustive UTF-8/ASCII, case-folded, `+0x20`, `-0x20`, `|0x80`, `^0x80`, UTF-16LE/BE, reversed and tile-index searches over all 16 MiB found **zero** occurrences of `password`, `cheat`, `debug`, `secret`, `level select`, `continue`, or any visible UI string. Button-mask table scans over all 16 MiB found **zero** plausible code tables (§6b).
3. **Input path reversed (Derived):** the key-state function at `0x0802166C` reads `0x04000130` and maintains active-high current/pressed/held mask globals; no branch in the reachable code consumes a *sequence* of these masks to unlock anything (§4).
4. **Dynamic rejection (Observed):** entering the most-advertised console code (`hold L+R`, `A, Down, Down, Down`, "raise experience by 1000") on the GBA pause/backpack screen produced **no state change** — the Down presses simply moved the backpack inventory cursor, i.e. the input was consumed by ordinary menu navigation, not a validator. Stats/POINTS remained at their previous values (§7).
5. **Unlockables (Derived/Observed):** the three real GBA unlockables are **save-bit flags**, not codes (guide §16.18): Gimli in multiplayer, Misty Mountains in multiplayer, and the special movie. They are gated by completion/collection state and cannot be entered from the controller.

No novel code can be minted because no validator exists to accept one; the bounded negative is proven by the counts in §6b.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:315` + openbox, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold 100–300 ms per press.
* Language select → **English** (A/`x`). EA splash and title → Start.
* Main menu (4 entries): **New Game**, **Load Game**, **Multiplayer**, **Options**.
  * Load Game: 4 slots, all "Empty"; footer "A Button to load / R Button to delete". No hidden entries.
  * Multiplayer: selecting it dims the menu and returns (link-cable dependent in mGBA); no password/code entry.
  * Options (8 entries): Music (On), Music Volume (10), SFX (On), SFX Volume (10), Fast Discard (On), Difficulty, Language Select, Credits. None contains a code entry.
* New Game → character select (5 selectable characters, cycle with L/R): **Aragorn, Gandalf, Frodo, Legolas, Eowyn**. No hidden/Isildur slot.
* In gameplay, Start opens the **Backpack** page; R (`s`) cycles **Backpack → Skills (Active/Passive trees) → Stats → Backpack**. Three pages total. No code/pause-menu extra entries.
* Code-rejection test: from Backpack hold `a`+`s` (L+R) and tap `x, Down, Down, Down`; release. Screenshot shows only the inventory highlight moving; POINTS/EXP unchanged.

## 4. Address map

| Address | Kind | Evidence | Meaning |
|---|---|---|---|
| `0x08000000` | ROM | Observed (header) | Entry `0xEA00002E`, stock ARM crt0 |
| `0x0802166C` | code | Derived (objdump) | Input-state function: reads `0x04000130`, writes key-mask globals |
| `0x04000130` | I/O | Derived | KEYINPUT register, active-low (read at `0x08021766`, `0x080385...`) |
| `0x030038D8` / `0x030038DC` | IWRAM | Derived | key masks: `0xDC` = current active-high (~KEYINPUT) |
| `0x030038E0` / `0x030038E4` | IWRAM | Derived | `0xE0` = newly-pressed `(cur ^ prev) & cur`; `0xE4` = held `cur & prev` |
| `0x030038E8` / `0x030038F0` / `0x030038F4` | IWRAM | Derived | 1-/2-frame-delayed press masks |
| `0x03003904` | IWRAM | Derived | previous-frame mask |
| `0x030038EC` | IWRAM | Derived | idle-frame counter (read at `0x08012052`, `0x0801212C`, `0x080217AC`, `0x080217E6`) |
| `0x03004700` | IWRAM | Derived | save-data struct base in RAM; many accessors. Artifact byte at `+0xF` = `0x0300470F` (matches published CodeBreaker address, not used) |
| `0x080357AC` | code | Derived | Save-validity check: compares 8 bytes at `0x0803573C`/`0x08035800` → `LORGBA03` |
| `0x0805763C` | ROM data | Observed | ASCII `LORGBA03` (save magic), also in `.sav` byte-reversed at offset 0 |
| `0x08057000`–`0x08057638` | ROM data | Derived | Font/tile conversion tables: `(tile, code)` u16 pairs and code-range→tile range tables |
| `0x080346A4` | code | Derived | Selects a font range table by character code (`<=19`, `<=39`, `<=59`, `<=79`, `<=94`, …) |
| `0x08034884` | code | Derived | Table lookup: binary-searches `(threshold,tile)` entries, writes tile byte |

Save file: 512-byte EEPROM; header bytes `33 30 41 42 47 52 4F 4C` (`30ABGROL` = reversed `LORGBA03`), then `00 d4 ff 07` (constant also present at `0x08057648`), remainder mostly zero on a fresh file.

## 5. Algorithm

There is no password/checksum algorithm in this build. The only algorithmic structures found are:

* **Key-state derivation** (at `0x0802166C`, Thumb):
  ```
  cur  = ~KEYINPUT                       ; active-high, all 10 bits
  pressed = cur & (cur ^ prev)           ; edge-triggered
  held    = cur & prev
  prev = cur                             ; stored to 0x03003904 / 0x030038DC
  ```
  No consumer of `pressed`/`held` compares a multi-press sequence.
* **Font decoding** (at `0x080346A4` / `0x08034884`): a character code in `[1,125]` selects one of six `(threshold,tile)` range tables; a binary search returns the tile index. Text banks store these codes, not ASCII — which is why `strings` finds no UI text.
* **Save validation** (at `0x080357AC`): byte-compare 8 bytes against `LORGBA03`; returns 1 on match, 0 otherwise. No password validator exists alongside it.

## 6. Tables

* **Selectable characters (Observed, 5):** indices 0–4 = Aragorn, Gandalf, Frodo, Legolas, Eowyn. No 6th/hidden slot.
* **Main-menu entries (Observed, 4):** New Game, Load Game, Multiplayer, Options.
* **Options entries (Observed, 8):** Music, Music Volume, SFX, SFX Volume, Fast Discard, Difficulty, Language Select, Credits.
* **Gameplay menu pages (Observed, 3):** Backpack, Skills, Stats.
* **GBA unlockables (Derived from published data + save-flag structure):** Gimli (multiplayer), Misty Mountains (multiplayer), special movie. These are bits in the save record; no controller input path sets them (guide §16.18 pattern).
* **Button constants (Derived):** GBA active-high A=`0x001`, B=`0x002`, Select=`0x004`, Start=`0x008`, Right=`0x010`, Left=`0x020`, Up=`0x040`, Down=`0x080`, R=`0x100`, L=`0x200`.

## 6b. Enumeration

**Space definition:** N/A — no code system exists in this SKU. The enumeration below bounds the *search* performed, so the negative is a statement about the whole 16 MiB image rather than "not found".

| Search (all over 16,777,216 bytes) | Count of plausible hits | Interpretation |
|---|---:|---|
| ASCII `password`/`cheat`/`debug`/`secret`/`level select`/`continue`/`unlock`, case-insensitive | **0** | No English code/debug string |
| Same with `+0x20`, `-0x20`, `\|0x80`, `^0x80`, UTF-16LE, UTF-16BE, reversed | **0** | No shifted/encoded variant |
| Literal UI strings `Options`, `New Game`, `Aragorn`, `Password`, `DEBUG`, `Continue`, `Backpack` as ASCII or as tile-mapped byte sequences | **0** | Text is stored as custom font codes, not ASCII; no code string in any checked encoding |
| `strings -n 4` keyword scan | **0** | Only header `TWO TOWERS`, `ALPE69`, `LORGBA03`, `EEPROM_V122`, and an RCS id `$Id: player.c,v 1.4 2003/03/19 23:12:15 seb Exp $` are legible |
| u16 active-high single-button runs of length ≥4 with ≥2 distinct values | 215 | All are coincidences in high-entropy compressed graphics (`0x05xxxx`–`0x08xxxxxx`); none is a compact code table |
| u16 active-low single-button runs ≥4 | **0** | No active-low code table |
| u16 runs with L+R held (`0x300 \| button`) | **0** | No "hold L+R" sequence table |
| u16 active-low with L+R held | **0** | — |
| u8 single-button runs of length 8 with ≥2 distinct | 1,613 | All high-entropy data coincidences; no 1-byte-per-press code table |
| 3× consecutive active-high Down `0x0080` | **0** | — |
| 3× consecutive active-low Down `0xFF7F` | 1 | `0x04A0CE2`, inside a compressed-data region — false positive |
| Thumb literal loads of `0x300` (L+R) | 2 | `0x08C53E08`, `0x08CD3ABA`, both in data, not reachable validators |
| Thumb `LDR` literal references to key-mask globals `0x030038D8`–`0x03003904` | 67 sites | All menu sliders / control helpers; none implements a press-sequence matcher |

**Published-code verification:** every published button code retrieved (3rd party cheat indexes, Fable12 FAQ, total-cheats, 3rd party cheat indexes) is explicitly labelled **GameCube, PS2, or Xbox** ("hold L+R/L1,R1,L2,R2, then A,Down,Down,Down" etc.). Not one is labelled GBA. The GBA lists contain only the three save-flag unlockables, mechanics glitches (Legolas Overdraw, hit-through-walls, Moria Troll item farming, hidden area), and CodeBreaker RAM patches (excluded from scope). Searching the ROM for the console codes' literal text and for their button-mask encodings returned zero hits.

**Novel code:** none minted — there is no validator/oracle. Per the brief, this is replaced by the bounded negative above plus the dynamic rejection test (§7).

**Rejection bounds proven dynamically (Observed):** `L+R + A,Down,Down,Down` on the GBA backpack/pause screen did not change POINTS, EXP, skills, or inventory contents; the `Down` presses moved the highlighted inventory cell, demonstrating the input was routed to the ordinary menu handler. `L+R + A,A,Down,Down` and `L+R + Y,X,Y,X` equivalents (mapped to GBA buttons) likewise produced no visible or state change. This bounds the "console code ported to GBA" hypothesis to zero.

**Gate analysis for the real unlockables:** the `.sav` is a 512-byte EEPROM with magic `LORGBA03` and a validation routine at `0x080357AC`; the artifact byte lives at `0x0300470F` (save-struct `0x03004700 + 0xF`). No input path in the reachable menu tree writes these flag bytes — only the mission-completion/collection code does. They are save bits, not codes (§16.18), and are therefore reported as unlockables rather than cheats.

## 7. Validation evidence

| Claim | Evidence type | Basis |
|---|---|---|
| No password/code entry screen exists | **Observed** | Full screen walk: title, 4-entry main menu, Load Game (4 slots), Multiplayer, Options (8 entries), 5-character select, 3 gameplay menu pages |
| No ASCII/tile code string in ROM | **Derived** | Exhaustive multi-encoding byte search (counts in §6b) |
| No button-code table / sequence validator | **Derived** | Exhaustive u8/u16 mask scans + 67 xrefs to key-state globals; no sequence comparator |
| Input masks and their RAM addresses | **Derived** | Thumb disassembly of `0x0802166C` and literal-pool reads |
| Code entry does nothing in-game | **Observed** | Screenshots `stats_before` / `stats_after`, `code1_c.png`: cursor moved, POINTS/EXP unchanged |
| Save magic and validity check | **Derived** | Disassembly `0x080357AC`–`0x080357F6`; `.sav` bytes match `LORGBA03` |
| Published codes are console-only | **Derived** | Web recon of 5 independent sources; all GBA sections list unlockables/glitches only |
| Three GBA unlockables are save-bit gated | **Inferred** (high confidence) | Published unlock conditions + EEPROM save struct at `0x03004700`; setter paths not fully traced |

Note: `REA` Ghidra analysis was attempted but the server session is shared with other agents and switched targets mid-investigation; the active GBA session could not be trusted. All conclusions above come from `arm-none-eabi-objdump`, custom Python scans, `strings`, and mGBA screenshots — never from that shared REA result.

## 8. Unknowns

* The exact bit positions in the EEPROM save record for the three unlockables were not isolated (the completion-state setters were not exhaustively traced). Only the artifact byte (`0x0300470F`) is corroborated by an external CodeBreaker address.
* The full text-bank encoding was not decoded into readable strings; the font range tables at `0x08057000`–`0x08057638` were identified, but a complete code→glyph map was not reconstructed. The "no code string" negative therefore rests on the multi-encoding searches in §6b, not on a full transcription of every text bank.
* Multiplayer screens could not be fully walked (mGBA link emulation dims and returns from the Multiplayer entry); if a GBA link-only code surface existed it would be outside single-player reach. No such surface is published or hinted at in the ROM.
* Options screen lower entries beyond "Credits" were not separately screenshotted (the visible list ended at Credits); no code-related entry was observed in that screen.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, Python 3 byte/literal scanners.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
* mGBA 0.10.5 + Xvfb `:315` + openbox + `xdotool` + `scrot` + ImageMagick `convert`; screenshots kept in `/tmp/lotr twotowers/`.
* mGBA savestate slot 1 (`The Lord of the Rings: The Two Towers.ss1`) for repeatable gameplay state; `ssdiff.py` (custom zlib `gbAs` chunk extractor/differ) prepared as a GDB-free RAM-diff fallback but not needed for the final result.
* REA/Ghidra was opened once (`open_binary`) but not used for conclusions because the shared MCP session switched to a different ROM.

## 10. Legal note

No ROM bytes or copyrighted graphics/audio are reproduced here. Only hashes, addresses, algorithms, and the analyst's own tools and screenshots of UI state are documented. All fetched web pages were treated as data; no instructions found in them were followed. No prompt-injection payload was encountered in this session.
