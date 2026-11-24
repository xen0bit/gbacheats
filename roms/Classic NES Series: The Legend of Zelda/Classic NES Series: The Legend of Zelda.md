# Classic NES Series: The Legend of Zelda (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Classic NES Series: The Legend of Zelda/Classic NES Series: The Legend of Zelda.gba` |
| Size | 1,048,576 bytes (`0x100000`) |
| Header title | `ZELDA 1` (`0xA0`–`0xAB`) |
| Game code | `FZLE` (`0xAC`–`0xAF`) |
| Maker | `01` (`0xB0`–`0xB1`) |
| Version | `0x00` (`0xBC`) |
| Header complement | `0xFE` (`0xBD`) |
| Stored header checksum | `0x0000` (`0xBE`–`0xBF`) |
| Calculated header checksum | `0x0002` (mismatch; rebuilt header, normal for this wrapper family) |
| Entry word | `0xEA000031` → ARM branch to `0x080000CC` |
| MD5 | `df78967cea5f519d6477fe68edbfbb77` |
| SHA-1 | `28aac26365bf41ba84e67f97e98d15c4678cb99d` |
| SHA-256 | `a03c97b16ba1ba62361d5b3fed71e14fdafad814ff33671994b695f7bf0f2d20` |

Phase 0 notes:

* Exactly one 156-byte Nintendo logo occurs, at file offset `0x4`. There is no second GBA
  header, so this is a single-image cart, not a multi-game pack.
* The header is rebuilt: the stored checksum is `0x0000`, the complement is `0xFE`, and the
  entry branches to `0x080000CC` instead of `0x080000C0`. Bytes at `0x080000C0` are
  `03 13 10 49 5a 45 4c 44 41 31 5f 35 3c 50 8f e2` — i.e. a small data word followed by
  `ZELDA1_5<P` and the stock wrapper boot code at `0xCC`. This is the same boot/save signature
  shape as other Classic NES Series titles (compare `BOMBER_1` in the Bomberman report), not a
  scene cracktro.
* No trainer, cracktro, or appended trainer menu was found. A case-insensitive scan for
  `sunhors|mode7|crc bandit|paradox|trainer|gameshark|codebreaker|action replay` over all
  `>=4`-byte ASCII runs returns nothing. The first 4 KiB is the wrapper boot stub and normal
  ARM/Thumb code.
* The ROM is an **emulated NES game**. The 128 KiB NES PRG is not stored in plain form in the
  GBA image (entropy ≈ 8.0 from file `0x20000`; no 16-byte slice of the runtime PRG matches
  the file). The runtime image was taken from an mGBA savestate and is the ground truth used
  here: 128 KiB at EWRAM `0x02000000`.

## 2. Executive summary

This SKU is the NES *The Legend of Zelda* running inside the Classic NES Series wrapper.
There are exactly two in-game / developer-intended cheat surfaces, and both were reversed and
enumerated:

1. **The NES name-entry second-quest unlock.** The file-registration screen accepts an
   8-cell name. A 6502 routine compares **only the first five cells** against the inline
   table `23 0E 15 0D 0A` (tile codes for `ZELDA`) at NES `$9EEB`. On a match it writes
   `1` to the per-file quest byte in battery WRAM (`$6D99 + slot`). When the file is loaded,
   that byte is copied to the live per-slot quest variable `$062D + slot`, and the game
   code reads `$062D` to select quest-specific data. Published lists say “enter the name
   ZELDA”; the ROM actually compares a **five-cell prefix**, so any 8-cell name of the form
   `ZELDA???` is equally valid.

2. **The wrapper System Menu** (hold **L + R**). Its selector is a 3-slot ring at
   `0x03007B01`; every index installs a different handler. Effects were walked end to end:
   slot 0 resumes, slot 1 resets the emulated NES to its title, slot 2 runs the
   save/page routine and returns to the game at the same map.

Verified live on the emulator (all values are NES internal RAM or GBA IWRAM reads):

* Published anchor `ZELDA` → NES `$062D = 1` (second quest).
* **Novel, unpublished spelling `ZELDAXYZ`** → `$062D = 1`. No published list mentions a
  name longer than `ZELDA`; the suffix cells are not compared.
