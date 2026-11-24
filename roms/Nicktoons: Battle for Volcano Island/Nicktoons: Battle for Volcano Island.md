# Nicktoons: Battle for Volcano Island (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity
- **File:** `Nicktoons: Battle for Volcano Island.gba` (4,194,304 bytes = 0x400000)
- **Header title:** `NICKTOONSBVI` · **Game code:** `BNVE` · **Maker:** `78`
- **Version:** 0x00 · **Fixed 0x96:** present · **Main unit/device:** 0x00/0x00
- **Entry branch:** `0xEA00002E` (stock `b 0x080000C0`, **not** a cracktro patch)
- **Header checksum:** 0x0000, complement 0x1E (normal rebuilt-header artifact)
- **MD5:** `07f3b7415eb3779ff11e51a38d0ad3f8`
- **SHA-1:** `aea4c43253d2a3d03c9d17224ebe2be49cbc95e0`
- **SHA-256:** `6b11d696559fc265c944cce015c7c2d34d4888662733e2f6b08be081db263121`
- **Embedded GBA-header scan:** Nintendo-logo byte pattern occurs **exactly once**, at file `0x4` (header `0x0`). Single-image ROM; no multiboot stub, no appended trainer. Last 4 KiB are all zeros; size is a clean power of two.

## 2. Executive summary
**The GBA build of Nicktoons: Battle for Volcano Island has no in-game cheat system.** There is no password/code-entry screen, no button-code matcher, no hidden debug menu, and no unlockable-by-input surface. The only "cheats"/"passwords" published for this title belong to the **PS2, GameCube and DS** SKUs (5-digit numeric codes in an "Extras → Cheats → Enter Cheat Code" menu); that menu does not exist in the GBA image. The GBA 3rd party cheat index page lists only **gameplay-gated character unlockables** (finish World 1 → Timmy, finish World 4 → Patrick, collect 5 Gold Hearts in every level → Manuel/Angel/Anne/Jessica), which are save-bit achievements, not codes.

This is a **bounded negative result** (guide §0.2): the complete UI-screen asset set, the complete localization text-ID set, the ASCII string space, and the entire raw-input handling library were enumerated with counts; every reachable menu was walked in mGBA with RAM reads; published cross-platform codes were tested against the ROM and found absent; representative button sequences were entered on the title screen and shown by savestate diff to change no persistent flag.

## 3. How to reproduce
- **Emulator:** mGBA (SDL), `SDL_AUDIODRIVER=dummy`, Xvfb `:316`, `mgba -3 <rom>` (the `-g` GDB stub stalls this build at boot; use `-d` or savestates for RAM work).
- **Keymap (mGBA SDL default):** A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold 60–150 ms.
- **Menu path (all screens walked):**
  1. Health & Safety → legal text → title "Press Start" (screenshots `s38`, `s41_fresh_*`, `s42_final`).
  2. Title → Start → **Select A File**: Game 1/2/3, Erase, Options (`s23`, `s25`). Cursor: Up/Down in left column, Right into Options/Erase row.
  3. Options → Music (slider), Sound (slider), Display (Normal), Credits (`s12`, `s13`, `s14`). No Cheats/Extras/Unlock Codes/Level Select entry.
  4. Credits → scrolling name list (`s16`, `s21`); no hidden input.
  5. Game 1 → long intro cutscene (≈300 A presses) → gameplay (`s32`, `s36`).
  6. In gameplay, Start → **PAUSED**: `Continue`, `Quit` only (`s33`, `s37`). Quit → "Are you sure you want to Save and Quit?" No/Yes (`s46`) → returns to title (`s47`). No other pause entries.
  7. Hub-world pause entries exist in the text bank (`PAUSE_WORLD`, `PAUSE_QUIT_HUB`, `PAUSE_QUIT_START`) but are normal navigation options, not cheats.
- **Published codes tested:** `81222 73338 95167 18925 24599` (PS2/GC "Damage Boost/Extra Ammo/Half Power Drain/Invulnerability/Unlimited Power"), `65892` (all salvage), `51367`, `42902`, `Spongebob,Danny,Timmy,Cosmo` (DS unlock). None appear in the GBA ROM in any encoding and GBA has no entry surface.

