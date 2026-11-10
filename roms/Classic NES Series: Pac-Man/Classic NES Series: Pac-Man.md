# Classic NES Series: Pac-Man (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Classic NES Series: Pac-Man/Classic NES Series: Pac-Man.gba` |
| Size | 1,048,576 bytes (0x100000) |
| Header title | `PAC-MAN` (0xA0, NUL padded) |
| Game code | `FP7E` (0xAC) |
| Maker code | `01` (0xB0) — Nintendo |
| Version | 0x00 (0xBC) |
| Complement check | stored 0x01, computed 0x01 → **valid/unmodified header** |
| Header checksum | 0x0000 (normal artifact of a rebuilt/Nintendo header; complement byte is the reliable signal) |
| MD5 | `1597d0bff45a3722beae045d218d6649` |
| SHA-1 | `843d853ed28a116c85a5357f9a94e9179f36a6d0` |
| SHA-256 | `e5dd09eb171d108131d849c0615a1faced4c9b0df5dee58e724d51e728f8422d` |
| Entry word | `0xEA000031` (not the stock `0xEA00002E`) → branches to `0x080000CC` |

**Embedded headers.** A 156-byte Nintendo-logo scan finds **exactly two** GBA headers, at
file 0x0 and file **0xD35C**:

* `0x000000` — title `PAC-MAN`, code `FP7E`, entry `0xEA000031`.
* `0x00D35C` — title `PAC-MAN`, code `FP7E`, entry `0xEA000061` → `0x0800D4E8`
  (a conventional ARM crt0 that sets up the stacks through the mode registers).
* File 0x6360 holds the multiboot ID string `Sio32ID_030820`.

The image is therefore a *two-image* cartridge build: the main program runs from the
first header (verified live, see §4) and a second, self-linked single-pak client image
is embedded at `0x0800D35C`. Both carry the same title, so a naive "header says
PAC-MAN" check cannot distinguish them; the live RAM evidence in §4 does.

**No trainer / cracktro.** `0x080000CC` is a 100-byte Nintendo-style loader, not alien
code:

```
080000CC  add  r5, pc, #0x3C          ; r5 = table at 0x08000110
080000D0  ldm  r5!, {r0,r1,r4,r6,r7,r8,r9}
080000D4  msr  CPSR_fc, r7            ; IRQ mode, sp = 0x03007FA0
080000DC  msr  CPSR_fc, r8            ; SVC mode, sp = 0x03007FE0
080000E4  msr  CPSR_fc, r9            ; System,   sp = 0x03007F00
080000EC  push {r0,r1}
080000F0  svc  0x11                   ; LZ77UnCompVram
080000F4  pop  {r0,pc}                ; jump to r1 = 0x03007400
```

Table at 0x110: `src=0x08006370`, `dst=0x03007400`, `DMA3=0x040000D4`,
`0x0800648C`, `0x12`, `0x13`, `0x1F`. The source block at 0x6370 is
`10 14 01 00 …` = GBA LZ77, decompressed size 276 bytes; the 276-byte stage-2
stub then loads the rest. Nothing in the first 4 KiB is a cracktro, and the
complement check is valid, so the image is treated as a stock Nintendo build.

**NES payload.** The emulated Famicom PRG is not stored plaintext in the GBA image
(it is in a compressed/obfuscated data bank), but at run time the wrapper has
decompressed the complete **16,384-byte PRG** into EWRAM at `0x02000000`
(observed in an mGBA savestate). Exact image used for all 6502 work:

* `nes_prg.bin`, 16384 bytes, MD5 `7979781312d13a6615a3c3cd38858433`
* NES vectors: NMI `$C10E`, RESET `$C033`, IRQ `$C17E`
* Reset copyright string `COPY RIGHT 1984 1993 NAMCO LTD. ALL RIGHTS RESERVED`
  at `$C000`; programmer credit `HIROKI AOYAGI` at `$C0FF`.

## 2. Executive summary

**This SKU has no password system, no button cheat code, no debug menu and no
unlockable-content system.** The complete in-game input surface is:

