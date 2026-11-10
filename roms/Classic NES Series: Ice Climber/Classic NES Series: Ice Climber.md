# Classic NES Series: Ice Climber (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Classic NES Series: Ice Climber/Classic NES Series: Ice Climber.gba` |
| Size | 1,048,576 bytes (`0x100000`) |
| Header title (`0xA0`) | `ICE CLIMBER` (NUL padded) |
| Game code (`0xAC`) | `FICE` |
| Maker code (`0xB0`) | `01` (Nintendo) |
| Version (`0xBC`) | `0x00` |
| Complement (`0xBD`) | `0xEA` (valid: calculated `0xEA`) |
| Header checksum (`0xBE`) | `0x0000` (rebuilt-header artifact; complement is correct) |
| Entry word (`0x00`) | `0xEA000031` → ARM branch to `0x080000CC` |
| MD5 | `bc62fa1f6a3f1421c802aba76f1f4732` |
| SHA-1 | `64e965d61b2d1be5dfadb0236fed83fea5995724` |
| SHA-256 | `2f68937c830fe1928a16f18e86927fcd1b40419c8b0f5a9d2917dc2a6191a4e0` |

Phase 0 notes:

* The Nintendo logo is intact at `0x04`.
* A **second GBA header** exists at file `0xCFA0` (logo at `0xCFA4`), title `ICE CLIMBER` at `0xD040`, game code `FICE` at `0xD04C`, entry `0xEA000061` → `0x0800D12C`. This is the series' single-pak / multiboot link-play image, not a second game: the ROM also contains `RFU_V1021`, `RFU-MBOOT` and `NINTENDOSio32ID_030820` at `0x5FB0`/`0x5FB0+` and repeated near `0x17B54`.
* The main image's boot signature is at `0xC0`–`0xCE`: `03 16 18 31` then ASCII `1MBR_6_2P<P`. This is the shared Classic NES wrapper boot signature (compare `KEY_5_2P<P` in Donkey Kong and `IEXBI` in Excitebike), not a cracktro.
* The save library signature `EEPROM_V124` is at file `0x239A4`; mGBA created an 8 KiB `.sav`, consistent with 8 KiB EEPROM.
* The wrapper message/text bank is duplicated three times: `0x2D38`, `0xEB8C`, `0x15348` (the latter two belong to the multiboot/link image copies).
* No trainer/cracktro/appended menu: `MODE7`, `SUNHORS`, `CRC BANDIT`, `PARADOX`, `PDX`, `crack`, `trainer` all return 0 hits.
* This is an **emulated NES game**. At runtime the 16 KiB NES PRG and 8 KiB CHR are materialised in GBA EWRAM at `0x02004000`/`0x02008000` (savestate offsets `0x25000`/`0x29000`). The NES 2 KiB RAM is at IWRAM `0x03007200` (savestate offset `0x20200`). The NES image's source in the GBA ROM is wrapper-encoded/patched (a similar but not byte-identical copy begins around file `0x17D6D`); the runtime EWRAM image is the ground truth used here.

## 2. Executive summary

The only in-game, developer-intended cheat surface in this ROM is the NES **MOUNTAIN (level) selector** on the game menu. There is no password system, no button-code cheat, no NES debug menu, and no hidden wrapper menu slot.

* **Mountain selector.** The title/game menu displays `MOUNTAIN xx` and lets the player choose any of the 32 mountains before starting:
  * Up or Left: `$59 = ($59 - 1) & 0x1F` (0 → 31 wrap).
  * Down or Right: `$59 = ($59 + 1) & 0x1F` (31 → 0 wrap).
  * Start begins the game at the selected mountain; `$59` is the 0-based level byte and the displayed number is `($59 & 0x1F) + 1`.
  * The selector is exactly 32 states (0–31). The 5-bit mask is `AND #$1F` at NES `$F54D`; there are no hidden or out-of-range mountain values reachable from the menu.
