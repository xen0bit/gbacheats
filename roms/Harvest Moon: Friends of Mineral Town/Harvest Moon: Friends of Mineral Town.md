# Harvest Moon: Friends of Mineral Town (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Harvest Moon: Friends of Mineral Town.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| `file` result | `Game Boy Advance ROM image: "HARVESTMOGBA" (A4NEE9, Rev.00)` |
| Header title | `HARVESTMOGBA` |
| Game code | `A4NE` |
| Maker code | `E9` (Victor Interactive Software / Natsume) |
| Version (0xBC) | `0x00` |
| Complement byte (0xBD) | `0x48` |
| Header checksum (0xBE) | `0x0000` — normal rebuilt-header artifact; complement byte is the edited-header signal |
| Fixed 0x96 (0xB2) | present |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock, **not** a scene cracktro) |
| MD5 | `80355c831a7a25b0f70dc021ebd344f1` |
| SHA-1 | `a2fc3574f0a65a4fcf7682fb274b9d7eebdef963` |
| SHA-256 | `ca6cebe7211b6f2693af210709f76222204bf9f7621dec08b30ca268117460dd` |

Phase 0 checks: the 152-byte Nintendo-logo scan found **exactly one** GBA header, at file `0x0`. No multiboot stub, 2-in-1 image, appended trainer, or entry-point patch. Save device is 32 KiB SRAM (`.sav` magic `47 42 41 ... 53 52 41`: "GBA…SRA").

## 2. Executive summary

**There is no developer-intended cheat system in this ROM** — no password entry screen, no gift-code validator, no button-code sequence, and no hidden/debug menu. Every published "code" for this SKU is a GameShark / CodeBreaker / Action Replay **memory-edit** code (including the two button-conditional ones, `SEL+L` "till whole field" and `B+L` "speed up time"), which is explicitly out of scope for this engagement; the cheat-device master-code literals are absent from the ROM, as expected for codes that patch RAM at runtime.

This is a **bounded negative** (guide §0.2 item 5), not an untested guess: (a) every reachable screen was walked in mGBA and RAM-verified; (b) the complete ASCII string corpus was classified and the font/tile-indexed text path was decoded; (c) the input space was searched for password alphabets, comparison tables, key-mask sequences and debug gates with explicit counts; (d) 11 title-screen, 5 boot-time and 11 in-game button probes produced no undocumented screen. The game's only text-input surfaces are the four **name fields** (Your / Farm's / Dog's name and the on-screen keyboard alphabet at `0x0E89B6`), which are labels consumed by the save record, not a validator (guide §16.2b). The `DIARY` menu is the save/load/settings screen; its seven sibling icons are the entire in-game menu set.

## 3. How to reproduce