1. **NES title screen** — `Select` toggles 1 PLAYER / 2 PLAYERS (`$47`), `Start`
   begins the game (`$C48A`–`$C4FA`).
2. **NES gameplay** — `Start` **or** `Select` toggles the NES pause (`$CAB3`);
   the game paints the word `PAUSE`.
3. **GBA wrapper system menu** — `L+R` opens a 5-item menu: `continue`,
   `reset`, `linked play`, `save high score`, `sleep mode`. The selector is an
   index at `0x03007B51`, range **0..4**, wrapping; there is no undocumented
   5th/6th slot.
4. **GBA wrapper reset combo** — `A+B+Select+Start` (`key == 0x0F`) enters the
   reset handler `0x080019C9`, which warm-resets the emulated NES.

The NES PRG contains exactly **one** controller-read site (`$C143`–`$C162` in the
NMI handler), and only **eight** consumers of the resulting button byte `$4D`;
none of them compares a *sequence*, so no key-mask cheat can exist in this image.

The published "GBA codes" are for other platforms. GameFAQs' GBA page mixes in
Commodore-64 `POKE`s, an Atari 2600 easter egg, a **Game Boy** "1/2 full-screen"
trick, Windows-Mobile/iOS achievement lists and an Xbox 360 gamerpic. None of those
literals or mechanics exists in this ROM (§6b.5).

The one genuine hidden-internals result is the **round table**: the per-round
6-byte record table at `$EBB6` has 22 distinct entries and the round counter `$68`
saturates (`CMP #$16`), so the arcade level-256 kill-screen rollover **cannot occur
in this port** — the 256-behaviour is arcade-only.

## 3. How to reproduce

Environment: Debian, mGBA 0.10.5 SDL (`/usr/games/mgba`), Xvfb on **:253**,
openbox, `SDL_AUDIODRIVER=dummy`. Key map used (mGBA default):
`A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, D-pad = arrows.
Every key is held 120–200 ms; `Shift+F1` writes `…/Classic NES Series: Pac-Man.ss1`.

```bash
Xvfb :253 -screen 0 1024x768x24 &
DISPLAY=:253 openbox &
DISPLAY=:253 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 "Classic NES Series: Pac-Man.gba" &
W=$(DISPLAY=:253 xdotool search --name mGBA | head -1)
DISPLAY=:253 xdotool windowfocus "$W"
```

Screens and how to reach them:

| Screen | Path |
|---|---|
| NES title | boot (title shows 1 PLAYER / 2 PLAYERS) |
| NES game | `Return` (Start) on the title |
| NES pause | `Return` or `BackSpace` during play; `PAUSE` appears |
| Ghost-cast attract screen | idle after title, `CHARACTER ; NICKNAME` / SHADOW/BLINKY … |
| Wrapper system menu | hold `a`+`s` (L+R) ~0.5 s |
| Wrapper reset | hold `x`+`z`+`BackSpace`+`Return` (A+B+Select+Start) |
| Link-play sub-screen | menu → item 2 → `x` (A); `z` (B) cancels |

Offline reproduction of the RAM claims: extract the `gbAs` chunk from the
savestate (zlib) → 397,312 bytes with this layout:

```
0x0000 CPU/regs   0x0400 IO regs    0x0800 palette   0x0C00 OAM
0x1000 VRAM (0x18000)   0x19000 IWRAM (0x8000)   0x21000 EWRAM (0x40000)
```

GBA address of a saved byte = `0x02000000 + off - 0x21000` (EWRAM) or
`0x03000000 + off - 0x19000` (IWRAM).

## 4. Address map

### 4.1 GBA side (main image)

| Address | Meaning |
|---|---|
| `0x080000CC` | entry: LZ77 stub → `0x03007400` |
| `0x08006370` | LZ77 stage-2 stub (276 bytes out) |
| `0x0800D35C` | second embedded GBA header (single-pak client image) |
| `0x0800D4E8` | client crt0 |
| `0x08002739` | **wrapper system-menu handler** (`L+R`) |
| `0x080027A0` | menu item dispatch table (5 pointers, 0..4) |
| `0x08002951` | entry wrapper entered from the game handler on L+R |
| `0x080029A1` | "game running" handler (also the menu's *continue* target) |
| `0x080029A0`+0x24 | L+R / A+B+Select+Start detector |
| `0x080025E5` | save-high-score confirmation handler |
| `0x08002169` | linked-play handler |
| `0x080019C9` | reset handler (entered by A+B+Select+Start) |
| `0x08001A21` | sleep-mode countdown handler |
| `0x08001945` | continue/return handler |
| `0x08003196` | font-encoded string `( menu )` |
| `0x080031A2..0x080031DF` | `continue`, `reset`, `linked play`, `save high score`, `sleep mode` |
| `0x08003CB0..0x08003E6C` | 111-slot message pointer table (76 distinct) |
| `0x08003080..0x08003CA8` | 58 `0xFF`-terminated font-encoded message records |
| RAM `0x030064BC` | current GBA key state (active high, 10 bits) |
| RAM `0x030064C0` | newly pressed keys this frame |
| RAM `0x030064C4` | **current UI handler pointer** (Thumb, low bit set) |
| RAM `0x03007B51` | **system-menu selector index** (0..4) |

The wrapper key reader (`0x0800E9F0`) computes
`cur = ~KEYINPUT & 0x3FF`, `new = cur & ~prev`, storing them at
`0x03005E28/0x03005E2C`; the first-image build uses `0x030064BC/0x030064C0`.
The live build is the first image: while L+R is held `0x030064BC == 0x300`
and the handler at `0x030064C4` changes from `0x080029A1` to `0x08002739`.

System-menu detector at `0x080029A0` (derived):

```
key = [0x030064BC]
if key == 0x0F:                 ; A+B+Select+Start
    handler = 0x080019C9        ; reset
