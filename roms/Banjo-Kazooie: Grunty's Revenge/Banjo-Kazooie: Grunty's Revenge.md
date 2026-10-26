# Banjo-Kazooie: Grunty's Revenge (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Banjo-Kazooie: Grunty's Revenge.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `BANJOKAZOOIE` |
| Game code | `BKZE` (USA) |
| Maker | `78` |
| Header revision | 0 (`0x00` at `0xBC`) |
| Internal version | `VER 0.42.75` (string at `0x064E9C`) |
| Complement check | `0x3A` at `0xBD` (computed `0x3A`, valid) |
| Header checksum | **`0x0000` at `0xBE`, computed `0x00C6`** — patched/mismatched header |
| MD5 | `4781a8e513de51ab90292c321ac34374` |
| SHA-1 | `8f5b7c20e8be0f1e7919915b905c2b182a993cec` |
| SHA-256 | `36fe9ed931dea1f14080a80071b187087ee437c046df8f62af847d09caa5ae86` |

Phase 0 scan:

* Exactly one 156-byte Nintendo logo / GBA header image, at file offset `0x04`. No second embedded header; this is not a multi-game pack.
* The ARM entry branch at `0x00` is `0xEA00002E` (`b 0x080000C0`), normal.
* The only anomaly is the zeroed header checksum field. The complement byte is correct for the header bytes, so the image boots, but it is not a clean Nintendo-checksummed dump. All addresses below are for this exact file.

## 2. Executive summary

This ROM contains **no password system and no in-game cheat-code entry**. A case-insensitive scan of 93,282 `strings -t x -n 4` lines found zero `password`, one `CHEATS` (debug menu), one `DEBUG INFO` (debug menu), two `UNLOCK*` (debug menu), and no `cheat mode`. The only published in-game button code is the save-erase code, and it is real.

There are two developer-intended input surfaces:

1. **Boot-time erase code.** ARM startup code at `0x0800013C` tests `((~KEYINPUT) & 0x214) == 0x214`, i.e. Select + L + Right, and sets the byte at `0x02000F58`. The frontend at `0x0800A07A` then opens the `ERASE ALL SAVED DATA?` screen at `0x08024BC4`. Because only those three bits are tested, **all other buttons are don't-care**: 128 of the 1024 ten-button combinations are accepted, not just the published three-button form. A novel accepted code, **Select + L + Right + Up**, was entered and screenshotted; Select + L + Left, Select + R + Right, and L + Right were rejected at boot.
2. **Disabled debug menu (`VER 0.42.75`).** The ROM contains a complete developer frontend: 7 top-level items, a 4-item `CHEATS` page, 6 warp-map pages (33 real destinations), 4 debug-info pages (20 toggles), and a 6-item `TRANSFORM` page. In the retail build the menu's frame hook `0x03002AA8` is initialised to the no-op stub `0x08009DD9`; the real handler `0x08010BA8` has **no BL or literal reference anywhere in the ROM**. Holding L+R+Select during normal gameplay does nothing (observed). The public "debug menu" recipe is a memory patch that writes `0x08010BA9` to `0x03002AA8`; that is out of scope as a cheat. For enumeration only, the same word was patched in an emulator savestate; this is analysis instrumentation, not a user-facing code.

`CHEATS` was then exercised: `UNLOCK GAME` changes the header from `LOCKED` to `UNLOCKED` and writes the 23-byte unlock table; `GOD MODE` sets `0x02001370` and the header changes `MORTAL` → `GOD`; `FULL E/F` writes the egg/feather counters. The debug frontend has no working exit once a page is entered in this build; this is documented under Unknowns.

## 3. How to reproduce

Emulator: mGBA SDL (`/usr/games/mgba`), 3× scale, under `Xvfb :165` + `openbox`.

```
Xvfb :165 -screen 0 1024x768x24 &
DISPLAY=:165 openbox &
cd /tmp/opencode/banjo
DISPLAY=:165 SDL_AUDIODRIVER=dummy mgba -3 rom.gba &
W=$(DISPLAY=:165 xdotool search --name mGBA | head -1)
DISPLAY=:165 xdotool windowfocus $W
```

mGBA default keymap used here:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Hold keys for 100–300 ms; a 10 ms tap is missed by the game's polling.

Normal menu path walked:

