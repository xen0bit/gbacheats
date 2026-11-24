# Rapala Pro Fishing (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rapala Pro Fishing.gba` (4,194,304 bytes = 4 MiB) |
| Header title | `RAPALA PRO F` |
| Game code | `BRFE` |
| Maker | `52` (Activision Value) |
| Version | `0x00` (Rev.00, USA) |
| Entry word | `0xEA000030` → entry `0x080000C8` (stock crt0, Thumb `main` at `0x08000110`) |
| Fixed `0x96` | present at `0xB2` |
| Header checksum | `0x0000`; complement byte `0xA3` (expected `0xBC` for the header bytes) — rebuilt-header artifact, not a gameplay patch |
| MD5 | `1a92e287f154d62c136ebe524e75c7f2` |
| SHA-1 | `e3df6fe7a447ab30faf6fd7d4c57e88f987a5639` |
| SHA-256 | `0b60699d658b4510ae19236f3cce6f150559a89c1f237d935259258c94353ea5` |

**Embedded-header / trainer scan (§0.2, §16.1):** the 156-byte Nintendo logo occurs exactly once, at file offset `0x004` (header base `0x000`). No second header, no multiboot stub, no appended trainer block (tail 1 KiB contains no ASCII). Entry branch and first 4 KiB are the normal ARM crt0. This is a header-rebuilt retail image, not a cracktro/trainer.

## 2. Executive summary

**There is no reachable in-game cheat system in this GBA build — no password, no button code, no hidden/developer cheat menu.** The shipping ROM does contain dormant *traces* of one: RTTI class names `CheatMenuState`, `UI_CheatFlagsObserver`, `UICheatFlagsObserver`, `UI_KeypadObserver`, `UIKeypadObserver`, plus a `Pitfall Debug Screen`/profiling menu (`0x0803C974`, built `Jun 25 2004`). Static and dynamic work proves these are **dead code** (§16.3 case 2), not a gated feature:

1. The debug-screen entry at `0x08000760` has **0** BL/XREF callers (manual Thumb BL scan + Ghidra xrefs).
2. `CheatMenuState`'s string pointer `0x0803DDFC` occurs exactly **2** times in the ROM — both are *data* literals (`0x0801ACA4`, `0x0801B298`) used only as a class-name label in two UI-builder functions. Those two branches call `0x0801B870`, which is a 2-byte empty stub (`bx lr`). No cheat logic is behind them.
3. The cheat-flag/keypad observer names occur only in RTTI type-info tables (`0x0803D124`, `0x0803D134`, `0x0803DAC8`, `0x0803DB10`); there are **0** code xrefs, and no keypad/alphabet/validator tables exist.
4. No published GBA codes exist to verify: 3rd party cheat index lists **0** cheats for this SKU, 3rd party cheat indexes' GBA cheats page is empty (no archived snapshot). The `UnlockAllItems` / `UnlockAllTours` console passwords belong to the PC/Xbox SKUs and their literals are **absent** from this ROM in ASCII, +0x20, or UTF-16LE. 3rd party cheat indexes Action Replay codes are external hardware codes and are out of scope.
5. Live breakpoints on both cheat-menu class-name writes (`0x0801AC66`, `0x0801B258`) and on the debug screen (`0x08000760`) never fired while touring every reachable screen and pressing every tested key combination.

The *legitimate* progression content is a save-bit unlock system (locked lakes, challenge completion), documented in §6/§7 as a non-code unlockable (§16.18).

## 3. How to reproduce

