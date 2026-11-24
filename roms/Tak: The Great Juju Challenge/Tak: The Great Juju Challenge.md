# Tak: The Great Juju Challenge (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Analysis date: 2026-11-20. Method: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md) §0.2 (full enumeration), §16.3/§16.20 (four kinds of "no"; CodeBreaker activator is not an in-game trigger), §16.13 (savestate RAM reads). REA skill loaded; raw-GBA path used (objdump/Capstone + mGBA + savestate diff) because REA had no bound native target.

Scope: **in-game / developer-intended cheats only.** No GameShark/CodeBreaker/AR code was applied to the game, published, or counted as a cheat; a CB-style *RAM write* was used only as a research tool to open the developer menu, exactly as §16.20 prescribes.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Tak: The Great Juju Challenge/Tak: The Great Juju Challenge.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title | `TAK GJC` |
| Game code / maker | `BJWE` / `78` |
| Entry word | `0xEA00002E` (`b 0x080000C0`, stock); one Nintendo logo; no trainer/cracktro |
| Version / complement / checksum | `0x00` / `0xE6` / `0x0000` |
| MD5 | `4328abd6ef7ffe7c75323db46b91ebdd` |
| SHA-1 | `0999a8ee2bae78a223c992408e987422ba0c0af9` |
| SHA-256 | `79ad2584f8b30885941d731ee58bba2fa725c8bfb9b746e1e4d5b651d13add4a` |
| Engine / developer | WayForward 2D platformer, Shin'en GAX 3.05A audio (`0x0817C088`); build string `build 07/25/2005, 5:26pm` |

This is **not** the Helixe SKU covered by `Tak 2: The Staff of Dreams` (BT9E) and not a console/DS SKU: the consumer "Universal Card" numbers and blessing-shrine codes belong to other platforms. Verified independently, not inherited from sibling reports.

---

## 2. Executive summary

There is **no reachable in-game code system**: no password keypad, no text-entry validator, and no controller button code that can be completed from any retail screen. The only cheat surface is a **developer debug menu** (13 root categories, 11 populated submenus, 108-effect sound test) reached when the one-byte screen selector at IWRAM `0x0300175C` is set to `0xC0`. 3rd party cheat indexes publish "CodeBreaker `74000130 00FF` + `3300175C 00C0`, then press L+R": the first line is a CB button activator (`0x00FF` = L+R XOR `0x3FF`) and the second is a device RAM write, not an in-game input. Writing `0xC0` alone from the debugger/savestate opens the menu with **no pad input at all** (screenshot `dbg_gate_C0.png`), so L+R is not an in-game code (§16.20).

A genuine 4-press listener **does exist in the ROM** at `0x08010D34` — Left, Up, Right, Down → `mov r0,#0xC0; bl 0x0800F090` (debug-menu request) — but it is **dead code**: zero BL references, zero 32-bit pointers (including the Thumb-bit form), the only call it makes registers a pointer to its own trailing `bx lr` (`0x08010D75`), and a live Thumb breakpoint at `0x08010D34` never fired while title → file select → difficulty → intro → world map → map-pause were walked and while the sequence and six other undocumented combinations were pressed. RAM after each combination stayed in the title's own screen set (`0x31/0x35/0x37`) with the request byte `0x03000970` and the listener flag `0x03007204` both zero. This is a bounded dead-code negative, not "not tested".

The debug screen-index space is a single byte. Exact menu tables were decoded from ASCII (not guessed from screenshots): 13 root entries, 3+3+3+3+3 levels, 12 arenas, 12 misc screens, 5 dreams, 5 bosses, 8 driving, and 108 FX names. A **novel, unpublished screen value `0x01`** was minted and entered through the gate: it renders the legal screen and was RAM-verified (`0x0300175C` read back `0x01`, then auto-advanced to `0x32` with previous-screen `0x01`). Out-of-range values `0x00/0x02/0x03/0xD0/0xD1/0xFE/0xFF` were rejected (black screen with the selector unchanged at its boot value).

---

## 3. How to reproduce

### 3.1 Environment

```bash
Xvfb :316 -screen 0 1024x768x24 &  DISPLAY=:316 openbox &
DISPLAY=:316 SDL_AUDIODRIVER=dummy mgba -3 "<rom>.gba" &
```
mGBA 0.10.5; default SDL map A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Keys held 60–90 ms (longer double-steps menus, §16.2). Screenshots via `scrot` on `:316`; all captured frames were in `/tmp/takjuju3/`.

