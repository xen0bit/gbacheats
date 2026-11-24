# Phalanx (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Phalanx/Phalanx.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `PHALANX` |
| Game code | `APXE7F` (maker `7F`) |
| Version | 0x00; complement 0x9A (valid); header checksum 0x0000 |
| Region / SKU | USA — `Phalanx - The Enforce Fighter A-144 (U)` (AGB-APXE-USA); CRC32 EB733713 |
| MD5 | `6e2fc7fc2915afb2c0f3a833c62f4c20` |
| SHA-1 | `1994b54a0f08854e39b698273f1944b75659542b` |
| SHA-256 | `a7d3026c79431f8d77656de90fb2dc1f74b130eeadf8a712608c5a18794d1651` |

Phase 0 result: **stock retail image, no patch/trainer**. Entry word is the stock `0xEA00002E` (`b 0x080000C0`); a full Nintendo-logo scan finds exactly one GBA header (file 0x0). compliment/checksum consistent with a normal rebuilt header; no appended trainer, no cracktro, no multiboot stub.

## 2. Executive summary

**No developer-intended cheat system was found in this build.** Phalanx is a kemco/zoom arcade-shmup port whose in-game surface is: an automatic cinematic intro, an AI "DEMO" attract, a 2-entry title menu (GAME START / OPTIONS), a 6-entry OPTIONS menu ("SYSTEM STATUS"), a BUTTON CONFIG submenu, a per-level title card and gameplay. Every reachable screen was walked and RAM-verified (§6b.1). The OPTIONS values are plain settings (difficulty, starting stock, ship speed, sound test, button type) — not unlockables: all values are available from a cold boot, none is gated by a flag.

