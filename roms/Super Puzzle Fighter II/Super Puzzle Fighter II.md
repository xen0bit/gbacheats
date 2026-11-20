# Super Puzzle Fighter II (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Super Puzzle Fighter II/Super Puzzle Fighter II.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| `file` | Game Boy Advance ROM image: `"PUZZLEFIGHT2" (AZ8E08, Rev.00)` |
| Header title | `PUZZLEFIGHT2` (ASCII @ `0xA0`) |
| Game code | `AZ8E` — USA | maker `08` (Capcom) |
| Fixed byte | `0x96` @ `0xB2`; unit `0x00`; device `0x00` |
| Version | `0x00` @ `0xBC`; complement `0x43` @ `0xBD`; checksum `0x0000` @ `0xBE` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock Capcom crt0, no cracktro/trainer found in first 4 KiB) |
| MD5 | `14d0771c15676e2b3b75c4c149879586` |
| SHA-1 | `801df7f69fc574a17e8c5efce6ca18ae5749aa97` |
| SHA-256 | `9f7f7ee2245051ed4f22ff82b84776a06b5fd4b1a0574acb974b7b1f754a6d2d` |

This is a single-image retail ROM (one Nintendo logo / one header), not a multiboot stub or 2-in-1 pack.

## 2. Executive summary

**The GBA SKU does contain developer-intended in-game cheats.** Unlike the arcade/PS2 versions, the GBA image ships a complete ASCII text bank with a `GOODIES` main-menu page, a `SECRET CODES` sub-page, an eight-entry button-code table, and a hidden `LEVEL SELECT` / `MODE SELECT` debug screen. This is a genuine in-game code surface; no GameShark/CodeBreaker/AR data was used or is reported.

What was established:

* The text bank at `0x08355014`–`0x0835578B` is **plain ASCII** (not tile-index encoded). It contains the full Goodies menu, all eight code hint strings, the debug screen labels, and the complete main-menu item list. Decoding it removed the "no text = no codes" trap (guide §11 / §16).
* An eight-record button-code table lives at **`0x083550C7`**, 16 bytes per record: 13 button-index bytes (`0`–`7`) + `0x09` terminator + `00 00`. It is referenced exactly once, by the Goodies-screen glyph loader at `0x08008A00` (literal at `0x08008A44`).
* The Goodies/main-menu machinery is fully mapped statically: 7 menu strings at `0x08008D10`, the main-menu drawer at `0x08009F40`, the main-menu input handler at `0x08009988` (cursor mask `0x00C0`, confirm mask `0x0009`), the title input helper at `0x08009E68`, and the scene dispatch table at `0x08355590` (main menu = scene 39/40).
* A hidden debug `LEVEL SELECT` / `MODE SELECT` screen exists at `0x08378AD0`, drawn by the handler at `0x0801DF94`, gated by a byte at scene-state `+0x77`.
* **No novel code was minted and accepted in-game.** The GOODIES screen could not be reached by retail input within this session: the title → level-select → player-select → gameplay path is fully reproducible, but the main-menu (scene 39) entry was not found. Per guide §0.2 this is reported as a **bounded negative with counts**, not as "no cheats". All eight codes are enumerated below from the table itself (a closed set), and the exact gaps are named in §8.

Published codes were recon'd early (GameFAQs GBA page, StrategyWiki, IGN, the PS1 manual hosted on gamegear.net). Most widely circulated codes (Akuma `D,D,D,L,L,L+A` from Morrigan, Dan, Devilot, Anita, Mei-Ling) are for **arcade/PS/Saturn/DC**; the GBA FAQ repeats only the "highlight Morrigan, hold Select, Down×3, Left×3, A" style entries. **None of those literal button strings appear in this GBA image in any encoding searched** — consistent with this implementation storing codes as short button-*index* records rather than as ASCII or u16 masks.

## 3. How to reproduce

* Emulator: `mgba 0.10.5` under `Xvfb :315` (own server + openbox), `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.
* Keymap used (XTEST events sent with `xdotool key[down|up] --window <mGBA window>`): `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, D-pad = arrow keys. Input was verified at the hardware level by savestate diff: KEYINPUT shadow at raw-state offset `0x530` changes `0x03FF → 0x03F7` while `Return` is held (Start = bit 3, active low).
* Boot is slow under Xvfb: CAPCOM logo ≈ 10–15 s, `PRESS START` title ≈ 26–29 s from launch.
* Reproducible screen path: title → press **Start** (the first press is often eaten by the attract skip; press 2–3 times) → `LEVEL SELECT 1/2` (EASY/NORMAL/HARD, 19 s countdown; Left/Right changes difficulty) → **Start** → `PLAYER SELECT` (8 portraits, 2×4) → confirm → character intro → match → attract demo / `SCORE RANKING`.
* Savestates: `Shift+F1` saves slot 1, `F1` loads. **Caution:** a state saved while the attract loop is showing the title reloads into a title that ignores a single Start press; use 2–3 presses or a clean boot. mGBA's GDB stub (`-g`) was tried first and proved unreliable here (the emulator exited after a batch GDB attach); the CLI debugger (`-d`) works but halts rendering while stopped. Savestate diffing is the reliable RAM-evidence path.
* No `.sav`/`.ss*` files were left in the ROM folder (see Cleanup).

