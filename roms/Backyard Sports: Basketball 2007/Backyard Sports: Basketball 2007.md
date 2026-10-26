# Backyard Sports: Basketball 2007 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Backyard Sports: Basketball 2007/Backyard Sports: Basketball 2007.gba` |
| Size | 4,194,304 bytes (`0x400000`, 4 MiB) |
| Header title (`0xA0`) | `BBASKET2007` |
| Game code (`0xAC`) | `BB7E` |
| Maker (`0xB0`) | `70` |
| Version (`0xBC`) | `00` |
| Fixed `0xB2` | `0x96` ✔ |
| Entry (`0x00`) | `0xEA00002E` → ARM branch to `0x080000C0` (stock crt0) |
| Complement check (`0xBD`) | `0x25`; recomputed `-(sum(0xA0..0xBC)+0x19)&0xFF = 0x25` ✔ |
| `0xBE`–`0xBF` | `0x0000` (reserved) |
| MD5 | `175ffe1ee242cac0316a9882a240d794` |
| SHA-1 | `9852c09a6d31bd39602dd1e92df7577bea7ad4a8` |
| SHA-256 | `c373a662ff16d96009b16af1fa4e8fe453615651b463dd379dde06d1d5dade77` |

**Embedded GBA-header scan** (156-byte Nintendo logo search over the whole file):

* `0x000000` — the game header (`BBASKET2007`, `BB7E`, ver 00).
* `0x04D370` — a **second complete header** with the same title/code, the same
  `0xEA00002E` entry branch and its own entry at `0x084D430` (`+0xC0`). The
  bytes at `+0xC0` are Thumb code (`f0 b5 ...`), so this is the embedded
  multi-boot/link-cable child image, not a second game and not a boot selector.
  No other logo hits exist in the 4 MiB image.

**Patch check.** No trainer/intro/cracktro: the entry branch is stock, the
header complement is valid, the embedded header is a copy of the same retail
header, and no non-game banner strings were found. The image is treated as an
unpatched retail build.

## 2. Executive summary

The game has **no password/passcode system** (`password`, `passcode`,
`pass word`: 0 occurrences each) and **no debug menu**. Its developer-intended
cheat system is the Backyard-engine **button-code table on the pre-game
matchup screen**:

* A **20-entry table** of NUL-padded ASCII button sequences at
  `0x083ABC5C` (file `0x3ABC5C`), 10 bytes per entry.
* Buttons are recorded into a 30-press buffer at `0x030007D8`
  (counter `0x030007F7`) as the letters `a b s t r l u d v m`.
* The matcher at `0x0801FD08` runs a `strstr`-style search
  (`0x08067A4C`) of the buffer against all 20 entries and keeps the match
  that occurs **latest** in the buffer. It stores the 1-based table position
  in the byte at `0x03003E24` (`game struct 0x03003770 + 0x6B4`).
* Entries **1–5** are the five global game modifiers (the published set).
* Entries **6–19** are **power-up selector codes**. In play, `0x08027600`
  range-checks the cheat index (`6 < index <= 19`) and a 14-entry jump table
  at `0x08027674` calls `0x08040B2C(type)` with a power-up type 0–13. The
  game records the active type at `0x0300098C` (signed byte, `-1` = none)
  and a timer at `0x0300098D` (starts at 5). These 14 codes are absent from
  every published list.
* Entry **20** (`msm`) is the table's last slot and is a special "master"
  value; because the matcher only fires on A/Start, the literal string `msm`
  does not submit: adding a trailing A (`msma`) does, and stores index 20.
* **Novel input found and confirmed in-game:** `B Select Select B B B B A`
  (`bsbbbba`) is not in the table and not in any published list; the
  substring matcher resolves it to entry 5 and the game starts with the
  10-second quarter clock and 10-second shot clock (screenshots below).
  Separately, `msvvva` (entry 6) activates power-up type 0 and `msvbua`
  (entry 9) activates type 1, both read back from the game's own
  `0x0300098C`/`0x0300098D` fields.

The 4 in-ROM cheat descriptions ("Hot hands", "Super speed", "All dunks",
"Unlimited turbo") are present at `0x0838409D`–`0x083841C8`, but the
**"Cheats" screen is not reachable**: the Extras menu has exactly four rows
(Meet the Players, Unlocked Awards, Past Game MVPs, Credits) and the
`Cheats` label at `0x0837CAEC` is never displayed. No pointer references any
of the four description strings.

The **9-entry coach-name mechanism of Backyard Baseball 2006 is absent**:
the 4 MiB contains no fixed-stride run of ≥5 NUL-terminated uppercase name
records (strides 6–24), all nine 2006 literals (`BABYBEAR`, `BIGFISH`,
`NACHOS`, `HOOPS`, `LIBERTY`, `ANCHOVY`, `SPACEMAN`, `SHOWTIME`, `ATLANTIS`)
occur 0 times in uppercase, and entering `BIGFISH` and `BABYBEAR` in the real
Coach Sign In name grid produced no unlock message — both were accepted as
ordinary coach names and went straight to Game Setup.

A secondary, non-code name table does exist: the Create Player screen offers
a 59-record **nickname preset** list (from `"SUPERSTAR"` at `0x081306B4` to
`"AXEMAN"` at `0x08130DC4`); entries such as `"YAO MAN"` are paired with a
real-player identity (`YM / YAO / MING`). This is a selectable preset, not a
typed code, and is not part of the button-code space.

