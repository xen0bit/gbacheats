# Backyard Sports: Baseball 2007 (GBA) — Reverse Engineering Report

Status: complete for the code/unlock surface. Scope: in-game / developer-intended
cheats only (passwords, button codes, hidden/debug menus, unlockables). No
GameShark, CodeBreaker, Action Replay or other memory-edit codes are proposed or
relied on. One debugger-only experiment is explicitly labelled as such.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Backyard Sports: Baseball 2007/Backyard Sports: Baseball 2007.gba` |
| Size | 4,194,304 bytes (`0x400000`, 32 Mbit) |
| Header title (`0xA0`) | `BASEBALL2007` |
| Game code (`0xAC`) | `BC7E` |
| Maker code (`0xB0`) | `70` |
| Software version (`0xBC`) | `0x00` (Rev.00) |
| Entry branch (`0x00`) | `0xEA00002E` → ARM branch to `0x080000C0` |
| Fixed header byte `0xB2` | `0x96` ✔ |
| MD5 | `bd5fd53f6315d6668fdbf4e7bf4e81eb` |
| SHA-1 | `cde84171b11a767338158c61ee2ad608d4eb8889` |
| SHA-256 | `314d34b30602aab2d92a31c1c2d0a88e8ff29d0c76fb14b050b5cd261f19416e` |

Embedded-header scan: the exact 156-byte Nintendo logo from header offset `0x04`
was searched over all 4,194,304 bytes. Exactly **one** occurrence exists (the
game header itself); there is no second GBA image, multiboot child or boot
selector in the file.

Header integrity caveat: the stored complement check (`0xBD`) is `0xEA` while the
computed value is `0xED`, and the stored header checksum (`0xBE`) is `0x0000`
while the usual byte-sum gives `0x00EA`. The entry branch, Nintendo logo, fixed
`0x96`, game code and crt0 at `0x080000C0` are stock; no cracktro, trainer,
modified entry point or extra code at the entry was found. The invalid header
fields look like a dump/normalisation artefact, not a gameplay patch. All
addresses below are for the SHA-256 above.

## 2. Executive summary

The retail game has **one reachable code system: an eight-entry coach-name
table**. On `Season Play → New Coach → Enter Name`, eight fixed names are
compared against the 8-byte, `0x5E`-padded committed name field. A match sets one
bit and shows `YOU HAVE UNLOCKED …`. The eight accepted names and their effects
were all entered on a real emulated keyboard and all eight messages were
observed:

| Code | Effect |
|---|---|
| `NACHOS` | Bobby Abreu |
| `HOOPS` | Derek Jeter |
| `LIBERTY` | Derek Lee |
| `BIGFISH` | Dontrelle Willis |
| `ANCHOVY` | Johan Santana |
| `BABYBEAR` | Paul Konerko |
| `SPACEMAN` | Area 51 |
| `SHOWTIME` | Humongous Memorial Stadium |

This is the same code family as Backyard Baseball 2006, but the table is **8
entries, not 9**: the 2006 `ATLANTIS` (Aquadome) entry and its string were
removed entirely. `LIBERTY` was moved from index 3 to index 2 (it now unlocks
Derek Lee), and `BIGFISH` from 2 to 3 (Dontrelle Willis). The list order matches
the developer Cheat Manager's page-2 unlock list in the same ROM.

The ROM also contains the complete ASCII developer **`Cheat Manager v1.0`**
(four pages: diagnostics, eight unlocks, nine gameplay modifiers, twelve season
jumps). Its launcher at `0x08036744` has **zero** BL/BLX/pointer references, and
its gate compares the held-input word with `0x3080` — a value no controller can
produce (bits 12–13 are outside the GBA button mask) and for which no writer
exists. Its state pointer `0x03003E88` was zero in six savestates (Options,
matchup, gameplay ×2, name entry ×2). Breakpoints on the launcher and menu main
never fired during the menu walk. It is dead developer content in this retail
build, exactly as in 2006; its page-2 unlocks are reachable through the eight
coach-name codes.

The published 2007 GBA button code (`Up, Up, Left, Right, B, Down`, "Unlimited
Turbo") is **not implemented in this build**. The sequence string occurs nowhere
in the ROM in any tested encoding, the sequence produced no visible change at
the matchup screen, and the 17-entry ASCII table/matcher used by the sibling
Backyard Basketball engine (including `Backyard Sports: Basketball 2007`, table
at `0x083ABC5C`) is absent from this image in every encoding tested. The
published Paul Konerko name code `GRAND SLAM` is likewise not in the ROM: the
9-letter word cannot even be entered (the name field caps at 8 characters), the
8-character truncation `GRANDSLM` is rejected, and the real Paul Konerko code is
`BABYBEAR` (observed).

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba`), scale `-3`, headless Xvfb
`:160` (1024×768×24) + `openbox`, `SDL_AUDIODRIVER=dummy`. Keymap used:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L / R | `a` / `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Hold keys for 150–300 ms; this menu drops short taps and eats the first key
after a savestate load.

### 3.1 Path to the code screen

```
boot → Atari/Humongous logos → title (PRESS START) → Start
  → MAIN MENU → Season Play (Down, A)
  → TEAM DUGOUT → NEW COACH (A)
  → ENTER NAME
