# Classic NES Series: Super Mario Bros. (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Classic NES Series: Super Mario Bros/Classic NES Series: Super Mario Bros.gba` |
| Size | 1,048,576 bytes (`0x100000`) |
| Header title | `SUPER MARIO` (`0xA0`–`0xAB`) |
| Game code | `FSME` (`0xAC`–`0xAF`) |
| Maker | `01` (`0xB0`–`0xB1`) |
| Version | `0x00` (`0xBC`) |
| Header complement | `0x9E`; stored header checksum `0x0000` |
| Calculated header checksum | `0x00B6` (does not match stored `0x0000`) |
| Entry word | `0xEA000031` → ARM branch to `0x080000CC` |
| MD5 | `97e977d6bb8b2e45a5ad6952dd9a5481` |
| SHA-1 | `8ca35864ae33c9462dd66ceff1fac5a79e2e0a6f` |
| SHA-256 | `5e8ee5d663a7767639ede878cee93d6add10f37c96e03e21551af0073de16879` |

Phase 0 notes:

* Exactly **two** 156-byte Nintendo logos occur: `0x0004` (main header) and `0x0CFBC`
  (a second header whose base is `0x0CFB8`). The second image is the same title/code,
  entry `0xEA000061` → `0x0800D144`, and is a small ARM multiboot loader, not a
  second game (it copies the main image to EWRAM and sets link/display registers).
  This is the single-cart LINKED PLAY payload used by System-Menu slot 3.
* The main header is rebuilt: stored checksum `0x0000`, complement `0x9E`, entry
  `0xEA000031`. Bytes at `0x00C0` are `03 16 18 31` followed by the ASCII wrapper
  build tag `RIO_4_2P` at `0x00C4`; ARM code starts at `0x080000CC`. This is a
  wrapper boot signature, not a scene cracktro.
* No trainer, cracktro, appended trainer menu or patched entry stub was found in the
  first 4 KiB or at the second header.
* The ROM is an **emulated NES game**. The NES PRG is staged at EWRAM `0x02000000`,
  CHR at EWRAM `0x02008000`, and NES RAM at IWRAM `0x03007200` (verified by reset
  vector, live zero-page values and the title/game HUD). The PRG copy stored at file
  `0x17C59` is wrapper-encoded (an extra `0xFF` appears after `A2 FF`), so the runtime
  PRG from an mGBA savestate was the ground truth for 6502 analysis.

## 2. Executive summary

This is a direct emulation of the NES *Super Mario Bros.* inside the Classic NES
Series GBA wrapper. There is **no password system, no NES cheat-code table and no NES
debug menu**. The only developer-intended cheat surfaces are:

1. **The wrapper System Menu**, opened by holding **L+R** (verified on this SKU, not
   just on other entries in the series). The gate is exact: `held == 0x0300` *and*
   a new L/R edge in the same frame. It has **five slots** in a ring. This report
   enumerates all five, their page IDs, handlers and observed effects, including the
   undocumented input aliases **Select = Down**, **Start = A**, and **B = close**.
2. **The SMB title-screen button space.** Start starts the selected game; **A+Start**
   starts at `ContinueWorld` (`$07FD`); the Select branch toggles 1P/2P (derived);
   B is ignored unless the world-select flag `$07FC` is set. There is no sequence
   table and no hidden button code beyond these branches.
3. **The world-select flag `$07FC`**, normally described on fan sites as “press B at
   the title after beating the game”. The ROM disagrees: the **only writer** of
   `$07FC` is NES `0x8491–0x8493`, inside the World-8 completion path
   (`PlayerEndWorld`, `WorldNumber >= 8`, `WorldEndTimer == 0`), and it requires B to
   be held at that moment. A title-screen B before that write is ignored. This is a
   concrete correction to the published instruction.
4. **The 256-world / level-table space.** All world changes go through
   `GoContinue` (`$830E`). The warp table at `$87F2` contains `24 05 24 00`, whose
   `0x24` entry means WorldNumber `0x23` (displayed “36”, i.e. the Minus World).
   World `0x23` resolves through the out-of-bounds 8-entry `WorldAddrOffsets` table
   to AreaPointer `0x01` → AreaData `0xAE45` and enemy data `0x9FF1`. The HUD writes
   `WorldNumber+1` directly as a tile number, so world 36 renders as a blank tile
   plus the pre-existing dash: “World -1”.

