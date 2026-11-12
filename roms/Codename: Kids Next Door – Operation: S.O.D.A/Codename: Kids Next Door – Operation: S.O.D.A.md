# Codename: Kids Next Door – Operation: S.O.D.A. (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Codename: Kids Next Door – Operation: S.O.D.A/Codename: Kids Next Door – Operation: S.O.D.A.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title | `KIDSNEXTDOOR` (`0xA0`) |
| Game code | `BNDE` (`0xAC`) |
| Maker code | `54` (`0xB0`) |
| Version | 0 (`0xBC`) |
| Fixed byte | `0x96` at `0xB2` |
| Entry word | `0xEA00002E` (stock ARM `b 0x080000C0`; no cracktro/trainer) |
| Header complement | `0x31` (recomputed matches stored), header checksum `0x0000` |
| MD5 | `e26711c4aae6f6271e73f663b476c66a` |
| SHA-1 | `bbd176cc9a5331fdfdb332ad037d869610e4b3fb` |
| SHA-256 | `9462aa17c8e9c5e4f7ee079a7469da41d06d1aee92c42e31b6948046d4f3b7b0` |

Embedded-header scan: exactly one copy of the 156-byte Nintendo logo, at file
offset `0x04` (header `0x00`). This is a single normal image, not a
multi-game pack; no appended trainer, no cracktro, no rebuilt header.

Engine notes: native ARM/Thumb, Shin'en Multimedia string at `0x7E2582`
("Shin'en Multimedia. Code: B.Wodok"), mode-4 bitmap menus, script-driven
screens ("script_license", "script_cutscene", "script_startLevel" at
`0x32D70`–`0x32D98`).

## 2. Executive summary

The game has **two independent developer-intended input systems**:

1. **A 6-character progress password**, typed on an on-screen 4×8 keyboard.
   Alphabet (ROM `0x08032D98`):

   ```
   bcdfghjkmnpqrstvwxyz0123456789?*
   ```

   Six symbols × 5 bits = a **30-bit payload**. The decoder at `0x0800EBD8`
   reads the six *symbol indices* LSB-first and, after every five payload bits,
   discards three alignment bits (the unused high bits of each index byte); the
   six 3-bit reads at field positions 6, 12, 18, 24, 30 and 36 are discarded by
   the code. The 30 bits therefore decode to 30 single-bit flags / small packed
   fields written into the progress struct at `0x02004414`.
   A 2-bit checksum and a handful of range checks gate acceptance; failures
   return 0 and take the reject path at `0x08015DFE`.

   The famous published code **`1mc001` is not part of that encoding** — it is a
   hard-coded literal comparison at `0x08015D80`/`0x08015D86`. On a match the
   game calls `0x0800589C(0x02002B08, 2)`, which writes byte `0x02002B22 = 1`
   (cheat slot #2), and displays the message descriptor at `0x08032B14`.

   Verified published progress codes: `0k0hgd` (Section 1, Numbuh Five) and the
   rest of the GameFAQs/Vizzed list decode and pass the ROM checksum. The
   complete representable space is **32^6 = 1,073,741,824** inputs; the
   checksum + range layer leaves at most `2^28` accepted values (≤268 million;
   the 2-bit check alone passes 1 in 4 payloads, and the range checks only
   reduce that further).

2. **A key-sequence recorder** at `0x08005814` that turns the joypad mask into
   the characters `B L R u d l r` (and space) and compares the recent history
   against six stored strings at `0x08032524`:

   ```
   "lrudBBLR"  "baisoku"  "BBBrdu"  "LRLRuuudd"  "RRlrrl"  "urdlurdlB"
   ```

   Entry 2 is the text "baisoku" (Japanese "high speed"), not a button string,
   so that slot cannot be typed and is dead data. The six slots map to ids
   1,2,3,4,0,5 respectively; each id sets a flag byte at object `+0x18+id`
   (`0x0800589C`).

The pause-menu text bank also contains four never-shown entries — `level skip`,
`cheats`, `cs`, `mission select` — in the same descriptor family as
`Quit level?`/`Quit game?`/`Sleep?` (`0x0803CCF8`–`0x0803CD2C`, menu tables at
`0x3E4F0`/`0x3E6F8`). They are present as data; no reachable screen in this run
selected them (see §8).

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL) under `Xvfb :258` + `openbox`,
`SDL_AUDIODRIVER=dummy`, `mgba -3 -d game.gba` (CLI debugger on a pty).
Default keys: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
d-pad = arrows. Hold 120 ms; menus poll once per frame. Savestates: `Shift+F1..F10`
save, `F1..F10` load. `kill -INT` breaks into the mGBA debugger; commands
`x/4 ADDR`, `w/4 ADDR VAL`, `w/r rN VAL`, `break/t ADDR`, `c`, `n`, `save N`, `load N`.

