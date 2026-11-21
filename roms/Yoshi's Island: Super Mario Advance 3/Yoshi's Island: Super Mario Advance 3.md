# Yoshi's Island: Super Mario Advance 3 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Yoshi's Island: Super Mario Advance 3.gba` (4,194,304 bytes = 4 MiB) |
| Header title (USA half, `0x00`) | `SUPER MARIO` — game code `A3AE`, maker `01`, rev `0x00`, fixed byte `0x96` |
| Second header | `0x12FDC0` (ROM `0x0812FDC0`) — `SUPER MARIO`, code `A3AJ` (Japan), rev `0x00` |
| Entry word | `0xEA00002E` (stock crt0; no cracktro/trainer observed) |
| `file(1)` | `Game Boy Advance ROM image: "SUPER MARIOC" (A3AE01, Rev.00)` |
| MD5 | `bb09508c782f37934c9519c5f8a7350c` |
| SHA-1 | `7352d2bd064d9ebaec579e264228aa21c7345b80` |
| SHA-256 | `a8bb331a6f0ff7af4387df9ac8566ae395863c2f79a5a597528a64c8bff57941` |

Dual-region image: a USA (`A3AE`) image based at `0x08000000` and a Japanese
(`A3AJ`) image whose header sits at file `0x12FDC0` (base `0x0812FDC0`).
All addresses below are for the **USA half** unless stated. A literal scan of
the whole 4 MiB for the button-code mask sequence found exactly one hit, in the
USA half; the Japanese half has no separate copy of that table.

## 2. Executive summary

This game has **one developer-intended in-game cheat**: a five-press button code
entered on the world-map / stage-select screen — hold **Select** and press
**L, L, B, A, R**. It toggles the "Bandit Mini-Games" selection interface.

The code is not a password system. There is no on-screen alphabet, no text
entry, no string table of accepted codes and no password validator. The only
validator in the image is a fixed button-mask matcher (§5). It is implemented as
two parallel `u16` tables: one holds the button that must be pressed at each
step, the other holds the *exact* active-high key mask required at that step.
The whole space is therefore **one accepted sequence** — there is no field to
vary and no novel code to mint (§6b).

The code is **scene-gated**: its only caller is the stage-select/world-map input
handler at `0x08007914`, and a non-zero byte at `gameState+0xCBE` suppresses it.
Success toggles `gameState+0x16F4`, sets `gameState+0xCBD = 7`, clears
`gameState+0xCBE`, resets the step counter and plays sound `0x21`.

On acceptance the game shows the mini-game selection screen. On a fresh file
that screen is not reachable quickly (the map/stage-select gate requires game
progress), so the in-game acceptance was **not** observed in this engagement;
this is stated explicitly rather than inferred (§7, §8). The code was entered on
a reachable gameplay screen and produced no mini-game transition, which is the
expected rejection outside the gated scene.

Everything published about this game's in-game codes agrees with one 5-press
sequence; the widely copied SNES variant `Select + X,X,Y,B,A` belongs to the
SNES release, not this GBA image, and the malformed GBA variant `L,L,B,R,R`
found on one fan site is contradicted by the ROM bytes.

## 3. How to reproduce

### Static
```bash
ROM="Yoshi's Island: Super Mario Advance 3.gba"
md5sum "$ROM"; sha256sum "$ROM"
strings -t x -n 4 "$ROM" | grep -iE 'password|cheat|debug|select'   # no hits
# exact button masks, read as u16 little-endian:
python3 - <<'PY'
import struct
r=open("Yoshi's Island: Super Mario Advance 3.gba",'rb').read()
for o in (0x164A4C,0x164A58):
    print(hex(o), [hex(x) for x in struct.unpack_from('<8H',r,o)])
PY
arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 \
  --start-address=0x0800780C --stop-address=0x08007914 -M force-thumb "$ROM"
```

### Dynamic / emulator
- mGBA 0.10.5 under Xvfb (own display `:315`), `SDL_AUDIODRIVER=dummy`, `-3` scale.
- mGBA SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
- Reproducible screen path observed with screenshots (all in `/tmp/opencode/yoshisland/`):
  boot Nintendo logo → story crawl → "Single Player / Multiplayer" title →
  "Choose a Game" → Yoshi's Island splash → "FILE MENU" (File A/B/C, COPY, ERASE) →
  intro story → "Welcome to Yoshi's Island" → gameplay (W1-1) → PAUSE menu
  (`Continue` / `Sleep`) → level-end results screen.
