# Dexter's Laboratory: Deesaster Strikes! (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Dexter's Laboratory: Deesaster Strikes!/Dexter's Laboratory: Deesaster Strikes!.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`) |
| Header title (`0xA0`) | `DLDEESASTER` |
| Game code (`0xAC`) | `ADLE` (AGB-ADLE-USA) |
| Maker (`0xB0`) | `6L` |
| Version byte (`0xBC`) | `0x00` |
| Entry word (`0x00`) | `0xEA00002E` (`b 0x080000C0`, stock) |
| Fixed `0xB2` | `0x96` |
| Complement (`0xBD`) | `0x89` (recomputed `0x85`), header checksum (`0xBE`) `0x0000` |
| MD5 | `8aa75eb2e94320c942e8c71cedcec97c` |
| SHA-1 | `f230375ba4b0346d749e50117fe701d8c1cbfffa` |
| SHA-256 | `88d5bebf017e8b684c4eefe96ad02548af6e424c6762182c3c19fd90b88dbdee` |
| CRC32 | `E948D412` |

Notes:

* **Single-image cart.** A scan for the Nintendo logo bytes (`24 FF AE 51 …`)
  hits exactly one header, at file `0x0`. No multi-game shell, no second image.
* **No patch/trainer.** Entry word is the stock branch; the first 4 KiB is the
  normal crt0 + IRQ stubs. There is no cracktro string, no appended payload,
  and CRC32 `E948D412` matches the known USA dump listed on GameHacking.org.
* The empty header checksum `0x0000` with a complement byte that does not match
  the recomputed value is how this title shipped (the same header is present in
  every documented dump); it is not evidence of editing here — the CRC proves it.
* **Build/version inside the ROM:** `DEBUG INFORMATION` / `  VERSION 02/08/01`
  at file `0x20EDC` / `0x20EF0`. Per TCRF the 1.1 re-issue says `14/08/01`, so
  this image is the **initial release (v1.0)**, i.e. the build with the
  final-level wrench softlock.
* Audio: `GAX Sound Engine v2.01b (Jun 22 2001)` / `Shin'en Multimedia. Code:
  B.Wodok` at `0x55030`/`0x55057`. This is the Shin'en GAX banner, **not** a
  hidden code system (see §16 lesson on `Code:` banners).

## 2. Executive summary

There is **no password/keypad screen** in this game. The only developer cheat
surface is a **16-press L/R sequence entered on the PAUSE screen**, which is the
system the fan sites half-document.

The complete system is:

* A 16-bit shift register built from the pause screen's per-frame key latch:
  each **new** L press shifts in `1`, each **new** R press shifts in `0`, newest
  bit in bit 0. There is no checksum, alphabet, or length field — the 13 codes
  are 13 literal 16-bit constants.
* A **19-entry literal table at `0x083E7F6C`**. Entries 0–5 are milestone
  notifications (`DEXTER IS INVINCIBLE` … `ALL LEVELS ARE OPEN`) that are
  **never compared**; the scan runs `id = 6 … 18`, so exactly **13 codes are
  enterable**.
* On a match: the game clears a 32-bit "cheat active" bitmask at
  `0x02032614`, arms a **1800-frame (30 s) timer** at `0x02032618`, and sets
  `1 << id`. Only **one cheat can be active at a time** (each match clears the
  mask first). Two ids have immediate side effects in the dispatch table:
  id 16 adds one try (capped at 9), id 17 adds +10 to two ammo counters.
* All 13 codes were entered in mGBA and each produced its own
  `YOU HAVE UNLOCKED: <name>` screen, with the matching bit read back from RAM.

**Enumeration result (the deliverable):** of `2^16 = 65,536` possible L/R
strings, exactly **13** are accepted. Nine of them appear (some with wrong
labels) on the published cheat pages; **four are in no published list**:

| id | value | sequence | name | status |
|---:|---|---|---|---|
| 12 | `0xC6CA` | `LLRRRLLRLLRRLRLR` | **STRONG DEXTER** | unpublished |
| 14 | `0xC9E7` | `LLRRLRRLLLLRRLLL` | **ROBOTS ARE WEAK** | unpublished |
| 15 | `0x8ADF` | `LRRRLRLRLLRLLLLL` | **SLOW ENEMIES** | unpublished |
| 18 | `0xCD0E` | `LLRRLLRLRRRRLLLR` | **DEXTER-ROO** | unpublished |

All four were typed on the pause screen in mGBA, each opened its own
`YOU HAVE UNLOCKED:` banner (screenshots taken) and each set exactly
`1 << id` in `0x02032614`.

