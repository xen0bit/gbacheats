# Tomb Raider: The Prophecy (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tomb Raider: The Prophecy.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `TOMB RAIDER` (12-byte field, 0xA0) |
| Game code / maker | `AL9E` / `41` (full code `AL9E41`) |
| Software version | `0x00` |
| Entry branch | `0xEA00002E` (stock — no cracktro observed) |
| Complement / checksum | `0xD8` / `0x0000` (non-standard complement: sum 0xA0..0xBC = `0x0F`, expected complement `0xF1`; header likely patched by the release group. Logo and entry are intact and the ROM boots straight to the language screen.) |
| MD5 | `ba38712ad91c6c0287298d4c53ad48b1` |
| SHA-1 | `25d1c4c412ada421b88a88dba89a0ffd23f6f75d` |
| SHA-256 | `d98a1f93478f2d45bf237edfb60f952ef9eaeda210e3d624571b3f529970643c` |

Header record: `file` reports the exact SKU as `"TOMB RAIDER" (AL9E41, Rev.00)`. RetroAchievements lists
the USA CRC32 as `556F40FA`; ROM content matches the multi-language USA/EU SKU described by GameFAQs.

## 2. Executive summary

This is a **developer-intended 4-symbol password system**, not a GameShark/CodeBreaker surface.
The game has no battery save: on reaching a level the game reveals that level's four-letter password;
`Continue → Password` lets the player type any four symbols from an on-screen `0-9 A-Z` keyboard.

