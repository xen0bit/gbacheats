# The Incredible Hulk (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/The Incredible Hulk/The Incredible Hulk.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `HULKV1` |
| Game code / maker | `AHLE` / `7D` (Universal Interactive), version 0 |
| Entry word | `0xEA00002E` (stock crt0 branch — **not** a cracktro, §16.1) |
| Complement / header checksum | `0x01` / `0x0000` |
| MD5 | `3b953c03dcc4276324b9bf95624f1c6e` |
| SHA-1 | `7076ec6b68098b9ace9d8e5f4a6bbfdc66c32e4e` |
| SHA-256 | `e00e5da3e7ce372945a1a863096dcee63ce4d760e028deac8d525838006097db` |

GameFAQs identifies the SKU as Pocket Studios / Universal Interactive, 2003-05-27.
All addresses below are ROM addresses (`file offset + 0x08000000`) unless marked RAM.

## 2. Executive summary

This GBA title has **no password/code-entry screen and no cheat menu**. Its only
developer-intended cheats are **two fixed button sequences** implemented by a pair
of state machines inside the pause/menu input handler at `0x08013880`:

1. **Published, mode 0** — at the in-game pause screen:
   **Down, Right, Down, Right, Left, Left, Up**. Accepted →
   `0x03000478 = 6`, which produces an on-screen **"LEVEL COMPLETE"** and advances
   to the next level. Confirmed in emulator (screenshots `code_7_test.png`,
   `play_next.png`; RAM `ss8`).
2. **Undocumented, mode 1** — during gameplay when RAM byte `0x0300047c != 0`:
   **B, Left, Up, Down** repeated **four** times (16 presses). Accepted →
   `0x03000474 = 1` and `0x03000478 = 3`. Confirmed by savestate RAM diff
   (`0x03000474: 00 00 00 00 → 01 00 00 00`, screenshots `code16_correct.png`,
   `ss5`). This code appears **in no published list**.

A third candidate machine at `0x080121c0` (handlers for B, A, Down, A, Select,
Select, Select) was found but its dispatch table at `0x08013a0`-adjacent bytes is
malformed and the sequence could not be made to fire in any reachable screen;
it is reported as **unconfirmed / probably unreachable**, not as a working code.

All other web-published "codes" for this SKU are GameShark / CodeBreaker / Action
Replay ROM patches (e.g. `32000EC0 00FF`, `ACVT-8N82`), explicitly out of scope.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap (mGBA SDL default): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Hold ~60–70 ms per press (longer double-steps menus).
* Path to the pause screen: main menu → NEW GAME → slot 1 → spam A through the
  intro until gameplay → `Return` → PAUSE.
* Enter `Down Right Down Right Left Left Up` at PAUSE → "LEVEL COMPLETE".
* Savestates: `Shift+F1`–`F9` save, `F1`–`F9` load. A savestate with the mode
  byte `0x0300047c` patched to 1 was built from `ss2` by decompressing the PNG
  `gbAs` chunk, writing `raw[0x19000 + 0x47c] = 1`, recompressing and rebuilding
  the chunk CRC (§16.13). Loading that state, then entering the 16-press code
  **during gameplay** (B exits the pause menu, so it cannot be entered there),
  sets `0x03000474 = 1`.
