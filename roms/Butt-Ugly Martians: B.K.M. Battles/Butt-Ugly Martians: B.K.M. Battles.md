# Butt-Ugly Martians: B.K.M. Battles (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-11-09.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Butt-Ugly Martians: B.K.M. Battles/Butt-Ugly Martians: B.K.M. Battles.gba` |
| Size | 4 MiB (`0x400000`) |
| Header title | `BKM BATTLES` |
| Game code | `ABWE` |
| Maker code | `7D` |
| Software version | `0x00` |
| Complement check | `0xAE` (matches computed `0xAE`) |
| Header checksum | `0x0000` (computed `0x3ED7`; the usual rebuilt-header artifact) |
| Entry word | `EA00002E` → stock ARM branch to `0x080000C0` |
| MD5 | `37b681295390ef9f55ee3222c761c4c3` |
| SHA-1 | `24962220f242b49231969f6d313e325148886106` |
| SHA-256 | `264fdc8b3f1dd6770694f3e0f39a05ea2ac05b48a9695cb8051e2005189be51f` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at
file offset `0x4` (header base `0x0`). The file is a single 4 MiB image, not a
multi-game pack. The entry word is the stock branch, the complement check is
correct, and the first 4 KiB contain no cracktro/trainer strings. **No patch or
trainer was found.** The only header anomaly is the zero header checksum, which
is normal for a rebuilt header.

ROM addresses below are `0x08000000 + file_offset`. All findings are tied to
this exact hash; another revision may differ.

---

## 2. Executive summary

The game has **two independent code surfaces**, both on the same
`ENTER PASSWORD` screen reached from `MAIN MENU → RESUME GAME`:

1. **An 18-entry table of fixed 8-character cheat strings** at file
   `0x3A7B5C` (12-byte stride), indexed by a pointer table at `0x3CFF88` and
   tested by the function at `0x0802586C`. Fourteen of the eighteen are
   published (GameFAQs lists eight upgrades and six level-select codes); **four
   are in no published list**: `LMBOTFLP`, `IIFHABLH`, `WPTBITWN`, `AALAALAL`.
   Each entry's effect is a byte write to `0x03002098/0x03002099/0x0300209A`;
   all 18 were entered in the emulator and their writes read back with the GDB
   stub (table in §6).

2. **A general 15-symbol level password** over a 32-symbol alphabet
   `*BCDFGHJKLMNPQRSTVWXYZ0123456789`, five bits per symbol, with a 7-bit
   checksum, an 8-byte XOR key `SNIPPY02`, and an encoder/decoder pair. The
   password encodes the current world and a second 2-bit (4-value) axis plus
   thirteen 3-bit progress fields and two 2-bit fields. The game itself contains
   the generator (`0x080251AC`), so arbitrary valid codes can be minted. I
   reimplemented the whole format in Python and generated codes that the ROM
   accepts; three were entered in the emulator and their effects observed
   (level 0 tutorial, level 3 Aquatica, level 7 Koo Foo Ship).

**Published-code verification:** all 14 published literals are present in the
ROM. One GameFAQs literal is a typo (`IIALTSMO4`, nine characters; the ROM has
`IALTSMO4`). The VGChartz "Passwords" (17 characters, e.g.
`nbb3j r2wr2b pz*mk2`) cannot be entered: the screen caps input at 15 symbols
and those strings are absent from the ROM. The VGChartz label
"Four Defense Upgrades = IWTSOWN7" is wrong; `IWTSOWN7` is the Koo Foo Ship
level code.

**Important negative result:** the six published 8-character *level-select*
codes are accepted and write the correct level index to `0x03002098` bits 0–2,
but that byte is **never read** during the new-game/level-load path (verified
with a hardware read watchpoint). On this build they do not actually take the
player to the named level; the working route to a level is the 15-symbol
password, whose level numbering matches the published level names exactly
(level 3 = Aquatica, level 7 = Koo Foo Ship, both observed).

