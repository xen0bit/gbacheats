# Beyblade: G-Revolution (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-26.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Beyblade: G-Revolution/Beyblade: G-Revolution.gba` |
| Size | 4,194,304 bytes (`0x400000`, 4 MiB) |
| Header title | `BEYBLADEGREV` (`0x080000A0`) |
| Game code | `BB2E` (`0x080000AC`) |
| Maker code | `70` (Atari) (`0x080000B0`) |
| Version | `00` (`0x080000BC`) |
| Complement check | stored `0x83`, computed `0x83` |
| Header checksum | stored `0x0000`, computed `0xFA83` |
| Entry branch | `0xEA00002E` → `0x080000C0` |
| Fixed byte `0xB2` | `0x96` |
| Save type string | `EEPROM_V124` present |
| MD5 | `78c34b8026991ab7b0a4990e1af5d9b5` |
| SHA-1 | `a89f7b4eb77dc986022201db51a676451ba7c5e4` |
| SHA-256 | `c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5` |

Embedded-header scan: exactly one 156-byte Nintendo logo, at file offset
`0x4` (header at `0x0`). This is a single GBA image, not a multi-game pack.
**Observation:** the complement byte is correct but the 16-bit header checksum
field at `0xBE` is zero, while the bytes imply `0xFA83`. Title, game code,
maker, logo and entry point are all intact and no trainer/patcher banner
(`POKE`, `PARADOX`, `EURASIA`, `TRAINER`, …) is present. The mismatch is
consistent with a header rebuilt after dumping; no functional patch was found.

ROM addresses below are `0x08000000 + file_offset`. All findings are tied to
this exact hash; other revisions/regions may differ.

---

## 2. Executive summary

**There is no password system and no button-code cheat system in this build.**
The only developer cheat surface is a hidden QA menu labelled **`Test/QA`**,
inserted as a fifth entry in the overworld Start menu.

* The `Test/QA` entry is gated by one byte,
  `*(u8*)(*(u32*)0x03000198 + 0x1850)`. In the analysed state that resolved to
  EWRAM `0x02002054`. The game **initialises this byte to 0** at state setup
  (`0x08046196`); it is the only writer of the `+0x1850` byte found in the ROM,
  and the other three references are the Start-menu readers. It is therefore
  a developer switch, not something a player can set with a password,
  button sequence or save file. With the byte 0 the Start menu has four items;
  with any non-zero value a fifth item, `Test/QA`, is built and selectable.
* The QA menu has **six entries**, all enumerated and exercised:
  `Select level`, `Blader stats editor`, `View characters`, `Level viewer`,
  `Inventory editor`, `Blade editor`.
* `Select level` is backed by an **82-record table** at `0x080BB110`
  `{u32 area_id, u32 spawn_x, u32 spawn_y, char *name}` terminated by
  `0xFFFFFFFF`. All 82 entries were dumped and several were entered in-game.
* TCRF documents this menu but tells the reader to set `0x02001009 = 04`
  (“2001009”). That byte is **not** the gate in this ROM: writing `04` there
  and reopening the menu produced no `Test/QA` entry (**observed**). The real
  gate and its only writer are given above.
* Published “cheat” lists for the game are GameShark/CodeBreaker memory
  patches only; they contain no passwords. The only published button inputs
  are battle controls (`A+B` Engine Gear, `L+R` Bit Beast, `Up+Down+A` /
  `Right+Left+A` combos), i.e. normal combat, not code entry.

The deliverable in §6b is therefore the full characterisation of the QA menu’s
input spaces: gate (1 bit, rejection proven), menu (6 entries), level select
(82 indices, clamp proven), inventory pickers (beyblade list and 4/4/3-item
launcher/ripcord/object lists), and the blade editor (7 fields). Two
unpublished level-warp results are shown: **`Maze end` (index 76, area 0x62)**
and **`Shop in Oz` (index 81, area 0x67)**.

---

## 3. How to reproduce

### Emulator

