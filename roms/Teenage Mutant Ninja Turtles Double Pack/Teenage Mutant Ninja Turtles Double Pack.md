# Teenage Mutant Ninja Turtles Double Pack (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Teenage Mutant Ninja Turtles Double Pack.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| Header title | `TMNT GBA 1+2` |
| Game code / maker | `BT8E` / `A4` |
| Version / complement / checksum | `0x00` / `0xEE` / `0x0000` |
| Entry word | `0xEA00002E` (stock crt0; no cracktro patch observed) |
| MD5 | `f80cad97ed415aba1ec81d983fb4ae56` |
| SHA-1 | `15cbff45ce0cb35f3e6a6059ada2710f0cec05c3` |
| SHA-256 | `05267b1bdce75047fa77a16cbdce324368d5f033b057cff48a5c228973975779` |

**Layout (§5.4b).** A full-file scan for the 156-byte Nintendo logo produced exactly **one** hit, at file offset `0x0`. This is a *single integrated image*, not two concatenated ROMs: the 8 MiB boundary at `0x800000` is continuous code/data with no second header. Both games live in one image and share the shell + much of the engine. All ROM addresses below are absolute (`0x08000000 + file offset`); the halves are referred to as "TMNT1" (roughly file `0x0`–`0x8FFFFF`) and "TMNT2" (file `0x800000`–`0xFFFFFF`).

## 2. Executive summary

Both games implement **closed, hard-coded password tables** — not generators:

* **TMNT1**: a 5-symbol password (alphabet L/R/D/M/S, 5¹⁵ = 3,125 spellings) checked by a validator at `0x08032E34` against **exactly 5** ten-byte records. All 5 are on published lists. `SRLMD` was entered on the real screen and unlocked **Course 4** (screenshot + 392-byte SRAM diff).
* **TMNT2**: a 7-symbol password (5⁷ = 78,125 spellings) checked by a validator at `0x088195CC` against **exactly 6** seven-character strings. All 6 are on published lists. `DDRSMSR` was entered on the real screen and unlocked **Course 16** (screenshot).
* **Button code**: one 10-press sequence (`U U D D L R L R B A`) stored as u16 masks at `0x08E0C584`, matched by `0x0881DB00`; published as COWABUNGA (TMNT2) / "Very Hard" (TMNT1).
* **Debug content**: a full "TANIMURA MENU" with 17 TEST entries survives in TMNT2 (`0x08CBE208`), with its dispatch table and function pointers intact. No retail input path to it was found in the screens walked, and the setup function has zero BL callers — reported as a bounded gated/dead-code negative, not as "not looked for".

