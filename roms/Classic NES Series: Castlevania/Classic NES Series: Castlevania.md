# Classic NES Series: Castlevania (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Classic NES Series: Castlevania/Classic NES Series: Castlevania.gba` |
| Size | 1,048,576 bytes (1 MiB) |
| Header title (0xA0) | `CASTLEVANIA` |
| Game code (0xAC) / maker (0xB0) | `FADE` / `01` |
| Fixed byte 0xB2 / version 0xBC | `0x96` / `0x00` (Rev.00) |
| MD5 | `1f90a64fb3b26abee5ff9284fe628758` |
| SHA-1 | `47a60315ed4074a8c986723b95b3c90513d3b35c` |
| SHA-256 | `9e2b1feed479e90448cbf7defb34b1a286b57c016bccd7c78c933812380b3e89` |
| Entry word (0x00) | `0xEA000033` → `0x080000D4` (**not** the stock `0xEA00002E` → `0x080000C0`) |
| Header checksum (0xBE) | `0x0000` |
| Complement byte (0xBD) | `0xB5` (recomputed value also `0xB5` — header is internally consistent) |
| Embedded GBA-header scan | Nintendo logo found **once** (file offset `0x4`). Not a multi-game pack; single image. |

**Patch/trainer note.** Bytes `0xC0–0xD3` are not the stock crt0 prologue: they contain
`2419 0508` (word `0x24190508`), ASCII `CASTLEVA`, `2419 0508`, ASCII `kaae`.
The entry branch was retargeted five words later so the stock crt0 tail at `0xD4`
(`add r5,pc,#0x3c; ldm r5!,{r0,r1,r4,r6,r7,r8,r9}; msr CPSR…; svc 0`) still runs.
No trainer text, trainer menu, or overwritten game code was found; the image boots
straight into the emulated NES title. Classified as a **header/entry rebuild artifact**,
not an in-game cheat. (The zero header checksum is the usual companion of a rebuilt header.)

## 2. Executive summary

This SKU is a straight NES emulator wrapper. The emulated game is *Castlevania* (NES),
which has **no password, no stage select, no sound test**. Published "Castlevania"
sound-test/name codes belong to *Castlevania III: Dracula's Curse*; none of them exist
in this image (literals absent, see §6).

The developer-intended cheat surface that *does* exist is the **Classic NES Series
System Menu**, opened by holding **L + R** during play:

* The ROM installs a menu handler (`0x03006758 ← 0x0800225D`) only when the held-key
  word is exactly `0x0300` (L|R). L alone, R alone, L+R+Start and L+R+A are rejected.
* The menu panel is drawn in VRAM and reads, from the tile/palette data:
  **`MENU`** (title), **`CONTINUE`**, **`RESET`**.
* The selector (`0x03007B0D`) is a 4-slot ring (0…3). Slots 0/1 are the two drawn
  entries; slots 2/3 have **no drawn label** in this build and install their own
  handlers (`0x080020F9` and `0x0800207D`) — the two undocumented, unpublished slots.
* Effects: slot 0 resumes; slot 1 returns to the NES title screen
  (`DISPCNT 0x1960`, title nametable); slots 2/3 open the two unlabelled sub-screens
  and neither writes SRAM (the 8 KiB `.sav` stays all-`0xFF`).

