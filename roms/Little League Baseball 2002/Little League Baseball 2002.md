# Little League Baseball 2002 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Little League Baseball 2002/Little League Baseball 2002.gba` |
| Size | 8,388,608 bytes (`0x800000`, 8 MiB) |
| Header title | `LLB 2002` |
| Game code / maker | `ALCE` / `5L` (file utility prints `ALCE5L`) |
| Version | `0x00` (Rev.00), fixed byte `0x96` present, main-unit `0x00`, device `0x00` |
| Region / publisher / developer | USA / NewKidCo / Handheld Games ("Handheld Baseball Engine © 2002") |
| MD5 | `1923216a92a9d7b4640c39a37b6a612b` |
| SHA-1 | `8cc3da732100657568a684b27a3ed08d674e4bdb` |
| SHA-256 | `260d9cb9ddcf0e978141138b229107576c3111df8fc0ceec288a95db855ed5c2` |

**Phase 0 / image-integrity checks (all observed):**
- Entry word `0xEA00002E` → stock `0x080000C0` reset handler; no scene cracktro patch.
- Exactly **one** Nintendo-logo occurrence (file `0x4`); this is a single retail image, not a multiboot/double-pack.
- Size is exactly 2^23; final 1 MiB is uniform `0xFF` padding — no appended trainer.
- Header checksum fields are non-standard (`0xBD = 0xFD`, `0xBE..BF = 0x0000`; computed complements would be `0x16` / `0xFB19`). This is a common commercial-ROM artifact and is **not** evidence of a patch, given the stock entry branch and single logo.
- No patch/trainer signature found. No cheat device is required to play.

## 2. Executive summary

**Result: this game has no developer-intended cheat system.** There is no password screen, no password/cheat validator, no button-code sequence table, no hidden/debug menu reachable by controller input, and no unlockable content gated on controller input. Everything published for this title is a CodeBreaker/GameShark-style **memory patch** (out of scope). 3rd party cheat indexes have no in-game codes or guides for this SKU.

The negative is bounded, not assumed:

* All **13 reachable screens** in both English and Spanish were walked in mGBA and each was correlated to a distinct value of the screen-state byte at IWRAM `0x03000F00` (§7).
* The **entire 8 MiB** was searched case-insensitively: `password`, `cheat`, `secret`, `unlock`, `debug`, `code`, `hidden`, `bonus`, `master`, `invalid`, `enter code/password`, `gameshark`, `codebreaker`, `action replay` — **0 hits each**. Five classic password alphabets — **0 hits** (only `0123456789ABCDEF` occurs once, inside the C library `vfprintf` at ROM `0x086715C0`).
* Button-space: the only key-mask gate found in the input handler is `A|B|Start|Select` (`held & 0x0F == 0x0F`) at `0x08024EAE`, which calls `0x08027F94` — a **BIOS soft reset** (`svc 0x01`), not a cheat. 12 documented/speculative combos (Konami, L+R+Start, L+R+Select, L+R+A+B, L+R+Start+Select, Select+A, R+A+B, B+Start, held Start, Up+Down+Left+Right, A+B+Start+Select) were pressed on the language/title screens; none opened a hidden screen.
* A leftover **developer screen-name table** exists at `0x08038580` and `0x08038660` (12 named screens, including `"TEST TEXT"`). It is **dead data**: exhaustive raw-pointer, Thumb `LDR`-literal, Thumb `ADR` and u16-offset scans found **no code reference** to it (only self-references inside the table). No menu entry or gate reaches it. This is the "dead code / cut feature" case of guide §16.3, not a hidden menu.

## 3. How to reproduce

**Environment:** mGBA (Qt/SDL, `mgba -3 -g`), `Xvfb :317 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`. Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold each key 120–200 ms.

**Boot quirk (harness, not game):** with `-g`, this mGBA build sometimes parks the core at PC=0 with DISPCNT=`0x80` until a GDB client connects and detaches once; after that the game runs normally. This does not affect the ROM analysis. A GDB stub is also single-client and was blocked by other sessions, so savestate RAM diffing (§16.13) was used for all RAM evidence.

