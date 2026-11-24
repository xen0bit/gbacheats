# GT Advance 3: Pro Concept Racing (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `GT Advance 3: Pro Concept Racing.gba` |
| Size | 8,388,608 bytes (0x00800000, 8 MiB) |
| Header title | `GT ADVANCE 3` |
| Game code | `A2GE78` |
| Maker code | `78` (THQ); developed by MTO Co., Ltd. |
| Version | 0x00 |
| Fixed byte 0x96 | present |
| Complement / checksum | 0xE3 / 0x0000 |
| Entry word | `0xEA00002E` → `0x080000C0` (stock) |
| MD5 | `e7951ea3e7f3e80e0a90573aeea5dd0b` |
| SHA-1 | `851d50f642d3d1fd0328f6e3a4ef54b8108f89fd` |
| SHA-256 | `d19d1905ca7b317adccaa1c6f3cd7e5d86346f17c2ebf559a3911ae2654842e6` |

**Phase 0 result:** stock retail image. A full-file scan for the 156-byte Nintendo logo
found exactly one GBA header, at file offset 0x0. No appended trainer, no second
image, no cracktro patch: the entry branch is the stock `b 0x080000C0`. Save memory
is 512-byte EEPROM (a fresh `.sav` was all `0xFF`).

## 2. Executive summary

**No developer-intended password, button code, or unlock code system was found in
this image, and none is reachable from any screen in the game.** The game's
unlockables (97 cars, 20 owned on a fresh save) are ordinary progress-gated
content; the `EXTRA` mode entry on the main menu is locked and ignores A/B/Start
entirely on a fresh save. The only text-entry surface found is a 3-character
driver initials field whose consumer is a display/save buffer, not a validator
(no comparison against any constant code table).

The ROM does contain a substantial **embedded debug/test subsystem** — ASCII
labels `DBG TOP MENU`, `LINK TOP MENU`, `TST3/4/5`, `RACE`, `CAR`, `END`, and a
handler table with 9 entries — but it is **unreachable from the shipped UI**: the
debug screen function `0x0800CAE4` has exactly one caller (the internal dispatch
at `0x0800CC60`), the dispatch `0x0800CC3C` appears only in a table at
`0x0800CB3D4`, and that table has zero code/pointer xrefs anywhere in the 8 MiB.
This is §16.3 case 2 (dead code), not a hidden menu with a lost key sequence.

A real input combination exists — **A+B+Start+Select held** triggers a soft reset
(`0x08004F6`→`0x0800520`: disables IRQ, writes the reset flag at `0x03007FFA`,
branches to `0x08000378`) — but that is a system reset, not a cheat.

Published codes could not be retrieved (3rd party cheat indexes 403, DuckDuckGo CAPTCHA, Bing
returned unrelated "GT" pages, archive/CDX timed out). No code literal from any
published source was therefore verified; per §3.4 this is recorded as unverified,
not as a silent omission. Fetched content was treated strictly as data.

## 3. How to reproduce

* Emulator: `mgba -3 -d gta3.gba` under `Xvfb :317` (my own display), `SDL_AUDIODRIVER=dummy`.
* Keymap (verified on-screen): A = `x`, B = `z`, Start = `Return`, Select =
  `BackSpace`, D-pad = arrow keys, L = `a`, R = `s`.
* Boot sequence: legal text → attract "DEMO" → title "PRESS START" → Start →
  **MODE SELECT**: CHAMPIONSHIP, TIME ATTACK, DRIFT-COMBO, LINK, OPTIONS,
  QUICK RACE, PRACTICE, EXTRA, SAVE.
* Menu walk performed with RAM evidence: title, MODE SELECT, CLASS, GARAGE
  (CHAMPIONSHIP and DRIFT-COMBO), and the locked EXTRA entry. Savestates
  `gta3.ss1`–`gta3.ss7` in `/tmp/gta3` contain the RAM images; IWRAM
  (state offset `0x19000`) and EWRAM (`0x21000`) MD5 fingerprints are distinct
  for each captured state (e.g. ss1 `66fb4f64fa0c`/`5c7a827fc28a`,
  ss3 `f4f7d5387e83`/`7795911833a7`, ss7 `c3d3b6c16678`/`c55176c789ea`).
* Input state struct: key reader `0x08002430` reads `0x04000130`, stores
  active-high held at `0x0300C035` (+0) and newly-pressed at +2; accessors are
  `0x08002494` (held) and `0x08002488` (pressed).
* No code was entered because no entry surface exists; button combos tested
  (L+R, L+R+Start, L+R+A, L+R+B, Start+Select+A+B, A+B+Start+Select, Konami
  sequence, triple-A+Start) produced only menu movement or the reset above.

## 4. Address map

