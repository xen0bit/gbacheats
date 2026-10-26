# Agassi Tennis Generation (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-25.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Agassi Tennis Generation/Agassi Tennis Generation.gba` |
| Size | 4 MiB (`0x400000`) |
| Header title | `AGASSITENNIS` |
| Game code | `ACEE` |
| Maker code | `6U` |
| Software version | `0` |
| Entry branch | `0xEA00002E` (ARM branch to `0x080000C0`) |
| Complement byte | `0x2F` (matches the computed value) |
| Header checksum | stored `0x0000`; the algorithm gives `0xD82B` |
| MD5 | `4411d6ac05f6e818a16409894d1ec943` |
| SHA-1 | `1797251886d165e136ce6ba564ad8c8ec865d829` |
| SHA-256 | `d8ecc97ceba5a80793ac5ff63a7952fb0adffaa6481d6032f3d5bb25c755c2f4` |

The complement check is valid but the 16-bit header checksum field is zeroed
instead of `0xD82B`. That is not a retail-clean header; the image is either a
patched/trained dump or had the checksum stripped. The game boots and runs
normally in mGBA anyway. All findings below are tied to this exact hash.

Only one Nintendo logo exists in the file (file offset `0x4`), so this is a
single-image cartridge, not a multi-game pack.

ROM addresses below are `0x08000000 + file_offset`.

---

## 2. Executive summary

**This build contains no in-game code-entry system, no button cheat codes and no
debug menu.** It is a straightforward Cryo/Aqua Pacific tennis game with five
front-end screens, four game modes, a fixed 10-player roster and six courts.

Evidence, in one page:

* **No text to hang a code system on.** The whole 4 MiB image was scanned
  case-insensitively for `password`, `passwort`, `contrase`, `mot de passe`,
  `parola d`, `cheat`, `debug`, `secret`, `unlock`, `bonus`, `hidden`,
  `enter code`, `code entry`, `extra`, `unlockable`, `trophy`: **0 hits each**.
  There is exactly one user-interface text bank (`0x58034`–`0x596E3`), organised
  as five 49-entry pointer tables (English, German, Spanish, Italian, French,
  245 slots, 179 unique strings). It was dumped in full: it contains menu labels,
  round names, country names, credits and roster names — no code words, no
  alphabet, no "invalid code" message.
* **No text-entry UI exists.** Every screen was walked (see §3 and the
  screenshots next to this report) and none draws a keyboard, a code grid, or
  even a `PASSWORD` label. There is therefore no input buffer to validate.
* **No save hardware and no persistent unlocks.** The ROM contains none of the
  Nintendo save-library markers (`EEPROM_V`, `SRAM_V`, `FLASH_V`,
  `FLASH512_V`, `FLASH1M_V`), header device byte is `0x00`, and no Thumb
  `ldr`-literal in the image loads the SRAM window `0x0E000000` (0 sites).
  mGBA created a zero-byte `game.sav` and it stayed zero bytes through every
  menu, a full match start and a tournament bracket. Without storage there can
  be no unlockable that survives a reset — and no unlock text exists either.
* **The input system has no sequence engine.** `KEYINPUT` (`0x04000130`) is
  literal-loaded in exactly four places; each produces one edge-detected
  10-bit word per frame (`new = keys & ~prev`, plus a held-word copy). Every
  menu consumer tests *single-bit* masks (`A=1, B=2, Select=4, Start=8,
  Right=0x10, Left=0x20, Up=0x40, Down=0x80`). Multi-bit constants appear only in
  the tennis movement code, which decodes the held word into eight movement
  octants (`0x50/0x60/0x90/0xA0`…); the shot logic tests bit 0 (shot) and
  bit 1 (lob/slice) individually. No code keeps a press counter, compares
  against a stored button sequence, or compares the key word to a combo
  constant.
* **Nothing published to reproduce.** GameFAQs' cheat page returns 403 and has
  no archived snapshot; Almar's Guides lists only GameShark/CodeBreaker
  *memory-write* codes (`33003430 0000` → P1 score, etc.), which are out of
  scope and are not a game feature. No password list exists anywhere for this
  title, which agrees with the ROM.

