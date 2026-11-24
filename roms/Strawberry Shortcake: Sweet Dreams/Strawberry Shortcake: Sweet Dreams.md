# Strawberry Shortcake: Sweet Dreams (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Strawberry Shortcake: Sweet Dreams.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `SWEET DREAMS` |
| Game code | `B4TE` |
| Maker code | `5G` (Majesco Entertainment) |
| Revision | `Rev.00` (version byte `0x00`) |
| Fixed byte / complement | `0x96` / `0x62` |
| Header checksum | `0x0000` (rebuilt-header artifact; entry word is the retail `0xEA00002E`) |
| MD5 | `6889044339203f0bec9f20c478772079` |
| SHA-1 | `77210297d7d2890e0d2c34b5a8aa933857486b57` |
| SHA-256 | `b41e30193a241a203ce1418e18d9823b0a89e83ecb33bd194448c65bc4c130ef` |
| Legal splash | "Developed by Gorilla Systems Corporation. Published by Majesco Entertainment" (2006) |

Engine: C++ with a registered scene system (RTTI-style `{name, size, ctor}` descriptors and
`{0, function}` vtable blocks). Scene-name table at `0x0802E424`; scene registry mirror in EWRAM
at `0x02010FC0` onward.

## 2. Executive summary

**There is exactly one in-game cheat: a hidden 10-press button code that launches a Pong minigame.**

Enter it **on the Credits screen** (title menu → CREDITS → wait for the scrolling credits):

> **Hold L + R throughout, then press:**
> **↑ ↑ ↓ ↓ ← → ← → A B**

On acceptance the active scene key at EWRAM `0x02010FF0` changes from `"Credits"` to `"Pong"`,
the screen turns white with two blue paddles and a ball, and the minigame is fully playable
(verified: left paddle moves on ↑/↓, ball moves, score increments).

The input path was reverse engineered end-to-end: a 16-entry press-history ring buffer at
`0x02000A0C` is compared against a hard-coded 10-symbol sequence by a single validator at
`0x0802AC88`, called from exactly one site (`0x08012C86`). There are **no password / text-entry
screens, no published code lists, and no other sequence checkers in the image**. The accepted set
has exactly one member; five near-miss variants were rejected in-game, proving the bounds.

A separate save-bit unlock system exists ("MY SWEETS": 8 collectible sets × 20 items, each with a
lock icon). It is progress-gated save data, **not** a code — documented in §8.

## 3. How to reproduce

1. Emulator: mGBA 0.10.5 under Xvfb (`SDL_AUDIODRIVER=dummy`), keymap A=`x`, B=`z`, L=`a`, R=`s`,
   Start=`Return`, D-pad = arrow keys.
2. Boot; press Start through the splash screens until the title menu (NEW GAME / MY SWEETS /
   CREDITS) appears. Select **CREDITS** (Down, Down, A) and wait until the candy-heart credits
   background is scrolling.
3. Hold **L+R**. Tap, in order: **Up, Up, Down, Down, Left, Right, Left, Right, A, B**. Release L+R.
   ~0.5 s later the Pong minigame appears.
4. In Pong: ↑/↓ move the left paddle; the ball bounces and scores the right player.
5. Negative control: reload a Credits savestate and repeat with the final B replaced by A — nothing
   happens (see §6b).

All screenshots and scripts were in `/tmp/strawberrydreams/` (key files:
`credits_ready.png`, `credits_code_b.png`, `pong_play1.png`, `montage_credcode.png`,
`test_correct.png`, `test_wrong_last_B_to_A.png`, `test_nine_presses.png`).

## 4. Address map

