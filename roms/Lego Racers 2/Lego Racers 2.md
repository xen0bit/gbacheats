# LEGO Racers 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Lego Racers 2/Lego Racers 2.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `LEGO RACERS` |
| Game code | `ALRE` |
| Maker code | `5Q` |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Fixed `0x96` | present |
| Header checksum | stored `0x0000`, computed `0x0560` — rebuilt-header artifact; not a patch marker |
| Embedded GBA headers | **exactly 1** (Nintendo logo at file `0x004`); no second image, no appended trainer |
| MD5 | `35ca3b91976497cc24384f9367f16462` |
| SHA-1 | `293ffd94f1637c49cd5e29447399cce602c6ab2f` |
| SHA-256 | `ea2cf5aaa5df5841db9b9074e138396754a3d73025c00829b34af5b9f977e695` |

**Observed (Phase 0):** stock first 4 KiB (`0x080000C0` crt0 installs IRQ, copies IWRAM, zeroes EWRAM), no cracktro, no scene entry patch, no 2-in-1 shell. Single 8 MiB image.

## 2. Executive summary

**Finding: the GBA build has no password/cheat-code system and no hidden/debug menu.** It is a separate
implementation by Pocket Studios; the widely published button-sequence cheats belong to the PS2/PC builds
(Attention to Detail) and do not exist in this ROM.

Evidence in three layers:

1. **Binary absence.** No accepted-code table, no key-mask sequence table, no validator, and no
   code-related text exist in any of the four encodings searched (ASCII, `+0x20`, UTF-16LE, UTF-16BE)
   across the whole 8 MiB. All 16 published PS2/PC sequences were searched as 5 direction encodings ×
   2 widths × 2 byte orders × forward/reverse (640 literal searches): zero code-region hits.
2. **Web verification.** The 3rd party cheat indexes GBA cheats page (archived 2024-01-05) lists **no GBA codes** — every
   entry is explicitly tagged PS2 or PC. The full 16-code PS2/PC list (3rd party cheat indexes + the 2026 decompilation
   write-up) was collected and tested anyway.
3. **Runtime absence.** All 16 published sequences were entered at both documented entry points
   (GBA **MAIN MENU** and the in-race **PAUSE** menu) under the GDB stub, with before/after dumps of
   EWRAM (`0x02000000..0x02040000`), IWRAM (`0x03000000..0x03008000`) and the 512-byte SRAM save.
   Every test: **0 changed EWRAM bytes, 0 changed SRAM bytes**, and the only low-IWRAM delta was the
   frame counter at `0x03000D90` (changes identically with no input). Eight common debug key combos
   (`L+R+Start`, `L+R+Select`, `Start+Select+A+B`, etc.) likewise produced 0 state deltas.

Every reachable menu was walked and enumerated from the plain-ASCII text bank plus live screens
(§7). The only character entry is a 5-slot driver name used for dialogue substitution (`*`), not a
validator; the LEGO Racers 1 name-cheat strings (`NMRCHTS`, `NWHLS`, `NCHSSS`, …) are absent.

No novel code can be minted because there is no code system to enumerate — the §6b section proves the
bounds by exhausting the input spaces and testing rejection of all published values.

## 3. How to reproduce

```
Xvfb :316 -screen 0 1024x768x24 &
DISPLAY=:316 openbox &
DISPLAY=:316 SDL_AUDIODRIVER=dummy mgba -g -3 "Lego Racers 2.gba" &
xdotool search --name mGBA | head -1 | xargs xdotool windowfocus
```

Keymap used (mGBA SDL defaults): `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`,
D-pad = arrow keys. Holds of 80–150 ms; 0.4–1 s waits between screens.

Menu path to each tested screen:

* **Title** → language `ENGLISH` (`A`) → intro dialogue (`A` ×5) → `PRESS START` (`Start`).
* **MAIN MENU** (`STORY GAME / SINGLE PLAYER / MULTIPLAYER / OPTIONS`).
* **OPTIONS** → `MUSIC ON`, `SOUND EFFECTS ON`, `SAVE OPTIONS`
  (`CLEAR STORY MODE`, `CLEAR HI-SCORES`), `CREDITS`.
