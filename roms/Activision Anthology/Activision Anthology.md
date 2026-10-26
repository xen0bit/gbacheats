# Activision Anthology (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Activision Anthology/Activision Anthology.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `ACTANTHOLOGY` |
| Game code | `BAVE` |
| Maker code | `FM` |
| Software version | 0x00 (Rev.00) |
| Entry branch | `0xEA00002E` → `0x080000C0` |
| Fixed byte 0xB2 | `0x96` |
| Complement check | stored `0x13`, computed `0x13` (valid) |
| Header checksum | stored `0x0000` (not the usual computed value `0x05ED`; tolerated) |
| MD5 | `5f3567dd3487f600dd2962c2fe73844f` |
| SHA-1 | `5125bbbbf1df7782590d99273735826636a2f9ba` |
| SHA-256 | `3848b99ff114cde1c8ba7f162ffb9dcab77fc676871da703b82132ce1743ce32` |
| Save type | 4 Kbit EEPROM, 512 bytes (`Activision Anthology.sav`) |

The file also contains a **second complete GBA header** at file offset
`0x2A6B14` (Nintendo logo at `0x2A6B18`), title `ANTHOLOGY`, code `ANTH`,
maker `FM`, same entry branch. It is followed immediately by the strings
`Please wait while transferring player two data to the other Game Boy
Advance` and `FATAL ERROR!` (`0x2A6E6C`–`0x2A6F50`), i.e. it is the
single-pak/multiboot client image for link play, not a second playable game.
No cheat data lives in that half; this report treats the main image at
`0x08000000`.

## 2. Executive summary

**The game contains a real, working in-game unlock system: 43 Activision
"patches" spread over 33 of the 56 included Atari 2600 games.** The prior
triage note ("no cheats, manual text false positives") was half right: the
manual scans at `0x5E0000+` do generate most keyword hits, but the actual
patch UI and patch tables live at `0x2A5C00`–`0x2A8200` and were missed.

Mechanism, in one paragraph: while an emulated 2600 game runs, the GBA shell
executes a **per-game monitor routine**. The monitor reads a 128-byte mirror
of the 2600's RAM at `0x030001F8`, computes that game's score/time/condition,
and compares it against constants in its own code. When the condition is
met, the monitor calls the current award callback (`0x03005860`, normally
`0x08009708`, thumb `0x08009709`) with `r0 = patch_index - 1`. The award
routine checks the persistent bitmap at `0x02029C44`; if the bit is clear it
draws `Congratulations! You have unlocked the <patch> patch!`, sets the bit,
and the bitmap is written to EEPROM. The per-game "earned" latch is a byte in
`0x02029944`.

There is **no password, no button code, no unlock-all code, and no debug
menu** that can unlock patches. The only bitmap setter used during play is
`0x08016864` (the load routine also restores the saved bytes); its only
caller is `0x0800984C` inside the award routine; the award routine is
reached only through the per-game monitor callback. A
hidden "4Kb EEPROM dump" screen exists at `0x0800A9F8` but is unreferenced
dead code, and 13 button-combination test runs (8 distinct combinations,
some repeated on both screens) at the bedroom and options screens had no
effect.

The Barnstorming/Flying Aces gate was proven exactly:
`0x080121B8` requires the 2600 time-valid byte `0x0300024B == 0` and the BCD
time at `0x0300022D..0x0300022F` to be `<= 3330`, `5100`, `5400` hundredths
for game variants 0/1/2 respectively. Boundary tests: `0:33.30` accepted
(congratulations + bit set), `0:33.31` and `0:34.00` rejected (no
congratulations, bitmap unchanged). The unlock was produced with a
**savestate-injected time** (clearly labelled; no normal playthrough was
completed) and survived a cold boot from EEPROM.

## 3. How to reproduce

### Emulator

```bash
Xvfb :122 -screen 0 1024x768x24 &
DISPLAY=:122 openbox &
cd "roms/Activision Anthology"
DISPLAY=:122 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 "Activision Anthology.gba" &
```

mGBA 0.10.5 (SDL). Default keymap used: A=`x`, B=`z`, L=`a`, R=`s`,
Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys 150–300 ms.

### Menu paths walked

* Splash → A → **cartridge rack** (`Select <game>`, L/R = Rotate rack).
* B → **bedroom**, five options reachable with Left/Right:
  `Select a game`, `View the credits`, `Start the game`, `View records`,
  `Change options`.