The entire system is a **closed hard-coded table of exactly 33 codes** (32 level starts + `ARIA` for
the credits). There is no checksum, no bit-packed payload, no generator, and no algorithmic second
format. The validator packs the four typed symbols into one little-endian u32 and compares it against
33 ASCII records; the loop bound is 33. All 33 records are present in the published GameFAQs list
(one published entry, `WEFK`, is a typo for the ROM's `WEFX`).

Because the accepted set is provably closed and fully published, **no novel accepted code exists**;
this is reported as a bounded negative with counts (§6b), not as a missing enumeration. In-game
evidence: `PRLD` / `ARIA` / `WEFX` accepted with RAM confirmation, `1234` / `WEFK` / `PRLC` rejected
(X-ed-out display). No button code or hidden debug menu was found; the widely republished
"Select+L Skip Level" is a **CodeBreaker activator**, not an in-game trigger (out of scope).

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `-3 -g`.
- Keymap (mGBA SDL default): A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`,
  D-pad = arrow keys.
- Screen path from cold boot:
  1. Language select → choose ENGLISH (A). `screen.png`
  2. Main menu NEW GAME / CONTINUE → Down, A → `screen_continue_menu.png`
  3. Password screen (`screen_password.png`). Keyboard rows: `0-8 / 9 A-H / I-Q / R-Z`, i.e. 9 columns.
  4. Navigate with D-pad, confirm each symbol with A; after the 4th symbol the field either renders clean
     with a `PRESS START` prompt (accepted) or with an X strike-through (rejected).
  5. Start loads the level. `PRLD` → the book/Prelude cutscene; `ARIA` → credits.
- Savestate slot 2 was saved on the blank password screen; every code test is `F2`, navigate, A×4.
- In-game: Start opens the pause menu (shows the current password, Continue/Quit), Select opens inventory.
  `screen_pause.png`, `screen_inventory2.png`, `screen_credits.png`.
- RAM evidence: mGBA `.ssN` files are PNGs with a zlib-compressed `gbAs` chunk. `zlib.decompress` that
  chunk for a 397,312-byte state; EWRAM is at state offset `0x21000`. Four typed indices live at
  **EWRAM `0x0200BD9C`** as four u32s (state `0x2CD9C`); e.g. typing `PRLD` yields
  `[25, 27, 21, 13]` = P,R,L,D. GDB stub (`-g`) was tried but is unreliable in this build
  ("Ignoring packet error", disconnect, "Cannot access memory"); savestate diffing was used instead.

## 4. Address map

All addresses are ROM addresses `0x08000000 + file offset` (file offsets in parentheses).

| Item | Address / range (file offset) | Notes |
|---|---|---|
| Code record table | `0x0803E78C`–`0x0803E894` (`0x3E78C`–`0x3E894`) | 33 records × 8 bytes: 4 ASCII chars + 4 zero bytes. Physical order starts at `ARIA`, ends at `PRLD`. |
| Validator pointer table | `0x08060F70`–`0x08060FF0` (`0x60F70`–`0x60FF0`) | 33 × u32, **reverse** physical order: index 0 = `0x0803E88C` (`PRLD`), index 32 = `0x0803E78C` (`ARIA`). |
| Level-ID table | `0x0803E894`–`0x0803E918` (`0x3E894`–`0x3E918`) | 33 × u32, indexed by the same validator index. Values 1,4,…,54. |
| Identity table | `0x0803E918`–`0x0803E99C` (`0x3E918`–`0x3E99C`) | 33 × u32 = 0..32. No extra/hidden entries. |
| Validator | `0x08025254` (Thumb) | Called with `r1` = packed 4-char code; returns 1 = accepted. Loop bound `cmp r2,#32; bgt`. |
| Pack routine | `0x08026E74` | Reads 4 bytes at object+`0x61C/0x620/0x624/0x628`, converts, packs into u32. |
| Index→ASCII converter | `0x08026ECC` | idx 0..9 → `'0'`..`'9'`; 10..35 → `'A'`..`'Z'`; ≥36 → 0xFF + error. |
| Typed-input validation call | `0x08026B2A` → `0x08026B44` | Fires when the 4th symbol is entered. Only typed-input validation path in the ROM. |
| Other validator callers | `0x08025698`, `0x08026DA4` | Initialise/refresh the displayed current password; same lookup, no second format. |
| Typed symbol array | EWRAM `0x0200BD9C` | 4 × u32, symbols as alphabet indices (0..35). Object base ≈ `0x0200B780`. |

Pointer xrefs: raw pointer to `0x0803E78C` exists only at `0x60FF0` (the last pointer-table entry);
raw pointer to the table base `0x08060F70` exists at `0x252CC`, `0x256A0`, `0x256B4`.

## 5. Algorithm

```text
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"   # 36 symbols
CONVERT(i):                                          # ROM 0x08026ECC
    if i <= 9:  return 0x30 + i                      # '0'..'9'
    if i <= 35: return 0x37 + i                      # 'A'..'Z'  (i=10 -> 0x41)
    return 0xFF                                      # + error call

PACK(c0,c1,c2,c3):                                   # ROM 0x08026E74
    return u32_le( c0 | c1<<8 | c2<<16 | c3<<24 )

VALIDATE(code):                                      # ROM 0x08025254
    p = PACK(*code)
    pointer_table = 0x08060F70
    for i in 0..32:                                  # exactly 33 iterations
        record = u32[pointer_table + 4*i]
        if u32[record] == p:                         # compare first 4 ASCII bytes
            level_id = u32[0x0803E894 + 4*i]
            return ACCEPTED, i, level_id
    return REJECTED
```

The UI calls `PACK`/`VALIDATE` only after the 4th symbol; on accept it shows `PRESS START` and arms
the level load, on reject it draws the X strike-through. No checksum, no XOR, no permutation,
no length branch, no reserved bits — the comparison is a plain 32-bit equality over 33 literals.
The on-screen keyboard has exactly the 36 symbols the converter accepts; there is no hidden 37th
symbol and no way to submit a 5th character (counter saturates at 4).

## 6. Tables

Full accepted set, in **validator pointer-table order** (this is the index used to look up the
internal level ID). `ARIA` is the credits pseudo-level; all others are level starts.

| idx | Code | Internal level ID | idx | Code | Internal level ID |
|---:|---|---:|---:|---|---:|
| 0 | PRLD | 1 | 17 | ROMA | 29 |
| 1 | GAZE | 4 | 18 | MONK | 32 |
| 2 | MEDI | 5 | 19 | AEON | 33 |
| 3 | HAXE | 6 | 20 | TIME | 34 |
| 4 | PATH | 7 | 21 | OLIM | 35 |
| 5 | BONE | 8 | 22 | LAND | 36 |
| 6 | TREE | 9 | 23 | DART | 37 |
| 7 | LINK | 10 | 24 | HILL | 41 |
| 8 | KURZ | 16 | 25 | CHEX | 43 |
| 9 | HELL | 18 | 26 | STLK | 44 |
| 10 | WEFX | 19 | 27 | MECH | 45 |
| 11 | MEMO | 20 | 28 | ARKD | 46 |
| 12 | HEAR | 21 | 29 | MUSH | 47 |
| 13 | FITZ | 23 | 30 | SPOK | 49 |
| 14 | ELRC | 24 | 31 | LITH | 51 |
| 15 | CLIK | 26 | 32 | ARIA | 54 |
| 16 | MGSL | 27 | | | |

Field/layout facts:
- Symbols: 36 (0-9, A-Z). Bijective index→ASCII map; no aliases, no case folding, no glyph collisions.
- Length: exactly 4. Shorter inputs cannot trigger validation; longer inputs are capped.
- Packing: 4 bytes → one u32 little-endian, first typed symbol in the low byte.
- Checksum: none. Reserved/unused bits: none.
- Records: 8-byte stride, 4 ASCII bytes + 4 zero bytes, so a u32 load at the record base is the whole code.

Published-list verification: every one of the 33 ROM codes appears on the GameFAQs level-password
list. The second GameFAQs list uses `WEFK` for the Angkor Wat chapter; `WEFK` is **absent** from the
ROM and rejected in-game, while `WEFX` is present and accepted — a published typo, not a second code.

## 6b. Enumeration

**Space definition.** Alphabet size 36, length 4 ⇒ **36⁴ = 1,679,616** representable inputs.
Every input maps to a distinct packed u32. The accepted set is the 33 literals in the ROM table.

**Exhaustive offline run of the validator model** (`/tmp/tombraider/enumerate.py`, which
reimplements `0x08026ECC`, `0x08026E74` and `0x08025254` bit-for-bit):

```text
space: 36^4 = 1679616
accepted: 33
accepted codes: AEON ARIA ARKD BONE CHEX CLIK DART ELRC FITZ GAZE HAXE HEAR
                HELL HILL KURZ LAND LINK LITH MECH MEDI MEMO MGSL MONK MUSH
                OLIM PATH PRLD ROMA SPOK STLK TIME TREE WEFX
matches ROM table: True
1234 -> REJECTED   0000 -> REJECTED   ZZZZ -> REJECTED
WEFK -> REJECTED   PRLC -> REJECTED
PRLD -> level 1    WEFX -> level 19   ARIA -> level 54 (credits)
```

**Novel codes.** None exist. This is a **bounded negative**, not an untested gap: the whole
36⁴ space was enumerated against an exact model of the ROM validator, the model's accepted set
equals the ROM's 33-record table byte-for-byte, the validator has a hard 33-iteration bound and a
single typed-input call site, and every accepted value is already on the public GameFAQs list.
There is no algorithmic encoder, no second alphabet, no checksum collision and no unused payload
bit that could mint a 34th spelling. Consequently no novel accepted code can be generated, entered
or RAM-verified for this SKU.

**Bounds proven by in-game rejection** (all on the real password screen, symbols observed in EWRAM
at `0x0200BD9C` before reading the display):

| Input | Type | In-game result | Evidence |
|---|---|---|---|
| `PRLD` | valid, public | clean text + `PRESS START`; Start loads the Prelude cutscene | `screen_pw_PRLD2.png`, `screen_level_PRLD.png`; RAM `[25,27,21,13]` |
| `ARIA` | valid, public (credits) | clean text; Start shows credits | `screen_code_ARIA.png`, `screen_credits.png`; RAM `[10,27,18,10]` |
| `WEFX` | valid, public | clean text + `PRESS START` | `screen_code_WEFX.png`; RAM `[32,14,15,33]` |
| `1234` | digits, otherwise well-formed | X-ed out, no `PRESS START` | `screen_pw_1234.png`; RAM `[1,2,3,4]` |
| `WEFK` | published typo (ROM has `WEFX`) | X-ed out, no `PRESS START` | `screen_code_WEFK.png`; RAM `[32,14,15,20]` |
| `PRLC` | one-symbol mutation of a valid code | X-ed out, no `PRESS START` | `screen_pw_PRLD.png`; RAM `[25,27,21,12]` |
| `0000` / `ZZZZ` | alphabet extremes (offline model) | REJECTED by validator model | `enumerate.py` |

The rejections bound three things simultaneously: the alphabet (digits are permitted as input but
no accepted code uses them), the exact-match semantics (a single-character mutation fails), and the
closed table (no algorithmic fallback accepts near-misses).

**Other code surfaces checked (negative):**
- Button-code scan: Konami-style mask sequences as bytes, u16s and active-low forms — 0 hits.
- "Select+L Skip Level": published only as a **CodeBreaker/GameShark button activator**
  (`74000130 01FB` / `32007CC6 0007`); it is the cheat device's activation condition, not a game
  input. Pressing Select+L in-game opened/closed the inventory and did not change level
  (`screen_select_L.png`). Excluded from scope.
- Hidden/debug menu: no debug strings beyond engine error messages
  (`Unknown Command type`, `Tilekit compression type unknown`, `THE END!`, profiling notices).
  UI labels are font/tile indices, not ASCII, so a plain `strings` scan alone would be misleading;
  the entire reachable UI was walked visually and the validator call graph was checked instead.
  Pause menu (Continue/Quit + "Are you sure?"), inventory, credits and password screens were all
  enumerated; no unlabelled/hidden menu entry appeared.

## 7. Validation evidence

- **Observed (emulator):** all screens and screenshots listed above; symbol indices read from the
  uncompressed savestate at EWRAM `0x0200BD9C`; accepted vs X-ed-out display; credits screen after `ARIA`.
- **Derived (static):** 33-record table and 33-entry pointer table with the reverse-order index
  mapping; exact 4-byte u32 comparison; loop bound 33; single typed-input call path; no second format.
- **Inferred:** the internal level-ID numbers' human-facing names (the ROM stores numeric IDs, and
  the public list supplies the level labels). `ARIA`'s ID 54 is interpreted as credits because the
  emulator actually showed the credits.
