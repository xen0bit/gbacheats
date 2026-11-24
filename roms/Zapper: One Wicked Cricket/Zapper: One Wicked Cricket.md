# Zapper: One Wicked Cricket! (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Zapper: One Wicked Cricket.gba` (analysed on a byte-identical copy in `/tmp/zapper/zapper.gba`) |
| Size | `0x400000` (4 MiB) |
| `file` | Game Boy Advance ROM image: "ZAPPER" (AZPE70, Rev.00) |
| Header title | `ZAPPER` |
| Game code | `AZPE` (Europe), maker `70` (Infogrames) |
| Version | `0x00`; fixed byte `0x96`; complement `0xE8`; header checksum `0x0000` |
| Entry word | `0xEA00002E` → stock `0x080000C0` crt0 (no cracktro / appended trainer, §16.1) |
| MD5 | `9a83e6571c9543a1a4d658564f02be4c` |
| SHA-1 | `1561c4e1f4ab945299f2dfb5bb7df532ec4d4067` |
| SHA-256 | `3b8b576d236b83cd47045c140b44c4ebd389390c1a081f9de884a0c63b8a308f` |

Legal note: no ROM bytes or copyrighted assets are reproduced here; only addresses, hashes, and our own tooling are published.

## 2. Executive summary

This game has **no password / text-code system**. It has a **button-code system** played on the title/main menu and (per published sources) on the pause screen. A published main-menu code and a **novel, unpublished variant** of it were both entered in mGBA from a fresh save and both unlock **Arcade Mode** (its three sub-modes Time Attack / Orb Challenge / Ghost Race). A near-miss variant is rejected. The relevant input plumbing and the cheat-flag applier were located in the ROM; the sequence matcher itself was **not** recovered — its likely implementation and the exact accepted-set are labelled Unknown below.

The only "text entry" in the game is a 3-character **ENTER NAME** screen for the save slot (alphabet ` ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.` at `0x083292EB`, file offset `0x3292EB`). Its consumer is the save-slot label, not a validator (§16.2b): no `strcmp`-style comparison against the entry buffer was found, and it is reached only from "NEW GAME" on Story Mode.

## 3. How to reproduce

* Emulator: `mgba 0.10.5`, `SDL_AUDIODRIVER=dummy`, own Xvfb `:316` + openbox. `-3` scale, 1024×768 root, GBA viewport cropped from the window.
* Keymap (verified live with a KEYINPUT watchpoint, not assumed):

  | GBA | xdotool key | raw KEYINPUT when held | active-high bit |
  |---|---|---|---|
  | A | `x` | `0x3FE` | `0x001` |
  | B | `z` | `0x3FD` | `0x002` |
  | Select | `BackSpace` | `0x3FB` | `0x004` |
  | Start | `Return` | `0x3F7` | `0x008` |
  | Right / Left / Up / Down | arrows | `0x3EF / 0x3DF / 0x3BF / 0x37F` | `0x010 / 0x020 / 0x040 / 0x080` |
  | R | `s` | `0x2FF` | `0x100` |
  | L | `a` | `0x1FF` | `0x200` |

  Hold **100–120 ms** with a **≥300–400 ms inter-key gap**. Shorter gaps drop presses in this build. Focus the window with `xdotool windowactivate --sync` before sending XTEST events (§16.2).
* Menu path for the confirmed code:
  1. Boot ~12–16 s to the main menu (`STORY MODE / ARCADE MODE / MULTIPLAYER / OPTIONS`).
  2. With **no save file**, hold **L** and press `Right, Left, Right, Left, Up, Up, Up, Up`.
  3. Move to **ARCADE MODE** and press A. The mode-select screen (`TIME ATTACK`, `ORB CHALLENGE`, `GHOST RACE`) opens. Without the code, the same action shows "YOU MUST COMPLETE AT LEAST ONE LEVEL IN STORY MODE TO UNLOCK THIS OPTION".