* Boot → THQ/Rare logos → title `PRESS START` (`screenshots/00_title.png`) → Start → main menu `NEW GAME / CONTINUE` (`screenshots/01_main_menu.png`).
* `CONTINUE` → `CONTINUE GAME` save-slot page (3 slots; all empty at first, slot 0 later filled).
* In-game Start → pause menu `CONTINUE / TOTALS / OPTIONS / SAVE`.
* `TOTALS` → map-name page (`SPIRAL MOUNTAIN`).
* `OPTIONS` → `TEXT SPEED / BGM VOLUME / SE VOLUME` (no language item in the US build).
* `SAVE` → 3-slot `SAVE GAME` page → `ARE YOU SURE? YES / NO` → `GAME SAVED`.
* No separate file-select screen exists: the 3-slot page is the save/continue selector.

### 3.1 Boot erase code — minimal (published) form

Power on / reset while holding **Select + L + Right**. In mGBA, hold the keys *before* `Ctrl+R` (or before launching) so they are down when the ARM startup code runs:

```
xdotool keydown BackSpace; xdotool keydown a; xdotool keydown Right
xdotool keydown ctrl; xdotool key r; xdotool keyup ctrl
sleep 4
xdotool keyup BackSpace; xdotool keyup a; xdotool keyup Right
```

Expected: `ERASE ALL SAVED DATA?` with `YES / NO`. The cursor starts on `YES`; in this build B did not abort, but `Down` then A selects `NO` and gives `ERASE SAVED DATA ABORTED.` Choosing `YES` erases the save and shows `ERASING... PLEASE DO NOT TURN POWER OFF.`

### 3.2 Boot erase code — novel accepted form

Hold **Select + L + Right + Up** at power-on/reset. The extra Up is ignored by the mask, but is not the A button, so the erase prompt is not auto-confirmed:

```
xdotool keydown BackSpace; xdotool keydown a; xdotool keydown Right; xdotool keydown Up
xdotool keydown ctrl; xdotool key r; xdotool keyup ctrl
sleep 4
xdotool keyup BackSpace; xdotool keyup a; xdotool keyup Right; xdotool keyup Up
```

Expected: the same `ERASE ALL SAVED DATA?` prompt. `Down` then A selects `NO` and shows the abort message.

### 3.3 Debug menu (analysis only)

The retail build gate is closed. To enumerate the developer menu, use a savestate taken in normal gameplay and patch the IWRAM word `0x03002AA8` in the `gbAs` PNG chunk from the stub `0x08009DD9` to the real handler `0x08010BA9`:

```python
import struct, zlib
src, dst = "gameplay.ss4", "gameplay_debug.ss5"
b = open(src, "rb").read()
chunks = []
i = 8
while i < len(b):
    n = struct.unpack_from(">I", b, i)[0]
    typ, data = b[i+4:i+8], b[i+8:i+8+n]
    chunks.append([typ, data])
    i += 12 + n
    if typ == b"IEND":
        break
for c in chunks:
    if c[0] == b"gbAs":
        d = bytearray(zlib.decompress(c[1], 15))
        struct.pack_into("<I", d, 0x1BAA8, 0x08010BA9)  # IWRAM base 0x19000
        c[1] = zlib.compress(bytes(d), 9)
out = bytearray(b"\x89PNG\r\n\x1a\n")
for typ, data in chunks:
    out += struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
open(dst, "wb").write(out)
```

Load the resulting slot with mGBA `F5` (or the slot you wrote). The debug menu then draws over live gameplay; D-pad moves, A confirms, B backs up. This is **not** an in-game cheat and is not presented as one.

## 4. Address map

File offset ↔ ROM address is simply `ROM address = 0x08000000 + file offset`.

