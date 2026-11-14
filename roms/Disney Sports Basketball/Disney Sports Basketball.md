# Disney Sports Basketball (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney Sports Basketball/Disney Sports Basketball.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| Header title | `DS_BASKET_U` |
| Game code | `A2AE` |
| Maker code | `A4` (Konami) |
| Software version | 0x00 (Rev.00) |
| Fixed byte 0xB2 | 0x96 |
| Complement check 0xBD | 0x7F — **valid** (computed 0x7F) |
| Header checksum 0xBE | 0x0000 (standard computation gives 0x0081; a zeroed field indicates a rebuilt header, while the complement and entry word are stock) |
| Entry word 0x00 | `0xEA00002E` — stock branch to 0x080000C0, no cracktro |
| Nintendo logo | one copy at 0x04; no second header anywhere in the file |
| MD5 | `1c4467efeb8c13831b8ad08d7e8f4908` |
| SHA-1 | `8999364d93339017743ab280d22fda6c61be3f42` |
| SHA-256 | `2257e2afd309b29ae69521a43f9cba5011f2244c096946ab0f1a09571e1801ab` |

No trainer/cracktro markers (`SUNHORS`, `CRC BANDIT`, `MODE7`, `CRACK`, `TRAINER`,
`PARADOX`, `EURASIA`, `INDEPENDENT`) are present; first 4 KiB is ordinary crt0
code and literal pools. Sample rate: 512 bytes EEPROM (mGBA created a 512-byte
`.sav`; the save module strings at 0x10A4EC/0x10A4F8 name both `EEPROM SAVE`
and `SRAM SAVE` paths).

## 2. Executive summary

**There is no password, no button cheat code, and no player-reachable debug menu
in this ROM.** The game has no code-entry surface at all: the only user text
field is the 6-cell profile-name entry on save-slot creation, and it is a label
(printed back on the Load screen), not a validator. A full string scan found
**zero** occurrences of `password`, `passwd`, `cheat`, `secret`, `unlock` or
`hidden`; the only four `debug` hits are Konami/KCEK development-tool leftovers.

What *does* exist:

1. A complete KCEK in-house debug subsystem compiled into the ROM:
   `AGB SYSTEM Ver3.00 BY KCEK`, `L+R+START SOFT RESET`,
   `L+R+SELECT MEM+DMA DEBUG`, `DEBUG MENU`, `PAGE %d.`, an EEPROM/SRAM
   save-tool page, a sample-menu page, a stage/player debug printout
   (`PLAYER0:`–`PLAYER3:`, `LEVEL:`, `GMODE:`, `STAGE:`, `PL0 ITEM:`).
   The documented `L+R+START` soft reset **works** (observed). The documented
   `L+R+SELECT` memory/DMA debugger **does not activate** at boot, on the title,
   or on the main menu (observed, three timings).
2. A debug "GAME MODE SELECT" page table that warps to otherwise-unreachable
   screens, first described publicly by TCRF. Its entry selector is the byte at
   `0x02000240`, which this work shows is a *menu-object id*, and forcing it to
   `3` from a savestate does not open the screen in USA Rev.00. The real screen
   dispatcher reads the mode word at `0x0200FA60` (`cmp r0,#3` at
   `0x0801C406`). The page table and its seven mode-set launchers are
   enumerated in §6b.
3. Unlockables that are **save/progress flags, not codes**: Mortimer + the
   Imperials + Aero Field (Challenge level 2), Pete + Steamrollers +
   SteamRoller Dome (Challenge level 3), the All-Star mode (Challenge Cup), and
   the Tiny Rockets (collect the item set). The character record table at
   `0x0815B3A8` contains Pete and Mortimer records even though the default
   player-select ring offers only six named characters + `RANDOM`.

The negative is bounded, not assumed: the menu/screen inventory, the text space,
the button-mask space and every published code/claim in scope are listed and
tested in §§6b and 7. Memory-write codes (CodeBreaker/GameShark/TCRF RAM
patches) are out of scope and are not offered as cheats; they are used only as
address hints and are labelled as such.