## 3. How to reproduce

Emulator/display used:

```bash
Xvfb :161 -screen 0 1024x768x24 &
DISPLAY=:161 openbox &
DISPLAY=:161 SDL_AUDIODRIVER=dummy mgba -3 \
  "Backyard Sports: Basketball 2007.gba" &
```

The mGBA binary on this host is `/usr/games/mgba` (not on `PATH` by default).
Default SDL keymap used throughout:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

### 3.1 Exact path to the cheat screen (from boot, ~50 s)

```
reset → legal screen (A) → title (Start) → Main Menu
  → PICK-UP GAME (A)
  → Game Setup (A) → Select Team (A) → Select Court (A)
  → Ball Toss (A, then A) → Player Select (A once per pick; Start randomises)
  → Edit Lineup (A) → **Matchup screen**
```

The matchup screen shows `VISITOR PLAYER 1 / HOME CPU`, the court and
`PICK-UP GAME`. It is the screen that feeds the cheat recorder and the only
screen on which the 20 codes were observed to take effect.

### 3.2 Entering a code and reading the ROM's verdict

The code must be typed **on the matchup screen**. The matcher is called only
after an **A (letter `a`)** or **Start (letter `t`)** press; all codes ending
in `A` therefore produce their verdict on the final A. A matched code
**consumes that A** (the screen does not advance); press A once more to start
the game. Codes ending in Start (`ssbbt`) resolve on the Start press.

Every test below was automated with `xdotool` and read back from the game's
own index byte in an mGBA savestate (`Shift+F1`..`F10` save; `F1`..`F10` load).
mGBA 0.10.5 savestates are PNGs whose `gbAs` chunk is a zlib stream; IWRAM is
at decompressed offset `0x19000`, so
`RAM 0x0300xxxx → state 0x19000 + xxxx`. The cheat index is at state offset
`0x1CE24` (`0x03003E24`).

```python
# state.py (excerpt)
import struct, zlib
def gbas(path):
    d = open(path, "rb").read(); off = 8
    while off < len(d):
        ln = struct.unpack_from(">I", d, off)[0]
        if d[off+4:off+8] == b"gbAs":
            return zlib.decompress(d[off+8:off+8+ln])
        off += 12 + ln
iw = gbas("Backyard Sports: Basketball 2007.ss2")[0x19000:0x21000]
print(iw[0x3E24])          # cheat index: 0 = rejected, 1..20 = table position
```

### 3.3 Published codes tested (GameFAQs GBA 2007)

Source: `https://web.archive.org/web/20181126025856/https://gamefaqs.gamespot.com/gba/935651-backyard-sports-basketball-2007/cheats`
(capture of the GameFAQs GBA cheats page; direct fetch is 403).

| Published effect | Published code | Table entry | Index observed |
|---|---|---|---|
| Hot Hands | `UP,UP,DOWN,DOWN,A` | 1 `uudda` | 1 |
| Super Speed | `DOWN,UP,DOWN,UP,A` | 2 `dudua` | 2 |
| All shot are dunks | `SELECT,SELECT,B,B,START` | 3 `ssbbt` | 3 |
| Unlimited turbo | `UP,UP,LEFT,RIGHT,B,A` | 4 `uulrba` | 4 |
| 10 Second Quarters | `SELECT,B,B,B,B,A` | 5 `sbbbba` | 5 |

All five literals are present in the ROM table, and all five were entered in
the emulator. The 10-second-quarter code was additionally confirmed visually
(clock `00:10`, shot clock `10`).

### 3.4 Negative and novel inputs tested

| Input | Letters | Why | Index observed |
|---|---|---|---|
| `uuddd` | Up Up Down Down Down | not a table entry | 0 |
| `uuuua` | Up Up Up Up A | not a table entry | 0 |
| `msm` | L Select L | entry 20 without an A/Start trigger | 0 |
| `msma` | L Select L A | entry 20 with trigger | 20 |
| 35 × `B` | `bbbb…` | overlong input | counter stops at 30, 31st+ dropped |
| `buudda` | B Up Up Down Down A | **novel** substring of entry 1 | 1 |
| `bbuudda` | B B Up Up Down Down A | **novel** substring of entry 1 | 1 |
| `bsbbbba` | B Select Select B B B B A | **novel** substring of entry 5 | 5 |
| `msvbua` | L Select R B Up A | **novel table entry 9** (not in 2002 table) | 9 |

## 4. Address map

File offset → ROM address is `0x08000000 + offset`. Code is Thumb unless
noted.