* The GDB stub (`mgba -g`) is single-client and flaky here (packet errors /
  timeouts); savestate diffing was used for all RAM evidence instead.

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x08016b22` | code | Reads `0x04000130` (KEYINPUT), stores active-high masks |
| `0x03001914` | RAM u32 | Current held keys (active-high) |
| `0x030014f4` | RAM u32 | Previous-frame held keys |
| `0x030014b8` | RAM u32 | Newly-pressed keys = current & ~previous |
| `0x080178cc` | code | Key-history recorder; 12-byte records at `0x03001a00`, field `+6` = newly-pressed mask |
| `0x0801caec` | code | Accessor: returns `history[index].+6` (newly-pressed mask) |
| `0x08013880` | code | Main pause/menu handler; initializes `sl = sp+0x37` from `0x0300047c` (at `0x0801388c`) |
| `0x08013eb2/b4` | code | Gate: if mode byte `!= 0` → 16-state machine; else → 8-state machine |
| `0x08013ec4` | table | 16-entry jump table for the mode-1 machine |
| `0x08013fd4` | table | 8-entry jump table for the mode-0 machine |
| `0x08013fb4` | code | Mode-1 success: `0x03000474 = 1`, `0x03000478 = 3` |
| `0x0801400e` | code | Mode-0 success: `0x03000478 = 6` |
| `0x03000474` | RAM u8 | Mode-1 cheat flag (0 → 1) |
| `0x03000478` | RAM u32 | Menu/game state (pause = 2; level-skip success = 6) |
| `0x0300047c` | RAM u8 | Gate byte selecting which sequence is armed (0 → 7-button, nonzero → 16-button) |
| `0x080121c0` | code | Third, unconfirmed key-state machine (dispatch near `0x080123a0`) |

## 5. Algorithm

Key input is read each frame at `0x08016b22`:

```
held = ~KEYINPUT & 0xFFFF                -> 0x03001914
pressed = held & ~previous               -> 0x030014b8
previous = held                          -> 0x030014f4
```

`0x080178cc` copies `pressed` into a 12-byte-per-entry history ring at
`0x03001a00`; `0x0801caec(i)` returns `history[i].field6` (the newly-pressed
mask). The cheat validators call `0x0801caec(0)` once per state.

**Mode-0 (8-state) machine**, dispatch `0x08013fc2`, table `0x08013fd4`.
Active-high masks: Right `0x10`, Left `0x20`, Up `0x40`, Down `0x80`, A `0x01`.

```
state 0 (0x8013ff4): require (h & ~0x81)==0 and (h & 0x80)!=0   -> Down
state 1 (0x8014016): require (h & ~0x11)==0 and (h & 0x10)!=0   -> Right
state 2 (0x8014034): require (h & ~0x81)==0 and (h & 0x80)!=0   -> Down
state 3 (0x8014052): require (h & ~0x11)==0 and (h & 0x10)!=0   -> Right
state 4 (0x8014070): require (h & ~0x21)==0 and (h & 0x20)!=0   -> Left
state 5 (0x8014098): require (h & ~0x21)==0 and (h & 0x20)!=0   -> Left
state 6 (0x80140c0): require (h & ~0x41)==0 and (h & 0x40)!=0   -> Up -> state 7
state 7: 0x03000478 = 6
Any failed `& ~mask` test resets the state to 0; a wrong key with a clean
subset test leaves the state unchanged (so a later correct key can still
advance, but the overall sequence must still match).
```

**Mode-1 (16-state) machine**, dispatch `0x08013eb4`, table `0x08013ec4`.
Masks: B `0x02`, Left `0x20`, Up `0x40`, Down `0x80`.

```
states  0,4,8,12  (0x8013f04): require (h & ~0x03)==0 and h==0x02  -> B
states  1,5,9,13  (0x8013f4c): require (h & ~0x21)==0 and h==0x20  -> Left
states  2,6,10,14 (0x8013f6c): require (h & ~0x41)==0 and h==0x40  -> Up
states  3,7,11    (0x8013f2a): require (h & ~0x81)==0 and h==0x80  -> Down
state  15         (0x8013f94): require (h & ~0x81)==0 and h==0x80  -> Down
                               then 0x03000474=1, 0x03000478=3
