# Classic NES Series: Zelda II: The Adventure of Link (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Classic NES Series: Zelda II: The Adventure of Link/Classic NES Series: Zelda II: The Adventure of Link.gba` |
| Size | 1,048,576 bytes (`0x100000`) |
| Header title | `NES ZELDA 2` (`0xA0`–`0xAB`) |
| Game code | `FLBE` (`0xAC`–`0xAF`) |
| Maker | `01` (`0xB0`–`0xB1`) |
| Version | `0x00` (`0xBC`) |
| Header complement | `0x0F` (`0xBD`; calculated value also `0x0F`) |
| Stored header checksum | `0x0000` (`0xBE`–`0xBF`) |
| Calculated header checksum | `0xE221` (mismatch: rebuilt header, normal for this wrapper family) |
| Entry word | `0xEA000033` → ARM branch to `0x080000D4` |
| MD5 | `c0a26ae6d6bc38e07f87c9a860de8586` |
| SHA-1 | `22ea42ad9a99a6bc0fcba8721cf8f484f68c3bf7` |
| SHA-256 | `732560be6c6957b809c9cc821d0f03c3842c61af220c0a61dc77ffb0f695e862` |

Phase 0 notes:

* Exactly one Nintendo logo occurs, at file offset `0x4`. There is no second GBA
  header, so this is a single-image cart, not a multi-game pack.
* The header is rebuilt: stored checksum `0x0000`, complement `0x0F`, entry
  branches to `0x080000D4` instead of `0x080000C0`. Bytes at `0x080000C0` are
  `08 05 19 24 5A 45 4C 44 41 32 5F 31 08 05 19 24 6B 61 61 65` — a build
  stamp (`08 05 19 24`, `ZELDA2_1`, repeat, `kaae`), not a scene cracktro.
* No trainer, cracktro, or appended trainer menu was found. A case-insensitive
  scan of the GBA image for `sunhors|mode7|crc bandit|trainer|gameshark|codebreaker|action replay`
  returns nothing.
* This is an **emulated NES game**. The 128 KiB NES PRG is not stored in plain
  form in the GBA image: 0 of 512 sampled 16-byte slices of the runtime PRG
  occur anywhere in the 1 MiB file. The GBA image is 128 KiB of ARM wrapper
  code (`0x0`–`0x20000`), a 512 KiB region at `0x20000`–`0xA0000` whose bytes
  use only 16 values (2bpp tile/CHR art), and a high-entropy 384 KiB region
  from `0xA0000` (entropy 8.0 — compressed NES payload/audio).
* Ground truth is therefore the runtime NES image taken from an mGBA savestate:
  **128 KiB PRG at EWRAM `0x02000000`**, vectors at `0x0201FFFA`–`0x0201FFFF`
  = reset `$C07B`, NMI `$FF70`, IRQ `$FFF0`.

## 2. Executive summary

This SKU is the NES *Zelda II: The Adventure of Link* running inside the
Classic NES Series wrapper. Every developer-intended input surface was walked
and RAM-verified; the report reaches a **bounded negative** on the widely
repeated "name changes your starting stats" claim, and fully enumerates the two
real menu surfaces:

1. **The NES name-registration field is a label, not a validator.** The entry
   screen offers 38 symbols (`A`–`Z`, `?`, `.`, `0`–`9`), stores eight cells at
   SRAM `$602C + slot*0x32`, pads with `$F4`, and never compares the name to a
   constant. A new file's Attack/Magic/Life always come from the fixed table
   `bank5_Beginning_Values` at CPU `$BAE3` (`01 01 01 …`), copied to
   `$0777`–`$0779` at `$B2CC`. Controlled runs: name `ZELDA` → levels `01 01 01`;
   name `A8C` (a digit-bearing, unpublished spelling) → levels `01 01 01`. The
   encoded string `ZELDA` occurs once in the PRG, inside ending/story text at
   CPU `$A989`, not in a comparison; there are **zero** `CMP #<letter>` sites
   against the five name codes. The "ZELDA name" cheat is Zelda 1's second quest
   (different SKU), not this game.

2. **The wrapper System Menu (hold L+R)** is a real three-slot developer menu
   in ARM code, not 6502 code. Gate: `held == 0x0300` exactly plus a fresh L/R
   edge on word `0x030067C8`; any extra button held first is rejected
   (`0x0304`, `0x0308`, `0x0340`, `0x0380` all stay closed). Selector is a
   three-slot ring at IWRAM `0x03007B15` (`0→1→2→0`, Down forward, Up reverse).
   Slot 0 resumes, slot 1 resets the emulated NES, slot 2 runs the
   `0x0800376D → 0x08003729` transition and returns to gameplay after ~60
   frames. The page geometry and text tilemaps are documented in §4/§6.

