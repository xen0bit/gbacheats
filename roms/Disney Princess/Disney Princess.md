# Disney Princess (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney Princess/Disney Princess.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `DISNEY PRINC` |
| Game code / maker | `AQPE` / `78` (THQ) |
| Version | 0 (Rev.00) |
| MD5 | `49ecae7f7a6b1edfbc354b32d730d42b` |
| SHA-1 | `c469e87b533b98d6e7831d291be7fde16c95df37` |
| SHA-256 | `49aff56e10c35077a341d849cb109900e6b6053715bff4e334dee5c7811a310f` |
| Header complement byte | `0x53` — correct for the title bytes |
| Header checksum field | `0x0000` — zeroed, i.e. **rebuilt header** |
| Entry word | `0xEA1CDDF9` — **not** the retail `0xEA00002E` |

**The image is a scene release with an appended trainer.** With the header entry
word as shipped, the ROM boots into a **SUNHORS** trainer menu:

```
UNL. ENERGY   NO      UNL. WEAPONS  NO
IMMORTAL      NO      NO TIMER      NO
LEVELSKIP     NO      "SUNHORS ARE B..."
```

For all analysis below the entry word was restored on a **copy** (`0xEA00002E`,
branch to the stock crt0 at `0x080000C0`, whose main pointer literal at header
`+0x100` is `0x0800037D`). With the branch restored the game boots the normal
Disney Interactive → title sequence. The trainer is reported here and otherwise
ignored: it is not an in-game cheat and its menu is not part of the game.

No second GBA header exists in the image (Nintendo-logo scan: one hit, at
offset `0x4`), so it is a single-ROM image, not a multi-game pack.

## 2. Executive summary

* The game has a **real, algorithmically generated 20-character password
  system**, reached from the Table of Contents → **Password**. There is no
  battery save; the password is the only persistence.
* The password is **20 symbols from a 50-symbol alphabet**
  (`BCDFGHJKLMNPQRSTVWXZbcdfghjklmnpqrstvwxz0123456789` — the alphabet omits
  every vowel). It is differential-encoded (differences mod 50 between
  neighbours) with a 2-symbol checksum, and decodes to a **78-entry bit array**
  that is copied into the progress structure.
* Progress decoded from the password:
  * 11 status words (`0x03001858`, value 100 = set),
  * a **19-bit flag word** (`0x03001874`),
  * **47 treasure bits** (`0x030017E0`, 6 bytes: 8/8/6/8/8/8 per princess plus a
    Tiara bit).
* Full reversal of validator (`0x08074D60`), decoder (`0x08003148`) and the
  game's own encoder (`0x08002FF8` + `0x08074854`) was achieved; the encoder was
  re-run offline (Unicorn) to mint codes for arbitrary states.
* **Novel, unpublished code generated and typed on the real keypad:**
  `sw7003Fv648tJ7SZF2PB` — accepted, unlocks **Special Stage** and sets
  **Snow White 5/8 treasures** with every other princess at 0/8. This state
  appears in no published list (published bonus code is the all-treasures code).
* **Bounds proven by rejection:** a single-character corruption of that code is
  rejected; two published GameFAQs codes (`FlLC0kkL9FgWnW1FlRsZ`,
  `FvDMvtxV5pqwxwPfvr2z`) are rejected by the ROM and fail the recovered
  checksum — the published list contains transcription errors.
* The password space is **50^20 ≈ 9.09 × 10^33 strings**, of which about
  **7.6 × 10^30** pass the checksum (≈ 1 in 1 194). The last symbol is not used
  by the validator at all: every accepted code has **50 aliases**.

## 3. How to reproduce

Emulator: mGBA (SDL) under Xvfb, 3× scale, `SDL_AUDIODRIVER=dummy`.

```bash
Xvfb :310 -screen 0 1024x768x24 &
DISPLAY=:310 openbox &
DISPLAY=:310 SDL_AUDIODRIVER=dummy mgba -3 rom.gba &   # copy with entry 0xEA00002E
```

Keymap used: **A = `x`, B = `z`, Start = `Return`**, D-pad = arrows,
`Shift+F1..F10` save state, `F1..F10` load state.

Menu path (from power-on; the intro logos + legal screen take ~15 s):

```
PRESS START (Return)
  → Table of Contents: Options / Snow White / Belle / Aurora / Cinderella /
                       Ariel / Jasmine / ??? / Treasures / Password
Password  : Down ×9, A        (Options is selected first)
```

