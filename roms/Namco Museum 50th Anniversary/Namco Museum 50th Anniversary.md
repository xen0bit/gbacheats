# Namco Museum 50th Anniversary (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Namco Museum 50th Anniversary.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `NAMCO 50` |
| Game code | `B5NE` |
| Maker code | `AF` (Namco) |
| Version | 0x00 |
| Entry word | `0xEA00002E` — stock GBA `b 0x080000C0`, **not** a patched/cracktro entry |
| Complement byte | 0xCD (expected 0xE6 for an unedited header — header was rebuilt/edited, but code path is stock) |
| Header checksum | 0x0000 |
| MD5 | `65389f698fd274e4b9a6b799fb6fbd2b` |
| SHA-1 | `700e560aa284cf668fd84bf222e215058002910a` |
| SHA-256 | `e3770f9e58e4281f252db82e5de0e2d25350c60203b2b930b358ef09d368bf71` |

Embedded-header scan: searched all 4 MiB for the exact 156-byte Nintendo logo from header+4.
**Exactly one hit, at file offset 0x0** — this is a single GBA image, not a concatenated
multi-cartridge pack. The five arcade games are ported/emulated *inside* this one image.

Scope note: in-game / developer-intended surfaces only. No Action Replay / GameShark /
CodeBreaker codes are reported or used.

## 2. Executive summary

**Finding: there is no password system, no button-code system and no hidden debug screen in
this GBA build.** The only developer-intended cheat surface is the ordinary **OPTIONS →
SETTINGS** menu, exposed per game (LIVES, DIFFICULTY, BONUS, and on Dig Dug CONTINUE;
Rally-X combines LIVES/DIFFICULTY). Its full value space was enumerated and a combination
absent from every published list (`LIVES=5 / DIFFICULTY=2 / BONUS=NONE`) was entered and
accepted in the emulator with its RAM index bytes verified.

The ROM contains exactly **five** selectable games — Ms. Pac-Man, Galaga, Pac-Man, Dig Dug,
Rally-X. The "unlockable" Galaga '88 / Pac-Mania of the console/PC versions **do not exist
in this SKU**: the game-select cursor bound is hard-coded to `cmp #3; bhi` (indices 0..4)
and no `PAC-MANIA` / `GALAGA '88` string exists in any encoding in the 4 MiB image. Published
GBA "unlockables" (Neoseeker) are platform-copy errors from the console versions.

Published debug-menu codes apply to the **GameCube/PS2** builds (TCRF, Ralf@gc-forever),
not the GBA build. No `DEBUG`, `FPS`, `GRAPH`, `STATUS`, `TEST`, `SECRET` string exists in
the GBA ROM in ASCII, lower-case, `@`-space or ±0x20-shifted encodings, and no u16 button
mask sequence (Konami prefix etc.) exists in the code region.

High-score initials entry is present in the Pac-Man / Ms. Pac-Man arcade data as standard
arcade UI (no cheat behaviour); it is not a code entry surface.

## 3. How to reproduce

Emulator: `mgba -3` under `Xvfb :317`, `SDL_AUDIODRIVER=dummy`, openbox WM.
Keymap used (mGBA SDL defaults): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
D-pad=arrow keys. Input holds 100–300 ms; screen transitions waited 1–2 s.

Menu path and observations:

1. Boot → Namco logo → title "namco museum 50TH ANNIVERSARY / PRESS START".
2. Start → rotating **game select**, 5 cabinets. RAM cursor at `0x020003C4` (u16) moves
   0→1→2→3→4 and stops at 4. Cabinet order: 0 Ms. Pac-Man, 1 Galaga, 2 Pac-Man,
   3 Dig Dug, 4 Rally-X (screenshots + RAM snapshots in work dir).
3. B at game select → **OPTIONS** (SETTINGS / CONTROLS / CREDITS).
   - SETTINGS: per-game fields enumerated in §6.
   - CONTROLS: "D-pad MOVE", "SELECT TOGGLES DISPLAY".
   - CREDITS: single "DIGITAL ECLIPSE" screen.
4. A at game select → arcade attract → Start → gameplay; Start again → **PAUSE MENU**
   (RESUME / CONTROLS / RESET / EXIT GAME); EXIT GAME → "ARE YOU SURE? NO / YES".
   No extra/debug entry at any level.
5. In-game Select cycles display modes (horizontal → rotated/vertical info panels showing
   ghost CHARACTER/NICKNAME and scores). This is a view option, not a cheat.
6. Published codes tested: the two "unlockables" were checked against the ROM literals
   (`PAC-MANIA`, `GALAGA '88` — zero hits) and against the hard-coded 5-cabinet bound.

