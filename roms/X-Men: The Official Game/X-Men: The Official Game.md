# X-Men: The Official Game (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/X-Men: The Official Game/X-Men: The Official Game.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `X-MEN: THE O` (12-byte field; full title on title screen: "X-Men: The Official Game") |
| Game code | `B3XE` |
| Maker | `52` |
| Version | 0 (Rev.00) |
| Complement byte | `0xC9` at 0xBD (header checksum 0x0000 — treat complement as the edited-header signal, §16.1) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0; no cracktro/trainer observed) |
| MD5 | `2584c4d9c73888ffc9096a02fafea08c` |
| SHA-1 | `e53aefa4e6fdab6b9d4d29d19f9c29004e767c94` |
| SHA-256 | `f825af4f1a18896832707259b0c9919286c95977cdfb6b808bafcee126be854a` |
| Build strings | `BUILD: 060306 2000 (Master)`, `XMEN 3, AGB`, `U.S. BUILD` at file 0x3B2E0 / 0x3B300 / 0x3B420 |

## 2. Executive summary

The GBA SKU has a **developer debug menu reached by an undocumented 31-press button code on the title screen**. No published cheat list carries this code: the widely published "Cerebro Files" codes (Right/Right/Left/Left/Down/Up/Down/Up/Start etc.) belong to the PS2/GameCube/Xbox/DS versions of *X-Men: The Official Game*, not to this GBA build. Searching the ROM for those console sequences as key masks (u8 and u16, both polarities, 4-press prefixes) produced **0 hits** (§6b).

The accepted GBA code is:

```
L L R R R R R R R R L L L L L L R R L L L L L L L R R R R L L
```

(2×Left, 8×Right, 6×Left, 2×Right, 7×Left, 4×Right, 2×Left — 31 presses.)

Entering it on the title screen sets a flag and jumps to scene 2, a two-page debug menu with **32 reachable entries**: 13 Screens, 6 Debug actions, 26 level starts, and a duplicate "Unlock NtCwlr" entry. Every entry was activated in mGBA and mapped to its scene index with savestate RAM readback. Selecting `Unlock NtCwlr` shows "Nightcrawler UNLOCKED" and flips a RAM byte (0x030002F8: 0x00 → 0x01). The debug menu's `EXTRAS` entry reaches the normal in-game Extras screen, which is greyed out and unreachable from the ordinary main menu in a fresh file.

The game's main loop is a 91-slot scene dispatcher; all 91 scene indices were enumerated by patching the scene byte in an mGBA savestate (§7). No password/keyboard, codebreaker-style checksum, or second algorithmic code system exists: the only input-matched cheat is the 31-step L/R sequence.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap verified in emulator: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, L=`a`, R=`s`, D-pad=arrow keys. Hold ≈55 ms per press, ≈75 ms gap (45–70 ms moves one menu step; longer holds double-step).
* Boot the ROM. The intro advances through Legal → WayForward → Activision → Marvel → title automatically; wait for the "THE OFFICIAL GAME / Press START" screen (scene byte `0x03001858 == 0x0A`).
* On the **title screen** press, in order:
  `Left Left Right Right Right Right Right Right Right Right Left Left Left Left Left Left Right Right Left Left Left Left Left Left Left Right Right Right Right Left Left`
* The debug menu appears immediately (no Start press needed after the last L).
* In the debug menu: Up/Down move within a column, Left/Right switch column/page, A (`x`) activates. The footer reads `(Page 1 of 2)` / `(Page 2 of 2)`.
* To reach the locked Extras screen from a fresh file: debug menu, page 1, select `EXTRAS` (index 8), press A.
* To unlock Nightcrawler from a fresh file: debug menu, page 1, select `Unlock NtCwlr` (index 17), press A.

Screenshots and the state-file enumeration are in `/tmp/opencode/xmenofficial/` (not in the ROM folder). Key frames: `real_title6.png` (natural title), `real_code_after6.png` (menu after code on real title), `dbg_entry.png`, `walk_p1_*.png`, `walk_p2_*.png`, `walk_p2left_*.png`, `unlock_ntcwlr_effect.png`, `bound_30press.png`, `bound_31press.png`, `bound_wrong15.png`, `scenes/s01.png`…`s91.png`.

## 4. Address map

All addresses are ROM addresses (`file offset + 0x08000000`) unless marked RAM.

