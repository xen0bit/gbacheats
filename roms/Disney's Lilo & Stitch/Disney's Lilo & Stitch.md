# Disney's Lilo & Stitch (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney's Lilo & Stitch/Disney's Lilo & Stitch.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title | `LILO AND STI` (12-byte field, space-padded) |
| Game code | `ALTE` |
| Maker code | `4Q` |
| Version | `0x00` |
| Fixed `0xB2` | `0x96` |
| Complement (`0xBD`) | `0x73` (matches the computed complement) |
| Header checksum (`0xBE`) | `0x0000` (computed value would be `0x73`) |
| MD5 | `cb10fdb5b2574626ee062a60482052f6` |
| SHA-1 | `4d652556004c7cb4110e362b2cd8e45b2cbb7ca7` |
| SHA-256 | `6e634f03fcf4907e6e7bca33ebc6f5c7d736b3d4c3f6aea6b83cff18df776014` |

Embedded-header scan: the 156-byte Nintendo logo occurs **once**, at file offset `0x04`
(header base `0x0`), so this is a single GBA image, not a multi-game pack.

### 1.1 The supplied image is a MODE7 release (patch, not a trainer)

The file is not the stock image:

* Entry word at `0x00` is `0xEA1FE5FE`, i.e. ARM `b 0x087F9800`, not the stock
  `b 0x080000C0` (`0xEA00002E`).
* `0x087F9800` is a small ARM→Thumb thunk (`ldr sp,=0x03007F00`, `bx`) feeding a
  custom decompressor at `0x087F980C` that takes a `0x3A83`-byte source block
  at `0x087F992C`, writes the expanded code to `0x02000000`, and jumps to
  `0x02000001`.
* The appended block contains the intro text `MODE7 PRESENTS`, `06/05/2002`,
  `GBA/USA/64MBS`, `SUPPLIED BY: TU-WHITT TU-WHO` at file offsets
  `0x7FD2FA`–`0x7FD3A9`.
* The block sits in the cartridge tail: the last non-`0xFF` game byte before it
  is `0x7F961F`, and the loader begins at `0x7F9800`. No game data appears to be
  overwritten; the entry word is the only on-disk change (3 differing bytes,
  because the top byte `0xEA` is shared).
* It is a **cracktro/boot intro only** — no trainer menu, no cheat options, no
  extra lives prompt. It is reported separately and is not an in-game cheat.

The header checksum field was zeroed by the release tooling while the complement
byte is still consistent; the computed header checksum is `0x73`.

For analysis and emulation the entry was restored to the stock branch on a copy
(`0x00`–`0x02` = `2E 00 00`, byte `0x03` already `0xEA`). The only difference
between the supplied file and the working copy is those 3 bytes; the working
copy is MD5 `703c5e0aa4930f99d04ff101e62ca3b1` /
SHA-256 `4be299071db38aa0c272588b11677c85e4af3330666d798bb27620a91f2e926a`.

No EEPROM/SRAM/Flash save-library signature is present and no save data is
produced (`game.sav` stays 0 bytes). The 7-icon password screen is this game's
persistence mechanism; unlocks observed below are session state.

## 2. Executive summary

The game has exactly one developer-intended code surface: a **7-slot icon
password screen** (icons: Stitch, Lilo, Scrump, Gun, UFO, Flower, Rocket,
Pineapple). Each slot is a 3-bit value; the 21 bits are bit-sliced into four
fields plus a 4-bit checksum:

```
lives  = 3 bits (stored as lives-1, 1..8)
f6     = 3 bits (stored as f6-1; no gameplay consumer found)
mode   = 3 bits (selects the level/start handler and a scene selector)
flags  = 8 bits (progress bitmask; gates the PICTURES menu, any non-zero value)
chk    = 4 bits = ~(lives+f6+mode+flags) & 0xF
```

The accepted set is **131,073 of the 2,097,152 possible 7-icon strings**:
131,072 checksum-valid payloads plus the special all-Stitch string (sum of the
seven icon values == 0), which is accepted without a checksum and does not write
the state globals.

