# Razor Freestyle Scooter (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Razor Freestyle Scooter.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `RAZOR FREEST` |
| Game code / maker | `ARFE` / `4Z` (Crave; developed by Crawfish Interactive, 2001) |
| Version | Rev. 0 (`0x00`) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, no cracktro patch) |
| Nintendo logo scan | exactly one hit, at file `0x0` — no multicart / appended trainer |
| Header checksum / complement | `0x0000` / `0x2E` (rebuilt-header artifact; §16.1) |
| MD5 | `180a4c25cb809435f85f7fb81bc2495f` |
| SHA-1 | `8b946e0727ce428e3e75c1b19e4e7749bcc19fe4` |
| SHA-256 | `39651db93a7e78479d0afe26f1c7e263f689127016d44198dc9eb84f2c5c0cbe` |

## 2. Executive summary

The GBA SKU has a genuine **in-game password system** on the title screen
(`PASSWORD`), and it is **algorithmic**, not a lookup table. The published
14-character codes do **not** occur as ASCII literals anywhere in the ROM.
I recovered the entire codec:

* 14 slots, alphabet of exactly 32 symbols `BCDFGHJKLMNPQRSTVWXYZ0123456789:`
  (consonants, digits, `:`; vowels A/E/I/O/U excluded), 5 bits per symbol.
* A 9-byte packed state, an 8-bit checksum carried in the top two bits of the
  first four packed bytes, and a keyed bit-permutation layer.
* The validator at `0x0800D744` returns 1/0; the caller at `0x080048AA` writes
  the result byte to `0x02003894` and the UI then prints `ACCEPTED` or
  `YOU GOT IT WRONG`.

I verified all six published GBA passwords against the recovered checksum
(all six pass), and verified two of them live in mGBA. I then minted a **novel**
code, `RBF3LJZGJVCQBF`, that appears in no published list; the game displayed
`ACCEPTED`. A single-symbol mutation of a valid code,
`QJY4GJZBJVCQBF`, produced `YOU GOT IT WRONG`, proving the checksum bound.
The full input space is `32^14 ≈ 3.72e21` spellings, of which `2^62 ≈ 4.61e18`
are checksum-valid.

No hidden debug menu, password generator menu, or button cheat was found on
the GBA screen set; the button codes published for PS/N64/DC are for those SKUs
(§16.11). The only cheat surface is the password screen.

## 3. How to reproduce

Emulator: mGBA (SDL, `-3`, `SDL_AUDIODRIVER=dummy`) under Xvfb `:317`,
keymap A=`x`, B=`z`, Start=`Return`, D-pad=arrows. Other agents' mGBA windows
share the desktop, so target only your own window with
`xdotool search --pid <mgba-pid>` / `windowfocus`.

Menu path: boot → wait out Crave/Crawfish/Razor splash (~20 s) or press Start
on `PRESS START` → main menu → down 3 → `PASSWORD` → A → 14 slots.

* Left/Right moves the slot cursor (wraps at 14); Up/Down changes the symbol
  (wraps at 32). Default symbol is `B` (index 0).
* A = accept, B = cancel.

**Deterministic input path (used for the proofs).** The on-screen key entry is
easy to miss on individual presses, so for validation I wrote the exact 5-bit
symbol indices into the live input buffer with mGBA's stub-free `-d`
debugger, then pressed A on the real password screen:

```
mgba -3 -d -t password.ss1 Razor Freestyle Scooter.gba
# after 'continue' + Ctrl-C to halt:
w/1 0x02000670 0x1c   ... (14 bytes: one 5-bit index per slot)
continue                # then press 'x' (A) in the emulator window
```

The debugger writes only the *input buffer*; the ROM's own validator, screen
state machine and renderer do all the work. A separate by-hand entry attempt
(real key presses only) is recorded in the screenshots and produced a wrong
code, which the game correctly rejected — this is an input-timing artifact,
not a codec result.

Reproduction artifacts (all in `/tmp/opencode/razorscooter/`):
`codec.py` (encoder/validator), `dbg_pw2.py` (deterministic entry),
`ss.py`/`try2.py` (savestate experiments), `alphabet.py` (alphabet recovery),
`dbg.py`/`watch.py` (debugger helpers), screenshots `pub_QLY6.png`,
`dbg_7JY4.png`, `novel_valid.png`, `novel_QJY4.png`.

