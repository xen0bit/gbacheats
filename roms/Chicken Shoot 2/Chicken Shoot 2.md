# Chicken Shoot 2 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Chicken Shoot 2/Chicken Shoot 2.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `CHICKENSHOT2` |
| Game code | `B6GE` |
| Maker code | `20` |
| Software version | 0 (`Rev.00`) |
| MD5 | `4acb75f06293b30690e98740cf3e3f81` |
| SHA-1 | `16b793184790411c1461dec9faf812bd05b1249c` |
| SHA-256 | `ded84ce21bc7a734e502397a3b6a0b017ac2eaf1eae11e1b36dd23dc4b624ef3` |

Header detail: entry word `0xEA00002E` (stock `b 0x080000C0`), fixed byte `0x96`,
complement byte `0x86` (matches the computed value), 16-bit header checksum `0x0000`.
The entry branch is the retail branch and the first 4 KiB is the stock crt0 (ARM at
`0x080000C0`, IRQ setup at `0x080000FC`, Thumb `main` at `0x08001AE4`); no cracktro, no
SUNHORS/Mode7 string, no appended trainer and the last 32 bytes are zero. The zero
32-bit header checksum is common in GBA images and is not by itself evidence of a patch;
no code patch or trainer was found.
Embedded-header scan (156-byte Nintendo logo): exactly one hit, at file offset 0 — this
is a single-image cartridge, not a multi-game pack.

## 2. Executive summary

**This ROM has no in-game code/password system and no button-code (sequence) system.**
The report below is therefore a bounded negative result, not a list of accepted codes.

What the game does contain is a localized menu engine with ten static screen descriptors
(72 item slots), a global key-state block, and a high-score *name* entry field. What it
does **not** contain is:

* no `password`, `passwd`, `cheat`, `secret`, `unlock`, `gallery`, `debug`,
  `level select` string anywhere in the image in ASCII, case-insensitive (0 hits each);
* no alphabet, length check, checksum, key table or validator for code entry;
* no table of button masks in code (0 u16 runs of length ≥3 over
  `{A,B,Select,Start,Right,Left,Up,Down,R,L}` in `0x000000`–`0x030000`);
* no literal comparison of the key state against any multi-button combination:
  all 41 pressed-key consumers in the code region do `pressed & mask` and compare the
  result with **0**, where `mask` comes from the global key map or an item record. A
  sequence/prefix matcher would require comparing the key word (or a history) with
  literals; no such comparison exists.

Two development leftovers are present and **dead**:

* `test arcade` (5 language copies, `0x083BD0C2`, `+0x19`, …) and `test classic`
  (5 copies, `0x083BD13F`, …). Each has **zero** 32-bit code/data references; they are
  not in any item table and cannot be selected.
* A `-highscore-` screen (`0x083BEECC`, items at `0x083BEEB4`) exists but is only
  referenced by its own dispatch chain: its opener `0x0800C570` is referenced only by
  the literal `0x0800C571` inside `0x0800C588`, and `0x0800C588` is only referenced by
  literals inside the high-score item handlers. There is no external caller, i.e. the
  screen is cut/dead in this build. (Its name-entry field is not a validator — see §5.3.)

The only text input in the game is the high-score name entry (`-enter name-`,
`0x083BE256`), which cycles the single buffer byte through `a`–`z` (`0x61`–`0x7A`) and
writes a glyph; the byte is never compared with any code table.

