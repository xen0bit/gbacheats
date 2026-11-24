# The Incredibles: Rise of the Underminer (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Incredibles: Rise of the Underminer.gba` |
| Size | 8,388,608 bytes (0x00800000, 8 MiB) |
| Header title | `INCREDBLROTU` |
| Game code | `BIQE` (US), maker `78` (THQ), rev `00`, version `0x00` |
| Complement / checksum | `0x34` / `0x0000` (rebuilt-header artifact; entry `0xEA000031` is stock, no cracktro) |
| MD5 | `50d0ca20b90c0b2e46fe5a33d9ea6d8b` |
| SHA-1 | `69352c762c306ce5efbf4606e1fb9bb1bde6189a` |
| SHA-256 | `0308a3db8e870f20d78221b05192b2ad3cab922020e8639d8a0aebdbcbeea4bc` |
| Developer (splash) | Helixe; MusyX audio by Factor 5 |
| Analysis ROM | exact file above, independently analysed (sibling "The Incredibles" report is a different SKU) |

Address convention: file offset `F` → ROM address `0x08000000 + F`.

## 2. Executive summary

This GBA SKU **has a real, developer-intended in-game password system**. The main menu
(`NEW GAME / PASSWORD / OPTIONS / CREDITS`) exposes a **PASSWORD** screen with six slots
and a 32-symbol keyboard. There are **two independent validators behind that one screen**:

1. A **13-entry hard-coded developer table** (`0x0846B3A4` pointer table, `0x0846B3D8`
   result bytes) whose accepted codes are names in leetspeak (`H3L!X3`, `M4TT!!`,
   `K3V!N!`, `CR3D!T`, …) and a reserved/profanity block. A match returns effect IDs
   1–9 dispatched through a nine-way jump table at `0x08022124`.
2. An **algorithmic (generated) code system**: a 30-bit packed payload transformed by
   `0x080225C4`, checked for reserved words by `0x08022514`, then validated by
   `0x080222E8` / `0x08022260`. This is the interesting surface: it accepts a large
   family of short, compressed codes, e.g. `GFBBBB` → GIANT ROBOT FACTORY 3 and
   `BBFBBB` → CORRUPTORATOR 1. Pressing OK on the result screen **starts that level**.

All codes below were minted from the format and confirmed on the real screen; several
are aliases of each other. `BBBBBB`, `R3T9RD` and `B1TCHK` are rejected with the
visible `INVALID` overlay, which bounds the reserved-word and structural checks.

No GameShark/CodeBreaker/AR material was used or reported.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, window focused with
  `xdotool windowactivate --sync`; XTEST key events, 70 ms hold / 120 ms gap.
* Keymap: A = `x`, B = `z`, Start = `Return`, D-pad = arrow keys. `Shift+F1..F9` saves
  savestates (used as a RAM oracle; `gbAs` PNG chunk → zlib → raw state, see §9).
* Boot → splash → Helixe logo → title (`PRESS START`) → Start → main menu → Down → A
  enters PASSWORD.
* Keyboard grid (verified visually and against the literal at `0x08042934`):
  `B C D F G H J K / L M N P Q R S T / V W X Y Z 1 2 3 / 4 5 6 7 8 9 ? !`.
  Cursor starts on `B`; D-pad moves, A selects a symbol, B deletes one symbol,
  the **sixth selection auto-submits**.
* Example: enter `G F B B B B` → result screen `GIANT ROBOT FACTORY 3 / PASSWORD
  GFBBBB / OK` → A starts the level.

## 4. Address map