```bash
sudo apt-get install -y mgba-sdl xvfb xdotool scrot imagemagick gdb-multiarch
Xvfb :182 -screen 0 1024x768x24 &
DISPLAY=:182 openbox &
DISPLAY=:182 SDL_AUDIODRIVER=dummy mgba -3 "Beyblade: G-Revolution.gba" &
```

Default mGBA keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows. Presses held 120–200 ms.

Savestate shipped next to this report: `Beyblade: G-Revolution.ss1`, taken at
the overworld Start menu with the gate byte already set (so `Test/QA` is the
fifth item). mGBA uses Shift+F1..F10 to save and F1..F10 to load.

### Menu path (observed)

```
Copyright/Atari splash
└─ MAIN MENU            NEW GAME / LOAD GAME / OPTIONS
   ├─ OPTIONS           SFX volume / MUSIC volume
   └─ NEW GAME          intro dialogue → Tyson's room (overworld)
      └─ Start          PAUSE MENU
         ├─ Continue
         ├─ Save game   → “Do you want to save the current game?” Yes/No
         ├─ Settings    → Menu color, Text speed, Weather, Tips, Sfx, Music
         ├─ Exit game
         └─ Test/QA     ← only when the gate byte is non-zero
```

To set the gate (analysis only; **not an in-game code**), with
`mgba -g` attached:

```gdb
set $p = *(unsigned int*)0x03000198
set *(unsigned char*)($p+0x1850) = 1     # resolved to 0x02002054 in this state
```

Close and reopen the Start menu; `Test/QA` becomes the fifth entry. Pressing A
on it enters the QA root; B returns to the Start menu; B again resumes play.

### Published material tested

| Source | Claim | Result |
|---|---|---|
| TCRF, *Beyblade G-Revolution* | “Open the start menu, set 2001009 to 04, press A” | **Rejected in this build**: `0x02001009 = 04` produced no fifth entry; actual gate is the `+0x1850` byte above |
| Neoseeker / SuperCheats / almarsguides | GameShark & CodeBreaker codes | Out of scope (memory patches, not in-game codes); names/values match the ROM’s RAM layout but were not used |
| SuperCheats “Unlockables” | `A+B` Engine Gear, `L+R` Bit Beast, `Up+Down+A` hard combo, `Right+Left+A` medium combo | Battle controls, not code entry; no sequence table exists (see §6b bounds) |

`tcrf.net` returned HTTP 403 to a direct fetch; the quoted “set 2001009 to 04”
method was taken from the search-result snippet and then tested in the
emulator as described above. GameFAQs/VGChartz hold no password page for this
title; the only published codes are the GameShark/CodeBreaker patches.

---

## 4. Address map

