# Disney's Magical Quest 3 Starring Mickey & Donald (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Disney's Magical Quest 3 Starring Mickey & Donald.gba` |
| Size | 8,388,608 bytes (8 MiB / 64 Mbit mask ROM) |
| Used content | 0x000000–0x4207AD (4,326,830 bytes); 0x4207AE–0x7FFFFF is 0xFF padding |
| Header title (0xA0) | `M&D MAGICAL3` |
| Game code (0xAC) | `BMQE` (Europe) |
| Maker (0xB0) | `08` (Capcom) |
| Version (0xBC) | `00` |
| Complement (0xBD) | `0xCC` — **verified correct**: `-(0x19 + sum(0xA0..0xBC)) & 0xFF = 0xCC` |
| Header checksum (0xBE) | `0x0000` (unused field; normal) |
| Entry word | `0xEA00002E` (stock ARM branch to 0x080000C0) |
| MD5 | `47fe0fe1ee054ac37e286fb909e49be0` |
| SHA-1 | `6fd2ffe2f1ffc25f27fae00631ab7733d08f86ea` |
| SHA-256 | `28ce9d2e800b54c0f6a580e2193c23f80b6e2567890bb9048901a3ff8f163d6c` |

**Image integrity (Phase 0).** A full-image scan for the 156-byte Nintendo logo
(`24 FF AE 51 69 9A A2 21 …`) returns exactly **one** hit, at file offset 0x04 —
there is no second/embedded GBA header, no 2-in-1 shell, no appended trainer
menu. The entry word is the stock `b 0x080000C0`, not a cracktro branch, and the
header complement check is valid. **No patch or trainer is present**; the image
is a retail build.

## 2. Executive summary

This GBA release is a save-based remake of the 1995 Super Famicom game. It has
**no in-game code system of any kind**: no password screen, no button code, no
hidden/debug menu, no unlockable entry.

Evidence chain (details in §6b):

* The complete UI string inventory (26 pointer tables, §6) contains no
  `PASSWORD`/`CHEAT`/`DEBUG`/`SECRET`/`STAGE` label in ASCII, in the `+0x20`
  text bank, or in any pointer table; the only menus are the data-select menu
  (4 entries), the player-select menu (2), the options screen (6 rows), the
  party-game menu (3 entries), the battle list (3 + EXIT), the records screen and
  the pause/status screen (4 rows).
* The main menu is a fixed 4-entry table at `0x0823D71C`. Writing its cursor
  byte (`0x02025672`) with 0…9 and pressing A reaches only existing screens
  (0…3 the four entries; 4, 6…9 OPTIONS; 5 the party battle list) — no unknown
  screen, hence no fifth entry (§6b).
* All seven published *stage passwords* are SNES-era, 4-name sequences
  (3rd party cheat indexes/visualboyadvance/3rd party cheat index list them for the SNES SKU). An exhaustive
  consistency scan for the 28-symbol sequence (byte and u16 encodings, any
  bijective symbol→value map) returns **0 hits** anywhere in the 8 MiB image.
* Losing all lives returns to the title screen; no password/continue-code screen
  appears at death or at game over (observed, §6b).
* The SNES debug flag (`$7E00FE`, 3rd party cheat indexes) and its debug UI (`1 Player / 2 Player /
  2 Players`, OBJECT VIEWER, V-RAM DUMP, COLOR CHECK, MAP ATARI, SOUND TEST) were
  **not ported**: none of those strings or screen objects exist in the image, and
  the SNES flag's WRAM offset mirrored into GBA RAM (`0x020000FE`) has no effect.

The one genuine "developer artefact" that survives is cosmetic: the OPTIONS
screen still carries the SNES display setting **COLOR MODE: LCD A / LCD B /
TELEVISION** (meaningless on a GBA), alongside HOLD/SHOOT and JUMP/THROW button
remapping.

Magical Quest 2 (analysed in a parallel job) shares the same publisher and a
similar menu style, but **no table, address or conclusion here was taken from
that job**; every address in this report was read from *this* image.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL, `/usr/local/bin/mgba`), headless
`Xvfb :332 -screen 0 1024x768x24` + `openbox`, `SDL_AUDIODRIVER=dummy`,
`mgba -3 <rom>`.

Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows. Hold keys 100–250 ms; menus accept one step
per press and need ~0.5 s between presses during transitions.

Menu paths (all screens walked):

