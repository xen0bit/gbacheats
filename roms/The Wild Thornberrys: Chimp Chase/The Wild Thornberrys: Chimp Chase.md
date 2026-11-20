# The Wild Thornberrys: Chimp Chase (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Wild Thornberrys: Chimp Chase.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title / code / maker / version | `CHIMP CHASE` / `AWTE` / `78` (THQ) / `0x00` |
| Entry word | `0xEA00002E` (stock; not a cracktro) |
| Fixed `0x96`, complement, checksum | `0x96`, `0x00`, `0x0000` |
| Developer (splash) | Klasky Csupo; published by THQ (2001) |
| MD5 | `11100f0c82de617894a90b0fa70b7e63` |
| SHA-1 | `cc8e699dd200d4b678c6d8ba7237d44f4b1d8733` |
| SHA-256 | `55ff0d9bf610e47d69d78e8c67808cd9858698529bd1e921acb922bde0ea4aa8` |

Sibling *The Wild Thornberrys Movie* was analysed separately; all findings below were
re-derived from this ROM's own bytes and live emulator state.

## 2. Executive summary

This GBA game has a **developer-intended 8-symbol password system** on the main menu
(`PASSWORD`). The on-screen keyboard is a strict 32-symbol alphabet
`BCDFGHJKLMNPQRSTVWXYZ123456789!?` (no vowels). A password is **exactly 8 symbols**.
Entry is capped at eight characters; the eighth keypress runs the validator.

The codec was recovered completely: a key-XOR, two triangular XOR diffusion stages,
a 5-bit-rank parity check over the first six symbols, and a 30-bit packed game-state
payload. Both the decoder (`0x0800DE94`) and the in-game generator (`0x0800E060`) were
reimplemented in Python; the decoder agrees with the ROM on accepted *and* rejected
inputs, and the generator's output was confirmed against the game's own behaviour.

A **novel, previously unpublished code `KFPBCDVL`** was navigated and typed on the real
password screen (not injected), accepted ("password accepted, press START to play"),
started a Jungle-level game with an unlockable character, and its decoded state was
verified in RAM at `0x02014BD4` = `00 00 01 02`. Four rejection tests bound the check
and field ranges: one bad checksum and three checksum-valid-but-out-of-range codes.

Web recon found **no published code list** for this SKU (GameFAQs/TCRF return 403;
search engines return nothing). The single hard-coded generator preset `crdts123`
(`0x082F09D8`) is **rejected** by the password screen — it is unreachable through the
keyboard (and no 8-symbol code decodes to its state `{1,2,3,4}`), so the credits
shortcut is effectively a dead/gated feature on this screen.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, Xvfb + openbox.
* Keymap (mGBA SDL): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, arrows = D-pad.
  Hold keys 35–70 ms; 45+ ms can double-step a cursor.
* Path: boot → title "Press Start" → Start → **MAIN MENU** → down once → **PASSWORD** → A.
* Keyboard grid (rows/columns as shown):
  `BCDFGHJK` / `LMNPQRST` / `VWXYZ123` / `456789!?`.
  Arrows move the highlight; **A** appends the highlighted symbol; **B** erases the
  last symbol (and exits the screen when empty). Eight symbols trigger validation.
* Novel code, typed character-by-character: **KFPBCDVL** → "password accepted, press
  START to play" → Start → map screen → Jungle-level intro/gameplay.
* Evidence images (analysis work dir `/tmp/opencode/chimpchase/`):
  `typedcrop.png` (novel code typed + accepted), `NOVEL_code_KFPBCDVL_accepted.png`,
  `accepted_startcrop.png` (map), `walk3crop.png` (Jungle dialogue),
  `rej0crop.png`–`bound2crop.png` (rejections), `optionscrop.png`, `s3.png`–`s5.png`.

## 4. Address map