```

So the mode-1 code is exactly `(B, Left, Up, Down) x 4`.

## 6. Tables

| Item | Value |
|---|---|
| Published 7-button code | D, R, D, R, L, L, U (GameFAQs, Cheat Happens) |
| SuperCheats 8-button variant | D, R, D, R, L, L, L, U — **rejected** (see §6b) |
| Novel 16-button code | B, L, U, D, B, L, U, D, B, L, U, D, B, L, U, D |
| Key masks | A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200 |
| Mode-0 state table | `0x08013fd4` (8 pointers) |
| Mode-1 state table | `0x08013ec4` (16 pointers) |
| Success effects | `0x03000478=6` (level complete) / `0x03000474=1` + `0x03000478=3` |

## 6b. Enumeration

**Space definition.** There is no alphabet, no checksum and no variable field:
each cheat is a **single fixed-length sequence of button masks** consumed by a
state machine. The complete space is therefore exactly **two sequences**, one
per value of the gate byte `0x0300047c`:

| Gate `0x0300047c` | Sequence length | Accepted spellings | Effect |
|---|---|---|---|
| `0` (normal pause) | 7 | 1 canonical; the checks also *derive-allow* A (`0x01`) co-pressed on each step | `0x03000478=6` → LEVEL COMPLETE |
| nonzero | 16 | 1 (`B,L,U,D` × 4) | `0x03000474=1`, `0x03000478=3` |

Total representable cheats = **2** (plus mask aliases in gate 0 noted below).
No other action branches exist: the 8-entry and 16-entry jump tables were fully
decoded, and every entry was mapped to a required mask or to a success/reset
path. The only other `0x0801caec` caller cluster outside the pause handler is
at `0x080121fa`–`0x080122e6` (third machine, unconfirmed) and single callers at
`0x08012934`, `0x0803bda`, `0x0803c7a`, `0x08056bc` (menu/dialogue handling).

**Novel code.** `B, Left, Up, Down` × 4 is absent from GameFAQs, Cheat Happens,
SuperCheats, CodeTwink, Almar's Guides, GameHacking.org and Cheat Happens — all
of which publish only the 7-button level skip or cheat-device patches. It was
entered on the real keypad during gameplay with the gate byte patched to 1, and
the ROM's own state machine set `0x03000474: 00 → 01` (savestate `ss5` vs the
patched baseline `ss3`). Screenshots: `code16_correct.png`, `code16_gameplay.png`.
The visible on-screen change is subtle/unconfirmed; the proof is the RAM write,
which is consistent with the success branch at `0x08013fb4`. **Derivation of the
gate byte from a savestate patch is labelled as debugger-assisted**, not a
pure-input unlock.

**Mask aliases (derived, not observed).** In mode 0 the subset tests use
`~0x81`, `~0x11`, `~0x21`, `~0x41`, so A (`0x01`) is tolerated on each press.
An A-modified spelling (e.g. D+A, R+A, …) is therefore *behaviorally equivalent*
to the canonical code. Attempting it at the pause screen with real input failed:
A is consumed by the pause menu (it toggled MUSIC, screenshot `novel_A_variant.png`),
so this alias is a **derived** result, not an in-game observation.

**Bounds proven by rejection.**

| Test | Input | Result | Evidence |
|---|---|---|---|
| Wrong final button | D,R,D,R,L,L,**D** | No LEVEL COMPLETE; `0x03000478` stays `2` (pause), `0x03000474=0` | `reject_bad_final.png`, `ss7` |
| Published 8-button variant | D,R,D,R,L,L,**L**,U | Rejected; `0x03000478 = 2` | `reject_8btn.png`, `ss9` |
| Wrong gate for 16-button code | correct 16 presses with `0x0300047c = 0` | `0x03000474` stays `0` | `ss6` |
| Extra/out-of-alphabet key (B at pause) | B | Closes the pause menu instead of advancing any cheat state | `code16_correct.png` |

These establish both sequence lengths exactly (7 and 16), the final-button
identity, and the gate condition.

**Negative result for a password system (bounded).** All reachable screens were
walked with screenshots: title menu (`s6`), LOAD GAME (`s0`), NEW GAME slots
(`newgame1`), intro/cutscenes, gameplay (`play4`, `play_next`), PAUSE (`pause1`)
with its RESUME / MUSIC / SOUND / QUIT entries and confirm dialog, OPTIONS
(`options_menu2`: MUSIC, SOUND, CONTROL TYPE 1), MULTIPLAYER (`multiplayer_menu3`:
"PLEASE WAIT"). None contains a text-entry field, password prompt, cheat list or
"Special Features" menu. `strings -t x` (104,367 lines) produced only developer
asset names (`w_menu_move`, `w_pistol_fire`, …), BGM/level names (`DESERT_BOSS`,
`FUTRCITY`, …) and localized dialogue at `0x158c48+`; menu labels are rendered
from font tiles, so the string scan alone would not prove absence — the screen
walk and the state-machine enumeration do. Literal searches for the published
sequence in 20+ encodings (u16/u32 LE/BE, byte masks, active-low, button indices,
nibble-packed, strides 2–32, forward and reversed) returned **zero** hits,
consistent with the validator using immediate comparisons rather than a table.

## 7. Validation evidence

* **Observed** — mGBA screenshots of every screen listed in §6b; "LEVEL COMPLETE"
  after the 7-button code; next-level cutscene after advancing; savestate RAM
  diffs showing `0x03000478=6`, `0x03000474=0` (mode 0) and
  `0x03000474=1`, `0x03000478=0` (mode 1, gameplay).
* **Derived** — disassembly of `0x08013880` and both jump tables gives the exact
  masks, lengths, reset/success semantics and the `0x0300047c` gate; the
  A-copress alias and the third machine's handler requirements are derived.
* **Inferred** — the semantic meaning of `0x03000474` (a persistent unlock/debug
  flag); its readers at `0x08004db6` / `0x08004fde` add `0x800` to a display
  parameter but the full downstream effect was not traced. The mode-1 code's
  visible effect was not isolated, so only its RAM write is claimed.

## 8. Unknowns

* What naturally sets `0x0300047c` to nonzero in retail play (a writer at
  `0x080129c0` sets it to 1 on a story/level transition; no complete trigger
  condition was established). The mode-1 code was exercised with a patched
  savestate.
* Whether the third machine at `0x080121c0` is live in any context (its dispatch
  table bytes at `0x080123a0+` are inconsistent with a 12-entry pointer table).
* Precise gameplay meaning of the `0x03000474` flag and of `0x03000478=3`.

## 9. Tooling

`strings`, `grep`, Python (`struct`, `capstone`, `zlib`, `binascii`) for header
parsing, BL/literal scans, savestate patching and RAM reads; `xdotool` +
`scrot` for input and screenshots; `arm-none-eabi-objdump -M force-thumb` for
disassembly; mGBA 0.10.5 with Xvfb `:317` and `openbox`. No ROM or copyrighted
assets are redistributed; screenshots were kept only in `/tmp/hulk`.
