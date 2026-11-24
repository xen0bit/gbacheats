# Naruto: Ninja Council (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Naruto: Ninja Council.gba` |
| Size | `0x800000` (8,388,608 bytes) |
| Header title | `NARUTO US1` |
| Game code | `A7AE` |
| Maker | `DA` (boot logo: TOMY Dream Energy) |
| Version | `0x00`; complement `0xFC`; header checksum `0x0000` |
| Entry branch | `0xEA00002E` → stock crt0 at `0x080000C0` |
| MD5 | `dffc7306234751e18b163fbf3e925f1b` |
| SHA-1 | `1e4c622668c4cc0c9e86816507ada8c17491c257` |
| SHA-256 | `0108679db5f628ebec5d0953a2ec80861f5932029023057ab1e4fffbd01f880b` |

Phase 0 result: **one** embedded GBA header (Nintendo-logo scan over the whole 8 MiB finds only offset `0x0`); no appended trainer, no cracktro, no GameShark/CodeBreaker signature, stock entry word. The `0x0000` header checksum / non-standard complement byte are the only anomalies and are treated as a rebuilt-header artifact, not a patch (§16.1).

The sibling image `Naruto: Ninja Council 2.gba` is a **different ROM**: title `NARUTO US2`, code `BN2E`, MD5 `60eca5e9057972a76361158cc7ab31b8`, first difference at byte 169. None of NC1's debug strings (`NARUTO MENUE` at file `0x5A5D8`, `NARUTO MAIN` at `0x18C2C0`, `farc/farc_dev_na.c` at `0x5A648`) occur in NC2. **Nothing is shared** between the two images at the level examined here; NC2's published "Access Debug Menu [Sel+Up]" is a GameShark code for that other image and does not apply to NC1.

## 2. Executive summary

**No developer-intended cheat system exists in this retail image.** There is no password screen, no button-code sequence, and no reachable hidden/debug menu. The only unlockables (Kakashi, 2nd Mission, Sound Test, Picture Gallery, 4th-level jutsu) are ordinary save-flag / story-progress rewards, not cheats — they are gated by `clear` and `leaf-symbol` counters in the EEPROM save, exactly the §16.18 "save-bit unlock, not a code" pattern.

