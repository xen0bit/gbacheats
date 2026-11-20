# Top Gun: Firestorm Advance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Top Gun Firestorm Advance.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `TOPGUN FSTA` |
| Game code / maker | `ATGE` / `60` (version `0x00`) |
| Entry word | `0xEA00002E` (stock crt0 branch — not a patched scene image) |
| Header complement / checksum | `0x9F` / `0x0000` (zero checksum is the usual rebuilt-header artifact, §16.1) |
| Nintendo-logo scan | exactly **one** header, at file `0x0` — single-game image, not a multiboot/double-pack |
| MD5 | `248d9fa9903d27cd9890e6a08dbd97cf` |
| SHA-1 | `68ccb866bcb82a1c884ef40d74540e63ce0d5bd1` |
| SHA-256 | `1151b7b986881300b9c7db484a295833f7c12a6561b50f79fa1bce988bad9335` |

`file(1)` identifies it as `"TOPGUN FSTA" (ATGE60, Rev.00)`. All addresses below are for this exact hash.

## 2. Executive summary

The game has a **developer-intended password system**, reached from the main menu
**PASSWORD** entry. A password is four picture-symbols chosen from a **9-symbol
alphabet** (values `0..8`); the player selects a slot with Left/Right and changes
its symbol with Up/Down, then presses A.

The validator at ROM **`0x0800B352`** is a pure lookup, **not a checksum**: it
compares the four `u32` input words at IWRAM `0x03000B00..0x03000B0C` against a
ROM table of **36 records** at `0x0803819C` (24 bytes each). A full match writes
a *group* to `0x03002BC0` and a *level* to `0x03000AF0` and starts the mission;
any mismatch draws four green **X** marks.

The table is **3 groups × 12 levels = 36 valid codes** out of `9^4 = 6561`
representable inputs. Public lists (GameFAQs, Cheat Happens, ChapterCheats)
publish only the 11 group-0 codes for levels 2–12, and **one of those 11 is
mis-transcribed** (level 6). Twenty-five accepted codes are absent from every
published list.

A novel code from an unpublished group — `[2,4,0,3]` (group 1, level 1) — was
generated from the table, typed on the real PASSWORD screen, accepted by the
game (distinct Top Gun school-history briefing), and confirmed in RAM
(`group=1`, `level=1`, input buffer `[2,4,0,3]`). A second novel code
`[4,0,4,0]` (group 2, level 12) was also accepted with `group=2`, `level=12`.
Bounds were proven three ways: exhaustive enumeration (36/6561), rejection of
an unlisted in-alphabet code (`[1,3,1,2]` → X marks), and rejection of an
out-of-range value `9` written directly into the input buffer (→ X marks).

No title-screen button code, hidden debug menu, or unlockable cheat surface was
found; the one web lead for a button sequence produced **0 hits** in six
encodings (see §8).

## 3. How to reproduce

**Emulator / display.** mGBA 0.10.5 at `/usr/local/bin/mgba`, Xvfb `:317`,
`SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`. SDL keymap used: A=`x`, B=`z`,
L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Holds of
90–150 ms with ~300 ms between presses.

**Menu path.** Language screen → A (ENGLISH) → title → Start → main menu →
Down once (the cursor clamps at the ends; the menu has six entries:
START / PASSWORD / MULTIPLAYER / DIFFICULTY / MUSIC / CREDITS) → A to enter
PASSWORD.

**Code entry (from a freshly entered PASSWORD screen, all four values `0`).**
For each slot `i = 0..3`: if `i > 0` press **Right** once to move the cursor;
press **Down** `v[i]` times (Down increments the value `0→1→…→8→0`; Up
decrements `0→8→7→…`); then press **A** to submit.

Reproduced inputs and results:

