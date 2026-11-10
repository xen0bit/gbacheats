# Broken Sword: The Shadow of the Templars (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Broken Sword: The Shadow of the Templars/Broken Sword: The Shadow of the Templars.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `BROKENSWORD` |
| Game code | `ABJE` |
| Maker code | `6L` (BAM! Entertainment) |
| Software version | 0x00 (Rev.00) |
| Complement byte (0xBD) | 0x6D — valid |
| Header checksum (0xBE) | 0x0000 (rebuilt-header artifact; complement is valid) |
| Entry word (0x00) | `0xEA00002E` — stock ARM branch to 0x080000C0 |
| MD5 | `5bf98eb8cc6247b4edf7b9b5b08dbab9` |
| SHA-1 | `314eced054604866153883ee20e0966e1443e0d9` |
| SHA-256 | `bd66dfee0a05c252957333b9b040bc8f730b3e986fd5f18cc12f0981aef08d30` |

Phase 0 checks:

* The Nintendo logo occurs exactly once, at file 0x4. There is no second GBA
  header, no multiboot stub, and no concatenated image.
* Entry branch, logo, fixed 0x96 byte, and complement are stock. Searches for
  `MODE7`, `SUNHORS`, `CRC BANDIT`, `PARADOX`, `EURASIA`, `Venom`, `cracktro`,
  and `trainer` returned zero hits. No trainer menu or cracktro is present.
* The last 8 bytes of the image are zero, matching the published account that
  the game fit on the 8 MiB cartridge with 8 bytes to spare.
* Save hardware: EEPROM; engine strings `Failed to write EEPROM tag data.`
  (0x1C4F6), `Failed to erase slot.` (0x1C518), `illegal slot` (0x1C530),
  `no save in slot` (0x1C548). mGBA created an 8192-byte `.sav`.

## 2. Executive summary

**There is no in-game code system in this port.** No typed password screen, no
button cheat code, no debug/test room, no chapter select, no unlockable gallery
or "making of", and no hidden pause-menu entry was found. The negative is
bounded by the searches and screen walks in §6b.

What the ROM does contain:

1. **A new engine, not the original Virtual Theatre/SCUMP debug build.** The
   image is full of C++ RTTI/class names (`CASprite`,
   `CAPalettised8x8Tiled`, `CADrawable2D`, `CAPixelSource`) and a custom
   script VM with phase/action tables and `SC_*` opcodes. Its script symbol
   table has 5,229 unique identifiers and 147 room/location names; none is a
   debug, test, cheat, password, chapter or unlock room.
2. **One hard-coded multi-button sequence in code:** hold A+B+Start and press
   Select → the stock GBA BIOS `SoftReset` at 0x080165C8. It is the standard
   reset combo, not a cheat; it was observed returning to the Revolution logo.
3. **One free-text field:** the save-slot name entry. It offers 60 glyphs
   (A–Z, a–z, space, `! ? * , . [ ]`), accepts up to 15 characters (the cursor
   then moves to OK), stores the characters verbatim in the 16-byte slot name
   field, and has no validator or rejection path. It is a save label, not a
   password.
4. **Credits are a normal, visible surface:** Title → Options → Credits from
   first boot. The scrolling credit roll shows the GBA port staff (Producer
   Steve Ince; System Design Tony Warriner; Technical Programming Andrew
   Boskett; Implementation Ross Hartshorn, Jonathan Howard, Dale Strachan).
   There is no "making of", concept-art, gallery or movie-unlock surface.
5. **One hidden developer room:** `PARIS4 / MONTFAUCON_EXTRA` in the room table,
   with the `extra_door` object and `montfaucon_extra0` phase. This is the
   published *Broken Sword 3* sewer easter egg, reached by walking in the
   Montfauçon sewer, not by a code. It is developer-intended hidden content,
   not a cheat.

Published "cheats" for this title are Pro Action Replay/GameShark v3 memory
patches (master code + "All Map Areas Open"). They are external memory edits,
not in-game inputs, and are out of scope; their literals are absent from the
ROM (0 hits) and no screen exists on which to enter them.

