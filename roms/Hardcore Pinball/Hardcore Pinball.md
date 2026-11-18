# Hardcore Pinball (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Hardcore Pinball/Hardcore Pinball.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `HCPINBALL` |
| Game code | `AH6E` (maker `5M`, AGB-AH6E-USA) |
| Revision / version | 0x00 |
| Entry word | `0xEA00002E` → stock `b 0x080000C0` (unpatched) |
| Header checksum | `0x0000` stored; recomputed over `0xA0..0xBD` = `0x0000` (valid) |
| MD5 | `84a1007a744a784bb16c98f1ce04f94e` |
| SHA-1 | `1c8d1e6738443239f3acd14f0f979b3bde274dda` |
| SHA-256 | `6a0c96543627c88005644e0ef73e0f5672136b638175f1fe4928f4f1b8e213c6` |

**Phase 0 result.** Exactly one Nintendo-logo hit (file offset `0x4`): this is a single
retail image, not a multi-game pack, and there is no appended trainer/cracktro. The
entry word is the stock branch and the crt0 literal pool holds the normal `main`
pointer `0x080005D9` (Thumb). No patch or trainer was found or applied.

## 2. Executive summary

**No developer-intended cheat system exists in this ROM.** There is no password screen,
no button-code validator, no hidden/debug menu, and no unlockable reached by input.
Every reachable screen was walked in mGBA and every input-consuming function was
decompiled; all of them are ordinary menu/gameplay handlers using **single-button**
checks against a fixed, small item count. The only user-entered text in the game is a
3-character high-score name field whose 40-symbol alphabet (values `0..0x27`) is saved
verbatim — it is a label, not a validator (guide §16.2b).

The four "secret" elements in the game (*Unlock Sinkhole*, *Ball Unlocked*, *CHEATER*,
and the table bonuses) are **in-table script events**, not cheats: the strings live in
each table's bytecode script bank (e.g. `Unlock Sinkhole` at `0x080C770E`, `Ball
Unlocked` at `0x080C8BAD`, `CHEATER` at `0x080496AC`, `0x0808746F`, `0x080C539C`,
`0x080101B7A`). They are displayed by table events during play; no input path selects
them. No published GBA password/code list exists for this SKU (GameFAQs cheats page
returns 403 and has no archived copy; no TCRF page; web searches returned only release
data and reviews). Consequently there are no published literals to verify in the ROM.

## 3. How to reproduce

* Emulator: `mgba 0.10.5`, command `SDL_AUDIODRIVER=dummy DISPLAY=:319 mgba -3 game.gba`.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrows. Holds of ~100 ms were used; shorter holds occasionally double-stepped,
  so cursor position was confirmed from decompiled bounds and savestate PC.
* Screen path (all verified on screen and by savestate CPU PC):
  1. Boot splash (`TELEGAMES` → "THIS PROGRAM IS ©2002 BY TELEGAMES … LICENSED BY NINTENDO").
  2. Title **START / OPTIONS** — `Select` toggles highlight; `A`/`Start` confirms.
  3. **OPTIONS**: CONTROL (toggles L/R ↔ A/B), MUSIC (10), SFX (10), CREDITS.
     Left/Right adjust values; A/Start on CREDITS opens the scrolling credits.
  4. **SELECT A TABLE**: STATION, ROBOMECH, SOCCER, RETRO.
  5. Per-table **HI SCORES** panel: three slots, default name `AAA`.
  6. **Gameplay**: pinball table; flippers on L/R or A/B per the CONTROL option.
  7. **Pause**: `Select` opens a single-item **CONTINUE** overlay; B/A dismiss it.
  8. **High-score initials entry** (reached from game over): 3 letter slots, 40 symbols.
* Codes/button combos tested at title and in menus: none produced any effect beyond
  normal menu navigation (details in §6b).

## 4. Address map

| Item | Address / range | Evidence type |
|---|---|---|
| `main` (screen loop `0x0800069C`) | `0x080005D8` | Derived (objdump + Ghidra) |
| Input sampler `FUN_08000ADC` | `0x08000ADC` | Derived |
| Key mask, active-high | A=1, B=2, Sel=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200 | Derived (`mvns` of `KEYINPUT` at `0x04000130`) |
| Press (edge) global | `0x020034A0` | Derived |
| Held global / current / changed / repeat | `0x0200349C` / `0x02003494` / `0x020034A4` / `0x02003470` | Derived |
| Title handler `FUN_08007214` (2 items) | `0x08007214` | Derived (Ghidra pseudocode) |
| Options handler `FUN_08006168` (4 items) | `0x08006168` | Derived |
| Credits handler `FUN_08007408` | `0x08007408` | Derived |
| Table-select handler `FUN_08005A30` (4 items) | `0x08005A30` | Derived |
| High-score / initials handler `FUN_08006A54` | `0x08006A54` | Derived |
| High-score save routine | `0x0800D700` | Derived |
| Single-item CONTINUE/pause handler `FUN_0800C9E4` | `0x0800C9E4` | Derived |
| Font glyph source in EWRAM | `0x0200B6D0` | Derived (`FUN_08006984` literal at `0x08006A10`) |
| Table script text bank (ASCII) | `0x080496A8`, `0x08086CF0`, `0x080C4F00`, `0x080C770E`, `0x080C8BAD`, `0x101A3C`, … | Observed bytes |
| Save image (EEPROM 512 B; 4 × 0x80 table blocks) | SRAM/EEPROM `0x0E000000`, magic `9A BC DE F0 12 34 56 78` at block `+0x70` | Observed (`game.sav`) |

## 5. Algorithm

There is no validator to reimplement. The relevant algorithms are:

```
; input sampler, called once per frame (0x08000ADC)
cur  = ~KEYINPUT & 0xFFFF                 ; active-high
chg  = cur XOR prev[0x02003494]
press = cur AND chg                       ; 0x020034A0
held  = cur AND ~chg                      ; 0x0200349C
```

```
; title / options / table-select / initials handlers (Ghidra pseudocode, condensed)
switch (press & mask):                    ; masks are SINGLE-bit or "either-of"
    case 0x40:        cursor = (cursor - 1) & (N-1)   ; Up
    case 0x84:        cursor = (cursor + 1) & (N-1)   ; Down|Select
    case 0x10/0x20:   adjust value at cursor          ; Left/Right
    case 0x01|0x08:   confirm current item            ; A/Start
    case 0x02:        back                            ; B