| Input | Result |
|---|---|
| `1,3,1,1` (published L2) | ACCEPTED — "COMMENCE / BRIEFING / TUTORIAL / QUIT" |
| `8,6,4,2` (corrected L6) | ACCEPTED |
| `8,2,4,2` (published L6 *as printed*) | REJECTED (X marks) |
| `1,3,1,2` (unlisted, in alphabet) | REJECTED (X marks) |
| `2,4,0,3` (**novel**, group 1 / level 1) | ACCEPTED — Top Gun school-history briefing; RAM: group=1, level=1 |
| `4,0,4,0` (**novel**, group 2 / level 12) | ACCEPTED; RAM: group=2, level=12 |
| `9,3,1,1` (out-of-range, written via debugger) | REJECTED (X marks) |

Screenshots of every case are in `/tmp/opencode/topgun/` (`pub_l2_beforeA.png`,
`pub_l2_afterA.png`, `novel_g1l1_beforeA.png`, `novel_g1l1_afterA.png`,
`novel_g2l12_afterA.png`, `reject_test_afterA.png`, `pub_l6_typo_afterA.png`,
`pub_l6_fixed_afterA.png`, `oor_dbg_after.png`), together with `game.ssN`
savestates and the helper scripts listed in §9.

## 4. Address map

| Address (ROM unless noted) | Meaning | Evidence |
|---|---|---|
| `0x0800B150`–`0x0800B510` | PASSWORD screen handler / validator | Derived (Thumb disassembly) |
| `0x0800B2D8`–`0x0800B350` | input handling: Left/Right cursor, Up/Down symbol, A submit | Derived |
| `0x0800B316` | `KEY & 0x40` (Up): `v--`, if `v > 8` then `v = 8` | Derived |
| `0x0800B32E` | `KEY & 0x80` (Down): `v++`, if `v > 8` then `v = 0` | Derived |
| `0x0800B352`–`0x0800B39E` | validator: loop `i=0..35`, compare 4 words, write group/level | Derived |
| `0x0800B3C0` (literal) | `0x0803819C` — password table base | Derived |
| `0x0800B3C4` (literal) | `0x03000B00` — input buffer | Derived |
| `0x0800B3E8` / `0x0800B3EC` (literals) | `0x03002BC0` (group) / `0x03000AF0` (level) | Derived |
| `0x0803819C`–`0x080385A3` | 36 × 24-byte password records | Derived / Observed (entry matches published codes) |
| `0x03000B00`, `+4`, `+8`, `+0xC` | four input symbols, `u32` each, range 0–8 | Observed (savestate / debugger reads) |
| `0x03002BC0` | selected group (0,1,2) | Observed |
| `0x03000AF0` | selected level (1–12) | Observed |
| `0x04000130` | KEYINPUT (active-low) | Derived |

Record layout (24 bytes): `u32 symbol[4]; u32 group; u32 level;`.

## 5. Algorithm

```
; input words live at 0x03000B00 + 4*i  (i = 0..3), each 0..8
; r7 = 0x0803819C (table), r6 = 0x03000B00 (input), r9 = candidate index i
for i in 0 .. 35:
    matches = 0
    for j in 0 .. 3:
        if input[j] == table[i].symbol[j]:
            matches += 1
    if matches == 4:                       ; 0x0800B38C
        word_at(0x03002BC0) = table[i].group    ; 0x0800B3D6
        word_at(0x03000AF0) = table[i].level    ; 0x0800B3E4
        accepted = true; break
if no candidate matched:
    draw four X marks over the slot row       ; Observed
```

Input layer (derived from `0x0800B2D8`–`0x0800B350`):

```
if (KEY & 0x020) && slot > 0:  slot--; ptr -= 4      ; Left
if (KEY & 0x010) && slot < 3:  slot++; ptr += 4      ; Right
if (KEY & 0x040):  v = *ptr - 1; *ptr = (v > 8) ? 8 : v       ; Up
if (KEY & 0x080):  v = *ptr + 1; *ptr = (v > 8) ? 0 : v       ; Down
if (KEY & 0x001):  validate()                                ; A
```

The comparison is `ldr r1,[r6+4*j]` vs `ldr r0,[r7+24*i+4*j]`; there is no
checksum, no PRNG, and no arithmetic on the symbol values. The UI's `0..8`
clamp matches the fact that every stored symbol is `0..8`; a value of `9`
cannot match any record (proved by direct RAM write, §7).

