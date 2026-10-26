# Backyard Sports: Football 2007 (GBA) — Reverse Engineering Report

Status: complete. Scope: in-game / developer-intended cheats only (passwords,
button codes, hidden/debug menus, unlockables). No GameShark, CodeBreaker,
Action Replay or memory-edit code is proposed or used.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Backyard Sports: Football 2007/Backyard Sports: Football 2007.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`) |
| Header title (`0xA0`) | `BYF 2007` |
| Game code (`0xAC`) | `BF7E` |
| Maker (`0xB0`) | `70` |
| Version (`0xBC`) | `00` |
| Fixed `0xB2` | `0x96` |
| Entry (`0x00`) | `0xEA000030` → ARM branch to `0x080000C8` |
| Complement check (`0xBD`) | `0x1C` (computed `0x1C`) |
| Reserved (`0xBE`–`0xBF`) | `0x0000` (normal GBA value) |
| MD5 | `68a460a4face41897d483d3de367d809` |
| SHA-1 | `1b1504edd7220e14a694cb2c4b722f29868d8192` |
| SHA-256 | `d6845eeb8972f69a0cc78e50bd10d691ee3107559178a223e03c7c3204898208` |

Embedded-header scan: the whole 4 MiB image was searched for the exact 156-byte
Nintendo logo (`24 ff ae 51 …`). Exactly **one** occurrence exists, at file
`0x04`. This is a single-image cartridge, not a 2-in-1 or a boot-selector pack.

Build identification: the engine debug text includes `Built: Jul 14 2006` and
`Host:  scameron` (`0x087844`, `0x087858`); a second timestamp
`Jul 14 2006.22:17:13` sits at `0x087D78`. The header is internally consistent
and the entry region is stock, so this is a normal retail-style image with no
trainer/intro patch.

## 2. Executive summary

**This ROM contains no reachable in-game cheat, password, button-code, or
coach-name system, and no reachable debug menu.** The only developer leftovers
are the same Torus engine debug strings and dead debug-screen code already
documented for *Backyard Football 2006*: the `Debug Screen` root at
`0x0800449C` and its menu table at `0x0803AD910` have **zero** references (no
32-bit pointer, no Thumb/ARM `BL`, no Thumb-tagged pointer) anywhere in the
4 MiB image. They are dead developer tooling, not a hidden menu. TCRF lists the
same debug text and documents no access method; the retail build also leaves
the engine's entity-debug strings at `0x0803A79C8` (`Flag for deletion`,
`Entity Options:`), again without a game-menu reference.

What the game does have is a normal **create-a-player** feature: a roster slot
named `Custom Player` opens a preset editor with **15 nicknames, 10 hair
styles, 11 hair colours and 9 bodies**. It has no free-text field and no
alphabet/keyboard, so it is not a name-code surface. Selecting it allocates
skill points through the ordinary `Add Skill Points` screen, then stores the
created player in the 512-byte EEPROM save. No nickname in the list is a
developer code word, and no combination changes the accepted-input model.

All four mechanisms named in the brief were checked independently:

1. **Button codes** — the gameplay/menu keypad poll is
   `0x08075BBC`, which writes `held`/`pressed` to `0x03000E66`/`0x03000E68`
   and nothing else. (The other `0x04000130` literal users are a low-level
   wait helper at `0x08076BA8` and literal pools, not a second game-input
   path.) There is no rolling button history, no ASCII button-letter table,
   and no contiguous key-mask table in the code region. A scan of the whole
   image found 23 short key-mask runs, all in data/graphics/text (file offsets
   `0x090228`, `0x20108E`…, `0x393746`), none in executable code. The nearest
   published Backyard GBA codes were entered and behave only as menu
   navigation or are impossible because `B` is the screen's BACK button.
2. **Passwords / alphabets** — `password`, `passcode`, `cheat`, `secret`,
   `unlock`, `code`, `coach` occur zero times (case-insensitive) in the ASCII
   text bank. No password screen, alphabet keyboard, or accepted-code table
   exists in the walked screen set. The large UI labels are glyph/tile-encoded,
   which is why the screen walk (28 screens plus 3 input tests) is the primary evidence for this
   negative, not a string grep.
3. **Coach names** — Season Play has no `Coaches Sign In` and no name-entry
   step; it goes `Difficulty Level → Select Home Field → Select Team → Player
   Select → Team Photo → Season Menu`. The 512-byte save has no name field
   (only an 8-byte header and an 80-byte season block at
   `0x1B0`–`0x1FF`).
4. **Hidden/debug menus** — one root and three sub-screens exist, all
   unreferenced. The engine entity-debug strings at `0x0803A79C8`/`0x0803A79DC`
   are likewise unreferenced game-data leftovers.

Because no accepted input language exists, no novel code can be minted. The
enumeration deliverable is therefore the **bounded negative proof** in §6b:
space definitions, counts, the exact dead-debug map, and in-emulator rejection
of every published/nearby input that could plausibly be a code.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL frontend), headless Xvfb. The session used display
`:162` (1024×768×24) with `openbox`:

```bash
Xvfb :162 -screen 0 1024x768x24 &
DISPLAY=:162 openbox &
DISPLAY=:162 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 \
  "Backyard Sports: Football 2007.gba" &