## 3. How to reproduce

Emulator: mGBA 0.10 (`mgba -3`), Xvfb `:311`, `SDL_AUDIODRIVER=dummy`.
Keys: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad.

```
Xvfb :311 -screen 0 1024x768x24 &
DISPLAY=:311 openbox &
DISPLAY=:311 SDL_AUDIODRIVER=dummy mgba -3 "Disney Sports Basketball.gba" &
```

Exact paths used:

| Screen | Path |
|---|---|
| Title menu | boot → `PRESS START` (Start) → New Game / Load Game / Data Reset |
| Name entry | New Game → pick a `No Data` slot → `OK?` → NAME ENTRY (6 cells) → Start jumps to `↵`, A → `OK?` → A |
| Main menu | New Game slot → name → A → MAIN MENU (Single Play / Multi Play / Options) |
| Single Play | MAIN MENU → A. Two columns of three: **left** Exhibition, Challenge, Player Training; **right** Minigame, Tutorial, Quick Start |
| Exhibition | Single Play → Exhibition → SELECT PLAYER (Left/Right = character, A = pick, A = `OK?`) → SELECT ITEM → game |
| Challenge | Single Play → Challenge → SELECT LEVEL |
| Player Training | Single Play → Player Training |
| Minigame | Single Play → Minigame → 6 events |
| Tutorial | Single Play → Tutorial → 32-cell technique grid |
| Multiplay | MAIN MENU → Multi Play → Versus / Items / Minigame High-Score |
| Options | MAIN MENU → Options → Game Settings / Item List / Total Score / Minigame Score / ? ? ? / ? ? ? |
| Pause | in game, Start → RESUME / REPLAY / RETRY / SELECT / SLEEP / EXIT |

Savestates: `Shift+F1`…`Shift+F10` save, `F1`…`F10` load. Savestate files are
PNG containers; the `gbAs` chunk is zlib data whose EWRAM window starts at raw
offset `0x21000` (verified: `0x0200FA60` in EWRAM reads back at raw `0x30A60`).
`state_edit.py` (below) rewrites a single byte and rebuilds the PNG CRCs, which
is how the `0x02000240` / `0x0200FA60` experiments were made without a cheat
device. Those experiments are debugger evidence, not user-reachable cheats.

## 4. Address map

ROM addresses are `0x08000000 + file_offset`.