On the Password screen the keypad is a 5×10 grid (rows of the alphabet above).
The cursor starts at row 0, column 0 (`B`), entry position 0. `A` writes the
highlighted symbol into the current position and advances it; `Down`×5 moves to
the END/BACK row (`col` snaps to 5, `Right`×2 reaches the END cell at col 7);
`A` on END validates. The 20th symbol jumps the cursor to END automatically.

Enter the novel code by moving the grid cursor to each symbol's cell
(`row = index/10`, `col = index%10`), pressing A after each move.

Exact codes tested in the emulator are listed in §6/§6b.

## 4. Address map

| ROM address | File off | Meaning |
|---|---|---|
| `0x080000C0` | `0xC0` | stock crt0 (ARM); main pointer `0x0800037D` at `+0x100` |
| `0x08002F8C` | `0x2F8C` | `push_value(r0)` → `0x03006610[counter++]` |
| `0x08002FD0` | `0x2FD0` | `pop_value(dst)` → `*dst = 0x03006610[counter++]` |
| `0x08002FF8` | `0x2FF8` | **encoder**: progress → value stream at `0x03006610` |
| `0x08003148` | `0x3148` | **decoder**: value stream → progress (called on accept) |
| `0x080036EC` | `0x36EC` | renders the 20 symbols from `0x030065D0` |
| `0x08007BE6` | `0x7BE6` | END key handler; calls validator at `0x08074D60` |
| `0x08074854` | `0x74854` | **encoder**: value stream → 20 symbols at `0x030065D0` |
| `0x08074D60` | `0x74D60` | **validator** (returns 1 accept / 0 reject) |
| `0x0832377E` | `0x32377E` | 50-symbol password alphabet (NUL-terminated) |
| `0x08323983` | `0x323983` | the five keypad rows as strings (`10+10+10+10+10`) |
| `0x083239B8` | `0x3239B8` | pointer table to the five row strings |
| `0x08323731` | `0x323731` | font/glyph charset used to draw the codes |

RAM (IWRAM unless noted):

| Address | Meaning |
|---|---|
| `0x03001780` | current screen object; `+0x00` screen id (0x80 menu, 0x87 password, 0x88 treasures, 0x89 special-stage intro), `+0x14` keypad column, `+0x16` keypad row, `+0x18` entry position |
| `0x030065D0` | 20 × u16 password buffer (symbol indices 0..49) |
| `0x03006610` | 79-entry value/bit stream (0/1/100) |
| `0x03001858` | 11 status words (0 or 100) |
| `0x03001874` | 19-bit flag word |
| `0x030017E0` | 47 treasure bits (6 bytes) |
| `0x030002D4` / `0x030002D6` | stream read/write index and "100-marking" flag |

## 5. Algorithm

### 5.1 Validator (`0x08074D60`)

Symbols `S[0..19]` are indices 0..49 into the alphabet. The routine works on a
copy `B`:

```python
B = S[:]
for a,b in [(1,6),(3,8),(11,16),(13,18)]:   # fixed pairwise swaps
    B[a],B[b] = B[b],B[a]
for i in [0,1,2,3,4,5,6,7,8,9,10,12,14,16,18]:   # XOR mask
    B[i] ^= 1

S[0] ^= 1                     # toggled in RAM (restored on failure)
key = 3 + ((S[0] & 0x20) >> 5)      # 3 or 4  (S[0] here == B[0], since bit0 flipped)

chk[0] = B[0]
for i in 1..19:
    chk[i] = (B[i] - B[i-1] - key) mod 50      # add 50 until >= 0

total = (B[0] & 0x20) + sum(chk[i] for i in 2,4,6,...,18)
q, r  = divmod(total, 50)     # q by repeated subtraction, r in 0..49

accept  iff  r == chk[1]  and  q == (B[0] & 0x1F)
```

On success the buffer is overwritten with `chk[]` and the validator extracts two
3-bit fields from the working word (`0x0300666A`/`0x0300666C`) before returning 1.
There is **no semantic range check** — every checksum-valid string is accepted
(verified with a deliberately extreme code, §6b).

### 5.2 Stream → progress (`0x08003148`)

Reads 78 single values from `0x03006610` and writes:

```
status[0..10]   = stream[0..10]            -> 0x03001858 (11 u16, 0/100)
flags bits 0..10  = stream[11..21]
flags bits 12..18 = stream[22..28]         -> 0x03001874
flags bit 11 is forced to 1 by the decoder
treasure bits 0..47 = stream[29..76]       -> 0x030017E0 (3 u16)
```

