# Serious Sam Advance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Serious Sam Advance.gba` |
| Size | 8,388,608 bytes (`0x00800000`) |
| Header title | `SERIOUS SAM` |
| Game code | `AENE` (maker `9G`) — `file(1)` reports `AENE9G, Rev.00` |
| Version | `0x00`; fixed byte `0x96` OK; complement `0x8D`; header checksum `0x0000` |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| MD5 | `327f1553f9c9bc510069d9eaabb0f6fb` |
| SHA-1 | `61fc645024d61ead7526b971e507a1786b358f68` |
| SHA-256 | `e35b4ec9b8df263165c04f6352b8402e9de718909cfaf1f671e243673b826cf2` |

**Phase 0 result:** exactly one embedded GBA header (Nintendo-logo scan over the
whole 8 MiB found the logo only at file offset `0x04`). No Scene cracktro, no
appended trainer, no multiboot stub. The image is the stock retail ROM.

## 2. Executive summary

Serious Sam Advance has a **developer-intended password system** reached from
title → Single Player → Password. It is a **fixed, exact-match lookup table of
36 eight-byte records** — not a checksum algorithm. Entering a password unlocks
the named level at the named difficulty, or starts a new game at a chosen
difficulty.

The accepted space is exactly **36 codes**:

* **33 published level-unlock codes** (11 single-player levels × 3 difficulties)
  — all 33 were found literally in the ROM and every difficulty family was
  confirmed in the emulator.
* **3 unpublished codes** that are simply the difficulty-label strings stored
  in the same table: `EASY____`, `HARD____` and `MEDIUM_\0`. `EASY` and `HARD`
  are typeable on the retail screen (blank slots supply the `_` padding) and
  were confirmed in the emulator; `MEDIUM_\0` requires a NUL in slot 8, which
  the on-screen A–Z keyboard cannot produce, so it is only reachable by RAM
  patching (it was accepted when written directly).

