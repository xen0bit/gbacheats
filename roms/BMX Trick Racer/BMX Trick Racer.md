# BMX Trick Racer (GBA) — Reverse Engineering Report

Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)
Analysis date: 2026-10-26

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/BMX Trick Racer/BMX Trick Racer.gba` |
| Size | 16 MiB (`0x1000000`, 128 Mbit) |
| Header title | `BMX TRICK RA` |
| Game code | `AT9E` |
| Maker code | `7L` |
| Software version | `00` |
| Fixed byte `0xB2` | `0x96` (valid) |
| Complement check `0xBD` | `0x84` (valid; recomputed `0x84`) |
| Header checksum `0xBE` | `0x0000` — **invalid**; recomputed `0xFA84` |
| Entry word `0x00` | `0xEA3FD596` (`b 0x08FF5660`) — patched, see §2 |
| Save type | EEPROM (`EEPROM_V122` string at `0xF4674C`), 512-byte `.sav` |
| MD5 | `87887a34f52b119c0bbce4a6be26d842` |
| SHA-1 | `76707d81aeb84665dac35f40d33301a4f8d82924` |
| SHA-256 | `4ee87572db6a1bcb9488ab7b423aa1ce71391013520d68ee8b7342949c4b63ba` |

Embedded-header scan: the 156-byte Nintendo logo (`24 ff ae 51 …`) occurs
exactly **once**, at file `0x04`; the image is a single GBA program, not a
multi-game pack. ROM addresses below are `0x08000000 + file_offset`.

The complement check is correct but the 16-bit header checksum at `0xBE` is
zero, so the image fails the header-checksum test even though mGBA's HLE BIOS
boots it. Combined with the patched entry word (§2) this marks the file as a
post-build-modified release, not a clean dump of the retail cartridge.

---

## 2. Executive summary

**BMX Trick Racer has no cheat system.** There is no password screen, no
password/check code, no button-code table, no hidden or debug menu, and no
character/level-select shortcut. Progress is stored on EEPROM and the only
"secret" content is ordinary progression: the ten BMX bikes and five locations are
unlocked by finishing Tour legs (top-3 to advance, 1st to unlock the next
world), and a points pool is distributed over rider abilities. Every menu in
the game was walked; the text menus' item counts match their literal-pointer
tables exactly (e.g. the pause table holds three pointers), and no unreachable
or hidden entry exists.

The ROM, however, is **not the retail build**. It is a MODE7 scene release:

* The GBA entry word at `0x08000000` has been replaced with `b 0x08FF5660`.
  The stock instruction is `b 0x080000C0` (`0xEA00002E`).
* `0x08FF5660` is a small loader that installs an IRQ vector
  (`0x03007FFC = 0x0300151C`), sets up the stacks and jumps into a 2 KiB
  intro module at `0x08FFF788`.
* The intro is a seven-screen cracktro (screens and exact text in §6.1) with a
  hidden 32-column text slab at `0x08FF56D0`: `$ MODE7 $`, "BLASTS THE OTHERS
  AWAY WITH", `GAME SUPPLIED BY: NANOOK`, `RELEASED ON: SEPTEMBER 8TH, 2002`,
  greets to AGGRESSION / ANTHROX / ILLUSION / SNEAKERS / SWAT / DCS,
  `- MODE SEVEN -`, "POWERED BY THE HATRED FOR THE SCENE".

**Functional defect found in the shipped image:** after the cracktro hands
control to the game, the game reaches its own MAIN MENU and renders normally,
but **never polls the joypad**. In mGBA the hardware register `KEYINPUT`
(`0x04000130`) tracks every key press, yet the game's key-state words
`0x030058B8` (held) and `0x030058BA` (new presses) stay zero, and none of 28
tested keys changes any screen. The game's only `KEYINPUT` reader is the
routine at `0x0800584C`, and it is never called in this state. Restoring the
stock four-byte entry (`0xEA00002E`, `b 0x080000C0`) on a copy produces a
byte-identical-otherwise image (`SHA-256 347667e4…b4c4b0d0a`) that boots
straight to the HYPNOTIX logo and is **fully interactive**. All menu and
gameplay observations below were made on that restored copy; the shipped file
was used for every static claim and for the intro.

Since no code system exists, the deliverable is the bounded negative result in
§6b: the text space, the button-mask space, the complete screen tree and every
published-code source, with counts.

---

## 3. How to reproduce

### Emulator

```bash
Xvfb :150 -screen 0 1280x1024x24 &
DISPLAY=:150 openbox &
export DISPLAY=:150 SDL_AUDIODRIVER=dummy
mgba -3 "BMX Trick Racer.gba" &
W=$(xdotool search --name mGBA | head -1)
xdotool mousemove 600 550 click 1      # focus + mouse grab
xdotool windowfocus --sync "$W"
```

Default SDL keymap (verified against `KEYINPUT`): A=`x`, B=`z`,
Start=`Return`, Select=`BackSpace`, L=`a`, R=`s`, D-pad = arrow keys.
Hold 60–150 ms; menu transitions take 1–2 s and the first press after a
transition can be swallowed.

### Boot the shipped image (reproduces the defect)

1. Start the ROM. The MODE7 cracktro auto-cycles its seven screens.
2. Press Start repeatedly; the intro ends and the game's MAIN MENU appears.
3. Press any key: nothing happens. `START GAME` / `OPTIONS` / `RECORDS`
   never activate.

Machine check with mGBA's GDB stub (`mgba -g`, then read memory while stopped):

```
KEYINPUT (0x04000130)      : 0x03FF idle, 0x037F while Down is held
game held-key word 0x030058B8 : 0x0000 in both cases
```

The hardware sees the key; the game does not.

### Restore the stock entry (what all gameplay below used)

```bash
cp "BMX Trick Racer.gba" /tmp/bmx_clean.gba
python3 - <<'EOF'
d = bytearray(open('/tmp/bmx_clean.gba','rb').read())
d[0:4] = (0xEA00002E).to_bytes(4,'little')   # b 0x080000C0
open('/tmp/bmx_clean.gba','wb').write(d)
EOF
```

The copy then boots HYPNOTIX → title (`PRESS START TO BEGIN`) → MAIN MENU and
every menu responds. Nothing else is modified.

### Menu path (observed, restored copy)

```
title (PRESS START TO BEGIN)
└─ MAIN MENU ── START GAME ── SELECT PLAYER ─┬─ SINGLE PLAYER ─┬─ SELECT MODE ─ TOUR ────── CHOOSE RIDER ─ CHOOSE BIKE ─ TRAINING ROOM
   │                                        │                 ├─ EXHIBITION ─ SELECT MODE ─┬─ FREESTYLE ─ SELECT DIFFICULTY ─ CHOOSE RIDER ─ CHOOSE BIKE ─ CHOOSE LOCATION ─ CHOOSE TRACK ─ track card ─ race
   │                                        │                 │  (FREESTYLE/RACE)        └─ RACE ───── SELECT DIFFICULTY ─ … (same)
   │                                        │                 └─ PRACTICE ── SELECT MODE ─ … (same)
   │                                        └─ MULTIPLAYER ── "NO LINK DETECTED" (link cable required)
   ├─ OPTIONS ── RESET CHARACTER <name> / SFX LEVEL / GAMMA ── (reset confirm: RESET / CANCEL)
   └─ RECORDS ── RECORD BOOK (15 tracks, Top 3 Times / Top 3 Scores, A = main menu)
