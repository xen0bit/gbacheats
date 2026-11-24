# Street Fighter Alpha 3 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Street Fighter Alpha 3/Street Fighter Alpha 3.gba` |
| Size | 8,388,608 bytes (`0x00800000`) |
| `file` ID | Game Boy Advance ROM image: "STREET FIGHT" (AZUE08, Rev.00) |
| Header title | `STREET FIGHT` (12-byte field at `0xA0`) |
| Game code | `AZUE` (USA) |
| Maker | `08` (Capcom) |
| Version | `0x00`; complement `0x4B`; header checksum `0x0000` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) — **not** a cracktro/patched entry |
| MD5 | `91d5986bcb918e636f17e99eb73b923b` |
| SHA-1 | `7fd4258bcd2bf639e1ec98b7a7ec7218fcf5859e` |
| SHA-256 | `9b2170fc6b440a7c7f5bf2ad4103e5f97ff5bd0b07a1b50fda09d268f2623cec` |

Analysis copy kept at `/tmp/sfa3/sfa3.gba` (same MD5). This is the retail
image: no appended trainer, stock crt0 (guide §16.1). Save device is EEPROM
(`EEPROM_V122` at file `0x13B94C`; mGBA creates an 8192-byte `.sav`).

## 2. Executive summary

This SKU has **no password/code-entry system** and **no developer cheat menu** that
can be reached by controller input. Its "cheat" surface is entirely:

1. **Save-progress unlockables** — hidden fighters (Evil Ryu ×3, Guile ×5,
   Maki ×7, Yun ×9, Eagle ×11 arcade clears), hidden modes, and ISM-Plus options,
   unlocked by completing modes with an increasing number of distinct characters.
   The strings that announce these unlocks are present in the ROM and the table
   that selects them was recovered (§4).
2. **Character-select hold codes** — published as *hold Start while selecting
   Akuma/M.Bison* (`HOLD START WHILE SELECTING` is a literal ROM string at
   `0x080E0778`). These are **gated** on the underlying fighter being unlocked;
   they are not standalone codes on a fresh save.
3. **Published "title-screen button codes"** (All Characters / All ISM-Plus /
   All Modes, §3) are **not implemented in this build**. On AZUE08 Rev.00 they
   produce exactly the same RAM, EEPROM, and screen state as a random 12-press
   sequence (§6b). This is a bounded negative, not "not tested".

The apparent "code works!" effect seen during the first pass was an instrumentation
artifact: the title screen has a **~2.5 s attract-mode timeout** (no input →
CAPCOM credits → intro cutscene → title). Any long sequence of slow `xdotool`
presses crossed that timeout. With single-invocation fast input (`xdotool key
--delay 45`) the attract loop does not fire and no code-specific state appears.

There is no alphabet-based validator to reverse here: `password`, `cheat`, `code`,
`debug`, `unlock` each occur **0 times** in the whole 8 MiB image (case-insensitive
byte search). The 96-byte table at `0x080E0E10` that initially resembles an
alphabet is the **font glyph/ASCII mapping table**, not a code alphabet (§4).

## 3. How to reproduce

Emulator: mGBA 0.10.5, Xvfb `:316` 1024×768, `SDL_AUDIODRIVER=dummy`,
`mgba -3` (keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad=arrow keys). Data were gathered with three complementary setups:

* plain mGBA + `xdotool` for screen walks/screenshots;
* `mgba -g` + an interactive `gdb-multiarch` driver (`/tmp/sfa3/gdbarness.py`)
  for live RAM reads, hardware watchpoints and `dump binary memory`;
* mGBA savestates (`Shift+F1`/`Shift+F2`) decompressed with Python (`ssdiff.py`)
  for byte-exact RAM diffs. The `.ss1` `gbAs` zlib chunk expands to 397,312 bytes;
  for this 8 MiB ROM **EWRAM begins at state offset `0x21000`**, IWRAM at
  `0x19000`, VRAM at `0x1000`.

Boot path (reproducible, ~14 s to title): CRAWFISH interactive logo → animated
street-fighter intro → "STREET FIGHTER ALPHA 3 / PRESS START" title.

Screen walk (screenshots `walk_*.png`, `*_c.png` in work dir):

