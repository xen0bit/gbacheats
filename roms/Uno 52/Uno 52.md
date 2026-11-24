# Uno 52 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Uno 52/Uno 52.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `UNO 52` (offset `0xA0`) |
| Game code | `BU5E` (`0xAC`); maker `20` (`0xB0`); `file(1)` prints `BU5E20` |
| Version | `0x00` (`0xBC`); complement `0x65` (`0xBD`); header checksum `0x0000` (`0xBE`) |
| Fixed byte | `0x96` at `0xB2` — normal |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, no scene-patch cracktro) |
| MD5 | `de44e3ae64659aba9824d0047c381981` |
| SHA-1 | `cfff9dd74be1d46f6787fe0403f2dea633481617` |
| SHA-256 | `2350420c3f83982dac2684d84cbc03a073ea2d8fcb319ab0b54ed9f2d1141b08` |
| Developer strings | `uno_52_ai.th.cpp`, `uno_52_game_state.th.cpp`, `uno_52_interface.th.cpp` at `0x0803BD2C`, `0x0803BF24`, `0x0803C0D4` (assert file names, not debug menus) |

The 0x0000 header checksum plus a non-`~version` complement byte is a rebuilt-header
artifact, not a cheat-enabling patch (§16.1). First 4 KiB is ordinary ARM crt0.

## 2. Executive summary

**Finding: bounded negative.** *Uno 52* has **no in-game/developer-intended cheat
system**: no password screen, no passcode validator, no alphabet-driven code
format, no hard-coded code table, no button-code sequence matcher, no hidden/
debug menu, and no save-bit unlockables. The only 38-symbol alphabet in the image
is the **name-entry keyboard** (`0x0803BCE0`), and all five references to it are
name-entry rendering/selection code. The only 4-key “button code” surface is the
documented in-game control set (L, R, Select, Start), which the game itself lists
on its Controls screen. Everything reachable from a 0-byte save is available on
a first run: all four Special Modes, all six Challenge entries, all 15
backgrounds, four music tracks, three difficulties and 20 player icons. The five
`######` strings near `0x080404F0` are untranslated placeholders in the French,
Italian, German and Spanish string banks — not locked or hidden content.

No novel code could be minted because no validator exists to mint *for*. The
negative is bounded by counts in **§6b**.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy mgba -3 "Uno 52.gba"` under
  `Xvfb :318` + openbox. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrows. Key holds 0.05–0.15 s; longer holds
  double-step the menus (§16.2).
* Boot path: Health warning → Mattel → copyright → UNO 52 title (`PRESS START`)
  → Main Menu (Quick Play / Custom Game / Special Modes / Options / Help).
* Save a state on the title screen (`Shift+F1`); plain `F1` reloads it exactly
  (verified by identical PNG MD5 `9ea3a7633041…`). All controlled combo tests
  used this reload.
* No code was entered because no code-entry surface exists. Combinations tested
  are listed in §6b.
* GDB stub: `mgba -g` was tried on default 2345 and `-C gdb.port=2401`; no socket
  was opened by this build, so RAM evidence uses mGBA savestate `gbAs`-chunk
  diffs (§16.13, script `ssdiff.py`) instead.

## 4. Address map

| Address (ROM) | Meaning |
|---|---|
| `0x08000000` | ARM entry branch; crt0 copies to IWRAM |
| `0x0800C93C`–`0x0800CB14` | Name-entry UI: 14-column cursor into alphabet, glyph draw, buffer write |
| `0x08027E40`–`0x08027F98` | Input library: key mask init `{1,2,4,8,0x100,0x200}` for A,B,Start,Select,R,L; D-pad `{0x10,0x20,0x40,0x80}` |
| `0x080278A4` | `KEYINPUT` read (`0x04000130`), only literal occurrence in ROM |
| `0x08027F4C` | `keyHeld(mask)` — reads global at `0x03005040` |
| `0x08027F68` | `getKeys()` — returns held mask |
| `0x08027F2C` | `keyDown(index, repeat)` |
| `0x08027F98` | `keyUp()` |
| `0x0803BCE0` | **Only alphabet**: `ABCDEFGHIJKLMNOPQRSTUVWXYZ'-0123456789` + `08 20 0A 20` control bytes (38 bytes) |
| `0x0803BC24` | `%d/%d` format; `0x0803BD2C`/`0x0803BF24`/`0x0803C0D4` assert file names |
| `0x0803DD88`–`0x0803DDC0` | Background-name pointer table, 15 entries: Spheres … Blocks |
| `0x0803DDC4`–`0x0803DDD0` | Music-track pointer table, 4 entries: Relax, Voyage, Wonder, Tense |
| `0x0803DDD4`–`0x0803DDDC` | Difficulty pointer table: Easy, Normal, Hard |
| `0x0803E408` | French copy of main string-pointer table (`Blocks` → `######`, `Yes`/`No` → `######`) |
| `0x08040934`–`0x08040CF4` | 60 AI first names (not codes) |
| `0x03005040` | IWRAM global: active-high key mask |
| Save | No SRAM/Flash/EEPROM access code found; `Uno 52.sav` stayed **0 bytes** through all menus and a live game |

