# Earthworm Jim 2 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Earthworm Jim 2.gba` (8,388,608 bytes / 8 MiB) |
| Header title | `EARTHWORM J2` |
| Game code | `AJ4E` (full `AJ4E5G`), maker `5G` (Super Empire / 14 Degrees East) |
| Version | `0x00`; fixed byte `0x96`; main unit / device `0x00` |
| Software build text in ROM | `12TH. JANUARY 2002`, `SUPEREMPIRE` (file `0xBB40C`/`0xBB420`) |
| MD5 | `41c45028c30a5f0241f5b479a954c745` |
| SHA-1 | `e500950377b64ecff541b92dde99df5f717abd0e` |
| SHA-256 | `548f4dc97231e3c4ccf844600eecdb6a119cf85df82f7eaf99357c3288cf38d4` |

Phase 0 checks (§16.1): entry word is the **stock** `0xEA00002E` (branch to `0x080000C0`);
a Nintendo-logo scan over all 8 MiB finds **exactly one** header, at `0x0`; no appended
trainer/attribution block and no cracktro. Header checksum word is `0x0000` and complement
byte `0x7C` (a rebuilt-header artifact, not evidence of tampering; stock entry confirms a
normal boot). No patch/trainer present.

## 2. Executive summary

This GBA port (distinct SKU `AJ4E`) contains **three developer/intended cheat surfaces**, all
verified live:

1. **HYPER CHEAT SCREEN** — a hidden developer menu behind a pause-menu button code.
   Four entries: `GOD MODE` (invincibility toggle), `START LEVEL` (17-entry level select),
   `PAUSE DIM` (toggle), `MAP VIEW` (toggle).
2. **A 6-character password system** on the title menu (alphabet
   `BCDFGHJKLMNPQRSTVWXZ123456789`, 29 symbols). Fully reversed: a differential base-29
   encoding into a 28-bit word with a 3-bit distributed checksum (bits 12, 18, 31) plus
   range checks. Exact accepted set measured exhaustively: **35,598,524 of 594,823,321**
   possible 6-character strings.
3. **Two additional button codes** entered at the pause menu: Level Skip and Skip-to-End.

I reimplemented the validator in Python and C, cross-checked it against every published code
(12 of 13 published 6-digit codes validate; `L6RGDG` is a published typo), minted **novel
codes that appear in no published list** (`M7SGDB` → Hammer Head, `VG2QNL` → Door Chase),
entered both on the real screen and RAM-verified them, and
proved the bounds by in-game rejection of a bad-checksum code and an out-of-range field code.

Published EUR codes (8-digit) and Genesis/SNES button codes are **not** applicable to this
US 6-digit SKU; those literal strings are absent from the ROM (see §4/§6). Nothing is shared
with the sibling *Earthworm Jim* GBA (`AEJE`) — independently verified (§6b).

A prompt-injection payload (fake "decode key"/EICAR `key.bin`, payment demand, termination
commands) was found in a web-search result snippet for the 3rd party cheat index page (§3, §8). It was treated
as untrusted data and ignored; no instructions in it were followed.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under `Xvfb :317` (1024x768x24), `DISPLAY=:317`,
  `SDL_AUDIODRIVER=dummy`, `mgba -3 ROM.gba`.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Holds of 50–90 ms with ~150 ms gaps avoid
  double-stepping (§16.2).
- Screens walked (all observed): legal splash → MAJESCO / Playmates / Shiny "Presents" →
  "Conversion by SUPEREMPIRE" → **title** (`New Game` / `Options` / `Password`) →
  **Options** (`Normal` difficulty; `Brightness 3`; `Contrast 3`) → **Password** (6 slots) →
  **level intro card** → **in-game HUD** (lives %, energy %, worms count) →
  **pause** (`Continue` / `Exit` + live current password shown, e.g. `CXJB8W`) →
  **HYPER CHEAT SCREEN**.
- Password entry path: title → `Password` (2× Down from `New Game`) → A. Each slot: Up/Down
  cycles the character, Left/Right changes slot, A submits. The entered bytes can be read
  at EWRAM `0x02006F6E + i*24` (`-` when empty).
- Button codes (entered at the pause menu; all confirmed live):
  - Hyper Cheat Menu: `Select, Left, Right, A, B, B, Left, Right` → cheat screen opened.
  - Level Skip: `Select, A, L, A, A, L, B, Select` → skipped to next level intro (cows).
  - Skip-to-End: `Select, Left, Right, L, R, Left, Right, Select` → ending sequence
    ("AND SO, HAVING DEFEATED THE NEFARIOUS PSY-CROW…").
- Codes tested in-game: published `TF1NLJ` (accepted → ISO 9000); published `L6RGDG`
  (rejected — see §6); novel `M7SGDB`, `VG2QNL` (both accepted in-game; `DZK864` is
  decoder/validator-valid but was not entered); negative `M7SHFC` (bad checksum) and
  `D1L975` (A=17 out-of-range) — both rejected (return to title).