| File offset | ROM address | What |
|---:|---:|---|
| `0x000000` | `0x08000000` | GBA header (single image) |
| `0x046134` | `0x08046134` | Game-state initialiser; **only writer** of the gate |
| `0x046196` | `0x08046196` | `ldr r1,=0x1850; add; strb 0` → clears the gate |
| `0x052B94` | `0x08052B94` | Pause menu screen (screen id 7) enter/draw |
| `0x053010` | `0x08053010` | Pause-menu item builder; gate test at `0x0805301A` |
| `0x052C98` | `0x08052C98` | Pause-menu A/B handler; jump table at `0x08052D18` |
| `0x052D2C`–`0x052DBE` | `0x08052D2C`–`0x08052DBE` | Five action cases; case 4 → `set_screen(35)` |
| `0x052DE8` | `0x08052DE8` | Pause menu Up (decrement, clamp) |
| `0x052E3C` | `0x08052E3C` | Pause menu Down (increment, 4 vs 5 items) |
| `0x04A0D8` | `0x0804A0D8` | QA root enter; builds six items via `0x0804A350` |
| `0x04A188` | `0x0804A188` | QA root A handler; jump table at `0x0804A200` |
| `0x04A200` | `0x0804A200` | QA dispatch: 31, 34, 36, 37, 38, 39 |
| `0x0B9B68` | `0x080B9B68` | QA root screen struct (screen id 35) |
| `0x0BA1A8` | `0x080BA1A8` | Screen-struct pointer table (54 entries) |
| `0x0BB110` | `0x080BB110` | Debug level table, 82 × 16 bytes |
| `0x0BB630` | `0x080BB630` | Level-table terminator `0xFFFFFFFF` |
| `0x3A92B8`–`0x3A9338` | `0x083A92B8`–`0x083A9338` | Level-name strings |
| `0x3A7384`–`0x3A73DC` | `0x083A7384`–`0x083A73DC` | QA menu labels |
| `0x3A86F4` | `0x083A86F4` | `Test/QA` label (five localisation slots) |
| `0x09960C` | `0x0809960C` | `Test/QA` localisation row (5 pointers) |
| `0x0B9A28` | `0x080B9A28` | Level-select screen struct (screen 31) |
| `0x066F24` / `0x066F68` | `0x08066F24` / `0x08066F68` | Level-list Up / Down |
| `0x0B9B18` | `0x080B9B18` | Blader stats (screen 34) |
| `0x0B9BB8` | `0x080B9BB8` | View characters (screen 36) |
| `0x0B9C08` | `0x080B9C08` | Level viewer (screen 37) |
| `0x0B9C58` | `0x080B9C58` | Inventory editor (screen 38) |
| `0x0B9CF8`–`0x0B9E38` | `0x080B9CF8`–`0x080B9E38` | Inventory sub-screens 40–44 |
| `0x0B9CA8` | `0x080B9CA8` | Blade editor (screen 39) |
| `0x07A1F4` | `0x0807A1F4` | Beyblade record table used by the picker; 0x28-byte stride, first record `Dragoon S` |

RAM used by this path:

| Address | Use |
|---|---|
| `0x03000198` | Pointer to the current game-state block (EWRAM; `0x02000804` in the analysed state) |
| `0x02000804 + 0x1850` = `0x02002054` | **QA menu gate byte** (initialised to 0) |
| `0x03000964` | Current screen id |
| `0x03004060` | Key state word (active-high held keys) |
| `0x03003F60` | Second key-state word (menu/edge use) |
| `0x03000674` / `0x03000678` | Generic list scroll / row |
| `0x03000668` / `0x0300066C` | Inventory selected index / item count |
| `0x03000670` | Inventory count used by the picker |

---

## 5. Algorithm

### 5.1 The gate (0x08053010)

```c
build_start_menu(state, obj) {
    u8 flag = *(u8 *)(*(u32 *)0x03000198 + 0x1850);   // 0x0805301E..22
    if (flag == 0) {                                  // 0x0805302A beq
        add_item(0, row(Continue));                   // 4 items
        add_item(1, row(Save game));
        add_item(2, row(Settings));
        add_item(3, row(Exit game));
    } else {
        add_item(0, row(Continue));                   // 5 items
        add_item(1, row(Save game));
        add_item(2, row(Settings));
        add_item(3, row(Exit game));
        add_item(4, row(Test/QA));                    // 0x0809960C
    }
}
```

The cursor handlers use the same byte to choose the clamp:

```c
// Down, 0x08052E3C
sel = *(u8 *)(obj + 0x2D5) + 1;
limit = (*(u8 *)(state + 0x1850) != 0) ? 4 : 3;
if (sel > limit) sel = 0;
```

The A handler (`0x08052C98`) jumps on `sel`:

| sel | Action | Address |
|---:|---|---|
| 0 | Continue (resume, screen 7 → game) | `0x08052D2C` |
| 1 | Save prompt | `0x08052D84` |
| 2 | Settings (screen 11) | `0x08052D94` |
| 3 | Exit to title | `0x08052DAC` |
| 4 | **QA menu** (`set_screen(35)`) | `0x08052DBE` |

### 5.2 QA menu dispatch (0x0804A188)

