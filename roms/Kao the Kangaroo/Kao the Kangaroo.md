# Kao the Kangaroo (GBA) — Reverse Engineering Report

## 1. Target identity

| Item | Value |
|---|---|
| File | `roms/Kao the Kangaroo/Kao the Kangaroo.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `KAOTHEKANGAR` |
| Game code / maker | `AKKE` / `60` (Europe), version `0x00` |
| Entry word | `0xEA00002E` (stock GBA branch to 0x080000C0) |
| Complement / checksum | stored `0x5F` / `0x0000` (expected complement `0x77`) — header was rebuilt/edited; no functional patch found |
| MD5 | `c6926d0bbbdbed3372e6fc01c81cd52b` |
| SHA-1 | `772d323145cb7707cb8792bdfd5c7ef5e1e27c46` |
| SHA-256 | `d3797db287c149d587e0b8e590b7c4a8d58e2b204b91af4873474ccead8b2d2d` |

Phase 0: one Nintendo-logo hit only (file offset 0), so this is a single retail image, not a multi-game pack. No scene cracktro or trainer strings (`CRC BANDIT`, `MODE7`, `SUNHORS`, `TRAINER`, GameShark/CodeBreaker banners) anywhere in the image. File offset = ROM address − 0x08000000 throughout this report.

## 2. Executive summary

The GBA version has a **developer-intended 5-symbol picture password system** on the main menu (`PASSWORD`), plus one undocumented "CHEAT CODE" password that unlocks every level. There are no GameShark-style codes in scope and no button-code system on this SKU (the widely published L+R+direction codes are for the **Dreamcast/PC** versions and do not apply).

The password alphabet is 16 icons; each of the 5 slots holds one icon, so the raw input space is 16^5 = 1,048,576. The validator at **`0x0801CBF0`** accepts exactly:

* 1 exact special sequence → "CHEAT CODE" and all 29 level-unlock flags set;
* 25 hard-coded 3-symbol prefixes × 3 allowed 4th symbols × 6 allowed 5th symbols = 450 level passwords.

= **451 accepted inputs**. The 4th and 5th symbols are only checksum/range fields: any value in {face, glove, mushroom} for symbol 4 and {face…cat} for symbol 5 works, which is why every published list uses `Boxing Glove, Kao's Face` there while the ROM's own table stores `face, face`.

Published GameFAQs codes were fetched from an archived snapshot and verified: all 21 published 3-symbol prefixes except one (a likely published transposition for *Hypnodjin*) exist in the ROM table; five were entered in the emulator successfully. Two inputs absent from every published list were minted and confirmed in-game (§6b). `DEBUG MODE` is a **dead string** — its pointer-table entry has no code xref.

## 3. How to reproduce

Emulator: mGBA (SDL build), Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, window focused with `xdotool windowfocus`. Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Holds of 100–150 ms; shorter taps are dropped by this game's input polling.

Menu path: boot → Start (Titus splash) → Start (language list) → A on ENGLISH → main menu:

```
NEW GAME / PASSWORD / OPTIONS / TUTORIAL / CREDITS
```

* `PASSWORD` → five icon slots; **Left/Right** select slot, **Up/Down** change icon, **Start** (or A) submits. A wrong code shows `WRONG PASSWORD`.
* Accepted level code → world map with a level banner (e.g. `HUNTER`, `ISLAND SHORES`, `CURSED JUNGLE`); B/A on the map enters the level.
* Savestates: `Shift+F1` saved the all-faces password screen; `F1` reloaded it before every code test (this is the reproducible experiment loop).