The ROM contains **no password alphabet, no code table, no character-entry screen and
no debug key sequence**. The wrapper's only text UI is the page/script table at
`0x080033CC` (menu messages), and no ASCII text exists anywhere in the image (all UI is
tile-index text), so the negative is bounded by: full ASCII/keyword scans, shifted and
UTF-16 scans, key-mask scan, and a complete walk of both the NES screens (title,
gameplay) and every System-Menu slot.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba`), headless X, CLI debugger (`-d`) so all
evidence is memory reads (no screenshots used).

```bash
Xvfb :247 -screen 0 1024x768x24 &
DISPLAY=:247 openbox &
cd /tmp/opencode/cnescastlevania && cp "<rom>" work.gba
DISPLAY=:247 SDL_AUDIODRIVER=dummy /usr/games/mgba -d work.gba &
```

mGBA SDL keymap: `A=x  B=z  L=a  R=s  Start=Return  Select=BackSpace  D-pad=arrows`.
The ROM runs in real time; `frame` in the debugger advances exactly one frame, so every
step below is deterministic.

Reproduction path (frame counts are exact):

1. Boot, advance 240 frames → NES title screen (`DISPCNT=0x1960`).
2. Tap Start (`Return`) 20 frames, release, advance 200 frames → gameplay
   (`DISPCNT=0xFF60`).
3. Hold `a`+`s` (L+R) 12 frames, release → System Menu opens. Verify
   `hw(0x03006750)==0x0300` while held and `w(0x03006758)==0x0800225D` after open.
4. `Down` moves the selector at `0x03007B0D`: 0→1→2→3→0 (4-slot ring); `Up` reverses;
   `Select` also increments.
5. `A` (`x`) activates the slot. Observe `0x03006758`:
   slot 0 → `0x080023C1` (game), `DISPCNT=0xFF60`;
   slot 1 → `0x080023C1`, `DISPCNT=0x1960` (title/reset);
   slot 2 → `0x080020F9`; slot 3 → `0x0800207D`.
6. Reset combo: hold `x`+`z`+`Return`+`BackSpace` 12 frames → `DISPCNT=0x1960`,
   title nametable (`0x08000000` reset path).

RAM/VRAM evidence addresses used throughout: key-held `0x03006750`, key-pressed
`0x03006754`, menu handler `0x03006758`, selector `0x03007B0D`, game struct base
`0x03007200` (the code's `struct+0x90D` = `0x03007B0D`).

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08000000` | entry `b 0x080000D4` (patched from 0xEA00002E) |
| `0x080000C0–0x080000D3` | rebuilt-header data (`CASTLEVA`, 0x24190508, `kaae`) |
| `0x080000D4` | stock crt0 tail (stack setup for IRQ/SVC/SYS, SoftReset, jump) |
| `0x08001DE0` | read keypad: `KEYINPUT ^ 0x3FF` → held `0x03006750`, edge → `0x03006754` |
| `0x08001E10` | wait for VCOUNT > 159 (frame wait) |
| `0x08001E30` / `0x08001E4C` | frame wait / wait for any of A,B,Select,Start (`and 0x0F`) |
| `0x08001E70` | wait for key with mask (used by menu timing) |
| `0x08001910`, `0x08001954` | DMA3 tile/tilemap blit helpers (`0x040000D4`) |
| `0x08001A5C` | write glyphs from a nibble table (16-entry `0x0800F825`, tile table `0x08000826`) |
| `0x08001AA8` | **page renderer**: 8-byte records at `0x080033CC`, `{x,y,w,h,script_ptr}` |
| `0x08001B54–0x08001C8A` | page script interpreter (opcodes 0x00–0x0A, `0xFF`=end) |
| `0x080023C0` | **in-game handler** (`0x080023C1`): reset gate (`held==0x000F`) and L+R menu-open gate |
| `0x0800225C` | **System-Menu handler**: slot dispatch + draw (also closes/reset slot on B) |
| `0x08001FA0` | menu sub-handler (close / return to caller) |
| `0x08001FE0`, `0x08002000`, `0x08002024` | selector/slot sub-handlers (counter at `struct+0x910`) |
| `0x0800207D` | handler installed by System-Menu slot 3 |
| `0x080020F9` | handler installed by System-Menu slot 2 |
| `0x080023C1` | in-game handler (restored by CONTINUE and by RESET after title boot) |
| `0x080033CC` | page table, 60 × 8-byte records (menu pages 8, 9, 11, 12) |
| `0x08002608` | 256-entry `u16` glyph/tile table used by the page renderer |
| `0x0800F825` | 16-entry nibble→index table for the glyph writer |
| `0x03006750` | held keys, active-high (`KEYINPUT ^ 0x3FF`) |
| `0x03006754` | newly pressed keys (edge) |
| `0x03006758` | current screen handler pointer |
| `0x03007200` | wrapper/game state struct base |
| `0x03007B04` | struct+0x904: tilemap base pointer used by the page renderer |
| `0x03007B0D` | struct+0x90D: System-Menu slot selector (0–3) |

## 5. Algorithm (System-Menu gate and dispatch)

```c
// 0x080023C0, in-game handler (installed as 0x080023C1)
held    = *(u16*)0x03006750;     // active-high, KEYINPUT ^ 0x3FF
pressed = *(u16*)0x03006754;     // edge bits

if (held == 0x000F) {                    // A+B+Select+Start, exactly
    handler = 0x08002520;                // published soft-reset path
}
else if (held == 0x0300 && (held & pressed)) {
    struct->0x967 = 0; struct->0x968 = 0;
    handler = 0x0800225D;                // open System Menu
}

// 0x0800225C, System-Menu handler (runs while 0x03006758 == 0x0800225D)
if (pressed & 0x0002) {                  // B closes
    handler = 0x080023C1;
}
draw_page(struct, page_id_for(state->sel));      // 0x08001AA8
switch (state->sel) {                            // 0x03007B0D
case 0: page = 0x0C; break;   // empty script (0xFF) -> no message
case 1: page = 0x0B; break;   // "… RESET" message page
case 2: page = 0x09; break;   // save-progress page
case 3: page = 0x08; break;   // sleep-mode page
}
// navigation (pressed only)
if (pressed & 0x40) sel = (sel + 3) & 3;         // Up
if (pressed & 0x84) sel = (sel + 1) & 3;         // Down or Select
if (pressed & 0x09) {                            // A or Start
    switch (sel) {
    case 0: handler = 0x080023C1; break;         // CONTINUE (resume)
    case 1: handler = 0x080023C1; reset_to_title(); break;
    case 2: handler = 0x080020F9; break;         // undocumented sub-screen
    case 3: handler = 0x0800207D; break;         // undocumented sub-screen
    }
}
```

