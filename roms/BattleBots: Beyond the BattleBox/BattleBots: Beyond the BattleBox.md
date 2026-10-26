# BattleBots: Beyond the BattleBox (GBA) — Reverse Engineering Report

Report written 2026-10-26 from a local ROM analysis.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/BattleBots: Beyond the BattleBox/BattleBots: Beyond the BattleBox.gba` |
| Size | 8 MiB (`0x800000`) |
| Header title | `BATTLEBOTS` |
| Game code | `ABEE` |
| Maker code | `5G` |
| Software version | `0` |
| Complement check | `0xD4` (matches computed value) |
| Entry word | `0xEA00002E` → ARM at `0x080000C0` |
| MD5 | `4d5bd1475fb898e5be99b85aa45f77fa` |
| SHA-1 | `aa4ee55f8bbb906edbec1761eccc067454a881f8` |
| SHA-256 | `764bb6781efd35986c01e70a230a1cec4b48c308febe6f3ffc0603ce802a818f` |
| Save type | SRAM, 512-byte image (mGBA creates a 512-byte `.sav`) |
| Embedded GBA headers | exactly one (Nintendo logo at file `0x04`) |

ROM addresses below are `0x08000000 + file_offset`. No patch, trainer, or
second image was found: the single Nintendo-logo hit at `0x04`, a standard ARM
crt0 at `0xC0`, and the header fields above account for the whole file.

---

## 2. Executive summary

**This ROM has no password, cheat-code, button-code, or debug-menu system.**
The finding is a bounded negative, not an unfinished search:

* The bytes `PASSWORD`, `PASSWD`, `CHEAT`, `DEBUG`, `SECRET`, `CODE`,
  `SOUND TEST`, `STAGE SELECT`, `LEVEL SELECT`, `BONUS`, `EXTRA` and `CONFIG`
  occur **zero** times in all 8 MiB (case-insensitive; see §6b for counts).
  The only `UNLOCK` hit is the ordinary victory message
  `UNLOCKED FOR THIS PLAYER!` at `0x0426C8`.
* The only text-entry surface in the game is the **team/bot name keyboard**
  (`ENTER TEAM NAME`, handler at `0x08027BC0`). It accepts 8 glyphs from a
  47-symbol alphabet (`0x04244C`) and the buffer (`0x03000100`) is used as a
  display label. No code-shaped constant string exists in the ROM for it (or
  any other field) to be compared against.
* All 55 code sites that read the key-state globals were enumerated. Every
  constant test is an **"any bit of this OR-mask"** test against the current
  held/pressed word (`ands` + `beq`): `A|Start` leaves the title screen, any
  d-pad press cancels the idle timer, `A|Start|R` confirms a name. There is
  **no progress counter, no expected-mask table, and no multi-press sequence**
  anywhere in the ROM.
* The game saves to SRAM instead of passwords: 512-byte image, three 0x90-byte
  slots at `0x000`/`0x090`/`0x120`, plus a configuration block at `0x1F0`.

The password system that people remember from this title belongs to the
32-Mbit re-release **BattleBots: Design & Destroy** (`BBDE`, 4 MiB), which
removed SRAM and added `ENTER TEAM PASSWORD` / `ENTER BOT PASSWORD`. That ROM
is a different build; its password strings and its 34-character alphabet probe
`BCDFGHJKLMNPQRSTVWXYZ-0123456789<>` have **0 hits** in `ABEE`. The
re-release difference is also documented on The Cutting Room Floor.

What *is* developer-intended here is the unlockable content: a five-arena set
of which three are selectable on a fresh save (`BATTLEBOX`, `OIL RIG`,
`AIRPLANE GRAVEYARD`), and the tournament/division victory messages that this
report maps. Those are gameplay unlocks, not codes.

---

## 3. How to reproduce

### Emulator

```bash
sudo apt-get install -y mgba-sdl xvfb xdotool scrot imagemagick \
  binutils-arm-none-eabi python3
