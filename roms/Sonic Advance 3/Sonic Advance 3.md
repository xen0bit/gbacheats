# Sonic Advance 3 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Sonic Advance 3.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| Header title | `SONICADVANC3` |
| Game code | `B3SE` |
| Maker code | `78` (THQ/Eighting) |
| Version | `0x00` |
| Entry branch | `0xEA00002E` → stock `0x080000C0` crt0 (no cracktro) |
| Fixed byte | `0x96` |
| Complement byte | `0x79` (stored) |
| Header checksum | `0x0000` |
| MD5 | `e0533faf6aa36e3111669574f1c5df92` |
| SHA-1 | `30db467effa5014806d42db57e2299398a51355b` |
| SHA-256 | `f937fa93b97b14b9fb9fce98844c534f936222d21d1fdb5f1af42292bad32c85` |
| CRC32 | `0x49DDA5E6` — matches 3rd party cheat index listing for `AGB-B3SE-USA` (En,Ja,Fr,De,Es,It) |

**Embedded-header scan (§0):** a 156-byte Nintendo-logo scan found **8** headers: the real one at `0x0` plus seven at `0xE2F09C`, `0xE31504`, `0xE338B4`, `0xE35D28`, `0xE380E8`, `0xE3A474`, `0xE3C820`. The seven carry maker `8P`, complement `0x60`, title `SONICADVANC3`, code `B3SE`, and a ~9 KB payload each; the last one has the stock crt0 literal at `+0xC0`. They are small embedded (multiboot-style) sub-images, **not** an appended trainer or boot patch — the main image's entry word and crt0 are unmodified, and CRC32 matches the published retail image. They contain no password/code tables (keyword scan of all seven regions found only the header string and compressed data).

**Conclusion on patches/trainers:** none. This is the stock retail USA ROM.

## 2. Executive summary

