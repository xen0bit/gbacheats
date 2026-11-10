# CT Special Forces 2: Back in the Trenches (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-11-09.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/CT Special Forces 2: Back in the Trenches/CT Special Forces 2: Back in the Trenches.gba` |
| Size | 8 MiB (`0x800000`) |
| Header title | `CT SPECIAL F` |
| Game code | `A9CE` |
| Maker code | `FL` |
| Main unit / device | `0` / `0` |
| Software version | `0` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Fixed byte `0xB2` | `0x96` (valid) |
| Complement check | stored `0x9F`, computed `0x9F` (valid) |
| Header checksum | stored `0x0000`, computed `0xCD45` (zeroed) |
| MD5 | `a827b6305c196589c0fa6ed2f9ec0e3b` |
| SHA-1 | `cedca3aac39309dc122909d11457e306c81e16be` |
| SHA-256 | `f568e20eb32a050c2d7f4f62b077a5728c3c5987c54efe0d4c2b83e0bed0e37c` |

ROM addresses below are `0x08000000 + file_offset`. Nintendo-logo scan over the
whole 8 MiB finds exactly one GBA header (at file `0x0`), so this is a single
game image, not a multi-game pack.

**Patch/trainer check.** The entry branch is the stock crt0 branch, the Nintendo
logo is intact, the image is exactly 8 MiB with no appended payload, and the
`strings` scan finds no cracktro/trainer banner (Mode7, SUNHORS, "CRC BANDIT",
etc.). The only header anomaly is the zeroed header-checksum field (`0x0000`
instead of `0xCD45`; the complement byte is still correct), which is the normal
artifact of a header rebuild/trim tool. No code-level patch was observed.
GameHacking.org lists this serial as `AGB-A9CE-USA`, so the game code is the
retail one.

---

## 2. Executive summary

The GBA SKU has **one** code surface: a 4-digit **password screen** reachable
from the main menu. It is a closed **lookup table**, not a checksum/field format:

* The ROM contains a **250-record table** of 4 decimal digits at ROM
  `0x087D8618` (file `0x7D8618`), record size 4 bytes, one digit per byte
  (`d1 d2 d3 d4`).
* On Confirm, the game linearly searches the table (indices `0..249`) for an
  exact 4-digit match (`0x080022B0`). If no record matches → reject.
* A matched index `i` is split as **`level = i / 10`, `lives = i % 10`** and
  written to `0x0300000C` (u32) and `0x0300314C` (u16). `0x0300314C` is the
  lives counter (independently visible in the published AR MAX code
  `0030314C 00000009`).
* A range check (`0x080009AC`) then rejects any match with **`level > 21`**
  (`cmp #21; bhi reject`). Therefore the reachable set is exactly
  **indices 0–219 = 220 codes**; entries 220–249 (levels 22–24) are present in
  the ROM but **dead**.

Consequences:

* Public lists are correct but incomplete: 51 distinct published codes all
  appear in the table (26 GBA-list, 14 "PS"-list, 14 wiki-list codes; the lists
  overlap), and **169 accepted codes are in no published list**.
* The published "PS" codes are **not** PS-only. `0024` was entered on the GBA
  screen and accepted (`CONNECTED`), setting level 8 / lives 3. The GBA and PS
  published lists draw from the same 250-entry table.
* The "nine lives" variants in the GameFAQs list are simply the `lives = 9`
  column (indices ending in 9); other lives values are reachable and
  undocumented.
* Two novel codes were minted and confirmed in mGBA:
  **`7938`** (index 9 → internal level 0, lives 9: the helicopter prologue
  mission, absent from every published list) and **`4711`** (index 18 →
  level 1, lives 8: the same first stage as `1431` but with 8 lives). Bounds
  were proven by rejecting **`5461`** (a real table record, index 220, level 22
  → out of range) and **`0865`** (not in the table at all).

No debug menu, button code, or hidden menu was found. All menu screens were
walked and are listed in §6b.

---

## 3. How to reproduce

### Emulator

```bash
sudo apt-get install -y mgba-sdl xvfb xdotool scrot imagemagick
Xvfb :220 -screen 0 1280x960x24 &
DISPLAY=:220 openbox &
DISPLAY=:220 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 \
  "CT Special Forces 2: Back in the Trenches.gba" &
```

