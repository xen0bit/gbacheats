# Final Fantasy I & II: Dawn of Souls (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Final Fantasy I & II: Dawn of Souls.gba` |
| Size | 16,777,216 bytes (`0x01000000`, 16 MiB) |
| Header title | `FF1&2DAWNOFS` |
| Game code | `BFFE` (maker `01`), version `0x00` |
| Header entry branch | `0xEA004681` → `0x08011A0C` (standard ARM crt0; first words `01 30 a0 e3 / 00 20 a0 e3 / 10 00 2d e9 / 00 00 50 e1`) |
| Header checksum | `0x0000`; complement byte `0xB6` (standard sum check does not reproduce `0xB6` → header was edited/rebuilt; see guide §16.1: checksum `0x0000` + bad complement is the normal signature of a rebuilt header, not evidence of a cheat). |
| MD5 | `5d29999685413c4d2bec10d3160f6ee6` |
| SHA-1 | `6472695d69661490f78245e2982e1e676c080be7` |
| SHA-256 | `bbafb77d2be577ca0a4bfcbec9fc3004b589f24478ec5e406d61645296449422` |

**Embedded-header scan:** the full 156-byte Nintendo logo at header offset `+4` occurs exactly **once**, at file offset `0x0`. This is a single GBA image, not a multi-game concatenated cart; there is no second `FF1`/`FF2` sub-ROM to search separately (§5.4b does not apply).

**Patch/trainer check:** boot branch and crt0 are stock; no cracktro/trainer signature in the first 4 KiB. No published GameShark/CodeBreaker code was in scope or tested (scope: developer-intended cheats only).

## 2. Executive summary

**No reachable developer-intended cheat system exists in this ROM.** There is no password screen, no button-code gate, no reachable hidden/debug menu, and no unlockable-code surface. The negative is bounded by (a) a full string/literal/xref search of the 16 MiB image, (b) static enumeration of the only debug subsystem present, and (c) emulator testing of every published-style button combination that could plausibly gate a debug screen, with a live breakpoint on the debug screen's draw routine as the oracle.

The ROM *does* contain a complete, self-contained **sound-test debug subsystem** (`0x08053xxx`–`0x08059xxx`) with ASCII debug labels (`MODE:PAT`, `MODE:SEQ`, `SEQ No.%02d/%02d %s`) and 61 track-name strings (34 `FF#:` FF1 tracks + 27 `FF$:` FF2 tracks). This subsystem is **dead code**: its four entry functions have zero callers and zero external data xrefs anywhere in the image — every pointer to them lives inside the subsystem's own literal pools. No game scene, menu handler, title-screen handler, or input matcher ever transfers control to it. It is therefore classified as **dead code** (§16.3, type 2), not a gated feature and not a delivered cheat.

Published-code research was attempted against 3rd party cheat indexes, Google, Bing, DuckDuckGo, Mojeek and Jina.ai. All engines returned CAPTCHAs/403/no results; the archived 3rd party cheat index article documents only unused items and regional differences, **no debug menu or cheat code**. No code literal from any version (Famicom/PSP included) could be located because none is published for this SKU.

## 3. How to reproduce

* Emulator: mGBA (`/usr/local/bin/mgba`) under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, `openbox` window manager.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold 120–300 ms (§4.2).
* Boot: `SDL_AUDIODRIVER=dummy DISPLAY=:316 mgba -3 -d "<rom>"` (the `-d` CLI debugger was used instead of `-g` because sibling sessions hold GDB port 2345; §16.2).
* Reproducing the static result:
  ```
  strings -t x -n 4 <rom> | grep -iE 'password|cheat|debug|secret|unlock|code'
  # → only: "camp equip menu switch error:%d", "menu select error:%d", "FF#: Menu Screen"
  grep -abo 'MODE:SEQ' <rom>                  # → 0x1E2ED0, sound-test debug label
  ```
* Reproducing the dead-code proof (BL/xref scan over every 2 bytes, Thumb BL `0xF000/0xF800`):
  ```
  # targets 0x080553F8, 0x080557B4, 0x080557D4, 0x08055830 → BL count 0, ptr count 0
  ```
  Thumb-bit pointers exist only internally: `0x080553F9` at file `0x553E4` and `0x557D0`; `0x080557B5` at `0x55870`; `0x080557D5` at `0x5586C`.
