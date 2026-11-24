# Spy Hunter (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Spy Hunter.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `SPY HUNTER` |
| Game code | `AHNE` |
| Maker | `5D` (Midway) |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock crt0 — not a patched/cracktro image) |
| Complement / checksum | `0xCA` / `0x0000` (checksum 0 is normal for this build) |
| Nintendo-logo hits | 1 (file `0x0`) — single image, not a multiboot/2-in-1 |
| MD5 | `5a6f98ebca34b1d19870481dbe3e3089` |
| SHA-1 | `0cd7527b1ac7e23f14c1eea8b7c58d800d859b38` |
| SHA-256 | `cf32ee296ac04fd67777b244ec2f27a6c026798b91c67787d56d75339042ac66` |

**SKU check (guide §16.11).** This is the retail GBA SKU `AHNE5D`. The sibling
image *Spy Hunter – Super Sprint* is a different ROM and was **not** used as
evidence here. Several widely published "Spy Hunter" codes are for the GC/Xbox/
PS2 SKUs and are **absent from this image under every encoding checked**:
`OGSPY`, `GDOG57`, `WWS413`, `MAKING`, `GUNN`, `SALIVA`, `SHAWN`, `WOODY`,
`SCW823`, `3IQ2`, etc. → 0 literal hits each. Conversely every GBA name-code
published for this SKU is present verbatim. `SPYHUNT` has a second hit at
`0x6374B0`, but that is the credits string `SPYHUNTER\0\0\0COPYRIGHT 2002`,
not a code.

## 2. Executive summary

The only in-game/developer-intended code system in this image is a set of
**eight exact-match profile names** (agent names) entered on the `ENTER NAME`
keyboard. There is no checksum, no alphabet cipher, no generator and no second
algorithmic format: a single byte-exact `strcmp` at `0x0802C98C` is called from
11 sites, and those 11 sites cover the entire accepted set. The accepted set is
therefore **closed and exactly eight strings**; all eight are in the published
GBA lists. A bounded negative is proven below with counts.

One code (`SUPERSPY`) was entered on the real screen and verified in RAM:
name buffer `0x030007C0 = "SUPERSPY"`, flag byte `0x030007F2 = 0x07`. The
other seven were verified statically (exact literal, pointer, validator branch
and effect), not by typing each on screen.

Published **button** sequences exist (Legal-screen erase codes and an in-game
"Chicken Blood" sequence), but no contiguous mask table for them was found in
an exhaustive search (counts in §6b); they remain recon leads, not verified
findings. No hidden/debug menu, password generator, unlockable beyond the
eight names, or unreferenced code string was found.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys.
* Boot path: legal screen → Midway logo → attract → `PRESS START` title →
  `Start` → `AGENT` select → `A` on an empty slot → `ENTER NAME`.
* `ENTER NAME` is an 8-slot keyboard, alphabet `A–Z 0–9` in four rows
  (`ABCDEFGHIJK` / `LMNOPQRSTUV` / `WXYZ0123456` / `789`). Unused trailing
  slots are auto-filled with `.` (the ROM literals are 8-byte dot-padded, e.g.
  `EDACRA..`), so a 6-letter code is entered as 6 letters then `B` to end.
* `B` deletes the last character / ends the name; `A` confirms a character.
* Verified code: type `SUPERSPY` (8 letters), press `B`. The name appears in
  slot 1; RAM `0x030007C0` changes from empty to `SUPERSPY` and
  `0x030007F2` becomes `0x07`.
* Savestate workflow: `Shift+F1..F4` saves, `F1..F4` loads. State files are
  mGBA PNGs with a zlib-compressed `gbAs` chunk; decompressed length is
  397,312 bytes for this 4 MiB-mapped ROM. IWRAM begins at chunk offset
  `0x19000`, so GBA address `0x030007C0` is chunk offset `0x197C0`.

## 4. Address map

### Code (ROM addresses)

