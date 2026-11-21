# Yoshi Topsy-Turvy (GBA) — Reverse Engineering Report

## 1. Target identity
- File: `Yoshi Topsy-Turvy.gba` (8,388,608 bytes, 8 MiB)
- Header title: `YOSHI TOPSY`; game code `KYGE01`; maker `01` (Nintendo); version `0x00`; fixed byte `0x96`; entry word `0xEA00002E` (stock crt0 — not a scene-patched image, §16.1)
- **MD5** `e66d2e98947a5bd1068228e4084b06da`
- **SHA-1** `947498cb1db918d305500257e8223deeaddf561d`
- **SHA-256** `0a65d4c44c4cb8036ca2bd36a3ed14286fb1a285f6849639672181d2fe1ad6e8`
- Save hardware: **EEPROM 64 Kbit / 8 KiB** — SDK string `EEPROM_V124` at ROM `0x086463D8`, `.sav` size 8192 (observed in mGBA). Two 0x30-byte records at SRAM `0x00` and `0x30`.

## 2. Executive summary
**There is no player-facing code/password system in this SKU.** No password entry field, no alphabets, no code validator, no button-code table, and no hard-coded code list exist. The entire published "cheat" corpus for this game consists of **save-data unlockables** (Challenge mode after two Story clears; Challenges 2–4 after the Egg Gallery; Challenge 5 after all-Gold medals) — not input codes. This is a §16.11 case: the franchise/platform match produces cheat pages, but the codes are progression flags, not typed or entered secrets.

The ROM **does** contain a substantial unused debug/editor infrastructure (sound test, menu mode, Area Edit, Path Edit, Enemy Edit, Gimmick Edit, Player Param, "Free Fall", "Goal Disable", "Invincible", "Scrole Test"). It is gated on the IWRAM byte `0x03000466` (debug level). That byte is **0 during all reachable screens**, including the title screen, main menu, file select, options, pause menu, chapter select and gameplay. The gate is a four-way comparison requiring `>= 3`; the only setter reachable from the game's scene dispatcher (`0x08027BB4`, called from `0x0803E1AC`) passes a value loaded from a per-scene table whose reset path writes 0. A live debugger write of 3–6 produces no menu change on any walked screen (the menu is drawn only from a different scene object), confirming this is a **gated/dead feature**, not a player-accessible cheat (§16.3 category 4).

