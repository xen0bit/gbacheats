# Camp Lazlo: Leaky Lake Games (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Camp Lazlo: Leaky Lake Games/Camp Lazlo: Leaky Lake Games.gba` |
| Size | 4,194,304 bytes (`0x400000`, 32 Mbit) |
| Header title | `CAMP LAZLO` (`0xA0`, NUL padded) |
| Game code | `BLCE` (`0xAC`) |
| Maker code | `4Z` (`0xB0`) |
| Version | `0x00` (`0xBC`) |
| Entry word | `0xEA00002E` → branch to `0x080000C0` (stock GBA crt0, not a cracktro) |
| MD5 | `6385b15433d8cd369cadec45e5d5a783` |
| SHA-1 | `184fe377d82264c2c3ae426d9e57437ec5f8901e` |
| SHA-256 | `24270fc9ed0f7ec459b14ee6adfe778c517a4db3fe13105264515a7ee8ca30a6` |

Header anomaly: the 156-byte Nintendo logo occurs exactly once (file offset `0x04`), so this is a single GBA image, not a multi-game pack. The entry point and the crt0 at `0x080000C0` are stock. The header check fields are inconsistent with the header bytes:

* `0xBD` (complement) = `0xEA`; computed complement = `0x1C`.
* `0xBE..0xBF` (header checksum) = `0x0000`; computed checksum = `0x00EA`.

The stored `0xEA` is exactly the computed header checksum, while the checksum field is zero — the signature of a header rewrite/repair tool, not of a code patch. No trainer, cracktro, or appended banner was found: `CRC BANDIT`, `SUNHORS`, `Mode7`, `CRACKTRO`, `TRAINER`, `PIRACY`, `PRESENTS`, `GREETINGS` all return no hit; the final 64 bytes are zero and first-4 KiB entropy is normal code entropy (6.47 bits/byte). Analysis used the image as shipped.

## 2. Executive summary

**This GBA title has no in-game password, cheat-code, button-code, or hidden debug-menu system that is reachable by the player.** The conclusion is a bounded negative result, not an absence of searching:

1. **No code-entry surface exists.** There is no text-entry screen, no alphabet/keypad screen, no `PASSWORD`/`CODE` UI, and no buffer that is compared against user text. The only input devices are the title screen, the three-slot file menu, the pause menu, the map overlay, and the in-world NPC/event script.
2. **No code data exists.** A full 4 MiB scan found no `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `GALLERY`, `OPTIONS`, `BONUS`, `EXTRAS`, `MINI GAME`, `LEVEL SELECT`, `SOUND TEST`, or `PRESS START` string in ASCII, lowercase, `+0x20`, `-0x20`, or UTF-16LE. The dialogue bank is ASCII (`0x0801D124`); all menu labels (`PAUSE`, `SAVE`, `CONTINUE`, `QUIT`, `SELECT A FILE`, `MINIGAMES`) are pre-rendered tile graphics, which is why string scans miss them.
3. **No button-sequence validator exists.** The joypad routine is at `0x08003D88`; its edge-pressed word is `0x03006670`. A scan of all 2,097,152 halfword positions found 388 runs of four or more button masks, 213 runs of five or more, and exactly one run of six or more containing L/R (`0x083BD608`); that run has no pointer reference and is data. The only pointer-referenced mask-looking run is `0x0801D0C4`, which is a sine/geometry coefficient table used by the rotation code at `0x08001C84`/`0x08004814`, not an input table. The Konami sequence (`Up Up Down Down Left Right Left Right B A`) is absent in both u16 and byte form.
4. **No in-game codes are published.** GameFAQs' cheat page and the usual mirrors publish only CodeBreaker/GameShark **device** codes for this SKU (e.g. `83007390 8C96` timer, `830073F0 0034` infinite paint). Those are RAM writes, not in-game codes, and are outside this engagement's scope. No password/button list exists to verify. TCRF documents only an unused ending song.
5. **The game-select hub is an event list, not a code surface.** The `MINIGAMES` board is the game's event/mini-game list. Its scene handler is `0x08010724`. The unlock count is `0x030074E4`, computed from a 3×5 table of 15 progress flags at `0x03007320`; the cursor is `0x030074E8` and the index→ID table is 16 halfwords at `0x080E43B8`. With zero unlocks the board is blank; with the 15 flags set (analysis aid) it renders numbers 1–15 and a blank 16th slot. The count loop caps the normal list at 15, but the navigation code has a special case at `0x08010B54`: with all 15 events unlocked, the input **Down, Down, A** from the initial cursor (slot 1) moves to slot 9, then to the blank 16th slot, and A writes area/event ID `0x0017` to `0x03004300`. This is the only unadvertised entry found; it is a blank slot, not a password or a cheat.
6. **The only menus are:** title (Start only), file select (3 files + erase with YES/NO), pause (SAVE / CONTINUE / QUIT), map overlay (Select), hub, cabin interiors, and the `MINIGAMES` board. There is no options/sound/gallery/debug screen, and Select/L/R/A/B/D-pad on the title produce no alternate screen.

## 3. How to reproduce

### Emulator and display

```bash
Xvfb :226 -screen 0 1024x768x24 &
DISPLAY=:226 openbox &
cd "roms/Camp Lazlo: Leaky Lake Games"
DISPLAY=:226 SDL_AUDIODRIVER=dummy mgba -3 "Camp Lazlo: Leaky Lake Games.gba"
```

mGBA 0.10.5 (Debian `mgba-sdl`). The GBA viewport is `720x480+152+144` in the 1024×768 root.

### Keymap (mGBA SDL default)

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Hold keys 80–150 ms; menus debounce and a 10 ms tap is often lost. Holding A advances dialogue quickly; a single press advances one line.

### Exact menu path

1. Boot → Crave logo → legal screen → title screen (`PRESS START`). Only Start responds.
2. `Return` → `SELECT A FILE` (FILE 1/2/3 + `ERASE THIS FILE?`). File 1 was used; a saved file shows a progress label (`CAMPGROUNDS` in the capture) and the red flag marker.
3. On `ERASE THIS FILE?`, A opens a `YES / NO` confirmation; B cancels back to the file list. No file is erased by cancelling.
4. Select File 1 → intro dialogue (hold A to advance) → camp hub.
5. In the hub: `Return` opens `PAUSE` with `SAVE`, `CONTINUE`, `QUIT` (three entries; Up at SAVE does not wrap). `BackSpace` opens the map overlay. `x` talks to NPCs / examines objects. The `MINIGAMES` board is to the right of the Jellybean cabin door.
6. `SAVE` writes the 512-byte EEPROM and displays `SAVING... Do not turn off the power.`

### Codes tested

No in-game codes exist to test. The published CodeBreaker codes were **not applied** (device/RAM codes are explicitly out of scope). The only literal-code test possible is a negative one: the board accepts no input with zero unlocks, and no text-entry field exists anywhere in the reachable menus.

### Screenshots (kept on disk, not embedded)

`/tmp/opencode/camplazlo/`: `boot2.png` (title), `fs2.png` (file select), `fs_back.png` (erase YES/NO), `pause2.png` (pause), `save_res.png` (SAVING), `map_forest.png` (map), `nav1.png` (MINIGAMES board, 0 unlocked), `out2.png` (MINIGAMES board, 15 unlocked + blank 16th), `cabin_in3.png` (cabin).

## 4. Address map

ROM addresses are `0x08000000 + file_offset`.

| Address | Meaning |
|---|---|
| `0x08003D88` | Joypad updater: reads `0x04000130`, stores held/pressed edges |
| `0x0300666C` | Previous held keys (u16) |
| `0x03006674` | Current held keys, active-high (`~KEYINPUT & 0x3FF`) |
| `0x03006678` | Copy of held keys |
| `0x0300667C` | Newly pressed edges (u16) |
| `0x03006670` | Newly pressed edges, copy used by menu code |
| `0x08010724` | `MINIGAMES` board / event-list scene handler (called by `BL` from `0x080093D6`) |
| `0x030074E4` | Unlocked-entry count for the board (u16, 0..15) |
| `0x030074E8` | Board cursor (u16, 0..count-1) |
| `0x03007320` | 3×5 table of 15 progress/unlock flags (u16 each) |
| `0x080E43B8` | 16-entry u16 index→event-ID table (see §6) |
| `0x03004300` | Selected event ID written on confirm (`0x08010C38..0x08010C46`) |
| `0x0801D124` | Dialogue text bank (ASCII, `#`-delimited) |
| `0x0801D0C4` | 48×u16 geometry coefficient table (false-positive "button run") |
| `0x083BD608` | 6×u16 mask-looking run `R,Right,R,Right,R,Right`; data, no pointer |
| `0x081AC630` | Character/glyph map; ASCII `0x20..0x9D` maps identity, so text is ASCII |

