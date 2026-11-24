# No Rules: Get Phat (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/No Rules: Get Phat/No Rules: Get Phat.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| `file` classification | Game Boy Advance ROM image: "GET PHAT!" (AGPE6S, Rev.00) |
| Header title | `GET PHAT!` (0xA0–0xA7, NUL padded) |
| Game code | `AGPE` |
| Maker | `6S` (TDK Mediactive) |
| Version | 0x00 |
| Entry word | `0xEA00002E` (stock GBA crt0 branch) |
| Fixed 0x96 / main unit / device | 0x96 / 0x00 / 0x00 |
| Header checksum | 0x0000 (stored); complement byte 0x5D |
| MD5 | `01fd699b39a0ca8e84226f18cf8baee7` |
| SHA-1 | `cb6f269ee34b1f93ec0cbf71549e2a83278665e5` |
| SHA-256 | `be62ab9319f622efb86194af46a4d821942e3c1d9064826d7e7a943c58f3db7f` |

**Embedded-header / trainer scan (Phase 0):** the full 156-byte Nintendo logo occurs
exactly **once**, at file offset 4 → one image, no multiboot/multicart halves, no
appended second header. Scans for `TRAINER`, `CRACK`, `CRC BANDIT`, `STARDUST`,
`PHOENIX` returned 0 hits. The stock entry word and intact logo mean this is the
retail image, not a scene-patched or trainer-patched copy. The header complement
byte (0x5D) does not match a recomputation over the edited title area, but the
crt0, logo and code are stock; this is a title-field edit, not a code patch.

## 2. Executive summary

