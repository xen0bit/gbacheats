# Iridion II (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Iridion II/Iridion II.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `IRIDIONII` |
| Game code / maker | `AI2E` / `5G` |
| Version | 0x00 |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Header checksum / complement | `0x0000` / `0x34` |
| MD5 | `553e8c9a80190617ec13fa2a06487f2d` |
| SHA-1 | `3d9a8af95a636be82e1af184df2110f20e170824` |
| SHA-256 | `8f89c1ab8fb52f302dbed6e57f163918101470bce8f6442b4ffd19153f970449` |

Embedded-header scan: the 156-byte Nintendo logo occurs **once**, at file offset `0x4`. This is a single 8 MiB retail image, not a multi-game pack. Entry word is the stock branch and there is no appended trainer or cracktro; the `0x0000` header checksum is the normal rebuilt-header artifact. No patch/trainer present.

## 2. Executive summary

Iridion II has a genuine developer-intended **password system** with two layers:

1. **Ten hard-coded special codes** (`4RC8!`, `CH4LL`, and eight `!…!` cheat codes) compared by a `strcmp` chain at `0x08007442`–`0x08007608`.
2. An **algorithmic 5-symbol password** for progress (level/difficulty/state) — the published "levels beaten" lists are *not* stored as literals in the ROM. The decoder at `0x0800E35C` implements: 32-symbol no-vowel alphabet → 25-bit base-32 pack → 25-bit bit permutation → XOR `0x0102A6AA` → six bit-fields + a 4-bit checksum.

The on-screen keyboard alphabet is exactly 32 symbols: `BCDFGHJKLMNPQRSTVWXYZ0123456789!` (no vowels). The accepted space is **860,160 distinct 5-character strings** (53,760 field tuples × 16 unused-bit aliases) out of `32^5 = 33,554,432`.

A novel code, `RCPHX` (difficulty Ace, all other fields zero), absent from every published list, was minted from the recovered encoder, entered on the real password screen, accepted, and confirmed in RAM: save slot `+22 = 0x02`, `+24 = 0x01`, all other fields zero. Bounds were proven by in-game rejection of a bad-checksum string (`RCPHC`) and an out-of-range-field string (`TGPHV`, f3=5).

Published literals were verified: all ten special codes appear in a table at `0x0804319C`–`0x080431F3`; 4RC8!, CH4LL and !S3CR3TS! were entered in the emulator. Several published-list transcription errors were identified (`O` vs `0`, `!0BJ!` vs `!0BJS!`, and an invalid Advanced-L14 entry `9!H84`).

The sibling image analysed concurrently is a **different game**: `Iridion3D` (MD5 `f88df40fedb9d31a6e59dba4a9be1b2a`), whose gallery password is `*G4LL3RY*`. It shares the Shin'en developer/staff credits but **nothing** in the password system, code table, alphabet, or addresses. No cross-contamination: this report was derived solely from the `AI2E` image.

## 3. How to reproduce

