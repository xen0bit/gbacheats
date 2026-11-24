# Disney's Treasure Planet (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Disney's Treasure Planet.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `DIS T PLANET` |
| Game code | `AZQE` (USA) |
| Maker code | `4Q` |
| Version | 0x00 |
| Entry branch | `0xEA00002E` (stock, `0x080000C0`) |
| Complement byte | stored `0x63`, computed over 0xA0..0xBC = `0x5F` |
| Header checksum | `0x0000` |
| Embedded GBA headers | 1 (Nintendo logo only at file 0x4; not a multi-game cart) |
| MD5 | `2a47d9da2a8653f65f2a23d8052efe8c` |
| SHA-1 | `5d76ab06e6433604f5070ba78b5448f81c6c7a04` |
| SHA-256 | `c5e7ac2ffdaa46ab4cc6afc6be4dcad192321825c716fca5cba31ab0efdadd57` |

Phase 0 notes:

* The entry word is the stock `b 0x080000C0`; the first 4 KiB are normal crt0
  code, not a cracktro.
* No trainer/trojan strings (`SUNHORS`, `Mode7`, `CRC BANDIT`, `trainer`,
  `patch`, `crack`, `piracy`) occur in the image.
* The header complement does not match (0x63 vs 0x5F) and the header checksum
  field is 0x0000. This is the signature of a rebuilt/repacked header (dump
  site artifact), not of a game patch; the entry branch, Nintendo logo and
  title/code fields are stock. All addresses below were derived from this
  image and should be re-checked on another dump.

## 2. Executive summary

The USA build uses **level-name passwords** as its only save/continue system
(the cartridge writes no battery save; the `.sav` mGBA creates is 0 bytes).

* The password table is 26 rows × 6 language columns (`0x03CC9C` strings,
  `0x0E9B34` pointer array). Only rows 2..24 are used; rows 0, 1 and 25 point
  at the sentinel string `none`.
* The player types into an A–Z keyboard (plus a space cell, backspace and OK),
  maximum 8 characters (`0x0800E20E`). The validator compares the input as a
  **prefix** of the table entry for the current language column, case-folded,
  and returns the first matching **row index**. Row index → level id
  (`0x030000E0+12`); the user-visible level is `row − 1`.
* In this USA image the language byte (`0x030000E0+15`) is never written: the
  only store to it found in code is the language-select screen at `0x0801C296`,
  and that screen is scene 4, which **no code ever queues** (all 22
  `0x08016764` call sites pass ids 0,1,2,3,5,6,7,8). The main Options menu has
  only Music/SFX/Credits.
  Consequently only the **English column** is usable here: 23 codes,
  all of which are the published GameFAQs/VGChartz list. The other 115
  localized passwords exist in ROM and match the published six-language FAQ
  exactly, but are unreachable in this build (the FAQ states the European
  version selects a language; scene 4 is that selector and is dead here).
* The table is not checksummed and the input length is not compared, only the
  table entry length. Two consequences were confirmed in the emulator:
  * **Novel code `NONEX`** (also `NONE ` with a space, and any `NONE`
    followed by at least one further character, total length 5..8) bypasses
    the explicit `strcmp(input,"NONE")` guard and matches the reserved row 0.
    The game accepts it and then hangs on a black screen at level id 0
    (`+12` stays 0, `+10` becomes 0xFF).
  * Any valid word may carry trailing characters: `CLOUDYZ` is accepted and
    starts level 3, exactly like `CLOUDY` (these are aliases, not new levels).
* The compiled-in debug **Theme/Level/Room Select** menu is present and
  functional (`0x0801C524`, `0x0801C63E`, scene 3 at `0x080EA318`) but is cut:
  its only entry (`0x0800E7C8`) requires the front-end selection byte to be 3,
  while the menu has three items and the selector clamps at 2 (observed in
  RAM and on screen). It is dead code in the retail build.

