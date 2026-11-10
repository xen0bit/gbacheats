# Candy Land + Chutes and Ladders + Original Memory Game (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Candy Land - Chutes and Ladders - Original Memory Game.gba` |
| Size | 4,194,304 bytes (4 MiB); real content ends at file `0x1FE1CC` |
| MD5 | `12d9fcae83c5295aac6da015b75a24d6` |
| SHA-1 | `946ccbf8d21adc7a5587ef85a9759a2ded23875d` |
| SHA-256 | `02225bf0fa6810fe510014774382379cce83836069b58d32ca836f0830024b3f` |
| Header title (`0xA0`) | `CANDYLAND CH` |
| Game code (`0xAC`) | `BC4E` (cart id `AGB-BC4E-0`, USA) |
| Maker (`0xB0`) | `20` |
| Version (`0xBC`) | 0 |
| Entry word | `0xEA00002E` → branch to `0x080000C0` (stock) |
| Fixed byte `0xB2` | `0x96` |
| Header complement (`0xBD`) | `0xB8` (recomputed `0xB8`, valid) |
| Header checksum (`0xBE`) | stored `0x0000`; recomputed `0xFAB8` (zeroed header checksum — a rebuild artifact; complement byte proves the header text itself was not edited) |
| Save hardware | none used (see §5.4) |

### 1.1 Embedded-image scan (multi-game check)

The title is a 3-in-1 pack, so the whole 4 MiB was scanned for additional GBA
headers before anything else:

* Nintendo logo (156 bytes at header `+0x04`) searched at **all** file offsets,
  and again with 16-, 32-, 48- and 96-byte prefixes: **exactly 1 hit**, at file
  `0x4` (header `0x0`).
* `0x96` at `+0xB2` with a printable 12-byte title at `+0xA0`: only `0x0`
  (101 other unaligned `0x96` hits are data).
* Stock entry branch `0xEA00002E`: exactly 1 hit, at `0x0`.

**Result: the pack is one GBA image, not concatenated ROMs.** The three games
are game modes inside a shared shell/engine, selected from the in-game
"Select Game" menu (below). There is no second crt0, no second Nintendo logo,
and no second header base to recompute. Addresses in this report are therefore
plain `0x08000000 + file offset` for the whole 4 MiB.

### 1.2 Patch / trainer check

* Entry word is the stock branch; Nintendo logo intact at `0x4`.
* No cracktro/trainer markers in the image: `TRASH`, `MODE7`, `SUNHORS`,
  `CRC`, `BANDIT`, `PATCH`, `CRACK`, `PROTECT`, `GAMESHARK` → **0 hits each**.
* Header checksum zeroed but complement valid (§1). No trainer menu exists;
  the first visible screen is the publisher logo.

## 2. Executive summary

**There is no developer-intended code system on this cartridge — no password, no
button cheat, no debug menu, no unlockable, in any of the three games.** The
three titles are modes of one engine behind a shared shell:

1. **Candy Land** — board game, 2–4 players, Human/Computer, no codes.
2. **Chutes and Ladders** — board game, 2–4 players, Human/Computer, no codes.
3. **Original Memory Game** — card game, 1–4 players, 20/42/72 cards, no codes.

The negative is bounded, not assumed:

* The image contains **exactly one** GBA header and **two** text-pointer tables:
  `0x081A534` (249 pointers, menu/UI) and `0x081BD74` (270 pointers, in-game),
  i.e. **487 unique strings** in five languages. **Zero** contain
  `password`, `passcode`, `code`, `cheat`, `secret`, `debug`, `unlock`,
  `hidden`, `bonus` or `level` in any form (whole-ROM `strings` scan: 49,435
  strings, same zero counts; the single `code` hit is a 5-byte run inside
  graphics data).
* Every screen of every game was reached and photographed, including each
  game's end-of-game results screen (§3.3, §7).
* All input goes through a single `KEYINPUT` read per frame
  (`0x0800B820`, called from the main loop at `0x08003ADE`). Game modules use
  only edge/held mask tests (`0x0800BF08`, `0x0800BF28`). No game code compares
  a *sequence* of presses; the library's 8-slot per-player press history
  (§4) has no game-module consumer.
