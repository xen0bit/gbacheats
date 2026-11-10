# Care Bears: Care Quest (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Care Bears: Care Quest/Care Bears: Care Quest.gba` |
| Size | 4,194,304 bytes (0x400000, 32 Mbit) |
| Header title | `CARE_BEARS` |
| Game code | `BEAE` |
| Maker code | `GY` |
| Software version | 0x00 |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0) |
| Fixed byte 0xB2 | `0x96` |
| Complement check 0xBD | `0xBD` (valid; `sum(0xA0..0xBC)+0x19+0xBD ≡ 0`) |
| Header checksum 0xBE | `0x0000` |
| MD5 | `10d14cbd9d43d2c4d59da9a7ee64ba95` |
| SHA-1 | `750eb05960ace3bd38c6e362a0f6970ac3371964` |
| SHA-256 | `5e629cae8e999327ba53f580482d7f7a9cb8a1f0b53ca9e8734fcf15e3ad69cf` |
| Save hardware | EEPROM (`EEPROM_V124` at file 0x3D7340); mGBA creates a 512-byte `.sav` |

**Patch/trainer check.** The entry branch is the stock `EA00002E`, the first 4 KiB
contains the normal crt0 and no cracktro/trainer banner. Searches for
`SUNHORS`, `CRC BANDIT`, `MODE7`, `TRAINER`, `CRACK`, `PATCH`, `cracktro`
returned 0 hits. The SHA-1 matches the No-Intro USA dump
(`Care Bears - The Care Quests (USA) (En,Fr,Es)`), so this is the clean retail
image. The header checksum field is 0, which is common in this collection's
dumps; the complement byte is valid.

Embedded-header scan: the Nintendo logo occurs once, at file offset `0x4`.
There is no second GBA header (not a multi-game pack).

## 2. Executive summary

**This ROM has no password, cheat-code, button-code, debug-menu or
code-unlock system.**

The evidence is fourfold:

1. **No code text.** The ROM's text bank and all printable strings contain no
   `PASSWORD`, `CHEAT`, `SECRET`, `UNLOCK`, `GALLERY`, `DEBUG`, `OPTION`,
   `LEVEL SELECT`, `STAGE SELECT`, `SOUND TEST` or `MUSIC TEST` string (0 hits
   each, case-insensitive, over 48,337 printable runs). The only `CODE` hit is
   the binary-noise substring `wcODESh` at 0x36CAF1, not a UI string.
2. **No code surface.** Every interactive screen was walked and disassembled.
   The complete UI is: a 3-flag language selector, a 3-item title menu, a
   12-entry quest selector, a 12-page high-score/medal screen, a 5-page credits
   roll, the quest intros/gameplay, and a 2-choice pause overlay. There is no
   text-entry field, no alphabet entry, no sequence matcher, and no debug scene.
3. **No hidden scene.** The scene archive at `0x08BB94` (`BfGBAM01`) contains
   exactly 16 scenes: `title.mge`, `title_fr.mge`, `selector.mge`, `hiscore.mge`
   and `game1.mge` … `game12.mge`. All 16 are accounted for by observed
   screens. The global scene-state variable `0x03005BA4` is only ever written
   with `{0, 1, 3, 4…16, 18}`, all of which map to observed screens.
4. **No validator.** There is no checksum routine, no accepted-string table, no
   alphabet table, and no function that reads user text. The input layer merely
   exposes ten per-button held/previous bytes; menus read single buttons.

Published-code check: VGChartz, CheatHappens and CheatingDome all list **0
cheats** for this game. GameFAQs and TCRF blocked automated fetches (HTTP 403)
and search snippets show no code list. One low-quality site
(`classicemu.com`) publishes `HEART99` and `UNLOCKALL`; both strings are absent
from the ROM in ASCII, lower-case, upper-case, UTF-16LE, UTF-16BE and
`-0x20`-shifted encodings (0 hits each), and the ROM has no screen on which
letters can be entered. They are fabricated and unenterable.

Because no code system exists, the deliverable is the bounded negative required
by guide §0.2: complete menu enumeration, exhaustive text/button-space counts,
and rejection tests showing that code-like input is not consumed anywhere.

