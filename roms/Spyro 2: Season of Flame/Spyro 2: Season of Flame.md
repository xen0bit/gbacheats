# Spyro 2: Season of Flame (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Spyro 2: Season of Flame/Spyro 2: Season of Flame.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `SPYRO 2` |
| Game code | `A2SE` (USA) |
| Maker code | `7D` (Vivendi Universal Games) |
| Version / complement / checksum | `0x00` / `0xDC` / `0x0000` |
| Entry word | `0xEA00002E` (stock crt0 branch — **not** a modified/cracktro image) |
| `main` (Thumb) | `0x08002A04` (from crt0 literal at `0x1C8`) |
| MD5 | `8d9fbf8bde7941ca97dcba7757d60e81` |
| SHA-1 | `53e77c7e4a895e0652ec2ca2c9b4a590e84abdca` |
| SHA-256 | `75c1c3846f0a7e762c453455ff86c9fe7c3eecbd1d153809798831e5ee0a8117` |

All addresses below are for **this exact hash**.

## 2. Executive summary

This game has a **title-screen button-code system**: 12 fixed 8-direction sequences, each
followed by **B** as the submit key. There is no password entry screen, no text alphabet, and
no checksum/arithmetic generator — the accepted set is a hard-coded 12-row mask table at
`0x080660C4`. The validator at `0x08055980` compares the **last eight directional presses**
held in an 8-entry ring buffer against each row; a match sets bit *i* of the global cheat
flags word at `0x030026C8` and plays a confirmation sound.

- The 10-entry lists on GameRevolution and Neoseeker omit two codes; **GameFAQs lists all
  12** (the omissions are *Blue Spyro* and *Unlock Sparx Panic*). All 12 ROM rows were
  entered in the emulator and the flags word reached `0x00000FFF`.
- The matcher is a **suffix matcher**: extra presses before the 8-press window are ignored.
  This yields an unbounded family of unpublished, accepted sequences. Novel alias
  `ULDUUULDUB` (extra leading `Up`) was entered on the real title screen, set bit 6
  (`0x00000040`), and visibly enabled the previously greyed-out **Sparx Panic** menu entry.
- Bounds were proven by rejection: 7 presses, a wrong 8th press, and a wrong final key (A
  instead of B) all left the flags word at `0`.
- Bounded extra: in the title handler at `0x08057610` there is a gated `L+R+Start` combo
  (mask `0x308`) that clears a title state word and sets a flag; it is a reset/clear path,
  not a hidden menu, and no second code table or password surface was found.

Evidence types are labelled **Observed** (emulator/savestate RAM), **Derived** (disassembly),
and **Inferred** ( plausibility only) throughout.

## 3. How to reproduce

1. mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, keymap A=`x`, B=`z`, Start=`Return`,
   D-pad = arrow keys. Hold each key ~120 ms with ~160 ms gap.
2. Boot and wait ~13 s to the **PRESS START** screen (no save needed).
3. Enter a sequence as eight arrow presses followed by `z` (B). A chime confirms success.
4. Save an mGBA state (Shift+F1…F8); `.ssN` is a PNG with a zlib `gbAs` chunk. Decompress it
   (raw state `0x61000` bytes) and read:
   - IWRAM: state offset `0x19000 + (addr - 0x03000000)` — cheat flags at state `0x1B6C8`.
   - EWRAM: state offset `0x21000 + (addr - 0x02000000)` — `W = [0x030008D4] = 0x0203E404`;
     ring buffer at `W+0x54`, ring head (u16) at `W+0x7BE`.
5. Reload the clean title state with F1 between experiments.

Reproduction commands and the exact sequences are in §6 and §6b.

## 4. Address map

| Item | File offset / ROM address | Meaning |
|---|---|---|
| Sequence table | `0x660C4` → `0x080660C4` | 12 rows × 8 u16 masks (192 bytes); values are active-high `R=0x10, L=0x20, U=0x40, D=0x80` |
| Action-ish table | `0x66184` → `0x08066184` | Pointer used by a nearby title/menu function (not the code table) |
| Validator | `0x55980` → `0x08055980` | Copies table to stack, matches ring buffer, sets flag bit, clears ring, calls sound `0x08171550` |
| Validator caller | `0x080575C0` | Runs only when title mode byte `W+0x7CA == 3`, `W+0x7D3 == 0`, and key-code halfword `0x030010B0 == 2` (B) |
| Ring buffer | EWRAM `W+0x54` (16 bytes), head `W+0x7BE` | Last 8 directional presses; `W = [0x030008D4]` |
| Cheat flags | IWRAM `0x030026C8` (u32) | Bit *i* = code row *i* accepted |
| Key code | IWRAM `0x030010B0` (u16) | `2` = B (submit); directions are `0x10/0x20/0x40/0x80` |
| Raw keys | IWRAM `0x030010AC` | `0xFC00` observed with no key held |
| Flag consumers | `0x0800666C`(b1), `0x08007514`(b7), `0x08007954`/`98E`/`9C2`(b4), `0x08007B26`(b3), `0x08007BE0`(b6), `0x08007C1C`(b5), `0x08018740` etc.(b11), `0x080194F6`(b7), `0x0801E6A0`(b2), `0x080449B8`(b10), `0x08045768`(b8), `0x080457CE`(b9), `0x0804E92C`(b0) | Each `ldr` literal `0x030026C8` then `ands` with the bit mask |
| Sparx Panic unlock test | `0x08007BD0` | returns true if save byte `+0x20 & 0x20` **or** cheat bit 6 (`0x40`); setter `0x08007BFC` |
| Mini-games unlock test | `0x08007C0C` | returns true if save byte `+0x40` **or** cheat bit 5 (`0x20`); setter `0x08007C38` |
| Blue Spyro path | `0x0804E92C` → `0x08054828(6)` | Bit 0 makes the level/overlay renderer call the descriptor loader with index 6 |

