# Bratz: Forever Diamondz (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Bratz: Forever Diamondz.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `BRATZDIAMOND` (12 bytes at 0x0A0) |
| Game code | `BXFE` |
| Maker code | `78` |
| Software version | 0x00 (Rev.00) |
| MD5 | `afbd8a5d314391d9731692cc1131dc6c` |
| SHA-1 | `68222b1e029d931c2a9776b7040928a921a9c12b` |
| SHA-256 | `263f58a5634b42ff593afd98e7e42042581347b6b9e0cc5a5b63cd4636646689` |

Header details (observed):

* Entry word `0x00` = `0xEA00002E`, the stock `b 0x080000C0` branch.  No cracktro entry.
* Nintendo logo at `0x04` is the standard 156-byte logo.
* Fixed byte `0x0B2` = `0x96`.
* Complement byte `0x0BD` = `0x3E`, which matches the calculated value
  (`sum(0x0A0..0x0BC) = 0xA9`, `-(0xA9+0x19) & 0xFF = 0x3E`).
* Header checksum at `0x0BE` is `0x0000`; the value implied by the complement
  is `0x00C2`.  A zero checksum with a valid complement is the usual artifact
  of a header-normalisation/rebuild tool, not a trainer.
* Embedded-header scan: the 156-byte logo occurs exactly once, at `0x04`.
  This is a single 8 MiB image, not a multi-game pack, and there is no
  appended second image.
* Trainer/cracktro scan: no `SUNHORS`, `Mode7`, `CRC BANDIT`, `cracktro`,
  `trainer`, `GameShark` or `Action Replay` strings; the first 4 KiB is normal
  crt0/IRQ code.

Developer/publisher: Barking Lizards Technologies / THQ (GBA SKU).  The
PlayStation 2, GameCube and PC SKUs were Blitz Games titles and are a different
game with a different feature set.

## 2. Executive summary

**This GBA ROM has no in-game password system, no cheat computer, no
button-code table and no debug menu.**

The published `SIZZLN`, `FLAUNT`, `SPRKLE`, `SKATIN`, `JEWELZ`, `DIMNDZ`,
`LIPSTK`, `TREATZ` … passwords are console/PC (`Blitz Games` SKU) codes.  The
GBA SKU is the separate `Barking Lizards` game.  Its complete text bank
(UTF-16LE, 1,315 strings of >=4 chars in the main bank; 4,589 >=4-char runs over
the whole image) contains:

* `PASSWORD` / `PASSCODE` — 0
* `CHEAT` / `CHEATS` — 0
* `CODE` / `CODES` — 0
* `SECRET CODE` — 0
* `ENTER` as an entry prompt — 0 (`Enter Stage Right` is a stage direction)
* `INVALID` / `TRY AGAIN` (as code rejection) — 0 / 1 (a minigame retry)
* `UNLOCK` — 0
* `DEBUG` — 0
* `GALLERY` / `CONCEPT ART` — 0
* `COMPUTER` — 1, and that one is `Jade: But we don't have a computer.`
* `OFFICE` — 5, all `Festival Office(s)` (a story location), never a Bratz
  office with a cheat computer.

No code literal is present as a code entry: none of the 15 published codes
occurs as a standalone 6-character record anywhere in the 8 MiB, in ASCII,
UTF-16LE, 5-bit packing, 6-bit packing, simple XOR or +/-0x20 forms.  Two codes
occur only as substrings of unrelated words (`SKATIN` inside `ICE SKATING`,
`JEWELZ` inside `CRYSTAL JEWELZ`).

The game has a complete, working input library, but it stores only the current
per-button state/counters, not a sequence history; no cheat-sequence table or
matcher exists.  The only text-template token in the game is `#NAME?`, used to
substitute a character's name into dialogue — there is no name-entry screen and
no keyboard UI.

The non-cheat, story-gated content is present and was enumerated: a 14-slot
Mini Games menu, a Level Select menu, and the Dressing Room/shop outfit system.
None is reached by a code; all are driven by story progress or Blingz.

Because the code space is empty, there is no novel code to mint.  Section 6b
states the bounded negative with the exact search counts and the dynamic probes.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (`/usr/games/mgba`, `mgba-sdl` package) under
`Xvfb :205 -screen 0 1024x768x24`, openbox, `SDL_AUDIODRIVER=dummy`.

Keymap used (mGBA SDL default):

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Boot and reach the street reproducibly:

1. `DISPLAY=:205 SDL_AUDIODRIVER=dummy mgba -3 "Bratz: Forever Diamondz.gba"`.
2. Wait through the four-character splash and the title.
3. Title with no save: `New Game`, `Mini Games`, `Level Select`, `Credits`.
4. `New Game` → intro dialogue → press Start on the `TRUCK DESIGN` tutorial →
   `Down`, `A` on `Accept changes` → intro dialogue → Road Tripz driving level →
   Start → `Quit` → `OVERVIEW` → `CONTINUE` → Willoughby Springs street.
5. Pause menu: Start → `Resume`, `Dressing Room`, `Objectives`, `Save Game`,
   `Quit`.
6. After `Save Game`, quit to the title: the title gains `Load Game`
   (`New Game`, `Load Game`, `Mini Games`, `Level Select`, `Credits`).

Menu paths exercised (screenshots retained in `/tmp/opencode/bratzforever`,
prefix `c_`):

| Screen | Path | Observed |
|---|---|---|
| Title, no save | boot | 4 items: New Game, Mini Games, Level Select, Credits |
| Title, with save | after Save Game + Quit | 5 items: New Game, Load Game, Mini Games, Level Select, Credits |
| Mini Games | title → Mini Games | `1 of 14` … `14 of 14`, each `???` with lock icon |
| Level Select | title → Level Select | empty framed list at fresh save and after early save |
| Credits | title → Credits | Barking Lizards staff roll; no code text |
| Pause | street → Start | Resume, Dressing Room, Objectives, Save Game, Quit |
| Dressing Room | Pause → Dressing Room | Tops / Bottoms / Accessories, `CONTINUE`; 2 tops at start |
| Objectives | Pause → Objectives | `1 of 2 Find a contestant`; `2 of 2 Buy at least 8 articles of clothing / 8 Pieces Remaining` |
| Save Game | Pause → Save Game → Yes | `Save In Progress`, `Please do not turn the power off or remove the Game Pak.`, then save complete |
| Load Game | title (with save) → Load Game | resumes the single save directly (no slot list) |
| Truck design | New Game → tutorial → Start | `TRUCK DESIGN`, Left/Right design, Down + A = Accept changes |
| Road Tripz | New Game → after truck | driving tutorial, Start → Resume/Quit |

Published codes tested (literals and record forms) — see §6.  Because there is
no text-entry surface anywhere in the game, none can be submitted; the test is
a search of the complete binary and its decompressed resources, not a menu
entry.

## 4. Address map

File offset ↔ ROM address: `rom_address = 0x08000000 + file_offset`.

| Offset / address | Meaning |
|---|---|
| `0x000000`–`0x0000BF` | GBA header |
| `0x03EFB8` | Start of the 1,113-name asset-name string pool (ASCII, NUL-separated) |
| `0x043700`–`0x045xxx` | Inline asset directory records: NUL-terminated name padded to 4, then 3–4 `u32` fields (offset/size/type/aux) |
| `0x64551C` | `text.dat` payload (glyph/text resource; the dialogue text itself is elsewhere) |
| `0x0684F54`–`0x06AE8E0` | Main UTF-16LE dialogue/text bank (1,315 runs of >=4 chars) |
| `0x079F2A8` | 96-byte glyph map.  `glyph = table[text_byte - 0x20]` |
| `0x079F2C9` | 26-byte run `0x00..0x19` — part of the glyph map, **not** a password alphabet |
| `0x0802D74C` | Input-library init: clears 10 byte flags and two 10-entry `u16` counter arrays |
| `0x0802D780` | Per-frame key update: reads `KEYINPUT` at `0x04000130`, XORs with `0x3FF` |
| `0x03002D10` | 10-byte current-button flag array (indexed 0..9) |
| `0x03002CF0` | 10 × `u16` press-duration counters |
| `0x03002D20` | 10 × `u16` release-duration counters |
| `0x08033D80`–`0x08033E40` | Text draw routine; loads byte, `sub #0x20`, indexes `0x08079F2A8`, draws glyph |

Input button index order (derived from the masks tested at
`0x0802D78E`…`0x0802D9C8`):

| Index | Button | Mask after `0x3FF ^ KEYINPUT` |
|---:|---|---:|
| 0 | Start | 0x008 |
| 1 | Select | 0x004 |
| 2 | L | 0x200 |
| 3 | R | 0x100 |
| 4 | A | 0x001 |
| 5 | B | 0x002 |
| 6 | Left | 0x020 |
| 7 | Right | 0x010 |
| 8 | Up | 0x040 |
| 9 | Down | 0x080 |

