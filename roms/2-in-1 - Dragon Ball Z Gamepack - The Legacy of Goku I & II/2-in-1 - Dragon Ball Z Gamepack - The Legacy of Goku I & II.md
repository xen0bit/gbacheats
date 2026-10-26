# 2-in-1: Dragon Ball Z Gamepack — The Legacy of Goku I & II (GBA) — Reverse Engineering Report

## 1. Target identity

**File analysed:**
`roms/2-in-1 - Dragon Ball Z Gamepack - The Legacy of Goku I & II/2-in-1 - Dragon Ball Z Gamepack - The Legacy of Goku I & II.gba`

| Property | Value |
|---|---|
| Size | 16,777,216 bytes (0x1000000, 16 MiB) |
| MD5 | `be0ec0dc899635edd6ad0c74574aa826` |
| SHA-1 | `f02d179accbeb9b68bcaef8720eb0ae426dde6ee` |
| SHA-256 | `7d1d76efc87df45d9a8f9eca57769d252bef21a79025555e4882a9c7025a51ca` |
| `file(1)` | Game Boy Advance ROM image: "DBZLEGACY1&2" (BLFE70, Rev.00) |

The file is a **multi-game cartridge**: three GBA headers, each identified by the
156-byte Nintendo logo at header+4 (the logo was searched as a byte string over the
whole file; hits at file offsets `0x4`, `0x40004`, `0x800004`, i.e. header bases
`0x0`, `0x40000`, `0x800000`).

| Header base | File range | Header title | Game code | Maker | Ver | Entry word | Role |
|---:|---|---|---|---|---:|---|---|
| `0x0000000` | `0x0`–`0x3FFFF` (256 KiB) | `DBZLEGACY1&2` | `BLFE` | `70` | 0 | `0xEA00002E` | launcher / game selector |
| `0x0040000` | `0x40000`–`0x7FFFFF` (7.75 MiB) | `DBZ LGCYGOKU` | `ALGE` | `70` | 0 | `0xEA00002E` | **Legacy of Goku I** |
| `0x0800000` | `0x800000`–`0xFFFFFF` (8 MiB) | zeros | zeros | `01` | 0 | `0xEA00002E` | **Legacy of Goku II** |

Notes:

* The third image's `0x800000` header has valid logo, `0x96` at `0xB2`, and a valid
  branch, but the title/game-code bytes are zeroed and the header checksum bytes are
  `F0 00` (not a valid complement pair). This is a pack-build artifact: the image is
  still a full standalone game image, and its Nintendo logo is byte-identical to the
  first image's.
* ROM address of any byte in a sub-image = `0x08000000 + file_offset`. Thus the first
  game's data starts at `0x08040000` and the second game's at `0x08800000`.
* The launcher at `0x0` is built with Webfoot's WinGBA-derived engine core; it contains
  debug-path strings such as `Q:\WinGBACore\GBARam.cpp` (file `0xAA4`),
  `Q:\WinGBACore\SoundChannel.cpp` (`0x115C`), `FrameBuffer.cpp` (`0x2684`),
  `IInputSource.cpp` (`0x3340`). It draws the "DRAGON BALL Z I / II" selector and
  jumps into the chosen image. It has no code system of its own.

## 2. Executive summary

**There is exactly one developer cheat that is reachable in-game in this cartridge:
the Legacy of Goku I debug menu.** It is opened with a button chord, and it contains
five actions rather than the four that every published list names.

* **Legacy of Goku I — debug menu (confirmed in emulator).**
  On the Options screen, put the cursor on **Text Speed**, then **hold L + R + Up and
  press A** (`KEYINPUT` mask `0x0341`). The Options screen can be reached two ways:
  1. title screen → **Options**, and
  2. in-game pause menu → **Options** (this second entry point is not in any published
     description and was confirmed here).
  The debug menu that appears has five rows, in this order:

  | Row | Label | Action | Internal counter bound (derived) | Observed on-screen maximum |
  |---:|---|---|---|---|
  | 0 | `Go To Map` | warps into the game at a map entry | `< 41`, i.e. 42 entries (`0x08040C56: cmp r1,#41`) | `42` |
  | 1 | `Sprite Viewer` | opens the character animation-set viewer | selection handled inside the viewer | — |
  | 2 | `Play SFX` | plays a sound effect from the SFX sample table | `< 30`, i.e. 31 entries (`0x08040CA4: cmp r1,#30`) | `36` (see §8) |
  | 3 | `Play Music` | plays a music track; B/R/L adjust volume | `< 17`, i.e. 18 tracks (`0x08040CE2: cmp r1,#17`) | `17` |
  | 4 | `Show Image` | opens the 15-image art gallery | `< 14`, i.e. 15 images (`0x08040D78: cmp r1,#14`) | `14` |