* **SINGLE PLAYER** → `ARCADE GAME` → `SETTINGS` (`LAPS 3`) → `CHOOSE RACERS` → `CHOOSE TRACK`
  (`BRICKTON / DINO ISLAND / MARS / ARCTIC / XALAX`) → race → `Start` → **PAUSE**
  (`RESUME / RESTART / SOUND OPTIONS / QUIT`).
* **SINGLE PLAYER** → `TIME TRIAL`, `BONUS GAMES` (`COPS AND ROBBERS`, `COLLECT THE EGGS`,
  `TUBE RACING`, `COLLECT THE METEORS`, `LEVEL 1..3`).
* **SINGLE PLAYER** → `SPECIAL GAMES` → `BATTLE GAME` (5 worlds, all selectable),
  `CAPTURE THE FLAG`, `CONSTRUCTION GAME`.
* **STORY GAME** → dialogue → face/body/legs builder → **ENTER NAME** (5 slots, `?` placeholders).
* **MULTIPLAYER** → `PLEASE WAIT` (link-mode lobby; no entries).

A savestate was taken at MAIN MENU (`Shift+F1`) so every code test reloaded to an identical state;
`F1` restores it. GDB stub: `target remote :2345`, `interrupt`, `dump binary memory`, `continue &`.

## 4. Address map

| Item | Address / file offset | Evidence |
|---|---|---|
| ROM base / entry | `0x08000000`, entry `0xEA00002E` | observed header bytes |
| Single GBA header (Nintendo logo) | file `0x004` | observed, one hit |
| Text bank (plain ASCII, all languages) | file `0x01D5200..0x0215000`, ROM `0x09D5200..` | observed strings |
| `MAIN MENU` string | file `0x01D525D` | observed |
| `ENTER NAME`, `DRIVING LICENCE` | file `0x01D5267`, `0x01D5272` | observed |
| `PRESS START`, `CHOOSE CHARACTER`, `SPECIAL GAMES`, `BONUS GAMES` | `0x01D529E`, `0x01D52AE`, `0x01D52EB`, `0x01D544C` | observed |
| Menu label table (English) | file `0x01D5260..0x01D5500` | observed contiguous NUL/dot-delimited strings |
| `CODE SUPERVISOR` (credits role, **not** a cheat) | file `0x01DB763` (+7 localized copies) | observed context |
| Generic key read → held/pressed globals | `0x08006B44` (literal `0x04000130` at `0x08006B64`) | derived (disassembly) |
| Second key reader → `0x03001268`, `0x03000D70` | `0x0800CF4E` (literal at `0x0800CF70`) | derived |
| Menu input handler (B-button check) | `0x08018F7C` (literal at `0x08019000`) | derived |
| Fourth key reader | `0x08020C1C` | derived |
| Frame counter (only low-IWRAM delta over time) | `0x03000D90` | observed |
| SRAM save (512 bytes) | `0x0E000000`, file `Lego Racers 2.sav` | observed |

No validator, accepted-code table, key-mask table, or cheat flag word was found; none exists to map.

## 5. Algorithm

Not applicable — no code system was located. The negative is bounded explicitly in §6b.

For completeness, the *only* transformation found on user text is the driver-name entry path: five
slots selected with Up/Down and committed with A, then rendered into dialogue at `*` positions. No
`strcmp`/`memcmp` against a constant is reachable from that buffer (no candidate literal exists in
the ROM in any encoding), so §16.2b ("a text field is not a password field") applies.

## 6. Tables

### 6.1 Menu inventory observed (all reachable entries)

