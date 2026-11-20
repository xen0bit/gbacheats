# Tiger Woods PGA Tour 2004 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tiger Woods PGA Tour 2004.gba` (16,777,216 bytes / 16 MiB) |
| Header title | `TIGERWOODS04` |
| Game code | `BTWE` (USA) |
| Maker | `69` (EA) |
| Revision | `0x00` |
| Version byte | `0x45` at `0xBC` |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock ARM crt0, no cracktro) |
| MD5 | `aa571c3f25128f4b1cbfac89a7ae5d99` |
| SHA-1 | `89f93bf10314c4094a96036b4f5df95e7d80b37c` |
| SHA-256 | `1fd3e381d002f0c2b1becd3fee6599b48f5a7781c14a24bb0414ad1aa07db9fe` |
| Save type | Flash (career data; `.sav` created by mGBA) |

## 2. Executive summary

**Result: bounded negative for a reachable in-game code system.** This EA Sports GBA title has a
large, fully enumerated UI text bank containing several strings that look like cheat/password /
debug features — `"Enter Password"`, ten debug-menu labels (`AutoTest`, `Skeleton Key`,
`Access Locked Items`, `Access Debug Features`, `FIXED SHOT`, `Set Shot Power`, …), and a
`"Debug Speed Golf"` game-mode label. However, after walking **every reachable screen** from a
fresh boot (6 main-menu sections, 4 career sub-screens, 3 practice sub-screens, the tutorial
syllabus, the versus flow through gameplay, options, and the GameCube-link path) and after an
exhaustive button-combination scan, **no password entry screen, button-code validator, or debug
menu was reachable**. The `"Enter Password"` string groups with link-mode strings in the text
table and is most plausibly a GameCube/GBA link feature; the debug labels have no reachable
caller on any screen exercised. The unlockables present in the game are gated behind an
external Nintendo GameCube link cable (`"Unlock with GameCube Link"`) or normal career
progression, not an input code.

No GameShark / CodeBreaker / Action Replay codes are reported; none were used.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`) under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`,
  `-3` scale.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys.
* From a cold boot: press Start through the EA/TW/legal splash → Main Menu.
* Main-menu items (top to bottom): **Practice Mode, Career Mode, Tutorial, Versus Mode,
  Options, GameCube Link**.
* Screenshots of every state are in `/tmp/opencode/tiger2004/` (`mm*.png`, `m1.png`…`m6.png`,
  `career_*.png`, `practice.png`, `pm_d*.png`, `versus*.png`, `options*.png`, `linkmode.png`,
  `gc2.png`, `vs_step*.png`, `boot_*.png`).

### Screen-walk ledger (all Observed)

| # | Screen | Evidence | Code/password surface found |
|---:|---|---|---|
| 1 | EA/TW/legal splash → Main Menu | `mm5.png`, `title.png` | none |
| 2 | Practice Mode → Select Golfer (6 golfers, 1 `LOCKED`) | `practice.png`, `golfer_r*.png` | none |
| 3 | Practice Mode → Stroke Play / Any Hole / Putting Practice | `prac_modes.png`, `pm_d*.png` | none |
| 4 | Career Mode → Career Select (3 `-EMPTY-` slots, `-ERASE-`) | `career_sel.png`, `options_scr.png` | none |
| 5 | Career Mode → Select Golfer → New Player Name (keypad A–Z, 0–9, DONE, ←) | `career_main.png`, `keypad_done.png`, `name_entry_again.png` | **name-entry keypad only** — text label, not a validator (see §8) |
| 6 | Career Mode → Buy Attributes → Career Play | `attr_afterA.png`, `attr_start.png` | none |
| 7 | Career Play → Tournaments / Scenarios / EA Sports Crown (`-- LOCKED --`) | `cp_d*.png` | progression gate only |
| 8 | Tutorial → Tutorial Syllabus (8 lessons) | `m6.png`, `now2.png` | none |
| 9 | Versus Mode → 2/3/4 Player → Link Mode | `versus.png`, `versus2.png` | none |
| 10 | Versus → golfer select → Select Course → Course Options (TEE/PIN/WEATHER/WIND) → Passaround | `v2.png`, `v3.png`, `vs_step*.png` | none |
| 11 | Options → Music / Sound / Ambiance / Reset All Data / Game Credits | `options_scr.png` | none |
| 12 | GameCube Link → Career Select (requires link cable) | `gc2.png`, `linkmode.png`, `"Waiting for link"` | hardware-gated only |

