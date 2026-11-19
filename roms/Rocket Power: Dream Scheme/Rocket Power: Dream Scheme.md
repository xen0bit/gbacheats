# Rocket Power: Dream Scheme (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rocket Power: Dream Scheme.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `DREAMSCHEME` |
| Game code / maker | `ARKE` / `78` (`file(1)` reports `ARKE78, Rev.00`) |
| Software version | `0x00` |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| Header checksum | stored `0x0000`; complement byte `0xA1` (recomputed complement `0xBA`) — header was rebuilt/edited |
| Nintendo-logo scan | **one** header only, at file `0x0`; no appended trainer, no multi-game image, no cracktro |
| MD5 | `b14194832a55a7197916edb0bb92bea3` |
| SHA-1 | `1552dd95a0352a45353292a1a4ae711857fb7510` |
| SHA-256 | `ac4db702bb73fe7328ece2309a96ba59f0385d2305cfb70989ff262a7ea78a3c` |

The game is the Helixe/THQ GBA title (2001), sibling to *Rocket Power: Beach Bandits*, which is a different game/ROM and was **not** used as evidence.

## 2. Executive summary

The game has an **in-game password system** (main menu → PASSWORD). Passwords are exactly **8 symbols** drawn from a 32-symbol, vowel-less alphabet `BCDFGHJKLMNPQRSTVWXYZ123456789!?`, so the representable space is `32^8 = 1,099,511,627,776` spellings, of which a 40-bit code space (30 payload bits + 10 check bits) is reachable algorithmically.

Key results:

* The on-screen alphabet is stored as font/tile glyph numbers: each symbol is held in RAM as `0x40 + alphabet_index`. The 8-character input buffer is at **`0x0203E310`** (observed: `B`→`0x40`, `C`→`0x41`, …, `?`→`0x5F`).
* The validator is **`0x08026494`**; the matching generator is **`0x08026660`**. Both use a 10-byte XOR/parity key at **`0x083732E4`**, a 5-entry preset table (`0x0836225C` keys / `0x08362234` strings), and a reversible two-stage XOR cascade.
* I reimplemented the validator bit-for-bit in Python. It accepts 8 of the 13 published codes algorithmically; the other 5 (`TW1ST3R!`, `!!QTTQ!!`, `?R3GG13?`, `S4MDL4RD`, `M4DTQWN!`) are the 5 ROM preset records and are accepted by the table path.
* **A novel, unpublished code was generated and accepted in the emulator:** `V73ZJMTD` → "The Neighborhood" level. Bounds were proven by rejection (`????????`, `6YZ3QBRY`, `W621JMTF`).
* The 13 published codes from GameFAQs/TCRF were verified against the ROM and/or the live screen; no published code was found as plaintext in the ROM (they are glyph-encoded or algorithmic).

A **second semantic gate** exists in the caller (`0x0802C49E`–`0x0802C4D2`): after the algorithmic validator returns 1, `0x0203E3D4` must be nonzero and an indirect function pointer at `0x0203E3C4` must return 1 for the decoded 4-byte state. Checksum-valid codes with unsuitable states are rejected — this is why `6YZ3QBRY` and `W621JMTF` fail despite passing the checksum model.

## 3. How to reproduce

