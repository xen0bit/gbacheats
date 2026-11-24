# Shrek: Hassle at the Castle (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Shrek: Hassle at the Castle.gba` |
| Size | 4,194,304 bytes (0x00400000) |
| `file` ID | Game Boy Advance ROM image: "SHREK HATC" (AH4E6S, Rev.00) |
| Header title | `SHREK HATC` (0xA0–0xAB) |
| Game code | `AH4E` (0xAC–0xAF) |
| Maker code | `6S` (0xB0–0xB1) |
| Fixed byte | 0x96 at 0xB2; unit 0x00, device 0x00 |
| Version | 0x00 |
| Complement | 0x09 at 0xBD; check `sum(0xA0..0xBC)+0x19 == 0 (mod 256)` → 0x09 ✓ |
| Header checksum | 0x0000 (normal for rebuilt/verified retail header) |
| Entry word | `0xEA00002E` → `b 0x080000C0` (stock GBA crt0, **not** a cracktro) |
| MD5 | `f986d79271e685679f0b5ecb673e9dea` |
| SHA-1 | `afeb14671fad093fec0b3ab0e95e01a01de9f4d8` |
| SHA-256 | `e716bce02239bfc87b3a2b84294dc6b92d877afa0140a3e5a2425b0657bd0c88` |

**Embedded-header scan:** the 156-byte Nintendo logo occurs at file `0x04` (the real header) and at `0x1D1D60`. The second hit is a verbatim copy of the retail header embedded in ROM data (title `SHREK HATC`, code `AH4E`, entry word `0xEA00002E`); it is not a second playable image, a multiboot stub, a trainer, or a patch. No other headers, appended trainers, or cracktro entry patches were found.

## 2. Executive summary

Two button-code cheats are published for this exact SKU: **Level Skip = `BBABBABBAAAAB`** (Cheat Happens, GameFAQs mirror, okay.fandom, planetcheats) and **More Health = `BAABAACA`** (okay.fandom). Both were treated as data, never as instructions.

Exhaustive static and dynamic work found **no developer-intended password/code-entry system** in this ROM:

* Neither code string, nor any button-mask table, nor any code validator exists in the image under any of the encodings tested (ASCII, `+0x20`, UTF-16LE/BE, UTF-32, 1/2/3/4-bit packing, active-high/active-low u8/u16 masks, forward/reversed).
* The input path is a standard TOSE-engine driver (KEYINPUT at `0x080318e8` → state at `0x030015DC/E0/E4`), and no function in the ROM reads that state to compare a multi-button sequence. The only button-combination check found is a **developer reset** (all four D-pad directions → `SWI` reset at `0x0800997c`/`0x08032bbc`), verified live in the emulator.
* The font/tile-indexed in-game text bank was decoded (`byte = ASCII − 54`). It contains a **"SELECT LEVEL"** menu label that the retail build never displays: the main-menu selector is hard-bounded to three entries (Story, VS/Fighting, Options), so the fourth label is unreachable — a cut feature, not a gated code.
* Both published codes were typed in the emulator on every plausible screen (title, main menu, character select, level map, gameplay, pause) with long holds and with frame-accurate short holds; RAM diffs of IWRAM/EWRAM show no persistent code-progress state and no health/level change. The codes are **unverified and apparently non-functional** in this ROM.