* **Emulator:** `mgba -3` (mGBA SDL build), `DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`, Xvfb `:317` + openbox.
* **Keymap:** A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys ≥120 ms; focus the window with `xdotool windowactivate --sync`.
* **Boot path:** legal text → logo → title ("Press Start") → create/choose profile (5-character name) → **Main Menu** (Quick Fish / Challenge / Aquarium).
* **Screens walked:** Main Menu; Quick Fish → Choose Lake → AM/PM → available-fish map → Choose Lure → gameplay → Pause (Resume/Quit/Tackle Box/Music/Sound); Challenge → Choose Lake; Aquarium; title screen; credits.
* **RAM evidence method:** mGBA `.ssN` savestates are PNGs with a zlib `gbAs` chunk (`state.py`); raw state size `0x61000`, IWRAM at raw `0x19000`, EWRAM at raw `0x21000`. The active UI object is at EWRAM `0x0200C838`; its screen class-name pointer is at `+0x80` = `0x0200C8B8` and its screen-state word at `+0x84` = `0x0200C8BC`. This pointer is a reliable screen oracle (watchpoint confirmed: a write of `0x0803DDD0` at `0x0200C8B8` coincided with the Level Select screen).
* **Combos tested:** all 64 simultaneous subsets of {L,R,A,B,Start,Select} on the title screen, Main Menu, lake select, lure select, in-game and pause; plus 11 ordered sequences (Konami, L+R+A+B, Start×5, etc.) on the title screen. Result: **0** `CheatMenuState`, **0** debug screen.
* **No codes were entered** because no code entry surface exists.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | ARM entry, branch `0xEA000030` | Observed (header dump) |
| `0x08000760` | "Pitfall Debug Screen" menu entry (prints banner at `0x0803C974`, then menu loop `0x08000790`) | Derived (objdump); **0 callers** |
| `0x0801AB84` | UI builder A — case 1 → CheatMenu class label (`0x0801ACA4`), case 2 → MainMenu (`0x0801ADFC`), case 3 | Derived (Ghidra decompile) |
| `0x0801B004` | UI builder B — case 1 Level, 2 CheatMenu (`0x0801B298`), 3 Aquarium, 5/6 LevelSelect, 7 Aquarium | Derived (Ghidra decompile) |
| `0x0801B81C` | screen-state setter: r1 0→1, 1→2, 2→3, 3→4, 4→5, 6/7→6/7 (writes object+`0x84`) | Derived (objdump + watchpoint) |
| `0x0801B870` | empty stub (`bx lr`) called by both CheatMenu builder cases | Derived (objdump) |
| `0x0801AC66`, `0x0801B258` | instructions writing `CheatMenuState` pointer to object+`0x80` | Derived (objdump) |
| `0x0803C974` | "Pitfall Debug Screen" string | Observed |
| `0x0803CEA0`/`0x0803DAB0` | `UI_CheatFlagsObserver` / `UICheatFlagsObserver` RTTI names | Observed |
| `0x0803CEB8`/`0x0803DAFC` | Keypad observer RTTI names | Observed |
| `0x0803DDA8`, `0x0803DDD0`, `0x0803DD84`, `0x0803DE78`, `0x0803DE50` | class-name pointers for MainMenu, LevelSelect, Level, TackleBox(lure), Aquarium | Observed in RAM |
| `0x0803DDFC` | `CheatMenuState` name — only 2 data refs | Observed |
| `0x0803C400`-region | RTTI type-info tables (class-name pointer clusters) | Observed |
| `0x0200C838` / `0x0200C8B8` / `0x0200C8BC` | active UI object / class-name ptr / state ID | Observed (savestate + watchpoint) |
| `0x0200C638` | profile name `AAAAB` in EWRAM (saved at EEPROM `0x08`) | Observed |
| `0x04000130` | KEYINPUT; game stores active-high held/pressed/released masks in an input struct | Derived (`0x0802C400`, `0x0802F4D0`) |
| SRAM/EEPROM `0x00`-`0x1FF` | 512-byte EEPROM; magic `0xD0D0ADDE` at `0x04` and `0xE0` | Observed |

## 5. Algorithm

Not applicable — no password/checksum/button-code algorithm exists. The developmental cheat path is a single empty function call; the debug screen is an orphaned menu. Pseudocode of the only relevant logic (the dormant builder branch):

```
if (ui_object->screen_state == 2):          # 0x0801B004 case 2
    ui_object->class_name = "CheatMenuState"  # 0x0801B258
    FUN_0801B870(ui_object)                   # 0x0801B870: bx lr  (NO-OP)
```

And the screen-state setter actually used by the game:

```
set_screen_state(obj, r1):                   # 0x0801B81C
    table = {0:1, 1:2, 2:3, 3:4, 4:5, 6:6, 7:7}
    if r1 in table: obj->screen_state = table[r1]
```

## 6. Tables

**Reachable screens (RAM oracle, class-name pointer at `0x0200C8B8`):**

| Visible screen | Class-name pointer | Observed |
|---|---|---|
| Main Menu | `0x0803DDA8` (MainMenuState) | Yes |
| Choose Lake / AM-PM / Challenge select | `0x0803DDD0` (LevelSelectState) | Yes |
| Available-fish map / gameplay / Pause | `0x0803DD84` (LevelState) | Yes |
| Choose Lure | `0x0803DE78` (TackleBoxState) | Yes |
| Aquarium | `0x0803DE50` (AquariumState) | Yes |
| Title / credits | no class-name pointer (different state system) | Yes |
| **Cheat Menu** | `0x0803DDFC` (CheatMenuState) | **Never observed** |
| **Pitfall Debug Screen** | `0x0803C974` | **Never observed** |

**Menu item counts (observed by scrolling to wrap):** Main Menu = 3; Pause = 5; lakes = 5; lures = 5 (`LURE_A`–`LURE_E` in RTTI: Rattlin Fat Rap, Original Floater, Rattlin Rapala, Skitter Prop, Shad Rap).

