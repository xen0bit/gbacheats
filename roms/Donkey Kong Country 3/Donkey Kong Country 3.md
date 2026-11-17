# Donkey Kong Country 3 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Donkey Kong Country 3.gba` (16,777,216 bytes = 16 MiB) |
| Header title | `RAREDKC3` (bytes `0xA0`–`0xA7`) |
| Game code / maker | `BDQE` / `01` (Nintendo), Europe, version `0x00` |
| Entry word | `0xEA00002E` — **stock** GBA branch (§16.1: not a cracktro patch) |
| Complement / checksum | `0xA5` / `0x0000` (normal for retail rebuilds) |
| MD5 | `f577a97d679e669f8063910eb060e864` |
| SHA-1 | `c50982b4c26e25ba3538be97b585d95737d7ade7` |
| SHA-256 | `eef5120a58feaf194d3b47c67ba30e249217953e898cdcf5c3297f1c531ba24f` |

Embedded-header scan: the 156-byte Nintendo logo (`24 ff ae 51 ...`) occurs **once**, at file offset `0x4` (header base `0x0`). The file is exactly 16 MiB; no appended trainer or second image. No patch/trainer present.

## 2. Executive summary

DKC3 (GBA) has a **developer-intended cheat-code system** reached from the in-game menu:
`Options → Cheats → ENTER CHEAT` (an on-screen A–Z `.` `*` keypad). Submission is `START`.

