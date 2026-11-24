# Urban Yeti! (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Urban Yeti!.gba` (4,194,304 bytes / 0x400000) |
| Header title | `URBANYETI` (0x00A0) |
| Game code | `AYIE` (0x00AC) |
| Maker | `5M` (0x00B0) — Telegames |
| Version / complement / checksum | `0x00` / `0xF4` / `0x0000` (checksum 0 is the usual rebuilt-header artifact; entry word `0xEA00002E` is the stock crt0 branch, so this is a retail image with a repaired header, not a cracktro) |
| MD5 | `6f4148477f8d456c00c4099e990c2fb0` |
| SHA-1 | `79b72b0b290490019ed26a1ae6c481ac5c9f8893` |
| SHA-256 | `78793c5cbf1d620977deadb263768548a5b17e0337f648c810489f05f0541238` |

Engine strings confirm the build: `Factor 5`, `MusyX audio tools licensed by`, `Cave Barn Studios LLC`, `Tony Gold`.

## 2. Executive summary

Urban Yeti! has a real, developer-intended password system with **exactly 29 accepted inputs**: two hard-coded special codes and 27 records in an on-cartridge table. There is no checksum, no bit-packing, no button sequence and no algorithmic generator: the validator is a plain, case-sensitive, NUL-terminated `strcmp` against fixed strings. The input surface is eight uppercase letters `A`–`Z` (`0x41`–`0x5A`), so the representable space is `26^8 = 208,827,064,576` strings, of which 29 are accepted.

Published lists (3rd party cheat index-derived mirrors, 3rd party cheat indexes) document `TONYGOLD`, `BSWSBSWS` and the 26 level passwords `BUZZWORD` … `PROVIDER`. **All 28 of those were verified byte-for-byte in the ROM.** Three further published claims — `NTTTTT`, `MFKRPH` and the six-letter set `PBBQBB`/`QBCQBB`/…/`MTTQBB` — are **absent from this image** and are reported as unverified/wrong-edition (§16.7/§16.11).

The ROM's own table contains one record that **no published list mentions**: `PASSWORD` (record 0, category 0, index 1). It is the missing third member of the first category (published lists begin at `BUZZWORD`, category 0 index 2), i.e. an unadvertised difficulty/variant of the first area. This is the generated, novel code.

