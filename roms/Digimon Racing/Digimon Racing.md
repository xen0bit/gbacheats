# Digimon Racing (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Digimon Racing/Digimon Racing.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `DIGIMONRACIN` (12 chars, no padding) |
| Game code | `BDGE` |
| Maker | `B2` (Bandai) |
| Version | 0 (Rev.00) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Complement check (`0xBD`) | `0x57` — matches `-(0x19 + sum(0xA0..0xBC))` |
| Header checksum (`0xBE`) | `0x0000`; the correct value is `0xFA57`, so this field was zeroed. Cosmetic artifact of a header rebuild; game code is untouched (see §7) |
| Embedded headers | exactly one GBA header (Nintendo logo at file `0x04`) |
| MD5 | `0b8e817c956bf56035c3a5c73174f81b` |
| SHA-1 | `37c0bc3c8fc1b79efd18121fec6f2df97ddb3bdf` |
| SHA-256 | `f955ffeb7bed54f75264b83377e5732ae02e19c289441d4fbd6b817914bf1179` |

No cracktro/trainer: the entry branch is the retail `b 0xC0`, the first
4 KiB contains the normal crt0/IRQ stubs, and there are no `Mode7`,
`SUNHORS`, `CRC BANDIT` or piracy strings. The zeroed 16-bit header
checksum is the only header anomaly.

## 2. Executive summary

**Digimon Racing has no password, cheat-code or button-code system, and no
reachable debug menu.** The game exposes exactly two kinds of cheat-adjacent
content:

1. **Three gated roster slots** ("SECRET RACER") shown in the SELECT CHARACTER
   screen. Their own on-screen unlock text is:
   * slot A — `WIN ALL TIME TRIALS TO UNLOCK`
   * slot B — `WIN ALL QUICK RACES TO UNLOCK`
   * slot C — `WIN ALL CUP RACES TO UNLOCK`
   All three are locked on a fresh save and display a padlock/`?` portrait with
   empty stat bars. They are gameplay unlockables, not codes.
2. **A nine-slot Trophy Room** whose first slot is labelled
   `EVENT: CUP RACE / WESTERN CUP`.

Everything else is ordinary menu state: 4 main-menu entries, 4 single-player
modes, 8 options, 3 character-select options and a 2-entry pause menu. There is
no text field anywhere in the game that is consumed by a string validator.

The game's UI text is **not ASCII**: every menu label is drawn from 8×8 font
tiles into a sprite tile buffer at runtime. A byte-for-byte search of the whole
8 MiB image (and of all 733 LZ77 blocks, 146,383 decompressed bytes) for 22
keywords in six encodings returned zero genuine hits; the only ASCII `CUP`
matches are coincidental bytes inside compressed graphics. This is why a
text-only "no password" claim would be weak, and why the negative here rests on
screen enumeration plus the code-level input audit in §7.

The only published GBA "codes" for this title are GameShark/CodeBreaker memory
writes (e.g. the neoseeker master code) — those are RAM patches, not in-game
input, and are out of scope. GameFAQs/VGChartz publish only the three
unlockables, and their wording differs from the ROM: the ROM requires **all**
time trials / **all** quick races / **all** cup races, not a single win.

No accepted code can be generated because there is no code space (§6b).

## 3. How to reproduce

Emulator: mGBA SDL 0.10.x, headless Xvfb.

```bash
Xvfb :307 -screen 0 1024x768x24 &
DISPLAY=:307 openbox &
DISPLAY=:307 SDL_AUDIODRIVER=dummy mgba -3 "Digimon Racing.gba" &
```

Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows. Hold 100–150 ms; the menu debounce drops
shorter taps.

Boot path: language select (English) → © screen → Griptonite logo → title.
Press Start at the title demo to open the main menu.

Menu paths used in this report:

* Main: `SINGLE PLAYER / MULTIPLAYER / WIRELESS MULTIPLAYER / OPTIONS`
* SINGLE PLAYER → `GAME MODES`: `CUP RACE / QUICK RACE / TIME TRIAL / TROPHY ROOM`
* Any race mode → `SELECT CHARACTER`: `DIGIMON / KART COLOR / DONE`
* Cup Race → DONE → `SELECT A CUP` (Western Cup map) → A → `SELECT A TRACK`
  (`DESERT OASIS / TOY TOWN / DESERT CLIFFS / SWAMP BOG`)
* In race: Start → `PAUSE`: `RESUME RACE / QUIT RACE`
* OPTIONS: `MUSIC VOLUME / SFX VOLUME / DIFFICULTY / HUD STYLE / NEW GAME /
  CREDITS / LANGUAGE SELECT / RESET TO DEFAULT`

Savestate handling: `Shift+F1` saves slot 1, but **plain `F1` did not reload in
this build**; states had to be loaded with `mgba -3 -t game.ss1 game.gba`.
mGBA `.ss1` is a PNG; the `gbAs` chunk is zlib-compressed and decompresses to
397,312 bytes (VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000` when mapped to
GBA addresses).

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x0800889C` | code | per-frame input builder; reads `0x04000130` |
| `0x08008A00` | code | menu scroll/repeat routine, consumes the key-history ring |
| `0x0801194C` | code | time-trial input recorder; reads `0x04000130` and writes an 8-byte record |
| `0x0802F590` | code | load 232-byte profile block from EEPROM into `0x03006D00` |
| `0x0802F5CC` | code | read N 8-byte EEPROM blocks into `0x03006DF0` |
| `0x0802F62C` | code | validate settings record (checksum + magic) |
| `0x0802F6B4` | code | write N 8-byte blocks to EEPROM |
| `0x08047F74` | data | default save template + magic `DRGBA7` |
| `0x03004E90` | RAM | live settings struct (music, sfx, difficulty, HUD, flags) |
| `0x03004FF0` | RAM | previous raw key state |
| `0x03005018` | RAM | current held keys (active-high) |
| `0x03005048` | RAM | pressed-this-frame keys |
| `0x03005050` | RAM | key-history ring (menu repeat) |
| `0x03005F40` | RAM | second key-history ring (time-trial record) |
| `0x03005470` | RAM | current menu/state struct; `+0x00` screen id (`0x0D` = character select) |
| `0x0300547C` | RAM | **character-select roster index (u32)** |
| `0x03006D00` | RAM | 232-byte (`0xE8`) save profile buffer |
| `0x03006DF0` | RAM | 24-byte settings record |
| `0x0405DCC` (file) | data | 4-byte-stride candidate character stat table (see §6) |

## 5. Algorithm / save format

### 5.1 Input pipeline (derived)

```
held    = (~REG_KEYINPUT) & 0x3FF
pressed = (held ^ prev_held) & held
```
computed at `0x0800889C`; the result is stored at `0x03005018`/`0x03005048`.
A three-entry history copy is kept for scroll repeat (`0x03005050`). The
time-trial recorder at `0x0801194C` packs `~REG_KEYINPUT` into an 8-byte
frame record. **No other code reads the keypad.** There is no sequence
comparator anywhere in the ROM (§7.2).

### 5.2 Settings record (derived + observed)

EEPROM is 512 bytes (4 kbit), addressed in 8-byte blocks.

```
offset  size  field
0x00     8    "DRGBA7\0\0" magic (ROM copy at 0x08047F74)
0x08     4    zero
0x0C     8    option bytes, copied from settings struct 0x03004E90:
               [0C] = settings[0] low   (0x0F on fresh save)
               [0D] = settings[3]       (SFX volume, 8)
               [0E] = settings[2]       (music volume, 6)
               [0F] = settings[4]       (difficulty, 1 = Normal)
               [10] = settings[6]       (1)
               [11] = settings[5]       (HUD style, 0 = Type 1)
               [12] = settings[7]       (0x00 in the written record)
               [13] = settings[11]      (0)
0x14     2    zero
0x16     2    checksum = (-sum of the first 11 u16) mod 0x10000
```

Validation (`0x0802F62C`): length 24, sum of all twelve u16 == 0, and the
first eight bytes equal `DRGBA7\0\0`. The mGBA `.sav` file stores each 8-byte
record **byte-reversed**; un-reversing the first 24 bytes yields the record
above and the checksum verifies (`0x2B1E`).

The 232-byte profile block (`0x03006D00`) is read from a per-slot EEPROM
address by `0x0802F590`; on a fresh save it is entirely zero (only validity
bytes `+0xDD = 0x11`, `+0xE5 = 0xEF` are set). Progress/unlock persistence lives
in this block, but no race was completed in this engagement, so the exact
unlock bits were not observed being written (see §8).

## 6. Tables

### 6.1 Menus and effects (observed)

| Screen | Entries | Effect |
|---|---|---|
| Main | 4 | Single Player, Multiplayer, Wireless Multiplayer, Options |
| Game Modes | 4 | Cup Race, Quick Race, Time Trial, Trophy Room (each draws a preview emblem) |
| Select Character | 3 | DIGIMON (Left/Right cycles roster), KART COLOR, DONE |
| Pause | 2 | RESUME RACE, QUIT RACE (Down at QUIT wraps to RESUME) |
| Options | 8 | music 0–8, sfx 0–8, difficulty Easy/Normal/Hard (ring of 3), HUD Type 1/2 (ring of 2), New Game confirm, Credits roll, Language Select (5), Reset to Default |
| Language | 5 | English, Français, Deutsch, Italiano, Español |
| Trophy Room | 9 | 3×3 slots; selected slot header, e.g. `EVENT: CUP RACE / WESTERN CUP` |
| Link screens | 0 | Multiplayer and Wireless both show `Multi-Pak Link — Insert the Game Boy Advance Game Link cable(s) and turn the POWER on.` (no menu) |

### 6.2 Roster (observed)

Ring index at `0x0300547C`, 0–10, Right increments by one, index 11 wraps to 0.
The screen draws **one press behind** the variable (the first press after load
shows the new slot; subsequent redraws show index−1), which must be allowed for
when reading RAM against a screenshot.

| Index | Entry | Gate |
|---:|---|---|
| 0 | Agumon | none |
| 1 | Gabumon | none |
| 2 | Patamon | none |
| 3 | Tentomon | none |
| 4 | Biyomon | none |
| 5 | Salamon | none |
| 6 | Gomamon | none |
| 7 | Secret Racer A | `WIN ALL TIME TRIALS TO UNLOCK` |
| 8 | Secret Racer B | `WIN ALL QUICK RACES TO UNLOCK` |
| 9 | Secret Racer C | `WIN ALL CUP RACES TO UNLOCK` |
| 10 | wrap slot (redraws slot 9) | — |

Observed base stats (0–5 bars), from the SELECT CHARACTER panel:

| Entry | Speed | Handling | Acceleration |
|---|---:|---:|---:|
| Agumon | 3 | 3 | 3 |
| Gabumon | 5 | 1 | 1 |
| Patamon | 1 | 2 | 5 |
| Tentomon | 2 | 5 | 2 |
| Biyomon | 1 | 2 | 5 |
| Salamon | 2 | 4 | 4 |
| Gomamon | 5 | 1 | 1 |
| Secrets | 0 | 0 | 0 |

A 4-byte-stride stat table exists at file `0x045DCC`:
`(3,3,3) (5,1,1) (4,2,3) (1,2,5) (2,5,2) (1,2,5) (3,3,3) (5,1,1) (3,3,4)…`
It matches Agumon/Gabumon and contains Patamon/Tentomon/Biyomon's triplets later
in the array, but does not match the displayed order for every entry; treat it
as a candidate tuning table, not a confirmed roster map (Inferred).

### 6.3 Tracks (observed)

`DESERT OASIS`, `TOY TOWN`, `DESERT CLIFFS`, `SWAMP BOG` — four track nodes on
one map, cup name `WESTERN CUP`. Time Trial lists the same four and wraps after
the fourth. Cup Race goes map → `SELECT A TRACK` → race (3-lap HUD).

## 6b. Enumeration

**Code/password space: 0.** There is no entry screen, no alphabet, no field,
no validator and no accepted string. The space of representable codes is the
empty set; the relevant proof is the bounded negative below.

* **Screens walked (all reachable entries):** title → main (4) → Single Player
  (4) → all four modes; Cup Race (cup map + 4 tracks), Quick Race, Time Trial
  (4 tracks), Trophy Room (9 slots), character select (3 controls, 11-index
  ring), pause (2), options (8, every value ring cycled), language select (5),
  New Game confirm dialog, credits roll, Multiplayer link wait, Wireless link
  wait, © and logo screens. **Total interactive entries enumerated: 21.**
* **Text space:** the ROM contains no ASCII UI text at all. A search of all
  8,388,608 bytes for 22 keywords (`PASSWORD, CHEAT, DEBUG, SECRET, UNLOCK,
  CODE, TRACK, TIME TRIAL, GRAND PRIX, CUP, OPTION, SELECT, STAFF, TEST, ZUKAN,
  DIGIDEX, PADLOCK, CONTINUE, INVALID, FREE, RACE, MUSIC, VOLUME`) in ASCII,
  lowercase, `+0x20`, `XOR 0x80`, UTF-16LE and UTF-16BE produced **5 raw hits,
  all in compressed graphics and all classified false positives** (e.g.
  `0x6BC79` = `…84CUP3C%P-(`). The same keywords over all **733 LZ77 blocks
  (146,383 bytes)** produced **0 hits**. Therefore a text-string search cannot
  be the basis of the negative; the screen and code audits are.
* **Button space:** the literal `0x04000130` occurs 4 times. Only two are real
  keypad reads (`0x0800889C`, `0x0801194C`); the other two (`0x0800B628`,
  `0x0800B7A0`) are `CpuSet` control words (`count 0x130 | fill bit`), a
  numeric coincidence. Both real readers are accounted for (input state
  builder; time-trial frame recorder). A scan for runs of ≥4 u16 values shaped
  like button masks (single button) found **34** aligned runs; every one is
  Thumb code or glyph/width data (e.g. `0x7DE650` disassembles as `00 47 80 44`
  = `bx r0` / `add r0,r0`, and `0x4832D6` is 0x20 repeated). The relaxed
  ≤2-button-combination scan found 1102 runs, none referenced as a sequence
  table. **No code validator exists.**
* **Roster space:** 11 ring positions, 10 distinct entries (7 base + 3 gated),
  3 gated. No undocumented input reaches the gated entries; the only documented
  and displayed gates are the three "win all" conditions. Pressing A after
  `Down, Down` on a locked slot advanced the roster to the next secret slot
  instead of launching a race (observed; no race screen appeared).
* **Bounds proven by rejection:** difficulty rejects a fourth value (cycles
  3 → 1), HUD rejects a third (2 → 1), the pause cursor rejects a third entry
  (Down at QUIT returns to RESUME), and the roster cursor rejects index 11
  (wraps to 0) with index 10 being the wrap duplicate. Roster/stat reads at
  index 10 re-render the last secret entry rather than a new character.
* **Novel code:** not applicable — no code system exists, so no value can be
  minted. The §0.2 deliverable is replaced by the full screen/entry
  enumeration and the quantified text/button-space negatives above.

Published-list check: GameFAQs/VGChartz list no passwords or in-game codes,
only the three unlockables and one turbo glitch. Their conditions
("Win Cup Mode", "Win Time Trial", "First place Grand Prix") do not match the
ROM's own text ("win **all** time trials / quick races / cup races"). The ROM
never displays the names Agunimon/Guilmon/Veemon while the slots are locked, so
the published name-to-condition mapping is **unverified**.

## 7. Validation evidence

### 7.1 Observed
* Language select (5 options), title/main/options/game-modes/char-select/pause/
  trophy screens as listed in §6.1, with exact key paths in §3.
* Three locked `SECRET RACER` slots with the three distinct on-screen unlock
  sentences, padlock icon and empty stat bars.
* `0x0300547C` increments 0→10 then wraps to 0 (12-press experiment, one RAM
  snapshot per press); index 0 = Agumon … 6 = Gomamon, 7/8/9 = the three
  secrets.
* Pause menu has exactly two entries and the cursor wraps.
* Difficulty ring is Normal→Hard→Easy→Normal; HUD ring is Type 1→Type 2.
* Save file: 24-byte record with magic `DRGBA7`, options `0F 08 06 01 01 00 00
  00`, checksum `0x2B1E`; recomputed checksum matches and the twelve u16 sum to
  zero.
* Quitting a race rewrote two bytes of the temporary block at `.sav 0xF2/0xFA`
  (0x11/0xEF → 0x00/0x00), i.e. the game invalidates the in-progress block.

### 7.2 Derived
* `0x0800889C` builds held/pressed from `0x04000130`; `0x08008A00` is the only
  consumer of the key-history ring (menu auto-repeat).
* `0x0801194C` is the time-trial input recorder; it stores `~KEYINPUT` into an
  8-byte record (`0x03005F30` buffer) and ORs `0x1000` into `0x030050F4`.
* `0x0802F62C` validates the settings record (magic + two's-complement sum);
  `0x0802F590` reads a 29-block (232-byte) profile block per slot.
* The `0x04000130` literals at `0x0800B628`/`0x0800B7A0` are `CpuSet` control
  words passed to the BIOS wrapper at `0x0803A42C`, not keypad reads.

### 7.3 Inferred
* The three gated slots correspond to the publicly named Agunimon/Guilmon/Veemon
  (not displayed in ROM while locked).
* Progress flags live in the 232-byte profile block, since it is the only
  per-slot EEPROM structure read at boot; the exact bits were not observed
  (no race completed).
* `0x045DCC` is a per-mode character tuning table.

## 8. Unknowns

* **Exact unlock flag offsets** in the 232-byte profile block. Patching
  `0x03006D00` in a savestate to `0xFF` (both the full block and bytes
  `0x00–0xDC` with validity bytes preserved) did **not** unlock the slots, which
  is expected if the block is re-read from EEPROM when the character screen is
  entered. Completing one race would reveal the written bytes; this was not
  done.
* **Trophy Room semantics.** Nine slots exist, slot 1 is `EVENT: CUP RACE /
  WESTERN CUP`; the remaining eight headers were not enumerated (each requires
  moving the cursor and reading a pre-rendered banner). Their mapping to
  cups/tracks/difficulties is unresolved.
* **Number of cups.** Only `WESTERN CUP` and its four tracks were reachable on a
  fresh save; whether more cup regions appear after wins is untested.
* **Padlockmon.** TCRF documents an EU-ROM joker character at RAM `0x0300547C =
  0x0B`. Writing that index in this US ROM and cycling the cursor rendered the
  locked `SECRET RACER` placeholder, not a named character; the EU behaviour
  was not reproduced.
* **Text encoding.** The font/tile text system was not decoded; the Digidex /
  Zukan text bank mentioned by TCRF was not located. This does not affect the
  cheat conclusion because no input surface consumes text.

## 9. Tooling

* mGBA SDL + Xvfb `:307` + openbox, `xdotool` key injection.
* `keys.py` — key hold/gap helper.
* `snap.py` — `Shift+F1` savestate capture, zlib-decompress `gbAs`, write raw
  397,312-byte state.
* `patchstate.py` — patch a RAM address inside `game.ss1` and rewrite the PNG
  (used only for the hidden-slot experiments; all unlock effects were read from
  RAM/screens, not assumed).
* Python: `capstone` 5.0.7 (instruction checks), `zlib`, `struct`, Pillow
  (tile/VRAM rendering), `arm-none-eabi-objdump -M force-thumb` for raw Thumb.
* Scan scripts/results: `scan_results.txt` (keyword matrix), `button_scan.txt`
  (mask-run scan), `save_format.txt` (record decode/checksum).

## 10. Legal note

No ROM, graphics, music or extracted text is redistributed with this report.
All addresses, hashes, algorithms and the save-format description are original
analysis.