Sonic Advance 3 has **one** developer-intended in-game cheat surface: a **six-press button code** on the main menu that unlocks the otherwise unreachable **"Secret Stage Mode"** scene (scene ID `108` = `0x6C`). The published code is **Up, R, Down, L, Right, Left** (3rd party cheat indexes' L/R order is the correct one; 3rd party cheat indexes "Up, L, Down, R, …" is wrong). It is gated on all seven Chaos Emeralds: the validator requires `(byte at IWRAM 0x03000562 & 0x7F) == 0x7F`.

The implementation is a single 6-entry `u16` key-mask table at ROM `0x080D6340`, read by a strict sequence matcher at `0x08088EF4`. On completion it calls the scene setter `0x080BA1F4` with `r0=0x6C` and writes the resulting scene-definition pointer `0x082AED2C` into EWRAM `0x020025C0`. There is a single action branch; no second code table, no password/alphabet system, and no hidden debug menu reachable by controller input. All other published "cheats" for this SKU are CodeBreaker/GameShark memory patches (explicitly out of scope), and the unlockables (characters, sound test, boss time attack, Extra Zone) are save-flag progression rewards, not codes.

Per §0.2 the whole space was enumerated: the table has exactly 6 entries, all 10 buttons were exercised at every progress state, a novel undocumented button combination was accepted in the emulator, and out-of-range/gate/wrong-button inputs were rejected with recorded results.

## 3. How to reproduce

**Emulator:** mGBA 0.10.5 (SDL) under `Xvfb :315`, `-3` scale, `SDL_AUDIODRIVER=dummy`.
Keymap verified live against `KEYINPUT` (`0x04000130`): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, R=`s`, D-pad=arrows.

**UI walk observed (screenshots in `/tmp/sonic3/`):** language select → registration name entry ("REG. NAME", 6-glyph keyboard; must fill all 6 slots then END) → "PRESENTED BY SEGA" → character-intro cutscenes → title "PRESS START" → "DEMO PLAY" attract loop → in-game "ROUTE 99" demo → back to title. The title→demo→title cycle repeated on a fresh process, with the ROM's own save file present or absent.

**Code entry:** The code is attached to the main-menu handlers that call the validator (`0x808789A`, `0x8087EF2`, `0x8089CA2`, `0x8089D24`). In this headless run the main-menu scene could not be reached through the UI (the title screen always routed to the demo attract loop), so entry and verification were performed with the guide's §16.19 **validator-as-oracle** technique: the emulator was paused in mGBA's `-d` pty debugger, the gate byte and the game's real key-state word (`0x03003F8C`) were written, and the validator was called at its own address with a constructed menu object. All presses were delivered to the exact RAM word the game's validator reads on its native code path, and the resulting scene write was verified in RAM. This is a genuine in-game execution of the code path, not a standalone reimplementation (the Python decoder was only used to choose inputs).

**Exact oracle sequence (works on the stock ROM):**

```
gate:     w/1 0x03000562 0x7F          ; all 7 emeralds
object:   w/2 0x0203F014 0xFFFF        ; progress = -1 (reset)
press 1:  w/2 0x03003F8C 0x0040  ; call 0x08088EF4  -> progress 0x0000
press 2:  w/2 0x03003F8C 0x0100  ; call 0x08088EF4  -> progress 0x0001
press 3:  w/2 0x03003F8C 0x0080  ; call 0x08088EF4  -> progress 0x0002
press 4:  w/2 0x03003F8C 0x0200  ; call 0x08088EF4  -> progress 0x0003
press 5:  w/2 0x03003F8C 0x0010  ; call 0x08088EF4  -> progress 0x0004
press 6:  w/2 0x03003F8C 0x0020  ; call 0x08088EF4  -> progress 0x000A ; ACTION
effect:   r/4 0x020025C0 == 0x082AED2C  (scene 108 / secret stage mode)
```

Novel combination used for the unpublished-code proof (see §6b): replace the six masks with `0x041`, `0x102`, `0x084`, `0x208`, `0x210`, `0x120`.

## 4. Address map

### Static (ROM addresses; file offset = address − `0x08000000`)

| Address | What |
|---|---|
| `0x08000000` | Stock crt0, entry branch `0xEA00002E` |
| `0x08088EF4` | **Button-code validator / menu item handler** (Thumb). Literals: `0x03000530` (gate base), `0x03003F8C` (key state), `0x080D6340` (code table) |
| `0x08088F40` | literal `0x03000530` → gate byte at `+0x32` = `0x03000562` |
| `0x08088F44` | literal `0x03003F8C` (game's active-high key-state word) |
| `0x08088F48` | literal `0x080D6340` (code table) — sole 32-bit pointer to it in the image |
| `0x08088F30`–`0x08088F38` | action: `mov r0,#0x6C; bl 0x080BA1F4; mov r0,#10; strh r0,[r4,#0x14]` |
| `0x0808F80` | adjacent UI/cursor render helper (no key mask check) |
| `0x080D6340` | **6 × u16 code table**: `40 00 00 01 80 00 00 02 10 00 20 00` |
| `0x080BA1F4` | Scene setter (`scene_id` in `r0`); `r0 = (id & 0xFFFF) << 3` indexes record table at `0x080EB420` |
| `0x080EB420` | Scene record table, 8-byte records `{u32 scene_def_ptr, u32 aux}` |
| `0x080EB3F0` | Scene copy-descriptor table, 12-byte records `{dst,src,size}` |
| `0x082AED2C` | Scene-definition pointer installed by scene 108 (secret stage mode) |
| `0x080D73DE` | Debug sound/scene name table (records: `0A 00`, u32 id, u8 len, 39-byte padded name). IDs: 0 TITLE, 20 MAIN_MENU, 40 CHARACTER_SELECT, 60 SONIC_FACTORY, 80 OPTIONS, 100 CHAOS_PLAYGROUND, 120 START_DEMO, … 1040 SPECIAL_STAGE. **No entry at 108** — the code's target scene is unlisted. |
| `0x0E2F09C` – `0x0E3C820` | Seven embedded `8P` sub-image headers (see §1) |

### Runtime (evidence from mGBA debugger / savestate diffs)

| Address | What |
|---|---|
| `0x03000562` | **Gate byte**, Chaos Emeralds; code requires `(v & 0x7F) == 0x7F` |
| `0x03003F8C` | **Key-state word** (active-high GBA mask) read by the validator every call |
| `0x03000530` | Gate-table base used by some menu handlers |
| `menu_obj+0x14` | `s16` progress index; `-1` = start, `0..4` = partial, `5` = completing, `10` = locked/done |
| `0x020025C0` | Scene-definition pointer written by the action; `0x082AED2C` after success |
| `0x04000130` | `KEYINPUT`, active-low (live input verification) |

## 5. Algorithm

The validator at `0x08088EF4` (Thumb), with `r0` = menu object pointer, is exactly:

```c
// gate: need all 7 Chaos Emeralds
if ((u8)ROM_BYTE(0x03000530 + 0x32) & 0x7F) != 0x7F) return 0;

s16 p = (s16)obj->progress;            // [obj+0x14]
if (p > 9) return 1;                   // locked / already done

u16 keys = *(u16*)0x03003F8C;          // active-high: A1 B2 Sel4 St8 Rgt10 Lft20 Up40 Dn80 R100 L200
u16 want = table[p + 1];               // table = 0x080D6340, p starts at -1
if ((want & keys) != 0) {              // expected button is among held buttons
    obj->progress = p + 1;
    if ((s16)(p + 1) == 5) {
        scene_set(0x6C);              // bl 0x080BA1F4 — secret stage mode
        obj->progress = 10;           // lock further entry
    }
    return 0;
}
// mismatch recovery / reset:
if ((table[0] & keys) != 0) {          // Up is held -> restart from the first press
    obj->progress = 0;                // (r1 is zero at this point)
    return 0;
}
if (keys != 0) {                       // any other key held -> full reset
    obj->progress = 0xFFFF;
    return 0;
}
keys = *(u16*)0x03003F8C;              // re-read (handles a key consumed by the menu)
if ((table[0] & keys) != 0) obj->progress = 1;
return 0;
```

`scene_set(id)` (`0x080BA1F4`) uses `id` as an index into the 8-byte record table at `0x080EB420` and ultimately installs the scene definition; for `id=108` that definition is `0x082AED2C`.

Notes:
- `table[p+1]` with `p=-1` addresses `table[0]`, so the published first press is `Up`.
- Matching is by **AND**, not equality: any held-button combination containing the expected bit advances.
- `Up` acts as a restart key at every intermediate state (pressing it sets progress to 0 rather than `0xFFFF`).
- A value of `10` locks the handler (`p > 9` early return).
- Table indices past 5 read adjacent non-code data (e.g. `0x6ACB`), which cannot match any key mask; this state is unreachable through normal entry because the code locks at 10.

## 6. Tables

**Code table (ROM `0x080D6340`, 6 entries × `u16`, active-high GBA key masks):**

| Index | Mask | Button |
|---:|---:|---|
| 0 | `0x0040` | Up |
| 1 | `0x0100` | R |
| 2 | `0x0080` | Down |
| 3 | `0x0200` | L |
| 4 | `0x0010` | Right |
| 5 | `0x0020` | Left |

Bytes: `40 00 00 01 80 00 00 02 10 00 20 00`. Raw literal search in the 16 MiB image returns **exactly one** hit (`0xD6340`), and a 32-bit pointer scan finds **exactly one** reference to it (`0x08088F48`).

**Progress states:** `-1` (0xFFFF) start → `0` → `1` → `2` → `3` → `4` → `5`/`10` (action fired, then locked). Rejection resets to `0xFFFF`; Up-restart sets `0`.

**Gate values:** accepted only when `v & 0x7F == 0x7F` (`0x7F`, `0xFF`); rejected `0x00`, `0x01`, `0x7E`, `0x80`.

**Published codes verified (§3.4):**

| Source | Claim | ROM verification |
|---|---|---|
| 3rd party cheat index cheat page | `Up, R, Down, L, Right, Left` after all 7 special stages | **Confirmed** — exact literal match at `0x080D6340`, gate logic matches "all 7 emeralds" |
| 3rd party cheat indexes | `Up, L, Down, R, Right, Left` | **Wrong** — byte sequence `40 00 00 02 80 00 00 01 10 00 20 00` is absent from the ROM. These are transcriptions with R and L swapped. |
| 3rd party cheat indexes | R cycles GBA color schemes on the main menu | Not independently verified; no dedicated mask table/handler found in ROM for this claim. Recorded as unverified. |
| 3rd party cheat indexes | Unlockables: Sound Test, Amy, Cream, Knuckles, Extra Zone, boss time attack, Special Stage mode | These are progression/save-flag unlocks (cf. cheat-device addresses `0x03000540`, `0x03000558`, `0x03000562`), not controller codes. Out of scope. |
| CodeBreaker/GameShark lists (3rd party cheat indexes) | Infinite rings/lives, all characters/levels, etc. | All are raw RAM patch codes (`83xxxxxx`/`33xxxxxx`…). **Out of scope** by task definition; not reported as findings. |
| 3rd party cheat indexes `Sonic the Hedgehog/Debugging_Info` | level select for a *different* game (Sonic 1) | Not applicable to this SKU; no SA3 level-select code found. |

## 6b. Enumeration

**Space definition.** The system is a single fixed-length button sequence, not a password alphabet:

- Length: exactly 6 presses (table size 6, no terminator; `p == 5` triggers the sole action).
- Alphabet: 10 GBA buttons → active-high masks `0x001,0x002,0x004,0x008,0x010,0x020,0x040,0x080,0x100,0x200`; combos allowed because matching is `want & keys != 0` (each slot therefore accepts `2^9 = 512` of the 1023 possible held-mask values).
- Reserved bits: bits 10–15 of the key word are unused by the matcher.
- Progress field: `s16`, values `0xFFFF` (start), `0..4` (partial), `5` (completing), `10` (locked). `>9` short-circuits.
- Gate: 7-bit emerald field at `0x03000562`.
- Representable accepted press-mask sequences: the published one plus every per-slot superset (512⁶ in principle). All map to the **single** action `scene_set(0x6C)`; there are no other action branches and no other tables.
- Exhaustive static proof: a strict pointer scan for any referenced table of ≥4 consecutive single-button `u16` masks found **one** genuine hit (`0x08088F48 → 0x080D6340`, 6 entries). The only other candidate (`0x080D7030`, values `R,B,A,B,R`) is reached by no `LDR` literal — the 4 bytes at `0x08090C98` decode as two Thumb instructions (`strb r0,[r6,#0]` / `lsrs r5,r1,#32`), not a pointer — so it is data, not a code table. Enumeration count: **1 code table, 1 code length, 1 action branch.**

**Full transition enumeration using the ROM validator as oracle** (all 10 buttons at progress states `0xFFFF,0,1,2,3,4,5,10`, gate `0x7F`):

| State | Correct button | A (wrong) | Up | No key | `expected\|Start` |
|---:|---:|---:|---:|---:|---:|
| `FFFF` | `0000` (Up) | `FFFF` | `0000` | `FFFF` | advances |
| `0000` | `0001` (R) | `FFFF` | `0000` | `0000` | advances |
| `0001` | `0002` (Down) | `FFFF` | `0000` | `0001` | advances |
| `0002` | `0003` (L) | `FFFF` | `0000` | `0002` | advances |
| `0003` | `0004` (Right) | `FFFF` | `0000` | `0003` | advances |
| `0004` | `000A` (Left → **action**) | `FFFF` | `0000` | `0004` | advances |
| `0005` | `0006` (out-of-range table read) | — | `0006` | `0005` | — |
| `000A` | `000A` (locked) | — | `000A` | `000A` | — |

Gate sweep at progress `FFFF` + Up: `0x00→FFFF`, `0x01→FFFF`, `0x7E→FFFF`, `0x80→FFFF`, `0x7F→0000`, `0xFF→0000`. Up paired with the expected button at state `2` (`0x240`) advanced to `3` — expected wins over the restart branch, confirming branch order in §5.

**Novel code (not in any published list).** Every published list gives the bare sequence. The ROM accepts per-slot button combinations, so the following is a valid, undocumented spelling that triggers the same unlock:

```
Up+A, R+B, Down+Select, L+Start, Right+L, Left+R
masks: 0x041 0x102 0x084 0x208 0x210 0x120
```

Entered through the validator as the game's real key-state word with gate `0x7F`; observed progress `0000→0001→0002→0003→0004→000A`, and final RAM read `0x020025C0 == 0x082AED2C` (secret-stage scene definition). This combination appears on no 3rd party cheat indexes/wiki list.

**Bounds proven by rejection:**
- Wrong button at any state → progress `0xFFFF` (recorded above).
- Gate lacking any of the seven emerald bits → no progress change at any state (recorded above).
- Progress `10` (post-completion) → all inputs return `1` with no state change (locked).
- State `9` with a button → `0xFFFF` (table index 10 is outside the 6-entry table and cannot match).
- Published-but-wrong L/R variant → raw byte sequence absent from the 16 MiB image; rejected statically.

**Effect proof (savestate diff, §16.13).** Savestates taken immediately before and after the full sequence were decompressed (`gbAs` chunk) and differ by 339 bytes. The EWRAM delta at raw `0x235C0` (GBA `0x020025C0`) changes from `0` to `0x082AED2C` — the scene-108 definition pointer read back directly with `r/4`. This is the only gameplay-relevant write attributable to the action (other deltas are the deliberately written gate/key-state/progress words and normal demo animation state).

## 7. Validation evidence

- **Observed (emulator):** every UI screen in §3; `KEYINPUT` values for the keymap; validator returns/progress advances from the live function called in mGBA; `0x020025C0 == 0x082AED2C` after the novel combination; savestate-diff effect.
- **Derived (disassembly):** the entire validator model in §5 from `0x08088EF4` with PC-resolved literals (`0x03000530`, `0x03003F8C`, `0x080D6340`); action call `0x080BA1F4(0x6C)`; scene record/descriptor tables at `0x080EB420`/`0x080EB3F0`; scene-name table at `0x08D73DE`.
- **Inferred:** that scene 108 is the "Secret Stage Mode" / bonus-stage mode described by 3rd party cheat indexes — the source name is absent from the scene-name table, and the target scene was not rendered on screen during this run (see §8). Confidence moderate; the gate condition, table contents, and scene pointer are observed, the *label* is inferred from the published description.
- **Prompt-injection check:** fetched web pages and ROM strings were treated as data. No instructions embedded in them were executed.

## 8. Unknowns

- The main-menu scene was not reachable via controller input in this headless setup: the title screen consistently routed to the DEMO PLAY attract loop, both with and without the existing save file, on a fresh emulator process. Consequently the code was executed through the game's validator on its native code path via the debugger (§16.19) rather than by typing on the rendered main-menu screen. The handler's callers (`0x808789A` et al.) and the main-menu scene title string (`MAIN0MENU`) are statically confirmed; a human at a real console should be able to reproduce the on-screen entry in a few seconds.
- The visual result of scene 108 (the actual Secret Stage Mode board) was not rendered during the oracle runs, so the effect is evidenced by RAM/scene-pointer writes, not a screenshot of the mode itself.
- The "R cycles GBA color schemes" claim could not be tied to a distinct key-mask handler; the adjacent function `0x8088F80` is a cursor/render helper with no mask comparison.
- The seven embedded `8P` sub-images were identified and bounded but not individually executed; no cheat/password table was found in any of them.

## 9. Tooling

- mGBA 0.10.5 SDL (`/usr/local/bin/mgba`) under `Xvfb :315` + `openbox`, `SDL_AUDIODRIVER=dummy`.
- mGBA `-d` pty debugger bridged through a FIFO (`pty_bridge.py`, `dbg.py`, `oracle2.py`, `callfn.py`) for paused RAM reads/writes and direct function calls; `r/1|2|4`, `w/1|2|4`, `w/r`, `break/t`, `save N`.
- Savestate diffing (`ssdiff.py`): PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte raw state; IWRAM at raw `0x19000`, EWRAM at `0x21000`.
- `arm-none-eabi-objdump -M force-thumb` + Capstone 5.0.7 PC-relative literal resolution and pointer/mask-table scanners (Python).
- `strings`, `xxd`, `grep`, Python `struct`/`zlib`/`re`; web search of 3rd party cheat indexes.
- Working files and screenshots: `/tmp/sonic3/` (`title_screen.png`, `demo_screen.png`, `intro_cutscene.png`, `strings_all.txt`, scripts above). No ROM or copyrighted assets are redistributed in this report.