| ROM / RAM address | Meaning | Evidence |
|---|---|---|
| `0x08042934` | 32-byte alphabet `BCDFGHJKLMNPQRSTVWXYZ123456789?!` | literal + 8 xrefs |
| `0x08042954` | first password string `LLVVLL` (41 NUL-terminated, 4-byte-aligned strings through `0x08042A97`) | dump |
| `0x0846B3A4` | **Table A** — 13 pointers, newest-first, to developer passwords | disassembly literal `0x80223CC` |
| `0x0846B3D8` | **Table A results** — 13 bytes, effect IDs | disassembly literal `0x80223D0` |
| `0x0846B3E8` | **Table B** — 13 reserved/leetspeak words (`R3T9RD` … `PR!CKK`) | dump |
| `0x0846B438` | **Table C** — 4 reserved words (`B!TCH`, `PR1CK`, `PR!CK`, `B1TCH`) | dump |
| `0x0846B448` | **Table D** — 3 reserved words (`FVCK`, `D!CK`, `D1CK`) | dump |
| `0x0802237C` | Table-A validator (input `r0` = 6 bytes, returns effect ID or 0) | BL from `0x08024A86` |
| `0x08022514` | Reserved-word matcher over B (20 slots), C (4), D (4) | BL from `0x080226FC` |
| `0x080225C4` | Payload transform / range decoder | BL from `0x080226D0` |
| `0x080222E8` | Algorithmic validator: unpack fields from packed 30-bit `v` | BL from `0x080272E` |
| `0x08022260` | Final range/consistency gates; clears flag bit `0x02` in struct `[0x0A]` | BL from `0x080235E` |
| `0x08022124` | 9-way effect dispatcher for Table-A IDs 1–9 | jump table `0x0802213C` |
| `0x08022220` | Applies decoded save state (loads the advertised level) | BL from `0x08024AC4` |
| `0x08024A20` | Password-screen submit handler (length==6 → both validators → INVALID) | disassembly |
| `0x0201DF44` | keyboard cursor column (u8) | savestate diff |
| `0x0201DF48` | keyboard cursor row (u8) | savestate diff |
| `0x0201DF4C` | number of entered symbols (u8) | savestate diff |
| `0x0201DF50..55` | the six entered bytes, `symbol_index + 0x40` | savestate diff |
| `0x0201DF64` | transient `INVALID` flag (1 for ~0.1–0.2 s on rejection) | savestate sampling |
| `0x0201DE00` | global game-state struct; fields written by `0x080222E8` (`+0x1C..+0x31`) | disassembly + RAM read |

## 5. Algorithm

### 5.1 Input encoding

The keyboard stores each selected symbol as `index + 0x40` (index into the alphabet
string). Observed for `H3L!X3`: bytes `45 57 48 5F 52 57`. The table validator converts
with `char = ALPHA[(byte - 0x40) & 31]`, so the on-screen glyphs spell the canonical
password directly.

### 5.2 Table validator (`0x0802237C`)

```
buf[0..5] = ALPHA[(input[i] - 0x40) & 31]; buf[6] = 0
for i in 0..12:                      # loop bound cmp r4,#12
    if strcmp(buf, TABLE_A[i]) == 0:
        return TABLE_A_RESULT[i]     # 1..9
return 0
```
Caller (`0x08024A84`): nonzero → sound `0x60`, effect via `0x08022124(id)`, screen state
7. Zero → try the algorithmic validator; zero again → `INVALID` overlay.

### 5.3 Algorithmic validator (`0x080226D0`)

```
if strlen(input) != 6: reject
if canonical(input) in TABLE_B ∪ TABLE_C ∪ TABLE_D: reject        # 0x08022514
transform(input)                                                   # 0x080225C4
v = Σ (input[i] & 31) << (5*i)                  # 30-bit payload, input[0] = LSB
if validate(v): return effect through 0x08022220 else reject      # 0x080222E8/60
```

`transform` packs the typed indices into `v` first, then, for a small set of compact
ranges, expands it back into six alphabet characters using the reserved-word tables:

* `100 <= v <= 119` → copy `TABLE_B[v-100]` over the six bytes;
* `256 <= v <= 383` → `b[0] = ALPHA[(v-256)&31]`, `b[1..] = TABLE_C[(v-256)>>5]`;
* `1024 <= v <= 4095` → `b[0] = ALPHA[(v-1024)&31]`,
  `b[1] = ALPHA[((v-1024)>>5)&31]`, `b[2..] = TABLE_D[(v-1024)>>10]`;
* otherwise no expansion; then every byte is normalised to `0x40 + index` by searching
  the alphabet (`0x08042690` loop), with non-alphabet bytes becoming `0`.