```

Default mGBA SDL keymap used throughout:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| Start | `Return` |
| Select | `BackSpace` |
| L / R | `a` / `s` |
| D-pad | arrow keys |

Hold keys 100–250 ms. The reset hotkey is `Ctrl+R`; it takes ~12 s to return
to the title on this host. Savestates: `Shift+F1`…`F5` save, `F1`…`F5` load.
The test states used were `ss1` (matchup screen), `ss3`/`ss4` (matchup
before/after the Baseball 2007 code) and `ss5` (Season Menu).

### 3.1 Screen walk used for the negative proof

```
Atari logo → title ("Press Start") → main menu
main menu: PICKUP GAME / EXHIBITION / SEASON PLAY / PRACTICE /
           MULTIPLAYER (greyed) / OPTIONS / PLAYER CARDS / CREDITS
  SELECT on any main item → information panel

PICKUP GAME → Difficulty Level (EASY/MEDIUM/HARD, POWER-UPS, FATIGUE,
              TURNOVERS) → Matchup (Away Player 1 vs Home CPU, field) →
              kickoff play-call → Start = Time Out
Time Out: TEAM STRATEGY / CHANGE OFFENSE PLAYBOOK / CHANGE DEFENSE
          PLAYBOOK / CHANGE KICKING PLAYBOOK / CHANGE KICK RET. PLAYBOOK /
          QUIT GAME

EXHIBITION → Difficulty Level → Select Team → Player Select →
             Team Photo → practice/game

SEASON PLAY → Difficulty Level → Select Home Field (8 fields) →
              Select Team → Player Select → [Custom Player editor] →
              [Add Skill Points] → Team Photo → Season Menu
Season Menu: BEGIN SEASON / SEASON SCHEDULE / LEAGUE STANDINGS /
             TEAM STATISTICS / TEAM STRATEGY / OPTIONS / QUIT GAME
  SEASON SCHEDULE: 8-game list, scrolls, no locked row
  LEAGUE STANDINGS: 8 slots, L/R changes division
  TEAM STATISTICS: 7-player stat table, L/R changes category
  TEAM STRATEGY: Time Out menu (4 playbooks, no QUIT)
  OPTIONS: MUSIC / AUTO-SAVE AFTER EVERY GAME / CONTROL HELP
  QUIT GAME: QUIT AND SAVE / QUIT

PRACTICE → Practice Setup (DEFENSIVE/OFFENSIVE, START ON, OWN/OPP,
           score) → practice play-call