| Address | Meaning | Evidence |
|---|---|---|
| `0x080000C0` | ARM crt0 entry; `ldr r1,[0x0800023C]` = `0x0800A32D`, `bx r1` → game main | Derived (objdump ARM) |
| `0x0800A32C` | Game main / video-init loop (`FUN_0800A32C`); calls `0x0800BBE4` each frame | Derived (REA/Ghidra decompile) |
| `0x0800BBE4` | 91-slot scene dispatcher; `scene-1` indexes a jump table at `0x0800BC38` | Derived |
| `0x0800BC38` | Jump table, 91 × u32 scene handlers | Derived (dumped) |
| `0x08007490` | Scene setter: writes new scene to RAM `0x03001858`, zeroes `0x03003E64` and `0x03000544`, copies previous scene to `0x03001003` | Derived |
| `0x08010B84` | **Button-code matcher** (called only from scene 10 / title via BL at `0x0800BF14`) | Derived |
| `0x08010BD4` | 31-entry jump table of step handlers (`0x08010C50` = test `0x20`/Left, `0x08010C56` = test `0x10`/Right) | Derived (dumped) |
| `0x08010C50` / `0x08010C56` | Step handlers: `if (keyState & mask) counter++` | Derived |
| `0x08010C6A`–`0x08010C78` | `if (counter == 31) { *(u8*)0x03003E50 = 0xFF; scene_set(2); }` | Derived + Observed |
| `0x03003EB8` | Active-high key state (`0x3FF & ~KEYINPUT`), u16 | Derived |
| `0x030009FC` | Code progress counter, u8 | Observed (0x01 → 0x1F) |
| `0x03003E50` | Code success flag, u8 (0x00 → 0xFF) | Observed |
| `0x030020E8` | Matcher state byte (0xFF = uninitialised; reset to 0x01 on first call) | Derived + Observed |
| `0x03001858` | Current scene index, u8 | Observed (0x2F main menu, 0x0A title, 0x02 debug) |
| `0x030002F8` | Nightcrawler-unlock byte (0x00 → 0x01 after `Unlock NtCwlr`) | Observed (savestate diff) |
| `0x0816B654`–`0x0816C4F0` | Debug-menu text bank: `{u32 id; char text[32]}` records, stride 0x24; groups `Screens`, `Debug`, `Levels` | Derived |
| `0x0803AD50`–`0x0803B058` | Menu item-id tables (u32, `0xFFFFFFFF` terminated) | Derived |
| `0x0803B2E0` / `0x0803B318` / `0x0803B438` | Debug build strings: `BUILD: 060306 2000 (Master)`, `Nightcrawler UNLOCKED`, `XMEN 3, AGB - Cinema Debug` | Observed |
| `0x08006C58` | Literal `0x04000130` (KEYINPUT) — one of only 7 such literals in the ROM | Derived |

## 5. Algorithm

The title-screen matcher (`0x08010B84`) is an index-driven key sequence comparator, not a checksum:

```
state = byte[0x030020E8]                 # 0xFF means "needs init"
if state == 0xFF: state = 1
key  = u16[0x03003EB8]                   # active-high: A1 B2 Sel4 Sta8 R0x10 L0x20 U0x40 D0x80
i    = byte[0x030009FC]                  # progress counter
if i <= 30:
    step = jumptable[0x08010BD4][i]      # 0x08010C50 (mask 0x20=Left) or 0x08010C56 (mask 0x10=Right)
    if key & step.mask: i = i + 1
if i == 31:
    byte[0x03003E50] = 0xFF
    scene_set(2)                         # open debug menu
```

Masks from the jump table (index → expected key):

```
 0  L    1  L    2- 9  R (8x)   10-15 L (6x)   16-17 R (2x)
18-24 L (7x)   25-28 R (4x)   29-30 L (2x)
```

The step handlers never reset the counter on a wrong press; they simply do not increment it. (The precise reason a wrong press at step 15 read back as counter `0x02` rather than `0x0F` was not isolated — see §8.) Extra presses after success are ignored because the counter saturates at 31.

The debug menu itself (`0x0800C614`) is a separate state machine over a flat item index with column/page transitions derived from masks `0x80` (Down, +1), `0x40` (Up, −1), `0x10` (Right, +19/38) and `0x20` (Left, −19/38), with A (`0x01`) or Start (`0x08`) activating the selected item; each item calls `scene_set(id)` with the id stored in the text bank.