* A whole-ROM scan for single-button mask runs (u16 ≥3, u32 ≥3, u8 ≥4) found
  **92 / 93 / 7,196** candidate runs; 24 of them have a matching 32-bit
  pointer somewhere in the image, and every examined one resolves to a data
  blob or a sprite/size/palette table (e.g. `0x0801458C`, read as a u16 size
  table at `0x0800A9CA` in an entity routine), never to an input comparison.
* Published material: no in-game passwords/button codes exist for this SKU on
  GameFAQs/TCRF/fan sources. Only a GameShark/Action Replay `.cht` exists
  (gbatemp file 2402) — those are memory-edit codes and are **out of scope** by
  the brief.
* Nothing is saved: `game.sav` stays **0 bytes** after complete playthroughs of
  all three games, and there are no SRAM/EEPROM device literals in code
  (`0x0E000000`/`0x0D000000` occur only inside graphics data, never in an
  executed save routine). There is no persistent unlock state to cheat into.

Because the cartridge defines no code space (no alphabet, no length, no
checksum, no table, no validator), the §0.2 "novel code" deliverable is
vacuous; the equivalent deliverable is the bounded negative in §6b, including
in-game rejection/limit evidence for every selection surface that exists.

## 3. How to reproduce

### 3.1 Environment

```bash
Xvfb :227 -screen 0 1024x768x24 &
DISPLAY=:227 openbox &
DISPLAY=:227 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 game.gba &
W=$(DISPLAY=:227 xdotool search --name mGBA | head -1)
DISPLAY=:227 xdotool windowfocus $W
```

mGBA 0.10.5 (SDL), binutils 2.44, Python 3.13.5. The SDL window is 720×480 at a
variable origin — read it with `xdotool getwindowgeometry` before cropping (the
window moved once between runs during this analysis; a hard-coded crop offset
will silently produce the wrong region).

Default SDL keymap used throughout: **A = `x`, B = `z`, Start = `Return`,
Select = `BackSpace`, L = `a`, R = `s`, D-pad = arrow keys.** Hold 60–150 ms;
menus are edge-triggered and a 10 ms tap is missed.

### 3.2 Menu paths

| Destination | Path from boot |
|---|---|
| Title | wait through DSI Games logo |
| Select Game | `Return` at title |
| Credits | `Return` → `Down` → `A` (bracket moves to Credits) |
| Game list focus | `A` on "Select Game" (moves focus to the 3 tiles) |
| Candy Land | `Return` → `A` → `A` (Candy Land tile is first) |
| Chutes and Ladders | `Return` → `A` → `Down` → `A` |
| Memory | `Return` → `A` → `Down` → `Down` → `A` |
| Player count | `Return` at a game's title screen |
| Player setup | `A` on the player count |
| Human/Computer | `Left`/`Right` on the setup screen; `A` to confirm |
| Begin overlay | `A` through all player tabs |
| Pause | `Return` during play |
| Quit to shell | Pause → `Right` → `A` |

### 3.3 Tests performed (all reproducible)

1. Walked every screen of all three games to the end-of-game results and back
   to the shell (Memory 1-player and 2-player; Candy Land and Chutes with two
   Computer players, fast-forward hold `Tab`).
2. Credits: scrolled end-to-end (≈130 `Down` presses) and confirmed it returns
   to the shell with no extra page.
3. Title / shell menu / player setup / pause / board: pressed Select alone,
   L, R, `Up+Down+Left+Right`, `A`×6, `R`×4, Konami
   (`Up Up Down Down Left Right Left Right B A`), `A+B+Start`,
   `L+R+Start`, `Select+Start`.
4. Boot with `B`, `Select`, and `L+R` held through the logo.
5. Selection-bound probes: `Left` at player count 2; `Down` past the last tile;
   `Down` past Credits; `Right`/`Left` around the card-count control.

Observed effects of (3)/(4): normal menu navigation only. `A+B+Start+Select`
held together does **not** soft-reset this game (no reset handler); `Select`
alone is inert everywhere. No new screen, text, sound or state appeared.

## 4. Address map

File offset → ROM address is `0x08000000 + offset` throughout (single image).