Emulator: mGBA (SDL), `Xvfb :318`, `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, `-3` scale, `mgba -g` for the GDB stub.
Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys 60–150 ms.

Path: boot → wait through the story intro → **PRESS START** → title → Start → main menu (`NEW GAME` / `PASSWORD`) → Down, A → password screen. On-screen keyboard is 8 columns × 4 rows; cursor starts on `B`; A sets a character, B deletes, arrows move; after 5 characters press Down to reach `Confirm`, then A.

Codes tested in-game:
* `4RC8!` → accepted; menu expands to STORY / ARCADE / CHALLENGE / Gallery / Jukebox / Credits.
* `CH4LL` → accepted; same unlocked main menu.
* `!S3CR3TS!` → accepted; byte `!S3CR3TS!` present in input buffer at `0x03000042`.
* `RCPHX` (novel) → accepted; RAM proof below.
* `RCPHC` (bad checksum) → `Invalid Password! / Try Again`.
* `TGPHV` (f3=5, out of range) → `Invalid Password! / Try Again`.

Screens walked with RAM/observation: title with jukebox overlay, main menu pre- and post-unlock, password keyboard, invalid-password screen, difficulty select (Starter/Advanced/Ace Pilot), Arcade and Challenge gameplay, pause menu (Music Volume / FX Volume / Restart / Quit Game), Game Over. A debug label `PRELIMINARY MENU LAYOUT` and a cheat-list title `CHEAT-CHEAT-CHEAT-CHEAT` exist in the ROM (see §8) but no player-reachable entry point was found.

## 4. Address map

All file offsets are ROM addresses minus `0x08000000`.

| Address (ROM) | Meaning |
|---|---|
| `0x08043158` | 32-symbol alphabet, UTF-16LE `BCDFGHJKLMNPQRSTVWXYZ0123456789!` |
| `0x087DC154` | second copy of the same alphabet (8-bit, used by decoder) |
| `0x087DC175` | 25-byte bit-permutation table (see §6) |
| `0x0800E43C` | literal pool: XOR key `0x0102A6AA` |
| `0x0804319C` | `4RC8!` |
| `0x080431A4` | `CH4LL` |
| `0x080431AC` | `!S3CR3TS!` |
| `0x080431B8` | `!B1GH34D!` |
| `0x080431C4` | `!M1CR0!` |
| `0x080431CC` | `!SH1P2!` |
| `0x080431D4` | `!G4X!` |
| `0x080431DC` | `!R0T8!` |
| `0x080431E4` | `!L04D!` |
| `0x080431EC` | `!0BJS!` |
| `0x08007442`–`0x08007608` | special-code validator (`strcmp` at `0x08017EC4`) |
| `0x0800E35C` | level-password decoder (returns 1 on success) |
| `0x08006BE2`, `0x0800761A` | the two BL call sites of the decoder |
| `0x08017E98` | strlen; `0x0803D2B4` = memcpy |
| `0x0804350C` | `PRELIMINARY MENU LAYOUT` debug label; accessor `0x0800BD6C` called from `0x0800AF4A` |
| `0x08044168` | `CHEAT-CHEAT-CHEAT-CHEAT`; referenced at `0x0801395A`, `0x08013E70` |
| `0x080435B9` | orphan string `1sN9g` (no code xref found) |

RAM (IWRAM):

| Address | Meaning |
|---|---|
| `0x0300006C` | current save-slot index (observed 0) |
| `0x03000040 + 29*slot` | save-slot base for this state machine |
| `0x03000042 + 29*slot` | password input buffer (NUL-terminated, observed ASCII) |
| slot `+18..+21` | field f4, stored as a 32-bit value |
| slot `+22` | f1 — difficulty (0=Easy, 1=Advanced, 2=Ace) |
| slot `+23` | f3 — 3-bit field, range 0..4 (galaxy index, inferred) |
| slot `+24` | accepted flag (set to 1 on a valid level password) |
| slot `+25` | f2 — 3-bit field, range 0..6 (exact meaning unproven) |
| slot `+26` | f5 << 10 (score-like value) |

## 5. Algorithm

`decode(s)` — exactly as implemented at `0x0800E35C`:

```
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0123456789!"      # index 0..31
PERM  = [0,5,10,15,20, 1,6,11,16,21, 2,7,12,17,22,
         3,8,13,18,23, 4,9,14,19,24]            # 25 bytes
KEY   = 0x0102A6AA

1. require len(s) == 5                          # strlen == 5
2. p = 0
   for each character c in s:                   # first char = LEAST significant
       p = (p >> 5) | (index_of(c) << 20)
   # p = i0 | i1<<5 | i2<<10 | i3<<15 | i4<<20
3. d = 0
   for j in 0..24: d |= ((p >> PERM[j]) & 1) << j
4. d ^= KEY
5. fields:
       check = d & 0xF
       f1    = (d >> 4)  & 3
       f2    = (d >> 6)  & 7
       f3    = (d >> 9)  & 7
       f4    = (d >> 12) & 0xF
       f5    = (d >> 16) & 0x1F
6. reject if f2 == 7, f3 > 4, or f1 > 2
7. expected = (f5 + 22*f2 + 13*f4 + 7*f1 + 7) & 0xF
   reject if check != expected
