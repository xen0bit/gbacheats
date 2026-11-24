# Disney Sports Football (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney Sports Football/Disney Sports Football.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| Header title | `DS-FOOTBALLU` |
| Game code | `A3DE` (serial AGB-A3DE-USA) |
| Maker code | `A4` (Konami) |
| Software version | 0x00 (Rev.00) |
| Fixed byte 0xB2 | 0x96 |
| Complement check 0xBD | 0x73 — **valid** (computed 0x73) |
| Header checksum 0xBE | 0x0000 (standard computation 0x058D; a zeroed field is the usual artifact of a rebuilt header, while the entry word and complement are stock) |
| Entry word 0x00 | `0xEA00002E` — stock ARM branch to 0x08000180, no cracktro |
| Nintendo logo | two copies: 0x004 and 0x0C4 (the whole 0x100-byte boot block is duplicated at 0xC0; both entry words branch to 0x08000180). This is the normal Konami layout for this build, not a multi-game pack: only one image, one crt0. |
| MD5 | `86f872eafa573d4535e5f536ab7f5d2b` |
| SHA-1 | `c806b83f73defce9fcf269b9023fc1cc6dbf356c` |
| SHA-256 | `c490b8693a1e0a9083346f338da531580ceff4042a25a312521f179999b1a92a` |

No trainer/cracktro markers (`SUNHORS`, `CRC BANDIT`, `MODE7`, `CRACK`, `TRAINER`,
`PARADOX`, `EURASIA`, `INDEPENDENT`) occur anywhere in the image. The first 4 KiB
is ordinary crt0 code and literal pools. mGBA auto-detected **512-byte EEPROM**
and created a 512-byte `.sav`, which stayed all-`0xFF` through every menu
operation performed here (see §7).

## 2. Executive summary

**There is no password, no button cheat code, and no player-reachable debug
menu in this ROM.** The game has no code-entry surface and no user text input at
all. UI labels are rendered from art rather than from a searchable character
map: the usual words ("PASSWORD", "CODE", "DEBUG", "CONTINUE", "TEAM") exist
nowhere in the 16 MiB in ASCII, case-swapped ASCII, UTF-16LE/BE or any of the 91
valid LZ77 payloads, and ten visible labels have no linear alphabet mapping in
the VRAM tilemaps. That makes the usual string-led attack surface empty, and the
negative therefore rests on screen enumeration, table scans, key input analysis
and published-code testing (§§6b, 7).

What was established:

1. **No KCEK debug framework.** The sibling titles (*Disney Sports: Soccer* / EU
   "Football", and *Disney Sports Basketball*) carry a KCEK `AGB SYSTEM Ver3.00`
   string bank, `L+R+START SOFT RESET`, `L+R+SELECT MEM+DMA DEBUG`, a
   `DEBUG MENU`/`PAGE %d` renderer and a debug page table. This USA American
   Football build contains **zero** occurrences of every one of those strings in
   every encoding searched, and **zero** code references to the sibling RAM
   gate addresses (`0x02000430`, `0x02000240`, `0x02000270`, `0x0200FA60`).
   Both documented combos were pressed in the attract demo, the GAME MODE
   menu and the PRACTICE menu: **inert** at both menus. The only "restart"
   observable belongs to the attract loop and is reproduced by **Start alone**
   (control experiment, §7); it is not a reset combo.
2. **No button-sequence cheat table.** The ROM reads `KEYINPUT` at exactly two
   literal sites (`0x080004AC`, `0x08000D1C`); a whole-image scan of button-mask
   runs (154,770 raw in-set u16 runs; 572 runs of ≥4; the 8 runs with ≥4
   distinct masks) found only code bytes and ASCII/data coincidences. There is no multi-press sequence table, no
   `0x30C`/`0x304` combine-and-compare in code, and no keyed dispatcher.
3. **No unlock is gated by input.** All **7 teams** and all **7 stadiums** are
   selectable immediately on an empty save (`.sav` absent or all-0xFF), including
   STEAMROLLERS and IMPERIALS, which are the two teams that *Basketball* locks
   behind Challenge progression. The rings wrap at 7 in both cases (observed
   twice each). Any further content (trophies/all-star sides) is a
   save-progress flag, not a code (§16.18 pattern), and no code can set it.