* **Novel state (not in any published code list).** `MOUNTAIN 32` was minted through the menu (not a memory edit) and RAM-verified: title `$59 = 0x1F` and the nametable displays `MOUNTAIN 32` (digit tiles `0x03 0x02`); after Start `$59 = 0x1F`, `$20 = 3`, `$53 = 0`, `$90 = 4`, and the first screen differs from Mountain 1 by 226 of 960 nametable tiles. No published GameFAQs/VGChartz/TCRF/wiki list documents this selector; the published level/mountain codes are RAM pokes (`0059:00`, `0305:00`), not in-game inputs.
* **Wrapper System Menu.** `L+R` during play opens the series-standard system menu. Its complete item set, read from the ROM's own message records and verified on screen, is `CONTINUE`, `RESET`, `LINKED PLAY`, `SAVE HIGH SCORE`, `SLEEP MODE`. The selector is exactly five items (0–4): the cursor routine wraps `0→4` and `4→0`, and the dispatcher table has exactly five entries. There is **no sixth/unlabelled slot** (unlike the Excitebike design menu).
* **Secret-code dialog is dead.** The shared wrapper's secret-code messages exist in this ROM:
  * message 51: `SAVE HIGH SCORE AND SECRET CODE!` (`0x080038BB`)
  * messages 52/53: `YES / NO` variants (`0x080038E2`, `0x080038F1`)
  * message 54: `PRESS THE A BUTTON TO USE THIS SECRET CODE.` (`0x08003901`)
  No message-renderer call site passes IDs 50–54, and the actual `SAVE HIGH SCORE` path draws message 45/46. Entered live, `SAVE HIGH SCORE` shows `WAS UNABLE TO SAVE.` (message 46); it never shows the secret-code prompt. The code-dialog is a compiled-but-unwired leftover in this SKU.
* **Published lists.** GameFAQs' GBA cheats page could not be archived (Wayback CDX returned no snapshot; direct fetch 403). VGChartz lists 0 cheats; IGN's NES Classic guide says “No cheats are currently available” for Ice Climber; TCRF documents only unused graphics and regional/version differences; Cheat Happens lists only two Action Replay memory-edit codes (out of scope). No published in-game code exists to reproduce.

## 3. How to reproduce

### Emulator and keymap

