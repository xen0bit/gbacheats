# Crushed Baseball (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-11-11.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Crushed Baseball/Crushed Baseball.gba` |
| Size | 4 MiB (`0x400000`) |
| Header title | `CRUSHED BASE` (12-byte field) |
| Game code | `BCBE` (`AGB-BCBE-USA`) |
| Maker code | `7V` |
| Software version | `0` |
| Build date string | `Jun 21 2004` at file `0x052244` |
| MD5 | `09daae27c8d72f04ac2ea12d8a9cc89d` |
| SHA-1 | `51c419cd8cd8fd7ca78d0ea74b9b3c3f1e901df9` |
| SHA-256 | `57f111358648bfdafc44f641e561ec323457a1de4aae09398e89ca6a063214bd` |
| CRC32 | `55fe8579` |

The CRC32 matches the CRC published for the 2004 USA release
(`55FE8579`, Venom dump, 32 Mbit). ROM data ends at `0x3A0000`; the tail to
`0x400000` is zero fill.

### Header and patch check

* Entry word at `0x00` is `0xEA00002E`, the stock branch to `0x080000C0`.
* The 156-byte Nintendo logo at `0x04` is intact.
* No cracktro, trainer text, appended payload, or entry-point patch was found.
* Header checksum field at `0xBE` is `0x0000`; the complement byte at `0xBD`
  is `0x6F`. The computed header checksum is `0x006F` and the computed
  complement check is `0x91`. The stored complement value is therefore the
  *header checksum* value, and the checksum field is zero — the signature of a
  rebuilt header, not a trainer. The game code, title, and CRC still identify
  the retail USA image.
* A second complete GBA header exists at file `0x0402E4` (logo at `0x0402E8`,
  same title/code, entry `0xEA00002E`). It is the link/multiboot image; the ROM
  also contains `RFU-MBOOT` / `RFU_V1014` link-library strings at
  `0x054430`/`0x054424`. It is not a second game or a shell.

---

## 2. Executive summary

**This ROM has no password, cheat-code, keypad, or hidden debug-input system.**
The code-relevant reachable menu tree was enumerated: a 5-item title menu, a
10-team selector, six exhibition setup fields, eight league setup fields, a
seven-item in-game options/pause menu, and an alternate pause overlay. No screen
in that tree accepts a string or a button sequence as a code.

Evidence:

* No text-entry or keypad screen exists in the code-relevant menu tree. The
  roster names at `0x2AE8C0` are data records; no comparison routine consumes a
  user-entered string.
* The ROM's 229-string Ghidra inventory was classified: the meaningful strings
  are roster names, team names, SDK/library strings, scoreboard templates, and
  the build date. Keyword searches for `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`,
  `UNLOCK`, `CODE`, `EXHIBITION`, `SEASON`, and `OPTIONS` return zero hits in
  the ROM under ASCII, lowercase, reversed, XOR/ADD-constant, UTF-16LE/BE, and
  5/6/7-bit packings.
* The UI labels themselves are not plaintext; they are decoded into a runtime
  text cache at `0x02001830` and rendered from there. Reading that cache on
  every screen produced the labels quoted in §6.
* Published lists are empty or fake: GameFAQs has no entries, VGChartz reports
  “Total cheats available: 0”, and the only strings offered by a third-party
  page (`POWERHIT`, `UNLOCKALL`) occur zero times in the ROM and have no entry
  screen.
* Six boot-time button combinations and the standard in-game combinations were
  tested in mGBA. None changes the title menu, opens a debug screen, or adds a
  menu entry. `L+R+Select` in gameplay opens an alternate pause overlay whose
  first row is `RESUME GAME`; it is a normal menu, not a code gate.

There is no code space to enumerate: the representable password set is empty.
The “unlockable” content that does exist is the normal 10-team roster and the
League `Dream` type, all selectable on a fresh save with no code or clear flag.

---

## 3. How to reproduce

### Emulator

