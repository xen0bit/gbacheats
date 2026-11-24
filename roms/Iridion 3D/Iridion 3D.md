# Iridion 3D (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Iridion 3D.gba` (4,194,304 bytes / 4 MiB) |
| Header title | `IRIDION3D` |
| Game code | `AI3E`, maker `5G`, revision/version byte `0x00` |
| Complement / header checksum | `0x4E` / `0x0000` |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| MD5 | `f88df40fedb9d31a6e59dba4a9be1b2a` |
| SHA-1 | `4c9e0f52078d73d5843487de9eab4462c5c153f7` |
| SHA-256 | `8fa3e5bcbd98951dfcddac0c830376f6684ef6c47a9323c9979c1d2ffcfb91a2` |

Phase 0 checks: the whole file contains **one** Nintendo-logo occurrence (file `0x000004`), so there is no
multiboot image, second game or appended trainer. The entry branch is the stock one; the crt0 literal pool
at `0x1C8`/`0x1CC` holds `0x08000215` and `0x08023579` (boot/main). No patch or trainer was detected.
A byte-for-byte copy (`SHA-256` identical) was used for emulation so the ROM folder stayed clean.

## 2. Executive summary

Iridion 3D has **two developer-intended cheat systems**, both entered on the on-screen PASSWORD keyboard:

1. **A 9-symbol progress password** — a 45-bit value packed from the game's 32-symbol alphabet,
   validated by a 7-bit additive checksum plus two range checks at `0x08003068`. This is the
   end-of-level `PASSWORD:` system. The full space is ~1.7×10¹¹ valid codes; a novel code was
   generated, accepted in-game, and its fields confirmed by the HUD.
2. **A hard-coded 10-entry cheat-code matcher** at `0x0800324C`, comparing symbol *indices* against
   inlined byte sequences (`*G4LL3RY*`, `*SH0WT1M3*`, `*CR3D1TS*`, …). All ten entries are
   enumerated below; one (`*SH0WT1M3*`) unlocks the hidden START LEVEL / START AT BOSS debug rows.

There is **no button-code system** for this title in the ROM (no published button combos exist, and the
only password-validator input surface is the symbol keyboard). The hidden debug screen is a real,
reachable feature, not dead code: its two labels are drawn by the normal options renderer at
`0x080027D2`/`0x080027FE` behind a single bit test at `0x080027AC`.

Published lists were mostly correct but not exact: `*SH0WT1M3*` unlocks level select **by itself** (the
published two-step recipe with `*S3L3CT0N*` is unnecessary), the published `67NCBZBJC` is a typo
(correct `67NCBZBMC`), and the widely copied `*1NV1S4BL3*` / `*SHOWT1M3*` / `*S3L3TON*` strings are
**not** in the ROM's matcher.

## 3. How to reproduce

Emulator: `mgba -3` on `DISPLAY=:316` (`Xvfb :316 -screen 0 1024x768x24`, openbox,
`SDL_AUDIODRIVER=dummy`). Keymap used: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. Save state `iridion.ss1` taken at the PASSWORD screen made each test one `F1`.

Menu path (A/`x` confirms, Start/`Return` does **not** confirm in menus):
`title → Start → main menu (START / OPTIONS / PASSWORD) → Down,Down, A → PASSWORD`.

The keyboard is an 11-column × 3-row grid. Left/Right move the column with wrap 0–10
(`0x080037B2`/`0x080037CE`, wrap `0x080038E0`), Up/Down move the row with wrap 0–2
(`0x080037EA`/`0x08003806`, wrap `0x080038EC`); A sets the character, B erases, OK is at row 2 col 10.
Initial cursor is row 2, col 0 (`0`). `scripts/enter.py` reproduces every entry below.

Verified entries (all on the real screen, not debugger calls):

| Input | Observed result |
|---|---|
| `*G4LL3RY*` | Concept-art gallery slideshow opened |
| `*SH0WT1M3*` | OPTIONS gained `START LEVEL 1` and `START AT BOSS NO` |
| `*S3L3CT0N*` | Immediate return to main menu (quick-exit flag) |
| START LEVEL 2 + START AT BOSS YES → Start | `STAGE - 02`, `BOSS: CYTECTOR` |
| `R8NCV6ZPV` (novel) | `STAGE - 01`; HUD score `0043981` (0xABCD), 9 life icons |
| `67NCBZBMC` (repaired published typo) | `STAGE - 03` |
| `R8NCV62PV` (bad checksum) | `WRONG PASSWORD!` |
| `R8NCV62PZ` (f42=5, valid checksum) | `WRONG PASSWORD!` |

