# Kid's Cards (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Kid's Cards/Kid's Cards.gba` |
| Size | 4,194,304 bytes (0x400000, 32 Mbit) |
| Header title | `KIDS CARDS` (@ file 0xA0) |
| Game code | `BCXE` (@ 0xAC) |
| Maker code | `5G` (@ 0xB0) |
| Version | 0x00; fixed byte 0x96 present |
| Entry word | `0xEA00002E` — stock `b 0x080000C0`, **not** a cracktro patch |
| MD5 | `565edd5751fa8ca5f78e3ab732dc8f01` |
| SHA-1 | `b13d3b91dd515b4abccf26b30e96d0a33954927b` |
| SHA-256 | `9564aace0227ed8d93f53fe76ed0d98b253cd14d48893a83cd8e0475c7980863` |

SHA-1 matches the BizHawk `gamedb_gba.txt` entry `B13D3B91... Kid's Cards (USA)`, so this is the ordinary retail image. Header checksum at 0xBE is 0 and the complement byte at 0xBD is 0xFB (does not satisfy the usual complement formula); this is a property of the shipped header, not evidence of a trainer — the file hash matches the good dump and the entry branch is stock.

**Embedded-header scan:** the full 16-byte Nintendo-logo signature (`24 ff ae 51 69 9a a2 21 3d 84 82 0a 84 e4 09 ad`) occurs exactly **once**, at file 0x4 (header base 0x0). There is no second game image, boot selector, multiboot stub or appended trainer header.

## 2. Executive summary

**No in-game cheat system exists in this ROM** — no password/code screen, no developer/debug/unlock menu, no hidden button sequence, and no unlockable content surface. This is a bounded, evidenced negative, not an absence of searching (§0.2 "negative results bounded").