| Item | Address | Notes |
|---|---|---|
| ROM entry / crt0 | `0x080000C0` | ARM; main loop reached from here |
| `KEYINPUT` reader | `0x0800B820` | Thumb: `ldr r0,=0x04000130; ldrh r0,[r0]; bx lr` |
| Frame input update | `0x0800BE80` | called once per frame from `0x08003ADE`; stores `~KEYINPUT` |
| Key state (active-high) | `0x030044A8` | u32; full `~KEYINPUT` (keys in bits 0–9; read as u16 later) |
| Key state words | `0x030044AC`, `0x030044B0` | secondary/merged states |
| Per-player key array | `0x030044B4` | 6 × u16 |
| Key struct w/ press history | `0x03002FC0` | 24 bytes × 6 players; 8-halfword history at +0..+15, current +16, previous +20 |
| Mask test (all bits), indexed | `0x0800BF08` | 46 BL call sites |
| Mask test (all bits), word | `0x0800BF28` | 13 BL call sites |
| Key getters | `0x0800BEF0`, `0x0800BEFC` | return the word states |
| UI string pointer table | `0x081A534` | 249 `u32` pointers, ends `0x081A914` |
| In-game string pointer table | `0x081BD74` | 270 `u32` pointers, ends `0x081C1A8` |
| UI text bank | `0x081A918`–`0x081BD73` | ASCII + 0x80+ accented codepage |
| In-game text bank | `0x081C1AC`–`0x081E220` | ASCII + codepage |
| Font/hex formatter | `0x08146F8` | `"0123456789ABCDEFx0123456789abcdefx"` — number formatting, **not** a password alphabet |
| Results/final text slots | `0x081AD5C`–`0x081AFAB` | incl. unused `Final Cash Value` / `Cash Value: %$` |

## 5. Algorithm

### 5.1 Input path (derived)

```
every frame (main loop 0x08003ADE):
    raw   = KEYINPUT                      ; 0x04000130, active-low
    state = ~raw                          ; stored 0x030044A8 (u32)
    for p in 0..5:                        ; per-player slots
        prev[p] = cur[p]
        history[p].shift(cur[p])          ; 8 halfwords, 0x03002FC0 + 24*p
        cur[p]  = state & enable[p]
    ; game modules read only:
    pressed(p, mask) = (state[p] & mask) == mask      ; 0x0800BF08
    pressed(mask)    = (word    & mask) == mask      ; 0x0800BF28
```

There is **no** sequence buffer read by game code: the only writes/reads of the
history array (`0x03002FC0`) are in the input library (`0x0800BA00`–`0x0800BC60`)
and its entity/animation helpers (`0x0800AA00`–`0x0800AD20`); no game module
(`0x0804xxxx`+) touches it. Button masks are `A=1, B=2, Select=4, Start=8,
Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`.

### 5.2 Menu model (derived + observed)

All menus are the same generic widget: an integer cursor, `Up/Down` (or
`Left/Right`) bounded by a compile-time item count, `A` = confirm, `B` = back.
Cursors do **not** wrap on the shell menus or the game-tile list (they do wrap
inside the Memory card grid and the card-count control, which is a different
widget). Item counts observed exhaustively:

| Menu | Items | Evidence |
|---|---|---|
| Shell left list | 2 — Select Game, Credits | `Down` at Credits does nothing; `Up` at Select Game does nothing |
| Game tile list | 3 — Candy Land, Chutes and Ladders, Memory | `Down` at Memory does nothing (no 4th tile) |
| Player count (Candy/Chutes) | 3 — 2, 3, 4 | `Left` at 2 does nothing |
| Player count (Memory) | 4 — 1, 2, 3, 4 | visual |
| Player setup | n tabs; Human/Computer 2-way | visual |
| Pause | 2 — Resume, Quit | visual; `Right` at Quit does nothing |
| Card count (Memory) | 3 — 20, 42, 72 | cyclic; `Right`/`Left` wrap |

### 5.3 Why there is no validator to reverse

A validator needs an input buffer and a comparison. The cartridge has:

* no text-entry widget in any screen (no on-screen keyboard, no letter grid,
  no character-set table anywhere in 4 MiB — the only alphabet-like string is
  the hex formatter at `0x08146F8`);
* no string in either text table that names a code/password/debug screen;
* no code table of equal-length NUL-terminated records (the only record-like
  arrays are the two text-pointer tables and sprite tables);