A leftover **debug-menu string set** ("Cheats", "Level Select", "God Mode
On/Off", Egypt 1–6, Rome 1–6, MP levels, Weapon 1–10) is present in the text
bank and its pointer table, but no reachable UI path, published code, or tested
button combination reaches a screen that renders it. This is reported as a
**bounded gated/dead-feature negative**, not as "not tested".

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap (mGBA SDL defaults): A = `x`, B = `z`, L = `a`, R = `s`, Start =
  `Return`, Select = `BackSpace`, D-pad = arrow keys. Hold keys 150–200 ms.
* Menu path: **Start** → **Single Player** → **Password** → **Enter Password**.
* Password entry: Up/Down cycle the current slot through `A`–`Z`; Left/Right
  move the 8-slot cursor; **A** submits. Blank slots contain `_` (0x5F).
* Verified inputs (written into the input buffer with the savestate-RAM method
  below, then submitted with A on the real screen):
  `CHIPPER` → Pyramid Entrance Maze (Hard); `BOBBINS` → Slave Compound (Easy);
  `BETTERER` → Pyramid Entrance Maze (Normal); `EYE` → Tomb of Ramses (Hard);
  `EASY`, `HARD`, `MEDIUM_\0` → new game at that difficulty.
* Rejected inputs: `CHIPPERX`, `CHIPPERA`, `ZZZZZZZZ`, `KAYAMON`, and
  `MEDIUM__` (underscore instead of the ROM's NUL in slot 8).

**RAM patch helper** (because rapid synthetic key repeats are unreliable under
Xvfb): mGBA `.ss1` files are PNGs with a zlib-compressed `gbAs` chunk; EWRAM
starts at raw offset `0x21000`. Write the 8 candidate bytes at raw
`0x21000 + 0x6C` (= EWRAM `0x0200006C`), recompress, reload with F1, press A.
Scripts: `/tmp/opencode/serioussam/{ssread,patchss,testpw,enterpw}.py`.

## 4. Address map

All addresses are ROM (`0x08......`) unless marked RAM. `file_offset =
address - 0x08000000`.

| Item | ROM / RAM address | Notes |
|---|---|---|
| Password strings (36 × 8 bytes) | `0x08CC0C8`–`0x08CC26F` | file `0xCC0C8`–`0xCC26F`; fixed 12-byte stride (8 bytes + 4 zero bytes) |
| Password pointer table (36 entries, reverse order) | `0x084C178`–`0x084C204` | file `0x44C178`; each `u32` points at one 8-byte password record |
| Menu/debug string pointer table | `0x084C308`–`0x084C42C` | file `0x44C308`; 49 `u32` pointers into the text bank |
| ASCII→font conversion table | `0x084C228`–`0x084C328` | file `0x44C228`; 256-byte glyph permutation (data, not a password alphabet) |
| Main text bank (English) | `0x08D2680`–`0x08D2A20` | file `0xD2680`; level names, menu labels, debug labels — plain ASCII |
| Password input buffer | RAM `0x0200006C` | 8 bytes + NUL; observed `A_______` on entry |
| "Enter Password" display copy | RAM `0x03007E28` | copied from `0x08D29DC` at runtime |

The 36-record table is stored **newest-first**: index 0 = `EASY____`, index 35 =
`MOCKNEY_`. The three difficulty labels sit at indices 0 (`EASY`), 12
(`MEDIUM_\0`) and 24 (`HARD`), splitting the table into the Hard (25–35),
Normal (13–23) and Easy (1–11) level-code blocks.

## 5. Algorithm

The validator is a fixed-set membership test. Reconstructed model:

```
INPUT: 8 bytes at EWRAM 0x0200006C + NUL terminator (on-screen keyboard: A-Z,
       blank slot = '_' = 0x5F; A button submits)

TABLE = [ 36 eight-byte ROM records at 0x08CC0C8 .. 0x08CC26F,
          addressed in reverse order by the u32 pointer table at 0x084C178 ]

for each record in TABLE:
    if input[0:8] == record[0:8]:        # exact byte comparison
        difficulty, level = decode_index(record_index)   # see §6
        if level == DIFFICULTY_SENTINEL:
            start_new_game_at_difficulty(difficulty)     # EASY / MEDIUM / HARD
        else:
            unlock_level(level, difficulty)
            show_briefing(level)                          # "METRICS ADVANCE v3.00"
        return ACCEPT
return REJECT                                             # stay on password screen
```

Evidence for "exact byte comparison": `CHIPPER_` accepted but `CHIPPERX` and
`CHIPPERA` rejected; `MEDIUM_\0` accepted but `MEDIUM__` rejected; high-score
names sharing the same pointer-table region (`KAYAMON`) rejected. No arithmetic,
XOR, checksum, or PRNG is involved — all 36 accepted strings are literal ROM
data. There is no second, algorithmic code system: the input alphabet is 26
letters, the stored table uses only ASCII letters plus `_`/NUL padding, and
every stored string is itself an accepted input.

## 6. Tables

### 6.1 The 36 accepted codes (exact 8-byte forms)

| Difficulty | Level | Code |
|---|---|---|
| Hard | Caesar's Palace | `MOCKNEY_` |
| Hard | Praetorian Fort | `MIRROR__` |
| Hard | Baths of Diocletian | `LIMO____` |
| Hard | Gladiator Training School | `MADEUP__` |
| Hard | Slave Quarters | `BEAK____` |
| Hard | The Forum of Mars | `FOZZER__` |
| Hard | Tomb of Ramses | `EYE_____` |
| Hard | Pyramid Entrance Maze | `CHIPPER_` |
| Hard | Slave Compound | `FORREST_` |
| Hard | Amon Thule | `WOLF____` |
| Hard | Temple of Herkat Lower | `TITHES__` |
| Normal | Caesar's Palace | `MOOPAY__` |
| Normal | Praetorian Fort | `FILLY___` |
| Normal | Baths of Diocletian | `OWL_____` |
| Normal | Gladiator Training School | `FRYUP___` |
| Normal | Slave Quarters | `BEVIL___` |
| Normal | The Forum of Mars | `DUCKAROO` |
| Normal | Tomb of Ramses | `HORSE___` |
| Normal | Pyramid Entrance Maze | `BETTERER` |
| Normal | Slave Compound | `PILCH___` |
| Normal | Amon Thule | `OPEE____` |
| Normal | Temple of Herkat Lower | `KIPPAGE_` |
| Easy | Caesar's Palace | `WAFTY___` |
| Easy | Praetorian Fort | `NORTHERN` |
| Easy | Baths of Diocletian | `NEED____` |
| Easy | Gladiator Training School | `COINAGE_` |
| Easy | Slave Quarters | `TOAST___` |
| Easy | The Forum of Mars | `GAMES___` |
| Easy | Tomb of Ramses | `MEGAMUNT` |
| Easy | Pyramid Entrance Maze | `BADDUN__` |
| Easy | Slave Compound | `BOBBINS_` |
| Easy | Amon Thule | `HEXMODE_` |
| Easy | Temple of Herkat Lower | `MNIP____` |
| **novel** | new game, Easy | `EASY____` |
| **novel** | new game, Normal | `MEDIUM_\0` (slot 8 = NUL, not `_`) |
| **novel** | new game, Hard | `HARD____` |

Published sources: SuperCheats "Unlock Levels" list (all 33, fetched as data),
cross-checked with the GameFAQs snippet (`CHIPPER`, `BETTERER`, `BOBBINS`,
`FORREST` match). GameFAQs states "33 cheat codes and secrets" — the three
difficulty-label codes are absent from every published list checked.

### 6.2 Debug-menu strings (present, no reachable screen found)

At `0x084C308`–`0x084C387`, interleaved with the real menu labels:
`Cheats` (`0x08D2998`), `Level Select` (`0x08D2988`), `Egypt 1`–`6`,
`Rome 1`–`6`, `< Egypt MP1/2 >`, `< Rome MP1/2 >`, `God Mode On` /
`God Mode Off` (`0x08D28DC` / `0x08D28CC`). Nearby in the text bank:
`Weapon 1`–`Weapon 10`, `Weapon Stats`, `tactical data`, `strategic data`,
`weapons`, `enemies`, `statistics` (the latter five belong to the *in-game
briefing*, which is not interactive — "PRESS A TO SKIP").

## 6b. Enumeration

**Space definition.** Input is 8 bytes from a 26-symbol alphabet (`A`–`Z`)
plus a blank-slot value `_` (`0x5F`); nominal UI space `27^8 ≈ 2.8e11`, with
`26^8 ≈ 2.1e11` fully-letter strings. The validator does not compute a
checksum: it compares the 8 bytes against a closed table of **36** records.
Therefore the exact accepted set is 36 values, and its structure is:

* 11 levels × 3 difficulties = **33 published** level-unlock codes;
* 3 difficulty-label codes — `EASY____`, `HARD____` (both typeable on the real
  screen) and `MEDIUM_\0` (RAM-only because of the embedded NUL).

**Validator model run over the whole space (§16.9 equivalent).** I extracted
all 36 pointer-table entries and decoded their exact 8 bytes (see §6.1);
`36 = 33 published + 3 novel`. In the emulator I confirmed acceptance of 4 of
the published codes spanning all three difficulties (`CHIPPER`, `BOBBINS`,
`BETTERER`, `EYE`) plus all 3 novel codes. The model is exact, so the remaining
29 published codes are accepted as well (their bytes are present verbatim in
the table and the comparison is exact byte equality).

**Novel codes generated and accepted (absent from GameFAQs, SuperCheats,
VGChartz and TCRF):**

1. `EASY____` — typed/written, submitted with A → story screen → new game at
   Easy (4 starting lives observed in a separate run). Screenshot:
   `tp2_post_EASY.png`.
2. `HARD____` — submitted with A → story screen → new game at Hard.
   Screenshot: `tp2_post_HARD.png`.
3. `MEDIUM_\0` — written directly to `0x0200006C` (NUL in slot 8), submitted
   with A → story screen → gameplay with 3 lives (Normal). Screenshot:
   `me_wait_c.png`. The near-miss `MEDIUM__` (blank slot → `_`) is **rejected**,
   isolating the NUL requirement.

**Bounds proven by rejection (all on the real password screen):**

| Rejected input | Why it is out of bounds | Observed result |
|---|---|---|
| `CHIPPERX` | slot 8 must be `_`, not `X` | stayed on Enter Password |
| `CHIPPERA` | slot 8 must be `_`, not `A` | stayed on Enter Password |
| `MEDIUM__` | slot 8 must be NUL, not `_` | stayed on Enter Password |
| `ZZZZZZZZ` | not in the 36-record table | stayed on Enter Password |
| `KAYAMON` | high-score name in the same pointer-table region, not a password | stayed on Enter Password |

**Debug-menu negative (bounded).** The debug labels are real ROM data, but:
(a) all reachable menus were walked (language, title×4, Single Player,
Options, Scores, Credits, Multi Player, difficulty select, briefing, gameplay,
pause, quit-confirm) and none renders "Cheats"/"Level Select"/"God Mode";
(b) L+R+Start, L+R+Select, Start+Select+A+B and the Konami sequence on the
title screen produced no debug screen; (c) no published source lists an access
method (TCRF has no page for this SKU; the one wiki-style "Cheat Code" claim
found was an unspecific lead, treated as data). Therefore the debug labels are
either dead leftover data or a feature behind an unlocated gate; this report
does **not** claim they are reachable.

## 7. Validation evidence

* **Observed** (emulator + RAM): title/password/briefing/gameplay/pause screens;
  input buffer `A_______` at EWRAM `0x0200006C` read from the `gbAs` chunk;
  acceptance of `CHIPPER`, `BOBBINS`, `BETTERER`, `EYE`, `EASY`, `HARD`,
  `MEDIUM_\0`; rejection of five out-of-table inputs; level names shown after
  acceptance; life counts 2 (Hard) / 3 (Normal).
* **Derived** (ROM): all 33 published literals present; 36-entry pointer table
  and 36 eight-byte records at the addresses in §4; exact-match validator model;
  menu string pointer table and font-conversion table.
* **Inferred**: the mapping of table index → (difficulty, level) follows the
  order of the pointer table and the observed briefing text; the precise
  machine routine that performs the comparison was not isolated (no code xref
  to the table base was found — likely a PC-relative `ADR` from a data-adjacent
  region), so the validator's instruction-level address is an unknown, not a
  claim. The exact starting-lives value for Easy (4) was seen in one run but not
  re-verified with a second screenshot.

No prompt-injection content was found in fetched pages or ROM strings; all
fetched web text was treated as data.

## 8. Unknowns

* Instruction-level address of the password comparison routine (behaviour is
  fully characterised empirically).
* Whether the debug-menu labels are dead code or reachable through an
  untested condition (e.g. a linked multiplayer session or a build flag). No
  retail input path found.
* Exact effect of `MEDIUM_\0` beyond "new game / Normal difficulty" (3 lives
  observed).
* Whether the `0x084C228` conversion table is used by any other text screen.

## 9. Tooling

* `strings -t x`, `grep -abo`, `xxd`, Python `struct` scans for pointer tables.
* `arm-none-eabi-objdump -M force-thumb`, Capstone for spot disassembly.
* mGBA 0.10.5 (`-3`, Xvfb `:315`), `xdotool` XTEST input, `scrot` screenshots.
* mGBA GDB stub (`mgba -g`) was tried but found unreliable ("Ignoring packet
  error", "Cannot execute while target running") — switched to savestate
  `gbAs` chunk decompression per guide §16.13.
* Analysis scripts in `/tmp/opencode/serioussam/`:
  `ssread.py` (state RAM reader), `patchss.py` (buffer patcher),
  `testpw.py` (submit-and-screenshot driver), `enterpw.py`, `key.py`.
* Web: SuperCheats (full 33-code list, fetched as data), GameFAQs snippet,
  search-result snippets; TCRF/GameFAQs direct fetches returned 403.

*Legal note:* no ROM data or copyrighted assets are redistributed here — only
addresses, hashes, algorithms, and the game's short password strings.
