# Dragon Ball Z: The Legacy of Goku II (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dragon Ball Z: The Legacy of Goku II.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `DBZLGCYGOKU2` |
| Game code / maker | `ALFE` / `70` |
| Version / complement / checksum | `00` / `0x5B` / `0x0000` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`, **not** a cracktro patch) |
| Embedded GBA headers | **one** — Nintendo-logo signature occurs only at file `0x4`; no trainer/second image |
| MD5 | `4e1565aa1f0627c2bf5e51019440cb70` |
| SHA-1 | `18e0715dec419f3501c301511530d2edcd590f8b` |
| SHA-256 | `6e6c370c339ec9171cb1956adf837a0d342a197f78964882ef46c3086656ff75` |

Clean US retail image (ALFE, Rev 0). All addresses below are for this exact hash.

## 2. Executive summary

**There is no in-game code system in this ROM.** No password entry, no button-code matcher,
no cheat menu reachable by controller input, and no text that asks the player to type a code.
The only hidden feature is a **developer debug screen** (Music Test / Sample Test / Map Test
with Zone/Area/Variation) that lives in the retail image but is **gated**: its state value is
`2`, and the title-screen input code can only produce `0`, `1`, or `3`. The published way to
reach it is an *external* CodeBreaker RAM write (`0202B32D:02`) plus Start at the title screen
(TCRF) — a memory-edit code, explicitly **out of scope** here. I verified the feature itself
by making a temporary 2-byte analysis patch on a `/tmp` copy that redirects the title
dispatcher to the debug constructor; pressing Start then opens the DEBUG screen, and pressing
A on Map Test teleports into the game with the six-character roster (Piccolo observed at
Lv 40, HP 1012/1012). That patch is an analysis aid, **not** a code and is not shipped.

Everything that *looks* like an unlockable (Hercule, five level-50 trophies, Cooler boss,
alternate ending) is ordinary story/progress save data, not a code — the same pattern as the
sibling *Buu's Fury*. The two button codes published on the combined GameFAQs "LoG I & II"
page belong to **The Legacy of Goku I** (the other game in that compilation); neither works
in this ROM, and the published key sequence does not exist as bytes in the image.

Relation to siblings: no suffix-matched button codes (unlike *GT: Transformation*), no fixed
minigame input (unlike *Buu's Fury*'s Perfect Fusion). Shared Webfoot-engine traits only:
C++ `K:\Source\...` strings, script-driven dialogue, progress-based unlockables, and a
developer debug screen left in the shipping build.

## 3. How to reproduce

* Emulator: `mgba -3` (SDL build), `Xvfb :316`, `SDL_AUDIODRIVER=dummy`.
* Keymap (verified on the title menu): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrow keys. Hold keys ≥100 ms; the first Start tap after boot is
  sometimes missed (intro still settling) — press again.
* Menu walk (unmodified ROM): boot → Atari/FUNimation logos → title logo → title menu
  (`START`, `OPTIONS`) → `OPTIONS` (`TEXT SPEED`, `SOUND FX VOLUME`, `MUSIC VOLUME`,
  `CREDITS`, `EXIT`) → `START` → `SELECT GAME` (3 slots: NEW GAME / NEW GAME / NEW GAME) →
  new game → story intro → overworld → Start = pause (`STATUS`, `ITEMS`, `OPTIONS`,
  `JOURNAL`; R cycles tabs).
* Debug screen (analysis-only reproduction, not a player code): copy the ROM to `/tmp`, patch
  file offset `0x582` (ROM `0x08000582`) from `00 f0 a9 fb` (`bl 0x0800CD8`) to
  `05 f0 95 f8` (`bl 0x080056B0`), boot the copy, press Start at the title screen.
  DEBUG appears. Down/Right move the cursor/values; A activates Music/Sample/Map Test.
* Codes tested:
  * LoG I "Options → highlight Text Speed → hold L+R+Up → A" → simply exits Options to the
    title; **no debug menu**.
  * LoG I "Up, Down, Left, Right, B, A" during intro → no confirmation sound, no observable
    flag/state change; literal mask sequence absent from ROM (see §6).
  * TCRF CodeBreaker `0202B32D:02` (applied continuously with mGBA's cheat file as an
    analysis probe) → title still routes to `SELECT GAME`, because the title code overwrites
    byte `+9` with the 0/1 selection in the same frame; this confirms the gate is an external
    RAM write, not an input path.

## 4. Address map

| ROM address | Meaning |
|---|---|
| `0x08000434` | Title-screen update/input: toggles byte `+8` ∈ {0,1}; on A/Start sets `[+5]=2`, `[+9]=[+8]`; after 1800 idle frames sets `[+9]=3` |
| `0x0800055E` | **Title state dispatcher**: `switch (obj[9])` {0:`0x0800CD8` Select Game, 1:`0x0800640` Options, 2:`0x080056B0` **Debug**, 3:`0x801ED3C` attract} |
| `0x08000582` | `bl 0x0800CD8` — the state-0 branch patched in the analysis copy |
| `0x08000598` | state-2 branch → `bl 0x080056B0` (debug constructor) |
| `0x080056B0` | Debug screen constructor (allocates `0x8C`-byte object) |
| `0x08005724` | Debug screen renderer — draws the six entries with per-line highlight |
| `0x08005804` | Debug screen init (VRAM setup, draws title "Debug") |
| `0x080058AE` | Debug input handler; 6-case jump table at `0x080058C8` → handlers `0x080058D2`, `0x08005936`, `0x08005984`, `0x08005A02`, `0x08005A4C`, `0x0800F3FE` |
| `0x08005A40` | Secondary map-field handler (ZONE/AREA/VARIATION bounds from table) |
| `0x08005ABC` / `0x08005ACC` | format strings `Music Test: %d` / `Sample Test: %d` |
| `0x08005AE0` / `0x08005AEC` / `0x08005AF8` / `0x08005B04` | `Map Test` / `Zone: %d` / `Area: %d` / `Variation: %d / %d` |
| `0x08005B30` | `Debug` (screen title, reached by Thumb `ADR` at `0x08005856`) |
| `0x08409368` | Map-location table: 56-byte records `{u8 zone, u8 area, u8 variation_count, ...}` |
| `0x0E2C5B`… | UI text bank (`Start`, `Options`, `Text Speed`, `Credits`, `Exit`, `Switch Characters`, six character names, item/quest names) |
| `0x083C9CA2`, `0x083D2C80`, `0x083D674C`, `0x083E2736`, `0x083EC6E2` | five copies of `Hercule is now an available character!` (script text bank, no direct pointer — referenced by text ID) |
| RAM `0x0202B32D` | Gate byte = title state object `+9`; TCRF's CodeBreaker address. Values observed/derivable: `0`,`1`,`3` from gameplay; `2` = debug screen |

Note: all seven debug strings are addressed with Thumb `ADR` (`add Rd, PC, #imm`), which is
why no 32-bit literal pointer to them exists in the ROM (a direct `struct.pack` pointer scan
returns zero hits).

