# Dexter's Laboratory: Chess Challenge (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dexter's Laboratory: Chess Challenge.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `DEXTER CHESS` |
| Game code | `ADXE` |
| Maker | `6L` (Virtucraft) |
| Version | `0x00` (Rev.00) |
| Header `0x96` | `0x96` (valid) |
| Complement check `0xBD` | `0x4B` — recomputed value is also `0x4B` (valid) |
| Header checksum `0xBE` | `0x0000` — the recomputed value is `0x16E6`; a `0000` header checksum with a correct complement is the usual artifact of a rebuilt/trimmed header |
| Entry word | `0xEA00002E` → `0x080000C0`, stock crt0 branch (no cracktro) |
| MD5 | `da1471e76473766f201ead7c9c9e3595` |
| SHA-1 | `a6725f72bbc29c270322eab0d8043f7c16e1c96d` |
| SHA-256 | `5a8b8817870622cc9f97de843ec70d7904adb3f62343ef4d76e969936af88b28` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at file
`0x4` → a single GBA image, no 2-in-1 shell, no second header, nothing appended.
The entry word and the first 4 KiB are stock; no trainer, cracktro or entry patch
was found (§16.1 checked and negative).

## 2. Executive summary

The game has a real, developer-implemented password screen
(**OPTIONS → PASSWORD**, 16 character cells), and it is the only cheat surface:
no button codes, no debug menu, no hidden test screen was found in this image.

* The code is **16 symbols drawn from a 16-letter alphabet**
  (`B C D F G H J K L M N P Q R S T`), i.e. one 4-bit nibble per cell, 64 bits total.
* The game stores the entered code as **16 32-bit words (values 0..15) at IWRAM
  `0x03007A88`**, in two display rows: cells 1–8 show words 8–15 and cells 9–16
  show words 0–7.
* Pressing **A** runs an integrity check and then either shows
  **`PASSWORD ACTIVE`** with the decoded setup (PLAYER 1 / PLAYER 2 / TIER /
  SIDE / LEVEL / USE?) or **`PASSWORD DENIED`**.
* The 30 published level passwords (GameFAQs / emuinfo) are all real: they share
  the constant first half `CSHJMQNS` and differ only in the second half
  (`01 GRDSJJCP` … `30 BLRNKHHM`). Two of them were loaded into the buffer and
  accepted on screen (`PASSWORD ACTIVE`).
* **Every one of the 64 bits is integrity-checked.** All 16 single-nibble +1
  mutations of a valid code are rejected in-game (`PASSWORD DENIED`), and
  compensating two-nibble mutations are also rejected. The check is not a plain
  nibble-sum.
* The game's own encoder fills the screen from a fresh save with
  **`CSHJMQNSKTGRDHFN`**, a code that appears in **no published list** and that the
  game accepts — so the accepted set is strictly larger than the published list
  (31 accepted codes observed, 30 published).

## 3. How to reproduce

Emulator: mGBA 0.10.5 under `Xvfb :303`, `SDL_AUDIODRIVER=dummy`, `mgba -3`.
Default mGBA SDL keymap: **A = `x`, B = `z`, Start = `Return`, Select = `BackSpace`,
D-pad = arrows**; hold keys 50–120 ms.

Menu path (from a cold boot):

```
Cartoon Network splash → Virtucraft → title screen
Return (title) → main menu: TOURNAMENT / VERSUS / QUICK GAME / PUZZLE / OPTIONS
Down ×4, A            → OPTIONS
Down ×5, A            → PASSWORDS (16 cells, cursor on cell 1)
Up / Down            → change the letter (+1 / −1, wraps at 16)
Left / Right         → move the cell cursor
A                    → submit
B                    → back
```

Result screen: `PASSWORD ACTIVE` (fields shown) or `PASSWORD DENIED` (no fields).
`A` on the ACTIVE screen opens `USE? YES/NO`; `Down, A` returns to the main menu.

The 16-cell buffer can be reproduced deterministically either by typing or, for
bulk tests, by writing IWRAM `0x03007A88` (16 little-endian `u32`, values 0..15)
through a game-state patch; the display is refreshed on the next cursor move.
Address and value semantics were confirmed by watching the same words change when
`Up` is pressed:

