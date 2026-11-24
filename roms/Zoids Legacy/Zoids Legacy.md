# Zoids Legacy (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Zoids Legacy.gba` (8,388,608 bytes = `0x800000`) |
| Header title / code / maker | `ZOIDS LEGACY` / `AZ2E` / `70` (USA) |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Header checksum / complement | `0x0000` / stored `0x7A` (recomputed `0x93`) |
| MD5 | `220a6f1b9d8d63e7638248f24dbfa709` |
| SHA-1 | `460fa2158606097f6e6f63ce966d2d6ecdd58d70` |
| SHA-256 | `0379d0e57d77783ed1d18f28c78b9dd1a964e842aac023e6803377f2e86ddc7d` |
| Developer / publisher | Amedio / Atari (release of *Zoids Saga II*) |

**Observed:** crt0 at `0x080000C0` is a normal ARM startup; no cracktro or appended
trainer was found in the first 4 KiB. The zero header checksum and mismatched
complement indicate a rebuilt header, but the entry branch is stock. No `.sav`
or `.ss*` artifacts were written to the ROM folder (all emulation used a hashed
identical copy in `/tmp/zoidslegacy/zoids.gba`).

## 2. Executive summary

The developer-intended cheat surface is **two 17-button sequences entered on the
title screen after clearing the game once**. They are stored as literal arrays of
active-high GBA key masks, not as a password/checksum system:

* **Code A** — `L L R R ↑ ↓ ↑ ↓ ← ← R R → → ← ↑ START` → Diablo Tiger, Cyclops I/II
  Zoid Data + Z Core DT and Z Core CR.
* **Code B** — `R R L L ↓ ↑ ↓ ↑ → → L L ← ← → ↓ START` → Gilvader and King Gojulas
  Zoid Data + Z Core GV and Z Core KG.

Both were published on 3rd party cheat indexes/walkthroughs; this report verifies them at
the instruction level and goes beyond the published list (§6b). The validator is
a single Thumb function (`0x0809BAB0`) that runs as a title-screen task, compares
each incoming key against *both* tables, and grants rewards on a 17-match.
Access is gated by a single post-game byte at `0x02021770`.

**No text password system, debug menu, or algorithmic code generator exists in
this image.** The only cheat surface is the fixed button-code pair; the
interesting enumerable property is the matcher's reset semantics, which accept
arbitrarily many extra keys before the 17-press core (proved in §6b).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 `/usr/local/bin/mgba -3` under `Xvfb :315`,
  `SDL_AUDIODRIVER=dummy`, window manager `openbox`.
* Keymap (mGBA SDL defaults): `A`=`x`, `B`=`z`, `L`=`a`, `R`=`s`,
  Start=`Return`, D-pad = arrow keys.
* Path: boot → skip the intro with a few Start presses → title screen
  ("PRESS START" / menu). Walked screens: intro, title + menu, options-adjacent
  title states; no password/cheat entry screen exists.
* Gate: with a fresh/blank save `0x02021770 == 0`, the validator returns before
  any comparison. Set it to `1` (simulating "game cleared once") via the
  debugger, then enter either sequence with real key presses, or inject the
  masks at `0x0300000E` as done here.
* **Important harness note:** mGBA's GDB stub uses shared port `2345` in this
  environment and was repeatedly attached to *another agent's* ROM. All dynamic
  work was therefore done with the per-process `-d` pty debugger (helpful
  commands: `r/1 ADDR`, `w/2 ADDR VALUE`, `b ADDR`, `c`, `status`, `lb`).
  Real XTEST key presses do reach the validator, but the key queue drops
  presses if they are sent faster than roughly one press per few frames; for
  deterministic proofs the exact masks were injected at the validator's own
  key-read variable `0x0300000E`.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Address (ROM / RAM) | Meaning | Evidence |
|---|---|---|
| `0x087A1194` (file `0x7A1194`) | Code A table: 17 × `u16` active-high key masks | Derived (literal search of published 3-press prefix; dumped) |
| `0x087A11B6` (file `0x7A11B6`) | Code B table: 17 × `u16` | Derived |
| `0x0809BB64` / `0x0809BB68` | Two-entry pointer list to the tables above; next word `0xBC01BC70` is unrelated | Derived |
| `0x0809BAB0` | Validator entry (Thumb), registered as handler #7 at `0x0809BBD0`–`0x0809BBD4` (literal slot `0x0809BC28` = `0x0809BAB1`) | Derived + observed breakpoint hit |
| `0x0809BAC0` | `ldrh r2,[r6,#0]` — reads current key from `r6 = 0x0300000E` | Derived + observed breakpoint hit |
| `0x0809BACE` / `0x0809BADC` | Code A compare / success branch | Derived + observed |
| `0x0809BB18` / `0x0809BB26` | Code B compare / success branch | Derived + observed |
| `0x080ED17C` | Called after each key — Thumb `bx pc` veneer to ARM `0x0800026C` (task-switch/IRQ-style context save). Inferred to be "yield / next key" | Derived (veneer) + inferred (role) |
| EWRAM `0x02021770` | Gate byte (post-game clear flag); read by four sites: `0x08099F80`, `0x0809BAB2`, `0x0809DB0E`, `0x080A6972` | Derived + observed |
| IWRAM `0x0300000E` | Current key mask (`u16`) consumed by the validator | Derived + observed |
| EWRAM `0x02021801`, `0x02021803` | Item/core quantities set to 1 after code A | Observed |
| EWRAM `0x02021858` = `0x40`, `0x02021868` = `0x60` | Three Zoid-Data bits set after code A | Observed |