Default mGBA SDL keymap used: **A = `x`, B = `z`, Start = `Return`,
Select = `BackSpace`, D-pad = arrows**. Hold 50–120 ms per press; the digit
wheels need discrete presses (holding auto-repeats).

### Menu path (observed)

```
Boot logos (LSP, LSP Dev Team)
└─ Language select (English/Français/Deutsch/Español/Italiano/Nederlands)
   └─ Title ("Press Start")
      └─ Story intro (text pages; A advances)
         └─ Main menu
            ├─ Mission    → story intro → world map → briefing → gameplay
            ├─ Challenge  → link-cable "Waiting Room" (Player 1 / Player 2)
            ├─ Password   → 4-digit wheel screen  ← the code system
            └─ Options    → Music, SFX, Tutorial ON/OFF, Difficulty, Credits
```

At the password screen: **Up/Down** change the selected digit (`0-9`, wrapping),
**Left/Right** move between the four digit boxes (wrapping), **A = Confirm**,
**B = Quit** (returns to the main menu). On a valid code the screen changes to
the `CONNECTED` briefing and the level starts; on an invalid code the screen
stays and a **red X** appears in the lower-right corner.

In-game **Start** opens the pause screen: `PAUSE`, **A Resume**, **B Quit**;
B then opens `QUIT / Are you sure?` with **A No / B Yes**.

### Exact tests performed

| Input | Result (observed) |
|---|---|
| `1431` (published, GBA list) | accepted → `CONNECTED` briefing → first stage |
| `0024` (published, labelled "PS") | accepted → `CONNECTED`, level 8 / lives 3 |
| `4711` (**novel**) | accepted → `CONNECTED`, level 1 / lives 8, first stage |
| `7938` (**novel**) | accepted → `CONNECTED`, level 0 / lives 9, helicopter prologue |
| `5461` (table entry, level 22) | rejected, red X |
| `0865` (not in table) | rejected, red X |

Evidence screenshots are stored next to this report as
`CT Special Forces 2 - *.png` (title, main menu, options, pause, password
screen, entered codes, accepted `CONNECTED` screens, the level-0 helicopter
mission, and both red-X rejections).

---

## 4. Address map

| Item | ROM address | File offset | Notes |
|---|---:|---:|---|
| Password table (250 × 4 bytes) | `0x087D8618` | `0x7D8618` | 4 decimal digit bytes per record, order `d1 d2 d3 d4` |
| Table-search / validator | `0x080022B0` | `0x22B0` | linear search `i = 0..249`; returns index or `-1` |
| Range check / state write | `0x080009AC` | `0x9AC` | `if (level > 21) return 0`; writes level + lives |
| Password screen confirm branch | `0x08001F00`–`0x08001F72` | `0x1F00` | reads A/B and digit wheels; calls `0x080022B0` |
| Password screen update fn | `0x08001EA8` | `0x1EA8` | contains the confirm branch |
| Digit-widget construction | `0x08001D90`–`0x08001E6E` | `0x1D90` | builds four 0x34-byte widgets |
| Main loop / input | `0x08025ECC`, `0x0802E570` | `0x25ECC`, `0x2E570` | `0x0802E5BC` reads `KEYINPUT` |
| Level-sequence walker | `0x080009D4` | `0x9D4` | 16-byte level records at `0x087D7DAC`, bound `cmp #22` |
| Table pointer global | RAM `0x030030AC` | — | points to `0x020099C8` while the password screen is loaded |
| Digit 1 field | `0x020099F2` | — | = `[0x030030AC] + 0x2A`, u16 |
| Digit 2 field | `0x02009A26` | — | base `+ 0x5E`, u16 |
| Digit 3 field | `0x02009A5A` | — | base `+ 0x92`, u16 |
| Digit 4 field | `0x02009A8E` | — | base `+ 0xC6`, u16 |
| Level output | RAM `0x0300000C` | — | u32, `i / 10` |
| Lives output | RAM `0x0300314C` | — | u16, `i % 10` (AR MAX `0030314C`) |
| Full index output | RAM `0x03004284` / `0x03004286` | — | u16 pair, both = `i` |
| Key-state word | RAM `0x030042D4` | — | read by the confirm branch |
| Key-state word 2 | RAM `0x030042D6` | — | combined with `0x030042D4` by the confirm branch to detect the A/B press edge |

