# Teenage Mutant Ninja Turtles 2: Battle Nexus (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Teenage Mutant Ninja Turtles 2: Battle Nexus.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `TMNT GBA 2` |
| Game code / maker | `BT2E` / `A4` (Konami) |
| Version | `0x00` |
| Region / serial | USA — `AGB-BT2E-USA` |
| Entry word | `0xEA00002E` (stock ARM branch; no cracktro/trainer) |
| CRC32 | `802FC7C1` (matches published AGB-BT2E-USA) |
| MD5 | `da96ce67d0ddad72e032632c8fd9994a` |
| SHA-1 | `f42d0131e908942bf84d2323739ce015ee930142` |
| SHA-256 | `fb728fd8e940f35112f9b41b42288455d0acdc69bc4e88c0ea56667a53abd670` |

## 2. Executive summary

The game has one developer-intended cheat surface: a **7-symbol password
system** reached from `MODE SELECTION → INPUT PASSWORD`. Its alphabet is the
five turtle/Shredder icons `{L, M, D, R, S}` (stored internally as symbol indices
`0..4`), giving a canonical space of **5^7 = 78,125** inputs.

The validator at ROM `0x0808914C` is a **table lookup**, not a checksum: it
compares the entered symbol vector, through an ASCII translation table, against
seven NUL-terminated strings in a table at `0x0863B240`. A loop-bound quirk
(`for r4 = 6 .. 1`) means the first table entry is never tested, so exactly
**six codes are accepted**, returning dispatch indices `1..6`. They unlock
Battle courses 16–18 and Race courses 16–18. All six appear in published GBA
lists (SuperCheats); the seven-string table's unused entry `LSRSDSM` is dead.

A **novel accepted input that appears in no published list** was minted by
exploiting a translation-table overread: symbol index `91` aliases `'S'`
because byte `0x0863B2BC + 91` is `0x53`. The vector
`[2, 2, 1, 91, 3, 4, 1]` (written as `DD{S-alias}SMSR`, i.e. "DD◇SMSR") is
translated by the ROM into `DDRSMSR`, returns `r0 = 1`, and unlocked Battle
course 16 in the emulator (screenshot `novel2c.png`, flag `0x03003C64 = 0x8001`).
It was injected at the validator-entry breakpoint and then confirmed by the
game's own OK button — a debugger-assisted entry, labelled as such.

The 21 seven-letter "Passwords" published for the GameCube/PC versions
(`Abyss = SDSDRLD`, etc.) are **not** in this ROM; `SDSDRLD` is rejected in
game with `r0 = 0`. The `DISPLAY PASSWORD` screen's `LLRLDMD` (advertised there
for the GameCube version) is likewise rejected (`r0 = 0`).

A debug-menu framework ("TANIMURA MENU", "MAP SCROLL TEST", "TEST 0..3",
"RIDE MODE") is present in ROM with handler tables at `0x084FF88C` and
`0x084FF900`, but no caller/BL/literal xref reaches its dispatcher
(`0x0807E6D8`); reachability from normal play is unproven (§16.3 dead-code
case). No button-code mask table was found; `0x04000130` has exactly one
literal reference in the image.

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, `-3` scale.
Keymap: A = `x`, B = `z`, D-pad = arrows, Start = `Return`; hold ~150 ms.

Menu path (ground truth, each step screenshotted):

1. Title → `PRESS START` → intro cutscene → `FILE SELECTION`.
2. Choose file 1 → `CONTINUE` → `PLAY SELECTION` (`SINGLE PLAY`) →
   `TURTLE SELECTION` → `MODE SELECTION`.
3. `MODE SELECTION` entries, in order: `STORY MODE`, `RACE MODE`,
   `BATTLE MODE`, `INPUT PASSWORD`, `DISPLAY PASSWORD`.
4. `INPUT PASSWORD`: seven icon slots. Left/right moves the cursor;
   up/down cycles the icon; moving to `OK` and pressing A submits. The
   symbol-index vector lives at `0x0200D722` as seven 16-bit values.

Published-code check: navigate to slot 1, cycle each icon to spell
`D D R S M S R` (indices `2 2 1 4 3 4 1`), select `OK`, press A. Result:
`Saving...` → `MAP SELECTION` with course **16** unlocked. This was confirmed
with a debugger-assisted buffer write plus the real OK press (see §7).