| Address | Contents |
|---|---|
| `0x000000`–`0x0000FF` | GBA header, stock ARM branch, valid complement |
| `0x00109000`–`0x0010A600` | KCEK debug/development string bank (ASCII, NUL-terminated) |
| `0x00109BBC` | `A6DE / GDKE / WATCH / CHECKER / FREE / DEMO / SAMPLE / GSELECT / GAME / SELECT / TITLE / LOGO / STAFF_ROLL / HALF_TIME_DEMO / PLAYER POS DEBUG / LOADING DEMO / SAMPLE names` |
| `0x00109CA0` | `DEBUG ENV`, `PETE`, `PLUTO`, `MAX`, `GOOFY`, `DAISY`, `DONALD`, `MINNIE`, `MICKEY`, `STAGE5`…`STAGE0`, `EXHIBITION`, difficulties, item names |
| `0x00109F6C` | `PL1 ITEM:`, `PL0 ITEM:`, `LEVEL:`, `GMODE:`, `STAGE:`, `PLAYER3:`…`PLAYER0:` |
| `0x0010A04C` | `AGB SYSTEM   Ver%s`, `3.00`, `BY KCEK`, `L+R+START  SOFT RESET`, `L+R+SELECT   MEM+DMA DEBUG`, `%d.`, `PAGE NO.%d` |
| `0x0010A160` | `SAMPLE MENU`, `0. ITEM0`…`4. ITEM4`, `PUSHING %d FRAME`, `PUSH START TO FADE OUT`, `PUSH SELECT TO FADE IN`, `PUSH A TO PALET ROTATE` |
| `0x0010A364` | `0-6.SHOOTOUT` … `0-0.1ON1 OFFENCE`, `1-2.TUTORIAL FREE` … `1-0.TUTORIAL GUARD`, `DEBUG MENU`, `PAGE %d.` |
| `0x0010A4EC` | `EEPROM SAVE`, `  SRAM SAVE`, `SAVE LOAD ERROR`, `SAVE START_BUTTON`, `LOAD SELECT_BUTTON`, `FORMAT L_BUTTON`, `SAVE_POINT`, `LOAD_POINT` |
| `0x0010A680` | literal pool: 0x0810A04C, 0x0810A060, 0x0810A068, 0x0810A070, 0x0810A08C, 0x0808AB64 — banner print list |
| `0x0010A478` / `0x0010A484` | `DEBUG MENU` / `PAGE %d.` — loaded as literals at `0x0800CD24` / `0x0800CD2C` by the debug list renderer at `0x0800CC7C` |
| `0x0800CD30` | debug page-label renderer (returns in `bx lr` at `0x0800CC28`) |
| `0x0800CC7C` | debug list renderer, called by BL from `0x0800C776` and `0x0800C860` |
| `0x0880AB80` | debug "environment" name pointer table (FREE, CHECKER, WATCH, DEBUG ENV, samples, players, stages, difficulties, 28 item names) |
| `0x0880AE80` / `0x0880AEA0` | stage-name lists: 0-0…0-6 (7) and 1-0…1-2 (3) |
| `0x0880AEB0` | debug page descriptor table (2 pages × 4 rows; see §6) |
| `0x0880AEB8` / `0x0880AF38` | the two page row-lists referenced by the debug menu |
| `0x0880B78C` | top-level menu table: SINGLE PLAY/id 2, MULTI PLAY/3, OPTION/4 |
| `0x0880B7C4` | minigame table: MGAME 1ON1OFF 8, 1ON1DEF 9, 2ON1OFF 10, 2ON1DEF 11, 3PT 0x33, FT 0x32 |
| `0x0880B95C` | "Original" submenu: ORG TRAINING 0x21, ORG ABILITY 0x22, ORG STATUS 0x23, ORG SAVE AND EXIT 0x24 (×2) |
| `0x0880B9EC` | Single Play mode table: EXHIBITION 5, CHALLENGE 6, ORIGINAL 7, MINIGAME 9, TUTORIAL 8, QUICK START 0xA |
| `0x0880BA60` | stadium dev-name table: METOROPOLIS, STADION_DER_BURG, SEEDUCKS, BELL_S_MOLL, VISTA_ARENA, BRICKYARD, PRIDE_FIELD, GIANT_GEAR (8) |
| `0x0815B3A8` | character record table, 8 bytes/record, 23 records + NULL terminator: MICKEY1-3, MINNIE1-3, DONALD1-2, DAISY1-3, GOOFY1-3, MAX1-3, MORTIMER1-3, PETE1-3 |
| `0x0815B468`–`0x0815B524` | ASCII character strings `PETE3…MICKEY1` |
| `0x00118944`–`0x00118B48` | player-visible item name bank (`MYSTERY BOX` … `PHOENIX III`, 37 names + `NONE`) |
| `0x02000200` | array of 0x54-byte menu/save objects (`str r2,[r1]` at `0x08001E76` with `0x02000200`); object +0x40 is the id written by `0x02000240` |
| `0x0200D020` / `0x0200D148` / `0x0200D14C` | object index / selected-object pointer / object-array base pointers |
| `0x0200D889`–`0x0200D88D` | 40-bit item flag field (public CodeBreaker address `3200D889 00FF`, `8200D88A FFFF`, `8200D88C FFFF`) |
| `0x0200FA60` | screen-mode word; read at `0x0801C406` (`cmp r0,#3`) and by 0x109F24; written by the debug launchers as `0x0200D5C0 + 0x24A0` |
| `0x0200CCB8/BC/C0` | key state: new-press / previous / new-release (input routine `0x08000D6C`, KEYINPUT `0x04000130` at literal `0x08000DA0`) |
| `0x02009610` | engine struct base; key state at +0x36A8/+0x36AC/+0x36B0 |

