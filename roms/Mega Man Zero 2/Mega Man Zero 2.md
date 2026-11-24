# Mega Man Zero 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mega Man Zero 2/Mega Man Zero 2.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `MEGAMANZERO2` |
| Game code / maker | `A62E` / `08` (Capcom) |
| Software version / fixed byte / complement / checksum | `0x00` / `0x96` / `0x93` / `0x0000` |
| Entry word | `0xEA00002E` (stock `b 0xC0`; **not** a cracktro-patched entry) |
| MD5 | `182363b0698322e1864ced6e9eed7ead` |
| SHA-1 | `c4d93a58f0f82c526dec8a3fdbda170336303689` |
| SHA-256 | `4bb8b71ca8d50b5a8f0c737082d8f86c9ad31bd0abebddfa519b3af1ff3853a5` |

Phase 0: a 156-byte Nintendo-logo scan over the whole image found **one** GBA header, at file `0x0`. The image is exactly 8 MiB, so there is no appended trainer; the zero header checksum is the normal rebuilt-header artifact and the complement byte `0x93` is intact (§16.1). This is the USA retail image, not a multi-game pack or a patched release.

## 2. Executive summary

This game has **no password/code-entry system and no on-screen password keypad**. The only ASCII text banks in the ROM are the stage-name table (`0x080FF960`), the "YOU GOT …EC" messages (`0x080FF92C`) and the font/tile-index tables (`0x080FFB34`, `0x080FFC30`). Every visible menu label is font-index encoded and was decoded by driving the real screens (§9.4 of the guide). An "ENTER PASSWORD" screen observed early in this session belonged to a *different* emulator on the shared display (see §3) and is not present in this ROM under any searched encoding.

What the game does have:

1. **A title-screen button gate at boot** (`0x080007BE`): holding **A+B+Select+Start** (active-high mask `0x000F`) while the game boots writes two IWRAM debug flags through `0x0800113C`. This combination is *not* in any published cheat list found (a novel, verified combination — §6b).
2. **A hidden debug level-select menu** gated by EWRAM byte `0x0202F8E1 == 9` plus **L+R** in gameplay (TCRF publishes the byte-poke form; the in-game screen was reproduced here by patching that byte in a savestate and pressing the real buttons). It enumerates 17 destinations.
3. **A family of developer menus** selected by that same byte (`0x0202F8E1`): 1 = data pick, 5 = option/status, 8 = warning, 9 = level select, 10 = hard-mode hint, 11 = save menu. Values outside the accepted set produce no menu (bounds proven by rejection).
4. **Published title cheats (Hard mode / Gallery)** are real but gated by save flags: the game's own hidden hint text says *"To play the HARD mode, Save Game-clear data, then hold L Button down when you choose NEW GAME."* With a non-cleared save file, `L+Start` on NEW GAME opens the data-load menu and `L+R+Select+Start` is rejected (normal title screen remains).

All GameShark/Action Replay/CodeBreaker codes found on the web are out of scope and were **not** used as evidence.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `mgba -3 <rom>`, `SDL_AUDIODRIVER=dummy`, display `:319` (see Note below). Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows; hold 100–300 ms.
* Cold-boot four-button gate: with the ROM starting, hold `x`+`z`+`BackSpace`+`Return` (A+B+Select+Start) until the intro finishes. Read IWRAM flags at `0x03002A68` (savestate raw offset `0x1BA68`): a plain boot gives `04 01 02 02`, the code boot gives `02 01 04 00` — the two flag slots written by `0x0800113C` change.
* Debug level select: reach gameplay, save a state, change the `gbAs` chunk byte for EWRAM `0x0202F8E1` (state raw offset `0x508E1`) from its running value to `0x09`, reload the state and press **L+R**. The level list appears; Up/Down move the cursor, A launches the destination.
* Menu-byte enumeration: repeat the above with other byte values and press L+R; accepted values and screens are listed in §6.
* Title cheats: with save data present, highlight NEW GAME and try `L+Start` (opens "Pick data to load?") and `L+R+Select+Start` (no effect without cleared-hard-mode data).
* **Display note:** Xvfb `:319` was already running from another session and could not be started by this job; only this job's mGBA window (tracked by PID, obtained with `xdotool getwindowpid`) was focused and driven. A *second* mGBA on `:319` (a He-Man GBA game, PID 902994) was never touched. The "ENTER PASSWORD" screenshot captured before this was diagnosed came from that other game's window; inspecting `/proc/*/cmdline` and `/proc/*/environ` for every mGBA process proved it was not from this ROM. No other display was accessed.

## 4. Address map