**Unlockables (save-bit, not a code):**

| Item | State | Evidence |
|---|---|---|
| Sacramento River – California | locked (padlock graphic) until challenges are cleared | Observed on Choose Lake |
| Other lakes (Castaic, Mille Lacs, Minnetonka, Okeechobee) | selectable with the fresh profile | Observed |
| Challenge completion | RTTI `AllChallengesForLakeCompleteState`, `AllChallengesCompleteState`, `ChallengeCompleteState`, `QualifyForAquariumState`, `CongratsState` | Observed (strings) |

**Published-code verification:** no GBA codes published. Console passwords from other SKUs (`UnlockAllItems`, `UnlockAllTours`) — literal search: **0 hits** in this ROM (ASCII, +0x20, UTF-16LE).

## 6b. Enumeration

Because no code system exists, the enumeration is of the *search space that was checked* (§0.2 "negative results bounded"):

| Space | Size checked | Result |
|---|---|---|
| Simultaneous button combos | `2^6 = 64` subsets of {L,R,A,B,Start,Select}, on 6 distinct screens (title, Main Menu, lake select, lure select, in-game, pause): **384** trials, plus 64 on title again | 0 hidden screens; only normal menu navigation |
| Ordered sequences | 11 (Konami ×2, L+R+A+B, UDLR, Start×5, Select×5, A/B alternation, L/R+U/D, etc.) | 0 hidden screens |
| Debug-screen callers | manual Thumb BL scan over all 4 MiB + Ghidra xrefs on `0x08000760` | **0** callers |
| `CheatMenuState` string pointers | full-file u32 scan | **2**, both data labels (`0x0801ACA4`, `0x0801B298`) |
| Code/keypad/validator tables | `strings -t x` (58,685 strings) keyword scan for password/cheat/code/debug/secret/unlock; u32 searches for password literals and 0x030F-style key masks; RTTI xref counts | no alphabet table, no validator, no key-mask table; keypad/cheat-flag names only in type-info |
| Live breakpoint proof | breakpoints at `0x0801AC66`, `0x0801B258`, `0x08000760`, full menu tour + combos | 0 hits; emulator ran continuously |
| Published codes | 3rd party cheat indexes, PC/Xbox console passwords | nothing to verify/enter |

**No novel code could be minted because there is no validator or generator to enumerate.** This is a proven "no system" result (§16.3 case 1 + case 2), not an untested one.

## 7. Validation evidence

* **Observed:** all screenshots and RAM reads above; 512-byte EEPROM with magic `0xD0D0ADDE`; padlock on Sacramento River; breakpoints not hit during the tour; 384+64+11 input trials.
* **Derived:** dead-code classification from 0 callers / 2 data-only pointer refs; empty cheat-menu setup `bx lr`; screen-state setter mapping; UI object layout from disassembly and watchpoint; header-rebuilt (not patched) classification.
* **Inferred:** locked-lake unlock condition (complete all challenges at a lake) is inferred from RTTI state names + the padlock, not from playing a full tournament to completion. The exact save-bit offset for challenge completion was not isolated.

**Evidence type discipline:** no "code accepted" claim is made; no memory-edit/Action Replay codes were used or reported.

## 8. Unknowns

* Exact EEPROM bit offsets and progression rules for lake unlocks (would require completing tournaments in-game or reversing the save-bit helper).
* Whether an earlier/prototype build (the `Jun 25 2004` debug strings) ever had a working cheat menu — the shipped `Rev.00` image does not.
* Title/credits screens use a different state system; their class-name pointers were not identified, but combos on them were still exhaustively tested.

## 9. Tooling

* `file`, `xxd`, `strings -t x`, `md5sum`/`sha1sum`/`sha256sum` (Phase 0/1).
* `arm-none-eabi-objdump -M force-thumb` with `--adjust-vma=0x08000000`; Capstone 5.0.7; Keystone; custom Python BL/pointer scanners (`/tmp/rapala/*.py`).
* REA/Ghidra 12.1.4 (raw ARM import at `0x08000000`) for procedure decompilation and xref counts.
* mGBA SDL under Xvfb `:317` + openbox; `xdotool` XTEST input; `scrot`/ImageMagick for screenshots; `tesseract` OCR for menu labels.
* `state.py` — mGBA savestate `gbAs` zlib parser used as the RAM oracle; `watch_combo.py`/`watch_stateid.py` — mGBA `-d` write-watchpoint drivers; `bp_tour.py` — live breakpoint tour.
* No ROM or copyrighted assets were redistributed; only addresses, hashes, algorithms and findings are published.