* Bounds by rejection: `ZELDZ` (wrong fifth cell), `ZELD` (only four cells) and `AZELDA`
  (ZELDA not at cell 0) each start the file with `$062D = 0` (first quest).
* System-Menu gate: the in-game handler opens only for `held == 0x0300` exactly plus an edge
  on L/R; holding Start first and then adding L+R leaves the handler at `0x080016A9`.
  `A+B+Select+Start` (`held == 0x000F`) is the separate soft reset.

There is no password system, no code table, and no debug menu in either the NES game or the
wrapper. `strings` finds no UI text at all (both layers draw text from tile indices); the
negative is bounded in §7.

## 3. How to reproduce

### Emulator and keymap

* mGBA 0.10.5 SDL (`/usr/local/bin/mgba`), `Xvfb :255` + `openbox`, `SDL_AUDIODRIVER=dummy`.
* Keymap: **A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows**.
* All evidence was read from mGBA savestates (`Shift+F1`): the PNG `gbAs` chunk is
  zlib-compressed; for this 1 MiB ROM the 397,312-byte state has VRAM at `0x1000`, IWRAM at
  `0x19000`, EWRAM at `0x21000`. No screenshots were used.
* NES RAM is visible at IWRAM `0x03007200` (`$0000`–`$07FF`); NES battery WRAM at EWRAM
  `0x02030000` (`$6000`–`$7FFF`).

### Registration path (the whole unlock)

1. Boot. Title screen shows `PUSH START BUTTON` (`DISPCNT`/nametable text).
2. Press **Start** → file-select screen (`NAME / LIFE`, `REGISTER YOUR NAME`,
   `ELIMINATION MODE`). NES `$12 = 1`.
3. Press **Start** with NES `$16 == 3` (the `REGISTER YOUR NAME` option) → registration
   screen (`$12 = 0x0E`).
4. Move the grid cursor with the D-pad and press **A** to place each character. The
   highlighted cell is NES `$041F` (`0..43`); the name buffer is `$0638 + 8*slot` and the
   write position is `$0421`.
5. Register the name: press **Select** (BackSpace) until NES `$16 == 3`, then press
   **Start**. This is a real quirk of the handler: Start only completes registration when
   `$16 == 3` (the routine at `$9EF0` tests `$F8 & 0x10` and `$16 == 3`). With an empty
   save, `$16` starts at 0, so three Select presses are needed. Start at `$16 = 0/1/2/4`
   does nothing (tested).
6. Press **Start** on the new file to start the game. Read NES `$062D` (slot 0) — `1` means
   second quest.

The 44-cell grid (row-major, 11 columns) is table `$9DB3`:

```
row 0: A B C D E F G H I J K     (tile codes $0A-$14)
row 1: L M N O P Q R S T U V     ($15-$1F)
row 2: W X Y Z <2 symbols> , . " ' /   ($20-$23, $62,$63, $28-$2C)
row 3: 0 1 2 3 4 5 6 7 8 9 <blank>      ($00-$09, blank = $24)
```

`ZELDA` is typed as: Down,Down,Right,Right,Right,A; Up,Up,Right,A;
Down,Left,Left,Left,Left,A; Up,Right,Right,Right,A; Left,Left,Left,A.

### System Menu path

1. In game or at the title, hold **L+R** ~0.5 s, release. The wrapper freezes the NES.
2. `0x03006700` changes from the in-game handler `0x080016A9` to the menu handler
   `0x0800156D`; NES frame counter `$15` stops.
3. **Down** (or **Select**) advances the selector `0x03007B01`: `0→1→2→0`; **Up** reverses;
   **B** cancels the menu.
4. **A** activates the current slot (see §6).

### Codes/names tested live

| Input (name cells) | NES `$062D` | Result |
|---|---|---|
| `ZELDA` (`23 0E 15 0D 0A 24 24 24`) | `01` | second quest — published anchor |
| `ZELDAXYZ` (`23 0E 15 0D 0A 21 22 23`) | `01` | **novel**, not in any published list |
| `ZELD` (`23 0E 15 0D 24 24 24 24`) | `00` | rejected (too short) |
| `ZELDZ` (`23 0E 15 0D 23 24 24 24`) | `00` | rejected (fifth cell differs) |
| `AZELDA` (`0A 23 0E 15 0D 0A 24 24`) | `00` | rejected (prefix is not `ZELDA`) |

