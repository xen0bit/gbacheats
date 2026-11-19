# Planet of the Apes (GBA) — Reverse Engineering Report

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
| Complement byte | 0x3D (expected 0x56) — **edited/rebuilt header artifact**, cf. guide §16.1 |
| Header checksum | 0x0000 (typical rebuilt-header artifact) |
| MD5 | `23a5cf12dda1bd5ef4d3e03fa6112c19` |
| SHA-1 | `574a047ab79431e05e716db2688a3a012a6bc85d` |
| SHA-256 | `276aa09dcef2db458fcd8e01c52d1b51ef71621da62d7fcf9a9ccae2c1e39d99` |

**Embedded-header scan (Phase 0):** the 156-byte Nintendo logo was found exactly once, at
file offset `0x4` (header base `0x0`). There is no second game image, no boot selector, no
appended trainer/cracktro, and no patch stub. The code at `0x08000000` is the stock ARM crt0.

**Development/publishing note:** the shipped legal screen names *Ubi Soft*, *Twentieth Century
Fox Film Corporation* and *Visiware S.A.*; the audio engine banner at `0x24891B` reads
`Shin'en Multimedia. Code: B.Wodok`. That banner is an audio-engine string (guide §11),
**not** a cheat/code literal. Web sources variously credit Torus Games and Visiware; the ROM
itself credits Visiware.

## 2. Executive summary

This GBA title has **two developer-intended cheat surfaces**, both discovered and
characterised from the ROM itself:

1. **A 6-symbol level-password system** entered on a dedicated Password screen reached from
   the main menu (padlock icon). The on-screen wheel alphabet is exactly
   `BCDFGHJKLMNPQRSTUVWXYZ0123456789#` — 33 selectable characters plus a backspace arrow,
   with **no A, E, I or O**. Twelve published level passwords (levels 2–13) exist; a sample
   was verified in-game. The codes are **algorithmic** (no literal table exists in the ROM in
   ASCII, index-byte or 5-bit-packed form).

2. **A title-screen button code** B, A, Left, Down, Up, Right (then Start), which sets a
   flag and unlocks a cheat menu with level select / infinite health / all weapons. The
   exact key-mask sequence is present as a byte table in the ROM and the validator was
   fully disassembled. **Bounds of the dynamic verification are stated explicitly in §8.**

Published literals from GameFAQs, Cheat Happens, GameRevolution and Cheat Code Central were
collected and checked against the ROM. GameFAQs/GameRevolution/CheatCC truncate the Level 11
password to `3`; Cheat Happens gives the complete `3#9QLS`. No promotional code was found to be
a verbatim ROM string.

All ROM-address statements below are for the exact hash in §1.

## 3. How to reproduce

