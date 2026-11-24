# Flushed Away (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Flushed Away/Flushed Away.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title / code / maker | `FLUSHED AWAY` / `BLHE` / `G9` (Europe) |
| Version | 0x00 |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| MD5 | `db607f2427469e017560fd23fdc7ea70` |
| SHA-1 | `47c4852a850c0f094673289377c65bdfb5e8936e` |
| SHA-256 | `b940b64523a8c504926415b29a4dbad72cf773e281e8a3fe9d1cb9c2fb280f6b` |

Phase 0: one Nintendo-logo hit at file offset 0 (header checksum zeroed — rebuild artifact;
complement byte 0x59 is unchanged). Stock entry branch; no cracktro, no appended trainer,
no second GBA image. This is a clean retail image.

## 2. Executive summary

The game has **two entirely separate in-game code systems**, both reachable from menus, both
implemented as *closed lookup tables* (no checksum/algorithm):

1. **PASSWORD** (main menu) — eight decimal digits. One 176-byte table of **22** eight-byte
   records at ROM `0x080AE0BC`; validator at Thumb `0x0809D780`. All 22 entries are exactly the
   codes published on 3rd party cheat indexes/fandom/3rd party cheat indexes (21 level codes + `60861775` level select). There is
   no algorithmic generator, so **no unpublished numeric password exists**.
2. **BONUS CODE** (Options → Bonus Code) — eight characters, on-screen keyboard `A–Z 0–9`.
   A **32-byte table of 4** eight-byte records at ROM `0x080AE240`; validator at Thumb
   `0x080A082C`. These are the "lost" bonus codes that 3rd party cheat indexes say nobody has ever found.

I recovered both validators, reimplemented their accept tests as debugger-oracle calls, and
enumerated both closed sets. I then entered **CAKEWALK**, a code that appears in **no published
list**, on the real Bonus Code screen: the game displayed **"Correct! Game Level is now set to
Easy Mode."** RAM proof: code-index byte `0x03003DEC` changed `0x00 → 0x01` and the input buffer
`0x03004272` changed `azzzzzzz → cakewalk`. Rejected inputs were observed on both screens
("Oops! You've entered an incorrect password." / "Oops! Try again") and proven by the oracle
(`r0 = 0`).

In-game text is **tile/font-indexed**, not ASCII (74,819 `strings` hits were noise); every menu
label quoted here was decoded by reading the rendered screen, not from a string bank.

## 3. How to reproduce

* Emulator: mGBA (SDL) on `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, 3× scale.
* Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
  **Hold keys 0.12–0.2 s**; 0.05 s taps double-step / drop presses on these keypads.
* Path to PASSWORD: Title → Start → `PASSWORD` → keypad digits → `Enter`.
  * `12345678` → "Oops! You've entered an incorrect password." (observed).
  * `60861775` → accepted (table index 21; sets level-select flag; see §5).
* Path to BONUS CODE: Title → Start → `OPTIONS` → (B to leave the SOUND sub-focus) →
  Down ×2 → `BONUS CODE` → A. Keyboard is a 13×3 grid:
  row0 `ABCDEFGHIJKLM`, row1 `NOPQRSTUVWXYZ`, row2 `0123456789 BACK CLEAR ENTER`.
  * `CAKEWALK` → "Correct! Game Level is now set to Easy Mode." (observed, novel code).
  * `00000000` → "Oops! Try again" (observed rejection).
* Oracle reproduction (mGBA CLI debugger `-d`, state loaded, Thumb):
  * Numeric validator: set `r0 = 0x03003DB0`, `pc = 0x0809D781`, `lr = return`,
    digit bytes at `0x0300451A..21`, count at `0x03004518`; `r0=1` on accept.
  * Bonus validator: set `r0 = 0x03003DB0`, `pc = 0x080A082D`, `lr = 0x080A08CD`,
    ASCII bytes at `0x03004272..79`, count at `0x03004271`; `r0=1` on accept.
  (Setting `pc`/`lr` directly can disturb the scheduler — for oracle runs only; in-game
  confirmation was done with real keypad input.)

## 4. Address map

| Item | ROM / RAM | Evidence |
|---|---|---|
| Password validator (Thumb) | `0x0809D780` | Watchpoint on `0x03004518` hit `0x0809D2AC`; call site `0x0809D9BA` (`bl`) |
| Password table (22×8 = 176 B) | `0x080AE0BC` | Literal at `0x0809D7E0` = `0x080AE0BC`; `memcpy` at `0x080AD7A4` |
| Password input count (u8) | `0x03004518` (`base+0x768`) | Savestate diff `ss2` vs `ss3`; literal `0x768` at `0x0809D2A4` |
| Password input digits (8×u8, 0–9) | `0x0300451A..0x03004521` (`base+0x76A`) | Savestate diff; literal `0x76A` at `0x0809D7E8` |
| Level-select flag writer | literal `0x03001DDD` at `0x0809D838` | Derived from index-21 branch `0x0809D82E` |
| Code-index result (both systems) | `0x03003DEC` (`base+0x3C`) | `0x0809D802` / `0x080A0896`; RAM diff `00 → 01` |
| Bonus validator (Thumb) | `0x080A082C` | `cmp r7,#8` at `0x080A088C`; table literal at `0x080A089C` |
| Bonus table (4×8 = 32 B) | `0x080AE240` | Literal `0x080AE240` at `0x080A089C`; `memcpy(...,32)` at `0x080A0840` |
| Bonus input count (u8) | `0x03004271` (`base+0x4C1`) | Literal `0x4C1` at `0x080A08A0`; RAM read `08` |
| Bonus input chars (8×ASCII) | `0x03004272..0x03004279` (`base+0x4C2`) | Literal `0x4C2` at `0x080A08A4`; RAM read `7A 7A ...` ('z'×8) |
| Bonus input handler (char≤35) | `0x080A0B88` | `cmp r1,#35` at `0x080A0B94`; letters `value+0x61` at `0x080A0BBA` |
| Struct base used by both screens | `0x03003DB0` (r7/r6/r9/r5 in breakpoints) | Breakpoints at `0x0809D2AC`, `0x0809DC38`, `0x080A04DE` |

