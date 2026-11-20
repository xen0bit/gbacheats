# Spirits & Spells (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Spirits & Spells.gba` (same folder as this report) |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `SPIRITSPELLS` |
| Game code / maker | `AWNE` / `6U` |
| Version / fixed byte | `0x00` / `0x96` |
| Entry word | `0xEA000030` → `0x080000C8` (stock crt0, not a scene cracktro) |
| Header checksum / complement | `0x0000` / `0xED` |
| MD5 | `dce828e687f05511c1ad70e936b5ef25` |
| SHA-1 | `5b4764af4f7d0df0ae486f33bd905dc7` |
| SHA-256 | `379d2511b6cace8f5cb825660b2818db898d4e688547bf71816e027839ad7308` |

Phase 0: Nintendo-logo scan finds **exactly one** embedded GBA header (at file `0x0`). No appended trainer, no multi-game pack, no patched entry branch. Embedded splash text at ROM `0x083EAAF0` reads `HALLOWEEN / Jan 30 2003 18:41:51 / (C) WWW.MAGICPOCKETS.COM / NOT FOR RELEASE OR PUBLIC PERFORMANCE / PRESS ANY KEY TO CONTINUE` — a dated developer build of the retail image (file command confirms `AWNE6U, Rev.00`).

Developer: Magic Pockets; publisher DreamCatcher (from the splash and GameFAQs metadata).

## 2. Executive summary

The game has a genuine **developer-intended password system**, not a cheat-device surface. Main menu → **Password** opens a 7-slot keypad using 32 symbols `0123456789BCDFGHJKLMNPQRSTVWXZ/*`. Entering 7 characters and pressing A a further time calls a validator at `0x08345F48`; accepted passwords set a decoded state record (level index, difficulty-like fields, mode flag) and start the game at that level. A generator at `0x08345EC0` is the exact inverse and is reachable as an oracle.

All **14 published level passwords** (archived GameFAQs list) were verified: every one is accepted by the ROM's own validator. They are **not stored as literals** — each is computed from a mixed-radix payload plus a 6-bit XOR checksum, so no published string occurs anywhere in the ROM.

The published list is not the whole space. Using the game's own generator as an oracle I minted and confirmed:
- `/CMVCGZ` — payload level index `b5=0`, which **no published code uses** (published codes occupy `b5=1..14`); accepted.
- `GC0V3DC` — payload flag `b7=1`, which **no published code sets**; accepted; in-game screenshot shows a visibly different level/appearance from the published code `GH0V3GW` at the same `b5=1`.
- `GC0VCBC` (`b7=2`) and `*H2V7GV` (`b4=2`) — also accepted, both unpublished field combinations.

Bounds were proven by rejection: `HD1V3GT` (generated with out-of-range `b4=255`) is rejected; single-character mutations (`R6JGF90`, `0CMVCGZ`) and invalid checksum strings (`0000000`, `XXXXXXX`, `ZZZZZZZ`, `///////`) are rejected with return value 0 and a zeroed state record.

A debug level-name bank (15 entries `Level H011`…`Level H03B`) and `CACHEVERIFY` / `INITLEVEL: LEVEL ERROR` strings survive in the ROM, but no reachable debug menu was found: all four main-menu items (New Game, Options, Password, Training) and every sub-screen were walked. No button-code tables were found (`strings` has no debug/cheat/konami/unlock hits; key-mask prefix scan for common combos is zero).

## 3. How to reproduce