```
mGBA savestate .ssN → PNG chunk "gbAs" → zlib → 397,312-byte state
IWRAM = state offset 0x19000 (i.e. 0x03000000 maps to 0x19000)
EWRAM = state offset 0x21000
```

## 4. Address map

| Address (ROM / RAM) | Meaning |
|---|---|
| `0x080000C0` | crt0 (stock ARM branch target) |
| `0x080009E4` | keypad IRQ handler: reads `0x04000130`, builds `~KEYINPUT & 0x3FF` |
| `0x02000A48` | current key mask (active-high, `A=1 … L=0x200`) |
| `0x02000B52` | last/newly-pressed key word |
| `0x03007A88` | **password buffer**: 16 × `u32`, each 0..15 (words 0..7 = display row 2, words 8..15 = display row 1) |
| `0x0802248C` | password-screen update routine (draw + input); buffer pointer arrives in `[sp+0xE0]` |
| `0x08022530` | test of the `Up` mask (`0x40`) |
| `0x08022548` | increment selected cell, wrap `15 → 0` |
| `0x08022598` | test of the `Down` mask (`0x80`) |
| `0x080225CC` | decrement selected cell, wrap `0 → 15` |
| `0x08022762` | read of a buffer word inside the per-frame draw loop |
| `0x08569890`–`0x0856A500` | English UI text bank (`CHECK`, `PASSWORD ACTIVE`, `PASSWORD DENIED`, `USE?`, `LEVEL:`, `TIER:`, `SIDE:`, `PLAYER 1:`, …) |
| `0x0856F0C8` / `0x08575058` / `0x08580E97` / `0x08586493` | French / German / Spanish / second English copies of the same bank |

Selected string offsets (file offsets; ROM address = `0x08000000 + offset`):

| File offset | String |
|---:|---|
| `0x569A6C` | `SETTINGS AND PASSWORDS` |
| `0x569A8B` | `PASSWORD ACTIVE` |
| `0x569A9B` | `PASSWORD DENIED` |
| `0x569AAB` | `USE?` |
| `0x569AB0` | `LEVEL:` |
| `0x569AD3` | `TIER:` |
| `0x569AEE` | `SIDE:` |
| `0x569AFF` | `PLAYER 1:` |
| `0x569C39` | `PASSWORD` (options entry) |
| `0x569DC8` | `YOU HAVE UNLOCKED` |
| `0x569DDA` | `BOY GENIUS MODE` |
| `0x569DEA` | `PUZZLE MODE` |
| `0x569EF0`–`0x569F13` | `! "#$% … >?@ABC` character-set fragments (font/name-entry range) |

Note: no 32-bit pointer to this text bank exists anywhere in the image; the
strings are reached by an index/lookup path, so a pointer scan for
`0x08569xxx` returns zero hits. This is why the bank looks “unreferenced”.

## 5. Algorithm (as implemented by the screen)

```
; password buffer  B[0..15]  (u32 each, 0..15), base 0x03007A88
; display: row1 = B[8..15], row2 = B[0..7]
; alphabet index -> glyph: 0=B 1=C 2=D 3=F 4=G 5=H 6=J 7=K
;                          8=L 9=M 10=N 11=P 12=Q 13=R 14=S 15=T

cursor = 0                                   ; cell index 0..15
w = (cursor < 8) ? &B[cursor+8] : &B[cursor-8]   ; row1 first on screen

on Up:    (*w)++;  if (*w > 15) *w = 0        ; 0x08022548
on Down:  (*w)--;  if (*w < 0)  *w = 15       ; 0x080225CC
on A:     check(B) ? show(PASSWORD ACTIVE, decode(B))
                   : show(PASSWORD DENIED)
```

The code is filled from the current save when the screen opens; a fresh save
produces `CSHJMQNS` + `KTGRDHFN`.

Decode screen fields (from the constant half `CSHJMQNS`, identical for every
published code): PLAYER 1 = DEXTER, PLAYER 2 = DEE DEE, TIER = TIER 1,
SIDE = WHITE, LEVEL = EASY, USE? = YES. The variable half (cells 9–16) does not
alter any of these five fields; it carries the tournament stage.