## 6. Tables

### 6a. Debug-menu entries (page 1)

| Idx | Label | Scene | Observed result |
|---:|---|---|---|
| 0 | WF LOGO | 0x07 | WayForward logo |
| 1 | LEGAL | 0x31 | Legal text |
| 2 | MARVEL LOGO | 0x09 | Marvel logo |
| 3 | ACTIVISION | 0x08 | Activision logo |
| 4 | LANGUAGE | 0x30 | Language select (English, …) |
| 5 | TITLE | 0x0A | Title screen |
| 6 | LOAD MENU | 0x2A | "Loading…" template |
| 7 | MAIN MENU | 0x2F | Main menu |
| 8 | EXTRAS | 0x2C | Extras menu (Sound Test / Arrange Mode / Danger Room / Credits) — normally locked |
| 9 | SOUND TEST | 0x2B | Sound test screen |
| 10 | ARRANGE MODE | 0x2D | Arrange Mode screen |
| 11 | DANGER ROOM | 0x2E | Danger Room character select |
| 12 | CREDITS | 0x0B | Credits |
| 13 | Mobility GYM | 0x33 | Mobility GYM level |
| 14 | Enemy GYM | 0x34 | Enemy GYM level |
| 15 | Zoo | 0x35 | Zoo level |
| 16 | Player Anims | 0x04 | Animation viewer (`wAnimID`, `frame:`, `Cuts:` overlay) |
| 17 | Unlock NtCwlr | 0x05 | "Nightcrawler UNLOCKED", then back to menu |
| 18 | Test Cinemas | 0x06 | Cinema/cutscene list (4 pages) |
| 19–24 | LEVEL 01–06 | 0x36,0x37,0x43,0x44,0x45,0x47 | respective level |

### 6a (cont.). Debug-menu entries (page 2)

| Column | Label | Scene |
|---|---|---|
| Left | LEVEL 07–20 | 0x49,0x48,0x46,0x4B,0x4C,0x4D,0x4E,0x4F,0x50,0x51,0x52,0x53,0x4A,0x54 |
| Right | LEVEL 21–26 | 0x55,0x57,0x56,0x58,0x59,0x5A |
| Right | Unlock NtCwlr (2nd copy) | 0x05 |

Note: the level labels are in non-monotonic id order (e.g. LEVEL 03 = 0x43, LEVEL 08 = 0x48, LEVEL 19 = 0x4A) — the *numeric scene id*, not the printed "LEVEL NN", is authoritative (§16.15).

### 6a (cont.). Key mask encoding

Active-high image of `KEYINPUT & 0x3FF`: `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`. The cheat uses only `0x10` and `0x20`.

## 6b. Enumeration

**Space.** The cheat is a 31-step sequence over a 2-symbol alphabet (Left / Right), i.e. 2³¹ = 2,147,483,648 possible L/R strings of full length. Exactly one ordering is accepted; the jump table at `0x08010BD4` fully specifies it, so the accepted set is closed and was recovered without search.

**Novel code (not in any published list).** `L L R×8 L×6 R×2 L×7 R×4 L×2` was minted by reading the jump table and was accepted on a naturally reached title screen (`real_code_after6.png`, scene byte 0x0A → 0x02). All published lists for this title contain 8-direction + Start codes for the console/DS SKUs ("Cerebro Files menu"), not this 31-press GBA code; the literal search for those sequences in this ROM returned 0 hits.

**Bounds proven by rejection** (all from a patched title screen with counter reset to 0, then real controller input, read back from a savestate):

| Input | Counter after | Scene after | Result |
|---|---|---|---|
| 30 correct presses | `0x1E` | `0x0A` (title) | Rejected |
| 31 correct presses | `0x1F` | `0x02` (debug menu) | Accepted |
| 32 presses (1 extra L) | `0x1F` | `0x02` | Extra ignored after success |
| Correct 31 with step 15 flipped L→R | `0x02` | `0x0A` | Rejected |

**Screen-space enumeration.** All 91 scene indices 1–91 were injected into the scene byte of a savestate and rendered (`scenes/s01.png`–`s91.png`). The dispatcher has 91 slots but only the handlers listed in §6 are distinct; indices 14–41 and 50–55, 67, 69–70, 72–74, 76, 78–90 all route to the common handler `0x0800C510` (gameplay/common frame). All 32 debug-menu entries were activated individually with scene-ID readback (§6a). This is a complete enumeration of the reachable cheat/debug surface.

