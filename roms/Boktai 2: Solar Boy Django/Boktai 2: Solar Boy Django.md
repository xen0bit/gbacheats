# Boktai 2: Solar Boy Django (GBA, USA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Boktai 2: Solar Boy Django/Boktai 2: Solar Boy Django.gba` |
| Size | 16,777,216 bytes (0x1000000) |
| Header title | `BOKTAI2` |
| Game code | `U32E` |
| Maker code | `A4` |
| Software version | `00` |
| MD5 | `31231965d6a43d935e3629a67e06e0bb` |
| SHA-1 | `cd10d8ed82f4daf4072774f70d015e39a5d32d0b` |
| SHA-256 | `b51b6c667f4ff78f2e1462f8280af2e96e55fe872efdc85ecfc152f7c34e2483` |

Phase-0 integrity notes:

* One and only one GBA header exists: the 156-byte Nintendo logo occurs once, at
  file offset 0x4 (header base 0x0). This is a single 16 MiB image, not a
  multi-game pack.
* Complement check is valid (computed 0xF1, stored 0xF1).
* The header-checksum field at 0xBE is **0x0000**; the value computed from the
  header bytes is 0x8B77. The complement check and the entry chain are intact
  and the ROM boots and runs; the mismatch is recorded as a header-field anomaly
  of this image. No trainer/loader banner or patch strings were found
  (`PIRACY`, `TRAINER`, `CHEAT`, `BIOS` all absent).
* Entry word 0x00000000 = `EA000032` (`b 0x080000D0`); 0x080000D0 = `EA000037`
  (`b 0x080001B4`), where a normal Nintendo crt0 begins (`mov r0,#0x12; msr cpsr,r0`
  and the usual IRQ stack pointers at 0x080001E4). The 16 zero bytes at
  0x080000C0–0x080000CF are part of the same layout, not injected code.

### String reconnaissance

`strings -t x -n 4` yields 145,167 strings. Keyword counts over that list:

| keyword | hits | classification |
|---|---|---|
| `password` | 2 | both are the password screen (`Enter Boktai password?`, `Incorrect password.`) |
| `cheat` | 0 | — |
| `debug` | 0 | no ASCII debug menu in this build |
| `secret` | 3 | story/item prose ("secret remedy", "secret powers") |
| `unlock` | 3 | story prose ("unlock the Tarot Seal") |
| `bonus` | 0 | — |
| `code number` | 7 | the 4-digit door-lock system (strings at 0xCB52F0/0xCB57FE), a player-set in-game lock, not a cheat |
| `four-digit` | 1 | same door lock |

No published password appears literally in the ROM: all 13 codes in §6.2 were
searched as byte strings and are absent, which shows the password is
generated/validated, never stored. No trainer, debug menu or Cheat-Device menu
text exists in ASCII or in the +0x20 lowercase shift.

## 2. Executive summary

The game contains **two developer-intended code systems**:

1. **The Boktai 1 continuation password** ("Enter Boktai password?"), entered
   when starting a new game. It is a 32-character password over a 64-symbol
   alphabet; each symbol is 6 bits (192-bit stream). The stream carries a 3-bit
   format tag, a 16-bit CRC-16/CCITT checksum, a 2-bit scramble selector, twelve
   packed fields (title, stats/save data) and a 10-byte player name. The
   validator lives at ROM 0x08011490 and is fully reversed; a bit-exact
   encoder/decoder is in §5. All 13 published codes I could recover validate
   against the checksum model (13/13), and one **novel code that appears in no
   published list** was entered through the real on-screen keyboard and accepted
   by the game: it imports the otherwise-unpublished **Pawn** title and the name
   `OPENCODE`.
