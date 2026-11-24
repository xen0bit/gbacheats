# Shonen Jump's One Piece (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Shonen Jump's One Piece/Shonen Jump's One Piece.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| `file(1)` | Game Boy Advance ROM image: "ONEPIECE" (BONEB2, Rev.00) |
| Header title | `ONEPIECE` (0xA0–0xAB) |
| Game code | `BONE` (0xAC–0xAF) |
| Maker code | `B2` (0xB0–0xB1) |
| Version | 0x00 (0xBC); complement 0x71 (0xBD); checksum 0x0000 (0xBE) |
| Entry word | `0xEA00002E` → branch to `0x080000C0` (stock crt0) |
| MD5 | `ce153a5ce176b608edd035e3b9a27dad` |
| SHA-1 | `6dfe6572aa6b51e2c550ddeef7ca04c35fcdf299` |
| SHA-256 | `d62a5f4099ca5b2fb446793a00703b027548abfb07334eb0e2f80c851aeb40ee` |

**Phase 0 result:** single retail image. The 156-byte Nintendo logo occurs exactly once (file offset `0x4`), so there is no appended trainer, multiboot stub or second game image. No cracktro/trainer strings (`CRC BANDIT`, `MODE7`, `SUNHORS`, `TRAINER`, `CHEAT`) appear anywhere. The header checksum of `0x0000` is the normal rebuilt-header artifact noted in guide §16.1; the complement byte is present and the entry branch is unmodified, so the image is not a patched/cracked release.

## 2. Executive summary

This is a Dimps/Bandai licensed beat-'em-up/platformer (US-only, 2005). It has **no password system, no button code, and no reachable hidden debug screen**. Every published "cheat" for this SKU is a *gameplay unlockable* collected through normal play (flags, Luffy upgrades, Boss Battle / Mini-game modes, Sound Test, extra characters) — none is an entered code.

The ROM does contain a substantial **orphaned developer menu** (6 entries: BG VIEWER, ACTION VIEWER, MINI GAME, ENDING PLAY, SAMPLE START, GAME START; plus viewer HUD strings for action/BG inspection and GATE/AREA/STAGE/LOOP debug text). It is **dead code in this retail build**: a whole-ROM scan found **zero** BL calls, **zero** unconditional branches and **zero** 32-bit pointers (including the Thumb-bit `addr|1` form) to its three entry routines from anywhere outside its own 0x080007C4–0x08000A00 block. Its menu-state pointer `0x03003A80` is NULL on the main menu. An 18-combination title-screen brute force, a boot-time L+R hold, and in-game L presses produced no debug screen. This is a bounded **dead-code / gated-feature negative** in the sense of guide §16.3, not an "untested" result.

All reachable screens were walked under mGBA with RAM snapshots taken from the emulator's `.ss1` savestates (zlib `gbAs` chunk): Luffy intro → title → SELECT DATA → SELECT MENU → STORIES (NORMAL/HARD) → gameplay; COLLECTIONS (9 pages × 10 slots, all locked on a fresh save); OPTIONS (SCORE plus a locked Sound Test with the Gaimon/mini-chest hint).

Coordinator note: `roms/INDEX.md` and the guide are coordinator-only and were not edited.

## 3. How to reproduce

