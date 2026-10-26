# Atomic Betty (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Atomic Betty/Atomic Betty.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `ATOMIC BETTY` (0xA0, 12 bytes, space padded) |
| Game code | `BETE` (0xAC) |
| Maker code | `AF` (0xB0) |
| Fixed byte 0xB2 | `0x96` |
| Main unit / device | `0x00` / `0x00` |
| Software version | `0x00` |
| Complement check 0xBD | `0x45` (recomputed `0x45`, valid) |
| Reserved 0xBE–0xBF | `0x0000` |
| Entry branch 0x00 | `0xEA00002E` → `0x080000C0` |
| MD5 | `a3dd3b98ad5049503af18f80c84731fc` |
| SHA-1 | `59e7400802ab634065b9674de3f437ddf8309d6e` |
| SHA-256 | `e85966aef5fded854a4c1d833f6ef6750a466975402b9f3bd87eead4bc96aa35` |

Embedded-header scan: the 156-byte Nintendo logo (rom[0x04:0xA0]) occurs
once, at file offset `0x04`; there is no second image and no multi-game
shell. A multiboot/link header area occupies `0xC0–0xE3`: eight zero bytes, the
ASCII tag `SHAT01` at `0xC8` followed by `0x96` at `0xCE`, `0x0000F000` at
`0xD8`, and an ARM branch `0xEA000000` at `0xDC` to the real crt0 at `0xE4`
(`mov r0,#0x12; msr cpsr; …`). The tag does **not** match the cartridge code
`BETE`; it is engine/template state, not a second game. Observed. The same
crt0 bytes sit at `0xC0` in a cart without the 0x24-byte multiboot area
(e.g. Car Battler Joe), which is what makes the shifted entry easy to spot.

## 2. Executive summary

Atomic Betty has a **four-portrait password system**, not a typed password and
not a button code. The screen shows four character icons; Left/Right selects a
slot, Up/Down changes the portrait, and A submits. There are exactly **eight
portraits**, so the input space is `8^4 = 4096` codes.

The validator packs the four portrait indices as a 12-bit base-8 number,

```
v = d0*512 + d1*64 + d2*8 + d3
```

and linearly searches a **21-entry u32 table** at ROM `0x087349B4`
(RAM copy `0x03004568`). Exactly **21 of the 4096 codes are accepted**; the
other 4075 produce the "Incorrect Password" screen. The table is:

| slot | value | code | meaning |
|---:|---:|---|---|
| 0 | `0x000` | Betty, Betty, Betty, Betty | default selection; training stage |
| 1 | `0x7D6` | Maximus, X-5, Chameleon, Sparky | pre-Level-2 checkpoint (unpublished) |
| 2 | `0xA21` | Gray Robot, Betty, Minimus, Red Robot | pre-Level-2 checkpoint (unpublished) |
| 3–19 | … | … | published Levels 2–18, in order |
| 20 | `0x1D1` | Betty, X-5, Chameleon, Red Robot | published Last Boss |

All 18 published codes (17 levels 2–18 plus Last Boss) are byte-exact table
entries, which validates the decoder. The published lists omit **three** valid
codes: slot 0 and the two pre-Level-2 checkpoints. Slot 0 is the screen's
default state, so pressing A on a fresh "Continue" starts the training stage;
the other two are genuine, previously unpublished level/checkpoint codes.

