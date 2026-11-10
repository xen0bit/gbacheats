# Charlie and the Chocolate Factory (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Charlie and the Chocolate Factory/Charlie and the Chocolate Factory.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title | `CHARLIE AND` (12 bytes, NUL padded) |
| Game code | `BCFE` |
| Maker code | `54` |
| Software version | `0` |
| Entry branch | `0xEA00002E` → `0x080000C0` (ARM crt0) |
| Header checksum | stored `0x0000`, computed `0x00ED`; complement byte `0xED` (normal rebuilt-header artifact) |
| MD5 | `5ea39a20a2afb038555f013142a2a97a` |
| SHA-1 | `c85c9015d56530d0ffcefe6e3a21aa9a011da8a0` |
| SHA-256 | `908aa26aa73dfd4ea08961758168d1f2dd91d89fbf90ed9cc84a6ae056f634e3` |

### Embedded GBA-header scan

Scanning the whole file for the 156-byte Nintendo logo (present at header+4) finds **two**
headers:

| File offset | ROM address | Title | Game code | Maker | Entry |
|---|---|---|---|---|---|
| `0x000000` | `0x08000000` | `CHARLIE AND` | `BCFE` | `54` | `0xEA00002E` |
| `0x774000` | `0x08774000` | `TIGERWOODS04` | `BTWE` | `69` | `0xEA00002F` |

The boot entry is the first header (the Charlie crt0 at `0x080000C0`), so the cartridge boots
Charlie. The second header is an embedded stub: its crt0 at `0x087740C4` is a real ARM crt0 and
its literal main pointer at `0x08774144` is `0x08774299`, but `0x08774298` is `bx lr` (empty
main). The region after `0x08774000` is not dead: it contains a large Charlie-themed
demo/prototype text bank (`Debug`, `Access Debug Features`, `In-game debug data`, `Skeleton Key`,
`Scroller Demo`, `Platformer`, `Game Demo`, `Game Credits`, `Select Language`, plus the in-game
Oompa-Loompa tutorial text at `0x08796570+`). Pointers to those strings exist only inside the
`0x08774000+` region (e.g. `0x087909A4 → 0x08795F00`), and a raw BL scan finds **no** real BL
from the Charlie half into the stub (the 110 raw hits are data false positives; the call sites
disassemble as garbage). The second header is therefore an embedded, non-bootable demo/prototype
image with a mismatched Tiger Woods header — not a trainer and not a second playable game. It is
reported here as an artifact of this specific dump.

No cracktro, no appended trainer menu, and no patched entry branch were found.

## 2. Executive summary

The game has **one developer-intended in-game cheat**: a 6-button code entered on the
mode-select screen ("select game menu"):

```
Left, Right, L, R, Start, Select
```

The code is matched by a purpose-built validator at `0x0803C664` against a 6-entry mask table at
`0x0875E654`. On success it plays sound `0x208` and sets the byte flag at `0x0200087C`. The flag
is the gate for the two "press Select to unlock" actions documented in the published cheats:

* **Unlock all levels** — level-select screen ORs `0x00007FFF` into the per-save level bitfield.
* **Unlock all mini-games** — mini-game screen ORs `0x0000001F` into the mini-game bitfield.

There is **no password system** and **no other button-code table** in the Charlie half. The
published GameFAQs / Project Cheat Codes / GameGenie code is byte-for-byte the ROM table.

The cheat was confirmed dynamically with the mGBA debugger by invoking the ROM's own validator
with the real button masks: the correct sequence drives the internal index to 6 and sets
`0x0200087C = 1`; a swapped prefix, a 5-press truncation and a wrong final button all leave the
flag at 0. An unpublished subsequence variant (`Left, Up, Right, Down, L, R, Start, Select`) also
reaches index 6 and sets the flag, proving the matcher is a subsequence matcher (extra presses are
ignored, the index is not reset on a wrong press).

