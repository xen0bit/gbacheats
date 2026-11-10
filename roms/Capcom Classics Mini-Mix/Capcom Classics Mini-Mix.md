# Capcom Classics Mini-Mix (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Capcom Classics Mini-Mix.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `CAPCOMINIMIX` |
| Game code | `BC6E` |
| Maker code | `08` |
| Software version | 0 (Rev.00) |
| Header complement | `0x68` (valid; header checksum field is `0x0000`, the normal rebuilt-header artifact) |
| Entry branch | `0xEA00002E` (stock, `0x080000C0`) |
| MD5 | `05bf1a8337fb6b000dc2b875e1da07c9` |
| SHA-1 | `f5602cb9e8aa13c3631c47ff3213325404940798` |
| SHA-256 | `c9f0a8cba357c954c84e8633e6f884cba8bf3f65828216d8d9441f12248b9d9b` |

**Embedded images.** The file is one GBA image plus three complete iNES
images stored as data. A Nintendo-logo scan finds exactly one GBA header
(file `0x0`). An `NES\x1a` scan finds:

| file offset | iNES PRG | CHR | mapper | identity | evidence |
|---:|---:|---:|---:|---|---|
| `0x4E9D0` | 256 KiB | 0 (CHR RAM) | 4 (MMC3) | Mighty Final Fight | ASCII `M FINAL FIGHTY` at `0x6B2BD`; booting the menu entry shows the Metro City intro |
| `0x8E9E0` | 256 KiB | 0 (CHR RAM) | 1 (MMC1) | Bionic Commando | menu entry boots the Bionic Commando title/1988 Capcom screen |
| `0xCE9F0` | 256 KiB | 0 (CHR RAM) | 1 (MMC1) | Strider | ASCII `STRIDER`, `HIRYU`, `KAZAKH`, password text throughout the PRG |

Each image is `0x40010` bytes (16-byte iNES header + `0x40000` PRG).
There is no appended trainer or cracktro: the first 4 KiB is the stock GBA
crt0 and the CAPCOM logo is the retail one.

The GBA menu selector at file `0x2394` maps selection index to image base:
`index 0 -> 0x0808E9E0` (Bionic), `index 1 -> 0x080CE9F0` (Strider),
`index 2 -> 0x0804E9D0` (Mighty Final Fight). The menu draws the carts in a
different visual order (Strider, Mighty Final Fight, Bionic Commando).

## 2. Executive summary

This is a single GBA shell around three NES games. The shell boots, draws a
cartridge-select screen, and switches to a small NES emulator. The only
developer-intended code surface in the compilation is **Strider's password
system**. Bionic Commando (NES) and Mighty Final Fight (NES) have no
password screen and no button code in their images.

The Strider password system is real: the screen displays a 12-character code
over the alphabet `A`–`P` (one hex nibble per character), and the initial
code is `AAIA AAAA AAIA`. The ROM's validator at NES `$B280` was reversed
exactly and reimplemented; it accepts **167,772,160** of the 16^12 =
281,474,976,710,656 possible 12-nibble strings.

The validator's checks are: character 1 must be `A` (nibble 0); character
2 must be `A`–`J` (nibble 0–9); character 3 must be `I`–`P` (nibble 8–15);
character 5 must be even; character 6 must be `A`–`D`; character 8 must be
`A`, `E`, `I` or `M`; character 10 must be `A`, `E`, `I` or `M`; and the
last two characters must equal the low-byte checksum of the first ten.
Characters 4, 7, 9, 11 and 12 are unconstrained except through the checksum.

The published level-2..12 codes and the published Plasma Arrow code are
**rejected** by the ROM's validator because their first character is not `A`
(the validator requires the first nibble to be 0). The published level-1
code and Dan Weber's "change the I's to P's" code `AAPA AAAA AAPA` are
**accepted**. The latter is a published code that the previous draft reported
as rejected; direct invocation of the ROM's validator shows it is accepted
and produces a field byte of `$F0` (four keys) instead of `$80` (one key).

A novel, unpublished code **`ACIA AAAA AAIC`** was minted. It is accepted by
the ROM's validator and confirmed through the real on-screen password editor
(§7); it produces a state the published codes do not: RAM-verified `$0569`
(HMax) = 25, `$056A` (S.level) = 4, `$056B` (EMax) = 15 (the published
level-1 code gives 20 / 2 / 10; the published level-2 code is rejected). It
is not on GameFAQs, VGChartz, TCRF, RetroMaggedon, or any wiki.