Novel-code check: at the validator-entry breakpoint `0x0808914C`, write
`w/2 0x0200D722 2`, `0x0200D724 2`, `0x0200D726 1`, `0x0200D728 91`,
`0x0200D72A 3`, `0x0200D72C 4`, `0x0200D72E 1`, then `continue`. The game
translates index `91` to `'S'` and accepts the code as `DDRSMSR`.

## 4. Address map

All addresses are ROM (`0x08...`) unless marked RAM.

| Address | Meaning |
|---|---|
| `0x08088D80` | OK-button handler; calls validator at `0x08088D8E`, then dispatcher at `0x08088DA2` |
| `0x0808914C` | **Password validator** (Thumb). Returns `r0 = 0` reject, `1..6` dispatch index |
| `0x080891A0` | Validator return point (`r0 = r4`) — convenient breakpoint |
| `0x080891B8` | Unlock dispatcher; `cmp r0,#6`, jump table at `0x080891CC` |
| `0x080891CC` | 7-entry jump table → `0x080891E8` (reject), `...1F4/1FE/208` (Battle 16/17/18), `...22C/236/25C` (Race 16/17/18) |
| `0x08017C34` / `0x08017FD4` | Battle-side / Race-side unlock writers used by the dispatcher |
| `0x0863B240` | 7-pointer table of password strings |
| `0x0863B25C` | `"SRMLDDR"` (entry 6, Race 18) |
| `0x0863B264` | `"MDSMSDM"` (entry 5, Race 17) |
| `0x0863B26C` | `"RDLDSMD"` (entry 4, Race 16) |
| `0x0863B274` | `"LMSLSRS"` (entry 3, Battle 18) |
| `0x0863B27C` | `"SMRDLML"` (entry 2, Battle 17) |
| `0x0863B284` | `"DDRSMSR"` (entry 1, Battle 16) |
| `0x0863B28C` | `"LSRSDSM"` (entry 0 — **skipped** by validator loop) |
| `0x0863B294` | 10-pointer table used by DISPLAY PASSWORD (first 5 are the strings above; rest are graphics) |
| `0x0863B2A8` | 5-entry icon-graphics pointer table (`0x086516F4`, `0x08651714`, `0x08651734`, `0x08651754`, `0x08651774`) |
| `0x0863B2BC` | **Translation table** bytes `"LRDMS\\0\\0\\0"` followed by pointer bytes — the overread source of symbol aliases |
| `0x0863B1E7` | ASCII hint string shown on DISPLAY PASSWORD (GameCube cross-promo) |
| `0x084FF308` | `"MAP SCROLL TEST"` debug label |
| `0x084FF870` | `"%1P EXIT = PUSH B BUTTON"` debug label |
| `0x084FF914` | `"TANIMURA MENU"` debug label |
| `0x084FF924` | `"TEST 0   TEST11"`, etc. |
| `0x084FF88C` | Debug handler pointer table 1: `0x0807E6F9`, `0x0807E765`, `0x0807E881`, `0x0807EA5D` |
| `0x084FF900` | Debug handler pointer table 2: `0x0807C689`, `0x0807CB6D`, `0x0807CDE9`, `0x0807E119` |
| `0x0807E6D8` | Debug menu dispatcher (index in debug state +4 selects handler) |
| RAM `0x0200D710` | Password/menu state struct base |
| RAM `0x0200D712` | 7-byte ASCII display buffer (`"LLRLDMD"` observed) |
| RAM `0x0200D722` | **7 × 16-bit input symbol indices** |
| RAM `0x03003C64` | `0x8001` after Battle-course-16 unlock (observed) |
| RAM `0x03003C96` | `0x0001` after unlock (observed) |

## 5. Algorithm

Exact model of `0x0808914C` (Derived from disassembly, then validated against
the live ROM with breakpoints):

```python
ALPHA = "LRDMS"                 # index 0..4 -> character
TRANS = rom[0x63B2BC:0x63B2BC+160]   # byte at 0x0863B2BC+v
TABLE = ["LSRSDSM","DDRSMSR","SMRDLML","LMSLSRS",
         "RDLDSMD","MDSMSDM","SRMLDDR"]

def tr(v):
    return chr(TRANS[v]) if 0 <= v < len(TRANS) else '\0'

def validate(indices):              # indices = 7 signed 16-bit values
    first = tr(indices[0])          # fast first-symbol filter
    for e in range(6, 0, -1):       # r4 = 6..1 -- entry 0 is NEVER checked
        s = TABLE[e]
        if s[0] != first:
            continue
        if all(s[i] == tr(indices[i]) for i in range(1, 7)):
            return e                # 1..6
    return 0                        # reject
```