**Deliverable code (not in any published list): `NONEX`.**
Input at Continue → Enter Password; it is accepted and the machine locks on a
black screen (reserved level 0). `NONE ` (NONE + space) is the same code in
its minimal form. Bounds and rejections: `NONE` is rejected by the guard,
`BARILE` (Italian column) is rejected in English, `ZZZZZZZZ` is rejected, and
the 8-character cap ignores further letters.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL, `-3`, under `Xvfb :342` + openbox,
`SDL_AUDIODRIVER=dummy`. Default SDL keymap: **A = `x`, B = `z`,
Start = `Return`, Select = `BackSpace`, L = `a`, R = `s`**, arrows = d-pad.

Exact path:

1. Boot. Disney Interactive → Bizarre Creations → title; press Start.
2. Main menu: **New Game / Continue / Options** (no save exists, so Continue
   is the password loader).
3. `Down` to Continue, `A` → **ENTER PASSWORD** keyboard.
4. Keyboard: `A`–`J` row 1, `K`–`T` row 2, `U`–`Z` then a cell drawn as `-`
   (this cell inserts **0x20 space**), a `←` cell (backspace), and `OK`.
   Cursor starts on `A`; d-pad moves one cell (Up/Down = ±10 with row clamp);
   `A` selects. Maximum 8 characters; on the 8th the cursor jumps to `OK`.
5. `OK` (or the automatic jump plus `A`) validates. Invalid input shows
   **INVALID PASSWORD** and stays; valid input loads the level.

RAM checks used throughout (mGBA savestate `.ss1` = PNG with a zlib `gbAs`
chunk; raw 397,312 bytes, IWRAM at 0x19000, EWRAM at 0x21000):

* `*(u32*)0x030001D4` = front-end object pointer (EWRAM).
  * `+0xA8` = input buffer (ASCII, zero-initialised)
  * `+0xD4` = input length (u32)
  * `+1` = cursor index while typing / accepted row afterwards
  * `+0` = state (0 main menu, 1 options, 2 password/level transition)
* `0x030000E0` global: `+10` fade flag (0xFF = black), `+12` level id,
  `+14` theme id, `+15` language id (0 = English default).

Savestates: `Shift+F1` saves, `F1` loads. Put a clean state on the password
screen in slot 2 and a per-test state in slot 1.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x03CC9C` | `none` sentinel string |
| `0x03CCA4` | first real password string (`Mushroom`) |
| `0x03D118` | last password string (`Remos`) |
| `0x0E9B34` | password pointer array, 156 × u32 (26 rows × 6 columns), ends 0x0E9DA3 |
| `0x080E9B34` | same array as a ROM pointer (literal loaded by validator/display) |
| `0x0800E20E` | password-entry screen handler (keyboard input + validation copy) |
| `0x0800E300`–`0x0800E380` | keypad handling: letter insert, space, backspace, max-length test (`cmp r1,#7; bgt` at 0x0800E31C) |
| `0x0800E568` | space cell writes `0x20` |
| `0x0800E594` | backspace cell deletes last character |
| `0x0800E5E8` | OK/accept path, contains the screen-side validator |
| `0x0800ECA8` | standalone validator (same algorithm): input ptr in r0, returns row 0..25 or 0xFFFFFFFF |
| `0x0800ECCE` | literal `0x0803D120` = `"NONE"` guard string |
| `0x0800ECD2` | `bl 0x08030154` — `strcmp` (optimised, case-sensitive) |
| `0x0800ECDE` | table base `0x080E9B34` literal |
| `0x0800ECE8` | `bl 0x080301B4` — `strlen` |
| `0x0800ED1A`–`0x0800ED30` | byte compare with `-0x20` case fold |
| `0x0800ED16` / `0x0800ED02` | return row / return −1 |
| `0x0800E6E8` | front-end transition controller (state 2 = start level; writes `+12`) |
| `0x0800E73E` | level-start path: `0x0801B954(row)`, `0x0801B9A0(row)`, `0x0801B9E4(row)`, store row at `0x030000E0+12` |
| `0x030000E0` | global state block (IWRAM) |
| `0x030001D4` | pointer to the front-end/password object |
| `0x0801B954` / `0x0801B9A0` / `0x0801B9E4` | row → chapter/room/level setup |
| `0x080EA3AC` | level chapter table (4 pointers: 0x083950B4, 0x0850099C, 0x085ECE44, 0x08698444; u16 count at +2) |
| `0x080EA3CC` | 8-byte per-row metadata used by the start path |
| `0x08007C44` | password display: draws `table[6*level + (lang?lang-1:0)]` at (120,100) — "Next Level Password" screen |
| `0x0801C296` | language-byte store: `strb r1,[0x030000E0,#15]`, value = 1 + row + 3*col |
| `0x0801BE14` | language-select screen init (scene 4 first entry) |
| `0x0801C2DC` / `0x0801C33C` | language-select scene sub-functions |
| `0x080EA2E8` | scene descriptor table, 9 records × 16 bytes (four Thumb `\|1` function pointers) |
| `0x08016764` | scene scheduler; rejects id > 8, enqueues `0x080EA2E8 + id*16` |
| `0x080EA318` | scene 3 = debug Theme/Level/Room Select |
| `0x080EA328` | scene 4 = language select (never queued) |
| `0x0801C524` | debug "Theme Select" menu |
| `0x0801C63E` | debug "Level Select" / "Room Select" menu (draws `Level Select`, `Room Select`, `%d`) |
| `0x0800E7C4`–`0x0800E7CC` | only scene-3 entry: `if selection == 3 → scene 3` |
| `0x030000E0+15` | language id observed 0 in every USA-build screen |

