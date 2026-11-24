# SpongeBob SquarePants: Revenge of the Flying Dutchman (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Analysis date: 2026-11-20. Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md), especially §0.2 (full enumeration), §11 (text/font banks), §16.5/§16.9 (unary groups; prove closed sets), §16.11 (SKU verification).

Scope: **in-game / developer-intended cheats only.** No GameShark / CodeBreaker / Action Replay codes were analysed or published.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/SpongeBob SquarePants: Revenge of the Flying Dutchman/SpongeBob SquarePants: Revenge of the Flying Dutchman.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title | `SBREVENGEGBA` |
| Game code | `AQ3E` |
| Maker code | `78` |
| Software version | `0` |
| Entry word | `0xEA00002E` (`b 0x080000C0`, stock) |
| MD5 | `0be6c13af62a0f75651bb2acbc397a56` |
| SHA-1 | `f5e28f897edb62019addcf3635ab89df032186a0` |
| SHA-256 | `6f5b328b9a2fe15708f4153f1ca8727babf490ea225eb4d98a3954c2e001a24c` |

### Relation to the 2-in-1 release (critical for reusing addresses)

A byte comparison against the Revenge half of
`roms/2 Games in 1 - SpongeBob SquarePants - SuperSponge & Revenge of the Flying Dutchman/…gba`
(first `0x800000` bytes) gives **exactly 7 differing bytes**:

| File offset | Standalone | 2-in-1 half | Meaning |
|---:|---:|---:|---|
| `0x000000`–`0x000002` | `2E 00 00` (`EA00002E`) | `A1 57 68` (`E86857A1`) | entry branch (2-in-1 jumps to its boot selector) |
| `0x0000AC`–`0x0000AE` | `41 51 33` (`AQ3`) | `42 44 46` (`BDF`) | game code (`AQ3E` vs `BDFE`) |
| `0x0000BD` | `6D` | `66` | header complement check |

All remaining 8,388,601 bytes are identical. Therefore every game address and algorithm in the
[2-in-1 report](../2%20Games%20in%201%20-%20SpongeBob%20SquarePants%20-%20SuperSponge%20&%20Revenge%20of%20the%20Flying%20Dutchman/2%20Games%20in%201%20-%20SpongeBob%20SquarePants%20-%20SuperSponge%20&%20Revenge%20of%20the%20Flying%20Dutchman.md)
applies unchanged to this standalone image. This was **re-verified independently** here by
disassembly, live breakpoints and RAM reads (§4, §7), not merely assumed.

---

## 2. Executive summary

The only developer-intended cheat surface is a **6-symbol password keypad**, reached from
`Main Menu → Continue` (with no save). There is no button code, no hidden debug menu, and no
second password format.

The password is **not a table lookup and has no additive checksum**. It is a 30-bit packed
state: 6 alphabet symbols × 5 bits, little-endian. The 30 bits are a fixed permutation of three
game-state words — an 18-bit progress word `W`, a 10-bit treasure bitmap `H`, and a 1-bit flag
`B`, with one reserved bit that must be zero. Validity is **structural**: three 5-bit *unary*
progress groups must each be one of `{0,1,3,7,15,31}`, with a marker bit set whenever any group
is non-empty. `?` is the 32nd alphabet symbol (index 31), i.e. the maximum unary value, **not a
wildcard** — the game's own encoder emits it.

Raw space `32^6 = 2^30 = 1,073,741,824`; **exactly 1,777,664 (0.166 %) are valid**, enumerated
exhaustively offline with zero round-trip failures.

A freshly minted code **`H0X1S2`** (not on any published list and not in the earlier 2-in-1
report) was entered on the real keypad. It was accepted, opened all chapter entrances, and the
level card re-printed `H0X1S2` from the game's own encoder. Live IWRAM reads at the accept
breakpoint gave `W=0x0001FFFF`, `H=0x0000`, `B=0x00`, exactly as the offline decoder predicted.
Bounds were proven by two in-game rejections: `BBBBBH` (non-unary group, decoded value
`0x0A000000`) and `BBBCBB` (reserved bit 15, decoded value `0x00008000`), both of which hit the
ROM's reject path with all state words still zero.

---

## 3. How to reproduce

### 3.1 Environment

```bash
# :318 was occupied by another agent's live session, so this run used an isolated :320.
Xvfb :320 -screen 0 1024x768x24 &
DISPLAY=:320 openbox &
DISPLAY=:320 SDL_AUDIODRIVER=dummy mgba -d -3 "<rom>.gba"   # -d = built-in CLI debugger (PTY)
```