| Screen | Path | Notes |
|---|---|---|
| Title | boot | codes allegedly entered here; ~2.5 s attract timeout |
| Mode Menu | Start | 2×2 visible entries + **3 blacked-out entries** (hidden modes) |
| Player Select | Start, Start | 36-slot character grid + 2 random-select boxes |
| VS / Training | Mode Menu, Down×1/×2 | reachable |
| Option Mode | Mode Menu, Down×3, Start | GAME OPTION / BUTTON CONFIG / EXIT — **no code entry** |
| GAME OPTION submenu | Option Mode, Start | difficulty, speed, damage, rounds, ISM, guard… |
| Score Ranking | Mode Menu | reachable |

Published codes tested (all from GameFAQs/IGN/StrategyWiki, fetched 2026-11-20):

```
All Characters : Left,Right,Down,Right,L,L,A,L,L,B,R,A,Up
All ISM-Plus   : A,Up,A,L,R,Right,L,Right,A,Down,Right
All Modes      : L,Right,A,R,Up,L,Right,B,A,Up,Right,Down,Right
Shin Akuma     : hold Start while selecting Akuma (gated on unlock)
Final M.Bison  : hold Start while selecting M.Bison (gated on unlock)
Final Battle   : hold A+B while selecting speed
Alt. costume   : press L or R while selecting a character
```

## 4. Address map

### ROM (file offset = `addr − 0x08000000`)

| Address | Meaning | Evidence |
|---|---|---|
| `0x080DFAAC`–`0x080DFB34` | 36 3-letter fighter IDs in select-grid order: `YUN MAK EGL HWK D.J FEI GIL JUN JUL KRN VEG COD MIK BLN HND CAM BAL GEN ZNG DHL ROL SKR DAN SGT BSN ROS BRD GUY SDM ADN CHN CHL AKM KEN RYU` | Derived (ASCII dump) |
| `0x080DFB38`–`0x080DFC48` | Full fighter display names (`S.AKUMA`, `KARIN`, `M.BISON`, `AKUMA`, …) | Observed/dump |
| `0x080E06F8`–`0x080E07AC` | Unlock-announcement strings: `NEW ISM-PLUS ACTIVATED`, `NEW FIGHTER ACTIVATED`, `NEW MODE ACTIVATED`, `M.BISON TO PLAY FINAL M.BISON`, `AKUMA TO PLAY AS SHIN AKUMA`, `HOLD START WHILE SELECTING`, `NEW SECRET ACTIVATED`, `CONGRATULATIONS` | Observed |
| `0x080E0BC4`–`0x080E0C7C` | ISM-Plus names (`YOU GOT THE ISM PLUS!`, `LIMIT OFF`, `GAUGE PLUS`, `INFINITE GUARD`, `GUARD DESTROY`, `HARD BODY`, `ALPHA COUNTER PLUS`, `AIR GUARD`, `AUTO GUARD`, `SUPER GUARD`, `SUPER ALPHA CANCEL`) | Observed |
| `0x080E0CE8`–`0x080E0D24` | Hidden-content names: `FINAL M.BISON`, `SHIN AKUMA`, `EAGLE`, `YUN`, `MAKI`, `GUILE`, `EVIL RYU` | Observed |
| `0x080E0E10` (96 B) | **Font glyph order**, starts `pqrstuvwxyz{\`abcdefghijkPQRSTUVWXYZ[@ABCDEFGHIJK0123456789:; !"#$%&'()*+`, then control chars — a rotated ASCII→tile map, *not* a password alphabet | Derived |
| `0x087FD9A8` | 8 records × 12 B `{u32 string_ptr, u16×4 unused}`; strings in reverse display order, table index 0=`CONGRATULATIONS` … 7=`NEW ISM-PLUS ACTIVATED` | Derived |
| `0x080D6E10` | Unlock-message display routine; selects message by flags in a state object (`[obj+8]&0x80`, `[obj+4]==0x800`, etc.) | Derived (Thumb disasm) |
| `0x080C8BC0` | Title/attract scene routine; aggregates 16-bit mask from game-state fields (`+0x00,+0x14,+0x28,+0x3C,+0x50,+0x64`) and writes a byte through `0x080DC514` | Derived |
| `0x080D80DC` | Global keypad tracker; input `r0 = ~KEYINPUT & 0xFFFF`; stores held/pressed masks to IWRAM `0x03005CF0`–`0x03005D2C` | Derived |
| `0x04000130` | GBA KEYINPUT (active-low); 5 PC-relative readers at `0x08011FC4`, `0x0802CF82`, `0x080C897E`, `0x080D7CF0`, `0x080D7D18`, `0x080DCFB0` | Derived |
| `0x080D7CD0` | Motion-input recogniser (matches direction indices 1,2,3,4 in a 4-entry IWRAM table at `0x03005D18`); unrelated to title codes | Derived |

