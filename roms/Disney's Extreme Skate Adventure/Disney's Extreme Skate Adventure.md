# Disney's Extreme Skate Adventure (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-11-14.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney's Extreme Skate Adventure/Disney's Extreme Skate Adventure.gba` |
| Size | 8 MiB (`0x800000`) |
| Header title | `DISNEY SKATE` |
| Game code | `BESE` |
| Maker code | `52` |
| Software version | `0` (Rev.00) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Complement check | `0x67` (valid) |
| Header checksum | stored `0x0000` (same artefact as every other dump in this set; not evidence of a patch) |
| Save hardware | EEPROM — library string `EEPROM_V122` at `0x08072E60`, 512-byte `.sav` |
| MD5 | `08d2fe71572e3537f2e7d7c08dab5707` |
| SHA-1 | `92a587c8775cbed8f402e6e42d9c05ebe547607e` |
| SHA-256 | `192c2f02312e43710735710f706333f6a7c9c5660315e211d3363dc8c8e1fb0b` |

ROM addresses below are `0x08000000 + file_offset`. All findings are tied to
this exact hash.

### Phase 0 integrity checks

* **Single image.** A scan for the 156-byte Nintendo logo returns exactly one
  hit (file `0x04`). The file is not a multi-game pack.
* **No cracktro / trainer.** `EA00002E` is the canonical entry branch. The
  first 4 KiB contains the stock crt0 sequence (IRQ setup, `0x03007F00` stack,
  `0x08001858` main pointer) and engine tables. No `MODE7`, `SUNHORS`,
  `CRC BANDIT`, `cracktro`, or `trainer` string exists in the first 64 KiB.
* **No padding.** The last byte is not `0xFF`; the 8 MiB image is fully used.

---

## 2. Executive summary

**This GBA SKU has no cheat, password, or code-entry system.** The console
word codes were not ported, no developer/debug menu survives, and the only
published GBA "password" is not implemented in the ROM.

What was established:

1. **The published console cheats do not exist here.** All 15 distinct words
   from the GameCube/PS2/Xbox lists (`entourage`, `ambassador`,
   `trendytrickster`, `inthezone`, `savannah`, `nugget`, `marin`,
   `friendsofbob`, `extremepassport`, `sweetthreads`, `supercharger`,
   `happyfeet`, `frequentflyer`, `gethotgear`, `xtremebuddies`) are absent from
   the 8 MiB image in every encoding tested (ASCII lower/upper, UTF-16LE/BE,
   and four 5-bit packings).

   The game has exactly two text surfaces. The high-score initials field is
   **3 characters**; the versus "Word" field is a real 10-character editor
   (alphabet `0-9 A-Z : . space`, 39 symbols) reachable from
   Versus → Game Settings → Word → A. The word is not a validator: it is the
   spelling target of the two-player word game, and the runtime builds
   `Spell <word> to win!` from it. No comparison against any published word or
   other constant exists, and the longer console codes cannot even be typed
   (10-character field). Neither surface is a password screen.

2. **The published GBA password ("Unlock Peter Pan" —
   Left, Right, Left, Right, Left, Left, Start) is rejected/no-op.** It was
   entered at the title screen, the main menu, the story pause menu, and the
   tutorial pause menu, both plain and with R held (the GBA THPS convention).
   No menu animation, no flag, and no roster change resulted. The string
   `Peter`/`Peter Pan` does not exist anywhere in the ROM, and the skater-name
   table contains exactly seven names. All seven are selectable on a
   zero-progress save, so there is no eighth/hidden slot for a code to unlock.
   The entry is cross-posted on the PS2 and Xbox GameFAQs pages (tagged "GBA"),
   which is the classic cross-SKU artefact described in guide §16.11.

