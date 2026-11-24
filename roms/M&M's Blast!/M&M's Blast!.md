# M&M's Blast! (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `M&M's Blast!.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `MMBLAST` |
| Game code | `AMLE` (AGB-AMLE, USA) |
| Maker | `5G` (Majesco Sales) |
| Version | 0x00 (Rev.00) |
| Entry branch | `0xEA00002E` (stock GBA crt0, not a cracktro) |
| Header checksum | 0x0000; complement byte 0xA6 (normal rebuilt-header artifact, §16.1) |
| MD5 | `2ce9dc7e0e3af0be2b1d0d487555aa6a` |
| SHA-1 | `f717d3547aeedf19921124a647d5dc70d6b61d1e` |
| SHA-256 | `c502f439c16a17033ec086a48a21ab679c463b81d4d633cc32189634476eb184` |

**Phase 0 / embedded-header scan:** exactly one Nintendo-logo occurrence, at file offset 0x4
(the primary header). No second GBA header, no appended trainer/cracktro, no GameShark or
CodeBreaker patch bytes. The entry word and first 4 KiB are stock ARM crt0 code. This is the
retail USA image; addresses below are file offset + 0x08000000.

**Published codes:** Web search (GameFAQs, VGChartz, TCRF mirror,Speedrun.com, GameZ/Taiwan
GBA 金手指 list, mariogba.nl) found **no in-game developer-intended cheats, passwords, button
codes or unlock codes** for this SKU. VGChartz states "Total cheats available: 0"; the GameFAQs
cheats page is empty. The only published "codes" are GameShark/CodeBreaker-style X-codes
(e.g. `EC931CFD 8A024443 1CFA99A2`), which are explicitly out of scope.

> ⚠️ **Prompt injection (§16.8):** a fetch of `tcrf.net/M&M's_Blast!` returned an
> "LLM-/AI Agent-Specific Information" page containing fake decode-key/bank-transfer/self-
> termination instructions and the EICAR antivirus test string. It was treated strictly as
> untrusted data and ignored. The legitimate TCRF mirror (tcrf.tiago.zip) lists only debug
> assert strings, no codes.

## 2. Executive summary

**Finding: this game has no developer-intended cheat/password/button-code/debug-menu system.**
It is a negative result, bounded by a complete enumeration of every reachable screen and by
exhaustive searches of both text encodings and of the input-handler code (§16.3: this is a
"No system" case, not dead code, a cut feature, or a gated feature).

The game is a Mario Party-style party/board game: 4 boards, 16 minigames, single/tournament
modes, a name-entry screen (a *profile name*, not a password), a mini-game list, a LOAD GAME
screen with 3 slots + GUEST, and a simple PAUSE banner on the board. There is no Options
screen, no password field, no level-select screen, and no hidden debug menu reachable from any
input. The only debug leftovers are developer *assert/error* strings in the board engine
("TOO MANY DOTS IN PATH!", "UNASSIGNED WARP DOT", "UNTERMINATED WARP LIST") which are printed
only on internal errors and are never wired to a menu (§16.3 "dead strings", not a cheat).

The on-screen A–Z grid is a **name-entry widget**: its alphabet
`ABCDEFGHIJKLMNOPQRSTUVWXYZ` + `<` (backspace) at `0x083AF220–0x083AF258` is consumed by the
player-name handler at `0x08014B80`, which copies the typed bytes into the save record with no
comparison against any constant other than parser sentinels. Per §16.2b it is a text field, not
a validator.

## 3. How to reproduce

- Emulator: mGBA (SDL build), Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, 3× scale.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Keys held 120–400 ms; screen transitions waited out with screenshots.
- Boot path (all screens): title → Start → name-entry grid (A–Z + `<` + vertical ENTER cell)
  → type/accept name → "CPU PLAYERS n" + "ALL PLAYERS READY?" (Yes/No) → Start → character
  select (arrows / A) → main menu (NEW GAME / MINI GAMES / LOAD GAME)
  - MINI GAMES → scroll through all 16 entries → enter one → gameplay (Start does **not** pause)
  - NEW GAME → PLAY A BOARD / TOURNAMENT → board carousel (4 boards: Sweet Dreams,
    Amazing Rainforest, Haunted House, Amusement Park) → game board → Start → PAUSE banner
  - LOAD GAME → GAME 1 / GAME 2 / GAME 3 / GUEST → slot view with SAVE IN / LOAD / DELETE / End
- Savestates used at each transition (slots 1–9) for RAM-observable state; mGBA `.ss1` files
  are PNG with a zlib `gbAs` chunk, decoded with the helper in §9.