Thumb function pointers in tables carry the low bit; the addresses above are
the actual instruction addresses (even).

---

## 5. Algorithm

```
present(level, lives):
    i = level*10 + lives                       # 0..249
    return TABLE[i]                            # 4 digit bytes

validate(code[4]):                             # 0x080022B0
    for i in 0..249:
        if TABLE[i][0] == code[0] and
           TABLE[i][1] == code[1] and
           TABLE[i][2] == code[2] and
           TABLE[i][3] == code[3]:
            return i
    return -1

confirm(code):                                 # 0x08001F3A
    i = validate(code)
    if i == -1: return reject()                # red X
    level = i / 10                             # udiv, 0x08033FD4
    lives = i % 10                             # umod, 0x0803406C
    if level > 21: return reject()             # 0x080009AC, cmp #21
    [0x0300000C] = level                       # u32
    [0x0300314C] = lives                       # u16
    [0x03004284] = i                           # u16
    [0x03004286] = i                           # u16
    accept()                                   # CONNECTED briefing -> level
```

Notes on the assembly:

* The four digit widgets are 0x34 bytes apart; the digit value is a **u16** at
  widget `+0x12` (the widget base itself is not the digit address).
* The search reads table bytes with `ldrb` and the digit fields with `ldrsh`;
  a match requires the u16 high byte to be zero, which the wheel always writes.
* The search bound (`cmp r2,#249; bls`) includes all 250 records. The range
  check is a separate, later layer, so table entries 220–249 pass the search
  and then fail the range check.
* `0x080022B0` has exactly one caller (`0x08001F3A`), and `0x080009AC` has
  exactly one caller (`0x08001F5E`): this validator is reachable only from the
  password screen. There is no second password/checksum format.

---

## 6. Tables

### 6.1 The 250-entry table

Grid: rows = internal **level** (`index / 10`), columns = **lives**
(`index % 10`). Every cell is the 4-digit code that selects that level/lives
pair. Rows 22–24 are struck through: stored in the ROM but rejected by the
`level > 21` range check (30 dead entries, §6b).