The 11 published GBA passwords were taken from the public lists and decoded
against the ROM; 10 pass the checksum and the 11th is the all-Stitch special
case. Four were entered and verified in the emulator. A code absent from every published list was generated, entered,
and confirmed by RAM and on-screen HUD (`Flower, Lilo, Lilo, Scrump, UFO, UFO,
Stitch` starts the Mothership with **8 lives**). A one-icon modification of it
was rejected in-game (`INCORRECT`), proving the checksum layer.

A second in-game cheat was found and verified: on the main menu, **hold R +
Select and press A on START GAME** — the start routine sets lives to 99.

No hidden/debug menu, no separate level-select screen, and no additional menu
entries exist: the main menu has exactly 5 entries (RAM count) and the code
paths that build them have exactly 5 handlers. The password screen itself is the
developer's level/stage shortcut.

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb `:329`, `SDL_AUDIODRIVER=dummy`, 3× scale.
Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys. Keys must be held ≥60 ms.

Use a copy with the stock entry restored:

```
python3 - <<'EOF'
d=bytearray(open("Disney's Lilo & Stitch.gba","rb").read())
d[0:4]=(0xEA00002E).to_bytes(4,'little')   # b 0x080000C0
open("game.gba","wb").write(d)
EOF
DISPLAY=:329 SDL_AUDIODRIVER=dummy mgba -3 game.gba
```

Paths:

* **Password screen:** title → START → main menu → DOWN, DOWN, A.
  LEFT/RIGHT selects the slot, UP/DOWN changes the icon (wraps 0↔7),
  A or START submits, B cancels.
* **After ACCEPTED** the game returns to the main menu and the menu cursor
  becomes the sub-screen's return value. The password screen returns 1, so the
  cursor lands on OPTIONS. Press **UP once** (to START GAME) and A to start with
  the loaded state. (The all-Stitch special case returns 1 but leaves the state
  globals unchanged — at their defaults on a fresh boot — so it starts the
  Beach level.)
* **99 lives:** at the main menu, hold R (`s`) + Select (`BackSpace`), press A
  on START GAME, and keep both held until the level's start routine runs
  (~1–2 s). Lives become 99.
* **Movies:** main menu → DOWN×3, A. Entries are coloured by the game-state
  bits; locked entries play an error sound.
* **Pictures:** main menu → DOWN×4, A. Only reachable when `flags != 0`;
  8 pictures, wrapping 1→8→1.
* **Pause:** START during play. CONTINUE / QUIT; QUIT asks ARE YOU SURE? YES/NO.
  A decorative 7-icon strip is drawn but is not editable (LEFT/RIGHT/UP/DOWN
  do not change it).

## 4. Address map

File offset = address − `0x08000000`.

| Address | Meaning |
|---|---|
| `0x08000000` | Entry (patched to `b 0x087F9800` in the supplied image) |
| `0x080000C0` | Stock crt0; main pointer `0x080015F1` in its literal pool |
| `0x080015F0` | New-game/start init: defaults lives=3 (`0x02001140`), f6=3 (`0x02000A48`), mode=0, flags=0, state=1, selector=0 |
| `0x08001660` | Outer menu/start loop (calls main menu, then applies the 99-lives check) |
| `0x08001686` | **99-lives button check** (read `KEYINPUT` `0x04000130`, mask `0x104`) |
| `0x0800171C` | Level-start dispatch table, 8 entries (mode 0..7) |
| `0x08001E9C` | **Encoder**: globals → 7 icon bytes (inverse of the decoder) |
| `0x08001FB0` | **Decoder/validator**: 7 icon bytes → fields + checksum test |
| `0x080020EC` | Password-mode handler table, 7 entries (mode 0..6); mode 7 falls through at `0x08002188` |
| `0x08010E70` | Password screen UI wrapper: sums the 7 bytes, special-cases sum 0, calls decoder, draws ACCEPTED/INCORRECT, sets `0x0200D668` |
| `0x08010F28` | Password screen loop; 7-byte buffer at `SP+0xC` (during the screen it lives at `0x03007D70`) |
| `0x08011378` | OPTIONS screen (MUSIC/SOUND) |
| `0x08011540` | Main menu (5 entries, cursor is local `r6`) |
| `0x08011624` | Main-menu A-dispatch table, 5 entries |
| `0x0801111C` | MOVIES screen (4 entries, gated by state bits) |
| `0x08011694` | PICTURES menu item; checks `flags != 0`, then calls `0x08011BC0` |
| `0x08011BC0` | Picture gallery (8 pictures) |