## 6. Tables

### 6.1 Symbol alphabet (9 values)

The on-screen keyboard cycles visually in the reverse order of the stored
values because Up decrements and wraps. Stored values:

| Value | Symbol | Visual (Up-cycle position) |
|---:|---|---|
| 0 | Missile Man | 1st (soldier with shoulder launcher) |
| 1 | Jet | 9th (stylised jet / signal-like icon) |
| 2 | Top View Car | 7th |
| 3 | Missile | 6th |
| 4 | Boat | 5th |
| 5 | Tank | 4th |
| 6 | Side View Car | 3rd |
| 7 | Paratrooper (parachute) | 2nd |
| 8 | AA Gun | 8th |

Names are inferred by matching the ROM table against the published symbol
lists; visual identities are from the captured font/tile pictures
(`alpha_up.png`, `alpha_down.png`), decoded before the negative.

### 6.2 Complete accepted-code table (all 36)

`g` = group, `L` = level. "Published" marks the 11 group-0 codes that appear on
GameFAQs/Cheat Happens/ChapterCheats (the corrected ROM form is shown for L6).

| # | g | L | values | symbols | published |
|---:|---:|---:|---|---|:--:|
| 0 | 0 | 1 | 0482 | MissileMan, Boat, AAGun, TopViewCar | — |
| 1 | 1 | 4 | 0511 | MissileMan, Tank, Jet, Jet | — |
| 2 | 0 | 9 | 0815 | MissileMan, AAGun, Jet, Tank | yes |
| 3 | 1 | 7 | 1005 | Jet, MissileMan, MissileMan, Tank | — |
| 4 | 1 | 5 | 1065 | Jet, MissileMan, SideViewCar, Tank | — |
| 5 | 2 | 10 | 1202 | Jet, TopViewCar, MissileMan, TopViewCar | — |
| 6 | 0 | 2 | 1311 | Jet, Missile, Jet, Jet | yes |
| 7 | 2 | 11 | 1701 | Jet, Paratrooper, MissileMan, Jet | — |
| 8 | 1 | 9 | 1805 | Jet, AAGun, MissileMan, Tank | — |
| 9 | 1 | 6 | 2207 | TopViewCar, TopViewCar, MissileMan, Paratrooper | — |
| 10 | 2 | 4 | 2310 | TopViewCar, Missile, Jet, MissileMan | — |
| 11 | 2 | 1 | 2315 | TopViewCar, Missile, Jet, Tank | — |
| 12 | 1 | 1 | 2403 | TopViewCar, Boat, MissileMan, Missile | **novel (entered)** |
| 13 | 0 | 3 | 2653 | TopViewCar, SideViewCar, Tank, Missile | yes |
| 14 | 1 | 8 | 2808 | TopViewCar, AAGun, MissileMan, AAGun | — |
| 15 | 0 | 11 | 2884 | TopViewCar, AAGun, AAGun, Boat | yes |
| 16 | 0 | 10 | 3327 | Missile, Missile, TopViewCar, Paratrooper | yes |
| 17 | 0 | 12 | 3657 | Missile, SideViewCar, Tank, Paratrooper | yes |
| 18 | 1 | 2 | 3816 | Missile, AAGun, Jet, SideViewCar | — |
| 19 | 2 | 12 | 4040 | Boat, MissileMan, Boat, MissileMan | **novel (entered)** |
| 20 | 0 | 5 | 4210 | Boat, TopViewCar, Jet, MissileMan | yes |
| 21 | 0 | 4 | 4343 | Boat, Missile, Boat, Missile | yes |
| 22 | 2 | 5 | 4468 | Boat, Boat, SideViewCar, AAGun | — |
| 23 | 2 | 7 | 5362 | Tank, Missile, SideViewCar, TopViewCar | — |
| 24 | 2 | 8 | 5743 | Tank, Paratrooper, Boat, Missile | — |
| 25 | 1 | 3 | 6163 | SideViewCar, Jet, SideViewCar, Missile | — |
| 26 | 1 | 10 | 6502 | SideViewCar, Tank, MissileMan, TopViewCar | — |
| 27 | 0 | 7 | 6631 | SideViewCar, SideViewCar, Missile, Jet | yes |
| 28 | 1 | 12 | 6800 | SideViewCar, AAGun, MissileMan, MissileMan | — |
| 29 | 2 | 9 | 7327 | Paratrooper, Missile, TopViewCar, Paratrooper | — |
| 30 | 2 | 2 | 7642 | Paratrooper, SideViewCar, Boat, TopViewCar | — |
| 31 | 0 | 8 | 7878 | Paratrooper, AAGun, Paratrooper, AAGun | yes |
| 32 | 1 | 11 | 8080 | AAGun, MissileMan, AAGun, MissileMan | — |
| 33 | 2 | 6 | 8102 | AAGun, Jet, MissileMan, TopViewCar | — |
| 34 | 0 | 6 | 8642 | AAGun, SideViewCar, Boat, TopViewCar | yes (corrected) |
| 35 | 2 | 3 | 8765 | AAGun, Paratrooper, SideViewCar, Tank | — |