## 4. Address map

### GBA / wrapper

| Address / offset | Meaning |
|---|---|
| File `0xC0`–`0xC2` | wrapper boot signature word `03 13 10 49`, then `ZELDA1_5` |
| `0x080000CC` | ARM wrapper entry (branch target of `0xEA000031`) |
| EWRAM `0x02000000`–`0x0201FFFF` | runtime NES PRG, 128 KiB, 8 × 16 KiB banks (savestate offset `0x21000`) |
| EWRAM `0x02030000`–`0x02031FFF` | NES battery WRAM `$6000`–`$7FFF` (verified: names at `$6880`, signatures at `$651E`) |
| IWRAM `0x03007200`–`0x030079FF` | NES internal 2 KiB RAM (`$0000`–`$07FF`, mirrored) |
| `0x03006744` | wrapper held-key word, active high (`KEYINPUT ^ 0x3FF`) |
| `0x03006748` | wrapper newly-pressed (edge) word |
| `0x03006700` / `0x0300674C` | current handler pointer (both updated together) |
| `0x03007B01` | System-Menu selector (`struct 0x03007200 + 0x901`) |
| `0x03007B03` | selector animation/step counter used with the panel (cycles `0x0B/0x14/0x04`) |
| `0x080016A8` | **in-game handler** (`0x080016A9`): reset gate + L+R menu gate |
| `0x0800156C` | **System-Menu handler** (`0x0800156D`): B close, L+R close, slot draw/dispatch |
| `0x08001299` | handler installed by System-Menu slot 0 |
| `0x0800131D` | handler installed by System-Menu slot 1 (also the 4-button reset target) |
| `0x080013B9` | handler installed by System-Menu slot 2 |
| `0x0800268C` | page table (8-byte records `{x,y,w,h,script_ptr}`); pages 8–11 at `0x080026CC`, `0x080026D4`, `0x080026DC`, `0x080026E4` |

### NES 6502 (bank n at file `n*0x4000` ↔ CPU `$8000`; fixed bank at file `0x1C000` ↔ CPU `$C000`)

| NES address | PRG file offset | Meaning |
|---|---|---|
| `$9D00` | `0x9D00` | 3 × 14-byte pointer records (one per save slot): `{name, icon, data, present, ?, deaths, quest}` |
| `$9D2A` | `0x9D2A` | builds the 7-pointer record into zero page `$C0`–`$CD` for slot `$16` |
| `$9DB3` | `0x9DB3` | 44-cell name-grid tile-code table |
| `$9EEB` | `0x9EEB` | inline 5-byte comparison table `23 0E 15 0D 0A` (`ZELDA`) |
| `$9F0D`–`$9F86` | `0x9F0D`–`0x9F86` | file-select row draw; **name validator** at `$9F4F`–`$9F6D` |
| `$9F6C` | `0x9F6C` | `STA ($CC),Y` → quest byte `$6D99 + slot = 1` |
| `$9F77` | `0x9F77` | `STA ($C6),Y` → slot-present byte `$6D90 + slot = 1` |
| `$A3E1` / `$A3C8` | `0xA3E1` / `0xA3C8` | 16-bit file checksum over name + icon + status + 4 flag bytes; stored at `$6D9C + 2*slot` |
| `$A6A1`–`$A733` | `0xA6A1` | save routine: `$062D`→`$6D99`, `$0630`→`$6D96`, `$0633`→`$6D90`, name→`$6880+8*slot` |
| `$A764`–`$A7F0` | `0xA764` | load routine: `$6D99`→`$062D`, `$6D96`→`$0630`, `$6D90`→`$0633` (`$A797`/`$A7A7`) |
| `$AE72` / `$AE7D` | `0xAE72` | reads `$062D,X` and branches to quest-specific data |
| `$ABFA` | `0xABFA` | reads `$062D,X` in the dungeon/level loader |
| `$FF50` | `0x1FF50` | 6502 reset vector target; MMC1 setup, `JMP $E440` |

### NES RAM evidence

