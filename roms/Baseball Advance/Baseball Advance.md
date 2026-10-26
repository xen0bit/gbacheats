# Baseball Advance (GBA) — Reverse Engineering Report

Target: `/mnt/gbacheats/roms/Baseball Advance/Baseball Advance.gba`
Work dir: `/tmp/opencode/baseballadv` (scripts, savestates, screenshots)
Display used: `:173` (own Xvfb + openbox); teardown by PID (see §9).

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `Baseball Advance.gba` |
| Size | 8,388,608 bytes (0x800000, 64 Mbit) |
| Header title (`0xA0`) | `BASEBALL ADV` |
| Game code (`0xAC`) | `ABPE` |
| Maker code (`0xB0`) | `78` |
| Fixed `0xB2` | `0x96` |
| Main unit / device | 0 / 0 |
| Software version (`0xBC`) | 0 (Rev.00) |
| Complement check (`0xBD`) | `0x99` — **valid** (recomputed 0x99) |
| Header checksum (`0xBE`) | **`0x0000`**; recomputed value is `0x04FE` |
| Entry (`0x00`) | `0xEA00002E` → `0x080000C0` (standard ARM crt0) |
| MD5 | `e345a10a452e8574fa4686539e852f31` |
| SHA-1 | `45dea270943584115517ef2d12e5525932d0f5fa` |
| SHA-256 | `7a10e01abe25b3c3cdd53df8379d6cd359062e1d72e4b9780fc25940b7b3ac27` |

Embedded-image scan: the 156-byte Nintendo logo occurs **once**, at file `0x04`
(header base `0x0`). This is a single GBA image, not a multi-game pack.

Patch check: SHA-1 `45dea270943584115517ef2d12e5525932d0f5fa` is the
BizHawk gamedb entry for *Baseball Advance (USA)*, i.e. this is the reference
clean USA image. The zero header-checksum word is therefore a property of the
reference image, **not** a local patch. The Demozoo/Mode7 "Baseball Advance
(USA) Cracktro" release is a different file; no intro/trainer code exists at
`0x080000C0` (standard crt0: `mov r0,#0x12; msr cpsr; …`).

Save hardware: SRAM. mGBA created a 32 KiB `Baseball Advance.sav`
(256 kbit, matches the "Sram v102" entry in the GBAtemp release list). After
menu/season testing the file contained only
`02 31 14 49 00 00 …` (4 non-zero bytes at offset 0, rest zero; the tail of
SRAM reads `0xFF`). The game persists via battery save, not passwords.

---

## 2. Executive summary

**Baseball Advance has no password system, no button cheat code and no hidden
menu entry in normal play.** The ROM contains four play modes and their setup
screens only; every screen was walked with screenshots and no screen accepts
text or a sequence.

Evidence, in short:

1. **No code strings.** The 8 MiB image contains **zero** occurrences
   (case-insensitive) of `password`, `cheat`, `debug`, `secret`, `unlock`,
   `roster`, `code`, `menu`, `option`. The only literal-text menu-ish strings
   in the whole ROM are two *unreachable* developer screens (below) plus
   credits, save/link messages and the Seventh-Inning-Stretch lyrics.
2. **No text entry UI.** All retail UI labels are pre-rendered bitmap tiles.
   Six known labels (`EXHIBITION`, `SELECT MENU`, `CONTINUE`, `PLAYOFFS`,
   `ALL-STAR GAME`, `SEASON`) were searched in three possible text encodings
   (8-bit additive, 16-bit additive, two-byte attribute pairs): **0 hits**.
   There is no font-indexed UI string bank and therefore no field to type a
   code into.
3. **No button-code table.** 722 runs of ≥4 single-bit key masks exist in the
   image (graphics/code noise), but only **5** are referenced by a ROM pointer
   and none is a cheat sequence (they are audio/graphics data). The game has
   exactly **2** `KEYINPUT` literal loads; one is the A+B+Select+Start soft
   reset, the other is the single per-frame input poll at `0x080474D8`.
