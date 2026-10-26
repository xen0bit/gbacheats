# Banjo-Pilot (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Banjo-Pilot/Banjo-Pilot.gba` |
| Size | 16,777,216 bytes (0x1000000) |
| Header title (0xA0) | `BANJO PILOT` |
| Game code (0xAC) | `BAJE` |
| Maker code (0xB0) | `78` |
| Fixed byte 0xB2 | `0x96` (valid) |
| Main unit / device / version | 0x00 / 0x00 / 0x00 (Rev.00) |
| Entry word (0x00) | `0xEA00002E` → ARM branch to `0x080000C0` |
| Complement check 0xBD | stored `0xBE`, computed `0xBE` (valid) |
| MD5 | `1d55a0e331301a7d36ac326f3d8dc007` |
| SHA-1 | `58551d404c46b14ce3611dbfb70848e05bec2dac` |
| SHA-256 | `cabc774b551911279b796d450eb1bec73098b8a35a5a9ac664b5aefd38dcef50` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at file
offset `0x4` (the real header at 0). There is no second GBA header, no multiboot
stub and no "2 Games in 1" image. The last 0x20 bytes are `0xFF` padding. The
header is intact, the entry branch is the canonical `0x080000C0`; **no patch or
header fix is present**.

Save medium: mGBA created a **512-byte EEPROM image** (`Banjo-Pilot.sav`); its
first word reads `34 30 50 47` ("40PG" when read as big-endian text), a game
save magic. There is no password system covering for a missing battery — the
cartridge does have a battery save.

## 2. Executive summary

**The retail US ROM contains no password, passcode, button-code or debug-menu
system.** There is no screen, no validator, no alphabet table and no key-mask
sequence for entering a cheat. The game's only developer-intended "cheat"
surface is **Cheato's shop**: 21 named unlockables bought with Cheato Pages
earned in races. On a fresh save exactly four of the 21 are available to buy
(Green Glowbo GP 250, Purple Glowbo GP 150, Battle Track 1 100, Battle Track 2
100); the other 17 carry in-game unlock conditions. Selecting an entry with 0
pages is rejected with explicit dialogue.

The negative result is bounded by four independent lines of evidence:

1. **Text space.** The whole 16 MiB ROM contains zero case-insensitive
   occurrences of `password`, `passcode`, `debug`, `gameshark`, `codebreaker`,
   `enter code`, `cheat mode` or `level select`; the only `code` occurrence in
   the ROM is inside the audio-engine error string "audio RAM code" at file
   offset `0x3841` (dev text, not UI). The complete English UI text bank is
   18,926 bytes / 316 text entries (187 single-line printable strings plus
   multi-line dialogue using `0x0C`/`0x01` separators), and contains no
   code-entry prompt. Its only text-entry screen is `ENTER YOUR NAME` — three
   character slots, 36 symbols (A–Z, 0–9).
2. **Menu space.** Every reachable menu was walked (title, main, options, name
   entry, erase, single-player grid and all six entries, all mode/character/
   cup screens, race, pause, quit, multiplayer, Cheato room/dialogue/shop,
   trophies room). No hidden or debug entry appeared.
3. **Button space.** The game has a single keypad reader at `0x0802118C`
   (`KEYINPUT` = `0x04000130`), storing held/pressed state at `0x0201848C`.
   All 25 literal references to that state were disassembled. A scan for
   arrays of single-bit button masks produced 598 u16 runs and 271 byte runs.
   The pointer-referenced candidates resolve by location to the UI hit-test
   coordinate tables (`0x0805A5BC`, `0x0805A5C8`, used by `0x08026E88`),
   graphics tile bytes (`0x0806B900`, `0x0806B90C`), audio sample data
   (`0x08695xxx`, `0x08781A33`, `0x08A5001F`) or early header/crt0 bytes
   (`0x08000BE8`); none is a button sequence.
4. **Published lists.** GameFAQs' Banjo-Pilot "Cheats" page (archived
   2023-02-02), Rare Gamer's unlockables guide and TCRF all describe only
   Cheato purchases and in-game achievements — zero codes. TCRF's only unused
   text findings are `REVERSE CONTROLS` and `NOT USED 1`–`NOT USED 4`, which
   were verified in the ROM and are not reachable from any menu.

Because there is no code space, no "unpublished code" can be minted; §6b
therefore defines the spaces that do exist, proves their bounds by rejection,
and enumerates the 21-entry Cheato catalogue that is the game's real
developer-intended cheat surface.