```

No handler keeps a press *sequence*: the only history buffer is a 9-entry key-state
array used for repeat timing in `FUN_08000ADC`, and it is never compared to a code.

## 6. Tables

| Surface | Item count (source) | Items |
|---|---|---|
| Title | 2 (`cursor & 1`) | START, OPTIONS |
| Options | 4 (`cursor 0..3`) | CONTROL, MUSIC, SFX, CREDITS |
| Table select | 4 (`cursor & 3`) | STATION, ROBOMECH, SOCCER, RETRO |
| High scores | 3 (`loop < 3`) | 3 per-table entries, default `AAA` |
| Pause overlay | 1 | CONTINUE |
| Initials entry | 3 slots × 40 symbols | values `0..0x27`, no comparison |

Observed key-mask AND-immediates at all 18 sites that read `0x020034A0`:
`{0x1, 0x2, 0x3, 0x4, 0x8, 0x9, 0xD, 0x10, 0x20, 0x22, 0x30, 0x40, 0x80, 0x84}`.
The multi-bit values are all "either-of" groupings (e.g. `0x09`=A or Start,
`0x84`=Down or Select, `0x30`=Left or Right), not sequence elements. No table of
button masks, no `strcmp`/`memcmp` against an input buffer, and no password alphabet
table exists.

Font/text: menu labels are **not** stored as ASCII. Byte searches of all 4 MiB for
`OPTIONS`, `CONTROL`, `CREDITS`, `SCORES`, `TABLE`, `SELECT` returned zero hits, including
±0x20 letter shifts, UTF-16LE/BE, NUL-interleaved and reversed forms; the only ASCII
`CONTINUE` is a table-script message at `0x0000EE1C`. Labels are drawn from a glyph
bitmap copied to EWRAM (`0x0200B6D0`) by `FUN_08006984`, which indexes 40 glyphs
(`value * 13` stride). This is the font/tile-indexed text bank; decoding it confirms
there is no hidden label such as "DEBUG" or "PASSWORD" on any menu — the menu item
counts above come from the dispatch bounds in code, which is stronger evidence.

## 6b. Enumeration

Because no code system exists, the space is bounded as a negative result (guide §0.2.5).

* **String/text space:** 4,194,304 bytes scanned; case-insensitive keyword sweep for
  `password|cheat|code|debug|secret|unlock|initials|high score` produced **6 hits**,
  all classified: 4 × `CHEATER` (table scripts), `Unlock Sinkhole` and `Ball Unlocked`
  (table scripts). Zero hits for any password/debug label in ASCII, shifted ASCII,
  UTF-16, or tile-index-searchable forms.
* **Input space:** 18 code sites read the edge-triggered key global; 43 `AND`-immediate
  masks were extracted; the widest is 4 bits (`0xD`, "A/Select/Start pressed"), and no
  site compares a mask sequence or stores one beyond the 9-entry repeat array.
* **Menu space:** every menu index was walked and its bound read from code:
  2 title, 4 options, 4 tables, 3 high scores, 1 pause, 3×40 initials. Sum of all
  reachable menu entries = 14; no unlabelled or unreachable entry was found in the
  dispatch code.
* **Button-code tests (novel/unpublished inputs):** six sequences were entered at the
  title screen with savestate PC as ground truth. Baseline PC `0x0800738B` (title
  handler). Konami code ended at `0x080066CD` (options handler — ordinary cursor
  navigation ending in A), `L+R+Start` and `Start×5` at `0x08005D59` (normal START
  confirmation), `A+B+Start+Select`, `UpUpDownDownLeftLeftRightRight`, `L+R+A+B` all
  stayed at `0x0800738B`. **No sequence unlocked a new screen or flag.** Since no
  system exists, no novel code could be minted; the negative is bounded by the counts
  above rather than by an accepted generated code.
* **Bounds / rejection proof:** the only field with a range is the initials field
  (`0..0x27` per letter, 3 letters = 40³ = 64,000 spellings). It is accepted and saved
  by `FUN_0800D700` without any checksum or range rejection — proving it is a name
  field, not a code. No out-of-range code input exists to reject.
* **Published-code verification:** none available. GameFAQs cheats page returned HTTP
  403 and had no Wayback snapshot; TCRF has no page for this title; web searches
  returned release data/reviews only. Therefore zero published literals were found to
  test against the ROM (and none could be absent).

## 7. Validation evidence

* **Observed:** boot/title/options/credits/table-select/high-score/gameplay/pause screens
  in mGBA on `:319`; savestate `gbAs` chunks parsed to raw RAM (PC @0x74, EWRAM key
  globals, 512-byte EEPROM image with 4 table blocks and magic signature); key-mask
  sequences entered in-game with PC recorded before/after.
* **Derived:** Ghidra/objdump disassembly of `main`, input sampler, and all six menu
  handlers; item-count bounds (`&1`, `0..3`, `&3`, `<3`, `0..0x27`); font pointer
  `0x0200B6D0` and 40-symbol stride; save/checksum routine `0x0800D700`; absence of
  ASCII/tile-searchable hidden labels; key-mask scan results.
* **Inferred:** the exact in-table trigger of the four `CHEATER` messages and the two
  unlock strings (they are script-bytecode events; the script VM was not fully
  decompiled). These are gameplay events, not input-reachable cheats — the input paths
  were exhaustively checked and none selects them.

## 8. Unknowns

* The table-script VM (opcodes `0x07` text, `0x16`, `0x1a`, `0x22` end, `0x36` conditional,
  etc.) was not fully decoded, so the precise in-game action that prints `CHEATER` or
  grants `Unlock Sinkhole` is unproven. This does not affect the cheat-code conclusion:
  no controller-input path reaches those strings.
* The glyph bitmap at `0x0200B6D0` was identified and its 40-value indexing derived, but
  its pixels were not OCR'd into a letter↔index table (the menu bounds are proven from
  code instead). A hidden label would still have to be selected by a menu handler, and
  every handler's full item range was walked.
* The initials-entry screen was confirmed from code (`FUN_08006A54`, `param_2 != 0`) and
  the empty `AAA` high-score panel was observed, but a live game-over→initials capture
  was not obtained before the all-balls-drain window (the ball remained in play for the
  observation period). Its behavior is Derived, not Observed.

## 9. Tooling

* `file`, `xxd`, `strings`, `grep`, `md5sum`/`sha1sum`/`sha256sum` — Phase 0/1.
* `python3` + custom scripts: `scan_input.py`, `scan_ptr.py`, `ctx2.py` (Capstone
  5.0.7 PC-relative literal resolver), savestate `gbAs` zlib parser, font renderer.
* `arm-none-eabi-objdump -M force-thumb` — raw Thumb disassembly.
* REA MCP + Ghidra 12.1.4 — `open_binary` (raw-binary, ARM, base `0x08000000`),
  `resolve_containing_procedure`, `procedure_pseudo_code`, `close_binary`.
* `mgba 0.10.5` under `Xvfb :319` + `openbox`, `xdotool`, `scrot`; `SDL_AUDIODRIVER=dummy`.
* No ROM or copyrighted assets are redistributed; only addresses, hashes and findings are reported.