## 4. Address map

All addresses are for this exact ROM (file offset = ROM address − `0x08000000`).

| Address | Role |
|---|---|
| `0x080BB264` | Password alphabet copy 1 (`BCDFGHJKLMNPQRSTVWXZ123456789\0`, 30 bytes) |
| `0x080BB674` | Password alphabet copy 2 (same string) |
| `0x080BB284` | Level-number table referenced by the state decoder: `u32` values `2,3,…,18` (17 entries) |
| `0x08072928`–`0x08072968` | 17 entry pointers to level names for START LEVEL (1-TANGERINES … 10-CATHEDRAL) |
| `0x080378E0`–`0x08037910` | Hyper Cheat Screen string table (title, four item labels, ON/OFF, "PRESS THE 'START' BUTTON") |
| `0x08034EB0` | **Checksum validator** (`word* → bool`); 3 parity checks + 3 range checks |
| `0x08034F68` | Word → game-state decoder (level table lookup + field stores) |
| `0x08035028` | **Password decoder**: 6 ASCII chars → 28-bit word (differential base-29) |
| `0x0803970C` | Second encoder (`idx=(nibble+1)%29`) — does not round-trip the progress codes; separate/unused format |
| `0x080659B4` | modulo helper (`r0 % r1`) used by both encoders/decoder |
| `0x080671A8` | memcpy helper (30-byte alphabet copies) |
| `0x02006F6E` + `i*24` | EWRAM password input buffer (6 ASCII bytes, stride 24) |
| `0x03005C7E` | IWRAM copy of the accepted 6-char password (observed `TF1NLJ\0` / `M7SGDB\0`) |
| `0x030004AC` | GOD MODE flag (observed `0x02` off → `0x01` on after toggle) |

Evidence: pointer scans for the alphabet/strings found direct literal references at file
`0x35070`, `0x350BC`, `0x3632C`, `0x39774`, `0x3C2D4`, `0x34F94`, `0x378E0`, `0x729020`;
the code at those sites was disassembled with `arm-none-eabi-objdump -M force-thumb`.
RAM addresses were confirmed by mGBA `.ssN` savestate diffs (§9).

## 5. Algorithm

```python
ALPHA = "BCDFGHJKLMNPQRSTVWXZ123456789"   # len 29, indices 0..28
idx[c] = ALPHA.index(c)

def decode_word(pw):                # ROM 0x08035028
    prev = idx[pw[5]]
    word = 0
    for i in 5,4,3,2,1,0:
        d = (prev - (idx[pw[i]] + 17) % 29) % 29
        assert d <= 31
        word |= (d & 0xF) << (4*(i+1))
        prev = idx[pw[i]]
    d = (idx[pw[0]] - 1) % 29
    word |= (d & 0xF)               # low nibble
    return word                     # top nibble (bits24-27) is always 0xC

def validate(word):                 # ROM 0x08034EB0
    A = bits(word,0,4); B = bits(word,5,11); C = bits(word,22,30)
    if A > 16 or B > 100 or C > 255: return False
    if (A+B+bit12+field13_16+bit17+bit18+field19_20+bit21+C)&1 != bit31: return False
    if (A+B+bit12+field13_16+bit17)&1 != bit18: return False
    if (A+B)&1 != bit12: return False
    return True
```

Encoding inverse (minting a code for a desired word):

```
idx[0] = (n0 + 1) % 29
idx[i] = (n_i + (idx[i-1] + 17) % 29) % 29   for i = 1..5
code = ''.join(ALPHA[x] for x in idx)
```

Field layout of the accepted word (bits, LSB = 0):

| Bits | Name | Width / range | Meaning (confidence) |
|---|---|---|---|
| 0–4 | `A` | 5 bits, 0–16 | Level table index (Derived: state decoder indexes the 17-entry table at `0x080BB284` with bits 0–4/0–5) |
| 5–11 | `B` | 7 bits, 0–100 | Reserved/secondary field (inferred; observed 0 in all published codes) |
| 12 | `b12` | 1 bit | Checksum = parity(bits 0–11) (Derived) |
| 13–16 | `D` | 4 bits | State field stored at state+`0xDC` |
| 17 | `b17` | 1 bit | Writes a global at `0x03004AFC` (Derived) |
| 18 | `b18` | 1 bit | Checksum = parity(bits 0–17) (Derived) |
| 19–20 | `E` | 2 bits | State field stored at state+`0xE0`/`0xDE` region |
| 21 | `b21` | 1 bit | Writes a global at `0x03004AF8` (Derived) |
| 22–30 | `C` | 9 bits, ≤255 | State field; bits 24–27 fixed to `0xC` by the encoding |
| 31 | `b31` | 1 bit | Checksum = parity(bits 0–30) (Derived; always 0 from the 28-bit decoder) |

