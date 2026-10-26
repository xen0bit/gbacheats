# Bomberman Max 2: Red Advance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Bomberman Max 2: Red Advance/Bomberman Max 2: Red Advance.gba` |
| Size | 8,388,608 bytes (`0x800000`, 8 MiB) |
| Header title (`0xA0`) | `MAX2-REDADV` (11 chars + NUL) |
| Game code (`0xAC`) | `AMYE` |
| Maker (`0xB0`) | `5G` (Hudson Soft) |
| Main unit / device (`0xB3`/`0xB4`) | `0x00` / `0x00` |
| Software version (`0xBC`) | `00` |
| Complement check (`0xBD`) | `0xAE` (recomputed `0xAE` — valid) |
| Header checksum (`0xBE`) | `0x0000` (not a valid complement word) |
| Entry word (`0x00`) | `0xEA1D7CFE` → ARM branch to `0x0875F400` (patched; see below) |
| MD5 | `b95e907343855ea923dae38e3bb44f95` |
| SHA-1 | `30411d1231b13b39752dce69dd14c31399fdacda` |
| SHA-256 | `41fa91dc9943f49330397cc005492152bf1fd183598b2d8aaf13816fcbeaef99` |

`0xEA1D7CFE` is `b` with imm24 `0x1D7CFE`; the ARM target is
`0x08000008 + (0x1D7CFE << 2) = 0x0875F400`.

### Patch / trainer note

The image is **not a clean commercial dump**. It carries the same Mode7
cracktro as the Blue edition:

* The header entry word is patched; a clean image would branch to
  `0x080000C0` (`0xEA00002E`). The original crt0 at `0x080000C0`
  (`12 00 a0 e3 00 f0 29 e1 ...`) is intact.
* At file `0x75F400` (ROM `0x0875F400`) there is an appended ARM block,
  `0x75F400`–`0x762FA9` (last non-`0xFF` byte). It is entered in ARM
  mode, sets `SP=0x03007F00`, switches to Thumb, programs DMA
  (`0x040000D4`, control `0x85000000`) and then jumps to the literal at
  file `0x75F464`, which is `0x080000C0`.
* Cracktro text at file `0x762EFA`: `MODE7 PRESENTS`, `ON 05/31/2002`,
  `BOMBERMAN MAX 2`, `RED ADVANCE`, `FROM MAJESCO`, `AND HUDSON`,
  `GBA/USA/64MBS`, `SUPPLIED BY:`, `DROPCOM!`, `GREETINGS TO`,
  `JEFF'S MOM`, `AKA THE MILFOB`.
* **No trainer menu or gameplay modification was found.** The block
  contains no reference to `0x04000130`, `0x03005DE0` or `0x03005DE4`.
  (A byte pattern equal to `0x04000130` occurs at unaligned file
  `0x75F6CB`; it is data, not an instruction literal.) The intro has no
  choices and control returns to the original crt0.
* The 16-byte header fields `0xA0`–`0xBD` have a valid complement but the
  `0xBE` header-checksum word is `0x0000`; the Blue image is the same, so
  both were rebuilt by the same tool. It does not affect execution.

### Embedded GBA header (single-pak child, not a second game)

A whole-file scan for the 156-byte Nintendo logo found exactly **two**
headers: the main header at `0x0` and a second at `0x734868`.

* Nintendo logo at `0x73486C`; title `MAX2-REDADV`, code `AMYE`,
  maker `5G`, complement `0xAE`.
* Entry `0xEA00002E` → `0x08734928` (base + `0xC0`).
* The child image spans `0x734868`–`0x75F341` (last non-`0xFF` byte),
  followed by `0xFF` padding up to the Mode7 block at `0x75F400`.
* This is the multiboot / single-pak child image downloaded to the second
  GBA, not a second game and not a multi-game pack.

### Save hardware

mGBA created an **8,192-byte (64 Kbit) `.sav`** — EEPROM, not SRAM/Flash.
Progress (cleared areas, Charaboms) is battery-saved; the game never
displays a password. This is the structural reason a password system is
unnecessary, and it matches the Blue edition.

---

## 2. Executive summary

**No in-game password system, no button cheat, and no reachable debug menu
exists in this ROM.** Red is a normal EEPROM-save title built from the same
engine as Blue:

* A whole-ROM case-insensitive search finds **zero** occurrences of
  `password`, `pass`, `cheat`, `debug`, `secret`, `unlock`, `code`,
  `hidden`, `extra`, `sound`, `option` or `continue`. The only ASCII UI
  bank outside the cracktro is the link-mode minigame/bonus selector plus
  the `BOMBERMAN-MAX2` save-slot names.
* The reachable menus are: title (four items), Normal Game area-objective
  screen, gameplay, the **in-level pause menu** (`Resume Game` / `End Game` /
  `Save`, opened with **Select**), the `Save?` confirmation, the three-file
  save list, Game Over, the Rating Notice, the `Continue` menu, Battle Game
  file select and the `Pitch Area` link lobby, and Single-Pak Link. There is
  no password screen, no alphabet keyboard, no options screen and no debug
  screen.
* The only simultaneous multi-button gate in the parent game's code is the
  standard **A + B + Select + Start → BIOS SoftReset** check at
  `0x0800E9D0`. It was confirmed in mGBA (the Mode7 intro replays). Every
  tested subset (L+R+Start, Select+Start, A+B+Start, A+B+Select) is
  rejected (no reset).
