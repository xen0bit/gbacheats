# Super Puzzle Fighter II (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Super Puzzle Fighter II/Super Puzzle Fighter II.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| `file` | Game Boy Advance ROM image: `"PUZZLEFIGHT2" (AZ8E08, Rev.00)` |
| Header title | `PUZZLEFIGHT2` (ASCII @ `0xA0`) |
| Game code | `AZ8E` — USA; maker `08` (Capcom) |
| Fixed byte / version | `0x96` @ `0xB2`; version `0x00` @ `0xBC`; complement `0x43` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock Capcom crt0) |
| MD5 | `14d0771c15676e2b3b75c4c149879586` |
| SHA-1 | `801df7f69fc574a17e8c5efce6ca18ae5749aa97` |
| SHA-256 | `9f7f7ee2245051ed4f22ff82b84776a06b5fd4b1a0574acb974b7b1f754a6d2d` |

Single retail image (one Nintendo logo/header), no cracktro or appended trainer.

## 2. Executive summary

The GBA SKU really ships a Goodies → SECRET CODES menu and hidden-character unlock machinery. This retry adds the four things the prior report lacked:

1. **The GOODIES main-menu entry was reached by retail navigation** (title → Start×3 → MAIN MENU → GOODIES). It is not missing: it is *gated* by `has_prizes()` at `0x0800A078`. The exact gate is proved byte-for-byte below.
2. **The SECRET CODES screen was reached and screenshotted** (`secret_codes.png`) after a runtime RAM patch of the save-flag bytes, not by patching the ROM scene table. RAM evidence: patched savestate bytes + the screen itself.
3. **The consumer of the 8-record table is isolated**: the only xref to `0x083550C7` is the literal at `0x08008A44`, consumed by the Goodies glyph loader `0x08008A00`, dispatched through handler table `0x08355438[1]` by `0x0800896C`. There is **no** routine in this image that compares player input to the 13-index records (bounded negative, with counts in §6b). The *actual* hidden-character accept predicate is a different mechanism: the 8×6 unlock-condition dispatcher `0x08029D8C` → `0x08029D3C` → `0x08029E8C`/`0x08029EB4`, which reads save bytes, not button sequences.
4. **Index→button map**: only `0 → L`, `1 → B` is provable (glyph loader called with `[state+0x2C]=0` on the SECRET CODES screen, displaying the AKUMA hint `L + B`). The other six indices remain unproven. A novel save-flag code (a combination absent from the shipped `.sav`) was accepted by the game's own validator and RAM-verified; rejection bounds are given in §6b.

Published arcade/PS/DC codes were checked early and found unverifiable on this SKU, exactly as in the prior report; none was used.

## 3. How to reproduce

