# Altered Beast: Guardian of the Realms (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Altered Beast: Guardian of the Realms/Altered Beast: Guardian of the Realms.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `ALTEREDBEAST` (12 bytes at 0xA0) |
| Game code | `AARE` |
| Maker code | `78` |
| Fixed byte 0xB2 | `0x96` |
| Main unit / device | `0x00` / `0x00` |
| Software version | `0x00` |
| Entry branch | `0xEA00002E` → execution at `0x080000C0` |
| Stored complement check | `0x59` (computed `0x55`) |
| Stored header checksum | `0x0000` (computed `0xC73C`) |
| MD5 | `dc96748e298935c8e3d49e362cafa0b8` |
| SHA-1 | `194dc1fff5578dcd8a2a6914647f1b67334f2a8a` |
| SHA-256 | `4a82fb525d8cbf6e4a2df00db9b3d96c92735f4c39f84c2e83492641d9bf9e55` |

`file(1)` reports `AARE78, Rev.00`. The complement/header checksum fields are not
valid for the file (both are common in header-patched dumps); the game boots and
runs normally, and all addresses in this report are file offsets / addresses of
this exact SHA-256.

Embedded-header scan: the 156-byte Nintendo logo occurs **once**, at file
offset `0x4`. This is a single GBA image, not a multi-game pack.

## 2. Executive summary

**This revision has no password system, no button-code sequences, no debug
menu, and no unlockable hidden menu.** The strings `Invalid Password`, `Password` and
`Enter Password` exist in a text bank, but they are dead data: the engine's only
text-by-ID renderer is called from eight sites, and none of them ever passes a
password text ID. The three password text IDs are never drawn on any screen.

The only published "cheat" for the game is a GameFAQs entry saying *"Hold L or R
on the Main Menu to make the background speed up."* It was tested in the
emulator; no measurable change was observed, and the generic menu-input routine
does not read L/R at all, so it cannot be a hidden-menu gate. It is recorded as
unconfirmed.

The game's menu structure was enumerated completely: 26 outer screen states, 23
main-menu action branches, two main-menu definitions (with and without a stored
game), and the full text-ID table. Password-related IDs are 6, 18 and 21; the
only IDs passed to the dedicated text-by-ID renderer are 42, 44, 45, 48 and 66.
The save-gated `Review Progress` screen was also reached and observed (on a
temporary ROM copy with the first main-menu entry redirected to action `0x15`).
It is a 10-cell beast-form gallery with `CANIS` / `LOCKED` labels and the prompt
`PRESS SELECT TO CLEAR DATA`; Select opens `ARE YOU SURE YOU WANT TO ERASE YOUR
SAVED GAME?` (No/Yes). Its only text-by-ID draw is 42. **It has no password
field, cursor, or text entry.**

Consequently the correct §0.2 deliverable is a **bounded negative**: the
representable password space is empty, so no novel code can be minted and no
in-game acceptance/rejection can be demonstrated. The bounds are proven by the
text-ID call-site count, the action/screen tables, and an exhaustive button
matrix (28 combinations at the main menu, 8 at Options).

## 3. How to reproduce

Emulator and display used:

```bash
Xvfb :134 -screen 0 1024x768x24 &
DISPLAY=:134 openbox &
cd "roms/Altered Beast: Guardian of the Realms"
DISPLAY=:134 SDL_AUDIODRIVER=dummy mgba -3 "Altered Beast: Guardian of the Realms.gba"
```

mGBA SDL default keymap used: **A = `x`**, **B = `z`**, **L = `a`**, **R = `s`**,
**Start = `Return`**, **Select = `BackSpace`**, D-pad = arrow keys. Keys must be
held 100–300 ms; short taps are missed. Useful states: `Shift+F1..F10` saves,
`F1..F10` loads.

Menu path to every reachable screen:

1. Boot → legal screen → WOW logo → title (press Start).
2. Main menu: `NEW STORY`, `OPTIONS`, `MULTIPLAYER BRAWL`.
   - `OPTIONS`: `MUSIC`, `SOUND`, `SWAP BUTTONS`, `GAME CREDITS`.
   - `GAME CREDITS` starts the scrolling credits.
   - `MULTIPLAYER BRAWL` enters `WAITING FOR LINK…`; B cancels to the main menu.
   - `NEW STORY` → intro stills → first level (`Crete`).
