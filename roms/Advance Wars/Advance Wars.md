# Advance Wars (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Advance Wars/Advance Wars.gba` |
| Size | 4,194,304 bytes (`0x400000`, 4 MiB) |
| Header title (`0xA0`) | `ADVANCEWARS` (NUL padded) |
| Game code (`0xAC`) | `AWRE` (USA) |
| Maker (`0xB0`) | `01` |
| Version (`0xBC`) | `0x01` (Rev.01; `file` reports “Rev.01”) |
| Fixed `0x96` (`0xB2`) | `0x96` |
| Complement check (`0xBD`) | `0x91` |
| Header checksum (`0xBE`) | `0x0000` |
| Entry branch (`0x00`) | `0xEA00002E` → `0x080000C0` (ARM) |
| MD5 | `04775a93461d24cf1a7e3346d244e516` |
| SHA-1 | `15053499d5b3f49128a941d7f2d84876f5424d0c` |
| SHA-256 | `4dd4bd22441f29b22ca5af554f30bf0eb7d2b1a5daff0e2cd071a43e11383305` |

**Embedded GBA-header scan.** The 156-byte Nintendo logo occurs **three** times:
one real header at file offset `0x000000`, plus two header-shaped records at
`0x3BADC8` (zeroed title/game code) and `0x3BD0E0` (title `GAMEBOYWARS`, game
code `AWRJ`). Both carry the same entry word `0xEA00002E`, a valid logo, a valid
complement (`0xF0` and `0x7B`), and ARM code at their entry points
(`0x083BAE88` polls the link port at `0x04000120`; `0x083BD1A0` sets
CPSR/stack and jumps to `0x0201993D`). The two records and their payload occupy
the last 283,192 bytes (`0x3BADC8–0x400000`); the AWRJ image alone is 274,208
bytes. They contain no password/cheat/debug ASCII. They are
**link/multiboot slave images**, not a second playable game; the `AWRJ` code is
consistent with TCRF’s note that the Japanese release was the *Game Boy Wars
Advance 1+2* combination cartridge. All analysis below refers to the main image
based at `0x08000000` (`rom_address = 0x08000000 + file_offset`).

## 2. Executive summary

The prior triage note “No in-game cheats” is **false**. This ROM contains four
developer-intended, in-game codes, all confirmed in mGBA:

1. **Hold `L + Right + Select` at power-on → “Delete all saved data.OK? Yes / No”.**
   Validator at `0x08038798`: an explicit `(held & 0x00F) == 0x00F` guard,
   then **exact equality** with `0x214`. Handler `0x08038848`; the message text
   is at `0x082EA11A`. Confirmed on both an empty (never-used) save and an
   unlocked save; choosing Yes runs “Now deleting data. Do not turn OFF.” and
   then “Data has been deleted!”. This is the same engine family as AW2
   (`0x214`, guard `0xF`).
2. **Hold `A + B + Select + Start` anywhere → soft reset.** The global main loop
   (`0x08038800`) calls `0x08038824` every iteration; that function reads
   `KEYINPUT` directly and tests `(held & 0x00F) == 0x00F`. On true it calls
   `0x080386D8` → `0x080796F0` (`IME=0`, `SP=0x03007F00`, `SWI 1`, `SWI 0`).
   Any extra buttons are tolerated. Confirmed at the delete prompt and in a
   battle. An unpublished six-button variant `A+B+Select+Start+L+R` (`0x30F`)
   also resets.
3. **Hold `L + R` while the Design Map editor initialises → the fixed “Nintendo”
   map.** The map loader at `0x08003938` tests `(held & 0x300) == 0x300`; on
   true it calls `0x0800449C`, which fills a 30×20 map from a fixed 600-byte
   layout table at `0x0827EDFC` using four terrain codes at `0x0807CFCC`.
   Rendering the table shows the three kanji **任 天 堂** (Nintendo) across the
   map (`Advance Wars - hidden map Nintendo layout.png`).
   `L`-only, `R`-only and no-key entries take the procedural generators
   (`0x08003E58` / `0x0800421C`) instead. Confirmed with screenshots and a RAM
   dump; `L+R+A+B` still produces the fixed map (mask test, not equality).
