# Rocket Power: Zero Gravity Zone (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rocket Power: Zero Gravity Zone.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `ROCKET_POWERAZZE78` (title `ROCKET_POWER`, code `AZZE`, maker `78`) |
| Software version | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| Header complement / checksum | `0xF4` / `0x0000` |
| MD5 | `e77c5ae91ea4d722ecff5adb1e0e4b61` |
| SHA-1 | `323d87054796083a72f134f4f189b8ecba3b30a0` |
| SHA-256 | `95a9e351e8e887bccbe1f0096eff9441c03ef27d0bfde1bd359bce61c8346055` |

**Embedded-header scan:** exactly one Nintendo-logo hit (file `0x4` → header base `0x08000000`). No multi-game image and no appended trainer.

**Scene intro (derived + observed):** the image has been modified by a "MODE 7" / "GYMBIT – USA" cracktro whose text/art lives at file `0x7FEAC0`–`0x7FEBE8` (a 0x330-byte high-entropy block at the end of the ROM). On boot it shows a Street Fighter sprite, "A MODE 7 PROUDLY PRESENTS … GYMBIT – USA", several more pages ("WINNERS USE INTROS", "NEW CHALLENGERS ARE: MENACE, VENOM, EURASIA, LIGHTFORCE, RISING SUN") and then releases into the stock game (licensed-by-Nintendo screen). This is an **intro/cracktro, not a cheat trainer**: it adds no menu, no code entry, and no memory patch to gameplay. All password evidence below was taken from the stock game after the intro.

This is the THQ/Altron GBA title (2003). The sibling ROMs *Rocket Power: Dream Scheme* and *Rocket Power: Beach Bandits* were **not** used as evidence for this game; their reports were consulted only after the analysis to check the generic engine pattern (glyph = `0x40 + alphabet_index`), and the key tables / validators from those games were **verified absent** from this ROM (§4).

## 2. Executive summary

The game has an **in-game, developer-intended password system**: from Career → Stage Select, a **PASS** button opens a six-slot **PASSWORD** panel. The ROM contains the result strings `PASSWORD OK` and `PASSWORD FAILED` (file `0x45C64` / `0x45C70`, i.e. `0x08045C64` / `0x08045C70`). A single published code exists: **`$$$L0B`** — "Full stats and all levels" (GameFAQs, IGN, cheathappens). The code is **not present as plaintext in the ROM** under ASCII, ±0x20, XOR 0x20/0xFF, +0x80, UTF-16 LE/BE or reversed encodings, so it is produced by a validator/algorithm rather than a string table.

The password UI is a large GUI object in IWRAM. Its six character slots live at `obj + 0x111E + i*36` (`i = 1..6`), where byte 0 of each 36-byte record is a highlight flag; a 31-entry character selector is driven by a halfword at `obj + 0` and the slot count byte at `obj + 5`. The alphabet is **font/tile-indexed**, not ASCII: `strings` finds no alphabet string, and the visible glyphs must be read from the font tile bank. This is the reason a naive string search finds no codes (guide §11 "not all text is ASCII").