**Emulator/harness:** mGBA (SDL), `/usr/local/bin/mgba`, under `Xvfb :319` with `SDL_AUDIODRIVER=dummy`,
openbox as window manager. GBA→key map verified by reading held-key state at `0x030045D4`:
`A=x (0x001)`, `B=z (0x002)`, `L=a (0x200)`, `R=s (0x100)`, `Start=Return (0x008)`,
D-pad=arrow keys (Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`).
**Short key holds (~0.03–0.06 s) are mandatory**: a 0.12 s hold double-steps menus via key repeat.

**Boot path:** boot → legal screen (press A) → language grid (select **English**) →
title "PRESS START" → Start → main menu.

**Screen enumeration (all observed on :319):**

| Screen | Evidence | Notes |
|---|---|---|
| Legal / © screen | screenshot `screen.png`, `f_lang.png` | Ubi Soft / Fox / Visiware text |
| Language select | `screen2.png`, `f_title.png` | 6 flags: English, Nederlands, Français, Español, Italiano, Deutsch |
| Title "PRESS START" | `screen3.png`, `cc_title4.png` | silhouette art |
| Main menu | `mainmenu1.png` | 4 rotating **icons** (no text): GameBoy=Play/New Game, cyan robot=Continue, padlock=Password, music note=Sound |
| Password entry | `password1.png`, `pw_zoom.png`, `wheel_montage.png` | 34-slot circular character wheel; selected char green at top; A appends; arrows rotate |
| 6-char entry complete | `entered.png`, `entered_zoom.png` | wheel replaced by 6 glyphs in centre |
| Pause (in game) | `pause.png`, `pause2.png`, `pause3.png` | 3 rotating icons: skull=Quit, GameBoy=Play, note=Sound; skull → "QUIT?" checkmark/X confirmation |
| Gameplay | `screen11.png`, `quit.png` | Level 1 HUD (life bar + ammo bar) |
| Story cutscenes | `screen8.png`–`screen11.png`, `after_submit.png` | still images + dialogue boxes, advanced with A |

**Passwords tested in-game** (entered on the Password wheel):

* `64N4HY` (published Level 2) → **ACCEPTED**: screen transitioned into the level/story
  sequence (`after_submit.png`).
* `BBBBBB` (no published code) → **REJECTED**: game returned silently to the main-menu icon
  screen (`invalid_test.png`). This is the proof-of-bounds for the on-screen code entry.

**Button code tested:** published sequence B,A,Left,Down,Up,Right was entered on the title
screen, on the legal screen, at boot, and on the main-menu screen; with the 10 s window
expired the flag at `0x03004514` read back 0. See §8 for the exact status.

## 4. Address map

All addresses are GBA bus addresses; file offset = address − `0x08000000`.

### Password system

| Item | Address (ROM) | File offset | Evidence |
|---|---|---|---|
| Password screen name string `PASSWORDNODE` | `0x08017908` | `0x17908` | strings |
| Main-menu/pause node names | `0x080178F8`–`0x08017924` | `0x178F8`–`0x17924` | strings: `PAUSEMENUNODE`, `PASSWORDNODE`, `MAPMENUNODE`, `MAINMENUNODE` |
| `CHEATOPTS` resource name (x2 manifest copies) | `0x08017614`, `0x080284B2` | `0x17614`, `0x284B2` | strings |
| Resource record referencing `PASSWORDNODE` (id `0x3D`) | `0x08024FE30`-region | `0x24FE30` region | pointer scan |
| Font ASCII→tile maps (3 copies) | `0x08205040`, `0x082090E0`, `0x0820D170` | `0x205040`, `0x2090E0`, `0x20D170` | byte dumps |
| Audio engine banner (false positive) | `0x0824891B` | `0x24891B` | strings |

### Button code / cheat menu

| Item | Address | Notes |
|---|---|---|
| **Key-mask table** (6 presses, one byte each) | **ROM `0x0801CA58`** = file `0x1CA58` | bytes `02 01 20 80 40 10` = B, A, Left, Down, Up, Right. Followed by a second 6-byte block `10 11 12 13 14 15` at `0x0801CA5E` and byte `0A` at `0x0801CA64` |
| Literal pointer to table | `0x0800A454` | `ldr r0,[pc,#64]` in validator |
| Literal pointer to table+6 | `0x0800A434` | loaded in root state machine |
| **Button-code validator** | **ROM `0x0800A3A0`** (Thumb) | 600-frame polling loop; called from root state-machine state 2 at `0x080065E6` |
| Progress index (byte) | IWRAM `0x03002BD0` | reset on validator entry; increments per matching press; reset to 0 on any non-matching press |
| Cheat-flag word | IWRAM `0x03004514` | set to `-1` (0xFFFFFFFF) when index reaches 6 |
| Companion flag word | IWRAM `0x030045CC` | set to `-1` by root state machine at `0x080065FC` |
| Pressed-key mask (active-high) | IWRAM `0x030045D0` | written by `0x0800A610` (reads `0x04000130`, XOR `0x03FF`, `& ~previous`) |
| Held-key mask (active-high) | IWRAM `0x030045D4` | same routine |
| Root state machine / main handler | ROM `0x080064D8` (Thumb) | referenced as Thumb pointer `0x080064D9` at `0x080001C8` (crt0 literal pool) |
| Cheat-menu handler | ROM `0x08006ACC` | called at `0x08006856` when `0x03004514 != 0`; on the zero path the state machine selects 9 instead |
| Key-read function | ROM `0x0800A610` (Thumb) | KEYINPUT literal `0x04000130` at `0x0800A630`; called from `0x080061AE`, `0x080061FA` |

### Savestate RAM layout used for proofs

mGBA `.ss1` = PNG with zlib `gbAs` chunk; for this 4 MiB ROM the decompressed state is
397,312 bytes; IWRAM begins at raw `0x19000` (so IWRAM `0x03004514` is raw `0x1D514`).
This layout was validated by reading back the live held-key word (`z`→`0x0002`,
`x`→`0x0001`, arrows→`0x10/0x20/0x40/0x80`, Return→`0x0008`).

## 5. Algorithm

### 5.1 Button-code validator (fully recovered, Thumb)

Function `0x0800A3A0` (called with `r0 = 12` from state 2 of the root state machine):

```
r7 = (u16)r0                       ; default return state = 12
[0x03002BD0] = 0                   ; reset press-progress index
[0x03004520] = 0
[0x03004510] = table_at_0x0801CA5E[ [0x03004548] ]   ; secondary table lookup
r3 = [0x03004510]; r2 = 6; call 0x0800D8A4
r6 = 600                           ; 150 << 2  — 600 frames (~10 s at 60 Hz)
loop:
    wait_one_vblank()               ; BL 0x0800A548, parameter 1
    pressed = (u16)[0x030045D0]     ; active-high newly-pressed keys
    idx = (u8)[0x03002BD0]
    expected = (u8)[0x0801CA58 + idx]
    m = expected & pressed
    if m == 0:
        if pressed == 0: goto keep  ; no key this frame → keep progress
        [0x03002BD0] = 0            ; wrong key → reset progress to zero
        goto keep
    [0x03002BD0] = idx + 1          ; correct key → advance
keep:
    if idx == 6: [0x03004514] = 0xFFFFFFFF   ; full sequence → enable cheat flag
    if pressed & 0x0008: r7 = 3; break        ; Start → return state 3
    if --r6 != 0: goto loop
return r7
```

Properties derived from the disassembly:

* Matching is `expected & pressed != 0`, i.e. a press that **contains** the expected bit also
  advances the index (active-high, edge-triggered semantics).
* Any pressed key that does not contain the expected bit resets the index to 0.
* The check is **per press**, with a 600-frame (~10 s) window that begins when the validator
  function is entered. Guide §16.12 applies: the flag can expire if Start is pressed late.
* Completion writes `0xFFFFFFFF` to `0x03004514`; the root state machine tests this word at
  `0x0800684E` and, on nonzero, calls the cheat-menu handler `0x08006ACC` (otherwise it
  selects state 9).

### 5.2 Password system (partial — validator not isolated)

* Input alphabet: 33 characters, 6 positions → nominal space `33^6 = 1,291,467,969`.
* Wheel order (clockwise, derived by stepping all 34 positions and OCR/reading the green
  glyph at top): `B C D F G H J K L M N P Q R S T U V W X Y Z 0 1 2 3 4 5 6 7 8 9 # ←`.
  A, E, I and O are absent; `←` is backspace, not a code symbol.
* Entered characters are drawn as 6 large glyphs once the sixth symbol is appended; Start
  then validates. A valid code transitions to the story/level; an invalid one returns to the
  main menu with no message.
* The 12 published codes are **not stored verbatim** in the ROM: searches for ASCII strings,
  for the alphabet-index byte sequences, and for 5-bit-packed 30-bit values all returned
  zero hits. This proves an algorithmic generator/checker rather than a flat lookup list.
* Repeated attempts to isolate the password validator (key-state read watchpoints at
  `0x030045D0`/`0x030045D4`, savestate RAM diffs of the live input buffer, Capstone scans for
  `cmp #33`/`cmp #6` patterns, and pointer scans to font tables) did not produce a single
  accepted/rejected oracle function; those attempts are reported under §8 rather than
  presented as a solved algorithm.

## 6. Tables

### 6.1 Level passwords (published; all verified to be composed solely of the ROM's 33-symbol alphabet)

| Level | Password | Notes |
|---:|---|---|
| 1 | *(no password published)* | default start level |
| 2 | `64N4HY` | **accepted in emulator** (`after_submit.png`) |
| 3 | `F5BMGF` | published literal; not in ROM as ASCII |
| 4 | `B1SKZR` | ditto |
| 5 | `76FNHB` | ditto |
| 6 | `P7GRXK` | ditto |
| 7 | `6B7VM#` | ditto |
| 8 | `QK6293` | ditto |
| 9 | `JDDUTJ` | ditto |
| 10 | `046PJ#` | ditto |
| 11 | `3#9QLS` | GameFAQs/GameRevolution/CheatCC truncate this to `3`; Cheat Happens gives the full 6-character code |
| 12 | `C12KYY` | published literal |
| 13 | `CBCYPH` | published literal |

Sources: GameFAQs GBA cheats, Cheat Happens GBA page, GameRevolution GBA cheats,
Cheat Code Central GBA page, VGChartz GBA cheats index. CodeBreaker/Action Replay entries
also found on ROMSFUN/libretro are **out of scope** and were not used.

### 6.2 Button code

| Published effect | Sequence | ROM table bytes (0x0801CA58) | Rendered masks |
|---|---|---|---|
| Cheat menu (stage select, infinite health, all weapons) | B, A, Left, Down, Up, Right (then Start) | `02 01 20 80 40 10` | `0x002,0x001,0x020,0x080,0x040,0x010` |

### 6.3 Relevant strings

`PASSWORDNODE`, `MAINMENUNODE`, `MAPMENUNODE`, `PAUSMENUNODE`, `PAUSEMENUNODE`,
`CHEATOPTS` (x2), `Press Start`, `Password`, `New Game`, `Continue`, `Credits`, `Sound`,
`Return`, `Quit`, `Tally`, `Game Over`, `Congratulations` — all localized into English,
French, Italian, German, Spanish and Dutch near file offsets `0x17C34`–`0x18040`.
The UI menu itself is icon-based; these strings are the resource/localization bank.

## 6b. Enumeration

**Password entry surface.** Wheel cycle length = 34 (33 characters + backspace), code
length fixed at 6 → 33⁶ ≈ 1.29×10⁹ nominal symbol strings. The set of symbols reachable
through the UI was enumerated exhaustively by stepping the wheel through every slot
(`wheel_montage.png`); there is no hidden 34th character. Both acceptance outcomes were
proven on the real screen: `64N4HY` accepted, `BBBBBB` rejected (§3). The published
`3` for Level 11 is a truncated transcription: a one-character code cannot satisfy the
six-symbol input, so the corrected `3#9QLS` is the operative entry.

**Button-code surface.** The key-mask table at `0x0801CA58` holds six one-byte masks; the
validator compares exactly six presses (`cmp r0,#6` at `0x0800A462`), so the documented
sequence is the entire table-driven sequence. The adjacent six bytes at `0x0801CA5E`
(`10 11 12 13 14 15`) are a secondary lookup table indexed by the RAM byte `0x03004548`,
also consumed by the root state machine; they are **not** a second button sequence in the
validator. No additional key-mask sequence was found by scanning the ROM for the published
6-press pattern in active-high u8/u16, active-low u16, and reversed (newest-first) forms —
only the single u8 hit at `0x1CA58`.

**Novel codes.** No unpublished code was generated. This is a material gap against guide
§0.2: the password validator/checksum was not isolated (§5.2), so an offline encoder could
not be written, and no alphabet-valid generated value was accepted in the emulator. The
button code is fully decoded statically, but the in-game trigger was not reproduced (§8).

## 7. Validation evidence

* **Observed (emulator/screenshot):** every screen in §3; `64N4HY` → story sequence;
  `BBBBBB` → main-menu rejection; wheel glyph order (34-step montage); keymap via
  `0x030045D4` reads from patched/decompressed savestates.
* **Observed (ROM bytes):** single Nintendo logo/header; all strings and literal pointers in
  §4; button mask table `02 01 20 80 40 10`; absence of published password literals in ASCII,
  index and 5-bit packings.
* **Derived (disassembly):** button validator algorithm §5.1, including progress index,
  600-frame window, reset-on-wrong-key, flag write and cheat-menu call; font tables;
  key-read routine and key-state addresses.
* **Inferred:** the six glyphs shown after entry are the accepted password echoed in the
  game's stylized password font (visual only; the glyph→character mapping was not decoded).
  Mapping of main-menu icons to New Game / Continue / Password / Sound is inferred from the
  resource names and observed transitions.

## 8. Unknowns / limits (explicit, not "not tested")

1. **Password validator not isolated.** Key-state watchpoints (`0x030045D0`, `0x030045D4`)
   landed in generic UI handlers (`0x08001C88`, `0x080099EC`, `0x08001CCC`), not in a
   password-specific routine. RAM diffs around entry were dominated by animation/audio
   state. No offline encoder, no novel code, no rejection test of a checksum-valid but
   out-of-range value could therefore be produced. This is the main incomplete item.
2. **Button code not triggered dynamically in this harness.** The exact mask table and the
   complete validator were found and decoded, but repeated attempts to make the flag at
   `0x03004514` go to `0xFFFFFFFF` via xdotool input read back `0x00000000`. The most likely
   cause is the 10-second (600-frame) window in §5.1 expiring during the long, animation-gated
   intro before the title screen is reachable; a secondary harness constraint is that mGBA's
   GDB stub port 2345 was occupied by another process in this shared environment, so debugger
   sessions attached to the wrong emulator. The `-d` CLI debugger breakpoint at
   `0x0800A3A0` never hit during boot/intro/title within the intervals sampled. **The code is
   therefore ROM-verified but not click-verified.** A patch of the cheat flag into a
   savestate was attempted but mGBA rejected the reconstructed PNG (fresh boot), so the
   cheat menu screen itself was not walked.
3. **Secondary table at `0x0801CA5E`** (`10 11 12 13 14 15`) is consumed via
   `[0x03004548]`; its semantics were not resolved. No claim is made that it is a code.
4. **Font/tile-indexed text bank** for the password glyphs was not decoded; the negative
   claim that the codes are algorithmic rests on literal searches (ASCII, index bytes,
   5-bit packing) plus the in-game accept/reject, not on reading an algorithm.
5. **Credits and Sound menu items** are present as localized strings and icons (music note
   in the main menu and pause menu), but their detail screens were not exhaustively captured
   in this run.

## 9. Tooling

* `xxd`, `strings -t x`, `grep -abo`, `python3` (struct/zlib), `capstone`/`keystone`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all
  disassembly; literal words re-read with `struct.unpack_from("<I", …)` (guide §11).
* mGBA SDL on `Xvfb :319`; `xdotool` XTEST key events; `scrot`/ImageMagick for screenshots;
  `tesseract` for screen detection; ImageMagick `montage` for the wheel enumeration.
* mGBA `.ss1` savestates parsed as PNG + zlib `gbAs` chunk for IWRAM/EWRAM reads (guide §16.13).
* mGBA `-d` command-line debugger (pty) used after the GDB stub proved unusable on the
  contended port; `binutils-arm-none-eabi`, `capstone`, `keystone-engine` were already present.

No ROM image or copyrighted asset is reproduced in this report; only hashes, addresses,
algorithms and the analyst's own observations are published.

---

### Reproduction quick recipe

1. `Xvfb :319 -screen 0 1024x768x24 & DISPLAY=:319 openbox &`
2. `DISPLAY=:319 SDL_AUDIODRIVER=dummy mgba -3 "Planet of the Apes.gba"`
3. Skip legal screens with short A taps; select **English**; Start → main menu.
4. Rotate the icon carousel to the **padlock** (one Right from the initial GameBoy icon), press A.
5. On the wheel, rotate with Left/Right (short holds) and press A to append each symbol;
   type `64N4HY` → Start → accepted; type `BBBBBB` → Start → returns to main menu.
6. Button code (static-verified): masks at ROM `0x0801CA58`, flag `0x03004514`,
   cheat-menu handler `0x08006ACC`.