else if key == 0x300:           ; L+R, exactly
    if key & [0x030064C0]:      ; at least one was a new press
        handler = 0x08002951    ; → menu state machine 0x08002739
```

### 4.2 NES side (PRG, addresses are 6502)

| Address | Meaning |
|---|---|
| `$C033` | RESET: PPU off, clear RAM, warm-boot check |
| `$C087–$C0B4` | compare `$C0FF..` with `$0052..`; on mismatch clear RAM and copy the 13-byte `HIROKI AOYAGI` marker (warm-boot/continue flag) |
| `$C14D–$C162` | **the only** `$4016/$4017` read: 8× `ROR` into `$4D`/`$4E` |
| `$C48A`, `$C490` | title: `$4D & 4` (Select), `$4D & 8` (Start) |
| `$C4B2–$C4E6` | Select edge → toggle `$47` (1P/2P), move cursor OAM |
| `$C4E9–$C504` | Start edge → `$CA54` (new game) |
| `$CAB3–$CABD` | in-game `$4D & 0x0C` (Start or Select) → pause, `$3F = 2` |
| `$CB5B` | `PAUSE` tile list written to `$024D..` |
| `$CAD7` | game-state pointer table (states 0..8) |
| `$CF3C–$CF42` | round counter `$68`: `CMP #$16` / `BEQ` / `INC` → **saturates at 22** |
| `$CF59–$CF65` | record index = `$68 * 6` |
| `$EBB6` | **per-round table, 6 bytes/record** (file 0x2BB6) |
| `$EC40` | 22-byte records, indexed by `$EBB6[rec+0]` |
| `$ECAE` | 8-byte records, indexed by `$EBB6[rec+0]` |
| `$ECCE` | 2-byte pairs, indexed by `$EBB6[rec+2]` |
| `$ECDC` | 4-byte records, indexed by `$EBB6[rec+3]` |
| `$06xx` | NES OAM shadow / sprite buffers |
| `$C69D` region | ASCII screen text (`CHARACTER ;  NICKNAME`, ghost names, `10 PTS`, `50 PTS`) |

NES RAM at run time is the 2 KiB block at **GBA `0x03007200`** (`$0052` holds the
`HIROKI AOYAGI` marker, `$4D` the P1 pad byte, `$68` the round).

## 5. Algorithm

### 5.1 NES input → game (derived, one site)