```

The grid is four rows plus a button row:

```
1 2 3 4 5 6 7 8 9 0 <
A B C D E F G H I J
K L M N O P Q R S T
U V W X Y Z . , - ! #
[ DELETE ]   [ SPACE ]   [ DONE ]
```

Use the D-pad, **A** to select a character and **A** on `DONE` to submit. On a
match the `YOU HAVE UNLOCKED …` panel appears immediately; on a miss the game
goes straight to `SET RULES`. The name field caps at **8** characters: typing a
ninth changes nothing (observed with `GRANDSLAM`, which displays `GRANDSLA`).

For repeated tests a savestate at the Options screen was used as the clean base
(`Backyard Sports: Baseball 2007.ss1`); the per-code loop is
`F1 → B → Down → A → A → type → DONE → A`.

### 3.2 Published codes tested

| Published code (source) | Claimed effect | Result in this ROM |
|---|---|---|
| `Up, Up, Left, Right, B, Down` (IGN / archived GameFAQs GBA page, entered at the matchup screen) | Unlimited Turbo | No screen change; no such sequence table in ROM (see §6b.4) |
| Type `Grand Slam` (GameFAQs, "Unlock Paul Konerko") | Paul Konerko | Not implemented: `GRANDSLAM`/`GRAND SLAM` are absent from the ROM and exceed the 8-character cap; `GRANDSLM` rejected. The real Paul Konerko code is `BABYBEAR` (observed) |
| Season achievements (30 hits / 45 strikeouts / shut-out / World Series) | Derek Lee / Dontrelle Willis / Johan Santana / Area 51 | Normal unlock conditions, not codes; they set the same unlock flags through gameplay |

### 3.3 Accepted inputs and rejections actually entered

All of the following were entered through the real on-screen keyboard. Evidence
screenshots are in `/tmp/opencode/bb2007/shots/` (paths below).

| Input | Length | Result | Screenshot |
|---|---:|---|---|
| `NACHOS` | 6 | `YOU HAVE UNLOCKED BOBBY ABREU` | `56_nachos_game.png` |
| `HOOPS` | 5 | `YOU HAVE UNLOCKED DEREK JETER` | `47_game.png` |
| `LIBERTY` | 7 | `YOU HAVE UNLOCKED DEREK LEE` | `55_game.png`, `101_liberty_flag_game.png` |
| `BIGFISH` | 7 | `YOU HAVE UNLOCKED DONTRELLE WILLIS` | `60_bigfish_game.png` |
| `ANCHOVY` | 7 | `YOU HAVE UNLOCKED JOHAN SANTANA` | `61_anchovy_game.png` |
| `BABYBEAR` | 8 | `YOU HAVE UNLOCKED PAUL KONERKO` | `62_babybear_game.png` |
| `SPACEMAN` | 8 | `YOU HAVE UNLOCKED AREA 51` | `63_spaceman_game.png` |
| `SHOWTIME` | 8 | `YOU HAVE UNLOCKED HUMONGOUS MEMORIAL STADIUM` | `64_showtime_game.png` |
| `ATLANTIS` | 8 | no unlock; went to SET RULES | `65_atlantis_game.png` |
| `OCTOBER` | 7 | no unlock; SET RULES | `66_october_game.png` |
| `GRANDSLM` | 8 | no unlock; SET RULES | `68_grandslam8_game.png` |
| `GRANDSLA` | 8 | no unlock; SET RULES (8-char prefix of the published word) | `70_grandsla_game.png` |
| `GRANDSLAM` | 9 attempted | only `GRANDSLA` accepted (cap 8) | `67_grandslam_cap_game.png` |
| `ZZZZZZZZ` | 8 | no unlock; SET RULES | `69_zzzz_game.png` |

## 4. Address map

File offset → ROM address is `0x08000000 + offset`. Code is Thumb unless noted.

| Item | ROM address | File offset | Notes |
|---|---:|---:|---|
| Coach-code pointer table (8 × u32) | `0x0839EBC8` | `0x39EBC8` | Entries point to the eight encoded names |
| Code string pool | `0x0815C01C`–`0x0815C058` | `0x15C01C`–`0x15C058` | Encoded `ASCII − 0x21`, `0x5E` terminator/pad |
| Decoy string `OCTOBER` | `0x0815C014` | `0x15C014` | Immediately before the pool; not referenced by the table; rejected in-game |
| String equality `streq8` | `0x08024C70` | `0x24C70` | 8-byte compare, `0x5E`-aware; returns 1 on equal/terminator |
| Current-name getter | `0x08024870` | `0x24870` | Returns `0x03002F70` |
| Validator loop | `0x0803658E`–`0x080365C2` | `0x3658E`–`0x365C2` | `for i = 0..7`, `cmp r6,#7` at `0x080365C0` |
| Bit set on match | `0x080365B2` | `0x365B2` | `lsls r0,r6; orrs r7,r0` |
| Flag merge/store | `0x080365EA`–`0x0803660C` | `0x365EA`–`0x3660C` | Name bits shifted to bits 8..15 of `0x03003E84` |
| Cheat-state applier | `0x0801BD34` | `0x1BD34` | Consumes the merged state |
| Name input buffer | `0x03003E00` | RAM | 8 bytes, `ASCII − 0x21`, zero-padded while typing |
| Name length (u8) | `0x03003DEC` | RAM | 0..8 |
| Name max length | `0x03003E14` | RAM | reads `0x08`; compared at `0x0803038A` |
| Committed name field | `0x03002F70` | RAM | 8 bytes, `0x5E`-padded; comparator operand |
| Cheat flag word | `0x03003E84` | RAM | u32; code bits occupy bits 8..15 |
| Name-entry UI / commit | `0x0802FC00`–`0x080303D0` | `0x2FC00`–`0x303D0` | Grid navigation, DELETE/SPACE/DONE, draw |
| Cheat Manager launcher | `0x08036744` | `0x36744` | Gate: `0x03003E88 == 0` and `held0 == 0x3080` |
| Cheat Manager main | `0x08037CB0` | `0x37CB0` | Four-page ASCII UI |
| Cheat Manager init | `0x08037D54` | `0x37D54` | Allocates/clears 20 × 30 menu buffer |
| Cheat Manager dispatch table (9 × u32) | `0x0839EC88` | `0x39EC88` | 4 page-inits, 4 draw/input, 1 helper |
| Page 1 init | `0x08036D4C` | `0x36D4C` | `Cheat Manager v1.0`, version/RAM diagnostics |
| Page 2 init | `0x08036E6C` | `0x36E6C` | Eight `Un-lock …` items |
| Page 3 init | `0x080371CC` | `0x371CC` | Nine gameplay modifiers |
| Page 4 init | `0x08037878` | `0x37878` | Twelve season jumps |
| Cheat Manager state pointer | `0x03003E88` | RAM | Zero at every screen checked |
| Held input word [player 0] | `0x03000B6C` | RAM | Read by the launcher; zero at every screen checked |
| Cheat Manager ASCII strings | `0x08041EA4`–`0x0804234C` | `0x41EA4`–`0x4234C` | Plain ASCII (unlike the retail vector font) |