| Screen | Entries |
|---|---|
| Title | `ENGLISH` (language select), `PRESS START` |
| MAIN MENU | `STORY GAME`, `SINGLE PLAYER`, `MULTIPLAYER`, `OPTIONS` |
| OPTIONS | `MUSIC ON/OFF`, `SOUND EFFECTS ON/OFF`, `SAVE OPTIONS`, `CREDITS` |
| SAVE OPTIONS | `CLEAR STORY MODE`, `CLEAR HI-SCORES` |
| SINGLE PLAYER | `ARCADE GAME`, `TIME TRIAL`, `BONUS GAMES`, `SPECIAL GAMES` |
| ARCADE SETTINGS | `LAPS 3` (and `CHOOSE RACERS`, `CHOOSE TRACK` downstream) |
| Track select | `BRICKTON`, `DINO ISLAND`, `MARS`, `ARCTIC`, `XALAX` |
| PAUSE | `RESUME`, `RESTART`, `SOUND OPTIONS`, `QUIT` |
| BONUS GAMES | `COPS AND ROBBERS`, `COLLECT THE EGGS`, `TUBE RACING`, `COLLECT THE METEORS`, `LEVEL 1..3` |
| SPECIAL GAMES | `BATTLE GAME`, `CAPTURE THE FLAG`, `CONSTRUCTION GAME` |
| BATTLE GAME | all 5 worlds selectable (no lock icon) |
| STORY GAME | character builder → `ENTER NAME` (5 chars) → `DRIVING LICENCE` |
| MULTIPLAYER | `PLEASE WAIT` (link lobby) |

### 6.2 Published codes tested (all PS2/PC, none GBA)

| Name | Sequence (L/R/U/D = D-pad) | GBA MAIN MENU | GBA PAUSE |
|---|---|---|---|
| Award Everything | L3 U3 R3 D3 L U R D | rejected | rejected |
| Unlock All Tracks | R U2 R L D2 L | rejected | rejected |
| Unlock Bonus Games | U R2 U D L2 D | rejected | rejected |
| Award Car Upgrades | D L U3 D R U3 | rejected | rejected |
| Find All Hidden Golden Bricks | (L,R)×4 U L D R | rejected | rejected |
| Unlock Arctic | L2 R2 L2 R2 U R L | rejected | rejected |
| Unlock Dino Island | L2 R2 L2 R2 U L R | rejected | rejected |
| Unlock Mars | L2 R2 L2 R2 D L R | rejected | rejected |
| Unlock Xalax | L2 R2 L2 R2 D R L | rejected | rejected |
| Be A Martian | R L R U D L R U2 | rejected | rejected |
| Top-Down Camera | L U3 R U3 L U3 R U3 | rejected | rejected |
| Mirror Mode | L4 R4 U4 D4 | rejected | rejected |
| Wide Angle Camera | L3 R3 U3 D3 L3 R3 | rejected | rejected |
| Super Speed | (L R U D)(R L U D) ×3 + L R U D | rejected | rejected |
| Enable Stream Replay (debug leftover) | L10 | rejected | rejected |
| Enable Stream Store (debug leftover) | R10 | rejected | rejected |

"Rejected" here means **zero observable effect**: no EWRAM/SRAM delta and no confirmation. The PS2/PC
build confirms a valid code with a giggling sound; no such confirmation was ever triggered on GBA.

## 6b. Enumeration

**Space definition.** There is no code space to enumerate. The two candidate input surfaces were
exhausted:

1. **Button sequences.** 16 published sequences (lengths 4–20 presses), each encoded as
   active-high/active-low u8/u16, index maps `{R=1,L=2,U=3,D=4}`, `{U=1,D=2,L=3,R=4}`, nibble map
   `{L=1,R=2,U=4,D=8}`, little/big endian, forward and reversed — **640 literal searches** over
   `0x08000000..0x08030000` (code) and the whole 8 MiB: **0 code-region hits**. The only raw hits were
   runs of `0x20`/`0x10` inside graphics/compressed data at `0x02CD56`, `0x030B04`, `0x03AFB2`,
   `0x08685D44` — all confirmed as tile/pixel data, not tables. Additionally, 8 debug key combos
   were pressed live at MAIN MENU with 0 EWRAM/SRAM/flag deltas.
2. **Text/code input.** The only text entry is the 5-slot driver name. Searched the entire ROM in
   ASCII, `+0x20`, UTF-16LE and UTF-16BE for `password`, `cheat`, `debug`, `unlock`, `hidden`,
   `code`, `konami`, `gamegenie`, `gameshark`: **0 relevant hits**. Case-insensitive ASCII hits are
   only `CODE SUPERVISOR` (8 credit-role strings) and French `aucun secret pour moi` at `0x01DD20E`
   (dialogue). The LEGO Racers 1 name cheats `NMRCHTS`, `NWHLS`, `NCHSSS` etc. are **absent**.

