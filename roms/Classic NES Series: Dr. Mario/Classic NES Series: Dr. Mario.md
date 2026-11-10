# Classic NES Series: Dr. Mario (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Classic NES Series: Dr. Mario.gba` (1,048,576 bytes / 0x100000) |
| Header title | `DR. MARIO` |
| Game code / maker | `FDME` / `01` |
| Version | `0x00` |
| Entry word | `0xEA000033` → ARM at `0x080000D4` |
| Fixed `0xB2` | `0x96` (valid) |
| Complement byte `0xBD` | `0x78` — recomputed value is `0x78` (valid) |
| Header checksum `0xBE` | `0x0000` (rebuilt-header artifact, as in the other Classic NES Series dumps) |
| MD5 | `b63010010c4ad6877209b5cc41d368f2` |
| SHA-1 | `fc396f0eae55cf19e573aa322f525427e03d3854` |
| SHA-256 | `0c8e7923a5fbb99f1d8367ba96cf61cd09df4ebebe716bc2871de4bc4a934fe9` |

**Embedded-image scan.** Scanning the whole file for the 156-byte Nintendo logo found
exactly two GBA headers:

* `0x000000`: the main image (above).
* `0x01DE20`: a second, complete GBA header (`DR. MARIO`, `FDME`, logo at
  `0x01DE24`, entry `0xEA000061` → `0x081DFAC`). Its code is an SIO/multiboot
  slave: `0x081DF00` polls `[r0+8]`/`[r0]` for bits `0x80`/`0x40` (link handshake)
  and the multiboot header fields are at `0x081DEE0`–`0x081DEFC`
  (`0000 1100 00ea … 0000 2a00 00ea`). This is the single-pak link client image,
  not a second game.

**Patch/trainer check.** The first image is stock: entry branches to its own crt0,
and `0x080000C0` contains the wrapper signature
`08 05 19 24 "RMARIO_3" 08 05 19 24` (the same kind of 4-byte + 8-byte save/boot
signature the Bomberman Classic NES report found as `BOMBER_1`). No cracktro,
trainer menu, appended loader, or altered first-4-KiB code was found.

**Layout (file offsets).**

| Range | Content |
|---|---|
| `0x000000`–`0x017FFF` | GBA wrapper code/data (ARM crt0 at `0xC0`, Thumb code from `0x130`) |
| `0x018000`–`0x01DE1F` | wrapper-encoded/compressed NES payload (entropy 7.4–7.5; no plaintext) |
| `0x01DE20`–`0x03FFFF` | second GBA image = single-pak link (multiboot) client |
| `0x040000`–`0x0FFFFF` | filler: 16-bit quadratic ramp (`d(n) = −0x100·n`), not code/data |

## 2. Executive summary

**This SKU has no password system, no button-code cheat, no debug menu and no
unlockable.** The complete in-game cheat/selection surface is:

1. The **NES Dr. Mario game-select screen**: `VIRUS LEVEL` 0–20 (21 values),
   `SPEED` LOW/MED/HI (3 values), `MUSIC TYPE` FEVER/CHILL/OFF (3 values).
   All values are normal game options; the selector hard-clamps at both ends.
2. The wrapper's **System Menu** (L+R): 5 entries — `CONTINUE`, `RESET`,
   `LINKED PLAY`, `SAVE HIGH SCORE`, `SLEEP MODE`. `LINKED PLAY` is the only
   non-obvious entry, but it is the documented 2-player link setup (GameFAQs'
   guide lists exactly these five); it is hardware-gated, not a cheat.

A complete business-password alphabet/table/validator does not exist in either
the GBA image or the emulated NES image. There is also no multi-press key table:
43 code sites read the controller bytes and every mask is a single-button test.
The published "Select + Start = Dr. Mario" entry from a pirate-multicart list was
tested at the title, the game-select screen and the pause state; it does nothing
in this ROM (it belongs to a CoolBoy 198-in-1 multicart, not to Dr. Mario).

