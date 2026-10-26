# A Sound of Thunder (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/A Sound of Thunder/A Sound of Thunder.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title (`0xA0`) | `ASOT` |
| Game code (`0xAC`) | `A3QE` |
| Maker code (`0xB0`) | `6L` |
| Software version (`0xBC`) | 0 |
| Complement (`0xBD`) | `0x8E` (matches `-(sum 0xA0..0xBC + 0x19) mod 256`) |
| Header checksum (`0xBE`) | `0x0000` |
| Entry branch (`0x00`) | `0xEA00002E` → ARM at `0x080000C0` |
| MD5 | `26b44c6f29e95b1aae1b79f37725d959` |
| SHA-1 | `6eeb95555c432e2a28e29438711f2fdee4d9cf7f` |
| SHA-256 | `bcfcf623a1addb0fbf251aeeab4f47275388f166a325c23c88b2741f01e070f3` |

Header scan for the 156-byte Nintendo logo found **two** headers in the file:

* `0x000000` — the cartridge header above (`ASOT` / `A3QE`).
* `0x0809E8` — an embedded multiboot header: same logo, entry `0xEA00002E`,
  title `SOUNDOFTHNDR`, game code `ASOT`, maker `??`.

The second header is a single-pak/link-cable multiboot copy, **not** a second
game. Addresses in this report always refer to the first image
(`ROM address = file offset + 0x08000000`).

Published metadata: developed by Rockstar Leeds (Möbius Entertainment),
published by BAM! Entertainment, GBA release Feb 2005.

## 2. Executive summary

The Password screen is a plain lookup, not a checksum or generator. There are
exactly **eleven** hard-coded 6-character codes, stored as 8-byte NUL-padded
strings at file `0x64970` and paired with an apply function in an
`{ char *code; void (*apply)(); }` record table at file `0x649C8`.

The screen appends one letter per A press into a 6-byte space-padded buffer at
`0x03007630`. When the sixth letter lands, the handler at `0x0801C912` calls the
validator wrapper at `0x08027F00`, which calls `0x08019680`. That function walks
the record table and compares six bytes (`buf[0..5]` against `code[0..5]`,
`strcmp`-like but fixed length). On a match it calls the record's apply function
through the `bx r3` helper at `0x080298F0` and returns 1; otherwise it returns 0.

Ten of the codes are level passwords: record *i* (0-based) calls
`0x0801957C(i+1)`, which writes `i+1` to `0x03001B30` and sets
`0x03001B34[0..i] = 1`. That 11-word array is copied into each level widget's
`+0x6C` field, and the menu only activates a widget when that field equals 1
(`0x0801C324`). So a level-*N* password unlocks levels 2..N. The eleventh code,
`DCRDTS`, does not touch the level array: it sets `0x03006B18 = 1` and
`0x03006B14 = 11`, which starts the ending.

Confirmed in mGBA with controller input only:

* `BHRTYP` → "Password accepted", `0x03001B34[0..1] = 1`, and level 2 then
  starts from Level Select (indoor level, HUD `075` / `100`).
* `DCRDTS` → the password screen is replaced by a cutscene and then the credits
  ("A SOUND OF THUNDER / CREDITS").
* Control run without a password: Level Select → Right → A on level 2 does
  nothing, i.e. the same input is rejected while the array entry is 0.

All eleven codes match the published GameFAQs list exactly, and the on-screen
alphabet (21 consonants, three rows of seven) contains exactly the characters
the codes use.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL frontend, `-3` scale, 720×480 window.

```bash
Xvfb :104 -screen 0 1024x768x24 &      # any free display works
DISPLAY=:104 openbox &
DISPLAY=:104 SDL_AUDIODRIVER=dummy mgba -3 "A Sound of Thunder.gba" &
```

When driving the game with `xdotool`, hold each key ~60–100 ms and leave
~300 ms between presses. The game polls input per frame; this timing is what
the shipped script uses.

Default mGBA SDL keymap used here:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Menu path (English):

1. Language select → **English** (`A`).
2. Title menu: `Single Player` / `Link-up` / **`Password`** / `Options`.
   Press `Down` twice, then `A`.
3. The password screen shows a 3×7 letter grid, an `A +` icon, a `B -` icon and
   a `Main Menu` entry. There is no separate text field: typed letters are drawn
   over the background, and the selected cell is a faint grey box. This makes a
   screenshot after every few keystrokes the easiest way to stay oriented.

Controls on the password screen:

* D-pad moves the highlight: `Left`/`Right` inside a row (clamped at the row
  ends), `Up`/`Down` between rows (row 0..2, column preserved).
