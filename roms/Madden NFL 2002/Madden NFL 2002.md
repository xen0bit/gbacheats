# Madden NFL 2002 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

- File: `roms/Madden NFL 2002/Madden NFL 2002.gba`
- Size: 4,194,304 bytes (`0x400000`), one retail GBA image.
- Header title `MADDEN NFL02`; game code `A2ME`; maker `69`; version `0x00`.
- Entry word `0xEA00002E` (stock crt0). Header checksum `0x0000`, complement
  `0xD2` (rebuilt header artifact, per guide §16.1). No cracktro or trainer.
- MD5 `d20405dfb7b446fbeb365a5cc11233c3`
- SHA-1 `9b26d3e3e641059e93efeb0732b413a375402339`
- SHA-256 `0eb0316e9eaf38481462b61fabf8679bb760e1690935f1ceb890b7d92bd9129e`
- Nintendo-logo scan: exactly one hit at file offset `0x4`; no embedded/multiboot
  images, no appended trainer.

## 2. Executive summary

The GBA SKU has **no password-entry screen and no working text passwords**. The
"Secret Codes" passwords published by 3rd party cheat indexes are tagged PC/GBC for this title;
none of their literals appear anywhere in this ROM (§6). The N64 button combo is
not applicable (C-Up/Z do not exist on GBA).

The game does have a developer-intended **button-code system on the exhibition
GAME RULES screen**, with two codes:

| Sequence | Effect |
|---|---|
| `L, L, R, R, Select` | QUARTERS changes `5 MINUTES` → `15 SECONDS` |
| `L, R, L, R, Select` | Hidden **Super Bowl win screen**: "CONGRATULATIONS TO THE LAS VEGAS BUDCATS" |

Both were confirmed in emulation with screenshots **and** a byte-level RAM diff.
The system is screen-gated (no effect on SEASON RULES) and the entire reachable
L/R prefix family was enumerated: **16 sequences tested, exactly 2 accepted**.

3rd party cheat indexes additionally documents three hidden teams (Players, Inc.; EA Sports;
Budcat) at RAM `0x0200050E`/`0x02000510` values `0x21`–`0x23`, explicitly
stating that **no in-game code is known** for them (CodeBreaker-only). Within the
enumerated in-game code space no sequence sets those addresses; memory-edit
codes are out of scope for this report.

## 3. How to reproduce

- mGBA 0.10 SDL under `Xvfb :317 -screen 0 1024x768x24`, `SDL_AUDIODRIVER=dummy`,
  `-3` scaling. Only my own PIDs were used/killed.
- Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold 110–150 ms; shorter taps are missed (guide §16.2).
- Menu path: title (PRESS START) → main (**PLAY NOW**) → **TEAM SELECT**
  (accept) → **GAME RULES**. Enter the sequences there.
- Save a state on GAME RULES (Shift+F3) so each test costs one load (F3).
- Helper scripts and captured frames were in `/tmp/madden02/`.

## 4. Address map

### ROM

| Item | File offset | ROM address | Evidence |
|---|---|---|---|
| Header / crt0 | `0x000000` / `0x0000C0` | `0x08000000` / `0x080000C0` | read |
| KEYINPUT literal (input init) | `0x000B58` | `0x08000B58` | disassembly |
| KEYINPUT literal (key mapper) | `0x001F54` | `0x08001F54` | disassembly |
| Raw→internal key mapper | `0x001F04` | `0x08001F04` | Thumb disassembly |
| Developer text bank | `0x377C0E` | `0x080377C0E` | ASCII + xref scan |
| Suspected history-template literals | `0x217874` | `0x08217874` | byte match to captured RAM history |

### RAM (from decompressed mGBA `.ss1` `gbAs` chunk, guide §16.13)

Savestate raw layout for this 4 MiB ROM (0x61000 bytes total): header `0x00000`,
VRAM `0x01000`, IWRAM `0x19000`, EWRAM `0x21000`.

