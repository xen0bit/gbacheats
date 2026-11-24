# Columns Crown (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Columns Crown/Columns Crown.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `COLUMNSCROWN` |
| Game code / maker | `ACGE` / `6W` (THQ) |
| Version / complement | Rev.00, complement `0x0A`, header checksum `0x0000` (rebuilt-header artifact only) |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| MD5 | `38f369f1ca0872790995943e8cb4a877` |
| SHA-1 | `f11c7a225524d418907e42666b33649b585fb6d4` |
| SHA-256 | `26bff2e97f21b5150c7180b527d506df1eef31c42053a8b0a07128fe242dd884` |

Header notes: the Nintendo logo appears at file `0x4`, `0xC4` and `0x7CD354`. The
duplicate at `0xC0` is a copy of the retail header whose branch continues to the
real crt0 at `0x08000180` (stack `0x03007FA0`, main `0x0800050D`). The third
header (title empty, code `AGBJ`) at `0x7CD350` is a multiboot/link stub, not a
second game. Complement check recomputes to `0x0A`; no trainer, no cracktro, no
appended payload, no modified entry word. Nothing was patched for this analysis.

## 2. Executive summary

**Columns Crown has no password system, no button cheat code, and no reachable
debug menu.** That is a bounded negative, not an absence of search:

* There is no text-entry surface other than the player-name field. The game's
  menus are tile graphics; the only strings in the image are the ASCII story
  script and Shift-JIS player names.
* Every keyword that a password/cheat/debug surface would need is absent in
  ASCII, folded ASCII, UTF-16LE/BE and Shift-JIS (counts in §3/§6b).
* The pad is read in exactly one place (`0x08006E18`). All 75 code sites that
  consume the resulting held/pressed words were disassembled. None builds a
  press history or compares against a sequence.
* The ROM contains 380 runs of ≥5 consecutive single-button 16-bit masks
  (the shape of a button-code table). **Zero** of those run addresses is
  referenced by any 32-bit pointer in the image, i.e. no code can dispatch to
  them.
* The player name is written to the save block and passed only to the text
  print routine (`0x08021040`); nothing compares it. It is a label, not a
  validator.

What the ROM *does* hide is an **unlockable set larger than the manual admits**.
The manual and every published page describe 24 Magic Gems. The ROM contains
**25 gem descriptions** and a **25-entry description pointer table**, plus a
**26-record collection layout table**. Gem index 24 (the 25th) is
`Gives you a guaranteed win. / Requirement: 66` — the "25th Magic Gem" the
story text teases. Gem index 25 has a layout record but no description and no
slot inside the 25-byte per-character count page, so its record can never be
drawn: it is dead/cut data. This 25th gem is not in the manual's 24-gem list and
is not in any published cheat list (published GBA "codes" for this title are
CodeBreaker memory writes, which are out of scope and are not in-game cheats).

The complete state machine, save layout, gem table and the absence proof are
below, with exact addresses so a second analyst can reproduce every claim.