## 4. Address map
| Item | Address (ROM / RAM) | Notes |
|---|---|---|
| ROM base / header | `0x08000000` / file `0x0` | single image |
| Input state struct | RAM `0x02006D70` | `u16` prev @+0, `u16` current @+2; idle value `0xFC00FC00` (= `~0x03FF`) |
| 10 per-key hold counters | RAM `0x02006D80`–`0x02006DA4` | indexed by key bit 0..9 (A,B,Select,Start,R,L? per GBA bit order) |
| Input poll routine | ROM `0x0804B7E4` | reads `KEYINPUT` literal at `0x0804B814` = `0x04000130`, writes the two state halfwords and 10 counters |
| Key-press edge detector | ROM `0x0804BA1C` | `(prev & mask)==0 && (cur & mask)!=0 → 1` |
| Generic key→action dispatch | ROM `0x0804BA84` | 14-entry jump table at `0x0804BA94`; per-key action getters only |
| Localization text-ID table | ROM `0x03AE000`–`0x03AF95C` | IDs `MENU_*`, `OPTIONS_*`, `PAUSE_*`, `LANGUAGE_*`, `UPGRADE_*`, `CREDITS_*`, `CS*` |
| UI screen scripts (.dts) | ROM file region `~0x19C000`–`0x1B1000` | 21 `interface\*.dts` assets (full list in §6) |
| Save image | `0x0E000000`, 512-byte EEPROM | 3 × 0xA0-byte game slots + global settings at `0x1E0`; each slot begins `00 32 30 30 65 6d 61 67` (ASCII `"emag"`, byte-reversed `"game"`) |

**RAM mapping in mGBA `.ssN` savestates (verified):** decompress the PNG `gbAs` chunk (zlib) → 397,312-byte raw state. IWRAM `0x03000000` at state offset `0x19000` (32 KiB); EWRAM `0x02000000` at `0x21000` (256 KiB). Reading `0x02006D70` from the state returned `0xFC00FC00`, confirming the mapping.

## 5. Algorithm
No password/checksum/button-code algorithm exists. The only relevant routine is the standard input poller:

```
poll_input():
    prev = state[0]                       @ 0x0804B7E8
    state[0] = cur                        @ 0x0804B7EA
    cur = ~(*(u16*)0x04000130)            @ 0x0804B7EC..0x0804B7F2  (active-high keys)
    state[2] = cur
    for keybit in 0..9:                   @ 0x0804B7FA
        mask = 1 << keybit
        if (prev & mask) != 0: counters[keybit]++      @ 0x02006D80+4*keybit
        else: counters[keybit] = 0
```

Followed by generic edge/held/release helpers and a 14-entry key→action jump table. **No code compares a captured press history against a constant sequence**, and **no code reads a password buffer**.

## 6. Tables
- **Localization IDs (complete, no cheat-related entry):**
  - `MENU_TITLE`, `MENU_GAME_1..3`, `MENU_OPTIONS`, `MENU_ERASE`, `MENU_YES`, `MENU_NO`, `MENU_CONFIRM_ERASE`, `MENU_INFO_BAR`, `MENU_INFO_BAR_ERASE`, `MENU_TITLE_ERASE`
  - `OPTIONS_TITLE`, `OPTIONS_MUSIC`, `OPTIONS_SOUND`, `OPTIONS_DISPLAY`, `OPTIONS_LANGUAGE`, `OPTIONS_CREDITS`, `OPTIONS_INFO_BAR`, `DISPLAY_LCD_1/2`, `DISPLAY_TV`
  - `PAUSE_TITLE`, `PAUSE_CONTINUE`, `PAUSE_WORLD`, `PAUSE_QUIT_GAME`, `PAUSE_QUIT_HUB`, `PAUSE_QUIT_START`
  - `LANGUAGE_ENGLISH/FRENCH/GERMAN/ITALIAN/JAPANESE/SPANISH`, `LANGUAGE_SELECT_INFO_BAR_*`
  - `MSG_CORRUPT_FILE_1..3`, `MSG_CORRUPT_GLOBAL`, `MSG_SAVE`, `PRESS_START`, `DOOR_HUB_REJECT`, `UPGRADE_*`, `CREDITS_*`, `CS*`
  - **Absent:** `CHEAT*`, `PASSWORD*`, `EXTRA*`, `UNLOCK*`, `LEVEL_SELECT`, `DEBUG*`, `WARP*`.