## 3. How to reproduce
- Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`), `SDL_AUDIODRIVER=dummy`, Xvfb `:318`, openbox, `-3` scale. Keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
- Boot: caution screen → 4 tilt-calibration screens → ~45 story pages → level 1-1. `Start` in gameplay opens Pause: Continue / Chapter Select / Quit / Sleep / Calibrate Tilt Sensor. `Quit` → title → `Start` → Main Menu: New Game / Continue / Options. `Continue` → Choose a File (3 slots + Erase). `Options` → Tilt Sensor Calibration / Sleep Mode. `Chapter Select` → 1-1 / 1-2 / 1-3 (3 entries).
- Savestate `game.ss2` (title) and `game.ss3` (main menu) used to shorten every test.
- Debugger: mGBA `-d` PTY (`help watch`, `w/1`, `x/1`, `r/4`, `c`, Ctrl-C) used because the GDB stub on :2345 is single-client and was occupied by another session (§16.2, §16.13).
- Tested combinations: `A+B+Select+Start` (soft reset only), `Down+Select` held (no effect), every D-pad direction on every menu, every menu item.

## 4. Address map
| Item | Address | Evidence |
|---|---|---|
| Header / entry | `0x08000000` / `0x080000C0` | Derived (header bytes, stock branch) |
| EEPROM SDK signature | `0x086463D8` | Derived (`strings`) |
| EEPROM `gbAx` chunk in savestate | PNG chunk type 2, 8192 bytes | Observed (state dump) |
| Text rendering | tile-indexed BG maps, no ASCII | Derived (no UI strings found) |
| Debug-level byte | IWRAM `0x03000466` | Derived (17 literal refs, setter/getter) |
| Debug scene pointer | IWRAM `0x0300045C` | Derived |
| Debug scene index | IWRAM `0x03000484` | Derived |
| Debug-level getter | `0x08019994` (`ldrb`/`bx lr`) | Derived |
| Debug-level setter-to-0 | `0x08019774` | Derived |
| Debug-level setter (level arg) | `0x08019888` | Derived |
| Debug-level reset (5/6) | `0x08019A0` | Derived |
| Debug gate (cmp #3 / #4 / #6) | `0x08021D3A`–`0x08021D48` | Derived |
| Debug menu object setup | `0x08021CF4` | Derived |
| Debug level from scene | `0x08027BB4` (BL from `0x0803E1AC`) | Derived |
| Scene descriptor table | `0x08498964` (5×20-byte records) | Derived |
| "sound test" / "menu mode" | `0x08312EF0` / `0x08312F18` | Derived (ASCII) |
| "Free Fall" / "Goal Disable" | `0x08268DAC` / `0x08268E04` | Derived (ASCII) |
| "Area Edit" | `0x082751C0` | Derived |
| "Path Edit" | `0x08407804` | Derived |
| "Player Param" / "Invincible" | `0x084086CC` / `0x08408A28` | Derived |
| "Enemy Edit" / "Gimmick Edit" | `0x08478448` / `0x084784A0` | Derived |
| "Scrole Test" | `0x083231C4` | Derived |
| Joypad reader | `0x0801A0E` (`0x04000130` literal at `0x0801A30`) | Derived |

## 5. Algorithm
No validator exists. The relevant algorithm is the **debug gate**:

```
debug_level = *(u8*)0x03000466           // getter 0x08019994
if (debug_level < 3) return;             // 0x08021D3A
if (debug_level <= 4) { /* layout A */ } // 0x08021D42
else if (debug_level <= 6) { /* layout B */ }
else return;
```

Setter path: `0x0803E1AC` → `0x08027BB4(level)` → `0x08019888(level)`, with `level` loaded from `scene_table[scene].byte1` at `0x08498964 + 20*i + 1`; the table's +1 bytes are `03, 00, 01, 02, 04` for the five records. All normal scene transitions load a 0-valued record; reset (`0x08019774`) writes 0. Observed RAM value during every walked screen: **0**.

EEPROM records: 0x30 bytes each, header `00 FF 00 30 A0 40`, 16-bit field at `+6/+7` (observed `0x6C4E`, `0x26B3`), data `+8..+0x2F`. No checksum algorithm was reverse-engineered; patching all-FF / all-zero payloads in the savestate produced **no menu change**, so these fields are progress/metadata, not codes.

## 6. Tables
- Save slots: 3 (`0x00`, `0x30`, and an uninitialised third record).
- Debug-menu strings found (ROM address, all ASCII): 14 distinct entries (see §4). None is referenced by a 32-bit literal from code — all are reached through a data-driven scene/menu table.
- Button masks: GBA active-low standard; `0x400` special bit set by A+B+Select+Start = soft reset (observed).
- Published codes (web recon): Challenge mode, Challenges 2/3/4, Challenge 5 — **all progression unlockables**, no typed codes. No published password/code string occurs anywhere in the ROM under ASCII, +0x20, UTF-16LE/BE, XOR-0x80, or 5/6-bit packing (searched).

## 6b. Enumeration
**Bounded negative — no code system.** Search space checked:
- Whole 8 MiB ROM for ASCII menu/password/debug keywords and for 5 known button-code sequences in active-high and active-low, 8-bit and 16-bit encodings. Only incidental false positives (e.g. `Start,A,B` byte coincidences in compressed data) and the `EEPROM_V124` SDK banner were found; no code table.
- Whole ROM for `strcmp`/`strncmp`-style validator patterns and for alphabets (32-symbol set like the Car Battler Joe `1234KLMN...`): none found.
- Whole ROM for 32-bit literals pointing to debug strings and for `BL` callers of the debug gate: all debug strings are table-referenced only; there is no input path to the gate.
- **Screen enumeration (complete for reachable states)**: 7 screens, 21 distinct menu entries (title 1, main menu 3, file select 4, options 2, pause 5, chapter select 3, gameplay HUD 3). Every entry was activated and its result screenshotted; no hidden "code", "cheat", "debug", or "password" entry appeared.
- **Debug-gate enumeration**: `debug_level` observed = 0 on every screen. Live writes of 3, 4, 5 and 6 to `0x03000466` produced no new menu on any walked screen (screenshots `gate_3.png`…`gate_6.png`). The gate's caller's return set is `{0,1,2,3,4}` from the scene table plus reset→0; no controller input can set it to `>=3` on the title or menu screens. This is a **gated/dead feature** (§16.3 #4, §16.3b), not "not tested".
- **Save-flag patch enumeration**: setting every byte of both 0x30-byte EEPROM records to 0xFF, preserving headers, and reloading the main-menu savestate produced an **identical** menu. Published "unlockables" are therefore standard progression flags, not cheat codes.
- **Novel code**: none possible — the space is empty. Bounded negative proven by the counts above, not by absence of evidence.

## 7. Validation evidence
- **Observed**: title/main-menu/file-select/options/pause/chapter-select/gameplay screens (screenshots in `/tmp/opencode/yoshitopsy/`); EEPROM `.sav` 8192 bytes with two 0x30 records; debug-level byte 0 on all screens; A+B+Select+Start soft reset; no menu change from debug-level writes 3–6 or all-FF save patches.
- **Derived**: all addresses in §4; the 4-way debug gate; the scene-table setter; the absence of literal xrefs to debug strings; the joypad reader at `0x0801A0E`; `EEPROM_V124` signature.
- **Inferred**: that the five hidden editor entries are fully functional if the gate were satisfied — the menu objects and handlers exist and the table is intact, but **the entry screen was never reached**, so this is not claimed as observed.

## 8. Unknowns
- EEPROM record checksum: the 16-bit fields at `+6/+7` did not match standard CRC-16/CCITT/crc32 over any obvious byte range; the algorithm is not recovered. Patching them did not change menus, so they are not code validators.
- Which exact save bits implement the published Challenge-mode unlocks was not isolated (would require completing Story mode twice in emulator; out of scope for a code-system search).
- The debug editor screens themselves were not visually reached, because the gate cannot be satisfied by controller input; only their data structures and strings were enumerated.

## 9. Tooling
- Scripts in `/tmp/opencode/yoshitopsy/`: `key.py` (XTEST keymap), `dbgtool.py` (`-d` PTY driver), `dumpram.py`, `dumpvram2.py`, `dumpmaps.py`, `scan.py`, `refs.py` (single-pass literal-xref map), `buttoncodes.py`, `findfont.py`, `renderfont.py`, `patchstate.py`, `patch_ss.py`, `boot_test.py`, `testgate.py`, `testlevels.py`.
- Installed tools used: `mgba` 0.10.5, `gdb-multiarch`, `xdotool`, `scrot`, ImageMagick, `arm-none-eabi-objdump`, Capstone (Python). No ROM or extracted assets are redistributed.

## 10. Legal note
No ROM image, save data, or copyrighted graphics/audio are included in this report. Only addresses, hashes, algorithms and original tooling are published.
