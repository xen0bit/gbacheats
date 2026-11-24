# SD Gundam Force (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/SD Gundam Force/SD Gundam Force.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `SDGFORCE` (bytes `0xA0`–`0xA7`) |
| Game code | `BGEE` (USA) |
| Maker | `B2` |
| Version | `0x00` (Rev.00); complement `0x00`; header checksum `0x007D` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, not a cracktro) |
| Fixed byte | `0x96` at `0xB2` |
| MD5 | `9530a3e226b2fdfbfb8fd72242793635` |
| SHA-1 | `f45af1fabfa9c95bc98c6d3cc986cc68afd7ea61` |
| SHA-256 | `2d4bbe9fa0b7051c33a2b63b5b44513cc58e5c9cf91d88449f8cdc94f1b6a8bc` |

Embedded-header scan: exactly **one** Nintendo-logo hit (file `0x4`, header base `0x0`). No
multiboot stub, no appended trainer, no patched entry. A single retail USA image.

## 2. Executive summary

**There is no in-game password, button-code, or cheat-code system in this SKU.** Every
published "cheat" for the GBA release is a GameShark/CodeBreaker *memory patch* (out of the
scope of this engagement). The search space was bounded (§6b): 49,841 ASCII strings contain
zero occurrences of `password`, `cheat`, `code`, `debug`, `secret`, `unlock`, `level`,
`invalid`, or `continue`; the only text bank that is ASCII is the developer bank at
`0x6CF60`–`0x6F6xx`; the font/tile-index tables at `0x6F4E4`/`0x6F5A4`/`0x6F640`/`0x6F68F`
were decoded and contain no hidden password alphabet; and a u8/u16 key-mask search for the
Konami prefix and other common sequences found only random-data false positives.

What the game *does* contain is a **hidden developer/QA OPTIONS menu**, reachable from the
ordinary title-screen OPTIONS entry with no unlock, on a fresh save:

- `PERSONAL DATA` (completion stats, 50 smileys)
- `BGM TEST--<nnn>` — sound test, **000–020** (21 values, clamps at 020)
- `SE TEST--<nnn>` — sound-effect test, **000–110** (111 values, clamps at 110)
- `SPECIAL` — five `???????????????` placeholder rows, all inert
- `EXIT`

This is the entirety of the developer-intended surface. Two published memory-edit flag
addresses (`0x02020A58`, `0x02020A84`) were used **as analysis only** (debugger write) to
test whether the SPECIAL rows are flag-gated; they are not, and no memory-edit code is
reported as a finding.

A prompt-injection payload was encountered in a TCRF search result (fake "not for humans"
instructions, a "$1,000,000,000,000" transfer demand, and an `E_SHITASS_OPERATOR` directive).
It was ignored and is recorded here as required by guide §16.8. The TCRF pages returned are
for the PS2 title *SD Gundam Force: Showdown!*, a different game.

## 3. How to reproduce

