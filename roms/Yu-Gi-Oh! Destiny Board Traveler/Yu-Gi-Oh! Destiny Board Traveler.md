# Yu-Gi-Oh! Destiny Board Traveler (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Yu-Gi-Oh! Destiny Board Traveler.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `YUGIOU DBT` |
| Game code | `BYDE` (BYDEA4) |
| Maker | `A4` (Konami) |
| Version | 0x00 |
| Header checksum | 0x0000 (rebuilt-header artifact); complement byte 0xDC |
| Entry word | `0xEA00002E` — stock crt0 branch (retail image, not a patched cracktro) |
| MD5 | `875524c19ada69a0c9f3e585e6bedaa2` |
| SHA-1 | `df001a60b7ab52e9735906fcd80f6c8b834ed684` |
| SHA-256 | `ca818f32cba69d4ade8bdea200ae39206747c50d6d4f256eca89b81c357caff4` |

Developer KCEJ / publisher Konami, US release 2004-10-26 (per GameFAQs/VGChartz).

## 2. Executive summary

The game has **one developer-intended cheat surface**: four **title-screen button codes** that unlock four hidden playable characters. There is no password/keypad screen and no debug menu reachable by controller input.

The four codes are stored as a table of four `u16`-mask arrays at ROM `0x087E98A8`, each 8 presses long, stored **newest-first** and terminated by `0xFFFF`. The validator at `0x08032114` scans a 16-entry ring buffer at EWRAM `0x0201DE60` backwards from the most recent press, comparing against the selected table entry; a full match writes an unlock flag in the byte array at `0x0201D770` (Grandpa = index 9, Yami Yugi = 5, Yami Bakura = 6, Kaibaman = 7). The flags are mirrored into the 32 KiB SRAM save at offsets `0x14` and `0x400C`.

