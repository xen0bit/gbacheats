# The King of Fighters EX: Neo Blood (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Scope: **in-game / developer-intended cheats only** (passwords, button codes, hidden/debug menus, unlockables). No GameShark / CodeBreaker / Action Replay codes were sought or produced.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The King of Fighters EX: Neo Blood.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `KINGOFEXNEOB` (0xA0–0xAB) |
| Game code | `AKOE` (0xAC–0xAF) |
| Maker code | `BF` (0xB0–0xB1) |
| Fixed byte | `0x96` at 0xB2; main unit `0x00`, device `0x00`; version `0x00`; complement `0x2A`; header checksum `0x0000` |
| Entry word | `0xEA00002E` at 0x00 → stock GBA crt0 at 0x080000C0 (no scene cracktro / appended trainer) |
| `file(1)` | `Game Boy Advance ROM image: "KINGOFEXNEOB" (AKOEBF, Rev.00)` |
| MD5 | `1266f7f9d73252d70b25ebfe966c9a2b` |
| SHA-1 | `06a42bba1c892f77c7d12381fbf243fb294363cc` |
| SHA-256 | `4e5f75f98b3a5c617be9f61bc0b359a190d3f37c17500b13db41570223afa643` |
| Save hardware | EEPROM (512-byte `.sav`; `EEPROM_V122` string at 0x7FC604) |

This is the `AKOE` US/EU SKU. All addresses are valid for this exact hash only. The report was produced independently of the sibling EX2 analysis; the two ROMs share an engine family but have different text banks, state addresses and screen layouts.

## 2. Executive summary