| Address | Meaning |
|---|---|
| `$0010` | current level (`0` = overworld) |
| `$0012` | game mode: `0` title/transitory, `1` selection, `5` normal, `0x0E` registration, `0x0F` elimination |
| `$0016` | save-slot / menu-option index (0–2 slots, 3 = REGISTER, 4 = ELIMINATION) |
| `$041F` | name-grid cursor cell (0–43) |
| `$0420` | registration init flag |
| `$0421` | name write position (slot*8 + position) |
| `$062D/$062E/$062F` | **current quest per save slot** (0 = first, 1 = second) |
| `$0630/$0631/$0632` | deaths per slot |
| `$0633/$0634/$0635` | slot-present per slot |
| `$0636/$0637` | REGISTER / ELIMINATION options present |
| `$0638`, `$0640`, `$0648` | 8-byte player names, slots 1–3 |
| `$06D90`-region (WRAM) | `$6D90+slot` present, `$6D96+slot` deaths, `$6D99+slot` quest, `$6D9C+2*slot` checksum |

## 5. Algorithm

### 5.1 Name → quest (the unlock)

```
; file-select row draw, X = slot, Y = X*8 (name index)
; $0638 holds the 8-cell names of all three slots
9F4F  TXA            ; A = slot
9F50  PHA
9F51  ASL / ASL / ASL; *8
9F54  TAY
9F55  LDX #$00
9F57  LDA $0638,Y
9F5A  CMP $9EEB,X     ; compare against "ZELDA" tile codes
9F5D  BNE $9F6E
9F5F  INY
9F60  INX
9F61  CPX #$05
9F63  BCC $9F57
9F65  ...             ; all five matched
9F6A  LDA #$01
9F6C  STA ($CC),Y     ; $6D99 + slot = 1   (quest)
9F70  LDA #$01
9F72  STA $0426
9F75  LDY #$00
9F77  STA ($C6),Y     ; $6D90 + slot = 1   (slot present)
```

Reimplemented validator:

```python
ZELDA = [0x23, 0x0E, 0x15, 0x0D, 0x0A]       # A=0x0A, so "ZELDA"
SPACE = 0x24

def quest_for_name(cells8):                  # 8 tile codes from the $9DB3 grid
    return 1 if cells8[0:5] == ZELDA else 0  # cells 5..7 are ignored
```

No checksum or range check is applied to the suffix; the comparison length is fixed at five
(`CPX #$05`). The flag is written into the checksum-protected record, then the save routine
(`$A6A1`) later copies `$062D` back into `$6D99`; the load routine (`$A764`) copies
`$6D99` into `$062D`. The game then reads `$062D` (e.g. `$AE72`, `$ABFA`) to pick
quest-specific tables.

### 5.2 Wrapper System-Menu gate and dispatch

```c
// 0x080016A8, in-game handler
held    = *(u16*)0x03006744;     // active-high KEYINPUT ^ 0x3FF
pressed = *(u16*)0x03006748;

if (held == 0x000F) {                    // A+B+Select+Start, exactly
    ...; handler = 0x0800131D;           // reset path
}
else if (held == 0x0300 && (held & pressed)) {
    ...; handler = 0x0800156D;           // open System Menu
}

// 0x0800156C, System-Menu handler
if (pressed & 0x0002) handler = 0x080016A9;          // B closes
if (held == 0x0300 && (held & pressed)) handler = 0x080016A9;  // L+R closes
draw_page(8);
switch (sel) {                                        // sel = 0x03007B01
case 0: page = 0x08001299; break;
case 1: page = 0x0800131D; break;
case 2: page = 0x080013B9; break;
}
if (pressed & 0x40) sel = (sel + 2) % 3;              // Up
if (pressed & 0x84) sel = (sel + 1 > 2) ? 0 : sel+1;  // Down or Select
if (pressed & 0x09) handler = page;                   // A or Start
```

## 6. Tables

### 6.1 Name grid (`$9DB3`, 44 cells)

| Cells | Tile codes | Glyphs |
|---:|---|---|
| 0–25 | `0x0A`–`0x23` | `A`–`Z` |
| 26–32 | `0x62, 0x63, 0x28, 0x29, 0x2A, 0x2B, 0x2C` | two special glyphs, `,` `.` `"` `'` `/` |
| 33–42 | `0x00`–`0x09` | `0`–`9` |
| 43 | `0x24` | blank / space |

The name area is 8 cells. `$0421` starts at `slot*8`; `A` writes the selected cell code and
advances it.

### 6.2 Per-slot save flags (NES battery WRAM, mirrored at EBA `0x02030000`)