mGBA's GDB stub could not be used: port 2345 was held by another agent's emulator. RAM reads/writes therefore used **savestate patching** (§16.13): a `.ss1` is a PNG whose `gbAs` chunk is zlib-compressed; `zlib.decompress` gives a 397,312-byte state whose IWRAM image begins at raw offset `0x19000`, so GFA `0x0300175C` is raw byte `0x1A75C`. `patchstate.py` rewrites that byte, recompresses, and rebuilds the PNG chunk with a fresh CRC. `F1` reloads slot 1, so each experiment is one keypress. (The CLI `-d` debugger was also used for breakpoints; it only accepts commands while halted.)

### 3.2 Retail screen walk (all observed, with screen-index RAM)

| Screen | Path | `0x0300175C` |
|---|---|---|
| Title / "PRESS START" | boot | `0x31` (cycles `0x35`/`0x37` with the character animation) |
| SELECT A FILE (File 1/2/3 NEW, ERASE THIS FILE?) | Start, A | `0x37` |
| SELECT A DIFFICULTY (EASY/MEDIUM/HARD) | A on File 1 | — |
| Intro storyboards ("Hello Lok and Tak!", "Now go, and don't lose!", …) | A on EASY | `0x3F` (same screen as debug "Intro Storyboards") |
| World map "Grammazom's" | advance storyboard | — |
| World-map Pause (Resume / Quit) | Start on map | — |
| Gym test stage (green room, debug counters) | debug menu → Gym | `0x04` |

No screen offered a password field, code entry, name entry, or hidden option.

### 3.3 Debug menu

Write `0xC0` to `0x0300175C` (patchstate + `F1`, or `w/1` in `-d`). The menu opens immediately — **before any pad input**. Navigation: D-pad Up/Down (14-slot ring, wraps), **Start** confirms (A does nothing), and the list is drawn from the ASCII tables below.

---

## 4. Address map

| Address (ROM / GFA) | Meaning | Evidence |
|---|---|---|
| `0x0817CA90`–`0x0817CC64` | Root debug-menu table, 13 records (`u32 scene_id`, 32-byte label), terminator `0xFFFFFFFF` | Derived from bytes; rendered labels match `dbg_reopen.png` |
| `0x0817CC88`–`0x0817D5D0` | Eleven submenu tables, same 0x24-byte record format | Derived; each rendered via patched screen ID |
| `0x0817D5F4`–`0x0817E524` | FX (sound-test) table, 108 records, IDs 1–123 | Derived; `enum_fx.png`, `fx_bottom.png` |
| `0x08010D34` | **Dead** button listener: L,U,R,D → request screen `0xC0` and set `0x03007204=1` | Derived + live breakpoint never hit |
| `0x08010D0C` | Its getkey helper (polls `u16` at `0x030024C4`, 15-try yield loop) | Derived |
| `0x0800F090` | Screen-request setter: `r0`=u8 screen id, `r1`=0x80 | Derived from 24 BL callers |
| `0x0800EC40`–`0x0800EC52` | State machine: pending `0x03000970` → current `0x0300175C`, previous → `0x03000770` | Derived |
| `0x0300175C` | **Current screen index (u8)** — the gate byte | Observed via savestate + prior GDB read |
| `0x03000770`, `0x03000970` | Previous screen; pending screen request | Observed |
| `0x03007204` | Flag the dead listener would set | Observed (always 0) |
| `0x030024C4` | Engine's active-high pressed-key bits (`u16`) | Derived from `0x0800E7BA`–`0x0800E7CC` |
| Savestate raw `0x19000` | IWRAM base; `+0x175C` = gate byte | Observed by patch → screen change |

---

## 5. Algorithm / pseudocode

```
// state machine at 0x0800EC40 (derived):
if (pending = byte[0x03000970]) != 0:
    byte[0x03000770] = byte[0x0300175C]   // save previous
    byte[0x0300175C] = pending            // switch screen
    byte[0x03000970] = 0

request_screen(id):                       // 0x0800F090
    byte[0x03000970] = id & 0xFF

// DEAD listener at 0x08010D34 (not reachable in the retail image):
register_callback(0x08010D75)             // = its own "bx lr" — a no-op
loop:
  for key in [LEFT(0x20), UP(0x40), RIGHT(0x10), DOWN(0x80)]:
      if getkey() != key: continue loop
  byte[0x03007204] = 1
  request_screen(0xC0)                    // debug menu
```
`getkey()` returns `u16 byte[0x030024C4]` after up to 15 yields; that global is the engine's active-high newly-pressed mask, so the four comparisons are the D-pad directions. The listener is unreachable, so no retail input can produce request `0xC0`.