3. **The published GBA "Quicksave" is verified and its UI fully enumerated.**
   Start, then Select+Up simultaneously, opens a two-option `CONTINUE / SAVE`
   menu. Select moves the cursor (Up/Down do not), Start confirms, B does not
   cancel. `CONTINUE` resumes; `SAVE` writes battery SRAM and resets to the
   title. Select+Up without a preceding Start does nothing.

4. **The four-button reset `A+B+Select+Start` is a second wrapper-level input.**
   Held word `0x000F` installs the same reset handler as System Menu slot 1
   (`0x080036D1`), drives NES frame counter `$15` to 0 and clears `$0777`–`$0779`.
   It is not on the GameFAQs GBA cheat page.

5. **New Game Plus** (the little triangle on a completed file) is a gated
   unlockable: `$07A0 == 1` marks the new-game-plus load path at `$B2BC`, which
   re-applies the beginning stats. It requires finishing the game and was not
   triggered; it is reported as a gated unlockable, not as a live result.

There is no password system, no code table, and no debug menu in the NES game.
A GBA-side `strings` scan is meaningless for this SKU (all keyword counts zero
because the NES payload is compressed); the negative rests on the decoded
runtime PRG scan and the full menu walk.

## 3. How to reproduce

### Emulator and keymap

* mGBA 0.10.5 SDL, `Xvfb :257` + `openbox`, `SDL_AUDIODRIVER=dummy`.
* Keymap: **A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrows**.
* Evidence was read from mGBA savestates (`Shift+F1`): the PNG `gbAs` chunk is
  zlib-compressed; for this 1 MiB ROM the 397,312-byte state has VRAM at
  `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000`. No screenshots were used.
* NES RAM is at IWRAM `0x03007200` (`$0000`–`$07FF`); NES battery SRAM is at
  EWRAM `0x02030000` (`$6000`–`$7FFF`); the 128 KiB NES PRG is at EWRAM
  `0x02000000`.

### Game menu path

1. Boot. Title screen. Press **Start** → file-select screen (`SELECT`,
   `REGISTER YOUR NAME`, `ELIMINATION MODE`).
2. On the file-select, **Select** cycles the fairy cursor (`$19`: 0,1,2 slots,
   3 = REGISTER, 4 = ELIMINATION). Put it on REGISTER and press **Start**.
3. Name-entry screen (`== REGISTER YOUR NAME ==`, the `END` row, the alphabet
   grid). The cursor is the fairy at `$1F` (column) and `$20` (row); **A** writes
   the highlighted symbol to the name and advances the eight-cell ring `$1E`.
4. **Select** cycles the name target `$19` 0→1→2→3; at `$19 == 3` press **Start**
   to finish. The screen returns to file-select with the name and `LEVEL 1 1 1`.
5. Press **Start** on the file to start the game. Live levels are
   `$0777/$0778/$0779` = Attack/Magic/Life.

### Name test (the negative)

* `ZELDA`: type `Down,Down,Right,Right,Right,A; Up,Up,Right,A;
  Down,Left,Left,Left,Left,A; Up,Right,Right,Right,A; Left,Left,Left,A`.
  SRAM `0x0203002C` = `F3 DE E5 DD DA F4 F4 F4`; live `$777`–`$779` = `01 01 01`.
* Control `A8C`: entered through the same grid (`A`, a digit from the bottom
  row, `C`); the observed SRAM name was `DA D8 DC F4 F4 F4 F4 F4` and the live
  levels were `01 01 01`. The exact cursor path is not needed to reproduce the
  result: any spelling other than the published `ZELDA` yields the same fixed
  beginning-values copy.

### Quicksave path

1. In game: press **Start** (pause/status), then hold **Select+Up** together for
   ~0.5 s, release. A two-line `CONTINUE / SAVE` menu appears.
2. **Select** toggles the cursor between CONTINUE and SAVE (Up/Down do nothing).
   **Start** confirms. **B** does not cancel.
3. CONTINUE resumes the game. SAVE writes the battery save and resets to title.

### Wrapper System Menu path

1. In game or at the title: hold **L+R** exactly (`held = 0x0300`) for ~0.5 s and
   release. The menu handler `0x08003959` is installed at IWRAM `0x03006730`
   (and `0x030067D0`).