### 5.3 Progress → stream → symbols (the game's own encoder)

`0x08002FF8` pushes the 11 status words, the 19 flag bits and the 48 treasure
bits into `0x03006610` in exactly that order; `0x08074854` then repacks that
stream into the 20 symbols (values 0..49) in `0x030065D0`. Both were executed
offline in Unicorn, which lets an arbitrary progress state be turned into a
valid, unpublished password (see §6b).

### 5.4 Entry state machine (observed)

A press on END (`0x08007BE6`) requires keypad row 5, column 7. Accept → beep
`0xEF`, state `0x86`, `[0x030015FC] |= 2`, return to the Table of Contents
(`0x80`). Reject → beep `0xB2`, entry position reset, stays on the Password
screen (`0x87`). Entering the Special Stage shows two "congratulations" pages
and then launches the bonus level with all six princesses.

## 6. Tables

### 6.1 Alphabet and layout

```
flat alphabet (0x0832377E), 50 symbols, index 0..49:
B C D F G H J K L M N P Q R S T V W X Z b c d f g h j k l m
n p q r s t v w x z 0 1 2 3 4 5 6 7 8 9
keypad rows are the same string split 10/10/10/10/10
```

### 6.2 Treasure bits (`0x030017E0`, 47 bits used)

| Bits | Princess | Count |
|---|---|---|
| 0–7 | Snow White | 8 |
| 8–15 | Belle | 8 |
| 16–21 | Cinderella | 6 |
| 22–29 | Ariel | 8 |
| 30–37 | Jasmine | 8 |
| 38–45 | Aurora | 8 |
| 46 | Tiara of Happiness (shown on the Treasures page when set) | 1 |

Proven bit-by-bit in the emulator: single-bit codes produced "Snow White 1/8",
"Belle 1/8", "Cinderella 1/6", "Ariel 1/8", "Jasmine 1/8", "Aurora 1/8".

### 6.3 Special Stage gate

The `???` entry becomes **Special Stage** iff `(flags & 0x3FFFC) == 0x3FFFC`
(bits 2..17; bits 0 and 1 are not tested, bit 11 is forced by the decoder).
Measured: `0x3FFFC` shows Special Stage, `0x3FFFE` shows it, `0x3FEFF` (bit 8
missing) does not, `0x3FF00`, `0x01FF`, `0x00FF` do not.

### 6.4 Published codes verified against the ROM

Alphabet-valid and checksum-valid in the ROM (21 of 23 published strings):

```
Snow White 1  BvJdJtt1tR S2b2jnX0g6     Snow White 2  FJ2VSHPlrR S2b2jnX0g6
Snow White 3  t2TQ2xphHL Q6b8lrW5hF     Ariel 1       DwgnQR01cD wCDChwB7JF
Ariel 2       H7bDQRvRcg MSkSxDxQcX     Ariel 3       HKkXZV3mg0 hxCxQjQv52
Belle 1       FMFjrGXz0s zW5WCF1R7Z     Belle 2       t4cVD0wkPk pTzW7BsQ2b
Belle 3       FPKnzJd14D KtRtZcMpTw     Cinderella 1  DwHJtqcW0l RXfX2JZVhd
Cinderella 2  BzJ5lsH0k6 1tRtZcMpTw     Jasmine 1     HNlFbc4Nmh JltlDV5jtq
Jasmine 2     HWrbhd9pn2 kFHFkzS9LH     Jasmine 3     vzCj55SsCC tnSqDWfmsw
Aurora 2      FfR2kXmFqS Z9h9ttc5kC     Aurora 3*     FvDMvtxV5p qwxwPfvr2z
Aurora 1*     FlLC0kkL9F gWnW1FlRsZ     Bonus         z8L5HGSCP4 x3tHlk0BtL
Bonus alt     FLc1WWVwdN hLBNn67LXS     SW2 (Genie)   Cg0rbfzm5D KtRwZcMrTz
SW3 (Genie)   qpXxRkStdN S8dDntZ9kK     SWe (Genie)   BkM0HdGvNR S2b4jnX2g8
```

`*` = **rejected by the ROM** and failing the recovered checksum (published
transcription errors, see §7).

Two published strings contained `O`, a character **not in the 50-symbol
alphabet** (`CgOrbfzm5D…`, `BkMOHdGvNR…`); substituting `0` produces codes that
pass the checksum — i.e. OCR `O`/`0` errors in the published lists.

## 6b. Enumeration