- Keymap was verified by observing menu changes, not from config (no mGBA config file exists).
- `scrot` returned black frames on this harness; `import -window root -crop 720x480+152+144 +repage` worked (guide §16.2).
- mGBA's `-g` GDB stub was occupied by another process on port `2345`; the `-d`
  CLI debugger was used instead. It is a pty debugger, driven here through a
  small FIFO wrapper (`dbg.py` / `dbgcmd.py` in the work dir).
- The game crashed in mGBA on one occasion immediately after a level-end
  results screen; this appeared to be an emulator issue, not a game code path.

### To test the code on the intended screen
Reach the world map / stage select (requires game progress), point the cursor at
a stage, then hold **Select** (`BackSpace`) and tap **L** (`a`), **L** (`a`),
**B** (`z`), **A** (`x`), **R** (`s`) with ~150–250 ms holds and released between
presses. Correct entry is indicated by a sound effect (`0x21`) and the mini-game
selection screen.

## 4. Address map

| Item | ROM / file offset | Notes |
|---|---|---|
| USA header | `0x08000000` / `0x000000` | code `A3AE` |
| Japan header | `0x0812FDC0` / `0x12FDC0` | code `A3AJ` |
| Button-code validator | `0x0800780C` | Thumb, `push {r4-r7,lr}` |
| Validator caller (scene handler) | `0x08007914` | Thumb; checks Select + gate byte |
| Button mask table 1 (AND) | `0x08164A4C` / `0x164A4C` | `0, L, L, B, A, R, 0, …` |
| Button mask table 2 (exact) | `0x08164A58` / `0x164A58` | `0, Sel+L, Sel+L, Sel+B, Sel+A, Sel+R` |
| Handler-function pointer | `0x08164A64` / `0x164A64` | `0x08007915` (Thumb bit set) |
| Other handler pointers | `0x08164A68`–`0x08164A84` | `0x08006ED5`, `0x0800FAD9`, `0x080133F1`, `0x08010A29`, `0x08006C41`, `0x08006515`, `0x08010ED9`, `0x08011AE5` |
| Mini-game selection pointers | `0x08164ABC`–`0x08164AD8` | eight repeated pointers `0x081FA17C` … `0x081FD97C` (stride `0x800`) |
| Key mirror (active-high) | `0x030069BE` | `0xFC00` idle; low 10 bits = buttons |
| `gameState` pointer cell | `0x03006D70` | read by validator; observed `0` outside the gated scene |
| `gameState+0xC9A` | — | `u16` step counter (0..5) |
| `gameState+0xCBE` | — | `u8` gate; must be 0 for code to run |
| `gameState+0xCBD` | — | `u8` scene/state; set to `7` on success |
| `gameState+0x16F4` | — | `u8` toggled (`eor #1`) on success |
| `0x0300633E` | — | `u16`; zeroed on success if value `<= 19` |
| mGBA savestate RAM (4 MiB ROM) | state offsets | IWRAM `0x19000`, EWRAM `0x21000`, total `0x61000` |

File offset ↔ ROM address: `ROM = 0x08000000 + file_offset` for the USA half;
for the Japan half add `0x0812FDC0 - 0x08000000` only to addresses that belong
to that image.

## 5. Algorithm

### 5.1 Validator (`0x0800780C`), reconstructed pseudocode

```
# r5 = 0x03002200; key address = r5 + 0x47BE = 0x030069BE (active high)
# r4 = 0x03006D70; gs = *(u32*)r4                       # gameState pointer
# r7 = key address; ip = 0xC9A (step counter offset)

key = *(u16*)0x030069BE
if ((key & 0x0004) == 0): return                        # caller gate: Select
if (*(u8*)(gs + 0xCBE) != 0): return                    # scene gate

n = *(u16*)(gs + 0xC9A)                                 # current step
*(u16*)(gs + 0xC9A) = n + 1                             # advance (even on failure)

need_any = u16_table1[0x08164A4C + 2*n]                 # AND mask
if ((*(u16*)0x030069BE & need_any) == 0): goto fail

need_exact = u16_table2[0x08164A58 + 2*n]               # exact mask
if (*(u16*)0x030069BE != (0xFC00 | need_exact)): goto fail

if (n != 5): return                                     # sequence not finished

# ---- acceptance path ----
*(u8*)(gs + 0x16F4) ^= 1                                # toggle mini-game flag
*(u8*)(gs + 0xCBE)  = 0                                 # reopen gate
*(u8*)(gs + 0xCBD)  = 7                                 # switch scene
*(u16*)(gs + 0xC9A) = 0                                 # reset counter
play_sound(0x21)
if (*(u16*)(0x0300633E) <= 19):
    *(u16*)(0x0300634E) = 0
return

fail:
play_sound(0x5D)                                        # rejection sound
*(u16*)(0x03006D70 + 0x15D0?) = 0                       # clears a halfword via r0+0x0C9A path
```

