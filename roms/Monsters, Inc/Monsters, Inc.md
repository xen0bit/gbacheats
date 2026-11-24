# Monsters, Inc. (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

- File: `roms/Monsters, Inc/Monsters, Inc.gba`
- Size: 4,194,304 bytes (0x400000)
- Header title: `MONSTERS,INC` (12 bytes at 0xA0)
- Game code: `AMXE` (USA), maker `78`, version `0x00` (Rev.00)
- `file` identification: `Game Boy Advance ROM image: "MONSTERS,INC" (AMXE78, Rev.00)`
- MD5: `3e4a2e644d21654e1e5c68baa9115df9`
- SHA-1: `21a12d54cc709eb54e6c81a3d1b9b6e7d6cf51ef`
- SHA-256: `cfae1622ea6bc88bbcf09be2851b9370032b62090d2443f20111c12ba7241e78`

Header notes (Observed): entry word `0xEA00002E` (stock `b 0x080000C0`); fixed byte
`0x96` present; header checksum `0x0000` and stored complement `0x36` disagree with
the computed complement `0x4F` — a rebuilt-header artifact (Guide §16.1), **not** a
cracktro. First 4 KiB are normal crt0 (literal pool at 0x1C0 carries `0x03007FFC`
and Thumb `main` pointer `0x080001D1`). Embedded-header scan for the 156-byte
Nintendo logo (`24 ff ae 51 ...`) found exactly **one** hit, at file offset 0x4 —
single retail image, no appended trainer, no multi-game pack.

## 2. Executive summary

The GBA game has a real, developer-intended **6-symbol password system** on the
main menu (`New Game / Password / Options`). The on-screen alphabet is exactly 32
symbols `BCDFGHJKLMNPQRSTVWXYZ0123456789!`, so each password character is a 5-bit
value. The ROM validator at **`0x08008CE4`** accepts a code when:

1. the password screen is active (`[0x03000024] == 5`);
2. `c5 == (c0+c1+c2+c3+c4+1) & 31` (a 5-bit additive checksum);
3. `n = c0 + 32*c1 <= 999` and `(c2 & 15) != 15`;
4. not (`n < 100 && c4 == 0 && ((c2&16) ? (c2&15)%5 : 0) == 0`).

Accepted space: **30,662,400** of 32^6 = 1,073,741,824 possible strings.
The validator decodes the payload into difficulty, start/area, progress and flag
fields stored in IWRAM; the difficulty field was RAM-verified by entering a
minted code. Public 3rd party cheat index codes were verified against the model: 62/64 satisfy
the checksum; the two exceptions are published typos, one of which was disproved
in the emulator (`M2F9S7` rejected, corrected `M2F9SV` accepted).

No button code, hidden debug menu or level-select cheat exists in this SKU. The
only global button combination found is `L+R`, which is a **soft reset** (SWI 0/1
via `FUN_08039A84`) guarded by a one-shot byte at `0x030023CC` — not a cheat
surface. The GBC-only 4-character `CRDT` credits code published on 3rd party cheat indexes are
not applicable to this 6-character GBA screen.

No prompt-injection payload was encountered in any fetched page or ROM string.

## 3. How to reproduce

- Emulator: `mgba -3` under `Xvfb :316`, `SDL_AUDIODRIVER=dummy`.
- Keymap (mGBA SDL default): A=`x`, B=`z`, Start=`Return`, D-pad = arrow keys,
  L=`a`, R=`s`. Hold keys 100–150 ms.
- Path: boot → Pixar logo → Monsters, Inc. logo → `PRESS START` → `MAIN MENU` →
  `Password`. Keyboard grid:
  - row 0: `BCDFGHJKLMN` (11)
  - row 1: `PQRSTVWXYZ` (10)
  - row 2: `0123456789!` (11)
  - D-pad moves the highlight; A selects a symbol; after 6 symbols the highlight
    moves to `Enter`; Start also jumps to `Enter`/`Exit`; A submits. A rejected
    code clears the field and stays on the screen.