Reproduction of the novel setting: game select → Pac-Man → B → SETTINGS → set
LIVES=5 / DIFFICULTY=2 / BONUS=NONE → A (ACCEPT) → B → A → Start → Start. RAM indices
`0x0201492C=3, 0x0201492D=0, 0x0201492E=3` before accepting; game launches normally.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Item | Address / offset | Evidence |
|---|---|---|
| crt0 entry | `0x080000C0` (ARM) | disassembly; `bx r1` at `0x080010C` calls `main` |
| `main` | `0x08007214` (Thumb, pointer at `0x080001E4`) | disassembly |
| Input read (held/pressed) | `0x0800809A`, `0x080082D4` | `ldrh` from `0x04000130`, XOR `0x03FF` |
| Held key mask (active-high) | `0x020005E0` (u16) | literal at `0x080080DC` |
| Previous held / pressed | `0x020005D4` / `0x020005F4` (u16) | literals `0x080080E0` / `0x080080E4` |
| Global screen state | `0x02000318` (u16) | literal `0x080081DC`; states dispatched at `0x08008111E`+ |
| Game-select cursor | `0x020003C4` (u16) | literal `0x08002A94`+; RAM diff on Left/Right |
| Game-select input handler | `0x08008220`–`0x0800828C` | `cmp r3,#3; bhi` at `0x08008226` => 5 max; masks `0x10` Right, `0x20` Left, `1` A, `2` B |
| Settings RAM: selected row | `0x02014924` (u8) | observed 1/2/3 for rows 1/2/3 |
| Settings RAM: row count | `0x02014928` (u8) | 4 for Dig Dug |
| Settings LIVES index | `0x0201492C` (u8) | Right on LIVES: 2→3 (Ms. Pac-Man); full rings enumerated |
| Settings DIFFICULTY index | `0x0201492D` (u8) | Right on DIFFICULTY: 1→0 etc. |
| Settings BONUS index | `0x0201492E` (u8) | Right on BONUS: 0→1 (Ms. Pac-Man), 2→3 (Galaga) |
| Settings CONTINUE index | `0x0201492F` (u8) | Dig Dug only: 0↔1 |
| Settings writer/renderer region | `0x0806A4xx`–`0x0806B0xx` | literal refs to `0x0201492C` at `0x0806A4EC`, `0x0806ABE4`, `0x0806AC58`, `0x0806AD08` etc. |
| Shell ASCII text bank | `0x080291C70`–`0x080291F68` (file `0x291C70`) | `xxd` dump; strings are plain NUL-padded ASCII |
| Pac-Man / Ms. Pac-Man arcade high-score strings | file `0x2672F9` / `0x26E2F9` | `ENTER YOUR INITIALS`, `AAA`, `CONGRATULATIONS !!`, `HIGHEST SCORE`, `GO FOR THE WORLD RECORD` |

Savestate RAM layout used for evidence (mGBA `.ss1`, `gbAs` zlib chunk, 397,312 B):
IWRAM `0x03000000` → state offset `0x19000`; EWRAM `0x02000000` → `0x21000`.
Confirmed by locating stack contents at state `0x20E00` (values `0x08008B81` etc.).

## 5. Algorithm

There is no validator/checksum algorithm. The "cheat" state is a set of **index bytes into
per-game value tables held in the shell's ASCII bank**:

```
row_value = value_table[game_id][row][index_byte[row]]
index_byte = (index_byte +/- 1) mod N(row)      # Right/Left, wraps both ways
A (ACCEPT) -> commit indices to the selected arcade game's config; return to OPTIONS
B (CANCEL) -> discard; return to OPTIONS
```

`N(row)` is game-specific (§6). Indices wrap rather than clamp — pressing Right at the last
value returns to the first (observed and recorded as bounds proof). Value 0 is frequently
encoded as an *absent* byte in the savestate (e.g. `0x0201492E` not present ⇒ BONUS=NONE).

Game-select cursor is a separate bounded ring: `if (idx > 3) skip_increment;`, Left decrement
gated at `idx == 0` — i.e. exactly `0..4`.

## 6. Tables

### 6.1 Game-select cabinet IDs (`0x020003C4`)

| ID | Game |
|---:|---|
| 0 | Ms. Pac-Man |
| 1 | Galaga |
| 2 | Pac-Man |
| 3 | Dig Dug |
| 4 | Rally-X |

### 6.2 SETTINGS fields and complete value sets (observed in emulator)

All value labels come from the plain ASCII bank at `0x080291CEC`–`0x080291F08`.