Dynamic confirmation was obtained for the password *output* side: the in-game GAME OVER screen prints the table-derived password `FOREWORD` live (02:xx timer, CREDITS: 1), proving the same table is consumed by the shipping engine. The retail entry UI was **not** reached after walking every reachable screen (title attract, Select menu, NEW GAME, in-game pause, GAME OVER with CONTINUE/STATS/QUIT); see §8 for the bounded negative and why the entry path is reported as gated/unconfirmed rather than absent. The validator itself was fully reversed statically and reimplemented offline; all 29 accept and representative rejects agree with the disassembly.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `-3` scaling. A renamed copy (`uy_gba`) was used because other agents' `pkill -x mgba` repeatedly killed the default-named process; this is a harness workaround, not a game modification.
* Keymap (mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 100–150 ms.
* Screen walk performed:
  1. Boot → legal screen → `Return` → Telegames splash → CAVE+BARN splash → title attract (loops through all seven "legend of the Yeti" narration scenes).
  2. `BackSpace` on the title reveals a `NEW GAME / CONTINUE` menu at the lower right.
  3. `Return` on the title (no menu) starts a game: intro cutscene (`x` to advance) → city gameplay with HUD (clock, +100 health).
  4. In gameplay `Return` opens `CONTINUE / QUIT`. `QUIT` → studio splash → title.
  5. `Select`+`Down`+`A` from gameplay produced a GAME OVER screen: `CREDITS: 1`, `CONTINUE`, `STATS`, `QUIT`, and the generated password `FOREWORD` rendered at bottom right. `CONTINUE` resumed play with one credit spent.
* Static tools: `strings -t x`, literal/`u32` pointer scans, Thumb PC-relative literal scanner, BL scanner, `arm-none-eabi-objdump -M force-thumb`, Capstone. Work files and screenshots were in `/tmp/urbanyeti/`.

## 4. Address map

All values are ROM addresses (`0x08000000 + file offset`). RAM is IWRAM/EWRAM.

| Address | Meaning |
|---|---|
| `0x08040000`–`0x080406A0` | Password/menu scene function (`0x803FF28` is its entry). Draws the menu, the 8-letter entry field, and performs validation. |
| `0x08040288` | Literal → `0x0809483C` `"PASSWORD"` (drawn at y=0x52) |
| `0x0804047C` | Literal → `0x0809484C` `"TONYGOLD"` |
| `0x080404CC` | Literal → `0x08094858` `"BSWSBSWS"` |
| `0x080406A0` | Literal → `0x08094864` `"INVALID"` |
| `0x08040528` | Literal → `0x03005C90` (input buffer pointer) |
| `0x0804052C` | Literal → `0x081FD0D4` (password record table base) |
| `0x08040530` | Literal → `0x03005BA0` (result state struct) |
| `0x08040534` | Jump table, 9 category handlers: `0x804055C, 0x80405A0, 0x80405CC, 0x80405D2, 0x80405D8, 0x80405DE, 0x8040562, 0x80405AC, 0x80405E4` |
| `0x080540…` n/a | `0x08054680` = optimized `strcmp` (word-at-a-time compare, NUL terminated, case sensitive) used by all comparisons |
| `0x08094830/3C/46/4C/58/64` | ASCII strings `NEW GAME`, `PASSWORD`, `_`, `TONYGOLD`, `BSWSBSWS`, `INVALID` |
| `0x081FD0CC` | `u32 0x1F` (31 — nominal table count; only 27 records are actually iterated, see §8) |
| `0x081FD0D4` | 27 × 20-byte password records (see §6) |
| `0x081FD5B8`–`0x081FD820` | Secret-menu item pointer table (level/difficulty/mode/sound-test labels: `Hard`, `Medium`, `Easy`, `View`, `Play`, `Play Music`, `Play Sounds`, `Credits`, `Level`, `Mode`, `Difficulty`, minigame names) |
| `0x03005C90` | 8-byte input buffer (plus NUL) |
| `0x03005BA0+0x4D` | result category byte (0–8) |
| `0x03005BA0+0x4F/+0x50` | result index/level bytes |
| `0x03000068` | scene/menu cursor state (0 = NEW GAME action, 1 = CONTINUE/password action, other = draw menu) |

## 5. Algorithm

The validator is `0x803FF28`. Its relevant control flow:

```
input = (char*)0x03005C90                 # 8 bytes + NUL
keys  = *KEYSTATE (active-high in this engine; A/Start = mask 0x09)

# entry UI (only when the password scene is active)
Up/Down   -> cursor 0..7
Left/Right-> current char = (char + 1) & 0xFF; if > 'Z' -> 'A'
             decrement: if < 'A' -> 'Z'
             if current == 0x20 (' ') -> 'A' on increment
A/Start   -> submit

submit:
  if (keys & 0x09) == 0: return unchanged
  if strcmp(input, "TONYGOLD") == 0:      # 0x08040438
      install secret-menu handler table (level select, sound test,
      difficulty, Mode Play/View); call 0x08041434; result = 1; return
  if strcmp(input, "BSWSBSWS") == 0:      # 0x080404B0
      call 0x08030620(2), 0x0803FDFC, 0x080305E8(2);
      result = 1; return                  # "Black Screen White Screen"
  for i = 0 .. 26:                        # 0x080404D4 .. 0x0804061E
      rec = (Record*)0x081FD0D4 + i       # stride 20
      if strcmp(input, rec->text) == 0:
          state[0x4D] = rec->category     # u32 at rec+0x0C
          state[0x50] = rec->index        # u32 at rec+0x10
          state[0x4C] = state[0x4F] = 0
          if state[0x4D] <= 8:
              jump table[state[0x4D]]()   # start level / minigame
          result = 1; return
  else:
      play sound 0x3B; show INVALID; result = 0
```

`strcmp` at `0x08054680` is the standard aligned-word implementation: it checks 4-byte alignment, compares whole words, falls back to bytes, and stops at NUL. There is **no case folding, no wildcard, no length branch, no checksum and no transformation** of the input buffer. Consequently the accepted set is exactly the union of the two literals and the 27 table strings.

Record layout (little-endian, 20 bytes):

```
+0x00  char text[8]      NUL-terminated, uppercase A-Z
+0x08  u32  reserved      always 0 in all 27 records
+0x0C  u32  category      0..8  (dispatch index)
+0x10  u32  index         1..3  (difficulty/level slot)
```

## 6. Tables

### 6.1 Special codes

| Code | Effect | Evidence |
|---|---|---|
| `TONYGOLD` | Secret menu: level select, sound test, difficulty, Mode Play/View (View follows a seagull; quitting returns to the secret menu) | Derived from `0x8040432`–`0x8040474`; matches 3rd party cheat indexes |
| `BSWSBSWS` | "Black Screen White Screen" memory game / strange-graphics mode | Derived from `0x80404AC`–`0x80404CA`; matches 3rd party cheat indexes |

### 6.2 Full 27-record table at `0x081FD0D4`

Published level numbers are shown for comparison (3rd party cheat indexes). `cat`/`idx` are the ROM's own fields.

| # | Code | cat | idx | Published level |
|---:|---|:---:|:---:|---:|
| **0** | **`PASSWORD`** | **0** | **1** | **— (UNPUBLISHED / novel)** |
| 1 | BUZZWORD | 0 | 2 | 1 |
| 2 | FOREWORD | 0 | 3 | 2 |
| 3 | COOKBOOK | 3 | 1 | 3 |
| 4 | FEEDBAGS | 3 | 2 | 4 |
| 5 | HAMSTEAK | 3 | 3 | 5 |
| 6 | DAYBREAK | 7 | 1 | 6 |
| 7 | SUNLIGHT | 7 | 2 | 7 |
| 8 | NITETIME | 7 | 3 | 8 |
| 9 | EASTSIDE | 1 | 1 | 9 |
| 10 | BEATDOWN | 1 | 2 | 10 |
| 11 | VENGEFUL | 1 | 3 | 11 |
| 12 | FRISBEES | 4 | 1 | 12 |
| 13 | ICESKATE | 4 | 2 | 13 |
| 14 | PINGPONG | 4 | 3 | 14 |
| 15 | DOWNTOWN | 8 | 1 | 15 |
| 16 | CITYMAPS | 8 | 2 | 16 |
| 17 | DUMPSTER | 8 | 3 | 17 |
| 18 | WATERWAY | 5 | 1 | 18 |
| 19 | TIRETUBE | 5 | 2 | 19 |
| 20 | YETIRAFT | 5 | 3 | 20 |
| 21 | SUBURBIA | 2 | 1 | 21 |
| 22 | HOUSETOP | 2 | 2 | 22 |
| 23 | CITIZENS | 2 | 3 | 23 |
| 24 | CHICKENS | 6 | 1 | 24 |
| 25 | SONGBIRD | 6 | 2 | 25 |
| 26 | PROVIDER | 6 | 3 | 26 |

The `cat` field is the handler selector; `idx` is an unadvertised 1/2/3 slot (publishers flatten this to a 1–26 level number). Categories 0,1,2,3,4,5,6,7,8 each have exactly three words except category 6 (`CHICKENS/SONGBIRD/PROVIDER`) whose handler differs.

### 6.3 Published codes not present in this ROM

`NTTTTT`, `MFKRPH`, `PBBQBB`, `QBCQBB`, `SBFQBB`, `DBKQBB`, `NBTQBB`, `PCTQBB`, `RFTQBB`, `CKTQBB`, `MTTQBB` — literal search over all 4 MiB returns zero hits in each case (ASCII, `+0x20`, UTF-16LE/BE checked for the two 6-letter "special" claims). Treat as unverified/wrong-edition.

## 6b. Enumeration

**Space definition.** Entry UI accepts exactly eight symbols from the 26-letter alphabet `ABCDEFGHIJKLMNOPQRSTUVWXYZ`; UI code maps `0x20→'A'`, `'>'Z'→'A'`, `'<'A'→'Z'`. No digits, no punctuation, no space, no lowercase can be produced by the retail keyboard. `26^8 = 208,827,064,576` distinct input strings.

**Validator model (offline reimplementation).** `accept(s) = (s == "TONYGOLD") or (s == "BSWSBSWS") or (s in table[0..26])`, with byte-exact strcmp semantics. This model agrees with every instruction in `0x8040428`–`0x8040626`.

**Complete accepted set: 29 strings.**

* 2 special literals: `TONYGOLD`, `BSWSBSWS`.
* 27 table records: `PASSWORD`, `BUZZWORD`, `FOREWORD`, `COOKBOOK`, `FEEDBAGS`, `HAMSTEAK`, `DAYBREAK`, `SUNLIGHT`, `NITETIME`, `EASTSIDE`, `BEATDOWN`, `VENGEFUL`, `FRISBEES`, `ICESKATE`, `PINGPONG`, `DOWNTOWN`, `CITYMAPS`, `DUMPSTER`, `WATERWAY`, `TIRETUBE`, `YETIRAFT`, `SUBURBIA`, `HOUSETOP`, `CITIZENS`, `CHICKENS`, `SONGBIRD`, `PROVIDER`.

**Novel code (absent from every published list checked):** `PASSWORD` (record 0, `cat=0`, `idx=1`). Every published level list begins at `BUZZWORD` (published level 1); the ROM proves a third, unadvertised member of category 0 exists. It exercises a difficulty/slot combination the public lists omit. Its exact bytes are at `0x081FD0D4` and it is compared by the same `strcmp` at `0x08054680` as the published codes.

**Bounds proven by rejection.** The following are *not* accepted by the model and are rejected by the ROM's byte-exact comparison path (the `0x8040620` failure branch → sound `0x3B` → `INVALID`):

* `TONYGOLX` — one-character mutation of a special code: no literal match, and the table loop of 27 records exhausts (`cmp r5,#26; bgt` at `0x804061A`) → reject.
* `password` / `Password` — lowercase/mixed case: `strcmp` is case-sensitive and every stored string is uppercase → reject.
* `PASSWOR` (7 chars) and `PASSWORDX` (9 chars) — length mismatch against the 8-byte fixed field → reject; the edit loop is hard-bounded to indices 0..7 (`cmp r3,#7; bgt` at `0x8040324`).
* `NTTTTT`, `MFKRPH` — published but absent from the image (ASCII scan: 0 hits) → reject.
* Reserved field: `rec+0x08` is zero in all 27 records and is never read by the validator, so it cannot encode an alias.

**Closed-set proof (counts).** The validator contains exactly two literal `strcmp` calls (`0x8040438`, `0x80404B0`) plus one loop whose bound is `i <= 26` over a 20-byte-stride table. Pointer scans for the two literals and the table base each returned exactly one reference site. A scan for all 32-bit pointers into the string bank `0x08094000–0x08095000` found exactly four validator-relevant entries (`0x8040138` pad, `0x8040144` NEW GAME, `0x804014C` CONTINUE, `0x8040288` PASSWORD, `0x804047C` TONYGOLD, `0x80404CC` BSWSBSWS, `0x80406A0` INVALID). There is no second password format, no generator, and no comparison outside this set. The nominal count `0x1F` at `0x081FD0CC` is 31; the loop bound of 27 is authoritative, and bytes after record 26 (`0x081FD2F0` onward) are code pointers, not records — so 27, not 31, is the real table size.

## 7. Validation evidence

* **Derived (disassembly).** Validator address, table base, record stride, loop bound, handler dispatch, input alphabet, input buffer address, `strcmp` identity — all read directly from Thumb code at `0x0803FF28`–`0x080546D8` and verified against raw bytes with `struct.unpack_from`.
* **Observed (emulator).** Boot sequence, title attract, Select menu (`NEW GAME / CONTINUE`), NEW GAME cutscene and gameplay HUD, in-game pause (`CONTINUE / QUIT`), GAME OVER screen with `CREDITS: 1` and live-generated password `FOREWORD`, CONTINUE spending a credit. Screenshots saved under `/tmp/urbanyeti/` (`full_c.png`, `menu_hi_c.png`, `end1_c.png`, `eatlas.png`, …).
* **Observed (recon).** All 28 published code strings located verbatim; the 11 unverified published strings located zero times.
* **Inferred (not observed).** The *visual* result of entering `PASSWORD`, `TONYGOLD` or `BSWSBSWS` on the entry screen: the handlers are identified and their calls listed, but the entry screen itself was not reached in the retail build (§8). Effects are labelled inferred, not confirmed.
* **No prompt-injection content was found or followed** in ROM strings or fetched cheat pages; all fetched text was treated as data.

## 8. Unknowns

* **Retail entry path not reached.** Screens walked and inputs tried: title attract (all narration phases, 60 s observation), title Select menu with A/Start/B/L/R/Up/Down, NEW GAME start, in-game pause (CONTINUE/QUIT), GAME OVER menu (CONTINUE/STATS/QUIT) with all three cursor positions and A. None produced the 8-letter entry UI (`0x0809…` strings `PASSWORD` / `_` / `INVALID` are present and the entry code exists, but the scene that draws it was not entered). This is a **gated-feature / dead-entry uncertainty**, not a claim that no password system exists — the table, validator and result-state writes prove the system is real and shipped. The likely gate is the `0x03000068` scene cursor / the `[struct+1]==0` test at `0x8040F10`; forcing it with an analysis build (patched copy of the ROM) did not reach the UI either, so the exact retail trigger remains open.
* `cat`/`idx` field names are inferred from the dispatch structure and published level numbers; the game never labels them directly on screen.
* Whether the 31st record implied by `0x081FD0CC` ever existed in an earlier build is unknown; the shipping loop bound is 27.
* Save-medium question: a 0-byte `.sav` is created by mGBA, consistent with passwords replacing a battery save; no EEPROM/Flash save format was reversed.
* `STATS` on the GAME OVER screen was not opened (no visible effect on the tested path).

## 9. Tooling

* `strings -t x -n 3/4`, `grep -abo`, Python `struct` scans for `u32` pointers, Thumb PC-relative literal scanner (`ldrscan.py`, `ldrscan2.py`), BL scanner.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for `0x08040000–0x08040800`, `0x08054000–0x08054700`, `0x0803FF00–0x08041000`.
* Capstone-based literal scanner (per guide §5.2).
* mGBA 0.10.5 under Xvfb `:317` + openbox, `xdotool` XTEST key driver (`keys.py`, `combo.py`), `scrot` + Pillow cropping (full 720×480 viewport at 3×).
* mGBA `-d` pty debugger and `-g` GDB stub were attempted; other agents' stubs on port 2345 and their `pkill -x mgba` made these unreliable, so the final analysis is static-first with emulator screenshots for the screen walk.
* No ROM or copyrighted asset is redistributed; this report contains addresses, hashes and findings only.
