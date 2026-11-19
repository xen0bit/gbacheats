# Rock 'Em Sock 'Em Robots (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rock 'Em Sock 'Em Robots.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `ROCKEMSOCKEM` |
| Game code / maker | `BR7E` / `20` |
| Version / fixed byte | `0x00` / `0x96` |
| Complement / header checksum | `0x5C` / `0x0000` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0) |
| MD5 | `567b56a215ff295aca69ac85c4f08273` |
| SHA-1 | `77cde5839dd0dbec2dfda4062caab969b7308672` |
| SHA-256 | `d762c24fd31151d6ec38d91bca3215ecbeb0ebfc6a1c4cb59231b733b494b53b` |

Embedded-header scan: the 156-byte Nintendo logo occurs **exactly once**, at file offset `0x4` (header `0x0`). This is a single retail image, not a multiboot/2-in-1 pack. The entry word is the stock `b 0x080000C0` and the first instructions are a normal crt0; no cracktro, appended trainer, or patched entry was found. Header checksum `0x0000` is the usual rebuilt-header artifact (guide §16.1) but does not indicate a cheat trainer here.

Build/credits strings (0x080573C8–0x080576AF): Full Fat (programming Ben Wilcock, engine Andrew Docking), Destination Software Inc., Mattel license.

## 2. Executive summary

The game has a **developer-intended password system** with a 31-symbol on-screen keypad and 6-symbol codes. It is **algorithmic, not a lookup table**: none of the ten published codes appears anywhere in the ROM as plaintext. The alphabet is `BCDFGHJKLMNPQRSTVWXYZ0123456789` (no vowels), at `0x0804EF3C`.

The validator is a 6-byte decoder at `0x0802AAE4`. It packs five symbols into a 16-bit payload, XOR-scrambles it with `0x123F`, derives two further fields (`valB`, `valC`) from the remaining nibbles, and checks a checksum formed from `c4` bit 4 and all 5 bits of `c5` against `(c0^c1^c2^c3)&0x3F`. All nine unambiguous published codes satisfy this decoder exactly, which validates the model.

The whole space is `31^6 = 887,503,681` strings, of which **14,314,576 (1.61 %) are checksum-valid**. The payload fields are `valA` (16 bits), `valB` (4 bits: 0–8 select a robot, 9 = "Game Finished"), and `valC` (4 bits). Every published code has `valC = 0`; `valC = 4` enables a hidden progress-update branch at `0x08029EE0` that no published code can reach. Two novel codes (`3CTNJS`, `3CTNFS`) were generated offline, typed through the real keypad, accepted with "PASSWORD OK!", and their exact 6 bytes were read back from RAM. A bad-checksum code (`3CTNKB`) was rejected with "PASSWORD INVALID!", proving the checksum bound.

No button-code sequence and no hidden debug menu were found; the five menu modes, the Title Fight submenu, options, credits, all selection screens, the fight, and the pause menu were walked on-screen. The ROM does contain leftover debug/assertion strings, but no reachable screen exposes them.

## 3. How to reproduce

* Emulator: `mgba -3` under Xvfb on `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, openbox window manager. mGBA SDL keymap used: A=`x`, B=`z`, Start=`Return`, D-pad=arrow keys. Hold each key ~60 ms with a ~220 ms gap (longer holds double-step the menus).
* Boot path: health warning → Mattel legal screen → title ("PRESS START") → **Select Game Mode** carousel.
* Main carousel (5 entries, wraps): `CLASSIC` → `VERSUS` → `TITLE FIGHT` → `ENTER PASSWORD` → `OPTIONS`.
* `TITLE FIGHT` opens a submenu: `NEW GAME` / `CONTINUE GAME` / `ENTER PASSWORD`. Both `ENTER PASSWORD` entries lead to the same 6-slot keypad.
* Keypad controls: LEFT/RIGHT select a slot; UP/DOWN cycle the symbol in that slot; A submits; B backs out.
* To test a code, set all six slots, press A, and read the result line: `PASSWORD OK!` or `PASSWORD INVALID!`.
* Savestate RAM reading: Shift+F1 saves `Rock 'Em Sock 'Em Robots.ss1`; it is a PNG with a `gbAs` zlib chunk. `zlib.decompress` yields 397,312 bytes with IWRAM at state offset `0x19000` (maps to `0x03000000`) and EWRAM at `0x21000` (maps to `0x02000000`).

Codes verified on screen (all typed, not memory-patched):

| Code | Result | Notes |
|---|---|---|
| `LSTL2B` | PASSWORD OK! | Published "Unlock Black Bruiser" |
| `3CTNKS` | (offline verified) | Published "Game Finished" |
| `3CTNJS` | PASSWORD OK! | **novel**, valC=1 |
| `3CTNFS` | PASSWORD OK! | **novel**, valC=4 (hidden branch) |
| `3CTNKB` | PASSWORD INVALID! | bad checksum (bounds proof) |

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`) unless marked RAM.