| Symbol | ROM address | File offset | Notes |
|---|---|---|---|
| Cheat sequence table (20 × 10 bytes) | `0x083ABC5C` | `0x3ABC5C` | ASCII, NUL-padded |
| Entry 1 `uudda` | `0x083ABC5C` | `0x3ABC5C` | |
| Entry 5 `sbbbba` | `0x083ABC84` | `0x3ABC84` | 10-second quarters |
| Entry 9 `msvbua` | `0x083ABCAC` | `0x3ABCAC` | new vs 2002 table |
| Entry 14 `msvbla` | `0x083ABCDE` | `0x3ABCDE` | new vs 2002 table |
| Entry 15 `msvmla` | `0x083ABCE8` | `0x3ABCE8` | new vs 2002 table |
| Entry 20 `msm` | `0x083ABD1A` | `0x3ABD1A` | special slot |
| Table end | `0x083ABD24` | `0x3ABD24` | next: a text/font pointer table |
| Matcher / dispatcher | `0x0801FD08` | `0x1FD08` | loops 20 entries |
| `strstr`-style comparator | `0x08067A4C` | `0x67A4C` | returns match pointer or 0 |
| Button-letter recorder | `0x0801FEA4` | `0x1FEA4` | appends `b,u,d,l,r,s,m,v,a,t` |
| Matcher call sites | `0x0801FFD2`, `0x08020004` | | after `A`, after `Start` |
| Accept / advance routine | `0x0801FE18` | `0x1FE18` | called when byte `0x030007D4 == 3` at `0x0802017E` |
| Input buffer (30 bytes) | `0x030007D8` | IWRAM | letter history |
| Input counter | `0x030007F7` | IWRAM | accepts old count 0..29 |
| Base of game struct | `0x03003770` | IWRAM | |
| Cheat index | `0x03003E24` | IWRAM | `base + 0x6B4`, 1-based; 0 = none |
| Quarter length field | `0x03003E34` | IWRAM | `base + 0x6C4`, seconds |
| Second clock field | `0x03003E38` | IWRAM | `base + 0x6C8`, seconds |
| Shot-clock field | `0x03003E3C` | IWRAM | `base + 0x6CC`, seconds |
| Quarter/clock setup | `0x08026818` | `0x26818` | reads index at `0x08026848`–`4E` |
| Power-up dispatch (indices 6–19) | `0x08027600` | `0x27600` | range check + `mov pc` jump table |
| Power-up jump table (14 entries) | `0x08027674` | `0x27674` | index 6→type 0 … index 19→type 13 |
| Power-up activation | `0x08040B2C` | `0x40B2C` | stores type, timer, entity |
| Active power-up type | `0x0300098C` | IWRAM | signed byte, `-1` = none |
| Power-up timer | `0x0300098D` | IWRAM | starts at 5 |
| Power-up entity | `0x03000988` | IWRAM | scene object pointer |
| "Cheats" label | `0x0837CAEC` | `0x37CAEC` | present, never displayed |
| Description "Hot hands…" | `0x0838409D` | `0x38409D` | embeds glyph bytes |
| Description "Super speed…" | `0x083840EA` | `0x3840EA` | |
| Description "All dunks…" | `0x08384139` | `0x384139` | |
| Description "Unlimited turbo…" | `0x08384187` | `0x384187` | |
| Create-Player nickname list (59) | `0x081306B4`–`0x08130DC4` | `0x1306B4`–`0x130DC4` | quoted nickname + initials/first/last |

### 4.1 Index readers (static scan)

A Capstone scan for code that loads `0x03003770`, adds `0x6B4`, and reads the
byte found **36 strict read sites**, plus the group dispatch at `0x08027600`
(whose `0x6B4` literal is farther from the `ldrb`). The immediate values
compared against that byte are only:

| Index | Comparison site(s) | Meaning |
|---|---|---|
| 1 | `0x0802CB7A`, `0x0802CD18`, `0x0802CEB4`, `0x0802EA86`, `0x0802EC14`, `0x0803110E`, `0x080319F0`, `0x08036ACA` | hot hands |
| 2 | `0x08037206`, `0x0803777E` | super speed |
| 3 | `0x08029964`, `0x0802F7AC`, `0x08030C6C` | all dunks |
| 4 | `0x080377FC` | unlimited turbo |
| 5 | `0x0802684E` | 10-second quarters/shot clock |
| 6–19 | `0x08027606` (`cmp r0,#5 / bhi`), `0x0802760C` (`cmp r0,#19 / bls`) | group power-up dispatch |
| 20 | `0x08001AA6`, `0x080043C8`, `0x080044B4`, `0x0800458C`, `0x080046BC`, `0x08004774`, `0x080048C2`, `0x08004A58`, `0x08004B66`, `0x080059BA`, `0x0800AF86`, `0x0800B004`, `0x0800BA1C`, `0x0801E25A`, `0x0801E288`, `0x0801E47A`, `0x0801E4B6`, `0x0804C6BC` | special "master" value |