* mGBA 0.10.5 (SDL frontend, `/usr/games/mgba`) under `Xvfb :251`, `openbox`, `SDL_AUDIODRIVER=dummy`.
* Keymap: **A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`**, D-pad = arrow keys.
* Keys must be sent as XTEST events to the focused mGBA window; one press = 0.06–0.15 s hold + 0.25–0.45 s gap. A long hold double-steps menus.

### Savestate reading (no debugger needed)

mGBA `.ssN` is a PNG with a zlib-compressed `gbAs` chunk. `zlib.decompress` gives a 397,312-byte (`0x61000`) state for this 1 MiB ROM:

| State offset | Region |
|---:|---|
| `0x0000` | header/CPU |
| `0x0400` | GBA I/O (`KEYINPUT` at `0x0530`) |
| `0x0800` | palette |
| `0x0C00` | OAM |
| `0x1000` | VRAM (`0x18000`) |
| `0x19000` | IWRAM (`0x8000`) |
| `0x21000` | EWRAM (`0x40000`) |
| `0x25000` | runtime NES PRG (`0x02004000`) |
| `0x29000` | runtime NES CHR (`0x02008000`) |
| `0x20200` | NES 2 KiB RAM (`0x03007200`) |

Visible NES background: the wrapper mirrors the NES nametable as a 32×30 GBA BG3 tilemap at VRAM `0x2000` (`BG3CNT = 0x0405` at the title, with bit 15 set transiently after some transitions; char base `0x4000`, 4 bpp). NES tile index = low byte of each 16-bit map entry. NES text can be read by rendering those tiles with the CHR at EWRAM `0x8000`; the title's `MOUNTAIN xx` line is nametable row 20.

Wrapper dialogue text is the BG0 tilemap at VRAM `0x6800` (`BG0CNT = 0x8D04`, screen base 13, char base 1); the wrapper uploads its proportional font into tile slots around `0x1B8`–`0x1C9`.

### Exact menu paths

**Title / game menu**

1. Reset the emulated NES with **Start + Select + A + B** (hold ~0.5 s). The title appears: NES `$53 = 0`, `$20 = 0`, `$51 = 1`.
   (Cold boot instead runs the attract/demo: `$53 = 1`; pressing Start there starts a game directly at the stored selection.)
2. Press **Up/Down/Left/Right** to change `$59`; the screen redraws `MOUNTAIN xx`.
3. Press **Start** to begin at the selected mountain. Select/A/B do not start the game on the title.

**Mountain 32 (novel state)**

1. Reset to the title (`$59 = 0`).
2. Press **Down 31 times**. `$59 = 0x1F`; nametable row 20 shows `MOUNTAIN 32`.
3. Press **Start**. In-game: `$59 = 0x1F`, `$20 = 3`, `$53 = 0`, `$90 = 4`.

**Wrapper System Menu**

1. During play hold **L + R** (~0.6 s). The NES freezes (NES `$50` unchanged over 1 s; NES RAM diff 0).
2. Cursor rows: `27` CONTINUE, `29` RESET, `31` LINKED PLAY, `33` SAVE HIGH SCORE, `35` SLEEP MODE.
3. **Down** cycles `27→29→31→33→35→27`; **Up** reverses. **A** (or Start) activates the highlighted item.
4. `CONTINUE` resumes the NES (NES RAM changes again). `RESET` returns to the NES title (`$20=0`, `$90=0`). `LINKED PLAY` opens the link/connection dialog and freezes the NES. `SAVE HIGH SCORE` runs the EEPROM save, showing `PRESS THE B BUTTON TO CANCEL` and then `WAS UNABLE TO SAVE.` (message 46) in this emulator. `SLEEP MODE` produced no visible freeze/blank in this emulator: the NES frame counter kept advancing and the game screen remained; **Select + L + R** returns to the game. (The wrapper most likely uses the GBA STOP/sleep state, which this mGBA build does not render as a blank screen.)

**NES pause**

* **Start** during play freezes the NES (`$50` unchanged); Start again resumes.

### Recon classification (strings)

* `strings -t x -n 4` over the 1 MiB image finds the Nintendo/RFU/EEPROM signatures and the wrapper's UI text, but the UI is stored in the wrapper's font code (e.g. `0x23=A`, `0x34=B`), so a naive ASCII keyword grep sees mojibake.
* ASCII keyword search (whole image): `PASSWORD`, `password`, `CHEAT`, `DEBUG`, `SECRET`, `secret`, `UNLOCK`, `LEVEL`, `STAGE`, `CONTINUE` = **0 hits**.
* Wrapper font-code search (whole image): `CONTINUE` 19, `SELECT` 15, `RESET` 3, `SLEEP MODE` 6, `LINKED PLAY` 33, `SAVE HIGH SCORE` 7 — all of these are the System Menu / link-play / help text, not code entry. `SECRET CODE` 6 hits = 3 text-bank copies × the two dead dialog strings. `PASSWORD`, `ENTER`, `DEBUG`, `TEST`, `SOUND TEST`, `STAFF`, `OPTION`, `CONFIG`, `LEVEL SELECT` = **0 hits**.
* The NES side stores text as CHR tile indices; its 16 KiB PRG has no ASCII `PASSWORD` and no `0x0A..0x23` alphabet run.

## 4. Address map

### GBA / wrapper

| Address / offset | Meaning |
|---|---|
| `0x08000000` | GBA header, entry `0xEA000031` → `0x080000CC` |
| `0x080000C0`–`0x080000CE` | wrapper boot signature `03 16 18 31` + ASCII `1MBR_6_2P<P` |
| `0x0800CFA0` | second GBA header (single-pak/multiboot image), entry → `0x0800D12C` |
| `0x08002D38` | wrapper message/text bank (first copy; also `0xEB8C`, `0x15348`) |
| `0x08003954` | message-record table base (8 bytes/record): `{u8 x, u8 y, u8 w, u8 h, u32 string_ptr}`; 55 records |
| `0x08000FCC` | message renderer: `r0 = context`, `r1 = message id`; record = `0x08003954 + 8*id` |
| `0x08001480` | keypad reader: `current = KEYINPUT ^ 0x3FF`; stores current at `0x0300649C`, newly pressed at `0x030064A0` |
| `0x08002428` | System Menu state handler (opens on L+R, reads item index at context+`0x94D`) |
| `0x08002490` | System Menu dispatcher table, 5 entries: `0x24A4`, `0x24B0`, `0x24BC`, `0x2594`, `0x25A0` |
| `0x080025D0`–`0x0800262A` | System Menu cursor: Up (`0x40`) at `0x25D4`, Down|Select (`0x84`) at `0x25FE`, A|Start (`0x09`) at `0x2620`; wrap `>4→0` at `0x2614`, `0→4` at `0x25F8` |
| `0x080023B8` / `0x080023F0` | render message 45 (`HIGH SCORE SAVED.`) / 46 (`WAS UNABLE TO SAVE.`) |
| `0x080038BB` | message 51 string `SAVE HIGH SCORE AND SECRET CODE!` (unreferenced by code) |
| `0x080038E2`/`0x080038F1` | messages 52/53 `YES / NO` (unreferenced) |
| `0x08003901` | message 54 `PRESS THE A BUTTON TO USE THIS SECRET CODE.` (unreferenced) |
| SRAM `0x0E000000` | 8 KiB EEPROM save; wrapper record magic `_RBM1` at `0xF8`/`0x100` |

### NES side (16 KiB NROM-128 mapped at `$C000`–`$FFFF`)

| NES address | PRG offset | Meaning |
|---|---:|---|
| `$C000` | `0x0000` | data before RESET handler |
| `$C014` | `0x0014` | RESET handler (`78 D8 A9 10 8D 00 20 A2 FF 9A`) |
| `$C460` | `0x0460` | demo/menu setup: masks `$59` with `0x1F`, stores selection to `$03FE`, sets demo `$59 = $03FD & 3` |
| `$C620` | `0x0620` | Start/Select handler: `LDA $14; AND #$30`; copies `$03FE` to `$59`; clears demo `$53`; increments `$03FD` |
| `$CC7E` | `0x0C7E` | mountain progression: `INC $59`; wraps at `0x63` (`CMP #$63` / `LDA #0; STA $59`) |
| `$DFA5` | `0x1FA5` | mountain display helper: `LDA $59; AND #$1F; TAY` |
| `$F53E` | `0x353E` | **title mountain selector**: `LDY $59; DEY; LDA $14; AND #$0F`; Right/Down add 2 before `AND #$1F`, Up/Left do not; `STA $59` at `$F551` |
| `$F54D` | `0x354D` | `AND #$1F` mask (5-bit mountain field) |
| `$F560` | `0x3560` | selector debounce/store path (`$37`, `$4E`, `$FE`) |