pip install --break-system-packages capstone
Xvfb :179 -screen 0 1280x960x24 &
DISPLAY=:179 openbox &
cd "roms/BattleBots: Beyond the BattleBox"
DISPLAY=:179 SDL_AUDIODRIVER=dummy mgba -3 "BattleBots: Beyond the BattleBox.gba" &
```

mGBA 0.10.5 SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows. Hold 150 ms. Shift+F1 saves state slot 1,
F1 loads it.

Capture only the game window (several mGBA windows can exist at once — select by
PID, not by name):

```bash
W=$(DISPLAY=:179 xdotool search --pid "$(pgrep -n -x mgba)" | head -1)
DISPLAY=:179 import -window "$W" shot.png     # 720x480 at -3
```

### Menu path exercised (all screenshots in `screens/`)

```
Title  (Start)
└─ Main menu: TOURNAMENT MODE / BRAWL MODE / MULTI PLAY / LOAD & ERASE / OPTIONS
   ├─ TOURNAMENT MODE → ENTER TEAM NAME (47-glyph keyboard, 8 chars)
   │                    → PIT (CHASSIS / TIRES / BATTERY / MOTOR / WEAPON /
   │                            ARMOR / FIX BOT / DONE; prices, weights,
   │                            TOTAL: $, LIGHTWEIGHT 25-60 LBS bracket)
   │                    → EXIT TO MAIN MENU?  (A = yes, B = no)
   ├─ BRAWL MODE → SELECT DIVISION (LIGHT/MIDDLE/HEAVY/SUPER HEAVY)
   │               → ARENA SELECT (3 of 5 arenas rotate)
   │               → SELECT A BOT (roster of that division)
   │               → P1..P4 lobby (ADD OR REMOVE AI PLAYERS)
   │               → VS screen
   │               → fight (Start = pause overlay)
   │               → END OF BATTLE: GO TO PIT / CONTINUE TO NEXT BOUT /
   │                               REPLAY ARENA / RETURN TO MAIN MENU
   ├─ MULTI PLAY → LINK NOT DETECTED (no link partner)
   ├─ LOAD & ERASE → three slots, LOAD / ERASE buttons
   └─ OPTIONS → TIME / BRIGHT / SFX / MUSIC / CONTROL / PLAY / DONE
                (TIME 2→3→5→8→NO LIMIT; CONTROL NORMAL/REVERSE;
                 PLAY ARCADE/SIM; A SAVE / B CANCEL)