4. **Campaign → New with `Select` held → “ADVANCE CAMPAIGN”.** Without Select the
   same action shows the normal `CAMPAIGN MAP`. The alternate action is selected
   by a per-menu-entry key mask: `0x08017E54` ANDs the entry mask with the
   press/edge key state at `key+12` and calls `0x080172E4`, which sets the
   Advance flag at `0x03000DA4`. Confirmed with an unlocked save (banner and RAM
   flag).

There is **no password system, no sound test / Sound Room, and no reachable
debug menu**. A complete developer debug lexicon survives at
`0x082110–0x082240` (`FLAGALL`, `FLASHCLEAR (L.R.SELECT)`, `FLASH << DUMMY
(L.R.SELECT)`, `BACKUP UTL`, …), with its widget table at `0x082E72C8` and code
at `0x0803CC90–0x0803D5xx`, but the table root has no reference outside that
cluster, and none of the key-mask comparisons in the image routes to it;
`L+R+Select` at the main menu and in the editor does not open it. It is dead
code from a development build, as in AW2. TCRF (archived) documents the same
L+R “Nintendo” map and lists no debug menu for this game.

The button-code space is fully enumerated in §6b: the boot delete validator is
one point in 1024 states; the global reset is 64 states (low nibble `0xF`); the
design-map selector is 4 L/R states, exactly one of which is the fixed map.

## 3. How to reproduce

**Emulator.** mGBA 0.10.5 (Debian `mgba-sdl`) on Xvfb `:125`, 3× scale,
`SDL_AUDIODRIVER=dummy`. Screenshots were taken from the mGBA window
(`import -window root` + crop to the 720×480 content area).

**Keymap used (mGBA SDL default):**

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Hold keys 150–400 ms; mGBA polls once per frame. For a boot code, hold the keys
through a `Ctrl+R` reset and for another ~0.3 s.

**Delete-save code.**

1. Start mGBA with the ROM.
2. Hold `a` (L), `Right`, `BackSpace` (Select).
3. Reset (`Ctrl+R`) while holding; keep holding ~0.3 s.
4. Release. Within ~2 s the black screen shows
   `Delete all saved data.OK?  Yes  No` (No preselected).
5. `A` on No returns to boot; `Left` + `A` on Yes runs the delete sequence.
   Evidence: `Advance Wars - boot delete prompt.png`,
   `Advance Wars - data deleted.png`.

**Rejections tested the same way** (all produced the normal intro/title, no
prompt, observed ≥5 s):

| Held | Value | Result |
|---|---:|---|
| `L + Right + Select` | `0x214` | **prompt shown** |
| `L + Right + Select + A` | `0x215` | rejected (`Advance Wars - delete rejected 215.png`) |
| `L + Right` | `0x210` | rejected |

The offline model in `bootcheck.py` rejects the other 1022 states; `0x204`
(`Select + L`, missing Right) is one of them.

**Global reset.**

1. Reach any screen (title, delete prompt, battle).
2. Hold `A+B+Select+Start`; at the delete prompt the text disappears and the
   attract screen returns within ~0.4 s. Evidence:
   `Advance Wars - reset four button.png` (and the earlier in-battle reset).
3. Unpublished variant: hold `A+B+Select+Start+L+R`; same reset
   (`Advance Wars - reset accepted 30F.png`).
4. Rejection: `B+Select+Start` (`0x00E`) leaves the delete prompt untouched
   (`Advance Wars - reset rejected 00E.png`).

**Design Maps.**

A save with Design Maps unlocked is required. The test harness was the
published GameFAQs save #2112 (“Version 1.1, All CO’s, all maps, Advance
Campaign unlocked”, Europe), downloaded from Zophar’s Domain and loaded into
this USA Rev.01 image; the save format is compatible. It was used only to reach
the screen and is not redistributed.