- Screens walked and verified: title/attract, MAIN MENU (3 items), PASSWORD,
  Options → DIFFICULTY (EASY/NORMAL/HARD, selection starts a new game), in-game
  HUD, PAUSE overlay, plus all intro/cutscene frames reached through those paths.
  `L+R` was held on the main menu and observed to soft-reset (no debug screen).
- Codes tested (all entered on the real PASSWORD screen):
  - `XRDZB1` (published) → accepted, Scare Floor, HUD 34 energy / 4 lives.
  - `XRKZB6` (**novel**) → accepted, different scene (two companions, candy,
    shorter energy bar); RAM difficulty byte 0x03002652 changes 0x00→0x01.
  - `M2F9SV` (**novel**, corrected published typo) → accepted, HUD 2/45/7.
  - `BBBBBB`, `L!DZB9` (out-of-range n=1000), `BBBZB0` (all-zero fields),
    `M2F9S7` (published typo) → all rejected (field cleared).

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Password validator (`r0`=unused, returns 0 accept / -1 reject) | `0x08008CE4` | Derived (Thumb disassembly) + emulator |
| Password buffer clear (`0xFF` × 6, clears state) | `0x0800852C` | Derived |
| Password screen init | `0x08008558` | Derived |
| Password input buffer (6 bytes; 0xFF = empty) | IWRAM `0x03000028` | Observed (savestate scan: `XRDZB1` → `12 0d 02 14 00 16`) |
| Screen-state gate, must equal 5 | IWRAM `0x03000024` | Derived + observed (state = 05 on PASSWORD) |
| n/100 field ("hundreds") | IWRAM `0x03002754` | Derived; observed 04 for XRDZB1, 02 after Options→Hard |
| n%100 field ("remainder") | IWRAM `0x0300286C` | Derived; observed 0x22 for XRDZB1 |
| c3 & 3 | IWRAM `0x03002850` | Derived; observed 00 for XRDZB1 |
| c2 flags: bit2(c3)/bit4(c3) | IWRAM `0x03002650` / `0x03002651` | Derived |
| difficulty = (c2&15)/5 | IWRAM `0x03002652` | Derived + **observed 00 → 01** for XRDZB1 → XRKZB6 |
| c2 low-field | IWRAM `0x030028A4`, `0x03002860` | Derived |
| c3 bit3 | IWRAM `0x03002C74` | Derived |
| c4 bits, reversed | IWRAM `0x03006A60..0x03006A64` | Derived |
| Keypad reader (`~KEYINPUT`, held/pressed state) | `0x08024BF4` | Derived |
| Global input state struct | IWRAM `0x03006D90` | Derived |
| Font ASCII→tile map (0x20..0x7F → tile index) | ROM `0x083BAA1C` | Derived (text is tile-indexed; no plaintext in ROM or savestate RAM) |
| L+R soft-reset gate, one-shot byte | `0x08000378`–`0x0800038A`, `0x030023CC` | Derived; emulator-held L+R produced reset, no menu |
| Reset helper (disables IRQ, SWI 1 + SWI 0) | `0x08039A84` | Derived |

File offset ↔ ROM address: `0x08000000 + file_offset`. Savestate IWRAM mapping:
`state_offset = 0x19000 + (real_address - 0x03000000)` (§16.13).

## 5. Algorithm

Validator pseudocode (immediately after clearing the output fields):

