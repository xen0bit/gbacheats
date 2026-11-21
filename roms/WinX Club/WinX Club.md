# WinX Club (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/WinX Club/WinX Club.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| Header title / code / maker | `WINXCLUB` / `BWIE` / `A4` (Konami) |
| MD5 | `80acbed66f2f7a2fc88357f9a2028458` |
| SHA-256 | `a3d9b2461d5408f354a511716fdd586514ffe4af713e8d4e3a39e123a5151c65` |

All offsets below are **file offsets**; the GBA bus address is offset + `0x08000000` (code/ROM). Work copy and all evidence: `/tmp/opencode/winxclub3/`. **No patched ROM, savestate or screenshot was left in the ROM folder.**

## 2. Executive summary — what this pass established

This pass **broke the progression gate** that stopped both earlier passes. The gate is not a story item: it is a one-byte **system handler selector** in IWRAM at `0x03003C80`. Writing `0x14` to it in a savestate makes the game call the warp-menu handler `0x08038D2D` on the next frame with no controller input. The warp menu's destination list is built from a flag array at `0x03003478`; setting flag `0x37` adds the Alfea destination **Learning Annex**, and pressing A teleports there. A second, independent state word — the **scene/destination byte at `0x02033C34`** — was also located; writing a scene ID there and forcing handler `0x0F` (teleport) loads **any** of the 39 scene IDs `0x00`–`0x26` directly. Both mechanisms were verified on screen with screenshots and RAM reads.

The trophy-case accept path is confirmed at byte level (two correct-code messages, zero wrong-code strings, spoken `0001` in five languages, no digit constant in either safe script), but **the native accept comparator itself was still not reached on screen**: the display cases visible in the forced Alfea scene did not produce a dialog on A/B at any tested position, and none of the 24 system handlers is a password keypad. This is reported as a bounded negative with the exact searched spaces, not as "progression blocked".

## 3. The gate — exact byte-level proof (NEW)

### 3.1 Handler selector `0x03003C80`

`0x0801837C` registers a handler:
```
0801837C  0e4a  ldr r2,[pc,#0x38]     ; literal @0x080183B8 = 0x03003C84  (handler table base)
08018380  5050  str r0,[r2,r1*4]      ; table[r1] = r0   (r1 = handler index)
```
`0x08018386` / `0x08018390` set/read the current handler index:
```
08018386  0c49  ldr r1,[pc,#0x30]     ; literal @0x080183B8 = 0x03003C84
0801838A  subs r1,#4                  ; -> 0x03003C80
0801838C  strb r0,[r1]                ; selector BYTE = index
08018390  0948  ldr r0,[pc,#0x24]     ; -> 0x03003C84
08018394  subs r0,#4                  ; -> 0x03003C80
08018396  ldrb r0,[r0]                ; main loop reads selector
```
`0x08018398` is the main dispatch loop: it loads the selector byte, reads `handler_table[index]`, calls it, and loops while index != `0x18`.

At boot, `0x0800EAB6` registers the warp-menu function:
```
0800EAB4  movs r1,#0x14              ; handler index 20
0800EAB6  ldr  r0,[pc,#0x268]        ; literal @0x0800ED20 = 0x08038D2D
0800EABA  bl   0x0801837C            ; register
```
Live RAM confirmation in the savestate: `0x03003C80 = 0x12` (in-game handler), `0x03003C84 = 0x08017DE7` (table[0]), and **`0x03003CD4 = 0x08038D2D`** (table[0x14]) — exactly the expected entry.

**Forcing it:** patch savestate raw `0x1CC80` (`= 0x19000 + 0x3C80`) from `0x12` to `0x14`. On load, the DESTINATION menu appears immediately with zero input (`warp1.png`). This is the same class of gate as guide §16.20.

### 3.2 Warp-menu construction and its flag gate

`0x080389CC` is the menu builder. At `0x080389EA` it does `adr r1, ...` to the literal string `"BgMenuWarp"` (file `0x38C88`) and calls `0x08004FFC` (name-based resource lookup). It then builds a 7-entry menu (`movs r1,#7` at `0x080389F8`, `bl 0x0802EF0A`).

Each destination is gated by a flag check `0x0803F708(flag)`:
```
0803F708  r2 = flag & 0x1F ; r1 = 1 << r2
0803F714  r0 = flag >> 5
0803F716  ldr r2,[pc,#0x10]   ; literal @0x0803F728 = 0x03003478  (flag array)
0803F71A  ldr r0,[r2,r0*4]
0803F71C  ands r0,r1         ; nonzero => destination enabled
```
Flags checked in the builder: `0x34,0x35,0x36,0x37,0x38,0x39,0x3A,0x3B`. In the untouched state only flag `0x34` is set (`0x0300347C = 0x00100000`), which is why only Gardenia Park is shown.

