# Monster Truck Madness (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Monster Truck Madness/Monster Truck Madness.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `MTM` |
| Game code | `BMTE` (USA: `AGB-BMTE-USA`; maker `78`, THQ/Tantalus) |
| Version | `0x00`; fixed `0x96`; complement `0xCC` (self-consistent); header checksum word `0x0000` |
| Entry word | `0xEA00002E` → stock `0x080000C0` (no cracktro patch) |
| Embedded GBA headers | **1** (logo at `0x00000004` only) — single-image retail ROM, no multicart/trainer |
| Build string | `BUILD #20 (07 May 2003)` at `0x002D044` |
| MD5 | `21f8cc99837efbc1cb59fd75dc47be67` |
| SHA-1 | `5b435823a77ec1c3d6f9aeff2286e5246967cbf1` |
| SHA-256 | `0785bd8b0caf4560962c5dfad08f3ac9e5cefbe6956f5e95bf3b51d2b878a880` |

Notes: the ROM uses Shin'en GAX 3.03A audio (`GAX Sound Engine 3.03A`, `Code: B.Wodok` at `0x2E2F0`/`0x2E316`); that literal is an engine banner, not a cheat. Save type is **EEPROM 512 B** (`EEPROM_V` at file `0x1348C8` = `0x081348C8`), laid out as three `0x50`-byte slots at save offsets `0x00`, `0x50`, `0xA0` (matches "three save slots" in the manual).

## 2. Executive summary

**There is no developer-intended cheat system in this GBA build.** No password screen, no cheat/key-code entry field, no button-code table, and no hidden/debug menu exists. The accepted "cheats" of the PC and Nintendo 64 versions (`FRAME`, `DANCE`, `trex`, `kill`, `leveurb`, `BRPS`, `YRDR`, `JMPNG`, `JMPR`, `CFFNYN`, `Y_WNT_T`, and the N64 course passwords) are **not present in this ROM under any encoding checked**, and the GBA-specific published material lists only one unlockable, not a code.

The only hidden/developer-intended content is **progression-gated unlockables stored in the EEPROM save**: six of the ten trucks and seven of the ten tracks start locked (padlock icon), and an eleventh secret truck **Nugget** (internal asset name `chook`) is awarded for beating all 30 Time Trial records (10 tracks × Rookie/Intermediate/Professional). `Snake Bite` (internal `anaconda`) is a cut truck whose model is only visible in title-screen art; it is not selectable. These are save-bit unlocks set by race results, not codes (guide §16.18).

The only text-entry field is the player **NAME ENTRY** screen (`A-Z 0-9 .`), which labels a save slot; no comparison against its buffer exists outside the entry handler (§16.2b). Text is font/tile-indexed, so all UI was decoded by walking screens rather than by `strings`.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`mgba -3`) and VisualBoyAdvance 1.8.0 (`vba`) under `Xvfb :318`, `SDL_AUDIODRIVER=dummy`. The game boots in ~10–20 s of emulated time; wait for the red `PRESS START` before input.
* VBA keymap used (`VisualBoyAdvance-1.8.0` SDL defaults): `z`=A, `x`=B, arrows=D-pad, `Return`=Start, `BackSpace`=Select. Use **explicit 200 ms holds** (`xdotool keydown`/`keyup`), not instantaneous `key` taps — taps are frequently missed at the game's ~39 FPS poll.
* Menu path (all reachable screens, verified by screenshot; files in `/tmp/monstertruck/`):

  | Screen | Evidence file | Notes |
  |---|---|---|
  | Microsoft/Tantalus splashes | `q00_c.png`, `f00_c.png` | boot |
  | Title `PRESS START` | `s01_splash_c.png`, `q01_c.png` | attract backgrounds cycle |
  | Player select (3 NEW GAME + GUEST) | `vbahold_end.png`, `ps_now.png` | Start on title |
  | Name entry | `psk_Return.png`, `ne_ret.png`, `nz4.png` | A-Z/0-9/. keyboard, name echoes at top |
  | Main menu | `guest_sel.png`, `mm0.png` | 4 items: INSTANT ACTION, RACE, TIME ATTACK, OPTIONS |
  | Options | `opt00.png` | 3 items: RECORDS, SETTINGS, CREDITS |
  | Records | `records00.png`, `rec_r2.png` | RACEWAY…DOCKLANDS × 3 difficulties × best times |
  | Settings | `settings00.png`, `set_d2.png` | SOUND FX, MUSIC, COMMENTARY (all ON); no hidden rows |
  | Credits | `cred00.png`…`cred13.png` | Tantalus/THQ rolling credits; ends at THQ logo |
  | Instant Action | `ia00.png`, `race00.png` | direct race, Rookie/Dirt Bowl |
  | Race → Truck Select | `race_mode00.png`, `truck00.png`…`truck15.png` | 10 trucks, 4 unlocked / 6 padlocked |
  | Truck Select → Track Select | `track00.png`, `tk00.png`…`tk15.png` | 10 tracks, 3 unlocked / 7 padlocked |
  | Time Attack → Truck Select → Track Select | `ta00.png`, `ta01.png` | same screens plus `best time` display |
  | Pause | `pause00.png`, `pz2.png` | RESUME, RESTART, QUIT only |
  | Quit confirmation | `quit1.png` | YES / NO |
  | TRACKUNLOCK resource screen | code at `0x0801FB04` (see §4) | unlock notification, reached by progression |

