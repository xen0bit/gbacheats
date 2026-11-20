# Strike Force Hydra (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Strike Force Hydra/Strike Force Hydra.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| `file(1)` | Game Boy Advance ROM image: "HYDRA" (AFHE7M, Rev.00) |
| Header title / game code / maker | `HYDRA` / `AFHE` / `7M` |
| Version / complement / checksum | `0x00` / `0x41` / `0x0000` |
| Entry word | `0xEA00002E` (ARM branch to `0x080000BC`); first 4 KiB is stock crt0, no cracktro observed |
| MD5 | `531b1f6688e0c646b23f78d4019dd42e` |
| SHA-1 | `39fcdd20cb253d9a0292208902994381a3ba7c27` |
| SHA-256 | `c6bec3c11bb118be50a52d7efd9c01b75000a30c9c95eb17cba2c0e0b3a729ac` |

Header hygiene: computed complement over `0xA0..0xBC` is `0x5A` (stored `0x41`) and computed header checksum is `0x24C4` (stored `0x0000`). The header was rebuilt/edited, a common scene-release artifact; the code itself is ordinary ARM/Thumb and no appended trainer or cracktro was found. Treat all addresses below as specific to this hash.

## 2. Executive summary

The game has a **pause-screen button-code system**: five exact button sequences, checked by a single Thumb function at `0x08002530` against an 18-slot IWRAM "button history" ring at `0x03000D50..0x03000D72`. There is **no password entry screen, no alphabet, no checksum and no code table** — the sequences are inline `cmp` chains. All five published codes were verified against the ROM and accepted in mGBA with RAM evidence.

The validator checks only the most recent 6, 7 or 9 button presses. Older slots are unconstrained, so **arbitrarily prefixed (undocumented) combinations are accepted**. Two novel codes were generated and entered in the emulator: an 8-press invulnerability variant with a leading `Up` (flag `0x03001BE4`: 0→1) and a 10-press skip-zone variant with a leading `Up` (scene word `0x03000CB8`: 1→2, Zone 1A→Zone 2A). Bounds were proven by three rejected inputs (truncated, interior insertion, wrong final press). The complete action set is exactly five branches; a bounded negative for additional code systems is documented in §6b.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold about 50 ms with ~70 ms gaps; the history recorder uses edge-triggered input, so every press must be released before the next.
* Path: title → `A` → main menu (`START GAME` / `OPTIONS`) → `START GAME` → zone intro → in-flight → `Start` to reach `PAUSED`.
* Codes are entered **only while paused**. `Start` is the unpause key and must not be used as a code press (the pause handler checks the newest slot for mask `0x0008`).
* RAM evidence: mGBA `.ss1` savestate, PNG `gbAs` chunk zlib-decompressed; IWRAM begins at decompressed offset `0x19000`, so `0x03000D50` is at file offset `0x19D50`. Helper scripts in `/tmp/opencode/strikeforce/` (`ss.py`, `game.py`, `trial.py`, `testseq.py`, `ptybridge.py`, `dbg.py`).
* Codes from public lists (GameFAQs "Strike Force Hydra — Cheats", and a July 2026 Rings of Saturn article that names `0x08002530` and `0x03000D5A..0xD72`) were used as leads and verified against the bytes; published GameShark/CodeBreaker/AR codes were explicitly out of scope.

## 4. Address map

| Address (ROM / RAM) | Role |
|---|---|
| `0x0800249C` | Button-history recorder. `~KEYINPUT & 0xFFFF` → new-press mask; edge-detect against `0x03000C7C`; shift 18 u16 slots down one; write mask to newest slot `0x03000D72`; reset idle counter `0x0300161C`. If no change for 36 frames, clear all slots. |
| `0x08002530` | **Validator**. Five independent exact-match blocks, `0x08002532`–`0x08002682`. |
| `0x08001D0C` | Pause handler. Calls recorder (`0x08001D22`) then validator (`0x08001D26`) each frame while `[0x03000D80]==0`; if newest slot `== 0x0008` (Start) sets scene `0x03000CB8=5` and clears the history. |
| `0x080012EC` | History reset loop: zeroes 18 slots at `0x03000D50`. |
| `0x080055F8`, `0x08007368` | Weapon/rocket upgrade effects called by validator block A. |
| `0x08001F60` | Skip-to-next-zone routine (block D). |
| `0x08002100` | Show-ending routine (block E). |
| `0x08002E684` | Sound effect (`r0=15`) played on every accepted code. |
| `0x03000D50..0x03000D72` | 18 u16 history slots, stride 2. Press masks occupy *odd* slots (offsets `0x02,0x06,...,0x22`); the even slots hold the zero inserted on the following frame. Newest press at `0x03000D72`. |
| `0x03000D24` / `0x03000C7C` | Newly-pressed mask / previously-held mask. |
| `0x0300161C` | Idle-frame counter; 36 frames without a new press clears the history (~0.6 s at 60 Hz). |
| `0x03000CB8` | Scene/state word: `1` = paused, `2` = zone transition, `5` = gameplay. |
| `0x03001AD4` / `0x03001ADA` | Shot type / missile level (observed `0→5`, `0→3`). |
| `0x03001AF8` | Health byte (observed `2→10`). |
| `0x03001BE4` | Invulnerability flag (observed `0→1`). |
| `0x04000130` | KEYINPUT (active-low; code uses its complement). |