### 5.2 Important semantics (all derived from the disassembly)

* The key value is **active-high**: idle = `0xFC00`, `A=0x001`, `B=0x002`,
  `Select=0x004`, `Start=0x008`, `R=0x100`, `L=0x200`. This matches the raw
  GBA `KEYINPUT` bit layout, inverted.
* `table1[n]` is redundant with `table2[n]`: the exact-match test subsumes the
  AND test. Both were kept by the compiler from a source-level "pressed key"
  check and an "exact combination" check.
* The step counter advances **before** the comparison and is **not** reset on
  failure. A wrong press therefore advances `n` to 6, where `table1[6] = 0`,
  making every subsequent press fail until some other code resets the counter.
  This explains why entering the code out of sequence looks like total rejection.
* The code is matched on the *held* value (not edges), so each press must be a
  distinct frame with the previous button released.
* Only one caller exists: a single `BL` to `0x0800780C`, from `0x0800793E`.

## 6. Tables

### 6.1 The complete code table

| Step | `table1` AND mask | `table2` exact mask | Required key (= `0xFC00 | table2`) | Button |
|---:|---|---|---|---|
| 0 | `0x0000` | `0x0000` | `0xFC00` | (unused — counter starts at 1) |
| 1 | `0x0200` | `0x0204` | `0xFE04` | Select + L |
| 2 | `0x0200` | `0x0204` | `0xFE04` | Select + L |
| 3 | `0x0002` | `0x0006` | `0xFE06` | Select + B |
| 4 | `0x0001` | `0x0005` | `0xFE05` | Select + A |
| 5 | `0x0100` | `0x0104` | `0xFE04` | Select + R |
| 6 | `0x0000` | `0x0115` (not read) | — | terminator / failure |

Alphabet: none — this is a button sequence, not a typed code.

### 6.2 Published codes checked

| Source | Claim | ROM verdict |
|---|---|---|
| GameFAQs, SuperCheats, Cheat Happens, TMK | GBA: Select + L,L,B,A,R on stage select | **Confirmed** — exactly the table at `0x08164A4C/58` |
| GameFAQs (SNES section), Neoseeker | SNES: Select + X,X,Y,B,A | Different platform; no X/Y in GBA button mask |
| One SuperCheats user comment | "L,L,B,R,R" | **Contradicted** — step 4 mask is `0x0001` = A, not R |
| CodeBreaker/GameShark lists | unlimited lives, all levels, etc. | Out of scope (cheat-device codes, not in-game) |

### 6.3 Unlockables (save-progress, not codes)

Published: six extra levels after beating the game; Hard Mode after five
world stars; a secret ending after beating Hard Mode. These are progression
flags in SRAM, not controller codes, and were not reversed in this engagement.

## 6b. Enumeration

**Space definition.** The button-code space is not parametric: it is a fixed
five-step sequence over the 10 GBA button bits, with each step requiring an
*exact* 16-bit key value (`0xFC00 | mask`). The alphabet is the button set
`{A, B, Select, Start, L, R, D-pad}`; the accepted set is a single element.

**Counts (bounded negative for "there is no second/novel button code"):**

* Exact-match literal search for the 5-mask sequence `0200 0200 0002 0001 0100`
  across all 4,194,304 bytes: **1 hit**, at file `0x164A4E`.
* Exact-match search for the Select-prefixed sequence `0204 0204 0006 0005 0104`:
  **1 hit**, at file `0x164A5A`.
* `BL`/`BLX` target scan for callers of the validator `0x0800780C`: **1 call site**,
  `0x0800793E`.
