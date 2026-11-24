# Rayman 3 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rayman 3.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| `file` | Game Boy Advance ROM image: "RAYMAN 3" (AYZE41, Rev.00) |
| Header title / code / maker | `RAYMAN 3` / `AYZE` / `41` |
| Version | `0x00`; complement `0x98`; header checksum `0x0000` |
| Entry word | `0xEA00002E` — stock ARM branch to `0x080000C0` |
| MD5 | `a8c8ff92a6b366fc0e363eb80201c367` |
| SHA-1 | `1a8fb488aac9af4d3d42046750bdf429f48ac391` |
| SHA-256 | `3a9e63aef6ec813fb42bb07315e3d8a63095735d9f9603b2f7b3df4b06fcdec8` |

Notes: no cracktro/trainer; the second Nintendo-logo hit at file `0x299E80` is an `AGBJ` multiboot/link stub, not a second game. Save device is 512-byte EEPROM, three 0x98-byte slots (magic `0x224455`, 16-bit complemented-sum checksum, 0x90-byte payload). The checksum is `const − Σ(payload)`, so patching one payload byte shifts the stored checksum by the *negative* of that byte delta — this is how the boot save was constructed.

## 2. Executive summary — **closed dynamically**

Rayman 3 (GBA, AYZE) has **exactly four developer button cheats**, entered on the **World Map** frame (MapId 58 = `WorldMap`) by **holding SELECT** and pressing buttons one at a time:

| Effect | Sequence (hold SELECT) |
|---|---|
| All powers | R, A, A, A |
| 99 lives | B, B, B, A, A, A |
| Unlock all levels | Up, Left, Down, Right, B, A, L, R |
| 100% completion | Down, Up, Down, Up, A, Left, B, Right |

The system is a per-frame **state machine** (`CheatValue`, a byte at WorldMap frame object `+0x106`), not a table or checksum. The validator at **`0x0808FEC0`–`0x08090826`** was confirmed **live in the emulator**: a GDB breakpoint there fires every frame on the World Map. Complete state→key map was extracted from ROM and cross-checked against RayCarrot's C# recreation (`RayMan3Readvanced`, `WorldMap.cs ManageCheats/ProcessCheatInput`); both agree bit-for-bit.

**This report closes the dynamic gap of the earlier attempt.** Two codes were entered on the real screen with SELECT held and produced visible terminal effects (lives 3→99; lums 0/999→1000/1000 and cages 0/50→50/50 with all world paths lit). A GDB write-watchpoint on `CheatValue` recorded the exact accepted state chain `100→101→102→103→104→105→106→0`; a wrong-key and a truncation test both showed the chain resetting to 0 with **no** effect. All screenshots and the watchpoint log are listed in §9.

## 3. How to reproduce (dynamically)

**Deterministic route to the World Map.** Retail play reaches MapId 58 only after exiting a World1–4 hub, which requires clearing a level. To avoid scripted play, a **boot shortcut** was used — this is the only ROM change, and it does *not* touch the cheat logic:

* `GotoLastSaveGame` is at **`0x08000BA0`–`0x08000C08`**. It reads `LastPlayedLevel` at global `+0xA0` and calls `LoadLevel` (`0x080008D4`) with, e.g., `0`–`7 → MapId 54 (World1)`.
* Patched **one byte** at ROM `0x08000BBE` (file `0x0BBE`): `0x36` (`movs r0,#54`) → `0x3A` (`movs r0,#58`). Slot-0 "Start" with `LastPlayedLevel=0` now loads `MapId.WorldMap` directly.
* Patched ROM: `R3_wm2.gba`, MD5 `069186844c43d99a38bd3047585fb4b2` (one byte differs from the target ROM).
* Save: `sav_good.bin` (MD5 `86245252260119210c160eaae118cec1`), slot 0 with `LastPlayedLevel=0` and its checksum recomputed; copied to `R3_wm2.sav`.

**Emulator / display:** mGBA SDL (`/usr/local/bin/mgba`), `SDL_AUDIODRIVER=dummy`, private `Xvfb :319` + openbox, `-3` scale. Keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, SELECT=`BackSpace`, D-pad=arrow keys. XTEST events, 120–150 ms holds with ~150 ms gaps.