* **Legacy of Goku II — debug menu exists but is not in-game reachable in this build.**
  The second image contains the developer sound/map test (`Music Test: %d`,
  `Sample Test: %d`, `Map Test`, `Zone: %d`, `Area: %d`, `Variation: %d / %d`,
  `Debug` at `0x08805AF4`–`0x08805B68`) and its code (`0x088058E6`, `0x08805B84`,
  `0x08805C2C`). The only published access (TCRF) is a CodeBreaker RAM write
  `0202B32D:02` followed by holding Start — a memory-edit cheat, out of scope here.
  Writing `0x02` to `0x0202B32D` during startup and holding Start at the title (or at
  Select Game) **did not open the menu in this 2-in-1 build**; no in-game button chord
  was found. This is reported as a bounded negative (§6b, §7).

* **No password/passcode system exists in either game.** Both games use battery saves
  (save-slot menus in both halves). The keywords `password`, `cheat`, `code`,
  `unlock`, `secret code`, `sound test`, `level select` are absent from both halves as
  ASCII (table in §6b). The only cheat-like string in the whole ROM is `Debug`
  (`0x805B68`) in the second image.

* **Published lists reproduce only partly.** The widely published instruction
  ("Options → Text Speed → hold L+R+Up → A") is correct; the published *contents*
  ("Level Select, Sound Test, Sprite Viewer, Photo Gallery", 4 items) undercounts the
  menu by one: the ROM has separate `Play SFX` and `Play Music` rows plus
  `Go To Map`, `Sprite Viewer`, `Show Image`.

## 3. How to reproduce

### Emulator and keymap

```
Xvfb :108 -screen 0 1024x768x24 &
DISPLAY=:108 openbox &
DISPLAY=:108 SDL_AUDIODRIVER=dummy mgba -3 rom.gba &
```

mGBA 0.10.5 (SDL). Default keymap used (verified against the title/options screens):

| GBA | key | GBA | key |
|---|---|---|---|
| A | `x` | L | `a` |
| B | `z` | R | `s` |
| Start | `Return` | Select | `BackSpace` |
| D-pad | arrow keys | | |

The GBA viewport is the 720×480 client area (3× 240×160); screenshots were taken with
`scrot` and cropped `720x480+153+164` after `xdotool getwindowgeometry` on the mGBA
window. Hold keys 120–200 ms; the debug menu polls the key state **every frame**, so a
held direction keeps incrementing (this is why rapid/held presses overshoot).

### Exact path — Legacy of Goku I debug menu

1. Boot the cartridge. The launcher shows the `I` / `II` screen. Press **A** on `I`.
2. Wait through the Atari/Bird Studio/Toei screens; press **Start** at the attract
   sequence to reach the title menu (`New Game / Continue / Options`).
3. Choose **Options**. The screen shows `Text Speed`, `Music Volume`, `SFX Volume`,
   `Exit`.
4. With the cursor on **Text Speed**, hold **L + R + Up** and press **A**.
5. The debug menu replaces the options panel. Its five rows are controlled with
   Up/Down; Left/Right change the row's number; A executes.

The same chord works from the **in-game pause menu → Options** (Start → `Options` →
cursor on `Text Speed` → hold L+R+Up + A).

The debug screen has **no cancel path**: B does nothing, and the screen persists until
a row is executed (e.g. a map warp, which starts the game at level 1) or the console is
reset. Row values are held in RAM and persist when the menu is reopened from the
in-game Options.

### Exact path — Legacy of Goku II menus

Launcher → `II` → title → Start → `Select Game` (3 slots) → `New Game` → intro →
Start → pause tabs `STATUS / ITEMS / OPTIONS / JOURNAL` (L/R cycle). Options here is
`Text Speed / Sound FX Volume / Music Volume / Sleep / Credits`. The LOG1 chord does
**not** open anything in LOG2 (tested on both the title Options and the in-game
Options; the screen simply closes).

### Savestates used

`rom.ss1` = LOG1 debug menu immediately after opening (Row 0 value `01`, all other
rows `00`), `rom.ss2` = Legacy of Goku II intro point. Both are emulator states in the
work directory, not part of the ROM.

### Screen evidence

The curated screenshots are stored next to this report in `evidence/`; the complete
working set was produced in `/tmp/opencode/dbzlegacy/shots/` with the same filenames.
All are 720×480 crops of the 3× GBA viewport.