1. Main menu → `Design Maps` → `A`.
2. Hold `L+R` through the `A` press and until the editor appears.
3. Dismiss the “Welcome to Design Maps mode!” text with `A`; the map shown is
   the fixed layout.
4. Repeat with no keys, `L` only, and `R` only for the other branches.
5. Evidence: `Advance Wars - design map L+R.png`,
   `- design map L+R+A+B.png`, `- design map no keys.png`,
   `- design map L only.png`, `- design map R only.png`.

**Advance Campaign.**

1. Main menu → `Campaign` → `A` → `Up` to `New`.
2. Hold `Select`; press `A`; keep Select held until the map screen appears.
3. Banner changes from `CAMPAIGN MAP` to `ADVANCE CAMPAIGN`.
4. Evidence: `Advance Wars - advance campaign.png`,
   `- campaign map normal.png`.

**Menu walk.** Title → intro/name → initial `Vs. Mode / Link Mode / Field
Training` menu; after a completed save the full `SELECT MODE` menu is `Stats`,
`War Room`, `Campaign`, `Field Training`, `Vs. Mode`, `Link Mode`,
`Design Maps`, `Battle Maps` (circular). Submenus walked: Campaign
New/Continue; Design Maps editor (`SELECT` menu: File / Help / Intel / Fill /
End); Battle Maps shop; Vs. Mode (`SELECT MAP` → `TEAMS` → `RULES` → battle);
Link Mode (`Single-Pak` / `Trade Maps` / `Multi-Pak`); Stats (`Rank` /
`Records`); War Room map list; in-battle `SELECT` menu (`Unit` / `Intel` /
`Save` / `Options` / `End`) and `Options` (`Music On/Off`, `No Visual`,
`Delete`, `Yield`, `Exit Map`). No Sound Room, sound test, jukebox, or password
entry exists anywhere in that walk.

## 4. Address map

| ROM address | File offset | Role |
|---|---:|---|
| `0x08000000` | `0x0` | GBA header |
| `0x08038718–0x08038724` | `0x38718` | read `KEYINPUT`, compute `held = 0x3FF & ~KEYINPUT`, store at `sp+4` |
| `0x08038798–0x080387B6` | `0x38798` | **boot delete validator**: guard `0xF`, exact compare `0x214` |
| `0x08038848` | `0x38848` | delete-save handler: message box `0x082E2218`, text `0x082EA11A` |
| `0x08038800` | `0x38800` | global main loop |
| `0x08038814` | `0x38814` | call to reset check, every main-loop iteration |
| `0x08038824–0x0803883E` | `0x38824` | **global reset check**: `(held & 0x00F) == 0x00F` |
| `0x080386D8` | `0x386D8` | `movs r0,#0xFE; bl 0x080796F0` |
| `0x080796F0` | `0x796F0` | `IME=0` (`0x04000208`), `SP=0x03007F00`, `SWI 1`, `SWI 0` |
| `0x08003938–0x080039DA` | `0x3938` | **design-map init / generator dispatch** |
| `0x08003972–0x08003982` | `0x3972` | L/R mask test, `(held & 0x300) == 0x300` |
| `0x0800449C` | `0x449C` | fixed hidden-map builder |
| `0x0827EDFC` | `0x27EDFC` | 600-byte hidden-map layout table (values 0–3) |
| `0x0807CFCC` | `0x7CFCC` | four terrain codes `0x002A, 0x0001, 0x0087, 0x0020` |
| `0x08003E58` | `0x3E58` | procedural generator A (random) |
| `0x0800421C` | `0x421C` | procedural generator B (random) |
| `0x020157F8` | RAM | design-map struct (width `0x1E`, height `0x14` at +0/+2) |
| `0x0201621A` | RAM (`+0xA22`) | design-map tile layer, 600 × `u16` |
| `0x080103C0` | `0x103C0` | key poll: `held`, pressed, repeat, mirrors |
| `0x030031B4` | RAM | key struct: `+0` held, `+2` pressed, `+4` pressed copy, `+8` raw held, `+12` pressed copy used by the alternate-action check, `+14` previous raw |
| `0x030031D8` | RAM | direct held copy written by the key poll |
| `0x04000130` | I/O | `KEYINPUT` (active-low) |
| `0x08017E54–0x08017E86` | `0x17E54` | menu alternate-action check: entry mask & key press/edge state |
| `0x080172E4` | `0x172E4` | **set Advance Campaign flag** (`strh 1` at `0x03000DA4`) |
| `0x080172F0` | `0x172F0` | clear Advance Campaign flag |
| `0x03000DA4` | RAM | Advance Campaign flag (`u16`: 1 = Advance, 0 = normal) |
| `0x082110–0x082240` | `0x82110` | unreachable debug lexicon |
| `0x08212C` | `0x8212C` | debug menu list of 8 string pointers |
| `0x082E72C8` | `0x2E72C8` | debug widget descriptor table (root) |
| `0x0803CC90–0x0803D5xx` | `0x3CC90` | debug-menu code cluster |
| `0x082EA11A` | `0x2EA11A` | `Delete all saved data..OK?` (control bytes `0x0E 0x0E`) |
| `0x082296` | `0x82296` | `Advance Campaign` text record (`09 83` prefix) |
| `0x08080DB4` / `0x08080DC0` / `0x08080DF8` | `0x80DB4` | main-menu ASCII labels: `Design Maps`, `War Room`, `Campaign` |