2. **Down** advances selector `0x03007B15` 0→1→2→0; **Up** reverses. The
   handler also maps **Select** onto the same increment (derived from the
   `AND #0x84` branch at `0x08003A12`). **B** closes; **L+R** also closes.
3. **A** or **Start** activates the current slot.
4. Holding any extra button *before* L+R (Start, Down, Up, Select) leaves the
   menu closed.

## 4. Address map

### GBA / wrapper

| Address / offset | Meaning |
|---|---|
| File `0xC0`–`0xD3` | build stamp `08 05 19 24` + `ZELDA2_1` + repeat + `kaae` |
| `0x080000D4` | ARM wrapper entry (branch target of `0xEA000033`) |
| EWRAM `0x02000000`–`0x0201FFFF` | runtime NES PRG, 128 KiB (savestate offset `0x21000`) |
| EWRAM `0x02030000`–`0x02031FFF` | NES battery SRAM `$6000`–`$7FFF` (name area `$602C`; second copy `$7400` region) |
| IWRAM `0x03007200`–`0x030079FF` | NES internal 2 KiB RAM (`$0000`–`$07FF`) |
| `0x03007200` | wrapper state struct base (`r4` in the ARM handlers); same base as NES RAM |
| `0x030067C8` | wrapper held-key word, active high (L=0x200, R=0x100, Start=0x08, Select=0x04, Down=0x80, Up=0x40, A=0x01, B=0x02) |
| `0x03006730` / `0x030067D0` | current handler pointer (updated together): in-game `0x08003AAD`, menu `0x08003959` |
| `0x03007B15` | System-Menu selector (3-slot ring) |
| `0x03007B0C` | wrapper menu tilemap pointer (`0x06006E00` while the menu is open) |
| `0x08003958` | **System-Menu handler** (`0x08003959`, Thumb): B/L+R close, selector move, slot dispatch |
| `0x08003AAC` | **in-game handler** (`0x08003AAD`): reset gate + L+R menu gate |
| `0x0800364C` | slot 0 page/action (`0x0800364D`) → resume via `0x080035EC` |
| `0x080036D0` | slot 1 page/action (`0x080036D1`) → reset path |
| `0x0800376C` | slot 2 page/action (`0x0800376D`) → `0x08000364`, then `0x08003729` |
| `0x08004A98` | page table, 8-byte records `{x,y,w,h,script_ptr}` |
| `0x08004A98 + 8*8` | page 8 (slot 2 page), script `0x08004060` |
| `0x08004A98 + 8*11` | page 11 (slot 1 page), script `0x080040CD` |
| `0x08004A98 + 8*12` | page 12 (slot 0 page), script `0x080044F0` |
| `0x0800314C` | page draw dispatcher (`r1` = page id) |
| `0x08002FF8` | page text/tilemap writer |
| `0x08000268` | reset helper used by the slot-1 action |
| `0x08000364` | display/transition helper used by the slot-2 action |

### NES 6502 (bank n at file `n*0x4000` ↔ CPU `$8000`; fixed bank at file `0x1C000` ↔ CPU `$C000`)

| NES address | PRG file offset | Meaning |
|---|---|---|
| `$B23C` | `0x1723C` | name pointer table: `$602C`, `$605E`, `$6090` (slots 0–2) |
| `$B2CC` | `0x172CC` | new-file copy: `bank5_Beginning_Values` → `$0777,Y` |
| `$B678` | `0x17678` | file-select/sub-state: Start advances registration (`$073B++`) |
| `$B711`–`$B725` | `0x17711`–`0x17725` | name-position ring: `INC $1E`, wrap at 8 |
| `$B892`–`$B8C2` | `0x17892`–`0x178C2` | name write: `LDA $BD75,X; STA ($00),Y` into SRAM name |
| `$B8CF` | `0x178CF` | `JMP $CF05` (increment game mode) |
| `$BAE3` | `0x17AE3` | `bank5_Beginning_Values`: `01 01 01 00 … 04 04 … 06 … F4×8` |
| `$BD75` | `0x17D75` | name alphabet table: A–Z (`DA`–`F3`), `F6` = `?`, `CF` = `.`, `D0`–`D9` = digits, `F4` = space |
| `$BD00` | `0x17D00` | name-entry screen PPU script (`22 46 15 …`) |
| `$BC78` / `$BCC7` | `0x17C78` / `0x17CC7` | `REGISTER YOUR NAME` text |
| `$A989` | `0x16989` | story-text `ZELDA` (not a validator) |
| `$C000` | `0x1C000` | fixed bank: save/load, file-select, name display |
| `$FFFA` | `0x1FFFA` | 6502 vectors: reset `$C07B`, NMI `$FF70`, IRQ `$FFF0` |