Key NES RAM (base `0x03007200`):

| Address | Meaning |
|---|---|
| `$14` | joypad buttons (Right=1, Left=2, Down=4, Up=8, Start=0x10, Select=0x20, B=0x40, A=0x80) |
| `$15` | D-pad only (start-pause reads `$15 & 0x10`) |
| `$20` | lives (3 at game start) |
| `$31` | title animation/sound counter (changes on Select; not a mode selector) |
| `$50` | frame counter (stable while paused/frozen) |
| `$53` | demo mode (`1` = attract/demo, `0` = title/game) |
| `$58` | 1P/2P state byte (0 at title; not changed by observed Select) |
| `$59` | **mountain/level byte** (0-based; display = `($59 & 0x1F)+1`) |
| `$03FD` | game-start counter (incremented on Start) |
| `$03FE` | saved mountain selection (written at `$C460`, read at `$C626`) |

## 5. Algorithm

### 5.1 Title mountain selector (reimplementation)

```c
// NES $F53E, called from the demo/title frame loop
uint8_t buttons = RAM[$14];          // active-high
uint8_t dpad = buttons & 0x0F;       // Right=1,Left=2,Down=4,Up=8
uint8_t y = RAM[$59] - 1;            // 8-bit
if (dpad != 0) {
    if (dpad & 0x05) {               // Right or Down
        y += 2;                      // net +1 after DEY
    }
    uint8_t next = y & 0x1F;         // $F54D
    if (RAM[$37] == 0) {             // debounce
        RAM[$59] = next;
        RAM[$4E] = 0x80;
        RAM[$FE] = 0x08;
        RAM[$37] = 0x0F;
    }
}
```