* **Select a game** → A → rack; A on a title → pre-play screen with
  `A Play game`, `B Back`, **Left = View manual**, **Right = View box**,
  `Select = Hide text`.
* In game: **Start = pause** (`B Return to game`, `L High score`,
  `Select Help`, `A Exit game`); exit asks `Exit Game — Are you sure?`.
* **View records** → game list with `Score` and `Patch` columns; A → per-game
  score screen with `View Patches`; the patch page shows either the coloured
  badge (unlocked) or `This patch has not been unlocked yet` (locked).
* **Change options**: Brightness, Game volume, SFX volume, Music volume,
  Music track, Erase all saved data (+ confirm dialog).
* **View the credits**: scrolling booklet.
* **View manual / View box**: scanned manual pages and cartridge label/box
  renderings (the source of the earlier keyword false positives).

Screenshots for each screen are in `screenshots/` next to this report
(01 title, 02 bedroom, 03 rack, 04 records, 05 locked patch, 06 options,
07 pre-play, 08 high-score requirements, 09–12 unlock/bound tests, 13 badge,
14 cold boot, 15 credits, 16 pause, 17 help, 18 exit confirm, 19 manual,
20 label/box).

### Savestate-injection recipe (analysis instrumentation only)

This is **not** the deliverable cheat; it is how the score gate was probed
without a skilled 33.3 s run. mGBA `.ssN` files are PNGs with a zlib `gbAs`
chunk. Decompressed state layout used here (mGBA 0.10.5):

```
state+0x19000 = IWRAM 0x03000000
state+0x21000 = EWRAM 0x02000000
```

1. Boot Barnstorming, press A (play), Select (Game Reset), A (Fire), let the
   timer run; save slot 2 (`Shift+F2`) → `Activision Anthology.ss2`.
2. Decompress the `gbAs` chunk, then patch these IWRAM bytes:
   * `0x0300022D` (state `0x1922D`) = minutes BCD (0x00)
   * `0x0300022E` (state `0x1922E`) = seconds BCD (0x33)
   * `0x0300022F` (state `0x1922F`) = hundredths BCD (0x30)
   * `0x0300024B` (state `0x1924B`) = `0x00` (time-valid/game-over latch)
3. Recompress the chunk and rebuild the PNG (chunk length + CRC-32).
4. Load the slot. On the next frame the monitor awards patch #1.

For rejection, use `0x33/0x31` (33.31 s) or `0x34/0x00` (34.00 s) instead;
the bitmap stays zero.

### Published material checked

* VGChartz GBA cheats page for this title: **"Total cheats available: 0"**.
* GameFAQs GBA cheats page: no GBA code list (site blocks automated fetch,
  search snippets show no codes).
* No published in-game code or unlock-all method was found for the GBA
  version. The documented mechanic (earn original Activision patches with
  high scores) is what the ROM implements.

## 4. Address map

File offset → ROM address is `+0x08000000`.

