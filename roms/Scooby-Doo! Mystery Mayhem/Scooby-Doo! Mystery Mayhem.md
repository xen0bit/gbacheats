# Scooby-Doo! Mystery Mayhem (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Scooby-Doo! Mystery Mayhem.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `SCOOBYMAYHEM` |
| Game code / maker | `BMME` / `78` (THQ) |
| Version | `0x00` (Rev 00) |
| Entry word | `0xEA00002E` (stock `b 0xBC`) |
| Fixed byte / complement / header checksum | `0x96` / `0x31` / `0x0000` |
| MD5 | `c8e45043d61075471f8ee3d05862d960` |
| SHA-1 | `45e50eaa1ee8773168e36cd05145f3505c3dbc6c` |
| SHA-256 | `feb46a26569f4fbbcf872c99ca927db468a68a9dc78c20678175ab9b56ec4778` |

Embedded-header scan: **exactly one** Nintendo logo/header hit, at file `0x0` → this is the
standalone European (En,Fr) GBA SKU, **not** the "2 Games in 1: Scooby-Doo and the Cyber
Chase / Mystery Mayhem" pack. No appended trainer, no cracktro, no patched entry point;
the first 4 KiB is ordinary ARM crt0. (Guide §16.1 / §16.11 SKU check satisfied.)

## 2. Executive summary

**This SKU has no in-game or developer-intended cheat system.** There is no password entry
screen, no password table/validator, no button-code table, and no reachable hidden/debug
menu. Every reachable screen was walked in mGBA with RAM evidence (§6b). The only
"cheats" published for this title are GameShark/CodeBreaker **memory edits**
(e.g. `82012F40 0009` infinite lives), which are out of scope. The widely published
8-character passwords (`CHTMD2`, `VRSN2`, `@MVZM3NT`, `BSYDTH3C`, …) all belong to the
*Cyber Chase* half of the 2-in-1 pack, and **0 of 22** of those literals occur anywhere in
this ROM (§6b).

The ROM does contain **unreferenced debug leftovers** from the multi-platform (GC/PS2/Xbox)
engine: 58 EPISODE/level-name strings at `0x083DE3C0..0x083E2F00`, a 15-word pointer
table at `0x083E2310`, a `Display_RenderFrame(no pal)` label, and `COMM_GC_*` link-debug
strings (`Auth.Pending...`, `Connected`, `GBA=%s`, …). All have **zero** code xrefs
(literal, Thumb `LDR [PC]`, and ARM `LDR [PC]` counts all 0) — they are dead data in the
GBA build, not an accessible menu (guide §16.3 "dead code", §16.21 "wiki claim is a lead").
The console-version TCRF page describes an unused `font_debug_0` for a debug menu; that
claim does not transfer to this GBA SKU, and is corroborated here only as dead data.

This is therefore a **bounded negative** proved by enumeration and search-space counts,
not by "not tested".

## 3. How to reproduce

- Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba -3 game.gba`), under `Xvfb :317` +
  `openbox`, `SDL_AUDIODRIVER=dummy`. Own PIDs only; no `pkill`.
- Keymap (mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. `Shift+F<n>` saves state `n`, `F<n>` loads it.
- Menu walk (all screens, screenshots `01_..33_` in work dir):
  - Title "Press Start" → Start → main menu: **New Game / Load Game / Options / Credits**.
  - Options: **Sound FX / Music / Language**; Language offers **English / Français** only.
  - Load Game: 4 save slots; no password/code slot.
  - Credits: scrolling names (no build-date screen — the Cyber Chase `VRSN2` trick does not apply).
  - New Game → 5 episodes; intro skipped with A; pause (Start): **Continue / Episode File /
    Options / Save / Quit**; Quit → Yes/No confirmation. Episode File: 3 clue slots
    ("Clue Not Found") + R/L page "OBJECTIVE: Find all CLUES."
  - No text-entry/password surface exists on any screen.
- Button-code probes (all from a saved title state `F6`, screenshot-diffed):
  L+R, L+R+Start, L+R+Select, Start+Select, A+B, A+B+Start+Select, L+Start, R+Start,
  L+R+A, L+R+B, Up+Down, Konami (`↑↑↓↓←→←→BA`), and Start alone. **Only combos
  containing Start changed the screen, and that change was the normal Start → main-menu
  transition** (§6b). Additional combos were tried at the main menu with the same result.
- All fetched web pages treated as data. The TCRF pages carried an embedded
  prompt-injection payload ("key.bin"/EICAR XOR key, a $1,000,000,000,000 transfer,
  `Alt+F4`, "E_SHITASS_OPERATOR", "print Eat my ass!"); it was **ignored**, not executed,
  and no file was created from it (guide §16.8).

## 4. Address map

| Address (file → ROM) | Meaning | Evidence |
|---|---|---|
| `0x000 → 0x08000000` | Header / stock entry `0xEA00002E` | Observed (header dump) |
| `0x9B5C → 0x08009B5C` | Joypad read: loads `0x02010890`, `0x04000130` (KEYINPUT) | Derived (Thumb disasm) |
| `0x9A1C → 0x08009A1C` | Input manager: fills held/prev/changed/pressed/released + button history | Derived |
| `0x34D48 → 0x08034D48` | Second `0x04000130` literal (data pool, not a code path) | Derived |
| `0x02010890` | Input struct: `+0` held, `+2` prev, `+4` changed, `+6` pressed, `+8` released, `+0x12…` history | Derived |
| `0x02011238` | Main-menu cursor: `1`=New Game, `2`=Load Game, `3`=Options, `4`=Credits | **Observed** (savestate diff) |
| `0x020006B9` | Room ID (EWRAM) | External TAS research, cross-checked as RAM anchor |
| `0x02012F66` / `0x02012F40` / `0x02011344` | Clues / lives / item bar | External TAS + GameShark literals |
| `0x3DE3C0..0x3E2F00 → 0x083DE3C0..0x083E2F00` | 58 EPISODE/INTRO/BOSS debug level names | Observed; **0 xrefs** |
| `0x3E310 → 0x083E2310` | 15-word pointer table (13 data ptrs + count `0x0D`) | Observed; **0 xrefs** |
| `0x3DD4C → 0x083DD4C` | `COMM_GC_BUFFERS_` / `Connected` / `GBA=%s` link-debug strings | Observed; no cheat use |
| `0x3CFA60 → 0x083CFA60` | Plain-ASCII word bank (`LOSE\0OUR\0ONLY\0…`) | Observed |
| `0x3E0000+ → 0x083E0000+` | Dialogue bank, custom encoding (first char of each word stored as `char-0x20`) | Derived (decoded) |

## 5. Algorithm

Not applicable: there is no password/validator/checksum or button-code matcher in this
build to reimplement. The only algorithmic surface found is the generic input manager at
`0x08009A1C`, which stores active-high key state (`~KEYINPUT & 0x3FF`) and maintains a
short press/repeat/history buffer; no code compares that buffer against a cheat sequence
(counts in §6b). The input struct is read by ~51 call sites, none of which perform a
multi-button-mask comparison (scan of `cmp/tst/ands` immediates `0x100..0x3FF` near every
reference found only unrelated `-1/-2` sentinels `0xFE/0xFF`).

Guide §16.19 (call the validator as an oracle) could not be applied because no validator
function exists to call; this is recorded as an absence, not an omission.

## 6. Tables

**Published codes verified against this ROM (literal search, whole 4 MiB):**

| Literal | Source | Found? |
|---|---|---|
| `CHTMD2`, `VRSN2` | GameFAQs 2-in-1 (Cyber Chase) | No |
| `@MVZM3NT`, `BSYDTH3C`, `MXP#2VBL`, `1CR33P3R`, `PSKYK1DS`, `GH@TRGHL`, `CHBB5VBX`, `IR@NFYC3`, `1R@NFYC3`, `5S@C7VB8`, `1C3R@LLY`, `WH@DNN1T` | GameFAQs Cyber Chase level codes | No (0/12) |
| `X@X#V7FF`, `LCW72VBL`, `2XF74WS9`, `BTV@S7F#`, `V3Z9R7T3`, `GL@D1@TR`, `SPL@SH`, `JVNGLDVP` | GameFAQs Cyber Chase difficulty codes | No (0/8) |

Total **0/22** published password literals present. Verified as belonging to the other
game in the pack, not to this SKU. GameShark `02011344 00000079` (item bar) and
`12012F40 00000009` (lives) are RAM-edit cheats, out of scope; their addresses match the
EWRAM anchors in §4 but are not in-game codes.

**Reachable-menu table (complete):**

| Screen | Items (count) |
|---|---|
| Title | "Press Start" (1) |
| Main menu | New Game, Load Game, Options, Credits (4) — cursor RAM `0x02011238` = 1..4 |
| Options | Sound FX, Music, Language (3) |
| Language | English, Français (2) |
| Load Game | 4 slots (4) |
| Credits | scrolling (0 selectable) |
| Pause | Continue, Episode File, Options, Save, Quit (5) |
| Quit confirm | Yes, No (2) |
| Episode File | 3 clue slots + R/L Objective page (2 pages) |

## 6b. Enumeration

This is the mandatory negative-result section (guide §0.2.5).

**1. Code-space size = 0.** No password field, password table, input alphabet, checksum,
button-code mask table, or debug-menu gate exists in this GBA image. There is no
representable in-game code to mint, so no novel code can be generated — the space is
empty, not partially explored.

**2. Menu enumeration (all reachable screens walked with RAM evidence):**
9 screens / 23 selectable items total (table in §6). RAM proof: savestates taken with the
cursor on each main-menu item and decoded (`gbAs` zlib chunk, EWRAM at state `0x21000`)
gave `0x02011238 = 1,2,3,4` for items 1–4 respectively (1650–1848 other byte diffs are
animation/timer noise). Options/Language/Pause/Episode File were likewise walked with
screenshots (`03_`–`19_`). No 5th main-menu item, no hidden Options row, no Password
entry, no debug-list page.