**Menu path (exact):**
1. Boot → copyright / Handheld Games / NewKidCo splashes → `Start` → Title (LLB 2002 logo).
2. `Start` → **Language Select** (English / Spanish).
3. `A` → **Game Setup**: START GAME / DIFFICULTY / INNINGS / ROSTERS / OPTIONS / CREDITS.
4. OPTIONS → **Game Options**: AUTO FIELDING / SOUND EFFECTS / MUSIC.
5. ROSTERS → **Team Roster**; CREDITS → scrolling credits; DIFFICULTY / INNINGS cycle with Left/Right.
6. START GAME → **Select Team** (HUMAN vs CPU, star ratings) → **Select Field** (3 fields) → **Pre-Game Menu** (PLAY BALL / BATTING ORDER / OPTIONS) → **Batting Order** → PLAY BALL → **in-game (batting / pitching / fielding)** → `Start` → **Paused** (MUSIC / SOUND FX / EXIT GAME).

**Codes tested:** none exist to test as in-game codes. The only published "codes" are 15 libretro CodeBreaker memory patches (e.g. `8300002E 00??` away score, `10024EA4 0007` enable) — these write RAM directly and are explicitly out of scope. No 3rd party cheat indexes in-game code was found or claimed.

## 4. Address map

| Address (ROM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Stock ARM reset entry (branch to `0x080000C0`) | Derived: header bytes |
| `0x08024D8C` | Keypad poller; reads `0x04000130`, computes held / pressed / released masks | Derived: disassembly |
| `0x08024EAE` | `(held & 0x0F) == 0x0F` gate → `0x08027F94` | Derived: disassembly |
| `0x08027F94` | Soft-reset helper (`svc 1`, `svc 0`) | Derived: disassembly |
| `0x080356CC` | Credits name strings (BRADLEY, SKALKA, FEINSTEIN, …) | Observed: strings |
| `0x08037B60` | English UI text bank (PLEDGE, OPTIONS, ROSTERS, teams/cities, …) | Observed + screenshot |
| `0x08038238` | Spanish UI text bank | Observed + screenshot |
| `0x08038580` | Developer screen-name table #1 (`{0x08, ptr}` × 10) | Derived: byte dump |
| `0x08038660` | Developer screen-name table #2 (`{ptr, 0x08}` × 12) | Derived: byte dump |
| `0x08038778` | `"TEST TEXT"` debug label | Observed: strings |
| `0x0803C500`–`0x0803C6B0` | Pointer table into the above string bank; **data**, not code | Derived: disassembly attempt produced pointer halfwords |
| `0x086715C0` | libc hex alphabet `0123456789abcdef` / `0123456789ABCDEF` (vfprintf) | Observed: strings |

| Address (RAM) | Meaning | Evidence |
|---|---|---|
| `0x03000420` | Held key mask, active-high (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`) | Derived: keypad poller stores `~KEYINPUT & 0x3FF` here |
| `0x03000410` | Just-pressed mask (`held & (held ^ prev)`) | Derived: same |
| `0x03000414` | Just-released mask | Derived: same |
| `0x03000F00` | Screen-state byte (see §7) | Observed: savestate correlation over 8 screens |

## 5. Algorithm

No password/cheat algorithm exists. The only input algorithm is the keypad decoder:

```
held     = ~KEYINPUT & 0x3FF
pressed  = held & (held ^ prev)
released = prev & (held ^ prev)
prev     = held
if (held & 0x0F) == 0x0F: BIOS_SoftReset()
```

Reimplemented in Python only for the static scanner (`buttonscan.py`, `keyscan.py`). Font/tile-index note: the in-game UI text **is plain ASCII** (the bank at `0x08037B60` renders verbatim on screen), so the "decode the tile-indexed text bank" caveat of guide §11 does not apply here; the ASCII keyword sweep therefore covers the visible text space.

## 6. Tables

* **Difficulty cycle (4 values, observed):** `T-BALL`, `MINORS`, `MAJORS` (MAYORES), `WORLD SERIES`. All four are legitimate menu settings; selecting any of them produced no hidden team, screen, or flag change.
* **Fields:** 3 selectable (default CHICAGO) — no hidden fourth field was found.
* **Screens named in dead developer table (12):** LANGUAGE SELECT, GAME SETUP, WORLD SERIES, SELECT TEAM, SELECT FIELD, PRE-GAME MENU, GAME OPTIONS, PAUSE MENU, TEAM ROSTER, BATTING ORDER, CREDITS, WORLD SERIES TEAM, plus `TEST TEXT`. All except `TEST TEXT`/`WORLD SERIES TEAM` correspond to real reachable screens; `WORLD SERIES` is a difficulty label, not a separate screen.

## 6b. Enumeration

Per §0.2, the "space" is formally empty for developer-intended cheats:

| Search space | Size checked | Result |
|---|---|---|
| ROM keyword/text space | 8,388,608 bytes × 17 keywords, case-insensitive | 0 hits for all cheat-related keywords |
| Standard password alphabets | 5 alphabet strings × 8 MiB | 0 hits (except libc hex alphabet, 1 hit) |
| Code-like ASCII runs | 7,469 candidate runs | all are credits names, UI labels, or city/team names; none is a password |
| Button-code tables (Konami prefix, L+R combos, 4-button combos), u8/u16/u32 + active-low encodings | 6 sequences × 4 encodings over 8 MiB | 0 plausible hits (1 coincidental byte hit at `0x08671FCE` in compressed graphics) |
| Key-mask gate branches (reads of held/pressed globals) | 1 raw `0x04000130` reference; 41 held-mask pool refs | 1 combo gate (`0x0F`) = soft reset; no cheat gate |
| Cross-references to debug screen-name table / `"TEST TEXT"` | raw pointer, Thumb LDR literal, Thumb ADR, u16 offset | 0 code references; table is unreachable developer data |
| Reachable screens | 13 (English + Spanish) | none offers a code entry, unlock, or debug menu |
| Published in-game codes | 3rd party cheat indexes/libretro | 0 in-game codes published; 15 CodeBreaker RAM patches (out of scope) |

**Novel code minted:** not applicable — there is no code system to enumerate. Per §0.2 this is a *proven negative* over the spaces above, not an untested assumption. Bounds are proven by (a) exhaustive literal/alphabet/pointer scans and (b) in-game rejection of every candidate input surface: the only input-accepting screen is the language selector, which accepts exactly English/Spanish, and every button combination tested either navigated normally or triggered the documented soft reset.

## 7. Validation evidence

**Observed (emulator / savestate RAM):**

| Screen | `0x03000F00` value | Screenshot |
|---|---|---|
| Game Setup (cursor ROSTERS) | `0x17` | `setupscreen.ss2`, `crop5.png` |
| Game Options | `0x18` | `opt.ss1`, `crop6.png` |
| Team Roster | `0x1C` | `rs_TEAM_ROSTER.ss8`, `crop8.png` |
| Select Team | `0x1D` | `rs_TEAMS.ss8`, `r_teams.png` |
| Select Field | `0x15` | `rs_SELECT_FIELD.ss8`, `r_field.png` |
| Pre-Game Menu | `0x0F` | `rs_PRE_GAME_MENU.ss8`, `r_pregame.png` |
| Batting Order | `0x12` | `rs_BATTING_ORDER.ss8`, `r_batord.png` |
| Paused (in-game) | `0x04` | `pause.ss5`, `pause.png` |

Language Select, Title, splashes, all 4 difficulty values, credits, the in-game batting view, and the Spanish variants were also captured (`lang.png`, `t5.png`, `t6.png`, `diffcycle.png`, `credits.png`, `credits2.png`, `ingame2.png`, `verify.png`). The screen-state byte taking a distinct value on 8 different screens is direct RAM evidence that each screen was actually reached.

**Derived (disassembly / byte dumps):** keypad poller and its three globals; the `0x0F` soft-reset gate; soft-reset helper at `0x08027F94`; screen-name tables and lack of xrefs; all literal/alphabet scan counts.

**Inferred (labelled):** that `0x03000F00` is a *screen ID* rather than a closely correlated UI variable — supported by 8 distinct stable values but not proven by a write-site analysis. It is used only as evidence of screen transitions, not as a cheat target.

## 8. Unknowns

* The exact purpose of the dead `TEST TEXT` / `WORLD SERIES TEAM` developer-table entries is unknown; no code path or caller reaches them. They are reported as dead/cut developer data, not as a hidden feature (§16.3).
* Saved-game persistence (the `.sav` created by mGBA is 0 bytes) was not required for any finding; no feature depended on it.
* The header checksum fields are non-standard; the reason (developer tooling) is not proven.
* The `0x2B` value adjacent to the developer table (`0x080386F4`) was not given a semantic label; it has no code reference.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 ... -M force-thumb` for keypad/input code.
* Python 3 + Capstone 5.0.7 for Thumb literal/ADR/BL scans.
* `strings -t x -n 3/4`, `grep`, `xxd`, `re` for text/keyword/alphabet sweeps.
* mGBA `-3 -g` under Xvfb `:317` + xdotool for screen walks; `scrot` + ImageMagick for captures.
* `ssram.py` / `ssdiff.py` / `findstate.py` — mGBA `.ssN` PNG `gbAs` zlib state extraction and diffing (guide §16.13). All analysis scripts were in `/tmp/llb2002/`.

**Legal:** no ROM image or copyrighted assets are reproduced here; only hashes, addresses, algorithms, and observations are published.
