# Hugo: The Evil Mirror (GBA) — Reverse Engineering Report

## 1. Target identity

| Item | Value |
|---|---|
| File | `roms/Hugo: The Evil Mirror/Hugo: The Evil Mirror.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `EVILMIRROR` |
| Game code | `AHJE` (region code `A` = USA), maker `AF` (Namco) |
| Revision | 0x00, fixed byte 0x96, complement 0xA7, header checksum 0x0000 |
| Entry word | `0xEA00002E` — stock GBA `b 0x080000C0`, **not** a cracktro |
| MD5 | `bbb939c3839fc2d4864fc7be89b60cc4` |
| SHA-1 | `9603ecc890f0d7b152214736aefc3b98976352d8` |
| SHA-256 | `47a776f9a6abdd4d3a308ae98a18ca96fb9431d2b796506282b09b95f589f543` |

Embedded-header scan (156-byte Nintendo logo at header +4): exactly **one** hit, at file 0x0.
No multi-game image, no appended trainer, no GameShark/CodeBreaker/Action Replay signature.

## 2. Executive summary

**There is no password, cheat-code, code-entry, or reachable hidden/debug menu in this GBA
SKU.** The only developer-intended button code found is a **soft reset: A+B+Select+Start**
(held simultaneously), which sets `0x03003A41` and reboots to the Nintendo logo. It was
confirmed in the emulator, and near-miss combinations were rejected.

The widely published "Level 21/22/47" passwords (`MFBBDQDBMHDK`, `PFBBDQDBMMJSD`,
`RPBFGDDBJLJD`) are **from the Game Boy Color SKU**. GameFAQs itself files them under the
heading **"Level passwords GBC"**, even on its GBA page. They are a §16.11 SKU trap. None
appears anywhere in the 4 MiB GBA image under ASCII, lowercase, UTF-16LE/BE, or ±0x20
shifts (18 literal checks, 0 hits), and the GBA image contains no code-entry surface.

A **dead/cut** debug level-select screen does exist as code and data: C++ RTTI class
`CSelectLevel` (RTTI name `0x0803F3F58`), strings `SELECT LEVEL` / `WORLD %02d` /
`LEVEL %02d` / `REAL LEVEL %02d` / `( BOSS LEVEL )` at `0x08047384`–`0x080473BC`, and a
vtable at `0x083F648C`. It is **never instantiated**: no code in the ROM references its
vtable (`0x03006C00` when copied to IWRAM), and no live savestate from any of the five
walked screens contains that vtable pointer, whereas `CMainMenu`'s vtable (`0x03006B90`)
does. This is §16.3 "dead code / cut feature", not a gated menu.

## 3. How to reproduce

Environment: `Xvfb :319 -screen 0 1024x768x24`, `DISPLAY=:319 openbox`,
`SDL_AUDIODRIVER=dummy mgba -3 <rom>`; mGBA SDL keymap A=`x`, B=`z`, L=`a`, R=`s`,
Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Input was verified by reading the
game's own input state table in savestates: holding Down produced pressed-word `0x80`
and table entry `[7] = 1` at `0x03003A48`.

Screen path (all screens walked, RAM-snapshotted via mGBA `gbAs` savestate chunks):

1. Nintendo boot → language select (English/US, Italian, German, Spanish, Dutch, French,
   Swedish, Norwegian, Danish, Finnish, Polish — 11 flags) → difficulty (Easy/Normal/Hard)
   → multi-page "How to Play" / "The Monster System" → level intro → gameplay.
2. Gameplay → Start → PAUSE banner; running out of time → `CONTINUE / QUIT` prompt.
3. Death → GAME OVER → HIGH SCORE (3-letter name entry) → main menu.
4. Main menu: **NEW GAME / LOAD GAME / HIGH SCORE / CREDITS** — exactly four, verified
   statically at `0x080091F0` (four text objects, `r6 = 3` loop) and dynamically (Down
   wraps after the fourth; no fifth entry appears).
5. NEW GAME → difficulty (3 options). LOAD GAME → six scroll save slots + CANCEL (no
   code field). HIGH SCORE → score list. CREDITS → scrolling credits.

Button-code test: from any screen, hold **A+B+Select+Start** for ~0.3 s → cold reboot to
the Nintendo logo (`rs_before.png` → `rs_after.png`). A+B+Start (Select omitted) did
**not** reboot (`bd_ABS_c.png`) — bounds proof.

Published-code test: no entry screen exists; literals checked against the ROM (§6b).

## 4. Address map

| Address (ROM unless noted) | Meaning |
|---|---|
| `0x08000000` | Stock entry branch `0xEA00002E` |
| `0x08012B4` | Input handler: reads `0x04000130`, writes pressed mask `0x03003A44`, builds 10-entry u16 button-state table at `0x03003A48` (0=up, 1=held, 2=new press) |
| `0x0801322`–`0x0801330` | **Soft-reset gate**: `KEYINPUT & 0x0F == 0x0F` → `0x03003A41 = 1` |
| `0x080045FE`–`0x080460A` | Reset consumer: reads `0x03003A41`, clears it, calls init `0x08001258` |
| `0x080048D0` | Helper returning `(flag != 0)` for `0x03003A41`; called by many screen updates |
| `0x080091F0` | `CMainMenu` constructor: creates exactly 4 menu text objects |
| `0x08009390` / `0x08009404` | Main-menu input/selection and activation handlers |
| `0x080101CC` | Dead code: `CSelectLevel` level-select input/render logic (WORLD/LEVEL/REAL LEVEL) |
| `0x08010014` | Pointer to `SELECT LEVEL` string used by the dead level-select constructor |
| `0x08047384`–`0x080473BC` | Dead debug strings: `SELECT LEVEL`, `WORLD %02d`, `LEVEL %02d`, `REAL LEVEL %02d`, `( BOSS LEVEL )` |
| `0x083F51A8`–`0x083F62A0` | Localized string-pointer table: **281** pointers into the ASCII text bank `0x08029F00`–`0x0802B200` |
| `0x083F6400` | `CMainMenu` vtable (present in RAM as `0x03006B90`) |
| `0x083F648C` | `CSelectLevel` vtable (never present in RAM as `0x03006C00`) |
| `0x0803F3F58` / `0x0803F3EE8` | RTTI names `12CSelectLevel`, `9CMainMenu` |

RAM (IWRAM) addresses, verified by GDB read and savestate diffing:
`0x03003A41` reset-request byte; `0x03003A44` active-high pressed mask;
`0x03003A48` 10×u16 button-state table; `0x03003A5C` debug byte (observed 0 in every
snapshot); `0x03003E9C` menu action field.

Savestate layout used: mGBA `.ss1` PNG, zlib-decompressed `gbAs` chunk = 397,312 bytes;
IWRAM at raw `0x19000`, EWRAM at `0x21000`. GDB cross-check:
`0x03003A48` table and `0x03003A5C` byte matched byte-for-byte.

## 5. Algorithm

Input/reset path (derived from Thumb disassembly, `objdump -M force-thumb`):

```
; 0x08012B4 — called once per frame by every screen
prev = press_mask                         ; [0x03003A60]
press_mask = 0x3FF & ~KEYINPUT            ; active-high, stored at 0x03003A44
for i in 0..9:                            ; one entry per GBA button bit
    if press_mask & (1<<i):
        table[i] = (table[i] == 0) ? 2 : 1   ; 2 = new press, 1 = held
    else:
        table[i] = 0