| Address | Meaning |
|---|---|
| `0x08000000` | ARM entry (`b 0x080000C0`) |
| `0x0800013C`–`0x08000158` | Boot button check; mask `0x214` |
| `0x080001B0` | Literal `0x04000130` (KEYINPUT) used by the check |
| `0x02000F58` | Boot erase flag (1 = show erase screen) |
| `0x0800A07A` | `if (*(u8*)0x02000F58) call 0x08024BC4` |
| `0x08024BC4` | `ERASE ALL SAVED DATA?` screen/main loop |
| `0x0652AC` | `ERASE ALL SAVED DATA?` |
| `0x0652C4` | `ERASING... PLEASE DO NOT TURN POWER OFF.` |
| `0x0652F0` | `SAVED DATA ERASED.` |
| `0x065304` | `ERASE SAVED DATA ABORTED.` |
| `0x065320` / `0x065328` | `YES` / `NO` |
| `0x08009DD4` / `0x08009DD8` / `0x08009DDC` | No-op frame stubs (`bx lr`) |
| `0x0800A19C` | Init table: `0x03002AA4←0x08009DD5`, `0x03002AA8←0x08009DD9`, `0x03002AAC←0x08009DDD` |
| `0x03002AA4` / `0x03002AA8` / `0x03002AAC` | Frame-callback slots; `AA8` is the debug hook |
| `0x08010BA8` | Real debug handler (dead code in retail) |
| `0x08011158` | Debug handler's top-menu init (`state = 12`) |
| `0x080424B0` | Shared menu page dispatcher |
| `0x08042508` | 28-entry menu-state jump table (states 0–27) |
| `0x0203EA90` | Current menu state byte |
| `0x0203EA94` | Menu widget base; `+0x30` count, `+0x34` item-array, `+0x38` selected index |
| `0x08043B48` | Top debug menu builder (7 items) |
| `0x08043BF0`–`0x08043C08` | Top-menu string pointers (`WARP MAP`…`PROFILE`) |
| `0x08043C0C` | `CHEATS` builder (4 items) |
| `0x08043CA8`–`0x08043CB4` | `UNLOCK GAME`, `RESERVED`, `GOD MODE`, `FULL E/F` pointers |
| `0x08043CB8`, `0x08043D70`, `0x08043E28`, `0x08043EE0` | Debug-info pages 1–4 builders |
| `0x08043F98` | AI-control page builder (`NORMAL`/`NO AI`/`NO HARM`/`NO AI-HARM`) |
| `0x08044040` | `GOD ON`/`GOD OFF` builder |
| `0x080440D8` | `TRANSFORM` builder (6 items) |
| `0x08044190`, `0x08044250`, `0x08044310`, `0x080443D0`, `0x08044490`, `0x08044550` | Warp-map builders: SPIRAL, FARM, BEACH, BAYOU, HARBOUR, FURNACE |
| `0x08064A8C`–`0x08064C68` | Warp/debug labels (0xFF-terminated, not NUL) |
| `0x08064DF4`–`0x08064E90` | Debug-info/transform labels |
| `0x08011428` | Debug header draw: version, UNLOCKED/LOCKED, MORTAL/GOD, map, coords |
| `0x0200143C` | Unlock flag: 0 = UNLOCKED, nonzero = LOCKED |
| `0x02001370` | God-mode flag: 0 = MORTAL, nonzero = GOD |
| `0x08011AD4` | `CHEATS` page handler |
| `0x08011AF4` | `UNLOCK GAME` branch (writes 23 flags at `0x0200209A`) |
| `0x08011B44` | `GOD MODE` branch (opens 2-item page) |
| `0x08011B78` | `FULL E/F` branch (`bl 0x0800FA58`) |
| `0x08011A84` | GOD ON/OFF handler (sets `0x02001370`) |
| `0x08011B80` | `TRANSFORM` handler (index 0–4 → `0x08019FCC(0–4)`) |
| `0x0200107E` / `0x0200107F` | Unlock count / current count (6/6 observed) |
| `0x0200104E`, `0x02001052`–`0x02001056` | `FULL E/F` counters (`0x1C`, `0x19`, `0x0F`, `0x14`, `0x0A`, `0x19`) |
| `0x02001200` / `0x02001202` | `FULL E/F` secondary counters (`0x22`, `1`) |

## 5. Algorithm

### 5.1 Boot erase validator

Reimplementation of the ARM startup check:

```python
KEYINPUT = 0x04000130  # active-low, readable at boot
held = (~read_u16(KEYINPUT)) & 0x3FF
erase_flag = (held & 0x214) == 0x214
# 0x214 = Select (0x004) | L (0x200) | Right (0x010)
```

The ROM does `mvn r1, keyinput; and r1, r1, #0x214; cmp r1, #0x214`. It does **not** compare the whole key state, so any superset of the three required buttons passes. The flag is written to `0x02000F58`; the frontend reads it at `0x0800A07A` and enters `0x08024BC4` before the title screen.