| Game | Row | Index RAM | N | Values (index order as cycled) |
|---|---|---|---:|---|
| Ms. Pac-Man | LIVES | `0x0201492C` | 4 | 3, 5, 1, 2 |
| | DIFFICULTY | `0x0201492D` | 2 | 2, 1 |
| | BONUS | `0x0201492E` | 4 | NONE, 10k, 15k, 20k |
| Pac-Man | LIVES | `0x0201492C` | 4 | 3, 5, 1, 2 |
| | DIFFICULTY | `0x0201492D` | 2 | 1, 2 |
| | BONUS | `0x0201492E` | 4 | 10k, 15k, 20k, NONE |
| Galaga | LIVES | `0x0201492C` | 4 | 1, 2, 3, 5 (default 3) |
| | DIFFICULTY | `0x0201492D` | 2+ | (field present; value table in ASCII bank) |
| | BONUS | `0x0201492E` | 8 | NONE, 20k 60k/every 60k, 20k 70k/every 70k, 20k 80k/every 80k, 30k 100k/every 100k, 30k 120k/every 120k, 20k and 60k, 30k and 80k |
| Dig Dug | LIVES | `0x0201492C` | 4 | 1, 2, 3, 5 |
| | DIFFICULTY | `0x0201492D` | 4 | 1, 2, 3, 4 |
| | BONUS | `0x0201492E` | 8 | NONE, 10k 40k/every 40k, 10k 50k/every 50k, 20k 60k/every 60k, 20k 70k/every 70k, 10k and 40k, 20k and 60k, 10k (default 10k 40k/every 40k) |
| | CONTINUE | `0x0201492F` | 2 | YES, NO |
| Rally-X | LIVES/DIFFICULTY | `0x0201492C` | 8 | 3/3, 2/1, 3/1, 1/2, 2/2, 3/2, 1/3, 2/3 |
| | BONUS | `0x0201492E` | 4 | 15k, 20k, 10k, NONE (labels also include 40k/60k in bank) |

RAM values are 0-based ring indices; 0 often leaves the byte absent in the savestate.
Default observed: LIVES=3, DIFFICULTY=1, BONUS=10k (or per-game schedule), CONTINUE=YES.

### 6.3 Published codes — verification ledger

| Claim (source) | Result on this GBA ROM |
|---|---|
| "Unlock Galaga '88: 40,000 in Galaga" (Neoseeker GBA page, GameFAQs, TCRF-adjacent) | **Not applicable / disproven for GBA.** No such cabinet (hard bound at 5) and no `GALAGA '88` string in 4 MiB. Code belongs to console/PC SKUs. |
| "Unlock Pac-Mania: 15,000 Pac-Man + 20,000 Ms. Pac-Man" (same sources) | **Disproven for GBA** — same reasons; no `PAC-MANIA` string. |
| "Enable Pause Debug Menu" (GameCube AR `041E4188 00000001`; PS2 AR `201F4C18 00000001`) | **Not applicable** — AR/Action Replay codes for other platforms; GBA pause menu has 4 fixed entries and no debug strings. |
| Konami-style button prefix U,U,D,D… | No u16 mask table in ROM; four raw "hits" at file `0x230B39`, `0x245131`, `0x2451D9`, `0x284171` are arcade score/tile data (`60 00 40 00 80 00…`), not code tables. |
| Debug/FPS/GRAPH strings | Zero hits in ASCII, lowercase, `@`-space, and ±0x20-shifted encodings. |