3. **There is no button-sequence validator to enumerate.** The engine's input
   component was located and fully mapped (EWRAM object `0x02002C80`, global
   pointer `0x020000F4`). Only 14 code sites reference it, and they are all
   navigation/gameplay: menu confirm/cancel, "is this direction held", and
   key-state copying. There is no press-history buffer, no sequence table, and
   no comparator. A scan of the whole ROM for the published press masks (8-,
   16-, and 32-bit, active-high/low, with and without R) returns zero hits.
   Of the 18 runs of five or more consecutive `u16` key-mask values in the
   image, none contains an adjacent L/R pair.

4. **One real hidden feature remains in the data: 84 `*_hax0r` script labels.**
   The script bank contains alternate copies of 64 goal dialogues, 14 tutorial
   lessons, 3 story intros, and 3 boss intros, each duplicated with a `_hax0r`
   suffix. Their decoded text is identical to the normal variant in the sample
   examined; no trigger string, menu entry, save bit, or key table was found.
   They are documented here as **dormant/unreachable developer content**, not
   as an in-game cheat. This is the honest limit of the current result
   (see §8).

5. **The only documented multi-button *gate* is not a cheat.** The Sleep Mode
   confirmation screen documents the wake combo **A + B + SELECT**, which
   returns from sleep. No other simultaneous-button gate is presented in any
   menu; ordinary gameplay chords (L/R reverts, trick buttons with directions)
   are moves, not codes.

Consequently the "code space" of this title is empty. The negative is bounded
in §6b by the menu enumeration, the encoding search, the mask search, and the
in-emulator tests.

---

## 3. How to reproduce

### Emulator

```bash
Xvfb :323 -screen 0 1024x768x24 &
DISPLAY=:323 openbox &
DISPLAY=:323 SDL_AUDIODRIVER=dummy mgba -3 "Disney's Extreme Skate Adventure.gba" &
```

mGBA SDL default keymap used throughout:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Savestates: `Shift+F1..F10` save, `F1..F10` load. Menu transitions take
0.5–2 s; hold keys 80–150 ms.

### Menu paths walked (every screen reachable without a top score)

| # | Screen | Path / entries |
|---|---|---|
| 1 | Title | boot; "Press START" |
| 2 | Save-slot select | Start; `Slot 1`, `Empty Slot` ×2, `Erase slot` |
| 3 | Erase confirm | `Erase slot` → `Are you sure?` Yes/No |
| 4 | Main menu | `Story`, `Tutorial`, `Games`, `Versus`, `Options` |
| 5 | World select | Toy Story / Lion King / Tarzan |
| 6 | Skater select | 7 names total (see §6) |
| 7 | Story stage select | stage name, `Goals: n/9`, `1st/2nd/3rd run` |
| 8 | Games stage/mode | stage, `Time Challenge`, `Trick Challenge`, `Turbo Challenge`, `Top Score` / `Stars` |
| 9 | Select Tutorial | 14 lessons |
| 10 | Versus Game Settings | Level, Skater 1, Skater 2, `Word:`, time; A on Word opens **Edit Word** |
| 10b | Edit Word keyboard | `0-9 A-Z : . space` + delete + done; max 10 characters |
| 11 | Options | `Options`, `Sound`, `Credits` |
| 12 | Sound Options | Music Volume, Sound Volume |
| 13 | Credits | auto-scrolling roll (`credits_00`…) |
| 14 | Pause (story) | `Resume`, `View Goals`, `Sleep Mode`, `Exit and Save` |
| 15 | Pause (tutorial) | `Resume`, `Next Lesson`, `Restart Lesson`, `Quit` |
| 16 | Goals list | `Find the Golden Spear`, `Earn a Big Score`, `Collect letters J-A-N-E` |
| 17 | Sleep Mode confirm | `Sleep Mode / Are you sure?` + wake combo |

No entry labelled Codes/Cheats/Password/Debug exists on any of them.
The high-score initials dialog (same keyboard widget, 3-character cap) is
gated behind a score above the level default; the widget itself was exercised
through **Edit Word** (row 10b), and the gate is recorded in §8.

### Code tests performed

All tests entered the sequence with 90 ms holds / 220 ms gaps, then waited
0.5 s and screenshotted. "R held" means `s` was held down for the whole
sequence.