**Flag → destination map** (proved by setting one flag at a time and reading the on-screen name, `flag_scan.png`):

| Flag | Destination | Scene ID (from `tableA`) |
|---:|---|---:|
| 0x34 | Gardenia Park | 0x03 |
| 0x35 | Black Mud Marsh | 0x07 |
| 0x36 | Black Mud Glades | 0x09 |
| 0x37 | **Learning Annex (Alfea)** | **0x16** |
| 0x38 | Red Fountain Grounds | 0x0C |
| 0x39 | Red Fountain 3rd years | 0x0E |
| 0x3A | Ice Caverns | 0x13 |
| 0x3B | Storage Area | 0x19 (derived; pressing A with only this flag fell back to Gardenia — the 8th entry is not teleportable) |

Setting flag `0x37` alone (`0x0300347C = 0x00200000`) and forcing selector `0x14` makes the warp menu show only Learning Annex; pressing A loads Alfea (`alfea_scene.png`). This is how the trophy-room map was reached without any story progression.

### 3.3 Scene/destination state byte `0x02033C34` (NEW)

When A is pressed on a warp destination, the handler at `0x08038DC8` reads the menu selection, converts it through the u16 table at `0x080514B0`, and stores the resulting **scene ID**:
```
08038DD8  ldrb r0,[r0,#0xc]        ; dest code
08038DDA  ldr  r1,[pc]             ; literal @0x08038E34 = 0x080514B0
08038DDC  ldrb r1,[r1,r0]          ; scene ID from {3,7,9,0x16,0xc,0xe,0x13,0x19}
08038DDE  ldr  r0,[pc]             ; literal @0x08038E38 = 0x03003D2C
08038DE0  ldr  r0,[r0]             ; pointer = 0x02033BA4
08038DE2  strb r1,[r2,r0]          ; r2=0x90 -> [0x02033C34] = scene ID
```
**`0x02033C34` is the scene-state byte.** Verified values: `0x03` in Gardenia, `0x16` in Learning Annex/Alfea.

**Forcing an arbitrary scene:** patch that byte (savestate EWRAM raw `0x21000 + 0x33C34 = 0x54C34`) and set selector `0x03003C80 = 0x0F` (the registered teleport handler). On load the game warps to the patched scene. Verified: byte `0x03` + selector `0x0F` → Gardenia Park on screen (`force_scene_test.png`), byte left at `0x16` → Alfea. Scenes `0x00`–`0x26` were enumerated this way (`scenes_montage.png`); `0x16` is Learning Annex, `0x17` the adjoining Alfea room, `0x19` a library/stone room, `0x0E` a plant room, etc. A scene byte alone does **not** reload the room — the handler `0x0F` trigger is required (that is why the two earlier ROM patches failed).

## 4. Address map

| Item | Address / offset | Notes |
|---|---|---|
| Handler selector byte | `0x03003C80` (IWRAM raw `0x1CC80`) | set to `0x14` → warp menu, `0x0F` → teleport |
| Handler pointer table | `0x03003C84`, 4 bytes per index | `table[0x14] = 0x08038D2D` at `0x03003CD4` |
| Handler registration | `0x0801837C`; loop `0x08018398` | literal pool `0x080183B8 = 0x03003C84` |
| Warp handler | `0x08038D2D` (builder `0x080389CC`) | registered at `0x0800EAB6` |
| Warp resource name | `"BgMenuWarp"` at file `0x38C88` | ADR at `0x080389EA` |
| Flag checker | `0x0803F708`; array `0x03003478` | flag N → word `N>>5`, bit `N&0x1F` |
| Alfea warp flag | `0x0300347C` bit 21 (flag `0x37`) | set → Learning Annex |
| Scene/destination byte | `0x02033C34` (IWRAM pointer `0x03003D2C` + `0x90`) | scene ID, see table in §3.3 |
| Scene ID table | `0x080514B0` (u16) | dest code → scene ID |
| Script-function table | file `0xF1D81E`, 707 × `0x20` | `#AlfeaA00_Safe01_Open` rec 285 @ `0xF1FBBE`; `Safe02` rec 286 |
| Safe handler bytecode | file `0xF3D562` (16 B), `0xF3D66A` (4 B) | no digit/comparison constant |
| Brandon `0001` dialogue | file `0xD9BD00`–`0xD9BE76` | ASCII `30 30 30 31` at `0xD9BD41` + 4 translations |
| Safe messages | file `0xD881A4`, `0xD882C8`, `0xD88384`, `0xD88504`, `0xD885BC` | reject / 2 correct / 2 miniature grants |
| Resource manifest | file `0x55CCC` | 33 entries, `[name][u32 size][u32 offset]` |