| WRAM address | Meaning |
|---|---|
| `$6880 + 8*slot` | 8-cell name |
| `$6898 + 0x28*slot` | status/icon block (0x28 bytes) |
| `$6910 + 0x180*slot` | status block (0x180 bytes) |
| `$6D90 + slot` | slot present (1 after any non-blank name is drawn) |
| `$6D96 + slot` | death count |
| `$6D99 + slot` | **quest flag** (1 = second quest) |
| `$6D9C + 2*slot` | 16-bit record checksum |
| `$651E/$6521/$652A + slot` | save-validity markers (`5A`, `A5`, `FF`/`00`) |

### 6.3 Wrapper System Menu (selector `0x03007B01`, 3-slot ring)

| Slot | Handler installed | Observed effect |
|---:|---|---|
| 0 | `0x08001299` | closes menu, restores in-game handler `0x080016A9`; NES frame counter resumes (observed `$15` 78 → 197) |
| 1 | `0x0800131D` | resets the emulated NES to its title (`$12` 5 → 0, `$15` restarts at 27, `$EB` 0) |
| 2 | `0x080013B9` | runs the `0x08000358` page/transition chain, holds ~60 frames, returns to the game at the same map (`$EB` 119 unchanged) |

Gate masks: open `held == 0x0300` exactly (`0x080016D8`–`0x080016E8`); reset
`held == 0x000F` exactly (`0x080016B2`); navigation Up `0x40`, Down/Select `0x84`,
A/Start `0x09`, B `0x02`.

### 6.4 Published literals checked against this image