Everything reachable was walked with screenshots; the negative result is bounded by the counts in §6b.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`) under Xvfb on `:316`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`. mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. **Hold keys ~200–600 ms**: 120 ms taps are missed by this engine's polling (a 1 s A-hold was required to leave the level-map screen).
* Screens walked (each with screenshots saved in `/tmp/shrekhassle/`): legal splash → title ("Press Start") → main menu (Story Mode / Fighting Mode / Options) → Options (Difficulty Easy/Normal/Advanced; Languages EN/IT/FR/ES/DE/NL; Erase Saved Data) → Story Mode → Select Saved Game (3 slots + New Game) → Level-1 intro → cutscene → Level-1 map screen → Select Character → objective card → gameplay (HUD: lives, hearts, ∞ shout, score, coins) → in-game pause ("Pause") → Fighting Mode ("Multiplayer With Single Game Pak" / "Multiplayer With Multi-Game Pak").
* Code-entry attempts: published sequences entered on each of the above screens; no effect observed.
* Debug trigger (works): during gameplay, hold **Up+Down+Left+Right simultaneously** for ~1 s → game resets to the Level-1 map screen, then A → Select Character. Confirmed twice.
* Font decode: text bytes are ASCII−54 (`0xCA` addend); `0xF2` = space, `0xFE` = line break, `0xFF` = skip. Example: bytes `1A 1C 0F 1D 1D` → "PRESS". Decode script: `decode_all.py` (§9).

## 4. Address map

| Address (ROM) | File offset | Meaning | Evidence |
|---|---|---|---|
| `0x08000000` | 0x000000 | Entry `b 0x080000C0`, stock crt0 | Observed |
| `0x080001DC` | 0x0001DC | crt0 literal = `0x0800239D` → **main() = 0x0800239C** | Derived (`ldr r0,[pc,#148]; bx r0`) |
| `0x0800239C` | 0x00239C | main: sets up engine, enters menu loop `0x08002728` | Derived (Ghidra) |
| `0x08002728` | 0x002728 | Main-menu dispatcher: index 0→Story, 1→VS, 2→Options; **no case 3** | Derived (Ghidra) |
| `0x08009A58` | 0x009A58 | Menu object constructor | Derived (Ghidra) |
| `0x08009AC0` | 0x009AC0 | Menu handler; selection index wrapped with bound **3** (`FUN_08009930(x,3,±1,1)`) | Derived (Ghidra) |
| `0x0800997C` | 0x00997C | Debug check: if `held & 0xF == 0xF` → `FUN_08032BBC(0xFF)` | Derived (Ghidra) |
| `0x0801AD38` | 0x1AD38 | Wrapper calling input driver then `0x0800997C` | Derived (Ghidra) |
| `0x08032BBC` | 0x32BBC | Reset helper: `IME=0; SWI 1; SWI 0; SWI 0x28` | Derived (Ghidra) |
| `0x080318E8` | 0x318E8 | Input driver; literal pool at `0x08031930` = `0x04000130` (KEYINPUT) | Derived (objdump) |
| `0x030015DC` | — | IWRAM: active-high **held** keys | Derived |
| `0x030015E0` | — | IWRAM: newly **pressed** keys this frame | Derived |
| `0x030015E4` | — | IWRAM: **released** keys this frame | Derived |
| `0x030015B0` | — | IWRAM: input state base / per-key repeat counters | Derived |
| `0x0803F520` | 0x3F520 | ASCII debug strings: "Sample Menu", "Sample Program", "Sound Test", "MultiSio Sync Test" | Observed (`strings`) |
| `0x0803FEB6` | 0x3FEB6 | ASCII debug UI: "STOP","WAIT","LINK","EXIT","ERROR","A : Start","B : Exit","B : Cancel","+ : Move","ID : ","Push Any Key To Exit" | Observed |
| `0x08042400+` | 0x42400 | Text-string pointer table (u32 into ROM) | Derived |
| `0x0804244C` | 0x4244C | Table entry → `0x08047035` "PRESS START" (start of main-menu string block) | Derived |
| `0x08042458` | 0x42458 | Table entry → `0x08047057` "SELECT LEVEL" (hidden) | Derived |
| `0x08047035` | 0x47035 | Encoded text bank: PRESS START / STORY MODE / VS MODE / **SELECT LEVEL** / OPTIONS, ×6 languages | Derived (decoded) |
| `0x08049000+` | 0x49000 | More encoded text: "GAME OVER", "CONTINUE GAME", "YES","NO", credits | Derived (decoded) |
| `0x1D1D60` | 0x1D1D60 | Embedded duplicate of retail GBA header | Observed |

