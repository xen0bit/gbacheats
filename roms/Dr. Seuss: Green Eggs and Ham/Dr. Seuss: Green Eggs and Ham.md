# Dr. Seuss: Green Eggs and Ham (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dr. Seuss: Green Eggs and Ham.gba` (4,194,304 bytes / 4 MiB) |
| Header title | `GREENEGGSHAM` |
| Game code / maker | `BUSE` / `5L` (NewKidCo / Handheld Games, LLC), `file(1)` reports `(BUSE5L, Rev.00)` |
| Version / fixed byte | `0x00` / `0x96` |
| Entry word | `0xEA00002E` — stock `b 0xC0`, **no cracktro/trainer patch** |
| Header checksum | `0x0000`, complement byte `0x34` (rebuilt-header artifact; §16.1) |
| Embedded GBA headers | **1** (Nintendo-logo scan at file `0x0` only) — not a multi-game pack |
| MD5 | `ebc7077768e9fc856480a80cb6be5b2c` |
| SHA-1 | `be062fa28db26ec37ec96e5a7e6dc77cf4ad6907` |
| SHA-256 | `47d822b098cf1808abf6c1bbf3c912f5ea543e7bd29e973e60f09da7f23efd62` |
| Save hardware | 512-byte EEPROM (mGBA created a 512-byte `.sav`) |

## 2. Executive summary

**There is no in-game password, button-code, or cheat system in this ROM.** No published code
exists for the title (3rd party cheat indexes all report *zero* cheats; no
3rd party cheat index cheat page), no password/cheat/code/secret/debug keyword occurs anywhere in the
4 MiB image (literal counts all 0), no key-mask sequence table exists, and no validator or
accepted-code table exists. The only text-entry field is a player **name** field, which has no
comparison consumer.

The game does contain developer test material, and one genuinely hidden screen:

1. **Game Options → Sound Test / Music Test** (reachable normally): value cyclers that
   preview sound IDs (`Horn`, `Tick`, …) and music IDs (`Gameboard`, `Intro`, `Action`,
   `Memory`, `Map Theme`). *(Observed)*
2. **A complete but unreachable "Level Select" debug screen** ("Select a level to view!",
   `Level:`, `Next`, `Back`, 40 selectable entries, selector range 2–41). Its init/update
   handlers and its starter function are all present, but the starter at `0x08005D20` has
   **zero** callers or function-pointer references in the image and is omitted from the
   screen dispatcher at `0x080004F8`. It cannot be entered by any controller input. Forcing
   the starter from mGBA's debugger displays the screen and its A button launches a level
   view. This is §16.3 case **2 (dead code)**, not a gated or cut feature. *(Observed +
   Derived)*

**Sibling comparison:** *Dr. Seuss' The Cat in the Hat* (GBA) is a **different game/engine**:
game code `AQTE7D` vs `BUSE5L`, and none of the debug/UI strings listed above
(`Level Select`, `Game Options`, `Sound Test`, `Music Test`, `Level_GameboardSequence`,
`Handheld Games LLC`) occur in its image. **Nothing is shared.** *(Observed)*

## 3. How to reproduce

* Emulator: `mgba -3` under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, default SDL keymap
  (A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows). Hold keys
  ~150 ms.
* Title → press A through legal text/"Presents"/logo (~6 s) → `Press Start` → Start.
* **Main Menu** (`0x080CA280`): `Start Game` / `Options` / `Credits`.
  `Options` → **Game Options**: `Sound Test`, `Music Test`, `Music`, `Sound`, `Clear Save`;
  Left/Right cycles the value, A confirms, B returns.
* `Start Game` → `Select Number of Human Players` (1–4) → `Select Number of CPU Players`
  (1–3) → `Choose a player` (Boy/Girl) → `Choose a hat` → `Enter your Name` → game board.
* Game board → dismiss dialogue with A, press A to spin; the spinner selects a mini-game
  (e.g. **Mix-up Match** reached and screenshotted). Start on the board and inside Mix-up
  Match produced **no visible pause overlay** in repeated tests; the strings `PAUSED`
  (`0x080CB524`), `Paused` (`0x080CB53C`), `Score:` and `Lives:` are present in the text
  bank and are rendered through text IDs, so a pause path exists in code but was not
  reached by Start in the screens exercised. *(Observed negative result)*
* **Force the hidden screen** (mGBA CLI debugger via PTY, `mgba -d -3`):
  1. `b/t 0x08059790` (input handler, hit each frame), `c`; let the game reach any menu.
  2. At the halt note `r13` (sp). Execute `w/4 <sp> 0x08059791` (craft return address),
     `w/r pc 0x08005D20`, `c`.
  3. `d 1`, `c`, wait ~1 s. The `Level Select` screen renders (verified by screenshot).
     A = `Next` (launches the highlighted level view), B = `Back`.