## 3. How to reproduce

Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy mgba -3 "Columns Crown.gba"` on
`DISPLAY=:260` (Xvfb + openbox). Default SDL keymap used: A=`x`, B=`z`,
L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.

Input timing matters and cost time if ignored:

* a 45–70 ms tap moves a menu cursor **one** step; a ≥400 ms hold repeats and
  can jump to the last item (`03003DB2` goes 0→5 on one 0.4 s press);
* some confirmations need A or Start held ~0.5–0.9 s (a 0.2 s press is eaten by
  the transition);
* savestates on F1–F10 are useful, but in this build plain `F1`/`F2` did not
  reload; restarting with `mgba -t <state>` does.

Boot-to-menu path used for the dynamic evidence:

1. Boot; logo state 0 → intro state 12 (`03003DB6`).
2. Hold A across the script: ~70 presses of ~0.9 s reach state 11 (the intro
   script pointer in the state header advances from the text table at
   `0x087CCA90` into the script at `0x087CCB78`).
3. At state 11 hold Start (`Return`) 0.5 s: sets the save-valid bit
   `03002A24.0` and enters state 1.
4. Hold Start 0.5 s again: state 1 → state 2, the front-end screen (name
   entry, then the Select Mode menu, both run by `0x0801A2C8`).
5. At state 2 the character grid accepts A (it appends Shift-JIS glyphs to
   `03002A2C`); once the name phase is done the same scene shows the 6-item
   Select Mode menu. `Down`/`Up` move its cursor `03003DB2` (wraps 5→0).
   A 0.9 s A press confirms; item 0 was observed entering state 4 (Survival).
6. Item 5 (Options) enters the options sub-dispatch on `03003DB3`:
   `0` = Trade Magic Gems (`0x080147A8`), `1` = Rankings (`0x08015BA8`),
   `2` = Erase Data (`0x08004CC4` + clears `03002A24`).

Published codes tested: no in-game code list exists for this SKU. 3rd party cheat index list only CodeBreaker/GameShark memory writes
(e.g. `33003DDF 0063`, `43002A40 0505 / 0000001B 0002`,
`83003E06 8080`). Those were treated as **address hints only**, not as codes;
each address was checked against the real state block (§4) and is a memory
edit, not a developer-intended input. No 3rd party cheat indexes in-game code
for Columns Crown GBA was found to test.

## 4. Address map

ROM addresses are `0x08000000 + file offset`.

### Code / engine

| Address | Meaning |
|---|---|
| `0x08000180` | real ARM crt0 (entry from the header copy at `0xC0`) |
| `0x0800050C` | main loop; scene dispatch table at `0x08000594` |
| `0x08000594` | 15 × u32 Thumb handler pointers (scene 0..14) |
| `0x080006C0` | 6 × u32 Select Mode dispatch (index → scene) |
| `0x0800072C` | Options sub-dispatch on `03003DB3` |
| `0x08006E18` | the only KEYINPUT reader |
| `0x08004CC4` | save-block init / Erase Data |
| `0x080147A8` | Trade Magic Gems screen (reads gem counts + layout) |
| `0x08015BA8` | Rankings screen |
| `0x0801A2C8` | name-entry / character-grid UI |
| `0x0801CCDC` | opening/logo animation |
| `0x08021040` | text print function (only consumer of the name buffers) |
| `0x08021348` | gem collection layout table, 26 × 8 bytes |
| `0x08026E40` | name-entry Shift-JIS character rows (5 chars + `00 00` pad) |
| `0x08024364` | `"COLUMNS-SAVEDATA"` (only first 4 bytes `COLU` are copied to RAM) |

### Scene dispatch (scene byte `0x03003DB6`, 0..14; >14 spins at `0x08000572`)

| Scene | Handler | Observed function |
|---:|---|---|
| 0 | `0x08000624` | logo/boot animation → sets 12 |
| 1 | `0x08000638` | opening animation (`0x0801CCDC`) |
| 2 | `0x08000690` | front-end: name entry → Select Mode (`0x0801A2C8`) |
| 3 | `0x08000572` | idle/wait (no screen) |
| 4 | `0x08000784` | mode 0 (Survival) |
| 5 | `0x08000898` | mode 4 (Flash Columns) |
| 6 | `0x08000572` | idle/wait |
| 7 | `0x0800092C` | mode 1 (VS-CPU) |
| 8 | `0x08000A18` | mode 2 (One-Pak VS) |
| 9 | `0x0800080C` | mode 3 (Two-Pak VS) |
| 10 | `0x08000572` | idle/wait |
| 11 | `0x080005FC` | commit save-valid bit → scene 1 |
| 12 | `0x080005D0` | intro script (`0x0800F7D4`), then 11 or 1 |
| 13 | `0x08000664` | pre-title branch |
| 14 | `0x08000650` | pre-title → scene 1 |

Mode order (manual and table agree): 0 Survival, 1 VS-CPU, 2 One-Pak VS,
3 Two-Pak VS, 4 Flash Columns, 5 Options. There is no Endless and no Time
Attack screen in this SKU; the 15-entry table has no level-select or debug
slot.

### RAM (IWRAM)

| Address | Size | Meaning |
|---|---|---|
| `0x03002C1C` | u16 | held keys, active-high (`~KEYINPUT & 0x3FF`) |
| `0x03002C1E` | u16 | newly pressed keys (edge) |
| `0x03002A20` | 0x1FC | save block A (profile) |
| `0x03002A20` | 4 | `"COLU"` signature |
| `0x03002A24` | u32 | save flags; bit0 = save valid/initialised |
| `0x03002A28` | 4 | flags/pad |
| `0x03002A2C` | 12 | player-1 name, Shift-JIS (max 6 chars, NUL padded) |
| `0x03002A38` | 12 | player-2 name |
| `0x03002A44` | 25×2 | Magic Gem counts, page 0 |
| `0x03002A5D` | 25 | Magic Gem counts, page 1 (other character) |
| `0x03002B10` | — | report-card grade thresholds (u8 desc) |
| `0x03002C16` | 4 | second `"COLU"` signature (footer of block A) |
| `0x03002C30` | 0x2A8 | game session block (jewels, meters, score) |
| `0x03002C52` | u16 | VS jewel/score counter (CodeBreaker `83002C52`) |
| `0x03003DB0` | 0x84 | scene struct |
| `0x03003DB2` | u8 | Select Mode cursor 0..5 |
| `0x03003DB3` | u8 | Options sub-cursor 0..2 |
| `0x03003DB6` | u8 | scene id 0..14 |
| `0x03003DC8` | u16 | mode/round index used by scene 4 |
| `0x03002EB0` | u16 | gem page index (character) used by Trade screen |

Save medium: EEPROM, mGBA creates a 512-byte `.sav` (4 Kbit). The persisted
image stores 32-bit words byte-reversed; reversing each 4-byte group yields
`"COLU"`, the Shift-JIS names and the gem counts, i.e. the same block A.

## 5. Algorithm

### 5.1 Input path (no code matcher)

```
every frame:
  r2 = 0x3FF ^ KEYINPUT          ; held, active high
  pressed = r2 & ~held           ; edge
  held = r2