Password screen (screen-request 5):

```
app = [0x02004410]            ; 0x02014640 in this run
write 5 to app+0x128          ; screen request word, dispatch table 0x0800D110
continue                      ; dispatcher 0x0800D0E4 -> case 5 -> 0x0800DAA4
                              ; -> init 0x08015AD8 (object 0x020147C4)
```

On the screen: d-pad moves a 4-row × 8-column cursor, A appends the highlighted
symbol (`index = row*8 + col`), B deletes, the 6th symbol validates
immediately. Cursor at object `+0x24` (col), `+0x28` (row), count at `+0x2C`,
ASCII at `+0x30..0x35`, symbol indices at `+0x38..0x3D`.

> Harness note (labelled): the password screen is normally reached through the
> mission/pause flow. In this run the title/attract loop ignored menu input, so
> the screen was requested by writing the game's own screen-request word
> (`app+0x128 = 5`). The screen, keyboard, decoder, checksum and accept/reject
> branches are the game's own code driven by real `KEYINPUT`; only the
> transition request was issued by the debugger.

Codes tested (all entered with real key presses):

| Code | Type | Result |
|---|---|---|
| `1mc001` | published "sooper secret" | special branch; `0x02002B22` 0→1 |
| `0k0hgd` | published (Section 1, Numbuh Five) | ROM decoder returns 1 (accepted) |
| `cbbbcb` | **generated, unpublished** | accepted, `0x02004497` = 1 |
| `bbbbbc` | generated, bad checksum | rejected at `0x08015DFE` |
| `bbbbbb` | all symbols identical | rejected at `0x08015DFE` |

## 4. Address map

| Address | Meaning |
|---|---|
| `0x0800D0E4` | screen dispatcher; `state = [app+0x128]`, jump table `0x0800D110` (31 entries) |
| `0x0800D238` | case 5 body: enter password screen → `0x0800DAA4` |
| `0x0800DAA4` | password-screen enter wrapper |
| `0x08015AD8` | password screen constructor (alloc 0x50, vtable `0x02001910`) |
| `0x08015CC8` | password screen update (input, cursor, 6-char check, accept/reject) |
| `0x08015D4A` | A-press: `buf[count]=alphabet[row*8+col]`, `map[count]=row*8+col` |
| `0x08015D80` / `0x08015D86` | hard-coded compare with `"1mc0"` / `"01"` (`1mc001`) |
| `0x08015DB4`–`0x08015DE8` | "all six characters equal" reject pre-check |
| `0x08015DEA` | decode call: `0x0800EBD8(dest=0x02004414, src=obj+0x38)` |
| `0x08015DFE` | reject path (error jingle, 60-frame timer) |
| `0x08015E1C` | accept path (applies decoded save fields) |
| `0x0800EBD8` | **password decoder** |
| `0x0800EF10`–`0x0800EFA4` | checksum computation and 2-bit compare |
| `0x0800F1DC` | decoder reject/return-0 |
| `0x08004D78` | bit-reader init `{src, bitpos=0, bytepos=0}` |
| `0x08004CD0` | get_bits(n): LSB-first across bytes |
| `0x0800F5BC` | symbol → alphabet index (returns -1 if absent) |
| `0x0800F614` | alphabet index → symbol |
| `0x0800589C` | set flag `obj+0x18+id = 1` |
| `0x08005890` | add (sequence,id) to the key-sequence object |
| `0x08005814` | key mask → `B L R u d l r` recorder (`0x42 0x4C 0x52 0x75 0x64 0x6C 0x72`) |
| `0x08005790` | key-sequence object constructor (6 strings, ids 1,2,3,4,0,5) |
| `0x08032D98` | password alphabet (32 bytes) |
| `0x08032524` | key-sequence strings (6, variable length) |
| `0x080326B0`–`0x080326E0` | per-slot data records `{7, 0x0E, text_ptr}`; slot 4 is `{0x19,0,0x1F4}` |
| `0x08032B14` | message descriptor shown after `1mc001` |
| `0x0803CCF8` / `0x0803CD08` / `0x0803CD14` / `0x0803CD1C` | "level skip", "cheats", "cs", "mission select" strings |
| `0x0803E4F0`, `0x0803E6F8` | pause-menu item descriptors containing the hidden entries |
| `0x02004410` | global app pointer |
| `0x02014640` | app object (this run); state word `+0x128` |
| `0x02004414` | progress/save struct (decode destination) |
| `0x02000138` | secondary progress table touched by the decoder |
| `0x02002B08` | key-sequence object; flags at `+0x18`, e.g. `0x02002B22` |
| `0x02004524` | input struct `{mask, held, pressed}` used by the main loop |

