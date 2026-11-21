# Yu-Gi-Oh! Dungeon Dice Monsters (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Yu-Gi-Oh! Dungeon Dice Monsters.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `YU-GI-OH DDM` |
| Game code | `AYDE` (region: A = USA) |
| Maker code | `A4` (Konami) |
| Revision | `Rev.00` (header version byte `0x00`) |
| Entry word | `0xEA00002E` — stock `b 0x080000C0` (no cracktro/trainer patch; §16.1 check passes) |
| Header fixed byte | `0x96` at `0xB2`, complement check `0x95` at `0xBD` |
| MD5 | `1ac4901f9a831d6b86ca776bb61f8d8b` |
| SHA-1 | `fdd69455a072b2f74e6c5c50b96daa0438156b27` |
| SHA-256 | `298bb77f816272c4e0bb7ab2c75f31f7270621b07e43db2d5198357a4c7b2cb0` |

**Verdict:** bounded negative (§0.2 case 5). No in-game password system, button-code
sequence, hidden/debug menu, unlockable-code surface, or alphabetic validator exists
in this exact image. The one text-entry surface is a **player-name field**, proven by
its consumer (§16.2b): it is echoed verbatim on a "Name: … / Okay / Cancel" confirm
screen and never compared against a table.

## 2. Executive summary

Yu-Gi-Oh! Dungeon Dice Monsters (Konami, 2001) has **no developer-intended cheat
system**. There is no password entry screen, no published code list that maps to this
SKU, no button-code mask table, no reachable debug menu, and no validator function.

Evidence, in decreasing strength:

1. **Observed — full screen walk.** Every reachable screen was visited in mGBA and
   screenshotted: language select, intro, 10-slot name entry + confirm, and the main
   menu with all **six** entries (Dice Pool, Tournament, Free Duel, Link Duel, Trade,
   Grandpa's Shop) and each of their sub-screens. No code/password/options/debug entry
   exists anywhere. The main-menu selector ring was walked past its end and wrapped
   back to index 1 after exactly 6 Down presses — ring size is 6, all six slots are
   labelled, none are hidden (contrast §16.17).
2. **Derived — exhaustive static search.** The entire 8 MiB file was searched for
   alphabet strings, password/cheat/debug keywords, and button-code mask sequences in
   ASCII, `+0x20`, lowercase, UTF-16LE and UTF-16BE: **zero** hits for every pattern
   (§6b for counts). Ghidra auto-analysis found 106 defined strings; *all* 106 are
   ASCII `printf`-style development-log format strings in one bank at
   `0x08059AB4–0x0805A3A4`; none is a code, menu label, or alphabet.
3. **Derived — debug infrastructure is inert.** The 91 log strings are called through
   the common debug-print wrapper at `0x08025D30`, whose entire body is
   `0F B4 04 B0 70 47 00 00` = Thumb `push {r0,r1,r2,r3}; add sp,#0x10; bx lr`.
   It discards its arguments and returns immediately — a stub, not a live debug
   overlay (§16.3 "dead code"). 175 call sites reach this no-op; none produce output.
4. **Observed — input path is ordinary.** The joypad reader at `0x08027E00` reads
   `0x04000130` and writes a standard held/pressed/repeat state machine to
   `0x030008E8` (`+2` held, `+4` previous, `+6` pressed, `+8` held|repeat). No
   sequence accumulator, no mask-history table, and no comparison against a
   multi-button constant was found in its callers.

Because no validator exists, §0.2 items 3–4 (novel code / rejection bounds) are
**not applicable**; the bounded negative below supplies the required counts and
search-space enumeration instead.

## 3. How to reproduce

```
export DISPLAY=:316
SDL_AUDIODRIVER=dummy mgba -3 game.gba        # or: mgba -3 -g game.gba
# keymap: A=x, B=z, L=a, R=s, Start=Return, Select=BackSpace, D-pad=arrows
```

Menu path observed:

1. Language select → `A` on English (US flag).
2. Intro cutscene → press `A` ~7 times to skip.
3. Name entry (10 masked slots, on-screen alphabet QWERTY-style grid) → `Start`
   jumps the cursor to `END`; `A` confirms, then `A` confirms `Okay`.
   The typed value is echoed as `Name: AAAAY` — this is a name, not a code.
4. Main menu (6 items). Press `Down` repeatedly: the selector wraps after the
   6th item, never revealing a 7th. Each item opens the screens listed in §7.

Savestate `game.ss1` (in the work dir, **not** the ROM folder) was taken at the
main menu; `F1` reloads it, making each submenu walk one keypress.

Web reconnaissance (§3.4) was attempted against GameFAQs, TCRF, Bing, DuckDuckGo,
Google and the Wayback Machine; all returned 403/503/captcha or irrelevant generic
"dungeon" results. **No published code for this SKU was found or verified** — this is
recorded as a negative result, not silently omitted.

## 4. Address map

| Address (ROM) | File offset | Meaning | Evidence |
|---|---:|---|---|
| `0x08000000` | `0x000000` | Stock entry `b 0x080000C0` | Observed (header) |
| `0x08025D30` | `0x025D30` | Debug-print **stub** (no-op) | Derived (disassembly) |
| `0x08027E00` | `0x027E00` | Joypad reader; `ldr r1,[0x04000130]`, `and #0x3FF` | Derived |
| `0x08027E48` | `0x027E48` | Literal `0x030008E8` — input-state base pointer | Derived |
| `0x08035478` | `0x035478` | Example debug call: `ldr r0,[pc,#48]` → `"TRADE STAT"` | Derived |
| `0x08059AB4` | `0x059AB4` | Start of debug-log format-string bank (91 strings) | Observed |
| `0x0805A3A4` | `0x05A3A4` | `"TRADE STAT\n"` — last string in bank | Observed |
| `0x8058A8C` | `0x058A8C` | Frequent call target in early code (utility) | Derived |

| RAM | Meaning | Evidence |
|---|---|---|
| `0x030008E8 +2` | Held key mask, active-high (`A=1,B=2,Select=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,R=0x100,L=0x200`) | Derived |
| `0x030008E8 +4` | Previous held mask | Derived |
| `0x030008E8 +6` | Newly-pressed mask | Derived |
| `0x030008E8 +8` | Held | auto-repeat | Derived |
| `0x030008F2` | 10-byte name-entry slot array (observed empty-slot filler `0x10`) | Observed |
| `0x0E000000` | Flash save, 64 KiB (`.sav` in work dir) | Observed |

**Note on pointers:** literal at file `0x27E48` is bytes `e8 08 00 03` →
`0x030008E8`; literal at file `0x354AC` is `a4 a3 05 08` → `0x0805A3A4`.
Both were re-read with `struct.unpack_from('<I', …)` before use (§11).

## 5. Algorithm

Not applicable — no validator, encoder, checksum, or comparison table exists.

The only algorithmic finding is the shape of the debug-log call path:

```
caller (e.g. 0x08035478):
    ldr r0, [pc, #48]      @ 0x080354AC -> 0x0805A3A4 ("TRADE STAT\n")
    bl  0x08025D30         @ debug print

0x08025D30:
    0FB4    push {r0,r1,r2,r3}
    04B0    add  sp, #0x10
    7047    bx   lr
```

This is a compiled-out log sink. It is present in 175 call sites but produces no
side effect, so it cannot expose a debug menu or a code entry point.

## 6. Tables

### 6.1 Main menu (6 entries, ring size 6 — observed)

| Index | Label | Sub-screen observed |
|---:|---|---|
| 0 | Dice Pool | Duel board with three dice tokens and a `POOL` cursor |
| 1 | Tournament | Cup bracket selection (`Lunch Selects Cup`, `Joker's Carnival Fun`, …) |
| 2 | Free Duel | Deck/board selection screen |
| 3 | Link Duel | `"Connecting, please wait."` — link-cable only, no code entry |
| 4 | Trade | Board with `SET` cursor; link trade, no code entry |
| 5 | Grandpa's Shop | Character dialogue → buy screen with purchasable dice |

None of these screens contains a password/code field, a debug menu, or an
unlockable list. The only text entry in the whole game is in §6.2.

### 6.2 Name entry — NOT a password field (§16.2b)

* 10 slots, on-screen keyboard: `A–K / L–V / WXYZ`, `a–k / l–v / wxyz`,
  `1–9 0`, and `+ - 0 / & $ % ? ! . ,`; `Start` focuses `END`.
* Confirmed by consumer: the buffer is echoed on a `Name: <value>` / `Okay` /
  `Cancel` confirm screen (screenshot `after_end.png`) and then used as the
  player name. No `strcmp`/`memcmp` against the entry buffer exists, and the
  buffer is never read outside the entry/confirm flow.
* Alphabet strings do **not** exist in ROM under any tested encoding (§6b), so the
  grid is generated procedurally by a character-code loop, not decoded from a
  password table.

### 6.3 Debug-log format-string bank (0x08059AB4–0x0805A3A4, 91 strings)

Representative entries: `" Dice %d Player %d\n"`, `"SpcFlag %x\n"`,
`"Set DiceRoll  "`, `"Error Sync!!\n"`, `"CPU Item %d\n"`,
`"*** SetDuelCondition  %d %d (Init %d) ***\n"`, `"Non SaveDat\n"`,
`"SaveDat Put\n"`, `"Make SaveDat\n"`, `"Over SprDma\n"`, `"DMA Req Over\n"`,
`"_ENDING %d"`, `"TRADE STAT\n"`. These are development diagnostics, not UI.

## 6b. Enumeration

This section is mandatory (§0.2). For this ROM the code space is **empty**;
the enumeration is the search space that was checked to establish that.

### Search-space counts (all derived from the exact 8 MiB image)

| Space checked | Method | Size | Hits relevant to cheats |
|---|---|---:|---:|
| All printable strings | `strings -t x -n 4 game.gba` | 217,006 lines | 0 password/cheat/code/secret/unlock/debug-menu strings |
| Ghidra defined strings | `list_strings` | 106 | 106/106 are debug `printf` formats in one bank; 0 codes |
| Debug format-string bank | byte scan `0x59AB4–0x5A400` | 91 strings | 91/91 diagnostics; 0 menu labels/alphabets |
| `password`/`cheat`/`code`/`secret`/`unlock`/`debug`/`master`/`gamegenie` | literal, case-sensitive, whole 8 MiB | 8 patterns × 1 encoding | **0** each |
| Same, `+0x20` and `-0x20` shifts | byte transform | 16 patterns | **0** each |
| `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `abcdefghijklmnopqrstuvwxyz`, `0123456789`, `BCDFGHJKLMNPQRSTVWXYZ`, `…0123456789` | literal | 5 alphabets | **0** each |
| `"DICE POOL"`, `"TOURNAMENT"`, `"FREE DUEL"`, `"GRANDPA"`, `"PRESS START"`, `"ENTER CODE"` | ASCII, `+0x20`, `-0x20`, UTF-16LE, UTF-16BE | 6 words × 5 encodings | **0** each (UI text is tile-index encoded) |
| 26-byte ascending runs (step 1) | byte scan | whole file | 8 hits, all inside compressed/graphics data at `0x087CD973+`; none an alphabet |
| Konami sequence `U U D D L R L R B A` | u8 and u16 little-endian masks | 2 patterns | **0** |
| `L+R+Start` (`03 00 09 00`), `Start+Select+A+B` (`0f 00`) | u16 masks | 2 patterns | **0** |
| `L+R+A` (`03 00 01 00`) | u16 mask | 1 pattern | 21 hits, all coincidental data bytes in compressed banks; 0 in code/literal pools |
| Main-menu selector ring | observed cursor wrap in mGBA | 6 slots | 6 labelled entries, 0 hidden |
| Reachable screens | manual walk in mGBA | 12 screens (language, intro, name entry, confirm, main menu, 6 sub-screens) | 0 code-entry surfaces |
| Joypad sequence state | Ghidra decompile of `0x08027E00` caller set | 1 reader, 1 caller in main loop | 0 history buffers, 0 mask-code comparisons |

### Consequences for §0.2

1. **Space definition:** no alphabet, length, checksum, field widths, or lookup table
   exist. Representable values = 0. The name field is a 10-character label; its
   "space" is unbounded user text with no validity predicate.
2. **Validator model:** none. There is no function to reimplement, so no offline
   accept/reject oracle can be built.
3. **Novel code:** none can be minted — there is no encoding to invert. This is a
   structural property of the ROM, not an untested hypothesis.
4. **Rejection bounds:** not applicable for the same reason.
5. **Negative result bounded:** the tables above define the exact searched spaces.
   Absence of a code system is a statement about the full 8 MiB file (strings,
   masks, literal encodings), the complete set of 106 defined strings, the complete
   Ghidra procedure inventory (1,047 procedures), and every reachable screen — not
   a failure to look.

### Distinguishing the four "no"s (§16.3)

This is **case 1, "no system"**: there is no alphabet, table, validator or entry
surface. It is *not* merely dead code — the debug-log strings are dead (no-op sink),
but even if they were live they are diagnostics, not a cheat. It is *not* a cut
feature (no `TEMP` placeholders or unreachable code rows). It is *not* a gated
feature (no RAM byte/scene flag guards a hidden menu; all 6 menu slots are reachable
from a fresh save).

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| ROM identity / hashes | Observed | `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd -l 0x100` |
| Stock entry branch | Observed | Header word `2e 00 00 ea` at file `0x0` |
| 6 main-menu entries, no hidden slot | Observed | `menu_down1.png`, `menu_wrap.png`; 7 Down presses from index 0 land on index 1 |
| All six sub-screens contain no code entry | Observed | `sub_dicepool.png`, `sub_tournament.png`, `sub_freeduel.png`, `sub_linkduel.png`, `sub_trade.png`, `shop_menu.png` |
| Name field is a label, not a validator | Observed + Derived | `after_end.png` shows `Name: AAAAY` echoed on confirm; buffer read only by entry/confirm flow |
| Debug print is a no-op stub | Derived | `xxd -g2 -s 0x25D30`: `0f b4 04 b0 70 47 00 00`; objdump: `push {r0,r1,r2,r3}; add sp,#0x10; bx lr` |
| 106 defined strings, all diagnostics | Derived | `tools.rea.list_strings` (Ghidra 12.1.4) |
| 0 alphabet/password strings in any encoding | Derived | exhaustive Python scans (§6b counts) |
| Joypad state machine at `0x030008E8` | Derived | disassembly of `0x08027E00` + `xrefs` → single caller `0x0802CE22` in main loop |
| Save is 64 KiB Flash with 0x1000 mirrored pages | Observed | `game.sav` (65536 bytes), repeated page pattern with 16-bit checksums at `0x0FFE`, `0x1FFE`, … |

Labels follow §8: **Observed** = emulator screenshot / memory read / hash;
**Derived** = instruction sequence or exhaustive scan; **Inferred** = none in the
load-bearing claims.

## 8. Unknowns

* The game's menu text is stored as font/tile indices, not ASCII. Direct, `±0x20`,
  and UTF-16 searches for visible phrases returned zero. The font-to-character
  mapping was not fully decoded (the on-screen keyboard is generated by a character
  loop, so no alphabet string exists to anchor it). This limits a *textual* proof
  that no hidden label exists anywhere in the tile banks; the screen-walk and
  string/mask searches are the load-bearing evidence for the negative.
* Tournament deeper brackets and in-duel pause menus were not exhaustively walked,
  beyond the first selection screen. No code entry was visible at those levels, but
  they are not individually screenshotted.
* The 1,047 Ghidra procedures were inventoried, not each manually decompiled.
  Exhaustive decompilation could in principle reveal a dormant validator; the zero
  hits for alphabets, code keywords, and button-mask tables make this unlikely but
  not formally impossible.

## 9. Tooling

* mGBA 0.10.5 (`/usr/local/bin/mgba`) under Xvfb `:316` + openbox,
  `SDL_AUDIODRIVER=dummy`; `-3 -g` for GDB stub, `-3` for interactive runs.
  Keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`.
* `gdb-multiarch` driven through a persistent PTY/socket bridge
  (`/tmp/opencode/yugiohddm/gdbdrv.py`) so the core can be interrupted for
  `dump binary memory` and resumed with `continue &`.
* `arm-none-eabi-objdump -M force-thumb` for literal-pool and stub verification.
* Python 3 + `capstone` 5.0.7 for BL/pointer scans; `struct.unpack_from('<I', …)`
  for literal re-reading (§11 byte-order discipline).
* REA MCP with Ghidra 12.1.4 (`binary_overview`, `list_strings`, `xrefs`,
  `procedure_pseudo_code`) — Evidence IDs `ev_dd069d…`, `ev_cec3fa…`,
  `ev_9efed8…`, `ev_59534c…`.
* `strings -t x -n 4`, `xxd`, `scrot`, `xdotool`.

All screenshots, dumps, savestates and scripts live in `/tmp/opencode/yugiohddm/`.
No ROM or copyrighted asset is redistributed by this report. No `.sav`/`.ss*` files
were left in the ROM folder.

## 10. Cleanup

Own processes only, killed by PID number: mGBA instances `891817`, `893890`,
`894615`, `916228`; GDB drivers `895847`, `916339`; GDB stub clients by PID.
The Xvfb (`:316`) and openbox started for this job were also stopped. Every
`game.sav` / `game.ss1` artifact is in `/tmp/opencode/yugiohddm/`; the ROM folder
contains only the original `.gba` and this report.
