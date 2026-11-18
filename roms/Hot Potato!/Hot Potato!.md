# Hot Potato! (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Hot Potato!/Hot Potato!.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `HOT POTATO` |
| Game code / maker | `AHPE` / `6L` |
| Version / complement / checksum | `0x00` / `0xCF` / `0x0000` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0) |
| MD5 | `176da8ac357508b17baa922352a30568` |
| SHA-1 | `6d07c27f7d7858f177cf3c1466ea5a8858df4f92` |
| SHA-256 | `274f67f7ec5399ab9f8cc42542a21c55a2a1e83648d15bcddb22cb06825feb33` |

Retail licensed image: Pukka Games / BAM! Entertainment, 2001. One Nintendo-logo
header hit only (file offset 0), no appended trainer, no cracktro, no patch stub.
Entry word and first 4 KiB are stock (§16.1 clean).

## 2. Executive summary

**There is no reachable developer-intended cheat system in this SKU.** No password
screen, no button-code matcher, no level-select, and no hidden debug menu can be
reached through the game's own input on any screen.

The ROM *does* contain an unfinished/unreachable debug engine (guide §16.3,
category 2 "dead code"): a 36-state main dispatcher at `0x08008154`, a 7-option
"screen select" debug handler at `0x080099B0`, and a separate beta/dev text bank
at `0x0823A390` ("MAIN MENU", "INTRODUCTION", "START GAME", "OPTIONS",
"DIFFICULTY: EASY/MEDIUM/HARD", developer nicknames, a "DAMON BRANCH LICKS PIGS"
inside joke). Six code sites write the debug state `0x1A` into `0x030005F0`
(`0x08009624`, `0x08009836`, `0x08009878`, `0x08009E14`, `0x08009E30`,
`0x08009F9A`), but every one of them lives in a handler for a state that is
itself never written by any reachable path:

* state `0x19` (INTRO, `0x080095A0`) — **no writer exists at all**;
* state `0x1E` (`0x08097A8`) — written only from the debug handler itself;
* state `0x09` (`0x0809D34`) — its only non-debug writer (`0x080092B4`) sits in the
  state-`0x0B` handler, and state `0x0B` is likewise never written;
* state `0x17` (`0x0809F50`, Select-key gate) — its only writer (`0x080086D6`,
  Start on the state-`0x00` handler) never executed during a full input sweep.

I armed Thumb breakpoints on all five principal write sites and swept every
reachable screen with A, B, Select, Start, L, R, L+R, A+B, and an Up-Up-Down-Down-
Left-Right-Left-Right-B-A sequence: **zero breakpoint hits** (Observed). This is a
proven dead-code negative, not "not tested".

"ENTER YOUR NAME" is a high-score name field, not a password (§16.2b): its buffer
has no comparison consumer. The 512-byte save holds high scores and ordinary
progress/unlock bits (§16.18) — collectible/level unlockables, not a code system.

## 3. How to reproduce

* Emulator: `SDL_AUDIODRIVER=dummy mgba -3 <rom>` under `Xvfb :315 -screen 0 1024x768x24`
  with `openbox`. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrows. Hold keys 120–300 ms.
* Path: boot → A (clear "A Dima Pavlovsky Game" and "Licensed by Nintendo" splashes)
  → title "PRESS START" → Start → main menu
  (`MISSION GAME` / `SCORE GAME` / `OPTIONS`). From there:
  `MISSION GAME` → `MARS 1` mission intro → gameplay; `SCORE GAME` →
  `NEW SCORE GAME` / `LOAD SCORE GAME` / `BACK`; `OPTIONS` → `MUSIC IS ON`,
  `SFX ARE ON`, `CONTRAST 2`, `BACK`. In-game Start gives the pause/quit menu.
  None of these screens exposes a password/code entry surface.
* Codes tested: none published (see §6b). All button sequences listed in §2 were
  entered on every screen above; none changed the screen state to `0x1A`.
