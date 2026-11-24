# Defender of the Crown (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Defender of the Crown/Defender of the Crown.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `DOTC` (0xA0, space/NUL padded) |
| Game code | `ADHE` (0xAC) |
| Maker code | `5N` (0xB0) |
| Software version | 0 (0xBC) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock GBA crt0; `mov r0,#0x12; msr cpsr…` at 0xC0) |
| Complement check | stored `0x92`, computed `0x8E` → header was rebuilt/edited |
| Header checksum | stored `0x0000` (the usual artifact of a rebuilt header) |
| MD5 | `7ba10bec1582dc62d0a1ac742af9ab7b` |
| SHA-1 | `efbea6dfa027a578e4f9878768a82c9bd7f2c31c` |
| SHA-256 | `c4b3748c30e2a9a8cf0a59f7ae1b49600c5e61a1af8e1922cc75b41fb1a12ad9` |

Phase-0 integrity notes:

* Exactly **one** Nintendo logo / GBA header in the image (logo at 0x04, base 0). No
  second game image, no multiboot stub, no appended trainer.
* No `SUNHORS` / `Mode7` / `CRC BANDIT` / `PARADOX` / `VENOM` strings; bytes at
  0x3FF000–0x3FFFFF are zero. First 4 KiB is the stock crt0. The image is the
  retail game with a rebuilt header (complement mismatch), not a cracktro build.
* Save file produced by mGBA on first boot: `Defender of the Crown.sav`, 512 bytes
  (`00 58 00 54 00 4F 00 44` then `FF` fill) — battery save, EEPROM-sized, **not**
  a password medium.

## 2. Executive summary

Defender of the Crown on GBA is the Cinemaware strategy game (credits screen reads
`DEFENDER OF THE CROWN / CINEMAWARE / EXECUTIVE PRODUCER LARS FUHRKEN-BATISTA /
PRODUCER ZAK McCLENDON / ORIGINAL MUSIC JIM CUOMO`). It has **no in-game password,
code, or player-enterable unlock system**; all four playable knights are available on
a fresh boot. Progress is battery-saved (512-byte EEPROM image), so the
Amiga/PC/C64 password culture of the original does not exist here.

The only "cheat-shaped" content in the ROM is two **developer screens that are dead
code**: a 12-entry test menu (`SWORDFIGHT`, `MACEFIGHT`, `MAIDEN SCREEN 1–4`,
`BATTLE TEST`, `CATAPULT GAME`, `TEST MAP`, `JOUST TEST`, `CHARACTER SELECT`,
`AERIAL MAP VIEW`) at 0x08009B64, and a five-parameter `HORSE DEBUG` tuning screen
(AI skill, bob range, bob speed, lance speed, mace-after-unseat/point) at
0x08012F94. Both were proven unreferenced by a whole-ROM scan of every branch form
(`bl`, `blx`, `b`, `bcc`, ARM `bl`) and every 32-bit pointer to their entry points,
and confirmed by live breakpoints that never fire while the control breakpoint
(pause menu) does.

What does exist and was fully enumerated is the *menu* space: title/attract, a
6-item main menu, a 4-knight selection screen (the "scenario select"), a 4-item
pause menu, and an enemy-skill option with three values. All are documented below
with addresses and RAM variables. Published GBA "codes" are CodeBreaker
memory-patch codes (addresses such as `0x03001150` for gold); they are external
memory edits, not in-game codes, and are out of scope — but their RAM addresses were
verified against the running game (gold = 13, home artillery = 10/0/0, campaign
artillery = 0/0/0, enemy skill = 1, music/sfx = 1/1).

The original-platform hold-key cheats (`hold K`, `hold H+J+K+L` on Amiga) have no
GBA equivalent: there is no keyboard, and every faithful analogue tested on the
controller during load (7 single buttons, and `L+R+A+B`, `Select+Start`,
`L+R+Select`, `L+R+Start`) left the campaign state byte-identical.

## 3. How to reproduce