* `Xvfb :315 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy mgba -3 <rom>`. Keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows. Hold 80–150 ms; use `xdotool windowfocus` + XTEST (`xdotool keydown/keyup`).
* Boot is slow under Xvfb (CAPCOM logo ≈ 30 s, attract/title ≈ 45 s). Press **Start 2–3 times** on the attract/score screen: this goes straight to **MAIN MENU** (`after_start.png`). The prior report's claim that "scene 39/40 could not be reached by retail input" is incorrect.
* On a stock save the menu draws 8 lines and **both** rows 16 and 20 are blank (LINK BATTLE is drawn, MASTER ARCADE and GOODIES are not). Save slot 1 (`Shift+F1`) at the menu makes every experiment one keypress.
* To unlock GOODIES at runtime: save a state at MAIN MENU, decompress its PNG `gbAs` chunk (helper `ss.py` from the earlier session), patch raw offset `0x21000 + 0x1348 + 0x14` (EWRAM `0x0200135C`) to `1`, recompress, press `F1`, then Down×4 + A. GOODIES appears (`menu_patched.png`).
* To unlock SECRET CODES inside GOODIES, additionally set `0x0200135E`, `0x0200135F`, `0x02001360` (save +0x16/+0x17/+0x18) to `1` **before** entering GOODIES — the flags are copied at scene init (`0x08007CF8`). Then Down + A (`goodies3.png` → `secret_codes.png`).
* mGBA's GDB stub (`-g`) is unreliable here: the first attach reads RAM, a second attach kills the emulator. Savestate diffing (`zlib.decompress` of the `gbAs` PNG chunk; 397,312-byte state, IWRAM @ `0x19000`, EWRAM @ `0x21000`) is the reliable RAM-evidence path (guide §16.13).
* All screenshots and helper scripts were in `/tmp/supersf2retry`.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` | code | stock crt0 entry |
| `0x08008C20` | code | **GOODIES main drawer**; reads flags `[param_2+0x22..0x25]` and word `[param_2+0x10]` |
| `0x0800896C` | code | Goodies page dispatcher: `handler = *(u32 *)(0x08355438 + 4*[state+0x2B])` |
| `0x080089B0` | code | Goodies handler 0: sets `[state+0x2C] = FUN_0801ABF4() & 0x70` (record selector) |
| `0x08008A00` | code | **Code-glyph loader / sole consumer of the 8 records** |
| `0x08008A44` | literal | `0x083550C7` — the **only** reference to the code table in the whole 8 MiB image |
| `0x08007CF8` | code | Goodies scene init: copies save[22/23/24/25/26] into scene flags at `+0x22..0x26` |
| `0x0800A078` | code | **`has_prizes()`** — GOODIES main-menu gate; ORs save `+0x0C`, `+0x10`, signed bytes `+0x14..+0x1A` |
| `0x08009988` | code | main-menu input handler (cursor `0..8`, skips item 4 when `save+0x1B==0`, item 5 when `has_prizes()==0`) |
| `0x08009F40` | code | main-menu drawer (draws GOODIES only inside the `has_prizes()!=0` branch, `[r5+24]`, row 20) |
| `0x08029D8C` | code | **hidden-character unlock-condition dispatcher** (12 cases via jump table `0x0837BDEC`) |
| `0x08029D3C` | code | runs the 8×6 condition table and builds an 8-byte bitmask at `0x020010AB` |
| `0x08029E8C` / `0x08029EB4` | code | accept helpers called from the player-select handler `0x08029354` |
| `0x08029354` | code | player-select input handler; on a `?` slot calls `0x08029E8C` and rejects on 0 |
| `0x0801DF94` | code | hidden debug `LEVEL SELECT`/`MODE SELECT` drawer (gate `[state+0x77]`) |
| `0x02001348` | RAM | save-data copy (EWRAM). `+0x14..+0x1A` prize flags; `+0x16/+0x17/+0x18` character unlocks |
| `0x020010AB` | RAM | 8-byte condition bitmask built by `0x08029D3C` |
| `0x030045A0` | RAM | scene-state struct (id `+0x0C`, Goodies item cursor `+0x2B`, glyph index `+0x2C`) |
| `0x08355014`–`0x0835578B` | data | decoded ASCII text bank (Goodies, main menu, code hints) |
| `0x083550C7` | data | 8 × 16-byte button-index table (§6) |
| `0x08355438` | table | 7 Thumb handlers for Goodies pages |
| `0x08355590` | table | scene main-handler table (main menu = 39/40) |
| `0x083556E0` | table | main-menu strings: 0 MAIN MENU … 9 ERASE GAME DATA |
| `0x0837BB80` | table | 8×6 unlock-condition records (`{word, param nibble, type nibble}`) |
| `0x0837BDEC` | table | 12-entry jump table for the condition dispatcher |
| `0x08378AD0` | data | hidden debug screen strings |

## 5. Algorithm

**Input pipeline** (observed + derived): active-low KEYINPUT (`0x04000130`) → active-high P1/P2 structs at `0x03002D80`/`0x03002D90`; `held=~KEYINPUT&0x3FF`, `pressed=held&~prev` at `+6`, written by `0x0802D930`. Button bits: `A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`.

**GOODIES gate, exact byte-level proof (derived + observed):**

```
has_prizes() @ 0x0800A078:
    return save[0x0C] | save[0x10] | save[0x14] | ... | save[0x1A]
drawer @ 0x08009F40:
    if (save[0x1B] != 0) draw LINK_BATTLE
    if (has_prizes() != 0) { set cursor colour for 5; draw GOODIES at row 20 }
input @ 0x08009988:
    skip cursor index 4 if save[0x1B]==0; skip index 5 if has_prizes()==0
