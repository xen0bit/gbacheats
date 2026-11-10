# Cabela's Big Game Hunter 2005 Adventures (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Cabela's Big Game Hunter 2005 Adventures.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `CABELA'S BIG` (0x0A0, space padded) |
| Game code | `BG5E` (0x0AC) |
| Maker code | `52` (0x0B0) |
| Software version | `0x00` (0x0BC) |
| Entry word | `0xEA000030` — stock ARM branch to `0x080000C0` |
| Logo | intact at 0x004, single GBA-logo hit in the file |
| MD5 | `d569ea9204f4683592ed49e47f6f9568` |
| SHA-1 | `aff3c5bc948c2c868be7da8a327aee25beaa027c` |
| SHA-256 | `118afa69c0ccf98a3cc62e67bad5d94593bcb2ed8b16f7477f8ba6ec5c6ae2ac` |

**Header/patch note.** The complement byte at 0x0BD holds `0xE3` and the header
checksum at 0x0BE holds `0x0000`. Computed values for the untouched header are
complement `0x1D` and checksum `0x00E3`. The entry word, logo, title, code and
maker are stock, and the file contains no cracktro/trainer strings
(`SUNHORS`, `Mode7`, `CRC BANDIT`, trainer menus: 0 hits), so this is the
rebuilt-header artifact described in guide §16.1, not a patched game.
No trainer is present and no stock branch needed restoring.

## 2. Executive summary

**This build has no reachable in-game cheat, password, or debug-menu system,
and no in-game code space at all.** The Torus engine linked into the ROM still
contains a class literally named `CheatMenuState`, which is why a text scan
looks promising, but that class is a leftover stub and nothing reachable in
this build instantiates it (the only path is a value that no input produces).

Evidence chain (details in §4–§6b):

1. `CheatMenuState` is one record of the engine's class/RTTI table at
   `0x0804C4A0`–`0x0804D2F8`. Its three virtual methods are `0x0801FEB8`,
   `0x0802000C`, `0x0801FEBC`. The first two are literally `bx lr` stubs; the
   third is the generic inherited text-layer update. The class defines **no
   menu entries, no labels, and no actions**.
2. The only code that selects that class is the state-transition dispatcher
   `0x0801F1AC` (the title-screen update). When its request byte
   `[state+0x84] == 1` it installs the `CheatMenuState` vtable, writes the class
   pointer `0x0804C59C` and calls the stub init. The request byte is produced by
   the 3-way title callback `0x0801F5A8`, which maps `0 -> CreditsScreenState`,
   `1 -> MainMenuState`, `2 -> CheatMenuState`.
3. At the title screen only two UI action elements exist (values `0` and `1`,
   enumerated from an EWRAM savestate): `A` sends `0`, `Start` sends `1`.
   `B`, `Select`, `L`, `R` and the four directions send nothing. No input sends
   `2`; a live breakpoint on the value-2 branch (`0x0801F5D2`) never fires
   across the entire game walk.
4. There is no second code surface: no password/keypad validation, no
   button-sequence table, no hidden menu. The on-screen letter grid is the
   **profile-name entry** (5 characters, accepts anything, stored in the save
   slot), not a code field.
5. No GBA cheat/password list exists publicly for this SKU. The widely published
   `bgh_*` / `ai_drawmap` codes are the PC console commands and are absent from
   the GBA image under every encoding checked. The sibling Torus GBA title
   *Pitfall: The Lost Expedition* does publish a title-screen code
   (`B, A, Down, Left, A, Down`); the mask sequence is present in that ROM
   (0xB60F6) and **absent** from this ROM, and entering it here has no effect.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba -3`), Xvfb `:223`, openbox,
`SDL_AUDIODRIVER=dummy`. Keymap used: `x`=A, `z`=B, `Return`=Start,
`BackSpace`=Select, `a`=L, `s`=R, arrows=D-pad.

Exact menu path walked (each screen also reached and photographed):

```
license/copyright ("LICENSED BY NINTENDO")
  A -> Torus Games logo -> Activision logo -> title
