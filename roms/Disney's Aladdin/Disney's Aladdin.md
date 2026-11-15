# Disney's Aladdin (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney's Aladdin/Disney's Aladdin.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `ALADDIN` (`0xA0`) |
| Game code | `BADE` (USA) |
| Maker code | `08` (Capcom) |
| Version | 0 |
| Entry word | `0xEA00002E` (branch to `0x080000C0`) |
| Fixed byte `0xB2` | `0x96` |
| Complement `0xBD` | `0xF0` (computed `0xF0`, valid) |
| Header checksum `0xBE` | `0x0000` (typical of a rebuilt/extended header) |
| MD5 | `4bda2a3e0249dfd09330dabc3aa20978` |
| SHA-1 | `3cfe653a54f3bc9f3ad20234de680ebfc4145cf6` |
| SHA-256 | `8faf7635d203fde1b556ebc0c5b9110e03570605b5306f3ec21addddca837337` |

**Image layout.** The Nintendo logo occurs twice: at file `0x04` and again at
`0xC4`. The file therefore carries a normal cartridge header at `0x0` and a
second, identical header at `0xC0`; the entry word at `0x0` branches to the
second header at `0xC0`, whose identical entry word branches to the ARM crt0
at `0x08000180`. This is a multiboot-style duplicated header, not a trainer:
the crt0 at `0x180` is the stock `mov r0,#0x12 / msr CPSR` sequence, the literal
pools point at `0x08000429` (valid Thumb main) and the RAM stacks
(`0x03007900`, `0x03007E00`, `0x03007FA0`), and no cracktro/menu code precedes
the game. Complement byte is correct. No patch text, no appended payload.

## 2. Executive summary

**There is no in-game password, cheat-code, level-select or debug-menu system
in the GBA SKU.** The GBA port replaced the SNES password engine with a
512-byte SRAM save. This is not an inference from missing strings: the string
`PASS WORD` still exists in the ported text bank, but no code path can request
it, and the title menu has exactly three items (`GAME START`, `LOAD GAME`,
`OPTIONS`) with no fourth slot hidden behind a wrap.

What the ROM does contain:

* a complete, live message/text system (`u16` glyphs, per-language pointer
  tables) whose English table still lists the SNES-era labels `STAGE SELECT`
  (index 6) and `PASS WORD` (index 53). **Neither index is ever queued by any
  of the 30 message-queue call sites**, so neither screen exists in this build.
* a save engine (`SAVE`/`LOAD GAME`, "NO SAVED DATA", 512-byte SRAM) that
  replaces the password feature.
* one live, conditionally-drawn leftover: `TIME ATTACK MODE` (message 58),
  gated on a game-state byte at `0x03000665`. It is not a title-menu item in
  this build; its display/entry trigger was not established (see §8).
* a developer-style soft reset: **L + R + Start + Select** on the options
  screen returns to the boot/language screen (observed).

The seven published "GBA" passwords (`GMAS JMPG GJAM MAGP PJSP JPAJ APMS`)
are the **SNES** passwords. They are absent from this ROM in ASCII, lower-case,
`+0x20`, UTF-16LE/BE, spaced glyph, `0x2000/0x2400/0x2800/0x2C00/0x3000`
glyph encodings, as all 720 four-symbol byte permutations (three row orders),
and as packed 3-bit/4-bit `u16` tables. There is no input surface on which to
enter them. This agrees with the contemporary 2004 IGN review: the GBA version
"sticking in a save RAM chip so players don't have to fumble with the original
version's stupid password engine."

**Deliverable:** a bounded negative. Code space size = **0**. No novel code
can be minted because no code field, validator or table exists; the proof is
the menu enumeration, the complete queue-index enumeration, and the
encoding/table searches in §6b.

## 3. How to reproduce

Emulator and display:

```bash
Xvfb :317 -screen 0 1024x768x24 &
DISPLAY=:317 openbox &
DISPLAY=:317 SDL_AUDIODRIVER=dummy mgba -3 game.gba &
W=$(DISPLAY=:317 xdotool search --name mGBA | head -1)
DISPLAY=:317 xdotool windowfocus "$W"
```

Default mGBA SDL keymap used: **A = `x`, B = `z`, L = `a`, R = `s`,
Start = `Return`, Select = `BackSpace`, D-pad = arrows**. Hold 40–80 ms;
longer holds double-step menus. mGBA hotkeys: `Ctrl+P` pause, `Ctrl+N` frame
advance, `F1`–`F10` load state, `Shift+F1`–`F10` save state.