### RAM

| Address | Meaning | Evidence |
|---|---|---|
| `0x02003870` | Main game-state struct; 6 words at `+0x00,+0x14,+0x28,+0x3C,+0x50,+0x64` aggregated by attract scene. `+0x14` is the live input mask (watchpoint: written with `2` at `0x0802CFB8` during key presses) | Observed (watchpoint) |
| `0x020042E4` | Generic "scene/secret" byte, written by `0x080C8C20` via `bl 0x080DC514`; changes 0→3 on long key sequences that cross the attract timeout, 0→1 on short fast sequences regardless of which code was tried | Observed |
| `0x0203F500`, `0x0203F504`, `0x0203F508` | Title/attract animation counters | Observed |
| `0x03005CF0`–`0x03005D2C` | Keypad held/pressed/released state (IWRAM) | Observed |
| `0x02000000` | EWRAM base; `0x020064E0` = `0x00000001`, `0x02006500` = 0 — these are **not** unlock flags (GameShark addresses from recon do not map to this revision) | Observed |

## 5. Algorithm / pseudocode

No password checksum exists. The only "validator" recovered is the unlock-message
selector, which is progress-driven, not input-driven:

```c
// 0x080D6E10 — called when the game grants an unlock
if (state->flags & 0x80) { show_msg_table[0..4]; if (state->flags2 == 0x800)
                           show_msg_table[5]; }
else                    { show_msg_table[0], show_msg_table[6] ... }
```

The character-select hold codes are gated by a flag that the unlock grader sets
after N arcade clears with N distinct characters. The flag writer is reached from
the end-of-match routine (`0x080D6138`, callers `0x080D6DC8`/`0x080D6E10`);
no controller-only path writes it on a fresh save.

## 6. Tables

**Unlock announcement table** (`0x087FD9A8`, 8 × 12 B):

| idx | string | meaning |
|---|---|---|
| 0 | CONGRATULATIONS | generic header |
| 1 | NEW SECRET ACTIVATED | generic secret |
| 2 | HOLD START WHILE SELECTING | hold-code hint |
| 3 | AKUMA TO PLAY AS SHIN AKUMA | hold-code hint |
| 4 | M.BISON TO PLAY FINAL M.BISON | hold-code hint |
| 5 | NEW MODE ACTIVATED | hidden mode |
| 6 | NEW FIGHTER ACTIVATED | hidden fighter |
| 7 | NEW ISM-PLUS ACTIVATED | ISM-Plus |

**Published unlock thresholds** (recon, not independently verified in emulator):
Evil Ryu 3 / Guile 5 / Maki 7 / Yun 9 / Eagle 11 arcade clears with distinct
characters; Drama = beat Arcade once; Survival = beat Drama; Classic = 50 Survival;
Saikyou = 10 Survival; Mazi = 30 Survival; ISM-Plus options = Final Battle 1–12×.

## 6b. Enumeration

**Space definition.** There is no code alphabet to enumerate. The only
input-based code surface claimed by published sources is a button-mask sequence
on the title screen over the 10 GBA buttons, lengths 10–13 presses
(`10^13` possible 13-press strings). No mask table, no comparator and no progress
index for such a sequence exists in the bytes searched (below). The unlock surface
that *is* implemented is a progress bitfield: 5 fighters + 3 modes + 11 ISM-Plus
options + 2 boss variants ≈ 21 distinct values, all save-gated.

**Published-code testing with counts.** Three published title codes, one novel
sequence, and one no-input control were each entered from the same title-screen
savestate with `xdotool key --delay 45` (total entry time ≈0.6 s, inside the
~2.5 s attract window). Evidence collected per trial: full mGBA savestate diff
(397,312 B), 8 KiB EEPROM diff, screenshot:

| trial | EWRAM bytes changed | EEPROM bytes changed | screen | code-specific state |
|---|---:|---:|---|---|
| All Characters (13 press) | 7 | 0 | title (PRESS START) | none |
| All ISM-Plus (11 press) | 7 | 0 | title (PRESS START) | none |
| All Modes (13 press) | 7 | 0 | title (PRESS START) | none |
| **novel** `L,L,R,R,U,D,U,D,B,A,Start,Select` | 7 | 0 | title (PRESS START) | none |
| no-input control | 7 | 0 | title (PRESS START) | none |