All ROM addresses = `0x08000000 + file offset`.

| Address | Kind | Meaning |
|---|---|---|
| `0x08000000` | header | stock entry branch `0xEA00002E` |
| `0x080007BE`–`0x08000824` | code | boot-time button gate (A+B+Select+Start) |
| `0x0800113C` | code | sets one byte of the debug flag table at `0x03002A68 + idx*24` |
| `0x08001FC4` / `0x08001FE4` | code | joypad read/edge-detect routines; read `0x04000130` via literal at `0x08002074` |
| `0x080FF92C` | data | ASCII `YOU GOT 20EC` / `YOU GOT 100EC` |
| `0x080FF960` | data | ASCII stage-name table: `STAGE 01 OPENING` … `STAGE 10 YGGR-DRASILL`, `COMMANDER ROOM` |
| `0x080FFB34`, `0x080FFC30` | data | font/tile-index conversion tables (12 columns per row) |
| `0x02000D10` | RAM | input struct: `+0` held, `+2` previous, `+4` pressed edges, `+0xA…` per-key hold counters. Active-high bits: A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200 (verified by holding each key and diffing savestates) |
| `0x0202F8B4` | RAM | title-menu cursor: `0` = NEW GAME, `2` = GAME LINK (observed 0→2→0) |
| `0x0202F8E1` | RAM | developer menu selector; `9` + L+R opens level select |
| `0x03002A68` | RAM | debug flag table, 24-byte stride; two slots written by `0x0800113C` |
| `0x0E000000` | SRAM | 32 KiB save; slot 1 written as magic `49 4e 54 49` ("INTI") + `1B 01 …` after the in-game save |

## 5. Algorithm

Boot gate (derived from `0x080007BE`–`0x08000824`):

```
if byte[0x02000D40] == 0 and (word16[0x02000CA2] & 1) == 0:
    held = word16[0x02000D10]          # active-high low 10 bits
    if (held & 0x0C) == 0x0C and (held & 0x01) and (held & 0x02):
        pressed = word16[0x02000D14]
        if (pressed & 0x0C) or (pressed & 0x01) or (pressed & 0x02):
            call 0x0800113C(0)         # debug flag slot 0 = 1
            call 0x0800113C(1)         # debug flag slot 1 = 1
            call 0x080DFBC0(0x0202F680, 1)
            call 0x08001064(0, 0x0800051D)
```

Debug menu dispatch (observed dynamically):

```
if L_held and R_held:                 # gameplay, L+R = 0x300
    switch byte[0x0202F8E1]:
        1 -> data-pick prompt; 5 -> option/status; 8 -> restart warning;
        9 -> level select; 10 -> hard-mode hint; 11 -> save menu;
        other -> no menu
```