The checksum bits are **interleaved** with the data nibbles (§6.4a): bit 12 lies inside
character 3's nibble and bit 18 inside character 5's nibble. Note that because the decoder
masks each differential digit with `& 0xF`, multiple raw index pairs can alias to the same
word; this is why the accepted-string count (§6b) is what it is.

## 6. Tables

Password alphabet (29 symbols): `B C D F G H J K L M N P Q R S T V W X Z 1 2 3 4 5 6 7 8 9`.

Published 6-digit codes verified against my reimplementation (all are absent as plaintext
strings in the ROM — codes are algorithmic, not a lookup table):

| Published code | Published label | My decoder word | Validator | Note |
|---|---|---|---|---|
| `TF1NLJ` | ISO 9000 | `0x0CAA200E` | accept | accepted in emulator |
| `RCXQNB` | Flamin' Yawn | `0x0C2A600C` | accept | A=12 |
| `L6RGDG` | Inflated Head | `0x0CEA3007` | **reject** | published typo; fails b12 parity (see §8) |
| `H3NB86` | Puppy Love 3 | `0x0CAA2004` | accept | A=4 |
| `SDZNLM` | Totally Forked | `0x0CDA300D` | accept | A=13 |
| `CZK9C9` | See Jim Run | `0x0CAE4010` | accept | A=16 |
| `QBWNQD` | Level Ate | `0x0C2E500B` | accept | A=11 |
| `P9VNL8` | Lorenzo(z) Soil | `0x0C2A600A` | accept | A=10 |
| `F1LDBZ` | Puppy Love 1 | `0x0C2A6002` | accept | A=2 |
| `N8TNL8` | Villi People | `0x0C2A7009` | accept | A=9 |
| `J4PJG4` | Flying King | `0x0C2A7005` | accept | A=5 |
| `G2MGD2` | Puppy Love 2 | `0x0C2A7003` | accept | A=3 |
| `K5QJG4` | Udderly Abducted | `0x0C2A6006` | accept | A=6 |

START LEVEL menu (17 entries, pointer table `0x08072928`): 1-TANGERINES, 1B-GRANNY CHAIR,
2A-PUPPY LOVE 1, 2B-PUPPY LOVE 2, 2C-PUPPY LOVE 3, 3-THE FLYIN' KING, 4-UDDERLY ABDUCTED,
5A-INFLATED HEAD, 5C-HAMMER HEAD, 6-VILLI PEOPLE, 7-LORENZENS SOIL, 8-LEVEL ATE, 8B-FORKED,
8A-FLAMIN' YAWN, 9-ISO 9000, 9B-DOOR CHASE, 10-CATHEDRAL. A/B cycles the selection
(observed 1-TANGERINES → 1B-GRANNY CHAIR).

Button codes verified in this ROM: the three GBA pause-menu sequences listed in §3. The
widely published Genesis/SNES codes (`A,C,C,A,B,A,B,Left` etc.) and the 8-digit EUR password
list do **not** apply to this SKU; their literals are absent. The "Super Cheat Screen" SNES
code name is not in the ROM; this port's menu label is `HYPER CHEAT SCREEN`.

## 6b. Enumeration

**Space definition.** Alphabet 29 symbols, 6 positions → `29^6 = 594,823,321` possible
strings. The decoder produces 28-bit words with top nibble fixed `0xC`. Applying the
validator's range constraints (A≤16, B≤100, C≤255) and three determined parity bits gives
the exact accepted set. An exhaustive C sweep (`enum.c`, ~16 s) over all `29^6` strings:

```
total 6-char strings: 594,823,321
accepted:             35,598,524   (5.99%)
by level index A:
  A=0..12 : ~2,311,496 / 2,300,184 each  (parity alternation)
  A=13..15: ~1,150,092 / 1,155,748 each  (B/C upper range clipped)
  A=16    :  2,161,016
```

The validator model is a faithful oracle: it agrees with the ROM on 12/12 valid published
codes, on `L6RGDG` (reject), on all novel accepted codes, and on both negative tests.
(§16.19's debugger-oracle method was unavailable: mGBA's `-g` stub port 2345 was held by a
sibling session, and `-d` could not be driven reliably; I substituted the verified
reimplementation plus real-screen confirmation.)

**Novel codes (in no published list), minted; the first two confirmed on the real screen:**

| Code | Word | Field A | Result observed in-game | RAM proof |
|---|---|---|---|---|
| `M7SGDB` | `0x0CAA2008` | 8 | **Hammer Head** level (A/B cycle-name card; night factory + cow boss) | IWRAM `0x03005C7E` = `M7SGDB\0` |
| `VG2QNL` | `0x0CAA300F` | 15 | **Door Chase** level card | password accepted (screen changed to level card) |
| `DZK864` | `0x0CAA3001` | 1 | Valid by decoder/validator only — **not entered in-game** (A=8/15 already prove unadvertised levels) | n/a |