Boot shows the Majesco, Cave+Barn and BattleBots Productions logos (A/Start
skips the sequence after its first frame).
```

### Screenshot index (`screens/`)

| File | Shows |
|---|---|
| `00_title.png` | title screen |
| `01_main_menu.png` | five-item main menu |
| `02_options.png` | OPTIONS |
| `03_load_erase.png` | LOAD & ERASE, three slots |
| `04_multiplay.png` | MULTI PLAY link error |
| `05_brawl_division.png` | SELECT DIVISION |
| `06_brawl_arena.png` | ARENA SELECT (3 arenas) |
| `07_brawl_bot.png` | SELECT A BOT |
| `08_brawl_lobby.png` | P1..P4 lobby |
| `09_brawl_vs.png` | VS screen |
| `10_brawl_fight.png` | fight |
| `11_brawl_pause.png` | pause overlay |
| `12_team_name.png` | ENTER TEAM NAME keyboard |
| `13_pit.png` | PIT / CHASSIS SELECT |
| `14_pit_tires.png` | PIT / TIRES list |
| `15_pit_exit.png` | EXIT TO MAIN MENU? dialog |
| `16_end_of_battle.png` | END OF BATTLE menu |
| `17_logo.png` | Cave+Barn logo (intro) |

### Tests actually run for the negative result

1. Full 8 MiB string scan and keyword classification (`battlebots_scan.py`).
2. Literal search for every password-shaped string and for the `BBDE`
   re-release's password UI/alphabet → 0 hits.
3. Enumerated all LDR sites of the three key globals (55 sites) and the
   constant masks they test.
4. Booted with held combinations: `L+R+Start`, `A+B+Select+Start`,
   `Up+Down+Left+Right`; each produced the normal logo→title→main-menu flow.
5. At the main menu pressed `L`, `R`, `Select`; no extra item or screen.
6. On the name keyboard: stamped 8 glyphs, then pressed A again; the 9th
   glyph was rejected (field stayed at 8).
7. Rotated the arena wheel on a fresh SRAM: only 3 arenas appear.
8. Ran a complete Brawl bout to the `END OF BATTLE` menu.

**Published codes.** The sources checked — GameFAQs cheat page (Wayback
snapshot 2025-10-30), SuperCheats, ChapterCheats and TCRF — list *no* password
or button code for `ABEE`: GameFAQs has two unlockables and one money glitch,
SuperCheats/ChapterCheats repeat the unlockables, TCRF documents only the
re-release difference. There was therefore no published code literal to test.
The only published "codes" for the family are CodeBreaker memory patches
(`almarsguides`) for `BBDE`, which are memory edits and out of scope. The
`BBDE` password UI and alphabet were used as negative probes instead and have
0 hits here. Sources:
`web.archive.org/web/20251030175423/https://gamefaqs.gamespot.com/gba/561454-battlebots-beyond-the-battlebox/cheats`,
`supercheats.com/gameboyadvance/battlebotsbeyondthebattlebox.htm`,
`chaptercheats.com/cheats/gameboyadvance/10305/battlebots-beyond-the-battlebox-cheat-codes`,
`web.archive.org/web/2026/https://tcrf.net/BattleBots:_Beyond_the_BattleBox`.

---

## 4. Address map

| Address | Size | Meaning |
|---|---:|---|
| `0x08003208` | 0x28 | Thumb key poll: reads `REG_KEYINPUT`, derives held/pressed/released |
| `0x04000130` | 2 | `REG_KEYINPUT` (literal at `0x08003230`) |
| `0x03000194` | 2 | held keys, active-high (`~REG_KEYINPUT & 0xFFFF`) |
| `0x03000196` | 2 | pressed-this-frame keys |
| `0x03000198` | 2 | released-this-frame keys |
| `0x0800430C` | ~0x50 | main loop; dispatches update+draw through the tables below |
| `0x030005AC` | 1 | top-level state index (signed byte, 0..5 used) |
| `0x030001A4` | 1 | substate / screen index inside the state |
| `0x030001A5` | 1 | per-substate init flag |
| `0x08288420` | 6×4 | state → substate-array pointer |
| `0x0803F2AC` | 0x24 | shared substate→handler byte table (state 5 base) |
| `0x0803F2B0` | — | state 0/3 array; `0x0803F2BA` state 1; `0x0803F2C2` state 2; `0x0803F2CD` state 4 |
| `0x08288390` | 18×4 | handler update-function table |
| `0x082883D8` | 18×4 | handler draw-function table |
| `0x04244C` | 47 | name-entry glyph alphabet (`A-Z0-9.,*/-=+?!< ` + space) |
| `0x04212E` | 70 | display font/glyph map (A-Z0-9 + punctuation + `$:&`) |
| `0x03000100` | 8 | team/bot name buffer |
| `0x0828619C` | 16×4 | robot short-name pointers |
| `0x082861DC` | 16×4 | robot long-name pointers |
| `0x0828A1EC` | 5×4 | arena name pointers |
| `0x0828B56C` | 8×4 | PIT category pointers (`FIX BOT` … `DONE`) |
| `0x08289FE8` | 32×4 | OPTIONS string pointers |
| `0x0828E8B0` | — | tournament-victory display list (CONGRATULATIONS / WINNINGS / ALL ARENAS ARE NOW UNLOCKED) |
| `0x08007394` | ~0x60 | CONTROL=NORMAL/REVERSE: swaps Up/Down bits in held and pressed masks |
| SRAM `0x000`, `0x090`, `0x120` | 0x90 each | three save slots: name at +0, slot check word at +8, `0x5203` at +0x0E |
| SRAM `0x1F0` | 0x10 | configuration block (`B0 17 00 00 04 04 02 02 00 06 B0 0B B0 0B B0 0B`; option meanings Inferred) |