No button-code table, debug menu, sound test, gallery, or separate unlock-flag
system was found; the only secrets are the three unpublished password slots.
The 15 menu classes were recovered from the live menu-object table; all but
one are navigable or interstitial screens, and the 15th (`cDifficultyMenu`)
is instantiated but unreachable and its stored value is never read.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba`), Xvfb `:148`
(1024×768×24), `SDL_AUDIODRIVER=dummy`, openbox.

Default SDL keymap used throughout (verified on the first menu):

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Exact path to the password screen:

```
Title ("PRESS START")  -> Return
Main Menu              -> A on "Play"
Game Select            -> Down to "Continue", A
Enter Password         -> four portrait slots, cursor on slot 1
```

On the password screen:

* `Left`/`Right` move the highlighted slot (4 slots).
* `Up`/`Down` cycle the portrait through the 8-entry list. Up runs
  `Betty -> X-5 -> Sparky -> Gray Robot -> Minimus -> Maximus -> Chameleon ->
  Red Robot -> Betty`; Down runs the reverse.
* `A` submits the whole four-slot code; `B` returns to Game Select.
* A rejected code opens the "Incorrect Password" screen, which echoes the
  four attempted portraits; `B` returns to the entry screen with the attempt
  still selected.

Hold keys for 100–200 ms: taps shorter than a few frames are dropped.
A savestate at the password screen (mGBA `Shift+F1` saves, `F1` loads) makes
each test a few keypresses; all enumeration runs below used such a baseline
state (`internal [6,0,0,0]`, cursor slot 1), restored before every code.

The password screen's default state (fresh entry) is Betty/Betty/Betty/Betty.
Pressing A there accepts immediately.

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`; the file offset is given too
because the table was found by content search.

| File offset | ROM/RAM address | Contents |
|---:|---|---|
| `0x7349B4` | `0x087349B4` | **21 × u32 password table**, first word `0x00000000`, then the 20 codes; table ends at `0x734A08`, where the icon sprite-pointer table begins |
| — | `0x03004568` | RAM copy of the same 21 words (IWRAM); lookup base used by the validator |
| — | `0x03002D78` | four u32 selected portrait values (`d0..d3`) |
| — | `0x03002D6C` | u32: table index accepted by the validator (stage id) |
| — | `0x03002DD9` | byte: "menu finished/accepted" flag, set to 1 on A |
| — | `0x03002D68` | u32: difficulty selection written by `cDifficultyMenu` (never read) |
| — | `0x03002D9C` | 15-entry menu-object pointer table (ids 0–14) |
| — | `0x03007A78` | live `cPasswordMenu` object |
| — | `0x030045BC` | 8 icon→sprite-frame pointers (primary) |
| — | `0x030045DC` | 8 icon→sprite-frame pointers (secondary) |
| `0x5C8F8` | `0x0805C8F8` | ARM `cPasswordMenu::update` — input handling + validator call |
| `0x5C828` | `0x0805C828` | ARM packed-code lookup helper (returns index or `-1`) |
| `0x5D66C` | `0x0805D66C` | ARM menu switch #1 (`r0` = menu id) |
| `0x5E104` | `0x0805E104` | ARM menu switch #2 (same semantics) |
| `0x5D12C` | `0x0805D12C` | ARM `cNewPasswordMenu` init: unpacks `table[0x03002D6C]` into the four slots |
| `0x5D3B0` | `0x0805D3B0` | ARM `cNewPasswordMenu::update` |
| `0x5C748` | `0x0805C748` | ARM `cDifficultyMenu::update` (writes `0x03002D68`) |
| `0x73365C` etc. | — | GCC RTTI strings `13cPasswordMenu`, `22cIncorrectPasswordMenu`, `16cNewPasswordMenu`, `15cDifficultyMenu`, … |

Password menu object fields used by the handler (verified in a savestate):
`+0x10` = slot count 4, `+0x14` = current slot, `+0x50` = portrait count 8,
`+0x78` = pointer to the current slot record (36 bytes per slot).

### 4b. Menu inventory (menu-object table `0x03002D9C`)

The 15 live menu objects map to the classes and were identified by their
vtables and RTTI names:

| id | class | observed? | how reached |
|---:|---|---|---|
| 0 | `cIntroMenu` | yes | boot/attract; Start/A advances, B asks "Are you sure?" |
| 1 | `cMainMenu` | yes | Play / Options |
| 2 | `cGameMenu` | yes | Game Select (New Game / Continue) |
| 3 | `cOptionsMenu` | yes | Music / Sound / Credits |
| 4 | `cMusicMenu` | yes | On / Off |
| 5 | `cSoundMenu` | yes | On / Off |
| 6 | `cCreditsMenu` | yes | scrolling staff credits over a planet |
| 7 | `cDifficultyMenu` | **no** | **no code switches to id 7**; its output `0x03002D68` is never read |
| 8 | `cPasswordMenu` | yes | Continue / New Game → Enter Password |
| 9 | `cIncorrectPasswordMenu` | yes | any non-table code |
| 10 | `cNewPasswordMenu` | **no** | switch site at `0x08058CB8` (story/level sequencer); it is an interstitial, not a menu-graph entry |
| 11 | `cTryAgainMenu` | yes | losing all health in the space section ("Try Again? Yes/No") |
| 12 | `cSureMenu` | yes | "Are you sure?" before Exit Game |
| 13 | `cPauseMenu` | yes | plain `PAUSE` screen (no map data during a cutscene stage) |
| 14 | `cPauseMapMenu` | yes | Start in a platform stage: level map + EXIT GAME/PAUSE/CONTINUE |

Extra screens walked: the "Ship Controls" help card (after Try Again → No, in
the space section), the in-game dialogue boxes, and the level-intro cutscenes.

The two menu classes that are not in the regular navigation graph are both
accounted for: `cDifficultyMenu` is dead (no switch site, output never read),
and `cNewPasswordMenu` is an interstitial shown by the story/level sequencer
(the password-display screen between stages), called at `0x08058CB8`; no level
was completed in this session, so it is established statically plus by its
call site, not by a screenshot.

## 5. Algorithm

The whole validator is ARM code at `0x0805C8F8`. On A it builds the packed
value and runs the table search:

```python
# r4 = cPasswordMenu object
# 0x03002D78 holds the four portrait values d[0..3], each 0..7
d = [u32(0x03002D78 + 4*i) for i in range(4)]
v = d[3] + 8*(d[2] + 8*(d[1] + 8*d[0]))      # = d0*512 + d1*64 + d2*8 + d3

table = [u32(0x03004568 + 4*i) for i in range(24)]   # only 0..20 are codes
idx = -1
for i in range(24):
    if table[i] == v:
        idx = i
        break

if idx < 0:
    switch_menu(9)          # cIncorrectPasswordMenu
else:
    u32(0x03002D6C) = idx   # stage id
    u8(0x03002DD9)  = 1     # "accepted" flag
    # caller resumes the stage sequencer with this id
```

Instruction-level detail:

* Left: `index = ([this+0x14] - 1) mod [this+0x10]` (slot count 4).
* Right: `index = ([this+0x14] + 1) mod [this+0x10]`.
* Up: `d[slot] = (d[slot] - 1) mod [this+0x50]` (portrait count 8).
* Down: `d[slot] = (d[slot] + 1) mod [this+0x50]`.
* A: the packing above; search; on miss play sound and `switch_menu(9)`.
* B: play sound and `switch_menu(2)` (Game Select).
* The search loop is unrolled by 8 and bounded by `cmp r2,#23; ble`; entries
  21–23 are the icon sprite-pointer table (`0x0823986C`, `0x08239A8C`,
  `0x08239CAC`), all > `0xFFF`, so they can never equal a 12-bit code.

Encoder (used by `betty_password.py`):

```python
def encode(d): return (d[0]<<9) | (d[1]<<6) | (d[2]<<3) | d[3]
```

Decoding is the four `(v >> {9,6,3,0}) & 7` fields in the same order.

Published-label ↔ internal-value mapping (validated by the 18 published codes
matching 18 distinct table rows):

```
0 Betty      1 Red Robot   2 Chameleon   3 Maximus
4 Minimus    5 Gray Robot  6 Sparky      7 X-5
```

(The published name "Atomic Betty" in the Level 2 code is just Betty;
"The Cameleon" in the boss code is Chameleon.)

## 6. Tables

### 6a. Accepted codes (complete, 21 rows)

