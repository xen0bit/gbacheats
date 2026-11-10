# Bratz: Rock Angelz (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Bratz: Rock Angelz/Bratz: Rock Angelz.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title (`0xA0`–`0xAB`) | `BRATZ ROCK A` |
| Game code (`0xAC`–`0xAF`) | `BRRE` (region nibble `E` = USA) |
| Maker code (`0xB0`–`0xB1`) | `78` (Altron) |
| Fixed byte `0xB2` | `0x96` |
| Main unit / device | `0x00` / `0x00` |
| Software version | `0x00` |
| Complement check (`0xBD`) | `0x84` — recomputed value is also `0x84`, so the header is intact |
| Header checksum (`0xBE`–`0xBF`) | `0x0000` (normal artifact of a rebuilt/zeroed header; the complement byte is the reliable signal) |
| Entry word | `0xEA00002E` = stock `b 0x080000C0`, not a cracktro branch |
| MD5 | `874aa5c4c6217febec6405a22d7bc9ef` |
| SHA-1 | `eb2b8ddbb5ca2449f80ddf2c7bec2bd0b4a75e47` |
| SHA-256 | `08f5dc54324dd7e9cc3fb50bfa1e39e2f6ff7a94ce4c907fc84f88d076df9c0e` |

Embedded-header scan: the full 156-byte Nintendo logo occurs exactly once, at
file offset `0x4` (header base `0x0`). There is no second GBA image, no appended
trainer, no cracktro, and no boot shell. The first 4 KiB decode as a normal ARM
crt0 (`0x080000C0` → main `0x08000338`). The image is the retail
`BRATZ ROCK A` / `BRRE` Rev.00 build.

Save type: 512-byte SRAM-sized save image (`rom.sav` is exactly 512 bytes;
mGBA created/loaded it as the cartridge save). The save is written only through
the pause-menu `SAVE → YES` flow.

## 2. Executive summary

**This build has no in-game password, cheat-code, button-code, or debug-menu
system.** The delivered result is a bounded negative, not a confirmation of the
published strings.

* The published strings `SIZZLN`, `FLAUNT`, `SPRKLE`, `SKATIN` and `JEWELZ` are
  **absent from the ROM** in ASCII, lowercase, UTF-16LE/BE and 5-bit-per-letter
  forms. In this ROM `SKATIN` occurs only as the ordinary English word
  `Skatin` inside dialogue (`0x18A615`); the others do not occur at all.
* Those codes belong to the **console/PC Bratz line** (Forever Diamondz and the
  Rock Angelz "cheat computer"), not to the GBA SKU. GameFAQs' GBA cheats page
  (archived 2025-11-13) lists only PS2/PC/GC cheat-computer passwords;
  VGChartz lists **0** cheats for the GBA release. The IGN walkthrough itself
  records that the end-credit code `SIZZLN` "will not work" in the cheat
  computer.
* The GBA game is by **Altron** (maker `78`) and is a different engine from the
  Barking Lizards Bratz GBA titles. It has no text-entry surface at all: every
  in-game string is drawn from ROM ASCII, and no `PASSWORD`/`CODE`/`CHEAT`/
  `ENTER`/`DEBUG` UI string exists (0 hits across 3,316 printable strings).
  There is therefore nowhere to type a code.
* All menu surfaces were walked and are listed in §3/§6: title, main menu,
  story sub-menu, Mini Game Mode (7 slots, all unselectable at new game),
  Gallery Mode (2 sub-galleries; Item Gallery 10×4 grid with an `1/8`
  indicator; Fashion Gallery with four categories), and the 4-item pause menu
  with its MEMO, Item List, Fashion Change and SAVE screens.
* The two `????????` pause rows are **not a cheat**: they are the normal
  progress-gated **Fashion Change** and **Item List** features. A savestate-only
  analysis patch of gate byte `0x03001D49` (bit 1 = `0x02`, bit 2 = `0x04`)
  opened them and showed their real screens; the labels remain `????????`
  because the pause label asset selection uses a separate condition.