| level | +0 | +1 | +2 | +3 | +4 | +5 | +6 | +7 | +8 | +9 |
|---:|---|---|---|---|---|---|---|---|---|---|
| 0 | 0961 | 4056 | 7779 | 7791 | 6824 | 4748 | 9375 | 0786 | 2790 | 7938 |
| 1 | 7334 | 6360 | 1357 | 5079 | 2262 | 0801 | 4356 | 6295 | 4711 | 1431 |
| 2 | 4476 | 4923 | 0112 | 4770 | 4220 | 5779 | 7578 | 0038 | 7135 | 3731 |
| 3 | 2736 | 6747 | 5261 | 2818 | 8620 | 1729 | 9695 | 1675 | 6611 | 6937 |
| 4 | 7182 | 4264 | 0738 | 4221 | 7736 | 0612 | 1293 | 2126 | 4969 | 9701 |
| 5 | 4956 | 3583 | 9836 | 9110 | 9222 | 4107 | 4154 | 8765 | 8871 | 2405 |
| 6 | 1002 | 7312 | 2303 | 4703 | 9803 | 6516 | 0427 | 3914 | 9283 | 7069 |
| 7 | 4193 | 7100 | 3246 | 6580 | 1635 | 9587 | 5861 | 6223 | 2448 | 5607 |
| 8 | 4927 | 1625 | 0772 | 0024 | 8289 | 2009 | 2245 | 0916 | 2178 | 1525 |
| 9 | 7256 | 6407 | 0597 | 0505 | 5703 | 6492 | 2909 | 7530 | 9774 | 9319 |
| 10 | 6944 | 7442 | 2072 | 5792 | 8118 | 3210 | 0623 | 9380 | 0821 | 1123 |
| 11 | 3073 | 5308 | 8194 | 4494 | 0737 | 9388 | 3708 | 3722 | 4501 | 6831 |
| 12 | 8648 | 4505 | 5653 | 4473 | 9812 | 1232 | 7396 | 5658 | 8463 | 0377 |
| 13 | 1814 | 2548 | 2748 | 5804 | 2623 | 4877 | 8067 | 3631 | 6418 | 4267 |
| 14 | 1713 | 3218 | 7189 | 6843 | 4078 | 7876 | 0543 | 0349 | 4433 | 8099 |
| 15 | 0942 | 5425 | 7693 | 7068 | 2553 | 8170 | 2682 | 6076 | 8167 | 3163 |
| 16 | 7930 | 6544 | 6406 | 8881 | 6041 | 5644 | 9202 | 0938 | 8354 | 3204 |
| 17 | 6002 | 4599 | 4362 | 5595 | 1989 | 8127 | 6863 | 4715 | 8001 | 3198 |
| 18 | 8070 | 2638 | 5129 | 4130 | 1387 | 4405 | 2499 | 5992 | 6183 | 5941 |
| 19 | 5584 | 5035 | 4542 | 3918 | 6919 | 2675 | 5478 | 2659 | 0637 | 1379 |
| 20 | 4743 | 7730 | 6262 | 9714 | 7667 | 4805 | 6227 | 0903 | 2703 | 7460 |
| 21 | 2365 | 7715 | 6308 | 9427 | 9362 | 9225 | 2458 | 4171 | 7777 | 8804 |
| 22 | ~~5461~~ | ~~3676~~ | ~~0687~~ | ~~4863~~ | ~~9095~~ | ~~8850~~ | ~~5420~~ | ~~1666~~ | ~~0668~~ | ~~0021~~ |
| 23 | ~~3685~~ | ~~8002~~ | ~~7749~~ | ~~3925~~ | ~~2066~~ | ~~0430~~ | ~~7095~~ | ~~8123~~ | ~~5456~~ | ~~1255~~ |
| 24 | ~~8390~~ | ~~4979~~ | ~~4896~~ | ~~3776~~ | ~~6218~~ | ~~4742~~ | ~~7980~~ | ~~8999~~ | ~~8937~~ | ~~4126~~ |

All 250 records are unique (no duplicate code → no alias indices).

### 6.2 Published codes verified against the ROM

All 51 distinct codes in the fetched lists are present in the table and within
the accepted range. (Sources: GameFAQs GBA "Level Passwords", GameFAQs
"Alternative Level Passwords PS", the CT Special Force Fandom wiki, CheatCC,
CheatHappens.)

| Code | Index | Level | Lives | Published as |
|---|---:|---:|---:|---|
| `0024` | 83 | 8 | 3 | PS |
| `0038` | 27 | 2 | 7 | PS |
| `0349` | 147 | 14 | 7 | PS |
| `0377` | 129 | 12 | 9 | GBA/PS |
| `0427` | 66 | 6 | 6 | PS/wiki |
| `0505` | 93 | 9 | 3 | PS |
| `0612` | 45 | 4 | 5 | PS |
| `0623` | 106 | 10 | 6 | PS |
| `0637` | 198 | 19 | 8 | PS |
| `0737` | 114 | 11 | 4 | PS |
| `0738` | 42 | 4 | 2 | PS |
| `0772` | 82 | 8 | 2 | PS |
| `0801` | 15 | 1 | 5 | GBA/PS |
| `0821` | 108 | 10 | 8 | PS |
| `1123` | 109 | 10 | 9 | GBA |
| `1293` | 46 | 4 | 6 | GBA |
| `1379` | 199 | 19 | 9 | GBA |
| `1431` | 19 | 1 | 9 | GBA |
| `1525` | 89 | 8 | 9 | GBA |
| `1729` | 35 | 3 | 5 | GBA |
| `2405` | 59 | 5 | 9 | GBA |
| `2638` | 181 | 18 | 1 | wiki |
| `2748` | 132 | 13 | 2 | wiki |
| `3163` | 159 | 15 | 9 | GBA |
| `3198` | 179 | 17 | 9 | GBA |
| `3204` | 169 | 16 | 9 | GBA |
| `3731` | 29 | 2 | 9 | GBA |
| `4154` | 56 | 5 | 6 | GBA |
| `4267` | 139 | 13 | 9 | GBA |
| `4362` | 172 | 17 | 2 | wiki |
| `4494` | 113 | 11 | 3 | wiki |
| `5035` | 191 | 19 | 1 | wiki |
| `5607` | 79 | 7 | 9 | GBA |
| `5653` | 122 | 12 | 2 | wiki |
| `5703` | 94 | 9 | 4 | wiki |
| `5779` | 25 | 2 | 5 | GBA |
| `5792` | 103 | 10 | 3 | wiki |
| `5861` | 76 | 7 | 6 | wiki |
| `5941` | 189 | 18 | 9 | GBA |
| `6262` | 202 | 20 | 2 | wiki |
| `6831` | 119 | 11 | 9 | GBA |
| `6937` | 39 | 3 | 9 | GBA |
| `7069` | 69 | 6 | 9 | GBA |
| `7189` | 142 | 14 | 2 | wiki |
| `7460` | 209 | 20 | 9 | GBA |
| `7693` | 152 | 15 | 2 | wiki |
| `8099` | 149 | 14 | 9 | GBA |
| `8804` | 219 | 21 | 9 | GBA |
| `8881` | 163 | 16 | 3 | wiki |
| `9319` | 99 | 9 | 9 | GBA |
| `9701` | 49 | 4 | 9 | GBA |