## 3. How to reproduce

Emulator/environment used:

```
Xvfb :229 -screen 0 1024x768x24
DISPLAY=:229 openbox
DISPLAY=:229 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 "Care Bears: Care Quest.gba"
```

mGBA SDL keymap used: `x` = A, `z` = B, `a` = L, `s` = R,
`Return` = Start, `BackSpace` = Select, arrow keys = D-pad. Keys were held
100–300 ms; screenshots were taken from the X root and cropped to the
720×480 (3×) viewport.

Menu path and observations:

1. **Boot splash** (The Game Factory / Nelvana / Sirius Games).
2. **Language selector** — three flags: USA, Canada, Mexico. Selecting
   USA gives the English title `Care Bears: The Care Quests`; Canada gives
   `Les Calinours: Mission calins`; Mexico gives the Spanish title
   `Comenzar partida / Puntuaciones / Créditos`. Exactly three choices.
3. **Title menu** — exactly three entries, in this order:
   `Start Game`, `High Score`, `Credits` (English build).
   A/Start confirms, Up/Down moves, B/Select/Left/Right do nothing.
4. **Select Quest** — 12 entries, each with a bear portrait and a quest title:
   1. It's Good To Have Friends
   2. Hide-And-Seek
   3. All We Need Is Love
   4. A Helping Hand
   5. Let's Play
   6. Sweet Dreams
   7. The Sun Always Shines
   8. Always Look On The Bright Side
   9. I Will Look After You
   10. Let's Share
   11. Lucky Day
   12. When Dreams Come True
   Left/Right page, A/Start confirm, B/Select cancel to title. There is no
   lock icon, no "?" entry, and no 13th entry; Right on quest 12 wraps to 1.
   All 12 were selected and all loaded their intro/gameplay (no locked or
   error screen).
5. **High Score** — 12 pages, one per quest. Left/Right page; A returns to
   title (observed); page 12 wraps to page 1. No extra page.
6. **Credits** — 5 pages: Game Design, Art, Code, Music and sfx,
   Administration; then it returns to the title. No extra/easter-egg page.
7. **Quest intro / tutorial** — one text card per quest, dismissed with A.
8. **Gameplay** — `Get Ready!` banner, HUD (hearts, timer, score), then play.
   In quest 2 the `Level Complete!` (`Nivel completado!`) banner was observed.
   These are normal gameplay transitions, not menus.
9. **Pause** — Start opens `Quit?` with a B icon and an A icon. B resumes,
   A quits to the quest selector. Select/L/R do nothing while paused; there is
   no options entry.

Published codes tested:

| Source | Claim | Result |
|---|---|---|
| VGChartz | "Total cheats available: 0" | No codes to test |
| CheatHappens | "no cheats or cheat codes" | No codes to test |
| CheatingDome | "No Cheats or Achievements yet" | No codes to test |
| GameFAQs / TCRF | pages returned HTTP 403 to automated fetch | No list recovered; search snippets show none |
| classicemu.com | `HEART99`, `UNLOCKALL` | Both absent from ROM in 6 encodings; no text-entry screen exists; rejected as fabricated |

Button tests performed (all with screenshots):

* Title: single Select, L, R, B produced no state change; A/Start/Up/Down
  behaved as the 3-item menu. Simultaneous `L+R`, `L+R+Select`,
  `A+B+Select`, `L+R+A` produced no hidden screen (A/Start-containing
  combinations simply activate the selected menu item).
* Select Quest: L and R produced no page change; B/Select returned to title.
* Pause: Select, L and R produced no change; B resumed, A quit.
* Gameplay: Select during `Get Ready!` produced no change.

## 4. Address map

All addresses are ROM addresses unless marked RAM.

