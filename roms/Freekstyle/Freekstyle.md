# Freekstyle (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

- File: `roms/Freekstyle/Freekstyle.gba`
- Size: 8,388,608 bytes (0x800000)
- Header title: `FREEKSTYLE`; game code `BFSE`; maker `20`; version 0
- Entry word: `0xEA00002E` (stock `b 0x080000C0`)
- MD5: `36fc2b7afa77e449eb8b709bb6f9b2ee`
- SHA-1: `4375f9a9b2b767f41ba20d2e86d6ddec54c6cb3e`
- SHA-256: `a20df3295350ea82d5dbe123df1b29f8412cfc320148cceae1869bbe84f34215`

**Packaging note (Observed).** Exactly one Nintendo-logo hit, at file offset 0 (single GBA
image, no appended trainer/multiboot half). The header has been rebuilt: stored header
checksum `0x0000` (expected `0xFAEA`) and complement byte `0xD1` (sum of `0xA0..0xBD` is
`0xE7`, not `0`). The entry word is nonetheless stock. Boot shows a **scene cracktro**
("MOOGE" gear logo, scene shouts: "ACCESSION", "EURASIA", "VENOM", "HEMAGE",
"LIGHTFORCE", "RISING SUN") that hands control back to the stock crt0, which then shows
"LICENSED BY NINTENDO" and the EA Sports BIG splash. The cracktro is a release artifact,
not an in-game cheat; it is reported separately and is not part of the code system.

## 2. Executive summary

Freekstyle GBA has a developer-intended **cheat-code system** reached from
Main menu → **ENTER CODE**. The on-screen keyboard is A–Z (26 symbols) plus DEL and END;
input is capped at **6 characters**. The validator (`0x080195AC`) is a plain exact-match
loop over a **10-record table** at `0x0804A340` (records of 0x84 bytes, code-string pointer
at `+0x30`), comparing the typed lowercase-ASCII buffer at `0x03000098` with each of ten
strings using the strcmp-like routine at `0x0801D0A8`. A match selects that record's unlock
bitmasks, which are ORed into EWRAM `0x02011714+`.

The complete accepted set is: `cactus, momo, dice, back, saturn, motox, eight, spokes,
finale, code`. All ten were entered in mGBA and verified by savestate RAM diffs; each
produces a progressive, distinct unlock-mask change, and the master code `CODE` sets every
flag. The published GameFAQs/Neoseeker code **`MOTOK` is wrong**: the ROM literal is
`motox`, `MOTOK` is *rejected* in-game (zero RAM change), and `MOTOX` is *accepted*
(16 EWRAM bytes changed). `MOTOX` therefore qualifies as a generated code absent from
every published list. The console/PS2-only `FREAKY` (and `LOKSMITH`, `TRAKMEET`, etc.) is
rejected, confirming §16.11 (same title, different SKU). The novel invalid codes `ZZZZZZ`
and `MOTOK` are rejected with no flag changes, bounding the space at exactly 10 accepted
strings.

No button-code table, hidden/debug menu, or second algorithmic password system was found.
The only "password"-flavoured text besides the cheat screen is the career-mode
"your new password is:" / "the code for this league is" bank (`0x0807353F4`–`0x0807356A4`),
whose codes are the same ten table strings paired with cup names in the table at
`0x0804A340`; there is no independent checksum/generator surface.

## 3. How to reproduce

- Emulator: mGBA (SDL build), `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
- Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. **Hold keys 0.08–0.2 s**; 0.03–0.05 s taps are frequently missed by
  this game's input polling (this produced false "B does nothing" results).
- Boot path: cracktro → press Start/keys until "LICENSED BY NINTENDO" → EA BIG splash →
  attract DEMO race → press **A** once to reach Main menu.
- Menu path: Main menu → down 3 → **ENTER CODE**. Type letters with D-pad + A; DEL
  (row 3, col 5) backspaces; **END** (row 3, col 6) submits. Screen returns to Main menu on
  both accept and reject — acceptance must be proven by RAM, not by the screen transition.
- Verify unlocks: OPTIONS → VIEW CODES lists all ten codes as `CODE 1..CODE 10` in table
  order (CACTUS, MOMO, DICE, BACK, SATURN, MOTOX, EIGHT, SPOKES, FINALE, CODE). Note the
  on-screen "MOTOK"-looking glyph is actually `motox` (the font's `x` glyph); the ROM bytes
  at `0x0807374D8` are `6d 6f 74 6f 78`.
- RAM proof: save state on the ENTER CODE screen before entry (`shift+F`), enter a code,
  return to ENTER CODE, save another state, decompress the PNG `gbAs` chunk and diff the
  EWRAM region (state file offset `0x32710`–`0x327A0`, i.e. EWRAM `0x02011710`–`0x020117A0`).
  Script: `ssdiff.py` in the work dir.

Codes tested (all accepted unless noted): CACTUS, MOMO, DICE, BACK, SATURN, MOTOX, EIGHT,
SPOKES, FINALE, CODE. Rejected: MOTOK, ZZZZZZ, FREAKY.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Cheat-code record table (10 × 0x84) | `0x0804A340`–`0x0804A868` | Derived (pointer xrefs + disassembly) |
| Code strings (lowercase ASCII) | `0x080737470`–`0x080737570` | Observed (ROM bytes) |
| Validator (submit handler) | `0x080195AC` | Derived (Thumb disassembly) |
| strcmp-like comparator | `0x0801D0A8` | Derived (returns 1 on match) |
| Keyboard/input handler | `0x08019504` | Derived; key = `0x61 + row*7 + col` |
| Input buffer (7 chars + length at +7) | `0x03000098` (`0x0300009F` = length) | Observed (savestate diff) |
| Cursor row/col pairs | `0x030000A0`+ | Observed (savestate diff) |
| Unlock flags (EWRAM) | `0x02011714`+ (12-byte stride) | Observed (savestate diff) |
| Text bank (localized UI strings) | `0x080733B48`–`0x080738000` | Observed |
| Scene cracktro | boot, before stock crt0 | Observed |

File offset → ROM address: `0x08000000 + file_offset` (flat 8 MiB image, no sub-images).

## 5. Algorithm

Keyboard handler (`0x08019504`), switch on action in `r1`:

```
case 0: clear buffer, init keyboard screen
case 5: if len>0: len--; buffer[len]=0            # DEL
case 2: submit -> validator path
default: if len<=5: buffer[len] = 0x61 + row*7 + col; len++
         # A..Z -> 'a'..'z'; DEL(row3,col5) -> '{'; END(row3,col6) -> '|'
         # cap of len<=5 means max 6 characters (longest code is 6)