- Emulator: `mgba 0.10.5`, `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, launched `mgba -3 <rom>`.
- Keymap verified against `KEYINPUT` (`0x04000130`, active-low): idle `0x03FF`; `x`=A→`0x03FE`; `z`=B→`0x03FD`; `a`=L→`0x01FF`; `s`=R→`0x02FF`; `Return`=Start→`0x03F7`; `BackSpace`=Select→`0x03FB`; arrows→`0x03BF/37DF/03EF/037F`. The game's input library converts with `~KEYINPUT & 0x3FF` at `0x0800912C` (literal `0x04000130` at `0x08009138`, mask `0x03FF` at `0x0800913C`).
- Exact new-game path: title → **A** → "Your Name" keyboard → type → **Start** (moves cursor to *End*) → **A** → "Is this name correct? Yes" → birthday (season, day) → two confirmations → "Farm's Name" → "Dog's Name" → "Is this OK? Yes" → intro cutscene (Thomas / Mother / flashback) → farm.
- Menus: **Start** alone = date/time overlay; **Start+L** = seven-icon bar (Diary, Rucksack, World Map, Farm Map, Earnings, Memo, Tutorial); **L/R** = cycle held item. Bed in farmhouse → Diary/Save screen.
- **RAM evidence method**: `Shift+F1` writes mGBA `.ss1`; the `gbAs` PNG chunk is zlib-compressed. Layout verified against mGBA source (`include/mgba/internal/gba/serialize.h`): state `0x00400`=I/O, `0x19000`=IWRAM (`0x03000000`), `0x21000`=EWRAM (`0x02000000`), total `0x61000`. `ram.py` in the work dir parses any state to arbitrary GBA addresses. (The GDB stub on port 2345 was single-client and shared with another session, so savestate reads were used as the primary RAM oracle.)
- Codes tested: none applicable — no in-game code entry surface exists. Published cheat-device codes were catalogued, classified as out of scope, and their master literals searched for in the ROM (all absent).

## 4. Address map

| ROM / file | Meaning | Evidence |
|---|---|---|
| `0x08000000`/`0x000000` | Stock reset branch `0xEA00002E` | Derived (header + disassembly) |
| `0x080000C0` | ARM crt0; BSS zero-fill; constructor table `0x080E8610` | Derived (objdump) |
| `0x0800018C` | `main` — init, RAM banks, scene-task creation | Derived (Ghidra decompile) |
| `0x0800082C` | Scene/task scheduler (230-byte loop) | Derived (Ghidra) |
| `0x080036F8` → `0x080E5A18` | Initial scene task definition; function-pointer records | Derived |
| `0x0800912C` | `keys_current()` = `~KEYINPUT & 0x03FF` (active-high) | Derived (objdump) |
| `0x08009138`, `0x0800913C` | Literal pools `0x04000130`, `0x03FF` | Observed (bytes) |
| `0x0E86A8`–`0x0E8A6A` | Diary/menu/save/name-entry ASCII label bank | Observed (`strings -t x`) |
| `0x0E89B6`–`0x0E8A6A` | On-screen keyboard alphabet (`A-Z o a-z ' . 0-9 + - x ~ / < > ( ) & ! ?`) | Observed |
| `0x08100A36` | Generic C-library charset `A-Za-z0-9…`, next to `bad_alloc` — **not** a code alphabet | Observed + classified |
| `0x08139B80`–`0x08139CEF` | ASCII→tile/font conversion tables (rendering only) | Derived |
| RAM `0x04000130` | Keypad (active-low), probed values above | Observed |
| RAM `0x02006640`–`0x02006660` | Name buffers; ASCII `_` padding during entry, 16-bit font tile indices (`0x12D0`, `0x12AF`, …) after confirm | Observed (savestate diff) |
| SRAM `0x0E000000` | 32 KiB save; updated by Diary→Save (`YYYY MM-DD`, farm name, player name) | Observed (`.sav` mtime + content) |

## 5. Algorithm

No password/checksum algorithm exists. The only transformation found is the ordinary font pipeline: ASCII labels in ROM → 16-bit tile indices in EWRAM (`0x02006640` region) → VRAM glyphs. There is no comparison table, no `strcmp`/`memcmp` against a user-input buffer, no hash/checksum loop, and no generator/decoder pair. The input library is a standard held/pressed/released key-state helper (`0x08009140`–`0x080091A2`) used by every screen; it contains no cheat matcher.

The scene system is a linked task scheduler: `main` seeds a task at `0x080036F8`; `FUN_0800082C` repeatedly constructs/executes/destroys tasks via `FUN_080D3914`. No task corresponds to an unlabelled or hidden screen — all reachable tasks were observed through the walks in §3.

## 6. Tables

