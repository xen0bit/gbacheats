# Backyard Skateboarding (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Backyard Skateboarding/Backyard Skateboarding.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title (`0xA0`) | `BYSK8NG2006` |
| Game code (`0xAC`) | `BS6E` |
| Maker code (`0xB0`) | `70` |
| Fixed byte `0xB2` | `0x96` (valid) |
| Software version (`0xBC`) | `0x00` |
| Complement (`0xBD`) | `0x0C` |
| Header checksum (`0xBE`) | `0x0000` |
| MD5 | `6b618c3fa5f38736632781b0a1ed2d23` |
| SHA-1 | `c0e4055ecfb5f40f290044c44de2e66e2d3da833` |
| SHA-256 | `16623544ea60a021f5fbee489a39b5250fdbc1c377dec2b0140b563d8cb78896` |

Header notes:

* The 4-byte entry at `0x00` is `2E 00 00 EA` (`b 0x080000C2`), so the entry is ARM at `0x080000C0`.
* The Nintendo logo occurs **once**, at file offset `0x4`. No second logo/header, no
  multiboot stub, no concatenated second image.
* The header is not intact: `sum(0xA0..0xBC) + 0x19 = 0x4DB`; the expected
  complement is `0x0B` but the stored byte is `0x0C`, and the checksum field is
  `0x0000` instead of the computed `0x0C`. The ROM still boots (mGBA does not
  enforce the header checksum). Treat this as a modified/repacked dump of the
  `BS6E` USA image, not a pristine retail header.

## 2. Executive summary

**There is no working in-game password or button-code cheat in this build.**

The ROM contains a complete-looking cheat *mechanism* and the text of two button
codes, but the code path that would act on them is unreachable:

1. The credits contain two 8-press button codes and the line
   `ON THE TITLE SCREEN` (`0x081C45F0`–`0x081C496C`). The natural reading of the
   two credit blocks is:
   * `L, R, B, B, L, L, R, R` — "ALL LEVELS, TO UNLOCK ALL RIDERS"
   * `R, LEFT, RIGHT, B, DOWN, UP, DOWN, UP` — "TRY OUT THIS CHEAT"
2. The main-menu screen handler (`0x080284B4`, screen id 5) contains a **fifth,
   hidden dispatch case** at `0x080285B8` that sets the game state byte
   `gameState[4] = 1`. That byte is the game's **"unlocked mode"**: the save menu
   switches from the normal overwrite warning to
   `currently in unlocked mode: saving disabled` (`0x081BCEDC`). Case 4 then
   continues into the normal new-game path, i.e. it starts a new tour with all
   levels and riders unlocked and saving disabled.
3. Case 4 is selected by the menu accept handler passing **item index 4** to the
   handler. The main menu is a list whose runtime count is **4** (read directly
   from the list object), whose selected index is bounds-checked against that
   count, and whose only event-5 call site (`0x08031356`) passes the list index.
   The fifth entry in the menu item table (`0x08064238`) is an all-NULL
   terminator, not a hidden item. Consequently **no normal input can produce
   index 4**, and the unlock case is dead code.
4. The title-screen input handler (`0x080287F4`) tests only `keypressed & 0x009`
   (A and Start). The generic menu/pause input handler (`0x0803132x`) tests only
   A (`0x001`), B (`0x002`), D-pad Down/Up/Left/Right (`0x080/0x040/0x020/0x010`).
   The L and R shoulder bits (`0x200`/`0x100`) are never tested by any front-end
   screen; a whole-ROM scan finds no `cmp/tst/ands` with those key masks in the
   front-end code (the only `0x200` values found are struct offsets such as
   `0x80 << 2`).
5. Both codes were entered at the title, main menu and credits at 0.05–0.20 s
   per press, in forward, reverse and L/R-swapped order, and with the D-pad
   reading of `L/R`. None produced any observable change: no unlocked mode, no
   menu change, no save-disable message.
6. A control experiment proves the test would have detected success. Patching
   the fifth dispatch-table slot so that selecting NEW GAME routes to case 4
   immediately sets `gameState[4] = 1`, reproducing the unlock. Patching only
   the *write* to `gameState[5]` made a persistent marker that still never
   fired under any tested input.