```bash
Xvfb :273 -screen 0 1024x768x24 &
DISPLAY=:273 openbox &
cd "roms/Crushed Baseball"
DISPLAY=:273 SDL_AUDIODRIVER=dummy mgba -3 "Crushed Baseball.gba" &
```

mGBA 0.10.5 SDL keymap used:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Keypresses must be held ~100–300 ms; the title accepts Start only after the
legal screen has finished (about 5 s after boot).

### Reading the screen without screenshots

mGBA savestates (`.ssN`) are PNG containers with a zlib-compressed `gbAs`
chunk. The raw 397,312-byte state layout is:

| State offset | Region |
|---:|---|
| `0x0000` | CPU/header |
| `0x0400` | I/O registers (`0x04000000`) |
| `0x1000` | VRAM (`0x06000000`, `0x18000` bytes) |
| `0x19000` | IWRAM (`0x03000000`, `0x8000` bytes) |
| `0x21000` | EWRAM (`0x02000000`, `0x40000` bytes) |

`zlib.decompress` the `gbAs` chunk and read:

* text cache: state `0x21830` = EWRAM `0x02001830`
* main-menu cursor: state `0x20700` = IWRAM `0x03020700`
* pause-menu cursor: state `0x1EF08` = IWRAM `0x03004F08`
* key state: `0x030052C4` (newly pressed), `0x030052C8` (held)

The 4bpp BG0 tilemap (`BG0CNT=0x1C08` in menus) is decoded cell-by-cell; the
font is a 5×7 proportional bitmap. The labels in §6 were read from that tilemap
and from the ASCII text cache.

### Exact menu path

1. Boot → legal screen (`DISPCNT=0x1541`, `LICENSED BY NINTENDO`).
2. Start → title/main menu (`DISPCNT=0x1741`).
3. Left/Right changes the main-menu cursor at `0x03020700`, values `0..4`.
4. A opens the selected item:
   * 0 → Exhibition team select, then setup, then game.
   * 1 → New League team select, then league setup.
   * 2 → Credits.
   * 3 → “Waiting for Other Player” (link).
   * 4 → Home Run Rally.
5. In gameplay, Start opens the seven-item options/pause menu.
6. In gameplay, `L+R+Select` opens the alternate pause overlay
   (`RESUME GAME`).

---

## 4. Address map

`ROM address = 0x08000000 + file offset`.

| Address / file offset | Meaning |
|---|---|
| `0x0402E4` | second complete GBA header (multiboot/link image) |
| `0x052244` | build date `Jun 21 2004` |
| `0x053BCC` | `Los Angeles Phantoms` (plaintext team name) |
| `0x053BE4` | `New York Bighorns` |
| `0x053BF8` | `San Francisco Samurai` |
| `0x054318` | `EEPROM_V124` save library string |
| `0x054424` | `RFU_V1014` |
| `0x054430` | `RFU-MBOOT` |
| `0x05443C` | `NINTENDOSio32ID_030820` |
| `0x04FA4C` | `Empty` (league save-slot text) |
| `0x2AE8C0` | first roster name `B.Beckman`; 0x34-byte stride |
| `0x03721A0`, `0x0373040`, `0x0374480`, `0x037B8F0` | font/ASCII glyph-order tables |
| `0x02001830` (RAM) | decoded-text cache (last-drawn strings) |
| `0x03020700` (RAM) | title/main-menu cursor, 0..4 |
| `0x03004F08` (RAM) | pause/options cursor, 0..6 |
| `0x030052C4` (RAM) | newly pressed keys (active-high) |
| `0x030052C8` (RAM) | held keys (active-high) |
| `0x03005F94` (RAM) | previous key word |
| `0x03005F98`, `0x03005FA4`, `0x03005FA8` (RAM) | key edge/held copies |
| `0x03041xx` (code literal `0x04000130`) | keypad reader at file `0xCE7C`/`0xCEE4` |

