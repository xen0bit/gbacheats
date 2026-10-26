# Backyard Baseball (GBA) — Reverse Engineering Report

Status: complete for the questions asked (in-game code/password/menu systems).
Result: **negative** — this ROM contains no password system, no
coach-name code table, and no developer cheat/debug menu, and the one
published GBA cheat (Options → Select, R, L) is **disproven**: the Options
screen handler never samples R or L, and the advertised effect does not occur.

Scope: in-game / developer-intended input only. No GameShark, CodeBreaker,
Action Replay or memory-edit code is proposed or relied on.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Backyard Baseball/Backyard Baseball.gba` |
| Size | 4,194,304 bytes (0x400000, 32 Mbit) |
| Header title | `BASEBALL2003` |
| Game code | `ACKE` |
| Maker code | `70` |
| Software version | `0x00` |
| Entry branch | `0xEA00002E` (ARM branch to `0x080000C0`) |
| Fixed header byte 0xB2 | `0x96` |
| Main unit / device | `0x00` / `0x00` |
| MD5 | `688caad7531ec6956aebbca88f07e857` |
| SHA-1 | `657a639ab3ffbfc85c7a0da51d640ac2e60ec430` |
| SHA-256 | `7c817528d9848c0390dba0fbd0ede3472833ab83a5cda76150ce8f3460dd899a` |

Embedded-header scan: the exact 156-byte Nintendo logo (file `0x04`–`0x9F`)
occurs once in the whole 4 MiB file, at `0x04`. Single-image cartridge, not a
multi-game pack.

Header integrity:

* complement check (`0xBD`) stored `0xDB`, computed `0xDB` — valid;
* header checksum (`0xBE`) stored `0x0000`, computed `0x0BF7` — **invalid**.

The image boots in mGBA regardless (the emulator ignores those fields). All
addresses below are for the exact SHA-256 above.

## 2. Executive summary

Backyard Baseball (GBA, 2003) has **no in-game code system**:

* **No password screen and no cheat menu.** The strings `PASSWORD`, `CHEAT`,
  `DEBUG`, `UNLOCK`, `CODE` and `GOODIE` occur **zero** times in all 4 MiB,
  both as plain ASCII and in the game's own text encoding. There is no
  `Cheat Manager`, no `ROM Version:`, no `Corrupt save file`, and no debug
  menu text; the 2006 sequel's developer menu does not exist here.
* **No coach-name code table.** Season Play → Season Sign In has a real
  10-character coach-name field, but none of the 2006 title's nine code words
  is present in this ROM, there is no unlock message string, and no string
  comparison table for the name was found. The 2006 system was not reused.
* **The published GBA cheat is false for this ROM.** A GameFAQs/GamesRadar
  hint says: *Options → press Select, R, L → you hear a noise → Cards →
  create a player with unlimited stats*. The Options screen handler at
  `0x08013950` reads the pressed-key word and tests only `A` (0x001),
  `B` (0x002), `Select` (0x004), `Start` (0x008), Up/Down (0x0C0) and
  Left/Right (0x030). **R (0x100) and L (0x200) are never read.** On the
  main-menu Options `Select` simply exits to the main menu; on the pause-menu
  Options it opens the `Quit? Are you sure?` dialog. Pressing the published
  sequence (sequential and same-frame chord, at the main-menu Options, on the
  main-menu OPTIONS item, and at the pause-menu Options) produced no state
  change in EWRAM/IWRAM beyond animation noise, and the Custom Player
  `UNASSIGNED BALLS` counter still starts at 8 and still caps at 8.

Consequently the accepted-value set for every in-game code channel examined is
**empty**, so no novel code can be minted. The negative is bounded by the
search space quantified in §6b.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba`; not on `PATH`), display
`:154` (1024×768×24) with `openbox`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
Window content is a 720×480 viewport at `+152+141`.

Default mGBA SDL keymap used throughout:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Key masks were verified in RAM, not assumed: holding each key and reading
`0x03001830` gave `A=0x001, B=0x002, Select=0x004, Start=0x008, R=0x100,
L=0x200`, with the active-high pressed copy at `0x03001832` / `0x0300164C`.

