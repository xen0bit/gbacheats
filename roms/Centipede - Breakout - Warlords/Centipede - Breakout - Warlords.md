# Centipede / Breakout / Warlords (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Centipede - Breakout - Warlords/Centipede - Breakout - Warlords.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`) |
| Header title (0xA0) | `CENTIPEDECOM` |
| Game code (0xAC) | `B6ZE` (USA) |
| Maker (0xB0) | `20` |
| Version (0xBC) | `0x00` |
| Entry (0x00) | `0xEA00002E` → ARM branch to `0x080000C0` (stock crt0) |
| Header complement (0xBD) | `0x68` (valid: `0x100 - (0x19 + sum(0xA0..0xBC))`) |
| Header checksum (0xBE) | `0x0000` (unused by GBA; normal) |
| MD5 | `cab2a6bb0d3c754ccf75ac3b3dc94cb0` |
| SHA-1 | `e91e58c62363fb10dd4ffcaeb09c98ca6b9b5a77` |
| SHA-256 | `d9bf11913c326a05500ca5d3456c86d913d7ca6f295ca09c5d1c1f14e8775bcf` |
| Developer | Epicenter Interactive (TCRF) |
| Publishers | DSI Games (US), Zoo Digital Publishing (EU) |
| Release | 2005-08-21 (US), 2005-09-09 (EU) |
| Sub-images | 1 (single header at file offset 0; no multiboot stubs, no cracktro) |

The ROM is a **single 4 MiB image**, not a concatenated multi-game cart. The
Nintendo logo occurs exactly once (file offset 4). The entry word is the stock
`0xEA00002E`; no scene-release/cracktro signature (`CRC BANDIT`, `SUNHORS`,
`Mode7`, `TRAINER`) is present. The header complement is valid, so the header
is a genuine retail header (the SHA-1 differs from the BizHawk/No-Intro entry
because that database entry is a different dump of the same SKU; the header
title/code and all analysed addresses below are for *this* dump).

### Per-game identities

The cartridge is a compilation shell plus three independent game engines. The
main loop keeps a one-byte "current game" index at `0x0300137E` and dispatches
through a function table at `0x08135A70`:

| Index | Function | Game |
|---:|---|---|
| 0 | `0x0801BCB5` | Centipede (game loop) |
| 1 | `0x0801C24D` | Title/intro state machine |
| 2 | `0x0800C535` | Compilation shell / Centipede menu frontend |
| 3 | `0x0800D389` | Shell transition |
| 4 | `0x080107D5` | Breakout |
| 5 | `0x08011831` | (Breakout/MP transition) |
| 6 | `0x08011CBD` | Warlords |
| 7 | `0x08012E4D` | (Warlords/MP transition) |

Selecting a game on the compilation menu writes the index and the launcher at
`0x0801D83D` performs the hand-off (selection 0 → state 2, 1 → state 4,
2 → state 6). The three engines share the shell's graphics, sound, input and
menu code but have separate data and game loops.

---

## 2. Executive summary

**No in-game cheat system exists in this ROM.** There is no password screen,
no button-sequence cheat, no hidden/debug menu and no unlock code. The only
cheats ever published for this SKU are CodeBreaker/GameShark/Action Replay
memory writes, which are outside the scope of this engagement.

The result is not "we did not find it"; it is a bounded negative:

* The ROM contains **zero** occurrences of `password`, `cheat`, `debug`,
  `secret` or `unlock` in ASCII (case-insensitive), UTF-16LE or `+0x20`-shifted
  ASCII. The full string table (25,159 strings, `strings -t x -n 4`) was
  scanned; the only "cheat-adjacent" text is ordinary menu prose.
* Every menu table in the ROM was enumerated. The 8 menu tables contain
  32 items, all of which are ordinary game functions (New Game, Continue,
  Options, Abort, difficulty, game type, lobby). None is a debug/cheat entry.
* The keypad state is read at `0x0300137A` (held) and `0x0300137C` (pressed).
  All 39 ROM references to the pressed-state offset and all 15 references to
  the held-state offset were classified. Every code reference is a menu
  navigation check (Up/Down/Left/Right/A/B/Start/Select) or a gameplay input
  mapping. **No reference participates in a sequence matcher, a mask table or a
  cheat flag.**
* The one candidate "single-press cheat helper" (`0x08015F9C`, which does
  `pressed & mask` and calls a handler) has **no caller and no function-pointer
  reference anywhere in the ROM** — it is dead code.
* The only published "codes" (GameHacking.org, emucheatz, GameFAQs cheat
  pages) are memory edits. VGChartz lists 0 cheats; TCRF lists only unused
  link-cable text at `0x327BC`; GameFAQs has no cheat page for this title.

