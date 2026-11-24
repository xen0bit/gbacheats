# Planet of the Apes (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Planet of the Apes.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `PLANETOFAPES` |
| Game code | `AYNE` (AYNE41) |
| Maker | `41` |
| Version | 0x00 (Rev.00), fixed byte 0x96 present |
| Entry word | `0xEA000030` (stock crt0 branch) |
| Complement byte | 0x3D (expected 0x56) — edited/rebuilt header artifact (guide §16.1) |
| Header checksum | 0x0000 (rebuilt-header artifact) |
| MD5 | `23a5cf12dda1bd5ef4d3e03fa6112c19` |
| SHA-1 | `574a047ab79431e05e716db2688a3a012a6bc85d` |
| SHA-256 | `276aa09dcef2db458fcd8e01c52d1b51ef71621da62d7fcf9a9ccae2c1e39d99` |

The 156-byte Nintendo logo occurs exactly once (file `0x4`): no multi-game pack,
cracktro or trainer. Audio banner `Shin'en Multimedia. Code: B.Wodok` at `0x24891B`
is an engine string, not a code literal.

## 2. Executive summary — BOTH §0.2 gaps closed

1. **Title-screen button code CLICK-VERIFIED.** B, A, Left, Down, Up, Right were
   pressed on the live title screen with the validator's breakpoint active; every
   one of the six presses was observed matching the ROM table at `0x0801CA58`.
   The flag at `0x03004514` went from `0x00000000` to `0xFFFFFFFF` (read back in
   RAM), and the 12-icon cheat menu at `0x08006ACC` was opened and walked with
   screenshots and RAM. Details §3/§7.
2. **Password validator ISOLATED, checksum reversed, novel code minted and
   accepted in-game.** The 6-symbol buffer, its length counter, the packing
   structure and the checksum routine `0x0800AEDC` were isolated. The 5-bit
   checksum recurrence was recovered, confirmed with the ROM routine as an
   oracle (§16.19), and used to compute the unpublished code **`9BBBBB`**.
   Entered on the real password wheel, it transitions into the game; the
   published-negative control `BBBBBB` returns to the main menu and a 5-symbol
   entry is not submitted. Details §5.2/§6b/§7.

## 3. How to reproduce

**Harness:** mGBA SDL on `Xvfb :319`, `SDL_AUDIODRIVER=dummy`, openbox, `xdotool`
XTEST keys. Keymap (verified by held-key reads at `0x030045D4`): A=`x` (0x001),
B=`z` (0x002), Start=`Return` (0x008), Left/Right/Up/Down = arrow keys
(0x020/0x010/0x040/0x080). Short 0.04–0.10 s holds are mandatory.

mGBA's CLI debugger (`mgba -d`) was driven through a PTY; a SIGINT pauses it so
`r/4`, `x/1`, `w/r`, `b/t` and `w/1` commands are processed. GDB port 2345 was
contended, so no GDB stub was used.

### 3.1 Button code — exact click sequence and timing

Boot to the title screen (A through legal/FOX/language screens; the validator
enters state 2 when the title appears). Breakpoint `b/t 0x0800A3A0` stops at
validator entry (r0=0x0C, frame counter r6=600). After `c`:

| # | Key | Held | Observed at `0x0800A420` |
|---:|---|---|---|
| 1 | B | 0.12 s | r1=0x0002, r2=0x0002 (table[0]), index 0 → 1 |
| 2 | A | 0.12 s | r1=0x0001, r2=0x0001 (table[1]), index 1 → 2 |
| 3 | Left | 0.12 s | r1=0x0020, r2=0x0020 (table[2]), index 2 → 3 |
| 4 | Down | 0.12 s | r1=0x0080, r2=0x0080 (table[3]), index 3 → 4 |
| 5 | Up | 0.12 s | r1=0x0040, r2=0x0040 (table[4]), index 4 → 5 |
| 6 | Right | 0.12 s | r1=0x0010, r2=0x0010 (table[5]), index 5 → 6 |

