# Noddy: A Day at Toyland (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Noddy: A Day at Toyland.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `NODDYTOYLAND` |
| Game code / maker | `BNKE` / `GY` |
| Version | `0x00` (file identifies `Rev.00`) |
| Entry branch | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| MD5 | `fe8aac1a517af3ea89fd680536962ddf` |
| SHA-1 | `b796262171986494f98b0c4ebe8a7c8ccf6b25a1` |
| SHA-256 | `f94864a50ea41b4ec457fcedf08a65d8cc154c6cc511c028bdf9cbb622fb2c53` |

Phase 0: exactly one Nintendo-logo occurrence (file `0x4`), so there is **no embedded
second header, no appended trainer, and no shell/cracktro**. Entry word is the stock
`0xEA00002E`. Header anomaly: checksum field at `0xBE` is `0x0000` and complement at
`0xBD` is `0xF8`, whereas the stock complement over `0xA0..0xBC` (sum `0x05EF`) would
be `0x11`. Per §16.1 this is the normal signature of a rebuilt/edited header; it does
not indicate a code patch — the executable first 4 KiB is a conventional crt0.

## 2. Executive summary

**There is no in-game cheat, password, button-code, unlockable, or hidden debug-menu
system in this GBA game.** The negative is proven by a complete walk of every reachable
screen (title, language select, main menu, Options, Level Select, Scrapbook, story
cutscenes, gameplay and the Start pause path) with RAM snapshots at each, plus an
exhaustive static search of the input/key-state code and the literal space.

The reachable UI is:

* language select (English / Français / Español)
* title screen — "Press START"
* main menu — **Play Game / Scrapbook / Level Select / Options**
* Options — Music ON/OFF, Sound FX ON/OFF, Difficulty NORMAL/…, B = Exit
* Level Select — freely available from a fresh boot; left/right arrows select a level,
  level name + preview art, A = Select, B = Back
* Scrapbook — static story/collection pages ("It is a new day in Toyland.")
* Play Game — introductory cutscenes, then gameplay; Start pauses

There is no password-entry field anywhere. The "level passwords" published for
*Noddy* are for the **Game Boy** title *Noddy and the Birthday Party* (character-name
codes such as "Tessie, Noddy, Big Ears, Tessie"), a different SKU and engine (§16.11).
The only codes published for this GBA SKU are CodeBreaker/GameShark raw memory patches,
which are explicitly out of scope; none of their literals appear in the ROM. A 3rd party cheat index
forum submission for this exact GBA game independently states that the level select is
available from the start and that the game has no unlockables and no 100% category.
That claim was treated as data and re-verified locally rather than trusted.

All visible text is stored as font/tile indices: `strings` finds **no** English UI words
at all (0 hits for password/cheat/code/debug/secret/unlock/level/options/scrapbook in
any of ASCII, UTF-16LE, UTF-16BE, `+0x20`, `-0x20`, or interleaved-NUL forms). The
negative therefore rests on the screen walk and on code/data analysis, not on strings.

## 3. How to reproduce

