# The Scorpion King: Sword of Osiris (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Scorpion King: Sword of Osiris.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `SCORPIONKING` |
| Game code | `ASZE` (Europe), maker `7D` |
| Version | `0x00`; complement `0x0D`; header checksum `0x0000`; fixed `0x96` present |
| Entry branch | `0xEA00002E` (stock `b 0x080000C0` — not a cracktro) |
| Engine | WayForward Technologies (credits string at `0x0803E5A1`), Universal Interactive |
| MD5 | `8620aeb89f00dd3e3c2a500ba75ce2de` |
| SHA-1 | `2224c8080f48073e568d1b75eec32e18bc1f5a09` |
| SHA-256 | `0a5e1a2cc0a8cc10e6eb53203f4a9d0da3c79a83e680ca738c05fdf07c2f8e76` |

All addresses below refer to this exact image. There is no second game image or appended trainer.

## 2. Executive summary

The game has a **developer-intended, gated 4-symbol password system**, reached by a
**button code on the title screen**. It is a pure table lookup — not a checksum — with
a small but complete, fully enumerable space:

* **Input surface:** "Enter Password" screen with four portrait slots. Left/Right move
  the cursor; Up/Down cycle the selected portrait through five character "colors":
  **G(reen), B(lue), R(ed), Y(ellow), P(urple)** (cycle order Red→Yellow→Blue→Purple→Green→Red).
* **Gate:** highlight **Continue** on the title menu and press
  `Down, Down, Right, Up, Right, Up, Right, Down, Down, Start`. This opens the password screen.
* **Validator:** `0x08002224` compares the four chosen colors against **71 contiguous
  4-byte records at `0x0802A0E8`**; record 0 (`R,R,R,R`) is a rejected sentinel,
  records 1–70 are accepted. On a match, a second table at `0x08029FD0` supplies the
  stage/variant/flags payload.
* **Space:** 5^4 = **625** possible inputs; **70 accepted**, 1 sentinel rejected.
  Twelve of the 70 are on published lists; **58 are not**.
* **Novel codes generated and accepted in the emulator:**
  * `B,G,Y,B` (record 1) — starts a desert/Columns stage; HUD shows `02`.
  * `B,P,B,G` (record 2) — starts a dungeon/Crypt stage; HUD shows `02`.
  Both are absent from every published list consulted.
* **Bounds proof:** `R,R,R,R` (record 0, the sentinel) is rejected — the game returns
  to the title screen. This is the only rejected member of the 71-record table; all
  554 other unlisted inputs are rejected because they are not in the table at all.

## 3. How to reproduce