The open gate requires **held == 0x0300 exactly** (`movs r0,#0xC0; lsls r0,#2; cmp r1,r0`)
**and** at least one of L/R in the edge word (`ands r1,r2; bne`). Any additional held
button blocks the menu. The reset gate is the same shape: `cmp r1,#15` at `0x080023CA`,
i.e. exactly `A+B+Select+Start` and nothing else. Both are confirmed dynamically (§7).

## 6. Tables

### 6.1 System-Menu slots (0x03007B0D)

| Slot | Label drawn in VRAM | Page id | Script pointer | Handler installed | Observed effect |
|---:|---|---:|---|---|---|
| 0 | `CONTINUE` | 0x0C | `0x08002E1A` (first byte `0xFF` = empty) | `0x080023C1` | menu closes, game resumes |
| 1 | `RESET` | 0x0B | `0x080029F7` | `0x080023C1` | returns to NES title (`DISPCNT 0x1960`) |
| 2 | *(none drawn)* | 0x09 | `0x08002994` | `0x080020F9` | opens unlabelled sub-screen; SRAM untouched |
| 3 | *(none drawn)* | 0x08 | `0x0800294F` | `0x0800207D` | opens unlabelled sub-screen; SRAM untouched |

Keyboard gate masks (open gate `0x080023C0`, menu `0x0800225C`): `0x0040` Up, `0x0084` Down/Select,
`0x0009` A/Start, `0x0002` B, `0x0300` L+R (open), `0x000F` reset (in-game handler).

### 6.2 Published literals tested against this image

Searches were run on the exact bytes of this ROM, case-insensitive, plus shifted
(1…0x5F) and UTF-16LE/BE variants.

| Published item | Source class | Result in this ROM |
|---|---|---|
| `AKAMA`, `OKUDA`, `FUJIMOTO`, `URATA`, `HELP ME` | Castlevania III name codes | absent |
| `L1TTLVN`, `CR3D1TS` | unrelated GBA password lists | absent |
| `PASSWORD`, `SOUND TEST`, `STAGE SELECT`, `DEBUG`, `CHEAT`, `SECRET`, `UNLOCK`, `KONAMI` | keyword scan | absent (ASCII, shifted, UTF-16) |
| `L + R` System Menu | GameFAQs (Classic NES Series) | **verified working** |
| `Start + Select + A + B` reset | GameFAQs (Classic NES Series) | **verified working** |
| `SLEEP MODE` menu entry | GameFAQs (Classic NES Series) | **not drawn/labelled** in this build; only the two slots above are labelled |

`strings -n 4` yields 10,968 strings but **none** are ASCII UI text: the wrapper and the
NES game both store text as tile indices, so keyword absence is not by itself proof.
It is combined here with the menu walk and the page-table enumeration.

## 6b. Enumeration

**Space definition.** The only code-bearing surface in this ROM is the System-Menu
selector: one byte at `0x03007B0D`, 4 representable values (`0x00–0x03`), no checksum,
no payload bits, no alphabet. Ring arithmetic (`(sel±1)&3`) fixes the size at exactly 4;
a fifth `Down` wraps to 0 (observed: 0,1,2,3,0,1,2,3,0).

**Complete slot walk (each tested on a fresh boot, gameplay reached at frame ~460):**

| Slot | `0x03007B0D` | `DISPCNT` after A | `0x03006758` after A | SRAM MD5 |
|---:|---:|---|---|---|
| 0 | 0 | `0xFF60` | `0x080023C1` | `69e2d0f6…` unchanged |
| 1 | 1 | `0x1960` | `0x080023C1` | unchanged |
| 2 | 2 | `0xFF60` | `0x080020F9` | unchanged |
| 3 | 3 | `0xFF60` | `0x0800207D` | unchanged |

`work.sav` is 8,192 bytes, all `0xFF`, before and after every slot: no save path is
executed by slots 2/3 in this SKU.

**Novel / unpublished results (not in any published list).**