## 3. How to reproduce

Environment used:

```bash
Xvfb :166 -screen 0 1280x960x24 &
DISPLAY=:166 openbox &
DISPLAY=:166 SDL_AUDIODRIVER=dummy mgba -3 roms/Banjo-Pilot/Banjo-Pilot.gba &
```

mGBA 0.10.5 (SDL). The 720×480 game viewport sits at `+280+255` inside the
1280×960 root; screenshots were cropped with
`convert raw.png -crop 720x480+280+255 +repage shot.png`.

Keymap used (mGBA SDL defaults, verified on the menus):

| GBA | Key | | GBA | Key |
|---|---|---|---|---|
| A | `x` | | D-pad | arrow keys |
| B | `z` | | Start | `Return` |
| L | `a` | | Select | `BackSpace` |
| R | `s` | | | |

Hold 50–180 ms per press; menus debounce. Savestates: `Shift+F1` save,
`F1` load (used heavily). Reset: `Ctrl+R`.

Menu paths:

* **Main menu**: boot → THQ/Rare logos → title → `Return` (Start) →
  `SINGLE PLAYER / MULTIPLAYER / OPTIONS`.
* **Options**: main → Down ×2 → A. Rows: Music Volume, SFX Volume, Default
  Name, Erase Save Data.
* **Name entry**: Options → Default Name → A. Three slots; Left/Right change
  the current character and wrap through `A…Z` then `0…9` (observed
  `... W X Y Z 0 1 2 3 ...`); A advances slot 1→2→3→done.
* **Single-player grid**: main → Single Player → A. Six jigsaw pieces:
  Grand Prix (top-left), Jiggy Challenge (top-middle), Time Trial (top-right),
  Trophies (bottom-left), Cheato (bottom-middle), Quickrace (bottom-right).
  Navigation in this grid is not plain 2-D: from the top-left piece Right goes
  to Quickrace then Time Trial; Up/Down toggles between the top and bottom
  rows at the current column. The label bar at the bottom always names the
  selected piece. (Short 50 ms presses are needed to avoid double-steps.)
* **Cheato shop**: Single Player → select Cheato (book icon) → A. Intro
  dialogue: A ×4. The shop then lists the currently available entries. A on an
  entry with 0 pages produces the rejection. Down past the last entry wraps to
  the first; L/R do not page.
* **Trophies**: Single Player → Trophies. A 3-D trophy room; empty on a fresh
  save.
* **Race / pause**: Grand Prix → A (character) → A (Bottles GP) → A ×N through
  dialogue → A on race splash → race → `Return` = pause (Continue / Restart /
  Quit) → Quit → Yes.
* **Multiplayer**: main → Multiplayer → A → "INSERT A GAME BOY ADVANCE GAME
  LINK CABLE." (single-cartridge dead end).

Published material checked (all 403 on direct fetch; archives used):

* GameFAQs Banjo-Pilot cheats, Wayback `20230202172139`.
* Rare Gamer "Banjo-Pilot Unlockables Guide".
* TCRF `Banjo-Pilot`, Wayback `20260910234901`.

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`. RAM is little-endian.

| Address | Kind | Meaning |
|---|---|---|
| `0x08000000` | ROM | image base; header |
| `0x080000C0` | code | ARM entry (crt0) |
| `0x0802118C` | code | keypad update routine |
| `0x080211C8` | literal | `0x04000130` (`KEYINPUT`) |
| `0x0201848C` | RAM | key state: `+0` held, `+2` newly pressed, `+4` repeat-enable byte |
| `0x08026E88` | code | (x,y)→index hit-test helper over the two 12-byte tables below |
| `0x0805A5BC` | data | 12-byte coordinate table used by `0x08026E88` (values 0x08/0x10/0x20/0x40 → 8/16/32/64, **coordinates, not key masks**) |
| `0x0805A5C8` | data | second 12-byte coordinate table used by `0x08026E88` |
| `0x08CF7EC8` | data | English UI text bank start (first string `SELECT A SLOT`) |
| `0x08CFC8B6` | data | English UI text bank end (localized/compressed banks follow) |
| `0x08CF8200` | string | `GRAND PRIX` |
| `0x08CF8210` | string | `JIGGY CHALLENGE` |
| `0x08CF8224` | string | `TIME TRIAL` |
| `0x08CF8234` | string | `CHEATO` |
| `0x08CF8240` | string | `TROPHIES` |
| `0x08CF82CC` | string | `QUICKRACE` |
| `0x08CF80B4` | string | `LANGUAGE` (unused in this build) |
| `0x08CF8130` | string | `REVERSE CONTROLS` (unused in this build) |
| `0x08CFB82C` | string | `GREEN GLOWBO GP` (shop) |
| `0x08CFB83C` | string | `PURPLE GLOWBO GP` (shop) |
| `0x08CFB8F9` | string | `BATTLE TRACK 1` (shop) |
| `0x08CFB908` | string | `BATTLE TRACK 2` (shop) |
| `0x08CFB960` | string | `TRADE PAGES?` |
| `0x08CFBA08` | string | `HEY! YOU DON'T HAVE ENOUGH PAGES TO EXCHANGE FOR THAT! ...` |
| `0x08CFC50C` | string | `NOT USED 1`–`NOT USED 4` (unused) |
| `0x08CFC54C` | string | `CREDITS` |
| `0x08CF7EDC` | string | `ENTER YOUR NAME` (3-slot name entry) |

