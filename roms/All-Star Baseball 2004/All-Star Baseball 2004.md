# All-Star Baseball 2004 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/All-Star Baseball 2004/All-Star Baseball 2004.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title (0xA0–0xAB) | `ALLSTAR 2004` |
| Game code (0xAC–0xAF) | `AA7E` |
| Maker code (0xB0–0xB1) | `51` (Acclaim) |
| Fixed byte 0xB2 | `0x96` |
| Main unit / device (0xB3/0xB4) | `0x00` / `0x00` |
| Software version (0xBC) | `0` |
| Complement check (0xBD) | `0xF4` — matches `(-Σ bytes 0xA0..0xBC) - 0x19` |
| Header checksum (0xBE–0xBF) | `0x0000` (stored; not validated by the game) |
| Entry branch (0x00) | `0xEA00002E` → `0x080000C0` |
| Embedded GBA-header scan | Nintendo logo (156 bytes at 0x04) occurs **once**, at file `0x4` → one GBA image, not a multi-game cart |
| MD5 | `9a7d740691276d4f33cf090bc62ba379` |
| SHA-1 | `29e168a84e51c3b765e345baee6910433f298993` |
| SHA-256 | `06c9b7dd1dc90920b9db2fbf1da5bee35e9d650d9eadc058501a8ed5d9bff395` |

All ROM addresses are `0x08000000 + file_offset`. The 8 MiB image is mirrored
at `0x0A000000`/`0x0C000000`; a few engine tables use the mirrored form
(e.g. the tweak table `0x087C1C34` = file `0x7C1C34`).

## 2. Executive summary

**There is no password, no passcode keypad, no button cheat, and no
cheat/debug menu in this retail build.** There is exactly one hidden,
developer-intended **unlockable mode**: an `Extra teams` row appears at the
bottom of the Single Player menu at the top of the card-collection tiers
(observed at tier 5 = all 199 base cards; the row is absent at tier 3 and the
tier-4 case was not isolated), and opens a Legends vs Heroes exhibition. The front end is the same
Acclaim FELIB engine family as *All-Star Baseball 2003* and *Aggressive Inline*
(GBA), but the 2004 build is not a copy of 2003:

* The text database changed from a UTF-16 `TDBI` bank (2003) to an **ASCII
  `TDBB` v2** bank with 256 strings (ids 0–265, ten ids unused). No
  `password`, `passcode`, `cheat` or `secret` string exists in the ROM in
  ASCII, UTF-16, or the `+0x20` lower-case-shifted encoding.
* 2004 **kept** 2003's orphaned `Tweak` / `All Your Baseball Are Belong To Us`
  / `Parameter` / `Value` text (ids 161–164), **and added** `Test SFX` (239)
  and `Debug Info` (240) plus four roster labels (241–244). The roster labels
  are live: they are the pause-menu **Box Score** submenu. `Test SFX` and
  `Debug Info` are not displayed on any screen reached, are never passed to
  the only by-id text setter (`0x080529A0`), and have no literal pointer. They
  are best classified as text for a removed/disabled developer page.
* 2004 also contains a real `be/Source/tweakscreen.c` (`TWEAKSCREEN_init`,
  `0x0803A404`), called every frame from `0x080161BC`. Disassembly shows it is
  **not a menu**: it copies 38 per-difficulty gameplay parameters from
  `0x087C1C34` into `0x03003774`, indexed by the difficulty level 0–3, with
  the assert `Invalid difficulty level!`. In 2003 the same strings suggested a
  removed "Tweak" screen; in 2004 the name belongs to the difficulty-tuning
  table, not a UI.
* The game **does** have developer-intended **unlockables**, but they are
  card-count tiers, not codes: `TCINFO_isExtraStadiaUnlocked` (`0x0800FB74`)
  counts a 242-byte trading-card array at `0x030004C4` and returns tier 0–6.
  The team-select and stadium-option handlers add that tier to 30. Result:
  30+tier teams and 30+tier stadiums, i.e. six extra teams and six extra
  stadiums. The six extra stadiums were enumerated in-game (tier 6):
  **Classic Fenway, Classic Wrigley, Classic Yankee, Polo Grounds, Puerto
  Rico, Tiger Stadium** (indices 30–35). Tier 0 clamps at Pacific Bell Park;
  tier 1 exposes exactly Classic Fenway.
* At tier 5 (all 199 base cards) a hidden **`Extra teams`** row appears at the
  bottom of the Single Player menu (TDB id 235); the row is absent at tier 3. Selecting it opens an
  Exhibition between two otherwise unavailable teams, **Legends** and
  **Heroes**, with their own logos and a full playable game. This is the only
  hidden menu found; it is not in any published GBA cheat list.

No code system exists, so no code could be minted; §6b states the exact
negative space with counts and the rejected inputs. The published GBA "cheat"
pages contain only CodeBreaker device codes (out of scope by construction) and
one gameplay-control tip (R during a home-run trot), which is not a code.