## 5. Algorithm / accept path (byte level, unchanged from prior passes)

* Safe script `#AlfeaA00_Safe01_Open` bytecode `02 00 14 00 04 00 18 00 FE FF 01 00 02 00 03 00` and `#AlfeaA00_Safe02_Open` `10 00 00 00` contain **no digit constant, no compare, and no `3921`/`0001` literal**.
* The text bank contains exactly **two** "You have entered the correct code!" strings (`0xD882C8` Cloud Tower branch, `0xD88504` Red Fountain branch), each followed five strings later by its miniature-grant line (`0xD88384`, `0xD885BC`), and **zero** distinct wrong-code strings. Reuse of the single "It seems this safe requires a password..." line (`0xD881A4`) is the reject path.
* Therefore the accept predicate is native code comparing a RAM input buffer; the script only selects which message pair to print. All 16 MiB were searched for `3921` as ASCII/u16/u32/BCD and all 24 digit permutations; no code or script xref was found (§6b).

## 6. Tables

Published/accepted codes from walkthroughs and in-game dialogue:

| Code | Unlocks | In-ROM evidence |
|---|---|---|
| `3921` | Cloud Tower miniature | walkthroughs; plaque graphic, not a text literal |
| `0001` | Red Fountain miniature | spoken verbatim in 5 languages, ASCII at `0xD9BD41` |

Warp destination names (text bank): `0xD79708` "Alfea Main Floor", `0xD79778` "Alfea Dorm Wing", `0xD7A0B8` "Learning Annex", `0xD7A10C` "Archives", `0xD7A148` "Cafeteria", `0xD7A180` "Storage Area", `0xD7A1F8` "Professorial Offices", `0xD7A6CC` "Mini Cloud Tower", `0xD7A76C` "Mini Red Fountain".

## 6b. Enumeration

**Space definition.** 4-symbol decimal field, digits `0`–`9`, `10^4 = 10,000` strings `0000`–`9999`; alphabet/width corroborated by the in-game spoken `0001` and two 4-digit walkthrough values. No checksum, reserved bits or alternative length observed. Outcome domain is {reject, accept-CT, accept-RF} — two correct-code messages, zero wrong-code messages.

**Accepted set known:** `{3921, 0001}`. `0001` is a literal in the dialogue bank; `3921` is supported by walkthroughs but not present as a code literal (only as a graphic).

**Novel codes generated and confirmed in-game: NONE.** The native comparator and the RAM input buffer were not isolated, so no value can honestly be claimed accepted. §0.2's novel-code deliverable remains unmet.

**Bounds proven by rejection: not achieved dynamically.** No wrong-code submission was observed. The report does not claim the accepted set is exactly `{3921, 0001}`.

**Static search bounds (bounded negatives):**