Text encoding: ASCII bytes, `0x00` terminator, `0x0C` line break, `0x01`
page/section separator in dialogue. The English bank holds 316 text entries
(460 non-empty NUL segments including non-text bytes; 187 entries are
single-line printable-only). Localized banks after `0x08CFC8B6` are compressed
and were not used.

Save file: 512-byte EEPROM image, magic word `0x47503034` ("40PG").
`ERASE SAVE DATA` rewrites it; `SAVING GAME, DO NOT TURN OFF` is displayed when
leaving the Options screen.

## 5. Algorithm

### 5.1 There is no code/password validator

No function that reads a code buffer was found: nothing takes a string
argument, checks a length, compares it against a table or computes a checksum
for entry. The only text editor in the ROM is the 3-slot name screen. The
searches that would have found a validator are listed in §6b. The only input
pipeline is the keypad state:

```
; 0x0802118C
k      = ~*(u16*)0x04000130 & 0x3FF
pressed= k & ~prev
*(u16*)0x0201848C = k          ; held
*(u16*)0x0201848E = pressed     ; new this frame
prev   = k
```

Everything else (menus, racing) reads `0x0201848C`/`0x0201848E`. Button masks
are the canonical GBA values: A=1, B=2, Select=4, Start=8, Right=0x10,
Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200.

### 5.2 The only text-entry model: 3-character name

```
alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"   # 36 symbols (observed wheel:
                                                     #  ... W X Y Z 0 1 2 3 ...)
slots    = 3
cursor   = slot index 0..2
Left/Right: alphabet index = (index ± 1) mod 36
A:          cursor += 1; if cursor == 3 -> commit name and return
space    = 36^3 = 46,656 fixed-length names
```

This is a player-name field (shown as `DEFAULT NAME` and in records). It is not
validated, not compared with any table, and has no checksum. Its length is
proven by the three slots: a fourth A press commits and exits instead of
creating a fourth slot.

### 5.3 The Cheato shop gate (observed)

```
if selected_entry.visible:                 # only unlocked entries are listed
    if cheato_pages < entry.cost:
        show "HEY! YOU DON'T HAVE ENOUGH PAGES TO EXCHANGE FOR THAT!"
    else:
        pages -= entry.cost
        set unlock flag                        # inferred from item text
        play "sold" / unlock dialogue          # inferred; not purchased here
```

`visible` is what filters the 21-name catalogue down to the four entries on a
fresh save. The exact table address/record layout was not recovered; the names,
the four displayed costs and the rejection are observed (see §8).

## 6. Tables

### 6.1 Cheato catalogue (21 entries)

All 21 names are contiguous in the English text bank and are the shop's item
strings. "Observed" means shown in the shop on a fresh save; "gated" means the
string exists but the entry is filtered out until its condition is met. Prices
are from the shop (observed) or GameFAQs (published); character prices are not
published and their entries are gated, so they are unresolved.

