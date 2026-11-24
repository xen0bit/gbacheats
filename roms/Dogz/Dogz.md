# Dogz (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Dogz/Dogz.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title (`0xA0`) | `DOGZ` |
| Game code (`0xAC`) | `B82E` |
| Maker code (`0xB0`) | `41` (Ubisoft) |
| Software version (`0xBC`) | `0x00` (Rev.00) |
| Complement check (`0xBD`) | `0xC7` — matches the computed value |
| Header checksum (`0xBE`) | `0x0000` — the usual artifact of a rebuilt header |
| Entry branch (`0x00`) | `EA00002E` (stock: branch to `0x080000C0`) |
| Nintendo logo | standard 156-byte logo, byte-identical, at file `0x04` |
| MD5 | `3981044ebb25a3db6b6f5da9725e4f4e` |
| SHA-1 | `462f05c18534cb22fffc65d47351a29f10a3f254` |
| SHA-256 | `75a52a3b58b997890a1b31217a15da464430862498e05d40bfca5837310601e1` |

Embedded-header scan: searching the whole image for the 156-byte Nintendo logo
returns **one** hit, at file offset `0x04`. There is no second/sub-image header,
no multiboot stub, and no 2-in-1 shell.

Patch/trainer check: entry word is the stock `EA00002E`; the crt0 at
`0x080000C0` is ordinary and there is no cracktro or appended trainer in the
first 4 KiB. `EEPROM_V124` is at file `0x22A884`; the save hardware is EEPROM.

The image is the retail US single build (`B82E`, 2004 MTO/Ubisoft).

## 2. Executive summary

**This ROM has no in-game code system.** There is no password screen, no button
cheat sequence, no code-driven unlockable, and no reachable debug menu. The only
"unlockable" in the published lists, **Always Together Mode**, is an ending
reward stored as a save flag, not a code; **Puppy Visiting Mode** is the GBA
Link mode. The published lists (3rd party cheat indexes) contain
those two modes and no passwords.

What was proven, and how:

* **Text.** The dialogue/tutorial bank at file `0x2F000–0x33000` is a 16-bit
  glyph-code text bank (not ASCII). A decoder was recovered from a dynamic
  plaintext pair (`I'M IN THE THIRD GRADE.` captured from the message VM) and
  then used to decode the whole image: 14,077 printable runs. The dialogue
  bank contains **0** occurrences of `PASSWORD`, `PASSCODE`, `CHEAT`, `DEBUG`,
  `SECRET`, `UNLOCK`, `CODE` or `ITEM` in the game's own encoding. The same words are also
  absent as ASCII, `+0x20`-shifted ASCII, single-byte XOR/ADD transforms, and
  UTF-16LE/BE anywhere in the 8 MiB image.
* **Input layer.** The keypad register `0x04000130` is read at exactly **one**
  site (`0x0807D82C`). It feeds a 4-field key state at `0x03004EE8` (held,
  pressed edge, repeat, timer). There is no press-history buffer and no
  sequence matcher: all 243 references to the key state are single-frame
  menu/navigation tests. A whole-ROM scan for runs of single-button masks found
  1,345 runs, of which only 14 have any ROM pointer; all 14 are data tables
  (bit masks, NPC paths, timer tables), none referenced by input code.
* **Menus.** The title ring is exactly five entries: `New Game`, `Continue`,
  `Always Together Mode`, `Puppy Visiting Mode`, `Settings`. With no save,
  `Continue`, `Always Together` and `Puppy Visiting` are greyed and `Settings`
  answers `NOT YET AVAILABLE`. The published FAQ confirms `Settings` only
  changes the movement type; the ROM contains the matching strings
  `CHANGE THE MOVEMENT OPTION.` / `MOVEMENT OPTION HAS BEEN SET.` at
  `0x0802E746`/`0x0802E75C` (and `0x0802E7EC`). There is no item-select or pause
  code surface: **Start is not a pause button** (pressed in the free-roam pet
  shop, no menu), and the only selection screens are gender/colour, the 8-slot
  name keyboard, the `Puppy Survey`, and the `PUPPY` table.
