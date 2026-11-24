# Disney's Princess Royal Adventure (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Disney's Princess Royal Adventure.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title (0xA0) | `PRINCESSTOWN` |
| Game code (0xAC) | `BQNE` (USA) |
| Maker code (0xB0) | `4Q` |
| Version (0xBC) | 0 |
| Entry word | `0xEA00002E` (stock ARM branch to 0x080000C0) |
| Fixed byte 0xB2 | `0x96` |
| Complement (0xBD) | `0xF7` (valid; computed `0xF7`) |
| Header checksum (0xBE) | `0x0000` (computed `0xF9F7`; normal rebuilt-header artifact — see §16.1) |
| MD5 | `76cdc3ec8b886f378ebc6de368399220` |
| SHA-1 | `a033a92eab635c035444b2165fe04631aa3bb118` |
| SHA-256 | `c9f67fbf3853fd0dea9e656118ff4cd29731547b093dd1360b8b9ccd257aaf7d` |
| CRC32 | `0xC6AD2251` |

**Phase 0 structural scan.** The standard 156-byte Nintendo logo occurs exactly once
(file `0x04`), so this is a single GBA image, not a multi-game pack. The entry
branch, logo, fixed `0x96`, complement and title all match a normal retail
build. No cracktro, appended trainer, or entry patch was found. The header
checksum field is zero and the complement is valid, the documented signature of
a header that was rebuilt without redoing the checksum field.

## 2. Executive summary

**There is no in-game password, button-code, hidden debug menu, or
developer cheat in this USA build.** The game's entire content — six
princess cutscene sets, six minigames with four difficulty modes, intro and
ending — is unlocked by story progress and stored in a three-slot save file.
Nothing is entered as a code. There is no chapter/level select; the story is
continuous and the only content hub is `Extras`.

The evidence is both dynamic and static:

* All title/menu/options/extras/pause screens were walked on :336 (screenshots
  taken at every transition). The only selectable surfaces are fixed menu
  lists; there is no text-entry or password screen anywhere.
* The 988-entry UI string table contains no `PASSWORD`, `CHEAT`, `DEBUG`,
  `CODE`, `LEVEL`, `MENU`, `SELECT`, or `TEST` string in ASCII, uppercase,
  lowercase, UTF-16LE or UTF-16BE (0 hits each across all 8 MiB).
* The keypad module (`0x08008290`) stores only three per-frame words —
  pressed `0x030042C0`, stable `0x030042C2`, raw current `0x030042C4` —
  and the key-test helpers accept a single 16-bit mask. There is no press
  history, sequence index, or mask table. A 10-press Konami-shaped sequence
  left no trace in a 397,312-byte savestate, and no key comparison uses a
  multi-button chord.
* Published codes for this title are **CodeBreaker device codes for the
  Europe SKU `BQNP`**, not in-game passwords, and the target here is the USA
  SKU `BQNE`. They are outside the requested scope and cannot be typed into
  the game.
* Unlockables are real but are save flags set by story scripts. The six
  minigames, their four difficulty levels, the six cutscene sets, Intro and
  Ending form the complete list; locked entries are skipped by the menu
  (verified) and no controller input sets them.
* A localization leftover is visible: the USA text table still contains
  `Language`, `English`, `Deutsch`, `Français`, `Italiano`, `Español`, but
  the USA Options menu exposes only Music/Sound/Credits. This is a cut
  feature, not a cheat.

Because there is no code space, no novel code exists to mint. §6b below
defines the absence precisely and records the rejected/bounded tests.

## 3. How to reproduce

### Emulator and keymap

```bash
Xvfb :336 -screen 0 1024x768x24 &
DISPLAY=:336 openbox &
cd /path/to/rom
DISPLAY=:336 SDL_AUDIODRIVER=dummy mgba -3 "Disney's Princess Royal Adventure.gba" &
```

mGBA SDL default keymap used:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |
| L / R | `a` / `s` |
| Save state | `Shift+F1` … `Shift+F10` |
| Load state | `F1` … `F10` |

Hold keys 100–300 ms. Screenshots were taken with
`import -window root` and cropped `720x480+152+144`.

### Menu path (fresh save)

1. Boot → Nintendo logo → Human Soft splash → **Press START**.
2. `Start` → main menu: **New Game / Load Game / Options / Extras**.
3. `Load Game` → three empty slots (`Empty` ×3).
4. `Options` → **Music On/Off, Sound On/Off, Credits** (only these three rows;
   Left/Right do nothing on them).