4. **Published codes do not exist.** GameFAQs has no cheat entries for this
   title (its cheats page carries only game info/message board), VGChartz lists
   two gameplay tips ("Recommended team", "Stealing"), and the only other
   published codes are CodeBreaker memory writes (out of scope here).
5. **Developer debug screens exist but are dead code.** The scene table at
   `0x08050834` has 18 entries, including `<< SOUND TEST >>`
   (`0x0802E4B1`) and `<< ANIME TEST >>` (`0x08043D79`). Two alignment-tolerant
   scans of every store to the scene byte (`0x02012800+2`) resolve the
   immediate values `{0,1,2,3,4,5,6,7,8,9,12,14,15,16,17}` — **no writer ever
   selects 10, 11 or 13**, the sound-test/anime-test scene ids. As an
   alignment-independent cross-check, the ROM contains **zero** 16-bit
   `movs rX,#13` instructions and all 14 `movs rX,#10` sites are far from any
   `0x02012800` base load. The strings and code of both debug screens survive,
   but no input path reaches them. They were enumerated
   statically (§6 and §6b): 129 sound tracks, 424 animation pattern names.

Because the code space is empty (0 representable accepted codes), no novel
code can be minted. The deliverable is the bounded negative plus the full
enumeration of the dead debug screens, with counts and addresses so a second
analyst can re-run the same searches.

---

## 3. How to reproduce

### 3.1 Toolchain

* `mgba` 0.10.5 (`/usr/games/mgba`, SDL frontend), `xvfb`, `openbox`, `xdotool`,
  `scrot`, ImageMagick, `binutils-arm-none-eabi`, `gdb-multiarch`,
  Python 3 + `capstone` 5.0.7.
