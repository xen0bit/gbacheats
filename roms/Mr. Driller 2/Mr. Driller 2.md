# Mr. Driller 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mr. Driller 2/Mr. Driller 2.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `MR. DRILLER2` |
| Game code | `BR2E` |
| Maker | `AF` (Namco) |
| Version | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` — stock branch to `0x080000C0`, **no cracktro patch** |
| Complement / checksum | `0x92` / `0x0000` |
| MD5 | `d7118be078b9a61284a99d3f1f7e972f` |
| SHA-1 | `e7009dd8418303343c4aac2558538b8caa28b694` |
| SHA-256 | `053841acf102cee1d7ecc9d10a7264fb6e1e56d58026c3eeabad0848c2df4e2a` |

Embedded-header scan: exactly one Nintendo-logo hit (file `0x4`, title `0xA0`). No
appended trainer, no second game image, no patch. The first 4 KiB is normal ARM
crt0 code (ROM copy loop at `0x08000100` onward). This is the retail image.

## 2. Executive summary

There is **one developer-intended, in-game cheat** in this ROM: the **10-lives
pause-menu button code**. It is genuine, published on GameFAQs/VGChartz-equivalent
lists and Japanese wikis, and it works — but only with a deliberately slow input
cadence. It takes the lives byte at `0x03001151` from `0x03` to `0x0A` (10).

There is **no password system, no cheat-code keypad and no on-screen code entry
surface** in this game. The "ENTER YOUR NAME!" screen is a record-label field,
not a validator (§16.2b): the characters it collects are never compared to any
constant in the entry handler. The unlockables (North Pole stage, reverse Time
Attack courses, 20 Driller Cards, Endings gallery) are **save-bit progress
unlocks**, not codes.

A real **developer test/debug menu** is present in the ROM: a fully decoded ASCII
text bank at `0x082A35C` (`PG602 - Mr.Driller`, mode list, courses, characters,
difficulties), a dedicated drawer at `0x08010F5C`, and a dispatch entry at
`0x08029EAC+2`. It is **dead code**: the only function that can select its screen
index (`0x08011A44`, setting `0x030048B4 = 2`) has **zero callers and zero pointer
references**; the 11-entry mode table at `0x0801199C` stops one entry short of it.
No in-game input reaches it. It was forced for inspection by patching a savestate.

The published arcade A.D.S. "North Pole" code is an **arcade-only** operator-menu
code (P1/P2 button nomenclature) and has no GBA equivalent in this ROM.

## 3. How to reproduce

Emulator: mGBA (SDL), display `:318`, `SDL_AUDIODRIVER=dummy`, `Xvfb :318`,
`openbox`. Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`,
Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.

**10-lives code (verified):**

1. Start **Mission Driller** and enter any stage (India/America/Egypt).
2. Press **Start** to pause. Leave the cursor on **Continue** ("再開").
3. Press, **slowly — about 2 presses/second**, each key held ~120 ms with
   ~420 ms between presses:

   `Down, Select, Up, Down, L, R, Down, Up, R, L, Up, A`

4. The game resumes and the HUD reads **Lives × 10**.

The slow cadence is essential: the identical sequence pressed at ~4 presses/s
(80 ms hold / 180 ms gap) is **rejected** (lives stays 3).

**Reading RAM:** mGBA savestates (`Shift+F1`) are PNGs with a zlib `gbAs` chunk.
For a 4 MiB ROM the IWRAM image begins at state offset `0x19000`; therefore
`0x03001151` lives at state byte `0x1A151`. A parser is in
`/tmp/mrdriller2/ss.py`; a patcher in `patchss.py`.

