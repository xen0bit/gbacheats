# Nicktoons Racing (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Nicktoons Racing.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `NICKTOONSRAC` |
| Game code | `ANQE` |
| Maker code | `70` |
| Version | `0x00` (Rev.00) |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock) |
| Complement byte | `0x37`; header checksum `0x0000` (rebuilt-header artifact; sum of 0xA0..0xBD = 0xE7) |
| MD5 | `cc25621658169b41ada436ef99c078e8` |
| SHA-1 | `ad53fdc15c3e68a4ada8f4d902bfd579c6313025` |
| SHA-256 | `7dc93a355519b8bf027872604359dbc6f9f1e74e0e8ef676d8392de34932a88a` |

Single retail image. The 156-byte Nintendo logo occurs exactly once (file 0x4), so there is
no multi-game pack, appended trainer, or cracktro; the entry word is the stock ARM branch.

## 2. Executive summary

The GBA build has **one developer-intended cheat**: a button code entered on the **Main Menu**.
There is **no password entry screen**, no on-screen keyboard, and no hidden debug menu in this
SKU. The published code (3rd party cheat indexes) is real and was verified bit-for-bit in the
ROM:

> **Hold R, then press Start → Select → L → Select → Start** on the Main Menu.

The gzip-free plaintext table at `0x08049030` stores exactly five `u32` button masks
(`0x08, 0x04, 0x200, 0x04, 0x08`) followed by a zero terminator. The validator at
`0x08007488` requires R held in the current held-button word and an edge-triggered press
containing the expected mask within a 20-frame window. On completion it sets five unlock
bits (`0x1F`) in the save/work byte at EWRAM `0x0201DF5B` (or a word at `0x03007088` in the
link-mode path), which is the "all cheats" state: extra characters, tracks, cups and
difficulties. RAM proof: `0x00 → 0x1F`, reproduced repeatedly.

The widely published `XBG-7LB555DB…` / `CDBD6BB555GB…` passwords belong to the **Game Boy
Color** release and are absent from this GBA ROM in every encoding tested. The "Left Right
Left Right Up Down" codes belong to the PlayStation build; CodeBreaker/Action Replay codes
are memory edits and are out of scope.

## 3. How to reproduce

1. Toolchain: mGBA SDL, `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, `xdotool` XTEST events.
2. Key map verified against held-button RAM (masks are active-high ORed with `0xFC00`):
   `x`=A(0x001), `z`=B(0x002), `BackSpace`=Select(0x004), `Return`=Start(0x008),
   `Right`=0x010, `Left`=0x020, `Up`=0x040, `Down`=0x080, `s`=R(0x100), `a`=L(0x200).
3. Boot the ROM. From cold start it takes five Start presses (Infogrames logo → attract →
   Crawfish logo → title → Main Menu); intro length varies, so confirm visually.
   A verified Main-Menu savestate is the reproducible starting point.
4. Enter the code with ~0.12 s holds and ~0.12 s gaps: hold `s` (R), then tap
   `Return`, `BackSpace`, `a`, `BackSpace`, `Return`; release `s`.
5. RAM proof: save a savestate before and after; decompress the PNG `gbAs` chunk and read
   EWRAM offset `0x1DF5B` (state offset `0x3EF5B`). It changes `0x00 → 0x1F`.
6. The unlock byte is the ground truth; the menus reached after the code (Select Character,
   Select Cup, Select Difficulty, race HUD, pause) are listed in §7. A visible
   before/after differential for a specific menu row was **not** isolated, because the
   Select Difficulty screen also appears without the code; the RAM bit change is the proof.
7. Negative control: replace the third press `a` (L) with `z` (B); the byte stays `0x00`.

## 4. Address map

| Item | Address (ROM / RAM) | Evidence |
|---|---|---|
| ROM header | `0x08000000` | observed bytes |
| Text bank (ASCII) | `0x08048BE8`–`0x080496xx` | `strings -t x`; all menus and track names are plaintext |
| Button-code table | `0x08049030` (file `0x49030`) | literal pointer at `0x08007504` |
| Validator / handler | `0x08007408`, check at `0x08007488` | BL from `0x0800737A`; breakpoint hit live |
| Progress counter | IWRAM `0x03007594` | literal at `0x080074FC`; reset when timer expires |
| Inter-key timer | IWRAM `0x03007588` | literal at `0x080074F8`; set to 20 (frames) on each match |
| Input struct | IWRAM `0x03005AF0` | held u16 at `+4`, pressed u16 at `+12`, player index at `+0x20` |
| Unlock work byte | EWRAM `0x0201DF5B` | `0x08005824`/`E0`/`0x08005990` OR bits into `[0x0201DF50+11]` |
| Unlock word (link mode) | IWRAM `0x03007088` | alternate path in the same helpers |
| Legitimate unlock callers | `0x0800D4AC`, `0x0800D524`, `0x0800D54E` | BL xref scan |

File offset ↔ ROM address: `addr = 0x08000000 + file_offset`. In mGBA `.ss1` states,
EWRAM `0x02000000` maps to state `0x21000` and IWRAM `0x03000000` to `0x19000`.

## 5. Algorithm

Pseudocode of `0x08007488` (derived from Thumb disassembly, verified by breakpoint):

```
held    = *(u16*)(0x03005AF0 + 4 + 2*player)     // 0xFC00 | active-high mask
pressed = *(u16*)(0x03005AF0 + 12 + 2*player)    // edge-triggered this frame
if (held & 0x100) == 0: return                   // R must be held
if (*(u32*)0x03007588 != 0): decrement it; if it hits 0 -> progress = 0
expected = *(u32*)(0x08049030 + 4*progress)
if (pressed & expected) == 0: return             // AND, not equality
progress++
if *(u32*)(0x08049030 + 4*progress) == 0:
    unlock(0x1|0x2|0x4|0x8|0x10); return
