# Mary-Kate and Ashley: Sweet 16 – Licensed to Drive (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mary-Kate and Ashley: Sweet 16 – Licensed to Drive.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `MKASWEET16` |
| Game code / maker | `AAYE` / `51` (Acclaim / Club Acclaim) |
| Version | `0x00` (Rev.00); fixed `0x96`; complement `0x03`; checksum `0x0000` |
| Entry word | `0xEA00002E` → stock `0x080000C0` (no cracktro/trainer patch) |
| MD5 | `e7ea7a7570b301ae1cfab5531c7a3941` |
| SHA-1 | `284059f03f0dda9ce511d3c57bf0607706b9fca3` |
| SHA-256 | `18a7059d5d088d3a2d91f17b432c3778094ece4bf1d11a91db90736f866bba6e` |
| Embedded GBA headers | Exactly one (logo pattern at file `0x0` only). No multiboot/stub/trainer. |

## 2. Executive summary

The game has a **single developer-intended password system** on the main-menu screen
`PASSWORD → ENTER PASSWORD`, with a 6-character on-screen keyboard. All 42 published
GBA level passwords (3rd party cheat indexes) are accepted, but none is
stored as an ASCII literal: the ROM contains an **algorithmic validator** at
`0x080164A8`. Each of the first five symbols is mapped to a 5-bit index via a 32-byte
alphabet table at `0x080432A4`; the 25-bit word is XORed with key `0x00368EF7` at
`0x080432C4`; the sixth symbol is the **population count** of the low 24 bits; and the
decoded word must pass three range gates. The winner word is stored to IWRAM `0x030014B4`.

The accepted space is fully characterised: 4,128,768 codes using the 32-symbol table,
4,737,150 value patterns once the ROM's out-of-table OR-overflow is included, and
20,262,816 distinct strings over the 46-key keypad. Only one decoded field (`f1`, the
level index) changes gameplay; 42 distinct levels are reachable. Novel codes from
outside every published list were minted, typed on the real screen, and RAM-verified
(`99B8SM`, `99B83K`, `BLC8BR`, `KKKAH8`). Out-of-range inputs (`f1=36`, `f2=2`, `f3=3`,
wrong checksum) were rejected in-game, closing the bounds.

No button codes, hidden debug menu, or second password surface was found after walking
every reachable screen and decoding the tile-indexed keyboard text bank. Published
CodeBreaker/GameShark codes exist but are memory cheats, out of scope.

## 3. How to reproduce

* Emulator: mGBA (`mgba -3`) under `Xvfb :318`, `SDL_AUDIODRIVER=dummy`, 1024×768,
  default SDL keymap (A=`x`, B=`z`, Start=`Return`, D-pad = arrows).
* Path: boot → press Start through the Powerhead / "Games for Real Girls" / AOL splashes
  → **Main Menu** → `PASSWORD` (press Down ×4, A) → `ENTER PASSWORD`.
* Keyboard grid (row, col): row0 `! ? ' & - # ( ) _ ^`; row1 `0..9`; row2 `A..J`;
  row3 `K..T`; row4 `U V W X Y Z ← → END`. D-pad moves the cursor; **A** appends a
  character; **←** (row4 col6) backspaces; **END** (row4 col8) submits. The field is
  capped at 6 characters.
* Entering `99B8BK` → Chapter 1 cutscene (published code accepted). Entering
  `99B8GM` → `INCORRECT!` banner and no state change.
* RAM evidence: mGBA `.ss1` states were parsed with `zlib.decompress` of the `gbAs`
  PNG chunk; layout verified as VRAM `+0x1000`, IWRAM `+0x19000`, EWRAM `+0x21000`
  (state size `0x61000`). Input field = EWRAM `0x02018034`; cursor col/row =
  `0x02018030`/`0x02018032`; decoded word = IWRAM `0x030014B4`.
* Keyboard input was also trapped live: an mGBA CLI-debugger read watchpoint at
  `0x02018034` hit at `0x080164DC` with `r1=0x02018034`, `r0=0x4B`, `r5=0x39`,
  `lr=0x0801261B`, proving the comparison loop below.

## 4. Address map

