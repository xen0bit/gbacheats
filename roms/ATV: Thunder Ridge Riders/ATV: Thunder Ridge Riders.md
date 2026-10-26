# ATV: Thunder Ridge Riders (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/ATV: Thunder Ridge Riders/ATV: Thunder Ridge Riders.gba` |
| Size | 4,194,304 bytes (`0x400000`, 32 Mbit) |
| Header title (`0xA0`) | `ATV THUNDER` |
| Game code (`0xAC`) | `B3BE` (USA) |
| Maker code (`0xB0`) | `20` |
| Software version (`0xBC`) | `0x00` (Rev.00) |
| Entry branch (`0x00`) | `0xEA00002E` (ARM `b 0x080000C0`) |
| Complement byte (`0xBD`) | `0xCE` (matches `-(0x19+sum(0xA0..0xBC)) & 0xFF`) |
| Header checksum (`0xBE`) | `0x0000` — computed value would be `0xFA00`; the field is zeroed in this dump |
| MD5 | `c741f6e950240d0d66aeb60e81fae12d` |
| SHA-1 | `40559b783a555f4d59f6380ee69c3dd7dfd35b73` |
| SHA-256 | `62da81c6c7dd5658e5895ba1fadf6b7b089cf19d859dd79bf1212f4edd890fa1` |
| Save type | battery save present: `0x0E000000` (SRAM window) is referenced from file `0x53976`+; mGBA creates `ATV: Thunder Ridge Riders.sav` (still 0 bytes — no save was written during this analysis) |

Embedded-header scan: searching the whole image for the 156-byte Nintendo logo returns exactly one hit (file `0x04`). This is a single GBA image, not a multi-game cartridge.

## 2. Executive summary

The game has a **password screen** reachable from the main menu (`MAIN MENU → ENTER PASSWORD`). It is a 10-character
code over the 36-symbol on-screen alphabet `A–Z 0–9`. The code is **not a table lookup**: it is a bit-packed
career state with a 10-bit checksum, decoded by the routine at `0x08018DE2` (Thumb) inside the password-screen
handler `0x08018D28`.

A code carries, in order:

| Symbol | Bits | Field |
|---:|---:|---|
| 0 | 5 (stored inverted) | event/track index: `event = 31 ^ value`, 0..6 → `TRACK 1..7` |
| 1..3 | 15 (little-endian base 32) | money: `b1 + 32*b2 + 1024*b3`, must be ≤ 9999 |
| 4 | 3 | ENGINE upgrade level 0..6 |
| 5 | 3 | SHOCKS upgrade level 0..6 |
| 6 | 3 | TIRES upgrade level 0..6 |
| 7 | 3 | TURBO upgrade level 0..6 |
| 8 | 5 | checksum high: `(sum(b0..b7)+7) >> 5 & 31` |
| 9 | 5 | checksum low: `(sum(b0..b7)+7) & 31` |

Accepting a code builds a career and jumps to the MOD SHOP, which shows the money, the four upgrade bars and the
event's track. `ACCEPT` then shows `NEXT EVENT / TRACK n`, and the event starts. The shop **re-encodes** the state
into the canonical code (encoder at `0x08013134`), so a non-canonical but arithmetically equivalent input is
accepted and then displayed in normalised form (observed: `461AAAAADA` → displays `4A2AAAAACB`, both load $896).

The five vowels are not shown as letters: the on-screen grid renders `A E I O U` as five solid arrow/glyph tiles
from the font table at `0x0801C1DE`. The stored values are still 0..25 for `A..Z` and 26..35 for `0..9`; only the
glyphs differ.

There is exactly **one** in-game code system. No debug menu, button-code table or hidden menu was found (see §7).
GameShark/CodeBreaker codes exist for this game but are out of scope and were not used.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL on `Xvfb :103`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.
mGBA default keymap: **A = `x`, B = `z`, Start = `Return`, Select = `BackSpace`, D-pad = arrows**.