| File | Content |
|---|---|
| `004_title2.png` | launcher I/II selector |
| `013_title.png`, `019.png` | LOG1 title, main menu |
| `022_optmenu2.png` | LOG1 Options (title path) |
| `031_debug_try2.png` | **debug menu opened from title Options** |
| `196_ingame_debug.png` | **debug menu opened from in-game Options** |
| `033_gotomap2.png` | warp row 0 value `01` → Kame House |
| `178_warp37b.png`, `315_warp42b.png` | warp values `37` and `42` → Kami's Lookout |
| `225_sprite_view.png`, `226_sprite_scroll.png`, `227_sprite_scroll2.png` | Sprite Viewer list and preview |
| `img_00.png` … `img_14.png` | all 15 gallery images, in order |
| `181_pause2.png`, `182_inventory.png`, `187_attacks2.png`, `236_quests.png`, `195_opts2.png` | LOG1 pause: Quests/Inventory/Attacks/Save/Options/Exit |
| `302_up.png` | debug rows at their maxima (`42 / 36 / 17`) |
| `173_img_maxval.png` vs `174_img_right_after_max.png` | image row at `14`, RIGHT produces no change (diff is only the blinking cursor) |
| `280_v4.png` vs `290_map_after42.png` | map row at `42`, RIGHT produces no change |
| `233_LR_only.png` | L+R + A (no Up) → no debug menu |
| `234_LRD_only.png` | L+R+Down + A → no debug menu |
| `107_ii_t3.png`, `109_ii_options2.png`, `144_filesel.png` | LOG2 title, Options, Select Game |
| `211_pause_ii2.png`, `213_items.png`, `216_options_ii.png` | LOG2 pause tabs Status/Items/Options |
| `219_ii_debug_in_game2.png` | LOG2 chord attempt → no debug menu |

## 4. Address map

All addresses are GBA ROM addresses (file offset = address − `0x08000000`).

### Launcher (0x000000–0x03FFFF)

| Address | Meaning |
|---|---|
| `0x08000000` | header, `DBZLEGACY1&2` / `BLFE` / `70` |
| `0x08000AA4` | `Q:\WinGBACore\GBARam.cpp` |
| `0x0800115C` | `Q:\WinGBACore\SoundChannel.cpp` |
| `0x08002684` | `Q:\WinGBACore\FrameBuffer.cpp` |
| `0x08003340` | `Q:\WinGBACore\IInputSource.cpp` |

### Legacy of Goku I (0x040000–0x7FFFFF)

| Address | Meaning |
|---|---|
| `0x08040000` | header, `DBZ LGCYGOKU` / `ALGE` / `70` |
| **`0x08040BFE`** | **debug-menu per-frame handler (Thumb)**; `push {r3,r4,r5,lr}`, `r0` = menu object |
| `0x08040C30` | 5-entry jump table (`u16` offsets/2) for rows 0–4 |
| `0x08040C3A` | row 0 body — `Go To Map` (map table lookup + warp) |
| `0x08040C78` | row 1 body — `Sprite Viewer` (`ldr r0,=0x03000924; bl 0x0804991C`) |
| `0x08040C88` | row 2 body — `Play SFX` |
| `0x08040CC6` | row 3 body — `Play Music` (also volume keys) |
| `0x08040D5C` | row 4 body — `Show Image` |
| `0x08040C56` | `cmp r1,#41` — map counter increment bound (bytes `29 29`) |
| `0x08040CA4` | `cmp r1,#30` — SFX counter bound (bytes `1e 29`) |
| `0x08040CE2` | `cmp r1,#17` — music counter bound (bytes `11 29`) |
| `0x08040D78` | `cmp r1,#14` — image counter bound (bytes `0e 29`) |
| `0x08040E1C` | literal `0x03003E44` — pointer to the processed key-state halfword |
| `0x08040E20` | literal `0x0820A3C8` — map pointer table |
| `0x08040E28` | literal `0x08600CD0` — SFX sample table |
| `0x08040E2C` | literal `0x085D2100` — music track table |
| `0x08040E30`–`0x08040E3C` | `0x03003E2E / 0x03003E2D / 0x03003E2F / 0x03003E32` — volume/flag bytes |
| `0x08040E40`–`0x08040E48` | `0x03003C94 / 0x03003C90 / 0x03003CA0` — gallery state bytes |
| `0x08050070` | debug-menu descriptor: `01 00 03 00 12 00 13 00 05 00 00 00` + 5 pointers |
| `0x0805007C` | **5 pointers to menu item descriptors** (see §6) |
| `0x08602F30`–`0x08602F97` | the five item descriptor records and their strings |
| `0x0820A3C8` | map pointer table, 42 × `u32` (see §6) |
| `0x08600CD0` | SFX table, 31 × 12 bytes |
| `0x085D2100` | music table, 18 × 12 bytes |
| `0x085118B8` | Options menu descriptor (`03 00 01 00 0a 00 04 00`), 4 pointers at `0x0851190` |
| `0x0857ACD0`–`0x0857AD14` | Options item descriptors (`Exit`, `Music Volume`, `SFX Volume`, `Text Speed`) |
| `0x085117C` | `Low\0Medium\0High\0` (Text Speed values) |
| `0x03003E44` | IWRAM: processed key-state halfword (bit0=A, bit4=Left, bit5=Right …) |
| `0x030000D8` | IWRAM menu/screen object seen at handler entry |