The first five are individual reads; the 14 values 6–19 are handled as one
group. `0x08027600` loads `base+0x6B4`, checks `index > 5` and `index <= 19`,
then indexes the jump table at `0x08027674` (14 entries, one per index 6–19)
and jumps to a handler. Each handler calls `0x08040B2C` with a small type
number (0–13). The type is written to `0x0300098C`, the timer
`0x0300098D = 5`, and an entity is created at `0x03000988`
(`scnPowerUpBig.c` is in the ROM's own string table at `0x071674`).

Two readers are outside the strict 36-site window because their base/offset
loads are farther from the `ldrb`; both were verified by hand:

* index 4: `0x080377F6 ldr r5,=0x6B4; 0x080377FA ldrb r0,[r0]; 0x080377FC cmp r0,#4`
  (skips the turbo decrement at `0x08037808`).
* index 5: `0x08026848 ldr r1,=0x6B4; 0x0802684C ldrb r0; 0x0802684E cmp r0,#5`
  (writes 10 to `0x03003E34` and `0x03003E38`, then 10 to `0x03003E3C`).

## 5. Algorithm

```
letters:  A→'a' B→'b' Select→'s' Start→'t' Right→'r' Left→'l'
          Up→'u' Down→'d' R→'v' L→'m'          (KEYINPUT bits 0x001..0x200)

on the matchup screen, each frame:
    keys = ~KEYINPUT & 0x3FF
    for each of the 10 bits, in the fixed order b,u,d,l,r,s,m,v,a,t:
        if keys & bit and count <= 29:
            buffer[count++] = letter

    # matcher runs only after the 'a' and 't' appends
    on 'a' or 't':
        best = 0 ; best_pos = buffer_start - 1
        for i in 0..19:                       # 20 entries, stride 10
            p = strstr(buffer, table[i])
            if p and p > best_pos:            # latest match wins
                best_pos = p
                best = i + 1                  # 1-based table position
        *(u8*)0x03003E24 = best               # 0 = none

    if best != 0:
        play sound; set base+0x6DF/+0x6E0/+0x6E2 = 1; mark selected players
    # on leaving the screen: index and counter are cleared by the screen exit
```

The match is a **substring** test, not a suffix test, and the "latest match
wins" rule means a longer sequence typed after a shorter one supersedes it.
Because the buffer is 30 presses and is cleared on screen exit, a code must be
entered in one go on the matchup screen.

`msm` is in the table but cannot submit by itself: the matcher is only called
after A or Start, and `msm` ends in L. The reachable input is `msma` (or
`msmt`), which stores index 20.

The five global effects are read at the sites in §4.1:

* index 1 — the shot-resolution path treats the shot as "hot" (in-ROM text
  "Hot hands for everyone!").
* index 2 — the player-update path skips the normal speed limit
  ("Super speed for everyone!").
* index 3 — the shot/dunk selection forces a dunk ("All dunks.").
* index 4 — the turbo decrement is skipped ("Unlimited turbo.").
* index 5 — `0x08026818` overrides quarter length (60 → 10) and shot clock
  (24 → 10).

Indices 6–19 are a second, orthogonal layer. During play:

```
if base+0x6B4 in 6..19 and active power-up type == -1:
    type = table[index - 6]          # 14-entry jump table at 0x08027674
    activate_powerup(type)           # 0x08040B2C
        *(s8*)0x0300098C = type
        *(u8*)0x0300098D = 5
        create entity at 0x03000988, play sound, set sprite frame
```

The type is the power-up selected by that code; the timer counts down in
`0x0300098D`. This is an in-play effect, not a game-setup option, so the
setup fields at `0x03003E34`/`0x03003E38`/`0x03003E3C` remain at 60/60/24
for all power-up codes (verified).

## 6. Tables

### 6.1 The 20-entry cheat table (`0x083ABC5C`, 10 bytes/entry)

| # | Bytes | Letters | Buttons | In-ROM description? | Published for GBA 2007? | Effect |
|---|---|---|---|---|---|---|
| 1 | `uudda` | u u d d a | Up Up Down Down A | yes | yes — Hot Hands | hot hands |
| 2 | `dudua` | d u d u a | Down Up Down Up A | yes | yes — Super Speed | super speed |
| 3 | `ssbbt` | s s b b t | Select Select B B Start | yes | yes — All shot are dunks | all dunks |
| 4 | `uulrba` | u u l r b a | Up Up Left Right B A | yes | yes — Unlimited turbo | unlimited turbo |
| 5 | `sbbbba` | s b b b b a | Select B B B B A | **no** | yes — 10 Second Quarters | 10 s quarters + shot clock |
| 6 | `msvvva` | m s v v v a | L Select R R R A | no | **no** | power-up type 0 |
| 7 | `msvvba` | m s v v b a | L Select R R B A | no | **no** | power-up type 2 |
| 8 | `msvvsa` | m s v v s a | L Select R R Select A | no | **no** | power-up type 3 |
| 9 | `msvbua` | m s v b u a | L Select R B Up A | no | **no** | power-up type 1 |
| 10 | `msvvua` | m s v v u a | L Select R R Up A | no | **no** | power-up type 4 |
| 11 | `msvvra` | m s v v r a | L Select R R Right A | no | **no** | power-up type 7 |
| 12 | `msvvda` | m s v v d a | L Select R R Down A | no | **no** | power-up type 8 |
| 13 | `msvvla` | m s v v l a | L Select R R Left A | no | **no** | power-up type 5 |
| 14 | `msvbla` | m s v b l a | L Select R B Left A | no | **no** | power-up type 6 |
| 15 | `msvmla` | m s v m l a | L Select R L Left A | no | **no** | power-up type 9 |
| 16 | `msvvma` | m s v v m a | L Select R R L A | no | **no** | power-up type 10 |
| 17 | `msvbva` | m s v b v a | L Select R B R A | no | **no** | power-up type 11 |
| 18 | `msvbba` | m s v b b a | L Select R B B A | no | **no** | power-up type 12 |
| 19 | `msvbsa` | m s v b s a | L Select R B Select A | no | **no** | power-up type 13 |
| 20 | `msm` | m s m | L Select L | no | **no** | special master value (`msma` submits it) |

The 2002 game's 17-entry table at `0x08133E90` is **not** at that address in
this ROM. The same engine table moved to `0x083ABC5C` and grew to 20 entries:
the 17 strings of the 2002 table plus 3 new power-up selectors
(`msvbua`, `msvbla`, `msvmla`). The matcher design is unchanged
(`strstr` over 10-byte records, latest match wins).

The table ends at `0x083ABD24`; the matcher's loop bound is
`0x0801FD34 cmp r4,#19 / bls` → exactly 20 entries.

The three entries **new relative to the 2002 table** are 9 `msvbua`,
14 `msvbla`, 15 `msvmla`; all three are power-up selectors (types 1, 6, 9).

### 6.2 Power-up selector mapping (indices 6–19)

The jump table at `0x08027674` maps each table index to a power-up type. The
type is the argument to `0x08040B2C`; it is also the value stored at
`0x0300098C`. Type 13 is clamped to 12 when a game flag is clear at
`0x08040B32` (observed for entry 19).

Lineage: 11 of these 14 selectors (6, 7, 8, 10, 11, 12, 13, 16, 17, 18, 19)
already existed in the 2002 game's 17-entry table (see the repo's Backyard
Basketball 2002 report); 9, 14 and 15 are new in 2007. None of the 14 appears
in a published 2007 code list.

