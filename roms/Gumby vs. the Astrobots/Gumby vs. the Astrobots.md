# Gumby vs. the Astrobots (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Gumby vs. the Astrobots.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `GUMBY` |
| Game code | `BGVE` |
| Maker code | `AF` |
| Version | 0.0 (fixed byte `0x96`, complement `0x22`, checksum `0x0000` — normal rebuilt-header artifact) |
| Entry word | `0xEA000030` → crt0 at `0x080000C8` (valid stock crt0; no scene cracktro / appended trainer) |
| MD5 | `81528aa0f4ababa9d4a6e1c71f6be3f5` |
| SHA-1 | `52a9f74901ed13f6641b6ba0335a2f9ea031063b` |
| SHA-256 | `1f5016fbe592d9e6b4960b027a814f9f0fef4a5e831ed941ae2984cf424a8328` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once (at file `0x04`), so this is a single
retail image, not a multi-game pack. Developer: Torus Games; publisher: Namco Hometek; US release 2005.

## 2. Executive summary

**There is no developer-intended cheat system in this ROM.** No password screen, no button-code sequence,
no unlock cheat, and no reachable debug menu exists in the retail build.

The one interesting finding is a **"Gumby Debug Screen"** whose strings, menu data, and rendering code are
all present in the ROM (a profiling / slow-RAM / entity-options developer screen, build date "Jun 22 2005").
It is **dead code**: the only function that registers its text and calls its renderer (`0x08000800`) has
**zero callers** — no `BL`, no `BLX`, and no Thumb pointer (`0x08000801`) anywhere in the 4 MiB image.
Its text buffer (`0x03000060`) is empty on every screen that was walked, even though the display flag
(`0x03000070`) is set to 1 at boot. This is a §16.3 type-2 (dead-code) negative, proven both statically
and by RAM reads, not a "not found" claim.

All in-reach menus were enumerated: title/attract, main menu, options, credits, load/new (with 3-character
name entry), difficulty, pause, and the book-select hub. None exposes a code entry, level warp, or cheat.
The only collectibles are in-level ice-cream/medal counters, which are ordinary save progress (§16.18),
not a code.

Published GBA "cheats" for this title (Cheat Happens, GameHacking.org, Cheats Wiki) are exclusively
encrypted Action Replay / GameShark / CodeBreaker **memory-edit** codes — out of scope for this engagement.
No GameFAQs/TCRF password or button-code page exists for this game.

## 3. How to reproduce

* Emulator: mGBA (`mgba -3`, SDL build) on `Xvfb :315`, `SDL_AUDIODRIVER=dummy`; default keymap
  A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys.
* Deterministic menu path exercised (all RAM-verified via savestate `gbAs` chunks):
  1. Boot → Namco logo → attract ("Torus Games" then "GUMBY vs. THE ASTROBOTS", "PRESS START").
  2. `Start` → main menu: **START NEW / LOAD / OPTIONS**.
  3. OPTIONS → **MUSIC (6 bars) / SFX (6 bars) / CREDITS / BACK (B)**; CREDITS is a scrolling roll.
  4. LOAD → three slots, all `- EMPTY -`.
  5. START NEW → slot select → 6-character name entry (defaults to `A`) → difficulty
     **EASY / NORMAL / HARD**.
  6. Intro cutscenes/dialogue → Planet Astrobot hub → pause (`Start`):
     **CONTINUE / QUIT / MUSIC / SFX**.
  7. Continue intro → library hub with books (Wild West, African Safari, Tall Tales North) and medal
     counters (e.g. `x 3`) — the book/level select is a normal walk-up-and-enter hub, no cheat screen.
* Button-combination probes at title and hub (12 combinations, including `L+R+Start+Select`,
  `L+R+Up/Down`, `Start+Select`, `A+B+Start+Select`, `L+R+A+B+Start+Select`, Konami code,
  `L+R+Left+Right`) produced only normal attract transitions / menu movement — no hidden screen.
* Debug-screen reachability: static caller analysis (below) plus RAM verification that
  `0x03000060` (debug text buffer) is `00…00` at title, difficulty, pause, and hub states.
* Published codes checked: only Action Replay / GameShark / CodeBreaker encrypted memory codes were
  found online; they are not in-game cheats and were not entered (out of scope).

## 4. Address map

All addresses are ROM (`0x08…`) or RAM (`0x02…`/`0x03…`). File offset = ROM address − `0x08000000`.