3. In level: Start opens `RESUME GAME`, `OPTIONS`, `QUIT GAME`; `QUIT GAME` asks
   `REALLY QUIT?` with `NO`/`YES`.
4. Death/continue: `PRESS START`, `CONTINUES LEFT: n`, then a repeat of the
   intro; after continues are exhausted the game returns to the main menu.

`Review Progress` is the fourth entry of the save-present main-menu definition
and is not shown when no stored game exists. The no-save menu has exactly three
entries (observed, screenshot `screenshots/Altered Beast - main_menu.png`).

To observe the save-gated screen without a stored game, a **temporary copy** of
the ROM in `/tmp` was patched at file offset `0x256CF0`: entry 0's label became
`Review Progress` (`0x08255ADC`), its description `0x08255AEC`, and its action
field `0x15`. The unmodified target ROM was used for every system/validator
conclusion and for the button tests. The patched copy only substituted a menu
entry; it did not alter the screen handler. Observed screens:
`screenshots/Altered Beast - review_progress.png`,
`screenshots/Altered Beast - review_locked.png`,
`screenshots/Altered Beast - review_erase.png`.

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`. RAM addresses are GBA physical
addresses.

| Address / offset | Meaning |
|---|---|
| `0x08000000` | ARM entry branch (`0xEA00002E` → `0x080000C0`) |
| `0x08002754` | **Text draw by ID** (`r0` = menu context, `r1` = text ID) |
| `0x08003C6C` | Main-menu screen function |
| `0x080031B8` | `Review Progress` screen function (save review/erase) |
| `0x08003D788` | Generic menu-input routine (D-pad / A / B / Start) |
| `0x0804DBB8` | Text-bank descriptor: `{u32 count=1, u32 table=0x08257210}` |
| `0x08257210` | Text table base; first pointer at `0x08257214` |
| `0x08255CA0` | `"Invalid Password"` (text ID 6) |
| `0x08255CA8` | `"Password"` (text ID 18; points inside the previous string) |
| `0x08255D48` | `"Enter Password"` (text ID 21) |
| `0x08255E90` | `"Press Select to Clear Data"` (text ID 42) |
| `0x08256CF0` | Main menu, no stored game (3 entries) |
| `0x08256D70` | Main menu, stored game (4 entries, includes Review Progress) |
| `0x0804E330` | Main-menu action switch table (23 entries, action 0..22) |
| `0x08050C50` | Outer screen-state table (26 entries, state 0..25) |
| `0x0804DBBC` | Table of menu/resource-table pointers (indices 0..13) |
| `0x030000A8` | Key state, active-high (`Right` was `0x10` in a state diff) |
| `0x03000F2C` | RAM pointer to text-bank descriptor `0x0804DBB8` |

### Text table

`0x08257214 + 4*id` is a pointer to a NUL-terminated string. IDs 0–181 were
dumped (182 entries; the table ends with a null word at ID 182). The
password-related entries are:

| ID | Pointer | String |
|---:|---|---|
| 6 | `0x08255CA0` | `Invalid Password` |
| 18 | `0x08255CA8` | `Password` (substring of the ID-6 string) |
| 21 | `0x08255D48` | `Enter Password` |

## 5. Algorithm

### 5.1 Text-by-ID renderer (`0x08002754`)

```
draw_text_id(ctx, id):
    bank  = *(u32*)0x03000F2C          # -> 0x0804DBB8
    table = *(u32*)(bank + 4)          # -> 0x08257210
    s     = *(u32*)(table + id*4)      # NUL-terminated string
    create_text_sprite(ctx + 0x7C, s, ...)