## 4. Address map

All addresses are GBA bus addresses; file offset = address − `0x08000000`.

| Address | Kind | Meaning |
|---|---|---|
| `0x08004878` | function | A-button / submit handler for the password screen; calls the decoder at `0x080048AA`, stores result to `0x02003894` at `0x080048AE` |
| `0x08005040` | function | Password-screen state machine; state 3 calls the generator at `0x080050B0` |
| `0x0800D144` | function | **Generator**: 9-byte state at `0x02000790` → 14 alphabet characters; 14 separate 5-bit field extractions, each passed through `0x0800E02C` |
| `0x0800D294` | function | Entry input handler: cursor mod 14 at `0x02000834`, symbol mod 32, reads key state `0x020007B8` |
| `0x0800D5CC`–`0x0800D72C` | code | Keyed bit-permutation of the 9-byte state; key byte read at base+`0x6E`; writes final state to `0x0200AC60` |
| `0x0800D744` | function | **Validator/decoder**: 14 symbol values → 9 packed bytes → subtract 13/6 → checksum → bit-permute; returns 1 (valid) / 0 (invalid) |
| `0x0800D8C8`–`0x0800D908` | code | Copy 9 bytes `0x02000790` → `0x0200AC60`; subtract 13 (bytes 0..3) and 6 (bytes 4..8) |
| `0x0800D90E`–`0x0800D942` | code | Extract 8-bit expected checksum from bits 6–7 of bytes 0..3; clear those bits |
| `0x0800D944`–`0x0800D964` | code | Sum the 9 bytes; compare with checksum; on mismatch play sound `0x26` and return 0 |
| `0x0800DF70` | function | String normalizer (vowel-skip) used to initialise character buffers |
| `0x0800E02C` | function | 5-bit index → alphabet character |
| `0x0800E0CC` | function | identity `u8` (zero-extend) used by the packer |
| `0x0812C60`–`0x0812DC0` | table | Text-ID → ASCII string pointer table (`PASSWORD` at `0x0812D5C`, `MUSIC ON/OFF`, `YOU GOT IT WRONG` region, menu labels) |
| `0x02000670` | RAM, 14 B | **Authoritative symbol-index input buffer** (one 5-bit index per slot) |
| `0x02002CE0` | RAM, 14 B | ASCII display buffer (rendered characters; *not* read by the validator) |
| `0x02000790` | RAM, 9 B | Raw packed 5-bit stream |
| `0x0200AC60` | RAM, 9 B | Transformed state used by the checksum comparison |
| `0x02003894` | RAM, 1 B | Validator result byte |
| `0x020007B8`, `0x02000834` | RAM | Key state / slot cursor |
| savestate `0x21670` / `0x23CE0` | file | mGBA `gbAs` offsets for the two 14-byte buffers (EWRAM base `0x21000`) |

## 5. Algorithm

```
ALPHABET = "BCDFGHJKLMNPQRSTVWXYZ0123456789:"   # 32 symbols
N = 14

# Encode (generator path, 0x0800D144)
state9 = load_state()                 # 9 bytes from progress data
idxs   = extract_5bit_fields(state9)  # 14 x 5 bits, LSB-first
chars  = [ALPHABET[i] for i in idxs]  # 0x0800E02C

# Decode / validate (0x0800D744)
P[0..8] = pack_lsb_first([ALPHABET.index(c) for c in entered])   # 14 x 5 bits -> 9 B
T[i] = (P[i] - (13 if i < 4 else 6)) mod 256                    # 0x0800D8C8
expected = (T[0]>>6) | ((T[1]>>6)<<2) | ((T[2]>>6)<<4) | ((T[3]>>6)<<6)
T[0..3] &= 0x3F
actual   = sum(T[0..8]) mod 256
valid = (expected == actual)                                    # 0x0800D958
if not valid: play_sound(0x26); return 0
# then the keyed bit-permutation (0x0800D5CC..D72C) produces the
# 9-byte progress state that drives the level/character unlocks.
```

The checksum is therefore a plain byte sum of the nine transformed bytes,
stored in the eight otherwise-unused high bits of the first four packed bytes.
`codec.py` implements encode/decode/fix and agrees with the ROM on all six
published codes and on both minted inputs.