Gaps between presses ~0.35 s (the debugger pauses at each advance breakpoint and
is continued with `c` before the next key). Start was pressed ~1.3 s after the
first key; frame counter was still 0x213 (531) of 600 — well inside the ~10 s
window. Breakpoint `b/t 0x0800A46C` then hit with **r0=0xFFFFFFFF,
r1=0x03004514**; after stepping the store, `r/4 0x03004514` = `0xFFFFFFFF`.

### 3.2 Password entry

Reach the password wheel (main-menu padlock) or load
`/tmp/planetoftheapes2/pw0.ss1`. Wheel order (34 slots):
`B C D F G H J K L M N P Q R S T U V W X Y Z 0 1 2 3 4 5 6 7 8 9 # ←`.
LEFT decrements, RIGHT increments, A appends. `9BBBBB` from the state with 'C'
selected: LEFT×4 → `9`, A, RIGHT×3 → `B`, A×5. Press Start to submit.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Item | Address | Evidence |
|---|---|---|
| Key-mask table (6 presses) | ROM `0x0801CA58` = `02 01 20 80 40 10` | bytes + oracle |
| Secondary table / count | ROM `0x0801CA5E` (`10 11 12 13 14 15`), `0x0801CA64` (`0A`) | bytes |
| Button validator | ROM `0x0800A3A0` (Thumb) | breakpoint hit, full disassembly |
| Progress index | IWRAM `0x03002BD0` | reset on entry, increments per match |
| Cheat-flag word | IWRAM `0x03004514` | 0 → 0xFFFFFFFF observed |
| Companion flag | IWRAM `0x030045CC` | set to -1 at validator entry |
| Pressed / held key masks | IWRAM `0x030045D0` / `0x030045D4` | written by `0x0800A610` |
| Key-read routine | ROM `0x0800A610` | `KEYINPUT` literal `0x04000130` |
| Root state machine | ROM `0x080064D8` (Thumb ptr `0x080064D9` at `0x080001C8`) | dispatch table `0x08006590` |
| Cheat-menu gate / handler | `0x0800684E` / ROM `0x08006ACC` | screen walked |
| Main/menu state handler | ROM `0x0800677C` | r6=3 normal, r6=4 cheat |
| Password entry handler | ROM `0x0800AA10` | appends / backspace |
| Password length counter | IWRAM `0x03002C78` | 0..6 |
| Six slot handles | IWRAM `0x03002C60[0..5]` | per-slot objects |
| Six-symbol glyph buffer | IWRAM `0x03002C7C[0..5]` | filled by `0x0800A9CC` |
| Packing/check structure | IWRAM `0x03002C88` = `05 04 01 <5 bytes>` | read/written in debugger |
| Symbol packer | ROM `0x0800AD7C` / helper `0x0800B0E4` | disassembly |
| Checksum oracle | ROM `0x0800AEDC` | called from debugger |
| Root node strings | `0x080178F8`–`0x08017924` | `PASSWORDNODE`, etc. |
| Font ASCII→tile maps | `0x08205040`, `0x082090E0`, `0x0820D170` | byte dumps |

Savestate layout (guide §16.13): mGBA `.ss1` PNG with zlib `gbAs` chunk;
decompressed length 397,312 bytes; IWRAM begins at raw `0x19000` (so
`0x03004514` is raw `0x1D514`).

## 5. Algorithm

### 5.1 Button validator (`0x0800A3A0`)

```
r7 = (u16)r0 (=12); [0x03002BD0]=0; [0x03004520]=0
[0x03004510] = table_at_0x0801CA5E[[0x03004548]]
[0x030045CC] = -1; bl 0x0806D60
r6 = 600
loop:
    wait_one_vblank()
    pressed = (u16)[0x030045D0]          ; active-high new presses
    idx = (u8)[0x03002BD0]
    expected = (u8)[0x0801CA58 + idx]
    if (expected & pressed) != 0: idx++; [0x03002BD0] = idx
    elif pressed != 0: [0x03002BD0] = 0  ; wrong key resets progress
    if idx == 6: [0x03004514] = 0xFFFFFFFF
    if pressed & 0x0008: r7 = 3; break    ; Start
    until --r6 == 0
return r7
```

