# LEGO Star Wars II: The Original Trilogy (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Lego Star Wars II: The Original Trilogy/Lego Star Wars II: The Original Trilogy.gba` |
| Size | 16,777,216 bytes (`0x1000000`) |
| Header title | `LSW2GBA` |
| Game code / maker | `BL7E` / `64` (Europe, Rev.00) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Header complement / checksum | `0xEB` (non-standard) / `0x0000` — see note below |
| Build strings | `Jul 10 2006`, `RC 2.00`, `LEGO2010` at `0x080779C0`–`0x080783E0` |
| MD5 | `bd64515fa58ec5052ce4d231e6241f23` |
| SHA-1 | `38f640be68981c258d435bf103ab443346fb5953` |
| SHA-256 | `74b44acfe3b55d4f4c06bcc56ca993a9a8605994a15e3659bf66d568608499fe` |

**Phase 0 result:** exactly **one** Nintendo-logo hit, at file offset `0x4`. No embedded
second header, no appended trainer/cracktro, stock entry branch. The non-standard
complement byte and zero header checksum are header-rebuild artifacts, not evidence of
a patch (BIOS only validates the logo). No GameShark/CodeBreaker codes were used or
report as in-game cheats; a libretro CodeBreaker `.cht` and 3rd party cheat index entries were
seen in web results and explicitly excluded by scope.

## 2. Executive summary

The game has **one developer-intended cheat system**: 5-digit numeric passwords entered
at the Mos Eisley Cantina "?" Codes counter. It is a **closed 22-entry lookup table**,
not a checksum algorithm. The validator at `0x08032FD0` compares five raw digit bytes
against 22 records of 8 bytes each at `0x080770D0`; on a match it dispatches through a
22-entry jump table at `0x08033578`.

The whole space was enumerated: **exactly 22 accepted values out of 100,000**
(`00000`–`99999`), and all 22 are the codes published by 3rd party cheat indexes — there is
**no unpublished accepted code**, so §0.2's "novel accepted code" deliverable is
unachievable *by construction*; this is proven, not assumed (§6b). A novel code
(`75047`) was rejected by the ROM's own validator with no flag change (RAM proof), and
three published codes were accepted with the predicted flag bits set.