## 5. Algorithm

### 5.1 Key masks

GBA `KEYINPUT` is active-low; all values here are active-high “held” masks:

| Button | A | B | Select | Start | Right | Left | Up | Down | R | L |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Mask | `0x001` | `0x002` | `0x004` | `0x008` | `0x010` | `0x020` | `0x040` | `0x080` | `0x100` | `0x200` |

### 5.2 Boot delete-save validator (`0x08038798`)

```python
def boot_delete(held):            # held = (~KEYINPUT) & 0x3FF
    if (held & 0x00F) == 0x00F:   # explicit guard; 0x00F is the reset combo
        return False
    return held == 0x214          # exact equality, not a mask test
```

`0x214` = `L | Right | Select`. Any extra button (`A`, `B`, `Start`, `Left`,
`Up`, `Down`, `R`) makes the compare fail. The guard is redundant for
`0x214` (its low nibble is `4`), but it documents that the four face buttons
are reserved for the reset path.

Handler `0x08038848` builds a two-choice message box and returns to the boot
loop. The prompt text is at `0x082EA11A`; Yes runs the save manager’s delete
path and prints “Now deleting data. Do not turn OFF.” then “Data has been
deleted!”.

### 5.3 Global reset (`0x08038824`, called from `0x08038800`)

```python
def global_reset(held):
    return (held & 0x00F) == 0x00F
```

It reads `KEYINPUT` directly, not the key struct, so it runs in every mode
including battles and the delete prompt. On true: `0x080386D8` →
`0x080796F0`:

```
0x04000208 = 0          ; IME off
SP = 0x03007F00
SWI 1
SWI 0                   ; BIOS SoftReset
```

Because the main loop calls this every iteration, holding the four face
buttons produces a reset loop until released.

### 5.4 Design-map dispatch (`0x08003938`)

The map struct is `[0x08282CB4]` (observed `0x020157F8`); its width/height are
set to 30 × 20 at `+0/+2`, then the map is initialised. (`[0x020100B0]` is a
separate editor work pointer used for the byte at `+19`.) The dispatch is:

```python
r = held & 0x300
if r == 0x300:      hidden_map()          # 0x0800449C, fixed 600-byte layout
elif r == 0x200:    generator_A()         # 0x08003E58, procedural
elif r == 0x100:    generator_B()         # 0x0800421C, procedural
else:                                     # neither L nor R
    if rand_quotient() <= 29: generator_B()
    else:                     generator_A()
```

The L+R branch is a **mask** test, so `L+R+A+B` and any other extra buttons
still select the fixed map. The fixed builder:

1. `memcpy(8 bytes from 0x0807CFCC)` into a stack buffer: four `u16` terrain
   codes `0x002A, 0x0001, 0x0087, 0x0020`.
2. Initialise all 30×20 tiles to `0x2A` (terrain layer at `map+0x0A22`) and
   `7` (secondary byte layer at `map+0x1432`).
3. For each of the 600 tiles, read the next byte from `0x0827EDFC` (values
   0–3), select the corresponding `u16` from the four codes, and write it with
   helper `0x08003CD4`.

The 600-byte table is therefore the complete map layout; §6.4 shows it.

### 5.5 Advance Campaign alternate action (`0x08017E54`)

The menu table at `0x03001D50` uses 24-byte slots; each slot points to a
descriptor whose `+12` field is a key mask. The handler is:

```python
entry = current_menu_entry
if (key_state.pressed & entry.key_mask) != 0:         # 0x08017E6E, key+12
    set_advance_flag(1)                              # 0x080172E4
else:
    clear_advance_flag()                             # 0x080172F0
```

The observed key is `Select` (`0x004`); the published instruction is “hold
Select before entering Campaign Mode”. `0x03000DA4` is `1` on the Advance
campaign map and `0` on the normal campaign map (IWRAM dumps of the two
savestates). The entry’s save-side unlock (Advance Campaign purchased) was
present in the test save; the key-side gate is proven.

## 6. Tables

### 6.1 Confirmed button actions

| Screen | Input | Value | Effect | Evidence | Status |
|---|---|---:|---|---|---|
| Power-on / boot | `L+Right+Select` | `0x214` | delete-save prompt | observed + derived | **works**, published |
| Power-on / boot | `L+Right+Select+A` | `0x215` | nothing | observed | rejected |
| Any mode | `A+B+Select+Start` | low nibble `0xF` | soft reset | observed + derived | **works**, published |
| Any mode | `A+B+Select+Start+L+R` | `0x30F` | soft reset | observed | **works**, unpublished variant |
| Any mode | `B+Select+Start` | `0x00E` | nothing | observed | rejected |
| Design Maps init | `L+R` | `held&0x300==0x300` | fixed hidden map | observed + derived | **works**, published |
| Design Maps init | `L+R+A+B` | same mask | fixed hidden map | observed | **works**, unpublished variant |
| Design Maps init | no keys / `L` / `R` | mask 0/0x200/0x100 | procedural maps | observed + derived | not the fixed map |
| Campaign → New | `Select` held | entry mask | `ADVANCE CAMPAIGN` banner, flag `0x03000DA4=1` | observed + derived | **works**, published |
| Campaign → New | no Select | — | normal `CAMPAIGN MAP`, flag `0` | observed + derived | — |
| Main menu / editor | `L+R+Select` | `0x304` | no debug menu | observed | no entry |
| Password screen | — | — | does not exist | strings + menu walk | absent |
| Sound Room / sound test | — | — | does not exist | strings + menu walk | absent |

### 6.2 Boot delete accepted set

Space: 10 key bits = `2^10 = 1024` states. Accepted delete state: exactly one.

| Value | Combo | Delete? |
|---|---|---:|
| `0x214` | `L+Right+Select` | **yes** |
| any `(held & 0x00F) == 0x00F` (64 states) | `A+B+Select+Start` + extras | no (reset path) |
| all other 959 states | — | no |

### 6.3 Design-map selector

| `held & 0x300` | Buttons | Branch | Result |
|---:|---|---|---|
| `0x300` | L+R | `0x0800449C` | fixed 600-byte hidden map |
| `0x200` | L | `0x08003E58` | procedural map A |
| `0x100` | R | `0x0800421C` | procedural map B |
| `0x000` | none | random | A or B (quotient ≤ 29 → B) |

### 6.4 Hidden-map layout (600 bytes at `0x0827EDFC`)

Symbols: `0` = `.`, `1` = space, `2` = `#`, `3` = `@`; row-major 30 × 20.
Terrain codes at `0x0807CFCC`: index 0 `0x002A`, 1 `0x0001`, 2 `0x0087`,
3 `0x0020`.