---

## 6. Tables

### 6.0 Debug menu record format
`u32 scene_id; char label[32];` — `0x24` bytes/record, `0xFFFFFFFF` terminator. Labels are plain ASCII, so no font decoding was needed to enumerate them; screenshots confirm the rendered glyphs.

### 6.1 Root menu (13 entries, IDs not otherwise published)
`Gym=0x04`, `Intro Storyboards=0x3F`, `World1=0xC2`, `World2=0xC3`, `World3=0xC4`, `World4=0xC5`, `World5=0xC6`, `Mini Games=0xC7`, `Bosses=0xCB`, `Dream Worlds=0xC8`, `Driving=0xC9`, `Misc Screens=0xCA`, `FX=0xCF`. The build line is an unselectable header; the ring is 14 slots.

### 6.2 Submenus (verified on screen)
| Submenu | Entries (id → label) |
|---|---|
| World1 | `0x0A W1_1`, `0x0B W1_2`, `0x0D W1_3` |
| World2 | `0x1D W2_1`, `0x1E W2_2`, `0x1A W2_3` |
| World3 | `0x38 W3_1`, `0x39 W3_2`, `0x3A W3_3` |
| World4 | `0x3C W4_1`, `0x3B W4_2`, `0x3D W4_3` |
| World5 | `0x83 W5_1`, `0x82 W5_2`, `0x84 W5_3` |
| Mini Games | `0x0E W1_ARENA1`, `0x0C W1_ARENA2`, `0x0F W1_ARENA3`, `0x10 W1_ARENA4`, `0x11 W1_ARENA5`, `0x1B W2_ARENA1`, `0x1C W2_ARENA2`, `0x1F W2_ARENA3`, `0x20 W2_ARENA4`, `0x21 W2_ARENA5`, `0x22 W2_ARENA6`, `0x85 W5_ARENA1` |
| Bosses | `0x06 Mummy King`, `0x05 Caged`, `0x07 Mind Reader`, `0x08 DarkMist`, `0x09 Dinky` |
| Dream Worlds | `0x25`–`0x29 DREAM1`–`DREAM5` |
| Driving | `0x13 DRIVING TEST`, `0x15 DRIVING TEST2`, `0x12/0x16/0x17/0x18/0x19 W1..W5 RACING`, `0xCD KartX` |
| Misc Screens | `0x32 STARTUP`, `0x2F MAP 1`, `0x2B..0x2E MAP 2..5`, `0x30 MAP MINI`, `0x2A MAP OVER`, `0x23 LIFE`, `0x24 GAME OVER`, `0xC1 SAVE/CONTINUE`, `0xCE CREDITS` |
| FX (sound test) | 108 entries, IDs 1–123 (15 unused: 2,6,21,22,25,32,38,42,43,48,51,54,60,94,101); e.g. `1 FX_accelerate_loop_01`, `0x3F FX_jumping_woodie_attack_spin`, `0x73 FX_thunder_01`, `123 FX_woodie_walk_02` |

Selection semantics: 14-slot wrap on root; FX clamps at entry 108 after 120 Down presses (`fx_bottom.png`), so no hidden entries past the terminator.

---

## 6b. Enumeration

**Space definition.** The feature is a selector byte, not a checksum code: alphabet = integers `0x00..0xFF` (256 values), length 1 byte, no reserved/checksum bits in the gate itself. The game's own menu table names 13 root IDs and 11 submenus; the rest of the 256 values are either ordinary game screens or invalid.

**Novel value (not in 3rd party cheat indexes, or any debug table): `0x01`.** Generated offline (patched into the savestate gate), entered through the real screen dispatcher with `F1`, and observed on the emulator: the THQ/WayForward legal screen is drawn (`novel_screen_01.png`). RAM immediately after entry read `0x0300175C = 0x01`, `0x03000770 = 0x00`; the legal screen then auto-advanced and a later state read `0x0300175C = 0x32`, `0x03000770 = 0x01`, confirming the transition came from that novel value. `0x05` (Caged boss storyboard) is a second working ID absent from the root table but present in the Bosses submenu.