Notes:

* The first character is checked only through the `input[0] → ASCII` filter;
  positions 1–6 are compared against the table string via the same translation
  table.
* The `r4` loop counter doubles as the return/dispatch value; entry 0 would
  return `0`, identical to rejection, so `LSRSDSM` is unreachable twice over.
* `tr()` is an *overread*: any index whose byte in the adjacent ROM data is one
  of `L/R/D/M/S` aliases that symbol. Within indices `0..148` there are **26**
  such aliases (canonical 0–4 plus `9,13,17,21,25 → D`, `91 → S`,
  `105,109,113,117,121,125,129,133,137,141,144 → R`, `145 → D`,
  `146 → M`, `147 → L`, `148 → S`). The UI itself cycles only `0..4`, so these
  are reachable only through RAM/debugger input.
* Dispatcher `0x080891B8` maps `r0 = 1,2,3` to Battle courses 16,17,18 via
  `0x08017C34`, and `r0 = 4,5,6` to Race courses 16,17,18 via `0x08017FD4`.

## 6. Tables

### Accepted codes (all six published; complete accepted set)

| Code | Return `r0` | Unlock | ROM string address |
|---|---:|---|---|
| `DDRSMSR` | 1 | Battle course 16 | `0x0863B284` |
| `SMRDLML` | 2 | Battle course 17 | `0x0863B27C` |
| `LMSLSRS` | 3 | Battle course 18 | `0x0863B274` |
| `RDLDSMD` | 4 | Race course 16 | `0x0863B26C` |
| `MDSMSDM` | 5 | Race course 17 | `0x0863B264` |
| `SRMLDDR` | 6 | Race course 18 | `0x0863B25C` |
| `LSRSDSM` | — | **dead** (entry 0, skipped by loop) | `0x0863B28C` |

Published-list verification: the six accepted strings match the GBA bonus-course
list on SuperCheats exactly (including `SRMLDDR`, which the DISPLAY PASSWORD
hint also calls out for the GameCube version). No typo or OCR-correction was
needed. The 21 console cheat passwords were searched in the ROM as ASCII,
`+0x20`, 8-bit symbol indices and 16-bit symbol indices: zero genuine hits
(one 7-byte index match at `0x7445A7` is inside unsigned audio sample data).

## 6b. Enumeration

**Space definition.** Alphabet = 5 icons `{L,M,D,R,S}` → internal indices
`0..4`; length fixed at 7; no checksum; one 7-entry string lookup with a
first-symbol fast filter. Canonical space = `5^7 = 78,125`. The table stores
7 strings but the validator loop covers only entries 6..1, so the effective
accepted set is 6 values (7.68e-5 of the space).

**Whole-space proof (§16.9).** The Python model in §5 was run over all 78,125
canonical vectors. Result: **exactly 6 accepted**, with return values 1–6 and
codes identical to the published GBA list. No truncation, hidden entry or
reserved-symbol hole exists in the canonical space.

**Novel code (not in any published list).**

| Property | Value |
|---|---|
| Symbol-index vector | `[2, 2, 1, 91, 3, 4, 1]` |
| As glyphs | `D D R ◇ S M S R` where `◇` = out-of-alphabet index 91 |
| ROM translation | `tr(91) = 'S'` (byte at `0x0863B2BC+91`, file `0x63B317`, is `0x53`) → code reads as `DDRSMSR` |
| Model result | `r0 = 1` |
| Live ROM result | Breakpoint `0x080891A0`: `r4 = 1`; after one step `r0 = 1` (log line `p r0 → 1`) |
| In-game effect | `Saving...` → `MAP SELECTION`, Battle course **16** unlocked; RAM `0x03003C64 = 0x8001` |
| Evidence | `novel2c.png` (MAP SELECTION with course 16), `dbg2.py` log excerpt above |
| Entry method | Debugger-assisted: indices written at validator-entry BP, then the game's own OK button pressed. Not pressable on the on-screen keypad (UI wraps 0–4) — labelled as such. |

Why it is novel: every published GBA/Race/Battle password uses only the five
canonical icons; this accepted input uses an undocumented 92nd symbol value and
exercises the translation-table overread path. It is an alias of `DDRSMSR`, not
a new course — a 16.4b-style alias finding.

**Bounds proven by rejection (live ROM, breakpoint at `0x080891A0`, step, `p r0`).**

