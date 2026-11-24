# Polly Pocket: Super Splash Island (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Item | Value |
|---|---|
| File | `Polly Pocket: Super Splash Island.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `POLLY POCKET` |
| Game code / maker | `AOTE` / `7D` (i.e. `AOTE7D`), version `00` |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| Fixed 0x96 | present at `0xB2` |
| Header complement | `0x37` (recomputed `0x4F` over `0xA0..0xBC`); checksum `0x0000` — consistent with a rebuilt/patched header, but **no trainer or cracktro found**: exactly one Nintendo-logo hit, at file `0x0`, and no second embedded GBA header |
| MD5 | `d53ca7a7f09e222722e110445e1a4e6c` |
| SHA-1 | `e8df35f71cba359a077522815ca5c4887d0ce161` |
| SHA-256 | `2416b2c3aa5c3c1a13383fd5a4c76cc353fc1a71ba3dd8d0992b96164be4219a` |

## 2. Executive summary

The game has a **developer-intended, in-game password system** with a fully algorithmic
validator — not a hard-coded code table. It is reached from the title menu:
**CONTINUE → ENTER PASSWORD** (selecting CONTINUE with no save lands on the password
screen; with a save it resumes play, so the practical route is a fresh/blank save).

The password is **eight symbols from a 16-letter consonant alphabet**
`B C D F G H J K L M N P Q R S T` (indices 0–15). The validator at `0x080172DC`
checks only **one 4-bit checksum**: the last symbol must equal the sum of the first
seven modulo 16. The decoder at `0x080171B8` packs the first seven symbols into
three state fields: a 12-bit "tickets12" counter, a 6-bit thousands-of-tickets
bonus (×1000), and six unlock flags. A generator at `0x08017254` performs the
inverse. All five published 3rd party cheat index codes were verified against the ROM, decoded,
and re-entered; their literals are **not present as ASCII anywhere in the ROM**,
confirming the algorithmic design.

Novel code **`MBFTDDCB`** (values `9,0,3,15,2,2,1,0`), absent from every published
list, was generated, typed on the real ENTER PASSWORD screen, and RAM-verified:
`tickets12=777`, `bonus=47000`, flags `+4` and `+16` set. Bounds were proven by
rejection: `MBFTDDCC` (bad checksum) shows **INCORRECT PASSWORD** and changes no
state. The four unused payload bits were also demonstrated by the alias
`BBBDGBBJ` → same 2000-ticket state as `BBBDBBBD`.

## 3. How to reproduce

* Emulator: `mgba` (SDL build), `Xvfb :315`, `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, viewport 3×.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys.
* Hold each GBA key ~100 ms; short 50 ms taps can be missed or double-step.
* Path from a fresh boot: press **A ~16×** to skip the license/cutscenes until
  `PRESS START`, press **Start**, then **Down** once (highlight `CONTINUE`) and **A**;
  after a short transition the `ENTER PASSWORD` screen appears (8 slots, cursor on slot 0).
* On the password screen: **Left/Right** move the cursor, **Down** increments the
  current symbol, **Up** decrements it (values wrap 0..15), **A** submits, **B** exits.
  Note the game's internal button enum is `A=1,B=2,Select=4,Start=8,Right=16,Left=32,Up=64,Down=128`,
  so the physical D-pad Down/Up — not A/B — edit a digit.
* Type the eight letters of a code, press **A**. A valid code returns to the Info
  Booth and updates the ticket counter; an invalid one shows `INCORRECT PASSWORD`.
* Codes tested in-game: `BBBDBBBD`, `GSFJDBBR`, novel `MBFTDDCB`, alias `BBBDGBBJ`,
  rejected `MBFTDDCC`.
* Savestates (`Shift+F1`) were used to avoid replaying the intro; the `.ss1` chunk
  `gbAs` was zlib-decompressed and IWRAM read at raw offset `0x19000`.

## 4. Address map

| Address (ROM / RAM) | Meaning |
|---|---|
| `0x08033364` | ASCII string `ENTER PASSWORD` (menu string ID 15 of the 40-entry table) |
| `0x08033438` | 40-string pointer table (5 languages × 8 string IDs) |
| `0x08033C00` | 16-byte font table: alphabet indices `(1,2,3,5,6,7,9,10,11,12,13,15,16,17,18,19)`; glyph tile index = `table[v]*6 + tile_base` |
| `0x08033C10` / `0x08033CCC` / `0x08033CE4` | Tile-indexed text banks: `ENTER PASSWORD`, `PASSWORD`, `INCORRECT PASSWORD` (`0x40` = space, `#` = line marker) |
| `0x08016C6C` | Password-entry screen handler (key processing, cursor, submit) |
| `0x080171B8` | **Decoder / apply**: code values → state globals |
| `0x08017254` | **Generator**: state globals → code values + checksum |
| `0x080172DC` | **Validator**: checksum test, returns 1/0 in `r0` |
| `0x08012BB8` | Screen-state jump table; **index 6 = password entry** (`0x08012D54` → `BL 0x08016C6C`), index 8 → `0x08016638` (View Password) |
| `0x03002260` | Eight 32-bit code values (one per symbol), indices 0..7 |
| `0x03001694` | tickets12 (12-bit) |
| `0x0300169C` | ticket bonus, stored as an integer multiple of 1000 |
| `0x03001640` | Six unlock flags at `+4,+8,+12,+16,+20,+24` |
| `0x30015D8` (h), `0x300165C` | Screen-state variables used by the dispatcher |