### 3.1 Menu paths used

* Boot → Humongous logo → MLB Players Choice → GameBrains → title
  (`PRESS START TO CONTINUE`) → Start → Main Menu.
* Main Menu (7 items): QUICK PLAY, HOME RUN DERBY, SINGLE GAME, SEASON PLAY,
  MULTIPLAYER, OPTIONS, CARDS.
* OPTIONS (8 items): SOUND, MUSIC, SWING SPOT, PITCH LOCATOR, ERRORS,
  DIFFICULTY (TEE-BALL/EASY/MEDIUM/HARD), CREDITS, HELP.
* CARDS → Player Cards (SORTING / NAME / CUSTOM) → CUSTOM → Custom Player
  (NICK NAME, CUSTOMIZE, BOY/GIRL, THROW, BIRTHDAY) → CUSTOMIZE → SKILLS EDIT
  (`UNASSIGNED BALLS`, BATTING, RUNNING, PITCHING, FIELDING).
* SEASON PLAY → Season Sign In (COACH name with 10 slots, NEW SEASON,
  LOAD SEASON) → Season Game Setup.
* In-game Start → PAUSE (season game: 7 items incl. TEAM INFO and SAVE GAME;
  quick game: 6 items incl. STATISTICS) → OPTIONS (same 8-item options
  screen; `Select` opens the quit dialog there).

### 3.2 Published code tested

| Source | Claim | Result here |
|---|---|---|
| GameFAQs `gba/560785-backyard-baseball/cheats` (403 to fetch; content recovered via search snippets) and GamesRadar user hint (GBA, "ryan fajdetich") | Options → press Select, R, L → noise → Cards → create player with unlimited stats | **Rejected**: no noise-driven state change, no flag, stat cap still 8 |

The GameFAQs page itself returns HTTP 403 to automated fetches; the snippet
text (`Create a Charater with Stats All the Way ... Go to options and press
select, r, l buttons you will hear a noise ...`) was recovered from search
results and from the GamesRadar mirror. The only other GBA results on those
pages are CodeBreaker/memory-edit codes, which are out of scope.

### 3.3 Effect test (ground truth)

1. Load a state on either Options screen.
2. Press the published sequence.
3. Back out to Main Menu → CARDS → CUSTOM (4 × Down + A) → CUSTOMIZE
   (Down + A).
4. Observe `UNASSIGNED BALLS` and press Right nine times.

Observed every time: `UNASSIGNED BALLS: 8` at entry, BATTING caps at 8/8 and
the counter reaches 0 (`shots/12_after_published_code_skills.png`). The same
result without the sequence. The advertised "unlimited stats" never appears.

### 3.4 State-diff test

Savestates were taken at the same screen before and after the chord
(`Shift+F1` / `Shift+F2` via mGBA hotkeys), then the `gbAs` chunk was
zlib-decompressed and compared. Layout was proven by writing sentinels with
the mGBA debugger (`w/4`) and locating them:

| Region | Savestate offset | Size |
|---|---:|---:|
| IWRAM (`0x03000000`) | `0x19000` | `0x8000` |
| EWRAM (`0x02000000`) | `0x21000` | `0x40000` |

