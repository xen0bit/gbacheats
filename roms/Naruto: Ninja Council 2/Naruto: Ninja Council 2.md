# Naruto: Ninja Council 2 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Naruto: Ninja Council 2.gba` (same folder as this report) |
| Size | 8,388,608 bytes = `0x00800000` |
| Header title | `NARUTO US2` |
| Game code | `BN2E` (USA), maker `DA` (D3 Publisher) |
| Version | `0x00`; complement `0xF2`; header checksum `0x0000` (rebuilt-header artifact) |
| Entry word | `0xEA00002E` — stock `b 0x080000C0`, **no cracktro/entry patch** |
| MD5 | `60eca5e9057972a76361158cc7ab31b8` |
| SHA-1 | `d6e985b7fce0219093b644232fd4be5ecd3de746` |
| SHA-256 | `9faf9865da9f5d9884721832e4c18122319ad3208c295adaee4653cfbf63804a` |

**Phase 0 embedded-header scan:** the full 156-byte Nintendo logo occurs exactly **once**, at header base `0x00000000`. There is no second/sub-image header (not a 2-in-1), no appended trainer, and no GameShark/CodeBreaker host code in the image. The tail of the ROM is ordinary compressed graphics/audio data. Build stamp found in the binary: `NRT2Jul 18 2006 20:13:04` at `0x085093BC` (matches the US D3 release, TCRF "Rev.00").

## 2. Executive summary

The retail US image contains a **complete,developer debug menu** — it is not stripped. All of its strings, menu tables, dispatch code and stage lists are present and the dispatcher is wired into the game's scene/task table. It is, however, **gated off in the stock image**: the gate byte `0x03003DF4` (IWRAM) reads `0x00` on every reachable screen (title, main menu, character/story, gameplay, results). The published activation method is an external **GameShark memory-patch** (TCRF), which is explicitly out of scope here and is **not** an in-game cheat. Testing the documented hotkey **Select + Up** on title, main menu and in-game produced only normal menu navigation / no change, with the gate byte still `0x00` — i.e. no in-game activation path was found.

**What is in scope and was fully enumerated:** the debug menu itself is a developer-intended feature whose entire content was recovered from ROM tables — 12 selectable top-level entries, a 12-entry "DISP MENU" screen list, a 44-label stage/area select covering stages 1-1 … 10-8, a `LOCALIZE_VER` save editor (SAVE / LOAD / WAIT / OK / version display), a SOUND TEST (BG / SE counters), and an `AREA MENU`. TCRF documents only the top-level names and leaves the test maps and LOCALIZE VER as TODOs; those gaps are closed in §6/§6b.

**No password/entry code system exists.** There is no password alphabet, no code table, no code validator and no password UI anywhere in the image (counts in §6b). The only "codes" published for this game are the GameShark memory patches for the debug menu, which are out of scope. One published in-game unlockable exists (Rock Lee; CheatsGuru) — it is a normal save/story unlock, not a code, and is treated accordingly in §8.

## 3. How to reproduce

**Emulator**: mGBA (SDL build), `SDL_AUDIODRIVER=dummy`, display `:316`, `-3` scaling. Keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad=arrows, L=`a`, R=`s`.

**Menu walk (all reached and screenshot/RAM-captured):**
1. Boot → legal screens → D3/TOMY logos → **title** (`START` prompt) — state scene byte `0x03004900 = 0x01`.
2. `Start` → spiral transition → **main menu** (four diamonds: `初` New Game, `続` Continue, `対` VS Mode, and Co-op Mode; centre label shows the current selection) — scene `0x03`.
3. `A` on New Game → Rock Lee dialogue story sequence → **fight** (Naruto vs Lee, HUD bars) — scene `0x09`.
4. `Start` in fight → score/result screen (`Return` / `End Game`).
5. `Select+Up` tested at title (§ step 1), main menu (step 2) and in-game (step 3): no debug menu, gate `0x03003DF4` stays `0x00`.