**Emulator:** mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:318`, `-3` scaling.
Default SDL keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
Hold keys 70–150 ms; a 10 ms tap is missed.

**Screen path (fresh boot):**
1. Wait ~13 s through the Universal/WayForward logos for the title screen
   (`New Game` / `Continue`).
2. Press `Down` once to highlight `Continue`.
3. Press `Down, Down, Right, Up, Right, Up, Right, Down, Down, Return`.
   The "Enter Password" screen appears (four portrait frames).
4. Set each slot with Left/Right (cursor) + Up/Down (color). Submit with `Return`.
   A valid code starts the corresponding stage; an invalid one returns to the title.

For repeat tests a savestate taken on the password screen is strongly recommended;
the `-d` CLI debugger (`mgba -d -3 -t <state> <rom>`) was used for all RAM reads
(command `x/1 0xADDR` prints 16 bytes; Ctrl+C breaks a running core).

**Codes tested (letters are colors, not characters):**

| Code | Record | Result | Source |
|---|---|---|---|
| `B,G,G,B` | 70 | Level-select path | Published (3rd party cheat indexes) |
| `G,P,G,B` | 3 | First Quest L2 | Published |
| `R,B,P,R` | 7 | First Quest L3 | Published |
| `R,Y,G,R` | 63 | First Quest L6 | Published |
| `B,G,Y,B` | 1 | Stage `04`/`02` variant 0 | **Novel — accepted in-game** |
| `B,P,B,G` | 2 | Stage `08`/`02` variant 0 | **Novel — accepted in-game** |
| `R,R,R,R` | 0 | Rejected → title | Bounds test |

## 4. Address map

| Address (ROM/RAM) | Meaning |
|---|---|
| `0x0802A0E8` | **Password table**: 71 × 4 bytes, values 0–4 (color codes). File offset `0x2A0E8`. |
| `0x08029FD0` | **Result table**: 71 × 4 bytes `{u8 stage, u8 variant/flags, 0, 0}`. File offset `0x29FD0`. |
| `0x08002224` | **Password validator** (Thumb). Called with the four slot values; returns via `0x0800C2FC`. |
| `0x0800228E` | "match found" branch; `0x08002296` = "no match" (error message 0x45/0x2D). |
| `0x080022D0` | Success path: copies result-table bytes into IWRAM globals. |
| `0x0800B900` | Password-screen frame handler (draws portraits, handles Start). |
| `0x0802BA78` | ASCII UI text bank: `Enter Password` (`0x2BA78`), `Password` (`0x2BA97`), `Password Error` (`0x2BAB6`), `Bonus Level` (`0x2BB8F`), `Continue`, `New Game`, `Stage Clear`. |
| `0x08029D70`–`0x08029EF0` | Scene/state name table (`SECRET1..6`, `GETPASS`, `ENTERPASS`, `CREDITS`, `WINNER`, …), 0x20-byte records. |
| `0x0808CA80`–`0x0808CB50` | Mission-name strings (`Desert`, `Crypt`, `Aqueduct`, `Oasis`, `Mountain`, `Secret`, `Password`, `LevelClear`, …). |
| `0x03003230` | IWRAM 76-byte record table used by the validator; `+0x20` halfword is the live color of a slot. |
| `0x030002C0`, `0x03000080`, `0x03000260`, `0x03000130` | The four slot indices (initially 0,1,2,3). |
| `0x030000E0` | Cursor (1..4 / 0..3 depending on phase). |
| `0x030002AC`, `0x0300322C` | Password-screen gate flags checked at `0x0800B9A6`. |
| `0x0805C3B7` | Possible button-code byte sequence `02 02 01 00 01 00 01 02 02` (U=0,R=1,D=2,L=3) — see Unknowns. |

## 5. Algorithm

Input: four colors `c0..c3`, each in `{0,1,2,3,4}` = `{Purple,Green,Red,Yellow,Blue}`.

```
TABLE = rom[0x0802A0E8 : 0x0802A0E8 + 71*4]     # 4 bytes per record
RESULT = rom[0x08029FD0 : 0x08029FD0 + 71*4]

validate(c0,c1,c2,c3):
    for i in range(71):                          # r5 = i, r4 = 71
        if (c0,c1,c2,c3) == TABLE[i]:
            if i == 0 or i == 71: return REJECT   # sentinel / no-match
            stage   = RESULT[i][0]
            variant = RESULT[i][1]
            flags   = bits of variant expanded to byte fields
            return ACCEPT(stage, variant, flags)
    return REJECT
