# Super Mario Advance 4: Super Mario Bros. 3 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Super Mario Advance 4: Super Mario Bros. 3.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `SUPER MARIOD` (12-byte GBA title field, truncated "SUPER MARIO ADVANCE 4") |
| Game code | `AX4E` (USA), maker `01` (Nintendo), version `0x01` |
| Header | fixed `0x96`, complement `0x72`, checksum `0x0000`, entry `0xEA00002E` (stock, §16.1 clean) |
| Build date | `0x00263C78` = `04-01-20 13:32:00` — matches 3rd party cheat indexes "US, Australia (Rev 1) & US (Virtual Console)" |
| MD5 | `605286b3aedeffba70bf46b834b120b1` |
| SHA-1 | `532f3307021637474b6dd37da059ca360f612337` |
| SHA-256 | `53ec98fc672d94e3962ba854805ce5005e07e10a4c7ed4e7dbec7a2ca7846562` |

Note: a **second, embedded GBA header** exists at file offset `0xE9978` (ROM `0x08E9978`), code `AX4J01` (Japan, version 2), entry `0xEA00002E`. It is leftover JP-build data inside the US image (observed; role not established). The image is **not** a multi-game pad — the Nintendo logo occurs only at `0x4` and `0xE997C`.

## 2. Executive summary

**There is no in-game password, button-code, or cheat-entry system in this SKU.** The advertised "cheats" for SMA4 are gameplay tips and completion-gated unlockables (World Select after beating the game; Level Select after clearing all 90 levels), not entered codes. All published cheat-device entries (GameShark/CodeBreaker/AR) are out of scope and were used only as a RAM map.

**There is one hidden, developer-intended menu**: the *Card-e Mode Select* debug menu (scene `0x34`). Its main screen was observed in the emulator after a debugger RAM write, and its structure is `Challenge Mode` (Time Attack / Infinite 1-ups / Defeat enemies / Collect coins, levels 1–0x20) and `Scenario Mode` (S-01–S-80 with `S-N`/`TEST`/`QUICKCK` selectors). The menu is **gated**: the only two ROM writers of scene `0x34` (`0x08035714`, `0x08036430`) both sit inside debug-menu handlers and require the internal flag `0x03002DBE & 0x02`, which no reachable retail input was found to set. This is a *gated feature* (§16.3 case 4), not a button code — the published way in is an external RAM poke, which is explicitly out of scope as a "code".

The whole scene space was enumerated: **51 distinct scene values written at 106 `strb` sites**, exactly **2** of which write `0x34`. A bounded negative for a code system is proven with counts in §6b.

## 3. How to reproduce

Environment: `Xvfb :317 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy /usr/local/bin/mgba -3 -g <rom>`.
mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 100–150 ms. `KEYINPUT` at `0x04000130` reads `0x03FF` released / `0xFD` with B held; XTEST events to the focused window work, `xdotool key --window` does not.

Screen walk (scene byte read from `0x03003774` with the GDB stub at `:2345`; `set architecture arm`, `set style off`):

| Path | Keys | Scene | Evidence |
|---|---|---|---|
| Boot → SMB3 intro | Start, Start | `0x39` → `0x07` → `0x3A` → `0x09` | `fresh0c.png`, `s2c.png`, `s7c.png` |
| Game select → Mario Bros. | Down, A at `0x07` | `0x3B` | `mbstartc.png` |
| Mode select → New Game → world map | A, A | `0x09` → `0x10` → `0x11` | `m5c.png` (`WORLD 1` HUD) |
| Pause/continue panel | Start/B | `0x2E`-family | `dbg_holdc.png` |
| Debug menu (forced) | GDB write `0x34` to `0x03003774` | `0x34` | `burst2c.png`, `dbg1`-`dbg2`, `key_bbc.png` |