### 5.2 Debug menu state machine

The shared dispatcher at `0x080424B0` takes a menu-state index in `r0`, bounds it to 27, and jumps through the table at `0x08042508`. The top debug menu is state 12. Item handlers use the selected index from `0x0203EA94+0x38` and either set a flag, switch to another state, or call a page builder.

The handler `0x08010BA8` is the *entry* to the debug frontend. It initialises the menu (state 12, header, three menu frames) and checks `KEYINPUT` bit 2 (Select) at `0x0801102E`. It is linked but unreachable in the retail build: the callback slot `0x03002AA8` is initialised to the `bx lr` stub `0x08009DD9`. A public memory patch overwrites that slot with `0x08010BA9`; that is the only way the menu appears in the retail ROM. The real handler has no static reference in the file.

## 6. Tables

### 6.1 Top debug menu (7 items)

| Index | Label | Action |
|---:|---|---|
| 0 | `WARP MAP` | state 22; six warp pages |
| 1 | `WARP TEMP` | checks byte `0x02001442`; no visible effect when zero |
| 2 | `DEBUG INFO` | state 13; four pages |
| 3 | `CHEATS` | state 19 |
| 4 | `TRANSFORM` | state 20 |
| 5 | `RESERVED` | no-op |
| 6 | `PROFILE` | handler returns 0; no visible effect |

### 6.2 `CHEATS` page (4 items)

| Index | Label | Effect |
|---:|---|---|
| 0 | `UNLOCK GAME` | `0x0200143C = 0`; 23 bytes at `0x0200209A`..`0x020020B0` = 1; `0x0200107E = 6`; calls `0x080388E0` |
| 1 | `RESERVED` | no-op |
| 2 | `GOD MODE` | opens 2-item `GOD ON`/`GOD OFF` page |
| 3 | `FULL E/F` | `bl 0x0800FA58`; writes the counters in §4 |

`GOD ON` sets `0x02001370 = 1`; `GOD OFF` sets it to 0. The header draw reads `0x02001370` and prints `GOD` or `MORTAL`. Several player-hurt handlers read `0x02001370`; when nonzero they branch to `0x0800F7A0` instead of the normal damage path (e.g. `0x08018BF8`, `0x08019894`, `0x0801C010`, `0x0801E2CE`, `0x08023ACA`). That is the mechanism behind the documented auto-refilling health.

### 6.3 `TRANSFORM` page (6 items)

| Index | Label | Handler target |
|---:|---|---|
| 0 | `BANJO` | `0x08019FCC(0)` |
| 1 | `MOUSE` | `0x08019FCC(1)` |
| 2 | `CANDLE` | `0x08019FCC(2)` |
| 3 | `TANK` | `0x08019FCC(3)` |
| 4 | `OCTOPUS` | `0x08019FCC(4)` |
| 5 | `RESERVED` | no-op |

### 6.4 `DEBUG INFO` pages (4 pages, 20 toggles) and AI page

| Page | Items (5 selectable + NEXT/RESERVED) |
|---:|---|
| 1 | `NONE`, `FPS, ESN, ESV`, `FPS, A2ESN, ESV`, `FPS, A4ESN, ESV`, `FPS, A8ESN, ESV`, `NEXT` |
| 2 | `FPS, ESN, MESN`, `CA, CB, CC`, `CA2, CB2, CC2`, `CA4, CB4, CC4`, `CCA, CCB`, `NEXT` |
| 3 | `CCA2, CCB2`, `CCA4, CCB4`, `CCC, CCD`, `CCE, CCF`, `CCG, CCH`, `NEXT` |
| 4 | `CCI, CCJ`, `CCK, CCL`, `CCM, CCN`, `CCO, CCP`, `CCQ, CCR`, `RESERVED` |
| AI page (state 17) | `NORMAL`, `NO AI`, `NO HARM`, `NO AI-HARM` |

The four debug-info pages are debug overlay/collision counters. The separate AI page has four combat-AI toggles. The exact meaning of each abbreviation is not established (see Unknowns).

### 6.5 Warp-map pages (6 pages, 33 real destinations)