```c
// sel at obj+0x2D5, cursor moved by 0x0804A2E8 / 0x0804A31C
switch (sel + 1) {          // jump table 0x0804A200
  case 1: screen = 31; break;   // Select level
  case 2: screen = 34; break;   // Blader stats editor
  case 3: screen = 36; break;   // View characters
  case 4: screen = 37; break;   // Level viewer
  case 5: screen = 38; break;   // Inventory editor
  case 6: screen = 39; break;   // Blade editor
}
set_screen(screen);          // 0x08066390 writes 0x03000964
```

### 5.3 Level select list

* `Select level` enters screen 31 (`0x08066C38`).
* The list walks the 82 records at `0x080BB110`; the cursor is clamped with
  `total-1` (`0x08066F68`: `ldr r0,[obj+0x304]; subs r0,#1; cmp`). The count is
  therefore 82 and index 82 cannot be expressed: pressing Down on the last
  entry is a no-op (**observed**: screenshots 08 and the following press are
  identical).
* A is “select”: it sets the player’s area/spawn from the record and closes the
  QA menu back into gameplay (**observed** for `Maze end` and `Shop in Oz`).

### 5.4 Level viewer (screen 37)

Screen 37’s enter callback (`0x0804D5B0`) restores the camera from the player
position (`0x0300068C`/`0x03000690`) and draws the ordinary map. Selecting
`Level viewer` therefore returns to the current level rather than opening a
separate viewer; no distinct viewer overlay exists in this build (**observed**:
screenshot 19; **derived** from the enter callback).

---

## 6. Tables

### 6.1 Start menu (screen id 7)

| Index | Label | Normal | Gate ≠ 0 |
|---:|---|---:|---:|
| 0 | Continue | ✓ | ✓ |
| 1 | Save game | ✓ | ✓ |
| 2 | Settings | ✓ | ✓ |
| 3 | Exit game | ✓ | ✓ |
| 4 | Test/QA | — | ✓ |

### 6.2 QA menu (screen id 35)

| Index | Label | Screen id | Enter | Update | Input |
|---:|---|---:|---:|---:|---:|
| 0 | Select level | 31 | `0x08066C39` | `0x08066CBD` | `0x08066D05` |
| 1 | Blader stats editor | 34 | `0x0803E475` | `0x0803E531` | `0x0803E5F9` |
| 2 | View characters | 36 | `0x0804D779` | `0x0804D811` | `0x0804D889` |
| 3 | Level viewer | 37 | `0x0804D5B1` | `0x0804D629` | `0x0804D6F9` |
| 4 | Inventory editor | 38 | `0x0804B029` | `0x0804B0E1` | `0x0804B129` |
| 5 | Blade editor | 39 | `0x0804A54D` | `0x0804A67D` | `0x0804A739` |

### 6.3 Inventory editor (screen 38)

Header is `Item N = <type>: <name>`; **D-pad Left/Right** changes `N`. Action
list (cursor at `obj+0x2D5`):

| Index | Action | Sub-screen | Observed contents |
|---:|---|---:|---|
| 0 | Add beyblade | 42 | Scrollable beyblade picker, starts `Dragoon S`; last reachable entry `Rushing Boar`; A adds the highlighted record, picker stays open, B returns |
| 1 | Add launcher | 40 | `Competition launcher`, `Professional launcher`, `Metal launcher`, `Plastic launcher` (4) |
| 2 | Add ripcord | 41 | `Competition ripcord`, `Super long ripcord`, `Extended ripcord`, `Plastic ripcord` (4) |
| 3 | Add blade parts | 44 | Parts picker with sprite column; observed weight disks `6 Balance`, `6 Heavy`, `6 Wide`, `8 Balance`, `8 Heavy`, … (scrollable) |
| 4 | Add object | 43 | `Trunks`, `Towel`, `Goggles` (3) |
| 5 | Delete item | — | Removes the item at the current `Item N`; count and header update |