**Novel, unpublished result (dynamic):** on this cartridge the System Menu's
**SAVE HIGH SCORE** slot executes the save path but fails its verification
(`0x08000B10` does not return `0x180`); it installs the save-error handler
`0x08001E71`, sets `struct+0x992 = 0xA0`, and leaves the 8 KiB `.sav` byte-identical.
No published Classic NES SMB list describes this failure page. It was reached
through the real menu in the emulator and RAM-verified, and B cancels it back to the
game. A second unpublished state is the **System Menu opened on the NES title
screen** (published notes say “in-game” only).

## 3. How to reproduce

### Emulator and keymap

* mGBA 0.10.5 (SDL frontend, `/usr/games/mgba`) under `Xvfb :254`, openbox,
  `SDL_AUDIODRIVER=dummy`.
* Keymap verified against the wrapper's key state at `0x0300648C`:
  **A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys**.
* Use a copy (`work.gba`) in a scratch directory so no `.sav`/`.ss*` is written next
  to the master ROM. mGBA `Shift+F1..F9` saves a slot; the state is a PNG with a
  zlib-compressed `gbAs` chunk (397,312-byte raw state for this 1 MiB ROM).

### Wrapper System Menu (verified)

1. Boot to the NES title, or start a game (Start).
2. Hold **L+R** (`a`+`s`) for ~0.3 s and release. The wrapper handler at
   `0x03006494` changes from `0x08002691` (game) to `0x08002429` (menu).
   This also works on the NES title screen.
3. `Up` decrements, `Down` or `Select` increments the selector at `0x03007B4D`
   (ring 0→1→2→3→4→0).
4. **A or Start** activates the selected slot; **B** closes the menu and resets the
   selector to 0.
5. Inside the menu, `A+B+Select+Start` (`held == 0x000F`) is the wrapper soft reset.

### SMB title-screen button space (verified)

1. At the NES title, Start (`Return`) starts the selected game; the first gameplay
   state has `OperMode $0770 = 1`, `OperMode_Task $0772 = 3`, `WorldNumber $075F = 0`,
   `AreaNumber $0760 = 0`, `LevelNumber $075C = 0`.
2. `A+Start` starts at `ContinueWorld $07FD` (set at game over from `WorldNumber`).
3. The Select branch at `0x8276` toggles `NumberOfPlayers $077A` (derived; our live
   Select presses at the title did not change `$077A` inside the sampled window,
   likely because of the demo/select timer, so this is not claimed as observed).
   B at the title does nothing while `WorldSelectEnableFlag $07FC == 0`.
4. Start+Select and Down at the title were rejected (`$0770` stayed 0).

### Published list used for Phase 1

The archived GameFAQs cheats page for this GBA entry
(`web.archive.org/web/20250126130918/.../919774-.../cheats`) lists: Continue with
A+Start, Level Select/World Select with B at the title after completing the game,
the World 1-2 wall-clip Minus World, and the normal 1-2/4-2 warps. The button
branches were checked against this ROM; the Minus World payload and the world-select
writer are corrected below.

### Codes / combos tested live

| Input | Result | RAM evidence |
|---|---|---|
| L+R (exact, edge) | System Menu opens | `0x03006494 = 0x08002429` |
| L alone / R alone | no menu | handler stays `0x08002691` |
| Start+L+R pre-held (`0x0308`) | rejected | handler stays `0x08002691` |
| A+L+R pre-held (`0x0301`) | rejected | handler stays `0x08002691` |
| Menu `Down` ×5 | 5-slot ring wraps | selector 0→1→2→3→4→0 |
| Menu `Select` | increments like Down | selector 1→2 (and 0→1 on retest) |
| Menu `Start` on slot 1 | activates RESET | handler `0x08002691`, NES `OperMode=0, Task=3` |
| Menu `B` | closes menu | handler `0x08002691`, selector 0 |
| Menu slot 2 + A | save fails → error page | handler `0x08001E71`, `struct+0x992=0xA0`, `.sav` MD5 unchanged |
| Menu slot 2 error + B | back to game | handler `0x08002691` |
| A+B+Select+Start | NES soft reset | `OperMode=0`, `Task=1` (reboot) |
| Title Start | starts game | `$0770=1`, `$0772=1→3` |
| Title Start+Select | rejected | `$0770` stays 0 |
| Title B (flag 0) | rejected | `$07FC=0`, `$0770` stays 0 |

## 4. Address map

### GBA side