Published lists (GameFAQs, VGChartz, Neoseeker, cheatcc) contain exactly these four codes; all four were verified against the ROM table and in the emulator. Crucially, the validator **tolerates extra presses before the code** (it matches the last 8 presses of a 16-entry ring). A novel 11-press input (three extra prefix presses + Grandpa's 8) was generated, accepted in-game, and verified by both the RAM flag and the Player Select screen. Bounds were proven by four in-game rejections: wrong final key, extra simultaneous key, wrong order, and too few presses.

**Observed vs derived:** code acceptance, flag writes and screen changes are **Observed** (mGBA + savestate RAM diffs + screenshots). Table layout, validator algorithm and the `0xFFFF` terminator are **Derived** from disassembly. The SRAM mirror offsets are **Derived** from binary diff of `target.sav`.

## 3. How to reproduce

1. Start mGBA with the ROM, `SDL_AUDIODRIVER=dummy`, display `:320`:
   ```
   Xvfb :320 -screen 0 1024x768x24 &
   SDL_AUDIODRIVER=dummy mgba -3 -g -t clean_title.ss1 target.gba &
   ```
2. Let the Konami splash play, press **A** (mGBA default key `x`) once to reach the "Yu-Gi-Oh! Destiny Board Traveler / 1PLAYER" title screen.
3. Enter a code **on the title screen** (not on Player Select). Use ~0.25 s key holds with ~0.25 s gaps — published notes warn "do not enter the code too quickly".
4. Press **Start** to go to Player Select. Locked characters appear as silhouettes; unlocked ones appear in color.
5. Verify the flag in RAM: EWRAM `0x0201D770` + index. Save state (Shift+F2) and read the 16 bytes at the state offset `0x21000 + (0x0201D770 - 0x02000000) = 0x231770` after zlib-decompressing the `gbAs` PNG chunk.

Keymap used (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.

## 4. Address map

| Item | Address (ROM/EWRAM) | File offset | Notes |
|---|---|---:|---|
| crt0 entry branch | `0x08000000` | 0x000000 | `0xEA00002E` |
| Keypad press handler | `0x08019D14` | 0x019D14 | writes debounced key state; literal pool at 0x08019D54 |
| KEYINPUT literal | — | — | `0x04000130` |
| Held-key state | `0x0201D6D8` / `0x0201D6DC` | — | active-low, high bits `0xFC00` set |
| Code ring buffer | `0x0201DE60` | — | 16 × `u16` masks |
| Ring write index | `0x0201DE80` (state+0x20) | — | `u8`, 0..15 |
| Script variable | `0x0201DE81` (state+0x21) | — | 2=YamiYugi, 3=Bakura, 4=Kaibaman, 5=Grandpa |
| **Code pointer table** | `0x087E98F0` | 0x7E98F0 | 4 × `u32` pointers to `0x087E98A8/BA/CC/DE` |
| **Yami Yugi code** | `0x087E98A8` | 0x7E98A8 | 8 × `u16`, then `0xFFFF` |
| **Yami Bakura code** | `0x087E98BA` | 0x7E98BA | 8 × `u16`, then `0xFFFF` |
| **Kaibaman code** | `0x087E98CC` | 0x7E98CC | 8 × `u16`, then `0xFFFF` |
| **Grandpa code** | `0x087E98DE` | 0x7E98DE | 8 × `u16`, then `0xFFFF` |
| **Validator** | `0x08032114` | 0x032114 | `(state, code_idx) -> bool`, reverse-match |
| Validator loop driver | `0x08032084` | 0x032084 | tries idx 0..3, sets script variable |
| Ring-buffer clear | `0x080321D8` | 0x0321D8 | zeroes 16 slots + index |
| Unlock flag setter | `0x0801B8B4` | 0x01B8B4 | `(index) -> flags[index] = 1` |
| Unlock flag array | `0x0201D770` | — | 16 × `u8` |
| Script-var consumer | `0x08036654` | 0x036654 | maps var 2/3/4/5 -> flag 6/7/9/5 (see below) |
| SRAM save | `0x0E000000` | file `target.sav` | 32 KiB; flags mirrored at 0x14 and 0x400C |

Flag-index map (from `0x08036654` disassembly and live verification):

| Code idx | Character | Script variable | EWRAM flag index |
|---:|---|---:|---:|
| 0 | Yami Yugi | 2 | 5 |
| 1 | Yami Bakura | 3 | 6 |
| 2 | Kaibaman | 4 | 7 |
| 3 | Grandpa | 5 | 9 |

## 5. Algorithm

Button masks are `~KEYINPUT & 0x3FF`, i.e. GBA active-high bits:

```
A=0x001  B=0x002  Select=0x004  Start=0x008
Right=0x010  Left=0x020  Up=0x040  Down=0x080  R=0x100  L=0x200
```

Simultaneous presses are OR'ed; the table uses `0x012` (B+Right), `0x140` (R+Up), `0x202` (L+B).

Validator `0x08032114(state, code_idx)` in pseudocode:

```python
A = [0x087E98A8, 0x087E98BA, 0x087E98CC, 0x087E98DE]   # YamiYugi, Bakura, Kaibaman, Grandpa; ptr table 0x087E98F0
def validate(state, idx):
    table = A[idx]
    j = 0                                   # index into code, r6
    k = (state[0x20] - 1) & 0xFF             # last written ring slot, r5
    for i in range(16):                     # r7 = 0..15
        expected = u16(table + j*2)
        if expected == 0xFFFF:
            return True                     # full code matched
        if u16(state + k*2) != expected:
            return False                    # mismatch -> reject
        j = (j + 1) & 15
        k = (k - 1) & 15
    return False
```

The driver `0x08032084` loops `idx = 0..3`; the first `validate() == True` sets the script variable via `0x080320D8/0x080320E4/0x080320F0/0x080320FC`, which `0x08036654` turns into an unlock flag. There is no checksum, no length branching beyond the `0xFFFF` terminator, and no other hidden action branch: the loop bound is exactly 4 and the table has exactly 4 pointers.

## 6. Tables

Published codes (order as typed on the title screen; recovered from ROM tables and verified in emulator):

| # | Character | Button sequence | ROM record |
|---:|---|---|---|
| 0 | Yami Yugi | R, Left, B, Right, Up+R, Right, Down, A | `0x087E98A8` |
| 1 | Yami Bakura | L, Down, Right, B+Left, R, Down, Down, A | `0x087E98BA` |
| 2 | Kaibaman | Down, B, Left, Right, Right, R, Up+R, A | `0x087E98CC` |
| 3 | Grandpa | L, B+Right, Right, B, R, Left, Down, A | `0x087E98DE` |

Raw mask arrays as stored (newest-first, before the `0xFFFF` terminator):

| Record | u16 masks (storage order) | Reversed = typed order |
|---|---|---|
| `0x087E98A8` Yami Yugi | `0001 0080 0010 0140 0010 0002 0020 0100 FFFF` | R, Left, B, Right, Up+R, Right, Down, A |
| `0x087E98BA` Yami Bakura | `0001 0080 0080 0100 0022 0010 0080 0200 FFFF` | L, Down, Right, B+Left, R, Down, Down, A |
| `0x087E98CC` Kaibaman | `0001 0140 0100 0010 0010 0020 0002 0080 FFFF` | Down, B, Left, Right, Right, R, Up+R, A |
| `0x087E98DE` Grandpa | `0001 0080 0020 0100 0002 0010 0012 0200 FFFF` | L, B+Right, Right, B, R, Left, Down, A |

The four typed sequences above are authoritative: each was entered in the emulator and set its expected flag.

Flag array `0x0201D770` base values before any code: `01 01 01 01 01 00 00 00 01 00 01 01 ...` (indices 0-4, 8, 10, 11 already set; 5, 6, 7, 9 are the four unlockable characters).

## 6b. Enumeration

**Space definition.** Alphabet = 10 button bits (`A B Select Start Right Left Up Down R L`), with OR-combination permitted. Each press is a `u16` mask with the top 6 bits zero. Each code is exactly **8 presses**, stored newest-first with a `0xFFFF` terminator. The validator's ring buffer is **16 presses**; matching examines the last 8 presses of that ring. Total syntactic input space for 8 presses is `2^80`, but the accepted set is **exactly 4 inputs** (one per table record). There is no checksum, no reserved-bit test, and no alternate-length code: the driver's loop bound is `idx < 4` (`0x08032084`) and the pointer table at `0x087E98F0` has exactly 4 entries.

**Completeness proof.** The validator at `0x08032114` is the only compare loop over the ring buffer; `0x08032084` is its only caller and iterates `idx = 0,1,2,3` unconditionally. The four table records are the only mask arrays. Unlike a checksum system, the accepted set is a literal closed set of 4 sequences (plus the tolerated prefix, see below).

**Published-list comparison.** GameFAQs, VGChartz, Neoseeker and cheatcc all list exactly these four codes (modulo transcription variants like "Right + B" vs "B+Right"). All four literals were found in the ROM table at the addresses above and accepted in the emulator. No published list contains any other button code for this SKU.

**Novel code generated and accepted.** Because the validator scans backward from the newest press and stops at `0xFFFF`, any sequence whose **last 8 presses** equal a table record is accepted regardless of preceding presses (up to the 16-slot ring capacity). Generated novel input (not in any published list):

```
Up, Down, Left, L, B+Right, Right, B, R, Left, Down, A
```
(11 presses; first 3 are a prefix, last 8 are Grandpa's code.)

Verified deterministically by patching the ring buffer at `0x0201DE60` with the first 10 masks `40,80,20,200,12,10,02,100,20,80` and write index 10 in a savestate, loading it, and pressing the final `A` in mGBA. Result: EWRAM flag `0x0201D779` (index 9) changed `0x00 -> 0x01`, and the Player Select screen showed the previously-silhouetted Grandpa character in color (`novel_crop.png`). This proves the undocumented "arbitrary prefix" branch of the validator.

A second novel variant was also accepted in live entry (3 extra prefix presses + Grandpa's 8 in an earlier run).

**Bounds proven by rejection** (all in-game, via patched ring buffer + final key press, reading the same flag):

| Test | Last input(s) | Flag 9 after | Result |
|---|---|---:|---|
| Valid Grandpa code | `... Down, A` | 1 | ACCEPT |
| Novel prefix + valid code | `... Down, A` (11 total) | 1 | ACCEPT |
| Wrong final key (`B` instead of `A`) | `... Down, B` | 0 | REJECT |
| Extra simultaneous key at step 2 (`Right+B+Start`) | full 8 | 0 | REJECT |
| Wrong order (B and Right+B swapped) | full 8 | 0 | REJECT |
| Only 7 presses (final A omitted) | `... Down` | 0 | REJECT |
| Valid code plus trailing extra key (`... A, B`) | 9 total | 0 | REJECT |

The trailing-extra rejection is especially informative: it confirms matching is anchored to the **newest** press, not suffix-tolerant in the other direction, so the extra-prefix behavior is exactly the ring-buffer window semantics, not a fuzzy matcher.

## 7. Validation evidence

- **Observed** (mGBA 0.10.5 under Xvfb :320):
  - Title screen reached reproducibly; four silhouettes on Player Select before codes.
  - Each of the four published codes set its flag (`0x0201D770` index 5/6/7/9 respectively) and made the corresponding character appear on Player Select.
  - Novel 11-press code set flag index 9 and displayed Grandpa.
  - Five rejection variants left flag 9 at 0.
  - SRAM `target.sav` contains the flag bytes at 0x14 and 0x400C.
- **Derived** (arm-none-eabi-objdump `-M force-thumb`, Capstone, Ghidra/REA decompilation):
  - Validator `0x08032114`, ring buffer `0x0201DE60`, table `0x087E98F0` → 4 records, `0xFFFF` terminator, reverse-match.
  - Unlock setter `0x0801B8B4`, script-var mapper `0x08036654`.
  - Flag indices 5/6/7/9 mapped to Yami Yugi/Yami Bakura/Kaibaman/Grandpa.
- **Inferred**:
  - The unlockables described on GameFAQs ("Chicago Map", "Domino Pier", etc.) are **not** button codes: they are save-bit/clear-condition rewards for winning with specific characters, driven by the same flag array's other bits. They were not brute-forced (§16.18: a save-bit unlock is not a code).

## 8. Unknowns

- The exact semantics of flag indices 0–4, 8, 10, 11 (set at boot; likely default-unlocked characters/maps) were not individually identified.
- The map unlocks (Chicago, Desert, Graveyard, etc.) are gated by win conditions and were not exercised; they are not button-code surfaces.
- No hidden/debug menu was found. Keyword scans for `password`, `cheat`, `debug`, `level select` over the whole 8 MiB returned no engine/debug strings — only card names containing "Secret". Text is ASCII card data; no font/tile-encoded debug bank was found. This is a bounded negative for the searched patterns, not a claim that no dead code exists anywhere.
- The JP title (`Yu-Gi-Oh! Sugoroku no Sugoroku`) may differ; only the US `BYDE` image was analyzed.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum` — Phase 0.
- `strings -t x`, `grep -abo` — reconnaissance (no debug strings found).
- `arm-none-eabi-objdump -D -b binary -marm -M force-thumb --adjust-vma=0x08000000` — disassembly.
- Capstone 5.0.7 / Keystone (Python) — LDR-literal and BL scans.
- Ghidra 12.1.4 via REA MCP (`open_binary`, `resolve_containing_procedure`, `procedure_pseudo_code`, `procedure_callers`, `search_bytes`) — decompilation of `FUN_08032114`, `FUN_08032084`, `FUN_0801B8B4`, `FUN_08036654`.
- mGBA 0.10.5 (`mgba -3 -g -t <state>`) under Xvfb :320 + openbox, `SDL_AUDIODRIVER=dummy`; xdotool XTEST input.
- Custom Python scripts (all in `/tmp/yugiohdestiny/`): `keys.py`, `dbg.py`, `dbg2.py`, `clear_ring.py`, `patch_ring.py`, `run_tests.py`, `run_tests2.py`, `run_tests3.py`.
- Savestate RAM diffing: zlib-decompress the PNG `gbAs` chunk; EWRAM begins at raw offset `0x21000`, so `0x0201D770` maps to `0x231770`.
- Evidence screenshots (`novel_select.png`, `novel_crop.png`, `sel_before.png`, `sel_after.png`, `crop_before.png`, `crop_after.png`, `title_before.png`, `title_after_grandpa.png`) are in the work dir, deliberately outside the ROM folder.

## 10. Legal note

No ROM bytes, extracted graphics, music, or copyrighted text are redistributed here — only hashes, addresses, algorithms, and original analysis scripts/observations.