Because the acceptance bar requires a *reproducible* negative, the report also
documents the dynamic walk that was performed (boot → title → compilation menu
→ each game's menu → options → gameplay → game over) and the exact key-state
addresses and menu tables that were inspected.

---

## 3. How to reproduce

Toolchain: `mgba-sdl 0.10.5` (Debian), `arm-none-eabi-objdump`, Capstone 5.0.7,
Python 3.13, Xvfb. No ROM asset is redistributed.

```bash
Xvfb :240 -screen 0 1024x768x24 &
DISPLAY=:240 openbox &
DISPLAY=:240 SDL_AUDIODRIVER=dummy mgba -3 "Centipede - Breakout - Warlords.gba"
```

Default mGBA keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys. Hold keys 100–300 ms; the shell polls
input once per frame.

Menu path walked (all verified by RAM reads and by rendering the mode-3 bitmap
to text):

1. Boot → "CENTIPEDE" title / PRESS START.
2. Press Start repeatedly → compilation menu (screen index 5), 3 game slots
   (selection `0x03000104`: 0 = Centipede, 1 = Breakout, 2 = Warlords).
3. Select Centipede → main loop state 2 (`0x0300137E`), shell frontend.
4. Shell menu items: NEW GAME / CONTINUE / OPTIONS / 1 PLAYER / 2 PLAYER.
5. OPTIONS → "Select Picture", "Select Picture Colour", "Select Background
   Colour", "Selects Screen View", "Select a New Background".
6. NEW GAME → Centipede playfield; Start → pause; game over → "GAME OVER".
7. Select Breakout → main loop state 4; select Warlords → main loop state 6.

Dynamic state used for verification:

| Variable | Address | Meaning |
|---|---|---|
| Current keys (active-high) | `0x0300137A` | `A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200` |
| Pressed this frame | `0x0300137C` | `current & ~previous` |
| Main-loop game index | `0x0300137E` | 0/1/2/4/6 table index |
| Compilation menu selection | `0x03000104` | 0=Centipede, 1=Breakout, 2=Warlords |
| Compilation menu counter | `0x03005A3C` | 15-frame selection timer |
| Shell screen ID | `0x03002D28` | index into screen table `0x0813C7A4` |
| Shell screen struct | `0x03002D24` | pointer to current screen struct |
| Title state machine | `0x030059F0` | 0=wait fade, 1=update, 2=launch |
| Title screen index | `0x030059F4` | 0..5 |

---

## 4. Address map

| Address | Kind | Description |
|---|---|---|
| `0x080000C0` | ARM | Stock crt0 entry (sets SP, calls `0x0800024D`) |
| `0x0800024C` | Thumb | `main`: hardware init, shell init, enters main loop |
| `0x08000398` | Thumb | Main per-frame loop: timers, text, state-function dispatch, input update |
| `0x080005D4` | Thumb | **Input update**: reads `0x04000130`, writes held `0x0300137A` and pressed `0x0300137C` |
| `0x0800C318` | Thumb | Screen setup from screen ID (`0x03002D28`) and table `0x0813C7A4` |
| `0x0800C534` | Thumb | Compilation shell loop (main-loop state 2) |
| `0x0800C568` | data | Shell state jump table (10 entries) |
| `0x0800D450` | Thumb | Shell state-0 handler (menu cursor / activation) |
| `0x0800D490` | Thumb | Screen transition setup |
| `0x08015F9C` | Thumb | **Dead code**: `pressed & mask` → handler helper; no caller, no pointer |
| `0x08016250` | Thumb | Generic menu handler (Up/Down/Left/Right/A/B; option toggles) |
| `0x08017864` | Thumb | Shell frontend state machine (draws menu box, Start/Select/B checks) |
| `0x0801C22C` | Thumb | Title state setter: `state = 2`, calls `0x0801BC60(arg)` |
| `0x0801C24C` | Thumb | Title/intro state machine (main-loop state 1) |
| `0x0801C2EC` | Thumb | Title screen 0 update (timer/key → next screen) |
| `0x0801C400` | Thumb | Title screen 3 (left/right selector, 5 options, A confirms) |
| `0x0801C5A5` | Thumb | Compilation menu init (draws the 3 game items) |
| `0x0801C7C9` | Thumb | Compilation menu handler (Left/Right/Start, selection at `0x03000104`) |
| `0x0801D83D` | Thumb | Compilation menu launcher (writes `0x0300137E` = 2/4/6) |
| `0x0801BCB5` | Thumb | Centipede game loop (main-loop state 0) |
| `0x080107D5` | Thumb | Breakout game loop (main-loop state 4) |
| `0x08011CBD` | Thumb | Warlords game loop (main-loop state 6) |
| `0x08135A70` | data | Main-loop function table (8 entries, indexed by `0x0300137E`) |
| `0x0813C7A4` | data | Shell screen-parameter table (0x28-byte records) |
| `0x0813E3B0` | data | Title screen table (init/update/launch function pointers) |
| `0x0813E9EC` | data | Compilation menu data (graphics + coordinates) |

---

## 5. Algorithm

There is no cheat algorithm to reverse. The only "code-like" input path is the
normal keypad poll:

```
; 0x080005D4, Thumb, called every frame from 0x0800057A
ldrh r1, [0x04000130]          ; KEYINPUT, active-low
mvns r1, r1                    ; active-high
lsls r1, r1, #16
lsrs r1, r1, #16               ; r1 = held keys, bits 0..9
ldrh r3, [0x0300137A]          ; previous held state
strh r1, [0x0300137A]          ; store current
bics r0, r1, r3                ; r0 = current & ~previous
strh r0, [0x0300137C]          ; store pressed-this-frame
```

Menu code then tests single masks (`ands rX, mask` with 1/2/4/8/0x10/0x20/0x40/
0x80/0x30) and advances a cursor. No sequence state machine, no mask table and
no cheat flag exists.

---

## 6. Tables

### 6.1 Menu item tables (all 0x18-byte records; `{field0, label, description, id, handler/data, 0}`)

**Centipede menu — `0x08022F10` (5 items)**

| # | Label | Handler |
|---:|---|---|
| 0 | Continue playing game | `0x08015D39` (set shell bit 1) |
| 1 | Starts a New game | `0x08015D49` (set shell bit 2) |
| 2 | Choose New Game Type | `0x03005140` |
| 3 | Options | `0x030051A4` |
| 4 | Abort Game | `0x08015D29` (set shell bit 3) |

**Breakout menu — `0x08023958` (5 items)**

| # | Label | Handler |
|---:|---|---|
| 0 | Continue Game | `0x08015D39` |
| 1 | Begin a New Game | `0x08015D49` |
| 2 | Choose New Game Type | `0x03005140` |
| 3 | Options | `0x030051A4` |
| 4 | Abort Game | `0x08015D29` |

**Warlords menu — `0x08023EC8` (4 items)**

| # | Label | Handler |
|---:|---|---|
| 0 | Continue Game | `0x08015D39` |
| 1 | Start 1 Player Game | `0x08015D49` |
| 2 | Multiplayer | `0x03005140` |
| 3 | Abort Game | `0x08015D29` |

**Warlords MP pause — `0x08024040` (2 items)**: Continue Game, Abort Multiplayer Game.

**Options menu — `0x08022CC8` (3 items)**: Select Picture, Select Picture
Colour, Selects Screen View.

**Centipede difficulty — `0x08022E04` (3 items)**: New EASY game, New NORMAL
game, New EXPERT game.

**Breakout game type — `0x080236E4` (5 items)**: Timed, Breakthru, Steerable,
Catch, Invisible.

**Multiplayer lobby — `0x08023DA0` (4 items)**: Enter the Lobby, Multiplayer
Best of, Select Rounds to play, Set multiplayer name.

No table contains a debug, cheat, credits, level-select or "secret" entry.

### 6.2 Keypad masks

| Bit | Button |
|---:|---|
| 0x001 | A |
| 0x002 | B |
| 0x004 | Select |
| 0x008 | Start |
| 0x010 | Right |
| 0x020 | Left |
| 0x040 | Up |
| 0x080 | Down |
| 0x100 | R |
| 0x200 | L |

### 6.3 Published in-game codes

**None.** Verified sources:

* VGChartz cheat page for this title: "Total cheats available: 0".
* GameFAQs title page: 11 guides, no cheat/FAQ cheat page.
* TCRF: only unused link-cable text at `0x327BC`; no cheat, no debug menu.
* GameHacking.org / emucheatz: only CodeBreaker/GameShark memory writes
  (out of scope).

---

## 6b. Enumeration

### Space searched

| Search | Result |
|---|---|
| `strings -t x -n 4` total | 25,159 strings |
| `password` (ASCII, case-insensitive) | **0** |
| `cheat` (ASCII, case-insensitive) | **0** |
| `debug` (ASCII, case-insensitive) | **0** |
| `secret` (ASCII, case-insensitive) | **0** |
| `unlock` (ASCII, case-insensitive) | **0** |
| Same five keywords in UTF-16LE | **0** |
| Same five keywords in `+0x20`-shifted ASCII | **0** |
| Long alphanumeric runs (≥32 chars, candidate password alphabets) | 478 runs, all graphics/tile/font data; none is a password alphabet |
| 4-byte literal `0x00000C0C` (pressed-state offset) | 39 hits; 26 are data/graphics, 13 are code (all menu/gameplay checks) |
| 4-byte literal `0x00000C0A` (held-state offset) | 15 hits; 1 is data, 14 are code (all gameplay input mappings) |
| 4-byte literal `0x000003FF` (all-buttons mask) | 52 hits; all in graphics/fixed-point math data; **0 in cheat logic** |
| Thumb pointer `0x08015F9D` (candidate cheat helper) | **0** (dead code) |
| Menu tables enumerated | 8 tables / 32 items |

### Bounds / negative proof

* **No password alphabet**: the only long alphanumeric strings are the font
  tables at `0x082427C` (the ASCII glyph set) and compressed tile data. There
  is no 32/36/64-symbol password alphabet and no keypad entry screen.
* **No sequence matcher**: every code reference to the pressed-state offset
  (`0x0300137C`) was disassembled and classified; all are single-mask menu
  checks. There is no table of masks, no progress counter and no cheat flag.
* **No hidden menu entry**: every menu table was enumerated; all 32 items map
  to ordinary game functions. The shell's screen table (`0x0813C7A4`) and the
  title screen table (`0x0813E3B0`) contain no debug/cheat record.
* **Dead helper**: the only function shaped like a cheat helper
  (`0x08015F9C`) is unreachable — no `BL` target and no pointer to it exists
  in the ROM.
* **Dynamic walk**: booted, walked the title, compilation menu, Centipede
  menu, options, gameplay and game-over screens, and launched Breakout
  (state 4) and Warlords (state 6). No hidden screen appeared.

Because there is no code system, the §0.2 requirement to mint a novel code does
not apply; the equivalent deliverable is the bounded negative above.

---

## 7. Validation evidence

**Observed (emulator, mGBA 0.10.5 on Xvfb :240):**

* Boot reaches the "CENTIPEDE" title / PRESS START.
* Start advances the title state machine; index reaches 5 (compilation menu).
* Compilation menu selection `0x03000104` = 0/1/2; Start launches the game
  and writes `0x0300137E` = 2 (Centipede), 4 (Breakout), 6 (Warlords).
* Centipede menu items and cursor movement observed; OPTIONS screen rendered;
  NEW GAME starts the playfield; Start pauses; game over shows "GAME OVER".
* Key state addresses verified: holding A sets `0x0300137A = 0xFC01`; holding
  Start sets `0xFC08`; the pressed state at `0x0300137C` is `0x0008` for one
  frame.
* The ROM folder's `.sav` is 0 bytes after play (no save written; the game
  uses battery save only for high scores / initials).