Two published-list errors were found and proven by rejection: the widely copied
"Reverse controls" string ending in `R` (`0x8166`) is **rejected** — the ROM
accepts the variant ending in `L` (`0x8167`); and "Slower opponents / Slower
Enemies" is published as `0xC466`, which the ROM labels **SLIPPERY FLOOR**
(the real slow-enemies code, `0x8ADF`, is unpublished).

The ROM's `DEBUG INFORMATION` overlay (`0x0800504C`) exists but is **dead code**:
zero BL callers and zero pointer literals anywhere in the image.

**Published sources checked** (button-code pages only; GameShark/CodeBreaker/
Action Replay RAM lists are out of scope by instruction): ggmania.com cheat
4379, GameRevolution guide 28598, cheatbook.de, games-cheats.org,
cheatingdome.com and the gbadamud blog. All six carry the same nine
L/R strings (with the two defects above); none list STRONG DEXTER, ROBOTS ARE
WEAK, SLOW ENEMIES or DEXTER-ROO. TCRF documents the text table and the debug
strings but no code system.

## 3. How to reproduce

Emulator: mGBA SDL under Xvfb.

```bash
Xvfb :304 -screen 0 1024x768x24 &
export DISPLAY=:304 SDL_AUDIODRIVER=dummy
mgba -3 "Dexter's Laboratory: Deesaster Strikes!.gba" &
```

Default mGBA keymap used: **A = `x`, B = `z`, Start = `Return`,
Select = `BackSpace`, D-pad = arrows**. Key holds 70–100 ms (a longer hold is
still one bit — the latch is edge-style — but long holds make the menu cursor
double-step).

Path to the code surface:

1. Title → `PRESS START` (`Return`).
2. First boot only: `ENGLISH / FRANÇAIS / DEUTSCH / ITALIANO / ESPAÑOL`.
3. Main menu `START GAME / OPTIONS / TUTORIAL` → `START GAME`.
4. `CHOOSE A SAVED GAME SLOT` (4 slots, `B ERASE`, `A PLAY`) → pick a slot.
5. In game press `Start` → **PAUSE** screen (stats + 6 empty inventory slots +
   `QUIT GAME? YES/NO`).
6. Press the 16-button L/R sequence **now** (`a` = L, `s` = R).
7. `YOU HAVE UNLOCKED: <name>` appears; `A` hides it; the pause menu remains.
8. Leave and re-open the pause screen before entering a second code (see §5.4).

To test the accepted set quickly: savestate on the pause screen (`Shift+F1`
saves, `F1` loads) and reload between tests.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Item | ROM address | File offset | Notes |
|---|---:|---:|---|
| Code table (19 × u16 LE) | `0x083E7F6C` | `0x3E7F6C` | ends at `0x083E7F91` (next u16 `0x0000`) |
| Pause-screen validator | `0x08013DCA`–`0x08013F62` | `0x13DCA` | inline in pause handler; accumulator `[sp,#24]` |
| Table compare loop | `0x08013DFC` | `0x13DFC` | `r4 = 6 … 18`, `cmp/beq` |
| Match handler | `0x08013E0A`–`0x08013E2C` | `0x13E0A` | clear mask, arm timer, `orr 1<<id` |
| Action/jump table (17 × u32) | `0x08013E58` (base ptr `[0x08013E54]`) | `0x13E58` | indexed by `id-1`, ids 1…17 |
| id16 handler (tries) | `0x08013EEA` | `0x13EEA` | `++u16[state+0x40]` if `<= 8` |
| id17 handler (ammo) | `0x08013EFA` | `0x13EFA` | `+10` to `u32[state+0x120]` and `u32[state+0x124]` |
| Message draw call | `0x08013F26`–`0x08013F50` | `0x13F26` | picks header + name string by id |
| Text block base (level 0) | `0x083D5D0C` | `0x3D5D0C` | per-level block, 68-byte stride |
| `YOU HAVE UNLOCKED:` (EN) | `0x083E0A9C` | `0x3E0A9C` | other languages at `0x3E0E3F`, `0x3E11E6`, `0x3E15A9`, `0x3E1983` |
| Cheat name list (EN) | `0x083E0AAF`–`0x083E0BD2` | `0x3E0AAF` | 19 NUL-terminated strings |
| Key-press latch | `0x02000942` | — | u16, L=`0x0200`, R=`0x0100` |
| Game state base | `0x0203257C` | — | EWRAM |
| `+0x40` u16 | tries | — | pause screen "TRIES" |
| `+0x44` u16 | level/section index | — | used to select text block |
| `+0x98` u32 | **cheat active mask** | — | abs `0x02032614` |
| `+0x9C` u32 | **cheat timer (frames)** | — | abs `0x02032618`, 1800 = 30 s |
| `+0x120`, `+0x124` u32 | ammo counters (id17) | — | |
| Debug overlay (dead) | `0x0800504C` | `0x504C` | 0 BL callers, 0 pointer literals |

