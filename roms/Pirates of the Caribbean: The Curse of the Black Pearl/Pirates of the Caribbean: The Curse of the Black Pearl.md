# Pirates of the Caribbean: The Curse of the Black Pearl (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pirates of the Caribbean: The Curse of the Black Pearl.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `PIRATESCARIB` |
| Game code / maker | `A8QE` / `6S` |
| Version / complement / header checksum | 0x00 / 0x40 / 0x0000 (rebuilt-header artifact) |
| Header entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| Embedded GBA headers | **1** (Nintendo logo hit only at file offset 0x4) |
| Patch / trainer | none; retail image |
| MD5 | `fc393954c63fa0e82ccfd7334491c2a7` |
| SHA-1 | `034e5206c3ed8275e4bbb249edf305d14948bf8f` |
| SHA-256 | `8b12ea1121c65b25d0f957e77865e561f9850f2cfd9f4186be0b0ebb2db98285` |

## 2. Executive summary

The game has **two developer-intended code systems**, both entered on the same screen
(Continue Game → on-screen 32-symbol keypad, 10 slots):

1. **Seven fixed cheat strings** (5–8 characters) compared by `strcmp` in the validator.
   All seven published codes are present verbatim in a table at `0x0804A4F8`.
2. **An algorithmic 10-symbol progress code** (5 bits/symbol, 50 bits total) using the
   alphabet `BCDFGHJKLMNPQRSTVWXYZ0123456789?`. The validator XORs the ten 5-bit
   symbols with one of 16 ten-word keys, unpacks five fields (level, "first", cheat3,
   selector, and a 22-bit checksum), and accepts iff `second == 0x3FFFFF & ~(level + first + selector + cheat3)`.

The whole space was characterised and the ROM's own validator was executed as an
**offline oracle** (Unicorn) to confirm the decoder bit-for-bit and to mint codes absent
from every published list. `JNNBG14?37` (level 7, cheat3=7, first=478) was typed on the
real password screen and **accepted in-game** (no "INVALID PASSWORD"; game started).
A corrupted code shows "INVALID PASSWORD", and a level-32 code is unrepresentable by the
format, bounding the space.

Debug-build leftovers (entity list / debug toggles / "Pirates password generator") exist
as code and menu tables, but no in-game trigger was found on any reachable screen.

## 3. How to reproduce

**Emulator:** mGBA (SDL), `SDL_AUDIODRIVER=dummy`, Xvfb `:317`, scale 3.
Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.

**Menu path:** boot → language (A selects English) → title (Start) → main menu →
**Continue Game** (Down, A) → password keypad.

**Entering a code:** the keypad is an 8x4 grid; D-pad moves one cell, A types. The
bottom row has a backspace (left arrow) and a checkmark (accept). Navigate to the
checkmark and press A; accepted codes leave the screen (effect or game start), rejected
codes show **INVALID PASSWORD**. The on-screen keyboard itself is authoritative and
matches the ROM alphabet exactly (screenshot `f3_password.png`).

**Codes tested in-game:** `L1TTLVN` → baby photo "Congratulations Tom & Yvonne"
(`baby1.png`, `baby_submit_long.png`); `CR3D1TS` → credits/ending presentation
(`entered_short.png`, `cred_adv*.png`); `JNNBG14?37` (novel) → accepted, game started
(`novel2_result.png` → `novel_gameplay.png`); corrupted code → `INVALID PASSWORD`
(`gg1.png`).

**Offline oracle:** `oracle.py` executes `0x080098A4` with Unicorn, placing the code at
`0x02001000`, stack at `0x03007F00`, and reading the four output globals.
`fields.py` injects arbitrary `w[]` words at `0x8009A46` to recover exact per-bit field
contributions.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x0804A4E0` | 21-letter alphabet `BCDFGHJKLMNPQRSTVWXYZ` (file 0x4A4E0) |
| `0x0804A4F8` | cheat table: `CR3D1TS` (0x4F8), `L1TTLVN` (0x500), `SH33P` (0x508), `BVLL1TZ` (0x510), `1MM0RT4L` (0x518), `G00D13S` (0x524), `G3N1VS` (0x52C) — variable length, NUL-terminated |
| `0x080098A4` | password validator (Thumb): `r0` = NUL-terminated input, returns 0/1/2/3/4 |
| `0x08009164` | caller: maps return values to game start / credits / baby photo / cheat toggle |
| `0x08099AC` | 10-symbol progress decode path (char → 5-bit value, selector, XOR) |
| `0x0809A38` | 10-word XOR loop against key table |
| `0x0809BCE` | checksum comparison against `0x003FFFFF & ~sum` |
| `0x0855D884` | XOR key table, 16 selectors × 10 words (file 0x55D884) |
| `0x03004DC0` | global: `first` field |
| `0x030053E4` | global: `cheat3` field |
| `0x030051D0` | global: `level` field |
| `0x03004D70` | global: cheat flag word (u16, XOR bits) |
| `0x0200010E` / `0x0200011D` | keypad input buffer (1-based symbol indices; split banks) |
| `0x0809F6EC`, `0x0809F7AC`, `0x0809F82C`, `0x0809F84C`, `0x080A000C` | debug-build strings (BETA debug / entity list / debug toggles / password generator / level+lives) |
| `0x0805F440`–`0x0805FD58` | Thumb function-pointer table for debug-menu items (10 entries; password generator = `0x08014B4D`) |

## 5. Algorithm

### 5.1 Validator dispatch (`0x080098A4`)

```
strcpy/ memcpy(sp, alphabet[0x0804A4E0], 21)      ; 21-letter lookup table
if input[0] == 0: set globals, return 1             ; empty = start game
n = strlen(input)
if n <= 9:                                          ; short cheat path
    for (s,ret,bits) in 7 strcmp records:
        if strcmp(input, s)==0: toggle bits in 0x03004D70; return 4
    return 0 (invalid)
