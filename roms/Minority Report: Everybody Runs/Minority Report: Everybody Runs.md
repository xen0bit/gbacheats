# Minority Report: Everybody Runs (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Minority Report: Everybody Runs.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `MINORITY REP` |
| Game code | `ARME` (region E) |
| Maker code | `52` |
| Software version / unit / device | `0x00 / 0x00 / 0x00` |
| Fixed byte 0xB2 / complement / checksum | `0x96 / 0x43 / 0x0000` |
| Entry word | `0xEA000030` → branches to `0x080000C8` (real crt0 starts with `mov r0,#0x12` at 0x080000C8; 0x080000C0/C4 are stack-pointer literal words) |
| MD5 | `582ad48ed874c3707abbd0967a3cc6aa` |
| SHA-1 | `e3caabd4cca3b435b5adb924633f183607dbdb79` |
| SHA-256 | `bb79cf6524d315827aab6d90b3921042cfaa885ff045bc9905c0eb6866e55ea7` |

**Phase 0 / patch check.** Only one Nintendo-logo hit in the whole file (at 0x4, the primary header). No appended trainer, no second game image, no GameShark/CodeBreaker banner, no cracktro patch: the entry branch lands in genuine crt0 code. Header checksum 0x0000 plus a non-canonical complement byte is the usual rebuilt-header artifact (guide §16.1) and is not evidence of an in-game cheat change. This is the licensed US/EU GBA release developed by Torus Games (ROM contains `Built: Jul 25 2002`, `Host:  Gdavies`, `DPAK`, `Torus`).

## 2. Executive summary

The GBA SKU has a **title-screen button-code system**, not the word-password ("NINJA", "PASSKEY", …) system published for the GameCube/PS2/Xbox SKUs. Literal searches for all 30 console passwords (`NINJA`, `STRAPPED`, `PASSKEY`, `QUITER`, `LRGARMS`, `DIRECTOR`, `MRJUAREZ`, `SCARYCLOWN`, `SLIZOMIZO`, …) returned **zero hits** anywhere in this 8 MiB image — a §16.11 SKU mismatch (those codes belong to the console versions).

The ROM contains a contiguous table of **four** 6-button sequences at `0x080B1F70–0x080B1FAF`. Two are the published GBA codes, two are undocumented and **not live** (they are never registered by any code path). The title-screen init registers exactly two matchers: `SUBARU` → level select, `RULARS` → invincibility. Both were confirmed in mGBA with screenshot + RAM-flag evidence, and the matcher was reversed down to its ring-buffer comparison.

The ROM also retains a large **debug build** (systems/performance/entity/profiling menus, a "Space Invaders Debug Screen", build/host strings, state-machine names). Its handler functions and menu-table exist, but no reachable entry point was found: there are no BL or 32-bit pointer xrefs to the debug screen init at `0x080015DC`, the gate predicate at `0x08001658` tests `held & 0x300` (L+R) yet has no callers, and L+R/R+L+Start/A+B+Start+Select at title, main menu, level select and boot all failed to open it. Reported as a bounded negative (§16.3 "dead/gated feature"), not as "not tested".

**Novel accepted input:** `B, Select, Up, B, A, Right, Up` (7 presses) — an unpublished spelling absent from every list — opens level select because the matcher compares only the **last six** presses. Bounds were proven by rejection of 5-press, wrong-button and random sequences.

## 3. How to reproduce