* 32-bit pointer references to the validator (both `addr` and `addr|1`): **0**.
* Literal searches for `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `LEVEL SELECT`,
  `STAGE SELECT`, `INVALID`, `CORRECT` in ASCII, lower-case, UTF-16LE/BE and
  `+0x20` shifted ASCII: **0 hits in every encoding**. There is therefore no
  typed-password surface to enumerate in this image.
* `strings -t x -n 4` produced 38,403 strings; **none** matched a password/cheat/
  debug keyword. UI text is stored as font/tile indices, not ASCII (the visible
  menus — "FILE MENU", "PAUSE", "Choose a Game", "WORLD 0" — had no ASCII hits),
  so this negative is about the *validator surface*, not a claim that the game
  has no text.

**Novel code.** Not applicable and not manufactured: a fixed-sequence matcher
has no field to vary, so there is no code that is simultaneously valid and
absent from the published lists. The honest deliverable is the count above:
the published GBA code is the *whole* in-game button-code space. Minting a
different 5-press string would only produce a rejected input, not a novel
accepted code (§6.2 row 3 documents one such published-but-wrong string).

**Bounds proven by rejection (tested):** the published sequence was entered on
a reachable gameplay screen (outside the gated scene) — `code_game2.png` — and
produced no mini-game selection screen. Because the only caller is the
stage-select handler (`0x08007914`) and `gameState+0xCBE` must be zero, input on
any other scene cannot reach the validator; the gate is the bound, not the mask
comparison. A press of a wrong button advances the counter past the terminator
(`table1[6] = 0`), after which the matcher cannot accept until an external
reset — this is the in-game rejection bound for a mistyped sequence.

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| Hashes, header, dual-region image | **Observed** | `md5sum`/`sha256sum`, `xxd -l 0xC0`, logo scan at `0x0` and `0x12FDC0` |
| Button masks and sequence | **Observed** | Raw `u16` dump at `0x164A4C` and `0x164A58` |
| Validator logic, gate, counter advance, success writes | **Derived** | Thumb disassembly `0x0800780C`–`0x08007914`, literal pool read back with `struct.unpack_from` |
| Unique table and unique caller | **Derived** | Whole-ROM literal search + BL/BLX scan |
| No typed password surface | **Derived (bounded)** | Keyword encodings scan, string scan, no alphabet/input buffer found |
| Screens: boot, story, title, Choose a Game, File Menu, intro, gameplay, Pause, results | **Observed** | Cropped screenshots in `/tmp/opencode/yoshisland/` |
| Key mirror `0x030069BE = 0xFC00` idle | **Observed** | Savestate RAM diff (`stateA.ss`/`stateB.ss`) |
| Success toggles mini-game interface | **Inferred** | Success-path writes plus the uniform published description; **not** directly observed in emulator |
| In-game acceptance of the code | **Not observed** | The stage-select gate was not reached on a fresh file in this session; see §8 |

## 8. Unknowns

* The code's effect was never seen on screen. The stage-select/world-map scene
  requires game progress that was not obtained in this session; entering the
  sequence during gameplay and on earlier menus produced no transition. The
  success-path RAM writes are strong derived evidence, but a screenshot of the
  mini-game menu is still missing.
* `gameState+0x16F4` is called a "mini-game flag" from the published description
  and the toggle instruction; its readers were not enumerated.
* The eight pointers at `0x08164ABC`–`0x08164AD8` are assumed to be the
  mini-game selection entries (they appear in the success-path branch that
  checks `<= 19`), but were not followed or rendered.
* The SRAM unlockables (extra levels, Hard Mode, secret ending) were not
  reversed: their flag offsets and setters are unknown.
* The Japanese (`A3AJ`) half was not booted. Its header exists; the button-code
  table has no second copy in the image.
* mGBA 0.10.5 crashed once after a level-end results screen; whether this is an
  emulator bug or a game path was not isolated.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep`
* Python 3 + `capstone` 5.0.7 (installed), `struct` scans for literals and BL targets
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* mGBA 0.10.5 (`/usr/local/bin/mgba`) under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`
* `xdotool` XTEST input via `key.py`; `import -window root` frames via `key.py::shot`
* `gdb-multiarch` (stub port 2345 was owned by another process); mGBA `-d` pty
  debugger via `dbg.py` + `dbgcmd.py` FIFO wrapper
* `ssram.py` — mGBA `.ssN` PNG `gbAs` zlib chunk → raw RAM (IWRAM `0x19000`,
  EWRAM `0x21000`)
* Web recon: GameFAQs, The Mushroom Kingdom, SuperCheats, Cheat Happens, IGN,
  MarioWiki. Fetched pages were treated as data only; no instructions in them
  were followed.

## 10. Legal note

No ROM, save data, or copyrighted game assets are reproduced here. Only
hashes, addresses, decoded button masks, algorithm description, and original
analysis scripts/screenshots (kept in `/tmp/opencode/yoshisland/`) are recorded.