---

## 3. How to reproduce

### Emulator

```bash
sudo apt-get install -y mgba-sdl xvfb openbox xdotool scrot imagemagick gdb-multiarch
Xvfb :218 -screen 0 1280x960x24 &
DISPLAY=:218 openbox &
DISPLAY=:218 SDL_AUDIODRIVER=dummy mgba -3 "Butt-Ugly Martians: B.K.M. Battles.gba" &
```

Default mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows. Hold direction keys 120 ms with ~250 ms
between presses; shorter taps are dropped by the password grid.

### Reaching the password screen

1. Title → `PRESS START` (Start).
2. Main menu: `NEW GAME`, `RESUME GAME`, `OPTIONS`, `HIGH SCORES`.
3. `RESUME GAME` → `ENTER PASSWORD`.

The password grid is 8 columns × 5 rows: `0-9`, `A-Z`, `*`, `←` (backspace),
`×` (clear). The bottom-right cell is `OK`. The buffer holds **15 symbols**;
the input handler stops accepting at length 15 (`cmp r1,#14` at
`0x08014F4E`), confirmed by typing 18 symbols and observing 15 stored.

The validator is reached through the wrapper at `0x0801788C`:
`r0 = 0x03002D90; bl 0x080253F4`.

### Reaching the level-complete password display

The pause menu contains `PASSWORD` as a caption (string `0x2AEEBC`); the
level-complete screen uses `CURRENT PASSWORD` (`0x2B02E4`) and is produced by
the generator at `0x080251AC`. The complete level was not played; the
generator format was instead proven by generating codes and having the game
accept them.

### Menus walked

| Screen | Path | Notes |
|---|---|---|
| Title | boot | `PRESS START` |
| Main | Start | 4 entries only |
| New Game | Main → NEW GAME | → DIFFICULTY |
| Difficulty | New Game | `EASY` / `MEDIUM` / `HARD` |
| Character select | Difficulty → A | 4 portraits, first selected |
| Resume / password | Main → RESUME GAME | the target screen |
| Options | Main → OPTIONS | BRIGHTNESS, SFX VOLUME, MUSIC VOLUME, CREDITS, ACCEPT, CANCEL |
| High Scores | Main → HIGH SCORES | 5 default entries `AAA`–`EEE` |
| Credits | Options → CREDITS | Runecraft staff |
| Pause | Start in game | OPTIONS, SELECT PLAYER, HELP, CONTINUE, QUIT GAME, `PASSWORD` |
| Select Player | Pause → SELECT PLAYER | GBA control diagram |
| How To Play / Map | Pause → HELP | two pages |
| Quit confirm | Pause → QUIT GAME | `ARE YOU SURE ?` NO / YES |

Evidence screenshots are committed next to the ROM as
`Butt-Ugly Martians - *.png` (see §9).