Emulator: mGBA 0.10 (SDL), Xvfb `:286`, `SDL_AUDIODRIVER=dummy`, scale `-3`.

Default mGBA SDL keymap used: `x`=A, `z`=B, `a`=L, `s`=R, `Return`=Start,
`BackSpace`=Select, arrows = D-pad.

Evidence method (no screenshots): the game renders all UI text as a BG tile map at
`0x0600A800` using the ROM's own 77-glyph table at `0x0801C1A0`
(`ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-+!?:;,$$.'£=`).
Every menu capture below is the *decoded tile map* from an mGBA savestate,
i.e. the exact characters the game wrote, reproducible without images.

Reproduce a savestate read:

```python
# mGBA .ss1 is a PNG; the state is the zlib "gbAs" chunk.
# Layout for a 4 MiB ROM: 0x00000 header/CPU, 0x1000 VRAM, 0x19000 IWRAM, 0x21000 EWRAM.
```

Exact menu path:

1. Boot. A graphical attract/publisher screen runs for ~8 s (text layer blank,
   `0x0600A800` all zero), then the main menu appears automatically.
2. Main menu (6 entries): `BEGIN CAMPAIGN`, `CONTINUE CAMPAIGN` (skipped when no
   save), `ENEMY SKILL` (MEDIUM default), `MUSIC ON`, `SFX ON`, `CREDITS`.
   Up/Down move, A activates. `ENEMY SKILL` cycles MEDIUM → HARD → EASY → MEDIUM;
   `CREDITS` rolls the credits pages.
3. `BEGIN CAMPAIGN` → prologue story page (`In the year of our lord 1149…`) →
   A → home-territory text (`SHERWOOD FOREST / Here you visit your old friend`) →
   A → knight stat panel.
4. Knight panel: **Left/Right select one of four knights** (wrap-around), showing
   name and LEADERSHIP/JOUSTING/SWORDPLAY. A confirms.
5. Campaign summary: `GEOFFREY LONGSWORD / LEADERSHIP: AVERAGE / JOUSTING: AVERAGE /
   SWORDPLAY: STRONG / INCOME: 3 / TREASURE: 13 / SEPTEMBER 1149`.
6. Press **Start** on the campaign screen → pause menu (4 items: music toggle,
   SFX toggle, QUIT GAME with YES/NO confirm, RESUME GAME).

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`. RAM is little-endian.

| Address | Meaning |
|---|---|
| `0x080000C0` | stock crt0 (ARM) |
| `0x0800064C` | per-frame input update: `held = ~KEYINPUT & 0x3FF`; stores `pressed` and previous held |
| `0x04000130` | KEYINPUT (read at file 0x66C, 0x52E4, 0xDC18, 0x11C28 only) |
| `0x03001248` | `pressed` (edge, active-high, bit0=A … bit9=L) |
| `0x03001140` | previous frame's `held` |
| `0x08000C84` | text draw: `drawstr(str, col, row, palette)` → `0x0600A800` |
| `0x0801C1A0` | 77-byte glyph order table (A–Z, a–z, 0–9, `-+!?:;,$$.'£=`) |
| `0x0600A800` | BG text map (32×32), used by every menu |
| `0x08009D68` | main-menu draw |
| `0x08009E98` | main-menu handler/loop (6 items) |
| `0x0800A5C4` | knight-select loop (4 items) |
| `0x0800A66C` | knight panel draw (name + portrait + stats) |
| `0x08002FB4` | campaign loop: `bl 0x08004498` when `pressed & 8` (Start) |
| `0x08004498` | pause-menu handler (4 items) |
| `0x080046A8` | pause-item highlight draw |
| `0x08004420` | 2-item YES/NO confirm (used by QUIT) |
| `0x08004780` | "ARE YOU SURE?" confirm builder |
| `0x03000F7C` | current menu cursor / knight index (also debug-screen cursor) |
| `0x03000F90` | 18 × 12-byte territory records (owner, soldiers, knights, catapults, castle, spare) |
| `0x03001150` | gold (campaign TREASURE) |
| `0x03001152` | income per month |
| `0x03001154/56/58` | campaign soldiers / knights / catapults |
| `0x03000FB6/B8/BA` | home-territory soldiers / knights / catapults |
| `0x0300385C` | enemy skill (0=EASY, 1=MEDIUM, 2=HARD) |
| `0x030011D4` | music enable flag (1/0) |
| `0x03003448` | SFX enable flag (1/0) |
| `0x03004EBC/4E9C/4F08` | siege payload counts (boulders / Greek fire / disease) |
| `0x03004F54/4F74/4F68/4F30/4F3C` | HORSE DEBUG parameters (AI skill, bob range, bob speed, lance speed, mace toggle) |
| `0x08009B64` | **dead** 12-entry test-menu draw/loop |
| `0x08009D2C` | test-menu 12-pointer label table |
| `0x08012F94` | **dead** HORSE DEBUG screen |
| `0x08013138` | HORSE DEBUG value draw helper |