Duplicate adds are allowed (A can be pressed repeatedly without leaving the
picker): adding `Competition launcher` twice produced `Item 2` and `Item 3`
both named `Competition launcher` (**observed**, screenshot 14).

### 6.4 Blade editor (screen 39)

Header `Blade N - <beyblade> - <owner>`; L/R change blade, Up/Down change field,
Left/Right change value, hint “Use shoulder buttons to change blade”.

| Field | Example (Blade 0) | Edited value (observed) |
|---|---|---|
| Attack ring | Reverse Dragon | — |
| Weight disk | 8 Wide | → `10 Heavy` after 2×Right |
| Blade base | Storm Grip | — |
| Spin direction | Left spin | — |
| Bit chip | Dragoon | — |
| Experience | 0 | — |
| Spin gear | Normal | — |

Blade 1 in the same save: `Dragoon S` / `Chris`, `Holy Despell`, `10 Wide`,
`First Crush Base`, `Left spin`, `Griffolyon`, `0`, `Normal`.

### 6.5 Debug level table (`0x080BB110`, 82 records)

Record: `u32 area_id; u32 spawn_x; u32 spawn_y; char *name`. Terminator
`0xFFFFFFFF`.

| # | id | x | y | Name |
|---:|---:|---:|---:|---|
| 0 | `0x09` | 192 | 152 | Tysons back garden |
| 1 | `0x06` | 112 | 96 | Tysons hallway |
| 2 | `0x05` | 96 | 112 | Tysons room |
| 3 | `0x07` | 144 | 104 | Tysons dining room. |
| 4 | `0x08` | 144 | 104 | Tysons front garden |
| 5 | `0x0A` | 112 | 128 | Tysons dojo |
| 6 | `0x01` | 344 | 136 | Park |
| 7 | `0x00` | 48 | 112 | Alley |
| 8 | `0x02` | 128 | 128 | Shops |
| 9 | `0x03` | 256 | 256 | Playing field |
| 10 | `0x04` | 992 | 304 | Woods |
| 11 | `0x0B` | 128 | 128 | Maxs house front |
| 12 | `0x0C` | 152 | 152 | Max's kitchen |
| 13 | `0x1E` | 64 | 160 | Max's shop |
| 14 | `0x0D` | 128 | 128 | Kenny's house |
| 15 | `0x0E` | 80 | 160 | Kenny's lounge |
| 16 | `0x11` | 280 | 160 | Tokyo Airport |
| 17 | `0x12` | 128 | 128 | BBA HQ Front |
| 18 | `0x13` | 136 | 168 | BBA HQ Foyer |
| 19 | `0x14` | 128 | 128 | BBA HQ Meeting room |
| 20 | `0x15` | 104 | 168 | BBA HQ Practice area |
| 21 | `0x16` | 128 | 208 | Changing room |
| 22 | `0x17` | 248 | 160 | Pool foyer |
| 23 | `0x18` | 56 | 152 | Pool gym |
| 24 | `0x19` | 440 | 288 | Pool |
| 25 | `0x1A` | 272 | 128 | Pool front |
| 26 | `0x1B` | 304 | 152 | Stadium - Arena |
| 27 | `0x1D` | 184 | 128 | Stadium - front |
| 28 | `0x22` | 112 | 384 | Stadium - changing room |
| 29 | `0x23` | 112 | 168 | Stadium - foyer |
| 30 | `0x24` | 104 | 152 | Stadium - gym |
| 31 | `0x25` | 224 | 256 | Stadium - corridor |
| 32 | `0x27` | 272 | 288 | NY - airport |
| 33 | `0x29` | 128 | 128 | Shop in tokyo |
| 34 | `0x2E` | 128 | 128 | NY - arena |
| 35 | `0x2F` | 128 | 128 | NY - changing room |
| 36 | `0x30` | 224 | 256 | NY - corridor |
| 37 | `0x31` | 128 | 128 | NY - gym |
| 38 | `0x33` | 128 | 128 | NY - Stadium front |
| 39 | `0x5A` | 128 | 128 | NY - Stadium foyer |
| 40 | `0x36` | 128 | 128 | Madrid - airport |
| 41 | `0x38` | 128 | 128 | Madrid - arena |
| 42 | `0x39` | 128 | 128 | Madrid - changing room |
| 43 | `0x3A` | 224 | 256 | Madrid - corridor |
| 44 | `0x3B` | 128 | 128 | Madrid - gym |
| 45 | `0x3C` | 128 | 128 | Madrid - foyer |
| 46 | `0x3D` | 128 | 128 | Madrid - front |
| 47 | `0x40` | 128 | 128 | Rome - airport |
| 48 | `0x41` | 128 | 128 | Rome - stadium front |
| 49 | `0x42` | 128 | 128 | Rome - arena |
| 50 | `0x43` | 128 | 128 | Rome - changing room |
| 51 | `0x44` | 224 | 256 | Rome - corridor |
| 52 | `0x45` | 128 | 128 | Rome - gym |
| 53 | `0x46` | 128 | 128 | Rome - Foyer |
| 54 | `0x48` | 128 | 128 | Egypt - airport |
| 55 | `0x4A` | 128 | 128 | Egypt - arena |
| 56 | `0x4B` | 128 | 128 | Egypt - changing room |
| 57 | `0x4C` | 224 | 256 | Egypt - corridor |
| 58 | `0x4D` | 128 | 128 | Egypt - gym |
| 59 | `0x4E` | 112 | 168 | Egypt - foyer |
| 60 | `0x4F` | 128 | 128 | Egypt - s/front |
| 61 | `0x51` | 128 | 128 | Oz - airport |
| 62 | `0x53` | 128 | 128 | Oz - arena |
| 63 | `0x54` | 128 | 128 | Oz - changing room |
| 64 | `0x55` | 224 | 256 | Oz - corridor |
| 65 | `0x56` | 128 | 128 | Oz - gym |
| 66 | `0x57` | 128 | 128 | Oz - Foyer |
| 67 | `0x58` | 128 | 128 | Oz - s/front |
| 68 | `0x59` | 128 | 128 | Neighbourhood HUB |
| 69 | `0x5B` | 128 | 128 | Maze 1 |
| 70 | `0x5C` | 128 | 128 | Maze 2 |
| 71 | `0x5D` | 128 | 128 | Maze 3 |
| 72 | `0x5E` | 128 | 128 | Maze 4 |
| 73 | `0x5F` | 128 | 128 | Maze 5 |
| 74 | `0x60` | 128 | 128 | Maze 6 |
| 75 | `0x61` | 128 | 128 | Maze start |
| 76 | `0x62` | 128 | 128 | Maze end |
| 77 | `0x63` | 128 | 128 | Shop in New york |
| 78 | `0x64` | 128 | 128 | Shop in Madrid |
| 79 | `0x65` | 128 | 128 | Shop in Rome |
| 80 | `0x66` | 128 | 128 | Shop in Egypt |
| 81 | `0x67` | 128 | 128 | Shop in Oz |