---

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x083A7B5C` | data | 18-entry cheat string table, 8 chars + 4 NUL, 12-byte stride |
| `0x083CFF88` | data | 18-entry pointer table to the strings above |
| `0x083CFF68` | data | 32-symbol level-password alphabet `*BCDFGHJKLMNPQRSTVWXYZ0123456789` |
| `0x083A7C8C` | data | XOR key `SNIPPY02` (8 bytes) |
| `0x083A7C31` | data | table C: `C[level*4+char]` → F1; `0xFF` = invalid combo |
| `0x083A7C51` | data | table A: F1 → char axis (0–3) |
| `0x083A7C6D` | data | table B: F1 → world axis (0–7) |
| `0x0802586C` | code | 8-char cheat-table matcher; returns 1 on match |
| `0x080258B0` | data | 18-entry handler-address table |
| `0x080253F4` | code | password validator (returns 0 reject, 1 level password, 2 cheat) |
| `0x08025730` | code | 15 symbols → 12-byte packed state |
| `0x08025838` | code | checksum: signed sum of state bytes 0–7 + (byte 8 & 0xE0), & 0x7F |
| `0x080255A8` / `0x080255FC` | code | XOR state bytes 0–7 with `SNIPPY02` |
| `0x08025650` | code | packed state → 15 symbols |
| `0x080251AC` | code | state builder + encoder (generator); writes 15-char string |
| `0x0801788C` | code | validator wrapper (`r0 = 0x03002D90`) |
| `0x08014FA0` | code | password-screen input/return handling; calls `0x0801788C` |
| `0x03002D90` | RAM | password input buffer (15 bytes + NUL) |
| `0x03003098` | RAM | 12-byte packed state (encoder/decoder scratch) |
| `0x03002098` | RAM | cheat byte 0: bits 0–2 level index; bits 3–4 unknown; bits 5–7 extra-lives code |
| `0x03002099` | RAM | cheat byte 1: bits 0–2 weapon level; bits 3–5 defense level; bit 6 max; bit 7 unlimited lives |
| `0x0300209A` | RAM | cheat byte 2: bit 0 level-select flag; bit 1 second flag |
| `0x0201F95C` | RAM | runtime copy of the 32-symbol alphabet |
| `0x0201F97C` | RAM | runtime copy of the cheat-string pointer table |
| `0x02000006` | RAM | starting-lives value written by the new-game init |
| `0x08015AC4` | code | new-game init: reads `0x03002099` bit 7 (unlimited lives) |
| `0x08015B08` | code | new-game init: reads `0x03002098` bits 5–7 (extra lives) |

---

## 5. Algorithm

### 5.1 15-symbol level password

Alphabet (32 symbols, 5 bits each), indexed 0–31:

```
*BCDFGHJKLMNPQRSTVWXYZ0123456789
```

The screen offers `0-9 A-Z *`; the conversion table is the string above, and a
character not present in it (all five vowels, for example) returns index **31**
(`0x08025704`), i.e. it aliases to `9`.

Decode (`0x08025730`, then the validator):

```
idx[i] = alphabet_index(symbols[i])          # 15 symbols, missing -> 31
w0 = ((((((idx0<<5|idx1)<<5|idx2)<<5|idx3)<<5|idx4)<<5|idx5)<<2) | (idx6>>3)
w1 = ((((((idx6<<5|idx7)<<5|idx8)<<5|idx9)<<5|idx10)<<5|idx11)<<4) | (idx12>>1)
w2 = (((idx12<<5|idx13)<<5|idx14)<<21)

u = LE32(w0, w1, w2)                          # 12 bytes, u[8]=u[9]=0,
                                              # u[10] <= 7