The published mission/stage labels do **not** map one-to-one to the internal
level index for every code (e.g. `0801` is internal level 1, `1293` is internal
level 4 and is labelled "nuclear warning level 1"). The internal index is what
the ROM stores; treat the fan labels as human descriptions of the level reached,
not as field values.

---

## 6b. Enumeration

### Space definition

| Property | Value |
|---|---|
| Input alphabet | `0`–`9` (10 symbols) |
| Input length | exactly 4 digits |
| Representable inputs | `10^4 = 10,000` |
| Storage | 250 fixed records × 4 bytes at `0x087D8618` |
| Search domain | indices `0..249` (`cmp #249`) |
| Acceptance rule | exact match **and** `index / 10 <= 21` |
| **Accepted values** | **220** (indices 0–219) |
| Dead records | 30 (indices 220–249, levels 22–24) |
| Rejected inputs | 9,780 (9,750 non-table + 30 out-of-range records) |
| Field widths | level 5 bits usable (0–21), lives 4 bits (0–9); no checksum |
| Duplicates/aliases | none (250 unique codes) |

This is a closed lookup, not a checksum format: there is no arithmetic relation
between the four digits, so “minting” a code means selecting a table row.
Running the reimplementation in `ctsf2_password.py` over all 10,000 strings
`0000`–`9999` yields exactly **220 accepts** (the 220 table indices 0–219),
matching the ROM's single validator function; the other 9,780 strings fail
either the table search or the `level > 21` check.

### Novel codes (in no published list) — observed in mGBA

**`7938` — index 9 → internal level 0, lives 9.**

* Not present in the GameFAQs GBA list, the "PS" list, the wiki, CheatCC or
  CheatHappens.
* Entered on the unmodified ROM at the password screen → `CONNECTED` briefing
  → the **helicopter prologue mission** (Jill/Raptor dialogue, helicopter over
  desert). The campaign's published lists start at internal level 1; level 0 is
  omitted.
* RAM after acceptance: `0x0300000C = 0`, `0x0300314C = 9`.
* Screenshots: `CT Special Forces 2 - 7938 level 0 helicopter.png`,
  `CT Special Forces 2 - 7938 briefing.png`.

**`4711` — index 18 → internal level 1, lives 8.**

* The published "first stage" code is `1431` (same level, 9 lives); `4711`
  exercises the unadvertised 8-lives variant of the same level.
* Entered on the unmodified ROM → `CONNECTED` → first stage.
* RAM after acceptance: `0x0300000C = 1`, `0x0300314C = 8`.
* Screenshots: `CT Special Forces 2 - 4711 entered.png`,
  `CT Special Forces 2 - 4711 accepted CONNECTED.png`,
  `CT Special Forces 2 - 4711 gameplay level 1.png`.

**`0024` — published only as a "PS" code, accepted by the GBA ROM.**