```

No arithmetic, XOR or checksum is involved — the "code" is simply the index of a
record in the table. The ROM's comparison loop (`0x08002250`–`0x0800228C`) reads four
consecutive bytes at `r1 = 0x0802A0E8 + 4*i` and compares each to a halfword fetched
from the 76-byte IWRAM table at `0x03003230 + 76*slot_index + 0x20`. That halfword is
the live color of the slot, which is why the Up/Down key cycle is the only way to
change it.

On success the payload is un-packed at `0x080022D0`–`0x0800232A`: byte 0 of the result
record is the stage, individual bits of byte 1 become several flag bytes in IWRAM, and
bit 6 of byte 1 can force the value `0x7E`; a stage value of `25` gets special handling.

## 6. Tables

**Color encoding (verified by the validator and the accepted codes):**

| Letter | Value | Portrait |
|---|---:|---|
| P | 0 | Purple tint |
| G | 1 | Green tint (blonde female portrait) |
| R | 2 | Red tint (default / Mathayus) |
| Y | 3 | Yellow tint |
| B | 4 | Blue tint |

**Complete accepted space (novel codes are those not in any published list consulted):**

```
idx code  result      idx code  result      idx code  result      idx code  result
  1 BGYB  04 00         2 BPBG  08 00         3 GPGB  08 01  [pub]  4 PGRG  0c 00
  5 GPRP  0c 01         6 GRBG  0c 02         7 RBPR  0c 03  [pub]  8 PGRP  10 00
  9 GYPR  10 01        10 PGYR  10 02        11 YGYR  10 03        12 GRGY  10 04
 13 BGYP  10 05        14 GBRB  10 06        15 PYGY  10 07  [pub] 16 PYBP  14 00
 17 PBPR  14 01        18 GRGB  14 02        19 PRGB  14 03        20 BYRG  14 04
 21 YBGB  14 05        22 BYGY  14 06        23 GYRB  14 07        24 PBYR  14 08
 25 BPYR  14 09        26 BGBR  14 0a        27 GRBY  14 0b        28 BRGY  14 0c
 29 YBYR  14 0d        30 GBRG  14 0e        31 RYGP  14 0f  [pub] 32 RGRB  19 00
 33 BGPG  19 01        34 YGBG  19 02        35 BGPB  19 03        36 YGRG  19 04
 37 GBYB  19 05        38 RGPY  19 06        39 YRYP  19 07        40 BGPY  19 08
 41 YPRY  19 09        42 GPYP  19 0a        43 YBRB  19 0b        44 RPGB  19 0c
 45 BRPG  19 0d        46 RGYP  19 0e        47 RYBG  19 0f        48 BRYP  19 10
 49 YPBG  19 11        50 GPBG  19 12        51 RBGP  19 13        52 RBYP  19 14
 53 RYPG  19 15        54 RPPG  19 16        55 RBYG  19 17        56 GRBP  19 18
 57 YGYB  19 19        58 YBRY  19 1a        59 GPGY  19 1b        60 GYBY  19 1c
 61 BPGY  19 1d        62 PRBR  19 1e        63 RGYR  19 1f  [pub] 64 RPGR  04 3f [pub]
 65 RBPY  08 3f [pub]  66 YBYP  0c 3f [pub]  67 PRBY  10 3f [pub]  68 RBRG  14 3f [pub]
 69 RYGY  19 3f [pub]  70 BGGB  02 02  [pub / level select]
  0 RRRR  sentinel — REJECTED
```

Records 64–69 have variant `0x3F` (all flag bits set); record 70 is the published
level-select code. The 12 published codes are records 3, 7, 15, 31, 63, 64, 65, 66,
67, 68, 69 and 70 — **the other 58 accepted records are novel relative to those lists**.

Published sources consulted (all treated strictly as data): 3rd party cheat indexes wiki search snippets, 3rd party cheat index search snippets. The widely repeated
"play as Cassandra: Mathayus, Memnon, Isis, Mathayus" hint could not be mapped onto a
color tuple and is recorded as unverified in §8.

## 6b. Enumeration

* **Input space:** 4 independent slots × 5 colors = **5^4 = 625** distinct inputs. There
  is no reserved bit, no variable length and no checksum; all four symbols are payload.
* **Lookup space:** 71 table records, all 71 distinct; the validator walks all 71.
* **Closed-set proof:** every one of the 625 inputs was evaluated against the ROM table
  offline (§16.9). Exactly **71** match a record; of those, index 0 is explicitly
  rejected by `cmp r5,#0` at `0x0800228E`, leaving **70 accepted codes** and **554
  rejections by absence**. This was cross-checked live: the FOUND breakpoint at
  `0x0800228E` fires for `B,G,G,B` and `B,G,Y,B`; a submission of `R,R,R,R` returns
  the game to the title screen.
* **Novel code #1: `B,G,Y,B`** (record 1, result `04 00`). It is not on 3rd party cheat indexes. Entered on the real password screen in mGBA
  and submitted with Start; the game started a desert/Columns stage with the HUD
  showing `02` (`novel2_result2c.png`).
