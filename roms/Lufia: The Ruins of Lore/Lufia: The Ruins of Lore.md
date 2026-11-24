# Lufia: The Ruins of Lore (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Lufia: The Ruins of Lore.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `LUFIA` |
| Game code | `AGDE` (US) |
| Maker code | `EB` (Atlus) |
| Version | `0x00` |
| Fixed byte `0xB2` | `0x96` (present) |
| Entry branch | `0xEA00002E` (stock `0x080000C0` crt0) |
| Header checksum | `0x0000`; complement `0x48` (matches 3rd party cheat indexes US CRC32 `DE5FFCBC`) |
| MD5 | `22b31aa8f66e7c6528fd4903a09f030f` |
| SHA-1 | `a2b7e80a6c7d586ebeec77c8a2c2545fe27e0592` |
| SHA-256 | `f58cf030045d4049f5fef15032d10a691322d599ea8239d7b49539bfe53657ab` |

**Embedded-header scan:** scanning the whole image for the 156-byte Nintendo logo (`24 ff ae 51 ...`) yields exactly **one** hit, at file offset `0x0`. There is no multiboot/2-in-1 sub-image and no appended trainer; the file is a single unmodified retail US image.

## 2. Executive summary

There is **no controller-reachable cheat system** in this GBA SKU: no password screen, no button-code sequence, and no unlockable/debug menu that can be entered with the GBA controls. Every published "cheat" for the game is either a GameShark/CodeBreaker **memory-edit code** (out of scope for this engagement) or an in-game **glitch/exploit** (Infinite Nectar, Sacrifice self-heal, Blue Tea arbitrage), not a code the game validates.

The ROM does contain a substantial set of **developer debug menus** (KANDA / AJIKI / SAITO / YOKOTA / IMAI tasks): a six-entry task selector plus battle-BG/enemy-group pickers, a character/sprite viewer, a sound test, area changers, a teleporter, save-data editors, job selectors, shop/collector tools and communication test screens. Their existence and full contents are proven statically (strings + task table + function pointers, cross-checked against 3rd party cheat indexes). They are **hard-gated**: the only documented activation is via CodeBreaker RAM patches writing `0x02001A2C`/`0x0300597E` (menu 1) and the handler slot `0x03005978`/`0x0300597A` (menu 2). No ROM code path writes those gate values from controller input — the gate is a developer-only external hook, not an in-game unlock. This is a **gated feature** (guide §16.3, type 4) whose only writer is an external debugger, so no controller sequence can reach it.

The negative is bounded: all controller-reachable screens were walked with screenshots, the entire string table and all font/alphabet tables were searched and classified, and every published code was verified to be a memory edit or a gameplay glitch rather than a validated code.

## 3. How to reproduce

