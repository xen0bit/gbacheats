# Super Hornet F/A-18F (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Super Hornet F-A-18F/Super Hornet F-A-18F.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| `file` ID | GBA ROM image: "F-18 HORNET" (BF8E5G, Rev.00) |
| Header title | `F-18 HORNET` (0xA0) |
| Game code / maker | `BF8E` / `5G` (Majesco; UK Magic developer logo in intro) |
| Version / fixed byte / checksum | `0x00` / `0x96` / `0x0000` (normal rebuilt-header artifact) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, no cracktro/trainer found) |
| MD5 | `acce7ee3388d135aaa8c5ec88e568182` |
| SHA-1 | `038b533bb09845ade7b0a13c7ca9923348eb1100` |
| SHA-256 | `090713684c66bafec1bdf4e4233c332e0e7531adff07ba8c8a90e5691ec17762` |

The analysed image was byte-copied to `/tmp/superhornet/sh.gba` so that all emulator
artifacts (`.ss1`) were written into the work directory, never the ROM folder.

## 2. Executive summary

The game has a **hard-coded, closed password system** — there is no algorithmic
generator, no checksum, and no hidden/unpublished code. The entire accepted set is
**exactly 40 eight-character strings**, stored as NUL-terminated ASCII at
`0x083FAFA4..0x083FB10A`, in 9-byte stride (`8 chars + NUL`). Two are "special"
codes that set `0x030000D0` to 1 or 2; the remaining 38 are level-skip codes
(19 Novice + 19 Ace) that set the difficulty flag `0x03004830` and select a
mission. The on-screen keyboard alphabet is the 21 letters
`BCDFGHJKLMNPQRSTVWXYZ` at `0x083FB10C`.

Every one of the 40 codes is already in the published lists (3rd party cheat indexes' Novice/Ace
tables plus the two codes the game itself prints in its ending messages). The
complete validator was reversed and its whole accept set enumerated statically;
the published list matches the ROM table exactly. This is therefore a **bounded
negative for a novel password** (§6b): the space is closed and fully published,
not "unsearched".

Dynamic verification in mGBA: accepted codes produce the expected RAM flags and
screens; an out-of-set 8-letter code is rejected with no flag change. A web-published
title-screen button sequence (`U,D,L,R,L,R,B,A`) was tested on both the title and
briefing screens and produced no flag change; no button-mask table, no debug menu
strings, and no hidden gate were found in the bounded searches documented in §6b.

## 3. How to reproduce

* mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `mgba -3`.
* Default keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold 45–60 ms per press: 150 ms double-steps menus.
* Boot takes ~45 s (legal → Majesco → UK Magic → story → credits → title). A
  savestate at the title menu is supplied as `title.ss1` in the work directory;
  `mgba -3 -t title.ss1 sh.gba` starts there. In this SDL build **F1 loads** and
  **Shift+F1 saves** slot 1.
* Menu path: title → `ENTER PASSWORD` (Down once from `NEW GAME`, Start).
* Password screen: green cursor starts on `B`. D-pad moves (row/col wrap);
  **A** enters the highlighted letter; `<` deletes; `Enter`/Start submits; B
  cancels. Eight slots; entered letters are previewed above the slots.
* `enter.py` in the work directory navigates the 3×7 keyboard and submits a code.
* RAM evidence was taken by saving a state (Shift+F1) and decompressing the PNG's
  `gbAs` zlib chunk: IWRAM `0x030nnnnn` maps to raw offset `0x19000 + (addr-0x03000000)`.

## 4. Address map