**Negative result for the published console codes.** Search performed: 3 published 8-press sequences × 4-press prefixes × 2 encodings (u8, u16 LE) × 2 polarities (raw active-low `KEYINPUT`, active-high `~KEYINPUT & 0x3FF`) over the whole 8 MiB image = **0 hits**. The three sequences were also entered literally at the GBA main menu (`iceman_after.png`, `night_after.png`, `wolv_after.png`): no cheat effect; they only moved the menu cursor / started Story Mode. Those codes are therefore not present in this SKU (§16.11).

## 7. Validation evidence

* **Observed (emulator / savestate):**
  * Natural boot title screen, then the 31-press code → debug menu (`real_title6.png`, `real_code_after6.png`).
  * Code flag `0x03003E50`: `0x00` (pristine) → `0xFF` (after code); counter `0x030009FC`: `0x01` → `0x1F`; scene `0x03001858`: `0x2F`/`0x0A` → `0x02`.
  * 30/31/32/wrong-press bounds above with counter and scene readback.
  * All 32 menu entries launched; `Unlock NtCwlr` showed the unlock banner and flipped `0x030002F8` 0x00 → 0x01.
  * Extras screen (idx 8) opened from the debug menu although it is greyed out on a fresh main menu.
  * All 91 scene indices rendered.
* **Derived (static disassembly / decompilation):**
  * crt0 → `0x0800A32C` main → `0x0800BBE4` dispatcher + jump table `0x0800BC38`.
  * Matcher `0x08010B84`, 31-entry step table `0x08010BD4`, two step handlers, success branch `0x08010C6A`, single BL caller at `0x0800BF14` (scene 10 / title).
  * Text-bank record format and debug-menu id lists.
* **Inferred (not fully exercised):**
  * Persistence of the Nightcrawler unlock across a save/reload (the `.sav` was not inspected in detail after the unlock).
  * The exact reset path that produced counter `0x02` after a wrong press at step 15 (the step handlers only show "increment on expected key"; no explicit reset was isolated).

## 8. Unknowns

* Whether `0x030002F8` is the definitive persistent Nightcrawler flag or a transient UI byte; its writer was not isolated.
* The reset/expiry semantics for a wrong press (§6b shows the rejection, not the mechanism). §16.12-style title-screen reset windows were not measured for this code.
* Whether the second `Unlock NtCwlr` entry on page 2 differs from page 1's — both set scene `0x05` and produced the same banner; no second writer was found.
* Other titles' console codes were not re-tested on the GBA SKU beyond the three published Danger Room sequences.

## 9. Tooling

* `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep` — Phase 0/1.
* `arm-none-eabi-objdump -M force-thumb` / `force-arm` with `--adjust-vma=0x08000000` — targeted disassembly.
* Capstone — Thumb literal/BL scans (`keyinput_xrefs.py`, `blscan.py`).
* REA MCP + Ghidra 12.1.4 raw-binary import (ARM:LE:32:v7, base 0x08000000) — `procedure_pseudo_code` on `FUN_0800A32C`, `FUN_0800BBE4`, `FUN_080000C0`; session closed after analysis.
* mGBA 0.10.5 + Xvfb `:316` + openbox + xdotool + scrot + ImageMagick `montage` — dynamic walk and screenshots.
* Python scripts in `/tmp/opencode/xmenofficial/`: `parse_bank.py`, `strings_bank.py`, `ptrscan.py`, `findptr.py`, `blscan.py`, `buttonsearch.py`, `idsearch.py`, `patch_ss.py`, `patch2.py`, `enter_code.py`, `bounds.py`, `dbgtest.py`, `walk_menu.py`, `ram_evidence.py`, `realtest3.py`, `ss.py`.
* Savestate technique (§16.13): mGBA `.ss1` PNG, zlib-decompressed `gbAs` chunk (397,312 bytes); IWRAM at raw 0x19000, scene byte at raw 0x1A858. Patching the scene byte and reloading F1 gave deterministic access to all 91 scenes. GDB stub on mGBA 0.10.5 returned protocol errors, so savestate diffing was used instead.

## 10. Legal note

No ROM bytes or copyrighted assets are reproduced here; only hashes, addresses, algorithms and original observations are published.