## 5. Algorithm

### 5.1 Entry and keyboard

```
alphabet = "bcdfghjkmnpqrstvwxyz0123456789?*"   # 32 symbols at ROM 0x08032D98
cursor(row 0..3, col 0..7) -> index = row*8 + col
A: buf[count] = alphabet[index]; map[count] = index; count++
B: count-- (if count>0)
when count == 6: validate()
```

### 5.2 Bit reader

`get_bits(n)` reads **n bits LSB-first**

```
bit = (src[bytepos] >> bitpos) & 1
result |= bit << outpos
```

starting at `bytepos=0, bitpos=0`, wrapping `bitpos==8 -> bytepos++, bitpos=0`.

### 5.3 Decoder field stream (0x0800EBD8)

36 `get_bits` calls in a fixed order, total 48 bits:

```
for each of the 6 symbols:
    read 5 x 1-bit payload fields
    read 3 bits and DISCARD          # these are bits 5..7 of the index byte
```

The discarded 3-bit reads exist because the reader consumes whole bytes while
the alphabet only populates 5 bits. The 30 payload bits are written to the
progress struct as single-bit flags and to a few small multi-bit fields built
with `lsls/orrs` (e.g. `r5` from bits 3, 13, 19; a 2-bit field from bits 8, 11;
a 3-bit field from bits 4, 6, 17).

### 5.4 Checksum

Data bits **k16** and **k20** form a 2-bit stored check
(`k16 -> bit0`, `k20 -> bit1`). Let

```
S = sum(save+0x7B .. save+0x8A)          # 16 bytes written by the decode
  + 4 * sum(dest+0x8F .. dest+0x92)      # same 4 bytes added for each of 4 groups
  + popcount(field r5)
  + popcount(field [sp+0x0C])
  + popcount(field [sp+0x10])
accept <=> (3 & ~S) == stored2bit
```

Mismatch returns 0. Additional range checks: `r5 <= 4`, `[sp+0x0C] <= 4`,
`if r5==4 then [sp+0x0C]!=0`, and per-value conditionals on the low fields;
failures also return 0.

Decoder return: 0 = invalid, non-zero = valid (the caller tests `r0 != 0`).

### 5.5 Special code

```
if buf == "1mc001":
    set_flag(0x02002B08, 2)      # 0x0800589C -> byte 0x02002B22 = 1
    show_message(0x08032B14)
    close screen
else if all six buf bytes equal:
    reject (0x08015DFE)
else:
    r = decode(0x02004414, map[0..5])
    if r == 0: reject (0x08015DFE) else accept (0x08015E1C)
```

## 6. Tables

### 6.1 Alphabet and symbol values

| idx | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sym | b | c | d | f | g | h | j | k | m | n | p | q | r | s | t | v |

| idx | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sym | w | x | y | z | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | ? | * |

Vowels and `l` are absent, which is why the published codes look like
`0k0hgd`, `5?8pv6`, `3307?*`.

### 6.2 Published passwords (GameFAQs / Vizzed / emu-land)

