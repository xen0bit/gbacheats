# Super Army War (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Super Army War/Super Army War.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `ARMY WAR` |
| Game code | `BG6E` (AGB-BG6E-USA) |
| Maker | `EB` (Atlus USA / Neko Entertainment; splash: "SUPER ARMY WAR ©2005 Olivier DENIS … NEKO entertainment") |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock retail branch) |
| Fixed byte / complement / checksum | `0x96` / `0x83` / `0x0000` |
| CRC32 | `BAF484BE` (matches 3rd party cheat indexes USA record) |
| MD5 | `1b93ef2e096d7eb72e76b8662a3e74ec` |
| SHA-1 | `2840446005baa66e8b224f756d07caa7de25a5dc` |
| SHA-256 | `fd88b21fee3c8630d3cb278ffdf788fb10b1981dc83bd776009c3b377268c334` |

Retail image: no cracktro, no appended trainer, stock crt0. File offset = ROM address − `0x08000000` throughout.

## 2. Executive summary

The game has a deliberate **6-digit numeric password system** on the main-menu `CODE` screen. It is
**not** a generator/algorithm: it is an exact-match lookup against three hard-coded 16-entry tables
(Easy/Normal/Expert) at `0x081EFF30`, `0x081EFF74`, `0x081EFFB8`, plus **three extra special-value
comparisons** in the caller (`444442`, `119119`, `777777`). There is no checksum, no bit-packing and
no second algorithmic format: the value is entered as BCD (one decimal digit per nibble) and compared
bit-for-bit.

The published 3rd party cheat indexes/3rd party cheat index lists are **incomplete**, not wrong: they omit 26 of the 48 table
entries. Those 26, plus the two unpublished special values, are genuine novel codes. One of them —
Easy level 7 = **`684464`** — was typed on the real screen and produced RAM `difficulty=0,
level_index=6` and the in-game level-7 splash and mission. Bounds were proven with a rejected input
(`999999`) that left game state untouched.

The on-screen alphabet is only 8 symbols (`1 2 3 4 6 7 8 9`): a D-pad direction + A selects a digit,
the centre cell is not `5`, and `0` has no key. The input space is therefore 8⁶ = **262,144**, of
which **49 distinct inputs** are accepted (46 unique table values + 3 specials; `222222` appears in
all three tables but always resolves to Easy because the scan is easy-first).

## 3. How to reproduce

* Emulator: `mgba 0.10.5`, `DISPLAY=:316 SDL_AUDIODRIVER=dummy mgba -3 <rom>` under Xvfb + openbox.
* Keymap (mGBA SDL default): A = `x`, B = `z`, Start = `Return`, Select = `BackSpace`, D-pad = arrows.
* Path: boot → splash (press Start/any key) → main menu `CAMPAIGN BATTLE CODE CREDITS` → `Right`,
  `Right`, `A` → `CODE` screen.
* Entering a digit: hold the D-pad direction(s) for that cell and tap **A** while held. Direction →
  digit mapping (derived from `0x08016112`–`0x080161A6`, confirmed by `122888` → level 2):

  | Direction | Digit | Direction | Digit |
  |---|---|---|---|
  | Up+Left | 1 | Down+Left | 7 |
  | Up | 2 | Down | 8 |
  | Up+Right | 3 | Down+Right | 9 |
  | Left | 4 | Right | 6 |

  The validator fires automatically on the 6th digit; no separate OK press is needed.
* Repro helper scripts: `/tmp/superarmy/ui.py` (focus/key/screenshot),
  `/tmp/superarmy/enter.py` (`python3 enter.py 684464`).
* Savestates `F1`–`F9` save, `F1`–`F9` load; mGBA `.ssN` files are PNGs with a zlib `gbAs` chunk
  (raw 397,312 bytes; IWRAM at raw `0x19000`, EWRAM at `0x21000`). This was the RAM-reading method
  because the `-g` stub never bound a TCP port in this environment (see §9).

Codes tested in emulator: `122888` (published Easy L2), `684464` (novel Easy L7), `777777`
(unpublished special), `444442` (published Modern War), `119119` (unpublished special), `222222`
(alias), `999999` (rejected).

## 4. Address map