## 5. Algorithm

### 5.1 Character encoding

The name-entry buffer is one byte per character. For letters, digits and the
punctuation cells the stored value is `ASCII − 0x21` (e.g. `A` → `0x20`, `G` →
`0x26`, `Z` → `0x39`). The SPACE button stores `0x00` (observed: `A` + SPACE
gives `20 00`, length 2). The left-arrow cell is not used by any accepted code;
the 2006 engine stored it as `0x08` and this engine uses the same grid.

At `DONE` the typed bytes are copied into the committed field `0x03002F70` and
padded with `0x5E` (`^`), which is also the table's terminator/pad byte. The
maximum is 8 characters (`0x03003E14 = 8`).

### 5.2 Comparator

`0x08024C70(a, len_a, b, len_b)` is the `0x5E`-terminated equality routine used
by both this and the 2006 build:

```c
int streq8(const uint8_t *a, uint8_t len_a,
           const uint8_t *b, uint8_t len_b) {
    uint8_t n = (len_a < len_b) ? len_a : len_b;
    for (uint8_t i = 0; i < n; i++) {
        uint8_t ca = a[i], cb = b[i];
        if (ca != cb) return 0;
        if (ca == 0x5E) return 1;   /* terminator/pad on both sides */
    }
    return 1;
}
```