* The only published in-game secrets are gameplay unlocks (100 jump-rope
  jumps → **Th. Liger** in Red, Turtle King in Blue). The OCR of the
  official 84-page English/French manual contains no `password`, `code` or
  `secret` occurrence. Public Action Replay / CodeBreaker lists are memory
  edits and out of scope.

### Is Red "the same build with a palette/level swap"? No — verified.

Red and Blue are **separate builds of a shared engine**, not one binary with
different colours:

| Check | Red | Blue |
|---|---|---|
| Header title / game code | `MAX2-REDADV` / `AMYE` | `MAX2BLUEADV` / `AMHE` |
| Different bytes vs the other image | 6,556,362 / 8,388,608 = **78.16 %** | — |
| 1 KiB blocks identical at the same offset | 693 / 8192 (8.5 %) | — |
| Multiboot header offset | `0x734868` | `0x7306EC` |
| Mode7 block offset | `0x75F400` | `0x75B400` |
| ASCII minigame bank | `0x6DC2C` | `0x6DAE0` (+`0x14C` shift) |
| Mode table | `0x0806D8E0`, 44 entries | `0x0806D794`, 43 entries |
| Per-frame key scan | `0x08001D70` — **byte-identical** | `0x08001D70` — same bytes |
| Soft-reset gate | `0x0800E9D0` — identical except BL displacement | `0x0800E980` |
| Dispatcher | `0x0800E9FC` — identical except pool/BL | `0x0800E9AC` |

So: the engine's input path, reset gate and dispatcher are literally the
same machine code, but the data layout, link/multiboot payload, Mode7 block
placement and at least one mode handler differ, and the images are 78 %
different. Red is a distinct build, not a palette swap of the Blue file.
The 78 % figure is dominated by data blocks (graphics/level/pointer tables)
moving; several code regions are byte-identical at the same addresses
(e.g. `0x1A4A`–`0x2518`, `0x1D70` key scan).

### Finding not in the Blue report

The Blue report states that Start shows a menu-less `PAUSE` freeze and that
no pause menu exists. In Red that is only half the story: Start draws the
`PAUSE` marker, but **Select opens a real pause menu**
(`Resume Game` / `End Game` / `Save`), exactly as the manual describes
("Select: Displays the Pause Menu Screen"). Verified in Red
(`ev07`, `ev08`, `ev21`, `ev22`). The same manual covers both editions, so
the Blue report's menu list is probably incomplete too, but only Red was
tested here.

Because there is no validator and no input alphabet, there is no novel
password to mint. The deliverable is the **bounded negative** required by
guide §0.2 item 5: the menu space, the text space, the alphabet space and
the button space are enumerated below, with accepted and rejected inputs
recorded.

---

## 3. How to reproduce

### Emulator and display

```bash
export DISPLAY=:195
export SDL_AUDIODRIVER=dummy
Xvfb :195 -screen 0 1280x900x24 &
DISPLAY=:195 openbox &
DISPLAY=:195 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 \
  "roms/Bomberman Max 2: Red Advance/Bomberman Max 2: Red Advance.gba" &
W=$(DISPLAY=:195 xdotool search --name mGBA | head -1)
DISPLAY=:195 xdotool windowfocus "$W"
```

mGBA 0.10.5 (`mgba-sdl`), 3× scale (720×480 window), 1280×900 Xvfb.

### Keymap (mGBA SDL defaults)

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |
| Fast-forward | `Tab` |

Hold keys 120–300 ms. Save/load state with `Shift+F1` / `F1`. A
title-screen state is kept at
`roms/Bomberman Max 2: Red Advance/Bomberman Max 2: Red Advance.ss1`.

### Boot path

1. Mode7 cracktro (~50 s at 1×; `Tab` makes it ~10 s), auto-advances.
2. Hudson/Majesco story intro: `Start` skips it.
3. Title/menu: `Normal Game`, `Battle Game`, `Pitch Area`,
   `Single-Pak Link`.
4. `Normal Game` → Area Objective screen (`Garden Stage 1-01`,
   "Receive Charaboms through the Teleporter!") → A advances → gameplay.
5. In gameplay, `Start` = `PAUSE` freeze only; **`Select` = pause menu**.
6. Game Over → A → Rating Notice → A → `Continue` menu.

### Menu paths tested

| Path | Result |
|---|---|
| Title → Normal Game | area objective `1-01` → gameplay (save resumed) |
| Title → Battle Game | `Pitch Area` file select (`File 1/2/3`, 0 %) |
| Battle file select → File 1 | `Pitch Area` lobby: `Select Area! GardenStage`, `Waiting for opponent.` |
| Title → Pitch Area | the same file select and lobby |
| Title → Single-Pak Link | two-GBA `Checking…` screen (loops with no cable) |
| Gameplay → Start | `PAUSE` marker, no menu (`ev06`) |
| Gameplay → Select | pause menu `Resume Game` / `End Game` / `Save` (`ev07`) |
| Pause → End Game | `Save? Yes/No` (`ev08`); No ends the game → intro |
| Pause → Save | three-file save list (`File 1/2/3`, 0 %) → `Saved!` (`ev21`, `ev22`) |
| Game Over → A → A | Rating Notice → `Continue` menu (`ev10`, `ev11`) |
| Continue → Save | three-file save list, `Saved!` (`ev12`) |
| Title → Select / L / R | no change (`ev19` tests L+R+Start) |
| Title → GBC 12-press sound-test code → A | no sound test; A started Normal Game (`ev16`, `ev17`) |
| Gameplay → A+B+Select+Start | BIOS SoftReset; Mode7 intro replays (`ev18`) |
| Gameplay → L+R+Start / Select+Start / A+B+Start / A+B+Select | no reset (`ev20` for Select+Start; A+B+Select opens pause) |

