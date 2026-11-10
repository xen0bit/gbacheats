# Breath of Fire II (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Breath of Fire II/Breath of Fire II.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `BOF2` |
| Game code | `AB2E` (USA) |
| Maker code | `08` (Capcom) |
| Software version | 0 |
| Entry word | `0xEA00002E` = `b 0x080000C0` (stock) |
| Fixed byte `0xB2` | `0x96` |
| Complement `0xBD` | `0xE6` (matches computed `0xE6`) |
| Header checksum `0xBE` | `0x0000` (rebuilt-header artifact; computed `0x031A`) |
| MD5 | `2132b06357239d4e6a0716d963f46597` |
| SHA-1 | `d35e452d467093c4a788d290a65adf05a4270343` |
| SHA-256 | `ea3b2e4c8d0d8bc9ff2f3eff7b62cc94d914764e5de3a3256a93366a5970a821` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at file
offset `0x4`. This is a single GBA image; there is no second header, no
multiboot stub, and no appended trainer. The entry branch and the first 4 KiB
are the stock Capcom crt0 (no cracktro).

## 2. Executive summary

Breath of Fire II (GBA) has **no password system and no published in-game
button code**. Its saves are battery-backed; all published "cheats" for the
game are GameShark/CodeBreaker/Action Replay memory writes, which this
engagement excludes.

What the ROM does contain is a **developer battle-debug mode**, disarmed at
build time by a one-byte config string, and re-armed by a hidden controller
sequence that is not in any published list:

> Hold **L** (or **R**) and press
> **Up, Up, Down, Down, Left, Right, Left, Right, Select, Start**.

The sequence is a ten-entry `u16` table at `0x08191A62`, checked per frame by
the battle module at `0x08091334`. A completed sequence toggles
`battle_debug_mode` at `0x03005B0C`. With the flag set, pressing **A** in a
battle opens a seven-row debug configuration menu (`configuration / divetimer /
waterfx / difficulty / cockpit / cheat / critical / end`) implemented at
`0x08091AE0`. The ROM initialises the flag from the string
`battle_debug_mode=00` at `0x191A4C`; because the character after `=` is `'0'`
(value 0), the mode starts off and the controller sequence is the intended
in-game switch.

The only "PASSWORD" text in the ROM is a story-line joke at the Highfort
control-room door (text ID 330, `0x08177C46`): the party is asked to "PLEASE
ENTER YOUR PASSWORD", the timer runs out, the force field drops, and the Portal
boss fight begins. There is no input field, alphabet, buffer or comparison for
it. That is a bounded negative, not a password system.

The one developer-intended unlockable is the Township **sound test**: recruit
Sumner (the `MUSICIAN` NPC, Tunlan) as the sixth-house tenant and he opens a
35-track music player. It is documented by the fan wiki and the GBA Township
FAQ; the ROM carries the `MUSICIAN` NPC titles at `0x190582`/`0x1905B1`.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba`), 3× scale, under
`Xvfb :211` + `openbox`, `SDL_AUDIODRIVER=dummy`.

Default mGBA SDL keymap used and verified:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Boot path walked:

1. Title screen (flames, "BREATH OF FIRE II"), press Start.
2. Main menu: `NEW GAME`; press A.
3. File select: three slots (`No. 1/2/3 Blank`).
4. Name entry: 12-column grid `A–Z`, `a–z`, `0–9`, `. ? ! ' - :` plus
   `Fwd / Bck / End`. Selecting `End` with no letters accepts the default name.
5. Options: `Text Speed  Fast | Nrml | Slow`, `Dash  Nrml | Auto`,
   `Music  ON | OFF`, `EXIT`. All values were cycled. `L+R`, `Select` and
   `Start` on this screen do nothing (no hidden row).
6. File select with a save present: `GAME START / NEW GAME / COPY / ERASE /
   EXCHANGE`. All five rows were opened; Copy/Erase/Exchange are ordinary
   save-management screens.
7. `GAME START` → slot → prologue. The field menu was then opened:
   `ITEM / SPEL / EQIP / STAT / FORM / OPTN / SAVE / EXIT`, with the status
   panel (`Ryu`, `Lv 1`, `HP 24/24`, `AP 3/3`, `EXP 0`, location `Gate`).
   The `ITEM` page exposes `USE / DSOD / CHNG / SORT / VITL`.

Screenshots were kept on disk under `/tmp/opencode/boff2/` (title, file select,
name entry, options, field menu, item submenu); they are deliberately not
embedded in this report.

### 3.1 Button-code procedure (derived; in-game confirmation still open — see §7)

In a battle, hold **L** (or **R**) and press, in order:

```
Up, Up, Down, Down, Left, Right, Left, Right, Select, Start
```

