# Backyard Basketball (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Backyard Basketball/Backyard Basketball.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`) |
| Header title (`0xA0`) | `BBASKETBALL` |
| Game code (`0xAC`) | `AYBE` |
| Maker (`0xB0`) | `70` |
| Version (`0xBC`) | `00` |
| Fixed `0xB2` | `0x96` ✔ |
| Entry (`0x00`) | `0xEA00002E` → ARM branch to `0x080000C0` |
| Header checksum (`0xBD`) | `0xB2` (computed `0xB2`) ✔ |
| MD5 | `8b525f6d0d80a287df61ec99a97c6c08` |
| SHA-1 | `b6b5b490541a3b0c3bd15e598dafe1d67a022f54` |
| SHA-256 | `c1a029c897d3fa9488aa6e3d62615f7810e92eb80fae86cb9a4318b77954964a` |

Embedded-header scan (156-byte Nintendo logo search over the whole file):

* `0x000000` — the game header (title `BBASKETBALL`, code `AYBE`, ver 00).
* `0x048D98` — a **second complete GBA header** with the same title/code, a valid
  ARM branch `0xEA00002E` and its own crt0 at `0x048E58`. This is an embedded
  multi-boot/link-cable child image, not a second game and not a boot selector.
  No other logo hits exist in the 4 MiB image.

No cracktro, trainer, intro patch or modified entry point: the first two
instructions are the stock `b 0x080000C0` + Nintendo logo, the header checksum is
consistent, and the entry region matches the rest of the build.

## 2. Executive summary

The game has **no password/passcode system** (the strings "password", "passcode",
"debug", "roster", "code" occur zero times in the file) and **no coach-name cheat
table** of the Backyard Baseball 2006 kind. What it does have is a **button-code
("cheat") system on the pre-game matchup screen**, implemented as a 17-entry
table of ASCII button-letter sequences that is matched against a rolling input
buffer with a substring search.

* The table is at `0x08133E90` (file `0x133E90`), 17 records of 10 bytes each,
  NUL-padded ASCII over the alphabet `u d l r a b s t m v`.
* Buttons are recorded into a 29-byte buffer at `0x030007F0`; the counter is at
  `0x03000F08`; the record layout is `a`=A, `b`=B, `s`=Select, `t`=Start,
  `r`=Right, `l`=Left, `u`=Up, `d`=Down, `v`=R, `m`=L.
* The matcher (`0x0801ED58`) runs `strstr(buffer, entry)` for all 17 entries,
  keeps the entry whose match is **latest in the buffer**, and stores its
  **1-based table position** at `0x030031A0 + 0x674 = 0x03003814`.
* Four entries are the documented/published cheat codes ("Hot hands",
  "Super speed", "All dunks", "Unlimited turbo"). **Thirteen entries are not in
  any published list** and were reproduced here for the first time.
* All 17 sequences were typed into the emulator; 16 of them leave the expected
  index 1…16 in `0x03003814`, proving the ROM accepts them. The 17th (`msm`) is
  a table entry that does not persist an index (it behaves as a reset/no-op and
  was rejected in the same sense a non-table sequence is).
* Non-table sequences leave the index at 0 (rejection), which bounds the space.

The four entries with an in-ROM description string are the developer-documented
ones, and each description literally embeds the button glyphs of its sequence.
The "Cheats" screen that would have displayed those descriptions is **not
reachable**: the Extras menu has four items and no "Cheats" row, although the
label exists in the text bank between "Past game MVPs" and "Credits" and the four
description strings exist at `0x396661`–`0x3967A0`. Every menu in the build was
walked (see §7) and no Cheats row appeared.

## 3. How to reproduce

Emulator and display (this session):

```bash
Xvfb :155 -screen 0 1024x768x24 &
DISPLAY=:155 openbox &
DISPLAY=:155 SDL_AUDIODRIVER=dummy mgba -3 "Backyard Basketball.gba" &
```