| Item | Address (ROM) | File offset | Notes |
|---|---|---|---|
| Password special-code table | `0x083FAFA4` | `0x3FAFA4` | 2 strings, 9-byte stride |
| Password level-code table | `0x083FAFB6` | `0x3FAFB6` | 38 strings, 9-byte stride |
| Alphabet | `0x083FB10C` | `0x3FB10C` | `BCDFGHJKLMNPQRSTVWXYZ\0` (21 bytes) |
| Password screen / input handler | `0x0801D1D8` | `0x1D1D8` | zero-fills 8-byte buffer at `sp+0x54`; keyboard → ASCII at `0x0801D440`; key tests at `0x0801D2F6`/`338`/`370`/`3B8`/`4B4`/`4EC` |
| Special-code validator loop | `0x0801D4FA`–`0x0801D57C` | `0x1D4FA` | 2 exact 8-byte comparisons, stride 9 |
| Level-code validator loop | `0x0801D57E`–`0x0801D604` | `0x1D57E` | 38 exact 8-byte comparisons, stride 9 |
| Special flag | `0x030000D0` (RAM) | — | 1 = NHDCDKPM, 2 = LCMLFLTC |
| Difficulty flag | `0x03004830` (RAM) | — | 0 = Novice, 1 = Ace |
| Mission/work variable | `0x030047D0` (RAM) | — | 1-based; displayed password = table[(mission-1) + 19*difficulty] |
| Key state (active-high) | `0x03001B40` (RAM) | — | `~KEYINPUT & 0x3FF`; written at `0x08000D9C` |
| Password-display lookup | `0x08020BC4`–`0x08020BDE` | `0x20BC4` | `index = (mission-1) + 19*difficulty; r0 = table + 9*index` |
| "CURRENT PASSWORD: " string | `0x082A6B8` | `0x2A6B8` | title/mission-complete rendering |
| Ending messages with the two special codes | `0x082A23B`, `0x082A31A` | `0x2A23B`, `0x2A31A` | plaintext ASCII with `0A 10`/`0A 0F` control bytes |

## 5. Algorithm

Validator (derived from `0x0801D4FA`–`0x0801D604`, Thumb):

```
input = 8 ASCII bytes from the on-screen keyboard buffer (zero-filled on entry)
if input == table[0]: write 1 to 0x030000D0; sound; return 0
if input == table[1]: write 2 to 0x030000D0; sound; return 0
for i in 0..37:                      # table base 0x083FAFB6, stride 9
    if input == table_2[i]:
        difficulty = (i > 18) ? 1 : 0     # store at 0x03004830
        level0 = (i > 18) ? i-18 : i+1    # 0-based mission index returned in r0
        sound; return level0
sound("invalid"); return 0           # no flags written
```

Display of "CURRENT PASSWORD" is a pure lookup, not a generator:
`9*((mission-1) + 19*difficulty) + 0x083FAFB6`. `19*difficulty` is assembled as
`(d<<2)+d` then `<<2` then `-d` (`0x08020BCC`–`0x08020BD2`).

Keyboard input path (`0x0801D440`): a 2-D cursor `(r6,r7)` indexes the alphabet,
`index = ((r6-14)*7 - 7 + r7)/2`, clamped by the on-screen grid; the selected
character is written into the buffer and its font index (`char + 0xE0`) is drawn.

## 6. Tables

### 6.1 Special codes (table base `0x083FAFA4`, stride 9)

| Code | ROM addr | RAM effect | In-game meaning / published source |
|---|---|---|---|
| `NHDCDKPM` | `0x083FAFA4` | `0x030000D0 = 1` | Printed in the "out of this world experience" ending message (`0x082A23B`); 3rd party cheat indexes: enter then complete a mission |
| `LCMLFLTC` | `0x083FAFAD` | `0x030000D0 = 2` | Printed in the "relive your stick and rudder days" ending message (`0x082A31A`); 3rd party cheat indexes: unlimited weapons and fuel |

### 6.2 Level codes (table base `0x083FAFB6`, stride 9, 38 entries)