## 5. Algorithm

Button alphabet is the active-high GBA keypad mask:

| Button | A | B | Select | Start | Right | Left | Up | Down | R | L |
|---|---|---|---|---|---|---|---|---|---|---|
| Mask | `0x0001` | `0x0002` | `0x0004` | `0x0008` | `0x0010` | `0x0020` | `0x0040` | `0x0080` | `0x0100` | `0x0200` |

Recorder (derived from `0x0800249C`):

```text
held = ~KEYINPUT & 0xFFFF
new  = held & ~prev          # prev = 0x03000C7C
prev = held
if new == history[17]:       # no new distinct press
    history[17] = 0
    if ++idle >= 36: history[0..17] = 0
else:
    for i = 0..16: history[i] = history[i+1]
    history[17] = new
    idle = 0
```

Consequence: each press writes its mask into the newest slot and a `0` one frame later; the *presses* therefore appear in odd-numbered u16 slots, spaced 4 bytes apart, newest at `+0x22`. The validator reads those odd slots directly. There is no checksum, permutation, length gate or table lookup — each of the five blocks is a pure conjunction of exact u16 comparisons:

```text
block A: hist[+0x0E..+0x22] == [2,1,0x80,2,4,4]                 -> weapon/rocket upgrade
block B: hist[+0x0A..+0x22] == [0x20,1,0x100,0x80,2,4,4]        -> invulnerability
block C: hist[+0x0A..+0x22] == [0x20,0x40,0x80,0x10,0x200,0x100,1] -> restore HP
block D: hist[+0x02..+0x22] == [2,1,0x80,0x40,1,0x20,1,4,4]     -> skip zone
block E: hist[+0x02..+0x22] == [0x200,0x100,0x40,0x80,2,1,0x20,0x40,2] -> ending
```

Blocks D and E additionally require scene word `0x03000CB8 != 8`. All blocks fall through to the next; there is no early exit, so at most one can match in practice because their sequences differ.

## 6. Tables

| # | Branch | Sequence (press order) | Length | Effect | RAM evidence (Observed) |
|---|---|---|---|---|---|
| A | `0x08002532` | B, A, Down, B, Select, Select | 6 | Weapon/rocket upgrade + SFX | `0x03001AD4`: 0→5; `0x03001ADA`: 0→3 |
| B | `0x0800256C` | Left, A, R, Down, B, Select, Select | 7 | Invulnerability + SFX | `0x03001BE4`: 0→1 |
| C | `0x080025A6` | Left, Up, Down, Right, L, R, A | 7 | Restore HP + SFX | `0x03001AF8`: 2→10 |
| D | `0x080025E8` | B, A, Down, Up, A, Left, A, Select, Select | 9 | Skip to next zone + SFX | `0x03000CB8`: 1→2; screenshot: Zone 2A |
| E | `0x08002632` | L, R, Up, Down, B, A, Left, Up, B | 9 | View ending + SFX | screenshot: "YOUR MISSION IS COMPLETE!" |

All five match the published GameFAQs list exactly (verified literal-by-literal against the comparison chain). CodeBreaker/Action Replay entries found during recon are cheat-device codes and were not tested or reported as in-game codes.

## 6b. Enumeration

**Space definition.** The history is 18 u16 slots, each one of 11 values (zero or one of the ten button masks): `11^18` representable histories. The validator constrains only the newest 6–9 *press* slots (offsets `0x0E..0x22` for A/B/C, `0x02..0x22` for D/E), with exact equality and no checksum or reserved-bit algebra. Therefore the accepted set is **exactly five exact-match windows** (lengths 6, 7, 7, 9, 9), plus every longer sequence whose *suffix* equals one of those windows and whose extra leading presses fall outside the checked window and inside the ~36-frame (0.6 s) idle window. `Start` cannot be a prefix press because it unpauses the game when it becomes the newest slot.