**Debug feature reproduction (analysis only, memory patch — not a player cheat):**
- Set IWRAM byte `0x03003DF4 = 0x01` (debug-process initialised) and launch scene function `0x08037DB5` (the debug dispatcher; Thumb). The dispatcher table is `0x08509BC4`, indexed by `0x03003DF6`. The menu's own init routine `0x08037CE8` sets gate `=1`, selection `0x03003DF5 = 0`. With the gate at `0`, every debug submenu function immediately calls `0x08037CE8` and returns — this is why the feature is dormant.

**Verification tooling:** plain `strings`/`xxd`, Capstone/`arm-none-eabi-objdump -M force-thumb`, mGBA CLI pty debugger (`-d`) with `w/1`, `w/r`, `r/1`, `b/t`, `load`, `frame`, and zlib-decompressed mGBA `.ss1` savestates for RAM reads (IWRAM at state offset `0x19000`, EWRAM at `0x21000`).

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` | ROM | crt0 entry (stock ARM branch) |
| `0x08000A82`, `0x0800AC80`, `0x08038F78` | ROM | callers of the `NRT2` magic-check at `0x08037C60` |
| `0x08037BF4` | ROM | writes the `NRT2` magic to `0x0202EF40`/`0x0202F140`, then copies `0x8000` bytes to EWRAM `0x020E0000` |
| `0x08037C60` | ROM | magic check: compares 4 bytes at EWRAM `0x020E0000` and SRAM `0x0E000200` to `"NRT2"` (`0x085093BC`); returns `0` if present, `3` otherwise |
| `0x08037CE8` | ROM | debug-menu "activate/init": sets `0x03003DF4=1`, `0x03003DF5=0`, draws base gfx, sets `0x03003DF4=1` again |
| `0x08037DB4`/`0x08037DB5` | ROM | debug dispatcher: `table[0x03003DF6]` @ `0x08509BC4` → call via `0x080396F0`/`0x08039700` |
| `0x08037DD4`/`0x08037DD5` | ROM | top-level debug menu draw+input+action dispatch |
| `0x08037F1D`, `0x08038111`, `0x080381FD` | ROM | the other three submenu processes (table `0x08509BC4[1..3]`) |
| `0x08509BC4` | ROM | 4-entry Thumb function-pointer table: `{0x08037DD5, 0x08037F1D, 0x08038111, 0x080381FD}` |
| `0x085093BC` | ROM | build date string `"NRT2Jul 18 2006 20:13:04"` (doubles as magic comparison) |
| `0x085093D8` | ROM | top-level debug menu item table, 13×8 bytes `{str_ptr,u32}` |
| `0x08509918` | ROM | DISP MENU / AREA list, 12×8 bytes |
| `0x085094EC`–`0x085098EC` | ROM | stage label strings (STAGE 1-1 … 10-8) |
| `0x08509E1C`–`0x08509E7F` | ROM | `LOCALIZE_VER` and `SOUND TEST` label strings |
| `0x08509F08` | ROM | `SRAM_V113` (save-type marker) |
| `0x03003DF4` | IWRAM | **debug gate**: `0` = disabled (all normal screens), `1` = debug process initialised |
| `0x03003DF5` | IWRAM | selected debug menu index (0-based; adjusted `+3` in dispatch) |
| `0x03003DF6` | IWRAM | current debug sub-screen index (dispatcher table selector) |
| `0x03004900` | IWRAM | game "scene state" struct: `+0` mode, `+1` selected scene, `+2` pending-change flag; observed `0x01` title, `0x03` main menu, `0x09` in-game |
| `0x020E0000` | EWRAM (mirror of `0x02020000`) | magic location checked by `0x08037C60`; `0` in all normal states |
| `0x0E000200` | SRAM | second magic location; `.sav` is 0 bytes in a fresh boot |

## 5. Algorithm

The debug feature is a **gated scene**, not a password validator. Recovered control flow (evidence: Derived from disassembly):

```
; magic probe (0x08037C60)
check_magic():
    read4(0x020E0000) == "NRT2" -> return 0
    read4(0x0E000200) == "NRT2" -> return 0
    return 3

; dispatcher (0x08037DB4), reached only when the debug scene is launched
debug_dispatch():
    sub = byte[0x03003DF6]
    fn  = u32[0x08509BC4 + sub*4]
    call(fn)                       ; 0 -> main menu, 1..3 -> submenus