*(u32*)0x03007588 = 20                           // 20-frame inter-key window
```

Unlock helpers (all OR bits; never clear):
`0x08005824(1)`→bit0, `0x08005824(2)`→bit1, `0x080058E0(1)`→bit2,
`0x080058E0(2)`→bit3, `0x08005990`→bit4 of `0x0201DF5B`.

## 6. Tables

Button masks (active-high, GBA KEYINPUT inverted):

| Button | Mask |
|---|---|
| A | 0x001 |
| B | 0x002 |
| Select | 0x004 |
| Start | 0x008 |
| Right / Left / Up / Down | 0x010 / 0x020 / 0x040 / 0x080 |
| R / L | 0x100 / 0x200 |

Code table at `0x08049030`: `08 00 00 00 | 04 00 00 00 | 00 02 00 00 |
04 00 00 00 | 08 00 00 00 | 00 00 00 00` = Start, Select, L, Select, Start, END.

Unlock byte bits: `0x1F` (bits 0–4) = "all cheats" as advertised.

## 6b. Enumeration

**Space.** The accepted input language is exactly one five-press sequence with R held,
under a 20-frame inter-key window. The table contains five entries plus a terminator; its
pointer is unique (`0x08007504` is the only `u32` reference to `0x08049030` in the 4 MiB
image). A scan of all 4-byte-aligned `u32` runs returned 333 accidental graphics matches;
`0x08049030` is the only one with five *distinct* valid button masks referenced by code.

**Published code (verified):** hold R + Start, Select, L, Select, Start → `0x00 → 0x1F`.

**Novel accepted inputs (not in any published list)** — each reproduced from the fixed
Main-Menu savestate, with unlock-byte readings:

| Variant | Result |
|---|---|
| Hold R + **Left** (extra held modifier) during the standard sequence | `0x1F` accepted |
| Each press delivered **together with A** (`pressed = expected \| 0x001`) | `0x1F` accepted |
| **R+Start simultaneously** on the first step, then Select, L, Select, Start | `0x1F` accepted |
| Extra **Down** press before the sequence, then the standard sequence | `0x1F` accepted |

These are possible because the matcher tests `held & 0x100` and `pressed & expected` with
bitwise AND, so extra held bits and extra simultaneously-pressed bits are ignored.

**Bounds proven by rejection:**

| Rejected input | Result | Why |
|---|---|---|
| Third press B (`0x002`) instead of L (`0x200`) | `0x00` | wrong mask, `pressed & 0x200 == 0` |
| R held but only four presses | `0x00` | terminator not reached |
| Standard sequence with 0.30 s holds/gaps | `0x00` | exceeds the 20-frame inter-key window |
| Entering the sequence on the **title** screen or Select Race screen | `0x00` | code is only driven from the Main-Menu loop path |
| GBC password literals `XBG-7LB555DB` etc. | absent | not in ROM as ASCII, case-shifted, `+0x20`, or dashless |

## 7. Validation evidence

* **Observed** — emulator screens for title, Main Menu, Select Race, Select Character,
  Select Cup, Select Difficulty, Options (5 items), Hall of Fame, in-race HUD (lap, timer,
  position, minimap), and PAUSE menu (CONTINUE / TRY AGAIN / QUIT); savestate bytes showing
  `0x00 → 0x1F` at `0x0201DF5B`; rejected variants staying `0x00`.
* **Derived** — Thumb disassembly of `0x08007408`–`0x080075A0` and helpers
  `0x08005824`/`0x080058E0`/`0x08005990`; literal tables at `0x08049030`; BL xrefs.
* **Inferred** — the semantic labels "all tracks / all cups / all difficulties / secret
  character" come from the published description plus the five OR bits; each individual
  bit-to-menu mapping was not isolated. No per-row visual unlock differential was proven.

## 8. Unknowns

* Which of the five unlock bits maps to which specific unlockable (all five are set together
  by this code). Bit-level attribution would require isolating each bit with a debugger.
* Whether the link-mode word at `0x03007088` produces a different visible unlock set.
* The game has no hidden debug screen reachable from any menu walked; no debug strings exist
  in the ASCII bank. This is a bounded negative for the screen/string space searched, not a
  claim about code paths that could be reached only by hardware/link-cable events.

## 9. Tooling

`strings -t x`, `xxd`, `grep`, `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7,
Python 3 (struct/zlib/PIL), mGBA SDL under `Xvfb :315` with `SDL_AUDIODRIVER=dummy`,
`xdotool` XTEST, `scrot`/ImageMagick. Helper scripts in `/tmp/nicktoons/`:
`ss.py` (gbAs savestate decoder), `keymap.sh`, `brute.sh`, `novel3.sh`, `walk.sh`,
`gdbrsp.py`. Note: mGBA's GDB stub returned zeros for RAM reads on this build, so savestate
diffing was used as the RAM oracle. No ROM or copyrighted asset is redistributed here.