## 3. How to reproduce

### Emulator and display

```bash
mkdir -p /tmp/opencode/asb2004
Xvfb :133 -screen 0 1024x768x24 &
DISPLAY=:133 openbox &
cd "/mnt/gbacheats/roms/All-Star Baseball 2004"
DISPLAY=:133 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 "All-Star Baseball 2004.gba" &
```

mGBA SDL default keymap used here:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Screenshots: `import -window <mGBA-window> out.png` (the window is exactly
720×480 = 240×160 at 3×). Savestates: `Shift+F1`…`Shift+F10` save,
`F1`…`F10` load.

### Menu path walked (all observed; see `evidence/`)

```
Boot logos
Title ("Press Start")                        evidence/01_title.png
Main menu                                    evidence/02_main_menu.png
 |- Single player                            evidence/03_single_player.png
 |   |- Quick Game -> team select            evidence/04_quick_game_team_select.png
 |   |    -> Options (Difficulty)            evidence/05_quick_game_options.png
 |   |    -> gameplay -> pause
 |   |- Exhibition -> team select -> Options
 |   |- All-Star Game -> team select         evidence/06_allstar_game.png
 |   |    -> Options (Difficulty, Time of day) evidence/07_allstar_options.png
 |   |- Batting Practice -> setup            evidence/08_batting_practice.png
 |   |    -> Options (Difficulty, Time of day, Pitch type, Location,
 |   |       Throws, Stadium)                evidence/09_batting_practice_options.png
 |   |- Home Run Derby -> player select      evidence/10_hrd_player_select.png
 |   |    -> Options (Control, Difficulty, Time of day, Style, Stadium)
 |   |                                       evidence/11_hrd_options.png
 |   |    -> derby game -> pause
 |   |- Season -> season type (5 rows)       evidence/12_season_type.png
 |   |    -> team select -> season main      evidence/13_season_main.png
 |   |       -> Schedule / Standings / Statistics (table pages)
 |   |       -> Team management              evidence/14_team_management.png
 |   |          -> Set lineup                evidence/15_set_lineup.png
 |   |          -> Set pitching staff / Trade players / Reset rosters
 |   |- World Series -> team select + Options + Start Series
 |                                            evidence/16_world_series.png
 |   |- (tier 5 only) Extra teams -> Legends vs Heroes exhibition
 |                                            evidence/33, 34, 35
 |- Multiplayer -> 2P LINK-UP (no link)      evidence/22_2p_link.png
 |- Trading cards                             evidence/17_trading_cards.png
 |- Options (Music, Effects, Crowd, In-game music, Auto fielding)
 |- Statistics (Team hitting / Team pitching) evidence/18_statistics.png
 |- Credits                                   evidence/19_credits.png

Pause menu (all 8 rows)                      evidence/20_pause_menu.png
 |- Play ball / Box score (4 roster pages) / Manage bullpen (greyed in
 |  Quick Game) / Swap position / Pinch hitter (greyed) / Game options /
 |  Change controls (side assignment)         evidence/21_change_controls.png
 |  / Quit game
```

Every screen above was opened with the d-pad/A and B was used to walk back.
No screen accepts text or shows a password/passcode/cheat/debug entry. The
`Box Score` submenu (Home/Away Team Batters/Pitchers) is the only place where
the "roster-looking" TDB ids 241–244 are used.

The `Extra teams` row is not visible at 0 cards, so the row and its mode were
reached by loading a savestate whose card-count array was set to the tier-5
condition (all 199 base cards). That is analysis instrumentation, not a
player-available shortcut; the underlying gate is the normal card collection
(`TCINFO`, §5.6). The original savestate was restored afterwards.

### Codes/inputs tested in the emulator

| Input | Where | Result |
|---|---|---|
| Up,Up,Down,Down,Left,Right,Left,Right,B,A (Konami) | Title | No effect (`evidence/31`). |
| L,R,L,R,Select | Title | No effect; title stays. |
| L / R / Select / Start individually | Title | No effect. |
| L+R+Select+Start held | Main menu | No effect (`evidence/32`). |
| Konami, then L/R/Select | Main menu | No effect; only normal menu navigation. |
| Select | In-game at bat | No visible change (contact cursor present before and after). |
| R | In-game at bat/pitch | No menu/state change. |
| L / R / Select / Start | Pause menu | No hidden row; the 8 rows never change. |
| Left/Right on team rows | Quick Game / Exhibition / World Series | Swaps the User/CPU side assignment (normal control), does not open a menu. |
| A on team row | Quick Game | No effect (no team-list popup). |

The published GBA CodeBreaker list (master code `0000351C 000A`,
`1003F8A4 0007`, etc.) is a device code list, not an in-game system, and is
outside the scope of this engagement; it was not used to reach any result.

## 4. Address map

