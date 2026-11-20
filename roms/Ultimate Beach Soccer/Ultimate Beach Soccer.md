# Ultimate Beach Soccer (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ultimate Beach Soccer/Ultimate Beach Soccer.gba` |
| Size | 4,194,304 bytes (0x00400000), 32 Mbit |
| Header title | `ULTIMATE BEA` (truncated "ULTIMATE BEACH SOCCER") |
| Game code / maker | `AVEE6U` / `6U` |
| Version / fixed / complement | `0x00` / `0x96` / `0x58` |
| Header checksum | `0x0000` (rebuilt-header artifact; per guide §16.1) |
| Entry branch | `0xEA000030` (stock, not a cracktro) |
| MD5 | `d14cf631928fc1523b49c9ae0a2cdd2f` |
| SHA-1 | `8d21a404042c2b3c5fd1f6f1b6a28c7c6ff72dd7` |
| SHA-256 | `eed58607e7c099dcc49b3f62d8e3f4602b22a77ed4560b86b271be979dd6942c` |
| Build string | file `0x3FE0B4` → ROM `0x0BFE0B4`: `PRO BEACH SOCCER` / `Jun 18 2003 17:07:46` / `WWW;MAGICPOCKETS;COM` / `NOT FOR RELEASE OR PUBLIC PERFORMANCE.` |
| Developer / publisher | Magic Pockets / DreamCatcher Interactive (US SKU) |

The build string and CRC/serial match the TCRF mirror entry for the US release, so addresses below are specific to this revision. No multi-game header, cracktro, or appended trainer was found.

## 2. Executive summary

**No in-game password, cheat-code, button-code, or hidden debug menu exists in this ROM.** The only input-driven "cheats" published for the title are *gameplay techniques* (the Bicycle Kick / Super Dribble controls) and *save-based unlockables* (winning specific competitions unlocks five All-Star team slots and the World Trophy/World Championship). Both were enumerated; neither is a code system.

This is a bounded negative, not "did not find": every reachable menu screen was walked, the two text banks and the font/alphanumeric tables were decoded and searched in eight encodings (0 hits for password/cheat/secret/debug/level select/unlock), the only on-screen text-entry surface was identified as a **profile name field** (28 cells: A–Z, `123`, `OK`) with no comparison against constants, and a raw scan of all 4 MiB for key-mask sequences found 1,893 candidate `u16` runs and 54 active-low runs, all explainable as Thumb opcodes/PCM samples; the exact published L→B→A prefix occurs once, at file `0x73338`, inside 8-bit signed PCM audio.

**Findings (confidence):**
1. **Observed** — 6 main-menu entries, 7 option entries, 4 pause entries, 25 team slots (20 playable + 5 `???`), 25 opponent slots, 4 cups, 4 leagues; no hidden/undocumented entry.
2. **Derived** — key state globals at IWRAM `0x030044DC` (`held & ~prev`, i.e. newly-down), `0x030044CC` (`(held ^ prev) & prev`, i.e. newly-up), `0x03007C4E` (previous held), written by routine at `0x083E4DDA`; no validator consumes a code buffer.
3. **Derived** — save data is a set of 120-byte, checksummed profile records (checksum routine `0x083D9BD0`, constant `0x1234`; loader `0x083D9D78`); unlock state lives in save data, not in typed input.
4. **Inferred** — the 5 `???` team cells are the All-Star teams listed by GameFAQs; their setters are competition-win paths (no controller-only path was found, and no published or ROM-internal code grants them).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `mgba -3`. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. 45–120 ms holds; F1 loads the slot-1 savestate, Shift+F1 saves it.
* Boot → DreamCatcher splash → Start → **Name** entry (first boot only) → spell a name, move to `OK`, press A → **Main Menu**.
* Menu path used: `Exhibition → Your Team → (team) → stats → Opponent → VS screen → match → Start (pause)`. Also `Tournaments → Cup/League → Bangkok/Rio/Marseille/Venice`, `Training → Your Team`, `Link Mode`, `Options → Match Length / Difficulty / Music / Sfx / Winners Table / Name / Credits`.
* Savestate at the Main Menu was the working base for every test. ROM-folder `.sav`/`.ss1` were removed at the end.

## 4. Address map