The only other plausible in-series mechanism — a name-based cheat like
Backyard Baseball 2006's coach-name table — is also absent: the game has an
`ENTER NAME` UI (`0x081BCC10`, alphabet at `0x081BAC28`/`0x081BCC28`, name
record at `0x08067A00`) but no name-comparison or name-to-unlock table exists.
`password`, `passwords`, `coach`, `debug` and `hidden` occur **zero** times in
the extracted strings; the four `cheat` hits are the two `CHEATING` score
words and the two credit hint lines.

**Bottom line:** the credits advertise codes that the retail front-end cannot
accept. The "unlocked mode" implementation is present but unreachable. This is a
bounded negative result, not an incomplete search: the acceptor is dead, so the
accepted code space is empty.

## 3. How to reproduce

Emulator and environment:

```bash
Xvfb :159 -screen 0 1024x768x24 &
DISPLAY=:159 openbox &
DISPLAY=:159 SDL_AUDIODRIVER=dummy mgba -3 \
  "roms/Backyard Skateboarding/Backyard Skateboarding.gba" &
```

mGBA 0.10.5 SDL keymap used:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Held key tests use 100–300 ms; menu presses use 120–200 ms.

Observed screen path:

1. ATARI logo → Full Fat logo → title with `PRESS START`.
2. `START` → **MAIN MENU**: `NEW GAME`, `CONTINUE GAME` (disabled/grey),
   `MULTIPLAYER`, `CREDITS`.
3. `MULTIPLAYER` → `CONNECT`, `SELECT SKATER`; `SELECT SKATER` shows the
   roster and `L/R CHANGE` (the change keys are the **D-pad** Left/Right, not
   the shoulder buttons).
4. `CREDITS` → auto-scrolling credits; the two cheat hints scroll past. The
   credits contain no input prompt.
5. `NEW GAME` → intro cut-scene → tutorial (NEIGHBORHOOD, five rookie lessons:
   OLLIE, POWERSLIDE, GRIND-TO-GRIND, KICKFLIP, MANUAL).
6. In the tutorial, `START` opens **PAUSE**: `CONTINUE`, `RESTART CHALLENGE`,
   `END CHALLENGE`, `TOUR BOOK`, `TRICK LIST`, `SOUNDTRACK`, `EXIT`.
   `TOUR BOOK` opens the lesson list; `TRICK LIST` and `SOUNDTRACK` are
   list/audio screens. `EXIT` asks `ARE YOU SURE YOU WANT TO EXIT THE GAME IN
   PROGRESS?` then `SAVE GAME? YES/NO`.
7. After saving and exiting a challenge the game reaches **TOUR HOME**:
   `PLAY GAME`, `SELECT LEVEL`, `SELECT SKATER`, `CUSTOMIZE SKATER`,
   `TOUR SUMMARY`, `SETTINGS`.
   * `SELECT LEVEL` — four thumbnails, three locked; per-level challenge counts.
   * `CUSTOMIZE SKATER` — `NAME`, `LOOKS`, `UPPER GEAR`, `LOWER GEAR`,
     `BOARD`, `SKILLS`; gear opens `CUSTOMIZE GEAR` (HELMET/GRAPHICS/SHIRT/
     DESIGN).
   * `SETTINGS` — `CONTROL TYPE`, `MUSIC VOLUME`, `SFX VOLUME`; no cheat item.

Codes tested (all at the title screen, main menu, and credits; the table is the
complete matrix, not a sample):

| Sequence | Orders/timings tested | Result |
|---|---|---|
| `L,R,B,B,L,L,R,R` | forward, reverse, L/R-swapped; 0.05, 0.08, 0.10, 0.12, 0.18, 0.20 s | no effect |
| `R,LEFT,RIGHT,B,DOWN,UP,DOWN,UP` | forward, reverse; 0.06–0.20 s | no effect |
| `LEFT,RIGHT,B,B,LEFT,LEFT,RIGHT,RIGHT` (D-pad reading of code 1) | forward; 0.15 s | no effect |
| `RIGHT,LEFT,RIGHT,B,DOWN,UP,DOWN,UP` (D-pad reading of code 2) | forward; 0.15 s | no effect |
| all 45 two-button combinations at main menu | simultaneous 180 ms press, then A | no effect |
| every single button at main menu | 200 ms press | no effect |
| menu navigation `UP/DOWN` 1–5 steps, then A | — | no effect |

After each test the emulator state was saved and the game-state byte was read
directly (see §4). A successful case-4 dispatch sets `gameState[4] = 1`; it was
`0` in every test.

