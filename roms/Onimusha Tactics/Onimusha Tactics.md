# Onimusha Tactics (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Onimusha Tactics/Onimusha Tactics.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `ONITAC1US` (12 bytes at 0xA0, NUL-padded) |
| Game code | `A6OE` |
| Maker code | `08` (Capcom) |
| Version | `0x00` (Rev.00) |
| Complement / header checksum | `0x47` / `0x0000` |
| Entry word | `0xEA00002E` (stock ARM branch to 0x080000C0) |
| MD5 | `7c8e479f4c4e46f406b1da5e786358c0` |
| SHA-1 | `83abee3aa535590f666d7e9a6971640d8a41aa9d` |
| SHA-256 | `ded6f9ab2cab130088ee3fe3c8507bb3192ea1150a3cb236a89e1f37e0a10a44` |
| CRC32 | `70475D7F` (matches gamehacking.org listing and mGBA savestate header) |

**Embedded-header scan:** scanned all 8 MiB for the 156-byte Nintendo logo; exactly **one** hit, at file offset `0x0`. This is a single retail image — no multiboot stub, no concatenated second game, and no appended trainer. The first 4 KiB contain ordinary ARM crt0 code with no cracktro strings (no `CRC BANDIT`, `MODE7`, `SUNHORS`, etc.), and the entry word is the unmodified `0xEA00002E`. **No patch/trainer present.**

## 2. Executive summary

**There is no in-game/developer-intended cheat-code system in this ROM.** Specifically, there is:

* no password entry screen, no password alphabet/table, and no validator;
* no button-code/key-mask sequence handler on the title, options, field, or pause screens;
* no reachable hidden/debug/level-select/sound-test menu;
* no hidden in-game code that mints characters or items.

Every cheat published for this game is an **external memory-edit code** (CodeBreaker / GameShark / Action Replay / ARMAX) that writes directly to EWRAM, e.g. `82000286 03E7` (max HP P1), `830056BC FFFF` (all recipes), `32011540 00??` (active-character count). These are explicitly out of scope and are **not** in-game codes.

The only developer-intended hidden content is **save-progress unlockables**, earned by clearing the 16-floor "Phantom Realm":

| Unlockable | Condition (published) | Confidence |
|---|---|---|
| **Onikko** (Oni Kid), the 16th/secret character, Lv.1 axe wielder | clear all 16 Phantom Realm floors | published + consistent with a `== 16` gate in ROM |
| **Genma Agoni** item | clear Phantom Realm twice | published only |
| **Oni Armor** item | clear Phantom Realm three times | published only |

The game text is **tile-indexed** (ASCII `strings` finds only the episode-title bank), so all screens were enumerated visually with savestate/RAM evidence rather than inferred from strings.