## 5. Algorithm

### 5.1 Accumulator

Every frame the pause handler reads the u16 key-press latch and updates a
16-bit stack variable:

```python
v = 0                                  # [sp,#24], 16-bit
if keys & 0x0200:  v = ((v << 1) | 1) & 0xFFFF   # L  -> 1
if keys & 0x0100:  v = (v << 1) & 0xFFFF         # R  -> 0
```

Disassembly (Thumb, `0x08013DCA`):

```
8013dca: ldr  r1, [pc,#124]   ; -> 0x02000942 (key latch)
8013dcc: ldrh r2, [r1]
8013dce: movs r0, #0x80
8013dd0: lsls r0, r0, #2      ; 0x200 = L
8013dd2: ands r0, r2
8013dd6: cmp  r0, #0
8013dd8: beq  0x8013de6
8013dda: ldr  r1, [sp,#24]
8013ddc: lsls r0, r1, #1
8013dde: adds r0, #1
8013de0: lsls r0, r0, #16
8013de2: lsrs r0, r0, #16     ; mask 16 bits
8013de4: str  r0, [sp,#24]
8013de6: movs r0, #0x80
8013de8: lsls r0, r0, #1      ; 0x100 = R
8013dea: ands r0, r2
8013dec: beq  0x8013df8
8013df0: ldr  r2, [sp,#24]
8013df2: lsls r0, r2, #17
8013df4: lsrs r0, r0, #16     ; v <<= 1, 16-bit
8013df6: str  r0, [sp,#24]
```

One bit per press: the latch is a per-frame "newly pressed" word, so a 90 ms
hold still contributes exactly one bit (verified: six L taps produced `0x3F`).

### 5.2 Match

```python
BASE = 0x083E7F6C
for cheat_id in range(6, 19):            # ids 0..5 are never compared
    if v == u16[BASE + 2*cheat_id]:
        state[0x98] = 0                  # only one cheat at a time
        state[0x9C] = 1800               # 30 s at 60 Hz
        state[0x98] |= 1 << cheat_id     # cheat active bit
        dispatch(cheat_id)               # jump table [0x08013E58 + (id-1)*4]
        show_message(cheat_id)           # header + name from the text block
        break
```

The disassembly of the loop bound is exact: `movs r4,#6` before the first
compare (`0x08013DF8`), `cmp r4,#18` / `bgt` after the increment
(`0x08013F5E`).

**This is the only reference to the table in the image.** The literal
`0x083E7F6C` occurs once, at file `0x13E4C` (the pause validator's literal
pool), so there is no second code path, no copy in EWRAM (a savestate search for
the 26-byte table image found nothing) and no per-level variant. The same 16-bit
values also occur elsewhere as graphics/wave data (spot-checked: `0xC0CE` at
file `0x28326` is a sine table), never as comparison constants.

### 5.3 Effects

* The active cheats are read elsewhere as the bitmask at `state+0x98`. While
  paused the 30 s timer does not tick; in gameplay it decrements once per frame
  and when it reaches 0 the mask is cleared (observed: mask `0x40` at t=0,
  `0x40` at +18 s, `0x0` at +24 s, timer `1282 → 859 → 436 → 13 → 0`).
* `id 16` (ONE MORE TRY) increments `u16[state+0x40]` (tries) if `<= 8`, then
  zeroes the timer so its bit is momentary. Observed: TRIES 3 → 4 on the pause
  screen after entering `LLRRLRLLLRLLRRLL`.
* `id 17` (GET DOUBLE AMMO) adds 10 to two ammo counters at `state+0x120/0x124`
  and zeroes the timer, likewise momentary.
* The other 11 ids (6–15, 18) set their bit and leave the 30 s timer armed.

### 5.4 Session quirks (reproduction-critical)

* **One code per pause session.** After a match the pause handler stays in its
  message state; `A` hides the banner but the pause screen remains, and a
  second L/R sequence is ignored (observed: entering id 6 then id 7 in one
  session left the mask at `0x40`, not `0x80`). Exit the pause screen and
  re-open it; the same test then yields `0x80`.