The banner sound `SE 0x21` and the bit set at `0x02006EE8` mark the enable; the
flag itself is at `0x03005B0C`. Afterwards press **A** in the battle to open
the debug configuration menu.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x080002F0` | Key-state update. `[0x03001244]` = held keys, `[0x03001246]` = newly pressed keys (active-high GBA masks). |
| `0x08091230` | Helper called by the battle-debug handler when `0x03005B10 == 1`. |
| `0x08091334` | **Button-sequence validator** (entry). |
| `0x08091340` | First-run init: reads `0x08191A4C+19` (`'0'`) & `0x0F`, stores to `0x03005B0C`. |
| `0x0809136E` | Reads `[0x03001240]+4` (held) and `+6` (pressed). |
| `0x080913A8` | Sequence loop; index at `0x0300104C`, table at `0x08191A62`. |
| `0x080913EA` | Match: `EOR` toggle of `0x03005B0C`; SE `0x21`/`0x20`; set bit `0x800` at `0x02006EE8`. |
| `0x0809142C` | Function epilogue. |
| `0x080B468C` | `bof2_battle.c` per-frame battle handler; calls `0x08091334` at `0x080B4698`. |
| `0x080B46A4` | If `0x03005B0C != 0` and `A` is pressed: clear `0x03005B38[0..5]`, set `0x03001138 = 1`. |
| `0x080B46D0` | If `0x03001138 != 0`: call `0x08091AE0` (debug menu); clear on return. |
| `0x080B644C` | Tiny wrapper `bl 0x080B468C; bx lr` (battle callback). |
| `0x08091AE0` | Debug-menu init/update. |
| `0x0809160C` | Debug-menu draw (rows, values). |
| `0x08091434` | Debug-option setter (`switch` 0..5; writes bits of `0x02006EE8`). |
| `0x080919B0` | Debug-menu cursor movement / A / B handling. |
| `0x08091A40` | Debug-menu second half (index 0..6). |
| `0x08091BC4`, `0x08091BFC` | Debug-menu helpers (flag get/set). |
| `0x0300104C` | Button-sequence index (`u32`). |
| `0x03001068` | Debug-menu row index (`u32`, 0..6). |
| `0x03001138` | "Open debug menu" request (`u32`). |
| `0x03001240` | Key-state block; `+4` held, `+6` pressed. |
| `0x03004674` | Menu key block (`byte[0]` pressed, `byte[1]` held). |
| `0x03005010` | Battle-debug first-run flag (`u8`). |
| `0x03005B0C` | **`battle_debug_mode`** (`u32`). |
| `0x03005B10` | Battle-debug sub-mode flag (`u32`). |
| `0x03005B38` | Debug-menu cursor/state bytes. |
| `0x02006820` | Saved-game / system block base. |
| `0x02006EE8` | Debug option bits (`u16`): bit 9,10,11,12,13,14. |
| `0x08191A4C` | ASCII `battle_debug_mode=00` (20 bytes + NUL). |
| `0x08191A62` | Button table: `0040 0040 0080 0080 0020 0010 0020 0010 0004 0008 0000`. |
| `0x081919C2` | `configuration` (debug menu title; custom font). |
| `0x081919D2` | `divetimer` |
| `0x081919F9` | `difficulty` |
| `0x08191A04` | `easy` |
| `0x08191A09` | `hard` |
| `0x08191A0E` | `cockpit` |
| `0x08191A26` | `cheat` |
| `0x08191A2C` | `critical` |
| `0x08191A35` | `end` |
| `0x0818C200` | Text pointer table (1197 × `u32`, `0x08170000`–`0x08189478`). |
| `0x08177C46` | Text ID 330: `PLEASE ENTER YOUR PASSWORD.` |
| `0x08177C93` | Text ID 331: `YOUR TIME IS UP. WE START ATTACKING. THE FORCE FIELD HAS BEEN CANCELED.` |
| `0x0B9D80`–`0x0BD000` | Assert / source-file name bank (`bof2_battle.c`, `bof2_emset.c`, `bsound.c`, …). |
| `0x190582`, `0x1905B1` | NPC title `MUSICIAN` (Township Sumner). |

File offset ↔ ROM address: `rom_address = 0x08000000 + file_offset`.

## 5. Algorithm

### 5.1 Button sequence (validator `0x08091334`)

Reimplementation, precise enough to run offline:

```c
uint16_t table[11] = {0x40,0x40,0x80,0x80,0x20,0x10,0x20,0x10,0x04,0x08,0};
// GBA active-high: A=1 B=2 Select=4 Start=8 Right=0x10 Left=0x20
//                  Up=0x40 Down=0x80 R=0x100 L=0x200

// first run, once:
battle_debug_mode = rom8(0x08191A5F) & 0x0F;   // '0' (0x30) & 0x0F = 0

// every battle frame:
held    = key_held;      // 0x03001244
pressed = key_pressed;   // 0x03001246