| Address | Meaning |
|---|---|
| `0x0802C98C` | Byte-exact, case-sensitive custom `strcmp` (word fast path + null search). Returns 0 on equality. |
| `0x080033FE` | `strcmp(profile[cur], "EDACRA..")` — Arcade Mode gate. |
| `0x08004908` | `strcmp(profile[cur], "........")` — blank-name test. |
| `0x08004BEC`, `0x08004C12` | `strcmp(profile[cur], "SPYHUNT.")` twice (special mode 1; writes `3` to `0x030006D0`). |
| `0x08007448`, `0x0800751E` | `strcmp(profile[cur], "SUPERSPY")` — Super Agent gate; also tests signed halfword at profile+`0x36` against `0x01`. |
| `0x08008258` | Master validator for `BUYMKDA`, `G6155`, and the `BEST`/`GAME`/`EVER` triple (full disassembly below). |
| `0x0800216–0x0800564` | Screen-state accesses to `0x030006D0` (legal/agent/special-mode dispatcher). |

### Data / strings (file offsets; ROM address = `0x08000000` + offset)

| Offset | Bytes | Meaning |
|---|---|---|
| `0x41278` | `EDACRA..\0\0\0\0` | Arcade Mode code |
| `0x41288`/`0x41298` | `. . . . . . . . ` / `. . . . ` | default/blank name render strings |
| `0x412A0`–`0x412F8` | `A B C … 9` | name-entry alphabet glyph labels |
| `0x41300` | `.` / `........` | dot placeholders |
| `0x41310` | `SPYHUNT.` | Special Mode 1 |
| `0x4131C` | `SUPERSPY` | Super Agent Mode |
| `0x41328` | `BUYMKDA.` | Special Mode 2 |
| `0x41334` | `G6155...` | All Cars |
| `0x41340`/`0x4134C`/`0x41358` | `BEST....`/`GAME....`/`EVER....` | three-file "unlock everything" combo |
| `0x31635C` | `C:\Projects\SpyH` + `U` padding | embedded build-path leftover in a data bank; no code references it (0 pointers found) |
| `0x86374B0`+ | credits text (`SPYHUNTER`, `COPYRIGHT 2002`, names) | no code strings |

### RAM (verified against savestate / GDB)

| Address | Meaning |
|---|---|
| `0x030007C0 + 0x6C*n` | profile `n` name, fixed 8 bytes (n = 0..7) |
| `0x030007C0 + 0x34 + 0x6C*n` | 32-bit unlock word written by `BUYMKDA` / `G6155` paths |
| `0x030007F2` (= profile 0 + `0x32`) | flag byte observed `0x07` after `SUPERSPY` |
| `0x030006D0` | scene/screen index: `0` legal, `3` agent select, `1` after the name-entry test |

## 5. Algorithm / validator model

The `strcmp` at `0x0802C98C` is a plain case-sensitive C-string compare. There
is no case folding, no alias table, no length branch and no checksum. The
profile buffer is a fixed 8-byte field; the UI pads unused positions with `.`,
which is why the ROM literals are dot-padded.

Master validator at `0x08008258` (Thumb, reconstructed):

```
check_name_codes(u8 profile_index):
    rec = 0x030007C0 + 108*profile_index
    result = 0
    if strcmp(rec, "BUYMKDA.") == 0:          # 0x0800826E
        *(u32*)(0x030007C0 + 0x34 + 108*i) = 0xFF000200
        result = 2
    if strcmp(rec, "G6155...") == 0:          # 0x08008286
        *(u32*)(0x030007C0 + 0x34 + 108*i) = 0xFF000200
        result = 4
    if strcmp(0x030007C0+0x00, "BEST....") == 0 and    # 0x0800829E
       strcmp(0x030007C0+0x6C, "GAME....") == 0 and    # 0x080082AC
       strcmp(0x030007C0+0xD8, "EVER....") == 0:       # 0x080082BA
        *(u8*)(base+0x30) = 7
        *(u8*)(base+0x31) = 7
        *(u32*)(base+0x34) = 0xFF0103FF
        result = 5
    return result
```

The other three validators (`EDACRA`, `SPYHUNT`, `SUPERSPY`) are separate
call sites of the same `strcmp`; each sets its own flag/scene word on equality
(no match → the post-branch code simply does nothing).

## 6. Tables

### Accepted name codes (complete set)