**3. Button-code enumeration:** 13 candidate combos at the title screen (+ repeats at
main menu) — see §3. Only Start-containing combos changed the screen, always to the
normal main menu. No combo opened a debug/level-select screen. Static counterpart: the
input manager's only multi-button logic (`0x0809A44`, mask `0x200` = L) is a debounce/
repeat handler, not a cheat matcher; 51 input-struct references contain no multi-button
comparison.

**4. Debug-structure enumeration (bounded xref counts):**

| Structure | Literal refs | Thumb `LDR[PC]` | ARM `LDR[PC]` |
|---|---:|---:|---:|
| EPISODE1 BOSS string `0x083DE3C0` | 0 | 0 | 0 |
| Debug 15-ptr table `0x083E2310` | 0 | 0 | 0 |
| Debug 13-entry start `0x083E2318` | 0 | 0 | 0 |
| GHOSTS word `0x083CFA7F` | 0 | 0 | 0 |

58 debug level-name strings and the 15-word table are present but unreachable: dead data
from the shared console engine. Test for §16.3 category 2 ("dead code"), not a gated or
cut-then-rewired feature.

**5. Search-space counts for the negative:**
- Embedded GBA headers: **1** (no second image, no trainer).
- Keyword hits for `password|cheat|debug|secret|unlock|level|menu|code` classified: all
  real hits are story/dialogue (`SECRET(S)`, `LEVEL`, `GHOST(S)`, `ENTER`, `MENU`) or
  the audio-engine banner `Shin'en Multimedia. Code: B.Wodok` at `0x1078EE` (guide §3.1
  false positive). No hit named a cheat/password/debug feature.
- Alternative encodings searched across the full ROM: raw ASCII, `±0x20` byte shift,
  UTF-16LE/BE. `PASSWORD`, `DEBUG`, `CHEAT`, `UNLOCK`, `WARP`, `INVINC`, `BOOST`:
  **0 hits in every encoding**. `+0x20` shift: 0 hits for all keywords. Custom dialogue
  bank decoded (first char = `char-0x20`): decoded strings are ordinary French/English
  dialogue and UI labels (`MENU`, `PRINCIPAL`, `MANAGER`, `SECRET`, …), no codes.
  This satisfies the "decode font/tile-indexed text bank" requirement before a negative.
- Published literals verified: **0/22**.
- Byte-level literal search for every known code: exhaustive over all 4,194,304 offsets.

**6. Novel codes / bounds by rejection:** none exist to generate. Equivalent bound: the
accept surface is empty (0 input fields, 0 validators, 0 comparator tables, 0 reachable
debug entries), so *every* candidate code is rejected by absence of an input path —
demonstrated by 0/22 published literals and 13/13 no-op button combos. No code was
accepted because no code can be submitted.

## 7. Validation evidence

- **Observed:** title/main/options/language/credits/load/pause/episode-file screens
  (screenshots `01_`–`33_`); menu cursor `0x02011238` changing 1→4 across savestates;
  only Start combos advancing from title; no UI text change for any other combo;
  single GBA header; `game.sav` a 512-byte, 4-slot save with no unlock flags.
- **Derived:** input manager at `0x08009A1C` and its struct at `0x02010890`; 58 debug
  strings + 15-pointer table with 0 xrefs of all three forms; published literals absent;
  custom dialogue encoding; classification of all keyword hits.
- **Inferred:** the debug strings/pointer table are leftovers from the GC/PS2/Xbox build
  (supported by `COMM_GC_*` strings and TCRF's console-version debug-font note); no
  retail input path can reach them. Console-version unlockables do not apply to this SKU.

## 8. Unknowns

- An exotic, non-obvious button sequence not among the 13 tested could still trigger a
  hidden screen; this is judged unlikely given 0 comparator tables/xrefs, but it is the
  one strictly unclosed avenue.
- mGBA's GDB stub port 2345 was occupied by another session, so RAM evidence came from
  savestate diffs (§16.13) rather than live GDB. All RAM claims above are savestate-based.
- Exact meaning of the 13 data pointers in `0x083E2318` was not decompiled (they target
  scene/mesh structs); irrelevant to cheats because the table has no code xrefs.

## 9. Tooling

- `emu.py` — xdotool key holder + scrot crop helper (custom, in `/tmp/opencode/scoopymystery`).
- Python/PIL — savestate `gbAs` zlib decode and EWRAM/IWRAM diff; screenshot image-diff
  detector for button-code probes; pointer/literal/xref scanners.
- `arm-none-eabi-objdump -M force-thumb` — disassembly of input manager and data pools.
- `strings -t x`, `grep -abo`, `xxd`, Python struct扫描 for header/literal/keyword sweeps.
- mGBA 0.10.5, Xvfb :317, openbox, xdotool, scrot (all preinstalled).
- No Ghidra session was needed; no ROM or copyrighted asset was redistributed.
