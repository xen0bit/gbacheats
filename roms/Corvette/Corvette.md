# Corvette (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Corvette/Corvette.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `CORVETTE` (0xA0, NUL padded) |
| Game code | `AVCE` (0xAC) |
| Maker | `6S` (0xB0) |
| Fixed byte 0xB2 | `0x96` |
| Version | `0x00` (0xBC) |
| Complement | `0x3D` (0xBD) — matches the computed value over 0xA0–0xBC |
| Header checksum | `0x0000` (0xBE) |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| MD5 | `5e5295484bb4cff6c487ae06fa4c4c69` |
| SHA-1 | `676145da9d6824f0beb7dc4a58062c3bc8ae266a` |
| SHA-256 | `f3c17d66817715980144341653c5adf1d7ef868db6b06dbb20c916cd5b2356bb` |

**Patch/trainer check.** The 60-byte Nintendo logo occurs exactly once in the
file (offset `0x4`), so this is a single GBA image, not a multi-game pack. The
entry word is the stock `b 0x080000C0`, the complement byte is consistent, and
the first 4 KiB entropies are 5.4–6.4 bits/byte (normal ARM code + graphics).
No cracktro branch, no appended trainer, no second header. The observed
`.sav` is 512 bytes (SRAM).

## 2. Executive summary

Corvette GBA has **no password system**. It has a single, developer-intended
**button-code screen on the title screen**, gated on `L+R` being held, and it
implements exactly **two** sequences of **eight D-pad presses**. Both were
located in ROM, both are published on 3rd party cheat indexes, and both were
re-entered and verified in RAM in mGBA.

* **Mini Cars mode** — hold `L+R`, press
  `Up, Right, Down, Left, Right, Left, Right, Left`.
  Action writes `1` to `0x03000187`.
* **Unlock all events/cars** — hold `L+R`, press
  `Up, Left, Down, Right, Left, Right, Left, Right`.
  Action writes `0x000FFFFF` to `0x020001E8` and `0x08` to `0x020001EC`.

The validator is a pair of independent 8-entry dispatch tables inside one
function at `0x0800D90C`. Every press is compared against the expected button
for the current index; a wrong press resets that index to zero, and releasing
`L+R` resets both indices. Exhaustively simulating all `4^8 = 65,536`
direction sequences against the recovered model yields **exactly two**
accepted sequences, the two published ones, with no overlap.

No third accepted sequence exists, so the report's novel deliverable is:

* a **16-press combined sequence** (mini-code then unlock-code in one title
  visit) that appears in no published list, verified in RAM with all three
  flag values set simultaneously, and
* an undocumented **`A+B+Select+Start`** front-end reset gate
  (`0x08003308` → `0x08003068`), observed to return the game to the language
  select screen.

Published name-entry password `XOPENSEZ` is **not present in this ROM under any
encoding** (ASCII, lowercase, UTF-16LE/BE, reversed, 5-bit packing). The name
field is a label, not a validator (see §8).

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL under `Xvfb :263` with `SDL_AUDIODRIVER=dummy`.
Default mGBA SDL keys used: `x`=A, `z`=B, `a`=L, `s`=R, `Return`=Start,
`BackSpace`=Select, arrow keys = D-pad.

Boot path and exact menu path:

1. Boot. The first screen is **SELECT LANGUAGE**; the ASCII language list is
   drawn from `0x0802EF38` (`ENGLISH`, `FRANçAIS`, `DEUTSCH`, `ITALIANO`,
   `ESPAÑOL`).
2. Press **A** on `ENGLISH`. The title screen appears and draws
   **PRESS START** (text ID `0x2712`, drawn by `0x0800D90C`).
3. At the title screen, hold **L+R** (`a`+`s`) and tap the eight directions.
4. Read flags while paused (see §4). B/Select at the title returns to the
   language screen; Start leaves the title for the 3-D front-end screen.