Evidence screenshots (720×480 mGBA window, in `/tmp/opencode/bmaxred/`):

| File | Content |
|---|---|
| `ev01_mode7_red.png` | Mode7 cracktro, `RED ADVANCE` text |
| `ev02_story_intro.png` | Hudson story intro (Planet Bomber / Bomber Base) |
| `ev03_title_menu.png` | four-item title menu |
| `ev04_area_objective.png` | Area Objective, Garden Stage 1-01 |
| `ev05_gameplay.png` | gameplay |
| `ev06_pause_overlay.png` | Start → `PAUSE` marker, no menu |
| `ev07_pause_menu.png` | Select → pause menu (Resume Game / End Game / Save) |
| `ev08_pause_endgame_confirm.png` | End Game → `Save? Yes/No` |
| `ev09_game_over.png` | Game Over |
| `ev10_rating_notice.png` | Rating Notice, area clear rate 0 % |
| `ev11_continue_menu.png` | Continue / End Game / Save |
| `ev12_save_file_list.png` | File 1/2/3 save list |
| `ev13_battle_file_select.png` | Battle Game → Pitch Area file select |
| `ev14_pitch_lobby.png` | Pitch Area lobby, Waiting for opponent |
| `ev15_singlepak_check.png` | Single-Pak Link `Checking…` |
| `ev16_gbc_code_rejected_before.png` | after the GBC 12-press code, still on title |
| `ev17_gbc_code_rejected_after.png` | final A started Normal Game instead |
| `ev18_softreset_after_4button.png` | A+B+Select+Start → Mode7 intro replays |
| `ev19_title_lrs_rejected.png` | L+R+Start on title: no change |
| `ev20_selectstart_no_reset.png` | Select+Start in gameplay: no reset |
| `ev21_pause_save_list.png` | Select → Save: three-file list |
| `ev22_pause_saved.png` | save confirmation `Saved!` |
| `ev23_abselect_pause.png` | A+B+Select: pause menu, no reset |
| `ev24_abstart_pause.png` | A+B+Start: `PAUSE` marker, no reset |
| `ev25_lrstart_no_reset.png` | L+R+Start in gameplay: no reset |
| `ev26_title_selectstart.png` | Select+Start on title: no change |

---

## 4. Address map

File offset → ROM address is `rom_address = 0x08000000 + file_offset`.
All values are little-endian.

### Header, patch, embedded image

| File offset | ROM address | Meaning |
|---:|---:|---|
| `0x000000` | `0x08000000` | ARM entry branch `0xEA1D7CFE` → `0x0875F400` |
| `0x0000C0` | `0x080000C0` | original crt0 entry, intact |
| `0x734868` | `0x08734868` | embedded multiboot header (single-pak child) |
| `0x75F400` | `0x0875F400` | Mode7 cracktro entry (ARM) |
| `0x75F444` | `0x0875F444` | stack literal `0x03007F00` |
| `0x75F464` | `0x0875F464` | literal `0x080000C0` (return to game) |
| `0x762EFA` | `0x08762EFA` | `MODE7 PRESENTS` text |

### Input