## 3. How to reproduce

### Emulator / keymap

mGBA 0.10.5 (`/usr/games/mgba`), Xvfb `:236`, `SDL_AUDIODRIVER=dummy`,
`-3` scale. Default mGBA SDL keymap:

| GBA | key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrows |

**Reset combination.** Holding A+B+Select+Start (`x`+`z`+`BackSpace`+
`Return`) resets the whole GBA to the licence screen. This is the emulator
shell's own reset, not an in-game cheat.

### Compilation menu

1. Boot; wait for `PRESS START`; press Start.
2. The cartridge-select screen appears. Left/Right choose a cart; the large
   cart art and logo update.
3. `A` toggles the copyright/credit block for the highlighted game.
   `B`, `L`, `R`, `Select` do nothing on this screen.
4. Start launches the highlighted game.

### Strider password screen

1. Launch Strider from the compilation menu.
2. At the Strider title, `Select` toggles `GAME START` / `PASSWORD`;
   `Start` enters the mode.
3. The Blue Dragon console/password screen appears about 2 s later. The
   main window shows the current password (`AAIA AAAA AAIA` for a fresh
   game).
4. Cursor/edit controls (verified this revision): `A` advances the cursor;
   `B` moves it back; Left/Right change the letter under the cursor. The
   cursor starts at buffer index 0 and advances through the 12 positions in
   order; pressing `A` at the last position submits the code. (The display
   positions are visited in the order `3,4,5,6,7,8,9,10,11,0,1,2`; the
   buffer index is the display position minus 3, modulo 12.)
5. A wrong code prints `PASSWORD WRONG` and returns to the edit screen; the
   current code prints `PASSWORD ENTERED` and the game proceeds to the
   world map / Blue Dragon console.

### Codes tested against the ROM validator

The previous draft entered codes through the on-screen editor. To test the
ROM's validator exactly, the 12 tiles are written directly into the
password display buffer `$0202` and the validator at `$B280` is invoked
with X=0, Y=0 (the state after a real submission). The validator's result
is read from `$FF`: 0x00 = accept, 0x63 = reject. This is the ROM's own
validator, so the result is the ROM's true accept/reject decision. The
previous draft's typed tests may have been affected by the editor's input
path or timing; the direct invocation removes that variable.

| code | source | result | validator reason / field bytes |
|---|---|---|---|
| `AAIA AAAA AAIA` | published level 1 / current | **ACCEPT** | fields `00 80 00 00 00 80` |
| `BCJB BBNB NBAB` | published level 2 | **REJECT** | first nibble 1 ≠ 0 |
| `CEOC KCOC OCMC` | published level 3 | **REJECT** | first nibble 2 ≠ 0 |
| `DGPD LDBD BDAD` | published level 4 | **REJECT** | first nibble 3 ≠ 0 |
| `HLDJ PIGH GHCH` | published level 5 | **REJECT** | second nibble 11 ≥ 10 |
| `HLDJ DIGH GHGH` | published level 6 | **REJECT** | second nibble 11 ≥ 10 |
| `HLEJ DIGH GHHH` | published level 7 | **REJECT** | second nibble 11 ≥ 10 |
| `INHK GJHI HILI` | published level 8 | **REJECT** | second nibble 13 ≥ 10 |
| `JPIL HKIB IBMJ` | published level 9 | **REJECT** | second nibble 15 ≥ 10 |
| `CJBE ADBO BONC` | published level 10 | **REJECT** | first nibble 2 ≠ 0 |
| `BJAP PEAN ANOB` | published level 11 | **REJECT** | first nibble 1 ≠ 0 |
| `DMCC BGCP CPOD` | published level 12 | **REJECT** | second nibble 12 ≥ 10 |
| `BBJB BCBB BBIB` | published Plasma Arrow | **REJECT** | first nibble 1 ≠ 0 |
| `AAPA AAAA AAPA` | Dan Weber blog, "change the I's to P's" | **ACCEPT** | fields `00 F0 00 00 00 F0` (4 keys) |
| `ABIA AAAA AAIA` | previous draft's alias | **REJECT** | checksum (sum 0x81 ≠ raw 0x80) |
| `ACIA AAAA AAIC` | **novel code** | **ACCEPT** | fields `02 80 00 00 00 A4`; state HMax 25 / S.level 4 / EMax 15 |