```
boot → language select (ENGLISH / FRANÇAIS / DEUTSCH)      [A on language]
     → city intro (Start ×6 to skip)
     → title: logo + PRESS START
Start → data select: NEW GAME / LOAD GAME / OPTIONS / PARTY GAME
  NEW GAME  → player select: 1 PLAYER / 2 PLAYERS → intro → Stage 1 (in game)
  LOAD GAME → loads the EEPROM save and resumes at the saved checkpoint
  OPTIONS   → DIFFICULTY / HOLD-SHOOT / JUMP / THROW / COLOR MODE / EXIT
  PARTY GAME→ 1PLAYER / 2PLAYERS / VIEW RECORDS
              1 PLAYER   → KNIGHT BATTLE / WOODSMAN BATTLE / MAGICIAN BATTLE / EXIT
              2PLAYERS   → same battle list (link play)
              VIEW RECORDS → battle records (KNIGHT/WOODSMAN/MAGICIAN, TOP TIME,
                             COMPUTER/PTS/WIN/LOSS, MICKEY/DONALD)
in game: Start → CONTINUE / SAVE overlay
                 SAVE → status/save screen:
                        DIFFICULTY (EASY/NORMAL/HARD), PLAYER, coins,
                        SAVE, EXIT, and the confirm dialogs
                        ("NO SAVED DATA", "OLD DATA WILL BE LOST. IS THAT OKAY?",
                         "DATA SAVED.", "SAVING…", "CLEAR ALL DATA AND RESTORE
                         ORIGINAL STATUS.")
```

Screenshots taken during the run: `shot_04` (title menu), `shot_22/38` (data
select), `shot_29` (OPTIONS), `shot_41/43/44` (menu cursor experiments),
`shot_46` (party submenu), `shot_47`/`idx5` (battle list), `shot_07` (pause
overlay), `shot_08/10/70` (status/save screen), `shot_51/pre` (in game),
`death4` (back at title after the last life).

## 4. Address map

File offset → ROM address = `0x08000000 + offset`.

| Address | Contents |
|---|---|
| `0x0823D090` | Pause/status label table (EN): DIFFICULTY, PLAYER, SAVE, EXIT, EASY, NORMAL, HARD |
| `0x0823D0F0` / `0x0823D150` | Same table, FR / DE |
| `0x0823D1BC` | Save dialogs (EN): NO SAVED DATA / OLD DATA WILL BE LOST. / IS THAT OKAY? / DATA SAVED. / SAVING… |
| `0x0823D334` | CLEAR ALL DATA AND / RESTORE ORIGINAL STATUS. / IS THIS OKAY? |
| `0x0823D474` | Link-cable dialogs (EN): OPEN CONNECTION. / OKAY? / CONNECTING… / CONNECTION FAILED. / PRESS THE A BUTTON. / SELECT GAME DIFFICULTY. / EASY / NORMAL / HARD |
| `0x0823D71C` | **Main menu label table** (EN, 4 entries): NEW GAME, LOAD GAME, OPTIONS, PARTY GAME; followed in the same table by the player-select/party labels (1PLAYER, 2PLAYERS, VIEW RECORDS) and the FR/DE copies |
| `0x0823D8A4` | Party-game records labels (EN): KNIGHT BATTLE, RECORD, RESULTS, WOODSMAN BATTLE, TOP TIME, MAGICIAN BATTLE, COMPUTER, PTS, WIN, LOSS, MICKEY, DONALD |
| `0x0823DA58` | Party battle list (EN/FR/DE): KNIGHT BATTLE, WOODSMAN BATTLE, MAGICIAN BATTLE, EXIT |
| `0x0825E2B8` | OPTIONS labels (EN): DIFFICULTY, HOLD/SHOOT, JUMP, THROW, COLOR MODE, EASY/NORMAL/HARD, A BUTTON/B BUTTON, TYPE 1/TYPE 2, EXIT, LCD A/LCD B/TELEVISION |
| `0x0825E4A0` | OPTIONS pointer table (EN/FR/DE) |
| `0x081194BC` | Physical→logical key mask table (0x80, 1, 2, 4, 8, 0x10, 0x20, 0x40, 0x100, 0x200) |
| `0x02023AF0` | Per-player key state array, 8 bytes/player: `+0` held, `+2` previous, `+4` pressed edge (`pressed = held & ~prev`) |
| `0x04000130` | KEYINPUT (active-low); read at `0x08009160` (literal at `0x08009180`), pressed-edge computed at `0x08009110` |
| `0x02025672` | Menu cursor byte (savestate-verified; §6b) |
| `0x0E000000` | Save window (4 Kbit EEPROM; mGBA produces a 512-byte `.sav`) |
| `0x081214B0` | Credit/cast text bank (ASCII with `0x00`=space, `0x02..0x04` control bytes): `PRESENTED BY`, `DISNEY'S MAGICAL QUEST3`, `MICKEY MOUSE`, `DONALD DUCK`, `HUEY/DEWEY/LOUIE`, `MINNIE MOUSE`, `DAISY DUCK`, `GOOFY`, `PLUTO`, `KING PETE`, `STORYBOOK`, `FAIRY`, `THE BLACKSMITH`, `WOODCUTTERS` |