## 5. Algorithm

### 5.1 Validation (reimplementation, exact)

```python
# table[row][col] = ROM string at *(u32*)(0x080E9B34 + (row*6+col)*4)
# input: NUL-terminated uppercase ASCII buffer, length <= 8
def validate(inp, lang):
    col = 0 if lang == 0 else lang - 1
    if strcmp(inp, "NONE") == 0:          # exact, case-sensitive, 0x08030154
        return -1
    for row in range(26):                 # 0..25 inclusive
        s = table[row][col]
        n = strlen(s)                     # 0x080301B4
        match = True
        for i in range(n):                # NOTE: input length is never checked
            c = s[i]
            if ord(c) > 0x60: c = chr(ord(c) - 0x20)   # case fold table side
            if i >= len(inp) or inp[i] != c:
                match = False; break
        if match:
            return row
    return -1
```

Evidence: `0x0800ECA8` (standalone) and `0x0800E5E8` (screen copy) implement
this literally; the loop stride is 0x18 bytes (`adds r5,#24`) = six pointers,
so the row advances while the column stays fixed; the column starts at
`(lang-1)*4`, and `lang==0` is clamped to column 0 by the `blt`/`movs r4,#0`
path at `0x0800ECDA`/`0x0800ED3A`.

### 5.2 Row → level

The accepted row is written to the front-end object (`+1`), then the
transition controller's state-2 path runs:

```
row   = object[1]
level = row                       # 0x030000E0+12
theme = row_meta[row] (+3, +5)    # 0x080EA3CC, passed to 0x080162B0
0x0801B954(row); 0x0801B9A0(row); 0x0801B9E4(row)
```

Observed mapping: row 2 → user level 1 (Montressor/Police Station intro),
row 3 → user level 2 (Mines intro), row 4 → user level 3 (Iron Works),
row 24 → user level 23 (Treasure Planet interior). RAM after load:
`+12 = row`, `+14 = theme`.

### 5.3 Why only English is usable in this build

The language byte is read at `0x030000E0+15` by the validator and by the
password display. The only store to it found in code is `0x0801C296`, inside
the language-select screen whose scene is descriptor 4 at `0x080EA328`
(stored as `{0x0801BE15, 0x0801C10D, 0x0801C2DD, 0x0801C33D}`, Thumb `|1`
pointers). `0x08016764` bounds scene ids at 8; its 22 call sites pass a
literal r0 of 0,1,2,3,5,6,7 or 8. Scene 4 is never queued, and the two Options
menus expose no language item (Music/SFX/Credits; pause: SFX/Music). In the
USA image `+15` reads 0 on every screen tested. The English column is then
column 0, and the 23 English words are the whole usable code set (plus the
reserved-row bypass below).

