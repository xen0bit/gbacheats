# Games Explosion! (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Games Explosion/Games Explosion.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `GAMEEXPLSION` |
| Game code | `BG7E` |
| Maker | `78` |
| Version | 0 (Rev. 00) |
| Entry word | `0xEA00002E` → `b 0x080000C0` (stock crt0, no cracktro patch) |
| Header checksum | `0x0000`; complement byte `0x51` (rebuilt/vanity header, per guide §16.1) |
| MD5 | `05c54425438b4e1fb9944f380df39b4e` |
| SHA-1 | `f2d95cabf5cd75ee4ebcdf7b8ef669c6d8ede989` |
| SHA-256 | `07e987e29edc3794f0ec3e771381ffa9be02c3ecbff5a780e7b42647f139f211` |
| Publisher/developer (web) | THQ / FrontLine Studios, Engine Software "HEL Library 2.0.0 RC1" |

Embedded-header scan: searched the whole 4 MiB for the exact 156-byte Nintendo logo from this
ROM. Exactly **one** hit, at file `0x4` (header base `0x0`). This is a single image, not a
2-in-1 / multiboot pack. No appended trainer or patch signature found.

## 2. Executive summary

**Finding: this ROM has no developer-intended cheat system — no password entry, no button
code, no hidden debug menu, and no unlockable content.** The entire developer-facing surface
is a hierarchical menu shell (root ring → 5 categories → 16 games) plus a per-game options
menu (NEW GAME / RESUME / DIFFICULTY / [ROUNDS] / HELP / QUIT). Every reachable menu item was
enumerated at runtime and matched one-to-one against a statically decoded dispatch table;
there are no unreachable or unhandled entries.

The four "cheat codes" found on the web for this title are **CodeBreaker raw memory-write
patches** (e.g. `10300730C 00000063` = write 0x63 to IWRAM 0x0300730C for "infinite lives").
They are external cheat-device codes, explicitly out of scope for this engagement, and
**none of their target addresses appear as literals anywhere in the ROM** (0 hits for
0x0300730C, 0x030073E8, 0x02011024, 0x02002DE4) — they are volatile RAM locations, not
in-game codes.

The report therefore delivers a **bounded negative**: the whole reachable screen set was
walked with RAM evidence, the text space was searched in ASCII and decoded where it is
font/tile-indexed, the button/key space was checked against the input state machine, and the
game-launch table was counted (exactly 16 entries, no hidden 17th).

## 3. How to reproduce

