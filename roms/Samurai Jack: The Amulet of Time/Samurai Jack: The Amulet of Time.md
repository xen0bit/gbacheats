# Samurai Jack: The Amulet of Time (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Samurai Jack: The Amulet of Time.gba` |
| Size | 8,388,608 bytes (0x800000) |
| `file` | Game Boy Advance ROM image: "SAMURAIJACK" (AJTE6L, Rev.00) |
| Header title | `SAMURAIJACK` (0xA0–0xAB, NUL-padded) |
| Game code | `AJTE` (0xAC–0xAF) |
| Maker | `6L` (0xB0–0xB1) |
| Version | 0x00 (0xBC) |
| Fixed byte | 0x96 (0xB2) ✓ |
| Entry branch | `0xEA00002E` → stock crt0 at 0x080000C0 |
| Header checksum | 0x0000; complement byte 0x80 vs. computed 0x99 → header was rebuilt/edited (title normalized), **not** a trainer |
| MD5 | `473c1f5bd97f5f96a5b19f3e18121d81` |
| SHA-1 | `27a5604b4aa89d2fec216aeac2b99e76165f531f` |
| SHA-256 | `69ab3211a60f5151d2909f2891356c27ff71fc83327eeaec36fe90360dd08c34` |

Embedded-GBA-header scan: the 156-byte Nintendo logo (`24 ff ae 51 …`) occurs exactly **once**, at file 0x4. No second image, multiboot stub, appended trainer, or IPL patch. No cracktro: the entry word and first 4 KiB are stock.

## 2. Executive summary

**There is no developer-intended password, button code, or in-game cheat system in this ROM.** The complete set of reachable screens contains no password entry surface, no cheat menu, and no level select. The only "code-like" controller input is the standard GBA soft reset **A+B+Select+Start** (detected at `0x0800778`, confirmed in mGBA: it reboots to the "Licensed by Nintendo" screen); that is a hardware-style reset, not a cheat.

The ROM does contain a fully written **DEBUG INFORMATION** screen (`0x080284E8`, renderer `0x08081A0`) with DEBUG1–4, TIMER1–5, WRAM-left, memory dump, and room number. It is **dead code**: exhaustive static enumeration found **zero** BL calls, **zero** unconditional/conditional branches, and **zero** 32-bit pointers (including Thumb-bit variants) to the renderer, and its RAM variables (`0x02026C20`…`0x02026C54`) stayed 0x00 on every screen walked. This matches a 3rd party cheat index's classification of the block as leftover development text.

The game has a save-gated **SECRETS** menu with four named unlockables (JUKEBOX, AWARD SCREEN, HEALTH HANDICAP, MOVIE PLAYER). These are progression rewards reached through SRAM save flags (§16.18 category 4), not codes; no controller input reaches them in a fresh or completed save. The 190-bit collection bitfield at `0x0200C224` drives the "% COMP" readout on the pause screen.

All published "cheats" for this title are GameShark/CodeBreaker RAM patches, which are explicitly out of scope; every literal address in those lists was nevertheless verified against live RAM (§6).