| Address / offset | Meaning |
|---|---|
| File `0x0000` | main header; entry `0xEA000031` → `0x080000CC` |
| File `0x00C4` | wrapper build tag `RIO_4_2P` |
| File `0x17C59` | wrapper-encoded stored NES PRG image (not directly runnable) |
| File `0xCFB8` | second GBA header (same `SUPER MARIO`/`FSME`) |
| `0x0800D144` | ARM multiboot loader for LINKED PLAY (copies main image to EWRAM, sets DISPCNT/BG0CNT and link registers) |
| `0x08001480` | key read: `KEYINPUT ^ 0x3FF` → held `0x0300648C`, new-press `0x03006490` |
| `0x08002690` | in-game handler (installed as `0x08002691`): reset gate (`held==0x0F`) and L+R menu gate |
| `0x08002428` | System-Menu handler (installed as `0x08002429`); slot jump table at `0x08002490` |
| `0x08001644` | slot-0 action handler (CONTINUE path) |
| `0x080016C8` | slot-1 action handler (RESET path) |
| `0x08001E70` | save-error page handler (installed by failed SAVE) |
| `0x080022D4` | slot-3 action handler (LINKED PLAY) |
| `0x08001764` | slot-4 action handler (SLEEP/delay) |
| `0x08003954` | page record table, 8-byte records `{x,y,w,h,script_ptr}` |
| `0x08000FCC` | page renderer / script interpreter |
| `0x08002B3C` | glyph/tile lookup table used by the renderer |
| `0x08002B2C` | 16-entry nibble lookup table |
| `0x0300648C` | held keys, active-high |
| `0x03006490` | newly pressed keys (edge) |
| `0x03006494` | current screen handler pointer |
| `0x03007200` | wrapper/game struct base |
| `0x03007B44` | struct+0x944: menu tilemap base pointer (`0x06006E00` in the menu) |
| `0x03007B4D` | struct+0x94D: System-Menu selector (0–4) |
| `0x03007B92` | struct+0x992: save-media/save-result byte (`0x80` normal, `0xA0` after failure) |
| EWRAM `0x02000000` | runtime NES PRG (32 KiB) |
| EWRAM `0x02008000` | runtime NES CHR (8 KiB) |
| IWRAM `0x03007200` | runtime NES 2 KiB RAM |

The savestate layout used for RAM reads is mGBA's PNG `gbAs` chunk:
zlib-decompress, then VRAM at `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000`.
Thus GBA `0x03007B4D` is state offset `0x20B4D`, and NES `$075F` is state offset
`0x2095F` (`0x20200 + 0x75F`).

### NES side (runtime PRG mapped at `$8000`–`$FFFF`)

| NES address | Meaning |
|---|---|
| `$8000` | RESET (`SEI CLD ...`) |
| `$8082` | NMI |
| `$FFF0` | IRQ/BRK vector |
| `$8E56` | `ReadJoypads`: `$4016` strobe, 8-bit read into `$06FC`/`$06FD` |
| `$819D` | pause routine: Start (`$06FC & $10`) toggles pause |
| `$8245` | `GameMenuRoutine` (title): Start / A+Start / Select / B / demo branches |
| `$82D8` | `ChkContinue`: A+Start loads `ContinueWorld $07FD` |
| `$830E` | `GoContinue`: writes `WorldNumber $075F`, `OffScr_WorldNumber $0766`, zeroes `AreaNumber $0760` |
| `$8491`–`$8493` | **only writer** of `WorldSelectEnableFlag $07FC` (World-8 completion path) |
| `$87F2` | `WarpZoneNumbers` table: `04 03 02 00 24 05 24 00 08 07 06 00` |
| `$8882` | `PrintWarpZoneNumbers` (draws the 4/3/2, “5”, 8/7/6 labels) |
| `$DF0C` | `HandlePipeEntry` warp path; `$DF22` `GetWNum` indexes `WarpZoneNumbers` |
| `$9CB4` | `WorldAddrOffsets`: `00 05 0A 0E 13 17 1B 20` |
| `$9CBC` | `AreaAddrOffsets` (36 bytes, four/five areas per world) |
| `$9C03` | `LoadAreaPointer` |
| `$9C13` | `FindAreaPointer`: `WorldAddrOffsets[WorldNumber] + AreaNumber` → `AreaAddrOffsets[...]` |
| `$9C22` | `GetAreaDataAddrs`: AreaPointer → `AreaData`/`EnemyData` pointers |
| `$8808` | `WriteGameText`: lives/world/level/timer text |
| `$8850` | HUD world digit: `WorldNumber+1` written directly as a tile number |

