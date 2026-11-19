# Peter Pan: The Motion Picture Event (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Peter Pan: The Motion Picture Event.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `PETER PAN` |
| Game code | `BPTE` |
| Maker code | `70` |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock ARM branch) |
| Fixed byte / logo | `0x96` / valid 156-byte Nintendo logo (exactly 1 hit, at file `0x004`) |
| Header checksum | `0x0000`, complement `0x40` (rebuilt-header artifact; see guide §16.1) |
| MD5 | `72901a6a1a312adb8a65edeba1bca9fa` |
| SHA-1 | `a8ed38619fcfee15d3f357d47d00b80a6332800f` |
| SHA-256 | `97a8223686d872a9be51bf99092f551b2c6bb5bf515d2daea2ed4a3e711a6a2c` |

Phase 0 notes: single GBA header, no embedded second image, no appended trainer or
cracktro. The final `0x3BFD70..0x3FFFFF` (262,800 bytes) is padded with `0x69`.
No GameShark/CodeBreaker signatures. This is a licensed Saffire/Atari GBA title;
the header is a rebuild but the code is stock.

## 2. Executive summary

The game has a fully algorithmic 9-symbol password system on the title screen
(PASSWORD). There is no fixed code table: every published code, and every code
generated here, is accepted by a checksum decoder at `0x0800156c`. The on-screen
alphabet is exactly **32 symbols** (`123456789BCD0FGH!JKLMN*PQRST$VWX`), the
 keypad is an 8×4 grid, and each symbol contributes 5 bits → a 45-bit payload.

The payload is sliced into eight fields with widths `[4,5,4,3,1,11,8,9]`.
Field 1 (5 bits) is a checksum: the ROM accepts a code iff

```
f(total - (field1 << 4)) == field1
```

where `f()` sums the 5-bit chunks of its argument at bit offsets
`{0,10,15,20,25,30,35,40}` and keeps the low 5 bits. Field 0 selects the
destination (0 = ending cutscene, 1..8 = levels 2..9, 9..15 = default/ending).
All eight GameFAQs codes were recovered from the archived cheats page, verified
literally against the algorithm, and two were entered in mGBA.

**Novel codes (not on GameFAQs/TCRF/VGChartz) were minted with the recovered
encoder and accepted on the real password screen**, with RAM proof that the
non-checksum fields change game state. Rejection of a single wrong character
proves the checksum gate. The full space is 32^9 = 35,184,372,088,832 strings,
of which 2^40 = 1,099,511,627,776 are valid (one checksum symbol per 40-bit
payload); 2,000 random payloads were all solvable by the encoder.

No hidden button code or debug menu was found. `SOUND TEST` exists as a string
and a menu-record entry but has no reachable menu item (see §8).

## 3. How to reproduce

- Emulator: mGBA (SDL, `/usr/local/bin/mgba`), `SDL_AUDIODRIVER=dummy`, Xvfb `:315`,
  `mgba -3 <rom>`. Keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, arrows = D-pad. Hold keys ≥100 ms (50 ms taps are dropped).
- Boot: Atari → Saffire → story text. Mash Start to skip to the title menu.
- Main menu: NEW GAME / PASSWORD / OPTIONS MENU. Select PASSWORD (Down, A).
- Password screen: move the cursor on the 8×4 character grid; A appends a
  character; Left from column 0 reaches DELETE / DONE / BACK; A on DONE submits.
- Codes (spaces are display grouping only): `975 V9Q 132`, `JC! 511 111`,
  `K6B M19 151`, `4WB M3! 1C1`, `5LS 15! 1M1`, `N7T 56! 1M1`,
  `*R4 F8Q 1W1`, `P85 29Q 132`.
- Scripts in `/tmp/opencode/peterpan/`: `mint.py` (encoder), `submit.py`
  (type + submit + screenshot), `ram.py` (savestate RAM reader), `typepw.py` /
  `slowtype.py` (keypad navigation), `phase0*.py` (fingerprint).

## 4. Address map

ROM addresses are `0x08000000 + file offset`.