## 3. How to reproduce

Emulator and display:

```bash
Xvfb :214 -screen 0 1024x768x24 &
DISPLAY=:214 openbox &
DISPLAY=:214 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 \
  "roms/Broken Sword: The Shadow of the Templars/Broken Sword: The Shadow of the Templars.gba" &
```

Observed mGBA SDL keymap (verify with the title menu):

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Hold keys 100–250 ms; the game ignores very short taps in dialogue.

Menu path (all observed):

1. Boot → legal/copyright screen → A.
2. **Choose Language** (5 values): English, Français, Deutsch, Italiano,
   Español. `Left/Right` cycles, `Down` to **OK**, A.
3. **Title**: `Play`, `Options` (exactly two items).
4. **Options (title)**: `Audio ON/OFF`, `Language`, `Credits` (three items).
5. **Credits**: scrolling roll; B returns to Options.
6. **Play / save manager**:
   * no save: `New Game`, slots 1–3, `Copy`, `Erase`;
   * with saves: `Continue`, slots 1–3, `Copy`, `Erase`.
7. **Name entry** (new game): 5×12 glyph grid, `OK`, `Cancel`.
8. **Erase Game** → slot → `Are you sure? No/Yes`.
9. **In-game pause** (Start): `Play`, `Save Game`, `Options` (three items).
10. **In-game Options**: `Audio`, `Language` (two items; no Credits here).
11. **Inventory** (`L`): item-gated; no screen at the first save because George
    has no items yet. The combine gesture is `Up` on an item then A (in-game
    help/walkthrough); it is not a cheat surface.
12. **Dialogue**: icon-driven (talk/look/use), no typed input anywhere.

Soft reset (observed): hold A+B+Start, then press Select. The screen returns to
the Revolution logo and then the title.

Name-entry bound (observed): start a new slot, press A 15 times to fill the
name line with 15 characters. The next A moves the cursor to **OK**; one more
A submits the form and returns to the Play menu. The slot then displays the
name and the `.sav` contains it verbatim.

Published codes checked (not applied):

* `E6897AE2 AD10D116 66EDA8CB 1AC9BA47` (AR master)
* `C35D8D11 13E05B90 D9387327 8E61F83D` (AR master)
* `9A9D1915 C9140BBC 793C3816 … 921B3BB0` (All Map Areas Open)

All are GameShark/AR v3 encrypted memory patches. Their plaintext literals
(`E6897AE2`, `9A9D1915`, `All Map Areas Open`, etc.) return 0 hits in the ROM.
They are not in-game cheats and were not applied, per scope.

## 4. Address map

File offset ↔ ROM address: `rom_address = 0x08000000 + file_offset`.

| File offset | ROM address | Meaning |
|---:|---:|---|
| 0x000000 | 0x08000000 | ARM entry / header |
| 0x0000C0 | 0x080000C0 | stock crt0 |
| 0x000E60 | 0x08000E60 | **key-input reader** (only KEYINPUT reader in code) |
| 0x000ECC | 0x08000ECC | literal `0x04000130` (KEYINPUT) |
| 0x000ED0 | 0x08000ED0 | literal `0x000003FF` (button mask) |
| 0x0165C8 | 0x080165C8 | **BIOS SoftReset** (writes 0 to 0x02080408 and 0x03007FFA, SP=0x03007FFA, `svc 1`, `svc 0`) |
| — | 0x02000000 | EWRAM: held buttons, active-high |
| — | 0x02000002 | EWRAM: newly-pressed buttons |
| 0x0ED990 | 0x080ED990 | `phase_0_titles` (title/intro script table) |
| 0x109940 | 0x08109940 | phase table for the Paris map (`phase_0_paris_map` at 0x109961) |
| 0x10A0DF | 0x0810A0DF | `restart_or_load` script action |
| 0x10A712 | 0x0810A712 | `global_menu_text`, 122 × 12-byte text-ID records (0x64–0xFC) |
| 0x1A5EC1 | 0x081A5EC1 | `montfaucon_extra0` hidden-room phase |
| 0x1A5EF9 | 0x081A5EF9 | `extra_door` object |
| 0x1BD5A7 | 0x081BD5A7 | `skip` scenery object (Baphomet dig room) |
| 0x1BFB45 | 0x081BFB45 | `skip` scenery object (dig exterior), with `lower_skip` at 0x1BFD67 |
| 0x1CA9CB | 0x081CA9CB | `movie` script action (Scotland tower cutscene) |
| 0x1C4F6 | 0x081C4F6 | EEPROM error strings |
| 0x1C8C0 | 0x081C8C0 | `SC_SETGLOBALFLAG` error string |
| 0x1CCA0 | 0x081CCA0 | `SC_JUMPTOREF` error string |
| 0x1CD48 | 0x081CD48 | `SC_WALKTO` error string |
| 0x7F0422 | 0x087F0422 | start of resource-name manifest |
| 0x7F45F2 | 0x087F45F2 | `MENUS.LOC` |
| 0x7F87FE | 0x087F87FE | `CREDITS.LOC` |