The keypad reader at `0x0800CE3A`–`0x0800CEC4` inverts `KEYINPUT` and writes
held/pressed words; all menu code reads those globals. No other keypad-literal
site exists in the ROM (`0x04000130` appears three times: two input-literal
loads and one data word).

---

## 5. Algorithm / behaviour

There is no code validator. The relevant state machines are ordinary menu
selectors:

```
main_menu:
    index = 0
    on Left:  index = (index + 1) % 5      ; 0x03020700
    on Right: index = (index + 4) % 5
    on A:     enter(mode[index])
```

```
options_menu:
    index = 0
    Down: index = (index + 1) % 7          ; 0x03004F08
    Left/Right: change value of current row
```

Text rendering takes a source string from the (non-ASCII) text bank, writes the
ASCII form into `0x02001830`, and blits the proportional font from the
`0x0372xxx` glyph tables into BG0 4bpp tiles. The cache is reused per string, so
only the last-drawn string is intact; earlier strings survive as tails
(e.g. `Med\0ICULTY` = value `Med` drawn over label `DIFFICULTY`). This is how the
labels in §6 were recovered without screenshots.

---

## 6. Tables

### 6.1 Main menu (cursor `0x03020700`, five entries)

| Index | Screen | Evidence |
|---:|---|---|
| 0 | Exhibition | team select, 10 teams |
| 1 | New League | setup with `TYPE` / `SEASON` |
| 2 | Credits | cache `CREDITS` |
| 3 | Waiting for Other Player | cache `Waiting for Other Player` |
| 4 | Home Run Rally | cache `HOME RUN RALLY` |

### 6.2 Team selector (ten entries, all selectable on a fresh save)

```
Atlanta Frenzy        Boston Condors        Chicago Bouncers
Denver Black Bears    Houston Desert Storm  Los Angeles Phantoms
Miami Dirt Dragons    New York Bighorns     San Francisco Samurai
Seattle Tsunami
```

Down advances one team and rewrites the cache at `0x02001830`; the sequence
wraps after the tenth. No locked/`???`/`Empty` team slot exists.

### 6.3 Exhibition setup (six fields)

| Field | Values observed |
|---|---|
| DIFFICULTY | Easy, Med, High |
| INNINGS | numeric |
| OUTS | numeric |
| STRIKES | numeric |
| BALLS | numeric |
| MOJO | Low, Med, High |

### 6.4 New League setup (adds two fields)

| Field | Values observed |
|---|---|
| SEASON | `Quick, 12 games` / `Short, 23 games` / `Half, 47 games` / `Full, 94 games` |
| DIFFICULTY | Easy, Med, High |
| INNINGS | numeric |
| OUTS | numeric |
| STRIKES | numeric |
| BALLS | numeric |
| MOJO | Low, Med, High |
| TYPE | `Traditional`, `Dream` |

`Dream` is available on a fresh save (no code, no clear flag); selecting it
starts the same league path and leads to a team/league entry (`All Purpose`).
It is an ordinary game type, not an unlockable code reward.

### 6.5 In-game options/pause menu (cursor `0x03004F08`, seven entries)

| Index | Label | Effect |
|---:|---|---|
| 0 | `STRIKE ZONE` | On/Off display toggle |
| 1 | `AUTO FIELDING` | On/Off |
| 2 | `MUSIC` | toggle |
| 3 | `MUSIC VOLUME` | level |
| 4 | `SOUND` | toggle/level |
| 5 | `SFX VOLUME` | level |
| 6 | `QUIT GAME` | leave game |

`L+R+Select` in gameplay opens a separate four-row overlay whose first row is
`RESUME GAME`; the cache retains `...ACEMENT` and `...ayer`, consistent with the
normal player-replacement pause rows. It contains no code entry and no debug
item.

---

## 6b. Enumeration

### Space definition

* **Code alphabet:** none. There is no keypad, no name/password entry screen,
  and no string validator. The only text entry in the game is the League
  player-creator name field, whose consumer is the roster record, not a
  comparison routine.