- **Unverified published data:** all 33 GameFAQs codes were verified against the ROM bytes; `WEFK`
  is the one entry that is wrong.

## 8. Unknowns

- The numeric internal level IDs 2, 3, 11-15, 17, 22, 25, 28, 30, 31, 38-40, 42, 48, 50, 52, 53
  are not reachable from any password; whether they are cut content or reserved slots was not
  investigated (out of cheat scope).
- The non-standard header complement/checksum suggests a patched release header; the game code
  itself boots normally and no trainer/cracktro menu was seen.
- mGBA's GDB stub was unusable in this build, so RAM reads came from savestate diffs rather than
  live breakpoints. The validator was not executed in-process as an oracle; the offline model was
  validated against the ROM bytes and five in-game inputs instead.

## 9. Tooling

- `strings -t x -n 3` + literal `grep -abo` to locate the 33 codes.
- Python `struct` scanning for raw pointer xrefs to `0x0803E78C` / `0x08060F70`.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for the routines.
- `/tmp/tombraider/ssram.py` — extract/decompress the `gbAs` chunk from mGBA `.ssN` files.
- `/tmp/tombraider/keys.py`, `enter_code.py` — reproducible XTEST input and code entry.
- `/tmp/tombraider/enumerate.py` — exact offline validator model and 36⁴ enumeration.
- Screenshots named in §3/§6b were in `/tmp/tombraider/`; no ROM assets are reproduced here.

**Legal note:** no ROM image or extracted artwork is redistributed by this report; only addresses,
hashes, algorithms and original observation screenshots are recorded.