4. **One published "code" exists for this SKU and is not a GBA code.** 3rd party cheat indexes'
   GBA page lists exactly one entry: *Get Unlimited Magic GC — Y, Y, Y, Y, Y, B,
   A, Y, entered at the title screen.* The GBA has no Y button; the "GC" label
   and the button vocabulary identify it as a GameCube-pad code cross-filed on
   the GBA page. It is therefore not expressible on this platform and was
   recorded as inapplicable, not "rejected" (§6b.3).
5. **The in-game options are ordinary settings.** OPTION holds four rows:
   BGM ON/OFF, MAGIC ON/OFF, MINES ON/OFF, RESET SAVE DATA NO/YES, plus OK.
   MAGIC and MINES are also exposed in GAME RULES before a match. None is a
   cheat, developer switch or hidden mode.

The negative is bounded rather than assumed: 14 distinct screens were walked,
the text space is characterized (0 ASCII/UTF-16/LZ77 text hits out of 16 MiB
and 0 linear alphabet mappings in VRAM), the button space is counted (2 KEYINPUT
reads, 0 sequence tables), the sibling debug addresses are shown unreferenced,
and the single published code is analysed and tested as far as the hardware
permits.

## 3. How to reproduce

Emulator: mGBA 0.10 (`mgba -3`), Xvfb `:312`, `openbox`, `SDL_AUDIODRIVER=dummy`.

```
Xvfb :312 -screen 0 1024x768x24 &
DISPLAY=:312 openbox &
DISPLAY=:312 SDL_AUDIODRIVER=dummy mgba -3 "Disney Sports Football.gba" &
```