The out-of-order placement of `NY - Stadium foyer` (id `0x5A`) at index 39 is
in the ROM table itself.

---

## 6b. Enumeration

### 6b.1 What the “system” is

There is no text-entry password surface (`password` occurs 0 times in the
whole ROM; the game has EEPROM saves). The only developer code-like input
space is the **QA menu gate plus its menu/list inputs**. That is what is
enumerated here.

### 6b.2 Space definition

| Space | Size | Encoding | Evidence |
|---|---:|---|---|
| QA gate | 1 byte | 0 = hidden, non-zero = visible | `0x0805301A`–`0x0805302A`; initialiser `0x08046196` |
| Start menu | 4 or 5 entries | cursor 0..3 / 0..4 | `0x08052E3C` clamp |
| QA menu | 6 entries | cursor 0..5 | jump table `0x0804A200` |
| Level select | **82** entries | index 0..81, clamps at 81 | table `0x080BB110`, count `obj+0x304` |
| Beyblade picker | scrollable list | record stride 0x28, starts at `0x0807A1F4` (`Dragoon S`), ends at `Rushing Boar` | `0x0804D260` clamp `#0x51`; observed |
| Launcher picker | 4 | `Competition`, `Professional`, `Metal`, `Plastic` | screen 40 |
| Ripcord picker | 4 | `Competition`, `Super long`, `Extended`, `Plastic` | screen 41 |
| Object picker | 3 | `Trunks`, `Towel`, `Goggles` | screen 43 |
| Blade editor | 7 fields | list/step per field | screen 39 |