* RAM evidence method: `Shift+F1..F9` save a state; mGBA `.ssN` files are PNG with
  a zlib `gbAs` chunk; IWRAM lives at raw offset `0x19000 + (addr-0x03000000)`.
  Key mask register is `0x030005FC = ~KEYINPUT` (active-high).
  Debugger method: `mgba -d` on a PTY (`script -q -c ...` fed by a FIFO), set
  `b/t <addr>`, `c`, and the debugger halts and accepts `x/4`, `r/2`, `w/1`, etc.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x080000C0` | ARM crt0 entry |
| `0x08008154` | main 36-state dispatcher; reads byte `0x030005F0`, table at `0x08008174` |
| `0x08008174` | 36-entry function-pointer table (states 0–35) |
| `0x080098A4` | draws 4-item beta menu: MAIN MENU / INTRODUCTION / START GAME / OPTIONS |
| `0x080099B0` | 7-option debug/screen-select handler (state `0x1A`) |
| `0x08009A98` | 7-entry jump table for that menu |
| `0x08009F50` | state `0x17` handler; Select (`key & 4`) → state `0x1A`/`0x1B` |
| `0x080086D6` | only writer of state `0x17` (Start, `key & 8`) — never hit |
| `0x080092B4` | only non-debug writer of state `0x09` — in unreachable state `0x0B` handler |
| `0x08009624` | A/B key gate in unreachable state `0x19` handler → state `0x1A` |
| `0x0823A260`–`0x0823A390` | dev high-score name bank (`SUPERCLIVE`, `FUNKYDAMON`, …) |
| `0x0823A390`–`0x0823A550` | beta/dev menu string bank |
| `0x0835FA40`–`0x08360100` | normal UI text bank (ASCII) |
| `0x08000A60`–`0x08001400` | in-game message/tutorial bank (148 decoded strings) |
| `0x030005F0` | main screen-state byte (title `0x20`, main menu `0x22`, debug `0x1A`) |
| `0x030005EC` | screen-data pointer (e.g. `0x083815A4`, `0x0838156C`) |
| `0x030005FC` | key state, active-high: A=1 B=2 Select=4 Start=8 Right=0x10 Left=0x20 Up=0x40 Down=0x80 R=0x100 L=0x200 |
| `0x030023E4` | menu selection index (0=MISSION, 1=SCORE, 2=OPTIONS) — RAM-verified |
| `0x030005E8` | menu transition flag |

## 5. Algorithm

No password/checksum algorithm exists. The only relevant logic is the dispatcher:

```
state = byte[0x030005F0]              # 0..35
if state <= 35: pc = table[0x08008174][state]   # mov pc, r0
```

The unreachable debug gate in the state-`0x17` handler (`0x08009F6A`):

```
keys = halfword[0x030005FC]           # ~KEYINPUT, active-high
if keys & 0x04:                        # Select
    flag[0x030005E8] = 1
    state = 0x1A if halfword[0x030023E8] == 0 else 0x1B
    ptr[0x030005EC] = 0x0838156C
```

The seven debug-menu actions at `0x08009A98` set states 32 (main menu), 27, 30,
3, etc. — i.e. it is a screen-select menu, not a cheat/menu of prizes.

## 6. Tables

Key masks (active-high at `0x030005FC`, confirmed by holding Right:
`0xFC00 → 0xFC10`): A `0x001`, B `0x002`, Select `0x004`, Start `0x008`,
Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`, R `0x100`, L `0x200`.

Debug menu jump table at `0x08009A98` (all seven entries):
`0x08009A9C`, `0x08009AB8`, `0x08009AE0`, `0x08009AE0`, `0x08009AEC`,
`0x08009B30`, `0x08009B10`.

State values actually written anywhere in the ROM (from a Capstone scan of all
LDR-literals of `0x030005F0` followed by `movs`/`strb`):
`0, 1, 2, 3, 9, 23(0x17), 26(0x1A), 27, 32, 33, 34, 35`.
Not written: `4–8, 10–22, 24, 25, 28–31` — including three of the four states
whose handlers gate the debug screen.

## 6b. Enumeration