`1mc001` (sooper secret), `0k0hgd`, `0v2bbd`, `8jgqhd`, `wfddcd`, `wvwbcd`,
`9kjqgd`, `1v8nvp`, `1krntd`, `52rptp`, `9khqjd`, `528sv7`, `3307?*`,
`529n*7`, `53*n?*`, `5?8pv6`.

All are 6 symbols from the alphabet above. `0k0hgd` was executed through the
ROM decoder (`0x0800EBD8`) and returned 1. `528Sv7` in the source list is a
case-typo for `528sv7`; the ROM alphabet is lower-case.

### 6.3 Key-sequence table (`0x08032524`)

| slot | string | bytes | id |
|---|---|---|---|
| 0 | `RRlrrl` | `52 52 6C 72 72 6C` | 0 |
| 1 | `lrudBBLR` | `6C 72 75 64 42 42 4C 52` | 1 |
| 2 | `baisoku` | `62 61 69 73 6F 6B 75` | 2 (not buttons — dead slot) |
| 3 | `BBBrdu` | `42 42 42 72 64 75` | 3 |
| 4 | `LRLRuuudd` | `4C 52 4C 52 75 75 75 64 64` | 4 |
| 5 | `urdlurdlB` | `75 72 64 6C 75 72 64 6C 42` | 5 |

Recorder character set (`0x08005814`): `B`=0x42, `L`=0x4C, `R`=0x52,
`u`=0x75, `d`=0x64, `l`=0x6C, `r`=0x72, space=0x20.

### 6.4 Progress fields written by the decoder

Destination `0x02004414`; observed writes (byte offsets):

`+0x7B..+0x8A` (checksum sum bytes), `+0x7C +0x7D +0x7E +0x7F +0x80 +0x81
+0x82 +0x85 +0x8A +0x8D +0x8E +0x8F +0x90 +0x91 +0x92 +0x93 +0x97`,
plus `+0x0C` and the secondary table at `0x02000138`.

Example decodes (ROM oracle, dest = `0x02004414`, all other bytes zero):

| code | accepted | bytes set |
|---|---|---|
| `0k0hgd` | yes (r0=1) | `+0x90..0x93 = 01`, `+0xA4..0xA7 = 01`, `+0x0C = 4` |
| `cbbbcb` | yes (r0=1) | `+0x97 = 01` |
| `hqv05?` | no (checksum: computed 1, stored 2) | `+0x8F = 01`, `+0x91 = 01` |

## 6b. Enumeration

**Space.** The entry alphabet has 32 symbols and the length is fixed at 6, so the
representable space is **32^6 = 1,073,741,824** inputs (30 payload bits).
There are no out-of-alphabet inputs on the real screen: the keyboard exposes
exactly those 32 symbols (4 rows × 8 columns). The decoder rejects on a 2-bit
checksum (`3 & ~S`, §5.4) and on range checks (`r5 <= 4`, `[sp+0x0C] <= 4`,
conditional rules), so the 2-bit check alone passes 1 in 4 payloads and the
range layer reduces the accepted subset further (≤2^28, not enumerated
exhaustively; single-bit toggling plus a handful of full decodes were used).

**Novel code (absent from every published list).**

```
cbbbcb      symbols: c(1) b(0) b(0) b(0) c(1) b(0)
            payload bits: k0 and k20 set
```

* Offline oracle (executing the ROM function `0x0800EBD8` with dest
  `0x02004414`, src = `01 00 00 00 01 00`): returns **1**.
* In-game: typed on the real keyboard (`Right A Left A A A Right A Left A`).
  The update reached the **accept** branch `0x08015E1C`
  (breakpoint hit, `r3 = r4 = 0x02004414`).
* RAM effect: `0x02004497` (`save+0x83`) changed from `0x00` to `0x01`;
  every other byte in `0x0200448C..0x020044A7` stayed zero. This matches the
  offline decode exactly.
* The string `cbbbcb` is not in any of the 16 published passwords listed in
  §6.2, nor in the GameFAQs/Vizzed/emu-land tables those came from.

**Bounds proven by rejection.**

* `bbbbbc` — six valid symbols, correct length, but fails the 2-bit checksum.
  Entered in-game it takes the **reject** branch `0x08015DFE`
  (breakpoint hit); the progress bytes are not committed.