Keys (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad arrows. Hold 60–120 ms; a 150 ms hold can double-step
the team/stadium rings.

Boot sequence: Konami logo → Disney Interactive logo → intro cutscene →
title art with `PRESS START` → Start → `GAME MODE`.

Exact paths used:

| Screen | Path |
|---|---|
| Title | boot, wait through intro (~20 s) |
| Attract demo | title, wait without input; a CPU-vs-YOU match plays. **Start restarts the intro from the publisher logos.** |
| GAME MODE | title → Start. Four rows: CHALLENGE / EXHIBITION / PRACTICE / OPTIONS |
| TEAM SELECT | CHALLENGE → A, or EXHIBITION → A, or PRACTICE → A. Left/Right = team ring (7), A = pick, then P2 ring |
| GAME RULES | TEAM SELECT → A (both sides) → QUARTERS 1–4, TIME 3/5/…, MAGIC ON/OFF, MINES ON/OFF, GO TO GAME |
| Kickoff | GAME RULES → Right (cursor to GO TO GAME) → A → `1ST CHALLENGE` matchup card |
| Coin toss | A through the card → COIN TOSS (HEADS/TAILS, then RECEIVE/KICK OFF) |
| Play | coin toss → A. OFFENSE play-call screen (FORMATION + diagram) |
| PAUSE | in play, Start → TIMEOUT / STATS / TEAM SETTING / RETURN / QUIT |
| QUIT | PAUSE → QUIT → A: immediate return to GAME MODE; no confirmation, no results or save screen (observed) |
| STATS | PAUSE → STATS: SCORE, RUSHING YDS, PASSING YDS, TOTAL YARDS, TURNOVERS (5 rows) |
| DEPTH CHART | PAUSE → TEAM SETTING: OFFENSE/DEFENSE tabs (L/R), positions QB/RB/RB/WR/WR/WR/TE/TE/C/KP…, STR/SPD/AGI |
| STAGE SELECT | PRACTICE → TEAM SELECT (P1+P2) → STAGE SELECT: 7 stadiums, Left/Right |
| PRACTICE menu | STAGE SELECT → A: OFFENSE / DEFENSE / KICKOFF RETURN / KICKOFF |
| OPTION | GAME MODE → OPTIONS: 4 rows + OK |
| Title restart | B at GAME MODE returns to the logo/intro loop; Start during the attract demo also restarts the intro |

Note the two control facts that cost time if missed: (a) Start during the intro
skips straight to GAME MODE, so the `PRESS START` title is only seen if you let
the intro finish; (b) an idle title drops into an attract match, so "the game is
in gameplay" does not mean any input was accepted.

## 4. Address map

ROM addresses are `0x08000000 + file_offset`.

| Address | Contents |
|---|---|
| `0x000000`–`0x0001FF` | boot block duplicated at 0x000 and 0x0C0; entry `EA00002E`; crt0 at 0x180 |
| `0x0001B4` | crt0 stack pointer literal (`0x03007F00`) |
| `0x000428` | key/VSync helper: reads `KEYINPUT` (`0x04000130` literal at `0x0004AC`), forms `keys ^ 0x3FF`, calls the scheduler at `0x080740C4`; key-repeat timing word at `0x02001370` |
| `0x000D1C` | second `0x04000130` literal (early init / key-state seed) |
| `0x004698` | script-VM bytecode interpreter: reads opcode, high bit = extended, low bits index a 4-byte jump table; 21 cases for opcodes `0xEB`–`0xFF` |
| `0x08B10A84` | script-opcode jump table (22 entries, referenced from `0x080046F0`, `0x0800532C`, `0x08005384`) |
| `0x08B109EC`, `0x08B10AEC`, `0x08B10FF0` | further dispatch/function-pointer tables used by the engine |
| `0x0809A720` | sleep/stop + SIO/timer helper (touches `0x04000208`, `0x03007FF8`, `0x04000128`, `0x0400010E`) |
| `0x001BBC40`–`0x001BBFFC` | ASCII name bank: 113 names in 8-byte slots (`09` terminator), including `Mortimer`, `PETE`, `GOOFY`, `DONALD`, `MICKEY`, plus generic given names. This is the only substantial ASCII text in the image. |
| `0x00083000`–`0x00083xx` | table of 0xFD-byte (253-byte) blocks with `0x0E000000` (SRAM) references and varying sub-offsets; save/asset block descriptor (stride/field order not fully decoded — see §8) |
| `0x02001370` | key-repeat timing word (read at `0x0800043A` via literal `0x080004B8`) |
| `0x02007E80`–`0x02008000` | runtime roster: 8-byte name slots copied from the ROM name bank, with per-player pointers back into `0x081BBxxx` |
| `0x02000300`, `0x02006C3C`, `0x0200743C`, `0x02007EE0` | screen/menu state candidates (change on every screen transition; exact role not assigned) |
| `0x02000200`–`0x0200xxxx` | general engine/game state (EWRAM). No sibling-title debug gates exist here. |

Absent by measurement (0 occurrences of the 4-byte literal): `0x02000430`,
`0x02000240`, `0x02000270`, `0x0200FA60`.

## 5. Algorithm

### 5.1 There is no validator to reimplement

No password/cheat constant, alphabet table, checksum or input comparison exists:

* The game never reads a text-entry buffer. No text-entry screen was reached in
  14 screens, and the only keyboard-like interaction in the game is menu
  navigation.
* `strcmp`-style consumers would require character codes; the image contains
  none for UI text (§5.2).
* The only user-adjustable values are option/rule settings (BGM/MAGIC/MINES,
  QUARTERS, TIME) and menu cursors.

### 5.2 Text is pre-rendered art, not characters

This determines what a "strings" negative means for this ROM:

* 0 hits for 20 keyword families (`password`, `passwd`, `cheat`, `secret`,
  `unlock`, `hidden`, `debug`, `code`, `continue`, `invalid`, `clear`, `bonus`,
  `extras`, `gallery`, `sound test`, `staff`, `kcek`, `agb system`,
  `soft reset`, `mem+dma`) in case-insensitive ASCII over the whole 16 MiB.
* 0 hits for the five most diagnostic markers in ASCII, swap-case ASCII,
  UTF-16LE and UTF-16BE.
* 91 valid GBA-LZ77 blocks were decompressed; none contains any of those words.
* After loading each screen, EWRAM/IWRAM contain no ASCII text (only the
  8-byte name slots and pointers into the name bank).
* Ten visible labels were tested for a linear alphabet mapping in the VRAM
  tilemaps (`SELECT`, `TEAM`, `CHALLENGE`, `OPTIONS`, `SUPERSTARS`, `SEADUCKS`,
  `PAUSE`, `STATS`, `DEPTHCHART`, `FORMATION`); **0** matches. That is
  consistent with pre-rendered label strips (BG/OBJ art) rather than font
  indices; a non-linear font index map cannot be excluded by this test alone,
  which is why the screen walk and the input-consumer analysis carry the
  negative.

Consequence: a `strings`-based "no password text" result is necessary but not
sufficient here, exactly as in the bitmap-text case of the guide (§16.11). The
screen enumeration and the absence of any input consumer carry the negative.

### 5.3 Screen/menu machinery

The engine is an event/script-VM design (interpreter at `0x08004698`), with
pre-rendered labels stored as resource strips and menus built from small
objects in EWRAM. There is no switch that dispatches to a developer page: the
only reachable top-level states are TITLE/ATTRACT, GAME MODE, TEAM SELECT,
GAME RULES, STAGE SELECT (Practice only), PRACTICE, PAUSE, STATS, DEPTH CHART,
OPTION. Each is entered from the menu paths in §3; none is entered by a RAM
byte or button combination.

### 5.4 Key input

```
keys_raw   = REG_KEYINPUT (0x04000130)          ; literal at 0x080004AC (used 0x08000428)
                                                 ; second literal at 0x08000D1C
pressed    = keys_raw XOR 0x3FF                 ; 0x08000430
```
Only these two `KEYINPUT` reads exist in the image. No code combines key bits
into a multi-press mask constant: the only `0x30C`/`0x304` values in the file
are graphics/audio bytes (all 8 dword hits lie inside compressed art; none is
adjacent to a load/compare instruction).

## 6. Tables

### 6.1 Top-level and per-mode tables

| Table | Entries | Values |
|---|---|---|
| GAME MODE menu (observed) | 4 | CHALLENGE, EXHIBITION, PRACTICE, OPTIONS |
| TEAM SELECT ring (observed) | 7 | SUPERSTARS, SEADUCKS, SPACE NUTS, STEAMROLLERS, IMPERIALS, FLYING FOWL, LORDS |
| STAGE SELECT ring (observed) | 7 | MICKEY'S SUPER-STAR CENTER, SS CANTANKEROUS, VISTA ARENA, STEAMROLLER DOME, AERO FIELD, THE BELLE'S MALL PARK, PRIDE COLISEUM |
| GAME RULES (observed) | 4 + GO | QUARTERS 1–4 (min 1, clamped), TIME 3/5/…, MAGIC ON/OFF, MINES ON/OFF, GO TO GAME |
| PAUSE (observed) | 5 | TIMEOUT, STATS, TEAM SETTING, RETURN, QUIT |
| STATS (observed) | 5 | SCORE, RUSHING YDS, PASSING YDS, TOTAL YARDS, TURNOVERS |
| DEPTH CHART (observed) | 2 tabs × 10+ rows | OFFENSE/DEFENSE; Pos, No, NAME, STR, SPD, AGI |
| OPTION (observed) | 4 + OK | BGM, MAGIC, MINES, RESET SAVE DATA |
| PRACTICE submenu (observed) | 4 | OFFENSE, DEFENSE, KICKOFF RETURN, KICKOFF |

### 6.2 Roster / name bank

`0x081BBC40`–`0x081BBFFC`: 113 names in 8-byte slots (`09` terminator; an
8-character name like `Mortimer` fills its slot with no terminator). The bank
opens with a 16-entry short-name group (`Tiger`, `Chum`, `Cad`, `Clod`,
`Spotty`, `Fifi`, `Normo`, `Sparky`, `Fido`, `Jason`, `Charlie`, `Rover`,
`Luigi`, `Josh`, `Martin`, `Arnie`) and continues with the roster names:
`Mortimer`, `Denny`, `Dante`, `Rumble`, `Rocco`, `Reg`, `Lucky`, `Johnny`,
`Tor`, `Ryan`, `Leo`, `Socks`, `Lincoln`, `Igor`, `Ivan`, `Zach`, `Samson`,
`Deano`, `Guy`, `Fritz`, `Liz`, `Theresa`, `Jan`, `Michelle`, `Erica`, `Nate`,
`Hector`, `Simon`, `David`, `Bucky`, `Big Lou`, `Nicky`, `Earl`, `Joe`,
`Pauly`, `Marc`, `Otho`, `Rufus`, `Sal`, `Lloyd`, `Slim`, `Pug`, `Don`, `Gus`,
`Andre`, `C.J.`, `PETE`, `Ted`, `Ned`, `Sigmund`, `Wally`, `Willy`, `Harry`,
`Hank`, `Stan`, `Barney`, `Cletus`, `Otis`, `Skip`, `Jess`, `Chip`, `Freddy`,
`Herbert`, `GOOFY`, `Buck`, `Coop`, `Marvin`, `Jimmy`, `Scruffy`, `Slappy`,
`Chuck`, `Danny`, `Carl`, `Al`, `Malcolm`, `Ken`, `Frank`, `Peter`, `Calvin`,
`Keith`, `DONALD`, `Tom`, `Kurt`, `Jim`, `Wayne`, `Sam`, `Roy`, `Mike`, `Pat`,
`Bill`, `Jack`, `Scott`, `Dave`, `Steve`, `Bob`, `Dan`, and `MICKEY` at
`0x081BBFF4`. The runtime copy lives at `0x02007E80`+; the DEPTH CHART renders
the first ten uppercased: `MICKEY, DAN, BOB, STEVE, DAVE, SCOTT, JACK, BILL,
PAT, TOM`.

## 6b. Enumeration

### 6b.1 Space definition

**There is no code space: 0 alphabets, 0 lengths, 0 checksums, 0 validators,
0 table-of-codes.** The engagement therefore enumerates the menu surface, the
text space and the button space so the negative is bounded.

| Space | Size | Result |
|---|---|---|
| Code-entry screens | 0 of 14 walked screens | none |
| User text fields | 0 | name bank is a fixed roster, never edited by input |
| ASCII text (all encodings) | 16,777,216 B searched; 172,697 printable runs ≥4 | 0 password/cheat/debug strings; only one real text bank (0x3BC B of player names) |
| LZ77 blocks | 91 decompressed | no text/UI strings |
| `KEYINPUT` read sites | 2 (`0x080004AC`, `0x08000D1C`) | no multi-press combos |
| u16 button-mask runs | 154,770 raw runs; 572 with ≥4 | 8 with ≥4 distinct masks; all code/data bytes, no sequence table |
| `0x30C` dword literals | 8 | all inside compressed art (verified by disassembly) |
| Sibling debug gates | 4 addresses × 2 encodings | 0 references |
| KCEK banner strings | 21 markers × 4 encodings | 0 |
| Teams | 7 selectable on empty save | ring wraps at 7 |
| Stadiums | 7 selectable on empty save | ring wraps at 7 |

### 6b.2 Unpublished/undocumented findings

1. **The attract-demo "reset" is Start, not a code.** During the attract match a
   single Start press restarts the publisher-logo sequence. The same Start has
   no reset effect at GAME MODE, TEAM SELECT, GAME RULES or PRACTICE. This is a
   control experiment that invalidates the tempting "L+R+START soft reset"
   reading of the same observation.
2. **All seven teams and all seven stadiums are available on an empty save**,
   including STEAMROLLERS and IMPERIALS. In the sibling *Basketball* those two
   are Challenge-locked. This game's unlock pressure (if any) is therefore on
   tournament trophies/all-star sides, not the base ring.
3. **`TIME` steps 3 → 5** (not 1-minute steps), and `QUARTERS` clamps at 1
   (pressing Left at 1 does nothing). These are the only numeric rule fields;
   they are bounded and cannot express anything else.
4. **The Practice mode is the only place with a stadium select.** CHALLENGE and
   EXHIBITION go straight from TEAM SELECT to GAME RULES; the stadium is
   implicit. No published description of this US SKU's paths was found.
5. **The UI labels behave as pre-rendered art.** `SELECT TEAM.` and every menu
   label have no character-code representation and no linear font map, so the
   words never exist as searchable bytes. This is the reason a keyword scan
   cannot be the primary negative for this title.

### 6b.3 Published codes/claims tested

| Claim | Source | Test | Result |
|---|---|---|---|
| `Y, Y, Y, Y, Y, B, A, Y` at title screen → Unlimited Magic | 3rd party cheat indexes GBA cheats page (also cross-listed under the 2-in-1 Skateboarding+Football page) | Title screen reached and held; the sequence requires a **Y** button, which the GBA does not have | **Inapplicable** — GameCube-pad code cross-filed on the GBA page (label `GC`, Y button). Not enterable on this hardware. |
| `Up, Up, Down, Down, Left, Left, Left, Right, B, A` → Hidden Board | 3rd party cheat indexes 2-in-1 page | The code is explicitly for *Disney Sports Skateboarding* on the same cart page | Skateboarding-only code; excluded from the Football claim set |
| "Secret teams (Captain Hook's Pirate Squad, Pete's Bad Boys) unlock after winning the main tournament on Normal" | playeretro.cc (SEO aggregator) | Conflicts with the ROM's observable ring (all 7 sides, including Pete's STEAMROLLERS, are selectable at boot); Captain Hook is not part of this game's cast | **Unverified / contradicted** — treat as fabricated |
| "Game clear unlocks Pete and Mickey All-Star" | 3rd party cheat indexes blog comment | Consistent with a save-progress unlock of extra sides; not a code | **Consistent** with a save-progress unlock; the side is not input-reachable as a code |
| CodeBreaker/GameShark lists (Infinite Time, Always 1st Down, etc.) | 3rd party cheat indexes/almars/3rd party cheat indexes | RAM-write codes, out of scope as cheats | Used only as address hints; not deliverables |

