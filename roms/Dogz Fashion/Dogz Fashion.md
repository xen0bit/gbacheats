# Dogz Fashion (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Dogz Fashion/Dogz Fashion.gba` |
| Size | 8,388,608 bytes (8 MiB, 0x800000) |
| Header title (0xA0) | `DOGZ FASHION` |
| Game code (0xAC) | `BFEE` |
| Maker code (0xB0) | `41` (Ubisoft) |
| Software version (0xBC) | 0x00 (Rev.00) |
| Complement check (0xBD) | 0x7E — **matches** the computed value (header not hand-edited) |
| Header checksum (0xBE) | 0x0000 — the usual artifact of a rebuilt header |
| Entry branch (0x00) | `EA00002E` (stock: branch to 0x080000C0) |
| Nintendo logo | standard 156-byte logo, byte-identical, at file 0x04 |
| MD5 | `6c4adc19a909f934c7c01c4f889a12d9` |
| SHA-1 | `2db620fbc629e957e8b73dd169bf83950814fd51` |
| SHA-256 | `895d57f345bc28b4ae126f53d572c24a8c5018a141a3089425801f290565e0d2` |

Embedded-header scan: searching the whole image for the 156-byte Nintendo logo
returns **one** hit, at file offset 0x04. There is no second/sub-image header, no
multiboot stub, and therefore no 2-in-1 shell. The file is the retail single image.

Patch/trainer check: entry word is the stock `EA00002E`; the crt0 at 0x080000C0 is
ordinary (`1200a0e3 00f029e1 …`), there is no cracktro, no appended trainer, and the
first 4 KiB contains no injected menu. The header checksum being 0 with a valid
complement byte matches a routinely rebuilt header, not a gameplay patch.

Build tag: `WANKO ver1.0` at file 0x1237C4 (ROM `0x081237C4`) — “wanko” = puppy,
the Japanese original is *Kawaii Koinu Wonderful* (MTO, 2004; this is the 2006
Ubisoft localisation).

## 2. Executive summary

**This ROM has no in-game code system.** There is no password screen, no
button-cheat sequence, no debug menu, and no code-driven unlockable. The only
text-entry surfaces are the player-name and dog-name keyboards, which are
8-glyph *labels*: they are stored into the save struct and are never compared
with ROM constants.

What was proven, and how:

* **Text/strings.** The dialog/help text bank (file 0x43000–0x50000, 1,160
  printable runs ≥4 chars) contains **0** occurrences of `password`, `cheat`,
  `secret`, `unlock`, `debug`, or `code` in any case, and 0 occurrences of
  `PASSWORD` as UTF-16LE. The bank is complete for dialog text (it contains the
  quiz bank, shop lines, tutorial pages, title names and the erase prompt).
  Small UI labels (“Press START!”, “New Game”, “Enter a name”, “Is this OK?”,
  the six menu names) are baked into tile graphics, so the string scan alone is
  not the proof — see the code-level checks below.
* **Input layer.** The keypad register `0x04000130` is read at exactly **one**
  code site (0x08004064), feeding one key-state struct at `0x03001E70`. That
  struct has **69 readers**, and **none** of them compares the held field (+0)
  or the pressed field (+4) against an immediate constant. A button-code
  matcher would have to do exactly that. There is no key-history buffer and no
  sequence table: a whole-ROM scan for runs of u16 single-button masks produces
  one candidate (0x3B420, Right/Left/Up/Down) which is animation/movement data
  (followed by 0xF0/0xA0 timing words and a 1-byte-per-entry table), with no
  code xref to it.
* **Name fields are labels.** After entering the name `BBBBN`, the bytes are at
  EWRAM `0x0203E920` in the emulator state (verified by decoding the mGBA
  savestate `gbAs` chunk). The 137 literal loads of that struct base were
  disassembled; the six that read bytes 0–7 and then compare do so against
  state flags (`cmp r0,#0`, `#0x14`, `#0x31`), not against ROM strings. No
  `strcmp` against a name table exists, and no table of names exists in the
  text bank.