* **Hidden screen.** A developer **SOUND TEST** screen exists at screen index 0:
  string block `0x080830D0`, 17-entry table `0x0808327C`, handler
  `0x0800070C`/`0x08000634`. It lists `SOUND TEST`, `FLOOR`, `FLOOR CONTROL`,
  `TAKE WALK`, `REVERSY`, `QUIZ`, `ACTION`, `MAIN MENU`, `SHOP`, `MORNING`,
  `ENDING`, `EXTRA ENDING`, `STATUS`, `BREAKFAST`, `DINNER`,
  `LIVING WITH A PUPPY`, `DELETE SAVE`. It is **not reachable by any input**:
  the screen-dispatch byte is initialized to 4 at boot; the direct constant
  stores resolved by the literal-pointer scan write 1–27, and no input path was
  found that writes 0. It was invoked for evidence by writing the screen/mode
  bytes with the debugger, and is labeled as such in §7.
* **Sibling build.** `Dogz Fashion` (`BFEE`) is a different build with an ASCII
  text bank and no code system either. The two share the franchise concepts
  (Always Together, Puppy Visiting) but not a code system; this build has an
  unreachable sound-test screen, which the Fashion report did not find.

## 3. How to reproduce

Environment: mGBA 0.10.5 (SDL) 3× scale under `Xvfb :344` (1024×768×24) +
`openbox`, `SDL_AUDIODRIVER=dummy`. Default SDL keymap: **A = `x`, B = `z`,
Start = `Return`, Select = `BackSpace`, L = `a`, R = `s`, D-pad = arrows**.
Screen transitions take seconds; hold keys 80–150 ms and re-screenshot.

Exact path used:

1. Boot: MTO logo → Ubisoft logo → `Life with Puppy` → attract mode → title.
2. `PUSH START` → **START** → main menu ring:
   `New Game` → `Continue` → `Always Together Mode` → `Puppy Visiting Mode` →
   `Settings` → wraps to `New Game`. Highlighting a gated entry shows
   `NOT YET AVAILABLE.`; **A** on a gated entry does nothing.
3. `New Game` → **A** → `Which Are you?` (Girl/Boy, Color, Change, OK, Back) →
   **A** → `What's Your Name?` keyboard (8 glyph slots, `A–Z`, `OK`, `Move`,
   `Back`) → OK → `Is this okay?` (Yes/No) → `Puppy Survey`
   (`WHAT KIND OF DOG DO YOU LIKE? ENERGETIC/RELAXED`,
   `WHAT SIZE OF DOG DO YOU PREFER? SMALL/LARGE`, result `RELAXED / FEMALE /
   SMALL`) → `Life with Puppy` → pet-shop intro dialogue (`Mom`, `Dad`,
   `Clerk`) → `PUPPY` selection table → free-roam pet-shop room with HUD
   `WALK / CALL / START / B`.
4. Button tests at boot, at `PUSH START`, and on the main menu: Select held,
   `L+R+Start`, `Select+Start`, the Konami sequence
   (Up Up Down Down Left Right Left Right B A), and `A+B+Select+Start`.
   The Konami sequence is consumed by menu navigation (B closes the menu);
   `A+B+Select+Start` performs the engine's soft reset (observed: returns to
   the MTO copyright screen); nothing opens a code or debug screen.
5. Debug sound test (evidence only, not an in-game path): load a savestate at
   any screen, write `0x03000D64 = 0` and `0x03002CC0 = 0`, continue. The
   screen displays `SOUND TEST 000`; Down changes the track label (observed
   `ENDING 000`) and A is the select input.

**Codes tested:** there are none to test. The published lists were checked:
3rd party cheat indexes `Dogz (GBA) → Cheats` has a single Unlockables entry (`Always Together
Mode: get the best ending`); 3rd party cheat indexes repeat the
same; 3rd party cheat indexes' full FAQ lists no codes and says `Settings` only changes the
movement type. The literal `Always Together` is not a code string anywhere in
the image (0 hits in every encoding checked).

Savestates: `Shift+F1…F4` saved, `F1…F4` loaded. mGBA writes a 512-byte
`Dogz.sav`; the game did not write a real save during this session (no save
point was reached).

## 4. Address map