### 5.3 Validator and flag merge

At `0x0803658E`:

```c
uint16_t matched = 0;
for (int i = 0; i <= 7; i++) {
    const uint8_t *code = *(const uint8_t **)(0x0839EBC8 + 4*i);
    if (streq8(code, 8, (const uint8_t *)0x03002F70, 8))
        matched |= (uint16_t)(1u << i);
}
/* merge with the non-name state bits, then move name bits to 8..15 */
uint16_t state = *(uint16_t *)0x03003E84;
state = (state & ~matched) | (matched << 8);
*(uint16_t *)0x03003E84 = state;
apply_cheat_state();            /* 0x0801BD34 */
```

The loop bound is `cmp r6,#7` at `0x080365C0`; there is no ninth comparison.

### 5.4 Why the accepted set is finite

There is no arithmetic, checksum, XOR key, alphabet table or encoder anywhere in
the path: the only comparison is `streq8` against the eight pointers. The
accepted set is therefore exactly eight strings, regardless of the theoretical
name space.

## 6. Tables

### 6.1 The eight coach-name codes

| # | Code | ROM address | Encoded bytes | Bit | Effect | Published externally? |
|---:|---|---|---|---:|---|---|
| 0 | `NACHOS` | `0x0815C01C` | `2D 20 22 27 2E 32 5E` | 0 | Bobby Abreu | No |
| 1 | `HOOPS` | `0x0815C023` | `27 2E 2E 2F 32 5E` | 1 | Derek Jeter | No |
| 2 | `LIBERTY` | `0x0815C029` | `2B 28 21 24 31 33 38 5E` | 2 | Derek Lee | No |
| 3 | `BIGFISH` | `0x0815C031` | `21 28 26 25 28 32 27 5E` | 3 | Dontrelle Willis | Yes, for BB2006 only |
| 4 | `ANCHOVY` | `0x0815C039` | `20 2D 22 27 2E 35 38 5E` | 4 | Johan Santana | No |
| 5 | `BABYBEAR` | `0x0815C041` | `21 20 21 38 21 24 20 31` | 5 | Paul Konerko | Yes, for BB2006 only |
| 6 | `SPACEMAN` | `0x0815C049` | `32 2F 20 22 24 2C 20 2D` | 6 | Area 51 | No |
| 7 | `SHOWTIME` | `0x0815C051` | `32 27 2E 36 33 28 2C 24` | 7 | Humongous Memorial Stadium | No |

The pointer array at `0x0839EBC8` is exactly:

```
0x0815C01C 0x0815C023 0x0815C029 0x0815C031
0x0815C039 0x0815C041 0x0815C049 0x0815C051
```

The next u32 at `0x0839EBE8` is `0x0000035E`, not a pointer; there is no ninth
entry. `ATLANTIS` (the 2006 Aquadome code) does not exist in this ROM in either
plain or encoded form, and was rejected in-game as a valid 8-character name.

### 6.2 Cheat Manager item list (derived from ASCII strings at `0x08041EA4`)