Automation used: `mgba -3 -d`, a pty-backed controller, breakpoint at the
joypad reader `0x0800A340` (one `continue` per frame), and the ROM text routine
`0x0800CBFC` for screen-text capture. Key presses were sent with XTEST to the
focused mGBA frame window (`xdotool windowactivate`).

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` | ARM code | stock crt0 entry |
| `0x0800A340` | Thumb fn | joypad reader: `KEYINPUT` → held/pressed |
| `0x03000190` | RAM u16 | **held** buttons, active-high, low 10 bits (`~KEYINPUT`) |
| `0x03000194` | RAM u16 | **pressed** edge = held & ~previous-held |
| `0x0800D90C` | Thumb fn | title-screen per-frame handler: draws PRESS START, DMA of 0x200 bytes, and both cheat dispatchers |
| `0x0800D950` | Thumb | `L+R` gate: `(held & 0x300) == 0x300` |
| `0x0800D96E` | code | dispatcher #1 setup |
| `0x03006524` | RAM u8 | dispatcher #1 progress index (0–7) |
| `0x0800D9AC` | ROM ptr table | dispatcher #1: 8 Thumb handlers `D9CC D9D8 D9E4 D9F0 D9FC DA08 DA14 DA20` |
| `0x0800DA20` | Thumb | mini-cars action: `0x03000187 = 1`, resets index |
| `0x0800DA4E` | code | dispatcher #2 setup |
| `0x03007110` | RAM u8 | dispatcher #2 progress index (0–7) |
| `0x0800DA74` | ROM ptr table | dispatcher #2: 8 Thumb handlers `DA94 DA9C DAA4 DAAC DA9C DAAC DAB4 DAC8` |
| `0x0800DAC8` | Thumb | unlock action: `0x020001EC = 8`, `0x020001E8 = 0x000FFFFF` |
| `0x0800DB14` | Thumb | `L+R` released: both indices := 0 |
| `0x0800DB20` | Thumb | end of handler: clears bit 0 (A) of `0x03000194` |
| `0x03000187` | RAM u8 | **mini-cars flag**, read at `0x0800465C` to pick the car graphics table |
| `0x020001E8` | RAM u32 | **unlock bitfield**: bits 0–19 = events/cars unlocked (`0x000FFFFF` = all) |
| `0x020001EC` | RAM u8 | unlock byte written as `8` by the cheat |
| `0x08018148` | Thumb fn | `get_bit(n)` from `0x020001E8` |
| `0x08018168` | Thumb fn | `set_bit(n)` in byte `0x020001ED` |
| `0x08018194` | Thumb fn | OR a bit into `0x020001E8` |
| `0x0800CBFC` | Thumb fn | ASCII text blitter (font at `[[0x03006528]]+0x80`) |
| `0x0800C660` | Thumb fn | text-ID → string for current language |
| `0x08003308` | Thumb fn | front-end frame handler with `A+B+Select+Start` gate |
| `0x08003068` | Thumb fn | front-end re-initialisation called by that gate |

Text/bank anchors: `TO UNLOCK MINI CARS MODE` `0x080812D3`,
`ON THE TITLE SCREEN` `0x08081354`, `HOLD l AND r` `0x080813DC`,
`AND PRESS THE FOLLOWING KEYS` `0x0808144A`; title strings `PRESS START`
`0x0807D969`, `MAIN MENU` `0x0807D9BB`, `SELECT LANGUAGE` `0x0807D905`.

File offset = ROM address − `0x08000000` (e.g. validator at file `0xD90C`).

## 5. Algorithm

```
# runs once per frame while the title screen is active
handler(held, pressed):
    if (held & 0x300) != 0x300:          # L+R not both held
        idx1 = 0; idx2 = 0               # 0x0800DB14
        clear_A_bit(pressed)             # 0x0800DB20
        return

    if pressed == 0:                     # no new button this frame
        clear_A_bit(pressed)
        return

    # dispatcher 1 -- 0x03006524
    if pressed == SEQ1[idx1]:
        idx1 += 1
        if idx1 == 8:
            flag_03000187 = 1            # 0x0800DA20
            idx1 = 0
    else:
        idx1 = 0

    # dispatcher 2 -- 0x03007110 (evaluated in the same frame)
    if pressed == SEQ2[idx2]:
        if idx2 == 7:
            ram_020001EC = 0x08          # 0x0800DAC8
            ram_020001E8 = 0x000FFFFF
            idx2 = 0
        else:
            idx2 += 1
    else:
        idx2 = 0

    clear_A_bit(pressed)
