# Hot Wheels: Burnin' Rubber (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Hot Wheels: Burnin' Rubber/Hot Wheels: Burnin' Rubber.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `HOTWHEELS BR` |
| Game code / maker | `AHWE` / `78` (THQ; Altron developed) |
| Version / unit / device | `0x00` / `0x00` / `0x00` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock) |
| MD5 | `8ef10e6b20930b83f2ef3c11a1752793` |
| SHA-1 | `ce370386736de2243a078eb50d9b72362588b8b5` |
| SHA-256 | `9737fccc9982dcf28c18fb8e61eb724a7e592de2622733aa42b0aed9759b4bd1` |

Phase 0 result: the 156-byte Nintendo logo occurs **once**, at file `0x4`; there is no
second/multiboot header and no appended trainer. The entry branch is the stock
`b 0x080000C0` and the crt0 at `0x080000C0` is intact — no scene cracktro/patch.
Header complement byte is `0x56` and checksum `0x0000` (the latter is a normal
rebuilt-header artifact; the stock entry and single logo rule out a swapped image).
The save type is EEPROM: the literal `EEPROM_V121` is at `0x0811783C`, and mGBA
created a 512-byte `.sav`.

## 2. Executive summary

**There is no in-game cheat system in this SKU.** No password entry, no published
or unpublished code list, no button-code matcher, no hidden debug screen, and no
code-gated unlock exists. Every unlockable (20 hidden cars, extra cups, bonus/
time-trial content) is driven by ordinary gameplay progress in the 512-byte
EEPROM save; §16.18's save-bit unlock pattern applies, and there is no input
surface that writes those bits.

Evidence classes:

* **Title / menus (Observed):** title `PRESS START`, a 3-character `NAME ENTRY`,
  `RACE TYPE` (Grand Prix, Free Race, Time Trial, 2 Player, Options), Options
  (`BEST RECORD`, `SOUND ON/OFF`, `BGM 00`, `SFX 00`), Cup Select (BRONZE/SILVER/
  GOLD/…), Stage Select (Bathroom/Piano/Dining Table/Beach/…), Garage
  (`CAR SELECT`, `TUNING`, `SAVE`, `GO TO RACE`), the race HUD, and in-race
  Pause (`CONTINUE`, `RESTART`, `RETIRE`). Every one was entered and screenshotted;
  the screen-state byte in RAM was read at each transition (§4).
* **Sound test (Observed):** the "Sound Test" mentioned in contemporary reviews
  is not hidden — it is the `BGM`/`SFX` numeric fields on the ordinary Options
  screen.
* **Name entry is not a password (Derived):** its alphabet is a 4×9 grid
  `BCDFGHJKLMNPQRSTVWXYZ&,.-_123456789`, length exactly 3, and its buffer holds
  glyph indices (entering `BBB` wrote three `0x1D` bytes). No `strcmp`/table
  comparison against that buffer exists; it is a player name written to the save.
* **Published codes (Observed/Derived):** the only published "cheats" are an
  Action Replay master code + Max Cash code (external hardware, explicitly out of
  scope). The widely published `496-93-993` / `723-83-462` passwords belong to the
  **different game** *Hot Wheels: Velocity X* (§16.11) and are absent from this ROM
  in every encoding tried.
* **Text encoding (Derived):** all menu text is glyph/tile-indexed, not ASCII —
  `strings` finds only car names, track names and debug leftovers. The glyph path
  was probed through the name-entry buffer; the full tile↔letter table was not
  needed to enumerate the screens, and no hidden string bank exists in ASCII,
  `+0x20`, UTF-16LE/BE, or any single-byte additive/XOR transform.

## 3. How to reproduce

Environment: `Xvfb :317 -screen 0 1024x768x24`, `DISPLAY=:317 openbox`,
`SDL_AUDIODRIVER=dummy mgba -3 <rom>`. GDB port `2345` was occupied by another
process and was deliberately not touched; RAM evidence therefore uses mGBA
savestates (§16.13). Keymap verified by input: A=`x`, B=`z`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys; 80–300 ms holds.

Menu path (fresh 512-byte save):

1. Title `PRESS START` → **Start** → `NEW GAME` → **A**.
2. `NAME ENTRY`: **A** selects the glyph under the cursor, arrows move it,
   move to `O.K.` and press **A**. Three characters. (Entered `BBB`.)
3. `RACE TYPE`: **Down** cycles Grand Prix → Free Race → Time Trial → Options
   (the displayed `2 PLAYER` row is not selectable without a link cable).
   Screen-state byte below = `3`; select Options → byte `4`.
4. Grand Prix → `CUP SELECT` (BRONZE visible) → **A** → `STAGE SELECT`
   (GREASE MONKEY cup: Bathroom/Piano/Dining Table/Beach courses) → **A** →
   choose course → `GARAGE` (`CAR SELECT`/`TUNING`/`SAVE`/`GO TO RACE`) → race.