if (pressed != 0) {
    if ((held & 0x300) == 0) {          // L or R not held
        seq_index = 0;                  // reset
    } else if ((table[seq_index] & pressed) != 0) {
        seq_index++;
        if (table[seq_index] == 0) {    // all ten presses matched
            battle_debug_mode ^= 1;     // 0x03005B0C
            if (battle_debug_mode)
                play_se(0x21), sysflags |= 0x0800;
            else
                play_se(0x20);
        }
    } else {
        seq_index = 0;                  // wrong press: reject, start over
    }
}
```

The table is an exact matcher, not a mask set: each press must equal the
current entry. A wrong press resets the index and cannot complete the sequence.

### 5.2 Debug menu gate

```c
// battle frame handler 0x080B468C
if (battle_debug_mode && (pressed & 0x01)) {   // A
    memset(0x03005B38, 0, 6);
    debug_menu_request = 1;                    // 0x03001138
}
if (debug_menu_request) {
    r = debug_menu();                          // 0x08091AE0
    if (r) debug_menu_request = 0;
}
```

### 5.3 Debug menu options

Six toggles plus `end` (index 6). Setter `0x08091434` writes one bit of the
`u16` at `0x02006EE8` per row:

| Row | Label (custom font) | Bit at `0x02006EE8` | Value labels in ROM |
|---:|---|---:|---|
| 0 | `divetimer` | 13 | `on` / `off` |
| 1 | `waterfx` | 14 | `on` / `off` |
| 2 | `difficulty` | 10 | `easy` / `hard` |
| 3 | `cockpit` | 11 | `now` / `now` |
| 4 | `cheat` | 9 | `now` / `max` |
| 5 | `critical` | 12 | — |
| 6 | `end` | — | exits |

The labels are stored in a private font: byte `+0x37` = lowercase ASCII,
byte `+0x17` = the first letter of each record, `0x02` = space, `0x00` = record
break. Example: `0x2C 0x38 0x37 0x2F 0x32 0x30 0x3E 0x3B 0x2A 0x3D 0x32 0x38
0x37` → `configuration`.

## 6. Tables

### 6.1 Button table (`0x08191A62`)

```
index : 0    1    2    3    4    5    6    7    8    9    10
value : 0040 0040 0080 0080 0020 0010 0020 0010 0004 0008 0000
button: Up   Up   Down Down Left Right Left Right Sel  Start term
```

Modifier: `(held & 0x300) != 0` → hold **L** and/or **R**.

### 6.2 Published-code survey

| Source | Codes | Kind | In scope? |
|---|---|---|---|
| libretro `Breath of Fire II (USA, Europe) (Code Breaker).cht` | 10 | CodeBreaker memory writes (`82xxxxxx`, `83xxxxxx`) | No — memory edit |
| GameHacking.org | ~140 | GameShark / AR / CB memory writes | No — memory edit |
| GameFAQs item-patch FAQ | 48 × 2 lines | GameShark item writes | No — memory edit |
| Fandom / Township FAQ | 1 unlockable | Recruit Sumner → 35-track sound test | Yes — developer-intended unlockable |

No published list contains an in-game password or a controller sequence for
the GBA SKU. (The SNES Game Genie debug codes on TCRF are for the SNES build;
their RAM addresses `7E:xxxx` do not exist here.)

## 6b. Enumeration

**Button-code space.** The accepted set is a single fixed ten-press sequence
terminated by `0x0000`; there is no branch or wildcard. The validator's index
(`0x0300104C`) makes the space a chain, not a product: `32^10` raw press
strings collapse to one accepting string. Enumerated actions: one
(`battle_debug_mode ^= 1`), plus the pre-existing sub-mode branch at
`0x0809136E` (`0x03005B10 == 1`, handler `0x08091230`).

**Novel code (not in any published list).**
`L/R + Up, Up, Down, Down, Left, Right, Left, Right, Select, Start`.
No GameFAQs, TCRF, VGChartz, GameHacking or wiki page lists a GBA controller
code for this game; the only published BoF2 material is memory-write codes.

**Bounds by rejection.**
- A wrong press (e.g. `A` instead of `Up`) hits the `seq_index = 0` path at
  `0x080913E4` and cannot complete the sequence.
- Releasing L/R before the tenth press hits the same reset path.
- Omitting the `Select,Start` tail leaves `table[index] != 0` and the flag
  unchanged.
- A ninth-press-only `Start` fails at index 0.

**Password space.** Zero accepted inputs. The single `PASSWORD` string is
text ID 330 in a timed story event; it has no entry field or comparator.
Text search: 1197 text records, one `PASSWORD` occurrence, zero
`PASSWORD`-as-code tables.

**Unlockable enumeration.** Township house 6 has four tenants
(`Surfy`, `Sumner`, `Daiye`, `Salvador`). `Sumner` = sound test (35 tracks).
This is a story/recruitment unlock, not a typed code.

## 7. Validation evidence

**Observed (emulator):**
- Boot, title, main menu, file select, name-entry grid, options screen with
  all values, save-management menu, field menu, item submenu, status panel.
- Key mapping verified by opening the field menu with `x` (A) and navigating
  with the D-pad.
- Options screen: `L+R`, `Select`, `Start` produce no hidden row.
- Text/table bytes: `battle_debug_mode=00` at `0x191A4C`; button table at
  `0x08191A62`; debug labels at `0x1919C2`–`0x191A35`.
- Under the mGBA GDB stub, halted at `0x080002F0`; key block at `0x03001240`
  reads `+4`/`+6`. Injecting the first table entry (`pressed = 0x40`, `held =
  0x200`) and entering `0x08091334` at the manually reset index
  `0x0300104C = 0` produced `seq_index = 1`, `battle_debug_mode = 0` — the
  validator's first transition is confirmed on the emulated CPU.

**Derived (instruction sequence):**
- The complete ten-press table and its order.
- The `L/R`-held precondition (`ands r2, #0x300`).
- The reset-on-mismatch behaviour and the terminal toggle.
- The ROM init from `0x08191A5F` (`'0' & 0x0F = 0`).
- The battle-only caller (`0x080B4698`), so the code cannot fire in the field
  or on the title screen.