## 5. Algorithm

Derived from `0x08055980` (Thumb):

```
copy 192 bytes from ROM:0x080660C4 to stack[0..191]   # 12 rows x 8 u16
for i in 0..11:                                        # row index
    ring = W + 0x54 ; head = u16[W + 0x7BE]
    for j in 0..7:
        expected = u16[stack + i*16 + j*2]
        actual   = u16[ring + 2*((head + j) & 7)]
        if actual != expected: break
    else:
        cheat_flags |= (1 << i)                        # u32 at 0x030026C8
        for k in 0..7: u16[ring + 2*k] = 0              # clear ring
        sound(0x08171550)                              # confirmation chime
```

The caller at `0x080575C0` invokes the validator when the decoded key code is `2` (B),
**before** writing B into the ring; other decoded key codes are written into the ring at
`W+0x54 + 2*head` and advance `head = (head+1) & 7`. This is a **last-8 suffix matcher**:
presses before the final eight are irrelevant, and `B` is a submit trigger rather than a
ninth compared symbol.

No checksum, XOR key, permutation, or arithmetic generator exists in this path.

## 6. Tables

### 6.1 Complete accepted table (all 12 rows, ROM `0x080660C4`)

| Row | Bit | Mask | 8 directional presses (then B) | Published effect |
|---:|---:|---:|---|---|
| 0 | 0 | `0x001` | U U U U D L R D | Blue Spyro |
| 1 | 1 | `0x002` | U L U R U D U D | All Portals Open |
| 2 | 2 | `0x004` | L L D U U R L L | Super Charge |
| 3 | 3 | `0x008` | D U L L U L L R | Atlas Warping |
| 4 | 4 | `0x010` | L R L R R R U D | Infinite Lives |
| 5 | 5 | `0x020` | R U D D D R U D | Mini-Games / Dragon Draughts |
| 6 | 6 | `0x040` | L D U U U L D U | Unlock Sparx Panic |
| 7 | 7 | `0x080` | D U R L R U R L | Never Drown |
| 8 | 8 | `0x100` | R L U D R D U R | Infinite Ammo |
| 9 | 9 | `0x200` | L D U R L U U L | Infinite Shield |
| 10 | 10 | `0x400` | L R U U R L R U | View All Worlds in Atlas |
| 11 | 11 | `0x800` | R D U R L U R D | All Breath Types |

All 12 rows are present in the GameFAQs list; the GameRevolution/Neoseeker 10-item
lists omit rows 0 and 6.

### 6.2 Input alphabet

Only four symbols are compared: `R=0x10, L=0x20, U=0x40, D=0x80` (u16, active-high).
`B=0x02` is recorded in the ring after the comparison but is not part of any row.
`A=0x01`, `Start=0x08`, `L/R triggers=0x200/0x100` are not valid row symbols.

## 6b. Enumeration

**Space definition.** The validator compares an 8-symbol window over a 4-symbol alphabet
against exactly 12 hard-coded rows. There is no checksum, no free field, and no generator.
The complete compared space is therefore **12 accepted rows out of 4^8 = 65,536 possible
8-press windows**. With B as submit, the canonical accepted inputs are exactly 12 nine-press
sequences. Pressure on the ring buffer is suffix-based, so for any accepted row *s* and any
prefix *p* of arbitrary directional presses, *p·s·B* is also accepted: the canonical set has
12 members but the **reachable accepted input language is infinite**.

**Full-space proof (Observed).** Starting from the clean title state, all 12 canonical codes
were entered consecutively without reloading; the flags word advanced
`0x001 → 0x003 → … → 0x7FF → 0xFFF`, one new bit per code. This runs the game's own
validator over the entire table and proves there are exactly 12 reachable flag bits
(no hidden 13th row, no reserved bit). Screenshot evidence for two conspicuous effects:
`sp_menu.png` (Sparx Panic enabled after row 6), `play2.png` (blue in-game Spyro after row 0).