| Address (ROM) | Meaning |
|---|---|
| `0x080000C0` | stock crt0 entry |
| `0x08002430` / `0x08002488` / `0x08002494` | key poll / pressed / held |
| `0x08003350` | text renderer: 1 byte/char through 16-bit table at `0x080C49A0` (`char → tile-1`, `0xFFFF` = no glyph) |
| `0x08004F6`–`0x0800520` | A+B+Start+Select soft-reset gate |
| `0x08020198` | 3-character initials-entry handler; alphabet `0x0805FC2C`, cursor clamp 0..53, code pointer `0x080CBE74` |
| `0x0805F850` | debug top-menu item pointer table (RACE, CAR, TST3, TST4, TST5, TST LINK, END) |
| `0x0805F86C` / `0x0805F8B0` / `0x0805F8A4` | `DBG TOP MENU` / `LINK TOP MENU` / `GEB123` labels |
| `0x0800CAE4` | debug top-menu renderer (loads the 7 strings above) |
| `0x0800CC3C` | debug menu dispatch (cases 1/6/7/11 → `0x0800C7F4`/`0x0800C884`/`0x0800CAE4`/`0x0800CC38`) |
| `0x0800CB3D0`–`0x0800CB43C` | debug handler table, 9 records of 12 bytes `{parent 0x0800CB2B8 or 0x0800CB2B0, Thumb handler, arg}` |
| `0x080C44B0`–`0x080C4768` | 97-entry car model-code string table (K100P, EK9, DC5, BCNR33, JZX100, OROCHI, E-KART, E-WIRE, E-RADI, ASLS01/02, …) |
| `0x080C49A0` | 256-entry `u16` ASCII→font-tile table used by `0x08003350` |
| `0x080CBE74` | alphabet/permutation structure: `ptr 0x0805FC2C`, u16 permutation data, `ptr 0x0800CB2B8`, `ptr 0x0802087D` |

RAM: key state `0x0300C035` (mirror `0x03004035`), reset flag `0x03007FFA`;
savestate layout (397,312-byte `gbAs`): IWRAM `0x19000`, EWRAM `0x21000`.

## 5. Algorithm

There is no password validator to reimplement. The two algorithmic surfaces
that were reconstructed are:

```
# text rendering (0x08003350)
for each byte b of string until 0:
    tile = table_0x080C49A0[b] - 1        # u16; 0xFFFF => skip
    emit glyph(tile)

# 3-character initials entry (0x08020198)
cursor += (key & 0x80 ? +1 : 0) - (key & 0x40 ? +1 : 0)   # /0x080202F6,/0x080202F8
cursor = clamp(cursor, 0, 53)
char = alphabet_0x0805FC2C[cursor]        # via struct 0x080CBE74
buf[i] = ascii_to_tile_table[char]        # display conversion at 0x080202E6/0x08020342
memcpy(record+8, buf, 3)                  # 0x0800D95C; record stride 72 bytes
```

The A+B+Start+Select gate is `if ((pressed & 0xF) && (held & 0xF) == 0xF)`;
otherwise no button-comparison code relevant to cheats exists in the five
call sites of the held/pressed accessors (`0x0800442`, `0x08004F6`, `0x0800504`,
`0x0809B52`, `0x08028F54`, `0x08029562`).

## 6. Tables

* Debug menu items (`0x0805F850`): `RACE`, `CAR`, `TST3`, `TST4`, `TST5`, `TST LINK`, `END`.
* Debug submenu strings (`0x0805F88C`–`0x0805F93C`): `TST3`, `TST3-1`, `TST4`,
  `GEB123`, `*`, `REAL PLAYER=`, `MSIO PLAYERS=`, `NETGRP PLAYERS=`, `ID=`,
  `TST2`, `RACE`, `DUMMY1`, `DUMMY2`, `GO NEXT`, `LINK TST2`, `NETGRP=`.
* Debug handler table (`0x0800CB3D0`): 9 handlers
  `0x0800CC3C, 0x0800CCB0, 0x0800CE2C, 0x0800CFA0, 0x0800D17C, 0x0800D244,
  0x0800D470, 0x0800D664, 0x0800D734`. All xref-free from outside.
* Entry alphabet (54 symbols, `0x0805FC2C`, cursor 0..53):
  `P0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ.,:;/-+*='"_?!%&h`. **Consumer is a
  name field, not a code validator** (§16.2b): the 3 bytes are copied into a
  save/record struct; no `strcmp`/`memcmp` compares them to a constant.
* Car codes: 97 entries at `0x080C44B0` with variable NUL-padded 8-byte records;
  the in-game GARAGE reads `CARS COLLECTED 20/97` on a fresh save.

## 6b. Enumeration

**Result: the search space is empty — there is no code system to enumerate.**