**Page 1 — diagnostics**
* `Cheat Manager v1.0`
* `^or_=Select cheat item, <or>=Change item content`
* `{=Accept changes, }=Discard changes, [or]=Flip page`
* `Page 1 of 4`
* `ROM Version: Bb3AGB-023`
* `Remain Ext. Work RAM: ?????`
* `Corrupt save file`

**Page 2 — eight unlock flags (same eight effects as the name codes)**
* `Un-lock BOBBY ABREU`
* `Un-lock DEREK JETER`
* `Un-lock DEREK LEE`
* `Un-lock DONTRELLE WILLIS`
* `Un-lock JOHAN SANTANA`
* `Un-lock PAUL KONERKO`
* `Un-lock AREA51`
* `Un-lock HUMONGOUS MEMORIAL STADIUM`

**Page 3 — gameplay modifiers**
* `Runner Base Speed`
* `Runner Speed Modifier`
* `Fielder Base Speed`
* `Fielder Speed Modifier`
* `Ball Fly Time Multiplier`
* `Ball Throw Time Multiplier`
* `Gravity`
* `Get all pitching power-ups`
* `Get all batting power-ups`

**Page 4 — season jumps (enabled only in a season game)**
* `Season game cheat...`
* `This page will only be enabled when playing season game.`
* `Don't change season week`
* `Advance to middle season game`
* `Advance to last season game (winning)`
* `Advance to last season game (losing)`
* `Advance to division playoffs (begin)`
* `Advance to division playoffs (end)`
* `Advance to league championship (begin)`
* `Advance to league championship (end)`
* `Advance to world series (begin)`
* `Advance to world series (end)`

## 6b. Enumeration

### 6b.1 Space definition

* Input surface: the Season Play coach-name field (`ENTER NAME`).
* Alphabet: **43 symbols** — 42 grid cells (`A`–`Z`, `0`–`9`, `<`, `.`, `,`,
  `-`, `!`, `#`) plus the SPACE button. Row lengths are 11 / 10 / 10 / 11.
* Length: **1–8** characters. The max is a variable at `0x03003E14` and reads
  `0x08`; typing a ninth character leaves the length at 8 (observed with
  `GRANDSLAM`: the buffer held `26 31 20 2D 23 32 2B 20` = `GRANDSLA`, length
  byte `0x03003DEC = 8` in savestate `.ss6`).
* Storage: one byte per character; `ASCII − 0x21` for printable cells, `0x00`
  for SPACE; committed field padded with `0x5E`.
* Representable strings: `Σ(43^k, k=1..8) = 11,966,490,760,400` (≈1.20 × 10^13).
* Accepted values: **exactly 8**, the pointer table above. There is no checksum,
  key, reserved field or generator that could make another string valid.

### 6b.2 Novel codes (absent from every published 2007 list; two inherited from 2006)

All eight values were entered through the real on-screen keyboard. At least six
(the first six below) appear in no external list searched. The web check used
the archived GameFAQs GBA page (2018-11-26 snapshot: exactly two codes —
`Up, Up, Left, Right, B, Down` "Unlimited Turbo" and "Type Grand Slam" for Paul
Konerko — plus a season-achievement unlock table), IGN's GBA cheats page,
LoneBullet, ChapterCheats and the Backyard Sports Wiki; no 2007 GBA-specific
VGChartz or TCRF page was found. The two 2006-published words are marked
accordingly.

| Novel code | Bit | Observed effect | Screenshot |
|---|---:|---|---|
| `NACHOS` | 0 | `YOU HAVE UNLOCKED BOBBY ABREU` | `56_nachos_game.png` |
| `HOOPS` | 1 | `YOU HAVE UNLOCKED DEREK JETER` | `47_game.png` |
| `LIBERTY` | 2 | `YOU HAVE UNLOCKED DEREK LEE` | `55_game.png` |
| `ANCHOVY` | 4 | `YOU HAVE UNLOCKED JOHAN SANTANA` | `61_anchovy_game.png` |
| `SPACEMAN` | 6 | `YOU HAVE UNLOCKED AREA 51` | `63_spaceman_game.png` |
| `SHOWTIME` | 7 | `YOU HAVE UNLOCKED HUMONGOUS MEMORIAL STADIUM` | `64_showtime_game.png` |
| `BIGFISH` (published for 2006) | 3 | `YOU HAVE UNLOCKED DONTRELLE WILLIS` | `60_bigfish_game.png` |
| `BABYBEAR` (published for 2006) | 5 | `YOU HAVE UNLOCKED PAUL KONERKO` | `62_babybear_game.png` |