* **The 30 s timer is frozen while paused** (mask and timer `0x708` unchanged
  after 35 s paused), and only counts down in gameplay.
* **The surface is pause-only.** Typing a valid sequence during gameplay has no
  effect (mask stayed `0x0` after pausing).

## 6. Tables

### 6.1 The 19-entry table at `0x083E7F6C`

`v` is the 16-bit accumulator; the sequence is the press order (L/R), MSB =
first press. Names are the ROM strings reached through the per-level text block
(name pointers listed in §4/§6.2).

| id | value | sequence | ROM name | compared? | published? |
|---:|---|---|---|---|---|
| 0 | `0xE087` | `LLLRRRRRLRRRRLLL` | DEXTER IS INVINCIBLE | no | — |
| 1 | `0xA14E` | `LRLRRRRLRLRRLLLR` | GOT ALL DEE DEES | no | — |
| 2 | `0xE226` | `LLLRRRLRRRLRRLLR` | FIXED ALL MACHINES | no | — |
| 3 | `0xA313` | `LRLRRRLLRRRLRRLL` | GOT ALL TOOLS | no | — |
| 4 | `0xE489` | `LLLRRLRRLRRRLRRL` | GOT ALL GUNS | no | — |
| 5 | `0xA546` | `LRLRRLRLRLRRRLLR` | ALL LEVELS ARE OPEN | no | — |
| 6 | `0xC0CE` | `LLRRRRRRLLRRLLLR` | LOW GRAVITY | **yes** | yes ("low gravity" / "higher jumps") |
| 7 | `0x8167` | `LRRRRRRLRLLRRLLL` | CONTROLS ARE REVERSED | **yes** | yes (one list has `…LLR`, typo) |
| 8 | `0xC23F` | `LLRRRRLRRRLLLLLL` | STRONG ENEMIES | **yes** | yes |
| 9 | `0x83C3` | `LRRRRRLLLLRRRRLL` | FAST ENEMIES | **yes** | yes |
| 10 | `0xC466` | `LLRRRLRRRLLRRLLR` | SLIPPERY FLOOR | **yes** | yes (mislabeled "slower enemies" in two lists) |
| 11 | `0x8534` | `LRRRRLRLRRLLRLRR` | FAST DEXTER | **yes** | yes |
| 12 | `0xC6CA` | `LLRRRLLRLLRRLRLR` | **STRONG DEXTER** | **yes** | **no** |
| 13 | `0x877E` | `LRRRRLLLRLLLLLLR` | LESS DAMAGE | **yes** | yes |
| 14 | `0xC9E7` | `LLRRLRRLLLLRRLLL` | **ROBOTS ARE WEAK** | **yes** | **no** |
| 15 | `0x8ADF` | `LRRRLRLRLLRLLLLL` | **SLOW ENEMIES** | **yes** | **no** |
| 16 | `0xCBB3` | `LLRRLRLLLRLLRRLL` | ONE MORE TRY | **yes** | yes ("extra life") |
| 17 | `0x8CF6` | `LRRRLLRRLLLLRLLR` | GET DOUBLE AMMO | **yes** | yes ("double ammo") |
| 18 | `0xCD0E` | `LLRRLLRLRRRRLLLR` | **DEXTER-ROO** | **yes** | **no** |

Table bytes after entry 18: `0x0000` padding, then unrelated credit/text data.

### 6.2 Name-string pointers (English, level 0)

`0x083E0AAF` DEXTER IS INVINCIBLE · `0x083E0AC4` GOT ALL DEE DEES ·
`0x083E0AD5` FIXED ALL MACHINES · `0x083E0AE8` GOT ALL TOOLS ·
`0x083E0AF6` GOT ALL GUNS · `0x083E0B03` ALL LEVELS ARE OPEN ·
`0x083E0B17` LOW GRAVITY · `0x083E0B23` CONTROLS ARE REVERSED ·
`0x083E0B39` STRONG ENEMIES · `0x083E0B48` FAST ENEMIES ·
`0x083E0B55` SLIPPERY FLOOR · `0x083E0B64` FAST DEXTER ·
`0x083E0B70` STRONG DEXTER · `0x083E0B7E` LESS DAMAGE ·
`0x083E0B8A` ROBOTS ARE WEAK · `0x083E0B9A` SLOW ENEMIES ·
`0x083E0BA7` ONE MORE TRY · `0x083E0BB4` GET DOUBLE AMMO ·
`0x083E0BC4` DEXTER-ROO.

