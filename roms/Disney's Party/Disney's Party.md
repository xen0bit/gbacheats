# Disney's Party (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney's Party/Disney's Party.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| MD5 | `8dbd6bfdff54f2fc0f1bbde11706a803` |
| SHA-1 | `d4ad55cd32017a853c85f6247935c75f9b8cb7bc` |
| SHA-256 | `b1a08ee29d5d493d811e31404dbb52292a33f3534b5d19b9a516dfdee28c9dc9` |
| Header title (0xA0) | `DISNEY PARTY` |
| Game code (0xAC) | `BD8E` |
| Maker code (0xB0) | `69` (Hudson Soft) |
| Version (0xBC) | `0x00` |
| Complement (0xBD) | `0x63` — **valid** (`-(sum 0xA0..0xBC + 0x19)` = 0x63) |
| Header checksum (0xBE) | `0x0000` (zeroed; rebuilt-header/dumper artifact) |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |

No cracktro, trainer or entry patch: `0x080000C0` is the ordinary ARM crt0
(`msr CPSR, #0x12; ldr sp,=0x03007FA0; ...`), the IRQ handler store at
`0x080000D8` and the Thumb `main` pointer `0x0800082D` at header `+0x1EC` are
stock. The complement is valid, so the header was not edited after the build;
only the 16-bit header checksum field is zero, which is the common artifact of
a rebuilt/redumped header. Both hashes match 3rd party cheat indexes' "Good" dump
`Disney's Party (USA, Europe) (En,Fr,De,Es,It).gba` (SHA-1
`d4ad55cd…c75f9b8cb7bc`), so this is the standard five-language retail image.

A **second, complete GBA header** exists at file offset `0x356710` (logo at
`0x356714`): blank title/code, maker `01`, complement `0xF0` (valid), entry
`0xEA00002E`. It is followed by an ARM image containing the strings `Multi`,
`SioSync4`, `32Load`, `10214` (`0x3586B1`..) — the GBA multiboot/serial
transfer stub, i.e. the child image used for single-cartridge link play. It is
not a second game and contains no cheat surface.

## 2. Executive summary

**There is no in-game password, cheat-code or button-code system in this
ROM.** No text-entry field, no alphabet table, no accepted-string table and no
button-sequence table exists anywhere in the 8 MiB image. The only published
codes (3rd party cheat indexes) are CodeBreaker RAM
patches — memory edits applied by the cheat device, not content entered in the
game — and are out of scope here. The ROM contains no in-game equivalent.

**A complete, working developer debug menu is present but unreachable from the
retail code.** It is two levels deep:

* a 4-option developer menu (`FURUKAWA / KITAWAKI / SUGATA / TAKEMOTO` at the
  screen) whose option 2 opens the debug menu;
* the debug menu itself (`ｵﾚｻﾏ DEBUG MODE`) with eight entries:
  `EVENT, BOTS_SEL, MENU, OPENING, MINIGAME MENU, ATTRACTION MENU, ENDING,
  MESSAGE`.

Each entry was driven in mGBA and its effect recorded (§6b). The whole
component is a closed reference cycle: the only installer of each stage is the
previous stage, and no pointer to any of its entry addresses exists anywhere
else in the image, so no shipped input path can reach it. This is dead code,
not cut content — when the task pointer is set from a debugger/savestate the
menus run and behave normally.

A secondary finding is the embedded multiboot child image at `0x356710`, which
is the link-play client sent to other GBAs.

## 3. How to reproduce

Emulator: mGBA (SDL) under Xvfb.

```bash
Xvfb :334 -screen 0 1024x768x24 &
DISPLAY=:334 openbox &
cd "roms/Disney's Party"
DISPLAY=:334 SDL_AUDIODRIVER=dummy mgba -3 "Disney's Party.gba" &
W=$(DISPLAY=:334 xdotool search --name mGBA | head -1)
DISPLAY=:334 xdotool windowfocus "$W"
```