**Derived (disassembly):**

* Input update at `0x080005D4` and the two key-state addresses.
* Main-loop dispatch table at `0x08135A70` and the game-index byte at
  `0x0300137E`.
* Title state machine at `0x0801C24C`, title table at `0x0813E3B0`.
* Compilation menu handler `0x0801C7C9` and launcher `0x0801D83D`.
* Shell frontend `0x08017864` and shell loop `0x0800C534`.
* All 8 menu tables (32 items) and their handlers.

**Inferred:**

* The SHA-1 mismatch against BizHawk's database is a dump difference (the
  header complement is valid and the code is stock); no patched code was found.
* The "1 PLAYER" / "2 PLAYER" items on the Centipede menu are standard game
  modes (the strings are composed from the shared "1 Player game" text), not
  cheat entries.

---

## 8. Unknowns

* The high-score name-entry screen ("Enter your initials" at `0x08229BC`) was
  not driven to completion. It is a name field for the high-score table, not a
  password field, but a name-as-code Easter egg was not exhaustively excluded.
* The multiplayer lobby and "Select Rounds to play" screens (Warlords/Breakout)
  were enumerated statically but not driven dynamically.
* The exact save type (EEPROM vs Flash) was not determined; the `.sav` stayed
  0 bytes because no high score was entered.

---

## 9. Tooling

Scripts written to `/tmp/opencode/centipede/`:

* `drive.py` — pty driver for `mgba -d` (send commands, SIGINT to pause).
* `gbadis.py` — Capstone Thumb/ARM disassembler with PC-relative literal
  resolution (avoids the `objdump` halfword-order trap).
* `nav.py` — robust menu navigation (wait for fade, Left/Right selection,
  Start launch with retries).
* `savestate.py` — parse mGBA `.ss*` PNG savestates, extract the zlib `gbAs`
  chunk (397,312 bytes) and VRAM/IWRAM/EWRAM.
* `render.py` — render the mode-3 bitmap to ASCII text (used for all screen
  evidence; no image files were used).
* `bpcount.py`, `keytest.py`, `stateprobe.py`, `probe.py` — breakpoint and
  key-state probes.

No ROM, asset or image is redistributed by this report.