1. **Two extra selector slots.** Published descriptions give `CONTINUE`, `RESET`,
   (`SAVE HIGH SCORE`), `SLEEP MODE`; this ROM draws only `CONTINUE` and `RESET`, yet the
   selector has four slots. Slots 2 and 3 are reachable with `Down`/`Select` and install
   dedicated handlers `0x080020F9` / `0x0800207D` that have no drawn label. They are the
   undocumented entries; their pages exist in the table (`0x08002994`, `0x0800294F`) but
   are not rendered in the panel.
2. **Edge-sensitive exact gate.** The menu opens only for `held == 0x0300` *and*
   `held & pressed != 0` (`0x080023F0–0x08002400`). `L` (`0x200`), `R` (`0x100`),
   `L+R+Start` (`0x308`) and `L+R+A` (`0x301`) all leave `0x03006758` at `0x080023C1` and
   draw no panel — proven rejection, not an untested case.
3. **Undocumented cancel.** `B` inside the menu closes it (handler back to `0x080023C1`);
   no published description of this SKU mentions a cancel button.
4. **Reset is equally exact.** `0x080023CA` compares the held word to `0x000F`; the
   published `Start+Select+A+B` therefore resets only when no other button is held.

**Negative results, bounded.** No password/cheat-code system exists in this image:
there is no input buffer, no alphabet table, no string comparison against user text, and
no text-entry screen in either the wrapper or the emulated NES game. The searched spaces
were: all `strings -n 4` output (10,968 entries), all ASCII case variants of the keyword
list, shifts 1…0x5F of each keyword, UTF-16LE/BE of each keyword, and the complete
System-Menu page table (60 records, `0x080033CC`). The emulated *Castlevania* has no
password, stage select or sound test (the A+B sound test is *Castlevania III*).

## 7. Validation evidence

**Observed (emulator memory/VRAM reads, reproducible):**

* `0x03006750` tracks keys: `Return`→`0x0008`, `BackSpace`→`0x0004`, `x`→`0x0001`,
  `z`→`0x0002`, `a`→`0x0200`, `s`→`0x0100`; idle `0x0000`.
* L+R held → `0x03006750 == 0x0300`, `0x03006758` changes `0x080023C1 → 0x0800225D`;
  panel appears in VRAM (VRAM block at `0x6800` changes).
* L alone / R alone / L+R+Start / L+R+A → handler stays `0x080023C1` (no menu).
* `B` while the menu is open → handler returns to `0x080023C1` (menu closes).
* Panel text read from the composed VRAM+palette image: `MENU`, `CONTINUE`, `RESET`.
* Selector ring: `Down` 0→1→2→3→0; `Up` 0→3→2→1→0; `Select` increments.
* Slot 1 selection → `DISPCNT=0x1960`, title nametable restored (RESET).
* Slots 2/3 → handlers `0x080020F9` / `0x0800207D`; no SRAM write.
* `A+B+Start+Select` held 12 frames → `DISPCNT=0x1960`, title restored (published reset).

**Derived (instruction sequence):** the gate/dispatch at `0x0800225C`, page table at
`0x080033CC`, and script interpreter at `0x08001B54` were read with
`arm-none-eabi-objdump -M force-thumb`.

**Inferred:** the exact wording of the unlabelled page scripts (the renderer's nibble
encoding was not fully inverted); the two unlabelled slots are labelled here only by
their handler addresses.

## 8. Unknowns

* Full text of pages 8 and 9 (sleep/save message scripts) — the nibble glyph encoding
  was not inverted far enough to read them reliably; only `CONTINUE`/`RESET` were read
  from drawn VRAM.
* Whether slots 2/3 do anything on real hardware (they may depend on a save medium;
  this cart's 8 KiB SRAM stays empty in mGBA).
* Original purpose of the `0xC0–0xD3` header rebuild (loader/tool artifact); no trainer
  logic was found.

## 9. Tooling

* `arm-none-eabi-objdump` (binutils-arm-none-eabi) — Thumb/ARM disassembly.
* Python 3 + `zlib` — mGBA `.ssN` (PNG `gbAs`) parsing: state layout
  `0x0000` CPU/IO (`IO` at `0x400`, palette at `0x800`), `0x1000` VRAM (96 KiB),
  `0x19000` IWRAM, `0x21000` EWRAM.
* `render.py` — GBA mode-0 compositor (BG0–BG3 tilemaps, 4/8bpp, flips, scroll, palette)
  used to read menu text from VRAM as text.
* `gba.py` / `dbg3.py` — mGBA CLI-debugger driver (`frame`, `x/N`, `save/load`).
* No screenshots and no image files were used; all evidence is memory/VRAM/ROM bytes.

## Legal

No ROM, graphics, music or game text is redistributed. Only hashes, addresses,
instruction sequences, and derived menu/selector facts are published.