Validation of the RAM labels comes from the published CodeBreaker list and from
live reads: gold at `0x03001150` = 13 matches `TREASURE: 13`; `0x03001152` = 3
matches `INCOME: 3`; `0x03000FB6/B8/BA` = 10/0/0 matches the home record; enemy
skill `0x0300385C` = 1 matches `MEDIUM`; music/SFX flags = 1/1 matches `MUSIC ON`
/ `SFX ON`.

## 5. Algorithm

### 5.1 Input model (the only "validator" in the game)

```
every frame:
    held    = (~*(u16*)0x04000130) & 0x03FF
    pressed = held & ~prev_held
    *(u16*)0x03001248 = pressed
    *(u16*)0x03001140 = held
    prev_held = held
```

Every menu compares `pressed` (edge-triggered) against a **single** button mask.
There is no history buffer, no sequence counter, and no multi-press comparison
anywhere in the image (see §6b).

Mask values: A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010,
Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.

### 5.2 Text renderer

```
drawstr(p, col=u16, row=u16, pal=u16):
    base = 0x0600A800 + row*64 + col*2
    for c in *p:
        if c == '#': return
        if c == '@': col-- ; base -= 2 ; continue
        if c == '~': row++ ; base += 64 ; continue
        if c == ' ': col++ ; base += 2 ; continue      # leaves the fill tile 0xC2
        tile = index_of(c in glyph_table[0x0801C1A0])   # 0..75, 76 if not found
        *(u16*)base = tile | (pal << 12)
        col++ ; base += 2
```

Screens are plain functions; there is no generic "scene table". The pause screen
is reached by a direct `bl` from the campaign loop, e.g. `0x08002FB4:
bl 0x08004498` guarded by `pressed & 0x008`.

### 5.3 Main menu (`0x08009E98`)

```
sel = *(u8*)0x03000F7C          # 0..5
if pressed & 0x080: sel = (sel+1)%6 ; skip item 1 if no save
if pressed & 0x040: sel = (sel-1+6)%6 ; skip item 1 if no save
if pressed & 0x001:
    case 0: fade; play(0); intro(); knight_select(); campaign_init()
    case 1: campaign_init(); continue_campaign()        # only with save
    case 2: *(u8*)0x0300385C = (v+1)%3                  # EASY/MEDIUM/HARD
    case 3: *(u8*)0x030011D4 ^= 1                       # MUSIC
    case 4: *(u8*)0x03003448 ^= 1                       # SFX
    case 5: credits(0); redraw()
```

`CONTINUE` is skipped unless `*(u8*)0x0300123C != 0` and
`*(u16*)0x030039B0 == 1` (0x0800A000–0x0800A016). Observed: with no save one Down
moves the cursor 0 → 2.

### 5.4 Knight select (`0x0800A5C4`, draw `0x0800A66C`)

```
sel = *(u8*)0x03000F7C          # 0..3
if pressed & 0x020: sel = (sel==0) ? 3 : sel-1 ; redraw
if pressed & 0x010: sel = (sel==3) ? 0 : sel+1 ; redraw
if pressed & 0x001: accept
```