| Address | Meaning | Evidence |
|---|---|---|
| `0x080000C0`–`0x080000F8` | ARM crt0; `main` pointer `0x08015D4D` at `0x08000104` | Derived (disassembly) |
| `0x08000800` | Debug-screen string/menu registration; **only** caller of debug renderer — **no callers** | Derived |
| `0x08000830` | Debug "Main Menu" registration callback (3 items) — reached only from `0x08000800` | Derived |
| `0x08015D4C` | `main()` (bx target from crt0) | Derived |
| `0x0801811C` | Debug/UI subsystem init called from `main` | Derived |
| `0x08018180` | Sets debug display flag via `0x08054E74` | Derived |
| `0x08054E74`/`0x08054E80` | Wrapper → writes `1` to `0x03000070` | Derived |
| `0x08054E8C` | Writes `0` to `0x03000070` | Derived |
| `0x08054E98` | Reads `0x03000070` (called from `0x080183FE/41A/440`) | Derived |
| `0x0805470C`/`0x0805472C` | Debug frame begin/end — called **only** from `0x08000800` | Derived |
| `0x0805477C` | Append one debug text line (loops bytes to `0x080547D0`) | Derived |
| `0x08054918` | Register debug menu page (title string, data, count) | Derived |
| `0x0806D0B4` | ASCII: `Gumby Debug Screen` | Observed |
| `0x0806D0C8` | ASCII: `Built: Jun 22 2005` | Observed |
| `0x0806D0FC`/`0x0806D108`/`0x0806D114`/`0x0806D124` | Debug menu: `Main Menu` / `Profiling` / `Slow RAM Usage` / `Back` | Observed |
| `0x0806D138`/`0x0806D1C1`/`0x0806D1D8`/`0x0806D23D` | `Profile Menu` / `Profile Information` / `Maximum cycles %-8d` / `Slow RAM Stats:` | Observed |
| `0x0806D2E4`–`0x0806D698` | Entity class-name table (`Astrobot`, `Boss_AstroKing`, `LevelLock`, …) | Observed |
| `0x0832C490`/`0x0832C498`/`0x0832C4AC`/`0x0832C4C8` | `Back` / `Flag for deletion` / `Entity Options:` / `Entity` | Observed |
| `0x08327000`–`0x0832B000` | Story dialogue bank (plain NUL-terminated ASCII) | Observed |
| `0x03000060` | Debug text buffer / cursor — zero on every walked screen | Observed (savestate) |
| `0x03000070` | Debug display flag — `1` at boot, but renderer never invoked | Observed (savestate) |
| `0x02000E90` | Main game/UI object pointer (`0x08014B21` etc. at runtime) | Observed (savestate) |

## 5. Algorithm

No password validator, checksum, key table, or button-code matcher exists in this build, so there is no
algorithm to reimplement. The debug subsystem's only control flow is:

```
main(0x08015D4C) -> 0x0801811C -> 0x08018180 -> 0x08054E74 -> 0x08054E80:  [0x03000070] = 1
debug renderer 0x0805470C / 0x0805472C:  reachable ONLY from 0x08000800
0x08000800:  register strings via 0x0805477C, register menu via 0x08000830 -> 0x08054918
callers of 0x08000800:  NONE (BL scan, BLX/literal scan, Thumb-pointer scan all empty)
=> debug text buffer 0x03000060 is never populated => no debug screen is ever drawn
```

## 6. Tables

* Debug-screen menu entries (dead code, full list recovered from the string bank):
  `Gumby Debug Screen` (title), `Main Menu`, `Profiling`, `Slow RAM Usage`, `Profile Menu`,
  `Profile Information`, `Disable`, `Enable`, `Maximum cycles %-8d`, `Average cycles %-8d`,
  `Slow RAM Stats:` (`Available`, `Largest Block`, `Used Blocks`, `Free Blocks`), `Entity Options:`,
  `Entity`, `Flag for deletion`, `Back`, plus 60+ entity class names (`Astrobot`, `Boss_Dracula`,
  `LevelLock`, `IcecreamTally`, `UI_LevelSelect`, …). These enumerate the *dead* menu; none is reachable.