To force the debug menu:
```
(gdb) target remote :2345
(gdb) set style off
(gdb) interrupt
(gdb) set {unsigned char} 0x03003774 = 0x34
(gdb) continue &
```
Screenshot within ~1 s. The screen renders as a white card with blue striped border, black katakana text:
`かーど いー` (Card-e), `もーど せんたく` (Mode Select), `▷ ちゃれんじ もーど` (Challenge Mode), `しなりお もーど` (Scenario Mode). Cursor moves with Down or B. Selecting a submenu was **not** achieved by this RAM-write route (see §8) — the submenu list is from 3rd party cheat indexes documentation, not from our own screen walk.

Helper scripts used: `/tmp/sma4/gdbbridge.py` (persistent GDB-over-FIFO bridge; needed because `continue &` plus repeated `x` in a batch is unreliable), `gcmd.py`, `gset.py`, `probe.py`, `scan1534.py`.

## 4. Address map

### File ↔ ROM
`ROM address = 0x08000000 + file offset`. Key file offsets: header `0x0`, build string `0x263C78`, embedded JP header `0xE9978`.

### RAM / code (all addresses verified against the exact bytes)

| Address | Meaning | Evidence |
|---|---|---|
| `0x03002240` | global game-state base pointer (3,862 literal occurrences in ROM) | derived |
| `0x03002240 + 0x1534` = `0x03003774` | **current scene / event** (byte) | observed + derived |
| `0x03002240 + 0x17F4` = `0x03003A34` | debug sub-scene index (byte) | derived |
| `0x03002240 + 0x0B7E` = `0x03002DBE` | debug input/flag word (u16); gate bit `0x02` | derived |
| `0x03002A68/69` | saved/current world | external RAM map, cross-checked |
| `0x04000130` | KEYINPUT (active low) | observed |
| `0x08035408` | `NextScene()` — reads scene at base+`0x1534`, increments at `0x0803548A`, stores at `0x0803548C` | derived (watchpoint hit at `0x08035490`) |
| `0x080358DC` | sub-scene dispatcher: `ldrb` base+`0x17F4`, `lsls #2`, table `0x08137640`, `bl 0x080E7E54` | derived |
| `0x08137640` | table of 28 Thumb handler pointers, indices `0x00`–`0x1B` | derived |
| `0x080356C8`, `0x08036400`-region | debug-menu handlers that read flag `0x03002DBE` | derived |
| `0x08035714`, `0x08036430` | the **only** two `movs r0,#0x34; strb` writers of scene `0x34` | derived |
| `0x080E7E54` | handler-call helper used by the dispatcher | derived |
| `0x06000000`–`0x06017FFF` | VRAM; 98,304 bytes dumped to `vram.bin` | observed |

The scene byte is not referenced by a literal `0x03003774` anywhere in ROM (0 hits); all accesses are `ldr rX,=0x03002240` + `ldr rY,=0x1534` + `adds`. This is why naive pointer scans fail.

## 5. Algorithm (scene/gate model)

```
base = 0x03002240
scene      = byte[base + 0x1534]        // 0x03003774
subscene   = byte[base + 0x17F4]        // 0x03003A34
dbg_flags  = u16 [base + 0x0B7E]        // 0x03002DBE

NextScene():                            // 0x08035408
    reset per-scene fields
    scene = scene + 1                   // 0x0803548A / 0x0803548C
    return

Debug handler (0x080356C8 / 0x08036400-region):
    r4 = subscene
    r3 = dbg_flags
    if r3 & 0x009: r4++                // A/Start-like confirm
    if r3 & 0x002: scene = 0x34        // 0x08035714 / 0x08036430 -> debug main menu
    if r3 & 0x040: ...                 // cancel/decrement
    subscene = r4

dispatch_subscene():                    // 0x080358DC
    handler = pointer_table_0x08137640[subscene]
    call handler
```

No checksum, alphabet, or code validator exists anywhere in the enumerated scene/input path. The "validator" here is the gate `dbg_flags & 0x02`, whose only writers found in code are init/clear paths (`0x08000534` with mask `0xFFF3`, `0x08000586` writing 0) and the debug handlers themselves.

