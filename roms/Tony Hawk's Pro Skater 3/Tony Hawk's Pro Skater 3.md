# Tony Hawk's Pro Skater 3 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tony Hawk's Pro Skater 3.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `TONY HAWK 3!` |
| Game code | `AT3E` (USA) |
| Maker code | `52` |
| Version | 0x00 |
| Header checksum | 0x0000 (rebuilt-header artifact; complement byte 0xD4) |
| Entry word | `0xEA00002E` → stock crt0 at 0x080000C0 (not a cracktro) |
| MD5 | `36916861e921121015366b7d5ec45f3e` |
| SHA-1 | `d1d6806ac99a29dd3195491a213bec9023a3adb4` |
| SHA-256 | `59ed9dc1ff97f5a96d72d1dcffb14c84a2d68aee6155fccd88d497b962860064` |

## 2. Executive summary

**There is no typed cheat-code / password validator in this GBA image.** Every
published "cheat" for *this SKU* is a **progression-gated unlock**: completing
career (Pro + Sponsor tours) with a different skater N times unlocks a flag in
the EWRAM save record; the Options → CHEATS row then becomes selectable and
lists nine toggles. I searched the whole 8 MiB for every published console
password in seven encodings, searched every NUL-terminated uppercase/digit
string, searched packed-font-index encodings, searched for button-mask code
tables, and enumerated every reachable screen. All results are negative for a
code entry surface.

The console versions' `WEEATDIRT` / `YOHOMIES` / `backdoor` strings are **not
present in the GBA image in any encoding** (Guide §16.11 — a title match is
not an SKU match). 3rd party cheat indexes' GBA cheat page only lists "complete the game N
times" unlocks; the `WEEATDIRT` snippet that search engines surface on that
page is a cross-platform contribution duplicated from the console pages.

The one candidate "code machine" lead (a 3rd party cheat index Q&A answer claiming you
must type `Backdoor` into a code machine in the options menu) was checked and
is a console-version claim: no such string or screen exists in the GBA build.

**Finding: bounded negative (no code system); the cheat surface is a 9-entry,
career-completion-gated toggle list.** Confidence: high for "no typed code",
high for the 9-entry list, medium for the exact completion thresholds (the two
published GBA lists disagree on Turbo/Giant/Moon; see §8).

## 3. How to reproduce

* mGBA 0.10.5 on Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
* Keymap verified against `KEYINPUT` at `0x04000130` via mGBA's `-d` pty
  debugger: GBA D-pad = arrow keys, A = `x`, B = `z`, Start = `Return`.
  Active-low masks confirmed by savestate diff (holding Down changed
  `0x04000130` from `0x03FF` to `0x037F`, i.e. bit 7 = Down).
* Menu path (all with ~0.1 s key holds; the title menu hides after ~5 s idle —
  use `Shift+F1`/`F1` savestates):
  * Title → skate-shop main menu: **Start**.
  * Main menu rows (5): TONY HAWK, CAREER, FOUNDRY, SKATE SHOP, OPTIONS;
    **Down** selects, **A** (`x`) confirms, **Start** begins the highlighted
    mode directly.
  * OPTIONS rows (9 displayed): SOUND, KID MODE, CONTROLS, QUICKSTART, BLOOD,
    BRIGHTNESS, CREDITS, ADVANCED OPTIONS, CHEATS. With a fresh save,
    **CHEATS is skipped by the selection ring** (7×Down → ADVANCED OPTIONS,
    8×Down → wraps to SOUND). Screenshots: `dc1.png`–`dc8.png`, `opts_dbg.png`.
  * ADVANCED OPTIONS → RESET CAREER / CHANGE LANGUAGE (`advanced.png`).
  * SOUND → MUSIC / SOUND FX / SONG ADVANCE (`cheats_screen.png`).
  * In-game pause → CONTINUE / RETRY / VIEW GOALS / VIEW TRICKS / SOUND /
    END RUN (`s4.png`).
* Debugger: `mgba -d -3 ROM` under a pty. Commands must be terminated with
  **CR (`\r`)**, not LF; `Ctrl+C` breaks into the prompt. GDB stub port cannot
  be overridden with `-C gdb.port=` in this build (another agent held 2345),
  so the pty debugger was used instead.
* Savestates are written next to the ROM as `...ss1`–`...ss9`; the `gbAs`
  PNG chunk decompresses to 397,312 bytes with EWRAM at raw offset `0x21000`.

## 4. Address map