* no sequence matcher (see §5.1).

### 5.4 Save / unlock state

`mGBA` created a 0-byte `game.sav` at boot and **never wrote it** across
complete 1-, 2- and 4-player sessions of all three games. Static: the only
aligned `0x0E000000` / `0x0D000000` literals lie inside graphics blobs
(`0x020360`–`0x020384`, `0x1217A4`) with no code xref; no `SRAM`/`EEPROM`/
`FLASH` strings. There is no save routine and therefore no persistent
unlockable/debug flag to set.

## 6. Tables

### 6.1 Shell / game selection

| Index | Left menu | Right tile list |
|---|---|---|
| 0 | Select Game | Candy Land |
| 1 | Credits | Chutes and Ladders |
| 2 | — | Original Memory Game |

### 6.2 Per-game configuration space

| Game | Players | Player type | Other options |
|---|---|---|---|
| Candy Land | 2, 3, 4 | Human / Computer per player | character & colour fixed by slot |
| Chutes and Ladders | 2, 3, 4 | Human / Computer per player | character & colour fixed by slot |
| Memory | 1, 2, 3, 4 | Human / Computer per player | cards 20 / 42 / 72 |

No difficulty, level, board, sound-test, language or cheat field exists.
Language is selected by the cart build (all five localizations are present in
the same tables; the USA build displays English).

### 6.3 Text space (the complete "code alphabet" that could exist)

| Table | File offset | Entries | Unique strings |
|---|---:|---:|---:|
| UI/menu | `0x1A534` | 249 | 222 |
| In-game | `0x1BD74` | 270 | 267 |
| **Total** | | **519** | **487** |

Keyword scan over all 487 unique strings (case-insensitive): `password` 0,
`passcode` 0, `cheat` 0, `secret` 0, `debug` 0, `unlock` 0, `hidden` 0,
`bonus` 0, `level` 0, `options` 0.
The only keyword-shaped hits are ordinary words (`Credits`, `Select Game`,
`Sound Engine` credit line, `Gumdrop Pass`, `you have selected …`).

### 6.4 Button-space scan (sequence-table search)

| Width | Runs of ≥N single-button masks | Runs with a matching pointer | Verdict |
|---|---:|---:|---|
| u16 (≥3) | 92 | 8 | all size/sprite tables |
| u32 (≥3) | 93 | 2 | sprite/entity tables |
| u8 (≥4) | 7,196 | 14 | tiles/palettes/entity data |

Representative disproof: `0x0801458C` (`0x20,0x40,0x40,0x80,0x80,0x80,0x200,
0x100,0x100,…`) is a power-of-two size table read as a u16 array at
`0x0800A9CA` (`ldr r3,=0x081458C; ldrh r0,[r3,r1]`) inside an entity routine,
not a key sequence. Spot checks of the 24 pointer matches land in data blobs,
entity/sprite routines and literal pools — none in the shell/menu code — and
the game's only input surface is the edge/mask tests at `0x0800BF08`/
`0x0800BF28`, with no sequence buffer consumed anywhere.

## 6b. Enumeration

### 6b.1 Space definition

The cartridge defines **no code space**: alphabet = ∅, length = 0, field widths
= 0, checksum = none, table size = 0, representable values = 0. The only
enumerable spaces are the menu/selection space and the text space:

| Space | Size | Method |
|---|---|---|
| Shell menu items | 2 | cursor bound, walked |
| Game tiles | 3 | cursor bound, walked |
| Player-count values | 3 (board) / 4 (Memory) | cursor bound, walked |
| Player-type values | 2 per player | walked |
| Card-count values | 3 (20/42/72) | cyclic walk |
| Pause items | 2 | walked |
| Text strings | 487 unique (519 pointers) | pointer tables enumerated |
| Single-button mask runs | 92 u16 / 93 u32 / 7,196 u8 | full-image scan, xref-filtered |

### 6b.2 Novel codes

**None exist and none can be minted** — there is no accepted-string set,
alphabet, checksum or decoder anywhere in the image. The §0.2 deliverable is
therefore replaced by the bounded negative below: every surface that could
carry a developer code was enumerated, and each was shown to be closed.