Toolchain: `mgba` 0.10.5 (`/usr/local/bin/mgba`), `gdb-multiarch`, `xdotool`, `scrot`,
`arm-none-eabi-objdump`, Python 3 + Pillow + `tesseract` (screen-state detection), `capstone`
available but not needed. A PTY was used for mGBA's `-d` debugger; its GDB stub (`-g`) bound only
once and was abandoned because a second attach timed out. The built-in debugger accepts
`b/t <addr>` (Thumb breakpoint), `r/4|r/2|r/1 <addr>` (memory read) and `c` (continue).

### 3.2 Keymap and screen path

mGBA SDL defaults: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
Keys were held 60–80 ms (longer double-steps menus, per guide §16.2) and sent with XTEST to the
focused window. **Important:** with several mGBA windows on one display, target the window owned
by the intended PID (`xdotool search --pid <pid> --name mGBA`) — a stale window silently eats all
input.

```
Boot logos / "PRESS START" title  --Start--> attract demo --Start--> MAIN MENU
MAIN MENU: New Game / Continue / Options
  Options: SFX VOLUME <90%>, MUSIC VOLUME <100%>, B BACK, CHANGE < >
  Continue (no save) -> 6-slot PASSWORD keypad
  New Game -> SpongeBob intro cinematic (no hidden menu)
```

The keypad is an 8×4 grid, cursor starts on `B`, D-pad moves, A commits, B leaves:

```
row0  B C D F G H J K
row1  L M N P Q R S T
row2  V W X Y Z 0 1 2
row3  3 4 5 6 7 8 9 ?
```

The cursor stays on the committed glyph. **After a rejection the six slots clear, but the cursor
and/or partial input are not reliably reset to `B`** — so each code tested in this report was
entered from a fresh keypad rather than chained after a rejection.

Accepting a code leads to `SELECT CHAPTER`, where the ring shows the unlocked entrances; A opens
the level-intro card, which prints the level name, `-LEVEL n-` and **the code the game itself
generates for the current state** — the most useful verification screen.

### 3.3 Exact reproduction of the novel-code test

1. Set Thumb breakpoints `b/t 0x0801AEEA` (accept tail) and `b/t 0x0801AC56` (reject tail), then `c`.
2. Navigate to the keypad; move the cursor to each symbol of `H0X1S2`
   (`H`=row0 col5, `0`=row2 col5, `X`=row2 col2, `1`=row2 col6, `S`=row2 col4, `2`=row2 col7) and press A.
3. The accept breakpoint fires. Read `r/4 0x030019E4`, `r/2 0x030019E0`, `r/1 0x030007D0`.
4. `c`, then A on the hub; the level card prints `H0X1S2`.

No savestate or save file is required; the password screen is reachable from a fresh cart.

---

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`), valid for the standalone image.

| ROM address | What | Evidence |
|---:|---|---|
| `0x0801AA38` | Encoder: state words → 30-bit value → 6 symbols | prior report; consistent with live echo |
| `0x0801AB80` | Packer: 30-bit value in `r5` → 6 symbols at `0x03001954` | prior report |
| `0x0801ABB8` | **Decoder / validator**: 6 symbols → 30-bit value in `r7`, unary checks, state writes, returns 0/1/2 | disassembled here |
| `0x0801AC56` | Reject tail (`movs r0,#0`); breakpoint 2 in this run | disassembled + hit live |
| `0x0801ADB2` | `strb` B flag → `0x030007D0` | disassembled |
| `0x0801AE46` | `strh` H → `0x030019E0` (literal pool at `0x0801AE70`) | disassembled |
| `0x0801AE50` | `str` W → `0x030019E4` (literal pool at `0x0801AE6C`) | disassembled |
| `0x0801AEEA` | Accept tail (`movs r0,#1`); breakpoint 1 in this run | disassembled + hit live |
| `0x08020E94` | **Only** caller of the decoder (`BL 0x0801ABB8`) on the keypad's 6-byte buffer; BL scan over the whole ROM found exactly this one hit | derived here |
| `0x08020C00`–`0x08021060` | Password keypad screen (`cmp r3,#6` at `0x08020E8E`) | prior report |
| `0x080D1E28` | Alphabet string `BCDFGHJKLMNPQRSTVWXYZ0123456789?` (32 bytes + NUL) | byte dump here; literal at `0x0801AC5C` |
| `0x0802F72C` | `SELECT CHAPTER` hub builder | prior report |
| `0x0802E8F8`–`0x0802EA48` | Per-bit state query table (`W` bits, `H` treasure groups) | prior report |
| `0x0800CE40`–`0x0800CED4` | Bonus gate: requires `H` bits 1–3, 4–6, 7–9 all set | prior report |
| `0x0D2350` | `password:` string | `strings -t x` |
| `0x0D2AF0` / `0x0D2B08` | `select chapter` / `selectA` strings | `strings -t x` |
| `0x0D21DC`–`0x0D22AC` | Ten treasure names (matching the 10 `H` bits) | prior report |

