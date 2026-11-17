# Family Feud (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Family Feud/Family Feud.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `FAMILY FEUD` |
| Game code / maker | `B2FE` / `54` (Global Star Software) |
| Revision | `0x00` (`file`: "B2FE54, Rev.00") |
| Fixed `0x96` / complement / version | `0x96` / `0xE3` / `0x00` |
| Header checksum | `0x0000` (normal rebuilt-header artifact; complement byte intact) |
| Developer / publisher | Atomic Planet Entertainment / Global Star Software, 2006 (credits + GameFAQs/GamesDatabase) |
| MD5 | `079f35bf49c4c64aca46ac5b82c358e6` |
| SHA-1 | `37262e445c866f67cf0ff77cd64e2ce82454125a` |
| SHA-256 | `6a50e8699f744b8cf474ba4fde343a8ff41d8456e138c489181f8882b21bf9d1` |

**Embedded-header scan.** The 156-byte Nintendo logo occurs twice: at file `0x4` (the real header, entry `0xEA00002E` → `0x080000C0`, standard retail crt0) and at file `0x16F40` (ROM `0x08016F40`), a **multiboot/link stub** with blank title and code `AGBJ`, maker `01`, complement `0xDC`. It has a normal crt0 and is a link-transfer payload, **not** a second game, patch, or trainer. No GameShark/CodeBreaker signature, appended trainer menu, or modified entry point was found. This is the retail image.

## 2. Executive summary

**No developer-intended cheat, password, button-code, or hidden-debug system exists in this ROM.** The result is a *bounded negative*, not an untested guess:

* Every reachable screen was walked in mGBA with RAM evidence (full list in §6b): title → main menu (4 items) → Standard Game → Player-vs-Computer / Player-vs-Player → Difficulty (3) → family pick → family-chosen → Edit Family → two keyboard surfaces → Quick Game family pick → link-up submenu → Options (2 displayed items) → Credits → in-game intro/dialogue → answer-entry keyboard → gameplay board/strike. No password/cheat entry screen appears on any path.
* The only text-entry surfaces are the **family-name editor** and the **survey-answer entry** keyboard. Both use the same on-screen QWERTY/alphabetical grid (26 letters + SPACE/DEL/ENTER + a `BOARD` layout toggle). A 36-letter alphabet and 26-letter grids are the input space; **no literal table, comparison routine, or flag write consumes either buffer as a code** (§4, §6b).
* The game's entire ASCII text estate was classified: **2,169** strings in the UI/credits/dialogue bank (`0x1FD000–0x208000`) and **14,104** in the survey/answer bank (`0x208000–0x26C000`). All 82 keyword hits (`password`/`cheat`/`code`/`secret`/`debug`/`press`/`hold`/`button`, plus `+0x20`-shifted, UTF-16LE/BE variants) are legitimate survey answers, questions, or credit lines — e.g. `something that ends with the word 'code'.`, `Cheat sheet`, `Cheating`. There is no hidden code string in ASCII, shifted ASCII, or UTF-16.
* The screen dispatcher's function-pointer table at `0x0826C648` has **231 entries**; all in-game screen transitions target a small subset. Two screens that exist in the table but have **no incoming transition at all** — Volume (`0x0800DA44`, state 14) and Brightness (`0x0800DBF0`, state 15) — are dead code, not secret menus. The Options menu has a 3rd slot (index 1) that is a wired-but-unlabelled no-op; pressing A on it changes nothing.
* Published codes: **none exist for this GBA SKU.** Cheat Happens says "no Family Feud cheats or cheat codes for Game Boy Advance"; the archived GameFAQs GBA cheats page is empty. The frequently published `L+R+Start+Select` "family select" is for the **SNES** game and the `FAMILY` wardrobe password is for the **Wii/PC Ludia** game; both were checked against the ROM and the GBA build has neither surface. `Start+Select+A+B` on GBA is a plain soft-reset (`0x080024AC`), not a cheat.

## 3. How to reproduce