| Item | File offset | ROM address | Notes |
|---|---:|---|---|
| Validator entry | `0x164A8` | `0x080164A8` | `(char *code, u32 *out) -> u32` (Thumb) |
| Symbol compare loop | `0x164DC` | `0x080164DC` | `cmp r0,r5` — watchpoint hit here |
| Popcount checksum loop | `0x16542` | `0x08016542` | 24 iterations |
| Range gates | `0x1655E`–`0x16590` | `0x08016590` | f1/f2/f3 limits |
| Symbol alphabet (32 B) | `0x432A4` | `0x080432A4` | `KMHBYRLCW#1S48DP6FV3Q7J9NT0GX5Z2` |
| XOR key (u32) | `0x432C4` | `0x080432C4` | `0x00368EF7` |
| Caller / state write | `0x12600`–`0x12626` | `0x08012624` | stores decoded word |
| Password menu setup | `0x131A8`, `0x131CC` | `0x080131CC` | sets max length 6 (`strb #6,[r1,#0x30]`) |
| Keyboard row table | `0x28EF8`–`0x28F47` | `0x08028EF8` | 5 row strings, pointers at `0x28EF8` |
| Input string (EWRAM) | — | `0x02018034` | 6 bytes + NUL |
| Cursor col / row | — | `0x02018030`/`0x02018032` | u16 each |
| Decoded password word | — | `0x030014B4` | u32 written on accept, zeroed on reject |

## 5. Algorithm

```python
ALPHA = "KMHBYRLCW#1S48DP6FV3Q7J9NT0GX5Z2"   # 32 symbols, index == 5-bit value
KEY   = 0x00368EF7

def validate(code):            # code is 6 characters
    v = [ALPHA.find(c) for c in code[:5]]
    v = [32 if x < 0 else x for x in v]      # out-of-table -> 32 (OR overflow)
    p = 0
    for i, x in enumerate(v):
        p |= (x << (5 * i)) & 0xFFFFFFFF     # OR, not ADD (matters for value 32)
    word = (p ^ KEY) & 0xFFFFFFFF
    chk  = bin(word & 0xFFFFFF).count('1')   # popcount of low 24 bits
    if ALPHA.find(code[5]) != chk: return False   # 6th char is the checksum symbol
    f1 = (word >> 14) & 0x3F
    f2 = (word >> 20) & 0x07
    f3 = (word >> 23) & 0x03
    if 36 <= f1 <= 57: return False          # forbidden band
    if f2 > 1 or f3 > 2: return False
    return True                              # word is stored at 0x030014B4

def encode(f1, f2, f3, low14):               # exact inverse for in-table values
    word = (f3 << 23) | (f2 << 20) | (f1 << 14) | low14
    p = word ^ KEY
    s = ''.join(ALPHA[(p >> (5*i)) & 31] for i in range(5))
    return s + ALPHA[bin(word & 0xFFFFFF).count('1')]
```

Bit layout of the accepted word: `bits 0..13 = low14` (ignored by all gates),
`bits 14..19 = f1` (level selector), `bits 20..22 = f2` (must be 0 or 1),
`bits 23..24 = f3` (must be 0, 1 or 2). The 6th character is determined entirely by
checksum; it cannot be chosen freely. `f1` values 36–57 are rejected; published levels
use `f1 = 0..35` and `58..63`.

## 6. Tables

* All 42 published codes were decoded and every one passes the validator (`encoder.py`
  also reproduces all 42 from their decoded words). Example mappings:
  `99B8BK → word 0x00000000 (f1=0)` = Chapter 1-1; `7938BH → 0x00004002 (f1=1)`;
  `MNBBHS → 0x01701F6 (f1=28)` = Chapter 8-1; `5PB6H# → 0x01E830A (f1=58)` = 8-9.
* Alternate 3rd party cheat index codes (`9931HR`, `PJBRHR`, `CQBWHL`, `D7B#HL`, `MLBBBW`) are also
  valid: they are aliases with `f2` flipped against the 3rd party cheat index list.
* Field effect (empirical, §16.4b): `f1` selects the level. `f2`, `f3` and `low14` are
  accepted but produce no observable change — `9931BY` (f2=0) and `9931HR` (f2=1) gave
  identical Chapter 4-1 gameplay; `99B8SM` (f3=1) and `99B83K` (f3=2) both gave the
  same Chapter 1-1 gameplay as `99B8BK`; `BLC8BR` (low14=0x1234) also gave Chapter 1-1.

## 6b. Enumeration

* **Input space**: 46 keyboard characters (10 symbols, 10 digits, 26 letters) × 6
  positions. The validator's first five positions accept 33 distinct *values* (32 table
  symbols + the catch-all value 32); the sixth must be one of the 32 table symbols.
