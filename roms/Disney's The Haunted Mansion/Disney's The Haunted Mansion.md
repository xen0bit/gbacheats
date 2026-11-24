# Disney's The Haunted Mansion (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Disney's The Haunted Mansion.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `HAUNTEDMANSI` (0x00A0) |
| Game code | `ALIE` |
| Maker code | `6S` (TDK Mediactive) |
| Software version | 0 (`0xBC`) |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| Nintendo logo | intact at file offset 4 |
| Complement byte | stored `0x2C`, computed `0x28` |
| Header checksum | stored `0x0000`, computed `0x05D4` |
| MD5 | `e10c33761a85410bb894696ae03f22d0` |
| SHA-1 | `67ed68eeb1d737413f3b5cd1da6c29a3e29ceee4` |
| SHA-256 | `2cddcf7aa073bb3ead2b7ad45cee76fb5ae9408935ac9d15b9de338fe9fc600f` |

The entry branch, logo and crt0 are stock; there is no cracktro, trainer or
appended payload. The complement/header checksum mismatch shows the 256-byte
header was rebuilt/edited (this is the cancelled GBA build; GameFAQs lists the
GBA SKU as "Canceled"). All analysis below is against this exact image.

## 2. Executive summary

The game has **two independent, developer-intended code layers**:

1. **Four hard-coded 14-character cheat passwords** compared literally by the
   Password screen: `1B1GM4CNCH33S3`, `1ST0L3TH3C0L0R`, `T0VGHG0THCH1CK`,
   `M4NV4CH4MP10NS`. Each sets a mode value in bits 16-18 of `0x03000200`
   (`0x10000`…`0x40000`) and starts a new game. These are the four codes
   published on GameFAQs; all four literals are present in the ROM.
2. **A general 14-symbol progress password** over a 32-symbol alphabet
   (21 consonants + `0-9` + `?`), with a 14-byte XOR key, a 5-bit checksum
   formed from bit 0 of characters 0-4 vs characters 5-9, and the remaining
   bits unpacked by bit-planes into ten state words at `0x03000200`.
   The input space is `32^14 = 2^70`; the checksum leaves `32^13 = 2^65`
   accepted strings. The four cheat strings are **not** checksum-valid and are
   therefore outside the general space (they are special-cased first).

The general decoder was reimplemented offline and verified against the ROM's
own code with a GDB/CLI-debugger oracle. Three codes new to every published
list were generated and entered on the real Password screen:

* `GP6JRTMY8N0TKF` (checksum 1) — **accepted**, intro cut-scene and story
  pages rendered; the same start then proceeds to Graveyard Garden.
* `HN6JRSLY8N0TKF` (checksum 2) — **accepted**, different intro artwork, then
  the playable Graveyard Garden with HUD (observed).
* `GP6JRSMY8N0TKF` — one checksum bit changed — **rejected** with the
  on-screen text `INVALID PASSWORD`; this bounds the validator.

The published four-code list is confirmed against the ROM (all four literals
present; `M4NV4CH4MP10NS` entered and accepted) but is only the cheat shortcut. The
general progress-password system is the larger, unpublished surface.

## 3. How to reproduce

Emulator: mGBA SDL (`mgba -3`), headless X (Xvfb `:338`, openbox),
`SDL_AUDIODRIVER=dummy`. Default mGBA SDL keymap used throughout:
A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, L=`a`, R=`s`, D-pad=arrows.
Short taps (≈70–160 ms hold, ≥220 ms gap) are required; a 300 ms hold makes
menus repeat.

Boot path: legal screen → Pocket Studios / Disney / TDK logos →
intro cut-scene → `Press Start` → main menu.

Menus walked (screenshots on disk, `/tmp/hauntedmansion/`):

```
Main menu:  New Game | Password | Options
Options:    Music [check] | Sound [check] | Credits
Password:   14 slots; keyboard rows
            B C D F G H J K L M
            N P Q R S T U V W X Y
            Z 0 1 2 3 4 5 6 7 8
            <-  9  ?  [✓]
Pause:      Paused | Continue | Quit
Quit:       Sure?  ✓ ✗       (✗ is the default-selected red item)
```

There is no Continue/save slot, no level-select menu and no debug menu; the
Password screen is the only persistence surface exposed by the menus.

Entering a code: move with the D-pad (rows 0-2 are 10 columns; row 3 holds
backspace/9/?/check; vertical movement clamps to the nearest row-3 cell),
press A on each glyph, then A on the check mark. The check mark is reached
reliably from the last glyph `F` (row 0, col 3) by Down ×3, Right ×2, A.