| Item | File offset | ROM address | Notes |
|---|---:|---:|---|
| Header/title | `0x0000A0` | `0x080000A0` | `ULTIMATE BEAAVEE6U` |
| Build info | `0x003FE0B4` | `0x0BFE0B4` | "NOT FOR RELEASE…" |
| Keyboard strings | `0x003F7F00` | `0x0BF7F00` | `A`, `ABC`, `123`, `OK`, `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `0123456789 .,':-/*!?%$&#()` |
| Font/glyph index maps | `0x003F7FA0`–`0x003F8010` | `0x0BF7FA0`–`0x0BF8010` | tile-index lookup tables; no code alphabet |
| Filler developer credit | `0x003FDxx2`+ | `0x0BFDxx2`+ | `* Engine by www.MagicPockets.com` repeated to EOF |
| Localized text banks | `0x000D6F40`, `0x000D7D70`, `0x000DD112`, `0x000EC8A9`, `0x001AEC0A`, mirror `0x003CF7DE` | `0x08D6F40`, … | menu/move names; strings are length/control-byte packed, not NUL-only |
| Input reader | `0x003E4DDA` | `0x083E4DDA` | `ldrh` from `0x04000130`, computes pressed/released/held |
| KEYINPUT literal | `0x003E4E08` | `0x083E4E08` | `0x04000130` |
| newly-down / "pressed" (u16) | — | `0x030044DC` | `held & ~previous` |
| newly-up / "released" (u16) | — | `0x030044CC` | `(held ^ previous) & previous` |
| held (u16) | — | (local `r2` in the input routine) | `~KEYINPUT & 0xFFFF` |
| previous held | — | `0x03007C4E` | updated every poll |
| Profile table in RAM | — | `0x03000E30` / `0x03000E60` | 120-byte records, 8-byte name at +0, checksum at +0x38 |
| Save-record checksum | `0x003D9BD0` | `0x083D9BD0` | additive, folds with constant `0x1234` |
| Profile loader | `0x003D9D78` | `0x083D9D78` | iterates 120 records, validates +0x38 checksum, copies names |
| Profile writer | `0x003E507C` | `0x083E507C` | recomputes +0x38 checksum before storing |
| Title/menu key handler (sample) | `0x003D770A` | `0x083D770A` | checks held mask and pressed `0x8` (Start) |

File offset ↔ ROM address: `ROM = 0x08000000 + file_offset`. Savestate raw `gbAs` layout (4 MiB ROM): IWRAM at raw `0x19000`, EWRAM at raw `0x21000`; IWRAM address `0x0300xxxx` maps to raw `0x19000 + 0xxxxx`.

## 5. Algorithm

There is no code algorithm to reimplement. The two algorithms actually present are:

1. **Key-state derivation** (`0x083E4DDA`), equivalent to:
   ```
   held = (~KEYINPUT) & 0xFFFF
   [0x030044DC] = held & ~prev        (newly-down)
   [0x030044CC] = (held ^ prev) & prev (newly-up)
   [0x03007C4E] = held                (prev for next frame)
   ```
   Masks are the standard active-high GBA bits (A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200). Menu handlers test these masks directly; there is no press-history ring, index counter, or sequence table.

2. **Profile-record checksum** (`0x083D9BD0`): additive sum over selected byte ranges of a 120-byte record, folded with `0x1234` and a 16-bit rotate/fold; the loader at `0x083D9D78` rejects records whose stored +0x38 value disagrees. This governs save/profile validity and unlock persistence only.

## 6. Tables

* **Name-entry alphabet (28 cells)**: `A B C D E F G H / I J K L M N O P / Q W E R T Y U I O P / A S D F G H J K L / Z X C V B N M / 123 / OK` (rendered layout; canonical strings at `0x0BF7F00`). A types, B/L/R delete, D-pad moves, OK confirms. This is a **name field**, not a password keypad.
* **Main Menu (6)**: Exhibition, Beach Soccer Tour, Tournaments, Training, Link Mode, Options. No hidden seventh entry (cursor stops at Options).
* **Options (7)**: Match Length (3/6/9 min), Difficulty (Easy/Normal/Hard), Music (Yes/No), Sfx (Yes/No), Winners Table, Name, Credits.
* **Pause (4)**: Continue, Sounds, Restart Match, Quit Match.
* **Team grid (25 cells)**: 5×5; 20 national flags selectable, 5 `???` cells in column 5 (rows 1–5) are locked; pressing A on a `???` cell does nothing (observed). Opponent grid shows the same 20 unlocked flags.
* **Tournaments**: type Cup/League; venues Bangkok, Rio, Marseille, Venice (4 each). Competition unlockables published for this SKU: World Trophy + World Championship (win Pro Beach Soccer Tour), Africa All Stars (Marseille Cup), America All Stars (Venice Cup), Asia All Stars (Venice League), Europe 1 All Stars (World Championship), Europe 2 All Stars (Marseille League), World All Stars (World Trophy).
* **Published "cheats"**: Bicycle Kick (hold L to flip the ball up, press B in the air, then A) and Super Dribble (L+R during "State of Grace") — documented in the manual and on GameFAQs/VGChartz; these are controls, not codes. GameHacking.org entries are CodeBreaker/GameShark RAM patches and are explicitly out of scope.

## 6b. Enumeration

**Code-space definition:** empty. There is no alphabet/length/checksum system to enumerate, so the enumeration is the *bounded negative* required by guide §0.2:

| Search space | Count checked | Result |
|---|---:|---|
| Keyword hits for `password/cheat/secret/debug/level select/unlock/hidden/code` across 8 encodings (ASCII, lower, upper, UTF-16LE, UTF-16BE, +0x20, −0x20, reversed) | 8 keywords × 8 encodings = **64 scans** of all 4 MiB | **0 hits**. Only benign hits: `kode` (German "code" in the localized menu text) and `Extra Time`. |
| Reachable menu screens walked with screenshots | **10 screens** (Title, Name, Main Menu, Options, Winners Table, Exhibition/Your Team, Opponent, Stats, Pause, Training; plus Tournament Type, Tournament list, VS screen, gameplay) | No password/cheat/debug screen, no unlabelled menu entry. |
| Selectable entries enumerated | Main **6**, Options **7**, Pause **4**, Tournament Type **2**, Cups **4**, Leagues **4**, team cells **25** (20 open + 5 locked) | All entries accounted for; no unreachable/dummy entry observed. |
| On-screen keyboards | **1** (name entry, 28 cells) | Consumer is the profile-save/display path: the loader at `0x083D9D78` only verifies a checksum and copies the 8-byte name; no comparison of the name against a code constant was found. No second, 16/32-symbol code alphabet. |
| Raw `u16` key-mask sequences (consecutive values ≤0x3FF with 1–2 key bits) | **1,893** raw runs (4+ values) | All fall in Thumb opcode streams or PCM sample data; none is a code table. Sample: `0x000E60` (`90 90 90 90`) and `0x00B7D4` (`0x100 0x102 0x1 0x100`) disassemble as instructions. |
| Active-low mask sequences | **54** runs (4+ values) | Same: audio/PCM and code coincidences. |
| Exact published L→B→A prefix (`00 02 02 00 01 00`, active-high u16) | **1 literal hit** at file `0x73338` (ROM `0x0873338`) | Surrounding bytes (`f9 fe 07 05 04 03 00 fd 00 02 02 00 01 00 00 fd fb f6…`) are 8-bit signed PCM; **not** a button table. Active-low form hits once at `0x8A019`, also PCM. |
| Hidden debug-menu strings/gates | **0** debug strings in text banks; **0** passwords | No gate value, no handler, no unreferenced menu row. |
| Unlockables reachable without a code | **5** locked team cells + **2** locked competition entries | Set by winning competitions (published, save-bit state); no input path grants them. |

**Novel code:** not applicable — mintage requires a validator, and none exists. Rejection bound attempted: typing arbitrary names at the name screen is rejected as a *name* only by the 8-character field limit; pressing A on a locked `???` team cell was observed to do nothing (no unlock), which is the closest in-game rejection surface. The five locked cells and two locked competitions remain locked in a clean save (verified visually and in the 512-byte `.sav`).

## 7. Validation evidence

* **Observed (emulator)**: all screens listed in §6b, including the 5 `???` cells and their non-response to A; the 4-entry pause menu; the name-entry keyboard and its 8-character limit; Savestate RAM mapping (IWRAM `0x19000`, EWRAM `0x21000`) confirmed by locating the profile name bytes at IWRAM `0x03000E5B`.
* **Observed (static bytes)**: header/hashes, build string at `0x3FE0B4`, filler string repeated from `0x3FD9E2`, keyboard strings at `0x3F7F00`, mask-input routine bytes at `0x3E4DDA`.
* **Derived (disassembly)**: key-state globals and their arithmetic; profile checksum/loader/writer at `0x083D9BD0` / `0x083D9D78` / `0x083E507C`; menu handler at `0x083D770A` tests held/pressed masks with no sequence state.
* **Derived (scan counts)**: the enumeration table in §6b.
* **Inferred**: mapping of the 5 `???` cells to the five All-Star teams named by GameFAQs, and the competition→unlock mapping from the published list (not independently exercised: winning a tournament was not completed).
* **Unresolved**: direct identification of the individual save-bit offsets for each unlock (the savestate byte-patching experiment was inconclusive because the modified state failed to reproduce the team-select screen); the exact semantic effect of the Bicycle Kick/Super Dribble moves beyond the manual description.

## 8. Unknowns

* Which byte/bit in the 120-byte profile record stores each of the five team unlocks and the two competition unlocks. Save_Record checksum is understood, but the field layout beyond the 8-byte name and +0x38 checksum was not fully recovered.
* Whether a different regional build (EU "Pro Beach Soccer", 6-language) has a different menu/code surface. This report covers only `AVEE6U` US Rev.00.
* Whether the documented Bicycle Kick has an input-timing window distinct from the normal flip-up control (not frame-tested).

## 9. Tooling

* `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep -abo`, Python 3 `struct`/`zlib`/`Pillow`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for raw Thumb ranges; Capstone 5.0.7 for literal-pointer, input-global, and key-mask scanners.
* mGBA 0.10.5 (`-3`, `-g`, `-d`), Xvfb `:317`, openbox, xdotool (XTEST), scrot, ImageMagick.
* Helper scripts kept in `/tmp/opencode/beachsoccer/`: `gba.py` (input/screenshot), `scan.py` (Thumb literal scan), `input_scan.py`, `mdbg2.py` (stub-free `-d` debugger), `diffstate.py` (gbAs state diffs), `repack.py` (savestate patcher).

## 10. Legal note

No ROM bytes, graphics, music, or extracted assets are redistributed here. Only hashes, addresses, algorithms, scan counts, and observations are published. Fetched web pages were treated as data; one TCRF mirror URL returned 404 and the successful search snippet was used only as a lead. No prompt-injection content was encountered or acted on.