| Address | Meaning |
|---:|---|
| `0x04000130` | GBA `KEYINPUT` (active-low) |
| `0x08001D70` | per-frame key scan: reads `KEYINPUT`, inverts it (identical to Blue) |
| `0x08000598` | boot/multiboot helper: when `*(u8*)r3 == 2`, held A triggers `RegisterRamReset(0xE0)` and a jump to `0x08000000` |
| `0x03005DE0` | `u16` held keys, active-high (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`) |
| `0x03005DE4` | `u16` newly pressed keys (`held & ~prev`) |
| `0x0800E9D0` | multi-button gate: held `& 0xC == 0xC`, `& 1`, `& 2` → SoftReset |
| `0x08067574` | BIOS SoftReset trampoline: clears two bytes, `mov sp`, `svc 1`, `svc 0` |
| `0x08739AA4` | the child image's own copy of the key scan (literal `0x04000130` at `0x08739AC4`) |

Only two `KEYINPUT` reads exist in the parent image (`0x08000598` boot
helper, `0x08001D70` scan); the multiboot child carries its own copy at
`0x08739AA4`. This matches Blue and bounds the entire input surface.

### Screen state machine

| Address | Meaning |
|---:|---|
| `0x03002248` | `u16` current screen/mode index |
| `0x0806D8E0` | table of 44 mode handlers (`0x00`–`0x2B`), one `u32` each |
| `0x0800E9FC` | dispatcher: `handler = table[*(u16*)0x03002248]; blx handler` |
| `0x0800E9D0` | soft-reset check called once per frame from the dispatcher path |
| `0x030050D0` | `u32` flag checked by the boot helper (`0` = allow the A reset) |
| `0x0806D990` | start of the following unrelated table (`0x080Cxxxx` pointers) |

Mode table entries (thumb pointers, `|1`, printed as stored):

```
00 0800ea21  01 0800eb71  02 0800eb75  03 0800ed5d
04 0800efd5  05 0800f2fd  06 0800f325  07 0800f4b9
08 0800f515  09 0800f56d  0a 0800f7b5  0b 0800f82d
0c 0800f831  0d 0800f84d  0e 0800fc7d  0f 080100cd
10 080100f9  11 08010355  12 080103dd  13 080103e1
14 080103e5  15 080103e9  16 080103ed  17 0801052d
18 080109b9  19 08010ccd  1a 08010e59  1b 08010f39
1c 080112f9  1d 080112fd  1e 08011301  1f 080119b9
20 080119d5  21 080119f9  22 08011369  23 08011461
24 08011649  25 08011665  26 0801183d  27 08011879
28 08011885  29 080118c9  2a 08011939  2b 0801193d
```

`0x2A`/`0x2B` are 2-byte stubs (`bx lr; nop`), i.e. unused slots in this
build (Blue has live code at `0x2A`). `0x23`, `0x24`, `0x25` all enter the
minigame/bonus selector family.

### Minigame / bonus-game selector (link mode)

| Address | Meaning |
|---:|---|
| `0x08011460` | mode `0x23` handler; draws `MINIGAME SELECT` list |
| `0x08011648` | mode `0x24` handler; draws both lists, reads held+pressed |
| `0x08011664` | mode `0x25` entry into the same drawing path |
| `0x03004A3C` | category: `== 2` → minigame list, otherwise bonus-game list |
| `0x0800E6D8` | ASCII text draw helper (only 21 BL callers, all `0x0801151A`–`0x08011798`) |
| `0x0806DC2C` | `"MINIGAME SELECT"` |
| `0x0806DC3C` | `"NAWATOBI"` |
| `0x0806DC48` | `"MATOATE"` |
| `0x0806DC50` | `"KENKENPAPA"` |
| `0x0806DC5C` | `"NAKAMASAGASI"` |
| `0x0806DC6C` | `"BONUSGAME SELECT"` |
| `0x0806DC80` | `"BAROMDARAKE"` |
| `0x0806DC8C` | `"MOGURAHOREHORE"` |
| `0x0806DC9C` | `"JUMPRACE"` |
| `0x0806DCA8` | `"BLOCKKICK"` |

### ASCII / text

| Address | Meaning |
|---:|---|
| `0x0806BA94` | `"BOMBERMAN-MAX2"` save-file name (4 xrefs) |
| `0x0806BD94` | `"BOMBERMAN-MAX2"` (save slot 2) |
| `0x0806C094` | `"BOMBERMAN-MAX2"` (save slot 3) |
| `0x08067D60` | `"AMYJ"` (Japanese game-code string used by the link/save code) |
| `0x0806CCB4` | `"AMYJ"` (second copy) |
| `0x08078144` | `"battle mode programming by fuzzball"` (developer credit, no literal xref) |
| `0x0806D7F9`, `0x0806D819` | ASCII→tile row tables for the ASCII draw path |
| `0x08175BE0`–`0x08175C5F` | font tile-index table (ASCII 0x00–0x7F) |
| `0x0806A130`, `0x0806A150` | `"MultiSioSync4Sio32Load"`, `"Sio32MultiLoad"` (SIO library banners; a duplicate copy sits at `0x08751C84`) |

### Save

| Item | Value |
|---|---|
| `.sav` size | 8,192 bytes (EEPROM 64 Kbit) |
| Save slots | 3 (`File 1/2/3`), each listing clear % |
| Save UI | pause menu (`Select`) → Save; game-over `Continue` → Save |

---

## 5. Algorithm

### 5.1 Per-frame input scan (`0x08001D70`)

```c
uint16_t raw     = *(volatile uint16_t*)0x04000130;  // active-low
uint16_t held    = (~raw) & 0x03FF;
uint16_t pressed = held & ~prev_held;               // 0x03005DE4
*(uint16_t*)0x03005DE4 = pressed;
*(uint16_t*)0x03005DE0 = held;
prev_held = held;
```

This function is **byte-identical** to the Blue image at the same address,
so key mapping and semantics are shared.

### 5.2 Soft-reset gate (`0x0800E9D0`)

```c
uint16_t held = *(uint16_t*)0x03005DE0;
if ((held & 0x000C) == 0x000C &&   // Select + Start
    (held & 0x0001) != 0 &&        // A
    (held & 0x0002) != 0) {        // B
    soft_reset();                  // 0x08067574 -> svc 1; svc 0
}
```

Identical to Blue except for the BL displacement. This is the only
simultaneous chord applied to the key state in the parent image.

A whole-ROM scan for the `movs rD,#imm / ands rD,rS / cmp rD,#imm`
multi-bit-compare shape returns 15 sites. Only `0x0800E9D6` is fed by the
held-key word; the others read object/direction bytes or state words
(`0x0800A222`, `0x0801ABCC`, `0x0801AC92`, `0x0801AD78`, `0x0801AE50`,
`0x08058BA6`, `0x08062AA0`, `0x08062B3E`, `0x08062C12`, `0x08062CEC`,
`0x08064C22`, `0x08302BDE`). In addition, 16 literal sites load
`0x03005DE0` (held) and 71 load `0x03005DE4` (pressed); all are ordinary
single-button menu navigation or gameplay movement.

### 5.3 Screen dispatcher (`0x0800E9FC`)

```c
void dispatch(void) {
    uint16_t mode = *(uint16_t*)0x03002248;
    void (*handler)(void) = (void(*)(void))mode_table[mode]; // 0x0806D8E0
    handler();
    check_soft_reset();                                      // 0x0800E9D0
}
```

### 5.4 ASCII selector (modes `0x23`–`0x25`)

```c
void screen_23(void) {
    setup_bg_and_palette();
    if (*(uint16_t*)0x03004A3C == 2) {
        draw_text(8, 2, "MINIGAME SELECT");
        draw_text(5, 6, "NAWATOBI");      draw_text(5, 8, "MATOATE");
        draw_text(5,10, "KENKENPAPA");    draw_text(5,12,"NAKAMASAGASI");
    } else {
        draw_text(8, 2, "BONUSGAME SELECT");
        draw_text(5, 6, "BAROMDARAKE");   draw_text(5, 8,"MOGURAHOREHORE");
        draw_text(5,10, "JUMPRACE");      draw_text(5,12,"BLOCKKICK");
    }
}
```

This is a link-mode menu. It has no password entry and sets no flags.
Only these three modes call the ASCII text helper, so the ASCII bank is
fully accounted for.

### 5.5 Password validator

There is none. No routine in the ROM reads a character buffer, measures a
password length, compares against a code table, or computes a checksum over
typed characters. The evidence is bounded in §6 and §6b:

* the text space has no password/cheat/code/debug string;
* the only ASCII drawer is the link selector (21 call sites, contiguous);
* there is no input alphabet: the only ascending symbol tables are font
  rows (`0x0806D7F9`, `0x0806D819`, `0x08175xxx`, duplicated at
  `0x08076C10`, `0x08747BC5`, `0x08751F30`), not a code alphabet;
* there is no table of candidate codes;
* no mode handler outside the link selector family references a character
  table or the ASCII drawer.

### 5.6 Pause menu (observed)

`Start` in gameplay draws the `PAUSE` marker and freezes the game but opens
no menu. `Select` opens the pause menu, which behaves like the game-over
menu:

```c
Resume Game -> return to play
End Game    -> "Save? Yes/No"; Yes -> save file list, No -> end game
Save        -> "File 1/2/3" list -> "Saved!"
```

The handler's mode index was not pinned (the mGBA GDB stub did not accept a
connection in this build), but the behaviour and every menu item were
observed directly.