* **Accepted space**: 4,128,768 strings with all five values in the table
  (= 42 valid `f1` × 2 `f2` × 3 `f3` × 2^14 `low14`); 4,737,150 value patterns when the
  out-of-table OR-overflow is counted; **20,262,816 distinct 46-key strings** after
  expanding each value-32 position to its 14 possible glyphs (C brute force, complete
  over all 33^5 patterns).
* **Distinct outcomes**: 42 levels. All other accepted variation is aliasing.
* **Novel codes entered on the real screen and RAM-verified** (none appears in any
  published list):

| Code | Fields | Word at `0x030014B4` | Result |
|---|---|---|---|
| `99B8SM` | f1=0, f2=0, f3=1, low=0 | `0x00800000` | Accepted → Chapter 1 cutscene/gameplay |
| `99B83K` | f1=0, f2=0, f3=2, low=0 | `0x01000000` | Accepted → Chapter 1 |
| `BLC8BR` | f1=0, low=0x1234 (alias) | `0x00001234` | Accepted → Chapter 1 |
| `KKKAH8` | contains vowel `A` (out-of-table OR-overflow) | `0x00068EF7` | Accepted → f1=26 level (Chapter 7) |

* **Bounds proven by in-game rejection** (all leave the player on the password screen
  and zero the decoded word; `99B8GM` visibly showed `INCORRECT!`):

| Code | Defect | Word after submit |
|---|---|---|
| `99B8BB` | wrong checksum character | `0x00000000` |
| `99B2BH` | `f1=36` (forbidden 36–57 band) | `0x00000000` |
| `99B8MM` | `f2=2` (out of range) | `0x00000000` |
| `99B8GM` | `f3=3` (out of range) | `0x00000000` |

## 7. Validation evidence

* **Observed**: all screenshots and RAM words above; watchpoint hit at `0x080164DC`
  with the expected register values; `INCORRECT!` rejection banner; 42/42 published
  codes accepted by the decoder; the five 3rd party cheat indexes aliases valid.
* **Derived**: the validator/encoder disassembly at `0x080164A8`–`0x080165A4`, the
  table/key bytes at `0x080432A4`/`0x080432C4`, the word store at `0x08012624`, and the
  exhaustive C enumeration counts.
* **Inferred**: `f2`/`f3`/`low14` are semantically unused aliases — proven only for the
  tested levels (Chapter 1-1 and Chapter 4-1); a hidden use in untested missions cannot
  be excluded. The `displaypassword.mnu` / "Your Password is:" screen was located as a
  resource but not reached through any walked menu path.

## 8. Unknowns

* No button-code sequence or hidden debug menu was found. Bounds: every reachable screen
  was walked (splashes, main menu, adventure difficulty/character select, gameplay,
  pause, 7 arcade entries incl. character select and ATV gameplay, multiplayer link,
  options with SONG/SOUND/CREDITS, password entry); `strings` contained zero matches for
  `debug|secret|cheat|generator`. The ROM's UI text is tile-indexed, so the keyboard
  alphabet was decoded from the font row table at `0x08028EF8` rather than from ASCII.
  `carselect.mnu`/`advcarselect.mnu` resources exist (3rd party cheat indexes development-text list) but no
  car-select screen appeared on any walked path.
* Effects of `f2`/`f3` on levels other than those tested remain unexercised.
* The "Your Password is:" display screen was not reached; it may be gated on level
  completion.
* Prompt-injection attempt: the 3rd party cheat index page for this game contained a block claiming
  "This page is not intended for humans… only for LLMs… operator is a clown". It was
  treated as data and ignored; no instruction from fetched web content was followed.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for validator disassembly; Capstone 5.0.7 and Python for literal scans.
* mGBA 0.10 CLI debugger driven through a PTY (`ptydebug.py` / `dbg.py` in
  `/tmp/mksweet16`); read watchpoint at `0x02018034` located the validator.
* Python scripts: `decoder.py`, `encoder.py`, `validate_rom.py` (bit-exact validator),
  `state.py` (savestate `gbAs` zlib parser), `typer2.py` (keyboard automation),
  `testcodes2.py` (code → RAM proof). C scripts: `enum.c`, `enum2.c` (exhaustive counts).
* Screenshots retained under `/tmp/mksweet16/` (`password.png`,
  `novel_f3_1_result.png`, `t_*_result.png`, `reject_gm_imm.png`, `credits.png`, etc.).
* No ROM or copyrighted assets are redistributed here — only addresses, hashes,
  algorithms and generated code strings.