## 5. Algorithm

### 5.1 There is no validator to reimplement

No password/cheat constant, table or alphabet exists in the image, and the only
user text field feeds the save-slot label:

```
name_buffer[6]  (font-tile codes, not ASCII)
  -> stored in the save record
  -> printed in the Load/Continue slot list ("Data 2  AAAAA")
```

Supporting evidence:

* `strings` on the whole image: `password` 0, `passwd` 0, `cheat` 0, `code` 0,
  `secret` 0, `unlock` 0, `hidden` 0; `debug` 4 (all KCEK tool labels).
* No `PASSWORD`/`CODE` screen exists in the walked menu tree (§6b); the only
  on-screen keyboard is NAME ENTRY, reached from New Game only.
* The name is echoed on the Load screen, confirming the consumer is display.
* None of the 14 walked screens contains a text comparison prompt; no
  "INVALID CODE"-style rejection string exists in any encoding searched.

### 5.2 Screen/menu dispatch

* `0x0200FA60` is the screen-mode word. The renderer at `0x0801C3xx` tests
  `mode == 3` and swaps a tile base (`0x80E8`), i.e. mode 3 is a special
  (developer) layout inside the player-select renderer.
* The debug page launchers each do:
  `*(u32*)(0x0200D5C0 + 0x24A0) = <mode>` then return, i.e. they set the next
  screen-mode word directly. Values used: 8, 9, 10, 11, 27, 28, 34.
* The menu tables at 0x0880B78C/0x0880B7C4/0x0880B95C/0x0880B9EC are arrays of
  12-byte records `{char* name, u32 id, u32 next_id}` consumed by the menu
  builder at `0x0801F6F8` (`bl 0x0802A4C4` for the label, `bl 0x0802A69C` for
  the list).

### 5.3 Unlock model (save flags, not codes)

* Character records for PETE and MORTIMER exist at `0x0815B3A8`; the default
  SELECT PLAYER ring enumerates only the six base characters plus `RANDOM`
  (observed: 8 entries: `RANDOM`, `MAX`, `GOOFY`, `DAISY`, `DONALD`, `MINNIE`,
  `MICKEY` and back to `RANDOM`).
* Therefore the two extra characters are filtered out by save state, exactly as
  published: Mortimer/Imperials/Aero Field from Challenge level 2, Pete/
  Steamrollers/SteamRoller Dome from Challenge level 3, All-Star mode from
  Challenge Cup, Tiny Rockets from the item set.
* This is the §16.18 pattern: a bitfield in the save record, tested per bit, not
  a code. No controller input can write the roster table; the setters are the
  Challenge win handlers. The report therefore does not offer a "code" for
  these, and does not brute-force them.

## 6. Tables

### 6.1 Top-level and screen tables

| Table | Entries | IDs |
|---|---|---|
| Main menu `0x0880B78C` | 3 | SINGLE PLAY=2, MULTI PLAY=3, OPTION=4 |
| Single Play `0x0880B9EC` | 6 | EXHIBITION=5, CHALLENGE=6, ORIGINAL=7 (UI "Player Training"), MINIGAME=9, TUTORIAL=8, QUICK START=0xA |
| Minigame `0x0880B7C4` | 6 | 1ON1 OFF=8, 1ON1 DEF=9, 2ON1 OFF=10, 2ON1 DEF=11, 3PT=0x33, FT=0x32 |
| Original submenu `0x0880B95C` | 4 | TRAINING=0x21, ABILITY=0x22, STATUS=0x23, SAVE AND EXIT=0x24 |
| Debug stage list `0x0880AE80` | 10 | `0-0`…`0-6` (1ON1 offence/defence, 2ON1 offence/defence, free throw, free-throw minigame, shootout), `1-0`…`1-2` (tutorial guard, handcheck, free) |
| Pause (observed) | 6 | RESUME, REPLAY, RETRY, SELECT, SLEEP, EXIT |
| Options (observed) | 6 | Game Settings, Item List, Total Score, Minigame Score, `? ? ?`, `? ? ?` (rows 5–6 are inert) |
| Game Settings (observed) | 6 | Out of Bounds, Shot Clock Violation, Defence Foul, Replay, Free Throws, BGM — each ON/OFF |

