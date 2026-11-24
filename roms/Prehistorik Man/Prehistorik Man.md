# Prehistorik Man (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Prehistorik Man/Prehistorik Man.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| `file` | Game Boy Advance ROM image: "PREHISTO MAN" (APHE60, Rev.00) |
| Header title | `PREHISTO MAN` (0xA0–0xAB) |
| Game code | `APHE`; maker `60` (Titus Interactive); version 0x00 |
| Header bytes | fixed 0x96 at 0xB2 OK; complement 0x63; checksum 0x0000; entry `0xEA00002E` → `0x080000C0` (stock) |
| MD5 | `6ce9bb835428a17300fd191c7b9d8ece` |
| SHA-1 | `b1731d8c326128c10ed5d4c6ddcf452a8b8ee72e` |
| SHA-256 | `d45969aac08146bf102f654c8e60dc17c954336757bd9b895e69252462dec9f6` |

Embedded-header scan (156-byte Nintendo logo at header+4) found **exactly one** header, at file 0x0. No appended trainer, no patch, no cracktro strings (`SUNHORS`, `CRC BANDIT`, `GAMESHARK`, etc. absent); tail is 0xFF padding. This is the stock retail image, not a rebuilt/patched one.

## 2. Executive summary

The GBA build has a **12-symbol password system** reached from the main menu (`PASSWORD`). It is algorithmic, not a lookup table: a 32-symbol alphabet `BCDFGHJKLMNPQRSTVWXZ0123456789:?` (5 bits per symbol) at ROM `0x0802C576`, a generator at `0x08021DE8`, a validator at `0x08021EBC`, and conversion helpers at `0x0800271C`/`0x080027B8`. A valid password carries 50 payload bits (48 semantically effective — two bits in the last group are ignored, giving 4 spellings per state); an 8-bit ASCII-sum checksum occupies two deliberately non-adjacent character slots (positions 4 and 9).

On acceptance the game writes the 0-based stage index to `0x03002CB0`, copies the entered string to `0x03004DD0`, and restores a save-state structure. Three **undocumented literal passwords** live beside the validator at `0x0802C9E4`: `BLV45670RJ` toggles bit 0 of `0x03002B40`, `CR3F?J1D:H` toggles bit 1, and `SHWNDPRT` jumps to a special cutscene/credits scene. These were confirmed on the real entry screen.

Published GBA lists were checked literally and against the algorithm: 10 of 12 distinct published codes are valid; **both** published level-4 codes (`BBDQWC8XDJBQ`, `BBLVTBSF?HB5`) are rejected by the ROM because their checksum characters are wrong. The corrected level-4 code `BBDQFC8XDJBQ` was minted and accepted (stage 3). Several "different level" codes are aliases with identical stage fields but different other payload fields.

A code absent from every published list — `BBH9?BSD6GDG` (stage 17 / level 18, exercising the literal `?` symbol) — was typed on the real on-screen keyboard, accepted, and verified in RAM (stage `0x11`). Bounds were proven by rejection: changing one checksum character (`BBH99BSD6GBH`) is rejected with no stage write and no password copy. Out-of-range stage 31 (`BBH9XBSD6GF8`) is accepted, proving there is **no stage range check** in the validator.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under `Xvfb :316 -screen 0 1024x768x24`, `SDL_AUDIODRIVER=dummy`, `mgba -3 -d <rom>`.
* Keymap (mGBA SDL defaults, verified with `KEYINPUT` at `0x04000130` = `0x03FE` while A held): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold 100–160 ms.
* Boot: ~15 s of timed splash → legal → title logo → main menu; Start advances the legal screen and the title logo. Main menu: GAME START / PASSWORD / OPTIONS.
* Password screen: from menu press Down once (cursor → PASSWORD) then A. On-screen keyboard is a 7-column grid:

  ```
  B C D F G H J
  K L M N P Q R
  S T V W X Z 0
  1 2 3 4 5 6 7
  8 9 : ?
  ```

  Cursor starts at `L`. D-pad moves between cells; A appends the symbol; B deletes one symbol. The last row has only 4 columns, so move Up before moving horizontally when entering row 4. Enter 12 symbols, then press Start to submit.
* Submitting a valid level code returns to gameplay at the decoded stage; invalid input leaves the password buffer and stage untouched.
* Helper scripts used (all in `/tmp/prehistorik/`): `mg.py` (pty debugger harness), `pwlib2.py` (`open_pw`, `goto`, `typepw`, `buf`), `pwalg.py` (encoder/decoder/checksum), `runcodes.py` (type → submit → read RAM). Example: `python3 runcodes.py novel=BBH9?BSD6GDG`.

## 4. Address map