### NES RAM evidence

| Address | Meaning |
|---|---|
| `$12` | game-mode/state byte (e.g. `1` selection, `5` normal) |
| `$15` | frame/substate counter (0 after a reset) |
| `$19` | fairy cursor / file slot index (0–4) |
| `$1E` | name-input position ring (0–7) |
| `$1F` / `$20` | name-input cursor column / row |
| `$305`–`$30C` | name-entry display row / live name cells |
| `$777` / `$778` / `$779` | Attack / Magic / Life level |
| `$07A0` | New Game Plus flag (1 = new-game-plus load path) |
| `$602C + slot*0x32` (SRAM) | 8-byte player name, `$F4` padded |

## 5. Algorithm

### 5.1 Name field (no validator)

```
; file-select / registration, CPU $B2CC (new file)
LDY #$29
loop:
  LDA bank5_Beginning_Values,Y    ; fixed 30-byte template at $BAE3
  STA $0777,Y                     ; Attack/Magic/Life/items
  DEY
  CPY #$0C
  BCS loop

; name entry, CPU $B711
if (pressed & 0xC0) {             ; A or B edge
  pos = (pos + 1) & 7;            ; eight-cell ring
}
; CPU $B892
if (pressed & 0x80) {             ; A edge
  Y = (pos == 0) ? 8 : pos - 1;
  ptr = name_pointer[$19];        ; $602C/$605E/$6090
  ptr[Y] = alphabet[row*11 + col]; ; $BD75
}
```

`bank5_Beginning_Values` is `01 01 01 00 00 00 00 00 00 00 00 00 04 04 … 06 …
F4 F4 F4 F4 F4 F4 F4 F4`. The copy length is 30 bytes (`Y = 0x29..0x0C`).
Nothing in this path reads the name, so the name cannot influence starting
stats. The name is written straight to SRAM and later rendered; it is also used
as dialogue text (the King/townspeople address Link by name), which is why a
literal `ZELDA` exists in story text.

### 5.2 Wrapper System-Menu gate and dispatch

```c
// 0x08003AAC, in-game handler
held    = *(u16*)0x030067C8;      // active-high held word
pressed = *(u16*)0x030067CC;      // newly-pressed/edge word used with held

if (held == 0x000F) {             // A+B+Select+Start exactly
    handler = 0x080036D1;         // reset path
}
else if (held == 0x0300 && (held & pressed)) {
    handler = 0x08003959;         // open System Menu
}

// 0x08003958, System-Menu handler
if (pressed & 0x02) handler = resume_action;          // B closes
if (held == 0x0300 && (held & pressed)) handler = resume_action; // L+R closes
switch (sel = *(u8*)0x03007B15) {                     // 3-slot ring
case 0: page = 12; action = 0x0800364D; break;        // resume
case 1: page = 11; action = 0x080036D1; break;        // reset
case 2: page = 8;  action = 0x0800376D; break;        // transition
}
draw_page(state, page);
```

Selector movement: `held & 0x80` (Down) → `sel = (sel+1) % 3`; `held & 0x40`
(Up) → `sel = (sel+2) % 3`; `held & 0x04` (Select) also advances. Activation is
`pressed & 0x09` (A or Start). The gate is exact: the L/R edge must occur while
the held word equals `0x0300`, so `L+R+Start` etc. are rejected if the extra
button was already down.

### 5.3 Quicksave menu

```
if (pressed & Start) { /* NES pause/status */ }
if (held == (Select|Up) after Start) open CONTINUE/SAVE menu;
menu: Select toggles cursor; Start confirms; B is ignored;
      CONTINUE -> resume; SAVE -> write SRAM, NES reset to title
```

The NES-side code is the game-over/save screen (`$C3ED` timer path, `$CA85`
Start/Select edge logic); the GBA wrapper adds the Start+Select+Up shortcut.
`SAVE` was observed to update the battery save and reset the NES (see §7).

## 6. Tables

### 6.1 Name alphabet (`$BD75`, 38 usable symbols)

```
A B C D E F G H I J K L M N O P Q R S T U V W X Y Z ? . 0 1 2 3 4 5 6 7 8 9
DA DB DC DD DE DF E0 E1 E2 E3 E4 E5 E6 E7 E8 E9 EA EB EC ED EE EF F0 F1 F2 F3 F6 CF D0 D1 D2 D3 D4 D5 D6 D7 D8 D9
```