| Address (ROM) | Meaning |
|---|---|
| `0x08015E3C` | **Password validator** (Thumb). Scans the three 16-entry tables, returns level index in `r0` (`-1` = no match) and writes resolved difficulty to `0x03003E80`. |
| `0x08015EB0` | Table accessor: `get_code(difficulty=0 → Easy, 1 → Normal, else Expert)[index]`. |
| `0x08015EE4` | Unrelated scripted-event command builder (shares the region; not the validator). |
| `0x08016112`–`0x080161A6` | D-pad → digit-nibble mapping (reads key shadow `0x03004080`). |
| `0x08016288`–`0x08016294` | Packs 6 digits into BCD at `0x03000180`, counts to 6, then calls validator at `0x08016354`. |
| `0x08016354` | Validator caller / effect dispatcher: special-code comparisons, level/difficulty writes. |
| `0x080163FC` | Literal `0x00444442` |
| `0x08016400` | Literal `0x00119119` |
| `0x08016404` | Literal `0x00777777` |
| `0x081EFF30`–`0x081EFF6F` | Easy table, 16 × u32 BCD |
| `0x081EFF74`–`0x081EFFB3` | Normal table, 16 × u32 BCD |
| `0x081EFFB8`–`0x081EFFF7` | Expert table, 16 × u32 BCD |
| `0x0801ECCC` | Duplicate special-code recogniser; **dead code** (no BL, branch or pointer xref). Same 3 constants. |
| `0x083FBA40` / `0x083FBA48` | ASCII `ATLUS` / `MASTER V1012`, drawn by `0x080150A2` when `0x030041C0 == 1`. |

RAM (`IWRAM`, observed via savestate diff):

| Address | Role | Observed values |
|---|---|---|
| `0x03000180` | Entered/resolved BCD code | `0x222222`, `0x122888`, `0x684464` |
| `0x03003E80` | Resolved difficulty | `0` Easy, `1` Normal |
| `0x03003EE0` | Copy of active code | `0x122888`, `0x684464` |
| `0x030041E0` | Level index (`level number − 1`) | `1` for `122888`, `6` for `684464` |
| `0x03002440` | Flag set by `777777` | `0 → 1` |
| `0x030041C0` | Flag toggled by `119119` | `0 → 1` |
| `0x030049E0` | Flag toggled by `444442` (Modern War) | `0 → 1` |
| `0x03004080` | Key shadow (active-low GBA masks) | `0x3FF` idle |

## 5. Algorithm

Exact reimplementation of `0x08015E3C` + caller:

```python
EASY   = [0x222222,0x122888,0x121789,0x882244,0x248622,0x211786,0x684464,0x242887,
          0x322987,0x111114,0x137737,0x777322,0x448632,0x777332,0x124444,0x122846]
NORMAL = [0x222222,0x222888,0x123789,0x882246,0x248624,0x214786,0x684463,0x244887,
          0x321987,0x111112,0x137731,0x777326,0x148632,0x777331,0x122444,0x222846]
EXPERT = [0x222222,0x221888,0x113789,0x882222,0x248224,0x224786,0x684466,0x224887,
          0x324987,0x111116,0x137733,0x777346,0x144632,0x777431,0x142444,0x212846]

def validate(input_bcd):
    # input_bcd is six decimal digits packed one per nibble (0x122888 for "122888")
    for i in range(16):
        if EASY[i] == 0:          # terminator (one past the last entry)
            return None
        if EASY[i]   == input_bcd: return ('level', 0, i)   # difficulty=0
        if NORMAL[i] == input_bcd: return ('level', 1, i)
        if EXPERT[i] == input_bcd: return ('level', 2, i)
    return None

def submit(input_bcd):
    r = validate(input_bcd)
    if input_bcd == 0x444442:  ram[0x030049E0] ^= 1; return   # special
    if input_bcd == 0x119119:  ram[0x030041C0] ^= 1; return   # special
    if input_bcd == 0x777777:  ram[0x03002440]  = 1; return   # special
    if r is None:              reset_to(0x222222); return     # rejection
    unlock_level(r[1], r[2])                                  # difficulty, index
```

Notes:
* The terminator is `EASY[i] == 0`; all 16 entries of all three tables are non-zero, so exactly 16
  indices are tested. Table strides are 4 bytes; there are no variable-length records.
* The easy table is checked first, so the duplicated `222222` always resolves to Easy index 0.
  Its Normal and Expert rows are unreachable aliases (confirmed in RAM: `difficulty=0` after
  typing `222222`).
* The caller's three special comparisons happen **after** the table scan, so a special value would
  have to be absent from all tables (all three are).