The Options item table and strings are plain ASCII (unlike most in-game UI, which is
font-tile encoded), which is why they were found by `strings`.

### Legacy of Goku II (0x800000–0xFFFFFF)

| Address | Meaning |
|---|---|
| `0x08800000` | header, title/game-code zeroed, logo valid, maker `01` |
| `0x08805AF4` | `Music Test: %d` |
| `0x08805B04` | `Sample Test: %d` |
| `0x08805B18` | `Map Test` |
| `0x08805B24` | `Zone: %d` |
| `0x08805B30` | `Area: %d` |
| `0x08805B3C` | `Variation: %d / %d` |
| `0x08805B68` | `Debug` |
| `0x088058E6` | debug sound-test handler (frame loop); list bound `cmp r0,#43` at `0x0880592C` |
| `0x08805B84` | text-draw helper that formats `Music Test: %d` via text bank `0x088E1668 + 0x24C` |
| `0x08805C2C` | second debug helper (map/zone/variation display) |
| `0x08C094E0` | LOG2 music record table, 56-byte stride, 44 records (0–43) |
| `0x088E2CD0`–`0x088E2E00` | LOG2 options/menu ASCII string block (`Select Game`, `Options`, `Text Speed`, `Sound FX Volume`, `Music Volume`, `Credits`, `Journal`, `Status`, `Items`, …) |

## 5. Algorithm

### 5.1 The debug-menu gate (button chord)

The menu is a normal engine screen; its handler is entered per frame with `r0` = a
screen object (`r4`). Input arrives pre-processed in a halfword at `[0x03003E44]`.
The handler tests individual bits: `lsls r0,r0,#31 / lsrs …` for A (bit 0),
`lsls #27` for Left (bit 4), `lsls #26` for Right (bit 5).

The *opening* condition is the published chord: with the Options screen active and
the cursor on `Text Speed`, **L (0x0200) + R (0x0100) + Up (0x0040) + A (0x0001) =
0x0341**. Observations:

* L+R+A (`0x0301`) → no debug menu; the Text Speed value changes normally.
* L+R+Down+A (`0x0381`) → no debug menu; the Down is processed normally (cursor moves).
* L+R+Up+A on LOG1 Options → debug menu (both from the title and from the in-game
  pause Options).
* The same chord in LOG2 options → nothing (the options screen closes).

The chord is a screen-transition check, not a table lookup; no u16 mask table exists
for it (see §6b for the searches).

### 5.2 Debug-menu handler (Legacy of Goku I)

Reimplementation-level pseudocode (`0x08040BFE`; Thumb):

```
keys = *(u16*)0x03003E44            # A=bit0, Left=bit4, Right=bit5, ...
sel  = menu->[4]                    # 0..4
switch (sel):
 case 0:                            # Go To Map
   if (keys & LEFT)  and map  > 0:  map -= 1
   if (keys & RIGHT) and map  < 41: map += 1
   if (keys & A):
       p = *(u32*)(0x0820A3C8 + map*4)   # 0x34-byte map descriptor
       warp(p->mapdata + 0x28)           # 0x08042FBC / 0x08041F9C
 case 1:                            # Sprite Viewer
   if (keys & A): open_viewer(0x03000924)      # 0x0804991C
 case 2:                            # Play SFX
   if (keys & LEFT)  and sfx > 0:  sfx -= 1
   if (keys & RIGHT) and sfx < 30: sfx += 1
   if (keys & A): play(0x08600CD0 + 12*sfx)    # 0x0804AE18
 case 3:                            # Play Music
   if (keys & LEFT)  and mus > 0:  mus -= 1
   if (keys & RIGHT) and mus < 17: mus += 1
   if (keys & A): play(0x085D2100 + 12*mus)    # 0x0804A74A
   if (keys & bit1): volume_down(0x0804A70C)
   if (keys & bit8): volume_up(0x0804A714); copy 0x03003E2E->0x03003E2D; 0x03003E2F=1
   if (keys & bit9): volume_up(0x0804A714); 0x03003E2D=0; 0x03003E2E=1; 0x03003E2F=1
 case 4:                            # Show Image
   if (keys & LEFT)  and img > 0:  img -= 1
   if (keys & RIGHT) and img < 14: img += 1
   if (keys & A): show_image(img)              # 0x08048EFC/0x080499E0 + 0x03003C90..A0
```

