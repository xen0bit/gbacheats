# Disney's Magical Quest 2 Starring Mickey and Minnie (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney's Magical Quest 2 Starring Mickey and Minnie/Disney's Magical Quest 2 Starring Mickey and Minnie.gba` |
| Size | 4,194,304 bytes (0x400000), no appended data |
| Header title (0xA0) | `M&M MAGICAL2` |
| Game code (0xAC) | `AQME` (USA) |
| Maker code (0xB0) | `08` (Capcom) |
| Version (0xBC) | 0 |
| Entry word (0x00) | `0xEA00002E` (stock branch to 0x080000C0) |
| Fixed 0x96 (0xB2) | `0x96` ✓ |
| Complement (0xBD) | stored `0xC5`, computed over 0xA0–0xBC = `0xC1` |
| Header checksum (0xBE) | stored `0x0000`, computed `0x053B` |
| MD5 | `9397ee8e46cd0357d49af1cff6fd97b3` |
| SHA-1 | `85358586e818913485da97089910712adaf4eb69` |
| SHA-256 | `31e35fbd67edbbf106f7d20f8c6e885aeebf4b8803bf078f4329ac97bec18e69` |

Nintendo logo is intact at 0x04 and no second/third GBA header exists in the image. The
entry branch, logo and code are stock, so the image is not a cracktro/trainer build; the
header's complement/checksum do not match the body, which is the usual artifact of a
header rewrite (e.g. a dump tool normalising the header or replacing the title). It does
not affect execution. No trainer text, no appended payload, no code cave in the first 4 KiB.

## 2. Executive summary

**This ROM has no in-game code, password, button-cheat or debug system.** The GBA release
is a 2003 port of the 1994 SNES/Genesis game *The Great Circus Mystery*. The console
versions' 4-icon **Password** screen has no counterpart in this image: the ROM contains a
complete save/load UI and a 512-byte save, and contains no password UI, string, alphabet or
validator.

What exists, and was walked end to end:

* first-boot **language select** (ENGLISH / FRANÇAIS / DEUTSCH), persisted to the save;
* **title** with a blinking `PRESS START`;
* **main menu**: `NEW GAME` / `LOAD GAME` / `OPTIONS` (with no save data the cursor skips
  `LOAD GAME`; selectable-with-save is inferred from that disabled state);
* **player select**: `1PLAYER` / `2PLAYERS`;
* **character select**: `SELECT PLAYER` with Mickey / Minnie;
* **options**: `DIFFICULTY` (EASY/NORMAL/HARD), `HOLD/SHOOT` (A/B BUTTON, with `JUMP`
  showing the complement), `THROW` (TYPE 1/TYPE 2), `COLOR MODE` (LCD A/LCD B/TELEVISION),
  `EXIT`;
* **pause**: `CONTINUE` / `SAVE`; the save panel (`DIFFICULTY / PLAYER / SCORE / COINS`,
  `NO SAVED DATA`, `SAVE`, `EXIT`);
* **link**: `2PLAYERS` → `OPEN CONNECTION. OKAY?` (YES/NO) → connection attempt.

The only stale UI labels found are `COMING SOON` (present in all three languages at the
same table slot, never displayed by any menu) and an `OFF`/`ON` option-value pair present in
all three option-value tables with no corresponding option row. Both are leftovers, not
reachable features.

Because there is no entry surface and no stored code table, the "novel code" deliverable
(§0.2) is replaced by the bounded negative proof in §6b: the complete per-language menu
label space, the full key-mask table scan, the known-sequence literal scan, and the
published-code check.

## 3. How to reproduce

Emulator: mGBA (SDL) 3× scale under Xvfb.

```bash
Xvfb :331 -screen 0 1024x768x24 &
DISPLAY=:331 openbox &
DISPLAY=:331 SDL_AUDIODRIVER=dummy mgba -3 "<rom>.gba" &
```

Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad=arrows. Focus with `xdotool windowfocus $(xdotool search --name mGBA | head -1)`.

**Input timing is the whole reproduction risk.** The menu advances once per frame while a
direction is held and has no auto-repeat delay, so a 20 ms `xdotool keydown/keyup` moves
one row but a 40 ms hold moves two. Reproduce single steps with:

```bash
xdotool keydown Down; sleep 0.02; xdotool keyup Down
```

Menu paths verified:

1. Boot (fresh save) → `ENGLISH` → `DATA SAVED.` → attract (bus/clouds) → title.
2. Title: `PRESS START` blinks; `Start` advances (a 0.25 s Start hold at the `PRESS START`
   phase opens the main menu; a shorter tap while the text is blinked off restarts the
   attract intro instead). `A` was pressed at the title and had no effect.
3. Main menu → `NEW GAME` → `1PLAYER` → `SELECT PLAYER` (Mickey/Minnie) → intro cutscene
   (skippable with Start) → gameplay.
4. Gameplay → Start → pause (`CONTINUE`/`SAVE`) → `SAVE` → save panel.
5. Main menu → `OPTIONS`: six rows, all values cycled to both extremes (they wrap).
6. Main menu → `NEW GAME` → `2PLAYERS` → `OPEN CONNECTION. OKAY?` → `YES`.

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`).

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | ARM entry, `b 0x080000C0` | observed |
| `0x0800B810` | per-frame keypad sample: reads `KEYINPUT`, XOR `0x3FF` (active-high), stores current/previous and computes `pressed = cur & ~prev` | derived |
| `0x0800B840` | literal pool: `0x04000130` (KEYINPUT), `0x000003FF` | derived |
| `0x020332F0+0x3A` (literal at 0x0800B838) | input-slot index byte used by the sampler | derived |
| `0x0202A140` (literal at 0x0800B83C) | per-slot input records: `+0 u16 current`, `+2 u16 previous`, `+4 u16 pressed`, `+6 u16 pad` (8-byte stride) | derived |
| `0x08257B7C` (file 0x257B7C) | English UI label table, base of a 0x1D4-stride record array | observed |
| `0x0827114C` (file 0x27114C) | German UI label table, same format | observed |
| `0x08284760` (file 0x284760) | French UI label table, same format | observed |
| file `0x6E9xx–0x6F7xx` | system/save/link message bank (0x28-byte records, EN/DE/FR triplets) | observed |
| file `0x6DDC4` | ASCII `MultiSioSync010918`; `0x6DDD4` = 10-entry `u16` key-order table (Down,A,B,Select,Start,Right,Left,Up,R,L), referenced 10× from 0x080094xx–0x080096xx (SIO/multiboot library) | derived |
| file `0x100` in the 512-byte save | configuration record (language) written at first boot | observed |

UI label record format (0x1D4 = 468 bytes; 16-byte header, text at +0x10):

```
+0x00  8 bytes  00
+0x08  u8       string length
+0x09  u8       attribute (0x20/0x24/0x0C/0x28 … = font/scale selector)
+0x0A  u16      0
+0x0C  u32      file offset of the glyph bitmap for this record (e.g. 0x0006E188)
+0x10  char[]   ASCII text (accented characters substituted: `]`=Ü, `>`=É, `=`=À, `;`=Ç)
```

The records are addressed by ID through a RAM table built when a menu is displayed; a
static pointer scan for the record base finds nothing because the array is only reachable
after the menu loader runs.

## 5. Algorithm

**No validator, decoder or encoder exists in this image.** There is no input buffer,
length check, character-alphabet loop, comparison table or flag write for a code: the
menu space contains no entry surface and §6b enumerates the negative.

What does exist:

* **Text renderer.** Text objects are the 468-byte records above; the renderer copies the
  record's glyph pointer and ASCII to RAM and draws with the font selected by the attribute
  byte. Some screens (pause panel, `SELECT PLAYER`, `PRESS START` art) use baked graphics,
  which is why words such as `CONTINUE` are absent from an ASCII scan.
* **Input pipeline.** `0x0800B810` samples `KEYINPUT` once per frame, converts to
  active-high and stores three halfwords per slot (current/previous/pressed). Menus test
  the `pressed` halfword; movement is edge-driven every frame with no repeat delay.
* **Save.** EEPROM (mGBA auto-detected a 512-byte save). First boot writes 16 bytes at 0x100
  (language/config) and displays `SAVING…` then `DATA SAVED.`. In-game `SAVE` from the pause
  panel was observed to close the panel and return to the pause menu without any
  `SAVING…` overlay or data change (see §8).

## 6. Tables

### 6.1 Complete UI label table (English bank, `0x08257B7C`, IDs 0–120; labels only)

```
 0 STAGE            1 AREA             3 NEW GAME         4 LOAD GAME
 5 OPTIONS          7 1PLAYER          8 2PLAYERS        10 COMING SOON