Handler table (update function, Thumb bit cleared; screen identity is Observed
unless marked):

| # | Function | Screen |
|---:|---|---|
| 0 | `0x080203BC` | intro/publisher-logo sequence (Majesco, Cave+Barn, BattleBots Productions; A/Start skips after the first) |
| 1 | `0x08000750` | title screen (A/Start starts the game) |
| 2 | `0x08007930` | battle engine |
| 3 | `0x0802299C` | SELECT A BOT |
| 4 | `0x08021288` | OPTIONS |
| 5 | `0x080236B0` | ARENA SELECT |
| 6 | `0x08023CC4` | LOAD & ERASE |
| 7 | `0x080269B4` | MAIN MENU |
| 8 | `0x08027BC0` | ENTER TEAM NAME |
| 9 | `0x0802D304` | generic list menu (PIT) |
| 10 | `0x0802E9F0` | P1..P4 lobby / AI setup |
| 11 | `0x0802F614` | in-tournament transition phase (Derived) |
| 12 | `0x0802E614` | in-tournament transition phase (Derived) |
| 13 | `0x080301D8` | END OF BATTLE + victory/prize display |
| 14 | `0x08030E28` | boot/transition phase (Derived) |
| 15 | `0x08031A60` | VS screen |
| 16 | `0x08032494` | division select / link-status screen |
| 17 | `0x08032758` | late-tournament phase (Derived) |

The 6→18 mapping explains why the "state" byte only takes values 0..5 while
the game has eighteen screen routines: substate selects the handler. All 18
handler indices occur in the state/substate arrays, so there is no orphan
handler reserved for a flag-only debug screen.

Observed `(state,substate)` samples:

| Screen | state | substate | handler |
|---|---:|---:|---:|
| intro logos | 5 | 0 | 0 |
| title | 5 | 1 | 1 |
| main menu | 5 | 2 | 7 |
| OPTIONS | 4 | 0 | 4 |
| LOAD & ERASE | 3 | 0 | 6 |
| MULTI PLAY (link error) | 2 | 0 | 16 |
| SELECT DIVISION | 1 | 0 | 16 |
| ARENA SELECT | 1 | 1 | 5 |
| SELECT A BOT | 1 | 2 | 3 |
| lobby | 1 | 3 | 10 |
| VS | 1 | 4 | 15 |
| fight | 1 | 5 | 2 |
| END OF BATTLE | 1 | 7 | 13 |
| ENTER TEAM NAME | 0 | 1 | 8 |
| PIT | 0 | 2 | 9 |

---

## 5. Algorithm

### 5.1 Key poll (exact)

```python
raw     = REG_KEYINPUT            # 0x04000130, active-low, bits 0..9
held    = (~raw) & 0xFFFF         # 0x03000194
pressed = held & (~prev) & 0xFFFF # 0x03000196
released= prev & (~held) & 0xFFFF # 0x03000198
prev    = held
```

### 5.2 Screen dispatch (exact)

```python
state    = iwram[0x030005AC]          # signed byte
substate = iwram[0x030001A4]
ptr      = rom_u32(0x08288420 + 4*state)
handler  = rom_u8(ptr + substate)     # 0..17
update   = rom_u32(0x08288390 + 4*handler)
draw     = rom_u32(0x082883D8 + 4*handler)
update(); draw()
```

### 5.3 Menu/action input (the whole design)

