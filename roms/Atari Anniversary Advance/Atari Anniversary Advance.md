# Atari Anniversary Advance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Atari Anniversary Advance/Atari Anniversary Advance.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `ATARI_ANNIVE` |
| Game code | `AAVE` |
| Maker code | `70` |
| Software version | `0x00` (Rev.00) |
| Entry branch | `0xEA00002E` → `0x080000C0` |
| Fixed byte `0xB2` | `0x96` |
| Main unit / device | `0x00` / `0x00` |
| Complement check | stored `0x3C`, computed `0x3C` (valid) |
| Header checksum | stored `0x0000`, computed `0x05C4` (tolerated, as in other Digital Eclipse GBA builds) |
| MD5 | `5557fb798b7e5b05016d8269ddb9e20b` |
| SHA-1 | `aba3caa1f7ef8df5036ed735916fa04f74f2f29f` |
| SHA-256 | `969ef0f31b79318186fa9c0afbe645bfc5b5fd95faaa06fd495765dc7906611a` |
| Save type | none observed: mGBA produced a 0-byte `.sav`; the game never wrote save data and a cold boot returns to defaults |

**Embedded-header scan.** The 156-byte Nintendo logo was searched for across the
whole file. Exactly **one** hit exists, at file offset `0x000004` (header
`0x000000`); there is no second GBA image, multiboot client, or concatenated
game. This is a single 4 MiB image containing a shell (`0x08000000`–roughly
`0x08070000`), six emulated arcade ROM sets and graphics above that, and the
trivia bank in the shell’s text region.

**Structure.** The cartridge is a six-game compilation plus one quiz mode:

| Carousel # | Entry | Kind |
|---:|---|---|
| 1 | Asteroids | emulated arcade game |
| 2 | Battlezone | emulated arcade game |
| 3 | Centipede | emulated arcade game |
| 4 | Missile Command | emulated arcade game |
| 5 | Super Breakout | emulated arcade game |
| 6 | Tempest | emulated arcade game |
| 7 | Atari Trivia Challenge | native quiz mode |

## 2. Executive summary

**There is no password system, no button code, no hidden/debug menu, and no
unlockable content in this ROM.** The only developer-intended “cheat switches”
are the six per-game **option pages**, which expose the arcade DIP-switch
settings as a menu: number of players, lives/ships, bonus thresholds,
difficulty, game type, control scheme, and message language. There are **31
fields** across the six pages and **3,200 single-page settings combinations**;
if all six pages are set independently they define
**633,318,697,598,976** global configurations. No checksum, code, or hidden
value exists in that space.

A settings combination that appears in no published list was minted and
confirmed in-game:

> **Tempest:** 1 player, Landscape, **5 lives**, **bonus life every 10,000**,
> **Easy**, **Spanish**.

On launch Tempest displays the Spanish level-select prompt (`GIRE LA PERILLA
PARA EMPEZAR / OPRIMA FIRE PARA SELECCIONAR`) and the HUD shows **four spare
ship icons**, i.e. five lives total. The default is `3` lives / `20,000` /
`Medium` / `English`.

Bounds were proven by UI rejection: the `Lives to Start` field has exactly four
values and cycles

```
3 → 4 → 5 → 2 → 3
```

so an attempt to move past `2` wraps to `3`; `1`, `0`, `6`, and any other value
cannot be selected. `Super Breakout → Game Type` similarly cycles exactly three
values (`Cavity → Double → Progressive`), and no fourth value exists.

The quiz mode has a second enumerable system: a **76-record question bank** at
`0x080B468C`. Each record begins with `@` + a category letter + a **correct-answer
button letter** (`L`, `R`, `A`, or `B`), then the question and four answers.
That is the answer key, not a cheat code, but it is in the ROM and is not on
GameFAQs, VGChartz, or TCRF. Two independent questions were answered from the
key and produced `Correct!`; a deliberately wrong button produced `Sorry.
Incorrect!` and one of the three strike slots, which proves the four-button
answer space. Three strikes end the quiz (`Game Over / Thanks for playing.`).

Published material contains no in-game codes for this title. The GameFAQs page
lists only a gameplay exploit (Asteroids: hide behind the scoreboard); the only
device codes in circulation are Action Replay/CodeBreaker memory patches, which
are outside this engagement’s scope.

## 3. How to reproduce

### Emulator

