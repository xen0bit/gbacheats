# WWE Survivor Series (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `WWE Survivor Series.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `WWE_SURVIVOR` |
| Game code | `BWWE` (serial AGB-BWWE-USA / AGB-BWWP) |
| Maker | `78` (THQ) |
| Version | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` (stock) |
| Fixed byte / complement / checksum | `0x96` / `0xCB` / `0x0000` |
| MD5 | `61eb8c6b8da8e0edc327c5ea7bd3a000` |
| SHA-1 | `bb61e289f2a09e7ce0e193267430dbc6f5583a49` |
| SHA-256 | `08b0c6895e3814cbd657b7da82ae7d2bf1f035a254ffa86bd455c337ec8df6de` |

Developer Natsume, publisher THQ — confirmed by the ASCII credits bank at file
`0x35696C`–`0x358Cxx` ("Natsume Staff", "THQ SPECIAL THANKS", "JAKKS PACIFIC INC",
"WWE_SURVIVOR" at header `0xA0`). The entry word is the stock branch (§16.1: not a
cracktro). Header checksum `0x0000` with a live complement `0xCB` is the normal
rebuilt-header artifact, not evidence of a patched ROM.

## 2. Executive summary

**Bounded negative (§0.2 case 5).** This GBA SKU has **no password code system, no
button-sequence cheat system, and no reachable hidden/debug menu**. Every in-game
screen was walked in mGBA; the only published "cheats" are (a) GameShark/Action
Replay memory writes — explicitly out of scope for this engagement — and (b)
save-progression unlockables and in-match *finisher inputs*, which are gameplay
mechanics rather than typed/entered cheat codes.

The ROM contains **no code-entry alphabet, no validator, no accepted-code table and
no button-mask sequence table with any code reference**. The visible UI strings are
tile-glyph encoded, so ASCII `strings` alone cannot prove this; the font/text path
was examined explicitly (§5, §7). The one 10-element run of key-like masks in the
image has **zero** xrefs and is therefore coincidental data, not a cheat table.

The save is a 512-byte EEPROM with a 128-byte record at offset `0x80`; the record
begins `43 41 42 45 57 57` ("CABEWW") and contains a `32 4B` ("2K") tag. Mutations
of its numeric fields did not change the roster; a marker written at `0x98` made the
title unresponsive, bounding the validated/used region (§6b).

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy mgba -3 <rom>`, Xvfb `:315`, openbox.
* Keymap (mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold 100–150 ms; >150 ms double-steps in menus.
* Menu path (verified):
  `PRESS START` → **Main Select** (Single Play / Multi Play / Options) →
  *Options* (Difficulty = Easy/Normal/Hard, Entrances, Flash, BGM, SFX, Exit) →
  *Single Play* (Story Mode / Exhibition Mode) → *Story Mode* (New Game only) →
  Vince McMahon intro → show/character select (RAW and SmackDown, eight names each)
  → Exhibition "Select Superstar" detail screen. **Multi Play** plays a short
  transition and falls back to the title (no link partner).
* Buttons tested on the title screen with a reloadable savestate each time:
  `L+R+Start`, `L+R+Select`, Konami sequence, the 10-mask run from `0x0509F0`
  (`← ↓ L ↑ ↓ R ↑ ↓ R R`), `L+R ↑ L+R ↓`, `Start+Select+A+B`. None opened a hidden
  screen; `L+R+Start` merely starts the game normally (the Start edge is what acts).

Published reconnaissance (CheatCC, Neoseeker, SuperCheats, GameFAQs guide,
GameHacking.org, European CodeBase) yields **no password strings and no button
codes**. Every published "code" is either a GameShark/AR memory patch (out of
scope) or an in-match input such as "grapple then press Select with a full special
meter" or "press L near the apron in a hardcore match" — gameplay finisher/weapon
inputs, not cheat codes. The 100-GBA crackme sweep (REMY HAX) does not list this
title among its code-bearing ROMs.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Header / stock entry `0xEA00002E` | Observed (hex dump) |
| `0x08000560` | Loads `0x03007FFC` (IRQ stack, crt0) | Derived (LDR-literal scan) |
| `0x08001110`–`0x0800115C` | Joypad poll: reads `0x04000130`, inverts, computes held/pressed | Derived (disassembly) |
| `0x0800113C` | Literal `0x03000080` = input-state struct base | Derived (byte-order corrected) |
| `0x0300008E` / `0x03000090` / `0x03000092` / `0x03000094` | held / new-press / last-press / repeat counter (`u16`) | Derived |
| `0x08001160`–`0x08001170` | Soft-reset chord test `(held & 0xF) == 0xF` (A+B+Select+Start) | Derived — standard reset, not a cheat |
| `0x08006424`, `0x0800644C` | Highest-call-count Thumb BL targets (316 / 292 calls); Ghidra decompiles them as object-field setters, **not** `strcmp` | Derived (REA/Ghidra) |
| `0x0509F0` | 10-element run of key-like `u16` masks; **no** pointer or LDR literal references `0x08509F0` | Derived — coincidental data |
| file `0x3C2C5C`… | Uncompressed 4bpp tile bank; VRAM tiles match these bytes exactly | Observed |
| file `0x35696C`… | ASCII credits bank (the only long human-readable ASCII in the image) | Observed |
| EEPROM `0x00000080`–`0x000000FF` | 128-byte save record used by the game (magic `CABEWW`, `2K` tag) | Observed (`.sav` dump) |

Note the literal-pool pitfall (§11): objdump shows `0080 0300` at `0x0800113C`,
which is the little-endian word `0x03000080`, **not** `0x03000000`.

## 5. Algorithm

Not applicable — no validator exists. The relevant algorithms are:

* **Input model.** `held = ~KEYINPUT & 0xFFFF`; `pressed = held & ~old_held`;
  old_held is stored, and a 30-frame repeat counter is kept. There is no history
  buffer longer than the single `last-press` word, and no comparison against a
  stored key-mask sequence anywhere in the polled path (§5.4a scan below).
* **Text model.** UI strings are not ASCII. VRAM tiles `0x250`–`0x259` contain
  rendered glyphs ("o o s e", "a", "s h o w" from "Choose a show.") with rows of
  `0x22` fill above and below each 8×8 glyph; the graphics are 4bpp and match a
  ROM tile bank byte-for-byte. Consequently `strings` finds none of the visible
  labels, and a negative based on ASCII alone would be invalid — the tile path was
  checked independently.

## 6. Tables

* **Save record (EEPROM `0x80`):**
  `43 41 42 45 57 57 | 00 01 00 01 00 01 00 01 | 32 4B | 0F 2E | 00 00 | 00 01 00 01 | 00…`
  (magic `CABEWW`, four `u16` fields, `2K` tag, `u16 0x0F2E`, two zero/`u16` fields;
  remainder zero through `0xFF`; EEPROM bytes outside `0x80`–`0xFF` are `0xFF`).
* **Menu item counts (all reachable entries):** Main Select 3; Options 6
  (Difficulty values 3, each other toggle 2); Single Play 2; Story Mode 1;
  character select 2 shows × 8 visible superstars; Exhibition detail 1 with a
  YES/NO confirm. There is no "Password", "Cheat", "Code", "Debug" or "Unlock"
  entry on any screen.
* **Published unlockables (in scope as unlockables, evidence = published only):**
  The Rock (win RAW story mode 5 times with Chris Jericho / complete story with
  every character — sources disagree), The Big Show (win SmackDown story mode
  5 times with The Undertaker), Hulk Hogan (beat season mode with The Rock).
  The character-select screen on a clean save shows only the 16 base superstars;
  these three were **not** observed to appear, and their in-ROM flag/counter was
  not isolated in this session (see §8).

## 6b. Enumeration

**Search space checked and counts (this is the bounded negative required by §0.2):**

| Check | Space | Result |
|---|---|---|
| ASCII string inventory | 28,876 `strings -t x -n 4` records (whole 4 MiB) | 0 hits for `password`, `cheat`, `secret`, `unlock`, `debug`, `level select`, `invalid`, `enter code`; only credit words `Test Supervisor`, `Test Leads`, `Testers` |
| Published code literals | All fetched cheat pages | 0 password/button codes exist for this SKU; only GS/AR patches and gameplay finisher inputs |
| Visible-label literal search | `Benoit`, `Triple H`, `Undertaker`, `Jericho`, `Mysterio`, `Christian` in ASCII, `+0x20`, uppercase | 0 hits — text is tile-glyph encoded; font path examined instead (§5) |
| Thumb LDR-literal scan | All 2-byte-aligned halfwords; 26,353 candidate LDR literals | KEYINPUT (`0x04000130`) read once at `0x08001112`; input struct `0x03000080`; 0 loads of EEPROM base `0x0E000000` |
| Button-mask table scan | All `u16` aligned values; single-key masks `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}` | 15 runs of ≥4 consecutive masks; longest is 10 masks at `0x0509F0`; **0** PC-relative literals or 32-bit pointers to `0x08509F0` → no reachable table |
| Thumb BL inventory | All BL halfword pairs, whole ROM | Top 316-call target `0x08006424` is an object-field setter (Ghidra), not a string comparator; no password-style `strcmp` dispatch found |
| Debug-gate strings | Whole image, ASCII + case-insensitive | 0 candidates |
| Title-screen button codes | 6 documented/common sequences, each from a fresh savestate | 0 hidden screens (§3) |
| Menu walk | Every reachable menu screen listed in §6 | 0 code-entry or hidden entries |

**Space size / novel codes:** the accepted-code space is **empty (0 values)** —
there is no alphabet, length, checksum or validator field to enumerate, so no
novel code can be minted and §0.2's "generate a code absent from every published
list" requirement is satisfied by this bounded negative with counts, not by a
fabricated code. The three published unlockables are progression rewards, not
input codes; their combined state space was not brute-forced (§8).

**Bounds proven by rejection:** 
1. Writing six numeric `u16` fields of the EEPROM record to `0x0005` (the published
   "win 5 times" count) and rebooting left the two rosters byte-for-byte identical
   at the character-select screen — those fields are not the unlock counters.
2. Writing `MARKER!!` at EEPROM `0x98` made the title screen stop responding to
   Start on two consecutive boots (bright "PRESS START" persists and no menu
   appears), whereas the clean record boots normally. This bounds the live/checked
   portion of the 128-byte record and demonstrates that the record is consumed at
   boot.
Both are **Observed** (screenshots `s29`–`s34` in the work dir).

## 7. Validation evidence

* **Observed:** all screenshots `s00_boot.png` … `s38_multi2.png` in
  `/tmp/opencode/wwesurvivor/`; mGBA 512-byte EEPROM `.sav` dumps before/after
  mutation; GDB register/memory reads through the mGBA stub (`0x04000130` returned
  `0x03EF` with Right held, i.e. bit 4 clear — input path confirmed).
* **Derived:** disassembly of `0x08001110`–`0x08001170`; LDR-literal and BL scans;
  Ghidra decompilation of the two hottest library targets; VRAM-glyph montage and
  ROM tile-bank match; button-mask run xref count.
* **Inferred:** the three published unlock conditions; the interpretation of
  `CABEWW`/`2K` as a magic/tag; that `0x0509F0` is compressed/graphic data.

## 8. Unknowns

* The ROM-side implementation of the three unlockables (flag bits, counters, and
  their setters) was not isolated. Ghidra auto-analysis finds the functions but a
  raw 4 MiB Thumb/ARM image with no symbols made the save routine impractical to
  pinpoint within this session; setting the obvious numeric fields did not unlock
  anything. The published conditions therefore remain published claims, not
  ROM-verified facts.
* The contents of the 128-byte save record beyond the magic and `2K` tag were not
  fully decoded; a checksum/validation appears to exist (a marker at `0x98` is not
  tolerated) but its algorithm was not recovered.
* The Exhibition "Select Superstar" detail screen and a live match pause menu were
  reached visually but not exhaustively exercised; neither showed a cheat/debug
  entry, and no published source claims one.
* Fetched cheat pages were treated strictly as data. No prompt-injection payload
  was encountered in this engagement; none of their instructions were executed.

## 9. Tooling

* `mgba` 0.10.5 under Xvfb `:315` + openbox, `SDL_AUDIODRIVER=dummy`; GDB stub on
  `127.0.0.1:2345` with a persistent pty-backed `gdb-multiarch` client (the stub
  tolerates only one clean session; repeated fresh connections wedge it).
* `arm-none-eabi-objdump -M force-thumb`, Capstone (`ldrscan.py`, `blscan.py`),
  Ghidra 12.1.4 through the REA MCP provider, Python/Pillow for VRAM/ROM tile
  montages (`ss_extract.py`, `render_tiles.py`), `xdotool`/`scrot` for input and
  evidence, `test_combos.py` for title-code trials.
* Working files (not committed, not in the ROM folder): `/tmp/opencode/wwesurvivor/`.

## 10. Legal note

No ROM bytes, extracted graphics or copyrighted assets are reproduced here. Only
hashes, addresses, observations and the analyst's own tooling are published.