* `A` appends the highlighted letter to the 6-character buffer.
* `B` deletes the last letter.
* There is no confirm key: the sixth letter triggers validation automatically.
* On a fresh visit the highlight is on `B` (row 0, column 0). After a rejected
  attempt the highlight returns to `N` (row 1, column 3) and the buffer is
  cleared to six spaces.

Grid as proven dynamically by pressing A in every cell and reading the
stored byte:

```
B C D F G H J
K L M N P Q R
S T V W X Y Z
```

Note for reproduction: the font's `V` has a rounded bottom and reads like a
`U` in screenshots. The grid contains **no U** and no digits; it is the 21
English consonants.

Codes exercised in this session:

| Code | Result |
|---|---|
| `BHRTYP` | accepted, level 2 unlocked and started |
| `DCRDTS` | accepted, ending/credits started |
| `BHRTZP` (typo made during probing) | rejected, "Invalid password" |
| `LSKGHG` … `LKDSVB` | present in ROM; not individually typed |

To enter a code by hand, walk the grid and press A; e.g. `BHRTYP`:

```
B  start cell, A
H  Right×5, A
R  Down, Right, A
T  Down, Left×5, A
Y  Right×5, A
P  Up, Left×2, A      -> "Password accepted"
```

The state can be watched while the emulator is paused in the GDB stub:

```
x/6cb 0x03007630    # input buffer
x/1cb 0x03003D08    # cursor row
x/1cb 0x03003D04    # cursor column
x/1wx 0x03001B30    # last applied record index
x/11wx 0x03001B34   # level unlock array
```

## 4. Address map

Code addresses are Thumb. Data addresses are ROM or IWRAM literals.
`file = ROM - 0x08000000`.

| ROM address | File | Purpose |
|---|---|---|
| `0x08019680` | `0x19680` | **Validator**: fixed 6-byte compare against the record table |
| `0x08027F00` | `0x27F00` | Wrapper: `r0 = 0x03007630; bl 0x08019680; return` |
| `0x080298F0` | `0x298F0` | `bx r3` helper, used to call the apply pointer |
| `0x08064970` | `0x64970` | Code table, 11 × 8 bytes (`BHRTYP\0\0` … `DCRDTS\0\0`) |
| `0x080649C8` | `0x649C8` | Record table, 11 × `{u32 code_ptr; u32 apply_ptr}` + `{0,0}` terminator at `0x08064A20` |
| `0x0801C8E8` | `0x1C8E8` | Append path: load selected glyph byte, `strb` into buffer at slot |
| `0x0801C900` | `0x1C900` | `strb r2,[0x03007630 + slot]` |
| `0x0801C912` | `0x1C912` | `bl 0x08027F00` when slot reaches 6 |
| `0x0801C916` | `0x1C916` | Branch on validator result (1 = accepted) |
| `0x0801C91A` | `0x1C91A` | Accepted path: slot=0, text id `0xFF`, timer=100, `0x03006BDC=1` |
| `0x0801C940` | `0x1C940` | Rejected path: slot=0, clear buffer, text id `0xFE`, timer=100 |
| `0x0801C9DC` | `0x1C9DC` | B (bit 1 of `0x04000130`) path: `slot--`, write space |
| `0x0801D278` | `0x1D278` | Clear buffer: six `0x20` bytes at `0x03007630` |
| `0x0801957C` | `0x1957C` | Apply helper: `0x03001B30 = n`, `0x03001B34[0..n-1] = 1` |
| `0x080195A4` | `0x195A4` | Reset helper: clear 11 words, then same set-up-to-n |
| `0x080195DC`…`0x08019648` | | Ten level applies, each `movs r0,#1..10; bl 0x0801957C` |
| `0x08019654` | `0x19654` | Ending apply: `*(u8*)0x03006B18 = 1; *(u32*)0x03006B14 = 11` |
| `0x0801C324` | `0x1C324` | Menu activation: `ldr r3,[widget,#0x6C]; cmp r3,#1; beq handler` |
| `0x0801C444` / `0x0801C45E` | `0x1C444` | Copy `0x03001B34[widget->+0x68]` into `widget->+0x6C` |

RAM (IWRAM):

| Address | Purpose |
|---|---|
| `0x03007630` | 6-byte password buffer, space padded |
| `0x03003D04` | Cursor column (0..6) |
| `0x03003D08` | Cursor row (0..2) |
| `0x03001B10` | Pointer to the UI/widget state struct |
| `0x03001B30` | Last applied record index (1..10; 0 if none) |
| `0x03001B34` | 11-word level unlock array; index 0 = level 1 |
| `0x03006BDC` | "Accepted" latch set on a successful code |
| `0x03006B14` | Screen/mode number (`0x0A` at the password screen, 2 after starting level 2, 3 during credits) |
| `0x03006B18` | Ending request flag written by `DCRDTS` |