| Table entry | Sequence | Power-up type | Dynamic confirmation |
|---|---|---|---|
| 6 | `msvvva` | 0 | type 0 observed, timer 5 |
| 7 | `msvvba` | 2 | type 2 observed, timer 5 |
| 8 | `msvvsa` | 3 | type 3 observed, timer 5 |
| 9 | `msvbua` | 1 | type 1 observed, timer 5→0 |
| 10 | `msvvua` | 4 | type 4 observed, timer 5 |
| 11 | `msvvra` | 7 | type 7 observed, timer 5 |
| 12 | `msvvda` | 8 | type 8 observed, timer 5→0 |
| 13 | `msvvla` | 5 | type 5 observed, timer 5 |
| 14 | `msvbla` | 6 | type 6 observed, timer 5 |
| 15 | `msvmla` | 9 | type 9 observed, timer 5→0 |
| 16 | `msvvma` | 10 | type 10 observed, timer 5→0 |
| 17 | `msvbva` | 11 | type 11 observed, timer 5→0 |
| 18 | `msvbba` | 12 | type 12 observed, timer 5→0 |
| 19 | `msvbsa` | 13 (clamped to 12) | type 12 observed, timer 5 |

The dynamic confirmation is the game's own `0x0300098C` byte sampled from
savestates after a shot: baseline keeps `-1`; the code's type appears for
several frames, with `0x0300098D` starting at 5. The exact in-play rule for
each type (speed, size, shot, etc.) is not named by the ROM's UI, so the
type number is the precise, reproducible identifier; see §8.

### 6.3 Input alphabet and bounds

* Ten buttons only: `A B Select Start Right Left Up Down R L`, recorded as
  the ASCII letters `a b s t r l u d v m`.
* Buffer: 30 bytes at `0x030007D8`; counter at `0x030007F7`. Recorder
  condition is `cmp r2,#29 / bhi` on the old count, so old counts 0..29 are
  stored (30 presses); the 31st and later presses are dropped.
* No checksum, no field widths, no reserved bits: the accepted set is the 20
  literal strings, plus the infinite family of inputs that contain one of them
  as a substring (the matcher is `strstr`).

### 6.4 In-ROM descriptions and glyph map

The four description strings decode with the same font glyph map as the 2002
game: `0x8F`=A, `0x90`=B, `0x95`=Up, `0x96`=Right, `0x97`=Down, `0x98`=Left;
`Select` and `Start` are spelled as ASCII.

| String | Address | Button bytes | Decodes to |
|---|---|---|---|
| Hot hands for everyone! | `0x0838409D` | `95 20 95 20 97 20 97 20 8F` | Up Up Down Down A = entry 1 |
| Super speed for everyone! | `0x083840EA` | `97 20 95 20 97 20 95 20 8F` | Down Up Down Up A = entry 2 |
| All dunks. | `0x08384139` | `Select Select 90 90 Start` | Select Select B B Start = entry 3 |
| Unlimited turbo. | `0x08384187` | `95 20 95 20 98 20 96 20 90 20 8F` | Up Up Left Right B A = entry 4 |

There is **no description** for entry 5 (the published 10-second-quarters
code) or for any of entries 6–20. The `Cheats` screen that would have shown
these four strings is cut from the Extras menu.

### 6.5 Cheat-driven configuration fields

Measured from savestates taken after the game had started (not during the
transition):

| Field | Base game | Entry 5 (`sbbbba` / `bsbbbba`) | Power-up codes (6–19) |
|---|---|---|---|
| `0x03003E34` quarter length (s) | 60 (`0x3C`) | 10 (`0x0A`) | 60 |
| `0x03003E38` second clock field (s) | 60 | 10 | 60 |
| `0x03003E3C` shot clock (s) | 24 (`0x18`) | 10 | 24 |

The power-up codes do not alter these setup fields; their effect is a runtime
power-up (`0x0300098C`/`0x0300098D`, §6.2). No other stable field in
`0x03003770`–`0x03003E80` differed between a baseline game and games started
with entries 6, 9, 14, 15 or 19 (only the index byte itself and genuinely
dynamic gameplay state differed).

### 6.6 Create-Player nickname presets (secondary, not a code system)

The Create Player screen's NICKNAME field cycles a 59-record list of quoted
presets (`0x081306B4`–`0x08130DC4`). Each preset is followed by a two-letter
initials field and a first/last name, e.g.:

| Nickname | Initials | First | Last |
|---|---|---|---|
| `"YAO MAN"` | YM | YAO | MING |
| `"VINSANITY"` | VC | VINCE | CARTER |
| `"SHAQ DIESEL"` | SO | SHAQUILLE | O'NEAL |
| `"THE TRUTH"` | PP | PAUL | PIERCE |
| `"T-MAC"` | TM | TRACY | MCGRADY |
| `"ALL THAT"` | AL | — | — (custom player) |