Savestate workflow: mGBA `Shift+F1..F10` saves, `F1..F10` loads; the saved PNG
contains a zlib `gbAs` chunk. Decompressed state layout used here:

| State offset | RAM |
|---|---|
| `0x19000`–`0x20FFF` | IWRAM (`0x03000000`–`0x03007FFF`) |
| `0x21000`–`0x60FFF` | EWRAM (`0x02000000`–`0x0203FFFF`) |

The game-state pointer is the word at IWRAM `0x03000B58`; at the menu it is
`0x020008E4`, so `gameState[4]` is EWRAM `0x020008E8` (state offset `0x218E8`).

## 4. Address map

All addresses are ROM addresses (`file offset + 0x08000000`) unless marked RAM.

### 4.1 Front-end screens

| Address | Meaning |
|---|---|
| `0x08028648` | Title / PRESS START handler (screen id 4) |
| `0x080286BC`–`0x080286DE` | builds the PRESS START text from the 5-language array at `0x080642A0` |
| `0x080287F4`–`0x0802880A` | title input: `keypressed & 9` → `0x0802F5A4` (A or Start only) |
| `0x080284B4` | Main-menu screen handler (screen id 5) |
| `0x08028590`–`0x0802859E` | event-5 dispatch: `index = param >> 16`, bounds `<= 4`, jump through table `0x080285A4` |
| `0x080285A4` | dispatch table: `[0x080285C0, 0x080285E4, 0x08028610, 0x08028638, 0x080285B8]` |
| `0x080285B8`–`0x080285BE` | **case 4 (hidden):** `gameState[4] = 1` (unlocked mode), then falls through to `0x080285C0` |
| `0x080285C0` | case 0: new game |
| `0x080285E4` | case 1: continue |
| `0x08028610` | case 2: multiplayer |
| `0x08028638` | case 3: credits |
| `0x0802853E`–`0x08028542` | normal new-game path resets `gameState[4] = 0` |
| `0x0802F32E`–`0x0802F342` | save menu chooses message from `gameState[4]` |
| `0x0802FE58` | generic handler trampoline: `handler(screenMgr, event, param, handlerPtr)` |
| `0x0803132x` | generic list input/accept handler (see §4.3) |
| `0x080280E0`, `0x08028148`, `0x08028340`, `0x080283E0` | other front-end screen handlers (results, pause-adjacent) |

### 4.2 Main-menu data

| Address | Meaning |
|---|---|
| `0x08067D14` | screen-5 definition: `{flags=0x00010006, menudef=0x08064270, ?, layout=0x08064258, handler=0x080284B5}` |
| `0x08064270` | `MAIN MENU` text record (5 languages) |
| `0x08064258` | layout record: `00F0 0030 0020 0030`, font `0x08063E50`, item table `0x080641B8` |
| `0x080641B8` | item group 0 `NEW GAME` (5 language pointers + 3 padding words) |
| `0x080641D8` | item group 1 `CONTINUE GAME` (disabled when no save) |
| `0x080641F8` | item group 2 `MULTIPLAYER` |
| `0x08064218` | item group 3 `CREDITS` |
| `0x08064238` | item group 4: **all pointers NULL** — list terminator |
| `0x080642A0` | PRESS START 5-language array (used by the title handler) |
| `0x080642B4` | 24-entry u16 button-mask array; values are direction/button glyph tokens. No code xref exists to this table; it is UI/leftover data, not the cheat table |

### 4.3 Menu list and accept path

| Address | Meaning |
|---|---|
| RAM `0x03000634` | global list object used by the generic menu handler |
| list `+0x0C` | pointer to item array (stride `0x4C` bytes) |
| list `+0x14` | item count |
| list `+0x24` | selected index |
| item `+0x44` | disabled flag (CONTINUE GAME has `1`) |
| `0x0805665C` | `list_select(list, index)`: rejects `index < 0`, `index >= count`, disabled items; writes `+0x24` |
| `0x08056734` | `list_item_id(list)`: returns id of current item |
| `0x08056768` | `list_index(list)`: returns `[list+0x24]` |
| `0x0803132x` | input handler: D-pad Down/Up → `list_select(±1)`; Left/Right → `0x08056570(list, 0/1)`; A → event 5 with `(index<<16)|item_id`; B → event 6 |
| `0x08031356` | **the only** call site of `0x0802FE58` with event 5 |

Runtime read at the main menu (savestate, after `PRESS START`):