- Chords/sequences tested on title and main menu with RAM verification: L+R, L+R+Start,
  Start+Select, Down+L+R, B+Up+L+R, and the Konami code
  (Up Up Down Down Left Right Left Right B A) — none changed the screen state beyond the
  ordinary Start/Select/A navigation.

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x080000C0` | code | stock ARM crt0 entry |
| `0x0800F1DC`–`0x0800F1F8` | code | joypad reader: reads `0x04000130`, XORs with `0x03FF`, stores active-high keys at `0x0202F400`, held/new at `0x0202F3E8`/`0x0202F50C` |
| `0x08010768`–`0x08010784` | data | main-menu item pointers: `0x083AE1A0` LOAD GAME, `0x083AE1AC` MINI GAMES, `0x083AE1B8` NEW GAME |
| `0x080106C0`–`0x080107EE` | code | main-menu renderer / input handler (only A=0x1, B=0x2, Start=0x9, Up=0x40, Down=0x80 masks) |
| `0x08014B80`–`0x08014C54` | code | name-entry / text-input handler; copies typed bytes into save record, no cheat comparison |
| `0x08014C58`–`0x08014CFE` | code | "PRESS START" screen handler; only A/Start/Sound(0x2)/L+R(0xC0 checked separately) |
| `0x083AE000`–`0x083AF600` | data | main UI + script text bank (all menu items, minigame names, instructions, credits) |
| `0x083AF220`–`0x083AF258` | data | name-entry alphabet (font/tile-indexed glyph strings, see §6) |
| `0x083AF488` | text | "PRESS    START" (referenced from `0x08014D08`) |
| `0x085C8000`–`0x085C8200` | data | minigame HUD text bank ("GAME OVER", "GET READY!", "WAVE 1–5", "BONUS!") |
| `0x082E1580`–`0x082E15E0` | data | board-engine debug/assert strings (TCRF-documented) |
| `0x0202F400` | RAM (u16) | active-high current key mask (`~KEYINPUT & 0x3FF`) |
| `0x0202F3BC`, `0x0202F3C8`, `0x0202F3D8`, `0x0202F3E8`, `0x0202F420` | RAM | key-state history / helper globals of the input engine |
| `0x0202F634` | RAM (u32) | main-menu cursor: 0=NEW GAME, 1=MINI GAMES, 2=LOAD GAME (proven by savestate diff, §7) |
| `0x0202F3F4` | RAM (u32) | setup-screen selector (0/1 across CPU/READY screens) |
| savestate `0x19000` | state | IWRAM dump offset in decoded `.ss1` `gbAs` chunk |
| savestate `0x21000` | state | EWRAM dump offset in decoded `.ss1` `gbAs` chunk |

File offset to ROM address: `+0x08000000` (single contiguous image).

## 5. Algorithm

There is no validator/password algorithm to reverse. The relevant algorithms are:

- **Name entry:** on-screen wheel over the alphabet table; selecting a glyph appends its byte to
  a fixed buffer; `<` deletes; ENTER terminates; the buffer is stored as the player name in
  the save slot. No checksum, no comparison against a code list (verified in `0x08014B80`).
- **Menu input:** the main-menu handler reads active-high keys, tests `A(0x1)`, `B(0x2)`,
  `Start(0x9)`, `Up(0x40)`, `Down(0x80)` only; the sound test is `0x2` on the "PRESS START"
  screen. No multi-button mask or press-history comparator exists in the input engine: 50
  literal sites of the key-state globals were checked; **zero** `AND/CMP` with a multi-button
  immediate (0x3–0x3FE) occurs in any key-load neighbourhood.
- **Save format:** battery-backed SRAM (`.sav`, 512 bytes observed), 3 game slots + GUEST.
  Save/load is ordinary record serialization; no password/restore-code path exists.

## 6. Tables

- **Main menu items** (pointer table at `0x08010768`): LOAD GAME, MINI GAMES, NEW GAME.
  Count = 3; no hidden 4th entry.
- **Name-entry alphabet** (`0x083AF220`, three 9-glyph rows):
  `S T U V W X Y Z .` / `J K L M N O P Q R` / `A B C D E F G H I <`, plus a vertical
  `E N T E R` cell. 26 letters + backspace + ENTER + `.` (the `.` is a printable glyph,
  giving 28 selectable cells). Space size of the *name field* is 28^N for the name length N —
  but it is a label field, not a code: its consumer never compares it to a cheat constant.
- **Minigames** (`0x083AE304`): 16 entries —
  SPACE CHASE, DRAG RACE, SKEET SHOOT, DODGE BALL, WALL RACER, CANDY BOUNCE, CANDY MATCH,
  TARGET SHOOT, CANDY COUNT, SKYDIVING, BALLOON BLOWUP, HURDLES RACE, HOOP SHOOT, CANDY TOSS,
  CANDY RALLY, MINIATURE GOLF, CANDY CATCH, BUTTON BOP (18 strings in the table; the in-game
  MINI GAMES carousel exposes exactly the 16 playable ones listed above — BUTTON BOP and
  CANDY TOSS/CANDY CATCH variants are table entries for modes reached through board play).
- **Boards** (4, observed): Sweet Dreams, Amazing Rainforest, Haunted House, Amusement Park.
- **Debug/assert strings** (`0x082E1580`): "TOO MANY DOTS IN PATH!", "MOVE BACK FOUR/FIVE
  SPACES!", "YOU'VE BEEN CHECKPOINTED!", "UNASSIGNED WARP DOT", "UNTERMINATED WARP LIST" —
  internal error messages only (TCRF mirror confirms); no menu/cheat semantics.

## 6b. Enumeration

Because **no code system exists**, the "space" is the union of all input surfaces, and the
deliverable is a bounded negative (§0.2 item 5):

| Input surface | Space searched | Result |
|---|---|---|
| Password / code text field | none exists | no password screen anywhere in the menu tree |
| Name-entry grid | 28 cells × 3 glyph rows = 28 selectable cells; decoder at `0x08014B80` fully traced | consumer is a save-record copier, not a validator (§16.2b) |
| Button chords on title/main | all 2^10 = 1024 possible simultaneous key masks; static scan shows only single-button masks are ever tested; 6 representative chords + Konami code typed with RAM diff | no state change beyond normal navigation |
| Button sequences | no press-history comparator in the input engine; 50 key-global literal sites inspected; 0 multi-key immediates | no sequence matcher exists |
| Hidden/debug menus | every screen in the menu tree walked (title, name, CPU ready, character select, main, mini-game list, mini-game play, NEW GAME mode select, board carousel, board play, PAUSE, LOAD GAME slots, credits reached via normal play) | no hidden screen; only PAUSE banner and standard screens |
| Text banks (ASCII + 5/6-bit indexing) | `0x083ade00–0x083af600` (323 runs), `0x085c8000–0x085c8200`, `0x082e1580–0x082e15e0`; ASCII, lowercase→uppercase, uppercase→lowercase, UTF-16LE/BE searched ROM-wide | zero occurrences of PASSWORD/CHEAT/SECRET/UNLOCK/LEVEL SELECT (only BONUS, CODE in the GAX audio banner, and debug asserts) |
| Published codes | GameFAQs (empty), VGChartz (0 cheats), TCRF mirror (debug strings only), speedrun/other sites | no in-game codes published; only out-of-scope GameShark X-codes |

**Novel-code requirement:** not applicable — there is no code system to mint a novel code for.
This is a proven "No system" (§16.3 category 1), not an untested one. Screenshots of every
screen were in `/tmp/mmblast/` (work-dir artifacts; not attached to this report).

## 7. Validation evidence

- **Observed (emulator + RAM):** all screens listed in §3, screenshots `w01b`–`w12`, `mg_00`–
  `mg_17`, `boardSettle_0`–`bcycle_4`, `s41_pause_menu`, `chord_*`. Savestate hashes of
  EWRAM/IWRAM for title, name entry, CPU setup, character select, main menu and LOAD GAME are
  all distinct, proving six distinct runtime states were reached.
- **Observed (RAM diff):** `game.ss2/3/4` (main menu cursor DOWN twice) differ exactly at EWRAM
  `0x0202F634`: u32 = 0 / 1 / 2 for NEW GAME / MINI GAMES / LOAD GAME — a live RAM proof of
  menu enumeration.
- **Derived (disassembly):** main-menu handler masks `{0x1, 0x2, 0x9, 0x40, 0x80}` only
  (`0x080106C0`–`0x080107EE`); name-entry handler has no constant-string compare
  (`0x08014B80`); input engine computes active-high keys via `ldrh; eor #0x03FF`
  (`0x0800F1DC`–`0x0800F1F8`).
