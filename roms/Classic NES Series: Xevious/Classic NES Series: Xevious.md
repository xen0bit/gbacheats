# Classic NES Series: Xevious (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Classic NES Series: Xevious.gba` (1,048,576 bytes / 0x100000) |
| Header title | `XEVIOUS` |
| Game code / maker | `FXVE` / `01` (region nibble `E` = US/Europe build) |
| Version | `0x00` |
| Entry word | `0xEA000031` → ARM at `0x080000CC` |
| Fixed `0xB2` | `0x96` (valid) |
| Complement byte `0xBD` | `0x84`; recomputed value `0x84` (valid) |
| Header checksum `0xBE` | `0x0000` (rebuilt-header artifact seen in every Classic NES Series dump) |
| MD5 | `ac693d395395405b5cc902877025e675` |
| SHA-1 | `b2088582808480e0d70c63a777b046409d4e15c4` |
| SHA-256 | `604fd742a0c19ef09bf4d863dfb8a62ada973546b4dd4fbc84aa0c702a20f261` |

**Embedded-image scan.** Scanning the whole file for the 156-byte Nintendo logo
found exactly two GBA headers:

* `0x000000`: the main image (above).
* `0x015268`: a complete second header (`XEVIOUS`, `FXVE`, version 0), entry
  `0xEA000061` → `0x08153F4`. Its `0xC0` block holds the multiboot record
  (`11 00 00 ea`, destination pointer `0x0200D308` at `+0xCC`, `2a 00 00 ea`
  at `+0xE0`) and SIO register literals (`0x04000128` at file `0x18234` /
  `0x18444`). This is the single-pak link-play client image, not a second game.

**Patch/trainer check.** Stock: the entry word branches to the wrapper's own
crt0, `0xB2`/`0xBD` are valid, the boot signature at `0xC4` reads
`…OUS_1_2P` (the per-title wrapper signature), and no cracktro, trainer menu,
appended loader, or altered first-4-KiB code exists. The only added bytes are
the normal wrapper payload at `0x18000`+.

**Layout (file offsets).**

| Range | Content |
|---|---|
| `0x000000`–`0x017FFF` | GBA wrapper code/data (ARM crt0 at `0xC0`, Thumb code from `0x130`) |
| `0x015268`–`0x017FFF` | second (multiboot/link-client) header + code, inside the wrapper area |
| `0x018000`–`0x0FFFFF` | wrapper-encoded NES payload and filler (no plaintext NES image) |

## 2. Executive summary

The ROM is an **emulated Famicom/NES Xevious** inside the Classic NES Series
wrapper. At runtime the NES PRG (16 KiB) is at EWRAM `0x02000000+0x4000`
(NES `$C000`–`$FFFF`, NROM-128), NES CHR (8 KiB) at `0x02008000`, and the 2 KiB
NES RAM at IWRAM `0x03007200` (verified from mGBA savestates).

There is **no password system, no unlockable, no debug menu and no reachable
button cheat in this image**. The complete in-game cheat/selection surface is:

1. **NES title / pause**: `Start` at the title enters game state `$10 = 2`;
   `Start` during play toggles the pause word `$22` (0↔1). `A`, `B` and
   `Select` do nothing on the title screen (observed).
2. **Wrapper System Menu** (`L + R`): exactly **five** slots —
   `CONTINUE`, `RESET`, `LINKED PLAY`, `SAVE HIGH SCORE`, `SLEEP MODE` — all
   labelled. The selector is a 5-value ring (0…4, wraps both ways); the
   dispatcher is bounded by `CMP #4` with a five-entry table. There is **no
   unlabelled/undocumented slot** in this title.