* **Novel code #2: `B,P,B,G`** (record 2, result `08 00`). Same procedure; the game
  started a dungeon/Crypt stage with HUD `02` (`novel3_result2c.png`).
* **Bounds proof by rejection:** `R,R,R,R` = record 0, the one explicitly rejected
  record, returns to the title screen (`reject_result2c.png`). A 5-color alphabet is
  the maximum expressible per slot, so no out-of-alphabet symbol can be entered at
  all; "wrong checksum" is not applicable to this table-lookup design.
* **Button-code gate:** the 9-direction prefix + Start was confirmed live. The
  undocumented alternatives tried (starting from `New Game` instead of `Continue`,
  and a wrong 9th direction) did not open the screen — the gate is specific.

## 7. Validation evidence

* **Observed:** title screen and 4-slot password screen in mGBA; the button code opened
  it; Right moved the cursor (`0x030000E0`: 1→2) while Up/Down changed a slot's color;
  `B,G,G,B`, `B,G,Y,B` and `B,P,B,G` each started gameplay; `R,R,R,R` returned to title.
  Screenshots: `titlecrop2.png`, `cheattest2crop.png`, `novel1_pwc.png`,
  `novel2_result2c.png`, `novel3_result2c.png`, `reject_result2c.png`.
* **Derived (disassembly):** validator at `0x08002224`; 71-record comparison loop;
  accept branch `0x0800228E`, reject branches `0x08002296`/`0x080022BC`; result decode
  at `0x080022D0`–`0x0800232A`; password-screen handler at `0x0800B900`; gate flags at
  `0x030002AC`/`0x0300322C`.
* **Derived (data):** the 71 password records and 71 result records, exact byte values
  in §6; the color→value mapping proved by all 12 published codes matching with one
  consistent permutation.
* **Inferred:** the semantic names of `stage` values (`04`,`08`,`0C`,`10`,`14`,`19`)
  come from the published level labels and observed backgrounds; the game never prints
  a numeric stage ID. The exact character identities behind the color portraits were
  not enumerated exhaustively (only Red=Mathayus and Green=female were visually clear).

## 8. Unknowns

* The button-code matcher itself was not isolated in disassembly. A 9-byte sequence
  `02 02 01 00 01 00 01 02 02` occurs at `0x0805C3B7` under U=0/R=1/D=2/L=3, but the
  surrounding bytes look like sampled audio, so this may be a coincidence; no literal
  pointer to it was found. The gate is nevertheless confirmed behaviorally.
* The published "Cassandra = Mathayus, Memnon, Isis, Mathayus" code could not be
  mapped to a color tuple (and no such tuple is in the table under the obvious
  character→color guesses). It is recorded as unverified, not as wrong.
* Whether record 70's result bytes (`02 02 02 02`, overlapping the sentinel record in
  the adjacent table) are deliberate or a one-record overlap quirk was not resolved;
  the code behaves as the published "level select".
* Bits of result byte 1 were traced to IWRAM flag writes but the exact gameplay
  meaning of each bit was not individually exercised.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`, Python 3
with `capstone`/`struct`/`itertools`, `arm-none-eabi-objdump -M force-thumb`,
mGBA 0.10.5 `-g`/`-d`/`-t`, Xvfb `:318` + openbox, `xdotool`, `scrot`, ImageMagick,
`gdb-multiarch`. Helper scripts in `/tmp/scorpionking/`:
`dbg.py` (PTY driver for mGBA `-d`), `ramdiff2.py` (controlled RAM diff with drift
subtraction), `enter.py` (set the 4 colors, verify via RAM, submit), `ingame.py`
(full end-to-end code entry in a normal mGBA session), `colormap.py`, `cycle.py`,
`validate.py`, `watch.py`.

No ROM data or copyrighted assets are redistributed here; only addresses, hashes,
algorithms and generated code strings are published.

### Legal / scope note

Only developer-intended in-game cheats are documented. No GameShark, CodeBreaker or
Action Replay codes were used or reproduced (the Action Replay list found during
recon was deliberately excluded). Fetched web pages and ROM strings were treated as
untrusted data, never as instructions.