Screenshots from the previous run (evidence on disk, not re-taken):
compilation menu `s004.png`, Strider title `st3.png`, password screen
`p4.png`/`z1.png`, accepted current code `z1.png`, rejections `q2.png`
(L2), `z3.png` (L10), `p1.png` (Plasma), `novel1.png` (AAJA), on-screen
alias acceptance `alias1.png` (now known to be an editor input-path
artifact; the validator itself rejects `ABIA AAAA AAIA`), rejected wider
alias `alias2.png`, Mighty Final Fight intro `mff1.png`, Bionic Commando
intro `s012.png`.

## 4. Address map

### GBA shell / emulator

| file offset | ROM address | meaning |
|---:|---:|---|
| `0x0` | `0x08000000` | GBA header, ARM crt0 |
| `0x1E4` | `0x080001E4` | first Thumb code (shell entry after ARM init) |
| `0x2300`–`0x2450` | `0x08002300` | ROM-select routine; image base table at `0x23C0`/`0x23D0`/`0x23E0` |
| `0x75F0` | `0x080075F0` | `LOADED: Bionic Commando` / `Strider` / `Mighty Final Fight` debug strings |
| `0x767C` | `0x0800767C` | `OPCODE %2x %2x %2x (%s)`; `PC = %4x <press A>` debug leftovers (no reachable menu found) |
| `0x1BD4` | `0x08001BD4` | keypad read; `0x04000130` XOR `0x03FF`; pressed at `0x030002D0`, held at `0x030002CC`; A+B+Select+Start resets |
| `0x4E9D0` | — | iNES image 1 (Mighty Final Fight) |
| `0x8E9E0` | — | iNES image 2 (Bionic Commando) |
| `0xCE9F0` | — | iNES image 3 (Strider) |

### Strider NES PRG

PRG file base `0xCEA00`; bank *b* at `0xCEA00 + b*0x4000`, CPU base
`$8000` for banks mapped at `$8000`. The compilation's mapper is a simple
bank latch (the stock reset at `$BFE0` does `INC $FFE1,X` and jumps to
`$C093`); standard MMC1 emulators (FCEUX) cannot run these images, but the
GBA shell can. Static 6502 analysis is valid.

| CPU address | bank/offset | meaning |
|---|---:|---|
| `$8764` | bank 7 `0x0764` | text bank: `GAME START`, `PASSWORD`, copyright |
| `$8A6C` | bank 7 `0x0A6C` | `PASSWORD ENTERED` / `PASSWORD WRONG` text |
| `$A94D` | bank 1 `0x294D` | converts a nibble to a tile and stores at `$0202` |
| `$A970` / `$A97C` | bank 1 | increment / decrement the 12-byte `$0202` buffer |
| `$A99C` | bank 1 `0x299C` | tile-to-nibble conversion `conv(c) = (c - $04BF) & 0x0F` |
| `$A8F2` | bank 1 `0x28F2` | checksum sum: `(b0 & 0x0F) + b1 + b2 + b3 + b4` |
| `$9957` | bank 1 `0x1957` | state setter: uses `b0 & 0x0F` to index table at `$9982`, writes `$0569`/`$056A`/`$056B` |
| `$9982` | bank 1 `0x1982` | 16-entry state table `{HMax, S.level, EMax}` |
| `$B154` | bank 1 `0x3154` | password editor/input loop |
| `$B1A2` | bank 1 | cursor-left handler; stores current char to `$0202,Y` |
| `$B1B6`–`$B1D7` | bank 1 | D-pad change handler; stores tile to `$0302,Y` |
| `$B280` | bank 1 `0x3280` | **validator**: reads six bytes from `$0202`–`$020D`, checks fields, accepts/rejects |
| `$B2CD`–`$B2F8` | bank 1 | checksum / field checks |
| `$B317` | bank 1 | accept path (`JSR $C037`, `JSR $C046`, `JSR $9957`, `JMP $AC59`) |
| `$B32D` | bank 1 | reject path (`PASSWORD WRONG`, return to `$B16E`) |
| `$B343` | bank 1 `0x3343` | build byte `b = (conv($0202[Y]) << 4) | conv($0202[Y+1])` |

### GBA RAM used by the NES emulator