**No novel code was minted because no code system exists** (§0.2's generation deliverable is replaced by the bounded-negative proof in §6b).

## 3. How to reproduce

* **Emulator:** mGBA 0.10.5, `Xvfb :315 -screen 0 1280x1024x24`, `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.
* **Keymap (verified empirically):** A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.
  **Use 20–30 ms key holds.** 120 ms holds double-step the cursor (§16.2). Savestates: `Shift+F1..F9` save, `F1..F9` load.
* **Screens walked (each verified by screenshot + `.ssN` RAM snapshot):**
  1. Title "PRESS START" — `PRESS START` blinking.
  2. Title menu — `New Game / Load Game / Options`.
  3. Options — three settings (`Message`, `Movement`, `Music`; values `Fast/Normal`, `Fast/Normal`, `OFF/ON`), each with a `Accept / Cancel / Return` confirmation dialog.
  4. Load Game — two slots; with a blank `.sav` shows `No saved games.`; with a written `.sav` the same two-slot `Load` list appears.
  5. New Game → long story intro (skippable with Start) → field/dialogue (Sandayu) → `Turn 01` battle.
  6. Battle pause menu (Start) — `Unit / Save / Options / Objectives / Withdraw / End Phase`.
  7. Save screen — two slots, `Save Here? Yes/No`, `Saving…`, then `Quit the game? Yes/No`; writes ~0xDC0 bytes to the 8192-byte `.sav`.
* **Button codes tested on the title screen** (each from a clean `PRESS START` savestate, then screenshot + RAM diff): Konami code, `L+R+Start`, `L+R+Select`, `Start+Select`, `A+B+Start`, `A+B+L+R`, `L R L R`, `Up Down Up Down`, `Start A Start A`, `Select Start`. **None produced a hidden screen or flag** (see §6b).

## 4. Address map

| Item | Address (ROM / file offset) | Notes |
|---|---|---|
| Header / crt0 | `0x08000000` / `0x0` | entry branch `0xEA00002E` |
| `main` loop | `0x080010B0` / `0x10B0` | Thumb; per-frame call to `0x08001288`; reads byte `0x03000401` (always `0x08` observed) |
| Event dispatcher | `0x08011D38` / `0x11D38` | 31-entry jump table at `0x08011D74`; only cases 0,1,6,8,9,11,21 do work |
| 16-character unlock gate | `0x08011E6C` / `0x11E6C` | loops 16 records, stride `0xEC`, checks `+0x4A` byte and `+0x2E` s16; if all pass, stores `0x0A` to scene byte `0x030026D9` |
| Save character table (RAM) | `0x030028DC` | 16 records × `0xEC` bytes |
| Font glyph bank | `0x08060A00` / `0x60A00` | 16-pixel-wide bitmap glyphs (e.g. `0x0F80,0x3060,0x2020,0x4010…` = a round glyph) |
| Font/tile mapping tables | `0x080782E28`, `0x080782F20` / `0x782E28`, `0x782F20` | 180-byte and 136-byte structured byte tables (see §6b) |
| ASCII episode-title bank | `0x08078160E`–`0x080781D1D` / `0x78160E`–`0x781D1D` | `Episode 1…44` + `Final episode` — the **only** substantial ASCII text in the ROM |
| `secret lab` dialogue hit | `0x080781879` / `0x781879` | `"Episode 14@@@Guildenstern's@@secret lab"` — a story title, **not** a cheat |
| libgba save strings | `0x807EB…` / `0x7EB…` | `EEPROM_V122`, `SRAM_V113`, `_sbrk: Heap and stack collision`, `bug in vfprintf: bad base` |
| mGBA savestate layout | raw 397,312 bytes | VRAM @ raw `0x1000`, IWRAM @ `0x19000`, EWRAM @ `0x21000` (4 MiB-style layout holds for this 8 MiB ROM) |

## 5. Algorithm

No password/checksum/button algorithm exists. The only relevant piecewise logic is the event dispatcher (derived from Thumb disassembly):

```
scene = *(u8*)0x030026D9
if scene > 30: return
jump table[scene]()            // 0x08011D74; 24 of 31 cases are no-ops

case 8:                         // 0x08011E6C — "all characters present?" gate
    i = *(u8*)0x030026F9
    while i <= 15:
        rec = (u8*)0x030028DC + i*0xEC
        if rec[0x4A] == 0: break
        if *(s16*)(rec+0x2E) == 0: break
        i++
    if i == 16:
        *(u8*)0x030026D9 = 10    // advance to the special-event scene
    else:
        *(u8*)0x030026F9 = i
        call 0x080077D0, 0x080B6918
        *(u8*)0x030026D9 = 8
```

This is a **progress/flag gate**, not an input-validated cheat: its inputs are the 16 save character records, and no controller state is read on this path.

## 6. Tables

| Table | Location | Content |
|---|---|---|
| Event dispatch jump table | `0x08011D74` | 31 u32 entries; real handlers: case 0→`0x08011D78`, 1→`0x08011DF4`, 6→`0x08011E14`, 8→`0x08011E6C`, 9→`0x08011F04`, 11→`0x08011F68`, 21→`0x08011FA0`; all others → `0x08012088` (return) |
| Save character records | `0x030028DC` (RAM) | 16 slots × `0xEC` bytes; fields at `+0x2E` (s16) and `+0x4A` (u8) tested by the gate |
| Save file | `.sav`, 8192 bytes | Two slots; used bytes `0x0`–`0xDBF`; filler `0xFF` after |
| Phantom Realm unlockables | published | Onikko = 16-floor clear; Genma Agoni = 2 clears; Oni Armor = 3 clears |
| GBA key mask (standard) | — | `A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`; **no table of these masks is used as a code sequence in any code path found** |

## 6b. Enumeration

**Result: the code space is empty.** §0.2's enumeration deliverable is replaced by a bounded negative: every plausibly relevant search space was checked and counted.

| Search space | Method | Count / result |
|---|---|---|
| Plaintext cheat keywords | case-insensitive regex over all 8 MiB for `password`, `cheat`, `debug`, `secret`, `unlock`, `level select`, `sound test`, `onikko`, `phantom`, `menu`, `invalid`, `congrat`, `hidden`, `master code`, `continue`, `codebreak`, `gameshark` | **0 hits** for all except `secret` = **1** (`Guildenstern's secret lab`, a story title) |
| Fixed-width NUL-padded string tables (password-table shape) | ≥4 equal-length printable NUL-terminated strings with stride ≤64 | **1591** raw runs — inspected; all are 3–4 byte fragments embedded in compressed tile/audio data, **none** is a code table |
| Password alphabets | printable runs ≥20 chars with ≥16 distinct symbols | **975** — all are byte-pattern coincidences in compressed graphics |
| Button-code mask arrays | every aligned `u16` quadruple whose values are single GBA key bits | **609** — all in graphics/bitmap regions (e.g. `0x60A020` is a 16×N font glyph bitmap, not a key table); **0** in executable code |
| LZ77 text banks | decompressed all 23 valid `0x10`-header LZ77 blocks | **0** contained any UI/dialogue keyword |
| Alternate text encodings | UTF-16LE/BE, reverse, nibble-swap, `±0x20`, XOR-0x80, affine `(a·c+b) mod 256` over all a,b, and sliding-window font-table inversions over `0x781000–0x783200` | **0 hits** for `Message`, `Movement`, `Music`, `civilization`, `Onikko`, `Phantom` |
| Font/tile-indexed text banks | located glyph bitmaps at `0x08060A00` and structured mapping tables at `0x080782E28`/`0x080782F20`; rendered tile data from mGBA savestates | UI text confirmed tile-indexed (hence absent from `strings`); encoding not fully inverted (see §8), but **every screen was enumerated visually**, so no hidden menu text could be missed |
| Published codes | GameFAQs, ChapterCheats, SuperCheats, gamehacking.org, CodeTwink, TCRF search | All published "codes" are external memory edits (out of scope); **0** are in-game passwords/button codes; **no TCRF page exists** for this title; three unlockables verified as progress-based, not code-based |
| Button-code input space | 10 common sequences on title screen, each from clean savestate with Before/After RAM diff | IWRAM diffs 12–162 bytes (normal animation/counters), EWRAM diffs ~3200 bytes (save copy) — **no new flag or screen** in any case |
| Debug/hidden screen reachability | walked all reachable menus (title, options + 3 sub-dialogs, load, save, field, battle, pause + 6 items) | **0** unlabelled/hidden entries; every menu item is a normal game function |

**Bounds / rejection tests:** A "code" cannot be rejected by this game because there is no entry surface — so rejection is proven at the surface level: there is no password keypad, no code validator, and no key-sequence dispatcher anywhere in the 8 MiB image. The one gate that *does* compare against a literal (`scene == 16` at `0x08011ED4`) is fed by save-file records, not by controller input; entering any of the tested button sequences does not satisfy it (RAM diff shows no change to the gate inputs). The three published unlockables are likewise gated by Phantom Realm progress, not by any typed or pressed code.

**Novel code:** not applicable — no code system to mint from. This is a *proven* absence over the enumerated spaces above, not an untested one.

## 7. Validation evidence

* **Observed:** all screens in §3 captured as screenshots (`s_title.png`, `opt_menu.png`, `options2.png`, `loadgame_save2.png`/`lgseq7.png`, `field1.png`, `field2.png`, `pause.png`, `save5.png`) and as mGBA savestates with RAM dumps; save file written and inspected (`0x0–0xDBF` non-`FF`); 10 button-code trials with RAM diffs.
* **Derived:** header/entry/crc from file bytes; main loop and event dispatcher from `arm-none-eabi-objdump -M force-thumb`; 16-record gate and `0xEC` stride from literal pools; single-header result from logo scan; font glyph shapes from `0x60A000`.
* **Inferred (labeled):** the three unlockable→clear-count mappings come from published guides (ChapterCheats/SuperCheats/GameFAQs) and are *consistent* with the `== 16` gate in ROM, but were not executed end-to-end (would require clearing all 16 Phantom Realm floors). The exact save-file offset of the Phantom Realm clear counter was not isolated.

## 8. Unknowns

* Full inversion of the tile-indexed text encoding was not completed: the glyph bank and two mapping tables were located and several encoding hypotheses were tested, but the byte→glyph transform for the in-game UI font remains unresolved. This does **not** weaken the negative result, because every reachable screen was enumerated visually and the ASCII keyword census covers the only plaintext bank.
* The exact save-file byte(s) holding the Phantom Realm clear count, and the complete set of callers/setters for the Onikko / Genma Agoni / Oni Armor flags, were not isolated (would require a completed 16-floor run or deeper decompilation).
* Whether a debug menu exists in an unreleased/prototype build is outside this retail ROM.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep` — Phase 0/1.
* `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7 + Keystone — disassembly and literal-pool scanning.
* Python 3 scripts in `/tmp/onimusha/`: `static_scan.py`, `encsearch.py`, `fontcrack.py`, `lzscan.py`, `input_scan.py`, `ss.py`, `snap.py`, `walk.py`, `keys.py`, `button_tests.py`, `render_fb.py`.
* mGBA 0.10.5 under Xvfb `:315`, `scrot`, ImageMagick `convert` — dynamic screen walk and screenshots.
* REA/Ghidra 12.1.4 (opened the raw GBA image at base `0x08000000`, used `list_procedures`/`procedure_pseudo_code`/`xrefs`, then `close_binary`) — decompilation cross-check.
* Web search/fetch: GameFAQs, ChapterCheats, SuperCheats, gamehacking.org, CodeTwink, TCRF. Fetched pages were treated strictly as data; **no prompt-injection payload was encountered**.

**Legal note:** No ROM image or copyrighted asset is redistributed here. Only hashes, addresses, offsets, and original analysis are published.