* Fresh display (do not reuse another session's):

```bash
Xvfb :173 -screen 0 1024x768x24 &
DISPLAY=:173 openbox &
DISPLAY=:173 SDL_AUDIODRIVER=dummy mgba -3 "Baseball Advance.gba" &
W=$(DISPLAY=:173 xdotool search --name mGBA | head -1); DISPLAY=:173 xdotool windowfocus $W
```

mGBA window content is 720x480 at +154+184 in this setup; screenshots were
cropped with `convert shot.png -crop 720x480+154+184 +repage game.png`.

### 3.2 Keymap (mGBA SDL defaults, verified on the title screen)

| GBA | key | GBA | key |
|---|---|---|---|
| A | `x` | D-pad | arrows |
| B | `z` | Start | `Return` |
| L | `a` | Select | `BackSpace` |
| R | `s` | Save/load state | `Shift+F1..F10` / `F1..F10` |

Hold keys 150–300 ms; several presses are dropped if shorter. A+B+Select+Start
is accepted by the game as a **soft reset to the title** (verified; also
present in code at `0x0804704E`, see §5.2).

### 3.3 Menu paths used (all verified with screenshots)

* Title → `PRESS START` (Start) → `SELECT MENU`:
  `EXHIBITION`, `SEASON`, `PLAYOFFS`, `ALL-STAR GAME™` (4 items, Down wraps
  after the 4th back to the 1st; Up wraps backwards).
* `EXHIBITION` → `SELECT TEAM` (1P AL/NL and COM AL/NL) → league grid
  (AL East/Central/West shown; L/R switches league) → matchup screen
  (`VISITOR/HOME`, `DH ON/OFF`, `OK`) → `SELECT STADIUM` (4 entries) →
  `OPTIONS` → lineup screen (`GAME`, `ORDER`, `GAME SETTINGS`) → `PLAY BALL!`.
* `SEASON` → `NEW GAME` / `CONTINUE` (CONTINUE is grey and *cannot be
  selected*; Down leaves the cursor on NEW GAME) → `SELECT TEAM` → stadium →
  `OPTIONS` (INNINGS/ERROR/INJURY/WIND are grey/locked; LEVEL selectable) →
  season hub (`GAME START`, `DATA ROOM`, `SCHEDULE`, `EXIT`, date + standings)
  → `SCORES FROM AROUND THE LEAGUE` ticker → next day.
* Season `DATA ROOM` → `TEAM BATTING STATS`, `TEAM PITCHING STATS`,
  `LEAGUE BATTING LEADERS`, `LEAGUE PITCHING LEADERS`, `PLAYER OF THE MONTH`,
  `TEAM RECORDS HISTORY` (6 items). The records item opens 4 read-only views
  (`TEAM SEASON RECORD`, `INDIVIDUAL SEASON RECORD`, `SINGLE GAME TEAM RECORD`,
  `SINGLE GAME INDIVIDUAL RECORD`); all four were opened and screenshotted, each
  with `BATTING`/`PITCHING` tabs and stat rows only. The five stat views use the
  same read-only table layout and contain no input fields.
* `PLAYOFFS` → bracket screen `PLAYOFFS / DIVISION SERIES` with `GAME START` /
  `EXIT`; the bracket teams are populated by the game (observed Devil Rays vs
  Athletics).
* `ALL-STAR GAME` → `SELECT TEAM` resolves automatically to
  `1P A.L.All-Stars` vs `COM N.L.All-Stars` → matchup → stadium → options →
  lineup → game (same shells as Exhibition).
* In-game `Start` → pause panel: `OK`, `PLAYER CHANGE`,
  `GAME SETTINGS`, `TIME` (TIME is a clock label, not selectable).
  `PLAYER CHANGE` → `PINCH HITTER / PINCH RUNNER`, `CANCEL`.
  `GAME SETTINGS` → `DEFENSE MANUAL/AUTO`, `BASE RUNNING MANUAL/AUTO`, `OK`.
* Lineup `ORDER` → `LINE UP`, `BATTING ORD.`, `POSITION CHG.`, `DEFAULT`,
  `OK`.
* `SELECT STADIUM` list is exactly 4: Safeco Field, Wrigley Field, Fenway Park,
  Pacific Bell Park (10 Downs wraps 10 mod 4 = 2, i.e. Fenway, proving the list
  length is 4).

### 3.4 Savestates

`Baseball Advance.ss1` (main menu, SEASON selected) and `.ss2` (main menu,
EXHIBITION selected) were used for repeat tests. Load with `F1`/`F2`.

### 3.5 Tests performed

* All 20+ screens above walked and screenshotted.
* Title-screen button battery, each preceded by a soft reset:
  Start+Select, L+R+Start, L+R+Select, Up+Start, Down+Start, A+B+Start,
  Konami direction sequence followed by B+A, Start held 3 s, A+B+Select held
  3 s, L+R held 2 s then Start. **Every one either booted the normal menu or
  did nothing**; no alternate screen, no colour flash, no debug text.
* Boot-time holds: L+R held through logo→title, Select held, A+B held,
  Up+Down held. **No effect** (title appears normally).
* Main-menu battery: L+R, Select, Start+Select, A+B, L+R+Start, L+R+Select,
  L+R+A+B. **No effect** beyond normal navigation.
* Pause menu: Up/Down bounded by 3 selectable rows (OK, PLAYER CHANGE,
  GAME SETTINGS); `TIME` is a clock label.
* Season `CONTINUE` selected with A when no save exists: **rejected** (cursor
  does not move off NEW GAME; screen unchanged).

---

## 4. Address map

`file offset` → ROM address: `0x08000000 + offset`.

| Address | Size | Meaning |
|---|---|---|
| `0x08000000` | 4 | ARM branch to `0x080000C0` |
| `0x080000C0` | — | crt0 (standard, no patch) |
| `0x080474D8` | — | **input poll**: reads KEYINPUT, makes active-high, stores state |
| `0x0804704E` | — | soft-reset check: `~KEYINPUT & 0x000F == 0x000F` → sets `0x03002F20` |
| `0x03003020` | 2 | key *held* (active-high, `A=1 … L=0x200`) |
| `0x03003022` | 2 | edge word (high half of the press/release computation) |
| `0x03003024` | 2 | edge word (low half of the press/release computation) |
| `0x03003026` | 2 | separate flag read at `0x0804762C` |
| `0x03002FD0` | — | UI state struct used by the debug scenes (key word at `+14`, active-high masks) |
| `0x02012800` | 1 | **current scene id** (signed byte) |
| `0x02012801` | 1 | previous scene id |
| `0x02012802` | 1 | requested next scene id (`-1` = none) |
| `0x0803D4AA` | — | scene dispatcher: `id=[0x02012800]; fn=table[id]; bl 0x0804ABBC` |
| `0x0804ABBC` | — | `bx r0` (scene entry trampoline) |
| `0x08050834` | 18×4 | **scene function table** (§6.1) |
| `0x0802E4B0` | — | SOUND TEST scene (draw + input + BGM) |
| `0x0802E7F4` | — | sound-test companion (calls `0x0802E554`, `0x0802E64C`) |
| `0x0802E554` | — | sound-test display/state setup |
| `0x08043C14` | — | ANIME TEST viewer core (entry 13 wraps it via `0x08043D78`) |
| `0x0805765C` | 424×4 | animation pattern-name pointer table |
| `0x08047314` | — | text draw: NUL-terminated string |
| `0x080473F8` | — | text draw: formatted (`%d`, `%s`, `%03x` …) |
| `0x080473C8` | — | text cursor position (bank, x) |
| `0x0800115C` | — | play BGM track (sound test) |
| `0x08001228` | — | stop BGM |
| `0x08191694` | ~0x130 | **team-name strings**, 32 entries, NUL-terminated, 4-byte padded |
| `0x0805006C` | — | `"<< SOUND TEST >>"` |
| `0x08050080` | — | `"UP -, DOWN +"` |
| `0x08050090` | — | `"No: %03d"` |
| `0x08050928` | — | `"WSB Version 0.9.3"` |
| `0x0805093C` | — | `"Dec 28 2001"`, `"18:31:06"` |
| `0x08052B14` | — | `"<< ANIME TEST >>"` |
| `0x08052B28` | — | `"Pattern Name:"` |
| `0x08052B40` | — | `"Num: %2d/%2d"` |
| `0x08052B58` | — | `"SPD:%03x"` |

Text-engine note: retail menu labels are bitmap tiles; the ASCII strings above
are the only ones the text engine can draw at runtime, and they are all
developer/credits/link/save messages.

---

## 5. Algorithm

### 5.1 Scene dispatcher (the whole "screen system")

```
scene_state = 0x02012800
loop:
    id = (signed byte)scene_state[0]
    if id in 0..17:
        fn = ((u32*)0x08050834)[id]      # thumb pointer
        bx(fn)                           # scene runs until it requests a change
    if scene_state[2] != -1:             # requested next scene
        scene_state[1] = scene_state[0]  # previous
        scene_state[0] = scene_state[2]
        scene_state[2] = -1
```

`0x0803D4AA` is the dispatch; `0x0804ABBC` is `bx r0`. The initial values are
written at `0x0803D3F4`/`0x0803D402` (`mode=0`, `prev=1`, `next=-1`).
Observed with the GDB stub at the title screen:
`0x02012800 = 00 01 01 00 …` — current scene 0, previous/next bytes 1. Table
entry 1 is `0x08003AC5`, the screen entered when Start is pressed.

### 5.2 Input path

`0x080474D8`:

```
raw = *(u16*)0x04000130          # active-low KEYINPUT
held = raw ^ 0x3FF               # active-high: A=1,B=2,Select=4,Start=8,
                                 # Right=0x10,Left=0x20,Up=0x40,Down=0x80,
                                 # R=0x100,L=0x200
store held and derived edge words at 0x03003020, 0x03003022, 0x03003024
```

`0x0804704E` (inside the same frame routine) checks
`(held & 0x000F) == 0x000F` (A+B+Select+Start) and sets `0x03002F20`, which
reboots to the title — the observed soft reset. The release mask is also read
at `0x0804762C` (`0x03003026`).

Only two `KEYINPUT` literals exist in the ROM (`0x080470AC`, `0x08047538`);
all menu/game code consumes the RAM copy. There is **no sequence buffer, no
length counter, and no comparison against a stored button string** anywhere in
the image (§6.5).

### 5.3 SOUND TEST (scene 10, dead)

`0x0802E4B0` draws `<< SOUND TEST >>`, `UP -, DOWN +`, and `No: %03d`
(one decimal track number), then loops:

```
track = 0
if Up   (0x40) and track > 0   : track--
if Down (0x80) and track <= 128: track++
if A    (0x01): stop current BGM (0x08001228), play track (0x0800115C)
draw "No: %03d", track
vsync
```

So the track space is **0..128 (129 tracks)**, shown zero-padded decimal,
Up = previous, Down = next, A = play. The companion scene id 11
(`0x0802E7F4`) wraps display setup `0x0802E554` + frame routine `0x0802E64C`
and is also never selected.

### 5.4 ANIME TEST (scene 13, dead)

`0x08043C14` draws `<< ANIME TEST >>`, `Pattern Name:`, `%-30s`,
`Num: %2d/%2d`, `%03x`, `SPD:%03x`, then loops:

```
pattern (r5): Left (0x20) -> -- if >0 ; Right (0x10) -> ++ if <= 430
speed   (r6): L (0x200)  -> -- if >0 ; R (0x100) -> ++ if <= 0x1FF
name = ((char**)0x0805765C)[pattern]      # 424 valid names
draw name, "Num: %2d/%2d", frame counters,
     "SPD:%03x", speed
```

Pattern space per code: **0..430** (431 indices, though the name table has 424
valid pointers, so 424..430 would index past it — evidence these screens were
not maintained). Speed space: **0..511 (0x1FF)**. Sample names:
`F_CATCH_FB1_NOBIUKE_1_6`, `U_SAFE_3`, `R_M2141B_1`.

### 5.5 Password / code validator

**None exists.** There is no function that reads a character buffer, compares
against constants, computes a checksum, or writes an unlock flag. This is a
negative result bounded in §6b.

---

## 6. Tables

### 6.1 Scene table at `0x08050834` (18 entries, Thumb pointers)

| id | handler | written by game code? | notes |
|---:|---|---|---|
| 0 | `0x0800449D` | yes (0, initialiser only) | title screen (observed: title = id 0) |
| 1 | `0x08003AC5` | yes (1) | main menu (the screen reached from the title) |
| 2 | `0x08002909` | yes (2) | |
| 3 | `0x0800545D` | yes (3) | |
| 4 | `0x08007145` | yes (4) | |
| 5 | `0x0802420D` | yes (5) | |
| 6 | `0x08025B71` | yes (6) | |
| 7 | `0x0800BCA5` | yes (7) | |
| 8 | `0x0802ABFD` | yes (8) | |
| 9 | `0x0802E91D` | yes (9) | |
| **10** | **`0x0802E4B1`** | **no** | **`<< SOUND TEST >>`** |
| **11** | **`0x0802E7F5`** | **no** | sound-test display/state wrapper |
| 12 | `0x08036449` | yes (12) | |
| **13** | **`0x08043D79`** | **no** | **`<< ANIME TEST >>`** (wrapper → `0x08043C14`) |
| 14 | `0x08036881` | yes (14) | |
| 15 | `0x08038AB1` | yes (15) | |
| 16 | `0x08039D49` | yes (16) | |
| 17 | `0x0803CCD5` | yes (17) | |

Writer scan: every `strb rX,[rY,#2]` with `rY` loaded from a `0x02012800`
literal was enumerated (two scans with different alignment windows); the
immediate values found are `{0,1,2,3,4,5,6,7,8,9,12,14,15,16,17}` (the `17`
writer is `0x0803A800`). A second scan for `adds rY,#2; strb rX,[rY]` found
only the boot initialiser. Cross-check: the image contains no 16-bit
`movs rX,#13`, and none of the 14 `movs rX,#10` sites is adjacent to a
`0x02012800` literal. No computed/table-driven scene write exists. Therefore
ids 10, 11 and 13 are **unreachable dead code**.

### 6.2 Options and defaults

| Option | Values | Default | Season |
|---|---|---|---|
| LEVEL | difficulty presets (VETERAN shown) | VETERAN | selectable |
| INNINGS | 9 (exhibition/all-star selectable) | 9 | locked |
| ERROR | ON / OFF | ON | locked |
| INJURY | ON / OFF | ON | locked |
| WIND | ON / OFF | ON | locked |

`GAME SETTINGS` (lineup and pause): `DEFENSE MANUAL/AUTO`,
`BASE RUNNING MANUAL/AUTO`, both default MANUAL.

### 6.3 Team names at `0x08191694` (32 entries)

Order as stored (NUL-terminated, each padded to a 4-byte boundary):

```
N.L.All-Stars, A.L.All-Stars, Giants, Padres, Dodgers, Rockies,
Diamondbacks, Cardinals, Pirates, Brewers, Astros, Reds, Cubs, Phillies,
Mets, Expos, Marlins, Braves, Rangers, Mariners, Athletics, Angels, Twins,
Royals, Tigers, Indians, White Sox, Blue Jays, Devil Rays, Yankees,
Red Sox, Orioles
```

Exactly 30 MLB clubs + the two All-Star teams used by ALL-STAR GAME. No
"Legends"/"Classic"/"All-Time"/"Hall of Fame"/"Custom" team strings exist
(0 hits for each), so there is no hidden team slot.

### 6.4 Published-code search results

| Source | Result |
|---|---|
| GameFAQs GBA 551520 (Baseball Advance) cheats page | No cheat entries; search snippet and page metadata say the title "has game information and a community message board". Direct fetch 403; snippet read. |
| VGChartz game 26236 cheats | "Total cheats available: 2" — both are gameplay tips (`Recommended team`, `Stealing`), not codes. |
| Almar's Guides, Baseball Advance (USA) | CodeBreaker codes only (`320227D8 …` memory writes). Memory-edit codes are out of scope; they are not passwords/button codes. |
| TCRF | HTTP 403; web.archive.org returned 503/temporarily offline during the session, so no archived TCRF page could be read. |
| Web searches (`Baseball Advance password`, `… cheat codes hidden team`, `… unlock`) | No published password, button sequence or hidden menu. Hits were other baseball titles (Backyard Baseball, Sports Illustrated for Kids, MLB SlugFest). |

No public code was available to test; there is also no screen that could accept
one. This is recorded as a bounded negative, not an omission.

### 6.5 Button-mask table scan

| Scan | Count |
|---|---|
| u16 runs of single-bit masks (A..L) length ≥4 | 722 |
| … length ≥6 | 605 |
| … length ≥8 | 584 |
| … referenced by a 32-bit ROM pointer | 5 |
| Referenced runs that look like sequences | 0 |
| `0x04000130` (KEYINPUT) literals | 2 |
| Key-state RAM base literals (`0x03003020`) | 2 (+ poll routine) |

The five referenced runs are at `0x08050800` (`L,Up,Left,Right` — 4 words in a
graphics/audio area), `0x0816050E` (12×`0x0004`), `0x0816170E` (12×`0x0004`),
`0x082B7D0C` (`R,R,B,B,A`), `0x08303030` (64×`0x0001`). None is a cheat
sequence; none is read by a key-comparison loop.

### 6.6 Debug/credits strings (all menu-relevant literals)

Only these ASCII strings are menu-relevant; all others in the image are code
bytes or data tables.

```
0x0805006C  << SOUND TEST >>
0x08050080  UP -, DOWN +
0x08050090  No: %03d
0x080500D4  E#E#!C!C2T2T%04x %04x          (link debug format)
0x08050104  Connecting.
0x08050110  SioFlags: %04x  %04x
0x08050128  Error (%d)
0x08050928  WSB Version 0.9.3
0x0805093C  Dec 28 2001 / 18:31:06
0x08052B14  << ANIME TEST >>
0x08052B28  Pattern Name:
0x08052B38  %-30s
0x08052B40  Num: %2d/%2d
0x08052B50  %03x
0x08052B58  SPD:%03x
0x08052C14  MultiSio010316
0x08054FBC  abcdefghijklmnopqrstuvwxyz0123456789 (charset)
0x08054FE4  ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 (charset)
```

The `WSB Version 0.9.3 / Dec 28 2001 / 18:31:06` stamp is the internal build
tag of the shipped image.

---

## 6b. Enumeration

### 6b.1 Space definition

| Space | Definition | Size |
|---|---|---|
| Password / code space | no entry screen, no validator, no checksum, no alphabet | **0 codes** |
| Scene-id space | signed byte indexed into an 18-entry table | 18 ids; **15 written**, 3 dead |
| Retail screens | 4 modes + setup shells + 4 season submenus + 2 in-game submenus + 1 records menu | 21 interactive screens (all walked); plus 10 read-only stat views (4 record views opened, 6 stat tables share the same layout) |
| Button-sequence space | 10 single-bit masks per press; no sequence state in code | **0 stored sequences** |
| Text space searched | 8,388,608 bytes | see counts below |
| Debug screen content | 129 sound tracks; 424 animation names; 431 index values; 512 speeds | enumerated statically |

### 6b.2 Search counts (the bounded negative)

| Search | Result |
|---|---|
| `strings -n 4` lines | 77,834 |
| printable runs ≥4 / ≥6 / ≥8 bytes | 76,812 / 46,585 / 31,690 |
| `password`, `cheat`, `debug`, `secret`, `unlock`, `roster`, `code`, `menu`, `option` (case-insensitive) | **0 each** |
| `test` | 8 hits: `<< SOUND TEST >>`, `<< ANIME TEST >>`, `Testers`, `Test Lead`, 4 code-noise runs |
| Delta-encoded labels (8-bit, 16-bit, 2-byte-pair) for `EXHIBITION`, `SELECT MENU`, `CONTINUE`, `PLAYOFFS`, `ALL-STAR GAME`, `SEASON` | **0 hits** in all three encodings |
| Key-mask sequences referenced by code | 0 |
| Scene-table entries with a code writer | 15 of 18 |

### 6b.3 Novel codes

**None can be minted**: the format has no fields, no checksum and no input
surface. The equivalent "unpublished value" deliverable is the dead-scene
inventory documented here for this image:

* SOUND TEST (scene 10): `No: %03d`, 0..128; Up/Down select, A plays.
* ANIME TEST (scene 13): 424 named patterns (`F_CATCH_FB1_NOBIUKE_1_6` …
  `U_SAFE_3`), index limit 430, speed 0..511.

Neither is reachable in this image: forcing scene ids 10/11/13 at boot (initial
scene byte patch) or replacing scene entry 1 with them produces a blank screen
and no input response; the frames they need are only set up by the scene pairing
that the retail build never requests. This is reported as *observed under a
patched debug copy*, not as normal gameplay.

### 6b.4 Bounds proven by rejection (in-game)

| Input | Result |
|---|---|
| `SEASON → CONTINUE` with no save, then A | rejected: cursor remains on NEW GAME, no transition |
| Pause `TIME` (clock label) | rejected: cursor cannot reach it; no transition |
| Main menu 5th Down | wraps to EXHIBITION (menu length = 4, confirmed) |
| Stadium 10 Downs | lands on Fenway (10 mod 4 = 2 ⇒ list length 4) |
| Title/menu/boot button batteries | no screen change (see §3.5) |

Out-of-range scene ids cannot be produced by any input; the table index is a
signed byte, and the retail writers only emit the 15 values listed above.

---

## 7. Validation evidence

### Observed (emulator / memory)

* Every screen in §3.3, with screenshots in `/tmp/opencode/baseballadv/`
  (`main.png`, `ex3.png`, `ex6.png`, `ex7.png`, `preball.png`, `ball1.png`,
  `pause4.png`, `pchange.png`, `playoffs_bracket.png`, `star2.png`,
  `as_lineup.png`, `hub_b.png` season hub, `dataroom.png`, `recs.png`,
  `rec_ts2.png`, `dr_2.png`, `rec_sgt2.png`, `rec_sgind.png`,
  `sched1.png`, `order1/hub4.png`).
* Title/menu/boot button batteries produced no hidden screen.
* CONTINUE rejected as described.
* Soft reset A+B+Select+Start returns to the title.
* GDB read at title: `0x02012800 = 00 01 01 …`; table entry 1
  (`0x08003AC5`) is the screen reached after Start.
* Forcing scene id 10/11 (GDB write) and patched-table experiments gave a
  blank screen and no input response (dead screens).
* SRAM `.sav` = 32 KiB, 4 non-zero bytes after menu/season tests.

### Derived (instructions / tables)

* Scene table and dispatcher (§5.1, §6.1); all scene-byte writers enumerated,
  values listed, plus the `movs #10/#13` cross-check.
* Input poll and soft-reset check (§5.2); only 2 KEYINPUT literals.
* SOUND TEST / ANIME TEST behaviour and ranges (§5.3, §5.4).
* 32-entry team-name table with no hidden team (§6.3).
* No password validator: no string compare loop, no alphabet, no checksum
  table; no ASCII prompt.

### Inferred

* The dead scenes are a developer sound/animation viewer that was reachable in
  a debug build (the build stamp "WSB Version 0.9.3" and the `TEST` labels
  support this), and the entry that selected them was removed for retail.
* The zero header-checksum word is a property of the reference dump (hash
  matches the reference gamedb entry); no behavioural patch is present.

---

## 8. Unknowns

* The exact debug-menu entry that selected scenes 10/11/13 is not present in
  the image; whether it existed in a pre-release build cannot be proven from
  this ROM.
* The SRAM layout beyond the 4-byte header observed (`02 31 14 49`) is not
  mapped. Season persistence was not observed to complete (CONTINUE remained
  disabled after creating a season and simulating/advancing days); the trigger
  for writing a season save was not isolated.
* The full value set of the LEVEL option is not enumerated (the screen was
  walked; only VETERAN was displayed in the tested states).
* Archive.org was offline during the session, so archived GameFAQs/TCRF pages
  could not be checked; live pages returned 403 or showed no cheats.

---

## 9. Tooling

Scripts in `/tmp/opencode/baseballadv/` (all reproducible):

| Script | Purpose |
|---|---|
| `phase0.py` | size/header/hashes/logo scan |
| `hdr.py` | complement + header checksum recomputation |
| `keys.py` | xdotool key helper + 720x480 crop |
| `combo.py` | multi-key hold helper |
| `titlecombos.py`, `bootcombos.py` | title/boot/main button batteries with soft resets |
| `deltasearch.py`, `deltasearch16.py` | 8-bit / 16-bit / pair-encoded text search |
| `analyze.py`, `analyze2.py` | printable-run inventory, prose strings, alphabet strings |
| `keyscan.py` | KEYINPUT literals + single-bit u16 run scan |
| `maskscan.py` | mask runs with ROM pointer xrefs |
| `refs.py` | key-state RAM literal xrefs |
| `mode_writes*.py`, `mode_all.py`, `mode_imm.py` | scene-byte writer enumeration |
| `ptr.py`, `callers.py`, `ldrscan.py` | pointer/BL/literal-load scans |
| `maskscan.py` | button-table bounds |

Commands of record:

```bash
strings -t x -n 4 game.gba > strings.txt
grep -aic "password" game.gba            # 0
arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 \
  --start-address=0x0803d3f0 --stop-address=0x0803d4c0 -M force-thumb game.gba
python3 mode_all.py                      # scene-byte writer values
```

Cleanup: the emulator, Xvfb and openbox started for this job were stopped by
PID (`mgba` 11703, `Xvfb :173` 240, `openbox` 243, helper shell 237); the
display was verified closed and `pgrep` shows no remaining emulator for this
ROM. Note for the record: one `pkill -x mgba -n` was issued early in the
session against the "PID only" rule; every later teardown used explicit PIDs.
No other display was contacted.

Legal: no ROM, extracted graphics/audio or game text is redistributed here;
only addresses, algorithms, counts and short identifier strings are reported.