Every code path uses the *pressed* or *held* word and a constant OR-mask:

```asm
ldr  r0, =0x03000196
ldrh r1, [r0]
movs r0, #MASK
ands r0, r1
cmp  r0, #0
beq  no_action
```

`ands` + `beq` means **any** bit of `MASK` fires the action; the game never
requires two buttons simultaneously. Representative sites:

| Site | Word | Mask | Meaning |
|---|---|---|---|
| `0x080007BC` | held | `0x009` | A **or** Start leaves the title screen |
| `0x08007678` | held | `0x0F0` | any d-pad press cancels the idle/attract timer |
| `0x08027F98` | held | `0x080/0x040/0x010/0x020` | name keyboard Up/Down/Left/Right |
| `0x08027C5C` | held | `0x002` | B cancels name entry **if** `name[2] != 0` |
| `0x080280F8` | pressed | `0x109` | A **or** Start **or** R confirms name |
| `0x0803092E` | pressed | `0x009` | A or Start continues |

There is no table indexed by a progress counter and no per-frame "expected
button" comparison, so a multi-press code cannot be expressed by this engine.

### 5.4 Name entry (the only text input)

* Buffer `0x03000100`, 8 bytes, default names `AAAAAAAA`…`DDDDDDDD`.
* Alphabet `0x04244C`: 47 glyphs `A-Z 0-9 . , * / - = + ? ! < space`.
* A stamps the current glyph and advances; after 8 glyphs a 9th stamp is
  rejected. The wheel is scrolled with Up/Down; Left/Right move the edit
  position. B leaves the screen only when the name already has at least three
  characters (`name[2] != 0` at `0x08027C5C`).
* The name is used as a label: `TEAM:` (`0x041FEC`), ` BOT`/` BOTS`
  (`0x04220C`/`0x042214`) and the lobby/VS panels read `0x03000100`.

### 5.5 Unlockables (developer-intended, no code)

Five arenas exist in the ROM (`0x0828A1EC` → `BATTLEBOX`, `OIL RIG`,
`AIRPLANE GRAVEYARD`, `VOLCANO`, `MACHINE PLANT`). On a fresh save the ARENA
SELECT wheel rotates only through the first three; `VOLCANO` and
`MACHINE PLANT` never appear. The tournament-victory display list at
`0x0828E8B0` contains `ALL ARENAS ARE NOW UNLOCKED FOR THIS PLAYER!`
(`0x0426B4`, `0x0426C8`), and the division messages
`YOU HAVE DEFEATED ALL OPPONENTS! NOW TRY YOUR HAND IN THE ... DIVISION!`
(`0x0426F8`…).

---

## 6. Tables

### 6.1 Robot roster (16; `0x0828619C` short / `0x082861DC` long)

`BACKLASH, BIOHAZARD, COMPLETE CONTROL, DEADBLOW, EL DIABLO GRANDE,
DIESECTOR, HAZARD, JAWS OF DEATH, MINION, MOUSER MECHA-CATBOT, OVERKILL,
SUNSHINE LOLLIBOT, TAZBOT, TOE CRUSHER, TORO, ZIGGO`

Division select shows four per weight class; the lightweight Brawl wheel cycles
`TOE CRUSHER → MOUSER → BACKLASH → ZIGGO` (Observed).

### 6.2 Arena set (5; 3 selectable on a fresh save)

| String | ROM | Fresh-save selectable |
|---|---|---|
| `BATTLEBOX` | `0x042124` | yes |
| `OIL RIG` | `0x04211C` | yes |
| `AIRPLANE GRAVEYARD` | `0x042108` | yes |
| `VOLCANO` | `0x042100` | no |
| `MACHINE PLANT` | `0x0420F0` | no |

### 6.3 OPTIONS values (`0x08289FE8`)