8. return (f4, f3, f2, f1, f5 << 10)            # written to slot +18..+26
```

Notes:
* Step 2 packs the **first typed character into the low 5 bits** (little-endian symbol order).
* Step 3 is a pure bit transpose; PERM is a permutation of 0..24.
* **Bits 21–24 of `d` are never read.** They create 16 interchangeable spellings per game state (§6b).
* `encode()` is the exact inverse: build `d` from fields (high bits 0), XOR `KEY`, inverse-permute with the same PERM loop, emit 5 low-to-high symbols. A reference implementation is `/tmp/opencode/iridion2/pw.py`.

## 6. Tables

**Hard-coded special codes** (all verified as literals in the ROM at the addresses in §4):

| Code | Documented effect | Validator return path |
|---|---|---|
| `4RC8!` | story beaten / unlock Arcade+Challenge | writes slot `+20=1, +22=0, +23=5, +24=0` |
| `CH4LL` | unlock Jukebox | writes slot `+20=1, +22=0, +23=5, +24=0` |
| `!S3CR3TS!` | show secret locations | returns 3 to caller |
| `!B1GH34D!` | big-head mode | returns 4 |
| `!M1CR0!` | micro ship | returns 5 |
| `!SH1P2!` | change ship colour | sets slot `+25=1` |
| `!G4X!` | enable jukebox | returns 6 |
| `!R0T8!` | rotating satellites | returns 1 |
| `!L04D!` | CPU/debug indicator | returns 2 |
| `!0BJS!` | object counter | returns 2 |

**Published-list corrections:** the ROM contains `!0BJS!`, not the `!0BJ!` printed by one site. Two "level" codes contain a letter O where the alphabet requires digit zero: `!9ROX` → `!9R0X` and `SOL46` → `S0L46`; only the corrected forms decode. `4RC8!`/`CH4LL` are special codes and correctly fail the level decoder.

**Recovered field values for published level passwords** (f1 / f2 / f3 / f4 / f5): Easy L1 `SBJS5` = 0/4/0/1/14; Easy L14 corrected `!9R0X` = 0/3/4/1/17; Advanced L1 `9PTBY` = 1/1/0/3/17; Advanced L14 `9!H84` = 1/3/5/1/31 (f3=5 fails the f3≤4 gate — see §8); Ace L1 `8PKCX` = 2/1/0/3/19; Ace L14 `GJ0HN` = 2/3/4/9/10. 41 of the 42 published level codes decode after the O→0 corrections; the Advanced L14 entry `9!H84` is genuinely invalid (f3=5 and a checksum mismatch), and the nearest valid spellings of that state are `9!H8F` / `9!H8Y`.

## 6b. Enumeration

**Space definition**
* Alphabet: 32 symbols → 5 bits per character; 5 characters → 25 bits.
* Payload fields: f1 2 bits (3 legal values), f2 3 bits (7 legal), f3 3 bits (5 legal), f4 4 bits (16), f5 5 bits (32), check 4 bits.
* Field tuples: `3 × 7 × 5 × 16 × 32 = 53,760`.
* 4 bits of `d` (21..24) are ignored by the decoder → **16 aliases per tuple** → **860,160 accepted 5-character strings** out of `32^5 = 33,554,432` (2.56 %).
* Demonstrated alias pair: `TBPHX` and `TV60D` decode to the identical fields `f1=0,f2=0,f3=0,f4=0,f5=0`.

**Validator model** — `pw.py` reimplements §5 bit-for-bit and agrees with all 41 decodable published codes and with the ROM's own decoder on the novel and rejected inputs below.

**Novel code (not in any published list)**

| Code | Fields (f1,f2,f3,f4,f5) | Source | In-game result |
|---|---|---|---|
| `RCPHX` | 2,0,0,0,0 | generated by reimplemented encoder | **accepted**; menu unlocked; RAM slot `+22=02`, `+23=00`, `+24=01`, `+25=00`, `+26=00`, `+18..21=00000000` |

RAM proof (mGBA savestate `gbAs` chunks, IWRAM at state offset `0x19000`):

```
slot0 @0x03000040, before (state1): 00 00 00 00 ... +22=00 +23=00 +24=00 +25=00 +26=00
slot0 with marker BCDFG (state2):   00 00 42 43 44 46 47 00 ...   (buffer holds "BCDFG")
slot0 after RCPHX (state3):         00 00 52 43 50 48 58 00 ... +18..21=00000000 +22=02 +23=00 +24=01 +25=00 +26=00
```

This matches the decoder output for `RCPHX` exactly and demonstrates that f1 (difficulty) is stored at `+22` and the accept flag at `+24`.

**Bounds proven by rejection**
* `RCPHC` — differs from the accepted `RCPHX` only in the final symbol; checksum fails → in-game `Invalid Password! / Try Again`.
* `TGPHV` — checksum valid but f3 = 5, outside the decoder's `f3 ≤ 4` gate (0x0800E40A–0x0800E40C) → in-game `Invalid Password! / Try Again`.
* `BBBBB` — all index 0; decoder rejects (checksum mismatch).

## 7. Validation evidence

* **Observed** (emulator / savestate RAM): all screens listed in §3; `4RC8!`, `CH4LL`, `!S3CR3TS!` accepted; novel `RCPHX` accepted with the exact RAM field values above; `RCPHC` and `TGPHV` rejected with the `Invalid Password!` screen; input buffer at `0x03000042` holding typed strings; single header, stock entry word.
* **Derived** (disassembly): the full decoder algorithm (§5), the bit-permutation table, the XOR key, the checksum formula including the `adds r0,r0,r2` that makes the f2 coefficient 22, the range gates, the ten-code `strcmp` chain, the slot field offsets, the alphabet's 32 symbols.
* **Inferred**: f3 is a galaxy index (published level numbers advance three-at-a-time per f3 value); f2 is a 3-bit stage/score-like field; f4 and f5 are secrets/score-like values written to the save slot. The exact on-screen meaning of the eight `!…!` cheat effects was not isolated one-by-one; all eight literals and their validator branches were verified statically and one (`!S3CR3TS!`) was entered in-game.

## 8. Unknowns

* The debug surfaces `PRELIMINARY MENU LAYOUT` (`0x0804350C`, accessor `0x0800BD6C` called unconditionally from `0x0800AF4A`) and `CHEAT-CHEAT-CHEAT-CHEAT` (`0x08044168`, used at `0x0801395A`/`0x08013E70`) were not reached through normal play. Their labels and functions exist; no button-code gate or menu entry leading to them was identified, and the orphan `1sN9g` string at `0x080435B9` has no code xref. This is a **gated/dead-code** classification, not an absence claim: the strings are present and the accessor is called, so a developer build or a trigger outside normal input may still expose them.
* Precise semantics of f2/f4/f5 were not pinned to visible HUD quantities.
* Text on some screens is rendered from a font/tile-index bank (observed in IWRAM around `0x030011xx` after `!S3CR3TS!`); the ASCII-to-tile table was not fully decoded, so message text from that bank was not used as evidence.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep`.
* Python 3 + `capstone` 5.0.7 + `keystone-engine` + Pillow: literal-pool/xref scanners, `pw.py` codec, `key.py` XTEST input, `enter_pw.py` keyboard navigation.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* mGBA (SDL, `-3`, `-g`) under `Xvfb :318` + `openbox`; `xdotool`, `scrot`, ImageMagick, `tesseract`.
* Savestate RAM reading: decompress the PNG `gbAs` chunk with zlib (397,312-byte state; IWRAM at `0x19000`, EWRAM at `0x21000`) — used because the GDB stub is single-client and disconnects halted this mGBA build.
* REA/Ghidra was available but its session was bound to a different ROM belonging to another analyst, so it was deliberately not used; all findings here come from objdump/Capstone and the emulator.

All analysis scripts are in `/tmp/opencode/iridion2/`. No ROM bytes or copyrighted assets are reproduced in this report.
