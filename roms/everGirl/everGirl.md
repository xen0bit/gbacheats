# everGirl (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/everGirl/everGirl.gba` (analysis copy at `/tmp/opencode/evergirl/everGirl.gba`) |
| Size | 4,194,304 bytes (4 MiB) |
| `file` | Game Boy Advance ROM image: "EVERGIRL" (BEVE78, Rev.00) |
| Header title | `EVERGIRL` @ 0xA0 |
| Game code / maker | `BEVE` / `78` |
| Version | 0x00; fixed byte 0x96 @ 0xB2 present |
| Entry word | `0xEA00002E` (stock branch to 0x080000C0, no cracktro/trainer) |
| MD5 | `3d803864b58e1f842dd7ac944a52367a` |
| SHA-1 | `d6b58d50634b8541d631ce893222ef5f7bbdac6a` |
| SHA-256 | `58f1d286d5d3fd53af95a529406ff7b8d521ff60e49fcadaf694c445c0c2ea59` |

## 2. Executive summary

**No developer-intended password, button code, or code-entry screen exists in this
GBA build.** everGirl is a PDA-styled life/adventure game: the only persistent
state is a 4-slot EEPROM save (512-byte `.sav`), and all unlockable content
(Extras: Case / WallPaper / Ring Tone, four mini-games, four phone-book friends)
is reached through ordinary play. Every reachable screen was walked with
screenshots; no keyboard, text-entry field, cheat validator, or hidden menu gate
was found.

The ROM *does* contain a large developer level/asset-select data set — plain
ASCII strings `Select Episode`, `Asset Viewer`, `Normal Boot`, `Test Room`,
`Fx Player`, `Music Player`, `Obj Viewer`, `Level`, `MapX`, `MapY`, plus 210
`Episode-N Quest-M` entries (14 episodes × 15 quests). This is a **bounded
negative**, not an oversight: its renderer routines at `0x0801573C` and
`0x08015800` never executed during a complete title→save→room→pause→submenu
walk, while a live breakpoint at the ordinary scene initializer `0x08014190`
*did* fire. No button combination at the title screen or held at boot opened
it (counts in §6b). The strings are therefore developer material with no
retail input path reachable from the screens examined, not a player cheat.

No GameShark/CodeBreaker/Action Replay codes were used or reported.

## 3. How to reproduce

- mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `mgba -3 everGirl.gba`.
- SDL keymap verified by menu navigation: A=`x`, B=`z`, L=`a`, R=`s`,
  Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys 100–300 ms.