* Reproducing the dynamic negative: set `b/t 0x080553F9` (draw routine) in the `-d` debugger, `c`, then press each combination in §6b at the title screen and on the first playable field. No `Hit breakpoint 2` was ever produced. NOTE: `A+B+Start+Select` is the GBA BIOS soft-reset and returns to the title; it was not counted as a successful gate.

## 4. Address map

### ROM (file offset + `0x08000000`)
| Address | Meaning |
|---|---|
| `0x08000000` | Header / ARM entry branch → crt0 at `0x08011A0C` |
| `0x08011D70` | Per-frame keypad reader. Reads `0x04000130`, masks `0x03FF`, writes held mask to `0x020001F0` and new-press mask to `0x020001F4` |
| `0x080553F8` | Sound-test screen **draw** routine (Thumb). Literal pool loads debug labels `MODE:PAT`/`PAT No.`/`MODE:SEQ`/`SEQ No.` |
| `0x080557B4` | Sound-test helper: registers callbacks `0x08013859` and `0x080553F9` via `bx r1` thunk `0x0818C250` |
| `0x080557D4` | Sound-test helper (VBlank/graphic setup) |
| `0x08055830` | Sound-test **work init**: registers `0x080557D5`/`0x080557B5`, sets `[work+0x434]=0x081E2E78`, `[work+0x438]=5` |
| `0x0805661C` | Unrelated FF2 field/menu work; state IDs `0x7B`, `0x8E`, `0xA9`, `0xAE` |
| `0x0818C24C`–`0x0818C286` | Compiler `bx rN` call-via-register thunks (not real API functions) |
| `0x081E2EA0`–`0x081E2F18` | ASCII debug labels: `MODE:PAT`, `PAT No.%02d/%02d`, `:PAT`, `MODE:SEQ`, `PLAY`, `STOP`, `SEQ No.%02d/%02d %s`, `:PLAY`, `:SEQ`, `:MODE` |
| `0x08296C0C`–`0x0829707C` | 61 FF1/FF2 music track-name strings (34 `FF#:`, 27 `FF$:`) |

### RAM / I/O
| Address | Meaning |
|---|---|
| `0x04000130` | KEYINPUT (active-low) |
| `0x020001F0` | Held keys, active high: A=1, B=2, Sel=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200 |
| `0x020001F4` | Newly pressed keys |
| `0x02000584` | Pointer slot for the global game-state structure (`0x0807F15C`: `ldr r0,[0x02000584]; ldr r0,[r0]; bx lr`) |
| `[global+0xBEC]` | Current scene/state ID (read by `0x0805930`-region sound-test update; compared to `0x90`) |

Evidence: **Derived** from disassembly; `0x020001F0`/`0x020001F4` were also **Observed** live in the mGBA `-d` debugger (breakpoint at `0x08011D70`, register dump `r2=0x02001F08`, RAM read `0x00190009`).

## 5. Algorithm (of the dormant subsystem, for completeness)

The sound-test subsystem is a TOSE "work" (task) with three callbacks:

```
work_init(work):                       # 0x08055830
    set_callback(work, 0x080557D5)     # graphics/VBlank
    set_callback(work, 0x080557B5)     # input/state
    work[0x434] = 0x081E2E78           # UI layout data table
    work[0x438] = 5

helper(work):                          # 0x080557B4
    set_callback(work, 0x08013859)
    set_callback(work, 0x080553F9)     # draw

draw(work):                            # 0x080553F8
    if work[0x6458] == 0: goto tail
    if mode == PAT: draw "MODE:PAT", "PAT No.%02d/%02d", track name
    if mode == SEQ: draw "MODE:SEQ", "PLAY"/"STOP", "SEQ No.%02d/%02d %s"
```

`set_callback` is `0x0818C250` = `bx r1` (call through the pointer loaded into `r1`), not a game API. The work is never created: no BL, no branch, and no external literal pointer reaches `0x08055830`, `0x080557B4`, `0x080557D4`, or `0x080553F8`.