```
list+0x14 (count) = 4
list+0x24 (index) = 0
item 0 NEW GAME       disabled=0
item 1 CONTINUE GAME  disabled=1
item 2 MULTIPLAYER    disabled=0
item 3 CREDITS        disabled=0
```

Because the count is 4, `list_select` can only produce indices 0–3, and the only
event-5 call site forwards exactly that index. No code writes 4 to `[list+0x24]`
except `list_select`, which rejects it.

### 4.4 Input

| Address | Meaning |
|---|---|
| `0x08055CE8` | per-frame input update |
| RAM `0x030058F0`, `0x030059F0` | held-key mask (`~KEYINPUT`; low 10 bits are the held buttons) |
| RAM `0x030059F4` | previous held mask |
| RAM `0x030059F8`/`0x030059FC` | pressed/released edge masks |
| RAM `0x03005A00`/`0x03005A04` | pressed/released accumulators |
| RAM `0x03005900` | 10-entry (0x18-byte) per-key repeat table |
| `0x04000130` | KEYINPUT (literal at `0x0803E54C`, `0x08055C2C`, `0x08055D70`) |

Key mask values (active-high after `~KEYINPUT`): A `0x001`, B `0x002`,
Select `0x004`, Start `0x008`, Right `0x010`, Left `0x020`, Up `0x040`,
Down `0x080`, R `0x100`, L `0x200`.

### 4.5 Strings / tables

| Address | Meaning |
|---|---|
| `0x081C45F0` | `...ALL LEVELS,` |
| `0x081C4600` | `TO UNLOCK ALL RIDERS...` |
| `0x081C4618`–`0x081C466C` | `L BUTTON, R BUTTON...` / `B BUTTON, B BUTTON,` / `L BUTTON, L BUTTON,` / `R BUTTON, R BUTTON,` / `ON THE TITLE SCREEN` |
| `0x081C4680` | `OKAY NOW, TRY THIS NEW CHEAT` |
| `0x081C491C`–`0x081C496C` | `R BUTTON...` / `LEFT, RIGHT, B BUTTON` / `DOWN, UP, DOWN, UP,` / `ON THE TITLE SCREEN:` / `TRY OUT THIS CHEAT` |
| `0x08076654` | first credits script (includes the "unlock all riders" block at indices 26–33) |
| `0x080766E8` | second credits script (includes the second cheat block at indices 53–57) |
| `0x08076764` | third credits script (same second block at indices 22–26) |
| `0x081BCEDC` | `currently in unlocked mode: saving disabled.` |
| `0x081BCDE0` | `warning: saving will overwrite the previously saved game.` |
| `0x08067B24`, `0x08067B38` | message descriptors used by the save menu |
| `0x081BCC10` | `ENTER NAME` |
| `0x081BCC28`–`0x081BCC78` | name-entry alphabet `z y x ... e` (plus `spc`, `.`, `&`, `-` at `0x081BCC24`, `0x081BCC20`, `0x081BCC1C`) |
| `0x08067A00` | name-entry UI table (letter pointers) |

## 5. Algorithm

### 5.1 What the hidden unlock case would do

```
; 0x080285B8 (case 4 only)
gs = *(u32*)0x03000B58          ; 0x020008E4 at the menu
gs[4] = 1                       ; "unlocked mode"
[0x03000200] = 0
[0x030001FC] = 1
0x0803D688(1)                   ; reset/transition
0x0803D338()                    ; start new-game path
state = 0x30
```

`gs[4] != 0` makes the save confirmation at `0x0802F336` select the descriptor
at `0x08067B38` (`currently in unlocked mode: saving disabled`)
instead of `0x08067B24` (`warning: saving will overwrite...`). Normal new game
(`0x0802853E`) writes `gs[4] = 0`, so unlocked mode is single-session and
unsaved by design.

### 5.2 Why it cannot be reached

```
handler_event5(param):
    index = (param >> 16) & 0xFFFF
    switch (index):
        0: new_game()
        1: continue_game()
        2: multiplayer()
        3: credits()
        4: unlocked_new_game()      ; dead
        default: return

generic_menu_input():
    ...
    if pressed & 0x001:             ; A
        idx  = list_index(list)     ; [list+0x24]
        id   = list_item_id(list)
        handler_event5((idx << 16) | id)   ; only call site: 0x08031356
```

`list_index` is `[list+0x24]`; `list_select` is the only writer and enforces
`0 <= index < [list+0x14]`. At runtime `[list+0x14] == 4`. Therefore
`index ∈ {0,1,2,3}` and case 4 has no caller.