### 6b.3 Novel results (not in any published list)

No site publishes the `Test/QA` label, the 82-row level table, or any of these
warps. The following were produced by the analysis and entered in the
emulator:

| Input | Result | Screenshot |
|---|---|---|
| QA level index **76** = `Maze end`, area id `0x62` | warp into the unused forest “Maze end” map (Tyson, Max and a pickup on screen) | `evidence/07-level-list-maze-end.png`, `evidence/07b-level-warp-maze-end.png` |
| QA level index **81** = `Shop in Oz`, area id `0x67` | warp into the Oz shop interior | `evidence/08-level-list-last-shop-in-oz.png`, `evidence/09-level-warp-shop-in-oz.png` |
| Inventory: Add beyblade → `Dragoon G` | inventory count 1 → 2, `Item 1 = Beyblade: Dragoon G` | `evidence/14-inventory-added-items.png` |
| Inventory: Add launcher ×2 | duplicate `Competition launcher` at items 2 and 3 | `evidence/14-inventory-added-items.png` |
| Blade editor: weight disk `8 Wide` → `10 Heavy` | field changes live | `evidence/16-blade-editor-weightdisk-edit.png` |
| Blader stats: Level `2` → `4` (2×Right) | stat editable | `evidence/11-blader-stats-level-2to4.png` |

### 6b.4 Bounds proven by rejection

| Test | Expected if unbounded | Observed |
|---|---|---|
| Gate byte = 0, reopen Start menu | `Test/QA` still listed | **4 items only** (`evidence/03-pause-menu-4-items-flag0.png`) |
| Gate byte ≠ 0 | 5 items | **`Test/QA` appears** (`evidence/04-pause-menu-5-items-flag1.png`) |
| `0x02001009 = 04` (TCRF address) | debug menu | **no change**; the byte is unrelated to the gate |
| Down on level index 81 (`Shop in Oz`) | index 82 | **no movement**; cursor clamps at 81 (screenshot 08 unchanged after the press) |
| Down on the last beyblade (`Rushing Boar`) | another entry | **no movement**; the row after it is an uninitialised read from the adjacent parts table (`evidence/17-beyblade-picker-last-item.png`) |
| Any index outside 0..81 in the level list | warp to an out-of-table area | not expressible: the table is terminated and the cursor is clamped |

**Negative result on button cheats.** The full 4 MiB was scanned for arrays of
≥4 consecutive 16-bit GBA key masks (`1,2,4,8,10,20,40,80,100,200` and short
combinations): **37 candidate runs**, only **2** are referenced by a 32-bit
pointer, and **none** of those reference sites is within `0x200` of the 62 code
references to the key-state words (`0x03003F60`/`0x03004060`). The four
key-handling functions with ≥3 mask immediates all test single bits
(A/B/D-pad) with no progress counter. This matches the absence of any
button-code menu label in the string bank. The published `A+B`, `L+R`,
`Up+Down+A`, `Right+Left+A` inputs are combat controls and remain in-game
mechanics, not cheat codes.