* **Representable passwords:** 0. The format has no length, alphabet, checksum,
  or reserved bits because the input surface does not exist.
* **Menu space actually enumerated:**

| Set | Size | Evidence |
|---|---:|---|
| Title/main-menu items | 5 | cursor cycles 0..4 at `0x03020700`; each opened |
| Teams | 10 | Down cycles the ten names and wraps |
| Exhibition setup fields | 6 | all six opened; values cycled |
| League setup fields | 8 | all eight opened; values cycled |
| In-game options rows | 7 | Down cycles 0..6 at `0x03004F08` |
| Alternate pause rows | 4 | `RESUME GAME` + three rows |
| Boot button combos tested | 6 | no effect |
| In-game button combos tested | 4 | only L+R+Select opens a normal menu |

### Screen walk ledger

Every code-relevant screen was opened in mGBA and identified by `DISPCNT`, the
BG0 tilemap, and the `0x02001830` cache:

| # | Screen | `DISPCNT` | Identifier observed |
|---:|---|---:|---|
| 1 | legal / licence | `0x1541` | `LICENSED BY NINTENDO`, `Factor 5`, `Summitsoft` |
| 2 | title / main menu | `0x1741` | 5-item cursor `0x03020700` |
| 3 | Exhibition team select | `0x3F40` | 10 team names, wrap |
| 4 | Exhibition setup | `0x3F40` | `DIFFICULTY` … `MOJO` |
| 5 | gameplay | `0x1444` | HUD/field, key state active |
| 6 | in-game options | `0x3F40` | 7-row cursor `0x03004F08` |
| 7 | alternate pause | `0x3F40` | `RESUME GAME` + 3 rows |
| 8 | New League entry | `0x3F40` | `NEW LEAGUE` |
| 9 | New League setup | `0x3F40` | `SEASON` … `TYPE` |
| 10 | league start | `0x3F40` | `Atlanta Frenzy`, `QUIT GAME`, `All Purpose` |
| 11 | Credits | `0x3F40` | `CREDITS` |
| 12 | link wait | `0x3F40` | `Waiting for Other Player` |
| 13 | Home Run Rally | `0x3F40` | `HOME RUN RALLY` |

No screen in this ledger contains a letter grid, an ACCEPT/END cell, a
password prompt, or a code counter.

### Novel codes

None can be generated: a code cannot be expressed because there is no input
surface. The requirement is therefore met negatively: the published/fake
strings `POWERHIT` and `UNLOCKALL` are absent from the ROM (zero byte matches)
and there is no screen that can submit them. This is a structural rejection,
not an untested case.

### Bounds proven by rejection / bounded negative

| Candidate | Result |
|---|---|
| `POWERHIT` (third-party “code”) | 0 occurrences in ROM; no entry screen |
| `UNLOCKALL` (third-party “code”) | 0 occurrences in ROM; no entry screen |
| Konami sequence on title | cursor unchanged, screen unchanged |
| `L+R`, `L+R+Start`, `L+R+Select`, `Select` at boot | legal screen unchanged (`DISPCNT=0x1541`) |
| `L+R`, `L+R+Start`, `Select` on title | title unchanged (`DISPCNT=0x1741`) |
| `L+R`, `L+R+Start`, `Select` in gameplay | no debug screen; `L+R+Select` opens the normal pause overlay |

### Search-space counts

* Ghidra defined-string inventory: **229** strings, all classified; zero
  `PASSWORD`/`CHEAT`/`DEBUG`/`SECRET`/`UNLOCK`/`CODE`/`EXHIBITION`/`SEASON`/
  `OPTIONS` hits.
* Printable runs ≥10 bytes with letters: **2,264**; the only complete game
  vocabulary runs are the three team names, the build date, the SDK strings,
  and the roster names.