```

`0x03002C1C`/`0x03002C1E` are then read at 75 code sites. Every site is a
single-key test (one mask, one branch); the only multi-bit masks are direction
clusters used for cursor repeat. No site stores the key word into a buffer, so
there is no press-history array to compare against a sequence. This is the
structural reason a button code cannot exist in this engine.

### 5.2 Scene machine

```
if scene > 14: spin
else: pc = table[scene]        ; 0x08000594
```

Scene 2 runs the front-end UI (`0x0801A2C8`): the Shift-JIS character grid
(name entry) followed by the 6-item Select Mode menu. On return it dispatches
the cursor byte `03003DB2`:

```
0 -> scene 4   1 -> scene 7   2 -> scene 8
3 -> scene 9   4 -> scene 5   5 -> options(03003DB3)
```

### 5.3 Magic Gem model

```
descriptions:  ptr[i] = u32 at 0x087CC39C - 4*i   (i = 0..24, table runs backwards)
               strings at 0x08022438..0x08022910
counts:        count(page, i) = u8[0x03002A44 + i + 25*page]   (i = 0..24)
layout:        record r (r = 0..25) at 0x08021348 + 8*r
               record = {u8 a, u8 b, u8 xy, u8 gem_id, u8 ...}
               collection renderer iterates r = 0..24 only
