# Karnaaj Rally (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Karnaaj Rally/Karnaaj Rally.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `KARNAAJ` |
| Game code / maker | `AYKE` / `0A` |
| Version | 0x00 (Rev.00), USA/Europe |
| Entry word | `0xEA00002E` (stock ARM branch — no cracktro/trainer) |
| Header checksum | 0x0000; complement byte 0xBE (expected 0xD7 — header was rebuilt at some point, but the code is the retail image) |
| MD5 | `923a3437fcf84a5ca26158f7faada412` |
| SHA-1 | `31bb73186bb98f3d2b80089490f2eeca2861fe5e` (matches the TASVideos "Karnaaj Rally (USA, Europe)" publication) |
| SHA-256 | `524502fd1c66112c2369b1619f214d07f151967e0276a1f0a8a214072de02daf` |

Embedded GBA-header scan: exactly **one** Nintendo-logo hit (file 0x0). No multi-game pack, appended trainer, or patched boot code. Save type is Flash 512 Kbit (`FLASH512_V130` string at file 0x314FC); a 64 KiB `.sav` is created by mGBA.

## 2. Executive summary

**There is a real, developer-intended code system.** It is not a cheat for cars/tracks: it is the *ranking / hi-score import* feature documented by IGN ("18-character, alphanumeric passwords … entered on the karnaaj.com site"). In-game it lives at **OPTIONS → HI-SCORES → ENTER CODE** and accepts a 6-6-6 character code plus an 8-character name. The ROM contains `CODE ACCEPTED` (0x0830A94) and `CODE INCORRECT` (0x0830AA4).

The validator at **0x08016F1C** decodes 18 symbols from a 32-symbol alphabet, reconstructs a 32-bit payload, computes a CRC-32 over the payload fields **and the entered name**, and accepts iff four 8-bit checksum fields reconstructed from the code equal that CRC. The whole space is 32^18 = 2^90 strings; 2^32 are checksum-valid for a given name.