| Address | Meaning |
|---|---|
| `0x08000000` | ROM base |
| `0x080000C0` | Stock crt0 entry |
| `0x080004CC` | Title-menu update (A/Start confirm, Up/Down move) |
| `0x08000A80` | Select-Quest update (B/Select cancel, Left/Right page, A/Start confirm) |
| `0x08001971` | Selector page-update block (credit roll observed; 5 pages) |
| `0x08002300` | High-score page update (draws quest title + `High Score`, 12 pages) |
| `0x08002480` | Results/score routine; `SELECT SYMBOL` branch at `0x080026A6` |
| `0x08012E78` | Input read/init: reads `KEYINPUT`, stores current mask |
| `0x08012EB4` | Input edge update: fills held/previous byte arrays |
| `0x03005B40` (RAM) | Input state: +0x00…+0x09 held bytes (A,B,Select,Start,Right,Left,Up,Down,R,L), +0x0A…+0x13 previous bytes, +0x14 u16 mask |
| `0x03005BA4` (RAM) | Global scene state |
| `0x03004A0C` (RAM) | Current menu/page index |
| `0x083D7FA0` | UI text bank start (`GET_READY`, `GAME_OVER`, …) |
| `0x083D7D8C` | Scene/resource name table |
| `0x08BB94` | Scene archive `BfGBAM01`, 16 entries |
| `0x083D7340` | `EEPROM_V124` save driver string |
| `0x083D7DA0` / `0x083D7DAC` / `0x083D7DB8` | Resource names `start_game`, `highscore`, `credits` |

Title menu resource names (file 0x3D7D8C–0x3D7DC0):

```
title.mge
menu
start_game
highscore
credits
title_fr.mge
```

The pointer table at file 0x480 lists the three title resources
(`0x083D7DA0`, `0x083D7DAC`, `0x083D7DB8`), confirming the 3-item menu in both
the English and localized builds.

## 5. Algorithm

### 5.1 Input layer

The game does not poll a key mask per handler. It builds a 10-button state
structure once per update:

```c
raw      = REG_KEYINPUT;            // 0x04000130, active-low
current  = (~raw) & 0x03FF;         // A=1,B=2,Select=4,Start=8,Right=0x10,
                                    // Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200
prev     = state->mask;             // 0x03005B40 + 0x14
for (i = 0; i < 10; i++) {
    state->held[i]     = (current >> i) & 1;
    state->previous[i] = (prev    >> i) & 1;
}
state->mask = current;
```

Handlers test an edge with `held[i] && !previous[i]`. The full mask at `+0x14`
is written by the input update but **never read** by game code (0 readers
found), and there is no press-history/ring buffer beyond the one previous
frame. This is the structural reason a multi-press sequence code cannot exist.

### 5.2 Menu model

Each screen is a small state machine with a bounded index:

```c
if (pressed(A) || pressed(Start)) { play_confirm(); state = target[index]; }
if (pressed(Up)   && index > first) index--;
if (pressed(Down) && index < last)  index++;
if (pressed(B) || pressed(Select)) { state = STATE_TITLE; }
```

There is no text buffer, no checksum, no alphabet table, no accepted-code
table, and no function that reads letters. The ROM uses the standard
`EEPROM_V124` save driver; no code validator is present.

### 5.3 Scene state set

Immediate writes to `0x03005BA4` were enumerated. The values used are:

```
0   boot/init
1   title
3   Select Quest
4…15  quests 1…12
16  credits
18  high score
```

No immediate write outside this set was found; values 2, 17 and 19+ were not
observed. Every value in the used set was observed as a screen or transition;
there is no unreached debug state.

## 6. Tables

### 6.1 Button encoding

| Bit | Mask | Button |
|---:|---:|---|
| 0 | 0x001 | A |
| 1 | 0x002 | B |
| 2 | 0x004 | Select |
| 3 | 0x008 | Start |
| 4 | 0x010 | Right |
| 5 | 0x020 | Left |
| 6 | 0x040 | Up |
| 7 | 0x080 | Down |
| 8 | 0x100 | R |
| 9 | 0x200 | L |

### 6.2 Screen/input inventory

| Screen | Entries/pages | Buttons actually consumed | Select/L/R effect |
|---|---:|---|---|
| Language selector | 3 | Right/Down + A (observed) | none |
| Title | 3 | A, Start, Up, Down | none (observed) |
| Select Quest | 12 | B, Select, A, Start, Left, Right | Select = cancel; L/R = none |
| High Score | 12 | A observed; B/Start read by handler; Left/Right page | none observed |
| Credits | 5 | A observed; A/Start/Left/Right/B read by handler | none |
| Quest intro | 12 cards | A | none |
| Pause | 2 actions | Start, B, A | none (observed) |