## 5. Algorithm

### 5.1 Joypad edge detection (`0x08003D88`)

```c
u16 raw   = *(volatile u16*)0x04000130;   // active low
u16 held  = (~raw) & 0x3FF;
u16 prev  = *(u16*)0x0300666C;
u16 press = held & ~prev;                 // rising edges only
*(u16*)0x03006674 = held;
*(u16*)0x0300667C = press;
*(u16*)0x03006670 = press;
*(u16*)0x0300666C = held;
```

Mask values follow the GBA convention: A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.

### 5.2 Board unlock count (`0x0801075A`–`0x08010792`)

```c
u16 count = 0;
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 5; j++) {
        if (*(u16*)(0x03007320 + 2*(i*5 + j)) != 0)
            count++;
    }
}
*(u16*)0x030074E4 = count;
*(u16*)0x030074E8 = 0;
```

The table is exactly 15 halfwords, so `count` is the population count of 15 flags and can only be 0..15.

### 5.3 Cursor bounds (`0x08010ACC`–`0x08010B22`)

```c
u16 count  = *(u16*)0x030074E4;
u16 cursor = *(u16*)0x030074E8;
u16 press  = *(u16*)0x0300667C;

if (press & 0x010) {                 // Right
    if (cursor < count && cursor != 8)
        cursor++;
}
if (press & 0x020) {                 // Left
    if (cursor > 1 && cursor != 9)
        cursor--;
}
// Down (0x080) moves by +8 with the 7/8 and 14/15 wrap cases
// Up   (0x040) moves by -8 with the 15→8 wrap case
```

Initial cursor is 0. The Right-move test at `0x08010AE4` rejects `cursor >= count`, so the normal maximum index is `count-1`. There is one deliberate/edge-case exception: at `0x08010B54`, if `cursor == 8` and `count == 15`, Down sets `cursor = 15` (the blank 16th slot). The confirm path then stores `mapping[15] = 0x0017` in `0x03004300` and advances the scene state to 4.

### 5.4 Selection

On confirm (`0x08010C38`):

```c
u16 cursor = *(u16*)0x030074E8;
u16 id     = ((u16*)0x080E43B8)[cursor];
*(u16*)0x03004300 = id;              // selected event/level ID
```

No checksum, no alphabet, no text buffer, and no user-visible code string is involved.

## 6. Tables

### 6.1 16-entry board index→event-ID table at `0x080E43B8`

| Index | ID | Index | ID |
|---:|---:|---:|---:|
| 0 | `0x001B` | 8 | `0x000F` |
| 1 | `0x0009` | 9 | `0x0013` |
| 2 | `0x000D` | 10 | `0x000C` |
| 3 | `0x0011` | 11 | `0x0010` |
| 4 | `0x000A` | 12 | `0x0014` |
| 5 | `0x000E` | 13 | `0x0015` |
| 6 | `0x0012` | 14 | `0x0016` |
| 7 | `0x000B` | 15 | `0x0017` (blank slot) |

All 16 IDs are distinct. With the maximum count of 15, the normal list uses indices 0..14; index 15 (`0x0017`) is the blank 16th slot. The nav special case at `0x08010B54` can still move the cursor there, and the confirm code then writes `0x0017`. The board renderer draws `count` numbered slots; the 16th slot remains blank (observed).

### 6.2 The 15 reachable events (from the ASCII dialogue bank and the board)

The dialogue bank and the "play again" list name the same 15 events in story order: Hot Lava, Forest Clean-Up, Team Teeter Totter, Mulberry Berry, Swim Trunk, Fishing Challenge, Stinky Llama Race, Mud Puddle High Dive, Food Fight, Pinecone Sitting, Tube Gauntlet, Mud Puddle Tug of War, Big Buddy Swim Finale, Itchy Island Treasure Hunt, Kidney Five Hundred. These correspond to the 15 nonzero flags counted by §5.2. The 16th table ID (`0x0017`) has no matching name in the ASCII bank.

### 6.3 Four cabin flags

The hub HUD shows four flag slots (red X until collected); the intro script asks for four cabin flags (`"YOU FOUND A CABIN FLAG!"` is one of the pickup messages). These are story-collectibles, not a code system, and are stored in the save rather than in the 15-entry event table.

### 6.4 Published cheat-device codes (out of scope)