* Button-space checks found no sequence validator: 506 `u16` runs of button
  masks (length ≥4), only 6 of which are pointer-referenced, and all six are
  data tables (SIO sizes, sprite dimensions, font metrics). Ten candidate
  sequences (including the original Bratz trigger `L, B, Up, A, Down` and the
  Konami code) were pressed at the main menu: every one was consumed as ordinary
  navigation or ignored; none opened a hidden screen.

No GameShark/CodeBreaker/AR codes are used or reported.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL, `Xvfb :210 -screen 0 1024x768x24`, `openbox`,
`SDL_AUDIODRIVER=dummy`, scale `-3`. Screenshots were taken with
`import -window <mGBA window>` (720×480 client area).

Default mGBA SDL keymap used throughout:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Reproduction path:

1. Boot → THQ logo → title screen (`PRESS START`). Press Start.
2. Main menu: **STORY MODE / MINI GAME MODE / GALLERY MODE**.
   * `STORY MODE` → **NEW GAME** (only entry). Selecting it plays the intro;
     press Start to skip to the field.
   * `MINI GAME MODE` → a 7-row list of `????????` slots. At new-game progress
     every row is unselectable; pressing A on any row does nothing and the list
     does not transition.
   * `GALLERY MODE` → a 2-entry carousel (`ITEM GALLERY` ↔ `FASHION GALLERY`)
     selected with Left/Right.
     - `ITEM GALLERY`: 10×4 grid of 40 slots, with an `1/8` counter. Four
       starter items are present (`Blue Tank` for Cloe, `Pink Tank` for Jade,
       `Orange Tank` for Yasmin, plus one more); all others show `?`.
       Left/Right/Up/Down move only the selection.
     - `FASHION GALLERY`: character viewer with HAIR / TOPS / SKIRTS-BOTTOMS /
       ACCESSORIES rows and L/R character change.
3. In the field, Start opens the **PAUSE MENU**:
   `CHECK LIST` / `????????` / `????????` / `SAVE`.
   * `CHECK LIST` → MEMO notebook with three objective lines.
   * first `????????` → **Fashion Change** (when its gate bit is set).
   * second `????????` → **Item List** (when its gate bit is set).
   * `SAVE` → `YES / NO` tag prompt.
4. The field itself (Bratz City / Bratz office) was explored; the office has a
   door, couch, stools and a window. No computer, keyboard, code pad, or text
   field exists anywhere in the room.

Button sequences pressed at the main menu (each from a reloaded main-menu
savestate, 120–150 ms holds):

| Test | Result |
|---|---|
| `L, B, Up, A, Down` (original Bratz trigger) | ordinary navigation → Gallery Mode; no hidden screen |
| Konami (`Up Up Down Down Left Right Left Right B A`) | navigation → Story `NEW GAME`; no hidden screen |
| `B, A, B, A` | navigation → Story `NEW GAME`; no hidden screen |
| `L, R, L, R` | no visible/RAM effect |
| `Select ×3` | no effect |
| `L + R + Select` | no effect |
| `A + B + Start + Select` | no effect (no soft-reset screen) |
| `Up, Down, Up, Down` | no effect |
| `Up, Down, Left, Right` | no effect |
| hold `L` + `Start` | no effect |

The same non-Start sequences (original Bratz, Konami, `L R L R`, `Select ×3`)
were also pressed on the **title screen** before pressing Start. The title stayed
on `PRESS START` (screenshot `t2.png`) and Start then produced the normal main
menu (`t3.png`); no hidden screen appeared.