## 4. Address map

| Address (ROM unless noted) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Header / stock entry `0xEA00002E` | Derived |
| `0x08059798` | Reads `KEYINPUT` `0x04000130`, stores active-high mask | Derived |
| `0x030008AC` (RAM) | Current held-key mask (active-high: A=1,B=2,Select=4,Start=8,R=0x10,L=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200 — engine uses a custom order) | Derived |
| `0x0805986C` | `KeyPressed(mask)` helper: `held & mask && !(prev & mask)` | Derived |
| `0x08004F8` | Screen dispatcher: compares a global function pointer against known starter addresses and installs handler pairs | Derived |
| `0x08005D20` | **Dead** "start Level Select" function: stores `0x08012DE5`/`0x08012EA5` into struct `0x03002B00` (`+4`/`+8`), then `bl 0x08050C9C` | Derived |
| `0x08012DE4` / `0x08012EA4` | Level Select init / update handlers | Derived |
| `0x03004D50` (RAM) | Level Select selector (valid 2–41) | Derived |
| `0x030051D8` (RAM) | English/Spanish localization table (8-byte records); index 111 = `Level Select` at `0x03005550` | Observed (RAM dump) |
| `0x080CAD9C`, `0x080CADAC`, `0x080CADC4`, `0x080CADCC` | `Level Select`, `Select a level to view!`, `Level:`, `Next` | Observed |
| `0x080CAE28`, `0x080CAE38`, `0x080CAE44`, `0x080CAE8C` | `Game Options`, `Sound Test`, `Music Test`, `Clear Save` | Observed |
| `0x080C97BC`, `0x080C99A8` | `Game Board`, `Level_GameboardSequence` (internal sequence names) | Observed |
| `0x080CB524`, `0x080CB53C`, `0x080CB52C`, `0x080CB534` | `PAUSED`, `Paused`, `Score:`, `Lives:` | Observed |

## 5. Algorithm

No validator exists, so there is no password algorithm to reimplement. The relevant
dynamic behaviour is the hidden screen's input logic (Thumb, `0x08012EA4`):

```
selector = [0x03004D50]
if KeyPressed(0x20): selector -= 1        # Left
if KeyPressed(0x10): selector += 1        # Right
if selector <= 1: selector = 41
if selector > 41: selector = 2            # => valid domain 2..41, wraps
if KeyPressed(0x01):                      # A / "Next"
    if selector == 28: call 0x0801BA70    # special action
    install level-view handlers and enter selected level
if KeyPressed(0x02):                      # B / "Back"
    exit screen
```

Screen setup (`0x08012DE4`) reads the localization index at `0x03005AFC`, indexes the
tables at `0x03005550` ("Level Select"), `0x03005558` ("Select a level to view!"),
`0x030055E0`, `0x030055E8`, `0x030055F0`, and installs the menu via `0x08053420`.

## 6. Tables

* **String bank / localization table**: 8-byte records `{English_ptr, Spanish_ptr}` built in
  IWRAM at `0x030051D8` (mirror of ROM `0x08360FD8`). All UI strings used by the game are
  in this table; only the table entries hold pointers to strings such as `Level Select`.
* **Hidden-screen selector**: domain `2..41` (40 entries), wrapping. Entry `28` has a
  dedicated A-button action.
* **Sound Test values** (ROM pool, observed in Options): `Horn`, `Tick`, `Tock`, `Cokoo`,
  `Slide`, `Pop`, `Tunk`, `Whip`, `Buzzer`, `Boat Horn`, `Register`, `Door Bell`,
  `Fog Horn`, `Jump`, `Train`, `Train Bell`, `Down`, `Clang`, `Ding 1`, `Ding 2`.
* **Music Test values**: `Gameboard`, `Intro`, `Action`, `Memory`, `Map Theme`.
* **No accepted-code table, alphabet, checksum, key-mask table, or flag word for a cheat
  exists.**

## 6b. Enumeration

**Code space size: 0.** There is no password field, no button sequence, and no debug gate
driven by input, so no code can be minted — the §0.2 "generate a novel code" deliverable is
not applicable and is replaced by the bounded negative proofs below.