**Completeness count.** The validator function spans `0x08002530`–`0x08002686` and contains exactly five comparison blocks (no other `cmp` chains, no jump table). A PC-relative-literal xref scan over the whole 4 MiB found exactly eight references to the history base `0x03000D50`: one reset (`0x080012EC`), one caller (`0x08001D2A`), one recorder (`0x080024B6`) and the five validator blocks. A scan of the code region (`<0x08080000`) for u16 arrays of ≥5 button masks with ≥4 distinct masks found **0 hits** (there is no second mask table). `strings -t x -n 4` over the ROM returns only two meaningful ASCII strings, both from the header (`HYDRA`, `AFHE7M`); no ASCII password/debug-menu text exists, and the visible UI is drawn from font/tile indices — consequently this is a button-code system with no password surface, not a text-entry system. Every reachable screen was walked: title → main menu → OPTIONS (Difficulty Easy/Hard, Button Layout A) → zone intro → gameplay → PAUSED → zone transition → ending. No password/debug menu was present on any of them.

**Novel codes (not in any published list).**

1. `Up, Left, A, R, Down, B, Select, Select` (8 presses). The leading `Up` is recorded at `0x03000D54` (offset `0x04`), outside block B's checked range `0x0A..0x22`; the remaining seven presses match block B. Entered in mGBA from the clean baseline: `0x03001BE4` **0→1**. Buffer dump after entry:
   `... 0040 0000 | 0020 0000 | 0001 0000 | 0100 0000 | 0080 0000 | 0002 0000 | 0004 0000 | 0004 0000`
   (leading `0x0040` sits two slots before the first checked value).
2. `Up, B, A, Down, Up, A, Left, A, Select, Select` (10 presses). The leading `Up` lands at `0x03000D50` (offset `0x00`), outside block D's range `0x02..0x22`. Entered from the clean baseline: `0x03000CB8` **1→2**, with the Zone 2A banner on screen (screenshot `novel_skip.png`). This is the visible-effect proof.

**Bounds proven by rejection** (each from the same clean baseline, `0x03001BE4 = 0`):

| Input | Result | Buffer evidence |
|---|---|---|
| `Up, Left, A, R, Down, B, Select` (7 presses, missing final Select) | Rejected, `0x03001BE4` stays 0 | newest slot `0x0004` but preceding slot empty |
| `Up, Left, A, R, Down, B, Up, Select, Select` (9 presses, extra interior `Up`) | Rejected, flag stays 0 | extra `0x0040` appears at offset `0x1A`, displacing `0x0002` |
| `Up, Left, A, R, Down, B, Select, A` (wrong final press) | Rejected, flag stays 0 | newest slot `0x0001` instead of `0x0004` |

A simultaneous two-key press (Select+A via xdotool) was recorded as two successive frames (`0x0004`, then `0x0001`), not as a combined mask; the game's edge-triggered recorder therefore makes true same-frame combo tests inapplicable here. This is recorded as an unknown rather than a proven bound.

## 7. Validation evidence

* **Observed**: mGBA screenshots of title, main menu, OPTIONS, zone intro, gameplay, PAUSED, Zone 2A and ending screen; savestate-derived RAM reads for every effect and every rejection test (values in §6 and §6b).
* **Derived**: disassembly of `0x0800249C` (recorder), `0x08002530` (five-block validator), `0x08001D0C` (pause gate) and the literal words at `0x080024E8`–`0x08002694`; xref counts and mask-table scan.
* **Inferred**: the exact semantics of `0x03000D80` (a gate byte that must be zero for the pause handler to run) were not isolated; codes worked whenever the game was genuinely paused. The byte written at `0x03001AD4`/`0x03001ADA` by block A is subsequently modified by the two called routines, so the observed `5`/`3` are end results, not the immediate stored constants (`4`/`2`).

## 8. Unknowns

* The meaning of `0x03000D80` and why it must be zero was not traced to its writer.
* Whether a single-frame simultaneous multi-button mask can be produced through real hardware timing (xdotool sends sequential X events).
* Whether health/invulnerability flags have readers that change gameplay duration (invulnerability RAM flag was proven set; its exact gameplay effect was not timed).
* No additional code systems were found, but the negative is bounded to: all reachable screens walked, all 8 history-buffer xrefs accounted for, 5 validator blocks counted, zero mask-table hits and zero ASCII text hits.

## 9. Tooling

`arm-none-eabi-objdump -M force-thumb`, Python 3 + `struct`/`zlib` savestate parser, `strings`/`grep` static scans, mGBA 0.10.5 (`-d` CLI debugger driven through a Python pty bridge), Xvfb + openbox, `xdotool`, `scrot`, `gdb-multiarch` (GDB stub port 2345 was occupied by another analysis, so it was not used). No ROM or copyrighted assets are redistributed; screenshots and helper scripts remain in `/tmp/opencode/strikeforce/`.