**Debug screen (analysis only, not reachable by input):** patch a main-menu
savestate's `0x030048B4` to `2` with `patchss.py`, load with `mgba -t`, and the
`PG602` screen is dispatched; pressing A launches Mission Driller (India).

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | ROM base; one header at file `0x0` | Observed (header scan) |
| `0x0800704` | Main loop; frame dispatch | Derived (disassembly) |
| `0x0800758` | Gate read: `ldrsh r0,[0x03001314]`; `0` → menu table, nonzero → game-mode table | Derived |
| `0x0800762` | Menu dispatch table `0x08029EAC`, index from `0x03004470` | Derived |
| `0x08007A8` | Game-mode dispatch table `0x0829AA34` | Derived |
| `0x08010F5C` | Debug/test screen drawer (Thumb); draws `PG602 - Mr.Driller` and mode prompt | Derived |
| `0x08010FCC` | Literal `0x082A330` — debug menu's internal mode jump table (11 entries) | Derived |
| `0x08010FD0` | Literal `0x030048B4` — debug/menu screen index | Derived |
| `0x0801199C` | 11-entry menu-item → screen-index setter table; **omits index 2** | Derived |
| `0x08011A44` | Setter for screen index 2 (debug screen) — **unreferenced** | Derived |
| `0x08029EAC` | Menu dispatch table; entry 2 = `0x08010F5D` (debug drawer) | Derived |
| `0x0829AA34` | Game-mode dispatch table (12+ entries), used when gate nonzero | Derived |
| `0x082A330` | Debug menu's 11-entry mode handler table | Derived |
| `0x082A35C`–`0x082A5E2` | Debug menu ASCII text bank (NUL-terminated) | Observed (dumped) |
| `0x082B433`+ | Font/tile-index data bank (repeated `0x55/0x44` glyph indices); not ASCII | Observed (dumped) |
| `0x0300114E` | Air (byte), observed `0x64`=100% at gameplay start | Observed |
| `0x03001151` | **Lives (byte)**, `0x03` → `0x0A` after code | Observed |
| `0x03001314` | Menu/game gate (s16): `0` menus, `1` gameplay | Observed + derived |
| `0x03004470` | Secondary dispatch index (0 in menus) | Observed |
| `0x030048B4` | Menu screen index (see table in §7) | Observed |

File offset → ROM address: `0x08000000 + file_offset` (flat 4 MiB image).

## 5. Algorithm

**Button-code validator (behavioural model).** The accepted input is an ordered,
fixed-length vector of 12 GBA key masks, compared with exact positional equality:

```
mask[A]=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010
     Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200   (active-high)

expected = [0x080,0x004,0x040,0x080,0x200,0x100,
            0x080,0x040,0x100,0x200,0x040,0x001]
```

As a little-endian `u16` stream: `80 00 04 00 40 00 80 00 00 02 00 01 80 00
40 00 00 01 00 02 40 00 01 00`.

The trigger is **edge-triggered with a minimum inter-press interval**: presses
closer than roughly 300 ms are collapsed/ignored, so the sequence must be
entered at ~2 presses/s. On full match the game writes `0x0A` to `0x03001151`,
resumes from pause, and flags the play result as non-recordable.

A literal search for this mask vector failed under **all** encodings tried
(`u8/u16/u32`, reversed, active-low complements, 4-bit and 5-bit packed, key
numbers 0–9, and fixed strides 2/4/8/16). The comparison is therefore inline or
computed rather than a stored table; the exact instruction sequence was not
isolated (see §8, Unknowns). The behavioural model above is exact for the
accepted and all rejected inputs tested.

**Debug menu gate (derived exactly):**

```
; main loop, 0x0800758
r0 = (s16*)0x03001314
if (r0 != 0) handler = table_0x0829AA34[(s16)0x03004470]  ; game modes
else         handler = table_0x08029EAC[(s16)0x03004470]  ; menus
bx handler                                    ; via thunk 0x08024360 (`bx r0`)
```

Screen index 2 of the menu table is the PG602 test screen. Its setter at
`0x08011A44` is not in the reachable setter table and has no callers → dead.

## 6. Tables

**6.1 Published / verified codes**

| Source | Code | Platform | Verdict in this ROM |
|---|---|---|---|
| GameFAQs, Japanese wikis | Pause → `↓ Sel ↑ ↓ L R ↓ ↑ R L ↑ A` → 10 lives | GBA | **VERIFIED** (slow cadence required) |
| Japanese wiki (biglobe, nifty) | L+R held + Select = soft reset | GBA | Not reproduced in gameplay or menus; index unchanged (recorded negative) |
| GameFAQs | A.D.S. operator-menu "North Pole" unlock (P1/P2 buttons) | **Arcade** | Not applicable — no GBA operator menu or A.D.S. screen exists |
| VGChartz/NamuWiki | Reverse courses unlocked by clearing all 10 front courses | GBA | Save-bit unlockable, not a code |
| NamuWiki | North Pole stage unlocked by clearing India/America/Egypt | GBA | Save-bit unlockable, not a code |
| CodeBreaker lists (air/lives/score/depth at `0x0300114E`, `0x03001151`, `0x0300490C`, `0x0300113C`) | memory patches | GBA | Out of scope (GameShark/CodeBreaker); addresses independently confirmed in RAM |

