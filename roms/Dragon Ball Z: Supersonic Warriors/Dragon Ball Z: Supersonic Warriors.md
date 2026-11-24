# Dragon Ball Z: Supersonic Warriors (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dragon Ball Z: Supersonic Warriors.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| Header title / game code / maker | `DRAGONBLSSWU` / `AZJE` / `70` (Atari) |
| Version / fixed byte / complement / checksum | 0 / 0x96 / 0x25 / 0x0000 |
| Entry word | `0xEA00002E` (stock branch to 0x080000C0) |
| MD5 | `09f49996195a3fce6141306f9eeb2944` |
| SHA-1 | `f6f956989773e39cfde407d3763eb7f767ef2033` |
| SHA-256 | `588fd0bb53541a0c0ac49cc4192226988ab307dc3bee3c8328ee1a952d52091c` |

Header is **rebuilt/patched**: checksum `0x0000` and stored complement `0x25` vs computed `0x3E` (guide §16.1). The entry word is the stock ARM branch, so the cart entry itself is not a cracktro. Single Nintendo-logo header only (logo hits: 1, at file 0x4) — **no embedded second image and no appended trainer header**. The logo bytes are the nonstandard variant `24 ff ae 51 69 9a a2 21 3d 84 82 0a ...` (also present in the concurrently analysed Buu's Fury and GT images — a dumper/tool signature, not a shared game engine). Save is 512-byte EEPROM. Developer/publisher metadata: Cavia/Arc System Works, Atari SA, US release 2004-06-22 (3rd party cheat indexes).

## 2. Executive summary

**There is no password system, no button-code system, and no on-screen code-entry field in this image.** The developer-intended "cheat"/unlock surface consists of (a) **save-backed unlockables** (a 15-page Shop bought with Challenge-Mode points, Challenge teams, "Secret Final Battles" after a no-loss story clear) and (b) **one genuine hidden debug menu**, which 3rd party cheat indexes document but leaves "To do: Document this."

The debug menu is real, reachable, and fully enumerated here (§6b). Its gate is the single RAM byte `0x03000891 == 0x0C` (IWRAM), set at the main menu. With the gate set, an otherwise **unlabelled 8th dragon-ball option** appears; selecting it, choosing a character, watching the first story cutscene, and pressing **Start** opens a five-entry debug menu that 3rd party cheat indexes do not describe. All five entries were activated in the emulator and their effects recorded (§6b). The exact gate value was proved by rejection: 0x0B and 0x0D leave the normal, labelled menu (§6b).

Every published code for this SKU was checked (§6). All "codes" on cheat sites are **GameShark/CodeBreaker/Action-Replay memory edits (out of scope)** or **unlockable descriptions**; the four widely copied "Developer cheat codes" belong to *Dragon Ball GT: Transformation* / the PS2-era titles and are absent from this GBA image in every encoding checked (§6). Nothing is shared with the two concurrently analysed DBZ GBA images at code/table level (§7).

## 3. How to reproduce

* Emulator: mGBA (SDL) on isolated `Xvfb :318`, `SDL_AUDIODRIVER=dummy`, `mgba -3`. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Holds of 70–150 ms.
* Boot: FUNimation/Atari logos → title → **Start/A** → main menu (7 rotating dragon balls). D-pad **Up/Down** selects a mode (Left/Right do nothing). Mode ring, in Down order from STORY: STORY → Z BATTLE → CHALLENGE → FREE BATTLE → TRAINING → LINK VS → OPTION.
* Option Mode (Observed): submenu SETTING / SHOP / RANKING. Shop has **15 pages**, points balance displayed bottom-right (fresh file 00300); characters/levels are priced (e.g. Goku Lv3 = 500 points, "IF Story" = OPEN). Museum is absent until bought in the Shop (FAQ).
* **Debug-menu path (research instrument):** the gate is a RAM byte that cannot be set by any controller input found in this ROM (§8). To reach the screen for analysis, patch `0x03000891` to `0x0C` at the main menu (savestate `gbAs` chunk, IWRAM file offset `0x19000 + 0x891 = 0x19891`; mGBA savestates are PNG with zlib `gbAs`), then:
  1. Navigate Down to the **unlabelled 7-star dragon ball** (the option immediately after LINK VS);
  2. Press **A** → a story-mode-like character-select grid;
  3. Select a character (A) → the character's first cutscene plays;
  4. Press **Start** → the debug menu appears.
  * Timings: wait ~1 s after each screen transition; the cutscene text box must be present before Start is pressed.
  * Adjacent values 0x0B / 0x0D do **not** open the path — normal labelled main menu is shown (§6b).
* Screenshots of every step were in `/tmp/dbzsw/` (e.g. `invisible_option_c.png`, `char sel` in `testN0_c.png`, `cutscene1_c.png`, `dbg_fresh_c.png`, `dbg2_after.png`, `opt_inside_c.png`, `shop_c.png`). Screenshots are evidence only; RAM/address proofs are primary.

## 4. Address map

| Address / offset | Meaning | Evidence |
|---|---|---|
| file `0x000..0x1FF` | Rebuilt header (chk 0, complement 0x25); stock entry 0xEA00002E | Observed (bytes) |
| `0x03000890` | Global game-state struct base (71 Thumb PC-relative literal loads in ROM) | Derived |
| **`0x03000891`** | **Debug-menu gate byte; 0x0C enables the hidden option** | Observed (savestate patch + emulator path) + Derived (3rd party cheat indexes literal) |
| `0x03001890` | Secondary global state (menu mode dispatch, +0x12 switch selectors) | Derived (disasm 0x0802C0A4, 0x0802D80E, 0x0803F190) |
| `0x03004D50` / `0x03004D58` | Save/unlock flag region; `0x03004D58` is the "everything unlocked" GameShark target and has literal xrefs at `0x08038204`, `0x0803AD48` | Derived (literal scan) + published code |
| `0x08000BFE` | Earliest literal load of 0x03000890 (mode-dispatch function) | Derived |
| `0x0803F1FA` | `ldrb/strb [r5,#1]` accessor of the `0x03000891` byte (subs #5 countdown path) | Derived (disasm) |
| `0x0802C0A8`, `0x0802D812`, `0x0803DA8` | `cmp ...,#0xC` sites — 13-case switch bounds on `0x03001890+0x12`, **not** the debug gate | Derived (jump tables dumped) |
| Savestate `gbAs` layout | 0x0000 header/CPU, 0x1000 VRAM, 0x19000 IWRAM, 0x21000 EWRAM; size 0x61000 | Derived (mGBA serialize.h + verified) |

## 5. Algorithm

No checksum/validator exists. The recovered procedure is the gate/unlock classification:

```
# debug screen (Observed)
state = read8(0x03000891)
if state != 0x0C: main_menu_has_7_labelled_entries()
else:             main_menu_has_unlabelled_8th_entry()
                  # only this entry's handler reaches:
                  story_like_character_select()
                  first_cutscene()
                  on Start: debug_menu_5_entries()

# unlockables (Inferred / save-backed, not a code system)
points <- Challenge Mode rank rewards
Shop[15 pages] <- buy with points -> unlock flags in 0x03004D5x / EEPROM
```

## 6. Tables

**Published codes tested against this image (all verified as non-applicable or out of scope):**

| Source / code | Class | Result |
|---|---|---|
| 3rd party cheat index cheats page: 7 Challenge-Mode team unlocks | Unlockable description | Real feature, save-backed; not a code (§6b) |
| 3rd party cheat indexes: "Secret Final Battles — clear story without losing, wait after credits" | Unlockable description | Real gate; not a code |
| 3rd party cheat indexes: "Fast Win — beat Frieza <14 s in story mode" | Gameplay trick | Not a code system |
| 3rd party cheat index FAQ: "hidden characters besides those you buy/unlock in the Store? **No.**" | Negative statement | Consistent with observed Shop-only unlocks |
| `43004D58 FFFF / 00000004 0002`, `8300274A 6400`, `74000130 03FB 33002826 0000` (3rd party cheat indexes) | GameShark memory edits | Out of scope; useful only as RAM-location evidence (0x03004D58) |
| CodeBreaker / Action Replay lists (3rd party cheat indexes), e.g. `2EB1D3AADD1B FC73B37934AC` | Memory edits | Out of scope; not verified against ROM |
| 3rd party cheat indexes "unlock the redemption menu" | Unlockable/other-SKU claim | No redemption/code screen exists in reachable menu tree (Observed) |
| 3rd party cheat indexes `03000891:0C` | Memory-write **research instrument** | Verified: opens the hidden debug path in this exact image |
| PS2/console DBZ codes; Buu's Fury / GT "Developer cheat codes" | Other SKU | Absent from this ROM (no literals, no button-mask table); not applicable |

**Text/button search space (negative results bounded):**

| Search | Result |
|---|---|
| `strings -t x -n 4` (146,295 lines) | No password/cheat/debug-code strings. Hits for MASTER/SECRET/SPECIAL at 0x5DC989/0xA99D9/0x5EBF70 etc. are multilingual fight dialogue ("you mastered fusion", "CYBORGS", "MIGLIORATO") with control bytes 0xFC/0xFD/0x0E |
| Case-insensitive keyword grep | Same; no code-entry vocabulary |
| Literal 0x03000891 as u32 in ROM | 0 hits (gate accessed via base 0x03000890 + byte offset) |
| Literal 0x03000890 as u32 | 71 instruction sites |
| Button-mask table prefix scan / password alphabet | No table or on-screen keyboard found; menu has no text-entry field |
| Embedded GBA headers (logo scan) | 1 (the image itself) — no trainer/multicart |

## 6b. Enumeration

**Space definition:** There is no code space to enumerate for passwords/button codes — representable developer-intended codes = **0**. The enumerable hidden content is the debug menu: **exactly 5 entries**, all undocumented by 3rd party cheat indexes. Gate space tested: byte values 0x0B, 0x0C, 0x0D at 0x03000891.

**Debug-menu entries and effects** (Observed; cursor wraps after the 5th — entry 0 and entry 5 produce the same result). Labels render as garbled glyphs because the debug screen uses a nonstandard font mapping, so entries are identified by effect, not by their unreadable text:

| # | Activation result (Observed) | RAM/other evidence |
|---|---|---|
| 1 | Goku portrait / cutscene-art viewer | `dbg2_a0_c.png` |
| 2 | Blank black screen (no scene loaded); still blank after 5 s | `dbg2_a1_c.png`, `dbg_longwait_c.png` |
| 3 | Blank black screen with a grey dialogue box bar at the bottom | `dbg2_a2_c.png` |
| 4 | Settings toggle: returns to the debug menu; top-left value cycles `YPP` → `YX` (a 3-state ↔ 2-state value, consistent with an ON/OFF-style flag); 0x03000890/0x92/0x94 change | `dbg2_a3_c.png`, savestate diff `dbg_base.ss5` vs `dbg_e1_right.ss6` |
| 5 | Blank black screen | `dbg2_a4_c.png` |

This is a **story/scene-oriented debug menu**, not a universal "unlock all" panel. The five entries and their effects are **novel** relative to every published list checked (3rd party cheat indexes explicitly leaves the menu undocumented; 3rd party cheat index lists only unlockables).

**Bounds proven by rejection (Observed):** starting from the same main-menu savestate, patching `0x03000891` to `0x0B` (`gatebound_7_c.png`) or `0x0D` (`gatebound_8_c.png`) leaves the normal labelled "LINK VS MODE" menu; only `0x0C` (`gatebound_9_c.png`) removes the label and admits the hidden option. With no patch (stock 0x05/0x00) the main menu has exactly the 7 labelled entries in the mode ring and no unlabelled option (`gmenu_montage.png`, `menu2_montage.png`, 8+ Down presses). The exact gate value is therefore demonstrated, not assumed.

**Unlockables (save-bit system, not a code):** Challenge-team unlocks (7 teams), Secret Final Battles (no-loss story clear), and the 15-page Shop. These are save/point-gated, consistent with §16.18: no input can set them. 3rd party cheat indexes' FAQ explicitly states no hidden characters beyond Shop/unlockables, and the full reachable menu tree contains no code-entry surface.

## 7. Validation evidence

* **Observed:** hashes/header; 7-mode main menu ring; Option → Setting/Shop/Ranking; Shop 15 pages/prices; story character-select grid; first cutscene; debug menu reached via the gate; 5 debug entries activated with effects above; gate values 0x0B/0x0C/0x0D compared; savestate IWRAM layout verified against mGBA's serialized struct.
* **Derived:** gate accessor at 0x0803F1FA and 71 xrefs to state base 0x03000890; `cmp #0xC` sites identified as unrelated switch bounds; unlock flag word 0x03004D58 from published code + ROM literal xrefs; header rebuild from checksum/complement arithmetic.
* **Inferred:** Shop/unlock flag layout in EEPROM (not dumped/decoded); that blank debug entries are unused cutscene slots; that no controller sequence can set the gate (consistent with exhaustive menu/button-space search, but no formal proof over every possible sequence — see §8).
* **Prompt-injection watch:** fetched 3rd party cheat index pages contained no instruction-like payloads in this run; all page text treated as data (§16.8).

## 8. Unknowns

* The debug-menu labels are rendered with a nonstandard glyph mapping; their literal on-screen text could not be read, so entries are identified by effect only.
* No controller-only route to the gate byte (`0x03000891 = 0x0C`) was found; reaching the debug screen requires a RAM write (savestate patch here). The 71-state struct's byte-1 accessor at 0x0803F1FA is a countdown, not a controller gate.
* Blank debug entries (2, 5) were not made to display content; they may be unused scene slots.
* Unlock-flag bit-to-item mapping in the EEPROM was not decoded; the save-based unlocks were not brute-forced (correctly — §16.18).
* Save-bit "Secret Final Battle" after-credits timing was not played through.

**Shared components with the concurrently analysed Dragon Ball titles:** none at code/table/address level. *Buu's Fury* and *GT: Transformation* use the Webfoot bytecode-interpreter engine (8 MiB / 4 MiB class images) and have no code system; this image is a 16 MiB Cavia/Arc System Works fighting engine with a different global-state layout, different RAM gate, and different unlock region. The only commonality is header bytes (same nonstandard Nintendo-logo variant) — a ROM-processing artifact, not shared functionality. The GT/PS2 "developer codes" found by web search do not apply here.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, Python 3 (`struct`, `zlib`, `binascii`, PIL) for header parse, embedded-header logo scan, savestate `gbAs` decompress/patch/diff, literal scans and cursor tracking.
* `strings -t x`, `grep -iE` for text reconnaissance; Capstone 5.0.7 for Thumb PC-relative literal and byte-accessor scans; `arm-none-eabi-objdump -M force-thumb` for targeted disassembly of 0x08000BFE, 0x0802C0A4, 0x0802D80E, 0x0803F190, 0x0803D760.
* mGBA (SDL) under Xvfb :318 + openbox; xdotool/XTEST key helper (`key.py`); `import`/`scrot` + ImageMagick for screenshots.
* Fallback tooling noted for reproduction: mGBA CLI debugger via a PTY (`script` + FIFO) provides `r/1`/`w/1` RAM access; the GDB stub (`-g`) was found single-client/unreliable and savestate patching was used instead.
* All analysis artifacts were kept in `/tmp/dbzsw/`; no ROM or copyrighted assets are redistributed. Generated `.sav`/`.ss*` files were removed from the ROM folder; all spawned processes (mGBA, Xvfb :318, openbox) were stopped by PID.