RAM (EWRAM unless noted):

| Address | Meaning |
|---|---|
| `0x02001140` | lives (1..8; 99 after the button cheat) |
| `0x02000A48` | f6 field (stored f6-1) |
| `0x02000A4C` | mode (0..7) |
| `0x02001144` | flags (8-bit progress bitmask) |
| `0x02000E70` | game state (1/3/7; 15 after all-unlock) |
| `0x02006154` | scene selector written by the password handler (0,4,5,6,10,11,12) |
| `0x0200D668` | "a normal password was accepted" flag (0 → START GAME re-runs defaults) |
| `0x02007098` | canonical 7-byte code buffer produced by the encoder |
| `0x0200D660` | main-menu last index (4 → 5 entries) |
| `0x02000A50` | MUSIC on/off |
| `0x02000A40` | SOUND on/off |
| `0x03007D70` | password buffer while the password screen is active |

mGBA savestate (`.ss*`) layout used for the RAM proofs: PNG `gbAs` chunk →
zlib → 397,312-byte state; IWRAM at state offset `0x19000`, EWRAM at `0x21000`,
and the raw `KEYINPUT` register at state offset `0x530`.

## 5. Algorithm

### 5.1 Decoder (`0x08001FB0`)

Input: pointer to 7 bytes, each in `0..7` (the icon index on screen).

```
lives = (b0 & 1) | ((b1 & 1) << 1) | ((b2 & 1) << 2)
f6    = ((b0 >> 1) & 1) | (((b1 >> 1) & 1) << 1) | (((b2 >> 1) & 1) << 2)
mode  = ((b0 >> 2) & 1) | (((b1 >> 2) & 1) << 1) | (((b2 >> 2) & 1) << 2)

flags = ((b3 >> 1) & 1) | (((b4 >> 1) & 1) << 1) | (((b5 >> 1) & 1) << 2)
      | ((b3 & 1) << 3) | ((b4 & 1) << 4) | ((b5 & 1) << 5)
      | ((b6 & 1) << 6) | (((b6 >> 1) & 1) << 7)

chk   = ((b3 >> 2) & 1) | (((b4 >> 2) & 1) << 1)
      | (((b5 >> 2) & 1) << 2) | (((b6 >> 2) & 1) << 3)

if chk != (0xF & ~(lives + f6 + mode + flags)):
        return 0                                  # INCORRECT
```

On success the decoder writes:

```
[0x02001140] = lives + 1
[0x02000A48] = f6 + 1
[0x02000A4C] = mode
[0x02001144] = flags
state, selector = MODE_TABLE[mode]
[0x02000E70] = state
[0x02006154] = selector          (mode 7 leaves the selector alone)
if flags == 0xFF: state |= 8
```

The checksum is computed over the **stored** values (`lives-1`, `f6-1`, `mode`,
`flags`) in an 8-bit accumulator (the ROM truncates the running sum each
iteration; only the low nibble is used), then the low nibble of the complement.

Wrapper (`0x08010E70`):

* `sum = Σ b[i]` (mod 256). If `sum == 0` (only the all-Stitch string), it
  returns ACCEPT **without** calling the decoder and sets `0x0200D668 = 0`.
  No state globals are written. This is the published "Beach" code.
* Otherwise it calls the decoder. On success it encodes the canonical code into
  `0x02007098` (`0x08001E9C`) and sets `0x0200D668 = 1`.
* The return value (1/0) is shown as ACCEPTED!/INCORRECT.

### 5.2 Encoder (`0x08001E9C`)

Exact inverse of 5.1: reads `lives`, `f6`, `mode`, `flags` from the globals,
computes the same 4-bit check, and writes the 7 icon bytes. It is called by the
password screen after a successful decode and by three other UI routines
(`0x08011E64`, `0x08012180`, `0x08012400`), i.e. the game itself can mint codes.

### 5.3 Entry states / level selection

The decoder's mode handler table (`0x080020EC`) writes:

| mode | state `0x02000E70` | selector `0x02006154` | level-start handler (`0x0800171C`) |
|---:|---:|---:|---|
| 0 | 1 | 0 | `0x0800173C` (Beach) |
| 1 | 3 | 4 | `0x08001818` (Mothership — observed) |
| 2 | 3 | 5 | `0x08001890` (Space Cruiser, from published label) |
| 3 | 3 | 6 | `0x080018F8` (Junkyard, from published label) |
| 4 | 7 | 10 | `0x080019D4` (Escape, from published label) |
| 5 | 7 | 11 | `0x08001A68` (Rescue, from published label) |
| 6 | 7 | 12 | `0x08001AEC` (Final Challenge, from published label) |
| 7 | 7 | unchanged | `0x08001BEC` (runs the credits text routine `0x08001504`) |

`flags == 0xFF` ORs 8 into the state. State bits 0..3 gate MOVIES 1..4
(`0x0801111C` tests `state & 1/2/4/8`). Observed: state 3 → movies 1–2 coloured;
state 15 → all four coloured.

### 5.4 99-lives button code (`0x08001686`)

This runs in the outer start loop immediately after the main menu returns:

```
08001686  ldr r0,=0x04000130     ; KEYINPUT (active low)
08001688  ldrh r1,[r0]
0800168A  movs r0,#0x82
0800168C  lsls r0,r0,#1          ; r0 = 0x104 = R(0x100) | Select(0x4)
0800168E  ands r0,r1
08001690  cmp  r0,#0
08001692  bne  0x0800169A       ; either not held -> skip
08001694  ldr r1,=0x02001140    ; lives
08001696  movs r0,#0x63         ; 99
08001698  str r0,[r1]
```

Because it runs when the start routine begins, both keys must be held through
the menu→game transition.

## 6. Tables

### 6.1 Icon alphabet (observed by cycling slot 1)

| Value | Icon | Value | Icon |
|---:|---|---:|---|
| 0 | Stitch | 4 | UFO |
| 1 | Lilo | 5 | Flower |
| 2 | Scrump | 6 | Rocket |
| 3 | Gun | 7 | Pineapple |

UP decrements and DOWN increments; both wrap (7→0, 0→7). The alphabet is
exactly 8 symbols, so no 9th value is representable from the UI.

### 6.2 Published codes decoded against the ROM

| Published name | Icon sequence | lives | f6 | mode | flags | chk | result |
|---|---|---:|---:|---:|---:|---:|---|
| Beach | Stitch ×7 | 1 | 1 | 0 | 0x00 | (0) | **special accept** (sum 0) |
| Credits | Pineapple×4, Stitch×3 | 8 | 8 | 7 | 0x09 | 1 | accept |
| Escape | Stitch,Scrump,UFO,Gun,Rocket,Scrump,UFO | 1 | 3 | 4 | 0x0F | 10 | accept |
| Final Challenge (powerups) | Stitch,Rocket,Flower,Gun,Gun,Pineapple,Stitch | 5 | 3 | 6 | 0x3F | 4 | accept |
| Final Challenge (no powerups) | Lilo,Pineapple,Flower,Pineapple,Gun,Gun,Stitch | 8 | 3 | 6 | 0x3F | 1 | accept |
| Junkyard Planet | UFO,Rocket,Stitch,Rocket,Rocket,Scrump,Stitch | 1 | 3 | 3 | 0x07 | 3 | accept |
| Mothership | UFO,Scrump,Stitch,Rocket,UFO,Stitch,UFO | 1 | 3 | 1 | 0x01 | 11 | accept |
| Rescue | Flower,Scrump,UFO,Gun,Gun,Gun,UFO | 2 | 3 | 5 | 0x3F | 8 | accept |
| Space Cruiser | Lilo,Rocket,Stitch,Rocket,Rocket,Scrump,Stitch | 2 | 3 | 2 | 0x07 | 3 | accept |
| Level 1 + 8 lives | Lilo ×7 | 8 | 1 | 0 | 0x78 | 0 | accept |
| Unlock All | Flower,Rocket,UFO,Gun,Pineapple,Pineapple,Gun | 2 | 3 | 7 | 0xFF | 6 | accept |