File offset = ROM address − `0x08000000` for this single-image 4 MiB ROM.

## 5. Algorithm

**Input path (derived):** `held = ~KEYINPUT & 0x3FF` (active-high); `pressed = held & ~prev_held`; `released = ~held & prev_held`; store to `0x030015DC/E0/E4`. A 10-entry per-key repeat table starts at `0x030015B0`. All UI/movement code reads these three words; there is no sequential-code accumulator.

**Text encoding (derived):** for each byte `b` in a text string: `0x00` terminates, `0xF2` = space, `0xFE` = line break, `0xFF` = skip, otherwise character `= chr(b + 54)` (ASCII−54). Verified by rendering "PRESS START" / "STORY MODE" / "SELECT LEVEL" / "OPTIONS" / "GAME OVER" from raw ROM bytes.

**Menu bound (derived):** the main-menu handler wraps the cursor index with modulus 3; the dispatcher has exactly three action branches. A fourth label ("SELECT LEVEL") exists in the text bank but no branch or reachable index selects it.

## 6. Tables

| Item | Value |
|---|---|
| Published Level Skip code | `BBABBABBAAAAB` (13 presses: B B A B B A B B A A A A B) — Cheat Happens 2003-01-16; also okay.fandom, planetcheats |
| Published More Health code | `BAABAACA` (8 presses: B A A B A A C A; `C` unexplained — likely "Control"/D-pad) — okay.fandom |
| CodeBreaker RAM addresses (out of scope, used only as RAM anchors) | lives `0x0200D7D0`, health `0x0200F36C`, shout `0x0200D7D8`, timer `0x0200EF38` |
| Button masks (active-high) | A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200 |
| Debug reset trigger | all four D-pad directions held simultaneously → reset to level map |
| Main-menu entries (reachable) | 0=Story Mode, 1=VS/Fighting Mode, 2=Options |
| Main-menu string block (text bank) | PRESS START, STORY MODE, VS MODE, **SELECT LEVEL** (unreachable), OPTIONS |

## 6b. Enumeration

This section gives the bounded negative for the code/password system (§0.2 "negative results bounded").

**Reachable menu space (fully enumerated):** title screen → main menu with exactly **3** items (bound 3 verified in `0x08009AC0`; dispatcher `0x08002728` has branches for 0,1,2 only) → Options (3 groups: difficulty with 3 values, language with 6 values, Erase Saved Data) → save-selection (3 slots + New Game) → character select (3 characters per the manual: Shrek/Donkey/Fiona) → Fighting Mode (2 link modes). Every item was visited with screenshots. There is **no code-entry screen** among them.

**Hidden/unreachable text:** the main-menu text bank (`0x08047035`) holds 5 labels but the selector is bounded to 3; "SELECT LEVEL" (`0x08047057`) is the unreachable 4th. This is a cut feature, not a gated code — no dispatcher branch exists for index 3.

**Literal/search space checked (all negative):**

| Search | Space | Result |
|---|---|---|
| ASCII `BBABBABBAAAAB`, `BAABAACA` | 4 MiB whole ROM | 0 hits |
| Case-insensitive / `+0x20` shifted | 4 MiB | 0 hits |
| UTF-16LE/BE, UTF-32LE/BE | 4 MiB | 0 hits (generic word scan) |
| u16 masks, active-high and active-low, forward/reversed | 4 MiB | 0 hits |
| u8 masks (1 byte/press), active-high/low, forward/reversed | 4 MiB | 0 hits |
| Nibble-packed (4-bit), 2-bit and 3-bit packed, both bit orders | 4 MiB | 0 semantically valid hits (1 high-entropy false positive at `0x23D1A4`, in compressed data) |
| Runs of ≥6 single-button u16 masks (generic button-code table scan) | 4 MiB | none plausibly a code table (hits were graphics/script data) |
| Chains of ≥5 `cmp #1/#2` (sequential-validator signature) | Thumb-disassembled 4 MiB | none tied to the input state |
| PC-relative literal loads of input state (`0x030015DC/E0/E4/B0`) | 4 MiB | 54 code sites; all are menu/movement handlers, the input driver, or save-data packing — none a code validator |
| Known cheat RAM addresses as u32 literals | 4 MiB | 0 hits (accessed via base+offset) |