Text bank (plain ASCII, file offsets): `SINGLE` `0x6BB30`, `LINK-UP` `0x6BB38`,
`PASSWORD` `0x6BB40`, `OPTIONS` `0x6BB4C`, `Press  B  to  accept` `0x6BB54`,
`PW` `0x6BB6C`, `Invalid password` `0x6BB70`, `Password accepted` `0x6BB84`,
`Select Level` `0x6BD4C`, `Choosing Level. . .` `0x6BD8C`.

## 5. Algorithm

```
enter_screen:
    for i in 0..5: buf[i] = 0x20          # 0x0801D278
    slot = 0

on_dpad(dir):                              # widget cursor
    move (row, col) in 3x7 grid, clamped
    row -> 0x03003D08, col -> 0x03003D04

on_A:                                      # 0x0801C8E8
    if slot > 5: return
    buf[slot] = glyph_of_highlighted_cell  # ASCII letter
    slot += 1
    if slot != 6: return
    if validate(buf):                      # 0x0801C912 -> 0x08027F00
        slot = 0
        show("Password accepted")           # text id 0xFF
        *(u8*)0x03006BDC = 1
    else:
        slot = 0
        clear buf to spaces
        show("Invalid password")            # text id 0xFE

on_B:                                      # 0x0801C9DC
    if slot == 0: return
    slot -= 1
    buf[slot] = 0x20

validate(buf):                             # 0x08019680
    for rec in table:                      # table terminated by null code ptr
        if buf[0] != rec.code[0]: continue
        for i in 1..5:
            if buf[i] != rec.code[i]: goto next_record
        rec.apply()                        # via 0x080298F0 (bx r3)
        return 1
    return 0

apply_level(n):                            # n = 1..10
    *(u32*)0x03001B30 = n
    for i in 0..n-1:
        ((u32*)0x03001B34)[i] = 1          # sticky: unlocks 1..n

apply_ending():                            # DCRDTS
    *(u8*)0x03006B18 = 1
    *(u32*)0x03006B14 = 11

menu_enable(widget):                       # 0x0801C324
    widget->enabled = ((u32*)0x03001B34)[widget->level_index]   # -> widget+0x6C
    activate only if widget->enabled == 1
```

Because `apply_level` only ever writes 1 (never 0), entering a higher code also
unlocks every lower level; there is no way to lock a level from this screen.

The validator compares exactly six bytes. It does not check a length or a
terminator, but the UI caps input at six, so only the eleven table strings can
match. Reverse-engineering the exact C:

```c
int validate(const unsigned char *buf) {
    const struct rec { const char *code; void (*apply)(void); } *r = TABLE;
    while (r->code) {
        if (buf[0] == r->code[0]) {
            int i = 1;
            while (i <= 5 && buf[i] == r->code[i]) i++;
            if (i == 6) { r->apply(); return 1; }
        }
        r++;
    }
    return 0;
}
```

Core of the real function (`arm-none-eabi-objdump -M force-thumb`):

```
08019680  b5f0        push  {r4,r5,r6,r7,lr}
08019682  1c06        adds  r6,r0                ; r6 = buf
08019684  4d12        ldr   r5,[pc,#72]          ; r5 = 0x080649C8
08019686  7833        ldrb  r3,[r6,#0]           ; buf[0]
08019688  2000        movs  r0,#0                ; record index * 8
0801968a  469c        mov   ip,r3
0801968c  1d2f        adds  r7,r5,#4             ; &apply
0801968e  5943        ldr   r3,[r0,r5]           ; r3 = rec->code
08019690  781b        ldrb  r3,[r3,#0]           ; code[0]
08019692  2401        movs  r4,#1
08019694  2100        movs  r1,#0
08019696  459c        cmp   ip,r3
08019698  d010        beq   0x80196bc
0801969a  2400        movs  r4,#0
0801969c  2c00        cmp   r4,#0
0801969e  d108        bne   0x80196b2            ; matched -> dispatch
080196a0  3008        adds  r0,#8
080196a2  5943        ldr   r3,[r0,r5]           ; next rec->code
080196a4  3708        adds  r7,#8
080196a6  2b00        cmp   r3,#0               ; terminator
080196a8  d1f1        bne   0x801968e
080196aa  2000        movs  r0,#0                ; return 0
...
080196b2  683b        ldr   r3,[r7,#0]           ; rec->apply
080196b4  f010 f91c   bl    0x80298F0            ; bx r3
080196b8  2001        movs  r0,#1                ; return 1
080196bc  3101        adds  r1,#1
080196be  2905        cmp   r1,#5
080196c0  dcec        bgt   0x801969c           ; compared 6 bytes
080196c2  5943        ldr   r3,[r0,r5]
080196c4  5c72        ldrb  r2,[r6,r1]
080196c6  5c5b        ldrb  r3,[r3,r1]
080196c8  429a        cmp   r2,r3
080196ca  d0f7        beq   0x80196bc
080196cc  e7e5        b     0x801969a
```