- **On-screen keyboard alphabet** (`0x0E89B6`, 5 rows): `ABCDEFGHIJKLMNO`, `PQRSTUVWXYZ o`, `abcdefghijklmno`, `pqrstuvwxyz ' .`, `0123456789 + - x ~ /`, `< > ( )`, `& ! ?`. Used for the four name fields only.
- **Diary menu rows**: `Diary` → Save (`Write in diary.`) / Load (`Read diary.`), slot Data 1 / Data 2; `Buttons` → 1 / 2 (Control Pad Walk/Run, R Button Run/Walk); `Clock` Yes/No; `Face` Yes/No; `Name` Yes/No. Strings: "There is no saved data.", "Save failed.", "Load failed.", "The saved data may be corrupted.", "Load?", "Overwrite?" (`0x0E878C`–`0x0E8914`).
- **Seven icon-menu entries**: Diary, Rucksack, World Map, Farm Map, Earnings, Memo, Tutorial (`0x0E86A8`–`0x0E8A28`). Tutorial submenu: Crops / Animals / Useful Tips / Exit. Exhaustive; no eighth slot.
- **Title options**: `start`; `continue` appears only once a save exists. No Options, Password, Gift or Debug entry.
- **Cheat-device codes (out of scope, catalogued only)**: GameFAQs FAQ 26955, Neoseeker CB/GS lists, `harvestmoon.fandom.com/wiki/Gameshark_Codes_(FoMT)`, supercheats. All are direct SRAM/EWRAM pokes (e.g. `32004080 E100`, `820068B4 E0FF`, master codes `0000E882 000A / 100D1BF8 0007`, `98D7716AE281 2FEC9AA2DBAB 71D84B76AC98`). Button-conditioned members (`SEL+L` till field, `B+L` speed-up) are cheat-device *conditions* on RAM writes, not in-game button codes. chaptercheats lists this SKU as "No Codes, No Passwords, No Unlockables".

## 6b. Enumeration

**Space size: zero.** There is no code/password space to enumerate — no alphabet+length+checksum field space, no lookup table, and no button-sequence state machine. Consequently the §0.2 deliverables "mint a novel code" and "bounds proven by rejection" are **not applicable**; the negative itself is bounded and quantified below.

Negative-search space checked (all counts from this ROM/hash):

| Search space | Count / result |
|---|---|
| ASCII string corpus | 116,562 strings (`strings -t x -n 4`); keyword hits: `password` **0**, `game(shark)` **0**, `codebreaker` **0**, `cheat` **1** (dialogue "trying to cheat."), `debug` **2** (credits job title "Debuggers"), `unlock` **1** (dialogue), `secret` **36** (dialogue), `gift` (dialogue only). `SCR CODE` ×1329 = RIFF audio chunk ID, not codes. |
| Password/alphabet literals | `ABCDEFGHIJKLMNOPQRSTUVWXYZ` ×1 (C library at `0x08100A36`), `0123456789` ×3 (library/encoding tables), `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` ×0. No password alphabet in the game's own data. |
| Key-mask sequence tables (`01 02 04 08 10 20 40 80` and reverse, as u8/u16) | **0** hits. No button-code table. |
| `0x04000130` literal in ROM | **2** (`0x080002CC`, `0x08009138`) — both in the generic input library, not a cheat matcher. |
| Published cheat-device master-code literals (u32) | 0 hits for each of `0x0000E882`, `0x100D1BF8`, `0x98D7716A`, `0x2FEC9AA2` — confirming they patch RAM rather than appear in game data. |
| Title-button probes (no save) | 11 combinations: Select, L, R, B, A+B, L+R, Start+Select, Up+Down, L+R+Start+Select, R+A, L+A → only A advances; no hidden screen. |
| Title-button probes (with save) | 7: none/down/up/Select/L+R/Start+Select/B → cursor only toggles start↔continue; no third option. |
| Boot-time combo probes | 5: L+R, L+R+Start+Select, Start+A, Up+Down+A+B, Select+A+B → all remained the attract screen; no debug entry. |
| In-game button probes | 11: A, B, L, R, Select, Start, L+R, Select+L, Select+R, Start+L, Start+R → only documented effects (tool cycle, date/time, 7-icon menu). |
| Screens walked to completion | 25 (see §7) including all four name-entry screens, all confirmations, intro, farm, house, overlays, seven icon sub-screens and the Diary save/load settings. |

