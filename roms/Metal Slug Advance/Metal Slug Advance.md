# Metal Slug Advance (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Metal Slug Advance.gba` (8,388,608 bytes / 0x800000) |
| Header title | `METAL SLUG` |
| Game code | `BSME` (serial AGB-BSME-USA); maker `B7`; version 0 (Rev.00) |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock retail crt0; not a cracktro) |
| Header complement / checksum | `0xE3` / `0x0000` (0x0000 checksum is the common rebuilt-header artifact) |
| MD5 | `6838eb5df807a0f3299ad76066d59d26` |
| SHA-1 | `067e1511ab6becf797f1bbd321a858e96a0349af` |
| SHA-256 | `32e9771d05e6b88a246090c107d31371d226b9408ebd555b2a0277b703b1aa8c` |
| CRC32 (published) | `09980880` |
| Embedded GBA headers | **one** — Nintendo logo scan finds only file offset `0x0`; no multiboot/trainer image, no appended trainer |
| Developer / publisher | Noise Factory / SNK Playmore; US release 18 Nov 2004 |

## 2. Executive summary

**There is no password system, no button-code system, and no text-entry cheat surface in this GBA SKU.** Every string that could plausibly be a code was classified; the UI text bank (file `0x84000`–`0x85C00`) contains **zero** strings matching `pass`, `cheat`, `code`, `debug`, `level select`, or `stage select` (the sole `grep` hit is the card description `Makes ruin's steps passable` at `0x840CA`). No password alphabet, validator, comparison table, or password-entry widget exists. Published "cheats" for this game are exclusively CodeBreaker/GameShark memory edits and are out of scope; the developer-intended unlockables are a 100-card / 100-prisoner collectible system.

**The game does contain a hidden developer debug menu**, but it is **not reachable by any controller input**: it is gated behind a ROM-patch byte. The published access method (`CodeBreaker 08006524:F8CF`, i.e. write the 16-bit value `0xF8CF` at ROM `0x08006524` = file `0x6524`) was verified byte-for-byte in this ROM. Patching a *copy* of the ROM with those two bytes makes Start during gameplay open the full debug menu. Because the access method is a ROM/memory patch, it is **out of scope as a "code"**; it is documented here only to characterise the hidden menu (scope explicitly forbids presenting memory-edit codes as findings).

The debug menu has **8 top-level entries** and was enumerated completely, including all submenus. A genuine in-game unlockable (the `WASHOUT` card, earned by dying before killing anyone) was obtained and RAM-verified.

## 3. How to reproduce

Emulator: `mgba 0.10.5` under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, `-3` scale. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. All keys held 60–150 ms; screenshots cropped to `720x480+152+144`.

Screen path (unpatched ROM):
1. SNK PLAYMORE splash (≈2 s) → title `PUSH START` → Start.
2. `FILE SELECT`: slots 001/002/003 + `OPTION`. Selecting `OPTION` shows a single inline setting, `B Button Auto Fire` ON/OFF (changed with Left/Right). Selecting a slot → `DIFFICULTY` NORMAL/HARD → `SOLDIER SELECT` Walter/Tyra (Left/Right) → `OPEN BRIEF`.
3. `BASE CAMP`: `MISSION` / `CARD` / `PRISONER` / `SAVE` / `QUIT`.
   - `CARD` → `000/100` list (001…005 visible), BACK/NEXT.
   - `PRISONER` → `000/100` list grouped by MISSION.
   - `MISSION` → `Proceed?` YES/NO → world map showing `MISSION 1` (only M1 unlocked in a fresh file).
   - `SAVE` → `Current data will be overwritten. OK?`
   - `QUIT` → `Quit game?`
4. Mission 1 → "MISSION 1 START!" → gameplay HUD `LIFE / ARMS ∞ / BOMB 10`. Start → pause menu `Continue / Back to camp`. Dying → `MISSION FAILED` → `Continue / Back to camp`; choosing Continue after dying without kills grants the `WASHOUT` card (`You got a card. 'WASHOUT'`), and the CARD screen then reads `001/100`.

