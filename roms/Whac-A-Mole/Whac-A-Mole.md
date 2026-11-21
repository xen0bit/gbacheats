# Whac-A-Mole (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Whac-A-Mole/Whac-A-Mole.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `Whac-A-Mole` |
| Game code / maker | `BWEE` / `52` (Activision Value) |
| Version / fixed / complement / checksum | `0x00` / `0x96` / `0x1C` / `0x0000` |
| Entry word | `0xEA00003E` → `0x08000100` (stock crt0, no cracktro/trainer) |
| MD5 | `6b611dc9657c75d06808c198c4b51aac` |
| SHA-1 | `b5be37328187db934a1f7bfb158ceb59029209fb` |
| SHA-256 | `566f54787f9e5332e8ff4a4efd3085e98d217015e68eb5ee0f316a56875d10ac` |
| Provenance | DC Studios / Chasma, Activision Value, 2005 (NTSC-U) |

## 2. Executive summary

**No in-game/developer-intended cheat system exists in this ROM.** There is no password
screen, no button-code sequence, no hidden/debug menu, no unlockable flag with a
reachable setter, and no validator of any kind. The game is a save-game title: Arcade
progress is stored in a 512-byte EEPROM with three slots (`Create Game` / `Continue
Game`), and the only text-entry surface is a save-slot **name** field whose consumer is
save-data storage, not a comparison against a constant.

The strongest positive-looking lead — a 24-entry ASCII string bank at `0x0849A3C4`
containing `Select Style` / `Modern` / `Classic`, `Select Mode` / `Survival` /
`Challenge`, `Level Choice`, `Progress`, `Next Level` and similar — is **dead data**:
Ghidra reports zero references to all 24 strings, a full 8 MiB scan finds zero 32-bit
pointers into the whole `0x0849xxxx` page, and a Thumb PC-relative-literal scan finds
zero loads into it. None of those labels is ever drawn by the reachable UI, which uses
a different string set (`FX Volume`, `Music Volume`, `View Credits`, `Rounds`,
`Difficulty`, `Game Type`, …). It is an unreferenced leftover from another build of
the engine, not a hidden feature.

Web recon (Cheat Happens, GameFAQs, LaunchBox, GamesDatabase, GameSpot, Project Cheat
Codes, Fandom) found **no published codes at all** for this SKU; Cheat Happens states
explicitly that no cheats exist. Per §16.11 the title/platform match was checked against
the actual header code (`BWEE`) and the ROM bytes, so a "wrong SKU" published list is
not hiding here.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `mgba -3 game.gba`.
- Keymap (mGBA SDL default): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Hold 60–150 ms; menu cursors reset to the first item on return.
- Work copy used for all dynamic tests: `/tmp/opencode/whacamole/game.gba` (identical
  hash). The ROM folder was never written by the emulator.
- Screen path: title (`PRESS START`) → Start → Main Menu → [Arcade | Puzzle |
  Quick Play | Settings]. Arcade → [New Game → Create Game (3 slots) → Name entry |
  Continue → Continue Game (3 slots)]. Puzzle → [Peg Puzzle | Tic Tac Toe].
  Quick Play → [Rounds, Difficulty, Game Type]. Settings → [FX Volume, Music Volume,
  View Credits].