## 6. Tables

### 6.1 Debug labels (ASCII, `0x081E2EA0`)
`MODE:PAT`, `PAT No.%02d/%02d`, `:PAT`, `MODE:SEQ`, `PLAY`, `STOP`, `SEQ No.%02d/%02d %s`, `:PLAY`, `:SEQ`, `:MODE` — plus Japanese suffix bytes (`82 ab 82 e8 82 a9 82 a6` = "テスト") confirming these are developer test labels, not localised player UI.

### 6.2 Track-name tables (`0x08296C0C`–`0x0829707C`)
61 NUL-terminated strings: 34 prefixed `FF#:` (FF1: Prelude, Opening Theme, Castle Cornelia, Main Theme, Chaos Shrine, Matoya's Cave, Town, Shop, … Menu Screen, Airship, Mt. Gulg, Flying Fortress, Battle, Victory, End Theme, Game Over, Save Jingle, Church, Mini Boss Battle, Boss Battle A/B, Last Boss, Opening Demo, The Lute, Fanfare, Key Item Jingle, Restoration of the Crystals …) and 27 prefixed `FF$:` (FF2: Opening Theme, Battle Theme 1/2, Revival, Reunion, The Rebel Army, Town, Main Theme, Castle Pandemonium, The Imperial Army, Chocobo Theme, Tower of the Magi, Escape!, Ancient Castle, Dungeon, The Emperor's Rebirth … Finale, Prelude).

### 6.3 Debug error strings
~60 `... error:%d` strings (`ff2 camp config main error:%d`, `config select error:%d`, `p_ff2CampEquip switch error`, `name entry error:%d`, `item get error:%d`, …) at `0x08238B00`–`0x08260130`. These are compiler-assert remnants shipped in all TOSE builds and do not constitute a player-accessible menu.

## 6b. Enumeration

**Space definition:** there is no code space to enumerate — no password alphabet, no key-mask sequence table, no validator, no hidden-menu entry table, and no unlockable flag with a code-driven setter exists in the image. Consequently there is no novel code to mint and no bounds to prove by rejection; per §0.2 the negative itself is bounded below.

**Search-space bounds (what was checked, with counts):**

| Surface | Search | Result |
|---|---|---|
| Plaintext code/password literals | `strings -t x -n 4` over all 16 MiB; case-insensitive grep for `password/cheat/debug/secret/unlock/code/battle test/sound test/map warp/continue/menu/invalid` | 199,797 strings; **3** keyword hits, all debug/UI-error leftovers (§6.3). No code literals. |
| Short code-shaped ASCII (3–12 chars, `[0-9A-Z?!*-]`) | extracted and sorted | 11,687 candidates, all high-entropy compressed-data fragments; no coherent password table. |
| Debug-menu labels | grep for `sound test`, `battle test`, `warp`, `debug menu`, `secret`, `bonus`, `unlock` | **0** meaningful hits; only `QA Testers` (credit) and a garbage `TESTTUmeFm`. |
| Font/tile-indexed text | Verified the visible UI is tile-indexed (no ASCII hits for `NEW GAME`, `CONTINUE`, `CONFIG`, `OPTIONS`, `BESTIARY`); decoded the one ASCII debug bank instead. Its labels are technical (`MODE:SEQ`) and carry a Japanese "test" suffix — developer-only. | No hidden player-facing debug label exists in any encoding searched (ASCII, +0x20 folded case via `strings -i`, UTF-16 scan of the debug bank). |
| Button-code tables | u16 mask-array scan (§5.4a) driven by the derived active-high mask set; keypad readers located at `0x08011D70` and the lone literal ref to `0x020001F0` at `0x0803E860` | No multi-key sequence array; the `0x0803E860` hit is a data pool, not a matcher. |
| Debug subsystem reachability | Whole-ROM Thumb BL scan (every 2 bytes, `0xF000/0xF8xx`) + 32-bit literal-pointer scan for the four sound-test entries | BL=0 for all four; all pointer xrefs internal to the module. **Dead code proven.** |
| Published codes | 3rd party cheat indexes, Google, Bing, DDG, Mojeek, Jina.ai; CDX queries for archived cheat pages | All blocked/empty; 3rd party cheat index article contains no code or debug menu. Nothing to verify or reject. |