All ROM addresses = file offset + `0x08000000`.

| Address | Kind | Meaning |
|---|---|---|
| `0x0802C508` | data | `0123456789ABCDEF` (hex display alphabet) |
| `0x0802C518` | table | ASCII-hex → nibble (indexed by `char-0x21`) |
| `0x0802C576` | data | **32-symbol password alphabet** `BCDFGHJKLMNPQRSTVWXZ0123456789:?` |
| `0x0802C596` | table | symbol-char → 5-bit value (indexed by `char-0x21`): `B..Z`→0..19, `0..9`→20..29, `:`→30, `?`→31 |
| `0x0802C5A8`, `0x0802C5B8`, `0x0802C5F0` | tables | glyph indices / cell X positions for the keyboard |
| `0x0802C9E4` | data | `BLV45670RJ\0` (hidden code 1) |
| `0x0802C9F0` | data | `CR3F?J1D:H\0` (hidden code 2) |
| `0x0802C9FC` | data | `SHWNDPRT\0` (hidden code 3) |
| `0x080026A8` | fn | hex-string encoder (4 bits/char, alphabet `0x0802C508`) |
| `0x0800271C` | fn | **base32 encoder** (`val & 31`, `val >>= 5`, reverse; alphabet `0x0802C576`) |
| `0x08002790` | fn | hex-string decoder |
| `0x080027B8` | fn | **base32 decoder** (big-endian, table `0x0802C596`) |
| `0x08021F84` | fn | `sum of raw bytes(buffer[0..n-1])` (ASCII bytes, *not* symbol values) |
| `0x08021DE8` | fn | password **generator** (called from `0x08024214`) |
| `0x08021EBC` | fn | password **validator** (called from `0x080214E2`) |
| `0x080214C8` | fn | entry handler: `strcmp` the three literals, `strlen(input)==12` gate, call validator |
| `0x08043E20` / `0x08043E3C` | text | `PASSWORD INCORRECT` / `PASSWORD` (English bank) |
| `0x08043BE4` | text | `SELECT STAGE` (exists in bank; see §8) |
| `0x03001210` | RAM | 12-byte NUL-terminated password input buffer |
| `0x03004DD0` | RAM | accepted password copied here (`strcpy` at `0x080214F6`) |
| `0x03002CB0` | RAM | stage index, u16, **0-based** (matches published GameShark stage address) |
| `0x03002BD0` | RAM | save-state struct passed to validator/generator; `+0x04` progress (20 b), `+0x10` low field+3 (3 b), `+0x18` bones (14 b), `+0x1C` f28 (5 b), `+0x24` flag (1 b) |
| `0x03002B40` | RAM | hidden-code flag word (bits 0/1 toggled by the literal codes) |
| `0x03004604` | RAM | UI/message state written on acceptance |

## 5. Algorithm

```
ALPHA = "BCDFGHJKLMNPQRSTVWXZ0123456789:?"     # 32 symbols, 5 bits
value(c) = index of c in ALPHA                  # ? = 31 (literal max symbol)

encode5(v, n) = big-endian base32 of v in n chars, 'B'-padded
decode5(s)    = big-endian base32 -> integer

# generator (0x08021DE8), inputs: stage, other, state-struct
A = encode5(state.progress20, 4)                         # chars 0..3
Bv = (state.bones14 << 6) | (state.f28_5 << 1) | state.flag1
B = encode5(Bv, 4)                                       # chars 5..8
Cv = (b3 << 7) | (stage5 << 2) | low2                    # 10 bits
C = encode5(Cv, 2)                                       # chars 10..11
ck = (sum(ASCII(c) for c in A+B+C)) & 0xFF                # 0x08021F84, x/4 helper
password = A + ALPHA[ck & 31] + B + ALPHA[(ck >> 5) & 31] + C
#             ^ position 4 (LSB)              ^ position 9 (MSB)

# validator (0x08021EBC)
if strlen(input) != 12: reject                           # caller at 0x080214D2
ck_stored = decode5(input[9] + input[4])                 # note order: MSB first
ck_calc   = sum(ASCII(input[i]) for i in 0,1,2,3,5,6,7,8,10,11) & 0xFF
if ck_stored != ck_calc: reject                          # returns 0
stage   = (decode5(input[10:12]) >> 2) & 0x1F            # 5 bits, no range check
b1      = (C >> 7) & 1
low     = (C & 3) + 3
progress20 = decode5(input[0:4])
bones14    = decode5(input[5:9]) >> 6                    # NO mask: full 14 bits
f28        = (B >> 1) & 0x1F
flag       = B & 1
# bits 8..9 of the 10-bit C group are never read (unused -> aliases)
write stage -> 0x03002CB0; write fields -> 0x03002BD0+...;
strcpy(input, 0x03004DD0); accept (returns 1)
```

