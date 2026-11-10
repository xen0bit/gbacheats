# Boulder Dash EX (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Boulder Dash EX/Boulder Dash EX.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`) |
| Header title | `B-DASH EX` (NUL padded) |
| Game code | `ABDE` |
| Maker code | `7F` |
| Software version | `0x00` |
| Entry word | `EA00002E` = ARM `b 0x080000C0` (standard) |
| MD5 | `8653d5731f4effd21e435b9a274023a4` |
| SHA-1 | `8bc0dadbd18e3d88645aaba3aa0ced8088201c8f` |
| SHA-256 | `ffaabce2401a54dc4e454893a8ce831c81fa1e2d6c0404ceb29e8c620a813dde` |

Published identity: *Boulder Dash EX*, GBA, Vision Works / Kemco, 2002
(USA/EU). `file` reports `"B-DASH EX" (ABDE7F, Rev.00)`; the ROM is a
single 4 MiB image, not a multi-game cart.

**Phase 0 / header anomalies.** The Nintendo logo is intact and the
complement byte at `0xBD` is `0x7C`, exactly the value computed over
`0xA0..0xBC`. The 16-bit header-checksum field at `0xBE` is `0x0000`
instead of the computed `0x007C`. The entry branch, title, game code and
logo are stock, the first 4 KiB is ordinary crt0/code, and no cracktro or
trainer strings are present. This is a **repacked header tail**, not a
content patch or trainer.

**Embedded GBA header (logo scan).** A second complete GBA header exists at
file offset `0x60F38` (logo at `0x60F3C`): title `B-DASH EX`, game code
`ABDJ`, maker `7F`, version `0`, complement/checksum `0x8A`, entry word
`EA00002E`, and crt0 linked at `0x02000000`. This is the **multiboot /
single-pak link client** used by Battle Mode (one cartridge, up to four
players); it is not a second playable retail image and contains no separate
menu of its own that is reachable from the parent ROM.