There are no published in-game cheats for this SKU to verify (see §6b): Cheat Happens
lists none, GameFAQs' cheat page has no entries, ChapterCheats lists none. The only
circulating "codes" are Action Replay memory patches (GBAtemp cheat-file #2411), which
are explicitly out of scope for this engagement.

## 3. How to reproduce

Emulator: mGBA SDL on `Xvfb :243` + `openbox`, `SDL_AUDIODRIVER=dummy`.

```bash
Xvfb :243 -screen 0 1024x768x24 &
DISPLAY=:243 openbox &
DISPLAY=:243 SDL_AUDIODRIVER=dummy mgba -3 "Chicken Shoot 2.gba" &
```

Default mGBA SDL key map (verified against `KEYINPUT` `0x04000130`):

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| Start | `Return` |
| Select | `BackSpace` |
| L / R | `a` / `s` |
| D-pad | arrow keys |

Menu path (all states read back from RAM, not from screenshots):

1. Boot. After roughly 700–900 emulated frames the engine opens the main menu
   (`-menu-`, items `new game` / `options` / `about`; head at `0x03004348`).
2. `A` on the highlighted item opens **Options** (`-options-`, 10 slots:
   difficulty, value, sfx, value, music, value, gamma, value, back).
3. `B` returns to the main menu.
4. `A` on `about` opens the timed credits roll (text blocks at `0x083C0580`/`5B0`/`5E0`);
   it returns to the main menu by itself after ~20 s.
5. The remaining screens were opened by performing the same dispatch the game performs
   on an `A` press: write the screen's own opener (taken from the game's item callback
   literal pool) to `base+0x38` (`0x03002A58`) and press `A` once. This is the engine's
   documented action slot (`0x08006410`: `ldr r0,[base,#0x38]; cmp r0,#0; bl 0x080FA840`),
   not a flag poke. Every resulting screen was then read back from the item list.

Opener addresses used (Thumb pointers, low bit set):

| Screen | Opener |
|---|---|
| main | `0x0800BFD9` |
| select | `0x0800C44D` |
| options | `0x0800C559` |
| highscore | `0x0800C571` |
| key config 1 | `0x0800C9A5` |
| key config 2 | `0x0800C93D` |
| pause options | `0x0800CA0D` |
| connecting (level select) | `0x0800C33D` |
| language | `0x0800D8D9` / `0x0800D8F1` |
| in-game pause | inline at `0x08001678` (Start press) |

With the command-line debugger (`mgba -d`) the item list can be read directly:

```
x/4 0x03002A3C 1      # head of item list
x/1 0x03004348 0x50   # item 0: text ptr, next ptr, callback, ...
```

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08000000`–`0x080000BF` | stock GBA header (entry `0xEA00002E`) |
| `0x080000C0` | ARM crt0 |
| `0x08001AE4` | Thumb `main` (mode dispatch at `+0xD6`/`+0xD7`) |
| `0x0800970C` | keypad reader (only reader of `0x04000130`) |
| `0x0800610C` | clear/prepare menu (called before `menu_open`) |
| `0x08006194` | **menu_open(screen descriptor)**; builds item widgets |
| `0x08005D50` | build one menu item widget (`item*`, flag) |
| `0x080063F0` | menu list update; calls `base+0x38` on A press |
| `0x0800D130` | menu frame loop / fade (calls `0x0800970C`, `0x080063F0`) |
| `0x0800BFD8` | opener: main menu (`0x083BEDBC`) |
| `0x0800C44C` | opener: `-select-` (`0x083BEFDC`) |
| `0x0800C558` | opener: `-options-` (`0x083BF220`) |
| `0x0800C570` | opener: `-highscore-` (`0x083BEECC`) |
| `0x0800C93C` / `0x0800C9A4` | opener: `-redefine keys-` (`0x083BF8D0` / `0x083BF6BC`) |
| `0x0800CA0C` | opener: pause options (`0x083BF490`) |
| `0x0800C33C` | opener: `-connecting-` (`0x083BFB80`) |
| `0x0800D8D8` / `0x0800D8F0` | opener: language select (`0x083BECE0`) |
| `0x0800C480`-block (`0x0800C464` etc.) | per-item update callbacks (activate on B) |

RAM (all in IWRAM, base `0x03002A20`):

| Address | Meaning |
|---|---|
| `0x03002A3C` | `base+0x1C` — head of menu item linked list |
| `0x03002A58` | `base+0x38` — A-press dispatch slot (tail-called through `0x080FA840`) |
| `0x03002A5C` | `base+0x3C` — B-press dispatch slot |
| `0x03002ABA` | `base+0x9A` — current KEYINPUT (active low) |
| `0x03002ABC` | `base+0x9C` — pressed mask (0 = newly pressed) |
| `0x03002ABE` | `base+0x9E` — previous key state |
| `0x03002AC0`+ | key map: L=`0x0200`, R=`0x0100`, Left=`0x0020`, Right=`0x0010`, Up=`0x0040`, Down=`0x0080`, A=`0x0001`, B=`0x0002`, Start=`0x0008` |
| `0x03004348` + `0x50*i` | menu item widget *i* (0–15): `+0x00` text ptr, `+0x04` next, `+0x08` callback, `+0x4A` state/palette |
| `0x03005408` | scene/render state block |

ROM data:

| Address | Meaning |
|---|---|
| `0x083BC400`–`0x083C0500` | localized text bank (ASCII lower-case, drawn upper-case) |
| `0x083BECE0` | language screen descriptor `{items=0x083BECD0, 0xFFFF}` |
| `0x083BEDBC` | main menu descriptor |
| `0x083BEECC` | highscore descriptor (dead) |
| `0x083BEFDC` | select-mode descriptor |
| `0x083BF220` | options descriptor |
| `0x083BF4A8` | in-game pause descriptor |
| `0x083BF490` | pause-options descriptor |
| `0x083BF6BC`, `0x083BF8D0` | key-config descriptors |
| `0x083BFB80` | connecting/level-select descriptor |
| `0x083C0580`+ | credits text blocks |

## 5. Algorithm

### 5.1 Input

`0x0800970C` is the only routine that touches `0x04000130`:

```
cur   = KEYINPUT                     ; active low
[base+0x9A] = cur
if cur == [base+0x9E]: [base+0x9C] = 0xFFFF
else:
    changed = cur ^ [base+0x9E]
    [base+0x9C] = ~([base+0x9E] & changed)   ; 0 bit = newly pressed
    [base+0x9E] = cur