## 5. Algorithm / pseudocode

```
// title screen, 0x08000434 + dispatcher 0x0800055E
sel = obj[8];                       // 0 = START, 1 = OPTIONS; toggled by Up/Down/Select
if (A_pressed || Start_pressed) {
    obj[5] = 2;
    obj[9] = sel;                   // ONLY 0 or 1
}
if (idle_frames > 1800) obj[9] = 3; // attract/demo

switch (obj[9]) {
    case 0: create_SelectGame(); break;   // 0x0800CD8
    case 1: create_Options();    break;   // 0x0800640
    case 2: create_Debug();      break;   // 0x080056B0  <-- unreachable from controller
    case 3: create_Attract();    break;   // 0x801ED3C
}

// debug screen, 0x080058AE
music  = obj[12];  if Right: music  = min(music+1, 43); if Left: music  = max(music-1, 0);
sample = obj[16];  if Right: sample = min(sample+1, 63); if Left: sample = max(sample-1, 0);
map    = obj[20];  // index into 0x08409368 (56-byte records)
// ZONE / AREA / VARIATION are bounded by the record bytes and the value shown as "n / count"
// A on a Music/Sample/Map entry plays the track/sample or teleports to the selected record
```
No checksum, alphabet, code length, or password validator exists anywhere in this path.