Knight table (observed: name and stats rendered for each index):

| sel | Name | LEADERSHIP | JOUSTING | SWORDPLAY | portrait |
|---|---|---|---|---|---|
| 0 | `CEDRIC OF ROTHERWOOD` | STRONG | GOOD | WEAK | 0x080797A8 |
| 1 | `GEOFFREY LONGSWORD` | AVERAGE | AVERAGE | STRONG | 0x08077D88 |
| 2 | `WOLFRIC THE WILD` | AVERAGE | STRONG | AVERAGE | 0x08074948 |
| 3 | `WILFRED OF IVANHOE` | GOOD | GOOD | AVERAGE | 0x08076368 |

Default on a fresh start is index 1 (Geoffrey). A separate 9-pointer knight-name table
at `0x0801CB00` (used by the campaign UI at `0x0800C020`) holds, in index order:
`CEDRIC OF ROTHERWOOD`, `GEOFFREY LONGSWORD`, `WOLFRIC THE WILD`,
`WILFRED OF IVANHOE`, `BRIAN DE BOIS-GILBERT`, `PHILIP MALVOSIN`,
`REGINALD FRONT DE BOEUF`, `EDMUND THE GRIMM`, `ROGER FALCONBRIDGE` (strings
0x0801CB24–0x0801CBD0). Which of those are used as rival owners is **inferred**:
the 18 territory records observed in RAM used owner indices 0–5, and the text bank
also carries four `MAIDEN SCREEN 1–4` names (`ANNE OF LANCASHIRE`, `REBECCA OF YORK`,
`KATHARINE OF NOTTINGHAM`, `ROSALIND OF BEDFORD`, pointers at 0x0801CBF4).

### 5.5 Pause menu (`0x08004498`)

```
if pressed & 0x008 (Start, from 0x08002FB4):
    r5 = 0
    loop:
        if pressed & 0x080: r5 = (r5+1)&3 ; redraw
        if pressed & 0x040: r5 = (r5-1)&3 ; redraw
        if pressed & 0x001:
            case 0: *(u8*)0x030011D4 ^= 1 ; if 0 -> audio stop(3)
            case 1: *(u8*)0x03003448 ^= 1
            case 2: if confirm_yes_no(): exit_to_menu()      # 0x08004780/0x08004420
            case 3: return 0                                  # RESUME
        if pressed & 0x002 or 0x008: return 0
```

RAM-verified: pressing Start then A changed `0x030011D4` 1→0; Down+A changed
`0x03003448` 1→0; Down+A on item 2 entered the YES/NO confirm (B cancelled);
Down+A on item 3 resumed the campaign.

## 6. Tables

### 6.1 Main menu (6 entries, rows 3–16 of 0x0600A800)

| # | Label | Effect |
|---|---|---|
| 0 | `BEGIN CAMPAIGN` | new campaign (intro → knight → world setup) |
| 1 | `CONTINUE CAMPAIGN` | skipped without save data |
| 2 | `ENEMY SKILL` + `EASY/MEDIUM/HARD` | cycles `0x0300385C` 0..2 |
| 3 | `MUSIC ON/OFF` | `0x030011D4` |
| 4 | `SFX ON/OFF` | `0x03003448` |
| 5 | `CREDITS` | `0x0800B9DC`; observed pages `CINEMAWARE`, `EXECUTIVE PRODUCER LARS FUHRKEN-BATISTA`, `PRODUCER ZAK McCLENDON`, `ORIGINAL MUSIC JIM CUOMO` |

### 6.2 Territory record (`0x03000F90`, 18 × 12 bytes)

| Offset | Width | Meaning (observed/derived) |
|---|---|---|
| +0 | u16 | owner knight index 0..5, `0x00FF` = neutral |
| +2 | u16 | soldiers |
| +4 | u16 | knights |
| +6 | u16 | catapults |
| +8 | u16 | castle present (1) |
| +10 | u16 | spare/flag (0) |