| # | String address | Item | Price | Condition | Fresh-save visibility |
|---:|---|---|---:|---|---|
| 1 | `0x08CFB82C` | GREEN GLOWBO GP | 250 | none | **observed** |
| 2 | `0x08CFB83C` | PURPLE GLOWBO GP | 150 | none | **observed** |
| 3 | `0x08CFB84D` | GREEN GLOWBO TT | 250 | beat one lap + one track record in Time Trial | gated |
| 4 | `0x08CFB85D` | PURPLE GLOWBO TT | 150 | beat one lap + one track record in Time Trial | gated |
| 5 | `0x08CFB86E` | GREEN GLOWBO JC | 250 | win Bottles GP Beehive Cup | gated |
| 6 | `0x08CFB87E` | PURPLE GLOWBO JC | 150 | win Bottles GP Beehive Cup | gated |
| 7 | `0x08CFB88F` | HUMBA WUMBA | unresolved | beat her in the Jiggy Cup boss duel | gated |
| 8 | `0x08CFB89B` | JOLLY ROGER | unresolved | beat him in the Pumpkin Cup boss duel | gated |
| 9 | `0x08CFB8A7` | KLUNGO | unresolved | beat him in the Skull Cup boss duel | gated |
| 10 | `0x08CFB8AE` | GRUNTILDA | unresolved | beat her in the Broomstick Cup boss duel | gated |
| 11 | `0x08CFB8B8` | BOTTLES | unresolved | win every Bottles-GP Jiggy Challenge track with all 6 Jiggies | gated |
| 12 | `0x08CFB8C0` | GRUNTY T.T. | 250 | win Grunty GP Broomstick Cup | gated |
| 13 | `0x08CFB8CC` | GRUNTY J.C. | 550 | win Bottles GP Feather Cup | gated |
| 14 | `0x08CFB8D8` | RARE T.T. | 800 | complete both Time Trial modes | gated |
| 15 | `0x08CFB8E2` | JINJO G.P. | 500 | win Grunty GP Broomstick Cup | gated |
| 16 | `0x08CFB8ED` | STOP N SWAP | 999 | beat all Rare Time Trial records | gated |
| 17 | `0x08CFB8F9` | BATTLE TRACK 1 | 100 | none | **observed** |
| 18 | `0x08CFB908` | BATTLE TRACK 2 | 100 | none | **observed** |
| 19 | `0x08CFB917` | BATTLE TRACK 3 | 100 | win Bottles GP Feather Cup | gated |
| 20 | `0x08CFB926` | BATTLE TRACK 4 | 100 | win Grunty GP Broomstick Cup | gated |
| 21 | `0x08CFB935` | PHOTO ALBUM | 999 | all platinum trophies + all Jiggy Challenges + all Time Trials | gated |

Observed shop page (fresh save, 0 pages), in order:

```
GREEN GLOWBO GP    250 PAGES
PURPLE GLOWBO GP   150 PAGES
BATTLE TRACK 1     100 PAGES
BATTLE TRACK 2     100 PAGES
```

Down on the fourth entry wraps to the first; the list does not scroll and L/R
do not page. This confirms the availability filter: 21 strings, 4 visible.

Related unlock text in the same bank (all discovered by the shop, not codes):

* `0x08CFBBA4` "YOU CAN NOW ENTER ANY RACE PLAYING AS BOTTLES." (and the same
  pattern for Jolly Roger, Humba Wumba, Klungo, Grunty).
* `0x08CFBD70` "YOU CAN NOW RACE AS A FLYING SAUCER!" — an effect of unlocking
  the Jinjo GP that the published lists do not mention.
* `0x08CFBD48` "JINJO GRAND PRIX UNLOCKED."
* `0x08CFBD00` "RARE TIME TRIAL RECORDS UNLOCKED FOR BOTH BOTTLES AND GRUNTY
  MODES."

### 6.2 Name-entry alphabet

`A B C D E F G H I J K L M N O P Q R S T U V W X Y Z 0 1 2 3 4 5 6 7 8 9`
(36 symbols; the wheel visibly wraps `... W X Y Z 0 1 2 3 ...`). Three slots.
No punctuation, no lowercase, no 4th slot.

### 6.3 Unused/related UI strings (verified present)

| String | Address | Status |
|---|---|---|
| `LANGUAGE`, `ENGLISH`, `FRAN`, `DEUTSCH`, `ESPA`, `ITALIANO` | `0x08CF80B4`… | not in this build's Options menu (EU text carried in the shared bank) |
| `MULTIPLAYER WEAPONS` | `0x08CF80F4` | not in the single-cart Options menu |
| `REVERSE CONTROLS` | `0x08CF8130` | unused (TCRF agrees) |
| `NOT USED 1`–`NOT USED 4` | `0x08CFC50C` | unused (TCRF agrees) |
| `SELECT A SLOT` / `ENTER YOUR NAME` | `0x08CF7EC8` / `0x08CF7EDC` | name/records screens, not a code field |