**Published codes tested:** none exist. 3rd party cheat indexes ("we currently don't have any …
cheats"), 3rd party cheat indexes ("No Cheats or Achievements yet"), 3rd party cheat indexes ("Total cheats
available: 0"), and the 3rd party cheat indexes archive page all returned no codes; no 3rd party cheat index page for this
title was found. ROM literal counts: `password`=0, `cheat`=0, `secret`=0, `unlock`=0,
`debug`=0, `code`=0, `generator`=0, `warp`=0 (case-insensitive, 4 MiB).

**Text/button space searched (bounds):**
* Strings: all 4,194,304 bytes, `strings -n 3` + case-insensitive regex, plus literal
  byte-level counts above. Every `pass` hit was gameplay text (`Pass to player #`,
  `Pass to Next Player`) — not a password.
* Button-code tables: active-high single-key masks tested as `u16` (incl. combined
  L+R=`0x300`): 485 raw runs of ≥4 masks; after requiring a pointer reference, 35 runs —
  **all** homogeneous data runs (`0x04…`, `0x10…`, `0x20…`) inside compressed
  graphics/audio, none a varied button sequence. Byte-per-press form: 2,107 raw runs,
  none pointer-referenced as a code table. Result: **0 button-code tables**.
* Validator/table: BL scans to the string-print/core functions and pointer scans over the
  whole ROM found no comparison against a code table; the only input text is the name
  field, whose buffer is consumed only for display (no `strcmp`-style comparison to a
  constant list, and no constant list exists).

**Hidden-screen enumeration (the one hidden screen):**
* Space: 1 dead debug screen; selector 2..41 = **40** viewable entries; A launches the
  view, B exits, Left/Right move; entry 28 has a unique action.
* **Novel, unpublished reachability artifact**: forcing `pc = 0x08005D20` with a crafted
  return slot (§3) displays "Level Select / Select a level to view! / Level: / Matching
  Game / A Next / B Back" on the real emulator screen. This method and address are not on
  any published list (no lists exist). It is a debugger/developer path, **not** a
  controller cheat — stated explicitly per §16.10.
* **Bounds proven by rejection**: the screen's starter `0x08005D20` has **0** BL callers
  and **0** in-image pointer references (byte-aligned full-ROM search; the sole `0x0805D20`
  byte match at `0x0818EFF9` is inside compressed asset data). The dispatcher's compared
  starter set (`0x08005E29`, `0x08005C09`, `0x08001385`, `0x0800B2C1`, `0x0800B99D`,
  `0x0800C069`, `0x0800C739`, `0x08002405`, …) does **not** contain `0x08005D21`.
  Therefore every controller path is rejected: the screen is unreachable in-game.
  Additionally the selector's range checks explicitly reject 1 and 42 by wrapping.

## 7. Validation evidence

* **Observed** — emulator screenshots: legal/title, Main Menu, Game Options, player/name
  setup, game board, Mix-up Match mini-game; hidden Level Select screen forced via
  debugger; savestate-based RAM dumps locating the localization table and `Level Select`
  at `0x03005550`; .sav is 512 bytes.
* **Derived** — Thumb disassembly of `0x08012DE4`/`0x08012EA4`/`0x08005D20`/`0x08004F8`;
  full-ROM BL and pointer scans proving the hidden starter is unreferenced; key-mask
  reader at `0x08059798`.
* **Inferred** — the exact mapping of each of the 40 selector values to a level name was
  not enumerated one-by-one (forcing A launches the level and corrupts the debug overlay);
  the level-name list visible in code (`Main Game Board`, `Matching Game`, `In a Boat 1-4`,
  `On a Car 1-4`, `On a Train 1-4`, `In the Air 1-4`, `In a Box 1-4`, `Up a Tree 1-4`)
  is the likely set. The special action at selector 28 was not isolated. Pause overlay
  trigger was not found by Start in the screens exercised.

## 8. Unknowns

* Which button (if any) shows the `PAUSED` overlay in a mini-game — Start did not in the
  board or Mix-up Match screens tested.
* The exact level-name string for each of the 40 selector positions and the function of
  selector 28's dedicated A action.
* Whether the `Level_GameboardSequence`/`Victory Scene` name-printing code
  (`0x080129D8` region) is a live debug overlay or a logging path — not resolved; it does
  not affect the cheat/code conclusion.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3 (`struct`, `zlib`,
  `capstone 5.0.7`).
* `arm-none-eabi-objdump -M force-thumb` for all disassembly; custom Python BL/pointer/
  mask scanners.
* `mgba -3` (Xvfb `:315`, openbox, `SDL_AUDIODRIVER=dummy`) with `xdotool` (XTEST events to
  the focused window); `import -window root` for screenshots.
* mGBA CLI debugger `mgba -d -3` driven over a Python `pty` (`dbg.py`) for register reads,
  `w/r pc`, `w/4` stack crafting, and savestate diffing (§16.13: zlib-inflate `gbAs`
  chunk; IWRAM at state offset `0x19000` = `0x03000000`).

**Legal note:** no ROM image, extracted graphics, audio, or game assets are redistributed in
this report; only addresses, hashes, and the analyst's own tooling are published.