### 6.2 Character / team / court / item tables

* Character records (`0x0815B3A8`): 23 records, 8-byte stride, NULL terminator:
  `MICKEY1..3, MINNIE1..3, DONALD1..2, DAISY1..3, GOOFY1..3, MAX1..3,
  MORTIMER1..3, PETE1..3`. Donald has only two variants; that is in the data.
* Debug label list (`0x00109CB4`) contains `PLUTO` where the final record table
  has `MORTIMER`. Pluto is a **stale/unused debug label**; no Pluto character
  record, string or sprite-table entry exists.
* Teams observable in Exhibition: SUPER STARS (Mickey), CHARMERS (Minnie),
  SEADUCKS (Donald), BELLES (Daisy), SPACENUTS (Goofy), SHIFTERS (Max);
  Imperials (Mortimer) and Steamrollers (Pete) are the two locked teams.
  Published fan lists add the Mickey/Donald/Goofy all-star squads, Pete's
  All-Stars and the Tiny Rockets (13 names total); only the two Challenge
  unlocks and Tiny Rockets are ROM-verifiable as character/team records.
* Stadium dev-name table (`0x0880BA60`) has 8 names. A visible court banner
  `SS Cantankerous` was observed in a Quick Start game and is not in that ASCII
  list, so the ASCII table is developer naming, not the player-visible court
  name bank (player text is tile-encoded).
* Items: 37 names + `NONE` in the visible bank (0x118944–0x118B48), 27 names +
  `NONE` in the debug bank (0x109D54), with duplicate spellings that are real
  data (`STAR RING`/`STAR_RING`, `TORNADO II`/`TORNADO_II`, etc.). The 40-bit
  flag field at `0x0200D889` matches a 40-item set; the Item List screen draws a
  6×6 grid (36 cells) and initially shows one owned item.

## 6b. Enumeration

### 6b.1 Space definition

There is no code space: **0 alphabets, 0 lengths, 0 checksums, 0 validators.**
The engagement therefore enumerates the menu/debug surface instead, and states
the text and button spaces that were searched so the negative is bounded.

| Space | Size | Result |
|---|---|---|
| Profile name field | 6 cells, 61-symbol keyboard (A–Z 26, 0–9 10, 25 punctuation glyphs `#$%&+-*/=^~@\:;.,!?(){}<>` + `abc`/`DEL`/`←`/`→`/`↵` controls) | label only; echoed on Load screen |
| Whole-image strings (`strings -n 4`) | 161,211 lines | 0 password/cheat/secret/unlock/hidden; 4 debug |
| Button-mask runs (≥4 consecutive u16 in {1,2,4,8,10,20,40,80,100,200}) | 1,490 runs | all are code/data noise or repeated single bits; **no multi-press sequence table** |
| Documented button combos | 2 | `L+R+START` (0x30C) works; `L+R+SELECT` (0x304) inert in 3 states |
| Menus/screens walked | 18 distinct | title, title menu, main menu, name entry, single play, exhibition select, item select, challenge level, minigame, tutorial, multiplay, items exchange target, score-mix link check, options, game settings, total score, record (minigame score), pause |
| Debug page table | 2 pages × 4 rows | 7 mode-set launchers + 3 delay/no-op actions (below) |

### 6b.2 Unpublished/undocumented entries found

1. **"Player Training" is the developer `ORIGINAL` mode.** The mode table entry
   is the ASCII string `ORIGINAL` with id 7; the UI renders `Player Training`
   ("Train your favorite character, and raise their stats."). No published list
   names this mapping.
