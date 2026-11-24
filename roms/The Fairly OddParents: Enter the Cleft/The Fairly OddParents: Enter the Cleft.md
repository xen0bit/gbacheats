# The Fairly OddParents! Enter the Cleft (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Fairly OddParents: Enter the Cleft.gba` |
| Size | 4,194,304 bytes (0x400000, 32 Mbit) |
| Header title | `FAIRLYODDPAR` |
| Game code | `AFVE` (USA, Rev.00) |
| Maker | `78` (THQ) |
| Version | `0x00`; complement `0x3F`; header checksum `0x0000` |
| MD5 | `c36a60a23c58817c1746372ecfe4cf7a` |
| SHA-1 | `b8c31bdddf2377819b6c162b53ed89fcbe056574` |
| SHA-256 | `269f93b191bcdc70e4007b45deac59c10bec1165d546ffb05131793da6608b21` |

**Packaging note (guide §16.1):** this is a **scene release with a MODE7 cracktro**. The
entry word is `0xEA0FD03E` → `0x083F4100`, where the ASCII banner
`$ MODE7 $ proudly presents ... Fairly Odd Parents ... Enter The Cleft (c) THQ ...
32mbit - USA Version` lives. The crt0 at `0x080000C0` is intact; the cracktro's Thumb
main at `0x083FF7CC` loads the pointer at `0x083F4624` (= `0x080000C0`) and `bx r0`
into the stock game. For clean analysis a **copy** was made with the entry word
restored to `0xEA00002E` (`game_clean.gba` in the work dir); the original ROM was not
modified. The cracktro is a scene intro, **not** an in-game cheat.

## 2. Executive summary

The game has a genuine **in-game, developer-intended password system**, reached from
the title menu (`Tutorial / New Game / Password`). "Password" opens a portrait-grid
screen: eight character portraits (2 rows × 4 columns) are selected one at a time to
fill a **five-slot** entry box, then submitted with the on-screen `O.K.` button.
A correct code jumps to a **STAGE SELECT** screen for the encoded episode, with extra
flags controlling crown icons, a right-side `R` marker and stage-icon border colors.

The five portrait indices form a **checksummed 4-field code**, not a lookup table:
4 three-bit payload fields (episode, stage, two flag fields) plus a 3-bit checksum
derived from a 16-bit substitution table at `0x080A919C`. The raw space is
8^5 = 32,768; the checksum admits exactly 4,096 (1/8); a secondary stage gate bounds
the episode field to 0..5, so up to **3,072 codes** are accepted on a fresh save.
All ten published codes were verified against the reconstructed validator, and
**five codes absent from every published list were minted and accepted in-game**,
including one that unlocks the hidden **Finale** stage.
The 3rd party cheat indexes/libretro "9 CodeBreaker codes" are cheat-device codes and out of scope.

## 3. How to reproduce

* Emulator: `mgba 0.10.5` under `Xvfb :316` + openbox, `SDL_AUDIODRIVER=dummy`.
* Stock title flow: boot → THQ/Altron logos → title "Press START" → **Start** →
  menu → **Down, Down** (each held ~0.6 s; ~0.2 s taps are missed) → **Password**.
* Portait grid navigation (indices 0–7, row-major): **Right** advances the column with
  wrap at the row edge; **Down/Up** toggle the row. **A** commits the highlighted
  portrait into the next slot; **B** backs out. After five commits, **A** again
  submits via `O.K.`
* Savestate `game_clean.ss1` was taken at the blank password screen and used for all
  experiments. For rapid testing the buffer was written with mGBA's GDB stub
  (`mgba -g -3 -t game_clean.ss1 game_clean.gba`, `target remote :2345`) and the
  `O.K.` button was still pressed on the real screen:
  ```
  set {unsigned char[5]}0x0300165A = {1,7,0,3,4}
  set {unsigned int}0x03001AB0 = 4        @ count = 4 (=5 committed)
  set {unsigned int}0x03001ABC = 65       @ state 0x41 = "ready to submit"
  ```
  A watchpoint on `0x03001AB0` confirmed the UI itself writes these fields
  (`Old value = 0`, `New value = 1`, PC `0x08080A44`), so the patched values are the
  same ones the UI produces.