The only published codes for this SKU are CodeBreaker/GameShark RAM writes, e.g. from the EmuCheatz list:

```
Camp Lazlo Leaky Lake Games (US)
Timer         83007390 8C96
Infinite Paint 830073F0 0034
```

These are not in-ROM literals, are not entered on any game screen, and were not applied (scope excludes memory-edit codes). They do not indicate an in-game code system.

## 6b. Enumeration

### 6b.1 Space definition

There is **no code space** to define: the game has no alphabet, no code length, no checksum, no reserved bits, and no input buffer for a password or button code. The only enumerable list is the mini-game board:

* Table size: 16 entries (`0x080E43B8`).
* Reachable entries: 15 (`count = popcount(flags[0..14])`, maximum 15).
* Blank/special entry: 1 (index 15, ID `0x0017`; reached by the Down-from-slot-9 edge case, not by the normal count).
* State space of the board's unlock count: 16 values (0..15). The normal cursor cap is `count-1`, with one special case (`0x08010B54`, Down from slot 9 at `count == 15`) that reaches index 15.

### 6b.2 Validator model

There is no validator. The closest function is the count loop in §5.2, reimplemented exactly:

```python
flags = [0]*15
count = sum(1 for f in flags if f != 0)   # 0..15
selectable = list(range(count))           # normal: 0..count-1
if count == 15:
    selectable.append(15)                 # 0x08010B54 special case (blank 16th slot)
```

This model agrees with the ROM for every possible flag vector: the count is the number of nonzero flags, the normal indices are `0..count-1`, and the single extra index 15 is reachable only via the `cursor == 8` Down edge case. Index 15 is not a checksum result; it is a blank slot whose confirm writes ID `0x0017`.

### 6b.3 Novel codes

No novel code can be minted because no code format exists. The equivalent deliverable for a negative engagement is the bounded proof below.

### 6b.4 Bounds proven by rejection

| Test | Input | Observed result |
|---|---|---|
| Board with zero unlocks | Stand at the `MINIGAMES` board, press A, B, Start, Select, L, R, and D-pad | No state change; board remains blank/inert (`nav1.png`) |
| Board with 15 unlocks (analysis aid) | 15 flags set in `0x03007320`, open board | 15 numbered slots (1–15) drawn; 16th slot blank (`out2.png`); A on slot 1 (ID `0x001B`) produced no visible change; the Down-from-slot-9 path is derived from `0x08010B54` |
| Erase confirmation | `ERASE THIS FILE?` → A, then B (NO) | Returns to file list; file 1 remains `CAMPGROUNDS` |
| Text-entry surface | Search all reachable menus | No text field, no alphabet grid, no `PASSWORD`/`CODE` label |
| Button sequence | Konami u16/byte; all mask runs | 0 Konami hits; only pointer-referenced run is geometry data |
| Published in-game codes | GameFAQs/EmuCheatz/TCRF | Only CodeBreaker RAM writes; no in-game list |

### 6b.5 Negative results bounded (search counts)

* Whole-ROM byte scan: 4,194,304 bytes.
* ASCII `strings -t x -n 4`: 43,099 strings.
* Keyword hits in strings: `password` 0, `cheat` 0, `debug` 0, `secret` 0, `unlock` 0, `gallery` 0, `option` 0, `bonus` 0, `extra` 0, `minigame` 0, `mini game` 0, `level select` 0, `sound test` 0, `press start` 0, `enter code` 0, `continue` 0, `new game` 0, `pause` 0, `save` 0, `select a file` 0, `erase this file` 0. (`quit` has 2 false positives: `QUITE THE CONTRARY` in dialogue and `RICHARD QUITORIANO` in the credits.)
* Raw-ROM encoding scan for `PASSWORD`, `CHEAT`, `DEBUG`, `GALLERY`, `OPTIONS`, `SCORE`: 0 in ASCII, lowercase, `+0x20`, `-0x20`, UTF-16LE.
* Button-mask scan: 2,097,152 u16 positions; 388 runs ≥4, 213 runs ≥5, 1 run ≥6 containing L/R (`0x083BD608`, no pointer reference). Only one pointer-referenced run (`0x0801D0C4`), classified as geometry coefficients by its use at `0x08001C84` and `0x08004814` (sin/cos scaling, not input).
* Input code: three `0x04000130` literals (`0x324`, `0x3DBC`, `0x18960`); the real joypad updater is `0x08003D88`. The menu-relevant pressed-edge word is `0x03006670`.
* Menus walked: title, file select, erase YES/NO, pause, map overlay, hub, cabin interior, `MINIGAMES` board (0 and 15 unlocked states). No options, sound, gallery, password, or debug screen was found.