Observable consequences:

* Down/Right: `$59 = ($59 + 1) & 0x1F`.
* Up/Left: `$59 = ($59 - 1) & 0x1F` (0 → 31).
* No D-pad: unchanged.
* No value outside 0..31 can be produced.

### 5.2 Start and display

```c
// title/menu display ($DFA5)
uint8_t mountain_index = RAM[$59] & 0x1F;
draw_number("MOUNTAIN ", mountain_index + 1);

// Start ($C620/C626)
if (RAM[$14] & 0x30) {              // Start or Select
    RAM[$59] = RAM[$03FE];          // saved selection
    RAM[$53] = 0;                   // leave demo/title
    RAM[$03FD]++;                   // start counter
    start_game();
}
```

Observed on the title: Start begins the game; Select/A/B do not. Select does not change `$59` or `$53` in the observed state.

### 5.3 Post-mountain progression (derived from the level-clear path)

```c
// $CC7E, after a level-clear flag ($45==1)
if (RAM[$20] != 0x80) {
    RAM[$59] = (RAM[$59] + 1);
    if (RAM[$59] >= 0x63) RAM[$59] = 0x00;
    RAM[$56]++;
}
```

So normal play can carry `$59` from 0 to `0x62` (99 level slots, three 32-mountain loops plus 3), while the title display always shows `($59 & 0x1F)+1`. The selector itself remains 0..31.

### 5.4 Wrapper System Menu selector

```c
// $08002428: item index at ctx+0x94D, 5 items
if (newly_pressed & 0x40) {              // Up
    idx = (idx == 0) ? 4 : idx - 1;
} else if (newly_pressed & 0x84) {       // Down or Select
    idx++;
    if (idx > 4) idx = 0;
} else if (newly_pressed & 0x09) {       // A or Start
    handler = dispatch[idx];            // 5-entry table at 0x08002490
}
```

The `cmp r0,#4; bhi` at `0x08002470` and the 5-entry table make the item space exactly 0..4. There is no hidden slot.

## 6. Tables

### 6.1 Mountain selector states

| `$59` | Display | Notes |
|---:|---|---|
| `0x00` | `MOUNTAIN 01` | default; published memory poke `0059:00` reaches only this |
| `0x01`–`0x1E` | `MOUNTAIN 02`–`31` | all reachable by Down/Right or Up/Left |
| `0x1F` | `MOUNTAIN 32` | last selector value; **novel state minted here** |
| `0x20`+ | `MOUNTAIN 01`+ (display masks `&0x1F`) | not reachable from the menu; only via post-clear `INC $59` |

### 6.2 Wrapper System Menu

| Index | Cursor row | Label | Observed action |
|---:|---:|---|---|
| 0 | 27 | `CONTINUE` | resumes the frozen NES |
| 1 | 29 | `RESET` | resets the emulated NES to the title (`$20=0`, `$90=0`) |
| 2 | 31 | `LINKED PLAY` | opens the link/connection dialog; NES frozen |
| 3 | 33 | `SAVE HIGH SCORE` | runs EEPROM save; `PRESS THE B BUTTON TO CANCEL` → `WAS UNABLE TO SAVE.` |
| 4 | 35 | `SLEEP MODE` | no visible freeze/blank under mGBA; NES keeps running; exit with Select+L+R |

### 6.3 Save/high-score and secret-code message records