Default mGBA SDL keymap used here: **A = `x`, B = `z`, L = `a`, R = `s`,
Start = `Return`, Select = `BackSpace`, D-pad = arrows.** Hold keys 100–150 ms.
Screenshots: `import -window root` then crop 720×480 at the window's absolute
upper-left (query with `xwininfo -id $W`).

Normal menu path observed from a cold boot:

1. Language select — 5 entries (`ENGLISH, FRANÇAIS, DEUTSCH, ITALIANO,
   ESPAÑOL`); index wraps 0↔4. Index is byte `0x02017088`.
2. EA logo → `jupiter` logo → title. One option only: **New Game**.
3. Player-count dialog (`1P`..`4P`, `1`–`4` players).
4. Character select (`1P`): Mickey, Minnie, Donald, Daisy; cursor wraps in a
   4-entry ring (`Right` at Daisy → Donald).
5. `Tour Selection` ("Disney's PARTY Passport"), **Days 1–4**.
6. `Island Selection` — five islands on a map, moving highlight ring, `A` on an
   island confirms.
7. Stage intro dialogue → board. `Start` shows the modal **Pause** box.

No other user-reachable screen was found. Static bound: `0x08003234` is the
scene/task installer; its 74 call sites name **49 distinct scene init
functions** in the image, and every screen reached above is one of them.

### Re-entering the dead debug menus (labelled debugger intervention)

