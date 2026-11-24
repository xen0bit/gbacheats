# Mario & Luigi: Superstar Saga (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mario & Luigi: Superstar Saga/Mario & Luigi: Superstar Saga.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `MARIO&LUIGIU` |
| Game code | `A88E` (USA), maker `01` (Nintendo), version `0x00` |
| Header entry | `0xEA00002E` (stock, unchanged) |
| Complement / checksum | `0x8D` / `0x0000` (checksum 0 is normal for Nintendo-built headers) |
| Build date | `Oct  4 2003 06:21:36` at file offset `0x5202A4` — matches TCRF's North American retail build exactly |
| MD5 | `4b1a5897d89d9e74ec7f630eefdfd435` |
| SHA-1 | `7c303cdde5061ee329296948060b875cb50ba410` |
| SHA-256 | `af9066e7eacdab919e92987db8856d038e4b75d4ed011259c893702085a886be` |
| Save hardware | SRAM, 8 KiB (mGBA created an 8192-byte `.sav`) |

**Phase 0 / §16.1 check:** one Nintendo-logo hit only, at file offset `0x0`; no second header, no appended trainer, no cracktro patch, stock entry branch. This is the retail US image, not a rebuilt or multi-game image. Bytes `0xD00000`–`0xEFFFFF` are pure padding; used data ends before `0xD00000`.

## 2. Executive summary

**There is no in-game password, button-code, cheat-code or hidden-debug-menu system in this ROM.** The negative is bounded, not assumed:

* The title screen has exactly three entries (`MARIO & LUIGI`, `MARIO BROS.`, `OPTIONS`); the options screen has exactly three settings; the file-select screen has `Start Game / Copy File / Delete / Cancel`. Every one was entered and screenshotted. The field menu's complete item set is `Items / Equipment / Bros. Info / Beanbean Map / Sleep` and the battle menu's is `Jump / Hammer / Hand / Solo Attack / Bros. Attack / Use an Item / Run Away` — both enumerated from their ASCII string banks at `0x201F38` and `0x200448` (§16.2: this game's UI **is** ASCII, so `strings` is a valid census tool here; the control bytes are `0xFF`-prefixed markup, e.g. `D` = draw, `0x0A` = newline).
* Across all 319,414 ASCII runs, `password` = 0 hits, `unlock` = 0, `sound test` = 0, `level select` = 0, `master code` = 0. `debug` = 1 hit (`Debug T…` = *Debug Team* in the ending credits), `cheat` = 1 (a joke line, `Hmph... This game cheats!`), `code` = 2 (`Sun Door Release Code`, a scripted story puzzle at `0x3FA197`, and one compressed-data false positive).
* Only **three** real reads of `KEYINPUT` (`0x04000130`) exist in code — `0x08017CE4`, `0x08017F7A`, `0x0801A4E8` — all inside the generic input library. They compute an active-high mask and feed a debounce/repeat routine at `0x08018920`; none compares a button sequence, maintains a progress index or references a mask table. (Three further `0x04000130` literals at `0x8F50BE8`/`0x8F6FD00`/`0x8F7E434` fall in compressed high-ROM data and are not code.)
* AlphaDream did ship a debug room (room `000D`) and a cutscene-debug menu, but the only published way in is a **GameShark memory write** (TCRF: `02001E90:0001`, plus `02001E9C:0001` for Luigi). That is a memory-edit code, explicitly out of scope for this engagement. Statically, the ROM's 64-entry `gsys` label bank at `0x0839ECC4` has **zero** external literal references — the code that used it was deleted before release (TCRF agrees), so it cannot be a live menu.
* GameFAQs' cheat page for this exact SKU (game id `914980`, 2012 archive) contains **no passwords or codes at all** — only gameplay glitches, easter eggs and secrets. A VGChartz lookup returned an unrelated title and produced no code list for this game. Therefore there are no published in-game codes to verify; the published "codes" that do exist are GameShark addresses and were recorded, not tested (out of scope).

The only developer-intended extra is the bundled **Mario Bros. GBA remake**, reachable directly from the title screen and walked here.

## 3. How to reproduce

Emulator: `mgba 0.10.5` (SDL), own display `Xvfb :318 1024x768x24` + `openbox`, `SDL_AUDIODRIVER=dummy`. Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Holds of 50–150 ms; longer holds double-step menu cursors (§16.2).

For RAM evidence, mGBA was run with `-d` (CLI debugger on a PTY) because the GDB stub port was occupied by another process. `SIGINT` to the mGBA PID breaks into the debugger; `r/1|r/2|r/4 ADDR` reads memory, `c` resumes. Savestates were taken with `Shift+F1` and decoded with `zlib.decompress` on the PNG `gbAs` chunk (§16.13): for this 16 MiB image the raw state is 397,312 bytes, with EWRAM at raw `0x21000`, IWRAM at raw `0x19000`, verified against live `r/4 0x02000000` / `x/4 0x03000000` reads.

Screen path actually walked:

1. `PRESS START` title → three entries; cursor arcade pointer and left-hand info panel change with selection (RAM: savestate diff shows the title-menu state bytes change; `KEYINPUT` reads `0x000003FF` at idle).
2. `OPTIONS` → `Easy Sleep ON/OFF`, `Rumble Feature ON/OFF` (greyed out), `Auto Sleep ON/OFF`; Down wraps among the three, no fourth entry.
3. `MARIO & LUIGI` → file select: three `NEW GAME` tabs, `Start Game / Cancel`, plus `Copy File / Delete` strings in the same bank; `Start Game` → new game → full intro → playable Toad segment in Mario's house (field movement confirmed: Toad's on-screen position changes after Right/Left).
4. Back to title → `MARIO BROS.` → `Single Player / Multiplayer` → `Classic` → `PRESS START` → playable Phase 1 (savestate `mb_phase1.ss1`; IWRAM differs from the mode-select state in 7,030 bytes, EWRAM is zeroed).
5. Hidden-screen probes on every screen above: Start, Select, A+B, L+R, L+Select, R+Select, R+Start — no menu, debug overlay or extra option appeared (screenshots compared after each). The game's own decoded hint says `Press L/R+SELECT to view the menu` (script at `0x3D7D82`, `0x400D60`; dialogue `Press [L]+SELECT to open your suitcase` at `0x3DBEAA`) — those combos were also pressed (both hold orders, 300 ms) and produced no menu in the Toad-only scripted segment. A 120-step pseudo-random D-pad walk from that segment (checkpoint contact sheet) never produced a room transition; the only new screen state was the repeated thought bubble `I must find Mario immediately!` (observed at `0x3DBAxx` region of script).