Because the tests are level-triggered (no edge detection), **holding** Left/Right
advances one step per frame until the counter hits its clamp.

### 5.3 Menu description

The five rows come from a pointer array, not from a switch of strings:

* `0x08050070` header `{u16 1, u16 3, u16 0x12, u16 0x13, u16 5, u16 0}` followed by
  five `u32` pointers at `0x0805007C`.
* Each item record is `{u8 0x04, u8 id, u16 0, u32 text_ptr}` followed by a
  NUL-padded string. `id` is the per-screen action id (`0x04` map, `0x07` sprite,
  `0x0A` SFX, `0x0D` music, `0x10` image).

## 6. Tables

### 6.1 Debug-menu items (`0x0805007C` → descriptors)

| Row | Item pointer | Record | Text pointer | Label |
|---:|---|---|---|---|
| 0 | `0x08602F48` | `04 04 00 00` | `0x08602F50` | `Go To Map` |
| 1 | `0x08602F30` | `04 07 00 00` | `0x08602F38` | `Sprite Viewer` |
| 2 | `0x08602F5C` | `04 0A 00 00` | `0x08602F64` | `Play SFX` |
| 3 | `0x08602F70` | `04 0D 00 00` | `0x08602F78` | `Play Music` |
| 4 | `0x08602F84` | `04 10 00 00` | `0x08602F8C` | `Show Image` |

### 6.2 Map table (`0x0820A3C8`, 42 entries)

Each `u32` points to a `0x34`-byte descriptor `{u16 zone, u16 area, u16 width,
u16 height, 11 × u32 pointers}`. The debug `Go To Map` counter indexes this array and
is clamped at `41` (`cmp r1,#41`), so **42 entries** are reachable.

| idx | entry ptr | zone | area | w | h |
|---:|---|---:|---:|---:|---:|
| 0 | 0x08207F74 | 2 | 2 | 60 | 40 |
| 1 | 0x08207FA8 | 1 | 1 | 30 | 20 |
| 2 | 0x08207FDC | 5 | 5 | 150 | 100 |
| 3 | 0x08208010 | 2 | 10 | 60 | 200 |
| 4 | 0x08208044 | 5 | 5 | 150 | 100 |
| 5 | 0x08208078 | 5 | 5 | 150 | 100 |
| 6 | 0x082080AC | 1 | 1 | 30 | 20 |
| 7 | 0x082080E0 | 1 | 1 | 30 | 20 |
| 8 | 0x08208114 | 1 | 1 | 30 | 20 |
| 9 | 0x08208148 | 4 | 3 | 120 | 60 |
| 10 | 0x0820817C | 1 | 1 | 30 | 20 |
| 11 | 0x082081B0 | 2 | 10 | 60 | 200 |
| 12 | 0x082081E4 | 5 | 5 | 150 | 100 |
| 13 | 0x08208218 | 3 | 3 | 90 | 60 |
| 14 | 0x0820824C | 1 | 1 | 30 | 20 |
| 15 | 0x08208280 | 3 | 3 | 90 | 60 |
| 16 | 0x082082B4 | 3 | 4 | 90 | 80 |
| 17 | 0x082082E8 | 3 | 4 | 90 | 80 |
| 18 | 0x0820831C | 1 | 1 | 30 | 20 |
| 19 | 0x08208350 | 1 | 1 | 30 | 20 |
| 20 | 0x08208384 | 1 | 1 | 30 | 20 |
| 21 | 0x082083B8 | 1 | 1 | 30 | 20 |
| 22 | 0x082083EC | 3 | 2 | 90 | 40 |
| 23 | 0x08208420 | 3 | 4 | 90 | 80 |
| 24 | 0x08208454 | 4 | 4 | 120 | 80 |
| 25 | 0x08208488 | 1 | 1 | 30 | 20 |
| 26 | 0x082084BC | 1 | 1 | 30 | 20 |
| 27 | 0x082084F0 | 1 | 1 | 30 | 20 |
| 28 | 0x08208524 | 4 | 4 | 120 | 80 |
| 29 | 0x08208558 | 8 | 12 | 240 | 240 |
| 30 | 0x0820858C | 4 | 4 | 120 | 80 |
| 31 | 0x082085C0 | 4 | 4 | 120 | 80 |
| 32 | 0x082085F4 | 1 | 1 | 30 | 20 |
| 33 | 0x08208628 | 1 | 1 | 30 | 20 |
| 34 | 0x0820865C | 3 | 3 | 90 | 60 |
| 35 | 0x08208690 | 1 | 1 | 30 | 20 |
| 36 | 0x082086C4 | 2 | 1 | 60 | 20 |
| 37 | 0x082086F8 | 1 | 1 | 30 | 20 |
| 38 | 0x0820872C | 1 | 1 | 30 | 20 |
| 39 | 0x08208760 | 1 | 1 | 30 | 20 |
| 40 | 0x08208794 | 4 | 4 | 120 | 80 |
| 41 | 0x082087C8 | 4 | 4 | 120 | 80 |