| ROM address | Size | Meaning |
|---|---:|---|
| `0x0800623C` | 0x8C0 | Game database, 56 × 40-byte records |
| `0x08006AFC` | 0x2C0 | Patch table, 44 × 16-byte records (index 0 = NONE) |
| `0x08006DBC` | 0x380 | Requirement-text pointer table, 56 × 4 pointers |
| `0x08009708` | — | Patch award/congrats routine (`r0 = patch_index-1`) |
| `0x080121B8` | — | Barnstorming monitor (Flying Aces, patch #1) |
| `0x08012344` | — | Beamrider monitor (patch #2) |
| `0x08016830` | — | `patch_is_unlocked(idx)`: bitmap test |
| `0x08016864` | — | `patch_set_unlocked(idx)`: bitmap set (only writer) |
| `0x08016C00` | — | EEPROM save (magic `ANT`, XOR checksum, 512 bytes) |
| `0x08016CBC` | — | EEPROM load |
| `0x0800CEA8` | — | Key poll: `KEYINPUT` (`0x04000130`) → `0x02000014` |
| `0x0800A9F8` | — | Unreferenced "4Kb EEPROM dump" viewer (dead code) |
| `0x082A5C04` | — | 56 game-name strings |
| `0x082A5C38`–`0x082A6334` | — | 43 patch names + requirement text lines |
| `0x082A7C90`–`0x082A81F0` | — | Patch/menu UI strings |

RAM:

| Address | Size | Meaning |
|---|---:|---|
| `0x030001F8` | 128 | Mirror of the emulated 2600's RAM (`$00`–`$7F`) |
| `0x03005860` | 4 | Current award callback pointer (thumb `0x08009709` in game) |
| `0x03005814` | 4 | Current input poll callback (`0x0800CEA9` in game) |
| `0x03005758` | 2 | In-game flag (=1 while a 2600 game runs) |
| `0x02029844` | 256 | 32 × {u32 best value, u32 extra} monitor records |
| `0x02029944` | 43 | Per-patch "earned" latch (monitor sets to 1) |
| `0x02029C44` | 8 | Persistent patch bitmap; bit *n* = patch table index *n* |
| `0x02029A54` | 496 | High-score/settings payload copied to EEPROM |
| `0x02029E54` | 512 | EEPROM staging buffer |

### Game DB record (`0x0800623C`, 40 bytes)

```
+0x00 u8  req_index (b0)     ; index into the requirement-text table
+0x01 u8  unknown            ; 0/1, not resolved
+0x02 u8  first_patch        ; 1-based patch table index (0 = no patch)
+0x03 u8  patch_count        ; 0..4
+0x04 ptr name string
+0x08 ptr label/cart art
+0x0C ptr box art
+0x10 ptr manual
+0x14 ptr screenshot
+0x18 ptr ...                ; two more art/text pointers
+0x1C ptr ...
+0x20 ptr manual/extra text
```

Patch table entry (`0x08006AFC`, 16 bytes):

```
+0x00 ptr name line 1
+0x04 ptr name line 2 (or empty string)
+0x08 ptr badge tile data 1
+0x0C ptr badge tile data 2
```

### EEPROM layout (4 Kbit, 512 bytes)

The game builds a 512-byte buffer at `0x02029E54`:

```
[0..2]   "ANT"
[3..5]   3 bytes from 0x0300579C
[6..7]   16-bit XOR checksum over [0..5] + the 504-byte payload
[8..15]  8-byte patch bitmap (copied from 0x02029C44)
[16..511] 496-byte payload from 0x02029A54
```

mGBA stores each 8-byte EEPROM block byte-reversed in the `.sav`. Therefore
bitmap byte 0 (patch indices 0–7) appears at **`.sav` offset `0x0F`**.
Observed: before unlock `.sav[0x0F] = 0x00`; after unlocking patch #1
`.sav[0x0F] = 0x02` and the checksum byte changed; a cold boot reloaded it.

## 5. Algorithm

### Award path (game-independent)

```c
// r0 = patch_index - 1 (0..42)
void award(uint8_t a) {
    uint8_t idx = (a + 1) & 0xFF;
    if (patch_is_unlocked(idx)) return;   // 0x08016830
    draw_congrats(idx);                   // strings at 0x082A7C90/CA4/CC0
    patch_set_unlocked(idx);              // 0x08016864: bit (idx&7) of byte
                                          //  0x02029C44[(idx>>3)]
    // waits for B (0x04000130 mask 0x02), then saves
}

bool patch_is_unlocked(uint8_t idx) {
    if (idx == 0) return true;            // patch 0 is "NONE"
    return 0x02029C44[idx >> 3] & (1 << (idx & 7));
}
```

The callback pointer is installed when a game is launched:
`0x080003B8` stores `r2` at `0x03005860`; for the gameplay screen
`r2 = 0x08009709`. A gameplay state dump confirms
`[0x03005860] = 0x08009709` and `[0x03005814] = 0x0800CEA9`.

The call is made through the `bx r1` trampoline at `0x081112CC`, from each
per-game monitor. Example (Beamrider, `0x08012344`):

```
score  = bcd(ram[0x09]) + 100*bcd(ram[0x0A]) + 10000*bcd(ram[0x0B])
sector = bcd(ram[0x00])
if (earned[1] == 0 && score > 39999 && sector > 13) {
    earned[1] = 1;
    award(1);                 // patch #2
}
```

### Barnstorming / Flying Aces (`0x080121B8`, patch #1)

```c
ram = 0x030001F8;
if (bcd(ram[0x53]) != 0) return;       // time-valid/game-over latch must be 0
                                       // (code tests low + 10*high == 0)
time = bcd(ram[0x35]) * 6000           // minutes  (1 min = 6000 hundredths)
     + bcd(ram[0x36]) * 100            // seconds
     + bcd(ram[0x37]);                 // hundredths
variant = bcd(ram[0x00]) & 3;          // Game 1..4
best[variant] = max(best[variant], time);   // 0x02029844 + variant*8
if (earned[0]) return;
switch (variant) {
  case 0: if (time <= 3330) goto award; break;   // 33.30 s
  case 1: if (time <= 5100) goto award; break;   // 51.00 s
  case 2: if (time <= 5400) goto award; break;   // 54.00 s
  default: return;                                // Game 4: no patch
}
award:
  earned[0] = 1;
  award(0);                            // patch #1
```

The constants are literal-pool values at `0x080122B4` (`0x0D02` = 3330),
`0x080122B8` (`0x13EC` = 5100), `0x080122BC` (`0x1518` = 5400). The BCD
decoder uses `low_nibble + 10*high_nibble`.

### Score gating in general

Every one of the 43 patches has a monitor in the shell code that reads
`0x030001F8` and one or more constants. The monitor sets its byte in
`0x02029944` and calls `award(k)` where `k = patch_index - 1`. There is no
generic "threshold table": thresholds are immediate constants in each
per-game monitor (matching the human-readable lines in the requirement
table). This is why the patch system leaves no numeric threshold table next
to the text.

## 6. Tables

### Game-record → patch mapping

The requirement table is indexed by record byte `+0x00` (b0), not by menu
order; this is why a naive index by menu position misaligns several games.
Barnstorming b0=0, Beamrider b0=2, Chopper Command b0=6, Crackpots b0=9,
Decathlon b0=10, Dolphin b0=11, Dragster b0=12, Enduro b0=13, Freeway b0=15,
Frostbite b0=16, Grand Prix b0=17, H.E.R.O. b0=18, Ice Hockey b0=20, etc.

### Reward flag / award argument

```
patch_index p (1..43)  <->  earned latch 0x02029944[p-1]
                       <->  bitmap bit p of 0x02029C44
                       <->  award() argument r0 = p-1
```

Bit 0 of the bitmap is unused/reserved (`patch_is_unlocked(0)` returns true).
Bits 44–63 of the 8-byte bitmap are unused.

### All 43 patches

| # | Patch name | Game | Requirement (ROM text) |
|---|---|---|---|
| 1 | Flying Aces | Barnstorming | Game 1: 33.3 s or less; Game 2: 51.0 s; Game 3: 54.0 s |
| 2 | Beamrider | Beamrider | 40,000 points at sector 14 |
| 3 | Chopper Commandos | Chopper Command | 10,000 points |
| 4 | Crackpots | Crackpots | 75,000 points |
| 5–7 | Bronze / Silver / Gold Medal | Decathlon | 8,600 / 9,000 / 10,000 points |
| 8–9 | Friends of Dolphins / Secret Society of Dolphins | Dolphin | 80,000 / 300,000 points |
| 10 | World Class Dragster Club | Dragster | 6.0 seconds or less |
| 11 | Roadbusters | Enduro | Survive 5 days or more |
| 12 | Save the Chicken Foundation | Freeway | Game 3 or 7: 20 points |
| 13 | Frostbite Bailey's Arctic Architects | Frostbite | 40,000 points |
| 14 | Grand Prix Driving Team | Grand Prix | Game 1 0:35; Game 2 1:00; Game 3 1:30; Game 4 2:30 |
| 15 | Order of the H.E.R.O. | H.E.R.O. | 75,000 points |
| 16 | Activision All-Star Hockey Team | Ice Hockey | Game 1: beat the computer |
| 17 | The Bucket Brigade | Kaboom! | 3,000 points |
| 18 | Billy Club | Keystone Kapers | 35,000 points |
| 19–20 | Commander – Federation of Laser Blasters / One Million | Laser Blast | 100,000 / 1,000,000 points |
| 21 | Megamaniacs | Megamania | 45,000 points |
| 22 | Oinkers | Oink! | 25,000 points |
| 23 | Explorers' Club | Pitfall! | 20,000 points |
| 24 | Cliff Hangers | Pitfall II | 99,000 points |
| 25 | The No Plaque Pack | Plaque Attack | 35,000 points |
| 26 | Short-Order Squad | Pressure Cooker | 45,000 points |
| 27 | Super Sleuth | Private Eye | Solve case 3 |
| 28 | River Raiders | River Raid | 15,000 points |
| 29–31 | Medal of Merit / Cross of Excellence / Star of Honor | Robot Tank | 48 / 60 / 72 tanks |
| 32 | Sub Club | Seaquest | 50,000 points |
| 33 | Official Member – Ski Team | Skiing | Game 3: 28.2 s or less |
| 34 | Sky Stars | Sky Jinks | Game 1: 37.0 s or less, no missed pylons |
| 35–36 | Space Shuttle Pilot / Commander | Space Shuttle | 5 docks + 4,500 fuel / 6 docks + 7,500 fuel |
| 37 | Spider Fighters | Spider Fighter | 40,000 points |
| 38 | Trail Drive | Stampede | 3,000 points |
| 39–42 | Order of the Supreme Starmaster / Leader / Wing Commander / Starmaster | Starmaster | 3,800 / 5,700 / 7,600 / 9,000 points |
| 43 | Tennis | Tennis | Beat the computer |

Games with **no patch** (23): Baseball, Bloody Human Freeway, Boxing, Bridge,
Checkers, Climber 5, Cosmic Commuter, Fishing Derby, Kabobber, Okie,
Oystron, River Raid 2, Skateboardin', Skeleton+, Space Treat Deluxe,
Thwocker, Titlematch, Tomcat, Vault Assault, Venetian Blinds, Video Euchre,
Unknown Prototype #1, Unknown Prototype #2. For these the result screen
prints `There is no patch available for this game`.

## 6b. Enumeration

### Space definition

* The patch system is **not a code space**. There is no alphabet, length,
  checksum or serial. It is 43 independent boolean flags plus per-game
  numeric conditions.
* Representable flags: 8-byte bitmap = 64 bits; bit 0 reserved (NONE),
  bits 1–43 are the 43 patches, bits 44–63 unused. The space is therefore
  **2^43 flag combinations**, with 43 single-patch transitions; one flag byte
  per patch in `0x02029944` (43 bytes used).
* Each flag is monotonic (set once, never cleared except by erasing saves).
* Thresholds are continuous/score-based, not enumerable tokens. The complete
  threshold list is the requirement table above; two monitors were read at
  instruction level and match it:
  * Barnstorming: `<=3330 / <=5100 / <=5400` hundredths (`0x080122B4/8/BC`).
  * Beamrider: `>39999` and `sector>13` (`0x080123BA`, literal `0x9C3F`).

### Unlock performed (labelled savestate-advanced)

No skilled 33.3 s run was completed; the time value was injected into a
savestate as described in §3. This is instrumentation, not a RAM cheat
deliverable.

| Test | Injected 2600 state | Result |
|---|---|---|
| Accept | `time=0:20.00`, latch `0x0300024B=0` | `Congratulations! You have unlocked the Flying Aces patch!` (`screenshots/09_unlock_20s.png`); bitmap `0x02029C44` byte0 = `0x02` |
| Boundary accept | `time=0:33.30` | Same congratulations (`screenshots/10_accept_3330.png`) |
| Boundary reject | `time=0:33.31` | No congratulations, game continues, bitmap stays `0x00` (`screenshots/11_reject_3331.png`) |
| Reject | `time=0:34.00` | No congratulations, bitmap `0x00` (`screenshots/12_reject_3400.png`) |

After the accept, the badge page shows the full-colour Flying Aces patch
(`screenshots/13_patch_unlocked_badge.png`), the Records list shows filled
score and patch boxes, and a cold boot from the EEPROM `.sav` still shows the
patch unlocked (`screenshots/14_coldboot_persisted.png`). The `.sav`
changed at offset `0x0F` from `0x00` to `0x02`.

### Codes

**No codes exist.** Bounded evidence:

1. The only in-play setter of the patch bitmap is `0x08016864` (load also
   restores bytes from EEPROM). It has exactly one caller, `0x0800984C`,
   inside `0x08009708`.
2. `0x08009708` is installed as the gameplay award callback at
   `0x03005860` by `0x080003B8` when a game is launched; a gameplay state
   dump confirms `[0x03005860] = 0x08009709`.
3. `0x08009708` is reached only through the `bx r1` trampoline
   (`0x081112CC`) from the 43 per-game monitor routines, each of which is
   inside the emulator's frame loop and only fires on its in-game condition.
4. No menu code writes `0x02029C44`; the only other references are the
   save/load routines (`0x08016BF4`, `0x08016CA4`, `0x08016D70`,
   `0x08016E2C`).
5. Button-combination probes at the bedroom and options screens produced no
   screen change and no bitmap write: `L+R+Select`, `L+R+Start`,
   `Select+Start`, `L+R+Select+Start`, `L+R+Up+A`, `L+R+Down+B`, `L+R`,
   plus single Select. (The bedroom and options screens were used because
   those are where a hidden menu would live.)
6. A scan of 2-byte-aligned runs of key-mask values
   (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,
   L=0x200`) produced only graphics/data runs; none is referenced from the
   patch path (the only in-play bitmap setter remains `0x08016864`). Menu
   input is fed by the generic per-frame poll at `0x0800CEA8`
   (`KEYINPUT` → `0x02000014`); the other direct `KEYINPUT` reads only wait
   for a specific button on fixed screens.
7. The only "debug" surface found, the `4Kb EEPROM dump` viewer at
   `0x0800A9F8`, has no BL caller, no 32-bit pointer and no pointer-table
   entry anywhere in the ROM; it is unreachable dead code.

Consequently an unpublished *selection* here means an unpublished patch
state, not a novel code string. The novel state demonstrated is patch #1
unlocked through the exact score gate, with the boundary proven by rejection.

## 7. Validation evidence

**Observed**

* mGBA screens throughout §3; all 14 images in `screenshots/`.
* `0:20.00` and `0:33.30` produced the congratulations overlay and set
  `0x02029C44[0] = 0x02`; `0:33.31` and `0:34.00` did not.
* `0x02029944[0]` changed `0x00 → 0x01` on the award.
* EEPROM `.sav[0x0F]` changed `0x00 → 0x02`; cold boot still showed the
  patch box filled and the coloured badge.
* Gameplay state dump: `[0x03005860] = 0x08009709`,
  `[0x03005814] = 0x0800CEA9`, `[0x03005758] = 1`.

**Derived**

* Patch award path and helper semantics from disassembly of
  `0x08009708`, `0x08016830`, `0x08016864`, `0x08016C00/BC`.
* Barnstorming gate and constants from `0x080121B8` (literal pool
  `0x080122B4/8/BC`).
* Beamrider gate from `0x08012344` (`cmp r4,#13`, literal `0x9C3F`).
* No in-play bitmap setter other than the award routine; the only other
  accesses are the EEPROM save/load copies (full literal/call/pointer scan).
* EEPROM block/bitmap layout from the save routine and the `.sav` diff.

**Inferred**

* The byte at 2600 RAM `+0x53` is a "time valid / game over" latch; its
  exact game meaning was not traced inside the 2600 ROM.
* EEPROM bitmap byte order was confirmed for byte 0 only; the remaining
  bytes are inferred to follow the same block.
* The 43 monitor constants were taken from the displayed requirement table
  for the 41 patches not disassembled; all sampled monitors agree.

## 8. Unknowns

* The exact condition code of all 43 monitors was not transcribed line by
  line. Thresholds for 41 patches rest on the in-ROM requirement text and
  the award-index mapping; only Barnstorming and Beamrider were verified
  instruction-by-instruction.
* The `+0x53` latch semantics and the `+0x01` game-record byte remain
  unnamed.
* EEPROM bitmap bytes 1–7 (patches 8–43) were not individually observed in
  the `.sav`; only patch #1 was.
* The embedded multiboot/`ANTH` image was identified but not reversed.
* No legitimate 33.3 s playthrough was completed; the accept test is
  savestate-advanced and labelled as such.

## 9. Tooling

* mGBA 0.10.5 (SDL), Xvfb :122, openbox, xdotool, scrot.
* `arm-none-eabi-objdump` 2.x with `-M force-thumb` for all disassembly.
* Python 3 + `capstone` 5.0.7 for scans; `zlib` + PNG chunk/CRC code for
  savestate inspection and injection.
* Hash/header/table scripts are inline in this report; savestate layout:
  `IWRAM base 0x19000`, `EWRAM base 0x21000`, `gbAs` chunk = zlib.
* Screenshots: `screenshots/01_title.png` … `screenshots/20_label_box_viewer.png`
  (title, bedroom, rack, records, locked/unlocked patch, options, pre-play,
  high-score requirements, unlock/boundary/rejection, cold boot, credits,
  pause, help, exit confirm, manual and label/box viewers).
* The `.sav` and `.ssN` files are emulator artifacts and are git-ignored.

## Legal note

No ROM, extracted graphics, music or scanned manual content is redistributed
here. Only addresses, algorithms, hashes and UI screenshots needed as
evidence are included.