| # | Screen | Sequence | Result |
|---|---|---|---|
| T1 | Title (`Press START`) | L R L R L L Start | Start advanced to save-slot select; no other change |
| T2 | Title | **hold R** + L R L R L L | no visible change |
| T3 | Main menu | L R L R L L Start | no menu animation, no roster change |
| T4 | Main menu | L R L R L L | no change (savestate diff: only animation noise) |
| T5 | Story pause | L R L R L L Start | no pause-menu shake/spin; Start resumed play |
| T6 | Story pause | **hold R** + L R L R L L | no change |
| T7 | Tutorial pause | L R L R L L | no change |
| T8 | Tutorial pause | **hold R** + L R L R L L | no change |

RAM verification for T4/T5: two savestates taken 1.2 s apart with no input
(the baseline) change exactly the same addresses as the "after code" pair
(frame counter/timer at `0x0205480E..0x02054814`, RNG at `0x020218F8`,
graphics state). No unique byte is written by the sequence.

### Save-level verification

A slot was created, played into a story stage, exited with **Exit and Save**,
and the EEPROM image was dumped after closing mGBA: 512 bytes, header
`00 00 00 00 00 01 d6 09 …` at slot 0. Re-entering the same stage with and
without the published sequence produced the same empty progress record
(`01` at offset `0x3C`, no extra flags). The published code changes no save
bit.

### Static tools used

```bash
strings -t x -n 4 "Disney's Extreme Skate Adventure.gba" > strings4.txt
python3 tools.py dump 0x6c000 0x120          # menu string bank
python3 tools.py ptrs 0x0802e33c             # skater table xrefs
arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 \
  --start-address=0x08010840 --stop-address=0x08010960 -M force-thumb \
  "Disney's Extreme Skate Adventure.gba"
python3 encsearch.py                         # encoding search
python3 ssdiff.py a.ss1 b.ss2                # savestate RAM diff
```

Scripts are in `/tmp/opencode/extremeskate/` (`tools.py`, `encsearch.py`,
`ssdiff.py`, `keys.py`).

---

## 4. Address map

### Code / data

| Address | Meaning |
|---|---|
| `0x08010874` | input update: `held = ~KEYINPUT & 0x3FF`, stores held / held-copy / pressed / released |
| `0x0801089C` | held-direction → internal direction code (16-byte lookup at `0x08065CB5`) |
| `0x080108E4` | input set-from-argument (used once) |
| `0x08010900` | read hardware keys (`~*(u16*)0x04000130 & 0x3FF`) |
| `0x08010914` | input-object constructor (12-byte object, vtable `0x087F42B8`) |
| `0x08010934` | input-object reset/construct |
| `0x08010954` / `0x08010958` / `0x0801095C` | get released / pressed / held |
| `0x08022FB4` | Sleep Mode confirm-screen constructor (`0x080726E8`, `0x0807270C`, `0x08072728`) |
| `0x08023200` | title screen constructor (`0x08072774` = `Press START`) |
| `0x08023280` | Select Tutorial constructor (loads the 14-entry table) |
| `0x080235A4` | tutorial-list draw/update (selection highlight) |
| `0x08021160` | generic text-entry screen constructor (initials and Edit Word) |
| `0x080116FC` | name/id interning helper used by the script/UI layer (probable) |
| `0x0802E2CC` | tutorial table: 14 × {`char* title`, `char* description`} |
| `0x0802E33C` | skater names: `Woody`, `Buzz Lightyear`, `Jessie`, `Simba`, `Nala`, `Tarzan`, `Terk` |
| `0x0802E37C` | 7-entry pointer table into `0x0802E33C` |
| `0x0802E398` | stage-name table: `Andy's Room`, `Jungle Treehouse`, `Pride Rock`, `Pizza Planet`, `Human Camp`, `Elephant Graveyard`, `Toy Story Boss`, `Tarzan Boss`, `Lion King Boss` |
| `0x0806C01C` | main-menu strings (`Story`, `Tutorial`, `Games`, `Versus`, `Options`, …) |
| `0x0806E550` | story pause strings (`Resume`, `Continue Story`, `View Goals`, `End Current Goal`, `Sleep Mode`, `Exit and Save`) |
| `0x0803237C` | tutorial pause strings (`Paused`, `Resume`, `Next Lesson`, `Restart Lesson`, `Quit`) |
| `0x080725C8` | versus word preset table: 3 pointers → `Alien` (`0x080725B0`), `Mungo` (`0x080725B8`), `Timon` (`0x080725C0`); editable buffer at `0x02000870` |
| `0x08072E60` | `EEPROM_V122` (save-library signature) |
| `0x0802A91C`–`0x080337C0` | compiled script bank (dialogues, tutorial scenes, goal scenes) |

