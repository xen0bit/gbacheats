# Blackthorne (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Blackthorne/Blackthorne.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`) |
| Header title | `BLACKTHORNE` (space padded) |
| Game code | `AQXE` |
| Maker code | `7D` |
| Software version | `0x00` |
| Entry word | `EA00002E` = ARM `b 0x080000C0` (standard) |
| MD5 | `d0bb79fb5a05702ce8b7d03320fcdf52` |
| SHA-1 | `8f7f8c2051130b881e1fc131360cbc4946a63535` |
| SHA-256 | `2699ea8f2848dc41a5a22dd2ed236c3b8502fad04f9aff0b7e39cc898ef27db8` |

Published identity: *Blackthorne* (USA), GBA, Blizzard Classic Arcade /
Mass Media, 2003, AGB-AQXE-USA. The ROM self-identifies as a Mass Media
conversion (purple-elephant "mass media" splash, then "Blizzard Classic
Arcade").

**Header anomalies (Phase 0 note).** The Nintendo logo is intact and appears
exactly once (`0x04`, i.e. one game header — not a multi-game cart). The
header complement byte at `0xBD` is `0x7A`, but the value computed over
`0xA0..0xBC` is `0x93`; the header-checksum field at `0xBE` is `0x0000`
while the correct checksum for this header is `0x7A`. In other words,
`0xBD` holds the *checksum* value and `0xBE` holds zero: the 16-byte header
tail was rewritten by a tool after the ROM was built. The entry branch, logo,
game code and header title are standard; no trainer/injected entry code, no
intro/credits strings from a release group, and the ROM boots and plays
normally. Treat this as a **repacked header**, not a content patch.

Save hardware: `EEPROM_V122` string at file `0x44A78`; the game creates a
512-byte EEPROM image (`Blackthorne.sav`) with a `0xBEEF` magic.

## 2. Executive summary

The GBA port has **no text password entry**. This is the same design decision
Mass Media used for the GBA *The Lost Vikings*: the SNES passwords are still
in the ROM, but the player cannot type them. The port has:

1. **A hidden 8-button level-select code** — the only player-entered cheat:

   > On the **LOAD GAME** save-slot screen press
   > **Left, Left, R, R, Up, Up, Down, Select**.

   A sound effect (id `0xCC`) is requested, `0x030022DC` (level-select
   unlocked) is set to 1, and `0x030022DD` (a dormant god-mode flag) is
   cleared to 0. After that, pressing **Left/Right on the sixth (bottom)
   save-slot row** cycles through 17 level labels, from `MINE   00%` to
   `CASTLE 96%`. **A** on that row asks `ARE YOU SURE?`; answering **YES**
   writes a save for the chosen level and starts it.

2. **A 17-entry level/password table that is live, not dead.** The four-character
   SNES passwords (`DBQ7`, `FBWC`, … `K3CH`) are stored in EEPROM saves
   (byte-reversed, e.g. `37 51 42 44` = `DBQ7`) and are decoded at load time
   by a 17-entry pointer table to select the level. The hidden level select
   *writes* those codes into the save. So the passwords are unused as typed
   passwords but are used as save progress codes (this corrects the common
   "unused text" description).

3. **No implementation of the three "title screen" codes** that several cheat
   sites list for GBA (`Infinite Health` = Left,Right,Down,Up,B,B,Down;
   `Invisibility` = B,Down,Right,Down,Up,Up,Left,B,Up; `Never die from falling`
   = B,B,Up,Left,Down,Right,Right,Up). Those are SNES/DOS codes. An exhaustive
   scan for contiguous runs of the 10 button-mask values finds only the
   canonical `1,2,4,…,0x200` shift table and the single 8-press level-select
   code at length ≥ 6; there is no 7-press or 9-press table and no other
   key-sequence matcher.

4. **A disabled god-mode flag.** `0x030022DD`, when non-zero, makes the input
   routine copy the "max health" byte (`0x0300021E`) into health
   (`0x03000FC8`) every frame. It has exactly one writer in the whole ROM —
   the level-select code above, which **clears** it. No ROM code ever sets it,
   so the cheat is dead in this port.

5. The **EU-only developer-photo code** (Left,Right,Up,Down,Left,Right,Select,
   Select) does nothing in this US ROM, as expected from TCRF.

The hidden level select itself is documented (TCRF, GameFAQs). What is new in
this report is the complete internal model: the mask table address, the two
flags, the exact screen/row gating, the full index → level → save-code
mapping, and proof that the SNES password strings are live save data.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba`), Xvfb `:186` 1024×768,
`SDL_AUDIODRIVER=dummy`, Openbox as WM. Screenshots: `import -window root`
then crop the 720×480 client area.

Keymap used (mGBA SDL defaults): **A = `x`, B = `z`, L = `a`, R = `s`,
Start = `Return`, Select = `BackSpace`, D-pad = arrows**. Hold keys
100–220 ms; the front end samples `KEYINPUT` once per frame and derives a
one-frame "pressed" mask, so a held key produces exactly one press.

Exact menu path:

```
Boot → Mass Media splash → Blizzard Classic Arcade logo → MAIN MENU
  PRACTICE
  NEW GAME
  LOAD GAME     <-- hidden code goes here
  OPTIONS
```

1. From `MAIN MENU`, choose **LOAD GAME** (Down, Down, A).
2. Wait for `SELECT SAVE GAME SLOT` to finish drawing.
3. Press, one at a time: **Left, Left, R, R, Up, Up, Down, Select**
   (`s`, `s`, arrows, `BackSpace` on this keymap).
4. The cursor will be somewhere in the slot list. Move with Up/Down to the
   **sixth** row (the last row above `EXIT`).
5. Press **Left** or **Right**: the row now shows a level label
   (`CASTLE 96%`, `CASTLE 90%`, … `MINE   00%`).
6. **A** → `ARE YOU SURE?` → **YES** (`A`) starts that level and creates a
   save in that slot.

Any *other* button press resets the sequence matcher to position 0, so a
failed attempt can simply be retried on the same screen (this is also how the
wrong-button rejection test below was made).

Codes tested (see §7 for results):

| Input | Where | Result |
|---|---|---|
| `L,L,R,R,U,U,D,Select` | LOAD GAME slot screen | accepted; level select on row 6 |
| `L,L,R,R,U,U,D,L` | LOAD GAME slot screen | rejected (no level select) |
| `L,L,R,R,U,U,D,Select` | NEW GAME slot screen | no effect |
| `L,R,U,D,L,R,Select,Select` (EU photo) | LOAD GAME slot screen | no effect |
| `L,R,D,U,B,B,D` (published "infinite health") | MAIN MENU | no effect; only moves cursor |
| any 4-char code | — | no entry UI exists (§6b.3) |

Published code lists consulted: TCRF *Blackthorne (GBA)* (level select,
developer photo, "unused text"); GameFAQs cheat pages for GBA/SNES/32X;
StrategyWiki `Blackthorne/Passwords`. All are matched against the ROM in §6.

Reconnaissance summary (Phase 1):

* 24,710 `strings -n 4` lines. Keyword hits: `PASSWORD`/`password`/`CHEAT`/
  `DEBUG`/`SECRET`/`UNLOCK`/`CODE` = **0**; `LEVEL` = 1 (credits, "LEVEL
  DESIGN" at `0x27CC7`); `SOUND` = 2 (OPTIONS label at `0x2717B`, credits at
  `0x27E34`); `CONTINUE` = 1 (`0x282A9`, in-game prompt); `OPTION` = 1
  (`0x25D91`). So there is no English password/cheat UI text to find; the
  feature is entirely button-driven.
* Literal verification of every published code: all 16 StrategyWiki level
  passwords are present byte-for-byte in the 17-entry table at `0x44600`;
  `FMWY` is present only in the master table at `0x22D08`. The GameFAQs PC
  password list contains one typo — `Y4OJ` where the ROM has `Y4DJ` — which
  the ROM table settles. No other published code is wrong for this ROM.
* Key-mask search: an exhaustive scan of 16-bit windows over the whole ROM for
  maximal runs of the 10 button masks (values `1,2,4,…,0x200`) plus the
  active-low complements found exactly two runs: the canonical shift table at
  `0x1FEA4` and the 8-entry code at `0x46FE4`. This is the basis for the
  "no title-screen codes" negative in §2/§6b.

## 4. Address map

File offset = ROM address − `0x08000000`. All disassembly verified with
Capstone (Thumb) and `arm-none-eabi-objdump`.

### ROM data

| ROM address | File off | Contents |
|---|---|---|
| `0x08046FE4` | `0x46FE4` | **8 × u16 button-mask table** (the hidden code): `20 20 100 100 40 40 80 04` |
| `0x08044534` | `0x44534` | 17 progress-name strings, 12-byte stride, level 17 → 1 (`CASTLE 96%` … `MINE   00%`) |
| `0x08044600` | `0x44600` | 17 four-char codes, 8-byte stride, level 17 → 1 (`K3CH` … `DBQ7`) |
| `0x08046FF8` | `0x46FF8` | 17 name pointers (ascending into reversed list) |
| `0x0804703C` | `0x4703C` | 17 code pointers |
| `0x08022C36` | `0x22C36` | master password table, 23 × 10 bytes: `char code[4]; u16 id; u16 x; u16 y` |
| `0x080000C0` | `0xC0` | ARM entry / init (branch target of the header word) — Thumb front end follows |
| `0x08044A78` | `0x44A78` | `EEPROM_V122` string (save library) |

### Front-end code (Thumb)

| Address | Role |
|---|---|
| `0x08000D04` | front-end frame loop: reads `KEYINPUT`, dispatches state |
| `0x08000D2A`–`0x08000D66` | `held = ~KEYINPUT & 0x3FF` → `0x02022A36`; `pressed = held & ~prev` → `0x02022A38` |
| `0x08000DA4` | state jump table (states 0–6): `0D4A, 0D4A, 0DC0, 0E94, 10FC, 14B4, 15A4` |
| `0x08000DC0` | state 2 — MAIN MENU |
| `0x08000E94` | state 3 — save-slot screen reached from **NEW GAME** |
| `0x080010FC` | state 4 — save-slot screen reached from **LOAD GAME** |
| `0x08001244` | state 4 init; `bl 0x08001D28` (sequence checker) |
| `0x08001392`–`0x080013E8` | hidden level-select handler (Left/Right) |
| `0x080014B4` | state 5 — decode 4-char code against the 17-entry table |
| `0x080015A4` | state 6 — confirm / write save / start level |
| `0x08001D28` | **8-press sequence checker** |
| `0x080003F4` | input routine + dormant god-mode code (`0x08000410`) |

### RAM (IWRAM / EWRAM)

| Address | Meaning |
|---|---|
| `0x02022A24` | menu state (`u32`) |
| `0x02022A28` | cursor / item index |
| `0x02022A36 / 38` | held / pressed button masks (active-high, 10 bits) |
| `0x030022C4` | text tilemap base pointer |
| `0x030022C8` | **level index 0…16** (hidden select) |
| `0x030022CA` | sequence position (0…7) |
| `0x030022CC` | **8 × u16 expected masks** (runtime copy of `0x08046FE4`) |
| `0x030022DC` | **level-select unlocked** (0/1) |
| `0x030022DD` | dormant god-mode flag (read by `0x08000410`) |
| `0x030022E0` | 17 name pointers (runtime) |
| `0x03002324` | 17 code pointers (runtime) |
| `0x03002368` | level record table; `+0x0C` = level id (u16) |
| `0x0300037E`, `0x03000380`, `0x03000382`, `0x03000384` | four decoded code characters (u16 cells) |
| `0x03000FC8` | player health byte (cf. CodeBreaker `33000FC8 000C`) |
| `0x0300021E` | max-health byte copied into health when god flag ≠ 0 |
| `0x03005638` | in-game key state (ARM engine) |

EEPROM (512-byte image) slot record, observed for slot 1:

```
00: 1c 03        level/map id (0x031C)
06: ef be        magic 0xBEEF
08: "0   ENIM"   progress name, 8-byte groups stored reversed ("MINE   0")
16: "%0"         remainder of "00%"
1c: 37 51 42 44  code stored reversed: "DBQ7"
```

Slot 6's record sits at `0xB8` in the image; the `SAND   66%` selection wrote
`44 4e 41 53 32 03 00 00 00 00 25 36 36 20 20 20 4a 44 34 59`
(`"DNAS"`, id `0x0332`, `"%66 "`, `"JD4Y"` = reversed `Y4DJ`).

## 5. Algorithm

### 5.1 Front-end input

Once per frame:

```
held    = (~KEYINPUT) & 0x03FF          ; bit0 A=1, B=2, Select=4, Start=8,
                                       ; Right=0x10, Left=0x20, Up=0x40, Down=0x80,
                                       ; R=0x100, L=0x200
pressed = held & ~prev_held
prev_held = held
```

`KEYINPUT` is the active-low register at `0x04000130`.

### 5.2 The hidden 8-press code (`0x08001D28`)

```
seq[8] = {0x0020, 0x0020, 0x0100, 0x0100, 0x0040, 0x0040, 0x0080, 0x0004}
                       ;  Left  Left    R      R      Up     Up    Down Select
pos = *(u8*)0x030022CA
for each frame:
    if (pressed & seq[pos]) != 0:
        pos++
        if pos == 8:
            *(u8*)0x030022DC = 1        ; unlock level select
            *(u8*)0x030022DD = 0        ; clear (disable) dormant god mode
            pos = 0
            sound_request(0xCC)         ; 0x08000980, explosion SFX
    else if pressed != 0:
        pos = 0                          ; any wrong press resets the matcher
    *(u8*)0x030022CA = pos
```

Notes:

* Only the *pressed* edge counts, so holding a button is one press.
* The matcher is not tick-based; it waits indefinitely between correct presses.
* Because a wrong press resets to 0, the code may be attempted repeatedly on
  the same screen.
* Called from the state-4 init path (`0x08001244`) — i.e. the screen opened by
  **LOAD GAME**. The identical-looking screen opened by **NEW GAME** (state 3)
  never calls it.

### 5.3 Hidden level select (`0x08001392`)

```
if *(u8*)0x030022DC == 0:        goto normal_navigation
if item_id(cursor) != 5:         goto normal_navigation   ; 5 = sixth row
if LEFT pressed:
    idx = idx - 1;  if idx < 0:  idx = 0x10
if RIGHT pressed:
    idx = idx + 1;  if idx > 0x10: idx = 0
draw_string(names[idx])           ; name table 0x030022E0
```

`idx` is `0x030022C8`; the valid range is exactly `0…0x10` (17 levels).

### 5.4 Confirmation, save write and level start

* **A/Start** on the selected row: if the item is `EXIT` (id 6) leave; if the
  row is empty the game beeps; otherwise show `ARE YOU SURE?` (or
  `OLD DATA WILL BE LOST!` if the slot holds data).
* **YES**: build the save record from the table for the selected level —
  the progress name (`MINE   00%` … `CASTLE 96%`), the four-char SNES password
  (`DBQ7` … `K3CH`), a `u16` level id — and write it to the selected EEPROM
  slot. The level id comes from the runtime record table at `0x03002368`
  (record size `0x10`, field `+0x0C`), selected by the slot/level index, then
  the level is started (`0x080016F2`).

### 5.5 Loading a save (no password UI)

`0x080014B4` (state 5) takes four characters from the selected slot and
compares them, element by element, against the 17 code strings whose pointers
live at `0x03002324`:

```
for i in 0..16:
    p = code_ptr[i]
    if buf[0]==p[0] && buf[1]==p[1] && buf[2]==p[2] && buf[3]==p[3]:
        selected_index = i; break
```

The index is then used exactly as in §5.4. There is no keyboard, no character
picker and no buffer that the player can edit: the four characters always come
from the save record. This is why the SNES passwords are "unused as input, but
live as data".

## 6. Tables

### 6.1 The hidden code

`0x08046FE4`: `0020 0020 0100 0100 0040 0040 0080 0004`
= **Left, Left, R, R, Up, Up, Down, Select**.

### 6.2 Runtime index → level → save code

`idx` is the value shown in the sixth save-slot row after the code; selecting
it starts that level and writes that name/code into the slot.

| idx | Level | Save label | Save code | Master-table id |
|---:|---:|---|---|---|
| 0 | 1 | `MINE   00%` | `DBQ7` | `0x86` |
| 1 | 2 | `MINE   06%` | `FBWC` | `0x87` |
| 2 | 3 | `MINE   12%` | `QP7R` | `0x88` |
| 3 | 4 | `MINE   18%` | `WJTV` | `0x95` |
| 4 | 5 | `TREE   24%` | `RRYB` | `0x96` |
| 5 | 6 | `TREE   30%` | `ZS9P` | `0x97` |
| 6 | 7 | `TREE   36%` | `XJSN` | `0x98` |
| 7 | 8 | `TREE   42%` | `CGDM` | `0xA8` |
| 8 | 9 | `SAND   48%` | `TJ1F` | `0xA9` |
| 9 | 10 | `SAND   54%` | `GSG3` | `0xAA` |
| 10 | 11 | `SAND   60%` | `BMHS` | `0xAB` |
| 11 | 12 | `SAND   66%` | `Y4DJ` | `0xC1` |
| 12 | 13 | `CASTLE 72%` | `HCKD` | `0xC2` |
| 13 | 14 | `CASTLE 78%` | `NRLF` | `0xC3` |
| 14 | 15 | `CASTLE 84%` | `J6BZ` | `0xC4` |
| 15 | 16 | `CASTLE 90%` | `MJXG` | `0xC5` |
| 16 | 17 | `CASTLE 96%` | `K3CH` | `0x89` |

These 17 codes are the level-2 … level-17 passwords published on StrategyWiki
for the original game, plus `DBQ7` for level 1 (the PC password list gives
`DBQ7` as "level 1 without intro"); `FMWY` ("ending") exists only in the
master table, not in the 17-entry selector table. The hidden level select is
the mechanism that makes these passwords appear inside GBA saves.

### 6.3 Master password table (`0x08022C36`, 23 × 10 bytes)

| # | Code | id | x | y | note |
|---:|---|---:|---:|---:|---|
| 0 | `SJ5Z` | `0x85` | `0x218` | `0x22C` | training level (PRACTICE) |
| 1 | `DBQ7` | `0x86` | `0x568` | `0x0CC` | level 1, no intro |
| 2 | `FBWC` | `0x87` | `0x748` | `0x1AC` | |
| 3 | `QP7R` | `0x88` | `0x6C8` | `0x1AC` | |
| 4 | `WJTV` | `0x95` | `0x068` | `0x06C` | |
| 5 | `RRYB` | `0x96` | `0x0B8` | `0x35C` | |
| 6 | `ZS9P` | `0x97` | `0x088` | `0x35C` | |
| 7 | `XJSN` | `0x98` | `0x068` | `0x27C` | |
| 8 | `CGDM` | `0xA8` | `0x048` | `0x14C` | |
| 9 | `TJ1F` | `0xA9` | `0x8C8` | `0x28C` | |
| 10 | `GSG3` | `0xAA` | `0x528` | `0x28C` | |
| 11 | `BMHS` | `0xAB` | `0x2B8` | `0x36C` | |
| 12 | `Y4DJ` | `0xC1` | `0x4A8` | `0x31C` | |
| 13 | `HCKD` | `0xC2` | `0x028` | `0x36C` | |
| 14 | `NRLF` | `0xC3` | `0x038` | `0x36C` | |
| 15 | `J6BZ` | `0xC4` | `0x4C8` | `0x36C` | |
| 16 | `MJXG` | `0xC5` | `0x128` | `0x09C` | |
| 17 | `K3CH` | `0x89` | `0x080` | `0x080` | level 17, also in the 17-entry table |
| 18 | `L8VJ` | `0x9A` | `0x080` | `0x080` | not in the 17-entry table |
| 19 | `PBKT` | `0xB3` | `0x080` | `0x080` | not in the 17-entry table |
| 20 | `TNLQ` | `0xFE` | `0x080` | `0x080` | not in the 17-entry table |
| 21 | `FMWY` | `0x3F` | `0x080` | `0x080` | "ending" in the original |
| 22 | `L2RP` | `0xFFFF` | `0x086` | `0x096` | sentinel / end |

Only entries 0–16 are reachable through the GBA level select. Entries 18–22
are not decoded by the GBA loader at all: its table (`0x03002324`) has 17
entries, and the selector clamps to `0…16`.

### 6.4 Save record (observed)

```
+0x00 u16  level/map id        e.g. 0x031C (level 1), 0x032C (level 9), 0x0332 (level 12)
+0x06 u16  0xBEEF magic        (present in the slot-1 record)
+0x08 char progress name[?]    stored in reversed 8-byte groups ("0   ENIM" = "MINE   0")
+0x1C char code[4]             stored byte-reversed ("7QBD" = "DBQ7")
```

Slot-6 record lives at image offset `0xB8`. After selecting `SAND   66%`
(index 11) and confirming, it contained `DNAS` (`SAND`), id `0x0332`,
`%66`, `JD4Y` (`Y4DJ`).

## 6b. Enumeration

### 6b.1 Space 1 — the button code

* Alphabet: the 10 GBA buttons; sequence length **exactly 8**.
* Representable input strings: `10^8 = 100,000,000`.
* Accepted strings: **1** (`Left, Left, R, R, Up, Up, Down, Select`), because
  the matcher compares against one fixed 8-entry table (`0x08046FE4`) and
  resets on any mismatch.
* Action branches: **1** — writes `0x030022DC = 1`, `0x030022DD = 0`, requests
  SFX `0xCC`, resets the position.
* Bounds by rejection (observed): the same 8 presses with **L** instead of
  **Select** as the 8th button produce no level select
  (`screenshots/10_reject_wrong_button.png`).
* Screen gating (observed): the same correct code on the **NEW GAME**
  save-slot screen produces no level select
  (`screenshots/11_reject_newgame_screen.png`); only the **LOAD GAME** screen
  calls the matcher.
* The sequence need not be entered blind and can be retried: any wrong press
  resets position 0 (derived from `0x08001D7E`, observed while testing).

### 6b.2 Space 2 — the hidden level selector

* Values: `idx ∈ {0,…,16}` — 17 representable levels; clamp code branches
  `idx<0→16` (`0x080013C0`) and `idx>16→0` (`0x080013E0`).
* Enumeration (derived from `0x08044534`/`0x08044600`, §6.2): all 17
  name/code pairs listed above.
* In-game proof of four distinct values plus one cold-boot decode:

| Test | Index | Display | Result |
|---|---:|---|---|
| `Left` at 0 | 16 | `CASTLE 96%` | starts level 17 (Sarlac throne room, `AT LAST WE MEET, WHELP…`) — `screenshots/13_level17_sarlac.png` |
| `Right`×2 | 2 | `MINE   12%` | starts level 3 (Mines, different shaft) — `screenshots/16_level3_mine12.png` |
| `Right`×11 | 11 | `SAND   66%` | starts level 12 (Wastelands) — `screenshots/14_level12_sand66.png` |
| `Right`×8 | 8 | `SAND   48%` | starts level 9 (Wastelands) — `screenshots/15_level9_sand48.png` |

* **Novel/unpublished composite code** (not documented in any list we found —
  GameFAQs, TCRF, VGChartz or StrategyWiki): the selector index enumeration is
  not published anywhere, and neither is the save write. Execute
  **`L,L,R,R,U,U,D,Select` → `Right`×11 → `A` → `A`** on the LOAD GAME screen.
  The game starts level 12 **and writes `Y4DJ` into the sixth EEPROM slot**;
  the slot label becomes `SAND   66%` (`screenshots/14_level12_sand66.png`).
  A cold boot (fresh IWRAM, no code entered) with that slot loads level 12
  again, proving the 4-char code is *live data* decoded by the game
  (`screenshots/14_level12_sand66.png`, save dump in §6.4).
* Bounds by rejection: the selector is inert until the flags are set, inert on
  rows other than the sixth, and wraps rather than overflowing at both ends
  (`screenshots/09_wrap_left_to_castle96.png` = `Left` from 0;
  `screenshots/08_wrap_right_to_mine00.png` = `Right` from 16).

### 6b.3 Space 3 — typed passwords

* **Zero.** The port has no password-entry screen. Evidence:
  * Screen enumeration (§7): every reachable front-end screen was walked;
    only MAIN MENU, save-slot select (NEW/LOAD), OPTIONS and the in-game
    pause/inventory exist.
  * String search: `PASSWORD`/`password`/`CHEAT`/`DEBUG`/`SECRET`/`CODE`/
    `UNLOCK` = **0 hits** in 4 MiB (24,710 ASCII strings ≥4 chars).
  * The only code that touches 4-character input (`0x080014B4`) reads the
    four characters from the selected save record; no code writes that buffer
    from a keyboard.
* The 4-character alphabet of the 23-entry table is a fixed literal set, not a
  checksum format: none of the entries use `A,E,I,O,U` and none use `0` or
  `8`. Because the codes are stored as complete strings that are compared
  character-for-character, there is no generator/validator pair to enumerate
  and no field/checksum structure to reverse.

## 7. Validation evidence

### Observed (emulator, `:186`)

* Boot: Mass Media splash, Blizzard Classic Arcade logo, MAIN MENU.
* Main menu items, OPTIONS (MUSIC/SOUND/EXIT), LOAD GAME slot list
  (6 slots + EXIT, labels `MINE   00%`/`NO DATA`).
* The hidden code on LOAD GAME enables the selector on row 6
  (`screenshots/04_load_slots_before_code.png` before, `screenshots/07_code_accepted_castle96.png`
  after the code + one `Left`).
* Wrong 8th button → no selector (`screenshots/10_reject_wrong_button.png`).
* Correct code on NEW GAME screen → no selector
  (`screenshots/11_reject_newgame_screen.png`).
* EU developer-photo code on a fresh boot → no effect in the US ROM
  (`screenshots/17_reject_eu_photo.png`; row 6 still shows the save label after `Left`).
* Published "infinite health" sequence at MAIN MENU → no effect (only cursor
  movement; `screenshots/18_published_health_code_at_menu.png` is the menu
  immediately after the input).
* Level start from the selector at indices 16, 11, 8, 2 → levels 17, 12, 9, 3
  (`screenshots/13_level17_sarlac.png`, `screenshots/14_level12_sand66.png`,
  `screenshots/15_level9_sand48.png`, `screenshots/16_level3_mine12.png`).
* `ARE YOU SURE?` dialog on A (`screenshots/12_confirm.png`).
* EEPROM after selecting `SAND   66%` contains `DNAS … 4A 44 34 59`
  (`Y4DJ` reversed) and the cold boot with that save starts level 12.
* In-game pause overlay is a single `GIVE UP?  YES/NO` prompt
  (`screenshots/06_pause_giveup.png`); SELECT opens the inventory panel.

### Derived (from the ROM bytes / disassembly)

* Button-mask table at `0x08046FE4`; checker at `0x08001D28`; call site
  `0x08001244` (state 4 = LOAD GAME slot screen).
* Level-select handler `0x08001392`, clamp values, row-id check `== 5`, name
  draw from `0x030022E0`.
* 17-entry decode loop `0x080014B4`; level-record lookup at `0x080016F2`
  (`0x03002368`, record size `0x10`, field `+0xC`, indexed by the selection).
* Dormant god mode: `0x08000410` copies `0x0300021E` → `0x03000FC8` when
  `0x030022DD != 0`; the only writer in the ROM (`0x08001D56`) stores **0**.
  (`0x03000FC8` is the health byte — cf. CodeBreaker `33000FC8 000C`; that
  `0x0300021E` holds max health is **inferred**.)
* Exhaustive mask-run scan (maximal runs of `1,2,4,…,0x200` values, whole
  ROM): the only runs of length ≥ 6 are `0x08046FE4` (8×u16) and the canonical
  shift table `0x0801FEA4` (10×u16); no 7- or 9-press sequence table.
* Header tail rewritten (`0xBD` = checksum value `0x7A`, `0xBE` = 0).

### Inferred

* The `0xCC` sound is the "explosion" reported by TCRF/GameFAQs (audio was
  run with `SDL_AUDIODRIVER=dummy`; only the request call was observed).
* `0x030022DD` is a god-mode toggle from the original engine (health refill
  each frame) whose enabling path was removed/disabled during the conversion.
* Level ids `0x031C/0x032C/0x0332` are map/level identifiers; their exact
  numbering scheme is not needed for reproduction.
* Slot-6 EEPROM offset `0xB8` is the sixth 40-byte record; the exact record
  stride/ordering is only partially mapped (only the used fields are
  documented above).

## 8. Unknowns

* The exact EEPROM record stride and header/`0xBEEF` placement for slots
  2–6 (only the fields used by the game were identified).
* Why the `0x030022DD` god flag was left in the input routine with no writer:
  dead code from the original engine, or a disabled conversion-time cheat.
* Whether the extra master-table codes (`SJ5Z`, `L8VJ`, `PBKT`, `TNLQ`,
  `FMWY`, `L2RP`) are reachable in any other GBA build/mode. In this US ROM
  the decoder table has 17 entries and the selector clamps to 16, so they are
  not reachable.
* The EU developer-photo asset is absent/unreferenced in this US ROM (TCRF
  says EU-only); the exact EU code path was not analysed here.

## 9. Tooling

* `mGBA 0.10.5` (SDL), `Xvfb :186`, `openbox`, `xdotool`, `scrot`/ImageMagick
  `import`.
* `capstone` 5.0.7 + a small Thumb literal annotator
  (`tools/gbadis.py`), `arm-none-eabi-objdump` (`-M force-thumb` /
  `-M force-arm`) for cross-checks.
* `blackthorne_tables.py` (next to this report) regenerates every table in §6
  from the ROM; run `python3 blackthorne_tables.py Blackthorne.gba`.
* Screenshots in `screenshots/` (720×480 client-area crops).
* Emulator save (`Blackthorne.sav`) is a generated artifact and is git-ignored.

## 10. Legal note

No ROM, graphics, music or text assets are redistributed here. The report
contains addresses, algorithms, short menu strings and screenshots used as
evidence. The ROM analysed is the one whose SHA-256 is given in §1.