Published-code test: see §6. There is no entry surface, so the test is the
literal/encoding search plus the absence of any input widget.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x080000C0` | ARM crt0; call to main `0x08000338` via literal `0x08000339` |
| `0x08000AFC` | Thumb **key reader** (the single site that reads `KEYINPUT`) |
| `0x04000130` | `KEYINPUT` (active-low) |
| `0x03001E98` | pressed = `held & ~prev` (u16) |
| `0x03001E9A` | held = `~KEYINPUT & 0xFFFF` (idle `0xFC00`) |
| `0x03001E9C` | released = `~held & prev` (u16) |
| `0x03001E9E` | previous processed held value (u16) |
| `0x03000C04` | previous raw held value (u16) |
| `0x08006F88` | generic list/cursor widget (holds repeat timer, wraps index) |
| `0x081A48B4` | class descriptor for the main menu (id 3) |
| `0x08029354` | main-menu class init |
| `0x08029474` | main-menu class update (writes cursor index) |
| `0x08029924` | main-menu class draw |
| `0x030039A0` | main-menu entity base (size `0x35C`); list struct `0x03003C90` |
| `0x03003C92` | main-menu cursor index (0=STORY, 1=MINI, 2=GALLERY) |
| `0x081A7A04` | class descriptor for the field/pause manager (id 8) |
| `0x0802AED0` | field class init |
| `0x0802AFEC` | field class update |
| `0x0802BB20` | pause-menu sub-state dispatcher (states 0–4) |
| `0x0802BB78` | pause state 0: 4-item list + action dispatch |
| `0x0802BC54` | pause state 1: close/cancel |
| `0x0802BC80` | pause state 2: Item List / list widget |
| `0x0802BEA0` | pause state 3: (fashion/character flow) |
| `0x0802C0C8` | pause state 4: (save/other flow) |
| `0x03006DA0` | pause entity base (size `0x868`); cursor `0x03006DC2` |
| `0x03001D10` | progress/save global (111 ROM references) |
| `0x03001D49` | `progress+0x39`, pause-feature gate byte (bit0 Check List, bit1 Fashion Change, bit2 Item List) |
| `0x08136020` | ROM class-descriptor table, 24 entries (ids `0x03`–`0x1A`) |
| `0x03000C4C` | RAM class registry (24 × 4-byte descriptor pointers) |
| `0x1427D0` | font 0 character/width table (`A–Z a–z 0–9 !?.,:$/-'`) |
| `0x142861`, `0x142937`, `0x1429E5`, `0x142AA5`, `0x142B64`, `0x142C12` | six further font style tables |
| `0x1A575C` | text ID `" Item List ?"` |
| `0x1A5769` | text ID `" Fashion Change ?"` |
| `0x1A577B` | text ID `" Operations ?"` (purpose unresolved; see §8) |
| `0x1A56D6` | `"New items added"` text IDs used by the check list |

Class table (24 descriptors, `{id, init, update, draw, 0, 0, dtor, size}`),
extracted from `0x08136020`; the table ends at `0x08136080`:

| id | descriptor | id | descriptor |
|---|---|---|---|
| 3 | `0x081A48B4` | 0x0F | `0x081ACC10` |
| 4 | `0x081A8E04` | 0x10 | `0x0818D288` |
| 5 | `0x081A93CC` | 0x11 | `0x081A7E50` |
| 6 | `0x081A94B0` | 0x12 | `0x081A7E90` |
| 7 | `0x081A9694` | 0x13 | `0x081A8758` |
| 8 | `0x081A7A04` | 0x14 | `0x081A8798` |
| 9 | `0x081AAA9C` | 0x15 | `0x081A8DB0` |
| 0x0A | `0x081A7A24` | 0x16 | `0x081ACC30` |
| 0x0B | `0x081AC860` | 0x17 | `0x081ACC90` |
| 0x0C | `0x081AC888` | 0x18 | `0x081ACCB0` |
| 0x0D | `0x081ACA08` | 0x19 | `0x0818D248` |
| 0x0E | `0x081ACAF4` | 0x1A | `0x0818D268` |

## 5. Algorithm

### 5.1 Input decoding (`0x08000AFC`)