Start values observed: 6 owned territories (owners 2,1,0,3,4,5 in a fresh game),
each `soldiers=10, knights=0, catapults=0, castle=1`, the other 12 neutral
(`owner=0x00FF`). Gold 13, income 3, campaign army 0/0/0.

### 6.3 Debug screen 1 — test menu (`0x08009B64`, table `0x08009D2C`)

12 pointers; labels drawn at rows 4–15, column 5; a `-` cursor (string `-#` at
`0x0801E21C`) is drawn at column 4 of the selected row. There is no action table
and no caller.

| # | Label | String address |
|---|---|---|
| 0 | `SWORDFIGHT` | 0x0801E154 |
| 1 | `MACEFIGHT` | 0x0801E160 |
| 2 | `MAIDEN SCREEN 1` | 0x0801E16C |
| 3 | `MAIDEN SCREEN 2` | 0x0801E180 |
| 4 | `MAIDEN SCREEN 3` | 0x0801E194 |
| 5 | `MAIDEN SCREEN 4` | 0x0801E1A8 |
| 6 | `BATTLE TEST` | 0x0801E1BC |
| 7 | `CATAPULT GAME` | 0x0801E1CC |
| 8 | `TEST MAP` | 0x0801E1DC |
| 9 | `JOUST TEST` | 0x0801E1E8 |
| 10 | `CHARACTER SELECT` | 0x0801E1F4 |
| 11 | `AERIAL MAP VIEW` | 0x0801E208 |

### 6.4 Debug screen 2 — HORSE DEBUG (`0x08012F94`, draw `0x08013138`)

Cursor `0x03000F7C` 0..4; rows 1,5,6,8,9,10 on the same text layer.

| sel | Row text | Variable | Control |
|---|---|---|---|
| 0 | `AI PLAYER SKILL: %s` | `0x03004F54` | Left/Right clamp 0..3; 0=STRONG,1=GOOD,2=AVERAGE,3=WEAK |
| 1 | `BOB RANGE %u PIXELS` | `0x03004F74` | Left/Right ±1, clamps at 0 |
| 2 | `BOB SPEED: %u` | `0x03004F68` | Left/Right ±1, clamps at 0 |
| 3 | `LANCE SPEED: %u` | `0x03004F30` | Left/Right ±1, clamps at 0 |
| 4 | `MACE AFTER UNSEATING` / `MACE AFTER POINT DRAW` | `0x03004F3C` | Left/Right toggles 0/1 |
| — | A exits (returns the cursor value) | | |

String block: `0x08291414`–`0x082914A0`; AI-skill string table at `0x0808F62C`
(`STRONG`, `GOOD`, `AVERAGE`, `WEAK`).

### 6.5 Button masks observed per screen

| Screen | Masks actually read |
|---|---|
| main menu | A(1), Up(0x40), Down(0x80) |
| knight select | A(1), Right(0x10), Left(0x20) |
| pause menu | A(1), B(2), Start(8), Up(0x40), Down(0x80) |
| HORSE DEBUG (dead) | A(1), Right(0x10), Left(0x20), Up(0x40), Down(0x80) |

## 6b. Enumeration

**Space definition.** There is no password/checksum field. The entry UI spaces
are absent, not merely unreachable:

* `PASSWORD` = 0 occurrences, `CHEAT` = 0, `UNLOCK` = 0, `SCENARIO` = 0, `CODE` = 0,
  `OPTION` = 0, `HIDDEN` = 0, `BONUS` = 0 (case-insensitive, whole 4 MiB).
* `DEBUG` = 1 (`HORSE DEBUG`), `TEST` = 3 (`BATTLE TEST`, `TEST MAP`, `JOUST TEST`),
  `SECRET` = 2 (story prose: "conceals any secrets", "men into secret passages").
* No name-entry alphabet string exists; the only 77-entry character table is the
  renderer's glyph order at `0x0801C1A0`. No 36-symbol `A–Z0–9` entry table.