* Codes tested (all with L held):

  | Sequence | Where | Source | Result |
  |---|---|---|---|
  | `R L R L U D U D` | main menu | GameFAQs "Last Level" | **Accepted** — Arcade Mode unlocked (control) |
  | `R L R L U U U U` | main menu | **novel — not in any published list** | **Accepted** — Arcade Mode unlocked from a fresh save |
  | `R L R L U D U U` | main menu | near-miss | **Rejected** — no unlock |
  | `U U L L R L R` | pause screen | GameFAQs "Infinite Lives" | Entered; no visible change observed (see Unknowns) |
  | `L D R R U U U`, `U D U L R D U` | pause screen | GameFAQs "Unlock All Levels" / "Unlimited Shield" (PS2/GC-labelled) | Entered; no visible change observed |
* Evidence screenshots (all in `/tmp/zapper/`, **outside** the ROM folder): `clean_menu2.png`, `keytest_Return.png` (locked control), `arcade_after_code.png` (published code), `novel_code_test.png` (novel code), `options_screen.png`, `multiplayer_screen2.png`, `paused2.png`.

## 4. Address map

| Address | Kind | Evidence / role |
|---|---|---|
| `0x080000C0` | code | stock crt0 (entry branch `0xEA00002E`) |
| `0x080D71AC` | code | key-scan routine (Thumb). Reads `0x04000130`, computes `~KEYINPUT & 0x3FF`; writes **pressed** (newly-pressed mask) to `0x03000AA8` and **held** to `0x03001FA8`. Literal pool at `0x080D71CC`–`0x080D71D8`. **Derived** from disassembly, **observed** via read watchpoints. |
| `0x03000AA8` | RAM u16 | pressed mask, active-high |
| `0x03001FA8` | RAM u16 | held mask, active-high |
| `0x080CB244` | code | main-menu input handler; `pressed & 0x09` (Start\|A) reset combo at `0x080CB254`; Up/Down navigation at `0x080CB2F6`/`0x080CB31A` |
| `0x080D24C0`–`0x080D2742` | code | pause-menu handler: `pressed & 0x09` combo, held-L/R volume sliders, Up/Down/D-pad navigation (`0x080D24EE`, `0x080D2524`, `0x080D25B8`, `0x080D2648`–`0x080D2722`) |
| `0x080D0F00`–`0x080D0F8C` | code | gameplay input handler: maps pressed d-pad `0x20/0x10/0x40/0x80` → direction indices 0–3, calls `0x080D177C` |
| `0x080E3F68` | code | system combo check (`held & 0x0C` / `& 1` / `& 2`) — Start+Select+A+B style |
| `0x03001FA0` | RAM u16 | cheat/unlock flag bitfield. Written to `1` by applier `0x080D6D72`; cleared (`&= 0xFFFE`) by `0x080DA8BC`. A savestate taken 0.3 s after entering the novel code had `0x0001`; near-miss states had `0x0000` — see caveats. |
| `0x080D6D60` | code | **cheat-flag applier** (observed via write watchpoint on `0x03001FA0`): `ldr r0,=0x03001FA0; movs r4,#1; strh r4,[r0]` at `0x080D6D6E`–`0x080D6D72`, then plays a confirmation sound via `BL 0x080D68E8`. No direct `BL` reaches it; it is dispatched through a pointer table. |
| `0x080DA8B0` | code | clears bit 0 of `0x03001FA0` |
| `0x03001760` | RAM table | runtime function-pointer table (14 entries). Index 1 = `0x080D6D61` (the applier above); index 2 = `0x080C861D`; index 6 = `0x080E40E9`; default `0x080D7085`. Initialised by `0x080D6CD0`. **Derived** from a savestate RAM dump + disassembly. |
| `0x083292EB` (`0x3292EB`) | text | 3-character name-entry alphabet |
| `0x08329B8`–`0x0832C1C` (`0x329B8`–`0x32C1C`) | text bank | UI/strings; no PASSWORD/CODE debug screen present |
| `0x08359B0` (`0x3359B0`) | text | `AGB DEBUG ASSERT: PRESS A L AND R TO ATTEMPT TO CONTINUE ...` — a crash handler, not a cheat menu (matches TCRF) |
| `0x04000130` | I/O | KEYINPUT; exactly **one** literal reference in the whole 4 MiB (`0x080D71CC`) — no keypad-IRQ path (`0x04000132`: 0 references) |