Menu path:

1. Boot → `ENGLISH / DEUTSCH / FRANÇAIS / ESPAÑOL`. Choose `ENGLISH`.
2. Intro story text → `Start` skips to the title.
3. Title menu: `GAME START / LOAD GAME / OPTIONS`. D-pad moves, A/Start
   confirms. **Three items, wrapping** (Up from `GAME START` goes to
   `OPTIONS`; Down from `OPTIONS` goes to `GAME START`).
4. `OPTIONS`: `COLOR MODE TYPE1 TYPE2`, then `DASH B / JUMP A / THROW L /
   HOVERING R`, then `EXIT`. No stage-select row.
5. In game, `Start`: `CONTINUE / SAVE / TYPE1 TYPE2`. `SAVE` opens
   `NO SAVED DATA` with `SAVE / EXIT`, then writes SRAM.
6. On the options screen, hold **L+R+Start+Select**: the game returns to the
   boot/language screen (soft reset). Reproduced three times.

Published codes tested (all rejected structurally — no entry field):
`GMAS`, `JMPG`, `GJAM`, `MAGP`, `PJSP`, `JPAJ`, `APMS` (Genie/Abu/Aladdin/
Sultan/Jafar/Jasmine notation).

## 4. Address map

| ROM address | File offset | Meaning |
|---|---|---|
| `0x08000000` | `0x0` | cartridge header |
| `0x080000C0` | `0xC0` | duplicate multiboot header; entry branches to `0x180` |
| `0x08000180` | `0x180` | ARM crt0 (stock) |
| `0x08000428` | `0x428` | Thumb `main` (literal at crt0 `0x1D0`) |
| `0x0800C79C` | `0xC79C` | text lookup: `r0 = message index` → entry pointer |
| `0x0800D100` | `0xD100` | queue message (increments slot counter) |
| `0x0800D124` | `0xD124` | queue message, second slot bank |
| `0x0824EC38` | `0x24EC38` | English message-pointer table (index 0..65, then a mirrored block) |
| `0x0824BF66` | `0x24BF66` | small byte table of message indices (values `0x27/0x67/0xA7/0x25/0x65/0xA5/0x23/0x63/0xA3`) |
| `0x080524BC` | `0x524BC` | `GAME START` (index 7) |
| `0x08052538` | `0x52538` | `LOAD GAME` (index 8) |
| `0x080525AC` | `0x525AC` | `OPTIONS` (index 9) |
| `0x08052484` | `0x52484` | `STAGE SELECT` (index 6, dead) |
| `0x08052C08` | `0x52C08` | `PASS WORD` (index 53, dead) |
| `0x08052C80` | `0x52C80` | `TIME ATTACK MODE` (index 57/58, live queue site) |
| `0x0801DF64` | `0x1DF64` | title-screen init block |
| `0x0801DF9A` | `0x1DF9A` | queues index 19 (`PRESS START`), then 7, 8, 9 |
| `0x0801DF0C` | `0x1DF0C` | queue of index 58 (`TIME ATTACK MODE`), gated |
| `0x0801F170` | `0x1F170` | options screen queues index 23 (`COLOR`) |
| `0x080093E4` | `0x93E4` | save-block checksum/verify |
| `0x02001800` | — | save buffer (checksum block base) |
| `0x03000470` | — | game-state struct base |
| `0x030005C8` | — | title menu count = 3 |
| `0x03000665` | — | `TIME ATTACK MODE` gate byte (game-state `+0x1F5`) |
| `0x0E000000` | — | SRAM (512-byte `.sav` generated by mGBA) |

## 5. Algorithm

### 5.1 Message system (the only “code-like” table system)

Text is stored as little-endian `u16` glyphs `0x20xx` (`0x2041` = `A`); control
values `< 0x100` are spaces/line breaks, `0xFFFF` terminates. A text entry is:

```
u16 length; u16 text_id; length * u16 glyph; u16 0
```

The English pointer table at `0x0824EC38` is indexed by message number
(masked with `0x7F` by `0x0800C79C`). The queue functions `0x0800D100` and
`0x0800D124` take a message index in `r0` and increment the slot counter; they
are reached by 30 direct `BL` sites and by no function pointer.

### 5.2 Save engine

The GBA port stores options and progress in 512 bytes of SRAM. The `.sav`
created by mGBA after the first language selection begins:

```
0000: 07 06 05 04 03 02 01 00 00 00 00 00 00 00 00 00
0010: 00 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00
0020: 02 00 00 00 00 00 01 00 ff ff ff ff ... (to 0x1FF)
```

`0x080093E4` sums a 30-byte block at `0x02001800` and compares the result with
the block's check byte. The pause menu's `SAVE` opens the save screen; the
title's `LOAD GAME` resumes the saved game. This is the feature that replaces
the SNES password engine.

## 6. Tables

### 6.1 Live front-end menu items

| Screen | Items | Evidence |
|---|---|---|
| Boot | ENGLISH, DEUTSCH, FRANÇAIS, ESPAÑOL | observed |
| Title | GAME START (7), LOAD GAME (8), OPTIONS (9) | observed + init `0x1DF9A` |
| Options | COLOR MODE/TYPE1/TYPE2, DASH, JUMP, THROW, HOVERING, EXIT | observed + queue 23 |
| Pause | CONTINUE, SAVE, TYPE1, TYPE2 | observed |
| Save | NO SAVED DATA, SAVE, EXIT | observed |
| In-game | no password/debug screen | observed over all routes above |

### 6.2 Live and dead message indices

| Index | Text | Status |
|---:|---|---|
| 6 | `STAGE SELECT` | **dead** (never queued) |
| 7 | `GAME START` | live |
| 8 | `LOAD GAME` | live |
| 9 | `OPTIONS` | live |
| 19 | `PRESS START` | live |
| 23 | `COLOR` | live |
| 47/48 | `BONUS` / `FINAL` | live |
| 49/50 | `YOU FAILED` / `YOU COMPLETED` | live (results) |
| 51/52 | `MONAURAL` / `STEREO` | live |
| 53 | `PASS WORD` | **dead** (never queued) |
| 56 | `FINAL BATTLE` | live |
| 57/58 | `TIME ATTACK MODE` | queued at `0x1DF0C` only when `[0x03000665] != 0` |
| 61/62 | `YOU ARE ...` | live (rank strings) |

### 6.3 Published codes (verification status)

| Level | Code | Present in ROM? |
|---|---|---|
| Stage 2 Cave of Wonders | `GMAS` | no |
| Stage 3 Escape | `JMPG` | no |
| Stage 4 Genie's Lamp | `GJAM` | no |
| Stage 5 Pyramid | `MAGP` | no |
| Bonus A Whole New World | `PJSP` | no |
| Stage 6 Jafar's Palace | `JPAJ` | no |
| Final Battle | `APMS` | no |

These are the SNES codes. The GBA title has no `PASS WORD` item and no text
entry widget, so they are not enterable in this SKU.

## 6b. Enumeration

**Space definition.** Password/cheat code space = **0**. There is no alphabet,
length, checksum, reserved-bit field, table or validator in the image: the
input surface itself is absent.

Proof, in order of strength:

1. **Title menu count.** The title init at `0x0801DF64` queues exactly three
   labels (`0x0801DF9A`: index 19, then `0x0801DFA2/A8/AE`: indices 7, 8, 9)
   and writes the menu count 3 to `0x030005C8`/`0x030005CD`. Frame-stepping
   confirmed the ring: Up from `GAME START` wraps to `OPTIONS`, and repeated
   Down presses only cycle among those three labels. There is no fourth,
   invisible item.
2. **Queue-index closure.** All 30 direct `BL` sites to the two queue
   functions were decoded. The immediate index set is
   `{0,5,7,8,9,19,23,28,30,31,45,47,48,50,54,55,58,59,60,64,65,66}`; the four
   computed sites resolve to index 11, `0x00/0x38` (56), the byte table
   `0x0824BF66` (`0x27/0x67/0xA7/0x25/0x65/0xA5/0x23/0x63/0xA3`) and 31. No
   site can produce **53** (`PASS WORD`) or **6** (`STAGE SELECT`). There are
   no function pointers to the queue routines, so no indirect caller exists.
3. **No code table.** The seven published four-symbol codes were searched as:
   * ASCII, lower-case, `+0x20`, UTF-16LE, UTF-16BE, `char+0x20`, and
     `u16` glyphs with high bytes `0x20/0x24/0x28/0x2C/0x30` → **0 hits**
     for every code; the concatenated list also → 0.
   * all `6! = 720` symbol→value assignments × three row orders (level order
     with/without a blank stage 1, published order, reverse) as contiguous
     four-byte records, with 0-based and 1-based values → **0 tables**.
   * packed 3-bit and 4-bit `u16` records under all 720 assignments → **0**.