### Button-code scan (Observed)

* All 25 two-button and all 20 three-button combinations of {A,B,L,R,Start,Select} pressed
  simultaneously and held 350 ms on the Main Menu, each from a fresh savestate: **no screen
  change beyond ordinary menu navigation** (script `combos.py`, screenshots `combo_*.png`).
* 15 boot-hold combinations (including L+R, L+R+Start, L+R+Select, Start+Select, A+B,
  A+B+Start+Select, L+R+A+B, L+R+A+B+Start+Select) held from power-on for 1.5 s: **no debug
  menu** (script `bootcombos.py`, screenshots `boot_*.png`).

## 4. Address map

| Item | Address (ROM) | File offset | Notes |
|---|---|---|---|
| Header | `0x08000000` | `0x000000` | stock ARM entry `0xEA00002E` |
| UI text-bank pointer table | `0x08F2E27C`–`0x08F2EA60` | `0xF2E27C` | **505 entries**, 4-byte ROM pointers (id = (ptr − table)/4). Dumped in full. |
| `"Enter Password"` | `0x081024A4` | `0x1024A4` | table id **188** |
| `"Really quit?"` / `"Yes"` | `0x08103C1C` / `0x081024A0` | `0x103C1C` | ids 187 / 186 |
| Link-mode cluster | `0x081024A4`–`0x081024F4` | `0x1024A4` | ids 188–194: Enter Password, Multiple Game Paks, Link Type, Select Game, … |
| Debug-menu strings | `0x08103B2C`–`0x08103BB8` | `0x103B2C` | ids 489–498: AutoTest, Automatic Play, Coordinates, Display Ball Loc, Skeleton Key, Access Locked Items, DEBUG, Access Debug Features, FIXED SHOT, Set Shot Power |
| `"DEBUG : Last Shot"` | `0x08103AC0` | `0x103AC0` | id 482 |
| `"Debug Speed Golf"` | `0x08102FF4` | `0x102FF4` | ids 355 & 356 (duplicated) |
| `"Unlock with GameCube Link"` | `0x08105C5C` | `0x105C5C` | xrefs `0x8033B40`, `0x8034338`, `0x8034BD4`, `0x8035280`, `0x80357E4` |
| `"NINTENDO GAMECUBE BONUSES UNLOCKED"` | `0x0810584C` | `0x10584C` | xref `0x805BB00` |
| `"BONUSES UNLOCKED"` | `0x081058C8` | `0x1058C8` | xref `0x8025804` |
| `"Unlock:"` | `0x081066C0` | `0x1066C0` | xrefs `0x805555C`, `0x80557F4` |
| Keypad text bank (copied to EWRAM) | `0x08105820` (len `0x9600`) → `0x030002A0` | `0x105820` | set up by `FUN_0801F470` (`0x0801F470`); string-ID vector at `0x0300048C` |
| Key-input reader | `0x0804B228` | `0x04B228` | reads `KEYINPUT` at `0x04000130` via literal at `0x0804B26C`; callers `0x80048C4`, `0x8026C3E/42`, `0x80497DC/806` |

File offset ↔ ROM address: `addr = 0x08000000 + offset` (flat 16 MiB image, single header).

## 5. Algorithm