Screens walked and verified: Nintendo boot, Titus splash, language select (6 languages: EN, FR, DE, ES, IT, NL), main menu, difficulty select (`EASY/NORMAL/HARD`, used by both NEW GAME and OPTIONS), password screen, tutorial (playable level), credits (`PUBLISHED BY TITUS`), world maps, in-game levels, boss encounter, `WRONG PASSWORD`, `CHEAT CODE`. No pause overlay was produced by Start, Select or L+R in gameplay; no debug screen could be reached.

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x08001C54`–`0x08001C60` | code | initializes the 5 display icons at `0x03001828` to `0x17` (face) |
| `0x0801B23C`, `0x0801B828`, `0x0801BFE8`, `0x0801C846` | code | language-indexed string draws using table base `0x080D230C` |
| `0x0801C188` | code | password-screen input handler: `0x10`/`0x20` = slot ±1 (clamped 0…4), `0x40`/`0x80` = icon −/+ |
| `0x0801C25C` / `0x0801C2B0` | code | icon decrement / increment; bounds `cmp #23` / `cmp #38` prove 16 icons |
| `0x0801BD0C` | code | redraws the five slots from `0x03001828` |
| `0x0801CBF0` | code | **password validator** (called from `0x0801B59A`) |
| `0x0801CC00`–`0x0801CC5C` | code | special-code comparison against `[29,32,38,25,37]` → `CHEAT CODE` |
| `0x0801CCF4`–`0x0801CDAA` | code | 25-entry table search + 4th/5th range checks |
| `0x0801CD86` | code | draws `WRONG PASSWORD` on rejection |
| `0x0801C6CC` / `0x0801C6FC` | code | cheat-code effect: plays sound 18, then unlock-all |
| `0x0801BF2C` | code | generic text draw `(string_ptr, x, y)` |
| `0x080D2088` | ROM table | 25 records × 5 bytes: accepted 3-symbol prefixes (bytes 0–15) |
| `0x080D2300`…`0x080D23FC` | ROM table | string-pointer table (6 languages + menu labels + level names) |
| `0x080234C4`…`0x080238FC` | ROM text | strings terminated by `0x40` (`@`), not NUL |
| `0x03001828` | RAM | 5 displayed icon bytes, internal values 23…38 |
| `0x03003580` | RAM | index array `[0,1,2,3,4]` used by the validator |
| `0x03003770 + 212*i` | RAM | slot structs, i=0…4; halfword at +0 = current icon, halfword at +8 = X coord (23+48i) |
| `0x030024B0` | RAM | 29 level-unlock bytes (0 = locked, 1 = unlocked) |
| `0x030036B0` | RAM | language index used for string lookup |

## 5. Algorithm

```
# validator at 0x0801CBF0 — no arguments; reads globals
icons = [ halfword(0x03003770 + 212*i) for i in 0..4 ]   # each 23..38

if icons == [29, 32, 38, 25, 37]:
    draw("CHEAT CODE")            # 0x080D2340
    unlock_all()                  # 0x0801C6FC -> 0x030024B0[1..28] = 1
    return

found = False
for i in 0..24:
    rec = ROM[0x080D2088 + 5*i : +5]
    if (icons[0] == rec[0]+23 and
        icons[1] == rec[1]+23 and
        icons[2] == rec[2]+23 and
        icons[3]-23 <= 2 and       # symbol 4 in {face, glove, mushroom}
        icons[4]-23 <= 5):         # symbol 5 in {face, glove, mushroom, pine, fish, cat}
        found = True
        set_level_flags(i)
        break
if not found:
    draw("WRONG PASSWORD")        # 0x080D2324
```

Notes: subtraction is the Thumb `subs`/`cmp` pair at `0x0801CD60` and `0x0801CD70`, so an out-of-range low value wraps unsigned and fails. The comparison against `rec[j]+23` is why the on-screen Kao-face (internal 0x17) is the zero symbol of the table. The table is scanned newest-first in the sense that the match index, not the table order, selects the level flags. Accepting a code never writes to SRAM; all state is IWRAM.

## 6. Tables

### 6.1 Icon alphabet (stored byte → icon)

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|----|----|----|----|----|----|
| Kao's Face | Boxing Glove | Mushroom | Evergreen (pine) | Fish | Owl (cat head) | Butterfly | Bird | Key | Frog | Lamp | Palm Tree | Heart | Coin | Flag | Bomb |

Internal icon value = stored + 23. Enumerated visually with a contact sheet and bounded in code (`cmp #23`, `cmp #38`).

### 6.2 Accepted prefix table (0x080D2088, first 3 symbols; 4th/5th are range checks)