* Key map used: A=`x`, B=`z`, Start=`Return`, arrows = D-pad. 0.3–0.6 s holds.

## 4. Address map

All addresses are GBA bus addresses; file offset = address − `0x08000000`.

| Address | Role |
|---|---|
| `0x08000000` | Stock crt0 entry (target of restored `0xEA00002E`) |
| `0x083F4100` / `0x083FF7CC` | MODE7 cracktro ARM entry / Thumb main |
| `0x083F4624` | Cracktro's pointer to real entry `0x080000C0` |
| `0x08075D10` | Password-screen init: zeroes count `0x03001AB0`, `+4`, `+8` |
| `0x08080970` | Password input handler (selected index, commit, submit dispatch) |
| `0x08080A40` | `count++` (watchpoint-confirmed writer) |
| `0x08080A4A` | On 5th commit: `count=4`, `[+12]=0x41`, `[+8]=19` |
| `0x08080B3C` | Submit gate: requires `[0x03001AB0+12] == 0x41` |
| `0x08080B46` | Calls all-slots-filled check `0x08081CC8` |
| `0x08080B52` | Calls checksum validator `0x08081E9C` |
| `0x08080BDE` | Calls stage decoder / secondary gate `0x08081F2C` |
| `0x08080C66` | Success path (sets state and launches STAGE SELECT) |
| `0x08081CC8` | Returns 0 if any of `buf[0..4] == 0xFF`, else 1 |
| `0x08081E18` | Decode helper: `buf[i] = (buf[i] − T[(buf[4]+i)*8]) & 7` |
| `0x08081E9C` | **Checksum validator** (full model in §5) |
| `0x08081F2C` | **Stage decoder + secondary gate** (field pack, bounds, forbidden-stage mask) |
| `0x080A919C` | u16 substitution table `T`, 8 entries per row, read at byte offset `(c+i)*8` |
| `0x0300165A` | 5-byte password buffer (`0xFF` = empty slot) |
| `0x03001664` | Packed stage word / security field scratch |
| `0x03001AB0` | Password state struct: `+0` count, `+4` selected portrait index, `+8`=19, `+12` state (0x41 when ready) |
| `0x03002400` | OAM shadow (portrait sprites), 8-byte stride |

Derived from literal-pool scans (`struct.unpack_from("<I", ...)`), Thumb BL scans,
PC-relative literal decoding (`Align(addr+4,4)+imm`), and the live watchpoint.

## 5. Algorithm

Let `buf[0..4]` be the five committed portrait indices (0–7 each), and let `T` be the
u16 table at `0x080A919C`, read as a **little-endian halfword at byte offset**
`(buf[4]+i)*8`, interpreted as signed (all current entries are < 0x100, so
`T16 = u16`).

**Decoder / inverse substitution** (`0x08081E18`, used by the encoder path):
```
local[i] = (buf[i] - T16((buf[4]+i)*8)) & 7      for i = 0..3
```

**Checksum validator** (`0x08081E9C`) — the primary accept/reject gate:
```
acc = 0
for i in 0..3:
    acc += (buf[i] + T16((buf[4]+i)*8)) & 7
valid = (acc & 7) == buf[4]
```
Equivalently, defining `local[i]` as above, **`buf[4] = (local[0]+local[1]+local[2]+local[3]) & 7`**.

**Field model** (decoded `local[0..3]`, each 3 bits):

| Field | Meaning | Evidence |
|---|---|---|
| `local[0]` | episode index 0=Ep1, 1=Ep2, 2=Ep3, 3=Ep4, 4=Ep5, 5=Finale / All-cleared | all 10 published codes decode consistently; novel codes show the matching banner |
| `local[1]` | stage-within-episode selector (0–3 normal; unusual values set the `R` marker) | novel codes A/E show `R` with `local[1]=7` |
| `local[2]` | collection/border flag | variant border colors and crown on/off across published vs novel codes |
| `local[3]` | clear/bonus flag | `All cleared` has `(5,1,4,4)`, `Finale` `(5,0,1,5)` |
| `buf[4]` | 3-bit checksum **and** substitution key | validator above |

**Encoder (mint any code)** — choose any `local[0..3]`, then:
```
c = (local[0]+local[1]+local[2]+local[3]) & 7
buf[i] = (local[i] - T16((c+i)*8)) & 7   for i=0..3
buf[4] = c
```