Every published code found on the web is a **GameShark / Action Replay** device code (Master `d1e47677 c9179121 f5d1146a b4e2f983`, Infinite Health `08471805 d7152c89`, Infinite Energy `cdd7f4a7 4bb9cdb0`, Infinite Time `dea29a00 ed31cd6e`, Huge Score `612d341c c9d1ec6f`, Infinite Lives `f627de9b ebbeeeba 10732338 e43cb155`, Super Jump `e16e6cd3 22b85a6c ed9ce59b 0090ed9d`, plus 3rd party cheat indexes' "Unlock all Extras"/"Skip Area [Sel+L]"). None of these words appear in the ROM as ASCII or as `u32` (one coincidental `u32` hit at `0x0860935E` is inside compressed graphics). They are cheat-device decryption seeds, explicitly out of scope.

The image *does* contain a **dormant developer menu** — a two-entry record table and its renderer (addresses below) — but it is an alternate branch of the engine's generic dialogue/menu library, is not selected by any in-game input, and booting with the scene index forced to `0` produced a story cutscene rather than the menu. It is therefore reported as gated/dead developer code, not as an accessible cheat (§16.3 case 2/4).

## 3. How to reproduce

Emulator: `mgba -3` under `Xvfb :318 -screen 0 1024x768x24`, `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, `openbox` window manager. Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Holds of 100–300 ms.

Screen path (each transition RAM-verified through the scene object at `0x030010F4` → `+2` scene index, `+0xC` function-triplet pointer):

1. Boot → TOMY Dream Energy → Shōnen Jump → title (scene index **1**, triplet `0x0818DAA0`).
2. Start ×2 → save-slot select (scene **9**).
3. A on "Save 1" → main menu: exactly `Story Mode` / `Free Mode` (scene **13**, triplet `0x0818DB30`). Down wraps between the two; no third entry.
4. A on "Free Mode" → character select: `Naruto`, `Sasuke` only (scene **10**, triplet `0x0818DB0C`). Right from Sasuke wraps to Naruto — Kakashi is absent until unlocked.
5. A on a character → level select, first entry "Seaside Bridge", with a "Leaf Scroll" counter (scene **10**).
6. A → story dialogue ("You ready, Naruto?", "If you can find me … Genjutsu") → level gameplay with HUD (TIME, HP, chakra, score).
7. Start in gameplay → **PAUSE** overlay with exactly `Back to Game` / `End Game`. Menu-manager globals at `0x03000810/14/18/1C/20` read `[1,0,1,0,0]` on every screen examined; the pause cursor lives near `0x030029A0`.

RAM evidence was captured by mGBA `.ss1`–`.ss9` savestates: the PNG `gbAs` chunk is zlib-compressed; payload length `0x61000`, with IWRAM at payload `0x19000` and EWRAM at `0x21000` (guide §16.13). All scene/triplet values above were read from those payloads, not inferred from screenshots.

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` | code (ARM) | stock crt0 entry |
| `0x080002B8` | code (Thumb) | `main`; boot calls scene 15 at `0x080002C8` |
| `0x08000570` / `0x080005A4` / `0x080005D4` | code | init / loop / cleanup triplet used by the dormant menu renderer |
| `0x080005A4` | code | calls menu input `0x080007D8` then draw dispatcher `0x08000A40` |
| `0x080007D8` | code | generic menu input handler (reads key halfword at `0x030010DC+2`) |
| `0x080008A4` | code | paged renderer: draws `RETURN TO MENU`, `PREV PAGE`, `NEXT PAGE` |
| `0x08000964` | code | list renderer: draws `NARUTO MENUE` plus the two records |
| `0x08000A40` | code | draw dispatcher: branches on `[0x0300081C]` |
| `0x08004424` | code | scene dispatcher: `triplet = 0x0818DA94 + index*12`, stores to scene object `+0xC` |
| `0x08004454` | code | request next scene (writes scene object `+4`) |
| `0x08004460` | code | per-frame scene update; consumes `+4` and calls `0x08004424` |
| `0x0805A5AC` / `5C0` / `5CC` / `5D8` | data | ASCII `< RETURN TO MENU`, `< PREV PAGE`, `NEXT PAGE >`, `--NARUTO MENUE--` |
| `0x0805A600` | data | **dormant menu records**, 12-byte stride: `{u32 title-ptr, u32 desc-ptr, u32 handler}`; terminator all-zero at `0x0805A618` |
| `0x0818C2C0` / `0x0818C2CC` | data | "NARUTO MAIN" / Japanese Shift-JIS help text |
| `0x0818C3A8` / `0x0818C3BC` | data | "NARUTO Chara Viewer" / Japanese Shift-JIS help text |
| `0x0801A06D`, `0x0801A3C5` | code | record handlers (sprite/character viewer scenes) |
| `0x0818DAA4`, `0x0818DAEC` | data | function-pointer tables, 50 and 32 entries, `u32` Thumb pointers |
| `0x0818DA94` | data | scene function-triplet table (`index*12`) |
| `0x0818DAA0` / `DB0C` / `DB30` / `DB48` | data | triplets for scenes 1 (main), 10 (select), 13 (menu), 15 (boot) |
| `0x030010F4` | RAM (IWRAM) | pointer to scene object (observed `0x03001164`) |
| `0x03001164+2 / +4 / +0xC` | RAM | current scene index / requested next scene / triplet pointer |
| `0x03000810/14/18/1C/20` | RAM | generic menu-manager counters/page index |
| `0x03001988` | RAM | text/window state used by renderer |
| `0x08170298` | data | 4bpp font tiles, 32 bytes per tile, indexed directly by text byte |
| `0x0805A8AC`, `0x0805A954` | data | glyph-index ↔ character tables (12 glyphs per row) |

File offset = ROM address − `0x08000000` throughout (flat 8 MiB image).

## 5. Algorithm

Not applicable — no password/checksum/button-code algorithm exists in this image. The relevant reconstructed behaviour is the scene/menu machinery:

```
scene_set(index):                       # 0x08004424
    obj = [0x030010F4]
    obj[+2] = index
    obj[+0xC] = 0x0818DA94 + index*12   # {init, loop, cleanup} Thumb pointers (|1)
    obj[+0] = 0
    obj[+4] = 0xFFFF                    # no pending transition

each frame (0x08004460):
    obj = [0x030010F4]
    if obj[+0xC] == 0: return
    switch obj[+0]:                     # scene-local state 0/1/2
        state 0 -> call init triplet[0]; on result -> state 1
        state 1 -> call loop triplet[1]
        state 2 -> call cleanup triplet[2] -> scene_set(next)
    next = obj[+4]
    if next != 0xFFFF: scene_set(next)  # 0x080044D0..0x080044F0
```

The dormant menu's draw path:

```
draw_dispatch():                        # 0x08000A40
    if [0x0300081C] == 0: draw_record_menu(0x0805A600, 2 entries)  # 0x08000964
    else:                 draw_paged_text(...)                       # 0x080008A4
```

The record table decodes to exactly two live records (third record is all-zero terminator); each record's first field is a pointer to a `{title_ptr, help_ptr}` pair.

## 6. Tables

**Dormant menu records at `0x0805A600`:**

| # | Title | Help (Japanese, decoded via Shift-JIS) | Handler |
|---|---|---|---|
| 0 | `NARUTO MAIN` (at `0x0818C2C0`) | "Sprite enlargement/reduction, rotation, mosaic, bilinear-filter effects can be checked. +key: move; L: shrink mosaic; R: enlarge mosaic; B&+: scale; B&L/R: rotate; A: toggle bilinear filter" | `0x0801A06D` |
| 1 | `NARUTO Chara Viewer` (at `0x0818C3A8`) | "same controls; character viewer" | `0x0801A3C5` |
| 2 | — | all-zero terminator | — |

**Function-pointer table `0x0818DAA4`** (50 entries, first few): `0x0801A06D, 0x0801A005, 0x0803A269, 0x0803A2A9, 0x0803A289, 0x0803A33D, …`; `0x0818DAEC` is a 32-entry suffix table beginning `0x0801A3C5, 0x0801A3A5, …`. Neither table is referenced by any BL or u32 pointer found in the image — they are only reached through the dormant renderer's index arithmetic.

**Save format** (EEPROM, 512 bytes, `NARUTOEE` magic reversed in header): presence of unlockables is stored as progress bits; no field of the save is compared against player-entered text.

## 6b. Enumeration

Because **no code system exists**, the enumeration deliverable is the bounded negative (guide §0.2 items 1–5 applied negatively):

- **Screen space enumerated (all reachable screens walked, with RAM scene/triplet evidence):** boot/logo, title, save-slot select, main menu (2 items), character select (2 characters), level select (first "Seaside Bridge"), story dialogue, gameplay, pause (2 items). No options/settings screen exists in this image — neither the title nor the pause menu offers one. No password/cheat entry surface was observed on any of them.
- **Text space searched with counts:** `strings -t x -n 4` → **47,761** strings; case-insensitive keyword scan for `password|cheat|code|debug|secret|unlock|level|menu|invalid|enter|master|konami|bonus|hidden|extra|boss|story` returned **2** lines (`< RETURN TO MENU` @ `0x5A5AC`, `--NARUTO MENUE--` @ `0x5A5D8`), plus the related `PREV PAGE`/`NEXT PAGE` in the same data block. All UI text is font/tile-indexed (font tiles `0x08170298`, glyph tables `0x0805A8AC`/`0x0805A954`); searches for `Story Mode`, `Free Mode`, `Seaside Bridge`, `Save 1`, `Kakashi` returned **zero** ASCII hits in both ROM and decompressed savestate RAM, so the "no password string" result rests on the decoded tile-indexed text bank rather than on `strings` alone. Zero password-alphabet tables were found among the 48 alphabet-like ASCII runs (all are compressed-data noise).
- **Button space searched with counts:** raw `u16` scan for key-mask-like runs found **6,609** candidate runs ≥4; inspection of the first 60 shows they are palette/tile data (repeating `0x101/0x202/0x303`), not input sequences — no run is a plausible key-mask code. **24** held-button combinations were entered on the title screen (Select alone and with each direction/A/B/L/R/Start; L+R; L+R+Start; L+R+Select; L+R+A+B; Start+Select+A+B; Up/Down pairs; L/R + Up/Down; A+B; Select+A+B). Only the expected confirm buttons advanced the scene from 1 → 13 (main menu); **none** reached scene 0 or any hidden screen. The NC2 "[Sel+Up]" debug claim is a GameShark patch, not a reachable combo in NC1.
- **Published codes tested:** all GameShark/Action-Replay words from 3rd party cheat indexes and the archived lists were searched as ASCII and as `u32`: **0 / 19** meaningful hits (one hit is inside compressed graphics). They cannot be entered through the game's own UI and are out of scope.
- **Novel code / bounds:** impossible by construction — there is no validator, no alphabet, no checksum and no entry field to mint a code for or to reject an out-of-range value. Forced scene values (0 via boot-code patch on a **copy**, and via savestate patch) were used only to probe the dormant menu; they are memory edits, not cheats, and are not reported as codes. The boot-patch copy produced a story cutscene; the savestate patch crashed mGBA, so neither demonstrates an accessible hidden screen.

## 7. Validation evidence

- **Observed:** every screen listed in §3, captured as screenshots on `DISPLAY=:318`; scene indices/triplet pointers read from zlib-decompressed `.ss*` savestates; ROM hashes/header/logo scan; button-combo results; published-code literal searches.
- **Derived:** function boundaries and data-table meanings from Thumb disassembly (`0x08000570`/`0x080005A4`/`0x08000A40`/`0x08004424`/`0x08004460`) and literal-pool reads verified with `struct.unpack_from` (objdump's split halves were re-read as 32-bit words, per §11); the two-record count from the all-zero terminator at `0x0805A618`; the Japanese help-text translation via Shift-JIS.
- **Inferred:** that the `0x0805A600` records are leftover developer tools (the descriptions are unmistakably debug-oriented, but no in-game caller was exercised); that the `0x0000` header checksum is a rebuild artifact. The exact meaning of `[0x0300081C]` as the renderer's mode select is derived from the `cmp #0`/`beq` at `0x08000A42–0x08000A48`, but which in-game state (if any) sets it to select the record menu was not isolated.

## 8. Unknowns

- Whether any post-game/save-flag state ever selects the `0x08000964` record-menu branch of `0x08000A40`. The only writers of the relevant menu-manager globals were not exhaustively enumerated; completing the story to generate the "Gallery"/"Sound Test" unlockables would settle this, but those are save-bit unlocks (not cheats) even if they add menu entries.
- The 50- and 32-entry function-pointer tables at `0x0818DAA4`/`0x0818DAEC` were dumped but their consumers were not identified beyond the dormant renderer.
- The exact glyph↔character table used for the English tile-indexed text was not fully reconstructed; the negative text result therefore rests on "no ASCII/password literal in any encoding checked" plus complete screen enumeration, not on a full font decode.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` and a Capstone-based annotated disassembler (`cdis.py`) for Thumb ranges; `struct.unpack_from` for literal-pool verification.
- Custom Python: `scan_ptrs.py`/`xref.py` (u32 + Thumb-LDR + BL scanners), `patterns.py` (key-mask and alphabet scans), `findtext.py` (XOR/add/rotate text transforms), `ss.py`/`ssram.py` (savestate `gbAs` extraction and IWRAM/EWRAM reads), `combotest.py` (24 combo sweep with RAM probing), `patchss.py` (savestate patching), `fontrender.py` (tile rendering), `gba.py` (xdotool helpers).
- mGBA 3× under Xvfb `:318` with openbox; `scrot` + ImageMagick crop to the 720×480 viewport. GDB stub was tried but halts the core at reset on this build, so RAM evidence used savestates instead.
- No ROM or copyrighted assets are redistributed; all outputs are addresses, hashes, algorithms and the analyst's own scripts.

**Legal note:** analysis only; no ROM, graphics, audio or game text is republished here.