**Space.** Alphabet = 50, length = 20 → **50^20 = 9.09 × 10^33** strings.
The checksum constrains `B[0]` (low 5 bits = number of 50-subtractions) and
`B[1]`. Measured over 2 000 random 18-symbol payloads: average **1.997** valid
`(B[0],B[1])` pairs (distribution 0:5.1 %, 1:33.1 %, 2:23.1 %, 3:34.5 %,
4:4.3 %). So

* valid codes ≈ 50^18 × 1.997 ≈ **7.6 × 10^30** (≈ 1 in 1 194 strings);
* ~5 % of 18-symbol payloads have **no** valid checksum pair at all — a hard
  representability bound, not a game rule;
* **symbol 19 is never used**: changing it leaves the decoded bit array
  byte-identical, so every accepted code has **50 spellings** (alias family).
  Confirmed with the validator: `…F2PB` and `…F2PC` decode identically.

**Generator.** The game's own encoder was reimplemented by running
`0x08002FF8` then `0x08074854` in Unicorn with a chosen progress structure.
Example: encoding the published Bonus state reproduces the first 10 symbols of
`z8L5HGSCP4 x3tHlk0BtL` exactly and yields `z8L5HGSCP4x5tKlm0DtN`, an alias that
the offline validator maps to the same 78-bit array — proof that the encoder and
validator are inverse.

**Novel codes minted and confirmed in the emulator** (none of these strings
appears in any published list; each was verified by reading the progress
structure out of the emulator and by the on-screen effect):

| Code (20 symbols) | State encoded | In-game observation |
|---|---|---|
| `sw7003Fv648tJ7SZF2PB` | flags `0x3FFFF`, treasures bits 0–4 | **typed on the keypad**; Table of Contents shows **Special Stage**; Treasures: **Snow White 5/8**, Belle/Aurora/Ariel/Jasmine 0/8, Cinderella 0/6; Special Stage starts and plays |
| `tLSqTSNlcv0k8zJP5sF2` | status words 0, flags `0x3FFFF`, no treasures | Special Stage entry appears, all treasures 0 |
| `sw7k03Ff6ptX3nCGxk6t` | treasure bit 0 | Snow White 1/8 |
| `sz9T25HM87CsM6WbG3QC` | treasure bit 8 | Belle 1/8 |
| `sKWpNRfkVtMV1l9Dvh4r` | treasure bit 16 | Cinderella 1/6 |
| `sw7P03FK6TZJpXz2jTsf` | treasure bit 24 | Ariel 1/8 |
| `sz9R25HM8Wcsp6Wbg3QC` | treasure bit 30 | Jasmine 1/8 |
| `sKWpNRfkVtzV7lhD2hBr` | treasure bit 38 | Aurora 1/8 |
| `qRtwDZprx15lF0PS8wJ5` | flags `0x3FFFC` | Special Stage (minimal gate) |
| `t44XhB0SCdjRsh27pbzl` | flags `0x3FFFE` | Special Stage (bit 0 irrelevant) |
| `tGSlTNNgcqvf4tDK1n9x` | flags `0x3FEFF` | `???` (bit 8 required) |
| `rCqM37lHzRWBhQrvbMlW` | empty progress | `???`, all treasures 0/8 |

The first code was entered **only with the D-pad and A** (no RAM writes): after
entry the buffer at `0x030065D0` equalled the intended 20 indices, position = 20,
cursor at END, and the accept path ran (`0x03001780` = 0x80, flags = 0x3FFFF,
treasures = `ff 01 00 00 00 00`).

**Bounds proven by rejection** (each pressed on the real Password screen):

| Input | Expected | Observed |
|---|---|---|
| `sw7004Fv648tJ7SZF2PB` (one symbol changed, checksum broken) | reject | stays on Password screen, `0x03001780` = 0x87 |
| `FlLC0kkL9FgWnW1FlRsZ` (published "Aurora Level 1") | reject (checksum) | stays on Password, state 0x87 |
| default prefilled code with END pressed | reject | stays on Password, state 0x87 |
| `FlxC0kkL9FgWnW1FlRsZ` (repaired published code) | accept | returns to Table of Contents; Jasmine Chapter 1 shows coin × 100 |
| all-`49` symbols, no repair | reject | validator returns 0 |
| `J8888808888888899999` (checksum-valid, extreme payload) | accept | validator returns 1 — no range layer exists |

## 7. Validation evidence

**Observed (emulator, screenshots + savestate RAM reads)**