Integrity model (measured, not guessed): the accept path rejects every
single-nibble change anywhere in the 64-bit code, so all 64 bits participate in
the check. Two “compensating” pairs (`b0+1/b1-1`, `b2+1/b3-1`, `b0+1/b8-1`) are
also rejected, so the check is not a plain equal-weight nibble sum. The exact
arithmetic (table, CRC-like or keyed permutation) was not recovered from the
assembly in this engagement — see §8.

## 6. Tables

### 6.1 Alphabet (16 symbols → 4-bit value)

```
value : 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
glyph : B C D F G H J K L M  N  P  Q  R  S  T
```

### 6.2 Buffer layout

| Cells (screen) | Buffer words | Published value |
|---|---|---|
| 1–8 (row 1) | `B[8..15]` = `0x03007AA8 … 0x03007AC4` | constant `CSHJMQNS` = `1,14,5,6,9,12,10,14` |
| 9–16 (row 2) | `B[0..7]` = `0x03007A88 … 0x03007AA4` | varies with stage |

### 6.3 Published codes, verified against the ROM format

All 30 codes, decoded to nibbles (second half only; the first half is always
`CSHJMQNS` = `1,14,5,6,9,12,10,14`):

```
01 GRDSJJCP  4,13, 2,14, 6, 6, 1,11     16 RRDQRGGM 13,13, 2,12,13, 4, 4, 9
02 HQJSJJBP  5,12, 6,14, 6, 6, 0,11     17 GRGFFQSR  4,13, 4, 3, 3,12,14,13
03 TTHRDGDN 15,15, 5,13, 2, 4, 2,10     18 RSRJLLNK 13,14,13, 6, 8, 8,10, 7
04 KPHHDKFN  7,11, 5, 5, 2, 7, 3,10     19 QMRCFFPH 12, 9,13, 1, 3, 3,11, 5
05 QGPFCLMH 12, 4,11, 3, 1, 8, 9, 5     20 QRDLMGGL 12,13, 2, 8, 9, 4, 4, 8
06 HSJSDGBF  5,14, 6,14, 2, 4, 0, 3     21 BMGFFRSM  0, 9, 4, 3, 3,13,14, 9
07 TKHQNGBN 15, 7, 5,12,10, 4, 0,10     22 QBSFDSRF 12, 0,14, 3, 2,14,13, 3
08 FNHHDJFS  3,10, 5, 5, 2, 6, 3,14     23 SMRCHFPC 14, 9,13, 1, 5, 3,11, 1
09 QQPFMNMG 12,12,11, 3, 9,10, 9, 4     24 QHBLMGJN 12, 5, 0, 8, 9, 4, 6,10
10 HSJJBGNF  5,14, 6, 6, 0, 4,10, 3     25 BMQDFHQM  0, 9,12, 2, 3, 5,12, 9
11 SKRGNBBN 14, 7,13, 4,10, 0, 0,10     26 GLRPKGHP  4, 8,13,11, 7, 4, 5,11
12 TRJQHGQM 15,13, 6,12, 5, 4,12, 9     27 GFLMPSKD  4, 3, 8, 9,11,14, 7, 2
13 SQTKMNMQ 14,12,15, 7, 9,10, 9,12     28 QKLMMQJN 12, 7, 8, 9, 9,12, 6,10
14 RSKJLGNK 13,14, 7, 6, 8, 4,10, 7     29 BLRNKHQM  0, 8,13,10, 7, 5,12, 9
15 QPMCFFFK 12,11, 9, 1, 3, 3, 3, 7     30 BLRNKHHM  0, 8,13,10, 7, 5, 5, 9
```

The list is algorithmic, not a stored table: the literal ASCII strings, the
packed-nibble forms and the byte-per-cell forms of these codes are all absent
from the 8 MiB image (`grep`/binary search returns 0 hits), so the game derives
them at run time.

### 6.4 Other cheat-surface strings checked

