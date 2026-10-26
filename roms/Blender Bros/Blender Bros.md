# Blender Bros (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Blender Bros/Blender Bros.gba` |
| Size | 8,388,608 bytes (8 MiB), last bytes zero padding |
| Header title | `BLENDER BROS` |
| Game code | `ABRE` (USA) |
| Maker code | `70` |
| Software version | 0 (Rev.00) |
| Fixed byte / unit / device | `0x96` / 0 / 0 |
| Complement check | `0x7E` (recomputed `0x7E` — valid, unpatched header) |
| Entry branch | `ea00002e` → `0x080000C0` (standard crt0) |
| MD5 | `8aa4f88927f3c5bf1aaed1562742a64d` |
| SHA-1 | `485b1698b4005bc15a83982b85bac68bbbae40ec` |
| SHA-256 | `5d9a18f14392d823c88de21a73ce7cd57baa5a4fac47c6ab0bad0956d6eb34b4` |

Embedded GBA-header scan (Nintendo logo at every hit, then title/code at `+0xA0`/`+0xAC`):

| Logo at | Header | Title | Code | Maker |
|---:|---:|---|---|---|
| `0x000004` | `0x000000` | `BLENDER BROS` | `ABRE` | `70` |
| `0x085008` | `0x085004` | `BLENDER BROS` | `ABLJ` | `AP` |
| `0x086F44` | `0x086F40` | (empty) | `AGBJ` | `01` |
| `0x099E88` | `0x099E84` | (empty) | `AGBJ` | `01` |
| `0x0AF2E8` | `0x0AF2E4` | (empty) | `AGBJ` | `01` |
| `0x0C20CC` | `0x0C20C8` | (empty) | `AGBJ` | `01` |
| `0x0CD91C` | `0x0CD918` | (empty) | `AGBJ` | `01` |
| `0x0E00D8` | `0x0E00D4` | (empty) | `AGBJ` | `01` |
| `0x0EA9D8` | `0x0EA9D4` | (empty) | `AGBJ` | `01` |
| `0x0F59DC` | `0x0F59D8` | (empty) | `AGBJ` | `01` |

The image at `0x085004` is preceded by a 32-bit size word `0x0006A400`
(file `0x085000`), i.e. it is a multiboot child image with its own crt0
(`ea00002e`), not a second playable game. Its game code `ABLJ` is the
**Japanese** Blender Bros code; the Japanese release was cancelled, so the
link-play payload appears to be built from the JP line (observation; the
"JP build" label is inference). The eight `AGBJ` headers are 156-byte logo +
header stubs spaced through the same region — multiboot slave headers, not
games.

**No trainer, no intro, no patch**: the ROM begins with the Nintendo logo and
the normal crt0 branch, the complement check matches, and the file has no
extra bytes before `0x08000000`.

## 2. Executive summary

Blender Bros has **no password, no keypad code, no button cheat and no
options screen**. The words `PASSWORD`, `PASSWD`, `CHEAT`, `CODE`, `OPTION`,
`CONFIG`, `SECRET` and `UNLOCK` do not occur anywhere in the 8 MiB image
(case-sensitive ASCII scan, zero hits each). All menus were walked: title,
boot resume menu, main menu, file select, Cosmo Heaven hub, stage select,
in-game pause. The pause menu has exactly two entries (`Mini Bros.`, `EXIT`).

The only developer cheat surface is a complete **AGB SDK debug menu** that is
still linked into the retail ROM. It is reachable through the game's task
system: task 0's function pointer lives at `0x03001AA8`; the ROM contains one
stub (`0x080049A4`, case 44 of the debug screen dispatcher) that installs
`0x08008FD9`, the debug-menu start routine. Nothing else in the ROM writes
that pointer, and no button sequence in the retail build reaches case 44 —
`L + R` at the title, in the hub, and in the pause menu does nothing (tested).
The widely published "press L+R" is the **CodeBreaker conditional**
(`74000130 00FF`) that makes the cheat device perform the pointer poke while
the buttons are held; the game itself has no L+R handler. The menu therefore
appears the instant the pointer is installed, without any key press.

The debug menu exposes 16 rows, a 16-entry screen launcher (`MENU TEST`), three
test rooms, a tile editor, an entity editor, a sprite/collision-box viewer, a
4-player link test, a music/SFX player, a sprite data viewer, and a 49-entry
internal screen table of which only 16 are listed in `MENU TEST`. Parameter
fields have real, testable bounds (`MAIN GAME TEST` 0–60, clamped;
`MINI BROS NUM` 0–20, wrapping; `MINI GAME`, `SINGLE BOOT`, `MULTI BOOT` 0–3,
clamped).