```

`SEQ1 = [U,R,D,L,R,L,R,L]`, `SEQ2 = [U,L,D,R,L,R,L,R]` with
`U=0x40, D=0x80, L=0x20, R=0x10` (active-high joypad masks).

Notes from the instruction stream:

* The two dispatchers are independent and both run for every non-zero
  `pressed` value, so one press can advance one and reset the other.
* `idx1`/`idx2` are only reset by a wrong press or by releasing `L+R`; they
  persist across frames.
* The handler consumes bit 0 (A) every frame by clearing it in the pressed
  word (`0x0800DB22..0x0800DB26`, mask `0xFFFE`). This prevents A from starting
  the game while the title handler owns the input.
* The `pressed` word is the edge value from `0x0800A340`; held-over repeats do
  not re-trigger a step.

## 6. Tables

### 6.1 Accepted sequences (8 presses, L+R held)

| # | Sequence | Masks | Effect |
|---|---|---|---|
| 1 | Up, Right, Down, Left, Right, Left, Right, Left | `40 10 80 20 10 20 10 20` | `0x03000187 = 1` (mini cars) |
| 2 | Up, Left, Down, Right, Left, Right, Left, Right | `40 20 80 10 20 10 20 10` | `0x020001E8 = 0x000FFFFF`, `0x020001EC = 8` |

### 6.2 Flag layout

* `0x03000187` – boolean; read at `0x0800465C` to select the alternative
  (mini) car sprite/name table. Cleared on reset; not saved by the cheat.
* `0x020001E8` – 32-bit unlock bitfield. The cheat writes the 20 low bits
  (`0x000FFFFF`); `get_bit(n)` at `0x08018148` tests bit `n`.
* `0x020001EC` – byte written to `8` by the same action; `0x0801815C` returns
  it, `0x08018168` sets bits in `0x020001ED`.

### 6.3 Key masks

`A=0x01, B=0x02, Select=0x04, Start=0x08, Right=0x10, Left=0x20, Up=0x40,
Down=0x80, R=0x100, L=0x200` (active-high; hardware `KEYINPUT` at
`0x04000130` is active-low and idle `0x03FF`).

## 6b. Enumeration

**Space definition.** Alphabet: the four D-pad directions only (A/B/Start/
Select/L/R are either consumed or do not match any expected value). Length:
exactly 8 presses per code. Two independent index machines, each with a
single expected button per step and a single action at step 7. There is no
checksum, no character alphabet, no table of free-form strings, and no
reserved-bit field. Representable inputs: `4^8 = 65,536` direction strings
(plus arbitrary non-direction presses, which only reset an index).

**Closed-set proof (offline, exhaustive).** A Python model of the two
dispatchers above was run over all 65,536 sequences:

```
total 4^8 = 65536
accepted by mini dispatcher:   1  [(U,R,D,L,R,L,R,L)]
accepted by unlock dispatcher: 1  [(U,L,D,R,L,R,L,R)]
both (one 8-press code):       0
```

So the accepted set is exactly the two published sequences; a third
8-press code does not exist. This is a bounded negative about the whole
direction space, not a failure to find one.

**Novel code (not in any published list).** The two machines reset to 0 on
completion, so both can be entered back to back in one title visit. The
16-press sequence

```
L+R held:  Up, Right, Down, Left, Right, Left, Right, Left,
           Up, Left, Down, Right, Left, Right, Left, Right