This is case 1 of the guide's four "no"s — **no system** (no alphabet, no
table, no validator, no input surface) — not dead code, not a cut feature and
not a gated feature: there is no code-related string, no buffer, no comparison
and no flag writer to gate.

This is *not* "I did not find one": it is (a) one header, (b) 487/487 strings
accounted for with zero code vocabulary, (c) every screen reached including all
results variants, (d) 7,381 mask-run candidates filtered to 24 pointer-bearing
data tables, (e) zero game-module readers of the press history, (f) zero save
writes.

### 6b.3 Bounds proven by rejection / limit (in-game)

| Probe | Expected if a code/hidden item existed | Observed |
|---|---|---|
| `Left` at player count "2" | hidden "1 player" or debug value | no change (stays 2) |
| `Down` at Memory tile | 4th tile / hidden game | no change (stays Memory) |
| `Down` at "Credits" | 3rd shell item | no change (stays Credits) |
| `Right` past card count 72 | hidden value | wraps to 20 (only 20/42/72 exist) |
| Konami at title / shell / pause / board | cheat flag | no change (only normal navigation) |
| `A+B+Start`, `L+R+Start` | cheat/debug screen | no change (no reset handler either) |
| `Select` at title, menu, board, pause | debug overlay | no change |
| Boot holding `B`, `Select`, `L+R` | boot menu | normal DSI Games logo → title |
| `Right` at pause "Quit" | 3rd pause item | no change (stays Quit) |

## 7. Validation evidence

**Observed (emulator, screenshots in the work dir):**

* One Nintendo logo / one header; title, shell, credits, all three games'
  titles, player counts, setups, boards, pauses and results.
* Results variants: Candy Land and Chutes → `Final Ranking` → `Winner`
  (`Rank: 1st`) → shell; Memory 1P → `Results` (`Tries: N`) → shell;
  Memory 2P → `Final Scores` (`Score` HUD) → shell.
* Text tables: 249 + 270 pointers, 487 unique strings, zero code vocabulary.
* `game.sav` = 0 bytes after complete sessions.

**Derived (disassembly):**

* Single `KEYINPUT` reader `0x0800B820`, one call per frame from
  `0x08003ADE`; key state at `0x030044A8`; mask tests `0x0800BF08`/
  `0x0800BF28`; history array only used by the input library.
* Mask-run candidates resolve to size/sprite tables (`0x0801458C` → u16 size
  lookup at `0x0800A9CA`).

**Inferred (labelled as such):**

* "Final Cash Value" / "Cash Value: %$" strings are shared-engine leftovers
  (never displayed on any results page observed); not a cut cheat.
* The 8-slot key history is the library's key-repeat/debounce state.

## 8. Unknowns

* The exact original purpose of the `Final Cash Value` / `Cash Value: %$`
  strings (dead data in this build; most likely inherited from another title
  using the same Destination Software engine).
* The precise semantic difference between the two word-level key states
  `0x030044AC` and `0x030044B0` (both fed by the same per-frame update; not
  needed to bound the negative).
* Multiplayer-link behaviour was not exercised (no link partner); it cannot add
  a code surface because it would still route through the same mask tests.

## 9. Tooling

* `mGBA 0.10.5` (SDL) under `Xvfb :227` + `openbox`; `xdotool` for XTEST input,
  `scrot` + ImageMagick for captures.
* `arm-none-eabi-objdump 2.44` (`-M force-thumb`) for the key-input and
  entity-table disassembly.
* Python 3.13 scripts in `/tmp/opencode/candyland`:
  * header/logo scan and header-field parser,
  * text-pointer-table dumper and keyword classifier,
  * u16/u32/u8 single-button-mask run scanner with xref filter,
  * `keys.py` / `seq.py` input+capture harness (window-geometry aware),
  * `memory_play.py` (card-grid probe; the completed games were run with the
    in-game Computer player and `Tab` fast-forward).
* Addresses above were read back from the raw image with `struct.unpack_from`
  before use; `objdump` literal-pool pairs are little-endian halfwords.

## 10. Legal note

No ROM, graphics, audio or extracted game text is redistributed here. Only
hashes, addresses, algorithms, counts and the analyst's own probes/screenshots
are recorded.