```
..###..###...
..#@####@#........
.##@#@@@@#.............
##@###@###................
#@@###@#############.........
@#@#@@@@@#@@@@@@@@@#..........
##@###@#######@#####..........
##@#.#@#..####@####.#########.
.#@###@####@@@@@@@#.#@##@##@#.
.#@#@@@@@@####@####.##@#@#@###
.############@#@##.##@@@@@@@@#
.........###@###@###@#######@#
.........#@@##.##@@###@@@@@###
.........####...######@###@#..
.....................#@@@@@#..
 ...................####@####.
    ................#@@@@@@@#.
        ...........#####@#####
            .......#@@@@@@@@@#
                 ..###########
```

The same 600 tiles were read back from EWRAM at `0x0201621A` after the L+R
entry; the tile values fell into four disjoint groups keyed by the layout
index, around the four base codes (with edge/adjacency variants), and the map
was pixel-identical across two separate L+R entries (only the top-right HUD
differed by 441 pixels).

Rendering the table with one colour per value makes the layout explicit: the
cells at value 3 form the three kanji **任 天 堂** (Nintendo) over the water /
land background. The render is included as
`Advance Wars - hidden map Nintendo layout.png`.

### 6.5 Unreachable debug lexicon (`0x082110–0x082240`)

```
OFF / ON                 FLAG CONTROL / FLAG
  FLASH                  SAVEDATA
  FLAGALL                COINS / COIN
  MISSION                TUTORIAL / HISTORY
EDIT
  FLASHCLEAR     (L.R.SELECT)
  FLASH << DUMMY (L.R.SELECT)
  FLASH >> DUMMY (A BUTTON)
BACKUP UTL
 8/27 11:50
```

Pointer list at `0x08212C`; sub-list at `0x0821C8`; widget descriptors at
`0x082E72C8`; handlers `0x0803CF20`, `0x0803D038`, `0x0803D098`, `0x0803D248`,
`0x0803D2C4`, `0x0803D2F4`; L+R branch tests inside the menu at
`0x0803D39C`/`0x0803D3C4`. The only reference to the table root is the literal
at `0x0803CF8C` inside the same cluster; there is no `BL`, function pointer, or
screen-state entry from a reachable menu. `L+R+Select` at the main menu and in
the editor produced no debug screen.

## 6b. Enumeration

**Space definitions.**

| System | Space | Accepted | Model |
|---|---|---:|---|
| Boot delete-save | 10 key bits = **1024** | **1** (`0x214`) | `(held&0xF)!=0xF and held==0x214` |
| Global reset | 1024 | **64** (all low-nibble `0xF`) | `(held&0xF)==0xF` |
| Design-map selector | 4 (L,R) | **1** fixed map (`0x300`) | `(held&0x300)==0x300` |
| Advance Campaign | 2 (Select / not) | 1 alternate action | per-entry key mask + save unlock |

**Novel inputs absent from published lists, confirmed in mGBA.**

* **`0x30F` = `A+B+Select+Start+L+R`** — resets. Published lists give only
  `Start+Select+B+A`; the six-button form exercises the mask test. At the delete
  prompt it removed the prompt and rebooted (`reset accepted 30F.png`).
* **`0x303` = `L+R+A+B`** — reaches the same fixed hidden map as `L+R`
  (`design map L+R+A+B.png`), proving the design-map check is a mask test, not
  equality. The published instruction mentions only L+R.
* The reset code is present in AW1 even though the AW2 report found the same
  published “quick reset” did nothing there; this is a real engine-family
  difference, not a list error.

**Bounds proven by rejection (observed).**

* Delete: `0x215` (extra A) and `0x210` (missing Select) → normal boot, no
  prompt; the offline model rejects all other 1022 states, including `0x204`
  (missing Right).
* Reset: `0x00E` (`B+Select+Start`, one face button short) → delete prompt
  remains; `0x30F` (six buttons) → prompt disappears and boot logo returns.