| Item | Address | Evidence |
|---|---|---|
| Password alphabet (31 bytes) | `0x0804EF3C` | Derived — literal `BCDFGHJKLMNPQRSTVWXYZ0123456789` |
| **6-byte decoder / validator** | `0x0802AAE4` | Derived — fully disassembled; BL xrefs from 6 sites |
| Encoder (values → alphabet chars) | `0x0802AB78` | Derived — converts 6 raw values to 6 chars + NUL |
| Single-char alphabet lookup | `0x0802ABA8` | Derived |
| Decoder caller, password screen result | `0x080330C8` / `0x08033174` | Derived — shows OK/INVALID, sets accepted flag |
| Decoder caller, "Continue Game" copy | `0x08032FF4` / `0x080305C` | Derived — copies 8 bytes to user data |
| valA / valB / valC getters | `0x08029CBC` / `0x08029CF8` / `0x08029D2C` | Derived |
| **valC==4 hidden branch** | `0x08029EE0` (in fn `0x08029EC0`) | Derived — `cmp r0,#4` on valC |
| valB==9 "Game Finished" test | `0x08037CC4` | Derived — `cmp r1,#9` → return 1 |
| Unlock dispatch function | `0x08037C30` | Derived |
| Password award generator | `0x08037EE0`, hash `0x0803BAAC` | Derived |
| Debug strings | `PASSWORD OK!` `0x080566E0`; `PASSWORD INVALID!` `0x080566F0`; `New Password` `0x08058C04`; `Enter Password` `0x080554EC`, `0x080566A8`, `0x0804F8BC` | Derived |
| Live keypad entry buffer (6 bytes) | EWRAM `0x02000CDC` | Observed — UP on slot 0 changed `0x13`→`0x12` |
| Decoder input snapshot (6 bytes) | IWRAM `0x03000224` | Observed — held exact typed values |
| Sprites/text for robot names | `0x0804EE68`–`0x0804EF00` (10 names) | Derived |

## 5. Algorithm

Let the six keypad symbols be `c0..c5`, each an index `0..30` into `AL = "BCDFGHJKLMNPQRSTVWXYZ0123456789"`.

```
rawA   = c0 | (c1<<5) | (c2<<10) | ((c3 & 1)<<15)      # 16-bit
valA   = rawA ^ 0x123F
valB   = (c3 >> 1) ^ 12                                # 4-bit: 0..15
valC   = (c4 & 0x0F) ^ 7                                # 4-bit
stored = (c4 >> 4) | (c5 << 1)                          # 6-bit field
calc   = (c0 ^ c1 ^ c2 ^ c3) & 0x3F
accept = (stored == calc)
```

Rejected → return 0 ("PASSWORD INVALID!"). Accepted → return 1 and (depending on caller) copy the six raw bytes into the user-data password record, then show "PASSWORD OK!".

Notes on the packing (all confirmed by disassembly at `0x0802AAE4`):

* `c0`, `c1` contribute 5 bits each to `valA`; `c2` contributes the next 5; `c3` bit 0 is the top bit. `0x123F` scrambles bits 0–5, 9 and 12.
* Every published code has `c2 = 15` (`T`), so `valA` bits 10–15 are always the constant `11` after the XOR.
* Every published code has `c3` even (`c3&1 == 0`) and `c4 & 0x0F == 7` (`valC == 0`).
* `c3` bits 1–4 are **not** a single bit: `c3>>1` yields a full 4-bit value. Correcting this was necessary to make the published robot codes decode consistently (`valB` then takes the values 0–9).
* Because `c0..c3 < 32`, `calc = c0^c1^c2^c3` never exceeds 31. Therefore `c5` is restricted to `0..15` for any valid code and `c4` bit 4 must equal `calc & 1`.
* The validator called from the password screen passes `r1=r2=r3=0`, so that call is a pure checksum check; the extracted fields are consumed later by the getters (`0x08029CBC` etc.) when a game mode reads the stored password.

Python reimplementation used for all offline checks:

```python
AL = "BCDFGHJKLMNPQRSTVWXYZ0123456789"
def decode(s):
    c = [AL.index(x) for x in s]                 # raises on out-of-alphabet
    A = (c[0] | c[1]<<5 | c[2]<<10 | (c[3]&1)<<15) ^ 0x123F
    B = (c[3] >> 1) ^ 12
    C = (c[4] & 0xF) ^ 7
    return A, B, C, ((c[4]>>4)|(c[5]<<1)) == ((c[0]^c[1]^c[2]^c[3])&0x3F)
```

## 6. Tables