Flag proof: after entering `LIBERTY`, `0x03003E84` read `0x00000400`
(name bits 8..15 = `0x04`, i.e. index 2), while `0x03003E88` (Cheat Manager
state) stayed `0`. Savestate `.ss7`, screenshot `101_liberty_flag_game.png`.

### 6b.3 Bounds proven by rejection

| Test value | Why it is outside the accepted set | In-game result |
|---|---|---|
| `ATLANTIS` | Valid 8-char name; the 2006 Aquadome entry was removed from this ROM (no plain or encoded string, no pointer) | No unlock; SET RULES (`65_atlantis_game.png`) |
| `OCTOBER` | 7-char encoded string at `0x0815C014`, immediately before the pool, not referenced by the pointer table | No unlock; SET RULES (`66_october_game.png`) |
| `ZZZZZZZZ` | Valid 8-char name, not in the table | No unlock; SET RULES (`69_zzzz_game.png`) |
| `GRANDSLM` | 8-char truncation of the published `GRAND SLAM` code; not in the table | No unlock; SET RULES (`68_grandslam8_game.png`) |
| `GRANDSLA` | 8-char prefix of the published `GRANDSLAM`; not in the table | No unlock; SET RULES (`70_grandsla_game.png`) |
| `GRANDSLAM` | 9 characters; the input cap is 8 | 9th character not accepted; display/buffer stays `GRANDSLA`, length 8 (`67_grandslam_cap_game.png`, `.ss6`) |

The public 9-letter code is therefore unenterable, and neither the 8-character
prefix `GRANDSLA` nor the alternative truncation `GRANDSLM` is accepted. The
accepted set is exactly the eight table entries.

### 6b.4 The 17-entry button-code mechanism (bounded negative)

The sibling Backyard engine carries a 17-entry ASCII button-code table that is
matched against a rolling input buffer with a substring search:

| Build | Table | Form |
|---|---|---|
| Backyard Basketball (2006) | `0x08133E90` | 17 × 10-byte ASCII over `{a,b,s,t,r,l,u,d,v,m}`, NUL-padded |
| Backyard Sports: Basketball 2007 | `0x083ABC5C` | 17 × 10-byte ASCII, same alphabet; rows 9/14/15/17 differ from 2006 |

For **Backyard Sports: Baseball 2007** the mechanism is absent:

* Every one of the 17 Basketball sequences (`uudda`, `dudua`, `ssbbt`, `uulrba`,
  `sbbbba`, `msvvva`, …) occurs **0** times in the 4 MiB image, as does the
  published Baseball variant `uulrbd` and the common prefix `uulr`.
* The exact 32-byte signature of Basketball's substring matcher
  (`0x08066940`: `10 b5 03 1c 0c 1c 78 18 …`) occurs **0** times.
* A calibrated 17-row × stride-10/11/12 table detector finds Basketball 2007's
  table at `0x083ABC5C` but finds **0** candidates in Baseball 2007 for the
  lowercase button alphabet, its uppercase form, or the button-glyph range
  `0x8F–0x98`.
* No contiguous array of 17 packed `u32` key masks, and no 17-entry pointer table
  to short button-letter strings, was found.
* Dynamic: the one published sequence (`Up, Up, Left, Right, B, Down`) was
  entered at the matchup screen (`COUNTRY AIRPORT`, Phillies at Red Sox); it
  produced no visible change and no menu transition, and the static scans show
  no table or matcher that could consume it.

This is a bounded negative for the encodings the engine family actually uses.
The 2007 engine can still carry the table (Basketball 2007 does), but it was not
compiled into this Baseball build.

### 6b.5 Cheat Manager reachability (negative, bounded)

* Static: a full scan for Thumb `BL`/`BLX`, ARM `BL`/`BLX` and 32-bit pointers
  targeting the launcher `0x08036744`/`0x08036745` returns **zero** hits. The
  launcher's only caller of the menu main `0x08037CB0` is at `0x08036762`,
  inside the unreferenced launcher itself.