The published button code "hold R + Select, press A on Start Game" is the
`0x08001686` snippet in 5.4.

## 6b. Enumeration

**Space definition.** 7 slots × 8 symbols = **2,097,152** input strings = 2^21
(because each slot is a full 3-bit field). There are no unused input bits and no
reserved symbols: every one of the 2^21 strings is *expressible* on the screen.

**Field widths.** `lives` 3, `f6` 3, `mode` 3, `flags` 8, `chk` 4 = 21 bits.
The checksum is derived from the other 17 bits, so exactly **2^17 = 131,072**
strings pass the checksum, plus the one all-Stitch string accepted by the
special case: **131,073 accepted strings**.

**Aliases.** `flags` bits 4..7 enter the checksum only as multiples of 16, so
they do not change the check nibble; for any fixed low nibble there are 16
spellings that pass. `f6` is written to `0x02000A48` and has **no gameplay
reader** — the only read is the encoder at `0x08001EB8` — so its 8 values are
behaviourally identical during play (`8` aliases per behaviour).

**Novel codes generated (absent from GameFAQs / Fandom / IGN lists).**

| # | Icon sequence | Bytes | Fields | Result |
|---|---|---|---|---|
| N1 | Flower, Lilo, Lilo, Scrump, UFO, UFO, Stitch | `05 01 01 02 04 04 00` | lives=8, f6=1, mode=1, flags=0x01, chk=6 | **ACCEPTED** |
| N2 | Flower, Lilo, Lilo, Scrump, UFO, UFO, Scrump | `05 01 01 02 04 04 02` | lives=8, f6=1, mode=1, flags=0x81, chk=6 | **ACCEPTED** (alias family) |
| R1 | Flower, Lilo, Lilo, Gun, UFO, UFO, Scrump | `05 01 01 03 04 04 02` | lives=8, f6=1, mode=1, flags=0x89, stored chk=6 vs expected 14 | **INCORRECT** |