```

This is the dedicated menu/HUD text-by-ID renderer. Its callers are enumerated
below. Other UI routines read the same text bank for fixed labels or for
resource fields (e.g. `bank+8`), but no caller passes IDs 6/18/21 to any of
them; the screen-state table independently contains no password state.

### 5.2 Menu item record (`0x20` bytes)

```
struct MenuItem {
    const char *label;      // +0x00
    u32 zero0;              // +0x04
    u32 zero1;              // +0x08
    const char *desc;       // +0x0C
    u32 zero2, zero3, zero4;// +0x10..+0x18
    u32 action;             // +0x1C
};
```

`0x08003D950` appends one item to the current menu; `0x08006F0C` loads one item
from a table and renders it.

### 5.3 Main-menu action dispatch (`0x0804E330`)

The switch at `0x08003D0A` accepts values `0..22` and jumps through
`0x0804E330`. Only these actions have non-default handlers:

| Action | Meaning | Handler | Result |
|---:|---|---|---|
| 2 | Options | `0x08003D1A` | Options screen |
| 3 | Continue Story | `0x08003DBA` | continue setup |
| 4 | New Story | `0x08003ED4` | story start |
| 7 | unidentified action | `0x08003FDE` | next state 13 |
| 0x15 (21) | Review Progress | `0x08003FE2` | next state 19 |
| 0x16 (22) | Multiplayer Brawl | `0x08003FE6` | next state 20 |

All other actions fall to the default `0x08003D8C`. There is no password action.

### 5.4 Outer screen-state machine (`0x08050C50`)

State is read from `[ctx+8]`, bounded to `0..25`, and dispatched through the
table. States relevant to this report:

| State | Handler | Meaning |
|---:|---|---|
| 0 | `0x0802ED4A` | boot/logo sequence |
| 1..4 | `0x0802ED96`… | intro / title transitions |
| 8 | `0x0802EE1A` | main menu (`0x08003C6C`) |
| 19 | `0x0802EE68` | **Review Progress** (`0x080031B8`) |
| 20 | `0x0802EE74` | Brawl setup |
| 21/22 | `0x0802EE86` / `0x0802EE96` | two-line dialogs |
| 23..25 | `0x0802EEC0`… | other game screens |

There is no state whose handler is a password entry/validator.

### 5.5 Password validator

**None exists.** A validator would need an input buffer and a caller; the only
text-entry-like UI in the engine is the menu system, which is selection-only.
The three password strings are not reachable from any of the 8 text-ID call
sites, and no code loads their string pointers directly (the only references are
the text-table slots themselves).

## 6. Tables

### 6.1 All call sites of the dedicated text-ID renderer

`BL` scan for `0x08002754`; the ID is the `movs r1,#imm` immediately before the
call. This is the complete caller set of that function:

| Call site | ID (hex) | ID (dec) | String |
|---|---:|---:|---|
| `0x080028F6` | `0x2C` | 44 | `CHOOSE FORM` |
| `0x08002F10` | `0x2D` | 45 | `CHOOSE SUBFORM` |
| `0x08002F70` | `0x42` | 66 | `Player 1` |
| `0x08002FAE` | `0x2C` | 44 | `CHOOSE FORM` |
| `0x08002FFA` | `0x2C` | 44 | `CHOOSE FORM` |
| `0x0800305E` | `0x2D` | 45 | `CHOOSE SUBFORM` |
| `0x0800312E` | `0x30` | 48 | `Sound` |
| `0x080032B4` | `0x2A` | 42 | `Press Select to Clear Data` |

**Password IDs 6, 18 and 21 never appear.** The union of drawn IDs is
`{42, 44, 45, 48, 66}`.

### 6.2 Main-menu definitions

No stored game (`0x08256CF0`):

| # | Label | Description | Action |
|---:|---|---|---:|
| 0 | `New Story` | `Press START to begin new game` | 4 |
| 1 | `Options` | `Press START to change game options` | 2 |
| 2 | `MULTIPLAYER BRAWL` | `Play Multi Player` | 0x16 |

With a stored game (`0x08256D70`):

| # | Label | Description | Action |
|---:|---|---|---:|
| 0 | `Continue Story` | `Press START to resume play` | 3 |
| 1 | `Review Progress` | `Press START to RESET STORED GAME` | 0x15 |
| 2 | `Options` | `Press START to change game options` | 2 |
| 3 | `MULTIPLAYER BRAWL` | `Play Multi Player` | 0x16 |

### 6.3 Other menu tables

| Address | Entries |
|---|---|
| `0x08256E10` | Options: Music, Sound, Swap Buttons, Game Credits |
| `0x08256EB0` | Options without credits |
| `0x08256F30` | Pause: Resume Game, Options, Quit Game |
| `0x08257030` | Quit confirm: No, Yes |
| `0x08256FB0` | Link pause: Keep Waiting, Options, Quit Game |
| `0x082570D0` | Link menu: Start game, Options, UnLink Game |