```

All consumers then test `pressed & mask`; the result is 0 exactly when the mapped
button is down. No consumer tests the key word against a combination literal, and no
consumer keeps a sequence index or history. There is therefore no sequence space to
enumerate: the input model is stateless single-button actions.

### 5.2 Menu engine

A screen descriptor is `{ u32 items; u8 x; u8 y; u8 ?; u16 0xFFFF }` where `items` is a
NULL-terminated array of item pointers. `0x08006194` copies the origin bytes, sets
`base+0x38 = base+0x3C = 0`, then calls `0x08005D50(item, 0)` for every entry. That
routine allocates widget `i` at `0x03004348 + 0x50*i` and links it into the list at
`base+0x1C`. Each item callback is a per-frame update; the menu list update
(`0x080063F0`) tail-calls the address stored in `base+0x38` when A is pressed. This is
why the ten screens can be opened deterministically by writing their own opener into
`base+0x38` (see §3).

### 5.3 Name entry (not a password)

`-enter name-` (`0x083BE256`) uses the letter items at `0x083BE4C0`+. The letter callback
`0x0800B724`:

* A press: `buf[4] = (buf[4] <= 0x79) ? buf[4]+1 : 0x61`
* B press: `buf[4] = (buf[4] > 0x61) ? buf[4]-1 : 0x7A`
* then maps the byte through a glyph table and stores the tile.

The byte is a name character; there is no comparison against a dictionary, code table
or checksum. This is the field the guide's §16.2b warns about: a text field that is not
a password field.

## 6. Tables

### 6.1 Screen / item enumeration (all static screens in the image)

| Screen | Items array | Items (callback) |
|---|---|---|
| language | `0x083BECD0` | `select language`; ` `; `english` |
| main | `0x083BEDA8` | `-menu-`; `new game` (`0x0800C465`); `options` (`0x0800C79D`); `about` (`0x0800B375`) |
| highscore (dead) | `0x083BEEB4` | `-highscore-`; `arcade` (`0x0800C5FD`); `classic` (`0x0800C671`); `multiplayer` (`0x0800C6E5`); `back` (`0x0800C74D`) |
| select | `0x083BEFC4` | `-select-`; `arcade` (`0x0800AE29`); `classic` (`0x0800AEDD`); `multiplayer` (`0x0800B139`); `back` (`0x0800C38D`) |
| options | `0x083BF1F4` | `-options-`; `difficulty` + value (`0x0800C8DD`/`0x0800C8CD`); `sfx` + `9` (`0x0800B519`/`0x0800B49D`); `music` + `9` (`0x0800B65D`/`0x0800B5E1`); `gamma` + `1` (`0x0800B3E5`/`0x0800C8ED`); `back` (`0x0800C819`) |
| pause options | `0x083BF408` | `-menu-`; `sfx` + `9`; `music` + `9`; `gamma` + `1`; `back to game` (`0x0800CD5D`); `quit` (`0x0800CAF5`) |
| in-game pause | `0x083BF498` | `-menu-`; `back to game` (`0x0800CD5D`); `quit` (`0x0800CAF5`) |
| key config 1 | `0x083BF690` | `-redefine keys-`; `l`; value; `r`; value; `fire`; value; `reload`; value; `back` (`0x0800CA25`) |
| key config 2 | `0x083BF8A4` | same, `back` (`0x0800CA8D`) |
| connecting | `0x083BFB48` | `-connecting-`; `1 -`; `2 -`; `3 -`; `4 -`; `back` (`0x0800C2ED`); `level -` (`0x0800C2B5`); 6 value/status cells (`ok`/`no`/`1`/`2` labels) |

Total: **10 screen descriptors, 72 item slots**. The name-entry keyboard
(`0x083BE4C0`+) is a dynamic screen built from 8 letter slots plus two `ok` controls.

### 6.2 State flags

No cheat/unlock flag word and no unlock text exist. The game has no separate
title/attract screen with input: the boot sequence opens the main menu directly
(observed). Weapon upgrades are in-level pickups (the ROM contains no weapon-unlock
text or unlock flag table), and the only level/round selector is the `-connecting-`
lobby (`1 -`…`4 -`). The only progression state is the per-run score/level counters;
no `SRAM`/`EEPROM`/`FLASH` string exists and the high-score table is RAM-only, matching
the published description that scores are not retained.

## 6b. Enumeration

**Code/password space size: 0.** There is no entry screen, alphabet, length field,
checksum field or reserved bit. This is not an inference from "I did not find it": the
ROM's text bank was decoded in full (lower-case ASCII, `+0x00` mapping; see
`0x083BC400`–`0x083C0500`) and the keyword counts are 0 for `password`, `passwd`,
`cheat`, `secret`, `unlock`, `gallery`, `debug`, `level select` in any case. A full
32-bit pointer scan of the text bank found 91 references; 90 resolve to a menu item,
game-over/stats/name label or credits block, and the remaining one (`0x00014AF4`) is a
coincidental pointer into a graphics run. None points to a code-like string.

**Published codes: none to verify.** Cheat Happens' Chicken Shoot 2 GBA page states
"There are no Chicken Shoot 2 cheats or cheat codes"; GameFAQs' cheat page for the GBA
SKU has no entries; ChapterCheats lists no codes/passwords/unlockables;
`web.archive.org` has no snapshot of a Chicken Shoot 2 cheat page (404). The only thing
indexed is a GBAtemp Action Replay `.CHT` (memory edits), excluded by scope. A literal
search for the only candidate strings (`test arcade`, `test classic`) found 5 language
copies each and zero code references, so no published code could have been correct.

**Button-code space.** The natural full space is all sequences of length 1–10 over ten
buttons (10^10). It is not brute-forced; instead the implementation space is bounded.
The scan window `0x08000000`–`0x08030000` covers the whole low code/data region before
the text bank at `0x083BC000`; every routine identified in this report lies in
`0x0800xxxx`–`0x08015xxx`. That window contains **0** u16
runs (length ≥3) over the ten mask values, and all **41** `adds #0x9C` key consumers in
it perform `pressed & mask` then `cmp #0`; none compares the key state or a history to a
literal combination. A table-driven or chained `if` sequence matcher would have to appear
as one of those two patterns. Therefore the implemented input surface is exactly the
single-button actions listed in §6.1, and no undocumented sequence exists to press. (For
completeness, the classic Konami prefix `Up Up Down Down Left Right Left Right B A` was
also searched as u16 and as bytes, in both polarities and both orders: not present.)