| # | Code | Published label | # | Code | Published label |
|---|---|---|---|---|---|
| 0 | GHYRTSLG | Novice L2 | 19 | GHKRTYXL | Ace L2 |
| 1 | BSHCHNYT | Novice L3 | 20 | STPHLYNS | Ace L3 |
| 2 | FRMRYRSM | Novice L4 | 21 | NLHRDNGM | Ace L4 |
| 3 | GLNWZRDF | Novice L5 | 22 | DNLKTCHN | Ace L5 |
| 4 | LYDDRDKQ | Novice L6 | 23 | RSSMCKBQ | Ace L6 |
| 5 | RHNNCHNT | Novice L7 | 24 | KMGCCTNJ | Ace L7 |
| 6 | VMMRGLDK | Novice L8 | 25 | MJSCBPQK | Ace L8 |
| 7 | GWNDRYCL | Novice L9 | 26 | PSSWRDST | Ace L9 |
| 8 | YDNDRYLJ | Novice L10 | 27 | QLLSRPQR | Ace L10 |
| 9 | THDDZNZX | Novice L11 | 28 | BHKRTYSX | Ace L11 |
| 10 | DDLKMKFV | Novice L12 | 29 | PKTGHTST | Ace L12 |
| 11 | NTRPRSRG | Novice L13 | 30 | CHRSHWRT | Ace L13 |
| 12 | KTHLYSHM | Novice L14 | 31 | PLSCHFLD | Ace L14 |
| 13 | DRCRNGRZ | Novice L15 | 32 | JSNHGHGZ | Ace L15 |
| 14 | SLDRSHMX | Novice L16 | 33 | NDRWNLHN | Ace L16 |
| 15 | DVDRCRDB | Novice L17 | 34 | BGFRWQYQ | Ace L17 |
| 16 | BRSCCNTY | Novice L18 | 35 | DRTYHRRY | Ace L18 |
| 17 | BDMNTYDS | Novice L19 | 36 | MNGMRCLS | Ace L19 |
| 18 | TRVCSPBV | Novice L20 | 37 | RSYTHDNF | Ace L20 |

The ROM table order for entries 11/12 and 30/31 differs from the alphabetical
order used by the published list, but the strings and labels agree.

### 6.3 Alphabet and flags

* Alphabet (`0x083FB10C`): `BCDFGHJKLMNPQRSTVWXYZ` — 21 symbols, no vowels, no `A`.
* Input length: exactly 8 characters; no terminator beyond the buffer's NUL.
* No checksum, no bit packing, no key/permutation table, no reserved bits.

## 6b. Enumeration

**Space definition.** The entry alphabet has 21 symbols and the field is 8
characters, so the representable input space is `21^8 = 37,822,859,361` strings.
The validator is *not* checksum-based: it is two literal comparison loops, so
the accepted set is a fixed table of `2 + 38 = 40` strings. There are no field
widths, checksum bits, or reserved bits to enumerate.

**Exact accept set.** The 40 accepted strings were read directly from
`0x083FAFA4..0x083FB10A` and independently confirmed by reading the two loop
bounds in the validator (`cmp r4,#1; bls` for the 2 special codes;
`cmp r4,#0x25; bls` for the 38 level codes). All 40 are in the published
3rd party cheat index list or are the two codes the game itself prints in its endings.
A ROM-wide regex scan for 8-letter runs over the 21-letter alphabet found 292
hits; exactly the 40 contiguous entries at `0x3FAFA4..0x3FB10A` are NUL-terminated
table entries, the rest are graphics/audio data or the two in-message copies.

**Novel codes.** No novel password exists: there is no encoder/decoder pair, no
generator function, and no unused table slot. The "CURRENT PASSWORD" display is a
lookup (`0x08020BC4`), not a generator. Minting a new accepted password is
impossible without patching the ROM. This is a *closed-set negative with counts*,
not an unsearched space: 40 accepted / 37,822,859,361 representable / 40 published.

**In-game acceptance and rejection proof (observed, mGBA):**