Note: the ROM also contains the string `Press  B  to  accept` at `0x6BB54`, but
that belongs to a different dialog. On the Password screen, B is the delete key
(`0x0801C9DC` tests bit 1 of `0x04000130` and backs the buffer slot up); the
observed behaviour matches the disassembly.

## 6. Tables

Code table, file `0x64970`, 8 bytes per entry (6 chars + two NULs), record
table at `0x649C8`, and the effect of each `apply`:

| # | Code | `apply` | Effect | Published meaning |
|---:|---|---|---|---|
| 0 | `BHRTYP` | `0x080195DD` → `0x0801957C(1)` | `arr[0..0]=1` | Level 2 |
| 1 | `LSKGHG` | `0x080195E9` → `(2)` | `arr[0..1]=1` | Level 3 |
| 2 | `LZDBVZ` | `0x080195F5` → `(3)` | `arr[0..2]=1` | Level 4 |
| 3 | `LBKVRG` | `0x08019601` → `(4)` | `arr[0..3]=1` | Level 5 |
| 4 | `VWLFLG` | `0x0801960D` → `(5)` | `arr[0..4]=1` | Level 6 |
| 5 | `LZVKBD` | `0x08019619` → `(6)` | `arr[0..5]=1` | Level 7 |
| 6 | `KBDBVL` | `0x08019625` → `(7)` | `arr[0..6]=1` | Level 8 |
| 7 | `LVBRLG` | `0x08019631` → `(8)` | `arr[0..7]=1` | Level 9 |
| 8 | `KJBLVB` | `0x0801963D` → `(9)` | `arr[0..8]=1` | Level 10 |
| 9 | `LKDSVB` | `0x08019649` → `(10)` | `arr[0..9]=1` | Level 11 |
| 10 | `DCRDTS` | `0x08019655` (special) | `0x03006B18=1`, `0x03006B14=11` | Ending |

Alphabet (glyph grid, 3 rows × 7 columns):

```
row 0: B C D F G H J
row 1: K L M N P Q R
row 2: S T V W X Y Z
```

All eleven codes use only these 21 letters. There is no digit, punctuation or
wildcard symbol, so the entry screen cannot express anything outside this
alphabet.

Public list for comparison (GameFAQs, Wayback capture 2018-11-26,
`web.archive.org/web/20181126021449/https://gamefaqs.gamespot.com/gba/561536-a-sound-of-thunder/cheats`):

```
Ending DCRDTS   Level 2 BHRTYP   Level 3 LSKGHG   Level 4 LZDBVZ
Level 5 LBKVRG  Level 6 VWLFLG   Level 7 LZVKBD   Level 8 KBDBVL
Level 9 LVBRLG  Level 10 KJBLVB  Level 11 LKDSVB
```

Every published string is byte-identical to the ROM table; no published code is
missing and no ROM code is unpublished.

## 7. Validation evidence

**Observed (emulator).**

* Boot → language select → title menu → `Password` screen. Screenshots:
  `screenshots/01_language_select.png`, `02_title_menu.png`,
  `03_menu_password_highlighted.png`, `04_password_grid.png`.
* Typing `BHRTYP` with the controller, reading the buffer while paused after
  each letter: `B`, `BH`, `BHR`, `BHRT`, `BHRTY`, `BHRTYP`. Screenshot
  `screenshots/05_password_accepted_BHRTYP.png` shows `BHRTYP` and
  "Password accepted".
* Immediately after the sixth letter: `0x03001B30 = 1`, `0x03001B34 =
  {1,1,0,0,0,0,0,0,0,0,0}`. These are exactly the writes of
  `apply_level(1)`; before the code the array was `{1,0,...}` (level 1 only).
* `Single Player → Level Select`: pressing `Right` then `A` starts level 2 —
  an indoor tiled level with HUD ammo `075` and health `100`
  (`screenshots/06_level_select.png`, `07_level2_start.png`,
  `08_level2_gameplay.png`).