Per guide §0.2.5 this engagement is therefore closed as a **proven bounded
negative**: the menu space is enumerated, the text/button/table spaces are
bounded with counts, the published code is tested and rejected, and no
input-reachable value outside the published/document space exists.

The only values outside the menu's reachable set are implemented as **dead /
gated** code:

* NES level `21` (and `>21`): `$9E66`/`$B449` special-case it, the game runs it
  with 84 viruses and displays `LEVEL 21` (verified by an analysis-only RAM
  write), but the menu cannot select it (`$9B0E` stops at 20, `$999F` clamps on
  entry). The code routes to it from the post-level-20 progression
  (**inferred** from `$9E66`; the 20-level playthrough itself was not driven).
* NES 2-player screens (`1P`/`2P` virus-level screen at `$BF20`/`$BF46`) exist
  in the PRG but are link-gated; with one GBA the wrapper stays on a
  `CONNECTING...` overlay (`SIOCNT=0x600F`).

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL under `Xvfb :249` + `openbox`, `SDL_AUDIODRIVER=dummy`,
3× scale. Default SDL keymap: `x`=A, `z`=B, `a`=L, `s`=R, `Return`=Start,
`BackSpace`=Select. Savestates: `Shift+F1` save, `F1` load.

Menu path and keys:

| Screen | How to reach |
|---|---|
| Title / attract | boot, wait (or Start+Select+A+B resets to it) |
| NES game select | `Start` from the title (`$46` = 1) |
| `VIRUS LEVEL` change | cursor `$65`=0, `Left`/`Right` |
| `SPEED` change | `Down` once (`$65`=1), `Left`/`Right` |
| `MUSIC TYPE` change | `Down` twice (`$65`=2), `Left`/`Right` |
| Play | `Start` (`$46` = 4/8, HUD shows TOP/SCORE/LEVEL/SPEED/VIRUS) |
| Pause | `Start` during play (NES OAM buffer freezes) |
| Wrapper System Menu | `L`+`R` together, any time |
| System-menu cursor | `Up`/`Down` (ring 0..4) |
| Select entry | `A`; cancel = `B` or `Start` |
| Link setup | System Menu → `LINKED PLAY` → `A` (needs a second GBA) |

Reproduction of the system-menu labels from a savestate (no image files):

```
state gbAs offset 0x1000 = VRAM.  BG0: DISPCNT=0x1960, BG0CNT=0x8D04
  char base 0x4000, screen base 0x6800, 16-colour, 256x512, VOFS=192
tilemap entry at state 0x1000+0x6800+(row*32+col)*2
glyph tile = entry & 0x3FF, palette = (entry>>12)&0xF (1/2/3 normal, 9/10/11 selected)
8x8 4bpp tile at state 0x1000+0x4000+tile*32, colour index = nibble
pixel visible if its palette colour luminance is non-zero
```

This decodes rows 27/29/31/33/35 of the map to
`CONTINUE`, `RESET`, `LINKED PLAY`, `SAVE HIGH SCORE`, `SLEEP MODE`
(row 25 is the title `MENU`). The font packs **three glyph variants per tile**;
the tilemap palette selects the variant (normal rows 1/2/3, inverse-video
selection rows 9/10/11).

NES-side reproduction: the PRG is materialised in EWRAM. State offset `0x21000`
is EWRAM `0x02000000`, so **NES `$8000` ↔ GBA `0x02000000`**, and **NES RAM
$0000–$07FF is at GBA `0x03007200`** (state offset `0x20200`). Dump the PRG with
`state[0x21000:0x29000]` and disassemble with py65/6502. For dynamic 6502 work
an iNES image was rebuilt (32 KiB PRG + the 8 KiB block at state `0x29000` as
CHR); fceux reports CRC32 `0x7761D774`. That 8 KiB block does not decode as
standard NES 2-bpp CHR (the wrapper stores it in its own order), so fceux renders
the playfield with wrong graphics, but **all game logic, RAM and the
text/glyph-index encoding are correct**; NES text below
was read from the game's own encoding (`$0A–$23` = `A–Z`, `$00–$09` = `0–9`,
`$FF` = space), not from CHR.