* **Menus.** Title (single `New Game` with no save), player-name entry, dog
  select + dog-name entry, DAY card, in-house menu (Go To / Care / Tricks /
  Play / Dress Up / Save), Care submenu (Call / Give Food / Give Water / Brush /
  Bathe), food list (Dry Food / Meat / Fish, `Remaining n`), water bowl, Go To
  submenu (Get Close / My Room / Living Room / Entrance / Go for Walk). No
  entry in any of these leads to a code screen; each menu item’s own help text
  (ROM 0x08043ADC–0x08043BC4) was read and matches what the screen shows.
* **Published codes.** None exist. ChapterCheats states “No Codes, No
  Passwords, No Unlockables”; VGChartz lists one cheat, which is a
  walkthrough/tips entry; GameFAQs has guides but no cheats page (HTTP 403 to
  this session, no Wayback snapshot). The franchise’s only GBA “unlock” writeup
  belongs to the *sibling* `Dogz` (game code `B82E`): “Always Together Mode”,
  an ending reward with no input code. That string is **not** in this image
  (`together` occurs once, inside the line “We’ll be together forever”), and
  the two ROMs have different game codes and different titles, so no shared
  engine was assumed.

**Unlockables that do exist are progress-based**, not codes: nine fashion
titles plus “Regular Dog” awarded by a shop NPC (“I’ll give you titles if you
collect many fashions”), locations (Wonder Park, Dog City) opened by day count,
play items that enable the minigames, and the clothing shops. These are save
flags in EEPROM (see §4), and per the guide’s §16.18 a save-bit unlock is not a
code.

## 3. How to reproduce

Environment: mGBA (SDL) 3× scale under `Xvfb :343` (1024×768×24) + `openbox`,
`SDL_AUDIODRIVER=dummy`. Default SDL keymap: **A = `x`, B = `z`, Start =
`Return`, Select = `BackSpace`, L = `a`, R = `s`, D-pad = arrows**.

Long presses are dangerous here: the engine repeats a direction while it is
held, so a 120 ms `Down` moves two entries. All menu work below used 40–60 ms
taps with ≥0.5 s gaps.

Boot takes ~14 s (MTO logo → Ubisoft logo → title). Exact path used:

1. Title `Press START!` → **START** →
2. `New Game` (the only entry when no save exists; Down/Up change nothing)
   → **A** →
3. `Enter a name` keyboard (player): 8 slots, `A–Z`, `a–z`, `0–9` and symbols,
   `Gender` toggle, `Delete`, `OK`, then `Is this OK? Yes/No` →
4. Intro dialogue (A advances) → `Choose a dog!` → dog-name keyboard (same
   8-slot layout) → `Is this OK?` → `DAY 1` status card →
5. In the room, **A** opens the menu on the right wall: `Go To`, `Care`,
   `Tricks`, `Play`, `Dress Up`, `Save`. Moving the highlight displays that
   item’s help text; **A** advances/closes the help text and steps the
   highlight. `B` closes the menu/submenu.
6. `Care` (A) → `Call`, `Give Food`, `Give Water`, `Brush`, `Bathe`.
   `Give Food` → `Dry Food`, `Meat`, `Fish`, `Remaining 5`; `Give Water` →
   water-bowl screen with `B Stop`; `Bathe` shows `Remaining 0` at day 1.
7. `Go To` (A) → `Get Close`, `My Room`, `Living Room`, `Entrance`,
   `Go for Walk`.

**Codes tested:** none exist to test. **Button sequences tested in the
emulator** at boot and at the title: holding Select; holding `L+R+A+B`;
holding B; the Konami sequence (Up Up Down Down Left Right Left Right B A)
then START. All produced the normal title/name-entry flow. In the in-house
menu, A, B, Start, Select, L, R, Up, Down, Left and Right were all exercised;
none produced a hidden or debug screen.

**Savestates:** `Shift+F1/F2…` saved; `F1…` loaded. mGBA writes an 8 KiB
`.sav` (EEPROM, see §4); the game did not write it during this session (the
Save menu entry was never successfully activated at day 1 — see §8).

## 4. Address map