| idx | packed | code | stage / published label |
|---:|---:|---|---|
| 0 | `0x000` | Betty, Betty, Betty, Betty | default selection; training stage ("defeat these enemies using your kung fu") |
| 1 | `0x7D6` | Maximus, X-5, Chameleon, Sparky | unpublished checkpoint: "It was only a dream" → school stage |
| 2 | `0xA21` | Gray Robot, Betty, Minimus, Red Robot | unpublished checkpoint: "reporting for duty" → space-shooter section |
| 3 | `0x3C4` | Red Robot, X-5, Betty, Minimus | Level 2 |
| 4 | `0x56B` | Chameleon, Gray Robot, Gray Robot, Maximus | Level 3 |
| 5 | `0x87D` | Minimus, Red Robot, X-5, Gray Robot | Level 4 |
| 6 | `0x156` | Betty, Gray Robot, Chameleon, Sparky | Level 5 |
| 7 | `0x23E` | Red Robot, Betty, X-5, Sparky | Level 6 |
| 8 | `0x69F` | Maximus, Chameleon, Maximus, X-5 | Level 7 |
| 9 | `0xEDF` | X-5, Maximus, Maximus, X-5 | Level 8 |
| 10 | `0xB02` | Gray Robot, Minimus, Betty, Chameleon | Level 9 |
| 11 | `0xFCC` | X-5, X-5, Red Robot, Minimus | Level 10 |
| 12 | `0xEDD` | X-5, Maximus, Maximus, Gray Robot | Level 11 |
| 13 | `0x983` | Minimus, Sparky, Betty, Maximus | Level 12 |
| 14 | `0x082` | Betty, Chameleon, Betty, Chameleon | Level 13 |
| 15 | `0xB03` | Gray Robot, Minimus, Betty, Maximus | Level 14 |
| 16 | `0xA3A` | Gray Robot, Betty, X-5, Chameleon | Level 15 |
| 17 | `0xA93` | Gray Robot, Chameleon, Chameleon, Maximus | Level 16 |
| 18 | `0x4BB` | Chameleon, Chameleon, X-5, Maximus | Level 17 |
| 19 | `0x912` | Minimus, Minimus, Chameleon, Chameleon | Level 18 |
| 20 | `0x1D1` | Betty, X-5, Chameleon, Red Robot | Last Boss |

### Field layout

* Four fields, 3 bits each, left-to-right most-significant-first.
* Field order on screen = field order in the packed value (slot 1 is bits 9–11).
* No checksum, no parity, no reserved bits: the whole 12-bit value is the key.
* Leading Betty (value 0) is not stripped; `0x082` (Betty, Chameleon, Betty,
  Chameleon) is accepted as Level 13.
* Accepted set is a lookup table, not a formula. The table's first word is a
  real entry (`0x00000000`), not a bug: it is what makes the default
  all-Betty selection start the game.

## 6b. Enumeration

**Space.** 8 portraits per slot × 4 slots = **4096 representable codes**.
The table has **21 accepted values** (`0x000`, `0x7D6`, `0xA21`,
`0x3C4`, `0x56B`, `0x87D`, `0x156`, `0x23E`, `0x69F`, `0xEDF`, `0xB02`,
`0xFCC`, `0xEDD`, `0x983`, `0x082`, `0xB03`, `0xA3A`, `0xA93`, `0x4BB`,
`0x912`, `0x1D1`), so **4075 are rejected**. This was proven both ways:
the 21 rows were entered in mGBA and every one advanced to a cutscene/stage
(the contact sheet of `enum_00` … `enum_20`), and four non-table values were
entered and rejected.

**Novel codes (in no published list).** GameFAQs (archived copy; the live page
returns 403), SuperCheats and the CodeBreaker mirrors publish only Levels 2–18
and the Last Boss (18 codes). VGChartz has only a game entry with no password
list; TCRF could not be fetched (403) and no Atomic Betty page surfaced in
search. The following three codes are absent from every list found:

| code | packed | effect observed in mGBA |
|---|---:|---|
| Betty, Betty, Betty, Betty | `0x000` | accepted; starts the training stage ("Betty, defeat these enemies using your kung fu. Repeatedly press B to attack."). This is also the entry screen's default. |
| Maximus, X-5, Chameleon, Sparky | `0x7D6` | accepted; opens the story cutscene "Betty: It was only a dream." and continues into the school stage. |
| Gray Robot, Betty, Minimus, Red Robot | `0xA21` | accepted; opens the bridge cutscene "Betty: Atomic Betty reporting for duty Admiral!" then the space-shooter section. |

Evidence: `novel0_entry.png` / `novel0_effect.png`, `novel1_entry2.png` /
`novel1_effect2.png`, `novel2_entry.png` / `enum_02.png`. For each acceptance
the RAM state was also read from a savestate: `0x03002D6C` holds the table
index (0, 1, 2 respectively) and `0x03002DD9` = 1.

**Bounds proven by rejection.** Four codes the format can express but the
table does not contain were entered; all four produced "Incorrect Password"
and the screen echoed the attempted portraits:

| code | packed | result |
|---|---:|---|
| Betty, Betty, Betty, X-5 | `0x001` | Incorrect Password (`rej_0.png`) |
| Maximus, X-5, Chameleon, X-5 | `0x7D7` | Incorrect Password (`rej_1.png`) — one step from the valid `0x7D6` |
| X-5, X-5, X-5, X-5 | `0xFFF` | Incorrect Password (`rej_2.png`) — maximum 12-bit value |
| Red Robot, Chameleon, Maximus, Minimus | `0x29C` | Incorrect Password (`rej_3.png`) |

The `0x7D7` rejection is the strongest bound: it differs from accepted
`0x7D6` in one portrait and is still rejected, so validation is exact table
membership, not a range or prefix rule.

**Button-code / debug-menu search (bounded negative).**
* `strings -t x -n 4` over all 8 MiB: 57,108 strings. Keyword hits for
  `password|passcode|cheat|debug|secret|unlock|select|menu|code` total 19;
  all are either in-game dialogue, the credits, or C++ RTTI class names
  (`13cPasswordMenu`, `22cIncorrectPasswordMenu`, `16cNewPasswordMenu`,
  `15cDifficultyMenu`, …). There is **no** debug string, no sound-test or
  gallery label.
* The UI text is drawn from graphics, not ASCII; the visible menu labels
  ("Main Menu", "Options", "Enter Password", …) do not exist as strings.
  This is why the negative rests on the menu-object inventory and the
  validator, not on string hits.
* Button-sequence scan: every 2-byte run of 4+ values from the GBA key-mask
  set `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}` with at least three
  distinct masks was listed (38 candidates). Only one is referenced by a
  32-bit pointer, and that pointer (`0x0873415C` → `0x0805B60A0`) is a menu
  vtable entry, not a data table. No candidate has the shape of a
  prefix + action-dispatch cheat table.
* `cDifficultyMenu` is instantiated (menu object id 7, vtable `0x08733608`)
  but no `switch_menu(7)` call exists among the 21 direct call sites of
  `0x0805D66C`, nor among the indirect copy `0x0805E104`; its selected value
  `0x03002D68` is written at `0x0805C748` and never read anywhere in the ROM.
  It is dead code, not a hidden difficulty selector.

## 7. Validation evidence

**Observed (emulator / RAM):**

* Title, Main Menu, Game Select, Enter Password, Incorrect Password,
  Options, Music, Sound, Credits, Pause, Pause Map, Sure, Try Again, the
  Ship Controls help card, level intros, and the school/space stages were
  reached and screenshotted (`/tmp/opencode/betty/*.png`; not redistributed).
* The password screen cycles exactly 8 portraits in both directions; a
  savestate per stop proved the stored values are 0–7 with the mapping in
  §5 (`map0.png` … `map7.png`).
* All 21 table rows were entered; each produced a stage/cutscene rather
  than "Incorrect Password" (`enum_00` … `enum_20` contact sheet).
