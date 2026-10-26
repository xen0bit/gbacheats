# Avatar: The Last Airbender (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Avatar: The Last Airbender.gba` |
| Size | 8,388,608 bytes (`0x800000`, 8 MiB) |
| Header title | `AVATAR` (0xA0–0xAB, space-padded) |
| Game code | `BQZE` (0xAC–0xAF) |
| Maker code | `78` (0xB0–0xB1) |
| Fixed byte 0xB2 | `0x96` ✔ |
| Software version | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` → `0x080000C0` |
| Complement check | `0xF1` stored at 0xBD; recomputed `0xF1` ✔ |
| 0xBE–0xBF | `0x0000` (reserved field) |
| MD5 | `c19779d04914fae7268bfb8b47b8b048` |
| SHA-1 | `9d864e9b3ccce4e5e1b1c566afa0d06088e88dfd` |
| SHA-256 | `67df1edd696bfefa9f169ab03f1eca300c0efa336acf0da7fff8499d69fbe99a` |

**Embedded GBA-header scan (Phase 0).** The 156-byte Nintendo logo
(`24ffae51…21d4f807`) occurs exactly **once**, at file offset `0x4`, i.e. one
header at `0x0`. There is no second logo/header anywhere in the 8 MiB image, so
this is a single-game cartridge, not a multi-game pack, and every absolute
address below is `0x08000000 + file_offset`.

Save hardware: mGBA created an 8192-byte (8 KiB) `.sav` on first boot,
consistent with 8 KiB EEPROM (inferred; the save format itself was not part of
this engagement).

## 2. Executive summary

**This retail US GBA build has no in-game password, code-entry, cheat or
accessible debug menu.** The widely published five-digit Avatar codes
(`94677`, `53467`, `23637`, `24463`, `34743`, `54641`, `37437`, `97831`) belong
to the GameCube / PlayStation 2 / Xbox / Wii versions, not to this cartridge.
GamesRadar's platform-tagged list attributes them to “Wii” and “GameCube, PS2,
Xbox”; GBA-labelled reprints exist (e.g. miastogier.pl) but no GBA screen,
string, asset or literal in this ROM supports them.

The negative is bounded, not assumed:

* The game's **entire localized UI string table is enumerated**: 231 symbol IDs
  at ROM `0x68d4b8`. There is no `EXTRAS`, `CODE`, `CHEAT`, `PASSWORD`,
  `GALLERY`, `CONCEPT` or `BONUS` ID. The only developer/debug IDs are 17
  `DEBUG_*` strings (IDs 23–39).
* The only text-input widget in the game is the **name keypad**, whose alphabet
  is exactly `A`–`Z` (plus ABC/abc, backspace, CONTINUE). It has **no digits**.
  Pressing `9 4 6 7 7` at that screen changes nothing (Observed; screenshot
  `Avatar - name entry keypad no digits.png`). A five-digit code therefore
  cannot be expressed by any input surface in this build.
* The 8 published codes were searched under **10 encodings** each (ASCII,
  ASCII+NUL, UTF-16LE, u16/u24/u32 LE, u32 BE, packed BCD, digit-byte arrays,
  digit+`0xFF`). No two published codes are co-located within 128 bytes under
  any encoding: there is no code table.
* String search for `password`, `passcode`, `cheat`, `code entry`, `enter code`,
  `extras`, `gallery`, `concept`, `copper`, `stealth`, `treasure map` returns
  **0 case-insensitive hits** anywhere in the ROM.

What the ROM *does* contain is developer residue (in scope as “hidden/debug
menus”, but not reachable by input):

* 17 debug-menu labels in **all five language banks** — `God Mode`,
  `Level Select`, `Debug Fly (No Collision)`, `Activate all Abilities`,
  `Complete Quest`, `Key Settings`, `Play Test Mode`, `Playback Record`, etc.
  They are contiguous localization IDs 23–39 (left in English even in the
  Dutch/French/German banks) but no consumer, pointer table, gate or menu was
  found.
* A hidden **developer room select** that lists `.ro` room files and loads them.
  It is selected by game-state word `0x02001E50 = 3`, which is a RAM write.
  This is the screen TCRF documents as reachable only by a memory edit; that
  route is explicitly out of scope here and is not offered as a cheat. TCRF
  also records that a way to reach the debugging functions is still unknown.
  No in-game input sequence that reaches this state was found (35 button
  combinations tested).

Because the in-scope code space is empty, §6b enumerates the *absent* system,
the debug-text space, and the room-select set, and states the exact bound that
makes the negative reproducible.

## 3. How to reproduce

### Emulator / environment

```bash
Xvfb :149 -screen 0 1024x768x24 &
DISPLAY=:149 openbox &
DISPLAY=:149 SDL_AUDIODRIVER=dummy mgba -3 "Avatar: The Last Airbender.gba" &
W=$(DISPLAY=:149 xdotool search --name mGBA | tail -1)
DISPLAY=:149 xdotool windowfocus "$W"
```

mGBA 0.10.5 (SDL). Default keymap used throughout: **A = `x`, B = `z`,
L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrows**.
Keys held 150–300 ms; screenshots via `scrot` and cropped
`720x480+154+184` from the 1024×768 root.

### Menu paths observed

| Screen | Input path |
|---|---|
| Boot logos → attract (Aang on cliff) | wait ~25 s; no input needed |
| Title (`NEW GAME`, `OPTIONS`) | wait for attract to end |
| Title Options (`Display: Normal`, `Credits`) | `Down`, `A` |
| Credits | Title → Options → `Down` → `A` |
| Name entry (A–Z keypad) | Title → `A` (or `Start`) |
| Gameplay | name entry → `CONTINUE` |
| Pause journal (Options page) | in game, `Return` |
| Journal pages | `a`/`s` (L/R) cycle: Options → Items → Tutorials → Hint → Options |
| Quit confirm | journal → Options → `Down`×3 → `A` → `Right` → `A` |

Screenshots kept next to the ROM:

* `Avatar - title menu.png`
* `Avatar - title options.png`
* `Avatar - credits.png`
* `Avatar - name entry keypad no digits.png`
* `Avatar - journal pages.png` (all four pages)
* `Avatar - pause journal options.png`
* `Avatar - quit confirm.png`
* `Avatar - hidden room select (RAM state, not input).png`
* `Avatar - room select loaded fnp_000.png`

### Input test that matters for the codes

At the name entry screen the alphabet is `A`–`Z` only (26 letters; the `abc`
button toggles case). Pressing keyboard digits `9 4 6 7 7` produces no
character — the name stays `-` (Observed; `Avatar - name entry keypad no
digits.png` shows the same screen before and after). There is no other
text-entry widget in the game.

### Button combinations tested (35, none opened a debug menu)

* Boot, held through the logos (6; `L+R+Select+Start` was also held all the
  way through the title transition): `L+R+Select+Start`, `L+Select`,
  `R+Select`, `Select`, `L+R`, `A+B+Select+Start`.
* Title (2): `A A B L R R Start` (the PS2 invincibility sequence mapped to
  GBA), `Select` held 2 s.
* In game (13): `L+R+Select+Start`, `Select+Start`, `L+R+Start`,
  `Select+L+R`, `L+B`, `L+R+Select`, `Select`, `L+Select`, `R+Select`,
  `L+R+B`, `A+B+Select`, `Down+Select`, `Up+Select`.
* Journal (7): `Select`, `L`, `R`, `L+R`, `Select+L`, `Select+R`,
  `Select+L+R`.
* Room select (7): `Select`, `Start`, `L`, `R`, `Down`×20, `Right`, `A`.

## 4. Address map

All addresses are ROM file offsets; add `0x08000000` for the CPU address.
The localization banks are plain ASCII and are the source of the on-screen
menus (e.g. `NEW GAME` at `0x6832A8`), so keyword searches over them are
meaningful — the missing keywords are absent content, not a tile-text artifact.

| Offset | Size / layout | Meaning |
|---|---|---|
| `0x000000` | 8 MiB | ROM image, one GBA header |
| `0x260000`–`0x270000` | array of `0x7C`-byte records | asset directory: `{u32 crc32; u32 size; u32 data_offset; char name[0x70]}` |
| `0x68D4B8` | 231 × `0x24` | localization **symbol table**: `{u32 id; char name[32]}`, IDs 0–230, names alphabetical (`A_NOTYET` … `YES`) |
| `0x681F10` | 107 records | English (US) text bank #1 (help/items/quests/debug); record = `{u16 len; u16 type; char text[len]; pad 1–4}`; index 0 is an unused prefix, so ID = record index − 1 (verified for IDs 0–105) |
| `0x683178` | — | English (US) text bank #2 (frontend: `NEW GAME` at `0x6832A8`, `CONTINUE`, `OPTIONS`, file-select strings) |
| `0x682044`–`0x682178` | 17 records | English debug labels, IDs 23–39 (§6) |
| `0x67F2A4` | text start | Dutch copy of the 17 debug labels (`DOORGAAN` nearby) |
| `0x682048` | text start | English (US) copy |
| `0x684A88` | text start | second English (en-GB) copy |
| `0x6874F4` | text start | French copy (`CONTINUER`, `QUITTER` nearby) |
| `0x68A448` | text start | German copy (`WEITER` nearby) |
| `0x02001E50` | u16, EWRAM | game-state word; value `0x0003` selects the hidden room select (memory-write only; not an in-game cheat) |
| `0x080626E4`–`0x080628FF` | Thumb | frontend/state init observed writing state 15/16/21 at `0x08062790` and `0x08062816` |

Asset directory facts (Derived by parsing the `0x7C`-byte records):

* 2,484 records parsed from the `0x7C`-stride directory; **77 unique
  `interface\` path strings** (119 occurrences).
* Menu-screen `.ro` assets actually present: `credits`, `file_select_screen`,
  `language_screen`, `name_screen`, `options_screen` (plus `journal`,
  `title_screen`, `game_over`, `legal`). **No code-entry / password / extras
  screen asset exists.**
* 79 room assets (`rooms\…\*.ro`): `fnp` 15, `np` 11, `oma` 26, `sc` 21, `mf` 6.
  These are the entries the hidden room select browses.

**No code table.** There is no offset in the ROM holding the published values:
see the search matrix in §6b. No direct 32-bit pointer to `0x08681F10`,
`0x0868D4B8` or any debug label exists in the image (0 hits); the engine reaches
the language data through its pack/language layer (see §8).

## 5. Algorithm

### 5.1 Password / code-entry validator

**None exists in this build.** The reproducible model is a negative one:

```
input_surface  = { name_entry }                  # only text widget
alphabet       = 'A'..'Z'                        # 26 symbols, no digits
numeric_pad    = absent
code_screen_id = absent                          # not in the 231-ID table
code_table     = absent                          # 10 encodings × 8 codes, no co-location
```

A five-decimal-digit format has `10^5 = 100,000` strings. The representable
subset in this ROM is **0**: every code begins with a digit and no digit can be
entered. That is a stronger bound than “the code was rejected” — the code is
not expressible.

### 5.2 Debug-menu text (unused)

The debug labels are ordinary localization entries, ordered by ID:

```
record(i) at 0x681F10:  u16 len, u16 type, bytes[len], pad to 4 (1..4 bytes)
text_id = i - 1
IDs 23..39 = DEBUG_* labels, stored contiguously, in all 5 language banks
```

No code was found that reads these IDs, and no menu/asset consumes them. The
labels describe a developer test menu (fly/no-collision, god mode, level
select, quest/step completion, skills, playback record), i.e. a build-time
debug overlay, not a shipped cheat.

### 5.3 Hidden room select

`0x02001E50` is a 16-bit game-state/sub-state word. Writing `0x0003` from GDB
(analysis instrument only) switches the running game to a developer screen that
prints `.ro` room names in a grid. `Right` scrolls the list horizontally,
`Down` moves by row, `A` loads the selected room (Observed: `np_000.ro` and
`fnp_000.ro` loaded). This is the same screen TCRF documents as reachable only
by a RAM edit. It is not an in-game cheat and no button sequence in this build
reaches state 3.

## 6. Tables

### 6.1 Published five-digit codes (all console-only for this build)

| Code | Published effect (console versions) | Present as GBA literal? |
|---|---|---|
| 94677 | Infinite health | no |
| 53467 | Infinite stealth | no |
| 23637 | Infinite copper | no |
| 24463 | Infinite Chi | no |
| 34743 | Double damage | no |
| 54641 | One-hit dishonor | no |
| 37437 | All treasure maps | no |
| 97831 | Character concept gallery | no |

The GBA password lists found online use a 3×3 character grid (Aang, Zuko,
Toph, Katara, Sokka, Iroh, Momo) and belong to the **sequel**, *The Burning
Earth* (VGChartz/GameRevolution list them under that title). No equivalent
screen, text ID or asset exists in this ROM.

### 6.2 Debug labels: IDs, English text, file offsets

| ID | Symbol | English text | Record offset |
|---:|---|---|---:|
| 23 | DEBUG_ALL_ABILITIES | Activate all Abilities | `0x682044` |
| 24 | DEBUG_COMPLETE_QUEST | Complete Quest | `0x682060` |
| 25 | DEBUG_COMPLETE_STEP | Complete Quest Step | `0x682074` |
| 26 | DEBUG_FLY | Debug Fly (No Collision) | `0x68208C` |
| 27 | DEBUG_GODMODE | God Mode | `0x6820AC` |
| 28 | DEBUG_INVENTORY | Select Inventory | `0x6820BC` |
| 29 | DEBUG_KEYS | Key Settings | `0x6820D4` |
| 30 | DEBUG_LEVEL_SELECT | Level Select | `0x6820E8` |
| 31 | DEBUG_OFF | OFF | `0x6820FC` |
| 32 | DEBUG_ON | ON | `0x682104` |
| 33 | DEBUG_PLAY | Play Test Mode | `0x68210C` |
| 34 | DEBUG_PLAYBACK_RECORD | Playback Record | `0x682120` |
| 35 | DEBUG_QUEST | QUEST | `0x682134` |
| 36 | DEBUG_SKILLS | Select Skills | `0x682140` |
| 37 | DEBUG_STEP | STEP | `0x682154` |
| 38 | DEBUG_UNCOMPLETE_QUEST | UnComplete Quest | `0x682160` |
| 39 | DEBUG_UNCOMPLETE_STEP | UnComplete Quest Step | `0x682178` |

Copies of the whole 17-entry block exist at `0x67F2A4` (Dutch), `0x684A88`
(en-GB), `0x6874F4` (French), `0x68A448` (German). “Record offset” is the start
of the `{u16 len; u16 type}` header; the text itself begins 4 bytes later. The
`DEBUG_*` names themselves occur once each in the 231-entry symbol table.

### 6.3 Localization ID space (231 IDs)

| Prefix group | Count | Examples |
|---|---:|---|
| `HELP_*` (journal hint text) | 38 | `HELP_0_1`, `HELP_12_3` |
| `SCROLL_*` / `SCROLL_DESC_*` | 22 | `SCROLL_1`, `SCROLL_DESC_11` |
| `TUTORIAL_*` | 20 | `TUTORIAL_00`, `TUTORIAL_18` |
| `BUTTON_*` | 18 | `BUTTON_A`, `BUTTON_DPAD` |
| `DEBUG_*` (developer) | 17 | `DEBUG_GODMODE`, `DEBUG_LEVEL_SELECT` |
| `RECEIVED_*` (item pickups) | 17 | `RECEIVED_00`, `RECEIVED_GOLD_KEY` |
| `QUEST_*` | 13 | `QUEST_0`, `QUEST_12` |
| `ITEM_*` / `ITEM_DESC_*` | 12 | `ITEM_1`, `ITEM_DESC_6` |
| `JOURNAL_*` | 9 | `JOURNAL_PAGE_OPTIONS` |
| `FS_*` (file select) | 7 | `FS_TITLE`, `FS_OVERWRITE_CONFIRM` |
| `OPTIONS_*` | 6 | `OPTIONS_MUSIC`, `OPTIONS_DISPLAY` |
| `LANGUAGE_*` | 5 | `LANGUAGE_ENGLISH` |
| `ROOM_NAME_*` | 5 | `ROOM_NAME_OMASHU` |
| other (menus, states, confirmations) | 42 | `NEW_GAME`, `CONTINUE`, `QUIT_CONFIRM` |

Grep of this table: `EXTRA` 0, `GALLERY` 0, `CONCEPT` 0, `PASSWORD` 0,
`CHEAT` 0, `CODE` 0, `SECRET` 0, `BONUS` 0; `UNLOCK` 1 (`DOOR_UNLOCKED`).

## 6b. Enumeration

### 6b.1 Documented code space vs. representable space

* Published format: **5 decimal digits**, `10^5 = 100,000` possible strings;
  8 values documented (8/100,000 ≈ 0.008 % sampled).
* Input surfaces in this ROM: **1** (name entry). Alphabet `A`–`Z` (26) plus
  case toggle/backspace/CONTINUE; **0 digit glyphs**.
* Representable five-digit strings: **0**. A published code cannot be typed at
  any screen, therefore no acceptance/rejection can occur inside this build.
* Searched for a numeric keypad/entry screen: 77 unique `interface\` path
  strings, 5 menu-screen `.ro` assets, 231 localization IDs — **zero** matches
  for a code/password/extras screen or label.

### 6b.2 Published-code presence search (per encoding, match count in 8 MiB)

| code | ASCII | ASC+NUL | UTF16LE | u16LE | u24LE | u32LE | u32BE | BCD-BE | digit-bytes | digit+FF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 94677 | 0 | 0 | 0 | – | 0 | 0 | 0 | 0 | 0 | 0 |
| 53467 | 0 | 0 | 0 | 103 | 3 | 0 | 0 | 1 | 4 | 0 |
| 23637 | 0 | 0 | 0 | 55 | 2 | 0 | 1 | 0 | 0 | 0 |
| 24463 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 1 | 0 | 0 |
| 34743 | 0 | 0 | 0 | 14 | 0 | 0 | 0 | 0 | 1 | 1 |
| 54641 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 2 | 2 | 1 |
| 37437 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 2 | 0 | 0 |
| 97831 | 0 | 0 | 0 | – | 0 | 0 | 0 | 0 | 0 | 0 |

ASCII, UTF-16, u32 and NUL-terminated forms: **0 hits for every code**. The
u16/u24/BCD/digit counts are isolated coincidences inside graphics and code
(no two codes within 128 bytes under any encoding). Conclusion: **no code
table, no validator constants**.

### 6b.3 Debug-menu text space

* 231 localization IDs; 17 debug IDs (23–39); 5 language copies = 85 debug
  strings stored.
* Consumers found: **0**. No pointer to the text bank, the symbol table or any
  debug label exists in ROM; no menu asset for them exists.
* In-game gate found: **0** (35 button combinations, every reachable menu).
* The 17 effects are therefore *named but not observed*; they are enumerated
  in §6.2 and labeled Derived-from-text only.

### 6b.4 Hidden room-select enumeration

* Trigger: state word `0x02001E50 = 0x0003` (RAM write; **not** an in-game code,
  and not offered as a cheat). TCRF documents the same screen as reachable only
  by a RAM edit (memory-edit; out of scope for this report).
* Contents: room `.ro` names grouped by area. Visible first page (Observed):
  `np_000.ro … np_003.ro`, `fnp_000.ro … fnp_003.ro`, `oma_000.ro … oma_003.ro`,
  `sc_000.ro … sc_003.ro`, `mf_000.ro … mf_003.ro`; `Right` scrolls the columns.
* Full selectable set (Derived from the pack directory): **79 rooms** —
  `fnp` 15, `np` 11, `oma` 26, `sc` 21, `mf` 6. Loading `np_000.ro` and
  `fnp_000.ro` was confirmed in the emulator (screenshot).
* Novel codes minted: **none possible** — this screen has no code field, and the
  game has no validator.

### 6b.5 Bottom line

The in-scope code space of this cartridge is **empty**:

| Quantity | Value |
|---|---|
| Password/code entry screens | 0 |
| Numeric input surfaces | 0 |
| Published codes representable | 0 / 8 |
| Published codes found in ROM | 0 / 8 |
| Code tables / checksum constants | 0 |
| Accessible debug menus | 0 |
| Debug label strings present (5 languages) | 85 |
| Rooms in the hidden dev browser | 79 |

## 7. Validation evidence

**Observed (emulator/screenshots):**

* Title has exactly `NEW GAME` and `OPTIONS`; title Options has `Display` and
  `Credits`; no Extras.
* Name entry keypad is A–Z only; digit keys (tested `9 4 6 7 7`) do nothing.
* Pause journal has exactly four pages (Options, Items, Tutorials, Hint) and
  cycles back; the Options page has Music, Sound, Swap Type, Quit.
* Credits screen exists and scrolls (Halfbrick Studios first).
* Quit confirm is `NO`/`YES`, and Yes returns to the attract/title.
* Hidden room select renders `.ro` names; D-pad moves, A loads the room.
* 35 button combinations produced no debug menu.

**Derived (static):**

* 231-entry localization table, IDs and names exactly as listed.
* 17 debug labels ordered by ID in 5 language banks; no consumer/pointer.
* No code table: 10 encodings × 8 codes, no co-location.
* 77 unique interface paths, no code/extras screen; 79 room assets.

**Inferred:**

* The five-digit codes are console-version content; the GBA release dropped the
  Extras/Code Entry screen (supported by GamesRadar's platform tagging and by
  the complete absence of the strings/assets).
* The 8 KiB `.sav` is EEPROM.
* The debug text is build residue from the engine's developer menu, compiled
  into the localization file but not wired to any shipped screen.

## 8. Unknowns

* **Where the debug menu lives.** Its 17 labels are present (English text) in
  all five language banks, but no gate, consumer, pointer or menu asset was
  found. TCRF also lists “find a way to access the debugging functions” as a
  to-do for this ROM. It may only exist in a development build of the engine.
* **Text-layer wiring.** The language banks at `0x681F10` and the symbol table
  at `0x68D4B8` have no direct 32-bit pointer in ROM; the engine presumably
  resolves them through the pack/language layer. This does not affect the
  negative (the visible menus demonstrably come from this table), but the
  accessor was not located.
* **File-select / language-select screens.** These assets and IDs exist
  (`FS_TITLE`, `LANGUAGE_*`) but require a valid save or an EU build to reach;
  they were not entered. The 231-ID enumeration proves neither contains a code
  entry label.
* **Regional builds.** Only the US Rev.00 `BQZE` image was analyzed. An EU
  `BQZP`/`BQZX` build could differ; nothing in the published console code lists
  suggests a GBA code screen.
* **Room-select completeness on-screen.** The 79-room set is derived from the
  pack directory and the screen was exercised on its first page; every column
  was not scrolled to the end.

## 9. Tooling

* mGBA 0.10.5 (SDL), Xvfb `:149`, openbox, `xdotool`, `scrot`,
  ImageMagick `convert`/`montage`.
* GNU binutils `arm-none-eabi-objdump` (Thumb), Capstone 5.0.7,
  `gdb-multiarch` against mGBA's GDB stub (memory dumps, one RAM state write
  used only to observe the developer room screen).
* Helper scripts (analysis only, not part of the deliverable):
  `/tmp/opencode/avatar/h.py` (keys/screenshots), `combo.py`,
  `bootcombo.sh`, `statetest.sh`.
* All screenshots in this folder were taken from the running ROM; no ROM data
  or copyrighted assets are redistributed in this report.

References used for the public-code comparison:

* GamesRadar, “Avatar: The Last Airbender Cheats” (platform-tagged code list):
  `https://www.gamesradar.com/avatar-the-last-airbender/cheats/`
* TCRF, “Avatar: The Last Airbender (Game Boy Advance)” (debug text at
  `0x67F2A4`; room-select RAM-edit note):
  `https://tcrf.net/Avatar:_The_Last_Airbender_(Game_Boy_Advance)`
* GameFAQs GBA cheats page returned HTTP 403 to direct fetch; search snippets
  were used only for cross-checking, and every code was verified against the
  ROM rather than trusted from the web.

## 10. Legal note

No ROM, graphics, music or text assets are redistributed. Only hashes,
addresses, derived tables, and the report's own screenshots of menu states are
published here.