| ROM address (file offset) | Contents |
|---|---|
| `0x08004000` (0x4000) | Key-state update: builds held/released/pressed/repeat from the raw pad word |
| `0x08004064` (0x4064) | **Only** keypad wrapper: `r0=0x03001E70`, `r1=~KEYINPUT & 0x3FF`, `bl 0x08004000` |
| `0x03001E70` (RAM) | Key-state struct: `+0` held, `+2` released, `+4` pressed edge, `+6` repeat-pressed, `+8` repeat-held, `+A`/`+C` repeat timers, `+E` last-held |
| `0x08043ADC` (0x43ADC) | Generic help record (“Press the A Button to open the menu.”) |
| `0x08043B04`–`0x08043BC4` | Six 0x20-byte menu help records: Go To, Care, Tricks, Play, Dress Up, Save (each `{u32 text, 0, 0x1E34, 0x1C, fn, 0x80, 0x1E34, 1}`; Save uses `0x230` and fn `0x08013275`) |
| `0x08043E38` / `0x08043E18` / `0x08043DE0` / `0x08043DAC` / `0x08043D58` / `0x08043D38` | Help strings for Go To / Care / Tricks / Play / Dress Up / Save |
| `0x08043A14` (0x43A14) | Help/tutorial trigger table; its literal is referenced from the walker at `0x08012A20` (literal pool at 0x08012A94) |
| `0x08043C80`–`0x0804Fxxx` | Dialog/help text bank (ASCII, `/` = page break, `@nnw` = wait) |
| `0x08049960` (0x49960) | Title list: `Fashion Dogz`, `Fashion Diamond`, `Fashion Ruby`, `Fashion Sapphire`, `Fashion Topaz`, `Fashion Emerald`, `Fashion Aquamarine`, `Fashion Garnet`, `Fashion Amethyst`, `Regular Dog` |
| `0x0804CAB4` (0x4CAB4) | Records screen strings: `PlayTime`, `Clear`, `No Data`, `Register Favorite`, `Change Favorite`, `Change Clothes`, `Change Fashion`, `Select Location`, `Select Fashion` |
| `0x0804EFC0` (0x4EFC0) | `Clear save data.\nProceed?` (+ `Yes`/`No`) — title-screen erase prompt |
| `0x08123550` (0x123550) | `EEPROM_V124` — save hardware is 8 KiB EEPROM (`.sav` = 8192 bytes) |
| `0x0203E920` (RAM) | Player/save struct: `+0` name (8 bytes), `+8` gender; `0x0203E9B0` dog name (8 bytes) |
| `0x0202B0ED` (RAM, unaligned) | Tutorial/help state byte block used by the walker at 0x08012A20 |

RAM proofs (mGBA savestate, `gbAs` zlib chunk, 397,312 bytes; EWRAM at state
offset 0x21000, IWRAM at 0x19000):

* state 0x5F920 = EWRAM `0x0203E920` contained `42 42 42 42 4E 00 …` = the
  name `BBBBN` typed on the player-name keyboard; `+8` = `01` (gender).
* state 0x1AE70 = IWRAM `0x03001E70` was `0000…` at rest and
  `01 00 … 14 00 14 00 01 00` while A was held (held=0x0001, last=0x0001,
  repeat timers=0x14), confirming the struct and its field layout.

## 5. Algorithm

There is no validator to reproduce. What the ROM does with input is a plain
polled pad decoder; its exact behaviour is:

```
raw   = *(u16*)0x04000130            // active low
state = 0x03001E70
held  = (~raw) & 0x03FF
state->released = state->held & ~held
state->pressed  = held & ~state->held
if held != state->last:
    state->last = held
    state->repeat_held = held
    state->repeat_pressed = state->pressed
    state->timerA = state->timerB = 24
else if state->timerA == 0:
    state->repeat_pressed = held          // first auto-repeat after 24 frames
    state->timerA = 6
else if state->timerB == 0:
    state->repeat_held = held
    state->timerB = 1
state->timerA--; state->timerB--
```

The name keyboard writes glyph indices into `0x0203E920[0..7]` (8 slots); no
other code path reads those bytes except the renderer and the save copy. The
gender byte (`+8`) has the same shape. Therefore the “code space” of both text
fields is a label space: it cannot accept or reject anything.

The only “accept/reject” pair in the game that involves user text is the
name-entry `Is this OK? Yes/No` confirmation, which accepts any glyph string
(including the empty string — with an empty name the game falls back to the
built-in names Mio/Chappy; observed).