chk = ( sum_signed(u[0..7]) + (u[8] & 0xE0) ) & 0x7F
p = u;  p[0..7] ^= "SNIPPY02"
if (p[11] >> 1) != chk: reject
```

`p` is the decoded ("plain") 12-byte game state. The validator then extracts
the fields below from `p` and rejects any 3-bit field > 6 or 2-bit field > 2.

| Field | Bits of `p` | Width | Range checked |
|---|---|---|---|
| F1 | `p[2]` bits 2–6 | 5 | must be a valid (world,axis) index |
| v1 | `p[5]` bit 7 + `p[6]` bits 0–1 | 3 | ≤ 6 |
| v2 | `p[6]` bits 2–4 | 3 | ≤ 6 |
| v3 | `p[6]` bits 5–7 | 3 | ≤ 6 |
| v4 | `p[4]` bits 6–7 + `p[5]` bit 0 | 3 | ≤ 6 |
| v5 | `p[5]` bits 1–3 | 3 | ≤ 6 |
| v6 | `p[5]` bits 4–6 | 3 | ≤ 6 |
| v7 | `p[3]` bits 5–7 | 3 | ≤ 6 |
| v8 | `p[4]` bits 0–2 | 3 | ≤ 6 |
| v9 | `p[4]` bits 3–5 | 3 | ≤ 6 |
| v10 | `p[0]` bits 0–2 | 3 | ≤ 6 |
| v11 | `p[2]` bit 7 + `p[3]` bits 0–1 | 3 | ≤ 6 |
| v12 | `p[3]` bits 2–4 | 3 | ≤ 6 |
| v13 | `p[7]` bits 5–7 | 3 | stored, not range-checked |
| f2 | `p[7]` bits 0–4 | 5 | not range-checked |
| d1 | `p[10]` bit 7 + `p[11]` bit 0 | 2 | ≤ 2 |
| d2 | `p[10]` bits 5–6 | 2 | ≤ 2 |
| checksum | `p[11]` bits 1–7 | 7 | must equal computed chk |
| ignored | `p[0]` bits 3–7, `p[1]`, `p[2]` bits 0–1 | 15 | never read |
| forced 0 | `p[8]`, `p[9]`, `p[10]` bits 0–4 | — | not encoded |

`F1` selects the world and a second 2-bit axis through tables C/A/B:

```
F1 = C[B[F1]*4 + A[F1]]        # C[3]=C[5]=C[6]=C[7]=0xFF -> unreachable
```

Inverting it: the encoder computes `F1 = C[level*4 + char]`. Valid `F1` is
0–27; `F1` 28–31 fail the consistency check.

Encoder (inverse, verified round-trip on 5000 random states):

```
plain p (p[8]=p[9]=0, p[10]<8)
u = p; u[0..7] ^= "SNIPPY02"
chk = (sum_signed(u[0..7]) + (u[8]&0xE0)) & 0x7F
u[11] = (u[11] & 1) | (chk<<1)
idx[0..5] = five-bit groups of (w0>>2)
idx[6]    = ((w0&3)<<3) | ((w1>>29)&7)
idx[7..11]= five-bit groups of (w1>>4)
idx[12]   = ((w1&0xF)<<1) | (w2>>31)
idx[13]   = (w2>>26)&31
idx[14]   = (w2>>21)&31
```

(The 8-char cheat strings are checked by the table matcher *before* this
decoder, so their vowels never hit the alias rule.)

### 5.2 Cheat table

`0x0802586C` compares the input byte-by-byte against each of 18 NUL-padded
8-char strings. A full 8-character match returns index `i` to the dispatch
table at `0x080258B0`, whose handler sets the corresponding bits in
`0x03002098/0x03002099/0x0300209A` and returns 1; the wrapper then returns
**2** to the screen, which clears the field and stays on the password screen.
A 15-symbol password that is not an 8-char cheat falls through to §5.1 and
returns **1**, which immediately starts the game (screen state 9).

Cheat effect bits (measured in the emulator; semantics from the new-game
initialiser at `0x08015A9E`–`0x08015B10`):

| Code | `0x03002098` | `0x03002099` | `0x0300209A` | Effect |
|---|---|---|---|---|
| `JT2DU4MP` | `0x00` | `0x10` | `0x00` | defense upgrades = 2 (bits 3–5) |
| `DUATOU4M` | `0x00` | `0x20` | `0x00` | defense upgrades = 4 |
| `GMACOEWU` | `0x00` | `0x02` | `0x00` | weapon upgrades = 2 (bits 0–2) |
| `IAGAW4WU` | `0x00` | `0x04` | `0x00` | weapon upgrades = 4 |
| `2ELFMPLS` | `0x40` | `0x00` | `0x00` | extra lives = 2 (bits 5–7) |
| `IAGAW4EL` | `0x80` | `0x00` | `0x00` | extra lives = 4 |
| `ALWMAA15` | `0x00` | `0x40` | `0x00` | max firepower / pickups (bit 6) |
| `KMIORMAO` | `0x00` | `0x80` | `0x00` | unlimited lives (bit 7; init forces 7) |
| `IWTSOWN2` | `0x02` | `0x00` | `0x01` | level 2 Mechtropolis |
| `TMTWN3PD` | `0x03` | `0x00` | `0x01` | level 3 Aquatica |
| `IALTSMO4` | `0x04` | `0x00` | `0x01` | level 4 Arborea |
| `IOTJOWN5` | `0x05` | `0x00` | `0x01` | level 5 Silicon City |
| `FILGSOW6` | `0x06` | `0x00` | `0x01` | level 6 Magma |
| `IWTSOWN7` | `0x07` | `0x00` | `0x01` | level 7 Koo Foo Ship |
| `LMBOTFLP` | `0x00` | `0x00` | `0x02` | unknown field = 0 (unpublished) |
| `IIFHABLH` | `0x08` | `0x00` | `0x02` | unknown field = 1 (unpublished) |
| `WPTBITWN` | `0x10` | `0x00` | `0x02` | unknown field = 2 (unpublished) |
| `AALAALAL` | `0x18` | `0x00` | `0x02` | unknown field = 3 (unpublished) |

Starting lives are computed as `(0x03002098 >> 5) + 1`; if `0x03002099` bit 7
is set, the value is forced to 7 (`0x08015AC4`). Weapon/defense fields are read
by gameplay code, not by the new-game initialiser.

`0x03002098` bits 0–2 (level) and `0x0300209A` bit 0 are written by the level
codes, but a read watchpoint over the whole boot → NEW GAME → difficulty →
character → level-load sequence recorded **no reader**. `0x03002098` bits 3–4
and `0x0300209A` bit 1 (the four unpublished codes) were likewise never read.
They are accepted (return 2) but inert on this build.

---

## 6. Tables

### 6.1 Cheat strings in ROM order

`0x083A7B5C`, 12-byte stride (8 chars + four NULs):

```
IWTSOWN2  TMTWN3PD  IALTSMO4  IOTJOWN5  FILGSOW6  IWTSOWN7
2ELFMPLS  IAGAW4EL  GMACOEWU  IAGAW4WU  JT2DU4MP  DUATOU4M
ALWMAA15  KMIORMAO  LMBOTFLP  IIFHABLH  WPTBITWN  AALAALAL
```

Published (archived GameFAQs, 2018-11-26) and verified present: the first 14
above except that GameFAQs prints `IIALTSMO4` for Arborea. The ROM literal is
`IALTSMO4` (8 chars); the published 9-char form is a typo and was corrected
in the table above. The four last entries are **not published anywhere**.

### 6.2 Valid F1 ↔ (world, axis) ↔ 15-symbol code

All 28 valid combinations, with all other fields zero. Every one of these is
absent from every published list.

| world | axis | F1 | code | published level name |
|--:|--:|--:|---|---|
| 0 | 0 | 0 | `MBFY6Y3WHBPZBCT` | tutorial / intro |
| 0 | 1 | 1 | `MBHY6Y3WHBPZBFT` | — |
| 0 | 2 | 2 | `MB*Y6Y3WHBPZ*8T` | — |
| 1 | 0 | 3 | `MBCY6Y3WHBPZB*T` | — (solo level) |
| 2 | 0 | 4 | `MBPY6Y3WHBPZBMT` | Mechtropolis |
| 2 | 1 | 5 | `MBRY6Y3WHBPZBPT` | Mechtropolis |
| 2 | 2 | 6 | `MBKY6Y3WHBPZBHT` | Mechtropolis |
| 2 | 3 | 7 | `MBMY6Y3WHBPZBKT` | Mechtropolis |
| 3 | 0 | 8 | `MBYY6Y3WHBPZBWT` | Aquatica |
| 3 | 1 | 9 | `MB0Y6Y3WHBPZBYT` | Aquatica |
| 3 | 2 | 10 | `MBTY6Y3WHBPZBRT` | Aquatica |
| 3 | 3 | 11 | `MBWY6Y3WHBPZBTT` | Aquatica |
| 4 | 0 | 12 | `MB6Y6Y3WHBPZB4T` | Arborea |
| 4 | 1 | 13 | `MB8Y6Y3WHBPZB6T` | Arborea |
| 4 | 2 | 14 | `MB2Y6Y3WHBPZB0T` | Arborea |
| 4 | 3 | 15 | `MB4Y6Y3WHBPZB2T` | Arborea |
| 5 | 0 | 16 | `M*FY6Y3WHBPZ*CT` | Silicon City |
| 5 | 1 | 17 | `M*HY6Y3WHBPZ*FT` | Silicon City |
| 5 | 2 | 18 | `M**Y6Y3WHBPZB8T` | Silicon City |
| 5 | 3 | 19 | `M*CY6Y3WHBPZ**T` | Silicon City |
| 6 | 0 | 20 | `M*PY6Y3WHBPZ*MT` | Magma |
| 6 | 1 | 21 | `M*RY6Y3WHBPZ*PT` | Magma |
| 6 | 2 | 22 | `M*KY6Y3WHBPZ*HT` | Magma |
| 6 | 3 | 23 | `M*MY6Y3WHBPZ*KT` | Magma |
| 7 | 0 | 24 | `M*YY6Y3WHBPZ*WT` | Koo Foo Ship |
| 7 | 1 | 25 | `M*0Y6Y3WHBPZ*YT` | Koo Foo Ship |
| 7 | 2 | 26 | `M*TY6Y3WHBPZ*RT` | Koo Foo Ship |
| 7 | 3 | 27 | `M*WY6Y3WHBPZ*TT` | Koo Foo Ship |

`world` and `axis` are the table B/A values. The level names are the published
6 level-select labels, and their indices match the ROM's own numbering
(verified: world 3 = Aquatica story, world 7 = Koo Foo Ship interior).

### 6.3 Tables C/A/B (raw)

```
C (0x083A7C31, 32 bytes incl. overlap):
 0,1,2,255,3,255,255,255,4,5,6,7,8,9,10,11,
 12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27