No password validator, checksum, or button-code matcher was located, so there is no algorithm
to reimplement. The one input transform found is the generic **name-entry keypad**: grid
`← | 0-9 | DONE` / `A-M` / `N-Z`, one character per A press, B = cancel. Its buffer stores
plain ASCII (`"AAAA"` observed in an mGBA savestate at EWRAM offset `0x0D94`, i.e.
`0x02000D94`). It is consumed as a career profile label; no `strcmp`/fixed-candidate
comparison against this buffer was found, so per guide §16.2b it is a **text field, not a
password field**.

The text-rendering path is: `FUN_0801F470(ctx, bank, id)` reads a u16 ID from the vector at
`0x0300048C` and indexes the text bank copied from `0x08105820` into `0x030002A0`. UI menus
reference text by these IDs, which is why literal pointer xrefs from code to the strings are
absent.

## 6. Tables

### 6.1 Full UI string-table categories (505 entries, ids 0–504)

The table at `0x08F2E27C` was dumped end-to-end. Representative ranges:

| Id range | Content |
|---|---|
| 0–185 | Main UI, menus, tutorial text, golfer/course/tournament names |
| 186–194 | Generic dialog/menu labels: Yes, Really quit?, **Enter Password**, Multiple Game Paks, Link Type, Select Game |
| 195–340 | Link messages, results, HUD, career/stat labels |
| 341–356 | Versus game types: Capture, T-I-G-E-R, Target, Target-2-Target, Timed, Speed Golf, Race To the Pin, **Debug Speed Golf** (ids 355 & 356) |
| 357–488 | Career challenge names, scenario descriptions, records, hole IDs (`BAY01`…`HIG18`) |
| **489–498** | **Debug menu**: AutoTest, Automatic Play, Coordinates, Display Ball Loc, Skeleton Key, Access Locked Items, DEBUG, Access Debug Features, FIXED SHOT, Set Shot Power |
| 499–504 | Really Quit?, Game Over, English, Complete, Goal/Name Hole 1, Communication Error |

### 6.2 Debug-menu label inventory (all 10)

Every string is present at `0x08103B2C`–`0x08103BB8` with a pointer-table entry
(`0x08F2EA20`–`0x08F2EA44`). None was displayed by any reachable screen in this engagement.

### 6.3 Input masks

`KEYINPUT` (`0x04000130`) is active-low; the sole reader found (`0x0804B228`) computes
`held = KEYINPUT` and `pressed = held & ~prev` via `mvns`/`bics`. No code table of button
masks was found for any of the 8 common combinations searched as little-endian u16
(`0xFCFF`, `0xFFF3`, `0xFCF7`, `0xFCFB`, `0xFFFC`, `0xFCFC`, `0xF3F3`, `0xFFF0`, `0xFFBF`,
`0xFFC0`): all hits were ordinary instructions/data in code, not contiguous mask sequences.

## 6b. Enumeration

This engagement is a **bounded negative**, so the enumerated space is the *search space
checked*, not a code family.

| Dimension | Count | Result |
|---|---|---|
| Reachable top-level menu sections | 6 | walked, 0 code entry points |
| Reachable sub-screens (golfers, career, tutorial, versus, options, link) | 12 categories | walked, 0 code entry points |
| Main-menu 2-button combos | C(6,2)=15 | 0 debug/cheat screen |
| Main-menu 3-button combos | C(6,3)=20 | 0 debug/cheat screen |
| Boot-hold combos | 15 | 0 debug menu |
| UI string-table entries examined | **505** | 1 `"Enter Password"` (id 188), 10 debug labels (489–498), 1 `"Debug Speed Golf"` (355/356) — all unreachable |
| Uppercase/digit 4–10-byte strings in code region (`< 0x800000`) | **786** | all game text / status labels / debug labels; no code table |
| Button-mask constants searched | 10 | no contiguous cheat table |
| Key-input callers found | 5 | all ordinary menu/gameplay input |

**Novel code:** none can be minted because no generator or validator exists in the enumerated
space. In accordance with §0.2's negative-result clause, absence is proven here as a statement
about the enumerated screen space and the ROM's complete UI string table, not as an unchecked
claim.