| Item | Address | Notes |
|---|---|---|
| Key state (held, u16) | `0x02000368` | active-high internal map |
| Key press history | `0x02000383` | rolling 8-byte window |
| Home team id (u16) | `0x0200050E` | base `0x0019`; hidden ids `0x21`–`0x23` |
| Away team id (u16) | `0x02000510` | base `0x0010` |
| QUARTERS text buffer | `0x0200BB42` | ASCII composed at runtime |
| Menu/UI state | `0x03006Fxx`, `0x0200xxxx` | differs per screen; IWRAM also holds code |

## 5. Algorithm

### Internal key map (derived empirically)

Holding each button and reading EWRAM `0x02000368` from a savestate gives this
16-bit active-high map; it matches the raw KEYINPUT mapper at `0x08001F04`
(`A<<7`, `B<<14`, `Select<<11`, `Start<<9`, `Up<<5`, `Down<<3`, `Left/Right<<4`):

| Button | mask | Button | mask |
|---|---|---|---|
| Right | `0x0100` | R | `0x0010` |
| Left | `0x0200` | L | `0x0020` |
| Down | `0x0400` | A | `0x0080` |
| Up | `0x0800` | Start | `0x1000` |
| Select | `0x2000` | B | `0x8000` |

### Validator model

The validator compares the rolling key-history window at `0x02000383` against
fixed templates. The accepted histories were captured byte-for-byte after
entering each code and each exactly matches a literal in ROM at `0x217874`:

```
CODE A accepted history: 20 10 00 10 00 20 00 20   @ ROM 0x217874
CODE B accepted history: 20 10 00 20 00 10 00 20   @ ROM 0x21787E
```

The mapper and history window are the two structures a reimplementation needs;
the dispatch result is a screen/state write (quarters text or win screen). Code
in this title is partly copied into IWRAM (executing at `0x000001F8` at boot),
so no direct ROM pointer xref to the RAM buffers was found — the literal match
is **Derived**, the effect is **Observed**.

## 6. Tables

### Published codes verified against the ROM

| Source | Literal / sequence | Platform tag | Verification |
|---|---|---|---|
| 3rd party cheat indexes, 15 Second Quarters | `L,L,R,R,Select` | GBA page | **ACCEPTED** |
| 3rd party cheat indexes, View Super Bowl Win Screen | `L,R,L,R,Select` | GBA page | **ACCEPTED** |
| 3rd party cheat indexes, Bonus Teams N64 | `C-Up,Start,Start,Start,R,L,Z,A,A,B` | N64 | N/A on GBA |
| 3rd party cheat indexes, Cheat Codes! PC | `WILDCARD`, `PICKEDOFF`, `LACESOUT`, `NEVERMORE`, `GOLDENGOD`, `GORMENGHAST`, `HYSTERIA` | PC | 0 literal hits each |
| 3rd party cheat indexes, Hidden Teams | ids `0x21`/`0x22`/`0x23` @ `0x0200050E`/`0x02000510` | GBA | 3rd party cheat indexes say no in-game code known; out of scope (CodeBreaker) |

### Text bank (decoded per guide §11 "Strings and tables" / §16.11)

`strings` found only one ASCII bank relevant to secrets, at `0x377C0E`:
`GO <H`, `DOWN WITH DA <V`, `HI MOM`, `WE'RE ON TV!`, `JOHN MADDEN FOOTBALL`,
`EA SPORTS-ITS IN THE GAME`, `<H IN THE HOUSE`, `BUDCAT CREATIONS`,
`TIBURON ENTERTAINMENT`. These are hidden developer-credit / stadium-message
strings, not password table entries: NUL-delimited, no pointer table, no
comparison consumer. All other UI text (menus, "15 Seconds", "Raining") is
tile-indexed and composed into ASCII in EWRAM at `0x0200BB42` at runtime, which
is why `strings` cannot find menu labels. This was checked before concluding
there is no password UI.

## 6b. Enumeration

### Space definition

- Surface: GAME RULES screen only (SEASON RULES is a different, non-receptive
  screen — tested and rejected).
- Sequence length: 5 presses; the two accepted histories both end in
  `R, Select` and start with `L`.
- Input alphabet: the 10 mapped buttons above; practical branch alphabet for
  the accepted family is `{L, R}` in positions 1–4 with `Select` as terminator
  → **16 representable 5-press values**.

### Full enumeration results (all performed in the emulator)