Save image (observed, 512 B): one 64-byte record at `0x00..0x3F`
(`40 00 00 02 00 00 00 04 01 00 01 00 03 03 80 00 …`, byte `0x31 = 0xCE`),
`0x40..0x7F` zero, `0x80..0x1FF` `0xFF` (unwritten EEPROM). The record holds the
checkpoint, difficulty, character, lives and coin counters. The save is not a
code surface and was not reversed field-by-field.

## 5. Algorithm (menu behaviour)

```
data_select(entry):                 # entry = byte 0x02025672
    if entry == 0: new_game()       # -> player select
    if entry == 1: load_game()      # -> resume from EEPROM record
    if entry == 2: options()
    if entry == 3: party_menu()
    else:          options()        # default branch (observed for 4..9)

options():                          # rows, in draw order
    rows = [DIFFICULTY(3), HOLD_SHOOT(2), JUMP(2), THROW(2), COLOR_MODE(3), EXIT]
    # Left/Right cycles the value of the selected row; EXIT returns

pause():
    overlay: CONTINUE / SAVE
    SAVE -> status screen: DIFFICULTY, PLAYER, coins, SAVE, EXIT
    SAVE  -> overwrite confirm ("OLD DATA WILL BE LOST. IS THAT OKAY?")
    EXIT  -> back to the overlay, then to the game
```

Input: `pressed = held & (held ^ prev)` computed at `0x08009110..0x0800916E`
for the active player slot at `0x02023AF0 + 8*player`.

**No character/number entry routine exists**: every screen above is a
list/`Left-Right` selector. There is no keyboard, no `strlen`-style input buffer,
and no screen that accepts a string.

## 6. Tables

### 6.1 Complete UI inventory

An exhaustive whole-ROM scan for runs of ≥4 ROM pointers whose targets are
printable strings returns 26 hits; after discarding data-region false positives
the UI-relevant tables are:

```
pause/status     0x23D090 0x23D0F0 0x23D150
save dialogs     0x23D1BC 0x23D254 0x23D2DC 0x23D334 0x23D390 0x23D3E8 0x119ACC
link dialogs     0x23D474 0x23D52C 0x23D5B4
main/party menu  0x23D71C (4 + 7 entries x 3 languages)
party records    0x23D8A4 0x23D950 0x23D9FC
battle list      0x23DA58
options          0x25E4A0 (6 rows + values x 3 languages)
difficulty only  0x1AC34 0x1AC6C 0x1ACCC
```

No table anywhere contains a password/cheat/debug label.

### 6.2 Keyword counts in the raw image (ASCII, whole file)

| Literal | Count | Literal | Count |
|---|---:|---|---:|
| `PASSWORD` | 0 | `CHEAT` | 0 |
| `DEBUG` | 0 | `SECRET` | 0 |
| `UNLOCK` | 0 | `SAMPLE` | 0 |
| `STAGE` | 0 | `CONTINUE` | 0 |
| `GAME OVER` | 0 | `OPTION` | 4 |
| `PARTY` | 2 | `RECORD` | 4 |

`STAGE` and `CONTINUE` are displayed on screen but are **not** ASCII: the
"STAGE n" banner and the pause "CONTINUE" label are drawn from tile/glyph data,
so these two zeros are reported as *ASCII-only* results and are why the screen
enumeration (not the string scan) is the primary negative evidence.

### 6.3 Key-mask table scan

* Konami (`Up Up Down Down Left Right Left Right B A`) as u16: **0 hits**;
  reversed: **0 hits**; as bytes: **0 hits**.