---

## 6. Tables

### 6.1 Title / main menu

Exactly four items; the cursor clamps at the bottom (four Downs from the
first item leave the cursor on `Single-Pak Link`):

1. `Normal Game`
2. `Battle Game`
3. `Pitch Area`
4. `Single-Pak Link`

`Battle Game` and `Pitch Area` both lead to the same `Pitch Area`
file-select (`File 1/2/3`, each 0 %) and then to the `Pitch Area` lobby
(`Select Area! GardenStage`, stage list, `Waiting for opponent.`).

### 6.2 Pause / game-over menus

| Menu | Items |
|---|---|
| Pause (`Select`) | `Resume Game`, `End Game`, `Save` |
| Game Over → `Continue` | `Continue`, `End Game`, `Save` |
| `End Game` confirm | `Save?` → `Yes` / `No` |
| Save | `File 1`, `File 2`, `File 3` (0 % each) |

### 6.3 Minigame / bonus-game labels (ASCII, ROM-resident)

| Address | String |
|---:|---|
| `0x0806DC2C` | `MINIGAME SELECT` |
| `0x0806DC3C` | `NAWATOBI` |
| `0x0806DC48` | `MATOATE` |
| `0x0806DC50` | `KENKENPAPA` |
| `0x0806DC5C` | `NAKAMASAGASI` |
| `0x0806DC6C` | `BONUSGAME SELECT` |
| `0x0806DC80` | `BAROMDARAKE` |
| `0x0806DC8C` | `MOGURAHOREHORE` |
| `0x0806DC9C` | `JUMPRACE` |
| `0x0806DCA8` | `BLOCKKICK` |

### 6.4 Button masks

| Button | Mask |
|---|---:|
| A | `0x001` |
| B | `0x002` |
| Select | `0x004` |
| Start | `0x008` |
| Right | `0x010` |
| Left | `0x020` |
| Up | `0x040` |
| Down | `0x080` |
| R | `0x100` |
| L | `0x200` |

### 6.5 Keyword search counts

Whole-ROM, case-insensitive byte counts:

| Keyword | Count | Notes |
|---|---:|---|
| `password` | 0 | — |
| `pass` | 0 | — |
| `cheat` | 0 | — |
| `debug` | 0 | — |
| `secret` | 0 | — |
| `unlock` | 0 | — |
| `code` | 0 | — |
| `hidden` | 0 | — |
| `extra` | 0 | — |
| `sound` | 0 | — |
| `option` | 0 | — |
| `continue` | 0 | — |
| `bonus` | 1 | only `BONUSGAME SELECT` |
| `minigame` | 1 | only `MINIGAME SELECT` |
| `select` | 2 | the two selector titles |