| Address | Size | Meaning | Evidence |
|---|---:|---|---|
| `0x08000000` | 4 | Entry branch `0xEA00002E` | Derived (header bytes) |
| `0x0815EB78` | 8 | UI string `Cheats` | Derived (ASCII + pointer at `0x08161390`) |
| `0x0815F6FC`–`0x0815F774` | 10 strings | Cheat names + `- locked -` (see §6) | Derived |
| `0x081617A8`–`0x081617CC` | 10 × 4 | Pointer table to those strings | Derived (literal-pointer scan) |
| `0x08169714` | 10 | Text-entry alphabet `0123456789` | Derived |
| `0x08169720` | 10 | `ABCDEFGHIJ` | Derived |
| `0x0816972C` | 10 | `KLMNOPQRST` | Derived |
| `0x08169738` | 10 | `UVWXYZ-___` | Derived |
| `0x08169690`–`0x081696F0` | 4 × 32 | Spaced display form of the same alphabet | Derived |
| `0x08161330` | 4 | String-table base copied to `0x02006550` by `0x08014880` | Derived (disassembly) |
| `0x02000068` | 1 | Menu cursor candidate (4→5 on one Down in Options) | Observed (savestate diff) |
| `0x02007691` | 1 | Wolverine unlock flag; **0** in fresh save | Observed (debugger `r/1`) |
| `0x020076F1` | 1 | Shaun Palmer unlock flag; **0** | Observed |
| `0x02007751` | 1 | Mindy unlock flag; **0** | Observed |
| `0x0200778D` | 1 | Trial Mode unlock flag; **0** | Observed |
| `0x02006550/54/58` | 4 each | String-table pointers installed at boot | Derived |
| `0x04000130` | 2 | KEYINPUT (active low); `0x03FF` idle, `0x037F` with Down held | Observed |

## 5. Algorithm

There is no validator to reimplement. The cheat system is a **bit/byte flag
model** in the EEPROM-backed EWRAM save record:

```
career_completions (counter in save record)
    -> per-reward flag byte = 1        (e.g. 0x02007691 Wolverine,
                                        0x020076F1 Shaun Palmer,
                                        0x02007751 Mindy,
                                        0x0200778D Trial Mode)
    -> Options/CHEATS selection ring includes the row
    -> CHEATS screen renders names from pointer table 0x081617A8,
       selecting index i draws string at table[i] (0..8) or "- locked -" (9)
    -> toggling writes/clears a gameplay bit consumed by the skate engine.
```

The unlock flags are byte-sized and live in 0x60-byte skater/record slots;
the CodeBreaker equivalents (`32007691 0001`, `320076F1 0001`,
`32007751 0001`, `3200778D 0001`) corroborate the addresses, but those device
codes are out of scope and were used only as address hints.

The text-entry alphabet (`0-9 A-Z - ( ) _`, 40 symbols) is the Create-a-Skater
name editor. Its consumer is the name field, **not** a comparison routine: a
scan of the ROM found no `strcmp`/`memcmp` constant pool containing any
code-like string (Guide §16.2b).

## 6. Tables

### 6.1 Cheat names (pointer table `0x081617A8`)

| Index | ROM pointer | String | Published GBA unlock |
|---:|---|---|---|
| 0 | `0x0815F6FC` | `stud mode` | 10th career completion |
| 1 | `0x0815F708` | `rail balance` | 11th |
| 2 | `0x0815F718` | `always special` | 12th |
| 3 | `0x0815F728` | `manual balance` | 13th |
| 4 | `0x0815F738` | `moon physics` | 18th (see §8) |
| 5 | `0x0815F748` | `giant mode` | 17th (see §8) |
| 6 | `0x0815F754` | `slow-mo` | 15th/16th (sources differ) |
| 7 | `0x0815F75C` | `tiny mode` | 14th |
| 8 | `0x0815F768` | `turbo mode` | all gaps, or 16th (sources differ) |
| 9 | `0x0815F774` | `- locked -` | locked placeholder |

### 6.2 Published GBA unlock ladder (3rd party cheat index FAQ 17761 / 3rd party cheat indexes)

Completions 1–9 unlock Wolverine, The Zone, Trial Mode, The Zone-Speed,
Shaun Palmer, The Zone-Rail, Mindy, The Zone-Geo, The Zone-Fan (characters and
levels, not cheats). 10–17 unlock the cheats above. "Turbo mode" is attributed
to collecting all gaps in the 3rd party cheat index FAQ, but to the 16th completion by
3rd party cheat indexes; the ROM contains no string that resolves the conflict.

### 6.3 Alphabets found (all at `0x08169690`–`0x08169741`)

* Display (spaced): `0 1 2 3 4 5 6 7 8 9`, `A B C D E F G H I J`,
  `K L M N O P Q R S T`, `U V W X Y Z - ( ) _`.
* Compact: `0123456789`, `ABCDEFGHIJ`, `KLMNOPQRST`, `UVWXYZ-___`.
* This is a 40-symbol name-entry alphabet, **not** a password alphabet — there
  is no checksum, no fixed-length validator and no selector nibble anywhere in
  the code that reads it.

## 6b. Enumeration

**Space definition.** The cheat surface has *no code space*. The complete
developer-intended cheat set is the 9 entries of §6.1 (plus the `- locked -`
placeholder). Each is a boolean toggle in a save flag; the representable
state space is 2^9 = 512 toggle combinations, gated behind a career-completion
counter. There is no alphabet-driven code, no checksum width, and no reserved
bit in a code word. The name-entry alphabet is 40 symbols and variable length,
but is consumed only as a skater name.