| ROM address / file offset | Meaning |
|---|---|
| `0x08000000` / `0x0` | Header + ARM crt0; entry `0x080000C0` |
| `0x0806F524` / `0x6F524` | FELIB directory: `u32 count=1453`, `u32 hash_mult=10`, then 16-byte entries (`hash, 0, size, offset`) |
| `0x081FC6BC` / `0x1FC6BC` | Text DB `TDBB`: magic, `u32 version=2`, `u32 size=0x11DF`, `u32 0`, `u32 count=0x100`; table at `+0x14`; strings at `0x081FCAD0` |
| `0x080529A0` | `FE_setTextID(widget, id)` — the only by-id text setter (linear search of the TDB id table, stores the slot in `widget+0x0A`) |
| `0x08052A4C` | `FE_setTextString(widget, char*)` — sets literal text |
| `0x08052898` | `FE_textResolve(widget)` — resolves `widget+0x0A` (slot) to a string |
| `0x03004E6C` (RAM) | TDB runtime struct: `{base=0x081FC6BC, table=0x081FC6D0, strings=0x081FCAD0, count=0x100}` (points directly into ROM; no RAM copy) |
| `0x080460E4` | Key poll: `held = ~*(u16*)0x04000130`; `new = held & ~prev` → `0x03004310`, `prev` → `0x03004312` |
| `0x03004310` (RAM) | Newly-pressed keys, active-high (`u16`) |
| `0x03004312` (RAM) | Previous held keys (`u16`) |
| `0x03004314` (RAM) | Link/multi-player key word (`u16`) |
| `0x080423F8` | Per-player/link input poll (reads `0x04000130`, merges at `0x030041DC+8`) |
| `0x08798118` / `0x798118` | **Only** referenced table of key masks: `Up,Down,Left,Right,A,B` (`0040 0080 0020 0010 0001 0002`) |
| `0x0800205C` | Attract/demo input playback that uses the table above (literal at `0x080020DC`) — **not** a cheat table |
| `0x0803A404` | `TWEAKSCREEN_init`: copies 38 u32 values from `0x087C1C34 + difficulty*0x3A8` to `0x03003774`; difficulty `[0x030006D8+0x38]` must be 0–3 |
| `0x087C1C34` / `0x7C1C34` | 4 difficulty blocks × 0x3A8 bytes of 24-byte tuning records (first word copied by `TWEAKSCREEN_init`) |
| `0x0800FB74` | `TCINFO_isExtraStadiaUnlocked()` — card-count tier 0–6 |
| `0x030004C4` (RAM) | Trading-card array, 242 bytes, one non-zero byte per owned card; index 253 is a special completion flag |
| `0x080027EA` | Team-select handler: calls the tier function and uses `tier + 30` as the team count |
| `0x080050FA` | Stadium-option handler: calls the tier function and uses `tier + 30` as the stadium count |
| `0x08797DF8` / `0x797DF8` | 84 × `char*` layout names (`sc00`…`sc70`, `te00`, `sc72`…`sc83`) |
| `0x08797F84` / `0x797F84` | 84 × Thumb screen-handler pointers: 74 non-null, 10 null (slots 0, 38, 39, 55, 56, 57, 62, 63, 64, 70) |
| `0x081FCB73` | TDB id 13 `ABCDEFGHIJKLM` (dead alphabet run; no setter call) |
| `0x081FCB81` | TDB id 14 `NOPQRSTUVWXYZ` (dead alphabet run) |
| `0x081FCB8F` | TDB id 15 `TEST SCREEN` (dead) |
| `0x081FD25C` | TDB id 161 `Tweak` (dead) |
| `0x081FD262` | TDB id 162 `All Your Baseball Are Belong To Us` (dead) |
| `0x081FD285` | TDB id 163 `Parameter` (dead) |
| `0x081FD28F` | TDB id 164 `Value` (dead) |
| `0x081FD5B1` | TDB id 239 `Test SFX` (not displayed on any reached screen) |
| `0x081FD5BA` | TDB id 240 `Debug Info` (not displayed on any reached screen) |
| `0x081FD5C5` … `0x081FD5FD` | TDB ids 241–244 `Home Team Batters` / `Away Team Batters` / `Home Team Pitchers` / `Away Team Pitchers` — **live** Box Score submenu |
| `0x081FD586` | TDB id 235 `Extra teams` — **live, gated**: the hidden Single Player row that appears at card tier 5 |
| `0x0806456C`–`0x0806465C` | Team string bank special records: `MCA Manchester AS`, `NEL Negro League`, `HER Heroes`, `LGD Legends`, `HSA FreeAgents Unavailble`, `NL All-Stars`, `AL All-Stars` |
| `0x08064A1C`–`0x08064B00` | Stadium string bank special records: `Tiger`, `Puerto Rico`, `Polo Grounds`, `Classic Yankee Stadium`, `Classic Wrigley Field`, `Classic Fenway Park` |