### Published codes verified against the ROM

All literals were searched with `grep -abo`-equivalent byte search: **none are stored in the image**, confirming an algorithmic validator. Decoded with the model above:

| Published effect | Code | c[] | valA | valB | valC | checksum |
|---|---|---|---|---|---|---|
| Game Finished | `3CTNKS` | 24,1,15,10,7,14 | 11783 | 9 | 0 | 28/28 ✓ |
| Unlock Black Bruiser | `LSTL2B` | 8,14,15,8,23,0 | 12279 | 8 | 0 | 1/1 ✓ |
| Unlock Blue Bomber | `B5T32J` | 0,26,15,24,23,6 | 11647 | 0 | 0 | 13/13 ✓ |
| Unlock Green Grappler | `NMTZKQ` | 10,9,15,20,7,12 | 12053 | 6 | 0 | 24/24 ✓ |
| Unlock Orange Oppressor | `2XT9KN` | 23,18,15,30,7,10 | 11368 | 3 | 0 | 20/20 ✓ |
| Unlock Pink Pummeller | `6QT1KK` | 27,12,15,22,7,7 | 12196 | 7 | 0 | 14/14 ✓ |
| Unlock Purple Pyro | `02TX2T` | 21,23,15,18,23,15 | 11466 | 5 | 0 | 31/31 ✓ |
| Unlock Silver Stretcher | `GZTV2K` | 4,20,15,16,23,7 | 11451 | 4 | 0 | 15/15 ✓ |
| Unlock Yellow Yahoo | `W8T52Q` | 17,29,15,26,23,12 | 11662 | 1 | 0 | 25/25 ✓ |
| Unlock Brown Bully | `J[]T7KH` | — | — | — | — | **published string corrupt** |

`J[]T7KH` (GameFAQs/TCRF-family mirrors) is 7 glyphs and contains two characters outside the 31-symbol alphabet, so it cannot be typed. Restricting the search to `c0=J`, `c2=T`, `c4=K`, `valB=2` yields `J9T8KH` as the closest checksum-valid 6-symbol spelling (J,9,T,8,K,H — matches 5 of the 6 visible glyphs). Marked **Inferred**; not re-entered on screen.

`valB` maps 0–8 to the nine unlockable robots and 9 to "Game Finished"; Red Rocker is the default at game start. Note a discrepancy: after entering published `LSTL2B` (labelled "Black Bruiser"), the CLASSIC champion carousel displayed **BLUE BOMBER** as the newly selectable champion. Published robot labels should therefore not be trusted (guide §16.15).

### Field layout

| Symbol | Bits | Meaning |
|---|---|---|
| `c0` | 5 | valA bits 0–4 (scrambled by XOR) |
| `c1` | 5 | valA bits 5–9 (scrambled) |
| `c2` | 5 | valA bits 10–14; always 15 (`T`) in all published codes → fixed format field |
| `c3` bit 0 | 1 | valA bit 15; always 0 in published codes |
| `c3` bits 1–4 | 4 | `valB ^ 12` → robot/flag selector (0–9) |
| `c4` bits 0–3 | 4 | `valC ^ 7` → hidden mode field; always 0 in published codes |
| `c4` bit 4 | 1 | checksum bit 0 |
| `c5` bits 0–4 | 5 | checksum bits 1–5 |

## 6b. Enumeration

**Space size.** `31^6 = 887,503,681` typable strings. Acceptance requires `c5 = calc>>1` and `c4>>4 = calc&1` where `calc = c0^c1^c2^c3 ∈ [0,31]`. Counting exactly: there are `(31^4+1)/2 = 461,761` four-tuples with even `calc` (16 legal `c4` values each) and `(31^4-1)/2 = 461,760` with odd `calc` (15 legal `c4` values each), giving

```
461,761*16 + 461,760*15 = 14,314,576 valid codes  (1.6129 % of the string space)
```

For each accepted string `c5` is uniquely determined, so there are no free checksum aliases. The semantic payload is 19 bits (valA low 10 + valA bit15 + valB 4 + valC 4); the other 11 bits are the fixed `c2` field and the checksum.

**Novel codes generated and accepted in-game** (neither appears on GameFAQs, VGChartz, TCRF or any wiki consulted):

| Code | c[] | valA | valB | valC | Result | RAM proof |
|---|---|---|---|---|---|---|
| `3CTNJS` | 24,1,15,10,6,14 | 11783 | 9 | 1 | PASSWORD OK! | IWRAM `0x03000224` = `18 01 0f 0a 06 0e` |
| `3CTNFS` | 24,1,15,10,3,14 | 11783 | 9 | 4 | PASSWORD OK! | IWRAM `0x03000224` = `18 01 0f 0a 03 0e`; EWRAM `0x02000CE0` changed `06`→`03` |