- Screenshots for every transition are in `/tmp/opencode/whacamole/` (`menu1.png`,
  `arcade1.png`, `continue1.png`, `puzzle1.png`, `quickplay_menu.png`, `settings1.png`,
  `m_slot.png` (name entry), `qp_*`, `gtL_montage.png`, …).

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | ARM entry, stock crt0 | Observed (header + disassembly) |
| `0x08014860` | Main game loop / screen state machine (`FUN_08014860`) | Derived (Ghidra) |
| `0x08018230` | Debug print wrapper, prints `"Hello World!\n"` at `0x08018338` | Derived (Ghidra xref + decompile) |
| `0x08017A90` | `"level%d"` used by level loader `FUN_08017768` ← `FUN_0801A1A0` | Derived |
| `0x080185E0` | `"Patate"` (single debug string, one xref at `0x8018448`) | Derived |
| `0x0801A40`–`0x0801A70` | Default high-score names `Braeden`, `Bwian`, `AmyLee`, `Laosativ`, `Yanos`, seeded by `FUN_0801A79A` when save field `+0x10 == 0` | Derived |
| `0x08017E9C`–`0x08017F28` | Resource filenames `TxtPackage_All.bin`, `XMusic.bin`, `sFx.bin`, `sprites`, `menu1.fnt`, `menu2.fnt`, `menu_high.fnt`, `hud1..4.fnt` | Observed |
| `0x0849A1E0`–`0x0849A2FC` | Integer lookup tables (0..0x46, then 0xC8) | Observed |
| `0x0849A300`–`0x0849A3BC` | 24-entry u32 offset table (offsets into `0x0849A3C4`) | Observed |
| `0x0849A3C4`–`0x0849A4F0` | 24 NUL-terminated ASCII strings (dead/unreferenced) | Observed + Derived |
| `0x0849A000`–`0x0849A1DF` | Tile/font data (mostly `0x0F` indices), same dead region | Observed |
| Save | 512-byte EEPROM, 3 slots (`game.sav` created in work dir) | Observed |

## 5. Algorithm

Not applicable — no password, checksum, validator, code alphabet, or input-mask
sequence exists. The only algorithmic structure of interest is the dead offset table:

```
bank_base  = 0x0849A3C4
offsets[i] = u32 at 0x0849A300 + 4*i        (i = 0..23)
string[i]  = C-string at bank_base + offsets[i]
```

This resolves cleanly to the 24 labels listed in §6, but the table has **no consumers**,
so it is not a code system.

## 6. Tables

### 6.1 Dead string bank (unreachable)

| # | Offset | String | # | Offset | String |
|---:|---:|---|---:|---:|---|
| 0 | 0x000 | Play | 12 | 0x098 | Challenge |
| 1 | 0x008 | Game Settings | 13 | 0x0A4 | Level Choice |
| 2 | 0x018 | FX Volume | 14 | 0x0B4 | Progress |
| 3 | 0x024 | Sound Volume | 15 | 0x0C0 | Play |
| 4 | 0x034 | Credits | 16 | 0x0C8 | Level Completed |
| 5 | 0x040 | Select Style | 17 | 0x0DC | Game Over |
| 6 | 0x050 | Modern | 18 | 0x0E8 | Retry |
| 7 | 0x058 | Classic | 19 | 0x0F0 | Next Level |
| 8 | 0x064 | Select Mode | 20 | 0x0FC | Back To Menu |
| 9 | 0x074 | Survival | 21 | 0x10C | Game Paused |
| 10 | 0x080 | Challenge | 22 | 0x11C | Resume |
| 11 | 0x08C | Survival | 23 | 0x124 | Quit |

### 6.2 Live UI inventory (all reachable screens)

| Screen | Items / bounds |
|---|---|
| Title | `PRESS START` |
| Main Menu | Arcade, Puzzle, Quick Play, Settings (4) |
| Arcade | New Game, Continue (2) |
| Arcade → New Game | Create Game, 3 free save slots → name entry (A–Z, a–z, space, ⌫, done) |
| Arcade → Continue | Continue Game, 3 free save slots |
| Puzzle Mode | Peg Puzzle, Tic Tac Toe (2) |
| Quick Play | Rounds **1–5**, Difficulty **1–5**, Game Type **{Arcade, Survival}** |
| Settings | FX Volume, Music Volume, View Credits (3) |

## 6b. Enumeration

**The system has an empty code space: no password alphabet, no code length, no
validator, no flag written by code input, and no button sequence.** Per §0.2 the
negative is bounded as follows:

* **String/table space checked.** All **432** Ghidra-defined strings in the 8 MiB image
  were searched for `password`, `cheat`, `secret`, `debug`, `unlock`, `level select`,
  `code`, `enter`, `master`, `god`, `invincible`, `test`: **0 live hits**. The only
  cheat-like vocabulary is the 24-string dead bank at `0x0849A3C4` (`Challenge`,
  `Classic`, `Level Choice`, `Next Level`, …).