| Address | Meaning |
|---|---|
| `0x08000000` | Header; stock entry `0xEA00002E` |
| `0x080013cc` | checksum function `f()` (returns low 5 bits of a sum of 5-bit chunks) |
| `0x0800156c` | password validator: packs input, slices fields, checks, dispatches |
| `0x08001674` | `ldr` literal holding the field-dispatch table base `0x08001678` |
| `0x08001678` | 8-entry Thumb jump table for fields 0..7 |
| `0x080017d0` | literal `0x08126ac0` (field-width table) |
| `0x080017e8` | 16-entry jump table indexed by field 0 (level/screen dispatch) |
| `0x080022a8` | `BL 0x0800156c` in the DONE handler; result tested at `0x080022ac` |
| `0x080446c0` / `0x08044840` | 64-bit `<<` / `>>` helpers used by the validator |
| `0x08126ac0` | field-width byte table `04 05 04 03 01 0B 08 09` |
| `0x0812130c`+ | string-record table; each 0x1C-byte record starts with a 32-bit pointer into text bank `0x08120000` (e.g. `0x0812137c` → `SOUND TEST` at `0x0812abf4`) |
| `0x0812a160`, `0x0812a2bc` | 40-byte glyph mapping strings `ABCDEFGHIJKLMNOPQRSTUVWXYZazbz1234567890` plus high-byte glyph indices — font data, **not** the password alphabet |
| `0x0812abf4` | ASCII `SOUND TEST` |
| `0x0812ab8c`–`0x0812abb0` | `*I*PASSWORD`, `*G*PASSWORD`, `*F*PASSWORD`, `*S*PASSWORD` |
| `0x0813e38c`–`0x0813ee19` | "I like monkeys" copypasta — developer leftover in the story text bank (data only) |
| `0x03001518` | IWRAM cursor column (0..7) |
| `0x0300151c` | IWRAM field-4 output byte |
| `0x03001520` | IWRAM **9-byte password buffer** (5-bit symbol indices) |
| `0x03001530`, `0x03001538` | IWRAM field-7 / field-6 output words |
| `0x0300153c` | IWRAM cursor row |
| `0x03001468` | IWRAM field-5 output word |
| `0x03004ae8`, `0x03004af0` | IWRAM field-2 / field-3 output |
| `0x0300155c` | IWRAM password length (must be > 8) |

Savestate layout (mGBA `.ss1` `gbAs` chunk, 397,312 bytes): VRAM `0x1000`,
IWRAM `0x19000`, EWRAM `0x21000` (used for RAM diffs).

## 5. Algorithm

```
ALPHABET = "123456789BCD0FGH!JKLMN*PQRST$VWX"   # index = row*8 + col
WIDTHS   = [4,5,4,3,1,11,8,9]                    # @ 0x08126ac0

def f(x):                                        # 0x080013cc
    s = x & 31
    for shift in (10,15,20,25,30,35,40):
        s += (x >> shift) & 31
    return s & 31

def validate(symbols):                           # 0x0800156c
    if len(symbols) <= 8: return 0
    total = sum(symbols[i] << (5*i) for i in range(9))
    fields = []; off = 0
    for w in WIDTHS:
        fields.append((total >> off) & ((1<<w)-1)); off += w
    f1 = fields[1]
    if f(total - (f1 << 4)) != f1: return 0
    dispatch_screen(fields[0])                   # 16-way table @ 0x080017e8
    write_state(fields[2:8])                     # RAM globals above
    return 1

def mint(f0,f2,f3,f4,f5,f6,f7):                  # inverse (this work)
    for f1 in range(32):
        total = pack([f0,f1,f2,f3,f4,f5,f6,f7])
        if f(total - (f1<<4)) == f1:
            return ''.join(ALPHABET[(total>>(5*i))&31] for i in range(9))
```

Note: `f()` deliberately **omits** the 5-bit chunk at offset 5, so it is not the
sum of all nine symbols. `f1` is solved by brute force over 32 values; all
2,000 random payloads tested had a solution.

## 6. Tables

Published codes (GameFAQs game id 919303, archived 2013-04-24), all satisfying
the model; fields shown in order `[f0,f1,f2,f3,f4,f5,f6,f7]`:

| Label | Code | f0 | fields |
|---|---|---:|---|
| Last Cutscene / Ending Credits | `975 V9Q 132` | 8 | `[8,12,8,4,0,71,3,17]` |
| Level 2 | `JC! 511 111` | 1 | `[1,21,0,2,0,1,0,0]` |
| Level 3 | `K6B M19 151` | 2 | `[2,11,2,1,0,5,1,2]` |
| Level 4 | `4WB M3! 1C1` | 3 | `[3,28,3,1,0,21,2,5]` |
| Level 5 | `5LS 15! 1M1` | 4 | `[4,6,5,3,0,32,2,10]` |
| Level 6 | `N7T 56! 1M1` | 5 | `[5,13,6,3,0,41,2,10]` |
| Level 7 | `*R4 F8Q 1W1` | 6 | `[6,19,7,4,0,59,3,15]` |
| Level 8 Final Level | `P85 29Q 132` | 7 | `[7,15,8,4,0,64,3,17]` |

`975 V9Q 132` in the emulator shows the "NEVERLAND..." final-level map, not an
immediate credit roll — the published label is approximate. The immediate
ending text ("ALL CHILDREN GROW UP. EXCEPT ONE.") is produced by `f0 = 0`.

Field consumers (Observed/Derived from the dispatch handlers):

| Field | Width | Consumer |
|---|---:|---|
| f0 | 4 | 16-way dispatch `0x080017e8` → destination screen/level |
| f1 | 5 | checksum only (not written to state) |
| f2 | 4 | `0x03004ae8 = (f2<<3)+16` (observed 0x38 vs 0x10) |
| f3 | 3 | `0x03004af0 = f3` |
| f4 | 1 | `0x0300151c = f4` (0 in every published code) |
| f5 | 11 | transformed into `0x03001468` (0x43ad0 vs 0xe10) |
| f6 | 8 | `0x03001538 = f6` (4 vs 0) |
| f7 | 9 | transformed into `0x03001530` (0xc8 vs 0) |