**In-game proof (N1).** Entered on the real password screen; the buffer read
back from the savestate at `0x03007D70` was `05 01 01 02 04 04 00`, and the
screen showed `ACCEPTED!`. RAM after acceptance:
`lives=8 @0x02001140`, `f6=1 @0x02000A48`, `mode=1 @0x02000A4C`,
`flags=1 @0x02001144`, `state=3 @0x02000E70`, `selector=4 @0x02006154`.
START GAME then played the Mothership opening cutscene ("UH OH! WHERE AM I? …
BUT IT FEELS WRONG.") and the HUD showed **x8** lives. This is an unadvertised
combination: the published Mothership code gives 1 life and f6=3.

**In-game proof (published, for anchor).**
* All-Stitch (Beach): accepted; starts the Beach level with the default 3 lives
  (`state=1, selector=0, lives=3, mode=0, flags=0`).
* Mothership: accepted; RAM identical to N1 except lives=1/f6=3.
* Lilo ×7: accepted; RAM `lives=8, f6=1, mode=0, flags=0x78, state=1`; HUD x8.
* Unlock All: accepted; RAM `state=15, flags=0xFF, mode=7, lives=2`; plays the
  credits sequence, then returns to the menu with all four MOVIE entries
  coloured and PICTURES reachable (8 pictures, 1..8 wrap).

**Bounds proven by rejection.**
* R1 has every field in range but a wrong checksum → in-game `INCORRECT`
  (buffer `05 01 01 03 04 04 02` read from `0x03007D70` immediately before
  submission). R1 differs from N1 in slot 4 (Scrump→Gun), which flips a
  low-nibble flag bit and therefore the check, and in slot 7 (Stitch→Scrump),
  which only sets a high flag bit. The rejection is therefore the checksum
  layer, not an out-of-range field.
* A second accidental checksum failure (`00 02 00 06 04 00 04`, caused by a
  dropped first input) also showed INCORRECT with the buffer read from RAM,
  confirming the rejection is value-driven, not timing-driven.
* The UI cannot express a 9th symbol: DOWN from 7 wraps to 0 (observed), so the
  out-of-alphabet bound is a hardware/UI bound, not a validator branch.
* The all-Stitch string is the unique *special* accept: its checksum nibble is
  wrong (`0` vs `15`) yet it is accepted by the `sum==0` branch, and it writes
  no state (RAM verified: globals kept the previous values).

## 7. Validation evidence

**Observed (emulator screens / RAM reads).**
* Password screen, ACCEPTED! and INCORRECT screens at 240×160.
* `0x03007D70` buffers listed in 6b via mGBA `.ss*` savestate parsing
  (`gbAs` zlib chunk; IWRAM at `0x19000`).
* RAM fields after N1, Mothership, Lilo ×7 and Unlock All (values in 6b).
* Lives HUD x3 (default), x8 (N1 and Lilo ×7), x99 (button cheat).
* 99-lives cheat: with R+Select held, `KEYINPUT` (state offset `0x530`) read
  `0x2FB` and `0x02001140` became 99; released keys read `0x3FF`.
* Main menu count: `0x0200D660 = 4` → 5 entries; A-dispatch table has 5
  handlers (`0x08011624`).
* Menus walked: title, main (5 items), OPTIONS (MUSIC/SOUND), PASSWORD,
  MOVIES (4 entries), PICTURES (8 entries), pause/continue (CONTINUE/QUIT,
  YES/NO confirm, decorative 7-icon strip), credits.
* MODE7 intro: `MODE7 PRESENTS`, release date/region strings at `0x7FD2FA`.

**Derived (instruction-level).**
* Decoder `0x08001FB0` and encoder `0x08001E9C` (exact inverses).
* Mode/state/selector table `0x080020EC` and level-start table `0x0800171C`.
* Movie gating by state bits at `0x0801111C`.
* PICTURES gate on `flags != 0` at `0x0801167A`.
* 99-lives check at `0x08001686` (only `0x104` mask construction in code).

**Inferred.**
* Published level names for modes 2–6 are attached via the published code
  names plus the handler grouping; only mode 1 (Mothership) was started and
  observed in-game.
* `f6` is a progress/pass-through field (present in the encoder output, no
  gameplay reader); its actual meaning is not proven.

## 8. Unknowns

* Meaning of the `f6` field (`0x02000A48`, stored f6-1). No gameplay reader was
  found; only the encoder reads it. It may be a checkpoint/level-within-chapter
  byte preserved for the generated password.
* Exact semantics of the scene selector `0x02006154` (written as 0,4,5,6,10,11,12
  by mode, then incremented by the level handler). Values 1,2,3,7,8,9 are not
  reachable from the password handler, but whether they correspond to real
  game scenes was not tested.
* Per-bit meaning of `flags` beyond "non-zero opens PICTURES" and the
  state-bit movie gates. All 8 picture slots were navigable with flags=0x81 and
  0xFF; individual picture lock rendering was not compared across every flags
  value.
* Whether the MODE7 release patched anything at runtime beyond the boot intro;
  the disk diff against the supplied file is only the 3-byte entry branch, but
  no clean retail reference image was available to prove the rest of the image
  is byte-identical.
* Persistence: no save backend was observed (0-byte `.sav`, no
  EEPROM/SRAM/Flash signature). Session-only unlocks are consistent with a
  password-based design but a hidden save path was not exhaustively ruled out.

## 9. Tooling

* mGBA 0.10.5 (SDL), Xvfb `:329`, openbox, xdotool, ImageMagick
  (`import`, `convert`), scrot.
* `arm-none-eabi-objdump` and Python 3 + Capstone 5.0.7 for Thumb disassembly.
* `lilo_pw.py` (work dir `/tmp/opencode/lilo1`): alphabet/field model,
  encoder/decoder, published-code check, space enumeration
  (131,072 + 1 of 2,097,152) and alias demonstration.
* Savestate parser: PNG `gbAs` chunk → zlib → 397,312-byte state; IWRAM at
  `0x19000`, EWRAM at `0x21000`, `KEYINPUT` at `0x530`.
* Input helper `keys.py`: xdotool keydown/keyup, 70 ms hold / 160 ms gap.

## 10. Legal note

No ROM, graphics, audio, or extracted text is redistributed with this report.
Only hashes, addresses, field layouts, algorithms, and independently generated
codes are published.