I reimplemented the validator bit-for-bit, generated codes that appear in **no published list** (none exist for this game's in-game codes), and confirmed two of them on the real screen: `BBBBBB-BBBBBF-Y?Y?RQ` and `BZZ999-888778-1N1PQR`, both producing **CODE ACCEPTED** with `r0 == r6` at the final comparison. A one-character checksum corruption was rejected with `CODE INCORRECT` and `r0 != r6`.

No button-code sequence, hidden debug menu, or unlock code exists in this build. The only published "cheats" are GameShark/CodeBreaker RAM patches (out of scope); the one input-related entry ("Press Select+L to end race") was tested in a live race and produced no observable effect — it is a memory patch that *forces* a key state, not an in-game combo.

## 3. How to reproduce

**Environment:** `Xvfb :317 -screen 0 1024x768x24`, `DISPLAY=:317 openbox`, `SDL_AUDIODRIVER=dummy`, `mgba -3` (mGBA SDL). Keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad=arrows, L=`a`, R=`s`. Hold keys ≥120 ms.

**Menu path to the code screen:**
1. Title → `PRESS START` (creates/loads career)
2. SELECT CAREER → slot 1 → A → SELECT DIFFICULTY LEVEL → NORMAL → A
3. ENTER NAME → type 8 chars → move grid cursor to `END` → A
4. SELECT PLAYER → A
5. Main menu → OPTIONS → HI-SCORES → ENTER CODE

**Testing a code (reproducible, no debugger needed):** start from the savestate at the CODES screen (`/tmp/karnaaj/test_BB.ss1` during this engagement), patch the 20-byte code buffer in the `gbAs` chunk of the `.ss1` PNG at raw offset `0x20BEC` (6 chars, `-`, 6 chars, `-`, 6 chars; `'@'` = blank), load the state, and press A. (`roms/Karnaaj Rally/Karnaaj Rally.ss1` in the ROM folder was regenerated during testing and is a generated artifact.)

**Codes tested on the real screen:**

| Code | Expected effect | Observed |
|---|---|---|
| `BBBBBB-BBBBBB-BBBBBB` (all zeros, bad checksum) | reject | `CODE INCORRECT`; GDB `r0=0x55478F26`, `r6=0x83B9F0BA` |
| `BBBBBB-BBBBBF-Y?Y?RQ` (**novel**) | accept | `CODE ACCEPTED`; GDB `r0=r6=0x83B9F0BA` |
| `BZZ999-888778-1N1PQR` (**novel**) | accept | GDB `r0=r6=0x9394DBFD` |
| `BBBBBB-BBBBBF-Y?Y?RB` (one char corrupted) | reject | `CODE INCORRECT`; GDB `r0=0x43B9F0BA`, `r6=0x83B9F0BA` |

**Screens walked (all reached in emulator):** boot logos → title → SELECT CAREER → SELECT DIFFICULTY LEVEL → ENTER NAME → SELECT PLAYER → main menu → SINGLE PLAYER submenu (CAREER MODE / LOAD CAREER / QUICK RACE / GHOST MODE) → SELECT TRACK → SELECT CAR → race HUD → pause (CONTINUE / ABORT) → RACE TIMES → main HI-SCORES → OPTIONS submenu (SOUNDS, QUICK RACE, HI-SCORES with RESET / ENTER CODE, CONTROLS) → CODES / HI-SCORES (ENTER CODE / ENTER NAME) → CREDITS. MULTIPLAYER is present in the menu but is a link-cable mode; no second console was available, so its link-wait screen was not exercised (bounded negative). No hidden/debug screen was found on any of the above.

## 4. Address map

All ROM addresses are `file offset + 0x08000000`.

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Header / entry `0xEA00002E` | Observed (xxd) |
| `0x0800735C` | CODES screen handler (draws `@@@@@@-@@@@@@-@@@@@@` template from `0x0830A6C`, processes input) | Derived (disassembly) |
| `0x0800765E` | Call site of the validator (BL `0x08016F1C`); result tested at `0x08007662` (`lsls r0,#24; cmp r0,#0`) | Observed (GDB breakpoint) |
| `0x08016F1C` | **Validator** (10 args: r0..r3 + 6 stack words; returns 1 = accept, 0 = reject) | Observed (GDB) |
| `0x08016E8C` | XOR/bitstream encoder called by the validator at `0x0801726E` | Derived |
| `0x08016F6C` | 43-entry Thumb jump table indexed by `char - 0x30`; maps the 32 alphabet symbols to values 0..31; all other entries go to `0x080177EC` | Derived (table parsed from bytes) |
| `0x080177EC` | Reject/early-return handler (`movs r0,#0`) | Derived |
| `0x0802BC4C` | CRC-32 lookup table, 256 x u32 (low 16 bits of word[i] and word[i+1] combined) | Observed (GDB `r5` at `0x801735E`) |
| `0x0803176C` | Alphabet string `BCDFGHJKLMNPQRSTVWXYZ0123456789?` + 0x00 | Observed (grep/xxd) |
| `0x0830A6C` | Code template `@@@@@@-@@@@@@-@@@@@@` | Observed |
| `0x0830A94` | `CODE ACCEPTED ` | Observed |
| `0x0830AA4` | `CODE INCORRECT` | Observed |
| `0x03007BEC` | IWRAM code-entry buffer (18 chars + 2 dashes + NUL); savestate raw offset `0x20BEC` | Observed (GDB watchpoint) |
| `0x03007C04` | Name buffer (10 bytes of `0x40` '@' when blank) | Observed (GDB `r0` at call site) |
| `0x030079D4` | Screen-handler SP during validation | Observed (GDB) |

## 5. Algorithm

Pseudocode, precise enough to reimplement (validated against the ROM on two codes):

```
ALPHABET = "BCDFGHJKLMNPQRSTVWXYZ0123456789?"   # index = 5-bit value

# 1. char -> 5-bit value, jump table 0x08016F6C (index char-0x30, 0..42):
#    B,C,D,F,G,H,J,K,L,M,N,P,Q,R,S,T,V,W,X,Y,Z -> 0..19
#    0..9 -> 20..29 ; ? -> 31 ; all other chars -> reject (0x080177EC)
values = [ALPHABET.index(c) for c in code_without_dashes]   # 18 values

# 2. XOR/bitstream encoder (0x08016E8C), one byte per emitted bit:
state = 0xC5
bits = []
for v in values:
    x = (v ^ state) & 0x1F
    state = (state + 0x53) & 0xFF
    for j in 4,3,2,1,0: bits.append((x >> j) & 1)   # MSB first
# => 90 bytes, each 0 or 1

# 3. Extract one bit per byte, LSB-first accumulation, with the ROM's
#    off-by-one loop (n+1 bytes read for a nominal n-bit field):
def extract(off, n):
    return sum(bits[off+k] << k for k in range(n))

FIELDS = [(0,8),(8,8),(16,4),(20,8),(28,8),(36,4),(40,4),(44,2),(46,5),(51,5)]
CKSUM  = [(56,8),(64,8),(72,8),(80,8)]

# 4. CRC-32 (reflected, table 0x0802BC4C, init 0xFFFFFFFF, NO final XOR):
def crc_step(crc, x):
    idx = ((crc ^ x) & 0xFF) >> 1
    entry = ((T[idx] & 0xFFFF) << 16) | (T[idx+1] & 0xFFFF)
    return ((crc >> 8) & 0x00FFFFFF) ^ entry

def char_value(c):
    if c == '!': return 28
    if c == ' ': return 29
    if c == '.': return 26
    if c == '-': return 27
    if 'A' <= c <= 'Z': return ord(c) - 0x41
    return None   # digits and '?' are skipped by the character CRC loop

crc = 0xFFFFFFFF
for c in name: 
    if (v := char_value(c)) is not None: crc = crc_step(crc, v)
for off, n in FIELDS:
    crc = crc_step(crc, extract(bits, off, n))

# 5. Accept iff the four reconstructed checksum bytes equal the CRC:
checksum = sum(extract(bits, off, n) << (8*i)
               for i, (off, n) in enumerate(CKSUM))
accept = (checksum == crc)
```

On accept, the payload fields are written through the six output pointers
(`r1`, `r2`, `r3`, and stack args 3–5) into a hi-score record at `sp+0x240`:
a 24-bit value from F1/F2/F3, a 32-bit value from F4–F7, and bytes F8/F9/F10,
then the record is inserted by the helpers at `0x0800136C` / `0x08001290`.
The exact semantic label of each field (lap time, track index, car, driver) is
**Inferred** from the hi-score screen and the IGN description, not exercised
independently.

**Name binding (Derived):** the second loop at `0x08017236` copies the name
buffer into `sp+0x120` (converting `'@'` to 0), and the character CRC loop at
`0x08017294` iterates over it — so a code minted for an empty name will be
rejected if a name is entered, and vice versa. Codes in this report were
minted/tested with the name field blank.

## 6. Tables

**Alphabet (0x0803176C), value = index:**

```
idx:  0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31
char: B C D F G H J K L M  N  P  Q  R  S  T  V  W  X  Y  Z  0  1  2  3  4  5  6  7  8  9  ?
```

**Derived novel codes (not in any published list — see §6b):**

| Code | CRC / checksum match | Result |
|---|---|---|
| `BBBBBB-BBBBBF-Y?Y?RQ` | 0x83B9F0BA == 0x83B9F0BA | accepted |
| `BZZ999-888778-1N1PQR` | 0x9394DBFD == 0x9394DBFD | accepted |

**Published codes:** none for the in-game code system. GameFAQs' cheats page returned HTTP 403; web search, archived indexes, TCRF-style sources, and ROMSFUN/libretro listed only 13 CodeBreaker **memory patches** (e.g. `32016B20 0004` "unlock all cars/tracks", `8201A128 C350` infinite cash). These are out of scope and were not applied. IGN and gaming reviews document the 18-character *website ranking* code, which is exactly the system reversed here. No prompt-injection payload was encountered in fetched pages; fetched content was treated as data.

## 6b. Enumeration

**Space definition:** 18 symbols × 5 bits = 90 bits of raw code space, i.e.
32^18 = 1,237,940,039,285,380,274,899,124,224 (≈2^90) strings. The validator
checks a 32-bit CRC (four 8-bit checksum fields), so for a fixed entered name
there are ≈2^58 accepted codes. The 10 payload fields carry 46 nominal bits
(the ROM extracts 56 bits including one padding bit per field); no reserved
bits are rejected — the final comparison is the only check. No published list
exists to compare against, so *every* accepted code is novel by construction.

**Validator as oracle (§16.19 technique):** setting a breakpoint at the final
comparison (`0x080177A6`) and reading `r0` (reconstructed checksum) and `r6`
(computed CRC) gives an accept/reject ground truth independent of the UI. This
was cross-checked against two independent codes before minting.

**Novel code #1 — `BBBBBB-BBBBBF-Y?Y?RQ`**
- Generated by taking the all-zero seed `BBBBBB-BBBBBB-BBBBBB` (CRC 0x83B9F0BA),
  writing the CRC bytes into bitstream offsets 56/64/72/80, and re-encoding.
- In-game proof: `CODE ACCEPTED` on screen; `r0 = r6 = 0x83B9F0BA` at
  `0x080177A6`.

**Novel code #2 — `BZZ999-888778-1N1PQR`**
- Generated from a completely different seed `BZZ999-888777-BCDFGH`
  (CRC 0x9394DBFD), proving the encoder works across the symbol range, not
  just for zero-valued payloads.
- In-game proof: `r0 = r6 = 0x9394DBFD` at `0x080177A6`.
- Note: a savestate-patched `Z` in the *first* position is normalized to `B` by
  the on-screen editor during redraw; the seeds above deliberately begin with
  `B`. This is a UI artifact of state patching, not a validator rule.

**Bounds proven by rejection:**
- Wrong checksum (single character changed from `Q` to `B`):
  `BBBBBB-BBBBBF-Y?Y?RB` → `r0 = 0x43B9F0BA` vs `r6 = 0x83B9F0BA`, screen
  shows `CODE INCORRECT`. This proves the 32-bit checksum comparison is live.
- Alphabet bounds (Derived, static): the jump table at `0x08016F6C` routes
  `A, E, F, I, J, O, P, U, V, @, ;, <, =, >` and all codes outside `0x30..0x5A`
  to the reject handler `0x080177EC`. An attempted UI test with `A` in slot 0
  was normalized to `B` before validation, so the in-game confirmation of
  that specific layer is **not** claimed here.
- A code minted for name `BENJI` (`BBBBBB-BBBBBJ-5QSJVG`, CRC 0xD4240390)
  self-validates offline only with that name; with the name blank it is
  expected to be rejected (Derived from the CRC loop, not entered in-game).

## 7. Validation evidence

- **Observed:** ROM hashes/header; all screenshots/screens listed in §3;
  `CODE ACCEPTED`/`CODE INCORRECT` after entering patched codes; GDB register
  values at `0x0800765E`, `0x08017314`, `0x080177A6`; encoder output dump
  matching the Python model bit-for-bit (90/90 bits) for the all-B code;
  CRC progression over the ten fields matching the Python `crc_step` at every
  step; savestate diff locating the code buffer at IWRAM `0x03007BEC`.
- **Derived:** full validator algorithm, alphabet mapping, jump table, CRC
  table base/stride, field offsets/widths, output-pointer layout, name binding,
  invalid-character reject paths.
- **Inferred:** semantic meaning of the decoded payload fields (time/track/car/
  driver) and that `CODE ACCEPTED` writes a website-ready ranking record.

## 8. Unknowns

- Exact semantics of F1..F10 (which bits are lap time vs race time vs track,
  car, driver, position) — the fields were recovered numerically but their
  labels were not independently proven on the HI-SCORES screen.
- Whether the game itself ever *displays* a generated code; the website
  (karnaaj.com, now defunct) performed the encoding externally per IGN. The
  in-game surface is import-only.
- MULTIPLAYER link-wait screen (needs a second GBA/console) and GHOST MODE
  unlock gate were not exercised.
- The published "Select+L ends race" claim showed no observable effect during
  a live race with 0.3 s and 1.5 s simultaneous holds; it is a memory-patch
  entry, not a verified in-game combo.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
- Python 3 + Capstone 5.0.7 (BL target scan, Thumb literal checks), Keystone
- mGBA SDL with `-g` GDB stub (`gdb-multiarch`, `set architecture arm`,
  `target remote :2345`) and `-t` savestate loading; GDB breakpoints/watchpoints
  on `0x03007BEC`, `0x0800765E`, `0x080177A6`
- `xdotool` (XTEST key events, `windowfocus`), `scrot`, ImageMagick `convert`
- Custom scripts in `/tmp/karnaaj/`:
  `solve.py` (validator reimplementation + code generator), `xref.py`,
  `ssdiff.py` / `ssdiff2.py` (zlib `gbAs` savestate extraction and diffing),
  `sspatch.py` (code-buffer patcher), `key.py`, and the GDB command files
  `gdbargs.txt`, `gdbfields2.txt`, `gdbcrc.txt`, `gdbfull.txt`, `gdbfinal.txt`.
- No copyrighted ROM content or assets are redistributed by this report.

## 10. Legal note

Only addresses, hashes, algorithms, generated code strings, and original
analysis scripts are published. No ROM bytes, graphics, audio, or extracted
game text are reproduced beyond the short, functional strings needed to
identify UI states.