1. Emulator: `/usr/local/bin/mgba` 0.10.5, `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, own `Xvfb :318` + `openbox`. Keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. `xdotool` XTEST events to the focused mGBA window; hold keys ~200 ms (short taps are missed).
2. Boot to title: Start (skip Luffy intro) → Start (title "Press START") → A (SELECT DATA, FILE 1) → A (SELECT MENU).
3. Main menu has exactly three live items: STORIES, COLLECTIONS, OPTIONS. STORIES → NORMAL/HARD → gameplay. COLLECTIONS → 9 pages (Right/Left), 10 locked slots per page. OPTIONS → SCORE (only live item; Sound Test is locked with the "collect all mini chests / talk to Gaimon in Syrup Village" hint).
4. Debug-menu negative tests, all returning normal screens:
   - Boot hold L, R, L+R (held from launch through the intro).
   - 18 title-screen combos: L; R; L+R; L+Start; R+Start; L+R+Start; A+B; A+B+Start; A+B+Select; Start+Select; L+R+Down; L+R+Up; L+R+A; L+R+B; Select+L; Select+R; Select+Start; Konami (↑↑↓↓←→←→BA).
   - L pressed during gameplay (sibling-game debug trigger) — no menu.
5. RAM evidence: mGBA savestates (`Shift+F1..F3`) were parsed as PNG with a zlib-compressed `gbAs` chunk. For this 8 MiB image the raw state is 397,312 bytes; IWRAM `0x0300xxxx` maps to file offset `0x19000 + (addr - 0x03000000)`, EWRAM `0x0200xxxx` to `0x21000 + (addr - 0x02000000)`. Confirmed values: `0x03003A80 = 0x00000000` at SELECT MENU, `0x03002070` at OPTIONS; `0x030034AC = 0x12` (menu) vs `0x08` (options); `0x030034E8` input shadow = 0 when idle. A two-state diff located exactly the IWRAM menu-state region (`0x1CA80` ↔ `0x03003A80`), validating the mapping.

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x08000000` | ROM | Entry branch `0xEA00002E`; stock ARM crt0 at `0x080000C0` |
| `0x080000FC`–`0x080001BC` | code (ARM) | IRQ dispatcher (jump table `0x03001DE0`); not a debug gate |
| `0x080007C4` | code (Thumb) | Debug menu draw: prints `MAIN MENU %.4x`; called only from `0x0800089C` |
| `0x08000800`–`0x08000896` | code (Thumb) | Debug menu item loop (6 items; cursor byte at state+2; Up/Down wrap 0–5; A dispatches) |
| `0x0800089C`–`0x080009FC` | code (Thumb) | Debug menu input handler; reads active-high input shadow `0x030034E8` (Up `0x40`, Down `0x80`, A `0x01`); A handler dispatch at `0x08000904`–`0x08000910`; **no external callers** |
| `0x08000D05`, `0x08000D1D`, `0x08000D35`, `0x08000DA5`, `0x08000E15`, `0x08000E85`, `0x08000EF5` | code (Thumb) | Seven debug-menu item handlers (scene/mode setters via `0x08003688`, `0x0801098`, `0x080116C`) |
| `0x0807DA00`–`0x0807DA0D` | data | Hex digit table `0123456789ABCDEF` |
| `0x0807DA15`–`0x0807DA63` | data (ASCII) | Debug menu labels: `BG VIEWER`, `ACTION VIEWER`, `MINI GAME`, `ENDING PLAY`, `SAMPLE START`, `GAME START` |
| `0x0807DA64` | data | 7-entry pointer table to the handlers above |
| `0x0807DA8C` | data (ASCII) | `MAIN MENU %.4x` |
| `0x0807DA9C` | data (ASCII) | `VER A    ` |
| `0x08081C2C`–`0x08081C9C` | data (ASCII) | Viewer HUD: `ACTION VIEWER %04x`, `ACT TBL 0x%04x`, `ACT ID  0x%04x`, `CHA NUM %4d`, `POS-X %d`, `POS-Y %d`, `BG VIEWER %04x`, `BG NUM %4d` |
| `0x080872C0`–`0x080872FC` | data (ASCII) | Debug overlay: `GATE %2d(%d)`, `GATE **`, `AREA  %d`, `STAGE %d`, `LOOP %d` |
| `0x08056FA4`–`0x08056FDD` | data (ASCII) | Boss/character name table: `No Data`, `Helmeppo`, `AXE-HAND MORGAN`, `Mohji`, `BUGGY`, `Django the Hypnotist`, `CAPTAIN KURO`, `Ghin`, `DON KRIEG`, `Kuroobi, Choo, Hachi`, `ARLONG`, `Tashigi`, `CHASER`, `All Clear`; pointer table at `0x08056FDC` |
| `0x030034E8` | IWRAM | Active-high input shadow (Up `0x40`, Down `0x80`, A `0x01`) read by the debug handler |
| `0x03003A80` | IWRAM | Menu-manager state pointer; NULL on SELECT MENU, `0x03002070` on OPTIONS; dereferenced by the orphaned debug handler |

File offset → ROM address: `0x08000000 + file_offset`. Savestate offsets given in §3 are *not* ROM addresses.

## 5. Algorithm

There is no password/code algorithm to reimplement. The relevant reconstructed behavior is the orphaned debug menu's input model:

```
state = [0x03003A80]                 # pointer to IWRAM menu struct
cursor = signed_byte(state_struct + 6 ... +2)   # via r4 = 0x03000000 + halfword
keys = halfword[0x030034E8]          # active-high: A=1 B=2 ... Up=0x40 Down=0x80 R=0x100 L=0x200
if keys & 0x40:  cursor = (cursor - 1) & 0xFF; if cursor==0 -> 5
if keys & 0x80:  cursor = (cursor + 1) & 0xFF; if cursor==6 -> 0
if keys & 0x01:  call [0x0807DA64 + cursor*4]   # 6 live items, 7 stored pointers
# then: B/R/L branches manipulate scene state and call 0x08007BA3C
```

Up/Down wrap bounds (0 ↔ 5) prove a six-item menu, matching the six labels. The seventh stored pointer (`0x08000DA5`) is unreachable from this loop.

## 6. Tables

**Debug menu (present, unreachable in retail):**

| Cursor | Label | Handler |
|---|---|---|
| 0 | BG VIEWER | `0x08000EF5` |
| 1 | ACTION VIEWER | `0x08000E15` |
| 2 | MINI GAME | `0x08000D35` |
| 3 | ENDING PLAY | `0x08000E85` |
| 4 | SAMPLE START | `0x08000D05` |
| 5 | GAME START | `0x08000D1D` |
| (unused) | MAIN MENU %.4x | `0x08000DA5` |

**Reachable menu state:** SELECT MENU has exactly 3 items (STORIES, COLLECTIONS, OPTIONS); Mini-Games is hidden until game completion. STORIES has 2 difficulties (NORMAL, HARD). COLLECTIONS has 9 pages × 10 slots. OPTIONS has 1 live item (SCORE); Sound Test is locked.