### 6b.4 Novel codes

**None can be minted, because there is no code system.** This report does not
claim a generated password: the deliverable for a no-system title is the bounded
negative (§0.2 item 5), which §§6b.1–6b.3 supply. Stated positively: across
16 MiB, 14 screens, 4 top-level modes, 7 teams, 7 stadiums, 2 KEYINPUT sites,
154,770 mask runs and the complete published-claim set for this SKU, there is no
input path that accepts a code, so no code exists that could be unpublished.

### 6b.5 Bounds proven by rejection

* **Team ring**: pressing Right from LORDS returns to SUPERSTARS (7 positions);
  no 8th entry, no wrap-to-hidden page.
* **Stadium ring**: 7 positions, wraps MICKEY'S SUPER-STAR CENTER ← PRIDE
  COLISEUM; no 8th.
* **GAME MODE**: 4 rows; Down from OPTIONS does not open a 5th row.
* **OPTION**: 4 settings + OK; Down from RESET SAVE DATA reaches OK, then the
  screen exits. No hidden row.
* **QUARTERS**: at 1, Left is rejected (stays 1); the field cannot express 0.
* **TIME**: at 3, Left stays 3; Right gives 5, i.e. 1- and 2-minute values are
  not representable.
* **Combos**: `L+R+START` and `L+R+SELECT` rejected (no state change) at GAME
  MODE and PRACTICE; in the attract demo the observed restart is reproduced by
  Start alone, and no `0x30C`/`0x304` combine exists in code.