MULTIPLAYER: greyed; D-pad skips it and A cannot open it.
```

Screen states observed (28 screens plus 3 input-test states): boot/Atari logo, title, main menu, main info
panel, Options, Options info, Player Cards, Credits, Difficulty Level,
Matchup, kickoff play-call, Time Out, Select Home Field (8 pages), Select Team
(Frontyard pages), Player Select, Custom Player, Add Skill Points, Team Photo,
Season Menu, Season Schedule, League Standings, Team Statistics, Team
Strategy, Season Options, Quit confirmation, Practice Setup, Practice
play-call, plus the greyed Multiplayer and the `PICK ME?` card screen.

Representative screenshots are in `shots/` (01–22). Key ones:
`shots/01_title.png`, `shots/02_main_menu.png`, `shots/04_options.png`,
`shots/07_matchup.png`, `shots/09_timeout.png`, `shots/11_player_select.png`,
`shots/12_custom_player.png`, `shots/13_nicknames.png`,
`shots/22_nicknames_wrap.png`, `shots/14_season_menu.png`,
`shots/18_practice_setup.png`.

### 3.2 Exact code-entry attempts

All were performed at the only plausible surfaces (main menu, matchup,
pause/Time Out) and followed by a screenshot and, where relevant, a savestate
diff of IWRAM (`0x03000000`–`0x03008000`) and EWRAM
(`0x02000000`–`0x02040000`).

| Input | Where | Observed result |
|---|---|---|
| `Up Up Left Right B Down` (GameFAQs/IGN *Backyard Baseball 2007* GBA "Unlimited Turbo") | Matchup | `B` is the matchup BACK button: the screen returns to Difficulty Level before `Down`; sequence cannot be completed as a code (`shots/21_baseball_code_back.png`). |
| `Up Up Down Down A` (*Backyard Basketball* GBA "Hot hands") | Matchup | Up/Down do nothing on the static matchup; final `A` advances to kickoff. No stat/flag/HUD change. |
| `Down Up Down Up A` (*Backyard Basketball* "Super speed") | Matchup | Same: A advances; no effect. |
| `Select Select B B Start` (*Backyard Basketball* "All dunks") | Matchup | `B` backs out; sequence is consumed as navigation. |
| `Up Up Left Right B A` (*Backyard Basketball* "Unlimited turbo") | Matchup | `B` backs out; A never reaches the code path. |
| Konami `Up Up Down Down Left Right Left Right B A` | Main menu | Cursor moves, A enters PICKUP GAME; normal navigation. |
| `L+R+Select+Start` held at boot/title | Title | Normal title → main menu. |
| `Select` held/tapped on main menu | Main menu | Information panel (`WELCOME TO THE CLUBHOUSE! …`); second press closes it. |
| Random 6-button sequence (e.g. `Right Left Up Down B A`) | Matchup and Time Out | No visible or state change beyond normal navigation. |

The published literals for the older Backyard engines are absent from the ROM
(§6b.2): `superkid`, `sharpeye`, `whatatackle`, `MRCLANKY`, `moreplays`,
`superspeed`, `Grand Slam`, `Paul Konerko`, `Area 51`, `Aquadome`,
`Quantum Field`, `Humongous Memorial` all return **0** byte hits.

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`. Code is Thumb unless noted.

| Item | ROM address | File offset | Notes |
|---|---:|---:|---|
| Cartridge entry | `0x080000C0` | `0xC0` | ARM |
| Keypad poll | `0x08075BBC` | `0x75BBC` | reads `0x04000130`; computes `held` and `pressed`; no history buffer |
| KEYINPUT literal | `0x08075BD4` | `0x75BD4` | `0x04000130`; other literals at `0x021584`, `0x076B14`, `0x076C00` |
| Key-state struct | `0x03000E60` (IWRAM) | — | `+6` held `0x03000E66`, `+8` pressed `0x03000E68` |
| Debug strings | `0x080877F0`–`0x08087D90` | `0x877F0`–`0x87D90` | `Options`, `Back`, `Systems Menu`, `Performance Menu`, `Profiling Menu`, `Debug Screen`, `Built: Jul 14 2006`, `Host:  scameron`, RAM/frame stats |
| Build timestamp | `0x08087D78` | `0x87D78` | `Jul 14 2006.22:17:13` |
| Debug display root | `0x0800449C` | `0x449C` | prints banner + 4-item menu; **0 xrefs** |
| Debug menu table | `0x0803AD910` | `0x3AD910` | pointers to `Options`/`Back`/`Systems`/`Performance`/`Profiling`; **0 xrefs** |
| Systems handler | `0x080045A0` | `0x45A0` | only caller is root |
| Performance handler | `0x08004700` | `0x4700` | only caller is root |
| Profiling handler | `0x08004824` | `0x4824` | only caller is root |
| Entity-debug strings | `0x0803A79C0`–`0x0803A79E4` | `0x3A79C0`–`0x3A79E4` | `Back`, `Flag for deletion`, `Entity Options:`; 0 direct pointer refs |
| Player-name bank (lower "Custom player") | `0x0808D960` | `0x8D960` | NUL-terminated ASCII, used by the create-a-player record |
| Player-name bank (upper "Custom Player") | `0x080908B0` | `0x908B0` | roster card name |
| Player record table | `0x08091464` | `0x91464` | 40-byte (`0x28`) records; name pointer + stats; first `Achmed Khan` |
| Custom Player record | `0x08091A2C` | `0x91A2C` | name ptr `0x080908B0`, all stats zero |
| Font/glyph metric table (inferred) | `0x0832CD40` | `0x32CD40` | 16-bit per-character glyph width/attribute pairs; not a password alphabet |
| Stadium/commentary name blob | `0x083A192F` | `0x3A192F` | `Dmitri Dome` … `Sandy Flats`, concatenated |
| EEPROM library banner | `0x083A8D58` | `0x3A8D58` | `EEPROM_V` |
| Save image | 512 bytes | — | 8-byte header + zero padding + season block `0x1B0`–`0x1FF` |