mGBA SDL default keymap used: **A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad=arrows**. Screenshots via `scrot`, cropped
`720x480+154+164`.

Menu path to the cheat screen (reproducible from boot, ~35 s):

```
reset → (Atari logo, NBA notice, title) → Start
  → main menu → PLAY NOW (A)
  → Coach Sign In (only on a clean save; pick NEW, type a name, OK)
  → Game Setup (A) → Select Team (A) → Select Court (A)
  → Ball Toss (A) → Player Select (pick 5) → **Matchup screen**
```

The quickest reproducible route used for every test below: load the savestate
`Backyard Basketball.ss1`, which is saved **on the matchup screen** ("Visitor
Player 1 / Home CPU", court "Queens County Municipal", Quick Game). On that
screen press the code; the last `A`/`Start` also accepts the screen. Save a
state immediately after the last press and read byte `0x1C814` of the
decompressed `gbAs` chunk, which is IWRAM `0x03003814` (see §4 for the
state-layout mapping).

### Tested inputs

All 17 table sequences were entered (see §6). In addition the following were
entered as negative controls and produced index 0:

| Input | Letters | Result (`0x03003814`) |
|---|---|---|
| Up Up Down Down Down | `uuddd` | 0 (not in table) |
| Up Up Up Up A | `uuuua` | 0 (not in table) |
| L Select L | `msm` | 0 (table entry 17, does not persist) |
| Up Up Down Down A | `uudda` | 1 (documented "Hot hands") |

Publication check: the four documented codes match the public lists
(SuperCheats, Neoseeker, Vizzed, GameFAQs PS2 page's "In Match Codes" table)
exactly, including the alternate public wording:
`Select,Select,B,B,Start` / `Up,Up,Left,Right,B,A` / `Up,Up,Down,Down,A` /
`Down,Up,Down,Up,A`. The ROM table order is
`uudda, dudua, ssbbt, uulrba, …` = Hot hands, Super speed, All dunks, Unlimited
turbo.

## 4. Address map

File offset → ROM address is `0x08000000 + offset`. All code is Thumb unless
noted.

| Symbol | ROM address | File offset | Notes |
|---|---|---|---|
| Cheat sequence table (17 × 10 bytes) | `0x08133E90` | `0x133E90` | ASCII, NUL padded |
| Entry 0 `uudda` | `0x08133E90` | `0x133E90` | |
| Entry 16 `msm` | `0x08133F30` | `0x133F30` | |
| Matcher / dispatcher | `0x0801ED58` | `0x1ED58` | called with a dummy r0 |
| `strstr`-style comparator | `0x08066940` | `0x66940` | returns match pointer or 0 |
| Button-letter recorder | `0x0801F03C` | `0x1F03C` | appends 'b','u','d','l','r','m','v','a','t' |
| Matcher call sites | `0x0801F16A`, `0x0801F19C` | | after each append |
| Cheat-index store | `0x03003814` | IWRAM | `0x030031A0 + 0x674`, byte, 1-based |
| Cheat-index clear | `0x0801F446` | `0x1F446` | `strb 0` after the screen exits |
| Input buffer | `0x030007F0` | IWRAM | 29-byte letter history |
| Input counter | `0x03000F08` | IWRAM | byte, tested `<= 29` (`cmp #0x1d`) |
| Base of the option/game struct | `0x030031A0` | IWRAM | |
| Index readers (game setup) | `0x08001920`, `0x08004120`, `0x08005508` | | `cmp index,#17` special case |
| Descriptions (4) | `0x08396661`, `0x083966AE`, `0x083966FD`, `0x0839674B` | `0x396661`… | embed glyph bytes |
| "Cheats" label | `0x0838E6B4` | `0x38E6B4` | present, unreferenced by the menu |
| BBA kid roster (names) | `0x0812B0C4`…`0x0812B80C` | `0x12B0C4`… | nickname/initials/name records |

### Savestate ↔ RAM mapping (mGBA 0.10.5)

A savestate is a PNG whose `gbAs` chunk is a zlib stream of 397,312 bytes:

```
0x00000–0x19000  VRAM(0x18000) + palette/OAM/IO area
0x19000–0x21000  IWRAM  (0x03000000–0x03007FFF)
0x21000–0x61000  EWRAM  (0x02000000–0x0203FFFF)
```

so `RAM 0x0300xxxx → state 0x19000+xxxx` (the cheat index `0x03003814` is at
state offset `0x1C814`, the buffer `0x030007F0` at `0x197F0`).

## 5. Algorithm

```
letters:  A→'a' B→'b' Select→'s' Start→'t' Right→'r' Left→'l'
          Up→'u' Down→'d' R→'v' L→'m'          (KEYINPUT bits 0x001..0x200)

on the matchup screen, each frame:
    keys = ~KEYINPUT & 0x3FF
    for each of the 10 bits, in the fixed order b,u,d,l,r,m,v,a,t,s:
        if keys & bit and count <= 29:
            buffer[count++] = letter

    best = 0 ; best_pos = buffer_start - 1
    for i in 0..16:                       # 17 entries, stride 10
        p = strstr(buffer, table[i])
        if p and p > best_pos:            # latest match wins
            best_pos = p
            best = i + 1                  # 1-based table position
    *(u8*)0x03003814 = best               # 0 = none
    if best != 0:
        play sound 0x17
        set *(u8*)(0x030031A0+0x69F)=1, +0x6A0=1, +0x6A2=1
        set per-player flags on 3 of 5 players selected by a 5-entry shuffle
    # on leaving the screen:
    *(u8*)0x03003814 = 0 ; *(u8*)0x03000F08 = 0
```

The match is a **substring** test, not a suffix test, and the "latest match
wins" rule means a longer sequence typed after a shorter one supersedes it.
Because the buffer is only 29 bytes and is cleared on screen exit, a code must
be entered in one go on the matchup screen.

There is no checksum, no alphabet table and no generator/encoder pair: the whole
code space is the 17 literal strings. The only per-code data beyond the string
is the index stored at `0x03003814`, which the game-setup code reads
(`0x08001920`, `0x08004120`, `0x08005508`, each comparing it with 17).

## 6. Tables

### 6.1 The 17-entry cheat table (`0x08133E90`, 10 bytes/entry)

| # | Bytes | Letters | Buttons | In ROM description? | In any published list? |
|---|---|---|---|---|---|
| 1 | `uudda` | u u d d a | Up, Up, Down, Down, A | yes — "Hot hands for everyone!" | yes |
| 2 | `dudua` | d u d u a | Down, Up, Down, Up, A | yes — "Super speed for everyone!" | yes |
| 3 | `ssbbt` | s s b b t | Select, Select, B, B, Start | yes — "All dunks." | yes |
| 4 | `uulrba` | u u l r b a | Up, Up, Left, Right, B, A | yes — "Unlimited turbo." | yes |
| 5 | `sbbbba` | s b b b b a | Select, B, B, B, B, A | **no** | **no** |
| 6 | `msvvva` | m s v v v a | L, Select, R, R, R, A | **no** | **no** |
| 7 | `msvvba` | m s v v b a | L, Select, R, R, B, A | no | no |
| 8 | `msvvsa` | m s v v s a | L, Select, R, R, Select, A | no | no |
| 9 | `msvvua` | m s v v u a | L, Select, R, R, Up, A | no | no |
| 10 | `msvvra` | m s v v r a | L, Select, R, R, Right, A | no | no |
| 11 | `msvvda` | m s v v d a | L, Select, R, R, Down, A | no | no |
| 12 | `msvvla` | m s v v l a | L, Select, R, R, Left, A | no | no |
| 13 | `msvvma` | m s v v m a | L, Select, R, R, L, A | no | no |
| 14 | `msvbva` | m s v b v a | L, Select, R, B, R, A | no | no |
| 15 | `msvbba` | m s v b b a | L, Select, R, B, B, A | no | no |
| 16 | `msvbsa` | m s v b s a | L, Select, R, B, Select, A | no | no |
| 17 | `msm` | m s m | L, Select, L | no | no |

Button-glyph codes used in the description strings (0x8F–0x98) decode
consistently with the table: `0x8f`=A, `0x90`=B, `0x95`=Up, `0x96`=Right,
`0x97`=Down, `0x98`=Left. The four descriptions embed their own sequence, e.g.
entry 1's description ends with the bytes `95 20 95 20 97 20 97 20 8f`
("Up, Up, Down, Down, A").

### 6.2 Input alphabet

Ten buttons, recorded as one ASCII letter each. Maximum buffer length 29
(`cmp r2,#0x1d` before every append). No case, no symbols, no numbers — the
alphabet is exactly `{a,b,s,t,r,l,u,d,v,m}`.

## 6b. Enumeration

**Space definition.** The space is a literal table, not a field/checksum format:

* Alphabet: 10 buttons (`A B Select Start Right Left Up Down R L`).
* Lengths in the table: 3 (`msm`) and 5, 6 for the rest.
* No checksum, no reserved bits, no field widths.
* Table size: **17** entries (`0x08133E90`, stride 10). There is no second
  algorithmic format: the only reference to the table is the literal at
  `0x0801EDA8`, and the only comparator is `0x08066940`.

**Novel codes.** The following entries are in the ROM and in no published list.
All were typed on the matchup screen and read back from the game's own index
byte `0x03003814`:

| Sequence | Buttons | Index stored by the ROM | Evidence |
|---|---|---|---|
| `sbbbba` | Select B B B B A | **5** | savestate `0x1C814 = 0x05` |
| `msvvva` | L Select R R R A | **6** | `0x1C814 = 0x06` |
| `msvvba` | L Select R R B A | **7** | `0x1C814 = 0x07` |
| `msvvsa` | L Select R R Select A | **8** | `0x1C814 = 0x08` |
| `msvvua` | L Select R R Up A | **9** | `0x1C814 = 0x09` |
| `msvvra` | L Select R R Right A | **10** | `0x1C814 = 0x0A` |
| `msvvda` | L Select R R Down A | **11** | `0x1C814 = 0x0B` |
| `msvvla` | L Select R R Left A | **12** | `0x1C814 = 0x0C` |
| `msvvma` | L Select R R L A | **13** | `0x1C814 = 0x0D` |
| `msvbva` | L Select R B R A | **14** | `0x1C814 = 0x0E` |
| `msvbba` | L Select R B B A | **15** | `0x1C814 = 0x0F` |
| `msvbsa` | L Select R B Select A | **16** | `0x1C814 = 0x10` |

The index is exactly `table position`, which is the ROM's own verdict that the
sequence was found. A live hardware write watchpoint on `0x03003814` fired at
`0x0801ED90` (`strb r5,[r0]`) the first time `uudda` was completed, proving the
store is the acceptance event and not a coincidental byte.

For a direct in-game view, the game was started with `sbbbba` (index 5) and with
the documented `uudda`; both proceeded through commentary into play normally
(see `g2_c.png`, `y_hot_c.png`). The documented four are additionally described
by the game itself at `0x396661`–`0x3967A0`.

**Bounds proven by rejection.**

| Test | Why it is out of bounds | Observed |
|---|---|---|
| `uuddd` | 5-letter string not in the 17-entry table | index stays 0 |
| `uuuua` | not in table | index stays 0 |
| `msm` | in table but never persists an index (entry 17 is the reset/no-op slot) | index 0 |
| 30+ presses | buffer caps at 29 (`cmp #0x1d`), later presses are dropped | buffer stops at 29 letters |

There is no 18th code: 17 records exist and the game-setup readers special-case
`index == 17` only.

## 7. Validation evidence

**Observed (emulator):**

* Boot, title, main menu (7 items), Extras (4 items: Meet the Players, Unlocked
  Awards, Past Game MVPs, Credits), Game Setup, Select Team (30 NBA teams),
  Select Court, Ball Toss, Player Select (5 picks, one "?" slot), Matchup
  screen, pre-game commentary, in-game HUD. Every entry of every menu was
  opened; no Cheats row and no debug screen exists in any of them.
* All 17 table sequences typed: indices 1…16 stored, `msm` → 0, non-table
  sequences → 0.
* Hardware write watchpoint on `0x03003814` hit at `0x0801ED90` with
  old=0 / new=1 when `uudda` completed.
* The description strings at `0x396661`+ are the only cheat documentation in the
  ROM; they are not reachable from any menu.

**Derived (disassembly):**

* Table, matcher, comparator, recorder, index store/clear (addresses in §4).
* Button→letter mapping from the recorder's `ands` immediates
  (`0x01`→'a', `0x02`→'b', `0x08`→'t', `0x10`→'r', `0x20`→'l', `0x40`→'u',
  `0x80`→'d', `0x100`→'v', `0x200`→'m').
* No password system: zero occurrences of `password`/`passcode` in 4 MiB; no
  name-comparison table for the Coach Sign In path (the only all-caps name
  cluster, `0x12B0C4`+, is the BBA kid roster with nickname/initials/name
  records ending in the real player entries "BARRY"/"DEJAY", "YAO"/"MING", …).

**Inferred:**

* The gameplay meaning of indices 5–16. They are accepted and dispatched through
  the same accept path, and the game-setup readers branch on the index, so they
  are real codes; their per-index effect was not isolated to a single visible
  game rule in this pass (see §8).

## 8. Unknowns

* The exact gameplay effect of table indices 5–16. The accept routine is shared
  and writes per-player flags plus three option bytes at `0x030031A0+0x69F`,
  `+0x6A0`, `+0x6A2`; the index itself is consumed by game-setup code
  (`0x08001920`, `0x08004120`, `0x08005508`) which special-cases 17. Which
  gameplay rule each of 5–16 toggles was not proven here. The documented four
  (1–4) are proven by the game's own description strings and by the published
  lists.
* Why entry 17 (`msm`) is in the table but never persists an index; the most
  economical reading is "reset/cancel slot".
* Whether the unreachable "Cheats" screen (`0x38E6B4` label + four description
  strings) was cut from the Extras menu or hidden behind a second condition. All
  reachable menus were enumerated and it does not appear.

## 9. Tooling

* `Xvfb :155`, `openbox`, `mgba 0.10.5` (SDL), `xdotool`, `scrot`,
  ImageMagick, `arm-none-eabi-objdump` (binutils-arm-none-eabi),
  `gdb-multiarch` (mGBA GDB stub on `:2345`), Python 3 (zlib, struct).
* Scripts (in `/tmp/opencode/bball`): `rsp.py` (GDB-RSP memory client),
  `testcodes.py` / `testflags.py` (drive all 17 sequences via xdotool and read
  the index from savestates), `bounds.py` (negative controls), `hdr.py`,
  `logo.py` (identity/embedded-header scan).
* Savestates used: `Backyard Basketball.ss1` (matchup screen), `.ss3` (scratch).
* Screenshots: `/tmp/opencode/bball/*_c.png` (720×480 crops), notably
  `state1_c.png` (matchup), `g2_c.png` (play after novel code `sbbbba`),
  `y_hot_c.png` (after `uudda`), `m09_c.png` (Extras), `t03_c.png` (main menu).

Legal: no ROM, graphics, music or extracted text is redistributed here; only
hashes, addresses, algorithms and my own console strings.