* Control run, same ROM, no password: fresh boot → `Single Player` →
  `Level Select` → `Right` → `A` leaves the screen unchanged
  (`screenshots/09_baseline_level2_locked.png`). The identical input that
  starts level 2 after `BHRTYP` does nothing while `0x03001B34[1] == 0`.
* Typing `DCRDTS` leaves the password screen immediately; after ~6 s an
  in-engine forest cutscene plays and after ~14 s the credits screen
  "A SOUND OF THUNDER / CREDITS" appears
  (`screenshots/10_credits_DCRDTS.png`). The level array stayed `{1,0,...}` —
  the ending code does not unlock levels.
* A typo (`BHRTZP`, produced while probing the grid) produced
  "Invalid password"; this is the observed negative case.
* Grid map: pressing A in each cell and reading the stored byte produced
  `BCDFGHJ / KLMNPQR / STVWXYZ`; column 7 is unreachable (clamped at 6).

**Derived (disassembly).**

* `0x08019680` is a six-byte table comparison over the record table at
  `0x080649C8`, dispatching the paired function via `bx r3` (`0x080298F0`).
* `0x0801957C` writes the index to `0x03001B30` and 1 to `0x03001B34[0..n-1]`.
* The ten level applies are literally `movs r0,#N; bl 0x0801957C` with N = 1..10;
  the eleventh is the two-store special case.
* The menu activates a widget only when `widget+0x6C == 1` (`0x0801C324`), and
  that field is fed from `0x03001B34` (`0x0801C444`/`0x0801C45E`).
* Validation fires from the append handler at slot 6 (`0x0801C912`), which is
  why there is no confirm button.

**Inferred.**

* Level index *i* corresponds to level *i+1*: supported by the published list
  (`BHRTYP` = Level 2) and by starting level 2 after `BHRTYP`, but only level 2
  was started in this session.
* `0x03006B18`/`0x03006B14` are the ending request and mode number; the
  immediate write of 11 was not sampled before the engine advanced the mode to
  3, so the pair is inferred from code plus the observed credits transition.

## 8. Unknowns

* The exact consumer of `0x03006B14`/`0x03006B18` beyond "starts the ending"
  was not traced; the value 3 observed during the credits is a later mode.
* The data that fills the 3×7 password grid (glyph/tile indices) was not
  located as a static table; the grid was proven dynamically instead.
* Whether a locked level can be forced by other means (e.g. corrupted save) was
  not tested. No battery save content exists in this run (the `.sav` is 0
  bytes), consistent with a password-based progress system.
* Only this ROM (SHA-256 above) was tested. Other regions/revisions may move
  the tables; use the hashes, not the addresses, as the identity check.
* No second, algorithmic password format was found. The validator is a pure
  table lookup and the entry alphabet exactly matches the table, but "no other
  format exists" is not proven for the whole ROM.

## 9. Tooling

Shipped next to the ROM:

| File | Purpose |
|---|---|
| `asot_tables.py` | static dump of the code table and record table, and a Python reimplementation of `0x08019680`; prints accepted/rejected for sample inputs |
| `asot_type_code.py` | enters a code with real controller input via xdotool, verifies every stored byte through the mGBA GDB stub (buffer, cursor, unlock array), and screenshots the result; `--level2` continues into Level Select and starts level 2 |

`asot_type_code.py` needs mGBA started with `-g` and the game already on the
Password screen (a savestate plus `-t` makes it repeatable). mGBA's SDL
frontend hard-codes the GDB stub to TCP 2345; on a shared host that port may be
taken, in which case a tiny `LD_PRELOAD` shim that rewrites `bind()` to another
port (here 2471) is enough. The shim does not change the emulated machine, and
plain gameplay needs no stub at all.

Other tools used during the analysis (not shipped, easily reproduced):
`binutils-arm-none-eabi` (`objdump -M force-thumb`), `capstone` for the
literal-pool/BL scan, `gdb-multiarch` as a cross-check of the custom RSP client,
`xvfb` + `openbox` + `xdotool` + `scrot`/ImageMagick for display and input.

Recommended manual reproduction (no tooling beyond mGBA): boot the ROM, choose
English, `Down Down A` to the Password screen, walk the grid with the d-pad and
press `A` on `B H R T Y P`; the sixth letter validates and shows
"Password accepted".

## Legal note

No ROM, graphics, audio or other copyrighted assets are redistributed here.
The codes documented above were already published publicly; this report adds
the address map, the validator behavior and the observed effects.