- Emulator: `mgba` 0.10.x, Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, scaled `3×`.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys.
- Boot path: Start ×6–8 through Taito/Atlus logos and the prologue text → title menu (**New Game / Continue / Link**). New Game + A-mash through the opening dialogue → field. Select opens the field menu; Start opens Field Record (quick-save).
- Screens walked (screenshots kept in `/tmp/lufia/`): `z1_crop.png` (title), `w_field_crop.png` / `e2_crop.png` (field), `w_menu_crop.png` (field menu — renders as tile-indexed glyphs), `g1_000.png` / `y_clear_crop.png` (intro/dialogue), `w_record` capture (Field Record).
- Debug-menu activation attempts (all out-of-scope memory edits, used only as probes, none delivered as a "code"):
  - mGBA savestate `gbAs` chunk edits at `0x03005978`, `0x0300597E`, `0x02001A2C`;
  - mGBA GDB stub `w/4` (port 2345 was held by another agent, so a private `-d` pty debugger was used instead);
  - mGBA `-c` cheat files in both mGBA formats (`# name` and libretro `cheatN_code`) with CodeBreaker lines `8300597E FF00`, `83001A2C 0020`, `83005978 FDE5`, `8300597A 0805` (a 3rd party cheat index's published values).
  - Result: writing the handler slot produced a soft reset / intro replay (the debug task is invoked but tears down normal game state); a stable rendered debug menu was not obtained in the retail boot state. This does not affect the finding, because these are external memory edits and are out of scope.

## 4. Address map

File offset ↔ ROM address is `0x08000000 + offset`.

| ROM address | File offset | Meaning |
|---|---|---|
| `0x080D43C8` | `0xD43C8` | Debug task-name table: 6 records (see §6). Function pointers stored as `0x08xxxxx1` (Thumb bit). |
| `0x080D43E8` | `0xD43E8` | `KANDA - TASK` label; handler `0x0807CBB1`. |
| `0x080D4408` | `0xD4408` | `AJIKI - TASK`; handler `0x08002A2B`. |
| `0x080D4428` | `0xD4428` | `SAITO - TASK`; handler `0x0802F8CD`. |
| `0x080D4458` | `0xD4458` | `YOKOTA- TASK`; handler `0x0804BAD9`. |
| `0x080D4478` | `0xD4478` | `IMAI  - TASK`; handler `0x0805F7F9`. |
| `0x080D4494` | `0xD4494` | sixth entry; handler `0x0808CE51`. |
| `0x080D44D8` | `0xD44D8` | `DebugTaskMenuSelect` string. |
| `0x080D44F0` | `0xD44F0` | Debug menu item-name pointer table (`0x080B0855`, `0x080B08C5`, …). |
| `0x080B02C0` | `0xB02C0` | `DebugTaskMenuInit` — builds the 6-row selector. |
| `0x080B031C` | `0xB031C` | `DebugTaskMenuSelect` — input/dispatch (Up/Down/A), reads index at `0x0203EFF4`. |
| `0x080B01E8` | `0xB01E8` | Secondary debug launcher (`ImQsave/ImEntry/...` 6-row menu). |
| `0x03005978` | RAM | Debug handler slot (normal value `0x0807CC79`), reached as `0x03004D70 + 0xC08`. |
| `0x03004D70` | RAM IWRAM | Base struct for the above slots (346 literal references in ROM). |
| `0x0203EFF4` | RAM EWRAM | Selected debug-task index (0–5), written by `0x080B02BE`. |
| `0x02001A2C`, `0x0300597E` | RAM | Published CodeBreaker gate bytes for menu 1 (no in-ROM controller writer found). |
| `0x080C6DE0`–`0x080C6F00` | `0xC6DE0`– | KANDA debug text (ASCII + Shift-JIS). |
| `0x080CE030`–`0x080CE240` | `0xCE030`– | YOKOTA debug text and `YOKOTA Debug ShuffleJobSelect`. |
| `0x080D0186`–`0x080D028C` | `0xD0186`– | IMAI debug text and `src/imai/DebugMenu_imai.c`. |
| `0x080D1CEC` | `0xD1CEC` | Font character set `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-?!:#*&%` — a **font glyph table**, not a code alphabet. |
| `0x080C712C` | `0xC712C` | `0123456789` adjacent to battle text — digit glyphs, not a code table. |

## 5. Algorithm

The debug task dispatcher (`0x080B031C`, Thumb), reconstructed from disassembly:

```
idx = [0x0203EFF4]                       # 0..5
if (KEYINPUT & 0x40) /*Up*/:   idx = (idx - 1) mod 6
if (KEYINPUT & 0x80) /*Down*/: idx = (idx + 1) mod 6
if (KEYINPUT & 0x01) /*A*/:    call task_start( task_table[idx] )   # via 0x080BA9BC
[0x0203EFF4] = idx
render label = task_table[idx].name      # 36-byte stride
```

Task table stride is 36 bytes (`0x24`), six entries; the names at `0x080D43C8` are `NORMAL START`, `KANDA - TASK`, `AJIKI - TASK`, `SAITO - TASK`, `YOKOTA- TASK`, `IMAI  - TASK`. This is the entire menu space: there is no hidden seventh task (the sixth pointer at `0x080D4494` is `0x0808CE51`, and the loop bound is `cmp r4,#5; ble` at `0x080B02B6`).

The gate is not an algorithm in the game: `0x02001A2C = 0x20` and `0x0300597E = 0xFF00` are developer flags written only by external patches. No `str`/`strh` in the ROM targets `0x02001A2C` or `0x0300597E` from a controller path (they are reached, if at all, via the base `0x03004D70` + offset with values the normal UI never produces).

## 6. Tables

**Debug task table (ROM `0x080D43C8`, 6 × 36 bytes):**

| Index | Label | Handler |
|---:|---|---|
| 0 | NORMAL START | (stock boot path) |
| 1 | KANDA - TASK | `0x0807CBB1` |
| 2 | AJIKI - TASK | `0x08002A2B` |
| 3 | SAITO - TASK | `0x0802F8CD` |
| 4 | YOKOTA- TASK | `0x0804BAD9` |
| 5 | IMAI  - TASK | `0x0805F7F9` |

**Decoded debug menu contents (Shift-JIS / cp932; Japanese names translated):**

- KANDA DebugMenuSelect: `SELECT BATTLE BG`, `SELECT ENEMY GROUP`, `OBJECT CHARA VIEWER`, アニメばんごう (animation no.), パターンばんごう (pattern no.), ＢＧＭばんごう (BGM no.), せんとうＢＧ (battle BG), `Return Menu`, plus `SX %d SY %d EX %d EY %d`, `MAX FRAME %d`.
- YOKOTA DebugMenuSelect: 13 job selectors — むしょく/そうりょ/だいそうりょ/けんし(けん)/けんごう(けん)/けんし(こぶし)/けんごう(こぶし)/とうぞく/だいとうぞく/まじゅつし/ようじゅつし/くすりし — plus `YOKOTA Debug ShuffleJobSelect` and `GOLD`, `TIME`, `Options`, `Monsters`, `Change`, `Skills`, `Equip`, `Special`, `Stat`.
- Imai DebugMenuSelect: `ImQsave <DEBUG>`, `ImEntry <DEBUG>`, `ImHeroColor <DEBUG>`, `ImTemple <DEBUG>`, `ImShop <DEBUG>`, `ImCollecter <DEBUG>`.
- YOKOTA task text bank (`0x080CDE40`+): キャンプ (camp), ＯＰ(バンパー), ＯＰ(データロード), ＢＧたおしこみ, ルビウスかいてんばん, セーブデータINIT, セーブデータカプモン１SET, セーブデータカプモン２SET, セーブデータロード, シャッフルつうしん, シャッフルキャンプ, つうしんテスト, つうしんロビー, `GAME OVER`, `Event****`.
- 3rd party cheat indexes cross-reference (menu 1): Player Info, Levels Editor, Items Editor, Key Items Editor, Flags Editor, Skills Editor, Eldin's Skills, Teleporter, Area Viewer, Area Viewer Away. (menu 2): battle selector (BG + enemy set, A to start), sprite viewer, sound test, three area-changing tools, cinematic viewer, teleporter, debug shops.
- Published CodeBreaker activation values verified as real RAM addresses in this build: `0x0300597E` / `0x02001A2C` (menu 1); `0x03005978` / `0x0300597A` (menu 2). Both are external writes; their normal runtime values (`0xFC00`, `0x0807CC79`) are not the activation values. GameShark/CodeBreaker listings use encrypted addresses (e.g. `8203D1BE`, `4203E114`) that do not appear as ROM literals — they target EWRAM save data, confirming they are memory edits, not validated codes.

## 6b. Enumeration

This engagement is a **negative result**: there is no validated code space to enumerate. The searched spaces and their sizes are stated so the absence is a bounded statement:

| Space searched | Count / result |
|---|---|
| All `strings -t x -n 4` records | 92,679 lines |
| `password` | **0** hits |
| `enter code` / `invalid` / `level select` | **0 / 0 / 0** hits |
| `cheat` | 2 hits — both in dialogue ("You trying to cheat me, here?") |
| `secret` | 11 hits — all dialogue / item descriptions |
| `unlock` | 3 hits — all story dialogue ("unlock the seal") |
| `debug` | 14 hits — all developer menu/task strings (§6) |
| Literal password code tables (`strcmp` targets) | 0 found; no `strcmp` compares a controller-entered buffer |
| Code-entry alphabets | 5 candidate ASCII alphabets examined — all are **font glyph tables** (e.g. `0x080D1CEC`), not validators |
| Button-mask code sequences | 0 tables; no key-history ring/comparison; controller writes only the debug-task index `0x0203EFF4` (0–5) |
| Debug task menu entries | exactly **6** (loop bound `cmp #5; ble` at `0x080B02B6`), all listed in §6 |
| Published passwords / button codes / in-game unlock codes | **0** on 3rd party cheat indexes, or the walkthroughs |
| Published GameShark/CodeBreaker memory-edit codes | many (out of scope) — verified as RAM writes, not game-validated inputs |
| Published gameplay glitches | Infinite Nectar, Sacrifice self-heal, Blue Tea resale, 20,100 EXP boss — out of scope (no input code) |

**Novel code / in-game proof:** not applicable — no code system exists, so there is no validator to mint against and no bounds to prove by rejection. The equivalent negative proof is (a) every controller-reachable screen walked, (b) every debug-menu entry enumerated from the task table and text banks, and (c) the gate-provider analysis showing the debug screens' only writers are external memory edits (§5). The one dynamic probe that reached a debug handler produced a soft reset/intro replay, consistent with an external developer hook rather than an in-game menu — recorded as **Observed** in §7.

**Published codes tested:** the two 3rd party cheat indexes CodeBreaker gate patterns were applied with mGBA savestate edits and with `-c` cheat files in both mGBA formats; the 3rd party cheat indexes glitches are gameplay exploits, not entered codes, so they have no literal in the ROM to test. No published password or button code exists to test.

## 7. Validation evidence

- **Observed:** title menu, field, field menu (tile-indexed/garbled glyphs), Field Record, intro/dialogue screens via mGBA screenshots on `:318`; debug-handler write at `0x03005978` caused soft reset + intro replay; mGBA savestate `gbAs` dumps read/wrote the gate RAM bytes (`0x03005978`, `0x02001A2C`) and confirmed their normal values (`0x0807CC79`, `0x0000`).
- **Derived:** six-entry debug task table and its 36-byte stride, Up/Down/A dispatch, handler addresses, and all Shift-JIS menu labels — from `objdump -M force-thumb` disassembly and literal-pointer scans, corroborated by 3rd party cheat indexes.
- **Inferred:** that no in-game event ever sets the gate bytes (no controller-writer found in static analysis); the exact reason the patched debug handler resets the game (it expects a different game-state initialization) was not isolated. The natural battle screen was not reached in the scripted walking route (the opening cutscene dialogue consumed the scripted inputs); no published code pertains to it, so this does not affect the finding. No prompt-injection content was encountered in fetched pages; fetched 3rd party cheat index text was treated strictly as data.

## 8. Unknowns

- The exact runtime code path (if any) that writes the debug gate bytes `0x02001A2C`/`0x0300597E` was not isolated; static analysis found no controller-driven writer, which is the basis for the "gated, external-only" classification.
- A stable rendering of the debug menus in emulation was not achieved; their contents are proven statically and via 3rd party cheat indexes, not by an in-game screenshot. This is acceptable because activation requires an out-of-scope memory edit.
- The battle screen itself was not entered in the scripted route; no code system is associated with it.

## 9. Tooling

- `strings -t x`, `grep`, `xxd`, `python3` (Capstone 5.0.7 / Keystone for literal & BL scans), `arm-none-eabi-objdump -M force-thumb`.
- Helper scripts in `/tmp/lufia/`: `an.py` (literal/BL/Thumb-LDR scanners, hex dump), `ss.py` (mGBA `.ss1` `gbAs` zlib chunk read/write; IWRAM at `0x19000`, EWRAM at `0x21000`), `dbg.py` (pty driver for mGBA `-d` CLI debugger: `r/4`, `w/4`, `w/r`, `status`), `key.py` (XTEST key injection), `gdbint.py` (pexpect GDB stub helper).
- Emulator: `mgba` 0.10.x under `Xvfb :318` with `openbox`, `SDL_AUDIODRIVER=dummy`; screenshots via `scrot` + `convert` crop.
- Web cross-check: 3rd party cheat index cheats/walkthrough/boards, 3rd party cheat indexes.
- No ROM or copyrighted graphics were redistributed; only addresses, hashes, and translated menu labels are published here.