`strings -t x -n 4` produced 49,417 lines. Printable-run counts: 47,893
runs of ≥4 bytes, 8,139 of ≥8, 2,849 of ≥12; 13,125 unique alphabetic
tokens of length ≥4. None is a password, cheat, debug or secret label.

390 valid GBA LZ77 (`0x10`) blocks were found and decompressed
(7,888,602 bytes total); none contained `password`, `cheat`, `debug`,
`secret`, `unlock`, `code`, `select`, `bonus`, `sound`, `option` or
`continue`.

Only 112 printable runs have a literal pointer somewhere in the image. The
ASCII ones are all accounted for — header fields (`AMYE5G`, `AMYJ`),
`BOMBERMAN-MAX2` save names, the ten minigame labels, SIO library banners —
and the rest are 4-byte coincidences inside pointer tables and graphics
data.

### 6.6 Alphabet space

A scan for ascending byte runs ≥16 (the shape of an alphabet/input table)
returns 18 runs, all font/glyph rows and tilemaps:

| Offsets (ROM) | Meaning |
|---|---|
| `0x0806D7F9`, `0x0806D819` | ASCII→tile rows used by the selector text path |
| `0x080715C8` | `PQRSTUVWXYZ[\]^_` font row |
| `0x08076C10`, `0x08076C20`, `0x08751F30` | duplicate font rows |
| `0x08175CC0`–`0x08175CE0` | main font tile-index table |
| `0x0819C092`, `0x081AD1B4`–`0x081B0A45`, `0x081AF6B8`–`0x081AF8F4` | graphics gradients |
| `0x08747BC5`, `0x08747BE5` | copy of the ASCII rows in the Mode7/intro bank |

There is no 26/32/36-symbol code alphabet and no fixed-length code buffer.

### 6.7 Red vs Blue build comparison (detail)

| Property | Red | Blue |
|---|---|---|
| Entry word | `0xEA1D7CFE` → `0x0875F400` | `0xEA1D6CFE` → `0x0875B400` |
| Mode7 block | `0x75F400`–`0x762FA9` | `0x75B400`–`0x75EFA9` |
| Cracktro line 3 | `RED ADVANCE` | `BLUE ADVANCE` |
| Multiboot header | `0x734868` | `0x7306EC` |
| Minigame bank | `0x6DC2C` | `0x6DAE0` |
| Mode table | `0x0806D8E0`, 44 entries | `0x0806D794`, 43 entries |
| Mode 0x2A/0x2B | stubs (`bx lr`) | live handler at 0x2A |
| Soft-reset gate | `0x0800E9D0` | `0x0800E980` |
| Dispatcher | `0x0800E9FC` | `0x0800E9AC` |
| Key scan | `0x08001D70` | `0x08001D70` (identical bytes) |
| Save | 8 KiB EEPROM | 8 KiB EEPROM |

Closest-match check: 6,556,362 bytes differ (78.16 %); 693 of 8,192
aligned 1 KiB blocks are byte-identical at the same offset. Code regions
such as `0x1A4A`–`0x2518` and the key scan are byte-identical, which is
consistent with one source tree linked into two products with different
data placement, not with a palette swap.

---

## 6b. Enumeration

### 6b.1 Space definition

| Space | Definition | Size / result |
|---|---|---|
| Password space | alphabet × length × checksum | **0** — no entry screen, no alphabet table, no length check, no validator |
| Button-sequence space | 10 buttons, ordered sequences and simultaneous chords | one simultaneous gate on the key state: `0x00F` (A+B+Select+Start) → SoftReset. No ROM sequence table, no per-press progress counter. |
| Menu space | reachable screens | 15 screens walked (§6b.4); link/stage-gated screens enumerated statically |
| Link minigame space | 4 minigames + 4 bonus games | 8 entries, all named and addressed in §6.3; link-gated |
| Unlockable space | gameplay counters/flags | Red: 100 jump-rope jumps → Th. Liger; Blue: → Turtle King. Gameplay, not a code. |
| Charabom slots | 30 slots, 2 unused | slots 29/30 (Fly Shark, Elemouse) are documented on TCRF as RAM flags; memory edit, out of scope |
| Save space | 3 EEPROM files | 8,192-byte `.sav`; no password needed |

No password alphabet exists. The only long printable tables are font/tile
maps and the ten link-selector labels; there is no 26/32/36-symbol code
alphabet and no fixed-length code buffer.

### 6b.2 Novel codes

**None can be minted, because no code validator exists.** This is not an
unfinished search: the negative is established by

1. an empty text space (`password`/`cheat`/`code`/`debug`/`secret`/
   `unlock` = 0 in both the raw image and 390 decompressed LZ77 blocks, and
   in the 84-page official manual in English and French),
2. an empty alphabet space (18 ascending tables, all font rows; no input
   alphabet),
3. a fully disassembled input path with exactly one multi-button gate on
   the key state (the hardware SoftReset),