Variables: `$075F` WorldNumber, `$0760` AreaNumber, `$075C` LevelNumber,
`$076B` WorldSelectNumber, `$07FC` WorldSelectEnableFlag, `$07FD` ContinueWorld,
`$0770` OperMode, `$0772` OperMode_Task, `$077A` NumberOfPlayers, `$075A` lives,
`$06FC`/`$06FD` joypad 1/2.

## 5. Algorithm

### 5.1 Wrapper System-Menu gate and dispatch

```c
// installed handler 0x08002691, runs every frame
held    = *(u16*)0x0300648C;   // active-high
pressed = *(u16*)0x03006490;   // edge

if (held == 0x000F) {                 // A+B+Select+Start, exactly
    handler = 0x080016C9;             // NES soft reset path
}
else if (held == 0x0300 && (held & pressed)) {
    handler = 0x08002429;             // open System Menu
}

// menu handler 0x08002429
if (pressed & 0x0002) {               // B
    sel = 0; handler = 0x08001645;    // close menu (via delayed resume)
}
draw_page(page_id_for(sel));          // 0x08000FCC
switch (sel) {                        // 0x03007B4D
case 0: page = 8;  action = 0x08001645; break;  // CONTINUE
case 1: page = 8;  action = 0x080016C9; break;  // RESET
case 2: /* save path: page 49 if struct+0x992 bit7, else page 47 or 48;
           on A run 0x08004664, compare 0x08000B10()==0x180;
           success -> 0x080047C4; failure -> 0x08001E71, which draws page 41 */ break;
case 3: page = 9;  action = 0x080022D5; break;  // LINKED PLAY
case 4: page = 8;  action = 0x08001765; break;  // SLEEP/delay
}
if (pressed & 0x40) { if (sel == 0) sel = 4; else sel--; }       // Up
if (pressed & 0x84) { sel++; if (sel > 4) sel = 0; }              // Down or Select
if (pressed & 0x09) handler = action;                            // A or Start
```

The selector is a 5-slot ring (`cmp #4; bhi default` and `sel>4 -> 0`).

### 5.2 SMB title-screen menu

```c
// 0x8245 GameMenuRoutine, OperMode_Task == 3
a = SavedJoypad1Bits | SavedJoypad2Bits;
if (a == 0x10) goto ChkContinue;        // Start
if (a == 0x90) goto ChkContinue;        // A + Start
if (a == 0x20) { /* Select: toggle 1P/2P, reset demo timer */ }
if (DemoTimer == 0) { /* run attract demo */ }
else if (WorldSelectEnableFlag != 0 && a == 0x40) {
    WorldSelectNumber = (WorldSelectNumber + 1) & 7;
    GoContinue(WorldSelectNumber);      // selected world 0..7
    redraw mushroom icon;
}
// ChkContinue (0x82D8):
if (A button was also held) GoContinue(ContinueWorld);  // A+Start
LoadAreaPointer(); OperMode = 1; OperMode_Task = 0;
PrimaryHardMode = WorldSelectEnableFlag;
```

### 5.3 World-select unlock (corrected)

`WorldSelectEnableFlag $07FC` has exactly one writer in the 32 KiB PRG:

```c
// 0x8461 PlayerEndWorld (after World 8)
if (WorldEndTimer == 0) {
    if (WorldNumber >= 8) {                  // World 8
        if ((SavedJoypad1Bits|SavedJoypad2Bits) & 0x40) {  // B held
            WorldSelectEnableFlag = 1;       // 0x8493
            NumberOfLives = 0xFF;
            TerminateGame();
        }
    } else {
        AreaNumber = 0; LevelNumber = 0;
        WorldNumber++; LoadAreaPointer();
    }
}
```

A fresh boot has `WorldNumber = 0` and `$07FC = 0`; no other instruction writes
`$07FC`. Therefore B at the title cannot enable world select by itself. The
published “press B at the title after beating the game” is a compressed description
of a flag that is actually latched at the World-8 completion screen.

### 5.4 Warp/world model and the 256-world space