**Novel codes absent from every published list.** All published lists use exactly nine
presses. The following generated ten-press aliases are accepted in-game and appear in none
of them:

| Novel sequence | Preimage | ROM bit | Observed proof |
|---|---|---:|---|
| `ULRUURLRUB` (extra leading U) | row 10, View All Worlds in Atlas | 10 (`0x400`) | savestate slot 6 flags `0x00000400` |
| `ULRLRRRUDB` (extra leading U) | row 4, Infinite Lives | 4 (`0x010`) | savestate slot 7 flags `0x00000010` |
| `ULDUUULDUB` (extra leading U) | row 6, Unlock Sparx Panic | 6 (`0x040`) | savestate slot 8 flags `0x00000040`; `novel_menu.png` shows Sparx Panic bright/enabled |

The third row is the headline result: a code in no published list, entered on the real
title screen, with both a RAM read and a visual effect.

**Bounds proven by rejection (Observed, all from a clean title state):**

| Test | Input | Resulting flags |
|---|---|---|
| Too short (7 directions) | `LRLRRRU` + B | `0x00000000` |
| Wrong 8th press | `LRLRRRUU` + B | `0x00000000` |
| Wrong submit key (A instead of B) | `LRLRRRUD` + A | `0x00000000` |
| Leading non-direction submit (B) | B + `LRLRRRUD` + B | `0x00000010` (accepted — confirms suffix semantics, not a 9-symbol comparison) |

The ring buffer contents after each rejection were also dumped and matched the entered
presses, so rejection is at the comparison stage, not a failed input path.

**Bounded negative for other surfaces.** `strings -t x -n 4` over the whole 8 MiB returned
83,616 entries; a case-insensitive keyword pass (`password|cheat|code|debug|secret|unlock|
menu|invalid|continue`) returned **zero** relevant hits. This game's text is stored as
font/tile indices, not ASCII, so that scan alone proves nothing; the screen walk
(splash → PRESS START → main menu → New Game/Select Game → intro cutscene → gameplay) found
only the button-code entry surface. A literal-pointer scan found exactly one pointer to the
mask table (`0x55A14`) and one to its neighbor (`0x55AE0`), and a BL scan found exactly one
caller of the validator (`0x80575DC`). The `L+R+Start` gate at `0x08057610` writes title
state (`W+0x7C0 = 0`, `W+0x7D4 = 1`) rather than opening a menu.

## 7. Validation evidence

- **Observed:** ROM hash/header; all 12 canonical codes accepted with the expected flag bit;
  three novel aliases accepted; four rejection tests with `0x00000000` flags; ring-buffer and
  flags values read from decompressed mGBA `gbAs` savestate chunks; screenshots
  `title.png` (Sparx Panic greyed), `sp_menu.png` / `novel_menu.png` (bright), `play2.png`
  (blue Spyro), `press_start2.png` (code entry screen), `newgame.png` (Select Game/save slots).
- **Derived:** table layout 12×8 u16 at `0x080660C4`; validator loop, ring indexing, flag
  write, and ring clear at `0x08055980`; submit condition (`0x030010B0 == 2`) at
  `0x080575C0`; bit→effect consumer addresses; prefix-alias semantics.
- **Inferred:** the precise purpose of the `L+R+Start` state write at `0x08057610` (likely a
  save/reset confirm on the title screen) and the exact identity of the descriptor loaded by
  `0x08054828(6)` for Blue Spyro were not fully exercised. The published effect labels are
  from GameFAQs/Neoseeker and were visually confirmed only for Blue Spyro and Sparx Panic.

## 8. Unknowns

- Bit 2 (Super Charge) and bit 3 (Atlas Warping) effects were confirmed only by flag bits,
  not by in-game ability tests.
- The 3 `Unused` entries on the New Game "Select Game" screen appear to be save slots;
  they were not populated or tested as unlockables.
- Whether the cheat flags survive into a battery save (vs. being title-session RAM only)
  was not tested: tests were run from a clean savestate at the title screen.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all
  disassembly; Capstone (Thumb mode) for the literal-pointer and BL scanners.
- `strings -t x -n 4`, `grep -iE`, byte-pattern searches with Python `bytes.find`.
- mGBA 0.10.5 under Xvfb `:318` with `SDL_AUDIODRIVER=dummy`, `xdotool` XTEST input,
  `scrot` + ImageMagick `convert` for screenshots.
- Python helpers in `/tmp/spyro2/`: `scan_flags.py`, `scan_bl.py`, `enter_code.py`,
  `verify_all.py`, `bounds.py`; savestate RAM reader using `zlib.decompress` of the `gbAs`
  PNG chunk.

**Legal note:** no ROM image or extracted copyrighted assets are redistributed here; only
hashes, addresses, algorithms, and original analysis artifacts are published.