The banner above them is at `0x083E0A9C` (`YOU HAVE UNLOCKED:`), and the same
list is translated: FR `0x083E0E3F` **`TRICHE DÉBLOQUÉE:`**, DE
`0x083E11E6` `FREIGESPIELT:`, IT `0x083E15A9` `HAI ATTIVATO:`, ES
`0x083E1983` `HAS ACTIVADO:`. The French string is the only occurrence of the
word "cheat"/"triche" in the whole ROM and it names the feature explicitly.

### 6.3 Flag bits and timer

| State field | Meaning |
|---|---|
| `0x02032614` (base+`0x98`) | bit *n* = cheat id *n* active; always exactly one bit or 0 |
| `0x02032618` (base+`0x9C`) | frames remaining (1800 at match; 0 for ids 16/17) |
| `0x020325BC` (base+`0x40`) | tries (u16) |
| `0x0203269C` / `0x020326A0` | ammo counters touched by id 17 (`+0x120`/`+0x124`) |

## 6b. Enumeration

### Space definition

* Input alphabet: **2 symbols**, L and R (bits `0x200` / `0x100` of the key
  latch). No other button feeds the register (16 B presses left the mask at 0).
* Length: exactly **16 presses** to fill the 16-bit register.
* No checksum, no parity, no reserved bits, no wildcard symbol: the validator is
  a linear scan of 13 literal constants with `cmp`/`beq`, so acceptance is
  exact equality on all 16 bits.
* **Representable space: `2^16 = 65,536`.** **Accepted set: exactly 13.** The
  other six table entries (ids 0–5) are data-only: the loop starts at id 6, so
  their values cannot be entered.

### Novel codes (absent from every published list checked)

Entered on the pause screen in mGBA; each screenshot shows
`YOU HAVE UNLOCKED: <name>`, and the mask read from the savestate immediately
after is exactly the listed bit.

| code (press order) | value | id | observed banner | mask at `0x02032614` |
|---|---:|---:|---|---:|
| `LLRRRLLRLLRRLRLR` | `0xC6CA` | 12 | `STRONG DEXTER` | `0x1000` |
| `LLRRLRRLLLLRRLLL` | `0xC9E7` | 14 | `ROBOTS ARE WEAK` | `0x4000` |
| `LRRRLRLRLLRLLLLL` | `0x8ADF` | 15 | `SLOW ENEMIES` | `0x8000` |
| `LLRRLLRLRRRRLLLR` | `0xCD0E` | 18 | `DEXTER-ROO` | `0x40000` |

Each also armed the 1800-frame timer (`0x708`). For the published ids the same
procedure reproduced the ROM name for all nine (ids 6, 8, 9, 10, 11, 13, 16, 17
and 7), which validates the decoder.

### Bounds proven by rejection

All entered on the same pause screen; mask read back as `0x00000000`, no banner.

| input | why it should fail | result |
|---|---|---|
| `LLRRRRRRLLRRLLL` (15 presses, id 6 minus last) | short sequence | rejected |
| `RLRRRRRRLLRRLLLR` (id 6 with first bit flipped) | 1-bit error | rejected |
| `LLRRRRRLLLRRLLLR` (id 6 with middle bit flipped) | 1-bit error | rejected |
| `LLRRRRRRLLRRLLLL` (id 6 with last bit flipped) | 1-bit error | rejected |
| `LRRRRRRLRLLRRLLR` = `0x8166` (published "reverse controls" with final `R`) | published typo, not in table | rejected |
| `LLLRRRRRLRRRRLLL` = `0xE087` (table id 0) | id 0 is never compared | rejected |
| `LLLRRRLRRRLRRLLR` = `0xE226` (table id 2) | id 2 is never compared | rejected |
| `LLLLLLLLLLLLLLLL` = `0xFFFF` | not in table | rejected |
| `RRRRRRRRRRRRRRRR` = `0x0000` | not in table | rejected |
| `LRLRLRLRLRLRLRLR` | not in table | rejected |
| 16 × B during pause | wrong buttons | rejected |
| id 6 sequence typed in gameplay | wrong screen | rejected |

Semantic bounds: ids 0–5 exist as *data* but cannot be produced by any input;
there is no longer-form code (17+ presses only shift the window, and a valid
16-press suffix fires on its own).

## 7. Validation evidence

**Observed (emulator / RAM):**