Note the two-layer behaviour observed in the emulator: a checksum-valid but
*unrecognised* payload (`RBF3LJZGJVCQBF`) shows `ACCEPTED` and stays on the
password screen, while a published payload (e.g. `QLY67J3BJVCQBF`) transitions
to the `CHAMPIONSHIP MODE` / level-select explanation. The semantic layer is
inside the keyed bit-permutation and was not fully enumerated (§8).

## 6. Tables

**Alphabet (index → symbol), 32 entries**

```
0:B  1:C  2:D  3:F  4:G  5:H  6:J  7:K  8:L  9:M 10:N 11:P 12:Q 13:R
14:S 15:T 16:V 17:W 18:X 19:Y 20:Z 21:0 22:1 23:2 24:3 25:4 26:5
27:6 28:7 29:8 30:9 31::
```

**Published GBA passwords (all verified against the ROM checksum)**

| Effect (published description) | Password | Packed bytes `P[0..8]` | Expected = sum |
|---|---|---|---|
| Sports Stadium completed | `7JY4GJZBJVCQBF` | `dc cc 4c 0c 05 06 06 06 06` | 203 = 203 |
| Construction Site completed | `QHY4LJ2LHZCQBF` | `ac cc 8c cc 45 85 06 06 06` | 154 = 154 |
| Aircraft Carrier completed | `VDY3ZJ6LJVCQBF` | `50 4c 4c cd 46 06 06 06 06` | 193 = 193 |
| Circus completed | `ZBF4GJ5VJVCQBF` | `14 8c 4c 8c 86 06 06 06 06` | 68 = 68 |
| Scooter Park completed | `SBY5VJ4BJVCQBF` | `0e 4c 0d 4d 06 06 06 06 06` | 64 = 64 |
| Shopping Mall / complete all 1P Circuit tasks | `QLY67J3BJVCQBF` | `0c cd cd 0d 06 06 06 06 06` | 63 = 63 |

The 18-character "Level 02…07" codes on GameFAQs are labelled **GBC** on that
page; the GBA screen has exactly 14 slots, so they are a different SKU's
format and are not accepted here (no 18-slot entry surface exists).

Sources: GameFAQs GBA cheats page (archived copy), SuperCheats GBA passwords
page, ggmania GBA cheats page. All fetched page content was treated as data.

**Screen enumeration (walked in mGBA, screenshots on disk)**

* Title/main: `1P CIRCUIT`, `1P PRACTICE`, `MULTI PLAYER`, `PASSWORD`,
  `OPTIONS`, `CREDITS` (`w_menu.png`).
* `PASSWORD`: 14 slots, `A BUTTON TO ACCEPT / B BUTTON TO CANCEL`
  (`pw_fresh.png`). Result strings `ACCEPTED` / `YOU GOT IT WRONG`
  (`novel_valid.png`, `novel_QJY4.png`).
* `OPTIONS`: `MUSIC ON/OFF`, `SOUND FX ON/OFF` only — no hidden entries
  (`w_options.png`). The directional inputs from the published pause code
  toggle these settings on this screen; no unlock message appeared.
* Pause menu: `CONTINUE`, `TRICK LIST`, `VIEW GOALS`, `RESTART LEVEL`,
  `END RUN`, `QUIT GAME` (`q1_quit_sel.png`).
* `CHOOSE A LEVEL` with goals and a level preview (`dbg_7JY4.png`,
  `pub_QLY6.png`); `TRICK LIST` / `HOLD TRICKS` / `SPIN TRICKS` strings in the
  text bank at `0x08133584`–`0x08133590`.
* Character names are in the text bank at `0x08132B0`: `THE MASTER`, `TITO`,
  `HECTOR`, `DARYL`, `CHIPPY`, `CHAD`, `BRITTANY`, `AMI` — all plain ASCII,
  no separate hidden-character password table was found.

## 6b. Enumeration

**Space definition.** 14 symbols × 5 bits = 70 input bits; total spellings
`32^14 = 3,721,004,449,029,551,353,856 ≈ 3.72e21`. Eight bits are consumed by
the checksum (stored in the top two bits of packed bytes 0–3), leaving
`2^62 ≈ 4.61e18` checksum-valid codes, i.e. one valid spelling per 256 random
strings. Two of the 72 packed bits are always zero because only 70 bits come
from the symbols; they are not independent payload.