3. **NES debug command (dead)**: the Japanese Famicom release's debug entry is
   present verbatim in the NES PRG — hold pad-2 `A` **or** `B`, then press
   Right ×9, Up ×2, Left ×2, Down ×9. The gate is live in this GBA build
   (the wrapper mirrors the GBA pad to NES pad 2, and the gate index reaches
   22), but its completion hook calls `$C00F`, which is a one-byte `RTS`.
   There is no digit display, no digit buffer, no editor and no consumer: after
   completion the NES nametable, the sprite shadow and the game state are
   unchanged, and extra buttons do nothing.

Consequently the published four **8-digit debug values** (`01110000`,
`00001100`, `10000000`, `00000011`) are inapplicable to this SKU: GameFAQs
labels that menu “Japanese version”, and the US image contains only the entry
check, not the menu body. This engagement is closed as a **bounded negative**
per guide §0.2.5: the menu space is enumerated (5 wrapper slots), the button
space is bounded (one sequence table in the entire 16 KiB PRG), the published
sequence is tested and accepted by the gate, and its effect is shown to be
absent by RAM/VRAM evidence.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL under `Xvfb :256` + `openbox`, `SDL_AUDIODRIVER=dummy`,
3× scale. Default SDL keymap: `x`=A, `z`=B, `a`=L, `s`=R, `Return`=Start,
`BackSpace`=Select. Savestates: `Shift+F1` save, `F1` load.

| Screen / action | How to reach |
|---|---|
| Title (NES state `$10=0`) | boot, or wrapper menu → `RESET` |
| Start game (`$10=2`) | `Return` at the title |
| Pause (toggle `$22`) | `Return` during play |
| Wrapper System Menu | hold `a`+`s` (L+R) ~0.5 s |
| Menu cursor | `Up`/`Down` (ring 0→1→2→3→4→0) |
| Menu select | `x` (A); `z` (B) closes the menu |
| NES debug gate | at title (`$10=0`), hold pad-2 A or B, press Right×9, Up×2, Left×2, Down×9 |

**Observed reproduction of the debug gate** (all values read from NES RAM in
the savestate, `0x03007200 + $xx`):

```
title, no buttons      $ED=0  $E8=0x08   (gate not armed)
hold A+B               $ED=0  $E8=0x80   (armed, waiting for Right)
Right                  $ED=1  $E8=0x80
… 9×Right, 2×Up, 2×Left, 9×Down
complete               $ED=22 $E8=0x00
extra Right/A/B/etc.   $ED=22 $E8=0x00   (no re-arm, no effect)
```

The wrapper System Menu selector byte is `0x03007B4D`
(`0x03007200 + 0x94D`). Pressing `Down` walks it `0,1,2,3,4,0`; `Up` walks
`0,4,3,…`. The menu handler pointer `0x030064E4` is `0x080025ED` while the
menu is open and `0x08002855` in the game/title state.

## 4. Address map

### GBA wrapper (file offset + `0x08000000`)

| Address | Meaning |
|---|---|
| `0x080025EC` | System-Menu state handler (L+R open/close, selector reset) |
| `0x08002600`–`0x0800261A` | exact L+R gate: `held==0x300` and `held & pressed` |
| `0x08002634`–`0x08002640` | dispatch: `CMP #4; BHI default`; table at `0x08002654` |
| `0x08002654` | 5-entry handler table: `0x08002668`, `0x08002674`, `0x08002680`, `0x08002758`, `0x08002764` |
| `0x08002794` | cursor Up (`0x40`), wrap 0→4 (`CMP #4` after load) |
| `0x080027C2` | cursor Down|Select (`0x84`), wrap 4→0 (`CMP #4`) |
| `0x08003B60` | message-record table base, 55 records × 8 bytes `{u16 xy, u16 wh, u32 text_ptr}` |
| `0x08003B90` | record 6 = System-Menu text (`X MENU X` / five item names) |
| `0x03007B4D` | System-Menu selector (context `0x03007200` + `0x94D`) |
| `0x030064E4` | current wrapper state handler pointer (Thumb) |

### NES PRG (runtime EWRAM `0x02004000`, NES `$C000`; disassemble base `$C000`)