### 6.3 Sound-effect table (`0x08600CD0`, 31 × 12 bytes)

Each entry is `{u32 sample_ptr, u32 0, u32 sample_meta}`. Examples:
entry 0 `{0x085D21D8, 0, 0x3D480A01}`, entry 18 `{0x085E720F, 3, 0x0FF8043E}`,
entry 30 `{0x085F5B7C, 0, 0x13673260}`. Entry 31 onward is a different table, so the
`cmp #30` clamp exactly covers the table.

### 6.4 Music table (`0x085D2100`, 18 × 12 bytes)

Each entry is `{u32 sequence_ptr, u32 sample_ptr, u32 length}`; e.g. entry 0
`{0x0858615C, 0x0858458C, 0x687}`, entry 17 `{0x0858FAA4, 0x0858F5C4, 0x374}`.
18 tracks (0–17), matching the `cmp #17` clamp.

### 6.5 Image gallery (15 entries, `Show Image` row)

The `Show Image` action pushes a gallery screen (`0x08048EFC`, `0x080499E0`,
`0x08048EC` family) using the three state blocks at `0x03003C90/94/A0`; each image is
a full-screen cutscene illustration. Enumerated in-game:

| idx | content (observed screenshot) |
|---:|---|
| 0 | Kame House exterior |
| 1 | Snake Way (orange, wide) |
| 2 | Goku holding a planet |
| 3 | King Kai's planet (red/white saucer) |
| 4 | Goku in a spaceship / room |
| 5 | blue-green planet in space |
| 6 | domed ship in ice (Frieza's arrival) |
| 7 | group picture of Goku's friends |
| 8 | Goku on the Flying Nimbus (night) |
| 9 | Goku with halo (dead) |
| 10 | regeneration chamber room |
| 11 | Snake Way (purple, long) |
| 12 | Goku and Gohan |
| 13 | Vegeta charging a ki blast |
| 14 | Yajirobe cutting Vegeta's tail |

### 6.6 Legacy of Goku II debug strings and music list

Strings at `0x08805AF4`–`0x08805B68` (see §4). The sound test's list is a 44-entry
record table at `0x08C094E0` (56-byte stride); the handler's bound is
`cmp r0,#43` (`0x0880592C`), i.e. 44 tracks `0…43`. This matches the TCRF-published
track list (00 `Race To The Island` … 43 `World Map`, with **track 27 unused**).
TCRF's track titles are fan descriptions and are not present as ASCII in the ROM;
only the 44-entry count and the `%d` labels are verifiable from the image.

## 6b. Enumeration

### 6b.1 Space definition

This cartridge has **no password alphabet, no symbol table, and no checksum**. The
only user-entered "code" is the button chord, and the only lookup is the LOG1 debug
menu:

* **Chord space**: 10-bit `KEYINPUT` word; the accepted value is one exact mask,
  `0x0341` (A|Up|R|L) applied while Options has the cursor on `Text Speed`. The
  neighbouring masks `0x0301` (L+R+A) and `0x0381` (L+R+Down+A) are rejected.
* **Menu value space** (Legacy of Goku I):
  * `Go To Map`: 42 values (index `0…41`), table `0x0820A3C8`, 1-based display.
  * `Play SFX`: 31 table entries (`0…30`) — the row's display field saturates at
    `36` (open question, §8).
  * `Play Music`: 18 tracks (`0…17`).
  * `Show Image`: 15 images (`0…14`).
  * `Sprite Viewer`: a scrollable viewer over the character animation-set list; the
    list labels are font-encoded (not ASCII) and their count was not extracted
    statically (see §8).
* Total distinct debug-menu *actions/values*: 42 + 31 + 18 + 15 = **106 concrete
  selections**, plus the viewer.

### 6b.2 Novel selections (absent from every published list)

No published source gives numeric debug values at all; the published list names only
four items. The following values were minted here and confirmed in mGBA:

| Selection | Value | Result (screenshot) |
|---|---|---|
| `Go To Map` | `01` | starts the game at **Kame House**, Goku Lv1, world map (`033_gotomap2.png`) |
| `Go To Map` | `37` | starts at **Kami's Lookout** platform with Mr. Popo (`178_warp37b.png`) |
| `Go To Map` | `42` (last entry) | starts at **Kami's Lookout** (`315_warp42b.png`) |
| `Show Image` | `14` | **Yajirobe cuts Vegeta's tail** illustration (`img_14.png`) |
| `Show Image` | `13` | Vegeta charging a ki blast (`img_13.png`) |

Two items are themselves unpublished as distinct entries: `Play SFX` and `Play Music`
are separate rows (published descriptions collapse them into one "Sound Test"), and
`Show Image` is the "Photo Gallery" under a different label.

### 6b.3 Bounds proven by rejection

| Test | Result | Evidence |
|---|---|---|
| `Show Image` = 14, press RIGHT | value stays `14`, screen unchanged (pixel diff = cursor blink only) | `173_img_maxval.png` vs `174_img_right_after_max.png` |
| `Go To Map` = 42, press RIGHT | value stays `42`, screen unchanged (diff = cursor only) | `280_v4.png` vs `290_map_after42.png` |
| `Play Music` = 17, press RIGHT | value stays `17` (diff = cursor only) | `300_cur.png` vs `301_music_after.png` |
| `Go To Map` = 01, press LEFT | value stays `01` (minimum) | `220_map_min.png` |
| L + R + A on Text Speed (no Up) | **no** debug menu; Text Speed changes Low→Medium | `233_LR_only.png` |
| L + R + Down + A | **no** debug menu; Down moves the cursor to Music Volume | `234_LRD_only.png` |
| L + R + Up + A on LOG2 Options | **no** debug menu; options closes | `219_ii_debug_in_game2.png` |

The handler's own clamps (`cmp r1,#41 / #30 / #17 / #14`, §4) independently bound the
four counters, so no input sequence can produce an index outside the tables.

### 6b.4 Excluded space (bounded negative)

* **ASCII keyword scan, whole ROM**: `PASSWORD`, `Password`, `password`, `CHEAT`,
  `SECRET CODE`, `ENTER CODE`, `CODE:`, `UNLOCK`, `DEBUG` → **0 hits**; `Debug` → 1
  hit (`0x805B68`); `Music Test` → 1 hit (`0x805AF4`); `SOUND TEST`, `Sound Test`,
  `LEVEL SELECT`, `Level Select` → 0 hits.
* **Uppercase-run scan** (candidate password tables): 5,529 runs ≥ 6 chars in the
  first half, 4,293 in the second. Inspecting the dense repeated candidates (e.g.
  `!CW42D` four times at `0x2071B6` + `0x12C` stride) showed compressed tile data, not
  code tables (surrounding bytes are 4bpp tile patterns and pointers to graphics).
* **Mask-table scan**: no u16 sequence of button masks exists; the chord is tested as
  individual key bits inside the Options-screen transition, not from a table. The
  `0x0340` mask appears 5 times in the first half as unrelated data/literals, none in
  a menu table.
* **Menu walk** (both halves, every reachable screen): launcher I/II; LOG1 title,
  New Game/Continue/Options, Options, debug menu + all 5 sub-screens, pause
  (Quests/Inventory/Attacks/Save/Options/Exit); LOG2 title, Options, Select Game (3
  slots), pause tabs Status/Items/Options/Journal. **No password entry, no shop code,
  no sound-test accessible from a normal menu, no link/multiplayer screen**
  (`LINK`, `MULTI`, `CABLE`, `TRADE`, `BATTLE` → 0 ASCII hits).
* **Published literals checked**:
  * `Text Speed`, `Options`, `Low/Medium/High` — present (`0x0857AD14`, `0x0857ACD0`,
    `0x085117C`).
  * `Go To Map`, `Sprite Viewer`, `Play SFX`, `Play Music`, `Show Image` — present
    (`0x08602F50..`).
  * `Music Test: %d`, `Sample Test: %d`, `Map Test`, `Zone: %d`, `Area: %d`,
    `Variation: %d / %d`, `Debug` — present (`0x08805AF4..0x08805B68`).
  * Published *contents* of the LOG1 debug menu ("Level Select, Sound Test, Sprite
    Viewer, Photo Gallery") — 4 of 5 rows, with different labels; "Level Select" =
    `Go To Map`, "Sound Test" = `Play SFX` + `Play Music`, "Photo Gallery" =
    `Show Image`.
  * Published LOG2 access `0202B32D:02` + hold Start — **not reproducible** in this
    build (RAM write applied during the intro, verified byte = `02`; Start at title →
    Select Game, no debug screen).
  * VGChartz "Play as Hercule / Control Text Window / Get scouter early" — these are
    entries in VGChartz's cheat database without any in-game button/password content;
    no corresponding literal or table exists in the ROM (searched), so they are
    recorded as unverified/not applicable to this build.

## 7. Validation evidence

| # | Claim | Type | Evidence |
|---:|---|---|---|
| 1 | Cart is 3 images at `0x0 / 0x40000 / 0x800000` | Observed + Derived | logo scan hits; header dump; `file(1)` |
| 2 | LOG1 debug menu opens with L+R+Up+A on Text Speed | **Observed** | `031_debug_try2.png` (title Options), `196_ingame_debug.png` (pause Options) |
| 3 | The menu has 5 rows in a fixed order | **Observed** | `031`, `196`, `302_up.png` |
| 4 | The handler is `0x08040BFE` with a 5-way jump table | Derived | objdump `-M force-thumb`; BL/entry inspection; jump-table math |
| 5 | Counter clamps are 41 / 30 / 17 / 14 | Derived | bytes at `0x08040C56`, `0x08040CA4`, `0x08040CE2`, `0x08040D78` |
| 6 | Map, SFX, music tables are at `0x0820A3C8`, `0x08600CD0`, `0x085D2100` | Derived | literals at `0x08040E20/E28/E2C`; table dumps |
| 7 | `Show Image` has 15 images | **Observed** | `img_00.png`…`img_14.png`; clamp no-op diff |
| 8 | Warp 01 = Kame House, 37/42 = Kami's Lookout | **Observed** | `033_gotomap2.png`, `178_warp37b.png`, `315_warp42b.png` |
| 9 | Wrong chords are rejected | **Observed** | `233_LR_only.png`, `234_LRD_only.png` |
| 10 | LOG2 contains a developer debug menu (strings + handler) | Derived | strings at `0x08805AF4..`; code at `0x088058E6+` |
| 11 | LOG2 debug menu is not reachable in-game in this build | **Observed (negative)** | flag write + Start attempts (`140_after_flag.png`, `153_cbdebug2.png`); chord attempt `219` |
| 12 | No password/passcode system exists | Derived from observed (bounded search) | §6b.4 keyword/table scans; full menu walk |
| 13 | Debug values persist between screens until reset | Observed | in-game reopen showed map/SFX/music values retained (`196`, `331_after.png`) |

## 8. Unknowns

1. **On-screen field semantics for `Go To Map` and `Play SFX`.** For `Play Music`
   (17) and `Show Image` (14) the displayed number equals the handler counter, and for
   the map the handler clamp is 41 while the display reaches 42 (consistent with a
   1-based display). The `Play SFX` row displays `36` although its handler clamp is
   `30` and the sample table has 31 entries; the displayed field therefore is not the
   table index for that row. The exact mapping (a sound id vs. a display counter) was
   not isolated. The authoritative table bound remains `30` from the handler.
2. **`Sprite Viewer` list size and labels.** Labels are rendered from the game font /
   tile indices, not ASCII, so `strings` cannot recover them. The viewer was scrolled
   in-game (screenshots) but the full entry count was not extracted statically; the
   labels seen include `Goku SSJ 1..3`, `Gohan 1..3`, `Gogeta 1..2`, `Bubbles`,
   `Bora 1..2`, `Cell …`, `Babidi`, `Buu 1` — i.e. the list is a *shared character
   table*, larger than LOG1's story cast.
3. **LOG2 debug menu access in this rebuild.** The published CodeBreaker address did
   not work here. Because the second image is a later (Dec-2005 pack) rebuild with
   shifted data (e.g. `CharacterData.cpp` at `0x804336` vs TCRF's `0x42F4`), its
   EWRAM debug flag may live at a different address. This was not solved; the menu
   contents are documented from the strings/code and TCRF only.
4. **Audible verification of `Play SFX` / `Play Music`.** The emulator ran with
   `SDL_AUDIODRIVER=dummy`, so the screenshots prove the menu action and the table
   lookup, not the sound emitted. (A human with audio can confirm in one press.)
5. **Map-entry `zone/area` field meanings** are inferred from the descriptor layout
   (`u16 zone, u16 area, u16 width, u16 height`); only the warp effect itself was
   observed.

## 9. Tooling

* mGBA 0.10.5 (SDL), Xvfb `:108`, openbox, `xdotool`, `scrot`, ImageMagick.
  A private copy of the binary was used as `mgba-dbz` so that the shared
  `pkill -x mgba` cleanup of another session could not kill this run.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python 3 + `capstone 5.0.7` for BL-target/literal scans and function-region bit-test
  scans.
* `gdb-multiarch` against `mgba -g` (port 2345) for entry-register inspection
  (`r0` at `0x08040BFE`), IWRAM dumps, and the LOG2 flag write.
* Helper `gba.py` (key/screenshot/crop) and ad-hoc Python scans in
  `/tmp/opencode/dbzlegacy/`; screenshots in `/tmp/opencode/dbzlegacy/shots/`.
* Savestates `rom.ss1` (debug menu) and `rom.ss2` (intro) in the work directory.

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed with this report.
Only hashes, addresses, offsets, short UI labels needed to identify menu rows, and
this analyst's own screenshots/notes are included.
