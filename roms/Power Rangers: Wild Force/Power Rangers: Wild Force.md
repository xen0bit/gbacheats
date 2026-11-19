# Power Rangers: Wild Force (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Power Rangers: Wild Force.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `PR_WILDFORCE` |
| Game code | `APWE` (USA/Europe), maker `78` (THQ) |
| Version | `0x00` (Rev.00); complement byte `0x15`; header checksum `0x0000` |
| Entry word | `0xEA00002E` → stock `0x080000C0` (no cracktro/trainer patch) |
| MD5 | `577a14ef8e3646a2a8b3f39d9beb199e` |
| SHA-1 | `852d5eae2c6601a3ea0d17ecbff54d4d0a8cf8e4` |
| SHA-256 | `cdf1ab3b4732b54297370e7f59b844035c9c07772ad0ddc2451e371c4e1bebb9` |
| Embedded GBA headers | exactly 1 (Nintendo logo at file `0x04`); no multiboot stub, no appended trainer |

Developer Natsume, publisher THQ, 2002. Single-player campaign + 4-player link Battle Mode.

## 2. Executive summary

The game has a **5-symbol password system** on the main menu (`PASSWORD`), using a
32-symbol no-vowel alphabet `BCDFGHJKLMNPQRSTVWXYZ0123456789!`. It is **algorithmic**,
not a lookup table: no published code appears literally in the ROM in ASCII, `±0x20`,
UTF-16, or 5-bit-packed form.

The validator at `0x080065F4` was recovered completely and reimplemented in Python
(`pw.py`). It un-rotates five 5-bit fields, checks a 4-bit checksum, enforces fixed
bits and per-field ranges, and on success writes a start-state struct at
`0x03001860` (plus `0x030017D4`, `0x03001500`). Its encoder counterpart at
`0x08006530` generates the end-of-level password.

All 19 published codes found on SuperCheats/Cheat Happens validate against the model;
two were confirmed dynamically on the real ROM screen with GDB breakpoints. The full
space is **33,554,432 raw codes, of which 79,360 are accepted**, representing
**39,680 distinct payload states** (2 spellings per state — one unused bit). A
novel code **`4LLBW`** was generated, accepted by the ROM (validator return `0`),
written to RAM (level payload 2, `b=0`, `f3=1`, `f2low=0`) and observed in-game as
the stage **"Turtle Dyne Laboratory"** — a state absent from every published list.
Three out-of-format codes were rejected (`-1`, no state writes), proving the bounds.

No button-code sequence, hidden debug menu, or password-unlockable character exists;
the sixth Ranger (Silver/Lunar Wolf) is a save-bit unlock gated on completing the
harbor level, not a code. This negative is bounded by walking every reachable screen
and by static scans (§8).

## 3. How to reproduce