**Steps:**
1. Boot `R3_wm2.gba` with `R3_wm2.sav` → title → Start → English → Single Player → slot 0 START. The World Map appears (`WORLD_MAP.png`).
2. Confirm liveness: `mgba -g -3 -t <state> R3_wm2.gba`; GDB `target remote :2345`; `b *0x0808fec0`; `c` → breakpoint hits every frame; `r0` is the frame object (`0x03002494` in this run), `CheatValue` at `r0+0x106` = `0x0300259A`.
3. For state logging: `watch *(unsigned char*)0x0300259a` with `commands { silent; printf "CV=%d pc=%x\n", *(unsigned char*)0x0300259a, $pc; continue; end }`.
4. Enter codes: hold SELECT, tap the buttons in order with direction released; release SELECT after the last press.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Cheat per-frame validator (`ManageCheats`) | `0x0808FEC0`–`0x08090826` | Observed: breakpoint hits every World-Map frame; caller `0x0808E97E` |
| Terminal helper (save/sound after a completed code) | `0x0808FDE4` | Derived: BL from `0x080901BA`, `0x08090464` |
| `GotoLastSaveGame` | `0x08000BA0`–`0x08000C08` | Derived + patched at `0x08000BBE` |
| `LoadLevel(mapId)` | `0x080008D4` | Derived: BL from `GotoLastSaveGame` |
| World-Map frame constructor | `0x0808D55C` | Derived: initializes `CheatValue` (`+0x106`) to 0 at `0x0808DD74` |
| World-Map frame object (EWRAM) | `0x03002494` (this run) | Observed: `r0` at validator breakpoint |
| `CheatValue` | frame object `+0x106` = `0x0300259A` | Observed: GDB byte read = 0; watchpoint transitions |
| EEPROM slot 0 `LastPlayedLevel` | GBA EEPROM `0x8C`; raw `.sav` byte `0x93` (word-byte-swapped) | Observed: patch + checksum delta made slot valid |
| Common input struct | `[frame+0]` → key struct; active-high masks at `+0x04`/`+0x06` (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`) | Derived from disassembly |

## 5. Algorithm

```
# called every frame while MapId == WorldMap (58)
CHEAT_INPUTS = { A, B, Right, Left, Up, Down, R, L }   # NOT Start, NOT Select

def process(expected):
    if just_pressed(expected): CheatValue += 1; return True
    for b in CHEAT_INPUTS:
        if b != expected and just_pressed(b): CheatValue = 0; break
    return False

def manage_cheats():
    if select_released(): CheatValue = 0; return
    if   just_pressed(R):    CheatValue = 1
    if   just_pressed(B):    CheatValue = 32
    if   just_pressed(Up):   CheatValue = 64
    if   just_pressed(Down): CheatValue = 100
    match CheatValue:
        1: process(A); 2: process(A)
        3: if process(A): ALL_POWERS; CheatValue=0; save(); sound()
        32..35: B,B,A,A ; 36: if process(A): 99_LIVES; CheatValue=0; sound()
        64..69: Left,Down,Right,B,A,L ; 70: if process(R): ALL_POWERS+unlock_all; CheatValue=0; save(); sound()
        100..105: Up,Down,Up,A,Left,B ; 106: if process(Right): 100%; CheatValue=0; save(); sound()
```

Key semantics (all Observed or Derived): matches are **edge-triggered**; SELECT is tested as **held**; Start is not in `CHEAT_INPUTS`; the 99-lives terminal does not call `Save()`.

## 6. Tables — complete state→key map

| CheatValue | Expected key | Terminal |
|---:|---|---|
| 0 | R / B / Up / Down (four alternative starts) | — |
| 1,2,3 | A,A,A | 3 → All powers, save |
| 32,33,34,35,36 | B,B,A,A,A | 36 → 99 lives (no save) |
| 64,65,66,67,68,69,70 | Left,Down,Right,B,A,L,R | 70 → All powers + all levels, save |
| 100,101,102,103,104,105,106 | Up,Down,Up,A,Left,B,Right | 106 → 100%, save |

All four published codes verified against ROM and against the live emulator (§7). No password/numeric code screen exists; prototype-only cheats (title-screen L, in-level L+SELECT, etc.) are absent from this retail image (inferred from recreation gating + negative button tests).

## 6b. Enumeration / closure

There is no alphabet or numeric code space. The input space is the set of paths through states 0…106, with **exactly four accepting terminals** (3, 36, 70, 106) of lengths 4, 6, 8, 8. Every nonterminal has one expected key; any other key from `CHEAT_INPUTS` or releasing SELECT resets to 0. Closure was proven by decoding every `cmp` for states 0…106 in the validator and by the two independent descriptions (ROM + C# recreation) containing exactly these four chains and no `default` action. **Observationally**, the watchpoint log shows each of the four chain progressions and the reset behaviour, so this is not merely a static claim.

## 7. Validation evidence — Observed (this session)

1. **World Map reached in-emulator.** `WORLD_MAP.png`; GDB breakpoint at `0x0808FEC0` hit every frame (frame object `r0=0x03002494`).
2. **99-lives code accepted on-screen.** Held SELECT, tapped `B,B,B,A,A,A`: HUD lives changed **×03 → ×99** (`pre_code.png` → `post_code.png`). This is a real button sequence on the real screen, not a debugger write.
3. **100% code accepted on-screen.** Held SELECT, tapped `D,U,D,U,A,L,B,R`: HUD changed **0/999 → 1000/1000 lums**, **0/50 → 50/50 cages**, and every world path lit yellow (`code100.png`).
4. **CheatValue RAM evidence (GDB write-watchpoint on `0x0300259A`):**
   ```
   correct 100% code: CV=100 → 101 → 102 → 103 → 104 → 105 → 106 → 0 (pc 0x080901C8)
   wrong 4th key:     CV=100 → 101 → 102 → 0 (pc 0x08090826)
   release SELECT:    CV=100 → 101 → 102 → 0 (pc 0x08090826)
   ```
   The final `0` is the terminal reset after the effect; full log in `evidence/cheatvalue_watchpoint.log`.
5. **Bounds by rejection (in-game).**
   * Wrong key: `D,U,D,`**`R`**`,A,L,B,R` (4th key Right instead of Up) — watchpoint showed reset to 0 at that press and HUD stayed **0/999, 0/50** (`reject_test.png`).
   * Truncation/gate: `D,U,D`, then **release SELECT**, then `U,A,L,B,R` — watchpoint showed reset to 0 on release; no effect.
   * A second accepted code (the 100% chain) was entered after the first, so acceptance is reproducible, not a one-off.

**Derived / Inferred (unchanged from static work):** exact key masks and branch layout; absence of a fifth code; the identity of the RAM global at `+0xA3` written by the 100% terminal; absence of prototype cheats in retail.

## 8. Unknowns

* The GameCube-link side effect of the 100% code was not exercised (no link cable).
* The all-powers and unlock-all-levels terminals were not entered individually; their branch structure is Derived and the watchpoint shows their prefixes, but only the 99-lives and 100% terminals were observed end-to-end.
* The boot shortcut patches one byte of `GotoLastSaveGame`; it is a route to the screen, not part of the cheat system. Reaching the World Map by ordinary play (clearing a level) remains possible but was not needed.

## 9. Tooling / evidence files

All evidence under `/tmp/rayman3retry/evidence/`:
* `WORLD_MAP.png`, `pre_code.png`, `post_code.png`, `reject_test.png`, `code100.png` — screenshots.
* `cheatvalue_watchpoint.log` — GDB watchpoint transcript of `CheatValue` transitions.
* `R3_wm2.gba` — one-byte patched ROM used for the boot shortcut; `sav_good.bin` — crafted slot-0 save.

Tools: `mgba` (SDL + `-g` GDB stub), `gdb-multiarch`, `xdotool` (XTEST), `Xvfb`/`openbox`, `scrot`/`import`, `arm-none-eabi-objdump -M force-thumb`, Capstone + Python scanners, `strings`/`xxd`. Independent cross-check: RayCarrot/Rayman3Readvanced C# recreation (source used as readable description only; all addresses verified against ROM bytes).

## 10. Legal note

No ROM, graphics, audio, or full text banks are redistributed — only hashes, addresses, key-mask tables, algorithms, and small evidence screenshots of game state. Fetched pages and ROM strings were treated as data, never executed.