Codes tested:

| Code | Len | Result |
|---|---|---|
| `1B1GM4CNCH33S3` | 14 | accepted (published; flag `0x10000`) |
| `1ST0L3TH3C0L0R` | 14 | present in ROM (published; flag `0x20000`, derived) |
| `T0VGHG0THCH1CK` | 14 | present in ROM (published; flag `0x30000`, derived) |
| `M4NV4CH4MP10NS` | 14 | **entered and accepted**; RAM read `0x03000200 = 0x40000` |
| `GP6JRTMY8N0TKF` | 14 | **generated; accepted; intro cut-scene + story pages** |
| `HN6JRSLY8N0TKF` | 14 | **generated; accepted; intro variant, then playable Graveyard Garden** |
| `HP6JRSMY8N0TKF` | 14 | generated; accepted; black frame under HUD, Start ignored 5 s |
| `GP6JRSMY8N0TKF` | 14 | **rejected: `INVALID PASSWORD`** (checksum mismatch) |
| `?CDGP3?W4SW44W` | 13 | rejected (`INVALID PASSWORD`; length check) |
| 13-symbol variants | 13 | rejected (length check) |

## 4. Address map

ROM (file offset = address − `0x08000000`):

| ROM address | File offset | Contents |
|---|---|---|
| `0x08713F01` | `0x713F01` | 21-byte alphabet `BCDFGHJKLMNPQRSTVWXYZ` (NUL-padded) |
| `0x08713F18` | `0x713F18` | `1B1GM4CNCH33S3` (16-byte slot) |
| `0x08713F28` | `0x713F28` | `1ST0L3TH3C0L0R` |
| `0x08713F38` | `0x713F38` | `T0VGHG0THCH1CK` |
| `0x08713F48` | `0x713F48` | `M4NV4CH4MP10NS` |
| `0x087125B2` | `0x7125B2` | 14-byte XOR key `05 0B 1B 06 0D 0E 09 13 1D 0A 15 0F 07 03` |
| `0x085C7E98` | — | symbol-index → character decode helper |
| `0x085C7F08` | — | **password validator** (Thumb) |
| `0x085C85E8` | — | `roommask(floor, count)` helper (used by decoder and save code) |
| `0x085C79B8` | — | **password encoder** (state words → 14 symbols, XOR key) |
| `0x085C78A8` | — | save/password wrapper; calls encoder |
| `0x085C7004` | — | call site of the validator (accept handler) |

Validator internals:

| Address | Role |
|---|---|
| `0x085C7F1A` | read first slot; if empty → reject at `0x085C8582` |
| `0x085C7F26`–`0x085C7FB2` | copy 14 slot values into `0x03005860` |
| `0x085C7FB4` | decode symbols to chars at `0x03005780` |
| `0x085C7FBE` | `strcmp` vs `1B1GM4CNCH33S3` |
| `0x085C8018` | `strcmp` vs `1ST0L3TH3C0L0R` |
| `0x085C8064` | `strcmp` vs `T0VGHG0THCH1CK` |
| `0x085C80B0` | `strcmp` vs `M4NV4CH4MP10NS` |
| `0x085C80F8` | `strlen(string) == 14`, else reject |
| `0x085C810C` | XOR loop: `buf[i] = (buf[i] ^ key[i]) & 31` |
| `0x085C857E` | `cmp r6, sl` — stored checksum vs computed checksum |
| `0x085C8582` | reject: `r0 = 0` |
| `0x085C8586` | accept: store ten state words, `r0 = 1` |

RAM:

| RAM address | Contents |
|---|---|
| `0x03005780` | decoded 14-char string (NUL-terminated) |
| `0x03005860` | numeric buffer: 14 symbol indices, then XORed in place |
| `0x03005820` | encoder output: 14 encoded symbols (written by `0x085C79B8`) |
| `0x0201FF00 + 0x0B…0x18` | script variable area used by the Password UI; 14 slot values, reversed (char 1 at `+0x18`, char 14 at `+0x0B`) |
| `0x03000200` | checksum (low 5 bits) / cheat mode (`0x10000`–`0x40000`) |
| `0x03000204` | 13-bit field F |
| `0x03000208` | 7-bit field C |
| `0x0300020C` | result of `roommask(field G, checksum)` |
| `0x03000210` | 8-bit field E |
| `0x03000214` | 9-bit-derived H × 4 |
| `0x03000218` | `(H × 4) / 60` |
| `0x0300021C` | 7-bit field A |
| `0x03000220` | 4-bit field B |
| `0x03000224` | 4-bit field D |
| `0x03000228` | "password valid" flag (0 at entry, 1 on accept) |