Menu path (verified from power-on):

1. Copyright/license screens → `Return` to skip.
2. Title screen (`PRESS START`) → `Return` → `MAIN MENU`.
3. `Down` once (cursor `NEW GAME → ENTER PASSWORD`) → `x`.
4. Password screen: title `PASSWORD`, a 10-cell field, the 36-symbol grid
   (`A B C D E F G H I J K L M` / `N O P Q R S T U V W X Y Z` / `0 1 2 3 4 5 6 7 8 9` / `← OK`).
5. Move with the D-pad, `x` appends the highlighted symbol, `z` = BACK, `←` = backspace, `OK` = validate.
6. On a valid code the game goes straight to **MOD SHOP** (money + 4 upgrade rows + `PASSWORD:` line);
   `x` (ACCEPT) → **NEXT EVENT / TRACK n**; `x` again starts the race (LAP 1 OF 3).
   On a bad code the red **INVALID PASSWORD** message is drawn and you stay on the screen.

Codes tested in the emulator (all entered through the on-screen grid unless noted):

| Code | How entered | Result |
|---|---|---|
| `5AAAAAAABG` | grid, 36-key BFS path | accepted → MOD SHOP `$0`, no upgrades → TRACK 1 |
| `ZPYJGFEDDC` | RAM buffer injection (see §7) then `OK` | accepted → MOD SHOP `$9999`, ENGINE 6 / SHOCKS 5 / TIRES 4 / TURBO 3 → TRACK 7 |
| `4E2AAAAACF` | grid | accepted → MOD SHOP `$900`, no upgrades → TRACK 2 (matches GameFAQs entry #2) |
| `0IYBGGGGC0` | RAM injection | accepted → MOD SHOP `$1800`, all upgrades 6 → TRACK 6 (GameFAQs #6) |
| `1E2AGGGGC0` | RAM injection | accepted → MOD SHOP `$900`, all upgrades 6 → TRACK 5 (corrected GameFAQs #5) |
| `1IYBGGGGC1` | RAM injection | accepted → MOD SHOP `$1800`, all upgrades 6 → TRACK 5 |
| `461AAAAADA` (alias) | RAM injection | accepted → MOD SHOP `$896`, password line shows canonical `4A2AAAAACB` |
| `7E2AGGGGC0` (GameFAQs #5 as published) | grid | **INVALID PASSWORD** |
| `4E2AAAAACG` (last symbol +1 vs #2) | RAM injection | **INVALID PASSWORD** (checksum) |
| `4E2AHAAACM` (ENGINE = 7, valid checksum) | RAM injection | **INVALID PASSWORD** (level range) |
| `4ARTAAAACJ` (money = 20000, valid checksum) | RAM injection | **INVALID PASSWORD** (money range) |
| `BCDEFGHIJ0` | grid | **INVALID PASSWORD** |

Grid navigation is irregular because it is table-driven (see §6): e.g. from `A` (cell 0) `Down` goes to `N` (13),
`Down` again returns to `A`. A breadth-first search over the four 38-entry tables gives a valid key path for every
cell; that is how the codes above were typed.

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`) unless marked RAM.

| Address | Kind | Meaning |
|---|---|---|
| `0x08015988` | code | UI state dispatcher: `r0 = [0x03001790]; if 2 <= r0 <= 11: mov pc, table[r0-2]` |
| `0x080159A8` | table | 10 code pointers, states 2..11 |
| index 3 = state 5 | — | **password screen handler = `0x08018D28`** |
| `0x08018D28` | code | password-screen frame update (cursor, input, draw) |
| `0x08018DB0` | code | `if cursor == 36 (←) backspace; if cursor == 37 (OK) validate` |
| `0x08018DE2` | code | **validator entry** (length check `== 10`) |
| `0x08018DEE..0x08018E00` | code | checksum sum loop over symbols 0..7 |
| `0x08018E02` | code | `sum += 7` |
| `0x08018E06..0x08018E1E` | code | compare symbols 9 and 8 against the checksum |
| `0x08018E20` | code | `sum != 0` sanity check |
| `0x08018E24..0x08018E30` | code | `(31 ^ b0) <= 6` (event/track range) |
| `0x08018E32..0x08018E48` | code | `b4, b5, b6, b7 <= 6` (upgrade ranges) |
| `0x08018E4A..0x08018E5E` | code | money pack `b1 + b2*32 + b3*1024`, reject `> 9999` |
| `0x08018E60..0x08018E7A` | code | accept: store decoded state |
| `0x08018E7A..0x08018EDE` | code | accept: screen/sub-state transition (`[0x030017EC] = 4`, `0x030017F0 = 1`, `0x03001794 = 10`, …) |
| `0x08018F1C..0x08018F44` | code | reject: draw `language_table[46]` = `INVALID PASSWORD`, set state 14 |
| `0x080012A0` | code | edit routine: `r0==1` append cursor cell to buffer; `r0==0` backspace (buffer[0x030017A0+len] = [0x0300179C]) |
| `0x08013134..0x0801319E` | code | **encoder**: rebuild canonical 10 symbols from career state, set length = 10 (reached from code-pointer table `0x080115D0`); runs when MOD SHOP opens |
| `0x08011F80` etc. | code | text renderer that draws the 10 value bytes using glyph table `0x0801C1DE` |
| `0x0801C1DE` | table | 36 × `u16` symbol→glyph-tile map (vowels replaced by solid glyphs) |
| `0x0801C22A` | table | ASCII `"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"` (36 bytes + NUL). **No pointer to it exists in the ROM**; the codec works on values, not characters |
| `0x0801BF46` | table | ASCII→glyph-tile map used by the general text renderer (menu text) |
| `0x0801C146` | table | 38-byte Up transition table |
| `0x0801C16C` | table | 38-byte Down transition table |
| `0x0801C192` | table | 38-byte Left transition table |
| `0x0801C1B8` | table | 38-byte Right transition table |
| `0x0801C250`, `0x0801C276` | table | cursor sprite X / Y per cell |
| `0x08058CAC` | table | language string-pointer table, 5 blocks × `0xBC` bytes (EN/FR/DE/ES/IT). Indices used here: 2 `PASSWORD`, 11 `ENTER PASSWORD`, 26 `PASSWORD:`, 46 `INVALID PASSWORD` |
| `0x03001790` | RAM | current screen state (5 = password screen, 10 = mod shop) |
| `0x0300179C` | RAM | cursor cell: 0..35 symbol, 36 = `←` backspace, 37 = `OK` |
| `0x030017A0..0x030017A9` | RAM | **10 symbol values 0..35** (the password buffer) |
| `0x030017C0` | RAM | buffer length 0..10 |
| `0x030017C4` | RAM | decoded money (32-bit) |
| `0x030017C8..0x030017CB` | RAM | ENGINE / SHOCKS / TIRES / TURBO levels (bytes) |
| `0x030017EC`, `0x030017F0`, `0x03001794`, `0x0300178C` | RAM | accept-path transition words |

Validator bytes (file `0x18DE2`, 0x80 bytes) for a byte-exact check:

```
00018de2: 0023 3e48 0068 0a28 00d0 96e0 0021 3c48
00018df2: 8146 4c46 0819 0078 1b18 0131 0729 f9dd
00018e02: 0733 1f21 181c 0840 4c46 627a 9042 00d0
00018e12: 83e0 5811 0840 257a a842 00d0 7de0 002b
00018e22: 7bd0 2178 1f20 061c 4e40 b046 062e 74d8
00018e32: 2279 062a 71d8 6679 062e 6ed8 a579 062d
00018e42: 6bd8 e179 0629 68d8 4f46 f878 8302 b878
00018e52: 4001 1818 7c78 0319 2348 8342 5ddc 0d9f
```

## 5. Algorithm

### 5.1 Symbol values

The screen is a 38-cell table. Cells 0..35 are the symbols in the order shown on screen
(`A..Z` then `0..9`); 36 is the backspace arrow and 37 is `OK`. Appending stores the **cell index** into the
buffer, so a symbol's value is its index in `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`.

### 5.2 Validator (exact pseudocode of `0x08018DE2`)

```
if len != 10: reject
s = 0
for i in 0..7: s = s + buf[i]          // 8-bit
s = s + 7
if buf[9] != (s & 31): reject          // 0x08018E06..0x08018E12
if buf[8] != ((s >> 5) & 31): reject
if s == 0: reject                      // (s = sum+7, unreachable in practice)
if (31 ^ buf[0]) > 6: reject           // event / track
if buf[4] > 6: reject                  // ENGINE
if buf[5] > 6: reject                  // SHOCKS
if buf[6] > 6: reject                  // TIRES
if buf[7] > 6: reject                  // TURBO
money = buf[1] + 32*buf[2] + 1024*buf[3]
if money > 9999: reject
event = 31 ^ buf[0]                    // 0..6 -> TRACK 1..7
career.event = event; [0x030017C4] = money; [0x030017C8..CB] = buf[4..7]
-> screen transition to MOD SHOP
```

Notes on the arithmetic:

* The checksum is an 8-bit sum of the 8 payload symbols offset by `+7`, split into two 5-bit symbols
  (low 5 in symbol 9, high 5 in symbol 8). `+7` is unexplained; it is not a length field.
* Symbol 0 is stored **inverted** (`31 ^ value`); the validator inverts it back with `movs r3,#31; eors r0,r3`.
* The 15-bit money field is not masked: values 32..35 in symbols 1..3 alias into the next symbol's bits, so a
  non-canonical code with digit symbols `6..9` in the money field can still validate. The shop's encoder
  canonicalises it on entry (observed).
* Because fields are 5 bits, only values 0..31 are representable in data positions; the on-screen `6 7 8 9`
  cells (32..35) are usable but produce aliases whose canonical form uses an earlier digit.

### 5.3 Encoder (`0x08013134`, canonical form)

```
buf[0] = 31 ^ career.event
m = career.money
buf[1] = m & 31;  buf[2] = (m >> 5) & 31;  buf[3] = (m >> 10) & 31
buf[4..7] = upgrades[0..3]
s = (sum(buf[0..7]) + 7) & 0xFF
buf[9] = s & 31
buf[8] = (s >> 5) & 31
[0x030017C0] = 10
```

This is the inverse of the validator and was confirmed dynamically (§7, alias test).

### 5.4 Reference implementation (Python)

```python
ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def encode(event=0, money=0, engine=0, shocks=0, tires=0, turbo=0):
    assert 0 <= event <= 6 and 0 <= money <= 9999
    assert all(0 <= v <= 6 for v in (engine, shocks, tires, turbo))
    b = [0]*10
    b[0] = 31 - event
    b[1], b[2], b[3] = money & 31, (money >> 5) & 31, (money >> 10) & 31
    b[4], b[5], b[6], b[7] = engine, shocks, tires, turbo
    s = (sum(b[0:8]) + 7) & 0xFF
    b[9] = s & 31
    b[8] = (s >> 5) & 31
    return "".join(ALPHA[x] for x in b)

def decode(code):
    if len(code) != 10: return None
    try: b = [ALPHA.index(c) for c in code]
    except ValueError: return None
    s = (sum(b[0:8]) + 7) & 0xFF
    if b[9] != (s & 31) or b[8] != ((s >> 5) & 31): return None
    if (31 ^ b[0]) > 6 or any(x > 6 for x in b[4:8]): return None
    money = b[1] + 32*b[2] + 1024*b[3]
    if money > 9999: return None
    return {"event": 31 ^ b[0], "track": (31 ^ b[0]) + 1, "money": money,
            "engine": b[4], "shocks": b[5], "tires": b[6], "turbo": b[7]}
```

Working copy: `/tmp/opencode/atvtrr/atv_password.py` (also prints the published-code check table).

Valid-code space: `7 events × 10001 money values × 7^4 upgrade combos = 168,070,000` codes, i.e. about
1 in 21.8 million of the `36^10 = 3,656,158,440,062,976` possible 10-symbol strings.

## 6. Tables

### 6.1 Symbol grid / glyph substitution (`0x0801C1DE`, 36 × u16)

| value | glyph | tile | value | glyph | tile |
|---:|---|---|---:|---|---|
| 0 | A | `0x1B` (solid ▲) | 18 | S | `0x13` |
| 1 | B | `0x02` | 19 | T | `0x14` |
| 2 | C | `0x03` | 20 | U | `0x1F` (solid ◀) |
| 3 | D | `0x04` | 21 | V | `0x16` |
| 4 | E | `0x1C` (solid ▶) | 22 | W | `0x17` |
| 5 | F | `0x06` | 23 | X | `0x18` |
| 6 | G | `0x07` | 24 | Y | `0x19` |
| 7 | H | `0x08` | 25 | Z | `0x1A` |
| 8 | I | `0x1D` (solid ▼) | 26 | 0 | `0x20` |
| 9 | J | `0x0A` | 27 | 1 | `0x21` |
| 10 | K | `0x0B` | 28 | 2 | `0x22` |
| 11 | L | `0x0C` | 29 | 3 | `0x23` |
| 12 | M | `0x0D` | 30 | 4 | `0x24` |
| 13 | N | `0x0E` | 31 | 5 | `0x25` |
| 14 | O | `0x1E` (solid ■) | 32 | 6 | `0x26` |
| 15 | P | `0x10` | 33 | 7 | `0x27` |
| 16 | Q | `0x11` | 34 | 8 | `0x28` |
| 17 | R | `0x12` | 35 | 9 | `0x29` |

The five substituted vowels take tile ids `0x1B..0x1F` (just past the digit-free letter run); all other letters
use `0x02..0x14` and the digits use `0x20..0x29`. The table above is the literal content of `0x0801C1DE`.

### 6.2 Navigation tables (38 entries each)

```
Up    (0x0801C146): 13 26 27 28 29 30 31 32 33 36 37 24 25 0 1 2 3 4 5 6 7 8 9 10 11 12 14 15 16 17 18 19 20 21 22 23 34 35
Down  (0x0801C16C): 13 14 15 16 17 18 19 20 21 22 23 24 25 0 26 27 28 29 30 31 32 33 34 35 11 12 1 2 3 4 5 6 7 8 36 37 9 10
Left  (0x0801C192): 37 0 1 2 ... 36           (i-1 wrapping)
Right (0x0801C1B8): 1 2 3 ... 37 0            (i+1 wrapping)
```

The Up/Down tables are visibly hand-made and asymmetric (e.g. `Down[13]=0`, `Down[14]=26`); they are reproduced
here so a second analyst can replicate the exact key path.

### 6.3 Language string table (`0x08058CAC`, 5 × `0xBC`)

English block starts at `0x08058CAC`; French/German/Spanish/Italian blocks are at `+0xBC`, `+0x178`, `+0x234`,
`+0x2F0`. Index 46 is `INVALID PASSWORD` in every block; index 26 is `PASSWORD:`; index 2 is `PASSWORD`.

### 6.4 Published codes

GameFAQs (via search snippets; the page itself returns HTTP 403) lists "New Career Event passwords" for
events 2..6. Verified against the ROM/emulator:

| Event | Published | Decoder result | Emulator |
|---:|---|---|---|
| 2 | `4E2AAAAACF` | track 2, $900, 0/0/0/0 | accepted, TRACK 2 |
| 3 | `3AZADDDACG` | track 3, $800, 3/3/3/0 | decoder-verified |
| 4 | `2AZAFFFCCN` | track 4, $800, 5/5/5/2 | decoder-verified |
| 5 | `7E2AGGGGC0` | **invalid** (symbol 0 = 33 → `31^33 = 62 > 6`) | rejected, INVALID PASSWORD |
| 5 (corrected) | `1E2AGGGGC0` | track 5, $900, 6/6/6/6 | accepted, TRACK 5 |
| 6 | `0IYBGGGGC0` | track 6, $1800, 6/6/6/6 | accepted, TRACK 6 |

The published #5 differs from the accepted code only in the first character (`7` vs `1`), which is the field that
carries the event index — a transcription error on the fan site, not a ROM difference.

Examples generated with the encoder and confirmed in the emulator: `5AAAAAAABG` (track 1, $0, no upgrades) and
`ZPYJGFEDDC` (track 7, $9999, 6/5/4/3).

## 7. Validation evidence

**Observed (emulator screenshots + RAM reads, mGBA 0.10.5, `:103`)**

* Password screen with 10-cell field and 36-symbol grid; `INVALID PASSWORD` on bad input.
* `5AAAAAAABG` → MOD SHOP `$0`, empty upgrade bars, password line `5AAA…BG`; `ACCEPT` → `NEXT EVENT / TRACK 1`.
* `ZPYJGFEDDC` → MOD SHOP `$9999`, ENGINE 6 / SHOCKS 5 / TIRES 4 / TURBO 3; `ACCEPT` → `TRACK 7`.
* `4E2AAAAACF` (typed on the grid) → MOD SHOP `$900` → `TRACK 2`; the race then starts (`LAP 1 OF 3`).
* `0IYBGGGGC0` → `$1800`, all bars 6 → `TRACK 6`; `1E2AGGGGC0` → `$900`, all bars 6 → `TRACK 5`.
* `7E2AGGGGC0` typed on the grid → `INVALID PASSWORD`.
* `4E2AAAAACG` (one symbol changed), `4E2AHAAACM` (ENGINE 7), `4ARTAAAACJ` (money 20000) → all `INVALID PASSWORD`
  even though each carries a correct checksum for its payload.
* Alias test: injected `461AAAAADA` → MOD SHOP shows `$896` and the password line `4A2AAAAACB`; reading
  `0x030017A0` afterwards returns `[30,0,28,0,0,0,0,0,2,1]`, i.e. the encoder rewrote the buffer.
* RAM dumps while typing on the grid: buffer `0x030017A0` received one cell index per `A` press; `0x0300179C`
  tracked the cursor (0→1→…→35, then 37 when full); `0x030017C0` counted 0→10.
* Pause menu in a race contains only `Continue / Music: On / SFX: On / Quit`; OPTIONS contains only
  `MUSIC ON / SFX ON`; no debug or cheat entry exists in either.

**Derived (instruction-level)**

* Validator, field ranges, checksum form and the accept-path state writes from the disassembly listed in §4.
* Encoder at `0x08013134` is the exact inverse of the validator (same `+7`, same split).
* The grid stores cell indices, not characters (`0x080012A0`: `strb r1,[r0]` with `r1 = [0x0300179C]`).
* Cell 36/37 are handled before the append routine, so only 0..35 can enter the buffer.

**Inferred**

* The five vowel glyphs are a deliberate obscenity filter; the tile table proves the substitution but the intent
  is inferred from the pattern (all five vowels, no other letters).
* `+7` in the checksum is an arbitrary offset with no observable meaning.
* `event = track-1` naming: the screen labels the value `TRACK n`; whether the game also uses it for internal
  "event" numbering is not proven.
* The unreferenced ASCII alphabet at `0x0801C22A` is legacy/debug data (no 32-bit pointer anywhere in the ROM).

**Absence of other in-game cheats**

* `strings` over the whole ROM for `debug|test|cheat|secret|unlock|bonus|hidden` finds nothing outside the normal
  UI/copyright text.
* A scan for runs of ≥4 little-endian `u16` key masks (`1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200`) returned only
  two data regions (`0x5320E`, `0x2B0584`), both clearly non-code (small-value tables / tile data); no
  button-sequence table exists.
* Menus reached and inspected: MAIN MENU (NEW GAME / ENTER PASSWORD / OPTIONS / CREDITS listed), OPTIONS
  (`MUSIC ON`, `SFX ON` only), password screen, MOD SHOP, NEXT EVENT, and the in-race pause menu. No menu offers a
  code entry, debug entry or hidden extra outside `ENTER PASSWORD`. CREDITS is a plain text roll (its strings sit in
  the same `0x08058CAC` bank; it was not scrolled to the end).

## 8. Unknowns

* The commercial GameFAQs page was blocked (403) and only search snippets were available; the "6 cheat codes and
  secrets" entry count suggests one further entry (possibly a non-password secret) that was not recovered. The
  five event passwords were all accounted for.
* Whether the game ever *presents* a password after an event (rather than only echoing/normalising an entered one)
  was not exercised; the encoder exists and runs on the MOD SHOP screen, which is sufficient to regenerate a code,
  but a full play-through was not performed.
* The precise role of `0x030017D4` (a byte the screen code clears on BACK and that stayed `1` during cursor moves)
  was not determined.
* Alias codes (digit symbols 6..9 inside the money field) were shown to exist for one case; the complete set of
  aliases was not enumerated. All aliases normalise to the canonical encoding on screen.
* The header checksum field is zeroed in this dump; the ROM may be a re-dump/patched image. The complement byte is
  correct, and behaviour matched every public code, so the analysis is against the image whose SHA-256 is given
  above.

## 9. Tooling

* `mgba-sdl` 0.10.5 under `Xvfb :103` + `openbox`; `xdotool` for input, `scrot` for screenshots.
* GDB stub disabled for the main work; a small GDB-RSP client (`/tmp/opencode/atvtrr/rsp.py`, raw
  `$<data>#<checksum>` packets over TCP) was used instead because mGBA's stub accepts a single connection, caps
  memory reads at `0x200` bytes and does not survive repeated `gdb-multiarch` reconnects. It provided:
  `m` memory reads (RAM dumps), `M` writes (buffer injection), `Z0` breakpoints and the `0x03` interrupt.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for disassembly.
* Capstone 5.0.7 (python) for pointer/BL/literal scans; Pillow for screenshot pixel checks.
* Scripts in `/tmp/opencode/atvtrr/`:
  * `atv_password.py` — encoder/decoder and the verification table above.
  * `navgrid.py` — breadth-first key-path planner over the four navigation tables.
  * `phase0.py` — hashes/header/embedded-header scan.
  * `ptrscan.py`, `encscan.py` — literal-pointer and checksum-pattern scans.
  * `rsp.py`, `agent.py`, `ctl.py` — RSP client and command agent.
  * Screenshots: `b3.png` (empty password screen), `v2.png` (`7E2AGGGGC0` rejected), `neg_badck.png`,
    `neg_lvl7.png`, `neg_money20k.png`, `full2.png` (`5AAAAAAABG`), `t3.png` (`ZPYJGFEDDC`), `v3.png`
    (`4E2AAAAACF`), `s5.png` (`0IYBGGGGC0`), `alias1.png` (alias normalisation), `q2.png`/`t5.png` (TRACK 5/7),
    `p_race1.png` (race started), `p_pause.png` (pause menu).
* Installed during the engagement: `pillow` via `pip --break-system-packages` (no other new packages).

## 10. Legal note

No ROM, graphics, music or game text is redistributed with this report. It contains only addresses, file offsets,
the derived arithmetic format, short UI labels needed to reproduce the navigation, and the author's own codec.