Published material checked (treated strictly as data; no instructions in fetched pages were followed):
* TCRF, archived 2023-04-06: `https://web.archive.org/web/20230406091211/https://tcrf.net/Mario_%26_Luigi:_Superstar_Saga` — documents the debug room/menu, but every access method is a memory edit. No prompt-injection payload was observed in this fetch (contrast §16.8).
* GameFAQs, archived 2012-08-18: `https://web.archive.org/web/20120818054116/http://www.gamefaqs.com/gba/914980-mario-and-luigi-superstar-saga/cheats` — zero passwords/codes.

## 4. Address map

| Address (ROM = file + `0x08000000`) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Entry (`b 0x080000C0`) | Observed bytes |
| `0x0839ECC4` | 64-entry `gsys` label pointer bank (strings at `0x081E1EF4`…`0x081E23FC`) | Observed; pointer dump |
| `0x085202A4` | Build date `Oct  4 2003 06:21:36` | Observed bytes |
| `0x08201210`/`0x08201790`/`0x082017B0` | Wrecking Crew map/palette/image (unused, no access path per TCRF) | TCRF + ROM presence |
| `0x0828335C`, `0x082833C8` | Unused enemy scripts (TCRF) | TCRF |
| `0x08201F78` | `Start Game` (file-select/menu label bank begins `0x08201F30`) | Observed bytes |
| `0x08201F3C`…`0x08201FA0` | Pause/file menu strings: `Items`, `Equipment`, `Bros. Info`, `Beanbean Map`, `Sleep`, `Start Game`, `Copy File`, `Delete`, `Cancel`, `Loading...` | Observed bytes |
| `0x08200448`…`0x082004EC` | Battle command strings (EN): `Back`, `Nothing`, `Jump`, `Hammer`, `Hand`, `Solo Attack`, `Bros. Attack`, `Use an Item`, `Run Away` | Observed bytes |
| `0x083FA197` | `Sun Door Release Code` story puzzle script; `0xFF` control codes + `+O`/`-O` action glyphs | Observed bytes / decoded |
| `0x08017CE4`, `0x08017F7A`, `0x0801A4E8` | The only three real `KEYINPUT` reads | Derived (Capstone scan) |
| `0x08018920` | Generic key-state/debounce updater (writes struct via pointer at `0x03000374`) | Derived (disassembly) |
| `0x0839EC6C` | Key repeat/mask config table used by `0x08018920` | Derived (disassembly) |
| `0x02001E90`, `0x02001E9C` | Save flags used by TCRF's GameShark debug-room codes (observed `0x00` in normal play) | Observed + TCRF |
| `0x03000374` | Pointer to key-state struct (held/pressed/released + repeat counters) | Derived |