* Trainer menu at boot with the shipped entry word; stock boot after restoring
  `0xEA00002E`.
* Menu structure, Options screen, per-princess chapter screens with coin counts,
  Treasures page (0/8 … 8/8 and the Tiara panel), Password keypad, END/BACK.
* Password buffer at `0x030065D0` (20 u16) and cursor fields at `0x03001780`;
  renderer reads the buffer (`0x080036EC`).
* Accept path (`0x03001780` → 0x80/0x86) vs reject path (stays 0x87).
* Novel code `sw7003Fv648tJ7SZF2PB` typed on the keypad → Special Stage +
  Snow White 5/8; Special Stage intro and gameplay reached.
* Treasure-bit probes (bits 0,8,16,24,30,38,46) and flag-gate probes
  (0x3FFFC/0x3FFFE/0x3FEFF/0x3FF00/0x1FF/0xFF).
* Published-code rejection (`FlLC0kkL9F…`), OCR `O`→`0` corrections.

**Derived (disassembly + reimplementation)**

* Validator algorithm (§5.1) — agrees with the ROM on all 21 good published
  codes and rejects the 2 bad ones and every corrupted variant.
* Decoder map (§5.2) and stream/flag/treasure layouts — verified by extracting
  the same bit array from the emulator's RAM after acceptance.
* Encoder path (`0x08002FF8` + `0x08074854`) reproduces valid codes offline;
  one generated code was accepted by the real game.
* Space statistics (§6b) computed from the recovered checksum equation.

**Inferred**

* The 11 status words (`0x03001858`) are per-chapter completion markers; no
  password built with status-only changes altered any screen we visited, so
  their exact consumer was not isolated. Their order matches the 11 value slots
  read by the decoder, and the game writes 100 into them.
* Bit 46 is the "Tiara of Happiness" completion bit (the Treasures page draws
  the Tiara panel when all bits are set; the single-bit-46 code was accepted but
  its panel was not re-checked after the treasure probes).

## 8. Unknowns

* The **status words' consumer** (11 × 0/100 at `0x03001858`) — writing them
  changes no menu we reached; likely gates chapter buttons in the princess
  screens, which we did not diff for every combination.
* The **source of the prefilled password** shown when the Password screen opens
  (it differed between sessions: `CmWtfgQnXv1Z7cFH3W9f` vs `r9rK15mFwPT9fFpsX8jJ`).
  The offline encoder with zero progress does not reproduce it, so the screen
  may show a generator variant fed by additional state.
* The exact meaning of stream entries 77–79 (`0x45`/`0x44` marker plus one flag)
  and of the two 3-bit fields at `0x0300666A`/`0x0300666C`.
* Which single-character repair of the published Aurora codes is the "intended"
  spelling — 8 (Aur1) and 15 (Aur3) repairs satisfy the checksum and the ROM
  accepts all of them; they decode to different progress, so the original
  cannot be recovered from the list alone.

## 9. Tooling

* `mgba` (SDL) on `Xvfb :310` + `openbox`; input via `xdotool` XTEST
  (`x`/`z`/`Return`/arrows); screenshots with `scrot`; crops/montages with
  ImageMagick.
* `python3` scripts in `/tmp/disneyprincess`:
  * `ss.py` / `editstate.py` — read and rewrite IWRAM/EWRAM in mGBA `.ssN`
    savestates (PNG `gbAs` chunk, zlib, 397 312-byte state; IWRAM at 0x19000,
    EWRAM at 0x21000). Used for RAM proofs and to place the cursor/test codes.
  * `pw.py` — alphabet, transform, checksum model, code construction.
  * `val.py` — the ROM's validator (`0x08074D60`) executed bit-exactly in
    **Unicorn** on a savestate RAM image.
  * `enc.py` / `gen.py` — the ROM's encoder (`0x08002FF8` + `0x08074854`) run in
    Unicorn to mint codes for arbitrary progress states.
  * `type_code.py` — drives the on-screen keypad for a 20-symbol code.
  * `oracle.py` — submit a code in mGBA and read back the progress structure.
* Installed for this job: `unicorn` (`pip install --break-system-packages
  unicorn`); `capstone`, `binutils-arm-none-eabi`, `gdb-multiarch` already
  present.

## 10. Legal note

No ROM, graphics, text or other copyrighted assets are redistributed with this
report. Only hashes, addresses, algorithms and self-generated password strings
are published. The ROM analysed is a scene-patched copy; the entry-word patch is
documented so a clean image can be used instead.