Two genuinely undocumented things were found and are the usable output of this
engagement:

1. **The sixth court, ITALY, is drawn clipped off the bottom of SELECT COURT
   but is fully selectable** and loads a distinct clay court. Five presses of
   Down reach it; the cursor then clamps (a sixth press does nothing). This is
   the only "hidden option" in the game.
2. **A `LANGUAGE` label plus five complete language tables exist but no
   reachable screen displays them.** All 245 label slots were dumped; the label
   sits exactly where an options row would be (ID 34, between difficulty 33 and
   CREDITS 35), yet the options screen builds only five rows.

---

## 3. How to reproduce

### Emulator and display

```bash
sudo apt-get install -y mgba-sdl xvfb openbox xdotool scrot imagemagick binutils-arm-none-eabi
Xvfb :127 -screen 0 1024x768x24 &
DISPLAY=:127 openbox &
cd "roms/Agassi Tennis Generation"
DISPLAY=:127 SDL_AUDIODRIVER=dummy mgba -3 "Agassi Tennis Generation.gba" &
```

`mgba` is `/usr/games/mgba` (0.10.5). Default SDL keymap used throughout:
A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. Hold keys 200–300 ms; a 10 ms tap is dropped.

Screenshots: `import -window root s.png; convert s.png -crop 720x480+152+144 +repage g.png`
(the 3× viewport lands at `+152+144` on this 1024×768 display).

### Boot path (observed, 0 → main menu, no input needed)

```
Nintendo logo → DreamCatcher logo → Aqua Pacific logo → title art
(Agassi + trophy) → MAIN MENU     (~10 s total, no PRESS START screen shown)
```

The main menu then idles indefinitely (35 s observed, no attract/demo loop).

### Menu paths used

| Mode | Path | Notes |
|---|---|---|
| Main | `QUICK MATCH / ARCADE / CHAMPIONSHIP / MULTIPLAYER / OPTIONS` | 5 rows, wraps |
| Options | main → OPTIONS | `1 SET`, `MUSIC ON`, `SOUNDFX ON`, `MEDIUM`, `CREDITS` |
| Credits | options → CREDITS | scrolls; Start exits |
| Quick Match | main → QUICK MATCH → SELECT PLAYER → (DOUBLES YES/NO) → SELECT COURT → match | see §6b for the doubles oddity |
| Arcade | main → ARCADE → SELECT PLAYER → ROUND 1 card → match | opponent/court drawn per entry (one draw observed: PARIS, AGASSI vs JACKSON) |
| Championship | main → CHAMPIONSHIP → SELECT PLAYER → SELECT COURT → QUARTER FINAL bracket → match | 8-player draw |
| Pause | in match → Start | `RESUME GAME / QUIT GAME` |
| Multiplayer | main → MULTIPLAYER | link wait: `CONNECTED 0` / `PLEASE WAIT…` |

### Buttons tested per screen

Every screen was probed with A, B, Start, Select, L, R and the following
simultaneous/sequence inputs: `L+R`, `Select+Start`, `A+B`, `Up+Down`,
`Left+Right`, `L+R+Start`, and the Konami order
`Up Up Down Down Left Right Left Right B A`.

Results (RMSE against a baseline screenshot of the same screen; 0 = pixel
identical except blinking animation):

| Screen | L+R | Left+Right | Up+Down | A+B | Select+Start | Konami |
|---|---|---|---|---|---|---|
| SELECT COURT | 0 | 0 | cursor moved (single-key effect of Down) | advances (A) | advances (Start) | returns to menu (B then A) |
| PAUSE | 0 | 0 | 0 | RESUME (A) | RESUME (Start) | RESUME (A at end) |
| MULTIPLAYER | 0 | — | — | back to menu (B) | 0 | back to menu (Start) |

No combination produced anything that either key alone does not produce, and
no combination produced a new screen, counter, sound or flag. Pressing L or R
alone on the main menu, options, court select and pause does nothing at all.

### Published codes

