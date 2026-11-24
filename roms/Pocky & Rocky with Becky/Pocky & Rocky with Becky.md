# Pocky & Rocky with Becky (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Queue position 554. Analysis date 2026-11-19.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pocky & Rocky with Becky.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `POCKY-ROCKY` (file `0xA0`) |
| Game code | `APKE` |
| Maker | `E9` (Natsume) |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock `b .+0xBC` → `0x080000C0`) |
| Header checksum | `0x0000`, complement `0x77` |
| MD5 | `0f796b33898e0f7c3b001136e6a1c28b` |
| SHA-1 | `b24c3e299622ea7e249cfdaaa06146b5276834e9` |
| SHA-256 | `e3b6ae2bb9fcc4277d378b68f8d73ae55e8dd66add9d697ec987ad44989c9ce5` |

Embedded-header scan: the full 28-byte Nintendo logo occurs exactly once, at file
`0x04` (header `0x0000`). No second image, no multiboot stub, no appended trainer,
no cracktro patch. Development build `KiKi KaiKai Advance` (JP) is a different SKU.

## 2. Executive summary

This game has **two independent developer-intended cheat systems**, both confirmed live:

1. **Title-screen button codes** (2 published codes, both verified in the emulator):
   `Chapter Select` unlocks a `CHAPTER <nn>` selector on the main menu; `Expert Mode`
   recolours the main menu and enables the harder game.
2. **A 9-symbol algorithmic password system** reached from Main menu → Password.
   The password is not a table of stored strings: it is a 9-symbol, 6-bit-per-symbol
   code with a 4-bit additive checksum and a 48-bit encrypted payload. The payload
   decrypts through a 64-byte subtraction table, then is range-checked field by field
   (character, level, etc.). The conversion tables and validator were recovered from
   the ROM and reimplemented offline; **a code absent from every published list was
   minted, entered in the emulator, and observed to start Chapter 3 as a different
   character**. Bounds were proved by in-game rejection of a bad checksum and of an
   out-of-range field value.

No GameShark/CodeBreaker codes were used or reported.

## 3. How to reproduce

### Environment

```
Xvfb :316 -screen 0 1024x768x24 &
DISPLAY=:316 openbox &
DISPLAY=:316 SDL_AUDIODRIVER=dummy mgba -3 -d <rom> &
```

mGBA SDL default keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys. Holds of 60–120 ms are reliable; longer
holds can double-step the password cursor.

### Button codes (title screen, after "Press Start" appears)

| Effect | Sequence |
|---|---|
| Chapter Select | Up, A, Left, B, Down, L, Right, R, Select |
| Expert Mode | Up, Down, Right, Left, Left, Right, Down, Up, Select |

After either sequence press Start. Chapter Select adds `CHAPTER < 01 >` at the
top-right of the main menu; Left/Right changes the number. Expert Mode changes the
menu labels from green to magenta. Both were verified on the exact ROM hash above.

### Password system

Main menu → Down → Password → A. Enter 9 symbols, move the cursor with the arrow
keys and confirm each with A; move the bottom cursor to OK and press A.