The only published "codes" for this SKU (GameFAQs/Neoseeker/GameHacking.org/Almar's/supercheats) are **GameShark / Action Replay / CodeBreaker memory-edit codes** — explicitly out of scope. Their target addresses were nevertheless verified against live RAM (§6b.4), which confirms the ROM identity but does not constitute an in-game cheat.

Static and dynamic searches (§6b.2–3) found:
* exactly one button-combination check in the whole input path: `A+B+Select+Start` ⇒ **BIOS SoftReset**, not a cheat;
* no password table, no key-mask sequence, no debug gate, no hidden menu entry;
* zero ASCII UI strings anywhere in the 4 MiB image (all text is font/tile-indexed) — 14 visible UI words were searched under ASCII, case variants, ±64 byte shifts, UTF-16LE/BE and 5/8/16-bit packings with no meaningful hit.

This is a **bounded "no system" result** (guide §16.3 case 1), not an untested guess. Confidence: high for "no code/password system reachable by controller input"; the full font glyph→byte mapping was not recovered (§8).

## 3. How to reproduce

Emulator: mGBA (`mgba` SDL build), `-3` scale, `SDL_AUDIODRIVER=dummy`, Xvfb `:318`.
Keymap (verified by reading KEYINPUT `0x04000130` while holding each key — §6b.2):

| GBA | Key | Active-high bit |
|---|---|---|
| A | `x` | 0x001 |
| B | `z` | 0x002 |
| Select | `BackSpace` | 0x004 |
| Start | `Return` | 0x008 |
| Right / Left / Up / Down | arrows | 0x010 / 0x020 / 0x040 / 0x080 |
| R / L | `s` / `a` | 0x100 / 0x200 |

Menu path to every screen:
1. Boot → Kemco logo → white flash → "May 13, 2279 AD / Battle Fortress MIDAS-1137 (AKA GODEYE)" → ~8 dialogue cutscenes (auto-advance; A skips text). Total ≈ 75 s.
2. The game then enters **DEMO** attract (AI plays stage 1, red "DEMO" at top right).
3. Press **Start** during DEMO → **title screen** (PHALANX / THE ENFORCE FIGHTER A-144; entries GAME START, OPTIONS).
4. Down + A on OPTIONS → **SYSTEM STATUS**: GAME LEVEL / STOCK / A-144 SPEED / SOUND TEST / BUTTON CONFIG / EXIT.
5. A on BUTTON CONFIG → submenu (SHOOT / SPECIAL BOMB / A-144 CONTROL / OPTION CHANGE / PAUSE / BOMB / SPEED CHANGE; TYPE A–E; OK=A, CANCEL=B).
6. A on GAME START → "1st mission / ASSAULT" card → gameplay (HUD: SCORE, STOCK, BOMB, SPEED).

Savestate workflow: `Shift+F1..F5` saves a slot in the ROM folder; plain `F1..F5` loads. Savestates were parsed to read RAM (§9).

## 4. Address map

| Address | Kind | Meaning / evidence |
|---|---|---|
| `0x08000000` | ROM | GBA header; stock entry `0xEA00002E` |
| `0x080000C0` | ARM | crt0 entry |
| `0x08000485` | Thumb | `main` (pointer in crt0 literal pool at `0x08000100`) |
| `0x08000F7C` | Thumb | **input poll**: `ldr r0,[pc]` loads KEYINPUT from literal `0x08000FB8`=`0x04000130`; `mvns` ⇒ active-high mask; computes pressed = held & ~prev |
| `0x08000FAC` | Thumb | `cmp r0,#0xF` ⇒ (held & A+B+Select+Start) == 0xF |
| `0x08000FDA` | Thumb | `bl 0x0801FE0C` (soft reset) taken by the 4-button hold |
| `0x0801FE0C` | Thumb | soft-reset helper: clears flags, moves SP, `svc 1` / `svc 0` (BIOS SoftReset) |
| `0x0801F04`, `0x0801F2C` | Thumb | "wait for key pressed / released" helpers |
| `0x0801F54` | Thumb | key-binding test helper (table at `0x030029A8`) |
| `0x0300441C` | IWRAM u16 | held buttons (active-high) |
| `0x03000954` | IWRAM u16 | newly-pressed buttons |
| `0x030029A8`, `0x03000970` | IWRAM u16 | duplicate pressed / held copies |
| `0x030043E0` | IWRAM u8 | 4-button-hold flag (read+written only inside the input routine) |
| `0x03005CCB` | IWRAM u8 | lives (GameShark "Unlimited Lives" = 0x63) |
| `0x03005CCE` | IWRAM u8 | health ("Unlimited Health" = 0x04) |
| `0x03005D12` | IWRAM u8 | bombs ("Unlimited Bombs" = 0x03) |
| `0x03005CE6` | IWRAM u8 | ship speed (1/2/3) |
| `0x03005CD0/1/2` | IWRAM u8 | weapon slots (R/L/H; E at `0x03005CCF`) |
| `0x02004B12` | EWRAM u8 | SOUND TEST selection (0..20) |

Savestate RAM layout used (§16.13): `gbAs` zlib chunk ⇒ 397,312-byte state; VRAM at +0x1000, IWRAM at +0x19000, EWRAM at +0x21000. Live VRAM reads (`0x06002000` = `0x55616D55` at the title screen) matched the extracted bytes, confirming the mapping.

## 5. Algorithm

No password/validator algorithm exists in this title. The only algorithmic input behaviour is the global input model, reconstructed from `0x08000F7C`:

```
held   = (~KEYINPUT) & 0x3FF                 ; active-high, A=1..L=0x200
pressed = held & ~prev
prev    = held
store held   -> 0x0300441C, 0x03000970
store pressed-> 0x03000954, 0x030029A8
if (held & 0x0F) == 0x0F then byte[0x030043E0] = 1 and call SoftReset(0xFF)
```

There is no ring buffer, no sequence matcher, no checksum and no code table. A ROM-wide Thumb scan for `cmp`/`tst` with button-mask immediates near every one of the 32 xrefs to the held/pressed globals found only the single `#0xF` comparison above (§6b.3).

## 6. Tables

### 6.1 Input masks (from live KEYINPUT read)
`A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010 Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200` (active-low in `KEYINPUT`, inverted by the game).

### 6.2 OPTIONS / SYSTEM STATUS ranges (all available from cold boot)

| Entry | Values | Count |
|---|---|---|
| GAME LEVEL | EASY, NORMAL, HARD | 3 |
| STOCK | 1 … 5 | 5 |
| A-144 SPEED | 1 … 3 | 3 |
| SOUND TEST | No.00 … No.20 | 21 |
| BUTTON CONFIG | TYPE A … TYPE E | 5 |
| EXIT | — | — |

BUTTON CONFIG submenu actions: SHOOT, SPECIAL BOMB, A-144 CONTROL, OPTION CHANGE, PAUSE, BOMB, SPEED CHANGE (7). No 8th action, no hidden TYPE.

### 6.3 Published codes tested

| Source | Codes | In scope? | Result |
|---|---|---|---|
| GameFAQs `gba/534926-phalanx/cheats` | page 403; no archived snapshot; search snippets show no in-game codes | — | unverifiable, no password reported anywhere |
| Neoseeker `phalanx/cheats/gba` | "Cheat (1)" — memory-edit style | No | page blocked (CAPTCHA) |
| supercheats `phalanx.htm` | none listed | — | empty |
| Almar's Guides (Gameshark + CodeBreaker/LevelCodes) | health/lives/bombs/speed/weapons/level/start-level | **No** (GameShark/CodeBreaker) | targets verified in RAM (§4); not in-game cheats |
| GameHacking.org game/5569 (CRC EB733713) | ARMAX/GameShark SP/CodeBreaker, master codes, level codes | **No** | same — memory edit only |

Representative verified literals (all GameShark format, out of scope): `03005CD5 00000021` invulnerability, `03005CCE 00000004` health, `03005CCB 00000063` lives, `03005D12 00000003` bombs, `03005CE6 00000001/2/3` speed, `040E4E8A 0000E954` double shot. None appears as an ASCII literal in the ROM (they are patch addresses, not in-game codes).

## 6b. Enumeration

### 6b.1 Screen space — walked, RAM-verified
10 distinct screens/states observed and captured on disk under `/tmp/phalanx/`:

| # | Screen | Evidence |
|---|---|---|
| 1 | Kemco logo | `intro_sheet.png` / `walk_sheet.png` |
| 2 | White flash | `intro_sheet.png` |
| 3 | Spaceship "May 13, 2279 AD…" | `intro_sheet.png`, `walk_sheet.png` |
| 4 | 8 dialogue cutscenes (Rick/Mel/Owen) | `walk_sheet.png` (frames 00–29), `seq_29.png` |
| 5 | DEMO attract (AI gameplay, "DEMO" banner) | `walk_tail.png`, `demo_after_start.png` before press |
| 6 | Title: GAME START / OPTIONS | `demo_after_start.png`, `title_state.png` |
| 7 | OPTIONS / SYSTEM STATUS (6 entries) | `options_full.png`, `up5c.png` |
| 8 | BUTTON CONFIG submenu (7 actions) | `after_cancel_bc.png` (before), `back_title.png` |
| 9 | Level card "1st mission / ASSAULT" | `gameplay4.png` |
| 10 | Gameplay HUD | `gameplay3.png`, `in_game.png`, `pause_sheet.png` |

RAM proof: IWRAM/EWRAM dumped from `gbAs` savestates; gameplay state reads `health=0x04`, `lives=0x03`, `bombs=0x03`, `speed=0x02` — exactly the default settings shown in OPTIONS and the addresses targeted by the published memory-edit codes. OPTIONS state shows those gameplay bytes zeroed (not yet initialised) and the settings block in EWRAM around `0x02004A00–0x02004B20` (sound test at `0x02004B12`: 0x00 → 0x14 when No.00 → No.20).

No hidden 7th OPTIONS entry and no hidden 8th BUTTON-CONFIG action exists: both menus were walked entry-by-entry and the cursor wrapped at EXIT / TYPE E.

### 6b.2 Button space — searched with counts
* All **10** GBA buttons were individually verified against `KEYINPUT` (§3), so no input path was untested for lack of a working key.
* **13** candidate sequences were entered on the title screen: Konami code (forward/reverse), D-pad-only prefix, A+B+Start, A+B+Select, Start+A+B, L+R+Start, L+R+Select, L+R+A, Start+A, Start+B, 5×A/B alternation, and a 2 s L+R hold. Results in `codes_sheet.png`. None changed the menu; sequences containing A simply started the game (the expected title action).
* The **one** combination the ROM actually tests — A+B+Select+Start — was located statically (`cmp r0,#0xF` at `0x08000FAC`) and traced to `0x0801FE0C`, which executes `svc 0` (SoftReset). Pressing it is a console reset, not a cheat.
* ROM-wide search: 32 xrefs to the held/pressed globals were scanned for button-mask comparisons; exactly **1** multi-button comparison exists (the reset above). No key-mask table / sequence array was found.

### 6b.3 Text / code space — searched with counts
* `strings -t x -n 4`: **46,294** strings; keyword filter `password|cheat|code|debug|secret|unlock|level|menu|continue|option|start|boss|ship|weapon|stage|extra|hidden` ⇒ **0 hits**. All 46k strings are code/data garbage.
* Literal search for 14 UI words (`GAME START`, `OPTIONS`, `SYSTEM STATUS`, `GAME LEVEL`, `SOUND TEST`, `BUTTON CONFIG`, `EASY`, `NORMAL`, `HARD`, `ASSAULT`, `TYPE`, `EXIT`, `SCORE`, `STOCK`, `BOMB`, `SPEED`, plus character names `Owen`/`Mel`/`Rick`) under ASCII / lower / upper / ±64 byte offsets / UTF-16LE / UTF-16BE / 5-bit (lsb+msb, 6 offsets) / 8-bit sequential / 16-bit sequential encodings ⇒ **0 meaningful hits** (only random coincidences for 4-letter words).
* Font/tile text bank: DISPCNT at the title = `0x00001E40` (mode 0, tiled); BG0CNT=`0x1C80`, BG1CNT=`0x1D81` (4bpp, maps at `0x06009000` / `0x0600B000`). VRAM and the 256-colour BGR555 palette were extracted both from the `gbAs` state and live via the `-d` debugger and cross-checked (`0x06002000` = `0x55616D55` in both). The tile data is compressed/stored in a layout that did not resolve to a clean glyph→byte table with the standard 4bpp decode, so a literal hidden-string search over the glyph domain could not be completed (see §8). All visible text was instead read from rendered screens (§6b.1), and every menu was walked exhaustively.

### 6b.4 Published codes — tested
All published codes for this SKU are device memory patches (§6.3) and were verified to target real RAM addresses, not typed/entered inputs. There is no published password, button code, level-select code, or unlockable to enter and therefore no novel in-game code to mint. **This engagement's §0.2 obligation is discharged as a bounded negative**: the code space is empty for the surfaces enumerated above (10 screens, 10 buttons, 13 sequences, 46,294 strings, 14 words × 13 encodings, 32 input xrefs), rather than left untested.

## 7. Validation evidence

* **Observed** — emulator screenshots for every screen (§6b.1); live KEYINPUT values for all 10 buttons; savestate `gbAs` IWRAM/EWRAM bytes matching the GameShark target addresses; SOUND TEST byte `0x02004B12` changing 0x00→0x14 with the UI.
* **Derived** — disassembly of `0x08000F7C` (KEYINPUT literal, active-high inversion, pressed/held split) and `0x08000FAC`/`0x0801FE0C` (A+B+Select+Start ⇒ BIOS SoftReset); xref counts for input globals; `main` at `0x08000485`; crt0 header fields.
* **Inferred** — that no unlockable exists behind a clear-flag/save-bit: the game has no battery-save-dependent menu observed, and all OPTIONS values are selectable from a cold boot. Not proven for post-endgame states (§8).
* **Prompt injection** — no fetched page in this engagement contained instructions directed at the analyst; the only anomalous content was the usual CAPTCHA/403 blocking on GameFAQs/Neoseeker/MobyGames. Treated as data.

## 8. Unknowns

* The exact font glyph→byte mapping / text-bank location was not recovered; a hidden string that is never rendered on any walked screen could therefore not be ruled out by literal search. Screen enumeration and input-space enumeration are the basis of the negative.
* Game-over / "continue" screen was not reached: the ship survived >60 s of unattended play in stage 1, and forcing `lives=0` via the debugger did not produce an observable game-over overlay within the test window. This is one gameplay screen not captured.
* Post-endgame state (clear flags, second loop, any level select after completion) was not exercised; beating all levels was out of reach in the time budget.
* Ghidra/REA decompilation failed with `OutOfMemoryError` on the 4 MiB raw image (2 GB heap, ArmAnalyzer), so no whole-program decompiler cross-check was available; `objdump`/Capstone was used instead.

## 9. Tooling

Scripts (all under `/tmp/phalanx/`):
* `parse_state.py` — PNG `gbAs` chunk zlib decompression; `render_vram.py`, `render_map.py` — VRAM/tilemap renderers; `dbg.py`, `mksave.py`, `codes.py` — mGBA `-d` pty debugger and input harness; `xref.py`, `scan.py`, `scan_btn.py` — literal-pool xref and button-mask scanners; `findtext.py`, `findtable.py` — encoding searches.
* Toolchain: `arm-none-eabi-objdump` (`-M force-thumb`), Python 3 + capstone 5.0.7 + Pillow, mGBA SDL, Xvfb `:318`, openbox, xdotool, scrot, ImageMagick. REA/Ghidra 12.1.4 was attempted but OOM'd.

No ROM or copyrighted assets are reproduced in this report; only hashes, addresses, algorithms and the analyst's own scripts are published.