No screen reads all ten buttons, and no screen compares a multi-button mask or
accumulates a press sequence.

### 6.3 Scene archive

`BfGBAM01` at file 0x08BB94, entry count 0x10 (16):

```
title.mge        title_fr.mge     selector.mge     hiscore.mge
game1.mge        game2.mge        game3.mge        game4.mge
game5.mge        game6.mge        game7.mge        game8.mge
game9.mge        game10.mge       game11.mge       game12.mge
```

No `debug.mge`, `test.mge`, `password.mge`, `gallery.mge` or extra scene.

### 6.4 UI text bank

Representative strings and file offsets:

| Offset | String |
|---|---|
| 0x3D7FA0 | `GET_READY` |
| 0x3D7FAC | `GAME_OVER` |
| 0x3D7FB8 | `LEVEL_COMPLETE` |
| 0x3D7FC8 | `CONGRATULATIONS` |
| 0x3D7FD8 | `QUIT` |
| 0x3D7FE0 | 12 English quest titles |
| 0x3D80F8 | 12 French quest titles |
| 0x3D822C | 12 Spanish quest titles |
| 0x3D8364 | `High Score` / `Meilleur score` / `Puntuación` |
| 0x3D838C | `Select Quest` / `Choisis une mission` / `Seleccionar aventura` |
| 0x3D83C8 | English quest instructions (12 pairs) |
| 0x3D8AE8 | French quest instructions |
| 0x3D92F8 | Spanish quest instructions |
| 0x3D9AF0 | `Get Ready!` / `Game Over!` / `Level Complete!` / `Congratulations!` / `Quit?` |
| 0x3DA050 | `SELECT SYMBOL` (conditional label; see §8) |

No password/options/sound-test/gallery/debug text exists in this bank or
anywhere else in the image.

### 6.5 Published-code verification

| Code | Source | In ROM? | Enterable? | Verdict |
|---|---|---|---|---|
| `HEART99` | classicemu.com | No (6 encodings, 0 hits) | No text-entry screen | Fabricated |
| `UNLOCKALL` | classicemu.com | No (6 encodings, 0 hits) | No text-entry screen | Fabricated |
| (none) | VGChartz / CheatHappens / CheatingDome | — | — | 0 genuine cheats listed |

## 6b. Enumeration

### Space definition

This title has **no code space**:

* alphabet: none
* code length(s): none
* checksum: none
* reserved bits: none
* lookup table: none
* representable passwords/codes: **0**

The only finite user-input spaces are menu selections:

| Space | Size |
|---|---:|
| Language selector | 3 |
| Title menu | 3 |
| Quest selector | 12 |
| High-score pages | 12 |
| Credits pages | 5 |
| Pause actions | 2 |
| Button-sequence codes | 0 (no matcher) |

Total distinct menu selections: 3+3+12+12+5+2 = 37, all enumerated above.
No selection is a cheat, a password, or a debug gate.

### Novel code(s)

**None, and none can exist.** There is no validator to satisfy and no input
field to type into. The §0.2 "novel code accepted in-game" requirement is
vacuous for this ROM; the equivalent deliverable is the proof that the code
space is empty and that every screen/button surface has been enumerated.

### Bounds proven by rejection

| Test | Input | Result |
|---|---|---|
| Out-of-alphabet code | `HEART99` | Not representable: 0 occurrences in ROM in ASCII/lower/upper/UTF-16LE/UTF-16BE/+0x20 shift; no text-entry screen |
| Out-of-alphabet code | `UNLOCKALL` | Same; fabricated |
| Wrong button on title | Select, L, R, B | No state change (title remains) |
| Wrong button in quest select | L, R | No page change |
| Wrong button while paused | Select, L, R | Pause overlay remains |
| Forged multi-button combo | `L+R`, `L+R+Select`, `A+B+Select`, `L+R+A` on title | No hidden screen; only A/Start-containing combos activate the selected item |
| Extra menu entry | Right on quest 12 / page 12 | Wraps to 1; no 13th entry |
| Hidden scene | Scene archive count | Exactly 16; all accounted for |
| Hidden state | Global state writes | Only `{0,1,3,4…16,18}`; all observed |