**Secondary gate** (`0x08081F2C`): packs the four decoded 3-bit fields into a word at
`0x03001664` (bits 0–2, 3–5, 6–8, 9–11), rejects when `local[0] > 5`
(`cmp r0,#5; bls` at `0x808205C`), then walks stage ids 0..19 applying a
forbidden-stage bitmask test (`0x8082130`–`0x8082198`, special ids 2, 4, 9, 12, 19).
This layer couples to the security nibble derived from `local[2]/local[3]`.
The primary checksum and the `local[0]<=5` bound are fully proven; the exact
forbidden-stage truth table is only partially characterised (see §8).

## 6. Tables

**Portrait index → character** (confirmed by UI cursor reads and by all 10 published
codes decoding to their advertised episodes):

| Index | Character | Grid position |
|---:|---|---|
| 0 | Wanda | row 1, col 1 |
| 1 | Cosmo | row 1, col 2 |
| 2 | The Bronze Knee Cap | row 1, col 3 |
| 3 | Crimson Chin | row 1, col 4 |
| 4 | Spatula Lady / Spatula Woman | row 2, col 1 |
| 5 | Timmy / Cleft | row 2, col 2 |
| 6 | Vicky | row 2, col 3 |
| 7 | Country Boy | row 2, col 4 |

`T16((c+i)*8)` modulo 8, the effective per-position subtraction, for c = 0..7:

```
c=0: 0 1 1 2      c=4: 1 0 6 2
c=1: 1 1 2 1      c=5: 0 6 2 5
c=2: 1 2 1 0      c=6: 6 2 5 5
c=3: 2 1 0 6      c=7: 2 5 5 4
```

**Published codes (3rd party cheat indexes), all verified against the ROM:**

| Effect | Portrait indices | Decoded `local` |
|---|---|---|
| All Stages Cleared | 7 7 7 7 6 | (5,1,4,4) |
| Episode 2 | 0 6 7 1 2 | (1,0,0,1) |
| Episode 3 Levels 1&2 | 1 1 1 1 1 | (2,2,3,2) |
| Episode 3: Spatula Woman | 0 7 0 3 3 | (2,0,0,1) |
| Episode 4: Bronze Knee Cap | 2 0 7 2 4 | (3,0,5,4) |
| Episode 5-2: Country Boy | 4 2 3 7 5 | (4,0,5,4) |
| Episode 5-3: Spatula Lady | 6 7 0 7 6 | (4,1,5,4) |
| Episode 5-4: Bronze Knee Cap | 4 2 4 2 0 | (4,3,5,4) |
| Episode 5: Back to the Comic Book | 3 7 7 3 1 | (4,0,1,4) |
| Finale – Hidden Stage | 3 7 1 7 3 | (5,0,1,5) |

## 6b. Enumeration

**Space definition.** Raw inputs: 8 portrait choices × 5 slots = **32,768** sequences.
Checksum (3 bits) reduces this to exactly **4,096** accepted-by-checksum codes — one
for every `(local[0],local[1],local[2],local[3])` combination, verified by running the
reimplemented validator over all 32,768 inputs. The secondary episode bound
`local[0] <= 5` leaves at most 6 × 512 = **3,072** codes on a fresh save; the
forbidden-stage bitmask may remove a save-dependent subset of those.