## 6. Tables

**Button masks (raw pad word, active-high after XOR with 0x3FF):**
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200`.

**In-house menu (6 entries, ROM order = screen order):**

| # | Entry | Help string address | Trigger/effect |
|---|---|---|---|
| 0 | Go To | 0x08043E38 | opens location submenu |
| 1 | Care | 0x08043E18 | opens care submenu |
| 2 | Tricks | 0x08043DE0 | shows learned tricks (none at day 1) |
| 3 | Play | 0x08043DAC | requires a play item (“Play can be used once you have found a play item.”) |
| 4 | Dress Up | 0x08043D58 | dress-up/fashion menu (“Change Clothes”, “Change Fashion”) |
| 5 | Save | 0x08043D38 | save to EEPROM slot (“Save clear data. Select save spot.”) |

**Care submenu (5):** Call, Give Food, Give Water, Brush, Bathe.
Give Food list: Dry Food, Meat, Fish + `Remaining n`; Give Water: bowl screen
with `B Stop`; Brush/Bathe show `Remaining n` (0 at day 1).

**Go To submenu (5):** Get Close, My Room, Living Room, Entrance, Go for Walk.

**Titles (unlockables, 10):** Regular Dog, Fashion Dogz, Fashion Diamond,
Fashion Ruby, Fashion Sapphire, Fashion Topaz, Fashion Emerald, Fashion
Aquamarine, Fashion Garnet, Fashion Amethyst. Awarded by the fashion shop NPC
for collecting fashions.

**Name keyboard:** 8 slots; 5×7 left block (upper case + digits/punctuation),
5×7 right block (lower case + symbols), so ≈70 glyphs; `Gender` toggles
Girl/Boy; `Delete` removes the last glyph; `OK` → `Is this OK? Yes/No`.

**Minigames (unlocked by play items):** bone grab (time limit, avoid balls),
pair matching, meteor/UFO item recovery, falling-floor (“Iron squares never
fall…”), meat-to-goal — five descriptions at 0x0804D61C–0x0804D802, entered via
`Play` after the item is found.

## 6b. Enumeration

**Space definition.** Code/password space = ∅. Alphabet(s) = ∅, length(s) = ∅,
field widths = none, checksum = none. Number of representable *valid codes*:
**0**. There is no table of accepted strings and no generator/decoder pair, so
there is nothing to invert.

What was enumerated instead, with the size of each space stated:

| Surface | Size | How bounded |
|---|---|---|
| Dialog/help text bank | 1,160 printable runs (≥4 chars) in 0x43000–0x50000 | `strings` sweep; 0 hits for password/cheat/secret/unlock/debug/code (case-insensitive), 0 for UTF-16LE `PASSWORD` |
| Fixed 8-char ASCII records (password-table shape) | 342 whole-token matches, every one inside graphics/misaligned data | token scan; none in the text bank, none NUL-padded and pointer-referenced |
| Keypad read sites | 1 (0x08004064) | literal 0x04000130 search + PC-relative LDR check; the other three literal occurrences are unaligned graphic bytes |
| Key-state readers | 69 | literal 0x03001E70 search + LDR check |
| Readers comparing held(+0)/pressed(+4) to a constant | **0** | capstone scan of ±8 instructions around every reader |
| Button-sequence tables | 0 | u16 runs of single-button masks over the whole ROM; the one 16-entry run at 0x3B420 is movement/animation data (no xref) |
| In-house menu entries | 6 | on-screen walk + help-record table at 0x08043B04 |
| Care entries | 5 | on-screen walk |
| Go To entries | 5 | on-screen walk |
| Player-name space | 8 slots × ≈70 glyphs = 70^8 ≈ 5.76×10^14 strings | 8-slot field observed; not a validator (no comparison in ROM) |
| Dog-name space | same | same |
| Gender | 2 | toggled on screen |
| Titles | 10 | string table at 0x08049960 + NPC text |
| Minigames | 5 | description strings + `Play` gate |

**Novel code.** None can be minted, because the accepted set is empty. This is
the “no system” case of §16.3 (no table, no validator, no input surface), not a
dead, cut, or gated feature:

* *Dead code?* No unreferenced code-entry screen: the six menu records are the
  complete help-record set and all six labels appear on screen.
* *Cut feature?* No placeholder/localisation markers (`TEMP`, etc.) anywhere in
  the text bank.
* *Gated feature?* The only gates found (Play/Tricks/Dress Up/Save) are gameplay
  menus gated by items/tricks/clothes/save-spot, and their own help strings say
  so; none gates a code screen.

**Bounds proven by rejection.** Because there is no validator there is no
accept/reject pair to test; the analogous bound is the input-cap: the name
keyboard exposes exactly **8 slots** and the field stops accepting glyphs once
they are full (confirmed visually on the 8-underscore field and by the cursor
advancing through all eight). An empty name is accepted and the game substitutes
its built-in names. Both are recorded as observations, not as a code verdict.

## 7. Validation evidence

**Observed (emulator):**

* Title → single `New Game` entry; START enters name entry. Down/Up on the
  title menu changes nothing.
* Player-name and dog-name keyboards: 8 slots, upper/lower/digits/symbols,
  gender toggle, Delete, OK, `Is this OK? Yes/No`; empty name accepted with
  default names.
* DAY 1 card (name/gender/breed/love level), room HUD with clock and hearts.
* In-house menu with the six entries and their help pages (screenshots
  38/43/44/54/55).
* Care submenu and its three action screens (food list with `Remaining 5`,
  water bowl with `B Stop`, `Remaining 0` for Bathe).
* Go To submenu.
* Boot button tests (Select, L+R+A+B, B, Konami at title) all reach the normal
  title; Select at the title menu does nothing.
* Name bytes at EWRAM 0x0203E920 and key struct at 0x03001E70 (savestate RAM
  reads, §4).

**Derived (static):**

* Single keypad read site; key-state layout and repeat algorithm (§5).
* 0/69 key-state readers compare a button bit to a constant.
* No button-sequence table; no code/name table; 0 password-vocabulary hits.
* Six-entry help-record table = the menu; title table; EEPROM save marker.

**Inferred (not fully exercised):**

* `Dress Up` opens a fashion menu with `Change Clothes`/`Change Fashion` and
  `Select Location`/`Select Fashion` (strings at 0x0804CAF8–0x0804CB28) — the
  entry label and help text are confirmed, the sub-menu was not reached at
  day 1 (no fashion items owned).
* `Save` writes an EEPROM slot at a save spot (“Select save spot.”); no save
  was produced in this session, so the slot UI was not seen.
* `PlayTime`/`Clear`/`No Data`/`Register Favorite`/`Change Favorite` belong to
  the dog-select/favourites screen (link-cable favourites); not reached without
  save data.
* Title-screen `Continue` and `Clear save data.` entries appear only when a
  save exists; only the erase-prompt string is ASCII in the ROM.

## 8. Unknowns

* The dress-up sub-menu’s exact entry list was not seen at day 1; its strings
  are present, and the entry behaves as a no-op at that state (help text only).
* Save-slot count and the save-spot rule were not exercised (no save written);
  `Save clear data. Select save spot.` implies ≥1 slot, and the erase prompt
  implies ≥1 save block.
* The favourites/`PlayTime` screen needs save data or a link partner.
* Whether any *day-gated* shop NPC awards an extra title beyond the ten in the
  table is not proven; the table lists ten and the NPC line says titles are
  given for collecting fashions.

## 9. Tooling

* `mgba` (SDL) under `Xvfb :343` + `openbox`, `xdotool`, `scrot`/`import`.
* `arm-none-eabi-objdump -M force-thumb` for the input wrapper and menu/help
  code.
* Python 3 + `capstone` scripts: literal/LDR scan, BL-frequency scan,
  key-state reader classification, u16 button-mask run scan, mGBA `.ss*`
  `gbAs` chunk extraction (`ss.py`) for RAM proofs.
* `strings -t x`, `grep -abo`, custom ASCII/token scans.
* No ROM assets are reproduced in this report.

## 10. Legal note

No ROM, graphics, music or text assets are redistributed. Addresses, hashes,
algorithm description and our own test notes only.
