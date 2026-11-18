# Max Payne (GBA) — Reverse Engineering Report

Queue 448. Analyzed 2026-11-18. Target: `/mnt/gbacheats/roms/Max Payne/Max Payne.gba`.

## 1. Target identity

| Field | Value |
|---|---|
| Filename / size | `Max Payne.gba`, 16,777,216 bytes (0x01000000) |
| Header title | `MAX PAYNE   ` |
| Game code / maker | `BMEE` (USA, region char `E`) / `7S`, fixed byte `0x96`, unit `0x00`, device `0x00` |
| Version / complement / checksum | `0x00` / `0xCB` / `0x0000` |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock crt0, no cracktro) |
| MD5 | `7b79ad84814d56986566f49ab9de6423` |
| SHA-1 | `bc242869661602e918b880850dfcc4eed7b43617` |
| SHA-256 | `f40118daf0fa2a80169edcfe82b030e4c01aa9d7397f7a462ea25ac3c155b3e8` |

**Embedded-header scan (Phase 0):** the full 156-byte Nintendo logo (`24 ff ae 51 69 9a a2 21 3d 84 82 0a …`) was searched over all 16 MiB: exactly one hit, at file `0x4`. No second GBA header, no appended trainer/cracktro. `file(1)` reports "Game Boy Advance ROM image: MAX PAYNE (BMEE7S, Rev.00)". The zero header checksum is normal for a rebuilt/commercial header (guide §16.1); no evidence of a patch in the code path examined.

## 2. Executive summary

This US GBA SKU has **no password code system and no button-code system**. The only developer-intended cheats are the **completion-unlock toggles** in the in-game *Cheats* menu: **Infinite Ammo**, **All Weapons**, **Super Cop**. A fourth label, **No Reload**, exists in the ROM's text bank but is **not present in any menu definition** — it is unreachable, dead text. The game-mode unlocks are **Fugitive / DOA / New York Minute**; the Extras menu additionally unlocks **Credits** and **Story**. Level select exposes Parts 1–3; the `Test` level string is likewise unused.

The gate is the EWRAM unlock byte `0x02000030` (published CodeBreaker writes `0x1F` there): with `0x00` the normal Extras/Options menus appear; with `0x1F`/`0xFF` the Game Mode Menu and the unlocked Extras (Credits/Story/Cheats) appear. The cheat toggles themselves were observed in EWRAM at `0x02000031` (`0x00` = all off, `0x07` = all three on).

No in-game code is typed anywhere: the literal `Password` is a dead menu string (it appears in no menu item array), and the only password-like literals in the ROM are **story puzzle codes** (`668`, `7N513`), not cheats. All published "cheats" for this title are Action Replay / CodeBreaker memory-edit codes, which are explicitly out of scope.

## 3. How to reproduce