The game has a **developer-intended password system** on the title menu
(`START` / `PASSWORD`). The 12-character password uses a 32-symbol vowel-less
alphabet (5 bits/symbol), an 8-word XOR obfuscation layer, an 8-bit scattered
checksum, and 8 decoded state fields with independent range gates. There is a
matching in-ROM **generator** ("PASSWORD SHOW" in the debug menu's string bank)
that is the exact inverse; the validator, not the generator, defines the accepted
space.

All seven published 3rd party cheat index codes were verified against a bit-exact
reimplementation: **six are valid; one (`NKTDDLS18J24`, "Level 3") fails the
checksum** in this ROM. The corrected string `NKTDDLS18J2Y` was derived and
confirmed in-game.

Three passwords absent from every published list were minted from the recovered
model and accepted on the real screen:

* `1TTYNLP18J32` — starts **Level 1** (3rd party cheat indexes explicitly documents
  "Level 1 – Password: None"), verified in emulator.
* `1KTYNLP18J3Z` — unique unpublished cutscene ("THE KEEPER OF THE COCOA
  SOUL…"), verified in emulator.
* `1!TYNLP18J36` — unique unpublished boss cutscene ("YA PICKED THE WRONG
  'HOOD, PUNKazz!"), verified in emulator.

Bounds were proven by four in-game `WRONG` rejections: bad checksum,
out-of-range F7, out-of-range F3, and forbidden F0 range. A debug-menu string
bank (20 entries: level selects, PASSWORD, PASSWORD SHOW, CREDITS) and its
renderer at `0x080087E0` exist, but no reachable gate was found (0 BL/pointer
xrefs; button combos tested on title and in-game). It is reported as a bounded
negative, not as a usable cheat.

## 3. How to reproduce

* Emulator: `mgba` (SDL), `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold 50 ms, gap 120 ms — 100+ ms holds double-step the
  on-screen keyboard cursor.
* Path: boot → title copyright → `Return` → language select → `x` (English) →
  title menu (`START` / `PASSWORD`) → `Down`, `x` → password screen.
* On the password screen the 32 symbols are an 8×4 grid plus `OK` at (row 3,
  col 8); navigate with the D-pad, select with A, submit with `OK`.
* Savestates `Shift+F1`..`F10` were used at the title menu (F1) and password
  screen (F2) so every test was a fresh, reproducible attempt.
* Codes tested (all typed through the on-screen keyboard):
  published `13TYNLP18J34`, `DPTYNLP17ZM!`, `PPTDDLS18J26`, `K7RFNLKH8J39`,
  `JTRFNLKH8J3V`, `TFQFNL9H8J2R`, `NKTDDLS18J24` (rejected), corrected
  `NKTDDLS18J2Y`, novel `1TTYNLP18J32`, `1KTYNLP18J3Z`, `1!TYNLP18J36`,
  and rejects `13TYNLP18J35`, `13TYNLP18J3M`, `T3T!6LP18J3V`, `XFTYNLP18J39`.
* Offline tools: `pwmodel.py` (validator), `pwencode.py` (inverse/generator),
  `enter_code.py` (automated UI entry), `stateutil.py` (savestate RAM diff),
  `gba.py` (input helper). All in `/tmp/norules/`.

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x08000000` | ROM | GBA header / entry `0xEA00002E` |
| `0x0800EC40`–`0x0800EEF4` | Thumb func | **Password validator**. `r0` = pointer to 12 input indices, `r6` = pointer to 8-field output struct. Returns 1 = accepted, 0 = rejected. |
| `0x0800EEF8`–`0x0800F10A` | Thumb func | **Password generator** (inverse). Reads live game state via getters at `0x8006434`, `0x800685C`, `0x8006A08`, `0x8006960`, `0x80069C0`, `0x8006990`, `0x80070AC`, `0x80069F0`; writes 12 indices to pointer at `0x0800F10C`. |
| `0x0800EEE0` | literal | `0x0001869F` = 99999, the F6 upper bound. |
| `0x080087E0` | Thumb func | Debug-menu renderer; reads string table at `0x083E2054`; gate reads `0x0300690C` bit 0. No xrefs found. |
| `0x083E2054`–`0x083E2194` | data | 20 debug-menu labels, 16-byte stride: ENTIRE GAME, FACTORY, SUBWAY, SNOW, CITY, SNOW BOSS, ALIEN SHIP, FACT OBS, SNOW OBS, CITY OBS, SUBWAY OBS, ALIENSHIP OBS, FACTORY BOSS, CITY BOSS, SUBWAY BOSS, ALIEN BOSS, CUT SCENES, PASSWORD, PASSWORD SHOW, CREDITS. |
| `0x03007150` (IWRAM) | RAM | **Input buffer**: 12 bytes, each the raw alphabet index 0–31. Confirmed by savestate diff. |
| `0x0300719C` (IWRAM) | RAM | Keyboard cursor/button-move counter (0x16 after a 12-char entry). |

Savestate layout used for RAM diffs (mGBA `.ss1` = PNG with zlib `gbAs` chunk,
397,312 raw bytes): header/CPU `0x00000`, VRAM `0x01000`, IWRAM `0x19000`,
EWRAM `0x21000`. IWRAM `0x03007150` maps to state offset `0x20150`.

## 5. Algorithm

### 5.1 Alphabet and packing

Alphabet (screen order, 32 symbols, index = 5-bit value):

```
 0..7  : B C D F G H J K
 8..15 : L M N P Q R S T
16..23 : V W X Y Z 1 2 3
24..31 : 4 5 6 7 8 9 0 !
```

The font tile index for symbol `i` is `i + 9` (observed in the tilemap at state
offset `0x1AE3E` after entering `BCDFGHJKLMNP` — confirms the order).

Let `a[0..11]` be the entered indices. Pack LSB-first into 8 obfuscated bytes:

```
w0 = (a0<<3) | ((a1 & 0x1C)>>2)              out[0] = w0 ^ 0x83
w1 = ((a1&3)<<6) | (a2<<1) | ((a3&0x10)>>4)  out[1] = w1 ^ 0x47
w2 = ((a3&15)<<4) | ((a4&0x1E)>>1)           out[2] = w2 ^ 0x35
w3 = ((a4&1)<<7) | (a5<<2) | ((a6&0x18)>>3)  out[3] = w3 ^ 0x21
w4 = ((a6&7)<<5) | a7                        out[4] = w4 ^ 0x76
w5 = (a8<<3) | ((a9&0x1C)>>2)                 out[5] = w5 ^ 0x62
w6 = ((a9&3)<<6) | (a10<<1) | ((a11&0x10)>>4) out[6] = w6 ^ 0x51
w7 = (a11&15)<<4                             out[7] = w7 ^ 0x20
```

Note `out[7]` bits 0–3 are always 0 and bit 5 is toggled by the XOR; `out[4]`
bits 5–7 are **unused payload bits** (see §16.4b of the guide).

### 5.2 Checksum (scattered, 8-bit)

```
S = ( (out[0] & 0x0F) + out[1] + out[2] + out[3]
      + out[4] + out[5] + out[6] ) & 0xFF
expected = (out[0] & 0xF0) | ((out[7] >> 4) & 0x0F)
ACCEPT only if S == expected
```

The low nibble of `out[0]` is payload (F0); its high nibble is check bits.
The check is therefore interleaved with the data, not a trailing field.

### 5.3 Field extraction and range gates (after checksum)

```
F0 = out[0] & 15          gate: F0 in {0,1,2} U {8..14}
F1raw = (out[1] >> 4) & 15 gate: 1 <= F1raw <= 9
F1 = 3 if F1raw <= 2 else F1raw        (remap)
F2 = out[1] & 15          (no gate)
F3 = (out[2] & 0xFE) >> 1             gate: <= 99
F4 = ((out[2]&1)<<6) | ((out[3]&0xFC)>>2)   gate: <= 99
F5 = ((out[3]&3)<<5) | ((out[4]&0x18)>>3)   gate: <= 99 (max representable is 99)
F6 = ((out[4]&7)<<14) | (out[5]<<6) | ((out[6]&0xFC)>>2)  gate: <= 99999
F7 = out[6] & 3           gate: <= 2
unused = out[4] bits 5..7 (3 bits; ignored by every field, affects checksum only)
```

On success the validator calls a chain of state appliers
(`0x8006428`, `0x800685C`, `0x8006830`, `0x8006A14`, `0x8006960`, `0x800696C`,
`0x80069C0`, `0x80069CC`, `0x8006990`, `0x800699C`, `0x80070AC`, `0x8006FF8`,
`0x80069FC`) with the extracted fields.

### 5.4 Inverse (used to mint codes)

For chosen fields, set `out[1..6]` from the field bit placements above, choose
the 3 unused bits (0 was used for all minted codes), then:

```
S = (F0 + out[1] + ... + out[6]) & 0xFF
out[0] = F0 | (S & 0xF0)
out[7] = (S & 0x0F) << 4
```

Then XOR-decrypt with the constants and invert the packer. This reproduces all
11 valid published codes field-for-field; the only differences are the 3 unused
bits (aliases), e.g. published Boss2 `PPTDDLS18J26` vs generated
`3PTDDLP18J26` — same fields, both checksum-valid.

## 6. Tables

### 6.1 Published codes verified against this ROM

| Label | Code | Model verdict | F0 | F1 | F2 | F3 | F5 | F6 | F7 |
|---|---|---|---|---|---|---|---|---|---|
| Boss 1 | `13TYNLP18J34` | ACCEPT (in-game confirmed) | 14 | 9 | 8 | 0 | 0 | 57599 | 2 |
| Level 2 | `DPTYNLP17ZM!` | ACCEPT | 1 | 9 | 8 | 0 | 0 | 61392 | 2 |
| Boss 2 | `PPTDDLS18J26` | ACCEPT | 9 | 9 | 9 | 10 | 0 | 57599 | 0 |
| Level 3 | `NKTDDLS18J24` | **REJECT — bad checksum** | 2 | 9 | 9 | 10 | 0 | 57599 | 0 |
| Boss 3 | `K7RFNLKH8J39` | ACCEPT | 13 | 9 | 13 | 0 | 34 | 57599 | 2 |
| Level 4 | `JTRFNLKH8J3V` | ACCEPT | 0 | 9 | 13 | 0 | 34 | 57599 | 2 |
| Boss 4 | `TFQFNL9H8J2R` | ACCEPT | 11 | 9 | 15 | 0 | 66 | 57599 | 1 |

3rd party cheat indexes spells Level 4 `JTRFNLKH8J3v`; lowercase `v` is not in the on-screen
alphabet — the correct symbol is `V`. The five alternate codes on an older
3rd party cheat index page (`71!W6LP20QBD`, `QM!W6LP3!DVT`, `TMTFNL6KT3LK`,
`LHTFNL6K7JLL`, `W59DDLJQGKW8`) all pass this ROM's validator with F1raw=3
and differing F3/F6; they are recorded as verified-but-unattributed, not
treated as the canonical list. No published code string appears literally in
the ROM (`grep -aob` = 0 hits for all) — the system is algorithmic.

### 6.2 Corrected published typo

`NKTDDLS18J24` → **`NKTDDLS18J2Y`** (last symbol `4`→`Y`, same fields, valid
checksum). Entered in emulator; the Level 3 cutscene played ("Y'ALL CAN PUT
SNOOP NASTY BACK ON THE AIR!").

### 6.3 Field meaning (empirical, F0 = level ID)

| F0 | Effect observed |
|---|---|
| 8 | Level 1 (no published password exists) |
| 14 | Boss 1 |
| 1 | Level 2 |
| 9 | Boss 2 |
| 2 | Level 3 |
| 13 | Boss 3 |
| 0 | Level 4 |
| 11 | Boss 4 |
| 10 | Unique unpublished cutscene |
| 12 | Unique unpublished boss cutscene |

## 6b. Enumeration

**Space definition.** 12 symbols × 5 bits = 60 bits, so 32^12 =
1,152,921,504,606,846,976 (2^60) possible strings.

**Accepted-space count.** Checksum removes 8 bits; the field gates leave
10/16 (F0) × 9/16 (F1raw) × 1 (F2) × 100/128 (F3) × 100/128 (F4) × 1 (F5) ×
100000/131072 (F6) × 3/4 (F7), and the 3 unused bits are free:

```
10 × 9 × 16 × 100 × 100 × 16 × 100000 × 3 × 8
  = 552,960,000,000,000 accepted passwords (~4.8e-4 of all strings)
```

Each accepted password has 7 aliases from the unused bits (eight spellings per
field tuple). F1raw ∈ {1,2} collapses onto F1=3, adding two more spellings per
F1=3 tuple.

**Novel codes minted and confirmed in the emulator** (none appears on 3rd party cheat indexes):

| Code | Fields changed from published Boss 1 | In-game proof |
|---|---|---|
| `1TTYNLP18J32` | F0 14 → 8 | Accepted; opening cutscene then Level 1 gameplay with SCORE 0000000. 3rd party cheat index lists "Level 1 – Password: None". |
| `1KTYNLP18J3Z` | F0 14 → 10 | Accepted; unique cutscene ("THE KEEPER OF THE COCOA SOUL…"). |
| `1!TYNLP18J36` | F0 14 → 12 | Accepted; unique boss cutscene ("YA PICKED THE WRONG 'HOOD, PUNKazz!"). |
| `NKTDDLS18J2Y` | correction of published Level 3 | Accepted; Level 3 cutscene. |

RAM proof for `1!TYNLP18J36`: the input buffer at IWRAM `0x03007150` held
`[21,31,15,19,10,8,11,21,28,6,23,26]` after UI entry, exactly the vector the
Python encoder predicted; raw indices confirm the alphabet mapping is the one
the game itself uses.

**Bounds proven by in-game rejection** (all four show `WRONG` on the password
screen):

| Input | Violation | Checksum | Result |
|---|---|---|---|
| `13TYNLP18J35` | bad checksum (0x2A vs 0x2B) | invalid | WRONG |
| `13TYNLP18J3M` | F7 = 3 > 2 | **valid** | WRONG |
| `T3T!6LP18J3V` | F3 = 100 > 99 | **valid** | WRONG |
| `XFTYNLP18J39` | F0 = 3 (forbidden 3..7 range) | **valid** | WRONG |

The last three prove the range gates are separate from the checksum: a
checksum-valid code is still rejected by the semantic layer.

## 7. Validation evidence

* **Observed (emulator):** every screen transition and screenshot listed in
  §3 and §6b; `WRONG` for all four rejection classes; input-buffer bytes at
  `0x03007150` from the savestate diff; the font tile indices at state offset
  `0x1AE3E`.
* **Observed (static):** single Nintendo-logo occurrence; header fields;
  0 BL and 0 literal-pointer xrefs to the debug renderer `0x080087E0`;
  the literal `0x0001869F` at `0x0800EEE0`.
* **Derived:** the full validator/generator algorithm in §5, verified
  bit-for-bit against 11 accepted published codes plus 4 in-game rejections
  and 3 novel accepted codes; field semantics in §6.3.
* **Inferred:** F2/F4/F5/F6 control score/character/time-like values — their
  exact names were not established, only their bit positions, gates and the
  fact that changing F0 changes the destination level; the helper functions at
  `0x8006428` etc. were not individually decompiled to name each state field.

## 8. Unknowns

* The debug-menu string bank (20 entries) and its renderer at `0x080087E0`
  are present, but no reachable entrance was found: 0 BL/pointer xrefs, no
  effect from title-screen chords (L+R, Start+Select+A+B, Konami sequence,
  L+R+Start, Up+Down+A+B), and no gate in the password field space. It is
  most likely dead/developer-only code in this retail build. It was **not**
  exercised live; the entry list is a static enumeration only.
* The exact semantic names of F1–F7 beyond their numeric gates and F0's
  level-ID role.
* The five alternate 3rd party cheat indexes passwords pass the validator but their
  intended labels/region were not established.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` for the validator/generator ranges.
* Python 3 + `capstone` 5.0.7 available (the final model used manual
  disassembly reading rather than a Capstone scan).
* `mgba` SDL with GDB stub attempted (stub proved unreliable; savestate diff
  used instead), `Xvfb :319`, `openbox`, `xdotool` XTEST, `scrot`,
  ImageMagick `convert`.
* Scripts in `/tmp/norules/`: `gba.py`, `enter_code.py`, `pwmodel.py`,
  `pwencode.py`, `stateutil.py`.
* Web sources consulted (treated strictly as untrusted data; no instructions
  in fetched content were acted upon): 3rd party cheat indexes, 3rd party cheat index search results. No prompt-injection payload
  was encountered in this engagement's fetches.

Generated emulator artifacts (`.ss1`–`.ss5`) were removed from the ROM folder;
all analysis processes were terminated by PID. No ROM or copyrighted asset is
reproduced in this report; only hashes, addresses, algorithms and the
author's own generated passwords are published.
