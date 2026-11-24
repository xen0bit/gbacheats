# Disney's The Little Mermaid: Magic in Two Kingdoms (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Disney's The Little Mermaid: Magic in Two Kingdoms.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `LITLEMERMAID` |
| Game code | `BN9E` |
| Maker code | `4Q` |
| Software version | `00` |
| Entry word | `0xEA00002E` (stock Nintendo/GCC crt0 branch, **not** patched) |
| Fixed byte `0xB2` | `0x96` |
| Complement check `0xBD` | `0x45` (matches computed value) |
| Header checksum `0xBE` | `0x0000` (normal artefact of a rebuilt header; complement byte is valid) |
| MD5 | `a05c86d8c5291049ebd22304ad9c2029` |
| SHA-1 | `c75a4fe95bd27baad3d800f6f8d66603a18ffadb` |
| SHA-256 | `34577d0635fff5e2e99f69cf6d6760354409d03e7144134315e7ca5f7fe2c344` |

Integrity checks:

* Exactly **one** GBA header/logo in the image (no embedded second image, no
  multiboot stub, no 2-in-1 shell).
* Entry code at `0x080000C0` is the stock SDK startup (`mov r0,#0x12; msr CPSR…`),
  not a cracktro. No appended trainer, no modified `0xEA00002E`.
* Save hardware: the SDK string `EEPROM_V124` sits at file `0x50DC4C`; mGBA
  creates a 512-byte `.sav` (4 kbit EEPROM). There is one save slot
  (`Overwrite This Game?` prompt), not a password save.

## 2. Executive summary

**This ROM has no in-game password, cheat code, button code, debug menu,
sound test, gallery or minigame-select screen.** It is a linear, chapter-based
action/adventure. The complete screen set is a 44-entry scene-class table; the
only non-gameplay screens are Title, Options, Language, Credits and the two
splash/legal screens, and every one of them was walked on `:341`.
Options contains exactly `Language`, `Credits`, `Back`; the pause menu contains
exactly `Continue`, `Save`, `Quit`. No screen contains a text-entry field, a
symbol grid, a code counter, or a hidden fourth entry.

The evidence is threefold:

1. **Text:** 98,881 ASCII strings (`strings -n 4`) and a multi-encoding literal
   scan (ASCII, case-folded, `+0x20` storage, UTF-16LE/BE) return **zero** hits
   for `password`, `passwd`, `cheat`, `debug`, `secret`, `unlock`, `extras`,
   `gallery`, `sound test`, `jukebox`, `level select`, `minigame`/`mini-game`
   and `code`. There is no password alphabet (`BCDFGHJKLMNPQRSTVWXYZ0123456789`
   and similar tables are absent).
2. **Structure:** the scene table at file `0x574` has 44 records
   (`{char* name, char* class_desc, void* ram_obj}`, 12 bytes each). Fifteen are
   engine/menu classes and 29 are the story chapters; there is no debug,
   password or minigame scene. The Title screen state machine
   (`0x08002C58–0x08002D1A`) handles exactly states 1/2/3, i.e. exactly three
   menu actions, and the pause is a fixed 3-item menu.
3. **Input:** there is **one** keypad poll (`0x0806376C`) writing
   `0x02000EB0` (pressed `+4`, held `+6`, released `+8`). A whole-ROM BL scan
   finds 46 call sites (39 × pressed accessor, 7 × triple accessor, 0 × held
   accessor, 0 × released accessor). None implements a multi-press sequence
   matcher: the gameplay handlers test only `START` (pause), `A`/`B` and the
   four directions; the menu framework (`0x0805EFA8`) forwards key state to
   per-item callbacks. A 14-sequence button battery at the title screen changed
   nothing; only `Start` in gameplay opens the pause menu.

The only published codes for this title are **CodeBreaker memory patches**
(3rd party cheat indexes: master code, "Access All Minigames", unlimited health and two
meter codes). They are device-level RAM writes, not in-game codes, and are
outside this report's scope; the game itself provides no field in which to
enter them. Consequently there is no valid code space to enumerate, no
validator to call as an oracle, and no novel code to mint: the deliverable is a
bounded negative with the complete menu/scene/input enumeration below.

## 3. How to reproduce

Emulator: mGBA SDL, Xvfb `:341`, `SDL_AUDIODRIVER=dummy`.

```
Xvfb :341 -screen 0 1024x768x24 &
DISPLAY=:341 openbox &
DISPLAY=:341 SDL_AUDIODRIVER=dummy mgba -3 "<rom>.gba" &
```

Default SDL keymap: `x`=A, `z`=B, `a`=L, `s`=R, `Return`=Start,
`BackSpace`=Select, arrows=D-pad. Hold keys 90–150 ms; menu bubbles animate,
so wait 0.5–1 s between presses.

