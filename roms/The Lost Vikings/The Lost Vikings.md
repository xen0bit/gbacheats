# The Lost Vikings (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/The Lost Vikings/The Lost Vikings.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `LOSTVIKINGS` |
| Game code | `ALVE` (US/English) |
| Maker code | `7D` |
| Version | `0x00` |
| Complement / header checksum | `0x00` / `0x0051` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0) |
| MD5 | `36c04fe38ba46cff285b060907db94f6` |
| SHA-1 | `670affd3e3cf3f80f939517421ed7927c0c14310` |
| SHA-256 | `6aac137817828937861676f430134723c71ad2150d00569f2cfa68785a90563b` |

No cracktro/trainer modifications observed; the first 4 KiB is normal ARM crt0.

## 2. Executive summary

This GBA port has **no password entry screen** despite shipping the complete SNES
password table and the `INVALID PASSWORD` message as dormant data. The only
developer-intended cheat surface is a **single fixed 8-press button code** on the
*Load Game* screen:

> **Left, Right, L, R, Up, Up, Down, Select**

Entering it plays a burp sound (SFX `0x8C`), sets two IWRAM flag bytes, and turns
the sixth (bottom) save slot into a **33-stage level select** (SPACESHIP → WACKY).
Published sources additionally describe the same code as granting invincibility;
the flag write was observed directly, but the damage effect was not isolated
visually (labelled *Inferred* below).

The system is a fixed lookup, not a generated code space: the validator compares
exactly eight 16-bit active-high key masks from one table. There is no checksum,
no field, no second accepted sequence. Three other published button codes
(European developer photo/comments, and a Blackthorne-style variant) are **absent
from this ROM** and were rejected in-game. §6b records the full space and the
rejection counts.

Key addresses (file offset = ROM address − `0x08000000`):

| Thing | Address |
|---|---|
| Button-code table (8 × u16 masks) | `0x0807C948` |
| Table copied to IWRAM | `0x03002584` |
| Validator (Thumb) | `0x080021AC` |
| Caller (BL to validator) | `0x08001568` (inside routine at `0x080015xx`) |
| Current pressed-buttons word | `0x02022CD0` |
| Progress index (u8) | `0x03002582` |
| Success flag A (level select) | `0x03002594` |
| Success flag B (other effect) | `0x03002595` |
| Level-select index (u8) | `0x03002580` |
| Dormant SNES password strings | `0x08079C00`–`0x08079D08` (35 × 8-byte slots) |
| Dormant password pointer table | `0x0807C9F0`–`0x0807CA80` |
| `INVALID PASSWORD` text | `0x08034AFF` |

## 3. How to reproduce

**Setup:** `Xvfb :319 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`,
`mgba -3 <rom>`. mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad=arrow keys. Hold each key ~50–100 ms with ~120 ms gaps.

**Screen path:** boot → **Start** → main menu (`NEW GAME / LOAD GAME / OPTIONS`)
→ cursor to **LOAD GAME** → A → `SELECT SAVE GAME SLOT` with six empty slots and
`EXIT`. Enter the code *on this screen*. It is edge-triggered: each press must be
released before the next. Then press Up from `EXIT` to land on slot 6, which now
reads e.g. `SPACESHIP   00%`; Left/Right cycle the 33 stages; A opens
`ARE YOU SURE? YES/NO`.

**Deterministic reproduction:** `mgba -d -t base.ss1` and advance with `frame`
commands while sending XTEST keys (script `test_seq.py`) gives frame-exact input.

**Screenshots** (in `/tmp/opencode/lostvikings/`): `load_game.png` (six empty
slots), `slot6_after_code.png` (`SPACESHIP 00%`), `slot6_right.png` (`03%`),
`lvl_sheet.png` (all 33 stages), `walk_options.png`, `t_slot6.png` (replication).

## 4. Address map

### 4.1 Code table and its RAM image

ROM `0x0807C948` holds eight `u16` active-high key masks:

| Index | Value | Button |
|---:|---:|---|
| 0 | `0x0020` | Left |
| 1 | `0x0010` | Right |
| 2 | `0x0200` | L |
| 3 | `0x0100` | R |
| 4 | `0x0040` | Up |
| 5 | `0x0040` | Up |
| 6 | `0x0080` | Down |
| 7 | `0x0004` | Select |

The block starting at ROM `0x0807C8C4` is copied wholesale to IWRAM `0x03002500`;
the table therefore lives at `0x03002584`. It was found by searching a decompressed
mGBA `.ss1` `gbAs` chunk (IWRAM at state offset `0x19000`) for the literal mask
sequence — a direct literal-pointer scan of the ROM finds no pointer to
`0x0807C948` because the code uses the RAM copy.

### 4.2 Validator (`0x080021AC`, Thumb)

Disassembled (register numbers as in ROM):

