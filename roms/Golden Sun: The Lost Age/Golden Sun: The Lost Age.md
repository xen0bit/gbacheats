# Golden Sun: The Lost Age (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Golden Sun: The Lost Age.gba` |
| Size | 16,777,216 bytes (`0x01000000`, 16 MiB) |
| Header title | `GOLDEN_SUN_B` |
| Game code | `AGFE` (PAL/English), maker `01` (Nintendo) |
| Version / complement / checksum | `0x00` / `0x2E` / `0x0000` |
| Entry word | `0xEA000108` → `b 0x08000428` (stock Camelot crt0) |
| MD5 | `8efe8b2aaed97149e897570cd123ff6e` |
| SHA-1 | `b500663220cb9bf56b9f8e8c0c544f1d6fa3a824` |
| SHA-256 | `4199d82f845edf3e2e92f3783bca00190b5bc102d7c8aa339b951de280b1e6cc` |

**Embedded-header scan:** the 156-byte Nintendo logo occurs exactly once, at file `0x4`.
There is no second image, no appended trainer and no cracktro in the first 4 KiB. This is
the retail PAL image, unmodified. Header checksum `0x0000` is normal for this title
(the sibling `Golden Sun` (AGSE) also has `0x0000`; different size/hash/title, so no
shared-image relationship).

**Sibling comparison:** `roms/Golden Sun/Golden Sun.gba` is `0x800000` bytes, title
`Golden_Sun_A`, code `AGSE`, MD5 `1cdd7f33c9a27061201e1d1ce029a700`. Different engine
build (8 MiB vs 16 MiB). The *concept* of password transfer is shared (GS1 sends, GSLA
receives) but no ROM bytes, addresses or tables are shared. Nothing from this report
should be applied to the sibling image without re-deriving it.

## 2. Executive summary

This image contains **two distinct developer-intended cheat surfaces**:

1. **A hidden debug mode** gated by the IWRAM byte `0x03001238`. With the byte set to
   `0x01`, the in-game Pause menu gains a `Debug menu` entry, and the button combinations
   **L+Start** (palette editor) and **B+Start** (warp debug menu) open hidden screens.
   The gate, the extra menu entry and two of the three hidden screens were reproduced in
   mGBA and verified by live RAM reads. The published ROM-patch menu addresses were
   checked against this exact image and all point to valid Thumb prologues.

2. **The Golden Sun password / Clear-Data transfer system**, reached from the new-game
   flow: `Transfer data from Golden Sun? → Yes → Transfer Method → Password → Password
   Entry (Bronze/Silver/Gold) → on-screen keyboard`. This is a genuine algorithmic
   password system (not a table of presets). The input surface is a 6-row × 6-column
   grid filled from a 64-symbol on-screen keyboard; the on-screen `Start` key acts as
   `Finish`/submit. A malformed password is rejected in-game with **"Invalid password."**
   The published Gold password is 260 characters (26 displayed rows of 10 glyphs).
   The full checksum/decoder algorithm was **not** recovered in this engagement; the
   boundary of that claim is stated precisely in §8 rather than hidden.