`validate(v)` (verified field extraction against a live RAM read after `BBFBBB`):

```
level4 = (v % 25002) << 2 ; if level4 == 100000: level4 = 99996
q = v / 25002
f1 = q & 15 ; q >>= 4
f2 = q % 10 ; q /= 10
f3 = q & 7  ; q >>= 3
f4 = q % 5  ; q /= 5
f5 = q                          # must be <= 1
final gates (0x08022260): f4<=2, f2<=7, f3<=5, struct[0x28]<=8,
                          plus f1/f2 cross-checks when f5==0
```
Live RAM after starting the level from `BBFBBB` showed
`f1=8, f2=1, f3=3, f4=2, f5=1` at `0x0201DE1D/1F/1E/20/29`, matching this extraction.
The exact `rem` bound in the final gates was not isolated (§8).

## 6. Tables

### 6.1 Table A — developer passwords (`0x0846B3A4`, results `0x0846B3D8`)

| # | Code | Effect ID | # | Code | Effect ID |
|---:|---|---:|---:|---|---:|
| 0 | `H3L!X3` | 3 | 7 | `SHNBRT` | 8 |
| 1 | `P4TMC!` | 1 | 8 | `MDSK!P` | 8 |
| 2 | `X4V!3R` | 2 | 9 | `4NDR3W` | 8 |
| 3 | `M4RK!!` | 5 | 10 | `M4TT!!` | 5 |
| 4 | `GDZGL4` | 6 | 11 | `K3V!N!` | 5 |
| 5 | `ZQMB!3` | 7 | 12 | `LLVVLL` | 9 |
| 6 | `B!LL!!` | 1 | | | |

`H3L!X3` = Helixe (the developer), `CR3D!T` (`0x080429BC`) is a further stored string.
IDs 1–9 dispatch to nine distinct effect functions at `0x08022140`–`0x08022198`.

### 6.2 Reserved words (rejected)

* Table B (13): `R3T9RD MYB1CH SH!TRD B!TCHB B!TCHH B!TCHJ B!TCHK PR1CKD PR1CKC
  PR1CKK PR!CKD PR!CKC PR!CKK`
* Table C (4): `B!TCH PR1CK PR!CK B1TCH`; Table D (3): `FVCK D!CK D1CK`.

## 6b. Enumeration

### Space definition

* Keyboard/validator input: **32 symbols × 6 positions = 32^6 = 1,073,741,824**
  representable strings; on-screen alphabet `BCDFGHJKLMNPQRSTVWXYZ123456789?!`.
* Table subsystem: **exactly 13 accepted strings** (loop bound `cmp r4,#12` at
  `0x080223DA`; all 13 entries dumped in §6.1). Closed set, proved statically by
  running the loop bound over the table — no 14th entry can be reached.
* Algorithmic subsystem: 6×5-bit indices pack into a **30-bit payload** (max
  `1,073,741,823`); `v / 25002` yields the field word, `v % 25002` the level word.
  The transform reserves the payload ranges `[100,119]`, `[256,383]` and `[1024,4095]`
  (20 + 128 + 3072 compact seeds). Final gates constrain `f5<=1, f4<=2, f2<=7, f3<=5`.
  The exact accepted count was not exhaustively computed (§8); the structure and a
  large accepted family are demonstrated below.

### Novel codes (absent from every published list; none exists on the web for this SKU)

| Code | Result screen / effect | Proof |
|---|---|---|
| `GFBBBB` | GIANT ROBOT FACTORY 3 | accepted, `res_GFBBBB.png` |
| `BLBBBB` | BLIZZARD BACKDOOR 1 | accepted, `res_BLBBBB.png` |
| `BBFBBB` | CORRUPTORATOR 1 | accepted, `res_BBFBBB.png`; OK → gameplay `after_ok.png` |
| `HFBBBB` | UNDERMINER (final level) | accepted, `res_HFBBBB.png` |
| `JFBBBB` | GIANT ROBOT FACTORY 1 | accepted, `res_JFBBBB.png` |
| `BMBBBB` | CORRUPTORATOR 1 (alias of `BBFBBB`) | accepted, `res_BMBBBB.png` |
| `BPBBBB` | GIANT ROBOT FACTORY 3 (alias of `GFBBBB`) | accepted, `res_BPBBBB.png` |

