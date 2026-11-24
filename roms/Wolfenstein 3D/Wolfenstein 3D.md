# Wolfenstein 3D (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Wolfenstein 3D.gba` (8,388,608 bytes / 0x800000) |
| Header title | `WOLF3D` |
| Game code / maker | `AWOE` / `6L` (Stalker Entertainment port; "boom!" and id Software splashes) |
| Version | 0x00; fixed byte 0x96; complement 0xF4; header checksum 0x0000 |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0` (retail image, no cracktro) |
| MD5 | `821e6ee7197d8b7aac69aea82509e93a` |
| SHA-1 | `4cf7b70807e8de6472844ea260fc4c48c879134a` |
| SHA-256 | `cf327148ace896adc624451edbd7c2ca1da9c1ac8746a22d8085edfc510b5c65` |

A byte-identical working copy was analysed in `/tmp/wolfenstein/game.gba` (same MD5). No ROM or game asset is reproduced here.

## 2. Executive summary

The only developer-intended cheat surface in this SKU is a **pause-menu button-code system**: while the in-game `Options` menu is open, hold **L+R** and press an eight-button sequence of **A/B**. The validator at `0x0800131C` compares an eight-entry circular buffer against a five-record table at ROM `0x083B5A9E`. The space is exactly 2^8 = 256 A/B sequences, of which **5** are accepted. Four match the published lists; the fifth, **`A A B A B B B B`**, is absent from every list consulted and is a real, reachable code: it switches the "invulnerable/god" flag at `0x0200B250` back **off** (the complement of the published `AABAAAAA`). It was entered on the real pause screen and verified both in RAM (flag 1 → 0) and by its unique acceptance signature (input buffer cleared, unlike rejected inputs).

There is **no password-entry screen** in this build. The `PASSWORD`, `NEW PASSWORD`, `SINGLE-PLAYER` / `MULTI-PLAYER` and debug strings (`INVULNERABLE`, `GOTO LEVEL`, `CYCLE CAMERA`, `PRINT`, `COLLISION`, `TIMING`) at `0x087B19AE`–`0x087B2080` are unreferenced PC-engine leftovers: the pointer table that addresses them (`0x087A4948`) has zero code-region xrefs, the individual strings have zero Thumb `LDR` literal xrefs, and the actual GBA UI text bank at `0x087DA930` contains no password label. Every reachable screen was walked (§7).

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* SDL keymap used: **A = `x`**, **B = `z`**, **L = `a`**, **R = `s`**, Start = `Return`, D-pad = arrow keys.
* Route: boot → title → Start through two credit screens → `Options` → `New Game` → episode 1 → difficulty "Bring 'em on!" → gameplay → **Start** to open the in-game `Options` menu (the cursor rests on `New Game`; `Back to Game` is highlighted in yellow but is *not* the cursor).
* Code entry: hold `a`+`s` (L+R), tap the A/B sequence with ~90 ms holds and ~90 ms gaps, release L+R. A successful code plays a distinct confirmation sample and clears the input buffer; the effect applies when you select `Back to Game` (cursor: press `Up` once from `New Game`, then `A`).
* A pristine savestate of the pause menu was kept as `base.ss1` in `/tmp/wolfenstein/`; every test below was run by reloading it (mGBA `F1`) and re-saving (`Shift+F1`) to an independent file.
* Codes tested (all with L+R held): `AABAAAAA`, **`AABABBBB`** (novel), `ABAABBBA`, `ABAABBAA`, `ABBAAAAA`, `AAAAAAAA` (reject), `AABABBBA` (near-miss reject).

## 4. Address map

| Address (ROM / file) | Purpose |
|---|---|
| `0x0800131C` / `0x00131C` | Button-code validator (`thumb`) |
| `0x0800C620`, BL at `0x0800C63E` | Sole caller — pause/Options menu input handler |
| `0x08002FEC`, `0x08002FF8` | Input helpers: `pressed` (u16 @ `0x02017878`), `held` (u16 @ `0x0201787A`) |
| `0x083B5A9E` / `0x003B5A9E` | Five 8-byte code records (`0x01`=A, `0x02`=B), terminated by `00 00` at `0x003B5AC6` |
| `0x087DA930` / `0x003DA930` | Actual GBA UI text bank ("Which episode to play?", save/load prompts, …) |
| `0x087B1980`–`0x087B2080` / `0x003B…` | Unused PC-engine text bank incl. `PASSWORD`, debug labels |
| `0x087A4948` / `0x007A4948` | Pointer table into that unused bank (no code xrefs) |
| RAM `0x020178BC` (8 bytes) | Circular A/B press buffer (code 0/1/2 per slot) |
| RAM `0x020178C4` (u16) | Buffer write index, masked `& 7` |
| RAM `0x02017878` / `0x0201787A` | Edge-triggered `pressed` / level `held` key masks |
| RAM `0x0200B250` (u32) | Invulnerable/"god" flag: 0 off, 1 on |
| RAM `0x0200CFC4` (u32) | Deferred game-action word (1 next level, 4 boss warp, 9 next episode/level) |
| RAM `0x0200B0D0` +2 / +4 | Player level / episode |
| RAM `0x0200B0D0` +0x12 / +0x14 / +0x16 | Health / ammo / lives |

Savestate RAM mapping (for reproduction with the diff method): raw `gbAs` state `0x21000 + (addr − 0x02000000)`.

## 5. Algorithm

Validator `0x0800131C`, reimplemented exactly:

```text
held    = *(u16*)0x0201787A          # active-high: A=1 B=2 … R=0x100 L=0x200
pressed = *(u16*)0x02017878          # held & ~previous_held (edge triggered)
if (held & 0x300) != 0x300: return 0        # L AND R must both be down
if pressed == 0: return 0
code = 1 if (pressed & 0x001) else (2 if (pressed & 0x002) else 0)   # A wins ties
if code == 0: return 0
buf = (u8*)0x020178BC ; idx = *(u16*)0x020178C4
buf[idx] = code ; idx = (idx + 1) & 7 ; *(u16*)0x020178C4 = idx
for each of the 5 records T at 0x083B5A9E:
    if all(buf[(idx + i) & 7] == T[i] for i in 0..7):     # oldest-first
        memset(buf, 0, 8)                                 # acceptance signature
        apply effect (below) ; play sound id ; return message id