**Validator model.** None exists; therefore no offline reimplementation is possible or meaningful.

**Novel codes.** None can be minted: there is no generator/validator pair and no accepted set. Per
§0.2 this is a *proven negative*, not an untested gap — the entire candidate input space was searched
and the published values were all entered in the emulator.

**Bounds proven by rejection.** All 16 published values were rejected at both real entry points with
byte-for-byte identical RAM/save before and after (deltas = 0), so the "accepted set" is empty for
every value anyone has ever published. The only changing low-IWRAM word during these tests was the
frame counter `0x03000D90`, which changes at the same rate with no input — a clean control.

**Negative-result classification (§16.3):** this is a **No system** case (no alphabet, table,
validator, or input surface for codes), not dead code, not a cut feature, not a gated feature.
`SAVE OPTIONS → CLEAR STORY MODE / CLEAR HI-SCORES` are destructive reset options, not unlock gates;
all five worlds/tracks and all three special games were selectable from a fresh save.

## 7. Validation evidence

* **Observed** — boot logos, language select, intro dialogue, title, MAIN MENU, OPTIONS, SAVE
  OPTIONS, CREDITS (listed in text bank), SINGLE PLAYER and its four sub-screens, ARCADE SETTINGS,
  track select, live race, PAUSE, STORY GAME character builder, 5-slot ENTER NAME, MULTIPLAYER
  `PLEASE WAIT`. Screenshots retained in `/tmp/legoracers2/` (not attached).
* **Observed** — 16 published sequences × 2 screens + 8 combos, each with GDB RAM dumps before/after:
  0 EWRAM delta, 0 SRAM delta, 0 low-IWRAM delta beyond the frame counter.
* **Derived** — four `0x04000130` readers at `0x08006B44`, `0x0800CF4E`, `0x08018F7C`, `0x08020C1C`;
  none contains a comparison against a multi-press sequence.
* **Derived** — single header, stock entry word, no appended trainer (logo scan).
* **Inferred** — the driver-name field feeds only dialogue substitution; no comparator literal exists
  anywhere in the image.
* **Fetched-page hygiene** — 3rd party cheat indexes PS2/PC cheats page returned HTTP 403 directly and was read via
  `web.archive.org`; the moonbase.lgbt decompilation write-up was treated strictly as data. No
  prompt-injection payload was encountered in either source. No fetched instruction was acted upon.

## 8. Unknowns

* The 512-byte SRAM layout was dumped but not fully field-decoded; exact bit meanings of the
  progress/upgrade words were not needed for the cheat question and were not reverse engineered.
* The four "bonus games" were enumerated in the menu and text bank but not played to completion;
  their objectives are fully quoted in the text bank (`0x01D544C..0x01D8900`).
* mGBA's GDB stub cannot read `0x0E000000` (SRAM); save verification used the on-disk `.sav` copy instead.
* Multiplayer `PLEASE WAIT` cannot be progressed without a second GBA/link cable; no hidden menu was
  observed there, but a link-triggered screen is untested.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` — literal-pool and input-routine disassembly.
* Python 3 + Capstone 5.0.7 / Keystone — literal xrefs and 640-way button encoding scan.
* `strings -t x -n 3/4`, `grep -iE`, custom Python multi-encoding scanner (ASCII, `+0x20`, UTF-16LE/BE).
* mGBA 0.10.5 with `-g` GDB stub on Xvfb `:316`, `SDL_AUDIODRIVER=dummy`.
* `gdb-multiarch` persistent session via FIFO; `dump binary memory` for EWRAM/IWRAM; on-disk `.sav`
  for SRAM. `scrot` + ImageMagick crops; `tesseract` for OCR triage (font too stylised for reliable OCR,
  so conclusions rest on RAM + direct screenshot reads).
* `web.archive.org` snapshot 20240105224016 of the 3rd party cheat indexes GBA cheats page; moonbase.lgbt 2026
  decompilation write-up (data only).

No ROM bytes or copyrighted assets are reproduced in this report. All addresses/hashes refer to the
exact ROM identified in §1.