Screen grid: row 0 `A–K`, row 1 `L–V`, row 2 `W X Y Z ? .` (six cells),
row 3 `0–9` (ten cells); 11 columns, 4 rows. Space/padding is `$F4`; the
name-entry cursor/display marker is `$FA`/`$1B9` depending on layer.

### 6.2 Save record / beginning values

`bank5_Beginning_Values` (`$BAE3`, 30 bytes):

```
01 01 01 00 00 00 00 00 00 00 00 00 04 04 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 06 00 00
00 00 00 00 00 00 00 00 00 00 F4 F4 F4 F4 F4 F4
F4 F4
```

Mapping into live RAM: `$777=01` (Attack), `$778=01` (Magic), `$779=01`
(Life), `$783/$784=04 04`, `$78A=06`, name padding at the tail.

Name slots (SRAM): `$602C` (slot 0), `$605E` (slot 1), `$6090` (slot 2), each
8 bytes, stride `0x32`. Writing a name never changes another slot.

### 6.3 Wrapper System-Menu slots

| Selector | Page | Action address | Observed effect |
|---:|---:|---|---|
| 0 | 12 (`script 0x080044F0`) | `0x0800364D` → `0x080035EC` → `0x08003AAD` | resume gameplay |
| 1 | 11 (`script 0x080040CD`) | `0x080036D1` → `0x08000268` | reset emulated NES; `$15` 112→0; `$777-$779` 01→00 |
| 2 | 8 (`script 0x08004060`) | `0x0800376D` → `0x08003729` (~60 frames) → `0x08003AAD` | display transition, then resume; `$15` unchanged (112); no SRAM write |

The panel text is a proportional tile font written to the wrapper tilemap at
`0x06006E00`. With selector 0 the three rows are (tile indices, cursor tile
`0x1B9` in bold position):

```
row5: 1C0 1C7 1C4 1C2 1C6 1C4 1C4 1BF   (8 cells; item 1)
row7: 1C0 1BF 1BE 1BF 1C2               (5 cells; item 2)
row9: 1BE 1C7 1BF 1BF 1C8 1C5 1C7 1BF 1BF (9 cells; item 3)
```

The `0x1B9` cursor moves between these rows as `0x03007B15` changes (0→row5,
1→row7, 2→row9). The English labels are rendered from this tile font and were
not decoded; the behaviors above are the verified identities. Slot 2 matches
the wrapper's sleep/display-off path (`0x08003729` timer then `0x0800374D`).

## 6b. Enumeration

### Space definition

* **Name field**: alphabet 38, length 8, no checksum, no range/validator.
  Representable spellings: `38^8 = 4,347,792,138,496` (≈4.35×10¹²). The name is
  a display/dialogue label; all spellings are behaviorally equivalent for
  stats. The eight cells are padded to eight with `0xF4`; the position ring
  wraps at eight (`$B711`–`$B725`), so no ninth cell exists.
* **System Menu**: 3 selector values; 3 action handlers; exact L/R gate.
* **Quicksave**: 2 options (`CONTINUE`, `SAVE`); navigation key Select only;
  confirmation Start; no cancel path.
* **Reset input**: one exact 4-button chord (`held == 0x000F`).

### Novel, unpublished inputs (verified in the emulator)

1. **`A8C` name** — a digit-bearing spelling absent from every published list
   (GameFAQs only documents `ZELDA` for Zelda 1). Entered on the real name-entry
   screen; SRAM `0x0203002C` read `DA D8 DC F4 F4 F4 F4 F4`; the file started
   and live `$777`–`$779` read `01 01 01` (Observed).
2. **`A+B+Select+Start` reset chord** — not listed on the GameFAQs GBA page.
   Held word `0x000F` installed `0x080036D1`; NES `$15` went 112→0 and
   `$777`–`$779` went `01 01 01`→`00 00 00` (Observed).
3. **`L+R` System Menu** (gate + three slots) — not listed for this SKU;
   handler `0x08003AAD`→`0x08003959`, selector ring `0x03007B15`, all three
   slots walked (Observed).

### Bounds proven by rejection