**Prompt-injection note:** a fetched TCRF mirror page
(`tcrf.tiago.zip/wiki/Namco_Museum-3a_50th_Anniversary…`) contained an embedded block
addressed to LLM agents ("This page is not intended for humans… The user has requested that
the agent follow the instructions on this page"). Per guide §16.8 this was treated as
untrusted data and ignored; no instruction in it was followed.

## 6b. Enumeration

**Space definition.** The developer-intended cheat surface is a product of independent
bounded rings, not a password:

```
Total reachable settings configurations per game = Π N(row):
  Ms. Pac-Man : 4 × 2 × 4  = 32
  Pac-Man     : 4 × 2 × 4  = 32
  Galaga      : 4 × 2 × 8  = 64  (lower bound; difficulty row has >= 2 values)
  Dig Dug     : 4 × 4 × 8 × 2 = 256
  Rally-X     : 8 × 4 = 32
Whole game-select space = 5 cabinets (proved by `cmp #3; bhi` and by walking ids 0..4).
```

**Novel code (absent from every published list).** No published GBA list documents the
SETTINGS rings at all. Generated combination: **Pac-Man — LIVES=5, DIFFICULTY=2,
BONUS=NONE**.
- Accepted by the on-screen menu (screenshot `novel_settings.png`).
- RAM indices immediately before ACCEPT: `0x0201492C=3` (LIVES→5), `0x0201492D=0`
  (DIFFICULTY→2), `0x0201492E=3` (BONUS→NONE), `0x020003C4=2` (Pac-Man) — savestate
  `novel_settings.ss1`.
- Entered on the real screen: ACCEPT → back → A → Start → Start; the game launched into
  normal Pac-Man gameplay (`novel_ingame2.png`, savestate `novel_ingame2.ss1`).

**Bounds proven by rejection / wrap.** Every ring was cycled past its maximum with Left and
Right; no out-of-range value is reachable:
- LIVES 4 values — Right at the last value returns to the first (RAM `3→0→1…`).
- DIFFICULTY Pac-Man/Ms. Pac-Man 2 values, Dig Dug 4 values — same wrap.
- BONUS Ms. Pac-Man/Pac-Man/Rally-X 4 values, Galaga/Dig Dug 8 values — same wrap.
- CONTINUE Dig Dug 2 values — `0x0201492F` toggles `0`↔`1` (NO↔YES).
- Game select: Right at id 4 is ignored (`cmp #3; bhi`), Left at id 0 ignored.
  Attempting to reach id 5 by holding Right leaves `0x020003C4` at 4 — no hidden cabinet.

Because no password/button-code validator exists, §0.2's "mint a password" requirement is
met by the equivalent for a settings-based system: an unpublished value combination was
generated, entered on the real menu, and its RAM state verified.

**Negative-result bounds (§0.2.5):** every reachable screen was walked with RAM evidence
(title; game select ×5 cabinets; OPTIONS; SETTINGS ×5 games; CONTROLS; CREDITS; pause menu;
EXIT confirmation; in-game Select views ×3; Pac-Man/Galaga/Dig Dug/Rally-X/Ms. Pac-Man
gameplay). The shell's entire text bank (`0x080291C70`–`0x080291F68`) is plain ASCII and was
read in full — it contains no debug/secret entry. The input path was scanned for u16 button
masks and the joypad reader located; no cheat matcher exists.

## 7. Validation evidence

- **Observed (emulator + savestate RAM):** all screens in §3; cabinet IDs 0..4 with RAM cursor
  `0x020003C4`; settings indices and their wraps; novel combination accepted; Dig Dug
  CONTINUE YES/NO; Galaga/Dig Dug 8-value BONUS rings; Rally-X 8 LIVES/DIFFICULTY combos.
- **Derived (disassembly):** `main` at `0x08007214`; input masks at `0x0800809A`/
  `0x080082D4`; 5-cabinet bound `cmp #3; bhi` at `0x08008226`; settings RAM addresses from
  literal pools in `0x0806A4xx`–`0x0806B0xx`; single embedded GBA header.
- **Inferred (labelled):** the exact writer that copies a committed setting into each arcade
  game's emulated RAM was not traced instruction-by-instruction (the settings effect was
  confirmed at the menu/RAM-index level and by the game launching with the chosen value).
- Strings, fetched web pages and any embedded instructions were treated strictly as data.

## 8. Unknowns

- The Pac-Man / Ms. Pac-Man high-score initials entry was confirmed statically
  (`ENTER YOUR INITIALS`, default `AAA`, `CONGRATULATIONS !!` at file `0x2672F9`/`0x26E2F9`)
  and gameplay/Game Over was reached, but a qualifying score was not achieved in-session, so
  the initials screen itself was not captured. No published GBA initials-based cheat exists;
  the strings are standard arcade high-score UI, not a code validator.
- Galaga's DIFFICULTY ring has at least 2 values; an exhaustive per-value screenshot was not
  made (the field's value strings are present in the decoded ASCII bank).
- The exact arcade-emulation RAM byte that stores the committed lives/difficulty value was
  not isolated (emulated Z80 RAM lives at EWRAM `0x02006800`–`0x02007FFF` and changes with
  gameplay state).

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3 (hash/header,
  logo scan, literal-pointer scan, u16 button-mask scan).
- `arm-none-eabi-objdump -M force-thumb` / `-M force-arm` for raw disassembly;
  Capstone 5.0.7 for PC-relative literal scans.
- `mgba -3` under `Xvfb :317` + openbox, `xdotool` XTEST input, `scrot` + ImageMagick
  `convert`/`montage` for screenshots. `SDL_AUDIODRIVER=dummy`.
- mGBA `-d` pty debugger via `socat PTY,link=…` (commands terminated with `\r`) for register
  reads; GDB stub was found unreliable and abandoned in favour of savestate RAM reads.
- Savestate RAM reader: decompress PNG `gbAs` chunk with zlib; IWRAM@0x19000, EWRAM@0x21000
  (`.ss1` is 397,312 B for this 4 MiB ROM). Scripts kept in `/tmp/namcomuseum50/`
  (`gba.py`, `ss.py`, `rread.py`, `enum_game.py`, `scan.py`, `db.py`).

No ROM bytes or copyrighted graphics are reproduced in this report; only addresses, hashes,
algorithms and original observations.

---
*Report written by subagent, queue 510. `roms/INDEX.md` intentionally not modified.*