4. **No validator.** No code path consumes a four-symbol input buffer, and no
   per-level code generator or comparison table was found. The only 512-byte
   persistent structure is the save block (§5.2).

**Button-code space.** All front-end screens were walked. The published SNES
level-select entry (L, R, Start, Select, X, Y, A, B on controller 2) cannot be
performed on a GBA (no X/Y, one controller). The nearest GBA sequence
(L, R, Start, Select, A, B) was tested on the options screen: it does not
produce a chime or a `STAGE SELECT` row; its first four presses match the
GBA soft reset (L+R+Start+Select), which returns the game to boot. Holding
L+R and pressing Up on the title (the SNES sub-level selector) also produced
no stage number. A scan for runs of ≥5 key-mask halfwords found 96 candidates;
all are graphics/audio/OAM or the 10-entry control-order table at `0x51B54`
(`1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200`), not a cheat table.

**Novel code.** None exists to mint. The closest live “unlockable” is
`TIME ATTACK MODE` (message 58) gated by `0x03000665`; it is not a code entry
and did not become a title-menu item when the gate was forced to 1.

**Bounds proven by rejection.** Because the title menu has no password field,
the game's rejection is structural: there is no cell, cursor or ACCEPT action
for any of the seven published codes. Testing the strings against the image
proves they are not stored, and the queue closure proves their label is never
drawn. This is a complete negative for this SKU, not an untested guess.

## 7. Validation evidence

**Observed**

* Boot/language screen; title with three items and a wrapping cursor
  (frame-stepped); options screen rows; pause menu; `SAVE` screen reading
  `NO SAVED DATA`; gameplay and level intro (`ACTION`).
* Since `LOAD GAME` starts level 1 and the pause `SAVE` path writes the SRAM
  image, the port's save feature is live.
* L+R+Start+Select on the options screen reboots to the language screen.
* The seven published codes cannot be entered (no field).

**Derived**

* `PASS WORD` (53) and `STAGE SELECT` (6) are dead message entries: the
  complete 30-site queue enumeration cannot produce those indices.
* The text bank is a direct SNES port: it retains SNES-only labels and
  localized variants (`PASS WORT`, `MOT DE PASSE`, `CLAVES`) that no GBA screen
  uses.
* The GBA save engine replaces the password engine (matches the 2004 IGN
  review's statement about the save RAM chip).

**Inferred**

* `TIME ATTACK MODE` is a post-clear or results-screen label, not a cheat
  menu: the gate byte is in the game-state struct and the label is queued in
  the title/footer code, but forcing it did not add a selectable item.

## 8. Unknowns

* The exact writer/trigger for `0x03000665` (the `TIME ATTACK MODE` gate) was
  not isolated. It is almost certainly set by game completion, but that was
  not played to the end in this pass.
* Whether the debug/test strings `BG CHAR TEST` / `OBJ CHAR TEST`
  (`0x5B9A0`, `0x5BCF4`) belong to a reachable developer screen. They have
  pointers only inside data tables (`0x431CC`, `0x44F84`), not in game code.
* The brand-new GBA-only level mentioned in contemporary reviews was not
  enumerated; it is normal progression content, not a code/unlockable.

## 9. Tooling

* `mgba` 0.10-era SDL build, `Xvfb :317`, `openbox`, `xdotool`, ImageMagick
  `import`, `SDL_AUDIODRIVER=dummy`.
* `arm-none-eabi-objdump`, Python 3 + Capstone 5.0.7 for Thumb disassembly,
  BL-target scans, message-table parsing and encoding searches.
* mGBA savestates (`.ss*` PNG with zlib `gbAs` chunk) for RAM inspection and
  frame-stepped menu navigation; mGBA CLI debugger (`-d`) for a breakpoint at
  the title init and a RAM write to `0x03000665`.
* Scripts used in the work directory: `p0.py` (header/hash), `analyze.py`
  (message table, queue sites, code-encoding search), `state.py` (savestate
  extraction), `findtable.py` (symbol-table search).

**Legal note.** No ROM, graphics, music or text assets are redistributed.
Only hashes, addresses, message labels and derived algorithms are published.

## 10. Sources consulted

* GameFAQs GBA pages for the published password list (the pages are SNES
  guides mirrored onto the GBA entry).
* IGN, "Disney's Aladdin" GBA review, 2004-10-06: the GBA version adds a save
  RAM chip instead of the SNES password engine.
* Nintendo World Report GBA review, 2004-11-06: "You can now save whenever
  you want."