## 4. Address map

### GBA wrapper (ROM addresses)

| Address | Meaning |
|---|---|
| `0x08000000`–`0x080000F0` | ARM crt0 (`entry 0x080000D4`); `RMARIO_3` signature at `0x080000C4` |
| `0x08000130`+ | Thumb wrapper code (input, script VM, menu) |
| `0x08001464`+ | wrapper GUI-script VM jump table (11 opcodes 0–10) |
| `0x080014BE` | script text opcode: glyph tile = byte + `0x1B9` |
| `0x080049F0` | `KEYINPUT` (0x04000130) read + complement to active-high |
| `0x08005CE0` | `KEYINPUT` read, `bics #0x3FF`, write to key shadow + `0x0400012A` |
| `0x0801DE20` | second GBA header (link client) |
| `0x0801DF00` | link-client SIO poll (`ldrh [r0,#8]`, bits 0x80/0x40) |
| `0x0801DFAC` | link-client entry |

### Wrapper RAM / registers observed

| Item | Address / value |
|---|---|
| System-menu selector (local) | `0x03007B69` — values 0..4, ring |
| Menu highlight | tilemap palettes 1/2/3 (normal) vs 9/10/11 (selected) |
| Font glyph base | VRAM `0x06007720`+ (tiles `0x1B9`–`0x1C8`) |
| Menu window map | VRAM `0x06006800`, visible map rows 25–35 |
| `DISPCNT` (menu) | `0x1960` |
| `BG0CNT` | `0x8D04`, `BG0VOFS`=192, `BG0HOFS`=0 |
| LINKED PLAY state | `SIOCNT=0x600F` (multiplayer, 16-bit), `CONNECTING...` overlay |
| SLEEP MODE state | `SIOCNT=0x2003` observed after selection |
| SAVE HIGH SCORE state | `IE=0x0000` in the sampled post-selection state, menu closes |

### NES image (NES addresses; runtime EWRAM offset = address − 0x8000 + 0x21000)

| NES address | Meaning |
|---|---|
| `$8000` | NMI handler (`LDA $FE; STA $2001; JSR $B7A2…`) |
| `$FF00` | reset (`CLD SEI LDX #0 … TXS … JMP $8000`) |
| `$B7E1` | controller poll (final); unused alternates `$B812`, `$B828`, `$B844` |
| `$8280` | virus count: `(min(level,20)+1)*4` → `$0328`; level 21 sets `$0728=1` |
| `$999F` | menu-entry clamp: if `$0316 ≥ 21` store `20` |
| `$9ADF` | level input handler (Right/Left, max `0x14`) |
| `$9B37` | speed input handler (Right/Left, max 2) |
| `$9B5C` | draw level/speed from `$96`/`$8B` |
| `$9E66` | level special cases: `==21` → `$9E81`, `>21` → `$9EF4` |
| `$B449` | if speed==2 and level==21 → `JSR $B459` (special sound) |
| `$A012` | 96-byte special table, index `speed*32+level` |
| `$A0F8` | per-speed table used by the level-21 path (`86 84 84`) |
| `$A2AE` | level digit tiles, 21 entries, stride 4 (`57 5B … A7`) |
| `$A2C9` | speed tiles (`58 80 A4`) |
| `$BDF0`–`$C1FF` | game-select screen templates (incl. `1P`/`2P` link screen) |

### NES RAM variables