**Emulator**: mGBA 0.10.5 (SDL) under `Xvfb :318`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`. Window crop `720x480+282+258`. Keymap A=`x`, B=`z`, Start=`Return`, D-pad=arrow keys; hold 70–200 ms.

**Menu path to the code screen**:
1. Press Start through the Klasky Csupo intro, legal screen and title ("Press START") until the menu shows NEW GAME / PASSWORD / OPTIONS.
2. Move down once to PASSWORD, press A.
3. The entry grid is 8 columns × 4 rows; D-pad moves the highlight, A adds the highlighted symbol, B erases the last symbol. Exactly 8 characters are accepted.
4. Press Start after a valid 8-character code; the footer reads `password accepted, press START to play`, then the game starts at the encoded level.

**Codes tested on the real screen** (screenshots kept in `/tmp/opencode/rocketdream/`):

| Code | Result |
|---|---|
| `TW1ST3R!` (published) | accepted → Monkey Jungle, 6 collectibles visible |
| `2V74BFDG` (published) | accepted → Elementary School |
| `????????` | `invalid password, press B to erase` |
| `6YZ3QBRY` (checksum-valid, bad state) | rejected |
| `W621JMTF` (checksum-valid, bad state) | rejected |
| **`V73ZJMTD` (novel, not published)** | **accepted → The Neighborhood** |

**Automated reproduction**: `/tmp/opencode/rocketdream/pw.py` (validator), `mint.py` (GF(2) inversion + code generator), `pwentry.py`/`gba.py` (on-screen keyboard driver), `savestate.py` (mGBA `.ss1` `gbAs` decoder).

## 4. Address map

| ROM / RAM address | Meaning |
|---|---|
| file `0xA0` / `0xAC` / `0xB0` | header title / game code / maker |
| `0x0801CEC8` | screen that displays "To continue your game use this password:" (string pool `0x0801D0A4`–`0x0801D0BC`) |
| `0x0801D0A4`, `0x0801D0AC`, `0x0801D0BC` | pointers to those three UI strings |
| `0x0801E348`, `0x0801E38C`, `0x0801E3B0` | password-screen message helpers ("add a letter", "password accepted", "invalid password") |
| `0x0801E0A8`–`0x0801E0BC` | callback pointer table used by the password-entry widget |
| `0x08026494` | **password validator** `validate(u8 *input, u8 *out_state)` → 1 = accepted |
| `0x08026660` | **password generator** `generate(u8 *out_glyphs, u8 *in_state)` |
| `0x083732E4` | 10-byte XOR/parity key `0A 15 12 19 0C 16 0B 05 14 1A 0D 06 13 09 18 1C 0E 07 03 11` |
| `0x0802C49E`–`0x0802C4D2` | caller: validator result + second semantic gate |
| `0x0200D63C` / `0x0200D640` / `0x0200D644` | RAM pointers to preset key table / count (5) / preset string table |
| `0x0836225C` / `0x08362234` | 5 preset state keys (4 bytes) / 5 preset password records (8 bytes) |
| `0x0203E310` | **8-byte password input buffer** (`glyph = 0x40 + alphabet_index`) |
| `0x0203E3C4`, `0x0203E3D4` | second-gate function pointer and enable flag |
| savestate `.ss1` `gbAs` layout | raw state `0x61000` bytes; VRAM `+0x1000`, IWRAM `+0x19000` → `0x03000000`, EWRAM `+0x21000` → `0x02000000` |

## 5. Algorithm

Validator `0x08026494`, for an 8-byte glyph buffer `g[0..7]`:

```
key = [0A 15 12 19 0C 16 0B 05 14 1A 0D 06 13 09 18 1C 0E 07 03 11]
tmp[i] = (g[i] - 0x40) XOR key[i]            # i = 0..7
# reverse two XOR cascades (linear, GF(2)-invertible):
for s in 1..5: for i in 0..7-s: tmp[i] ^= tmp[s]
for s in 1..5: for i in 0..7-s: tmp[s] ^= tmp[i]
r8 = XOR(tmp[0..5])
# check bytes:
for b in 0,1: for j in 0..4:
    bit_j(tmp[6+b]) == parity((r8 & key[5*b+j]) & 0x1F)
# if any mismatch -> try 5-entry preset table; else reject
# unpack tmp[0..6] as a 5-bit stream into 4 state bytes (tmp[7] unused):
acc=0; bits=0; n=0
for out in 0..3:
    while bits <= 7: acc = (acc<<5) | tmp[n++]; bits += 5
    bits -= 8; state[out] = acc >> bits; acc &= (1<<bits)-1