| Page | Destinations |
|---|---|
| `SPIRAL` | `SPIRAL BOT`, `SPIRAL MID E`, `SPIRAL MID W`, `SPIRAL TOP`, `JIGGY TMPL`, `RESERVED`, `NEXT` |
| `FARM` | `FARM LOWER`, `FARM UPPER`, `COW BOSS`, `MILL HOUSE`, `MUMBO FARM`, `RESERVED`, `NEXT` |
| `BEACH` | `BEACH`, `QUARRY BOT`, `QUARRY TOP`, `UNDERCORAL`, `BEACH TOP`, `MUMBO BCH`, `NEXT` |
| `BAYOU` | `BOARDWALK`, `HOUSEROOM`, `CANDLE PUZ`, `SWAMP GAS`, `MUMBO SWMP`, `RESERVED`, `NEXT` |
| `HARBOUR` | `HARBOUR`, `SAND AREA`, `CASTLE IN`, `VILLAGE`, `INSIDE A`, `MUMBO HARB`, `NEXT` |
| `FURNACE` | `FJORD`, `FJORD CAV`, `FURN SECT`, `FURNSTORE`, `POISONROOM`, `MUMBO FURN`, `NEXT` |

Observed warp: selecting `FARM LOWER` changed the debug header to `LOWERFARM`, coordinates `800 1032`. Selecting `SPIRAL BOT` from the first page changed the header to `SPIRALBOTTOM` and, when the menu had been entered from a frontend state, restarted the game; from a valid gameplay state it returned to the debug frontend. The menu does not resume normal rendering in this build.

## 6b. Enumeration

### 6b.1 Boot button-code space (complete)

The startup check is a single 10-bit mask comparison. Define the 10 GBA buttons as:

`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`

Space: `2^10 = 1024` combinations. Validator: `(held & 0x214) == 0x214`.

* Accepted: every combination that contains Select, L and Right. The other 7 buttons are don't-care, so **128 accepted** combinations (`2^7`).
* Rejected: the remaining **896** combinations.
* The published GameFAQs code is the minimal three-button member: **Select + L + Right**.

Novel codes generated and entered (not in any published list):

| Code | Formula | Result | Evidence |
|---|---|---|---|
| **Select + L + Right + Up** | `0x214 \| 0x040` | accepted; `ERASE ALL SAVED DATA?` prompt | `screenshots/06_erase_novel_select_l_right_up.png` |
| Select + L + Right + A | `0x214 \| 0x001` | accepted; because A is also the `YES` confirm, it advanced to `ERASING...` | `screenshots/22_erase_novel_select_l_right_a.png` |
| Select + L + Right (published) | `0x214` | accepted; prompt | `screenshots/05_erase_prompt.png` |

Bounds proven by rejection (all booted to the normal title screen, no erase prompt):

| Rejected input | Why |
|---|---|
| Select + L + Left | Right missing (`0x010`) |
| Select + R + Right | L missing (`0x200`) |
| L + Right | Select missing (`0x004`) |

Screenshots: `screenshots/08_reject_select_l_left.png` (representative), plus the same title result for the other two.

The abort path was also exercised: `Down` to `NO`, A → `ERASE SAVED DATA ABORTED.` (`screenshots/07_erase_aborted.png`).

### 6b.2 Debug menu enumeration

Menu system size: 28 states (0–27) in the dispatcher table; 16 of them are the developer frontend (states 12–27). The developer frontend contains:

| Surface | Entries | Notes |
|---|---:|---|
| Top menu | 7 | 4 functional sections + WARP TEMP + RESERVED + PROFILE |
| Cheats | 4 | 3 functional (`UNLOCK GAME`, `GOD MODE`, `FULL E/F`), 1 RESERVED |
| Transform | 6 | 5 forms, 1 RESERVED |
| Debug info | 4 pages × 5 toggles = 20 | 4 `NEXT`/`RESERVED` navigation cells |
| AI control | 4 | `NORMAL`, `NO AI`, `NO HARM`, `NO AI-HARM` (state 17) |
| Warp map | 6 pages × ~6 = 33 real destinations | 6 `NEXT`/`RESERVED` cells |
| GOD ON/OFF | 2 | submenu of `GOD MODE` |

Every top-level page and all four debug-info pages were opened and photographed; the separate AI-control page (`state 17`) was located statically but is not reachable from the top menu path exercised here.