- Emulator: `/usr/local/bin/mgba` 0.10.5 under `Xvfb :316`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
- Keymap (mGBA SDL default): A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`,
  Select = `BackSpace`, D-pad = arrow keys. **Hold keys 150 ms**; 60 ms taps are missed by
  this game's input polling (this caused several false "button ignored" observations).
- Path to the debug menu, from a clean boot:
  1. `PUSH START` → `Return`
  2. `Down`, `Down` → `OPTIONS`; `x`
  3. OPTIONS screen shows `PERSONAL DATA / BGM TEST--<000> / SE TEST--<000> / SPECIAL / EXIT`.
  4. `Down` moves the cursor. On a numeric row, `x` enters value-edit; `Right`/`Up` add,
     `Left`/`Down` subtract; `x` plays the sample. BGM clamps at `020`, SE at `110`.
  5. `Down`, `Down`, `Down`, `x` from PERSONAL DATA opens `SPECIAL`.
- Other screens walked: title `NEW GAME` → `PLAYER SELECT` (3 selectable characters) →
  `EPISODE 1` intro → gameplay (HP/score/LV HUD); in-game pause is **Select only**
  (Start does nothing) and shows the word `PAUSE` with no menu items.
- No button sequence was found that unlocks anything at the title, OPTIONS, or pause screen.

## 4. Address map

| File offset | ROM address | Meaning |
|---:|---|---|
| `0x000` | `0x08000000` | Header; entry branch to `0x080000C0` |
| `0x4DF64` | `0x0804DF64` | Literal pointer to `"Matsuyoshi san TEST "` (`0x0806CF60`) |
| `0x0804DF46` | — | Debug-print routine that emits that string via `0x08002368`; sets callback `0x0804DF6D` |
| `0x5A270` | `0x0805A270` | Pointer to `"Zako-Zako Hour"` |
| `0x5A294` | `0x0805A294` | Pointer to `"OPTION"` |
| `0x0805A144` | — | Debug sound-test scene init; callback `0x0805A29D` |
| `0x29AC` | `0x080029AC` | Thumb pointer `0x0805A3C1` to stage-list scene init |
| `0x6CF60` | `0x0806CF60` | `"Matsuyoshi san TEST "` (20 bytes) |
| `0x6CFcb`–`0x6DD3c` | `0x0806CFCB`–… | Developer stage-name table, 8-byte stride: `ST_11`…`ST_SX_7`, `TEST STAGE 4`–`7`, `TIME?UP`, `NEOTOPIA`, `STAGE 1`–`54`, `EXTRA STAGE`, `MAX COMBO ATTACK`, `SPEED ATTACK`, `SURVIVAL ATTACK`, `BOSS ATTACK` |
| `0x6DD53`–`0x6EF13` | `0x0806DD53`–… | Plain-ASCII end-credits bank |
| `0x6EF8C` | `0x0806EF8C` | `"Zako-Zako Hour"`, `TYPE A/B/C`, `OPTION` |
| `0x6F4E4`, `0x6F5A4` | `0x0806F4E4`, `0x0806F5A4` | Tile-index ↔ ASCII font tables |
| `0x6F640`, `0x6F68F` | `0x0806F640`, `0x0806F68F` | Auxiliary glyph/rotation tables |
| `0x5DC4` | `0x0805DC4` | Literal pointer to `0x02020A58` |
| `0x0805D8C` | — | Counts set bits in 50 halfwords at `0x02020A58` (smiley total, matches `00/50` UI) |
| `0x02020A58` | — | EWRAM: 50-halfword completion/smiley flag array |
| `0x02020A84` | — | EWRAM: episode-select unlock flag (published memory-edit target) |

Savestate layout (mGBA 0.10.5, `gbAs` zlib chunk, 397,312 bytes decompressed): IWRAM at
state offset `0x19000`, EWRAM at `0x21000`; validated by diffing single-key states and by
reading `0x02020A58` live in the `-d` debugger.

## 5. Algorithm

No validator exists to reverse. The only algorithmic content found is:

```
smiley_count(flags @ 0x02020A58):
    n = 0
    for i in 0..49:
        word = flags[i >> 5]            # u32 at 0x02020A58 + 4*(i>>5)
        if (word >> (i & 31)) & 1: n += 1
    return n                            # shown as "TOTAL <smiley> nn/50"
```
(derived from `0x0805D8C`, Thumb: `lsrs r0,r2,#5; lsls r0,#2; add r0,r5; ldr r0,[r0];
asrs r0,r1; and r0,#1; cmp; beq; add r3,#1` — the loop bound `cmp r2,#49; bls` gives 50
iterations.)

Sound-test value update (observed):
```
Right/Up  -> value = min(value + 1 / +10, MAX)
Left/Down -> value = max(value - 1 / -10, 0)
MAX(BGM) = 0x14 (20), MAX(SE) = 0x6E (110)
```