The main game contains **no reachable debug menu**. The only debug-menu strings
(`Debug`, `Access Debug Features`, `In-game debug data`, `Skeleton Key`, `Access Locked Items`)
live in the embedded non-bootable demo image at `0x08774000+` and are not referenced by the
Charlie half.

## 3. How to reproduce

Environment: mGBA 0.10.5 (`mgba-sdl`), Xvfb `:241`, `SDL_AUDIODRIVER=dummy`, openbox.
Keymap verified by reading `~KEYINPUT` (`0x02002710`) from a savestate for every key:

| GBA | Key | `~KEYINPUT` |
|---|---|---|
| A | `x` | `0xFC01` |
| B | `z` | `0xFC02` |
| Select | `BackSpace` | `0xFC04` |
| Start | `Return` | `0xFC08` |
| Right | `Right` | `0xFC10` |
| Left | `Left` | `0xFC20` |
| Up | `Up` | `0xFC40` |
| Down | `Down` | `0xFC80` |
| R | `s` | `0xFD00` |
| L | `a` | `0xFE00` |

Menu path for the published cheat:

1. Boot the game; wait out the intro logos.
2. At the mode-select screen (`ADVENTURE` / `MINI-GAMES` / `OOMPA-LOOMPA ALBUM`) press
   `Left, Right, L, R, Start, Select`. A sound confirms.
3. Highlight `ADVENTURE` and press `A` → level select; press `Select` → all levels unlocked.
4. Back out, highlight `MINI-GAMES` and press `A` → mini-game screen; press `Select` → all
   mini-games unlocked.

Dynamic proof method used for this report (no screenshots; text/RAM only): the mGBA debugger
(`mgba -d`) was driven through a pty. The ROM's own validator was invoked directly with the
running CPU in Thumb mode and the real active-high key-state variable `0x02000AC8` written with
each button mask; the returned index and the flag at `0x0200087C` were read back. Savestate RAM
diffs (`gbAs` chunk, EWRAM at state offset `0x21000`) were used to confirm the RAM map.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x080000C0` | ARM crt0 (entry) |
| `0x08000374` | `main` |
| `0x08000528` | main loop / screen dispatcher |
| `0x08000914` | level-select screen handler (ADVENTURE) |
| `0x08000BD2` | level-select "Select + cheat flag" unlock (OR `0x7FFF`) |
| `0x08000E60` | mode-select screen ("select game menu") |
| `0x08001172` | mini-game "Select + cheat flag" unlock (OR `0x1F`) |
| `0x0800495E` | third "Select + cheat flag" handler (flag > 1 gate) |
| `0x0803C664` | **cheat-code validator** |
| `0x0875E654` | **6-entry button-mask table** |
| `0x08004068` | key-state update (writes `0x02000AC8` and `0x02002710`) |
| `0x08034EB8` | sound player (sound `0x208` = cheat confirmed) |
| `0x02000AC8` | key state, rising edge, active-high (`~KEYINPUT & ~previous`) |
| `0x02002710` | `~KEYINPUT` (all buttons, active-high) |
| `0x0200087C` | **cheat flag** (0 = normal, 1 = cheat mode) |
| `0x020021FC` | current screen id (general dispatcher) |
| `0x08774000` | embedded second GBA header (Tiger Woods stub / Charlie demo text) |
| `0x08795F00` | `Debug` / `Access Debug Features` strings (demo image only) |

## 5. Algorithm

### 5.1 Key state

`0x08004068` runs once per frame:

```
v   = ~KEYINPUT                      ; 16-bit, active-high
0x02002710 = v
0x02000AC8 = v & ~previous_v         ; rising edge only
previous_v = v
```

So `0x02000AC8` is a one-frame, active-high "button pressed this frame" word.

### 5.2 Validator (`0x0803C664`, Thumb)

```
index = r0                             ; carried in r0 across frames
if key_state == 0: return index
if index > 5:
    flag = 1                           ; 0x0200087C
    return index
if (mask[index] & key_state) == 0:     ; any matching bit counts
    return index                       ; NO reset on a wrong press