| NES address | Meaning |
|---|---|
| `$FAF6` | RESET (vectors at `$FFFA`: NMI `$FC4E`, RESET `$FAF6`, IRQ `$FF1D`) |
| `$FC4E` | NMI |
| `$FC9B`–`$FCC7` | **debug gate** (only runs while `$10==0`) |
| `$FF06` | debug sequence table, 22 bytes + `$00` terminator |
| `$C00F` | completion hook: single `RTS` (`0x60`) — **no handler** |
| `$FE37`–`$FE7D` | controller read: `$06`/`$0A` held pad1/pad2, `$09`/`$0D` pressed |
| `$FCA1` | `LDA $0A; AND #$03` (pad-2 A or B held) |

### NES RAM (IWRAM `0x03007200`)

| Address | Meaning | Observed values |
|---|---|---|
| `$10` | game state | 0 title, 2 play |
| `$22` | pause/start toggle (parity) | 0↔1 on Start |
| `$06`/`$0A` | pad 1 / pad 2 held | `$0A` mirrors `$06` on one GBA |
| `$09`/`$0D` | pad 1 / pad 2 pressed edge | 0/− |
| `$E8` | expected next sequence button (`0` = gate complete) | `0x08` idle, `0x80` armed, `0` complete |
| `$ED` | sequence index | 0…22 |

Pad bit order in this engine (read by `ROR` over 8 `$4016` bits):
`A=0x01, B=0x02, Select=0x04, Start=0x08, Up=0x10, Down=0x20, Left=0x40,
Right=0x80`.

## 5. Algorithm

### 5.1 NES debug gate (reimplementation, agrees with the ROM)

```
SEQ = [0x80]*9 + [0x10]*2 + [0x40]*2 + [0x20]*9 + [0x00]
ed, e8 = 0, 0x08
def frame(pad2_held, pad2_pressed):
    global ed, e8
    if game_state != 0: return
    if not (pad2_held & 0x03): return          # A or B must be held
    exp = SEQ[ed]
    if exp == 0:
        call_0xC00F()          # RTS — no-op in this build
        return
    e8 = exp
    if pad2_pressed == exp:
        ed += 1
        e8 = SEQ[ed]           # 0 after the 22nd press
    else:
        ed = 0                 # any wrong press restarts
```

Agreement with the ROM: valid sequence → `$ED=22, $E8=0`; Down first →
`$ED=0, $E8=0x80`; Right×3 then Up → `$ED=0`; no A/B hold → `$E8=0x08,
$ED=0`; extra press after completion → unchanged.

### 5.2 Wrapper System Menu

```
if pressed == 0x300 and (held & 0x300):   # exact L+R on the press frame
    selector = 0; open menu
if Up:    selector = (selector == 0) ? 4 : selector-1
if Down/Select: selector = (selector == 4) ? 0 : selector+1
if A/Start: dispatch[selector]            # bound: CMP #4; table of 5
```

The same `L+R` closes an open menu (observed). Holding `Start` *before* L+R
suppresses the open (press word becomes `0x308`), which proves the gate is
exact.

## 6. Tables

### 6.1 Wrapper System-Menu items (record 6, `0x08003B90`)

| Slot | Label drawn | Dispatch handler | Observed effect |
|---:|---|---|---|
| 0 | `CONTINUE` | `0x08002668` → installs `0x080017ED` | menu closes, game resumes |
| 1 | `RESET` | `0x08002674` → installs `0x08001871` | NES reset to title (`$10=0`) |
| 2 | `LINKED PLAY` | `0x08002680` (inline) | link-play screen (`WIRELESS LINK PLAY`) |
| 3 | `SAVE HIGH SCORE` | `0x08002758` → installs `0x08002499` | save dialog; 8 KiB `.sav` rewritten |
| 4 | `SLEEP MODE` | `0x08002764` → installs `0x0800190D` | sleep screen; `Select+L+R` exits |

### 6.2 Debug sequence table (`$FF06`, file offset `0x3F06`)

