# 3-in-1 Sports Pack: Paintball Splat! / Dodgeball: Dodge This! / Big Alley Bowling (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/3-in-1 Sports Pack: Paintball Splat! - Dodgeball Dodge This! - Big Alley Bowling/3-in-1 Sports Pack: Paintball Splat! - Dodgeball Dodge This! - Big Alley Bowling.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `3N1SPORTSPAK` |
| Game code | `B3NE` |
| Maker code | `5G` (Majesco / DSI) |
| Software version | 0 |
| Fixed byte `0xB2` | `0x96` |
| Entry branch | `0xEA00002E` → `0x080000C0` |
| MD5 | `eedd67a815e798e19159237a4d151d1a` |
| SHA-1 | `82a01a4395146f01b235b1adcb266abc96fc26ea` |
| SHA-256 | `770278d2970ae989eef2161bfbf2151428e07fc9e78210cd4217c7f3db3fd799` |

`file` reports `Game Boy Advance ROM image: "3N1SPORTSPAK" (B3NE5G, Rev.00)`.

### Embedded GBA headers (multicart scan)

Scanning the whole 8 MiB for the 156-byte Nintendo logo produced four headers. Each logo hit is at
header offset `+4`; every image is preceded by `0xFF` padding (checked 32 bytes before each base).

| File offset | ROM address | Title (12 B) | Code | Maker | `0xBC` | Entry branch | Complement | Header checksum | Image extent |
|---:|---:|---|---|---|---:|---|---:|---:|---|
| `0x000000` | `0x08000000` | `3N1SPORTSPAK` | `B3NE` | `5G` | 0 | `EA00002E` → `0x080000C0` | `0x54` | `0x0000` | `0x000000–0x0300FF` (shell, 192.25 KiB) |
| `0x030100` | `0x08030100` | `PAINTBALLSPL` | `    ` | `5G` | 0 | `EA00002E` → `0x080301C0` | `0xCF` | `0x0000` | `0x030100–0x2FFFFF` (2.81 MiB) |
| `0x300000` | `0x08300000` | `DODGEBALLDOD` | `    ` | `5G` | 0 | `EA00002E` → `0x083000C0` | `0x00` | `0x0000` | `0x300000–0x5E7FFF` (2.90625 MiB) |
| `0x5E8000` | `0x085E8000` | *(blank)* | `\0\0\0\0` | `01` | 0 | `EA00002E` → `0x085E80C0` | `0xF0` | `0x0000` | `0x5E8000–0x7FFFFF` (2.09 MiB) |

All four header **complement** bytes are correct (verified by recomputing them), but every
**header checksum** field is `0x0000` (the recomputed values are `0x0AF2`, `0xEB12`, `0xCA33`,
`0xDE21`), i.e. the repacker zeroed the checksums. The pack still boots because the shell jumps
straight to each image entry.
The Paintball image does **not** follow the `+0x1C8 = main` convention: at `0x080301C8` there is a
`ldr sp,[pc,#40]`, and its crt0 at `0x080301C0` branches through the pointer at `0x080302A8`.
Dodgeball's `+0x1C8` word is `0x083001D1` and Bowling's is `0x085E8331` (both valid Thumb pointers).

## 2. Executive summary

**There is no in-game cheat system in this cartridge.** None of the three games contains a
password/code entry, a cheat menu, a debug menu, a level/stage select, a sound test, an unlock
code, or a button-sequence cheat. The earlier triage line "No in-game cheats" is confirmed by
enumeration and by bounded searches, not by assumption.

What the pack actually contains:

* A **multicart shell** at `0x08000000` that draws the three panels and writes a warm-boot word
  before jumping to one of three absolutely-linked images.
* **Paintball Splat** (`0x08030100`), **Dodgeball: Dodge This!** (`0x08300000`) and
  **Big Alley Bowling** (`0x085E8000`), each with a handful of ordinary menus.
* Exactly **one text-entry widget in the whole 8 MiB**: Big Alley Bowling's
  `LOAD TOURNAMENT` name field. It accepts 15 characters from `0-9` and `A-Z` and behaves as a
  save-slot name lookup (inferred; see §7) — not a password field. Entering the two "published" codes (`PAINT123`,
  `BOWLINGX`) has no effect at all, and neither string exists anywhere in the ROM. They are
  auto-generated SEO filler on a ROM-hosting site, not real cheats.