## 6. Tables

### 6.1 Scene values

`51` distinct values are stored into base+`0x1534` at `106` `strb` sites (complete list derived by scanning every Thumb `ldr` of literal `0x1534` and the following `strb`):

`00 01 02 03 04 05 06 07 08 0A 0B 0D 0F 10 11 12 14 15 1A 1B 1C 1D 1F 20 22 23 25 29 2C 33 34 36 37 39 3A 3B 3C 3D 3E 44 45 46 48 4A 4B 4C 4D 4F 53 55 56`

Observed live: `0x39` intro, `0x07` game select, `0x09` mode select, `0x10` file select, `0x11` world map, `0x2E` continue panel, `0x3B` Mario Bros. intro, `0x34` debug menu, `0x35`/`0x36` black/erroneous when forced out of sequence.

### 6.2 Debug menu (externally documented submenu structure; main screen observed)

| Screen | Selector range / choices |
|---|---|
| Main | Challenge Mode, Scenario Mode |
| Challenge Mode | Time Attack `T-1`…`T-20`; Infinite 1-ups `U-1`…`U-20`; Defeat enemies `E-1`…`E-20`; Collect coins `C-1`…`C-20` |
| Scenario Mode | `S-01`…`S-80`; left/right toggles `S-N`, `TEST`, `QUICKCK` (`QUICKCK` absent from JP 1.0) |

Source: 3rd party cheat index wiki debug-menu section and 3rd party cheat indexes talk page (read as data). Our emulator confirmed only the main screen; selecting a submenu via the forced route did not work.

### 6.3 Keymap / masks

GBA active-low KEYINPUT bits: `A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010 Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200`. The debug gate tests `0x002` (B-like) in an internal flag word, not in KEYINPUT directly.

## 6b. Enumeration

**Space definition.** There is no password alphabet, no code length, no checksum, and no code table in this build. The only input-derived state is the 10-bit key mask in `0x04000130`; the only hidden-state space is the scene system: 256 possible byte values for `0x03003774`, of which **51** are actually written by the game (106 write sites), plus a 256-value sub-scene index at `0x03003A34` (documented range `0x00`–`0x1B` for the 28-entry handler table at `0x08137640`).

**Validator model.** No character/button-sequence validator was found. The debug gate is a single-bit state predicate: `scene == 0x34` is produced only by two code sites, both conditioned on `dbg_flags & 0x02`. Reimplemented model above in §5; it agrees with every observed scene and with the forced `0x34` screen.

**Novel code.** Not applicable — no code system exists to mint. The equivalent novel *state* was produced: scene `0x34` was written by the debugger (a value never reached by any retail input we exercised), the debug menu appeared on screen, and the byte was RAM-verified at `0x03003774` before and after. Screenshots: `burst2c.png`, `key_bbc.png`. This state is absent from every published in-game-code list (all published SMA4 codes are cheat-device RAM pokes).

**Bounds proven by rejection.**
- Direct writes of `0x35` and `0x36` to `0x03003774` produced **black screens** (`dbg0bc.png`, `dbgokc.png`) — those values are not valid entry points in this scene context, bounding the accepted scene set.
- Direct write of `0x34` produced the menu; writing `0x34` while simultaneously neutralizing `NextScene` produced the same menu (`dbg_holdc.png`).
- The gate flag `0x03002DBE` was read as `0x0000` on every walked screen (intro, game select, mode select, world map, Mario Bros., continue panel) and while holding B at the main menu; the bit required by the two `0x34` writers was never observed set by controller input.