else:                                               ; 10-symbol progress path
    ... decode below
```

### 5.2 Symbol → value

```
c in 'B'..'Z' : v = index in BCDFGHJKLMNPQRSTVWXYZ       (0..20)
c in '0'..'9' : v = ord(c) - 0x27                        (21..30)
c == '?'      : v = 31
selector s    = ((raw[0]&16)>>4)|((raw[1]&16)>>3)|((raw[2]&16)>>2)|((raw[3]&16)>>1)
w[i]          = raw[i] XOR keytable[s][i]                (10 words)
```

### 5.3 Field unpacking (exact, recovered from the ROM oracle)

Per-bit contributions `(word, bit) → field bit` (all are OR of distinct bits):

```
first    : w0.b1→15, w0.b3→14, w1.b1→13, w2.b1→11, w2.b3→12, w3.b1→9, w3.b3→10,
           w4.b1→7, w4.b3→8, w5.b1→5, w5.b3→6, w6.b1→4, w7.b1→3, w8.b1→2,
           w9.b1→0, w9.b4→1
cheat3   : w0.b0→1, w0.b2→2, w1.b3→0
level    : w4.b4→4, w5.b4→3, w6.b4→2, w7.b4→1, w8.b4→0
second   : w1.b0→20, w1.b2→21, w2.b0→18, w2.b2→19, w3.b0→16, w3.b2→17,
           w4.b0→14, w4.b2→15, w5.b0→12, w5.b2→13, w6.b0→9, w6.b2→10, w6.b3→11,
           w7.b0→6, w7.b2→7, w7.b3→8, w8.b0→3, w8.b2→4, w8.b3→5,
           w9.b0→0, w9.b2→1, w9.b3→2