**Published unlockables (from 3rd party cheat indexes / One Piece Wiki; all gameplay-gated, none entered as a code):**
- 10 pirate flags (Alvida, Arlong, Black Cat, Buggy, Cook, Kreig's armada, Navy, Red Hair, Straw Hat, Veggie).
- 9 Luffy upgrades priced 25M–350M bounty (Gum Gum Fruit, Master of the Near Sea, two "More Deadly Techniques", two "Raise Life Limit", Straw Hat, Pandaman, Pansamay).
- Modes: Boss Battle (collect all coins), Mini-game (finish once); Sound Test (all mini chests + Gaimon).
- ~20 collection items/statues (Wado, Chakram, Elephant Tuna, etc.).
- Extra characters (3rd party cheat indexes): Smoker, Tashigi, Aokiji — event-mode clear conditions.

**Verified published "codes":** none exist for this SKU. 3rd party cheat indexes' cheat page lists only the unlockables above; its walkthrough §3.2 says "Are there any cheat codes for this game? When I find them they'll be in here" (empty section). 3rd party cheat indexes show "Total cheats available: 0"; 3rd party cheat indexes show none. The 3rd party cheat indexes GameShark-style 32-bit codes are memory-edit cheats and are explicitly out of scope. A 3rd party cheat index "Going Baseball (J) (GBA)" button sequence belongs to a *different game* — a SKU mismatch of the kind described in guide §16.11; it does not appear in this ROM.

## 6b. Enumeration

**Code space size: 0.** There is no password alphabet, no input length, no checksum field, no literal comparison table and no validator in this image; correspondingly no code can be "minted" and no bounds can be demonstrated by a rejecting validator. Per §0.2 the negative is instead bounded by counting the searched spaces:

| Space searched | Count | Result |
|---|---|---|
| Reachable screens walked with RAM evidence | 8 (intro, title, SELECT DATA, SELECT MENU, STORIES/difficulty, gameplay, COLLECTIONS, OPTIONS) | No text-entry field, no password/keyboard screen, no hidden menu entry |
| `strings -t x -n 4` lines | 38,967 | Exactly 1 cheat/debug keyword: `MAIN MENU %.4x` at `0x7DA8C`; the rest are instruction-byte coincidences or the debug strings listed in §4 |
| Pure uppercase-alphanumeric runs ≥4 chars | 3,881 | No password/code table; all are instruction bytes, the header strings, the debug labels, or the boss-name table |
| Keyword scan (password/cheat/code/secret/unlock/debug/menu/level/select) | 11 patterns | 1 hit (`MAIN MENU %.4x`); no password UI string in any case/offset encoding |
| Embedded GBA headers (Nintendo-logo scan) | 1 hit (`0x4`) | Single image; no second game/trainer whose codes could be conflated |
| BL calls into debug-menu block from whole ROM | 0 | `0x080007C4`, `0x0800089C`, `0x08000A04` have no BL caller |
| Unconditional B branches into block from outside | 0 | Only intra-block branches found |
| 32-bit pointers to block (plain and `\|1`) from outside | 0 | Self-references only; the 7 handler pointers are consumed only by the dead menu |
| Title-screen button combinations tested | 18 (listed in §3) + boot holds L/R/L+R + in-game L | 0 debug screens; only title and SELECT DATA |
| Published in-game codes verified | 0 published codes exist | 3rd party cheat indexes confirm; blogspot codes are GameShark memory edits (excluded) |

**Novel code:** not applicable — a system with zero representable codes cannot yield an unpublished example. This is the bounded negative outcome required by §0.2 item 5, not an omitted deliverable.

**Bounds by rejection:** no validator exists to accept or reject a code. The closest bounded rejection tests are the 20 input experiments above, all of which were rejected (normal screens continued). If the debug menu is taken as the "hidden feature," its reachability bound is the three independent zero counts (BL, B, pointer) plus the 20 input experiments and the NULL state pointer at the main menu.

**Known limitation of the negative:** a function-pointer table built entirely at runtime (not present as a ROM literal) could in principle launch the orphaned menu; no such table was observed in the walked screens or in the savestate RAM dumps, but an exhaustive runtime data-flow proof was not attempted. This is the only respect in which the dead-code conclusion is inferential rather than observed.

## 7. Validation evidence

- **Observed:** all eight screens in mGBA with screenshots; 18-combo contact sheet; boot holds; in-game L; `.sav` file (512 bytes, all `0xFF` on a fresh profile); two `.ss1` savestates whose decompressed `gbAs` chunks diff exactly at the IWRAM menu-state region.
- **Derived:** debug menu label/pointer/HUD tables at the addresses in §4; six-item loop bounds (`cmp r5,#5` at `0x08000870`); active-high input semantics at `0x080008B4`/`0x080008E2`; dead-code counts from whole-ROM BL/B/pointer scanners; IWRAM savestate mapping (`0x19000 + (addr-0x03000000)`).
- **Inferred:** that the debug menu was reachable in a developer build but disconnected for retail (consistent with zero references and a NULL state pointer); that the locked OPTIONS items are Sound Test / BGM / SE (the Gaimon/mini-chest hint matches the published unlock condition, but the locked rows were not rendered legibly enough to enumerate their labels with certainty).
- Prompt-injection check: all fetched web content and all ROM strings were treated as data; no instruction found in them was followed. No suspicious payload was encountered.

## 8. Unknowns

- Whether the 7th debug-menu pointer (`0x08000DA5`, unreachable in the 6-item loop) was a removed menu entry or a leftover.
- The exact labels of the locked OPTIONS rows (Sound Test is strongly indicated by the on-screen Gaimon/mini-chest hint and the published unlock condition).
- Whether a runtime-built pointer table can reach the orphaned debug menu (see §6b limitation).
- No save was advanced to game completion, so the unlocked states of the 9 COLLECTIONS pages and the extra characters were not observed directly; their existence rests on the published lists and the boss-name table at `0x08056FA4`.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x -n 4`, `grep`, Python 3 for header parsing, literal-pool dumps, bl/B/pointer scanners and savestate (`gbAs` zlib) parsing.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` (and `-M force-arm` for crt0); Capstone for Thumb PC-relative checks.
- `/usr/local/bin/mgba` 0.10.5 under `Xvfb :318` + `openbox`, `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input; `scrot` + ImageMagick `convert`/`montage` for screenshots and contact sheets. GDB stub (`gdb-multiarch`, `:2345`) was used for spot RAM reads; it proved unstable across repeated batch sessions, so savestate RAM diffing (guide §16.13) was the primary RAM method.
- Analysis scripts/artifacts: `/tmp/onepiece/phase0.py`, `helper.py`, `state_raw.bin`, screenshots and contact sheets (`combos_sheet.png`, `coll_sheet.png`, `menu_main.png`, `s2.png`, etc.).

**Legal note:** only hashes, addresses, algorithms and findings are published; no ROM bytes or copyrighted assets are redistributed.