### 4.1 Save image (observed)

After normal play the 512-byte EEPROM contains:

```
0x000: b5 1e 02 f3 3e 2b 27 7c   (8-byte save header)
0x008-0x1AF: 00 … 00
0x1B0-0x1FF: 80-byte season/custom-player state, ending in the
             descending trailer 33 32 31 ("321")
```

There is **no ASCII name field** and no second 512-byte block: 512 bytes is the
whole save. The only mutable game-state area is `0x1B0`–`0x1FF`, which is the
season struct (including a created custom player's stat allocation); any
progression flags would live inside that struct, not in a separate code/cheat
store.

### 4.2 mGBA savestate mapping (for reproduction)

An mGBA `.ssN` file is a PNG with a `gbAs` chunk. The chunk is zlib-compressed
to 397,312 bytes (`0x61000`) with the same layout used for the other Torus
titles:

```
0x00000-0x18FFF  VRAM + palette + OAM + I/O
0x19000-0x20FFF  IWRAM  (0x03000000-0x03007FFF)
0x21000-0x60FFF  EWRAM  (0x02000000-0x0203FFFF)
```

so `RAM 0x0300xxxx` is state offset `0x19000 + xxxx` and
`RAM 0x0200xxxx` is `0x21000 + xxxx`. `ss1` was saved on the matchup screen,
`ss5` on the Season Menu.

## 5. Algorithm

### 5.1 Input pipeline

`0x08075BBC` is the gameplay/menu keypad poll:

```c
uint16_t raw    = *(volatile uint16_t*)0x04000130;  /* active-low */
uint16_t held   = raw ^ 0x03FF;                     /* active-high */
uint16_t prev   = *(uint16_t*)0x03000E66;
*(uint16_t*)0x03000E68 = held & ~prev;              /* newly pressed */
*(uint16_t*)0x03000E66 = held;
```

Bit values: A=`0x001`, B=`0x002`, Select=`0x004`, Start=`0x008`,
Right=`0x010`, Left=`0x020`, Up=`0x040`, Down=`0x080`, R=`0x100`,
L=`0x200`. The routine returns after the two stores; it does not append to a
buffer, does not hash a sequence, and does not call a matcher.

### 5.2 Debug suite (dead)

The root at `0x0800449C` prints the `Debug Screen` banner and draws a four-item
menu using the table at `0x0803AD910`:

```
Options / Back
Systems Menu   -> 0x080045A0 (Slow RAM, Fast RAM, Message System,
                              Entity Allocator, Back)
Performance    -> 0x08004700 (Reset Frame Rate, Frame Rate, Back)
Profiling      -> 0x08004824 (Show raw numbers, profiling counters, Back)
```

No instruction anywhere references `0x0800449C` or `0x0803AD910` (0 BL, 0
BLX, 0 ARM BL, 0 aligned/Thumb-tagged 32-bit pointers). The three sub-handlers
are called only from the root, so the whole suite is unreachable from game
code. This matches TCRF's independent note that the game has hidden
development text and does not document any way to open it.

### 5.3 Create-a-player (normal feature, not a code system)

`Player Select` contains a `Custom Player` record (`0x08091A2C`) whose stats
are zero. Pressing A opens the editor:

```
NICKNAME     : 15 presets (BIG DOG, BULLDOZER, BUTTERFINGERS, CRUSHER,
               CUTIE-PIE, FANCY PANTS, MELVIN, NOODLES, ROCKET,
               SCAREDY CAT, SLOPPY JOE, SWEET POTATO, SWEETNESS,
               THE GENERAL, TUFF SKIN)
HAIR         : STYLE 1 … STYLE 10
HAIR COLOR   : YELLOW 1, YELLOW 2, RED, BROWN 1, BROWN 2, BLACK,
               BLUE 1, PURPLE 1, PURPLE 2, GREEN, BLUE 2  (11)
BODY         : SMALL/MEDIUM/LARGE 1–3  (9)
```

Navigation is a preset picker only: L/R arrows on each row, no letter grid,
no text field, no OK-on-string. `SELECT PLAY` leads to `Add Skill Points`
(RUN/PASS/CATCH/KICK/BLOCK/TACKLE allocation) and then to Team Photo. The
15 × 10 × 11 × 9 = **14,850** cosmetic combinations are all name/appearance
choices; none is compared against a code table.

## 6. Tables

### 6.1 Screen inventory (complete walk)

| # | Screen | Items / result |
|---:|---|---|
| 1 | Boot | Atari logo |
| 2 | Title | `Press Start` |
| 3 | Main menu | 8 rows; Multiplayer greyed |
| 4 | Main info panel | `SELECT - INFO` text for each row |
| 5 | Options | Music, Auto-save, Control Help (3 rows, wraps) |
| 6 | Player Cards | L/R cycle, no locked slot |
| 7 | Credits | Torus Games scroll |
| 8 | Difficulty Level | Easy/Medium/Hard + 3 toggles |
| 9 | Matchup | Away Player 1 vs Home CPU, field |
| 10 | Kickoff play-call | 3 play pages, L/R flip |
| 11 | Time Out | 6 rows incl. QUIT GAME |
| 12 | Select Home Field | 8 fields, wraps |
| 13 | Select Team | 32 NFL + Backyard mascots, paged |
| 14 | Player Select | roster grid + Custom Player |
| 15 | Player Card / PICK ME? | YES / NO |
| 16 | Custom Player | 4 preset rows |
| 17 | Add Skill Points | 6 stats, available-points bar |
| 18 | Team Photo | 7 players |
| 19 | Season Menu | 7 rows |
| 20 | Season Schedule | 8 games |
| 21 | League Standings | 8 slots, L/R division |
| 22 | Team Statistics | 7 players, L/R category |
| 23 | Team Strategy | Time Out menu (4 playbooks) |
| 24 | Season Options | same 3 options |
| 25 | Quit confirmation | QUIT AND SAVE / QUIT |
| 26 | Practice Setup | Defense/Offense, Start On, Own/Opp, score |
| 27 | Practice play-call | 3 play pages |
| 28 | Multiplayer (greyed) | D-pad skips; A no-op |
| 29 | Boot combo test | normal title → main |
| 30 | Matchup after published code | normal / B-back |
| 31 | Time Out after random sequence | normal |

### 6.2 Published inputs verified against this ROM

| Source | Input | ROM literal? | In-game result |
|---|---|---|---|
| GameFAQs/IGN, *Backyard Baseball 2007* GBA | `Up Up Left Right B Down` | n/a (button code) | Rejected: B leaves matchup for Difficulty |
| *Backyard Basketball* GBA (2002) | `Up Up Down Down A` | n/a | Consumed as navigation; A starts game |
| *Backyard Basketball* GBA (2002) | `Down Up Down Up A` | n/a | Consumed as navigation |
| *Backyard Basketball* GBA (2002) | `Select Select B B Start` | n/a | B backs out; not enterable |
| *Backyard Basketball* GBA (2002) | `Up Up Left Right B A` | n/a | B backs out; not enterable |
| PC *Backyard Football* name codes | `superkid`, `sharpeye`, `whatatackle`, `MRCLANKY`, `moreplays`, `superspeed` | **0 hits** | No text-entry surface exists |
| *Baseball 2007* unlock | `Grand Slam` / `Paul Konerko` | **0 hits** | Not this game |
| *Football 2006/2008* published names | `Area 51`, `Aquadome`, `Quantum Field`, `Humongous Memorial` | **0 hits** | Not this game |

The GameFAQs page for *Backyard Sports Football 2007* (GBA) has a Cheats tab
but no in-game code entries surfaced (direct fetch returns HTTP 403); the only
community material found is a GBAtemp `.CHT` file, which is GameShark/Action
Replay memory-edit content and is out of scope. No in-game code for this title
was found on GameFAQs, IGN, or TCRF.

### 6.3 Debug strings (verbatim, for identification)

`Options`, `Back`, `Systems Menu`, `Performance Menu`, `Profiling Menu`,
`Debug Screen`, `Built: Jul 14 2006`, `Host:  scameron`, `Slow RAM`, `Fast RAM`,
`Message System`, `Entity Allocator`, `Reset Frame Rate`, `Frame Rate`,
`Show raw numbers`, `MAIN_LOOP`, `AI_SYSTEM`, `Z_ORDERER`, `MAP_SYSTEM`,
`SPRITE_SYSTEM_ENGINE`, `SPRITE_SYSTEM_UPDATES`, `SOUND_SYSTEM`, `CAMERA`,
`LINK_SYSTEM_SEND`, `LINK_SYSTEM_RECEIVE`, `PLAYER_CONTROL_HUMAN`,
`GAME_ENTITY_MANAGER`, `PLAYERS`, `BALL`, `COLLISIONS`, `PLAYER_COLLISIONS`.

## 6b. Enumeration

### 6b.1 Space definitions

This build has **no accepted code language**. The spaces that were bounded are:

| Space | Size / definition | Result |
|---|---|---|
| Button sequences | 10 buttons (A, B, Select, Start, Right, Left, Up, Down, R, L); the engine keeps no history, so any length is theoretically expressible | **Accepted set empty.** No table/matcher exists to accept a sequence. |
| ASCII code strings | Any NUL-terminated string over printable ASCII | No comparator/table; `password`/`cheat`/`code`/`secret`/`unlock`/`coach` counts are 0. |
| Text-entry surfaces | Free-text name/code field | **None.** The only text-like UI is the preset Custom Player picker (14,850 cosmetic combinations). |
| Coach-name surface | Season coach name | **None.** No sign-in/name screen; no name field in the 512-byte save. |
| Debug menus | 1 root + 3 sub-screens + entity menu | **0 references**; unreachable. |
| Unlockables | Fields, teams, cards | No locked/greyed/`?` slot in any selector; save has no unlock flags beyond the season struct. |

### 6b.2 Search counts (whole 4 MiB)

| Probe | Count / result |
|---|---|
| `strings -t x -n 4` | 35,234 strings; `password/passcode/cheat/secret/unlock/code/coach` = **0**; `debug` = 1 (`Debug Screen`); `extra` = 2 (commentary) |
| Case-insensitive keyword regex over raw bytes (23 terms) | only `debug` (1) and `extra` (2) |
| ASCII button-letter tables (`udlrabstmv`, ≥5 letters, 10-byte NUL-padded) | 10 hits at 6 unique offsets, all inside ASCII text/graphics (`0x2E07E3`, `0x2E0855`, `0x2E0F05`, `0x2E0F77`, `0x3394A7`, `0x3A348D`); no table |
| Contiguous `u16` key-mask runs (length ≥ 4, ≥ 3 distinct) | 23 runs, all in data/graphics/text (file offsets `0x090228`, `0x20108E`, `0x20112C`, … `0x393746`); **0 in code `0x000000`–`0x088000`** |
| Contiguous `u32` key-mask runs (length ≥ 4, ≥ 3 distinct) | 13 runs, all in data (file offsets `0x893A8`, `0x13F9E8`, … `0x270BF0`); **0 in code** |
| `cmp r0–r7,#imm` with a key mask, clustered ≥4 sites/64 bytes | 16 clusters, all A/B/Select/Start menu branches; **0 clusters containing a D-pad mask chain** |
| Long alphabet strings (`A–Z`/`0–9`, ≥26) | 3 ASCII tables (`0x325BA1`, `0x326A89`, `0x3A7ED1`) plus the glyph-metric table at `0x32CD40`; all font/ASCII mapping tables, not input alphabets |
| 16-entry single-character pointer tables | **0** |
| Debug root `0x0800449C` xrefs | **0** BL, 0 BLX, 0 ARM BL, 0 pointer, 0 Thumb-tagged pointer |
| Debug table `0x0803AD910` xrefs | **0** |
| Entity-debug string direct refs | **0** |

### 6b.3 Novel codes

**None can exist.** There is no accepted-input language, so the accepted set is
empty. The novel result of this engagement is the negative proof itself:
the exact dead-debug map, the complete 28-screen inventory (31 states including
input tests), and the bounded search counts above.

### 6b.4 Bounds proven by rejection

* **Baseball 2007 published combo** `Up Up Left Right B Down`: at the matchup
  screen, `B` returns to Difficulty Level; the sequence cannot be completed
  and no state is changed. This is a rejection by the screen's own control
  map (`B - BACK`).
* **Basketball 2002 published combos** `Up Up Down Down A`, `Down Up Down Up A`:
  the D-pad inputs do nothing on the static matchup and the final `A` is
  ordinary ADVANCE; the game starts normally with no flag/stat/HUD change.
  `Select Select B B Start` and `Up Up Left Right B A` are impossible because
  `B` exits the screen.
* **Konami code** at the main menu: moves the cursor and enters PICKUP GAME;
  no hidden state.
* **Boot chord** `L+R+Select+Start`: normal title → main menu.
* **Random 6-button sequence** at matchup and Time Out: no change beyond
  ordinary navigation.

These are negative bounds on the only surfaces that could carry a code: a
five/six-press sequence on the matchup or pause screen. The static absence of
any table/matcher is the stronger, whole-ROM bound.

## 7. Validation evidence

**Observed (emulator / screenshot / save):**

* 28 screen states walked plus 3 input-test states; no password, code, name-entry, or debug screen.
* Custom Player renders exactly 15 nicknames, 10 hair styles, 11 hair colours,
  9 bodies; L/R cycles and wraps; no free-text field.
* Published/nearby inputs produce only menu navigation or BACK, as tabulated
  in §3.2 and §6b.4.
* Save is 512 bytes; only the 8-byte header and `0x1B0`–`0x1FF` are non-zero;
  no ASCII name.
* Screenshots 01–22 in `shots/`.

**Derived (instruction/data analysis):**

* `0x08075BBC` is the gameplay/menu keypad poll and writes only `held`/`pressed`; the only other KEYINPUT reader is a low-level wait helper at `0x08076BA8`.
* No 32-bit pointer, Thumb/ARM `BL`, or Thumb-tagged pointer references the
  debug root `0x0800449C` or its table `0x0803AD910` (0 hits).
* The debug sub-handlers are called only by the dead root.
* No contiguous key-mask table or ASCII button table exists in the code region.
* The `Custom Player` record is a normal 40-byte roster record with zero
  stats; the editor stores presets, not a string.

**Inferred:**

* The debug suite is Torus engine tooling left in the retail build; its
  intended effects (RAM/frame stats) are clear from its strings; because it is
  unreachable, no runtime trace of the screens exists and the static evidence
  is the proof.
* The exact semantics of the 80-byte season block (beyond holding season and
  custom-player state) are not fully labelled; it contains no name or obvious
  cheat flag.

## 8. Unknowns

* The dead debug screens are unreachable by any reference in this image, so no
  runtime trace exists. Their layout is inferred from their strings and the
  menu table.
* Some bytes in the 80-byte season block are not individually labelled. They
  are season/custom-player state, not a name or code field; no accepted code
  writes there.
* The large UI labels are stored as glyph/tile data, so a raw ASCII grep cannot
  prove their absence. The negative rests on the complete screen walk plus the
  absence of any comparator/table, which is the stronger claim.

## 9. Tooling

* `mGBA 0.10.5` (SDL) under `Xvfb :162` + `openbox`; `xdotool` for input,
  `ImageMagick import/convert` for screenshots, `tesseract` for name OCR.
* Python 3 scripts in `/tmp/opencode/bfoot2007/`:
  * `phase0.py` — hashes, header parse, embedded-logo scan.
  * `scan_keys.py`, `scan2.py`, `scan3.py` — u16 key-mask runs, ASCII button
    table scan, keyword counts.
  * `xref.py` — Thumb/ARM BL and pointer xref scans.
  * `state.py`, `diffstate.py` — mGBA `gbAs` savestate extraction and IWRAM/
    EWRAM diff.
* `arm-none-eabi-objdump -M force-thumb` for the input poll and debug code.
* Reference pages: TCRF `Backyard Sports Football 2007` (debug text, archived
  2024-05-28); GameFAQs GBA page (Cheats tab, no in-game entries surfaced);
  IGN *Backyard Baseball 2007* GBA cheats page (nearest published combo).

## 10. Legal note

No ROM, extracted graphics, music, or text assets are redistributed here. Only
addresses, algorithms, hashes, screen descriptions, and the analyst's own
search results are published. The ROM remains at the path above and is
git-ignored.