File offset = ROM address − `0x08000000`.

## 5. Algorithm

The complete validator was **not** recovered. What is proven:

```
per frame:
  raw = *0x04000130
  held   = ~raw & 0x3FF              -> 0x03001FA8
  pressed = held & ~previous_held     -> 0x03000AA8
  menu / gameplay handlers consume pressed & held (enumerated above)
  when a sequence is accepted:
      0x03001FA0 |= 1                 (applier 0x080D6D60)
      play confirmation sound
      persist unlock to SRAM (survives .sav deletion across restarts in our runs)
```

No pseudocode for the sequence matcher is claimed. The published acceptance set behaves like a short state machine over 8 d-pad presses with L held; the last three presses are not free (three near-miss variants were rejected).

## 6. Tables

Published codes (GameFAQs GBA page, verified against the web archive snapshot; PS2/GC/XBOX-labelled entries recorded but not attributed to this SKU):

| Effect | Sequence (hold L) | Screen |
|---|---|---|
| Last Level | R L R L U D U D | main menu |
| Infinite Lives | U U L L R L R | pause |
| Unlimited Lives (PS2/XBOX label) | U U U L L R L R | pause |
| Unlimited Shield | U D U L R D U | pause |
| Unlock All Levels (PS2 label) | L D R R U U U | pause |

Observed acceptance at the main menu:

| Sequence | Status |
|---|---|
| `R L R L U D U D` | accepted (published) |
| `R L R L U U U U` | accepted (**novel**) |
| `R L R L U D U U` | rejected |

## 6b. Enumeration

**Space definition.** The input surface is button sequences, not text. Each step is one d-pad press (4 directions, `0x10/0x20/0x40/0x80`) with L (`0x200`) held; published lengths are 7 or 8 presses. The raw step space is therefore `4^7 + 4^8 = 81,920` distinct ordered press sequences; with the L modifier held throughout, each step's combined key mask is one of `0x210/0x220/0x240/0x280`. No checksum symbol, reserved bit, or alphabet was found — this is a fixed-sequence matcher.

**Novel code (deliverable).** `R L R L U U U U` (hold L throughout), entered on the main menu from a **freshly deleted `zapper.sav`**, unlocks Arcade Mode. Evidence: `novel_code_test.png` (mode-select screen with Time Attack / Orb Challenge / Ghost Race). The string `RLRLUUUU`, and the button sequence `Right Left Right Left Up Up Up Up`, appears in **none** of the GameFAQs, IGN, TCRF, planetcheats, or Ethereal Games lists recovered in recon. It differs from the published `RLRLUDUD` in the final three presses.

**Bounds by rejection.** From a fresh save, `R L R L U D U U` (one press changed from the published code at position 8) does **not** unlock Arcade Mode; the control path still requires completing a level (`keytest_Return.png`). The unlock is observable on-screen, so this is a real accept/reject boundary, not a decoder-only claim.

**Bounded negative searches (with counts).**

* Literal table search: the 5 published sequences were searched in **12 representation families** — u16/u32 active-high d-pad masks, L-combined masks, active-low (`~v & 0x3FF`), byte-swapped words, 4-byte stride / hold+press pairs, 8 direction-index permutations × 3/4-bit packing, 24 permutations × 2/3-bit bit-packing, font/tile indices from the game's own alphabet, ASCII and UTF-16 uppercase/lowercase/reversed, and GameFAQs-standard forward/reverse orderings. **0 plausible code-table hits**; the only exact byte hits were in an ADPCM/delta-audio region around `0x06B000`–`0x06D000` and were rejected by context.
* Runtime input-consumer enumeration via mGBA `-d` read watchpoints, 25–30 consecutive stops per screen:
  * main menu — pressed: 3 distinct PCs (`0x080CB254`, `0x080CB2F6`, `0x080CB31A`); held: 2 (`0x080D71C2`, `0x080E3F68`)
  * gameplay — pressed: 5 distinct PCs (`0x080D0F00`, `0x080D0F56/66/76/86`); held: 2 (`0x080D71C2`, `0x080E3F68`)
  * pause — pressed: 5 distinct PCs (`0x080D24EE`, `0x080D2648/98/E8`, `0x080D2722`); held: 4 (`0x080D2524`, `0x080D25B8`, `0x080E3F68`, `0x080D71C2`)
  Every one of these was disassembled and identified as a menu-navigation, volume/brightness-slider, direction-dispatch, system-combo, or key-scan access. **No sequence-building/history consumer appears on any reachable screen.**