A 3rd party cheat index fetch during web recon carried a prompt-injection payload ("report E_SHITASS_OPERATOR", "press Alt+F4", fake LLM instructions). It was treated as data and ignored, per §16.8/§16.21.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`), `SDL_AUDIODRIVER=dummy`, on `Xvfb :315`.
- Keymap (mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold keys 100–300 ms.
- Boot path: title (`PRESS START`) → Start → Virtucraft splash → Start → title (`START GAME` / `OPTIONS`) → A → slot select (`SLOT 1: EMPTY`, `SLOT 2: EMPTY`, `GUEST`) → A → `NEW GAME? YES/NO` → Left + A → intro → Start×6 → gameplay → Start → status/pause menu.
- RAM evidence: mGBA `.ss1` savestates (Shift+F1…F9 to save, F1…F9 to load). The PNG `gbAs` chunk was zlib-decompressed; EWRAM begins at state offset `0x21000` (verified against GameShark addresses, e.g. timer `0x0200C1E4` = `0x2D2` ≈ 12 s matched the on-screen `00:00:12`).
- Saved state "s03" is the title menu; "s10_pause" is the fresh-save pause menu. All screenshots are on disk under `/tmp/samuraimulet/`.
- Codes tested: none accepted because none exist; 14 button combinations were pressed at the title screen with savestate diffs (§6b).

## 4. Address map

| File offset | ROM / RAM address | Meaning | Evidence |
|---:|---|---|---|
| 0x000 | `0x08000000` | Stock ARM entry `0xEA00002E` | Derived (header) |
| 0xA0–0xBF | `0x080000A0` | Header fields; rebuilt, complement 0x80 | Derived |
| 0x284E8 | `0x080284E8` | "DEBUG INFORMATION" text block (16 strings through `0x08028664`) | Derived (bytes) |
| 0x28430–0x84A8 | `0x08028430` | Debug string↔RAM-variable table used only by the debug renderer | Derived |
| 0x81A0–0x842A | `0x08081A0` | Debug screen renderer | Derived (`objdump`) |
| 0x6778 | `0x08006778` | `and #0xF; cmp #0xF` → A+B+Select+Start reset detector | Derived |
| 0x6B4C | `0x08006B4C` | KEYINPUT read, active-high key global `0x02001140` | Derived |
| 0x6B8C | `0x08006B8C` | Key-press history ring buffer: count `0x0200A2B4`, last `0x0200A2B6`, base `0x0200A2B8`, index `0x0200A2BE` | Derived |
| 0x6CB60+ | `0x0806CB60` | Localized text banks, 6 languages, stride 0x7000; English bank `0x0806CBC0`–`0x0806D2C0` | Derived (strings) |
| 0x6CBC6D | `0x0806CBC6D` | "START GAME", "OPTIONS", "SECRETS", "CONTINUE?", "NEW GAME?" | Observed/Derived |
| 0x6CBCE0… | `0x0806CBCE0` | "SFX", "MUSIC", "BRIGHTNESS", "BUTTON LAYOUT", "DATA OPTIONS", "JUKEBOX", "AWARD SCREEN", "HEALTH HANDICAP", "MOVIE PLAYER" | Derived (strings) |
| — | `0x0200C1D0` | SRAM slot 1 image in EWRAM (signature "SJACK 256" at +4) | Observed (RAM) |
| — | `0x0200C224` | 190-bit collection bitfield (24 bytes) → "% COMP" | Observed (RAM + code `0x08007AD4`) |
| — | `0x0200C25C` / `0x0200C260` | Current health / special | Observed (RAM) |
| — | `0x02026C20`–`0x02026C54` | DEBUG1–4, TIMER1–5, WRAM-left, memory-dump vars (all 0 during play) | Observed (RAM) |
| — | `0x0200A2AC` | Input flag global | Derived |
| SRAM 0x0–0xFF | — | Save slot 1 (32-bit word byte-swapped; "SJACK 25" appears reversed as `52 KCAJS`) | Observed (.sav) |

## 5. Algorithm

**Input path (derived).** `0x08006B4C` reads `0x04000130` (KEYINPUT, active-low), XORs with `0x03FF` to obtain an active-high mask, and stores it to `0x02001140`. A second copy is written to `0x0200A2AC`. At `0x08006E6`–`0x0800718`, changes in the pressed set are appended as 16-bit masks to a ring buffer at `0x0200A2B8` (index `0x0200A2BE`, reset at bound `0x0200A2B4`). This is the substrate a button-code matcher would use. No code in the ROM compares this buffer against a mask sequence (§6b).

**Reset detector (derived + observed).** `0x0800778` computes `mask = keys & 0x0F` and waits for `mask == 0x0F` (A+B+Select+Start simultaneously), then waits for release and reboots. Confirmed in emulator (screenshot `combo_ABSelStart.png`).