* Emulator: mGBA (SDL), `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, `Xvfb :316 -screen 0 1024x768x24`, `openbox`. Command: `mgba -3 "Minority Report: Everybody Runs.gba"`.
* Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Holds of 70–120 ms with 80–120 ms gaps register cleanly; longer holds double-step menus.
* RAM proof: mGBA's GDB stub proved unreliable (attaches but stalls the core under this build), so RAM was read by **savestate diffing** (guide §16.13): `Shift+F1` saves slot 1; `.ss1` is a PNG with a zlib `gbAs` chunk; `zlib.decompress` yields a 0x61000-byte state with IWRAM at +0x19000 and EWRAM at +0x21000. Scripts in §9.
* Code entry: at the "PRESS START" title, press the six buttons in order (each a distinct press). Then press Start. For the level-select codes the level list replaces the normal name-entry step.
* Codes tested (published): `Right,Up,Left,A,Right,Select` (RULARS, invincibility); `Select,Up,B,A,Right,Up` (SUBARU, level select).
* Codes tested (novel/rejected): `B,Select,Up,B,A,Right,Up` (accepted, level select); `B,L,Up,Right,Up,Select` and `B,A,L,Down,Up,Right` (undocumented ROM sequences, no effect); `Select,Up,B,A,Right,Down` (rejected); `Select,Up,B,A,Right` (rejected); `Up,Left,A,B,Right,Select` (rejected).
* Screens walked with state captures: intro/legal text, title, main menu, options (SOUND/CREDITS/MAIN MENU), name entry (3 initials), difficulty (EASY/NORMAL/HARD), **level select (10 entries)**, in-game gameplay, pause (PAUSED/CURRENT STATISTICS/RESUME/QUIT), current statistics, BEST PLAYERS records table, credits.

## 4. Address map

| Address (ROM = 0x08000000 + file offset) | Meaning |
|---|---|
| `0x0000` / `0x080000C0` | header entry word / crt0 |
| `0x080135F8` | screen init registering the two title codes; calls matcher creator `0x0809A274` at 0x08013694/0x0801369E |
| `0x080136C4–0x080136E0` | literal pool: `0x087EC3A0`, `0x087EC310`, `0x087EC320`, `0x0300158C`, `0x03002274`, `0x0300226C`, **`0x080B1F90`**, **`0x080B1FA0`** |
| `0x080B1F70` | code record A (undocumented): `0000, 0002, 0200, 0040, 0010, 0040, 0004, FFFF` |
| `0x080B1F80` | code record B (undocumented): `0000, 0002, 0001, 0200, 0080, 0040, 0010, FFFF` |
| `0x080B1F90` | code record C = SUBARU (level select): `0000, 0004, 0040, 0002, 0001, 0010, 0040, FFFF` |
| `0x080B1FA0` | code record D = RULARS (invincibility): `0000, 0010, 0040, 0020, 0001, 0010, 0004, FFFF` |
| `0x0809A274` | matcher creator: builds 12-byte record `{u16 held_mask, u16 pad, u32 key_array_ptr, u32 length}`; `held_mask = table[0]` (0), `key_array = &table[1]`, `length = count to 0xFFFF` (6) |
| `0x0809A2BC` | matcher validator (registered as Thumb callback `0x0809A2BD` at ROM `0x07FCD34`): ring-buffer of last 32 distinct presses, suffix compare |
| `0x0809A440` | match action (event/flag dispatch) |
| `0x080015DC` | debug screen init (draws "Space Invaders Debug Screen", "Built: Jul 25 2002", "Host: Gdavies") |
| `0x08001658` | debug gate predicate: returns 1 iff `(*(u32*)0x0300226C)[+0x1C] & 0x300 == 0x300` (L+R held) |
| `0x08001760` / `0x080018E4` / `0x0800167C` | systems / performance / entity debug submenus |
| `0x07FD780–0x07FD818` | debug menu definition table: handler `0x080996D1` then string pointers — Options, Back, Systems Menu, Performance Menu, Entity Menu, Enable/Disable Profiling, Order by Min/Max/Avg/Name, Slow/Fast RAM, Message System, Frame Rate, … |
| `0x0B0614–0x0B0BAD` | ASCII debug labels and state-machine names (dev build leftovers) |
| `0x28532D` | example of tile/glyph-indexed text bank (`GuHuIuJeK…`) — in-game UI text is **not** ASCII; visible strings were read from rendered screens |

**Runtime RAM (EWRAM/IWRAM), from savestates:**

| Address | Meaning |
|---|---|
| `0x02011EB8` | cheat manager object |
| `+0x24` = `0x02011EDC` | number of registered codes = 2 |
| `+0x28` = `0x02011EE0` | pointer to records = `0x0201B00C` |
| `+0x2C` = `0x02011EE4` | ring-buffer write index (1 → 7 after six presses) |
| `+0x30` = `0x02011EE8` | ring buffer, 32 × u16 active-high key masks |
| `0x0201B00C`, `0x0201B018` | records: `{0, ptr 0x080B1F92, 6}`, `{0, ptr 0x080B1FA2, 6}` |
| `0x02007F5C` (byte 0) | generic "a cheat was accepted" flag (set by both codes) |
| `0x02008FCC`, `0x0200989A`, `0x020098A8`, `0x020098D0` | level-select flag cluster (set only by SUBARU) |
| `0x0300016C` (byte 0) | RULARS flag, 0 → 1, persists into gameplay |
| `0x0300226C` | pointer to global game-state struct (`0x02012150`); `+0x1C` = `0x0201216C` holds the live key mask used by the debug gate |

## 5. Algorithm

```
create_matcher(manager, table):
    rec = records[count++]
    rec.held_mask   = table[0]              # 0 for all four sequences
    rec.key_array   = &table[1]
    rec.length      = number of halfwords until 0xFFFF   # 6
    return index