```

The Trade/collection screen copies every non-zero `count(page,i)` into a list
and then draws the item using the layout record whose `gem_id == i`. Because
the renderer stops at 24, `gem_id = 25` (record 25) can never be drawn, and
index 25 of the count page is outside the 25-byte page (it is the first byte of
the next page).

## 6. Tables

### 6.1 Magic Gem descriptions (25 entries, table at `0x087CC33C` descending)

`idx` is the table index (0-based); `file` is the string offset; `req` is the
in-game requirement number printed with the description.

| idx | file | description | req |
|---:|---|---|---:|
| 0 | `0x022438` | Triggers a random gem power. | 24 |
| 1 | `0x022468` | Gives your rival 4-jewel drops. | 24 |
| 2 | `0x022498` | Stops your rival's field. | 39 |
| 3 | `0x0224C4` | Gives you only yellow jewels. | 26 |
| 4 | `0x0224F4` | Doubles the next Magic Gem drop. | 48 |
| 5 | `0x022528` | Creates a wall in the rival's field. | 37 |
| 6 | `0x022560` | Steals bar energy from your rival. | 33 |
| 7 | `0x022594` | Bumps your rival's field up 2 rows. | 35 |
| 8 | `0x0225C8` | Disables your rival's controls. | 36 |
| 9 | `0x0225F8` | Speeds up your rival's drops. | 12 |
| 10 | `0x022628` | Turns your rival upside down. | 18 |
| 11 | `0x022658` | Shakes up your rival's field. | 12 |
| 12 | `0x022688` | Takes away 3 rows from your field. | 41 |
| 13 | `0x0226BC` | Completely clears your field. | 48 |
| 14 | `0x0226EC` | Drops black rocks on your rival. | 32 |
| 15 | `0x022720` | Erases a column of rival's jewels. | 15 |
| 16 | `0x022754` | Hides your rival's jewel drops. | 19 |
| 17 | `0x022784` | Adds 2 rows to you & 4 to your rival. | 48 |
| 18 | `0x0227BC` | Turns your rival's jewels gray. | 27 |
| 19 | `0x0227EC` | Stops your rival from rotating. | 18 |
| 20 | `0x02281C` | Switches fields with your rival. | 42 |
| 21 | `0x022850` | Clears many jewels from your field. | 36 |
| 22 | `0x022884` | Copies the rival's Magic Gem power. | 21 |
| 23 | `0x0228B8` | Creates a one-time defensive shield. | 39 |
| **24** | **`0x0228F0`** | **Gives you a guaranteed win.** | **66** |

### 6.2 Collection layout table (`0x08021348`, 26 records)

| rec | bytes | gem_id | rec | bytes | gem_id |
|---:|---|---:|---:|---|---:|
| 0 | `00 06 3C 00` | 0 | 13 | `00 00 24 10` | 16 |
| 1 | `04 05 27 01` | 1 | 14 | `00 04 0C 0D` | 13 |
| 2 | `00 02 15 02` | 2 | 15 | `00 04 12 0E` | 14 |
| 3 | `04 05 24 03` | 3 | 16 | `00 01 0C 0F` | 15 |
| 4 | `03 04 2A 04` | 4 | 17 | `01 05 29 0C` | 12 |
| 5 | `00 01 12 05` | 5 | 18 | `00 01 23 11` | 17 |
| 6 | `00 03 1B 06` | 6 | 19 | `01 04 21 12` | 18 |
| 7 | `00 03 13 08` | 8 | 20 | `00 01 25 13` | 19 |
| 8 | `03 00 30 07` | 7 | 21 | `04 00 30 14` | 20 |
| 9 | `00 02 0F 09` | 9 | 22 | `01 05 1A 15` | 21 |
| 10 | `00 02 20 0A` | 10 | 23 | `00 03 27 16` | 22 |
| 11 | `04 00 2E 0B` | 11 | 24 | `00 03 18 18` | **24** |
| 12 | `00 02 18 17` | 23 | 25 | `00 02 0F 19` | **25 (no description)** |

Record 24 is the hidden 25th gem. Record 25 is unreachable (renderer bound 24;
count page 25 bytes).

### 6.3 Save flags / fields

| Offset | Type | Meaning |
|---|---|---|
| `+0x00` | 4 | `"COLU"` magic |
| `+0x04` | u32 | flags; bit 0 = save initialised (set at `0x080005FC`; cleared by the Erase Data path `0x0800076E`→`0x08004CC4`, store at `0x08000776`) |
| `+0x08` | 4 | per-save options/pad (observed `0x00000000`) |
| `+0x0C` | 12 | name 1 (Shift-JIS) |
| `+0x18` | 12 | name 2 (Shift-JIS) |
| `+0x24` | 50 | gem counts, 2 pages × 25 |
| `+0x1F6` | 4 | second `"COLU"` (footer) |

Report-card grade thresholds live at `+0xF0` (`06 05 05 04 04 03 03 02 02 01
01 00`, then u16 values `0x0AAA, 0x028A, 0x0258, …`).

## 6b. Enumeration

### 6b.1 What the space is

This title has **no code/password space**. The enumerable surfaces are:

1. **Scene space** — 15 slots (`0x08000594`), state byte `0x03003DB6`.
   Values 0..14 are all handled; >14 is rejected by the `cmp #14 / bhi` guard
   and spins forever at `0x08000572`. 12 of 15 are screens; 3, 6 and 10 are
   pure idle/wait entries.
2. **Mode space** — 6 items, cursor `0x03003DB2` 0..5, wraps 5→0 (observed).
   Dispatch table `0x080006C0` maps 0..5 to scenes 4/7/8/9/5/options.
3. **Options space** — 3 items, `0x03003DB3` 0..2: Trade, Rankings, Erase.
4. **Magic Gem space** — 25 descriptions (index 0..24), 2 character pages ×
   25 count bytes = **50 count cells** at `0x03002A44`, and 26 layout records
   (index 0..25). Representable gem identities: 25 with descriptions; 26
   layout slots; the 26th has no description and no reachable count cell.
5. **Name space** — Shift-JIS glyph grid at `0x08026C00`–`0x08027100`: rows
   of up to five glyphs (Latin, kana and symbols; ~160 glyphs counted in the
   window), field capped at 6 characters per player (observed: a 7th A press
   does not grow the buffer). The consumer is the print routine only.

### 6b.2 Novel finding (not in any published list)