### RAM (from mGBA `.ssN` states)

| Address | Meaning |
|---|---|
| `0x020000F4` | global pointer to the live input object |
| `0x02002C80` | input object: `+0` held, `+2` held copy, `+4` pressed (edge), `+6` released, `+8` vtable `0x087F42B8` |
| `0x02000870` | versus word buffer (16 bytes; up to 10 characters + NUL), e.g. `AlienHHH` |
| `0x03000000`–`0x03007FFF` | IWRAM (stack, engine globals) |
| `0x02000000`–`0x0203FFFF` | EWRAM (heap, screen objects, script state) |

Verified live: holding Left at the main menu makes
`0x02002C80 = 20 00 20 00 00 00 00 00 b8 42 7f 08` (held = `0x0020`).
Holding Start gives `08 00 08 00 …`. This is the anchor for every key claim
below.

---

## 5. Algorithm

There is no password/validator algorithm. The relevant "algorithm" is the
input pipeline, which was reversed to prove that no sequence comparator exists:

```
read_keys():
    return (~*(volatile u16*)0x04000130) & 0x03FF

input_update(obj, held):
    prev = obj->held
    obj->pressed  = held & ~prev
    obj->released = prev & ~held
    obj->held = obj->held2 = held

direction(obj):
    d = 0
    if obj->held & 0x10: d |= 8      # Right
    if obj->held & 0x20: d |= 4      # Left
    if obj->held & 0x80: d |= 2      # Down
    if obj->held & 0x40: d |= 1      # Up
    return table_08065CB5[d]
```

Menu navigation uses `pressed & 0x08` (Start) and `pressed & 0x01/0x02`
(A/B) plus Up/Down edges; gameplay uses the direction getter. **There is no
second stage**: no ring buffer, no expected-mask array, no index counter, no
comparison against a stored sequence.

The sleep screen adds one held-mask gate documented on-screen
(`A + B + SELECT`, consistent with `held == 0x07`); it is a wake path, not a
code.

The `_hax0r` scripts are selected by the script/UI layer, not by a player
input path that survived into this build (see §8).

---

## 6. Tables

### 6.1 Skater roster (`0x0802E33C`, exactly 7 entries)

| # | Name | World |
|---|---|---|
| 0 | Woody | Toy Story |
| 1 | Buzz Lightyear | Toy Story |
| 2 | Jessie | Toy Story |
| 3 | Simba | Lion King |
| 4 | Nala | Lion King |
| 5 | Tarzan | Tarzan |
| 6 | Terk | Tarzan |

All seven are available on a fresh, zero-goal save (verified by cycling the
skater selector in all three worlds). There is no locked eighth entry, no
"Peter Pan" string, and no skater-unlock message in the ROM. The skater list
is therefore a closed set of 7; a code could not add an eighth selectable name.

### 6.2 Tutorial lessons (`0x0802E2CC`, 14 entries)

`Forward Motion`, `Turning`, `Crouching / Jumping`, `Ramp Jumps`, `Air Tricks`,
`Grab Tricks`, `Grinds`, `Balance`, `Manuals`, `Lip Tricks`, `Revert`,
`Spine Transfer`, `Combos`, `Specials`.