**Emulator:** mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`. Default SDL keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.

**Menu path:** boot → press A (Magic Pockets splash) → press Start → main menu → move down to **Password** → press A → on-screen password keypad with 7 empty slots → select each of the 7 symbols with arrows + A → press A once more to validate. On accept the intro/gameplay starts; on reject the game plays an error sound and clears the slots.

**Deterministic oracle (preferred for verification):** mGBA's CLI debugger (`mgba -3 -d`) makes the game's own functions callable:
1. Save a main-menu savestate in a GUI mGBA (`Shift+F1`).
2. Launch the CLI debugger and `load 1`; set `b/t 0x8346108` (password-screen entry), navigate to the Password screen, delete that breakpoint and set `b/t 0x8345F48` (validator) and `b/t 0x83465E6` (return).
3. Press A eight times (7 characters + validate) to hit the validator breakpoint; `r0` is a pointer to the 7-byte ASCII buffer (observed at `0x03007E4C` on the stack).
4. Overwrite the buffer with any 7 ASCII characters via `w/1`, then `c` to the return breakpoint. `r0 != 0` means accepted; the decoded record is at `0x03000BB0`.
5. To mint: at the validator breakpoint, clear the breakpoints, set the state record at `0x03000BB0`, call `0x8345EC0` with `r0` = an output buffer, `lr` = a breakpoint address, `cpsr=0x3F`, `pc=0x8345EC1`; read the 7-char string from the output buffer.

Helper scripts are in `/tmp/opencode/spiritsspells3/` (`oracle.py`, `pworacle.py`, `minter.py`, `verify_code.py`, `levelcheck.py`).

**Codes tested (all from the archived GameFAQs list):** `R6JGF91`, `GH0V3GW`, `D7JDN31`, `/6JT12S`, `PC5R05M`, `6C14X05`, `GB1G40P`, `PG7R05R`, `*2XZMC6`, `4HNZB44`, `4G7ZJ5R`, `4BQR85P`, `N/0RGFG`, `PBQZS5P` — all accepted.

**Web sources:** GameFAQs GBA cheats page via `web.archive.org` (3 captures, 2018–2025) gave the 14-code list and the "Hard Mode: beat the game once" unlockable. Direct GameFAQs and TCRF fetches returned HTTP 403. All fetched page text was treated as data, not instructions; no prompt-injection payload was encountered.

## 4. Address map

File offset = ROM address − `0x08000000`.

| ROM address | Kind | Meaning |
|---|---|---|
| `0x083EA258` | data, 32 bytes | Password alphabet `0123456789BCDFGHJKLMNPQRSTVWXZ/*` |
| `0x083EA21C` | data, 15×u32 | Pointer table to `Level H011`…`Level H03B` |
| `0x083EA168` | data | 15 NUL-terminated debug level names (`Level H011` … `Level H03B`, 12 bytes each) |
| `0x083EA27C` | data | Codec parameters: `0x65`, `15`, `10`, `0x2000`, `3`, `0xFFFFFFFF` … |
| `0x083EAAF0` | data | HALLOWEEN developer-build splash text |
| `0x083EA034` | data | `INITLEVEL: LEVEL ERROR` debug string |
| `0x083EA791` | data | `CACHEVERIFY: …` debug strings (7 entries) |
| `0x08345860` | Thumb fn | string → 5-bit-packed buffer (alphabet lookup) |
| `0x083458CC` | Thumb fn | packed buffer → 7-char string |
| `0x08345918` | Thumb fn | bit-swap across two bytes |
| `0x08345948` | Thumb fn | encode scramble (multi-pass bit permutation / XOR) |
| `0x08345B8C` | Thumb fn | decode scramble (inverse of above) |
| `0x0834CFA4` | Thumb fn | set bit field (`setbits`) |
| `0x0834D074` | Thumb fn | get bit field (`getbits`) |
| `0x08345DC0` | Thumb fn | mixed-radix pack value |
| `0x08345DD8` | Thumb fn | mixed-radix extract field (mod+div by table) |
| `0x08345E14` | Thumb fn | initial pack of the 5 state fields |
| `0x08345E60` | Thumb fn | 6-bit XOR checksum |
| `0x08345EC0` | Thumb fn | **generator**: state record → password string |
| `0x08345F48` | Thumb fn | **validator**: password string → accept/reject + state record |
| `0x08346108` | Thumb fn | password-screen UI (keypad, 7 slots, input handling) |
| `0x083475A0` | Thumb fn | accept path: copies decoded fields into game globals |
| `0x0834568C` | Thumb fn | debug 15-level selector (copies level-name pointer table) |
| `0x03000BB0` | IWRAM | decoded state record: word `+0`, bytes `+4..+7` |
| `0x03000BA4` | IWRAM | checksum width byte = `0x06` (6 bits) |
| `0x03000C30` | IWRAM | checksum bit-count byte = `0x1D` (29 bits) |
| `0x03007E4C` | IWRAM stack | observed 7-byte ASCII input buffer at validator entry |
| `0x03002E30` | IWRAM | game global receiving level index `b5` on accept |
| `0x03000870` | IWRAM | game global receiving payload word ×5 |

## 5. Algorithm

Precise enough to reimplement, with the scramble delegated to the ROM oracle (it is a long multi-pass bit permutation, not a simple XOR):

```
ALPHABET = "0123456789BCDFGHJKLMNPQRSTVWXZ/*"        # 32 symbols
index(c) = position of c in ALPHABET                  # 0..31, 5 bits

encode_payload(state):
    W, b4, b5, b6, b7 = state                        # from 0x03000BB0
    buf = mixed_radix_pack([b4,b5,b6,W,b7])           # 0x08345E14 / 0x08345DC0
    check = (((xor_of_bits(buf, 29)) ^ 0x3B) + 0x35) & 0x3F
    setbits(buf, check_field, check, 6)
    scramble(buf)                                     # 0x08345948
    return "".join(ALPHABET[get5(buf,i)] for i in 0..6)

validate(code):                                       # 0x08345F48
    buf = [index(c) for c in code] packed 5 bits each # 0x08345860
    inverse_scramble(buf)                             # 0x08345B8C
    if getbits(buf, check_field, 6) != checksum(buf): return 0
    b4,b5,b6,W,b7 = mixed_radix_extract(buf)          # 0x08345DD8
    if b4 >= bound: return 0                          # product/range table check
    stored_word = (W >> 4) << (W & 15)                # final transform at 0x08346014
    write {stored_word,b4,b5,b6,b7} to 0x03000BB0
    return 1
```

`xor_of_bits` XORs the low-level bit buffer: full bytes `buf[0..(29>>3)-1]` plus the significant bits of the partial byte, then `^ 0x3B`, `+ 0x35`, masked with `(1<<6)-1`. Checksum width and bit count are read from IWRAM bytes at `0x03000BA4` (`6`) and `0x03000C30` (`29`), i.e. they are data-driven, not hard-coded.

`b5` is a radix-15 field (`0..14`): minting with `b5=15` produced a decoded record of `b4=1, b5=0`, i.e. a carry into `b4` — proven with generated codes `/H1V3GQ` (input `b5=14`) and `HBLVCGN` (input `b5=15`). This matches the 15 debug level names and the 14 published level indices.

The generator input word must be the **pre-transform** value `W`: feeding `W=0x17B3` reproduces `R6JGF91` exactly (validator stores `(W>>4)<<(W&15) = 0x0BD8`), and `W=0x1F90` reproduces `GH0V3GW` (stores `0x01F9`).

## 6. Tables

**Alphabet / keypad** (`0x083EA258`; on-screen grid rows of 8):

```
row0: 0 1 2 3 4 5 6 7
row1: 8 9 B C D F G H
row2: J K L M N P Q R
row3: S T V W X Z / *
```

Alphabet index = `row*8 + col`. Vowels A/E/I/O/U/Y and `Q` is present while `Y` is not; the grid matches the string byte-for-byte.

**Published 14 codes and their decoded records** (all verified accepted):

| Level (GameFAQs) | Code | W-stored | b4 | b5 | b6 | b7 |
|---|---|---|---|---|---|---|
| Cemetery | `GH0V3GW` | 0x01F9 | 0 | 1 | 2 | 0 |
| The foggy bridge | `/6JT12S` | 0x050C | 0 | 2 | 3 | 0 |
| The frozen crypts | `6C14X05` | 0x08A0 | 1 | 3 | 4 | 0 |
| The Bogeyman | `R6JGF91` | 0x0BD8 | 1 | 4 | 5 | 0 |
| The Haunted house | `GB1G40P` | 0x0C78 | 1 | 5 | 5 | 0 |
| The nests | `*2XZMC6` | 0x12D0 | 7 | 6 | 9 | 0 |
| The endless corridors | `D7JDN31` | 0x18B0 | 10 | 7 | 9 | 0 |
| The tall tower | `N/0RGFG` | 0x20C0 | 13 | 8 | 9 | 0 |
| The Vampire | `PBQZS5P` | 0x22E0 | 16 | 9 | 9 | 0 |
| The secret laboratory | `4G7ZJ5R` | 0x22E0 | 16 | 10 | 9 | 0 |
| The robot factory | `4HNZB44` | 0x2320 | 16 | 11 | 9 | 0 |
| The forbidden experiment room | `PC5R05M` | 0x2380 | 16 | 12 | 9 | 0 |
| The soul reservoirs | `4BQR85P` | 0x2380 | 16 | 13 | 9 | 0 |
| The Mad Scientist | `PG7R05R` | 0x2380 | 16 | 14 | 9 | 0 |

**Encoder parameters:** alphabet length 32 (5 bits/symbol); code length 7 (35 bits); checksum 6 bits over 29 bits; `b5` radix 15; word transform `(W>>4)<<(W&15)`; generator field order (from `0x08345E14`) is `b4, b5, b6, word, b7`.

## 6b. Enumeration

**Space definition.** Raw input space = `32^7 = 34,359,738,368` strings. A 6-bit checksum (`0x03000BA4=6`) makes roughly `2^35 / 2^6 = 536,870,912` strings checksum-valid, further reduced by the field range check on `b4` (product table consulted at `0x08345FBE`) and by `b5` being radix 15. Validator model: implemented as described in §5, with the scramble step used as a ROM oracle; it agrees with the game on every code tested (14 accepted published codes, 4 accepted novel codes, 7 rejected codes).

**Complete published set:** 14 codes (archived GameFAQs); every literal is absent from the ROM as ASCII because codes are computed, and every one was confirmed accepted by the ROM validator. No other published list was found (TCRF/GameFAQs direct fetch = 403; archived GameFAQs used instead).

**Novel codes generated that appear in no published list** (minted with the game's generator, then re-validated through the real validator and in the emulator):

| Novel code | Generator input fields | Decoded record | In-game proof |
|---|---|---|---|
| `/CMVCGZ` | W=0x1F90, b4=0, b5=0, b6=2, b7=0 | word 0x01F9, b4=0, **b5=0**, b6=2, b7=0 | accepted (r0=1); `b5=0` is outside all 14 published records |
| `GC0V3DC` | W=0x1F90, b4=0, b5=1, b6=2, b7=1 | word 0x01F9, b5=1, b6=2, **b7=1** | accepted; gameplay screenshot `play89_c.png` shows daytime/blue-sky level, visibly different from published `GH0V3GW` (night/moon) at the same b5 |
| `GC0VCBC` | same with b7=2 | **b7=2** | accepted (r0=1) |
| `*H2V7GV` | W=0x1F90, b4=2, b5=1, b6=2, b7=0 | **b4=2** | accepted (r0=1) |

`b5=0` and `b7∈{1,2}` and `b4=2` occur in none of the 14 published records (published `b4∈{0,1,7,10,13,16}`, `b5∈{1..14}`, `b7=0` always).

**Bounds proven by rejection** (each returns `r0=0` and leaves the state record zeroed; observed via the validator breakpoint):

| Input | Why it must fail | Result |
|---|---|---|
| `HD1V3GT` (minted with b4=255) | out-of-range field | **rejected** |
| `R6JGF90` (last symbol of a published code changed) | checksum mismatch | rejected |
| `0CMVCGZ` (first symbol of a novel code changed) | checksum mismatch | rejected |
| `0000000` | checksum mismatch | rejected |
| `XXXXXXX` | checksum mismatch | rejected |
| `ZZZZZZZ` | checksum mismatch | rejected |
| `///////` | checksum mismatch | rejected |
| `b5=15` mint (`HBLVCGN`) | field overflow — did not reject; carried into b4 (`b4=1,b5=0`), proving the radix-15 bound | accepted with carried payload (bound characterised, not a rejection) |

Length is bounded by the UI: exactly 7 slots; no 8th character can be entered.

**Negative surfaces (bounded):** no button-code table (`strings` has zero debug/cheat/konami/unlock hits; key-mask prefix scan for `(1,2,8)` and `(L,R,Start)` = 0); no reachable hidden menu (all four main-menu items and every Options/Password/New-Game sub-screen walked); the debug level-name bank at `0x083EA168` and `CACHEVERIFY` strings are present but no reachable caller was found. Published "Hard Mode: beat the game once" is a save-progress unlock, not a code.

## 7. Validation evidence

- **Observed (emulator/RAM):** title screen; main menu with 4 items; Options with SFX/Music/Key config; password keypad (32 symbols, 7 slots) at `0x08346108`; 8th A press calls validator with ASCII buffer at `0x03007E4C`; all 14 published codes accepted; 4 novel codes accepted; 7 rejections; decoded state records read at `0x03000BB0`; generator reproduced `R6JGF91` / `GH0V3GW` byte-for-byte when given the pre-transform word; gameplay screenshots after `GC0V3DC` and `GH0V3GW` differ.
- **Derived (disassembly):** validator/generator/checksum/scramble addresses and roles; state-record layout; 6-bit checksum formula; `(W>>4)<<(W&15)` word transform; `b5` radix 15; alphabet table; debug level-name bank.
- **Inferred:** exact semantics of `b4` and `b6` (difficulty-like and world-like fields) are inferred from their correlation with level names in the published list, not proven by a dedicated gameplay test; the scramble permutation was not reimplemented offline — the ROM itself was used as the oracle, which is sufficient for generation and validation but not a standalone reimplementation.

## 8. Unknowns

- The multi-pass bit scramble (`0x08345948` / `0x08345B8C`) was treated as an oracle rather than reimplemented as a standalone function; a from-scratch encoder would need to decode those passes.
- Gameplay meaning of `b4`, `b6`, and `b7` beyond the observed level/appearance differences was not exhaustively played through (e.g. whether `b7=1` is a distinct mode or an alternate level variant).
- Two rejection tests (`GHOV3GW` with the letter O, `AAAAAAA`) hit a debugger timing fault and were not recorded; the rejection conclusion rests on the seven successful cases above.
- No reachable caller of the debug level-select code at `0x0834568C` was found; it is reported as present-but-unreached, not proven absolutely unreachable by every possible input sequence.
- Hard Mode unlock (`beat the game once`) was not exercised end-to-end.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for raw ROM disassembly; Python + `struct` for literal/pointer scans.
- `strings -t x`, `grep -abo`, `xxd` for reconnaissance; `web.archive.org` for the GameFAQs cheat list.
- mGBA 0.10.5 GUI under `Xvfb :316` with `openbox`, `xdotool` for input, `scrot`/ImageMagick for screenshots.
- mGBA CLI debugger (`-d`) over a pty: `r/1|2|4`, `w/1|2|4`, `w/r`, `b/t`, `c`, `status` — used as the validator/generator oracle (guide §16.19).
- Helper scripts: `/tmp/opencode/spiritsspells3/{oracle,pworacle,minter,verify_code,levelcheck,ingame,visual,phase0,static1,static2,blscan}.py`.
- No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms and self-generated codes are published.