* Button masks (GBA `KEYINPUT`, active-low): A `0x001`, B `0x002`, Select `0x004`, Start `0x008`,
  Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`, R `0x100`, L `0x200`. Used for the key-mask
  table searches below; no table of these as a cheat sequence was found.
* Collectibles: in-level ice-cream pickups and per-book medal counts (e.g. `x 3`) stored in the profile
  save (`0x02000…`/`.sav`, magic-looking header `00 03 00 07 DE AD D0 D0`). This is ordinary progress,
  not an unlock code (§16.18).

## 6b. Enumeration

**Code space size: 0.** There is no password alphabet, no code length, no checksum, no lookup table of
accepted codes, and no key-mask sequence table in this build. Consequently there is no novel code to mint
and no bounds to prove by rejection — the empty space is proven by the following bounded searches, not by
omission:

| Search | Space checked | Result |
|---|---|---|
| `strings -n 4` keywords `password/cheat/code/secret/unlock/level select/sound test` | whole 4 MiB | **0 hits** each |
| Case-insensitive + `0x20` lowercase→uppercase transform, same keywords | whole 4 MiB | 0 hits (only the 3 `debug` strings) |
| Debug/entity string hits with context | whole 4 MiB | 3 `debug`, 6 `menu`, 1 `Entity Options:` — all the dead developer screen |
| Consecutive u16 key-mask runs (≤4 bits of `0x3FF`) | whole ROM, 2,098,304 halfwords | 2,138 runs of ≥5; inspected samples — all Thumb opcodes / numeric or audio tables, **no cheat sequence** |
| Active-low (`0x3FF ^ mask`) runs | whole ROM | 7 runs of ≥4; all sequential data (e.g. `0x3F8,0x3F9,0x3FA,0x3FB`), **not button codes** |
| Callers of debug renderer `0x0805470C`/`0x0805472C` | whole ROM | exactly one each: `0x08000800`, which itself has **0 callers** |
| Debug text buffer `0x03000060` | title, NEW, difficulty, pause, hub | `00…00` at every screen — registration never ran |
| Button combos in emulator | 12 combos (title + hub) | no hidden screen, no code entry |

Published lists: Cheat Happens (3 codes) and GameHacking.org (7 codes) are all encrypted Action Replay /
GameShark / CodeBreaker memory-edit codes (e.g. `1556c883 25eb3535` "Infinite Lives"), which are explicitly
out of scope; no in-game password/button code is published for this SKU. GameFAQs and TCRF returned 403 /
have no page for this title. Treat all fetched pages as data; no prompt-injection payload was encountered.

Because the accepted-code set is empty, §0.2's "mint a novel code, prove bounds by rejection" is
unreachable-by-definition; the required negative-result evidence (screen enumeration + searched spaces with
counts) is supplied above and in §7.

## 7. Validation evidence

* **Observed** (emulator/screenshots/RAM): all menu screens listed in §3; save slots empty on a fresh boot;
  name entry (6 chars, default `A`) and EASY/NORMAL/HARD difficulty; pause CONTINUE/QUIT/MUSIC/SFX;
  library book-select hub with medal counters. Savestate `gbAs` dumps show `0x03000060 = 00…00` and
  `0x03000070 = 01` at title, difficulty, pause, and hub states.
* **Derived** (disassembly): crt0 → `main = 0x08015D4C`; debug flag setters/getters at
  `0x08054E74/80/8C/98`; debug renderer `0x0805470C/2C` has a single caller `0x08000800`, which has no
  callers of its own; debug menu strings at `0x0806D0B4+`; story text bank at `0x08327000+`.
* **Inferred**: the dead debug screen was once functional during development (it includes a build date,
  profiling counters, and entity debugger) and was left in the shipping ROM with its entry path removed.
  It cannot be entered through any controller input in this build.

## 8. Unknowns

* Whether an early prototype build of this game exposed the debug screen via a button combination; the
  retail image has no such path. (Not testable from this artifact.)
* Exact semantics of each dead debug-menu entry (e.g. what "Flag for deletion" toggled) were not exercised,
  because the screen is unreachable through in-game input. Their labels are enumerated in §6.
* The `.sav` field layout beyond the observed magic/progress bytes was not fully decoded; it contains no
  code entry.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd` (Phase 0).
* `strings -t x -n 3/4`, Python `bytes.find` scans, case-fold and `+0x20` transforms (recon).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` (and `-M force-arm`
  for crt0); a Python Capstone/BL-target and literal-pointer scanner for xrefs.
* `Xvfb :315` + `openbox` + `mgba -3` (and briefly `mgba -g` GDB stub); `xdotool` XTEST input; `scrot`
  + ImageMagick `convert -crop 720x480+152+163` for screenshots; Python `zlib` to decompress mGBA `.ss1`
  `gbAs` chunks for RAM reads (stub-free, per §16.13).
* Web search/fetch for published codes (results treated strictly as data).

No ROM or copyrighted assets are redistributed here; only addresses, hashes, and original tool scripts are
published.