| # | Literal (8 bytes) | ROM offset | Validator site | Published? | Effect (as published / derived) |
|---|---|---|---|---|---|
| 1 | `EDACRA..` | `0x41278` | `0x080033FE` | yes | Arcade Mode |
| 2 | `SPYHUNT.` | `0x41310` | `0x08004BEC`, `0x08004C12` | yes | Special Mode 1 (writes scene `3`) |
| 3 | `SUPERSPY` | `0x4131C` | `0x08007448`, `0x0800751E` | yes | Super Agent Mode (flag `0x07` observed) |
| 4 | `BUYMKDA.` | `0x41328` | `0x0800826E` | yes | Special Mode 2 (unlock word `0xFF000200`, result 2) |
| 5 | `G6155...` | `0x41334` | `0x08008286` | yes | All Cars (same word, result 4) |
| 6 | `BEST....` | `0x41340` | `0x0800829E` | yes | part of 3-file combo |
| 7 | `GAME....` | `0x4134C` | `0x080082AC` | yes | part of 3-file combo |
| 8 | `EVER....` | `0x41358` | `0x080082BA` | yes | part of 3-file combo (result 5) |

The `BEST`/`GAME`/`EVER` entries are position-fixed: profile 0, 1 and 2
respectively (offsets `+0x00`, `+0x6C`, `+0xD8` from the profile base).

### Published button sequences (recon leads — NOT independently verified)

| Effect | Sequence | Where |
|---|---|---|
| Erase all data | Left, Left, Right, Left, R, R | Legal screen |
| Erase arcade high scores | Up, Up, Down, L, R, L | Legal screen |
| "Chicken Blood" | Left, Left, Right, Right, Right, Left, Left, A | Pause, Special Agent mode |

These came from 3rd party cheat indexes, not from this ROM's code. No contiguous
mask table for any of them exists in the image (search counts in §6b), so they
may be implemented as a chain of immediate comparisons or may be wrong/for a
different revision. They are recorded, not asserted.

### Font/text note

All UI text and code strings are ASCII in this image (unlike Car Battler Joe);
`strings -t x -n 4` finds the whole code bank at `0x41200–0x41360`. The
`EDACRA`/`SPYHUNT`/… literals are therefore not false positives.

## 6b. Enumeration

**Space definition.** A profile name is exactly 8 bytes drawn from a 36-symbol
alphabet (`A–Z`, `0–9`) plus automatic `.` padding: representable name space =
`36^8 = 2,821,109,907,456` distinct 8-character inputs (the 8-byte field itself
allows more, but the UI cannot enter `.`). The validator is a closed whitelist,
**not** a checksum system: it accepts exactly 8 byte strings.

**Whole-space proof (static, exhaustive for this code path).**
* Number of calls to the name `strcmp` (`0x0802C98C`) found by a full BL scan of
  the 8 MiB image: **11**.
* Those 11 calls reference exactly **8 distinct strings** (list in §6).
* No other string-comparison helper is used by any name-entry path (the other
  strcmp-like routines in the image are not reachable from the name buffer).
* Number of accepted name strings not on the published GBA lists: **0**.

**Novel code.** None exists for the name system: the accepted set is exactly
the published 8. Per the brief, the required alternative is delivered as a
**bounded negative with counts** rather than a fabricated novel code. No
checksum/field system exists to mint from, so minting an unpublished name code
is impossible without changing the ROM.

**Rejection bounds.**
* Codes published for other platforms were tested against the image under all
  encodings checked: 10 strings × 1 literal encoding each (**10 literals**),
  plus case-folded/`+0x20`/UTF-16 spot checks → **0 hits**. These would be
  rejected by the game because no validator compares against them.
* The 36-symbol keyboard contains no `.`/space key, so any 8-character input
  not equal to one of the 8 literals is rejected by construction: `36^8 − 8`
  rejected inputs in the reachable space.
* Case sensitivity is proven by the compare instruction sequence (`ldrb`/
  word-load, `cmp`, no case-fold): e.g. `spyhunt.` cannot match `SPYHUNT.`.

**Button-code search counts (bounded negative for a mask table).**
* Published sequences encoded as `u16` little-endian, big-endian, active-low
  complement, byte-per-press, and reversed (newest-first): **3 sequences × 5
  encodings = 15 full-sequence searches**, **0 hits**.