* `L+R+Select` held first → held `0x0304`, handler stays `0x08003AAD`.
* `L+R+Start` held first → held `0x0308`, handler stays `0x08003AAD`.
* `L+R+Up` held first → held `0x0340`, handler stays `0x08003AAD`.
* `L+R+Down` held first → held `0x0380`, handler stays `0x08003AAD`.
* `Select+Up` without a preceding Start → no quicksave menu (`SAVE` text absent).
* `B` inside the quicksave menu → menu remains (no cancel path).
* Name field: no out-of-range value exists (38-symbol fixed grid, 8 cells);
  the negative is bounded by the zero-hit search for a validator (§7), not by a
  failed input.

### Published-list check

* GameFAQs GBA `Quicksave` (Start, then Select+Up) — verified verbatim; the
  options and their effects were enumerated beyond the published text.
* GameFAQs GBA `New Game Plus` — code path verified at `$07A0`/`$B2BC`; not
  triggered because it requires a completed game.
* GameFAQs NES Game Genie codes — memory-edit codes, out of scope; none are
  in-game inputs.
* No published password/name code for this SKU exists to test; the `ZELDA`
  name stat claim is a Zelda 1 behavior, disproved here.

## 7. Validation evidence

**Observed (emulator RAM / SRAM reads):**

* `ZELDA` registration: SRAM `$602C` = `F3 DE E5 DD DA F4 F4 F4`; file-select
  row shows `ZELDA` and `LEVEL 1 1 1`; live `$777/$778/$779` = `01 01 01`.
* `A8C` registration: SRAM `$602C` = `DA D8 DC F4 F4 F4 F4 F4`; live
  `$777/$778/$779` = `01 01 01`.
* System Menu: `L+R` held `0x0300` → handler `0x08003959`; selector
  `0x03007B15` stepped `0→1→2→0` with Down and `2→1→0` with Up; B or L+R closed
  (handler `0x08003AAD`); slot 0 resumed; slot 1 drove `$15` 112→0 and cleared
  stats; slot 2 ran `0x08003729` ~60 frames then resumed with `$15` unchanged.
* Reset chord: `A+B+Select+Start` held `0x000F` → handler `0x080036D1`,
  `$15` 112→0, stats `00 00 00`.
* Quicksave: Start then Select+Up → screen text `CONTINUE / SAVE`; Select moved
  the cursor from CONTINUE to SAVE; Start on SAVE updated the battery save and
  reset the NES; Start on CONTINUE resumed; B left the menu open.
* Gate bounds: extra button held first (`0x0304/0x0308/0x0340/0x0380`) all left
  the handler at `0x08003AAD`.

**Derived (instruction sequence):**

* New-file stats are copied from the fixed `$BAE3` table at `$B2CC`; the name
  write path `$B892` does not read that table or branch on the name.
* The name-position ring is `INC $1E` / compare `#$08` at `$B711`–`$B725`.
* The wrapper gate is `held == 0x0300 && (held & pressed)`; the selector ring
  is modulo 3; the page table is at `0x08004A98`.

**Inferred (not fully exercised):**

* The System Menu's three English labels; only the tile rows and behaviors are
  proven. Slot 2 is consistent with the wrapper's sleep/display-off path but its
  label was not decoded.
* New Game Plus works from `$07A0 == 1` at `$B2BC`, but a completed-game file
  was not produced.

## 8. Unknowns

* Exact English strings for the three System-Menu pages (proportional tile font
  at `0x06006E00`; the tile rows are in §6.3, the glyph table was not extracted).
* Whether System Menu slot 2 is labelled SLEEP or a resume variant; its
  behavior (60-frame transition, no SRAM write, NES frame counter unchanged) is
  proven.
* New Game Plus was not triggered; only its flag and load path are proven.

## 9. Tooling

* mGBA 0.10.5 SDL, Xvfb `:257`, openbox, xdotool; `SDL_AUDIODRIVER=dummy`.
* `ss.py` — decodes the PNG `gbAs` zlib chunk (VRAM `0x1000`, IWRAM `0x19000`,
  EWRAM `0x21000`) and reads RAM/ROM by address.
* `nesmap.py` — decodes the Zelda II tile encoding (`A=0xDA … Z=0xF3`,
  space `0xF4`, digits `0xD0`–`0xD9`) from NES/wrapper tilemaps.
* `dis6502.py` / Capstone 5.0.7 — 6502 disassembly of the 128 KiB runtime PRG.
* `arm-none-eabi-objdump -M force-thumb` — wrapper handler disassembly.
* `FiendsOfTheElements/z2disassembly` — symbol names for the matching NES PRG
  (its file offsets are the PRG offset + `0x10` iNES header).
* No ROM or copyrighted assets are redistributed; all tables above are
  re-derived addresses, byte values and our own generated inputs.