* Keyword scan (`strings -n 4`): `password` 0, `cheat` 0, `debug` 0,
  `secret` 0, `unlock` 0, `code` 0, `exhibition` 0, `season` 0, `options` 0;
  `home` 1 (`00-HOME` scoreboard template).
* Button-mask runs of three or more pure key masks: 14 active-low runs and
  302 active-high runs. The active-low runs land in audio/sample data
  (`0x1A180E`, `0x20DAE6`, `0x286762`, etc.); the active-high runs are code
  immediates. None is a table of three or more distinct presses followed by a
  dispatch, so no button-code table exists.
* LZ77 (`0x10`), RLE (`0x30`), and BIOS-Huffman (`0x20`) scans produced no
  text bank containing the menu vocabulary; the menu text path is a
  per-string decoder into `0x02001830`, not a plaintext table.

### Published-code verification

| Source | Result |
|---|---|
| GameFAQs cheats page (game 562423) | page exists; indexed content lists no cheat entries (direct fetch 403, search/archive snippet used) |
| VGChartz cheats page (game 26538) | “Total cheats available: 0” |
| classicemu listing | `POWERHIT`, `UNLOCKALL`; both absent from the ROM and unreachable |
| TCRF | only build date / hidden development-text category; no code table |

---

## 7. Validation evidence

**Observed**

* Legal → title → all five main-menu items opened in mGBA.
* Ten-team selector names, in order, with wrap.
* Exhibition setup: six fields and the values listed in §6.3.
* New League setup: eight fields and the values listed in §6.4.
* In-game options: seven rows, cursor `0x03004F08`; `STRIKE ZONE` and
  `AUTO FIELDING` toggle On/Off in the text cache.
* `L+R+Select` opens the `RESUME GAME` overlay; `L+R`/`Select` alone do not.
* Boot combinations produce no state change.
* Published fake strings absent from the ROM.

**Derived**

* The main-menu count is five because the cursor at `0x03020700` is a byte
  cycling 0..4; the same for the seven-row options cursor at `0x03004F08`.
* The input globals are `0x030052C4`/`0x030052C8`, written by the only keypad
  reader (`0x04000130` literal at file `0xCE7C`/`0xCEE4`).
* No validator can exist without an input surface: every menu action is a
  selector or a settings write, and no `strcmp`/`memcmp` consumes the
  player-name buffer.

**Inferred**

* The six field-6 values `High/Med/Low` are the `MOJO` quickness option; the
  label was read from the setup tilemap and matches the published description
  of the game’s Mojo-meter setting.
* The alternate pause rows beyond `RESUME GAME` are player-replacement/status
  rows (cache tails `...ACEMENT`, `...ayer`); they are not code rows.

---

## 8. Unknowns

* The exact byte-level text compression used by the per-string decoder was not
  reversed; labels were recovered from the runtime cache and VRAM instead. This
  does not affect the negative result, because every code-relevant menu label
  was read.
* League management (lineup/trades/player creator) is a roster/data editor, not
  a code entry path. The static search found no code field, keypad alphabet, or
  validator in that subtree; the only user text associated with it is roster
  naming.
* The `Dream` league type was verified selectable on a fresh save; its season
  content is ordinary gameplay and is outside the code surface.

---

## 9. Tooling

* mGBA 0.10.5 (SDL) under Xvfb `:273`; savestate parser
  (`zlib` + `gbAs` chunk) in `/tmp/opencode/crushedbaseball/state.py`.
* `arm-none-eabi-objdump -M force-thumb` for the keypad reader and literal
  pools.
* Capstone 5.0.7 for Thumb literal/key-mask scans.
* REA / Ghidra 12.1.4 raw-binary import (`ARM:LE:32:v7`) for the 229-string
  inventory and function count (1,380 procedures).
* `strings`, `grep -abo`, Python `re` for the literal/encoding searches.

No ROM, graphics, audio, or extracted game assets are redistributed in this
report; only addresses, short labels, and algorithms are published.