## 5. Algorithm

No password algorithm exists. The recovered input model is:

```
held = ~(KEYINPUT) & 0x3FF          # active-high, read at 0x080278A4
A=1 B=2 Select=4 Start=8 Right=0x10 Left=0x20 Up=0x40 Down=0x80 R=0x100 L=0x200
keyDown(i, 10) / keyHeld(10) / getKeys() / keyUp() are the only consumers.
```

Every game-side call site (71 `keyDown`, 21 `keyHeld`, 21 `getKeys`, 20 `keyUp`)
uses either a **single key index 0–5** or the mask `0x0A` (B+Select, a generic
“cancel”). A representative handler at `0x0800AC50` is `keyHeld → getKeys →
switch(key)` with cases 1/2 — cursor movement, not a sequence matcher. No call
site stores a key history, compares a multi-key mask against a table, or writes
a “cheat unlocked” flag.

The name-entry field at `0x0800C93C` indexes the 38-byte alphabet with
`x + 14*y` and writes glyph indices into a buffer at `+0x20`; there is no
`strcmp`/`memcmp` against that buffer and no later read outside the entry
handler (§16.2b). It is a player label, not a password.

## 6. Tables

* **Alphabet (only one):** `0x0803BCE0` =
  `41 42 43 … 5A 27 2D 30 31 … 39 08 20 0A 20`; 38 bytes, 14 per row on screen.
  Five literal pointers: `0x0800C9C4`, `0x0800CB04`, `0x0800CDB8`, `0x0800CFB8`,
  `0x0800D054` — all inside name-entry code.
* **Backgrounds (15):** Spheres, Wings, Cards, Sunshine, Falling, Spill,
  Marching, Oval, Suits, Stars, Royal, Cubes, Shards, Squares, Blocks
  (`0x0803DD88`…). All selectable on a first run; `######` strings in other
  language banks are untranslated slots, not a 16th hidden theme.
* **Music (4):** Relax, Voyage, Wonder, Tense. **Difficulty (3):** Easy, Normal,
  Hard. **Icons (20):** 4×5 grid, all selectable.
* **Special Modes (4):** Challenge, Endurance, Timed, Solitaire — all present
  and selectable with a 0-byte save. Challenge contains 5 levels + Random.
* **Documented controls (Controls 2/2):** L=Challenge Forgetting UNO,
  R=Call UNO, Select=Challenge Wild Draw 4, Start=Pause; Controls 1/2 =
  D-pad/A/B. No other button is assigned anywhere in the UI strings.

## 6b. Enumeration

**Space definition: zero code-space.** There is no alphabet/code format, no
validator, no lookup table of accepted codes and no button sequence. The
enumerated *reachable* space is the UI set below; the counts that bound the
negative are:

| Search | Space checked | Hits relevant to cheats |
|---|---|---|
| `strings -t x -n 4` | 37,858 strings | 0 for `cheat/debug/secret/password/unlock/hidden` in EN/FR/IT/DE/ES; only 5× “Special Modes” at `0x0803FD94` |
| Password-shaped NUL strings `[A-Z0-9!?-]{4,16}\0` | 353 occurrences | 0 code tables; first 33 are instruction bytes, remainder are 60 AI first names at `0x08040934` |
| 38-byte alphabets | entire 4 MiB | 1 (`0x0803BCE0`), 5 pointers, all name-entry |
| Konami prefix as u16 masks, forward + reversed | entire 4 MiB | 0 |
| Konami prefix as low-byte masks, forward + reversed | entire 4 MiB | 0 |
| 4 consecutive u16 multi-key masks | 59,989 runs | 0 with code-table structure (all are incidental data, e.g. `0x2F2` fill in graphics/audio banks) |
| Input API call sites | 71+21+21+20 = 133 | 0 sequence comparators / history buffers |
| SRAM/Flash/EEPROM literals | `0x0E005555`, `0x0E002AAA`, `0x04000120/124` | 0 each; `.sav` = 0 bytes throughout |
| Hidden theme slots | 15 backgrounds + 4 music + 3 difficulty | 0; `######` = translation placeholders |
| Controlled button combos on title (savestate reload) | 22 combinations | 0 hidden screens; every Start-containing combo advanced to Main Menu via documented Start, every non-Start combo left the title unchanged |
| Button combos in-game | 22 combinations | 0 hidden screens; Start combos opened the documented Pause menu |