## 5. Algorithm

Validator (`0x080172DC`), Thumb pseudocode:

```c
uint32_t *code = (uint32_t*)0x03002260;
uint32_t sum = 0;
for (int i = 0; i < 7; i++) sum += code[i];
return (code[7] == (sum & 15)) ? 1 : 0;
```

Decoder / apply (`0x080171B8`), executed only on accept:

```c
uint32_t *v = (uint32_t*)0x03002260;
*(uint32_t*)0x03001694 = v[0] + (v[1]<<4) + (v[2]<<8);        // tickets12
*(uint32_t*)0x0300169C = 1000 * (v[3] + ((v[4]&3)<<4));       // bonus
uint32_t f = v[5] + (v[6]<<4);
for (int b = 1; b <= 6; b++)
    if (f & (1<<b)) *(uint32_t*)(0x03001640 + b*4) = 1;       // six flags
```

Generator (`0x08017254`) reverses this: splits tickets12 into nibbles, divides the
bonus by 1000 and splits the quotient into nibbles, packs the six flags, then
stores `(sum of first seven) & 15` as symbol 8.

## 6. Tables

**Alphabet (16 symbols, value → letter):** `0=B 1=C 2=D 3=F 4=G 5=H 6=J 7=K
8=L 9=M 10=N 11=P 12=Q 13=R 14=S 15=T`. The ROM font table at `0x08033C00`
stores the alphabet positions `1,2,3,5,6,7,9,10,11,12,13,15,16,17,18,19`,
confirming vowels are omitted and the on-screen glyphs are those letters.

**Published codes decoded (all checksum-valid):**

| Code | values | tickets12 | bonus | flags | Published effect |
|---|---|---|---|---|---|
| `BBBDBBBD` | 0,0,0,2,0,0,0,2 | 0 | 2000 | 0x00 | 2000 tickets |
| `GSFJDBBR` | 4,14,3,6,2,0,0,13 | 996 | 38000 | 0x00 | "38170 tickets, 1 secret costume" |
| `JNSTBSKD` | 6,10,14,15,0,14,7,2 | 3750 | 15000 | 0x7e | 15000 tickets, all costumes/slide |
| `TTTHCSKL` | 15,15,15,5,1,14,7,8 | 4095 | 21000 | 0x7e | 21000 tickets, all dressing rooms |
| `HKLTFSKP` | 5,7,8,15,3,14,7,11 | 2165 | 63000 | 0x7e | 63000 tickets, all dressing rooms |

All five literals are **absent** as ASCII in the ROM (`grep -abo` = no hits), as
expected for an algorithmic code space. 3rd party cheat index lists exactly
these five; 3rd party cheat index list the same set. No 3rd party cheat index page
with additional codes was found.

**Published-list discrepancy (result, not an omission):** `GSFJDBBR` was entered
and RAM-verified as `tickets12=996`, `bonus=38000`, **all flags zero**. The
published "38,170 tickets, 1 secret costume" description is therefore inaccurate
for this revision (the ROM has no 38170 or 170 literal and no costume flag set).
`JNSTBSKD`/`TTTHCSKL`/`HKLTFSKP` all decode to `flags=0x7e` (all six bits set),
consistent with their "all" descriptions; the difference is only which ticket
amount is advertised.

**Flag bits:** bit1→flag at `+4`, bit2→`+8`, bit3→`+12`, bit4→`+16`, bit5→`+20`,
bit6→`+24`. Bit0 of symbol 6 and bit3 of symbol 7 are never read.

## 6b. Enumeration

* **Alphabet/length:** 16 consonant symbols, 8 positions → `16^8 = 4,294,967,296`
  representable strings.
* **Validator model:** one 4-bit checksum over the first seven symbols, so
  `16^7 = 268,435,456` strings are accepted (`1/16` of the space). The offline
  model (`password.py`) agrees with the ROM on all five published codes, the
  novel code, the alias and the rejected code.