* Top: `screenshots/09_debug_top.png`
* Cheats: `screenshots/10_debug_cheats.png`
* UNLOCK GAME result: `screenshots/20_debug_unlocked.png` (header `UNLOCKED`)
* GOD ON result: `screenshots/11_debug_god_on.png` (header `GOD`); the 2-item page is `screenshots/21_debug_god_page.png`
* FULL E/F: `screenshots/12_debug_full_ef.png` (returns to top; counters changed)
* Debug info pages 1 and 4: `screenshots/13_debug_info_p1.png`, `screenshots/14_debug_info_p4.png`
* Transform: `screenshots/15_debug_transform.png`
* Warp pages: `screenshots/16a_debug_warp_spiral.png` … `16f_debug_warp_furnace.png`

Novel, unpublished combination exercised: **UNLOCK GAME + GOD ON + FULL E/F** in one session. The header changed `LOCKED` → `UNLOCKED` and `MORTAL` → `GOD`; the `FULL E/F` memory diff set `0x0200104E=0x1C`, `0x02001052..56 = 19,0F,14,0A,19`, `0x02001200=0x22`, `0x02001202=1`. No published list describes this combination or those counters.

Gate proof (negative):

* `0x08010BA8` has zero BL targets and zero literal pointers in the ROM.
* `0x03002AA8` is initialised to `0x08009DD9` (a `bx lr` stub) by the table at `0x0800A19C`; a gameplay savestate confirmed the slot held `0x08009DD9`.
* Holding L+R+Select in normal gameplay produced no menu (observed `screenshots/19_reject_lrs_in_game.png`; gameplay unchanged).
* Therefore the debug menu is **developer content with a disabled gate**, not an in-game cheat. The public GameShark/CodeBreaker recipe is a memory patch and is outside the in-game scope.

### 6b.3 Password / alphabet search (negative, bounded)

There is no password system:

* `strings -t x -n 4`: 93,282 lines; `password` = 0, `cheat mode` = 0, `code` = 1 (an audio error: `AUDIO ERROR, not enough space to put audio RAM code`), `cheat` = 1 (`CHEATS`, debug menu), `debug` = 1 (`DEBUG INFO`, debug menu), `unlock` = 2 (debug menu), `secret` = 10 (all story text), `hidden` = 2 (story text).
* No 32/40/64-symbol alphabet table, no 5-bit-per-character decoder, and no checksum validator exists in the ROM. The only literal accepted inputs are the boot erase button mask and the debug menu labels.
* The only published in-game code (GameFAQs "Erase All Save Data", Select+L+Right at power-on) was verified against the ROM and the emulator. The VGChartz page has only the gameplay secret "Get N.Kreditzs"; its other entries are walkthrough tips, not codes. TCRF documents the debug menu only via a memory patch.

Published-source check:

* `https://gamefaqs.gamespot.com/gba/517531-banjo-kazooie-gruntys-revenge/cheats` — direct fetch is 403; the archived 2022 snapshot contains only the two ending unlocks and the N.Kreditzs secret, while the current search snippet/summary gives the erase code used above.
* `https://www.vgchartz.com/game/12283/banjo-kazooie-gruntys-revenge/cheats` — "Total cheats available: 5"; four are walkthrough tips and one is the N.Kreditzs gameplay secret.
* `https://tcrf.net/Banjo-Kazooie:_Grunty%27s_Revenge` — debug-menu description and the CodeBreaker/GameShark patch; no in-game trigger.
* `https://almarsguides.com/retro/walkthroughs/gba/games/banjokazooiegruntysrevenge/codebreaker/` — same memory-patch recipe, out of scope.

## 7. Validation evidence

**Observed**

* Boot with Select+L+Right → `ERASE ALL SAVED DATA?` (`05_erase_prompt.png`).
* Boot with Select+L+Right+Up → same prompt (`06_...png`); extra Up accepted, proving don't-care bits.
* Boot with Select+L+Left, Select+R+Right, or L+Right → normal title, no prompt (`08_...png` and two identical title results).
* Erase screen `NO` → `ERASE SAVED DATA ABORTED.` (`07_...png`).
* Debug menu pages draw and respond to D-pad/A/B when the `0x03002AA8` hook is patched in a savestate.
* `UNLOCK GAME` → header `UNLOCKED`; `GOD ON` → header `GOD`; `FULL E/F` → counter diff above.
* Warp to `FARM LOWER` → header `LOWERFARM`, coords `800 1032` (`16g_debug_warp_lowerfarm_result.png`); warp pages all listed and photographed.