Title codes (game's own hint text, value 10 of the debug menu):
`game-clear save data` is the gate; with it, holding `L` while choosing NEW GAME selects Hard mode. The published Gallery recipe (`L+R+Select` then Start, or `L+A+Select`) is gated by clearing Hard mode; both were rejected on this non-cleared save (§6b).

## 6. Tables

Input masks (active-high, verified by savestate diffs of `0x02000D10`):

| Button | bit |
|---|---|
| A | 0x001 |
| B | 0x002 |
| Select | 0x004 |
| Start | 0x008 |
| Right / Left / Up / Down | 0x010 / 0x020 / 0x040 / 0x080 |
| R / L | 0x100 / 0x200 |

Developer menu selector `0x0202F8E1` (all values 0–15 tested with L+R in gameplay):

| Value | Observed screen |
|---:|---|
| 0 | none (gameplay) |
| 1 | `Pick data to load?` (save slots) |
| 5 | Option/status (`… LEVEL F … HARD MODE … CRYSTAL … PLAY TIME`) |
| 8 | restart warning (`… RESTARTS GAME? BUT THE GAME …`) |
| 9 | **Level select** |
| 10 | hint: `To play the HARD mode, Save Game-clear data, then hold L Button down when you choose NEW GAME.` |
| 11 | `OK to Save the current data? YES NO` → `To which file?` (6 slots) → `Data has been saved.` |
| 2,3,4,6,7,12,13,14,15 | none |
| 16,17,20,32,64,128,255 (sample) | none |

Level-select entries (17, from the rendered screen and the ASCII table at `0x080FF960`): `STAGE 01 OPENING` (off-screen above the visible window), `STAGE 02 JUNGLE`, `03 ICE`, `04 BOMBER`, `05 PLANT`, `06 TRAIN`, `07 JUNGLE2`, `08 ICE2`, `09 BOMBER2`, `0A PLANT2`, `0B NA-OLD2`, `0C NA-OLD1`, `0D NA-1`, `0E NA-2`, `0F NA-3`, `10 YGGR-DRASILL`, `COMMANDER ROOM`. Selecting COMMANDER ROOM loaded its gameplay room (observed).

Published codes checked: all web-listed GameShark/Action-Replay/CodeBreaker entries are memory-edit cheats and are out of scope. The button codes were verified as gated (above). No published *password* literals exist to test — `grep` for `PASSWORD`, `GALLERY`, `DEBUG`, `ENTER`, `HARD` in the ROM returned zero hits in every encoding tried (ASCII, `+0x20`, UTF-16LE/BE, UTF-32).

## 6b. Enumeration

* **Space defined.** The developer-menu space is the 8-bit value at `0x0202F8E1` (256 possible values) crossed with the L+R button condition. All 16 low values were exercised in the emulator, plus a sample of high values (16, 17, 20, 32, 64, 128, 255). Exactly six values open a screen (1, 5, 8, 9, 10, 11); every other tested value is rejected with no menu. The level-select list itself was enumerated completely: 17 destinations, of which STAGE 01 is not rendered by the menu window (cursor can wrap to it).
* **Novel combination (not on any published list).** The boot-time **A+B+Select+Start** gate at `0x080007BE` was found statically and pressed on a real cold boot. RAM proof: IWRAM debug flags at `0x03002A68` changed from `04 01 02 02` (plain boot) to `02 01 04 00` (code boot). No GameFAQs, VGChartz, TCRF or wiki page found lists this four-button boot code.
* **Bounds proven by rejection.** (a) Menu values 16/17/20/32/64/128/255 and 0/2/3/4/6/7/12–15 produced no menu. (b) `L+R+Select+Start` on NEW GAME left the title menu unchanged on a non-cleared save. (c) `L+Start` on NEW GAME with no save data started a normal game, while with save data it opened the data-load menu — both observed, showing the save-data gate. (d) The boot gate's own conditions were enumerated in code: omitting A, B, Select or Start fails the `held` test; a cold boot with only L+R did not change the flags.
* **Validator as oracle (§16.19).** The game's own hidden hint screen (value 10) served as the oracle for the Hard-mode recipe, and the value-9 screen as the oracle for the level select; each was then entered/reproduced on the real screen and checked by RAM and screenshot.

## 7. Validation evidence

* **Observed (screenshots + savestate RAM):** title PRESS START; title menu and cursor bytes 0→2→0; GAME LINK `NEED SAVE DATA`; gameplay; dialogue/subtitle toggle; save prompt, slot list and `Data has been saved.`; SRAM magic `INTI`; all six developer menus; level-select list, cursor movement and COMMANDER ROOM load; boot-code flag change; rejection cases in §6b.
* **Derived (disassembly):** boot-gate conditions and called functions; input-struct layout and key masks; level-select gate location; stage-name and font tables.
* **Inferred:** the exact behavioural meaning of the two IWRAM debug flags written by `0x0800113C` was not established; the boot code visibly changes them but no changed UI was identified. The Gallery button recipe is published but could not be exercised because its clear-Hard-mode save gate was not satisfied.

## 8. Unknowns

1. Effect of the two IWRAM flags at `0x03002A68` / `0x03002A80` set by the boot four-button code (value proven, downstream consumer not isolated).
2. Gallery screen: published recipes exist, but on this non-cleared save they are rejected; the actual cleared-hard-mode flag and gallery screen were not reached.
3. Level-select STAGE 01 is reachable by cursor wrap but is off the rendered window; its selection was not executed.
4. The full 256-value menu-byte space was sampled at 0–15 plus seven high values, not swept exhaustively.

## 9. Tooling

* `binutils-arm-none-eabi` (`arm-none-eabi-objdump -M force-thumb`), Capstone 5.0.7 (literal/BL/immediate scans), Python 3 + Pillow.
* mGBA 0.10.5 (`-3`), Xvfb (shared `:319`), xdotool, scrot, tesseract OCR.
* Working scripts in `/tmp/mmzero2/`: `drive.py` (PID-scoped window focus, key/combo, screenshot+crop), `testcombos.py` (title button-code sweep), savestate `gbAs` zlib patcher (used to set `0x0202F8E1`), EWRAM/IWRAM diff helpers.
* Method note (§16.13): mGBA `.ssN` files are PNGs with a zlib `gbAs` chunk; for this image the raw state is `0x61000` bytes, VRAM at `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000`. SRAM is separate (`.sav`).
* No ROM or copyrighted assets are redistributed by this report; only hashes, addresses, and derived algorithms are published.
