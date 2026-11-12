# Dave Mirra Freestyle BMX 2 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Dave Mirra Freestyle BMX 2/Dave Mirra Freestyle BMX 2.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `DAVE MIRRA F` |
| Game code | `AX2E` (USA) |
| Maker | `51` (`0x35 0x31`) |
| Version | 0 |
| Complement | `0xBA` (matches computed value) |
| Header checksum field | `0x0000` (zeroed — header was rebuilt; complement is valid) |
| Entry word | `0xEA00002E` (stock GBA branch to `0x080000C0`) |
| Logo | intact, single hit at file offset `0x04` |
| Embedded-header scan | exactly one Nintendo logo in the image → single ROM, no pack |
| MD5 | `87faeacbfe02c12d1fa89b41ef1d676e` |
| SHA-1 | `3b86100fce6fda95b46c0d9e02d08052e69c2c2c` |
| SHA-256 | `b15fb51fae042c26fb09a6f556233b3e06828ecb4b83a54f25ff35fad77eacc6` |

No cracktro, trainer, or patched entry branch: first 4 KiB contains only the stock
crt0/vector table and no ASCII banners. The only anomaly is the zeroed header
checksum, the expected artifact of a rebuilt (but otherwise stock) header.

## 2. Executive summary

This GBA SKU is a different game from the PS2/GameCube/Xbox versions (Full Fat,
not the console engine). It has **no password system and no cheat menu**: there
is no password/cheat/code/debug string in the ROM, no text-entry surface, and
every menu is a normal game menu.

It does contain **one hidden button code on the pause screen**:

> **Left, Right, Left, Right, Up, Down, L, R** — at the pause menu.

Entering it executes a dedicated callback `0x080085B8` that stores `0xFFFF` into
the 16-bit global word at **`0x03001608`**. The word is an achievement/objective
latch (bit 3 is set by the "all 10 stars collected" objective check at
`0x0800C34E`). The pause code sets all 16 bits.

Static analysis of all 4 instruction sites that touch `0x03001608` (whole-ROM
Thumb scan) and read-watchpoints on title, main menu, options, level select,
session pause and gameplay show **no code ever branches on the latched bits**: it
is a write-only/dead developer latch in this build. No visible or RAM state change
beyond the latch itself was observed. That is reported as a bounded result, not
as "unknown whether the code works": the code is real, the write is proven, and
the absence of a consumer is proven for this image.

The widely published console master code
(`Up, Right, Down, Left, Right, Right, Up, Down, Left, Right, Up, Left, Right,
Right, Down` + face button) **is not in this ROM in any key-mask encoding** and
does nothing on the GBA beyond navigating menus. GameFAQs' GBA cheats page copies
that console code; it is not a GBA code.

## 3. How to reproduce

Emulator: mGBA (SDL) under Xvfb, `SDL_AUDIODRIVER=dummy`, 3× scale.
Default mGBA SDL keymap used: **A = `x`**, **B = `z`**, **L = `a`**,
**R = `s`**, **Start = `Return`**, **Select = `BackSpace`**, D-pad = arrows.
Hold keys 50–100 ms; shorter taps can be missed.

Observed path from a cold boot (no save data):

1. Boot; wait ~7 s for the title (`PRESS START`).
2. `Return` → main menu (RAM-verified: pointers to `PROQUEST`, `SESSION`,
   `FREERIDE`, `2 PLAYER`, `OPTIONS` at `0x020110ec`…`0x0201120c`).
3. `Down`, `A` → rider select (pointers to `continue`, `biography`,
   `edit stats`, `select bike` at `0x02011f2c`…`0x02012004`).
4. `Right`, `A` → level select (`dLEVEL SELECT` pointer appears at
   `0x03007cfc`; level names such as `WOODWARD` at `0x03007d48`).
5. `A`, `A` → in-game.
6. `Start` → pause menu (session mode: `CONTINUE`, `MUSIC TRACK:`, `END RUN`
   at `0x020188ec`, `0x02018934`, `0x0201897c`).
7. Enter **Left, Right, Left, Right, Up, Down, L, R** (≈60 ms press, 200–250 ms
   gap).
8. Read `0x03001608`: `0x0000` before, `0xFFFF` after.

The same sequence entered on the main menu does **not** set the word (the
matcher is only instantiated by the pause-screen function).