```bash
Xvfb :147 -screen 0 1024x768x24 &
DISPLAY=:147 openbox &
cd "roms/Atari Anniversary Advance"
DISPLAY=:147 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 "Atari Anniversary Advance.gba" &
```

mGBA 0.10.5 (SDL), window 720×480 at `+154+184` (3× 240×160). Default keymap:
A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
Hold keys 150–250 ms. Savestates: `Shift+F1`–`Shift+F9` save, `F1`–`F9` load.

### Menu paths

* Boot → Infogrames splash → Digital Eclipse splash → title (`PRESS START`).
* Title: **Start** (or A/B/Select) → **carousel**.
* Carousel, play mode (`Select Game To Play`):
  * Left/Right = previous/next entry (wraps after Trivia to Asteroids);
  * Up or Down = switch to `Change Game Options`;
  * A = launch the selected game (or enter Trivia).
* Carousel, options mode (`Change Game Options`):
  * Left/Right = previous/next entry;
  * Up or Down = switch back to play mode;
  * A = open the selected game’s options page (Trivia has no page; it starts
    the quiz directly).
* Options page:
  * Up/Down = select row; Left/Right = previous/next value (wraps);
  * A = leave the page; B does nothing; Start does nothing.
* In a game: **Start** = pause → `Continue` / `Main Menu` (only two items);
  Down + A selects `Main Menu`.
* Trivia: answer with the button shown beside each answer (`L`, `R`, `A`, `B`).
  Wrong answer or timer expiry adds a red X; three X icons end the quiz.

### Screen enumeration

Every reachable shell screen was walked: Infogrames splash, Digital Eclipse
splash, title, carousel in play mode, carousel in options mode, the six per-game
option pages, the in-game pause menu, a trivia question, trivia
correct/incorrect feedback, and the trivia game-over screen. The carousel has
exactly seven entries and wraps; no eighth entry, credits page, sound test, or
debug page is reachable from any of the 10 single buttons or 45 button pairs.

### Minted configuration (Tempest)

1. Carousel → select `TEMPEST`.
2. Down (`Change Game Options`) → A.
3. Set fields with Down/Right:

| Row | Field | Value |
|---:|---|---|
| 1 | Number of Players | 1 |
| 2 | Game View | Landscape |
| 3 | Lives to Start | **5** (Right ×2 from 3) |
| 4 | Bonus Lives Every | **10,000** (Right ×7 from 20,000) |
| 5 | Game Difficulty | **Easy** (Right ×2 from Medium) |
| 6 | Game Messages in | **Spanish** (Right ×3 from English) |

4. A (leave page) → Up (play mode) → A (launch).
5. At the level select, A (Fire) starts the game.
6. HUD top-left shows four yellow spare ships (5 lives); all prompts are Spanish.

Screenshots: `screenshots/09_options_tempest_default.png`,
`10_options_tempest_max.png`, `11_tempest_level_select_spanish.png`,
`12_tempest_five_lives.png`, `13_tempest_lives_crop.png`.

### Bounds test

On `Lives to Start` (Centipede page), place the cursor on row 3 and press Right
four times, capturing each step:

```
5 → 2 → 3 → 4 → 5
```

`screenshots/21_bounds_lives_wrap_5to2.png` (the 5→2 wrap) and
`24_bounds_lives_cycle_montage.png` (all four states). No fifth value, and no
`1`, `0`, or `6`, is reachable. `screenshots/22_bounds_sb_type_progressive.png`
shows the third and last Super Breakout game type; the next Right wraps to
`Cavity`.

### Published material checked

* GameFAQs GBA cheats page (archived 2018 snapshot, direct fetch 403): the only
  entry is “Asteroids: fly behind the scoreboard to become invincible” — a
  gameplay exploit, not an input code. Current search snippets add no GBA
  password/button code.
* VGChartz: search results did not surface a cheats page for this title; the
  only “Total cheats available: 0” hit was the unrelated Activision Anthology.
* TCRF: no reachable `Atari_Anniversary_Advance` page (direct 403, archive 404).
* Ethereal Games / JeuxMangas: Action Replay and CodeBreaker **memory patch**
  codes only (`Asteroids: Infinite Lives`, etc.), excluded by scope.
* No published in-game code was found, therefore none could be “verified as
  working”; this is a bounded negative, not an untested omission.

## 4. Address map

File offset → ROM address is `+0x08000000`.