### 6b.6 Hidden 16th slot found

The one non-trivial hidden entry is the **blank 16th board slot**:

* The table at `0x080E43B8` contains 16 IDs; the 16th is `0x0017`.
* The unlock loop at `0x0801075A` counts only 15 flags (3×5 at `0x03007320`), so the normal list length is 15.
* The Right-move test at `0x08010AE4` rejects `cursor >= count`, but the Down branch at `0x08010B54` has an explicit special case: if `cursor == 8` and `count == 15`, it sets `cursor = 15`.
* Confirm at `0x08010C38` then stores `mapping[15] = 0x0017` in `0x03004300` and writes scene state 4 (`0x08010C50`).
* The board renderer draws 15 numbered slots plus a blank 16th slot (observed).

So the blank slot is not a password/cheat, but it is an unadvertised 16th event/area ID reachable by a specific navigation edge case (Down from slot 9 when all 15 are unlocked). The gameplay content for ID `0x0017` was not identified by name; it is a distinct ID in the table, not a duplicate.

## 7. Validation evidence

**Observed (emulator/screenshot or RAM read):**

* Boot → Crave logo → legal screen → title; only Start advances.
* Title: Select, L, R, A, B, Up, Down produce no alternate screen.
* File select has three files and an erase row; erase opens YES/NO and B cancels.
* Pause has exactly SAVE, CONTINUE, QUIT; Up at SAVE does not wrap.
* Select opens a static map overlay with `YOU ARE HERE`.
* The `MINIGAMES` board is blank at zero unlocks; with 15 flags set it shows numbers 1–15 and a blank 16th slot; A on the visible slots produced no visible change in the tested positions.
* `SAVE` writes a 512-byte EEPROM image (`0xA4`-byte active block, rest `0xFF`); no password field is involved.
* GDB read at the hub: `0x030074E4 = 0x0000` and all 15 halfwords at `0x03007320 = 0x0000` before any event completion.

**Derived (instruction sequence / table):**

* Joypad edge detection and the key globals from `0x08003D88`.
* Count loop and cursor bound from `0x0801075A`/`0x08010ACC`, including the `0x08010B54` blank-slot special case.
* 16-entry mapping table at `0x080E43B8`; selection write to `0x03004300`.
* Button-mask run at `0x083BD608` has no pointer/xref; run at `0x0801D0C4` is used as geometry coefficients.
* All keyword scans and encoding variants.

**Inferred:**

* The header check-field swap is a header-repair artifact, not a gameplay patch (entry/crt0 are stock and no trainer strings exist).
* The area/event content for ID `0x0017` was not identified by name; it has no matching entry in the ASCII text bank. Its selection path is derived from `0x08010B54`/`0x08010C38`; the blank 16th slot is observed.

## 8. Unknowns

* The human-readable name/asset for event ID `0x0017` was not located; the table value is known but the corresponding graphic/name asset was not isolated.
* The exact tool that rewrote the header check fields is unknown; the code and data are stock.
* TCRF's page could not be read directly (Cloudflare 403); the search snippet reports only “An unused ending song. The game does not have an ending cutscene”, which is consistent with the absence of a debug menu. No prompt-injection content was encountered in the fetched material.

## 9. Tooling

* `mgba` 0.10.5 (`/usr/games/mgba`) under `Xvfb :226` + `openbox`, `SDL_AUDIODRIVER=dummy`.
* `xdotool` for XTEST input, `scrot`/ImageMagick for captures.
* `arm-none-eabi-objdump -M force-thumb` for the raw Thumb disassembly.
* Python 3 + Capstone 5.0.7 for the LDR-literal and BL scans.
* GDB (`gdb-multiarch`) over mGBA's `-g` stub for RAM reads and the analysis-only flag write used to render the populated board.
* Scripts/logs: `/tmp/opencode/camplazlo/keys.py`, `strings4.txt`, `gdb.log`.

## 10. Legal note

No ROM, extracted graphics, audio, or text assets are redistributed. Only hashes, addresses, short identifiers, and behavioural findings are reported. The screenshots referenced above are local analysis artifacts under `/tmp/opencode/camplazlo` and are not part of the repository.