* Generic scan: 82 runs of ≥6 consecutive u16 values drawn from the 10 GBA key
  masks. Manual inspection of every run: all lie inside executable code
  (offsets < 0x60000) or are non-input data (repeated single values, sprite
  tables). The only real key-mask data table in the image is the 10-entry
  physical→logical remap at `0x081194BC`.

## 6b. Enumeration

### Space definition

**0 accepted codes.** The engine exposes no field of any width to encode a
code: there is no text/number entry widget, no alphabet table for input, and no
validator. The "space" is therefore empty, and the deliverable that §0.2
normally requires (a novel code) does not exist for this title. What follows is
the enumeration that proves the empty space.

### Screens enumerated (12 distinct interactive screens)

| # | Screen | Entry | Notes |
|---:|---|---|---|
| 1 | Language select | boot | ENGLISH / FRANÇAIS / DEUTSCH |
| 2 | Title / attract | boot | "PRESS START", © 2004 Disney, Developed by CAPCOM |
| 3 | Data select | Start | 4 entries |
| 4 | Player select | NEW GAME | 1 PLAYER / 2 PLAYERS |
| 5 | OPTIONS | data select | 6 rows |
| 6 | Party submenu | PARTY GAME | 1PLAYER / 2PLAYERS / VIEW RECORDS |
| 7 | Battle list | party submenu | KNIGHT/WOODSMAN/MAGICIAN BATTLE + EXIT |
| 8 | Records | VIEW RECORDS | times/points/win-loss |
| 9 | Pause overlay | Start in game | CONTINUE / SAVE |
| 10 | Status/save | pause → SAVE | DIFFICULTY, PLAYER, coins, SAVE, EXIT |
| 11 | Save confirms | SAVE / clear | yes/no dialogs |
| 12 | Link dialogs | 2 PLAYERS | OPEN CONNECTION / CONNECTING / FAILED |

None of them accepts a code.

### Bounds proven by rejection

* **Main menu count.** The byte `0x02025672` was found by savestate diff (it
  steps 0 → 1 → 2 as Down is pressed from NEW GAME) and then written directly in
  the `gbAs` chunk of a savestate and reloaded with F1, pressing A:
  * 0 → NEW GAME (player select)
  * 1 → LOAD GAME (resumes the save)
  * 2 → OPTIONS
  * 3 → PARTY GAME submenu
  * 4, 6, 7, 8, 9 → OPTIONS, byte-for-byte identical to a stored OPTIONS
    reference (ImageMagick RMSE = 0)
  * 5 → the party **battle list** (an existing screen)
  No value produced an unknown screen: normal movement only ever visits 0…3, and
  out-of-range pokes land on existing screens (consistent with an index being
  clamped or reading the neighbouring table slot), so there is **no fifth menu
  entry**.
* **Options rows.** 6 rows only (5 settings + EXIT); the label table has exactly
  those strings.
* **Published passwords.** The 7 published stage passwords
  (`Mickey,Minnie,Daisy,Donald` / `Goofy,Minnie,Donald,Pete` /
  `Daisy,Goofy,Pete,Minnie` / `Minnie,Pluto,Mickey,Daisy` /
  `Mickey,Daisy,Donald,Pluto` / `Daisy,Pluto,Mickey,Pete` /
  `Pluto,Pete,Daisy,Minnie`) were encoded as 28 symbols and scanned against
  every offset of the ROM under *any* consistent bijective symbol→byte and
  symbol→u16 map (the scan builds the mapping on the fly and only keeps complete
  consistent hits): **0 hits, both widths**. The table is not in the GBA image.