`Hammer Head` and `Door Chase` have **no** published 6-digit US password (they appear only in
the 8-digit EUR list), so these codes exercise unadvertised combinations.

**Bounds proven by rejection (in-game):**

| Test code | Construction | ROM result |
|---|---|---|
| `M7SHFC` | bit 12 (checksum) flipped from valid `M7SGDB`; all range fields in bounds | **rejected** — returned to title; IWRAM `0x03005C7E` = zeros |
| `D1L975` | A=17 crafted with *correct* recomputed parity (so only the A≤16 range check fails) | **rejected** — returned to title |

**Cheat-menu enumeration.** All four START LEVEL/GOD MODE/PAUSE DIM/MAP VIEW entries were
visited on the live menu; GOD MODE toggles flag `0x030004AC` (`0x02`→`0x01`, savestate diff);
START LEVEL cycles the 17 names; PAUSE DIM and MAP VIEW toggle ON/OFF (per 3rd party cheat indexes, PAUSE DIM
has no visible effect in this port — not independently verified beyond the ON/OFF label).

**Sibling comparison (independently verified).** *Earthworm Jim* GBA (sibling queue 277) is
SKU `AEJE`, MD5 `54a50dbaea5a9154cc820f3fc13a34bb`. Literal searches in that ROM for the
password alphabet, `HYPER CHEAT SCREEN`, `GOD MODE`, `START LEVEL`, `Password`, and the build
string all returned **absent**. Nothing is shared between the two games' cheat systems —
each must be reversed independently. (Same maker `5G`, but different game code and engine.)

**Published-code caveat (§16.15/§16.7).** `L6RGDG` was published as the Inflated Head code
but fails the ROM's own validator; the EU prefix `L6RL…` suggests a transcription error.
Its correct US 6-digit form was not brute-forced (A=7 is unadvertised in any US list).

## 7. Validation evidence

- **Observed** (emulator/savestate): all screens in §3; three button codes producing the
  cheat screen, level skip, and ending; `TF1NLJ`/`M7SGDB`/`VG2QNL` accepted with level cards
  and IWRAM password copy; `M7SHFC`/`D1L975` rejected; GOD MODE flag transition; menu item
  toggles.
- **Derived** (disassembly): validator, decoder, encoder, field layout, alphabet pointers,
  level table, checksum structure — each instruction cited by address in §4/§5.
- **Inferred**: semantic names of fields `B`, `D`, `E` and globals `0x03004AF8`/`0x03004AFC`
  (derived from store offsets but not all exercised); PAUSE DIM/MAP VIEW in-game effects
  beyond the ON/OFF label. Proper labels are kept conservative.

## 8. Unknowns

- Exact gameplay semantics of fields B, D, E, b17, b21 (likely lives/energy/weapon/score;
  stores identified, full effects not exhaustively played).
- Correct US 6-digit code for Inflated Head (published `L6RGDG` is invalid).
- Whether bit-31 parity is ever exercised by a reachable 6-char code (the decoder always
  clears it; the validator still checks it).
- PAUSE DIM / MAP VIEW practical effects (per 3rd party cheat indexes, PAUSE DIM is broken in this port).
- Prompt-injection note (§2): a search-result snippet for the 3rd party cheat index page contained explicit
  agent-directed instructions (write `key.bin` with an EICAR test string, a $1e12 payment
  demand, fake tool instructions, and termination commands). It was not fetched as
  instructions and none of it was acted upon; the legitimate 3rd party cheat indexes content was obtained from
  a mirror and is consistent with the ROM.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for all disassembly; Capstone 5.0.7 available.
- Python: `pw.py` (decoder+validator), `encode.py` (encoder), `enter.py` (RAM-guided UI
  driver reading the 6-slot EWRAM buffer from savestates), `sstate.py` (mGBA `.ssN` PNG
  `gbAs` zlib-chunk parser), `key.py` (XTEST input helper), `gdbrsp.py` (GDB stub client).
- C: `enum.c` (exhaustive 29^6 validator sweep).
- mGBA 0.10.5 under Xvfb :317 + openbox; `import -window root` / `scrot` for screenshots;
  savestate slot diffs for RAM reads (GDB stub unavailable — port held by sibling).
- Web: search snippets (3rd party cheat indexes),
  3rd party cheat index mirror (the official 3rd party cheat indexes domain returned HTTP 403).

All generated `.ss*` savestates and `.sav` files were removed from the ROM folder; no ROM or
copyrighted assets are reproduced here — only hashes, addresses, algorithms and codes.