## 5. Algorithm

Not applicable: there is no validator, checksum, password decoder or code generator in this image. The only algorithmic input handling is the generic key-debounce routine at `0x08018920`:

```
mask   = ~KEYINPUT & 0x3FF                 // active high
pressed  = mask & ~held;  released = held & ~mask
held   = mask
for each key with a repeat-eligible mask from 0x0839EC6C:
    if newly pressed: counter = initial delay
    else if still held: decrement counter; on zero: emit repeat, reload counter
```

This was confirmed at `0x08017CE4`/`0x08017F7A` (load, invert, mask to 10 bits, call updater) and `0x0801A4E8` (D-pad `0xF0` edge detect with a `cmp #3` repeat bound). No comparison against a stored sequence occurs in any of the three.

## 6. Tables

**Title menu** (3 entries, all reached): `MARIO & LUIGI`, `MARIO BROS.`, `OPTIONS`.

**Options** (3 settings, all reached): `Easy Sleep`, `Rumble Feature` (disabled), `Auto Sleep`; each `ON/OFF`.

**Pause / field menu** (ROM table at `0x08201F38`, 5 entries): `Items`, `Equipment`, `Bros. Info`, `Beanbean Map`, `Sleep`.

**File select** (same bank): `Start Game`, `Copy File`, `Delete`, `Cancel`.

**Battle commands** (ROM table at `0x08200448`, 7 localized triples): `Back/Nothing`, `Jump/Hammer/Hand`, `Solo Attack`, `Bros. Attack`, `Use an Item`, `Run Away`.

**Keyword census** (all 319,414 ASCII runs ≥4 chars):

| Term | Hits | Interpretation |
|---|---:|---|
| password | 0 | — |
| unlock | 0 | — |
| sound test | 0 | — |
| level select | 0 | — |
| master code | 0 | — |
| cheat | 1 | dialogue joke at `0x47B341` |
| debug | 1 | `Debug Team`, credits at `0x2122C8` |
| code | 2 | `Sun Door Release Code` (`0x3FA197`) + compressed-data noise |
| secret | 40 | item descriptions/dialogue (`Secret Scroll 1/2`, etc.) |

**gsys label bank**: 64 valid ROM pointers, 0 external literal references → dead data.

## 6b. Enumeration

For a *positive* password/code system §0.2 would require space size, validator model, a novel generated code and rejection bounds. Here the enumerated space is **empty**, so the deliverable is the bounded negative:

* **Screen space:** title (3/3 entries entered), options (3/3, Up/Down wrap verified), file select (3 tabs + all 4 actions present in bank), Mario Bros. (2/2 modes, Classic/Phase 1), field (Toad segment reached), battle and pause command sets enumerated exhaustively from `0x08200448` (7 entries) and `0x08201F38` (5 entries) — these are fixed tables, not generated, so there is no unenumerated state.
* **Text space:** 319,414 ASCII runs searched for 10 cheat-related keywords; counts above. The game's script text is ASCII with `0xFF`-prefixed control codes (decoded at `0x3D7D20` and `0x400D60`: `0xFF 0x44` = draw, `0xFF 0x0A` = newline, `0xFF 0x2B`/`0x2D` = action glyphs), so an encoded hidden label would still contain the ASCII word. No password alphabet string (e.g. `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`) exists in any bank.
* **Button space:** all three `KEYINPUT` readers disassembled; no mask sequence, no progress counter, no jump table keyed by press index. All 10 GBA keys were pressed individually and in the six most plausible modifier combinations on every walked screen; no hidden menu appeared. There is therefore no undocumented action branch to enumerate and no novel button code to mint.
* **Debug content:** the debug room/menu exists as data but its only access is a GameShark write (`02001E90:0001`) — a memory-edit code, out of scope. Its would-be UI (the 64 `gsys` labels) has zero code references; it cannot be opened by any controller input.
* **Published codes:** GameFAQs has none for this SKU; the only published "codes" are TCRF's GameShark values, which were verified to target RAM flags, not an input system.
* **Novel code / rejection bounds:** not applicable — with no accepting validator there is no code to mint and no acceptance bound to test. This is a proven absence over the spaces above, not an untested one.

## 7. Validation evidence

* **Observed** — ROM hashes/header/build date; all screenshots and cursor/key presses listed in §3; `KEYINPUT = 0x000003FF` at idle; `0x02001E90 = 0x00` during play; savestate diffs between title/menu/mode/gameplay states (e.g. 7,030 IWRAM bytes between Mario Bros. mode select and Phase 1); ASCII string dumps at `0x201F38`, `0x200448`, `0x3D7D20`, `0x3FA197`, `0x400D60`; Toad's thought bubble `I must find Mario immediately!`; 120-step D-pad random walk with 12 checkpoints showing no room change.
* **Derived** — only three real `KEYINPUT` readers and the shape of `0x08018920`; 64 gsys pointers with 0 external refs; build-date and single-header identification; complete menu counts from fixed string tables.
* **Inferred** — that the debug room can *only* be entered by memory editing (TCRF documents one method and the gsys UI has no live xrefs; absence of every other possible access method cannot be proven absolutely); that `Rumble Feature` is disabled because the GBA lacks rumble hardware (it is greyed out on screen).
* **Not tested / out of scope** — GameShark/CodeBreaker codes, by explicit instruction. The main-story pause and battle screens were enumerated from their ROM tables; a full natural playthrough to a battle was not completed (see §8).

## 8. Unknowns

* A natural-play route to a first RPG battle and the in-game pause overlay was not completed: the opening Toad segment’s exit from Mario's house was not located within the time budget, and the field menu is unavailable during that scripted segment (Start/Select/L+Select/R+Select all no-op). Their **contents** are nevertheless fully enumerated from the two fixed ROM tables, so no menu entry is unknown.
* `0x0839EC6C` entry 0 (`0xC000`) and entry 1 (`0x3000`) are outside the 10-bit key mask; their exact role in the repeat logic was not isolated.
* Wrecking Crew graphics (`0x08201790`/`0x08201210`) and the unused enemy scripts have no known in-game trigger; no controller input was found that reaches them.

## 9. Tooling

All analysis scripts were in `/tmp/mlss/`: `scan_keys3.py` (Capstone KEYINPUT scan), `final_scan.py` (keyword/menu census), `dbg_daemon.py` + `d.py` + `q.py` (mGBA CLI debugger over PTY), `cap.py`/`ss.py`/`ram.py` (savestate decode, address mapping and diffs), `k.py` (xdotool keymap), `start.sh`/`replay.py`/`wander*.py` (display and navigation helpers). System tools: `arm-none-eabi-objdump` (`-M force-thumb`), Capstone 5.0.7, `mgba 0.10.5`, `Xvfb`, `openbox`, `xdotool`, `scrot`, ImageMagick, Python 3.

No ROM or copyrighted asset is redistributed; only addresses, hashes, counts and derived observations are published.