**Gem 24 = "Gives you a guaranteed win. Requirement: 66".**

* It is the 25th entry of the description pointer table at `0x087CC33C`
  (`ptr[24] = 0x087CC33C → 0x080228F0`), while the manual, 3rd party cheat indexes and every cheat page describe **24** gems.
* It is present in the collection layout table as record 24 (`gem_id 0x18`)
  and is inside the renderer's 25-slot loop; it is the only gem with a
  "guaranteed win" power.
* Its requirement (66) is the highest of the set and is absent from all
  published lists (published Columns Crown "codes" are memory writes only).
* The story script itself acknowledges it: `"There's a 25th Magic Gem, you
  know."` at file `0x08026624` (pointer table entry 0x087CCB3C), a line that
  only plays in the all-gems branch.

### 6b.3 Bounds proven by rejection

* **Scene id**: `cmp r0,#14; bhi` at `0x0800057A`. 15 is the first rejected
  value; the main loop then spins without dispatch. No scene 15+ exists.
* **Layout record 26**: renderer loop `cmp r4,#24; ble` (`0x08014806` region)
  accepts only r4=0..24. Record 25 (`gem_id 25`) is never drawn. Its gem id also
  indexes past the 25-byte page (`0x03002A44 + 25*page + 25`).
* **Name length**: 6 Shift-JIS characters per name; further A presses leave the
  buffer unchanged (observed on `0x03002A2C`).
* **Mode cursor**: 6 values; a further Down wraps to 0 (observed). There is no
  seventh mode to select.
* **Button-code table**: 380 candidate u16 runs exist in the image, but a full
  pointer scan of every 4-byte-aligned `0x08xxxxxx` value finds **0** references
  to any of them. A table no code points at is not a cheat table.

## 7. Validation evidence

**Observed (emulator RAM/state reads):**

* Boot scene 0 (logo) → A → scene 12 (intro) → ~70 A presses → scene 11 →
  Start 0.5 s → scene 1 with `03002A24 = 1` → Start 0.5 s → scene 2.
* At scene 2, `Down` moves `03003DB2` 0→1→2→…→5 and wraps 5→0; a 0.9 s A at
  `03003DB2 = 0` enters scene 4.
* At scene 2, `03002A2C` holds `82 69 82 60 82 63 82 64` = "JADE"; A presses
  append `82 60` ('A') until the 6-character cap.
* The `.sav` written by the game persists the same `COLU` + names + gem counts
  (word-reversed) and is loaded on the next boot (`03002A24` bit0 set).
* `03002C1C` reads `0x0008` while Start is held, `0x0001` while A is held,
  confirming the active-high held/pressed words and the keymap.

**Derived (instruction/data evidence):**

* One KEYINPUT read (`0x08006E18`), 75 consumers, no history buffer.
* 15-entry scene table and bounds check; 6-mode dispatch table.
* 25-entry gem description table, 26-record layout table, 25-byte count page.
* Name pointers are passed only to `0x08021040` (print), never compared.
* 380 button-mask runs, 0 pointer references.

**Inferred:**

* Gem acquisition conditions (which mode/grade grants each gem) are gameplay
  triggers implemented inside the mode handlers; the mapping from each gem to
  its trigger was not located as a table and is not needed to prove the code
  surface is absent.
* Record 25 is either a cut 26th gem or an off-by-one leftover; the data alone
  cannot distinguish these.

## 8. Unknowns

* The exact acquisition trigger per gem (grade/opponent/stage) is not stored in
  a single table we located; it is spread through the five mode handlers.
* The meaning of layout record bytes `a`/`b`/`xy` is inferred as position/tile
  selectors from their use in the draw calls, not proven.
* The 25th gem's effect ("guaranteed win") was not exercised in play; only its
  description, requirement and table membership are proven.

## 9. Tooling

* `strings`, `xxd`, `arm-none-eabi-objdump -M force-thumb`
* Python 3 + `struct`/`zlib` scripts for header parsing, pointer scans,
  LDR-literal scans, button-mask run scan, gem table extraction, and mGBA
  savestate (`gbAs` zlib chunk) parsing/diffing
* mGBA 0.10.5, Xvfb `:260`, openbox, xdotool
* Verified mGBA state layout: VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`
  (IWRAM `0x03000000` maps to state `0x19000`)

## 10. Legal note

No ROM, extracted graphics, music or text bank is redistributed. Only hashes,
addresses, decoded structure and short descriptive strings needed to identify
the tables are published here.