## 6. Tables

### 6.1 Complete ROM password table (26 rows × 6 columns)

Rows 0, 1 and 25 are `none` in every column and are reserved. Rows 2..24 are
the 23 stages. Columns: EN, IT, DE, FR, NL, ES — the order matches the
language-name strings at `0x03D228` and the offsets used by the language
screen. The published GameFAQs six-language list matches this table
**138/138** (verified literal by literal).

| user lvl | row | stage (published label) | EN | IT | DE | FR | NL | ES |
|---:|---:|---|---|---|---|---|---|---|
| 1 | 2 | Police Station | Mushroom | Barile | spacekid | butin | Piraten | Ancla |
| 2 | 3 | Mines | trumpet | Pianeta | pelsinor | cachette | Kapitein | Babor |
| 3 | 4 | Iron Works | cloudy | Tesoro | hawkins | caisse | Stuurman | Bote |
| 4 | 5 | Old Forest | rabbit | Portale | morph | canon | Herberg | Catalejo |
| 5 | 6 | Smugglers Caves | sunshine | Nave | scroop | tonneau | Buit | Crucero |
| 6 | 7 | Cave Exit | spider | Spazio | zandaria | carte | Schat | Estrella |
| 7 | 8 | Crescentia | apron | Universo | localex | chambre | Procyon | Estribor |
| 8 | 9 | Tavern | rainbow | Stella | robot | coffre | Kristal | Flotar |
| 9 | 10 | Docks | goose | Pianeta | jimbo | coque | Solar | Fondear |
| 10 | 11 | Warehouse | england | Miniera | amelia | cristal | Ruimte | Galaxia |
| 11 | 12 | Sewers | mountain | Giungla | pantheon | espace | Zon | Galerna |
| 12 | 13 | Legacy | captain | Taverna | surf | rocher | Avontuur | Grumete |
| 13 | 14 | Cargo Hold | snowman | Ladro | solar | galion | Aarde | Meteoro |
| 14 | 15 | Crew Quarters | witches | Capitano | legacy | gemme | Melkweg | Navegar |
| 15 | 16 | Asteroid | monkey | Pirata | ben | grenade | Dubloen | Rumbo |
| 16 | 17 | Engine Room | princess | Caverna | sarah | huile | Schip | Oleaje |
| 17 | 18 | Treasure Planet | window | Energia | pigors | jeton | Heelal | Periplo |
| 18 | 19 | Pirate Camp | coconut | Surf | oxy | mines | Legacy | Pirata |
| 19 | 20 | BEN's House | football | Robot | portal | moteur | Sterren | Planeta |
| 20 | 21 | Jungle | concrete | Sole | plasma | pique | Robot | Popa |
| 21 | 22 | Cave | elephant | Vela | cyborg | piste | Vriend | Proa |
| 22 | 23 | Flint's Trove | phantom | Laser | procyon | planche | Sleutel | Quilla |
| 23 | 24 | Escape | dragon | Moneta | yellato | police | Gevaar | Remos |

The only shadowed entry is Italian row 10 (`Pianeta`, the Docks), which is
identical to Italian row 3 (`Pianeta`, the Mines); the first-match loop returns
row 3. This exactly reproduces the published FAQ's "Note 1" (the Italian Docks
password takes you to the Mines).

### 6.2 Keyboard alphabet

| index | cell | effect |
|---:|---|---|
| 0..25 | `A`..`Z` | append uppercase letter |
| 26 | drawn `-` | append 0x20 (space) |
| 27 | `←` | delete last character |
| 28 | `OK` | validate / accept |

### 6.3 Reserved / special rows

| row | column string | reachable? | effect |
|---:|---|---|---|
| 0 | `none` | only by guard bypass (`NONE` + char) | level id 0 → black screen/hang |
| 1 | `none` | no (identical to row 0, first match wins) | — |
| 25 | `none` | no (identical, first match wins) | — |

## 6b. Enumeration