**Bounded negative with counts (no code system).**
1. `strings -n 4` over all 4 MiB: **0** ASCII occurrences of `PASSWORD`, `CHEAT`, `DEBUG`, `WARP`, `SECRET`, `MENU` (case-insensitive/case-shifted search included). Visible UI text is tile-index encoded, not ASCII; VRAM was dumped (`vram.bin`, 98,304 bytes) and a font/tile text bank exists — the absence of ASCII therefore proves nothing about UI text, which is why the screen walk was used.
2. Web recon: 3rd party cheat indexes/3rd party cheat index lists yield only gameplay tips and completion unlockables; **0** in-game button codes published. Every visual "code" found is a cheat-device RAM poke (e.g. `03003774:34`, `83002D52 ...`), out of scope and not counted as an in-game code.
3. Raw `u16` mask-sequence scan at both byte alignments: **2,862** runs of ≥4 halfwords with values `1..0x3FF` and ≤2 bits set. Every high-scoring cluster inspected is either ordinary code/data (alternating `0x200` literals) or the debug-handler region; **0** clusters form a terminator-delimited sequence with a validating comparison and a state write.
4. Scene/gate enumeration: **106** scene-write sites, **51** distinct scene values, **2** sites writing `0x34`, both gated; **7** reachable screens walked with RAM evidence. No other hidden-menu gate was found.

Conclusion: the negative is bounded to "no in-game code system and no controller-reachable debug-menu entry in the walked state space of this exact AX4E-01 image"; it does not claim anything about cheat-device codes or the e-Reader feature.

## 7. Validation evidence

- **Observed**: scene bytes from GDB (`0x39`, `0x07`, `0x09`, `0x10`, `0x11`, `0x2E`-family, `0x3B`, `0x34`, `0x35`, `0x36`); `KEYINPUT` `0x03FF`/`0xFD`; debug-menu screenshot; black-screen rejections; VRAM/IWRAM dumps; hashes and build string.
- **Derived**: base pointer `0x03002240` + offsets `0x1534`/`0x17F4`/`0x0B7E`; `NextScene()` at `0x08035408` (hardware watchpoint fired with old `0x35`→new `0x36` at `0x08035490`); dispatcher `0x080358DC`; handler table `0x08137640` (28 entries, `0x00`–`0x1B`); the two `0x34` writers and their `& 0x02` gate.
- **Inferred**: the debug submenu list and ranges (from external documentation — not exercised in our emulator); the role of the embedded `AX4J01` header at `0xE9978`; the mapping of dbg flag bit `0x02` to a B-like input.

## 8. Unknowns

- The debug submenus were never entered in the emulator. Writing `0x34` while a non-debug handler was active left cursor movement apparently driven by the previous screen; forced scene values `0x35`/`0x36` gave black screens. A proper entry would need to call the game's own scene-change path with `dbg_flags` bit `0x02` set, or run from a save state where the debug handler is already installed.
- No controller input was found that sets `0x03002DBE` bit `0x02`; the scan covered 71 `strh` sites near literal `0xB7E`, of which 7 combine `#2`/`OR` with a store and 5 of those are in the debug-handler block. A definitive proof would require enumerating all writers of that word on every reachable screen.
- e-Reader/e-Card level and switch content is fully outside this GBA-only setup; the embedded JP header may relate to it.
- The header complement/checksum values (`0x72`/`0x0000`) are reported as-is; a rebuilt header is a possibility but was not investigated further.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` over `0x08000000`–`0x08100000` (19 MB listing `thumb1m.txt`); Capstone for short windows.
- `gdb-multiarch` + mGBA GDB stub on `:2345` through a persistent FIFO bridge (`gdbbridge.py`), because batch GDB detaches and mGBA's stub then stops listening. `set style off` needed to strip ANSI codes. `x/4xb` used instead of `x/16bx` after watchpoint stops (GDB reported "Invalid hex digit 83" for the latter).
- Python scans: literal-xref scan for `0x1534`/`0xB7E`, `movs #imm`+`strb` pairing, u16 mask-run scan, Nintendo-logo/multi-header scan.
- `xdotool` XTEST input, `scrot` + ImageMagick crop (720×480+154+184). Screenshots saved in `/tmp/sma4/`.
- No ROM or copyrighted assets were modified or redistributed; all patches attempted were in-emulator only and were discarded with the emulator process.