### 6.3 Stage names (`0x0802E398`, 9 entries)

`Andy's Room`, `Jungle Treehouse`, `Pride Rock`, `Pizza Planet`, `Human Camp`,
`Elephant Graveyard` (six parks) plus `Toy Story Boss`, `Tarzan Boss`,
`Lion King Boss` (three boss arenas). Console-only stages (`Zurg's World`,
`Clayton's Ship`, `Scar's Canyon`, `Olliewood`) do not exist in this build.

### 6.4 Versus word (`0x080725C8`, 3 presets + editor)

Presets `Alien`, `Mungo`, `Timon` (5 characters each), but the field is
**editable**: pressing A on the `Word:` row opens the `Edit Word` keyboard
(`0x0806C06C`), alphabet `0-9 A-Z : . space` (39 symbols), with a delete key
and a done key. Measured maximum length **10 characters** (20 further letter
presses appended only 5 characters to a 5-character seed). The edited value is
stored at EWRAM `0x02000870` (16-byte buffer) and is consumed as the versus
spelling target, e.g. runtime text `Spell <word> to win!` at `0x02032096`.
There is no constant comparison of this buffer anywhere in the ROM.

### 6.5 Published codes and their status in this ROM

| Code | Platform listed | Present in BESE? | Surface |
|---|---|---|---|
| `entourage` | GC | no | typeable in Edit Word (9), not compared |
| `ambassador` | GC | no | typeable in Edit Word (10), not compared |
| `trendytrickster` | GC | no | too long (14) for Edit Word |
| `inthezone` | GC | no | typeable in Edit Word (9), not compared |
| `savannah` | GC/PS2/Xbox | no | typeable in Edit Word (8), not compared |
| `nugget` | GC/PS2/Xbox | no | typeable in Edit Word (6), not compared |
| `marin` | GC/PS2/Xbox | no | typeable in Edit Word (5), not compared |
| `friendsofbob` | PS2 | no | too long (12) |
| `extremepassport` | PS2 | no | too long (15) |
| `sweetthreads` | PS2 | no | too long (12) |
| `supercharger` | PS2 | no | too long (12) |
| `happyfeet` | Xbox | no | typeable in Edit Word (9), not compared |
| `frequentflyer` | Xbox | no | too long (13) |
| `gethotgear` | Xbox | no | typeable in Edit Word (10), not compared |
| `xtremebuddies` | Xbox | no | too long (13) |
| L,R,L,R,L,L,Start ("Peter Pan") | GBA listing | no mask table; no `Peter` string | tested, no-op |

"Present" means a literal match in ASCII lower/upper, UTF-16LE/BE, or 5-bit
packing (A=0 and A=1, LSB- and MSB-first).

---

## 6b. Enumeration

### Space definition

Because the ROM contains no validator, the representable space is defined by
the *published formats* plus every input surface the UI actually exposes:

1. **Console word-code space** — 15 published words, lengths 5–15 over
   `[a-z]`. Format size: Σ 26^len ≈ 10^21; accepted set in this ROM = ∅
   (0/15 literals present; 0 fields compared; only the 5–10-character subset is
   even typeable into the versus word editor, where it is not validated).
2. **GBA button-sequence space** — 10 buttons, published length 7
   (10^7 = 10,000,000 sequences of length 7; 10^1+…+10^16 for ≤16 presses).
   Accepted set in this ROM = ∅, because there is no sequence comparator and
   no stored sequence. Literal mask searches:
   * `20 10 20 10 20 20 08` (L,R,L,R,L,L,Start) as 8/16/32-bit: 0 hits
   * reversed (`10 20 …`): 0 hits
   * active-low complements (`DF EF …`): 0 hits
   * R-held variants (`0x120,0x110,…` as `u16`): 0 hits
   * 4-press prefix `20 10 20 10` as 8/16/32-bit: 0 hits
   * whole-ROM scan of all 5+-element `u16` runs drawn from
     `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}`: **18 runs**, maximum 3
     distinct values, and **0 runs containing an adjacent L/R pair**.