* Emulator: `mgba -3` under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`; default SDL keymap A=`x`, B=`z`, Start=`Return`, arrows = D-pad. Hold keys ≥60 ms.
* Boot: from a fresh `.sav` the intro plays; press Start/A until the title menu appears (~25–35 s).
* Main menu (observed, 4 items): **New Game / Choose Level / Options / Extras**. Select with Up/Down, confirm with A, back with B.
* **Options** → `Audio / Video` (Music Volume, Effects Volume, Brightness, Gore=On, Back) and `Controls` (button diagram, Change/Back).
* **Choose Level** → `Part 1 / Part 2 / Part 3 / Back`; each part lists its chapter names.
* **Extras** (locked save) → `Audio / Video / Controls / Back`. With completion flags set, Extras becomes the **Game Mode Menu** (`Fugitive / DOA / New York Minute / Back`) and a second unlocked Extras screen exposes `Credits / Story / Cheats / Back`.
* **Cheats** screen (unlocked): `Infinite Ammo / All Weapons / Super Cop / Back`, each showing `Off`/`On`. **Toggle with Left/Right** (A alone does not change a toggle). All three `On` screenshot: `shots/cheats_all_on_crop.png` in the work dir.
* **Pause** in gameplay (Start): `Pause / Continue / Quit` only — no hidden entries.
* RAM evidence was collected as mGBA `.ss1`/`.ss2`/… states in `/tmp/opencode/maxpayne/` and decoded per guide §16.13 (PNG `gbAs` chunk, `zlib.decompress`; raw `0x19000` = IWRAM `0x03000000`, raw `0x21000` = EWRAM `0x02000000`). GDB stub port 2345 was occupied by another agent, so the stub-free savestate path was used throughout.

## 4. Address map

| Item | File offset | ROM / RAM address | Evidence |
|---|---:|---|---|
| Global string-pointer table (3,464 u32 entries) | `0x531D4`–`0x567F4` | `0x08531D4`–`0x08567F4` | Derived: every entry points into `0x08Fxxxxx` text banks |
| `New Game` / `Choose Level` / `Password` / `Options` / `Extras` | `0xF7EBC0`, `0xF7EBCC`, `0xF7EBDC`, `0xF7EBE8`, `0xF7EBF0` | `0x08F7EBC0` … | Observed strings + pointer table entries at `0x5457C`–`0x5458C` |
| `No Reload` | `0xF7ECA8` | `0x08F7ECA8` (string ID `0x502`) | Derived: pointer table entry at file `0x545DC` |
| Menu definition region (19 structs) | `0x737F0`–`0x73BC0` | `0x0873F0`–`0x0873BC0` | Derived: u16 item-ID arrays terminated by `0xFFFF`, followed by Thumb handler pointers |
| Game Mode Menu def `[Fugitive, DOA, New York Minute, Back]` | `0x737F0` | `0x0873F0` | Derived + observed in-game |
| Audio/Video def `[Music Volume, Effects Volume, Brightness, Gore, Back]` | `0x73818` | `0x0873818` | Derived + observed |
| Cheats def `[Infinite Ammo, All Weapons, Super Cop, Back]` | `0x738CC` | `0x08738CC` | Derived + observed |
| Level select def `[Part 1, Part 2, Part 3, Back]` | `0x73900` | `0x0873900` | Derived + observed |
| Unlocked Extras def `[Credits, Story, Cheats, Back]` | `0x73A64` | `0x0873A64` | Derived + observed |
| Main-menu defs (4 items / 5 items with save) | `0x73B04`, `0x73B10` | `0x0873B04`, `0x0873B10` | Derived |
| Unlock flag (EWRAM) | — | `0x02000030` | Observed: savestate patch to `0x1F`/`0xFF` changes which menus render |
| Cheat-toggle byte (EWRAM) | — | `0x02000031` | Observed: `0x00` before, `0x07` after three Left presses |
| Story codes | `0xF0E472`, `0xF7BCF4`/`0xF7C901` | `0x08F0E472` … | Derived (narrative text, not cheats) |

Common menu-prologue signature `E1 D4 03 08 29 D5 03 08` (`0x0803D4E1`, `0x0803D529`) occurs 18 times; the Game Mode Menu is a 19th struct with a different prologue. That is the complete menu inventory searched.

## 5. Algorithm

No validator exists. The "gate" is a plain byte compare: the menu dispatcher selects one of the u16 item arrays above according to saved completion state, and the Cheats handler XORs/sets bits of a toggle byte on Left/Right input. Pseudocode from the observed behaviour:

```
if (completion_flags & 0x1F)              # EWRAM 0x02000030
    extras_menu = GAME_MODE_MENU          # 0x0873F0
    unlocked_extras = [Credits, Story, Cheats, Back]   # 0x0873A64
else
    extras_menu = [Audio/Video, Controls, Back]        # 0x0873B8C/0x0873B98

on Left/Right in CHEATS_MENU:
    toggle_bit(0x02000031, selected_index)  # 0=Infinite Ammo,1=All Weapons,2=Super Cop