The published **6-character alphanumeric codes** (`KSY792`, `CL4U5H`, `HLP221`, …) and
DS button codes (`UDLRAB`, `ABACAB`, `BIGGUN`, …) are for other SKUs: **none appear in
this GBA image** under ASCII, +0x20, BCD, u16/u32 or tile-index encodings.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, `mgba -3 -d ROM`.
* Keymap (mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrows. Hold keys ~70–150 ms (shorter taps are missed).
* Menu path (all screens walked, screenshots on disk in `/tmp/legostarwars2/`):
  boot splash → title `START` → **main menu** (New Game / Load Game / Options) →
  **Options** (Music Volume 5/10, Effects Volume 10/10, Gamma Off, Vehicle Control
  Rotation, Credits) → **Credits** (scrolling AMAZE ENTERTAINMENT) → **New Game slot
  select** (Game 1/2/3) → gameplay (Tatooine/Mos Eisley hub; SELECT switches character;
  tutorials for studs and character switch) → **pause** (Resume / Options / Extras /
  Save & Quit) → **Extras** (16-item ring, all Off) → Cantina interior level-preview.
* **Code-entry screen gate:** the "?" Codes counter is inside Mos Eisley Cantina; the
  save used here had 0 studs / 0% and the counter interaction was not reachable by
  controller alone in this session (§8). Verification therefore used the guide's
  §16.19 technique: the ROM's own validator was **called from mGBA's CLI debugger**
  with a crafted input buffer, and its effects read from RAM. The entry screen itself
  was located statically (input handler `0x08032218`, UI state `0x03004E50`).

## 4. Address map

| Address (ROM/EWRAM) | Meaning |
|---|---|
| `0x080770D0` | 22-record code table, stride 8. Digits at `record+1 … +5` |
| `0x08077180` | Powers-of-ten table `1,10,100,…,10000000` (u32) |
| `0x08032FD0` | Validator (no args; reads input via `[0x03003434]`) |
| `0x08032376` | BL call site of validator (Cantina "?" UI handler) |
| `0x08033540` | Apply dispatcher (arg `r0` = table index) |
| `0x08033578` | 22-entry function-pointer table for the dispatcher |
| `0x080335D0` | Handler for indices 0–17 (level select / level codes) |
| `0x080335D8/E4/FC/08033608` | Handlers for indices 18/19/20/21 (feature toggles) |
| `0x0802FC7E` | Per-frame point in main loop (convenient debugger breakpoint) |
| `0x03003434` | EWRAM global holding pointer to code-entry struct (digits at `ptr+3..+7`) |
| `0x03004780` / `0x030047AC` | Extras-flag global / actual flag word (bits below) |
| `0x03004E40` / `0x03004E50` | Cantina UI state globals |

## 5. Algorithm

Validator `0x08032FD0` (Thumb), exact behaviour:

```
p = [0x03003434]            // pointer to code-entry struct
inp = p + 2                 // validator uses inp[1]..inp[5] = p+3..p+7
for i in 0 .. 21:
    if all(inp[j] == ROM[0x080770D0 + i*8 + j] for j in 1..5):
        apply(i)            // BL 0x08033540
        return
    if i == 21: return      // rejected — no flag write, no apply
```

A 6-bit match bitmask is maintained but the acceptance test only requires bits 1–5,
so the comparison is exact and order-independent only in the sense of a straight 5-byte
`memcmp` against each record. No length check, checksum, PRNG, XOR or substitution is
involved. Input digits are raw bytes `0x00..0x09`.

Dispatcher flags (EWRAM `0x030047AC`):

| Index | Code | Effect | Flag bit |
|---:|---|---|---|
| 0–17 | level codes | level select / transition + byte `+0x6A = 2` | — |
| 18 | `11340` | Sith Mode | `0x00000004` |
| 19 | `70546` | Dancing Girl | `0x00008000` |
| 20 | `75046` | Jedi Spirit | `0x00000080` |
| 21 | `80873` | Bubble Blaster | `0x00000800` |

(Indices 19/21 also call `0x0803369C`, a second unlock helper.)

## 6. Tables

All 22 table records (index, digits, published label; all verified present in ROM):

```
 0 82434 Mos Eisley                11 61806 Sensor Balcony
 1 40214 Obi-wan's House           12 06881 Yoda's Hut
 2 13197 Mos Eisley Cantina        13 31299 Ewok Village
 3 27000 Alderaan                  14 52583 Death Star 2
 4 11911 Trash Compactor           15 20876 Emperor's Lair
 5 80500 Death Star Hanger         16 51999 Death Star Subsector 1
 6 52577 Death Star                17 01138 View Final Movie
 7 42352 Wampa Cave                18 11340 Sith Mode
 8 89910 Millennium Falcon         19 70546 Dancing Girl
 9 50250 The Dark Cave             20 75046 Jedi Spirit
10 08433 Carbonite Chamber         21 80873 Bubble Blaster
```

Extras ring (16 items, all `Off` on a fresh save): Cantina Music, Jabba's Baroque,
Sith Mode, Invincibility, Lightsaber Blue, Lightsaber Red, Lightsaber Green, Jedi
Spirit, Silhouette, Clown, Classic, Bubble Blaster, Egg Blaster, El Pollo Blaster,
Washed Out Mode, Monochrome Mode.

## 6b. Enumeration

* **Space:** 5 decimal digits, alphabet `{0..9}`, length exactly 5 → **100,000**
  representable values. No reserved bits, no checksum field, no second alphabet.
* **Method (§16.9):** reimplemented the validator from the disassembly and ran it over
  all 100,000 inputs (`/tmp/legostarwars2/enumerate.py`). **Exactly 22 accepted**;
  the accepted set equals the ROM table byte-for-byte. The published lists are complete
  and correct for this SKU. **No novel accepted code exists** — the system is a fixed
  table, so §0.2's "mint an unpublished accepted code" is impossible here; the complete
  characterisation is the deliverable instead.
* **Novel code tested (rejected):** `75047` — unpublished (differs from `75046` in the
  last digit). Written to the validator's input buffer and called through the debugger:
  flag word `0x030047AC` stayed `0x00000000` (was reset to 0 immediately before). This
  proves the boundary by rejection.
* **Published codes tested (accepted, RAM-verified through ROM validator):**

  | Input | Flag before | Flag after | Meaning |
  |---|---|---|---|
  | `75046` | `0x00000000` | `0x00000080` | Jedi Spirit unlocked |
  | `80873` | `0x00000000` | `0x00000800` | Bubble Blaster unlocked |
  | `11340` | `0x00000000` | `0x00000004` | Sith Mode unlocked |
  | `75047` (novel) | `0x00000000` | `0x00000000` | rejected |

  Also rejected: out-of-alphabet digits (`10` in any position) and wrong lengths
  (4 and 6 digits) in the Python model; the ROM's straight byte-compare rejects both.
* **Other code surfaces (negative, bounded):** the 6-char alphanumeric codes from PSP/GC
  and the DS button codes have **0 literal hits** in this 16 MiB image (searched ASCII,
  `+0x20`, UTF-16LE, BCD and 5-digit tile encodings). Button-mask sequence search for
  `UDLRAB` (active-high, reversed, active-low, u16 form) and `L+R+Start` found **no
  code table**; dynamic entry of `Up Down Left Right A B` on the title/gameplay screen
  produced no menu or flag change. No debug/secret/password strings were found in the
  ASCII scan or in four candidate font/tile-index decodings of the whole ROM; the only
  ASCII "code"-like strings are TT script event names (`SpawnSecretRoom`,
  `OpenCantinaDoor4x4`, `CheckStudVariable`, …) at `0x0807xxxx`, which are level-script
  event labels, not cheats.

## 7. Validation evidence

* **Observed (emulator):** every screen in §3; all 22 code literals in ROM; the
  debugger-driven validator calls and the flag-word reads above; novel-code rejection.
* **Derived (disassembly):** table layout and stride, validator comparison loop, apply
  jump table and flag bits, UI state machine and input global.
* **Inferred:** the exact physical placement of the "?" counter within Cantina (the
  counter NPCs and red "!" markers were seen in the Cantina level-preview, but the
  interaction itself was gated in this save). The Python model and the ROM agree on all
  4 oracle-tested inputs and on the exhaustive 22-code set.

## 8. Unknowns

* Typing a code on the physical counter screen was not achieved: the fresh save (0 studs,
  0%) could not reach the counter interaction, and direct writes to the UI state global
  (`0x03004E50`) caused a reset. §16.10 classification: **gated feature** (story/
  progression gate), not dead code — the validator has a live BL call site and produced
  RAM effects when invoked. A second analyst with story progress can type any of the 22
  codes at the counter to reproduce the flag effects visually.
* Whether flags `0x8000` (Dancing Girl) and the level-code path behave exactly as
  labelled was derived from code, not separately exercised in the oracle.
* Fetched web pages were treated as data; no prompt-injection payload was encountered.

## 9. Tooling

`python3` + `capstone` 5.0.7, `arm-none-eabi-objdump -M force-thumb`, mGBA 0.10.5 with
CLI debugger driven over a PTY (`dbgserver.py`), `xdotool`/`scrot`/`convert` on `:315`,
Python scripts `findcodes.py`, `xref.py`, `callers.py`, `enumerate.py`, `ss.py`.
No ROM or extracted asset is redistributed; only addresses, hashes, algorithms and
original analysis scripts are published.