Menu path (all walked):

1. Boot → **language select** (English / Français / Español / Italiano;
   `A` on English).
2. `LICENSED BY NINTENDO` → Disney / Buena Vista / **GORILLA** splash.
3. **Title**: `New Game`, `Continue`, `Options` (spatial navigation:
   `Right` steps New Game → Continue → Options; `Up` from Options → Continue).
4. `Options` → `Language`, `Credits`, `Back`; `Credits` = copyright screen
   ("The Little Mermaid: Magic in Two Kingdoms / Copyright 2006 Disney"),
   `A` returns.
5. `New Game` → long dialogue cutscene (press `A`; Start does **not** skip) →
   gameplay starts in chapter `ShipWreckA`.
6. `Start` in gameplay → **Pause**: `Continue`, `Save`, `Quit`.
   `Save` → `Save This Game?` `Yes`/`No`; `Yes` writes the 512-byte EEPROM save.
   `Quit` returns to the title.
7. Re-boot with the save present → `Continue` loads the save at `ShipWreckA`
   (observed). The save survives a title round-trip and a `Quit`.

Buttons/sequences tested (all at the title screen, each from a fresh savestate;
no screen or state change observed):

`Konami (U U D D L R L R)`, `D D U U`, `L L R R`, `R L R L`,
`Select ×3`, `Start+Select`, `L+R+Start`, `B+Select`, `Select` held 2 s,
`L+R` held 2 s, `Down ×6`, `Right ×6`, `B ×5`, `Start ×3`.
(Only sequences containing `A` can activate a menu item; those were not used
for the hidden-screen test.)

## 4. Address map

All addresses are ROM addresses (`file offset + 0x08000000`) unless noted.

### Input path

| Address | Meaning |
|---|---|
| `0x0806376C` | keypad poll: reads `KEYINPUT` (`0x04000130`), builds held/pressed/released |
| `0x08063790` | literal `0x04000130` |
| `0x080637AC` | literal `0x04000132` (`KEYCNT`) |
| `0x02000EB0` | key-state struct: `+0` unused, `+4` pressed, `+6` held, `+8` released, all u16 active-high (`~KEYINPUT & 0x3FF`) |
| `0x080637C0` | accessor: writes pressed/held/released into three caller pointers (7 call sites) |
| `0x080637DC` | accessor: returns pressed (39 call sites) |
| `0x080637E8` | accessor: returns held (**0 call sites — dead**) |
| `0x080637F4` | accessor: returns released (**0 call sites — dead**) |
| `0x0805EFA8` | UI/menu key dispatcher; calls `0x080637C0` at `0x0805EFF8`, then invokes each widget vtable with pressed/held/released |
| `0x0800AD84–0x0800ADC6` | gameplay handler: `pressed & 8` (START) → pause state 9 |
| `0x08019DEE` | second scene handler: same `START` pause test |
| `0x0801AC62`, `0x0801B89C`, `0x08023FF6`, `0x08027328` | per-scene movement/rhythm handlers (A/B/directions only) |

### Scene system

| Address | Meaning |
|---|---|
| file `0x574` | scene record table, 44 × 12 bytes: `{u32 name_ptr, u32 class_desc, u32 ram_obj}` |
| file `0x6950C` | scene-name string bank (`NpService`, `Keyboard`, … `BattleUrsula1`; `FinalSave` also present but is a save tag, not a 45th record — its would-be RAM field is code) |
| file `0x6999C–0x69B64` | class descriptors, 0x18 stride; a Thumb method pointer at descriptor `+0x0C` |
| `0x08000915–0x08000CAD` | scene method stubs (one per scene; e.g. Title `0x08000BA9`, Options `0x08000B95`, Language `0x08000B81`, Credits `0x08000B59`) |
| `0x08002D28` | Title scene factory/constructor |
| `0x08002C58–0x08002D1A` | Title selection state machine, states 1/2/3 only |
| `0x08004164` | Options scene factory |
| `0x08005D34` | Language scene factory |
| `0x08006998` | Credits scene factory |
| `0x08002970` | Splash scene |
| `0x08006E4C` | Cut/cutscene scene |

Title/Options/Language labels are **graphics**, not ASCII (the ASCII text bank
holds dialogue only); this is why a string search for "New Game" fails.

### Dead developer code (proven unreachable)

| Address | Content |
|---|---|
| `0x08040F3C` | map dumper, formats `--------- CURRENT MAP ------------` (`0x08245374`), `line %2.2d --`, `widthSize %d`, `tileSize %d` |
| `0x08040CCC` | map dumper, formats `--------- MAP ------------` (`0x082453D0`) |
| `0x08041078` | adjacent debug-print helper (only internal xref) |
| `0x08245648` | `GamePak loading %d bytes.` |