* **Sibling debug gate**: no reference to `0x02000430` exists, so writing 2
  there cannot open anything; the Soccer debug-page table is not compiled into
  this build (0 banner strings).

## 7. Validation evidence

**Observed (emulator, screenshots, RAM reads):**

* Screens walked: title art (`PRESS START`), attract demo, GAME MODE,
  TEAM SELECT (two rings), GAME RULES, matchup card (`1ST CHALLENGE`),
  COIN TOSS (HEADS/TAILS → RECEIVE/KICK OFF), OFFENSE play-call, PAUSE,
  STATS, DEPTH CHART, STAGE SELECT, PRACTICE submenu, OPTION. 14 distinct
  screens.
* Team ring enumerated by Right presses with 0.5 s spacing. From SUPERSTARS the
  ring is SEADUCKS → SPACE NUTS → STEAMROLLERS → IMPERIALS → FLYING FOWL →
  LORDS → SUPERSTARS: exactly 7, verified over 8 consecutive presses twice.
  Same for the 7 stadiums.
* All 7 teams and 7 stadiums selectable with no save file present; a match was
  started and played (score 0-0, quarter clock running) to confirm the flow.
* `L+R+START` and `L+R+SELECT` produce no reset, no debug screen and no visible
  state change at GAME MODE and PRACTICE. A single Start during the attract demo
  restarts the logo/intro sequence (control experiment).