```

Validator (`0x080195AC`):

```
gate: word @0x03005770 must have low bytes (byte0==3, byte1==6)
r6 = 0                                  # matched index+1, 0 = no match
for i in 0..9:                          # cmp r4,#9 ; ble
    s = table[i*0x84 + 0x30]            # pointer to code string
    if strcmp_equal(input@0x03000098, s):   # 0x0801D0A8 returns 1 on match
        r6 = i+1
if r6 != 0: accept -> apply unlock masks for record r6-1
else:       reject (error sound, no flag changes)
```

The comparator at `0x0801D0A8` is a standard NUL-terminated byte-wise string compare that
returns **1** only when length and every byte match, else 0. Since the on-screen keyboard
can only produce `a`–`z`, case is never an issue; the table strings are stored lowercase.

Reimplementation: `accepted = set(table codes)` with `len(s) <= 6` and `s` composed only of
`a`–`z`; any other input is rejected.

## 6. Tables

| # | Code | Cup/league paired in table | Mask @+0x34 | Mask @+0x38 | Mask @+0x3C | Mask @+0x40 | EWRAM bytes changed on entry (Observed) |
|---:|---|---|---|---|---|---|---:|
| 1 | CACTUS | the saguaro cup | `0x00000007` | `0x00000133` | `0x00000003` | `0x00000003` | 5 |
| 2 | MOMO | the motox triple | `0x0000000F` | `0x00001377` | `0x00000007` | `0x00000007` | 8 |
| 3 | DICE | sunset valley | `0x0000001F` | `0x000137FF` | `0x0000001F` | `0x0000000F` | 10 |
| 4 | BACK | the high roller cup | `0x0000003F` | `0x00137FFF` | `0x0000007F` | `0x0000001F` | 11 |
| 5 | SATURN | inverse and reverse | `0x0000007F` | `0x0137FFFF` | `0x00000C7F` | `0x0000003F` | 15 |
| 6 | MOTOX | the def con 1 cup | `0x000000FF` | `0x137FFFFF` | `0x00000EFF` | `0x0000007F` | 16 |
| 7 | EIGHT | rocket mountain | `0x000000FF` | `0x37FFFFFF` | `0x00001EFF` | `0x000000FF` | 17 |
| 8 | SPOKES | reverse the stakes | `0x000000FF` | `0x7FFFFFFF` | `0x00007EFF` | `0x000001FF` | 19 |
| 9 | FINALE | the 1969 cup | `0x000000FF` | `0xFFFFFFFF` | `0x0001FEFF` | `0x000003FF` | 22 |
| 10 | CODE | the final challenge | `0x000000FF` | `0xFFFFFFFF` | `0x0003FFFF` | `0x000003FF` | 23 |

The masks grow monotonically down the table; `CODE` is the master code. The bit semantics
are inferred as progressive rider/track/cup unlocks (the "changed byte count" column is
the observed number of EWRAM flag bytes that differ from baseline after entry).

## 6b. Enumeration

- **Space definition.** Alphabet = 26 symbols (`a`–`z` internally, displayed as A–Z);
  length 1–6 (keyboard cap `len<=5` before append, longest table string 6). No checksum,
  no reserved bits, no packing: the validator is an exact string lookup. Total representable
  inputs `Σ(26^k, k=1..6) = 321,272,406`; accepted set size = **10**, defined exactly by the
  loop bound `cmp r4,#9 ; ble` at `0x08019612`. No 11th record exists: the next table at
  `0x0804A868` is a different structure (pointers to `0x080385xx`).