Adjacent ROM data (`0x087A1100`–`0x087A1170`) is 16-bit-packed text
("Game Boy Advance", "Game Link Cable", …) and is *not* part of the code tables.

## 5. Algorithm

Key-mask encoding is active-high `~KEYINPUT & 0x3FF`:
`A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`.
The tables are stored in exactly this form as little-endian `u16`.

Validator (decompiled from `0x0809BAB0`):

```
if (*(u8*)0x02021770 == 0) return;                 // post-game gate
iA = 0; iB = 0;
loop:
    key = *(u16*)0x0300000E;
    if (key == 0) goto yield;

    if (key == tableA[iA]):                        // 0x0809BACE
        iA = (iA + 1) & 0xFF
        if (iA == 17): grant_A(); iA = 0           // 0x0809BADC
    else:
        iA = 0

    if (key == tableB[iB]):                        // 0x0809BB18
        iB = (iB + 1) & 0xFF
        if (iB == 17): grant_B(); iB = 0           // 0x0809BB26
    else:
        iB = 0
yield:
    call 0x080ED17C                                // yield / next key
    goto loop
```

`grant_A()` calls `0x080E5DC4(6, 0x85, 0x86)`, `0x080E5E0C(3,1)`,
`0x080E5E0C(5,1)`, `0x080940D4`, `0x080940C0`, and message `0x08092E84(0x49)`.
`grant_B()` calls `0x080E5DC4(0x75, 0x92)`, `0x080E5E0C(13,1)`,
`0x080E5E0C(17,1)`, the same save/sound pair, and message `0x08092E84(0x4E)`.

**Semantics worth naming (from the branch structure, not guesswork):**
* A mismatch resets that code's index to 0 but the mismatching key is **not**
  re-tested against index 0. Therefore any number of non-matching keys may
  precede the 17-press core — the matcher accepts the *suffix* of the key stream.
* Both codes are advanced by the same key stream; overlapping prefixes can
  advance both indices simultaneously, but a full 17-match is still required
  for either reward.
* Simultaneous multi-button masks (e.g. `L+A = 0x201`) never equal a table
  entry and therefore only reset the indices.

## 6. Tables

**Code A** — `0x087A1194`, 17 masks (buttons):
`L, L, R, R, Up, Down, Up, Down, Left, Left, R, R, Right, Right, Left, Up, Start`
hex: `0200 0200 0100 0100 0040 0080 0040 0080 0020 0020 0100 0100 0010 0010 0020 0040 0008`

**Code B** — `0x087A11B6`, 17 masks:
`R, R, L, L, Down, Up, Down, Up, Right, Right, L, L, Left, Left, Right, Down, Start`
hex: `0100 0100 0200 0200 0080 0040 0080 0040 0010 0010 0200 0200 0020 0020 0010 0080 0008`

**Rewards observed for code A:** two core quantities at `0x02021801` and
`0x02021803` became `1`; Zoid-data bits `0x40` at `0x02021858` and `0x60` at
`0x02021868` (three bits total) — consistent with the published "three Zoids,
two cores" description. Code B's success branch was executed but its reward
RAM was not captured (see §8).

**Published-list discrepancy resolved:** one 3rd party cheat indexes posting omits the
second-to-last `Left` of code A. The ROM table contains it at index 14, so that
posting is a transcription error (guide §16.7).

## 6b. Enumeration

**Space definition.** The code space is not a numeric password space: it is
**exactly two fixed 17-symbol sequences** over the 10 single-button masks
(`A, B, Select, Start, Right, Left, Up, Down, R, L`). Each stored sequence is
34 bytes (17 × `u16`); the pointer list at `0x0809BB64` holds **2** entries and
is immediately followed by unrelated data. A whole-ROM literal search for the
**full** 16-press prefix found exactly two hits — the tables at `0x7A1194` and
`0x7A11B6` — and a broader scan for long runs of single-key masks found no
other plausible code table. No other validator, alphabet table, mask sequence,
or debug-gate table was found. There is no checksum, generator, or text-entry
code system in this SKU.