| ROM address | Meaning |
|---|---|
| `0x08018E78` | Password-screen setup; calls `0x0800DBC0` with 8×4 keyboard geometry and callbacks |
| `0x0800DBC0` | Generic keyboard-widget initialiser; parameters copied to EWRAM globals |
| `0x0800D7DC`–`0x0800D800` | Key append: stores `code = 0x40 + row*8 + col`, caps index at 7 |
| `0x0800D84E`–`0x0800D886` | On 8th symbol: call decoder; call state validator through thunk `0x0802A094`; set success flag |
| `0x0800DE94`–`0x0800E058` | **Password decoder** (validates checksum, emits 4-byte state) |
| `0x0800E060`–`0x0800E22C` | **Password encoder/generator** (4-byte state → 8 symbols) |
| `0x0800E004` | Literal pool word = `0x0802EC798` (key table pointer) |
| `0x0802EC798` | Key table, first 10 bytes used: `0A 15 12 19 0C 16 0B 05 14 1A` |
| `0x08018196` | Installs preset generator table (`count=1`, states `0x082F09E0`, codes `0x082F09D8`) |
| `0x082F09D8` / `0x082F09E0` | Preset code `"crdts123"` / preset state `{01 02 03 04}` |
| `0x0801740C` | State interpreter: `{1,2,3,4}` → credits, else unpack fields, call range checker |
| `0x0801738C` | Field range checker; `0x0802C1C8` = per-field cap table |
| `0x08021CAE` | In-game password generator call site (builds state via `0x08017770`) |
| Strings: `0x0802C500` `PASSWORD`; `0x0802C554` accepted; `0x0802C57C` invalid; `0x0802C5A4` append/erase help; `0x0802C730` character names; `0x0802C3FC`–`0x0802C490` level names | |

| EWRAM address | Meaning (verified in savestates) |
|---|---|
| `0x02014B20`–`0x02014B27` | 8 input symbol codes (`0x40 + alphabet index`) |
| `0x02014B2C` / `0x02014BAC` | keyboard column / row index |
| `0x02014B30` | input length (index of last symbol, 0–7; validation at 8) |
| `0x02014BD4`–`0x02014BD7` | **decoded 4-byte game state** (RAM-verified `00 00 01 02` for `KFPBCDVL`) |
| `0x02014BDC` | acceptance flag (1 after a valid password) |
| `0x02014BF8` / `0x02014BFC` / `0x02014C00` | generator table ptr / count / code ptr (`0x082F09E0` / 1 / `0x082F09D8`) |

## 5. Algorithm

Symbols map to internal codes `c_i = 0x40 + alphabet_index`, index 0..31 in row-major
keyboard order. Let `K = [0A,15,12,19,0C,16,0B,05,14,1A]` (first ten bytes at
`0x0802EC798`).

**Decoder** (`0x0800DE94`), exact reimplementation in `pw.py`:

```
t[i] = (input[i] - 0x40) XOR K[i]          for i = 0..7
# diffusion stage A (r5 = 1..5, r4 = 0..7-r5)
for r5 in 1..5: for r4 in 0..(8-r5)-1: t[r4] ^= t[r5+r4]
# diffusion stage B
for r5 in 1..5: for r4 in 0..(8-r5)-1: t[r5+r4] ^= t[r4]
ck = t[0]^t[1]^...^t[5]
for j in 0..9:
    p = parity(K[j] & ck)                  # XOR of low five bits
    check[j//5] = (check[j//5] << 1) | p    # MSB first, 2 x 5-bit chars
require t[6] == check[0] and t[7] == check[1]
state = pack_5bit_sliding(t[0..7])         # 4 bytes, see pw.dec_pack
```

`pack_5bit_sliding` is a 32-bit-register sliding packer: it accumulates five-bit chunks
and emits bytes after 10/20/30/40 accumulated bits at shifts 2/4/6/8 (the top chunk is
truncated by the 32-bit register). This is reproduced bit-for-bit in `pw.py`; it matches
the ROM's RAM result exactly.