The five-entry appearance of the item table is misleading: group 4
(`0x08064238`) is an all-zero terminator. Replacing it with five valid label
pointers makes the menu builder scan past the table into the following layout
data and hang at the title→menu transition, confirming that the builder scans
for a NULL terminator and that a fifth item is not part of the shipped list.

### 5.3 Why the printed codes cannot be the trigger

* Title handler (`0x080287F4`) accepts only A and Start: `movs r0,#9; ands`.
* Main-menu/pause input (`0x080313x`) accepts A, B, D-pad Down/Up/Left/Right.
* A whole-ROM Thumb scan for `cmp/tst/ands/movs` with `0x100`/`0x200` finds no
  front-end key test with those masks; the `0x200` hits are struct offsets
  (e.g. `0x80 << 2` used as `0x200` bytes into a state block).
* Hence `L BUTTON` / `R BUTTON` (shoulder L/R) can never be observed by the
  title screen or any menu, and the eight-press codes cannot be consumed there.

## 6. Tables

### 6.1 Main-menu items and cases

| Index | Label | Handler case | Action |
|---:|---|---|---|
| 0 | `NEW GAME` | 0 (`0x080285C0`) | normal new tour, `gs[4]=0` |
| 1 | `CONTINUE GAME` | 1 (`0x080285E4`) | continue; disabled if no save |
| 2 | `MULTIPLAYER` | 2 (`0x08028610`) | link/multiplayer |
| 3 | `CREDITS` | 3 (`0x08028638`) | credits |
| 4 | — (no item) | 4 (`0x080285B8`) | unlocked new tour, `gs[4]=1`, saving disabled |

### 6.2 Credits hint blocks

`0x08076654` indices 26–33 (read from the top of the block downward):

```
OKAY NOW, TRY THIS NEW CHEAT
ON THE TITLE SCREEN
L BUTTON, R BUTTON...
B BUTTON, B BUTTON,
L BUTTON, L BUTTON,
R BUTTON, R BUTTON,
TO UNLOCK ALL RIDERS...
...ALL LEVELS,
```

`0x080766E8` indices 53–57:

```
TRY OUT THIS CHEAT
ON THE TITLE SCREEN:
DOWN, UP, DOWN, UP,
LEFT, RIGHT, B BUTTON
R BUTTON...
```

### 6.3 Key masks

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

## 6b. Enumeration

### 6b.1 Space definition

* Alphabet: the 10 GBA buttons actually readable by the front-end input code
  (A, B, Select, Start, Right, Left, Up, Down, R, L) — 10 symbols.
* Length of each documented code: 8 presses.
* Representable space per code: `10^8 = 100,000,000`.
* Documented codes: 2 (the two credit blocks), so 200,000,000 representable
  8-press strings are described by the ROM text.
* Storage model: **none**. There is no code table, no checksum, no key mask
  table and no generator associated with the hints. The only `u16` button-mask
  array in the ROM (`0x080642B4`, 24 entries) has no code xref and does not
  encode either hint under any tested reading.
* Accepted subset in this build: **∅**. The acceptor (case 4) has no reachable
  caller, and the input handlers cannot observe the L/R symbols the hints use.

### 6b.2 Novel codes

A novel accepted code cannot exist when the accepted set is empty. The
enumeration was therefore pushed into the acceptor instead of the string space:

* The main-menu list was read at runtime: count 4, index 0.
* Its only accept path (`0x08031356`) can pass indices 0–3.
* The handler's index-4 slot (`0x080285B8`) was exercised by a controlled patch
  (dispatch table slot 0 redirected to `0x080285B8`). Pressing A on NEW GAME
  then executed case 4 and set `gameState[4] = 1` — i.e. the acceptor works, but
  no shipped input reaches it.
* An instrumented ROM that changed the unlock write from `gameState[4]` to
  `gameState[5]` (so it is not reset by the new-game path) was driven with every
  code and reading in §3 and never set the marker.

This is the enumeration result: the representable text space is 200 million
strings, the reachable input space at the acceptor is 4 indices, and the
intersection is empty.

### 6b.3 Bounds proven by rejection