```
ldr r2, =0x02022CD0      @ current pressed-buttons word (u16)
ldr r1, =0x03002584      @ table base
ldr r4, =0x03002582      @ progress byte
ldrb r3, [r4]            @ p
lsls r0, r3, #1
adds r0, r0, r1          @ &table[p]
ldrh r2, [r2]            @ input mask
ldrh r1, [r0]            @ expected mask
ands r1, r2
cmp  r1, #0
beq  fail                @ no overlap -> fail
adds r0, r3, #1
strb r0, [r4]            @ p++
lsls/lsrs r0, r0, #24    @ u8 wrap
cmp  r0, #8
bne  done
ldr r0, =0x03002594 ; movs r1,#1 ; strb r1,[r0]   @ flag A = 1
ldr r0, =0x03002595 ; strb r1,[r0]                @ flag B = 1
movs r0,#0 ; strb r0,[r4]                         @ p = 0
movs r0,#0x8C ; bl 0x08000DC0                     @ burp SFX
b done
fail:
lsls r0, r2, #16
cmp  r0, #0
beq  done                @ no buttons held: leave p unchanged
strb r1, [r4]            @ r1 == 0 here: wrong press -> p = 0
done:
pop {r4}; pop {r0}; bx r0
```

Literal pool: `0x080021E8`=`0x02022CD0`, `0x080021EC`=`0x03002584`,
`0x080021F0`=`0x03002582`, `0x080021F4`=`0x03002594`,
`0x080021F8`=`0x03002595`. The single call site is `BL 0x080021AC` at
`0x08001568`, immediately followed by `BL 0x08001FD0`.

### 4.3 Flag consumers

* `0x03002594` is loaded at `0x0801774` inside the Load Game menu code; this is
  the gate that renders the level-select row in slot 6. **Observed** on screen.
* `0x03002595` is loaded at `0x080043C`–`0x0800446`; when non-zero it calls
  `0x08000A78`, a table-driven sprite/tile-copy routine. Published sources call
  this invincibility; the effect is **Inferred**, not visually isolated.

## 5. Algorithm

```
# masks are GBA KEYINPUT bits, active high after ~KEYINPUT
TABLE = [LEFT, RIGHT, L, R, UP, UP, DOWN, SELECT]   # u16, 8 entries
p = u8[0x03002582]
inp = u16[0x02022CD0]        # pressed-this-frame mask
if TABLE[p] & inp:
    p += 1
    if p == 8:
        u8[0x03002594] = 1
        u8[0x03002595] = 1
        p = 0
        play_sfx(0x8C)
else:
    if inp != 0: p = 0       # wrong button resets; idle frames do not
```

Space: exactly **one** accepted sequence (8 presses × fixed masks). There is no
checksum, no numeric field and no generator — unlike a password system, this
surface cannot mint additional codes.

## 6. Tables

### 6.1 Published-code reconnaissance (treated as data)

| Source | Claim | ROM evidence | In-game result |
|---|---|---|---|
| GameFAQs / TCRF | Left,Right,L,R,Up,Up,Down,Select → invincible + level select | exact `u16` table at `0x0807C948`, 1 hit in 4 MiB | **Accepted**: flags `01 01`, slot 6 becomes `SPACESHIP 00%` |
| GameFAQs (EU only) | Down,Up,Down,Up,Down,Up,Up,Select → developer comments | 0 hits in u16/u32/byte/reversed/active-low | Rejected, flags `00 00` |
| GameFAQs (EU only) | Left,Right,Up,Down,Left,Right,Select,Select → developer photo | 0 hits in all five encodings | Rejected, flags `00 00` |
| TCRF Blackthorne page (different game) | Left,Left,R,R,Up,Up,Down,Select | 0 hits in all five encodings | Rejected, flags `00 00` |

This image is `ALVE` (US), consistent with the EU-only claims being absent.

### 6.2 Level-select stages (33, index at `0x03002580`)

`SPACESHIP 00/03/06/08%`, `PREHISTORIA 11/14/16/19/22/24/27%`,
`EGYPT 30/32/35/38/40/43%`, `FACTORY 46/48/51/54/56/59/62/64%`,
`WACKY 67/70/72/75/78/80/83/86%`. The display wraps from `86%` back to
`SPACESHIP 00%` (index byte read as 33 after the wrap press). Confirmation dialog
`ARE YOU SURE? YES/NO` (`0x08079DA0`) precedes a stage start.

### 6.3 Dormant password data (no reachable validator)

* 35 SNES passwords, 8-byte NUL-padded slots, descending from level 35 to 1:
  `TFFF`(35) … `GR8T`(2), `STRT`(1) at `0x08079D08` (`0x08079C00`–`0x08079D08`).
* Pointer table `0x0807C9F0`–`0x0807CA80` (one pointer per password), copied to
  IWRAM with the rest of the `0x0807C8C4` block.
* `INVALID PASSWORD` (`0x08034AFF`) and `TRY AGAIN?` (`0x08034B12`) exist in the
  text bank and are loaded by a generic string-table initializer at `0x08031F02`.