| Input | Indices | Observed `r0` | Interpretation |
|---|---|---:|---|
| Near-miss `DDRSMS` + `L` | `[2,2,1,4,3,4,0]` | 0 | last-symbol change rejected |
| Console "Abyss" `SDSDRLD` | `[4,2,4,2,1,0,2]` | 0 | console password absent from GBA ROM |
| Display hint `LLRLDMD` | `[0,0,1,0,2,3,2]` | 0 | GameCube cross-promo code rejected on GBA |
| Dead table entry `LSRSDSM` | `[0,4,1,4,2,4,3]` | 0 | confirms loop skips entry 0 |
| Out-of-alphabet `DDGSMSR` (index 6 → NUL) | `[2,2,6,4,3,4,1]` | 0 | NUL translation rejected |
| Default on-screen code `LSRSDSM` | — | no transition | same, via plain GUI OK press |

Every rejected input left the game on `INPUT PASSWORD` with no unlock and no
save screen; every accepted input produced the save screen and an unlock.

**Button codes / debug menus (bounded negative).** `strings` found no
`DEBUG`, `SECRET`, `cheat` or `password generator` labels; the only
`PASSWORD` hit is the GameCube hint. `0x04000130` has exactly one literal
reference, so there is no obvious key-history matcher. The debug framework
does exist (§4) but its dispatcher has zero BL/literal xrefs, so it is either
dead code or gated by an unlocated mechanism — reachability is not claimed.

## 7. Validation evidence

* **Observed (emulator):** boot, screen walk to INPUT PASSWORD; icons change
  with Up/Down; OK press with canonical `DDRSMSR` (RAM-written) produced
  `Saving...` then MAP SELECTION with course 16 (`after_ddrc.png`,
  `after_savec.png`); novel alias code produced the same transition
  (`novel2c.png`); rejected inputs stayed on INPUT PASSWORD
  (`after_deadc.png`, `reject1c.png`).
* **Observed (live RAM, mGBA `-d` CLI debugger):** input buffer
  `0x0200D722 = 0002 0002 0001 0004 0003 0004 0001`; validator-entry BP hits
  at `0x0808914C` with `lr = 0x08088D93`; return BP at `0x080891A0` gives
  `r4 = 1` for the novel code and `r4 = 0` for every rejection; post-unlock
  `0x03003C64 = 0x8001`, `0x03003C96 = 0x0001`.
* **Derived (disassembly):** validator loop bounds, first-char filter,
  translation-table overread, dispatcher jump table, dead entry 0, and the
  exact 6-code accepted set (78,125-input offline enumeration).
* **Inferred:** that the debug handler tables are unreachable in retail
  (no xref found is consistent with, but does not prove, dead code).
* **Limitation:** canonical codes were submitted through the game's OK button
  with the buffer prepared by the debugger; a fully keypad-only entry of a
  published code was not performed. The novel alias code is inherently not
  keypad-reachable.

## 8. Unknowns

* Whether any normal gameplay action (specific story clear, button combination
  at boot, or save flag) can reach the `TANIMURA MENU` / `MAP SCROLL TEST`
  debug framework.
* The exact semantics of RAM `0x03003C64 = 0x8001` vs `0x03003C96 = 0x0001`
  (both changed after the battle-course unlock; the CodeBreaker "unlock all
  courses" code writes `0xFFFF` to `0x03003C64/66/94/96`).
* Whether the `DISPLAY PASSWORD` value `LLRLDMD` is static or varies with
  save progress (only one save state was observed).
* The 21 console cheat passwords may work in the GameCube/PC SKUs; this report
  only establishes their absence and rejection in `BT2E`.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings` — Phase 0/recon.
* `arm-none-eabi-objdump -M force-thumb` and a small Capstone wrapper
  (`dis.py`) with PC-relative literal resolution — disassembly/xrefs.
* Custom Python scripts in `/tmp/tmnt2/`: `xref.py` (pointer-scan),
  `litscan.py` (literal scan), `enumerate.py` (exhaustive validator model),
  `dis.py`, `dbg2.py`, `testcode.py`.
* mGBA 0.10.5 `-d` CLI debugger driven through a PTY (`script`) and a
  `tail -f` FIFO bridge for stable live RAM reads/writes and breakpoints;
  `xdotool` for GUI input; `scrot`/ImageMagick for screenshots.
* REA/Ghidra was attempted for decompilation but raw 8 MiB auto-analysis
  exceeded the 330 s startup deadline; all conclusions here come from
  objdump/Capstone plus live emulator evidence.

**Legal note:** no ROM image, extracted graphics, or game assets are
redistributed here; only addresses, hashes, algorithms and original analysis.