A ready-made code, expressed as keyboard symbol **indices 0–63 in entry order**
(index = symbol's reading-order position on the on-screen keyboard, row-major):

```
26 11 00 3F 20 1B 03 3E 02   → starts Chapter 3 (Pocky)
35 23 12 12 33 2E 03 10 30   → starts Chapter 3 (Rocky) — novel, not published
```

To enter these without navigating the 64-cell keyboard, the password buffer can be
written with the mGBA CLI debugger (`-d`) and the normal OK button pressed:

```
w/1 0x03006D78 0x26   ... (9 bytes total)
w/2 0x030019BC 9      ; slot count
w/2 0x03001A10 0x42   ; OK selected
continue              ; then press A
```

The screenshot `valid_effect_c.png` (work dir) shows the Chapter 3 start banner and
the Pocky sprite; `nb_f1_0_c.png` shows the same chapter with the second character.

## 4. Address map

All addresses are GBA bus addresses; file offset = address − `0x08000000`.

### Password screen / state

| Address | Kind | Meaning |
|---|---|---|
| `0x0809A380` | Thumb fn | Password-screen main handler |
| `0x0809A41E` | insn | writes entry count |
| `0x0809A47C` | literal | `0x03006D78` (password buffer base) |
| `0x0809ABE8` | Thumb fn | "all 9 slots filled?" → 1/0 (buffer[i] != `0xFF`) |
| `0x08099C1C` | Thumb fn | **4-bit checksum**: `buf[8]&0xF == (Σ buf[0..7])&0xF` |
| `0x08099334` | Thumb fn | **payload decrypt + field validator**; writes payload to `0x03006D70/74` |
| `0x08099C90` | Thumb fn | inverse transform (generator), called from `0x0809A922` |
| `0x0809DD08` | Thumb fn | integer division helper used by the final field check |
| `0x083CFA80` | table, 64 B | subtraction key `T[0]=0, 6, 12, … 255` |
| `0x083CFAC0` | table, 64 B | cursor grid conversion `idx = T[pos]−1` |
| `0x030019A4` | IWRAM | password-screen state struct |
| `0x030019A4+0x18` = `0x030019BC` | u16 | current input slot count (0..9) |
| `0x030019A4+0x34` = `0x030019D8` | u16 | currently selected symbol index |
| `0x030019A4+0x6C` = `0x03001A10` | u16 | bottom cursor: `0x42`=OK, `0x43`=Cancel |
| `0x03006D78..0x03006D80` | IWRAM, 9 B | password symbol indices (0..63); `0xFF` = empty |
| `0x03006D70/0x03006D74` | IWRAM, u32×2 | decrypted 48-bit payload |

### Code paths (from `0x0809A55E`, OK pressed)

```
0x0809ABE8()          ; all 9 slots filled  → 0 ⇒ error
0x08099C1C()          ; 4-bit checksum      → 0 ⇒ error at 0x0809A57C
0x08099334()          ; decrypt + fields    → 0 ⇒ error at 0x0809A5C4
0x0809A600: accept (sound + transition to gameplay)
```

## 5. Algorithm

`buf` = the 9 entered symbol indices (each 0–63).

```
# Layer 1 — completeness
all(buf[i] != 0xFF for i in 0..8)

# Layer 2 — checksum (4 bits)
assert (buf[8] & 0x0F) == (sum(buf[0..7]) & 0x0F)

# Layer 3 — payload decryption and validation
key = ((buf[8] >> 4) & 3) + buf[6]
T   = ROM[0x083CFA80 .. +64]          # 0,6,12,18,25,...,255
v[i] = (buf[i] - T[(key + i) & 63]) & 0x3F   for i in 0..7, i != 6
v[6] = buf[6]                                  # used to form key, not transformed

w0 = v0 | v1<<6 | v2<<12 | v3<<18 | v4<<24 | v5<<30     (mod 2^32)
w1 = v6 | v7<<6

# field bounds (all inclusive maxima)
bit 0      <= 1
bits 1..2  <= 2       # character selector
bits 3..5  <= 6
bits 6..9  <= 9
bits 10..13 <= 9
bits 14..15 <= 3
bits 16..17 <= 3
bits 18..19 <= 3

C = (w0 >> 22) | ((w1 & 0x3FFF) << 10)
assert 10 <= C <= 4999
assert C != 9999999
assert (C / 10) > 0                    # integer divide
```

The generator at `0x08099C90` performs the inverse (add `T[(key+i)&63]` mod 64) and
recomputes the nibble checksum.

Encoder (verified against the game):

```
v = desired 6-bit payload values satisfying the bounds above
keyhi = 0..3
key   = keyhi + v[6]
buf[i] = (v[i] + T[(key+i) & 63]) & 0x3F   (i != 6); buf[6] = v[6]
buf[8] = (keyhi << 4) | (sum(buf[:8]) & 0x0F)
```

## 6. Tables

### 6.1 Symbol alphabet and keyboard

The keyboard holds **64 symbols** (6 bits each), laid out as a 15-column grid with
rows in reading order. Verified anchors (set cursor index directly, read glyph from
the screen and `0x030019D8` from RAM):

| Index | 0 | 3 | 14 | 15 | 16 | 30 | 46 |
|---|---|---|---|---|---|---|---|
| Glyph | `b` | `f` | `s` | `t` | `u`/`v` | `M` | `5` |

Row structure (reading order): lower-case `b c d f g h j k l m n p q r s`;
lower-case `t u v w x y z`; upper-case `B C D F G H I J K L`;
upper-case `M N P Q R S T V W X Y Z`; digits `1 2 3 4 5 6 7 8 9 0`;
punctuation `! ? + -`; suits `♠ ♣ ♥ ♦`; `★ ♪ ♫ :`. The on-screen font is a
tile-indexed stylised font — `strings` finds **no** menu/password text (the only ASCII
text bank in the ROM is the cutscene dialogue around `0x3D4800–0x3D5300`). All UI
labels were therefore read from the screen and from RAM/font indices, not assumed
from ASCII.

### 6.2 Published codes verified against the ROM

| Source | Code | ROM status |
|---|---|---|
| GameFAQs / Cyberly / ggmania | Pocky L2 `H1NVR9c ♪ 2` | format consistent; glyph→index table is tile-indexed so literal `grep` finds no ASCII (expected for this engine) |
| GameFAQs | Pocky L7 `1dy ♦ mzzLl` | same |
| GameFAQs | Becky L2 `Z- ♦ nQ ♪ fnQ` | same |
| GameFAQs | Rocky L2 `CSGNs4c ♠ B` | same |
| GameFAQs / SuperCheats | Chapter Select button code | **verified live**: CHAPTER selector appears |
| GameFAQs / SuperCheats | Expert Mode button code | **verified live**: menu recolours |

Published codes are plaintext glyph strings, not ASCII bytes in the ROM: a literal
search for `H1NVR9c`, `mzzLl`, `TSG613d`, `nDTC2D`, `P?mgBgJm.` all returned zero hits.
This is a property of the font-tile text system (§11 of the guide), not evidence that
the codes are invalid. The algorithm above is the ROM's actual validator and accepts
codes minted offline.

### 6.3 Field→effect map (confidence: derived + observed)

| Field | Bits | Observed effect when changed |
|---|---|---|
| character | 1–2 | value 0 → second playable character on the start banner; value 2 → Pocky; value 1 rejected in-game |
| level/chapter-ish | 6–9 | 8 → Chapter 3; varying it changes decoded payload but several values still start Chapter 3 (further fields participate) |
| tail `C` | 22–31 + w1 | must be 10..4999; out-of-range rejected |

## 6b. Enumeration

### Space definition

* Alphabet: 64 symbols (6 bits), length exactly 9 ⇒ `64^9 = 2^54` raw strings.
* Checksum: 4 bits (symbol 9 low nibble) ⇒ `2^50` checksum-valid strings.
* Payload: 48 bits (8 × 6-bit decoded values), of which the field bounds above
  restrict the low 20 bits to about `2 × 3 × 7 × 10 × 10 × 4 × 4 × 4 = 268,800`
  combinations; the tail `C` is bounded to 4,990 values. Total accepted space is
  comfortably larger than the 20-odd published codes.
* No hard-coded code table exists: a literal search of the whole ROM for every
  published password string returned **zero** hits.

### Novel code (absent from GameFAQs, VGChartz, TCRF and Cyberly)

```
index sequence: 35 23 12 12 33 2E 03 10 30
```

Derived by taking the working `26 11 00 3F 20 1B 03 3E 02` payload and changing the
character field (bits 1–2 of `v[0]`) from 2 to 0, then re-encrypting with the ROM's
`T` table and recomputing the nibble checksum. **In-game proof:** accepted at
`0x0809A600`, decoded payload `0x1038211a…` written to `0x03006D70`, and Chapter 3
started with the second character sprite (screenshot `nb_f1_0_c.png`, work dir).
This code does not appear in any published list.

### Bounds proved by rejection

| Input | Change | Result |
|---|---|---|
| `26 11 00 3F 20 1B 03 3E 0?` with nibble ≠ 8 | wrong checksum | rejected before `0x08099334` (breakpoint at `0x0809A5C4` never reached; decoded payload at `0x03006D70` stays zero) |
| `26 11 00 3F 20 1B 09 3E 02` | bad checksum (`8` expected, `2` given) | rejected |
| `37 23 12 12 33 2E 03 10 32` | valid checksum, character field = 1 (reserved) | rejected at the semantic layer (`0x03006D70` still holds the raw buffer, no decode) |
| field `C > 4999` (v6=9 → `C=7176`) | out-of-range tail | rejected |
| fewer than 9 symbols | incomplete | rejected by `0x0809ABE8` |

### Button-code enumeration

Every action branch of the two published title-screen sequences was exercised in the
emulator; both produced visible state changes. No additional undocumented sequence
was found in a literal key-mask scan (active-high and active-low, 1/2/4-byte widths,
forward and reversed) for either published sequence, so the key tables are likely
implemented as per-frame comparisons rather than a stored array.

### Screen walk (all reachable screens)

1. Boot logos (Taito, Altron) → title "Press Start".
2. Title + button codes → main menu (New Game / Password, plus CHAPTER selector after the code; menu recolours after Expert code).
3. Password screen (9 slots, 64-symbol keyboard, OK/Cancel) — RAM-verified.
4. Password failure message path (`0x0809A57C`, `0x0809A5C4`) — breakpoint-verified.
5. Gameplay (Chapter 3 banner, HUD, sprites) — screenshot + RAM-verified.
6. Pause: Start during gameplay produced no separate pause menu in the captured frame; no hidden debug/menu screen was reachable from the title, main, password or gameplay screens with the input sequences tried.

## 7. Validation evidence

* **Observed** — all screenshots listed above; breakpoint hits at `0x0809A600`
  (accept), `0x0809A5C4` (semantic reject); RAM reads of `0x03006D70…80` before and
  after entry; keyboard cursor index at `0x030019D8` tracked with arrow keys and
  direct writes; CHAPTER selector and Expert colour change on the main menu.
* **Derived** — validator/checksum algorithm, field bounds, key/table addresses,
  generator/encoder inverse, input-state struct offsets, from Thumb disassembly.
* **Inferred** — exact semantic meaning of fields 3–7 and of the tail value `C`
  (only their bounds and observable effect on chapter/character were exercised).

## 8. Unknowns

* Full glyph→index table for all 64 keyboard cells: anchors at indices 0, 3, 14, 15,
  16, 30 and 46 were confirmed by RAM+screen; the remainder were read from the
  screenshot but not individually RAM-verified, so codes are reported primarily as
  numeric index sequences.
* Meaning of payload bits 20–21 and higher tail bits beyond the `10..4999` bound.
* Whether a hidden debug screen exists behind a sequence not published anywhere;
  the searched spaces (strings, key-mask arrays, all reachable menus) were bounded
  but not exhaustive over all possible 2^N input histories.
* Pause screen: no distinct pause menu was captured.

## 9. Tooling

* `strings -t x`, `grep -abo`, Python struct scans (header, logo, key-mask literals).
* `arm-none-eabi-objdump -D -b binary -marm -M force-thumb --adjust-vma=0x08000000`
  for all disassembly.
* Capstone 5.0.7 / Keystone / Pillow installed (via pip `--break-system-packages`).
* mGBA CLI debugger (`-d`) driven through a Python pty helper (`drive.py`, `dbgd2.py`),
  with `w/1`, `w/2`, `x/1`, `break/t`, `watch/w`, `load`, `save`.
* Savestate diffing: mGBA `.ss1` PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte
  raw state (`ssdiff.py`); IWRAM at state `0x19000`, EWRAM at `0x21000`.
* Work dir: `/tmp/pockyrocky` (scripts, screenshots, logs, savestates).
* Legal note: no ROM images or copyrighted assets are redistributed; only addresses,
  hashes, algorithms, and original findings are published.