This is a **selectable preset list**, not a typed name-code table; it is
developer-intended content, but it is not part of the matchup button-code
space and is not required to explain the five published codes.

## 6b. Enumeration

### 6b.1 Space definition

* **Alphabet:** 10 buttons (`A B Select Start Right Left Up Down R L`).
* **Table:** exactly **20** NUL-terminated ASCII strings of length 3–6 at
  `0x083ABC5C`, stride 10. The matcher's loop bound (`cmp r4,#19`) confirms
  there is no 21st entry.
* **No checksum, no field widths, no reserved bits.** The accepted set is the
  20 strings. Because the comparator is `strstr`, every input that contains
  one of the 20 strings is also accepted and resolves to the **latest**
  matching entry, so the input space is infinite but has exactly 20
  equivalence classes.
* **Effect space:** five global modifiers (indices 1–5), 14 power-up types
  (indices 6–19), and the special master value 20. The five published codes
  cover exactly the global modifiers; the 14 power-up selectors are
  unpublished.

### 6b.2 Validator model (reimplementation)

```python
TABLE = ["uudda","dudua","ssbbt","uulrba","sbbbba",
         "msvvva","msvvba","msvvsa","msvbua","msvvua","msvvra",
         "msvvda","msvvla","msvbla","msvmla","msvvma","msvbva",
         "msvbba","msvbsa","msm"]
KEY = {"a":0x001,"b":0x002,"s":0x004,"t":0x008,"r":0x010,
       "l":0x020,"u":0x040,"d":0x080,"v":0x100,"m":0x200}

def record(keys, buf):
    for ch in "budlrsmvat":          # fixed order used by the ROM recorder
        if keys & KEY[ch] and len(buf) < 30:
            buf.append(ch)

def resolve(buf):
    best, best_pos = 0, -1
    for i, s in enumerate(TABLE):
        p = bytes(buf).find(s.encode())
        if p >= 0 and p > best_pos:
            best_pos, best = p, i + 1
    return best                      # 0 = rejected

def submit(seq):
    buf = []
    for ch in seq:
        record(KEY[ch], buf)
        idx = 0
        if ch in "at":               # matcher runs only after A / Start
            idx = resolve(buf)
    return idx, buf
```

This model agrees with all 20 table-entry tests and the five control tests in
§3.4: `uuddd`/`uuuua` → 0, `msm` → 0 (no trigger), `msma` → 20, 35 × B →
counter 30, `buudda`/`bbuudda` → 1, `bsbbbba` → 5.

### 6b.3 Novel codes (not on GameFAQs/VGChartz/TCRF; table entries or substring variants)

| Code | Letters | Buttons | Index | In-game evidence |
|---|---|---|---|---|
| `bsbbbba` | b s b b b b a | B Select Select B B B B A | **5** | index byte `0x03003E24 = 0x05`; game clock `00:10`, shot clock `10` (`shots/novel_bsbbbba.png`, `shots/novel_clean.png`) |
| `msvvva` | m s v v v a | L Select R R R A | **6** | power-up type 0 appears at `0x0300098C`, timer 5 at `0x0300098D`; baseline stays `-1` |
| `msvbua` | m s v b u a | L Select R B Up A | **9** | power-up type 1 appears at `0x0300098C`; timer 5→0 (`shots/idx9.png`) |
| `buudda` | b u u d d a | B Up Up Down Down A | **1** | index byte `0x03003E24 = 0x01`; hot-hands effect (documented by `0x0838409D`) |
| `msma` | m s m a | L Select L A | **20** | index byte `0x03003E24 = 0x14`; game starts normally (`shots/novel_msma.png`) |

`msvbua` is the cleanest novel **table** code: entry 9 does not exist in the
2002 table and is absent from every published 2007 list; the game activates
power-up type 1 and the type/timer were sampled through the full 5→0 timer.
`msvvva` (entry 6) likewise activates type 0 but also existed in the 2002
table (unpublished there too). Both are reproducible with
`scripts/sample_powerup.py`.

`bsbbbba` is the headline novel **input**: it is **not** one of the 20 table
strings and is **not** in any published list, but the substring matcher
resolves it to entry 5. Screenshot `shots/novel_bsbbbba.png` shows the
10-second quarter clock (`00:10`) and shot clock (`10`) at tip-off;
`shots/novel_clean.png` shows the same game a few seconds later (`00:07`).
The published `sbbbba` produces the identical effect (`shots/s5b.png`), which
validates that the novel input rides the same entry-5 path.

`buudda` (index 1) demonstrates the same substring property against entry 1
(hot hands). `msma` reaches the otherwise unsubmittable 20th slot.

### 6b.4 Bounds proven by rejection

| Test | Why it is out of the accepted set | Observed result |
|---|---|---|
| `uuddd` | 5 letters, not a table string and no substring match | index stays 0 |
| `uuuua` | 5 letters, not a table string | index stays 0 |
| `msm` (no A/Start) | table entry 20 exists, but the matcher is not invoked because the last press is L | index stays 0 |
| 35 × B | buffer accepts only 30 presses (`cmp #29`) | counter 30; presses 31–35 dropped; buffer `bbbb…` (30) |
| `msma` | table entry 20 submitted with a trigger | index 20 (special value, not an effect index) |
| index 21+ | matcher loop `cmp r4,#19 / bls` | no 21st entry exists |
| index 6–19 | accepted and dispatched as power-up types 0–13 (not rejected) | `0x0300098C` takes the type; `0x0300098D` starts at 5 |