**Space definition.** Table: 26 rows × 6 columns = 156 pointer slots, 138 of
them non-`none` strings. Input alphabet: 27 symbols (A–Z + space), length
1..8 (the 8-character cap is enforced at `0x0800E31C`; an existing 8-char
buffer ignores further letters — observed). Raw input space
`27^1 + … + 27^8 = 293,292,210,960` strings.

**Reachable space in this USA ROM.** Language byte is fixed at 0 → column 0.
Because validation is a prefix test with no input-length check, the accepted
inputs are:

* 23 English canonical codes and every extension of them with up to
  `8 − len(word)` trailing characters (A–Z/space): 45,653 strings;
* the reserved-row family `NONE` + 1..4 further characters (length 5..8):
  551,880 strings;
* exact `NONE` (4 chars) is rejected by the guard.

Total accepted strings: **597,533**; 23 playable level payloads + 1 reserved
payload (row 0) = 24 distinct row results. Rows 1 and 25 cannot be returned.
The other five language columns (115 words) are present and correct but
unreachable in this build (scene 4 is never scheduled; `+15` never leaves 0).

**Novel codes (not in GameFAQs, VGChartz, TCRF or the FAQ's six-language
list).** These exercise the reserved row 0, which no published list contains:

| code | typed | observed effect | RAM proof |
|---|---|---|---|
| `NONEX` | N O N E X | accepted (no INVALID message), fades to black, frame output freezes (identical frame hashes over 6+ s and after key presses) | `+10 = 0xFF`, `+12 = 0`, `+14 = 6`; front-end object cleared; later the global block reads all-zero |
| `NONE ` | N O N E space | same | same |

Minimal reproducible entry: Continue → Enter Password → type `NONEX` →
OK. The game never reaches a playable level; it hangs at reserved level id 0.
This is a real acceptance, not a rejection: the INVALID path was observed for
`NONE`, `BARILE` and `ZZZZZZZZ`, while `NONEX`/`NONE ` leave the password
screen and enter the level transition.

**Alias demonstration (not a new payload).** `CLOUDYZ` (7 chars) is accepted
and starts user level 3, identical to the published `CLOUDY`; RAM
`+12 = 4`, `+14 = 2`, global frame/level state identical to the `CLOUDY`
path. This proves the missing input-length equality check; the extension
suffix is unconstrained (27^k spellings for k extra characters), so these are
aliases, not distinct codes.

**Bounds proven by rejection (all entered on the real screen):**

| input | result | reason |
|---|---|---|
| `NONE` | INVALID PASSWORD, stays on screen | exact guard `strcmp(input,"NONE")` at `0x0800ECD2` |
| `BARILE` (Italian row 2) | INVALID PASSWORD | validator reads column 0 in English; column 1 is unreachable here |
| `ZZZZZZZZ` | INVALID PASSWORD | no table entry has that prefix |
| 9th letter after 8 chars | ignored, buffer unchanged | cap at `0x0800E31C`; cursor auto-jumps to OK at 8 |
| `NONEX` / `NONE ` | accepted → black/hang | guard bypass + reserved row 0 |

**Published-list verification.** All 138 six-language words were searched as
literals in the image and all 138 are present at the table addresses above;
all 23 English words are in both the GameFAQs password list and VGChartz.
The published FAQ's Italian-Docks duplicate is reproduced by the ROM's
first-match loop. Sources: GameFAQs FAQ 20558 (`Password List` by Shdwrlm3,
v1.1, 15 Dec 2002, archived 30 Dec 2018) and the GameFAQs GBA cheats page
(archived 6 May 2023), plus the VGChartz GBA cheats page. TCRF returned only
its PlayStation 2 article for this title (direct GBA fetch 403; the PS2 page
documents a debug level select on that SKU, consistent with the cut GBA debug
scene found here). The only other
published GBA cheats on the GameFAQs page are two GameShark/RAM-write codes
(`0300021063`, `0300021305`), which are memory-edit codes and out of scope for
this engagement; they are not in-game cheats and are excluded here.

## 7. Validation evidence

**Observed (emulator, mGBA 0.10.5):**