Savestate layout used for RAM proofs (guide §16.13): `.ssN` is a PNG; zlib-decompress the
`gbAs` chunk → 397,312-byte state; IWRAM at state `0x19000` (RAM `0x03000000`), so RAM
`0x0300451A` is state `0x1D51A`.

## 5. Algorithm

Both systems are **pure table lookups**, not checksums.

```
password_check(digits[0..count-1]):        # 0x0809D780
    memcpy(stack, 0x080AE0BC, 176)          # 22 records x 8 bytes
    for rec in 0..21:
        matches = 0
        for i in 0..count-1:
            if digits[i] == stack[rec*8 + i]: matches += 1
            else: matches = 0
        if matches == 8:
            [base+0x3C] = rec
            if rec == 21: [0x03001DDD] = 1        # level select
            elif rec <= 17: world = rec>>2; level = rec&3
            else: ...                              # 5-3 boss phases
            return 1
    return 0

bonus_check(chars[0..count-1]):            # 0x080A082C
    memcpy(stack, 0x080AE240, 32)           # 4 records x 8 bytes
    for rec in 0..3:
        matches = 0
        for i in 0..count-1:
            if chars[i] == stack[rec*8 + i]: matches += 1
        if matches == 8:
            [base+0x3C] = rec
            return 1
    return 0
```

Both require `count == 8` (the `matches == 8` test). The password comparison resets the match
counter on a mismatch (so it needs 8 *consecutive* matches); the bonus one does not reset it
but still requires 8 total matches over an 8-byte input — equivalent for count 8.

Input encodings: PASSWORD stores raw digit values 0–9; BONUS stores ASCII — `A–Z` map to
`0x61–0x7A` (`value + 0x61`, `0x080A0BBA`) and `0–9` map to `0x30–0x39`.

## 6. Tables

### 6.1 PASSWORD (all 22 — identical to the published list)

| # | Code | # | Code |
|---:|---|---:|---|
| 0 | 00000000 | 11 | 85196655 |
| 1 | 20849889 | 12 | 10212967 |
| 2 | 04046254 | 13 | 43307561 |
| 3 | 36951399 | 14 | 88407936 |
| 4 | 01082119 | 15 | 38954636 |
| 5 | 69083140 | 16 | 83791936 |
| 6 | 95546453 | 17 | 15348136 |
| 7 | 32577619 | 18 | 37625907 |
| 8 | 07217123 | 19 | 19077573 |
| 9 | 62184927 | 20 | 02348653 |
| 10 | 32051128 | 21 | 60861775 (level select) |

Site labels: 0 = 1-1, 1 = 1-2, 2 = 1-3, 3 = 1-4, 4 = 2-1, 5 = 2-2, 6 = 2-3, 7 = 2-4
(also published as "play the boat"), 8 = 3-1, 9 = 3-2, 10 = 3-3, 11 = 3-4, 12 = 4-1,
13 = 4-2, 14 = 4-3, 15 = 4-4, 16 = 5-1, 17 = 5-2, 18–20 = 5-3 phases 1–3.

### 6.2 BONUS CODE (4 records — none published)

| # | 8 table bytes at `0x080AE240` | Typed form | Effect |
|---:|---|---|---|
| 0 | `6d 6f 76 69 65 73 04 75` | `movies` + byte `0x04` + `u` | Not typeable on the on-screen keyboard (byte `0x04` has no key); oracle-accepted |
| 1 | `63 61 6b 65 77 61 6c 6b` | `CAKEWALK` | **Easy Mode — confirmed on screen** |
| 2 | `6c 63 6b 64 6e 6c 64 64` | `LCKDNLDD` | Oracle-accepted; effect not exercised |
| 3 | `73 68 69 65 6c 64 6d 65` | `SHIELDME` | Oracle-accepted; effect not exercised |