- **Validator model.** Reimplemented offline as `accepted = {'cactus','momo','dice','back',
  'saturn','motox','eight','spokes','finale','code'}` with the length/alphabet filter above.
  It agrees with the ROM on every accepted and rejected input tested below.
- **Novel code (absent from every published list): `MOTOX`.** GameFAQs, Neoseeker, ggmania
  and superdicasetruques all publish `MOTOK`. The ROM literal at `0x0807374D8` is `motox`;
  the on-screen VIEW CODES glyph is the same word (stylised `x`). Entered on the real
  ENTER CODE screen: **accepted**, 16 EWRAM flag bytes changed from baseline (e.g.
  `0x02011714: 0x01→0x7F`, `0x02011718: 0x03→0xFF`, `0x0201171E: 0x00→0x7F`). This is a
  genuine published-list correction per §16.7, and a code that appears in no published list.
- **Bounds proven by rejection.**
  - `MOTOK` (the published spelling): **rejected**, 0 EWRAM flag changes.
  - `ZZZZZZ` (novel in-alphabet, max length): **rejected**, 0 EWRAM flag changes.
  - `FREAKY` (PS2/GameCube code from GameFAQs): **rejected**, 0 EWRAM flag changes — confirms
    console codes do not apply to this GBA SKU.
  - Length cap: the handler refuses to append a 7th character (`cmp r5,#5 ; bgt`), so the
    longest published console code `LOKSMITH` (8) is not even representable on this screen.
- **Completeness.** All ten table entries were entered and accepted, with strictly
  increasing flag-change counts (5,8,10,11,15,16,17,19,22,23), matching the monotonic mask
  progression — so the whole accepted set is characterised, not merely confirmed.

## 7. Validation evidence

- **Observed (emulator/RAM).** Boot through cracktro to Demo to Main menu; every screen in
  §"Screens walked" below captured by screenshot. `CODE` typed letter-by-letter and
  submitted; VIEW CODES screen lists the ten codes; savestate `gbAs` chunks decompressed and
  diffed. Input buffer at IWRAM `0x03000098` observed as lowercase ASCII (`63 6f 64 65` for
  `code`) with length byte at `0x0300009F`. All ten codes accepted with distinct EWRAM flag
  diffs; MOTOK/ZZZZZZ/FREAKY rejected with zero flag changes.
- **Derived (static).** Code table, stride, validator loop, comparator return semantics,
  keyboard character formula `0x61+row*7+col`, input cap of 6, and the gate word at
  `0x03005770` — all read from Thumb disassembly and verified against the observed bytes.
- **Inferred.** The unlock-mask bit meanings (rider/track/cup groups) are inferred from the
  monotonic masks and the paired cup names; individual bits were not attributed one by one
  to specific riders/tracks. The "your new password is:" career screen was not triggered
  (would require completing a cup); its codes are the same table strings.

**Screens walked (all with screenshots in `/tmp/freekstyle/`):** scene cracktro
and shouts; "LICENSED BY NINTENDO"; EA Sports BIG splash; attract DEMO race; Main menu
(CAREER / SINGLE RACE / MULTIPLAYER / ENTER CODE / OPTIONS); CAREER → rider select
(NETZ, stats, quote) → cup select ("THE SAGUARD CUP", 11 cup icons); SINGLE RACE → rider
select → track select ("MONUMENTAL MOTOPLEX", "SAND, CACTI AND AIR"); MULTIPLAYER → rider
select; ENTER CODE keyboard; OPTIONS (music volume, sfx volume, VIEW CODES, CREDITS);
VIEW CODES (code 1..10); CREDITS ("FREEKSTYLE"); in-race HUD; PAUSE menu (RESUME,
SOUNDTRACK, CRY?CELL, EXIT). No further screen was reachable from any of these.

## 8. Unknowns

- Individual unlock-mask bit-to-content mapping (which exact rider/track/cup bit each of
  `+0x34/+0x38/+0x3C/+0x40` toggles) — the aggregate effect is proven; bit-level attribution
  is inferred only.
- The career "your new password is:" presentation screen was not triggered by completing
  a cup. Its code strings are the same ten table entries; no independent algorithmic
  password path was found in the ROM.
- The cracktro was not statically located (it runs before the stock crt0 and is outside the
  cheat system); it is treated as a release artifact.
- The PAUSE item rendered `CRY?CELL` was not fully decoded at the glyph level; it is present
  on every pause menu inspected and is not a cheat entry.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for the validator/keyboard disassembly; Capstone
  5.0.7 + Keystone (installed via `pip --break-system-packages`) for literal/xref scans.
- `strings -t x`, `grep -abo`, Python `bytes.find` for literal and +0x20-shifted searches.
- mGBA under Xvfb `:319`, `xdotool` XTEST key events, `scrot` screenshots, ImageMagick
  crop/montage for glyph reading.
- `gba.py` (key/shot helper), `code_entry.py` (grid navigator + code typer), `ssdiff.py`
  (PNG `gbAs` zlib chunk decompress + RAM diff). Work dir: `/tmp/freekstyle`.

Legal note: no ROM or copyrighted graphics/audio/text assets are redistributed here; only
addresses, hashes, algorithms, and the ten short code strings (already public) are published.