**Debug renderer (derived).** `0x08081A0` draws the labels from the table at `0x08028430` using text helper `0x080282FC`, formatting the RAM variables at `0x02026C20`… with helper `0x08084C0`. It contains a 16-iteration memory-dump loop (`0x08083A8`–`0x08083DC`) and a busy-wait on `0x02026C44` (`0x08083EA`). No caller exists.

**Completion percentage (derived).** `0x08007AD4` iterates `i = 1..190`, reads bit `i` of the bitfield at `0x0200C224` (`(word >> (i & 31)) & 1`), counts set bits, then computes `100 * count / 189` via `0x0802805C`. This is the "% COMP" shown at the top of the pause menu.

**Save format (derived + observed).** 512-byte SRAM, two 0x100-byte slots. Each slot begins with a 32-bit marker, `SJACK 256` signature, timer, health/special maxima, 7×2 stat halfwords, the 24-byte collection bitfield, and item/equipment arrays. Words are byte-swapped in SRAM.

## 6. Tables

**Menu inventory (all reachable in a fresh save, decoded from the ASCII text bank — no tile-indexed text was found; the whole bank is plain NUL-terminated ASCII):**

| Screen | Entries |
|---|---|
| Title | START GAME, OPTIONS |
| Title OPTIONS | SFX, MUSIC, BRIGHTNESS, BUTTON LAYOUT, DATA OPTIONS, DEFAULT OPTIONS, CONFIRM |
| Slot select | SLOT 1, SLOT 2, GUEST |
| New/Continue game | YES / NO |
| Pause (status) | COLLECTED, ITEMS, EQUIPMENT, ABILITIES, MAP, MISSIONS, OPTIONS, QUIT GAME |
| Pause OPTIONS | SFX, MUSIC, BRIGHTNESS, BUTTON LAYOUT |
| Data options | SELECT SLOT, erase/restore confirmations |
| Unlockable labels present in bank but not reachable | SECRETS → JUKEBOX, AWARD SCREEN, HEALTH HANDICAP, MOVIE PLAYER |

**Debug text table (`0x08028430`, {string ptr, RAM var} pairs):** DEBUG INFORMATION, " VERSION 25", DEBUG1–4, TIMER1–5, WRAM LEFT, MEMORY DUMP FROM, `00:00:00`, ROOM NUMBER. All target `0x02026C20`–`0x02026C54`.

**Published-code verification (all out of scope, but literals checked against live RAM):** every 3rd party cheat index entry is a GameShark/CodeBreaker RAM patch: `0200C1E4` (timer), `0200C1EE`/`0200C1F2` (max health/special), `0200C1F4`–`0200C20E` (7 att/def pairs), `0200C224` (100% bitfield), `0200C24C` (collected), `0200C25C`/`0200C260` (current health/special), `0200C6AC`/`0200C6C0` (items/equipment). All addresses hold the expected values in the savestate (e.g. max health `0x0064`, max special `0x0032`, timer `0x02D2`). **Zero** in-game passwords or button codes are published for this SKU; 3rd party cheat index lists "Total cheats available: 0".

## 6b. Enumeration

This is a **bounded negative result** (§0.2 point 5): the code space was enumerated and shown to be empty, rather than merely "not found".