No sound-test, level-select, debug menu, or code-entry screen exists in these
tables. `MULTIPLAYER BRAWL` only reaches the link-wait screen without a second
GBA; B returns to the main menu. The brawl arena strings (`Arena : Pit Fight`,
etc.) are link-mode room names, not a level-select feature.

### 6.3a `Review Progress` screen contents (observed)

| Element | Observation |
|---|---|
| Title | `REVIEW PROGRESS` |
| Grid | 10 beast-form cells (2 rows × 5), plus a 4-cell bottom row |
| Selected label | `CANIS` on the unlocked cell; `LOCKED` on a locked cell |
| Prompt | `PRESS SELECT TO CLEAR DATA` |
| Select | `ARE YOU SURE YOU WANT TO ERASE YOUR SAVED GAME?` with `NO`/`YES` |
| Password/text entry | **None** |

The screen behaves as a save-slot form gallery, not a password screen.

### 6.4 Published codes tested

| Source | Code | Test | Result |
|---|---|---|---|
| GameFAQs (archived 2018-11-25) | “Hold L or R on the Main Menu to make the background speed up.” | Held L for 8 s at the main menu; 15 frame-pair RMSE samples compared with a no-key run | **Unconfirmed**: mean frame-pair RMSE 10,746 (L) vs 11,192 (baseline); no consistent speed-up. Generic menu input does not read L/R. |
| GameFAQs / VGChartz / TCRF | Any password | Searched all three; none published. TCRF explicitly states the game has no password system and the strings are unused. | No published password exists to test. |

### 6.5 String-search counts

Searched the whole 8 MiB image, case-insensitive:

| Term | Occurrences |
|---|---:|
| `password` | 2 (`0x255CA8` inside `Invalid Password`, `0x255D4E` inside `Enter Password`) |
| `cheat` | 0 |
| `debug` | 0 |
| `secret` | 0 |
| `unlock` | 0 |
| `level select` | 0 |
| `sound test` | 0 |
| `hidden` | 0 |
| `bonus` | 0 |
| `code` | 0 |

Printable runs ≥4 bytes: 55,554. Uppercase-alphanumeric runs ≥16: 366; these
are compressed-graphics/statistical runs, not input alphabets. The only
sequential ASCII alphabets are the font maps at `0x36C66E`, `0x373AB0` and
`0x369827` (ASCII→tile conversion), not password alphabets.

## 6b. Enumeration

### Space definition

**Representable password space: 0 values.** There is no password entry surface,
no alphabet table, no length check, and no validator. Text IDs 6, 18 and 21 are
allocated but are never passed to the only text-ID renderer.

### Counts

| Space | Size | Enumerated | Password/debug members |
|---|---:|---:|---:|
| Text table IDs | 182 (0–181) | 182 dumped | 3 allocated, **0 drawn** |
| Text-ID draw call sites | 8 | 8 | 0 password IDs |
| Outer screen states | 26 (0–25) | 26 mapped | 0 password states |
| Main-menu action branches | 23 (0–22) | 23 mapped | 0 password actions |
| Main-menu entries (no save) | 3 | 3 | 0 |
| Main-menu entries (save) | 4 | 4 (code/table) | 0 |
| Main-menu button combinations | 28 tested | 28 | 0 hidden screens |
| Options button combinations | 8 tested | 8 | 0 hidden screens |
| `Review Progress` screen | 1 | 1 observed | 0 password fields |
| `Review Progress` button combinations | 6 tested | 6 | 0 password prompts (Select = erase dialog) |
| Main-menu button sequences | 6 tested | 6 | 0 new screens |

### Novel code

**None can be minted.** With no entry surface, there is no way for the ROM to
accept or reject a password. This is the bounded-negative branch of §0.2, not an
incomplete positive result.

### Bounds proven by rejection

- A hypothetical code (`AAAAAAAA`, `INVALID1`, or any other 8-character string)
  has no screen on which it can be entered. The menu system is selection-only;
  there is no text field, keyboard grid, or character cursor in the 26-state
  screen table.
- Every single-button and modifier combination tested at the main menu either
  left the menu unchanged or entered one of the known screens (`New Story`,
  `Options`, `Multiplayer Brawl`). No combination produced a password prompt.
- At Options, Select/L/R/A/B combinations either stayed on Options, changed a
  setting, or returned to the main menu; no hidden sound-test/debug screen.
- Pressing A or Start on the default main-menu entry starts `New Story`; this is
  the normal confirm action, not a hidden path.