| ID | Pointer | Text (decoded from the wrapper font) |
|---:|---|---|
| 45 | `0x080037BB` | `HIGH SCORE SAVED.` / `PRESS THE B BUTTON.` |
| 46 | `0x080037E8` | `WAS UNABLE TO SAVE.` / `PRESS THE B BUTTON.` |
| 51 | `0x080038BB` | `SAVE HIGH SCORE AND SECRET CODE!` |
| 52 | `0x080038E2` | `YES / NO` prompt + `PRESS THE A BUTTON` |
| 53 | `0x080038F1` | ` YES / NO` + `PRESS THE A BUTTON` |
| 54 | `0x08003901` | `PRESS THE A BUTTON TO USE THIS SECRET CODE.` |

### 6.4 Published sources checked

| Source | Result |
|---|---|
| GameFAQs GBA cheats (`/gba/919772-.../cheats`) | direct fetch 403; Wayback CDX returned no snapshot. No archived in-game list recovered. |
| VGChartz (`/game/26548/.../cheats`) | “Total cheats available: 0” |
| Cheat Happens | 2 Action Replay codes only (`f27f40d9 9d9a7538 bf3eebed ee253d6f`, `38a0f2d1 a24bb1a1`); memory writes, out of scope; literals absent from ROM (0 hits) |
| TCRF `Ice_Climber` | unused hammer-up sprite, regional Topi seal/yeti, FDS version differences; no codes |
| IGN NES Classic guide | “Ice Climber — No cheats are currently available.” |
| Libretro/RetroGameSpace cheat DB | Game Genie/AR codes including `0059:00` “Level Select (At Title Screen)”; a RAM poke, and it corroborates `$59` as the level byte |

## 6b. Enumeration

### Space definition

* In-game level selector: one 5-bit field, values `0..31` (32 states), displayed as `MOUNTAIN 01..32`.
* Mask: `AND #$1F` at NES `$F54D` (and at `$C460`); wrap at both ends (`0→31`, `31→0`).
* No checksum, no alphabet, no length rule, no reserved bits.
* The in-game level byte `$59` is also written by post-clear progression (`INC $59`, wrap at `0x63`), giving a derived 99-value range (`0..0x62`) for normal play; the title selector itself is only 0..31.

### Novel state (not in any published list)

**State: `MOUNTAIN 32`, 1 player, entered through the game menu.**

* Title before Start: `$59 = 0x1F`; nametable row 20 = `3C 5B 93 5A 3A 33 3B 5A 38 03 02` (`MOUNTAIN ` + digit tiles `0x03 0x02` = `32`).
* After Start: `$59 = 0x1F`, `$20 = 0x03`, `$53 = 0x00`, `$90 = 0x04`.
* The first screen differs from a Mountain 1 start in 226 of 960 nametable tiles in the sampled run (232 in another run; a few tiles are randomized two-deep blocks). The border/mountain tiles change (e.g. `0xA4/0xAA` → `0x42/0x45`) and the platform rows differ, so the state is not an alias of Mountain 1.
* Reproduction: reset (`Start+Select+A+B`) → Down ×31 → Start. The same state is reachable with a single **Left** press from `MOUNTAIN 01` (`$59 0x00 → 0x1F`); the manual assigns Up/Down to mountain selection and Left/Right to movement, so Left-as-selector is an unadvertised behavior. The code at `$F54D` treats Right like Down and Left like Up (mask `0x05`).
* No published list contains this: GameFAQs/VGChartz/TCRF/IGN list no in-game Ice Climber codes at all; the published level/mountain codes are the RAM pokes `0059:00` and `0305:00`, not selector inputs, and `0059:00` forces Mountain 1 rather than 32.

### Bounds proven by rejection

| Input | Result | RAM |
|---|---|---|
| Down at `MOUNTAIN 32` (`$59=0x1F`) | wraps to `MOUNTAIN 01` | `$59=0x00` |
| Up at `MOUNTAIN 01` (`$59=0`) | wraps to `MOUNTAIN 32` | `$59=0x1F` |
| Left at `$59=0` | wraps to `$59=0x1F` | `$59=0x1F` |
| 40 consecutive Downs from `$59=0` | sequence `01..1F, 00, 01..08`; never `>0x1F` | `$59 ≤ 0x1F` |
| Static mask | `AND #$1F` at `$F54D` and `$C460` | — |