## 6. Tables

**Debug-menu entries (6, all enumerated by walking the screen and decoding the 6-case table):**

| # | Entry | Values / effect | Observed |
|---|---|---|---|
| 0 | `MUSIC TEST` | 0–43 (44 tracks); A plays, B stops | Right×50 stops at **43**; Left×50 returns to **0** |
| 1 | `SAMPLE TEST` | 0–63; A plays one sample | Right×70 stops at **63** |
| 2 | `MAP TEST` | select a location record; A teleports | default record teleported to a grass/desert scene with Trunks + Piccolo |
| 3 | `ZONE` (green sub-cursor) | table-driven; Right×5 changed 1 → **6** | A after change teleported to **CAPSULE CORPORATION** (different map) |
| 4 | `AREA` (green sub-cursor) | table-driven; Right×5 changed 1 → **6** | value display confirmed |
| 5 | `VARIATION` | displayed `0 / 1` for the default record; count from record byte 2 | confirmed |

TCRF additionally documents an unused track at index 27 and names all 44 tracks; this report
does not reproduce the copyrighted track list.

**Map table `0x08409368`:** records of 56 bytes; first three bytes are `{zone, area,
variation_count}`. Examples from the dump: rec0 `01 01 01` → `ZONE:1 AREA:1 VARIATION:0 / 1`;
rec7 `02 01 02`; rec110 `04 63 01`; rec141 `05 01 01`. At least 180 consecutive valid records
were dumped (zones 1–7+); the debug menu treats this as its level-select space.

**Character roster (UI bank `0x0E2DF4`…):** Gohan, Piccolo, Vegeta, Trunks, Goku, Hercule.
Debug teleport gave Piccolo at Lv 40, HP 1012/1012, EP 140/140, STR 51/100, POW 48/100,
END 60/100, EXP 2721115 — matching TCRF's "all six characters, upgraded to a certain degree".

**String-space counts (`strings -t x -n 4`, 114,271 lines):** `password` 0, `cheat` 0,
`gameshark` 0, `codebreaker` 0, `enter code` 0, `level select` 0, `sound test` 0,
`invincib`/`immortal` 0; `debug` 1 (the screen title), `Map Test` 1, `Music Test: %d` 1,
`Sample Test: %d` 1; `secret` 3 and `unlock` 1 are all ordinary dialogue lines
(e.g. `My secrets will not be unlocked so easily.` at `0x3E1005`). No code-like string table.

**Button-mask search:** the published LoG I sequence Up,Down,Left,Right,B,A was searched as
`u16` little-endian active-high (`40 00 80 00 20 00 10 00 02 00 01 00`), active-low, `u8`
active-high and active-low — **0 hits**. A broad u16/u8 key-mask-run scan returned only the
expected noise from animation/script data (23,832 u16 runs, 33,103 u8 runs), with no
controller-input table among the plausible candidates. No compare-and-set button matcher
exists on the title/menu path.

## 6b. Enumeration

* **Space definition:** there is no password/checksum space. The only enumerable system is the
  debug screen: 6 entries; Music Test 0–43 (44 values), Sample Test 0–63 (64 values), and a
  map-record space of ≥180 fifty-six-byte records `{zone, area, variation_count}`. No code
  validator, alphabet, field width, or checksum exists to mint a code from.