**Negative result on passwords.** `strings -n 4` yields **66,921** entries.
Case-insensitive counts: `password` **0**, `cheat` **0**, `debug` **0**,
`unlock` **3** (all `GF_*_UNLOCKED` script flags), `secret` **10** (all
dialogue), `code` **1** (leftover log string `resizeSpriteBlock: Reduce. Code
needs writing.`). There is no alphabet table, no NUL-padded equal-length code
bank, and no string-compare validator.

---

## 7. Validation evidence

### Observed (emulator screenshots / live state)

* Start menu with four items, no `Test/QA` (flag 0).
* Start menu with five items, `Test/QA` selectable (flag non-zero).
* QA root with the six labels; each sub-screen opened.
* `Select level` list, `Maze end`, `Shop in Oz`, and warps into both the
  Maze-end forest map and the Oz shop interior.
* Level cursor stops at index 81; beyblade cursor stops at `Rushing Boar`.
* Blader stats Level 2 → 4 by Right.
* Inventory add/duplicate/delete and the count changing.
* Blade editor field edit `8 Wide` → `10 Heavy`.
* In-game Settings screen with six rows; title OPTIONS with two rows.

Screenshots: `evidence/01`–`evidence/20`, plus `evidence/07b`.

### Derived (code)

* The gate is exactly `*(u8*)(*(u32*)0x03000198 + 0x1850) != 0`
  (`0x0805301A`–`0x0805302A`); the same byte selects the 4-vs-5 clamp
  (`0x08052E3C`).
* The only reference to the `+0x1850` byte besides the Start-menu readers is
  the state initialiser at `0x08046196`, which stores **0**. Hence there is no
  in-game trigger.
* QA dispatch table `0x0804A200` maps the six entries to screens
  31/34/36/37/38/39.
* Level table has 82 records and a `0xFFFFFFFF` terminator at `0x080BB630`.
* Screen 37 is the normal map view: its enter callback restores camera from
  player coordinates.

### Inferred

* The zeroed 16-bit header checksum at `0xBE` is a post-dump header rebuild;
  no functional patch was observed.
* The garbage row after `Rushing Boar` is the picker’s draw loop reading one
  record past the end of the beyblade list (the next records are spin-gear
  names such as `Engine Gear`).

---

## 8. Unknowns

* The exact original purpose of the `+0x1850` byte is not documented; it is
  cleared on state init and never set by shipped code. It may have been a
  build-time switch.
* The full beyblade picker list length is not proven beyond the observed last
  entry (`Rushing Boar`) and the `#0x51`-style clamp; the underlying record
  table continues into the parts tables, so “82” here is a UI bound, not a
  record-table end.
* The `+0x1850` byte’s address in other regional/revision builds was not
  tested (this is the USA `BB2E` Rev 0 image). TCRF’s `0x02001009` may belong
  to a different build or to a different state block.
* The battle-time Start overlay was not exercised in this save because no
  opponent was armed. No separate battle-pause builder exists in the ROM: the
  only screen that builds `Continue`/`Save game`/`Settings`/`Exit game` is
  screen 7 (`0x08053010`), so an in-battle overlay would reuse it. This does
  not affect the code/cheat-surface result.

---

## 9. Tooling

| Item | Purpose |
|---|---|
| `grev_tables.py` | dumps identity, gate expression, QA screen structs, all 82 level records and picker head |
| `arm-none-eabi-objdump -M force-thumb` | Thumb disassembly of the menu/QA code |
| Capstone 5.0.7 | PC-relative literal scan, key-mask run scan, key-state xref proximity check |
| mGBA 0.10.5 (SDL) + Xvfb `:182` + openbox | ground-truth emulator |
| `xdotool` + ImageMagick `import` | scripted keys and 720×480 screenshots |
| `gdb-multiarch` + mGBA `-g` | read `0x03000198`, set/inspect the gate byte |

No ROM, graphics, music or game text is redistributed here; only addresses,
tables, hashes and screenshots of menu states.

---

## Legal note

Analysis performed on a locally owned ROM image. No copyrighted assets are
included; the report contains addresses, algorithms, our own tables and
screenshots of menu states for documentation.