* OPTION toggles change on screen (BGM ON→OFF), OK applies and returns to GAME
  MODE. RESET SAVE DATA YES was selected but not applied; OK was used with
  NO afterwards. The 512-byte `.sav` stayed all-`0xFF` throughout.
* Savestate RAM reads: EWRAM `0x02000430` = 0x00 at the title (read from the
  `.ss2` state); no code references the address. EWRAM contains the roster copy at
  `0x02007E80` and no ASCII UI text.
* VRAM tilemap scan for 10 visible labels: no linear alphabet mapping.

**Derived (disassembly / tables):**

* `KEYINPUT` literal sites = 2; key helper at `0x08000428`; `pressed = raw ^
  0x3FF`.
* Script-VM interpreter at `0x08004698` with a 22-entry opcode jump table at
  `0x08B10A84` (opcodes 0xEB–0xFF).
* No literal `0x30C`, `0x304`, `0x308` adjacent to a compare; the 8 dword hits
  are inside compressed graphics/audio.
* No reference to the sibling debug gates; no KCEK banner strings in any
  encoding.
* ASCII name bank with 113 names at `0x081BBC40`–`0x081BBFFC`.

**Inferred:**

* The visible labels are pre-rendered art: no character encoding and no linear
  VRAM mapping reproduces them. The exact resource format of a label strip was
  not reversed.