The checksum deliberately sums **raw ASCII bytes**, not decoded symbol values, and is split across two non-adjacent positions. This was confirmed against 10 published codes (all match exactly) before any code was generated.

## 6. Tables

### 6.1 Symbol mapping (alphabet at 0x0802C576)

`B C D F G H J K L M N P Q R S T V W X Z 0 1 2 3 4 5 6 7 8 9 : ?`
→ values `0..31` in that order. Vowels A/E/I/O/U are excluded; `?` (31) is a real, enterable symbol (verified by code `BBH9?BSD6GDG`).

### 6.2 Published codes checked against this ROM (0xAPHE60)

| Published label | Code | Valid? | Decoded stage (0-based) | Note |
|---|---|---|---|---|
| Level 2 (games-cheats.org) | `BBC02BBNDGBG` | yes | 1 | additional published code |
| Level 4 (all sites) | `BBDQWC8XDJBQ` | **NO** | 3 | stored ck 209, computed 195 — rejected in emulator |
| Level 4 (ggmania) | `BBLVTBSF?HB5` | **NO** | 6 | stored ck 175, computed 183 — rejected; also mislabeled |
| **Corrected level 4** | `BBDQFC8XDJBQ` | yes | 3 | minted by fixing checksum LSB (`W`→`F`); accepted in emulator |
| Level 5 | `BBH9QBSD6HBV` | yes | 4 | accepted in emulator |
| Level 5 (games-cheats.org) | `BBJ1FBD8NHBV` | yes | 4 | alias: different bones/f28, same stage |
| Level 7 | `BBJQWC8ZFHB5` | yes | 6 | — |
| Level 11 | `BBS9XBSF7HCM` | yes | 10 | — |
| Level 14 | `BBXGSB4HTHH1` | yes | 13 | — |
| Level 16 | `BB38LNBTTHH9` | yes | 15 | — |
| Level 16 (ggmania) | `BB1TRB6WTHH9` | yes | 15 | alias, same stage |
| Level 20 | `BB9DCB4JCHJS` | yes | 19 | — |
| Level 22 | `BCC5XCVRTHD2` | yes | 21 | — |
| "Final level" (ggmania) | `BCFSHBPH7HD2` | yes | 21 | same stage as level 22; different progress fields |
| Novel stage 17 (not published) | `BBH9?BSD6GDG` | yes | 17 | **novel**, see §6b |

### 6.3 Undocumented literal passwords (0x0802C9E4)

| Code | Length | Observed effect (RAM / screen) |
|---|---|---|
| `BLV45670RJ` | 10 | `0x03002B40` bit0 set (observed value 1); stage and password-copy unchanged |
| `CR3F?J1D:H` | 10 | `0x03002B40` bit1 set (observed value 2) |
| `SHWNDPRT` | 8 | no flag/stage change; branches to `0x08021640` with arg 50 and displays a special cutscene/credits screen (screen capture `res_special_SHWND.png`) |

Readers of these bits were located by Thumb PC-relative literal scans: bit0 at `0x08000444`, `0x0800436E`, `0x08009520`, `0x0800971E`; bit1 at `0x0800107A`, `0x0800E78C`, `0x08013192`. Several of those branches are additionally gated on a second counter (`obj+0x28/0x2A` == 0). Exact player-visible meaning of each bit is **inferred only** (see §8).

## 6b. Enumeration

**Space definition.** 12 symbols × 5 bits = 60 bits of input (`32^12 = 2^60` strings). Composition:

| Group | Positions | Width | Meaning |
|---|---|---|---|
| A | 0–3 | 20 bits | progress word → `0x03002BD4` |
| checksum LSB | 4 | 5 bits | low 5 bits of 8-bit check |
| B | 5–8 | 20 bits | bones (14 b), f28 (5 b), flag (1 b) |
| checksum MSB | 9 | 5 bits | high 3 bits of check (top 2 bits always `B`) |
| C | 10–11 | 10 bits | low (2 b), stage (5 b), b (1 b), **2 unused bits** |

The checksum is a deterministic function of the other 50 bits, so exactly `2^50` strings are valid. Because two of the ten C-group bits are never read by the validator, these collapse to `2^48` distinct semantic states, **4 spellings each**. Position 9 can only ever be one of `B,C,D,F,G,H,J,K` (3-bit MSB), which matches every published code.

**Novel codes (not on GameFAQs, VGChartz, TCRF, ggmania, Neoseeker, cheats-dome or games-cheats.org), all typed on the real keyboard and RAM-verified:**