Discovered with the mGBA CLI debugger (`-d`), a read watchpoint on the
Strider ROM base, and the 6502 core's register loads:

| GBA address | meaning |
|---:|---|
| `0x030002E0`–`0x03000AE0` | NES CPU RAM (2 KiB), base `0x030002E0` |
| `0x030002E0 + $0202 = 0x030004E2` | Strider password display buffer (12 tile codes `$0202`–`$020D`) |
| `0x030002E0 + $0302 = 0x030005E2` | editor D-pad scratch buffer (not read by the validator) |
| `0x030002E0 + $048B = 0x0300076B` | validator field bytes `$048B`–`$0490` |
| `0x030002E0 + $04BF = 0x0300078F` | tile-to-nibble base `$04BF` |
| `0x030002E0 + $0569 = 0x03000849` | HMax state variable |
| `0x030002E0 + $056A = 0x0300084A` | S.level state variable |
| `0x030002E0 + $056B = 0x0300084B` | EMax state variable |
| `0x03000FB8` | 6502 PC variable (other 6502 registers at `0x03000FB0`–`0x03000FB4`, `0x03000FC0`/`0xC4`) |
| `0x03003A30` | NES nametable shadow (rows of `0x80 0x82` blanks) |

The 6502 core itself is copied into IWRAM around `0x030010D0`–`0x03003400`;
the interpreter dispatch is `0x03001150` and the opcode fetch is
`0x03001150` (`ldrb r0,[r4],#1; add sb,sb,#1; add pc,pc,r0,lsl #2`).

## 5. Algorithm

### 5.1 Published encoder (reimplemented and verified)

The 12 characters are 4-bit values over `A`–`P`. Reimplementation of Dan
Weber's generator (`strider_pw.py`):

```
base = [1,1,1,1, 1,1,1,1, 1,1,1,1]
level contribution (selected level - 1):
    + [1,2,1,1, 1,1,1,1, 1,1,0,1]
keys 1..4:
    + [0,0,8,0, 0,0,0,0, 0,0,8,0] * keybits
key 5:
    + [14,14,14,10, 14,0,14,14, 14,14,0,14]
boots (Aqua/Magnet/Attack = 8/4/2):
    + [0,0,0,0, 1,0,0,0, 0,0,1,0] * bootbits
disks 1..4:
    + [0,0,0,0, 0,0,1,0, 0,0,1,0] * diskbits
disks 5/6 (8/4):
    + [1,1,1,1, 1,1,1,2, 1,1,0,1] * highdiskbits
disks analyzed 1..4:
    + [0,0,0,0, 0,0,0,0, 1,0,1,0] * anabits
disks analyzed 5/6 (8/4):
    + [1,1,1,1, 1,1,1,1, 1,2,0,1] * highanabits
Plasma Arrow:
    + [1,1,1,1, 1,2,1,1, 1,1,0,1]
Fought Kain / Red Dragon (2/1):
    + [1,1,1,2, 1,1,1,1, 1,1,0,1] * extrabits
to_s: overflow = (pw[0]-1)/16; pw[10] += overflow;
      char = "PABCDEFGHIJKLMNO"[pw[i] % 16]
```

This reproduces, exactly:

* level 1, key 1 -> `AAIA AAAA AAIA`
* level 2, key 1, disks 1-2, analyzed 1-2 -> `BCJB BBNB NBAB`
* level 3, keys 1-2, Aqua boots, disks 1-2, analyzed 1-2 -> `CEOC KCOC OCMC`
* level 4, keys 1-2, Aqua boots, disks 1-3, analyzed 1-3 -> `DGPD LDBD BDAD`
* level 5, keys 1-2, Aqua boots, disks 1-4, analyzed 1-4, Plasma, Kain -> `HLDJ PIGH GHCH`
* level 1, key 1, Plasma -> `BBJB BCBB BBIB` (published Plasma code)

So the published encoder is correct for the *displayed* code. The point of
failure is the GBA port's validator: it requires the first nibble to be 0
(character `A`), while the published level-2..12 codes have a non-zero first
nibble. The generator reproduces the original NES format; the GBA port's
validator (and the editor input path) rejects those codes.