A (0x083A7C51, 28): 0,1,2,0, 0,1,2,3, 0,1,2,3, 0,1,2,3, 0,1,2,3, 0,1,2,3, 0,1,2,3
B (0x083A7C6D, 28): 0,0,0,1, 2,2,2,2, 3,3,3,3, 4,4,4,4, 5,5,5,5, 6,6,6,6, 7,7,7,7
```

`C[3]`, `C[5]`, `C[6]`, `C[7]` are `0xFF`, which is why world 0/axis 3 and
world 1/axis 1–3 have no reachable password.

---

## 6b. Enumeration

### Space size

* Raw alphabet/length: 32 symbols × 15 positions = `32^15` =
  `37,778,931,862,957,161,709,568` (2^75 ≈ 3.78 × 10^22).
* Checksum: 7 bits, stored in state byte 11 bits 1–7. Exactly 1 string in 128
  passes the checksum: `2^68` =
  `295,147,905,179,352,825,856` (≈ 2.95 × 10^20).
* Free payload before semantic checks: 68 bits (state bytes 0–7, byte 10
  bits 5–7, byte 11 bit 0). Fifteen of those bits are never read by the
  validator (`p[0]` bits 3–7, `p[1]`, `p[2]` bits 0–1), so each semantic state
  has `2^15 = 32,768` distinct valid spellings (aliases).
* Semantic fields: F1 (28 valid values) × thirteen 3-bit fields (7 values
  each) × f2 (32 values) × two 2-bit fields (3 values each) =
  `781,312,979,922,048` (≈ 7.81 × 10^14) distinct accepted states.
* Accepted strings: `781,312,979,922,048 × 32,768` =
  `25,602,063,726,085,668,864` (≈ 2.56 × 10^19), about 0.068 % of the raw
  space. The rest fail the 7-bit checksum, the `≤ 6` / `≤ 2` range checks, or
  the F1 consistency check.

### Novel codes generated and confirmed in-game

All codes below are absent from GameFAQs, VGChartz, TCRF and the fan wikis.

| Code | Decoded | Emulator result |
|---|---|---|
| `MBFY6Y3WHBPZBCT` | world 0, axis 0, all fields 0 | **accepted**; intro dialogue and tutorial level start |
| `MBYY6Y3WHBPZBWT` | world 3 (Aquatica), axis 0 | **accepted**; story line "Our old enemy Jax is gathering forces on Aquatica – the water world." |
| `M*YY6Y3WHBPZ*WT` | world 7 (Koo Foo Ship), axis 0 | **accepted**; story "Great work, Martians! Only one bad guy left!" and Koo Foo Ship interior |
| `M*WY6Y3WHBPZ*TT` | world 7, axis 3 | **accepted**; world 7 gameplay |

The first three were captured as screenshots
(`Butt-Ugly Martians - novel level 7 code accepted.png`,
`... - level 7 Koo Foo Ship.png`, `... - level 3 Aquatica story.png`).

### Bounds proven by rejection

| Input | Defect | Result |
|---|---|---|
| `*BFY6Y3WHBPZBCT` | wrong checksum (stored 69 vs computed 117) | **rejected**: field cleared, screen stays; no game start (`... - bad checksum rejected.png`) |
| `MBFY6Y3WHSPZBF*` | checksum valid but `v1 = 7` (> 6) | **rejected**: field cleared, screen stays; no game start (`... - out of range field rejected.png`) |
| 18-symbol entry | exceeds the 15-symbol cap | only the first 15 symbols are stored; extra presses ignored |
| 17-char VGChartz code | exceeds the cap and absent from ROM | cannot be entered; not a valid code for this SKU |

### Published-code check

* All 14 published literals (`JT2DU4MP`, `2ELFMPLS`, `GMACOEWU`, `DUATOU4M`,
  `IAGAW4EL`, `IAGAW4WU`, `ALWMAA15`, `KMIORMAO`, `IWTSOWN2`, `TMTWN3PD`,
  `IALTSMO4`, `IOTJOWN5`, `FILGSOW6`, `IWTSOWN7`) are present at
  `0x083A7B5C`–`0x083A7C33`.
* `IIALTSMO4` (GameFAQs) is **not** present; `IALTSMO4` is. This is a published
  typo.
* The two VGChartz user passwords (`nbb3j r2wr2b pz*mk2`,
  `nbd3j rswcb pz*c*pk`) contain 17 non-space characters, exceed the 15-symbol
  cap, and are absent from the ROM in ASCII, lowercase and every case variant
  checked. They are unverified/invalid for this ROM.
* VGChartz labels `IWTSOWN7` as "Four Defense Upgrades"; the ROM handler writes
  level index 7, not a defense value. The GameFAQs label (Koo Foo Ship) is the
  correct one.
* The six published level-select codes are accepted and write the correct
  index, but as noted in §2 the byte is not consumed on this build; the 15-symbol
  passwords are the working level selector.

---

## 7. Validation evidence

**Observed (emulator / memory):**

* All 18 cheat codes entered on the real `ENTER PASSWORD` screen; GDB breakpoint
  at `0x08014FA4` logged `r0 = 2` (cheat path) for every one and the RAM bytes
  in §5.2 were read back. The four unpublished codes were accepted the same way.
* `MBFY6Y3WHBPZBCT`, `MBYY6Y3WHBPZBWT`, `M*YY6Y3WHBPZ*WT` and
  `M*WY6Y3WHBPZ*TT` entered on the same screen; the first three started the
  game (`r0 = 1`) with distinct story/level outcomes.
* Bad-checksum and out-of-range codes stayed on the password screen and did not
  start a game.
* Read watchpoints on `0x03002098` and `0x0300209A` over the boot → NEW GAME →
  difficulty → character → level-load path recorded reads only at
  `0x08025976` (handler old-value read), `0x08025912` (handler OR), and
  `0x08015B0C` (lives init, value 0x07); no consumer of bits 0–2 or of
  `0x0300209A`.
* 18-symbol entry test: 15 symbols stored, extras ignored.
* Menus listed in §3 were walked and screenshotted.

**Derived (disassembly):**

* The 15-symbol packing, checksum, XOR key and field extraction in §5.1
  (validator `0x080253F4`; decoder `0x08025730`; checksum `0x08025838`;
  encoder `0x080251AC`, `0x08025650`).
* The 18-entry cheat matcher and handler table (`0x0802586C`, `0x080258B0`).
* The new-game lives computation (`0x08015AC4`, `0x08015B08`).
* The 15-symbol input cap (`0x08014F4E`, `cmp r1,#14`).