* Prefix searches (first 2 and first 3 presses) for all three sequences in
  forward and reversed order: hits were inspected and all fell in font/tile or
  unrelated data banks (e.g. `0x237130`, `0x3B7B0`, `0x401E0`); **0 in code**.
* Encodings varied over A/B = {0x01,0x100,0x200}, Left/Right = {0x10,0x20,0x40},
  L/R shoulder = {0x100,0x200,0x400,0x800}: **0 full-sequence hits**.
* Thumb `cmp rX,#key-mask` scan of the code region `0x08000200–0x08090000`:
  **737** candidate instructions in 37 clusters of ≥3; none formed the
  published sequence order, i.e. no immediate-comparison matcher was isolated.
* Conclusion: the three published button sequences are **not** stored as a
  contiguous mask table or a simple immediate chain in this image. This is a
  bounded negative about *that search space*, not proof the effects do not
  exist.

## 7. Validation evidence

**Observed**
* mGBA boots the image; screens walked: legal → Midway logo → attract/demo →
  `PRESS START` title → `AGENT` select (8 slots) → `ENTER NAME` keyboard →
  gameplay. Screenshots kept in `/tmp/spyhunter1/`.
* `SUPERSPY` typed on the real keyboard: name displayed as `SUPERSPY` in slot 1
  and persisted in `game.sav`.
* RAM after entry (GDB and savestate reads agree): `0x030007C0` bytes
  `53 55 50 45 52 53 50 59` = `SUPERSPY`; `0x030007F2 = 0x07`;
  scene word `0x030006D0 = 0x03` at agent select.

**Derived** (from disassembly, not executed)
* All 8 accepted literals and their validator addresses (§4/§6).
* The full branch structure of `0x08008258`, including flag words
  `0xFF000200` / `0xFF0103FF` and return values `2/4/5`.
* Case sensitivity and exact 8-byte comparison of `0x0802C98C`.
* Absence of any 9th name-comparison call site (11 BL total).

**Inferred / unverified**
* The gameplay effect labels (Arcade Mode, All Cars, Special Modes) come from
  published lists; the flag writes are derived but the resulting menus were
  not walked for all seven un-entered codes.
* All three published button sequences — not verified in emulator, no table
  found.
* The `C:\Projects\SpyH` string at `0x31635C` has zero code pointers; it is
  treated as dead build metadata, not a debug menu.

**Prompt-injection check.** Fetched cheat pages were treated as data. No
instruction-like payload was encountered; nothing from a page or ROM string
was executed.

## 8. Unknowns

* Which exact menu/flag each of the seven non-entered names unlocks on screen
  (only `SUPERSPY` was walked end-to-end).
* Whether the published button sequences are correct for revision `AHNE5D`;
  the Legal-screen timing window made a controlled in-emulator test
  inconclusive, and the static mask search was negative.
* Whether a code effect requires a second gate (the `SUPERSPY` path also tests
  a signed halfword at profile+`0x36`; that additional condition was not fully
  characterised).

## 9. Tooling

* `strings`, `xxd`, `grep -abo`, Python 3 (`struct`, `capstone`) for hashes,
  header, literal/pointer/BL scans and key-mask brute force.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M
  force-thumb` for all disassembly shown.
* mGBA 0.10.5 (`-3`, `-g`, `-t`, `-d`), Xvfb `:319` + openbox, `xdotool`
  XTEST events (45–150 ms holds), `scrot`, ImageMagick `convert`.
* `ssdiff.py` — decompresses mGBA `.ss*` `gbAs` PNG chunks and diffs RAM
  (guide §16.13). `scan_calls2.py` — BL-to-`strcmp` xref listing.
  `scan_keycmp.py` — Thumb key-mask `cmp` cluster scan. `typer.py` /
  `enter_code.py` — keyboard navigation helpers. All in
  `/tmp/spyhunter1/`.
* No ROM, save, or copyrighted asset is redistributed; only addresses,
  algorithms and hashes are published.

## 10. Cleanup

All processes started for this engagement were terminated by PID number
(Xvfb, openbox, mGBA); no `pkill`/`pkill -f` was used. No `.sav`, `.ss*` or
other emulator artifacts were left in `roms/Spy Hunter/` — the
directory contains only `Spy Hunter.gba` and this report.