### 6.3 Published-list discrepancy

GameFAQs/Cheat Happens/ChapterCheats all print level 6 as
`AA Gun, Top View Car, Boat, Top View Car` = `[8,2,4,2]`. Entering that exact
code yields **X marks** (`pub_l6_typo_afterA.png`). The ROM record for
group 0 / level 6 is `[8,6,4,2]` = `AA Gun, Side View Car, Boat, Top View Car`,
which is accepted (`pub_l6_fixed_afterA.png`). This is a published-list
transcription error (§16.7), not a second code.

## 6b. Enumeration

**Space definition.**
- Alphabet size: 9 symbols (`0..8`), stored as four `u32` words.
- Length: exactly 4 symbols; no checksum, no reserved bits.
- Representable inputs: `9^4 = 6561`.
- Accepted inputs: **36** (one per table record: 3 groups × 12 levels).
- Acceptance rate: `36/6561 ≈ 0.55%`.

**Validator model.** Reproduced bit-for-bit in
`/tmp/opencode/topgun/enumerate.py`: it iterates all 6561 tuples and matches
them against the 36 dumped records; the script reports exactly 36 accepted
codes and the groups `{0,1,2}` × levels `{1..12}`. This is a bounded negative
for every other one of the 6561 inputs.

**Novel codes (absent from every published list), generated from the table and
confirmed on the real PASSWORD screen:**

1. `[2,4,0,3]` — group 1, level 1 (TopViewCar, Boat, MissileMan, Missile).
   Accepted; a distinct briefing screen (US Navy Top Gun school history) rather
   than the group-0 tutorial. RAM read after acceptance:
   `0x03002BC0 = 1`, `0x03000AF0 = 1`, input buffer `= [2,4,0,3]`.
2. `[4,0,4,0]` — group 2, level 12 (Boat, MissileMan, Boat, MissileMan).
   Accepted; RAM read: `0x03002BC0 = 2`, `0x03000AF0 = 12`,
   input buffer `= [4,0,4,0]`.

**Bounds proven by rejection:**
- `[1,3,1,2]` — in-alphabet but not a table record → four X marks.
- `[8,2,4,2]` — the published level-6 typo → four X marks.
- `[9,3,1,1]` — out-of-range symbol `9` injected into `0x03000B00` with the
  mGBA CLI debugger (`w/1`), pressed A → four X marks. The UI cannot produce
  this value because Up/Down clamp to `0..8` (`0x0800B326`, `0x0800B342`).

**Coverage of the table:** 11 of the 36 records are published (group 0,
levels 2–12, with the level-6 correction); **25 records are unpublished** and
were identified here for the first time.

## 7. Validation evidence

* **Observed** — emulator screenshots of every menu screen and of accept/reject
  outcomes; RAM reads from decompressed mGBA `gbAs` savestate chunks and from the
  mGBA `-d` debugger (input buffer and group/level globals); literal byte dump
  of the 36-record table; published-list fetch via web archive.