Relevant assets in the name pool: `mainmenu.scn`, `pause.scn`, `flyermenu.scn`,
`text.dat`, `font2_15.gbf`, `font_title.gbf`, `wint_offices.scn` (Winter
Offices, a story location).  There is no `cheat`, `password`, `keyboard`,
`keypad`, `computer` or `office` scene asset.  The full 1,113-name list was
scanned.

## 5. Algorithm

There is no code validator to reimplement.  The only relevant algorithms are
the text renderer and the input library.

### 5.1 Text renderer

The dialogue/menu text in the 0x684F54–0x6AE8E0 bank is little-endian UTF-16
(ASCII code units with a zero high byte).  The renderer at `0x08033D80`:

```text
for each byte c in string:
    if c == 0x20: handle word wrap
    glyph = glyph_table[c - 0x20]      ; glyph_table = ROM 0x08079F2A8
    draw_glyph(glyph, x, y)
```

This is why a raw ASCII `strings` pass finds almost no game text: the bank uses
16-bit code units.  It also means any password UI would have had to store
`ENTER`, `CODE`, `PASSWORD`, `INVALID`, etc. as UTF-16 strings — all are absent.

### 5.2 Input library

`0x0802D780` runs once per frame:

```text
pressed = 0x3FF ^ KEYINPUT          ; active-high
for each of 10 buttons in the order above:
    if pressed & mask:
        press_counter[i]++
        if press_counter[i] == 1: flag[i] = 1
    else:
        release_counter[i]++
        if release_counter[i] == 1: flag[i] = 0
```

There is **no** ring buffer, progress index or sequence compare.  A cheat code
matcher would need its own sequence state; none exists in the ROM (see §6b).

### 5.3 Unlock flow

`Level Select`, `Mini Games` and the Dressing Room are story/progress-gated:
the Mini Games menu always shows 14 slots but all are `???`/locked at a fresh
save; Level Select is an empty list at fresh and early saves.  Outfits are
bought with Blingz in shops; no code path touches them.

## 6. Tables

### 6.1 Menus and counts

| Menu | Items | Notes |
|---|---:|---|
| Title, no save | 4 | New Game, Mini Games, Level Select, Credits |
| Title, with save | 5 | adds Load Game (single-slot, resumes immediately) |
| Pause | 5 | Resume, Dressing Room, Objectives, Save Game, Quit |
| Dressing Room | 3 categories | Tops, Bottoms, Accessories + CONTINUE; 2 tops at start |
| Objectives | 2 pages | find a contestant; buy 8 clothing articles |
| Mini Games | 14 slots | all `???` locked at fresh save |
| Level Select | variable | empty at fresh/early save (story-gated) |
| Shop | purchase UI | item list + Blingz; no code entry (text census) |

### 6.2 Keyword census

UTF-16LE main text bank (>=3-char runs) plus whole-image ASCII strings:

| Token | UTF-16 hits | ASCII hits | Comment |
|---|---:|---:|---|
| PASSWORD / PASSCODE | 0 | 0 | — |
| CHEAT / CHEATS | 0 | 0 | — |
| CODE / CODES | 0 | 0 | — |
| SECRET CODE | 0 | 0 | — |
| DEBUG | 0 | 0 | — |
| UNLOCK / UNLOCKED | 0 | 0 | — |
| GALLERY / CONCEPT ART | 0 | 0 | console-version rewards are absent |
| COMPUTER | 1 | 0 | `Jade: But we don't have a computer.` |
| OFFICE | 5 | 2 | Festival Office(s); the 2 ASCII hits are asset names |
| ENTER (prompt) | 0 | 0 | only `Enter Stage Right` (stage direction) |
| INVALID | 0 | 0 | — |
| CLEAR / DELETE | 0 | 0 | no keypad UI |
| OPTIONS | 1 | 0 | control-pad tutorial sentence, not a menu |

### 6.3 Published codes vs. this ROM

Codes checked: `SIZZLN`, `FLAUNT`, `SPRKLE`, `STYLIN`, `SKATIN`, `JEWELZ`,
`DIMNDZ`, `LIPSTK`, `TREATZ`, `REDHOT`, `KICKIT`, `FLIRTY`, `TONSOF`, `STYLES`,
`ANGELZ`.