* Index 83 → internal level 8, lives 3. Observed `CONNECTED` and RAM
  `0x0300000C = 8`, `0x0300314C = 3`.
* This disproves the GameFAQs platform split for this title: the GBA table
  contains the PS list.

### Bounds proven by rejection (observed in mGBA)

| Input | Why it must fail | Observed result |
|---|---|---|
| `5461` | real table record, index 220, `level = 22` → `level > 21` | red X; still on password screen |
| `0865` | no record in the 250-entry table | red X; still on password screen |

The `5461` rejection is the range-layer proof: the code *is* a genuine table
record (so the search succeeds), yet the game rejects it at the `cmp #21`
check. The `0865` rejection proves the table-match layer. A code that fails
both (e.g. any 4-digit value not in the table) takes the same red-X path.

### Published list vs enumeration

* 51 distinct published codes, **all** in the accepted set; 0 published codes
  missing from the ROM.
* 220 accepted codes total → **169 accepted codes are unpublished** (e.g.
  `0961`, `4056`, `4711`, `7938`, `1002`, `1232`, `7777`, …). The 169 are
  uncommon lives/level combinations the lists simply omit; the table is the
  complete answer.
* The 30 dead records are `5461 3676 0687 4863 9095 8850 5420 1666 0668 0021
  3685 8002 7749 3925 2066 0430 7095 8123 5456 1255 8390 4979 4896 3776 6218
  4742 7980 8999 8937 4126`. They are not “hidden codes”; they are unreachable
  table padding/cut levels.

### Negative results: menus and button codes

* **Screens walked (observed):** boot logos; language select (6 languages);
  title (`Press Start`); main menu (Mission / Challenge / Password / Options);
  Mission intro text; world map; mission briefing (`CONNECTED`); gameplay;
  pause (`PAUSE`, A Resume / B Quit); quit confirm (A No / B Yes); Challenge
  Waiting Room (link-cable Player 1/2); Password; Options (Music, SFX, Tutorial
  ON/OFF, Difficulty, Credits); Credits roll. No additional hidden/debug screen
  was found on any of them.
* **No button-code system:** the pause screen exposes exactly two actions
  (Resume/Quit) with no input sequence, and the title/main menu accept only
  normal navigation (`Start`, D-pad, A/B). A raw scan for contiguous runs of
  GBA key masks is not discriminative on this ROM (1,357 incidental small
  16-bit runs in graphics/audio data), so the negative rests on the complete
  screen walk above, not on that scan; no `debug`/`secret`/`cheat` string exists
  either.
* **Text search counts** (`strings -n 4` over the whole 8 MiB ROM):
  `password` 0, `passwd` 0, `cheat` 0, `debug` 0, `secret` 0, `unlock` 0,
  `level` 0, `stage` 0, `warp` 0, `continue` 0, `option` 0, `menu` 0,
  `invalid` 0, `lives` 0, `mission` 1 (`missioncompleted1`, an asset name),
  `code` 1 (`Shin'en Multimedia. Code: B.Wodok`, the GAX audio-engine banner).
  The visible UI is pre-rendered tile art, so the absence of ASCII UI text does
  not mean the screens are absent — the screen walk above is the primary
  evidence.
* **No second format:** the only caller of the table search is the password
  confirm branch, and the only caller of the range check is that same branch
  (`BL` scan). There is no encoder/generator pair and no alternate alphabet.

---

## 7. Validation evidence

### Observed (emulator / RAM)

| Claim | Evidence |
|---|---|
| `1431` accepted | `CONNECTED` briefing screenshot; gameplay reached |
| `0024` accepted; level 8 / lives 3 | `CONNECTED` screenshot; debugger read `0x0300000C=8`, `0x0300314C=3` |
| `4711` accepted; level 1 / lives 8 | `CONNECTED` + gameplay screenshots; debugger read `0x0300000C=1`, `0x0300314C=8` |
| `7938` accepted; level 0 / lives 9 | `CONNECTED`, helicopter-prologue screenshots; debugger read `0x0300000C=0`, `0x0300314C=9` |
| `5461` rejected | red X screenshot (index 220, level 22) |
| `0865` rejected | red X screenshot (not in table) |
| Password screen digits live at `0x020099F2/0x02009A26/0x02009A5A/0x02009A8E` | byte-diff of RAM before/after each Up press; addresses matched the `+0x12` field of 0x34-byte widgets |
| `[0x030030AC]` is the widget base at the password screen | debugger read `0x030030AC = 0x020099C8`; `0x020099C8+0x2A = 0x020099F2` |