```c
// 0xDF0C, when a warp pipe is entered
control = WarpZoneControl & 3;
base    = control * 4;                   // 0 or 4 (0x24 row)
x       = (player_x < 0x60) ? base : (player_x < 0xA0 ? base+1 : base+2);
world   = WarpZoneNumbers[x] - 1;        // byte, wraps
WorldNumber = world;
AreaNumber  = 0; LevelNumber = 0;
AreaPointer = AreaAddrOffsets[WorldAddrOffsets[world] + 0];
```

`WorldAddrOffsets` has only 8 entries, so `world >= 8` reads past it into
`AreaAddrOffsets` and then past that into the enemy-data tables. The first eight
worlds are the only authored ones; the rest are glitch worlds. `WorldNumber` is an
8-bit value, so 256 worlds are representable; with the 8-bit `AreaNumber` the
`FindAreaPointer` query space is 65,536 combinations.

Worked values (verified against the runtime PRG bytes):

* `world = 0x00` (World 1) → `WorldAddrOffsets[0]=0x00` → `AreaAddrOffsets[0]=0x25`
  → AreaType 1 (ground) → 1-1.
* `world = 0x07` (World 8) → `0x20` → `AreaAddrOffsets[0x20]=0x30`.
* `world = 0x23` (display 36, Minus World) → `WorldAddrOffsets[0x23]=0x33`
  → `AreaAddrOffsets[0x33]=0x01` → AreaPointer `0x01` → AreaData `0xAE45`,
  EnemyData `0x9FF1` (the “Minus World” payload).
* `world = 0xFF` (display 256) → OOB byte at `$9DB3` → AreaPointer `0x9D`.
* Warp row for the 4-2/glitched zone: `24 05 24 00` → worlds 35, 4, 35, 255
  (the two `0x24` entries are the World-36 pipes; `0x00` is the 255/“0” pipe).

The HUD does not range-check the world digit: `WriteGameText` writes
`WorldNumber+1` as a tile number into the “WORLD - ” template. For world 36 the
tile is `0x24` (blank), so the visible result is the pre-existing dash plus the
level digit: “World -1”.

## 6. Tables

### 6.1 Wrapper System-Menu slots

| Slot | Page ID | Handler installed | Observed effect |
|---:|---:|---|---|
| 0 | 8 | `0x08001645` → `0x08002691` | CONTINUE: menu closes, NES resumes |
| 1 | 8 | `0x080016C9` | RESET: NES returns to title (`OperMode=0`, `Task=3`, `DemoTimer=0x16`) |
| 2 | 49, then 41 | `0x08002429`, then `0x08001E71` | SAVE HIGH SCORE: save attempted, verification fails, save-error page 41; `.sav` unchanged. (Pages 47/48 are the no-media branch, not reached here: `struct+0x992` bit 7 was set.) |
| 3 | 9 | `0x080022D5` | LINKED PLAY: link/display setup, page 45 when no partner |
| 4 | 8 | `0x08001765` → `0x08001721` → `0x08002691` | SLEEP/delay: waits for release, ~60-frame timer, auto-resume |

Menu gate/key masks: open `0x0300` + edge; Up `0x0040`; Down/Select `0x0084`;
A/Start `0x0009`; B `0x0002`; reset `0x000F`.

### 6.2 SMB title branches

| Input (OR of both pads) | Branch | Result |
|---:|---|---|
| `0x10` Start | `0x8255` → `0x82D8` | start selected world |
| `0x90` A+Start | `0x8255` → `0x82D8` | start at `ContinueWorld $07FD` |
| `0x20` Select | `0x8276` | toggle `$077A` 1P/2P |
| `0x40` B, `$07FC != 0` | `0x8271` | increment `WorldSelectNumber $076B` mod 8 |
| other | fall through | ignored (demo timer path only) |

### 6.3 Level / warp tables

`WorldAddrOffsets` `$9CB4`: `00 05 0A 0E 13 17 1B 20`
`AreaAddrOffsets` `$9CBC`:
`25 29 C0 26 60 | 28 29 01 27 62 | 24 35 20 63 | 22 29 41 2C 61 |`
`2A 31 26 62 | 2E 23 2D 60 | 33 29 01 27 64 | 30 32 21 65`

`WarpZoneNumbers` `$87F2`: `04 03 02 00 | 24 05 24 00 | 08 07 06 00`

### 6.4 Header / save artefacts

* Main header and second header both carry `SUPER MARIO`, `FSME`, maker `01`,
  version `0`, complement `0x9E`, stored checksum `0`.