4. a fully walked reachable menu tree with no password or debug entry,
5. a save system that makes passwords unnecessary (8 KiB EEPROM, 3 files),
6. the complete public record: GameFAQs, a Japanese Bomberman compendium
   and the manual list only the jump-rope unlock; no code or password is
   published for either edition.

The closest thing to an unpublished discovery is a *UI* fact rather than a
code: the in-level pause menu is reached with **Select**, not Start (Start
only shows the `PAUSE` marker). It is undocumented on the Blue report's
menu list and is confirmed here in the emulator (`ev07`) and by the
manual's control table. It contains no code entry.

### 6b.3 Bounds proven by rejection

| Input | Where | Result |
|---|---|---|
| A+B+Select+Start (`0x00F`) | gameplay | **accepted**: BIOS SoftReset, Mode7 intro replays (`ev18`) |
| A+B+Select (`0x007`) | gameplay | **rejected as reset**: no reset; the Select component opens the pause menu (`ev23`) |
| A+B+Start (`0x00B`) | gameplay | **rejected as reset**: no reset; Start shows the pause marker (`ev24`) |
| Select+Start (`0x00C`) | gameplay | **rejected**: no reset, no menu (`ev20`) |
| L+R+Start (`0x308`) | gameplay | **rejected**: no reset, game resumes (`ev25`) |
| L+R+Start (`0x308`) | title | **rejected**: no change (`ev19`) |
| Select+Start (`0x00C`) | title | **rejected**: no change (`ev26`) |
| GBC predecessor sound-test sequence: R,L,R,R,L,L,R,L,R,L,L,R then A | title | **rejected**: no sound test; the final A selected Normal Game (`ev16`, `ev17`) |
| L / R with an empty Charabom list | gameplay | **rejected**: no Charabom screen (manual: L/R only with Charaboms owned) |
| Start | gameplay | no code path: draws `PAUSE` only (`ev06`) |

The Select+Start and L+R+Start results are the important bounds: `0x00C`
and `0x308` are subsets/supersets of the accepted chord's button set, but
they are rejected, so the gate requires exactly all four bits A+B+Select+
Start (`0x00F`).

The 12-press GBC code is the strongest published-code test: it is the
documented sound-test code of the two Game Boy Color predecessors
(`Bomberman Max: Blue Champion` / `Red Challenger`) and it does nothing in
this GBA build — statically, the 12-mask sequence
`0x10,0x20,0x10,0x10,0x20,0x20,0x10,0x20,0x10,0x20,0x20,0x10` does not
occur anywhere in the image as `u16` or bytes.

### 6b.4 Screens walked (completeness)

| # | Screen | Reached by | Evidence |
|---|---|---|---|
| 1 | Mode7 cracktro | boot | `ev01` |
| 2 | Story intro (Planet Bomber / Bomber Base) | cracktro end | `ev02` |
| 3 | Title menu (4 items) | intro end / Start | `ev03` |
| 4 | Area Objective (Garden Stage 1-01) | Normal Game | `ev04` |
| 5 | Gameplay | A on area objective | `ev05` |
| 6 | `PAUSE` overlay | Start | `ev06` |
| 7 | Pause menu | Select | `ev07` |
| 8 | `Save?` confirmation | Pause → End Game | `ev08` |
| 9 | Save file list | Pause → Save / Continue → Save | `ev12`, `ev21` |
| 10 | Game Over | dying in gameplay | `ev09` |
| 11 | Rating Notice | A on Game Over | `ev10` |
| 12 | Continue menu | A on Rating Notice | `ev11` |
| 13 | Battle Game file select (`Pitch Area`) | Title → Battle Game | `ev13` |
| 14 | Pitch Area lobby | select File 1 | `ev14` |
| 15 | Single-Pak Link `Checking…` | Title → Single-Pak Link | `ev15` |

Statically enumerated but not enterable without a second GBA or cleared
progress:

* Stage Selection and Area Selection (manual p.11; require a completed
  stage),
* Battle setup: Player Selection, Match Selection, Charabom Selection,
  Rules Setup, Tactic Option (require Charaboms or a link peer),
* Battle **Merge** (requires two Charaboms),
* the minigame/bonus selector (modes `0x23`–`0x25`, link only).

None of these is a password/code gate; all are tournament/setup screens
whose code and labels are mapped in §4–§6.

---

## 7. Validation evidence

### Observed (emulator)

* Mode7 cracktro with `RED ADVANCE` plays from the patched entry and hands
  control to the original game (`ev01`, `ev18`).
* Hudson story intro, then the four-item title menu (`ev02`, `ev03`).
* Normal Game → garden stage `1-01` area objective → gameplay
  (`ev04`, `ev05`).
* Start freezes the game and draws only `PAUSE`; Select opens the pause
  menu (`ev06`, `ev07`); End Game shows `Save? Yes/No` (`ev08`).
* Save writes `File 1` and prints `Saved!`; the three-file list shows 0 %
  (`ev12`, `ev21`, `ev22`).
* Game Over → Rating Notice (`0 %`, "Work Harder!") → Continue menu
  (`ev09`–`ev11`).
* Battle Game → `Pitch Area` file select → lobby with
  `Connecting…`/`Waiting for opponent.` (`ev13`, `ev14`).