### Proof that no hidden debug screen exists

1. The only scene archive in the ROM declares 16 entries; all 16 names are
   either a menu (`title`, `title_fr`, `selector`, `hiscore`) or one of the 12
   quests. There is no unnamed archive and no second GBA header.
2. The global scene-state variable has a closed write set of 17 distinct
   values (`0,1,3…16,18`), all of which were reached or observed as
   transitions. A debug screen would require a state value outside this set.
3. Every menu handler was disassembled and dynamically exercised. None reads
   Select/L/R as a gate, and none maintains a press history or compares a
   multi-button mask.
4. The full text bank contains no `DEBUG`, `TEST`, `PASSWORD`, `CHEAT`,
   `SECRET`, `UNLOCK` or `GALLERY` string; the only engine-internal debug
   string is `importScene('%s')...0x%08x\n` at 0x3DA988, which is a resource
   loader trace, not an in-game screen.

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| ROM identity and clean USA dump | Observed | Hashes above; No-Intro SHA-1 match |
| No patch/trainer | Observed | Stock entry `EA00002E`, stock crt0, 0 keyword hits |
| Title has 3 entries | Observed + Derived | Screenshots; resource names and pointer table at 0x480; handler 0x080004CC |
| Quest selector has 12 entries | Observed + Derived | 12 screenshots; handler 0x08000A80; right-wrap code at 0x080026BE |
| High score has 12 pages | Observed | 12 page screenshots; wrap to page 1 |
| Credits has 5 pages | Observed | 5 distinct pages then title |
| Language selector has 3 options | Observed | English, French and Spanish titles all reached |
| No text-entry surface | Derived | No text buffer or alphabet in any handler; all input is menu-only |
| No button-sequence matcher | Derived | Input state is 10 held + 10 previous bytes; mask at +0x14 never read; all handlers enumerated |
| No hidden scene | Derived | 16-entry scene archive; state set `{0,1,3…16,18}` |
| `HEART99`/`UNLOCKALL` fabricated | Observed + Derived | 0 hits in 6 encodings; no entry screen; dynamic button tests |
| Pause has only B/A | Observed | B resumes, A quits; Select/L/R no effect |
| `Level Complete` is a normal banner | Observed | Quest 2 completion showed `Nivel completado!`, then next level |

## 8. Unknowns

* **`SELECT SYMBOL` (file 0x3DA050).** This string is referenced once, at
  `0x080026A6`, in the results/score routine (`0x08002480`). It is selected
  when a condition on the menu index is 2; no input path or global state was
  found that makes it a separate screen. It is classified as a conditional or
  unused label (Inferred), not a cheat surface.
* **High-score medal thresholds.** The 12-page screen shows gold/silver/bronze
  bear and score fields. The exact score thresholds are outside the cheat
  question; the screen is a normal score-achievement display, not a code gate.
* **Ending text.** All 12 quests were entered; quest 2's first level was
  completed and its `Level Complete` banner observed. The `CONGRATULATIONS`
  ending string is a normal completion message; the state/input/scene analysis
  above is independent of completion and cannot hide a code system.
* **GameFAQs/TCRF.** Both returned HTTP 403 to automated fetches; no archived
  cheat list was recovered. The three accessible cheat databases list zero
  codes, and the two claimed codes on one low-quality site were disproved.

## 9. Tooling

* `mGBA 0.10.5` under `Xvfb :229` + `openbox`, `SDL_AUDIODRIVER=dummy`.
* `xdotool` for XTEST key events; `ImageMagick` (`import`, `convert`) for
  screenshots and crops.
* `arm-none-eabi-objdump -M force-thumb` for targeted disassembly.
* Python 3 + `capstone 5.0.7` for whole-ROM instruction scans (literal-pool
  loads of `0x03005B40`, input-offset reads, state writes).
* Python scripts: literal search, encoding-variant search, scene-name
  enumeration, header parse.
* No ROM, graphics, music or long text is redistributed with this report.