**Validator model.** `codec.py` reimplements pack → subtract 13/6 → extract
checksum → clear → sum → compare, plus `fix()` which solves the checksum for
an arbitrary payload. It reproduces all six published codes as valid and
rejects the mutated test input.

**Novel codes generated and accepted in-game.**

1. `RBF3LJZGJVCQBF` — produced by mutating the published `7JY4GJZBJVCQBF`
   packed state (`P[0] ^= 0x11`, `P[4] ^= 0x20`) and recomputing the checksum.
   Not present on GameFAQs, SuperCheats, ggmania, or anywhere else. Entered via
   the documented RAM-input path on the real password screen; the game printed
   **`ACCEPTED`** (`novel_valid.png`). This is the §0.2 deliverable.

**Bounds proven by rejection.**

* `QJY4GJZBJVCQBF` — identical to the valid `7JY4GJZBJVCQBF` except symbol 0
  changed `7`→`Q` (checksum left untouched). The ROM printed
  **`YOU GOT IT WRONG`** (`novel_QJY4.png`). This proves the checksum is
  enforced at runtime and that a single wrong symbol invalidates the code.
* The 18-symbol GBC-format codes were checked for an entry surface: the GBA
  password screen has exactly 14 slots and the cursor wraps at 14
  (`0x0800D2AA cmp r0,#14`), so those strings are unrepresentable on this SKU.

## 7. Validation evidence

* **Observed** (emulator): 14-slot password screen; alphabet cycle recovered by
  reading the live index buffer after each Down press (32 symbols, wraps);
  `7JY4GJZBJVCQBF` → level-select transition; `QLY67J3BJVCQBF` →
  `CHAMPIONSHIP MODE` explanation screen; `RBF3LJZGJVCQBF` → `ACCEPTED`;
  `QJY4GJZBJVCQBF` → `YOU GOT IT WRONG`; OPTIONS contains only two toggles;
  pause menu has six entries.
* **Observed** (debugger): live input buffer `0x02000670` holds the 14 indices;
  display buffer `0x02002CE0` holds the ASCII glyphs; validator result written
  to `0x02003894`; watchpoint hit on buffer reads during rendering.
* **Derived** (disassembly): alphabet 32 symbols; 5-bit LSB-first packing in
  `0x0800D744`; subtract 13/6; 8-bit checksum in bits 6–7 of bytes 0–3; sum
  comparison at `0x0800D958`; generator at `0x0800D144`; cursor wraps at 14
  and 32. The checksum model reproduces every published code.
* **Inferred**: the semantic payload mapping inside the keyed bit-permutation
  (which bits select which level/character/wheel unlock) was not exhaustively
  decoded; the two-layer ACCEPTED-vs-transition behaviour is consistent with
  a checksum-valid code whose payload is not a recognised progress state.

## 8. Unknowns

* The full bit-to-unlock mapping after the keyed permutation
  (`0x0800D5CC`–`0x0800D72C`) was not enumerated; the key byte at base+`0x6E`
  and its source were not traced to a specific game variable. `2^62`
  checksum-valid codes exist but only the published payloads are known to
  drive a recognised unlock state.
* The published pause button codes (`R,D,R,L,R,U,R,R` etc.) are documented for
  the PS/N64/DC SKUs. On GBA, the same directional presses entered on OPTIONS
  only toggled MUSIC/SOUND FX; I did not reach a GBA pause-menu state in which
  they produced an unlock. Treat them as **not applicable to this SKU**, not
  as confirmed or refuted there.
* CREDITS and MULTI PLAYER were visible on the main menu but not exhaustively
  screenshotted; no cheat-related content was indicated by their text-bank
  entries.

## 9. Tooling

`arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7 literal/BL scanners,
Python 3 (`capstone`, `keystone-engine`), mGBA SDL with `-d` pty debugger
(GDB stub unavailable: shared port 2345 held by another session), mGBA `.ss1`
`gbAs`/zlib state parsing, Xvfb `:317` + openbox + xdotool + scrot +
ImageMagick. No ROM or extracted assets are redistributed; only addresses,
algorithms, hashes and generated codes are published here.