| ROM address | Size / range | Meaning | Confidence |
|---|---|---|---|
| `0x080000C0` | — | ARM crt0 entry; sets up stacks and jumps to shell | derived |
| `0x0800029E`–`0x0800031C` | — | shell init; writes screen state 1, cursor, key globals | derived |
| `0x080048C0`–`0x08004A40` | — | menu value handler: reads key edges, cycles a value, redraws row | derived |
| `0x08004C00`–`0x08004E00` | — | carousel/“Change Game Options” handler; draws the B-label | derived |
| `0x08004DE2`–`0x080050E0` | — | options page handler (row/value input, `!N` limit checks) | derived |
| `0x080050CC` | — | sets screen state 3 on A (launch transition) | derived |
| `0x080053B8` | — | sets screen state 2 (carousel/quiz entry variant) | derived |
| `0x08005D40`–`0x08005FC4` | — | text parser: splits `@`/`!N`, builds value tilemaps; font index table at `0x08078BC8` | derived |
| `0x08006380` | — | page-layout selector, 7 pages (`1`–`7`) | derived |
| `0x080064B4`, `0x080065BC` | — | transition/wipes between pages | derived |
| `0x080B3F38`–`0x080B468C` | `0x754` | **options text bank**, 6 blocks, `!N` value counts | observed + derived |
| `0x080B468C`–`0x080B6800` | `0x2174` | **trivia question bank**, 76 records | observed + derived |
| `0x080B6824`–`0x080B6978` | — | trivia/menu UI strings (`Select Game To Play`, `Correct!`, …) | observed |
| `0x0835C668` | — | text-engine descriptor: pointers to options bank, trivia bank, UI strings | derived |
| `0x080C0000`+ | — | embedded arcade ROM/graphics data (not reversed) | inferred |

RAM (from mGBA savestates; `gbAs` chunk, IWRAM base `0x19000`, EWRAM base
`0x21000`):

| Address | Size | Meaning | Confidence |
|---|---|---|---|
| `0x03000000`–`0x03007FFF` | 32 KiB | IWRAM (unchanged by option edits) | observed |
| `0x02000000`–`0x0203FFFF` | 256 KiB | EWRAM shell state and buffers | observed |
| `0x02021DA8` | 1 | **screen state**: 0 = game/pause overlay, 1 = carousel, 2 = carousel/quiz entry variant, 3 = launch transition, 4 = quiz question, 5 = options page | observed |
| `0x020101AC` | 1 | carousel rotation/cursor counter (not the game index) | observed |
| `0x020111D0` | 2 | pressed-key edges (active-high) | derived |
| `0x020101BC` | 2 | current keys, active-high (`~KEYINPUT & 0x3FF`) | derived |
| `0x020101B4` | 2 | previous keys | derived |
| `0x020101B8` | 1 | current field’s value count parsed from `!N` | inferred |
| `0x02022248` | 5 | Battlezone option index bytes (row order) in the text workspace | observed (savestate diff) |
| `0x02022259` | 6 | Tempest option index bytes (row order) in the text workspace | observed (savestate diff) |
| `0x02021DAC` | 1 | mode flag (1 in options/carousel) | observed |

The option-index address moves with the parsed page (the workspace is written
by the text engine), so the stable way to read a value is the UI, not a fixed
RAM address. For Battlezone the indices appeared at `0x02022248..0x0202224C`;
for Tempest at `0x02022259..0x0202225E`, both one byte per row.

## 5. Algorithm

### 5.1 Option/DIP page model

Each page is one NUL-terminated block in the options text bank. A block is a
sequence of fields:

```
@ !N <label><value 0><value 1>...<value N-1> !N <label>... !1 <padding>
```

* `!N` gives the number of selectable values for the following field. The
  parser at `0x08005D40` reads that digit into the current-field count
  (`0x020101B8`) and renders the N value strings at fixed columns.
* The field’s selected index is one byte in the text workspace. Changing it
  with Left/Right repaints the value string immediately.
* A (`0x080050CC`) sets screen state 3 and launches the selected game; the
  per-game settings are copied into the emulated machine’s configuration.
* The six pages map to the six text blocks; the text-block order in the
  file is Centipede, Super Breakout, Asteroids, Battlezone, Missile Command,
  Tempest, but the page-to-game mapping is by game ID, not by file order
  (`Asteroids` correctly shows the `Control Scheme / Ships to Start` block).

Pseudocode for the only “cheat switch” interaction:

```c
int idx[ROWS];                 // per-page value indices, one byte each
for (row = 0; row < rows; row++) {
    if (pressed(RIGHT)) idx[row] = (idx[row] + 1) % count[row];
    if (pressed(LEFT))  idx[row] = (idx[row] + count[row] - 1) % count[row];
    draw_value(row, idx[row]); // value string from the !N list
}
```

There is no checksum, no reserved value, no hidden index, and no code path that
accepts an index outside `0 .. count[row]-1`; the modulo wrap is the bound.

### 5.2 Trivia answer key

The bank is a concatenation of records:

```
'@' <category> <correct-button> <question text with CR line breaks>
    <answer L> '\n' <answer R> '\n' <answer A> '\n' <answer B> '\n'
```

`<category>` is `G`, `A`, `T`, `B`, `M`, `S`, or `C`. The **second letter is the
button that answers the question correctly**. The screen prints the four
answers with `L`, `R`, `A`, `B` icons, so the key is directly usable:

```python
tag = record[1:3]              # e.g. "GA"
correct = tag[1]               # 'A' -> press A
```

Observed confirmations:

| Question (paraphrased) | Tag | Key | Result |
|---|---|---|---|
| Nolan Bushnell’s original Atari business partner | `GA` | A (third answer, Ted Dabney) | `Correct!`, score 452 |
| 1982 Atari fast-food promotion | `GL` | L (first answer, McDonald’s) | `Correct!`, score 854 |
| First coin-operated video game, answered L (Space Wars) | `GA` | A (Computer Space) | `Sorry. Incorrect!`, one X |

Three X icons end the quiz. The three circles at the top-right are the three
strikes; a correct answer leaves them unchanged, a wrong answer or timeout
turns one into a red X.

## 6. Tables

### 6.1 Option pages

Counts are from the `!N` tags in `0x080B3F38`; each was also walked in the UI.

| Game | Rows | Field → values | Combinations |
|---|---:|---|---:|
| Asteroids | 4 | Players 1/2; Control Default/Alternate; Ships 3/4; Language EN/DE/FR/ES | 2·2·2·4 = **32** |
| Battlezone | 5 | Control Default/Alternate; Tanks 3/4/5/2; First Bonus 15k/25k/50k/NEVER; Missiles 10k/20k/30k/5k; Language | 2·4·4·4·4 = **512** |
| Centipede | 6 | Players 1/2; View Landscape/Portrait; Lives 3/4/5/2; Bonus 12k/15k/20k/10k; Difficulty Easy/Hard; Language | 2·2·4·4·2·4 = **512** |
| Missile Command | 5 | Players 1/2; Control Default/Alternate; Cities 6/7/4/5; Bonus City 10k/12k/14k/15k/18k/20k/NEVER/8k; Language | 2·2·4·8·4 = **512** |
| Super Breakout | 5 | Players 1/2; View Landscape/Portrait; Length 3/5 balls; Type Cavity/Double/Progressive; Language | 2·2·2·3·4 = **96** |
| Tempest | 6 | Players 1/2; View Landscape/Portrait; Lives 3/4/5/2; Bonus 20k/30k/40k/50k/60k/70k/NEVER/10k; Difficulty Medium/Hard/Easy; Language | 2·2·4·8·3·4 = **1536** |

Totals: **31 fields**, **3,200 single-page combinations** (633,318,697,598,976
global configurations if all six pages are set independently). Language is four
values on every page (English, German, French, Spanish).

Note: the raw Super Breakout text contains the run-together string
`Cavity   Doubleogressive` (the `Pr` is lost in the fixed-column padding). The
screen renders the three values correctly as `Cavity`, `Double`, `Progressive`;
the `!3` count is authoritative.

### 6.2 Trivia bank

| Property | Value |
|---|---|
| Location | `0x080B468C`–`0x080B6800` |
| Records | **76** |
| Categories | G 24, A 12, T 11, B 10, M 10, S 5, C 4 |
| Answer buttons | L 19, R 20, A 20, B 17 (sums to 76) |
| Choices per record | 4 (exactly) |
| Answer space | 76 × 4 = **304 answer cells**, 76 correct |
| Strikes | 3 X icons; 3rd ends the quiz |

### 6.3 Option-index examples (savestate observations)

| Page | Address | Bytes |
|---|---|---|
| Battlezone (Control=Alternate, Tanks=4) | `0x02022248` | `01 01 00 00 00` |
| Tempest (1P, Landscape, 5 lives, 10k, Easy, Spanish) | `0x02022259` | `00 00 02 07 02 03` |