| Input | Screenshot / state | RAM after submit |
|---|---|---|
| `LCMLFLTC` | returns to title | `0x030000D0 = 2` (confirmed) |
| `NHDCDKPM` | returns to title | `0x030000D0 = 1` (confirmed) |
| `GHYRTSLG` | pre-flight briefing showing `MISSION: 2 MIGS: 5 SUBS: 2 SAMS: 0` | `0x03004830 = 0` (Novice) |
| `RSYTHDNF` | accepted as Ace campaign entry | `0x03004830 = 1` (Ace) |
| `BBBBBBBB` (out of set, valid alphabet/length) | returns to title, no mission screen | `0x030000D0 = 0`, `0x03004830 = 0` — rejected |

The `BBBBBBBB` rejection bounds the format: a syntactically valid 8-symbol code
with a wrong table value is rejected with no state change.

**Button-code negative (bounded).** The web-published title-screen sequence
`Up, Down, Left, Right, L, R, B, A` was tested from the title menu and from the
New Game briefing page with 40–45 ms holds. In both cases `0x030000D0` remained
`0`; the D-pad presses navigated the menu/briefing pages and A selected a menu
item. Searches for an 8-press mask table were run over the code region
(`0x08000000..0x08300000`) for active-high and active-low masks, 1/2/4-byte
strides, forward and reversed order — no match. No keyboard/debug-menu strings
exist in ASCII, `+0x20`, lowercase, UTF-16LE/BE or reversed encodings (the only
`DEBUG`/`MENU`-like hits are credits text and the Shin'en GAX audio banner).
The only reachable menu items are NEW GAME, ENTER PASSWORD, GAME OPTIONS and
PRACTICE LANDING (screenshots `r0.png`, `screen_options.png`,
`screen_practice.png`); no hidden entry was observed.

## 7. Validation evidence

* **Observed** — screenshots and savestate RAM reads listed in §6b; title/password/
  options/practice/briefing/gameplay/pause screens walked in mGBA; the 40 strings
  and 21-letter alphabet dumped from the ROM bytes.
* **Derived** — the two validator loops and their bounds/strides
  (`0x0801D4FA`–`0x0801D604`); flag addresses from the literal pools at
  `0x0801D570`, `0x0801D5EC`; display index formula from `0x08020BC4`–`0x08020BDE`;
  keyboard character mapping from `0x0801D440`–`0x0801D452`.
* **Inferred** — the exact gameplay effect of `0x030000D0` values 1 and 2 beyond
  their printed descriptions (the "unlimited weapons/fuel" effect was not played
  through a full mission); the published button sequence is treated as unverified,
  not proven absent in every possible timing/context.

## 8. Unknowns

* The precise gameplay effect/timing of the special-code register
  `0x030000D0 = 1` ("out of this world experience"); only the RAM write and the
  ending-message text were verified.
* Whether the published `U,D,L,R,L,R,B,A` sequence works in some other context
  (e.g. a different timing or a "PRESS START" state); no such context was reached
  in the screen walk, and no mask table was found in the bounded scan.
* Mission-complete/failure screens were decoded from the text bank
  (`0x08289xx`–`0x08292xx`) but not triggered in gameplay.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for all disassembly; Python `struct` for literal pools; `strings -t x`,
  `xxd`, `md5sum`/`sha1sum`/`sha256sum` for recon.
* Python scripts in `/tmp/superhornet`: `gba.py` (XTEST key holds),
  `nav.py` (title→password navigation), `enter.py` (keyboard driver),
  `detect.py` (green-cursor detection), `memread.py` (savestate `gbAs` zlib
  decompress + IWRAM reads), plus the one-shot scan/test scripts.
* Web recon: 3rd party cheat indexes full password list (verified literally against the ROM);
  3rd party cheat index cheat page returned HTTP 403 to direct fetches, so only its search
  snippets were used (they agree with the ROM contents).
* No ROM or copyrighted asset is redistributed; only addresses, hashes, and
  findings are published.

## 10. Legal note

No ROM image, extracted graphic, or game text asset is included in this report.
Fetched web pages and ROM strings were treated as data, never as instructions.