## 4. Address map

| ROM address | File offset | Meaning |
|---|---|---|
| `0x08015B6C` | `0x15B6C` | Joypad poll: reads `0x04000130`, stores active-high held keys |
| `0x03007300` | IWRAM `0x7300` | Held keys, active-high (`~KEYINPUT`; idle `0xFC00`) |
| `0x03007304` | IWRAM `0x7304` | Pressed-this-frame word (edge helper) |
| `0x03007400` | IWRAM `0x7400` | Second copy of held keys, used by the sequence matcher |
| `0x030012E0` | IWRAM `0x12E0` | Frame counter used by the matcher |
| `0x08015C94` | `0x15C94` | Sequence-matcher **init** (state, table, out array, len, timing, callback) |
| `0x08015CDC` | `0x15CDC` | Sequence-matcher **update** (call once per frame) |
| `0x08015C20` | `0x15C20` | Per-step matcher (`held & mask == mask`, 65-frame window) |
| `0x08015C88` | `0x15C88` | Entry initialiser |
| `0x08027174` | `0x27174` | **8-entry pause code table** (u32 masks) |
| `0x08027104` | `0x27104` | 12-entry music-track name pointer table |
| `0x080085C8` | `0x85C8` | Pause-screen function; builds matcher with table `0x08027174`, len 8 |
| `0x080085B8` | `0x85B8` | **Callback**: `strh 0xFFFF, [0x03001600+8]` |
| `0x03001608` | IWRAM `0x1608` | 16-bit **cheat/achievement latch** (target of the code) |
| `0x0800928A` | `0x928A` | Boot init: clears `0x03001608/0A/0C/0E` and `+4` |
| `0x0800C34E` | `0xC34E` | ORs bit 3 (`8`) into `0x03001608` when 10 star bits are set |
| `0x080096F2` | `0x96F2` | Second (only other) matcher caller: the 97-entry **trick** input system |
| `0x08025F60` | `0x25F60` | Trick table records, stride 44 (`{table_ptr, u16 len, …}`) |
| `0x08029740` | `0x29740` | Trick callback array, stride 44 |
| `0x0802B3DC` | `0x2B3DC` | Options screen definition (5 language lists + handler) |
| `0x0802B1EC` | `0x2B1EC` | Options item template: controls, music, sound fx, kids mode, credits, high scores |

Key mask constants (active-high, `0x03007300`/`0x03007400`):
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200`.

## 5. Algorithm

### 5.1 Sequence matcher (`0x08015C94` / `0x08015CDC` / `0x08015C20`)

```
init(state, table, out, len, window, callback, arg7):
    state[+4]  = 0                 # progress index
    state[+6]  = len
    state[+8]  = window            # 300 for the pause code
    state[+0]  = callback
    state[+12] = arg7
    state[+16] = table
    state[+20] = out
    for i in 0..len-1:
        out[i] = { start=0, done=0, mask=table[i], held=0 }   # 12-byte entries

match(entry, frame, held):
    if (held & entry.mask) == 0: return 0
    if entry.held == 0: entry.start = frame
    if frame - entry.start > 100: entry.start = frame; entry.held = 0
    entry.held |= (held & entry.mask)
    if (entry.held & entry.mask) != entry.mask: return 0
    if frame - entry.start > 65: return 0
    entry.done = frame; entry.held = 0; return 1

update(state, frame, held):
    i = state[+4]
    entry = out + i*12
    prev  = (i ? entry - 12 : 0)
    if match(entry, frame, held):
        if prev and (prev.done + state[+8]) < entry.done: return 0
        state[+4] = i + 1
    if state[+4] >= state[+6]:
        state[+4] = 0
        if state[+0]: call(state[+12])     # completed → callback
        return 1
    return 0