```
80 80 80 80 80 80 80 80 80   9×Right
10 10                        2×Up
40 40                        2×Left
20 20 20 20 20 20 20 20 20   9×Down
00                           terminator
```

This is the only run of ≥4 contiguous button masks in the 16 KiB PRG other
than data coincidences at `$C19E`/`$F977` (verified by disassembly: those are
sprite/level byte tables, not a comparator).

### 6.3 Published values (verified against the image)

| Published code (JP menu value) | Status in this image |
|---|---|
| Entry sequence Right×9/Up×2/Left×2/Down×9 | **present**, gate accepted (`$ED=22`) |
| `01110000` (1UP every 50k/150k) | **not representable**: no digit UI/consumer |
| `00001100` (aggressive enemies) | not representable |
| `10000000` (invincibility) | not representable |
| `00000011` (5 lives) | not representable |

## 6b. Enumeration

**Space A — wrapper selector.** 5 values (0…4). All five are labelled in
record 6; the dispatcher bound is `CMP #4` with a 5-entry table at
`0x08002654`; the cursor wraps `4→0` (Down) and `0→4` (Up), both observed.
Number of representable values = **5**; number of unlabelled values = **0**.
A sixth slot is not expressible through input.

**Space B — NES debug gate.** Input alphabet: the ten pad-2 button masks;
sequence length 22 with a `$00` terminator. The accepted set is **exactly 1**
sequence (the one above); the gate index `$ED` takes 0…22 and the expected
value `$E8` is derived from the table. Terminal action: `JSR $C00F` = `RTS`.
Therefore the output space of the gate is **empty**: no screen, no flag, no
game-state change (nametable diff 0, no new sprite entries, `$10` unchanged).

**Space C — published 8-digit cheat values.** 2^8 = 256 combinations. This
image contains **no writer** (no digit editor), **no storage** (no buffer whose
reader is a cheat check; the only 8-byte zero-page array `$D8–$DF` is a sprite
slot table with `0x80` sentinel, written at `$C010` and read at `$C209`/`$C265`/
`$C27D`) and **no consumer**. Reachable subset = **0**. The four published
values are therefore JP-ROM data, not this SKU's.

**Novel code.** None can be minted: an accepted code must change state through
`$C00F`, which is a one-byte `RTS`. The gate-complete state (`$ED=22,
$E8=0`) is reachable and RAM-verified but is behaviourally identical to the
idle title; it is not a code and does not appear in any published list.

**Bounds proven by rejection (all observed in mGBA):**

| Test | Result |
|---|---|
| Down as first press (holding A+B) | `$ED=0` (not 1) |
| Right×3 then Up (wrong 4th) | `$ED` resets from 3 to 0 |
| Sequence without A/B held | gate not armed (`$E8=0x08`, `$ED=0`) |
| A only, or B only, + Right | `$ED=1` (both accepted, as the JP guide states) |
| Complete 22-press sequence | `$ED=22, $E8=0`; NES nametable 0 diffs; sprite shadow has no digit entries |
| Extra A/B/Left/Right/Down/Up after completion | `$ED=22, $E8=0`; nametable 0 diffs |
| Wrapper `L+R+Start` with Start pressed first | menu does **not** open (handler stays `0x08002855`) |
| Wrapper `L+R` alone | menu opens (handler `0x080025ED`, selector 0) |

**Search space bounded (negative evidence).**

* GBA image ASCII keyword scan (1 MiB, case-insensitive): `PASSWORD` 0,
  `CHEAT` 0, `DEBUG` 0, `SECRET` 0, `UNLOCK` 0, `LEVEL` 0, `STAGE` 0, `CODE` 0;
  `SOUND`/`TEST` occur once each (Namco staff credit text, not a menu).