* The UI string bank `0x1C000–0x1E900` contains 191 `#`-terminated strings; none is
  a code list, password list or keypad legend.
* Save medium: 512-byte battery file; "CONTINUE" is gated on save bytes, not on a
  typed code.

**Button space.** 10 buttons, edge-triggered, per-screen accept set as in §6.5.
To look for undocumented sequences the whole image was scanned for runs of key
masks: 119 runs of ≥3 active-high masks and 1 run of ≥3 active-low masks. Every
run lies inside data (graphics/pointer tables), none inside an input handler; there
is no array of expected presses, no progress index, and no code that compares the
`pressed` word with a concatenated/multi-press constant. The button space is
therefore exactly the sum of the single-press sets above: 3 (main menu) + 3
(knight select) + 5 (pause) = 11 accepted button edges across the three reachable
screens, plus 5 in the unreachable debug screen. The space is complete.

**Debug-screen space.** 12 test-menu entries and 5 HORSE DEBUG parameters = 17
enumerated debug affordances, all unreachable:

* `bl`/`blx`/`b`/`bcc` scan over every 2-byte offset: **0** references to
  `0x08009B64` and **0** to `0x08012F94`.
* ARM `bl` scan over every 4-byte offset: **0** references.
* 32-bit pointer scan (`addr` and `addr|1`): **0** occurrences in the 4 MiB.
* Thumb ADR (`add rX,pc,#imm`) scan: **0**.
* Live breakpoints on both entries installed at reset, with a control breakpoint on
  the pause entry `0x08004498`: pressing Start hit the control; no amount of menu
  input (all 10 buttons, repeated) hit either debug entry.
* Context: their sibling functions *are* referenced and reachable — the main-menu
  draw `0x08009D68` is called at `0x08009EA6`/`0x08009FD8`, and the pause entry has
  a single caller at `0x08002FB4`. The two debug screens have none.

This is "dead code" in the §16.3 sense: the strings and handlers exist, but no
table entry, branch or pointer reaches them.

**Published codes.** GBA lists (3rd party cheat indexes) contain only
CodeBreaker memory patches, e.g. master `00000E4F 000A / 1000064C 0007`,
`83001150 270F` (gold), `83000FB6/8/BA 03E7` (home artillery),
`83001154/6/8 03E7` (campaign artillery), `33004EBC/4E9C/4F08 0009` (siege
payloads), `73001ACA 000E / 33001AC4 000F` (combat). These are out of scope per
the brief (memory edits, not in-game codes). Their addresses were verified live:
gold `0x03001150`=13, `0x03000FB6/B8/BA`=10/0/0, `0x03001154/6/8`=0/0/0,
enemy skill `0x0300385C`=1, music/SFX `0x030011D4`/`0x03003448`=1/1.

**Original-platform cheats.** The Amiga release documents "hold `K` while loading"
(2048 knights) and "hold `H+J+K+L`". The GBA has no keyboard and the ROM contains no
2048/1024 constant in the campaign initialiser (`0x080029EC`) and no held-key test
at boot. Tested in-game, holding a button during load and playing normally into the
campaign summary:

| Held during load | gold | home soldiers/knights/catapults |
|---|---|---|
| none (control) | 13 | 10 / 0 / 0 |
| Select | 12–13 | 10 / 0 / 0 |
| A | 12 | 10 / 0 / 0 |
| B | 12 | 10 / 0 / 0 |
| L | 12 | 10 / 0 / 0 |
| R | 12 | 10 / 0 / 0 |
| Start | 12 | 10 / 0 / 0 |
| L+R+A+B | 12 | 10 / 0 / 0 |
| Select+Start | 12 | 10 / 0 / 0 |
| L+R+Select | 12 | 10 / 0 / 0 |
| L+R+Start | 12 | 10 / 0 / 0 |

(The 12/13 difference is the *random home territory/knight*, not a cheat: repeats
of the same timing produce identical 12/10/0/0 states; no run produced 1024/2048
knights or any other army change.)