## 6b. Enumeration

**PASSWORD space.** Alphabet 10 symbols (`0`–`9`), length 8 → 10⁸ = 100,000,000 representable
strings. The accept set is the 22-record table at `0x080AE0BC`; there is no generator function
and no checksum, so a code outside those 22 is unreachable. The full space of *table entries*
was enumerated (22/22 accepted by the ROM validator per static decode and by the literal dump)
and every published code was found present. **No unpublished numeric password can be minted**;
this is a bounded negative result, not an omission. Rejection proved on screen for `12345678`.

**BONUS space.** Alphabet 36 symbols (`A–Z`,`0–9`), length 8 → 36⁸ ≈ 2.82×10¹² representable
strings. Accept set = 4 records at `0x080AE240`. All 4 were called through the game's own
validator (`r0=1`); two out-of-table codes (`zzzzzzzz`, `AAAAAAAA`) returned `r0=0`, proving the
bounds. `00000000` was also rejected on the real screen ("Oops! Try again").

**Novel code (not in any published list):** `CAKEWALK`. 3rd party cheat indexes state that only the password
code is known and "no one knows any bonus codes"; 3rd party cheat indexes document only the level select. The
bonus-code table is not on any of those pages. Entered on the real Bonus Code screen:
"Correct! Game Level is now set to Easy Mode." (screenshot `q15.png`). RAM proof in §7.

## 7. Validation evidence

* **Observed (emulator):** title screen; main menu (`START GAME`/`PASSWORD`/`OPTIONS`);
  OPTIONS (`SOUND`/`SOUND TEST`/`BONUS CODE`, with font-decoded descriptions "Toggle the
  game's sound ON or Off", "Select and listen to the sounds from the game", "Enter a code to
  unlock bonuses"); numeric keypad; rejection message for `12345678`; bonus keypad; rejection
  "Oops! Try again" for `00000000`; success "Correct! Game Level is now set to Easy Mode." for
  `CAKEWALK`; gameplay after Easy Mode; pause attempt/cutscene. Screenshots `title_crop.png`,
  `s08.png`, `p02.png`, `p16.png`, `p35.png`, `q05.png`, `q12.png`, `q15.png`, `q21.png`.
* **Observed (RAM):** `0x0300451A = 01 02 03 04 05 06 07 08` after typing `12345678`;
  `0x03004272 = 7A×8` ('z'×8) on the bonus screen; after `CAKEWALK`, `0x03004272 =
  63 61 6B 65 77 61 6C 6B` and `0x03003DEC: 00 → 01`.
* **Observed (debugger):** watchpoint on `0x03004518` hit `0x0809D2AC`; breakpoint at
  `0x0809DC38` gave `r5=0x03004519`, `r6=0x03003DB0`; oracle calls returned `r0=1` for all 4
  bonus records and `r0=0` for `zzzzzzzz`/`AAAAAAAA`.
* **Derived:** both validators, table addresses/sizes, field offsets, success side effects
  (from Thumb disassembly verified against `objdump -M force-thumb`).
* **Inferred:** the exact gameplay meaning of bonus records 0, 2, 3 (their table strings suggest
  movies / a lock-down or download flag / a shield, but the effects were not exercised).

## 8. Unknowns

* Bonus records 0, 2 and 3 were accepted by the oracle but their on-screen effects were not
  exercised; record 0 contains byte `0x04`, which the on-screen keyboard cannot produce, so it
  is likely unreachable without RAM editing.
* Whether entering `60861775` produces a `LEVEL SELECT` menu entry was confirmed only statically
  (literal `0x03001DDD` at `0x0809D838`); the level-select screen itself was not captured.
* No hidden debug menu or button-code sequence was found; the search was bounded to the two
  code screens and their keypad/screen-mode code paths (no ASCII debug strings exist in this
  font-indexed ROM).

## 9. Tooling

`arm-none-eabi-objdump -M force-thumb`, Capstone (pattern scans), `gdb-multiarch`/mGBA `-d`
CLI debugger driven through a Python pty (`ptydrv.py`, `dbgsend.py`), Python zlib savestate
decoder/differ, `strings`/`xxd`, `xdotool`/`scrot`/`convert`. All generated scripts live in
`/tmp/flushed/`. No ROM or copyrighted asset is redistributed here.

## 10. Cleanup / legal note

No ROM, save, or extracted game asset is published — only addresses, hashes, and findings.
All emulated `.sav`/`.ss*` artifacts were removed from the ROM folder and all processes started
for this run (Xvfb `:316`, openbox, mGBA) were stopped by PID.