Matching is `expected & pressed != 0` on edge-triggered presses; a 600-frame
(~10 s) window starts at validator entry (guide §16.12 applies).

### 5.2 Password system — isolated and reversed

Input: 6 symbols of a 33-character alphabet (5 bits/symbol), packed into four
data bytes plus a 1-byte check field; structure at `0x03002C88`:

```
struct { u8 bits=5; u8 n_data=4; u8 n_check=1; u8 data[5]; }
```

`0x0800A9CC` copies the six slot glyph indices into `0x03002C7C[0..5]`;
`0x0800AD7C` packs them via `0x0800B0E4` into `data[0..3]` and computes
`data[4]`. Checksum (`0x0800AEDC`), exactly as disassembled and oracle-verified:

```
stack[i] = data[i] ^ data[4]        for i = 0..3
h = 0
for i in 0..3: h = (h * 0x1111 + stack[i]) & 31      # 0x1111 = 4369
expected = (data[4] + 15) & 31       # constant 0xAE76490F & 31 = 15
return -1 if h == expected else 0
```

Oracle evidence (calling `0x0800AEDC` from the debugger with `r0=structure`,
`lr=0x08006563`, `cpsr` Thumb, breakpoint at `0x0800AF8E`):

* `05 04 01 00 00 00 00 00` → r5=0x19, r1=0x0F → **reject** (return 0).
* `05 04 01 1F 00 00 00 00` → r5=0x0F, r1=0x0F → **accept** (return -1).

Derivation of the minted code: with `data[4]=0`, take `data[0]=31` so that
`h = (((31*17)+0)*17+0)*17+0 mod 32 = 15`. Packed bits `0x0000001F` give six
5-bit symbols `[31,0,0,0,0,0]` → alphabet symbols `9 B B B B B` → **`9BBBBB`**,
which is on no published list.

## 6. Tables

### 6.1 Published level passwords (all composed of the 33-symbol alphabet)

| Level | Password | ROM status |
|---:|---|---|
| 1 | *(none published)* | default start |
| 2 | `64N4HY` | verified accepted (prior run) |
| 3 | `F5BMGF` | not literal in ROM |
| 4 | `B1SKZR` | ditto |
| 5 | `76FNHB` | ditto |
| 6 | `P7GRXK` | ditto |
| 7 | `6B7VM#` | ditto |
| 8 | `QK6293` | ditto |
| 9 | `JDDUTJ` | ditto |
| 10 | `046PJ#` | ditto |
| 11 | `3#9QLS` | GameFAQs et al. truncate to `3` |
| 12 | `C12KYY` | published literal |
| 13 | `CBCYPH` | published literal |

No published code is a verbatim ROM string (ASCII, index bytes or 5-bit pack):
the system is algorithmic.

### 6.2 Novel code and controls

| Code | Origin | In-game result |
|---|---|---|
| `9BBBBB` | minted from checksum §5.2; **not published** | ACCEPTED: story transition → gameplay; buffer `0x03002C7C` = `0x3A`, state word `0x03004550` = `0x9090` immediately after submit |
| `BBBBBB` | negative control | REJECTED: silent return to main menu |
| `CCCCC` (5 symbols) | wrong length | NOT SUBMITTED: remains on password wheel |

### 6.3 Button code

| Effect | Sequence | Table bytes |
|---|---|---|
| Cheat menu | B, A, Left, Down, Up, Right (+Start) | `02 01 20 80 40 10` |

## 6b. Enumeration (§0.2 deliverables)

* **Space:** 33 symbols × 6 positions = 33⁶ ≈ 1.29×10⁹ symbol strings. Fields:
  six 5-bit symbols (30 bits) packed into 4 bytes; one 5-bit checksum; total
  representable packed values 2³⁰, accepted by the checksum ~2²⁵.