| Search | Space checked | Hits |
|---|---|---:|
| `3921` as ASCII / u16 / u32 / BCD | 16,777,216 offsets each | 0 / 3 / 11 / 87 — all mid-instruction or compressed graphics, no code xref |
| 24 permutations of `{3,9,2,1}` | 16,777,216 × 24 | 1 plausible hit at `0x4155B`, disassembled: false positive |
| `0001` as ASCII in text bank | 400,216-byte bank | 5 (one per language, Brandon's dialogue) |
| Digit/comparison constant in safe scripts | records 285, 286 | 0 |
| Distinct correct / wrong code strings | full text bank | 2 correct, 0 wrong |
| Handler brute-force (selectors `0x00`–`0x17`) | 24 savestates, screenshot each (`handlers_montage2.png`) | title, inventory, magic, objectives, options, save/load, scrapbook, version, credits, warp menu, field scenes — **no password keypad** |
| Scene brute-force (`0x00`–`0x26`) | 39 savestates, screenshot each (`scenes_montage.png`) | 39 rooms identified; Alfea rooms `0x16`, `0x17`, `0x19`, `0x0E`, `0x00`, `0x01` inspected |
| Alfea display cases at scene `0x16` | A/B pressed at 12 + 4 positions around both cases (`sweep*.png`, `caseup*.png`) | 0 dialogs |

**Debug-menu / button-code finding (closed, not dead):** the warp menu is live code with an exact gate — selector `0x03003C80` must be `0x14` for `0x08038D2D` to run. No retail menu input sets it; the forced savestate patch is the proof. This supersedes the earlier "gated, selector not produced" statement: the selector address, value and dispatch routine are now fully identified.

## 7. Validation evidence

| Claim | Evidence type | Evidence |
|---|---|---|
| Handler gate at `0x03003C80` | Derived + observed | disassembly `0x0801837C/86/90/98`; live savestate `0x03003CD4 = 0x08038D2D`; `warp1.png` after patching selector to `0x14` |
| Warp destinations flag-gated | Derived + observed | `0x0803F708` flag reader; flag scan montage `flag_scan.png` |
| Alfea reached without progression | Observed | `alfea_scene.png` (Learning Annex) after flag `0x37` + selector `0x14` + A |
| Scene byte `0x02033C34` | Derived + observed | `0x08038DD8–DE2`; values `0x03`/`0x16` in savestates; `force_scene_test.png` |
| 39 scene IDs enumerated | Observed | `sc0*.png` + `scenes_montage.png` |
| Digit-entry password system | Observed (byte level) | `0001` ASCII at `0xD9BD41` + four translations; safe strings |
| Native comparator not isolated | Bounded negative | §6b search table; exhaustive literal/script/handler search |
| mGBA CLI debugger via PTY | Observed | `dc.py`, register dumps at BIOS halt |

## 8. Unknowns

1. **Native keypad routine, RAM input buffer and accept comparator — not isolated.** Excluded from scripts and literals; the only remaining implementation is native. Twenty-four system handlers and thirty-nine scenes were sampled without finding it.
2. **The exact trophy-case interactable was not identified.** The display cases in the forced Alfea scene (ID `0x16`) did not respond to A/B at any tested position; a scene byte alone does not run the scene's TriggerInit scripts, so a forced scene may lack the runtime objects that make the safe interactable. This is the precise reason no code was entered — recorded as a bounded negative, not as a story gate.
3. **Whether a third accepted code exists** — not disproven dynamically.
4. **Input alphabet/terminator** — 4 decimal digits inferred from the spoken value; no keypad glyph table decoded.

## 9. Tooling / how to reproduce

* ROM copy: `/tmp/opencode/winxclub3/game.gba`. Emulator: mGBA 0.10.5, Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `-3`. Keymap D-pad = arrows, A = `x`, B = `z`, Start = `Return`.
* `ss.py` decodes/re-encodes mGBA's PNG `gbAs` zlib chunk (raw `0x19000` → IWRAM `0x03000000`, raw `0x21000` → EWRAM `0x02000000`). `save()` must write to an existing copy of the source state.
* Minimal reproduction of the gate:
  1. Boot to a reachable screen; save a state (mGBA Shift+F1).
  2. Set raw `0x1CC80` (`0x03003C80`) to `0x14`; load → DESTINATION menu.
  3. For Alfea, also set raw `0x1CD2C` (`0x0300347C`) to `0x00200000` (flag `0x37`) before forcing the menu; press A → Learning Annex.
  4. For an arbitrary scene, set EWRAM raw `0x54C34` (`0x02033C34`) to the scene ID and raw `0x1CC80` to `0x0F`; load → teleport to that scene.
* Scripts: `dis.py` (Capstone Thumb), `litref.py` (literal-pool xrefs), `scanflags.py`, `scanscenes.py`, `scanhandlers.py`, `key.py` (XTEST), `dc.py` (mGBA CLI debugger over PTY).
* Static tools: `arm-none-eabi-objdump`, Capstone 5.0.7, `xxd`, `strings`, Python 3.

## 10. Cleanup

Only this session's own PIDs were signalled, by number: mGBA instances started from `/tmp/opencode/winxclub3` (including 839404, 839996, 840680, 841292, 841651, 842539, 842786, 843837, 846841–847745, 848739, 849062, 849413, 850025, 850241, 851xxx–852838). Xvfb `:318` and its openbox were started by this session (PIDs 837476, 837494). Other agents' displays (`:315`, `:316`, `:317`, `:319`) and processes were left untouched. No `pkill` was used. The ROM folder contains only `WinX Club.gba` and this report; all `.ss1`, `.sav`, logs and screenshots live in `/tmp/opencode/winxclub3/`.