The out-of-range values `0x20..0xFF` cannot be selected: the code masks them and the observed cursor wraps.

### Negative searches (bounded)

| Search | Space searched | Result |
|---|---|---|
| ASCII `PASSWORD`, `password`, `CHEAT`, `DEBUG`, `SECRET`, `secret`, `LEVEL SELECT`, `CONTINUE` | whole 1 MiB | **0 hits** |
| Wrapper font-code `PASSWORD` (`46 23 27 27 26 42 2E 2B`) | whole 1 MiB | **0 hits** |
| Wrapper font-code `ENTER` (`2A 38 32 2A 2E`) | whole 1 MiB | **0 hits** |
| Wrapper font-code `LEVEL SELECT` | whole 1 MiB | **0 hits** |
| Wrapper font-code `DEBUG`, `TEST`, `SOUND TEST`, `STAFF`, `OPTION`, `CONFIG` | whole 1 MiB | **0 hits** |
| Wrapper font-code `SECRET CODE` | whole 1 MiB | 6 hits = 3 text-bank copies × 2 dead strings (`0x38D5/0x3925`, `0xF891/0xF8E1`, `0x1604D/0x1609D`) |
| Wrapper message IDs 50–54 drawn | 46 `bl 0x08000FCC` call sites (one with a dynamic id) | **none**; IDs 50–54 absent from every call path |
| NES PRG ASCII runs | 16 KiB runtime PRG | 24 runs, all graphics/data (e.g. `hijklmjihmlkmlkjihklmhij`); no `PASSWORD` |
| NES alphabet run `0x0A..0x23` | 16 KiB PRG | **0 hits** |
| NES single-button-mask runs ≥4 (`{1,2,4,8,0x10,0x20,0x40,0x80}`) | 16 KiB PRG | 15 hits, all data tables (`0xCBED`, `0xCD90`, `0xD7BC`, `0xF267`, …), none an input sequence comparator |
| NES input reads | runtime PRG | only `$C620` (`$14 & 0x30`), `$F541` (`$14 & 0x0F`), `$C0EB`/`$C11C` (`$15 & 0x10`), `$C490`/`$C49E` (`$15 & 0x00/0x10`), `$CBFF` (`$15 → $70`), `$CC11` (`$17 → $71`); no press-history buffer or multi-press comparator |
| Wrapper System Menu hidden slot | cursor code + dispatcher + 5-item message | **none**; cursor wraps `0..4`, table has 5 entries |
| Secret-code dialog reachability | all 55 message records, all renderer call sites | messages 51–54 exist but are **never drawn** |

### Input-surface completeness

The menu walk covered the title/game menu, gameplay, NES pause, the five-item wrapper System Menu, the link dialog, the save dialog, sleep and reset. No options/config or debug screen exists (`OPTION`/`CONFIG`/`DEBUG`/`TEST` font-code hits = 0). The only multi-button gates are the documented wrapper controls: `L+R` (System Menu), `Select+L+R` (sleep exit) and `Start+Select+A+B` (reset). The remaining gameplay screens (bonus stage, game-over/score) have no text-entry or selector surface: every NES input read in the 16 KiB PRG is enumerated in the table above (`$14`/`$15`/`$17`), and the only selector code in the image is the title mountain selector at `$F53E` plus the wrapper System Menu at `0x08002428`. The only code-entry strings (the secret-code dialog) are unreferenced. This is the bound for “no other menu/code screen”.

## 7. Validation evidence

**Observed**