**Novel artefact.** Because there is no accepted-code space, no novel code exists to
mint. The unpublished result delivered here is the complete enumeration and
reachability proof of the two developer screens (17 entries/parameters), which does
not appear on 3rd party cheat indexes or any wiki for this SKU.

## 7. Validation evidence

**Observed (emulator state / RAM reads)**

* Main menu text decoded from `0x0600A800`: six entries, exactly as listed.
* `ENEMY SKILL` cycles MEDIUM→HARD→EASY (three presses) with `0x0300385C` = 1,2,0.
* Knight select: Left/Right produced `CEDRIC OF ROTHERWOOD` (0),
  `GEOFFREY LONGSWORD` (1), `WOLFRIC THE WILD` (2), `WILFRED OF IVANHOE` (3), each
  with a distinct stat block; A confirmed.
* Campaign summary decoded: `INCOME: 3`, `TREASURE: 13`; RAM
  `0x03001150`=13, `0x03001152`=3.
* Pause menu: Start from the campaign loop hit `0x08004498`; A toggled
  `0x030011D4` 1→0; Down+A toggled `0x03003448` 1→0; the QUIT item showed the
  YES/NO confirm and B cancelled; the last item resumed.
* Credits text decoded over time: `DEFENDER OF THE CROWN`, `CINEMAWARE`,
  `EXECUTIVE PRODUCER / LARS FUHRKEN-BATISTA`, `PRODUCER / ZAK McCLENDON`,
  `ORIGINAL MUSIC / JIM CUOMO`, `PUBLISHED BY`.
* Breakpoint control test: with breakpoints on `0x08009B64`, `0x08012F94` and
  `0x08004498`, pressing Start reported `Hit breakpoint 3 at 0x08004498`; breakpoints
  1 and 2 never fired.

**Derived (instruction sequence)**

* Input model, menu masks, item counts, wrap/skip rules, toggle flags and the
  territory record layout are read directly from the disassembly listed in §4.
* The two debug screens have no reference; see the scan counts in §6b.
* Save gating of `CONTINUE CAMPAIGN` is the `0x0300123C` / `0x030039B0` test at
  `0x0800A000`.

**Inferred (lower confidence)**

* The `.sav` is EEPROM-sized (512 B) and the "CONTINUE" gate implies battery save,
  but the exact save record layout was not reversed (not needed for the cheat
  question).
* HORSE DEBUG parameter defaults (what the joust setup writes before the screen is
  opened) were not exercised, because no input reaches the screen.

## 8. Unknowns

* Exact save-record layout and when the game commits a campaign to EEPROM.
* Whether the 12-entry test menu ever had a handler in an earlier build (the
  current image has only the draw/loop stub).
* The intended default values of the five HORSE DEBUG parameters.
* Meaning of the two spare bytes in the 12-byte territory record.

None of these can hide a player-entered code: the text, alphabet, sequence and
pointer spaces above are closed.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for all disassembly.
* Python 3 + Capstone 5.0.7 for literal-pool (`ldr rX,[pc,#imm]`), branch
  (`bl`/`blx`/`b`/`bcc`/ARM `bl`), ADR and pointer scans.
* mGBA 0.10 SDL under Xvfb `:286`; `.ss1` states are PNGs whose `gbAs` chunk is
  `zlib`-compressed (397,312 bytes; VRAM 0x1000, IWRAM 0x19000, EWRAM 0x21000).
* `xdotool` XTEST key injection (45–80 ms holds; 150 ms double-steps menus).
* Custom scripts (in `/tmp/defendercrown`): `phase0.py`, `state.py`,
  `screen.py` (tile-map text decoder), `nav.py`, `dbg2.py` (mGBA CLI debugger over
  a pty), `holdtest.py`.

## 10. Legal note

No ROM, graphics, music or extracted text assets are redistributed. Only hashes,
addresses, algorithms and the report author's own decoded menu labels are published.