## 5. Algorithm

### 5.1 Alphabet and symbol model

The keyboard offers exactly 32 symbols. Symbol index → character:

```
index  0..20 : "BCDFGHJKLMNPQRSTVWXYZ"[index]
index 21..30 : '0' + (index - 21)          # 21='0' … 30='9'
index 31     : '?'
```

The inverse is used for input. A code is exactly 14 symbols. The UI stores
`index + 1` per slot (`0` = empty), which is why the validator rejects an empty
first slot before doing anything else.

### 5.2 De-obfuscation

```
KEY = [0x05,0x0B,0x1B,0x06,0x0D,0x0E,0x09,0x13,0x1D,0x0A,0x15,0x0F,0x07,0x03]
for i in 0..13: d[i] = sym[i] ^ KEY[i]          # & 0x1F
```

### 5.3 Checksum (the accept/reject condition)

```
computed = Σ_{i=0..4}  ((d[i]   & 1) << i)      # 5 bits from chars 0..4
stored   = Σ_{i=0..4}  ((d[5+i] & 1) << i)      # 5 bits from chars 5..9
accept only if computed == stored
```

There is no further range/rejection check: a checksum-valid 14-symbol code is
accepted by the validator. The four published cheat strings do **not** satisfy
this relation (computed/stored pairs: 7/21, 27/24, 4/16, 4/17), which is why
they must be special-cased first.

### 5.4 Field unpacking (bit-planes of `d`)

```
A  = Σ_{i=0..6}  ((d[7+i] >> 2) & 1) << i                 -> 0x0300021C
B  = (d[12]&1) | ((d[8]>>4)&1)<<1 | ((d[9]>>4)&1)<<2
               | ((d[10]>>4)&1)<<3                        -> 0x03000220
C  = Σ_{i=0..6}  ((d[i] >> 2) & 1) << i                   -> 0x03000208
D  = (d[13]&1) | ((d[11]>>4)&1)<<1 | ((d[12]>>4)&1)<<2
               | ((d[13]>>4)&1)<<3                        -> 0x03000224
E  = Σ_{i=0..7}  ((d[i] >> 4) & 1) << i                   -> 0x03000210
F  = Σ_{i=0..12} ((d[i] >> 1) & 1) << i                   -> 0x03000204
G  = Σ_{i=0..7}  ((d[i] >> 3) & 1) << i                   -> arg to 0x085C85E8
H  = (d[10]&1) | (d[11]&1)<<1 | ((d[8]>>3)&1)<<3
   | ((d[9]>>3)&1)<<4
   | (((d[13]>>4)&1) | ((d[10]>>3)&1))<<5
   | ((d[11]>>3)&1)<<6 | ((d[12]>>3)&1)<<7 | ((d[13]>>3)&1)<<8
                                                          -> 0x03000214 = H*4
                                                          -> 0x03000218 = (H*4)/60
checksum(=computed=stored)                                -> 0x03000200
0x03000228 = 1
```

`0x085C85E8(G, checksum)` returns a room-mask built from comparisons of the
5-bit value against thresholds (0,3,5,10,13,17,18,21) and the bits of `G`; the
result is stored at `0x0300020C`. With `G = 0` it returns 0 (bit 0 of the
argument gates everything), which is the state of all codes used below.

### 5.5 Cheat path

Before the general decode, the validator compares the decoded string against
the four literals. On a match it clears all ten field words, writes
`0x03000200 = mode << 16`, sets `0x03000228 = 1` and returns 1:

| Literal | `0x03000200` |
|---|---|
| `1B1GM4CNCH33S3` | `0x10000` |
| `1ST0L3TH3C0L0R` | `0x20000` |
| `T0VGHG0THCH1CK` | `0x30000` |
| `M4NV4CH4MP10NS` | `0x40000` |

The values are written by `movs r0,#imm8; lsls r0,#N` in the four blocks at
`0x085C7FC8`, `0x085C8022`, `0x085C806E`, `0x085C80BA`. `M4NV4CH4MP10NS`
(the published "unknown effect" code) was entered in mGBA and the word was
read back as `0x40000`; its effect is a mode-4 new game (the same intro path
as the other cheats), not a distinct visible item in the tested build.