Toolchain: mGBA (SDL, `-d` CLI debugger), Xvfb `:316`, openbox, xdotool, scrot,
`arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, Python 3.

* Start: `Xvfb :316 -screen 0 1024x768x24 -nolisten tcp &`; `DISPLAY=:316 openbox &`;
  `SDL_AUDIODRIVER=dummy stdbuf -o0 mgba -d -3 "<rom>" < fifo > dbg_out 2>&1 &`.
  Keep a persistent FIFO writer (`sleep 100000 > fifo &`) so the debugger keeps reading.
* Keymap verified against `KEYINPUT` (`0x04000130`): A=`x` (`0x03FE`), B=`z`,
  Start=`Return`, D-pad = arrow keys. Hold a key while issuing several `frame`
  commands — key state is sampled only while the core is advancing.
* Debugger commands used: `frame` (single-step a frame, re-enters the command loop),
  `r/4 ADDR`, `x/4 ADDR COUNT` (bulk RAM/VRAM dump), `w/4 ADDR VALUE`, `status`.
  Do **not** issue `continue`: it permanently exits the CLI command loop in this
  build; use `frame` instead. Likewise delete breakpoints before resuming `frame`,
  or every frame re-trips the same breakpoint.
* Repro path: language select → A → title → Start → main menu. From the main menu,
  the selected entry is observable at `0x0203AF98` (`0`=Play Game, `1`=Scrapbook,
  `2`=Level Select, `3`=Options); Down/Up moves it, A enters, B exits.
* Codes tested: none exist to test. All published literals were searched (§6b).

Scripts used were in `/tmp/noddy/`: `send.sh`, `frames.sh`, `press.sh`,
`rd.py`, `ram.py`, `vramdump.py`, plus inline Python searches.

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x08000000` | ROM | Stock header; entry `0xEA00002E` |
| `0x080014F0` | code (Thumb) | Main-loop input polling routine |
| `0x08015AC` | literal pool | `0x04000130` (`KEYINPUT`) — the **only** such literal in the ROM |
| `0x0801544`–`0x080155A` | code | `held = ~KEYINPUT & 0xFFFF`; `pressed = held & ~prev`; writes globals below |
| `0x030010A0` | IWRAM | held keys, active-high (`A=1,B=2,Select=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,R=0x100,L=0x200`) |
| `0x030010A4` | IWRAM | newly-pressed keys (same mask convention) |
| `0x030010A8` | IWRAM | frame counter |
| `0x0203AF98` | EWRAM | main-menu cursor index `0..3` (observed 0→1→2→3 on Down presses) |
| `0x03002470`, `0x03002480` | IWRAM | screen/mode state words (differ between menu, Options, Level Select, gameplay) |
| `0x0801C180` | code | Gameplay frame handler; `0x0801C194` tests state `+0x2A==3` and `pressed & 0x8` (Start) → pause |
| `0x0801C210` | literal pool | `0x0801C511` — resume handler pushed on pause |
| `0x0801E180`–`0x0801E300` | code | Menu-option handlers; all test mask `0x3` (A or B) only |
| `0x0801EFA0`, `0x0801F084`, `0x0801FD60` | code | Other UI/gameplay input handlers; masks `0x1,0x2,0x8,0x10,0x20` only |

No password buffer, no validator function, no checksum routine, no hard-coded code
table, no key-sequence table, and no function-pointer dispatch to an unlabelled debug
screen were found. The state pointer written on pause is a UI push-state helper
(`0x801A2DC`), not a hidden screen.

## 5. Algorithm

Not applicable — the game has no code algorithm to reverse. Its only input algorithm is
the standard GBA edge detector at `0x08014F0`:

```
held    = ~KEYINPUT & 0xFFFF
pressed = held & ~prev_held
prev_held = held
frame_counter++
dispatch_to_game_callback(...)     # BL 0x080EF330
```

Every subsequent consumer of `held`/`pressed` tests **single buttons** (masks
`0x1, 0x2, 0x4, 0x8, 0x10, 0x20, 0x40, 0x80`) for ordinary menu/gameplay control.

## 6. Tables

| Table / item | Content |
|---|---|
| Main-menu cursor (`0x0203AF98`) | `0` Play Game, `1` Scrapbook, `2` Level Select, `3` Options |
| Options entries | Music, Sound FX, Difficulty; B = Exit |
| Level Select controls | ←/→ choose level, A Select, B Back; unlocked from boot |
| Key masks actually used | `0x1` A, `0x2` B, `0x3` A-or-B (menu confirm/back), `0x8` Start, `0x10` R, `0x20` L, `0x80` Down |
| Published GBA codes | none in-game; GameShark/CB raw patches only (out of scope), all literals absent from ROM |
| Published GB codes | character-name passwords for *Noddy and the Birthday Party* (GB) — different game; all literals absent from this ROM |

## 6b. Enumeration

**Space definition.** The code space is empty: 0 passwords, 0 button codes, 0
hidden screens, 0 unlockable flags. There is no alphabet, length, field width,
checksum, or lookup table to enumerate because no submit/validate surface exists.

**Screen enumeration (complete).** Every reachable screen was walked with RAM evidence:

1. Boot → language select (screenshot + `KEYINPUT` read).
2. Title "Press START" (screenshot).
3. Main menu (screenshot; `snap_menu.txt` full EWRAM/IWRAM dump; cursor `0x0203AF98`).
4. Options (screenshot; `snap_options.txt`; menu state `0x03002470=3`, `0x03002480=1`).
5. Level Select (screenshot; `snap_levelsel.txt` / `snap_levelsel_right1.txt`; arrow navigation changed level state `0x0300660C 0→2`).
6. Scrapbook (screenshot showing "It is a new day in Toyland."; RAM dump).
7. Play Game cutscenes (screenshots: "A NEW MORNING IN TOYLAND", "Time to wake up!").
8. Gameplay + Start pause path (`snap_prepause.txt` → `snap_pause.txt`, 1,712 words changed;
   pause handler `0x0801C194` disassembly proves Start, mask `0x8`, is the only trigger).

**Input/code-space enumeration.**

* `0x04000130` has exactly **one** literal reference in the whole 4 MiB image
  (`0x08015AC`), so there is a single input path and no alternative code-entry reader.