* **Derived** — Thumb disassembly of `0x0800B150`–`0x0800B510`, literal pool
  resolutions (`0x0803819C`, `0x03000B00`, `0x03002BC0`, `0x03000AF0`), and the
  exhaustive offline enumeration (36/6561).
* **Inferred** — that the `group` field is a difficulty/campaign selector: the
  main menu has a three-state DIFFICULTY option, and group 1 level 1 produced a
  different briefing from group 0 level 2. The precise effect of `group` on
  enemy stats was not measured.

No content found in the ROM or in fetched pages was treated as instructions;
the one archived cheat page that was readable contained only code lists.

## 8. Unknowns

* Exact semantics of the `group` field (difficulty vs. campaign) and its detailed
  gameplay effects were not measured; only the written global and the visibly
  different briefing were confirmed.
* A web page (GeoCities "Gameboy Advance Passwords and Codes") advertises a
  title-screen button sequence `L, Select, A, Select, R, A, L, Select` plus
  "Select + shoulder to change levels". That list is a generic compilation and
  the entry is **not attributed to this game**. A bounded search of this ROM for
  that sequence as `u16`/`u8` key masks, active-low and active-high, forward and
  reverse order, returned **0 hits** in all six encodings. The main-menu and
  title screens were walked in the emulator and no such handler was observed.
  Reported as a bounded negative, not as proof about other games on that page.
* Plain-text `strings` found only dialogue/menu text in five languages; symbol
  names exist as rendered pictures, not ASCII. They were decoded from the tile
  pictures before concluding there was no second text-based code surface.
* A patched savestate containing symbol `9` was rejected by mGBA's state
  integrity check; the out-of-range test was therefore performed with the
  debugger's `w/1` instead, which produced the same in-game rejection.

## 9. Tooling

All scripts and captures in `/tmp/opencode/topgun/` (analysis working copy of
the ROM; the original was never modified):

* `rsp.py`, `drive.py`, `repl.py` — attempted GDB-RSP drivers (abandoned: mGBA GDB
  stub on the shared default port 2345; `-C gdb.port=...` did not take effect in
  this build).
* `ssdiff.py` — mGBA `.ssN` PNG parser (`gbAs` zlib chunk → 397,312-byte state;
  IWRAM at `0x19000`, EWRAM at `0x21000`) and RAM diff.
* `keyprobe.py`, `greenprobe.py`, `cleanprobe.py`, `keytest.py`,
  `revealprobe.py`, `alphabet.py` — GUI input/symbol-classification probes;
  `alpha_up.png`, `alpha_down.png`, `keytest_m.png`, `reveal_m.png` are the
  decoded picture banks.
* `scan_codes.py`, `pattern_scan.py`, `pattern_scan2.py`, `pattern_scan3.py` —
  literal and equality-pattern table searches (ruled out a literal 4-byte code
  table before the real 24-byte-record table was found via the literal-pointer
  scan).
* `patch_ss.py` — savestate byte patcher (CRC corrected; state ultimately
  rejected by mGBA integrity check).
* `dbg.py`, `oor_debug.py` — mGBA `-d` pty debugger driver; used for the
  out-of-range RAM write and readback.
* `enter_code.py` — deterministic GUI password entry from a savestate.
* `enumerate.py` — offline validator model; full 6561-code enumeration and
  published-coverage counts.
* `dis_b1.txt`, `dis_b2.txt` — `arm-none-eabi-objdump -M force-thumb`
  disassembly of `0x0800B180`–`0x0800B700`.
* REA/Ghidra 12.1.4 session was opened on the raw image (`arm`, base
  `0x08000000`, SHA-256 as above) and closed cleanly; auto-analysis found only
  200 procedures, so the decisive evidence came from raw Thumb disassembly.

## 10. Legal note

No ROM image, extracted graphics, music, or game text is reproduced here. Only
hashes, addresses, algorithms, derived code tables, and original analysis
scripts/screenshots are published.