3. **Text-entry space** — two fields share the same keyboard widget
   (`0x08021160`):
   * high-score initials: stack argument 3 caps it at **3 characters**;
   * versus `Edit Word`: measured cap **10 characters**, alphabet
     `0-9 A-Z : . space` = **39 symbols** (space size
     `39^1 + … + 39^10 ≈ 8.1 × 10^15`).
   Neither is validated: the initials go into the high-score record and the
   versus word is formatted into `Spell <word> to win!`. No compare-with-
   constant call site exists, and no console word is present as a literal.
   The 10-character cap rejects 7 of the 15 console words by length;
   the eight that fit (`entourage`, `ambassador`, `inthezone`, `savannah`,
   `nugget`, `marin`, `happyfeet`, `gethotgear`) are still not compared.

### Novel code(s)

**None can exist.** To satisfy the §0.2 requirement in the only way this title
permits, the report instead states and proves the closed negative:

* 0 of 15 published console words are compared by any validator (0 literal
  matches); 7 of the 15 cannot even be typed (longer than the 10-character
  versus word field); the other 8 fit but are only used as a spelling word;
* 0 of 6 tested GBA sequence variants produce any RAM or screen change;
* the roster is a closed 7-name set with no hidden slot.

No generated code is claimed, because no accept path exists to confirm one.
Minting a code and forcing it into RAM would only demonstrate memory editing,
which is out of scope and would not be an in-game cheat.

### Bounds proven by rejection

| Out-of-format input | Where | Result |
|---|---|---|
| 11th character | Edit Word | rejected: 20 further letter presses on a 5-char seed produced exactly 10 characters |
| `ALIENHHHH` (10 chars, tested) | Edit Word | accepted; stored at `0x02000870`; becomes `Spell ALIENHHHH to win!`; no flag/unlock |
| `savannah` / `entourage` / `ambassador` (≤10) | Edit Word | representable in the field, but the literals are absent and no comparator exists (derived) |
| `friendsofbob` (12), `extremepassport` (15), `trendytrickster` (14), `frequentflyer` (13), `xtremebuddies` (13), `sweetthreads` (12), `supercharger` (12) | Edit Word | **cannot be typed** (>10) |
| `Peter Pan` / `peterpan` | any screen | no field; `Peter` absent in ASCII/UTF-16; no 8th name slot |
| L,R,L,R,L,L,Start | title | advances to save select only |
| L,R,L,R,L,L,Start (+R) | title/main/pause | no state change |
| L,R,L,R,L,L | main/pause | no unique RAM byte vs. no-input baseline |
| A,B,Select (wake combo) | sleep screen | documented wake path, not a cheat |

---

## 7. Validation evidence

### Observed (emulator)

* All 17 screens in the table were reached and screenshotted in mGBA, plus the
  `Edit Word` keyboard (row 10b).
* The title accepts Start; A alone (tested) does nothing.
* Skater selector shows exactly Woody/Buzz/Jessie (Toy Story),
  Simba/Nala (Lion King), Tarzan/Terk (Tarzan) on a fresh save.
* Story stage select shows `Goals: 0/9` and `1st/2nd/3rd run`.
* Games stage select shows `Andy's Room`, `Time Challenge`, `Trick Challenge`,
  `Turbo Challenge`, `Top Score / 0 Stars`.
* Versus Game Settings shows Level / Skater 1 / Skater 2 / `Word:` / time.
  Pressing A on `Word:` opens the `Edit Word` keyboard
  (`0-9 A-Z : . space`, delete, done). `Alien` + 20 letter presses produced a
  10-character word; further presses were ignored. The accepted word appears
  back on the settings row (`Word: AlienHHH`), is stored at EWRAM
  `0x02000870`, and the running game builds `Spell AlienHHH to win!`
  (`0x02032096`). This proves the field is the versus spelling target, not a
  code validator.