**Inferred:**

* The second F1 axis ("axis" 0–3) is most consistent with the four
  `CHOOSE CHARACTER` portraits, but the sprite difference between axis 0 and
  axis 3 codes was not conclusively isolated on screen. Table A/B/C and the
  consistency check are proven; the *name* of the axis is the inference.
* `0x03002098` bits 3–4 + `0x0300209A` bit 1 (the four unpublished codes) look
  like a planned character/difficulty selector of four values (0–3), but no
  consumer was found on this build, so their intended effect is unknown.

---

## 8. Unknowns

* Visual identity of the F1 second axis (character vs. player slot); the
  level axis is confirmed at worlds 0, 3 and 7.
* Intended effect of `LMBOTFLP`, `IIFHABLH`, `WPTBITWN`, `AALAALAL`; they are
  accepted but the written field is never read in the tested paths.
* The `PASSWORD` caption in the pause menu: it is not selectable with the
  D-pad/buttons tested and the current-password text was blank in the resumed
  game; the level-complete `CURRENT PASSWORD` screen was not reached by play.
* World 1 (only axis 0 reachable) has no published name.
* Whether the 8-char level-select codes work through a save file or another
  entry point not present in this build; no reader of the written field was
  found.
* The exact semantic meaning of the 13 3-bit progress fields (v1–v13) and f2;
  only their widths, ranges and state byte positions are proven.