**Menu space (enumerated, not sampled).** Ten descriptors and 72 item slots were
enumerated statically. Eight of the ten were also opened at runtime and read back from
`0x03004348`, and the RAM list matched the static table exactly for those eight (main,
select, options, highscore, key config 1, key config 2, pause options, connecting).
The language screen's two openers were tested but do not rebuild items in the
post-boot state (it is the first-boot selector), so its three items are proven
statically only. The simple in-game pause screen is reached inline from `0x08001678`
on Start and is likewise proven statically. The only screen that is *present but
unreachable* is `-highscore-`: its opener has no external reference (§2), so it is
recorded as cut/dead, not as a hidden cheat.

**Requested scope checklist.**

| Area | Result |
|---|---|
| Title screen | no input screen; boot reaches the main menu directly (observed) |
| Options | 10-slot `-options-` screen enumerated and opened |
| Level / round select | `-connecting-` lobby, levels `1 -`…`4 -` (multiplayer entry) |
| Gun / weapon unlocks | no unlock text or unlock flag table; weapons are in-level pickups |
| Hidden / debug screen | none reachable; `test arcade`/`test classic` have 0 xrefs; `-highscore-` is cut |
| Published codes | none exist for this SKU (see above) |

**Novel code.** None can be minted because the space is empty; the deliverable for this
engagement is the proven absence, bounded by the counts above rather than by a test of
one sample.