**Bounded negative (high confidence): no player-usable code system was found in this ROM.** There is no password entry screen, no password validator/table, no button-code sequence validator, and no reachable hidden debug menu. The game does contain an ordinary **save-data unlockable system** (3rd party cheat index lists Iori Yagami, Geese Howard and the strikers K', Maxima, Vanessa and Yamazaki as unlockables) and 512-byte EEPROM records; those are earned by play, not typed.

Evidence in brief:

1. A full 8 MiB scan of **124 patterns (31 cheat-related keywords × 4 encodings: ASCII upper, ASCII lower, UTF-16LE, UTF-16BE)** returned **six benign hits only** — `STRIKER`, `OPTION`, `RECORD`, `RESET`, `EXIT`, `CONTINUE`, all option-menu labels. No `PASSWORD`, `CHEAT`, `CODE`, `SECRET`, `DEBUG`, `UNLOCK`, `SOUND TEST` or `SPECIAL CONTENT` string exists in any checked encoding (§6b).
2. Every reachable screen was walked in mGBA with screenshots and savestate RAM evidence (§3, §6b): 14 distinct screens including the title, four ranking categories, the 8-entry mode select, the 2-player dialog, the 7-row GAME OPTION screen, the 32-slot character select and a battle. **None offers a code-entry affordance.** Option fields are ordinary bounded settings (difficulty 5 values, play time, striker count, button config).
3. The only literal reference to `KEYINPUT` (`0x04000130`) in the entire 8 MiB is the one at **0x080239D8**, inside one input manager at **0x08023980** that computes `pressed = (~KEYINPUT & 0x3FF) & ~old`, tracks a key-repeat counter, and writes `held`/`pressed`/`prev` fields. It has 103 BL callers; none of the inspected callers maintains a *sequence index* or compares a run of past presses. Two input structures live at IWRAM `0x03000000` with a 528-byte stride (initialiser `0x08023A10`, sole caller `0x080053DC`).
4. A scan for contiguous button-mask tables found **919 candidate runs of ≥5 mask values**; the top candidates inspected (0x424AE, 0x51FB00–0x51FFC0, 0x277848, 0x51FD94 …) are animation/AI script data and graphics, not code sequences. No L+R / L+R+Start debug-gate literal appears in code: `0x030C` has 0 occurrences below 0x60000, `0x030F` has 2 (only one code xref, `0x0802BABC`, which is a data bitmask compare, not a keypad test).
5. Undocumented combinations pressed at the title and at character select (Konami code, L+R+A+B+Start, L+R+Start, Select+Start) produced only ordinary cursor movement / navigation — no hidden screen (§6b).

Because no code system exists, §0.2's "mint a novel code" deliverable is **not applicable**; the bounded negative is delivered with explicit counts instead (§6b).

## 3. How to reproduce

- Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`), `SDL_AUDIODRIVER=dummy`, own `Xvfb :317` + openbox, `mgba -3 <rom>`.
- Keymap (verified by menu navigation): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows. Hold 100–300 ms; a full key-release cycle is needed after loading a savestate.
- Boot path (attract loops if Start is not pressed): MMY/Marvelous splash → "Officially Licensed by SNK" splash → title "THE KING OF FIGHTERS EX NeoBlood / PRESS START / ©MMY 2001 ©SNK Licensed by SNK / DEVELOPED BY ARTOON" → demo match → rankings → title. Repeated Start (`Return`) presses reach `SELECT MODE`.
- `SELECT MODE` (8 entries, 2 columns × 4 rows): TEAM PLAY, SINGLE PLAY, ENDLESS SURVIVAL, PRACTICE | TEAM BATTLE, SINGLE BATTLE, SURVIVAL TIME ATTACK, OPTION. Right-column entries prompt a `2-PLAYER MODE  YES / NO` dialog (link play), not an unlock gate.
- `GAME OPTION` rows: BUTTON CONFIG (4 BUTTONS / 3 BUTTONS), DIFFICULTY (BEGINNER, EASY, NORMAL, HARD, VERY HARD — 5 values), PLAY TIME (30/60/…), STRIKER (3, 4, 5, …), RECORD, RESET, EXIT.
- `SELECT CHARACTER`: two 4×4 portrait grids plus a yellow `?` slot between them. 32 selectable portraits; a blue highlight marks the current pick.
- 512-byte EEPROM save: header `00 30 30 30 32 46 4F 4B` (`\0 0002FOK`), checksum/ID bytes at 0x0C–0x0F, option/unlock area through 0x4F (bytes 0x4A/0x4B observed to change between boots: `03 11` vs `02 05`), default ranking data from 0x50, `FF` filler from 0x1C0.

## 4. Address map

| Address (ROM unless noted) | Meaning | Evidence |
|---|---|---|
| `0x00000000` | Entry branch `0xEA00002E` → crt0 `0x080000C0` | Observed (header bytes) |
| `0x080239D8` | Sole literal `0x04000130` (KEYINPUT) in 8 MiB | Derived (literal scan) |
| `0x08023980` | Input manager: reads KEYINPUT, `bics` with `0x03FF`, computes held/pressed, key-repeat counter capped at 16–19 | Derived (Thumb disasm) |
| `0x08023A10` | Input-structure initialiser (2 structures, 528-byte stride) | Derived |
| `0x08023A64` | Input helper, 9 BL callers | Derived |
| `0x080053DC` | Sole BL caller of `0x08023A10` | Derived |
| `0x03000000`, `0x03000210` (RAM) | Two per-player input structures (528 bytes each) | Derived |
| `0x02000A54`, `0x02000A8C` (RAM) | EWRAM words that change when the character-select cursor moves (`0x0B→0x06`, `0x0EBB→0x001D`) | Observed (savestate diff) |
| `0x0801FAED` | PC captured in the character-select savestate (Thumb) | Observed |
| `0x0801FB10`, `0x0801FC60` | Nearby scene handlers; check masks `0x09` (Start\|A), `0x02` (B), `0x40`/`0x80` (Up/Down) | Derived |
| `0x08051A58`–`0x08051B60` | Plain-ASCII option text bank (`EXIT`, `RESET`, `RECORD`, `STRIKER`, `PLAY TIME`, `VERY HARD`, `HARD`, `NORMAL`, `EASY`, `BEGINNER`, `DIFFICULTY`, `4 BUTTONS`, `3 BUTTONS`, `BUTTON CONFIG`, `GAME OPTION`) | Observed |
| `0x08050C54` | `CONTINUE` string | Observed |
| `0x08042518` | `KOF2000` orphan string (engine leftover; not a selectable mode) | Observed |
| `0x07FC604` | `EEPROM_V122` SDK string | Observed |
| `0x0E000000` / `.sav` | 512-byte EEPROM (see §3) | Observed |

Savestate layout used (mGBA `.ss1` = PNG with a zlib `gbAs` chunk; 397,312 raw bytes): header/CPU `0x00000`, VRAM `0x01000`, IWRAM `0x19000` (maps to `0x03000000`), EWRAM `0x21000` (maps to `0x02000000`). The Thumb PC is at raw offset `0x58` (character-select state: `0x0801FAED`).

## 5. Algorithm

**No validator exists to reverse.** The input path is a per-frame edge detector plus key-repeat timer:

```
held    = ~KEYINPUT(0x04000130) & 0x3FF          @ 0x08023984..0x0802398E
pressed = held & ~old                            @ 0x080239A0..0x080239A4
if (held != 0) { if (timer == 0 || timer == held) ...; index++ ; clamp 16..19 }
prev = old; old = held; pressed_out = pressed    @ 0x080239F0..0x080239F6
```

Register fields of the input struct: `+0x00` held, `+0x02` pressed this frame, `+0x04` repeat candidate, `+0x06` previous held, `+0x08` counter, `+0x0A` previous-old. Nothing accumulates a *sequence* of presses; there is no `progress` index and no comparison against a stored button sequence. Screen handlers consume `pressed` one or two bits at a time (`0x09`, `0x02`, `0x40`, `0x80`).

The unlockables are a save-bit design (guide §16.18 pattern): unlock flags in EEPROM are set by play outcomes, then tested by the character/striker selection code. No controller-input path that sets them was found.

## 6. Tables

**Mode select (enumerated, 8/8):** TEAM PLAY, SINGLE PLAY, ENDLESS SURVIVAL, PRACTICE, TEAM BATTLE, SINGLE BATTLE, SURVIVAL TIME ATTACK, OPTION.

**GAME OPTION (enumerated, 7/7):** BUTTON CONFIG (4/3 buttons), DIFFICULTY (5 values), PLAY TIME, STRIKER, RECORD, RESET, EXIT.

**Ranking categories (enumerated, 5/5):** MY SCORE (TEAM), MY SCORE (GAME), SURVIVAL ENDLESS, SURVIVAL TIME ATTACK, CHARACTER DATA (per-character victory rate; observed names KYO, MOE, BENIMARU, TERRY, ANDY — rendered from non-ASCII tile indices). Default `NAME` field is `MMY` in every row.

**Character select:** 32 portraits (2 grids × 16) plus one `?` slot. Character names are *not* stored as ASCII in any of the four checked encodings (§6b) — they are tile-index/pre-rendered text.

**Joypad masks (active-high GBA standard):** A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.

**Unlockables (external source, not verified in-game):** 3rd party cheat index lists Iori Yagami and Geese Howard as unlockable fighters, plus K', Maxima, Vanessa and Ryuji Yamazaki as unlockable strikers.

## 6b. Enumeration

This is a **no-code-system** engagement, so the §0.2 deliverables are stated as a bounded negative with counts.

**Search space actually covered**

| Search | Space | Result |
|---|---|---|
| Multi-encoding keyword scan | 8,388,608 bytes × **124 patterns** (31 keywords × {ASCII-upper, ASCII-lower, UTF-16LE, UTF-16BE}) | **6 benign hits**: `STRIKER` (0x51A94), `OPTION` (0x51B5D), `RECORD` (0x51A68), `RESET` (0x51A60), `EXIT` (0x51A58), `CONTINUE` (0x50C54). Zero `PASSWORD`/`CHEAT`/`CODE`/`DEBUG`/`SECRET`/`UNLOCK`/`SOUND TEST`/`SPECIAL CONTENT` hits. |
| `strings -t x -n 5` | 30,982 strings | All long readable strings are option labels or SDK strings (`EEPROM_V122`, `_sbrk: Heap and stack collision`); the rest is code/data noise. |
| KEYINPUT literal scan | All 8 MiB, 4-byte `0x04000130` | **1** occurrence (0x080239D8). Thumb PC-relative scan for the same literal: **0** additional. |
| Input manager call graph | BL scan for target `0x08023980` | **103** callers; representative screens disassembled, none keeps a sequence/press-history index. Helper `0x08023A64` has 9 callers. |
| Button-mask table scan | All 8 MiB, u16 and u8 runs of masks from {1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200} | **919** runs of ≥5 consecutive mask values; the longest/top ones inspected (0x424AE `B A B A B A B`; 0x51FB00–0x51FFC0; 0x277848; 0x51FD94) are animation/AI script or graphics data. No table of expected presses feeding a validator. |
| Debug-gate literal scan | 4-byte literals `0x0300`, `0x030C`, `0x030F` below 0x60000 | `0x0300`: 62 (only one code LDR, 0x0802BABC → data bitmask compare at 0x0802BACC); `0x030C`: **0**; `0x030F`: **2** (only code xref 0x0802BABC, again a data compare). No L+R / L+R+Start keypad gate. |
| Screen walk | 14 distinct screens observed (§3) | No password field, keypad, "enter code" prompt, or hidden menu entry on any screen. |
| Undocumented combos in emulator | Konami code (↑↑↓↓←→←→BA), L+R+A+B+Start, L+R+Start, Select+Start at title/character select | Cursor movement / ordinary navigation only; no hidden character, screen or flag observed. |

**Bounds proven:** option fields are closed sets enumerated by cycling each to wrap (difficulty 5 values wraps VERY HARD→BEGINNER; striker count increments 3→4→5; button config 4/3). Locked-looking right-column modes resolve to a YES/NO 2-player dialog, not a gate. The 2-player YES/NO dialog was tested both ways (NO returns to menu; YES is link play).

**Why the "mint a novel code" deliverable is not applicable:** there is no validator, table or input surface to mint a value for. Per guide §0.2, a bounded negative is the correct deliverable here.

**Evidence-type summary for the negative:** screen enumeration and button-combo results are **Observed**; keyword/mask/literal counts are **Derived** from byte scans; the statement "unlockables are gameplay-gated" is **Inferred** from the external unlockable list and the absence of an input path, not proven by playing a full clear.

## 7. Validation evidence

- **Observed:** mGBA screenshots of all 14 screens (`s_*.png`, `att_*.png`, `boot_*.png` in `/tmp/kofex1`), including the mode select, option values, 2-player dialog, character select, five ranking screens and a live battle.
- **Observed:** savestate diff between `ss_charselect.ss1` (cursor on Kyo) and `ss_charsel_left.ss1` (cursor on Moe) changed EWRAM words at `0x02000A54` (0x0B→0x06) and `0x02000A8C` (0x0EBB→0x001D) — RAM evidence that the character cursor is tracked in EWRAM.
- **Derived:** the input manager and its sole KEYINPUT literal; the 103-call BL graph; the 124-pattern keyword count; the 919 mask-run count.
- **Inferred:** the unlockables are save-bit gated; the character-name text is tile/pre-rendered rather than ASCII (names never appear in any checked encoding despite being visibly rendered).

## 8. Unknowns

- The tile-index/pre-rendered text bank for character names and story text was **not fully decoded**; therefore the negative for hidden messages in *that particular encoding* is not proven. The negative rests on the ASCII/UTF-16 scan plus the full screen walk (no code-entry UI was visible).
- The EEPROM flag semantics (which bit unlocks Iori/Geese/K'/Maxima/Vanessa/Yamazaki) were not isolated; 0x4A/0x4B were observed to change but their bit meanings were not derived.
- The yellow `?` slot at character select was not exhaustively tested with every cursor position; it behaved as an ordinary selection slot during the combos tried.
- Web reconnaissance was blocked: 3rd party cheat indexes direct, 3rd party cheat indexes, Google, Bing, DuckDuckGo, Mojeek and Brave either returned 403/CAPTCHA or no results through this environment; only 3rd party cheat indexes were reachable. All "published code" claims are therefore unverified for this ROM.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep -aob` for Phase 0/1.
- Python 3 + `capstone` for literal/BL/mask scans (`scan_input.py` and inline scripts in `/tmp/kofex1`).
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for disassembly.
- `ss.py` (written for this engagement): decodes the `gbAs` zlib chunk of mGBA `.ss1` files into a 397,312-byte raw state for RAM diffing (guide §16.13).
- `ui.py` (written for this engagement): xdotool key/screenshot helper for `DISPLAY=:317`.
- mGBA 0.10.5 under `Xvfb :317` + openbox, `SDL_AUDIODRIVER=dummy`; F1/Shift+F1 savestates; `-t` state loading.

Legal note: no ROM, save data or copyrighted graphics/music are redistributed here; only addresses, hashes, counts and conclusions are published.