### Derived (instruction-level)

| Claim | Evidence |
|---|---|
| 250-record table at `0x087D8618`, 4 bytes each | literal pool at `0x080022FC` = `0x087D8618`; search loop bound `cmp #249`; dump shows 250 unique 4-digit records |
| Search returns index or `-1` | `0x080022B0` compares 4 digits against `[table + i*4]`; after the loop `movs r0,#1; negs r0,r0` → `-1` |
| `level = i/10`, `lives = i%10` | caller calls `0x08033FD4` (quotient) and `0x0803406C` (remainder) with divisor 10, then `0x080009AC(level, lives)` |
| `level > 21` is rejected | `0x080009AC`: `cmp r2,#21; bhi return 0`; only then writes `0x0300000C` and `0x0300314C` |
| Exactly 220 codes reachable | 250 table records; 220 have `index/10 <= 21` |
| Validator is unique to the password screen | `BL` scan: `0x080022B0` has one caller (`0x08001F3A`); `0x080009AC` has one caller (`0x08001F5E`) |
| 22-entry level-record walk | level-sequence walker `0x080009D4` indexes 16-byte records at `0x087D7DAC` with `[0x0300000C]` and stops at `cmp r0,#22` |

### Inferred

| Claim | Confidence |
|---|---|
| Internal level 0 is the helicopter escort prologue/tutorial mission | High: accepted `7938` starts that mission with Jill/Raptor dialogue; the level index 0 is otherwise omitted from all published lists |
| Rows 22–24 are cut/padding levels | Medium: they are fully-formed table records but the separate range check excludes them; no level record beyond index 21 is reachable through this path |
| Header checksum was zeroed by a rebuild/trim tool, not a trainer | High: stock entry, intact logo, no trainer strings, valid complement |
| Fan mission labels are human descriptions, not internal fields | High: e.g. `0024` "Stop Igor" is internal level 8, `1293` "nuclear warning level 1" is internal level 4 |

---

## 8. Unknowns

* The exact design intent of the 30 dead records (levels 22–24): cut levels,
  padding to a fixed 250-record block, or a range check that was tightened after
  the table was authored. The ROM cannot distinguish these.
* The precise meaning of internal level 0 versus the normal campaign start. It
  behaves as a real playable mission (helicopter escort) but may be the tutorial
  that the Options "Tutorial ON/OFF" setting normally inserts.
* Why the GBA and PS published lists coexist in one table while fan sites label
  them by platform; likely the PS port reuses the GBA level ordering and the
  lists were split by whoever transcribed them.
* The header checksum field is zero; the tool that rebuilt/trimmed the header
  is unknown.
* Whether the `[0x03004284]` copy of the full index has a gameplay consumer
  beyond the briefing screen (not traced).

---

## 9. Tooling

* `mgba-sdl 0.10.5` under `Xvfb :220` / `openbox`, scaled `-3`,
  `SDL_AUDIODRIVER=dummy`.
* `xdotool` + `scrot` + ImageMagick for scripted input and 720×480 viewport
  crops; per-key 50–120 ms holds.
* mGBA command-line debugger (`mgba -3 -d`) driven through a pty: `x/1`,
  `x/2`, `x/4`, `b`, `trace`, `status`. Used for the RAM reads and the
  instruction trace that led to `0x08001F3A`.
* Python 3 + Capstone for Thumb decoding and the BL/caller scans;
  `arm-none-eabi-objdump -M force-thumb` for manual disassembly.
* Offline decoder/tool: `ctsf2_password.py` (companion script; reproduces the
  in-game accept/reject decisions and can list all 250 records).

---

## 10. Legal note

No ROM, graphics, audio, or extracted game assets are redistributed. This
report contains only hashes, addresses, algorithms, and short published
password strings needed to document the code system. Screenshots are emulator
captures included as behavioural evidence.