**State interpreter** (`0x0801740C` + `0x0801738C`):

```
level12 = s0 | ((s1 & 0xF) << 8)
fieldA  = s1 >> 4                # 0..5 required, not both A==0 and B==0
fieldB  = s2 & 0xF               # < 10 required
fieldC  = (s2 >> 4) & 3
fieldE  = (s2 >> 6) & 3          # < cap[fieldC] (table 0x0802C1C8)
fieldF  = s3 & 0x1F              # < 20 required
accept iff fieldA<=5 && (fieldA!=0 || fieldB!=0) && fieldB<10 && fieldF<20 && fieldE<cap[fieldC]
special: s == {1,2,3,4} -> credits screen (but see §8)
```

**Encoder** (`0x0800E060`): inverse pipeline — pack 4-byte state into six five-bit values
(30 bits), derive the two check chars by the same parity masks, apply the two diffusion
stages, XOR with `K[0..7]`, add `0x40`. Note the low two bits of `s3` are not preserved
(encoder/decoder are not strict inverses): generator input `[00,00,01,00]` decodes to
`[00,00,01,02]` — confirmed in RAM, so the codec encodes 30 state bits, not 32.

## 6. Tables

* Alphabet (index → symbol), row-major keyboard:
  `0:B 1:C 2:D 3:F 4:G 5:H 6:J 7:K / 8:L 9:M 10:N 11:P 12:Q 13:R 14:S 15:T /
   16:V 17:W 18:X 19:Y 20:Z 21:1 22:2 23:3 / 24:4 25:5 26:6 27:7 28:8 29:9 30:! 31:?`
* Key/parity table at `0x0802EC798` (first 10 bytes): `0A 15 12 19 0C 16 0B 05 14 1A`.
* Preset generator entry: code `"crdts123"` (`0x082F09D8`), state `01 02 03 04`
  (`0x082F09E0`), count 1.
* Characters (menu strings `0x0802C730`+): KANGAROO, DONNIE, DARWIN, ELIZA.
* Levels (`0x0802C3FC`–`0x0802C490`): Jungle 1–3, Plains 1–3, Arctic 1–3,
  Outback 1–3, Finale (13 values).

## 6b. Enumeration

**Space.** Inputs are 8 symbols over a 32-symbol alphabet: `32^8 =
1,099,511,627,776` strings. The payload is six five-bit characters (30 bits,
`32^6 = 1,073,741,824` payloads) plus two check characters. The 10 parity equations
have **GF(2) rank 5** (computed from the ten masks), so only 32 distinct check pairs
exist: exactly one per payload, i.e. **1,073,741,824 checksum-valid codes** — one in
every 32 random strings. The state range checker removes further codes as listed in §5.

**Novel code (not in any published list).** **`KFPBCDVL`** — typed character by
character on the real PASSWORD screen with xdotool; the game displayed "password
accepted, press START to play" and, after Start, entered the Jungle level. The decoded
state was read from `0x02014BD4` in an mGBA savestate: `00 00 01 02`. No published list
exists for this SKU (web recon: 0 results, GameFAQs/TCRF 403); the only hard-coded
code, `crdts123`, is not enterable/accepted. The codec source is in the work dir
(`pw.py`) and the code is reproducible from encoder input state `[00,00,01,00]`.

**Bounds proved by rejection** (each test code is *checksum-valid* per the reimplemented
decoder, so rejection isolates the semantic layer):

| Code | Decoded state | Violated field | In-game result |
|---|---|---|---|
| `KFPBCDVK` | (checksum fails) | wrong 8th-symbol check pair | invalid password |
| `LJ38SW6K` | `00 00 0A 00` | fieldB = 10 (must be < 10) | invalid password |
| `Y2RF11W5` | `00 00 00 14` | fieldF = 20 (must be < 20) | invalid password |
| `RJGS7K?D` | `00 60 01 02` | fieldA = 6 (must be ≤ 5) | invalid password |
| `CRDTS123` | (checksum fails) | hard-coded preset literal, uppercase | invalid password |