- Path: boot (THQ → Nickelodeon → legal text → title, ~16–20 s) → **Start** →
  save-slot screen → **A** to Load/**New** → short intro dialogue (A to advance)
  → bedroom scene → **Start** → pause carousel.
- Pause carousel: Left/Right selects, A opens, B backs out. A savestate on the
  pause screen (`Shift+F1`, load with `F1`) makes each experiment one keypress.
- GDB: `mgba -g -3`; `gdb-multiarch -ex 'set architecture arm' -ex 'target remote
  :2345'`. A GDB disconnect while the target is running can kill this mGBA
  build; keep the client attached or use savestate diffing instead.
- Work files (screenshots, scripts, states) are in `/tmp/opencode/evergirl/`,
  never in the ROM folder.

## 4. Address map

| ROM / address | Meaning |
|---|---|
| `0x0000A0` | Header title `EVERGIRL`; `0x00AC` game code `BEVE78` |
| `0x080000C0` | ARM entry point (stock crt0) |
| `0x080234AC` | `main` (Thumb pointer from header `+0x110`) |
| `0x0801E87C` | Scene dispatcher: `idx = byte[0x0200AFD0]`, calls table `0x083E0968[idx]` |
| `0x083E0968` | Scene init table: `[0]=0x0801E82D`, `[2]=0x0801F491`, `[3]=0x080342E8` |
| `0x08014190` | Ordinary scene initializer; writes `1` to EWRAM `0x02002234`; loads `0x080369CC`/`0x080369D4` ("MapX"/"MapY" strings) — **breakpoint observed to fire** |
| `0x0801573C`, `0x08015800` | Functions that consume the developer menu record table at `0x08147C18` — breakpoints never fired |
| `0x08147C18…` | Developer menu records, 0x1C-byte stride, string pointer at `+0x18`: `0x080369F8` "Obj Viewer", `0x080369E8` "Music Player", `0x080369DC` "Fx Player", `0x08036A0C` "Photo 1", `0x08036A04` "Race 1", then 210 quest entries from `0x08036B2C` |
| `0x08149524…` | Second developer menu record set, also 0x1C stride: `0x08037B50` "Test Room" (`0x08149538`), `0x08037B44` "Normal Boot" (`0x08149558`), `0x08037B34` "Asset Viewer" (`0x08149574`), `0x08037B24` "Select Episode" (`0x08149590`) |
| `0x081438F8` | Function-pointer slot `0x08014191` (Thumb) used by 13 scene-availability queries |
| `0x080369C0` | ASCII debug label bank: `Level`, `MapX`, `MapY`, `Fx Player`, `Music Player`, `Obj Viewer`, `Photo 1`, `Race 1` |
| `0x08037A80` | `Episode 14` … `Episode 1`, `Select Episode`, `Asset Viewer`, `Normal Boot`, `Test Room`, `Level`, `MapX`, `MapY` |
| `0x03C0000–0x03E0000` | In-game dialogue text bank (glyph codes, decoded in §5) |
| `0x02002234`, `0x0200AFD0`, `0x0202254` | EWRAM state bytes (savestate EWRAM base `0x21000`) |

## 5. Algorithm (text decoding, not a validator)

The visible UI strings are **glyph codes**, which is why plain `strings` shows
`EVER6IEW` for the on-screen "EVERVIEW". Decoder derived from the bank at
`0x3C0A30`:

```
ff fc        -> space (word separator)
0x21..0x3A   -> uppercase ASCII = byte + 0x20   ('6'->'V', '0'->'P', ')'->'I')
0x41..0x5A   -> literal uppercase ASCII
0x0E / 0x0D  -> line break / control
0x27 / 0x2E  -> apostrophe glyph
```

Worked example — raw `ff fc 27 4f 4f 44 ff fc 4d 4f 52 4e 49 4e 47 0e`
decodes to `" GOOD MORNING|"`, matching the introductory dialogue screenshot
exactly. No checksum, permutation, or comparison routine consumes player text:
there is no validator to reverse.

## 6. Tables

**Pause menu (8 entries, left/right carousel):** Continue, Save Game, Mini Game,
Extras, Text Message, Phone Book, Options, Exit. Screenshots:
`pl_all.png`, `extras2_c.png`, `tm_open2_c.png`, `phone2_c.png`, `options2_c.png`.

**Submenus:** Mini Game — Race, Memory, Photo, Rhythm (4). Extras — Case 1,
WallPaper 1, Ring Tone 1 (3, all initially unlocked at count 1). Phone Book —
Taylor, Chloe, Karen, Stephanie (4). Options — Sound Yes, Music Yes (2).
Text Message — "No Current Message" (0 entries). Save slots — 4.

**Developer data counts:** 14 episodes × 15 quests = 210 records, plus
Test Room / TestRoom2 / MidtownSpecial / SchoolSpecial / several
TownRace*Special scene names.

## 6b. Enumeration

**Code-space size: zero.** There is no alphabet, password length, checksum,
button mask table, or code validator in this ROM, so no code space can be
defined and no novel code can be minted. This is a *bounded negative*, with the
bounds established as follows:

| Test | Count | Result |
|---|---|---|
| Single-button presses at title | 10 | No new screen; only the "Press Start" prompt toggles |
| Two-button combos at title (from savestate, one fresh load each) | 45 | No new screen; all screens matched the title or its immediate Start transition |
| Three-button combos at title / during boot | 12 + 16 | No debug menu; boot combos all reached the normal splash/title |
| Reachable pause entries walked, including every submenu | 8 + (4+3+1+4+2) | No code-entry field, no hidden entry |
| Live GDB breakpoints on developer-menu renderers `0x0801573C`, `0x08015800` | 2 | **0 hits** across title→save→intro→room→pause→all submenus |
| Control breakpoint on normal scene init `0x08014190` | 1 | **1 hit** — debugger and harness verified working |
| ASCII literal scan for password/cheat/debug tokens | 118,989 `strings` lines | Only `Code: B.Wodok` (Shin'en GAX audio banner, guide §11 decoy) and developer asset/scene names; zero password strings |
| Decoded dialogue bank keyword scan (128 KiB, font decoder of §5) | 0 `PASSWORD`, 0 `SECRET`, 0 `CHEAT`, 0 `CODE`; `UNLOCK`×1, `BONUS`×13, `EXTRA`×6, `ENTER`×15 | All hits are ordinary gameplay dialogue / tutorial text; the `DEBUG`×2 developer line is cutscene-verification text ("NOT THE RIGHT CUTSCENE DEBUG VERIFY THE ALLSCRIPTDEFINE"), not a code |

**Rejection bounds:** not applicable — no input format exists, so no
out-of-range code can be submitted. The boundary proved here is the *input
surface* (all 8 pause entries and their children) plus the 55 title combos and
the developer-menu renderer breakpoints.

## 7. Validation evidence

- **Observed**: every screen in §3/§6 captured as a screenshot in the work dir;
  save file created (512-byte EEPROM, 4 slot records at 0x00/0x64/0xC8/0x12C);
  GDB breakpoint log (`gdb_batch.log`) showing one hit at `0x08014190` and none
  at the two developer-menu routines; savestate `gbAs` chunk decoded to a
  397,312-byte state with EWRAM at `0x21000`.
- **Derived**: text-bank glyph mapping (§5) from raw bytes to rendered dialogue;
  record strides and string pointers in §4 from `struct.unpack` of ROM words;
  scene dispatch from disassembly of `0x0801E87C`.
- **Inferred**: that the developer level-select is *unreachable* rather than
  absolutely absent — the breakpoints and combo sweep bound the retail input
  paths tested, but the game was not completed (estimated ~5 h), so a gate
  behind story progression cannot be excluded.

## 8. Unknowns

- Full story completion was not performed; Extras counts may rise through play,
  and a gate that only appears after clearing all 14 episodes was not tested.
- The exact input (if any) that would open the developer menu could not be
  derived: no direct code xref reaches its record tables, and no boot/title
  combination in the tested set did.
- A single GDB disconnect killed one mGBA instance; dynamic checks after that
  point used fresh processes or savestates.

## 9. Tooling

- `strings -t x -n 3`, `xxd`, `arm-none-eabi-objdump -M force-thumb`, Capstone.
- `scan.py` (4-byte pointer scan), `blscan.py` (Thumb BL target scan),
  `state_read.py` (mGBA `.ss1` `gbAs` zlib decoder and EWRAM reader).
- `k.py` (xdotool key/screenshot helper), `combo_test.py`, `title_combos.py`,
  `boot_combos.py`, `title_brute.py` (savestate-backed combo sweep),
  `gdb_harness.py`, `gdb_ctrl.py`, `gdb_batch.gdb`.
- All artifacts live in `/tmp/opencode/evergirl/`; no ROM or copyrighted asset
  is redistributed by this report.

**Legal note:** only hashes, addresses, algorithms, and original scripts are
published here. The ROM and extracted graphics/text are not redistributed.