```c
u16 raw   = *(volatile u16*)0x04000130;   // active-low
u16 held  = (~raw) & 0xFFFF;              // idle = 0xFC00
u16 press = held & (~prev);
u16 rel   = (~held) & prev;
*(u16*)0x03001E98 = press;
*(u16*)0x03001E9A = held;
*(u16*)0x03001E9C = rel;
*(u16*)0x03001E9E = old_held;
*(u16*)0x03000C04 = held;                 // previous raw held
prev = held;
```

Button masks (as used by the game): A=1, B=2, Select=4, Start=8, Right=0x10,
Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200.

### 5.2 Generic list/cursor widget (`0x08006F88`)

Arguments include the list struct (`+0` repeat timer, `+2` index), min/max
index, and a flag for wrap. It handles held-direction repeat and returns
`0 none`, `1 confirm`, `2 cancel`. The main menu and pause menu both use it.

### 5.3 Main menu (`class 3`)

`0x08029474` calls the list widget with the list struct at `entity+0x2F0`
(`0x03003C90`, index `0x03003C92`) and max index 2. Confirm dispatches to
STORY (`NEW GAME`), MINI GAME MODE, or GALLERY MODE. No other branch exists:
the only key compares in the function are against A and B.

### 5.4 Pause menu (`class 8`, sub-state `entity+0x0F`)

`0x0802BB20` dispatches on a 5-entry table:

```
state 0 -> 0x0802BB78  4-item list (max index 3) and action dispatch
state 1 -> 0x0802BC54  close/cancel
state 2 -> 0x0802BC80  list widget for item/fashion list
state 3 -> 0x0802BEA0
state 4 -> 0x0802C0C8
```

On confirm in state 0 (`0x0802BBDA`), the handler tests
`(*(u8*)(*(u32*)(entity+0x82C) + 0x39) >> index) & 1`:

* index 0 → CHECK LIST (always enabled in this save);
* index 1 → Fashion Change, gated by bit 1 (`0x02`);
* index 2 → Item List, gated by bit 2 (`0x04`);
* index 3 → SAVE (always enabled).

If the bit is clear, the handler calls the UI error routine
(`0x08002278` with `r0=4`) and stays in the pause menu; if set, it switches to
the corresponding screen. Nothing about this path reads a typed string or a
button sequence.

### 5.5 No code validator

There is no code validator to reimplement. The engine has:

* no text-entry widget (no buffer, cursor, alphabet picker, or accept key),
* no table of code literals (see §6),
* no user-controlled text buffer to compare (there is no text-entry widget at
  all),
* no multi-step key-sequence counter in the menu classes.

## 6. Tables

### 6.1 Main menu

| Index | Label | Action |
|---|---|---|
| 0 | STORY MODE | `NEW GAME` sub-menu → intro → field |
| 1 | MINI GAME MODE | 7-slot list |
| 2 | GALLERY MODE | Item Gallery / Fashion Gallery |

### 6.2 Pause menu

| Index | Observed label | Gate (progress `0x03001D49`) | Screen |
|---|---|---|---|
| 0 | CHECK LIST | bit0 `0x01` | MEMO notebook |
| 1 | `????????` (real: Fashion Change) | bit1 `0x02` | FASHION GALLERY-style dress-up |
| 2 | `????????` (real: Item List) | bit2 `0x04` | ITEM GALLERY/ITEM LIST grid |
| 3 | SAVE | always | `YES / NO` save prompt |

### 6.3 Unlockable structures (gameplay, not cheats)

| Surface | Size observed | Gate |
|---|---|---|
| Mini Game Mode list | 7 slots | story progress; all locked at new game |
| Item Gallery / Item List | 10×4 grid = 40 slots per page, `1/8` indicator | items found in story/shops |
| Fashion Gallery | HAIR / TOPS / SKIRTS-BOTTOMS / ACCESSORIES | clothes obtained in story |
| Check List | MEMO with 3 objective lines | story progress |