| # | Bytes | Prefix | # | Bytes | Prefix |
|---|---|---|---|---|---|
| 0 | `00 01 02` | face, glove, mushroom | 13 | `0d 0e 0f` | coin, flag, bomb |
| 1 | `01 02 03` | glove, mushroom, pine | 14 | `0e 0f 00` | flag, bomb, face |
| 2 | `02 03 04` | mushroom, pine, fish | 15 | `0f 00 01` | bomb, face, glove |
| 3 | `03 04 05` | pine, fish, owl | 16 | `0f 0e 0d` | bomb, flag, coin |
| 4 | `04 05 06` | fish, owl, butterfly | 17 | `0e 0d 0c` | flag, coin, heart |
| 5 | `05 06 07` | owl, butterfly, bird | 18 | `0d 0c 0b` | coin, heart, palm |
| 6 | `06 07 08` | butterfly, bird, key | 19 | `0c 0b 0a` | heart, palm, lamp |
| 7 | `07 08 09` | bird, key, frog | 20 | `0b 0a 09` | palm, lamp, frog |
| 8 | `08 08 00` | key, key, face | 21 | `0a 09 08` | lamp, frog, key |
| 9 | `09 09 00` | frog, frog, face | 22 | `09 08 07` | frog, key, bird |
| 10 | `0a 0b 0c` | lamp, palm, heart | 23 | `08 07 06` | key, bird, butterfly |
| 11 | `0b 0c 0d` | palm, heart, coin | 24 | `07 06 05` | bird, butterfly, owl |
| 12 | `0c 0d 0e` | heart, coin, flag | | | |

### 6.3 Published codes verified

Archived GameFAQs (21 codes, 2022-02-03 snapshot) lists 3-symbol prefixes that are all present in the table above. Codes actually entered and accepted in mGBA:

| Published effect | Symbols entered | Observed map banner |
|---|---|---|
| All Levels / Hunter | palm, lamp, frog, glove, face | HUNTER |
| Island Shores | coin, heart, palm, glove, face | ISLAND SHORES |
| Lightning Speed | palm, heart, coin, glove, face | LIGHTNING SPEED |
| Ancient Ruins | flag, bomb, face, glove, face | ANCIENT RUINS |
| Mythical Caves | mushroom, pine, fish, glove, face | MYTHICAL CAVES |

`All Levels` and `Hunter` share one password; the observed effect is a single level (HUNTER), and the RAM unlock bytes after a single-level password contain exactly one set bit. The genuine all-levels unlock is the CHEAT CODE password below. Published *Hypnodjin* is listed as `Flag, Bomb, Coin`, but no such prefix exists in the ROM table; entry 16 is `Bomb, Flag, Coin` (`0f 0e 0d`) — likely a published transcription transposition (not resolved in the emulator).

No prompt-injection content was encountered in the fetched pages; all fetched text was treated as data.

## 6b. Enumeration

**Space definition.** 5 positions × 16 icons = 16^5 = **1,048,576** raw inputs. Accepted set = 1 special + 25 prefixes × 3 (symbol 4) × 6 (symbol 5) = **451** values (0.043 %). The validator model above is precise enough to decide accept/reject offline; it agrees with every in-game test below.

**Novel code 1 — unpublished all-levels cheat.** Symbols (stored values):
`Butterfly(6), Frog(9), Bomb(15), Mushroom(2), Flag(14)` → internal icons `[29,32,38,25,37]`.
Not present in GameFAQs, IGN, GameRevolution, TCRF or any other published GBA list. Entered on the real password screen: `CHEAT CODE` is drawn, then the world map shows all levels (e.g. `CURSED JUNGLE` with multiple level markers). RAM proof: baseline `0x030024B0` = `01 00 00 …` (only byte 0 set); after this code = `01 01 01 … 01` — **29 consecutive bytes set to 1** (savestate `gbAs` chunk, IWRAM map offset `0x19000 + 0x24B0`).

**Novel code 2 — unpublished level password.** Symbols:
`Kao's Face(0), Boxing Glove(1), Mushroom(2), Boxing Glove(1), Kao's Face(0)` → table entry 0 prefix `00 01 02`, which no published list contains. Entered on the real screen: accepted, world map banner `CURSED JUNGLE`; RAM `0x030024B0` becomes `01 00 00 …` (one level flag), proving single-level rather than all-levels behavior. A second unpublished prefix (`Mushroom, Pine, Fish, …`) mapped to `MYTHICAL CAVES`, but that prefix *is* published, so it is not claimed as novel.