## 6b. Enumeration

**Space definition.** There is no password/code space: no alphabet table for
codes, no fixed-length code field, no checksum, no string-compare table. The
only user-entered strings in the ROM are the three-slot player name
(36 symbols, length exactly 3 → **36³ = 46,656** representable names, stored in
save data and never validated). The other developer-intended cheat surface is
the Cheato shop: **21** named entries, each with a page cost (character prices
unresolved) and an unlock condition; **4/21** are available on a fresh save
and were enumerated on screen.

**Novel codes.** None can exist, so none were minted. This is not a gap in the
search: a generated string has nowhere to be entered. The equivalent
"undocumented combination" deliverable is the catalogue in §6.1 — in
particular the Jinjo-GP flying-saucer effect, which is absent from the
GameFAQs and Rare Gamer lists, and the exact four-entry fresh-save subset.

**Bounds proven by rejection (observed):**

1. Cheato shop, Green Glowbo GP (250) selected with 0 pages → dialogue
   `HEY! YOU DON'T HAVE ENOUGH PAGES TO EXCHANGE FOR THAT! COME BACK FOR IT
   WHEN YOU HAVE ENOUGH PAGES.` (`0x08CFBA08`). Same for every visible entry;
   the purchase path is gated on the page counter.
2. Name entry, three slots: after the third character, A commits and returns
   to Options; a fourth character cannot be created. This bounds the only
   text field to length 3.
3. The shop list itself: 21 names exist in ROM, only 4 pass the availability
   filter; Down wraps after the fourth. This bounds the fresh-save catalogue
   and proves the filter is not a paging artefact (L/R do nothing).

**Text space searched (counts).**

| Measure | Count |
|---|---|
| ROM bytes | 16,777,216 |
| `strings -n 4` runs (whole ROM, mostly compressed data) | 153,142 |
| English UI bank | 18,926 bytes |
| Non-empty NUL segments in the bank | 460 |
| Text entries (ASCII + `0x0C`/`0x01`) | 316 |
| Single-line printable entries | 187 |
| Letters / digits | 2,129 / 12 |
| Distinct printable characters | 54 |
| Case-insensitive `password` / `passcode` / `debug` / `gameshark` / `codebreaker` / `enter code` / `cheat mode` / `level select` | 0 each |
| Case-insensitive `cheat` | 13 — one audio cue label (`Cheato Speech`, file `0x714338`), one menu label (`CHEATO`, `0x08CF8234`), 11 lines of dialogue about Cheato/cheating |
| `CODE` in the UI bank | 0 (the one ROM-wide `code` is audio dev text at `0x3841`) |

**Button space searched (counts).**

| Measure | Count |
|---|---|
| Keypad readers (`0x04000130` literal) | 1 (`0x0802118C`) |
| Literal references to key state `0x0201848C` | 25 (all disassembled) |
| u16 runs of ≥3 distinct single-bit masks in code region | 598 |
| …of those with a 32-bit ROM pointer to an entry | 17 (all inside the 0x08xxxxxx audio/sample area, values not a sequence) |
| byte runs of ≥4 distinct single-bit masks | 271 |
| …with a ROM pointer | 9; the two UI candidates (`0x0805A5BC`, `0x0805A5C8`) are 8/16/32/64 **coordinates** matched by `0x08026E88`, not held-button sequences |
| Cheat-sequence tables with a prefix and action dispatch | 0 |
| Multi-comparison chains against the key word | 0. The `1/2/4/8/16/32/64` chain at `0x0803FC3A` tests the UI state word at `0x0203CA78`, not `0x0201848C` |