## 4. Address map

All addresses are ROM addresses; file offset = address − `0x08000000`.

| Address | Role |
|---|---|
| `0x08002692`–`0x08002840` | Options/debug-menu renderer; hidden-row gate at `0x080027AC` (`ldrb [state+0x2F] & 0x10`) |
| `0x08002C28` | Score/level display helper in password path |
| `0x08003068` | **Progress-password validator** (7-bit checksum + range checks), returns 0/1 |
| `0x0800324C` | **Cheat-string matcher** — 10 inlined symbol-index sequences, returns 0/1 |
| `0x080035E0` | 9-symbol → 45-bit packer (memset 8 bytes; loop 0..8; `0x0802203C` shift/OR; `r5 += 5`) |
| `0x08003628`–`0x08003AAE` | Password keyboard handler (cursor, SET/ERASE, submit) |
| `0x08003A32` | Loads `WRONG PASSWORD!` string (`0x08023C00`) and draws rejection |
| `0x08023B94`–`0x08023C0F` | Plaintext string bank: MUSIC VOLUME, FX VOLUME, MUSIC TEST, FX TEST, REVERSE CONTROL, GAME LEVEL, START LEVEL, START AT BOSS, OK, WRONG PASSWORD! |
| `0x08027256`–`0x080272A8` | Results bank: BOSS:, STAGE CLEAR, ENERGY BONUS:, LIFE BONUS:, NEW SCORE:, PASSWORD:, WELL DONE! |
| `0x0801E353C` region | Ending text; contains `TO ENTER THE GALLERY USE THIS PASSWORT: *G4LL3RY*` at file `0x1E4C3C` |
| `0x0801DEE47` | `Shin'en Multimedia. Code: B.Wodok` — GAX audio-engine banner, **not** a cheat (guide §3.4 false positive) |

State byte used by the debug gate and cheat effects: `struct + 0x2F` (a RAM pointer loaded from the
literal pool at `0x08032B8`, `0x080337C`, …). Bit `0x10` shows START LEVEL / START AT BOSS and also
means gallery/level-select mode; bit `0x20` is set by `*S3L3CT0N*`. Byte `+0x07` is a mode index
(e.g. `0x1A` level select, `0x2F` gallery in the `*G4LL3RY*` path).

## 5. Algorithm

**Alphabet (32 symbols, 5 bits each, row-major on the keyboard):**

```
index:  0 1 2 3 4 5 6 7 8 9 10 | 11 12 13 14 15 16 17 18 19 20 21 | 22..31
char:   B C D F G H J K L M N  |  P  Q  R  S  T  V  W  X  Y  Z  *  | 0 1 2 3 4 5 6 7 8 9
```

**Pack** (`0x080035E0`): `P = Σ_{i=0..8} value(password[i]) << (5*i)` (45 bits, little-endian in an
8-byte accumulator).