| Address (ROM/ RAM) | Meaning |
|---|---|
| `0x0802AB8C` | Joypad poll: reads `KEYINPUT` (`0x04000130`), XORs with `0x03FF` (active-high), writes pressed/held/released at `0x02000A04/06/08`; on each **new press** appends the held mask to a 16-entry ring at `0x02000A0C`, advancing index at `0x02000A2C` (mod 16). |
| `0x0802AC88` | **Validator**: `check_seq(u16 *expected, int len)` — compares the last `len & 15` ring entries with `expected`; returns 1 on match, 0 on mismatch. |
| `0x08012C7C` | Sole caller of the validator (`BL` at `0x08012C86`) with `expected = 0x0803C8A0`, `len = 10`. On match: installs the Pong method block into `[this+4]` and sets a flag at `+8`. |
| `0x0803C8A0` | The 10 accepted button masks (10 × `u16`), immediately followed by the literal `CCreditsScene` (`0x0803C8B4`). |
| `0x0803C860` | Pong method block (`"Pong"` name at `0x0803C860`; methods `0x08012C45`, `0x08012C69`, `0x08012C7D`, `0x08012CBD`, `0x08012CC1`). |
| `0x0803C8C4` / `0x0803C9D8` | Descriptors keyed `"Pong"` / `"CPongScene"` in the scene registry. |
| `0x0803C948` | Pointer `0x08013081` — the Pong-scene factory is registered in a Minigames method table. |
| `0x08015538`–`0x0801554C` | Minigames menu string pointers: MAIN MENU, SLEEP BUG, BUTTERFLY RALLY, FACTORY FUN RIDE, DREAM CATCHER, CATCH PIE MAN (6 visible entries; Pong is **not** listed). |
| `0x02000A0C` / `0x02000A2C` | EWRAM: press-history ring buffer / next-write index. |
| `0x02010FF0` / `0x02010FD0` | EWRAM: current / previous 16-byte scene key (`"Credits"` → `"Pong"` on success). |
| `0x02011520` | EWRAM scene registry: `{char key[16], char pad[16], void *descriptor}` records (Pong, Credits, CatchMe, DreamCatcher, …). |

File offset = ROM address − `0x08000000` (flat 4 MiB image).

## 5. Algorithm

```
; poll (0x0802AB8C)
held_prev = [0x02000A06]
raw       = KEYINPUT ^ 0x03FF          ; active-high
pressed   = raw & ~held_prev
[0x02000A04] = pressed
[0x02000A08] = held_prev & ~raw
[0x02000A06] = raw
if pressed != 0:
    ring[index] = raw
    index = (index + 1) & 15

; validator (0x0802AC88)
check_seq(expected, len):
    len &= 15
    start = (index - len) & 15
    for i in 0 .. len-1:
        if ring[(start + i) & 15] != expected[i]:
            return 0
    return 1

; sole caller (0x08012C7C), runs while the Credits scene is active
if check_seq(0x0803C8A0, 10):
    obj = [this + 4]
    [obj]     = 0x0803C860       ; install Pong methods
    [obj + 8] = 1                ; activate
```

**Important input semantics:** only *new presses* append to the ring. Holding L+R and tapping the
10 direction/action keys yields exactly the 10 required entries with no gap entries; L+R must be
down before the first ↑ and held until after B.

## 6. Tables

### 6.1 Accepted sequence (ROM `0x0803C8A0`)

| # | Raw mask | Buttons (active-high GBA bits) | Key |
|---:|---:|---|---|
| 1 | `0x0340` | L + R + Up | `a`+`s`+`↑` |
| 2 | `0x0340` | L + R + Up | `↑` |
| 3 | `0x0380` | L + R + Down | `↓` |
| 4 | `0x0380` | L + R + Down | `↓` |
| 5 | `0x0320` | L + R + Left | `←` |
| 6 | `0x0310` | L + R + Right | `→` |
| 7 | `0x0320` | L + R + Left | `←` |
| 8 | `0x0310` | L + R + Right | `→` |
| 9 | `0x0301` | L + R + A | `x` |
| 10 | `0x0302` | L + R + B | `z` |

Bits: `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040,
Down=0x080, R=0x100, L=0x200`. This is the Konami code with L+R held and a trailing **A then B**
(not B then A).

### 6.2 Scene-state evidence

| Address | Credits state | After code |
|---|---|---|
| `0x02010FF0` (16 bytes) | `"Credits\0…"` | `"Pong\0…"` |
| `0x02010FD0` (16 bytes) | `"Options\0…"` | `"Credits\0…"` |

### 6.3 Published codes

Web search (3rd party cheat index-style queries, 2026-11-20) returned no published codes for this GBA SKU.
No code string appears literally in the ROM (the code lives as button masks, not ASCII). This
report's code is therefore not copied from any published list.

## 6b. Enumeration

**Space definition.** The system is a fixed-length button sequence, not a password:
10 presses, each an active-high 10-bit key mask; the only accepted sequence is the 10-entry table
at `0x0803C8A0`. There is no variable length, no checksum, no alphabet string, no user-controlled
sequence pointer and no second format. The complete accepted set has **exactly one member**
(selectable on the Credits scene; action = launch Pong).

**Completeness proof (static counts).**

* `BL` scan for the validator `0x0802AC88` over the whole 4 MiB image: **1 hit** (`0x08012C86`).
* Literal-pointer scan for the ring index `0x02000A2C`: 4 hits — writer (`0x0802ABDC`), two
  reset helpers (`0x0802AC1C`, `0x0802ACE4`) and the validator (`0x0802ACB8`): **1 matcher**.