Bounded searches performed (counts are of the checked space, not of hits):

| Space checked | Method | Result |
|---|---|---|
| All reachable screens (title, attract, MODE SELECT ×9 entries, CLASS, GARAGE, EXTRA) | emulator walk + 7 savestates with distinct RAM fingerprints | no code/password entry screen; EXTRA ignores all inputs on fresh save |
| 76,923 ASCII strings (`strings -t x -n 4`) | keyword filter `password\|cheat\|code\|debug\|secret\|unlock\|hidden\|bonus` | only debug/credits/save strings (see §6); no code table |
| 8 MiB for known-code literals from published lists | literal `grep -abo` / byte search | none available to verify (web blocked; recorded) |
| 8 MiB for 4+ consecutive single-button masks (u16) | scripted scan, 192 candidate runs | all in script/tile data; only semantic hit is the descending 10-button mask table `0x080CC1B4` in debug code and `0x080CD9D4`; no game input code |
| All 5 callers of key held/pressed accessors | Thumb disassembly | one combo: A+B+Start+Select → soft reset; no unlock sequence |
| References to debug screen `0x0800CAE4` | BL scan + 32-bit pointer scan | 1 internal caller, 0 external pointers; dispatch table `0x0800CB3D4` has 0 xrefs → unreachable |
| ASCII→tile text bank | recovered table `0x080C49A0` and renderer `0x08003350`; searched ROM and RAM for menu strings as ASCII, `+0x20`, UTF-16LE/BE, XOR 0..255, add/sub 0..255, high-bit, nibble-swap, bit-reverse, tile-index bytes/u16 | no representation of `CHAMPIONSHIP`/`MODE SELECT`/`GARAGE` found in either ROM or RAM; see Unknowns |
| LZ77 blocks (header `0x10` + 24-bit size) | decompressor over all 0x10 headers | 0 blocks containing menu text |

Because no validator exists, §0.2's "mint an unpublished code and enter it" is
not applicable; the deliverable here is the **bounded negative** required by
§0.2 item 5: the menu enumeration, the searched spaces with counts, and the
tested published-code channel (unavailable).

## 7. Validation evidence

* **Observed:** title → MODE SELECT → CLASS → GARAGE (`CARS COLLECTED 20/97`),
  EXTRA selection accepted highlight but A produced no transition; B returned to
  parent; A+B+Start+Select reset the game; all 7 savestates contain distinct
  IWRAM/EWRAM fingerprints; fresh EEPROM all `0xFF`.
* **Derived:** debug-menu strings and 9-entry handler table; dead-code xref counts;
  A+B+Start+Select gate at `0x08004F6`; 3-char initials consumer (memcpy into
  record, not comparison); glyph table and text renderer.
* **Inferred:** that the 97-car and `EXTRA` gating are normal progress unlocks
  (consistent with `CARS COLLECTED` counter and lack of any code surface); that
  the debug subsystem was left in by the developer but unreachable in the
  shipping build.
* **Not observed:** any accepted password, button code, or hidden screen.

## 8. Unknowns

1. The storage format of the on-screen menu text itself was not located. The
   ASCII→font-tile table and its renderer are identified, but `MODE SELECT`,
   `CHAMPIONSHIP`, etc. appear in neither ROM nor RAM under any of the tested
   encodings (§6b). The negative conclusion therefore rests on screen
   enumeration + input/comparator search, not on a decoded text bank. This is
   the one place where the "decode before declaring negative" requirement is
   only partially met.
2. Completion-gated behaviour (what unlocks the remaining 77 cars and EXTRA)
   was not played through; no code path was found that bypasses it.
3. Web verification of published codes was impossible from this environment;
   no published literal was available to test in the ROM.
4. A computed (runtime-derived) jump to the debug table cannot be excluded by
   static xref counting alone, though no such computation was found.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3
  (struct/Capstone 5.0.7), `arm-none-eabi-objdump -M force-thumb`.
* `mgba -3 -d` on `Xvfb :317` with a Python PTY debug server
  (`/tmp/gta3/dbgserver.py`, client `dc.py`) and savestate parser
  (`ssread.py`, decompresses the PNG `gbAs` chunk).
* Custom scans: `scanptr.py`, `blscan.py`, `ldrscan.py`, `lzscan.py`.
* Cross-game check: GT Advance 2 (`AGWE78`, SHA-256 prefix `2a61ba4a…`) lacks
  `DBG TOP MENU`, `GEB123`, and the `P0123…` alphabet; this image was analysed
  independently and **nothing was found to be shared** with that title (the
  incidental `GT2` string also exists there but is at an unrelated address).

No ROM bytes or copyrighted assets are reproduced in this report; only hashes,
addresses, and found code/data structure facts are published.