* **No entry surface.** With no password screen reachable from any of the 12
  screens, the SNES passwords cannot be entered at all; the published list
  applies to the SNES SKU (3rd party cheat indexes label it "Stage Passwords SNES"; the
  visualboyadvance page copies the SNES instruction "select the second option at
  the main menu", but on this GBA build the second option is LOAD GAME).
* **Game over.** Starting a new game (lives x3) and running into the stage-1
  enemies repeatedly produced three checkpoint respawns (each sampled 1.5 s
  after the death, still in-game), and the fourth death cycle ended at the title
  screen ("PRESS START") — `death4`. No password/continue-code screen appeared
  at any of those deaths or at the game-over transition; the run then returns to
  the title with the EEPROM save intact.
* **Hidden-entry attempts.** At the title, `L+R+Start`, `Select+Start`,
  `L+R+Select+Start`, `B+Start` and `Select` alone all either open the normal
  Start menu or do nothing; none produced a new screen.

### Published lists checked

| Source | What it lists | Verified against this ROM |
|---|---|---|
| 3rd party cheat indexes | snippet "Passwords / Stage Passwords SNES / Select the second option at the main…" — the passwords are labelled SNES | page returns 403; the passwords themselves were checked via the mirror below and the SNES label is confirmed by the GBA menu having no password entry |
| 3rd party cheat indexes ROM page | 7 stage passwords (4 cast names each) | 28-symbol consistency scan: 0 hits (byte and u16) |
| 3rd party cheat indexes | "Total cheats available: 0" | consistent with the negative result |
| 3rd party cheat indexes | only GameShark / CodeBreaker **master codes** (`937725CAAA41`, `FFC4D2F3D0EE`, `E47BD9FD9E48`) | memory-write codes, not in-game cheats; out of scope by the brief, and no in-game equivalent exists |
| 3rd party cheat indexes (*Mickey to Donald: Magical Adventure 3*, SNES) | debug flag at WRAM `$7E00FE` (PAR `C0FE0001`), debug menu, stage select, sound test, object viewer | debug UI strings and screen objects absent from the GBA image (keyword counts §6.2); mirroring the flag to GBA `0x020000FE`/`0x030000FE` produced no debug behaviour (the IWRAM write instead corrupts live state and hangs the game) |

### Novel code

Not applicable — with no validator, no code can be minted or accepted. The
nearest "unpublished" artefacts found are the unreachable-in-practice option
values (COLOR MODE = TELEVISION, a SNES TV-brightness setting on a handheld) and
the unused top half of the 8 MiB mask ROM (0xFF padding after 0x4207AE), neither
of which is a code.

## 7. Validation evidence

**Observed (emulator):**
* The four data-select entries, the party submenu, the battle list, the records
  screen, the OPTIONS screen with 6 rows, and the pause/status screen with its
  confirm dialogs were reached by controller input only.
* Menu cursor byte 0x02025672 changes 0→1→2 with successive Down presses
  (savestate diff), and writing it and reloading selects the corresponding
  screen.
* Death and lives exhaustion lead through checkpoint respawns to the title
  screen; no code screen.
* Title-screen button combinations produce only the normal Start menu.

**Derived (ROM):**
* The UI inventory is complete for pointer-table text; the label tables have
  exactly the counts stated.
* The published password table is absent under any bijective symbol map (the
  scan is exhaustive over offsets and consistent mappings).
* Header is stock (single logo hit, valid complement, stock entry branch).

**Inferred:**
* Because "STAGE"/"CONTINUE" are tile-drawn, the ASCII zero-counts for
  `PASSWORD` are not by themselves proof; the negative rests on the screen
  enumeration plus the absence of any input field, which is why that method was
  used as primary.
* The OPTIONS "COLOR MODE" values are SNES display settings carried over
  unchanged; the effect on GBA palettes was not measured.

## 8. Unknowns

* The 2-player link mode was not exercised (requires a second unit/instance);
  its dialogs exist only as strings. Nothing suggests a code surface there.
* Party battles were entered but not played to completion, so a record-based
  unlock (e.g. a hidden 4th battle at some score) cannot be excluded by play;
  the battle label table, however, contains exactly three battles + EXIT.
* The Japanese/USA SKUs have different game codes (`BMQJ`/`BMQP`-class) and were
  not examined; no claim is made about them.
* Save-record fields were not fully mapped (out of scope for a code search).

## 9. Tooling

Scripts (in `/tmp/magicalquest3`):
* `state.py` — read/patch mGBA `.ssN` PNG savestates (zlib `gbAs` chunk) and
  rewrite the PNG; used to locate and poke the menu cursor byte.
* `keys.py` / `combo.py` — XTEST key injection and screenshot capture with
  ImageMagick RMSE/AE comparison (used instead of reading images to keep the
  evidence RAM-based).
* Ad-hoc Python: header parse, Nintendo-logo scan, pointer-table extractor,
  keyword counter, published-password consistency scan, key-mask run scanner.
* Disassembly: `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000
  -M force-thumb`.

Environment: mGBA 0.10.5 SDL, Xvfb :332 + openbox, `SDL_AUDIODRIVER=dummy`,
ImageMagick `import`/`compare`, Binutils ARM.

## 10. Legal note

No ROM, graphics, music or game text is redistributed here. The analysed image
is identified by hash only; quoted strings are short UI labels required to
document the menus.