```

In-race Start opens `GAME PAUSED` with **CONTINUE / QUIT / RESTART**. In the
TRAINING ROOM the pause menu is **GUIDED TOUR / FREE RIDE / QUIT**.

### Published codes exercised

None exist to exercise. See §6b.4 for the three sources checked.

### Button combinations tried at MAIN MENU / SELECT PLAYER (restored copy)

| Input | Result |
|---|---|
| Konami sequence (Up Up Down Down Left Right Left Right B A) | no effect; D-pad input is consumed as menu navigation, no interception |
| L+R+Start held 1.2 s | no effect |
| Select+Start held 1.0 s | no effect |

---

## 4. Address map

All addresses verified against the bytes; `rom` = `0x08000000 + offset`.

| Address | What |
|---|---|
| `0x08000000` | entry word. Shipped `0xEA3FD596` → `0x08FF5660`; stock `0xEA00002E` → `0x080000C0` |
| `0x080000C0` | game crt0 (`mov r0,#0x12; msr cpsr…`, stack setup, `bx` main) |
| `0x0800584C` | **only joypad reader**: `held = 0x3FF ^ KEYINPUT`, `new = held & ~prev` |
| `0x0800586C` | literal pool word `0x04000130` (KEYINPUT) |
| `0x08005874/78` | literal pool words `0x030058BA` (new), `0x030058B8` (held) |
| `0x030058B8` | held keys, active-high: bit0 A, 1 B, 2 Select, 3 Start, 4 Right, 5 Left, 6 Up, 7 Down, 8 R, 9 L |
| `0x030058BA` | newly pressed keys this frame (same bit order) |
| `0x0800584C` callers (BL) | `0x0800705C`, `0x0800F45C`, `0x0800F74C`, `0x0800F868`, `0x08010AEA`, `0x08010AFE`, `0x08010DCC`, `0x08011630`, `0x080148F2`, `0x08015544`, `0x0801564E` |
| `0x08005E48` | function executing at the main menu; byte-field/table arithmetic, role inferred as save/profile parsing |
| `0x0802A000–0x0802C100` | ASCII text bank (font-rendered messages, menu labels, track/trick names) |
| `0x0802B2E8` | `GUIDED TOUR` (pause item) |
| `0x0802B2F4` | `FREE RIDE` (pause item) |
| `0x0802B300` | `QUIT` (pause item) |
| `0x0802B308` | `CONTINUE` (pause item) |
| `0x0802B314` | `RESTART` (pause item) |
| `0x0800F344–0x0800F35C` | literal pool holding the pause-item string pointers (3 entries per menu) |
| `0x0802B330/B348` | `Top 3 Times` / `Top 3 Scores` (record book) |
| `0x0802B358` | reset-character warning text |
| `0x0802B52C` | `Enter your initials into the Record Book:` (the game's only text-entry UI) |
| `0x0802B5C8–0x0802B7EC` | qualification / unlock messages (`You must finish at least 3rd…`, `unlocked new bikes!`) |
| `0x0802B838/B844/B84C` | `GET READY!` / `SET!` / `1ST PLACE` … `6TH PLACE` |
| `0x0802B894` | `MultiSio010918` (link-cable engine banner) |
| `0x0802BE98–0x0802C034` | trick input descriptions (`L BUTTON + UP`, `A+B+L BUTTONS TOGETHER`, …) |
| `0x0802BA0C`, `0x0802BA70` | short button-mask-like tables; referenced by gameplay code at `0x080100B4` and `0x0801DFD0` (trick/gameplay, not a code table) |
| `0x08D61874+` | per-track info cards (track name, world-leg, qualification/score/time requirements) |
| `0x08FF5660` | cracktro loader (installs IRQ vector `0x03007FFC = 0x0300151C`, jumps `0x08FFF88D`) |
| `0x08FF56D0–0x08FF5C5x` | cracktro 32-column text slab (greets, release date) |
| `0x08FFF788–0x08FFFF00` | cracktro code, sine table (`0x08FFF78C`), screen table (`0x08FFFF60`) |

---

## 5. Algorithm

### 5.1 Boot chain (derived from the bytes)

```
reset → 0x08000000 (patched) → 0x08FF5660
        mov r0,#0x12 ; msr cpsr → IRQ stack
        mov r0,#0x1F ; msr cpsr → system stack
        [0x03007FFC] = 0x0300151C     ; IRQ vector
        bx 0x08FFF88C                 ; cracktro main (Thumb)
cracktro: 7 text screens, Start advances/finishes
        → game entry 0x080000C0 → crt0 → game main
```

The cracktro stays resident and leaves the IRQ vector pointing at
`0x0300151C`. In the shipped image the game then draws its menus but never
executes its joypad reader (§2). The exact mechanism (IRQ ownership vs. a
skipped init path) was not isolated; it is reported as inferred.

### 5.2 Joypad polling (derived, verified dynamically)

```
every frame:
    raw   = REG_KEYINPUT (0x04000130)       ; active-low
    held  = 0x3FF ^ raw                     ; active-high, 10 bits
    new   = held & ~prev_held               ; stored at 0x030058BA
    prev_held = held                        ; stored at 0x030058B8
```

`new` is what menus consume (edge-triggered), which is why presses must be
released before the next one. The 11 BL callers above are menu loops and
gameplay handlers; no caller compares a sequence index against a table length.

### 5.3 Progression / unlocks (derived from the text bank and observed screens)

* 5 locations × 3 legs = 15 race tracks, plus 5 freestyle locations.
* Tour: finish at least 3rd to qualify for leg 2, 2nd for leg 3, 1st to win
  and unlock the next world. Every completed tour also grants ability points
  ("You've unlocked the next location, and earned N of M possible ability
  points") distributed with Left/Right and saved with A.
* Bikes are unlocked by tour completion; on a fresh EEPROM (all `0xFF`, no
  record) the bike list already contains locked entries (observed: selecting
  `AGGRAVATE` shows a `LOCKED` plate).
* The record book stores Top 3 Times and Top 3 Scores per track (15 entries);
  the untouched baseline display is `BMX 5:30.99` / `BMX 999`.

There is no flag, string or branch anywhere for a developer shortcut.

---

## 6. Tables

### 6.1 Cracktro screens (shipped image, observed)

| # | Screen |
|---|---|
| 1 | `$ MODE7 $` — `BLASTS THE OTHERS AWAY WITH:` / `* BMX TRICK RACER *` / `@ SIMON & SCHUSTER INT.` / `128MBIT - USA VERSION` |
| 2 | `GAME SUPPLIED BY:` / `NANOOK` / `RELEASED ON:` / `SEPTEMBER 8TH, 2002` |
| 3 | `BUBBLE GUMS TO OUR FRIENDS IN:` / `AGGRESSION $ ANTHROX ILLUSION $ SNEAKERS $ SWAT AND $ DCS $` |
| 4 | `- MODE SEVEN -` / `POWERED BY` / `THE HATRED FOR THE SCENE` |
| 5 | `"DOGE THIS?"` (with `-*`) |
| 6 | `-YSS SENITU-` / `PERFORMED BY:` / `* MICROFOKE *` |
| 7 | `GREETS:` / `* CODEWAVES *` |

Then the game's own boot: ©2002 Simon & Schuster legal text → `LICENSED BY
NINTENDO` → Simon & Schuster logo → HYPNOTIX → title screen.

### 6.2 Every screen and its item count

| Screen | Items |
|---|---|
| Title | `PRESS START TO BEGIN` (1) |
| MAIN MENU | START GAME, OPTIONS, RECORDS (3) |
| OPTIONS | RESET CHARACTER `<name>`, SFX LEVEL, GAMMA (3) |
| Reset confirm | RESET, CANCEL (2) |
| RECORD BOOK | track selector (15), Top 3 Times, Top 3 Scores |
| SELECT PLAYER | SINGLE PLAYER, MULTIPLAYER (2) |
| MULTIPLAYER | `NO LINK DETECTED` message (1) |
| SELECT MODE | TOUR, EXHIBITION, PRACTICE (3) |
| SELECT MODE (2) | FREESTYLE, RACE (2) |
| SELECT DIFFICULTY | AMATEUR, PRO, EXPERT (3) |
| CHOOSE RIDER | 6 riders + COLOR row |
| CHOOSE BIKE | bike list (locked entries show `LOCKED`) |
| CHOOSE LOCATION | 5 worlds |
| CHOOSE TRACK | 3 legs of the chosen world |
| Track card | name, requirements, `Press A to Start` (1) |
| GAME PAUSED (race) | CONTINUE, QUIT, RESTART (3) |
| GAME PAUSED (training) | GUIDED TOUR, FREE RIDE, QUIT (3) |

Item counts match the literal-pointer tables exactly (e.g. the pause table at
`0x0800F344` holds three string pointers), so there is no hidden fourth entry.

### 6.3 Riders (CHOOSE RIDER)

Six riders with per-rider stats (STRENGTH / STAMINA / SPEED / AGILITY, each
`value/max`), plus a cosmetic colour selector (red, yellow, green observed).

| Rider (screen text) | STR | STA | SPD | AGI |
|---|---|---|---|---|
| `PEATEY` | 3/15 | 1/15 | 4/15 | 2/15 |
| `HARLEY` | 2/15 | 2/17 | 4/17 | 2/11 |
| `ICE TRAY` | 1/15 | 2/13 | 5/18 | 2/14 |
| `MILLER` | 2/17 | 4/19 | 3/13 | 1/11 |
| `TONI` | 2/15 | 1/10 | 3/15 | 4/20 |
| `T. ROTTEN` | 4/14 | 1/14 | 3/15 | 2/17 |

The seventh Right press wraps to `PEATEY` with the same stats, which proves a
roster of exactly six. `PEATEY` is the default selection. The colour row below
the rider is cosmetic (red, yellow and green observed).

### 6.4 Bikes (CHOOSE BIKE)

| # | Bike | Weight | Stability | State (empty save) |
|---|---|---|---|---|
| 1 | `WHEELER` | 33 lbs | 2/10 | unlocked (default) |
| 2 | `VIKTOR` | 33 lbs | 4/10 | `LOCKED` |
| 3 | `AGGRAVATE` | 32 lbs | 3/10 | `LOCKED` |
| 4 | `BLITZ` | 30 lbs | 5/10 | `LOCKED` |
| 5 | `BLAZE` | 31 lbs | 6/10 | `LOCKED` |
| 6 | `TEMPEST` | 27 lbs | 8/10 | `LOCKED` |
| 7 | `TSUNAMI` | 29 lbs | 7/10 | `LOCKED` |
| 8 | `CYCLONE` | 26 lbs | 9/10 | `LOCKED` |
| 9 | `VENOMOUS` | 24 lbs | 8/10 | `LOCKED` |
| 10 | `VISION` | 23 lbs | 10/10 | `LOCKED` |

The eleventh Right press returns to `WHEELER`, so the selector holds exactly
ten bikes. The retail manual's "up to 11 BMX bikes" does not match the ROM's
selector; the tenth entry is `VISION` (lightest, maximum stability). Only
`WHEELER` is selectable before any Tour progress.

### 6.5 Locations and tracks

| World | Leg 1 | Leg 2 | Leg 3 |
|---|---|---|---|
| Amazon Jungle | River Run | Quetzalcoatl Throttle | Broken Bridge Ridge |
| Alaskan Frontier | Plummet | Piper's Peak | Ice Bridge Boogie |
| Desert Canyon | Canyon Climber | Air it Out | Down N' Dirty |
| Metro City | Metro Jam | Girder Grind | Mad Highway |
| Coaster Park | Coaster Calamity | Crazy Curves | Loopapalooza |

Exhibition/freestyle requirement text for each track is stored verbatim at
`0x08D61874+` (e.g. `- Score at least 4000 points.` / `- Finish within 1:30.`).

### 6.6 Button-mask data (not a cheat table)

The only code-referenced tables that look like button masks are
`0x0802BA0C` and `0x0802BA70` (values such as `0x0001, 0x0100, 0x0002,
0x0102, 0x0300`), referenced from gameplay code at `0x080100B4` and
`0x0801DFD0`, sitting beside the trick-name/input strings at `0x0802BE98`.
They are move-input descriptors (the game documents combos like
`A+B+L BUTTONS + UP`), have no length/terminator word and are not indexed by a
press counter.

---

## 6b. Enumeration

### 6b.1 Size of the code space

| Candidate system | Screens found | Alphabet | Length | Validator | Codes |
|---|---|---|---|---|---|
| Password entry | 0 | — | — | — | **0** |
| Cheat / debug menu | 0 | — | — | — | **0** |
| Button-code sequence | 0 | — | — | — | **0** |
| Hidden select (bikes/tracks) | 0 | — | — | — | **0** |

The code space is empty: there is nothing to enumerate because no
input-validation path exists. The *unlockable* space (the only progression
shortcut surface) is: 6 riders × cosmetic colour, 10 bikes (wrap proven by the
11th Right press), 5 worlds × 3 race tracks + 5 freestyle locations, and a
per-tour ability-point pool.

### 6b.2 Novel codes

None can be minted. A novel code requires an input channel whose decoder can be
reimplemented; here there is no input buffer, no alphabet, no length check, no
checksum and no table (§6b.3). Reporting a "generated" value would be
inventing a system that the ROM does not contain.

The one text field that exists is the 3-character initials entry for the
record book (`Enter your initials into the Record Book:` at `0x0802B52C`,
string pointer in the pool at `0x08016D64`, used by the record-book code at
`0x08016D32`). It is offered when a record is set (the `NEW RECORD TIME!`
message precedes it) and stores a display name; no alphabet, checksum or
comparison table exists for it anywhere in the ROM.

### 6b.3 Bounds of the negative result (counts)

**Text space.** Applied to the whole 16 MiB image:

| Search | Result |
|---|---|
| printable ASCII runs ≥ 4 bytes | 190,654 |
| runs containing `password` | **0** |
| runs containing `cheat` | **0** |
| runs containing `debug` | **0** |
| runs containing `secret` | **0** |
| runs containing `hidden` | **0** |
| runs containing `code` | **0** |
| runs containing `select` | **0** |
| runs containing `test` | **0** |
| runs containing `gallery` / `sound` / `jingle` | **0 / 0 / 0** |
| runs containing `unlock` | 7 — all progression messages (`0x2B660`, `0x2B678`, `0x2B6B8`, `0xD619EC`, `0xD61BA5`, `0xD61D56`, `0xD61EF5`) |
| runs containing `bonus` | 1 — `UNKNOWN BONUS` score label (`0x2AEE8`) |
| runs containing `master` | 1 — `Your a real trick master!` (`0xD64252`) |
| runs containing `continue` | 2 — pause item + `Press A to continue` |
| runs containing `track` | 1 — `or START for new track` |
| high-bit-set (`c|0x80`) variants of PASSWORD/CHEAT/DEBUG/SECRET/UNLOCK | **0** |

All hits were dumped with ±100 bytes of context and classified: they are the
track-description bank, the pause/record messages and the cracktro slab. No
hit sits in a table of equal-length strings with a pointer table, which is how
this engine stores real literals (trick names, track names).

**Button space.**

| Search | Result |
|---|---|
| `0x04000130` literal (the only `KEYINPUT` reader) | 2 occurrences: game `0x0800586C`, cracktro `0x08FFFB1C` |
| LDR sites that load the held-key word | 13 |
| LDR sites that load the new-press word | 47 |
| LDR sites with ≥3 comparisons against key-mask immediates in a 0x180-byte window | 7 — all menu-index (`1,2,3,4`) or steering/trick code; verified sample at `0x08013B38` is the rider Right/Left handler (`and #0x10`, `and #0x20`) |
| u16 runs ≥ 4 of single-bit key masks | 61 — none referenced by code except the two trick tables (`0x0802BA0C`, `0x0802BA70`) |
| u16 runs ≥ 5 of masks/two-mask combos | 229 — all in graphics/level data except the two trick tables |
| sequence-counter + length check at a key-read site | **none** |

A button cheat needs (a) a mask table and (b) a progress index compared against
a length. Neither exists: the two mask-like tables are consumed as individual
move descriptors, and no caller of `0x0800584C` maintains a sequence index.

**Menu space.** Every menu in §6.2 was reached and photographed, including both
pause variants, the multiplayer no-link screen, the reset confirmation and the
`LOCKED` bike plate. (The post-race initials prompt is a text field, not a menu;
see §6b.2 and §8.) Each menu's item count equals its literal-pointer
table count, so no hidden item exists.

**Rejection tests (bounds in the negative direction).**

| Input | Expected by a code system | Observed |
|---|---|---|
| Select `AGGRAVATE` bike on an empty save | unlock | `LOCKED` plate, cannot accept |
| `MULTIPLAYER` without a link cable | enter mode | `NO LINK DETECTED`, returns to menu |
| Konami / L+R+Start / Select+Start at MAIN MENU | secret | no screen change (§3) |
| Any of 28 keys at the shipped image's MAIN MENU | input | no screen change; key-state word stays 0 |
| Record book on an empty save | codes | baseline placeholders `5:30.99` / `999`, no entry prompt |

### 6b.4 Published codes

| Source | Result |
|---|---|
| VGChartz (`/game/26322/bmx-trick-racer/cheats`) | "Total cheats available: 0 — No cheats available for this game" |
| CheatingDome (`cheatingdome.com/gba/bmxtrickracer-cheats.htm`) | "No Cheats or Achievements yet" |
| GameFAQs (`/gba/582392-bmx-trick-racer/cheats`) | HTTP 403 to automated fetch; no codes page is linked from the game's GameFAQs entry, and search snippets surface no codes; archived copies return 404/429 |
| TCRF (`tcrf.net/BMX_Trick_Racer`) | HTTP 403 to automated fetch; search results show no cut-content/cheat page |
| CheatHappens (`show_board.asp?titleID=39694`) | no cheats, message board only |

There is no public code to verify or test, which is consistent with the ROM
containing none.

---

## 7. Validation evidence

**Observed (emulator screenshots / memory reads)**

* Shipped image: seven cracktro screens, then the game's MAIN MENU; 28 keys
  produce no navigation (screenshots before/after each key).
* `KEYINPUT = 0x03FF` idle and `0x037F` with Down held while `0x030058B8`
  stays `0x0000` (GDB-stub reads, shipped image).
* Restored copy: title responds to Start; every menu in §6.2 navigates and
  every photographed screen matches its table.
* Restored copy: 6 riders, 10 bikes, 5 worlds, 3 legs per world, `LOCKED`
  plate, both pause menus, no-link screen.
* Header fields and hashes of both images.

**Derived (instruction-level)**

* Entry word and stock replacement; cracktro loader at `0x08FF5660`; IRQ
  vector write; screen table and text slab.
* `0x0800584C` is the only `KEYINPUT` reader, producing `0x030058B8/BA`.
* Pause/menu item counts from the literal pools at `0x0800F344+`.
* No sequence detector: the mask tables and LDR-site analysis above.

**Inferred**

* The cracktro leaves the game's joypad polling inactive because the intro
  retains IRQ/state ownership after handing control to the game (the observed
  fact is "reader never called"; the causal mechanism was not isolated).
* Unlock conditions (top-3 / 1st) are read from the game's own messages and
  have not been driven to completion in this session.

---

## 8. Unknowns

* Why the game's joypad reader is not called in the shipped image; the
  cracktro's exact teardown is not reconstructed.
* Whether the header checksum `0xBE = 0x0000` was zeroed by the scene group or
  was already absent in the master used; the complement byte is valid.
* The number of colour palettes per rider (three observed; cosmetic only).
* The post-race initials prompt (string `0x0802B52C`, record-book code at
  `0x08016D32`) was not driven to completion; it needs a record-setting run.
  It is a three-letter name field (the baseline entries are named `BMX`), it is
  not one of the §6.2 menus, and no code alphabet, checksum or comparison table
  exists for it, so the negative result in §6b does not rest on it.

---

## 9. Tooling

| Tool | Use |
|---|---|
| `mgba-sdl 0.10.5` under `Xvfb :150` + `openbox` | ground truth, screenshots |
| `xdotool`, `scrot`, ImageMagick | input and capture |
| `arm-none-eabi-objdump`, Capstone 5.0.7 | Thumb/ARM disassembly and pattern scans |
| GDB remote-serial client (Python, `tools/rsp.py`) | break/read `KEYINPUT`, key-state words, RAM dumps |
| `LD_PRELOAD` port shim (`tools/portshift.c`) | remap mGBA's hard-coded GDB port 2345 → 2355 when another instance owns 2345 |
| `tools/keyscan2.py` | literal-pool/LDR-site scan for key-state readers |
| `tools/spaces.py` | text-space and button-mask-space counts |

Reproduction notes for a later analyst:

* mGBA's GDB stub exits the emulator when the client disconnects, so each
  experiment must run inside one connection.
* The SDL frontend hard-codes GDB port 2345; if it is busy, build
  `portshift.c` and start `LD_PRELOAD=…/portshift.so mgba -g …`, then connect
  to 2355.
* Menu transitions swallow the first press; always screenshot before
  concluding a key did nothing.

---

## 10. Legal

No ROM, graphics, music or text assets are redistributed here. All findings are
addresses, algorithms, statistics and short UI strings quoted for
identification. The analysed file is a modified scene release; the retail
cartridge differs at `0x00` (stock `0xEA00002E`).