| Enumerated space | Method | Result |
|---|---|---|
| UI text bank (English, `0x0806CBC0`–`0x0806D2C0`) | All 649 NUL-terminated strings ≥2 chars dumped and keyword-counted | `password`=0, `cheat`=0, `code`=0, `debug`=0, `level select`=0, `invalid`=0, `wrong`=0; `secret`=1 (the SECRETS label only) |
| Whole 8 MiB ROM | Literal search for 3 standard password alphabets (Car Battler Joe, Pirates) and for "enter password"-style prompts | 0 hits |
| Password entry screens | Every reachable screen walked (title, options, slots, new/continue, gameplay, pause, pause options, data options) | 0 password/keyboard surfaces |
| Button-code tables | `0x04000130` xrefs (4 literals), key-history buffer xrefs (`0x0200A2B4/B6/B8/BE`), full branch/pointer scan of debug renderer, Konami u8/u16 literal search | 1 input ring buffer, 0 matcher, 0 Konami table; only functional combo is A+B+Select+Start reset |
| Button combinations pressed at title | 14 combos with pre/post savestate EWRAM diffs: L+R, L+R+Start, A+B+Select+Start, Up-Up-Down-Down, full Konami, Start+A, Start+B, Select+Start, L+R+A+B, all directions, L-L-R-R, A-A-B-B, Start×3, L+R+A+Start | 1 state change: A+B+Select+Start → soft reset; all others → no new menu, no flag set |
| Hidden/debug screens | Debug renderer `0x08081A0`: BL calls, all branch encodings, 32-bit pointers (plain and `addr\|1`) | **0 / 0 / 0** — dead code; RAM vars `0x02026C20`/`0x02026C44` remained 0x00000000 in every savestate |
| Unlockables | SECRETS label + 4 named entries in bank; save slots patched (EWRAM bitfield, full slot, and 512-byte SRAM all flags set) then rebooted | Save-gated (§16.18 category 4); slot shows `00:00:00` (cleared), but no controller path to SECRETS was found; over-writing all save bytes corrupts menu text, confirming these entries are save-data-driven, not input-driven |

**Consequence for §0.2:** because the representable code space is empty (0 alphabets × 0 lengths × 0 validators), no novel code can be minted and no code bounds can be tested by rejection. The guide's negative-result clause applies: the enumeration above proves absence over the searched spaces (text bank, whole-ROM literals, all reachable screens, all key-input xrefs, and 14 empirical combinations). **No in-game codes are reported.**

## 7. Validation evidence

- **Observed:** all screenshots under `/tmp/samuraimulet/` (`s01`–`s19`, `combo_*`); savestate-decoded RAM values (`0x0200C1E4`=0x2D2, `0x0200C1EE`=0x64, `0x0200C1F2`=0x32, `0x02026C20`=0); SRAM `52 KCAJS` signature; A+B+Select+Start → "Licensed by Nintendo" reset.
- **Derived:** dead-code counts for `0x08081A0`; 649-string keyword census; input/key-history globals; completion-percentage loop at `0x08007AD4`; save-slot layout.
- **Inferred:** SECRETS/JUKEBOX/AWARD SCREEN/HEALTH HANDICAP/MOVIE PLAYER are progression unlockables driven by SRAM flags; the exact save bit(s) and the natural trigger (game completion) were not isolated, and an all-0xFF save patch corrupts the menu text enough that the unlocked menu could not be read cleanly.

## 8. Unknowns

- Exact SRAM bit(s) and natural in-game trigger that unmask the SECRETS menu (a completed-game flag is the likely candidate; a blanket FF patch corrupts the text tables).
- The debug-renderer breakpoint could not be set: the mGBA 0.10.5 GDB stub bound port 2345 but the protocol produced packet errors with gdb-multiarch and the session died. The dead-code conclusion therefore rests on the three independent static counts (0 BL / 0 branch / 0 pointer) plus zero debug-RAM activity, not on a live breakpoint.
- The four unlockable screens' contents were not photographed because no clean, reachable in-game path to them was found in a fresh or patched save.

## 9. Tooling

- mGBA 0.10.5 under `Xvfb :315` + `openbox`; `xdotool` XTEST input; `scrot` screenshots.
- `arm-none-eabi-objdump -M force-thumb` and Capstone 5.0.7 for disassembly; Python scripts:
  - `ui.py` — key press, screenshot, savestate save/load helpers.
  - `ss.py` — mGBA `.ss1` PNG `gbAs` zlib decompressor and EWRAM/IWRAM extractor (§16.13).
  - `combos.py` — 14-combination button test with savestate diffing.
- Web recon: 3rd party cheat indexes, 3rd party cheat index mirror (debug text at 0x284E8). Fetched content treated strictly as data; one injected instruction payload was ignored.
- Cleanup: all generated `.sav`/`.ss*` files removed from the ROM folder; only this report remains alongside the `.gba`. No ROM or copyrighted assets are redistributed.