`3CTNJS` keeps the published Game Finished payload (`valA`, `valB`) but sets `valC=1`, a value no published list exercises. `3CTNFS` sets `valC=4`, which at `0x08029EE0` (`cmp r0,#4` in function `0x08029EC0`, reached from `0x08037C7C`) is the gate for a hidden progress-update path that writes back into the password record and returns a non-zero unlock result. This branch is unreachable with any published code because all of them have `valC=0`.

**Bounds proven by rejection.** `3CTNKB` = `[24,1,15,10,7,0]` has `stored = (7>>4)|(0<<1) = 0` but `calc = 24^1^15^10 = 28`. Entered through the keypad with the live buffer verified as `[24,1,15,10,7,0]`; the game displayed **PASSWORD INVALID!** and returned to the keypad. This proves the checksum layer independently of the field layers.

**Negative results bounded.** Buttons codes: the five menu screens, Title Fight submenu, options, credits, both player-select screens, arena select, the fight HUD and the pause menu (CONTINUE / QUIT BATTLE only) were walked with screenshots; no sequence-gate or debug menu was exposed. Static keyword sweeps for `password|cheat|code|secret|unlock|debug|robot|hidden` across the whole 4 MiB found only UI/debug logging strings and the alphabet; no hidden menu table or button-mask table was present. The debug-looking strings (`UIDUMP:`, `currentCharDataBlock = %d`, `NBUNLOCKED = %d`, `Unlock me!`, `Assertion failed:`) are leftover logging with no reachable UI in the walked screens.

## 7. Validation evidence

* **Observed** — emulator screenshots and savestate RAM reads: main carousel (5 modes), Title Fight submenu, OPTIONS, CREDITS, `SELECT YOUR CHAMPION` in fresh state (only Red Rocker portrait; other slots blank), `VERSUS SELECT` (all 10 portraits), `ARENA SELECT` (Quarry), `PREPARE TO FIGHT`, live fight HUD (60 s timer), `GAME PAUSED` (CONTINUE / QUIT BATTLE).
* **Observed** — keypad entry buffer at EWRAM `0x02000CDC` changed with UP/DOWN and held the exact target bytes for every code typed; IWRAM `0x03000224` held the accepted code's six bytes; `PASSWORD OK!` for `LSTL2B`, `3CTNJS`, `3CTNFS`; `PASSWORD INVALID!` for `3CTNKB`.
* **Derived** — the decoder algorithm, the alphabet, the field layout, the exact valid-code count, and the `valC==4` / `valB==9` branches, all from disassembly and verified offline against nine published codes.
* **Inferred** — the exact effect of `valC=1` and `valC=4` beyond acceptance/storage (the hidden branch at `0x08029EE0` was read but not single-stepped to its final state write); the corrected spelling `J9T8KH` of the corrupt Brown Bully code; the mapping of `valB` values 0–8 to specific robot names (published labels disagree with one observed champion-select label).

## 8. Unknowns

* The `valC==4` branch (`0x08029EC0`) was identified and reached with an accepted code, but its full state transition (which progress fields it writes and when the game invokes it) was not traced to a visible outcome.
* Whether `valB=9` ("Game Finished") unlocks the entire roster could not be isolated: `VERSUS SELECT` already lists all 10 robots in a fresh, code-free session, and a clean before/after for the CLASSIC/TITLE FIGHT roster was obtained only for `LSTL2B`.
* The per-robot `valA` low-10-bit values look like a scramble/serial; their generator (`0x0803BAAC`) was located but not fully reversed.
* The published Brown Bully literal is corrupt; `J9T8KH` is a best-fit correction, not an accepted on-screen confirmation.
* No GameShark/CodeBreaker or raw memory-edit codes were investigated (out of scope).

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
* Capstone 5.0.7 / Python 3 for BL-target scans, literal-pointer scans and the validator reimplementation.
* `strings -a -t x`, `xxd`, `grep -abo` for recon and literal verification.
* `mgba -3` (mGBA) on Xvfb `:315` with openbox and `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST key events; `scrot` + ImageMagick `convert`/`montage` for screenshots.
* Custom helpers in `/tmp/opencode/rockemsockem/`: `gba.py` (focus/key/screenshot), `ram.py` (savestate `gbAs` zlib parser + address translators), `keypad.py` (types a code through the on-screen keypad and verifies each slot by savestate RAM read).
* mGBA's GDB stub was unavailable because TCP port 2345 was already held by another process; per guide §16.13, savestate RAM diffing was used instead. mGBA's stub-free CLI debugger (`-d`) was evaluated but not required.

## 10. Legal note

No ROM image, extracted graphics, audio, or game text is redistributed here. Only hashes, addresses, algorithms, and original analysis tools/findings are published.
