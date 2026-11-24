# Kirby: Nightmare in Dream Land (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Kirby: Nightmare in Dream Land/Kirby: Nightmare in Dream Land.gba` |
| Size | 8,388,608 bytes (0x800000, 64 Mbit) |
| `file` | Game Boy Advance ROM image: "AGB KIRBY DX" (A7KE01, Rev.00) |
| Header title | `AGB KIRBY DX` |
| Game code / maker | `A7KE` / `01` (Nintendo), version 0x00 |
| Entry word | `0xEA00002E` → stock `0x080000C0` crt0. **Not** a scene-patched/cracktro image. |
| Header checksum / complement | 0x0000 / 0xC1 |
| MD5 | `35ae64b0f27e60107c14ab956f6cdf70` |
| SHA-1 | `37a476567d133c146fee6b5e2eb0b07a215da6b0` |
| SHA-256 | `caa4e11b6102257939297710dc4b49f6cec307de67838b2e7b7627e81b155db8` |

**Embedded GBA headers (Phase 0)**: the 156-byte Nintendo logo occurs at file offsets `0x4`, `0x76B1FC`, `0x76F690`, `0x7954C0`, `0x7C0A4C`. All five headers carry the same title/code (`A7KE`, maker `01`) and the same stock entry word `0xEA00002E`. These are four embedded multiboot images plus the boot image — the implementation of the three link-capable SUB-GAMES (Quick Draw, Bomb Rally, Kirby's Air Grind, each labelled 1M–4M). They are per-title assets; nothing is shared with the separately-analysed *Kirby & the Amazing Mirror* (queue 396) among the surfaces examined here.

No patch, trainer, or appended cheat engine was found.

## 2. Executive summary

**There is no password system, no typed cheat code, and no button-code/sequence system in this GBA game.** Published "cheats" for the GBA SKU are three **gameplay-gated save unlockables** (Boss Mode, Extra Mode, Meta-Nightmare Mode) plus one glitch; a 3rd party cheat index's "debug rooms" require an external GameShark code and are therefore out of scope. Codes widely published for the NES original *Kirby's Adventure* (↑+A+Select for Extra Game, Start+Select for permanent copy ability, etc.) do **not** affect the GBA build — all were tested on live screens and rejected (§6b).

The developer-intended hidden surface that **does** exist is a **GAME SELECT** menu reached by pressing **Start on the FILE SELECT screen** (not on the title screen). It contains four entries: START GAME, SUB-GAMES (three playable minigames), SOUND TEST (MUSIC/SOUND jukebox, track select), and ERASE A FILE (with YES/NO confirmation). Every entry was entered and its effect observed; all are available on a 0%-complete save file, so none is gated.

All on-screen text is font/tile-indexed: an exhaustive `strings`/byte scan of all 8 MiB returned **zero** pure-alphabetic strings of length ≥5, and no English menu literal exists in any ASCII encoding (§6b). The apparent "alphabet tables" at 0x77A120–0x77A330 are **keyboard-row tables** for high-score name entry inside the embedded multiboot images (`pqrstuvwxyz`, `abcdefghijk`, `PQRSTUVWXYZ`, `0123456789:;`, …), not password alphabets.

## 3. How to reproduce

Emulator: mGBA (SDL), `SDL_AUDIODRIVER=dummy`, 3× scale, Xvfb `:319`.
Keymap (verified against gameplay movement): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys 100–150 ms.

1. Boot the ROM → **title screen** (`PRESS START`).
2. Press **Start** → **FILE SELECT** (FILE1/2/3; 3-item ring, Down wraps 3→1).
3. Press **Start** here → **GAME SELECT** (hidden menu, 4 items).
4. Down/Down → **SUB-GAMES** → A → choose a game (Quick Draw / Bomb Rally / Kirby's Air Grind) → A → ONE PLAYER / MULTIPLAYER → A → game starts (Quick Draw title card and level selector confirmed).
5. Down/Down → **SOUND TEST** → Left/Right changes MUSIC/SOUND, Up/Down changes track number, A/B exit back to GAME SELECT.
6. Down/Down/Down → **ERASE A FILE** → A → "WOULD YOU LIKE TO ERASE THIS FILE? YES / NO".
7. With GAME SELECT open, B returns to FILE SELECT; B again returns to title.
8. Starting a file (A on FILE1) plays the intro story and tutorials, then Level 1: Vegetable Valley. **Start during gameplay opens the single-page "About Copy Abilities" help screen** (A or Right dismisses; Start toggles). There is no separate pause menu.

Screenshots and per-screen savestates were in `/tmp/kirbynightmare/shots/` and `/tmp/kirbynightmare/*.ss1`.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Item | File offset / ROM address | Evidence |
|---|---|---|
| Entry branch / crt0 | 0x000 / 0x08000000 | Derived: stock `EA00002E` |
| Key-input routine (reads KEYINPUT, active-high mask) | 0x11DC / **0x080011DC** | Derived: `ldrh` from literal 0x04000130, `eor #0x03FF`, stores current/new keys |
| KEYINPUT literal pool | 0x1228 / 0x08001228 | Derived: bytes `30 01 00 04` |
| Key state (active-high, `~KEYINPUT & 0x3FF`) | RAM **0x0300100C** (u16) | Observed: savestate diff; 0 with no keys |
| Newly pressed keys (`cur & ~prev`) | RAM **0x03000038** (u16) | Derived from 0x080011F4; observed 0 at rest |
| Previous keys | RAM 0x03001EF4 (u16) | Derived |
| Input debounce counter | RAM 0x03001670 | Derived |
| Screen/menu state word | RAM **0x03003AE0** | Observed: title=0, file select=4, game select=1, sub-games=2, sound test=2 |
| Menu cursor (shared) | RAM 0x03003ADC, 0x03003BF8 | Observed: 0,1,2,3 on GAME SELECT; 0,1,2 on FILE SELECT |
| Save signature `"AGB  KIRBY"` | 0xCFE20 / 0x080CFE20 | Derived: written to SRAM; referenced at 0x080B7B02 |
| SRAM access literal 0x0E000000 | main-game hits at 0xD2C7D…0x1005A1 | Derived: many save read/write helpers; `.sav` is 32 KiB |
| Embedded multiboot headers | 0x76B1FC, 0x76F690, 0x7954C0, 0x7C0A4C | Derived: logo scan (Phase 0) |
| Keyboard-row/name-entry tables | 0x77A120–0x77A330 and copies at 0x7A1640, 0x7CD5B0 | Derived: byte dump |
| Font/tile text bank in VRAM | tilemap at VRAM 0x0600F800 (entries `0x8001,0x8002,…`) | Observed: savestate VRAM dump — text is tile-indexed, not ASCII |

### RAM evidence table (u16 reads from savestate `gbAs`, IWRAM at state offset 0x19000)

| Screen | 0x0300100C | 0x03000038 | 0x03003ADC | 0x03003BF8 | 0x03003AE0 | 0x03003AE4 | 0x03001EA4 | 0x03001EC8 |
|---|---|---|---|---|---|---|---|---|
| title | 0000 | 0000 | 0000 | 0000 | 0000 | 0000 | 00BF | 0001 |
| file select | 0000 | 0000 | 0003 | 0000 | 0004 | 00A0 | 032C | 0074 |
| game select | 0000 | 0000 | 0000 | 0000 | 0001 | 0040 | 0371 | 0026 |
| sub-games | 0000 | 0000 | 0001 | 0000 | 0002 | 00C0 | 03DD | 000F |
| sound test | 0000 | 0000 | 0001 | 0000 | 0002 | 0040 | 0409 | 0013 |

## 5. Algorithm

There is no validator/decoder to reimplement. The only algorithmic finding is the input path:

```
; 0x080011DC (per frame)
cur  = ~(*0x04000130) & 0x03FF        ; active-high button mask
new  = cur & ~prev
if cur == prev:
    if --counter > 0: skip latch
    else: latched = cur; counter = reload
else:
    latched = cur
prev = cur
```

Key-mask convention: A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.

Menu dispatch uses the cursor words above (0x03003ADC / 0x03003BF8) and screen word 0x03003AE0; no comparison against any multi-button combination was found in the input consumers (they test single-key bits such as `&0x09`, `&0x0B` in generic "wait for A/B/Start" helpers at 0x08009398, 0x08009866, 0x0800C09E, 0x0800CF42).

## 6. Tables

### 6.1 Hidden GAME SELECT menu (Start on FILE SELECT)

| # | Entry | Description line | Effect (Observed) |
|---|---|---|---|
| 0 | START GAME | PLAY THE GAME | returns to file/start flow |
| 1 | SUB-GAMES | PLAY THE EXTRA SUB-GAMES | opens SUB-GAMES list |
| 2 | SOUND TEST | LISTEN TO YOUR FAVORITE TUNES | opens MUSIC/SOUND jukebox |
| 3 | ERASE A FILE | ERASE SELECTED SAVE DATA | opens YES/NO confirmation |

### 6.2 SUB-GAMES (all available on a 0% save)

| # | Entry | Description | Player modes |
|---|---|---|---|
| 0 | QUICK DRAW | READY... SET... DRAW! | ONE PLAYER / MULTIPLAYER; LEVEL 1/2/3; gameplay confirmed |
| 1 | BOMB RALLY | SWING YOUR PADDLE; HIT THE BOMB! | 1M–4M |
| 2 | KIRBY'S AIR GRIND | JOIN THE RAIL BATTLE IN THE SKIES! | 1M–4M |

### 6.3 SOUND TEST

Modes: MUSIC / SOUND (Left/Right). Track counter starts at 0; Up/Down changes it. A/B return to GAME SELECT. No hidden entry was observed.

### 6.4 Published codes classified (web verification)

Source: 3rd party cheat index cheat page (live 403; fetched via `web.archive.org/web/20241003080557/...`) and 3rd party cheat indexes (via `web.archive.org/web/20250105165234/...`).

| Published item | Source | Verdict for this GBA SKU |
|---|---|---|
| Boss Mode — beat the game once | 3rd party cheat indexes GBA | Save-bit unlockable, gameplay-gated. Not a code. |
| Extra Mode — 100% in Adventure Mode | 3rd party cheat indexes GBA | Save-bit unlockable, gameplay-gated. Not a code. |
| Meta-Nightmare Mode — beat Nightmares on Extra | 3rd party cheat indexes GBA | Save-bit unlockable, gameplay-gated. Not a code. |
| Trick Mr. Frosty (level 1-4) | 3rd party cheat indexes GBA | Glitch, not a code. |
| Random Abilities (2+ swallowed enemies) | 3rd party cheat indexes GBA | Gameplay behaviour, not a code. |
| Debug rooms (Room 149–153), HAL Room | 3rd party cheat indexes | Require **GameShark** codes — out of scope (§ scope). |
| ↑ + A + Select (Extra Game), Start+Select (permanent ability), 30 lives, Sound Test unlock, etc. | 3rd party cheat indexes **NES** / Extra Mode wiki | NES-original codes. Tested on GBA title/file-select: **no effect** (§6b). |
| Extra Mode via ↑+A+Select | wiki snippet, ambiguous edition | Not reproducible on this GBA build. |

No published item supplied a literal to search for in the ROM — consistent with there being no code table. No prompt-injection payload was encountered in the fetched pages; all fetched content was treated as data.

## 6b. Enumeration

**Menu space (complete).** Every reachable screen was walked on the live emulator with screenshots and savestate RAM reads:

title → FILE SELECT (3 files, wrap confirmed) → hidden GAME SELECT (4 items, wrap 3→0 confirmed) → SUB-GAMES (3 items) → Quick Draw → ONE PLAYER → playable title card/levels; SOUND TEST (MUSIC/SOUND, track 0, A/B exit); ERASE A FILE (YES/NO); gameplay → intro story → tutorials → Level 1, plus Start-help page. Total distinct screens/menus enumerated: **10**. No password-entry screen, no debug menu beyond GAME SELECT, and no fourth sub-game were found.

**Text space (bounded negative).** `strings -t x -n 5` on all 8,388,608 bytes: **35,926** lines, of which **0** are pure `[A-Za-z]{5,}`. A byte-level regex for `[A-Za-z]{4,}` found only incidental code/graphic bytes (first at 0x669990). Searches for `PRESS START`, `FILE SELECT`, `GAME SELECT`, `SOUND TEST`, `QUICK DRAW`, `START GAME`, `ERASE A FILE` in plain ASCII, +0x20-shifted and 8 affine byte encodings returned **zero** ROM hits. VRAM dump shows the UI is drawn from a tile-indexed font bank (`0x8001,0x8002,…` tilemap entries at 0x0600F800). The only alphabet-like tables (0x77A120–0x77A330, plus copies) decode to **keyboard rows** for name entry in the embedded multiboot images — not a password alphabet. Therefore the negative "no password screen" is a statement about the entire text/button space, not just ASCII strings.

**Button-code space (bounded negative).** On both the title screen and FILE SELECT, eight multi-button inputs were held 0.6 s from a restored savestate, with screenshot + RAM diff against baseline:

| Combo | Title result | File-select result |
|---|---|---|
| ↑+A+Select (NES Extra Game) | stays title | opens GAME SELECT (Start-path) |
| Start+Select (NES permanent ability) | stays title | opens GAME SELECT |
| A+B+Start+Select | stays title | returns to title |
| L+R | stays title | no change (rejection) |
| A+Select | stays title | opens GAME SELECT |
| B+Select | stays title | returns to title (B = back) |
| L+R+Start | stays title | opens GAME SELECT (Start-path) |
| Konami-style 10-press sequence | stays title | returns to title |

Plus each single button on FILE SELECT (A=start game, B=back, Start=hidden menu; L/R/Select/Up/Down=no menu change). **Undocumented combinations pressed in-game**: `L+R`, `A+B+Start+Select`, `L+R+Start`, and the 10-press sequence — none produced a new screen, code effect, or save-bit change that was not already attributable to A/B/Start. **Bounds by rejection** are therefore demonstrated: combinations lacking Start/B/A do nothing, and the NES-specific combos have no GBA effect.

**Novel code / deliverable.** §0.2's "mint an unpublished code" does not apply because no code space exists. The equivalent deliverables — full branch enumeration and an undocumented input pressed in-game — are provided above. No GameShark/CodeBreaker/memory-edit code is reported, by scope.

**Unlockables.** The three 3rd party cheat indexes unlockables are completion-gated save bits, not reachable by any button/password tested. a 3rd party cheat index's debug rooms are gated behind an external cheat device and are not a developer-intended input path.

## 7. Validation evidence

- **Observed** — title, FILE SELECT, GAME SELECT, SUB-GAMES, Quick Draw, SOUND TEST, ERASE confirmation, gameplay and Start-help in mGBA on :319; screenshots in `shots/`; RAM values in the table above from savestate `gbAs` chunks (IWRAM at state offset 0x19000, EWRAM at 0x21000, state length 0x61000).
- **Derived** — input routine at 0x080011DC and its literal pool; key-state addresses; save signature reference at 0x080B7B02; embedded header bases; tile-indexed text conclusion from ROM scans + VRAM tilemap.
- **Inferred** — that the three unlockables are SRAM bits set by completion routines (consistent with 3rd party cheat indexes and the SRAM helpers at 0x0D2xxx–0x0F0xxx); the exact setter call sites were not isolated. The four embedded images are attributed to the three link-capable sub-games by content and naming, not by a verified loader xref.
- **Negative results** — absence of password system and button codes is bounded by the text and button searches quantified in §6b, not by a failed single search.

## 8. Unknowns

- Exact SRAM bit offsets and setter call sites for Boss/Extra/Meta-Nightmare unlocks (static proof of the gate was not completed; gameplay completion was not performed).
- Whether an additional GAME SELECT item appears after 100% completion (the menu always showed 4 items on a 0% save; the item-count table was not statically isolated).
- Full decode of the main-game font bank into a character↔tile map (the VRAM tilemap was located, but a complete glyph mapping was not generated). This does not change the negative: the text space itself was searched exhaustively in §6b.
- Whether the four embedded images include a fourth unadvertised minigame; three are exposed in the SUB-GAMES UI.
- SOUND TEST's complete track count was not enumerated (the counter is unbounded in the UI; no hidden entry observed).

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd` — Phase 0.
- Python (`scan.py`, `xref.py`, `capstone` 5.0.7, `keystone`, Pillow) — literal/PC-relative xrefs, key-mask scans, VRAM tile rendering.
- `arm-none-eabi-objdump -M force-thumb` — disassembly of input routine and menu helpers.
- mGBA (SDL) under Xvfb `:319` + openbox; `xdotool` XTEST input; `scrot`/ImageMagick screenshots; custom `gba.py` driver.
- `buttonprobe.py` — savestate restore + multi-button combo probe with RAM diff.
- `ram.py` — mGBA `.ss1` `gbAs` zlib-chunk parser for IWRAM/EWRAM reads and diffs (§16.13).
- Web: `websearch`; `webfetch` via `web.archive.org` for 3rd party cheat indexes.
- No ROM or copyrighted assets are redistributed; only hashes, addresses, and original findings are published.

## 10. Cross-check with sibling ROM

The concurrently-analysed *Kirby & the Amazing Mirror* (queue 396, display :315) is a different engine/image. This report's ROM hashes, header, embedded multiboot images, input addresses and menu structure are specific to `A7KE`. No shared code, codes, or save format were observed between the analysed surfaces of the two images; nothing from the sibling was carried into this report.