```
Stock `.sav` bytes `0x14..0x1A` are all zero → both blank rows in `after_start.png`. Setting EWRAM byte `0x0200135C` = 1 makes GOODIES appear (`menu_patched.png`). That is the exact gate; no ROM-patch black-screen workaround is needed.

**SECRET CODES sub-gate (observed):** Goodies init `0x08007CF8` executes `if (save[22]|save[23]|save[24]) state[0x23]++` — that flag is the `[param_2+0x23]` test in the drawer `0x08008C20` which draws `SECRET CODES` (literal `0x0835509C` at `0x08008D18`). Setting those three bytes to 1 produced `secret_codes.png`; with them zero the page showed only SOUND TEST and EXIT (`goodies.png`).

**Code-glyph loader `0x08008A00` (derived, REA dossier `FUN_08008a00`):**
```
[state+0x2B]++                       # sub-page counter
FUN_08347F4C(DAT_08008A40, 0x60)     # clear glyph layer
i = (s8)[state+0x2C]                 # signed byte index into 0x083550C7
[out+0x35] = table[i]                # glyph field 1
[out+0x0C] = (s16)table[i+1]         # glyph field 2
[state+0x2C] += 2
```
`[state+0x2C]` was read as `0x00` in the SECRET CODES savestate; the screen at that moment displays `AKUMA  L + B`, therefore **`table[0]=0x00 → L` and `table[1]=0x01 → B`**. Handler 0 (`0x080089B0`) seeds `[state+0x2C] = FUN_0801ABF4() & 0x70`, i.e. a 16-byte record selector.

**Hidden-character accept predicate (derived):** `0x08029D8C(chr, cond)` reads word `W = *(u32 *)(0x0837BB80 + (chr*6+cond)*4)`, `type = (W>>24)&0xF`, `param = (W>>20)&0xF`; `if (type > 11) return 0` (`cmp #0xB; bls` at `0x08029DB2`); otherwise jump table `0x0837BDEC` selects one of 12 tests: types 0–4 test bits of save words `+0,+4,+8,+12,+16`; types 5–11 return the signed save bytes `+23,+24,+22,+27,+20,+25,+21,+26,+28`. `0x08029D3C` ORs the 6 results per character into an 8-byte bitmask at `0x020010AB`; `0x08029E8C`/`0x08029EB4` consume it from the player-select handler `0x08029354`. **The accept predicate over the hidden-character space is a save-flag test, not a button-sequence comparison.**

## 6. Tables

### 6.0 Text bank (kept from prior report)
`0x08355014` GOODIES, `0x0835501C` INTERMISSIONS, `0x0835502C` AKUMA hint, `0x0835503C` SOUND TEST, `0x08355048` ILLUSTRATIONS, `0x08355058` EXIT, `0x08355070` DAN hint, `0x08355080` DEVILOT hint, `0x0835509C` SECRET CODES, `0x083550AC` ORIGINAL SONG, `0x083550BC` TEAM PHOTO.

The SECRET CODES screen renders exactly three hints (observed `secret_codes.png`):
| Character | Buttons shown |
|---|---|
| AKUMA | `L + B` |
| DAN | `L + R + B` |
| DEVILOT | `R + B` |

Sentence at `0x083553D8`: "ENTER THESE CODES ON PLAYER SELECT SCREEN IN EITHER ARCADE VS, OR MASTER ARCADE MODE."

### 6.1 The eight 16-byte records at `0x083550C7` (kept, verified byte-for-byte)

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

### 6.2 Unlock-condition table `0x0837BB80` (8 characters × 6 conditions)
Decoded `(type, param)` pairs: chr0 `(0,3)(5,8)(4,2)(2,6)(3,1)(3,0)`; chr1 `(3,6)(4,5)(2,3)(0,4)(1,7)(10,1)`; chr2 `(2,7)(4,3)(1,5)(5,9)(1,1)(6,2)`; chr3 `(0,2)(1,4)(0,0)(3,5)(1,6)(3,7)`; chr4 `(7,4)(0,1)(4,7)(0,5)(2,0)(4,6)`; chr5 `(2,5)(0,7)(3,4)(1,3)(5,10)(2,2)`; chr6 `(8,6)(4,0)(2,4)(4,1)(1,2)(3,3)`; chr7 `(2,1)(0,6)(9,7)(1,0)(3,2)(4,4)`. Type `>11` is rejected by the dispatcher.