```
if mem8[0x03000024] != 5: return -1              # gate: password screen active
c = mem8[0x03000028 .. 0x0300002D]               # six 5-bit symbols
n = c[0] + 32*c[1]
hundreds = n / 100          # integer division, FUN_08039C44
rem      = n % 100          # FUN_08039CBC
if hundreds > 9 or rem > 99: return -1           # rem check is trivial

lo   = c[2] & 15
b4   = (c[2] >> 4) & 1
pa4  = (lo % 5) if b4 else 0
diff = lo / 5               # 0=easy, 1=normal, 2=hard
if pa4 > 4 or diff > 2: return -1                # pa4 check trivial; lo=15 fails

mem[0x03002754] = hundreds
mem[0x0300286C] = rem
mem[0x03002652] = diff
mem[0x030028A4] = pa4
mem[0x03002860] = pa4
mem[0x03002650] = (c[3] >> 2) & 1
mem[0x03002651] = (c[3] >> 4) & 1
mem[0x03002C74] = (c[3] >> 3) & 1
mem[0x03002850] = c[3] & 3
for i in 0..4: mem[0x03006A60 + (4-i)] = (c[4] >> i) & 1
popcount = number of set bits in c[4] & 0x1F

if hundreds == 0 and popcount == 0 and pa4 == 0: return -1
if c[5] != (c[0]+c[1]+c[2]+c[3]+c[4]+1) & 31: return -1
return 0                                        # accept: start game
```

Helper at `0x08039C44` is unsigned integer **division** (returns quotient in r2);
helper at `0x08039CBC` is unsigned **modulo** (returns remainder in r0) — both
verified by instruction-level inspection.

## 6. Tables

**Alphabet (index → symbol), exactly as shown on the entry keyboard:**

```
0 B   1 C   2 D   3 F   4 G   5 H   6 J   7 K   8 L   9 M  10 N
11 P  12 Q  13 R  14 S  15 T  16 V  17 W  18 X  19 Y  20 Z
21 0  22 1  23 2  24 3  25 4  26 5  27 6  28 7  29 8  30 9  31 !
```

`I` and `O` are **not** keyboard symbols; published codes containing them are
OCR errors for `1` and `0` (Guide §16.7). Example: `XRDZBI` ≡ `XRDZB1`,
`VPB97I` ≡ `VPB971`, `IFZ2CJ` ≡ `1FZ2CJ`.

**Field layout (6 × 5 bits = 30 bits; 2 bits of the 32-bit word unused):**

| Symbol(s) | Bits | Field | Notes |
|---|---|---|---|
| c0,c1 | 10 | n = c0+32·c1 | split into n/100 (0..9) and n%100 (0..99) |
| c2 | 5 | lo=c2&15, b4=(c2>>4) | diff=lo/5 (0/1/2); pa4=b4?(lo%5):0; lo=15 rejected |
| c3 | 5 | bit flags | c3&3, bit2, bit3, bit4 written to four separate globals |
| c4 | 5 | progress/flag bits | 5 bits copied reversed; popcount participates in zero-check |
| c5 | 5 | checksum | (sum(c0..c4)+1) & 31 |

**Published-code verification (3rd party cheat indexes GBA list, 64 codes):** 62/64 satisfy the
checksum. Exceptions: `M2F9S7` (published "easy level 16") and `3RC!94`
(published "easy level 9"). `M2F9S7` was entered in the emulator and **rejected**;
its checksum-corrected form `M2F9SV` was **accepted**. All other published codes
are consistent with the validator model.

## 6b. Enumeration

**Space definition:** 32 symbols × 6 positions = 32^6 = **1,073,741,824** raw
strings. The additive checksum fixes c5 for any c0..c4 → 32^5 = **33,554,432**
checksum-valid candidates. Applying the validator's range checks
(`n <= 999`, `(c2&15) != 15`, and the all-zero exclusion) leaves
**30,662,400 accepted codes** (2.86% of raw strings). The validator itself was
read directly from ROM rather than guessed, so this count is a derivation from
the shipped code, corroborated by emulator accept/reject tests.

**Novel codes (absent from 3rd party cheat indexes and every other list
consulted; exact-string web search for `XRKZB6` returned no match):**