* Every screen enumerated: title (`PRESS START`), first-boot language select
  (5 entries), main menu (3 entries), options (7 entries: MUSIC, SOUND FX,
  START LIVES, BRIGHTNESS, BUTTON CONFIGURATION, CREDITS, RESTORE DEFAULTS),
  save-slot select (4 slots, `B ERASE` / `A PLAY`), pause (stats, 6 empty
  inventory slots, `QUIT GAME? YES/NO`), `ERASE SAVED GAME?` prompt, and the
  cheat banner overlay. There is **no level-select menu** (the hub computer is
  in-game and is not a cheat surface).
* 13/13 accepted sequences produce their named banner and their exact mask bit.
* Timer behaviour: `0x40`/1800 at match, decrement only in gameplay
  (1282→859→436→13→0 over 24 s), mask cleared at 0.
* TRIES 3→4 after id 16 (banner `ONE MORE TRY`).
* One-code-per-pause-session and pause-only surface, as described in §5.4.

**Derived (disassembly):**

* The 19-entry table at `0x083E7F6C`, the `id = 6 … 18` scan, the
  clear-mask/arm-timer/set-bit sequence, the 17-entry action table at
  `0x08013E58`, and the two instant handlers (`+0x40` tries, `+0x120/+0x124`
  ammo).
* The 16-bit shift semantics (L→1, R→0, newest bit in bit 0).
* Name lookup through the per-level text block (`state+0x44`, 68-byte stride,
  header at slot 87, names at slots 88+id) — matches all 13 observed banners.
* The `DEBUG INFORMATION` overlay at `0x0800504C` is unreachable: 0 BL hits and
  0 pointer literals to `0x0800504C`/`0x0800504D` in the whole image.

**Inferred:**

* The *gameplay meaning* of each modifier is taken from its own name string and
  the fact that the bitmask is consumed by the game each frame. Only LOW GRAVITY
  was probed physically (a coarse jump capture showed ~93 px rise vs ~81 px
  baseline) — the capture timing is not precise enough to call that proof, so
  the per-name effect magnitudes remain inferred. Ids 16/17 are the exception:
  their effects are proven (tries, ammo).
* Ids 0–5 are read as level-completion milestone messages (`GOT ALL DEE DEES`,
  `FIXED ALL MACHINES`, …) because their names match the pause/level-complete
  counters and they sit in the same message list; no writer of bits 0–5 was
  isolated.

## 8. Unknowns

* Exact per-id gameplay constants (how much faster/slower/stronger). The
  bitmask consumer routine was not isolated; the search for word reads of
  `state+0x98` inside the gameplay code was inconclusive because the state base
  is reached through a RAM pointer, not a literal.
* Whether the banner text block (per level, `state+0x44`) ever differs between
  levels for the cheat names — the English strings are identical across the
  five language banks, and only level 0 was exercised.
* The writer of the six milestone bits 0–5 (inferred: level-complete handler).
* What DEXTER-ROO changes visually: entering it produced the banner, set bit 18
  and armed the timer, but the sprite in the starting room was unchanged during
  the 30 s window. It may be consumed only on level load or affect an ability
  not visible in an empty room.

## 9. Tooling

* `mgba` (SDL) under `Xvfb :304` + `openbox`; `xdotool`, `scrot`, ImageMagick.
* Python 3 scripts in the work dir: savestate reader (PNG `gbAs` chunk,
  `zlib.decompress`; EWRAM at state offset `0x21000`, IWRAM at `0x19000`),
  sequence runner, mask reader.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M
  force-thumb` for the validator, dispatch table and debug overlay.
* `gdb-multiarch` against `mgba -g` for the shift-register watchpoint
  (`0x8013de8`, old 0 → new 1 on an L press).
* Pillow (installed with `pip install --break-system-packages pillow`) for
  screenshot pixel measurement; not required for the result.

## 10. Comparison with the sibling SKU

*Dexter's Laboratory: Chess Challenge* (same publisher era, same 5-language
text-bank style and the same dead `FIXED ALL MACHINES` / `LOW GRAVITY` /
`START LIVES` strings) implements a 16-cell password there. Here those same
strings are **live** as the 13-code pause cheat system. The tables are not
shared: Chess Challenge's password alphabet `BCDFGHJKLMNPQRST` and its
nibble validator do not exist in this image, and this table (`0x083E7F6C`) has
no analogue there. Treating the sibling report as a map for this ROM would have
been wrong in both directions.

## 11. Legal note

No ROM, extracted graphics, music or text banks are redistributed with this
report; only addresses, hashes, algorithms and our own generated inputs.