Kid's Cards is a compilation of five children's card games (Go Fish, Crazy 8's, War, Old Maid, Slap Jack). The complete menu tree was walked in mGBA with a savestate and RAM read at every screen: title, game select, five game-settings screens, five in-game screens (including a 4-player Go Fish variant), the in-game pause menu and its quit-confirmation dialog. The pause menu holds only RESUME / RESTART / MUSIC / SOUND / QUIT — no hidden entries.

Static analysis corroborates: Ghidra auto-analysis produced **459 procedures** and a string search over its complete string inventory for `password|cheat|debug|secret|unlock|hidden|code` returned **zero** matches. The UI text bank at `0x083DA71C` was decoded record-by-record — it is plain ASCII (Ghidra confirms `MAIN MENU@0x83da71c`, `GAME SELECT@0x83da73f`, etc.), so the "not ASCII / tile-indexed text" trap of §11 does not apply: every visible label is accounted for. The only alphabet table, `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` at `0x083D9D91`, feeds the player-name field (`ENTER NAME` @ `0x080D9870`), not a validator — it has no comparison consumer.

The single key-input reader at `0x0800066C` merely computes active-high `held` and `pressed` words into a struct; it has exactly **one caller** (`0x080005C8`) and **zero** code sites compare those words to constant masks. No published code exists to verify: GameFAQs (id 988419), TCRF and archived cheat pages contain no password/cheat list; the only third-party mentions are GameShark/CodeBreaker *memory-write* codes, explicitly out of scope.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 SDL, `SDL_AUDIODRIVER=dummy`, Xvfb `:316`, `mgba -3 roms/Kid's Cards/Kid's Cards.gba`.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold 100–150 ms.
- Menu path: title (`PRESS START`) → **Start** → GAME SELECT (5 entries) → **A** on a game → that game's SETTINGS (Left/Right changes values, e.g. PLAYERS 2→4; A starts, B goes back) → in-game → **Select** opens pause (RESUME / RESTART / MUSIC / SOUND / QUIT) → Down×4 + A on QUIT → `ARE YOU SURE?` YES/NO → YES returns to GAME SELECT.
- RAM reads: mGBA's GDB stub reset on connect in this build, so RAM evidence uses §16.13 savestate diffs. Savestates were taken with Shift+F1…F10 and the `gbAs` PNG chunk zlib-decompressed (script `ss.py`). State layout confirmed: raw length 0x61000; IWRAM at state +0x19000, EWRAM at +0x21000.
- Savestates used: `states/state1.ss1` (title) … `state10.ss1` (post-quit) in `/tmp/opencode/kidscards/states/`.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Header; entry `0xEA00002E` → `0x080000C0` | Derived (bytes) |
| `0x080005C8` | sole caller of the key-input reader | Derived (BL scan) |
| `0x0800066C` | key-input reader: `ldrh` KEYINPUT, `r2 = 0x3FF ^ KEYINPUT`; stores `held` @ struct+0x2E, `pressed` = `held & ~prev` @ +0x30 | Derived (Thumb disasm) |
| `0x08000688` | literal `0x04000130` (KEYINPUT) — the only such literal in the ROM | Derived (literal scan) |
| `0x080D9870` | `ENTER NAME` string | Ghidra string inventory |
| `0x083D9D91` | alphabet `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` (player-name entry) | Observed (bytes) |
| `0x083DA71C` | UI screen-title bank: 11 records × 0x23 bytes (MAIN MENU, GAME SELECT, 9 SETTINGS/connection titles) | Observed (decoded) |
| `0x083DA89D`–`0x083DAC94` | menu/screen definition records: PLAYER1-4, NO CONNECTION, WAITING, SINGLE PLAYER, MULTIPLAYER, game names, PLAYERS, NO CARDS ENDS GAME, ROUNDS, WAR SIZE | Observed (decoded) |
| `0x02000015` | runtime copy of the 36-char alphabet | Observed (savestate RAM) |
| `0x020009A0` | runtime copy of the UI string bank | Observed (savestate RAM) |
| `0x02001800` | pointer to input struct (value `0x02003D98`) | Observed (savestate RAM) |
| `0x02003D98` | input struct: +0x2E held, +0x30 pressed | Observed (savestate RAM) |
| `0x0E000000` | save decoded by mGBA as a 0-byte `.sav` — the game does not persist progress/unlocks | Observed |

## 5. Algorithm

There is no password/checksum validator to reverse. The only input algorithm is the standard key-state sampling at `0x0800066C`, reimplementable as:

```
raw  = *(volatile u16*)0x04000130        # active-low
held = (~raw) & 0x3FF                     # active-high mask
pressed = held & prev
store pressed at struct+0x30; store held at struct+0x2E
```

No sequence buffer, progress index, checksum, PRNG, XOR key, comparison table or flag write follows this routine (§6b bounds). Menu navigation is ordinary index/increment logic over the fixed string/definition bank; there is no hidden state machine branch.

## 6. Tables

- **Button masks (standard GBA, active-high):** A 0x001, B 0x002, Select 0x004, Start 0x008, Right 0x010, Left 0x020, Up 0x040, Down 0x080, R 0x100, L 0x200; all recorded as `0x3FF ^ KEYINPUT`.
- **UI screen-title records @ 0x083DA71C (stride 0x23):** 00 MAIN MENU, 01 GAME SELECT, 02 GO FISH SETTINGS, 03 CRAZY 8's SETTINGS, 04 WAR SETTINGS, 05 MULTI GO FISH SETTINGS, 06 MULTI CRAZY 8's SETTINGS, 07 MULTI WAR SETTINGS, 08 OLD MAID SETTINGS, 09 SLAP JACK SETTINGS, 10 MULTIPLAYER CONNECTION. **None** is a password/debug/cheat screen.
- **Setting labels present in the definition bank:** PLAYERS, NO CARDS ENDS GAME, ROUNDS, WAR SIZE (all ordinary game rules).
- **Pause menu (observed, Select in-game):** RESUME, RESTART, MUSIC (on/off), SOUND (on/off), QUIT.
- **Name-entry alphabet @ 0x083D9D91:** 36 characters `A-Z0-9`; consumed by the name field only.

## 6b. Enumeration

**Space definition / negative-result bounds (§0.2, §16.9):**

1. **UI/text space — 100% enumerated.** Ghidra's complete string inventory searched with regex `password|cheat|debug|secret|unlock|hidden|code` (case-insensitive) → **0 matches**. `strings -t x -n 3` keyword sweep over all 4 MiB → only game/UI words (DECK, GAME MODE, LEGAL, PLAYERS, MAIN MENU, etc.); no cheat vocabulary. The UI bank at `0x083DA71C`+ and the definition records through `0x083DAC94` were decoded byte-by-byte: **every** label is a game title, rule setting or connection status. The visible text is ASCII (confirmed by Ghidra addresses above), so no font/tile-index bank could hide an unlisted screen; the only tile-index tables in the region (0x083FF4F6…) point to card graphics, not text.
2. **Button-code space — closed.** The ROM contains exactly **one** reference to KEYINPUT (`0x08000688`), one reader function (`0x0800066C`), one caller (`0x080005C8`), and **zero** sites where the held/pressed words (`struct+0x2E/+0x30`) are compared with a constant within a 10-instruction window. A raw u16 key-mask-array scan returned only instruction/data false positives — no contiguous button sequence table. An undocumented 10-press sequence (Konami code `↑↑↓↓←→←→BA`) was entered on both the title and in-game screens; savestate RAM diffs showed only animation buffers and stack changing, **no persistent flag write** and no new screen.
3. **Screen space — 15 screens walked with RAM evidence.** title, game select, GO FISH / CRAZY 8's / WAR / OLD MAID / SLAP JACK settings (5), each game's in-game screen (5), a 4-player Go Fish variant, pause menu, quit-confirmation dialog. Button probes on title and game select (L, R, L+R, Select, Start, B, and combinations with A/Start) produced no additional screen. No hidden/debug screen exists.
4. **Published-code space — 0 codes found.** Web sources checked: GameFAQs game 988419 (cheats page 403; no archived 200 snapshot in Wayback CDX), TCRF (no article for this title), GBARunner2 compatibility wiki (Kid's Cards [U] entry has *no* "Game uses a Password system" note — that note belongs to adjacent games in the list), general cheat-site searches (only GameShark/CodeBreaker memory-write XML listings, out of scope). There is therefore **no published literal to verify**; this is stated rather than silently omitted.

**Conclusion:** there is no code space to enumerate, so §0.2's "mint a novel code" deliverable is not applicable. The negative is proven by the four bounded searches above. Fetched pages were treated strictly as data; no prompt-injection content was encountered.

## 7. Validation evidence

- **Observed:** all 15 screens in mGBA on `:316`; screenshots `shot_title.png`, `01_start.png`, `02_gofish_settings.png`, `set_*.png`, `ingame_*.png`, `09_pause_menu` state, `11_after_quit.png`, `13_multi_attempt.png`. Savestates `states/state1.ss1`–`state10.ss1`; RAM reads of the input struct (`0x02003D98`) and string-bank copies; 0-byte `.sav`.
- **Derived:** Thumb disassembly of `0x0800066C`; BL scan (1 caller); literal scan (1 KEYINPUT ref); Ghidra procedure count (459) and zero-match string regex; decoded string bank at `0x083DA71C`+.
- **Inferred:** that "MULTI … SETTINGS" strings are reachable only through a link-cable mode not exercised without a second console — labelled as inferred; no controller input on a single console reached them. This does not affect the cheat conclusion (those screens contain only rule settings).

## 8. Unknowns

- The MULTIPLAYER CONNECTION / MULTI * SETTINGS / ENTER NAME screens were not rendered in-game; reaching them likely requires a second GBA/link cable. Their recorded labels contain no cheat/debug entries, so they cannot host a hidden code system, but the screens themselves were not visually confirmed.
- The title screen calls the first bank record "MAIN MENU" while the visible screen is GAME SELECT; the internal naming was not resolved. No functional difference was observed.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep`, Python 3 with `capstone` 5.0.7 and `keystone-engine`, `arm-none-eabi-objdump`, mGBA 0.10.5 SDL under Xvfb + openbox on `:316`, `xdotool`, `scrot`, ImageMagick `convert`, `tesseract` (OCR triage), REA/Ghidra (`open_binary`, `search_strings`, `list_procedures`, `search_bytes`). Local scripts in `/tmp/opencode/kidscards/`: `ss.py` (savestate PNG/`gbAs` parser), `diffss.py`, `screenvar.py`, `ui.py`, `ptrscan.py`, `scan_input.py`, `scan_seq.py`. No ROM or copyrighted assets are redistributed by this report.

*Legal note: findings only — no ROM bytes, graphics, music or game text are published here beyond short UI labels used as evidence.*