* mGBA created an 8 KiB `.sav`; at boot the wrapper writes an 8-byte signature
  `5F 4F 49 52 31 18 16 03` at file offset `0x0F8` (`"RIO_1"` little-endian plus
  three version/type bytes). The SAVE path did not modify this block in any test.

## 6b. Enumeration

### Space definition

1. **Wrapper menu selector.** One byte at `0x03007B4D`; 5 representable values
   (`0x00–0x04`); ring arithmetic `(sel±1)` with a 5-slot compare; no checksum,
   no payload bits, no alphabet. Space = **5 states**.
2. **Wrapper menu input word.** 10 GBA buttons are mapped into `held`
   (`0x0300648C`), 1024 possible held masks. Only `0x0300` (L+R) with a new edge
   opens the menu; only `0x000F` resets. Tested rejection: `0x0200` (L), `0x0100`
   (R), `0x0308` (L+R+Start pre-held), `0x0301` (L+R+A pre-held).
3. **SMB title input word.** 8 NES buttons per pad; the routine ORs both pads and
   compares whole-byte values. Branches exist only for `0x10`, `0x90`, `0x20`,
   and `0x40` (the last gated by `$07FC`). All other 252 byte values fall through
   to the demo-timer path and do not start a game.
4. **World/level space.** `WorldNumber` and `AreaNumber` are 8-bit bytes:
   256 × 256 = **65,536** `FindAreaPointer` queries. The authored set is 8 worlds
   × 4 levels (plus per-world bonus areas); everything else reads out of bounds.
5. **No password space.** There is no alphabet table, no input buffer, no
   `strcmp`/`memcmp` against user text, and no password entry screen in either the
   wrapper or the emulated NES game. `strings -n 4` yields 10,163 ASCII runs; a
   case-insensitive keyword grep for
   `password|cheat|debug|secret|unlock|level|world|code|menu|select|option|sound|config|save|state|reset|system`
   yields **0** hits. All visible UI text (wrapper and NES) is tile/glyph-indexed,
   which is why absence of ASCII is not by itself the negative; the menu walk and
   the page-table enumeration above supply the positive enumeration.

### Novel / unpublished states (all reached through the game's own menus)

**N1 — SAVE HIGH SCORE failure page (not in any published list).**
Menu slot 2 + A on this cartridge runs the save routine `0x08004664`, then compares
`0x08000B10()` with `0x180`; the comparison fails and installs `0x08001E71`.
Observed RAM: `0x03006494 = 0x08001E71`, `0x03007B92` changes `0x80 → 0xA0`,
`.sav` MD5 `b72963f6d367c0f6d6aea824597f2eeb` before and after, and the failure
handler draws page 41 (`0x08001EAE`).
B then returns the handler to `0x08002691`. Published lists only mention
“SAVE HIGH SCORE” as an entry and do not describe the failure state.

**N2 — System Menu on the NES title screen (not in the “in-game” description).**
With the NES at `OperMode=0, Task=3`, holding L+R changes the handler from
`0x08002691` to `0x08002429`, exactly as in gameplay. Selector 0 and all five slots
are reachable from the title.

**N3 — Undocumented menu input aliases.** In the main menu, **Select** increments
the selector exactly like Down (`0x0084` mask; observed 1→2), **Start** activates
the selected entry exactly like A (`0x0009` mask; observed slot 1 reset the NES),
and **B** closes the menu and resets the selector to 0. These are not in the
published L+R menu descriptions.

### Bounds proven by rejection

* L alone, R alone: handler stays `0x08002691` (no menu).
* L+R+Start pre-held (`held=0x0308`): rejected; handler stays `0x08002691`.
* L+R+A pre-held (`held=0x0301`): rejected; handler stays `0x08002691`.
* Menu ring: five Downs visit 0,1,2,3,4 then wrap to 0; a sixth value is not
  representable.
* SAVE HIGH SCORE: the save path runs but its verification fails; the 8 KiB `.sav`
  is byte-identical, so no save state is produced.
* Title B with `$07FC=0`: rejected (`$0770` stays 0, `$07FC` stays 0).
* Title Start+Select and Down: rejected (`$0770` stays 0).
* World-select flag: the only writer is gated on `WorldNumber >= 8` and
  `WorldEndTimer == 0`; a fresh boot (world 0) cannot reach it by any title input.
  This is a **gated feature**, not an untested case.

### Dynamic evidence summary

