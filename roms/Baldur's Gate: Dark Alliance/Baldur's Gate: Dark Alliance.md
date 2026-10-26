# Baldur's Gate: Dark Alliance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Baldur's Gate: Dark Alliance/Baldur's Gate: Dark Alliance.gba` |
| Size | 8,388,608 bytes (`0x800000`, 8 MiB) |
| Header title | `BALDURSGATE` (11 chars + NUL) |
| Game code | `BGDE` |
| Maker code | `20` |
| Software version | 0 |
| Entry word | `0xEA000030` (ARM branch to `0x080000C0`) |
| Complement check | `0xAF` stored, `0xAF` computed — valid |
| Header checksum | `0x0000` stored, `0x0000` computed — valid |
| Save type | 512-byte save (mGBA creates a 512-byte `.sav`; the game's packed record is also 512 bytes, consistent with EEPROM-512 — the exact media type was not isolated) |
| MD5 | `13fd90ae7070ba25c2ce4223b8f51a1e` |
| SHA-1 | `c7c264ec85976f326b34bbd9f5e91ddc6eb29e17` |
| SHA-256 | `14269f56d73aba7c9e15ae586f7eaa1cc0eb0878442781b1cc1db1b21f48e0c0` |

Embedded-header scan: the full 156-byte Nintendo logo occurs **once**, at file offset
`0x4`. No second header, no multiboot stub, no concatenated second image. The
game title/game code at `+0xA0/+0xAC` are `BALDURSGATE` / `BGDE`. The header
complement and header checksum both validate, so there is **no header/logo
patch detected**.

## 2. Executive summary

This build has **no password system, no in-game cheat code table, no level
select and no debug menu**. That is a positive, bounded result: every reachable
menu was walked, the full string space and the plausible code/table spaces were
searched, and the only global button combination found is the documented
sleep/wake combination.

The only developer-intended unlockable is the fourth character class, the
**Elven Fighter**, awarded for completing the game. The unlock is a save flag,
not a code:

* the class-select handler computes its maximum entry count as **3 or 4** from
  bit 7 of the IWRAM byte `0x030001F1`;
* the normal completion path at `0x0869CB76` sets that bit and immediately
  calls the save packer (`0x08685D18`) and the save-record packer
  (`0x086859E0`);
* the save bit is **bit 0 of the 512-byte packed record at `0x03000200`**, and
  the load path at `0x08685D44` reads it back into bit 7 of `0x030001F1`.

A fresh save shows exactly three classes (`FIGHTER`, `WIZARD`, `ARCHER`), and
pressing Down on `ARCHER` wraps back to `FIGHTER` — the fourth slot is rejected.
An analysis-only ROM patch that changes only the handler bound (`0x068B64A`,
`03 26` → `04 26`, `movs r6,#3` → `movs r6,#4`) exposes the fourth slot: a
distinct purple preview with the stat line **16/12/8/9/11/10**, which differs
from all three named classes. The fourth slot's label is not drawn by that
minimal patch because the label-drawing path is separate; the class name string
`ELVEN FIGHTER` is string ID 55 in the table at `0x08227C10`.

All publicly listed “cheats” for this title are external device codes
(GameShark/CodeBreaker/Action Replay) plus the same Elven Fighter unlock. The
external codes are outside the scope of this engagement and were **not** used.

## 3. How to reproduce

### Emulator

* mGBA 0.10.5 (`/usr/games/mgba`), SDL frontend.
* `Xvfb :163 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`.
* `mgba -3 "<rom>"`.
* Viewport is 720×480 at screen offset `+153+172`; screenshots were cropped with
  ImageMagick.

### Keymap used (mGBA SDL default)

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Keys were held 100–300 ms. Savestates used `Shift+F1`..`Shift+F4`, loads
`F1`..`F4`.

### Menu path (fresh save)

1. Boot: legal notice → DSI Games / Magic Pockets logos → title.
2. Title: `NEW GAME` (fresh save) or `NEW GAME` / `CONTINUE SAVED GAME`
   (when a save exists). Selecting `NEW GAME` over an existing save shows
   `THIS WILL ERASE YOUR SAVED GAME. / ARE YOU SURE? / YES / NO`.
3. Character select: `CHOOSE YOUR CHARACTER'S CLASS:` with exactly
   `FIGHTER`, `WIZARD`, `ARCHER`.
4. `A CHOOSE` → skills screen. All 12 points must be spent; the action line
   changes from `A USE POINTS` to `A VALIDATE` only at 0 points.
5. `A VALIDATE` → Act I card → intro dialogue → in-game.
6. `Start` → seven-tab inventory/pause menu. Tabs (left to right): stats,
   armour, potions, ranged/ammo, spell/rune, book, red door (options).
   The seventh tab holds `SAVE GAME`, `SLEEP MODE`, `BRIGHTNESS` and
   `QUIT GAME`; `QUIT GAME` asks `QUIT GAME? YES / NO`.
7. `L + R + SELECT` at any time → `SLEEP MODE` screen (the game itself
   documents this combination).

### Codes / combinations actually tested

| Input | Context | Result |
|---|---|---|
| `L + R + SELECT` | in-game and pause | Sleep Mode screen (observed) |
| `L + R + SELECT` again | Sleep Mode screen | wakes, returns to game (observed) |
| `L + R + START` | in-game | ordinary pause menu; no extra menu (observed) |
| `L + R + A` | class select | ordinary class accept; no fourth class (observed) |
| `Down` on `ARCHER` | class select, fresh save | wraps to `FIGHTER` (observed rejection) |
| `START`, `SELECT` | class select / skills | no action (observed) |

No external GameShark/CodeBreaker/Action Replay code was entered; those are
memory/device codes and out of scope.

### Analysis-only patch used for the fourth class

Copy ROM to `/tmp/opencode/bgda/bgda_patch4.gba`, then change file offset
`0x068B64A` from `0x03` to `0x04` (only the class-handler bound). This is **not**
a cheat code and **not** a distributed ROM; it is lab evidence to make the
otherwise completion-gated fourth slot selectable. The original ROM was not
modified.

## 4. Address map

File offset → ROM address: `rom_address = 0x08000000 + file_offset`.

### Text and menus

| File offset | ROM address | Meaning |
|---:|---:|---|
| `0x227C10` | `0x08227C10` | UI string table: `u16` offsets relative to this base, index 0 = `0xFFFF`, NUL-terminated strings, `0x04` control byte before many strings |
| `0x2280F5` | `0x082280F5` | ID 1 `STRENGTH` |
| `0x22838F` | `0x0822838F` | ID 52 `FIGHTER` |
| `0x228398` | `0x08228398` | ID 53 `WIZARD` |
| `0x2283A0` | `0x082283A0` | ID 54 `ARCHER` |
| `0x2283A8` | `0x082283A8` | ID 55 `ELVEN FIGHTER` |
| `0x2284B8` | `0x082284B8` | ID 72 `NEW GAME` |
| `0x2284C2` | `0x082284C2` | ID 73 `CONTINUE SAVED GAME` |
| `0x22B165` | `0x0822B165` | ID 621 `CREDITS` |
| `0x683700`–`0x6837FF` | `0x08683700`–`0x086837FF` | UI script/data stream referencing string IDs (e.g. options IDs 58–61 at `0x68374C`) |
| `0x66CE54` | `0x0866CE54` | second copy of the same UI string table (duplicate bank; same strings) |

### Class select / unlock

| File offset | ROM address | Meaning |
|---:|---:|---|
| `0x68B632` | `0x0868B632` | class-select input handler (pressed-key edge) |
| `0x68B63E`–`0x68B650` | `0x0868B63E`–`0x0868B650` | reads bit 7 of `0x030001F1`; `r6 = 3` or `4` |
| `0x68C5C0` | `0x0868C5C0` | second class handler (hard bound 4; branches on the byte at `0x03000AB8`) |
| `0x69CB76` | `0x0869CB76` | completion path: `0x030001F1 |= 0x80`, then save |
| `0x685D18` | `0x08685D18` | pack unlock flag into save bitstream (bit 0) |
| `0x685D44` | `0x08685D44` | unpack flag from save bitstream (bit 0) |
| `0x6859E0` | `0x086859E0` | character-record packer (writes bitstream at `0x03000200`) |
| `0x6858C0` | `0x086858C0` | character-record unpacker |
| `0x696D80` | `0x08696D80` | generic bitstream writer (`buf`, bit position, value, count) |
| `0x696E2C` | `0x08696E2C` | generic bitstream reader |
| `0x697D8A` | `0x08697D8A` | new-game init clears bit 7 of `0x030001F1` |
| `0x6A33C0` | `0x086A33C0` | sleep combination check (`0x304` = L+R+Select) |

### RAM

| Address | Size | Meaning |
|---:|---:|---|
| `0x03000ACB` | 1 | selected class index (0–3) |
| `0x030001F0` | 1 | character-slot/aux byte |
| `0x030001F1` | 1 | flags; bit 7 = fourth class unlocked; low nibble written by slot logic |
| `0x03000200` | 512 | packed save bitstream (bit 0 = Elven Fighter unlock) |
| `0x03001520` + `0x5D` | 1 | slot state byte used by save menu |
| `0x030029A0` | 4 | global flag word (`bit 19` also packed at save bit 1) |
| `0x0300359C` | 2 | held keys, active-high (`~KEYINPUT & 0x3FF`) |
| `0x03002BFC` | 2 | newly pressed keys (edge) |
| `0x03002BEC` | 2 | newly released keys (edge) |
| `0x03002BE0` | 1 | sleep gate; must equal `0x55` for the sleep combo |

The key state is produced by the routine at `0x086A3370`:
`pressed = ~KEYINPUT & ~previous`, `held = ~KEYINPUT`, `released = previous & ~held`.

## 5. Algorithm

### 5.1 String IDs

The UI uses a 16-bit ID. Resolution:

```
base = 0x08227C10
off  = u16[base + 2*id]          # 0xFFFF = no string
if off != 0xFFFF:
    string = read_nul(base + off) # first byte 0x04 is a control/format code
```

Confirmed IDs: 1–6 stats, 52–55 class names, 56 `SKILLS`, 57 `STATISTICS:`,
58 `SAVE GAME`, 59 `SLEEP MODE`, 60 `BRIGHTNESS`, 61 `QUIT GAME`,
62 `QUIT GAME?`, 63 `YES`, 64 `NO`, 65 `SLEEP MODE`, 66 wake-up text,
67 `GAME SAVED`, 68 `[ OK`, 69–71 Act I–III, 72 `NEW GAME`,
73 `CONTINUE SAVED GAME`, 74 erase warning, 75 `ARE YOU SURE?`.

### 5.2 Class count and selection

```
unlocked = (mem[0x030001F1] >> 7) & 1
max_classes = 4 if unlocked else 3
idx = mem[0x03000ACB]              # signed byte

on Up:
    idx -= 1
    if idx < 0: idx = max_classes - 1
on Down:
    idx += 1
    if idx >= max_classes: idx = 0
```

This exactly predicts the observed fresh-save behaviour: from `ARCHER` (index 2)
with `max_classes = 3`, Down produces index 0 (`FIGHTER`).

### 5.3 Unlock persistence

```
# completion (0x0869CB76)
mem[0x030001F1] |= 0x80
bit_write(buf=0x03000200, bitpos=0, value=1)   # 0x08685D18
save_record_pack()                              # 0x086859E0

# load (0x08685D44)
v = bit_read(buf=0x03000200, bitpos=0, count=1) # 0x08696E2C
mem[0x030001F1] = (mem[0x030001F1] & 0x7F) | (v << 7)

# new game (0x08697D8A)
mem[0x030001F1] &= 0x7F
```

The packed record is 512 bytes; the character-record packer writes 8-bit
fields sequentially into it and appends a CRC-8 at record offset `0x1FF`
(loop at `0x08685B6E`). The `.sav` is also 512 bytes, but the exact save-media
byte/bit ordering (and therefore why a one-bit `.sav` edit is rejected) was
not fully reversed.

### 5.4 Sleep combination

```
if mem[0x03002BE0] == 0x55 and (held & 0x3FF) == 0x304:
    request_sleep()
```

`0x304 = L (0x200) | R (0x100) | Select (0x004)`. This is the only global
button combination found in the engine.

### 5.5 No password algorithm

No password/checksum routine exists: there is no input buffer, no alphabet
table, no length check, no text-entry screen. See §6b for the search boundaries.

## 6. Tables

### 6.1 Character classes (all values observed in-game)

| Index | Name | STR | DEX | INT | WIS | CON | CHA | Points | Preview |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 0 | FIGHTER | 16 | 10 | 8 | 9 | 13 | 8 | 12 | brown/tan |
| 1 | WIZARD | 11 | 12 | 15 | 10 | 11 | 13 | 12 | magenta |
| 2 | ARCHER | 15 | 13 | 9 | 11 | 12 | 9 | 12 | green |
| 3 | not drawn (ID 55 `ELVEN FIGHTER`) | 16 | 12 | 8 | 9 | 11 | 10 | 12 | purple |

Row 3 was reached only with the analysis-only bound patch; its label is blank
under that patch because the label-drawing path was not patched. Identification
as the Elven Fighter is **inferred** from (a) string ID 55, (b) the flag-gated
count of 4, and (c) the stat line being a fighter/archer hybrid. It is not
claimed as directly observed under a legitimate completed save.

### 6.2 Menu / screen inventory (all screenshots in `/tmp/opencode/bgda/shots/`)

| Screen | Evidence |
|---|---|
| Legal notice | `s00_boot.png` |
| DSI Games + Magic Pockets logos | `s01.png` |
| Title, fresh save (`NEW GAME`) | `s44_fresh_title.png` |
| Title with save (`NEW GAME`, `CONTINUE SAVED GAME`) | `s54_title_continue.png` |
| Erase-save confirmation (`YES`/`NO`) | `s37_class_fighter.png` |
| Class select, 3 entries | `s64_class_fresh.png` |
| Skills / point allocation | `s09_skills_bottom.png` |
| `A VALIDATE` at zero points | `s19_zero2.png` |
| Act I card | `s20_validate.png` |
| Intro dialogue / in-game | `s25_ingame3.png`, `s27_ingame5.png` |
| Pause tab 1 (stats) | `s28_pause.png` |
| Pause tab 2 (armour) | `s29_tab2.png` |
| Pause tab 3 (potions) | `s30_tab3.png` |
| Pause tab 7 (options) | `s31_tab7.png`, `s61_quit_sel.png` |
| `GAME SAVED` | `s32_tab7_open.png` |
| `QUIT GAME? YES/NO` | `s62_quit_confirm.png` |
| `SLEEP MODE` | `s57_combo_lrsel.png` |
| Book tab (empty without books/items) | `s60_book_controls.png` |
| Fourth slot, analysis patch | `s52_patch_4th.png` |
| Fourth slot stats | `s66_elf_top.png`, `s67_elf_bottom.png` |
| Archer stats | `s70_archer_top.png`, `s71_archer_bottom.png` |
| Wizard stats | `s77_wizard_real_top.png`, `s78_wizard_real_bottom.png` |

### 6.3 Key masks used by the engine

`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200` (active-high held state at
`0x0300359C`).

## 6b. Enumeration

### Space definition

There is **no code space** in this build: no alphabet, no length, no checksum,
no lookup table of accepted strings. Searches are therefore stated as bounded
negatives rather than as an enumerated code set.

The only hidden-content space is the character-class roster:

* 3 normally selectable classes (indices 0–2) and 1 gated class (index 3);
* gate = one bit in `0x030001F1`, persisted as one bit in the 512-byte
  save record;
* no other bits of that flag byte select a class (the low nibble is written by
  slot logic, not by a class code).

### Search boundaries (counts)

| Space | Search | Result |
|---|---|---|
| ASCII strings, length ≥4 | `strings -t x -n 4` | 109,814 lines; 108,519 regex ASCII runs |
| `PASSWORD` | literal, both cases | 0 |
| `CHEAT` | literal, both cases | 0 |
| `DEBUG` | literal, both cases | 0 |
| `UNLOCK` | literal, both cases | 0 |
| `CODE` | literal, both cases | 0 |
| `LEVEL SELECT` | literal | 0 |
| `PRESS START` | literal | 0 |
| alphabet `A–Z` contiguous | literal | 0 |
| alphabet `A–Z` minus confusables | literal | 0 |
| `SECRET` | literal | 16, all story dialogue (“secret passage”, “secret war”, …) |
| key-mask `u16` tables | runs ≥5 of single-button masks over whole ROM | 15 runs, **0 in code** (`0x680000`–`0x6B0000`) |
| key-mask `u8` tables | runs ≥8 over whole ROM | 1,087 runs, all text/font bytes (dominant `0x80`); no length/terminator record |
| `0x04000130` (KEYINPUT) literals | pointer scan | 3, all in audio/sleep support (`0x086A33DC`, `0x086A4D68`, `0x086A7150`); none in a cheat handler |
| menu-string pointers | literal pointer scan to `0x08227C10` / menu strings | 0 direct pointers; strings resolved through the ID table at `0x08227C10` |

### Published codes

Public lists contain only:

* **external device codes** — several CodeBreaker, Action Replay and GameShark
  entries from Ethereal Games / 53lu / GameHacking.org. These write RAM or
  ROM addresses and are outside the scope (no GameShark/CodeBreaker/memory-edit
  codes).
* **the Elven Fighter unlock** (“complete the game once”), which this report
  verifies structurally.

There is no published in-game password, button code, debug menu or level select
for this GBA build to test. GameFAQs' GBA cheats page lists only the completion
bonus plus external device codes.

### Novel / generated input

A code cannot be minted because no code grammar exists. The equivalent
deliverable for the only hidden system is the fourth-class state:

* the fourth slot is **not reachable** on a fresh save: Down on `ARCHER`
  wraps to `FIGHTER` (observed, `s64_class_fresh.png` plus Down input);
* `L + R + A` at class select does **not** unlock it (observed);
* forcing only the handler bound (analysis patch `0x068B64A`) yields a
  selectable fourth slot with a distinct purple preview and the stat line
  `16/12/8/9/11/10` (`s52_patch_4th.png`, `s66_elf_top.png`,
  `s67_elf_bottom.png`), proving the class data and preview exist in the build;
* the real gate is completion: `0x0869CB76` sets `0x030001F1` bit 7 and packs
  it as save bit 0 (`0x08685D18`), and the load path reverses it
  (`0x08685D44`).

### Bounds proven by rejection

1. **Class bound, fresh save:** with `max_classes = 3`, Down on index 2 wraps
   to 0; the fourth entry cannot be selected. Observed in `s64_class_fresh.png`
   and the following Down press.
2. **No unlock by button code:** holding L+R and pressing A on the class screen
   enters the normal skills screen for the selected class; no fourth class and
   no flag change. Observed (`s65_lr_a_class.png`).
3. **Save gate rejects a naive edit:** flipping bit 0 of a valid 512-byte
   `.sav` (the packed-record unlock bit) and booting made the title show only
   `NEW GAME`; `CONTINUE SAVED GAME` disappeared. The rejection is consistent
   with an integrity check (the packer writes a CRC-8 at record offset `0x1FF`),
   so a one-bit edit without the matching checksum is not accepted.
4. **Sleep combo is not a cheat gate:** L+R+Select produces only the documented
   Sleep Mode screen; waking requires the same combination and returns to the
   previous screen. No menu, flag or inventory change was observed.

### Enumeration completeness statement

Every menu reachable from boot on a fresh and on a saved game was visited:
title, erase confirmation, class select, skills/validate, Act card, in-game,
all seven pause tabs, options submenu, save confirmation, quit confirmation,
sleep screen and the book tab. No additional entry appeared for any input or
state tested. The negative is therefore a statement about those screens and
about the string/table spaces listed above, not a claim about unreachable
completion-only content.

## 7. Validation evidence

### Observed

* Boot/legal/logos/title screens; fresh title has only `NEW GAME`; title with a
  save has `NEW GAME` + `CONTINUE SAVED GAME`.
* Class select has exactly three labelled entries; Down on Archer wraps to
  Fighter.
* Fourth slot under the analysis patch: purple preview, stats
  `16/12/8/9/11/10`, 12 points, blank label.
* Wizard stats `11/12/15/10/11/13`; Archer `15/13/9/11/12/9`;
  Fighter `16/10/8/9/13/8`.
* L+R+Select opens Sleep Mode; L+R+Select wakes it.
* Pause menu has seven tabs; the seventh has Save/Sleep/Brightness/Quit;
  Quit asks Yes/No.
* A one-bit `.sav` edit is rejected at boot (no Continue).
* All menu screenshots listed in §6.2.

### Derived

* Class count is `3 + (bit 7 of 0x030001F1)` from `0x0868B63E`.
* The completion path `0x0869CB76` sets that bit and calls the save packer and
  writer.
* The unlock bit is save bitstream bit 0 (`0x08685D18` / `0x08685D44`) and is
  cleared by new-game init `0x08697D8A`.
* Sleep combination is `(held & 0x3FF) == 0x304` with gate byte `0x03002BE0 ==
  0x55` (`0x086A33C0`).
* No password/cheat validator exists: no input buffer/alphabet/checksum is
  present, and no such string or table exists in the searched spaces.

### Inferred

* Row 3 is the Elven Fighter. The string ID 55, the flag-gated fourth slot and
  the hybrid stat line all support it, but a full legitimate playthrough was not
  performed, and the minimal patch does not draw the label.
* The low nibble of `0x030001F1` is a slot/aux field, not a second class gate
  (it is written by slot logic at `0x08685988`).

## 8. Unknowns

* Exact save-media byte/bit ordering and the full save-record field map. The
  packed 512-byte record and its CRC-8 location are known; the mapping of every
  character field is not, and the media type (EEPROM vs SRAM) was not confirmed.
* The label-drawing path that adds `ELVEN FIGHTER` when the flag is legitimately
  set was not isolated; the class-data path was.
* The specific 4-credit scene/credits unlock, if any, was not exercised; the
  `CREDITS` string exists (ID 621) but no menu entry was found.
* The second string/UI bank at `0x0866xxxx` was not fully diffed against the
  primary bank; sampled strings are identical, so it is treated as a duplicate
  (US/EU) bank, not a hidden alternate menu.

## 9. Tooling

* `binutils-arm-none-eabi` (`objdump -M force-thumb`).
* Capstone 5.0.7 (pointer/literal scans).
* Python 3 scripts in `/tmp/opencode/bgda/`:
  * `patch_state.py` — mGBA PNG savestate `gbAs` chunk decompress/edit/recompress;
  * `press.py` — xdotool key/combo helper;
  * `shot.sh` — scrot + crop to 720×480;
  * `strings_all.txt`, `dis_680000.txt` — string dump and 0x08680000–0x086B0000 disassembly;
  * `save_before_erase.sav` — a valid 512-byte save used for the tamper test.
* mGBA 0.10.5, Xvfb, openbox, xdotool, scrot, ImageMagick.

### Legal note

No ROM, extracted graphics, music or text is redistributed. This report contains
only hashes, addresses, algorithms, observations and original screenshots of
gameplay screens.

### Reproduction caveat

The analysis-only patch changes one byte of a **copy** of the ROM
(`/tmp/opencode/bgda/bgda_patch4.gba`, offset `0x068B64A`). It is not a cheat
code, is not part of the original image, and should not be distributed as a
patched ROM.