## 7. Validation evidence

### Observed (emulator screenshots / state)

- Boot, legal, WOW logo, title, main menu, Options, Game Credits, Brawl link wait,
  story intro, first level, pause, quit confirm, continue screen.
- Main menu without a save has exactly three entries.
- B cancels the Brawl link wait back to the main menu.
- `Review Progress` (reached on the temporary copy) shows the 10-cell form
  gallery, `CANIS`/`LOCKED` labels, the Select-to-clear prompt, and the
  `ARE YOU SURE YOU WANT TO ERASE YOUR SAVED GAME?` dialog.
- At `Review Progress`, L, R, Start, A+B, L+R and L+R+Select were tested; only
  Select opened the erase dialog. None produced a text-entry/password screen.
- At the main menu, six non-confirm sequences were tested: `L,R,L,R,L,R`;
  `Select×5`; `Down,Down,Up,Up,Left,Right`; `Up,Down,Up,Down,L,R`;
  hold `L+R+Select` for 2 s; and `Select×5` again. All left the three-entry menu
  unchanged.
- Holding L or R at the main menu produced no new screen and no measurable
  background-speed change in 15 sampled frame pairs.
- Savestate diff while holding Right showed `0x030000A8 = 0x10`, identifying the
  active-high key-state word.

### Derived (instruction / table analysis)

- `0x08002754` is the only text-by-ID resolver; its complete call-site set is the
  eight entries in §6.1.
- The text table contains IDs 6/18/21 but no call site passes them.
- The main-menu action switch (`0x0804E330`) has no password action.
- The outer screen table (`0x08050C50`) has no password state.
- The generic menu input (`0x08003D788`) checks D-pad/A/B/Start bits only; there
  is no L/R (0x100/0x200) branch.
- `Review Progress` (`0x080031B8`) has exactly one text-ID draw, ID 42; it enters
  its erase/dialog states through selection, not text input. The observed screen
  matches this: no field, no cursor, no alphabet.

### Inferred

- The password strings are leftovers from an abandoned password/progress-backup
  feature; they were replaced by the battery-backed save and the `Review
  Progress` screen.
- The GameFAQs L/R background note is either cosmetic and below the measurement
  threshold, or a false/rumoured code for this revision.

## 8. Unknowns

- `Review Progress` was reached on a temporary ROM copy by redirecting the first
  main-menu entry to action `0x15`; no legitimate stored game was produced. The
  screen and its erase dialog were observed, but the gallery contents are those
  of the default save state (one `CANIS` cell unlocked, the rest `LOCKED`).
  Whether a fully completed save adds further labels is not relevant to the
  password question: the screen has no input field in any code path.
- The exact visible effect of the published L/R background code (if any) was not
  isolated; no numeric change was measured.
- The header complement/checksum mismatch suggests this dump had its header
  fields patched or zeroed. Code addresses were not affected.
- The reason the developers left IDs 6/18/21 in the text table (rather than
  deleting them) is not knowable from the ROM.

## 9. Tooling

- mGBA 0.10.5 (SDL), Xvfb `:134`, openbox, xdotool, scrot, ImageMagick,
  tesseract.
- Python 3 with `capstone` 5.0.7 for Thumb scanning (BL targets, PC-relative
  literal loads, immediate extraction).
- Ghidra 12.1.4 via the REA bridge for decompilation of
  `0x08002754`, `0x08003C6C`, `0x080031B8` and the menu helpers.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for spot-checking every address quoted above.
- mGBA savestates were used for menu/level replay; the state format was decoded
  as PNG chunks (`gbAs` zlib stream, `0x61000`-byte `GBASerializedState`,
  IWRAM at `0x19000`, EWRAM at `0x21000`).

Screenshots (cropped to the 720×480 viewport) are in `screenshots/`:

- `Altered Beast - title.png`
- `Altered Beast - main_menu.png`
- `Altered Beast - options.png`
- `Altered Beast - credits.png`
- `Altered Beast - brawl.png`
- `Altered Beast - pause.png`
- `Altered Beast - continue.png`
- `Altered Beast - review_progress.png`
- `Altered Beast - review_locked.png`
- `Altered Beast - review_erase.png`

### Legal note

No ROM, extracted graphics, music, or game text is redistributed here. The
screenshots are menu-state evidence for the findings above.