```

sets **all three** flags at once. No published list documents this combined
entry; 3rd party cheat index list the two codes separately only.

RAM proof after entering it (title screen, mGBA debugger reads):

```
0x03000187 = 0x01        (mini cars)
0x020001E8 = 0x000FFFFF  (all 20 unlock bits)
0x020001EC = 0x08
0x03006524 = 0x00        (mini index reset after action)
0x03007110 = 0x00        (unlock index reset after action)
```

A second, separate novel (and undocumented) input: holding
**A+B+Select+Start** while the front-end frame handler `0x08003308` runs calls
`0x08003068`; the observed result is a return to the **SELECT LANGUAGE**
screen (the game's own front-end re-initialisation, not a BIOS reset).
Derived from `0x0800331A` (`(held & 0xF) == 0xF → bl 0x08003068`) and observed
in the emulator (language list drawn again after the combo).

**Bounds proven by in-game rejection** (all observed on the title screen):

| Input | Result |
|---|---|
| `U,R,D,L,R,L,R,U` (wrong 8th press) | both flags stay 0, both indices 0 |
| seven correct presses only | mini index = 7, `0x03000187` = 0 |
| then the 8th `Left` | `0x03000187` = 1, index back to 0 |
| `Up` then `Down` (wrong at index 1) | mini index resets 1 → 0 |
| correct sequence **without** L+R held | all flags 0, indices 0 |
| correct sequence with L+R held | flags set as above |

## 7. Validation evidence

**Observed**

* Title screen text `PRESS START` captured from `0x0800CBFC` (r2 =
  `0x0807D969`); language screen text `ENGLISH` / `SELECT LANGUAGE`
  (r2 = `0x0802EF38`, `0x0807D905`).
* Joypad reader: holding L+R gives `0x03000190 = 0xFF00` (buttons `0x300`);
  pressing A gives `KEYINPUT = 0x03FE`, Start gives `0x03F7`.
* Mini sequence → `0x03000187 = 0x01`.
* Unlock sequence → `0x020001E8 = 0x000FFFFF`, `0x020001EC = 0x08`.
* Combined 16-press sequence → all three values simultaneously.
* All rejection rows in §6b.
* `A+B+Select+Start` gate landed in `0x0800310A` and returned to the language
  screen.

**Derived**

* The two dispatch tables (`0x0800D9AC`, `0x0800DA74`), the expected button
  for each of the 8 steps, the reset paths and the exact flag writes were read
  from the Thumb instruction stream at `0x0800D90C`–`0x0800DB2E`.
* The `L+R` gate is `(held & 0x300) == 0x300` (`0x0800D950`–`0x0800D960`).
* `0x020001E8` is a bitfield consumed by `get_bit` at `0x08018148`;
  `0x03000187` is consumed at `0x0800465C`.
* `4^8` closed-set result from the reimplemented validator.

**Inferred**

* `0x020001EC`'s gameplay meaning (a progress/“custom Corvette” byte) is not
  labelled in the ROM; only its value `0x08` and its readers are proven.
* The hint text at `0x0812D3` is the developer's own description of the mini
  cars code; the direction icons are drawn as graphics, which is why the
  sequence itself is not an ASCII string in the ROM.

## 8. Unknowns

* Published `XOPENSEZ` (listed under “Passwords” for the GBA SKU) is absent
  from this image in ASCII, lowercase, UTF-16LE/BE, reversed and 5-bit
  packing. The GBA name-entry screen is a label (alphabet
  `XABCDEFGHIJKLMNOPQRSTUVWXYZ!.-` at `0x0802F66A`), and no `strcmp`/`memcmp`
  against the name buffer was found; it is treated as a cross-platform
  (PS2/Xbox) entry, not a GBA password.
* The deep race menus (challenge/car/track select, in-race pause) draw their
  labels with the pre-rendered/sprite path rather than the ASCII blitter
  `0x0800CBFC`; the front-end entry screens were identified by captured text
  (language, title) and by the 3-D screen that Start opens and B/Select
  cancels. Their labels are present in the localized string bank
  (`CORVETTE CHALLENGE`, `TIME CHALLENGE`, `GALLERY`, `RECORDS`, `OPTIONS`,
  `SELECT CHALLENGE`, `GRAND PRIX`, `RALLY`, `EXTRA`, `PAUSE QUIT`,
  `PAUSE RESTART`), but the labels themselves were not resolved to a
  per-item state variable in this pass.
* `0x020001E8` bits above 19 are never set by the game code seen; whether any
  exist as spare/unused bits was not proven behaviourally.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* Capstone 5.0.7 literal-pool / mask scans (Python)
* mGBA 0.10.5 SDL under `Xvfb :263`, debugger over a pty
  (`b`, `c`, `r/1..4`, `x/1`, `status`, `delete`), breakpoint on
  `0x0800A340` for frame-synchronous stepping
* Python validator model for the exhaustive `4^8` enumeration
* mGBA PNG savestates (`gbAs` zlib chunk, 397,312 bytes) for full IWRAM/EWRAM
  snapshots when a bulk diff was needed

No ROM or copyrighted assets are redistributed here; only hashes, addresses,
algorithms and observed flag values are published.