## 6b. Enumeration

### Space definition

* **Option/DIP system:** 6 independent per-game pages; 31 fields; each field is
  an index into a text-declared list. No alphabet, no length, no checksum, no
  serial. The six pages offer **3,200 single-page combinations** in total
  (32 + 512 + 512 + 512 + 96 + 1536); if all six pages are set independently,
  the global configuration space is **32 × 512 × 512 × 512 × 96 × 1536 =
  633,318,697,598,976**. Each page is independently persistent across
  leaving/re-entering the page (observed: Super Breakout `Progressive` survived
  A-exit and A-re-entry).
* **Trivia:** 76 records × 4 answers = **304 answer cells**, exactly one correct
  per record; the key is 76 letters. The quiz tracks 3 strikes (observed
  1 X + 2 circles after one wrong answer; 3 X at game over).

### Novel selection (not in any published list)

**Tempest — 1 player, Landscape, 5 lives, bonus every 10,000, Easy, Spanish.**

* Settings page: `screenshots/10_options_tempest_max.png` shows all six values.
* Launch: `screenshots/11_tempest_level_select_spanish.png` shows the Spanish
  prompt and level-select screen.
* In game: `screenshots/12_tempest_five_lives.png`; the HUD crop
  `13_tempest_lives_crop.png` shows four yellow spare-ship icons (active ship +
  4 = 5 lives).
* Default for comparison: `09_options_tempest_default.png` (3 lives / 20,000 /
  Medium / English).

This exact combination is not documented in the manual summary, GameFAQs,
VGChartz, or TCRF; it is a generated selection inside the enumerated space.

### Bounds proven by rejection

* `Lives to Start` on the Centipede page cycles exactly four values. Starting at
  `5`, four Right presses give `2 → 3 → 4 → 5`; the `5 → 2` step is the wrap.
  Screenshots `21_bounds_lives_wrap_5to2.png` and
  `24_bounds_lives_cycle_montage.png`. Values `1`, `0`, `6`, and `7` are not
  reachable.
* `Super Breakout → Game Type` has exactly three values; the third is
  `Progressive` (`22_bounds_sb_type_progressive.png`), and the next Right wraps
  to `Cavity`.
* Trivia: the four answer buttons are exhaustive; a wrong button is rejected
  with `Sorry. Incorrect!` and a strike (`20_trivia_wrong.png`), while the key
  letter is accepted with `Correct!` (`18`, `19`). There is no fifth answer.

### Published-code check

No in-game password/button code exists to enumerate. Bounded evidence:

1. String scan: 40,399 `strings -n 3` lines; the keywords produce one “cheat”
   hit (the Pong quiz question at `0xB477B`), two “DIP” hits in the trivia bank
   (`0xB5E99`, `0xB5FD8`) plus one in embedded data (`0x2CD647`), one “free” hit
   in embedded Missile Command ROM text (`0xD3D71`), and zero `password`,
   `debug`, `secret`, `unlock`, `code`, `hidden`, `scanline`, `blur` hits.
2. Button-sequence scan: no u16 Konami/UDUD/LRBA table, no active-low variant,
   no 8-bit variant, and no run of ≥4 key-mask bytes in the shell code; the only
   such byte runs are `0x08` fills in graphics (`0x1A9xxx`+).
3. State machine: only states `0`–`5` are written anywhere in the shell
   (`0x080002A0`, `0x08000610`, `0x080009B8`, `0x0800101E`, `0x080016FC`,
   `0x08001B38`, `0x08001F0E`, `0x08002164`, `0x08003144`, `0x080031AA`,
   `0x080050CC`, `0x0800538E`, `0x080053B8`, `0x080054CC`, `0x0800566E`,
   `0x08005842`). No `6`/`7` write exists; every observed screen uses 0–5.
4. Carousel: all 7 entries walked; Left from Asteroids wraps to Trivia, Right
   from Trivia wraps to Asteroids; no 8th entry.
5. Button space: all **10 single buttons** and all **45 button pairs** at the
   title, and all **45 pairs** at the carousel, produced only the known title,
   carousel, `Change Game Options`, or launch screens; no hidden screen. (One
   carousel capture, `s+Right`, lost its scrot frame to a read race; the game
   remained on the known carousel screen. Logs: `pairs_title.txt`,
   `pairs_car.txt`, `pairs_car2.txt`, `pairs_car3.txt`; representative
   screenshots `01`–`03`.)