1. **`XRKZB6`** — derived from the published `XRDZB1` by changing only the
   difficulty field (`c2`: 2 → 7, so `(c2&15)/5`: 0 → 1 = Normal) and recomputing
   the checksum (`c5`: 22 → 27). Entered on the real PASSWORD screen: **accepted**,
   started a visibly different game state (two companion monsters, candy items,
   shorter energy bar). RAM proof (savestate diff, slots 6 vs 7):
   `0x03002652` = `0x00` (XRDZB1) → `0x01` (XRKZB6); all other decoded fields
   unchanged.
2. **`M2F9SV`** — the checksum-corrected form of the published typo `M2F9S7`;
   **accepted** in the emulator (HUD 2 / 45 / 7). Not present in any published
   list as written.

**Bounds proven by rejection (all on the real PASSWORD screen):**

| Input | Violated rule | Observed result |
|---|---|---|
| `BBBBBB` | checksum (expected `C`-index 1, got 0) | rejected, field cleared |
| `L!DZB9` | n = 1000 → hundreds = 10 > 9 | rejected, field cleared |
| `BBBZB0` | all-zero exclusion (hundreds=0, c4=0, pa4=0) | rejected, field cleared |
| `M2F9S7` | published typo: bad checksum | rejected, field cleared |

The `c2&15 == 15` bound is derived from the `cmp r0,#2` range check at
`0x08008DB0`; a code exercising it was not typed separately — reported as
Derived, not Observed.

## 7. Validation evidence

- **Observed** (emulator/screenshots/savestate RAM): all screens listed in §3;
  `XRDZB1`, `XRKZB6`, `M2F9SV` accepted with distinct game states; four rejections
  above; input buffer at `0x03000028` containing the six 5-bit indices of the
  typed code; difficulty byte `0x03002652` 0x00→0x01 for the minted code; L+R
  produces a reset with no menu; Options→Hard writes `0x03002754 = 2`.
- **Derived** (instruction-level): validator at `0x08008CE4` and its full accept
  model; division/modulo helper identities; field destinations and widths;
  accepted-space count; font ASCII→tile map at `0x083BAA1C`; L+R reset gate.
- **Inferred**: semantic labels of the n/100, n%100, c3 bit fields and c4 bits
  beyond difficulty. The exact in-game meaning of those fields (start area,
  lives, collectibles, flags) was not exhaustively mapped; the decoder is exact
  at the bit level, so this does not affect accept/reject or enumeration.

## 8. Unknowns

- The full semantic name of each decoded field other than difficulty was not
  proven; the validator was read directly, so the bit layout is certain, but the
  downstream gameplay meaning of `n/100`, `n%100`, the c3 bits and the five c4
  bits remains labeled conservatively.
- The GBC-only 4-symbol credits code `CRDT` published on 3rd party cheat indexes are a different
  SKU; it is not accepted by this 6-symbol GBA screen and was not tested on a GBC
  ROM.
- Text is tile-indexed: `strings`, raw ASCII, UTF-16, ±0x20 shifts and the
  ASCII→tile transform all failed to locate menu labels in ROM or savestate RAM.
  The visible strings were therefore enumerated on screen rather than via a text
  bank dump; no hidden text label was found by static search.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`
- Python 3 (standard library): header parse, logo scan, literal/pointer scans,
  published-code decode/encode model, space enumeration, PNG `gbAs` zlib
  decompression + savestate diffing (`/tmp/monstersinc/`)
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
- REA MCP with Ghidra 12.1.4 (raw ARM import @ 0x08000000) for function
  boundaries, xrefs and pseudocode cross-check; session closed after analysis.
- mGBA 0.x SDL under Xvfb :316 + openbox; `xdotool` XTEST input; `scrot` +
  ImageMagick crops; helper `/tmp/monstersinc/enter_code.py`.
- Web: 3rd party cheat indexes via `web.archive.org` (direct fetch 403), plus web-search checks
  of 3rd party cheat indexes and exact-string searches. Fetched pages were treated
  strictly as data.

No ROM or copyrighted assets are redistributed in this report.