---

## 9. Tooling

* mGBA 0.10.5 (`mgba-sdl`), Xvfb `:218`, openbox, `xdotool`, `scrot`,
  ImageMagick.
* `gdb-multiarch` via mGBA `-g` (GDB stub on `:2345`) for RAM reads and
  hardware read watchpoints. Note: mGBA `-g` pauses the emulator until the
  first client connects; key presses sent before that are lost.
* `arm-none-eabi-objdump -M force-thumb` and Capstone for disassembly.
* Python 3 model/encoder: `bkm_password.py` next to this report (reimplements
  decode, checksum, XOR, pack, field extraction, tables C/A/B; `decode`,
  `encode --level N --char N`, and `list` subcommands). It agrees with the ROM
  on accepted and rejected inputs and round-trips 5000 random states.
* Screenshots committed next to the ROM:
  `Butt-Ugly Martians - enter password screen.png`,
  `... - novel level 0 code accepted.png`,
  `... - novel level 7 code accepted.png`,
  `... - level 7 Koo Foo Ship.png`,
  `... - level 3 Aquatica story.png`,
  `... - bad checksum rejected.png`,
  `... - out of range field rejected.png`,
  `... - pause menu.png`, `... - main menu.png`,
  `... - character select.png`, `... - high scores.png`,
  `... - credits.png`, `... - options.png`.

### Legal note

No ROM, extracted graphics, music or game text is redistributed here. The
report contains addresses, algorithms and short code strings necessary to
document the format.