### Key reader (derived from disassembly)

`0x08000E60` is the only KEYINPUT reader found in the executable engine
code (`0x04000130` also appears once in a non-code data bank at 0x527F76):

```asm
08000E64  ldr r0, =0x04000130      ; literal at 0x08000ECC
08000E66  ldrh r0, [r0]            ; active-low key state
08000E68  ldr r2, =0x000003FF      ; literal at 0x08000ED0
08000E6A  eor r1, r2, r0           ; active-high
08000E6E  ldrh r2, [r4]            ; old held
08000E70  bic r0, r1, r2           ; newly pressed
08000E76  strh r0, [r4, #2]        ; struct+2 = new
08000E7A  strh r1, [r4, #0]        ; struct+0 = held
; reset check
08000E7C  ands r0, r1, #1          ; A
08000E84  ands r0, r1, #2          ; B
08000E8C  ands r0, r1, #8          ; Start
08000E9A  ands r0, r2, #4          ; Select newly pressed
08000EA4  movs r1, #0x80
08000EA6  lsls r1, r1, #18         ; 0x02000000
08000EA8  strh r0, [r1]            ; publish held
08000EAE  strh r0, [r1, #2]        ; publish new
08000EB4  bl 0x080165C8            ; BIOS SoftReset
```

The input module contains one multi-button test:
**A+B+Start held + Select newly pressed → soft reset**. A scan of the code
region for runs of pure button-mask `u16` values found no expected-mask
sequence table and no action dispatcher.

## 5. Algorithm

### 5.1 Key state

```python
held = (~io16(0x04000130)) & 0x03FF
new  = held & ~prev
prev = held
if (held & 0x0001) and (held & 0x0002) and (held & 0x0008) and (new & 0x0004):
    bios_soft_reset()
```

Bit values: A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40,
Down=0x80, R=0x100, L=0x200.

### 5.2 Save-slot name

There is no encoder, checksum, or validator. The name is a fixed 16-byte field
in the 0x800-byte EEPROM slot record:

```text
slot base + 0x00 : 8-byte magic "********" (0x2A × 8)
slot base + 0x08 : 16-byte name field (NUL-padded; observed 15 chars + NUL)
slot base + 0x18 : game-state/flags (not decoded)
```

Slots are at 0x0000, 0x0800, 0x1000; 0x1800 is a global/extra block outside the
three slots. The name is displayed verbatim in the slot list; no accept/reject
path or game-state effect was observed.

### 5.3 Room/phase selection

The script VM selects a section/location (e.g. `SECTIONS\PARIS2\LOCATIONS\
NICO_APT`) and runs a phase such as `phase_0_paris_map`, `go_to_cafe`,
`very_start`, `restart_or_load`. Phase transitions are gated by story flags in
the save state, not by any debug flag or button code.

## 6. Tables

### 6.1 Languages (observed, 5)

English, Français, Deutsch, Italiano, Español. Language is persisted in the
save/EEPROM; the title screen has localized variants `TITLE`,
`TITLE_F`, `TITLE_G`, `TITLE_I`, `TITLE_S`.