* Pitch Area → the same file select/lobby.
* Single-Pak Link → two-GBA `Checking…` screen (`ev15`).
* A+B+Select+Start resets; the Mode7 intro replays (`ev18`).
* L+R+Start, Select+Start, A+B+Start and A+B+Select do not reset
  (`ev19`, `ev20`, `ev23`–`ev26`).
* The GBC 12-press sound-test sequence does nothing; A then starts
  Normal Game (`ev16`, `ev17`).
* An 8,192-byte `.sav` is created (EEPROM).

### Derived (disassembly)

* `0x08001D70` is the per-frame key scan; `0x03005DE0`/`0x03005DE4` hold
  held/pressed state. Byte-identical to Blue.
* `0x0800E9D0` is the only simultaneous multi-button gate on that state;
  it calls the SoftReset trampoline at `0x08067574`.
* `0x0806D8E0` is a 44-entry handler table indexed by `0x03002248`;
  `0x0800E9FC` is the dispatcher.
* `0x08011460`/`0x08011648` are the minigame/bonus selector handlers; the
  ASCII draw helper `0x0800E6D8` has only 21 callers, all inside them.
* The Mode7 block is ARM, sets its own stack, DMAs, and returns to
  `0x080000C0`; the original crt0 is intact. It reads no keys.
* The embedded header at `0x734868` is a multiboot child image, not a
  second game.
* `0x08000598` is a boot/multiboot helper: when a byte is `2`, held A
  calls `RegisterRamReset(0xE0)` and jumps to `0x08000000`. Single-button
  reset helper, not a cheat sequence.

### Inferred

* The minigame/bonus selector is link-only. Its mode-table position, the
  battle category variable `0x03004A3C`, and the six-cart link labels
  support this, but it was not reached in single-cart play.
* Battle setup/merge screens are downstream of a link peer or of owning
  two Charaboms; the manual documents them but they were not exercised.
* The jump-rope unlock is a gameplay counter, not a code; it was not
  performed (it requires 100 consecutive jumps in the link minigame).
* The 78 % byte difference is dominated by moved data blocks; no attempt
  was made to identify every moved block.

---

## 8. Unknowns

* The pause-menu mode index and its handler address were not pinned
  (the `mgba -g` GDB stub in this build did not accept a connection; the
  menu was proven by observation and the manual).
* The 44 mode handlers were classified only by their literals/calls, not
  mapped one-by-one to named screens.
* Link-gated screens (battle setup, merge, minigame selector) were not
  entered; their entry points and static code/labels are documented, and
  the single-pak child was not exercised beyond its own key-scan copy.
* Stage/Area Selection screens require a cleared stage and were not
  reached.
* The original (pre-cracktro) header title cannot be recovered without a
  clean dump; `MAX2-REDADV` may be the scene group's rewrite.
* The two unused Charaboms are reachable by RAM flags documented on TCRF;
  no in-game unlock was found and memory edits are outside scope.

---

## 9. Tooling

* `mgba-sdl` 0.10.5 (`/usr/games/mgba`) under Xvfb `:195` + openbox,
  3× scale.
* `arm-none-eabi-objdump -D -b binary -marm -M force-thumb` (and default
  ARM mode for the Mode7 entry).
* Python 3 + Capstone 5.0.7, scripts in `/tmp/opencode/bmaxred/`:
  * `phase0.py`, `phase0b.py` — hashes, header, complement, logo/header
    scan, ROM diff statistics.
  * `scan1.py`, `lit.py` — literal-pointer and pointer-run scans.
  * `rtool.py`, `hdetail.py`, `handlers.py` — Thumb disassembly with
    resolved PC-relative literals; per-mode-handler profile.
  * `chords.py` — whole-ROM `movs imm / ands / cmp imm` chord-pattern
    scan (15 hits, 1 on the key state).
  * `masks.py` — button-mask sequence scan.
  * `lz.py` — GBA LZ77 (`0x10`) scanner/decompressor (390 blocks).
  * `k.py` — xdotool key helper; `shot.sh` — window screenshot.
* `strings`, `xxd`, `md5sum`, `sha1sum`, `sha256sum`, ImageMagick,
  `xdotool`, `scrot`, `pdftoppm` + `tesseract` (manual OCR), `pdftotext`.
* Official manual: `gamegear.net` scan, 84 pages (English + French),
  OCR'd locally.

Reproduction of the static claims:

```bash
# 1. header + hashes
xxd -l 0x200 game.gba
md5sum game.gba; sha1sum game.gba; sha256sum game.gba

# 2. keyword counts (all zero except bonus/minigame/select)
python3 - <<'PY'
rom = open("game.gba","rb").read().lower()
for k in (b"password",b"pass",b"cheat",b"debug",b"secret",b"unlock",b"code"):
    print(k, rom.count(k))
PY

# 3. input scan, reset gate, dispatcher
python3 rtool.py d 0x08001d70 20
python3 rtool.py d 0x0800e9d0 20
python3 rtool.py d 0x0800e9fc 14

# 4. mode table and selector
python3 handlers.py
python3 hdetail.py 0x08011460

# 5. build comparison (hash/diff statistics)
python3 phase0b.py

# 6. LZ77 sweep
python3 lz.py
```

---

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed with this
report. Only hashes, addresses, short menu labels needed for
identification, and the analyst's own screenshots of menu states are
included. The ROM remains the property of its rights holders.