| Test | Expected if accepted | Observed |
|---|---|---|
| `L,R,B,B,L,L,R,R` at title (0.05–0.20 s) | `gs[4]=1` / menu change | `gs[4]=0`, menu unchanged |
| same at main menu | same | same |
| same at credits | same | same |
| reverse `R,R,L,L,B,B,R,L` | same | same |
| L/R-swapped `R,L,B,B,R,R,L,L` | same | same |
| `R,LEFT,RIGHT,B,DOWN,UP,DOWN,UP` (forward/reverse) | same | same |
| D-pad readings of both codes | same | same |
| all 45 two-button combos, then A | same | same |
| each single button at main menu | same | same (A only starts NEW GAME) |
| 5th item table slot | a 5th menu item | NULL terminator; replacing it hangs menu build |
| control: dispatch slot 0 → case 4 | `gs[4]=1` | `gs[4]=1` (patch accepted) |

The control row is the key bound: the test method is proven sensitive to the
exact effect the hints promise.

## 7. Validation evidence

**Observed**

* Header, hashes, single logo hit, invalid header checksum/complement.
* Title, MAIN MENU (4 items), MULTIPLAYER (CONNECT / SELECT SKATER),
  SELECT SKATER (D-pad Left/Right changes skater), CREDITS scroll,
  NEW GAME intro/tutorial, PAUSE (7 items), TOUR HOME (6 items),
  SELECT LEVEL (4 thumbnails, 3 locked), CUSTOMIZE SKATER / CUSTOMIZE GEAR,
  SETTINGS (3 items), SAVE GAME? confirmation.
* Runtime list object: count 4, index 0, item 1 disabled.
* Save confirmation text is the normal overwrite warning, i.e. `gs[4]=0`.
* All code/input tests in §3 and §6b.3 produced no unlock/menu/save change.
* Control patch to dispatch case 4 sets `gs[4]=1`.

**Derived**

* Case 4 is the only writer of `gs[4]=1`; the save menu reads it.
* The only event-5 call site forwards the list index; the list bounds-check
  rejects index 4.
* The title handler's mask (`9`) and menu handler's masks exclude L/R shoulder.
* No password/name table exists in the scanned text space.

**Inferred**

* The credits hints are developer flavour/leftover text whose trigger was not
  wired into this front-end build (or was removed before the `BS6E` build).
* `gameState[4]` is a developer "unlocked mode" flag; its save-disable behaviour
  is deliberate (shown by the dedicated message).

## 8. Unknowns

* The exact retail-vs-dump history of this `BS6E` image (header checksum zeroed,
  title `BYSK8NG2006`, complement byte mismatch). All addresses are for this
  file only.
* The `ENTER NAME` path was observed in the menudef/string data but not driven
  to completion; no name-comparison or name-to-unlock table was found, so a
  name cheat is not supported by static evidence, but a name whose only effect
  is cosmetic was not exhaustively typed.
* Whether a *different* regional/revision build wires case 4 to a reachable
  input. This report claims the negative only for the hashed file above.

## 9. Tooling

* `strings -t x -n 4` (43,055 lines) for text reconnaissance.
* Python 3 + Capstone 5.0.7 for whole-ROM Thumb scans (key masks, single-bit
  tables, BL targets, literal loads).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000
  -M force-thumb` for manual disassembly.
* mGBA 0.10.5 SDL under Xvfb `:159`, `xdotool`, `scrot`.
* Python helpers in `/tmp/opencode/bskate/tools/`:
  * `seqscan.py`, `cscan2.py`, `cscan3.py`, `cscan4.py` — key-mask/table scans
  * `pngstate.py`, `diffstate.py` — mGBA PNG `gbAs` state reader/differ
  * `probe.py`, `marker_test.py`, `marker_noaccept.py`, `trytitle.py`,
    `trymenu.py`, `trycredits.py`, `brute_menu.py`, `single_menu.py` —
    emulator input harnesses and oracles
  * `test_unlock.gba` — item-table patch (5th slot populated; menu build hangs,
    proving the NULL terminator)
  * `marker.gba` — unlock write redirected to `gameState[5]` (persistent marker)
  * `marker2.gba` — dispatch slot 0 redirected to case 4 (positive control)

Screenshots are in `/tmp/opencode/bskate/shots/` (title, main menu,
multiplayer, select skater, credits, tutorial, pause, tour home, select level,
customize, settings, save confirmation, and the code-entry attempts).

## 10. Legal note

No ROM, extracted graphics, audio, or copyrighted text is redistributed with
this report. Only hashes, addresses, instruction semantics, and short UI labels
necessary to identify the mechanism are included.