* Wrapper text is font-encoded, not ASCII; its full message bank is 55 records
  at `0x08003B60`, decoded with the per-screen glyph map. No “enter code”
  prompt exists; records 50/53 (`SAVE HIGH SCORE AND SECRET CODE!`,
  `PRESS THE A BUTTON TO USE THIS SECRET CODE.`) are the shared-series save
  dialog, not an entry screen.
* NES PRG: 16,384 bytes, 33 printable ASCII strings ≥4 chars (copyright,
  staff names, `PUSH START`), zero password/cheat/debug strings.
* NES PRG button-mask scan: exactly one contiguous sequence table (`$FF06`);
  all other mask runs are code/data (disassembled and rejected).
* Published literals `01110000` / `00001100` / `10000000` / `00000011` are
  absent as ASCII, as raw bytes, and as 8-byte 0/1 arrays.

## 7. Validation evidence

**Observed**

* Boot → title (`$10=0`); `Start` → `$10=2`; `Start` in play toggles `$22`.
* `L+R` opens the System Menu; selector `0x03007B4D` walks 0→1→2→3→4→0 and
  wraps 0→4 on Up; handler pointer `0x030064E4` toggles `0x080025ED` ↔
  `0x08002855`; `B` closes the menu.
* Slot effects observed: 0 closes; 1 resets to title; 2 opens the link screen;
  3 rewrites the 8 KiB `.sav` and shows the save dialog; 4 opens the sleep
  screen and `Select+L+R` exits.
* Debug gate: `$ED` reaches 22 with `$E8=0`; no nametable change, no digit
  sprites, no state change; rejection tests above.
* NES pad 2 (`$0A`) mirrors pad 1 on a single GBA (verified by holding Up and
  reading `$06=$0A=0x10`), so the JP command can be driven from one GBA.

**Derived**

* `$C00F` is a single `RTS`; the only read of `$E8` is `$FD96` → `JSR $C00F`;
  the only reader of `$ED` is the gate. Therefore the gate has no consumer.
* The System-Menu dispatch is exactly five entries (`CMP #4`, table
  `0x08002654`), and the selector has no out-of-range path.
* The wrapper save dialog uses messages 49 (“SAVING…”) and 50 (“SAVE HIGH
  SCORE AND SECRET CODE!”) via the handler installed by slot 3.

**Inferred**

* The US `FXVE` release contains the Famicom entry check but not the JP-only
  debug menu body; the published 8-digit values belong to the Japanese
  Famicom/Famicom-Mini ROM. The stub `$C00F` and the absence of any other
  pad-2 reader are the evidence; no JP ROM was available for byte comparison.
* The `SECRET CODE` strings are shared-wrapper leftovers (as in Donkey Kong
  and Dr. Mario), unreferenced by any code-entry screen.

## 8. Unknowns

* The JP-only menu body was not recovered (not present in this image); its
  digit buffer and effect flags are unknown and cannot be tested here.
* Linked play with a second GBA was not exercised (no second unit); the link
  client image at `0x015268` and the link screens are present, and a real
  pad 2 could in principle drive the gate, but the terminal `RTS` makes the
  outcome the same.
* The exact purpose of the 475-byte EWRAM block at `0x0200A000` (wrapper font
  / attribute buffer) was not needed for the answer.

## 9. Tooling

* `p0.py` — header, hash, complement, embedded-logo scan.
* `ss.py` — zlib-decompress the `gbAs` chunk of an mGBA `.ss1` PNG and address
  VRAM (`0x1000`), IWRAM (`0x19000`), EWRAM (`0x21000`); 397,312-byte state.
* `dis6502.py` — py65-based 6502 disassembler over the runtime PRG (`$C000`).
* `scanzp.py`, string/keyword scans, button-mask run scan, message-table dump
  and BG-tilemap/font rendering (text-only; no image files used).
* mGBA 0.10.5 SDL, Xvfb `:256`, openbox, xdotool.

## 10. Legal note

No ROM, extracted graphics, music, or game text beyond the short menu strings
needed as evidence is redistributed. All findings are hashes, addresses,
algorithms, and short quotations.