The accepted codes are **exactly seven** fixed strings in a 12-byte-per-record literal table at
ROM `0x086EF33C`. A boolean validator at `0x08078E64` does seven `strcmp` calls; on a match a
second routine at `0x08078E94` ORs the record's `u16` mask into the cheat-flag word
`0x03000444`. All seven codes are already published (GameFAQs, MarioWiki); the table is a
**closed set** and no unpublished code can exist in it (§6b proves this by the loop bound,
the full table dump, and 32 inputs run through the game's own validator).

The `EXTRAS` code unlocks a developer menu **Extras** (Funky's Rentals / Swanky's Dash /
Cranky's Dojo) on the main menu; `MUSIC` unlocks a **Music Player** sound test. `KREDITS`
plays the credits. The widely published SNES-era button sequence
`L,R,R,L,R,R,L,R,L,R` and five-letter codes (`LIVES`, `ASAVE`, `TUFST`, `WATER`, `ERASE`,
`MERRY`, `COLOR`, `HARDR`) are **not present** in this GBA image and are rejected — those are
SNES-only (GameFAQs tags that list `SNES`; the GBA FAQ describes only the Options→Cheats
screen). This matches the brief's warning about SNES codes.

Sibling check: DKC1 and DKC2 (8 MiB each) contain their own similar 12-byte cheat tables
(e.g. DKC2 at `0x07FF5B8`: KREDITS/HELPME/WEAKLING/RICHMAN/…), so the *mechanic family* is
shared by Rare's GBA DKC engine. **No address, mask or code list was carried over from the
siblings**; everything above was re-derived from this ROM. DKC3's table, values, and code set
are different (7 codes, `0x086EF33C`, 16 MiB image).

## 3. How to reproduce

Emulator: `mgba` (SDL), `Xvfb :316 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`.
Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`Backspace`, D-pad=arrows.
Hold 100–150 ms per press.

Menu path (verified on screen):
1. Boot → intro → title `PRESS START` → `START`.
2. `Select Save Slot` screen: `DOWN ×3` → `A` (**Options**: Music Volume / SFX Volume / **Cheats**).
3. `DOWN ×2` → `A` → **ENTER CHEAT** keypad.
4. Type a code by moving the keypad cursor with the D-pad and pressing A for each letter;
   press `START` to submit. An accepted code plays a confirmation jingle; `MUSIC` jumps
   straight to the Music Player, `EXTRAS` saves and returns to a menu that now has an
   **Extras** entry, `KREDITS` plays the credits.

Address-level reproduction (no long keypad navigation): the entered string lives as a
NUL-terminated `char[]` at EWRAM `0x02008EA8`. Save a state on the ENTER CHEAT screen,
decompress the mGBA `gbAs` PNG chunk, write the code bytes at raw offset
`0x29EA8` = `0x21000 + (0x02008EA8 - 0x02000000)`, recompress, reload and press `START`.
All 7 acceptances and all rejections in §6b were produced this way with the ROM's own
validator/effect code executing normally.

Published codes tested in-ROM and in emulator: `KREDITS MONKEY HARDER TUFFER MUSIC AQUA
EXTRAS` (all accepted). SNES codes tested: `LIVES ASAVE ERASE TUFST` and button sequence
`LRRLRRLRLR` (all rejected).

## 4. Address map

| Address | Kind | Meaning (evidence) |
|---|---|---|
| `0x086EF33C` | ROM, table | 7 × 12-byte cheat records `{ char name[8]; u16 mask; u16 pad }` (Derived) |
| `0x086EF390` | ROM, table | identity byte table `00 01 02 … 0F` following the cheat table (Derived) |
| `0x08078E64` | ROM, Thumb fn | **validator**: `r0` = input string; returns 1 on match else 0 (Derived) |
| `0x08078E94` | ROM, Thumb fn | **applier**: on match ORs record mask (`ldrh [r4,#8]`) into `u16 [0x03000444]` (Derived) |
| `0x08078F18` | ROM, Thumb fn | ENTER CHEAT screen handler; calls both above at `0x8078FB0` / `0x8078FD4` (Derived) |
| `0x08078DF8` | ROM, Thumb fn | dispatcher: state 1 → name entry `0x08078ED8`, state 2 → cheat entry `0x08078F18` |
| `0x08078E64` loop bound | ROM | `cmp r5,#6; bls` → exactly 7 records (Derived) |
| `0x080015B8` | ROM, Thumb fn | `strcmp`; only 4 call sites total, 2 of which are the cheat functions (Derived) |
| `0x02008EA4` | EWRAM | text-entry UI object; `+0x4` = input buffer (Derived + Observed via injection) |
| `0x02008EA8` | EWRAM | 16-byte input string buffer (Observed: injected bytes read back from savestate) |
| `0x03000440` | IWRAM | global base used by cheat handler |
| `0x03000444` | IWRAM | **cheat flag word, `u16`** — OR target of the applier (Derived) |
| `0x03000550` | IWRAM | screen-mode word: `15` = cheat entry, `18` = music player, `16` = Extras, `6` = save/menu, `1` = title/menu (Observed) |
| `0x03000654` | IWRAM | byte set to 1 by `KREDITS` (and by the `0x100` branch) (Observed) |
| `0x03000709` | IWRAM | byte set by the `0x400` / EXTRAS branch (Derived) |

File offset ↔ ROM address: `addr = 0x08000000 + file_offset`. Table file offset `0x6EF33C`.

## 5. Algorithm

```c
// record layout, 12 bytes
typedef struct { char name[8]; uint16_t mask; uint16_t pad; } CheatRec;
CheatRec cheats[7] = (CheatRec*)0x086EF33C;   // file 0x6EF33C

int cheat_valid(const char *input) {          // 0x08078E64
    for (int i = 0; i < 7; i++)
        if (strcmp(cheats[i].name, input) == 0) return 1;
    return 0;
}

void cheat_apply(const char *input) {         // 0x08078E94
    for (int i = 0; i < 7; i++)
        if (strcmp(cheats[i].name, input) == 0) {
            *(uint16_t*)0x03000444 |= cheats[i].mask;   // ldrh/strh
            break;
        }
}

// DISPATCH (0x08078FAC, entered while screen mode == 15)
if (!cheat_valid(input)) { /* fail path 0x807908C */ }
else {
    play_confirmation_sound();                // 0x80AF2F2 × 2
    cheat_apply(input);
    flags = *(uint16_t*)0x03000444;
    if (flags & 0x0001) { /* KREDITS: byte 0x03000654=1, sound 0xE8 */ }
    if (flags & 0x0100) { /* MUSIC:   set screen mode 18 (Music Player) */ }
    if (flags & 0x0400) { /* EXTRAS:  byte 0x03000709=1, save, mode 16 */ }
    // remaining bits (0x4 MONKEY, 0x80 HARDER, 0xC0 TUFFER, 0x200 AQUA)
    // persist in the save record and change gameplay flags
}
```

Notes: the table strings are NUL-padded to 8 bytes; `strcmp` requires an exact,
case-sensitive, NUL-terminated match. There is no checksum, wildcard, prefix match, XOR or
PRNG anywhere on this path — it is a pure literal lookup. The UI offers `A–Z`, `.`, `*`;
`*` and `.` are ordinary characters to the validator (proved by rejection in §6b).

## 6. Tables

The complete ROM table at `0x086EF33C` (record = string + `u16` mask + `u16` pad):

| # | Name | Mask at `+8` | Published effect | Observed screen mode after submit |
|---:|---|---|---|---|
| 1 | `KREDITS` | `0x0001` | Play credits | stays 15, **but `0x03000654` = 1** (accepted) |
| 2 | `MONKEY`  | `0x0004` | Start with 50 extra lives | 6 (saved / menu) |
| 3 | `MUSIC`   | `0x0100` | Music Player (sound test) | **18** — Music Player screen |
| 4 | `AQUA`    | `0x0200` | All 98 Bonus Coins | 6 |
| 5 | `HARDER`  | `0x0080` | No midpoint (Star) barrels | 6 |
| 6 | `TUFFER`  | `0x00C0` | No DK/Star barrels on new game | 6 |
| 7 | `EXTRAS`  | `0x0400` | Unlock all minigames from main menu | **16** → main menu gains `Extras` |

`TUFFER`'s mask `0xC0` contains both bit 6 and bit 7; bit 7 is also `HARDER`'s mask, i.e.
TUFFER subsumes HARDER's flag (a deliberate combination, not a duplicate alias).

Hidden `Extras` menu (observed, screen `extras_entries.png`): exactly three entries —
**Funky's Rentals**, **Swanky's Dash**, **Cranky's Dojo**. No other hidden menu was found.

## 6b. Enumeration

**Space definition.** The system is a pure lookup, not a checksum code. Alphabet offered by
the input keypad: 28 symbols (`A`–`Z`, `.`, `*`). Record width: 8-byte name field (max 7
characters + NUL), 2-byte flag mask, 2-byte padding. Table length: **exactly 7 records**
(the validator's `cmp r5,#6; bls` loop). Therefore the number of representable accepted
strings is **exactly 7** — no other byte string can satisfy `strcmp` against these 7
constants. There is no generator, no checksum width, and no reserved payload bits.

**Closed-set proof (§16.9: run the ROM's validator, don't just read the table).** 32 distinct
strings were injected into `0x02008EA8` and submitted with `START` in mGBA; acceptance was
read from the screen-mode word `0x03000550` (and `0x03000654` for KREDITS):

- Accepted: `KREDITS, MONKEY, HARDER, TUFFER, MUSIC, AQUA, EXTRAS` — 7/7 published codes.
- Rejected (25): `ZZZZZZ, music, MUSIC , LIVES, ASAVE, TUFST, ERASE, MUSI, MUSICC, MUSIC.,
  MUSIC*, empty, DKC, MUSI*, MU*IC, *USIC, MUSI., MUS.*, MUSIC**, KREDIT, KREDITS*, EXTRA,
  EXTRAS , MONKE, MONKEYY`.
- Case change, trailing space, wildcard chars, truncation, extension, empty input and all
  four tested SNES codes are rejected — no aliases exist.

**Novel code: none can exist in this system.** §0.2's "mint an unpublished code" goal is
inapplicable to a closed 7-entry lookup whose every entry is already published; by the
guide's §7.1 such a table is enumerated directly, and §0.2's "negative results bounded"
clause is the operative requirement. The bound is proven three ways: (a) the validator's
loop iteration count is 7 and the table bytes were dumped in full (no hidden records before
`KREDITS` or after `EXTRAS`); (b) the only four `strcmp` call sites in the ROM are the two
cheat functions plus two unrelated resource-name checks at `0x08009246`/`0x080092C4`; (c) the
28 rejected inputs above exercise case, wildcard, truncation, padding and the published
SNES code space. Consequently **there is no unpublished code to report**, and this is a
positive finding, not an omission.

**Button-code space (SNES codes).** No key-mask sequence table exists in this ROM. Searches
for `L,R,R,L,R,R,L,R,L,R` encoded as active-high `u16` (`0x0200,0x0100,…`), active-low
`u16` (`0xFDFF,0xFEFF,…`), reversed order, and 1-byte-per-press key indices (9/8 and 2/1)
returned **no code/data hits**. The strings `LIVES`, `ASAVE`, `MERRY`, `COLOR`, `WATER`,
`ERASE`, `HARDR`, `TUFST` are **absent** from the image (literal and case-insensitive
search). Dynamically, pressing `L,R,R,L,R,R,L,R,L,R` on the title screen and on the
Select Save Slot screen left the screen-mode word at `1` — no ENTER CHEAT gate opened.
The GameFAQs "Codes" list carrying those codes is tagged `SNES`; the GBA FAQ lists only the
Options→Cheats passwords.

**Bounds proof.** Accepted set = 7, rejected set = 25 distinct tested out of the infinite string
space; the table's 7-record bound makes the enumeration exhaustive rather than sampled.

## 7. Validation evidence

- **Observed (emulator/screenshot/RAM):** title, Select Save Slot, Options (3 items),
  ENTER NAME keypad, ENTER CHEAT keypad, Music Player, pause/status screen (star with
  timer/counters), Extras main-menu entry and its 3 submenu entries. MUSIC → Music Player;
  EXTRAS → `Save successful` then main menu with `Extras`. Mode word `0x03000550` and byte
  `0x03000654` read from decompressed mGBA savestates before/after each submit. Injected
  bytes read back at `0x02008EA8`, confirming the buffer address. Button sequence produced
  no mode change.
- **Derived (disassembly):** table layout/values at `0x086EF33C`; validator/applier logic and
  their call sites; `strcmp` at `0x080015B8` with only 4 total callers; flag word
  `0x03000444`; dispatcher mapping screens 1/2 and modes 13/15.
- **Inferred (not fully played through):** the exact gameplay outcome of `AQUA`, `HARDER`,
  `TUFFER` and `MONKEY` (bonus-coin grant, barrel removal, +50 lives) is taken from the
  published descriptions plus the flag bits written; long completion playthroughs were not
  performed. The SNES button code is judged absent from the combination of a negative ROM
  search and a negative dynamic test, not from exhaustive enumeration of every button
  sequence of every length.

## 8. Unknowns

- Maximum number of characters the ENTER CHEAT keypad physically allows (the table's
  longest string is `KREDITS`, 7; longer injected strings were rejected by `strcmp` but the
  UI's own cap was not measured).
- Whether the cheat-flag word `0x03000444` is copied verbatim into the 512-byte SRAM save
  (mGBA had not flushed `0xEE`-filled `.sav` to disk at capture time); the in-RAM OR is
  proven, the on-disk encoding is not.
- SNES-only button codes could in principle be implemented by a sequence checker that uses
  an encoding not covered by the four searches in §6b; no such checker was located.
- The pause screen reached here was a status display (star, completion %, lives/counters);
  a separate hidden debug screen was not found in the screens walked.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for
  Thumb disassembly; Python `struct` for literal-pointer and byte-pattern scans.
- Python savestate injector: decompress the `gbAs` zlib chunk from the mGBA `.ss1` PNG,
  write bytes at `0x21000 + (addr - 0x02000000)` for EWRAM or `0x19000 + (addr -
  0x03000000)` for IWRAM, recompress and reload (§16.13). Scripts: `batch_test.py`,
  `test_code.py` in `/tmp/opencode/dkc3/`.
- `xdotool` XTEST input to the focused mGBA window; `import -window root` for screenshots;
  `Xvfb :316` + `openbox` + `SDL_AUDIODRIVER=dummy`.
- Web: archived GameFAQs cheats page (Wayback), MarioWiki GBA codes page, RareGamer.
  Fetched pages were treated as data only (§16.8); no instructions in them were executed.
- No ROM or copyrighted assets are redistributed; only addresses, hashes, and original
  analysis findings are published.