### 5.6 Encoder (for completeness)

`0x085C79B8` is the inverse: it packs the ten `0x03000200` words into 14
5-bit values (the bit-planes above), XORs each with the same key, and stores
the result at `0x03005820`; `0x085C78A8` wraps it and is called from a
front-end state machine at `0x085C057C`. This is the routine that would print a
password for a live game; in this build the Quit/`Sure?` confirmation returns to
the pause menu without printing one.

## 6. Tables

### 6.1 Published codes verified in the ROM

All four GameFAQs GBA passwords are literal NUL-terminated strings in 16-byte
slots at `0x08713F18`–`0x08713F58`, immediately after the 21-symbol alphabet.
No other fixed-slot 14-character code table was found in the image (the
surrounding `0x713F00`–`0x713F70` region holds the alphabet, the four strings,
`SYSTEM ERROR` and `Invalid Fright Band...`). A whole-ROM scan for 13+ character
runs over the same alphabet returns only text/data false positives, not a second
code table.

### 6.2 Alphabet / key

```
alphabet : BCDFGHJKLMNPQRSTVWXYZ
digits   : '0'..'9' at indices 21..30
wildcard : '?' at index 31
key      : 05 0B 1B 06 0D 0E 09 13 1D 0A 15 0F 07 03
```

### 6.3 State words set by a general code

For the all-zero-field codes used here, `0x03000200 = checksum` and
`0x03000204..0x03000224 = 0`, with `0x03000228 = 1`. RAM reads (mGBA
savestate, IWRAM at state offset `0x19000`) after entry:

* `GP6JRTMY8N0TKF` → `0x03000200 = 1`
* `HN6JRSLY8N0TKF` → `0x03000200 = 2`
* `M4NV4CH4MP10NS` → `0x03000200 = 0x40000`

## 6b. Enumeration

**Space definition.** 14 symbols from a 32-symbol alphabet = `32^14 = 2^70 =
1,180,591,620,717,411,303,424` input strings. The only general acceptance
condition is the 5-bit equality in §5.3, so the accepted progress-code set is
`32^13 = 2^65 = 36,893,488,147,419,103,232` strings (checksum class 0..31),
plus the four hard-coded cheats that bypass the checksum. The four cheats are
*not* members of the checksum set.

**Generator.** Offline encoder (Python, `/tmp/hauntedmansion/mint.py`)
that chooses the desired `d` bit-planes, enforces the checksum, and XORs the
key. Codes for checksum classes 0–7 with all other fields zero:

| checksum | code | in-game |
|---:|---|---|
| 0 | `HP6JRSMY8N0TKF` | accepted; black frame under HUD, Start ignored 5 s |
| 1 | `GP6JRTMY8N0TKF` | **accepted; intro cut-scene and story pages rendered** |
| 2 | `HN6JRSLY8N0TKF` | **accepted; intro variant, then playable Graveyard Garden** |
| 3 | `GN6JRTLY8N0TKF` | not entered (same formula) |
| 4 | `HP5JRSMX8N0TKF` | not entered |
| 5 | `GP5JRTMX8N0TKF` | not entered |
| 6 | `HN5JRSLX8N0TKF` | not entered |
| 7 | `GN5JRTLX8N0TKF` | not entered |

**Novel codes (absent from GameFAQs, VGChartz, TCRF and every list checked).**
`GP6JRTMY8N0TKF` and `HN6JRSLY8N0TKF` were typed on the real Password screen
with the on-screen keyboard, submitted with the check mark, and the game
accepted them: both played the intro cut-scene, and `HN6JRSLY8N0TKF` went on
to the playable Graveyard Garden with HUD (screenshot evidence `x2c.png`,
`x3c.png`, `ac2c.png`, `ac5c.png`). The state word `0x03000200` read back as 1
and 2 respectively; all other field words were 0.

**Bounds proven by rejection.** `GP6JRSMY8N0TKF` is byte-for-byte
`GP6JRTMY8N0TKF` with the fifth character changed from `T` (index 15 → bit 0
of `d[5]` = 0) to `S` (index 14 → bit 0 = 1). It is 14 symbols from the same
alphabet, but computed checksum = 1 and stored checksum = 0, and the game
displayed `INVALID PASSWORD` (`aa5c.png`). A 13-symbol code is rejected by the
length check before the checksum. Both layers (length and checksum) are
therefore individually exercised.