Diff of the Options screen before/after the chord: **0** bytes changed in
EWRAM; IWRAM changes were timer/stack/animation words (e.g. `0x03003BD4`
pointer rewrites), with **no 0→1 boolean flag**. A second diff (Select-only
exit vs chord exit) likewise produced no persistent flag.

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`.

| Item | ROM address | File offset | Notes |
|---|---:|---:|---|
| Input module | `0x080041D8` | `0x41D8` | keypad poll, held/pressed pipeline |
| Keypad register read | `0x08004210` | `0x4210` | `ldrh` from `0x04000130` |
| Global key pipeline | `0x0800423E` | `0x423E` | writes held/pressed globals |
| Held-key word | `0x03001830` | RAM | active-high 10-bit mask |
| Pressed-key word | `0x03001832` | RAM | new-since-last-frame mask |
| Pressed-key copy | `0x0300164C` | RAM | alternative pressed word |
| Options screen handler | `0x08013950` | `0x13950` | menu screen; 8 items |
| Options key read | `0x080139F8` | `0x139F8` | `ldrh r4,[0x0300164C]` |
| A / Start / B / Select tests | `0x080139FE` / `0x08013A50` / `0x08013A94` / `0x08013ABA` | | masks 1 / 8 / 2 / 4 |
| Up+Down / Left+Right tests | `0x08013ADC` / `0x08013B3C` | | masks 0xC0 / 0x30 |
| Quit-confirm dialog | `0x0800470C` | `0x470C` | called by Select branch |
| Options menu index | `0x03002FF0` | RAM | 0..7; verified 0 on entry, 1 after one Down, unchanged on the main menu |
| Options value table | `0x03003000` | RAM | 8 entries, init at `0x0801391C` |
| Skills Edit input loop | `0x08032260` | `0x32260` | stat allocation screen; reads pressed keys |
| Skills point accounting | `0x08031B20` | `0x31B20` | constants `0x23`/`0x24` |
| Skills stat globals | `0x03004DA0`/`A4`/`B0`/`B4` | RAM | selected stat, limit, counts |
| Limit byte | `0x0300151C` | RAM | `byte[0x03001510+0x0C]` |
| Text bank (encoded) | `0x081A8000`–`0x081B4000` | `0x1A8000` | `char = byte + 0x21` |
| Difficulty strings | `0x081AFB6x` | `0x1AFB6x` | `TEE`/`BALL`/`EASY`/`MEDIUM`/`HARD` |
| `UNASSIGNED BALLS` | `0x081AE10E` | `0x1AE10E` | encoded text |
| Game text pointer table | `0x081AB000` | `0x1AB000` | u16 offsets into `0x1A8000` |

No password table, no cheat-flag word and no debug-menu launcher exists in
this image; there is nothing to list for those rows.

## 5. Algorithm

### 5.1 Key pipeline (derived, confirmed in RAM)

```c
raw   = ~REG_KEYINPUT & 0x3FF;      /* 0x04000130, active low */
held  = raw;                        /* 0x03001830 */
pressed = raw & ~prev_raw;          /* 0x03001832 and 0x0300164C */
prev_raw = raw;
```

Field order matches the GBA convention: A=1, B=2, Select=4, Start=8,
Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200. Verified by
holding each key and reading the held word.

### 5.2 Options screen dispatch (derived)

```
r4 = *(u16*)0x0300164C                 ; pressed
if (r4 & 0x001) handle_A();            ; 0x080139FE
if (r4 & 0x008) handle_Start();        ; 0x08013A50
if (r4 & 0x002) handle_B();            ; 0x08013A94
if (r4 & 0x004) handle_Select();       ; 0x08013ABA
if (r4 & 0x0C0) move_cursor_vertical();/* 0x08013ADC */
if (r4 & 0x030) change_value();        ; 0x08013B3C
```

There is **no test of 0x100 or 0x200** anywhere in the function, and the
global input module contains no literal 0x100/0x200 compare either (scanned
`0x08003F00`–`0x08004600`).

`handle_Select` on the main-menu Options exits; on the pause-menu Options it
calls the `Quit? Are you sure?` dialog at `0x0800470C` when the byte at
`0x03000F39` is in 1..6. In both cases R/L are ignored.

### 5.3 Text encoding (derived, confirmed by decoding)

UI/commentary records use:

```
u16 length;          /* chars + 1 */
u8  text[length];    /* last byte 0x00 terminator */
```

with `char_code = ASCII - 0x21` and `0x00` used for a space inside strings.
Examples: `DIAMONDBACKS`, `KIDS`, `UNASSIGNED`, `TEE-BALL` (stored as `TEE`,
`BALL`). This is the same alphabet family as the 2006 sequel, but the records
are length-prefixed rather than 0x5E-padded.

### 5.4 Skills point accounting (derived)

At `0x08031B20` the screen sums the four skill fields, adds the selected
character index and the constants `0x23` (35) and `0x24` (36), and clamps the
unassigned pool. At entry the pool is 8; nine Right presses on BATTING give
BATTING = 8 and `UNASSIGNED BALLS = 0`. No cheat flag participates in this
computation in the builds examined.

## 6. Tables

### 6.1 Key masks

| Button | Mask |
|---|---:|
| A | `0x001` |
| B | `0x002` |
| Select | `0x004` |
| Start | `0x008` |
| Right | `0x010` |
| Left | `0x020` |
| Up | `0x040` |
| Down | `0x080` |
| R | `0x100` |
| L | `0x200` |

### 6.2 Menu inventory (observed)

| Screen | Items |
|---|---|
| Main Menu | QUICK PLAY, HOME RUN DERBY, SINGLE GAME, SEASON PLAY, MULTIPLAYER, OPTIONS, CARDS (7) |
| Options | SOUND, MUSIC, SWING SPOT, PITCH LOCATOR, ERRORS, DIFFICULTY, CREDITS, HELP (8) |
| Player Cards | SORTING, NAME, CUSTOM (3 focus rows) |
| Custom Player | NICK NAME, CUSTOMIZE, BOY/GIRL, THROW, BIRTHDAY (MONTH, DAY) |
| Skills Edit | UNASSIGNED BALLS, BATTING, RUNNING, PITCHING, FIELDING |
| Season Sign In | COACH (10 name slots), NEW SEASON, LOAD SEASON |
| Season Game Setup | FIELD, DIFFICULTY, INNINGS, SWING SPOT, PITCH LOCATOR, ERRORS |
| Home Run Derby | GAME TYPE, OPPONENT, FIELD |
| Pause (season game) | RESUME GAME, OPTIONS, TEAM STRATEGY, CURRENT STATUS, TEAM INFO, SAVE GAME, QUIT GAME (7) |
| Pause (quick game) | RESUME GAME, OPTIONS, TEAM STRATEGY, CURRENT STATUS, STATISTICS, QUIT GAME (6) |
| Quit confirm | `Quit? Are you sure?` Yes / No |

No screen in this inventory contains a text-entry field for a code or
password; the only free-text entry is the coach name.

### 6.3 Keyword search counts (entire 4 MiB)

Plain ASCII (`strings -n 3/4`, 96,908 / 37,771 runs; case-insensitive grep):

| Word | Hits |
|---|---:|
| PASSWORD | 0 |
| CHEAT | 0 |
| DEBUG | 0 |
| UNLOCK | 0 |
| CODE | 0 |
| GOODIE | 0 |
| SECRET | 1 (commentary: "THE SECRET WEAPON", not a code) |

Game text encoding (`byte + 0x21`) over all 4,194,304 bytes:

| Word | Hits | Context |
|---|---:|---|
| PASSWORD | 0 | — |
| CHEAT | 0 | — |
| DEBUG | 0 | — |
| UNLOCK | 0 | — |
| CODE | 0 | — |
| GOODIE | 0 | — |
| SECRET | 1 | `0x1AD8F7`, commentary "EVERYBODY'S FAVORITE ... THE SECRET WEAPON" |
| ROSTER | 3 | menu labels |
| OPTION | 3 | menu labels |
| CREDIT | 1 | menu label |

### 6.4 2006 sequel codes in this ROM

`NACHOS`, `HOOPS`, `BIGFISH`, `LIBERTY`, `ANCHOVY`, `BABYBEAR`, `SPACEMAN`,
`SHOWTIME`, `ATLANTIS` were searched in ASCII and in the game's text
encoding: **0 hits each**. The 2006 pointer table shape (array of 9 ROM
pointers to short strings) has no analogue here; the only clusters of
pointers into the text bank are structure tables at `0x3BA50`/`0x3DEE4`, not
code strings.

## 6b. Enumeration

### 6b.1 Space definition

**Button-code space (Options screen).** The screen samples 10 bits of the
pressed word: A, B, Select, Start, Up, Down, Left, Right — but **not R or L**.
The reachable symbol set for this screen is therefore:

```
{A, B, Select, Start, Up, Down, Left, Right}
```

R and L are unrepresentable *at the Options screen*, so any sequence that
contains R or L (including the published `Select, R, L`) cannot be handled
there. The published sequence is not "wrong code, right system": the system
cannot see two of its three symbols.

Global input module: the keypad poll at `0x08004210` tests only Select
(0x004); no 0x100/0x200 comparison exists in the module (`0x08003F00`–
`0x08004600`).

**Coach-name space.** Season Sign In gives 10 single-character slots over
the on-screen alphabet A–Z plus blank (27 symbols observed). Representable
strings:

```
27^10 = 205,891,132,094,649  (≈ 2.06 × 10^14)
```

Accepted values: **none found**. No comparison table, no accepted-word list
and no unlock message string exists in the image. The 2006 nine-word table is
absent. The name is free text, used for display ("COACHED BY: ..."), not as a
key.

**Password space.** No password screen, no password strings, no validator, no
flag: accepted set empty by construction (there is no input surface).

### 6b.2 Published code: tested and rejected

| Entry point | Timing | Result |
|---|---|---|
| Main-menu Options | Select, R, L sequentially | Select exits to Main Menu; R/L ignored |
| Main-menu Options | Select+R+L same-frame chord (single `keydown` burst) | exits; no noise-driven flag |
| Main-menu Options | hold L+R, then tap Select | exits; no state change |
| Main-menu, cursor on OPTIONS | same-frame Select+R+L | nothing; no state change |
| Pause-menu Options | same-frame Select+R+L | opens `Quit?` dialog; R/L ignored |
| Pause-menu Options | Select, then R, L | dialog stays; R/L ignored |

Ground truth after each: Skills Edit still enters at `UNASSIGNED BALLS: 8`
and nine Right presses cap BATTING at 8 (`shots/12_after_published_code_skills.png`).

State evidence: EWRAM diff before/after = 0 bytes; IWRAM diff contains no
0→1 flag (only timer/stack/pointer churn).

### 6b.3 Bounds proven by rejection

1. **Out-of-alphabet symbol at the Options screen.** R (0x100) and L (0x200)
   are not members of the handler's tested mask set; pressing them on the
   Options screen is a no-op (observed) and no code path reads them (derived
   from `0x08013950`).
2. **Wrong sequence.** Select alone exits the main-menu Options (observed)
   and opens the quit dialog on the pause Options (observed); appending R, L
   after it changes nothing.
3. **Wrong entry point.** The same sequence on the main menu with OPTIONS
   merely highlighted (not entered) is inert.
4. **Wrong field.** The Skills Edit cap cannot be exceeded: nine Right
   presses give 8/8 and 0 unassigned, with or without the sequence.

These four bound the claim in both directions: the sequence cannot be
expressed where the handler could see it, and even if it were, the advertised
effect does not occur.

### 6b.4 Negative systems, bounded

* **Password system:** no strings (`PASSWORD` = 0 in ASCII and encoded), no
  entry screen in the walked menu tree, no validator.
* **Coach-name code table:** the 2006 nine words absent; no unlock text; no
  table of short all-caps strings with a pointer array; name entry is
  free text.
* **Developer/debug menu:** no `Cheat`/`Debug`/`ROM Version`/`Corrupt save`
  ASCII anywhere (the 2006 Cheat Manager strings are absent); no large block
  of ASCII UI strings at `0x4xxxx`; no unreferenced menu launcher found.
* **Button codes:** the only in-game cheat hint found is the published
  Select/R/L one, and it is disproven above. No other published GBA button
  code exists on GameFAQs/VGChartz/TCRF/SuperCheats/Vizzed/CheatingDome for
  this title.

## 7. Validation evidence

**Observed (emulator, screenshots in `/tmp/opencode/bb/shots/`)**

* Boot, title, main menu, Options, Cards, Custom Player, Skills Edit, Season
  Sign In, Season Game Setup, pause menus, quit dialog, HR Derby setup,
  commentary and gameplay were reached and captured.
* Key masks read from `0x03001830` while holding each key.
* `0x03002FF0` is the Options index: 0 on entry, 1 after one Down (help text
  changed to "TURN THE MUSIC ON OR OFF."), and it does not change while
  navigating the main menu — this pins `0x08013950` to the Options screen.
* `Select` on the main-menu Options returns to Main Menu; on the pause-menu
  Options it opens `Quit? Are you sure?` (`11_quit_dialog.png`).
* Skills Edit entry value 8, cap at 8 after nine Right presses, both with and
  without the sequence (`06_skills_edit.png`, `12_after_published_code_skills.png`).
* Savestate diffs: EWRAM 0 changed bytes; IWRAM no boolean flag.

**Derived (disassembly)**

* `0x08013950` is the Options screen handler; it reads `0x0300164C` and
  tests only 0x001, 0x002, 0x004, 0x008, 0x0C0, 0x030.
* `0x0800470C` is the quit-confirm dialog reached from the Select branch.
* `0x08031B20` is the skills point clamp; constants 0x23/0x24; globals at
  `0x03004Dxx`.
* `0x0800423E` builds held/pressed from `0x04000130`.
* Text encoding `byte + 0x21`, length-prefixed records.

**Inferred**

* That the coach name is display-only (no comparator was found, but the
  screen's commit path was not fully reversed).
* That no hidden R/L sequence exists on screens not walked; the search
  covered the input module and the Options handler, not every screen handler.

## 8. Unknowns

* The Help/manual viewer opens a multi-page manual whose source is not stored
  as plain text in ROM or in RAM at the moment checked; its pages were not
  keyword-searched. It is documentation, not a code-entry surface.
* Credits, Multiplayer submenu, Single Game setup, Load Season, Team Strategy,
  Current Status, Statistics, Team Info and Save Game were not opened in this
  session; none of them contains a free-text field in the text bank.
* The exact writer of the `0x03000F39` byte that gates the pause-menu quit
  dialog was not traced (behaviour, not identity, was established).
* Regional/revision differences: all findings are for SHA-256
  `7c817528...dd899a`.

## 9. Tooling

* mGBA 0.10.5 SDL (`/usr/games/mgba`), `-3`, `SDL_AUDIODRIVER=dummy`.
* Xvfb `:154` (1024×768×24) + `openbox`; `xdotool` for input; `scrot` for
  screenshots; `tesseract` for screen OCR.
* mGBA built-in debugger (`mgba -d`), driven over a pty: `x/4` memory reads,
  `w/r`/`w/w` watchpoints, `save`/`load` slots. Used to locate the Options
  handler (read watchpoint on `0x0300164C`) and to map savestate regions with
  sentinel writes.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M
  force-thumb` for raw Thumb disassembly; Capstone 5.0.7 for pattern scans.
* Python 3 for hashes, text decoding, pointer/keyword scans and savestate
  (`gbAs` → zlib) diffs.

Minimal savestate diff reproducer (offsets proven in §3.4):

```python
import struct, zlib
def load(p):
    d = open(p, "rb").read(); i = 8
    while i < len(d):
        n = struct.unpack(">I", d[i:i+4])[0]
        t = d[i+4:i+8]
        if t == b"gbAs":
            raw = zlib.decompress(d[i+8:i+8+n])
        i += 12 + n
    return raw
a, b = load("a.ss1"), load("b.ss2")
for name, base, size in (("IWRAM", 0x19000, 0x8000), ("EWRAM", 0x21000, 0x40000)):
    x, y = a[base:base+size], b[base:base+size]
    print(name, sum(1 for i in range(size) if x[i] != y[i]))
```

Legal note: no ROM, extracted graphics, music or other copyrighted assets are
redistributed here. Only hashes, addresses, algorithms, menu labels and my
own screenshots/notes are published.