**Bounds proven by rejection.** With the same patched-state method: `0x00`, `0x02`, `0x03`, `0xD1`, `0xD0`, `0xFE`, `0xFF` all produced a black screen and were not entered as menus (`montage_oor.png`, `montage_novel.png`). In the byte space that is 8 explicitly rejected values; the debug menu itself is exactly the 13 table records (terminator at `0x0817CC64`) plus 11 submenus with 63 levels/arenas and 108 FX entries — no unlisted menu item was found on any screen that was walked.

**Button-code space bounded.** One candidate exists and is provably dead (zero xrefs, breakpoint never hit, registration points at a no-op). Seven undocumented combinations were pressed at the title with RAM verification: L,U,R,D; L+R; L+R+Start; Konami (U,U,D,D,L,R,L,R,B,A); A,B,Start,Select; L,L,R,R,U,U,D,D; Start,Select,A,B. All left `0x0300175C` in the title set (`0x31/0x35/0x37`), `0x03000970 = 0`, `0x03007204 = 0` — no accept path.

**Negative counts.** 112,187 printable runs (≥4 chars): `password` 0, `cheat` 0, `secret` 0, `debug` 0, `level select` 0, `sound test` 0, `gallery` 0, `invalid` 0; `code` 2 (binary noise at `0x120E27` and the Shin'en banner `0x17BC3E`), `unlock` 1 (`FX_unlock_pegasus_door_01`, a sound-effect name), `enter` 4 (gameplay text). Literal alphabet searches: `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `abcdefghijklmnopqrstuvwxyz`, `0123456789`, and the 36-symbol concatenation → **0 hits each** in all 8 MiB, in ASCII; no on-screen keyboard and no name/password field exists on any walked screen. A u16 scan of the first `0x60000` bytes for runs of 4–10 *single* GBA key masks returned **0** plausible sequence tables (a looser all-combination scan found 12,461 runs, all in compressed asset data). The save is a 512-byte all-`0xFF` EEPROM image with no name or unlock field. Therefore: no password system, no validator to reverse, no live button code — a bounded negative, not an untested guess.

---

## 7. Validation evidence

* **Observed (emulator/screenshot):** every screen in §3.2; all 13 root and 11 submenu lists; 108th FX entry and clamp; 14-slot root wrap; novel screen `0x01`; seven rejected key combinations with RAM reads; black-screen rejections for seven out-of-range IDs; no pad input needed after the `0xC0` write.
* **Derived (bytes/disassembly):** menu record format and counts; the u8 selector and its 25 code references; pending/previous globals; the `0x08010D34` listener and its exact four comparisons; its zero xrefs; the state machine at `0x0800EC40`; the CB `00FF` button value = L+R XOR `0x3FF`.
* **Inferred:** that the listener was intended as a debug shortcut but shipped unwired (its self-referential no-op callback). It is *not* reported as reachable. The exact effect of playing each of the 63 levels from the menu was not exercised; the tables and level-entry screens were verified, not full playthroughs.

---

## 8. Unknowns

* Why `0x08010D34` registers `0x08010D75` (its own `bx lr`) rather than its own entry — likely a build artifact or a removed feature; no in-game path now calls it.
* The 15 gaps in the FX ID sequence (1–123 with 108 records) were not matched to removed effects or music.
* Screen IDs that render ordinary levels/cutscenes (e.g. `0x05`) were confirmed as visible but not exhaustively enumerated outside the published menu tables; the 8 rejected values are the proven bounds, not a proof about every remaining byte.
* No EEPROM save was ever written in this run (all `0xFF`), so save-bit unlockables could not be exercised; no unlockable strings or name fields were found in ROM.

---

## 9. Tooling

* `mgba` 0.10.5 (`-3`, `-d`, `-g`), Xvfb `:316`, openbox, `xdotool` XTEST, `scrot`, ImageMagick `convert`/`montage`.
* `arm-none-eabi-objdump -M force-thumb` / raw ARM, Capstone (Thumb LDR-literal and BL target scanners), `strings -t x`, Python 3 `struct`/`zlib`.
* Local helper scripts in `/tmp/takjuju3/`: `patchstate.py` (savestate IWRAM patcher), `readstate.sh`, `enum_screens.sh`, `seqtest.sh`, `ptyctl.py`/`gpty.py` (PTY controllers for mGBA `-d` and gdb), `keylib.sh`.
* All screenshots were kept in `/tmp/takjuju3/`; no ROM, graphics, or audio were extracted or redistributed.

---

## 10. Legal note

Findings, addresses, hashes, and the algorithms above are published; no copyrighted ROM or extracted assets are included.