## 7. Validation evidence

### 7.1 Observed (emulator/RAM)

* Boot → main menu; item head `0x03002A3C → 0x03004348` with texts
  `-menu-`/`new game`/`options`/`about`.
* `A` (x) opened Options; RAM item list `0x083BEFE4…0x083BF1C4` matched the static
  options descriptor. `B` (z) returned to the main menu.
* `A` on `about` opened the scrolling credits; it returned to the main menu after about
  20 s.
* Each of main, select, options, highscore, key-config 1/2, pause options and
  connecting was opened through its own opener at `base+0x38` and its item list was
  read back from RAM. The `-connecting-` screen showed the level items `1 -`…`4 -` and
  `level -`, i.e. the only in-game level/round selector. The language screen was
  exercised through both of its openers; in the post-boot state it did not rebuild its
  items, so its (`select language` / `` / `english`) list is static evidence.
* `KEYINPUT` was polled to confirm every synthetic key (A=`0x03FE`, B=`0x03FD`,
  Start=`0x03F7`, Down=`0x037F`) and the pressed mask at `0x03002ABC`.

### 7.2 Derived (disassembly)

* `0x0800970C` is the only keypad reader; pressed-mask semantics as in §5.1.
* `0x080063F0`/`0x08006410` proves the `base+0x38` A-action slot; menu item callbacks at
  `0x0800C464` etc. write the next action pointer.
* The `-highscore-` opener chain is self-referential (all references are literals inside
  its own handlers), so it has no entry from the game.
* All 41 key consumers use AND-mask-then-zero; no sequence matcher.
* The name-entry callback `0x0800B724` cycles `0x61`–`0x7A` and never validates.

### 7.3 Inferred

* The ten screens constitute the complete developer **screen-descriptor** set for this
  build. This rests on the complete pointer scan of the text bank (no additional screen
  descriptors outside the ten; the remaining item records are game-over, stats and
  name-entry labels) and on the boot/credits flow, not on exhaustive play.
* The `test arcade`/`test classic` strings are development leftovers from a mode-select
  variant (they sit between `multiplayer` and `-options-` in the string bank); they have
  no code path, so the test modes are not reachable.
* Scores are RAM-only (no save strings or save routine found); this matches the
  published description that high scores are not retained.

## 8. Unknowns

* The exact purpose of the `-highscore-` chain cannot be exercised because it has no
  caller; it may have been reachable in a pre-release build.
* The two `test` labels cannot be assigned to a specific removed screen; only their
  position in the string bank and their total lack of xrefs are proven.
* Multiplayer/link behaviour of the `-connecting-` screen was not exercised with a
  second GBA; only its item table and level list are proven.
* The 16-bit header checksum field at `0xBE` is `0x0000`; the complement byte is valid.
  This is common in GBA images and no patched code was found.

## 9. Tooling

* `Xvfb :243`, `openbox`, mGBA SDL (`-3`, `-d` command-line debugger).
* Python 3 + Capstone 5.0.7 for Thumb disassembly and instruction-pattern scans.
* GNU `arm-none-eabi-objdump` (`-M force-thumb`) and `xxd`/`strings`.
* `/tmp/opencode/chickenshoot2/analyze.py` — reproduces the screen table, keyword
  counts, test-string xref counts, mask-table count and key-consumer count.
* `/tmp/opencode/chickenshoot2/daemon.py` + `ram.py` — pty controller for the mGBA
  command-line debugger (read RAM, run frames, write the A-action slot).

## Legal note

No ROM, graphics, audio or extracted game text is redistributed here. All addresses,
counts and algorithms are original observations about a locally owned image.