* **Novel values (not in any published list):** the exact field bounds `0..43` and `0..63`,
  the 56-byte `{zone,area,variation_count}` record layout at `0x08409368`, and the fact that
  debug state `2` is unreachable by controller input. A non-default map value
  (`ZONE: 6`, `AREA: 1`) was pressed in the emulator and produced the **CAPSULE CORPORATION**
  map — an undocumented combination confirmed dynamically (shot_41 → shot_42 in the working
  notes; screenshots are not attached to this reply).
* **Bounds proven by rejection:** Right held past the maximum does not advance past `43`
  (music) or `63` (sample); Left held past zero does not go below `0`. These are in-game
  rejections of out-of-range field values, observed on the DEBUG screen.
* **Negative result bounded:** every screen reachable by controller was walked (title,
  options, select-game, new-game intro/overworld, pause STATUS/ITEMS/OPTIONS/JOURNAL), the
  full text space was keyword-counted above, and the button-mask space was searched with
  counts above. The hidden debug screen's only gate is an external RAM write, so no in-game
  code can be generated, entered, or rejected — that is a proven statement about the input
  surface, not an omission.

## 7. Validation evidence

* **Observed (emulator, :316):** title/options/select-game/pause screens; L+R+Up+A in Options
  exits to title (no debug); debug screen with all six labels and default values; music bound
  43, sample bound 63; MAP TEST teleport to grass/desert with Piccolo Lv 40; pause STATUS shows
  Lv 40 / HP 1012; non-default ZONE 6 teleport to CAPSULE CORPORATION.
* **Derived (disassembly):** `0x0800055E` state switch and unreachable case 2;
  `0x08000434` writing only 0/1/3 to `+9`; `ADR` references to the seven debug strings;
  6-case jump table at `0x080058C8`; 56-byte map records at `0x08409368`.
* **Inferred (labelled):** that the five `Hercule is now an available character!` copies
  correspond to the five trophy/story events (text bank has no direct pointers, so the exact
  event IDs were not resolved). That the debug menu's remaining map records behave like the
  one tested — the table was dumped but not all ~180 records were individually teleported to.
* **Published sources checked:** TCRF (debug menu + CodeBreaker gate + track list) via
  web.archive.org; GameFAQs "LoG I & II" cheats (the two button codes belong to LoG I;
  LoG II entries are only glitches/unlockables); GameHacking/almarsguides/SuperCheats listings
  are GameShark/CodeBreaker memory edits and are out of scope. No prompt-injection content was
  encountered.

## 8. Unknowns

* Exact script text IDs / save-bit offsets that unlock Hercule and the five trophies were not
  resolved (no direct string pointers; text is referenced through the game's script bank).
* Not every one of the ~180 map-table records was teleported to individually; bounds and two
  distinct destinations were verified instead.
* Whether the 44-track music player's track 27 is truly unused was not re-verified in-game
  (reported by TCRF).
* The anti-piracy behavior noted by TCRF (check at first world-map transition) was not tested;
  it is not a cheat/code surface.

## 9. Tooling

* `strings -t x -n 4`, `xxd`, `grep`; Python 3 with `struct` for header parse, PC-relative
  `ADR` scan, BL/literal-pointer scans, key-mask literal and run scans, and map-table dump.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Capstone 5.0.7 (available; the `ADR` scan used an equivalent direct decoder).
* mGBA (SDL) under `Xvfb :316` + `openbox`, `xdotool` XTEST input helper, `scrot`/`import`
  screenshots. mGBA `-c` cheat file used once as an analysis probe; no shipped code.
* A 2-byte temporary ROM patch in `/tmp/opencode/logoku2/` was used solely to reach the
  gated debug screen for enumeration. It was not placed in the ROM folder and is not a code.
* Legal: no ROM bytes or copyrighted assets are reproduced here; only addresses, hashes,
  algorithms, and original observations are published.