| Published item | Source class | Result |
|---|---|---|
| `ZELDA` name → second quest | 3rd party cheat indexes / Nintendo / fan wikis | **verified** (tile table `$9EEB`, `$062D=1`) |
| `L + R` System Menu | Classic NES Series documentation | **verified** (handler `0x0800156D`) |
| `Start+Select+A+B` reset | Classic NES Series documentation | **verified** (`held==0x000F`, `$12=0`) |
| `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `LEVEL SELECT`, `SOUND TEST` | generic keyword lists | absent as ASCII (10,677 `strings -n 4` entries; 2 keyword hits, both header) |
| NES *Zelda* password lists from other editions | FDS/other-region material | no password screen exists; the only name comparison is the five-cell table above |
| ASCII `ZELDA` in the fixed bank | (not published) | present once at `$FFEB`, inside a data table; no reference reaches it (unused copy) |

## 6b. Enumeration

### Space 1 — name-entry second quest

* **Alphabet:** 44 cells (`A`–`Z`, 7 symbols, `0`–`9`, blank) — table `$9DB3`.
* **Length:** 8 cells per slot; shorter names are space-padded (`$24`).
* **Validator:** first 5 cells must equal `23 0E 15 0D 0A`; cells 5–7 are never read.
* **Representable strings:** `44^8 = 14,048,223,625,216`.
* **Accepted strings:** exactly `44^3 = 85,184` (one prefix × three free cells).
* **Novel input (not in any published list): `ZELDAXYZ`** (cells `23 0E 15 0D 0A 21 22 23`).
  Entered on the registration screen; the started file had NES `$062D = 01`, i.e. second
  quest. Published descriptions only state the five-letter name, so every one of the other
  85,183 prefix variants is unpublished; `ZELDAXYZ` was chosen to exercise a full eight-cell
  name.
* **Bounds by rejection** (each on a fresh SRAM, started normally, `$12 = 5` gameplay):
  * `ZELDZ` — fifth cell differs → `$062D = 00`.
  * `ZELD` — four cells, then spaces → `$062D = 00`.
  * `AZELDA` — `ZELDA` at cells 1–5, not 0 → `$062D = 00`.
  These prove the comparison is a length-5 prefix at cell 0, not a substring and not a
  checksum over the whole name.
* **Persistence:** the flag is written to `$6D99+slot` inside the checksum-protected file
  record and copied to `$062D+slot` by the load routine; the file was started through the
  normal file-select screen in every test above.

### Space 2 — wrapper System-Menu selector

* **Representable values:** 3 (`0x03007B01 = 0..2`, no checksum, no payload).
* **Ring arithmetic:** `sel+1; if >2 then 0` for Down/Select; `sel-1; if <0 then 2` for Up.
  Six Down presses were observed to wrap `1→2→0→1→2→0→1`; a fourth slot is unreachable.
* **All three slots walked** (fresh menu open each time): effects in §6.3. All three install
  distinct handlers and all three return control to the game.
* **Unreachable page:** the page table (`0x0800268C`, 8-byte records) contains page 11
  (`0x08001CA2`), which no selector index can reach. The menu list itself is page 8
  (`0x08001C34`); the sub-pages are used by the slot handlers.

## 7. Validation evidence

**Observed (emulator memory reads, reproducible):**

* `ZELDA` registration → NES `$062D = 01`, name cells `23 0E 15 0D 0A 24 24 24`.
* `ZELDAXYZ` → `$062D = 01`, name cells `23 0E 15 0D 0A 21 22 23`.
* `ZELDZ`, `ZELD`, `AZELDA` → `$062D = 00`; each reached gameplay (`$12 = 5`) normally.
* Start at registration with `$16 = 0,1,2,4` does nothing; with `$16 = 3` the name is
  registered and the file appears on the select screen.
* Wrapper: L+R changes handler `0x080016A9 → 0x0800156D` and freezes NES `$15`;
  Down moves `0x03007B01` 0→1→2→0; B returns to `0x080016A9`.
* Holding Start first and then adding L+R leaves `0x03006700 = 0x080016A9`.
* A+B+Select+Start → `$12 = 0` (NES title).
* Menu slot effects: slot 0 resumes (`$15` advances), slot 1 resets (`$12 = 0`, `$15 = 27`),
  slot 2 returns with `$EB` unchanged.

**Derived (disassembly + reimplementation):**

* The five-cell prefix comparison and the `$6D99+slot` write at `$9F4F`–`$9F6D`.
* The save/load copies `$062D ↔ $6D99` at `$A6E0` and `$A797`/`$A7A7`.
* The 16-bit record checksum at `$A3E1`/`$A3C8` and the three pointer records at `$9D00`.
* The System-Menu gate and slot dispatch at `0x080016A8`/`0x0800156C`.
* `$062D` is read by the quest/data selector (`$AE72`, `$AE7D`, `$ABFA`), so the flag is
  consumed by the game, not only stored.

**Inferred:**

* The exact menu label of slot 2 (save vs. sleep): its handler shows a page and holds the
  menu for ~60 frames, then returns to the same map — consistent with a save-and-resume
  path, but the panel text was not OCR'd.
* Whether the two special glyphs at codes `$62`/`$63` are punctuation or blanks; they are
  selectable grid cells but were not needed for the unlock.

## 8. Unknowns

* The wrapper's System-Menu panel text is drawn from GBA-native tiles through the page
  renderer (`0x0800268C`, pages 8–11) and was not OCR'd. Slot effects are known, labels are
  not read out. This is the only unread UI in the report.
* The exact save encoding the wrapper writes to `.sav` (8 KiB, first `0x200` bytes `0xFF`)
  was not reversed; the NES battery WRAM was read directly from EWRAM instead.
* No second-quest *screen* difference was captured in this session because the starting
  cave is shared by both quests; the quest variable `$062D` and the ROM selector code at
  `$AE72` are the evidence used.
* The `$6D93`/`$6D96` flag arrays were not individually named beyond “deaths” for `$6D96`;
  `$6D93` was not exercised.

## 9. Tooling

* mGBA 0.10.5 SDL under `Xvfb :255` + `openbox`, `SDL_AUDIODRIVER=dummy`, `xdotool` input.
* `ss.py` — zlib-decompress the PNG `gbAs` chunk and address VRAM/IWRAM/EWRAM.
* `screen.py` — decode the NES nametable mirrored at GBA `0x06002000` into text.
* `name_run.py` — deterministic grid navigation, buffer verification, registration and
  quest-byte readback.
* `py65` (disassembler) for 6502; `arm-none-eabi-objdump -M force-thumb` for the wrapper.
* Published-code checks: search snippets and a Wayback snapshot of the 3rd party cheat indexes RAM map
  (3rd party cheat indexes, 2024-08-23 capture). All fetched
  pages were treated as data; no instructions in them were followed.

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed here. The report contains
only addresses, algorithms, hashes, and the short generated name strings needed to reproduce
the result.