6. Web: GameFAQs has only the Asteroids scoreboard exploit; VGChartz has no
   list; TCRF has no page; the only circulating codes are Action Replay /
   CodeBreaker memory patches (out of scope).
7. No password entry screen or alphabet exists in any walked screen: the game
   only reads the ten GBA buttons; the ASCII banks are rendered output, not an
   input field.

Consequently the “unpublished selection” delivered here is a settings state,
not a code string, and the quiz key is the second generative result.

## 7. Validation evidence

### Observed

* All screens in §3 and the 25 images in `screenshots/`; the strike-row
  comparison is `25_trivia_strike_row.png` (1 X + 2 circles, then 3 X).
* Tempest with 5 lives / 10,000 / Easy / Spanish: Spanish level-select text and
  four spare-ship icons in the HUD.
* Centipede with 5 lives / 10,000 / Easy / Spanish / Portrait: options page
  (`14_options_centipede_max.png`) and running game
  (`15_centipede_portrait_play.png`).
* `Lives to Start` cycle `5 → 2 → 3 → 4 → 5` with screenshots of every step.
* `Game Type` cycle `Cavity → Double → Progressive`.
* Super Breakout `Progressive` persisted after A-exit and A-re-entry.
* Trivia `Correct!` for the `GA` and `GL` keys; `Sorry. Incorrect!` + X for a
  wrong button; three X icons and `Game Over / Thanks for playing.`
* The `.sav` remained 0 bytes throughout; a cold boot returned all options to
  defaults.

### Derived

* Six option blocks and their `!N` counts from `0x080B3F38`; 31 fields, 3,200
  single-page combinations.
* Text parser at `0x08005D40` and page selector at `0x08006380`.
* Screen-state variable `0x02021DA8` and the state writes listed in §6b.
* Trivia tag = category + correct-button from 76 records at `0x080B468C`,
  confirmed by two independent accepted answers.
* No key-sequence table in the shell (exhaustive u16/u8/run scan).

### Inferred

* The exact mapping of each option index to the emulated arcade DIP-switch bits
  was not traced into each 6502 game; the UI-to-machine copy is inferred from
  the visible effects (lives, difficulty, language).
* The quiz’s three-strike rule is inferred from the HUD icons and the observed
  game-over after the X row filled; the per-question timer value was not
  measured.
* The score formula (time/answer points) was not reversed; only that correct
  answers increase it.

## 8. Unknowns

* Full instruction-level trace of the six arcade DIP mappings (which bit each
  menu value writes) is not included; only UI effects were observed.
* The trivia score formula and exact per-question time limit are unresolved.
* Whether a zero-mistake quiz run triggers the unused-looking
  `Congratulations!` string (`0xB6940`) was not achieved; it may be a generic
  string for a perfect run or dead text.
* The embedded 6502 game ROMs and graphics were not reversed; this report treats
  them as opaque emulated targets.
* No legitimate playthrough of every game was performed; option effects other
  than Tempest lives/language and Centipede configuration are inferred from the
  setting names and the arcade originals.

## 9. Tooling

* mGBA 0.10.5 (SDL), Xvfb `:147`, openbox, xdotool, scrot, ImageMagick,
  tesseract 5, `arm-none-eabi-objdump`, Python 3 + capstone 5.
* Savestate parser: mGBA `.ssN` is a PNG with a zlib `gbAs` chunk; decompressed
  layout `+0x19000` = IWRAM `0x03000000`, `+0x21000` = EWRAM `0x02000000`.
* Scripts (next to this report, `analysis/`): `keys.py` (key hold helper),
  `pairprobe.py` (button-space probes; logs `pairs_title.txt`,
  `pairs_car*.txt`), `parse_options.py` (six blocks and `!N` counts),
  `trivia_key.py` (76 tags/keys without printing question text). The OCR answer
  matcher used during the session was `trivia_solve*.py` in the temporary
  workdir and is not needed to reproduce the key.
* Screenshots: `screenshots/01_title.png` … `25_trivia_strike_row.png`.
  Emulator artifacts (`*.sav`, `*.ssN`) are git-ignored and were not published.

## Legal note

No ROM, extracted graphics, music, or scanned manual content is redistributed
here. Only addresses, algorithms, hashes, option tables, and UI screenshots
needed as evidence are included.