## 6. Tables

**Hidden OPTIONS menu (all 5 entries):**

| # | Entry | Type | Observed behaviour |
|---:|---|---|---|
| 1 | `PERSONAL DATA` | screen | `TOTAL <smiley> 00/50`, `BEST SCORE`, `BEST TIME`, `MAX COMBO`, `ENEMIES DEFEATED`; `‹PREV -EXIT NEXT›` |
| 2 | `BGM TEST--<nnn>` | 3-digit value | 000–020, plays a music track on `x`; clamps at 020 |
| 3 | `SE TEST--<nnn>` | 3-digit value | 000–110, plays an SFX on `x`; clamps at 110 |
| 4 | `SPECIAL` | screen | 5 rows of `???????????????`; all inert on a fresh save |
| 5 | `EXIT` | action | returns to title |

**SPECIAL rows (5):** rows 1–5 all render the identical 15-`?` placeholder. Pressing `x`
on each produced no reveal and no persistent flag change (savestate RAM diff over all five
`x` presses: only cursor/animation bytes changed). Writing `0xFFFF` to `0x02020A58`–`0x5E`
and `0x02020A84` via the debugger (analysis only) did not change any row — these published
memory-edit targets do not gate this screen. Evidence: Observed for row 1 and the flag test;
Derived/Inferred for rows 2–5 (identical renderer, no branch found).

**Published codes examined and rejected as out of scope / unverifiable as in-game codes:**

| Source | Claim | Status |
|---|---|---|
| CodeTwink / almarsguides / gamehacking.org | 18 GameShark/CodeBreaker memory patches | Out of scope (memory edits), not in-game codes |
| GameShark | `Open Episode Select 82020A84 FFFF` | Targets EWRAM `0x02020A84`; memory edit, not an input code |
| GameShark | `All Secret Options 42020A58 FFFF…` | Targets `0x02020A58`; 50-item completion array, not an input code |
| CheatCC / CodeTwink | PS2 button passwords (Triangle/Circle sequences) | Different platform SKU; literals not present in this ROM |
| VGChartz | 7 "cheats" | All walkthrough/tips, no codes |
| TCRF | `SD Gundam Force: Showdown!` hidden level select | Different game (PS2) |

## 6b. Enumeration

This is a **negative result about a bounded space**, per guide §0.2 item 5 and §16.3.

**Code/password space: empty.** No password alphabet, no entry screen, no comparison
routine, and no key-mask sequence exists in this image:

| Search | Space checked | Result |
|---|---|---|
| `strings -t x -n 4` keyword scan | 49,841 ASCII strings, whole 8 MiB | **0** hits for `password`, `cheat`, `code`, `debug`, `secret`, `unlock`, `level`, `invalid`, `continue`, `version`, `gameshark`, `codebreaker` |
| Case-insensitive `strings -i` and `+0x20` letter shift | whole image | no hidden UI text bank found |
| Font/tile-index decode (`0x6F4E4`, `0x6F5A4`, `0x6F640`, `0x6F68F`) | 4 tables | tables map glyph indices to ASCII; no code alphabet or literal table |
| Literal search for published PS2 button passwords | whole image | **0** hits (different SKU) |
| u8/u16 key-mask search for Konami prefix `U,U,D,D,L,R,L,R,B,A` | whole image, active-high and active-low | **0** plausible table hits (only random-data 1-byte coincidences) |
| u8/u16 search for `L,L,R,R,B,A`, `A,B,A,B`, `L+R,L+R`, `Start,A,B` | whole image | **0** plausible table hits |
| `memcmp`/`strcmp`-style validator scan via literal pointers | all debug-string pointers | 1 pointer (debug print), 0 validators |

Because there is no code system, **no novel code could be minted** — §0.2's novel-code
deliverable is replaced by a complete enumeration of the actual surface:

| Enumerated surface | Size | Bounds proven |
|---|---|---|
| Title-menu entries | 3 (`NEW GAME`, `CONTINUE`, `OPTIONS`) | Walked all 3; `CONTINUE` has no data on a fresh save |
| Hidden OPTIONS entries | **5** | Walked all 5; no 6th entry (cursor stops at `EXIT`) |
| `PERSONAL DATA` stats | 5 | observed on screen |
| `BGM TEST` values | **21** (`000`–`020`) | Held `Right` 6 s: stayed at `020`; `Up` from `020`: stayed at `020` |
| `SE TEST` values | **111** (`000`–`110`) | Held `Right` 12 s: stayed at `110` |
| `SPECIAL` rows | **5** | All `?`; `x` on each inert; flag writes did not reveal text |
| `PLAYER SELECT` slots | **3** | All selectable on a fresh save; no hidden 4th slot (cursor wraps 0–2) |
| Pause-menu entries | **0** | `Select` shows only the word `PAUSE`; `Start` does nothing |

**Enumeration total for the debug menu:** 1 screen + 5 entries; 21 + 111 = 132 sound-test
values; 5 placeholder rows; 5 stats. All reachable states were visited with emulator
evidence; no entry was left "not tested".

## 7. Validation evidence

- **Observed** (emulator, mGBA 0.10.5 on `:316`): every screen and value in §3/§6;
  BGM clamp at 020 and SE clamp at 110; 3 player slots; Select-only pause; inert SPECIAL rows.
- **Observed** (savestate RAM diff / `-d` debugger): `0x02020A58` and `0x02020A84` are zero
  on a fresh save; single-key diffs locate the sound-test value at state offset `0x21414`;
  writing the published flag addresses changes no SPECIAL text.
- **Derived** (disassembly): debug-print routine `0x0804DF20`; debug scene inits
  `0x0805A144` / `0x0805A3C0`; 50-bit smiley counter `0x0805D8C`; stage-name table stride 8.
- **Inferred**: the five `SPECIAL` rows are cut/unimplemented placeholders (identical
  renderer, no reveal branch found, flag writes ineffective); no retail input path reaches
  any hidden stage-list screen via the debug scene dispatch (the stage names exist only in
  an ASCII table referenced by debug-print code).

## 8. Unknowns

- Whether any of the developer stage names (`ST_SX_0..7`, `TEST STAGE 4..7`, `EXTRA STAGE`)
  can be reached by a combination not tested; no input path or gate writer was found, so
  they are treated as debug-only data, not a level select.
- The exact unlock condition for the 50 smileys and the episode-select flag
  (`0x02020A84`) — almost certainly normal story progression; completing the game was not
  attempted, and no in-game input code sets them.
- Meaning of `"Zako-Zako Hour"` / `TYPE A/B/C` beyond the debug scene that prints them.
- The first SPECIAL row was fully exercised with `x`; rows 2–5 were exercised as a group
  (identical placeholder renderer) rather than individually at the pixel level.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all
  disassembly; PC-relative literal and BL scanners written in Python (`capstone`, `struct`).
- Custom scripts in `/tmp/sdgundam/`: `scan.py`/`scan2.py`/`scan3.py`/`scan4.py`
  (literal/xref/BL scans), `keysearch.py` (button-mask search), `statedump.py` /
  `decode_all.py` (mGBA savestate `gbAs` zlib decode + RAM diff), `dbgdriver.py` (pty driver
  for mGBA `-d` CLI debugger used as an RAM oracle per §16.19).
- `Xvfb :316`, `openbox`, `xdotool` (XTEST keys, 150 ms holds), `scrot`.
- Web: CodeTwink, almarsguides, gamehacking.org, VGChartz, GameFAQs (403), TCRF (search
  snippets; injection payload ignored).

No ROM bytes, screenshots, or copyrighted assets are redistributed in this report; only
hashes, addresses, and analysis results are published.