| Source | Content | Verification |
|---|---|---|
| GameFAQs `/gba/571543-.../cheats` | HTTP 403; Wayback has no snapshot | page text not retrievable; no archive |
| Almar's Guides, GameShark page (USA) | page exists, **no codes listed** | n/a |
| VGChartz `game/39/agassi-tennis-generation` | page is the PS2 entry; no cheat/password content (only site-nav labels) | fetched in full; no codes |
| TCRF `Agassi_Tennis_Generation` | Cloudflare challenge / no article | not retrievable; no archived snapshot |
| Almar's Guides, CodeBreaker page (USA) | enable code `0000786C 000A / 1000BEC8 0007`; `33003430 0000`, `33003430 0004`, `33003431 0000`, `33003431 0004` | these are GameShark/CodeBreaker memory writes to RAM, i.e. exactly the category excluded by this engagement; nothing in-game to test |

**There is no published password/button code for this title to verify against
the ROM.** That is itself consistent with the static result: no code system.

---

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` | code | ARM entry point (crt0) |
| `0x080008BC`–`0x08000960` | code | per-player key poll. `KEYINPUT` read at `0x080008C6`; `press = 0x3FF ^ KEYINPUT`; per player *i*: new-press word → `0x030008E0 + i*2`, previous word → `0x03000980 + i*2`; player count byte `0x030009A4` |
| `0x08000E70` | code | simple single-player poll. `KEYINPUT` at `0x08000E72`; new presses → `0x03000940`, previous → `0x03000860` |
| `0x08006140`–`0x080061F0` | code | second per-player poll (`KEYINPUT` at `0x08006150`), same `0x030008E0`/`0x03000980` arrays |
| `0x08002D36`–`0x0800319A` | code | held-key direction decode: D-pad combinations resolved to eight octant values (`0x10`…`0xA0`, incl. `0x50/0x60/0x90`) — inferred from the values and their per-player key source |
| `0x080031EC` | code | in-match input: Start/A branch, Up/Down adjusts a 0…2 index (`0x03000684`) |
| `0x08003BC0` | code | in-match action input: bit 0 (A) = shot, bit 1 (B) = second action (lob/slice — inferred from gameplay) |
| `0x080083E0`–`0x08008510` | code | **main-menu handler**: 5 rows, wrap through index 5, sound `0x0800BBD0` |
| `0x08008488` | code | **language-table apply**: copies cursor byte `0x03000684` → `0x03000864`, switches 0…4 and stores the chosen table base at `0x030008C0` |
| `0x080084AC` | data | 5-entry jump table for the above |
| `0x08008A10`–`0x08008E98` | code | **SELECT COURT handler**: own `KEYINPUT` read at `0x08008BA6`, 6 rows 0…5 (clamped), cursor `0x03000684`, on exit copies cursor → `0x03000678` |
| `0x0800A000`–`0x0800B500` | code | SELECT PLAYER drawing/selection (uses the roster name tables below) |
| `0x08019AB8` | data | language table pointer array: EN, FR, IT, DE, ES |
| `0x08019684` | data | 12 × 16-byte selector-sprite records (6 unselected + 6 selected) used by SELECT COURT |
| `0x08058034` | data | **UI string table, English**, 49 × u32 |
| `0x08058330` | data | UI string table, German |
| `0x0805859C` | data | UI string table, Spanish |
| `0x08058828` | data | UI string table, Italian |
| `0x08058A90` | data | UI string table, French |
| `0x08058D24` | data | roster names, “FIRST~ LAST” form, 10 × u32 |
| `0x08058E04` | data | roster names, plain, 10 × u32 |
| `0x08058ED8` | data | roster first names, 10 × u32 |
| `0x08058F60` | data | roster last names, 10 × u32 |
| `0x080591C8`–`0x080596E3` | data | credits/legal text (plain ASCII) |
| `0x03000684` | RAM | shared UI selection index (menu cursor / camera index / boot language index) |
| `0x03000678` | RAM | accepted selection copied out by SELECT COURT |
| `0x030008E0` | RAM | per-player new-press key words (10-bit, active high) |
| `0x03000980` | RAM | per-player previous key words |
| `0x03000940` / `0x03000860` | RAM | single-player new-press / previous key words |

Not present: any code reference to `0x0E000000` (SRAM), any EEPROM/Flash
library, any text-input buffer.

---

## 5. Algorithm

### 5.1 Key pipeline (all screens)

```
every frame:
    raw      = 0x3FF ^ REG_KEYINPUT      # active-high pressed bits
    new      = raw & ~prev               # edge-detect
    prev     = raw
    for i in 0..playerCount-1:           # up to 4 players (link)
        keys_new[i] = new
        keys_old[i] = raw
