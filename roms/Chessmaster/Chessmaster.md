# Chessmaster (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Chessmaster/Chessmaster.gba` |
| Size | 4,194,304 bytes (4 MiB, `0x400000`) |
| `file` identification | Game Boy Advance ROM image: "CHESSMASTER" (ACYE41, Rev.00) |
| Header title (`0xA0`) | `CHESSMASTER` |
| Game code (`0xAC`) | `ACYE` |
| Maker code (`0xB0`) | `41` (ASCII) |
| Software version (`0xBC`) | `0x00` |
| Complement check (`0xBD`) | `0x88` |
| Header checksum (`0xBE`) | `0x0000` (rebuild artifact; computed `0xFA19`) |
| Entry word (`0x00`) | `0xEA00002E` → `0x080000C0` (stock Nintendo crt0) |
| MD5 | `da7d71352fd92c7e44de1d7341042f27` |
| SHA-1 | `5e3ac500d119a2bbe67d480edc1c1dd09061e385` |
| SHA-256 | `adc7b798b909203e1b5535ffb5682a6997721ca8d3699aa33b75ddf3219f7490` |

Region: US/EU build (`AGB-ACYE-USA` / `AGB-ACYP-EUR`), Ubisoft, 2002.

### Embedded GBA header scan

A full 156-byte Nintendo logo + header is embedded at file offset `0x31B714`
(ROM base `0x0831B714`), occupying the last `0xE48EC` bytes of the image:

| Field | Value |
|---|---|
| Entry word | `0xEA00002E` → `0x0831B820` |
| Title | `CHESSMASTER` |
| Game code | `1234` |
| Maker | `01` (Nintendo) |

The code at `0x0831B820` is a small ARM stub: it polls `0x04000120`
(JOY_RE/SIOCNT) and shuttles 16-bit words through `0x0400012A` (SIODATA32),
then calls SVC `0x11` (BIOS LZ77 decompression) with source
`r0 = 0x020002B0` and destination `r1 = 0x02017250`, then
`ldr lr,[pc] ; bx lr` to `0x02017250`. This is a **multiboot / download-play
launcher**: it receives a payload over the link serial port into EWRAM,
decompresses it, and jumps to it. It is not a cheat.

The main game references it once: the function at `0x0803E1B0` calls
`0x0803D4EC` with `r0 = 0x0831B714` (the embedded header) and
`r1 = 0x08330A74` (a data pointer). This is the "One Cartridge" /
"Link Multiplayer" feature, not an in-game cheat.

**No cracktro, no trainer, no patched entry.** The stock crt0 at
`0x080000C0` runs; the header checksum `0x0000` is the normal artifact of a
rebuilt header and the complement byte `0x88` is consistent with a
Nintendo-formatted header.

---

## 2. Executive summary

**Chessmaster (GBA) has no in-game cheat, password, button-code, or
debug/test screen.** The only cheat codes published for this SKU are
CodeBreaker *memory-edit* codes (out of scope for this engagement, and not
present as literals in the ROM because they are external device codes).

The game is a data-driven chess title. All UI is built from a table of
**103 menu records** (each record = 3 header words + a variable offset
table + 3-byte-prefixed strings; 98 records with 2 titles, 3 with 6 titles,
1 with 4 titles, 1 with 1 title). The records cover every menu in the game:
main menu, game setup, options, chess-set select, chess tutor, chess rater,
famous games, in-game menu, and multiplayer. There is no text-entry surface,
no on-screen keyboard, no password alphabet, and no button-mask sequence
table.

The only "secret" content found is a hidden opponent/title record with the
literal name `???` (record id `0x3B9` at `0x0826DE74`), plus a set of
developer/family credits text in the message bank. Both are documented
below; neither is reachable through a code.

The embedded second GBA image at `0x0831B714` is a link-play/multiboot
launcher, not a hidden game or cheat.

---

## 3. How to reproduce

Environment: Debian, `mgba-sdl 0.10.5`, `Xvfb`, `openbox`, `xdotool`,
`arm-none-eabi-objdump`, Python 3 + Capstone.

```bash
Xvfb :242 -screen 0 1024x768x24 &
DISPLAY=:242 openbox &
export DISPLAY=:242 SDL_AUDIODRIVER=dummy
/usr/games/mgba -d /mnt/gbacheats/roms/Chessmaster/Chessmaster.gba &
```