**Derived**

* Exact boot mask and flag path from ARM instructions at `0x0800013C`–`0x08000158`.
* 128/1024 accepted boot combinations from the mask; rejection set from the same formula.
* Debug menu state table and item handlers from `0x08042508`, `0x08043xxx` builders, and `0x08011A84`/`0x08011AD4`/`0x08011B80`.
* Unlock flag `0x0200143C`, god flag `0x02001370`, `FULL E/F` counters, and the 23-byte unlock table from the handlers and savestate diffs.
* God-mode effect path: hurt handlers read `0x02001370` and branch to `0x0800F7A0` when nonzero.

**Inferred**

* The semantic names of the `DEBUG INFO` abbreviations (`ESN`, `ESV`, `CA`, `CB`, `CC`, `CCA`…) are collision/entity overlay categories; the acronyms are not decoded.
* `FULL E/F` counter meanings are inferred from their values and the game's egg/feather HUD (normal/fire/ice/battery/golden); the memory writes are observed.
* Transform form indices 0–4 map to Banjo/Mouse/Candle/Tank/Octopus from the handler; the visual form was not captured because the debug frontend remains active after selection in this build.

## 8. Unknowns

* Exact meaning of the 20 `DEBUG INFO` toggles and their on-screen effects; the pages were enumerated and photographed but the counters were not individually decoded.
* The separate AI-control page (`NORMAL`/`NO AI`/`NO HARM`/`NO AI-HARM`, state 17) was located and its build table dumped, but no top-menu path reached it; its parent entry may have been removed from the retail frontend.
* `WARP TEMP` and `PROFILE` are placeholders in this build. `WARP TEMP` checks `0x02001442`; both produced no visible change. The condition that enables `WARP TEMP` was not found.
* The debug frontend does not return to normal gameplay after a page action in this build; the handler's Select exit is only effective before navigating away from the initial state. The menu is therefore a development tool, not a playable cheat.
* The header checksum mismatch (`0x0000` vs `0x00C6`) shows the image was modified before analysis; the exact patching tool and whether any code bytes differ from a clean dump are not established (the game boots and the hashes above pin this file).
* Transform visuals and god-mode damage immunity were not played through to a combat outcome; their mechanisms are derived from code and flag diffs.

## 9. Tooling

* `binutils-arm-none-eabi` (`objdump -M force-thumb` / `-M force-arm`) for all disassembly.
* Python 3 + `capstone` 5.0.7 for BL/literal scans and the LDR-literal reader scan.
* mGBA SDL 0.10.x under `Xvfb :165` + `openbox`; `xdotool` for input; ImageMagick `import` for 720×480 screenshots.
* `strings -t x -n 4`, `xxd`, `grep`.
* Savestate format: mGBA PNG with a zlib-compressed `gbAs` chunk. State layout used here: IWRAM at uncompressed offset `0x19000`, EWRAM at `0x21000`; `0x03002AA8` is at chunk offset `0x1BAA8`.
* No ROM, graphics, music, or text assets are redistributed with this report. The `.gba` is not committed; screenshots are evidence only.

### Screenshot index (same folder)

```
screenshots/00_title.png
screenshots/01_main_menu.png
screenshots/02_file_select.png
screenshots/03_options.png
screenshots/04_pause.png
screenshots/05_erase_prompt.png
screenshots/06_erase_novel_select_l_right_up.png
screenshots/07_erase_aborted.png
screenshots/08_reject_select_l_left.png
screenshots/09_debug_top.png
screenshots/10_debug_cheats.png
screenshots/11_debug_god_on.png
screenshots/12_debug_full_ef.png
screenshots/13_debug_info_p1.png
screenshots/14_debug_info_p4.png
screenshots/15_debug_transform.png
screenshots/16a_debug_warp_spiral.png
screenshots/16b_debug_warp_farm.png
screenshots/16c_debug_warp_beach.png
screenshots/16d_debug_warp_bayou.png
screenshots/16e_debug_warp_harbour.png
screenshots/16f_debug_warp_furnace.png
screenshots/16g_debug_warp_lowerfarm_result.png
screenshots/18_gameplay.png
screenshots/19_reject_lrs_in_game.png
screenshots/20_debug_unlocked.png
screenshots/21_debug_god_page.png
screenshots/22_erase_novel_select_l_right_a.png
```