At the decoder accept breakpoint, register values were `r5=0x030019E4`, `r6=0x030019E0`,
`r14=0x08020E99` (return into the keypad caller) — independently confirming the pointer literals.

### RAM

| Address | Size | Contents | Live read in this run |
|---|---:|---|---|
| `0x030019E4` | u32 | progress word `W` (18 bits used) | `0x0001FFFF` after `H0X1S2`; `0x00000000` on both rejections |
| `0x030019E0` | u16 | treasure bitmap `H` (10 bits used) | `0x0000` in all tests |
| `0x030007D0` | u8 | single flag `B` (bit 0 carried by code) | `0x00` in all tests |
| `0x03001954` | 6 B + NUL | encoder output buffer (last generated code) | zero until a level card is drawn; then holds the current code |

---

## 5. Algorithm

### 5.1 Symbol → 30-bit value (`0x0801ABB8`, derived + observed)

```python
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0123456789?"       # 0x080D1E28

def to_val(code):                                 # 6 chars, LSB first
    v = 0
    for i, ch in enumerate(code[:6]):
        j = ALPHA.index(ch)                       # unknown char -> 255, fails all checks
        v |= j << (5 * i)
    return v
```

Live confirmation: `BBBBBH` produced `r7 = 0x0A000000` at the reject breakpoint (H = index 5 at
symbol position 5 → `5 << 25`); `BBBCBB` produced `r7 = 0x00008000` (C = index 1 at position 3 →
`1 << 15`, the reserved bit). The offline decoder reproduces both values exactly.

### 5.2 Bit permutation (`0x0801AD30`–`0x0801AE50`, derived)

`val` bit → state bit (`W` and `H` bit numbers; `B` is bit 0 of the flag byte):

```
W:  0->10, 2->3,  3->17, 5->2,  7->14, 9->9,  11->7,  14->8,
   16->6, 17->13, 19->11, 21->4, 22->12, 23->16, 25->5, 26->0,
   27->15, 29->1
H:  1->5, 4->4, 6->7, 8->8, 10->3, 13->2, 18->6, 20->9, 24->1, 28->0
B: 12->0
reserved (must be 0): bit 15
```

### 5.3 Validity (`0x0801ABFE`–`0x0801AD28`, derived)

```python
UNARY = (0, 1, 3, 7, 15, 31)
def valid(v):
    if (v >> 15) & 1: return False               # reserved hole
    W, H, B = split(v)
    A, Bc, C = (W >> 1) & 31, (W >> 6) & 31, (W >> 11) & 31
    if any(g not in UNARY for g in (A, Bc, C)): return False
    if (A or Bc or C) and not (W & 1): return False   # marker bit
    return True
```

No arithmetic checksum exists; all rejection is by these structural checks. A further
comparison against the u32 at `0x03000664` yields return 2, but that word was observed as
`0x1CF161A1` (≥ 2^30) in the prior work, so a 30-bit code can never equal it — the return-2 path
is dead.

### 5.4 Apply and encode

```python
def apply(code):
    v = to_val(code)
    if not valid(v): return 0                      # UI clears the buffer, stays on keypad
    W, H, B = split(v)
    *(u32*)0x030019E4 |= W                         # OR: bits are only set
    *(u16*)0x030019E0 |= H
    *(u8 *)0x030007D0  = B
    return 1                                       # UI sets 0x0300074C, shows hub

def encode(W, H, B):
    v = join(W, H, B)                              # inverse permutation of §5.2
    return "".join(ALPHA[(v >> (5*i)) & 31] for i in range(6))
```

`encode(split(v)) == v` was verified for all 1,777,664 valid values (§6b).

### 5.5 Meaning of the fields

`W` is a set of unlock flags queried one-by-one by the game's table at `0x0802E8F8`. Each 5-bit
unary group is four level flags plus a chapter-complete top bit; the unary rule forces levels to
be unlocked in order:

| Field | Bits | Meaning |
|---|---|---|
| `W` bit 0 | 1 | marker; must be 1 if any group non-zero |
| group A | `W` 1–5 | unary 0…5, four levels + complete (published "chapter 4") |
| group B | `W` 6–10 | unary 0…5 (published "chapter 2") |
| group C | `W` 11–15 | unary 0…5 (published "chapter 3") |
| `W` 16–17 | 2 | extra unlock flags used by all-levels/all-bosses codes |
| `H` | 10 | ten treasure/item flags; bonus gate needs triples 1–3, 4–6, 7–9 |
| `B` | 1 | extra flag; **not** the HUD difficulty (a `B=1` code displayed `NORMAL`) |

---

## 6. Tables

### 6.1 Alphabet

```
index: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
char:  B  C  D  F  G  H  J  K  L  M  N  P  Q  R  S  T
index:16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31
char:  V  W  X  Y  Z  0  1  2  3  4  5  6  7  8  9  ?
```

### 6.2 Public codes verified against the offline validator

All 27 strings below pass `valid(to_val(code))`. They come from the IGN / GameFAQs / Fandom /
planetcheats lists (fetched 2026-11-20, treated as data only) and the earlier 2-in-1 report.
`A,B,C` are the encoded unary group values; `free` = `W` bits 16–17.

| Code | Published effect | A,B,C | mark | free | `H` | `B` |
|---|---|---:|---:|---:|---:|---:|
| `BBBBB`→`BBBBBB` | Ch1 L1 | 0,0,0 | 0 | 0 | `0x000` | 0 |
| `BBBBN`→`BBBBBN` | Ch2 L1 | 0,0,0 | 1 | 0 | `0x001` | 0 |
| `VBBDBN` | Ch2 L2 | 0,1,0 | 1 | 0 | `0x011` | 0 |
| `XBXDBN` | Ch2 L3 | 0,7,0 | 1 | 0 | `0x031` | 0 |
| `VVXNBN` | Ch3 L1 | 0,15,0 | 1 | 0 | `0x051` | 0 |
| `VXX5BN` | Ch3 L2 | 0,15,1 | 1 | 0 | `0x0D1` | 0 |
| `V5X9GN` | Ch3 L3 | 0,15,7 | 1 | 0 | `0x1D1` | 0 |
| `V9X9HS` | Ch4 L1 | 0,15,31 | 1 | 0 | `0x3D1` | 0 |
| `V9X909` | Ch4 L2 | 1,15,31 | 1 | 0 | `0x3D3` | 0 |
| `2?5909` | Ch4 L3 | 7,31,31 | 1 | 0 | `0x3F7` | 0 |
| `V9X9HN` | Boss Alaskan Bullworm | 0,15,15 | 1 | 0 | `0x3D1` | 0 |
| `XVXNBN` | Boss Plankton | 0,15,0 | 1 | 0 | `0x071` | 0 |
| `2?6929` | Boss Wild Jellyfish | 15,31,31 | 1 | 0 | `0x3FF` | 0 |
| `V5X5GN` | Bonus Kara-tay | 0,15,3 | 1 | 0 | `0x1D1` | 0 |
| `XBDDBN` | Bonus Krabby Patty | 0,3,0 | 1 | 0 | `0x031` | 0 |
| `V?5909` | Bonus Jellyfish roundup | 3,15,31 | 1 | 0 | `0x3D7` | 0 |
| `9??99?` | All levels except Bullworm | 31,15,31 | 1 | 3 | `0x1FF` | 1 |
| `???91?` | All levels (Easy) | 31,31,31 | 1 | 2 | `0x1FF` | 1 |
| `???92?` | All levels (Hard) | 31,31,31 | 1 | 2 | `0x3FF` | 1 |
| `9??925` | All bosses (Hard) | 15,15,15 | 1 | 2 | `0x3FF` | 1 |
| `9?6925` | All bosses (Normal) | 15,15,15 | 1 | 2 | `0x3FF` | 0 |
| `??692?` | Final level (Normal) | 31,31,31 | 1 | 2 | `0x3FF` | 0 |
| `QCRBX6` | Fan-wiki Ch3 L1 | 31,0,0 | 1 | 2 | `0x00F` | 1 |
| `QFRVX6` | Fan-wiki Ch3 L2 | 31,0,1 | 1 | 2 | `0x08F` | 1 |
| `QPRZ16` | Fan-wiki Ch3 L3 | 31,0,7 | 1 | 2 | `0x18F` | 1 |
| `QTRZ2?` | Fan-wiki Ch4 L1 | 31,0,31 | 1 | 2 | `0x38F` | 1 |
| `7TR12?` | Fan-wiki Ch4 L2 | 31,1,31 | 1 | 2 | `0x39F` | 1 |