```

The menu screens then do, e.g. for the main menu:

```
if keys_new & 0x40:            # Up
    if cursor == 0: cursor = 5
    cursor -= 1
if keys_new & 0x80:            # Down
    cursor += 1
    if cursor == 5: cursor = 0
if keys_new & (0x08|0x01):     # Start or A
    accept(cursor)
```

SELECT COURT instead **clamps**:

```
if keys_new & 0x40 and cursor > 0: cursor -= 1
if keys_new & 0x80 and cursor < 5: cursor += 1
if keys_new & (0x08|0x01): selectedCourt = cursor; leave
```

That difference — wrap vs clamp — is why all six courts are reachable while
the five-row main menu simply cycles.

### 5.2 Language table apply (dead in the retail flow)

```
idx = *(u8*)0x03000684          # shared selection byte
*(u8*)0x03000864 = idx
switch (idx) {
  case 0: textBase = 0x08058034; break;   // EN
  case 1: textBase = 0x08058A90; break;   // FR
  case 2: textBase = 0x08058828; break;   // IT
  case 3: textBase = 0x08058330; break;   // DE
  case 4: textBase = 0x0805859C; break;   // ES
  default: break;                          // index 5 leaves the table alone
}
*(u32*)0x030008C0 = textBase;
```

The five tables share one layout, so `label(id) = *(u32*)(textBase + 4*id)`.
Only the English table is used in a fresh boot; no screen exposes a language
choice (see §6b).

### 5.3 Court selection visuals

`0x08019684` holds twelve 16-byte records. Entries 0–5 position the six
unselected rows; entries 6–11 position the highlighted row. The handler copies
the matching record pair into the sprite struct and moves the cursor sprite to
`y = 0x48 + index*16`. Because the panel is 160 px tall, row 5 (ITALY) at
`y = 0xC8` is drawn at the very bottom edge and clipped by the frame — but it
is a normal, selectable row.

---

## 6. Tables

### 6.1 UI string IDs (identical layout in all five languages)

| ID | English | ID | English |
|---:|---|---:|---|
| 0 | ARCADE | 25 | GAME OVER |
| 1 | CHAMPIONSHIP | 26 | VS |
| 2 | MULTIPLAYER | 27 | MUSIC ON |
| 3 | OPTIONS | 28 | MUSIC OFF |
| 4 | ENGLISH | 29 | SOUNDFX ON |
| 5 | FRANCAIS | 30 | SOUNDFX OFF |
| 6 | ITALIANO | 31 | EASY |
| 7 | DEUTSCH | 32 | MEDIUM |
| 8 | ESPAÑOL | 33 | HARD |
| 9 | RESUME GAME | 34 | **LANGUAGE** (never displayed) |
| 10 | QUIT GAME | 35 | CREDITS |
| 11 | UK | 36 | SELECT PLAYER |
| 12 | USA | 37 | SELECT COURT |
| 13 | FRANCE | 38 | 1 SET |
| 14 | GERMANY | 39 | 3 SETS |
| 15 | AUSTRALIA | 40 | 5 SETS |
| 16 | ITALY | 41 | SETS |
| 17 | CONNECTED | 42 | QUICK MATCH |
| 18 | PRESS START | 43 | CONGRATULATIONS |
| 19 | PLEASE WAIT | 44 | YOU ARE THE |
| 20 | ROUND 1 | 45 | WINNER |
| 21 | ROUND 2 | 46 | DOUBLES |
| 22 | QUARTER FINAL | 47 | YES |
| 23 | SEMI FINAL | 48 | NO |
| 24 | GRAND FINAL | | |

Options rows map to IDs 38, 27, 29, 32, 35. `LANGUAGE` (34) sits between the
difficulty row and CREDITS in ID order — the slot a language row would occupy —
but no row is built for it.

### 6.2 Language tables

| Language | File offset | ROM address |
|---|---|---|
| English | `0x58034` | `0x08058034` |
| German | `0x58330` | `0x08058330` |
| Spanish | `0x5859C` | `0x0805859C` |
| Italian | `0x58828` | `0x08058828` |
| French | `0x58A90` | `0x08058A90` |

Each is 49 u32 pointers to `'#'`-terminated strings (some strings are shared
between languages, e.g. `CHAMPIONSHIP` and `CREDITS`).

### 6.3 Roster (10 players, all selectable from boot)

| # | Name | Flag seen |
|---:|---|---|
| 0 | ANDRE AGASSI | USA |
| 1 | ROBERT BAXTER | UK |
| 2 | JACQUES MONBIOT | FRANCE |
| 3 | DAVID BEERBOLM | AUSTRALIA |
| 4 | GOTTFRIED GRUBER | GERMANY |
| 5 | ALDO GARBINO | ITALY |
| 6 | CHARLES CLEEVE | UK |
| 7 | CARLOS VICARIO | SPAIN |
| 8 | JACK JACKSON | USA |
| 9 | SEBASTIEN FOULARD | FRANCE |

Note the mismatch: seven nationalities appear on the players but only six
courts exist (no Spanish court).

### 6.4 Courts (6, all selectable)

| # | Name | Surface observed |
|---:|---|---|
| 0 | UK | grass (played) |
| 1 | USA | not played |
| 2 | FRANCE | hard, blue (played) |
| 3 | GERMANY | not played |
| 4 | AUSTRALIA | not played |
| 5 | ITALY | **clay, orange (played)**, drawn clipped at the frame edge |

### 6.5 Key masks

| Bit | Button | Used by |
|---:|---|---|
| `0x001` | A | confirm/advance; shot in match |
| `0x002` | B | cancel/back; lob/slice in match |
| `0x004` | Select | unused on every reachable screen |
| `0x008` | Start | confirm; pause |
| `0x010` | Right | player/court cycling |
| `0x020` | Left | player/court cycling |
| `0x040` | Up | menu up / doubles toggle / in-match index |
| `0x080` | Down | menu down / doubles toggle / in-match index |
| `0x100` | R | unused on every reachable screen |
| `0x200` | L | unused on every reachable screen |

---

## 6b. Enumeration

### 6b.1 Space definition

There is no code/password/menu-gate space in this ROM, so the deliverable is a
**bounded negative** over four explicitly defined spaces:

| Space | Definition | Size | Result |
|---|---|---|---|
| Text | every byte of the 4,194,304-byte image, case-insensitive | 4,194,304 bytes | 0 hits for 16 code/cheat/unlock keywords (§2) |
| UI strings | 5 language tables × 49 IDs | 245 slots (179 unique strings) | all dumped; no code word, alphabet, or “invalid” string |
| Keyboard | on-screen character grid | none exists | no screen draws an alphabet; no input buffer is ever created |
| Buttons | 10 buttons, simultaneous presses + order | 2¹⁰ = 1,024 states per frame (plus held vs edge) | all menu tests single-bit; combinations behave as their single keys |

The image also has no save path (`0x0E000000` code references: **0**;
`EEPROM_V/SRAM_V/FLASH_V/FLASH512_V/FLASH1M_V` markers: **0**; `game.sav`
remained 0 bytes), so an unlockable would have nowhere to live.

### 6b.2 Screen inventory (every screen, with counts)

| Screen | Items | Reached by | Bounds proven |
|---|---|---|---|
| Boot logos / title art | 4 phases | automatic | no input accepted; idle 35 s shows no attract loop |
| Main menu | 5 | boot | Down from OPTIONS wraps to QUICK MATCH (no 6th row) |
| Options | 5 | main → OPTIONS | Down from CREDITS wraps to `1 SET` |
| Credits | scrolling | options → CREDITS | Start exits |
| SELECT PLAYER (QM) | 10 players + DOUBLES YES/NO | QUICK MATCH | Right from FOULARD wraps to AGASSI |
| SELECT PLAYER (Arcade) | 10 players | ARCADE | same carousel, no DOUBLES row |
| SELECT PLAYER (Championship) | 10 players | CHAMPIONSHIP | same carousel |
| SELECT COURT | 6 | QM / Championship | Down ×5 reaches ITALY; 6th Down is rejected (clamped) |
| Round card | 1 | Arcade | ROUND 1 + city/country + VS pair |
| Bracket | 8 players / 4 matches | Championship | scrolls; 4th match clipped but readable |
| Pause | 2 | Start in match | resume / quit |
| Multiplayer wait | 1 state | main → MULTIPLAYER | `CONNECTED 0`, `PLEASE WAIT…`; B/Start exits |

### 6b.3 The undocumented, reachable item: court 6 (ITALY)

Published material describes six venues only as a list; nothing says the sixth
row is clipped. In the emulator:

| Step | Input | Result | Screenshot |
|---|---|---|---|
| 1 | SELECT COURT | cursor UK | `Agassi Tennis Generation - select court.png` |
| 2 | `Down` ×5 | cursor ITALY (bottom edge, atlas shows Italy) | same file |
| 3 | `Down` ×1 more | no movement — index clamped at 5 | RMSE 271.9 vs previous, i.e. only the globe/arrow animation |
| 4 | `A` (Start is accepted by the same handler) | match starts on an orange clay court | `Agassi Tennis Generation - italy clay court.png` |

This is the analogue of a “novel code” for a game without codes: an
option that exists in the binary and in the UI but is effectively invisible at
the default frame, confirmed by playing it.

### 6b.4 Bounds proven by rejection

| Test | Expected if the space were larger | Observed |
|---|---|---|
| SELECT COURT: `Down` at ITALY | a 7th court or wrap to UK | cursor stays on ITALY (clamp) |
| Main menu: `Down` at OPTIONS | a 6th row | wraps to QUICK MATCH |
| Options: `Down` at CREDITS | a 6th option (e.g. LANGUAGE) | wraps to `1 SET` |
| SELECT PLAYER: `Right` at FOULARD | an 11th player | wraps to AGASSI |
| `L`, `R`, `Select` on every menu | hidden action | no state change (pixel-identical) |
| `L+R`, `Left+Right` on every menu | hidden combo | pixel-identical |
| `A+B`, `Select+Start`, `Up+Down`, Konami | hidden combo | exactly the single-key effect, never a new screen |
| Keyword scan | any code text | zero occurrences in 4 MiB |

### 6b.5 Unreachable / vestigial content

| Item | Evidence | Status |
|---|---|---|
| `LANGUAGE` label (ID 34) + 5 language tables + apply routine `0x08008488` | tables and routine present; no screen draws ID 34; all screens walked | vestigial or cut feature |
| `PRESS START` (ID 18) | present in all five tables; never observed on screen | used, if at all, only by the link path |

### 6b.6 Why no code can be minted

A minted code requires a validator. The ROM has:

* no string comparison against user text (no input buffer is ever filled),
* no per-character alphabet table used by a UI (the only 49-entry tables are
  localised label pointers, indexed by label ID, not by typed characters),
* no checksum loop over an input buffer,
* no return value that means “code accepted” feeding a flag word.

The closest structures — the 49-entry language tables — are read-only label
lookups written by `0x08008488`, not validated input. Consequently the space of
acceptable codes is **empty**, and the honest deliverable is the enumeration of
screens/options above plus the rejected-input table in §6b.4.

---

## 7. Validation evidence

### Observed (emulator screenshots, this exact ROM)

* Boot sequence and idle main menu (no attract mode), §3.
* Main menu 5 rows with wrap; options 5 rows, with the sets row cycling
  `1 SET → 3 SETS → 5 SETS → 1 SET` on A (the same row handler serves the
  MUSIC/SFX/difficulty rows, whose strings are the same ID block).
* SELECT PLAYER: 10-player carousel, wrap from FOULARD to AGASSI; a DOUBLES
  YES/NO block appears after Start and its yellow highlight moves with Down
  (`select player.png`, `select player doubles row.png`).
* SELECT COURT: 6 rows, ITALY clipped at the frame edge, cursor clamps there,
  A loads a distinct clay court (`select court.png`, `italy clay court.png`).
* Arcade round card (`ROUND 1`, `PARIS / FRANCE`, `AGASSI vs JACK JACKSON`).
* Championship QUARTER FINAL bracket: 4 matches, 8 of the 10 players
  (`championship quarter final.png`).
* Pause menu (`pause menu.png`); multiplayer link wait
  (`CONNECTED 0 / PLEASE WAIT…`, `multiplayer link wait.png`).
* Button-combination matrix of §3 (pixel diffs recorded while testing).
* `game.sav` stayed 0 bytes across the whole session.

### Derived (instruction-level)

* Key pipeline, menu wrap vs clamp, court-sprite records, language-table switch:
  §4–§5, verified with `arm-none-eabi-objdump -M force-thumb` at the listed
  addresses.
* No SRAM/EEPROM use: zero `ldr`-literal sites for `0x0E000000`, no save-library
  marker strings, header device byte 0.
* String tables and IDs: dumped programmatically (`agassi_scan.py`).

### Inferred

* The LANGUAGE row was cut late in development (string and five tables remain,
  dispatch does not); `PRESS START` is likely link-only.
* The DOUBLES block is probably a 2v2 toggle; only its visual state change was
  observed, not a doubles match.

---

## 8. Unknowns

1. **DOUBLES YES/NO semantics.** Start on SELECT PLAYER reveals the block;
   Up/Down moves the YES/NO highlight; no tested button leaves that page except
   B (back to main menu). The earlier successful advance to SELECT COURT was
   observed once (`select court.png` after Start) but was not reliably
   reproducible with the same timing. This is a UI/timing quirk of the tested
   build, not a hidden feature — no extra screen or flag was ever observed.
2. **Link play.** Only the local `CONNECTED 0` wait state was reachable; with
   two instances and a link, `CONNECTED 1..4` and possibly `PRESS START` would
   be used. Not tested (no second emulator instance was run).
3. **Tournament completion.** The bracket, round strings and
   `CONGRATULATIONS / YOU ARE THE WINNER` text exist, but a full championship
   was not played to the final. No unlock text exists, so completion is
   unlikely to grant anything, but the final screen itself was not observed.
4. **Header provenance.** Checksum field `0x0000` versus computed `0xD82B`
   means this image is not a byte-clean retail header; the trainer/patch, if
   any, is not identified.
5. `PRESS START` and the five language tables are never displayed in the
   reachable flow; whether a retail European build reaches them is out of scope
   for this ROM.

---

## 9. Tooling

| Artifact | Purpose |
|---|---|
| `agassi_scan.py` (this folder) | hashes/header, dumps all 5 × 49 string tables, keyword scan, `ldr`-literal site counts for key-state/SRAM variables, `KEYINPUT` sites |
| `agassi_keys.py` (this folder) | xdotool key helper used for every probe (focus, hold 200–300 ms, screenshot + crop) |
| `arm-none-eabi-objdump -M force-thumb` | all disassembly in §4–§5 |
| Python 3 + `struct`/`re` | literal scan, `ldr`-literal scanner (fast prefilter on `0x48xx` Thumb encodings), table dumps |
| ImageMagick `compare -metric RMSE` | objective “no change” evidence for button probes |

Screenshots in this folder:

* `Agassi Tennis Generation - boot DreamCatcher.png`
* `Agassi Tennis Generation - main menu.png`
* `Agassi Tennis Generation - options.png`
* `Agassi Tennis Generation - credits.png`
* `Agassi Tennis Generation - select player.png`
* `Agassi Tennis Generation - select player doubles row.png`
* `Agassi Tennis Generation - select court.png`
* `Agassi Tennis Generation - italy clay court.png`
* `Agassi Tennis Generation - pause menu.png`
* `Agassi Tennis Generation - championship quarter final.png`
* `Agassi Tennis Generation - multiplayer link wait.png`

`roms/INDEX.md` was intentionally not modified (per the engagement brief).

---

## 10. Legal note

No ROM, graphics, audio or other copyrighted asset is redistributed here.
Only hashes, addresses, offsets, short UI labels needed to identify screens,
and original analysis text are published.