* Gate: the launcher reads the held-input word `0x03000B6C` and requires
  `0x3080`. `0x3080` contains bits 12–13, which are not GBA buttons. There is no
  literal-pool value `0x00003080`, and no instruction constructs it as a write
  value (`movs #0xC2; lsls #6` pattern: 0 hits); the only construction in the
  ROM is the launcher's own `movs r1,#0xC2; lsls r1,r1,#18` compare. The word
  read `0x0000` at Options, matchup, gameplay and name entry (savestates
  `.ss1`–`.ss6`).
* State: the Cheat Manager allocation pointer `0x03003E88` read `0x00000000` in
  all six states checked; the menu never initialises.
* Dynamic: breakpoints on `0x08036744` and `0x08037CB0` were installed while
  the menus were walked. The title, main menu, Pick-up Game → Set Rules →
  matchup → gameplay → pause → quit confirmation, Season Play → Team Dugout →
  New Coach → Enter Name, Mini Games, Link Play → player-name → Link menu,
  Options, and Extras → Player Cards / BBL Champions / Unlockable Goodies /
  Credits were all reached and photographed (the title and some submenus were
  walked before the breakpoint session; the breakpoint log covers the
  main-menu traversal). The log contains **0** `HIT_LAUNCHER` and **0**
  `HIT_CM_MAIN` entries.

The menu is real code and real UI text, but unreachable in this retail build.
Its page-2 list names the same eight unlocks, in the same order, as the eight
coach-name effects, so the developer shortcuts survive in reachable form even
though the menu does not.

### 6b.6 Search boundaries for the negative results

All scans covered the whole 4 MiB file; the 2006/Basketball addresses were used
only to calibrate detectors, not as assumptions about this ROM.