**Published list verification.** The GameFAQs page contains 21 Cheato shop
entries, 7 cup entries and one gameplay hint ("press A just before the race
starts for a boost") and **zero codes**. Its 21 shop entries match the 21 ROM
strings exactly, including the four visible ones with identical names and
prices. The published "Jinjo GP 500 pages" figure could not be read in the shop
because the entry is gated; it is recorded as published, not observed. No
completion-gated screen (race results, final standings, credits, photo album)
contains a text field: their strings are in the same bank and are all
display/dialogue text.

## 7. Validation evidence

**Observed (emulator screenshots, mGBA 0.10.5):**

* Boot logos, title, main menu (`SINGLE PLAYER / MULTIPLAYER / OPTIONS`).
* Options: Music Volume, SFX Volume, Default Name, Erase Save Data; no
  Language, Multiplayer Weapons or Reverse Controls entry.
* `ENTER YOUR NAME`: three slots; wheel shows A…Z then 0…9; A advances slots;
  third A commits.
* Single-player grid: six pieces and their labels; Grand Prix, Jiggy Challenge,
  Time Trial, Quickrace, Trophies and Cheato all open.
* Grand Prix: character select (Banjo selected), Bottles dialogue, cup select
  (`HONEYCOMB` + three `???`), race splash `CURRENT RACE: 1/4 SPIRAL MOUNTAIN`,
  race, pause (`CONTINUE / RESTART / QUIT`), quit confirm.
* Time Trial: character select → `SELECT A MODE` (Bottles GP) → Bottles intro
  dialogue → `SELECT A CUP` with `RACE RECORDS BROKEN 0/4` and
  `LAP RECORDS BROKEN 0/4` counters.
* Jiggy Challenge: character select → `SELECT A CUP`.
* Quickrace: character select → `SELECT A MODE` → `SELECT A CUP`.
* Multiplayer: link-cable prompt (single-cart dead end).
* Cheato: room, intro dialogue, shop with the four entries and prices, page
  rejection dialogue, farewell/hint dialogue.
* Trophies: empty 3-D trophy room.
* Erase save: `ERASING GAME, DO NOT TURN OFF`.

**Derived (ROM bytes / disassembly):**

* Header hashes/fields, single logo, valid complement, no patch.
* Text bank boundaries and all quoted strings/addresses.
* Single keypad reader and key-state layout; absence of any mask-sequence
  table after scanning every pointer-referenced candidate.
* 21 shop name strings; 4/21 availability filter; unused strings.

**Inferred:**

* The shop's post-purchase effects (page deduction, unlock-flag write, item
  dialogue) are inferred from the item result text and the published guide;
  no purchase was affordable on a fresh save.
* Character prices are inferred to exist in the gated table but were not read.

## 8. Unknowns

* Exact address/record layout of the Cheato entry table and its per-entry
  condition bits (the 21 names, the four costs and the filter behaviour are
  known; the data structure is not).
* Character-entry prices (Humba Wumba, Jolly Roger, Klungo, Gruntilda,
  Bottles): entries are gated and no price string exists.
* Post-purchase effects were not exercised because a fresh save has 0 pages
  and the cheapest entry costs 100.
* Multiplayer-only options (`MULTIPLAYER WEAPONS`) and the EU language menu
  need a second cartridge / EU build to display.
* The platinum-coloured Rare logo intro is published as an all-platinum reward;
  it was not triggered (requires full completion).

## 9. Tooling

* mGBA 0.10.5 SDL under Xvfb :166 + openbox; `xdotool` key injection;
  `scrot` + ImageMagick crop (`720x480+280+255`).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M
  force-thumb` for the keypad reader, the hit-test helper and the 25 key-state
  xrefs.
* Python 3 scripts (in `/tmp/opencode/banjopilot/tools/`):
  * `ident.py` — header/complement/logo/hash dump.
  * `textscan.py` — bank extraction, string/letter counts, keyword counts.
  * `maskscan.py` — single-bit mask run and pointer scan.
  * `ui.py` — key hold/crop helper.
* Evidence screenshots: `/tmp/opencode/banjopilot/shots/` — key files:
  `03_after.png` (title), `04_boot_start.png` (main), `05_options.png`
  (options), `168_name.png` and `150_one.png` (name entry + wheel showing
  `… Z 0 1 2 3 …`), `24_sp.png` (six-piece grid), `97_cupselect.png` (cups),
  `102_race2.png` (race splash), `105_pause.png` (pause), `63_after_a2.png`
  (Cheato dialogue), `126_shop_right2.png` (shop), `158_buy_reject2.png`
  (page rejection), `56_room_wait.png` (trophies), `121_mp.png` (multiplayer),
  `136_erasing.png` (erase).
* No ROM or extracted assets are redistributed with this report.

### 9.1 Legal note

Only the ROM's structure, strings, addresses and algorithms are documented;
no copyrighted graphics, audio or text banks are reproduced beyond the short
UI strings needed to identify the menus.