**Validator model:** none exists. The only whole-state button predicate is `held & 0xF == 0xF` at `0x0800997C` (all four directions → reset); it is a single-mask test, not a code sequence, and does not read `BBABBABBAAAAB` or `BAABAACA`.

**Novel code generation / bounds-by-rejection:** not applicable — there is no code system to mint a value for. Bounds are proven instead by (a) the menu item count of 3, (b) zero literal/table/validator hits across the search space above, and (c) in-game rejection: both published sequences produced no RAM change and no state change on every screen tested. A debug reset (documented above) is the sole developer-intended trigger found and was confirmed live.

**Conclusion:** the accepted code set is the empty set for a sequential password/cheat entry surface; the only in-game button trigger is the all-directions reset. This is a **negative result about the searched space**, not "not tested".

## 7. Validation evidence

* **Observed:** every screen transition and HUD state captured by screenshot; the all-directions reset reproduced twice; no effect from either published code in any screen; 512-byte `.sav` created by New Game (EEPROM-sized save).
* **Derived:** crt0 main pointer; input state addresses; menu bound 3; text encoding; debug reset chain; string pointer table; text bank decode; generic search counts.
* **Inferred:** `C` in `BAABAACA` most plausibly denotes a D-pad direction ("Control"); all four D-pad directions were tried for it with no effect. The second embedded header at `0x1D1D60` is inferred to be a checksum/reference copy of the retail header.

## 8. Unknowns

* Why the "SELECT LEVEL" label survives in the text bank while the retail menu is bounded to 3 entries — most likely a cut feature from a build that exposed a fourth option; no reachable index or dispatcher branch enables it.
* Whether the published codes belonged to a different prototype/build of the game, or were simply misreported by the cheat sites. The literal strings are absent from this exact revision (hash in §1).
* Whether a code surface exists behind a save-file flag (not reachable from a fresh retail boot in the time available); the `.sav` was created fresh and contains no obvious code field.
* Effects of the CodeBreaker RAM addresses were not used as in-game cheats (out of scope); they served only as RAM anchors.

## 9. Tooling

* `strings -t x`, `grep -abo`, `xxd`, Python 3 (`struct`, `zlib`, `capstone` 5.0.7), `arm-none-eabi-objdump -M force-thumb/-force-arm`, `gdb-multiarch`, mGBA 0.10.5 (`-3`, `-g`, `-d`), Xvfb + openbox on `:316`, `xdotool`, `scrot`, ImageMagick.
* REA MCP (Ghidra 12.1.4, raw-binary ARM import at `0x08000000`) used for `procedure_pseudo_code` / `xrefs` / `read_bytes` on the menu and input functions.
* Local scripts in `/tmp/shrekhassle/`: `key.py` (input helper), `find_ldr.py` (PC-relative literal scanner), `blscan.py` (BL scanner), `scan_input_cmp.py`, `scan_cmpchain.py`, `decode_text.py` / `decode_all.py` (font/text-bank decoder), `ssdiff.py` / `ssdiff2.py` (mGBA `gbAs` savestate RAM diff), `dbg_server.py` / `dbg.py` (mGBA `-d` pty bridge).
* Legal note: no ROM bytes or copyrighted assets were redistributed; only hashes, addresses, algorithms, and original analysis are published.

---

*Report written for queue position 39 (resumed). Coordinator-only files (`roms/INDEX.md`, `GBA_REVERSE_ENGINEERING_GUIDE.md`) were not modified.*