* Cold boot runs the NES attract/demo (`$53=1`); Start starts a game. Reset (`Start+Select+A+B`) returns to the title (`$53=0`, `$20=0`, `$51=1`).
* Title: Down/Right increment `$59`, Up/Left decrement; `MOUNTAIN 01` at `$59=0`, `MOUNTAIN 32` at `$59=0x1F` (nametable row 20 digit tiles `0x00 0x01` vs `0x03 0x02`).
* Start at `$59=0x1F` yields in-game `$59=0x1F`, `$20=3`, `$53=0`, `$90=4`; Mountain 1 start yields `$59=0`; first-screen tile diff 226/960.
* Wrap tests: `0x1F → 0x00` on Down, `0x00 → 0x1F` on Up/Left; 40-Down sequence never exceeds `0x1F`.
* `L+R` opens the System Menu; NES freezes (`$50` unchanged over 1 s, NES RAM diff 0).
* System Menu cursor rows 27/29/31/33/35 cycle with Down/Up; five items only.
* CONTINUE resumes the NES (NES RAM diff 52 over 1 s). RESET returns to title (`$20=0`, `$90=0`). LINKED PLAY opens the link dialog and freezes the NES (diff 0). SAVE HIGH SCORE shows `PRESS THE B BUTTON TO CANCEL` and then `WAS UNABLE TO SAVE.` (message 46). SLEEP MODE produced no visible freeze/blank in this mGBA build; the NES `$50` kept advancing and the game screen remained; Select+L+R returned.
* Start during play pauses the NES (`$50` unchanged); Start again resumes.

**Derived**

* NES `$F53E`/`$F54D` implements the 5-bit selector; `$DFA5` displays `($59 & 0x1F)+1`; `$C626` copies the saved selection and starts; `$CC7E` increments `$59` and wraps at `0x63`.
* Wrapper `0x08002428`/`0x080025D0`–`0x0800262A`/`0x08002490` implement a 5-item menu with no hidden slot.
* The 46 renderer call sites never pass message IDs 50–54; the secret-code dialog is dead code in this SKU.
* `EEPROM_V124` at `0x239A4` shows an 8 KiB EEPROM save; the save record uses magic `_RBM1`.

**Inferred**

* The second GBA header at `0xCFA0` and the `RFU-MBOOT`/`Sio32ID` strings are the single-pak link-play download image; the `LINKED PLAY` menu item uses it.
* The `$59 > 0x1F` post-clear loop displays `MOUNTAIN 01+` and is the game's mountain-loop behavior; reaching it requires clearing Mountain 32.
* The `SAVE HIGH SCORE` failure under mGBA 0.10.5 is most likely an EEPROM emulation/save-verify mismatch, not a ROM-path bug; it does not affect the cheat conclusion.

## 8. Unknowns

* The `$03FE`/`$59` start path has an implementation nuance: after starting at Mountain 32, `$03FE` read back as `0` even though `$C460` is the only writer. The observable state is reproducible (`$59=0x1F` in-game); the exact write order between `$C460` and `$C626` remains an open implementation detail.
* The `$59 = 0x20..0x62` post-clear loop is derived from `$CC7E`. It is a separate progression path, not part of the 32-value menu input surface; reaching it requires clearing Mountain 32.
* 2-player `LINKED PLAY` needs a second GBA and link cable. The link dialog and the NES freeze were observed; peer-to-peer gameplay is outside this single-console engagement.
* The wrapper's encoding of the NES image at `0x17D6D` (extra/patch bytes versus the runtime EPR image) is only partly decoded. The EWRAM runtime image is the ground truth for every NES claim here.
* The EEPROM save-record layout beyond the `_RBM1` magic and the cause of the emulator save failure remain open; the save path's drawn message set is fully enumerated.

## 9. Tooling

* mGBA 0.10.5 SDL under `Xvfb :251` + `openbox`, `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input.
* mGBA savestates parsed in Python (`zlib`, `struct`); NES nametable/NES RAM and wrapper BG0/BG3 maps rendered to text from VRAM/palette/OAM.
* `da65` 2.18 (cc65) for 6502 disassembly of the EWRAM PRG; `arm-none-eabi-objdump -M force-thumb` and Capstone for the GBA wrapper.
* Custom Python for message-table dumps, BL-target/renderer call-site scans, font-code keyword scans, key-mask run scans, and tile/layout diffs.

## 10. Legal note

No ROM, extracted graphics, music, or game text beyond short menu strings needed as evidence is redistributed. All findings are hashes, addresses, algorithms, and short quotations.