* The `0xFD`-byte/`0x0E000000` block table at `0x00083000` is the save/asset
  block descriptor; its field order was not decoded (§8).
* Progression unlocks (all-star sides, trophies) are save bits, by analogy with
  the sibling title and the 3rd party cheat indexes clear report; the save bit positions were
  not decoded because no save data could be produced through menus alone.

## 8. Unknowns

* Exact layout/checksum of the 512-byte EEPROM record and the meaning of the
  `0xFD`-byte block table at `0x00083000`. The `.sav` stayed all-`0xFF` after
  every menu operation and after emulator shutdown, so no real record existed to
  diff; the save path is a tournament-clear event, and a clear is a gameplay
  state, not an input code. This does not affect the code-system result: no
  input accepts a string or button sequence anywhere in the ROM.
* Whether clearing the tournament adds extra sides/characters to TEAM SELECT
  (3rd party cheat indexes report Pete + Mickey All-Star). This would be a save bit set by a
  win handler (§16.18), not a code; the 7-team/7-stadium ring is the complete
  set available to input on an empty save.
* Whether a developer page with art-only labels exists. Strings cannot answer
  this because all labels are art, so the claim rests on: 0 KCEK banner strings,
  0 references to the sibling RAM gates, both sibling combos inert, and the
  complete 14-screen walk. The reachable screen set is enumerated; no
  unreachable launcher was found in the 11 function-pointer tables scanned.
* Player-visible mapping of the 7 developer team/stadium names to their
  pre-rendered labels (labels are art; developer names are not present as text).
* Role of the script VM in menus (menus are data-driven; no script opcode was
  tied to a code/password function).
* The 7th team label reads `LORDS` on the TEAM SELECT bar; the name is rendered
  consistently on every visit.

## 9. Tooling

* mGBA 0.10 (`mgba -3`), Xvfb `:312`, openbox, ImageMagick `import`/`convert`/
  `montage`; `xdotool` for XTEST input.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M
  force-thumb` for targeted ranges.
* Python 3 + `capstone` 5.0.7 for targeted Thumb checks (installed; used for
  literal/pool verification).
* `lz.py` — GBA-LZ77 block scanner/decompressor (91 blocks, no UI text).
* `state.py` / `st.py` — mGBA `.ssN`/`.png` reader: zlib-decompress the `gbAs`
  chunk; IWRAM at raw `0x19000`, EWRAM at raw `0x21000` (layout confirmed by
  total size 397,312 B = 0x61000 and by known globals). Used to read
  `0x02000430`, diff screens, and scan VRAM for label encodings.
* `scan_results.txt` — keyword/encoding/mask-run counts quoted in §6b.
* No ROM patch was applied; the `.gba` was never modified.

## 10. Legal note

No ROM, graphics, music or extracted text is redistributed. Only hashes,
addresses, table layouts and the analyst's own notes are published here.