Because both password spaces are closed tables containing only published values, **no novel accepted code exists** in this ROM. That is a proven bounded negative with counts; §6b gives the rejection evidence and the exact enumeration.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `mgba -3 -d <rom>` under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`. The `-d` command-line debugger is essential: the platform's GDB stub on port 2345 was occupied by another agent, so `r/2`, `w/2`, `frame`, `b/t` and `!CTRLC` (Ctrl-C break-in) via a pty bridge were used instead.
* Keymap: A = `x`, B = `z`, Start = `Return`, D-pad = arrow keys. Hold 60–100 ms.
* **TMNT1 password path**: language select → A; splash → A (top logo); title → A; Mode Selection → Down, Down, A → PASSWORD. Up/Down cycles the symbol under the cursor (L→S→M→D→R→L); Left/Right moves between the 5 slots; A moves focus to OK; A submits. Accepted → "SAVING…" → Course Selection.
* **TMNT2 password path**: splash → Down, A (bottom logo); title → A; File Selection → A; Difficulty → A; Mode Selection → Down×3, A → INPUT PASSWORD. Same input semantics over 7 slots. Accepted → "Saving…" → Map Selection with the unlocked course lit.
* Codes verified in-game: TMNT1 `SRLMD` → Course 4; TMNT2 `DDRSMSR` → Course 16. Rejections: TMNT2 `SSR?SDSM` (edited first symbol) and `LSRSDSM` (ROM's own default string) — both returned to the input screen with no Saving screen and no unlock.
* Deterministic RAM tests: with the core paused in the `-d` debugger, write the 5 symbol halfwords at `0x020068B8` (TMNT1) or the 7 at `0x0200D732` (TMNT2), `c`, then press A twice.

## 4. Address map

All addresses are ROM unless marked RAM. "File" is the raw offset.

| Item | ROM / RAM address | File offset | Evidence |
|---|---|---|---|
| Header / Nintendo logo | `0x08000000` | `0x0` | observed |
| Single logo hit (no second header) | — | `0x0` only | derived (full-file scan) |
| **TMNT1 password validator** | `0x08032E34` | `0x32E34` | derived + breakpoint hit |
| TMNT1 validator literal: buffer base | `0x08032EA4` → `0x020068B0` | `0x32EA4` | derived |
| TMNT1 validator literal: table base | `0x08032EA8` → `0x0847C73C` | `0x32EA8` | derived |
| TMNT1 code table (5 × 10 bytes) | `0x0847C73C` + `0x0A,14,1E,28,32` | `0x47C73C` | derived (bytes decoded) |
| TMNT1 password caller / flag setter | `0x08032B0E` | `0x32B0E` | derived (lr at breakpoint) |
| TMNT1 input symbol buffer (5 u16) | RAM `0x020068B8` | — | observed (RAM diff) |
| TMNT1 "SECRET PASSWORD" hint strings | `0x0847C818` … `0x0847CA2A` | `0x47C818` | observed |
| **TMNT2 password validator** | `0x088195CC` | `0x8195CC` | derived |
| TMNT2 validator literal: code table | `0x0881962C` → `0x08E0BB88` | `0x81962C` | derived |
| TMNT2 validator literal: ASCII alphabet | `0x08819630` → `0x08E0BC04` | `0x819630` | derived |
| TMNT2 code-string pointer table | `0x08E0BB88` (7 pointers) | `0xE0BB88` | derived (bytes) |
| TMNT2 code strings | `0x08E0BBA4` … `0x08E0BBD4` | `0xE0BBA4` | observed (`strings`) |
| TMNT2 symbol→ASCII alphabet | `0x08E0BC04` = `"LRDMS\0"` | `0xE0BC04` | derived |
| TMNT2 input symbol buffer (7 u16) | RAM `0x0200D732` | — | derived + observed |
| TMNT2 ASCII mirror of entry | RAM `0x0200D722` | — | observed |
| **Button-code mask table** | `0x08E0C584` (10 u16) | `0xE0C584` | derived (literal search) |
| Button-code validator | `0x0881DB00` | `0x81DB00` | derived |
| Button-code success call | `0x087A86DC` | `0x7A86DC` | derived |
| GameCube-version password hint | `0x08E0BB2F` | `0xE0BB2F` | observed |
| TANIMURA MENU title | `0x08CBE208` | `0xCBE208` | observed |
| TANIMURA MENU 17 items | `0x08CBE218` … | `0xCBE218` | observed |
| Debug menu handler pointer table | `0x08CBE180` (4 Thumb ptrs) | `0xCBE180` | derived |
| Debug menu descriptor (count 0x11) | `0x08CBE1E0` | `0xCBE1E0` | derived |
| Debug menu setup function | `0x0880E8FC` (no BL callers) | `0x80E8FC` | derived |

## 5. Algorithm

### 5.1 TMNT1 validator (`0x08032E34`, Thumb)

```
buffer = (u16*)0x020068B0          # symbols at +8,+A,+C,+E,+10
table  = (u16*)0x0847C73C
for r5 = 5 down to 1:              # 5 records, newest first
    rec = 0x32 + (5-r5)*(-0x0A)    # offsets 0x32,0x28,0x1E,0x14,0x0A
    if buffer[0..4] == table[rec + 0,2,4,6,8]:
        return 5 - r5 + 1          # 1-based index; nonzero = accepted
return 0
```

Caller `0x08032B0E` checks a gate (`[state+0x0C] & 9`), calls the validator, and on nonzero result writes unlock bits into the save block, plays sound `0x6A`, saves, and jumps to Course Selection. On zero it plays `0x6C` and stays on the password screen.

### 5.2 TMNT2 validator (`0x088195CC`, Thumb)

```
input  = (s16*)0x0200D720          # first symbol at +0x12 (0x0200D732)
alpha  = (u8*)0x08E0BC04           # "LRDMS\0"
table  = (u32*)0x08E0BB88          # pointer table, 7 entries
first  = alpha[ input[0x12/2] ]
for r4 = 6 down to 1:              # SIX iterations — entry 0 is skipped
    ent = 0x18 + (6-r4)*4          # 0x18,0x14,0x10,0x0C,0x08,0x04
    s   = (char*)table[ent]        # 7-char NUL-terminated string
    if s[0] == first and all(s[i] == alpha[input[i]] for i in 1..6):
        return r4                  # nonzero = accepted