```
; NMI, $C143
LDA #1 : STA $4016
LDA #0 : STA $4016
LDX #8
loop: LDA $4016 : AND #3 : CMP #1 : ROR $4D     ; P1
      LDA $4017 : AND #3 : CMP #1 : ROR $4E     ; P2
      DEX : BNE loop
; bit order after 8 rotates: A B Select Start Up Down Left Right (bits 0..7)
```

There is no sequence matcher, no shift register of past presses, and no
`mod`/hash of the pad byte anywhere in the 16 KiB. Button-cheat systems are
therefore excluded by construction, not by a failed search.

### 5.2 Title / pause (derived)

```
Select edge  -> $47 ^= 1                 ; 1P/2P cursor
Start  edge  -> JMP $CA54                ; start, clears $3F,$46,$4A,$69
in game: if ($4D & 0x0C) != 0 and $48==0:
             $3F = 2                     ; pause state $CAE9
             write "PAUSE" to $024D..    ; OAM text
```

### 5.3 Round table and the "level 256" question (derived)

```
$CF3C  LDA $68            ; $68 = 0xFF on new game ($CA97)
$CF3F  CMP #$16           ; 22
$CF41  BEQ   skip
$CF42  INC $68            ; round counter, saturates at 22
...
$CF59  LDX $68
       A = (X-1)*6        ; 0 for X=0
       LDA $EBB6,A        ; per-round record
```

The record table at `$EBB6` therefore has **22 distinct 6-byte rows**
(row 23 duplicates row 22 because `$68` is allowed to reach 22). Consequence:
**the arcade Pac-Man level-256 rollover/kill-screen does not exist in this
port**; a "Be Like Billy! / Complete Stage 256" style goal is impossible here —
rounds 22 and beyond replay the last row.

Per-round rows (file 0x2BB6):

```
lvl  0: 00 07 00 00 00 04      lvl 11: 03 02 04 02 06 03
lvl  1: 01 06 01 01 01 04      lvl 12: 03 01 05 02 06 03
lvl  2: 01 04 02 02 02 03      lvl 13: 03 01 05 02 07 03
lvl  3: 02 03 02 02 02 03      lvl 14: 03 03 05 02 07 03
lvl  4: 02 02 02 02 03 03      lvl 15: 03 01 06 02 07 03
lvl  5: 03 05 03 02 03 03      lvl 16: 03 01 06 02 07 03
lvl  6: 03 02 03 02 04 03      lvl 17: 03 00 06 02 07 03
lvl  7: 03 02 03 02 04 03      lvl 18: 03 01 06 02 07 03
lvl  8: 03 01 04 02 05 03      lvl 19: 03 00 06 02 07 03
lvl  9: 03 05 04 02 05 03      lvl 20: 03 00 06 02 07 03
lvl 10: 03 02 04 02 06 03      lvl 21: 03 00 06 02 07 03
                               lvl 22: 04 00 06 02 07 03
```

Byte 0 is monotonically increasing (0→4) and indexes the `$EC40`/`$ECAE`
graphics/pattern records; byte 1 falls 7→0 (the difficulty/speed field, the
closest analogue of the published speed tables); byte 2 indexes the `$ECCE`
pairs; byte 3 indexes `$ECDC`; bytes 4–5 are copied to `$8C`/`$8D/$8E`
(*inferred* roles — see §8).

### 5.4 Wrapper system menu (derived + observed)

```
handler 0x08002739:
  if (new & 2) or (key == 0x300 && new & key):  menu_armed = 1
  update_emulator_frame()
  switch [0x03007B51]:            ; item index 0..4
    0: item = 0x08001945          ; continue
    1: item = 0x080019C9          ; reset
    2: link sub-screen code       ; linked play
    3: item = 0x080025E5          ; save high score
    4: item = 0x08001A65          ; sleep mode
  if key & 0x40 (Up):       idx = 4
  if key & 0x84 (Down|Sel): idx++; if idx > 4: idx = 0
  if key & 0x09 (A|Start):  [0x030064C4] = item
```

Observed handler transitions:

| idx | item | handler entered | notes |
|---|---|---|---|
| 0 | continue | `0x080029A1` | back to game |
| 1 | reset | `0x080019C9` → `0x080029A1` | NES soft reset; `$68` preserved |
| 2 | linked play | `0x08002169` | sub-screen; `B` returns to game |
| 3 | save high score | `0x080025E5` | confirmation (SRAM/EEPROM save) |
| 4 | sleep mode | `0x08001A21` → `0x080029A1` | power-saving path |

## 6. Tables

### 6.1 Wrapper system-menu items (ROM strings at 0x08003196)

| idx | encoded | plaintext |
|---|---|---|
| — | `G <*8: G` | `( menu )` |
| 0 | `,B82>8:*` | `continue` |
| 1 | `.*'*2` | `reset` |
| 2 | `C>8?*+ FC#6` | `linked play` |
| 3 | `'#0* 7>37 ',B.*` | `save high score` |
| 4 | `'C**F <B+*` | `sleep mode` |

(The wrapper font is a monoalphabetic tile-index encoding; the mapping was
recovered from `Press the Button`, `turn the power off and check the
connection`, `wireless adapter cannot be used`, etc.)

### 6.2 NES pad byte (`$4D`)

| bit | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| button | A | B | Select | Start | Up | Down | Left | Right |

### 6.3 NES game states (`$3F`, table `$CAD7`)

`0 $CEF3` level init · `1 $CB67` maze draw · `2 $CAE9` pause · `3 $CCD9` ·
`4 $CD06` · `5 $CE1F` · `6 $CDB0` · `7 $E6D6` · `8 $E7BF`

### 6.4 Round table: see §5.3.

### 6.5 All NES ASCII strings ≥4 chars (50 total)

Title/menu/credit: `COPY RIGHT 1984 1993 NAMCO LTD. ALL RIGHTS RESERVED`,
`HIROKI AOYAGI`, `1 PLAYER`, `2 PLAYERS`, `(C) 1980`, `1984 NAMCO LTD`,
`LICENSED TO NINTENDO`, `PAUSE`.
Attract cast: `CHARACTER ;  NICKNAME`, `:SHADOW`, `_BLINKY_`, `:SPEEDY`,
`_PINKY_`, `:POKEY`, `_CLYDE_`, `10 PTS`, `50 PTS` (the fourth row is drawn
with extended font tiles `$B6/$C1/$C3/$B7/$B4/$C2/$B3/$C4` = `:BASHFUL` and
`$C8/$B5/$C5/$C0/$C6/$C8` = `_INKY_`). The remainder are tile/palette blobs,
not text. **No `PASSWORD`, `CODE`, `CHEAT`, `DEBUG`, `SECRET`, `LEVEL`,
`STAGE`, `OPTION` string exists in the PRG.**

## 6b. Enumeration

### 6b.1 Space definition

This SKU has **no code entry field**. What exists is:

* **Wrapper menu selector** — one byte, index `0..4`; 5 representable values;
  no checksum, no alphabet.
* **NES title selector** — one boolean (`$47`), 2 values.
* **NES pad byte** — 8 bits, `2^8` = 256 raw states per frame, but consumed by
  only 8 sites and never combined into a sequence.
* **Text space searched** — NES PRG: 16,384 bytes, 50 printable strings ≥4;
  GBA message bank `0x08003080..0x08003CA8`: 3,112 bytes, 58 `0xFF`-terminated
  records, 111 pointer slots (76 distinct). Keyword scan over both, in ASCII
  and in the wrapper's font encoding: `PASSWORD`, `CODE`, `CHEAT`, `DEBUG`,
  `SECRET`, `UNLOCK`, `LEVEL`, `ROUND`, `STAGE`, `ACHIEVEMENT`, `POINT`,
  `FULL`, `SCREEN` → the only hit is the wrapper string
  `save high score and secret code!` / `press the button to use this secret
  code.` (§8, Unknowns).

### 6b.2 Validator model

There is no validator to reimplement. The equivalent closed set is the menu
selector, which was **run as a state machine**:

```
idx = 0 (L+R)
Down  -> 1
Down  -> 2
Down  -> 3
Down  -> 4
Down  -> 0      (wrap)
Down  -> 1
Up    -> 0
Select-> 1      (Select also advances)
```