## 4. Address map

File offset = ROM address − `0x08000000`.

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` | code | stock crt0 entry |
| `0x08008868`, `0x08008D18` | pointers | xrefs to `"SECRET CODES"` |
| `0x08008D10` | table | 7 Goodies-menu string pointers (`GOODIES`, `INTERMISSIONS`, `SECRET CODES`, `AKUMA - +`, `SOUND TEST`, `TEAM PHOTO`, `EXIT`) |
| `0x0800896C` | code | Goodies item dispatcher; reads selected index at `[state+0x2B]`, indexes pointer table `0x08355438` |
| `0x08008A00` | code | Goodies-screen code-glyph loader; `r2 = 0x083550C7`, reads two bytes per call, advances index at `[r2+0x2C]` by 2 |
| `0x08008A44` | literal | `0x083550C7` — the only pointer to the code table in the whole image |
| `0x080090E0` | code | scene frame dispatcher; `[state+0x0C]` = scene id; table `0x08355590` |
| `0x08009900` | code | main-menu scene init (gates on global `[+0x44]` and `[state+0x49]`) |
| `0x08009988` | code | **main-menu input handler**: mask `0x00C0` (Up/Down) moves cursor in `0..8`, skips locked items 4 and 5; mask `0x0009` (A\|Start) confirms, writes selected index to global `0x02000494` |
| `0x08009F40` | code | main-menu drawer; draws 9 items from table `0x083556E0` (index 6 = `GOODIES`) |
| `0x08009E68` | code | generic confirm helper: tests mask `0x0009` on `[0x03002D86]` (P1) and `[0x03002D96]` (P2) |
| `0x0801DF94` | code | hidden debug `LEVEL SELECT`/`MODE SELECT` drawer; gate byte at `[state+0x77]`; draws string ids 7..14 from `0x08378B10` |
| `0x03002D80` / `0x03002D90` | RAM | input structs P1/P2: `+2` held, `+4` previous, `+6` pressed (edge), `+8` released; written by routine at `0x0802D930` |
| `0x030045A0` | RAM | scene-state struct observed at a breakpoint in the dispatcher (id at `+0x0C`); address is runtime-allocated, not a fixed constant |
| `0x08355014`–`0x0835578B` | data | decoded ASCII text bank (Goodies, main menu, code hints) |
| `0x083550C7` | data | **8 × 16-byte button-code table** (§6) |
| `0x08355438` | table | 7 Thumb handlers for Goodies pages: `0x080189B1`, `0x08018A01`, `0x08018A49`, `0x08018A6D`, `0x08018A95`, `0x08018AD5`, `0x08018B2D` |
| `0x08355590` | table | scene main-handler table; index 11 = title-ish handler `0x08009269`, 39/40/41 = main menu (`0x08009901`/`0x08009989`/`0x08009AC9`) |
| `0x083556E0` | table | main-menu strings: 0 `MAIN MENU`, 1 `ARCADE MODE`, 2 `STREET PUZZLE`, 3 `VERSUS MODE`, 4 `LINK BATTLE`, 5 `MASTER ARCADE`, 6 `GOODIES`, 7 `TRAINING DEMO`, 8 `OPTION`, 9 `ERASE GAME DATA` |
| `0x08378AD0` | data | debug `LEVEL SELECT  `, ` MODE SELECT  `, ` STAGE `, ` FINAL `, `SELECT`, `PLAYER` |
| `0x02000494` | RAM | selected main-menu index written by `0x08009988` |

## 5. Algorithm

**Input pipeline (observed + derived).** Hardware KEYINPUT (`0x04000130`, active-low) is converted to two active-high P1/P2 structs at `0x03002D80`/`0x03002D90`. The routine at `0x0802D930` performs the standard edge extraction:

```
held   = ~KEYINPUT & 0x3FF
pressed  = held & ~prev            -> [struct+6]
released = prev & ~held            -> [struct+8]
prev   = held                      -> [struct+4]
```

Button bit numbering (GBA standard): `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`.

**Generic confirm gate** at `0x08009E68`:

```
if ((p1_pressed | p2_pressed) & 0x0009) != 0:   # A or Start
    state[0x3B] |= (p1?1:0) | (p2?2:0)
    play_sound(0x156); state[0x0C]=1; state[0x10]=0; sub_scene_change(2)