mGBA's `-d` debugger is driven through a pty (the GDB stub in this build
rejects gdb-multiarch with packet errors; SIGINT reliably breaks the `-d`
stub). Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows. Key presses were verified by reading
`KEYINPUT` (`0x04000130`): holding `x` reads `0x03FE` (A active-low).

Observed boot behaviour: the game boots into a title/attract state. Pressing
Start advances the screen state (RAM at `0x020289F0` changes state index
`1 → 2`). Pressing A on a menu item changes the screen object at
`0x020289F8`/`0x020289FC` to `0x42424242` (observed; interpreted as the item
label being rendered into the screen object's text buffer). No code entry
screen is reachable.

---

## 4. Address map

| Address | Description |
|---|---|
| `0x080000C0` | Stock ARM crt0 (entry `0x080000C0`) |
| `0x0800020C` | IRQ dispatcher (reads `IE & IF` at `0x04000200`, jumps via table at `0x02002FF0`) |
| `0x0803FCCD` | `main` (Thumb) — init, then calls the frame function `0x08006660` |
| `0x08006660` | Frame update (calls `0x08006730`, `0x08001AD0`, `0x08005270`, `0x08006B50`, `0x0800632C`, `0x080064A0`) |
| `0x0800628C` | VBlank handler (increments frame counter at `0x02003A54`, walks a screen list) |
| `0x08006D50` | Input read: `ldr r0,[0x04000130]; mvns r0,r0` (active-high key state) |
| `0x08006E9C` | Input event dispatcher (XOR of prev/cur key state, notifies listeners) |
| `0x02003A40` | Frame counter / screen-list head (EWRAM) |
| `0x02002FF0` | IRQ handler table (EWRAM) |
| `0x02028870` | Registered screen-definition table (8 static + 1 dynamic, see §6.8) |
| `0x020289E8` | Current screen object: `+0` frame counter, `+4` ptr to `0x02028700`, `+8` draw fn, `+0xC` screen def, `+0x10` state ptr, `+0x14` state index |
| `0x020289F4` | Current screen-definition pointer (observed `0x080B61D0`) |
| `0x080B61D0` | Screen definition currently active (64-cell grid, state machine) |
| `0x080B61FC` | Screen cell table (EWRAM handles `0x02002FAE`…`0x02002FB8`) |
| `0x0803FE74` | Screen setter (r0=4 → `0x080B61D0`, r0=0x40 → `0x080B61DC`) |
| `0x0804A680` | Function-pointer table used by the screen object |
| `0x081FEA14`…`0x081FF200` | Main-menu records (Standard Game, Handicap, Board Setup, Load, Link Multiplayer, Chess Tutor) |
| `0x082041CC` | "Opponent" menu record |
| `0x0823FCA8`…`0x08253E53` | 10 chess-set records |
| `0x0822A698`…`0x082784A0` | 21 opponent records (incl. `???`) |
| `0x0826DE74` | Hidden `???` record (id `0x3B9`, 6 title strings) |
| `0x082AF000`…`0x082AF900` | Chess-tutor / rater / famous-games records |
| `0x0831B714` | Embedded GBA header (multiboot/link launcher) |
| `0x0831B820` | Embedded ARM launcher entry (LZ77 → EWRAM → jump) |
| `0x0849C4C` | Credits/message text (high-bit encoded, `ENGMESS` bank) |
| `0x0849ED8` | `ENGMESS` marker (English message bank) |
| `0x0B61A8` | `&%$C_MENU` resource marker |
| `0x0B61B4` | `&%$C_SOUNDBANK` resource marker |
| `0x0B61C8` | `EEPROM_V122` save-type marker |
| `0x0B61D0` | Active screen definition (also referenced by the screen setter) |

---

## 5. Algorithm / data format

There is no cheat algorithm to reverse. The relevant reusable format is the
**menu-record format**, which is the game's entire UI description:

```
record:
  +0x00  u32  id                     (e.g. 0x142 "Standard Game", 0x3B9 "???")
  +0x04  u32  flags                   (high byte always 0x05; byte 2 = difficulty/style)
  +0x08  u32  title_count             (2 for normal items, 6 for title-progression items)
  +0x0C  u32  offset[title_count + N]  (relative to +0x0C)
  +...   strings, each: [u8 0][u8 type][u8 flags][ASCII text][0]
```

The `title_count` leading strings are the item's display names; the
remaining strings are per-frame/per-state text. Most records ship with the
literal placeholder text `"Text of frame N of state M"` (the game's text
system indexes these records by id; the placeholders are the default text
for each frame/state slot).

The screen system is a small state machine:

- A screen object lives in EWRAM at `0x020289E8`.
- `+0xC` points to a ROM screen definition (`0x080B61D0`).
- `+0x10` points into a function table at `0x0804A680`; `+0x14` is the
  state index.
- The VBlank handler at `0x0800628C` walks a screen list and calls each
  screen's update function.

Input is a generic event system: `0x08006D50` reads `KEYINPUT` and inverts
it; `0x08006E9C` XORs the previous and current state and notifies a list of
listeners. **No sequence/history buffer exists** — the dispatcher only sees
the current and previous frame, so a multi-frame button code cannot be
matched by this code path.

---

## 6. Tables

### 6.1 Main menu records (in ROM order)

| Record address | id | Name |
|---|---|---|
| `0x081FEA14` | `0x142` | Standard Game |
| `0x081FEB60` | `0x142` | Handicap Game |
| `0x081FECAC` | `0x148` | Board Setup Game |
| `0x081FEDFC` | `0x13A` | Load Game |
| `0x081FEF40` | `0x148` | Link Multiplayer |
| `0x081FF090` | `0x13E` | Chess Tutor |

### 6.2 Options / setup records

| Record address | id | Name |
|---|---|---|
| `0x082041CC` | `0x138` | Opponent |
| `0x0820430C` | `0x142` | Response Time |
| `0x08204458` | `0x13A` | Who Plays |
| `0x0820459C` | `0x142` | Teaching Mode |
| `0x082046E8` | `0x144` | Chess Set Look |
| `0x08204834` | `0x142` | Save Settings |
| `0x08235248` | `0x142` | Infinite Time |
| `0x08235830` | `0x146` | Player vs. A.I. |
| `0x08235980` | `0x14A` | Player vs. Player |
| `0x08235AD4` | `0x146` | A.I. vs. A.I. |

### 6.3 In-game menu records

| Record address | id | Name |
|---|---|---|
| `0x08288984` | `0x130` | Hint |
| `0x08288ABC` | `0x13C` | Force Move |
| `0x08288C00` | `0x13A` | Save Game |
| `0x08288D44` | `0x13A` | Load Game |
| `0x08288E88` | `0x140` | Change Sides |
| `0x08288FD0` | `0x140` | Rotate Board |
| `0x08289118` | `0x138` | New Game |

### 6.4 Chess Tutor / Rater / Famous Games records

`Basic Rules` (`0x082AEF60`), `Pieces Rules` (`0x082AF0A8`),
`Special Moves` (`0x082AF1F0`), `Notation` (`0x082AF33C`),
`Strategies` (`0x082AF47C`), `Chess Rater` (`0x082AF5C0`),
`Famous Games` (`0x082AF708`), plus 27 chapter records
(`Introduction` … `Correspondence`, `Basics` … `Strategy`) and
`Challenge Set 1/2/3` (`0x082D4370`/`0x082D44C0`/`0x082D4610`).

### 6.5 Chess sets (10)

| Record address | id | Name |
|---|---|---|
| `0x0823FCA8` | `0x13E` | Classic Set |
| `0x0823FDF0` | `0x142` | Newspaper Set |
| `0x0823FF3C` | `0x138` | Wood Set |
| `0x0824007C` | `0x142` | Kids Clay Set |
| `0x082401C8` | `0x140` | Napoleon Set |
| `0x08240310` | `0x13C` | Circus Set |
| `0x0825390C` | `0x138` | Dogs Set |
| `0x08253A4C` | `0x13E` | Fantasy Set |
| `0x08253B94` | `0x140` | Invaders Set |
| `0x08253CDC` | `0x136` | Sea Set |

### 6.6 Opponents (21 records, incl. hidden)

| Record address | id | Name |
|---|---|---|
| `0x0822A698` | `0x130` | Ryan |
| `0x0822A7D0` | `0x12E` | Ben |
| `0x0822A908` | `0x134` | Kamika |
| `0x0822AA44` | `0x130` | Ross |
| `0x0822AB7C` | `0x132` | Jesse |
| `0x0822ACB8` | `0x132` | Billy |
| `0x0822ADF4` | `0x130` | More |
| `0x082640F8` | `0x130` | Lucy |
| `0x08264230` | `0x134` | Hayden |
| `0x0826436C` | `0x134` | Alicia |
| `0x082644A8` | `0x12E` | Jon |
| `0x082645E0` | `0x130` | Rick |
| `0x08264718` | `0x144` | Board Champion |
| **`0x0826DE74`** | **`0x3B9`** | **`???` (hidden, 6 title strings)** |
| `0x08277D34` | `0x136` | Nikolai |
| `0x08277E74` | `0x136` | Muldoon |
| `0x08277FB4` | `0x130` | Will |
| `0x082780EC` | `0x132` | Waldo |
| `0x08278228` | `0x136` | Griffin |
| `0x08278368` | `0x130` | Hans |
| `0x082784A0` | `0x13E` | Chessmaster |

The hidden `???` record (id `0x3B9`, flags `0x05040902`) is the only
opponent record with `title_count = 6`. Its six title strings are:

```
"  Defender"
"    Draw\r\n   Master"
" Positional"
" Candidate\r\n   Master"
" Challenger"
"      ???"
```

The same `title_count = 6` pattern appears in three other non-opponent
records (`0x0823453C` "Beginner", `0x08249A64` "Style!",
`0x0825A36C` "Woof!"), which are skill/style title progressions. The `???`
record is the only one whose final title is the literal string `???`,
i.e. an intentionally hidden title/opponent.

### 6.7 Multiplayer records

`One Cartridge` (`0x0831AEB0`), `Two Cartridges` (`0x0831AFFC`),
`Join Game` (`0x0831B5D0`), `Link Failed` (`0x0831A438`).

### 6.8 Registered screen definitions (EWRAM table at `0x02028870`)

`main` writes 8 static screen definitions:

```
0x080B6248  0x080B6930  0x080B78A4  0x080B88A0
0x080BBF24  0x080BC5E4  0x080BD5C0  0x080BE4E8
```

A 9th entry at `0x02028890` is allocated at runtime (observed holding
`0x081B28F0`, a data structure at `0x081B28F0` containing the bytes
`22 10 22 05 08 …` and offsets `0x88, 0x96, 0xA4, 0xBE, 0xE4`). No
additional/hidden screen definition was found in the ROM.

---

## 6b. Enumeration

### Code/password space

**There is no code/password space.** The game has no text-entry surface, no
on-screen keyboard, no password alphabet, and no code validator. Therefore
there is no field layout, no checksum, and no representable value count to
enumerate. This is a proven negative over the checked space, not an
unexamined one.

### Search space checked (bounded negative)

| Check | Result |
|---|---|
| `strings` for `password`, `cheat`, `secret`, `unlock`, `debug`, `trainer`, `gallery`, `demo`, `level select`, `infinite`, `all pieces`, `all boards`, `sound test`, `hidden`, `bonus`, `special` | Only chess prose, tutorial text, and the Chess Rater "Bonus Question". No cheat/password/debug strings. |
| Plain ASCII and `ASCII|0x80` (high-bit) encodings of `STANDARD`, `HANDICAP`, `BOARD SETUP`, `MULTIPLAYER`, `CHESS TUTOR`, `RATER`, `FAMOUS`, `CHESS SET`, `SPECIAL`, `PASSWORD`, `CHEAT`, `DEBUG` | Menu labels found as plain ASCII records; no password/cheat/debug literals in any encoding. |
| Keyboard alphabets: `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, lowercase, `0123456789`, `0123456789ABCDEF`, `!?` | **0 hits** for every alphabet. No text-entry field exists. |
| Button-code sequences (Konami `U U D D L R L R B A`, `A B Start Select`, `L R L R`, `U U D D`) as bytes and as u16 key masks | **0 hits**. |
| u16 key-mask values `0x3FFE`, `0x3FFD`, `0x3FBF`, `0x3F7F`, `0x3FEF`, `0x3FDF`, `0x3EFF`, `0x3F7E` | Only graphics data (`0x2406xx` tile runs) and coincidental bytes in code. No mask table. |
| Name/profile/initials entry surfaces | **0 hits**. |
| Debug/test strings (`debug`, `test`, `demo`, `menu`, `screen`, `config`, `reset`) | Only chess prose, memory-allocation asserts (`Out of bg-characters bank 2 memory` at `0x08460B8`), and the `&%$C_MENU` resource marker. No debug menu. |
| Web: GameFAQs, Cheat Happens, libretro-database, Nintendo Fandom, IGN, GameSpot | The only GBA codes published are **CodeBreaker memory-edit codes** (libretro-database `Chessmaster (USA, Europe) (Code Breaker).cht`): `00005EED+000A+10027224+0007` (enable), `32012278+0000` / `32012278+00FF` (white clock), `32011960+0000` / `32011960+00FF` (black clock). These are external device codes, not in-game cheats; they are not literals in the ROM. No in-game password/button code is published for this SKU. |

### Novel code

None. No code system exists, so no novel code can be minted. The published
CodeBreaker list is memory-edit only and out of scope; it was verified to be
absent from the ROM as an in-game literal.

### Bounds / rejection

Not applicable (no validator). The negative result is bounded by the checks
above: every string in the image, both text encodings, the full menu-record
table, the button-mask search space, and the published-code lists were
checked.

### Unlockables (in-scope content)

The game's unlockable content is progression-based, not code-based:

- **10 chess sets** (Classic, Newspaper, Wood, Kids Clay, Napoleon, Circus,
  Dogs, Fantasy, Invaders, Sea) — selected via "Chess Set Look".
- **19 named opponents** across three difficulty groups, plus the hidden
  `???` record (`0x0826DE74`) — 20 opponents. The 21st record in the
  opponent region is the `More` pagination item, not an opponent.
- **Chess Rater** challenge sets 1–3 and the tutor chapters.
- **Famous Games** (a large bank of annotated master games; the ROM contains
  hundreds of annotation strings).

The `???` record is the only intentionally hidden entry found. Its unlock
condition was not determined (see §8).

---

## 7. Validation evidence

**Observed** (in mGBA, RAM reads / savestate diffs):

- Stock crt0 runs; entry `0x080000C0`; `main` at `0x0803FCCD`.
- VBlank handler `0x0800628C` increments a frame counter at `0x02003A54`.
- Screen object at `0x020289E8`; screen pointer `0x020289F4 = 0x080B61D0`.
- Pressing Start changes the screen state index at `0x020289FC` (`1 → 2`).
- Pressing A on a menu item changes the screen object: `0x020289F8` and
  `0x020289FC` become `0x42424242` (observed; interpreted as the item label
  being rendered into the screen object's text buffer).
- `KEYINPUT` reads `0x03FE` while A is held (input path verified).
- Embedded header at `0x0831B714` and its ARM launcher at `0x0831B820`.
- Savestate RAM/VRAM extraction (zlib `gbAs` chunk) works and matches live
  debugger reads.

**Derived** (from disassembly):

- Menu-record format (id / flags / title_count / offset table / prefixed
  strings) and the 103-record enumeration.
- Screen state machine (`0x020289E8` object, `0x0804A680` function table,
  `0x0803FE74` setter).
- Input dispatcher `0x08006E9C` only compares previous vs current frame;
  no sequence buffer, so no button code can be matched.
- The embedded binary is a BIOS-LZ77 multiboot/link launcher.

**Inferred**:

- The `???` record is a hidden opponent/title; its unlock condition is
  unknown (progression-based by analogy with the other title records).
- The credits text at `0x0849C4C` is a hidden/extra message-bank entry;
  its trigger was not found.

---

## 8. Unknowns

- The exact unlock condition for the `???` record (`0x0826DE74`). It is not
  referenced by any literal pointer; it is reached through the game's
  index-based menu system, which was not fully reversed.
- The exact trigger for the credits/message text at `0x0849C4C`.
- The full field semantics of the menu-record `flags` word (byte 2 appears
  to be a difficulty/style value; byte 3 `0x82` vs `0x02` is unexplained).
- Whether any of the 10 chess sets is locked behind progress (all 10
  records exist and are enumerated; dynamic selection was not exhausted).
- The precise on-screen identity of the current screen at boot (the ASCII
  render of the VRAM tilemap was inconclusive; the screen object state
  machine was verified instead).

---

## 9. Tooling

- `arm-none-eabi-objdump` (raw binary, `-M force-thumb` / `-M force-arm`).
- Python 3 + Capstone (planned scans), custom scripts:
  - `/tmp/opencode/chessmaster/mgba_tool.py` — pty driver for `mgba -d`
    (run/break/read/write/savestate).
  - `/tmp/opencode/chessmaster/state.py` — mGBA `.ss1` parser (PNG `gbAs`
    zlib chunk → CPU/VRAM/IWRAM/EWRAM segments).
  - `/tmp/opencode/chessmaster/walk3.py`, `input_test.py` — menu-walk and
    input-verification drivers.
- `strings`, `xxd`, `grep`, `xdotool`, `Xvfb :242`, `openbox`.
- No ROM or copyrighted assets are redistributed by this report.