**Code space:** empty — no password system, no cheat table, no button-code table,
no level-select code. Consequently there is no novel code to mint and no bounds to
prove by rejection; the negative itself is bounded below.

**Text/button spaces searched (with counts):**
* Full 4 MiB searched in case-folded ASCII, `A-Z→a-z` translation, and UTF-16LE.
  Keyword counts: `password`=0, `cheat`=0, `secret`=0, `unlock`=0, `debug`=0,
  `code`=0, `level select`=0, `warp`=0, `hidden`=0, `game shark`=0,
  `codebreaker`=0. Hits only for ordinary UI: `main menu`=1 (`0x23A3E8`),
  `options`=3 (`0x23A410`, `0x23A4B4`, `0x35FA90`), `enter your name`=6
  (high-score entry, e.g. `0xAD3`).
* In-game message bank `0x0A60`–`0x1400` decoded (control bytes stripped):
  148 printable strings, all scoring/tutorial/results text; zero password/code words.
* Button-code table scan: all 2-byte-aligned runs of 2–3-bit key masks in the
  code region produced 1,852 candidates; all examined hits lie in sample/graphic
  data and have **no code xref**. Zero comparator tables against `0x030005FC`
  sequences were found.
* Published codes: GameFAQs cheats page for GBA id 525413 returned HTTP 403 both
  directly and through a text proxy; web searches of GameFAQs, TCRF, VGChartz,
  and general engines returned only sales/review/boxart/video pages — **no
  published password or button code for this SKU**. (The "Hot Potato" hit on a TCRF
  user sandbox concerns the unrelated GB game *Sabotage* and was ignored as data.)
  With no published literal, there was nothing to verify against the ROM; §3
  button sweeps cover the alternative.
* Dead-menu proof: breakpoints at `0x08009624`, `0x08009836`, `0x08009878`,
  `0x08009E14`, `0x08009E30` and `0x080086D6` were armed from a clean boot and
  across a full menu/pause/gameplay input sweep — **0 hits**. A sixth site
  (`0x08009F9A`) is in the state-`0x17` handler, whose sole writer is the equally
  unhit `0x080086D6`.

## 7. Validation evidence

* **Observed** — ROM hashes/header; single logo header; all menu screenshots;
  savestate RAM reads (`0x030005F0=0x20` title, `0x22` main menus; `0x030023E4`
  moved 0→1→2 with the cursor); key register diff (`0xFC00→0xFC10` on Right);
  breakpoint non-firing; 512-byte save with default `TOH.1…` high scores.
* **Derived** — dispatcher and jump tables from Thumb disassembly with literal
  pointers re-read via Python (avoiding objdump's split-halfword trap); the six
  state-`0x1A` write sites and their impossible predecessor states; the key-mask
  meanings from the `ands` immediates at the gate sites.
* **Inferred** — the `0x23Axxx` string bank and the state-`0x1A` menu are leftover
  beta/debug content, not a shipped feature; the progress bits in the save are
  normal gameplay unlockables rather than cheat flags.

## 8. Unknowns

* `halfword[0x030023E8]` selects `0x1A` vs `0x1B` in the dead Select gate; its
  producer was not isolated (irrelevant while the gate is unreachable).
* Whether unusual conditions (link cable, specific save state, hardware reset
  timing) could satisfy the unreachable predecessor states; no such condition
  was found in ROM code reachable from the title screen.
* The high-score name buffer's full consumer set was not exhaustively traced;
  no string comparison against it other than score formatting was observed.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `strings -t x`, `xxd`, Python 3 with
Capstone 5.0.7 (custom `findwrite3.py`, `allstates.py`, `disas.py`,
`patchstate.py`, `cap.py`, `state.py`), `arm-none-eabi-objdump -M force-thumb`,
`Xvfb :315` + `openbox` + `xdotool` + `scrot`/ImageMagick, mGBA 0.10 SDL
(`-3`, `-d` CLI debugger over a `script` PTY + FIFO), mGBA savestate `gbAs`
extractor. No ROM or copyrighted assets are redistributed; only hashes,
addresses, and original analysis scripts are published.