| ROM address (file offset) | Contents |
|---|---|
| `0x0807D82C` (`0x7D82C`) | Keypad update: reads `0x04000130`, builds held/pressed/repeat |
| `0x0807D864` (`0x7D864`) | Literal `0x04000130` (the only KEYINPUT read) |
| `0x03004EE8` (RAM) | Key state: `+0` held, `+4` pressed edge (`u16` each) |
| `0x03004EF0` / `0x03004EF4` (RAM) | Repeat timer / repeat-held word |
| `0x0807D880` | `(held & 0xF) == 0xF` → soft reset (`A+B+Select+Start`) |
| `0x0807B9FC` / `0x0807B9xx` | Message-box / text setup |
| `0x0807BDE8` | Message VM step: `u16` opcode at `[obj+0x38]`; `<0x8000` = glyph, `>=0x8000` = control |
| `0x0802F000–0x08033000` | Dialogue/tutorial glyph-code text bank |
| `0x080830D0` (`0x830D0`) | Debug sound-test string block (`0xF500` prefix, `0xF600 0xFF00` separator) |
| `0x0808327C` (`0x8327C`) | Debug sound-test table, 12-byte records `{u32 name_ptr, u16 id, u16 arg, u32 flags}` |
| `0x0800070C` (`0x70C`) | Debug sound-test input/update (Down/Up/A/B) |
| `0x08000634` (`0x634`) | Debug sound-test init/state machine (mode byte `0x03002CC0`) |
| `0x080002DE` (`0x2DE`) | Screen dispatch: `u8` index at `0x03000D64`, 28-entry table at `0x08000310` |
| `0x08000310` (`0x310`) | Screen table; entry 0 = `0x08000380` → debug sound test |
| `0x03000D64` (RAM) | Current screen index (normal boot writes 4) |
| `0x03000DD8` (RAM) | "next screen" staging byte used by transitions |
| `0x03002CC0` (RAM) | Sound-test mode/state byte (init 0, then 1) |
| `0x08079608` (`0x79608`) | Title/menu screen logic (5-entry ring) |
| `0x0802E746` / `0x0802E75C` | `CHANGE THE MOVEMENT OPTION.` / `MOVEMENT OPTION HAS BEEN SET.` |
| `0x0822A884` (`0x22A884`) | `EEPROM_V124` save marker |

Text encoding recovered from the live VM: `A=0x1A … Z=0x33`, space `0x00`,
`.` `0x37`, `?` `0x39`, `!` `0x3A`, `,` `0x40`, `'` `0x41`/`0x45`, `"` `0x43`.
Controls seen: `0x8100` line break, `0x8400` page end, `0x8500/0x8501`,
`0x8800`, `0x9E00`, `0x9501`, `0x9200` (pointer), `0x9601` (player name),
`0x9F00` page, `0x9313/0x9280`, `0xF500/0xF600/0xFF00` list markers.
Example: `HI! MY NAME IS` encodes as
`21 00 22 00 3A 00 00 00 26 00 32 00 00 00 27 00 1A 00 26 00 1E 00 00 00
22 00 2C 00` (u16 LE).

## 5. Algorithm

There is no validator to reproduce. The ROM's input and text behaviour are:

```
raw   = *(u16*)0x04000130            // active low
held  = (~raw) & 0x03FF
pressed = held & ~old_held
repeat = pressed; timer = 30
if pressed: timer = 30
else if timer: timer--
else: repeat = held; timer = 6
old_held = held
if (held & 0x000F) == 0x000F: soft_reset()   // A+B+Select+Start
```

All menus consume `held`/`pressed` one frame at a time. No code path stores a
sequence of presses, and no code path compares a key word against a multi-key
constant. The title menu's ring index is a byte in EWRAM; its five entries are
rendered from bitmap graphics (the mixed-case labels are not glyph text).

The message VM reads `u16` opcodes from a pointer in the message object. Glyph
codes (`<0x8000`) are rendered with the game's 16-bit glyph font; `0x8000+`
opcodes select line/page/name/colour/pointer behaviour. The name command
`0x9601` inserts the eight-slot player/dog name into the message; the name is a
label, not a key. The name keyboard only accepts `A–Z` and has exactly 8 slots.

## 6. Tables