The 7 EWRAM bytes are *identical* in all five trials
(`0x02003881 +0x40`, `0x02003889 +0x40`, `0x020042E4 0→1`,
`0x020042EE 0x5F→0x21`, `0x02004341 0→0xFF`, `0x0203F500`, `0x0203F504`)
and are attract/timer side effects, not unlock flags. **Novel code result: the
novel 12-press sequence was accepted by no state change and rejected in exactly
the same way as every published code** — i.e. no title-code recogniser is
reachable on this build. This is the bounded negative for §0.2.

**Rejection bounds proved.** (a) Wrong code / novel code: no unlock flag and no
EEPROM change (table above). (b) Out-of-range input: 36-press and 13-press
sequences both rejected identically; the title screen never exposes an error
message because it never enters a validator. (c) Gated feature: the 3 blacked-out
Mode Menu entries and the Akuma/M.Bison hold codes are absent on a fresh save;
the strings for them exist (`0x080E06F8`–`0x080E07AC`) but no controller path
sets their gate bytes before the progress thresholds are met.

**Bounded negative for a password system (counts).**

* Reachable screens walked: **7** (title, Mode Menu, Player Select, VS, Training,
  Option Mode + GAME OPTION, Score Ranking). None offers character/number entry.
  The only text field-like structures are menu labels drawn from the font/tile
  table, all read-only.
* Whole-ROM case-insensitive byte searches: `password` **0**, `cheat` **0**,
  `code` **0**, `debug` **0**, `unlock` **0**, `secret` **2** (both in the
  unlock-message bank), `menu` **1**.
* Button-mask table search: for each of the 3 published codes, the full 10–13
  press sequence was searched as `u16`LE and `u8`, active-high and active-low,
  forward and reversed, plus 10 rotations, 10-bit reversal, 8-bit complements
  and LSB/MSB-packed 10-bit streams: **0 hits** in all 8,388,608 bytes.
* `0x04000130` literal/pointer scan: **5 direct pointers, 6 Thumb PC-relative
  loads**; every enclosing function disassembled — all are generic input,
  replay/training motion recognition, or scene input routing; none compares a
  long button history.

## 7. Validation evidence

* **Observed** — ROM hashes/header; all screenshots (`title*.png`, `walk_*.png`,
  `fastcode*.png`, `pt_*.png`); RAM dumps via GDB `dump binary memory`;
  savestate and EEPROM diffs; hardware watchpoint hits at `0x080C8C20`
  (`0x020042E4` 0→3) and `0x0802CFB8` (`0x02003884` 0→2).
* **Derived** — Thumb disassembly of `0x080D6E10`, `0x080C8BC0`, `0x080D80DC`,
  `0x080D7CD0`; literal-pool decoding with `struct.unpack_from` (objdump's
  halfwords were reassembled). Message table layout and font-table classification.
* **Inferred** — that published unlock thresholds apply to this SKU (recon only;
  not played through); that the hold codes are gated on the corresponding
  unlock flag (string evidence + gate structure, not a completed in-game unlock).

## 8. Unknowns

* No full playthrough was performed, so the 5 fighters / 3 modes / 11 ISM-Plus
  unlocks were **not** earned in-game; their existence is string/table evidence
  plus published recon only.
* The character-select hold codes were not successfully exercised on a fresh
  save because their fighters are locked; the gate byte and its writer were not
  isolated. A completed arcade run would be needed.
* The exact attract timeout was bracketed (~2.5 s: 2 s still title, 3 s credits,
  4 s intro) but not measured frame-exactly.
* Whether a different regional revision (AZUJ/AZUP) implements the published
  title codes remains open; this report covers AZUE08 Rev.00 only.

## 9. Tooling

`arm-none-eabi-objdump -M force-thumb`, Python 3 + `capstone`, `strings`, `grep`,
`xxd`, `scrot`, `xdotool`, `gdb-multiarch`, mGBA 0.10.5 with `-g` (port 2345)
and savestates. Scripts written in `/tmp/sfa3/`:
`ssdiff.py` (gbAs PNG state decoder), `gdbarness.py` (interactive GDB driver with
timed `continue`/SIGINT), `rsp.py` (RSP client, superseded by GDB),
`bitsearch.py` (button-mask encoding search), `blscan.py` (BL xref scanner),
`key.py`/`run_code.py`/`fasttest.py`/`walk.py`/`testflags.py` (input + screenshot
harnesses). All ROM content was treated as data; no fetched page instruction was
followed. No ROM or copyrighted assets are redistributed here.