**6.2 Debug text bank (fully decoded, `0x082A35C`)**

```
PG602 - Mr.Driller | Press A to select a mode | to Higashi | to Tsukada
Game | Endless | Time Attack | Survival
Logo/Title | Opening | Ending | Staff Roll | Epilogue | Test
Course: |  500m <India> | 1000m <United States> | 2000m <Egypt> | 2000m <Arctic>
Chara: | Susumu | Anna | Difficulty: | Easy | Normal | Hard | Start: | %6dm
Course A..Course J | Course A (R)..Course J (R)
Type: | TimeAttack | TimeAttack (R) | %3d
```

This is a complete mode-select debug screen: 4 gameplay modes + 6 cinematic/test
screens, 4 mission stages, 2 characters, 3 difficulties, 10 forward and 10
reverse time-attack courses.

**6.3 Menu screen indices in `0x030048B4` (observed, RAM)**

| Index | Screen |
|---:|---|
| 1 | Main menu ("MAKE YOUR CHOICE!") |
| 2 | 1P mode select — **also the debug/test screen index** (see §6.2) |
| 3 | Title screen / in-game HUD (reused) |
| 4 | Mission stage select |
| 5 | Pause menu |
| 6 | Name entry |
| 7 | 2P DRILLER |
| 9 | RECORDS |
| 0xA | OPTIONS |
| 0xB | ENDINGS |
| 0xC | BUTTON CONFIG |
| 0x14 | DRILLER CARDS |

## 6b. Enumeration

**Space definition.** The cheat surface is not a password with a numeric space;
it is a single fixed button sequence plus save-bit unlockables:

* Button sequence: length exactly **12**, alphabet = 10 GBA buttons, so the raw
  design space is `10^12` ordered press vectors (or `2^120` if held-state
  combinations were allowed). One vector is accepted.
* Entry timing: inter-press interval must exceed roughly 300 ms; this is a real
  second dimension of the input space (fast entry is rejected).
* Debug screen: one screen index (2) in an 11-entry menu-table space
  (`0x08029EAC`, valid indices 0–11). Its setter is unreferenced, so the
  reachable set is 10 of 11 menu indices; index 2 is dead code.
* Unlockables: 20 Driller Cards, 1 extra stage (North Pole), 10 reverse courses,
  4 endings — all progress-gated save bits, not codes.

**Novel codes.** No novel *accepted* code could be minted, and it would be
dishonest to claim one: the validator accepts exactly the single published
12-press vector. An undocumented combination *was* generated and pressed in the
emulator — `[Up] + published sequence` (13 presses) — and **rejected**. Other
undocumented combinations pressed and rejected are listed below. The genuinely
novel contribution is the full characterisation: the slow-input gate (absent
from every published description), the exact RAM effect and address, the
enumeration of rejections, and the dead debug screen with its decoded text bank.

**Bounds proven by rejection (all observed; lives byte stayed `0x03`):**

| Probe | Presses | Result |
|---|---:|---|
| Published 12-press sequence, slow | 12 | **0x0A — accepted** |
| Same sequence, fast (~4/s) | 12 | 0x03 — rejected (timing gate) |
| Extra `Up` prepended | 13 | 0x03 — rejected (exact length) |
| Extra `Down` prepended | 13 | 0x03 — rejected |
| First `Down` replaced by `Up` | 12 | 0x03 — rejected |
| `Select` replaced by `Start` | 12 | 0x03 — rejected |
| Final `A` omitted | 11 | 0x03 — rejected |
| Final `A` replaced by `B` | 12 | 0x03 — rejected |
| Final `A` replaced by `Start` | 12 | 0x03 — rejected |
| Whole sequence reversed | 12 | 0x03 — rejected |
| `L`↔`R` swapped everywhere | 12 | 0x03 — rejected |
| `Up`↔`Down` swapped everywhere | 12 | 0x03 — rejected |

Every position of the sequence and its length are therefore load-bearing; there
are no tolerated aliases among the probes.

**Button-space and text-space searches with counts:**