### 6.2 Menu items (observed)

| Screen | Items |
|---|---|
| Title | Play, Options |
| Options (title) | Audio ON/OFF, Language, Credits |
| Play (no save) | New Game, slot 1, slot 2, slot 3, Copy, Erase |
| Play (with saves) | Continue, slot 1, slot 2, slot 3, Copy, Erase |
| Name entry | 60 glyphs + OK + Cancel |
| Erase confirm | No, Yes |
| Pause | Play, Save Game, Options |
| Options (in-game) | Audio, Language |

There is no Extras/Bonus/Gallery/Movie item in any of them.

### 6.3 Name-entry alphabet (60 glyphs)

```text
ABCDEFabcdef
GHIJKLghijkl
MNOPQRmnopqr
STUVWXstuvwx
YZ_!?*yz,.[]
```

(`_` is the space position.) No digits. Maximum 15 characters; the stored
field is 16 bytes (15 characters + NUL).

### 6.4 Room table (manifest at 0x7F0422)

197 `SECTIONS\<SECTION>\LOCATIONS\<LOCATION>` path matches →
**15 sections, 147 unique locations**. Counts by section:

| Section | Locations |
|---|---:|
| INTRO | 20 |
| IRELAND | 12 |
| MAPS | 4 |
| PARIS1 | 10 |
| PARIS2 | 18 |
| PARIS2A_HOTEL | 10 |
| PARIS3_HOSPITAL | 6 |
| PARIS3_MUSEUM | 3 |
| PARIS4 | 8 |
| PARIS4_BAPHOMET | 7 |
| SCOTLAND | 21 |
| SPAIN | 10 |
| SYRIA | 5 |
| SYRIA_BULLS_HEAD | 5 |
| TRAIN | 8 |

The complete set is story locations plus `INTRO/TITLE`, `INTRO/LEGAL`,
`SCOTLAND/CREDITS`, `MAPS/DEATH`, `MAPS/EUROPE`, `MAPS/MENUS`, `MAPS/PARIS`,
and the one optional `PARIS4/MONTFAUCON_EXTRA`. There is no `DEBUG`, `TEST`,
`TESTROOM`, `DUMMY`, `GALLERY`, `EXTRAS` or `SOUNDTEST` location.

### 6.5 String/identifier census

* ASCII strings of length ≥ 4: **93,696** (`strings -t x -n 4`).
* Lowercase identifier-like strings: **6,420 occurrences / 5,229 unique**.
* Identifiers containing `phase`: **56**; map transitions `go_to_*`: **17**;
  `soundplayer*`: **18**.

Keyword hits in the identifier set (0 = absent):

| Keyword | Identifiers | Notes |
|---|---:|---|
| `debug` | 0 | — |
| `cheat` | 0 | — |
| `password` / `passwd` | 0 / 0 | — |
| `unlock` | 0 | — |
| `chapter` | 0 | — |
| `bonus` / `gallery` / `making` | 0 / 0 / 0 | — |
| `test` | 0 | — |
| `credits` | 0 | 2 ASCII path hits: `CREDITS.LOC`, `SECTIONS\SCOTLAND\LOCATIONS\CREDITS` |
| `skip` | 2 | `skip`, `lower_skip` — scenery object names in the Baphomet dig room |
| `secret` | 2 | `secret_door`, `secret_hole` — room object names |
| `movie` | 1 | script action in the Scotland tower scene |
| `extra` | 2 | `montfaucon_extra0`, `extra_door` — the BS3 easter-egg room |

The same terms were also searched as case-insensitive ASCII (which covers the
`+0x20` lowercase convention), UTF-16LE, UTF-16BE, and reversed byte order:
`debug`, `cheat`, `password`, `passwd`, `unlock`, `chapter`, `bonus`, `gallery`,
`making of`, `movie`, `extras` all returned 0 in every encoding. `secret`
returned only the two room objects, `skip` only the two scenery objects,
`credits` only the two path names.

### 6.6 Context of the "suspicious" hits