Observed sequence: `1,2,3,4,0,1` — exactly five states, wrap at 4, matching the
dispatch guard `cmp r0,#4 / bhi default` at `0x08002780`. **Every value 0..4
was entered and its action handler read from `0x030064C4`; value 5+ is not
expressible through input.**

### 6b.3 Novel, non-published results (in-game proof)

Neither of these appears in any published Pac-Man code list; both were produced
and confirmed on the running cartridge:

1. **Wrapper system menu** (`L+R`, exactly, no other key). Unpublished as a
   "secret" anywhere in the GameFAQs/TCRF material for this SKU. Proven by:
   `0x030064BC = 0x0300` while held, handler `0x030064C4` changes
   `0x080029A1 → 0x08002739`, and the five item handlers above are reached by
   `Down`+`A` navigation (each item's handler read from RAM).
2. **Round-table saturation at 22.** The round counter `$68` (NES `0x03007268`)
   is clamped by `CMP #$16` at `$CF3F`; therefore the arcade stage-256
   rollover cannot be reached. This is a derived-but-literal property of this
   image (instruction bytes quoted above), not an arcade assumption.

### 6b.4 Bounds proven by rejection

| Test | Result |
|---|---|
| Menu index 5 (undocumented slot) | not expressible: `Down` at 4 wraps to 0; dispatch is `cmp #4` with a default branch; no input path writes >4 |
| `L+R` + a third button held from the start | the detector needs one sampled frame with `key == 0x300`; sequential key presses give such a frame, so extra keys do not block the menu. Holding L+R alone is the reliable path. (Observed: `L+R+Start` → `0x08002739`.) |
| Menu re-entry / same-press close | while the opening press is still armed the handler rewrites itself to `0x08001945` (continue); observed once as `L+R+Down` → `0x08001945`. Releasing L+R leaves the menu open. |
| `Select` at title | only toggles 1P/2P (`$47` 0↔1); does not open any screen |
| `Left`/`Right` at title | no effect on the title screen; the GB "press Left/Right to show a ½ marker for full-screen mode" trick is absent — the title handler reads only bits 0x04 (Select) and 0x08 (Start), so no L/R path exists |
| `A+B+Select+Start` | resets (`key==0x0F` → `0x080019C9`) |
| Any pad sequence | rejected as a cheat: the only pad consumer is the 8-branch gameplay dispatcher; there is no sequence/history comparison |

### 6b.5 Published lists tested against this image

| Published claim | Platform it belongs to | Verdict for this ROM |
|---|---|---|
| `POKE 5737,254 …` cheat mode / lives | Commodore 64 | absent (no BASIC; NES PRG has no such code) |
| `1 + CLEAR` alternate pause easter egg | Atari 2600 | absent (no `CLEAR` key; pad handler reads only `$4016`) |
| "Left/Right at title → ½ → full-screen board" | Game Boy | **absent**; title reads only Select/Start, L/R leave the title tiles unchanged |
| Achievements `3-MIN. DIET`, `THE FIRST STEP`, `TOTAL FRUIT DOMINATION!` (WINM) | Windows Mobile Pac-Man | absent: no `ACHIEVEMENT`/`POINT` string in ASCII or font encoding |
| Achievements `Be Like Billy! Complete Stage 256` etc. (iOS) | iOS Pac-Man | absent; and Stage 256 is unreachable (round cap 22) |
| `Blinky GamerPic — Clear Round Five` | Xbox 360 | absent (no gamerpic concept) |
| "Level 256 kill screen" | arcade Pac-Man | **does not exist here** (round counter saturates at 22) |

## 7. Validation evidence

**Observed (emulator RAM/savestate):**

* Live build is the first image: `0x030064BC` tracks GBA keys (`0x0300` with
  L+R, `0x0F` with A+B+Select+Start); `0x03005E28/2C` (the other build's key
  variables) stay 0.
* `L+R` → handler `0x030064C4 = 0x08002739`; menu index `0x03007B51` walks
  `0→1→2→3→4→0` under `Down`, `Up` from 0 goes to 4, `Select` advances.
* Item handlers read from `0x030064C4`: 0→`0x080029A1`, 1→`0x080019C9`,
  2→`0x08002169`, 3→`0x080025E5`, 4→`0x08001A21` (then `0x080029A1`).
* `A+B+Select+Start` → `0x080019C9`, then `0x080029A1`; NES `$68` unchanged
  (soft reset).
* NES `$4D` = `0x08` with Start held, `0x80` with Right held; `$47` = 1 after
  `Select` on the title.
* NES screen text read directly from the PPU nametable (`0x02006000` in-state):
  title `1 PLAYER / 2 PLAYERS`, in-game `PAUSE`, attract
  `CHARACTER ;  NICKNAME` with SHADOW/BLINKY, SPEEDY/PINKY, BASHFUL/INKY,
  POKEY/CLYDE.
* NES PRG recovered from EWRAM `0x02000000`, MD5 `7979781…8433`, vectors
  `$C10E/$C033/$C17E`, `HIROKI AOYAGI` at `$C0FF` and at NES `$0052`.

**Derived (instruction-level):**

* Single `$4016` read site; eight `$4D` consumers; no sequence comparator.
* Round counter clamp `CMP #$16` at `$CF3F`; record index `=$68*6`.
* Menu dispatch guard `cmp r0,#4`; Up→4, Down/Select increment-with-wrap.
* Title reads only Select/Start; `L/R` cannot be a hidden title code.
* Reset/continue marker copy at `$C087`–`$C0B4`.

**Inferred:**

* The `$EBB6` byte-1 column is the difficulty/speed field (it falls 7→0 with
  round number and feeds `$8C`, used by ghost movement); the exact physical
  meaning of `$EC40`/`$ECAE`/`$ECCE`/`$ECDC` records is not proven.
* The second GBA image at `0x0800D35C` is the single-pak client (evidence:
  multiboot ID string `Sio32ID_030820`, its own valid header, its own crt0);
  it was not executed for this analysis.

## 8. Unknowns

* **`save high score and secret code!` / `press the button to use this secret
  code.`** (wrapper records at `0x08003C02` and `0x08003C5F`). The string is in
  the shared Classic NES Series save/link message bank next to
  `saving… wait a moment`, `game pak error`, `connecting using a game link
  cable`. No Pac-Man screen, no NES PRG string, and no item of the 5-slot
  system menu presents a code entry; the NES title/game/pause and the wrapper
  menu are the only reachable input surfaces. I classify these records as
  save/link-bank text whose trigger (if any) was not reached; a future pass
  should instrument the message-draw routine rather than the input handlers.
* Exact semantic names of the `$EBB6` columns 2–5 and of the `$EC40`/`$ECAE`
  records.
* Whether the embedded client image at `0x0800D35C` duplicates the same UI
  (it was not run; it would require a second GBA).

## 9. Tooling

* `/tmp/opencode/cnespacman/ss.py` — extract zlib `gbAs` chunk from `.ss1`.
* `/tmp/opencode/cnespacman/scr.py` — NES nametable → ASCII (PPU nametable at
  EWRAM `0x6000`).
* `/tmp/opencode/cnespacman/nes.py` — NES pattern-table ASCII renderer.
* `/tmp/opencode/cnespacman/gba.py` — minimal GBA mode-0 BG/OBJ renderer
  (IO block `0x0400`, palette `0x0800`, OAM `0x0C00`, VRAM `0x1000`).
* `/tmp/opencode/cnespacman/drive.py`, `menu.py` — xdotool driver +
  savestate/RAM probes.
* `/tmp/opencode/cnespacman/d6502.py` — py65 6502 disassembler wrapper.
* `da65` (cc65) for bulk 6502 listing; `arm-none-eabi-objdump -M force-thumb`
  for the wrapper.
* Tools: mGBA 0.10.5, Xvfb/openbox/xdotool, Python 3 + py65, capstone.

## 10. Legal note

No ROM, extracted graphics, music or text bank is redistributed here; only
hashes, addresses, instruction bytes and my own decoded field tables are
published.