* **Payload / field widths:** tickets12 = 12 bits (0–4095); ticket bonus = 6 bits
  (`v3` 4 bits + `v4` low 2 bits) → 0…63000 in steps of 1000; six flags = 6 bits.
  Total 24 state bits → `2^24 = 16,777,216` distinct states.
* **Unused bits / aliases:** `v4` bits 2–3, `v5` bit 0 and `v6` bit 3 are ignored
  by the decoder (4 bits), giving `2^4 = 16` spellings per state. Demonstrated
  in-game: `BBBDGBBJ` (values `0,0,0,2,4,0,0,6`) produced the same
  `bonus=2000`, `tickets12=0`, flags=0 state as `BBBDBBBD`.
* **Novel code (not in any published list):** **`MBFTDDCB`** — generated from a
  chosen state (tickets12=777, 47000 bonus tickets, flags `+4` and `+16`), typed
  on the real ENTER PASSWORD screen, accepted, and RAM-verified:
  `0x03001694=777`, `0x0300169C=47000`, `0x03001644=1`, `0x03001650=1`
  (all other flags 0). Screenshot `novel_result.png` shows the counter at 047000.
  Its ticket/flag combination appears on no 3rd party cheat indexes or
  3rd party cheat index list.
* **Bounds proven by rejection:** `MBFTDDCC` (identical payload, final checksum
  symbol `C` instead of `B`) was entered and submitted; the game displayed
  **INCORRECT PASSWORD** (`bad_checksum_result.png`), the ticket counter stayed
  at 000000 and no state global changed. No out-of-range field test exists
  beyond the checksum, because every 4-bit value 0–15 is a legal symbol; the
  "out-of-range" surface is the four ignored payload bits, whose non-effects were
  proven by the alias test above.

## 7. Validation evidence

* **Observed (emulator + screenshots):** title → CONTINUE → ENTER PASSWORD screen;
  screen literally renders `MBFTDDCB` before submission (`code_ready.png`);
  acceptance returns to Info Booth with counter 047000 (`novel_result.png`);
  `BBBDBBBD` → counter 002000 (`bbb_result.png`); `MBFTDDCC` → INCORRECT PASSWORD
  with counter 000000 (`bad_checksum_result.png`).
* **Observed (RAM, savestate `gbAs` diffs):** `BBBDBBBD` →
  `0x300169C=2000`; `MBFTDDCB` → `0x3001694=777`, `0x300169C=47000`,
  flags `+4=1`, `+16=1`, others 0; `GSFJDBBR` → `0x3001694=996`,
  `0x300169C=38000`, flags all 0; `BBBDGBBJ` → same state as `BBBDBBBD`.
* **Derived (disassembly):** validator formula at `0x080172DC`; decoder at
  `0x080171B8`; generator at `0x08017254`; font/alphabet table at `0x08033C00`;
  screen-state jump table at `0x08012BB8` (index 6 = password entry).
* **Inferred (not separately played out):** the exact in-game meaning of each of
  the six flag bits was not followed through every minigame/costume screen; they
  are named by their RAM offsets and their published "all"/"dressing room"
  correlations, not by a dedicated visual test per bit.

## 8. Unknowns

* The 12-bit `tickets12` field is stored but the on-screen counter displayed only
  the `bonus` value in every test (e.g. 47000 with `tickets12=777`). Its exact
  presentation/use in later play was not exhaustively traced.
* Which physical reward each of the six flag bits grants individually was not
  enumerated one-by-one; the correlated descriptions come from published lists.
* The header complement/checksum mismatch is recorded but its cause (rebuild vs.
  shipping quirk) was not determined; it does not affect the password system.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for raw Thumb disassembly; `capstone` 5.0.7 for literal/BL/branch scans.
* `python3` scripts in `/tmp/pollypocket/`: `password.py` (codec,
  decoder, encoder and space count), `xref2260.py` (literal xrefs),
  `findptr.py`/`jumptbl.py` (screen-state jump table), `entercode.py`
  (savestate-verified code entry), `lits*.py` (literal-pool decoding).
* `strings -t x`, `grep -abo`, `xxd`, `zlib` (mGBA `.ss1` `gbAs` chunk decode).
* Web: 3rd party cheat indexes archived snapshot (web.archive.org, 2021-11-18), 3rd party cheat indexes — all fetched as **data**, never as instructions.
* REA/Ghidra was opened on the ROM for cross-checks; its raw-ARM auto-analysis
  recognised only part of the Thumb code, so all addresses above were verified
  with `objdump`/Capstone and live emulator evidence.
* No ROM or proprietary asset is reproduced here; only hashes, addresses,
  algorithms, and the author's own generated code are published.

## 10. Legal note

No ROM image, extracted graphics, music, or game text is redistributed. All
passwords and field names are the analyst's own derived findings; the five
published codes are quoted solely as verification anchors.