* Design map: no keys, `L` only, and `R` only all fail to produce the fixed
  map; their screenshots differ from L+R by 154k–201k pixels in the map area.
* Advance Campaign: no Select → `CAMPAIGN MAP`; Select → `ADVANCE CAMPAIGN`.

**Published codes tested against the ROM.**

Sources consulted: the Nintendo manual PDF, GameFAQs (live page 403; used the
archived 2025 capture), IGN wiki, CheatCC, Cheat Happens, TCRF (live 403; used
the archived capture), and the VGChartz cheat listing. The code-bearing entries
recovered from those sources are the four rows below; the rest are gameplay
unlocks, tips, or glitches.

| Published item | Source | Result |
|---|---|---|
| Erase data `L+Right+Select` | Nintendo manual, GameFAQs, IGN, CheatCC | **accepted**, prompt observed |
| In-game reset `Start+Select+B+A` | GameFAQs, Cheat Happens, CheatCC | **accepted**, reset observed |
| Nintendo Design Map `L+R` at Design Maps | GameFAQs, CheatCC, TCRF | **accepted**, fixed map observed |
| Advanced Campaign `Select` before Campaign | GameFAQs, CheatCC | **accepted**, banner observed |
| Skip Field Training (play last mission) | GameFAQs | not a code; gameplay shortcut |
| CO / map / gold-menu unlocks | GameFAQs | gameplay unlocks, not codes; shop observed |
| Field Training map-edit glitch | GameFAQs | out of scope; a glitch, not a code |

**Negative results, bounded.**

* **Password system:** case-insensitive byte counts over the whole ROM:
  `password` 0, `passwd` 0, `passwort` 0, `cheat` 0, `debug` 0, `unlock` 0,
  `code` 0, `soundtest` 0, `sound room` 0, `jukebox` 0, `gallery` 0,
  `staff` 0. The only text-entry screen is the 6-character player-name entry;
  it accepts the offered letters/digits and is used as the save name, not a
  password screen. The menu walk reached every top-level mode and submenu
  listed in §3.
* **Debug menu:** the lexicon and widget table exist, but no reachable caller
  was found; `L+R+Select` at the main menu and in the editor does not open it.
  This is a static statement about the code paths found plus the observed key
  tests, not a proof about a hypothetical runtime dispatch not in the image.
* **Sound Room / sound test / staff roll:** no such menu or strings; the only
  “credit” occurrences are story text. AW1 has no Sound Room (that is an AW2
  feature).
* **Delete-save variants:** exact equality admits no second code; the only
  unadvertised boot branch is the `0x00F` path, which is the global reset, not
  a delete variant.

## 7. Validation evidence

**Observed (mGBA 0.10.5, screenshots in this folder).**

* `Advance Wars - boot delete prompt.png` — `Delete all saved data.OK? Yes No`
  after holding L+Right+Select through reset.
* `Advance Wars - data deleted.png` — `Data has been deleted!` after choosing
  Yes (the intermediate `Now deleting data. Do not turn OFF.` was also
  captured).
* `Advance Wars - delete rejected 215.png` — title screen after
  L+Right+Select+A; no prompt.
* `Advance Wars - reset rejected 00E.png` / `- reset four button.png` /
  `- reset accepted 30F.png` — the delete prompt survives B+Select+Start but is
  replaced by the attract screen after the four-button reset; the six-button
  variant also resets.
* `Advance Wars - design map L+R.png` / `- design map L+R+A+B.png` — the same
  fixed structured map; `- design map no keys.png`, `- design map L only.png`,
  `- design map R only.png` — the procedural alternatives.
* `Advance Wars - advance campaign.png` / `- campaign map normal.png` — the
  red `ADVANCE CAMPAIGN` banner vs. the blue `CAMPAIGN MAP` banner.
* Menu-walk frames: `- main menu unlocked save.png`, `- vs mode teams.png`,
  `- vs mode rules.png`, `- link mode.png`, `- pause menu.png`,
  `- options menu.png`, `- stats.png`, `- war room.png`.