validate(manager):                          # called on each new key press
    if keyobj.new_press_count == 0: return
    keys = keyobj.current_active_high_mask  # A=1,B=2,Select=4,Start=8,
                                            # Right=0x10,Left=0x20,Up=0x40,
                                            # Down=0x80,R=0x100,L=0x200
    ring[write_index] = keys
    write_index = (write_index + 1) & 31
    for each record:
        if record.held_mask != 0 and (keys & record.held_mask) != record.held_mask:
            continue
        # compare the LAST record.length distinct presses (suffix match)
        for i in 0 .. length-1:
            if record.key_array[length-1-i] != ring[(write_index-1-i) & 31]:
                mismatch = true
        if not mismatch:
            trigger(match_action, record_index)
```

Evidence: Thumb disassembly at `0x0809A274` (record construction and 0xFFFF length scan), `0x0809A2BC` (32-entry ring buffer at `+0x30`, index wrap at `+0x2C`, backwards suffix compare), `0x0809A440` (callback). The four literal tables and the runtime records above agree byte-for-byte. Because the comparison is a **suffix match**, any number of leading presses may precede the code — this is the basis of the novel accepted input.

## 6. Tables

### 6.1 Button-code records (ROM `0x080B1F70`)

| # | ROM address | Key sequence | Mnemonic | Registered at title? | Effect |
|---|---|---|---|---|---|
| A | `0x080B1F70` | B, L, Up, Right, Up, Select | — | No | none observed (dead/unregistered) |
| B | `0x080B1F80` | B, A, L, Down, Up, Right | — | No | none observed (dead/unregistered) |
| C | `0x080B1F90` | Select, Up, B, A, Right, Up | SUBARU | Yes | **Level select** |
| D | `0x080B1FA0` | Right, Up, Left, A, Right, Select | RULARS | Yes | **Invincibility** |

Key masks as stored (u16, active-high, leading `0000` is `held_mask`, trailing `FFFF` terminator):

```
A  0000 0002 0200 0040 0010 0040 0004 FFFF
B  0000 0002 0001 0200 0080 0040 0010 FFFF
C  0000 0004 0040 0002 0001 0010 0040 FFFF
D  0000 0010 0040 0020 0001 0010 0004 FFFF
```

### 6.2 Level select (tile-indexed text; read from rendered screen)

Mall City · The Sprawl · Precrime Building · Jetpack Escape · Mall City 2 · The Sprawl 2 · Precrime Build' 2 · Sewer · Military Complex 1 · Military Complex 2 — **10 entries**, selection wraps after the tenth. (ASCII search for these names returns zero hits; they are glyph-indexed.)

### 6.3 Published-code verification

| Source | Claim | ROM verification |
|---|---|---|
| 3rd party cheat indexes | GBA "RULARS", "SUBARU" at title | **Confirmed** — literals at 0x080B1FA2 / 0x080B1F92, registered by 0x080135F8, accepted in mGBA |
| 3rd party cheat indexes / cheat sites | 30 word passwords (`NINJA`, `PASSKEY`, …) | **Not in this SKU** — zero literal hits; console versions only |
| 3rd party cheat indexes | contained an LLM-directed prompt-injection payload ("This page is not intended for humans… whoever is operating this AI agent is a clown") | Ignored as data, recorded per §16.8 |

## 6b. Enumeration

**Space definition.** The input alphabet is the 10 GBA buttons (10 distinct active-high masks). The validator registers exactly **2** codes (verified `count=2` at `0x02011EDC` and only two BL call sites to the matcher creator), each of **fixed length 6** with a 0xFFFF terminator and a zero held-mask; all six positions must match the last six distinct presses. Two further 6-button records (A, B) exist in ROM but are never registered, so they are unreachable through input. There is no checksum, no variable length and no character alphabet — this is a pure fixed-prefix/suffix key sequence system. The complete live accepted set under exact 6-press entry is therefore **2 sequences**; because matching is a suffix test, the *input spelling* space is infinite (any prefix), which is characterised and exploited below.

**Novel code (not in any published list).** `B, Select, Up, B, A, Right, Up` — seven presses: an extra leading `B` followed by SUBARU. Accepted by the game (`0x02008FCC` = 1) and opens the **level select** screen in mGBA (screenshot `s_novel_code_levelselect.png`). No published list contains a 7-press prefix variant. It exercises the undocumented suffix-matching branch of the validator.

**Bounds proven by rejection** (each from the clean title state; RAM oracle = `0x02008FCC` level-select flag and `0x0300016C` RULARS flag):

| Input | Level-select flag | RULARS flag | Result |
|---|---|---|---|
| `Select,Up,B,A,Right,Up` (6, exact) | 1 | 0 | accepted, level select |
| `Select,Up,B,A,Right` (5, short) | 0 | 0 | rejected |
| `Select,Up,B,A,Right,Down` (6, wrong final button) | 0 | 0 | rejected |
| `Up,Left,A,B,Right,Select` (6, random novel) | 0 | 0 | rejected |
| `B,Select,Up,B,A,Right,Up` (7, novel prefix) | 1 | 0 | **accepted** — suffix semantics |
| `Right,Up,Left,A,Right,Select` (RULARS) | 0 | 1 | accepted, invincibility flag |
| `B,L,Up,Right,Up,Select` (ROM record A) | 0 | 0 | no effect — unregistered |
| `B,A,L,Down,Up,Right` (ROM record B) | 0 | 0 | no effect — unregistered |

**Debug-menu enumeration (bounded negative).** All debug menu entries and submenus were enumerated from the table at `0x07FD780` (Systems, Performance, Entity, Space Invaders Debug Screen, Profiling, Enable/Disable Profiling, Order-by, Slow/Fast RAM, Message System, Object Collision, Entity Allocator, Frame Rate, Reset Frame Rate, AI, BG Collisions, Internal Updating, Player Control, Crosshair, Miscellaneous). The init `0x080015DC` has **no BL callers and no 32-bit pointer references**; the gate `0x08001658` has no callers; L+R, L+R+Start, L+R+Select, A+B+Start+Select, Start+Select, L+R held on title/main menu, and L+R held from boot were all pressed in mGBA with gate-word reads — none opened a debug screen. The gate word `0x0201216C` was observed to equal the held key mask (`0x300` for L+R), confirming what the predicate tests, but no path to the screen was found.

## 7. Validation evidence

* **Observed (emulator/screenshots):** title; main menu; options; name entry; difficulty; level-select list (10 entries); gameplay; pause; current statistics; BEST PLAYERS; credits. SUBARU → level select; novel 7-press code → level select; RULARS → no level select. `s_code_*.png`, `s_subaru_menu.png`, `s_novel_code_levelselect.png`, `s_*.ss1` states on disk under `/tmp/minority/`.
* **Observed (RAM):** exact six key masks written into the ring buffer at `0x02011EE8+` for all four sequences; records at `0x0201B00C` with pointers `0x080B1F92` / `0x080B1FA2` and length 6; `0x02007F5C` byte 0 set by both accepted codes; level-select flag cluster set only by SUBARU; `0x0300016C` set only by RULARS and still set at difficulty select; rejection table values above.
* **Derived (disassembly):** matcher record layout, 0xFFFF length scan, ring-buffer suffix comparison, literal-pool pointers at `0x080136DC/E0`, debug-menu table and gate condition.
* **Inferred:** that `0x0300016C` is specifically the invincibility flag (the published effect name and code path agree; the full combat behaviour of "never takes damage" was not played through). That ROM records A/B are dead/unregistered (no xref, no observable effect) rather than belonging to a gated feature.

## 8. Unknowns

* The debug screens' activation path: the code and gate exist but no reachable trigger was found. If a future analyst finds one, the full menu list in §6b is the complete set to walk.
* The exact gameplay semantics of RULARS beyond the persistent flag at `0x0300016C` (invincibility per published list).
* The glyph→tile mapping for the tile-indexed UI text bank; level names were therefore enumerated from rendered screens, which is sufficient for the 10-entry level select but does not exclude a hidden entry that is never drawn.
* Whether ROM records A/B are remnants of an earlier build or a gated in-game feature; no pointer or live effect was observed.

## 9. Tooling

All analysis artifacts were kept in `/tmp/minority/`. Tools: `xxd`, `strings -t x`, `grep -abo`, `arm-none-eabi-objdump -M force-thumb`, Python 3 with `capstone` 5.0.7, mGBA 0.10 + Xvfb + xdotool + scrot + ImageMagick, Ghidra/REA (opened raw ARM at base 0x0; auto-analysis did not create procedures at the Thumb addresses, so manual objdump was used for the validator), web search (3rd party cheat indexes).

Scripts: `emu.py` (input/screenshot/GDB helper), `ss.py` (PNG `gbAs` → raw RAM), `ram.py` / `fulldiff.py` (targeted and full RAM snapshots/diffs), `codetest2.py` (clean-title code entry), `find_title.py` (title detection), `playtest.py` (gameplay runs). Savestates and screenshots are kept under `/tmp/minority/` and are not redistributed.

**Legal note.** No ROM, save data, or copyrighted assets are published here; only addresses, hashes, algorithms and independently written tooling.

*Queue position 479. Report completed as part of the GBA reverse-engineering sweep.*