**Field layout** (verified against all 18 valid published codes and the novel code's HUD):

```
score    = P & 0x00FFFFFF      bits  0..23   (displayed score)
lives    = (P >> 24) & 0x0F    bits 24..27   (live life icons)
color    = (P >> 28) & 0x03    bits 28..29   (weapon/laser colour index)
b30      = (P >> 30) & 1       bit  30       (hard-mode bit in observed codes)
b31      = (P >> 31) & 1       bit  31
checksum = (P >> 32) & 0x7F    bits 32..38   (7-bit additive check)
stage    = (P >> 39) & 0x07    bits 39..41   (0-based stage; +1 shown on banner)
level    = (P >> 42) & 0x07    bits 42..44   (weapon upgrade level; MUST be 0..4)
```

**Validate** (`0x08003068`), exact reimplementation:

```python
calc = (score + lives + color + b30 + b31 + stage + level) & 0x7F
valid = (calc == checksum) and (calc != 0) and (level < 5) and (score != 0)
```

On success the routine writes the decoded fields into the game-state struct (`+0x14` score,
`+0x02` lives/colour/b31, `+0x20`/`+0x21` colour, `+0x22` b30, `+0x07` `((stage+1)<<4)|1`)
and returns 1; otherwise it returns 0 and the keyboard handler shows `WRONG PASSWORD!`.

Notes on transcription: the Thumb sequence at `0x0803078`–`0x080308C` adds `b30` (logical shift,
`0x0FC0 = lsrs`); Ghidra renders this as a subtraction, which is wrong — adding is what makes
all seven published hard-mode codes validate. Bit `b31` likewise adds 1.

**Cheat matcher** (`0x0800324C`): a chain of `ldrb [r1,#i] / cmp #symbol_index` comparisons. Ten
chains end in a success block that ORs flag bits into `state+0x2F`, writes `state+0x07`, plays a
sound (`0x0800B988`/`0x0800B8E4`) and returns 1; the fall-through at `0x08035D8` returns 0.

## 6. Tables

**All 10 cheat strings (symbol indices → characters; alphabet as above):**

| # | Code string | Success block | Effect (evidence) |
|---|---|---|---|
| 1 | `*PNKRLZ*` (8) | `0x0803284` | `+7=0x10`, `+2 &=~0x20 \|= 5`, `+0x20 \|= 0x80`, `+0x21=28` — pink/special laser (Derived) |
| 2 | `*KYTNN*` (7 + NUL check) | `0x08032F2` | same flag set, `+0x21=30` — weapon variant (Derived) |
| 3 | `*CR3D1TS*` (9) | `0x0803368` | `+0x2F \|= 0x02`, `+7=0x1A` — ending credits music (Derived; published) |
| 4 | `*CHTRSXX*` (9) | `0x08033BC` | `+7=0x71`, `+2 &=~0x80`, `+3=0` — hidden test/display flag (Derived; unpublished) |
| 5 | `*B4RT0*` (7) | `0x080340E` | `+7=0x11`, `+0x2F \|= 0x05` — ship/appearance variant (Derived; unpublished) |
| 6 | `*P1NK*` (6) | `0x0803456` | `+7=0x11`, `+0x2F \|= 0x06` — pink ship variant (Derived; unpublished) |
| 7 | `*G4LL3RY*` (9) | `0x08034B8` | `+0x2F \|= 0x10`, `+7=0x2F` — gallery (Observed) |
| 8 | `*SP33D*` (7) | `0x08034F8` | `+0x2F \|= 0x04` — speed variant (Derived; unpublished) |
| 9 | `*SH0WT1M3*` (10) | `0x0803550` | `+0x2F \|= 0x10`, `+7=0x1A` — START LEVEL / START AT BOSS (Observed) |
| 10 | `*S3L3CT0N*` (10) | `0x08035B4` | `+0x2F \|= 0x20`, `+7=<mode>` — Select returns to title (Observed) |

Published strings **absent** from the matcher (searched symbol-index chains and ASCII):
`*1NV1S4BL3*`, `*SHOWT1M3*` (letter O), `*S3L3TON*`. The ROM uses zero (`0`) where these lists
show `O`, and has no 11-symbol chain at all.

Validation of published 9-char progress passwords (all 19 from 3rd party cheat index board, verified
against `calc()`): 18 pass; `67NCBZBJC` fails (stored check `0x30`, required `0x48`) and its corrected
form `67NCBZBMC` passes and starts Stage 3 in-game.

## 6b. Enumeration

**Space definition.** 32 alphabet symbols × 9 positions = 32⁹ = 35,184,372,088,832 spellings.
Two layers constrain them: the 7-bit checksum (≈1/128) and `level < 5` (5/8); `score != 0` and
`checksum != 0` remove a negligible few. Valid codes ≈ 32⁹ × 5 / (128×8) = **171,798,937,600**
(~1.72×10¹¹), matching the product of independent field widths
(2²⁴ scores × 16 lives × 4 colours × 4 flag bits × 8 stages × 5 levels).

**Novel code (in no published list).** `R8NCV6ZPV`
(`score=0x00ABCD`, `lives=9`, `color=3`, `b30=b31=0`, `stage=0`, `level=4`, `checksum=0x5D`).
Entered on the real PASSWORD screen: game accepted it, showed `STAGE - 01` and the HUD displayed
score `0043981` (= 0xABCD) with **9** life icons — a direct confirmation of the `score` and `lives`
field decoding. This code was derived from the validator, not copied from any web list.

**Bounds proven by rejection.**
* `R8NCV62PV` — identical payload, checksum field incremented by 1 (stored 94, required 93):
  `WRONG PASSWORD!`. This proves the 7-bit check layer.
* `R8NCV62PZ` — checksum recomputed *correctly* but `level = 5`: `WRONG PASSWORD!`. This proves
  the semantic range layer (`level < 5`) exists independently of the checksum.

**Special-code space.** The matcher is a closed set of exactly 10 hard-coded chains; every chain
was enumerated from `0x0800324C`–`0x08035DE` and each string's effect recorded in §6. Because the
comparisons are inline immediates (not a table with a length/count field), no other string can be
accepted by this function. Four unpublished chains (#2, #4, #5, #6, #8) were found that appear in
no 3rd party cheat index list; their effects are labelled Derived (static) because only #7, #9 and #10
were driven in the emulator.

**Button codes.** Bounded negative: no button-combo sequences are published for this SKU, the only
input consumer with cheat semantics is the symbol keyboard, and a search for key-mask sequence
tables found none associated with the password/state-flag code. The in-game PAUSE screen (`PAUSE`
text only, captured) exposes no cheat list.

## 7. Validation evidence

* **Observed** (emulator, screenshots + HUD): every screen walked — title, main menu, OPTIONS,
  OPTIONS with hidden rows, PASSWORD keyboard, gallery slideshow, PAUSE, stage intro and gameplay;
  all ten behaviours in the §3 table; novel code's score/lives in HUD; both rejection screens.
* **Observed** (static bytes/addresses): hashes, single GBA header, stock entry word, the exact
  literal strings and their pointer xrefs, all `cmp #imm` sequences in the two validators.
* **Derived** (disassembly, including Ghidra pseudocode cross-checked with `objdump -M force-thumb`):
  field layout, 7-bit checksum, `level < 5` gate, `state+0x2F` bit meanings, the effects of cheat
  chains not entered in the emulator.
* **Inferred**: friendly names such as "pink laser" / "speed" for the Derived cheat effects; these
  are inferred from the flags set, not from a played-out gameplay result.

Fetched web pages (3rd party cheat indexes boards) were treated strictly as
data; no prompt-injection payload was encountered.

## 8. Unknowns

* Friendly labels for cheat chains #2, #4, #5, #6, #8 are inferred from flag writes; their exact
  visual/gameplay result was not played out in the emulator.
* Bit `b31` and the precise meaning of the `level` field (weapon upgrade vs difficulty) were not
  exhaustively exercised across all five values; the range `0..4` itself is proven by rejection.
* Whether `*1NV1S4BL3*` ever existed in another regional revision (this ROM is `AI3E` Rev 00).

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`, Python 3 (`capstone`
5.0.7, `keystone`), `arm-none-eabi-objdump -M force-thumb`, REA/Ghidra 12.1.4 (raw-binary import,
base `0x08000000`, `analyze_function` for decompilation), mGBA with GDB stub, Xvfb `:316` + openbox,
`xdotool`, `scrot`, ImageMagick, `gdb-multiarch`.

Helper scripts kept in `/tmp/iridion/`: `gen.py` (field packer/encoder + published-code
check), `enter.py` (keyboard-grid driver), `cheats_parse.py` (matcher-chain extractor),
`parse_cheats.py`, `pw.py`, `findbuf.py`, `gdbctl.py`.

Screenshots are kept on disk in that work directory (`170_novel_c.png`, `172_novel_play_c.png`,
`180_badchk_c.png`, `180b_oor_c.png`, `141_showtime_alone2_c.png`, `161_boss_start_c.png`,
`100_gallery_c.png`, etc.) and are not redistributed with this report.

Legal note: no ROM image or extracted copyrighted asset is included here; only hashes, addresses,
algorithms, and original tooling are published.