**Accepted language.** Because a mismatch only resets the index (and does not
re-test the failing key), the accepted input language is the infinite set of
key streams **ending with** either 17-press core. Thus the number of *exact*
table codes is 2, but the number of accepting input strings is unbounded.

**Novel code (absent from every published list), generated and accepted:**
`A` prepended to code A — 18 presses:
`A, L, L, R, R, Up, Down, Up, Down, Left, Left, R, R, Right, Right, Left, Up, Start`.
Injection at the validator's key-read variable produced **`successA = True`**
(breakpoint `0x0809BADC` hit). No published source lists any 18-press variant;
the extra leading `A` is accepted because it fails both index-0 comparisons and
is discarded. This is the button-code analogue of a novel code under guide §0.2.

**Bounds proved by rejection (all executed in the emulator, gate = 1):**

| Test | Presses | Result |
|---|---|---|
| Code A, exact | 17 | `successA = True`; core/item RAM changed (observed) |
| Code B, exact | 17 | `successB = True`; `successA = False` |
| Novel: leading `A` + code A | 18 | `successA = True` |
| Truncated: code A without final START | 16 | `successA = False`, `successB = False` |
| Corrupted: extra `A` inserted at index 8 | 18 | `successA = False`, `successB = False` |
| Gate byte `0x02021770 = 0` (fresh save) | any | validator returns before any comparison |

This bounds the length at 17 for a clean match, proves the final START is part
of the accepted sequence, and proves that an in-sequence extra key breaks the
match while a leading extra key does not. The gate was verified both ways:
`0` → no comparisons (observed on a blank save), `1` → comparisons and success.

## 7. Validation evidence

Labels follow the guide's Observed / Derived / Inferred convention.

* **Observed** — ROM hashes and header; stock crt0; two code tables and two
  pointers; title-screen walk; gate byte values; every breakpoint hit
  (`0x0809BAB0`, `0x0809BAC0`, `0x0809BACE`, `0x0809BB18`, `0x0809BADC`,
  `0x0809BB26`); the four test outcomes in §6b; post-code-A RAM bytes
  (`0x02021801=1`, `0x02021803=1`, `0x02021858=0x40`, `0x02021868=0x60`);
  real XTEST key presses reaching the comparison loop with the expected masks
  (trace showed `0x200/0x100/0x40/0x80/0x20/0x8` being compared).
* **Derived** — full validator pseudocode and reward call arguments from Thumb
  disassembly; key-mask encoding; gate readers; table sizes; pointer-list
  cardinality; no-cracktro conclusion.
* **Inferred** — the role of `0x080ED17C` as "yield / next key" (its Thumb
  veneer targets an ARM context-save routine at `0x0800026C`); the mapping of
  `0x02021770` to a saved "game cleared" flag (four code readers and the
  published "after you beat the game" requirement agree, but the setter was
  not isolated); the semantic identification of the three Zoid-Data bits with
  Diablo Tiger / Cyclops I / Cyclops II (derived from the published effect plus
  the observed three bits, not from in-game name text).

No prompt-injection content was encountered in fetched pages or ROM strings;
all fetched text and game strings were treated as data.

## 8. Unknowns

* Code B's reward RAM was not captured (the success branch breakpoint fired,
  but the follow-up RAM reads were issued while the core was running and were
  ignored by the pty debugger). Its effect is taken from the published list and
  the static call arguments only.
* The writer/setter of `0x02021770` was not isolated — the gate was patched to
  `1` to simulate a cleared save rather than earned by playing through.
* The exact routine behind `0x080ED17C` was not fully decompiled; its yield
  behaviour is inferred from the loop structure.
* No hidden/debug menu was found. A `strings` sweep of all 119,394 extracted
  strings found no `password`, `cheat`, `generator`, or `debug menu` UI; the
  game's menu text is largely font/tile encoded, so this is a bounded negative
  on ASCII strings only, backed by the complete enumeration of the one button
  validator and its two tables.
* The six published CodeBreaker/GameShark lists were deliberately not tested —
  they are out of scope for this engagement.

## 9. Tooling

* `strings -t x -n 4`, `grep`, Python `struct` scanners for literal pointers,
  PC-relative Thumb `LDR` loads and `BL` target scanning.
* `arm-none-eabi-objdump -M force-thumb` for validator disassembly; Capstone
  5.0.7 for scans.
* mGBA 0.10.5 with `-d` pty debugger, driven by a small UNIX-socket bridge
  (`dbgserver.py` / `dbg.py` / `one_test.py`) that sets breakpoints, injects
  masks into `0x0300000E`, and logs hits.
* `xdotool` XTEST key injection and `scrot` + ImageMagick for the screen walk.
* Evidence (screenshots, logs, scripts) was kept in `/tmp/zoidslegacy/`,
  outside the ROM folder. No ROM or copyrighted asset is redistributed here.