return 0
```

Entry `table[0]` = `LSRSDSM` is the **default display** string and is never compared — a sentinel, not a code.

### 5.3 Button code (`0x0881DB00`, Thumb)

```
expected[] = {U,U,D,D,L,R,L,R,B,A}   # active-high u16 masks at 0x08E0C584
held = ~KEYINPUT (active-high)
if (held & expected[index]) == 0: index++         # press matched
else:
    if (held & 0x3FF & ~expected[index]) != 0: index = 0   # any EXTRA button resets
if index == 10: call 0x087A86DC                   # set COWABUNGA / very-hard flag
```

Held/extra-button semantics matter: `U+A` together at the `U` step fails the `bics` test and resets the progress.

## 6. Tables

### 6.1 TMNT1 accepted codes (alphabet L=0, R=1, D=2, M=3, S=4 as u16)

All 5 records at `0x0847C73C`; record stride 10 bytes; order below is the validator's newest-first search order.

| ROM record | Code | Published meaning |
|---|---|---|
| `0x0847C76E` | `LSDRM` | Playmates toy database / Bonus course 5 |
| `0x0847C764` | `SRLMD` | Casey Jones / Bonus course 4 |
| `0x0847C75A` | `MSSLD` | Michelangelo unlimited fire shurikens / Bonus course 3 |
| `0x0847C750` | `SSLDM` | Leonardo unlimited shurikens / Bonus course 2 |
| `0x0847C746` | `LSMMS` | Bonus course 1 |

The record at `0x0847C73C` = `LRDMS` is the **default display**, not checked (same sentinel pattern as TMNT2).

### 6.2 TMNT2 accepted codes

| String address | Code | Published effect |
|---|---|---|
| `0x08E0BBA4` | `SRMLDDR` | Course 18 race / Playmates bonus |
| `0x08E0BBAC` | `MDSMSDM` | Course 17 race |
| `0x08E0BBB4` | `RDLDSMD` | Course 16 race |
| `0x08E0BBBC` | `LMSLSRS` | Course 18 battle |
| `0x08E0BBC4` | `SMRDLML` | Course 17 battle |
| `0x08E0BBCC` | `DDRSMSR` | Course 16 battle |
| `0x08E0BBD4` | `LSRSDSM` | **not checked** — default display sentinel |

Other published TMNT2 passwords (e.g. `DSRDMRM` infinite health, `RSRLRSM` infinite shuriken, `DRSLLSR` poison) were searched for literally across all 16 MiB and are **absent**. This is the same pattern as TMNT1: the Double Pack keeps only the bonus-course unlock codes.

### 6.3 Button code

`0x08E0C584`: `40 00 40 00 80 00 80 00 20 00 10 00 20 00 10 00 02 00 01 00` = U,U,D,D,L,R,L,R,B,A. One table in the whole image; one action (`COWABUNGA` flag via `0x087A86DC`).

### 6.4 Debug menu

`TANIMURA MENU` (`0x08CBE208`) with entries `TEST 0`–`TEST 10`, `TEST11`–`TEST15`, `EXIT`, plus `MIC`, `DON`, `RAP`, `LEO`, `RIDE MODE`, `STAGE`, `PLAYER`, `MAP SAMPLE`, `HOGE`, `UGA`, `GA`. Descriptor at `0x08CBE1E0` gives item count `0x11` (17); handler pointers at `0x08CBE180`: `0x0880E8FD`, `0x0880E969`, `0x0880EA85`, `0x0880EC61`.

## 6b. Enumeration

### Space definition

| System | Alphabet | Length | Representable | Accepted | Fraction |
|---|---|---|---|---|---|
| TMNT1 password | 5 symbols | 5 | 5⁵ = 3,125 | 5 | 0.16 % |
| TMNT2 password | 5 symbols | 7 | 5⁷ = 78,125 | 6 | 0.0077 % |
| Button code | 10 button masks | 10 (exact) | 1 table entry | 1 | — |

Both code systems are **pure lookup tables** with no checksum, field packing, generator, or alias bits. The accepted sets were read exhaustively out of the validators' own tables (5 records at `0x0847C73C+{0x0A..0x32}`; 6 strings via `0x08E0BB88+{0x04..0x18}`), not inferred from a published list.

### Novel codes — bounded negative

Every accepted value in both tables appears in published lists (GameFAQs, IGN, GGmania, supercheats, TMNTForever, jeuxactu). Because the validators only compare against those fixed records, **the count of novel accepted codes is provably 0** — there is no unadvertised combination to mint. This is the required bounded negative with counts, rather than an untested absence.

Rejections actually observed in the emulator:

1. **TMNT2 `SSR?SDSM`** (first symbol edited away from the ROM's default) — entered through the on-screen 7-slot widget; result: returned to INPUT PASSWORD with no Saving screen and no course unlocked.
2. **TMNT2 `LSRSDSM`** — the unpublished string at `0x08E0BBD4`, absent from every published list searched. It is table entry 0, which the validator's `r4 = 6 … bgt` loop never visits. Entered on the real screen: rejected identically. This proves the "newest-first, skip entry 0" bound dynamically, not just statically.
3. **TMNT1 published-but-absent code**: e.g. `MLMLS` (Donatello double defense) was searched for as the u16 record `03 00 00 00 03 00 00 00 04 00` and is **not present** in the ROM; the TMNT1 validator has only 5 records, so it cannot be accepted. The only published TMNT1 codes retained in the Double Pack are the 5 bonus-course codes above.

### Accepted codes proven in-game

* `SRLMD` → **Course 4** unlocked; screenshot `result_srlmd2.png`; SRAM `before.sav` → `after_srlmd.sav`: 392 of 512 bytes changed (fresh save initialised; byte `0x0B` `0xFF → 0x01`).
* `DDRSMSR` → **Course 16** unlocked in Map Selection; screenshot `g2_course16.png`.

### Hidden/debug content enumeration

The TANIMURA MENU is real, fully present, and its 17 entries and handler pointers were enumerated. Reaching it from retail input was **not** achieved: a BL-target scan found **zero** callers of the setup function `0x0880E8FC`; it is only reachable through the static function-pointer table `0x08CBE180`, and none of the reachable screens (splash, language select, both titles, both mode selections, file/difficulty select, password screens, course/map selection, stage selection) offered an entry. This is a bounded **gated/dead-code** negative (§16.3 categories 2/4), not "not tested". No CodeBreaker/AR codes were used or reported as in-game cheats.

## 7. Validation evidence

* **Observed** (emulator + debugger): both boot screens, all menus listed above; `SRLMD` → Course 4 and `DDRSMSR` → Course 16 screenshots; SRAM diff for the TMNT1 unlock; RAM reads of `0x020068B8` (5 u16) before/after a symbol change and of `0x0200D722`/`0x0200D732` (TMNT2 entry buffer); breakpoint hit at `0x08032E34` with `lr = 0x08032B13`.
* **Derived** (disassembly + byte decode): both validators and their exact table bases/strides; the skip-entry-0 loop bound; the button-code mask table and its extra-button reset rule; the single-header layout; the debug-menu descriptor and the zero-BL-caller count.
* **Inferred** (not fully exercised): the semantic labels "Casey Jones", "Playmates database", etc. come from published lists, not from in-game observation — only the *course unlocks* were visually confirmed. The exact runtime effect of the COWABUNGA flag was not played through to the story-mode ending.

## 8. Unknowns

* Which button combination (or save flag) opens the TANIMURA MENU in retail play. The code and dispatch table are present, but no reachable caller was identified.
* The "SECRET PASSWORD" / GameCube-version hint at `0x0847C818` and `0x08E0BB2F` refers to a pattern that appears to be rendered as **art**, not ASCII; the literal pattern was not decoded from the tile banks. The 7-char code strings adjacent to the TMNT2 hint are the six course codes plus the sentinel, so the hint most likely refers to those.
* The remaining ~18 published TMNT1 and ~21 published TMNT2 passwords are absent from this image; whether this is a deliberate Double Pack cut or a regional revision difference was not established.
* The COWABUNGA flag was set by entering the sequence at the TMNT2 title, but the story-mode completion message was not replayed to confirm the visible payoff.

## 9. Tooling

* `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python byte scans (`findtable.py`, `findpw.py`).
* Capstone 5.0.7 (`dis2.py`, `dis_range.py`) and `arm-none-eabi-objdump -M force-thumb` for disassembly.
* mGBA 0.10.5 with `-d` pty debugger behind a Python TCP bridge (`dbgbridge.py`, port 2347), supporting `r/2`, `w/2`, `x/2`, `b/t`, `frame`, `reset`, `!CTRLC`.
* mGBA savestate PNG `gbAs` chunk decompressed with Python `zlib` for RAM dumps (§16.13); `before.sav`/`after_srlmd.sav` for SRAM diffing.
* Xvfb :318 + openbox, `xdotool` XTEST input, `scrot` screenshots. All helper scripts and screenshots were under `/tmp/tmntdouble/`.

No ROM bytes or copyrighted assets are reproduced in this report; only addresses, hashes, algorithms and the short published code strings are documented.