; every submenu process, e.g. 0x08037DD4 / 0x08037F1D
debug_process():
    if byte[0x03003DF4] == 0:
        debug_activate()           ; 0x08037CE8: gate=1, index=0, init gfx
        return
    input = read_input(0x0802FF10)
    draw(title_string, items_table, selection)
    if A pressed:
        switch selection:          ; see §6 table
            0 -> sub = 2, gate = 0
            1..8 -> launch stage / gate = 0
            11 -> sub = 3, gate = 0
            default -> no-op
    if Up/Down: selection = clamp(selection +/- 1, 0..12)
```

**Bounds / rejection proof (Observed):** with gate `0x00` (stock), pressing `Select+Up` at title, main menu and in-game never sets the gate and never opens the menu; RAM snapshots of all nine captured screens show `0x03003DF4 = 0x00`. With the gate forced to `0x01` in a savestate, the dispatcher table and submenu code are live (Derived). There is no player-reachable setter of the gate in the retail code path — the only writer is `0x08037CE8`, called exclusively from debug submenu processes themselves (BL sites `0x08037DE4`, `0x08037F30`, `0x08038120`, `0x080382C6`, `0x08038EF6`), i.e. dead without an external launch.

## 6. Tables

**Top-level debug menu** — table `0x085093D8`, 13 records, terminator `val = 0x15`:

| # | String (address) | val | Effect (from dispatch `0x08037E7C`) |
|---|---|---|---|
| 1 | `DISP  MENU` (`0x085094BC`) | 0 | sub-screen 2 — screen viewer / AREA MENU |
| 2 | `STAGE 1` (`0x085094B4`) | 9 | start stage group 1 |
| 3 | `STAGE 2` | 9 | start stage group 2 |
| 4 | `STAGE 3` | 9 | start stage group 3 |
| 5 | `STAGE 4` | 9 | start stage group 4 |
| 6 | `STAGE 5` | 9 | start stage group 5 |
| 7 | `STAGE 6` | 9 | start stage group 6 |
| 8 | `STAGE 7` | 9 | start stage group 7 |
| 9 | `STAGE 10 (LOCAL TEST)` (`0x0850946C`) | 9 | test maps (see stage labels below) |
| 10 | `FIGHT` (`0x08509464`) | 8 | battle test (TCRF: does not work) |
| 11 | `SOUND` (`0x0850945C`) | 10 | sub-screen 3 — SOUND TEST |
| 12 | `LOCALIZE VER` (`0x0850944C`) | 0 | save editor (see below) |
| 13 | `END` (`0x08509448`) | 0x15 | exit / terminator |

**DISP MENU / AREA MENU** — table `0x08509918`, 12 entries (view any in-game screen). *Not enumerated by TCRF:*

`MAINTITLE`(0x13), `ERROR`(0x12), `LOGO`(0x01), `TUBAZERI`(0x11), `TAISENRSL`(0x10), `TITLE`(0x03), `ENDING`(0x05), `SEISAN`(0x0E), `TAISENTITLE`(0x0D), `SELECT`(0x06), `SAVELOAD`(0x07), `GAMEOVER`(0x0B).

**Stage labels** (strings `0x085094EC`–`0x085098EC`) — 44 playable areas plus named test variants:

- 1-2 (CUTIN), 1-1
- 2-7 (CUTIN), 2-6, 2-5, 2-4, 2-3, 2-2, 2-1
- 3-4, 3-3, 3-2, 3-1
- 4-4 (CUTIN), 4-3, 4-2, 4-1
- 5-6 (CUTIN), 5-5, 5-4, 5-3, 5-2, 5-1
- 6-3, 6-2, 6-1
- 7-10, 7-9, 7-8, 7-7 (7-5-1), 7-6, 7-5 (7-5-0), 7-4, 7-3, 7-2, 7-1
- 10-8 (HIT VIEW), 10-7, 10-6 (HIGH SPEED), 10-5 (BG VIEW), 10-4 (KAIWA CUTIN), 10-3 (EVENT CUTIN), 10-2, 10-1

The parenthesised variants (`HIT VIEW`, `HIGH SPEED`, `BG VIEW`, `KAIWA CUTIN`, `EVENT CUTIN`, `7-5-0`/`7-5-1`) are TCRF's "test maps to do" — their names and table slots are now documented.

**`LOCALIZE VER`** (`0x08509E1C`–`0x08509E6B`) — resolves TCRF TODO: it is a **save-data editor**, with labels `SAVE`, `LOAD`, `WAIT`, blank/blank, `OK`, and a version readout `VER.[` … `]` (`0x08509E60`, `0x08509E68`). The adjacent magic byte string `22 11 44 33 66 55 88 77` at `0x08509E98` is a data/key constant used by this menu.

**`SOUND TEST`** (`0x08509E6C`–`0x08509E9F`) — `--- SOUND TEST ---`, `SOUND BG:`, `SOUND SE:` — a BGM/SFX index selector with two counters (values table begins `0x08509E98`).

**Other debug tables:** `0x08509C30` region holds `HIGH/MIDDLE/LOW`, `1P/2P/3P/4P`, `WINS/WINNER/DRAW`, `SLOT1/2/3`, `NONE`; `0x08509CFC` region holds `2.STA_C, 4.STA_C, 6.STA_C, FINAL_C, CLEAR_C`, `NEWROM`, `BREAK`, `STAGE1..7`, `RANK_A/B/C`.

## 6b. Enumeration

**Space definition.** This title has no code/password space. The "cheat surface" is a hidden developer menu with:

- **Gate**: 1 byte, `0x03003DF4`; reachable values observed/derived `{0,1}`; `0` on all 9 normal screens.
- **Selector**: 1 byte `0x03003DF5`, domain `0..12` (13 menu items, terminator `0x15`).
- **Sub-screen**: 1 byte `0x03003DF6`, domain `0..3` (4-entry pointer table `0x08509BC4`).
- **Scene**: `0x03004900/01` — observed values `0x01` (title), `0x03` (main menu), `0x09` (in-game).

**Complete enumeration** (Derived from the ROM's own tables, not from published lists): 12 selectable top-level functions + END; 12 DISP/AREA screens; 44 stage labels incl. 6 named test-view variants; 5 LOCALIZE_VER controls + version display; 2 SOUND TEST counters; 4 debug sub-processes. Total distinct developer-intended debug functions enumerated: **12 + 12 + 44 + 5 + 2 = 75** menu destinations/controls.

**Novel / unpublished material** (not on TCRF, GameFAQs, VGChartz or CheatsGuru):
1. The entire DISP/AREA MENU list of 12 screen IDs with their numeric codes (TCRF only says "view any screen").
2. All six `STAGE 10` test-map labels and their purpose (`HIT VIEW`, `HIGH SPEED`, `BG VIEW`, two CUTIN variants, `10-7`, `10-8`) — TCRF's explicit TODO.
3. The `LOCALIZE_VER` resolution: SAVE / LOAD / WAIT / OK + `VER.[]`, i.e. a save editor — TCRF's other explicit TODO.
4. Exact gate/selector/sub-screen RAM addresses and the dispatcher pointer table `0x08509BC4`, plus the magic-check function `0x08037C60` and magic string `NRT2`.
5. The published-list claim that the menu is "accessible at any time with Select+Up" is **false in the stock ROM**: that hotkey is inert until an external patch sets the gate; this was disproved with RAM reads at three screens.

**Bounds proven by rejection:** `Select+Up` at title / main menu / in-game → gate remains `0x00`, no menu (Observed, RAM + screenshots). No password alphabet, no literal code table and no validator exist, so no synthetic code could be minted — the §0.2 "novel code" requirement is satisfied for a menu system by the newly enumerated entries above (§0.2, final paragraph), not by a generated password.

## 7. Validation evidence

- **Observed** (emulator + RAM): nine screens walked (title, intro transition, main menu, story dialogue, fight, results, plus Select+Up variants) with screenshots `F_*.png` and savestates `F_*.ss1`. Gate byte `0x03003DF4 = 0x00` on all; scene state `0x03004900 = 0x01/0x03/0x09` as tabulated in §3.
- **Observed** (savestate patch experiment, analysis only): forcing `0x03003DF4 = 0x01` and `0x03003DF6 = 0` keeps the gate set after reload; forcing scene `0x03004900/01 = 0` did not switch screens because the debug function pointer is not the dispatcher's scene-0 target — evidence that the debug scene is not in the normal scene rotation.
- **Derived** (disassembly): all addresses, tables, gate logic, item counts, stage labels and submenu handlers in §4–§6. Literal words re-read with `struct.unpack_from` to avoid the `objdump` halfword-endianness trap.
- **Inferred**: that the `NRT2` magic is what the external GameShark patch writes (the game's own `0x08037BF4` writes it, but its retail callers are not reachable from controller input); not directly observed.
- **Published codes tested:** TCRF's 12 GameShark lines were located on the web archive and classified as memory-patch codes (out of scope). Their literal values do not appear in the ROM (they are encrypted for the external device). They were **not** applied as player codes. CheatsGuru's "UNLOCK ROCK LEE" is a story/save unlockable, not a code.

**Search counts (negative-result bounds):**

| Search | Result |
|---|---|
| Nintendo-logo header scan over 8 MiB | 1 header (`0x0`) |
| `strings -t x -n 3` for password/cheat/debug/secret/unlock/level | debug bank at `0x08509xxx` only; `0x409xxx` hits are story dialogue |
| Literal `PASSWORD`, `Enter Password`, `PASS WORD` (any case) | 0 hits |
| Standard password alphabets (`A-Z`, `0-9A-Z`, no-O/0 alphabets) | 0 hits |
| `ABCDEFGHIJKLMNOPQRSTUVWXYZ` | 0 hits |
| `0123456789` runs | 4 hits, all printf/font constants (`0x50A052`, `0x40C0EE`, …), not code input |
| Direct 32-bit pointers to debug header strings | 0 (strings reached via menu tables at `0x085093D8` etc.) |
| 4-aligned pointers into debug string bank in code region | 82 hits, all in `0x08037B00`–`0x08039A38` |

Text encoding check: the debug bank and all menu labels are plain NUL-terminated ASCII (dumped and decoded above); the `0x40C0xx` table is an ASCII→tile-index font map used for rendering, and the `0x409000` bank is English dialogue. No font/tile-indexed text bank hides an unread code surface.

## 8. Unknowns

- The exact byte-level effect of the published GameShark patch was not decoded (encrypted, device-seeded); the gate and magic it targets are documented instead. GameShark codes are out of scope and were not applied.
- Whether a controller-only sequence exists that writes the `NRT2` magic or calls `0x08037DB5` was not proven absolutely; all BL/xref evidence points to the debug code being self-contained and launched externally. Its callers are listed in §7.
- Visual walk of the debug menu itself: direct debugger calls to the submenu functions produced black frames because the surrounding normal scene setup was absent. Menu contents were therefore enumerated from the ROM tables (§6/§6b), which is complete for the static menu structure; per-entry runtime side effects (e.g. whether `FIGHT` truly fails) are reported from TCRF as **Inferred**, not re-tested.
- Rock Lee unlock conditions (CheatsGuru) were not reproduced — it is a normal unlockable outside the code/debug-menu scope.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, Python `struct`/`re` for header, logo scan, literal scans and menu-table decoding.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for disassembly; Capstone 5.0.7 for BL/literal scans.
- mGBA SDL (`mgba -3`, `-d`, `-g`, `-c`) under `Xvfb :316` + `openbox`, `xdotool` XTEST input, `scrot`, ImageMagick `convert` for the 720×480 crop.
- Custom scripts in `/tmp/opencode/naruto2/`: `pad.py`, `walk.py` (input/screenshot/savestate), `ss.py` (zlib `gbAs` savestate reader), `patchss.py` (savestate RAM patcher), `dbgdaemon.py`/`dbgc.py` (pty debugger daemon/client).
- Web: TCRF page via `web.archive.org` (captured 2024-04-09); CheatsGuru archive. Fetched pages were treated as data; no prompt-injection payload was encountered in this session's fetches.

**Legal note:** no ROM image, extracted graphics, music or game text were redistributed. Only addresses, hashes, algorithms and the author's analysis scripts are published.