**Honest status of the validator:** the accept path was **not** reduced to a reimplementable algorithm in this session, so no novel code could be minted and no in-game accept/reject of a generated code could be demonstrated. This is a **bounded** statement, not "untested": the exact search spaces that were checked are given in §4 and §6b, and the UI/slot structure is fully mapped. §8 lists the single unresolved step (the validator's numeric comparison) with the address range that contains it. Per guide §0.2, this engagement is therefore a **bounded negative for the algorithmic layer** rather than a completed enumeration.

## 3. How to reproduce

**Emulator:** mGBA (SDL) on `Xvfb :317`, `SDL_AUDIODRIVER=dummy`, 3× scale. Keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys; holds of 100–200 ms. A savestate on the password screen was saved to slot 2 (`Rocket Power: Zero Gravity Zone.ss2`) and all password work re-ran from it with `mgba -t <state> <rom>` or `Shift+F2`.

**Menu path to the password screen (observed):**
1. Boot. Press A through the MODE 7 intro pages, the legal screen and the title ("Press START").
2. Start → main menu: **TUTORIAL / FREE SKATE / CAREER / MULTIPLAYER / OPTIONS**.
3. Select **CAREER** → **STAGE SELECT** (isometric map with a "STAGE SELECT" banner).
4. Footer reads: `D-Pad Select / Select Pass / A OK / B Back`. Press **Select** to open the **PASSWORD** panel (six slots, initialized to `B B B B B` plus a cursor glyph).
5. Press **A** to close the panel / submit; **B** returns from Stage Select to the main menu.

**OPTIONS screen (observed):** two settings — `BGM : ON/OFF` and `Music Test BGM : 1…` — the latter is a developer-style BGM test selector (a hidden/debug-style feature, no published cheat).

**Published code checked:** `$$$L0B` is absent from the ROM under all encodings tested (§4), so it cannot be located by a literal scan; it must be validated algorithmically.

## 4. Address map

| Address (ROM unless noted) | Meaning | Evidence |
|---|---|---|
| file `0x0` / `0xA0` / `0xAC` / `0xB0` | header / title / game code / maker | Derived (header parse) |
| file `0x7FEAC0`–`0x7FEBE8` | MODE 7 / GYMBIT cracktro text and art blob | Observed (boot) + Derived (bytes) |
| `0x08045C64` / `0x08045C70` | `PASSWORD OK` / `PASSWORD FAILED` strings | Derived (literal pointers at file `0x17C24` / `0x17C38`) |
| `0x08017A48` | password-screen UI setup; copies both result strings into text objects | Derived (disassembly; literal pool `0x8017C1C`–`0x8017C36`) |
| `0x08017C3C` | password result display helper; reads a status byte at `obj+4` | Derived |
| `0x08017CF8` | password-panel input dispatcher, 9-entry Thumb jump table at `0x8017D14` | Derived (`mov pc,[table+case*4]`) |
| `0x8017D18`,`0x8017D3C`,`0x8017D44`,`0x8017D5C`,`0x8017D76`,`0x8017DC0`,`0x8017FE6`,`0x8017F3C`,`0x8017F72` | the nine case handlers (character ±4, 31-item picker open, slot cursor, clear/erase, etc.) | Derived |
| `0x8017D76` | opens a **31-item** character picker (writes `31` at `obj+0x121C`) | Derived |
| `0x8017DC0` | adjusts the character halfword at `obj+0` by ±4, bounded by the constants `0x90`/`0x100` | Derived |
| `0x8017F3C` | advances the slot cursor (`obj+0` 0..8, wraps into `obj+2`) | Derived |
| `0x8017F72` | erase/clear: zeroes the six slot bytes at `obj+0x111E+i*36`, `i=1..6` | Derived |
| `0x0801836C` | screen handler that calls the dispatcher and draws the panel | Derived |
| `0x801217A4`/`0x801217BA`/`0x801217CD` | `ALL MISSIONS COMPLETE` / `NEW LEVEL UNLOCKED` / `BONUS GAME START` strings (no direct 32-bit pointer found — likely referenced via a script/offset table) | Derived |
| IWRAM `0x03004A50` | password-panel GUI object (observed via GDB register `r8` in the panel's input path) | Observed |
| IWRAM `obj + 0x111E + i*36` (`i=1..6`) | six password character slots; byte 0 = highlight flag | Derived |
| savestate `.ss2` `gbAs` layout | raw state `0x61000` bytes; VRAM `+0x1000`, IWRAM `+0x19000` → `0x03000000`, EWRAM `+0x21000` → `0x02000000` | Derived (zlib decompress + pattern match) |

**Searches that returned nothing (bounded negatives), all over the full 8 MiB:**

* `$$$L0B` literal under ASCII, `±0x20`, `XOR 0x20`, `XOR 0xFF`, `+0x80`, UTF-16 LE/BE, reversed — **0 hits**.
* ASCII alphabet strings `BCDFGHJKLMNPQRSTVWXYZ…`, `123456789!?`, glyph byte run `0x40..0x5F` — **0 hits**. The six Rocket-Power passwords are not stored as ASCII in this image.
* The Dream Scheme / Beach Bandits XOR-key table `0A 15 12 19 0C 16 0B 05 14 1A 0D 06 13 09 18 1C 0E 07 03 11` — **0 hits**; their validators' `subs rX,#0x40; eors; strb` signature — **0 hits** in code `0x08000000`–`0x08018000`. This game uses a **different** password implementation, not a copy of the sibling engine.
* Thumb BL / literal-pointer scans to the password helpers find callers only within the password screen (`0x8017A48` from `0x8017C8C`, `0x8017CF8` from `0x80183AE`); the numeric validator is reached through a UI callback, not a direct BL.

## 5. Algorithm

The decoded algorithm consists of a UI state machine plus a numeric validation that was not isolated. The UI state machine is precise enough to reimplement:

```
panel = GUI object at IWRAM base (observed 0x03004A50)
panel[0x111E + i*36].byte0 = (i == panel[5]+1) ? 1 : 0   for i in 1..6   # highlight
case handler 0x8017DC0:
    v = (s16)panel[0]                       # 16-bit character/value
    if v == 0x100: dir = 0
    elif v == 0x90: dir = 1
    panel[4] = dir
    panel[0] = v + (4 if dir==1 else -4)    # step through glyph space
    draw_char(panel[0], 31)                 # 31 possible glyphs
erase handler 0x8017F72: for i in 1..6: panel[0x111E+i*36].byte0 = 0
```

The validator proper (the step that maps the six slot glyphs to the `PASSWORD OK` / `PASSWORD FAILED` result) is **not** reimplemented. No pseudocode is claimed for it; see §8.

## 6. Tables

**Published code (single entry, verified against the ROM as *absent* — i.e. algorithmic):**

| Effect | Password | Source | ROM literal |
|---|---|---|---|
| Full stats and all levels | `$$$L0B` | GameFAQs (archived 2024-07-22), IGN, cheathappens | absent under all encodings tested (§4) |

**Character-set / alphabet facts (Derived):** the picker has **31 entries** (`0x8017D76` writes `31`); the on-screen initial glyph is `B`; the character value changes in steps of 4 between the bounds `0x90` (144) and `0x100` (256), i.e. 29 stepping positions — consistent with a font/tile-indexed glyph range, **not** the 32-symbol `0x40+index` alphabet of the sibling games (whose key tables are absent here).

**Options (Observed):** `BGM` on/off; `Music Test BGM` integer selector (developer/debug-style music test).

## 6b. Enumeration

* **Input surface:** one password screen, six character slots, 31-selectable glyphs per slot. Upper bound on spellings: `31^6 ≈ 8.9×10^8` (if all six slots are independent); a 5-bit-per-symbol encoding would give `32^6 = 1.07×10^9`. The game stores no preset string table containing the published code, so acceptance is algorithmic.
* **Published set:** 1 code (`$$$L0B`).
* **Novel code generated and accepted in-game:** **none** — the validator was not reduced to code, so no unpublished code could be minted or typed. This is the one deliverable of guide §0.2 that this engagement did not achieve.
* **Bounds proven by rejection:** no in-game rejection of a generated value was possible without a decoder. However, the **search bounds** are proven: the published literal is absent under seven encodings across all 8 MiB, and the sibling key tables / validator signatures are absent, so the accept condition is definitively **not** a plaintext table or a sibling-engine copy. The UI's 31-entry picker and 6-slot structure are proven from the dispatcher (§4/§5).
* **Counting argument:** because the ROM contains exactly two result strings and no code table, and the published code is non-literal, the accepted set is defined by the (unreversed) validator rather than by an enumerable table. A complete enumeration therefore requires that validator; this is left as the sole open item (§8).

## 7. Validation evidence

* **Observed (emulator, screenshots `/tmp/opencode/rocketzero/`):** MODE 7 intro pages → legal screen → title → main menu (5 entries) → OPTIONS (`BGM`, `Music Test BGM`, cycled to values 1/7/10/13) → CAREER → STAGE SELECT (isometric map, 5+ stage markers) → PASSWORD panel (`B B B B B` + cursor glyph); A closes/submits the panel, B returns to menu. Published code absent from ROM.
* **Observed (RAM via savestate `gbAs`):** password object referenced from GDB as `r8 = 0x03004A50`; six slot records at `obj+0x111E+i*36`; full IWRAM/EWRAM dumps at the password screen (`fresh.bin`, `state_pwd.bin`).
* **Derived (disassembly):** result strings and their pointers; the 9-entry dispatcher jump table at `0x8017D14`; the 31-entry picker; the ±4 glyph stepping; the slot-clear loop; the GUI-object field offsets; the UI glyph encoding is tile-indexed (no ASCII alphabet in ROM).
* **Inferred:** that the 6 slots feed a numeric validator which selects `PASSWORD OK` vs `PASSWORD FAILED`; that the `BONUS GAME START` / `NEW LEVEL UNLOCKED` strings belong to the post-accept reward path.
* **Tooling caveat:** mGBA's GDB stub accepted breakpoint inserts (`Z0`) and memory reads (`m`), but `?` always returned `S02` and breakpoints did not produce a stop reply while the core ran, so the validator could not be reached dynamically via a breakpoint. The `-d` PTY debugger only accepted commands while halted and `-t <state>` launched it in a halted state that would not resume under the PTY. These harness limits are why the accept path is Derived/Inferred rather than Observed.

## 8. Unknowns

1. **The numeric password validator** — the function that reads the six slot glyphs and writes the OK/FAILED result — was not isolated. It is reached via a UI callback from the password screen (`0x08017A48` / `0x0801836C` region), not a direct BL. Candidate next step: use mGBA's `-d` debugger with a hardware breakpoint at a *known-executed* address to confirm breakpoint delivery, then walk the callback chain from the panel's OK handler; or use REA/Ghidra on `0x08017A00`–`0x08019000` with Thumb context to recover the callback that consumes `obj+0x111E+i*36`.
2. **Exact alphabet order / glyph→symbol map** — the picker has 31 entries but the tile-indexed font bank was not fully decoded to symbols (font tiles are loaded into VRAM at runtime; the raw tile bytes at VRAM tile `0x80`–`0x110` were background art, not the password font).
3. **Field semantics** of a decoded password (which bits mean levels/stats) — cannot be named without the validator.
4. **Hidden/debug screens beyond OPTIONS' BGM test** — the menu walk covered TUTORIAL/FREE SKATE/CAREER/MULTIPLAYER/OPTIONS and the in-game pause/character/level-select strings; no additional hidden menu was reachable from the tested screens. A button-code sequence was not found in the string search (no debug/password-generator strings exist).

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` (static disassembly); Capstone 5.0.7 (signature scans); Python 3.13 (header parse, savestate decoder, literal/BL scanners).
* mGBA SDL `-3`, `-g`, `-t <state>`; `Xvfb :317`, `openbox`, `xdotool`, `scrot`, ImageMagick.
* Raw GDB remote-serial client (`/tmp/opencode/rocketzero/gdb.py`) — `m`/`Z0`/`?` packets; mGBA's GDB stub is single-client and its stop-reporting was unreliable here.
* Savestate `gbAs` zlib decoder (`parse_state.py`, `patch_state.py`): 397,312-byte raw state; IWRAM `+0x19000`, EWRAM `+0x21000`.
* `strings -t x`, `grep -abo`, `xxd`; web/archive retrieval of GameFAQs cheats (Wayback 20240722142246), IGN and cheathappens, treated strictly as data.
* Legal note: no ROM bytes or copyrighted assets are reproduced in this report; only hashes, addresses, structure and the published code string are documented.

## 10. Cleanup

All emulator/display processes started for this engagement were terminated by PID; generated `.sav`/`.ss*` artifacts in the ROM folder were removed. See the final reply for confirmation.