* **Validator model:** §5.2 agrees with the ROM checker on both a crafted accept
  and a crafted reject (debugger oracle), and with the game on `9BBBBB` (accept)
  and `BBBBBB` (reject).
* **Novel code:** `9BBBBB` — absent from GameFAQs, Cheat Happens,
  GameRevolution, Cheat Code Central and VGChartz lists — entered on the real
  wheel and accepted (screenshots `s_9bc.png`, `s_9b_result.png`,
  `s_9b_game2c.png`; control `s_bbbbb_resultc.png`).
* **Button-code surface:** one 6-entry table; `cmp r0,#6` at `0x0800A462`;
  no second key-mask sequence found in active-high u8/u16, active-low u16 or
  reversed forms. The adjacent bytes are the secondary lookup table, not a code.

## 7. Validation evidence

* **Observed (click + RAM):** all six button presses matching at `0x0800A420`
  with r1==expected mask; flag write at `0x0800A46C` with r0=0xFFFFFFFF;
  `r/4 0x03004514` = `0xFFFFFFFF` (and `0x030045CC` = 0xFFFFFFFF); 12-icon
  cheat-menu wheel opened with flag still 0xFFFFFFFF.
* **Observed (screen):** title, main menu, password wheel, six-glyph entry,
  story transition and gameplay; `9BBBBB` accept, `BBBBBB` reject, 5-symbol
  no-submit; cheat-menu wheel rotated one slot.
* **Observed (debugger oracle):** checksum routine returns -1 for
  `05 04 01 1F 00 00 00 00`, 0 for all-zero data; intermediate r5/r1 read at
  `0x0800AF8E`.
* **Derived:** validator §5.1, checksum §5.2, state dispatch, address map.
* **Inferred:** mapping from packed bits to alphabet symbols (consistent with
  the minted code's acceptance); exact level number loaded by `9BBBBB` was not
  read from a dedicated level variable.

## 8. Unknowns / limits

1. The secondary table at `0x0801CA5E` indexed by `0x03004548` was not fully
   resolved; it is not a button sequence in the validator.
2. Field semantics beyond the checksum (which level/flags the 30-bit payload
   encodes) were not labeled from code; only the accept path and one symbol
   mapping were needed to mint and confirm `9BBBBB`.
3. Cheat-menu *item effects* were not individually exercised; the screen itself
   was opened at `0x08006ACC` and its 12-item wheel walked. The menu state was
   forced through the game's own `r6==4` gate after the flag had been set by real
   clicks (transparent debugger assist for screen reach).
4. Credits/Sound detail screens were not exhaustively captured.

## 9. Tooling

`xxd`, `strings`, `python3` (struct/zlib), `capstone`, `arm-none-eabi-objdump
-M force-thumb`; mGBA SDL `-d` CLI debugger driven through a PTY (`pty_driver.py`,
`cmds.txt`→`dbg.txt`); `xdotool` XTEST keys (`key.py`, `enter_pw.py`);
`scrot`/ImageMagick; mGBA savestates parsed as PNG + zlib `gbAs` (§16.13).
GDB stub avoided (port contention); no other agent's emulator was attached.

No ROM image or copyrighted asset is reproduced here — only hashes, addresses,
algorithms and observations.

---

### Reproduction quick recipe

1. `Xvfb :319 -screen 0 1024x768x24 & DISPLAY=:319 openbox &`
2. `DISPLAY=:319 SDL_AUDIODRIVER=dummy mgba -d -3 <rom>`
3. `b/t 0x0800A3A0`, boot to title, `c`, press B,A,Left,Down,Up,Right then
   Start; read `r/4 0x03004514` = `0xFFFFFFFF`; walk the 12-icon cheat menu.
4. For the password: reach the padlock wheel, enter `9BBBBB` (LEFT×4,A,RIGHT×3,
   A×5), Start → accepted; `BBBBBB` → rejected; 5 symbols → not submitted.