* `Advance Wars - hidden map Nintendo layout.png` — direct colour render of the
  600-byte layout table; the three kanji 任天堂 are visible.

**Derived (disassembly, `arm-none-eabi-objdump -M force-thumb`; byte checks
with Python; TCRF archived page cross-check for the published map).**

* Delete validator bytes at `0x38798`: `2200 a801 8801 200f 4008 280f d006
  a801 8801 2085 0080 4281 d100 2201`.
* Reset check at `0x38824`: `b500 4806 8801 4a06 1c10 4388 210f 4008 280f
  d101 f7ff ff4e bc01 4700`.
* Design-map mask at `0x3972`: `480a 6801 20c0 0080 1c02 8809 400a 4282
  d10d f000 fd8a f000 f972`.
* Fixed-map builder at `0x449C` copies 8 bytes from `0x0807CFCC` and reads the
  600-byte table at `0x0827EDFC`; rendering that table yields the kanji
  **任 天 堂** (Nintendo) (`Advance Wars - hidden map Nintendo layout.png`).
* Advance-flag setter at `0x172E4` (`movs r0,#1; strh r0,[r1]`) and the
  alternate-action AND at `0x17E6E`.
* The debug table root `0x082E72C8` is referenced only at `0x3CF8C`.

**RAM dumps (mGBA CLI debugger, savestate `-t` + breakpoint at `0x08038814`).**

* Design-map struct at `0x020157F8`: `001E 0014` (30 × 20); tile layer at
  `0x0201621A` contains 600 values; the values fall into four groups keyed by
  the layout index.
* IWRAM `0x03000DA4` = `0x0001` on the Advance campaign map, `0x0000` on the
  normal campaign map.

**Inferred.**

* The fixed 600-byte layout is the “Nintendo” map: the table spells 任天堂 and
  the L+R branch is observed; the exact mapping from layout values to the
  in-game terrain graphics is inferred from the editor screenshot.
* The Advance Campaign alternate action requires the save-side purchase/unlock;
  the test save had it, but the exact save bit was not isolated.
* The debug-menu cluster is dead development code; “no caller” is a statement
  about the paths found, not a proof about every possible runtime dispatch.

## 8. Unknowns

* The exact save flag/bit that records the Advance Campaign purchase; the
  key-side gate and the runtime flag `0x03000DA4` were isolated, the save-side
  bit was not.
* Whether the debug cluster is reachable through a runtime dispatch table not
  present as a direct pointer/`BL` in the image. No such path was found.
* The Europe save used as a harness is region-compatible for save data, but the
  unlock flags may differ from a USA-created save; this affects reachability,
  not the code logic.

## 9. Tooling

* mGBA 0.10.5 (`mgba-sdl`), Xvfb `:125`, `openbox`, `xdotool`, ImageMagick
  (`import`, `montage`), `arm-none-eabi-objdump`, Python 3.13, Capstone 5.0.7.
* `/tmp/opencode/aw1/out/`:
  * `bootcheck.py` — offline model and full 1024-state enumeration.
  * `keytests.py`, `keymasks.py` — literal-pool key-mask scans.
  * `xref.py` — Thumb `BL` and pointer cross-reference scan.
  * `dbg.py` — mGBA command-line debugger driver for RAM dumps.
  * `map_LR.hex`, `map_none.hex` — 600-tile dumps.
  * `iwram_adv.hex`, `iwram_norm.hex` — IWRAM dumps used for the flag diff.
  * `strings4.txt`, `dis0_60000.txt` — recon artifacts.
* Savestates `.ss1`–`.ss5` were used to return to the main menu / campaign map
  / design map; all are emulator-generated and git-ignored.
* The external GameFAQs/Zophar save used to reach Design Maps and Advance
  Campaign is not redistributed.

## Legal note

No ROM, extracted graphics, music, or copyrighted text is redistributed here.
Only hashes, addresses, short quoted UI labels needed to identify the features,
and the analyst’s own screenshots are included.