**Button combinations entered on the real screen (oracle = breakpoint at `0x080553F9` + screenshots):**
`L+R+Start`; `L+R+Select`; `A+B+Start+Select`; `L+R+A+B`; `Start+Select`; `L+R+A+B+Start+Select`; `Up+Down+Left+Right+A+B`; `Up,Up,Down,Down,Left,Right,Left,Right,B,A`; `Left,Right,Left,Right,Up,Down,Up,Down,B,A`; `L+R+Up+Down`; `L+R+Left+Right`; `R+Start`; `L+Start`; `A+Select`; `B+Select`; `L+R+A+B`; `Start+A`; `Start+B`.
Result: **0** breakpoint hits and **0** debug screens. (`A+B+Start+Select` is the GBA BIOS soft-reset; recorded, not counted.)

**Screens walked in the emulator:** title ("PRESS START", copyright, "Published by Nintendo"), boot crystal animation, "The winds die…" demo, full opening story sequence ("After a long journey…", "A rebel army arose…", "But their escape wasn't over…"), and the first playable field/world map. Start was used to advance and to attempt the pause menu; no hidden entry point or debug screen appeared at any of them. The title screen offers no separate game-select/options menu — Start begins a new game directly.

## 7. Validation evidence

* **Observed:** emulator boots to the documented title; button combinations produced no debug screen; the keypad globals and a live `Hit breakpoint 1 at 0x08011D70` register dump were read in mGBA's CLI debugger; screenshots `shot_00`–`shot_29` were in `/tmp/ff12/`.
* **Derived:** all addresses, the unreferenced status of the sound-test module, the mask values of the keypad globals, the ROM-vs-RAM address translation, and the meaning of the track-name tables — each from disassembly and exhaustive xref scans whose scanner was sanity-checked against a known BL (`0x8055420 → 0x0818C258`).
* **Inferred:** that the sound-test module was compiled into retail builds inadvertently (typical of TOSE/Square development builds). It is **not** claimed to be reachable; no code path was found.
* **External (attempted):** web research was blocked by CAPTCHA/403; the one accessible archived 3rd party cheat index article corroborates the absence of a documented debug menu. Treated as weak corroboration only.

## 8. Unknowns

* Whether some future/production build (JP `Final Fantasy I•II Advance`, or an unexamined prototype) wires up the sound-test work. Not testable from this single `BFFE` US image.
* The exact original source-level gate, if any, that the removed development build used to launch the sound test (no caller survives in this ROM to inspect).
* The in-game Config/pause submenus were not visually enumerated in full because the game's opening story is long and the attract loop returns to the title; the negative for a hidden menu rests on the static searches and entry-combination tests above, not on a claim that every submenu pixel was inspected.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo` — Phase 0/1.
* Python `struct` scripts for embedded-header/logo scanning, literal-pointer scanning, Thumb BL/BL-target scanning and `LDR [PC,#imm]` literal resolution.
* `arm-none-eabi-objdump -D -b binary -marm -M force-thumb --adjust-vma=0x08000000` — disassembly.
* REA MCP + Ghidra 12.1.4: full 16 MiB raw-ARM import timed out at the 330 s startup deadline; a 25 KiB trimmed window (`/tmp/ff12/soundtest_window.bin`, base `0x08054000`) was analysed instead and used to decompile `FUN_0805501C`, `FUN_080557B4`, `FUN_080557D4`, `FUN_0805661C`. Session closed afterwards.
* mGBA with `-d` CLI debugger driven through a FIFO (`stdbuf -oL -eL`) for breakpoints and RAM reads; Xvfb `:316` + openbox + xdotool + scrot for screen walking. Used `-d` because sibling sessions hold the single-client GDB stub port.
* Web tools: `webfetch`/`websearch` against 3rd party cheat indexes, Wayback Machine, Google, Bing, DuckDuckGo, Mojeek, Jina.ai — all blocked or empty as documented.

**Legal note:** no ROM bytes or copyrighted assets are reproduced here; only addresses, hashes, algorithms and the analyst's own findings are published.