```

**Main-menu cursor/gate logic** at `0x08009988`: OR of P1/P2 *pressed* masks; `0x0080` (Down) increments index with wrap `if idx>8: idx=0`; `0x0040` (Up) decrements with `if idx<0: idx=8`. Items 4 (`LINK BATTLE`, gated by a byte read via pointer at `0x08009AB0`) and 5 (`MASTER ARCADE`, gated by `has_prizes()` at `0x0800A078`, which ORs save words `+12`,`+16` and bytes `+20..+26`) are skipped by adding the step direction again. Confirm mask `0x0009`.

**Goodies code-glyph loader** at `0x08008A00` (derived):

```
idx = [state+0x2C]                 # byte, advanced by 2 each call
b0 = *(u8 *)(0x083550C7 + *(s8 *)(state+0x2C))
b1 = *(u8 *)(0x083550C7 + *(s8 *)(state+0x2C) + 1)
[out+0x35] = b0                    # glyph/text field
[out+0x0C] = b1                    # second field
[state+0x2C] = idx + 2
```

**Code-table record format (derived from the bytes):**

```
record_size = 16
code[0..12] : button index 0..7      # 13 presses
code[13]    : 0x09                   # terminator / end marker
code[14..15]: 0x00 0x00              # padding
```

This is a **lookup table**, not a checksum system: there is no generator/validator checksum in the code table itself. The 13 button values are consumed in order; the `0x09` marker ends the sequence.

## 6. Tables

### 6.0 Goodies menu strings (pointer table `0x08008D10`)

| # | String | Address |
|---|---|---|
| 0 | `GOODIES` | `0x08355014` |
| 1 | `INTERMISSIONS` | `0x0835503C` |
| 2 | `SECRET CODES` | `0x0835509C` |
| 3 | `AKUMA   -  +` | `0x0835502C` |
| 4 | `SOUND TEST` | `0x08355048` |
| 5 | `TEAM PHOTO` | `0x083550BC` |
| 6 | `EXIT` | `0x08355058` |

Other Goodies strings: `DAN     -  + +` (`0x08355070`), `DEVILOT -  +` (`0x08355080`), `VOICE` (`0x08355060`), `BGM`/`SE` (`0x08355067`/`0x0835506B`), `ORIGINAL SONG` (`0x083550AC`), `PRESS   TO` (`0x08355090`).

Explanatory sentence (pointer fragments at `0x083553D8`): `"ENTER THESE CODES ON PLAYER"` + `"SELECT SCREEN IN EITHER ARCADE"` + `"VS, OR MASTER ARCADE MODE."`

### 6.1 The eight secret codes (complete table at `0x083550C7`)

Each row is the 13 button-index bytes (values `0`–`7`); all rows end in `09 00 00`. Raw table spans `0x083550C7`–`0x08355146` (128 bytes).

| # | Start addr | 13 button indices (hex) | Terminator |
|---|---|---|---|
| 0 | `0x083550C7` | `00 01 01 00 02 03 03 04 04 07 05 04 06` | `09 00 00` |
| 1 | `0x083550D7` | `03 04 05 01 00 02 02 00 01 03 04 06 06` | `09 00 00` |
| 2 | `0x083550E7` | `05 04 03 07 01 05 04 03 02 02 00 01 06` | `09 00 00` |
| 3 | `0x083550F7` | `04 07 02 02 03 04 00 06 01 01 05 03 06` | `09 00 00` |
| 4 | `0x08355107` | `02 03 00 05 05 07 01 01 03 00 04 02 06` | `09 00 00` |
| 5 | `0x08355117` | `01 05 04 03 02 00 05 02 00 04 03 07 06` | `09 00 00` |
| 6 | `0x08355127` | `00 01 01 05 02 06 03 01 04 02 05 04 06` | `09 00 00` |
| 7 | `0x08355137` | `04 07 00 01 03 04 02 03 05 04 01 00 06` | `09 00 00` |

The index→button mapping (which of the eight GBA buttons each value `0..7` denotes) was **not** proven; the on-screen glyphs that would settle it are drawn by the `0x08008A00` path, which was not reached. No published list contains these byte records, so the *bit pattern* of all eight is novel as documentation even though the underlying in-game codes are developer-shipped.

### 6.2 Published codes — verification status

| Source | Code / claim | Verification against this ROM |
|---|---|---|
| GameFAQs GBA cheat page | P1 highlight Morrigan, hold Select, D×3, L×3, A → Akuma | Entered at player select: **not accepted** (Ryu vs Ryu match started). Likely wrong character position or GBA-specific variant; recorded as unverified. |
| GameFAQs / StrategyWiki / IGN | Dan, Devilot, Anita, Mei-Ling (mostly PS/arcade/DC forms) | Literal u16 button-mask searches for `DDD LLL A`, `LLL DDD A`, `DDD RRR A`, `RRR DDD A` all returned **0 hits** in the ROM. |
| PS1 manual (`gamegear.net`) | Mode Select with Goodies; Goodies appears after winning a Street Puzzle prize | Structural analogue confirmed in GBA ROM (Goodies menu + prize-gated `MASTER ARCADE` at `0x0800A078`), but GBA menu item 6 `GOODIES` itself is drawn unconditionally by `0x08009F40`. |

### 6.3 Hidden debug screen

`0x08378AD0`: `LEVEL SELECT  `, ` MODE SELECT  `, `LEVEL SELECT `, ` MODE SELECT `; `0x08378B4C`: ` STAGE `, `  FINAL `; `0x08378B5C`: `SELECT`, `0x08378B64`: `PLAYER`. Drawer at `0x0801DF94`, gate byte `[state+0x77]`. This is a real screen in the image (strings + handler + its own pointer table at `0x08378AB0`), not a dead string.

## 6b. Enumeration

**Space definition (complete for the implementable table):**

* **Records:** exactly **8**, each **16 bytes**, at `0x083550C7` + `16·i`. Total **128 bytes**. The table terminates at `0x08355147`; the next word (`0x08355148`) begins a pointer block to compressed graphics (`0x087CF97C`, …), so no 9th record exists.
* **Alphabet:** 8 symbols, byte values `0x00`–`0x07` (13 slots per code), plus one fixed terminator `0x09` and two zero-pad bytes. No byte in `0x08`, or in `0x0A`–`0xFF`, occurs anywhere in the 128-byte table — this is the format's hard bound.
* **Representable codes:** `8^13 = 549,755,813,888` possible 13-press strings *in principle*, but the ROM implements a **closed lookup set of 8**; there is no checksum field, no generator, and no algorithmic decoder in this table. The Goodies loader reads the table by index; it does not compute codes.
* **Alternative formats checked:** ASCII and `+0x20` shifts (full ASCII text bank decoded above), UTF-16LE/BE and UTF-32 (no code-like hits in the text bank), u16 active-low button masks (4 published sequences → **0 hits**), and 16-bit alphabets / local pointer tables (one and only one reference to the code table: `0x08008A44`). Keyword hits for `code`, `secret`, `password` outside the decoded bank were either the Goodies strings themselves or compressed graphics — no second code system was found.

**Counts that bound the negative:**

| Check | Count / result |
|---|---|
| ASCII strings in `0x355000`–`0x359700` containing code/menu/debug keywords | 46 (all in the decoded bank; none a literal published password) |
| 16-byte code records in `0x083550C7` table | 8 (exhaustive) |
| Out-of-alphabet bytes inside the 128-byte table | 0 for `0x08`, `0x0A`–`0xFF`; `0x09` appears **exactly 8 times**, always at record offset 13 |
| Raw 32-bit references to `0x083550C7` in the 8 MiB image | 1 (`0x08008A44`) |
| Goodies page handler pointers at `0x08355438` | 7 |
| Published u16 button-mask sequences found in ROM | 0 of 4 |
| Reachable screens walked with screenshots | 6 (title, level select, player select, character intro, match, score ranking/attract) |
| Main-menu (scene 39/40) reached by retail input | **0** — entry path not found |

**Bounded negative statement:** *Within the searched spaces (the 128-byte code table, the 0x355000–0x359700 ASCII bank, all 32-bit references to the code table, and the 4 published mask sequences), the eight records above are the complete shipped button-code set; no ninth code and no second alphabet exist there. A novel code was **not** minted and accepted in-game because the GOODIES screen that displays/uses these codes was not reachable by retail input in this session. This is a bounded negative, not a claim that the game has no cheats — the eight codes and the hidden debug screen are confirmed present in the image.*

**Rejection bounds attempted (recorded, not hidden):**
* `SELECT+START` held together at the default Ryu portrait on `PLAYER SELECT` → no character change (screenshot `hint_select_start.png`).
* Published Akuma sequence entered on `PLAYER SELECT` starting from Ryu with Select held → rejected; a normal Ryu-vs-Ryu match started (`akuma_attempt.png`). Because the cursor never reached Morrigan, this bounds only that specific attempt, not the published code.

## 7. Validation evidence

**Observed (emulator / RAM):**
* Boot → CAPCOM logo → SUPER intro → `PRESS START` title → LEVEL SELECT → PLAYER SELECT → character intro → match → attract/score ranking. Screenshots `w_3.png`, `cs_7.png`, `pc0.png`, `walk_4.png`, `cur.png`, `poll_now.png` in `/tmp/opencode/supersf2`.
* KEYINPUT shadow at savestate offset `0x530`: `0x03FF` idle → `0x03F7` while Start held.
* Savestate `Super Puzzle Fighter II.ss1` decompresses to a 397,312-byte (`0x61000`) `gbAs` chunk; header at `0x0`, IWRAM at `0x19000`, EWRAM at `0x21000` (guide §16.13).
* CLI debugger breakpoint at `0x08009122` hit with `r4 = 0x030045A0`, `lr = 0x0800911B`, confirming the scene-state pointer and dispatcher.

**Derived (instruction sequence):**
* Code-table format and the sole xref at `0x08008A44`.
* Input struct layout and edge extraction at `0x0802D930`.
* Main-menu cursor bounds `0..8`, item skips, and confirm mask `0x0009` at `0x08009988`.
* Scene dispatch table base `0x08355590`; main menu = index 39/40.
* Debug screen gate byte `[state+0x77]` at `0x0801DF94`.

**Inferred (not fully exercised):**
* Button-index → physical-button mapping for values `0..7` (the glyph loader's output was never rendered).
* That the eight records unlock, respectively, the eight Goodies page handlers at `0x08355438`; the table-to-reward association is plausible but unproven.
* That the debug LEVEL SELECT screen is reachable by any retail input; its gate writer was not found (0 `strb` instructions with disp `0x77` found in the first 2 MiB of Thumb code).

## 8. Unknowns

1. **Index→button map and code validator.** The code-glyph loader at `0x08008A00` reads the table but no comparison against player input was located; the character-select validator that consumes these records was not identified. Without it, a code cannot be minted offline.
2. **Main-menu entry.** Scene 39/40 is fully mapped statically, but the retail input path that selects it is unknown. Patching scene-table entry 0 (`0x08009231`) or entry 11 (`0x08009269`) to the main-menu handler on a *copy* of the ROM produced a black screen / unchanged attract flow, so those patches are not a valid substitute for the real path.
3. **Debug screen gate writer.** No code writing the `[state+0x77]` byte was found in the scanned range; the screen may be gated by a save flag or by a debug-only build path.
4. **Code-to-reward assignment.** Which of the 8 records corresponds to Akuma / Dan / Devilot / Sound Test / Illustrations / Team Photo / Original Song / BGM-SE is unresolved.
5. **Published-code discrepancies.** The GameFAQs GBA entry did not work as entered; the correct GBA starting character and hold timing were not determined.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo` for Phase 0/recon.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly; Capstone (Thumb) for literal/BL/xref scans; Python `struct` for pointer scans.
* Helper scripts in `/tmp/opencode/supersf2`: `xrefs.py` (raw + Thumb-PC-relative + ARM-literal xrefs), `ss.py` (mGBA `.ssN` PNG → `gbAs` zlib chunk), `verify_input.py` / `find_keyinput.py` (KEYINPUT discovery via savestate diff), `key.py` (XTEST input), `goto_level.py` / `catch_title.py` / `title_key.py` (screen timing), `dbg.py` + `dbg_server.py` (mGBA `-d` pty bridge), `probe.py` (input-key sweep).
* One throwaway ROM copy, `/tmp/opencode/supersf2/patched.gba`, was used for the failed scene-patch experiments. It contains a 4-byte patch at file offset `0x3555BC`; it is **not** the analyzed ROM and was never placed in the ROM folder.

## 10. Legal note

No ROM image, extracted graphics, music, or game text is redistributed here. Only hashes, addresses, algorithms, and the author's own analysis scripts/screenshots are reported. Fetched web pages were treated strictly as data; no instruction found in a fetched page or in ROM content was followed.

## Cleanup

Emulator, Xvfb, openbox, and debugger processes were stopped by PID number only; no `pkill`/`pkill -f` was used. `Super Puzzle Fighter II.sav`, `.ss1`, `.ss2`, and `.ss3` were removed from the ROM folder.