Checks performed for each: ASCII, lowercase `+0x20`, UTF-16LE (`c,0`),
UTF-16BE (`0,c`), UTF-32LE, 5-bit packing (A=0 and A=1, both bit orders),
6-bit packing, whole-string XOR with all 256 keys, and +/-decimal offsets
−64..+64.

Result:

* Exact standalone code records: **0 / 15**.
* Substring-only hits: `SKATIN` inside `MINIGAME- ICE SKATING` at
  `0x069E60C`; `JEWELZ` inside `CRYSTAL JEWELZ` at `0x06AB2DC`.
* No 6-character code table, no 26-symbol alphabet, no checksum, no
  accept/reject strings.

## 6b. Enumeration

### Space definition

This ROM defines **no code space**:

| Property | Value |
|---|---|
| Alphabet(s) | none (no keyboard/alphabet table exists) |
| Length(s) | none |
| Field widths | none |
| Checksum | none |
| Reserved bits | none |
| Lookup table | none |
| Representable values | 0 |

The only 26-byte ascending run in the image (`0x079F2C9`) is part of the
96-byte glyph map indexed by `ASCII - 0x20`; it is not an input alphabet.

### Menu enumeration

All non-story-gated menu surfaces were walked (screenshots in
`/tmp/opencode/bratzforever`):

1. Title, fresh: 4 items.
2. Title, after save: 5 items (Load Game added).
3. Mini Games: 14 slots, `1 of 14` … `14 of 14`, every slot `???` with a lock
   icon.  No unlock prompt, no code prompt, no hidden 15th slot.
4. Level Select: empty list at fresh and early save; no code prompt.
5. Credits: Barking Lizards staff roll to the end; no code line.
6. Pause: 5 items; Dressing Room, Objectives, Save Game each opened.
7. Save: confirmation, `Save In Progress`, completion.
8. Load Game: single-save resume, no slot/keyboard.
9. Truck design and Road Tripz tutorial: text-only tutorial screens.
10. Shop/interior menus: purchase UIs described entirely by the UTF-16 bank;
    no entry field, no `CODE/PASSWORD/ENTER` string, no keyboard asset.

### Text/asset search space

| Space | Count searched |
|---|---:|
| ASCII strings, `strings -n 3` | 162,092 |
| ASCII strings, `strings -n 4` | 112,632 |
| UTF-16LE runs, >=2 chars | 7,592 |
| UTF-16LE runs, >=3 chars | 5,183 |
| UTF-16LE runs, >=4 chars | 4,589 |
| Main dialogue bank, >=4 chars | 1,315 (0x0684F54–0x06AE8E0) |
| LZ77 blocks decompressed and searched | 100 |
| Asset names (`.scn/.gbf/.pal/.dat/.swb/.bin`) | 1,113 |
| `.scn` scene names | 98 |

### Button-code space

The input library was reversed (see §4/§5.2).  It stores per-button
current-state flags and press/release counters — not a sequence history.
Targeted searches:

* All 4–12-byte runs of key indices `0..9` with a 32-bit pointer into the run:
  18 candidates inspected; none is a cheat sequence (they fall in string/tile
  data or in UI tables).
* All 4–16-entry runs of `u16` key masks (`1,2,4,8,0x10,0x20,0x40,0x80,0x100,
  0x200`) with a 32-bit pointer: 17 candidates inspected; all are repeated-data
  graphics/tile runs, not sequences.
* Literal Konami sequence (`Up Up Down Down Left Right Left Right B A`) in
  active-high and active-low `u16`, and one byte per press: 0 hits.
* Dynamic probe: the Konami sequence typed on the title screen produced only
  normal menu navigation (the final `A` selected New Game); no hidden screen
  appeared.
* Dynamic probe: `L+R+Start` and `A+B+Start+Select` at the title both acted as
  Start (they selected the highlighted New Game); `L+R+Select` and
  `Up+Down+Left+Right` together produced no visible change.  No hidden screen
  or unlock appeared.
* No string tables for `CHEAT`, `DEBUG`, `SOUND TEST`, `GALLERY` or `BONUS`.

### Published codes — bounds and rejection

Because the ROM has no text-input surface, a published code cannot be
"rejected by the game": there is no screen on which to submit it.  The bounded
negative is therefore:

* 15 published codes checked against every encoding/record form above: 0
  standalone records, 2 substring-only hits.