`TIME` = 2/3/5/8 MIN, NO LIMIT · `BRIGHT` = LEVEL 1..5 · `SOUND FX` and
`MUSIC` = VOL 1..8 · `CONTROL` = NORMAL/REVERSE · `PLAY` = ARCADE/SIM ·
`DONE` (A SAVE / B CANCEL).

`CONTROL=REVERSE` is implemented at `0x08007394`: it swaps the Up (`0x40`) and
Down (`0x80`) bits in both the held and pressed words before the menus read
them.

### 6.4 SRAM layout (Observed `.sav`)

```
0x000..0x08F  slot 1: "AAAAAAAA" | 35 2A 00 00 00 00 03 52 | data
0x090..0x11F  slot 2: 00*8       | 33 22 00 00 00 00 03 52 | empty
0x120..0x1AF  slot 3: 00*8       | 33 22 00 00 00 00 03 52 | empty
0x1B0..0x1EF  zero padding
0x1F0..0x1FF  B0 17 00 00 04 04 02 02 00 06 B0 0B B0 0B B0 0B
```
The slot check word at +8 changes with the stored name (empty slots have
`0x2233`, the `AAAAAAAA` slot has `0x2A35`), so it is a per-slot check value,
not a fixed magic. The 512-byte image is exactly what a 4-Kbit SRAM cart
exposes; the game never asks for a password because it can write the slot.

### 6.5 Text-space census (exact)

| Metric | Count |
|---|---:|
| printable ASCII runs ≥3 in the whole ROM | 192,992 |
| runs ≥3 inside the UI bank `0x3A000..0x45FFF` | 668 |
| runs ≥8 inside the UI bank | 403 |
| `password`/`passwd`/`cheat`/`debug`/`secret`/`code`/`bonus`/`extra`/`config` hits | **0** |
| `unlock` hits | 1 (`UNLOCKED FOR THIS PLAYER!`) |
| `test` hits | 1 (`TESTING` in credits) |
| `BBDE` password UI strings / 34-character alphabet hits | **0** |

---

## 6b. Enumeration

### 6b.1 Space definition

| Surface | Representation | Size |
|---|---|---|
| Password / cheat code | **does not exist** | **0** |
| Stored code table | **none** (the short-string pointer tables are only the roster, arenas, OPTIONS, PIT and default team-name labels) | 0 |
| Validator / checksum | **none** (no length+checksum acceptance routine for entered text; the only name check is `name[2] != 0` to allow B to leave) | 0 |
| Team/bot name field | 8 glyphs × 47-symbol alphabet | 47⁸ = 2.381×10¹³ possible labels, not codes |
| Button input | 10 buttons, read as OR-masks; 55 read sites; 0 sequence tables | no code space |

### 6b.2 Novel codes

There is no code system, therefore no code can be minted. The deliverable for
this ROM is the bounded negative: the game offers no entry point, no validator,
and no stored code list, and every published "password" for the family belongs
to the `BBDE` re-release (absent here). No claim of a generated working code is
made because none is representable.

### 6b.3 Bounds proven by rejection (all Observed)

| Test | Input | Result |
|---|---|---|
| 9th name glyph | 8 stamps then A again | rejected: field stays at 8 |
| Glyphs outside the alphabet | only 47 wheel symbols exist | not selectable (e.g. `%`, `@`, `#`, `(`) |
| Boot button combos | `L+R+Start`, `A+B+Select+Start`, `Up+Down+Left+Right` held through reset | normal logo → title → main-menu flow, no extra screen |
| Menu modifier keys | `L`, `R`, `Select` at main menu | no change to the five-item menu |
| `BBDE` password material | `PASSWORD`, `ENTER BOT/TEAM PASSWORD`, 34-character alphabet | 0 occurrences; no screen could accept them |
| Published lists | GameFAQs (archived 2025-10-30), SuperCheats, ChapterCheats, TCRF | lists contain only unlockables/glitches, no codes |

### 6b.4 Search space actually covered