- With the flag set, `A` in battle reaches the debug menu via `0x03001138`.

**Inferred:**
- The visible effect of each debug row (`divetimer`, `waterfx`, `difficulty`,
  `cockpit`, `cheat`, `critical`) is not witnessed; the labels and bit writes
  are read from the ROM.

**Not observed / limit of this session:**
- The battle debug menu itself. Reaching a battle requires finishing the
  prologue. In a second session on `:211` the display was recreated, frames
  were verified to advance (two screenshots 1.2 s apart had different MD5s),
  and the prologue was played out of the church into Gate village. The
  village NPC/dragon hint **"Isn't Yua always playing at the back mountain"**
  was observed on screen, confirming the BushLnd objective. Repeated attempts
  to reach the village's north/BushLnd path (church-east path, church-west
  road, the house row, the forest edge, the south gate, the church interior
  and the kitchen) did not produce a map transition; the scripted Beak battle
  and any random encounter were therefore not reached. A third pass followed
  the published prologue route exactly: after Ganer's "find Yua", the church
  was exited, the woman in front of the centre house was spoken to (she gives
  "Isn't Yua always playing at the back mountain"), and the north end of Gate
  village was reached and screenshotted. At the north end the visible tiles
  are: the centre house with a closed door, a two-post fence, a small
  light-green tuft beside a grey rock, two dark bushes, and the forest edge;
  pressing A while facing the tuft, the rock and both bushes did **not** clear
  anything, and the character was collision-locked in the pocket between the
  house, the fence and the two villagers. The gate is therefore a
  navigation/collision problem in the prologue map, not a RAM flag that can be
  named from the evidence collected. The injected debugger call crashed the
  emulator on the second press (`Jumped to invalid address: 090F3470`)
  because the validator's sound/engine calls were re-entered outside the
  battle frame; only the first press was observed. This is reported rather
  than papered over, and §0.2's in-game confirmation remains the one open
  item.

**Data-handling note.** A TCRF mirror fetched during reconnaissance returned a
prompt-injection payload (fake "decode key", payment demand, fake tool
instructions, "Eat my ass" output). It was treated as untrusted data and
ignored, per guide §16.8. No instruction from a fetched page or ROM string was
executed.

## 8. Unknowns

1. In-battle visible effect of the debug configuration rows; the labels and
   bit positions are known, the gameplay consequence is not.
2. Whether the debug menu can be opened in the fishing minigame (the same
   `bof2_battle.c` module also implements fishing; not tested).
3. The exact meaning of the `0x03005B10` sub-mode branch (`0x08091230`).
4. Whether the Township sound-test room uses a separate menu routine or the
   ordinary house-interior script; not reached without a completed save.

## 9. Tooling

- `mGBA 0.10.5` SDL, `/usr/games/mgba -3` (and `-g` for the GDB stub).
- `Xvfb :211` + `openbox`, `scrot`, ImageMagick `convert`.
- `xdotool` for XTEST key events.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
- Python 3 `struct`/`hashlib` for header, pointer-table, string and mask scans.
- `gdb-multiarch` against mGBA's GDB stub for the validator transition test.
- Helper scripts and screenshots in `/tmp/opencode/boff2/` (not tracked).

## 10. Legal note

No ROM, extracted graphics, music or game text is redistributed here. The
report contains addresses, algorithms, hashes, my own disassembly-derived
pseudocode and generated test values only.