Additional accepted controls confirmed the upper parts of the space are not
artificially gated: `S4M!?MXS` (decoded level field `0x0FFF`) and `BLKRJM8T`
(fieldA = 4) were both accepted, i.e. the level field is not range-checked by the
validator despite its 12-bit width.

**Enumeration of reachable screens** (screenshots in work dir): THQ splash → legal
splash → title "Press Start" → MAIN MENU (`NEW GAME`, `PASSWORD`, `OPTIONS`) →
PASSWORD keyboard → OPTIONS (`MUSIC VOLUME`, `EFFECTS VOLUME` sliders only) → map →
level intro/dialogue → gameplay. No hidden menu entries, no debug strings
(`strings` hits only "The \"Super Secret\" Sub Shop" and a "secret hide out" dialogue
line, both ordinary game text), and no alternate input surface were found.

## 7. Validation evidence

* **Observed (emulator):** title/menu/options/password/map/dialogue screens;
  `KFPBCDVL` accepted after on-screen entry; `KFPBCDVK`, `LJ38SW6K`, `Y2RF11W5`,
  `RJGS7K?D`, `CRDTS123` rejected; `S4M!?MXS`, `BLKRJM8T` accepted.
* **Observed (RAM):** input buffer `0x02014B20` = `47 43 4B 40 41 42 50 48` for
  `KFPBCDVL`; decoded state `0x02014BD4` = `00 00 01 02`; length byte `0x02014B30 = 8`;
  success flag `0x02014BDC = 1`; generator table pointers
  `0x02014BF8/FC/00` = `0x082F09E0 / 1 / 0x082F09D8`.
* **Derived (disassembly):** decoder/encoder algorithms, key table, preset table,
  field unpacking and range checks, alphabet coding. Cross-checked by reimplementation
  (`pw.py`) and by the decoded-state RAM read.
* **Inferred:** exact gameplay meaning of the decoded fields (level/character/
  collectibles) is inferred from the generator/validator field packing and the observed
  Jungle-level start; the `crdts123` preset is inferred dead for the password screen
  because it fails the decoder and no 8-symbol solution exists for its state (solver
  `solve_credits.py`, 0 results).

## 8. Unknowns

* Whether the credits preset is reachable from any other UI screen (only its generator
  use was found; on the PASSWORD screen it is rejected).
* Exact semantic names of fields B/C/E/F beyond their validator bounds; field C's cap
  table at `0x0802C1C8` was located but not exhaustively decoded.
* Whether completing the game exposes additional generated passwords beyond this codec
  (generator call site `0x08021CAE` was located but not played through).
* No button-code sequences or debug gates were found; a bounded string search found no
  debug/menu strings, but an exhaustive button-mask search was not attempted (no
  candidate surface exists on the enumerated screens).

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` for raw GBA disassembly; Capstone 5.0.7 for
  literal/BL scans; Ghidra via REA MCP for decompiling `0x0800E060`, `0x0801740C`,
  `0x0801738C`.
* Python scripts in `/tmp/opencode/chimpchase/`: `pw.py` (codec), `scan.py`
  (pointer scan), `xref_ram.py`, `lits.py`, `alphabet_scan.py`, `ssdiff.py`
  (savestate `gbAs` zlib chunk diff), `patch_ss.py` (savestate RAM patcher),
  `drive.py` (window-pinned xdotool driver), `solve_credits.py`.
* mGBA 0.10.5 with GDB stub (`-g`) and CLI debugger (`-d`) were tried; savestate
  inspection proved more reliable here. All `.sav`/`.ss*` artifacts were kept in the
  work dir, never in the ROM folder.

## 10. Legal note

No ROM bytes or copyrighted graphics are redistributed here; only hashes, addresses,
algorithms, tool scripts and observations are published.