Save hardware is battery-backed (there is a real save struct at
`0x02018190` and a `Data Delete` screen that warns "Do not turn off the
power"), not a password-only cart.

## 2. Executive summary

**There is no player-entered password or button-code cheat in this build.**
The game has no text-entry field of any kind, no password alphabet and no
password string: `strings` contains zero occurrences of `password`/`passwd`
and no long `A-Z0-9!?` alphabet. Every menu is a fixed cursor menu driven
by D-pad + A/B/L/R/Start.

What does exist:

1. **A reachable Sound Settings sound test.** Options → Sound Settings has a
   BGM selector; **L/R** cycle the 27-entry track-name table at
   `0x083376B4` (`Underground New Wave` … `Tomorrow's Promise`, `Sound
   Select`). It plays late-game music from the very first menu, including
   "Final Trial" and "Tomorrow's Promise" (`screenshots/06_sound_test.png`).

2. **Reachable stage/level selects.** The in-game pause menu (Start) has
   *Continue / Map Preview / Retry / Change Stage / Exit*. *Change Stage* in
   EX Story Mode opens **World Select → Stage Select** (the header string at
   `0x0809F76C` was observed on screen); in Classic Mode it opens the classic
   **cave/level select** (`Boulder Dash`, `Select Cave`, `Select Level`).
   Both are gated by saved progress. The adjacent `Level Select` string
   (`0x0809F75C`) is the Classic-mode counterpart; the Classic screen we
   reached draws the Boulder Dash logo instead, so that exact label was not
   seen on screen.

3. **A hidden developer cheat/config screen that is dead code.** At
   `0x0801BBDC` there is a complete developer editor that draws and edits
   six save-flag "cheats":

   ```
   LANG_SELECT      English
   EXMODE_CHEAT     OFF
   CLASSIC_CHEAT    OFF
   CARD_CHEAT       OFF
   CLEAR_CHEAT      OFF
   TIME_CHEAT       OFF
   EVENT_CHEAT      OFF
   ```

   The screen is entered through screen state `73` (`0x49`). Only one BL
   references the function (`0x08007A36`), and the two instructions that can
   write state `73` (`0x080074F2`, `0x080076A4`) are both gated on a
   **`0xFF` return value** from `0x0802D440` / `0x0802E400`. Those two
   functions have exactly the return sites listed in §6, and none returns
   `0xFF`. **The branch is therefore unreachable by any controller input**;
   we proved this statically and by arming breakpoints at the screen and at
   both state writers during a complete menu walk (never hit).

   Forcing state `73` with a debugger makes the screen appear
   (`screenshots/11_hidden_cheat_screen_card_on.png`). It is a genuine,
   functional developer cheat: setting the `CARD_CHEAT` byte
   (`0x02018190 + 0x3B2`, i.e. `0x02018542`) to 1 makes every card in the
   gallery show its full artwork and description instead of the locked
   silhouette + "Clear the stages…" hint (`screenshots/12_card_cheat_effect.png`).
   This is a developer shortcut, not an in-game code, and it is labelled as
   debugger-forced everywhere it appears below.

**Deliverable classification:** negative result for *player-entered* codes,
with a fully enumerated dead developer cheat system and its one verified
effect. There is no password/button space to mint a code from; §6b proves
that absence against the actual search space.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba`), 3× scale.
* Display: `Xvfb :202 -screen 0 1024x768x24` + `openbox`, `DISPLAY=:202`,
  `SDL_AUDIODRIVER=dummy`.
* Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrows. Hold ordinary presses ~60 ms; longer holds auto-repeat and
  double-step the scrolling menus.
* Screenshots in `screenshots/` were taken with `scrot` on the 1024×768 root
  and are the raw window (no crop).

Menu paths (all observed):

| Screen | Path |
|---|---|
| Title | boot → "Press Start" (`01_title.png`) |
| Main | Start → EX Game / Classic Game / Options (`02_main_menu.png`) |
| EX submenu | A on EX Game → Story / Battle / Tutorial / Card Collection / Preview Scenes (`03_ex_menu.png`) |
| Classic submenu | A on Classic Game → Classic Mode / Tutorial (`04_classic_menu.png`) |
| Options | A on Options → Sound Settings / Data Delete (`05_options.png`) |
| Sound Settings | A → BGM L/R selector + BGM/SE volume + OK (`06_sound_test.png`) |
| Data Delete | A → "Caution! Erase all data? Yes/No" (`13_data_delete.png`) |
| Story Mode | EX → Story Mode → intro → World Select → Stage Select (`07_stage_select.png`) |
| Pause (EX/Classic) | Start → Continue / Map Preview / Retry / Change Stage / Exit |
| Classic Mode | Classic Game → Classic Mode → Select Cave / Select Level / Game Start |
| Tutorial | 8 lessons: Basics, Rock, Hope Crystal, Mushrooms, Super Pick, Time Bomb, Magic Glove, Monsters |
| Card Collection | EX → Card Collection → 49-card grid → detail view (`10_card_collection.png`) |
| Preview Scenes | EX → Preview Scenes → Opening, Scene I–VI, Credits, OK |
| Battle 1P | EX → Battle Mode → One Player → Time / Stage / Character / Computer / Game Start (`08_battle_setup.png`) |
| Battle link | EX → Battle Mode → Multi Player → "Checking Connection" (`09_multiplayer_check.png`) |

**Forcing the dead cheat screen (analysis only, not an in-game code):**

```
mgba -3 -g "Boulder Dash EX.gba"
gdb-multiarch
  set architecture arm
  target remote :2345
  break *0x080071EC                  # screen-state dispatcher
  # on hit:
  set {unsigned char}0x02003EA0 = 0x49
  continue
```

The screen appears; B returns to the title. This is a RAM write, not a
cheat, and is used only to document what the dead code does.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`; RAM is little-endian.

| Address | Meaning |
|---|---|
| `0x080000C0` | ARM crt0 entry |
| `0x080071EC` | Main/menu screen-state dispatcher (Thumb); reads byte `0x02003EA0`, indexes 102-entry table at `0x08007220`, max 101 |
| `0x08007220` | State jump table, 102 × `u32`; 29 distinct targets (28 handlers + default `0x080071EC`) |
| `0x02003EA0` | Current screen state (byte) |
| `0x08007A30` | State `73` handler: writes 7 to `0x0200D5BC`, then `BL 0x0801BBDC` |
| `0x0801BBDC` | Hidden cheat/config screen: reads save bytes, draws 7 rows, runs a key loop |
| `0x08007A36` | The only `BL` to `0x0801BBDC` (inside state-73 handler) |
| `0x080074DE` | Title-screen call to `0x0802D440`; compares return with `0xFE` (start) / `0xFF` (cheat) |
| `0x080074F2` | Dead writer of state `73` (`movs r0,#0x49; b 0x080071EA`) |
| `0x080076A4` | Second dead writer of state `73` |
| `0x0802D440` | Title/attract loop; return sites: `0x0802D716` → `0xFE`, `0x0802D74A` → `0x00`. No `0xFF` |
| `0x0802E400` | Options/Sound-Display screen; return sites: `0x0802E88C` → `0xFE`, `0x0802E94C` → `0x00`, `0x0802E988` → `0x62`. No `0xFF` |
| `0x02018190` | Save/config struct base (stage and cheat flags; matches all published CodeBreaker addresses) |
| `0x02018540`–`0x02018546` | Cheat/config bytes `+0x3B0…+0x3B6` (see §6) |
| `0x02018557` | Options/language latch used by the options screen (`+0x3C7` cursor family) |
| `0x0200D5BC` | Screen-transition byte written by state handlers (7 = cheat screen) |
| `0x03002830` | Active-high held keys (updated by `0x08000E34`) |
| `0x03002832` | Active-high newly-pressed keys |
| `0x0809F75C` | `"Level Select"` text |
| `0x0809F76C` | `"Stage Select"` text |
| `0x080A016C`–`0x080A01F4` | Cheat-screen strings (see §6) |
| `0x083376B4` | 27-entry BGM name pointer table (Sound Settings) |
| `0x08336BD4` | 49-entry card-name pointer table |
| `0x08336EE4` | 49-entry card-description pointer table |

The `0x02018190` base is independently corroborated by the published
CodeBreaker list: "World of Sand Open World" writes `0x02018194`, "World of
Fire" `0x02018195`, "World of Water" `0x02018196`, "World of Ice"
`0x02018197`, "World of Evil" `0x02018198`, "World of Forest Open Stage"
`0x0201819B`/`0x0201819C`/`0x020181A4`, "Classic Game - Open All Levels"
`0x02018560`. All are inside this struct.

## 5. Algorithm

### 5.1 Screen-state matcher (why the cheat screen is dead)

```
state = *(u8*)0x02003EA0
if state > 101: loop
handler = *(u32*)(0x08007220 + state*4)
goto handler
```

State `73` → `0x08007A30`:

```
*(u8*)0x0200D5BC = 7
cheat_screen()          // 0x0801BBDC
```

Only two sites write `state = 73`:

```
; title path, 0x080074DE
r0 = title_loop(0)                     ; 0x0802D440
if r0 == 0xFE: start_game()
if r0 == 0xFF: state = 73              ; 0x080074F2  <-- dead
else: return

; options path, 0x080075FC
r0 = options_screen(*(u8*)(0x02018190+0x3C9))   ; 0x0802E400
switch r0:
  0xFE -> ...
  0xFF -> state = 73                   ; 0x080076A4  <-- dead
  ...
```

Return-site audit (`objdump -M force-thumb`, single epilogue each):

| Function | Return sites | Values |
|---|---|---|
| `0x0802D440` | `0x0802D716`, `0x0802D74A` | `0xFE`, `0x00` |
| `0x0802E400` | `0x0802E88C`, `0x0802E94C`, `0x0802E988` | `0xFE`, `0x00`, `0x62` |

Both epilogues are reached only through those `movs r0,#imm` sites (verified
by grepping every branch to the epilogue). The value `0xFF` is never
produced, so the two `cmp r0,#0xFF / beq` edges are dead. A whole-ROM scan
finds only two `movs r0,#73` instructions in the menu code
(`0x080074F4`, `0x080076A6`); no ARM or indirect writer targets the state
byte.

### 5.2 Hidden cheat screen (dead code, documented for completeness)

```
base = 0x02018190
draw frame and fixed rows:
  LANG_SELECT   value[base+0x3B3] -> English/Japanese/German/French
  EXMODE_CHEAT  value[base+0x3B0] -> ON/OFF
  CLASSIC_CHEAT value[base+0x3B1] -> ON/OFF
  CARD_CHEAT    value[base+0x3B2] -> ON/OFF
  CLEAR_CHEAT   value[base+0x3B4] -> ON/OFF
  TIME_CHEAT    value[base+0x3B5] -> ON/OFF
  EVENT_CHEAT   value[base+0x3B6] -> ON/OFF
loop:
  read keys
  up/down move a row marker; left/right or A change the selected value
  B / cancel returns to the title screen (observed)
```

The ON/OFF test is literally `ldrb r0,[base+off]; cmp r0,#1`; every other
value is drawn as `OFF`. There is no checksum, alphabet or length; the
"space" is seven one-byte save fields.

### 5.3 Reachable level-select / sound test

* Pause → Change Stage is a normal game-state transition to the progress
  screen. In EX it shows `Stage Select` with one bubble per stage of the
  current world; only saved-cleared stages are selectable. In Classic it
  shows the Boulder Dash cave/level selector; locked caves/levels are shown
  with `*` and ignore Left/Right.
* Sound Settings reads the 27-entry BGM pointer table and changes the
  currently playing track; it is a sound test, not an unlock.

## 6. Tables

### 6.1 Dead cheat-screen strings and fields

| String | ROM address | Save field |
|---|---|---|
| `LANG_SELECT` | `0x080A016C` | `+0x3B3` (0=English, 1=Japanese, 2=German, 3=French) — inferred |
| `EXMODE_CHEAT` | `0x080A0178` | `+0x3B0` — derived from draw/read order |
| `CLASSIC_CHEAT` | `0x080A0188` | `+0x3B1` — derived |
| `CARD_CHEAT` | `0x080A0198` | `+0x3B2` — **confirmed by experiment** |
| `CLEAR_CHEAT` | `0x080A01A4` | `+0x3B4` — derived |
| `TIME_CHEAT` | `0x080A01B0` | `+0x3B5` — derived |
| `EVENT_CHEAT` | `0x080A01BC` | `+0x3B6` — derived |
| `ON` / `OFF` | `0x080A01C0` / `0x080A01C4` | values |
| `English`/`Japanese`/`German`/`French` | `0x080A01D0`…`0x080A01EC` | language names |
| `INIT` | `0x080A01F4` | reset label |

Confirmed effect: `+0x3B2 = 1` → screen shows `CARD_CHEAT ON`, and card 1
(`Mirror Jewel`) switches from the locked black silhouette + hint to full
art + full description (`screenshots/12_card_cheat_effect.png`). The other
five flags were not individually exercised (§8).

### 6.2 Key-mask / button-code search

The engine's key state is active-high at `0x03002830` (held) and
`0x03002832` (newly pressed), filled by `0x08000E34`. A scan for
contiguous `u16` runs of length ≥5 whose values are single-button masks
(`1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200`) found 22 runs. The only
ordered multi-button sequences are:

| Address | Length | Content | Xref |
|---|---|---|---|
| `0x08086376` | 11 | `0x200,0x80,0x10,0x1,0x2,0x4,0x8,0x20,0x40,0x100,0x200` | none (data/UI order) |
| `0x080919FC` | 10 | `0x80,0x10,0x1,0x2,0x4,0x8,0x20,0x40,0x100,0x200` | none |

Both are joypad/UI order tables, not cheat sequences. All other runs are
repetitions of one mask (level/terrain data). No code reads a sequence
table with a progress counter, and no input handler compares against a
multi-press literal. **No button-code table exists in this ROM.**

### 6.3 BGM sound-test table (`0x083376B4`)

27 named entries:

`0 Underground New Wave, 1 Jump Up, 2 Departure, 3 Magical Stones,
4 Legend's Legacies, 5 Well Done!, 6 As You Like, 7 Bittersweet,
8 Dig It All, 9 Desert Wind, 10 Bright Stream, 11 Rainbow Prism,
12 Touched By Fire, 13 Deep Underground, 14 Do Your Best, 15 You Win!,
16 Dead Heat, 17 Peaceful World, 18 Crisis, 19 To The Future,
20 Hurdling Hindrances, 21 Chaos, 22 Final Trial, 23 Tomorrow's Promise,
24 Eternal Dream, 25 Brain Teaser, 26 Sound Select`

Observed: `Underground New Wave` (index 0), `Hurdling Hindrances` (20),
`Final Trial` (22), `Tomorrow's Promise` (23) reached with L/R from the
first menu.

### 6.4 Card gallery

49 cards (`0x08336BD4` names, `0x08336EE4` descriptions). Six descriptions
are the literal string `It's a secret.` — cards **37, 38, 39, 40, 41, 45**
(Alex, Sonya, Nick, Emily, Dark King, Rockford). They are the gallery's
hidden entries; the rest show either a clear-stage hint or a
defeat-monster hint.

### 6.5 Screens / input surfaces walked

Title, main menu, EX submenu, Classic submenu, Options, Sound Settings,
Data Delete, Battle Mode (One Player + Multi Player), Battle setup, Tutorial
(8 lessons), Story Mode intro, World Select, Stage Select, Classic cave/level
select, in-game HUD, EX pause menu, Classic pause menu, Card Collection
(grid + detail), Preview Scenes. Every screen was entered and every menu
row was traversed; individual card pages, lesson playbacks and scene
playbacks were not all played. No screen other than the pause "Change
Stage" exposes a stage selector, and no screen accepts text.

## 6b. Enumeration

**Space definition — player-entered codes: none.**

| Candidate space | Result |
|---|---|
| Text password | 0 password strings (`password`/`passwd` = 0 hits in `strings -t x`), no text-entry routine, no alphabet string ≥16 uppercase/digit characters |
| Button code | 0 sequence tables; 22 mask runs examined, only 2 ordered tables and both are UI order data with no code reference |
| Hidden menu by input | 1 hidden menu exists in code but its entry is provably unreachable (0 of 2 state-writer edges can evaluate true) |
| Save-edit "cheats" (CodeBreaker) | Out of scope; they are RAM writes, not in-game codes |

**Button space considered.** The pad supplies 10 buttons = 1024 held-mask
states; the engine exposes both held (`0x03002830`) and newly-pressed
(`0x03002832`) states. We searched the entire 4 MiB for contiguous
multi-mask tables (above) and for literal comparisons against such tables.
No match exists, so the "undocumented combination" space for a
pause-menu code is empty in this build, not merely untested.

**Hidden-menu space.** Seven one-byte fields: six booleans and a 4-value
language ⇒ 2^6 × 4 = **256 legal configurations** (plus arbitrary byte
values, which the drawing routine renders as `OFF`). One configuration
(`CARD_CHEAT=1`) was forced and its effect verified in the gallery. The
menu itself was enumerated row-by-row from the draw code and one screenshot.

**Bounds proven by rejection.** Because there is no input surface, the
relevant rejection is the entry gate:

* `0x0802D440` is executed at the title screen; its return is `0xFE` or
  `0x00` for every input the title accepts (Start/A/B). The `0xFF` edge at
  `0x080074F2` never fires, with or without any button combination.
* `0x0802E400` is executed for Options; its returns are `0xFE`, `0x00`,
  `0x62` (the `0x62` path is the B/cancel result). The `0xFF` edge at
  `0x080076A4` never fires.
* Breakpoints at `0x0801BBDC`, `0x08007A30`, `0x080074F2`, `0x080076A4`
  were armed while walking title → main → EX → Story Mode → in-game pause →
  Change Stage → Options → Sound Settings → Data Delete. None hit. The
  remaining screens (Card Collection, Preview Scenes, Classic Mode, Battle,
  Tutorial) were walked in separate sessions; they cannot write state 73
  either, because the whole-ROM `movs r0,#73` scan finds only the same two
  sites. The only way the screen appeared was the explicit debugger write
  `0x02003EA0 = 0x49`.

**Published-code audit.** Searches for the game's cheats return only
CodeBreaker/GameShark RAM codes (Almar's Guides, GameHacking.org); GameFAQs'
cheats page returns 403 and has no Wayback snapshot, and the archived
walkthrough has no cheat/password section. There is therefore **no
published in-game code to test**; the published CodeBreaker addresses do,
however, corroborate the save base `0x02018190` (§4).

**Novel code.** None can exist: a novel code requires an encoder or an
accepted-input table, and neither exists. The equivalent deliverable here is
the novel *finding* that the only cheat surface is a dead developer menu,
proven by both the return-value audit and the live breakpoint walk, plus a
demonstration that the menu's flags work when forced.

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| Header/title/code/hashes | Observed | §1 commands and `boulder_tools.py` |
| Second header at `0x60F38` (ABDJ, multiboot client) | Observed | logo scan, header fields, crt0 at `0x020000C0` |
| No password UI/string/alphabet | Observed | `strings` counts, full menu walk |
| Hidden cheat screen text and layout | Observed | debugger-forced screenshot `11_hidden_cheat_screen_card_on.png` |
| Cheat screen is reached only from `0x08007A36` | Derived | BL scan; one hit |
| State 73 has only two writers, both `0xFF`-gated | Derived | disassembly of `0x080074EC`/`0x0800762E` and of both callees' epilogues |
| `0xFF` is never returned | Derived | complete return-site audit of `0x0802D440` and `0x0802E400` |
| Breakpoints at the screen/writers never hit in play | Observed | GDB log during the armed menu walk (title, main, EX, Story, pause, Options, Sound, Data Delete); other screens separately walked |
| `CARD_CHEAT` = `+0x3B2` | Observed | write `0x02018542=1` → screen shows `CARD_CHEAT ON`; card 1 unlocks |
| Six other flags' individual effects | Unknown | §8 |
| Sound test cycles 27 names | Observed | L/R on Sound Settings, names matched table |
| Stage/Level Select is progress-gated | Observed | only stage 1 / cave A available on a fresh save; Right ignored on locked slots |
| 49 cards, six "It's a secret." | Derived | pointer tables dumped and counted |

## 8. Unknowns

* The individual effects of `EXMODE_CHEAT`, `CLASSIC_CHEAT`, `CLEAR_CHEAT`,
  `TIME_CHEAT`, `EVENT_CHEAT` were not exercised. Writing `+0x3B0=1` and
  entering Story Mode did **not** open the other worlds or stages, so
  either the flag is applied only at a specific reload point or its meaning
  is narrower than the name suggests.
* The exact language encoding at `+0x3B3` is inferred from the four names;
  the screen wrote `1` there on exit in our run, which may be a side effect
  of the forced-entry path.
* Whether the Japanese retail build (the `ABDJ` multiboot image is only a
  link client) restored the cheat entry is unknown.
* `Sound Select` (BGM index 26) may be a placeholder rather than a track.
* The six secret card entries are enumerated, but their art was not extracted
  (only observed as "It's a secret." text behind the locked state).

## 9. Tooling

* `mgba` 0.10.5 SDL (`/usr/games/mgba`), `Xvfb :202`, `openbox`, `scrot`,
  `xdotool`, `gdb-multiarch` (mGBA `-g` stub).
* `binutils-arm-none-eabi` (`objdump -M force-thumb`), Python 3,
  `boulder_tools.py` in this folder (header scan, BL/pointer xrefs, state
  table, BGM/card table dumps, dead-entry audit).
* Screenshots: `screenshots/01_title.png` … `screenshots/13_data_delete.png`
  (raw 1024×768 window captures).

Reproduce the negative quickly:

```bash
python3 "roms/Boulder Dash EX/boulder_tools.py" \
        "roms/Boulder Dash EX/Boulder Dash EX.gba"
# expect: BL xrefs to 0x0801BBDC = ['0x8007a36'],
#         state 73 -> 0x8007a30,
#         return audit with no 0xFF,
#         secret cards [37, 38, 39, 40, 41, 45].
```

## 10. Legal note

No ROM, extracted graphics, music or game text is redistributed here. Only
hashes, addresses, our own screenshots and our own analysis code are
included.