`0x08040F3C` and `0x08040CCC` have **no** BL callers in the 8 MiB image and **no**
literal pointer anywhere (searched both `addr` and `addr|1`), so they cannot be
entered from any scene or menu. They are leftover development logging, not a
debug screen.

### Save

| Address | Meaning |
|---|---|
| `0x50DC4C` | SDK `EEPROM_V124` tag (4 kbit EEPROM, 512-byte save) |
| `0x08000000`-relative EEPROM window `0x0D000000` | EEPROM bit-bang port |

## 5. Algorithm / pseudocode

There is no code validator. The only input-processing algorithms are the key
pipeline and the menu state machine; both are reproduced here so the negative
result is checkable.

```c
// one 60 Hz tick, 0x0806376C
u16 raw   = REG_KEYINPUT;             // 0x04000130, active low
u16 held  = (~raw) & 0x03FF;          // active high
u16 prev  = KS->held;                 // 0x02000EB0 + 6
u16 delta = held ^ prev;
KS->pressed  = held & delta;          // +4
KS->released = delta & prev;          // +8
KS->held     = held;                  // +6
```

Button masks: `A=0x001, B=0x002, SELECT=0x004, START=0x008, RIGHT=0x010,
LEFT=0x020, UP=0x040, DOWN=0x080, R=0x100, L=0x200`.

```c
// Title selection (0x08002C58), obj+0x124 holds the chosen action
switch (obj->action) {
  case 1: if (obj->flag_0x11c) { obj->action = 0; }      // New Game path
          break;
  case 2: if (obj->flag_0x11c) create("Bvg");            // transition helper
          break;
  case 3: if (obj->flag_0x11c) create("Options");
          break;
}
```

No counter, no expected-mask array, no per-frame comparison against a stored
sequence exists in this function or in any of the 46 input-accessor call sites.

## 6. Tables

### 6.1 Scene classes (44 records, file `0x574`)

System/menu (15): `NpService`, `Keyboard`, `Scene`, `Cycle`, `GamePak`,
`Screen`, `Main`, `Legal`, `Bvg`, `Splash`, `Title`, `Options`, `Language`,
`Cut`, `Credits`.

Story chapters (29): `ShipWreckA`, `ShipWreck2`, `PuzzleBox`, `RescueEricA`,
`RescueEric1`–`RescueEric5`, `UTSARB`, `UTS1RB`–`UTS3RB`, `FJA`, `FJ1`–`FJ3`,
`ChefEscapeA`, `ChefEscape1`–`ChefEscape3`, `KissTheGirlA`,
`KissTheGirl1`–`KissTheGirl3`, `BreakCharm1`–`BreakCharm3`, `BattleUrsula1`.

`FinalSave` at file `0x696C0` is a save tag string, not a scene record. There is
no `Debug`, `Password`, `Sound`, `Gallery`, `Extras` or minigame-select class.

### 6.2 Menu action space (all reachable actions)

| Screen | Entries | Actions |
|---|---|---|
| Language (boot) | 4 visible labels; **5** buttons constructed with language IDs 4–8 | set language |
| Title | 3 | New Game, Continue, Options |
| Options | 3 | Language, Credits, Back |
| Pause | 3 | Continue, Save, Quit |
| Save confirm | 2 | Yes, No |
| Credits | 0 | `A` returns |

The Language factory (`0x08005D34`) calls the button constructor (`0x080037E4`)
with IDs 4,5,6,7,8 — five slots — while the boot layout shows four labels
(English, Français, Español, Italiano). German dialogue text is present
(`0x64C…–0x65F…`) but two development placeholders `Need German Translation`
sit at file `0x64CAE5` and `0x64F175`; no German label was observed.
**Inferred:** the fifth (German) slot is a disabled/cut entry, not a hidden
cheat.

### 6.3 Search-space counts

| Space | Count |
|---|---|
| Whole ROM bytes scanned for literals | 8,388,608 |
| ASCII strings (n ≥ 4) | 98,881 |
| Uppercase A–Z runs (font/UI tables) | 117 |
| `BCDFGHJKLMNPQRSTVWXYZ0123456789`-style password alphabet | 0 |
| UTF-16LE/BE occurrences of `password/cheat/debug/secret/unlock/code` | 0 |
| Scenes | 44 |
| Input-accessor call sites | 46 (39 pressed, 7 triple, 0 held, 0 released) |
| Code-sequence tables / expected-mask arrays | 0 |
| Published in-game codes | 0 |

## 6b. Enumeration

**Space definition.** The game exposes no code/password input surface, so the
code space is empty:

* alphabet(s): none (no symbol grid, no keyboard text field, no name field);
* length(s): none;
* field widths / checksum: none;
* table size: 0 entries.

The enumerable space is therefore the *menu action space*:

| Class | Number | Proof |
|---|---|---|
| Scene classes | 44 | 44 valid 12-byte records at `0x574`; 45th would-be record is code |
| Content chapters | 29 | table above |
| Menu screens | 5 | Title, Options, Language, Pause, Save-confirm |
| Menu actions | 16 | 5 (Language) + 3 + 3 + 3 + 2 |
| Hidden/unpublished actions | 0 | state machine `0x08002C58` handles 1/2/3 only; no counter/array in 46 input sites |

**Validator model.** Not applicable: no function reads a user-entered string.
The only `strcmp`-style consumers are the dialogue/script parser and the menu
callback dispatch; neither consumes a typed code.

**Novel code(s).** None possible. Because there is no encoder, decoder,
table or input field, no value can be "accepted" by the game. The closest
published material, CodeBreaker code `72251668D461` ("Access All Minigames"),
is an encrypted RAM patch applied by a cheat device; it is not a ROM literal
(searched) and cannot be entered on any screen. Using it was out of scope.

**Bounds proven by rejection.** Fourteen controller sequences (listed in §3)
were pressed at the title screen from a fresh savestate each time; every frame
remained the title layout (mean pixel intensity 12.0–12.3 k; gameplay measures
≈30.5 k) and no new label or screen appeared. Out-of-menu inputs are inert:
pressing `Down` at title does not move the selection to Continue (layout is
spatial), pressing `B` or `Select` does nothing, and `Start` is ignored on the
title screen. The menu code accepts only its enumerated items because the
action variable is compared against 1/2/3 and all other values fall through to
no-op.

## 7. Validation evidence

**Observed (emulator, `:341`)**

* Language select at boot: English/Français/Español/Italiano; `A` on English.
* Licensed-by-Nintendo, Disney/Buena Vista and Gorilla splash screens.
* Title with three bubbles; spatial navigation between them; New Game starts
  the dialogue cutscene and then `ShipWreckA` gameplay.
* Options: Language/Credits/Back. Credits screen text verified verbatim.
* Pause: Continue/Save/Quit. Save → `Save This Game?` Yes/No; Yes writes a
  512-byte `rom.sav`; Quit → title; Continue → loads the save at `ShipWreckA`.
* `Start` (Return) does not skip the intro cutscene; `A` advances it.
* 14-sequence button battery: no state change.

**Derived (static)**

* 44-entry scene table and per-scene Thumb method stubs.
* Single keypad poll and the 46 accessor call sites; held/released accessors
  have zero callers.
* Title state machine has exactly three action states.
* Debug map dumpers have zero callers and zero literal pointers.
* Zero keyword hits in all tested encodings; no password alphabet.
* `EEPROM_V124` and 512-byte save.

**Inferred**

* The fifth Language slot is German, disabled/cut (four labels visible, five
  constructed, German text exists, "Need German Translation" placeholders).
* CodeBreaker codes are the only published codes because no in-game code
  surface exists; this matches the complete absence of code strings/tables.

## 8. Unknowns

* The CodeBreaker "Access All Minigames" code was **not** decrypted (its
  multi-line master/seed format is device-level); it is presumed to patch a
  chapter/progress word. No in-game route to that state was found.
* The five Language slots were enumerated statically; the disabled slot was not
  driven to a visible confirmation because the boot layout exposes only four
  labels.
* The 29 story chapters were enumerated from the scene table and the first was
  played; they were not each completed, because the question (cheat surface)
  is settled by the menu and input enumeration.

## 9. Tooling / files

* Work directory: `/tmp/littlemermaid`.
* `p0.py` — header/hash/embedded-header check.
* `scenes.py`, `parse_scene.py` — scene table and class-descriptor parser.
* `blscan.py`, `inputcallers.py`, `dumpcallers.py` — BL/literal scans of the
  input accessors and their callers.
* `statecheck.py`, `decomp.py` — mGBA `.ss*` (PNG `gbAs` chunk) decompressor and
  RAM reader (`IWRAM @ 0x19000`, `EWRAM @ 0x21000`).
* `battery2.sh`, `k.sh` — deterministic key injection and sequence battery.
* Screenshots kept in the work directory (`t0`, `g2`, `g3`, `x6`, `g8`, `gj`,
  `gk`, `gm`, `r8`): language select, splash, title, options, credits,
  gameplay, pause, save-confirm, title re-check.

No ROM, graphics, music or text extracted from the game is redistributed here.

**Legal note:** analysis performed on a locally owned image; no game assets are
included in this report.