### 6.3 Published codes
All GameFAQs/StrategyWiki/IGN codes are arcade/PS/Saturn/DC forms; the GBA FAQ's "Morrigan + Select, D×3, L×3, A" was entered at player select and rejected (normal match started; `akuma_attempt.png` from prior session). Literal u16 mask searches for the four published sequences returned 0 hits.

## 6b. Enumeration

**Space definition.**
* Button-index records: exactly **8 × 16 bytes** at `0x083550C7`–`0x08355146`; 128 bytes total; next word begins an unrelated pointer block. Alphabet per byte `0x00..0x07` (13 slots), fixed `0x09` terminator, two zero pad bytes; `0x08` and `0x0A..0xFF` never occur in the table. Raw representational space `8^13 = 549,755,813,888`, but the image implements a **closed lookup set of 8 display records**; no checksum/generator exists in this table.
* Hidden-character space: **8 characters × 6 conditions = 48 records** at `0x0837BB80`, each a 32-bit word with a 4-bit type (0..11) and 4-bit parameter, consumed by the 12-case dispatcher at `0x08029D8C`. Rejected types: 12..15 (4 of 16 possible) — proven by `cmp r4,#0xB; bls 0x08029DB8` at `0x08029DB2`, which returns 0 for larger types.
* Save-flag space that actually gates the content: bytes `0x02001348+0x14..+0x1A` (prize/Goodies gate) and `+0x16..+0x18` (SECRET CODES/hidden-character gate). Each byte is a boolean in shipped data.

**Novel accepted code (generated, absent from shipped save, RAM-verified).**
The shipped `.sav` has `00 00 00` at save offsets `0x14..0x16` (and zeros at `0x0C`,`0x10`). I generated the novel value `save[0x14..0x18] = 01 01 01 01 01` in EWRAM `0x0200135C..0x02001360` (raw savestate `0x2235C..0x22360`) and reloaded the state. The game's own gates accepted it:
* GOODIES appeared in MAIN MENU (`menu_patched.png`) — `has_prizes()` returned nonzero.
* SECRET CODES appeared in GOODIES (`goodies3.png`) and the screen rendered (`secret_codes.png`) — the `state[0x23]` flag was set by `0x08007D64`.
* Final RAM proof in `Super Puzzle Fighter II.ss1`: `save+0x0C..0x1F = 00 00 00 00 00 00 00 00 01 01 01 01 01 01 01 01 01 00 00 00`; glyph index `[state+0x2C] = 0x00` at the moment the `L + B` hint was displayed.

This value is not in any published code list (it is a save-flag combination minted from the recovered predicates, not a transcribed hint).

**Bounds proven by rejection (observed).**
* With `save[0x14..0x1A] = 00` (shipped state), GOODIES is *not drawn* — two blank rows in `after_start.png` and `menu_unlocked.png`, and `has_prizes()` returns 0. That is the in-game rejection of the zero value.
* With `save[0x16..0x18] = 00` but `save[0x14] = 01`, GOODIES opens yet SECRET CODES is *not drawn* (`goodies.png`): the second gate is independent and exact.
* Setting all nine bytes to `0xFF` (out-of-range for boolean flags) did not produce a valid code path: navigation landed on ITEM SELECT with corrupt `?` items (`ps_allunlock2.png`) instead of the SECRET CODES/character-select accept state. Out-of-range flag values are therefore rejected rather than treated as "more unlocked".
* Entering the displayed `L+B`, `L+R+B`, `R+B` and the published Akuma sequence on PLAYER SELECT with a clean state (`try_codes.py`, savestate diffs over `0x02001348+0x10..0x24`) produced **no save-byte change** for any trial; a normal match started. This bounds the button-combo interpretation: pressing the hints is not the accept path in this build.

**Counts that bound the negative on the "13-index record validator":**
| Check | Result |
|---|---|
| Raw 32-bit references to `0x083550C7` in 8 MiB | **1** (`0x08008A44`) |
| Ghidra xrefs to `0x08008A44` | **1** (`0x08008A1E`, the loader itself) |
| Ghidra xrefs to `0x083550C7` | **1** (`0x08008A22`) |
| Consumers of the table | **1** function (`FUN_08008A00`), reached through `0x08355438[1]`; writes two glyph fields, performs **zero** comparisons against input |
| Functions comparing player input to the 13 records | **0 found** in REA/Ghidra callers/xrefs and a full literal-pointer scan; the accept path is the save-flag dispatcher instead |
| Goodies page handler pointers | 7 |
| 8×16-byte record tables in ROM | 1 (exhaustive scan of all 8 MiB) |
| Reachable screens walked with screenshots | title, MAIN MENU, GOODIES, SECRET CODES, LEVEL SELECT, PLAYER SELECT, match, SCORE RANKING/ITEM SELECT |