Published `BBBBB` and `BBBBN` are **five-symbol truncations**: the screen has six slots, so typing
them literally pads with `B` (`BBBBBB`/`BBBBBN`). Those six-symbol forms were accepted on this ROM
(`BBBBBB` → chapter 1 hub; `BBBBBN` → `SPECIAL DELIVERY`, `-LEVEL 1-` in the prior pass).

---

## 6b. Enumeration

### Space (exact, not sampled)

| Quantity | Value |
|---|---|
| Alphabet | 32 symbols (`BCDFGHJKLMNPQRSTVWXYZ0123456789?`) |
| Length | 6 |
| Raw space | `32^6 = 2^30 = 1,073,741,824` |
| After reserved-bit-15 filter | `2^29 = 536,870,912` |
| **Valid codes** | **1,777,664** (0.166 % of raw) |

The count is derived from the layout and confirmed by exhaustive construction:

```
marker/group combinations = 2 (all groups zero, marker 0 or 1)
                          + (6^3 - 1) = 215 (at least one group non-zero, marker 1)
                          = 217
217 x 2^2 (W bits 16..17) x 2^10 (H) x 2 (B) = 1,777,664
```

A Python enumeration built all 1,777,664 values, ran each through `valid()` (0 failures) and
checked `to_val(encode(W,H,B)) == join(W,H,B)` for every one (0 failures). All 27 published codes
above were decoded and passed.

### Novel code (not in any published list)

**`H0X1S2`** — minted here from a state no published code uses: all three progress groups full,
marker set, `W` bit 16 set, **zero** treasures, `B=0`:

```
H0X1S2 -> val 0x2EEB4AA5 -> W = 0x0001FFFF, H = 0x0000, B = 0
```

It appears in no GameFAQs / IGN / Fandom / planetcheats / VGChartz list (a web search for the
literal returns only an unrelated Reddit thread), and it is distinct from the `H0X1J2` used in
the earlier 2-in-1 report (that one has `W=0x0000FFFF`).

**In-game proof (all Observed in this run):**

1. Entered on the real 6-slot keypad; the accept breakpoint `0x0801AEEA` fired (breakpoint 2,
   reject, did not fire).
2. Live IWRAM reads at the breakpoint: `0x030019E4 = 0x0001FFFF`,
   `0x030019E0 = 0x0000`, `0x030007D0 = 0x00` — exactly the offline prediction.
3. `SELECT CHAPTER` opened with the full ring of level entrances
   (`shots/p_novel2_hub.png`).
4. The level-intro card printed `GARY, COME HOME!` / `-LEVEL 1-` and the game's own encoder
   re-printed **`H0X1S2`** (`shots/p_novel2_levelcard.png`) — a full ROM round-trip of the
   novel code.

A second freshly minted code, **`H0X1J2`** (`W=0x0000FFFF, H=0, B=0`), was also accepted in this
run with matching RAM and level-card echo (`shots/p_novel_hub.png`,
`shots/p_novel_levelcard.png`), independently reproducing the earlier 2-in-1 finding on the
standalone SKU.

### Bounds proven by rejection

| Input | Offline verdict | Decoded value at reject breakpoint | Live RAM | In-game result |
|---|---|---|---|---|
| `BBBBBH` | group A = 16, not unary | `r7 = 0x0A000000` | `W=0, H=0, B=0` | breakpoint `0x0801AC56` hit; slots cleared, still on keypad (`shots/p_after_rej_nonunary.png`) |
| `BBBCBB` | reserved bit 15 set | `r7 = 0x00008000` | `W=0, H=0, B=0` | breakpoint `0x0801AC56` hit; slots cleared, still on keypad (`shots/p_after_rej_reserved.png`) |

Both rejections prove that a structurally invalid value never reaches the state-write path, and
the `BBBCBB` case isolates the reserved-bit layer from the unary layer.

### Negative result: no other cheat surface (bounded)

* Screen enumeration (all reachable menus walked): boot logos, PRESS START title, attract demo,
  `Main Menu` (New Game / Continue / Options), Options (two volume sliders only), `New Game`
  intro cinematic, password keypad, `SELECT CHAPTER` hub, level-intro card. No hidden/debug
  menu entry appeared anywhere.