| String | Address | Assessment |
|---|---|---|
| `PASSWORD ACTIVE` / `PASSWORD DENIED` | `0x569A8B` / `0x569A9B` | the password result screen (reached) |
| `YOU HAVE UNLOCKED` / `BOY GENIUS MODE` / `PUZZLE MODE` | `0x569DC8`/`DD`/`EA` | unlock-message block; `BOY GENIUS` exists as a greyed tournament difficulty, `PUZZLE` exists as a menu entry — the *message* was not observed on screen (see §8) |
| `FIXED ALL MACHINES`, `GOT ALL TOOLS`, `LOW GRAVITY`, `STRONG ENEMIES`, `DEXTER-ROO`, `START LIVES`, `MAP/JUMP/PUNCH` | `0x569DF6`–`0x569EE5`, `0x569C53`, `0x569CA0`–`0x569CD6` | **unused leftovers** from the sibling n-Space/Virtucraft platformer engine (Dexter's Laboratory: Deesaster Strikes); no reader reaches them in this game |
| `SECRET` / `OWN SECRET` | `0x569F3C` / `0x56A36E` | character-biography text (“…OF HIS OWN SECRET LABORATORY!”), not a code |

## 6b. Enumeration

**Space definition.** 16 cells × 4 bits = **64 bits**; alphabet of 16 symbols,
no shorter/longer form, no wildcard symbol, no reserved cell observed (all 16
cells are editable and all are checked). Nominal space `16^16 = 2^64 ≈ 1.84×10^19`.
The accepted set is a proper, hard-to-reach subset: the accept path verifies the
whole 64-bit word (below).

**Known-accepted set.**

| # | Code | Source | In-game proof |
|---|---|---|---|
| 1–30 | `CSHJMQNS` + published half, levels 01–30 | GameFAQs / emuinfo list | level 02 (`HQJSJJBP`) and level 30 (`BLRNKHHM`) loaded into `0x03007A88` and submitted → `PASSWORD ACTIVE`, fields DEXTER / DEE DEE / TIER 1 / WHITE / EASY |
| 31 | **`CSHJMQNSKTGRDHFN`** | generated by the game itself for a fresh save when the screen opens | submitted in-game → `PASSWORD ACTIVE`, same field set (`ref_active` capture); this code appears in **no** published list |

`CSHJMQNSKTGRDHFN` is the deliverable “code outside every published list”: it is
a valid state the format accepts, and it demonstrates that the published 30 are
not the whole accepted set (31 observed, at least).

**Bounds proven by rejection.** Starting from the accepted code
`1,14,5,6,9,12,10,14, 7,15,4,13,2,5,3,10` (= `CSHJMQNSKTGRDHFN`), a `+1` was
applied to each of the 16 cells in turn; **all 16 variants were rejected**
(`PASSWORD DENIED`, background-only screen, no field block):

```
cell 0  +1 -> DENIED      cell 8  +1 -> DENIED
cell 1  +1 -> DENIED      cell 9  +1 -> DENIED
cell 2  +1 -> DENIED      cell 10 +1 -> DENIED
cell 3  +1 -> DENIED      cell 11 +1 -> DENIED
cell 4  +1 -> DENIED      cell 12 +1 -> DENIED
cell 5  +1 -> DENIED      cell 13 +1 -> DENIED
cell 6  +1 -> DENIED      cell 14 +1 -> DENIED
cell 7  +1 -> DENIED      cell 15 +1 -> DENIED
```

Compensating pairs (`cell0+1 & cell1−1`, `cell2+1 & cell3−1`,
`cell0+1 & cell8−1`) were also rejected, ruling out an equal-weight nibble sum
and showing that the check spans both halves (a checksum confined to one half
would have accepted a change entirely inside the other half).

**Not-expressible inputs.** Values above 15 cannot be entered: the per-cell
handler wraps at 16 (`cmp #15` / `movs r0,#0` at `0x08022548`, and `cmp #0` /
`movs r0,#15` at `0x080225CC`), so the on-screen keyboard cannot produce an
out-of-alphabet symbol; the bound is enforced in the input handler itself.

## 7. Validation evidence

**Observed (emulator, RAM)**
* The password screen, its 16 cells, alphabet cycle and result screens
  (`PASSWORD ACTIVE` / `PASSWORD DENIED`) — booted and walked on `:303`.
* `0x03007A88` holds the 16 nibbles; pressing `Up` on cell 1 changes word 8 and
  nothing else in the code region; the draw loop reads the same words
  (watchpoint on `0x03007AA8` stops at `0x08022548` on the write and
  `0x08022762` on the read).
* `PASSWORD ACTIVE` for the 30-code format (levels 02 and 30) and for the
  game-generated `CSHJMQNSKTGRDHFN`.
* `PASSWORD DENIED` for all 16 single-nibble mutations and for the three
  compensating pairs.

**Derived (instruction level)**
* Input handling: `Up`/`Down` masks `0x40`/`0x80`, increment/decrement with
  16-wrap at `0x08022548` / `0x080225CC`, buffer pointer taken from `[sp+0xE0]`.
* Alphabet/value mapping from the identity between stored words and rendered
  glyphs (words `7,15,4,13,2,5,3,10` render as `K T G R D H F N`).
* Text bank layout and absence of any literal pointer into it (whole-ROM scan).

**Inferred (not fully exercised)**
* That the variable half encodes the tournament stage; the decode screen shows
  only P1/P2/TIER/SIDE/LEVEL, all carried by the constant half.
* That `YOU HAVE UNLOCKED / BOY GENIUS MODE / PUZZLE MODE` is reachable as an
  unlock message in this title (the strings and the two game features exist, but
  the message was never displayed during the walk).
* That the platformer strings are shared-engine leftovers (they have no
  plausible use in a chess game, but no reader was disassembled).

## 8. Unknowns

* **The integrity/check function itself was not recovered.** All 64 bits are
  checked, but the arithmetic (keyed permutation, table CRC, or per-half CRC) is
  not yet in hand; consequently no *arbitrary* code could be minted beyond the
  one the game's own encoder produces. Recovering it needs a breakpoint inside
  the accept path (the `A` branch that calls the check), which was not reached
  before the session budget ran out; the address map above narrows the search to
  the routine containing `0x08022548`–`0x08022762` and its caller.
* Whether the accepted set is exactly “one code per (setup, stage)” (≈30×setup
  combinations) or larger, and whether the constant half can legitimately vary
  (other characters / DARK side / BOY GENIUS) — the tournament character-select
  screen was used to change P1/P2 but the re-opened password screen still
  prefilled `CSHJMQNSKTGRDHFN`, so the encode side is driven by the save record,
  not by the character-select screen.
* `BOY GENIUS` appears greyed in the tournament menu; whether it is unlocked by
  a password, by clearing a tier, or is simply disabled in this build is not
  proven.

## 9. Tooling

* mGBA 0.10.5 (`mgba -3`, `-g` GDB stub on `:2345`), `gdb-multiarch`,
  `Xvfb :303` + `openbox`, `xdotool`, `scrot`/ImageMagick `import`,
  `arm-none-eabi-objdump -M force-thumb`, Python 3 + Capstone 5.0.7.
* Custom scripts (in `/tmp/opencode/dexterchess`):
  * `dex.py`-style header/literal scans (`struct`, `grep -abo`),
  * savestate reader: PNG `gbAs` chunk → zlib → IWRAM at `0x19000`,
  * `patchstate.py`: rewrite the `gbAs` chunk to inject 16 `u32` into
    `0x03007A88` and reload the slot with `F9`,
  * `vtest.py`: submit-and-classify loop (`ImageMagick compare` against the
    `PASSWORD ACTIVE` / `PASSWORD DENIED` reference crops).
* Legal: no ROM, graphics, music or text assets are redistributed; only
  addresses, the alphabet, the published codes and the observed behaviour.

## 10. Screenshots kept as evidence

`ref_active_c.png` (PASSWORD ACTIVE for `CSHJMQNSKTGRDHFN`),
`ref_denied_c.png` (PASSWORD DENIED after a one-nibble mutation),
`shot_02.png`/`shot_03.png` (main menu, options), `shot_09`/`shot_10` (password
screen), `cur.png` walks. Files live in `/tmp/opencode/dexterchess` and are not
part of the repository.