check    : second == (0x3FFFFF & ~(level + first + selector + cheat3))
```

Note: `second` is a 22-bit checksum; the integer sum (with carries) is inverted and
masked. The `level` field is 5 bits (0–31), `cheat3` 3 bits (0–7), `first` 16 bits.

### 5.4 Encoder (inverse)

Choose `level` (0–31) and `cheat3` (0–7) and optional `first` bits. For each of the 16
selectors: set the corresponding `w` bits for level/cheat3/first, compute
`target = 0x3FFFFF & ~(level+first+sel+cheat3)`, set the 22 checksum-only `w` bits from
`target`'s bits, reconstruct `raw = w XOR key[s]`, and accept the selector whose raw
bit-4 pattern regenerates `s`. `raw → characters` via the inverse alphabet.

## 6. Tables

### 6.1 Fixed cheat passwords (verbatim in ROM, `0x0804A4F8`)

| Code | Effect | Return | Flag bit |
|---|---|---|---|
| `CR3D1TS` | credits / ending presentation | 2 | — |
| `L1TTLVN` | baby photo ("Congratulations Tom & Yvonne") | 3 | — |
| `SH33P` | soldiers/pirates become explosive sheep | 4 | 0x0004 |
| `BVLL1TZ` | infinite cannonballs and bullets | 4 | 0x0001 |
| `1MM0RT4L` | infinite lives | 4 | 0x0002 |
| `G00D13S` | start with triple cannons, sabre, pistol | 4 | 0x0008 |
| `G3N1VS` | more aggressive enemies | 4 | 0x0010 |

The flag word at `0x03004D70` is **XOR-toggled** (re-entering a code turns it off).

### 6.2 Progress-code fields

| Field | Bits | Source | Meaning |
|---|---|---|---|
| selector | 4 | bit4 of raw symbols 0–3 | indexes XOR key table |
| level | 5 | bit4 of w4..w8 | starting level (game uses 1–25; 0 and 26–31 accepted by validator) |
| cheat3 | 3 | w0.b0,b2 + w1.b3 | low cheat bits (guide's `T4RCJLJM84` has cheat3=7) |
| first | 16 | scattered bits 1/3/4 | progress/stats (published codes: 24 → 2277 as level 2 → 25) |
| second | 22 | scattered bits 0/2/3 | checksum |

## 6b. Enumeration

**Space definition.** Alphabet size 32, length 10 → `32^10 = 1,125,899,906,842,624`
(2^50) raw strings. The format partitions those 50 bits into 4 selector + 5 level +
3 cheat3 + 16 first + 22 checksum = 50 bits. A fixed checksum leaves
`2^50 / 2^22 = 2^28 = 268,435,456` valid codes (before semantic level range checks).
The seven short codes are a separate, closed set of exactly 7 table entries.

**Validator model.** Fully reimplemented in `pirates.py`; agrees with the ROM oracle on
all 24 published level codes, the Barbossa code, every minted code, and rejected inputs.

**Novel codes (generated, absent from 3rd party cheat indexes / all published lists):**

| Code | level | cheat3 | first | ROM oracle | In-game |
|---|---|---|---|---|---|
| `JNNBG14?37` | 7 | 7 | 478 | accepted (rv=1) | **accepted** — game started, no INVALID PASSWORD |
| `JNNBS9PVDH` | 2 | 7 | 24 | accepted (rv=1) | not typed (format verified by oracle) |
| `FDLB7GF0QP` | 26 | 0 | 2277 | accepted (rv=1) | not typed (beyond published level 25) |
| `FDNB9S6V6L` | 31 | 7 | 0 | accepted (rv=1) | not typed |
| `T4RCJLJM84` (guide) | 1 | 7 | 1125 | accepted (rv=1) | guide reports level 1, cheat bits 7 |

`JNNBG14?37` keeps the published level-7 code's `first=478` but changes `cheat3` from 4
to 7 — an unadvertised combination — so it is provably not in any published list.

**Bounds proven by rejection.**
- Bad checksum `T4RCJLJM88`: decoder rejects, oracle returns 0; in-game a corrupted
  entry produced **INVALID PASSWORD** (`gg1.png`).
- Level 32: not representable (5-bit field) — encoder cannot produce a code; oracle
  decoder reports no valid code.
- Garbage `AAAAAAAAAA`, `??????????`, `0123456789`: oracle rejects (rv=0), decoder rejects.
- Published lowercase "Uberclocked" list (`p4rmjdd5bl`, …) and the 3rd party cheat indexes alternate
  level list are **not accepted** by this ROM's decoder/oracle — different edition or
  transcription errors; recorded as unverified for this image.

**Enumeration method:** `fields.py` calls the ROM's own validator with injected `w[]`
words to recover the exact bit mapping (rather than trusting hand disassembly), then
`solve by construction`: every checksum bit has a dedicated w-bit, so an encoder can set
it directly. No brute force over 2^22 was needed.

## 7. Validation evidence

- **Observed (emulator):** every screen listed in §3; baby photo after `L1TTLVN`;
  credits presentation after `CR3D1TS`; game start after novel `JNNBG14?37`;
  INVALID PASSWORD for corrupted input; input buffer bytes in EWRAM savestate
  (`0x0200010E`, 1-based symbol indices).
- **Observed (ROM oracle, Unicorn):** return codes 2/3/4 for the short strings, flag
  toggles, and accept/reject plus all field values for arbitrary 10-symbol codes.
- **Derived (disassembly):** validator dispatch, literal table addresses, key table,
  checksum comparison at `0x0809BCE`, flag-write instructions, debug-menu pointer table.
- **Inferred:** exact narrative effect of the credits presentation (a cutscene montage
  was observed, the final scrolling-credit text was not followed to completion);
  debug-menu trigger (code and menu table exist but no reachable entry was found).

## 8. Unknowns

- The debug screen with "entity list / debug toggles / password generator" exists in the
  shipped image (strings + 10-entry Thumb pointer table at `0x0805F440`), but no
  in-game trigger was found on title, main, options, password, pause or gameplay screens.
  It is likely gated by a build-time flag or an undiscovered button code; not proven.
- `first` field semantics beyond "progress/stats" were not mapped to individual HUD
  quantities; minted codes use published `first` values or zero.
- Pause menu and level-select were not present as standalone screens in the reachable
  flow (no level-select screen exists; pause was not reachable in the tested states).

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, Unicorn 2.1.4, Python 3.
- `oracle.py` — ROM validator executed under Unicorn (accept/reject + outputs).
- `fields.py` — per-bit field contribution recovery via injected `w[]`.
- `pirates.py` — decoder/encoder and published-code verification.
- `ss.py` — mGBA savestate `gbAs` zlib parser (RAM evidence).
- `nav.py` / `input.py` — XTEST keypad navigation and screenshots on display `:317`.
- Web: 3rd party cheat indexes —
  all fetched as data; no instructions from fetched content were followed.

**Legal note:** no ROM bytes, graphics, or copyrighted assets are reproduced here; only
addresses, hashes, algorithms and the author's own generated example codes.