title ("PRESS START")
  A     -> CREDITS (scrolls, exits with any key)
  Start -> New/Select profile
New/Select profile
  A on empty slot -> 5-character name keypad -> "Accept profile?" -> Yes
  A on used slot  -> "Load profile" -> A=Yes / B=No
  -> Select Game
Select Game: Quick Hunt / Career Hunt / Log Cabin
  Quick Hunt / Career Hunt -> Location select
Location select: Alaska (open), Colorado, Pennsylvania, Texas, Wisconsin
  (locked ones show a padlock and reject A)
  A on Alaska -> area map ("ALASKA", Log Cabin, "Outfitter: BlackBear")
  A on Log Cabin -> Inventory (12 Gauge Pump Shotgun; one weapon only)
  A -> top-down hunt
  Start -> pause: Resume Game / Quit / Return to Log Cabin / Sound
      Quit -> "Yes / No" confirmation
      Return to Log Cabin -> Inventory
Log Cabin (from Select Game) -> Trophy Room: "No Trophies", only B Back
```

Inputs exercised on every menu (with the value-2 gate breakpoint armed):
`A`, `B`, `Start`, `Select`, `L`, `R`, `Up`, `Down`, `Left`, `Right`, and the
combinations `A+Select`, `Start+Select`, `A+L`, `Start+L`, `A+R`, `Start+R`,
`B+Start`, `A+B`, `L+R`.

Sequences explicitly tried on the title, on Select Game, in the pause menu and
in gameplay, with no effect and no gate hit:

* `B, A, Down, Left, A, Down` (the published Pitfall GBA code)
* `Up, Up, Down, Down, Left, Right, Left, Right, B, A`
* `L, R, L, R, Select, Start`
* `Select, Start, Select, Start`
* `B, A, B, A, Down, Down`

Published codes checked: there are **no published GBA codes** for this title.
The PC codes (`bgh_animalfreeze`, `bgh_needMoney`, `bgh_unlockLevels`,
`ai_drawmap`) are console commands in the PC build; literal search for
`bgh_`, `ai_drawmap`, `needMoney`, `unlockLevels`, `animalfreeze` in this ROM:
0 hits. The PS2/GC/Xbox Action Replay/CodeBreaker lists are memory patches on
other SKUs and out of scope.

## 4. Address map

ROM base is `0x08000000`; file offset + `0x08000000` = ROM address.

| Address | Meaning |
|---|---|
| 0x080000C0 | stock crt0 entry |
| 0x08000760 | dead "Pitfall Debug Screen" printer; 0 BL callers, 0 pointer refs |
| 0x0801F17C | `TitleScreenState` enter (`bx`-style init: alloc 0xA4, attach UI text) |
| 0x0801F1AC | `TitleScreenState` per-frame update, **state-transition dispatcher** |
| 0x0801F258–0x0801F276 | dispatcher case 1: copy `CheatMenuState` vtable from 0x0804C584/C8C/C94 |
| 0x0801F28C/0x0801F28E | load literal `0x0804C59C`; store class pointer to `[state+0x80]` |
| 0x0801F2F2 | `bl 0x0801FEB8` — call `CheatMenuState` enter (stub) |
| 0x0801F3E0–0x0801F44E | dispatcher case 2: `MainMenuState` (class 0x0804C520) |
| 0x0801F4E8–0x0801F59C | dispatcher case 3: `CreditsScreenState` (class 0x0804C5C4) |
| 0x0801F5A8 | 3-way title callback: 0→state 3, 1→state 2, 2→state 1 |
| 0x0801FEB8 | `CheatMenuState` enter: `bx lr` (`0x4770`) |
| 0x0801FEBC | `CheatMenuState` update: generic text-layer update |
| 0x0802000C | `CheatMenuState` second method: `bx lr` (`0x4770`) |
| 0x0804C584 | `CheatMenuState` vtable slot 1 (`0x0801FEB9`) |
| 0x0804C58C | `CheatMenuState` vtable slot 2 (`0x0802000D`) |
| 0x0804C594 | `CheatMenuState` vtable slot 3 (`0x0801FEBD`) |
| 0x0804C59C | ASCII `"CheatMenuState"` (class name) |
| 0x0804C4A0 | ASCII `"TitleScreenState"` start of the state-class table |
| 0x083E0A68 | only pointer to the 3-way callback (`0x0801F5A9`) in the image |
| 0x0300008E | engine held-key word (active high, `~KEYINPUT & 0x3FF`) |
| 0x03000090 | engine newly-pressed word |
| 0x03000E48 | front-end state-object pointer |
| 0x02006B18 / 0x02006C24 | the two title UI action elements (values 0 and 1) |

Engine key masks (active high): A=1, B=2, Select=4, Start=8, Right=0x10,
Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200.

## 5. Algorithm / pseudocode

### 5.1 Class table layout

The engine's class/RTTI records are not name-first: each record is three
virtual-method groups followed by the NUL-terminated class name (runtime
confirmation: the live `TitleScreenState` object had class pointer
`0x0804C4A0` and executed method `0x0801F1AC`, which is the third group located
immediately **before** that string).

```
struct Class {
    u32 pad; u32 tag=0xFFFF; u32 fn_a;   // three virtual methods
    u32 pad; u32 tag=0xFFFF; u32 fn_b;
    u32 pad; u32 tag=0xFFFF; u32 fn_c;
    char name[];                          // padded to 4, NUL terminated
};
```

`CheatMenuState` therefore owns `0x0801FEB8` / `0x0802000C` / `0x0801FEBC`
(`fn_a`/`fn_b` are `bx lr`).

### 5.2 State transition (title)

```
on_title_button(event):
    switch (event & 0xFF) {
      case 0: next_state = 3;   // CreditsScreenState
      case 1: next_state = 2;   // MainMenuState (profile / front end)
      case 2: next_state = 1;   // CheatMenuState
      default: next_state = 2;
    }
    state->request = next_state;