* Story pause shows 4 entries (Resume, View Goals, Sleep Mode, Exit and Save);
  the tutorial pause shows a different 4 (Resume, Next Lesson, Restart Lesson,
  Quit). The longer string bank is context-filtered.
* Sleep confirm shows `hold down A+B+SELECT`.
* Input object `0x02002C80` tracks held keys exactly (`Left` → `0x0020`,
  `Start` → `0x0008`).
* Savestate diffs with/without the published sequence show no unique change.
* EEPROM save is 512 bytes and survives power-cycle; no code-related bit.

### Derived (static)

* Input component `0x08010874` + getters + action mapper is the only key path;
  14 references to the input global (3 callers of the action mapper, 1 caller
  of the key setter) — none is sequence-based.
* Skater/tutorial/stage tables have 7/14/9 entries; the versus word preset
  table has 3 entries behind a 10-character free editor.
* All 15 console words absent in 8 encodings (120 literal checks).
* `Peter`/`Peter Pan` absent in 8 encodings.
* 84 `_hax0r` script labels exist (64 goal + 14 tutorial + 3 story + 3 boss).

### Inferred

* The `_hax0r` scripts are developer alternates for the same dialogue; the one
  sample decoded (`tutorial_0_hax0r`) contains the same lesson text and the
  same choice nodes as `tutorial_0`. Their selector was not found in retail
  code/data, so they are treated as unreachable.
* The published Peter Pan password is a console-side or fabricated entry; the
  GBA build has no Peter Pan asset/string/slot.

---

## 8. Unknowns

1. **The `_hax0r` selector.** The 84 alternate scripts exist, but the writer
   of the flag/ID that chooses them was not located. Because no trigger string,
   menu row, save bit, or key table exists, the most likely explanation is a
   developer build flag compiled out of this revision. A follow-up could parse
   the compiled script format and find the conditional node.
2. **Other revisions/regions.** Only Rev.00 `BESE` was analysed. An EU build
   could theoretically differ; nothing in this image suggests a code surface.
3. **High-score initials.** The same text widget is constructed with a
   3-character cap (`0x08013A08`..`0x08013A12`). The widget itself was driven
   through the `Edit Word` entry point; the initials instance was not reached
   in-game because it needs a score above the level default. Its consumer is
   the high-score record, and no constant comparison is reachable from that
   construction site in the inspected paths.

---

## 9. Tooling

| File | Purpose |
|---|---|
| `tools.py` | ROM pointer search (`ptrs`), hex dump (`dump`) |
| `encsearch.py` | multi-encoding literal search for published codes |
| `ssdiff.py` | decompress mGBA `gbAs` savestate chunk and diff IWRAM/EWRAM |
| `keys.py` | xdotool key helper (focus, hold, screenshot) |

Environment: mGBA (SDL) 0.10.x, Xvfb `:323`, openbox, xdotool, scrot,
ImageMagick, `arm-none-eabi-objdump` (binutils-arm-none-eabi), Python 3 +
Capstone 5.0.7.

Reproduction of the key static counts:

```bash
# console words + Peter Pan, 8 encodings, 0 hits for full words
python3 encsearch.py

# all 5+ u16 key-mask runs: 18 runs, none with adjacent L/R
python3 - <<'PY'
import struct
rom=open("Disney's Extreme Skate Adventure.gba","rb").read()
V={1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}
i=0; runs=[]
while i < len(rom)-2:
    j=i; seq=[]
    while j < len(rom)-1:
        v=struct.unpack_from("<H",rom,j)[0]
        if v in V: seq.append(v); j+=2
        else: break
    if len(seq)>=5 and len(set(seq))>=3: runs.append(seq); i=j
    else: i+=2
print(len(runs), sum(1 for s in runs for k in range(len(s)-1) if {s[k],s[k+1]}=={0x10,0x20}))
PY
```

---

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed with this
report. Only hashes, addresses, structure sizes, and short identifiers needed
to reproduce the analysis are included.