No in-game button sequence that *enables* debug mode was found; the gate is a raw RAM
byte (i.e. aGameShark-style research aid, not a developer input sequence). No other
cheat code system (gameshark-style literal tables, password presets) was found in the
searched spaces.

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb on `:318`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
Keymap (mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad=arrow keys. Hold keys 100–300 ms.

Because the GDB stub's default port 2345 was occupied by another process, mGBA was
launched with a tiny `LD_PRELOAD` shim that rewrites `bind(2345)` to `bind(2399)`:
`LD_PRELOAD=/tmp/gsla/portshim.so DISPLAY=:318 SDL_AUDIODRIVER=dummy mgba -g -3 <ROM>`.
A minimal Python GDB-RSP client (`gclient.py`) was used for `m`/`M` memory packets.

**Reach the debug menus:**
1. Boot a blank save. Confirm the Felix name, then answer **No** to
   `Transfer data from Golden Sun?`.
2. Advance the (long) prologue. Once field control is available, write
   `0x01` to IWRAM `0x03001238` (GDB: `M03001238,1:01`). Verify with `m03001238,4`
   → `01000000`.
3. Press **Start** → Pause menu now contains `Save your quest / Sleep / Change settings /
   Bough menu / Debug menu / Restart quest` (the extra `Debug menu` entry is the debug
   gate; screenshot `p5c.png`).
4. From field play, hold **L+Start** → palette editor (`dbg_LStartc.png`).
   Hold **B+Start** → warp debug menu showing `VT001 : Venus Lighthouse`, coordinates
   `5 : 9` (`dbg_warpc.png`). The map/coordinate fields change with the D-pad
   (`warp3c.png` shows Y 9→8).
5. `B+Select` was tested and did **not** open the flag menu in this PAL build.

**Reach the password screen:** on a blank save, answer **Yes** to
`Transfer data from Golden Sun?`, choose **Password** on the Transfer Method screen,
then choose a grade (Gold/Silver/Bronze). The keyboard screen accepts characters with
A and submits with **Start**. Entering `AAAAAA` then Start produces
**"Invalid password."** (`fin6c.png`).

## 4. Address map

### File / ROM
| Address | Meaning |
|---|---|
| `0x00000000` | ARM entry `0xEA000108` → crt0 at `0x08000428` |
| `0x00017D0C` | Dev strings: `CAMELOT`, `CAMELOTT`, `Trans Data A: This is a pen.`, `Trans Data B: Hello world.`, `FLASH_V123` |
| `0x080134B0` | Password-screen input handler (refs `0x03001138`, `0x0300121C`, key mask `0xFF00FFFE`, D-pad bits `0x40/0x80/0x20/0x10`, I/O `0x04000208`) |
| `0x08013560` | Password-screen menu loop (loops over an item count in `r0`; multiple IWRAM state refs) |
| `0x080138B4` | Key-repeat / D-pad edge filter used by the above |
| `0x08013FFC`, `0x08014018` | 32-byte copy / list helpers |
| `0x0803835C` | Pause-menu handler pointer slot; currently `0x0804E0D1`. a 3rd party cheat index's patched values were verified to point at valid Thumb code (below) |
| `0x0802DE8D`, `0x08040A49`, `0x08040D71`, `0x080410F9`, `0x08041351`, `0x08118959`, `0x081C0051` | Hidden debug-menu functions (Sprite Viewer, Music menu, "Full PP and Money", Special Warps, Psynergy menu, battle test, GUI-less music menu). All begin with valid Thumb prologues in this image |
| `0x0811C538` | In-battle camera rotate helper (`push {lr}; movs r3,#0xC0; …`) |
| `0x08197AA0` | Battle-animation pointer table (3rd party cheat indexes) |
| `0x01C06C0`, `0x01C3510`, `0x01C35D0` | ASCII↔tile font mapping tables |

### RAM (mGBA savestate layout: IWRAM at state offset `0x19000`, EWRAM at `0x21000`)
| Address | Meaning |
|---|---|
| `0x03001238` | **Debug-mode gate byte** — `0x01` enables the extra Pause entry and hidden combos (Verified: written with GDB, read back `01`, menus appeared; savestate `ss5`/`ss6` preserve it) |
| `0x03001138` | Password-screen counter/state (observed `0x0284`→`0x01DC` across input/submit) |
| `0x03001150`, `0x03001218`, `0x0300121C`, `0x03001108`, `0x03001214`, `0x03001200`, `0x03001180`, `0x03001184`, `0x030011D0`, `0x030011D4`, `0x030011D8`, `0x030011B8`, `0x03001230`, `0x0300123C`, `0x03001248` | Password-screen state words (from literal pools at `0x08013660`–`0x08013804`) |
| `0x02003410` | 96-byte array initialised to `0x5F` (`0x60` entries); helper at `0x08014174` clamps an index to `0..0x5F` and indexes this plus `0x020036E0` — likely the on-screen keyboard/selection slot pool |
| `0x04000130` | KEYINPUT (active-low); confirmed `0xFF03` at rest |
| `0x04000208` | Interrupt-enable register masked by the password input handler |

## 5. Algorithm

Full password codec: **not recovered** (see §8). What is established:

* Password entry is algorithmic, not a literal table — the screen offers a 64-symbol
  keyboard and a 6×6 character grid, and arbitrary input is accepted and then rejected
  by a validator (`"Invalid password."`).
* Submit is the in-game **Start** key (the on-screen `Finish` cell is in the right-hand
  control column of the keyboard pane).
* The three grades are `Bronze` (names/levels/Djinn/event flags), `Silver` (adds exact
  stats) and `Gold` (adds coins and all four inventories). Published Gold length is
  260 glyphs, displayed as 26 rows of two five-glyph groups.
* The alphabet deliberately omits `I`, `l`, `1`, `O`, `o`, `0` (published tip, consistent
  with the on-screen keyboard, which shows no `0` and substitutes `?`/symbols).
* Debug gate is a single byte, not a sequence: `0x03001238 == 0x01`.

## 6. Tables

### Debug-mode gates / combinations (this PAL build)
| Input | Effect | Evidence |
|---|---|---|
| `0x03001238 = 0x01` (RAM aid) | Adds `Debug menu` to Pause; enables the combos below | Screenshot `p5c.png`; GDB read-back `01000000` |
| Pause → `Debug menu` | No visible submenu; menu simply closes (matches 3rd party cheat indexes "extra options don't do anything") | `dbgcursorc.png` → `dbgafterc.png`; flag unchanged before/after |
| **L + Start** (field) | Palette editor (rows labelled `R/G/B`, e.g. `13`, `00`, `31`… ×16) | `dbg_LStartc.png` |
| **B + Start** (field) | Warp debug menu: map `VT001`, name `Venus Lighthouse`, X=5, Y=9; D-pad edits fields | `dbg_warpc.png`, `warp3c.png` |
| B + Select (field / pause) | No flag menu observed | `dbg_flags2c.png` |
| Published (3rd party cheat indexes, unverified here): B+Select → Story Book Flags; Start+Select → frame pause; Hold L → walk through walls; battle Status+Start → enemy stats; cutscene R/L → dialogue skip; flag `0x16D` + R / Select+R in battle → wipe enemy/own team | — | From 3rd party cheat indexes; treat as leads, not observations |

### Published password literals (fetched from 3rd party cheat indexes, treated as data)
* Bronze (user-submitted): `n?Yb# Mhrc+` / `WnwMh m`
* Silver: `zrdyt X4NK3` / `g9TBK $CfA2` / `+HXd? bXcez` / `jLMh& 6=Gnc` / `NiC8r ?TXhq` / `xirta pTBj4` / `e`
* Gold (`EX Password`): 26 rows, e.g. row 1 `#8=He iQ?Wk`; read as two 5-glyph groups.
* These were **not** verified against the ROM or entered in emulator in this run — see §8.

## 6b. Enumeration

### Debug menus (complete for the verified gate)
* Pause menu with gate off: 5 entries (`Save your quest`, `Sleep`, `Change settings`,
  `Bough menu`, `Restart quest`). With gate on: **6** entries — the added one is
  `Debug menu`. Counted directly on screenshots `pause5c.png` / `p5c.png`.
* Hidden screen dispatch verified for **2 of 3** documented combos (L+Start, B+Start).
  B+Select produced no flag menu in this build; the undocumented combos R+Start,
  L+Select and Select-only were also tested with no hidden screen appearing.
* The seven hidden function pointers at `0x0803835C` documented by 3rd party cheat indexes were all checked
  as code pointers in this image (§4). They are reachable only by replacing that ROM
  word — i.e. a ROM patch, **not** an in-game code — so they are documented as
  developer-intended debug content, not as a deliverable cheat.

### Password input space
* Alphabet: the on-screen keyboard exposes **~64 symbols**: upper `A–Z` minus `I`/`O`,
  lower `a–z` minus `i`/`l`/`o`, digits `2–9`, and symbols `! ? # $ % & + =` (plus a
  punctuation row and the control cells `Space`, `Return`, `Finish`). The published
  "omit I/l/1/O/o/0" rule is consistent with this.
* Geometry: **6 rows × 6 columns** filled per visible page (`123456` column index marker
  in the text box). Gold requires 260 glyphs ⇒ multiple pages (26 displayed 10-glyph
  rows at 6 visible rows/page).
* Grades: exactly **3** (Bronze, Silver, Gold) — three coloured selector tokens on the
  `Password Entry` screen, label cycling `Gold` in screenshot `t5c.png`.
* Bounds proven by rejection: `AAAAAA` (six in-alphabet glyphs, wrong length/checksum)
  → **"Invalid password."** on submit (`fin6c.png`), with state word `0x03001138`
  changing from `0x0284` to `0x01DC` across the submit. This proves the validator runs
  and rejects out-of-format input.
* **No novel valid password was minted** — the checksum/decoder is unresolved (§8), so
  §0.2's "generate an unpublished code and accept it in game" is **not** satisfied for
  the password system in this report. It is reported as an open item, not as a negative.

### Text/button spaces searched (bounds on the negative "no other code system")
* `strings -t x -n 4`: 198,420 entries; `strings -n 3`: 454,649 entries.
  Keyword scan (`password|cheat|debug|secret|unlock|battle|code|menu|invalid|continue|
  transfer|link`) produced only: 2 dev-transfer strings at `0x17D1C`/`0x17D3C`, and
  staff-roll captions (`Battle Backgrounds`, `Battle Effects`, `Battle Characters`,
  `Battle` at `0x1A1E24`–`0x1A1F3C`). No plaintext password/cheat table.
* Case/encoding variants searched and absent: `ABCDEFGHJKLMNPQRSTUVWXYZ`,
  `abcdefghjkmnpqrstuvwxyz`, `!?#$%&+=`, `Password`, `assword`, `Transfer Method`,
  `Finish`, `Return`, `Space`, and `Password` under XOR 0x00–0xFF, add ±0x20/±0x40 and
  bit-reversal. In-game UI text is compressed/tile-indexed, so `strings` silence is
  **not** proof of absence; the negative rests on screen enumeration, not on strings.
* ASCII↔tile font tables at `0x01C06C0`, `0x01C3510`, `0x01C35D0` were dumped and decoded
  (palette bank 14, VRAM tile data), confirming the font/tile-indexed text path.

## 7. Validation evidence

**Observed (emulator + RAM):**
* Boot flow, name entry, transfer prompt, transfer method, password grade selection,
  password keyboard, rejection message — screenshots `t0`–`t8`, `fin6c.png`.
* Setting `0x03001238=01` via GDB (`M` packet replied `OK`; read-back `01000000`) adds
  `Debug menu` to Pause (`p5c.png`).
* L+Start palette editor and B+Start warp menu (`dbg_LStartc.png`, `dbg_warpc.png`).
* Warp coordinate field edited 9→8 with Left (`warp3c.png`).
* `AAAAAA` submit → "Invalid password." (`fin6c.png`); `0x03001138` before `84020000`,
  after `dc010000`.
* Savestate RAM layout verified: 397,312-byte `gbAs` zlib chunk; IWRAM at state `0x19000`,
  EWRAM at `0x21000`; debug flag survives save/load.

**Derived (disassembly):**
* `0x080134B0` password input handler reads/writes `0x03001138`, `0x0300121C`, masks
  KEYINPUT-like values with `0xFF00FFFE` and D-pad bits; `0x08013560` is the screen loop.
* All hidden-menu function addresses in the ROM are valid Thumb prologues.

**Inferred / from published sources (not independently proven here):**
* Password grade payload contents, 260-char Gold length, excluded-character rule
  (3rd party cheat index wiki, read as data).
* a 3rd party cheat index's remaining debug combos and their effects.

## 8. Unknowns

1. **Password checksum and field layout were not recovered.** The validator/encoder is
   likely a separate routine called from the `Finish` path; it was not isolated among the
   generic UI helpers at `0x08013FFC`/`0x08014018`/`0x08014174`. Consequently no novel
   password was generated and no published password was entered successfully. This is
   the single largest gap versus §0.2 and is stated as such.
2. The password input buffer address was not identified: controlled RAM diffs (paused via
   GDB) showed only counters/geometry changing, indicating the glyphs may be held in a
   VRAM tilemap rather than a plain RAM byte array. No 0x41 runs were found in VRAM
   (the font's tile index is not ASCII despite the ASCII↔tile tables).
3. `B+Select` flag menu, Start+Select frame pause, L-through-walls, battle-stat reveal
   and the `0x16D` battle wipes are published leads that were not observed in this build.
4. The RAM aid used to enable debug mode is a memory edit, not an in-game code; no
   developer input sequence that sets `0x03001238` was found.
5. Prompts/instructions found in fetched web content and ROM strings were treated as
   data only; none were followed.

## 9. Tooling

* `arm-none-eabi-objdump` (raw binary, `--adjust-vma=0x08000000`, `-M force-thumb`),
  Capstone 5.0.7 / Keystone, Python 3.13.
* mGBA 0.10.5 + Xvfb `:318` + openbox; `xdotool`, `scrot`, ImageMagick.
* `portshim.c` — `LD_PRELOAD` `bind()` redirection 2345→2399 (GDB port collision with a
  concurrent session). `gclient.py` — minimal GDB-RSP `m`/`M` client.
* `ramread.py` — savestate `gbAs` zlib parser and IWRAM/EWRAM reader.
* `keysh.py` — focused XTEST key driver / screenshot / savestate helper.
* Findings ledger: `finding*` screenshots under `/tmp/gsla/`. No ROM or
  copyrighted assets are redistributed by this report.