* No key-mask table or sequence comparison in any image. All ten `KEYINPUT` load sites are generic
  held/pressed helpers. The Konami sequence is absent in every encoding tested (8/16/32-bit,
  active-high, active-low, inverted).

Because no code space exists, no novel code can be minted and no validator can be reimplemented.
The enumeration deliverable is therefore the complete menu/state space, the complete text-bank
inventory, and the rejection tests recorded in §6b.

### Published "codes" and their status

| Source | Claim | ROM check | Emulator check |
|---|---|---|---|
| classicemu.com (many language mirrors) | `PAINT123` unlocks all paintball colour skins | Literal `PAINT123` occurs **0 times** in 8,388,608 bytes (`PAINT` only at the header title) | Typed into the only text field: `OK` does nothing (screenshot `150/152/153`) |
| classicemu.com | `BOWLINGX` enables Big Alley Bowling turbo mode | Literal `BOWLINGX` occurs **0 times**; `TURBO` occurs **0 times** | Typed into the only text field: `OK` does nothing (`155/156`) |
| GBAtemp cheat-file list | `.CHT` files #2345 (EU) / #2553 (US) for this pack | n/a — these are GameShark/CodeBreaker **memory patches** | Out of scope (not in-game codes) |

## 3. How to reproduce

Tools: `mgba` 0.10.5 (SDL frontend), `Xvfb`, `openbox`, `xdotool`, `scrot`/ImageMagick `import`,
`arm-none-eabi-objdump`, Python 3 + Capstone, Ghidra 12.1.4 (REA) for one cross-check.

```bash
Xvfb :119 -screen 0 1280x960x24 &
DISPLAY=:119 openbox &
cd /tmp/opencode/sports3
DISPLAY=:119 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 "<path to the .gba>" &
W=$(DISPLAY=:119 xdotool search --name mGBA | tail -1)
DISPLAY=:119 xdotool windowfocus "$W"
DISPLAY=:119 import -window "$W" shot.png     # 720x480 = 3x GBA 240x160
```

Default mGBA SDL keymap used throughout: **A=`x`**, **B=`z`**, **L=`a`**, **R=`s`**,
**Start=`Return`**, **Select=`BackSpace`**, d-pad = arrow keys. Hold 140–400 ms; a 10 ms tap is
sometimes dropped by these menus.

Savestates: `Shift+F1` saves slot 1, `F1` loads it. A state on the shell selector makes every
experiment below a few keypresses.

### Exact paths

* **Shell** (`0x08000000`): all three panels bright at boot. `Right`/`Left` cycles the highlight
  (Bowling → Dodgeball → Paintball); `Start` boots the highlighted image. The highlight is a
  brightness change only (shots `44→45→46`).
* **Paintball Splat**: `Start` at title → `NEW GAME` / `OPTIONS`.
  `NEW GAME` → `CHOOSE GAME MODE` (Single/Multi) → `CHOOSE TEAM` (4 helmets) →
  `PLAYER SELECT` (4 portraits) → `CHOOSE GAME STYLE` (Capture the Flag / Search and Eliminate)
  → mode options (`TIMED GAME` / `PLAY TO CHOSEN SCORE`) → time `5/10/15/20` **or** flags
  `5/10/15/20` → `CHOOSE MAP` (`SUMMER`, `FALL`, `URBAN`) → match.
  `MULTI PLAYER` → `INSERT THE GAME BOY ADVANCE GAME LINK CABLE` (no further single-cart screen).
  In-match `Start` → pause: `CONTINUE / MUSIC ON|OFF / SOUND ON|OFF / RESTART / QUIT`.
* **Dodgeball: Dodge This!**: `Start` at title (or `A`) → `GAME SETTINGS`
  (`ASPHALT|GYMNASIUM` with Left/Right, `MUSIC ON|OFF`, `SOUND ON|OFF`) → `SELECT PLAYERS`
  (Up/Down swaps the 7-character roster, Left/Right adds to your/their 3 slots) → match.
  In-match `Start` → `CONTINUE / MUSIC ON|OFF / SOUND ON|OFF / RESTART / QUIT`, then
  `ARE YOU SURE / NO / YES`.