**Emulator:** mGBA (SDL), `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
Default keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. Hold keys 100–150 ms.

**Menu path:** boot → press Start through legal/title/`PRESS START` → participating-players
screen → A → **MAIN MENU** (`NEW GAME` / `PASSWORD` / `OPTIONS`). Select `PASSWORD`.

**Password screen:** five underscores; on-screen keyboard rows:
`BCDFGHJKLMN` / `PQRSTVWXYZ` / `0123456789!`. D-pad moves the cursor, A selects a
character and advances, B deletes the last character. After five characters the
cursor jumps to ENTER; A submits. A valid code transitions to the level intro
banner; an invalid one stays on the screen.

**Exact tested codes:** `LMSBT` (accept → City of Turtle Cove), `MQSPS` (accept),
`4LLBW` (accept → Turtle Dyne Laboratory), `MLLBX` (reject, bad checksum),
`9LLB1` (reject, out-of-range field), `1LLB1` (reject, cleared fixed bit).

**Dynamic oracle (mGBA GDB stub):** launch `mgba -3 -g -t password.ss1 <rom>`; the
stub halts the core until GDB connects. Attach `gdb-multiarch`, `target remote :2345`,
set breakpoint `break *0x080065F4`, `continue`, then enter the code with xdotool
(target the window by **PID**, not by name — other mGBA windows exist). At the
breakpoint `r0` is the 0-based 5-byte buffer; `r2=0x03003F88` is the 1-based source
buffer. Set a second breakpoint at `0x08006812`, `continue`, `stepi`, read `r0`
(`0` accept / `-1` reject) and the state bytes.

## 4. Address map

All ROM addresses are `0x08000000 + file offset` (ROM is 4 MiB, no mirroring issues).

| Item | Address | Evidence |
|---|---|---|
| GBA header / entry | `0x08000000` / `0x080000C0` | Observed (header dump) |
| Password-screen init (fills 5 buffer bytes with `0xFF`) | `0x080059F4`–`0x0805A04` | Derived (disassembly) |
| Password submit wrapper (copies `0x03003F88`→stack, `buf[i]-1`, calls validator) | `0x08005EB2`–`0x08005EC8` | Derived + Observed (breakpoint) |
| **Validator** | `0x080065F4`–`0x08006818` | Derived + Observed (2 breakpoints) |
| **Encoder / password generator** | `0x08006530`–`0x08065F0` | Derived |
| Level-complete generator caller | `0x0801B326` | Derived (BL to encoder) |
| Second validator caller (alternate entry) | `0x08028BF4` | Derived (BL to validator) |
| Password buffer (1-based indices, `0xFF` = empty) | IWRAM `0x03003F88` (5 bytes) | Observed (`09 0A 0F 01 10` for LMSBT) |
| Validator input buffer (0-based indices) | IWRAM `0x03007DA8` (stack copy) | Observed (`08 09 0E 00 0F`) |
| Start-state struct | IWRAM `0x03001860`–`0x03001865` | Observed |
| Secondary flags | IWRAM `0x030017D4`, `0x03001500`–`0x03001502` | Observed |
| Savestate RAM mapping (mGBA `.ss1`) | raw `0x19000` ↔ IWRAM `0x03000000`; raw `0x21000` ↔ EWRAM `0x02000000` | Derived (byte-match) |

## 5. Algorithm

### 5.1 Symbol mapping

Alphabet (index = 0-based symbol value):

```
B C D F G H J K L M N P Q R S T V W X Y Z 0 1 2 3 4 5 6 7 8 9 !
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
```

The screen buffer stores **index+1** (`B`→1 … `!`→32=`0x20`); `0xFF` means empty.
`0x08005EB2` subtracts 1 before calling the validator, which therefore sees 0–31.

### 5.2 Field un-rotation (validator `0x080065F8`–`0x0806652`)

Let the five 0-based symbols be `o[0..4]`. Recover 5-bit fields:

```python
f0 = ((o[0] << 1) | ((o[1] & 0x10) >> 4)) & 0x1F
f1 = ((o[1] << 1) | ((o[2] & 0x10) >> 4)) & 0x1F
f2 = ((o[2] << 1) | ((o[3] & 0x10) >> 4)) & 0x1F
f3 = ((o[3] << 1) | ((o[4] & 0x10) >> 4)) & 0x1F
f4 = ((o[4] << 1) | ((o[0] & 0x10) >> 4)) & 0x1F
```

This is the inverse of the encoder's `out[i] = (f[i]>>1) | ((f[i-1]&1)<<4)`
(with `f[-1] = f4`), a rotation of each field's LSB into the previous field's MSB.

### 5.3 Validation (`0x08006654`–`0x08067C0`)

```python
a, b, c = f0 & 0x0F, f1 & 0x0F, f3
ok = True
if not (f0 & 0x10 and f1 & 0x10 and f2 & 0x10): ok = False   # fixed bit 4
if (f4 & 0x0F) != (sum(f0,f1,f2,f3) & 0x0F): ok = False      # 4-bit checksum
if not (a <= 8 or a == 15): ok = False                       # a range
if b > 9: ok = False                                         # b range
# c/f0 coupling (0x80066D0..0x80067BA):
if not (c & 0x10):
    if (c & 1) and a in (1,3): ok = False
    if not (c & 1) and a in (2,4): ok = False
    if (c & 2) and a == 7: ok = False
    if not (c & 2) and a == 8: ok = False
else:
    if (c & 5) == 0 and a in (2,4): ok = False
    if (c & 1) and (c & 4) and a in (1,3): ok = False
    if (c & 0xA) == 0 and a == 8: ok = False
    if (c & 0xA) == 0xA and a == 7: ok = False