2. **`PLUTO` is a dead debug label.** The debug environment list at 0x109CB4
   names PLUTO; the shipped character record table has MORTIMER in that slot and
   no Pluto records.
3. **Debug page launchers.** The page descriptor table at 0x0880AEB0 supplies
   eight rows across two pages, with seven distinct mode-set functions:

   | Launcher | Writes mode |
   |---|---|
   | `0x0800CB9C` | 8 (1ON1 offence) |
   | `0x0800CBC4` | 9 (1ON1 defence) |
   | `0x0800CBB0` | 10 (2ON1 offence) |
   | `0x0800CBD8` | 11 (2ON1 defence) |
   | `0x0800CC00` | 27 (0x1B internal screen) |
   | `0x0800CBEC` | 28 (0x1C internal screen) |
   | `0x0800CC14` | 34 (0x22 internal screen) |

   plus `0x0800CC28` (`bx lr`), `0x0800CC2C` (frame wait) and `0x0800CC68`
   (delay/call) as row actions. The TCRF write-up mentions only the Normal and
   Minigame pages; the 27/28/34 screen warps are not described anywhere.
4. **The debug banner print list** at 0x0010A680 is complete and unreferenced by
   any menu path; it is the "AGB SYSTEM Ver3.00 BY KCEK / L+R+START SOFT RESET /
   L+R+SELECT MEM+DMA DEBUG" boot banner used by the development build.
5. **Shipped high-score defaults are `KONAMI`.** The Record (Minigame Score)
   screen for a fresh save lists 1st–5th as `KONAMI` with scores
   50/40/30/20/10. That is a developer placeholder table, not a player record,
   and no published list mentions it.
6. **Total Score page** shows eight counters for Single Play (Games, Wins, Wins
   Percentage, Points, Rebounds, Assists, Blocks, Steals), all zero on a fresh
   save.

### 6b.3 Published codes/claims tested

| Claim | Source | Test | Result |
|---|---|---|---|
| `L+R+START` soft reset | in-ROM string 0x10A070 | pressed on title/main menu | **works** (returns to title menu) |
| `L+R+SELECT` MEM+DMA debug | in-ROM string 0x10A08C | held at boot, title and main menu (3 s) | **inert**; no screen, no RAM change |
| `02000240:03` opens GAME MODE SELECT | TCRF (memory code, out of scope as a cheat) | savestate byte patch at 0x21240 (EWRAM 0x02000240) at title and at main menu | screen unchanged; byte holds 3 while the menu still renders, so this id alone is not the gate in USA Rev.00 |
| `02000270:07` opens Minigame | TCRF (memory code) | not used as a cheat; the Minigame screen is reachable normally (verified) | not needed |
| Unlock Mortimer + Aero Field (Challenge lvl 2) | GameFAQs/Neoseeker/cheatingdome | static: MORTIMER1-3 records exist; Mortimer absent from default ring; Challenge mode present | **consistent**; gameplay clear not replayed (hours) |
| Unlock Pete + SteamRoller Dome (Challenge lvl 3) | same | PETE1-3 records exist; Pete absent from default ring | **consistent** |
| All-Star mode after Challenge Cup | GameFAQs | Challenge mode present; no code surface | consistent |
| Tiny Rockets (all items) | 1UP retrospective | 40-bit item field at 0x0200D889 matches 38-name bank | consistent |
| CodeBreaker `Unlock All Items` | Ethereal/almars | address 0x0200D889 cross-checks the 40-bit field | used as address evidence only; not a deliverable |

### 6b.4 Bounds proven by rejection

* `L+R+SELECT` rejected in three states (boot, title, main menu) — no debug
  screen, no DMA/memory view.
* Options rows 5 and 6 (`? ? ?`) reject activation: pressing A moves the cursor
  but no screen opens (observed on row 6; both rows render identically).
* The Item List initially rejects 35 of 36 cells (only one owned item); the
  SELECT ITEM ring shows `No Equioment` (sic) until an item is equipped.