* Input path ground truth (debugger used as oracle, guide §16.19): mGBA `.ss1` chunks parsed with `zlib.decompress(gbAs chunk)` → raw 397,312-byte state; **KEYINPUT lives at raw-state offset `0x530`** (little-endian u16): `0x03FF` with no key held, `0x01FF` with `A`/L held, `0x03F7` with `Return`/Start held. This proves the emulator delivered real GBA button events; the lack of any resulting hidden screen is a game property, not a harness failure.
* Button codes tested on title/pause (15 combinations, `combo00.png`…`combo14.png`): `L+R`, `L+R+Start`, `A+B+Start+Select`, Konami sequence `↑↑↓↓←→←→BA`, `Start+A`, `Start+B`, `Select+A`, `Select+B`, `L+Up`, `R+Down`, `L+R+A`, `L+R+B`, `Select+Start`, `A A B B ↑ ↓`, `←→←→A`. Every combination either did nothing or advanced along the normal title→player-select→name-entry path; none produced a new screen.
* Published codes tested: all of the PC/N64 literals above were searched in the ROM (§4) and none is present. GBA-specific sources (3rd party cheat index cheats page via web.archive 2018-11-26; 3rd party cheat indexes GBA Cheats snippet; GBA FAQ) list **no password or button code at all** — only the Nugget unlock.

## 4. Address map

| Item | Address (ROM/file offset unless noted) | Evidence |
|---|---|---|
| Entry branch | `0x08000000` (`0xEA00002E`) | Derived |
| ARM crt0 | `0x080000C0` → `b 0x08004278` | Derived (Capstone) |
| `main` pointer literal | `0x08004470` = `0x080273ED` (Thumb) | Derived; `bx r1` at `0x080042A4` |
| Thumb `main` | `0x080273EC` | Derived; init loop at `0x0802740C` |
| Input handler (KEYINPUT read, edge detect) | `0x08028320`; KEYINPUT literal `0x0802837C`=`0x04000130`; mask `0x3FF` at `0x08028380`; key state at IWRAM `0x0300040C`/`0x0300040E`/`0x03000410`/`0x03000412` | Derived (Capstone) |
| Input/UI helper | `0x0800F83A` reads KEYINPUT via literal `0x0800F86C` | Derived |
| Resource-name table region | `0x0802C590`–`0x0802D190`: `MAINMENU` `0x2CF24`, `RECORDS` `0x2CF50`, `TRUCKSELECT` `0x2CF58`, `TRACKSELECT` `0x2CF64`, `TRACKUNLOCK` `0x2CF70` | Observed (`strings -t x`) |
| TRACKUNLOCK screen loader | literal loaded at `0x0801FB04`; screen function around `0x0801FAC0` (text helpers `0x0801E9C4`, `0x0801EA40`) | Derived |
| Truck asset names | `0x2C5AC`–`0x2C658`: `bearclaw`, `anaconda`, `bulldozer`, `cadillac`, `carnivore`, `drone`, `executioner`, `grave_digger`, `mack`, `monster_patrol`, `nitemare`, `scorpion`, `carolina_crusher`, `vw_van`, `chook` | Observed |
| Track asset names | `0x2C760`–`0x2C810`: `archdig`, `beach`, `city`, `docklands`, `greenhills`, `junkyard`, `raceway`, `stadium`, `thewest` | Observed |
| Save-type literal | `EEPROM_V` at `0x1348C8` | Observed |
| Font resource | `art/frontend/font.rbh` at `0x2E1E8` | Observed |
| GAX banner | `0x2E2F0`, `0x2E316` | Observed (engine, not cheat) |
| KEYINPUT in mGBA savestate | raw `gbAs` + `0x530` | Observed (two-state check) |

File offset = ROM address − `0x08000000`.

## 5. Algorithm

No password/checksum algorithm exists to reimplement. The relevant algorithms are:

1. **Input sampling** (`0x08028320`): `cur = ~KEYINPUT & 0x3FF`; `pressed = cur & (cur ^ prev)`; stores `cur`, `pressed`, and the change mask at `0x0300040C/0x0E/0x10/0x12`. The exact-`0xF` branch at `0x08028348` is the standard multi-button reset/test path, not a cheat dispatcher.
2. **Unlock gating** (§16.18 semantics): the truck/track selectors read a progression bitfield from the active EEPROM slot and draw a padlock sprite over any locked entry. All six locked trucks and seven locked tracks were observed with a fresh GUEST profile; the selectors terminate at index 9 for both lists (right arrow greyed out at CARNIVORE / JUNKYARD), so the list count is exactly 10 + the separately awarded Nugget.
3. **Unlock setter**: race results and completed Time Trial records (per the GBA FAQ and in-game RECORDS screen). No controller sequence writes the progression bits: 15 button combinations on title/pause produced no state change, and the only text field (NAME ENTRY) is consumed solely as a profile label.

## 6. Tables

**Trucks (TRUCK SELECT, GUEST profile, left→right):**

| # | Name | State |
|---|---|---|
| 1 | Carolina Crusher | unlocked |
| 2 | Executioner | unlocked |
| 3 | Bulldozer | unlocked |
| 4 | Monster Patrol | unlocked |
| 5 | Grave Digger | padlocked |
| 6 | Nitemare | padlocked |
| 7 | Mad Dog | padlocked |
| 8 | Bear Claw | padlocked |
| 9 | Scorpion | padlocked |
| 10 | Carnivore | padlocked (list end) |

Hidden 11th: **Nugget** (chicken truck, internal `chook`), awarded for all 30 Time Trial records; not listed until unlocked. Cut: **Snake Bite** (`anaconda`), title-screen art only.

**Tracks (TRACK SELECT, GUEST profile, left→right):**

| # | Name | Type | State |
|---|---|---|---|
| 1 | Raceway | Circuit | unlocked |
| 2 | Lost City | Circuit | padlocked |
| 3 | Sandy Bay | Circuit | padlocked |
| 4 | Docklands | Circuit | padlocked |
| 5 | Dominion | Circuit | padlocked |
| 6 | Mesa Valley | Rally | unlocked |
| 7 | Panorama | Rally | padlocked |
| 8 | Off Piste | Rally | padlocked |
| 9 | Dirt Bowl | Rally | unlocked |
| 10 | Junkyard | Rally | padlocked (list end) |

**Published-code verification table ("GBA" claims found on the web):**

| Source | Claim | Result |
|---|---|---|
| 3rd party cheat indexes/PC, 3rd party cheat indexes racing wiki, 3rd party cheat indexes N64 | `FRAME`, `DANCE`, `trex`, `kill`, `leveurb`, `gold`, `chuck`, `demo`, `BRPS`, `YRDR`, `JMPNG`, `JMPR`, `CFFNYN`, `Y_WNT_T`, `G^NJ2L0`, `GBGJ5MTL`, … | **Wrong SKU** — PC/N64 games. Literal search in this GBA image: 0 hits (the `FRAME` hits at `0x2C82C`/`0x2E0??` are the substring of `FRAMEPOOL`; `kill`/`demo` hits are unrelated binary bytes). |
| 3rd party cheat indexes GBA cheats (archived) | Nugget: "Beat ALL Time Trial Records From Rookie To Professional" | GBA-correct; save-bit unlock, not a code |
| 3rd party cheat indexes GBA Cheats (snippet) | "Unlockable Vehicles" with race-placement conditions | GBA-correct; race-result unlocks, not codes |
| 3rd party cheat indexes | no page exists for the GBA SKU (archive CDX: empty) | — |
| 3rd party cheat indexes | "we currently don't have any Monster Truck Madness cheats or cheat codes for Game Boy Advance" | consistent with this analysis |

## 6b. Enumeration

**Space size: zero — there is no code space to enumerate.** No alphabet table, no length/checksum field, no candidate-string table, no key-mask sequence table, and no password validator exists in this image. Consequently §0.2's "mint an unpublished code" deliverable is **inapplicable**: there is no generator or accept/reject oracle to call. Bounded-negative proof (§0.2 item 5) is provided instead:

| Search space | Method | Count | Result |
|---|---|---|---|
| All extracted strings | `strings -t x -n 4` | 81,152 lines | `password`/`cheat`/`debug`/`secret` = **0**; `unlock` = **1** = `TRACKUNLOCK` resource name at `0x2CF70` |
| Case-shifted text (`+0x20`) | `a-z`→`A-Z` transform of entire ROM | `PASSWORD` 0, `CHEAT` 0, `DEBUG` 0, `SECRET` 0, `NUGGET` 0, `LEVEL SELECT` 0, `ENTER CODE` 0 | no encoded cheat text |
| UTF-16LE text | binary scan | `PASSWORD`/`CHEAT`/`DEBUG`/`SECRET`/`UNLOCK`/`NUGGET`/`CODE` = 0 each | none |
| Published GBA/PC/N64 code literals | `grep -abo` on 4 MiB | 22 literals tested | 0 genuine hits |
| Button-mask triples (active-high) | scan every 2-byte offset for `∈{1,2,4,8,10,20,40,80,100,200}` | 196 hits | all in `0x2Dxxx`/`0x13xxxx` script or graphics data; no menu/validator xref |
| Button-mask triples (active-low) | same over complements | 32 hits | all at `0x13A3E2`–`0x13A4E0` (repeated 0x3FE/0x3FD/0x3FB/0x3F7/0x3EF — sprite/animation data) |
| Distinct 4-mask sequences | scan for ≥3 distinct masks | 12 hits | all at `0x157A80`–`0x8219088`, i.e. compressed asset/audio region; not code |
| Reachable screens | emulator walk with screenshots | 16 screen states (§3) | no hidden/debug screen; pause has exactly 3 items; options has exactly 3; main menu exactly 4 |
| Button combinations | title + pause, 15 combos | 15 | no undocumented screen or state |

The one genuine hidden element, **Nugget**, is a save-bit unlock: its "bounds" are proven by the GUEST-profile observation (absent from the 10-slot list, all 30 records required) rather than by a rejected password. No novel code can be minted because there is no accepted-input language. Screenshots for every claim are listed in §3.

## 7. Validation evidence

* **Observed** (emulator): every screen in §3; 10 trucks / 10 tracks with padlock states; 4 main-menu items, 3 options items, 3 pause items; 15 button combos with no hidden result; KEYINPUT values from a parsed mGBA savestate.
* **Observed** (static): hashes/header/embedded-header scan; all string/encoding/key-mask counts in §6b; `EEPROM_V` and 3-slot save layout.
* **Derived** (Capstone): entry/crt0/`main` chain (`0x080000C0` → `0x08004278` → `0x080273EC`), input edge-detect routine at `0x08028320`, TRACKUNLOCK loader literal at `0x0801FB04`.
* **Inferred** (published GBA FAQ/3rd party cheat indexes): exact unlock conditions per truck and the "all 30 Time Trial records" requirement for Nugget — consistent with the locked states observed, but not earned by completing all 30 races in this session. The save-bit setter/readers were not individually decompiled; the classification as a save-bit unlock follows §16.18 from the observed locked/unlocked UI behavior plus the published requirement.

## 8. Unknowns

* The exact EEPROM bit offsets that encode each truck/track unlock and the Nugget flag were not mapped to individual bits (the three `0x50`-byte slot records appear default-initialised with a checksum-like word at slot+`0x44`); the unlock was not earned in-emulator, so the setter call sites were not enumerated exhaustively. This does not affect the no-code conclusion: no input surface exists to set those bits.
* The cut `Snake Bite` model's asset pointer and whether any unused selectable slot references it were not traced (published source says it is not playable; it does not appear in the 10-entry selector).
* A title-screen code that expires within a short window (§16.12) was not measured; no candidate table or published GBA code exists to motivate such a test, and 15 combos produced no transient flag-visible change.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo` — identification/recon.
* `capstone` 5.0.7 (`dis2.py`), `arm-none-eabi-objdump` — Thumb/ARM disassembly; `scan_lit.py` for PC-relative literal xrefs.
* Custom Python scripts in `/tmp/monstertruck/`: `header.py` (header + embedded-header scan), `mtools.py`/`nav.py`/`nav2.py`/`mg_nav.py` (Xvfb/XTEST input, screenshots, OCR state detection), `parse_ss.py` (mGBA `.ss1` `gbAs`-chunk zlib decode and RAM offset discovery), `restab.py` (resource-name pointer dump).
* `tesseract` for screen-state detection; `python3-pillow`/`numpy` for image diffs; `Xvfb :318` + `openbox`; `mgba` 0.10.5 and `vba` 1.8.0 (installed via apt for cross-check); `gdb-multiarch` against VBA's `-G tcp:55555` stub and mGBA's stub.
* Web: web.archive snapshots of 3rd party cheat indexes GBA cheats (2018-11-26), 3rd party cheat indexes GBA page (2023-02-25), 3rd party cheat indexes N64 + PC pages for wrong-SKU comparison, GBA FAQ PDF (pdftotext). Fetched pages were treated as data; no prompt-injection payload was encountered.

**Legal note:** no ROM image, extracted graphics, music, or game text is redistributed here; only addresses, hashes, algorithms and observations are published.