**Novel code:** none generated — there is no validator to mint against, so a
“code absent from every published list” is not definable for this SKU. This is
reported as a bounded negative, not an omission.

**Rejection bounds:** likewise not applicable — no code format means no
checksum/reserved-bit/range check exists to exercise. Instead, the bounds are
the exhaustive UI/table counts above: every selector was cycled through its
full pointer table (15/4/3/20/6 entries) and every combo class was pressed
without producing an undocumented screen or RAM flag.

**Screen walk (screenshots in `/tmp/uno52/`):** Health warning (`s0`),
Mattel logo, copyright (`s1`), title (`s2`), Main Menu (`s3`), Name Entry
(`s4`), Icon Selection (`s9`), Special Modes (`s6`), Challenge Mode
(`sm_challenge*`; 6 entries wrapped), Theme (`t_theme3`; 15 backgrounds cycled),
Quick Play setup (`quick2`), live game (`game1`), Pause (`ingame_combo01`),
Options (`scr_options2`), Help (`scr_help2`), How to Play 1/5
(`back_special2` predecessor), Controls 1/2 and 2/2 (`scr_controls2`,
`scr_controls_p2`), Custom Game / Player Setup (`scr_help`), plus Credits entry
in the Options string table. All other rows of each menu resolve to the same
handlers; no unlabelled index exists (the Special Modes ring has exactly 4
entries, Help exactly 4, Options exactly 3).

**RAM evidence:** mGBA `gbAs` state diffs (`ssdiff.py`) between a saved state and
the same state after `L+R+A+B` on Icon Selection changed ~1.8 KiB of IWRAM timer
and animation scratch but produced **no new screen and no new persistent flag**
(`after_combo.png` = Icon Selection). The `.sav` file remains 0 bytes after all
tests, confirming there is no save-bit flag to unlock.

**Web recon limitation:** automated web recon was unavailable — `websearch`
returned no results for six queries; DuckDuckGo served a CAPTCHA; 3rd party cheat indexes
returned HTTP 403; Google blocked automated access. No published code list was
obtained. This does not affect the static result: every code-table shape that
such a list could point to was searched for directly in the image (above) and
found absent.

## 7. Validation evidence

* **Observed** — screenshots listed in §6b; 0-byte `.sav`; identical PNG hash
  before/after `F1` reload; savestate RAM diffs; no GDB socket from `mgba -g`.
* **Derived** — single-alphabet reference count (5); pointer-table lengths
  (15/4/3); input-API caller counts (133) and the absence of history buffers;
  zero literals for the three save technologies; `######` language-bank
  alignment at 0x648-byte strides.
* **Inferred** — that `0x080278A4` is the unique `KEYINPUT` consumer (one
  literal occurrence plus one BL) and that the button mapping in §5 is
  authoritative (corroborated by the Controls screen, so high confidence).

## 8. Unknowns

* Web-published cheats could not be retrieved (network blocks); if a list
  exists for a *different* SKU it would not apply to this `BU5E` image (§16.11).
* A debug build or a future patched release could contain code absent here;
  this report is bound to SHA-256 `2350420c…`.
* The 60 AI names and 20 icons were not exhaustively compared against a
  promotional list; none is a code surface (no buffer consumer outside UI).

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for the input library and name-entry code.
* Python scripts in `/tmp/uno52/`: `scan.py`, `scan2.py` (literal/BL/
  mask scans), `keys.py`, `combos.py`, `combos_reset.py`, `cycle_theme.py`,
  `ssdiff.py` (PNG `gbAs` zlib extraction + IWRAM/EWRAM diff).
* mGBA 0.10.5 under Xvfb `:318`, `scrot`, ImageMagick `montage`/`convert`.
* No ROM or copyrighted assets are redistributed here; only addresses, counts,
  hashes and analysis scripts are published.

## 10. Legal note

Analysis only; the ROM and extracted graphics/text are not redistributed.