return 0
```

The comparison starts at the *current write index*, which holds the oldest of the last eight presses. This was confirmed from the rejected near-miss buffer: with `idx=7` the physical slots `01 02 01 02 02 02 01 01` read circularly from slot 7 reconstruct `A A B A B B B A` exactly.

Effect per record:

| # | Code | Effect (from disassembly) | Distinct sound id |
|---|---|---|---|
| 0 | `AABAAAAA` | `*(u32*)0x0200B250 = 1` (invulnerable ON), returns 0x2B | 143 |
| 1 | **`AABABBBB`** | `*(u32*)0x0200B250 = 0` (invulnerable OFF), returns 0x2F | 147 |
| 2 | `ABAABBBA` | Level/episode advance; if level is last in episode → episode++, action = 9, else action = 1; returns 0x28 | 30 |
| 3 | `ABAABBAA` | level = 8 (floor 9), action = 4; returns 0x31 | 149 |
| 4 | `ABBAAAAA` | health = 100, ammo = 99, lives = 3, score = 0, weapon mask OR `0x0000A410`, 3 keys; returns 0x28 | 32 |

Other notes: A and B are edge-triggered; if both are pressed in one frame A wins. Keys other than A/B are never written to the buffer, so they cannot form a code. The only gate besides L+R is the eight-slot comparison itself — there is no save/progress gate (the code handler runs from the pause menu in a fresh game).

## 6. Tables

Published lists consulted (all as "hold L+R, press …"): 3rd party cheat indexes (4 codes: God `AABAAAAA`, Level Skip `ABAABBBA`, All Weapons `ABBAAAAA`, Warp to Boss `ABAABBAA`), World-of-Nintendo (All Weapons, Level Skip, Advance-to-Boss), 3rd party cheat indexes snippet (God Mode). AAA-CheatCodes listed God/Weapons/Skip without sequences. **None lists `AABABBBB`.**

Code table at file `0x003B5A9E` (ROM `0x083B5A9E`), five 8-byte records:

```
0x3B5A9E  01 01 02 01 01 01 01 01   AABAAAAA   invulnerable ON   (published)
0x3B5AA6  01 01 02 01 02 02 02 02   AABABBBB   invulnerable OFF  (NOVEL)
0x3B5AAE  01 02 01 01 02 02 02 01   ABAABBBA   level/episode skip (published)
0x3B5AB6  01 02 01 01 02 02 01 01   ABAABBAA   warp to boss      (published)
0x3B5ABE  01 02 02 01 01 01 01 01   ABBAAAAA   all weapons/ammo  (published)
0x3B5AC6  00 00                      terminator
```

## 6b. Enumeration

**Space definition.** One symbol per press drawn from {A, B}; length fixed at 8; each press stored as 1 (A) or 2 (B); L+R is a hold-gate, not part of the alphabet; no checksum, no reserved bits, no length variants. Representable inputs = 2^8 = **256**.

**Closed set, proven two ways.** (1) Static: the table has exactly five records followed by a `00 00` terminator, and the validator contains exactly five comparison branches with literal pointers to those five records (`0x080013AC/B0`, `14A4/A8`, `168C`). (2) Exhaustive offline replay of the comparison over all 256 sequences (`enumerate.py`): exactly **5** accepted — `AABAAAAA`, `AABABBBB`, `ABAABBAA`, `ABAABBBA`, `ABBAAAAA` — and 251 rejected. This is a closed enumeration of the validator's own predicate, not an inference from the table alone.

**Novel code (absent from every published list): `A A B A B B B B`** — hold L+R, press A,A,B,A,B,B,B,B on the pause menu. It is record 1 at `0x083B5AA6`, in no consulted list, and is not an alias of another code (distinct payload, distinct sound id 147, distinct return 0x2F).

In-game proof (pause-screen entry, savestate-evidenced):

| Test | Sequence | god flag `0x0200B250` | buffer `0x020178BC` | Other observed change |
|---|---|---|---|---|
| base | — | `00000000` | `00000000` | — |
| god on | `AABAAAAA` | `01000000` | cleared to 0 | — |
| **novel after god on** | `AABAAAAA` then **`AABABBBB`** | `00000000` | cleared to 0 | **flag 1 → 0** |
| novel alone | `AABABBBB` | `00000000` (already 0) | **cleared to 0** | acceptance signature present |
| reject | `AAAAAAAA` | `00000000` | `01010101` (not cleared) | none |
| near-miss | `AABAAAAA` then `AABABBBA` | `01000000` (stays 1) | `0102010202020101` (not cleared) | none |

Published codes, independently verified from the pristine base state: `ABBAAAAA` → ammo 8 → 99, HUD shows machine gun (`play_weapons.png`); `ABAABBAA` → level 0 → 8, HUD shows FLOOR 9 (`play_boss.png`); `ABAABBBA` → action word 0 → 9; `AABAAAAA` → god flag 0 → 1.

**Bounds proven by rejection.** `AAAAAAAA` is a checksum/format-valid A/B input (correct alphabet and length) but is not in the table: the game left the buffer filled with `01×8` and changed no flag. The one-bit-off near-miss `AABABBBA` likewise left a non-zero, un-cleared buffer and did not clear the god flag. Because the only acceptance criterion is the eight-slot comparison, these establish the 5-of-256 bound: no other A/B sequence can be accepted, and non-A/B keys cannot enter the buffer at all.

## 7. Validation evidence

**Observed** (emulator / savestate RAM): all rows of the §6b table; the weapon HUD (`play_weapons.png`), boss floor 9 (`play_boss.png`), the pause menu and all its sub-screens (`screen_graphics2.png` brightness, `screen_control2.png` turn acceleration, `screen_loadgame2.png` four empty save slots), title/credits/episode/difficulty screens (`shot_title.png`, `shot_menu1.png`, `shot_menu2.png`, `shot_newgame.png`, `shot_difficulty.png`, `shot_ingame.png`, `shot_pause.png`). Screenshots and `.ss1` evidence were in `/tmp/wolfenstein/`, outside the ROM folder.

**Derived** (disassembly): validator control flow, table contents, input semantics (edge-triggered A/B, held L+R gate), effect writes and sound IDs, absence of code-region xrefs to the `PASSWORD` text bank and its pointer table.

**Inferred**: that `0x0200B250 = 1` is "invulnerable on" and `0` is "off" (consistent with the published label for `AABAAAAA` and with the exact complement code); that action values 1/4/9 mean next-level/boss/next-episode (the dispatcher at `0x080096A0` handles 1 and 9; 4 is set together with level 8 and visually yields FLOOR 9). The confirmation feedback is audio-only, so no visual rejection message was available under `SDL_AUDIODRIVER=dummy`.

**Screen walk / negative result.** Reachable screens: boot splash → title → id Software credits → Stalker credits → Options (New Game / Graphics / Control / Load Game / Back to Game) → episode select (6 episodes) → difficulty (4 levels) → "Get Psyched!" → gameplay → pause Options → Graphics, Control, Load Game. None offers a password/keyboard entry. The 0x3DA930 UI bank was decoded in full for this range; the only `PASSWORD` strings live in the unused 0x7B19xx bank whose pointer table has zero code xrefs. This is a **no-system** negative, bounded by the complete screen walk plus decoded text banks, not "not looked for".

## 8. Unknowns

* The u16 array `0x003B5A8C` = `{3,4,5,6,7,8,0xB,0x11,0x23}` immediately before the code table has no xref in the validator; its meaning (possibly level/par data) is unresolved.
* The exact game-side consumer of action value 4 was not isolated; its effect (boss floor) is established by RAM + screenshot, not by naming the dispatcher case.
* The buffer index advances modulo 8, but the observed delta after an eight-press code was not exactly 8; the extra increments were not attributed (they do not affect acceptance or the effect writes).
* The exact meaning of sound IDs 30/32/143/147/149 (shout, door, siren, …) was not verified by listening; only their distinctness in code is established.

## 9. Tooling

`strings -t x`, `grep -abo`, `xxd`, `arm-none-eabi-objdump -M force-thumb`, Python `struct`/Capstone-style literal & BL scans, mGBA 0.10.5 under Xvfb :316 + openbox with `SDL_AUDIODRIVER=dummy`, `xdotool` XTEST input, `import`/`scrot` screenshots, mGBA `Shift+F1`/`F1` savestates, and a Python PNG `gbAs` zlib extractor (`ss.py`) for RAM diffs. Scripts kept in `/tmp/wolfenstein/`: `find_codes.py`, `parse_table.py`, `analyze_validator.py`, `xrefs.py`, `enumerate.py`, `ss.py`, `rebuild_ss.py`, `runtests.py`, `code_and_play.py`.

The mGBA GDB stub was unusable ("Ignoring packet error", memory reads failed), so all RAM evidence came from diffing decompressed savestates (guide §16.13).

## 10. Legal note

No ROM image or copyrighted asset is distributed with this report. All findings are addresses, hashes, algorithms and independently generated button sequences.

---

*Cleanup: all processes started for this job were stopped by PID and no `.sav`/`.ss*` files were left in the ROM folder.*