* **Big Alley Bowling**: `Start` at title → main menu.
  With `1 PLAYER`: `1 PLAYER` (Left/Right cycles 1–4), `LOAD TOURNAMENT`, `START TOURNAMENT`,
  and the lane selector. With 2–4 players the tournament items disappear and only the player
  count and lane selector remain.
  Down to the lane row and Left/Right cycles **five** venues: `BLACKLIGHT BOWLING`,
  `SKYWORKS LANES`, `FUTURE LANES`, `DUDE LANES`, `STARLITE LANES`.
  `LOAD TOURNAMENT` → 15-character name entry (36 keys `0-9 A-Z`, a `←` delete key, `OK`).
  `START TOURNAMENT` → advice screen ("must bowl 2 games and finish with an average of 100 or
  better") → `QUALIFYING ROUND 1`.
  In-match `Start` pauses; `Select` opens the `OPTIONS` overlay
  (`MUSIC`/`SOUND`/`AMBIENT` sliders, `START NEW GAME`, `EXIT GAME`, "PRESS 'A' BUTTON TO EXIT").

### Code tests

Enter `PAINT123`, then `BOWLINGX`, in the Bowling `LOAD TOURNAMENT` field and press `OK`.
Expected (and observed): the field keeps the text, the screen does not change, and no unlock or
message appears. For the field bound, fill it (`AEIOU` + `1234567890` = 15) and press one more
key: the 16th character is rejected.

## 4. Address map

`rom = 0x08000000 + file_offset`. All offsets are file offsets unless marked ROM.

| File offset | ROM address | Meaning |
|---:|---:|---|
| `0x000000` | `0x08000000` | Shell header + ARM entry |
| `0x0000C0` | `0x080000C0` | Shell crt0 |
| `0x000280` | `0x08000280` | Shell main loop / frame tick |
| `0x00044E–0x000454` | `0x0800044E` | `ldr r0,=0xA5A5A5A5; str r0,[0x03000000]` (warm-boot word) |
| `0x000456` | `0x08000456` | loads selector state `0x03000008`, compares 0/1/2 |
| `0x000468` | `0x08000468` | loads game table pointer `0x0802BA70` |
| `0x000496` | `0x08000496` | `ldr r0,[r0]; bl 0x080007F4` — indirect jump to image entry |
| `0x0004AC–0x0004FE` | `0x080004AC` | `Right` (`0x10`)/`Left` (`0x20`) change selector 0–2, wrap, redraw |
| `0x00054E` | `0x0800054E` | Shell `KEYINPUT` (`0x04000130`) read; builds pressed/held |
| `0x02BA6C` | `0x0802BA6C` | Jump table: `08000000, 085E8000, 08300000, 08030100` (self, Bowling, Dodgeball, Paintball) |
| `0x030100` | `0x08030100` | Paintball header; crt0 `0x080301C0`; main via `0x080302A8` |
| `0x03D0BC–0x03D37C` | `0x0803D0BC` | Paintball UI text bank (mode/team/style/map/link text) |
| `0x18A1C0–0x18A280` | `0x0818A1C0` | Paintball pause text (`continue`, `music on`, … `you lose`) |
| `0x18CB40` | `0x0818CB40` | Paintball ASCII→tile glyph map (132 bytes) |
| `0x035F10, 0x037776, 0x0377AA, 0x03783A, 0x037BF0, 0x037C28` | — | Paintball `KEYINPUT` load sites |
| `0x300000` | `0x08300000` | Dodgeball header; main pointer `0x083001D1` |
| `0x398754–0x398960` | `0x08398754` | Dodgeball UI text bank |
| `0x3B8798–0x3B8829` | `0x083B8798` | Dodgeball pause text |
| `0x3DBC90` | `0x083DBC90` | Dodgeball glyph map |
| `0x303B00, 0x303B62` | — | Dodgeball `KEYINPUT` load sites |
| `0x5E8000` | `0x085E8000` | Bowling header; main pointer `0x085E8331` |
| `0x5F5588–0x5F6140` | `0x085F5588` | Bowling game text (rounds, scoring terms, lanes, frames) |
| `0x6A78A4–0x6A7AB0` | `0x086A78A4` | Bowling menu text (`OPTIONS`, `LOAD TOURNAMENT`, high-score text) |
| `0x6A7B80` | `0x086A7B80` | Bowling glyph map; loaded by `LDR` at `0x086A7A2E` and `0x086A7A42` |
| `0x5EF222` | `0x085EF222` | Bowling `KEYINPUT` load site |
| `0x5F1E00–0x5F2152` | `0x085F1E00` | Bowling main-menu input/draw (player count, item index, lane index) |

### RAM used by the menus (observed/derived from the disassembly)

| Address | Width | Meaning |
|---|---:|---|
| `0x03000008` | u16 | Shell selector index (0–2) |
| `0x03000010` | u16 | Pressed-this-frame key bits (active high) |
| `0x03000004` | u16 | Previous/held key state |
| `0x03000C58` | u32 | Bowling player count 1–4 (`0x085F1E0A`) |
| `0x03002218` | u32 | Bowling main-menu item index 0–3 (`0x085F1E96`) |
| `0x03000A60+0x12` | u16 | Bowling lane index 0–4 (`0x085F1EA0`, `0x085F212A`) |
| `0x030013F0` | 2 B | ASCII digit buffer for the menu's "1/2/3/4 PLAYERS" label |

The menu code at `0x085F1E96` proves the item mapping: item `3` adjusts an index in the range
0–4 with Left/Right (the lane selector). The renderer at `0x085F204C` prints `PLAYER`/`PLAYERS`
and at `0x085F207C` prints the `LOAD TOURNAMENT`/`START TOURNAMENT` pair only while the player
count is 1; the item index selects which row is highlighted.

### Text and alphabet tables

The apparent "alphabet" strings found by a naive scan (`ABCDEFGHIJK0123456789`, `wvut…`) are not
password alphabets. They are the byte values of a **132-byte ASCII→tile map** (index ASCII
`0x20`–`0xA3`, three copies: `0x0818CB40`, `0x083DBC90`, `0x086A7B80`; the Bowling copy is the
one whose address is loaded by the renderer. The vowel entries land on tiles that the same VRAM
bank uses for UI icons, which is why the name-entry keyboard draws five of
its letter keys as icons: the tiles for `A`,`E`,`I`,`O`,`U` are shared with UI icon graphics.
Typing `AEIOU` into the name field produces, in order, a house, right arrow, down arrow, square
and left arrow (screenshot `202`); typing `PAINT123` produces `P`, house, down-triangle, `N`,
`T`, `1`, `2`, `3` (`150`). The stored characters remain ASCII letters, which is why `N` and
`T` render normally.

## 5. Algorithm / pseudocode

### 5.1 Shell dispatcher

```
state = 0x03000008          ; 0,1,2
if (pressed & RIGHT) state = (state + 1) mod 3
if (pressed & LEFT)  state = (state + 2) mod 3
draw_panel(state)           ; dims the other two panels

on START:
    *(u32*)0x03000000 = 0xA5A5A5A5      ; warm-boot word
    target = [0x0802BA70 + state*4]     ; 085E8000 / 08300000 / 08030100
    jump_to(target)                     ; ldr r0,[r0]; bl 0x080007F4
```

### 5.2 Input reader (all images)

```
raw   = *(u16*)0x04000130       ; active low, 10 buttons
held  = ~raw & 0x03FF
pressed = held & ~previous
previous = held
```

Each of the ten load sites is followed by this pattern and by menu tests against
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080,
R=0x100, L=0x200`. No site compares against a stored sequence; none increments a sequence index.

### 5.3 Bowling main menu (example of the densest menu)

```
player count (0x03000C58) changed by Left/Right while the top row is selected (1..4, wrap)
item index   (0x03002218) changed by Up/Down (0..3 = player row / LOAD / START / LANES)
if item == 1: render "LOAD TOURNAMENT" + "START TOURNAMENT"
if item == 3: lane (0x03000A60+0x12) = (lane ± 1) mod 5 on Left/Right
on Start/A: advance to the selected screen; player>1 hides the tournament items
```

### 5.4 Code validator

**None exists.** There is no routine in any image that:
* reads a fixed-length character buffer and compares it to a table of codes,
* decodes an alphabet into bit fields,
* computes a checksum over entered characters,
* or sets an unlock flag from an entered string.

The only buffer reader is the Bowling tournament-name field. Its `OK` handler produces no state
change for an unmatched name (and no unlock path was found anywhere); it has no rejection message.

## 6. Tables

### 6.1 Menu inventory (all values observed on screens)

| Game | Screen | Entries/values |
|---|---|---|
| Shell | Game select | 3 panels; Start boots; Left/Right cycles |
| Paintball | Main | NEW GAME, OPTIONS |
| Paintball | Options | MUSIC ON/OFF, SOUND ON/OFF |
| Paintball | Mode | SINGLE PLAYER, MULTI PLAYER (→ link-cable prompt) |
| Paintball | Team | Red, Blue, Yellow, Green |
| Paintball | Player select | 4 portraits |
| Paintball | Style | CAPTURE THE FLAG, SEARCH AND ELIMINATE |
| Paintball | CTF options | TIMED GAME, PLAY TO CHOSEN SCORE |
| Paintball | Time | 5, 10, 15, 20 minutes |
| Paintball | Flag captures | 5, 10, 15, 20 |
| Paintball | Map | SUMMER, FALL, URBAN |
| Paintball | Pause | CONTINUE, MUSIC ON/OFF, SOUND ON/OFF, RESTART, QUIT |
| Dodgeball | Settings | court ASPHALT/GYMNASIUM; MUSIC ON/OFF; SOUND ON/OFF |
| Dodgeball | Select players | 7-player roster, 3 slots per team |
| Dodgeball | Pause | CONTINUE, MUSIC ON/OFF, SOUND ON/OFF, RESTART, QUIT, ARE YOU SURE/NO/YES |
| Bowling | Main (1P) | players 1–4, LOAD TOURNAMENT, START TOURNAMENT, lane selector |
| Bowling | Main (2–4P) | players 1–4, lane selector only |
| Bowling | Lanes | BLACKLIGHT BOWLING, SKYWORKS LANES, FUTURE LANES, DUDE LANES, STARLITE LANES |
| Bowling | LOAD TOURNAMENT | 15-char name field, keys `0-9 A-Z`, delete, OK |
| Bowling | Tournament advice | 1 text screen |
| Bowling | Options overlay | MUSIC, SOUND, AMBIENT, START NEW GAME, EXIT GAME |
| Bowling | Pause | PAUSED (no menu) |

### 6.2 Classified text search

Case-insensitive substring counts over the whole file, split by image. `0` means the exact
substring does not occur anywhere in that image, not merely in a text bank.

| Term | Shell | Paintball | Dodgeball | Bowling | Classification of any hit |
|---|---:|---:|---:|---:|---|
| `password`, `passwd`, `passcode` | 0 | 0 | 0 | 0 | — |
| `cheat` | 0 | 0 | 0 | 0 | — |
| `code` | 0 | 0 | 0 | 0 | — |
| `debug` | 0 | 0 | 0 | 0 | — |
| `secret` | 0 | 0 | 0 | 0 | — |
| `unlock` | 0 | 0 | 0 | 0 | — |
| `hidden` | 0 | 0 | 0 | 0 | — |
| `stage select`, `level select` | 0 | 0 | 0 | 0 | — |
| `sound test`, `credits`, `staff` | 0 | 0 | 0 | 0 | — |
| `mot de passe`, `passwort`, `contraseña` | 0 | 0 | 0 | 0 | — |
| `bonus` | 0 | 0 | 0 | 2 | Bowling scoring labels `BONUS HEADPIN`, `BONUS ` |
| `option` | 0 | 2 | 2 | 1 | Ordinary options menus (`options`, `set game options`, `OPTIONS`) |
| `continue` | 0 | 1 | 1 | 0 | Pause-menu label |

The complete text-bank label sets were also extracted: the shell has **no ASCII labels at all**
(its title/panel art is drawn from graphics and no string table was found); Paintball's main bank has 36 UI strings plus 13 pause
strings; Dodgeball's has 32 UI + 11 pause; Bowling has three banks with 6, 103 and 31 strings.
The 103-string Bowling bank also holds scoreboard/display data (scoring names, five lane names,
ball weights `6/8/10/12/14/16 LBS`, colours `GREEN/RED/BLACK`, a 30-name player pool, difficulty
`EASY/FAIR/HARD/PRO`, `AI 1–4` and `FRAME 1–10`). None of those strings is a code, a prompt, or an
unlock; the UI labels map one-to-one onto the screens in §6.1 and the rest are drawn in the
scoreboard/tournament HUD.

### 6.3 Published codes

| Code | In ROM? | Field accepted it? | Effect |
|---|---|---|---|
| `PAINT123` | No (0 hits) | Yes, as text (`150`) | None (`152`, `153`) |
| `BOWLINGX` | No (0 hits) | Yes, as text (`155`) | None (`156`) |

### 6.4 Button-mask checks

* Konami sequence searched as `u8`, `u16`, `u32`, active-high
  (`40 40 80 80 20 10 20 10 02 01`) and active-low (`3BF 3BF 37F 37F 3DF 3EF 3DF 3EF 3FD 3FE`):
  **0 hits** in all four images.
* All maximal `u16` runs of length ≥ 5 whose values are drawn only from the ten button masks:
  372 runs (Paintball), 22 (Dodgeball), 220 (Bowling). Only one run is referenced by a data
  pointer: `0x0849D276` (Dodgeball), pointed at by the table at `0x083005B0`. It sits inside
  sprite/motion data (`0x0849D256` contains coordinate pairs `0x0074,0x0051,0x009C,0x0080,…`)
  and is copied as data by `0x083005A0`, never compared with `KEYINPUT`. All other runs are
  graphics/audio bytes.
* All ten `KEYINPUT` load sites were disassembled. Each computes held/pressed and branches on
  individual masks (menu navigation, pause, throw, dodge). No multi-step progress counter, no
  sequence table, no "code accepted" flag.
* Single-key gate probes: `Select`, `L` and `R` on the shell selector and on all three title
  screens produce a pixel-identical frame (compare metric 0, shots `240–257`).
* In-game combination probes at menus and during play: `L+R+Start`, `A+B+Start`,
  `Select+Start`, `A+B+Start+Select`, `L+R+Start+Select`. Results were only the ordinary
  Start/A behaviour (start a match, pause). No hidden screen, unlock or counter.

## 6b. Enumeration

**Space definition.** Number of code systems: **0**. Consequently:

* alphabets: none for codes. The only input alphabet in the pack is the name-entry keyboard
  `0-9` + `A-Z` (36 keys) with a 15-character field cap.
* lengths/fields/checksums/reserved bits: not applicable — there is no packed code word.
* lookup tables: the only tables found are text banks, three 132-byte ASCII→tile glyph maps,
  menu jump tables, and sprite/sound data. No table of accepted strings exists.

**Search space actually covered.** 8,388,608 bytes (all four images), 20 cheat-related substrings
per image (§6.2), all NUL-terminated text-bank labels, 6 Konami encodings, 614 button-mask
runs, 10 `KEYINPUT` load sites, and every reachable menu and option value (§6.1). This is the bound
on the negative claim: no code system exists in *this* image within *that* space.

**Novel codes.** None were minted because there is nothing to mint. This is the one engagement
shape where §0.2's "generate an unpublished code" requirement is vacuous; the equivalent
deliverable is the exhaustive screen/state enumeration plus the published-code rejection tests.
No generated string was withheld: every string that had to be tested is shown in §3/§6.3.

**Bounds proven by rejection.**

1. `PAINT123` and `BOWLINGX` are absent from the ROM (`grep`-equivalent literal search over 8 MiB)
   and were typed into the only text field; `OK` left the screen unchanged (`152/153`, `156`).
2. The name field accepts 15 characters and **rejects the 16th**: after `AEIOU` + `1234567890`
   (15 cells filled), one more `A` press changes nothing (`204`).
3. A 1-character name (`0`) and an 8-character name (`PAINT123`) submitted with `OK` produce no
   transition; the 1-character case clears the field, consistent with a failed name lookup.
4. No option in any menu produces an unlock, counter, extra life, extra ammo, new character,
   new lane beyond the five, or new map beyond the three. Paintball's in-match HUD starts at the
   same 99 paintballs and full life bar on every mode (observed `61`); Dodgeball's HUD starts at
   0–0 (`84`).

## 7. Validation evidence

**Observed (emulator screenshots in `/tmp/opencode/sports3/shots/`):**

* Shell selector and the three panels: `44`, `45`, `46`.
* Paintball: title `50`; main `51`; options `52`; mode `53`; team `54`; player select `55`;
  style `56`; CTF options `57`; time `58`; flag captures `191`; map `215` (URBAN);
  multi-player link prompt `135`; match `61`; pause `62`.
* Dodgeball: title `71`; settings `72`; court toggle `94`; select players `77`; team filled `83`;
  match `84`; pause `85`; quit confirm `91`; title return `92`.
* Bowling: title `111`; main `112`; 4-player variant `116`; 2-player `118`; lane selector
  `182`/`185`/`186`/`187`; name entry `140`; typed `AEIOU` `202`; typed `PAINT123` `150`;
  `OK` no-op `153`; typed `BOWLINGX` `155`/`156`; 15-char cap `204`; tournament advice `20`;
  qualifying round `21`; pause `22`; options overlay `25`/`29`; exit to front-end `160`.

**Derived (instruction-level):**

* Shell dispatcher, jump table and warm-boot word (§4, §5.1) from disassembly at
  `0x0800044E–0x080004FE`.
* Bowling menu indices, player count and 0–4 lane selector from `0x085F1E00–0x085F2152`.
* Ten `KEYINPUT` load sites and generic pressed/held logic (§5.2).
* The 132-byte ASCII→tile maps exist in all three images; Bowling's copy is loaded at
  `0x086A7A2E`/`0x086A7A42`. Their vowel entries coincide with icon tiles (inference).

**Inferred:**

* The `LOAD TOURNAMENT` field is a save-slot name lookup. The label, the silent no-op on `OK`,
  and the absence of any unlock effect support this, but no matching saved name could be produced
  (see §8), so the exact storage/comparison routine was not traced.
* The Dodgeball strings `choose game mode`, `choose map`, `summer/fall/urban` exist in its text
  bank but no single-cart screen exposes them; they are most likely shared-engine leftovers or
  used only in link mode.

## 8. Unknowns

* **Save backing store.** mGBA created a 0-byte `.sav` and no data was written during the
  session, so the tournament name list could not be populated. The field's comparator and the
  tournament persistence format were therefore not exercised. This does not affect the cheat
  conclusion (no code table, no validator, no unlock of any kind).
* **Link-cable modes.** Paintball's multiplayer stops at "INSERT THE GAME BOY ADVANCE GAME LINK
  CABLE"; Dodgeball's multiplayer path and the shared "players 1 2 3 4 connected" screens could
  not be entered with one emulator instance. Any link-only content is untested.
* **Bowling tournament completion.** Qualifying/tournament play was entered (`21`) but not
  played to completion, so the tournament prize flow and any name persistence were not observed.
* The exact purpose of the shell's `0xA5A5A5A5` word after the jump was not traced in the
  sub-images; it is written by the shell before every boot and is consistent with the multicart
  warm-boot convention, but no sub-image reader was located in the first 16 KiB.

## 9. Tooling

* `mgba` 0.10.5 SDL (`/usr/games/mgba`) under `Xvfb :119` + `openbox`; `xdotool` for input;
  ImageMagick `import`/`convert` for 720×480 screenshots.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb|force-arm`
  for all disassembly.
* Python 3: header/logo scanner, string classifier, keyword census, literal and pointer scans,
  mask-run scanner, and the name-entry driver (`/tmp/opencode/sports3/gb.py`,
  `name_entry.py`, `probe.py`).
* Capstone (16-bit Thumb literal-load scan) and Ghidra 12.1.4 via REA (raw import of the Bowling
  sub-image at `0x085E8000`) as a cross-check; Ghidra's default auto-analysis found only 173
  procedures in the 2 MiB image, so the manual `objdump` reading above is authoritative.
* Emulator artifacts (`*.sav`, `*.ss1`) were generated in the ROM folder and removed at cleanup.
  No ROM, graphics, music or text assets are redistributed with this report.

## Legal note

This report documents addresses, algorithms and observed behaviour only. It contains no ROM
data, extracted graphics, audio or copyrighted text, and no emulator cheat codes. The ROM and
`INDEX.md` were not modified.