50 ,               53 DIFFICULTY       56 HOLD/SHOOT      57 JUMP
59 THROW           60 COLOR MODE       61 EXIT            74 "  PAUSE    "
77 "    PAUSE  "   80 PRESS START      81 BUTTON          83 PRESS START
84 "BUTTON   "     86 GAME             87 OVER            89 GAME
90 OVER            92 WAIT             94 WAIT           111 HJLD
114 SAMPLE        116 "9 09"          117 "16:00"        119 "@ DISNEY"
120 PRODUCED BY CAPCOM 1994
```

German bank (`0x0827114C`): 0 STAGE, 1 AREA, 3 NEUES SPIEL, 4 SPIEL LADEN,
5 OPTIONEN, 7 `1 SPIELER`, 8 `2 SPIELER`, 10 COMING SOON, 57 SCHWIERIGKEIT,
60 GREIFEN/SCHUSS, 61 SPRINGEN, 63 WURFART, 64 FARBMODUS, 65 BEENDEN, 86 START,
88 DRUCKEN, 92 DRUCKEN, 94 GAME, 95 OVER, 100 WARTEN, 102 WARTEN, 116 YOU FAILED!,
plus the same PAUSE/DISNEY/credit entries.

French bank (`0x08284760`): 0 STAGE, 1 AREA, 3 NOUVELLE PARTIE, 4 CHARGER PARTIE,
5 OPTIONS, 7 `1 JOUEUR`, 8 `2 JOUEURS`, 10 COMING SOON, 63 DIFFICULT>E,
66 MAINTENIR/TIRER, 67 SAUTER, 69 LANCER, 70 MODE COULEUR, 71 QUITTER,
90 `APPUYER SUR`, 91 START, 93 `APPUYER SUR`, 94 START, 96 FIN DE LA, 97 PARTIE,
102 ATTENDEZ, 104 ATTENDEZ, 118 YOU FAILED!, plus credits.

There is **no** PASSWORD/CODE/DEBUG/SECRET/GALLERY/SOUND-TEST label in any of the three
tables. `COMING SOON` is the only never-displayed label; `OFF`/`ON` (options value table)
is the only never-displayed value pair. IDs 11–29 hold single glyph letters (`j`, `l`, `n`)
and IDs 50/54/55/58/68/75/78 hold spaces or punctuation used as kerning entries, which is
why the record count (49/51/49) exceeds the number of visible words.

### 6.2 Options value tables (file 0x29A6E0, EN/DE/FR)

| Row | Values (EN) |
|---|---|
| DIFFICULTY | EASY, NORMAL, HARD (wraps) |
| HOLD/SHOOT | A BUTTON, B BUTTON (JUMP always shows the other) |
| THROW | TYPE 1, TYPE 2 |
| COLOR MODE | LCD A, LCD B, TELEVISION |
| EXIT | — |
| *(unused)* | OFF, ON |

### 6.3 Published codes (SNES/Genesis only — not enterable on this SKU)

3rd party cheat index cheat pages and walkthroughs give
4-icon sequences for the 1994 console versions:

```
Haunted Circus : Mickey, Minnie, Goofy, Donald
Jungle         : Pluto, Donald, Mickey, Goofy
Haunted House  : Goofy, Donald, Mickey, Minnie
Caves          : Donald, Goofy, Pluto, Mickey
Frozen Plains  : Minnie, Mickey, Donald, Goofy
Baron's Castle : Mickey, Goofy, Donald, Minnie
```

The two 3rd party cheat index lists (GEN "Level 02–06" and SNES "1–5") are ten rows that collapse to five
of these sequences; the walkthrough adds the stage-1 row.

These are character-icon sequences on the console Password screen. This GBA image has no
such screen, no `PASSWORD` label in any language, and no character-icon alphabet table; the
GBA release notes (and the in-ROM save UI) confirm the console password was replaced by the
save feature. There is no GBA-specific published in-game code list to test.

## 6b. Enumeration

**Space definition.** The code space is empty: 0 entry surfaces, 0 alphabets, 0 lengths,
0 checksum bits, 0 table entries. The negative is bounded as follows.

**A. Menu space (all screens reached, all rows walked).**

| Screen | Rows | Result |
|---|---|---|
| Language select | 3 | ENGLISH / FRANÇAIS / DEUTSCH |
| Title | 1 | PRESS START (Start advances; A has no effect) |
| Main menu | 3 labels, 2 selectable | NEW GAME / LOAD GAME / OPTIONS; LOAD GAME skipped with no save |
| Player select | 2 | 1PLAYER / 2PLAYERS (cursor cycles 1→2→1) |
| Character select | 2 | Mickey / Minnie |
| Options | 6 | 5 settings + EXIT; every value cycled past both ends (wraps) |
| Pause | 2 | CONTINUE / SAVE |
| Save panel | 2 actions | SAVE / EXIT; `NO SAVED DATA` state |
| Link | 2 | OPEN CONNECTION. OKAY? YES / NO |
| Results screen | — | text-only table COIN/SCORE/BONUS/TOTAL (file 0x72950) |

No level-select screen exists: the complete menu inventory is the table above, and the only
stage-related labels in any language are `STAGE`/`AREA` (the in-game HUD) — there is no
stage list, warp or "level select" label. No shop exists either: no SHOP/BUY/PRICE/ITEM
label in any language; coins are pickups displayed on the results screen
(`COIN`/`SCORE`/`BONUS`/`TOTAL`).

**B. Text space (counts).**

* `strings -n 4` over the whole image: **38,339** strings.
* Keyword scan (whole image, ASCII, case-sensitive): PASSWORD 0, PASSWORT 0, KENNWORT 0,
  GEHEIM 0, `MOT DE PASSE` 0, CODE 0, CHEAT 0, DEBUG 0, TEST 0, SECRET 0, UNLOCK 0,
  EXTRA 0, GALLERY 0, GALERIE 0, MUSIC 0, MUSIK 0, SHOP 0, BUY 0, PRICE 0, ITEM 0,
  LEVEL/LEVELS 0, NIVEAU 0, CONTINUE 0 (pause text is baked art). `SOUND` occurs once,
  inside the end credits (`SOUND DESIGNER`, 0x29B437). `SELECT` occurs twice, both in
  link/difficulty messages. `STAGE`/`AREA` occur three times each (one per language, the
  in-game HUD labels); `STUFE` once, inside the German link-difficulty prompt.
* UI label record tables decoded in full: **49** EN labels, **51** DE labels, **49** FR
  labels; no code/debug/gallery label exists in any of them.
* System/save/link message bank (0x6E9xx–0x6F7xx) decoded in full: 62 distinct ASCII messages
  (connection, difficulty, saving, no-saved-data, overwrite and clear-data prompts); none
  is a password or debug screen.

**C. Button space (counts).**

* Every Thumb `LDR Rd,[PC,#imm]` in the image was decoded and its literal target collected:
  **28,137** unique literal targets. Testing each target as the start of a `u16`
  button-mask table (first entry a single-button mask, ≥3 of first 4 entries single masks)
  produced **3** candidates, all false positives on inspection (bytes `[0x200,0x202,0x001,0x200]`
  and two runs of `0x0001` inside graphics).
* `u16` runs of ≥3 consecutive single-button masks (any alignment): **198**. The only long
  ordered run is `0x6DDD4` = `80 00 01 00 02 00 04 00 08 00 10 00 20 00 40 00 00 01 00 02`
  (Down,A,B,Select,Start,Right,Left,Up,R,L), immediately after the ASCII string
  `MultiSioSync010918` and referenced 10× from the multiboot/SIO library at 0x080094xx —
  a link-cable key-order table, not a cheat table.
* Konami sequence (`Up Up Down Down Left Right Left Right B A`) is absent in both `u8` and
  `u16` encodings, in both D-pad-first and reversed forms.
* Title input: `A` was pressed at the `PRESS START` screen and produced no change (the title
  stayed up); `Start` produced the transition. The attract timer changes the screen every
  few seconds, so per-press probing of the other buttons is not attributable; the negative
  for multi-button codes therefore rests on the table scan above, not on probing.

**D. Published codes.** The published console passwords (§6.3) are 4-icon sequences: six
distinct stage sequences, appearing as ten list rows across the GEN and SNES lists
(the lists overlap). Their premise — a password screen with a character alphabet — does not
exist on this SKU (no screen, no label, no alphabet table). They are therefore not
"rejected codes"; there is nothing to type them into.

**E. Bounds proven by rejection.**

* `LOAD GAME` with an empty save: the cursor cannot be moved onto it (one Down moves
  NEW GAME → OPTIONS). Rejection is the disabled-entry behaviour.
* Options: a 4th Right/Left press wraps to the first value (3 difficulty values, 3 colour
  values, 2 throw values) — no out-of-range value is reachable.
* Options: a 7th Down press from EXIT wraps to DIFFICULTY — no hidden 7th row.
* Player select: a 3rd Down press returns to 1PLAYER — no hidden third entry (so the stored
  `COMING SOON` label is unreachable).
* Link: `YES` with no peer returns to the title without entering a lobby (no
  `CONNECTING…`/`SELECT GAME DIFFICULTY` screen without a second unit).

## 7. Validation evidence

**Observed (emulator screenshots + save file):**

* Language select, `DATA SAVED.`, title, main menu, player select, character select,
  options (all values), pause, save panel, link prompt.
* `LOAD GAME` skipped while the save panel reports `NO SAVED DATA`.
* Title: `Start` advances; `A` does not.
* Save file `mq2.sav`: 512 bytes; bytes 0x000–0x0FF and 0x110–0x1FF = 0xFF; 16 bytes at
  0x100 written by the first-boot language save.

**Derived (instruction/data analysis):**

* Key input pipeline at 0x0800B810 and its literal pool (KEYINPUT / 0x3FF).
* UI label record format (0x1D4 stride, 16-byte header, length byte at +8, text at +0x10).
* Absence of a button-mask table (28,137 literal targets, 3 false positives) and of the
  Konami literal encodings.
* 0x6DDD4 key-order table belongs to the SIO/multiboot library (adjacent
  `MultiSioSync010918`, 10 code references).

**Inferred:**

* `COMING SOON` (ID 10, all languages) was planned as a third player-select / link mode
  and is not wired into any menu (the observed player select has exactly two rows).
* The `OFF`/`ON` option-value pair belongs to a removed option row (the observed options
  screen has exactly six rows).
* The in-game `SAVE` is a no-op at the spawn point because no checkpoint has been reached;
  this is consistent with the panel returning immediately with the save data unchanged.

## 8. Unknowns

* **Why in-game `SAVE` wrote nothing.** Selecting SAVE and pressing A (or Start) closes the
  panel and returns to the pause menu with no `SAVING…`/`DATA SAVED.` overlay and no change
  in the 512-byte save; the boot-time language save does write. Whether this is a
  checkpoint gate, a save-type-detection quirk of this mGBA build, or port behaviour was not
  isolated. Consequence: the LOAD panel with real data (`OLD DATA WILL BE LOST` /
  `CLEAR ALL DATA AND RESTORE ORIGINAL STATUS` paths) was not displayed; those strings are
  present and enumerated but their screens are gated behind a valid save.
* **`COMING SOON` intent.** It may have been a third player-select entry or a link mode; no
  caller was found, and it is never drawn in the observed menus.
* **Non-ASCII UI text.** `CONTINUE`, `SELECT PLAYER` and the pause panel are baked graphics,
  so an ASCII scan cannot enumerate them; coverage rests on the screen walk.
* **Header mismatch.** Complement/checksum do not match the body; the image may be a
  header-normalised dump. Code, logo and entry are stock, so the analysis is unaffected.

## 9. Tooling

* `mGBA` (SDL) 3× under `Xvfb :331` + `openbox`; `xdotool` for XTEST input, `import`/`convert`
  for screenshots and montages, `compare -metric RMSE` to detect title vs menu.
* Python 3: header/hash parse, ASCII and keyword scans, UI record-table decoder
  (`0x1D4` stride), Capstone Thumb `LDR [PC,#imm]` literal-target scan, `u16` key-mask run
  scanner, Konami literal search.
* mGBA text savestates (`Shift+F1..F4`/`F1..F4`) used to return to the pause menu and title;
  `Ctrl+R` for reset while preserving SRAM.
* All emulator runs used a copy of the ROM in `/tmp/magicalquest2`; the ROM folder
  was left untouched (no `.sav`, no savestates).

## 10. Legal note

No ROM, graphics, music or game text beyond the short UI labels needed to document the
menus is redistributed here.