The debug menus cannot be reached by input. To inspect them, the mGBA
savestate was decompressed (`gbAs` chunk, zlib, 397,312-byte state; IWRAM at
state `0x19000`, EWRAM at state `0x21000`), EWRAM `0x020156F0` (the "next scene
init function" pointer) was overwritten, and the state reloaded:

| Pointer written | Screen |
|---|---|
| `0x08021DA9` | debug menu (`ｵﾚｻﾏ DEBUG MODE`, 8 entries) directly |
| `0x0800E34D` | parent 4-option developer menu |

This is an analysis aid, not a claim of reachability. The same pointer is
normally written by shipped code with values such as `0x08024805`,
`0x08026AE9`, `0x0800F819`.

## 4. Address map

All addresses are ROM (`0x08000000 + file offset`) unless marked RAM.

### Engine state

| Address | Meaning |
|---|---|
| `0x020156F0` (EWRAM) | pointer to the next scene/task init function |
| `0x02015B58` (EWRAM) | engine "input/scene ready" word; `1` at runtime |
| `0x030005B0` (IWRAM) | key state struct: `+0` unknown, `+4` held, `+6` new presses, `+8` repeat |
| `0x080002FC0` | key reader: `~KEYINPUT & 0x3FF` → `0x030005B4/6` |
| `0x08003234` | scene/task installer (`r0` = Thumb function pointer) |
| `0x080310E8` | "call init pointer from RAM" helper used by scene wrappers |
| `0x02017088` (EWRAM) | language index, 0..4 (language screen only) |

### Parent 4-option developer menu

| Address | Meaning |
|---|---|
| `0x0800E34C` | setup/draw (window 48×44 at 0,0; loads graphic `0x080AD000`) |
| `0x0800E448` | gate: if `[0x02015B58] != 0`, install input handler |
| `0x0800E464` | input: Up/Down change option `0x02017020` (0..3), A/Start confirms |
| `0x0800E54C` | option dispatch (reads `0x02017020`) |
| `0x0800E5C0` | option 0 handler → re-installs `0x0800E34C`, chains `0x0800E5F0` |
| `0x02017020` (EWRAM) | selected option 0..3 |
| `0x02017024` (EWRAM) | auxiliary byte cleared by setup (unused by dispatch) |
| `0x02017090` (EWRAM) | set to `1` by setup |

Dispatch targets: option 0 → `0x0800F818` (ending), 1 → `0x0801342C`
(Wild Garden stage), 2 → `0x08021DA8` (debug menu), 3 → `0x080106B4`
(board/results screen).

### `ｵﾚｻﾏ DEBUG MODE` menu

| Address | Meaning |
|---|---|
| `0x080BC8D8` | name table: `ｵﾚｻﾏ DEBUG MODE`, `EVENT`, `BOTS_SEL`, `MENU`, `OPENING`, `MINIGAME MENU`, `ATTRACTION MENU`, `ENDING`, `MESSAGE` (`0xBC8D8`–`0xBC93C`) |
| `0x080BC940` | 16 × u16 single-bit mask list `0x0001..0x8000` (debug display helper) |
| `0x080218C0` (file `0x218C0`) | menu draw/setup (loads VRAM from `0x08633144`, draws 8 rows) |
| `0x08021B30` | input: Up/Down move selection `0x02004574` (0..7), Left/Right edit params, A dispatches |
| `0x08021CF0` | dispatch: `handler = table[ [0x02004574] ]` |
| `0x08021D04` | base pointer word `0x08021D08` |
| `0x08021D08` | handler table, 8 × u32: `0x08021D28, D40, D4C, D58, D68, D74, D80, D8C` |
| `0x08021DA8` | init: clears `0x02004574/76/78`, starts the menu |
| `0x02004574` (EWRAM) | selected entry 0..7 |
| `0x02004576` (EWRAM) | EVENT parameter: index into the 155-entry `EVT_*` name table (0..154) |
| `0x02004578` (EWRAM) | MESSAGE parameter: message id (0..224) |

## 5. Algorithm

### 5.1 Scene/task chain

`main` (`0x0800082C`) stores `0x0800F0BD` into `0x020156F0` and calls
`0x080031F0`. Every scene wrapper is a Thumb function that:

1. sets up graphics/music, then
2. writes its successor scene init pointer to `0x020156F0` and/or calls
   `0x08003234(pointer)`.

Input handlers read `0x030005B0+6` (new presses). The key mask convention is
the standard active-high one: A=1, B=2, Select=4, Start=8, Right=0x10,
Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200.

### 5.2 Debug menu dispatch

```
on every frame:                              # 0x08021B30
  k = pressed(0x030005B0+6)
  if k & 0x40:  sel = (sel == 0) ? 7 : sel-1  # Up
  if k & 0x80:  sel = (sel == 7) ? 0 : sel+1  # Down
  if k & 0x10:  if sel==0: ev  = (ev  >  0) ? ev-1 : 154      # Right = -1
                if sel==7: msg = (msg >  0) ? msg-1 : 224
  if k & 0x20:  if sel==0: ev  = (ev  <  154) ? ev+1 : 0      # Left  = +1
                if sel==7: msg = (msg <  224) ? msg+1 : 0
  if k & 0x01:  install(0x08021CDC)          # A = dispatch
```

`0x08021CDC` then does `jump table[sel]` (table base `0x08021D08`), each
handler starting a normal game scene:

| sel | Name | Handler | Effect (observed) |
|---:|---|---|---|
| 0 | EVENT | `0x08021D28` | runs event script `EVT_*[ev]`; default `EVT_ALL_OPENING00`; Right twice → `EVT_SUB_ENDSAVE`; A runs the opening scene |
| 1 | BOTS_SEL | `0x08021D40` | shop / board-spot test screen (`Magic` item, 1000 coins) |
| 2 | MENU | `0x08021D4C` | retail title screen |
| 3 | OPENING | `0x08021D58` | opening event scene (same scene as EVENT with `EVT_ALL_OPENING00`) |
| 4 | MINIGAME MENU | `0x08021D68` | `Multijoueur` multiplayer minigame selector (`Autos tamponneuses`) |
| 5 | ATTRACTION MENU | `0x08021D74` | `Attractions` selector (`Wild Garden / Le Jardin Sauvage`) |
| 6 | ENDING | `0x08021D80` | ending / staff-roll start |
| 7 | MESSAGE | `0x08021D8C` | message-text viewer; id 0000 displays `une Carte 3 cases` |

### 5.3 Why the menus are unreachable

Reference closure (every edge verified by a byte-granular 4-byte pointer scan
of the whole 8 MiB image plus a Thumb/ARM `BL`/`BLX` scan):

```
0x0800E34C  installed only by  0x0800E5D6  (inside 0x0800E5C0)
0x0800E5C0  called    only from 0x0800E57A (option 0 of 0x0800E54C)
0x0800E54C  installed only by  0x0800E534  (inside input 0x0800E464)
0x0800E464  installed only by  0x0800E452  (inside 0x0800E448)
0x0800E448  installed only by  0x0800E3FA  (inside 0x0800E34C)
0x08021DA8  installed only by  0x0800E598  (option 2 of 0x0800E54C)
```

That is a cycle with no incoming edge from the retail boot chain
(`main → 0x0800F0BC → 0x0800F0D4 → 0x0800ECA8 → …`), and no literal pointer to
`0x0800E34D`, `0x0800E54D`, `0x0800E5C1` or `0x08021DA9` occurs anywhere else in
the image. The debug component is therefore **dead code**: no controller input,
save bit or link message can set `0x020156F0` to it. It was still a build-time
entry point (inferred: a debug build of `main` would have started it), which is
why it is complete and functional when executed.

### 5.4 What is *not* present

No text-entry validator, no `strcmp`-style accepted-string table, no
button-sequence matcher. The published CodeBreaker codes write EWRAM
(`0x02015BE8`, `0x02015BC2`, `0x0201731C`, …); those writes are performed by
the cheat device, not by the game, and there is no in-game path that produces
the same state.

## 6. Tables

### 6.1 Debug string block `0x080BC8B8`–`0x080BC93C`

```
0x080BC8D8  "ｵﾚｻﾏ DEBUG MODE\0"
0x080BC8E8  "EVENT\0"
0x080BC8F0  "BOTS_SEL\0"
0x080BC8FC  "MENU\0"
0x080BC904  "OPENING\0"
0x080BC90C  "MINIGAME MENU\0"
0x080BC91C  "ATTRACTION MENU\0"
0x080BC92C  "ENDING\0"
0x080BC934  "MESSAGE\0"
0x080BC940  01 00 02 00 04 00 08 00 10 00 20 00 40 00 80 00
            00 01 00 02 00 04 00 08 00 10 00 20 00 40 00 80
```

### 6.2 Handler table `0x08021D08` (8 entries, used by `0x08021CF0`)

`0x08021D04` holds the table base pointer `0x08021D08`.

```
0x08021D08: 0x08021D28  0x08021D40  0x08021D4C  0x08021D58
0x08021D18: 0x08021D68  0x08021D74  0x08021D80  0x08021D8C
```

### 6.3 EVENT name table

`0x080E32C0` onward: 155 NUL-terminated `EVT_*` names used by the event VM and
by the debug EVENT parameter (index 0..154). Examples:

```
EVT_SUB_ENDSAVE_Y   EVT_SUB_SAVE      EVT_SUB_FLDCONTINUE
EVT_SUB_FLDSET_MGS  EVT_SUB_PLT_GET_CARD3   EVT_SUB_GET_HPORB
EVT_STM_SHOP1       EVT_STM_PORT1_Y   ...
```

### 6.4 Parent developer menu options

Displayed top-to-bottom; option index is `0x02017020`.

| idx | Label (observed) | Dispatch target | Observed screen |
|---:|---|---|---|
| 0 | `FURUKAWA` | `0x0800F818` | ending / staff roll |
| 1 | `KITAWAKI` | `0x0801342C` | `Wild Garden / Le Jardin Sauvage` stage intro |
| 2 | `SUGATA` | `0x08021DA8` | `ｵﾚｻﾏ DEBUG MODE` |
| 3 | `TAKEMOTO` | `0x080106B4` | board/results screen (`PARADISE COVE`, star 04, rank E) |

### 6.5 Language screen

`0x0800E748` input, index `0x02017088` 0..4; Up/Down wrap; A or Start confirms.
Entries: English, French, German, Italian, Spanish.

## 6b. Enumeration

### Space definition

| Surface | Size | Bounds | Evidence |
|---|---:|---|---|
| Password / cheat string entry | **0** | no entry UI, no alphabet, no table | strings + screen walk + code search |
| Button-code sequence | **0** | no mask table, no sequence state | mask-run scan + 84 key consumers |
| Developer menu | 4 | `0x02017020 ∈ 0..3` | dispatch `0x0800E54C` |
| Debug menu | 8 | `0x02004574 ∈ 0..7`, wrap at 0/7 | input `0x08021B30` |
| EVENT parameter | 155 | `0x02004576 ∈ 0..154` | 155 `EVT_*` strings, wrap at 0x9A |
| MESSAGE parameter | 225 | `0x02004578 ∈ 0..224` | wrap at `0xE0` |

The debug-menu space is `4 × 8 × 155 × 225 = 1,116,000` reachable debug states,
but none is reachable by a retail input path (§5.3), so no "novel code" can be
typed into the shipped game. The equivalent deliverable here is the complete
list of the developer entries and their effects — i.e. the content that no
published list describes (3rd party cheat indexes only notes that the string block exists at
`0xBC8DD` and asks for investigation).

### All debug entries driven (not in any published list)

| Entry | Observed result | Evidence |
|---|---|---|
| `EVENT` + `EVT_ALL_OPENING00` | runs the opening event scene (Daisy dialogue) | screenshot; task `0x080221A1` |
| `EVENT` + `EVT_SUB_ENDSAVE` | parameter changed by Right×2 | screenshot of menu |
| `BOTS_SEL` | shop/board-spot screen, `Magic`, 1000 coins | screenshot; task `0x080233C5` |
| `MENU` | retail title | task `0x08026AE9` |
| `OPENING` | opening event | task `0x080221A1` |
| `MINIGAME MENU` | `Multijoueur`, bumper-cars minigame, arrows | task `0x08028A21` |
| `ATTRACTION MENU` | `Attractions`, `Wild Garden` | task `0x08029BE5` |
| `ENDING` | ending/staff roll | task `0x0800F819` |
| `MESSAGE` id 0000 | `une Carte 3 cases` message box | task `0x0802BBDD` |
| Boot option 0 `FURUKAWA` | staff names `FURUKAWA/KITAWAKI/SUGATA/TAKEMOTO` | task `0x0800F819` |
| Boot option 1 `KITAWAKI` | `Wild Garden` stage intro | task `0x0801342D` |
| Boot option 3 `TAKEMOTO` | `PARADISE COVE`, star 04, rank E | task `0x080106B5` |

### Bounds proven by rejection

* Selection `0x02004574` is clamped by `cmp r0,#7; bhi → return` in
  `0x08021CF0`; index 8+ falls through without dispatch. Up at 0 wraps to 7,
  Down at 7 wraps to 0 (both observed).
* EVENT index is clamped by `cmp #0x9A` (154); underflow 0 → 154 and overflow
  154 → 0 (`0x08021BD4`, `0x08021C26`). 155 is not representable.
* MESSAGE index is clamped by `cmp #0xE0` (224) with 0↔224 wrap
  (`0x08021BEE`, `0x08021C6C`). 225 is not representable.
* The retail title has no second option: the title handler `0x08026AE8` tests
  only `0x10/0x20` (a 1..4 counter) and `0x01/0x02`; there is no Up/Down list
  and no Continue branch, independent of save data.

### Negative-space counts (bounded search)

* `strings -t x -n 4`: **57,038** ASCII strings ≥ 4 chars. Keyword hits:
  `password` 0, `passwd` 0, `pass` 0, `cheat` 0, `code` 0, `secret` 0,
  `unlock` 0, `hidden` 0, `bonus` 0, `gallery` 0, `sound` 0, `test` 0,
  `continue` 0; **1** hit for `debug` — the `DEBUG MODE` string above.
  In-game UI text is *not* ASCII (font-tile/Shift-JIS), so the screen walk is
  the primary evidence for the absence of an entry UI.
* Single-bit u16 runs (button-mask tables): **1** run of 5, at file `0x12EA`,
  inside code and not a table; **0** runs of ≥ 3 elsewhere, and 0 runs of the
  active-low form.
* Byte arrays of button indices 1..10 of length ≥ 6: **0**.
* Alphabet tables: only the debug charset `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZudlr`
  at `0xAD4B0`; **0** password alphabets.
* Key-struct consumers: **84** literal sites of `0x030005B0`. Multi-bit AND
  masks found in them: `0x3, 0x7, 0x9, 0xB, 0xC, 0x30, 0xC0, 0xF0, 0xFF` — all
  ordinary UI semantics (A/B skip, Start/Select confirm, Left+Right and
  Up+Down diagonals, D-pad block). None is a cheat sequence or a press-history
  matcher.
* Hard-coded accepted strings / `strcmp` against user text: none; no text buffer
  in EWRAM is compared outside its entry handler (no entry handler exists).

### Published codes

All public codes for this title are CodeBreaker-format RAM patches
(`82015BE8 0063`, `82015BC2 0BA0`, `8201731C 0006`, plus encrypted CB lines).
Verified in the ROM only in the sense that they are plain EWRAM writes: the
addresses are in the 256 KiB EWRAM window and have no ROM literal. They are
memory edits, not in-game cheats, and were **not executed**; the scope of this
engagement excludes them. No published in-game password or button code exists
to test — the game has no such surface.

## 7. Validation evidence

**Observed (mGBA screenshots / RAM reads / tasks)**
* Language screen 5 entries, index wrap at 4; `0x02017088` is the index.
* Title: single `New Game` option; A → player count → character select; the
  4-character ring wraps (Daisy → Donald).
* `Tour Selection` Days 1–4; `Island Selection` 5 islands; board and `Pause`.
* Debug menu rendered (`ｵﾚｻﾏ DEBUG MODE`) with 8 entries; selection and
  parameters move; all 8 entries launch their scenes (task addresses above).
* Parent menu rendered with 4 developer names; option 2 launches the debug
  menu; options 0/1/3 launch ending/attraction/results.
* RAM: `0x020156F0` = current task; `0x02015B58` = 1; `0x02004574/76/78` = 0
  at menu entry; key struct `0x030005B0+4` = 0x0010 while Right is held.

**Derived (instruction-level)**
* Handler table `0x08021D08`, dispatch `0x08021CF0`, parameter clamps.
* Reachability cycle §5.3 and the absence of any external pointer.
* No text-entry or button-sequence matcher (counts in §6b).

**Inferred**
* The four labels' order equals option index 0..3 (the list is drawn
  top-to-bottom and Down increments the index; option 2 was proven to be the
  debug menu).