**Negative search bounds.** `strings -t x -n 4` over the whole 8 MiB produced
74,688 lines: 0 case-insensitive hits for `debug`, 0 for `cheat`, 1 for
`password` (the scroll hint text), 4 for `test` (poem), 2 for `sound`, 1 for
`level`. The Password screen is the only code-entry surface; the menu walk
(title, main, options, pause, quit-confirm, password) found no debug or
level-select entry. The string/table space searched is therefore the entire
ROM, and the absence of a hidden debug menu is a statement about that space.

## 7. Validation evidence

**Observed (emulator / RAM):**

* The 14-slot Password screen with the 32-symbol keyboard, typed codes
  rendering exactly the characters sent (`p2c.png`, `ab2c.png`).
* `GP6JRTMY8N0TKF` accepted → intro cut-scene and story pages (`x2c.png`,
  `x3c.png`); `0x03000200 = 1` in a savestate taken during the intro.
* `HN6JRSLY8N0TKF` accepted → different intro artwork and then the playable
  Graveyard Garden with HUD (`ac2c.png`, `ac5c.png`); `0x03000200 = 2`.
* `GP6JRSMY8N0TKF` rejected with `INVALID PASSWORD` (`aa5c.png`).
* `M4NV4CH4MP10NS` accepted; `0x03000200 = 0x40000` read from a savestate.
* `?CDGP3?W4SW44W` was submitted with only 13 of 14 slots filled and was
  rejected; the length check fires before the checksum.
* Menus: Options (Music/Sound/Credits), pause (Continue/Quit), Quit/Sure?
  confirmation; no debug or level-select entry.

**Derived (instruction sequence):**

* Alphabet, key table, length check, XOR loop, checksum comparison, reject and
  accept paths, ten state-word stores, encoder inverse, and the four cheat
  comparisons and mode constants.
* All four published literals exist at `0x08713F18`–`0x08713F58`; their
  checksums fail the general test (computed/stored 7/21, 27/24, 4/16, 4/17).

**Inferred (not fully exercised):**

* The low 5 bits of `0x03000200` (which equal the checksum) behave as a
  chapter/level selector: 1 and 2 both start the same Graveyard Garden after
  different intro art, and 0 produced a black frame. The exact meaning of
  value 0 and of values >2 is not proven; no room-name change was observed.
* The ten field words are believed to be the save/checkpoint record consumed
  by the script VM; only the all-zero record and checksum-only records were
  exercised.

## 8. Unknowns

* The semantics of fields A–H (13-bit F, 8-bit E/G, 7-bit A/C, 4-bit B/D,
  H/60 pair) are not labelled beyond their storage addresses. No code with a
  nonzero field other than the checksum was observed to change the starting
  room; `F=1` and `E=1` codes were typed and produced the same black/intro
  transition (acceptance inferred from the transition).
* The `roommask` helper `0x085C85E8` returns 0 for the exercised codes; a
  nonzero mask was not produced on screen.
* Whether the Quit path is supposed to display a generated password in the
  retail build is unknown; in this image it returns to the pause menu.
* The phone-code puzzle layer (inventory `Devices: Phone`/`Devices: Codes`,
  the eagle/knight/moose/seabeard/angel/gargoyle/clockwork/skeleton/lionhead
  codes, and the coffin ghost-letter mapping M=3 R=5 G=1 A=7 C=2 E=6 Y=4 !=8)
  is developer-intended gameplay content but is separate from the Password
  screen and was not reversed to a validator.

## 9. Tooling

* `python3` + `capstone`-free raw scripts in `/tmp/hauntedmansion/`:
  `phase0.py`, `ptrscan.py`, `blscan.py`, `model.py` (decoder),
  `mint.py` (encoder), `scan_codes.py`, `ss.py`/`ssmake.py` (mGBA savestate
  PNG/`gbAs` zlib reader/writer), `key.py`/`type_code.py`/`enter_code.py`
  (X11 input).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000
  -M force-thumb`.
* mGBA SDL with `-g` GDB stub and `-d` command-line debugger; the CLI
  debugger's `r/1`, `x/4`, `b/t`, `load` commands and Thumb software
  breakpoints were used as an oracle at `0x085C8104`, `0x085C8586` and
  `0x085C8580`.
* Xvfb `:338` + openbox + xdotool + scrot; short-tap input
  (70–160 ms hold) to avoid D-pad repeat.

## Legal note

No ROM, extracted graphics, music or game text is redistributed here. Only
hashes, addresses, algorithms, state layouts and self-generated example codes
are published.