* The second recogniser at `0x0801ECCC` has the same constants but no callers or pointer xrefs — dead
  code, not an extra entry point.

## 6. Tables

### 6.1 Complete accepted set (48 table records + 3 specials)

Index *i* = level number − 1. Values are the literal 6-digit strings; enter exactly as shown.

| # | Easy | Normal | Expert |
|---:|---|---|---|
| 1 | 222222 | 222222† | 222222† |
| 2 | 122888 | 222888 | 221888 |
| 3 | 121789 | 123789 | 113789 |
| 4 | 882244 | 882246 | **882222** |
| 5 | **248622** | 248624 | **248224** |
| 6 | **211786** | 214786 | **224786** |
| 7 | **684464** | **684463** | **684466** |
| 8 | 242887 | **244887** | **224887** |
| 9 | 322987 | **321987** | **324987** |
| 10 | 111114 | **111112** | **111116** |
| 11 | 137737 | **137731** | **137733** |
| 12 | 777322 | **777326** | **777346** |
| 13 | 448632 | **148632** | **144632** |
| 14 | **777332** | **777331** | **777431** |
| 15 | 124444 | **122444** | **142444** |
| 16 | 122846 | **222846** | 212846 |

Bold = absent from every published list consulted (3rd party cheat indexes). † = duplicate `222222`; only the Easy row is reachable.

### 6.2 Special codes

| Code | Effect (RAM observed) | Published? |
|---|---|---|
| `444442` | `0x030049E0 ^= 1` — Modern War mode (published label) | Yes |
| `119119` | `0x030041C0 ^= 1` — when 1, `0x080150A2` draws `ATLUS` + `MASTER V1012` | **No** |
| `777777` | `0x03002440 = 1` — enables a branch at `0x08014DD0` in mission logic | **No** |

### 6.3 Screen enumeration (all reachable screens walked)

| Screen | Evidence |
|---|---|
| Main menu | `CAMPAIGN BATTLE CODE CREDITS`, 4 items, all entered |
| `CODE` | 3×3 digit pad (centre = non-digit), 6-digit display, suffix `CODE` |
| `CAMPAIGN` | level splash (observed `7` after `684464`), mission then starts |
| Mission | HUD, pause menu `CONTINUE / RESTART / QUIT` and `ALLY CODE 122888` |
| `BATTLE` | 4×4 grid of 16 battle slots (1–16) |
| `CREDITS` | scrolling staff roll with portraits |

No hidden/debug menu, level-select overlay, sound test or button sequence was found. Keyword scan of
all 48,114 ASCII strings found only `CODE` (`0x083FB984`), `ATLUS` / `MASTER V1012`
(`0x083FBA40/48`) and the localised in-game messages around `0x083FB644`–`0x083FBC08`; the majority
of UI text is font/tile-indexed, so it was decoded by walking the screens above rather than by
`strings`. The CodeBreaker "Complete Mission [Press Select+Up]" entry on 3rd party cheat indexes are a
cheat-device button activator (guide §16.20), not an in-game trigger, and is out of scope.

## 6b. Enumeration

**Space definition.** Alphabet = the 8 reachable keypad symbols `{1,2,3,4,6,7,8,9}`; fixed length 6;
one decimal digit per nibble (BCD), most-significant digit first; no checksum, no reserved bits in the
stored word beyond the always-zero top nibble. Representable inputs = 8⁶ = **262,144**. (All 51
accepted words happen to contain only those 8 digits; `0` and `5` never appear in any table or
special value.)

**Validator model.** Exact section 5 pseudocode; it agrees with the ROM on all published inputs and
on the rejected probes. It was also cross-checked against the live RAM outcomes of seven typed codes.

**Accepted-set count.** 48 table records − 2 unreachable `222222` aliases = 46 reachable table
values, plus 3 specials = **49 distinct accepted inputs**. Running the validator over the full
8⁶ space yields exactly those 49; the remaining 262,095 inputs are rejected. The game's own scan
stops at the first match, so the two aliased rows cannot be selected by any controller input.

**Novel codes (not in any published list).** 26 table entries + 2 specials. In-game proof:

* `684464` (Easy level 7) — typed on the CODE screen. Savestate RAM: `0x03000180 = 0x684464`,
  `0x03003E80 = 0` (Easy), `0x030041E0 = 6` (level 7). The CAMPAIGN screen then displayed a large
  `7` (`campaign7.png`) and pressing A launched the snow/airfield level with the
  `ACTIVATE SPECIAL WEAPON BROKEN ARROW` briefing (`campaign_afterA.png`). This code is absent from
  all consulted published lists (their Easy column jumps 4 → 8).
* `777777` — typed on the CODE screen. RAM `0x03002440: 0 → 1`; no published source lists it.
* `119119` — typed on the CODE screen. RAM `0x030041C0: 0 → 1`; no published source lists it.
  Its only visible effect (drawing `MASTER V1012`) was **derived** from `0x080150A2` and not seen
  on the four walked menu screens, so it is labelled accordingly in §7.

The other 25 novel table codes are enumerated in §6.1 and are reachable by the same input path;
they were not individually typed, which is the one residual gap in the in-game proof (§8).

**Bounds proven by rejection.**

* `999999` (in-alphabet but not in any table/special): display reset to `222222`, remained on the
  CODE screen, `0x030041E0` unchanged at `0`, `0x03003E80` unchanged at `1`. This proves the match is
  exact and that no algorithmic/partial checksum path exists for arbitrary inputs.
* Digit `5` is structurally unenterable: the centre cell maps to nibble 5 and is explicitly skipped
  (`cmp r6,#5; beq` at `0x08016262`); pressing A there submits/exits rather than appending a digit
  (observed on the CODE screen). Digit `0` has no direction mapping at all. Hence 8⁶, not 10⁶ or 9⁶,
  is the correct upper bound, and codes such as `555555` / `000000` are outside the reachable space.
* No partial-length acceptance: the validator is only called when the digit counter reaches 6
  (`cmp r4,#6; beq 0x08016354`); shorter entries stay on the CODE screen.

## 7. Validation evidence

* **Observed** (emulator/savestate): `122888` → `difficulty=0, index=1` and pause menu showing
  `ALLY CODE 122888`; `684464` → `difficulty=0, index=6`, level-7 splash and level-7 mission;
  `999999` → rejected with state unchanged; `777777` → `0x03002440=1`; `119119` →
  `0x030041C0=1`; `444442` → `0x030049E0=1`; `222222` → `difficulty=0` (alias). All menu screens
  in §6.3 were seen and screenshotted.
* **Derived** (disassembly): the three table bases, the 16-entry stride and terminator, the
  easy-first resolution of `222222`, the three special comparisons and their target flags, the
  direction→digit map, the 8-symbol alphabet bound, the dead duplicate recogniser at `0x0801ECCC`,
  and the `ATLUS`/`MASTER V1012` render branch.
* **Inferred**: the human-facing meaning of `0x030041C0` and `0x03002440` beyond the code paths
  cited; the "Modern War" cosmetic label comes from published descriptions, not from a screenshot
  comparison. The two "no button code / no debug menu" results are bounded by the screen walk plus
  the ASCII string and caller scans in §6.3, not by an exhaustive search of every possible input
  combination.

## 8. Unknowns

* 25 of the 26 novel table codes and the long-term effects of `119119` / `777777` were not played
  through beyond the RAM writes and derived readers.
* Whether `119119`'s `MASTER V1012` text appears on a screen not reached in this walk (the render
  function `0x08014AA0` has no direct BL/pointer xref, so it may live in a jump table).
* `0x0801ECCC` is unreferenced by BL/B/pointer scans; a table-driven call using an offset rather than
  an absolute pointer cannot be excluded, though it recognises only the same three specials.
* mGBA's `-g` GDB stub never opened a listening TCP socket here (port 2345 refused; the process had
  no TCP fd). All RAM claims therefore rest on savestate `gbAs` diffs, cross-checked against the
  visible screen state.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, Python `zlib`/`struct`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for the
  validator, caller, keypad input and literal pools (literal addresses re-read with
  `struct.unpack_from` before following).
* Custom Python scans: Thumb BL target scan, Thumb/ARM PC-relative literal scan, BCD-constant census.
* `mgba 0.10.5` under `Xvfb :316` + openbox, `SDL_AUDIODRIVER=dummy`; `xdotool` key helpers and
  `scrot` screenshots; mGBA `Shift+F1..F9` savestates decoded as PNG `gbAs` chunks.
* No ROM or extracted graphics/audio are redistributed; only addresses, algorithms and hashes are
  published here. Web pages were treated as data; no instructions found in them were followed.