**Bounds**: the four name fields are capped at 12 characters and accept the 62-symbol keyboard alphabet; their consumer is the save record / on-screen labels (the only comparisons against the buffer are renderer font lookups), so no string-length or checksum predicate exists that could constitute a password validator (§16.2b). The button space tested covers every single key, every plausible multi-key gate, and the whole documented menu set; the ROM contains no key-mask table for any longer sequence.

## 7. Validation evidence

**Observed (emulator + RAM)** — screenshot files in `/tmp/opencode/harvestfomt/`:
- `01_title.png`, `title_saved2.png` — title with 1 and 2 options.
- `name_final.png`, `after_endA.png`, `birthday.png`, `farmname2.png`, `farm_confirm.png`, `dogname.png`, `dog_confirm.png`, `final_confirm.png` — full name-entry flow.
- `game1.png`–`game5.png`, `intro1.png` — intro cutscene and first farm view.
- `menu_start.png` — date/time overlay; `icons_contact.png` — all seven menu icons; `open_contact.png` — all seven sub-screens; `diary2.png`/`save_attempt2.png` — save/load and settings; `title_contact.png`, `ts_contact.png`, `boot_contact.png`, `ig_contact.png` — every button probe.
- RAM: `KEYINPUT` reads above; name-buffer ASCII→font-tile transition at `0x02006640`; 32 KiB SRAM save updated on Diary→Save.
- Savestate diffing (`ram.py`, `walk.py`) was the primary RAM oracle because the mGBA GDB stub on :2345 is single-client and was shared with another active session.

**Derived (disassembly / Ghidra)** — crt0 and main at `0x080000C0`/`0x0800018C`; task scheduler `0x0800082C`; input library `0x0800912C`; menu/name label banks; font conversion tables; exact mGBA savestate memory layout.

**Inferred** — that the game has no unfinished/cut debug screen: no ASCII label, pointer, key-mask table or task entry for one was found, and no input reached one. This is labelled inference, not direct observation of a dead code path.

**Fetched web pages** (GameFAQs, Neoseeker, Fandom, supercheats, chaptercheats) were treated strictly as data. No instruction-bearing/prompt-injection payload was encountered in this session's fetches.

## 8. Unknowns

- A GC↔GBA link-cable feature with *A Wonderful Life* (connection stars → seaside cottage) exists per public documentation; it is a link event, not a code/password, and was not exercised (no second console/ROM). It is not a cheat surface.
- Ghidra's raw-ARM auto-analysis treated some Thumb data as ARM; the addresses cited here were cross-checked with `objdump -M force-thumb` and live savestate RAM.
- No in-game code-of-any-kind was found, so §16.19's "call the validator as an oracle" technique had no target to apply to.

## 9. Tooling

- `mgba 0.10.5` (SDL, Xvfb `:315`, openbox, `SDL_AUDIODRIVER=dummy`), `xdotool`, `scrot`, ImageMagick (`convert`/`montage`).
- `arm-none-eabi-objdump` (`-M force-thumb`), Capstone 5.0.7, `strings`, `xxd`, Python 3.13.
- REA/Ghidra 12.1.4 (`open_binary` raw-binary ARM @ `0x08000000`) for `main`/task-scheduler decompilation; session closed afterwards.
- Work scripts in `/tmp/opencode/harvestfomt/`: `ui.py` (input/capture), `ram.py` (savestate→GBA RAM reader), `walk.py`, `scan.py` (Capstone literal/BL scans), `title_probe.py`, `ingame_probe.py`, `boot_probe.py`.
- No ROM or copyrighted assets are redistributed; only hashes, addresses and original findings are published.

## 10. Legal note

Only findings (hashes, addresses, algorithms, scripts) are recorded. No ROM bytes, graphics, music, or game text beyond short UI labels are reproduced.