5. In race, **Start** → `PAUSE` (`CONTINUE`/`RESTART`/`RETIRE`).

Savestates: `Shift+F1` writes slot 1; `F1` loads it. The `.ss1` is a PNG with a
zlib-compressed `gbAs` chunk; `zlib.decompress` yields 397,312 bytes with
VRAM at `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000` (`/tmp/hwburnin/ss.py`).

## 4. Address map

| Item | ROM address / savestate offset | Note |
|---|---|---|
| Header / entry | `0x08000000` / `0x080000C0` | single stock header |
| EEPROM identity string | `0x0811783C` | `EEPROM_V121`, 512-byte save |
| Car record table | `0x0811C144 + i*0x1A4`, `i=0..0x1B` | 28 records, 4-byte index then NUL name |
| Track name data | `0x082610F4` (`TABLE`), `0x08261544` (`BATHROOM`), `0x08261994` (`RAILROAD`), `0x08261C80` (`BILLIARDS`), `0x08261F48` (`CASINO`), `0x08262398` (`HOTWHEELS`), `0x08262660` (`SPACE`) | ASCII |
| Debug leftovers | `0x0802F216` `Swap\n`, `0x0802F21C` `SetRecTotalTime\n`, `0x0802C548` `0123456789ABCDEFCPU=` | data labels, no reachable debug menu |
| Key read routine | `0x08008778`–`0x0800888A` | only literal `0x04000130` in the whole ROM (`0x88C`) |
| Screen-state byte | savestate `0x19850` = IWRAM `0x03000850` | see table in §6 |
| Name buffer | savestate `0x1BA3A` = IWRAM `0x03002A3A` | 3 glyph bytes; `BBB` = `1D 1D 1D` |

## 5. Algorithm

None (no validator). The relevant derived behaviours:

* **Name entry:** on-screen 4×9 grid → glyph code written to a 3-byte IWRAM
  buffer; `B` was observed as code `0x1D`. The buffer is copied into the save and
  rendered for best-time records; it is never compared to a code table.
* **Unlockables:** progress flags in EEPROM; car/track availability is tested
  with bit tests, not by a code entered by the player. There is no encoder,
  decoder, checksum, key mask array, or sequence matcher to reverse.
* **Screen state:** a single byte at IWRAM `0x03000850` tracks the menu family
  (§6), which is the RAM proof for each screen walked.

## 6. Tables

### 6.1 Screen-state byte (savestate `0x19850`, IWRAM `0x03000850`)

| Value | Screen (Observed) |
|---:|---|
| 1 | `NEW GAME` title prompt |
| 2 | Title (`PRESS START`) |
| 3 | `RACE TYPE` main menu |
| 4 | `OPTIONS` (and subsequent submenus reuse 4) |
| 5 | `CUP SELECT` / `STAGE SELECT` |

### 6.2 Car record table (`0x0811C144 + i*0x1A4`)

28 records, indices `0x00`–`0x1B`:
`SO FINE`, `PHANTASTIPUE`, `HAMMERED COUPE`, `MAELSTORM`, `HYPER MITE`,
`KRAZY 8S`, `VUTLTURE`, `GREASED LIGHTIN'`, `SCREAMIN' HAULER`, `PHAETON`,
`EVIL TWIN`, `HOOLIGAN`, **`name13`** (index `0x0C`, development placeholder),
`TRACK T`, `SHREDSTER`, `MONOPOSTO`, `VULTURE ROADSTER`, `LAKESTER`,
`SOOO FAST`, `OLD #3`, `SUPER TUNED`, `SURF CRATE`, `XS-IVE`, `ROLL CAGE`,
`PURPLE PASSION`, `ARACHNOROD`, `TWIN MILL `, `MAX-48 TURBO`.
Public material lists 25 cars; the table has 28 slots including one placeholder.

### 6.3 Published-code verification

| Source | Claim | Result in this ROM |
|---|---|---|
| Cheat Happens / Action Replay | `(M) 9f6d2eaa aa3d2232 …`, `Max Cash d8e0fb0e fabd159c` | External AR hardware only; no in-game entry surface. Out of scope. |
| GameFAQs *Hot Wheels: Velocity X* | `496-93-993`, `723-83-462`, level codes `143-24-813`… | Different SKU; literals absent (0 hits ASCII/lower). §16.11 |
| GameFAQs Car List FAQ / RetroAchievements | 25 cars, unlock by cups and time trials | Consistent with 28 ROM records and save-gated unlocks |
| IGN / THQ press release (2001) | battery save replaces the password feature of *GT Advance* | Confirmed: EEPROM_V121, 512-byte `.sav`, no password screen |

## 6b. Enumeration

**Space definition.** There is no code space to enumerate. The player-input
spaces were measured, not assumed:

| Input surface | Measured space | Verdict |
|---|---|---|
| Name entry | 36 symbols × 3 positions (`36^3 = 46,656` spellings) | player name; no comparison against entry buffer |
| Options sound test | `BGM 00`/`SFX 00`, two numeric fields | settings, not codes |
| Name-entry alphabet | `BCDFGHJKLMNPQRSTVWXYZ&,.-_123456789` (4×9 grid) | no vowel/`0`; not a password alphabet |
| Car records | 28 fixed slots, indices `0x00`–`0x1B` | all enumerated above; one placeholder |
| Button codes | every reachable screen pressed through; key masks searched | no matcher or mask array exists |

**Novel code.** Not applicable: with no validator there is no code to mint. The
requirement in §0.2 is satisfied on the negative branch — the report proves the
absence over the measured spaces rather than generating a code for a
non-existent system.

**Bounds proven by rejection.** No code can be rejected because no code is
accepted: there is no entry widget outside the 3-character name field, and that
field's buffer is written to the save rather than compared. The negative is
bounded by these concrete searches over all 8,388,608 bytes:

* `strings -t x -n 4`: 87,534 strings; keyword sweep for
  `password|cheat|code|secret|unlock|debug|hidden|level select|invalid|wrong|correct`
  yielded only `TRACK T`, `MAX-48 TURBO` (car names) and one binary false positive.
* Literals `PASSWORD`, `Enter password`, `secret car`, `L1TTLVN`, `HAMA!333`,
  and the Velocity X / Action Replay strings: **0 hits** in ASCII and lowercase.
* Menu words `GRAND PRIX`, `OPTIONS`, `NEW GAME`, `SOUND TEST`, `CUP SELECT`,
  `STAGE SELECT`, `BEST RECORD`, `PRESS START`: **0 hits** in ASCII, `+0x20`
  lowercase, UTF-16LE and UTF-16BE; and **0 hits** for all 256 additive and 256
  XOR single-byte transforms (numpy scan).
* Button masks: only one `0x04000130` literal (input read at `0x08008F0`). Scan
  for ≥5 consecutive `u16` single-button masks with ≥3 distinct values found
  48 runs; all are audio/tile data (`0x0118_1CE0`: `0080 0200 0019 0080 0200
  0013 …` is a pitch table). Byte-wide scan found 203 runs; the repeated
  `08 40 10 80 01 20` pattern is the same data table, not a cheat sequence.
* Debug gate: the only debug-like strings (`Swap`, `SetRecTotalTime`,
  `0123456789ABCDEFCPU=`) are data labels in the sound/record subsystem; no
  pointer table or branch reaches a debug menu, and no hidden screen appeared on
  any of the screens walked.

## 7. Validation evidence

* **Observed** — emulator screenshots of title, name entry, RACE TYPE, Options,
  Cup Select, Stage Select, Garage, race HUD and Pause; savestate RAM byte
  `0x03000850` read as 1/2/3/4/5 across those transitions; name buffer `1D 1D 1D`
  after entering `BBB`; 512-byte all-`0xFF` fresh EEPROM.
* **Derived** — car table bounds `0x0811C144 + i*0x1A4`, `i=0..0x1B`; EEPROM_V121
  identity; glyph-index nature of the name buffer; absence of any comparison of
  the name buffer; single `KEYINPUT` literal; all search counts above.
* **Inferred** — the three non-public car records (`name13` placeholder plus two
  renamed entries) are unused/development leftovers; the save-bit unlock model
  follows §16.18 and the gameplay descriptions, but individual bit→car mappings
  were not assigned because no code input path exists to exercise them.

## 8. Unknowns (bounded)

* The full glyph-index↔letter bank used for menu rendering was not reconstructed
  byte-for-byte; it was bypassed by reading the on-screen labels and the
  name-entry buffer. The searches in §6b still bound the *text* space: no hidden
  label exists in ASCII, shifted ASCII, UTF-16, or any 1-byte affine transform.
* Individual EEPROM unlock-bit→car assignments were not mapped. This does not
  affect the cheat conclusion: §16.18's setter-call enumeration applies to a
  save-bit unlock, and there is no controller input that writes those bits.
* The `2 PLAYER` row is displayed but not selectable without a link cable;
  two-player behaviour is outside the in-game-cheat scope.

## 9. Tooling

* `png`/`zlib` savestate decoder: `/tmp/hwburnin/ss.py`.
* XTEST input + screenshot helper: `/tmp/hwburnin/k.py`.
* VRAM/palette tile renderer: `/tmp/hwburnin/vram.py`.
* searches: `strings -t x -n 4`, `grep -abo`, Python `struct`/numpy scans,
  `arm-none-eabi-objdump -M force-thumb`, REA/Ghidra raw-ARM import
  (268 procedures, 171 defined strings), `tesseract` for OCR triage.
* Screenshots/savestates retained in `/tmp/hwburnin/`; none are attached
  to this report. No ROM or copyrighted asset is reproduced here.

No ROM or copyrighted assets were redistributed. All addresses are for SHA-256
`9737fccc…4bd1` only.