| Code | Field exercised | Observed RAM after submit | Result |
|---|---|---|---|
| `BBH9?BSD6GDG` | stage 17 (level 18) + literal `?` symbol | `0x03002CB0 = 0x11` | accepted |
| `BBH99BSD6GBG` | stage 1 (level 2), progress/bones of level 5 | `0x03002CB0 = 0x01` | accepted |
| `BBH9XBSD6GF8` | stage 31 — **out of published/level range** | `0x03002CB0 = 0x1F` | accepted: no range check |
| `BBDQFC8XDJBQ` | corrected level 4 (repaired published typo) | `0x03002CB0 = 0x03` | accepted |
| `BBH9WBSD6HVG` | alias: unused bit 9 of C set vs `BBH99BSD6GBG` | `0x03002CB0 = 0x01` | accepted, identical effect → proves unused-bit aliases |

For each accepted code the password copy at `0x03004DD0` changed from 0 to the entered prefix (e.g. `39 48 42 42` = `BBH9` little-endian), while rejected codes left both `0x03002CB0` and `0x03004DD0` at zero.

**Bounds proven by rejection (in-game):**

* `BBH99BSD6GBH` — identical to the accepted level-2 code except checksum LSB `G`→`H`. Typed correctly; on submit stage stayed `0x00000000`, password copy `0x00000000`. This proves the 8-bit ASCII-sum check.
* `BBDQWC8XDJBQ` and `BBLVTBSF?HB5` — two published "level 4" codes with bad checksums; both rejected with no stage write. Their corrected versions are accepted, proving the published strings are transcription errors, not an alternate format.
* `BBH9XBSD6GF8` was *not* rejected: stage 31 is representable and accepted, bounding the "out-of-range" question to the field width (5 bits) rather than game level count.

## 7. Validation evidence

* **Observed** (emulator + RAM): boot/walk of splash, legal, title logo, main menu (GAME START / PASSWORD / OPTIONS), OPTIONS (LANGUAGE=ENGLISH, SKILL=NORMAL, MUSIC=01, CREDITS, EXIT), 32-symbol password keyboard, in-game intro/cutscene after a successful submit. KEYINPUT reads confirmed the keymap. Accepted codes: stage RAM and password-copy RAM changes listed in §6b. Rejected codes: both RAM locations remain zero. Hidden codes: flag word changed to 1/2; `SHWNDPRT` produced a distinct cutscene screen.
* **Derived** (disassembly, verified against the bytes): alphabet and value table, encoder/decoder helper behavior, generator/validator field layout, checksum formula, the `strlen==12` gate, the three literal-password `strcmp`s, and the location of every reader of the hidden flag bits. The offline encoder in `pwalg.py` reproduces all 10 valid published codes and every novel code byte-for-byte.
* **Inferred**: the exact gameplay benefit gated by flag bits 0/1 (the branches at `0x08000444` etc. are real but their full downstream effects were not played through); the semantic names `progress`, `f28`, `flag`, `b`, `low` are conservative labels for fields whose writers are in the save/UI code.

## 8. Unknowns

* What bit 0 and bit 1 of `0x03002B40` actually unlock in play. Both setters and nine readers were located, but only the flag writes were exercised end-to-end.
* `SELECT STAGE` (`0x08043BE4`) exists in the string bank. The widely published stage-select button sequence (Options → Exit + hold L/Start, then Game Start + hold R/Start, pause + Select) is documented for the **SNES** version; performing it on this GBA build led to the normal intro, not a stage-select screen. No GBA-specific button code was found in the ROM, and the gate that reaches this screen was not isolated.
* Behavior of stage 31 after the RAM write (whether the level loader crashes, wraps, or shows an unreachable area) was not played past the write.
* Meaning of the 14-bit bones field, 5-bit f28 field and 1-bit flag beyond their storage addresses and effect on the checksum; they are payload, not validation.

## 9. Tooling

All artifacts in `/tmp/prehistorik/`: `mg.py` (mGBA `-d` pty harness with key/shot/RAM helpers), `pwlib2.py` (on-screen keyboard driver), `pwalg.py` (encoder/decoder/checksum model), `runcodes.py`, `ss.py` (mGBA `.ss1` `gbAs` zlib decoder), plus investigation scripts and screenshots (`res_*.png`, `sc_*.png`). System tools: `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, Python 3, mGBA 0.10.5, Xvfb, xdotool, scrot, ImageMagick. No ROM or copyrighted assets were modified or redistributed; generated `.sav`/`.ss1` files were deleted from the ROM folder and all own processes stopped by PID.

**Legal note:** only addresses, algorithms, hashes and findings are published here; no ROM content or extracted assets are included.