**Button masks (active-high after `~KEYINPUT`):**
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200`.

**Title ring (5 entries, screen order):**

| # | Entry | State with no save |
|---|---|---|
| 0 | New Game | selectable; starts the intro |
| 1 | Continue | greyed; `NOT YET AVAILABLE` |
| 2 | Always Together Mode | greyed; `NOT YET AVAILABLE`; ending unlock |
| 3 | Puppy Visiting Mode | greyed; `NOT YET AVAILABLE`; GBA Link mode |
| 4 | Settings | greyed; `NOT YET AVAILABLE`; only movement type after a save |

**Debug sound-test table (`0x0808327C`, 17 entries observed):**

| # | Name | id | arg |
|---|---|---|---|
| 0 | SOUND TEST | `0x66` | 0 |
| 1 | FLOOR | 0 | 2 |
| 2 | MAIN MENU | 3 | `0x14` |
| 3 | ENDING | `0x0F` | 6 |
| 4 | FLOOR CONTROL | 2 | 0 |
| 5 | MORNING | 9 | `0x15` |
| 6 | TAKE WALK | 0 | 8 |
| 7 | REVERSY | 3 | `0x0A` |
| 8 | QUIZ | 3 | `0x0B` |
| 9 | ACTION | 3 | `0x0C` |
| 10 | SHOP | 1 | 9 |
| 11 | EXTRA ENDING | 7 | `0x0E` |
| 12 | STATUS | `0x0A` | `0x0F` |
| 13 | BREAKFAST | 1 | `0x19` |
| 14 | DINNER | 1 | `0x1A` |
| 15 | LIVING WITH A PUPPY | 0 | `0x1B` |
| 16 | DELETE SAVE | 0 | `0x11` |

The record order is the table order, not the string-block order. The strings
are music/scene labels; the screen is a developer sound test (it shows
`SOUND TEST` plus a 3-digit track number, and Down/A change the selected track).

**Text/keyword scan counts (8 MiB image):**

| Word | ASCII | +0x20 | XOR8 | ADD8 | 16-bit glyph |
|---|---:|---:|---:|---:|---:|
| PASSWORD | 0 | 0 | 0 | 0 | 0 |
| PASSCODE | 0 | 0 | 0 | 0 | 0 |
| CHEAT | 0 | 0 | 0 | 0 | 0 |
| DEBUG | 0 | 0 | 0 | 0 | 0 |
| SECRET | 0 | 0 | 0 | 0 | 0 |
| UNLOCK | 0 | 0 | 0 | 0 | 0 |
| CODE | 0 | 0 | 6* | 1* | 0 |
| ITEM | 0 | 0 | 1* | 1* | 0 |

`*` The `CODE`/`ITEM` transform hits are inside graphics/coefficient data, not
text: e.g. `CODE xor 0x48` at file `0xAF300` decodes to pixel/table bytes; no
hit is a NUL-terminated string or a pointer-referenced text record.

**Printable text runs:** 14,077 runs ≥6 glyphs across the whole image; the
dialogue bank `0x2F000–0x33000` alone decodes to 405 runs ≥6 glyphs. No run is
a code table (no run of equal length NUL-padded records with a pointer table).

## 6b. Enumeration

**Space definition.** Code/password space = ∅. Alphabet(s) = ∅, length(s) = ∅,
field widths = none, checksum = none. Number of representable valid codes:
**0**. There is no input field, no accepted-string table, no generator/decoder
pair, and no validator to invert.

What was enumerated instead, with the size of each space:

| Surface | Size | How bounded |
|---|---|---|
| Title ring entries | 5 | on-screen walk of the ring (`New Game` … `Settings`) |
| Intro screens | 9 | boot logos, title, gender/colour, name, confirm, survey, pet-shop intro, puppy table, free-roam |
| Dialogue/tutorial glyph runs | 14,077 (whole image), 405 in bank `0x2F000–0x33000` | 16-bit glyph decoder; 0 keyword hits |
| Text transforms searched | ASCII, +0x20, 256 XOR, 256 ADD, UTF-16LE/BE, 16-bit glyph | per-word counts above |
| Keypad read sites | 1 (`0x0807D82C`) | literal `0x04000130` scan + Thumb LDR verification |
| Key-state references | 243 | literal-pointer scan + Capstone LDR classification |
| Key-state histories / sequence tables | 0 | struct has 4 fields only; no array writes; no multi-key compares |
| u16 single-button mask runs | 1,345 | whole-ROM scan; 14 pointer-referenced, all data tables |
| Debug sound-test entries | 17 | table at `0x0808327C` + screen invoked in §7 |
| Save flag unlocks (Always Together / Puppy Visiting) | 2 modes | published lists + gate text; not codes |

**Novel code.** None can be minted, because the accepted set is empty. This is
the "no system" case of §16.3: no table, no validator, no input surface. It is
not dead/cut/gated code-entry: the text-entry-looking screens are the title
menu, the name keyboard, the puppy survey, the `PUPPY` table and gameplay
menus; the name keyboard is an 8-slot label field and the survey is a
personality quiz.

**Bounds proven by rejection / gate tests.**

* The only non-gameplay menu entry (`Settings`) was entered without a save and
  the game rejected it with `NOT YET AVAILABLE.` (observed). The published FAQ
  and the ROM strings show the unlocked screen contains only a movement-type
  toggle; there is no field that accepts a code.
* The name keyboard stops at **8 slots** (observed: eight underscores, cursor
  advances through all eight); it accepts any `A–Z` string, so it is not a
  validator. There is no rejected-name path.
* Every attempted button combo at boot/title was consumed as normal navigation
  (Konami's B closed the menu) or as the documented soft reset
  (`A+B+Select+Start`); no code screen appeared. A code input cannot be
  rejected because it cannot be entered.
* The debug sound-test screen is unreachable by input: the screen byte's boot
  writer stores 4; the direct constant stores resolved by the literal-pointer
  scan write 1–27; no input path writes 0. Setting the screen byte to 0 is a
  debugger action, not an in-game path.

## 7. Validation evidence

**Observed (emulator):**

* Header, logos, title, main ring with five entries and their `NOT YET
  AVAILABLE` messages.
* `New Game` flow: gender/colour, 8-slot name keyboard, `Is this okay?`,
  `Puppy Survey` (`ENERGETIC/RELAXED`, `SMALL/LARGE`, result `RELAXED / FEMALE
  / SMALL`), `Life with Puppy`, pet-shop dialogue, `PUPPY` table, free-roam
  pet shop with `WALK / CALL / START / B`.
* Button tests: Select, `L+R+Start`, `Select+Start`, Konami, and
  `A+B+Select+Start` (the last resets to the MTO copyright screen).
* Debug sound test rendered after debugger writes; `SOUND TEST 000` and
  `ENDING 000` screenshots.
* Keyboard slot limit (8) and any-string acceptance.

**Derived (static):**

* Single KEYINPUT read site; key-state layout and repeat algorithm.
* 243 key-state references, all single-frame tests; no sequence matcher.
* 1,345 mask runs, 14 pointer-referenced, all data tables.
* 16-bit glyph decoder and the 14,077-run text scan; zero code/password words.
* Screen dispatch and sound-test table; no input path writes screen 0 (the
  screen-0 entry is the debug handler itself).
* `EEPROM_V124` save hardware; title gate is a save-presence test.

**Inferred (not fully exercised):**

* Each sound-test entry selects/plays a music track; the screen title, the
  3-digit counter, and the table fields support this, but individual tracks
  were not auditioned.
* The `Settings` movement-type submenu was not reached because no save exists;
  its only option is established by the ROM strings and the published FAQ, not
  by a screen walk.
* `DELETE SAVE` is a developer erase option; its effect on EEPROM was not
  exercised.

## 8. Unknowns

* The exact save flag that unlocks `Always Together Mode` (ending rank bit) was
  not located; it is a save-bit unlock and per §16.18 not a code.
* The in-home item/pause menus were not reached: the intro tutorial's
  "hold the puppy" step did not advance in this session. They are gameplay
  menus, not code surfaces; the only text/key input is the name keyboard.
* The sound-test screen's reachability in a hypothetical debug build/flag is
  not applicable to the retail image; the retail screen-0 writer analysis
  closes it.

## 9. Tooling

* `mgba` (SDL) 0.10.5 under `Xvfb :344` + `openbox`, `xdotool`, `scrot`/`import`.
* `arm-none-eabi-objdump -M force-thumb` for the input, screen dispatch and
  sound-test handlers.
* Python 3 + `capstone` 5.0.7: literal/LDR scans, key-state reference
  classification, u16 mask-run scan, mask-table pointer scan, glyph decoder.
* mGBA built-in debugger (`-d`) and GDB stub for RAM reads and the sound-test
  invocation.
* `strings -t x`, `grep -abo`, custom XOR/ADD/UTF-16/glyph scans.

No ROM assets are reproduced in this report.

## 10. Legal note

No ROM, graphics, music or text assets are redistributed. Addresses, hashes,
algorithm description and our own test notes only.