### 6.4 Published codes and their status in this ROM

Search space: 8 MiB, ASCII, lowercase, UTF-16LE, UTF-16BE, 5-bit packing with
`A=0` and `A=1` offsets.

| Code | Published for | Present in this ROM? |
|---|---|---|
| `SIZZLN` | Forever Diamondz console / wrongly attributed to Rock Angelz | **No** |
| `FLAUNT` | Forever Diamondz console | **No** |
| `SPRKLE` | Forever Diamondz console | **No** |
| `SKATIN` | Forever Diamondz console | Only the English word `Skatin` at `0x18A615` (dialogue) |
| `JEWELZ` | Forever Diamondz console | **No** |
| `YASMIN` | Rock Angelz console/PC cheat computer | **No** |
| `PHOEBE` | Rock Angelz console/PC cheat computer | **No** |
| `DANCIN` | Rock Angelz console/PC cheat computer | Only lowercase `dancin` in dialogue (`0x1ABBD7`) |
| `WAYFAB` | Rock Angelz console/PC cheat computer | **No** |
| `HOTTIE` | Rock Angelz console/PC cheat computer | **No** |
| `BLAZIN` | Rock Angelz console/PC cheat computer | **No** |
| `ANGELZ` | Rock Angelz console/PC cheat computer | **No** |
| `STYLIN` | Rock Angelz console/PC cheat computer | Only lowercase `stylin` in dialogue (`0x186F87`) |
| `FASHION` | Rock Angelz (PC list) | only the English word |
| `SPARKLE` | Rock Angelz (PC list, Chloe) | **No** |
| `STRUT` | Rock Angelz (PC list) | **No** |
| `FLAIR` | Rock Angelz (PC list) | **No** |
| `MODEL` | Rock Angelz (PC list, Sasha) | only the English word |
| `PRETTY` | Rock Angelz (PC list) | only the English word |
| `SCORCHIN` | Rock Angelz (PC list) | only the English word |
| `FUNKY` | Rock Angelz (PC list) | only the English word |
| `COOL` | Rock Angelz (PC list) | only the English word |
| `CRAZY` | Rock Angelz (PC list) | only the English word |
| `SASSY` | Rock Angelz (PC list) | only the English word |
| `KOOLKT` | Rock Angelz console/PC | **No** |
| `MODELS` | Rock Angelz console/PC | only the English word |
| `CAMPFR` | Rock Angelz console/PC | **No** |
| `RUNWAY` | Rock Angelz console/PC | **No** |
| `FIERCE` | Rock Angelz console/PC | **No** |
| `MEYGEN` | Rock Angelz console/PC | **No** |
| `ROCKIN` | Rock Angelz console/PC | only lowercase `rockin` in dialogue |
| `PRTPRN` | Rock Angelz console/PC | **No** |
| `BNYBOO` | Rock Angelz console/PC | **No** |
| `FIANNA` | Rock Angelz console/PC | **No** |
| `FUNKALISH` | Rock Angelz (PC list) | **No** |
| `SLAMMIN` | Rock Angelz (PC list) | only the English word |
| `HOT` | Rock Angelz (PC list) | only the English word |

No code table exists: a scan of all 3,316 printable NUL-terminated strings
found 39 all-caps 5–10-letter tokens, and every one is a slice of compressed
sprite/audio data (`KFPFXC`, `WIWHPD`, `DDDTUUUB`, …), not a record table. There
is no run of equal-length code strings and no pointer table to one.

## 6b. Enumeration

**Space definition.** The representable code space is **empty**. The build has:

* **No alphabet**: there is no code entry screen, so no symbol set is offered.
* **No length**: no input widget exists, so no fixed/variable length applies.
* **No checksum/field layout**: there is no validator to encode.
* **No table**: no literal code record exists (§6.4).
* **No generator**: no encoder/decoder pair exists.