## 6b. Enumeration

- **Space**: 9 positions × 32 symbols = 32^9 = 35,184,372,088,832 possible
  strings. Field layout is 40 payload bits (4+4+3+1+11+8+9) plus a 5-bit
  checksum = 45 bits. For every 40-bit payload tested (2,000 random draws) the
  encoder found exactly one usable `f1`, so ≈2^40 = 1,099,511,627,776 codes are
  valid. `f4` and high values of `f0` are not semantically range-checked.
- **Novel code 1** — `1C! 511 111` (`f0=0`, other fields borrowed from Level 2,
   checksum re-solved to `f1=20`). Not in any published list. Entered on the real
   password screen: **accepted**, displays the ending cutscene text. Screenshot
   `submit_result_1Cx511111_3.png`.
- **Novel code 2** — `2VK MB1 292` (`f0=1`; `f2=5, f3=2, f5=77, f6=4, f7=20`,
   `f1=26`). Not published. Entered on the real screen: **accepted**, starts
   Neverland (L2) with changed state: RAM `0x03004ae8=0x38`,
   `0x03001538=0x0004`, `0x03001530=0x000000c8`, `0x03001468=0x00043ad0`,
   versus published `JC! 511 111` giving `0x10`, `0x0000`, `0x00000000`,
   `0x00000e10`. Screenshot `submit_result_2VKMB1292_3.png`.
- **Novel code 3 / bound test** — `RG! 511 111` (`f0=9`, outside the documented
   0..8 range, `f1=29`). Entered: **accepted** → ending/default screen. This
   proves the validator has no semantic range gate on `f0` beyond the checksum;
   the 4-bit field simply indexes a 16-entry dispatch whose 10..15 entries fall
   through to "accept with no level set".
- **Rejection / checksum bound** — `JC! 511 112` (published L2 with the last
   symbol changed, checksum not re-solved). Entered: **rejected**, game remains
   on the PASSWORD screen (`submit_result_JCx511112_3.png`). A one-symbol change
   is therefore not sufficient; the checksum layer is the sole gate.
- Published codes verified against the ROM: all 8 pass the checksum model;
  `JC! 511 111` and `975 V9Q 132` were additionally entered in the emulator and
  observed to start the level flow.

## 7. Validation evidence

- **Observed**: screens enumerated by screenshot (boot logos, story, title,
  password keypad, options, in-game, pause, level intro, ending); novel and
  published codes accepted/rejected on the password screen; RAM values read from
  decompressed `.ss1` `gbAs` chunks; keypad symbol values read at
  `0x03001520`; length at `0x0300155c`; savestate RAM diffs isolating those
  addresses.
- **Derived**: validator algorithm, field widths, checksum formula, dispatch
  table, encoder; all 8 published codes satisfy the formula; 2,000/2,000 random
  payloads solvable.
- **Inferred**: semantic names of fields 2..7 (lives/coins/time/etc.) are based
  on the RAM globals they write and observed value changes, not on in-game HUD
  labels; the "0 = ending" mapping of field 0 is inferred from the dispatch
  table and the observed cutscene, not from a named constant.

## 8. Unknowns

- `SOUND TEST` (`0x0812abf4`, record `0x0812137c`) and `SOUND MENU`
  (`0x0812abe8`) exist in the offset table but no menu item on title, options,
  or pause exposed them; no direct 32-bit pointer to the record was found in a
  literal scan. Treated as cut/unused text, not a reachable debug screen.
- `*I*/*G*/*F*/*S*PASSWORD` at `0x0812ab8c`–`0x0812abb0` appear to be
  language/variant labels; their selector was not identified.
- Button-code probing at the title (L+R+Start → soft reset to Atari logo;
  Select+L+R; Konami sequence; A+B+Start) produced no hidden screen.
  `Select+L+R` is documented in-game as SLEEP MODE and was not treated as a cheat.
- Exact gameplay meaning of fields 5 and 7 (complex transforms in the handler)
  was not mapped to HUD values.

## 9. Tooling

Installed/used: `binutils-arm-none-eabi` (`arm-none-eabi-objdump -M force-thumb`),
`mgba` (SDL + `-d` pty debugger, `-t` savestates), `xvfb`/`openbox`/`xdotool`/
`scrot`/ImageMagick, Python 3 (`pty`, `zlib`, `struct`), `gdb-multiarch`.
Web: GameFAQs cheats page recovered via `web.archive.org` CDX + snapshot.
Fetched page content was treated strictly as data; no instructions in it (nor in
the ROM's "I like monkeys" text) were executed. No ROM or copyrighted assets are
reproduced in this report; only hashes, addresses, algorithms and generated
codes are published.