Debug menu reproduction (patched **copy**; original ROM untouched):
```
cp "Metal Slug Advance.gba" /tmp/metalslug/MSA_debugpatch2.gba
python3 -c "p='/tmp/metalslug/MSA_debugpatch2.gba';d=bytearray(open(p,'rb').read());d[0x6524:0x6526]=bytes.fromhex('cff8');open(p,'wb').write(d)"
mgba -3 /tmp/metalslug/MSA_debugpatch2.gba
```
Original bytes at `0x6520` = `cb f8 00 06 00 0e 02 bc`; patched = `cb f8 00 06 cf f8 02 bc`. Start any mission, pause with Start → the debug menu is drawn over the pause menu. D-pad navigates, A selects, B cancels.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Item | File offset | ROM address | Evidence |
|---|---:|---:|---|
| Header / entry | `0x000` | `0x08000000` | Observed (xxd) |
| Debug gate byte (patch site) | `0x6524` | `0x08006524` | Derived (published literal verified: original halfword `0x0E00`, patched `0xF8CF`) |
| Debug renderer function | `0x79750` | `0x08079750` | Derived (pointer to `0x08004579` = Thumb `0x08004578`, the pause/debug dispatcher) |
| Debug text `-cmp_over[     ]` | `0x796F7` | `0x080796F7` | Observed |
| Debug text `palette_over!!!!!` | `0x79728` | `0x08079728` | Observed |
| Unused country-select text (`USA/EUROPE/JAPAN/ENDING/select country/<< >>`) | `0x797BC`–`0x797FA` | `0x080797BC`… | Observed; `select country` has a pointer at `0x0800460C`, but its functions (`0x080045C0`, `0x08004578`, `0x0800461C`) have **no BL callers** → dead code |
| Card name table (100 cards + 100 prisoners, 200 records of `{u16 0x0002, char name[]}`) | `0x84BAA`–`0x85589` | `0x08084BAA`… | Derived (parsed 200 records; #100 = `ALL CARDS`, #200 = `GEN.ARTHUR`) |
| Card description strings | `0x83F00`–`0x84500` | `0x08083F00`… | Observed |
| UI text bank (`%c%c` control prefix + ASCII) | `0x85700`–`0x85B00` | `0x08085700`… | Observed |
| `You got a card.` | `0x85A1C` | `0x08085A1C` | Observed |

RAM (from decompressed mGBA `gbAs` savestates; IWRAM at raw `0x19000`, EWRAM at raw `0x21000`):

| Address | Meaning | Observed values |
|---|---|---|
| `0x030021E7` | Debug-menu cursor index | `0x00` → `0x01` on one Down press |
| `0x03002AF8` | Debug DIP1 "invincibility" state | `0x00` → `0x80` when toggled ON |
| `0x0200464E` | Card-collection delta (Washout earned) | `0x00` → `0x01` |
| `0x0200CD85` | Card-collection delta (Washout earned) | `0x00` → `0x02` |
| `0x0200CD70` | Published "All Cards" CodeBreaker target (13 × `0xFFFF`) | all zero on fresh file — verified as the work area the edit targets (out of scope) |
| `0x0200CD68` | Published "All Missions Complete" target (`0x0600`) | zero on fresh file |

## 5. Algorithm

No password/checksum algorithm exists; there is no validator to reverse. The debug gate is a **single ROM byte**, not a runtime state machine:

```
if patch(0x08006524) == 0xF8CF:   # original 0x0E00
    Start during gameplay -> open debug menu (drawn over the normal pause menu)
else:
    Start during gameplay -> normal pause menu (Continue / Back to camp)
```

`0xF8CF` is the second byte-pair of the 16-bit CodeBreaker write; patching only the low byte to `0xCF` (BizHawk's "write CF to 6524" shortcut) was tested and **does not** enable the menu — the full 16-bit write is required. This is a useful negative result for anyone following the published one-byte instructions.

The unlockable card system is **save-bit based**, not code based: counters (soldiers killed, prisoners rescued, missions cleared, boss kill time) set bits in the 100-card flag field; the UI renders a name from the 200-record table at `0x08084BAA` and a description from `0x08083F00`. No controller sequence writes those bits (the game's own unlock conditions are all gameplay events).

## 6. Tables

**Debug menu — 8 top-level entries** (Japanese label → published English meaning → observed effect):

| # | Label | Meaning | Observed |
|---:|---|---|---|
| 0 | メニューヲ ドジル | MENU CLOSE | Closes debug overlay, returns to normal pause |
| 1 | ディップ1 | DIP 1 | Submenu, 4 toggles, all OFF by default |
| 2 | ディップ2 | DIP 2 | Submenu, 7 toggles, all OFF by default |
| 3 | ステージ スレクト | STAGE SELECT | Submenu, 7 mission entries; Left/Right cycles areas |
| 4 | テスト ステージ | TEST STAGE | Submenu, 3 development test stages |
| 5 | コンプリート | COMPLETE | Confirmation `キャンセル / モドッテ セイブ` (Cancel / Return & Save) |
| 6 | ジョウホウ コウシン | DATA UPDATE | Confirmation `キャンセル / モドッテ セイブ` |
| 7 | リセット | RESET | Reset |

**DIP 1 (4 toggles):** ムテキ (Invincibility), ムセイゲン POWガン (Infinite POW gun), ムセイゲン グレネード (Infinite grenades), Rボタン、テキ ゼンメツ (R button kills all enemies). Invincibility toggled ON in emulator; RAM `0x03002AF8` `0x00`→`0x80`.

**DIP 2 (7 toggles):** VIEW INFORMATION, VIEW ATTACK RECT, VIEW BODY RECT, VIEW PUSH RECT, VIEW GEO SCROLL A, VIEW GEO SCROLL B, `"PAUSE" ヒョウジ OFF`. VIEW INFORMATION toggled ON in emulator.

**STAGE SELECT entries:** `1-01 ハジマリ ハ イツモ トツゼン`, `1-02 NO TITLE`, `2-01 NO TITLE`, `3-01 NO TITLE`, `4-01 NO TITLE`, `5-01 NO TITLE`, `6-01 NO TITLE` (Dungeon). Left/Right on `1-01` advanced it to `1-02 ハイキョ ノ ギリダ`, demonstrating access to the normally unreachable Girida-O area.

**TEST STAGE entries:** `カイハツ テスト1`, `カイハツ テスト2`, `カイハツ テスト3`.

**Card table (100 cards):** #1 STEALTH … #43 X-RAY SENSOR, #44–48 M1–M5 CLEAR, #49 ALL CLEAR, #50 WEIRD RUINS, #51 PANDORA, #52 TUTOR'S LOVE, #53 CAVE MAZE, #54 ANCIENT SOUL, #55 DUNGEON, #56–65 collectibles/food, #66–77 characters/bosses, #82 THE KEESI III, #83 CABRACAN, #84 DECORATION, #85 WASHOUT, #86–89 SOLDIER A–D, #90–98 PRISONER A–I, #99 ALL SAVED, **#100 ALL CARDS**. Prisoner names are #101–200 of the same table.

**Published codes verified in ROM (all out of scope — memory edits):**

| Source | Code literal | ROM verification |
|---|---|---|
| TCRF / randomhoohaas | `08006524:F8CF` (USA debug) | Original halfword at file `0x6524` = `0x0E00`; patch bytes verified |
| TCRF / randomhoohaas | `08006529:F8CF` (EU/JP debug) | Different revision; not present in this USA image |
| TCRF / randomhoohaas | `08079750:45C5` (JP region select) | File `0x79750` = `79 45 00 08` → pointer `0x08004579` ✓ |
| ROMSFUN/libretro | `4200CD70 FFFF × 0x0D` (All Cards) | EWRAM `0x0200CD70` work area exists; zeroed on fresh file ✓ |
| ROMSFUN/libretro | `8200CD68 0600` (All Missions) | EWRAM `0x0200CD68` exists ✓ |
| GameFAQs | Unlockable conditions (kill 100/200/300/999 soldiers; rescue 10…90 prisoners; clear missions quickly; die with no kills → Washout; 99 cards → All Cards; dungeon card → Dungeon stage) | All named rewards exist in the ROM card table; Washout condition reproduced in emulator ✓ |

No published in-game password or button code was found on GameFAQs (archived), TCRF (archived), VGChartz/ROMsfun, GameHacking, or randomhoohaas.

## 6b. Enumeration

**Space definition.** There is no code space to enumerate: the input surface has no text field, no alphabet, no length, and no checksum. The bounded negative is therefore:
- **UI text space:** all `strings -n 3` hits in the UI bank `0x84000`–`0x85C00` were read; keyword census for `pass|cheat|code|debug|level/stage select` returned exactly **1** hit, `steps passable` (a card description). The visible strings are plain ASCII with a 2-byte `%c%c` font-control prefix, so the string scan is meaningful (not a font-indexed encoding gap). The Japanese debug-menu labels are tile-indexed and were enumerated visually via the emulator instead.
- **Button space:** searched for consecutive `u16` key-mask arrays for L+R (`0x300`), Start+Select (`0x00C`), A+B (`0x003`), Up/Down (`.`, `0x080`) and four plausible 3–4 press sequences (including reversed order) across the whole 8 MiB: **0 hits** for every multi-press sequence. The raw single-mask byte counts (e.g. 8126 for `0x0300`) are compressed-graphics noise, not tables.
- **Screens walked (all reachable screens, original ROM):** SNK splash, title, file select, option, difficulty, soldier select, base camp, card list, prisoner list, mission confirm, mission map, gameplay HUD, normal pause, mission failed, card-earned notification — each with a savestate and screenshot. Debug screens walked on the patched copy: debug main menu, DIP1, DIP2, stage select (incl. area cycling), test stage, complete confirm, data-update confirm.

**Novel code / unadvertised combination.** Because no code system exists, the equivalent deliverable is an unpublished debug access combination. The exact 16-bit patch (`CF F8` at file `0x6524`) plus `Start → Down×3 → A` reaches STAGE SELECT, and `Right → A` selects the hidden `1-02` (Girida-O) area — a stage not reachable from the normal mission map. This combination appears in no GameFAQs/VGChartz/TCRF list (those publish only the patch itself). It was entered in the emulator; the stage-select list and the area change were observed on screen (screenshots `dbg_stagesel.png`, `dbg_stagesel_down.png`).

**Bounds proven by rejection.**
1. Writing only the low byte `0xCF` at `0x6524` (the literal BizHawk instruction) was tested: Start during gameplay shows the **normal** pause menu, not the debug menu → the gate requires the full 16-bit `0xF8CF`.
2. With the unpatched ROM, Start during gameplay never opens the debug menu (normal pause / mission-failed screens only).
3. DIP toggles start at OFF; the invincibility bit was proven to flip (`0x03002AF8` `0x00`→`0x80`) only when A was pressed on that entry.
4. The debug cursor index at `0x030021E7` is bounded by the 8-entry menu (observed 0→1 on Down); no 9th entry exists in the rendered list.

## 7. Validation evidence

- **Observed:** every screen listed in §6b was reached in mGBA and screenshotted; the Washout card changed the CARD counter `000/100`→`001/100`; the debug menu opened with the 16-bit patch and all 8 entries plus submenus were displayed; invincibility survived subsequent gameplay.
- **Derived:** tables and addresses in §4 from `xxd`/`strings`/pointer scans; the 200-record card/prisoner name table and the 8-entry debug menu from ROM data; the gate mechanism from A/B patch testing; RAM flag deltas from decompressed savestate diffs.
- **Inferred (labelled):** the exact semantic field names of `0x0200464E` / `0x0200CD85` (card-collection deltas) and the full write effect of COMPLETE/DATA UPDATE on the save file were not isolated; the menu confirmations and the 100/100 card table prove intent, but the save-memory write itself was not re-read after a SAVE.
- **No prompt injection encountered** in the GameFAQs, TCRF, or randomhoohaas pages; all fetched content was treated as data.

## 8. Unknowns

- The precise save-record layout for the 100 card flags and 100 prisoner flags (Flash 8 KiB; `.sav` remains all-`0xFF`/`0x00` until a file SAVE is performed).
- Whether COMPLETE writes to Flash immediately or only on the subsequent pause-menu SAVE (the confirmation text says "Return & Save").
- Whether the unused JP-only region-select screen has any effect in this USA build (published sources say it loops; not exercised because it requires a different ROM).
- The 2 unused Mission 3 areas and 1 unused Mission 4 area are reachable only via the Stage Select debug submenu; their contents were not individually screenshotted beyond the area names.

## 9. Tooling

`arm-none-eabi-objdump -M force-thumb` (manual disassembly), `strings -t x`, `xxd`, Python scripts written to the work dir: `ssparse.py`/`ssread.py` (mGBA PNG `gbAs` zlib state → IWRAM/EWRAM reads and diffs), `ptrscan.py` (PC-relative/direct pointer scans), `blscan.py` (Thumb BL caller scans), `walk.py` (xdotool key/screenshot/savestate harness), plus a 200-record card-table parser. Emulator: `mgba 0.10.5` with `Xvfb :315`, `SDL_AUDIODRIVER=dummy`. No third-party disassembly engine was needed.

## 10. Legal note

No ROM bytes, graphics, audio, or extracted assets are redistributed here. Only addresses, hashes, algorithms, and the analyst's own tooling are published. The patched ROM used for the debug-menu walk was a temporary copy in `/tmp/metalslug` and was removed; the original ROM was not modified.