if press_mask == prev:  increment idle counter [0x03003A64]
else:                   reset counters / clear debug byte 0x03003A5C

; 0x0801322 — soft-reset code
if (press_mask & 0x0F) == 0x0F:            ; A + B + Select + Start
    [0x03003A41] = 1                       ; sticky reset request

; 0x080045FE — consumed on the next update
if [0x03003A41] != 0:
    [0x03003A41] = 0
    call 0x08001258                        ; re-init globals, reboot to boot logo
```

Button bit map (GBA KEYINPUT): 0=A, 1=B, 2=Select, 3=Start, 4=Right, 5=Left, 6=Up,
7=Down, 8=R, 9=L. No other mask comparison against the input state was found; there is
no sequence/ring-buffer matcher, no key-mask sequence table, and no password validator.

Dead level-select logic at `0x080101CC` (derived): Up/Down change a world counter,
Left/Right change a level counter, values are formatted through `WORLD %02d`,
`LEVEL %02d`, `REAL LEVEL %02d` and `( BOSS LEVEL )`. Its only caller is the
`CSelectLevel` render method `0x08010188`, reachable only through the vtable at
`0x083F648C`, which no code installs.

## 6. Tables

| Table / item | Value |
|---|---|
| Localized text bank | pointers `0x083F51A8`–`0x083F62A0` → ASCII strings `0x08029F00`–`0x0802B200`; **281** pointers |
| Keyword counts over entire text bank | `password` 0, `code` 0, `cheat` 0, `debug` 0, `secret` 0, `unlock` 0, `konami` 0, `level select` 0 |
| Main menu items | 4: `new game` (0x0802A0F8), `Load Game` (0x0802A1A0), `High score` (0x0802A104), `Credits` (0x0802A018) |
| Difficulty items | 3: Easy / Normal / Hard |
| Load slots | 6 scrolls + CANCEL; save record 0x20 bytes; no password field |
| Button-state encoding | 0 = released, 1 = held, 2 = newly pressed (10 entries) |
| Soft-reset mask | `0x0F` = A+B+Select+Start, exact-equality on low nibble |
| Save file | 512 bytes EEPROM/Flash; high-score 3-letter names, six 0x20-byte slots, `KODETINI` default at 0xE8; no code/password field |

## 6b. Enumeration

**Code space:** none exists. There is no alphabet, no input keypad, no checksum, no
code table, and no validator. Consequently no novel code can be minted, and the §0.2
"generate a code absent from every published list" criterion is **not applicable** to
this SKU — the correct bounded result is the proven absence below.

**Screen space enumerated (all reached, all RAM-snapshotted):** 11 language options;
3 difficulties; ≥4 tutorial pages; level intro; gameplay; PAUSE banner; time-out
CONTINUE/QUIT prompt; GAME OVER; HIGH SCORE; 4 main-menu entries; 3 difficulty entries;
7 LOAD-GAME entries (6 slots + CANCEL); CREDITS. Reachable screens that hold a
code-entry field: **0**.

**Button space enumerated:** single presses of all 10 buttons plus the chords
L+R, A+B, A+Start, B+Start, Start+Select, Up+Down, Left+Right, A+Up, B+Down,
L+R+Start, A+B+Start, A+B+Select+Start, L+R+Up+Down, A+Select, B+Select, and the
Konami sequence were pressed at the title/main menu and in gameplay. The only branch
in the ROM that consumes a button mask outside ordinary menu/gameplay movement is the
single exact test `press_mask & 0x0F == 0x0F` at `0x0801322`; there is exactly **one**
action branch (reset). Undocumented combos (L+R etc.) produced no debug screen.

**Published codes tested:** the three GameFAQs literals (`MFBBDQDBMHDK`,
`PFBBDQDBMMJSD`, `RPBFGDDBJLJD`) were searched in the ROM under 6 encodings
(ascii, lowercase, UTF-16LE, UTF-16BE, +0x20, −0x20) = **18 literal checks, 0 hits**.
The 21-consonant alphabet `BCDFGHJKLMNPQRSTVWXYZ` (implied by the codes, which contain
no vowels) and variants are also absent (0 hits), as are all 26-letter/digit alphabets
tried. GameFAQs labels these codes "Level passwords **GBC**"; the GBA SKU has no
password menu. Verdict: published codes are for a different SKU, not a ROM typo.

**Bounds proven by rejection:** the reset code requires the exact low nibble 0x0F.
A+B+Start (0x0B) and the other near-miss chords did **not** reboot — observed in the
emulator. The dead level-select is bounded by construction: its vtable pointer
`0x03006C00` was searched for in five independent savestates (main menu, difficulty,
load game, high score, credits): **0 occurrences**, while `CMainMenu`'s `0x03006B90`
was present in all five. Zero code references to `0x03006C00` exist in the ROM.

**Result type:** bounded negative (§0.2 point 5), plus one positive button code.

## 7. Validation evidence

- **Observed** — boot, language, difficulty, tutorials, gameplay, PAUSE, time-out
  prompt, GAME OVER, HIGH SCORE, main menu and its four children, LOAD GAME slots,
  CREDITS: screenshots in `/tmp/opencode/hugo/` (`c*.png`, `s*.png`, `m*.png`,
  `menu_*.png`, `cb_*.png`, `rs_*.png`, `bd_*.png`).
- **Observed** — A+B+Select+Start reboots to the Nintendo logo; A+B+Start does not.
- **Observed** — input table `0x03003A48` changes from all-zero to `[7]=1` with pressed
  word `0x80` when Down is held; GDB read matches savestate bytes.
- **Derived** — 4 main-menu items (`0x080091F0`), reset gate and consumer
  (`0x0801322`, `0x080045FE`), 281 localized strings, dead `CSelectLevel`
  (vtable xref count zero; absent from five live RAM snapshots).
- **Inferred** — the 15-frame idle path that sets debug byte `0x03003A5C` was read from
  disassembly but the byte was always 0 in snapshots; it has no reachable consumer
  because `CSelectLevel` is never instantiated.

## 8. Unknowns

- The exact purpose of the 0x03003A5C idle/debug byte and its 0x03003A64/68 counters
  could not be exercised: the only consumer is dead level-select code.
- The tutorial page count was not exhaustively numbered (all pages advanced with A/B and
  none contained input fields).
- TCRF's GBC page and the GameFAQs cheat page were blocked (403 / CAPTCHA); GBC-side
  details were taken from search snippets only and are not used as GBA evidence.
- No font/tile-indexed text bank needed decoding: every UI label was found as plain
  ASCII in the 281-entry localized pointer table.

## 9. Tooling

`objdump -M force-thumb` (arm-none-eabi), Python 3 + struct/re/capstone for pointer,
literal, BL and alphabet scans; REA/Ghidra 12.1.4 raw ARM import at `0x08000000` for
decompilation of `0x080101CC`; mGBA SDL 0.3 under Xvfb :319; `xdotool` XTEST input;
`scrot`+ImageMagick screenshots; mGBA `-g` GDB stub (single-connection) and
`gbAs`-chunk zlib savestate parser (`/tmp/opencode/hugo/ss.py`) for RAM evidence.
No game assets or ROM bytes are redistributed in this report.

**Legal note:** analysis only; no ROM, graphics, audio or text assets are published here.