* `BOTS_SEL` is a shop/board-spot test screen; the visible evidence is the
  `Magic` purchase panel with 1000 coins.
* Option 0/1/3 screens were observed at their first screen only; later flow of
  those test paths was not followed to completion. 3rd party cheat index lists Wild Garden
  as a selectable board, so option 1 is described as a stage/attraction intro.

## 8. Unknowns

* Whether the original debug build wired the developer menu directly into
  `main` (the retail image has no call site; a debug build's `main` is not in
  this ROM).
* Full downstream flow of the `FURUKAWA` ending test, the `KITAWAKI` stage
  test and the `TAKEMOTO` results test beyond their first screens.
* Exact semantics of the `MESSAGE` id space beyond id 0000 (range from code is
  0..224; not every id was entered).
* Meaning of the auxiliary byte `0x02017024` (cleared by setup; no reader
  found in the menu code).
* The 57 KiB of Shift-JIS/full-width text was not translated; it is story text,
  not a code surface.

## 9. Tooling

* `md5sum/sha1sum/sha256sum`, `xxd`, `strings -t x -n 4`, `grep -abo`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000
  -M force-thumb`.
* Python 3 + Capstone 5.0.7: pointer/xref scans, BL/BLX scan, key-mask scan.
* mGBA (SDL) under Xvfb `:334`, `xdotool`, `scrot`/`import`.
* Savestate tool: PNG `gbAs` chunk → `zlib.decompress` → patch EWRAM
  `0x020156F0` → `zlib.compress` → rebuild PNG chunks (used only to enter the
  dead menus; results labelled accordingly).
* No ROM, graphics, text or audio is redistributed here; addresses, hashes,
  algorithms and the debug-menu layout only.