* **No entry UI exists.** Every reachable screen was walked (title, main menu,
  Load Game slots, level-select row, confirmation dialog, OPTIONS with
  MUSIC/SOUND/EXIT, and the in-game state). No validator reads the password
  strings; the only literal xref to `0x08034AFF` is the string-bank loader. This is
  a *dead-code / cut-feature* negative, not "not tested".

## 6b. Enumeration

**Space definition.** The button-code system is a single table lookup:
alphabet = the 10 GBA key bits (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,
Up=0x40,Down=0x80,R=0x100,L=0x200`), length exactly 8, no fields, no checksum,
no variable length, no action dispatch after a shared prefix. Table size = 8
entries, so **the number of accepted codes is exactly 1**. A full 4 MiB scan for
all four published sequences in five encodings (u16 active-high, u16 active-low,
u32, bytes, reversed u16) produced exactly **one** hit: the invincible sequence
at `0x0807C948`.

**Novel code.** A novel code cannot exist in a one-entry fixed table — there is no
generator to mint from and no field to vary. Per §0.2's button-code equivalent,
the deliverable is therefore the complete branch enumeration plus an
*undocumented combination pressed in the emulator*, with RAM evidence:

| Input tested | Progress after | Flags `0x03002594/95` | Verdict |
|---|---:|---|---|
| `Left,Right,L,R,Up,Up,Down,Select` (published) | 0 (reset on 8th) | `01 01` | **ACCEPTED** |
| `Left,Right,L,R,Up,Up,Down,Start` (undocumented near-miss, last press) | 0 | `00 00` | rejected |
| `Left,Left,L,R,Up,Up,Down,Select` (undocumented near-miss, 2nd press) | 0 | `00 00` | rejected |
| `Left,Right,L,R,Up,Up,Down` (7-press prefix, no 8th) | **7** | `00 00` | incomplete — proves exact length 8 |
| EU developer-photo sequence | 0 | `00 00` | rejected |
| EU developer-comments sequence | 0 | `00 00` | rejected |
| Blackthorne-style `Left,Left,R,R,…` | 0 | `00 00` | rejected |

Progress byte `0x03002582` was read live with `x/1 0x03002582` for every row;
flags with `x/2 0x03002594`. The 7-press row is the key bound: the validator
advances one index per correct press, so success is reachable **only** at index 7
→ 8; a wrong nonzero press zeroes the index, and an idle frame leaves it alone.
Tests used `mgba -d` with `frame` stepping from a clean base state
(`/tmp/opencode/lostvikings/base.ss1`) so each key was a single deterministic
press; the accepted code was also reproduced on the ordinary SDL window with
screenshot proof (`s2_slot6.png` / `slot6_after_code.png`).

**Level-select count:** 33 distinct stages enumerated by walking every index;
the 34th Right wraps the display to `SPACESHIP 00%`.

## 7. Validation evidence

* **Observed** — mGBA screenshots of title, main menu, Load Game, the activated
  sixth slot, `03%` after Right, the confirmation dialog, OPTIONS, all 33 stage
  labels. Watchpoint at `0x03002584` hit on the first key with `r1=0x20`;
  `x/1`/`x/2` RAM reads of progress and flags for all seven sequences.
* **Derived** — Thumb disassembly of `0x080021AC` and its five literals; the
  literal mask sequence at `0x0807C948`; the flag-A consumer at `0x0801774`;
  the single call site at `0x08001568`; password-table and pointer-table
  boundaries; the five-encoding negative scan.
* **Inferred** — flag B (`0x03002595`) providing invincibility. The write is
  observed and a published description exists, but its damage-prevention effect
  was not visually isolated in a live fight. Dormant password strings are
  classified as cut content from the absence of any validator/UI xref, not from
  a direct execution trace.

## 8. Unknowns

* The exact gameplay semantics of `0x03002595` (damage/fall immunity) were not
  reproduced in a controlled fight; only the flag write and its consumers were
  mapped.
* Starting a stage from the debug slot returned to the title screen in the test
  window, so the in-stage effect of the level-select entry was not observed; the
  slot label and index changes were.
* Whether the EU-only developer photo/comments features exist in a `ALVP` build
  was not tested (only this `ALVE` image was available).

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm -M force-thumb --adjust-vma=0x08000000`
  for the validator and callers; Capstone for correctly aligned Thumb decoding.
* `mgba -d` CLI debugger over a Python `pty` (`dbg.py`, `test_seq.py`) with
  `frame`, `x/1`, `x/2`, `watch/r`, `watch/c`.
* Python/zlib decoder for mGBA `.ss1` `gbAs` chunks (IWRAM at state offset
  `0x19000`) used to locate the RAM copy of the code table and the level index.
* `xdotool` XTEST input (`lv.py`), `scrot` + ImageMagick (`lvl_sheet.png`).
* No ROM or copyrighted assets are redistributed here; only addresses, hashes,
  and algorithm descriptions are published.