5. `Extras` → **Minigames, Intro, Cutscenes, Ending**; `Ending` is dim.
6. `Extras → Minigames` → **Pairs, Clothes, Melody, Potion, Mosaic, Treasure**;
   on a fresh save Pairs is only the highlight (A does nothing), the other rows
   are dim, and Down/Up do not move off Pairs.
7. `Extras → Cutscenes` → **Aurora, Jasmine, Cinderella, Ariel, Belle,
   Snow White**; all dim, Down/A do not move/activate.
8. In game, `Start` → **Continue / Save Game / Quit**; `Save Game` shows the
   three slots and writes a 512-byte `.sav`.

Language selection never appears on a first boot with a deleted `.sav`; the
USA build boots directly to the English title screen.

### Tests actually run

* 10-press title sequence `Up Up Down Down Left Right Left Right B A`
  (followed by a savestate): no screen change and no sequence in RAM.
* Title chords: `Select`, `L+R`, `L+R+Start`, `A+B+Start`, `Up Up Down Down`,
  `Start+A`, `Start+B`, `Select+Start`, `B+Start`, `L+R+Start+Select`.
  Only Start or Select+Start entered the main menu; no hidden screen.
* Locked menus: `Down`/`A` on Clothes and Aurora did nothing (skipped/locked).
* Start held: RAM `0x030042C4 = 0x0008`; released: `0x0000`.

## 4. Address map

| Address / offset | Meaning |
|---|---|
| `0x000000`–`0x0000BF` | GBA header (logo at 0x04, title 0xA0, code 0xAC) |
| `0x0000C0` | ARM entry, switches to Thumb at `0x0000E0` |
| `0x08008254` | generic dispatch helper (swap function pointer) |
| `0x08008290` | **joypad update**: reads `0x04000130`, writes 3 state words |
| `0x080082BC` | literal pool: `0x04000130` (KEYINPUT) |
| `0x080082C0` / `C4` / `C8` | literals `0x030042C4`, `0x030042C0`, `0x030042C2` |
| `0x030042C0` | **pressed this frame** (active-high edges) |
| `0x030042C2` | **stable held** (`raw & previous`) |
| `0x030042C4` | **raw current keys** (active-high; 0 = none) |
| `0x080082D4` | `held(mask)`: `(raw & mask) == mask` |
| `0x080082F4` | `not pressed this frame` variant |
| `0x08008314` | `pressed(mask)`: `(pressed & mask) == mask` |
| `0x08008334` | `stable held(mask)` |
| `0x08008354` | `any held(mask)` |
| `0x08008368` | pressed/raw helper variants |
| file `0x230984` | 988-entry text pointer table (`u32` ROM pointers), ends `0x2318F0` |
| file `0x23044A`–`0x23064D` | UI/menu label cluster |
| file `0x2304B8`–`0x2304F3` | `English Deutsch Français Italiano Español Language English` (USA-cut) |
| file `0x2C4F0` | 16-bit sine/cosine table; its ASCII bytes look like `?ADGILNQSUXZ` |
| `.sav` `0x00`, `0x40`, `0x80` | three 0x40-byte save-slot records (512-byte .sav = 4 Kbit EEPROM footprint) |

## 5. Algorithm

### 5.1 No password/code validator

No function in the image consumes a player-entered string. The text system
reads `u32` pointers from the table at `0x230984` and draws fixed strings; the
only player input paths are the joypad helpers above and fixed menu selection.
There is no on-screen keyboard, keypad, name entry, or `strcmp`-style
comparison against a user buffer.

### 5.2 Joypad model (reimplemented)

```python
KEYINPUT = 0x04000130   # active low: 0 bit = pressed

def update(raw_hw, old_active):        # old_active = 0x030042C4
    raw_new = 0x3FF & ~raw_hw          # active-high current
    pressed = 0x3FF & ~(raw_hw | raw_prev_hw)  # newly pressed edge
    stable  = raw_new & old_active     # debounced held
    # state words: 0x030042C0 = pressed, 0x030042C2 = stable,
    #              0x030042C4 = raw_new
```

The helpers are one-shot mask tests, equivalent to:

```python
def held(mask):      return (raw & mask) == mask
def pressed(mask):   return (pressed_word & mask) == mask
```

There is no `history[]`, index, timer, or table of expected presses.

### 5.3 Unlock model

Unlock state is save data, not input. Each Extras row is tested against a
story-written save flag and is either drawn/dim or included/excluded from the
selection ring. Locked rows are not merely disabled-looking: Down/Up and A
have no effect on them, so the gate is in the menu logic, not just colour.
The exact save-byte offsets of each flag were not isolated (see §8); the
observable gate and the published unlock conditions are recorded in §6.