The ROM's rejection signal is the index byte remaining 0; there is no
"invalid code" message on the matchup screen. A rejected input simply leaves
the game unchanged and the next A starts a normal game.

### 6b.5 Coach-name mechanism: absent (bounded negative)

Backyard Baseball 2006 has a nine-entry coach-name table that unlocks
players/courts. In this 4 MiB Basketball 2007 image:

* Fixed-stride scan for runs of ≥5 NUL-terminated uppercase name records at
  every stride 6–24: **0 runs** (a run would be the signature of the 2006
  table). The same scan over lowercase records produces only dense-data false
  positives.
* The nine 2006 literals occur **0 times** in uppercase: `BABYBEAR`,
  `BIGFISH`, `NACHOS`, `HOOPS`, `LIBERTY`, `ANCHOVY`, `SPACEMAN`,
  `SHOWTIME`, `ATLANTIS` (`hoops` appears twice as ordinary lowercase prose).
* Dynamic probes through the real Coach Sign In name grid
  (`A–Z`, space, `0–9`, `-`, DEL, OK): `BIGFISH` and `BABYBEAR` were accepted
  as ordinary coach names, saved, and went straight to Game Setup; no
  `YOU HAVE UNLOCKED …` message or roster/court change appeared
  (`shots/season01.png`, `shots/nameentry.png`, `shots/n_babybear2.png`).
* An 8-character name fits the grid; the slot list is a plain save file, not a
  code validator.

Conclusion: the nine-entry coach-name cheat mechanism of Backyard Baseball
2006 was **not carried into Basketball 2007**; the Coach Sign In path is a
normal name/save slot.

### 6b.6 "Cheats" screen: present in text, unreachable

The Extras menu renders exactly four rows:

```
MEET THE PLAYERS
UNLOCKED AWARDS   (greyed until unlocked)
PAST GAME MVPS    (greyed until a game MVP is viewed)
CREDITS
```

The string `Cheats` at `0x0837CAEC` sits between `Past game MVPs` and
`Credits` in the text bank, and the four description strings at
`0x0838409D`–`0x08384187` are complete, but no Extras row displays them.
Pressing Select, L or R on the Extras screen does not add a row
(`shots/extras_select.png`). No pointer literal references any of the four
description strings (0 hits for each `u32` address), so they are dead text or
reached only through the cut text-ID menu. Every reachable menu was walked
(§7); no Cheats screen exists in this build.

## 7. Validation evidence

### Observed (emulator)

* Boot → legal → title → Main Menu; all six main items walked.
* Options → Game Setup (6 rows) and General (6 rows); all rows rendered and
  the values cycled.
* Extras (4 rows), Meet the Players (roster grid), Credits; Unlocked Awards
  and Past Game MVPs greyed with their "not available" messages.
* Mini-Games (4 rows: Practice, Hot Shot, Block Shot, Ball Balance).
* Multiplayer (3 rows: Head to Head, Hot Shot, Block Shot) → Awaiting
  Connection.
* Season Play → Coach Sign In (2 NEW slots, COPY, DELETE) → name grid;
  `BIGFISH` and `BABYBEAR` accepted as ordinary coaches.
* Pick-Up Game → Game Setup → Select Team (30 NBA teams) → Select Court →
  Ball Toss → Player Select (5 picks, `?` Custom Player) → Edit Lineup →
  Matchup screen.
* Custom Player (10 NEW slots, DELETE) → Create Player (Nickname, Body,
  Appearance, Hair Style, Hair Color).
* Pause menu: Resume, Time Out, Substitution, Quit Game (Yes/No confirm).
* All 20 table sequences typed on the matchup screen and read back from
  `0x03003E24` (enumeration log). Controls §3.4.
* `sbbbba` and `bsbbbba` games: clock `00:10`, shot clock `10`; baseline
  game: clock `01:00`, shot clock `24`.
* Savestate diff: only entry 5 changes `0x03003E34`/`0x03003E38`/`0x03003E3C`
  to 10/10/10; power-up codes 6, 9, 14, 15, 19 leave 60/60/24.
* Power-up sampling (`scripts/sample_powerup.py`), 14 samples per run:
  baseline keeps `0x0300098C = -1` for all samples. Each of the 14 power-up
  codes produced its mapped type: 6→0, 7→2, 8→3, 9→1, 10→4, 11→7, 12→8,
  13→5, 14→6, 15→9, 16→10, 17→11, 18→12, 19→12 (type 13 clamped).
  `0x0300098D` starts at 5 and counts down while the type is active. This is
  the game's own activation signal, not a visual inference.

Screenshots (in `/tmp/opencode/bball2007/shots/`):
`t02.png` (title), `mm3.png` (main), `m10.png` (Game Setup), `m05.png`
(General), `extras_select.png` (Extras, 4 rows), `season01.png` (Coach Sign
In), `nameentry.png` (name grid), `n_babybear2.png` (BABYBEAR → Game Setup),
`mp01.png` (Multiplayer), `p05.png` (Player Select), `cp2.png` (Create
Player), `pause_menu.png` (pause), `play_base.png` (baseline 01:00),
`s5b.png` (published `sbbbba` 00:10), `novel_bsbbbba.png` (novel `bsbbbba`
00:10), `novel_clean.png` (novel game 00:07), `idx9.png` (entry 9 accepted,
01:00), `novel_msma.png` (index 20, 01:00), `p6_a3.png`/`icon_idx6_big.png`/
`icon_cmp2.png` (power-up HUD sprite visible during an entry-6 play session),
`pu9_1.png` (power-up animation frame during an entry-9 session).