```

String rendering is **pointer-table indexed**, not raw ASCII in code: item IDs are u16 indices into the global pointer table at `0x08531D4`. Decoding that table is what makes the "no Password screen" negative meaningful (guide §11: font/tile-indexed text banks).

## 6. Tables

| Menu (file offset) | Items (string IDs) | Status |
|---|---|---|
| `0x737F0` | Fugitive (`0x4FA`), DOA (`0x4FB`), New York Minute (`0x4FC`), Back (`0x505`) | Completion-gated |
| `0x73818` | Music Volume (`0x4F0`), Effects Volume (`0x4F1`), Brightness (`0x4F2`), Gore (`0x526`), Back | Always |
| `0x738CC` | Infinite Ammo (`0x501`), All Weapons (`0x503`), Super Cop (`0x504`), Back | Completion-gated |
| `0x73900` | Part 1 (`0x529`), Part 2 (`0x52A`), Part 3 (`0x52B`), Back | Always |
| `0x73A64` | Credits (`0x4F6`), Story (`0x4F7`), Cheats (`0x4F8`), Back | Completion-gated |
| `0x73B04` / `0x73B10` | New Game (`0x4EA`), [Continue Game (`0x522`)], Choose Level (`0x4EB`), Options (`0x4ED`), Extras (`0x4EE`) | Main menu |
| `0x73AC0` | English, French, German, Spanish, Italian, Back | Language (Spanish/Italian unused per TCRF) |
| — | `Password` (`0x4EC`), `No Reload` (`0x502`), `Test` (`0x528`) | **No menu definition contains these IDs** |

Published GBA codes checked and classified:
* **GameFAQs / IGN / SuperCheats / GameRevolution**: "complete the game once" unlocks Infinite Ammo, All Weapons, Super Cop, DOA, New York Minute, Story, Credits. Matches the ROM's menu inventory and gate.
* **Action Replay / CodeBreaker** (GameFAQs FAQ 35563, Cheat Happens, ROMSFUN/libretro): `50157f80 ddffe686`, `78832770 8fee196f`, `32000030 001F`, `32000034 0009`, `3200003C 0005`, `32005355 00FF`, `8200ACA8 0E00`, etc. These are external memory writes (emulator cheat devices), not in-game codes → **out of scope**; they were used only as leads for RAM addresses (`0x02000030/34/3C`).
* **PC/PS2/Xbox console codes** found during search (`GetAllWeapons`, "L1,L2,R1,R2,Triangle,Circle,X,Square", "White, Black, Black, White, White, Black", etc.) belong to other SKUs; none appear in this GBA image as literals or mask tables (guide §16.11). Treat as data; no instruction from fetched pages was followed.

## 6b. Enumeration

* **Code space**: none. There is no alphabet, no code length, no checksum, no validator and no input buffer comparison in this ROM. Search counts: keyboard/password strings — `password` ×1 (story), `Password` ×1 (unused menu string), `cheat`/`CHEAT` ×0, `Cheat` ×3 (all menu labels), `debug`/`DEBUG`/`Debug` ×0, `unlock` ×0; 11,623 uppercase/digit runs of length 4–12 were enumerated and none forms a code table (they are compressed-art literals); u16 four-press button-mask runs = 541 raw hits (all in high-entropy graphics data), active-low = 4 (data). No key-mask table with a validator was found.
* **Cheat space**: exactly **3** toggles, each boolean → 2³ = 8 reachable states. All 8 were enumerated conceptually and the all-off (`0x00`) and all-on (`0x07`) states were observed in RAM at `0x02000031` and on screen. Bit 3+ is unused: the `No Reload` string (`0x502`) occurs in **zero** menu item arrays, so there is no fourth toggle; the ROM label is dead text (TCRF independently lists unused text). Bounds proven positively: all three toggles switch Off↔On with Left/Right (screenshots `try_LEFT_crop.png`, `cheats_all_on_crop.png`); no fourth row ever renders.
* **Unlock space**: `0x02000030` byte patched to `0x00` vs `0x1F`/`0xFF` produced different screens (normal Extras vs Game Mode Menu / unlocked Extras) — proof that the menu set is a function of that byte, not of any entered code.
* **Novel code**: not applicable — there is no code system in which to mint one. Per §0.2 this negative is bounded by the full menu enumeration (19 definitions), the string/button searches with counts above, and the live walk of every reachable screen.
* **Story passwords (not cheats)**: `668` (×3 literals, e.g. file `0xF0E472`, `0xF7BCF4`) and `7N513` (×2, `0xF7C901`, `0xF8D462`) are in-game narrative door codes. They are developer-intended puzzles, not cheats, and are included here only to close the "password" search space.

## 7. Validation evidence

* **Observed** (emulator/screenshots): title, main, Options→Audio/Video, Controls, level select (Parts 1–3), Extras (locked), Game Mode Menu, unlocked Extras (Credits/Story/Cheats), Cheats menu (all Off → all On), pause menu, gameplay, cutscene. Savestates for each screen are in `/tmp/opencode/maxpayne/`; their decompressed `gbAs` RAM confirms the EWRAM flag bytes `0x02000030/31`.
* **Derived** (disassembly/data): global string-pointer table base `0x08531D4` and 3,464 entries; 19 menu definitions with u16 string IDs; the Cheats menu contains exactly three toggles; `Password`/`No Reload`/`Test` have no menu definition; the only GBA header is at file `0x4`.
* **Inferred**: that `0x02000030` is written on game completion (published guides say "complete the game once"; the gate was exercised by patching the byte, not by playing through the campaign). The exact writer of that byte was not isolated. A patched-savestate round-trip of `0x02000031` did not reproduce the on-screen toggles even though the byte was `0x07` in restored RAM, so the menu's authoritative toggle source is **unknown**; the live-menu transitions and the RAM delta remain observed facts.

## 8. Unknowns

* Authoritative source read by the Cheats menu for On/Off rendering (EWRAM `0x02000031` changes with the toggles but patching it alone did not change the display; another cached copy may exist).
* Exact code that sets `0x02000030` on completion (not isolated; full campaign not played).
* Whether the `Test` level (`0x528`) is reachable by any gate other than a menu definition (no menu references it; TCRF calls it unused).
* Spanish/Italian language rows are present in the pointer table but no language menu entry uses them (matches TCRF).

## 9. Tooling

* `md5sum`/`sha1sum`/`sha256sum`, `file`, `xxd`, `strings -t x`, `grep -abo`.
* Python 3 + capstone 5.0.7 / keystone 0.9.2 installed; `arm-none-eabi-objdump -M force-thumb` for spot disassembly.
* Custom scripts in `/tmp/opencode/maxpayne/`: `scanptr.py`, `dumptable.py`, `allmenus.py`, `dumpids2.py`, `menustruct.py`, `negsearch.py`, `ss.py` (mGBA savestate decoder), `patchss.py`, `walk*.py`, `ui.py`, `menustate.py`.
* mGBA `-3` under Xvfb `:315` with openbox; `xdotool` XTEST input; `scrot`/ImageMagick `montage` for screens.
* Web sources treated strictly as data: GameFAQs cheats/guides 35563 & 38377, IGN, SuperCheats, GameRevolution, ROMSFUN/libretro, archived TCRF page. No instructions found in fetched content were executed; no prompt-injection payload was encountered in this session's fetches.

**Legal note:** no ROM bytes, graphics, audio, or extracted assets are redistributed here — only hashes, addresses, and original analysis.