**Validator model.** Not applicable. The only "validation" in the game is the
boolean progress gate `(progress[0x39] >> index) & 1` for pause-menu rows, and
the ordinary cursor bounds checks of the list widget `0x08006F88`.

**Novel code.** None can be generated because no accepted set exists. The
§0.2 deliverable is replaced by the proof that the space is empty:

1. **Text space searched (counted).** 3,316 printable NUL-terminated strings
   ≥4 chars. Keyword hit counts: `password` 0, `passwd` 0, `cheat` 0, `code` 0,
   `debug` 0, `unlock` 0, `hidden` 0, `bonus` 0, `option` 0, `config` 0,
   `setting` 0, `gallery` 0, `warp` 0, `teleport` 0, `sound test` 0,
   `level select` 0, `stage select` 0. `secret` 1 (the adjective "secretive" in
   dialogue), `pass` 3 (all inside "passion"/"backstage passes"), `sound` 3
   (all dialogue/credits), `music` 2 (dialogue), `god` 1 ("goddesses").
   All other hits are ordinary English prose. There is no UI prompt string for
   entering anything.
2. **Button space searched (counted).** 506 runs of `u16` button masks of
   length ≥4; 6 of those are referenced by a ROM pointer:
   * `0x4EA28` — tail of the `MultiSioSync010214` SIO size table (false
     positive from unaligned `0x0020/0x0040` values);
   * `0x4EEAC` — 17 × `0x0100` fill/size table;
   * `0x139A0E` — sprite-record dimensions `0x20, 4, 8, 4, 2`;
   * `0x1A8C46`, `0x1A8CC6`, `0x1AEF68` — font/metric data in the `0x1A8xxx`
     UI bank.

   All six sit inside data tables, not in a key-check code path; none is a
   sequence of distinct directional/L/R presses. A second scan of 4,032 mask
   runs of length ≥6 (at every byte alignment) and 51 pointer-referenced byte
   runs produced only font-metric and fill tables. A scan of 172 code sites that
   load the key struct literal found only ordinary single-press UI handlers: the
   only functions with ≥3 button compares are A/B/Start/Select menu and dialogue
   handlers, never a directional sequence counter.
3. **Published codes tested.** All 37 published words in §6.4 were searched in
   six encodings; only ordinary English-word collisions were found. The five
   codes named in the brief (`SIZZLN`, `FLAUNT`, `SPRKLE`, `SKATIN`, `JEWELZ`)
   are absent (except the dialogue word `Skatin`). There is no entry surface on
   which to type them; the field office contains no computer.
4. **Screens walked.** Title, main menu, STORY → NEW GAME, Mini Game Mode
   (7 rows, bottom reached), Gallery Mode carousel, Item Gallery (page/selection
   cursors moved), Fashion Gallery (all four category rows, L/R character
   change), pause menu (all four rows), MEMO/Check List, SAVE prompt, field
   city/office. No screen contains a code field, a keypad, a debug list, or a
   button prompt beyond the normal `Select / A OK / B Back` footer.
5. **Bounds proven by rejection.** Every attempt to reach a hidden surface was
   rejected:
   * all ten button sequences in §3 leave the game on a normal menu (or do
     nothing);
   * selecting any of the 7 locked mini-game rows does nothing;
   * selecting the two `????????` pause rows with the progress gate clear calls
     the UI error routine and does not transition;
   * no published literal can be typed because no text field exists.

**Conclusion of enumeration.** Accepted set = ∅; accepted literals = 0;
representable code values = 0. The negative is a statement about this exact
8 MiB image, its 3,316-string text space, its 24-class entity inventory and its
7-slot / 40-slot / 2-gallery / 4-row menu surfaces.

## 7. Validation evidence

### Observed (emulator/screenshots, on disk under `/tmp/opencode/rockangelz/`)

* `s03.png` — title screen.
* `s04.png`, `mm.png`, `mm2.png` — main menu with the three modes.
* `stmenu.png` — STORY MODE → `NEW GAME` (only entry).
* `miniA.png`, `miniB.png` — Mini Game Mode, 7 `????????` rows, cursor at both
  ends, all unselectable.