- Emulator: mGBA SDL (`mgba -3`, built from `/usr/local/bin/mgba`; also run as a renamed copy
  `gxmgba` to avoid other agents' `pkill -x mgba`). Xvfb `:317`, `openbox`,
  `SDL_AUDIODRIVER=dummy`.
- Keymap (mGBA SDL default): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
- Boot → "Fula Sound System" splash → title screen "GAMES EXPLOSION!" with a circular
  selector and a preview pane.
- Root ring (4 items, all walked): **CATEGORY**, **OPTIONS**, **HELP**, **CREDITS**.
  Left/Right cycles, A selects, B backs out.
- CATEGORY → 5-item ring: NEON, BOARD, ZAP, CLUB, CYBER (visual order). A opens the game
  list for that category; game lists contain 3/2/4/4/3 games respectively (16 total).
- HELP → scrollable text screens; also a full 16-game alphabetical list screen.
- OPTIONS → 2 toggles (0x03000A44 / 0x03000A48 in IWRAM).
- Selecting any game opens a per-game menu: NEW GAME / RESUME / DIFFICULTY / [ROUNDS in
  some games] / HELP / QUIT. DIFFICULTY cycles EASY/MEDIUM/HARD. QUIT returns to the root
  ring.
- RAM evidence: savestates were written with `Shift+F1..F9`; the `.ss1` PNG's `gbAs` chunk
  was zlib-decompressed (per guide §16.13) to read IWRAM (state offset `0x19000`) and EWRAM
  (state offset `0x21000`). Verified by locating the copied game-name pointer table at
  IWRAM `0x03004F34`.

Published codes tested: none are in-game codes; all four are CodeBreaker memory patches and
were verified to be absent from ROM literals (see §6b).

## 4. Address map

All addresses are ROM (`0x08......`) unless marked RAM. File offset = address − `0x08000000`.

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` / `0x08000100` | code | crt0, ARM then Thumb; copies `.data` to IWRAM/EWRAM |
| `0x08003054` | code | ARM `main`; calls init `0x0803D3D8`, then the state machine in a loop |
| `0x080013A8` | code | ARM shell/menu state machine (state at EWRAM struct `+0x29D`) |
| `0x0802CDC` | data | **game-launch jump table: exactly 16 pointers** (`0x08002ED4` … `0x08002D28`) |
| `0x0802CA8` | code | game launcher: `main` passes the selected index here |
| `0x08000904`…`0x08000A3C` | code/data | per-menu item-table setters (count at struct `+0x2D8`, table pointer at `+0x2D4`) |
| `0x08167600`…`0x08167634` | data | u16 menu item-ID tables (root, options, 5 categories) |
| `0x08345178`…`0x08345228` | data | 16 NUL-terminated ASCII game names |
| `0x08349F4C` | data | 16-entry pointer table to those names |
| `0x08345244`… | data | help/navigation strings and per-game help sentences |
| `0x0833F000`…`0x08341738` | data | font/tile glyph banks (menu labels are rendered as sprite art) |
| `0x02000B40` | RAM (EWRAM) | shell state struct: `+0x2B3` selected index, `+0x2D8` item count, `+0x2DA` context, `+0x2D4` item-table pointer |
| `0x03004F34` | RAM (IWRAM) | copy of the 16 game-name pointers (boot `.data` copy) |
| `0x03004300` | RAM (IWRAM) | global pad state (38 code references) |
| `0x03000A44`, `0x03000A48` | RAM (IWRAM) | the two OPTIONS toggle bytes |

Savestate layout for this 4 MiB ROM (verified): raw `gbAs` state length `0x61000`;
VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`.

## 5. Algorithm

Shell state machine (`FUN_080013A8`, ARM):

```
state = *(u8 *)(S+0x29D)          // S = EWRAM 0x02000B40
context = *(u8 *)(S+0x2DA)        // 0=root, 2=options, 3=category ring, 4=game list
sel = *(u8 *)(S+0x2B3)
table = *(u32 *)(S+0x2D4)         // u16 item-ID array
count = *(u16 *)(S+0x2D8)
pad = *(u8 *)0x03004300           // bit0x40=A, bit0x80=B, byte[4]&1=Up, &2=Down

if state == 1:
    if B:       back out (context 0/1/2/3 -> root/category), play sound 0/2
    if Up/Down: sel = (sel ± 1) mod count; state = 2 (fade)
    if A:       item = table[sel]
                switch(context):
                  case 0: 0x15 HELP -> FUN_08000CD0 (text screens)
                          0x16 CATEGORY -> FUN_08000A1C, context=3
                          0x17 CREDITS -> animation (DAT_08001B94/9C/A0/A4/A8)
                          0x19 OPTIONS -> FUN_08000920, context=2
                  case 2: 0x1B/0x1C -> toggle IWRAM 0x03000A44 / 0x03000A48
                  case 3: 0x10..0x14 -> FUN_080009F8/9D4/9B0/98C/968
                                       (set 3/2/4/4/3-item game list), context=4
                  case 4: FUN_08001044; state=3
                return item (the selected game index for context 4)
```

`main` takes that return value, masks it to 8 bits, and calls `0x0802CA8`, which indexes the
16-entry jump table at `0x08002CDC`. There is **no branch on any extra input state**, no
checksum, and no password buffer anywhere in this path.

## 6. Tables

Root items (table `0x08167606`, count 4): `0x16` CATEGORY, `0x19` OPTIONS, `0x15` HELP,
`0x17` CREDITS.

OPTIONS items (table `0x08167602`, count 2): `0x1B`, `0x1C` (two boolean toggles).

Categories (table `0x0816762E`, count 5) → game lists:

| Item | Category label (decoded from tile art) | Table | Count | Game indices → names |
|---|---|---|---|---|
| `0x10` | NEON | `0x08167628` | 3 | 7 Neon Square, 13 Sudoku, 14 Tic Tac Toe |
| `0x11` | BOARD | `0x08167624` | 2 | 2 Checkers, 5 Eliminate |
| `0x12` | ZAP | `0x0816761C` | 4 | 6 Ice Jumper, 8 MC Rudolf, 11 Pizza Man, 15 Warehouse Man |
| `0x13` | CLUB | `0x08167614` | 4 | 0 Avoider, 9 Music Pop, 10 Pipe Master, 12 Space Shooter |
| `0x14` | CYBER | `0x0816760E` | 3 | 1 Black Jack, 3 Crazy Bowling, 4 Darts |

(The visual order of the category ring was BOARD/CYBER/ZAP/CLUB/NEON when walked; the u16
values above are the static IDs. Sum of counts = 16, matching the launch table and name table.)

All 16 games (name pointer table `0x08349F4C`, also visible on the HELP list screen):
Avoider, Black Jack, Checkers, Crazy Bowling, Darts, Eliminate, Ice Jumper, Neon Square,
MC Rudolf, Music Pop, Pipe Master, Pizza Man, Space Shooter, Sudoku, Tic Tac Toe,
Warehouse Man.

Per-game menu items observed: NEW GAME, RESUME, DIFFICULTY, HELP, QUIT, plus ROUNDS in the
two-player games (e.g. Checkers). DIFFICULTY values: EASY / MEDIUM / HARD.

## 6b. Enumeration

**There is no code space to enumerate; the negative is bounded as follows.**

1. **Screen space — fully enumerated.** Root ring 4/4 items walked with RAM confirmation
   (state struct ctx=0, table `0x08167606`, count 4). Category ring 5/5 items verified
   (ctx=3, table `0x0816762E`, count 5), each game list opened and counted (3+2+4+4+3 = 16).
   HELP's 16-game list and text screens, OPTIONS' 2 toggles, CREDITS animation, in-game menus
   (NEW GAME/RESUME/DIFFICULTY/HELP/QUIT, ROUNDS where present), DIFFICULTY cycle, gameplay
   start, and GAME OVER screen were all reached and screenshotted. Six games were launched in
   one automated pass (`game_00..game_05`) and further games were entered manually; every
   in-game menu uses the same generic item set.
2. **Menu dispatch — closed.** Every item ID in every menu table (`0x10`–`0x1C`) has a case
   in `FUN_080013A8`; no unhandled ID and no extra menu table was found. The game-launch jump
   table at `0x08002CDC` has **exactly 16 entries** followed by non-pointer data — no hidden
   17th game/debug launcher.
3. **Text space — searched and decoded.** `strings -t x -n 3` (55,333 lines) and `-n 5`:
   zero occurrences of password / passcode / cheat / secret / unlock / level select / debug
   menu. The only `bonus`/`extra life`/`hidden color` hits are gameplay-help prose
   (e.g. `0x345E6C`, `0x2654BC`) describing normal game rules. The visible menu labels are
   **not ASCII**: they are font/tile-indexed sprite art in the bank around `0x0833F000`–
   `0x08341738`; they were decoded by OCR of the rendered circle labels (CATEGORY, OPTIONS,
   HELP, CREDITS, NEON, BOARD, ZAP, CLUB, CYBER, SOUND, game names). Help text *is* ASCII in
   the bank `0x0834528C`+ and was dumped directly. No hidden label or debug string exists in
   either bank.
4. **Button/key space — checked.** Pad state is a single byte at IWRAM `0x03004300`
   (38 code xrefs). The shell input handler tests only A (`0x40`), B (`0x80`), Up (`byte[4]&1`)
   and Down (`byte[4]&2`) individually; there is no multi-button sequence, ring buffer, or
   progress index — the structural prerequisites for a button code (guide §5.4a) are absent.
   No published button codes exist for this title.
5. **Published codes — verified and rejected as out of scope.** Web results (3rd party cheat indexes) list only four CodeBreaker RAW memory patches:
   `10300730C 00000063` (Space Shooter lives), `20330073E8 000F423F` (Space Shooter score),
   `102011024 0000000E` (Avoider money), `102002DE4 0000270F` ("Ice Climber" lives).
   They target volatile RAM addresses, and a literal scan of the 4 MiB ROM found **0 hits**
   for each of 0x0300730C / 0x030073E8 / 0x02011024 / 0x02002DE4 — i.e. they are not ROM
   data, not in-game codes, and cannot be entered through any screen. No 3rd party cheat indexes in-game password exists.
6. **No novel code can be minted** because no validator, alphabet, table of accepted strings,
   or key sequence exists. §0.2's "generate a code absent from published lists" is
   inapplicable; the required substitute — a closed-screen/closed-space proof — is provided
   in items 1–5 above.

## 7. Validation evidence

- **Observed** (emulator/savestate): title root ring, category ring, game lists, HELP list of
  16 games, in-game menus, DIFFICULTY/HELP/QUIT, GAME OVER; state struct
  `ctx/sel/count/table` values read from `gbAs` savestate bytes; game-name pointer table at
  IWRAM `0x03004F34`; six game launches captured in `game_00.png`…`game_05.png`.
- **Derived** (disassembly / REA decompilation): the ARM state machine `0x080013A8`, the
  item-ID tables at `0x08167600`+, the 16-entry launch table at `0x08002CDC`, the crt0 data
  copy to IWRAM/EWRAM, and the pad-state address `0x03004300`.
- **Inferred**: the mapping of category labels to item IDs (the ring order seen on screen was
  combined with the static table order); cosmetic credits animation details were not fully
  played.
- **Negative results**: counted, not assumed — 4 root items, 5 categories, 16 game-launch
  entries, 2 options, 0 password strings, 0 button-code structures, 0 CodeBreaker target
  literals in ROM.

## 8. Unknowns

- The exact visual category label for static item IDs `0x12`/`0x13` (ZAP/CLUB vs. the reverse)
  was read from a transient screenshot; the underlying game-index lists are exact.
- In-game RAM variables (lives, score, money) were not individually traced to writers; the
  CodeBreaker addresses were checked only for ROM-literal presence, not live patched.
- No persistent high-score system: `Games Explosion.sav` remained **0 bytes** after all play,
  and no Thumb `LDR` literal targeting SRAM (`0x0E000000`) was found. Any in-game scores are
  session-only.

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo` (Phase 0/1).
- Python 3 + `capstone` 5.0.7 for literal scans; `arm-none-eabi-objdump -M force-thumb` /
  default ARM for disassembly; REA (Ghidra 12.1.4) `analyze_function` / `read_bytes` /
  `list_procedures` for decompilation.
- mGBA SDL under Xvfb `:317` + openbox; `xdotool` XTEST input; `import -window` for
  screenshots; ImageMagick `montage` for contact sheets; `tesseract` for OCR of tile-rendered
  labels.
- `ss.py` (zlib-decompress the `gbAs` savestate chunk), `gx.py` (input helper),
  `walk_games.py` (automated game launch/walk). All under `/tmp/gamesexplosion/`.

Web content was treated strictly as data; no prompt-injection payload was encountered in the
fetched cheat pages.

## 10. Legal note

No ROM image or copyrighted assets are reproduced here. Only hashes, addresses, algorithms,
and original analysis artifacts are published.