## 6. Tables

### 6.1 Complete Extras / menu inventory

| Menu | Entries | Gate |
|---|---|---|
| Main | New Game, Load Game, Options, Extras | none |
| Options | Music On/Off, Sound On/Off, Credits | none |
| Extras | Minigames, Intro, Cutscenes, Ending | Ending after story completion |
| Minigames | Pairs, Clothes, Melody, Potion, Mosaic, Treasure | each unlocked when introduced in the story |
| Cutscenes | Aurora, Jasmine, Cinderella, Ariel, Belle, Snow White | each unlocked when its scenes are seen |
| Pause | Continue, Save Game, Quit | in game |
| Save slots | Saved Game 1, 2, 3 / Empty | 3 fixed slots |

### 6.2 Minigame difficulty table

| Mode | Unlock |
|---|---|
| Tutorial | always with the minigame |
| Easy | always with the minigame |
| Medium | after the Princess Aurora section |
| Hard | after the Princess Cinderella section |

This matches the published 3rd party cheat index walkthrough ("Medium is accessed after
completing the Princess Aurora section; Hard is accessed after completing the
Princess Cinderella section"). The labels `Tutorial Easy Medium Hard` are text
IDs 970, 924, 937, 927.

### 6.3 Published codes (all device codes, not in-game)

3rd party cheat indexes and the cheats.fandom CodeBreaker
page list only CodeBreaker codes, and 3rd party cheat indexes identify them for
**Europe `AGB-BQNP`**. a 3rd party cheat index's cheats page for the game reports
"Total cheats available: 0 / No cheats available for this game"; 3rd party cheat indexes have no
indexed page for this title (the site returned 403 to automated fetches, and
search snippets show no article).

Published device codes found:

```
Master: 9188FAEE661C  E5C5389EEDE2  30876C9BC743
Access All Cutscenes: 801E4B47 AF07
Access All Minigames: C7DA48C3 9902
Access Ending:        815A5143 BD86
Stop Timer:           913C83C3 E9AA / 807A89C7 BB83
```

The target here is `BQNE` (USA), not `BQNP` (Europe); no in-game entry screen
exists for any of these. Their 8-hex-digit prefixes (`801E4B47`, `C7DA48C3`,
`815A5143`, `9188FAEE`) have **0 ASCII occurrences** in the 8 MiB image, as
expected for device-side encrypted codes with no in-game equivalent. They are
recorded as published evidence that the unlocks are memory flags, not as
usable cheats.

### 6.4 USA-cut language strings

`Language` (ID 934) and the five language names (IDs 929–933, plus a second
`English` at 935) are present in the table but the USA Options menu has only
three rows. The Europe SKU (`BQNP`) is the localized
build; the strings are a leftover in the USA image.

## 6b. Enumeration

### 6b.1 Space definition — there is no code space

| Property | Result |
|---|---|
| Input alphabet | ∅ (no code entry surface) |
| Length(s) | 0 |
| Checksum | none |
| Code table | none |
| Representable code values | **0** |
| On-screen keyboard / keypad | absent (0 keyboard/name strings) |
| Password/cheat/debug strings (ASCII, UPPER, lower, UTF-16LE/BE) | **0 each** |

The full UI vocabulary is 988 strings (file `0x230984` table). Every one is
story dialogue, a menu label, a tutorial sentence, or a fixed confirmation.
The word `secret` occurs 38 times and `unlock` 4 times, but every occurrence is
story prose (secret passage, unlock the gate), not a code instruction.

### 6b.2 Button-sequence space

The game's complete input representation is the three per-frame words at
`0x030042C0/C2/C4`. The ten buttons give 1,024 single-frame chords; only
Start (title), A/B (menus), D-pad (menus) and the four face/shoulder buttons
during minigames are consumed. A multi-press code would require a stored
history; none exists:

* A 10-press sequence `Up Up Down Down Left Right Left Right B A` was entered
  on the title screen, then the state was saved. Searching the 397,312-byte
  state for the sequence as `u16` active-high, `u16` active-low, `u8` masks or
  `u8` button indices found **0 hits** in IWRAM and EWRAM.
* All 4,194,304 halfword positions were scanned for Thumb `LDR` literal
  targets beginning with ≥3 button masks. Exactly **2** targets matched:
  `0x08010A08` (actually the 32-bit timing constants `0x00100080` /
  `0x00200080`) and `0x082AC348` (compressed graphics). Neither is a table.
* 47 LDR literals whose 32-bit value happens to be a 2–4 button chord were
  listed; the sampled sites are counts/geometry constants, not key tests.
* 172 static call sites of the key-test helpers were found (39 raw-held,
  132 pressed, 1 any-held); each passes a single mask. No caller passes a
  sequence pointer or length.

**Bounds by rejection:** the candidate multi-press space is not
representable at all; the only representable surface is a single chord, and
the 10 probes listed in §3 produced no state change except Start. Locked menu
rows reject A/Up/Down outright.

### 6b.3 Unlockable content space (the only enumerated state space)

| Class | Count | Detail |
|---|---|---|
| Minigames | 6 | Pairs, Clothes, Melody, Potion, Mosaic, Treasure |
| Minigame modes | 4 each | Tutorial, Easy, Medium, Hard → 24 combinations; Medium gated on Aurora, Hard on Cinderella |
| Cutscene sets | 6 | Aurora, Jasmine, Cinderella, Ariel, Belle, Snow White; two pictures per princess per the guide |
| Intro | 1 | available immediately |
| Ending | 1 | after story completion |
| **Total content units** | **38** | 6×4 + 6 + 1 + 1 |

None of these is reachable by a code. The fresh-save menu shows the gate:
Minigames highlights Pairs only (A does nothing; the other rows are dim and
Down stays on Pairs), Cutscenes has all six names dim (Down/A do nothing), and
Ending is dim. Intro plays.

### 6b.4 Novel code

**None exists.** There is no validator to invert, no alphabet to enumerate,
and no accepted input to mint. The correct deliverable is the bounded negative
above, not a fabricated code.

## 7. Validation evidence

### Observed (emulator, :336)

* Title screen "Press START"; main menu with four entries; Load Game with
  three `Empty` slots; Options with three entries; Extras with four entries
  (Ending dim); Minigames with six rows (Pairs is the only highlight and A has
  no effect; the rest are dim); Cutscenes with six dim names;
  pause with Continue/Save Game/Quit; save writes a 512-byte `.sav`.
* Fresh boot with `.sav` deleted still skips language selection and goes to
  the English title.
* Locked rows: Down/A on Clothes and Aurora do nothing.
* RAM: `0x030042C4 = 0x0008` while Start is held, `0x0000` released. This is
  the raw-active-high key word used by helper `0x080082D4`.
* 10-press sequence produced no screen change; savestate search found no
  sequence copy.

### Derived (instruction/data analysis)

* Input module at `0x08008290` writes exactly three words; helpers are
  one-mask tests; no history buffer.
* Text table at `0x230984` has 988 entries and contains no code/debug
  vocabulary; the UI cluster includes cut language strings.
* The `?ADGILNQSUXZ`-looking bytes at file `0x2C501` are the ASCII rendering
  of a 16-bit sine table at `0x2C4F0`, not a password alphabet.
* No Thumb LDR references a button-mask table; the two apparent hits are
  timing constants and compressed graphics.

### Inferred

* The USA build's language strings are a shared-code leftover from the
  Europe `BQNP` build (the published codes and serial confirm the EU SKU).
* Unlock flags live in the 0x40-byte save records; their exact bit offsets
  were not isolated.

## 8. Unknowns

* Exact save-byte offsets for each minigame/cutscene/ending flag. The save is
  a 512-byte EEPROM image with three 0x40-byte slots and a checksum-like
  prefix; a played-to-completion save would be needed to diff each flag.
* Whether the Europe `BQNP` build's language menu is the only difference in
  the Extras/Options code. Not tested (different ROM).
* No claim is made about debug builds, prototypes, or the Europe revision;
  only the USA `BQNE` image above was analysed.

## 9. Tooling

* `binutils-arm-none-eabi` (`objdump -M force-thumb`), Capstone 5.0.7.
* Python 3 scripts used locally:
  * `phase0.py` — hashes, header/complement, embedded-logo scan.
  * `ptrscan.py` / text-table dump — 988-entry `u32` pointer table, strings.
  * `blscan.py` — Thumb `BL` target counts for the key helpers.
  * LDR-literal mask-table scanner, multi-button-literal scanner, alphabet
    scanner (inline Python; outputs reproduced in §6b).
  * mGBA `.ssN` parser: PNG `gbAs` chunk → zlib → 397,312-byte state;
    IWRAM at `0x19000`, EWRAM at `0x21000`.
* mGBA SDL, Xvfb `:336`, openbox, xdotool, ImageMagick `import`.

## Legal note

No ROM, extracted graphics, audio, or copyrighted text is redistributed in
this report. Addresses, counts, hashes, menu structure, and the negative
result are the findings.