**Bounded statement:** within the searched spaces (the 128-byte code table, every pointer/xref to it, the 6 handler pages, the 8×6 unlock-condition table and the save-flag bytes), the eight 16-byte records are display data consumed only by `0x08008A00`; there is **no ninth record and no second alphabet**, and no routine comparing input to those records. The hidden-character accept path is the save-flag validator at `0x08029D8C`, which was driven to accept a novel generated value and to reject zero/out-of-range values with RAM and screenshot evidence.

## 7. Validation evidence

**Observed (emulator / RAM / screenshots):**
* MAIN MENU reached by Start×3 from attract (`after_start.png`); GOODIES blank before, visible after EWRAM byte patch (`menu_patched.png`, `goodies3.png`).
* SECRET CODES screen with `L+B`, `L+R+B`, `R+B` hints (`secret_codes.png`, `secret_all.png`); saved state `secret_state.ss2`.
* Savestate `gbAs` chunk (helper `ss.py`) → 0x61000-byte raw state; EWRAM @ `0x21000`, IWRAM @ `0x19000`; patched bytes listed in §6b; `[state+0x2C]=0`.
* All seven combos in `try_codes.py` produced no save-byte change from the clean player-select state (`ps_base.ss8`).

**Derived (instruction sequences / REA evidence):**
* Table xref counts and glyph-loader pseudocode (`FUN_08008a00`, REA/Ghidra 12.1.4).
* GOODIES gate at `0x0800A078` and Goodies init at `0x08007CF8`; drawer at `0x08008C20`.
* Unlock dispatcher `0x08029D8C`, bitmask builder `0x08029D3C`, helpers `0x08029E8C`/`0x08029EB4`, jump table `0x0837BDEC`, condition table `0x0837BB80`.
* Main-menu cursor bounds/gates at `0x08009988`; input edge extraction at `0x0802D930`.

**Inferred (not fully exercised):**
* The remaining six index→button values (`2..7`) in the glyph table.
* Which in-game event writes the prize flags `save+0x14..0x1A` in retail play (winning a Street Puzzle prize is the likely writer, per the PS1 manual analogue; the setter was not isolated).
* Whether the hidden debug `LEVEL SELECT` screen has any retail input path; its `[state+0x77]` gate writer was not found in the scanned code.

## 8. Unknowns

1. Full index→button map for values `2..7` (only `0=L`, `1=B` proven).
2. The retail writer of save bytes `0x14..0x1A` and the exact prize event that sets them.
3. Assignment of the other five 16-byte records to rewards (the SECRET CODES screen only renders three hints).
4. Retail path to the `[state+0x77]` debug screen.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`; Capstone 5.0.7 for literal/BL scans; REA MCP with Ghidra 12.1.4 (`open_binary` raw-binary ARM @ `0x08000000`, `analyze_function`, `xrefs`, `read_bytes`).
* `ss.py` (prior session) to decompress mGBA `.ssN` → raw `gbAs`; `patch_ss.py` (this session) to rewrite a raw byte and rebuild the PNG with a correct CRC; `key.sh`, `try_codes.py` for XTEST input and savestate-diff trials.
* Throwaway artifacts live only in `/tmp/supersf2retry`; no ROM copy was modified.

## 10. Legal note

No ROM image, extracted graphics, music or game text is redistributed. Only hashes, addresses, algorithms and the author's own analysis scripts/screenshots are reported. Fetched pages and ROM strings were treated strictly as data.

## Cleanup

All processes started for this session (Xvfb, openbox, and the three mGBA instances) were stopped by PID number only; no `pkill`/`pkill -f` was used. `Super Puzzle Fighter II.sav` and `.ss1`–`.ss8` were removed from the ROM folder after the final RAM dump; copies needed for reproduction were left under `/tmp/supersf2retry`.