* `strings -t x` over the whole 8 MiB for `password|cheat|debug|invalid|secret|unlock|level select`
  found only game text (`password:`, `select chapter`, treasure/bonus messages). The single
  `"level select"` hit at file `0x5A7BE6` is a **music-track credit** ("level select" / Martin
  Schioeler) inside the sound bank, alongside `"Opening music"`, `"Coral reef level"`, etc. —
  not a debug menu (guide §11 "keyword hits need context").
* A whole-ROM Thumb BL scan found **exactly one** call to the validator (`0x08020E94`, inside the
  keypad screen). There is no second entry point and no table of accepted strings: every accepted
  code must pass `valid()`.

---

## 7. Validation evidence

**Observed (emulator / live debugger)**
- Screens: title, attract, main menu, Options, password keypad (8×4 alphabet, 6 slots), hub,
  level card; `BBBBBB` accepted from a fresh keypad.
- `H0X1S2` and `H0X1J2` each hit accept breakpoint `0x0801AEEA`; RAM exactly as predicted;
  level card re-printed the entered code.
- `BBBBBH` and `BBBCBB` hit reject breakpoint `0x0801AC56`; decoded values `0x0A000000` and
  `0x00008000`; RAM remained zero; keypad stayed on screen with empty slots.
- The decoder's literal pool at `0x0801AC5C` points to `0x080D1E28`, whose bytes are the 32-symbol
  alphabet with `?` last.

**Derived (disassembly / offline reimplementation)**
- 5-bit LSB-first packing, the exact 30→state bit permutation, reserved bit 15, the three unary
  groups + marker rule, and the `strh`/`str`/`strb` state writes at `0x0801AE46` / `0x0801AE50` /
  `0x0801ADB2`.
- Exact valid-set size 1,777,664 with zero encode/decode round-trip failures.
- Single BL caller (`0x08020E94`) proves the keypad is the only validation surface.
- The 7-byte header-only difference from the 2-in-1 Revenge half.

**Inferred**
- Group→chapter labels and `H` bit→treasure identity (from published-code correlation and the
  ten treasure strings; not isolated one bit at a time). `W` bits 16–17 and `B` lack published
  isolates; `B` is demonstrably not the HUD difficulty.
- The return-2 path against `0x03000664` is treated as dead code, as in the prior report.

---

## 8. Unknowns

* Per-bit treasure names within `H` were not mapped 1:1; the 3-bit group structure is proven.
* `B` and `W` bits 16–17 have no isolated in-game label; they are carried and decoded but only
  appear in combined "all levels"/"all bosses" codes.
* The cursor/buffer state after a rejected code was not characterised (it is not a clean reset to
  `B`); this is why each code here was tested from a fresh keypad. It does not affect validity.
* No attempt was made to identify individual level-entrance artwork or to decompress game assets.

---

## 9. Tooling

| Method | Purpose |
|---|---|
| `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd` | Phase 0 identity |
| `cmp -l` against the 2-in-1 Revenge half | proved a 7-byte, header-only difference |
| `strings -t x`, `grep -abo` | recon; located alphabet and the false-positive `"level select"` credit |
| `arm-none-eabi-objdump -D -b binary -marm -M force-thumb --adjust-vma=0x08000000` | decoder/encoder/state-write disassembly |
| Python BL scanner | single caller at `0x08020E94` |
| `codec.py` (work dir) | `to_val`, `split`, `join`, `valid`, `encode`; exact enumeration and published-code check |
| mGBA 0.10.5 `-d` debugger over a PTY | `b/t` breakpoints, `r/4`/`r/2`/`r/1` live RAM reads |
| Xvfb + openbox + xdotool + scrot + ImageMagick + tesseract | screen walk and state detection |
| web search (IGN/GameFAQs/Fandom/planetcheats) | published-code recon; pages treated strictly as data |

Work artifacts (screenshots, scripts, logs) were kept in `/tmp/spongedutchman/`;
notably `shots/p_novel2_levelcard.png`, `shots/p_novel_levelcard.png`,
`shots/p_after_rej_reserved.png`, `codec.py`, `pty_exp.log`. No ROM, graphics, audio or game text
is redistributed in this report — only addresses, algorithms, hashes and short identifiers.

---

## 10. Legal note

Analysis was performed on a legally obtained ROM for research. No copyrighted asset is
reproduced here.