* `skip` at 0x1BD5A7 / 0x1BFB45 is an object record:
  `2c 00 00 00 07 "skip" ...`, next to `paintpot`, `balustrade`, `Guard`.
  It is a scenery/animation object in the Baphomet dig rooms, not a flag.
* `lower_skip` at 0x1BD801 / 0x1BFD67 is the same object family.
* `movie` at 0x1CA9CB is a script action among `throw_knife`, `guido_talk`,
  `examine`; a cutscene command, not a movie gallery.
* `restart_or_load` at 0x10A0DF is a phase/action label in the Paris map
  script; there is no "Restart" menu item in the pause or title UI.
* `global_menu_text` at 0x10A712 is a 122-entry text-ID table, not a debug
  menu.

## 6b. Enumeration

### 6b.1 Space definition

| Surface | Alphabet / domain | Length / count | Validator | Accepted set |
|---|---|---|---|---|
| Typed password | none | 0 input screens | none | empty (0) |
| Button code | 10 buttons (A,B,Select,Start,←,→,↑,↓,R,L) | no sequence table | none | only A+B+Start+Select → reset |
| Save-slot name | 60 glyphs | 0–15 characters | none | **all strings** (no rejection) |
| Menus | fixed item lists | 2/3/5/6 items as in §6.2 | none | all items walked |
| Rooms | 147 locations / 15 sections | — | story flags only | no debug/test room |

### 6b.2 Typed code space

**Zero** password/code entry screens exist. The only free-text input is the
save-slot name, which is not a validator:

* it is offered only while creating a new save slot;
* it accepts every one of the 60 glyphs, in any order, including punctuation;
* it has no length check beyond the 15-character field;
* it stores the string verbatim at slot+0x08 and echoes it in the slot list;
* no accept/reject comparison was found; every string tested was accepted and
  stored (no accept/reject screen, no checksum, no error message).

Space size: `60^0 + 60^1 + … + 60^15 ≈ 60^15 ≈ 4.7 × 10^26` strings, all
accepted. Because the accepted set is the whole space, there is no validator
to model and no "novel code" to mint; a novel 15-character name
(`AAAAAAAAAAAAAAA` in the test) is accepted and stored, which is the
expected behaviour of a label, not of a code.

### 6b.3 Button-code space

A scan of the code region for runs of pure button-mask `u16` values found only
two runs (0x3D774, 0x3D836), both inside non-code data; the remaining runs are
in compressed asset banks. The input module's only multi-button test is the reset
combo in §5.1. No expected-mask table or action dispatcher was found.

Button combinations pressed on the title screen (each followed by a screenshot
and pixel comparison): Select, L, R, L+R, Up+Select, Down+Select, L+R+Start,
L+R+Select, all four d-pad directions together, B+Select, B+Start, L+Start,
R+Start, and the Konami sequence. None produced a new screen. A+Select entered
Play because A is the accept button; A+B+Start+Select produced the observed
soft reset. This bounds the short-combination space tested on the title
surface.

### 6b.4 Menu enumeration

All of the following were walked and screenshotted:

1. Legal screen.
2. Language select (5 values; cycled through all five).
3. Title (2 items).
4. Title Options (3 items).
5. Credits (scrolling; B exits).
6. Play/save manager with no saves (New Game, 3 slots, Copy, Erase).
7. Play/save manager with populated saves (Continue, 3 slots, Copy, Erase).
8. Name entry (60 glyphs, OK, Cancel).
9. Copy Game (slots, Copy, Erase).
10. Erase Game → "Are you sure? No/Yes".
11. In-game pause (Play, Save Game, Options).
12. In-game Options (Audio, Language).
13. Inventory control (L) — no items at the first save; no additional screen.

No hidden screen was reached by any combination or by any menu path.

### 6b.5 Room enumeration

147 unique locations in 15 sections were enumerated from the manifest. No
debug/test/placeholder room exists. The only non-story room is
`PARIS4/MONTFAUCON_EXTRA`, which the published sources identify as the
*Broken Sword 3* sewer easter egg; its `extra_door`/`montfaucon_extra0`
records are present at 0x1A5EC1/0x1A5EF9.