```

Masks are matched with `(held & mask) == mask`, **not equality**: extra buttons
held at the same time are tolerated. (Verified: holding Select for the whole
sequence still latches `0xFFFF`.)

### 5.2 Pause-screen instantiation (`0x08008608`)

```
state = sp+0x84; out = sp+0x9C
init(state, 0x08027174, out, 8, 0x12C /*300*/, 0x080085B9, 0)
every frame: update(state, frame, [0x03007400])
```

### 5.3 Callback (`0x080085B8`)

```
ldr r1, =0x03001600
ldr r0, =0x0000FFFF
strh r0, [r1, #8]      # 0x03001608 = 0xFFFF
bx lr
```

### 5.4 Latch initialisation and other writer

```
0x0800928A:  strh 0, [0x03001608]   # boot clear
0x0800928C:  strh 0, [0x0300160A]
0x0800928E:  strh 0, [0x0300160C]
0x08009290:  strh 0, [0x0300160E]
0x08009292:  str  0, [0x03001604]

0x0800C34A:  ldrh r2, [r1, #8]      # r1 = 0x03001600
0x0800C34C:  orr  r0, #8            # bit 3
0x0800C34E:  strh r0, [r1, #8]
```
The `0xC34A` path runs after counting ten set bits (`cmp r1,#10`) in the
current objective star mask and drawing the "ALL STARS COLLECTED!" text.

## 6. Tables

### 6.1 Pause button code (the only menu code)

| Step | Mask | Button |
|---:|---:|---|
| 1 | `0x020` | Left |
| 2 | `0x010` | Right |
| 3 | `0x020` | Left |
| 4 | `0x010` | Right |
| 5 | `0x040` | Up |
| 6 | `0x080` | Down |
| 7 | `0x200` | L |
| 8 | `0x100` | R |

Raw bytes at `0x08027174`:
`20 00 00 00  10 00 00 00  20 00 00 00  10 00 00 00
 40 00 00 00  80 00 00 00  00 02 00 00  00 01 00 00`

### 6.2 Trick-engine table (not cheats)

97 records at `0x08025F60`, stride 44; lengths: 28×1, 45×2, 15×3, 9×0.
Only 8 mask values occur: `0x10` R, `0x20` L, `0x40` U, `0x80` D,
`0x50` R+U, `0x60` L+U, `0x90` R+D, `0xA0` L+D. These are the in-game trick
inputs; they share the matcher but are **not** menu cheats.

### 6.3 Menus and their item counts (RAM-verified)

| Screen | Items |
|---|---|
| Title | `PRESS START` (Start only) |
| Main menu | PROQUEST, SESSION, FREERIDE, 2 PLAYER, OPTIONS (5) |
| PROQUEST | continue game, new game, load game (3) |
| Rider select | continue, biography, edit stats, select bike (4) + 14-rider roster |
| Mode select (2 PLAYER) | full run, star collector (2) |
| Level select | LEVEL SELECT; level list; `EXP TO OPEN` / `TO OPEN USE PROQUEST` |
| Options | controls, music, sound fx, kids mode, credits, high scores (6) |
| Session pause | CONTINUE, MUSIC TRACK: (12-track selector), END RUN (3) |
| PROQUEST pause | retry, level select, rider select, save game, quit (5) |

Options runtime list has 8 slots: the two extra rows (no static label, width 63,
at y=56 and y=82) are the value read-outs inserted beside MUSIC and SOUND FX
(inferred from their positions; not selectable).

No `debug`, `password`, `secret`, `unlock`, or `cheat` UI string exists.
`CHEAT` occurs only inside the score-rating table
(`CHEATING 2160`, `REALLY CHEATING 2340`, `0x7A15B0`/`0x7A15C8`).

## 6b. Enumeration

**Space definition.** The pause code is a fixed 8-step lookup table of key masks
(table size 1 sequence, length 8). Each step matches when the required mask is a
subset of the held-key word, so the representable input space is
`(2^10−1)^8 = 1,023^8` key-state streams, of which exactly one ordered 8-step
stream (the table) completes the sequence. The matcher is shared with the trick
engine; a whole-ROM scan found only **two** callers of `0x08015C94`:
the pause screen (`0x08008608`) and the 97-entry trick engine (`0x080096F2`).
Therefore there is exactly **one** menu button code in the ROM.

**Novel code.** `L, R, L, R, U, D, L, R` at the pause screen. This sequence is
not in any published GBA list (there is no GBA cheat list for this title; the
published master code is a console code that is absent from this ROM). It was
entered on the real pause screen and RAM-verified:
`0x03001608` goes `0x0000 → 0xFFFF`.

**Bounds proven by rejection (all entered on the real pause screen, same timing):**

| Test | Input | `0x03001608` | Result |
|---|---|---|---|
| Correct | `L R L R U D L R` | `0xFFFF` | accepted |
| Complete | `L R L R U D L R` with Select held | `0xFFFF` | accepted (extra keys tolerated) |
| Wrong last step | `L R L R U D L L` | `0x0000` | rejected |
| 7-step prefix | `L R L R U D L` | `0x0000` | rejected |
| Wrong gate | same 8-step code on main menu | `0x0000` | rejected (no matcher on that screen) |
| Published console code | `U R D L R R U D L R U L R R D + A` on main menu | `0x0000`; only menu navigation | no effect |

The 6-second and 15-second inter-step gap tests still latched `0xFFFF` on the
pause screen; the matcher's nominal 300-frame inter-step window does not reject
a slow human entry in this context, so timing is not a practical bound here.
Length and order are the effective bounds.

**Latch semantics (derived).** `0x03001608` is a 16-bit objective/achievement
bitfield. Bit 3 is ORed by the ten-star objective completion path
(`0x0800C34E`). The pause code sets all 16 bits. A whole-ROM Thumb scan finds
only four accesses to the halfword — boot clear (`0x0800928A`), the pause
callback (`0x080085BC`), and a read-modify-write OR of bit 3
(`0x0800C34A/0x0800C34E`). No branch ever tests the word, and a read watchpoint
on `0x03001608` fired zero times over six screens (title, main menu, options,
level select, session pause, gameplay). It is therefore a **dead developer
latch**: the sequence is a real, intended pause-screen code, but this retail
build exposes no effect from it.

## 7. Validation evidence

**Observed** (mGBA, RAM reads from mGBA savestates / debugger):
- `0x03001608` = `0x0000` on the pause screen before the code; `0xFFFF` after.
- Wrong order, 7-step prefix, and the code on the main menu leave it `0x0000`.
- Holding Select throughout does not block the code (`0xFFFF`).
- Pause menu item labels and counts listed in §6.3; music listbox state is
  identical with and without the latch.
- The published console sequence only navigates menus on this ROM.
- Read watchpoint on `0x03001608`: no read on title, main menu, options, level
  select, session pause, or gameplay (including a running game frame counter).

**Derived** (disassembly, exact bytes):
- Matcher algorithm and table at `0x08027174`; callback at `0x080085B8`;
  length 8 and window 300 passed at `0x08008608`.
- All four accesses to `0x03001608`; bit 3 writer; boot clear.
- Console master sequence absent from ROM as u16/u32 masks (including 4- and
  6-press prefixes).
- Single Nintendo logo/header (no multi-game pack); stock entry branch.

**Inferred**:
- The two unlabelled options rows are the numeric read-outs for MUSIC and
  SOUND FX (positions and zero static labels).
- The latch's original purpose was an achievement/objective record; its consumer
  was removed or never linked in this build.

## 8. Unknowns

- No consumer of `0x03001608` exists in this image, so the historical intent of
  the pause code cannot be observed. It is not a "lost feature" gate that can be
  opened by another input: the only writer besides boot and the code is the
  ten-star objective, and no code reads the word.
- The language-selection screen (5 languages, code near `0x0800FD80`, list
  `0x0802BB34`) was located statically but was not reached in a normal boot
  (English default); it writes the language byte at item `+0x1F`. It is a
  configuration screen, not a cheat.
- Console-version unlock lists were not tested one by one because their key
  tables are not present in the GBA image; the master prefix and the ROM-wide
  mask scan are the bounding evidence.

## 9. Tooling

- `mgba` (SDL) under `Xvfb :278` + `openbox`, `SDL_AUDIODRIVER=dummy`.
- `xdotool` for input; mGBA savestates (`.ssN`) decompressed with Python
  `zlib` (`gbAs` chunk) for RAM diffs and pointer scans.
- mGBA command-line debugger (`mgba -d`) for `r/2`, `w/2`, and `watch/r`
  read watchpoints.
- `arm-none-eabi-objdump -M force-thumb` for targeted disassembly.
- `capstone` for the whole-ROM Thumb scan of `0x03001608` accesses and
  `BL` call-site scans.
- Python scripts: savestate loader/differ, label-pointer scanner, mask/table
  dumper (kept in `/tmp/opencode/davemirra2`).

No ROM, graphics, music, or extracted text is redistributed.