* ROM literal `0x0803C8A0` (sequence table): **1 hit** (the validator caller).
* ROM literal `0x0803C860` (Pong method block): **1 hit** (installed by the same caller).
* No text/password entry surface exists: the only UI surfaces are title, MySweets, Credits,
  pause (PAUSE/CONTINUE/SAVE GAME/QUIT) and the six-item minigames menu; no keyboard field and
  no `strcmp` against user-entered text was found.

**In-game acceptance/rejection (all from a Credits-screen savestate, 2 s observation each).**

| Test | Sequence | Result |
|---|---|---|
| Correct code | ↑↑↓↓←→←→ A B (L+R held) | **ACCEPT** — Pong launched |
| Correct code (repeat) | same | **ACCEPT** — Pong launched |
| Wrong final button | ↑↑↓↓←→←→ A **A** | REJECT — stayed on Credits |
| Wrong 2nd press | ↑ **↓** ↓↓←→←→ A B | REJECT — stayed on Credits |
| Wrong length (9) | ↑↑↓↓←→←→ A | REJECT — stayed on Credits |
| L+R not held | same 10 directions alone | REJECT — stayed on Credits |
| Swapped ←/→ | ↑↑↓↓ **→←→←** A B | REJECT — stayed on Credits |

Detector: Pong screen is >90 % white with blue paddles; Credits screen has 0 % white.
Acceptance was also confirmed in RAM (`0x02010FF0` `"Credits"` → `"Pong"`, §6.2).

**Novel code.** None can exist: the validator's `expected` pointer and length are hard-coded
constants, so the accepted set is a singleton. The seven tests above characterise the entire
space; the five rejects are the *undocumented combinations* required by §0.2 and they prove the
bounds (one symbol, one length, L+R mandatory, order fixed). No generated novel code is claimed.

## 7. Validation evidence

* **Observed** — mGBA screenshots: `credits_ready.png` (scrolling credits), `credits_code_b.png`
  and `pong_play1.png` (white Pong field, blue paddles, ball, scores 0/0 then 0/8), paddle moved
  after ↑/↓; seven-test table in §6b; savestate RAM dumps `credits_state.bin` / `pong_active.bin`.
* **Derived** — disassembly of `0x0802AB8C`, `0x0802AC88`, `0x08012C7C`; sequence bytes at
  `0x0803C8A0`; pointer/BL counts in §6b.
* **Inferred** — the Pong scene factory is registered in a Minigames method table
  (`0x0803C948`), so the hidden minigame is developer-intended rather than stray code; the exact
  reason the code is gated to the Credits scene was not isolated (the sole caller is a method of
  the Pong/Credits method block).

## 8. Unknowns / other surfaces walked

* **MY SWEETS unlockables** (walked in full): 8 rows, each a character + food icon, `0/20` count
  and a closed-padlock icon; scrolling stops after the 8th row. This is save-bit progress data
  (§16.18), not a code; no input unlocks it. Not enumerated bit-by-bit.
* Code entered at the **title menu**, **in-game dialogue**, **a minigame (Sleep Bug)** and
  **MySweets** produced no Pong; on the title menu the trailing A press selects NEW GAME, which
  explains the failure there. Credits is the confirmed entry scene.
* Rejection after a close miss happens silently (no "invalid" message anywhere in the ROM).
* Pong appears to be session-only (RAM scene switch); persistence across a full reset was not
  tested.

No button codes other than the single 10-press sequence, no password validator, and no debug menu
were found. The bounded negative covers: all menu screens walked, the entire press-history
validator call graph (1 matcher), and the literal sequence table (1 entry).

## 9. Tooling

* `strings -t x -n 4`, `grep -iE` for recon; Python `struct` scans for literal pointers and Thumb
  `BL` targets; `arm-none-eabi-objdump -D -b binary -marm -M force-thumb --adjust-vma=0x08000000`.
* mGBA 0.10.5 under Xvfb `:318` with openbox, `SDL_AUDIODRIVER=dummy`; binary copied to
  `sd_mgba` to avoid a global `pkill -x mgba` loop launched by another job that was SIGKILLing
  unrelated emulator processes (exit 137).
* Input/screenshot helper `/tmp/strawberrydreams/ui.py`; savestate RAM reader
  `ssdump.py` (zlib-decompresses the `gbAs` chunk of mGBA `.ss1` PNGs; EWRAM at state offset
  `0x21000`); test harness `test_code.py`.
* No REA/Ghidra session was needed: the raw Thumb disassembly plus emulator and savestate RAM
  evidence resolved the feature completely.

**Legal note:** no ROM data or copyrighted graphics are redistributed here — only hashes,
addresses, algorithms, and references to locally captured evidence screenshots.