- **Complete UI screen script inventory (`interface\*.dts`, 21 files):** `credits\credits_screen`, `healthsafety\hs_{en,fr,gr,it,sp,us}`, `level_end\level_end`, `main_menu\main_menu`, `options\options_screen`, `startup\{halfbrick,legal,nick_games,thq,thq_oz}`, `title\title_{en,fr,gr,it,sp}`. **No cheat/debug/extras/level-select screen asset exists.**
- **Room scripts:** `rooms\1_1_a` … `6_3_a`, `7_u_a/b`, `game_hub`, `intro`, `start` — no hidden bonus/debug room script.
- **ASCII string census (case-insensitive `strings -t x -n 3`):** `cheat`=0, `password`=0, `secret`=0, `debug`=0, `level select`=0, `extras`=0, `unlock`=1 (`UnlockPlayer`, a cutscene script opcode at `0x05D704`), `code`=3 (all `layers\decodeco.*`, a company name "DecodeCo"), `bonus`=7 (all `bonus_bkg` / `6_x_bonus_bkg` background assets), `menu`=87 (all asset paths + localized UI text).
- **Cross-platform published codes in ROM:** all 8 numeric literals and the DS character-password string are **absent** as ASCII, UTF-16, u16 or u32 (the handful of u16 coincidences for `18925`/`24599`/`42902` fall inside compressed graphics at `0x082xxxxx` and are not code).

## 6b. Enumeration
- **Space definition:** There is no password alphabet, no code length, no key-mask sequence table and no hidden-menu entry to enumerate. The input space searched is: 10 active-high key bits → per-key edge/held/release helpers only (input library `0x0804B7E4`–`0x0804BA84`); the entire ROM has **9 pointers to `0x02006D70` and 23 to `0x02006D80`, all inside that one library** (verified by byte scan), so no external sequence matcher exists.
- **Validator model:** N/A (no validator). The 2-byte RAM diff after exhaustive title-screen button sequences contains only a frame timer (`0x02004B8C`: `0x011F` → `0x014D`, +46 frames) and a transient debounce counter (`0x02006DEC`: `0` → `4`); input state resets to `0xFC00FC00` and **no persistent unlock/cheat flag changes**.
- **Novel codes:** None possible — a code system does not exist in this SKU. This is the guide's explicit "no system" branch (§0.2 item 5), not an untested system.
- **Bounds proven by rejection:** Non-existent field values cannot be submitted because there is no entry UI; instead the bound is proven by (a) complete screen/asset/text enumeration showing zero entry surfaces, and (b) dynamic rejection: 40-button sequences (Konami-style Up/Up/Down/Down/Left/Right/Left/Right+B+A, L/R+diagonal variants) entered on the title screen produced **no state change** beyond the frame counter — screenshots `s43_after_codes_title`, states `title_base.ss` / `title_codes.ss`.
- **Published-list closure:** PS2/GC/DS 5-digit codes and DS character password verified against the ROM and rejected as GBA-applicable; GBA 3rd party cheat index list only gameplay unlockables and dev/unused text.

## 7. Validation evidence
- **Observed:** all screens in §3 captured in mGBA on `:316`; title-screen button sequences leave the title unchanged; save file is 512-byte EEPROM with 3 slots; input state read from decompressed savestate RAM.
- **Derived:** complete `.dts`/ID/string inventories prove no cheat UI; input-library disassembly and pointer-count prove no button-code matcher; literal searches prove cross-platform codes absent.
- **Inferred:** the four gameplay-gated characters are stored as save bits (consistent with the 3-slot save layout and 3rd party cheat indexes); exact bit positions were not isolated because the setters require story completion.

## 8. Unknowns
- Exact save-bit indices for the four gameplay-gated characters (require finishing World 1/4 and the 5-Gold-Heart condition; not needed to answer the cheat-system question).
- The hub-world pause screen (`PAUSE_WORLD` etc.) was not photographed because reaching the hub requires story progression; its text IDs are present and are ordinary navigation labels, so it is not a plausible cheat surface.
- The `-g` GDB stub stalls this mGBA build at boot; RAM work used savestate extraction instead.

## 9. Tooling
- `arm-none-eabi-objdump -M force-thumb` for the input library; Python/Capstone 5.0.7; `strings -t x`, `grep -abo`; Python `zlib` savestate `gbAs` decoder (`stateutil.py`, `ctl.py` in `/tmp/nicktoonsvolcano`); `Xvfb :316` + `openbox` + mGBA SDL + `xdotool` + `scrot`.
- Web: 3rd party cheat indexes GBA cheats (archived 2021), 3rd party cheat indexes GBA page (archived 2023), 3rd party cheat indexes GC/PS2/DS pages. Fetched pages were treated as data; no prompt-injection content was encountered.

No ROM or copyrighted assets are redistributed here — only addresses, hashes, and our own observations.