### 6b.6 Published codes

The only published codes are Pro Action Replay/GameShark v3 memory patches.
They are not accepted by the game's own UI and their literals are absent from
the image. The DS/PC "Extras/Bonus Images/Director's Message" unlockables are a
different SKU; the GBA ROM has no `extras`, `gallery`, `concept art`,
`director`, or `bonus images` string in any encoding, and no matching room.

Sources checked: GameFAQs (GBA FAQ index and walkthroughs), CheatingDome,
Almar's Guides/GameShark, SuperCheats, VGChartz (4 walkthrough tips, 0 codes),
Revfans, Broken Sword Zone, and TCRF.
The only GBA-specific published material is the AR/GameShark list and the
Montfauçon sewer easter egg; no typed password or button-code list exists. No
GameFAQs 403 was encountered, so no archive snapshot was needed.

**Conclusion of enumeration:** the code space is empty because no code entry
surface or validator exists; the button space is the standard reset combo plus
normal menu input; the only text space is a non-validating save label. There is
no unpublished code to mint, and the negative is bounded by the counts above.

## 7. Validation evidence

### Observed

* Title has exactly two items; title Options exactly three; pause exactly
  three; in-game Options exactly two.
* Credits are reachable on first boot via Title → Options → Credits and show
  the GBA port staff listed in §2.
* Five languages cycle in the expected order and persist.
* The name entry accepts 15 characters, moves the cursor to OK on the next
  press, and submits on the following press; the save slot stores and echoes
  the text.
* A+B+Start+Select returns the game to the Revolution logo/title.
* The button combinations listed in §6b.3 and the Konami sequence produced no
  hidden screen.
* `.sav` is 8192 bytes; slot magic `********` at 0x0000/0x0800/0x1000; name
  field at slot+0x08.

### Derived

* 0x08000E60 is the only KEYINPUT reader in executable code; its multi-button
  test is the A+B+Start+Select soft reset (0x080165C8).
* 147 locations / 15 sections; no debug/test location; one optional
  `MONTFAUCON_EXTRA`.
* The `skip`/`lower_skip` identifiers are scenery objects, not flags.
* No string in the image names a debug menu, password, cheat, chapter select,
  unlockable gallery or making-of.

### Inferred

* `MONTFAUCON_EXTRA` is the *Broken Sword 3* easter egg described by Revfans,
  Broken Sword Zone and the GameFAQs walkthroughs; it is developer-intended
  hidden content, not a code.
* `SCOTLAND/CREDITS` is the endgame credits room; the title Credits surface
  was observed, the ending itself was not replayed.

## 8. Unknowns

* The exact EWRAM address of the name buffer and a complete xref list for its
  readers were not recovered; the save file and the UI behaviour establish that
  it is a label, and no accept/reject path exists.
* A completion-gated change to the title menu was not exercised (the game was
  not completed in this run). No extras/gallery/concept-art location or string
  exists in the image, so such a menu would have no content to show.
* The ending credits room was not entered; the title credits surface was
  observed and the room exists in the table.

### Fetched-content note (guide §16.8)

A web search for a TCRF page on this title returned a TCRF article whose text
contained a prompt-injection payload (instructions to create `key.bin`, pay a
large sum, and run unrelated commands). It was treated as untrusted data and
ignored. No TCRF GBA article was found; the available TCRF article is for the
PlayStation version.

## 9. Tooling

* `mGBA 0.10.5` (SDL frontend), Xvfb :214, openbox, scrot, xdotool,
  ImageMagick.
* `arm-none-eabi-objdump -M force-thumb` for the key reader and reset routine.
* Python 3 + Capstone 5.0.7 for literal/instruction scans; custom scripts for
  string census, room-manifest extraction, keyword searches and save parsing.
* Work directory: `/tmp/opencode/brokensword` (screenshots and scripts).
* No ROM, graphics, music or text assets are redistributed here.

## 10. Legal note

This report contains only addresses, hashes, algorithms, counts and original
observations. It does not include ROM data or extracted copyrighted assets.