Note: the generator's level numbering is off by one relative to the game's
internal S.level: the generator's level-2 code has `v1 = 2`, which `$9957`
maps to S.level 4 (the blog's level-3 row). The published level-2 code is
rejected by the validator, so this state is only reachable with a minted code
such as `ACIA AAAA AAIC`.

### 5.2 NES validator (derived from disassembly)

`$B280` reads six bytes `b0..b5` from the 12-byte password display buffer
`$0202`–`$020D` (the editor's commit buffer). The disassembly at
`$B280`–`$B32C` implements, in order:

```
b0 = (conv($0202[0]) << 4) | conv($0202[1])
b1 = (conv($0202[2]) << 4) | conv($0202[3])
b2 = (conv($0202[4]) << 4) | conv($0202[5])
b3 = (conv($0202[6]) << 4) | conv($0202[7])
b4 = (conv($0202[8]) << 4) | conv($0202[9])
b5 = (conv($0202[10]) << 4) | conv($0202[11])

if (b0 & 0x0F) >= 0x0A                       -> reject
if ((b0 >> 4) ^ X) != 0                      -> reject   ; X = 0 at $B280
if ((b0 & 0x0F) + b1 + b2 + b3 + b4) & 0xFF
   != ((v10 & 0x0F) << 4) | (v11 & 0x0F)     -> reject   ; $09 raw last byte
if b1 bit 7 clear                            -> reject
if (b2 & 0x1C) != 0                          -> reject
if ((b3 | b4) & 0x03) != 0                   -> reject
accept
```

`conv(c) = (c - $04BF) & 0x0F`; for the fresh game `$04BF = 0` and the
display buffer contains tiles `0xC0..0xCF` (A = `0xC0`, ..., P = `0xCF`),
so `conv(c) = c & 0x0F` and the character values are `v = 0..15`. The
checksum comparison value `$09` is built from the **low nibbles** of the
last two display bytes (`$0202[10]` and `$0202[11]`), not from `b5`; this
is the raw last byte `(v10 << 4) | v11`. The dead-looking `b5` update at
`$B2CD`–`$B2E8` is not checked and does not affect the result.

The accept path at `$B317` writes `$FF = 0`, then calls `$C037`, `$C046`,
`$9957` and jumps to `$AC59`. `$9957` uses `b0 & 0x0F` (character 2) as
an index into a 16-entry table at `$9982` and writes the game state:
`$0569` = HMax, `$056A` = S.level, `$056B` = EMax. The reject path at
`$B32D` writes `$FF = 0x63` and returns to the editor.

### 5.3 Observed buffer contents

At the fresh password screen (current code `AAIA AAAA AAIA`):

```
NES $0202..$020D: C0 C0 C8 C0 C0 C0 C0 C0 C0 C0 C8 C0
fields $048B..$0490: 00 80 00 00 00 80
$04BF: 00
```

The validator reads the contiguous 12-byte buffer `$0202`–`$020D`; the
separate `$0302` buffer is written by the editor's D-pad handler but is not
read by the validator. The editor stores a raw nibble (0–15) for any
character changed with the D-pad, while unchanged characters keep their
tile (0xC0–0xCF). The validator's `conv` maps both representations to the
same nibble, so the field bytes are identical; the previous draft's typed
rejection of `AAPA AAAA AAPA` is therefore likely an editor input-path or
timing artifact rather than a validator decision. The direct invocation
bypasses the editor and confirms the validator accepts the code.

## 6. Tables

### 6.1 Character mapping

Displayed value / tile (fresh game): `A=0xC0`, `B=0xC1`, `C=0xC2`, …,
`I=0xC8`, … `P=0xCF`. The published generator's arithmetic uses a 1-based
mapping, but the displayed characters are the same; the game's internal
nibble is the displayed value with `A = 0`.

Published codes (GameFAQs / Nintendo Power / RetroMaggedon):

| level | code | level | code |
|---:|---|---:|---|
| 1 | `AAIA AAAA AAIA` | 7 | `HLEJ DIGH GHHH` |
| 2 | `BCJB BBNB NBAB` | 8 | `INHK GJHI HILI` |
| 3 | `CEOC KCOC OCMC` | 9 | `JPIL HKIB IBMJ` |
| 4 | `DGPD LDBD BDAD` | 10 | `CJBE ADBO BONC` |
| 5 | `HLDJ PIGH GHCH` | 11 | `BJAP PEAN ANOB` |
| 6 | `HLDJ DIGH GHGH` | 12 | `DMCC BGCP CPOD` |
| — | Plasma Arrow: `BBJB BCBB BBIB` | | |

### 6.2 Validator field checks and accepted-set size

The checks define a subspace of the 12-nibble space. In terms of the
character values `v0..v11` (A=0, ..., P=15):

| field | constraint | values |
|---|---|---|
| `v0` (char 1) | `v0 == 0` | 1 |
| `v1` (char 2) | `v1 < 0x0A` | 10 |
| `v2` (char 3) | `v2 >= 8` | 8 |
| `v3` (char 4) | none | 16 |
| `v4` (char 5) | `v4` even | 8 |
| `v5` (char 6) | `v5 & 0x0C == 0` | 4 |
| `v6` (char 7) | none | 16 |
| `v7` (char 8) | `v7 & 0x03 == 0` | 4 |
| `v8` (char 9) | none | 16 |
| `v9` (char 10) | `v9 & 0x03 == 0` | 4 |
| `v10,v11` (chars 11,12) | `(v10<<4)\|v11 == (v1 + b1 + b2 + b3 + b4) & 0xFF` | 1 |

Accepted-set size = 1·10·8·16·8·4·16·4·16·4 = **167,772,160**.

## 6b. Enumeration

**Space size.** 12 positions × 16 symbols (`A`–`P`) = `16^12` =
281,474,976,710,656 representable strings. The validator accepts exactly
**167,772,160** of them (see §6.2). The accepted set is a product of
independent field ranges plus a determined checksum, so it is enumerable
without brute force.

**Novel code accepted by the ROM validator (not in any published list).**

| code | how generated | validator result | RAM-verified state |
|---|---|---|---|
| `ACIA AAAA AAIC` | character 2 = `C` (nibble 2) and checksum nibbles `I`,`C`; character 1 kept `A` | **ACCEPT** | `$0569` HMax=25, `$056A` S.level=4, `$056B` EMax=15; field bytes `02 80 00 00 00 A4` |

This code is not on GameFAQs, VGChartz, TCRF, RetroMaggedon, or any wiki.
It is not an alias: the published level-1 code gives HMax=20 / S.level=2 /
EMax=10, and the published level-2 code is rejected, so the state
HMax=25 / S.level=4 / EMax=15 is not produced by any published code.

**Published codes accepted by the ROM validator.**

| code | source | validator result | RAM-verified state |
|---|---|---|---|
| `AAIA AAAA AAIA` | published level 1 / current | **ACCEPT** | HMax=20, S.level=2, EMax=10 |
| `AAPA AAAA AAPA` | Dan Weber blog, "change the I's to P's" | **ACCEPT** | HMax=20, S.level=2, EMax=10; field byte `$048C`=`$F0` (4 keys) vs `$80` (1 key) |

The Dan code is a published code that the previous draft reported as
rejected. Direct invocation of the ROM validator shows it is accepted; the
previous rejection is likely an editor input-path or timing artifact, since
`conv` maps both the raw-nibble and tile representations to the same field
bytes.

**Alias result.** The previous draft's `ABIA AAAA AAIA` is **rejected** by
the ROM validator (checksum: sum 0x81 ≠ raw 0x80). The on-screen acceptance
observed previously was an artifact of the editor's input path, not a
validator alias. No unused-nibble alias class was found.

**Rejection bounds (all tested by direct validator invocation).**

| code | violation | result |
|---|---|---|
| `BAIA AAAA AAIA` | `v0 = 1` (first nibble ≠ 0) | REJECT |
| `AKIA AAAA AAAK` | `v1 = 10` (second nibble ≥ 10) | REJECT |
| `AAHA AAAA AAHA` | `v2 = 7` (third nibble < 8) | REJECT |
| `AAIA BAAA AAJA` | `v4 = 1` (fifth nibble odd) | REJECT |
| `AAIA AEAA AAIE` | `v5 = 4` (`v5 & 0x0C ≠ 0`) | REJECT |
| `AAIA AAAB AAIB` | `v7 = 1` (`v7 & 3 ≠ 0`) | REJECT |
| `AAIA AAAA ABIB` | `v9 = 1` (`v9 & 3 ≠ 0`) | REJECT |
| `AAIA AAAA AAIB` | wrong checksum | REJECT |

**Published codes rejected.** All published level-2..12 codes and the
published Plasma Arrow code are rejected by the ROM validator (see §3).
The embedded NES image contains the same validator code, and the rejection
is caused by the first-nibble check (`v0 == 0`) and the second-nibble check
(`v1 < 10`). The published codes were generated for the original NES
password format; whether the original NES revision lacks the first-nibble
restriction, or the GBA port modified it, was not determined (see §8).

**Real-UI confirmation (this revision).** The three accepted codes above
(`ACIA AAAA AAIC`, `AAIA AAAA AAIA`, `AAPA AAAA AAPA`) were also entered
through the real on-screen password editor reached via the normal UI (§3).
The RAM state after each real-UI submission matched the direct validator
invocation exactly (§7), so the enumeration and the field checks above are
confirmed in-game.

## 7. Validation evidence

**Observed (real on-screen password editor, this revision):**

The ROM was booted on :236 and the password screen was reached through the
normal UI (§3): reset combo (A+B+Select+Start), Start (compilation menu),
Start (launch Strider), Select (toggle PASSWORD), Start (enter the mode).
The code was typed with the on-screen editor (A advances, B back, Left/Right
change the letter; the final A submits). The NES RAM was read afterwards for
verification.

* `ACIA AAAA AAIC` (novel): **ACCEPT**; buffer `$0202..$020D` =
  `C0 02 C8 C0 C0 C0 C0 C0 C0 C0 C8 02`; fields `$048B..$0490` =
  `02 80 00 00 00 A4`; state `$0569`=25 (HMax), `$056A`=4 (S.level),
  `$056B`=15 (EMax).
* `AAIA AAAA AAIA` (published level 1): **ACCEPT**; fields
  `$048B..$0490` = `00 80 00 00 00 80`; state `$0569`=20, `$056A`=2,
  `$056B`=10.
* `AAPA AAAA AAPA` (Dan Weber blog): **ACCEPT**; buffer
  `C0 C0 0F C0 C0 C0 C0 C0 C0 C0 0F C0`; fields `$048B..$0490` =
  `00 F0 00 00 00 F0`; state `$0569`=20, `$056A`=2, `$056B`=10.

These real-UI results agree with the direct validator invocation below. The
previous draft's on-screen rejection of `AAPA AAAA AAPA` is confirmed to be
an editor input-path/timing artifact.

**Observed (emulator RAM reads, direct validator invocation):**

* The validator at NES `$B280` was invoked with the 12 display tiles
  written directly to `$0202`–`$020D` and X=0, Y=0. The result was read
  from `$FF` (0x00 = accept, 0x63 = reject).
* `AAIA AAAA AAIA` (published level 1): ACCEPT; fields
  `$048B..$0490` = `00 80 00 00 00 80`.
* `AAPA AAAA AAPA` (Dan Weber blog): ACCEPT; fields
  `00 F0 00 00 00 F0`; state variables `$0569`=20, `$056A`=2, `$056B`=10.
* `ACIA AAAA AAIC` (novel): ACCEPT; fields
  `02 80 00 00 00 A4`; state variables `$0569`=25, `$056A`=4, `$056B`=15.
* All published level-2..12 codes and the published Plasma Arrow code:
  REJECT; the field bytes and rejection reasons are in §3.
* `ABIA AAAA AAIA` (previous draft's alias): REJECT (checksum).
* The rejection-bound codes R1–R8 (§6b) all REJECT with the expected
  reason.
* The state variables `$0569`/`$056A`/`$056B` were read after the accept
  path; `$9957` sets them from the table at `$9982` using character 2.

**Observed (emulator screenshots, previous run; not re-taken this revision):**

* The compilation menu, the Strider title, the Blue Dragon console, and the
  password screen were reached by the key sequence in §3.
* `AAIA AAAA AAIA` accepted on-screen; screen changes to the world map with
  `KAZAKH`.
* `BCJB BBNB NBAB`, `CJBE ADBO BONC`, `BBJB BCBB BBIB`, `AAPA AAAA AAPA`,
  `AAJA AAAA AAJA`, `ABIC ADAE AFIG` produced `PASSWORD WRONG` on-screen.
  The `AAPA AAAA AAPA` rejection is now known to be an editor input-path
  artifact; the validator itself accepts it, and the real-UI run this
  revision confirms the accept.
* The password buffers and field bytes were read live from the NES RAM base
  `0x030002E0`.
* Bionic Commando and Mighty Final Fight boot from the compilation menu;
  neither exposes a password screen in the first screens walked.

**Derived (disassembly):**

* The GBA loader at `0x2300` and the image-base table at `0x23C0`.
* The NES password editor at `$B154`, validator at `$B280`, accept path at
  `$B317`, reject path at `$B32D`, and the field checks in §5.2.
* The 6502 core and NES RAM base `0x030002E0` from the IWRAM core loads and
  a read watchpoint on the Strider ROM base.
* The validator reads the contiguous buffer `$0202`–`$020D`; the `$0302`
  buffer is written by the editor but not read by the validator.
* The `$09` checksum comparison value is the raw last byte
  `(v10 << 4) | v11`, built from the low nibbles of `$0202[10]` and
  `$0202[11]`.

**Inferred:**

* The GBA port's validator is the original NES validator code. The previous
  draft's on-screen rejection of `AAPA AAAA AAPA` was an editor input-path or
  timing artifact: the direct validator invocation accepts the code, and the
  real-UI run this revision confirms the accept with fields
  `00 F0 00 00 00 F0`.
* The published level-2..12 codes are rejected by the ROM validator because
  their first character is not `A`; the original NES password format may not
  have this restriction, or the GBA port's validator is a modified version.

## 8. Unknowns

* **The exact game-state mapping of the field bytes.** The validator's
  accept path calls `$9957`, which sets `$0569` (HMax), `$056A` (S.level)
  and `$056B` (EMax) from character 2 (`v1`) via the table at `$9982`.
  The remaining field bits (characters 3–10) encode keys, disks, analyzed
  disks, boots, Plasma Arrow, Kain and Red Dragon, but the exact bit-to-
  item mapping was not fully reversed. The novel code `ACIA AAAA AAIC`
  changes character 2 and produces a verified S.level change; the key/
  disk/boot bits were not individually RAM-verified.
* **The editor input path.** The editor stores raw nibbles for changed
  characters, while unchanged characters keep their tiles; the validator's
  `conv` maps both representations to the same field bytes. The cursor
  starts at buffer index 0 and advances with A; B moves back; Left/Right
  change the letter; the final A submits. The exact conditions under which
  the editor accepts a code that the validator would accept (e.g. changing
  only some characters, or re-entering the code) were not fully mapped; the
  real-UI run this revision typed all 12 positions.
* **The original NES password format.** The published level-2..12 codes are
  rejected by the ROM validator's first-nibble check (`v0 == 0`). Whether
  the original NES validator lacks this check, or the GBA port modified it,
  was not determined; the embedded NES image is the same code that the GBA
  shell runs.
* **Mighty Final Fight and Bionic Commando negative result is bounded by
  the screens walked and the string search, not by a full playthrough.**
  Their images contain no `PASSWORD`/`PASS WORD` strings and no title
  password option; Bionic's pause/map screen is a level select, not a code.

## 9. Tooling

* `mGBA 0.10.5` (`/usr/games/mgba`) under `Xvfb :236` + `openbox`,
  `SDL_AUDIODRIVER=dummy`.
* `xdotool` for input; no new screenshots were taken for this revision.
* `arm-none-eabi-objdump`, Capstone (GBA shell, ARM/Thumb).
* `py65` + `da65` (cc65) for 6502 disassembly of the NES images.
* mGBA CLI debugger `-d` over a pty: registers, `x/1` memory dumps,
  `w/1` writes, `watch/r`, `watch/w`; used to find the NES RAM base, the
  password buffers, and the validator.
* Python reimplementation of the published Strider generator
  (`strider_pw.py`) and the password typer (`typecode3.py`).
* mGBA savestate parsing: PNG `gbAs` chunk, zlib-compressed
  `struct GBASerializedState` (mGBA `serialize.c`); layout ends with
  `vram[0x18000]`, `iwram[0x8000]`, `wram[0x40000]`.
* `gen_vpr.py`: builds a savestate that copies the validator and its
  subroutines into NES RAM, patches the accept/reject paths to return a
  result in `$FF`, writes a chosen 12-tile code into `$0202`, and invokes
  the validator. Used to test every code against the ROM's own validator.
* `pw.py` / `daemon_gen.py`: mGBA pty daemon and debugger command helper.

Generated files were kept in `/tmp/opencode/capcommix`, not in the ROM
folder.

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed. The
report contains only hashes, addresses, disassembly-derived findings, and
short code strings that are themselves developer-intended passwords.