**Novel code.** Not applicable — there is no code to mint. Per the Guide's
"bounded negative" branch (§0.2 item 5), the negative is instead proven by
counts:

| Search | Space checked | Hits |
|---|---|---:|
| Published console codes (PC/PS2/Xbox/GC): `WEEATDIRT`, `YOHOMIES`, `TEAMFREAK`, `JUICE4ME`, `NEVERBOARD`, `ROLLIT`, `STIFFCOMP`, `MAGICMISSILE`, `POPCORN`, `IDKFA`, `backdoor` — each in ASCII, lowercase, uppercase, UTF-16LE/BE/32LE, ±0x20 | 11 × 7 = 77 whole-ROM scans of 8,388,608 bytes | **0** |
| Same six longest codes packed as alphabet indices (offsets 0, 1, 0x20, 0x80) | 6 × 4 = 24 scans | **0** |
| NUL-terminated `[A-Z0-9]{4,16}` strings containing a vowel | 200 candidates | 0 code-like (all trick names, credits, or compressed-data noise) |
| Runs of ≥4 consecutive `u16` single-button masks (active-high or active-low) | 897 runs | 0 with a terminator/progress-index structure; all repeated-value data |
| 32-bit literal pointers into the UI string table `0x08161300`–`0x08161800` | 8 pointers | all are ordinary string-table accessors |
| Reachable screens walked | 6 main-menu, 9 options rows (8 selectable), 2 advanced, 3 sound, 6 pause, 1 name-entry | no code-entry field on any |

**Rejection / gate bounds (observed).** On a fresh save all four checked
unlock flags read `0x00` (`0x02007691`, `0x020076F1`, `0x02007751`,
`0x0200778D`), and the Options selection ring skips the CHEATS row:
`7×Down → ADVANCED OPTIONS`, `8×Down → SOUND` (wrap). That is the in-game
rejection of the locked feature — the gate is real, not a missing screen.
Entering any of the console passwords at the name field is likewise rejected:
no comparison constant exists for them, so they are treated as an ordinary
custom-skater name.

**Unverified (bounded) negative.** The CHEATS *screen itself* was not entered:
its gate requires N career completions and no completion was performed. The
claim "the 9 cheat names are the entire cheat set" rests on (a) the table at
`0x081617A8` having exactly 10 slots, (b) the absence of any other code/flag
surface in the searches above, and (c) the published GBA lists containing only
these nine cheats. If a future analyst obtains a 100%-complete save, the
CHEATS screen should be walked and each of the 9 toggles verified there.

## 7. Validation evidence

* **Observed** — emulator screenshots of every screen listed in §3; `KEYINPUT`
  mask behavior; debugger reads of the four zero unlock flags; savestate diffs.
* **Derived** — string/pointer table addresses; absence of code-like constants
  in the enumerated searches; the stock crt0 entry word; the alphabet strings.
* **Inferred** — that the completion counter gates the CHEATS row (the row is
  skipped on a fresh save and the nine published rewards are completion-based);
  the exact completion thresholds: published sources conflict and no ROM
  constant was isolated for the counter.

## 8. Unknowns

1. Exact address and width of the career-completion counter that gates CHEATS.
   The unlock flags themselves are known, but the writer of those flags was
   not isolated (no literal pointer to `0x02007691` etc. in ROM; addresses are
   computed from a skater-record base).
2. The CHEATS screen on an unlocked save was never displayed; the 9 rows are
   inferred from the pointer table and published lists, not observed in-game.
3. Turbo / Giant / Moon completion thresholds conflict between 3rd party cheat indexes
   (16/17/18) and 3rd party cheat index FAQ 17761 (Turbo from all gaps, list ends at 17).
4. Ghidra auto-analysis of the 8 MiB raw image OOM'd at 2 GB heap, so no
   decompilation of the menu handler was obtained; conclusions use objdump,
   Capstone-style literal scans, and the mGBA pty debugger.

## 9. Tooling

* `strings -t x -n 4`, `grep -abo`, `xxd`, `objdump`/`arm-none-eabi-objdump
  -M force-thumb`, Python `struct` literal/pointer scanners, PDftotext +
  Tesseract on the GBA manual (image-only PDF; confirmed no cheat/code
  documentation).
* mGBA 0.10.5: `-3`, savestates (`Shift+F1`..`F5`), `-d` pty debugger (CR
  command terminator), `-g` GDB stub (port override nonfunctional).
* `scrot` screenshots, ImageMagick crops, Python zlib `gbAs` savestate decoder.
* Web recon: 3rd party cheat indexes GBA FAQ 17761, 3rd party cheat indexes GBA page, 3rd party cheat indexes GBA cheats,
  3rd party cheat indexes Q&A; all fetched content treated as data (Guide §16.8).
* Work files: `/tmp/thps3/` (screenshots, `menu_state.bin`, scripts
  `lit.py`, `dbg3.py`, `stateio.py`, `key2.py`).

No ROM or copyrighted assets are redistributed; only addresses, hashes and
findings are published.