* The held/pressed globals have 7 and 17 literal readers respectively. All 20 sites
  were disassembled and classified: every multi-bit mask is `0x3` (A-or-B on menus,
  five sites) or the incidental `0xF` in a nibble operation at `0x08016E4`; all others
  are single buttons. **No multi-button gate, no sequence index, no mask table.**
* Button-code searches over the whole ROM (Konami code and reverse, A/B/Start/Select,
  L+R+A, Up-Up-A-B, etc.) as little-endian `u16` and `u8`, both active-high and
  active-low: only coincidental matches inside compressed graphics/audio, none in
  executable code regions.
* Password/keyword literal search: `password`, `cheat`, `code`, `debug`, `secret`,
  `unlock`, `bonus`, `congrat`, `level select`, `options`, `scrapbook`, `Tessie`,
  `Big Ears`, `Policeman` — **0 hits** in ASCII (case-insensitive), UTF-16LE/BE,
  `±0x20` shifted ASCII, and interleaved-NUL forms.
* Published literals verified **absent**: `987654321234`, `0961EA536912`,
  `157D4C6C5BEF`, `1C5348AACDF4`, `8AD0596E13D0` (GameShark/CB, out of scope) and all
  GB-title character-name codes.
* Simple tile-index text mappings (A=1..26 with space=27 etc., ASCII±delta over the
  full byte range) were brute-forced against the four visible menu labels: no ROM hit,
  so the text encoding is a non-trivial glyph-index map, not a trivial cipher.

**Novel codes and bounds-by-rejection.** Not applicable: with zero codes, there is no
space in which to mint one and no validator to reject an out-of-range field. The
equivalent bounded result is the positive enumeration above (all 8 screen classes,
all 20 key-state readers, all published literals) — every searched space was checked
and counted, not left untested.

## 7. Validation evidence

* **Observed** — 20 screenshots (within the media budget) of language select, title,
  main menu, Options, Level Select (two positions), Scrapbook, two cutscenes and
  gameplay; `KEYINPUT` transitions (`0x03FF` → `0x03FE` on A); full RAM snapshots
  (`snap_*.txt`) at menu, Options, Level Select, Scrapbook, pre-pause and pause; menu
  cursor progression `0→1→2→3`; VRAM/DISPCNT/BG register reads.
* **Derived** — single `KEYINPUT` literal; input edge-detector at `0x08014F0`; global
  key-state addresses; gameplay pause test at `0x0801C194`; classification of all 20
  key-state reader sites; absence of validator/table/code-pointer structures.
* **Inferred** — the header's `0x0000` checksum / `0xF8` complement indicate a rebuilt
  header (consistent with §16.1 but the release origin was not independently confirmed).

## 8. Unknowns (bounded)

* **Font/tile-indexed text bank not decoded.** The game's text is glyph-index based,
  not ASCII. An attempt was made to recover the font from VRAM using the CLI debugger:
  VRAM and BG registers were dumped at the mid-frame breakpoint `0x080EF330`
  (`DISPCNT=0x3340`, `BG0CNT=0x8029`). The captured VRAM contained only 16 nonzero
  tilemap words at `0x06000000` and tile banks rendered as uniform stripe patterns, so
  no glyph→index mapping could be established. The mGBA `-d` build also did not accept
  a savestate-file argument (`save`/`Shift+F1` produced no file), so a rendered-frame
  savestate could not be used as an alternative. **This does not weaken the result:**
  the negative is established by visually walking every screen, not by string search,
  and the static searches above cover the literal space directly.
* Exact total number of levels in Level Select was not counted (arrows, not a code
  surface); irrelevant to the cheat question.
* The pause screen's text was not captured visually (media budget exhausted); its
  existence and sole trigger are proven by the RAM transition and the disassembly of
  `0x0801C194`.

## 9. Tooling

Installed/used: `binutils-arm-none-eabi` (`arm-none-eabi-objdump`), mGBA SDL with `-d`
CLI debugger, Xvfb, openbox, xdotool, scrot, ImageMagick, Python 3 with Capstone 5.0.7
and Pillow, `stdbuf` for unbuffered debugger output. Analysis scripts are listed in §3
and stored under `/tmp/noddy/`.

No ROM or copyrighted assets are redistributed here; only hashes, addresses, and
procedure descriptions are published.

## 10. Cleanup

All processes started for this job (Xvfb `:316`, openbox, mGBA, FIFO holder) were
terminated by PID; no `pkill` was used. No `.sav`/`.ss*` files were created in the ROM
folder (the savestate attempt produced no file). `roms/INDEX.md` was not modified as
instructed.
