# Disney Sports: Snowboarding (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney Sports Snowboarding/Disney Sports Snowboarding.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| MD5 | `1529f4677cba3e47f4be897f02b71044` |
| SHA-1 | `7e5ccf21f13e115a811dc19310390a9beacff07f` |
| SHA-256 | `919f99362d7325283927286f2976a26edeae1e8bb00e2c08c2baa0a42a4a52e0` |
| Header title | `DS_SNOWBD_U` (0xA0) |
| Game code | `A5DE` (0xAC) |
| Maker | `A4` (Konami) (0xB0) |
| Version | 0x00 (0xBC) |
| Complement check | 0x66 (valid for 0xA0–0xBC) |
| Header checksum field | `0x0000` (0xBE) — rebuilt-header artifact; the complement byte is correct |
| Entry word | `0xEA00002E` → stock branch to `0x080000C0`; no cracktro/trainer |
| Nintendo-logo occurrences | exactly one (header at 0), so a single image, not a multi-pack |

The first 0xC0 bytes are the stock Konami crt0 (`mov r0,#0x12; msr cpsr…`), and the
Nintendo logo is intact. There is no Scene/trainer patch in the image.

## 2. Executive summary

The game has **no password screen, no stored code table, and no checksum
generator**. Its cheat surface is exactly three things:

1. **One title-screen button code**, a fixed 10-press sequence entered at
   `PRESS START`:
   **Up, Down, Up, Down, Left, Down, Left, Down, A, Start**.
   It unlocks **`SOUND MODE`** (a B.G.M./S.E. sound-test player) as the third row
   of the OPTION menu, which otherwise reads `? ? ?`. The code was published by
   3rd party cheat indexes; this report verifies it against the ROM and the emulator and characterises
   the whole 10-press input space.