* Emulator: `DISPLAY=:317 SDL_AUDIODRIVER=dummy mgba -3 -g <rom>` under `Xvfb :317 -screen 0 1024x768x24` + `openbox`. GDB stub on `:2345` used for RAM reads.
* Keymap (mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold ≈130 ms per press; allow 1.5–2.5 s for fades (many transitions run a ~1 s fade, so an early screenshot can look black).
* Menu path used for the screen sweep: press A three times through the legal splash → **PRESS START** → Start → Main Menu → (each item) → … → B to back out.
* Codes tested on real screens:
  * `L+R+Start+Select` held at Player-1 family-pick: **no effect** (the A/Start component selects the default family; confirmed with RAM + screenshot).
  * `Start+Select+A+B` held at Main Menu: **soft reset** to the legal splash (confirmed; RAM reset to boot state).
  * `FAMILY` entered on the family-name keyboard: just a name; no reaction, no flag.
  * `BOARD` key on the keyboard: toggles QWERTY ↔ alphabetical layout; no hidden symbols/entries.
  * Dead Options slot index 1 (cursor forced via GDB, A pressed): **no effect**, screen unchanged.

## 4. Address map

| Address (ROM unless noted) | Kind | Meaning |
|---|---|---|
| `0x08000000` | header | entry `0xEA00002E` → crt0 at `0x080000C0` |
| `0x08016F40` | data | embedded AGBJ multiboot stub header |
| `0x080024AC` | Thumb fn | button gate: `held & 0xC == 0xC` (Start+Select) **and** A **and** B → soft reset (calls `0x08005778`/`0x0800579C`, resets state) |
| `0x080042FC` | Thumb fn | input manager: reads `KEYINPUT` (`0x04000130`) & `0x3FF` |
| `0x0800CE6C` | literal pool | `.. MAIN MENU ..` pointer (`0x08203DD4`) |
| `0x0800D8A8` | literal pool | `.. OPTIONS ..` pointer |
| `0x0800DA44` | Thumb fn | Volume screen (dead: no caller sets its state) |
| `0x0800DBF0` | Thumb fn | Brightness screen (dead: no caller sets its state) |
| `0x0805778` / `0x080579C` | Thumb fn | write/read screen state (`0x03004368` byte / `0x03004354` word) |
| `0x0826C648` | table | 231-entry screen/task function-pointer table (thumb pointers) |
| `0x08203DD4`…`0x0820472E` | text bank | all menu titles/items (ASCII, NUL-terminated) |
| `0x08246C00`-ish | text bank | survey questions; answer aliases follow (plain ASCII) |
| `0x030042B0` | IWRAM u16 | raw active-low `KEYINPUT & 0x3FF` |
| `0x030042B8` | IWRAM u16 | **held** keys, active-high (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`) |
| `0x030042BC` | IWRAM u16 | newly-pressed keys (edge = held & ~prev) |
| `0x03004354` / `0x03004358` / `0x03004368` | IWRAM | screen state word / queued state / menu sub-index |
| `0x030024D8` / `0x030024DC` | IWRAM u32 | menu cursor index / exclusive upper bound |
| `0x02000070` | EWRAM u32 | scene/state mirror observed during screen sweeps (title 3, menus 4, in-game 0) |

Key-state mapping was **observed**, not assumed: holding Left changed `0x030042B8` by `0x20`, L by `0x0200`, R by `0x0100`, Select by `0x4`, Start by `0x8` (EWRAM/IWRAM dumps before/during each key).

## 5. Algorithm / pseudocode

There is no password algorithm to reverse. The relevant model is the screen/menu state machine:

```text
KEYINPUT -> r = ~KEYINPUT & 0x3FF
held  = r                        @ 0x030042B8
edge  = r & ~prev                @ 0x030042BC
state = byte @ 0x03004368        ; index into fn table @ 0x0826C648
if (held & 0xC)==0xC and (held&1) and (held&2): soft_reset()   @ 0x080024AC

Menu dispatch (per screen handler, e.g. Options at 0x0800D818):
  Up/Down -> cursor @ 0x030024D8, wrap at bound @ 0x030024DC
  A       -> i = cursor
             if i==0: toggle TEXT DIALOGUES MINIMAL<->FULL
             else if i==2: enter Credits
             else: nothing        ; index 1 is a dead slot
  B       -> set_state(prev)
```

Text entry (family name / survey answer) is a direct glyph-to-buffer append with DEL/SPACE and an alphabet layout toggle. **No comparison of that buffer against a constant was found** (§6b).

## 6. Tables

* **Screen/task function table** — `0x0826C648`, 231 thumb pointers. Screen states and their handlers (first 27): 3 `0x0800CC08` title, 4 `0x0800CD48` main menu, 5 `0x0800D0F4` Standard Game, 9 `0x0800CF98` PvP, 10 `0x0800D2C0` Difficulty, 12 `0x0800D65C`, 13 `0x0800D818` **Options**, 14 `0x0800DA44` **Volume (dead)**, 15 `0x0800DBF0` **Brightness (dead)**, 16 `0x0800DF54`, 17 `0x0800E170`, 18 `0x0800E38C`, 19 `0x0800E5EC`, 20 `0x0800E8D4`, 21 `0x0800EAF4`, 22 `0x0800EC9C`, 23 `0x0800EE70`, 24 `0x0800F1FC`, 26 `0x08010684`. Remaining entries are gameplay/dialogue tasks.
* **Menu items (all in ASCII text bank):** Main Menu `Standard Game / Quick Game / Family Editor / Options`; Standard Game `Player vs Computer / Player vs Player`; Difficulty `Easy / Medium / Hard`; PvP `Single Machine / Link-up Play`; Options `TEXT DIALOGUES - MINIMAL|FULL`, `(dead slot)`, `CREDITS`; Player pick `Murphy / Santiago / Hill / Morales / Customize` (Quick Game: `Wheeler / Howard / Nichols / Webb / Customize`); Family chosen `Enter Studio / Edit Family`; Edit Family `Edit Family Name / Edit Members`.
* **Key masks:** accepted *single* keys only in all reachable menus; the only multi-key masks in the whole engine are soft reset `0xF` (Start+Select+A+B) at `0x080024AC` and the `0xC` (Start+Select) guard inside the same routine. No other chord is compared (full `cmp`/`tst` scan near every key-state load, §6b).

## 6b. Enumeration

**Screen-space enumeration (every screen walked, with RAM evidence).** For each I read `0x02000020/0x70/0xA0` and, once identified, `0x03004354/0x03004368/0x030024D8`:

1. Legal splash (Global Star / Atomic Planet / FremantleMedia) — `0x02000070` boot value.
2. Title "PRESS START" — `0x02000070=3`, `0x020000A8=0x08047740`.
3. Main Menu — `0x02000020/24=4`, `0x020000A8=0x08046F00`, state 4.
4. Standard Game menu — `0x030024DC=1`.
5. Player vs Computer → Difficulty `Easy/Medium/Hard` — `0x030024DC=2`.
6. Player 1 pick family → family chosen → Enter Studio / Edit Family.
7. Edit Family → Edit Family Name (QWERTY keyboard) and Edit Members.
8. Quick Game → family pick (`Wheeler/Howard/Nichols/Webb/Customize`) → family chosen.
9. Player vs Player → `Single Machine / Link-up Play`, and `.. LINK-UP PLAY .. / Waiting for opponent to join`.
10. Options → `TEXT DIALOGUES - MINIMAL` (toggled to FULL), `CREDITS` (scrolling developer credits captured).
11. In-game: intro dialogue → survey question → **answer-entry keyboard** → board/strike gameplay. No pause menu on Start, Select, or L+R.

**Text/keyword space:** 2,169 + 14,104 ASCII strings counted; 82 keyword hits manually classified as legitimate; `password` = **0 hits**; `DEBUG` = 1 (`AGB DEBUG ASSERT:`, a library assert). Encodings checked: ASCII, `+0x20` shifted ASCII, UTF-16LE, UTF-16BE. Keyboard glyph space: 26 letters (QWERTY and alphabetical layouts) + SPACE/DEL/ENTER; `BOARD` toggles layout; no numbers/symbols/code cells.

**Validator/comparator space:** no `strcmp`-style byte-compare loop (`ldrb,ldrb,cmp,bne,cmp #0,bne`) exists in Thumb code from `0x08000000` to `0x08020000` (0 candidates). All 33 load sites of held keys and all PC-relative literal loads of the key-state globals were disassembled and scanned for multi-button `cmp`/`tst` immediates: only the soft-reset path. No flag word is written by any text-entry routine.

**Reachability enumeration:** of the 231 function-table entries, every state-change call site (262 calls to `0x08005778`, 173 to `0x080057C8`) was decoded for its `r0` state value. States 14 (Volume) and 15 (Brightness) have **zero** incoming transitions; state 11 also has none. These are dead screens, not hidden features. The Options menu bound is 3 (`0x030024DC=2`), so index 1 is a real slot; setting the cursor to 1 and pressing A produced no state change — a dead slot, not a secret.

**Published codes tested (all verified against ROM):** SNES `L+R+Start+Select` (no code surface on GBA; tested, no effect), Wii/PC `FAMILY` wardrobe password (different game; name field accepts it but no effect), GBA-specific published codes (none exist per Cheat Happens, GameFAQs GBA cheats page via web.archive.org, and the 100-GBA-ROM study at remyhax.xyz). No novel code could be minted because **no code system exists**; the closest "novel" observation is the unreachable Options slot 1 and the dead Volume/Brightness screens, both proved by rejection/no-op.

**Bounds proven:** entering `FAMILY` as a family name (accepted as text, no flag); forcing dead Options slot 1 (no-op); holding Start+Select+A+B (soft reset, not a cheat). These bound the "no hidden code" conclusion on every surface the game exposes.

## 7. Validation evidence

* **Observed:** all 11 screen groups above via screenshots/OCR plus RAM dumps; key-state deltas in IWRAM; `0x030024DC=2` for Options; cursor moving `0→1` on Down; soft reset on `Start+Select+A+B`; `FAMILY` accepted only as a name; `BOARD` layout toggle; mGBA exiting during a long unattended credits playback (emulator quirk, not game behavior).
* **Derived:** key-state address map and input manager at `0x080042FC`; soft-reset gate at `0x080024AC`; screen-state globals `0x03004354/68`; 231-entry function table at `0x0826C648`; state 14/15 have no incoming transition; Options slot 1 is unwired; no strcmp-like comparator in engine code; all keyword hits are survey text.
* **Inferred:** the `AGBJ` header at `0x16F40` is a link multiboot stub (blank title, standard logo/crt0) rather than a second game; Volume/Brightness screens are leftover development options, not a gated player feature. Analysis artifacts (family name temporarily became `MU` after a mistimed chord test; both are session-local and do not affect the ROM).

## 8. Unknowns

* The dead Volume/Brightness screens exist but cannot be entered through any normal input; I did not force them to render via the game's own `0x0800579C` call, so their visual content is unobserved (their handlers were identified statically and by title-string xrefs).
* The exact matcher semantics of the survey-answer checker (how typed answers are scored against the alias lists) were not reversed; the answer bank is plain ASCII, so this was outside the "code system" question and is not needed for the negative result.
* Link-up play requires a second GBA and was inspected only to the "Waiting for opponent to join" screen; no second console was available. No code surface is visible there.
* No published GBA code list exists to cross-check beyond the negative web evidence recorded above.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for Thumb disassembly; Capstone 5.0.7 for literal-load / BL / state-value scans.
* Python 3 scripts in `/tmp/opencode/familyfeud/`: `menu_scan.py` (title→pointer map), `screens.py` (function-table enumeration), `transitions.py` (state-change graph), `final_static.py` (string/keyword counts + encodings), `find_strcmp.py`, `scan_keycmp.py`.
* mGBA `-g` GDB stub + `gdb-multiarch` for live RAM reads (`0x030042B8` key mask, `0x030024D8` cursor, screen-state globals). `dumpram.sh` diffs EWRAM/IWRAM to locate state variables.
* `Xvfb :317`, `openbox`, `xdotool`, `scrot`/`import`, ImageMagick `convert`, `tesseract` for screen capture/OCR. No ROM or assets were redistributed; only addresses, hashes, and findings are published.