| Address | Meaning |
|---|---|
| `$46` | screen/state (0 title, 1 select, 4/8 play, …) |
| `$96` | selected virus level (0..20) |
| `$8B` | selected speed (0=LOW, 1=MED, 2=HI) |
| `$65` | select-screen cursor row (0 level, 1 speed, 2 music) |
| `$0316` / `$0396` | player 1 / player 2 virus level |
| `$030B` / `$038B` | player 1 / player 2 speed |
| `$0727` | players (1 in this SKU's single-player path) |
| `$0731` | select-screen sub-row |
| `$5B` / `$5C` | new presses / held buttons |
| `$0724` / `$0725` | Virus-era options: pills stay in air / 2P win count (TCRF) |
| `$0740` / `$0741` | anti-piracy result / demo-recording flag (TCRF) |

## 5. Algorithm

### 5.1 NES game-select validator (the only "code-like" logic in the ROM)

```
; menu entry / return from a game  ($9961)
$999C: A = $0316
$999F: if A >= 21: A = 20; $0316 = A     ; hard clamp
       ...
; VIRUS LEVEL row  ($9ADF, held-repeat every 8 frames)
if Right and $96 != 0x14: $96 += 1       ; $9B0C..$9B1D
if Left  and $96 != 0x00: $96 -= 1       ; $9B25..$9B34
; SPEED row        ($9B37)
if Right and $8B != 2: $8B += 1
if Left  and $8B != 0: $8B -= 1
; draw             ($9B5C)
$44 = $A2AE[$96]      ; level digit tile
$44 = $A2C9[$8B]      ; speed text tile
; start
$0328 = (($0316 < 21 ? $0316 : 20) + 1) * 4    ; virus count
```

The reachable level set is therefore exactly `{0..20}`; `21` is a sentinel used
after clearing level 20 (`$9E66`, `$B449`) and is not selectable.

### 5.2 Wrapper System Menu

```
if (KEYINPUT & 0x300) == 0x300: open menu, i = 0
Up:   i = (i + 4) % 5
Down: i = (i + 1) % 5
A:    dispatch(i)
B/Start: close, resume
```

Observed dispatch:

| i | Label | Effect |
|---|---|---|
| 0 | CONTINUE | close menu, resume NES |
| 1 | RESET | close menu, NES soft-reset to title |
| 2 | LINKED PLAY | `CONNECTING...` overlay, `SIOCNT=0x600F`; needs 2nd GBA; `B` cancels |
| 3 | SAVE HIGH SCORE | close menu, SRAM write (sampled with `IE=0`) |
| 4 | SLEEP MODE | close menu, `SIOCNT=0x2003` |

## 6. Tables

**NES level digits (`$A2AE`, 21 entries, stride 4):**
`57 5B 5F 63 67 6B 6F 73 77 7B 7F 83 87 8B 8F 93 97 9B 9F A3 A7` (0..20).

**NES speed tiles (`$A2C9`):** `58 80 A4` (LOW/MED/HI).

**NES special table `$A012` (96 bytes, `speed*32 + level`), nonzero entries:**

| speed | level | value |
|---|---|---|
| 0 (LOW) | — | none |
| 1 (MED) | 6, 11, 16, 21 | 7, 5, 6, 8 |
| 2 (HI) | 6, 11, 16 | 2, 1, 4 |

**Wrapper System Menu entries:** 5, listed above.

**Published Dr. Mario codes checked against this SKU:**

| Published item | Source | Result in this ROM |
|---|---|---|
| `Select + Start` = Dr. Mario | cah4e3 "mostly unpublished NES cheats" — it is the hidden game on a CoolBoy 198-in-1 multicart | no effect at title, select screen, or pause; not a Dr. Mario code |
| Game Genie `EAAOUT`, `ENLEUG`, `IXPAGZ`, `GOALOK`, `TELAEI`, `YUPAEY` | community Game Genie lists | **out of scope**: memory-edit codes; the RAM bits they patch (`$724`, `$725`) exist and are unused UI toggles |
| Classic NES Series system menu (`CONTINUE`, `RESET`, `LINKED PLAY`, `SAVE HIGH SCORE`, `SLEEP MODE`) | GameFAQs guide 41707 | all five reproduced from ROM and by input |

## 6b. Enumeration

### Space 1 — wrapper System Menu
* Domain: `{0,1,2,3,4}`, one per drawn label.
* Proof of bounds: `Down` six times from 0 gives selector
  `1,2,3,4,0,1`; `Up` twice from 4 gives `0,4`. The selector byte at
  `0x03007B69` is the only byte in the state that is `0/1/2` across the three
  cursor savestates (state-wide search).
* No undocumented slot exists. Pressing `Select`, `L`, or `R` in the menu does
  nothing; `B` and `Start` cancel; `A+L`, `A+R`, `A+Select`, `A+Start` behave
  exactly like `A`.
* Novel state: none; `LINKED PLAY` is documented and hardware-gated.

### Space 2 — NES game-select
* Level `0..20` (21), speed `0..2` (3), music `0..2` (3) → **189** combinations.
* In-GBA RAM proof of bounds (NES RAM base `0x03007200`):

| Input | `$96` level | `$0316` | `$8B` speed | `$030B` |
|---|---|---|---|---|
| Right ×25 | `0x14` (20) | `0x14` | 1 | 1 |
| Right ×5 more | `0x14` (rejected) | `0x14` | 1 | 1 |
| Left ×30 | `0x00` (0) | `0x00` | 1 | 1 |
| Left ×5 more | `0x00` (rejected) | `0x00` | 1 | 1 |
| Down, Right ×6 | 0 | 0 | `0x02` (HI) | `0x02` |
| Right ×3 more | 0 | 0 | `0x02` (rejected) | `0x02` |
| Left ×6 | 0 | 0 | `0x00` (LOW) | `0x00` |

* Level 20 start: `$96=$0316=0x14`, HUD `LEVEL 20`, `VIRUS 84`.
  Level 0 start: `LEVEL 00`, `VIRUS 04` — matches `(level+1)*4`.
* `MUSIC TYPE` is a third cursor row (options FEVER/CHILL/OFF); it does not
  change level/speed and is a normal option.

### Space 3 — button codes
* 43 code sites read `$43`, `$5B` or `$5C` followed by `AND`/`CMP` with a
  constant; every constant is a direction/button mask no larger than `0x80`
  (`#1`, `#2`, `#3`, `#4`, `#7`, `#8`, `#0F`, `#10`, `#40`, `#80`). There is no
  sequence table, no progress counter and no "match N presses" loop.
* The only hold/repeat logic is the select-screen auto-repeat (`$93` timer,
  8 frames) for Left/Right.
* Tested published sequence: `Select+Start` at the title, select screen and
  pause — screen/state unchanged (`$46`, nametable row 5 unchanged).

### Space 4 — passwords
* GBA image: 10,826 ASCII runs ≥4 bytes; **0** case-insensitive hits for
  `password`, `cheat`, `debug`, `secret`, `unlock`, `level`, `speed`, `virus`,
  `code`, `menu`, `pause`, `sound`.
* NES PRG: 32,768 bytes; the game's glyph text was decoded; it contains the
  normal labels (`1 PLAYER GAME`, `VIRUS LEVEL`, `SPEED`, `MUSIC TYPE`,
  `FEVER`, `CHILL`, `OFF`, `LEVEL`, `VIRUS`, `TOP`, `SCORE`, `DRAW`,
  `GAME OVER`, `STAGE CLEAR`, `TRY NEXT`, `CONGRATULATIONS`) and **no**
  `PASSWORD`, `SOUND TEST`, `DEBUG`, `LEVEL SELECT`, `CHEAT` or `SECRET`.
  There is no alphabet, no length check, no checksum and no string comparison
  against user text in the PRG.

### Space 5 — dead / gated code (evidence, not a cheat)
* `$9E66` treats level 21 specially (`==21` → `$9E81`; `>21` → `$9EF4`), and
  `$B449` special-cases level 21 at HI speed. The menu clamp makes 21
  unreachable from input. **Analysis-only proof** (fceux, RAM write to `$96`/
  `$0316` = 21, clearly not an in-game cheat): the game starts and its HUD reads
  `LEVEL 21` / `VIRUS 84`, i.e. the level-21 path is live code, not a dummy.
  The code routes to it from the post-level-20 progression (**inferred** from
  `$9E66`); no 20-level playthrough was driven.
* The 2-player select screen templates (`1P`/`2P` rows at `$BF23`/`$BF46`,
  `VIRUS LEVEL`, `SPEED`) are in the PRG, but the wrapper's `LINKED PLAY` path
  stops at `CONNECTING...` without a second GBA (`SIOCNT=0x600F`, `B` cancels).

## 7. Validation evidence

**Observed (emulator / RAM):**
* Boot, title, NES select (`LEVEL 00`, `VIRUS 04`), HUD, pause, System Menu,
  `LINKED PLAY` → `CONNECTING...`, `B` cancel — all reproduced on `:249`.
* NES RAM in GBA IWRAM at `0x03007200`: gameplay state shows
  `$46=8`, `$96=$0316=0x14`, `$8B=$030B=1`, `$0727=1`.
* Pause: over 2 s paused the NES RAM changed 3 bytes (timer) and the OAM buffer
  (`$0200–$02FF`) changed 0 bytes; unpaused over 2 s it changed 268 / 144 bytes.
* System-menu selector cycles `0..4` and wraps; `LINKED PLAY` sets
  `SIOCNT=0x600F`; `SLEEP MODE` leaves `SIOCNT=0x2003`; `SAVE HIGH SCORE`
  closes the menu with `IE=0`.
* Level 20 start (GBA) reads `$96=$0316=0x14`; level 0 start reads `0`.

**Derived (instruction sequence):**
* Level clamp `$999F` and the `$9B0E`/`$9B27`/`$9B3F`/`$9B52` input limits.
* Virus count formula `$8280`.
* Level-21 special paths `$9E66`/`$B449`.
* Wrapper menu dispatch and 5-entry ring.

**Inferred:**
* The second GBA header at `0x01DE20` is the single-pak link client (SIO poll,
  multiboot fields); its exact end offset is bounded by the filler at `0x40000`.
* `SLEEP MODE` enters the GBA stop/sleep state; only the `SIOCNT=0x2003`
  register change was observed, not the LCD-off event.
* The `0x3236–0x3999` wrapper text bank is the wrapper's own link help text
  (glyph indices, not a code table); words such as `YOU`, `CAN`, `ALSO`,
  `PLAY`, `USING` are readable under the script-VM glyph bias, but the whole
  bank was not needed for the conclusions.

## 8. Unknowns

* The exact copy path between the menu variable `$96` and the play variable
  `$0316` was not located as a single instruction; both were observed to track
  each other in the menu and at game start (GBA RAM table in §6b), and the
  clamp is applied to `$0316` at menu entry.
* The exact `$0727` semantics (1 vs 2 players) are inferred from the 1P-only
  UI; the 2-player path is hardware-gated by the link cable.
* The post-link 2P level range (the `$B2D9` wait loop increments `$0316` up to
  `0x18` = 24) is bounded to the link-gated code path; it is not a claim about
  a reachable range.
* The wrapper's compressed NES payload at `0x18000` was not decompressed; the
  runtime EWRAM image was used as ground truth (same method as the Bomberman
  report).

## 9. Tooling

* `mgba` 0.10.5 (SDL), `Xvfb :249`, `openbox`, `xdotool` for input.
* Custom savestate parser: PNG `gbAs` chunk → zlib → 397,312-byte state;
  `io` at `0x400`, palette `0x800`, OAM `0xC00`, VRAM `0x1000`,
  IWRAM `0x19000`, EWRAM `0x21000` (mGBA 0.10.5 `serialize.h` layout).
* `/tmp/opencode/cnesdrmario/mgdaemon.py` + `mgc.py` (mGBA `-d` pty bridge),
  `st.py` (state loader/diff), `keys.py` (Xvfb key + F1/Shift+F1), `screen.py`
  / `rowtext.py` (VRAM tilemap → text), `comp.py` (BG compositor).
* `fceux` 2.6.5 with Lua for NES RAM and nametable reads.
* py65 for 6502 disassembly of the EWRAM PRG; `arm-none-eabi-objdump` for the
  ARM/Thumb wrapper.
* iNES reconstruction: `NES\x1a`, 2×16 KiB PRG, 1×8 KiB CHR, mapper 0; fceux
  CRC32 `0x7761D774`.

No ROM, graphics or text assets are redistributed in this report.