* `gal.png` — Gallery Mode carousel (`ITEM GALLERY` ↔ `FASHION GALLERY`).
* `itemA.png`, `item_page2.png`, `item_R.png` — Item Gallery, 10×4 grid,
  `1/8` indicator, starter items readable.
* `fashg.png` — Fashion Gallery with four categories and L/R character change.
* `pz0.png`, `pz.png` — pause menu, four rows, two `????????`.
* `chk1.png` — Check List / MEMO.
* `save1.png` — SAVE → `YES / NO`.
* `q2.png`, `off1.png` — field city and Bratz office.
* `gate03.png` — analysis-only savestate patch `0x03001D49=0x03`; selecting
  row 1 opens **FASHION CHANGE**.
* `gate07.png` — analysis-only savestate patch `0x03001D49=0x07`; selecting
  row 2 opens **ITEM LIST**.
* `seq_*.png` — main-menu sequence tests; all end on ordinary menus.
* `t2.png` — title screen after four non-Start sequences (still `PRESS START`);
  `t3.png` — Start afterwards opens the normal main menu.

### Derived (instruction sequences)

* Key reader `0x08000AFC`: exact `~KEYINPUT` + edge-detection formula in §5.1.
* Main-menu cursor `0x03003C92` written by `0x08029474` via list widget
  `0x08006F88`; class 3 descriptor `0x081A48B4`.
* Pause cursor `0x03006DC2` (`entity 0x03006DA0 + 0x22`) written by the same
  widget; pause dispatcher `0x0802BB20`, gate expression at `0x0802BBF0`.
* Class table at `0x08136020` yields exactly 24 descriptors (ids 3–0x1A).
* No code validator: no code path compares a user buffer with ROM literals.

### Inferred

* The two `????????` labels are drawn from a fixed `?` tile asset while the
  feature gate is clear (the label asset selection is separate from the gate
  byte).
* `Operations ?` is a text ID for a feature not present in the 4-row pause menu
  in this build; its consumer was not located.
* The `1/8` indicator in the Item Gallery is most likely an 8-page indicator,
  not an item count; page switching was not observed with the buttons tested.

## 8. Unknowns

* **Late-game screens.** The report proves the absence of a code surface in the
  retail image's text space and in every menu reachable at new-game progress.
  It does not play the whole story to unlock every shop interior; however, a
  password/cheat screen would still need ROM strings, a text-entry widget and a
  validator — none of which exist anywhere in the image.
* **`Operations ?`** (`0x1A577B`) has no observed screen in the 4-row pause menu.
  It may be a cut or alternate-menu label.
* **Pause label asset gating** for the two `????????` rows is not the same
  condition as the feature gate; the exact asset-selection test was not
  isolated.
* **Item Gallery pagination** (`1/8`) is unconfirmed; L/R did not change pages.

## 9. Tooling

* `xxd`, `strings -t x`, `file`, `md5sum`/`sha1sum`/`sha256sum`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python 3 with Capstone 5.0.7: literal-pool scan, BL-target scan, key-mask run
  scanner, encoding search.
* mGBA 0.10.5 SDL under Xvfb `:210`; `xdotool`, `scrot`, ImageMagick
  `import`/`convert`.
* mGBA CLI debugger (`-d`) used for live key-state reads and
  watchpoints on `0x03003C92` / `0x03006DC2`; a local savestate parser
  (`ss.py`) maps IWRAM to state offset `0x19000` and EWRAM to `0x21000` for
  offline RAM diffing.
* Analysis-only savestate patch script for the pause gate byte; no memory-edit
  code is published as a cheat.

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed with this
report. Only hashes, addresses, algorithms, menu inventories and original
analysis text are included. Screenshots are kept on disk as analysis evidence,
not embedded.