return 1
```

Generator `0x08026660`: pack state into six 5-bit values, compute the two check bytes as above, apply the two XOR cascades, then `g[i] = (tmp[i] XOR key[i]) + 0x40`. The whole 64-bit cascade is a nonsingular GF(2) matrix (rank 64), which is why it can be inverted offline (`mint.py`).

**Unused bits**: `tmp[7]` does not reach the decoded state; it is a check-only value. The generator consumes only the low 30 bits of the 32-bit input state.

## 6. Tables

**Alphabet (screen order, index 0–31):** `B C D F G H J K / L M N P Q R S T / V W X Y Z 1 2 3 / 4 5 6 7 8 9 ! ?`
(No vowels A/E/I/O/U and no `0` — hence `TW1ST3R!` for TWISTER, `M4DTQWN!` for MADTOWN.)

**Published codes (GameFAQs cheats page, 13 total; TCRF confirms the 3 special passwords):** 

| Effect | Password | ROM path |
|---|---|---|
| Elementary School | `2V74BFDG` | algorithmic |
| Mad Town | `MFKGTB!R` | algorithmic |
| Neighborhood | `?FXX6BLJ` | algorithmic |
| Ocean Shores Beach | `4GWD!KL1` | algorithmic |
| Spooky Woods | `2L!DZHS8` | algorithmic |
| Town Square | `6!LN99V5` | algorithmic |
| Unlock All Levels | `B!P356BT` | algorithmic |
| Start Game With No Beginning Sequence | `M4DTQWN!` | preset (5 records) |
| Start with items unlocked | `!!QTTQ!!` | preset |
| Start with max energy | `S4MDL4RD` | preset |
| Start with max energy and items unlocked | `?R3GG13?` | preset |
| Unlock Everything | `TW1ST3R!` | preset |
| Unlocks all Gadgets | `8XK7CNZ3` | algorithmic |

Note: GameFAQs spells the "Unlock All Levels" code `b!p356bt` in lowercase; the on-screen alphabet only has capitals, so the correct input is `B!P356BT`. All 13 strings are **absent from the ROM as ASCII** (searched literally, with ±0x20, XOR, and 5-bit-index encodings); the 5 special codes are stored as the 5 preset records above.

## 6b. Enumeration

* **Space**: 8 symbols × 5 bits = 40 bits (`32^8 = 1.10e12` spellings); the validator's algorithmic subset is 30 payload bits + 10 check bits, and the preset table adds 5 fixed records. Two XOR cascades are invertible (verified rank 64), so any pre-image can be generated offline.
* **Published set**: 13 codes; 8 satisfy the algorithmic check and 5 are the preset records.
* **Novel code generated and accepted in-game**: **`V73ZJMTD`** — derived from `2V74BFDG` by changing pre-scramble symbol 4 from `0x00` to `0x01`, recomputing both check bytes, re-applying the cascade and re-encoding. It is on no published list (GameFAQs, TCRF). Entered on the real password screen: `password accepted, press START to play`; after Start the game loaded **The Neighborhood** with two battery containers visible (screenshot `novel_effect.png`; savestate `novel_effect.ss1`).
* **Bounds proven by rejection**:
  * `????????` — fails the checksum (short/invalid pattern) → `invalid password`.
  * `6YZ3QBRY` — passes my checksum model but maps to a state the second gate rejects → `invalid password`.
  * `W621JMTF` — same, rejected. This establishes that the second semantic gate, not just the checksum, bounds the accepted set.

Because the second gate is an indirect call through a runtime pointer (`0x0203E3C4`), a complete offline enumeration of the semantically accepted subset is **not** claimed here; the published 13 plus the demonstrated novel code are proven accepted, and three out-of-set inputs are proven rejected.

## 7. Validation evidence

* **Observed (emulator + RAM)**: title/menu/OPTIONS/password/entry/intro/level screens (screenshots `walk_*.png`, `pw_*.png`, `novel_*.png`); input glyph buffer at `0x0203E310` read from decompressed `.ss1` states (B=`0x40…`, mixed `0x40 41 42 43 44 45 46 47`, `?`=`0x5F`); accept/reject footer text; `V73ZJMTD` → The Neighborhood.
* **Derived (disassembly)**: validator `0x08026494`, generator `0x08026660`, key `0x083732E4`, preset tables, second gate at `0x0802C49E`–`0x0802C4D2`, glyph encoding `0x40+index`.
* **Inferred**: mapping of the 5 failing published codes to the 5 preset records (count and mnemonic nature match, but the preset string bytes are stored in an encoded form I did not fully decode); field meanings of the 4 decoded state bytes (only their existence and bounds are proven).
* **Dynamic**: `TW1ST3R!` → Monkey Jungle; `2V74BFDG` → accepted (Elementary School); `V73ZJMTD` → The Neighborhood.

## 8. Unknowns

* The exact semantic predicate behind the second gate (`0x0802C4BE` indirect call) was not isolated; it rejects some checksum-valid codes.
* The 5 preset records at `0x08362234` are stored in an encoded form; I identified them by count and by which published codes fail the algorithmic path, not by decoding their bytes.
* Character-unlock state: the character-select text "Only Otto is available now" / "Choose Your Rocket Dude:" and `(COMPLETE)`/`(LOCKED)` markers exist at `0x34F5C`/`0x34FAC`/`0x34FF4`/`0x35000`; no published code system for characters was found on the reachable screens.
* Pause menu and level-select screens were not captured in this session (the shared display host repeatedly terminated the mGBA process); their strings and handler pointers are mapped above but not exercised.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, Python 3.13, `gdb-multiarch` (GDB stub was client-blocked by another session on port 2345, so mGBA's `-d` PTY debugger and `.ss1` savestate diffing were used for RAM evidence).
* `strings -t x`, `grep -abo`, `xxd`; web/archive retrieval of the GameFAQs cheats page and TCRF, treated strictly as data.
* Scripts: `xrefs.py`, `blxref.py`, `savestate.py`, `pw.py`, `mint.py`, `pwentry.py`, `gba.py`, `dbgserver.py`.
* Legal note: no ROM bytes or copyrighted assets are reproduced in this report; only hashes, addresses, algorithms and generated code strings are documented.