| Search | Space | Hits in this ROM |
|---|---|---|
| `password`, `passcode`, `debug`, `secret`, `coach`, `code`, `turbo` (ASCII, case-insensitive) | whole file | 0 each |
| `cheat` (ASCII, case-insensitive) | whole file | 3, all in the Cheat Manager block (`0x41EA4`, `0x41EB8`, `0x42190`) |
| Eight coach codes, encoded (`ASCII−0x21`) | whole file | 8 (the table strings) |
| `ATLANTIS` plain or encoded | whole file | 0 |
| 17 Basketball sequences + `uulr` + `uulrbd` | whole file | 0 each |
| Basketball substring-matcher 32-byte signature | whole file | 0 |
| 17-row × stride-10/11/12 table over button letters / glyphs | whole file | 0 (detector finds Basketball 2007's table, so it is calibrated) |
| Contiguous ≥4-entry u16 single-bit key-mask runs (active-high and low) | whole file | none plausible; hits are scattered data in graphics/level blocks |
| ASCII button-letter runs ≥4 | whole file | 20, all ordinary words (`batt`, `last`, `ddddd`, …), none a table |
| Cheat Manager launcher BL/BLX/pointer references | whole file (Thumb and ARM) | 0 |

## 7. Validation evidence

**Observed (emulator screenshots / savestates)**

* All eight accepted names produced their listed `YOU HAVE UNLOCKED …` panel
  (screenshots in §6b.2); `ATLANTIS`, `OCTOBER`, `ZZZZZZZZ`, `GRANDSLM` and
  `GRANDSLA` did not.
* Menus walked and photographed: title, main menu, Pick-up Game → Set Rules →
  matchup → gameplay → pause → quit confirmation, Season Play → Team Dugout →
  New Coach → Enter Name → Set Rules, Mini Games → Home Run Derby Set Rules and
  Fielders' Challenge coach select, Link Play → player name → Link menu →
  View Rankings / Trade a Custom Rookie (`PLEASE WAIT` link screen) and Edit
  Your Name, Options, Extras → Player Cards / BBL Champions / Unlockable
  Goodies / Credits. With no coach save, Team Dugout keeps the cursor on New
  Coach; Load Coach and Delete Coach do not take it.
* Link Play's networked items stop at `PLEASE WAIT` until a second GBA is
  present; that is a hardware boundary, not a hidden menu.
* `GRANDSLAM` displayed `GRANDSLA`; the length byte `0x03003DEC` read 8 and the
  buffer read `26 31 20 2D 23 32 2B 20` (`.ss6`).
* `LIBERTY` set `0x03003E84 = 0x00000400` (index 2 at bits 8..15); the Cheat
  Manager pointer `0x03003E88` stayed 0 (`.ss7`).
* The name buffer `0x03003E00` held `20 21 22 23` for `ABCD`; SPACE stored
  `0x00` (`.ss5`, `.ss8`).
* `0x03000B6C` (held input) read 0 and `0x03003E88` read 0 at Options, matchup,
  gameplay, name entry; breakpoints never fired during the menu walk.
* The published matchup sequence produced no visible change.

**Derived (instruction/table analysis)**

* The 8-entry pointer array at `0x0839EBC8`, its eight encoded strings, and the
  absence of a ninth pointer.
* `0x08024C70` is the 8-byte, `0x5E`-aware equality routine; `0x08024870`
  returns the committed field `0x03002F70`.
* The loop at `0x0803658E` tests i = 0..7 and sets bit i; the merge at
  `0x080365EA` shifts those bits to 8..15 of `0x03003E84`.
* The Cheat Manager launcher has zero incoming references; its gate is
  `held0 == 0x3080`; the page table is at `0x0839EC88`.
* Basketball 2007's 17-entry table is at `0x083ABC5C`; Baseball 2007 has no
  equivalent table/matcher in the encodings tested.

**Inferred**

* The left-arrow cell stores `0x08` (same engine as 2006; not needed by any
  accepted code).
* The exact mapping from the eight flag bits to profile/season fields (the
  applier at `0x0801BD34` is large; the effects were observed instead).
* The intended behaviour of Cheat Manager pages 3–4 (strings and code structure
  only; the menu is unreachable).
* The origin of the invalid GBA header checksum (dump artefact vs. patch; the
  entry/logo/crt0 are stock, so a gameplay patch is unlikely).

## 8. Unknowns

* Whether the Cheat Manager is reachable in a prototype/dev build or through a
  value written by hardware this image does not contain. In this image it is
  dead code. A debugger-only attempt to enter the launcher directly (PC set to
  `0x08036744` with a synthetic stack) raised `SIGILL` at `0x08047204`, so the
  menu's runtime behaviour was not observed; its item list is derived from the
  ASCII strings and page-init code.
* The precise writer/semantics of `0x03000B6C` beyond the normal input engine;
  no path sets it to `0x3080`.
* Whether the eight flags persist in SRAM across power cycles; the session
  messages and flag word were observed, but save persistence was not isolated
  from the emulator's `.sav` state.
* Regional/revision differences. All findings are for SHA-256
  `314d34b3…f19416e`; another dump may differ.

## 9. Tooling

* mGBA 0.10.5 SDL (`/usr/games/mgba`), `-3`, `SDL_AUDIODRIVER=dummy`.
* Xvfb `:160` (1024×768×24) + `openbox`; `xdotool` for input; ImageMagick
  `import`/`convert` for screenshots.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python 3 for hashes, pointer/BL scans, table decoding, savestate RAM extraction
  and the 17-row table detector (`/tmp/opencode/bb2007/`).
* `gdb-multiarch` against mGBA's `-g` stub (port 2345) for breakpoint and
  memory checks; the gbAs chunk of mGBA `.ssN` files was zlib-decompressed to
  read IWRAM (`0x19000`) and EWRAM (`0x21000`) without a debugger.

Minimal table reproducer:

```python
import struct
rom = open("Backyard Sports: Baseball 2007.gba", "rb").read()
PTR = 0x39EBC8                    # file offset of 0x0839EBC8
for i in range(8):
    a = struct.unpack_from("<I", rom, PTR + 4*i)[0] - 0x08000000
    s = rom[a:a+8].split(b"\x5e")[0]
    print(i, "".join(chr(c + 0x21) for c in s))
```

Output:

```
0 NACHOS
1 HOOPS
2 LIBERTY
3 BIGFISH
4 ANCHOVY
5 BABYBEAR
6 SPACEMAN
7 SHOWTIME
```

Legal note: no ROM, extracted graphics, music or other copyrighted assets are
redistributed here. Only hashes, addresses, algorithms, the eight short
developer-authored code words and my own screenshots/notes are published.