state_update_TitleScreen(state):
    if (state->request == 1) install(CheatMenuState);   // 0x0801F1AC case 1
    if (state->request == 2) install(MainMenuState);
    if (state->request == 3) install(CreditsScreenState);
```

`install(CheatMenuState)` copies the vtable from `0x0804C584/C58C/C594`, marks
the state phase and calls `0x0801FEB8`, which is `bx lr`.

### 5.3 Why no code can produce event 2

The front-end builds exactly two UI action elements for the title (values 0 and
1) from the UI layout; both are enumerated in EWRAM in a title savestate:

```
element A: vtable 0x02003F6C, +0xA0 = 0  -> A press
element B: vtable 0x020007F8, +0xA0 = 1  -> Start press
```

The callback is a *front-end action-table* entry (`{0xFFC8, 0x0801F5A9}` at
`0x02001748` in EWRAM, copied from ROM `0x083E0A40`). The action is referenced
by exactly one place in the image (`0x083E0A68`). No element with value 2 is
created, and no input is wired to one.

## 6. Tables

### 6.1 Relevant class records (methods precede the name)

| Name (ROM address) | fn_a | fn_b | fn_c |
|---|---|---|---|
| `"LicenseState"` 0x0804C478 | 0x0801D935 | 0x0801DAC1 | 0x0801D96D |
| `"TitleScreenState"` 0x0804C4A0 | 0x0801F17D | 0x0801F5A5 | 0x0801F1AD |
| `"MainMenuState"` 0x0804C520 | 0x0801DB15 | 0x0801DF41 | 0x0801DB4D |
| `"LevelSelectState"` 0x0804C548 | 0x0801EE0D | 0x0801F15D | 0x0801EE7D |
| `"CheatMenuState"` 0x0804C59C | **0x0801FEB9** | **0x0802000D** | **0x0801FEBD** |
| `"CreditsScreenState"` 0x0804C5C4 | 0x0801EC7D | 0x0801EE01 | 0x0801ECAD |
| `"TrophyRoomState"` 0x0804C5F0 | 0x0801E339 | 0x0801E77D | 0x0801E37D |

The `TitleScreenState` split and the `CheatMenuState` split were confirmed at
runtime (class pointer plus executing method) and by the descriptor pointers at
`0x0804C584/0x0804C58C/0x0804C594` respectively.

`CheatMenuState` fn_a (`0x0801FEB8`) and fn_b (`0x0802000C`) are `0x4770`
(`bx lr`); fn_c (`0x0801FEBC`) is the shared text-layer update.

### 6.2 The only "cheat"-named strings in the whole 4 MiB

All 19 key-word hits from `strings -n 4` are engine/class identifiers, not
user-facing text:

```
0x04AAD8 Pitfall Debug Screen     0x04B3AC UI_CheatFlagsObserver
0x04B1A0 LevelCompleteAction      0x04C250 UICheatFlagsObserver
0x04B1B4 LevelFailedAction        0x04C2A4 UILevelObserver
0x04B244 MakeLevelSafeAction      0x04C4FC LevelState
0x04B324 UI_CurrentLevel_...      0x04C548 LevelSelectState
0x04C59C CheatMenuState           0x04C6AC LevelFailedAction
0x100AAD DebugBarGraph            0x1010DA UI_CheatFlagsObserver
0x100ABB DebugPoint               0x1010F0 UI_CurrentLevel_...
0x100DE8 LevelCompleteAction      0x1010E4 ...
0x100DFC LevelFailedAction
0x100E0E MakeLevelSafeAction
```

`UI_CheatFlagsObserver` is registered in the script-visible widget table at
`0x0804B640`; no script or data in the image references it (only its registry
entry and its RTTI name string exist).

## 6b. Enumeration

**Space definition.** The only gate in the ROM that can enter the class named
`CheatMenuState` is one 2-bit selector value, produced by the title callback
`0x0801F5A8`. Its complete input domain is `{0,1,2,other}`; `0` and `1` are
reachable from two title UI elements (A and Start), `other` is treated as `1`.
The gate therefore has **3 effective values**; value `2` is the only path to
`CheatMenuState`. The target has **no payload**: its enter methods are `bx lr`,
so even the value-2 state would render only the inherited empty text layer —
there is no cheat list, no toggles, and no flag writes to enumerate.

**What was exhausted.**

| Search space | Count | Result |
|---|---|---|
| All front-end and in-game screens | 17 distinct screens/overlays (list in §3) | all reached and walked |
| Single inputs at title | 10 (A, B, Start, Select, L, R, 4 dirs) | only A (`0`) and Start (`1`) reach the callback |
| Modifier combinations at title | 6 (`A/Start` × `Select/L/R`) | no callback; no value 2 |
| Multi-press sequences | 5 sequences × 4 screens = 20 trials | no callback; no value 2 |
| Title UI action elements (EWRAM) | 2 (`+0xA0` = 0 and 1) | no element with value 2 exists |
| Live breakpoint on value-2 branch (`0x0801F5D2`) | whole walk | never hit |
| `u16` key-mask runs (≥4) in the whole ROM | 14 runs | all inside graphics/stat data or false positives; no sequence table |
| Pitfall-style `00 00 <masks> FF FF` script records | 3 hits (`0x359E88`, `0x378CE2`, `0x3C9394`) | each is `R,A,A`, not a code table |
| Literal Pitfall sequence `B,A,Down,Left,A,Down` (u8/u16, raw and inverted) | 4 encodings | 0 hits in this ROM (present once in Pitfall GBA at `0xB60F6`) |
| Password/cheat/debug/unlock strings (`strings -n 4`) | 34,815 strings scanned, 19 keyword hits | all are engine class names; no UI/validator text |
| Published GBA code lists | web search (GameFAQs, chaptercheats, Neoseeker, GameHacking, TCRF) | none exist for the GBA SKU |
| PC code literals in ROM | 5 strings, 4 encodings | 0 hits |
| Cheat class method references | 3 methods | only inside the class descriptor; 0 BL, 0 pointer tables |
| "Pitfall Debug Screen" renderer `0x08000760` | — | 0 BL callers, 0 pointer refs (dead engine debug screen) |

**Bounds proven by rejection (in-game).** The value-2 path was rejected by
construction at every tested point: the game boots to the title, A opens
Credits, Start opens the profile/front-end, and the value-2 branch breakpoint
never fires. The out-of-domain values are not expressible from the input
surface; the strongest rejection test is the literal Pitfall code
`B, A, Down, Left, A, Down`, which leaves "PRESS START" unchanged (no colour
change, no transition) and does not touch `0x0801F5A8`/`0x0801F5D2`.

**Novel code.** None can be minted: there is no input alphabet, no length
field, no checksum, no table, and no validator. The engagement therefore lands
in guide §16.3 category 2 (**dead code**): the handler (an empty stub) exists,
but the transition into it cannot be reached from any menu, and the state
contains no content to unlock. This is a proven negative for *this* space, not
an untested one.

## 7. Validation evidence

**Observed**

* Boot sequence and all 12 screens/overlays reached in mGBA on `:223`.
* `A` at the title produced a callback hit with `r1=0` and then the CREDITS
  screen; `Start` produced `r1=1` and the profile screen.
* `B`, `Select`, `L`, `R`, directions and the six modifier combinations
  produced no callback hit at the same breakpoint.
* Live breakpoint at `0x0801F5D2` (the `event==2` branch) never fired during the
  full walk.
* EWRAM savestate of the title screen contains exactly two UI action elements
  with `+0xA0` values 0 and 1.
* `CheatMenuState` enter (`0x0801FEB8`) and second method (`0x0802000C`) are
  `bx lr`.
* The published Pitfall GBA sequence is a no-op on this title screen.

**Derived**

* Class records are methods-then-name; this follows from the live object whose
  class pointer was `0x0804C4A0` and whose executing method was `0x0801F1AC`
  (the group immediately preceding that string).
* The 3-way callback's mapping `0→3, 1→2, 2→1` follows from the branch chain at
  `0x0801F5A8`–`0x0801F5DA` and is confirmed by the observed A/Start behaviour.
* `CheatMenuState` has no payload because both non-generic methods are stubs.

**Inferred**

* The `CheatMenuState`/`UI_CheatFlagsObserver` names are inherited from a
  Torus engine template also used by `Pitfall: The Lost Expedition` (GBA); the
  neighbouring title-screen code and the identical 3-state front-end layout
  support this, but only the class labels and code shape are evidence.

## 8. Unknowns

* Whether the retail *engineering* build (pre-master) had a third title UI
  element wired to value 2. No such element exists in this image; only the
  class stub survives.
* Script bytes inside the compressed DPAK chunks were not decompressed, so a
  *scripted* call to action id `0xFFC8` with value 2 in an unexercised script
  is not formally excluded. Counter-evidence: the action is referenced from
  exactly one table entry in the image, the title UI creates exactly two
  elements, and the value-2 branch never fires across all reachable modes.
* The two compressed DPAK chunks were not decoded; they contain graphics/audio
  by their size and entropy, and no ASCII or mask-sequence hits occur in them.

## 9. Tooling

* mGBA 0.10.5 SDL under Xvfb `:223` + openbox, `SDL_AUDIODRIVER=dummy`,
  `xdotool`/`scrot` for reproducible input and screenshots.
* `arm-none-eabi-objdump -M force-thumb` / `-M force-arm`.
* Python 3 + Capstone 5.0.7 for raw-memory scanning (pointer scans, BL-target
  scans, key-mask run scans, class-record parsing).
* mGBA savestates (`gbAs` PNG chunk → zlib → EWRAM slice at state offset
  `0x21000`) for EWRAM enumeration.
* A pty wrapper around mGBA's `-d` CLI debugger (`SIGINT` to halt, breakpoints
  and memory reads over a Unix socket).
* REA/Ghidra 12.1.4 was opened for identity/xref cross-checks; the raw Thumb
  function coverage was incomplete, so all claims above were verified with
  manual disassembly and the live debugger.

## 10. Legal note

No ROM, extracted graphics, audio, or copyrighted text is redistributed here.
All quoted strings are short engine identifiers required as evidence. The ROM
hash identifies the exact revision analysed.