| Space | Count | Accepted | Result |
|---|---|---|---|
| L/R × 4 + Select (`LLLLT`…`RRRRT`) | 16 | 2 | `LLRR` → 15 SECONDS; `LRLR` → Budcats win screen; other 14 rejected |
| L/R × 4 + Start (navigation terminator) | 16 | 0 | Start advances to Controller Setup; no cheat |
| L/R × 4, no terminator | 16 | 0 | quarters RAM stayed `Raining` for all 16 |
| L/R × 3 + Select | 8 | 0 | all rejected |
| `LLRR`/`LRLR` + A, B, L, R, Up, Down terminator | 12 | 0 | all rejected (A/B navigate, rest inert) |
| Same code at SEASON RULES | 1 | 0 | rejected — screen gate proven |
| Hidden-team ids after all 16 L/R+Select sequences | 16 | 0 | `0x0200050E`/`0x02000510` unchanged (`0x19`/`0x10`) |
| Published password literals in ROM | 7 | 0 | zero hits (wrong SKU) |

**Novel code:** none exists in the enumerated space. Both accepted values are
already published (3rd party cheat indexes). This is a *bounded negative*, not an omission:
every one of the 16 representable values of the accepted family was entered and
its state read, and the neighboring terminators/lengths/screens were tested.
Per guide §0.2, a novel code is reported only when it exists; inventing a
non-working "code" would contradict the evidence. The three hidden teams
documented by 3rd party cheat indexes have **no in-game unlock code** in this space (nor a published
one); they are reachable only by CodeBreaker memory writes, which are explicitly
out of scope here.

### Bounds proven by rejection

- `L,L,L,R,Select` and `L,R,R,R,Select` (undocumented neighbours) → no change,
  screenshotted.
- All 14 remaining L/R family members → `5 MINUTES` unchanged; quarters text
  buffer at `0x0200BB42` read directly for a subset and unchanged.
- Alternate terminators and shorter sequences → no change.
- Same code on SEASON RULES → no change.

## 7. Validation evidence

- **Observed** (emulator + savestate RAM): title, main menu, team select, game
  rules, controller setup, in-game scoreboard, season play (5 entries after a
  season starts), season rules, NFL schedule, and the hidden Super Bowl win
  screen. Both accepted codes with screenshots. EWRAM `0x0200BB42` changed
  `Raining` → `15 Seconds` after code A; key-history bytes at `0x02000383`
  matched the ROM templates; hidden-team ids unchanged across the sweep.
- **Derived**: internal key map from KEYINPUT mapper disassembly at
  `0x08001F04`; template correspondence at `0x217874`/`0x21787E`.
- **Inferred**: exact record stride/action code of the template table (only two
  records were identified; no direct pointer xref because code lives partly in
  IWRAM).
- No prompt-injection was encountered in fetched pages; all fetched text was
  treated as data.

## 8. Unknowns

- No hidden debug menu was reached on any walked screen; none is documented by
  3rd party cheat indexes for this SKU.
- Whether an unpublished button code of length ≥6 exists was not exhaustively
  testable; the accepted format observed is 5 presses with an 8-byte history
  window, and all 16 four-position L/R values were tested.
- The exact rendering path from tile-indexed text to the EWRAM ASCII buffer was
  not reversed (not needed for the cheat result).

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` / Capstone 5.0.7 for ROM disassembly.
- Python `ss.py`: PNG `gbAs` chunk + zlib decompress → raw 0x61000 state.
- Python PTY bridge to mGBA `-d` (GDB stub port 2345 was occupied by another
  agent; `-C gdb.port` is unsupported in this build; hardware watchpoints
  crashed the core, so savestate diffing replaced them per §16.13).
- `gba.py` (xdotool input), `keymap.py`, `sweep.py`/`sweep2.py`/`sweep3.py`/
  `sweep4.py`/`sweep5.py` (bounded enumeration), screenshot crops and montages.
- 3rd party cheat indexes (via web.archive.org 20230330215227) and 3rd party cheat indexes (via
  web.archive.org 20240409133444). Live sites returned 403.

## 10. Legal note

No ROM bytes, graphics, or audio are redistributed here. Only hashes, addresses,
algorithms and observations are published.