* The complete dialogue bank has no entry-prompt/rejection vocabulary
  (`ENTER`, `CODE`, `PASSWORD`, `INVALID`, `CLEAR`, `DELETE`): 0 hits.
* The asset pool has no keyboard/computer/cheat/office scene asset.
* Dynamic title-screen probe of a common button code produced normal menu
  behaviour only.

### Novel code

Not applicable: there is no code space in which a novel code could exist.  The
required positive deliverable for a code engagement (§0.2) is replaced by the
bounded negative above, which is the correct result for this SKU.

## 7. Validation evidence

**Observed (emulator screenshots / menu behaviour):**

* Title 4-item and 5-item menus; Load Game appears only after saving.
* Mini Games `1 of 14` through `14 of 14`, all `???` locked.
* Level Select empty at fresh and early save.
* Pause 5 items; Dressing Room with 2 tops; Objectives pages 1 and 2.
* Save In Progress screen and successful save.
* Credits roll ends with no code.
* Konami sequence on the title = normal navigation, final A starts New Game.
* Glass doors on the Willoughby Springs street are scenery/locked; no
  transition.

**Derived (instruction/data analysis):**

* Text bank is UTF-16LE and the renderer indexes a 96-byte glyph map with
  `byte - 0x20` (`0x08033DF2`/`0x08033E0A`, table `0x08079F2A8`).
* Input library `0x0802D780` stores current-state flags/counters, not a
  sequence; no cheat matcher or table exists.
* 100 LZ77 blocks decompress cleanly; none contains a code string.
* Asset-name pool has 1,113 names, none for a cheat/password/keyboard/computer
  scene.

**Inferred:**

* The GBA SKU is Barking Lizards' own game and diverges from the Blitz
  Games console/PC SKUs; the published console passwords were copied onto the
  GBA GameFAQs/SuperCheats pages but have no GBA implementation.
* Story-gated unlockables (14 Mini Games, Level Select, outfits) are the
  intended progression, not cheat codes.

## 8. Unknowns

* The exact story flag that first populates Level Select / unlocks each of the
  14 Mini Games was not isolated; the menus were observed locked, and the text
  bank ties them to story progress rather than a code.
* Shop interiors are story/position-gated purchase rooms.  Their complete
  string set was enumerated from the text bank and the asset pool; no shop
  string or asset contains an entry field, a code label, or a keyboard.  Their
  exact clerk/door coordinates therefore add no cheat surface and were not
  needed for this negative result.
* A later GBA revision or another regional build could differ; all findings
  here are for SHA-256
  `263f58a5634b42ff593afd98e7e42042581347b6b9e0cc5a5b63cd4636646689`.

## 9. Tooling

* mGBA 0.10.5 (`mgba-sdl`), Xvfb `:205`, openbox, xdotool, scrot,
  ImageMagick (`convert`, `montage`).
* `arm-none-eabi-objdump` with `-M force-thumb` for the input/text routines.
* Python 3 scripts in `/tmp/opencode/bratzforever`:
  * header/hash/logo/checksum check;
  * `strings` census and UTF-16LE text-bank extractor;
  * GBA LZ77 block scanner/decompressor;
  * encoding/packing search for the published codes;
  * mGBA PNG-savestate (`gbAs` zlib chunk) RAM extractor;
  * key-index/key-mask pointer-run scanners.
* Capstone 5.0.7 available for instruction verification.

## 10. Legal note

No ROM, extracted graphics, music or text is redistributed here.  Only hashes,
addresses, format descriptions and counts are published; screenshots are local
analysis evidence.

## 11. Reproduction checklist

* [x] ROM hashed, header/logo/complement/checksum checked; single image,
      no trainer.
* [x] ASCII and UTF-16 text census with counts.
* [x] Published codes searched in 15+ encodings; none standalone.
* [x] 100 LZ77 blocks decompressed and searched.
* [x] Title (4/5 items), Mini Games (14), Level Select, Credits, Pause,
      Dressing Room, Objectives, Save, Load, truck/Road Tripz walked.
* [x] Input library reversed; no sequence history or cheat table.
* [x] Key-index and key-mask pointer-run scans (18 + 17 candidates) inspected.
* [x] Dynamic probes at the title: Konami = normal navigation; `L+R+Start`
      and `A+B+Start+Select` = Start; `L+R+Select` and all four directions =
      no change.
* [x] Bounded negative written; no code space exists to enumerate.