Layout blobs: 74 of the 84 names resolve through the FELIB directory. The ten
names with no data are `sc37, sc38, sc54, sc55, sc56, sc57, sc61, sc62, sc63,
sc69` (names are still in the name table). `te00` also has no data but keeps a
handler pointer (equal to `sc65`'s), so it is an alias/leftover slot.

## 5. Algorithm

### 5.1 FELIB lookup (derived, same family as 2003)

```
dir = 0x0806F524
count = u32[dir+0]           # 1453
mult  = u32[dir+4]           # 10
h = 0
for c in name:
    if 'A' <= c <= 'Z': c += 0x20
    h = (h * mult + c) & 0xFFFFFFFF
binary-search dir+8 .. dir+8+count*16 for entry.hash == h
size = entry.size ; data = 0x0806F524 + entry.offset
```

Verified: `text\baseball.tdb` → size 4575, file `0x1FC6BC`;
`layout\sc00.LBN` → size 1508, file `0x3B10A8`.

### 5.2 Text database (`TDBB` v2, ASCII — not the 2003 `TDBI`)

```
if rom[0:4] != "TDBB": fail
version = u32[+0x04]         # 2
size    = u32[+0x08]         # 0x11DF
count   = u32[+0x10]         # 256
table   = +0x14              # count × (u16 id, u16 byte_offset)
strings = table + count*4    # 0x081FCAD0
for each (id, off):
    text = NUL-terminated ASCII at strings+off
```

Ids run 0…265 with **no entries for ids 224–233** (32 records after slot 223
jump from 223 to 234), so `id → slot` is not the identity above 223. All 256
strings are 7-bit ASCII. There is no UTF-16 text in this build (0 hits for
every UTF-16 keyword probe).

### 5.3 Text-by-id path (derived)

```
FE_setTextID(widget, id):
    for slot in 0..count-1:
        if u16[table + slot*4] == id:
            u16[widget+0x0A] = slot
            FE_textResolve(widget)
            return
    u16[widget+0x0A] = -1
```

`FE_setTextID` is called from 47 sites. The constant ids actually passed are
`0x41–0x44` (65–68), `0x7C/0x7D` (124/125), `0x83` (131), `0xAA/0xAB`
(170/171), `0xB2` (178), `0xD9` (217) and `0xFE` (254). The remaining sites
pass `small_index + 0x24` (team/difficulty/roster labels), `small_index +
0x46` (pitching stats) or `0x19 + small_index` (stat labels), or resolve a
widget field. **No call site passes 13, 14, 15, 161–164, 239 or 240.**

The Box Score labels (241–244) are the counter-example that shows some ids are
reached through a menu path rather than a literal call; they are live and
screenshot-proven. `Test SFX`/`Debug Info` were not reached on any of the 30+
screens and have no pointer or setter site.

### 5.4 Input path (derived + observed)

```
every frame: 0x04000130 -> ~value
  held = value                  (active-high, 10 bits)
  new  = held & ~previous       -> 0x03004310
  previous = held               -> 0x03004312
```

The per-player/link path (`0x080423F8`) merges into `0x030041DC+8`. The
attract mode simulates six buttons (Up,Down,Left,Right,A,B) through the table
at `0x08798118`; this is the only key-mask array in the ROM that is referenced
by code.

### 5.5 `TWEAKSCREEN_init` is a difficulty table, not a menu (derived)

```
difficulty = u16[0x030006D8 + 0x38]        # asserted 0..3
src = 0x087C1C34 + difficulty*0x3A8
dst = 0x03003774
for i in 0..37:
    dst[i] = u32[src + i*24]               # first word of each 24-byte record
```

The 24-byte records contain values and pointers into the engine's
`be/Source/tweakscreen.c` data. This is the per-difficulty gameplay tuning
set. It does not read input, draw a screen, or expose parameters to the
player; the 2003 strings `Tweak`/`Parameter`/`Value` are unrelated dead text.

### 5.6 Unlock tier (`TCINFO_isExtraStadiaUnlocked`, derived)

`c = 0x030004C4` (242 bytes; any non-zero byte = card owned):

```
n_base1 = count_nonzero(c[0x00..0x82])     # 131
n_base2 = count_nonzero(c[0x83..0xC6])     # 68
if n_base1 + n_base2 == 199:
    return c[0xFD] ? 6 : 5

n_a = count_nonzero(c[0xC7..0xD6])         # 16
n_b = count_nonzero(c[0xD7..0xE6])         # 16
n_c = count_nonzero(c[0xE7..0xF1])         # 11
if n_a + n_b == 32 and n_c == 11: return 4
if n_c == 11:                     return 3

total = n_base1 + n_base2 + n_a + n_b + n_c
if total > 126: return 2
if total >  62: return 1
return 0
```

Tier 0–6 is then added to 30 at the team-select handler (`0x080027EA`) and the
stadium-option handler (`0x080050FA`). The card array is 242 bytes, so the
"space" of unlock states is 2^242 in principle, but only the seven tier
outputs matter; the tier function is a monotone threshold classifier.

## 6. Tables

### 6.1 TDB ids relevant to this engagement

| ID | Text | Status |
|---:|---|---|
| 13 | `ABCDEFGHIJKLM` | dead alphabet run; no setter call (same as 2003) |
| 14 | `NOPQRSTUVWXYZ` | dead alphabet run; no setter call |
| 15 | `TEST SCREEN` | dead (kept from 2003) |
| **161** | **`Tweak`** | **dead** (kept from 2003) |
| **162** | **`All Your Baseball Are Belong To Us`** | **dead** |
| **163** | **`Parameter`** | **dead** |
| **164** | **`Value`** | **dead** |
| 165 | `All Your Cards:` | trading-cards screen |
| 202 | `You unlocked a new trading card!` | card-unlock toast |
| 235 | `Extra teams` | **live, gated**: hidden Single Player row at card tier 5; opens Legends vs Heroes |
| 239 | `Test SFX` | **not displayed** (new in 2004) |
| 240 | `Debug Info` | **not displayed** (new in 2004) |
| 241–244 | `Home Team Batters ` / `Away Team Batters` / `Home Team Pitchers` / `Away Team Pitchers` | **live**: pause → Box score |
| 250 | `WARNING! All trading cards will be lost…` | link/transfer |
| 265 | `Exit Game` | front-end exit |

The 2004 build adds ids 234–244 relative to 2003's text set. Of those,
234/236/237/238 (`Change positions`, `Total`, `Difficulty:`, `Time of day:`)
are normal option labels; 235 (`Extra teams`) is a gated menu row (tier 5);
239/240 are the two new debug-looking strings; 241–244 are the Box Score
labels.

### 6.2 Text-id call sites (47)

| Sites | Id / derivation | Used by |
|---:|---|---|
| 1 | `0x41` | link status |
| 1 | `0x42` | link status |
| 1 | `0x43` | link status |
| 2 | `0x44` | link status |
| 7 | `0x7C` | `User` / controller label |
| 8 | `0x7D` | `CPU` / controller label |
| 3 | `0x83` | `ON` |
| 1 | `0xAA` | link cable string |
| 1 | `0xAB` | `Disconnect` |
| 1 | `0xB2` | `Link error:` |
| 1 | `0xD9` | `No games scheduled!` |
| 1 | `0xFE` | `Start Series` |
| 6 | `[team/difficulty struct +0x24] + 0x24` | team/difficulty names |
| 2 | `[player struct +0x24] + 0x24` | player names |
| 2 | `[stats struct +0x46]` | pitching statistics |
| 1 | `0x19 + [byte]` | stat labels |
| 1 | widget field `+0x48` (generic list renderer) | menu/label widgets |
| rest | `ldr` from literal (dynamic) | menu labels |

None of these can select 161–164 or 239–240; 235 and 241–244 are selected by
menu data rather than by a literal call (235 is the gated `Extra teams` row;
241–244 are the Box Score submenu). The exact tables were not isolated; see §8.

### 6.3 Key masks (active-high)

| Button | Mask | Button | Mask |
|---|---:|---|---:|
| A | `0x001` | Right | `0x010` |
| B | `0x002` | Left | `0x020` |
| Select | `0x004` | Up | `0x040` |
| Start | `0x008` | Down | `0x080` |
| R | `0x100` | L | `0x200` |

The only code-referenced array of these values is `0x08798118`:
`0040 0080 0020 0010 0001 0002` (Up, Down, Left, Right, A, B) used by the
attract-mode input simulation at `0x0800205C`. No other run of ≥5 masks in the
ROM is referenced by a pointer.

### 6.4 Screen-table census

| Item | Count |
|---|---:|
| Layout-name slots (`0x08797DF8`) | 84 |
| Non-null handler slots (`0x08797F84`) | 74 |
| Null handler slots | 10 (0, 38, 39, 55, 56, 57, 62, 63, 64, 70) |
| Layout names with data in FELIB | 74 |
| Layout names without data | 10 (37, 38, 54, 55, 56, 57, 61, 62, 63, 69) |
| FELIB directory entries | 1453 |

The name/handler sets do not coincide exactly: `sc37, sc54, sc61, sc69` have
handlers but no layout data, and `sc39, sc64, sc70` (plus index 0) have layout
data but no handler. `te00` is an extra name with no data and a handler equal
to `sc65`'s.

### 6.5 Unlock tiers and extra content (derived + observed)

| Tier | Condition | Teams | Stadia | Last stadium in list |
|---:|---|---:|---:|---|
| 0 | total ≤ 62 | 30 | 30 | Pacific Bell Park |
| 1 | 63 ≤ total ≤ 126 | 31 | 31 | Classic Fenway |
| 2 | total ≥ 127 (and not 3–6) | 32 | 32 | Classic Wrigley |
| 3 | 11 special cards (`0xE7..0xF1`) | 33 | 33 | Classic Yankee |
| 4 | 32 cards (`0xC7..0xE6`) **and** 11 special | 34 | 34 | Polo Grounds |
| 5 | all 199 base cards (`0x00..0xC6`) | 35 | 35 | Puerto Rico |
| 6 | all 199 base cards **and** `c[0xFD] != 0` | 36 | 36 | Tiger Stadium |

Extra stadiums, observed in order at indices 30–35:

1. Classic Fenway
2. Classic Wrigley
3. Classic Yankee
4. Polo Grounds
5. Puerto Rico
6. Tiger Stadium

The six extra team records in the string bank are `Manchester AS` (MCA),
`Negro League` (NEL), `Heroes` (HER), `Legends` (LGD), `NL All-Stars` and
`AL All-Stars`; `HSA / FreeAgents Unavailble` is a placeholder. The hidden
`Extra teams` menu row is gated above **tier 3**: it is absent at tier 3
(11 special cards), present at tier 5 (all 199 base cards), and opens a
Legends vs Heroes exhibition. The tier-4 case and the exact list order of the
six team slots were not isolated (see §8).

### 6.6 Published-claim verdicts

| Published item | Source | Verdict in this ROM |
|---|---|---|
| CodeBreaker master code `0000351C 000A` / `1003F8A4 0007`; ball/strike/out codes | Neoseeker, Almar's Guides, 53lu, SuperCheats | Device codes, not in-game; outside scope. No in-game equivalent. |
| "Homerun Celebration: press R while running the bases" | SuperCheats GBA page | An in-game control, not a code. `R` was pressed in live play (no menu/state change); the HR-trot branch is a gameplay animation and was not reproduced (see §8). |
| "Cheat menu: press L", "hold L+R for uniforms", "R+Left/R+Down home runs", "Select to hit harder", "A during credits" | GameFAQs GBA page (search snippets; page returns 403 and has no Wayback snapshot) | No such text/table/state in this ROM; L/R/Select tests produced no menu or state change. These are 2003/console paraphrases. |
| Unused JPEG image | TCRF (archived 2021 snapshot) | Confirmed the ROM contains 270 baseline JPEGs (112×160 trading-card art). No debug menu or code is documented by TCRF. |

## 6b. Enumeration

### 6b.1 Password / passcode space

| Property | Value |
|---|---|
| Input screen | none (30+ screens walked; no keypad, no name entry, no text field) |
| Alphabet | none — TDB 13/14 are dead alphabet runs (no setter call) |
| Length | n/a |
| Field widths | n/a |
| Checksum | none (no checksum routine over typed symbols) |
| Reserved bits | n/a |
| Representable accepted values | **0** |

There is no validator to enumerate. A code cannot be "small but undocumented"
here: the comparison path that would accept a typed value does not exist.
This is a structural negative, not a short list.

### 6b.2 Button-sequence space

| Property | Value |
|---|---|
| Buttons observed | 10 (`A,B,Select,Start,Right,Left,Up,Down,R,L`) |
| Sequence validator | none |
| Code table | none; only `0x08798118` (Up,Down,Left,Right,A,B) exists, used by attract-mode demo playback at `0x0800205C` |
| Progress counters | none in the input path; `0x03004310/12` are only the per-frame new/previous words |
| Accepted hidden sequences | **0** |

Inputs tested and rejected with no effect: Konami at title (`evidence/31`),
`L,R,L,R,Select` at title, `L+R+Select+Start` at main menu (`evidence/32`),
Select/R in-game, L/R/Select/Start in the pause menu, and A on a team row.
The mask-array scan searched the whole ROM for runs of ≥5 legal key masks and
then for a 32-bit pointer to each run: **238 runs, 1 referenced** — the attract
demo order. That bounds the button-code space: no other sequence table is
reachable through a pointer.

### 6b.3 Text-ID and screen space

| Space | Size | Result |
|---|---:|---|
| Text-DB strings | 256 (ids 0–265, 10 ids unused) | 161–164 dead; 239–240 not displayed; 235 live-gated; 241–244 live Box Score |
| Text-by-id call sites | 47 | constant ids 65–68, 124/125, 131, 170/171, 178, 217, 254 only |
| Layout blobs | 74 with data (84 names) | no `password`/`cheat`/`debug` layout |
| Screen-table slots | 84 (74 handlers) | 10 null; none is a hidden menu |
| Dynamic menu rows | 1 hidden | `Extra teams` (id 235) appended to Single Player at tier 5 |
| ASCII runs ≥4 | 108,181 | 0 password/passcode/cheat/secret strings |
| UTF-16 keyword hits | 0 | the 2004 bank is ASCII, unlike 2003 |

Keyword classification over the 108,181 ASCII runs (case-insensitive
substring): `password` 0, `passcode` 0, `cheat` 0, `secret` 0, `debug` 61,
`unlock` 2, `tweak` 3, `parameter` 2, `code` 3, `menu` 1, `invalid` 15,
`select` 7, `test` 10. The `debug` runs are engine log tags
(`DEBUG_ASSERTSTRING()`, `DEBUG_Init`, `SOURCE/...`), the `unlock` runs are
`You unlocked a new trading card!` and `TCINFO_isExtraStadiaUnlocked`, the
`code` runs are `FE_COMMON_commonCode`, `this is now set up by the FE code`
and `Code Version: MakeLBN.inf v.%d`, and the `menu` run is
`FESCR03_selectTeamMenu` in an assert string. None is a menu label.

### 6b.4 Unlock-tier space (the positive hidden-content result)

| Property | Value |
|---|---|
| Tier function | `0x0800FB74`, input = 242-byte card array `0x030004C4` |
| Outputs | 0–6 (7 states) |
| Consumers | team select `0x080027EA`, stadium option `0x080050FA` |
| Teams | 30 + tier (max 36) |
| Stadia | 30 + tier (max 36) |
| Extra stadia (observed) | Classic Fenway, Classic Wrigley, Classic Yankee, Polo Grounds, Puerto Rico, Tiger Stadium |
| Extra teams (string bank) | Manchester AS, Negro League, Heroes, Legends, NL All-Stars, AL All-Stars |
| Hidden menu | `Extra teams` row appears at tier 5 (all 199 base cards); opens Legends vs Heroes; absent at tier 3 |
| Published list coverage | none of the extra stadiums, the extra teams, or the `Extra teams` mode appears in any published GBA cheat list found |

**Unpublished state demonstrated in-game.** With a controlled card-count
injection into a savestate (analysis instrumentation, **not** a cheat code),
the Single Player menu and the stadium list were enumerated:

* 62 cards (tier 0): 30 stadiums; last is **Pacific Bell Park**; pressing
  Right at the end stays there (`evidence/23`). No `Extra teams` row.
* 63 cards (tier 1): 31 stadiums; one extra appears, **Classic Fenway**
  (`evidence/24`). Right again stays on Classic Fenway — clamped, not wrapped.
  No `Extra teams` row.
* 11 special cards (tier 3): still no `Extra teams` row (`evidence/36`).
* 199 base cards (tier 5): the hidden **`Extra teams`** row appears at the
  bottom of the Single Player menu (`evidence/33`). Selecting it opens an
  Exhibition between **Legends** and **Heroes** (`evidence/34`), and the match
  starts normally: `LGD 1 / HER 0`, Comiskey Park (`evidence/35`).
* 199 base cards + `c[0xFD]` (tier 6): 36 stadiums; the six extra entries were
  captured one by one as `evidence/25`–`evidence/30` in the order above.

The `Extra teams` mode is the clearest "novel, unpublished" result: it is a
full hidden mode, not a code, and it appears in no FAQ or cheat list found.
Its gate is above tier 3: tier 3 does not show the row; tier 5 does.

The original `.ss4` state was restored byte-for-byte after the experiment
(MD5 before/after `815794bf6b6e96ed600c789f73258ce2`). The injection script is
`patchstate2.py` in §9; it only writes the card-count array and re-compresses
the mGBA state.

### 6b.5 Bounds by rejection

| Rejected input | Expected if a system existed | Observed |
|---|---|---|
| Konami at title | hidden mode | no effect; title unchanged (`evidence/31`) |
| L,R,L,R,Select at title | debug/cheat gate | no effect |
| L+R+Select+Start at main menu | debug menu | no effect; menu unchanged (`evidence/32`) |
| Select in-game | code entry / cheat | no visible state change |
| R in-game | cheat menu | no menu/state change |
| L/R/Select/Start in pause | hidden row | 8 rows unchanged |
| A on team row | team list / hidden teams | no effect |
| Tier-0 stadium list, Right at the end | Classic Fenway | clamps at Pacific Bell Park; Classic Fenway not reachable (`evidence/23`) |
| Tier-1 list, Right at Classic Fenway | another extra | stays on Classic Fenway (`evidence/24`) |
| Tier 3 menu, look for Extra teams row | hidden mode | absent (`evidence/36`); tier 5 shows it (`evidence/33`); tier 4 not isolated |
| Password text entry | keypad | no text-entry screen exists to reject input |

## 7. Validation evidence

**Observed (emulator screenshots / RAM reads)**

* All screens in §3 were opened; the key ones are photographed
  (`evidence/01`–`22`).
* Box Score submenu shows the four roster labels (TDB ids 241–244) — proving
  that at least one id path outside the literal call-site list exists.
* The hidden `Extra teams` row appears at tier 5 and opens Legends vs Heroes
  (`evidence/33`–`35`); it is absent at tier 3 and below.
* Tier 0/1/6 stadium lists enumerated and photographed (`evidence/23`–`30`);
  the six extra stadiums appear only as the card tier rises.
* `0x030004C4` holds the injected card flags; `TCINFO` tier outputs matched
  the observed list lengths (30, 31, 36).
* `0x03004310/12` were confirmed as the new/previous key words by reading the
  poll at `0x080460E4`; the title/main tests produced no state changes.

**Derived (instruction/data analysis)**

* `TDBB` v2 layout, 256 strings, ASCII, ids 0–265 with the 224–233 gap.
* `FE_setTextID` is the only by-id setter; 47 call sites; no literal site
  passes 13, 14, 15, 161–164, 239 or 240. (235 and 241–244 are reached
  through menu data, not through the literal sites; 235 is proven live.)
* `TWEAKSCREEN_init` copies a 38-word difficulty table; not a UI.
* `TCINFO_isExtraStadiaUnlocked` pseudocode and the `30 + tier` consumers.
* Only one code-referenced key-mask array (`0x08798118`), used by attract
  demo playback.
* 84 layout slots / 74 handlers / 10 null; 74 layout blobs.

**Inferred**

* `Test SFX` and `Debug Info` are text for a developer page that was disabled
  or removed before this retail build; the strings survive because the shared
  `.tdb` was not pruned (same pattern as 2003's `Tweak` block).
* The six extra team slots are the six non-placeholder special team records;
  the hidden `Extra teams` mode uses Legends and Heroes. Whether Manchester
  AS, Negro League, NL All-Stars and AL All-Stars are selectable in any other
  mode at tier 6 is inferred, not proven.
* `c[0xFD]` is a "complete collection" flag used only by tier 6.

## 8. Unknowns

* The exact menu table that selects TDB ids 235 and 241–244 was not isolated.
  It is the counter-example to the "all ids come from the 47 call sites"
  model; a debug page using 239/240 through the same table cannot be excluded
  by that model alone. It is excluded by observation: no screen displays those
  strings, and no pointer/setter path was found.
* The order of the six unlockable teams in the team-select list, and whether
  all six (rather than only Legends/Heroes) are reachable through a mode.
* The HR-trot celebration animation (published as "press R while running the
  bases") was not reproduced: no home run was hit during the session. `R`
  itself was tested in live play and changes no menu/state. This is a
  gameplay-outcome gap, not a code-path gap.
* The meaning of the individual 24-byte records in the tweak table (values
  are consumed by gameplay code; only the copy loop was reversed).

## 9. Tooling

* `mgba` 0.10.5 (`/usr/games/mgba`), `Xvfb :133`, `openbox`, `scrot`/`import`,
  ImageMagick, `xdotool`, `gdb-multiarch`, `arm-none-eabi-objdump`, Python 3,
  Capstone 5.0.7, Keystone.
* Header/hash scan: `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`.
* FELIB/TDB extraction and the enumeration:

```python
import struct
rom = open("All-Star Baseball 2004.gba","rb").read()
DIR = 0x6F524
count, mult = struct.unpack_from("<II", rom, DIR)
def h(name):
    v = 0
    for c in name.encode():
        if 0x41 <= c <= 0x5A: c += 0x20
        v = (v*mult + c) & 0xFFFFFFFF
    return v
def lookup(name):
    for i in range(count):
        hh, _, size, off = struct.unpack_from("<IIII", rom, DIR+8+i*16)
        if hh == h(name): return size, DIR+off
size, off = lookup("text\\baseball.tdb")      # 4575, 0x1FC6BC
cnt = struct.unpack_from("<I", rom, off+0x10)[0]           # 256
base = off + 0x14 + cnt*4                                  # 0x1FCAD0
for k in range(cnt):
    sid, o = struct.unpack_from("<HH", rom, off+0x14+4*k)
    p = base+o; e = rom.find(b"\x00", p)
    print(sid, rom[p:e].decode("ascii"))
```

* Savestate RAM reader: mGBA writes a PNG whose `gbAs` chunk is a zlib stream;
  decompressed length 397,312, IWRAM at `0x19000`, EWRAM at `0x21000`.
* Tier instrumentation: `patchstate2.py` decompresses `gbAs`, writes the
  card array at IWRAM `0x030004C4`, re-compresses and rebuilds the PNG chunks
  with correct CRC32; the original `.ss4` was restored afterwards.
* The instrumentation hook experiment (patching `FE_setTextID` to log ids to
  EWRAM) was attempted and abandoned; the patched build crashed with an
  illegal opcode, and no result from it is used in this report.
* Re-runnable scripts: `evidence/tools/phase0.py`, `phase0_logo_complement.py`,
  `tdb.py`, `screen_table.py`, `string_counts.py`, `mask_refs.py`,
  `state_read.py`, `patchstate2.py`, `seq.py`.
* Evidence: `evidence/01_title.png` … `evidence/36_tier3_no_extra_teams_row.png`.

**Legal note.** No ROM, extracted graphics, audio, or copyrighted text is
redistributed here; only hashes, addresses, algorithms, short UI labels as
evidence, and the analyst's own screenshots.