* Four non-table codes produced "Incorrect Password" (`rej_0` … `rej_3`).
* Savestate RAM reads: `0x03002D6C`/`0x03002DD9` after accepting slot 0,
  1 and 2 held `0`/`1`, `1`/`1`, `2`/`1`; after the published Level 2,
  Level 10, Level 18 and Last Boss codes they held `3`/`1`, `11`/`1`,
  `19`/`1` and `20`/`1`. The password-menu object's `+0x10` = 4 and
  `+0x50` = 8.
* All 18 published codes were checked in the emulator by entering them
  (the enumeration batch) and statically by table membership.

**Derived (disassembly):**

* `0x0805C8F8` is the password menu's ARM update: slot/portrait navigation,
  the base-8 packing, the 24-iteration table loop, the `switch_menu(9)` on
  miss, and the writes to `0x03002D6C` / `0x03002DD9` on hit.
* The table is 21 u32 at `0x087349B4` and its RAM copy is `0x03004568`; all
  21 words match in both places (verified against a savestate).
* `0x0805C828` is the same packing/lookup as a callable helper, used by the
  password-display initialisers (`0x0805D12C`, `0x0805D1F0`, `0x0805D2D0`)
  that unpack `table[stage]` into the four slots.
* Menu object table `0x03002D9C` has 15 live entries; vtable/typeinfo
  resolution gives the class list in §4b. `cDifficultyMenu` has no switch
  site and its output is never read.

**Inferred:**

* The slots 1 and 2 are checkpoints of the opening level sequence. The
  table order plus the published Level 2 at slot 3 implies slots 3–20 are
  Levels 2–18 + boss; slot 2 behaves like Level 1 (space section + school)
  and slot 1 like the preceding story/checkpoint. No on-screen level number
  is displayed, so the exact "Level 0/1" naming of slots 0–2 is an inference;
  the content of each slot is observed.
* `cNewPasswordMenu` is the between-stages password display (its init
  unpacks the current stage's table entry). Its call site is derived; no
  screenshot was taken because it requires finishing a level.

## 8. Unknowns

* Whether slots 1 and 2 are formally "Level 1" in the game's own numbering.
  The game displays no level number on the password or pause screens; the
  published Level 2 = slot 3 alignment is exact, but the labels for slots
  0–2 are inferred from content.
* `cNewPasswordMenu` was not captured visually. Its class, init, update and
  call site are known; reaching it requires completing a stage, which was
  not done in this session.
* The purpose of the `SHAT01` tag in the multiboot header area is not known;
  it does not match `BETE` and no second executable was found.
* Whether the three novel codes are *intended* player-facing shortcuts or
  leftovers. They are accepted by the ROM's own validator with no memory
  modification, so they are in-game codes either way.

## 9. Tooling

* `betty_password.py` (next to the ROM): reads the 21-word table at
  `0x7349B4`, decodes/encodes the four portraits, verifies all published
  codes, enumerates the 4096-code space, and reports accept/reject for a
  named code.
* `strings -t x -n 4`, `xxd`, `arm-none-eabi-objdump -D -b binary -marm
  --adjust-vma=0x08000000` (ARM mode; the menu/validator code is ARM, not
  Thumb), Python 3 `struct`/`zlib`.
* mGBA 0.10.5 SDL under Xvfb `:148` + openbox; `xdotool` for input,
  `scrot` + ImageMagick for the 720×480 viewport.
* mGBA PNG savestates: the `gbAs` chunk is zlib-compressed; decompressing it
  gives a 397,312-byte state with IWRAM at offset `0x19000`, which allowed
  reading `0x03002D6C`/`0x03002DD9`/the table without a live debugger.
  A GDB-stub run (`mgba -g`) was used once to confirm the RAM table before
  the savestate layout was known.
* All screenshots and savestates from this session are in
  `/tmp/opencode/betty/` and the game folder's `*.ss1` (git-ignored); no ROM
  or game art is redistributed here.

## Legal note

No ROM, extracted graphics, music, or game text is redistributed. This
report contains addresses, hashes, the code format, and codes generated from
the ROM's own table.