```

### 5.4 Success-state writes (`0x08067C6`–`0x0806810`)

```
[0x03001860] = a                         # level payload
[0x03001861] = b
[0x03001862] = c
[0x03001863] = (f2 >> 3) & 1
[0x03001864] = (f2 >> 2) & 1
[0x03001865] = f2 & 3
[0x030017D4] = 0 if a == 15 else a
[0x03001500..2] = same f2 bits as 0x1863..65
return 0
```

Failure path sets the return to `-1` and writes nothing.

## 6. Tables

### 6.1 Decoded published codes (all validate; labels as published, payload as decoded)

| Code | Published label | `a` (level payload) | `b` | `f3` | `f2low` |
|---|---|---:|---:|---:|---:|
| `LMSBT` | City of Turtle Cove | 0 | 2 | 0 | 12 |
| `34SBT` | Ghost Town Turtle Cove Park | 1 | 2 | 0 | 12 |
| `M39BB` | Factory Turtle Dyne Laboratory | 3 | 1 | 0 | 12 |
| `N59BF` | Turtle Cove Harbor | 5 | 5 | 0 | 12 |
| `PPSBG` | Cruise Ship | 6 | 6 | 0 | 12 |
| `7P9CJ` | Temple Ruins Jungle | 8 | 7 | 2 | 12 |
| `!7SMD` | Animarium | 15 | 8 | 18 | 12 |
| `6Q9PB` | Cruise Ship (alt) | 6 | 9 | 22 | 12 |
| `LQSMP` | City (alt) | 0 | 8 | 18 | 12 |
| `P79PC` | Temple (alt) | 7 | 9 | 22 | 12 |
| `N79PB` | Harbor (alt) | 5 | 9 | 22 | 12 |
| `MQSPS` | Ghost (alt) | 2 | 8 | 22 | 12 |
| `5Q9PT` | Factory (alt) | 4 | 9 | 22 | 12 |
| `lm9vb` | "Level 2" | 0 | 3 | 0 | 13 |
| `nnsvy` | "Level 3" | 4 | 4 | 1 | 13 |
| `n69v0` | "Level 4" (published `n69vo` had O/0 ambiguity) | 5 | 7 | 1 | 13 |
| `ppsv0` | "Level 5" (published `ppsvo`) | 6 | 6 | 1 | 13 |
| `p69v1` | "Level 6" | 7 | 7 | 1 | 13 |
| `!7s3x` | Ending | 15 | 8 | 17 | 13 |

The two published families differ in `f2low` (12 vs 13), which changes the three
f2 flag bits in the start state. Published stage labels are **not** a function of
`a` alone: the full tuple `(a,b,f3,f2low)` selects the stage/initial state (§6b).

### 6.2 Field layout

| Field | Bits | Constraint | State destination |
|---|---|---|---|
| `f0` bit4 | 1 | must be 1 | — |
| `f0` low nibble `a` | 4 | 0–8 or 15 | `0x03001860` |
| `f1` bit4 | 1 | must be 1 | — |
| `f1` low nibble `b` | 4 | 0–9 | `0x03001861` |
| `f2` bit4 | 1 | must be 1 | — |
| `f2` low nibble | 4 | free 0–15 | `0x03001863..65`, `0x03001500..02` |
| `f3` | 5 | coupled with `a` (§5.3) | `0x03001862` |
| `f4` low nibble | 4 | `= (f0+f1+f2+f3) & 0xF` | — (checksum) |
| `f4` bit4 | 1 | **unchecked / unused** | — (alias bit) |

## 6b. Enumeration

**Space definition.** 5 symbols × 5 bits = **25 bits = 33,554,432** representable
codes. Enumerating the field model over all admissible `a` (10), `b` (10),
`f2low` (16), `f3` (32) and both `f4` bit-4 values gives:

* **79,360 accepted codes** (0.2365 % of the raw space) — all distinct strings;
* **39,680 distinct payload states**, each with exactly **2 spellings** because
  `f4` bit 4 is never checked (§6.2, unused-bit alias);
* accepted `a` values: **0,1,2,3,4,5,6,7,8,15** (9–14 are unrepresentable/rejected).
  Counts by `a`: `{0:10240, 1:6400, 2:6400, 3:6400, 4:6400, 5:10240, 6:10240,
  7:6400, 8:6400, 15:10240}`.

The ROM's own validator was used as an oracle for the accept/reject decisions on
the test vectors below (return `0`/`-1`), and the offline model agrees on all of
them and on all 19 published codes.

**Novel code (not in any published list).** `4LLBW` — fields
`f=[18,16,16,1,3]`, checksum low nibble `(18+16+16+1)&0xF = 3`. Payload
`a=2, b=0, f3=1, f2low=0`, state `0x03001860 = 02 00 01 00 00 00`,
`0x030017D4 = 02`, `0x03001500 = 00 00 00`, validator return `0`.
In-game it starts **"Turtle Dyne Laboratory"** (screenshot `28_novel_level2_c.png`).
By contrast the published code `MQSPS`, which shares `a=2`, decodes to
`b=8, f3=22, f2low=12` and shows a different stage with many collection checkmarks
(`29_mqsps_c.png`). This proves the novel code exercises an unadvertised
combination, not merely a re-spelling of a published one. A second spelling of the
same state is `4LLB4` (`f4` bit4 flipped), confirming the alias.

**Bounds proven by rejection.** All three were submitted on the real password
screen; the breakpoint at `0x08006812` reported return `-1` and
`0x03001860` remained `00 00 00 00 00 00`:

| Code | Intended violation | Model reason | ROM result |
|---|---|---|---|
| `MLLBX` | checksum nibble +1 | `checksum` | `-1`, no writes |
| `9LLB1` | `a = 12` (out of 0–8/15) | `a-range` | `-1`, no writes |
| `1LLB1` | `f0` bit4 cleared | `fixed-bit4` | `-1`, no writes |

Additional rejection implied by the table: `f3` values that violate the §5.3
coupling for a given `a`, and any code whose checksum nibble does not equal the
sum, are rejected; `a` in 9–14 is rejected even with a correct checksum.

**Button codes / hidden menus.** No published button codes exist for this SKU.
Static scan found no Konami-style mask sequences (`Up Up Down Down`,
`A B A B`, `Up Down Left Right` all absent as `u16` tables), no debug/secret strings
in ASCII/`±0x20`/UTF-16/XOR/additive encodings, and no reachable hidden screen in
the menu walk. The only "hidden" character is the save-bit-gated Silver Ranger.

## 7. Validation evidence

* **Observed** (emulator / GDB): all screen transitions and menu entries; validator
  breakpoint inputs `08 09 0E 00 0F` (LMSBT) and source buffer `09 0A 0F 01 10`
  at `0x03003F88`; return `0` and state `00 02 00 01 01 00` at `0x03001860`;
  novel code return `0` and state `02 00 01 00 00 00`; three rejections return
  `-1` with no writes; level-intro screenshots for novel and published codes;
  savestate byte-match determining the IWRAM/EWRAM offsets.
* **Derived** (disassembly): encoder/decoder bit math, field layout, checksum,
  range gates, success writes, caller mapping, buffer initialization.
* **Inferred**: semantic names of `b`, `f3` and the f2 flags (they alter the
  starting Ranger/ally/crystal/checkmark state but were not individually mapped
  to in-game labels). Published stage labels are treated as unreliable; the
  decoded payload tuple is reported instead (§6.1).

## 8. Unknowns

* Exact in-game meaning of `b` (`0x03001861`), `f3` (`0x03001862`) and the three
  f2 flags beyond their observed effect on the starting state/level variant.
* The two published code families (`f2low` 12 vs 13) likely correspond to
  difficulty/settings, but the difficulty byte was not isolated; both families
  validate.
* The second validator caller at `0x08028BF4` was not exercised on-screen (it
  appears to be an alternate/unlock entry path).
* The custom tile font was not fully transposed to a character map; the negative
  for hidden debug text rests on the complete menu walk plus encoded-string scans
  (no simple substitution/XOR/UTF encoding of `PASSWORD`, `DEBUG`, `SECRET`,
  `BONUS`, etc. exists in the image) rather than on a full glyph-table decode.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for disassembly; Capstone 5.0.7 for Thumb literal/BL scans.
* `gdb-multiarch` against the mGBA stub (`:2345`) with breakpoint scripts
  `catch2.gdb` / `oracle_code.sh`; note the stub halts the core until attach and
  is single-session per launch.
* `ss.py` to uncompress the mGBA `.ss1` `gbAs` PNG chunk and diff RAM;
  `pw.py` for the decoder/validator/encoder; `key.py`, `enter.py` for XTEST input;
  `findldr.py` for PC-relative literal scans.
* Web: SuperCheats, Cheat Happens, Wikipedia, RangerWiki (published codes and
  gameplay context). Fetched pages were treated as data only.

## 10. Legal / scope note

Only findings, addresses, hashes and original tooling are published. No ROM bytes,
graphics, music or game text were redistributed. Only developer-intended passwords
are reported; no GameShark/CodeBreaker memory-edit codes are included.