* Main menu `New Game / Continue / Options`; Options `Music / SFX / Credits`;
  pause `PARTS 0 of 3`, `Continue / Options / Quit`; pause Options
  `SFX / Music`. No language entry, no gallery/sound test.
* Continue → ENTER PASSWORD keyboard. `MUSHROOM` starts level 1
  (Montressor/Police Station intro); `TRUMPET` starts level 2 (Mines intro,
  `+12 = 3`); `DRAGON` starts level 23 (`+12 = 0x18`).
* RAM after `MUSHROOM`: global `0x030000E0` bytes
  `... 02 00 02 00` at +12/+14/+15 → level 2 (row), theme 2, language 0.
  After `DRAGON`: `+12 = 0x18` (24), `+14 = 6`.
* `CLOUDYZ` accepted → `+12 = 4`, `+14 = 2` (level 3), same as `CLOUDY`.
* `NONEX` / `NONE ` accepted → transition starts, screen goes black, no
  further frame changes; `+10 = 0xFF`, `+12 = 0`, `+14 = 6`, front-end object
  zeroed.
* `NONE`, `BARILE`, `ZZZZZZZZ` → INVALID PASSWORD; password screen remains.
* Main-menu selection byte (`object+1`) walks 0→1→2 and clamps at 2; Up from 0
  stays 0; horizontal input does nothing.

**Derived (instruction-level):**

* Validator model and guard at `0x0800ECA8` / `0x0800E5E8`; exact `strcmp`
  at `0x08030154`; `strlen` at `0x080301B4`; case fold at `0x0800ED1A`.
* Table layout, 26×6 pointer array, row stride 0x18 in the validator loop.
* Language byte store at `0x0801C296`; language-select scene 4 at
  `0x080EA328`; scene scheduler `0x08016764` with bound id ≤ 8; all call
  sites use ids ≠ 4.
* Debug scene 3 (`0x080EA318`) implements Theme/Level/Room Select; entry
  branch at `0x0800E7C4` needs selection == 3; the menu's item count is 3.
* Password display at `0x08007C44` indexes
  `table[6*level + (lang ? lang-1 : 0)]`.

**Inferred:**

* The level-complete screen shows the *next* level's password: the display
  routine indexes the level id currently in `+12`, and the level-complete
  flow is expected to advance `+12` before queuing scene 6
  (`0x0802AD52`). Not exercised end-to-end (no level was completed).
* Row 0's hang is caused by the level-start path receiving an unused level id
  (chapter/level lookup returns an invalid pointer); the exact faulting
  instruction was not traced.

## 8. Unknowns

* The exact hang site for reserved row 0 (black screen, no frame updates);
  the acceptance itself is proven.
* Behaviour of the level-complete "Next Level Password" display and the
  game-over "Password" display were not exercised dynamically.
* The European build was not available: its language-select scene 4 is
  present here but dead; the published FAQ implies the EU build exposes it
  and accepts the other five columns. This report covers the USA image only.
* Origin of the rebuilt header (complement/checksum mismatch); game content
  appears stock.
* Whether any other dump/revision changes the menu item count or table
  contents; all addresses here are for the SHA-256 above.

## 9. Tooling

* `mgba 0.10.5` (SDL, `-3`), `Xvfb :342`, openbox, `xdotool`, ImageMagick
  `import`, `SDL_AUDIODRIVER=dummy`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000
  -M force-thumb` for all disassembly.
* Python 3: table extraction from `0x0E9B34`, offline validator model,
  138-entry round-trip check, enumeration counts; savestate reader
  (`tp.ss1` PNG → zlib `gbAs` → IWRAM at 0x19000, EWRAM at 0x21000).
* Scripts used in this engagement: `pw.py` (closed-loop keyboard driver
  reading the cursor byte from EWRAM), `case.py` (load clean slot 2, type,
  submit, screenshot, RAM dump), `enum_tp.py` (model + counts). The ROM was
  run from a copy in `/tmp/treasureplanet`; no `.sav`/`.ss*` files
  were left in the ROM folder.

No ROM, graphics, music or text assets are redistributed here; only addresses,
the algorithm, short password strings and hashes are documented.