All seven were typed through the on-screen keyboard with byte-for-byte RAM verification
of the six slots before submission. `BBFBBB` was additionally followed through OK into
the actual level (sprite, HUD and score visible), and RAM fields were read (`§5.3`).
The `BMBBBB`/`BBFBBB` and `BPBBBB`/`GFBBBB` pairs demonstrate **aliasing**: distinct
payload strings reach the same level, so unused payload bits exist (guide §16.4b).

### Bounds proved by rejection

| Input | Layer exercised | Observation |
|---|---|---|
| `BBBBBB` | structural (all-zero payload) | `INVALID` overlay, `invalid_crop.png`; transient flag `0x0201DF64=1` |
| `R3T9RD` | reserved-word matcher, Table B | `INVALID`, `res_R3T9RD.png` |
| `B1TCHK` | reserved-word matcher, Table B | `INVALID`, `res_B1TCHK.png` |
| `H3L!X3` | Table A positive control | accepted, state byte `0x0201DF64=0` |

Note the deliberate trap: `R3T9RD` is the *canonical expansion* of the accepted compact
code `GFBBBB`, yet typing `R3T9RD` directly is rejected by the reserved-word gate. This
is why the algorithmic family is not discoverable from the stored strings alone.

## 7. Validation evidence

* **Observed** (emulator/screenshots/RAM): every screen in the walk (splash, Helixe logo,
  title, main menu, difficulty NORMAL/SUPER/INCREDIBLE!, PASSWORD keyboard, INVALID
  overlay, password-result badge, gameplay); input buffer bytes, cursor bytes and length
  via savestate diffs; acceptance and rejection outcomes; all novel-code → level mappings;
  RAM fields after `BBFBBB`.
* **Derived** (disassembly): both validators, the three table bases and result bytes, the
  transform's three compact ranges, the field extraction with divisor 25002, the
  nine-way effect dispatcher, and the submit handler's accept/reject branches.
* **Inferred**: exact final gate arithmetic in `0x08022260` for bounds not exercised
  (the `rem` clause reads as `<=200` but accepted codes have larger `rem`, so one
  operand/condition was misread; the field gates derived from the same function are
  corroborated by live RAM). Meaning of effect IDs beyond their dispatcher targets.

## 8. Unknowns

* Exact accepted count of the algorithmic subsystem (2^30 payloads) was not enumerated;
  the observed family and the three reserved ranges are proven, not exhaustive.
* One condition in `0x08022260` (apparent `level4 <= 800`) contradicts observed
  accepted codes; treated as a misread, not a game rule. The corroborating gates and
  the field extraction are solid.
* The precise gameplay effect of each Table-A effect ID 1–9 was not individually played
  out; `H3L!X3` was observed accepted and returned to the main menu.
* OPTIONS/CREDITS screens were present in the main menu and the text bank but were not
  fully captured (navigation drift after the password tests); they are not cheat-related.

## 9. Tooling

* `strings -t x`, `xxd`, Python literal/xref scanners, `arm-none-eabi-objdump -M force-thumb`.
* Capstone 5.0.7 (installed beforehand) for Thumb literal/BL scans.
* mGBA 0.10.5 (`-3`, `-g` used briefly, then plain `-3` with savestates), Xvfb `:319`,
  openbox, `xdotool`, `scrot`, ImageMagick `convert`.
* Helpers in `/tmp/incredibles2/`: `stateutil.py` (zlib-decompress mGBA `gbAs`
  state), `pwdriver.py` (RAM-feedback keyboard navigation), `batch_test.py`
  (restart + enter + screen-based accept/reject), `model.py` (offline field decoder),
  plus the screenshot evidence listed in §6b.
* No ROM or copyrighted assets are redistributed; only addresses, hashes, codes and
  our own screenshots/tools are reported.

## 10. Legal note

Analysis only; no ROM image, extracted graphics, music, or game text is published here.