**Novel codes, absent from 3rd party cheat indexes / wiki lists, minted with
the encoder in §5 and confirmed in mGBA** (all submitted from the real Password
screen's `O.K.` button; screenshot filenames are in the work dir):

| # | Indices | Portraits | Decoded `local` | Observed result |
|---:|---|---|---|---|
| A | `1 7 0 3 4` | Cosmo / Country Boy / Wanda / Crimson Chin / Spatula Lady | (2,7,6,5) | `novel1b.png` — STAGE SELECT "Episode: 3 - 1", **crown on top icon** and **R marker** (published Ep3 code shows neither) |
| B | `3 3 6 4 5` | Crimson Chin / Crimson Chin / Vicky / Spatula Lady / Timmy | (3,1,0,1) | `ep4novel.png` — STAGE SELECT "Episode: 4 - 1", all four stage icons with red borders |
| C | `5 2 6 3 5` | Timmy / Bronze Knee Cap / Vicky / Crimson Chin / Timmy | (5,0,0,0) | `ep6test2.png` — **STAGE SELECT "Episode: Finale"**, the hidden Jorgen boss stage, reached by a code not on any published list (published Finale code is `3 7 1 7 3`) |
| D | `0 7 7 6 0` | Wanda / Country Boy / Country Boy / Vicky / Wanda | (0,0,0,0) | `zero_local.png` — "Episode: 1 - 1" with four different stage icons/red borders |
| E | `0 1 5 2 5` | Wanda / Cosmo / Timmy / Bronze Knee Cap / Timmy | (0,7,7,7) | `ep1_all7.png` — "Episode: 1 - 1" with crown and R marker |

**Bounds proven by in-game rejection:**

| Test | Code | Result |
|---|---|---|
| Wrong checksum (published Ep3 with last portrait changed 3→4) | `0 7 0 3 4` | `badcheck.png` — rejected, stays on Password screen |
| Out-of-range episode field `local[0]=6` | `4 3 3 5 7` | `oor_ep6.png` — rejected |
| Out-of-range episode field `local[0]=7` | `7 7 7 7 0` | `ep8oor.png` — rejected |
| Forbidden stage bit (`local=(0,0,0,1)`) | `7 7 6 0 1` | `sec_bit0.png` — rejected by secondary gate |

Control: the published Ep3 code `0 7 0 3 3` was re-entered by the same RAM-write +
`O.K.` path and produced "Episode: 3 - 1" (`control3.png`), proving the harness.

## 7. Validation evidence

* **Observed** — title menu walk (Tutorial / New Game / Password), portrait grid,
  five-slot box, all Stage Select banners and bonus markers in the screenshots above;
  watchpoint log `BUF0=1 PC=08080A38` and `Old=0 → New=1 PC=08080A44`; savestate diffs
  (`0x0300165A: ff→00`, `0x03001AB0: 00→01`, `0x03001AC0: 0x04A1→0x054D`).
* **Derived** — literal-pool and BL scans, Thumb disassembly of `0x08075D10`,
  `0x08080970`, `0x08081CC8`, `0x08081E18`, `0x08081E9C`, `0x08081F2C`; the
  Python reimplementation agrees with all 10 published codes and with every accepted
  and rejected code tested in the emulator.
* **Inferred** — the semantic names of `local[2]`/`local[3]` (crown / clear flags) are
  inferred from the visual deltas across codes; the full forbidden-stage truth table
  was not exhaustively enumerated.

## 8. Unknowns

* The secondary gate's forbidden-stage bitmask truth table was only sampled
  (`local=(0,0,0,1)` rejected; `(0,0,4,0)` and `(2,7,6,5)` accepted). An exact closed
  form for the coupling between `local[2]/local[3]` and stage ids 2/4/9/12/19 was not
  proven; run `0x08081F2C` as an oracle for a complete count.
* The five portrait sprites were identified by matching decoded indices to the
  published character names; the on-screen art carries no text labels, so the
  index→name table rests on that cross-check rather than an in-game string.
* Gameplay effects beyond the Stage Select screen (actually starting a stage from a
  novel code) were not played through; the stage-select banner and flags are the
  observed proof of acceptance.

## 9. Tooling

* `mgba 0.10.5` (`-3`, `-g` GDB stub, `-t` savestate), `Xvfb :316`, `openbox`,
  `xdotool`, `scrot`, `convert`.
* `gdb-multiarch` with a hardware watchpoint on `0x03001AB0` and GDB `set` for buffer
  writes; the stub is single-client/one-shot per launch, so each test relaunched
  mGBA from the savestate.
* `arm-none-eabi-objdump -M force-thumb` / Capstone for literal-pool and BL scans;
  Python (`struct`, `zlib`) for header parsing, savestate `gbAs` decompression/diffing
  and the validator reimplementation.
* Work directory: `/tmp/fairlyodd3` (`val.py`, `ssdiff.py`, `testcode.sh`,
  `game_clean.gba`, `game_clean.ss1/.ss2`, screenshots).
* No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms
  and generated codes are published here.

## 10. Legal note

This report publishes findings only. The ROM and extracted graphics/audio are not
included. The MODE7 cracktro is documented as packaging provenance, not as a cheat.