`MAIN GAME TEST` is the closest thing this game has to a "code": a numeric
scene selector, `000`–`060` (61 values, further presses rejected at 60), which
launches that developer scene with the collision/tile grid overlay.
Unpublished values were minted and confirmed in-game: `005` (seaside
creature), `010` (desert intro with Palty's "Emergency!" speech), `015`/`020`
(station corridor), `030` (space-station boss fight) and `060` (the maximum:
rocky canyon area); `040`/`050` fall back to the generic grid test map.
A second unpublished value, `MINI BROS NUM = 20` (the twenty-first,
undocumented value of that field), makes `MAIN GAME TEST`
boot with the maximum life gauge displayed, while `MINI BROS NUM = 00` boots
the same map with three hearts and no gauge.

No GameShark/CodeBreaker/memory-edit code is proposed as a result. The
`0x03001AA8` pointer is documented as an **address-map fact** and was written
with a debugger only to make the developer menu reachable for enumeration;
that write is instrumentation, not a deliverable cheat.

## 3. How to reproduce

### 3.1 Environment

```
Xvfb :188 -screen 0 1280x960x24
DISPLAY=:188 openbox
DISPLAY=:188 SDL_AUDIODRIVER=dummy mgba -3 "roms/Blender Bros/Blender Bros.gba"
```

mGBA 0.10.5 (SDL), default keymap: **A = `x`, B = `z`, L = `a`, R = `s`,
Start = `Return`, Select = `BackSpace`, D-pad = arrows**.
Screenshots: `import -window <winid> out.png` (window is 720×480 at 3×).

Note on key timing: the debug menu is edge-triggered but auto-repeats after a
few frames, so a 50 ms tap can move 2–3 rows. For deterministic single steps
use ≈20 ms key-down with ≥150 ms between presses; for value fields use one
short tap per increment and read the value back after each press.

### 3.2 Reaching the debug menu

The retail build has no input path to it. For enumeration the task pointer was
installed with mGBA's GDB stub:

```
mgba -3 -g "Blender Bros.gba"            # waits for gdb on :2345
gdb-multiarch -q -ex "set architecture arm" -ex "target remote :2345" \
  -ex "set *(unsigned int*)0x03001AA8 = 0x08008FD9" -ex "continue"
```

The menu appears on the next frame (see 3.3). A savestate taken at this
point (`Blender Bros.ss5`, `F5` to load) makes every later test one keypress.

The GDB server accepts one connection and stops listening after the client
disconnects; restart mGBA (or use the savestate) for another poke.

### 3.3 Menu paths used in this report

| Screen | Path |
|---|---|
| Debug main menu | pointer poke (above); cursor starts on `GAME START` |
| `MENU TEST` list | debug menu → 3×Down → A |
| `TEST1` / `TEST2` / `TEST3` | debug menu → 4 / 5 / 6×Down → A |
| `ENTRY EDIT` | debug menu → 8×Down → A |
| `HIT EDIT` | debug menu → 9×Down → A |
| `MULTI PLAY TEST` | debug menu → 10×Down → A |
| `SOUND MENU` | debug menu → 14×Down → A |
| `DATA VIEW` | debug menu → 15×Down → A |
| `MAIN GAME TEST` | debug menu → 1×Down → A (uses `MINI BROS NUM`) |
| Main menu | title `PRESS START` (Return) ×4 → `New Game / Load Game / Multiplayer` |
| Resume menu | boot with a save present → `Continue / Load` |
| File select | `New Game` or `Load Game → Load` |
| Pause | in game, Start (`Return`) |

`B` (`z`) returns from the debug sub-screens to the debug main menu. The
player-facing screens launched from `MENU TEST` (stage select, shop, etc.) do
**not** return with B or L+R; they are ordinary game screens.

### 3.4 Published codes tested

* `74000130 00FF / 83001AA8 8FD9 / 83001AAA 0800` (CodeBreaker, "Press L+R
  to access") — the raw ROM contains no writer for those addresses from input;
  loading the three lines through `mgba -c` produced no effect at the title
  or in the hub, and holding L+R at the title, in the hub and in the pause
  menu produced no effect (screenshots `lr.png`, `lr34.png`, `lrx12.png`).
* `L + R` alone, in the same three places — no effect.
* The literal `0x08008FD9` occurs exactly once in the ROM (`0x049AC`), so the
  only in-ROM way to start the menu is the stub at `0x080049A4`.

## 4. Address map

File offset = ROM address − `0x08000000`.

| ROM address | What |
|---|---|
| `0x080049A4` | case-44 stub: `ldr r0,=0x08008FD9; bl task0_set; b epilogue` — only reference to the debug entry |
| `0x08008FD8` | debug entry (`0x08008FD9` Thumb). Allocates the SDK text console (`0x08001DD0(0x40)`, `0x08001E30`), reads the menu flag, then `0x0800253C(0x08008F5D)` |
| `0x08008F5C` | transition: waits on fade counter `0x03002498`, then `task0 = 0x080048A5`; prints the frame counter with `"%05d"` at `0x08063C24` |
| `0x080048A4` | **debug menu main loop** (`0x080048A5`). First call: `0x08002850` (set 49 enable bytes), `0x08004780`, `0x08002868(17,3)`; then `0x0800289C` (layer/console service); then dispatch |
| `0x080048E0` | 49-entry screen dispatch table (`u32` stubs) |
| `0x08002868(id, flag)` | `*(u16*)0x03001B20 = id; 0x03001A20[id] = flag` |
| `0x0800287C` | `get_screen_id()` → `*(u16*)0x03001B20` |
| `0x08002888` | `get_screen_flag()` → `0x03001A20[*(u16*)0x03001B20]` |
| `0x0800253C` | task-0 setup: `0x080024C8(0, func)` then `0x080024FC(0)` |
| `0x080024C8` | task table base `0x03001AA0`, 12-byte records `{state, arg, func}`; writes state=4, arg=0, func |
| `0x08002570` | task runner: for 8 tasks, state 2 → call `func` |
| `0x080025BC` | key scan: `~KEYINPUT` → `0x03001B18` (held), new presses → `0x03001B10`, previous → `0x03003B28`, copies `0x03001E34` / `0x030032A8`; zeroes turbo counters |
| `0x03001AA0` | task 0 record (state, arg, func) — **gate at `0x03001AA8`** |
| `0x03001B10` | new key presses (active high) |
| `0x03001B18` | held keys (active high) |
| `0x03001B20` | current screen id (u16), 1..49 |
| `0x03001A20` | 49-entry screen enable/flag bytes |
| `0x03003710` | frame counter (printed as `%05d`) |
| `0x03002498` | fade/transition counter |

String table (ROM addresses; ASCII, NUL-terminated, in the SDK object that
begins at `0x0863888` with the printf helpers):

| Address | String |
|---|---|
| `0x0863974` | `--- AGB SYSTEM  DEBUG MENU ---` |
| `0x0863994` | `GAME START %s` |
| `0x08639A4` | `MAIN GAME TEST = %3d` |
| `0x08639BC` | `MINI BROS NUM = %2d` |
| `0x08639D0` | `MENU TEST` |
| `0x08639DC` / `E4` / `EC` | `TEST1` / `TEST2` / `TEST3` |
| `0x08639F8` | `ENTRY EDIT` |
| `0x0863A04` | `HIT EDIT` |
| `0x0863A10` | `MULTI PLAY TEST` |
| `0x0863A20` | `MINI GAME   = %2d` |
| `0x0863A34` | `SINGLE BOOT = %2d` |
| `0x0863A48` | `MULTI  BOOT = %2d` |
| `0x0863A5C` | `SOUND MENU` |
| `0x0863A68` | `DATA VIEW` |
| `0x0863A7C` | `TITLE` |
| `0x0863A84` | `STAGE SELECT` |
| `0x0863A94` | `MINI BROS SELECT` |
| `0x0863AA8` | `GAME OVER` |
| `0x0863AB4` | `SHOP ITEM SELECT` |
| `0x0863AC8` | `MINIGAME SELECT` |
| `0x0863AD8` | `COSM STATION` |
| `0x0863AE4` | `CI` |
| `0x0863AEC` | `MINI BROS SELECT MAIN` |
| `0x0863B04` | `MUSIC` |
| `0x0863B0C` | `CLEAR TIME` |
| `0x0863B18` | `SAVE` |
| `0x0863B20` | `BCHG1` |
| `0x0863B28` | `OPENING:` |
| `0x0863B34` | `ENDING:` |
| `0x0863B3C` | `DEBUG TITLE:` |
| `0x08648E4` | `20010919A` (build date, printed by `GAME START %s`) |
| `0x0863EC0` | `STAGE %d-%d` |
| `0x0863F54` | `SRAM_V112` (SDK marker) |

Related SDK strings at `0x0863DCC`–`0x0863E98` are the 19 Mini Bros romaji
names (`MARUN`, `PORUN`, `MERUN`, `NAKKURU` … `CHU-PI-`) used by the data/edit
screens.

## 5. Algorithm

### 5.1 Debug-menu gate (the only "cheat" mechanism)

```
task[0] = { state: u32, arg: u32, func: u32 } @ 0x03001AA0
every frame:
    # 0x08002570
    for t in 0..7:
        if t.state == 1 and --t.arg == 0: t.state = 2
        if t.state == 2: call t.func
        else if t.state == 3: t.state = 2

# entry installed by the ROM stub 0x080049A4 (case 44 of 0x080048E0 table)
task[0].state = 4
task[0].arg   = 0
task[0].func  = 0x08008FD9      # -> 0x08008FD8

# 0x08008FD8 / 0x08008F5C
console_alloc(0x40); console_clear()
wait for fade counter @0x03002498
task[0].func = 0x080048A5        # debug menu main loop
```

Menu loop (`0x080048A4`):

```
if screen_id == 0:
    for i in 0..48: flag[i] = 1
    screen_set(17, 3)            # start on screen 17
console_service()
id = screen_id
if 1 <= id <= 49: pc = table[id-1]
```

There is **no length check, no string compare and no key sequence** anywhere in
this path: the menu is a screen that is simply not selected by retail code.

### 5.2 Password / code model

None exists. The negative is bounded by:

* ASCII scan of all 8 MiB: `PASSWORD` 0, `PASSWD` 0, `CHEAT` 0, `CODE` 0,
  `OPTION` 0, `CONFIG` 0, `SECRET` 0, `UNLOCK` 0; `DEBUG` 2 (both in the SDK
  menu block, `0x63984` and `0x63B3C`), `STAGE` 3, `SAVE` 1.
* Every screen reachable from the title, main menu, file select, hub, pause
  and the debug menu was rendered and inspected; no alphabetic entry widget,
  no keypad and no "enter code" prompt appears in any of them.
* There is no SRAM/Flash/EEPROM password fallback: the cart saves normally
  (32 KiB `.sav` written by mGBA).

## 6. Tables

### 6.1 Debug main menu (16 rows, cursor order top→bottom)

| # | Row text | Kind | Observed effect |
|---:|---|---|---|
| 0 | `GAME START 20010919A` | action | cold-boots the game (logos → title) |
| 1 | `MAIN GAME TEST = %3d` | value | scene selector 0–60 (clamps at 60); `A` starts that developer scene with the debug grid overlay |
| 2 | `MINI BROS NUM = %2d` | value | selects a Mini Bro slot (effect observed on `MAIN GAME TEST` starts); 0–20, wraps |
| 3 | `MENU TEST` | action | opens the 16-screen launcher (6.2) |
| 4 | `TEST1` | action | tile/BG test screen (repeating tile pattern) |
| 5 | `TEST2` | action | field test map (grass road, mountains, player control) |
| 6 | `TEST3` | action | "TEST" tile-map room with player + numbered orbs |
| 7 | `=` (thin separator row) | inert | selectable, does nothing |
| 8 | `ENTRY EDIT` | action | map-entity editor: `MAP`, `NUMBER`, `NAME`, `MUKI`, `POS` |
| 9 | `HIT EDIT` | action | sprite + collision-box viewer |
| 10 | `MULTI PLAY TEST` | action | 4-player link test (4 Blenders, per-unit counters) |
| 11 | `MINI GAME = %2d` | value | 0–3, clamps |
| 12 | `SINGLE BOOT = %2d` | value | 0–3, clamps |
| 13 | `MULTI BOOT = %2d` | value | 0–3, clamps |
| 14 | `SOUND MENU` | action | music/SFX player with per-channel status |
| 15 | `DATA VIEW` | action | sprite data viewer (`DATA=0000`, 4 quadrants) |

### 6.2 `MENU TEST` — 16-screen launcher

| # | Label | Screen shown |
|---:|---|---|
| 0 | `TITLE` | `PRESS START` title screen |
| 1 | `STAGE SELECT` | Cosmo Heaven planet/stage select |
| 2 | `MINI BROS SELECT` | Mini Bros selection room |
| 3 | `GAME OVER` | Game Over screen |
| 4 | `SHOP ITEM SELECT` | "Music Shop" purchase screen |
| 5 | `MINIGAME SELECT` | "Mini Game room" (Cosmoride Race) |
| 6 | `COSM STATION` | Cosmo Heaven hub with Palty dialogue |
| 7 | `CI` | Infogrames logo / copyright card |
| 8 | `MINI BROS SELECT MAIN` | "Mini Bros. Room" hub screen |
| 9 | `MUSIC` | "Change Music" record player |
| 10 | `CLEAR TIME` | "Clear Time" per-area table |
| 11 | `SAVE` | "Select file" save screen |
| 12 | `BCHG1` | "Trade Room", link-cable `Checking connection…` |
| 13 | `OPENING:` | opening cutscene (planet + Zooligan logo) |
| 14 | `ENDING:` | ending art (`COSMO HEAVEN`) |
| 15 | `DEBUG TITLE:` | blank white screen (no output observed) |

The order above is the on-screen order; the cursor starts on `TITLE`.

### 6.3 49-entry screen dispatcher (`0x080048E0`)

Index = `screen_id − 1`. Values are the case stubs; `0x08004C82` is the
function epilogue (no-op case).

| id | stub | installs task func | id | stub | installs task func |
|---:|---|---|---:|---|---|
| 1 | `080049D4` | `0800F9FD` | 26 | `08004AAC` | `08051919` |
| 2–9 | `08004C82` | — | 27 | `08004AB8` | `08052C51` |
| 10 | `080049E0` | `0803D8DD` | 28 | `08004A94` | `08053E49` |
| 11 | `080049EC` | `08041041` | 29 | `08004AC4` | `080544B9` |
| 12 | `080049F8` | `080433FD` | 30 | `08004BF4` | (stub layout differs) |
| 13 | `08004A04` | `080440C1` | 31 | `08004B94` | (stub layout differs) |
| 14 | `08004A10` | `0804562D` | 32 | `08004A4C` | `08048AB5` |
| 15 | `08004A1C` | `08046AE9` | 33–37 | `08004C82` | — |
| 16 | `08004A28` | `08047FE1` | 38 | `080049BC` | `0800D62D` |
| 17 | `08004A34` | `08048375` | 39 | `080049C8` | `0800E1D9` |
| 18 | `08004A40` | `080486DD` | 40 | `08004ADC` | `08009E15` |
| 19 | `08004A58` | `08049C71` | 41 | `08004AE8` | `0800A3D9` |
| 20 | `08004AD0` | `0804BAE1` | 42 | `08004AF4` | `0800ABA1` |
| 21 | `08004A64` | `0804B469` | 43 | `08004B00` | `0800B12D` |
| 22 | `08004A70` | `0804BF01` | **44** | **`080049A4`** | **`08008FD9` (debug menu)** |
| 23 | `08004A7C` | `0804D825` | 45 | `080049B0` | `08009B1D` |
| 24 | `08004A88` | `0804F471` | 46–48 | `08004B0C` | shared handler |
| 25 | `08004AA0` | `08053C29` | 49 | `08004B6C` | shared handler |

`screen_set(id, 1)` with `id = 44` occurs at 24 sites in the UI code
(`0x04732`, `0x0AC1A`, `0x0D28E`, `0x0D298`, `0x0F398`, `0x3C532`,
`0x3DBDC`, `0x410CA`, `0x43514`, `0x44136`, `0x456B4`, `0x46B7C`,
`0x4805E`, `0x483EA`, `0x48754`, `0x48B2C`, `0x49CFA`, `0x4BB52`,
`0x4BF78`, `0x4D8A4`, `0x4F4F2`, `0x51992`, `0x52CC6`, `0x53EBE`) — the
"return to debug main menu" handlers of the test screens. No retail input path
that executes one of them was found.

### 6.4 Parameter fields (measured)

| Field | Domain | Behaviour at the edge |
|---|---|---|
| `MAIN GAME TEST` | 0…60 (61 values) | `60` + Right ×100 → stays `060`; `60` + Left → `059` |
| `MINI BROS NUM` | 0…20 (21 values) | `20` + Right → `00` (wraps) |
| `MINI GAME` | 0…3 | `3` + Right → `3` (ignored, 12 presses) |
| `SINGLE BOOT` | 0…3 | `3` + Right → `3` (ignored) |
| `MULTI BOOT` | 0…3 | `3` + Right → `3` (ignored) |
| `ENTRY EDIT / MAP` | `%02d`, increments | 01…10 observed one press at a time; upper bound not established |
| `ENTRY EDIT / NUMBER` | `%03d` | `000` (not exercised) |

### 6.5 Key state (for any future button-code work)

`0x03001B18` = held keys, active high (`A=1, B=2, Select=4, Start=8,
Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`);
`0x03001B10` = keys newly pressed this frame. Both are produced by
`0x080025BC` from `0x04000130`.

## 6b. Enumeration

### 6b.1 What the space is

There is **no password alphabet and no key sequence**, so the enumerable
cheat space is the debug menu itself:

| Space | Size | Evidence |
|---|---|---|
| Debug main rows | 16 (15 actions/values + 1 inert separator) | walked top→bottom, each row entered |
| `MENU TEST` screens | 16 | each launched and screenshotted |
| Internal screen table | 49 cases (`id 1..49`) | table dumped at `0x080048E0`; 13 no-op entries + 3 shared-handler entries |
| `MINI BROS NUM` | 21 values (0…20) | wrap measured |
| `MINI GAME` / `SINGLE BOOT` / `MULTI BOOT` | 4 values each (0…3) | clamp measured |
| `MAIN GAME TEST` | 61 values (0…60) | clamp measured at 60 |
| `ENTRY EDIT` fields | `MAP` 0…≥10, `NUMBER` 000…, `NAME`, `MUKI`, `POS` | editor exercised |
| `SOUND MENU` IDs | not enumerated | see Unknowns |

The retail build exposes none of this; the published "debug code" is a
CodeBreaker conditional that pokes `0x03001AA8`. That is a device-side poke,
not an in-game code, and is not reproduced here as a cheat.

### 6b.2 Novel, unpublished values confirmed in-game

**(a) `MAIN GAME TEST = 010`, `= 030`, `= 060` — the undocumented numeric
scene selector.**

This is the one true code-like field in the game: a three-digit value, all of
whose meaningful values are absent from every published list (GameFAQs,
VGChartz, TCRF, mushroom32x and gamehacking describe the menu or give RAM
pokes; none gives a scene table).

Procedure (from a fresh debug menu): `Down` once (cursor on
`MAIN GAME TEST`) → `Right` per increment → `A` to start.

* `000` → developer test map (black tile grid, Palty intro, no stage art).
* `005` → seaside scene with a large purple creature (`scene5.png`).
* `010` → desert opening scene, Palty: "Emergency! … one who can prevent this
  deep impact!" (`mt010.png`).
* `015` / `020` → space-station corridor / platform, Palty: "Move up and down"
  (`scene15.png`, `scene20.png`).
* `030` → space-station boss encounter, debug tile grid overlay visible
  (`mt30.png`).
* `040` / `050` → fall back to the generic black grid test map (`scene40.png`,
  `scene50.png`).
* `060` → the maximum; rocky canyon scene with a spinning NPC (`mt060.png`).

The range is therefore a **test-ID space**, not a 1:1 stage list: several IDs
share the generic test map, while 005/010/015/020/030/060 each start a distinct
scene. Only three of the 61 values are documented anywhere publicly: none.

The value is the deliverable "novel code": it is generated/selected by us, it
is not on any published list, the game accepts it, and the effect is a
different scene in each case.

**(b) `MINI BROS NUM = 20` — the undocumented 21st value.**

No published list gives values for this field. Its range is 0…20, i.e. 21
values, while the game has 20 Mini Bros; `20` is therefore a reserved/extra
slot.

Procedure: debug menu → `Down`, `Down` (cursor on `MINI BROS NUM`) →
20 × `Right` (value reads `20`) → `Up` (cursor on `MAIN GAME TEST`, value
`000`) → `A`.

* Observed (`mb20bc.png`): `MINI BROS NUM = 20`.
* Observed (`mb20_1.png`): `MAIN GAME TEST` boots with a **full purple/yellow
  life gauge** across the top-left.
* Control (`ctrl0.png`): identical path with `MINI BROS NUM = 00` boots the
  same map with three hearts and **no gauge**.
* Inference: value 20 selects a reserved slot that also switches on the
  maximum-life state; the exact consumer was not isolated.

**(c) `MENU TEST → CI` — an unlisted screen.**

`CI` (row 8 of the launcher) is not described in any public write-up of the
menu. It renders the Infogrames logo card (`mt_7.png`). `OPENING:` and
`ENDING:` likewise play the cutscenes directly (`sub13.png`, `sub14.png`), and
`BCHG1` opens the link `Trade Room` (`sub12.png`).

**(d) `TEST2`/`TEST3`/`ENTRY EDIT`/`HIT EDIT`** are developer maps/tools that
no published list documents; screenshots `test1c.png` (TEST2 field map),
`scr6.png` (TEST3), `scr8.png` (ENTRY EDIT), `scr9.png` (HIT EDIT).

### 6b.3 Bounds proven by rejection

| Input | Result |
|---|---|
| `MAIN GAME TEST` at 60, press Right ×100 | stays `060` — the field refuses 61 (`mt_range.png`) |
| `MAIN GAME TEST` at 60, press Left | `059` — the clamp is one-sided, not a wrap |
| `MINI GAME` at 3, press Right ×12 | stays `03` — the menu refuses out-of-range input (`mg14.png`, OCR `03` for presses 3–14) |
| `SINGLE BOOT` at 3, press Right ×6 | stays `03` (`b12_3..6.png`) |
| `MULTI BOOT` at 3, press Right ×6 | stays `03` (`b13_3..6.png`) |
| `MINI BROS NUM` at 20, press Right | wraps to `00` — 21 is not representable (`w5.png`) |
| `MINI BROS NUM` at 03, 20 × Left | `04` (3 − 20 ≡ 4 mod 21), proving modulo-21 arithmetic |
| `ENTRY EDIT / MAP` at 10, 120 × Right | moved off 10 (no clamp at 10); upper bound not established |

### 6b.4 Published-list cross-check

* The only published Blender Bros "cheat" that touches the debug menu is the
  CodeBreaker block above; its effect was reproduced **by installing the same
  pointer with a debugger**, not by the code itself.
* `almarsguides` "Press L+R To Access Debug Menu / 3D7B82CC 878A4667 /
  439B6256 39859717" is an encrypted GameShark variant of the same poke; not
  executable as a native code and not reproduced as a deliverable.
* No published code was found that names a password, keypad or button
  sequence. Nothing to verify against the ROM, and nothing in the ROM to
  verify.

### 6b.5 Button-code negative, with counts

* Scanned all 8 MiB for runs of ≥4 little-endian `u16` values drawn from the
  10 single-button masks and their 2-button combinations: **10,421 runs**
  (7,536 of length ≥6, 5,100 of length ≥10). Only **7** runs have a `u32`
  literal pointing at them (`0x3B13FA` len 238, `0x371F00` len 21, `0x0C0A04`,
  `0x71AFE`, `0x71FA8`, `0x0BFB06`, `0x420F00`); those are small-integer data
  tables (animation/frame counts), not key sequences, and none is read next
  to a key-state compare. The longest runs (≥400) sit in the graphics region
  around `0x2CCD64`/`0x301B82`/`0x38300E`.
* The only `KEYINPUT` readers are `0x080025BC` (the global scan) and nine
  later loader/diagnostic sites (`0x07854`, `0x894C4`, `0x8DE1C`, `0xB1868`,
  `0xB61C0`, `0xCFE9C`, `0xD47F4`, `0xECF5C`, `0xF1A24`); none of them
  compares a sequence.
* Dynamic: `L+R` was held at the title, in the Cosmo Heaven hub and in the
  in-game pause menu; no screen change (screenshots `lr.png`, `lr34.png`,
  `lrx12.png`). This is the only "press X" instruction attached to the
  published Blender Bros code, and it is the CodeBreaker condition, not a
  game-side handler.

## 7. Validation evidence

**Observed (emulator screenshots / RAM reads)**

* Debug menu rendered with all 16 rows and build date `20010919A`
  (`fresh.png`, `dbg2.png`); appears immediately after the pointer write,
  with no key press.
* `L+R` at the title, in the hub and in the pause menu does nothing
  (`lr34.png`, `lrx12.png`).
* All 16 debug rows and all 16 `MENU TEST` screens rendered (`scr4/6/8/9/10/14/15`,
  `mt_4`, `mt_7`, `ms_5`, `ms_6`, `sub0/2/3/9/10/11/12/13/14`, `mbsm`, `dbgt23`).
* `MAIN GAME TEST` measured 000 → 060 → (100 × Right, unchanged) → 059 on one
  Left (`mt_range.png`, `mt59c.png`), and three scene values launched:
  010 (`mt010.png`), 030 (`mt30.png`), 060 (`mt060.png`).
* `MINI BROS NUM` wrap and the `MINI GAME`/`SINGLE BOOT`/`MULTI BOOT` clamps
  read back from the screen (`w1..w5.png`, `mg1..mg14.png`, `b12_*`, `b13_*`).
* `0x03001AA0` = `{state=3, arg=0, func=0x080048A5}` while the menu runs;
  after the poke it becomes `{func=0x08008FD9}` and then `0x08008F5D`
  (GDB reads, section 3.2).
* Pause menu contents: `Mini Bros.`, `EXIT`, `Play Time` (`ps1.png`).

**Derived (instruction-level)**

* `0x080049A4` is the only code that materialises `0x08008FD9`
  (single occurrence at `0x049AC`); it is reached only when
  `*(u16*)0x03001B20 == 44`.
* `0x08002570` calls `task[0].func` every frame; `0x08002868` is the only
  writer of `0x03001B20`; `0x0800253C`/`0x080024C8` are the only writers of
  `task[0].func`.
* Build date and menu labels come from the ASCII block at `0x0863974`; the
  bottom-right counter is `"%05d"` of `0x03003710` (`0x08008F5C`).

**Inferred**

* The ABLJ multiboot payload at `0x085004` is the cancelled Japanese build's
  link-play image (game code letter changed `E`→`J`, maker `70`→`AP`).
* `MINI BROS NUM = 20` selects a reserved slot that also enables the max life
  gauge; the exact consumer was not traced.
* The 24 `screen_set(44,1)` sites are the test screens' "return to debug menu"
  handlers; none was observed executing in retail play.

## 8. Unknowns

* **How the menu strings are addressed.** No `u32` literal, Thumb `ADR`, or
  `u16` offset table in the ROM points at `0x0863974`…`0x0863B3C`, even though
  the text is drawn verbatim. The menu uses the SDK text console (`printf` at
  `0x08005904`, e.g. `"%05d"` in `0x08008F5C`), but the reference form for the
  label block was not located. A future pass should breakpoint `0x08005904`
  while the menu is up and read `r1`.
* Whether any of the 24 `screen_set(44,1)` call sites can be reached in retail
  play under a save/game-state condition; no input path was found, but the
  conditions were not exhaustively driven.
* The remaining 52 `MAIN GAME TEST` values (9 of 61 sampled: 000, 005, 010,
  015, 020, 030, 040, 050, 060) were not mapped; the range is a test-ID space
  with fallbacks, not a 1:1 stage list.
* `MINI GAME` / `SINGLE BOOT` / `MULTI BOOT` (values 0–3) were bounded but
  their consumers were not traced.
* `SOUND MENU` music/SFX ID space (000…?) was not enumerated; `VOLUME` reads 7.
* `DATA VIEW` did not respond to Right/Up in the entered state; its navigation
  keys were not determined.
* Whether the `AGBJ` multiboot stubs are separate mini-game payloads or merely
  loader headers; not needed for the cheat question.
* `DEBUG TITLE:` renders a blank white screen in this build; whether it is a
  broken test or a timing artifact was not determined.

## 9. Tooling

* mGBA 0.10.5 (SDL), `Xvfb :188`, `openbox`, `xdotool`, `import`/ImageMagick,
  `tesseract` (menu OCR), `gdb-multiarch` (task-pointer write and RAM reads).
* GNU binutils 2.44 `arm-none-eabi-objdump` for Thumb listings.
* Python 3 + capstone 5.0.7 for PC-relative literal resolution and BL scans;
  a small scanner for `ADR` and for `u16` button-mask runs.
* Scripts (in `/tmp/opencode/blenderbros`): `dis1.py` (Thumb disassembler with
  literal annotation), ad-hoc scanners for literals/`BL`/`ADR`/mask runs.
* Savestate `Blender Bros.ss5` (debug menu at `GAME START`) is an emulator
  artifact; `.sav`/`.ss*` are git-ignored.

**Legal note.** No ROM image, extracted graphics, music or game text beyond
short menu labels is redistributed here; only addresses, algorithms, hashes
and observations.