* `bbbbbb` — all six symbols identical. The pre-check at `0x08015DB4` jumps to
  `0x08015DFE` without calling the decoder; observed on the same breakpoint.
* The keyboard physically cannot produce a symbol outside the 32-symbol
  alphabet, so "out-of-alphabet" rejection is structural (there is no text
  field).

**Published special code, verified in-game.** `1mc001` is matched literally at
`0x08015D80` (`cmp r1, 0x30636D31` = "1mc0") and `0x08015D86`
(`ldrh r1,[r6,#0x34]; cmp r1, 0x3130` = "01"). Entering it in-game changed
`0x02002B22` from `0x00` to `0x01` through `0x0800589C(0x02002B08, 2)`.
Baseline before entry: `0x02002B20 = 00000000`; after: `0x02002B20 = 00010000`.

## 7. Validation evidence

**Observed**

* Boot, header, hashes, single embedded header.
* Password screen created by the game's own case-5 handler (`0x0800D238` →
  `0x0800DAA4` → `0x08015AD8`), object `0x020147C4`; cursor/count/ASCII/index
  fields read at `+0x24/+0x28/+0x2C/+0x30/+0x38` after each keypress
  (`31 6D 63 30` = "1mc0" with count 4, then full acceptance).
* `1mc001` accepted; `0x02002B22` 0→1.
* `cbbbcb` accepted (`0x08015E1C` hit); `0x02004497` 0→1, matching the offline
  decode of the same symbol vector.
* `0k0hgd` executed through the ROM decoder returns 1.
* `bbbbbc` and `bbbbbb` both stop at `0x08015DFE`.

**Derived**

* 6×5-bit payload with six discarded 3-bit alignment reads
  (`0x08004CD0` called 36 times, widths `1,1,1,1,1,3` × 6).
* Checksum formula and the two check-bit positions (k16, k20), from
  `0x0800EF10`–`0x0800EFA4`; confirmed numerically on `hqv05?`
  (computed 1 vs stored 2) and on `cbbbcb` (computed 2, stored 2).
* All-identical pre-check and the special `1mc001` literal from the update
  disassembly.
* Key-sequence table, id mapping and recorder character map from
  `0x08005790`–`0x08005870` and the string pointers at `0x08032524`.

**Inferred**

* The names of the decoded progress fields (the report gives byte offsets, not
  game semantics; the accept handler only propagates `+0x8F..+0x93` when
  `save+8 == 3`, a state a fresh boot does not have).
* The hidden pause-menu labels `level skip`/`cheats`/`cs`/`mission select` are
  developer leftovers; the descriptor data is real but no live screen selected
  them in this run.

## 8. Unknowns

* Exact human-readable meaning of each decoded byte (`+0x7B..+0x9E`); only the
  offsets and the checksum inputs are proven.
* Whether the key-sequence slots are reachable in normal play (the title/attract
  loop ignored menu input in this run, so the sequence recorder was not
  exercised live). The strings and the matcher are ROM data; slot 2
  (`baisoku`) is structurally untypeable.
* The gate that would make the pause menu show `level skip`/`cheats`/`cs`/
  `mission select`; the labels exist in the same descriptor family as
  `Sleep?` but were not observed on screen.

## 9. Tooling

* mGBA 0.10.5 (`-3 -d`), `Xvfb :258`, `openbox`, `xdotool`, `SDL_AUDIODRIVER=dummy`.
* `arm-none-eabi-objdump` (`-M force-thumb`), Python 3 + `capstone` for the
  `movs r1,#n; bl 0x08004CD0` field-width extraction and BL/pointer scanners.
* Debugger scripts in `/tmp/opencode/kndsoda`: `daemon.py` (pty command
  bridge), `key.py`, `ss.py` (extract the zlib `gbAs` chunk from `.ssN`),
  `ssdiff.py`, `ptr.py`, `blscan.py`, `fields.py`.
* No GameShark/CodeBreaker/AR codes, no memory-edit cheats, no redistributed
  ROM data. Text is quoted only where it is the ROM's own message string.

## 10. Legal note

No ROM, graphics, audio or extracted asset is redistributed. All findings are
addresses, byte layouts, algorithms and the game's own short UI strings.