* **Dead-bank reachability counts.** 24/24 strings have **0** Ghidra xrefs; the offset
  table `0x0849A300`, its base, the string-bank base and the integer tables all have
  **0** 32-bit pointers anywhere in the 8 MiB (word-aligned full-file scan), and **0**
  Thumb `LDR Rd,[PC,#imm]` literals resolve into `0x0849A000–0x0849AFFF`. Coverage
  control: the same methods find xrefs for `0x08017EDC` (menu1.fnt), `0x08017A90`
  (level%d) and `0x08018338` (Hello World!), so zero here is a real negative, not a
  raw-binary/Thumb analysis failure.
* **Input-mask space checked.** The ROM contains **0** occurrences of the literal
  `0x04000130` (KEYINPUT) and **0** of `0x04000132` (KEYCNT), i.e. no direct key-register
  comparison site to anchor a button code. A full sweep of the first 3 MiB for runs of
  ≥4 consecutive 16-bit values drawn from the GBA single/2-button mask set
  (`0x001..0x300`, popcount ≤3) returned 2,412 runs, all inside graphics/palette/sound
  tables (e.g. the `0x0200…0x0300` palette ramps at `0x08038Axx`) with no code xref and
  no progress-index structure — i.e. **0 candidate button-code tables**.
* **Screen space walked.** 8 top-level/sub screens and every item on them were entered
  (see §6.2); no unlabelled menu slot, no level-select, no debug page, and no extra
  Quick Play value appeared.
* **Bounds proven by in-game rejection (the equivalent of "reject a value the format
  cannot express").** From the default Rounds=1, eight Right presses stop at **5**
  (`qp_rounds_right.png`); four Left presses stop at **1**. Difficulty stops at **5**
  (`qp_diff_right.png`) and **1**. Game Type has exactly two values: Right from Arcade
  yields Survival and further Right presses are rejected/stay (`qp_gt_min.png`,
  `gtL_montage.png`); Left from Survival yields Arcade and further Left is rejected.
  These are the only bounded selectors in the game; there is no code field to
  over-range.
* **Novel code:** none can be minted, because there is no encoder/validator to invert.
  This is a proven empty-space result, not an untested one.

## 7. Validation evidence

* **Observed** — emulator screenshots for all screens listed in §6.2; 512-byte EEPROM
  save created after slot creation; all published-code searches returned no candidates;
  ROM hashes and header fields read directly from the file.
* **Derived** — Ghidra decompilation: `FUN_08014860` main loop, `FUN_08018230` debug
  print, `FUN_08017768` level loader, `FUN_0801A79A` score-table seeding; xref and
  pointer counts for the dead bank; no `0x04000130` literal.
* **Inferred** — the dead bank is an artifact of a different/unused build of the same
  engine (its labels resemble an earlier menu design). Strongly supported by zero
  references plus the live UI using a different string set, but not provable from the
  bytes alone.

## 8. Unknowns

* The exact origin of the `0x0849Axxx` dead bank (discarded prototype UI vs. shared
  engine resource) is not determinable from this ROM.
* The two 8-bit volume sliders were not swept to their numeric endpoints; they are not
  cheat-related and do not affect the negative.
* In-game gameplay was entered only far enough to confirm slot creation and name entry;
  no 7-world completion was performed, so a hypothetical *save-bit* unlock that requires
  clearing the game was not exercised. No `unlock`/`unlocked` string or setter call
  chain was found, so no such feature is positively indicated.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, Python `struct`
  scans (header, literal pointers, Thumb PC-relative loads, key-mask runs).
* REA MCP + Ghidra 12.1.4 raw-binary ARM/Thumb import at base `0x08000000`:
  `open_binary`, `search_strings`, `list_strings`, `xrefs`, `analyze_function`.
  Session closed with `close_binary` at end of work.
* `arm-none-eabi-objdump -M force-thumb` spot checks; Capstone available.
* mGBA 0.10.5 under Xvfb `:317` + openbox; `xdotool` XTEST input, `scrot` captures,
  ImageMagick crops/montages; `game.sav`, `game.ss1`, `game.ss2` kept in the /tmp work
  directory (never in the ROM folder).
* Helper scripts: `/tmp/opencode/whacamole/ui.py` (key/screenshot driver),
  `ssdiff.py` (savestate `gbAs` zlib diff).

**Legal note:** no ROM image, graphics, audio, or game text is redistributed here; only
hashes, addresses, counts, and observations are published.