2. **The Crossover Battle button code** entered in the Link section
   (`L R L R L L R R R R L L SELECT START SELECT START`). Its 16-entry
   `u16` mask table is present verbatim at 0x085A63A4 and its validator at
   0x0804AD42 is reversed. Link mode is gated on save data; the gate was
   reproduced in-game ("No saved data found. Saved data is required to enter
   Link mode."), which is why the button test in this run is limited to the ROM
   table/validator plus the gate observation (§8).

No GameShark/CodeBreaker/memory-edit codes are reported.

## 3. How to reproduce

### Emulator

* mGBA 0.10.5 (SDL frontend, Debian package `mgba-sdl`), on `Xvfb :190`,
  `SDL_AUDIODRIVER=dummy`, `openbox`.
* Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrows, fast-forward=`Tab`.
* The GBA viewport is 720×480 at window offset +282,+312 at `-3`.

### Menu path (all reached in this run)

* Boot → solar-sensor notice (A) → TIME SETTING (Start) → REGION SETTING (A) →
  Konami logo → title.
* Title menu: `GAME START` / `LINK` / `OPTIONS` (Left/Right cycles).
* `OPTIONS`: SOLAR SENSOR SETTING, REGION SETTING, EXPLANATION (8 pages:
  THE SOLAR SENSOR, SOLAR SENSOR EFFECTS, CAUTION, DIRECTION & TILT,
  SOLAR SENSOR & PLACE, SOLAR SENSOR & TIME, SOLAR SENSOR & WEATHER,
  SOLAR SENSOR & ? ? ?).
* `GAME START` → file select ("No data.", START FROM BEGINNING) →
  **"Enter Boktai password?" YES/NO** → INPUT PASSWORD (4 rows of 8 slots,
  65-symbol on-screen keyboard) → PLAYER NAME → CONFIRM SETTING
  (`Boktai title [ … ]`) → intro.
* `LINK` → blocked without save data (see §8).
* In-game pause (Start): MAP, ITEM, VALUABLES, STATUS, SLEEP (L/R cycle).
  STATUS shows LV, EXP, LIFE/ENE, ATCK/DFND, VITL/SPRT/STRG/AGIL and the imported
  player name.

### Codes tested

Published codes used as anchors (all accepted unless noted; all CRC-valid):

```
Trigger of Sol        N0#:7j@B-F_q^::Z5#7lmnCwN#lwM=Mc
Trigger of Sol (alt)  D??:7j@G-F_q^::Z5#7lmnCwN#lwM=Mc
Gun Master            X5zw6j>hMY^qg/:Z5#7lmnCwN#lwz+Mc
Bishop                >tZ>>YG_?gLLDX+3Zwm-^zmnCwNKQmJ:
Queen                 NzWQnfdKF!K8^w#1/8j48znCwN#lmJ:M
Berserker             0C+c-j212p8qg0:Z5#7lmnCwN#l+3+Mc
Solar Boy             >W+Jdj-c0^^qgs7G5#Mv8yCwN#lmJ:Mc
Solar Boy (alt)       NSf#fj4L1-^qMs7G5#Mv8yCwN#lwJ:Mc
Dark Boy              h9bfvCgX+>@Hf3>-9Sm^0smmnCw86jmJ
Death                 rF0MtRdD/_^g2bckYM+CNbmmnCwN#lmJ
Solar Merchant        DrJKKd2D:=87ghgk4-MlmnCwN#lS-=Mc
King                  NM?sdMJz!LNND8+3Zwm-^zmnCwN#lmJ:
Rook                  DF74Lj@p+-_7yTsk4+dlmnCwN#lmJ:Mc
```

Novel code (not in any published list), entered key-by-key in the emulator:

```
8>m@fj4L1-^qMKxZyvMG@=MQD#lmJ:Mc
```

Result: "Boktai data successfully continued." then CONFIRM SETTING with
`NAME : OPENCODE` and `Boktai title [ Pawn ]` (screenshots
`typednovel_typed.png`, `typednovel_submit.png`, `typednovel_confirm.png` in
`/tmp/opencode/boktai2/`).

Bounds tested (all rejected with "Incorrect password."):

```
a=1 variant           7>m@fj4L1-^qMKxZyvMG@=MQD#lmJ:Mc
bad checksum          8>m@fj4L1-^qMKxZyvMG@=MQD#lmJ:Mx
'.' (unused 65th key) 8>m@fj4L1-^qMKxZyvMG@=MQD#lmJ.Mc
```

### Solar sensor

The cartridge function is emulated by mGBA 0.10.5 at the GPIO level (the core
contains `[SOLAR] Output %u` and the Boktai GPIO handling), but the SDL frontend
has no control to set the light level. The game's `SOLAR SENSOR SETTING`
calibration screen runs, the Sun gauge stays empty, and solar charging does not
occur. This does not block any menu or the password/link code paths; it is
recorded as an emulator limitation.

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`.

| ROM address | Role |
|---|---|
| 0x08CE4441 | 65-byte symbol string `BCDFGHJKLMNPQRSTVWXYZbcdfghjklmnpqrstvwxyz0123456789?!@#=^>/-_+:.`; validator uses the first 64 bytes as its lookup table |
| 0x08CA0E3F | "Enter Boktai password?" |
| 0x08CA0E56 | "Boktai data successfully\ncontinued." |
| 0x08CA0E7A | "Incorrect password." |
| 0x08CA0E8E | "Boktai title" |
| 0x08CA0F48 | 15-title table: Trigger of Sol, Gun Master, Gladiator, Bishop, Queen, Berserker, Death, Solar Boy, Dark Boy, Solar Merchant, Running man, King, Rook, Knight, Pawn |
| 0x082178D8 | password-screen string renderer (reads 32-byte value buffer) |
| 0x08217A3C | append one symbol to the password buffer |
| 0x08217AEC | INPUT PASSWORD state machine |
| 0x08217D56 | submit path (calls the validator) |
| 0x08011490 | password validator wrapper (allocates 0xAC-byte work struct) |
| 0x080110C8 | alphabet conversion: 32 ASCII chars -> 32 values 0..63 |
| 0x080110A8 | linear search in the 64-byte alphabet table |
| 0x080111E0 | field unpack + CRC-16 check + name/title validation |
| 0x08011054 | LCG descrambler over bytes 4..31 |
| 0x08011100 | 6-bit-packed bit extractor `(array,pos,width)` |
| 0x080113E0 | export decoded values to the game state |
| 0x0804AF60 | Link/Crossover screen setup; stores 0x085A63A4 at object+0x30 |
| 0x0804AD42 | button-code validator (index compare loop) |
| 0x085A63A4 | 16 × u16 expected key masks (Crossover Battle code) |

RAM (observed while the password screen was open):

| Address | Role |
|---|---|
| 0x02007DB0 | password-screen object base |
| 0x02009F40 | 32-byte symbol buffer (values in the game's internal symbol order) |
| 0x02009F60 | u32 count of entered symbols |
| 0x0203C400 | save/import block; +0x0A/+0x0C/+0x0E receive imported values, +0x0E = title index |
| 0x030044E0 | pointer to key-state mirror; +2 = current key mask (u16) |
| 0x030047A8 | pointer written with 0x369F at button-code completion |
| 0x030046A0 | pointer to the active save block |

## 5. Algorithm

### 5.1 Symbol alphabet and internal order

The validator alphabet is the first 64 characters of the ROM string:

```
BCDFGHJKLMNPQRSTVWXYZbcdfghjklmnpqrstvwxyz0123456789?!@#=^>/-_+:
```

(0–20 uppercase, 21–41 lowercase, 42–51 digits, 52–63 the 12 symbols
`? ! @ # = ^ > / - _ + :` in that order). The 65th character of the ROM string
(`.`) exists on the entry keyboard but is **not** in the 64-byte lookup table, so
any code containing `.` is rejected (proved in §6b).

The on-screen keyboard stores a different internal code for each key
(0–51 letters/digits as above, then 52–64 in screen reading order
`+ = : . - _ > ^ # / ? ! @`). The submit path converts that internal code back
to an ASCII symbol; the validator then maps ASCII to 0..63 with the table above.
The conversion is therefore invisible to a user typing through the UI.

### 5.2 Bit stream

Let `v[0..31]` be the 32 six-bit symbols. Bit `i` of the 192-bit stream is bit
`i mod 6` of `v[i div 6]` (LSB-first, each symbol contributes 6 bits):

```
bits = concat(for v in symbols: for k in 0..5: (v >> k) & 1)
```

Fields are read LSB-first with `field(bits,pos,width)`.

### 5.3 Layout

```
pos  0  w3   type      must be 2 for the USA 32-char format
pos  3  w16  checksum  0xFFFF & ~CRC16( stored bytes 4..31 )
pos 19  w2   scramble selector c (0..3)
pos 21  w9   field0
pos 30  w7   field1
pos 37  w6   field2
pos 43  w6   field3
pos 49  w3   field4
pos 52  w5   field5
pos 57  w3   field6
pos 60  w4   field7
pos 64  w5   field8
pos 69  w7   field9
pos 76  w4   field10
pos 80  w5   field11   title index 0..14 (see §6)
pos 85  w8×10          player name, 10 ASCII bytes, NUL padded
(if type==1 only) pos 165 w6, 171 w6, 177 w8  — never accepted by this build
```

### 5.4 Checksum

CRC-16/CCITT, polynomial 0x1021, initial value 0xFFFF, over the **stored**
(scrambled) bytes 4..31, each 6-bit value placed in the low bits of a byte:

```
crc = 0xFFFF
for byte in stored[4:32]:
    crc ^= byte << 8
    repeat 8: crc = ((crc<<1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc<<1)&0xFFFF
checksum = (~crc) & 0xFFFF
```

### 5.5 Descrambler

A 32-bit LCG XORs the low 6 bits of 28 bytes:

```
state = 0x0008C159          # literal at validator +0x9C
k     = 0x6262C05D          # literal at 0x08011050
r6    = 0xFFFF              # literal at 0x080110A4
def step():
    global state
    state = (state * k + 1) & 0xFFFFFFFF
    return state
for _ in range(c + 4):      # c = bits 19..20
    r6 ^= step()
for i in 4..31:
    data[i] = (stored[i] ^ r6) & 0x3F
    r6 ^= step()
```

The same routine is its own inverse; the encoder applies it to the plaintext
fields and then computes the checksum over the result. Bytes 0..3 (which hold
type/checksum/selector and the first field bits) are never scrambled.

### 5.6 Validation

```
if len != 32 or any symbol not in 64-char table: reject
type = bits[0:3]; chk = bits[3:19]; c = bits[19:21]
if chk != ~CRC16(stored[4:32]): reject            # "Incorrect password."
descramble
if type != 2: reject
if name[0] == 0: reject
if field6 == 0 or field2 == 0: reject
if name contains a byte that is non-zero and not
   [A-Za-z0-9] or one of the 13 bytes at 0x085A564C: reject
accept
```

The name-character check at 0x0801118C returns 0 as soon as it meets one valid
character, so it only rejects wholly non-text names; this is why arbitrary ASCII
names are accepted.

### 5.7 Encoder (pseudocode)

```
def encode(type, c, fields[12], name[10]):
    bits = [0]*192
    put(bits,0,3,type); put(bits,19,2,c)
    pos = 21
    for w,v in zip(WIDTHS,fields): put(bits,pos,w,v); pos += w
    for b in name: put(bits,pos,8,b); pos += 8
    plain = to6bit(bits)
    stored = scramble(plain, c)
    put_bits_in_stored(stored, 3, 16, ~CRC16(stored[4:32]))
    return symbols(stored)
```

## 6. Tables

### 6.1 Title table (0x08CA0F48)

Index → string: 0 Trigger of Sol, 1 Gun Master, 2 Gladiator, 3 Bishop, 4 Queen,
5 Berserker, 6 Death, 7 Solar Boy, 8 Dark Boy, 9 Solar Merchant, 10 Running man,
11 King, 12 Rook, 13 Knight, 14 Pawn.

`field11` is the title index. Verified on the CONFIRM SETTING screen: the
published Solar Boy code shows `[ Solar Boy ]`; the published Dark Boy code
shows `[ Dark Boy ]`; the novel code with field11=14 shows `[ Pawn ]`.
Field 11 is exported to save block 0x0203C400+0x0E.

### 6.2 Published codes as decoded by this model

| Password | Label | field11 | Name | c | CRC |
|---|---|---|---|---|---|
| `N0#:7j@B-F_q^::Z5#7lmnCwN#lwM=Mc` | Trigger of Sol | 0 | Char | 3 | ok |
| `D??:7j@G-F_q^::Z5#7lmnCwN#lwM=Mc` | Trigger of Sol (alt) | 0 | Char | 3 | ok |
| `X5zw6j>hMY^qg/:Z5#7lmnCwN#lwz+Mc` | Gun Master | 1 | Char | 3 | ok |
| `>tZ>>YG_?gLLDX+3Zwm-^zmnCwNKQmJ:` | Bishop | 3 | Django | 1 | ok |
| `NzWQnfdKF!K8^w#1/8j48znCwN#lmJ:M` | Queen | 4 | Django | 2 | ok |
| `0C+c-j212p8qg0:Z5#7lmnCwN#l+3+Mc` | Berserker | 5 | Char | 3 | ok |
| `>W+Jdj-c0^^qgs7G5#Mv8yCwN#lmJ:Mc` | Solar Boy | 7 | Django | 3 | ok |
| `NSf#fj4L1-^qMs7G5#Mv8yCwN#lwJ:Mc` | Solar Boy (alt) | 7 | Django | 3 | ok |
| `h9bfvCgX+>@Hf3>-9Sm^0smmnCw86jmJ` | Dark Boy | 8 | Random | 0 | ok |
| `rF0MtRdD/_^g2bckYM+CNbmmnCwN#lmJ` | Death | 6 | Death | 0 | ok |
| `DrJKKd2D:=87ghgk4-MlmnCwN#lS-=Mc` | Solar Merchant | 9 | Pawn | 3 | ok |
| `NM?sdMJz!LNND8+3Zwm-^zmnCwN#lmJ:` | King | 11 | Django | 1 | ok |
| `DF74Lj@p+-_7yTsk4+dlmnCwN#lmJ:Mc` | Rook | 12 | Masa | 3 | ok |

The 13/13 checksum agreement (1 in 2^16 each) is the primary proof of the CRC
model; the decoded names are all plausible Boktai 1 player names and the exported
title index matched the label for every unambiguous published entry.

### 6.3 Crossover Battle button table (0x085A63A4)

16 × u16, exactly the published sequence:

```
0x0200 0x0100 0x0200 0x0100 0x0200 0x0200 0x0100 0x0100
0x0100 0x0100 0x0200 0x0200 0x0004 0x0008 0x0004 0x0008
 L      R      L      R      L      L      R      R
 R      R      L      L      SELECT START  SELECT START
```

Validator at 0x0804AD42:

```
i = obj[0x2D]
if keyState == table[i]:
    i++; obj[0x2D] = i; obj[0x2E] = 0
elif keyState != 0:          # a wrong key cancels progress
    obj[0x2D] = 0; obj[0x2E] = 0
if ++obj[0x2E] > 0x77: reset
if obj[0x2D] > 15:           # all 16 matched
    state = 3; obj[0x2D] = 0
    *(u16*)(*(u32*)0x030047A8 + 0x10) = 0x369F
    play sound 0x296
```

The comparison is equality against the *held-key* mask, so the sequence must be
pressed one button at a time (holding two buttons never matches). "No key held"
does not reset progress; a wrong key does.

## 6b. Enumeration

### Space

* 32 symbols from a 64-symbol alphabet: 64^32 = 2^192 ≈ 6.28×10^57 strings.
* The 16-bit checksum at bits 3..18 fixes 2^16 of those, so exactly
  2^192 / 2^16 = 2^176 ≈ 9.6×10^52 strings pass the checksum.
* Of those, the validator further requires `type==2` (1 of 8 → 2^173),
  `name[0] != 0`, `field2 != 0`, `field6 != 0` and the weak name-class test.
  The usable title space is field11 = 0..14 (15 values); values 15..31 produce a
  wrong text pointer on the confirm screen rather than a rejection.
* The alphabet has 64 usable symbols; the 65th key (`.`) is present on the
  keyboard but has no lookup entry and is always rejected.

### Novel codes (absent from every published list consulted)

| Code | Why novel | In-game proof |
|---|---|---|
| `8>m@fj4L1-^qMKxZyvMG@=MQD#lmJ:Mc` | field11=14 ("Pawn") is not present in any published list I recovered; name `OPENCODE` is not a published sample name | typed key-by-key; "Boktai data successfully continued."; CONFIRM SETTING shows `NAME : OPENCODE`, `Boktai title [ Pawn ]`; STATUS page shows the imported name |

A second novel code, for a different title, was also entered and accepted:

```
Dms#fj4L1-^qM#7G5#Mv8yCwN#lmJ:Mc   field11=2 ("Gladiator")
```

Result: "Boktai data successfully continued." and CONFIRM SETTING with
`Boktai title [ Gladiator ]` (screenshots `glad_after_submit.png`,
`glad_confirm.png`). `Gladiator` is not represented by any published code I
recovered. A checksum-valid `field11=14` variant with a different prefix is
`>DP#fj4L1-^qMK7G5#Mv8yCwN#lmJ:Mc`.

### Bounds proven by rejection (in-game, "Incorrect password.")

| Input | Property exercised | Result |
|---|---|---|
| `7>m@fj4L1-^qMKxZyvMG@=MQD#lmJ:Mc` | type=1, checksum valid, fields valid | rejected |
| `8>m@fj4L1-^qMKxZyvMG@=MQD#lmJ:Mx` | last symbol changed, checksum invalid | rejected |
| `8>m@fj4L1-^qMKxZyvMG@=MQD#lmJ.Mc` | contains `.` (the 65th keyboard symbol, outside the 64-byte table) | rejected |

This establishes that the accept path really checks the CRC and the symbol
table, not merely the length, and that the type field is constrained to 2.

## 7. Validation evidence

**Observed (emulator screenshots / RAM reads):**

* Title menu has three entries; overloaded OPTIONS submenu and 8 explanation
  pages; the password prompt appears at the start of a new game.
* Published Solar Boy code accepted and CONFIRM SETTING shows `[ Solar Boy ]`;
  published Dark Boy code shows `[ Dark Boy ]`.
* Novel code accepted from the on-screen keyboard; `[ Pawn ]` + `OPENCODE`.
* The three bound cases above show "Incorrect password.".
* Pause menu pages and STATUS page (LV.01, VITL/10 SPRT/10 STRG/10 AGIL/10 for
  the Pawn import) captured.
* `LINK` shows "No saved data found. Saved data is required to enter Link mode."
* RAM: password buffer 0x02009F40, count 0x02009F60, decoded struct with ASCII
  name at 0x020079xx, save block 0x0203C400 where +0x0A/+0x0C/+0x0E change with
  the imported values.

**Derived (instruction-level):**

* Field widths and positions, CRC polynomial/init/coverage, LCG constants and
  the XOR order, and the `type==2` requirement all come from the disassembly of
  0x080111E0/0x08011054/0x08011100.
* `field11` is the title index: it equals the published title order for all
  unambiguous codes and is what the confirm screen renders.
* Button table contents and the equality/held-key validator at 0x0804AD42.

**Inferred:**

* Three fields are exported straight to the save block by 0x080113E0:
  field1 -> 0x0203C400+0x0A, field10 -> +0x0C, field11 (title) -> +0x0E.
  This matches the code (`str` of struct+0x62, +0x74, +0x76) and the RAM reads
  for the Solar Boy and Dark Boy codes (68/3/7 and 68/2/8). The gameplay meaning
  of field1 and field10 (Boktai 1 play data: Sol count, time, rank) is not
  proven here.
* The exported per-title stat bonuses/items (e.g. Dark Boy +2 STRG/AGIL) are
  documented by the community but were not re-derived; the Pawn import grants
  no visible stat change (STATUS stayed at 10/10/10/10), which is consistent
  with Pawn being the zero-bonus title.

## 8. Unknowns

* **Link-mode runtime test.** Link mode (and therefore the in-game entry of the
  Crossover Battle button code) requires save data. The gate was reproduced but
  no save file was produced in this run, so the button sequence was not pressed
  on the real Link screen. What *is* proven: the 16-mask table is present at
  0x085A63A4 with every entry equal to the published sequence, the validator
  that consumes it is at 0x0804AD42, and the success path sets state 3 and
  writes 0x369F. A follow-up with any legitimate save file can confirm the
  screen transition in one attempt.
* The precise gameplay meaning of fields 0/1/2…10 (Boktai 1 Sol count, time,
  rank, continues, charged energy, dungeons cleared) is not proven; only the
  title index (field11) and the name are.
* Title indices 15..31 are not rejected by the validator but display an
  unrelated text pointer (observed: `[ UNDER A HOT SUN ]`); the intended
  behaviour of these values is unknown.
* The solar sensor cannot be driven from the SDL frontend, so sunlight-dependent
  effects could not be exercised.

## 9. Tooling

* `mGBA 0.10.5` (SDL), `Xvfb`, `openbox`, `xdotool`, `scrot`, ImageMagick.
* `arm-none-eabi-objdump -M force-thumb` for the validator, input screen and
  button-code functions.
* `codec.py` — bit-exact decoder/encoder (alphabet, CRC, LCG, field packer).
  `decode.py` is the earlier decode-only version.
* `testcode.py` / `typecode.py` — restart the emulator from the password-screen
  savestate, inject or key-type a code, submit it, and capture the acceptance
  and confirm screens.
* `rsp.py` / `rspserver.py` / `rc.py` — a minimal GDB-remote-protocol bridge used
  to read/write EWRAM, set watchpoints and step the validation path. Because
  another session owns TCP 2345, an `LD_PRELOAD` shim (`shim/shim.c`) remaps
  mGBA's GDB port to 23455.
* Working directory and screenshots: `/tmp/opencode/boktai2/`
  (`typednovel_*.png`, `novel_*.png`, `a1_*`, `badck_*`, `dot_*`, `g18.png`,
  `g49.png`, `g50.png`, `menu*.png`).

## Legal

No ROM, graphics, music or extracted text is redistributed. Only addresses,
algorithms, hashes and self-generated codes are published.