* Alternate input path: `0x04000132` (keypad IRQ) has **0** literal references; `0x04000130` has exactly **1**. Input cannot bypass the two buffers above.
* Font/text negative: the entire text bank `0x08329000`–`0x0832C1FF` was decoded as ASCII (not tile indices); it contains `ENTER NAME`, `SELECT LEVEL`, `LEVEL RECORDS`, unlock messages, game-mode names and a crash assert, but **no password/code-entry or debug-menu string**.
* Screens walked with screenshots: boot splashes; main menu; CHOOSE SAVE SLOT; ENTER NAME; Story intro; gameplay; PAUSED; OPTIONS; NEW GAME/CONTINUE; MULTIPLAYER link-search; Arcade mode-select. No hidden "code" or "debug" entry was rendered on any of them.

## 7. Validation evidence

* **Observed**: key mapping from live KEYINPUT watchpoint (10 keys); Arcade Mode after published code and after novel code from fresh saves; locked message without a code; rejection of the near-miss; all screen screenshots; flag word `0x0001` in the savestate taken after `RLRLUUUU` and `0x0000` after near-misses; write watchpoint firing at the applier `0x080D6D6E`–`0x080D6D72` with old=0/new=1.
* **Derived**: key-scan routine layout; every input-consumer PC identified by disassembly; effect flag/applier/pointer-table addresses; persistence of the unlock into SRAM.
* **Inferred**: that the matcher is a short state machine over the 8 presses with L held (the last-three-press boundary is observed, the internal representation is not); that `0x03001FA0` bit 0 is the "Arcade unlocked" flag (the same value is re-applied from the save at boot, so it is not a reliable per-attempt oracle).

## 8. Unknowns

1. **The sequence matcher itself was not located or reversed.** Its code was not among the live input-buffer readers, which suggests it may receive key state by value from another routine or be reached through a pointer dispatch; that path was not closed. Consequently the exact accepted set and any additional effects of the other published codes are unproven.
2. The pause-screen codes (`Infinite Lives`, `Unlimited Shield`, `Unlock All Levels`) were entered but produced **no visible change** in this EU build. They may be mis-attributed console codes (§16.7, §16.11), or their effect may be a counter/sound that was not observed with `SDL_AUDIODRIVER=dummy`.
3. The `0x03001FA0` flag is re-written at boot from persistent state, so the savestate-based flag oracle is ambiguous; the accept/reject conclusion rests on the **on-screen unlock**, not on that flag alone.
4. No emulator microphone/sound verification of the documented "noise when entered correctly" was possible in a dummy-audio environment.

## 9. Tooling

All scripts and evidence were in `/tmp/zapper/`:

* `find_table.py`, `find_table2.py`, `find_table3.py`, `find_table4.py`, `find_swap.py`, `find_pack.py`, `find16.py`, `find_font.py`, `find_ascii.py`, `scan_masks.py` — literal/encoding table searches
* `find_readers.py`, `blscan.py`, `funcs.py` — Thumb literal-pool and BL scanners (corrected to compare the *contents* of the literal pool, not its address)
* `keys.py` — XTEST input helper with verified keymap and window activation
* `state_diff.py`, `analyze_progress.py`, `analyze_progress2.py` — mGBA `.ssN` `gbAs` zlib-chunk extraction and RAM diffing (§16.13)
* `dbg.py`, `collect_pcs.py`, `keyprobe.py`, `code_oracle.py`, `flag_test.py`, `wp_verify.py` — mGBA `-d` debugger (via `script(1)` PTY + FIFO) watchpoint collection
* Toolchain: `mgba 0.10.5`, `gdb-multiarch` (GDB stub did not bind in this build; `-d` debugger used instead), `xdotool`, `scrot`, `arm-none-eabi-objdump -M force-thumb`, Capstone, Python 3.