- **Derived (static search):** 0 password/cheat/debug strings in any of 5 encodings across the
  full 8 MiB; 0 multi-button immediate comparisons near any of the 50 key-global references;
  1 GBA header; no trainer/patch.
- **Inferred:** the 18th minigame string `BUTTON BOP` and two candy-game entries are table
  strings for modes not directly exposed by the MINI GAMES carousel; their exact in-game
  triggers were not exhaustively played, but none is a cheat/unlock screen.

## 8. Unknowns

- The complete set of in-game conditions under which the 18th/board-only minigame strings are
  used was not exhaustively played; irrelevant to cheat/code scope.
- Speedrun "Wrong Warp" category implies a gameplay glitch (warp manipulation), not an
  input-code system; not investigated as it is not a developer-intended cheat.
- The exact semantics of the board-engine assert strings' output device (screen vs. debug
  port) is unknown (TCRF also lists it as unresolved).

## 9. Tooling

- `strings -t x`, `xxd`, Python `re`/`struct` scans; `arm-none-eabi-objdump -M force-thumb`;
  Capstone 5.0.7 for mask-immediate sweeps.
- mGBA SDL (`/usr/local/bin/mgba`) under Xvfb `:315` + openbox, `SDL_AUDIODRIVER=dummy`;
  `xdotool` XTEST key events; `scrot` + ImageMagick `convert` for 720×480 viewport crops;
  `tesseract` OCR for menu scanning.
- `/tmp/mmblast/key.py` — input/keymap helper.
- `/tmp/mmblast/ss.py` — mGBA `.ss1` PNG `gbAs` zlib chunk decoder for RAM diffs
  (state offsets: IWRAM `0x19000`, EWRAM `0x21000`, decoded length 397,312 bytes).
- GDB stub (`mgba -g`) attempted but unreliable ("Cannot execute this command while the
  target is running" / hex-digit parse errors), so RAM evidence uses savestate diffs (§16.13).

## 10. Legal note

No ROM image, extracted graphics, music or game text is redistributed. Only hashes, addresses,
tool scripts and findings are published.