index += 1
if index <= 5: return index
if flag == 0: play_sound(0x208)
flag = 1                               ; 0x0200087C
return index
```

`mask` is the u16 table at `0x0875E654`:

| index | mask | button |
|---:|---:|---|
| 0 | `0x0020` | Left |
| 1 | `0x0010` | Right |
| 2 | `0x0200` | L |
| 3 | `0x0100` | R |
| 4 | `0x0008` | Start |
| 5 | `0x0004` | Select |

Properties proven by the code and by the dynamic tests:

* The match is `mask[i] & key_state`, not equality; the masks are single bits, so it is a
  "this button was pressed" test.
* A press that does not match the current mask leaves the index unchanged (no reset).
* The index is only reset by the screen that owns it (the mode select initialises it to 0 at
  `0x08000E88`).
* The success branch is reached only when the index becomes 6.

### 5.3 Unlock actions

Both are gated on `Select` **and** the flag at `0x0200087C`:

* Level select (`0x08000BD2`): `level_bits |= 0x00007FFF` at `<save record>+0x1C`.
* Mini-games (`0x08001172`): `minigame_bits |= 0x0000001F` at `<record>+0x20`.
* A third handler at `0x0800495E` requires `flag > 1` (a second, unused flag value).

## 6. Tables

### 6.1 Button-mask table (`0x0875E654`, u16 LE)

```
0x0020, 0x0010, 0x0200, 0x0100, 0x0008, 0x0004
```

### 6.2 Published code cross-check

| Source | Published code | ROM table match |
|---|---|---|
| GameFAQs (Cloud20390) | Left, Right, L, R, Start, Select | exact |
| Project Cheat Codes | dpadLeft, dpadRight, bttnL, bttnR, bttnStart, bttnSelect | exact |
| GameGenie.com | Left, Right, L, R, Start, Select | exact |

The follow-up actions ("highlight ADVENTURE + Select", "highlight MINI-GAMES + Select") match
the two flag-gated Select handlers above.

### 6.3 Flag / state

| Address | Meaning |
|---|---|
| `0x0200087C` | cheat flag; 0 = normal, 1 = cheat mode. Written only by the validator (`0x0803C6B0`) and cleared once at init (`0x080004C0`). |

## 6b. Enumeration

### Space definition

The system is a **fixed 6-press sequence**, not a code space:

* sequence length: exactly 6 presses (the table has 6 entries; the validator's success branch is
  only reachable at index 6);
* alphabet: the 10 GBA buttons, but each position accepts exactly one button;
* matching: subsequence semantics — extra non-matching presses between the required presses are
  ignored, and the index is not reset by a wrong press;
* action: one action (set `0x0200087C = 1`); the flag then gates two Select actions in two
  sub-screens.

Representable inputs that set the flag: any press stream that contains the six required buttons in
order, with arbitrary extra presses interleaved. The minimal representatives are the 6! = 720
orderings, of which the ROM accepts exactly the published one (the table order); the accepted set
is therefore "all supersequences of `Left,Right,L,R,Start,Select`".

### Novel (unpublished) code — generated and confirmed

**`Left, Up, Right, Down, L, R, Start, Select`**

This is not on GameFAQs, Project Cheat Codes, GameGenie, VGChartz or TCRF (those list only the
6-press code). It exercises the undocumented subsequence property of the matcher.

Dynamic proof (mGBA debugger, invoking the ROM validator with the real key-state variable):

```
Left,Right,L,R,Start,Select                          -> index 6, flag 0x00000001
Left,Up,Right,Down,L,R,Start,Select                  -> index 6, flag 0x00000001
```

### Bounds proven by rejection (dynamic)

| Input | Final index | Flag | Result |
|---|---:|---:|---|
| `Right,Left,L,R,Start,Select` (swapped prefix) | 1 | `0x00000000` | rejected |
| `Left,Right,L,R,Start` (5 presses) | 5 | `0x00000000` | rejected |
| `Left,Right,L,R,Start,A` (wrong final button) | 5 | `0x00000000` | rejected |
| `Left,Up,Right,Down,L,R,Start,Select` (extra presses) | 6 | `0x00000001` | accepted |

The rejection cases prove the sequence length is exactly 6 and the final button must be Select;
the acceptance of the extra-press variant proves the index is not reset by non-matching presses.

### Action-branch enumeration

* Mode select (`0x08000E60`): Up/Down change the selection (0..2); `A`/`A+Start` activate;
  `B` returns (sets selection −1). Only one cheat branch exists (the validator), and it has
  exactly one action (set the flag).
* Level select: `Select` + flag → OR `0x7FFF` (all 15 level bits).
* Mini-games: `Select` + flag → OR `0x1F` (all 5 mini-game bits).
* Third handler (`0x0800495E`): requires `flag > 1`; no input path sets the flag to a value
  other than 1, so this branch is unreachable (dead).

## 7. Validation evidence

| Claim | Evidence | Type |
|---|---|---|
| Header / hashes / two GBA headers | `xxd`, `md5sum`, `sha1sum`, `sha256sum`, logo scan | Observed |
| Keymap | `~KEYINPUT` read from savestates for all 10 buttons | Observed |
| Mask table at `0x0875E654` | byte search for the u16 sequence; unique hit | Observed |
| Validator logic | disassembly of `0x0803C664` (Capstone/objdump) | Derived |
| Correct sequence sets the flag | debugger-invoked validator, index 6, `0x0200087C = 1` | Observed |
| Extra-press variant sets the flag | debugger-invoked validator, index 6, `0x0200087C = 1` | Observed |
| Swapped / short / wrong-final sequences do not set the flag | debugger-invoked validator, flag `0` | Observed |
| Level unlock ORs `0x7FFF` | disassembly of `0x08000BD2` | Derived |
| Mini-game unlock ORs `0x1F` | disassembly of `0x08001172` | Derived |
| Debug strings exist only in the embedded demo image | pointer scan (`0x087909A4` etc.), BL scan | Derived |
| No password system | `strings` keyword scan; no input field consumer | Derived |

## 8. Unknowns

* The **dynamic unlock effects** (level bitfield `|= 0x7FFF`, mini-game bitfield `|= 0x1F`) were
  verified by disassembly only; the mode-select/level-select screens could not be reached in this
  emulator session (the game sits in its intro-logo loop and the main-loop breakpoint at
  `0x08000528` was never reached), so the on-screen "Select unlocks everything" was not
  re-observed end to end. The flag itself was set and read dynamically.
* The exact semantics of the third flag reader at `0x0800495E` (requires `flag > 1`).
* The embedded `0x08774000` demo image: whether it is a leftover prototype, a multiboot stub, or
  a mis-headered second build. Its main is `bx lr`, so it is not bootable as-is.
* The level-select record base/stride and the save-slot index (`sl`, `r8`, `sb`) were not
  resolved to absolute RAM addresses.

## 9. Tooling

* `xxd`, `strings -t x`, `grep`, `md5sum`, `sha1sum`, `sha256sum`, `file`
* `arm-none-eabi-objdump` (`-M force-thumb` / `-M force-arm`) and Python + Capstone 5.0.7 for
  raw Thumb scanning (LDR-literal scan, BL scan, mask-run scan)
* mGBA 0.10.5 (`mgba-sdl`) under `Xvfb :241` + openbox, `SDL_AUDIODRIVER=dummy`
* mGBA command-line debugger (`mgba -d`) driven through a Python `pty` (register writes
  `w/r`, memory writes `w/4`, `trace`, `r/4`)
* mGBA savestates (`.ss1`): PNG `gbAs` chunk, zlib-decompressed; EWRAM at state offset `0x21000`,
  IWRAM at `0x19000`, VRAM at `0x1000` (used to confirm `~KEYINPUT` and the flag address)
* Scripts (in `/tmp/opencode/charlie/`): `phase0.py`, `ssread.py`, `drive2*.py`

Legal note: no ROM, asset or copyrighted data is redistributed; only addresses, algorithms,
hashes and the developer's own button sequence are published.