| Claim | Evidence |
|---|---|
| Menu opens on L+R | `0x03006494: 0x08002691 → 0x08002429` with `held=0x0300` |
| Exact gate | pre-held `0x0308`/`0x0301` leave `0x08002691` |
| 5-slot ring | `0x03007B4D`: 0,1,2,3,4,0 |
| Select navigation | `0x03007B4D`: 1→2 after Select |
| Start activation | slot 1 + Start → `0x08002691`, `OperMode=0`, `Task=3` |
| B cancel | menu + B → `0x08002691`, selector 0 |
| Save failure | slot 2 + A → `0x08001E71`, `0x03007B92=0xA0`, `.sav` MD5 unchanged |
| NES resumes | slot 0 + A → `0x08002691`, `OperMode=1`, `Task=3` |
| NES reset | slot 1 + A/Start → `OperMode=0`, `Task=3` |
| Title Start | `$0770=1`, `$0772=1→3` |
| Title rejection | B / Start+Select / Down leave `$0770=0` |

## 7. Validation evidence

**Observed (emulator RAM/VRAM, reproducible):**

* Header hashes/fields above; two 156-byte Nintendo logos at `0x0004` and `0x0CFBC`.
* GBA key state: `x`→`0x0001`, `z`→`0x0002`, `BackSpace`→`0x0004`,
  `Return`→`0x0008`, `Right`→`0x0010`, `Left`→`0x0020`, `Up`→`0x0040`,
  `Down`→`0x0080`, `s`→`0x0100`, `a`→`0x0200` at `0x0300648C`.
* System-Menu handler transitions and selector values as in §6b.
* Save failure handler/byte as in §6b; `.sav` MD5 unchanged.
* NES `$075F/$0760/$075C = 0/0/0` at the start of World 1-1; HUD nametable reads
  “WORLD 1-1”.
* Title Start sets `$0770=1`; rejected combos leave `$0770=0`.
* Wrapper soft reset (`A+B+Select+Start`) reaches `OperMode=0`, `Task=1`.

**Derived (instruction sequence in the runtime PRG / wrapper):**

* System-Menu gate, 5-slot jump table, handler addresses and page IDs.
* SMB title branches and the corrected `$07FC` writer at `0x8491–0x8493`.
* Warp-table indexing, out-of-bounds `WorldAddrOffsets` lookup, world-36
  AreaPointer `0x01` → AreaData `0xAE45`, EnemyData `0x9FF1`.
* HUD world digit = `WorldNumber+1` written as a tile number.

**Inferred:**

* The exact English glyph text of wrapper pages 8/9/41/47/48/49. The page table,
  renderer and tile table were located, but the 4bpp glyph encoding was not fully
  inverted; slot labels in §6.1 are inferred from their handlers/effects and the
  shared series menu, not from OCR.
* Slot 4's “SLEEP MODE” wording; the handler sequence and ~60-frame delay were
  observed, the exact blanking transient was not captured frame-by-frame.
* LINKED PLAY multiboot transfer was not exercised (requires a second GBA); the
  second header and loader code are static evidence.

## 8. Unknowns

* Exact page text for the wrapper menu/error pages (glyph encoding not inverted).
* Root cause of the SAVE verification failure (`0x08000B10() != 0x180`); the save
  medium exists and receives the boot header, so this is a software/verification
  failure rather than “no SRAM”.
* Whether the real cartridge's save type differs from mGBA's 8 KiB SRAM.
* Dynamic entry to World 36 was not attempted; it requires the published World 1-2
  wall-clip glitch. The level payload and warp bytes are fully derived here.
* The exact purpose of the second multiboot image beyond LINKED PLAY.

## 9. Tooling

* mGBA 0.10.5 (SDL) under Xvfb `:254` + openbox; `xdotool` for XTEST key events.
* `arm-none-eabi-objdump` (`-M force-thumb` / ARM) for wrapper/GBA code.
* `da65` (cc65) and the doppelganger SMB disassembly (6502disassembly.com) as a
  cross-reference for the NES PRG; all addresses above were re-checked against the
  runtime PRG bytes.
* Python 3 + `zlib` savestate parser (`state.py`, `menutext.py`) for RAM/VRAM reads;
  no screenshots or image files were used.
* `.sav`/`.ss*` artifacts were kept in `/tmp/opencode/cnessmb`, not next to the ROM.

## Legal

No ROM, graphics, music or game text is redistributed. Only hashes, addresses,
instruction sequences, table values and derived menu/selector facts are published.