* Multiplay Versus/Items/Minigame High-Score require a second unit/cable; the
  local only path is single-player, so those are link-gated, not code-gated.
* Savestate patch of `0x0200FA60 = 3` (the word the renderer compares against 3)
  did not switch screens; the menu state machine rewrites the visible list from
  its own object, so the debug layout cannot be reached by that byte alone.

## 7. Validation evidence

**Observed (emulator, savestate RAM reads):**
* Title, title menu, name entry, main menu, Single Play (6 modes), Exhibition
  player select (8 entries incl. RANDOM; banners SUPER STARS / SEADUCKS /
  SPACENUTS / BELLES / CHARMERS / SHIFTERS), SELECT ITEM 6×6 grid, Challenge
  SELECT LEVEL, Minigame (6), Tutorial (32 cells), Multiplay (3), Items
  exchange target (Game Boy Advance / GameCube), Score Mix link check
  ("Checking number of linked GBA"), Options (6 rows, 2 dead), Game Settings
  (6 toggles), Total Score (8 counters), Record (5 ranks, KONAMI defaults),
  Pause (6), in-game court banner `SS Cantankerous`.
* `L+R+START` soft reset works; `L+R+SELECT` does nothing.
* Data Reset asks "Are you sure you want to delete All saved data?" (cancelled;
  save preserved, Data 2 = `AAAAA` reloaded).
* Savestate EWRAM reads: menu object id at `0x02000240` = 4 (title/menu),
  5 (Single Play), 6 (Exhibition flow); screen mode at `0x0200FA60` = 3 after
  patch and stays 3 while the menu still renders.

**Derived (disassembly / tables):**
* Mode/minigame/original/stage tables and their ids (§6).
* Character record table with 23 records and PETE/MORTIMER present.
* Debug page descriptor table and its seven mode-set launchers.
* Key input routine at `0x08000D6C` and key-state addresses.
* No literal or BL reference to a password/validator routine; the only text
  consumer is the save-slot name display.

**Inferred:**
* The exact save bit positions for Mortimer/Pete/Aero Field/SteamRoller Dome and
  the all-star/Tiny Rockets flags were not decoded byte-for-byte; the roster
  filtering and published methods are consistent, but a full save-struct map is
  left as future work.
* The debug GAME MODE SELECT is a development-only screen (mode 3). Its entry
  path in USA Rev.00 is not via the menu ids we could reach; TCRF's byte patch
  did not reproduce here.

## 8. Unknowns

* Complete save-record layout (0x54-byte object array at 0x02000200 and the
  512-byte EEPROM image with `S YENSID   RECCO` magic) — checksum/obfuscation
  not reversed.
* Whether the debug GAME MODE SELECT can be entered in another revision
  (JP/EU) with a different gate; only USA Rev.00 was tested.
* Exact visible court-name bank (tile-encoded) and the mapping from the 8
  developer stadium names to the 10 player-visible courts.
* The Player Training sub-screen was listed (Single Play row 3, "Train your
  favorite character, and raise their stats.") but its sub-screen was not
  entered; the two `? ? ?` Options rows likewise render and reject activation
  without exposing a label.
* Visual effect of the three internal debug warps (modes 27/28/34); their mode
  ids are known but the screens were not entered.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* Python 3 + `capstone` 5.0.7 for targeted Thumb checks
* `state_edit.py` — read/patch mGBA `.ssN` PNG `gbAs` chunks (zlib), rebuild
  CRCs; EWRAM window at raw `0x21000`
* `probe.py` — save slot 9, decompress, print EWRAM `0x240` / `0xFA60`
* `keys.py` — xdotool key/combo/screenshot helper (hold 100–200 ms)
* ImageMagick `import`/`convert`/`montage` for menu montages
* No custom ROM patch was applied; the `.gba` was never modified.

## 10. Legal note

No ROM, graphics, music or extracted text is redistributed. Only hashes,
addresses, table layouts and the analyst's own notes are published here.