### Derived (disassembly)

* Table base/stride/end, matcher loop bound 20, `strstr` latest-match rule,
  recorder order and buffer cap, index store at `0x03003E24` (addresses in
  §4).
* Index comparisons: 1, 2, 3, 4, 5 individually; 6–19 as one range-gated
  jump table; 20 as the master value (§4.1).
* Entry 5's clock override at `0x08026818` and the three config fields.
* Power-up dispatch at `0x08027600`, jump table `0x08027674`, activation
  `0x08040B2C`, type/timer fields `0x0300098C`/`0x0300098D`.
* In-ROM description glyph decoding (§6.4).
* 59-record nickname preset table layout (§6.6).

### Inferred

* The intended meaning of indices 6–19: they are the developer's in-play
  power-up selectors (the "power-up" option is a separate Game Setup row).
  Their grouping in the same table as the global modifiers suggests they were
  the payload of the cut Cheats screen; the codes remain live in gameplay.
* Index 20's exact intended effect: the option-flag writers substitute
  `0xFF` when the index is 20 (comparisons at `0x080043C8` and `0x0801E25A`),
  so `msma` is a master/"all bits" value; its visible effect was not isolated
  (the game starts with normal 60 s / 24 s clocks).
* The four description strings belong to the cut Cheats screen.

## 8. Unknowns

* The per-type gameplay rule for the 14 power-up selectors. In this SHA-256
  they select power-up types 0–13 and the type/timer activation is proven;
  the rule attached to each type (speed, size, shot, etc.) is not named by
  any reachable UI or string.
* The exact gameplay semantics of each global effect beyond the ROM's own
  one-line description (e.g., the exact hot-hands probability, the
  super-speed multiplier, the turbo decrement rule). The acceptance and
  dispatch addresses are proven; the numeric tuning was not.
* Why types 10–13 behave differently: the activation stores them, but type 13
  is clamped to 12 when a game flag is clear at `0x08040B32`, and the
  sprite-position table at `0x08071624` only has five entries selected by a
  separate random index. Whether 10–13 are distinct power-ups or fallback
  values is not proven.
* Whether an indirect (RAM-pointer) reader of the index exists outside the
  36 static read sites. The code uses a single global base (`0x03003770`) and
  no literal `0x03003E24` appears in the ROM, so this is unlikely, but it is
  not formally excluded.
* The reason the Cheats row was cut (content approval vs. a build flag); no
  reachable reference to the four description strings was found.

## 9. Tooling

* mGBA 0.10.5 (SDL frontend, `/usr/games/mgba`), Xvfb `:161` (1024×768×24),
  openbox, `xdotool`, `scrot`, ImageMagick `import`/`convert`, Python 3.
* `arm-none-eabi-objdump` (binutils-arm-none-eabi), Capstone 5.0.7.
* Scripts in `/tmp/opencode/bball2007/scripts/`:
  * `keys.py` — xdotool key sender + window capture.
  * `testcodes.py` — button-letter → key map, savestate save/load, index read.
  * `enumerate.py` — final 20-entry + control enumeration (log
    `enumeration.log`, data `enumeration.json`).
  * `state.py` — mGBA `gbAs` PNG chunk → IWRAM reader.
  * `index_readers.py`, `index_track.py`, `index_cmps.py` — static scans for
    `base+0x6B4` readers and their comparisons.
  * `scan_headers.py` — identity/embedded-header scan.
  * `coach_scan.py` — fixed-stride coach-name table scan.
  * `name_entry.py` — Coach Sign In grid driver.
  * `playshots.py`, `collect_states.py`, `pre_states.py`, `mid_states.py` —
    in-game effect capture and RAM diffing.
  * `sample_powerup.py` — starts a game with a given code, presses A, and
    samples `0x0300098C`/`0x0300098D` from savestates to observe the
    power-up type/timer.
* Savestates used: `matchup_clean.ss1` (matchup screen, created from a live
  run), `*.ss2`/`*.ss4`/`*.ss5` scratch slots. mGBA writes these next to the
  ROM; they are git-ignored and were removed after the run.

## Legal note

No ROM, graphics, music or extracted game text is redistributed here. The
report contains hashes, addresses, algorithms, button sequences and my own
console output only. Game text is quoted only as short evidence snippets.

---

### Reproduction quick card

```
Main Menu → PICK-UP GAME
  Game Setup A → Select Team A → Select Court A
  → Ball Toss A (spin) → A (result) → Player Select Start (random five)
  → Edit Lineup A → Matchup
  baseline:                     A (start)                     → clock 01:00, shot 24
  published 10 s quarters:      Select B B B B A, then A      → clock 00:10, shot 10
  novel substring code:         B Select Select B B B B A, A  → clock 00:10, shot 10
  entry 6 (power-up):           L Select R R R A, then A      → type 0, timer 5
  entry 9 (power-up):           L Select R B Up A, then A     → type 1, timer 5→0
  entry 20:                     L Select L A, then A           → clock 01:00, shot 24
  rejected:                     Up Up Down Down Down          → index 0, no effect
```