**Bounds proven by rejection.**
* `palm, lamp, frog, bomb, face` (`0b 0a 09 0f 00`): correct 3-symbol prefix but symbol 4 = 15 > 2 → **`WRONG PASSWORD`**.
* `face, face, face, face, face`: no table prefix → **`WRONG PASSWORD`**.
* `palm, lamp, frog, face, face` and published `palm, lamp, frog, glove, face` are **both accepted** with the same HUNTER result: symbols 4 and 5 are aliases within the allowed ranges (§16.4b). These are not distinct codes.

**Special-path bound.** The special CHEAT CODE requires all five exact values; changing any one (e.g. `butterfly, frog, bomb, mushroom, face`) falls through to the table search and is rejected, because its prefix is not in the table.

## 7. Validation evidence

* **Observed (emulator/screenshot):** every screen listed in §3; all six accepted codes and both rejection cases; `CHEAT CODE` and `WRONG PASSWORD` messages; map banners; all-levels map with multiple markers.
* **Observed (RAM):** display array `0x03001828` changing from `17 17 17 17 17` to `17 17 18 17 17` when slot 3 was switched face→glove; baseline vs cheat-code unlock bytes at `0x030024B0` (1 byte set vs 29 bytes set); novel-code unlock byte (1 byte set). Savestate `gbAs` chunks were zlib-decompressed and diffed per §16.13.
* **Derived (disassembly):** icon bounds and 16-symbol alphabet (`0x0801C25C`/`0x0801C2B0`); table base and 5-byte stride (`0x0801CBD4`, `0x0801CDAC`); exact special constants, 25-entry loop and range checks (`0x0801CBF0`); unlock-all writes (`0x0801C6FC`); string-pointer table and `0x40` terminator.
* **Inferred:** mapping of the 25 match indices to specific level names beyond the ones actually seen; exact meaning of symbols 4 and 5 (they behave as a loose two-symbol checksum/range field, not as content). The `DEBUG MODE` string at `0x08023580` is labelled dead code because its pointer-table slot `0x080D2344` has no literal xref anywhere in the 4 MiB image, unlike `CHEAT CODE` (`0x080D2340`, used at `0x0801CC50`) and `WRONG PASSWORD` (`0x080D2324`, used at `0x0801CD86`).
* **Negative results bounded:** keyword strings for password/cheat/code/debug/secret/unlock/level were searched and classified; the only gameplay code surface is the one screen and one validator above. Text was not a problem here (this game uses real ASCII-with-`@` text); however the password *icons* have no text labels at all, so the 16-icon alphabet was enumerated visually and then confirmed by the `cmp #23`/`cmp #38` code bounds. No SRAM/button-code surface was found; DC/PC L+R codes were tested on the GBA map/gameplay without effect and are not applicable to this SKU.

## 8. Unknowns

* Whether a second, unreachable debug screen was intended: `DEBUG MODE`, `X=`, `Y=` are present as strings but no code references them. Treated as dead code, not an undiscovered menu.
* The published *Hypnodjin* prefix discrepancy (transposed `Flag`/`Bomb`) was not re-entered in the emulator.
* Exact per-index → level-name mapping for all 25 table entries; six were observed directly.
* Header complement mismatch (`0x5F` vs `0x77`) is recorded as a rebuilt-header artifact; no behavioral difference was found.

## 9. Tooling

`strings -t x`, `xxd`, `grep -abo`, `arm-none-eabi-objdump -M force-thumb`, Capstone (literal/BL scans), Python 3 (savestate `gbAs` zlib diff, table decode), mGBA SDL with `-3`, Xvfb `:316` + openbox, xdotool, ImageMagick `convert`/`montage`, tesseract (attempted OCR, unreliable on the stylized font). Analysis scripts are in `/tmp/opencode/kao/` (`phase0.py`, `textbank.py`, `strtab.py`, `findcode.py`, `blscan.py`, `ssdiff.py`, `dumptab.py`, `setpw.py`, `batchtest.py`, `novelfinal.py`, `ram_pause.py`).

No ROM or copyrighted assets are redistributed by this report; only hashes, addresses, algorithms and the author-generated code strings are published.