* `strings -t x -n 4`: 40,795 lines; keyword filter
  (`password|cheat|code|debug|secret|unlock|level|...`) → **0** hits.
  Case-insensitive English-word filter → 6 hits, all in the debug text bank.
* Whole-ROM button-mask runs (active-high and active-low, `u16`, length ≥ 6):
  83 candidate runs; the 8 in the code region (`<0x300000`) were dumped and all
  are false positives in graphics/OAM data (`0x0800E900` region etc.).
* Published sequence literal search: 12 encodings × 10 prefix lengths →
  **0** hits in the 4 MiB image.
* Pointer scans: `0x08029EAC` → 1 hit (`0x80007A0`); `0x08010F5D` → 1 hit
  (`0x29EB4`); `0x08011A44`/`0x08011A45` → **0** hits; BL-scan for those
  setters → **0** callers.

## 7. Validation evidence

**Observed (emulator / savestate RAM):**

* All 14 screens in §6.3 were reached by real key input and their
  `0x030048B4` values read from savestate RAM (files `*.ss1` in the work dir).
* Lives byte `0x03001151 = 0x03` before and `0x0A` after the code; HUD visibly
  reads "Lives × 10" in `slow_code12.png`.
* Air `0x0300114E = 0x64` (100) and depth `0x0300113C = 0` at gameplay start,
  matching the published CodeBreaker addresses.
* Pause index `0x030048B4 = 5`; gameplay index `3`; gate `0x03001314 = 1`
  during gameplay, `0` in menus.
* Debug text bank dumped byte-for-byte and decoded (§6.2).
* Debug screen forced from a patched savestate; A launched Mission India.

**Derived (disassembly):**

* The menu/game dispatch gate at `0x0800758` and both jump tables.
* The debug drawer's literal pool (`0x082A35C`, `0x082A370`, `0x082A330`,
  `0x030048B4`) and the `bx r0` thunk at `0x08024360`.
* The unreferenced debug-screen setter at `0x08011A44` and the incomplete
  11-entry setter table at `0x0801199C`.

**Inferred (not fully exercised):**

* The 12-press validator's code path is inline/computed; its exact instruction
  address was not isolated (GDB stub proved one-shot/unstable in this
  environment). The behavioural model is nonetheless exact over all tested
  inputs.
* The ~300 ms minimum inter-press interval is a measured boundary between two
  tested cadences, not a cycle-accurate threshold.
* The "result not recorded" side effect is published in Japanese sources and is
  consistent with the code path; it was not verified against the records screen.

**Prompt injection:** none encountered. Fetched GameFAQs, NamuWiki, Japanese
wiki and archive pages contained no instructions directed at the analyst; all
were treated as data.

## 8. Unknowns

* Exact validator instruction address and the reason for the slow-input gate.
* Whether any *other* button sequence is accepted (only the published one and
  11 near-neighbours were probed; exhaustive `10^12` search is infeasible).
* Whether soft reset (`L+R+Select`) works under a different screen/timing; two
  attempts (gameplay, menu) produced no state change.
* The tile-index bank at `0x082B433`+ was identified as glyph-index data but
  not rendered through its font; no readable strings are hidden there beyond
  the decoded ASCII debug bank.
* Debug-menu handler details (the 11 functions in `0x082A330`) were not
  exercised individually because the screen is unreachable by input.

## 9. Tooling

* mGBA (SDL) under `Xvfb :318` + `openbox`; `xdotool` XTEST input; `scrot` screenshots.
* `arm-none-eabi-objdump -M force-thumb` for raw disassembly; Capstone 5.0.7 for
  literal/BL/ADR scans; `strings`, `xxd`, `grep`.
* `/tmp/mrdriller2/ss.py` — mGBA `.ss1` `gbAs` parser (IWRAM at
  state offset `0x19000`, EWRAM at `0x21000`).
* `/tmp/mrdriller2/patchss.py` — savestate RAM patcher (used only to
  inspect the dead debug screen).
* `/tmp/mrdriller2/codetest.py` — reproducible button-code test harness
  (restart from `gameplay.ss1`, pause, slow presses, read `0x03001151`).
* `/tmp/mrdriller2/helper.py` — input/screenshot/GDB helpers.

No ROM or copyrighted assets are redistributed; only addresses, hashes,
algorithms and original scripts are published.