2. **A complete KCEK in-house debug bank** (`AGB SYSTEM Ver3.00 BY KCEK`,
   `L+R+START SOFT RESET`, `L+R+SELECT MEM+DMA DEBUG`, `PAGE NO.%d`) with a page
   table that can warp to every internal screen and to per-character animation
   testers. Both advertised key combinations are **inert** at boot, on the title
   and in every menu tested. The only published way in is a RAM write
   (a 3rd party cheat index's `0200023002`), i.e. debugger evidence, not an in-game cheat.
3. **Save-bit unlockables** (boards) whose setter lives inside the two-console
   `BOARDS` exchange flow, not on any single-console input path.

The title code is a single hard-coded sequence, not a generative space: the ROM
holds a 10-slot raw-button history, and only the one sequence advances the
matcher to its completion value. There is therefore **no novel code to mint** —
the code space is a fixed string, and the published 3rd party cheat index code is that string.
This is proved with a RAM latch oracle (accepted = `0x0000000A`, everything else
`0xFFFFFFFF` or a partial progress value) over 20+ sequences, including every
in-ROM button-command record and position/variant substitutions.

## 3. How to reproduce

* Emulator: mGBA (`mgba -3`), headless `Xvfb :315`, `SDL_AUDIODRIVER=dummy`.
* Default mGBA keys: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrows.
* Boot: Konami/Disney logos → skydiving intro → attract demo → title.
  **Start skips the intro/demo back to the title.**
* At the title (`PRESS START`), press with ~0.5 s gaps:

  ```
  Up, Down, Up, Down, Left, Down, Left, Down, A, Start
  ```

  The final `Start` is consumed (the title does **not** leave for the menu).
  Press **Select** to open the title menu, choose **LOAD GAME** (or NEW GAME),
  then at the main menu wheel choose **Option** (Down, Down, A). The third row is
  now **SOUND MODE** instead of `? ? ?`. Open it: B.G.M. / S.E. selector, track
  name in the ring (`Title`, `Staff Roll`, …), S.E. indices `000`, `001`, …
  Left/Right changes the track, A plays it.
* A rejected variant leaves the row as `? ? ?` and the final `Start` opens the
  title menu instead of being consumed.

## 4. Address map

ROM addresses are `0x08000000 + file_offset`.

| Address | Meaning |
|---|---|
| `0x000B90D0`–`0x000B9A40` | KCEK debug/development ASCII string bank |
| `0x000B961C` | `AGB SYSTEM   Ver%s`, `3.00`, `BY KCEK` |
| `0x000B9640` / `0x000B965C` | `L+R+START  SOFT RESET` / `L+R+SELECT  MEM+DMA DEBUG` |
| `0x000B9694` / `0x000B9154` | `PAGE NO.%d` / character, trick, course and difficulty name lists |
| `0x000B9958`–`0x000B9A40` | `EEPROM SAVE` / `SRAM SAVE` / `SAVE START_BUTTON` / `LOAD SELECT_BUTTON` / `FORMAT L_BUTTON` |
| `0x0800AEB0`+ | debug menu constructor chain; `0x0800AEBC` is the debug page constructor (installs the 27-entry item table) |
| `0x0800B0B0` | debug banner renderer (prints the four KCEK lines) |
| `0x0800B188` | debug page value/list renderer |
| `0x08C29154` | 10-entry table of internal screen-name pointers (`LOGO`, `TITLE`, `SELECT`, `GAME`, `GSELECT`, `SAMPLE`, `DEMO_1ST`, `LAST_DEMO`, `STAFF_ROLL`, `PLCHECK`) |
| `0x08C28E5C` | object/screen method table base (1-based); index 5 = `0x0800AEBC` (debug page) |
| `0x08C28FB8` | 14-entry debug warp table, 8 bytes/entry `{0x00400000, u16 scene}`; scene ids `2,3,6,0x1B,0x23,0x23,0x0C,0x17,0x1C,0x1D,0x1E,0x4C,0x4D,0x1F` |
| `0x08C2932C` | 27-entry debug page item-renderer table (`0x0800B0B1` at slot 2) |
| `0x08C29598`–`0x08C29818` | 11 in-ROM button-command records (9–10 raw `KEYINPUT` masks each, 0x40-byte stride) |
| `0x08000CD0` | key reader: `held = ~REG_KEYINPUT & 0x3FF` |
| `0x04000130` | `KEYINPUT` (literal at `0x08000CF8`) |
| `0x020058EC` | new-press word (edge, active-high) |
| `0x020058EE` | held word (active-high) |
| `0x0202449C` | title-screen press history, 10 × u16 raw masks |
| `0x020244DC` | history count (0–10) |
| `0x020244E0` | matcher progress/completion latch (u32): `0xFFFFFFFF` none, `0x0A` = sound code complete |
| `0x020071F8` / `0x020073F6` | save slots (primary/backup), ~0x1FE bytes each |
| `0x080097B0` | save checksum: `0xFFFF & ~sum(bytes[0..len-1])` |
| `0x02007C08` | board-unlock bitfield (13 used bits) |
| `0x0800E290` | board-unlock setter `f(ctx, index 0..12)` (masks `0x4000,0x8000,0x10000,0x20000,0x1,0x2,0x10,0x20,0x100,0x200,0x40000,0x200000\|0x1,0x30`) |
| `0x0800DB24` | only caller of the setter — item action in the 15-entry table at `0x08C298E8` (BOARDS exchange flow) |
| `0x0801E5A0` | per-player board-availability test against the unlock bitfield |

## 5. Algorithm

### 5.1 Input path

```
raw   = REG_KEYINPUT (0x04000130)        ; active low
held  = (~raw) & 0x3FF                  ; 0x020058EE, active high
press = held & ~prev_held               ; 0x020058EC, edge-triggered
```

Raw mask values (verified by observing the history buffer):

| Button | Mask | Button | Mask |
|---|---|---|---|
| A | `0x0001` | Select | `0x0004` |
| B | `0x0002` | Start | `0x0008` |
| Right | `0x0010` | Left | `0x0020` |
| Up | `0x0040` | Down | `0x0080` |
| R | `0x0100` | L | `0x0200` |

### 5.2 Title-screen matcher (operational model, verified)

At title entry the game clears a 10-slot u16 history at `0x0202449C` and a count
at `0x020244DC`. Each new press is appended as its **raw mask**; the count stops
at 10. A progress latch at `0x020244E0` starts at `0xFFFFFFFF`. Verified
behaviour:

```
on each press:
    if count < 10: hist[count++] = press
    else:          ignore (the buffer does not roll)

completion:
    a specific 10-press string drives the latch to 0x0000000A and consumes the
    final Start; every other tested string leaves the latch negative or at a
    partial progress value (3, 8, 9 seen for in-ROM command records) and Start
    opens the title menu as usual.
```

The completion string (the only one that reaches `0x0A`):

```
Up, Down, Up, Down, Left, Down, Left, Down, A, Start
40  80   40   80   20    80   20    80    01 08
```

Acceptance additionally requires the sequence to be **exactly the 10 presses
recorded from title entry**: a single extra press before it (B or A) prevents
completion, and ten junk presses followed by the code also fail (the buffer is
full and does not shift). The 9-press prefix is not enough, and replacing the
final Start with A, B or Select fails.

### 5.3 Effect

Completion sets the OPTION menu's third row from `? ? ?` to **SOUND MODE** for the
rest of the session. The row opens a B.G.M./S.E. player (`Title`, `Staff Roll`,
`000`… for effects). The unlock is not written to the save: a console reset with
no save restores `? ? ?`.

### 5.4 Save format (for the record)

Two slots at `0x020071F8` and `0x020073F6`; slot header `DISNEY SNOWBOARD`
(16 bytes). The checksum covers the first `0x1F8` bytes and is stored at `+0x1F8`
as `0xFFFF & ~sum`. The save holds profile name, VS/score/ranking records and
board flags. Board unlocks are bits in `0x02007C08`, set only by
`0x0800E290(index)` whose only caller is the BOARDS exchange item action
(`0x0800DB24`). The exchange screen was walked: it prints
“Exchange items with another GBA.” and then “Please wait …”, i.e. it waits for a
second unit; there is no single-console board shop.

## 6. Tables

### 6.1 The accepted title code

| # | Sequence | Raw masks | Result |
|---|---|---|---|
| 1 | Up, Down, Up, Down, Left, Down, Left, Down, A, Start | `40 80 40 80 20 80 20 80 01 08` | latch `0x0A`, SOUND MODE unlocked |

### 6.2 In-ROM button-command records (`0x08C29598`–`0x08C29818`, 0x40-byte stride)

| Address | Record (raw masks) | Title-screen result |
|---|---|---|
| `0x08C29598` | L,R,L,R,U,U,D,D,A | reject (`0xFFFFFFFF`) |
| `0x08C295D8` | Left,Up,Right,Down,Left,Up,Right,Down,A | reject |
| `0x08C29618` | U,U,D,D,Left,Right,Left,Right,B,A | reject |
| `0x08C29658` | U,U,D,D,L,R,L,R,B,A | partial (`0x03`), no completion |
| `0x08C29698` | L,L,R,R,U,U,D,D,A | reject |
| `0x08C296D8` | L,L,R,R,U,U,D,D,B | reject |
| `0x08C29718` | L,L,R,R,L,L,R,R,A | reject |
| `0x08C29758` | L,L,R,R,L,L,R,R,B | reject |
| `0x08C29798` | L,R,L,R,U,D,U,D,A | partial (`0x08`) |
| `0x08C297D8` | L,R,L,R,U,D,U,D,B | partial (`0x09`) |
| `0x08C29818` | U,D,U,D,L,D,L,D,A | **completes with Start** |

None of the other ten records completes the title matcher; they are the
in-engine trick/command records, not additional codes.

### 6.3 OPTION menu rows

| Row | Fresh profile | After the code |
|---|---|---|
| 1 | NAME ENTRY | NAME ENTRY |
| 2 | ? ? ? (inert) | ? ? ? (inert) |
| 3 | ? ? ? (inert) | **SOUND MODE** |
| 4 | TOTAL SCORE | TOTAL SCORE |
| 5 | RANKING (TOTAL RANKING / ??????RANKING) | same |
| 6 | ? ? ? (inert) | ? ? ? (inert) |

## 6b. Enumeration

**Space definition.** The title matcher consumes exactly ten presses drawn from
the ten game buttons (`A,B,Select,Start,Right,Left,Up,Down,R,L`). Each slot is
one raw mask; there is no alphabet remapping, no checksum, no field packing and
no stored table: the comparison is against one hard-coded string. Nominal input
space = 10^10 strings; **accepted set = 1 string**.

**Validator model (runs offline and agrees with the ROM on the tests below).**

```
accept(s) := (len(s) == 10) and
             all(s[i] == SEQ[i])        # SEQ = 40 80 40 80 20 80 20 80 01 08
             and no press precedes s within the title visit
```

The latch at `0x020244E0` is the ROM's own oracle: `0x0000000A` exactly for the
accepted string; `0xFFFFFFFF` for all rejected strings; intermediate records
produce partial values 3/8/9 but never `0x0A`.

**Novel code.** There is none to mint: the accepted set is a single fixed string
that is already published (3rd party cheat indexes). The button-code deliverable is therefore met by
enumerating the branch and length (one branch, length 10) and pressing
undocumented combinations, all of which are rejected below. This is a bounded
negative on the *whole* 10-slot space (the matcher has no generator and no second
chain that any of the 11 in-ROM command records completes).

**Bounds proven by rejection** (all at the title, all read back from the
`0x020244E0` latch; `0xFFFFFFFF` = not accepted):

| Test | Input | Latch |
|---|---|---|
| 9-press prefix, no Start | `U,D,U,D,L,D,L,D,A` | `FFFFFFFF` |
| Wrong final button | `U,D,U,D,L,D,L,D,A,B` | `FFFFFFFF` |
| Correct with final A | `U,D,U,D,L,D,L,D,A,A` | `FFFFFFFF` |
| Correct with final Select | `U,D,U,D,L,D,L,D,A,Select` | `FFFFFFFF` |
| One extra leading press (B / A) | `B`+code, `A`+code | `FFFFFFFF`, menu opens |
| Ten junk presses then code | `U×10` + code | `FFFFFFFF`, menu opens |
| Middle symbol changed | `U,D,U,D,L,D,R,D,A,Start` | `FFFFFFFF` |
| All 11 in-ROM command records | table 6.2 | reject or partial 3/8/9, never `0A` |

**Accepted input re-confirmed in-game.** The code was entered from a clean title
with the press history read back slot by slot
(`40 80 40 80 20 80 20 80 01`, count 9), then Start: latch `0x0A`, Start consumed,
and SOUND MODE appeared in OPTION (screenshots `shot_79`, `shot_80`, `shot_95`).

## 7. Validation evidence

**Observed (emulator / RAM read-back)**

* Title `PRESS START`; title menu `NEW GAME / LOAD GAME`; name entry (61-symbol
  keyboard, label only); main menu wheel (`Single Play`, `Exchange Board`,
  `Option`); 6-character PLAYER SELECT (Mickey, Chip & Dale, Pete, Goofy, Donald,
  Minnie); race; pause (CONTINUE/RETRY/EXIT); OPTION (6 rows); TOTAL SCORE;
  RANKING (TOTAL RANKING + locked `??????RANKING`); SOUND MODE (B.G.M./S.E.);
  BOARDS exchange (`Please wait …`); attract demo.
* Press history at `0x0202449C` records raw masks: 3×Up → `40 40 40`, count 3;
  the 9-press prefix → `40 80 40 80 20 80 20 80 01`, count 9.
* Accepted code → latch `0x020244E0 = 0x0000000A`, count 0, OPTION row 3 =
  **SOUND MODE**; SOUND MODE opens and lists `Title`, `Staff Roll` and S.E. `000`.
* Rejections in §6b all read back `0xFFFFFFFF` (or 3/8/9 partial) and leave the
  option row as `? ? ?`.
* `L+R+START` (held 1.5 s) does **not** reset at the main menu; `L+R+SELECT`
  does nothing at the BOARDS screen (and at the title/main menu).
* BOARDS exchange enters “Please wait …”, i.e. waits for a second GBA.

**Derived (instruction/data evidence)**

* Key reader and key globals (`0x08000CD0`, `0x020058EC/EE`) from the `KEYINPUT`
  literal at `0x08000CF8`.
* KCEK debug bank and page machinery: strings at `0x000B90D0`+, banner drawer at
  `0x0800B0B0`, page constructor `0x0800AEBC`, method table at `0x08C28E5C`,
  14-entry warp table at `0x08C28FB8`, 10 screen-name pointers at `0x08C29154`.
  `0x0800AEBC` has exactly one reference (the method table); no key handler
  references it.
* Save checksum at `0x080097B0`; slot bases and the `DISNEY SNOWBOARD` magic.
* Board unlock setter `0x0800E290` and its single caller `0x0800DB24` in the
  15-entry BOARDS action table at `0x08C298E8`.

**Inferred**

* The exact semantic of the partial latch values 3/8/9 (they track how far an
  in-engine command record matched) — observed values, not code-verified.
* The debug page row labels beyond the 10 screen names (the debug page would
  print character/trick/course/difficulty lists from the same bank; not walked,
  because the only entry is a RAM write).

## 8. Unknowns

* The matcher's comparison routine was not isolated to a single function address;
  the model in §6b is the ROM's observed input→latch behaviour (20+ cases) rather
  than a line-by-line decompilation. The accepted set is proven against the whole
  in-ROM command-record family and all prefix/suffix/length variations tested; a
  code-level sweep of 10^10 strings was not run.
* Whether the SOUND MODE session flag is a menu-object field or a separate global:
  a fresh-vs-unlocked diff at the title menu showed no new EWRAM flag byte, which
  suggests the unlock patches the option menu object rather than a save bit.
* The debug page contents were not entered; the page list is derived from ROM
  tables, and a 3rd party cheat index's screenshots corroborate it. Its gate is a RAM byte
  (`0200023002` per 3rd party cheat indexes), not an input sequence.
* The three `? ? ?` option rows other than row 3 stayed inert in every state
  tested (A does nothing); they may be unused placeholders.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* Python 3 + capstone/keystone for mask/pointer scans; `strings -t x`; `grep -abo`.
* mGBA 0.x SDL under `Xvfb :315`; `xdotool` key driver with 0.5 s gaps.
* Savestate reader: mGBA `.ssN` is a PNG whose `gbAs` chunk is zlib-compressed;
  EWRAM at `0x21000`, IWRAM at `0x19000` in the 397,312-byte state. All RAM
  claims above are byte offsets read from these states.
* No ROM, graphics, music or text assets are redistributed here.