* Whole file: 8,388,608 bytes, printable-run scan and keyword scan.
* Text bank: 668 runs, 403 of length ≥8 read and classified.
* Button engine: 14 held-word, 39 pressed-word and 2 released-word read sites;
  every constant mask recorded. Each mask is an immediate or a PC-relative
  literal, never a table entry. A whole-ROM scan for runs of four or more
  consecutive 16-bit button masks returned 178 candidates; the candidates
  inspected lie in tile/bitmap data (e.g. `0x049584`, `0x3F2F8`), not in a table the
  key code reads.
* Screen engine: 6 states × 18 handlers, 14 of 18 handlers matched to a
  photographed screen; the 4 remaining slots (11, 12, 14, 17) are the
  boot/arena transition phases listed in §4.
* Save engine: 512-byte SRAM image parsed into three 0x90-byte slots.

---

## 7. Validation evidence

**Observed**
* Every screenshot in `screens/` (title, five main-menu entries, all Brawl
  sub-screens, pause, name keyboard, PIT, exit dialog, END OF BATTLE, logos).
* Fresh-save ARENA SELECT cycles exactly three arenas; `VOLCANO` and
  `MACHINE PLANT` never appear.
* The 8-glyph limit on the name field (9th A rejected).
* 512-byte `.sav` with three repeated slot headers at `0x08/0x98/0x128`.
* Zero hits for all password/cheat/debug strings, including the `BBDE`
  probes.

**Derived**
* Key poll at `0x08003208` and the three globals (`0x03000194/196/198`);
  all constant tests are OR-masks with no sequence state.
* Main loop `0x0800430C` and the 6-state → 18-handler dispatch tables.
* Handler→screen table and the `(state,substate)` samples.
* Roster/arena/option/pit pointer tables.
* SRAM slot stride and magic.

**Inferred**
* Exact unlock conditions for `VOLCANO`/`MACHINE PLANT` (the in-ROM victory
  message names arenas; the published pages say tournament/division clears —
  the flag bit itself was not isolated).
* Screen identities marked "(Derived)" in §4 for handler slots 11, 12, 14, 17
  (intermediate arena/boot phases).

---

## 8. Unknowns

* The precise per-frame condition that turns the name keyboard's confirm cell
  on. The reproducible path used here is: stamp 8 glyphs, scroll the glyph
  wheel to the symbol band (`7 8 9 . , * / - =`), press A. Pressing A at the
  first glyph page with 8 glyphs did not confirm. This affects only the
  repro path, not the cheat conclusion.
* The arena-unlock flag bit (which byte of the SRAM slot is set on a tournament
  clear). Reaching a full tournament clear would take a long play session; the
  availability behaviour on a fresh save is observed, the flag is not.
* Handler slots 11/12/14/17 were not individually photographed; they are part
  of the tournament/boot transition chain, not menus.

---

## 9. Tooling

| Tool | Use |
|---|---|
| mGBA 0.10.5 (`mgba-sdl`) | ground truth, screenshots, savestates |
| Xvfb `:179` + openbox | headless display |
| `xdotool`, ImageMagick `import`/`convert` | input and 720×480 window capture |
| `arm-none-eabi-objdump -M force-thumb` | disassembly of handlers and polls |
| Capstone 5.0.7 | literal-pool / key-mask scans |
| `battlebots_scan.py` (next to the ROM) | reproduces §1, §6.5, §4 tables and the password probes |
| `battlebots_scan.txt` | saved output of the scan |
| `battlebots_state.py` (next to the ROM) | reads `state`/`substate`/key words out of an mGBA PNG savestate |
| `screens/*.png` | captured evidence (18 screens) |

`battlebots_scan.py` exits 0 and prints
`result: password-system probes present = 0` for this ROM.

---

## 10. Legal note

No ROM, extracted graphics, music, or text banks are redistributed with this
report. Only hashes, addresses, small UI label strings needed for
identification, and original screenshots of the running game are included.