**Rejection bounds:** not applicable (no code to reject). The nearest bounded observations are:
* `"-- LOCKED --"` on EA Sports Crown (`cp_d8.png`) — a progression gate, not an input gate.
* `"Waiting for link"` in Link Setup (`linkmode.png`) — an external-hardware gate.
* `LOCKED` golfer portrait (`practice.png`) — an unlockable gated by career state.

## 7. Validation evidence

* **Observed**: emulator screenshots (listed in §3); `"AAAA"` in the name-entry buffer at
  savestate EWRAM `0x02000D94`; all 505 string-table entries dumped by pointer walk; every
  screen transitioned via XTEST keys verified against the rendered image.
* **Derived**: table id arithmetic (`id = (ptr − 0x08F2E27C)/4`); text-bank copy destination
  `0x030002A0`/vector `0x0300048C` from `FUN_0801F470` disassembly/key-input reader semantics
  from `0x0804B228`.
* **Inferred**: `"Enter Password"` belongs to a link-mode feature (grouping with ids 189–194);
  the 10 debug labels are leftover debug code rather than a reachable menu.
* **Unknown**: whether a GameCube link cable plus the 2003 NGC game would expose the password
  screen or the unlock bonuses; no NGC hardware was available.

## 8. Unknowns

1. **Why `"Enter Password"` exists.** No screen in the single-player game displays it. It is
   adjacent to link-mode strings in the table; a link-cable-only screen is the leading
   hypothesis, but it was not exercised (hardware gate).
2. **Debug-menu gate.** The 10 labels have ROM pointers but no discovered activation path.
   mGBA's CLI/GDB debugger proved unreliable for live RAM reads in this environment
   (`continue` stalls the stub), so a gate byte could not be forced and observed. The negative
   is therefore limited to the enumerated retail input surface.
3. **`"Debug Speed Golf"`** (ids 355/356) may be a developer-only game type selectable via a
   link-mode menu; not reached.
4. The name-entry keypad was tested only as a profile label (per §16.2b no validator consumer
   was found for its buffer).

## 9. Tooling

* `scan.py` — pointer, Thumb-LDR-literal, BL-target scanners and hex dump/disassembler
  (`capstone`, `arm-none-eabi-objdump -M force-thumb`).
* `table.py`, `findids.py`, `near.py`, `idhits.py` — UI string-table walker and id/xref searches.
* `press.py`, `combos.py`, `bootcombos.py` — XTEST input automation on Xvfb `:317`.
* `ss.py` — mGBA `.ss*.png` → raw 397,312-byte `gbAs` state extractor (used to locate the
  name-entry buffer by diffing savestates).
* REPL-based REA/Ghidra session (shared with other agents) for pseudo-code of
  `FUN_0801F470` and string/xref checks; `close_binary` issued when switching targets.

### Web reconnaissance (blocked — recorded)

GameFAQs `…/gba/561998-tiger-woods-pga-tour-2004/cheats` returned HTTP 403 to `webfetch` and a
Cloudflare "Verify you are human" challenge in `agent-browser`; Google returned a reCAPTCHA;
Bing/DuckDuckGo returned animal results for the game title. **No published code list could be
retrieved**, so there is no public list to verify against. This is recorded as an environment
limitation, not a claim that no codes are published.

## 10. Legal note

No ROM bytes, graphics, music, or game text are redistributed here. Only hashes, addresses,
algorithms, counts, and the analyst's own scripts/screenshots are published. Screenshots are
analysis artifacts in `/tmp/opencode/tiger2004/` and are not part of the deliverable.

## 11. Cleanup

Emulator and display processes started for this engagement (PIDs recorded in
`/tmp/opencode/tiger2004/mgba.pid`) were terminated by PID number; Xvfb `:317` and its openbox
were terminated by PID number. No `.sav`/`.ss*` files remain in the ROM folder (all savestates
were created in `/tmp/opencode/tiger2004/`).
