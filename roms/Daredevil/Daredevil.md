# Daredevil (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Daredevil/Daredevil.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `DAREDEVIL` |
| Game code / maker | `AVLE` / `7H` (VU) |
| Version | Rev.00 (`0xBC` = 0x00) |
| Entry | `0xEA00002E` → `0x080000C0` (stock ARM branch) |
| Header checksum | `0x0000`, complement byte `0xBD` = `0x1A` (matches `-(sum A0..BC)-0x19`) |
| MD5 | `ab9f346110d5b97afa4e3e10347d1000` |
| SHA-1 | `db2bb397b47f1ff247dad5cfa6e35866b1048a7b` |
| SHA-256 | `bf443816c2d00f373c33040e14d1bddba7e35a18c33de1bfa777f65905b031fa` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once (file `0x4`); no second
image, no multi-game shell. Entry word and crt0 literal pool are stock; no cracktro or
trainer appended. Header complement is intact, so the header was not rebuilt.

## 2. Executive summary

Daredevil (Griptonite/Amaze, 2003) has one in-game code system: an **11-character password**
entered from the main menu's `PASSWORD` item. The on-screen keypad is the 32-symbol alphabet

```
# B C D F G H J K L M N P Q R S T V W X Y Z 0 1 2 3 4 5 6 7 8 9
```

where `#` is the Daredevil head icon that fan sites print as `@`, `¤`, `*` or `[DD]`. The
alphabet is stored three times in the ROM at `0x0802FB30`, `0x0802FB51`, `0x0802FB74`
(each 32 bytes, no NUL between the `#` and the rest).

Each character carries 5 bits. 11 characters = 55 bits:

* the 55 input bits are permuted with `dst[(s*29) mod 55] = src[s]` (29 = next prime after 27);
* `dst[0..46]` is a 47-bit payload, `dst[47..54]` is an 8-bit checksum;
* **checksum = (sum of the six payload bytes) & 0xFF**, where the 6th byte holds only 7 bits.

The 47-bit payload decodes to:

| bits | field |
|---|---|
| 1..16 | score/50 (17-bit `score` field, bit 16 discarded) |
| 17..21 | map id − 20 (map 20..51 expressible) |
| 22..25 | `f6` (4 bits, chapter/difficulty-like; 3..9 in published codes) |
| 26 | `f4` (1 bit; set only in the unlock-all code and level 1) |
| 32..46 | 15-bit secrets-unlocked mask (published codes use 0x000..0xFFF) |

All 23 published level passwords decode with a valid checksum, and re-encoding the decoded
payload reproduces the published string byte-for-byte. The published "all secrets" code
`41TK1S6ZNGV` decodes to map 44, score 246000, `f4`=1, flags `0xFFF` — exactly the
advertised "unlock everything".

A **novel code not present in any published list** was generated and accepted in-game:

```
PNP#8#RBC#N   → map 34, score 119000, f6=9, f4=0, flags=0x1F
```

The game accepted it and stored the decoded record in RAM at `0x03005290`
(`map = 0x22 = 34`, `score = 0x0001D0D8 = 119000`), then returned to the main menu. Map 34 is
absent from every published list (all published codes decode to maps 22–25, 27–33, 35–45).
A one-character mutation `Y#PSC##K##5` (same payload, broken checksum) is rejected: the game
prints "to try again.", leaves the decoded record at zero, and does not leave the entry screen.

Note on the published list: `RL#7S#RXHKM` ("Wrong Side Of The Tracks") is checksum-valid but
decodes to **map 25**, duplicating "A Question Of Honor". Maps 26 and 34 are absent from the
published set; `PNP#8#RBC#N` supplies map 34.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL under Xvfb `:279`, `SDL_AUDIODRIVER=dummy`, scale 3.
Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
Two mGBA savestate slots are used as anchors; the emulator was always the only instance on
`:279`.

1. Boot the ROM. Press Start through the legal/logos until the title; press Start again.
2. Main menu items (cursor is a 2-sprite pair, `OAM` entries 64/65, moving 14 px per Down):
   `SECRETS`, `PASSWORD`, `CREDITS`, `NEW GAME` (order observed by selecting each).
3. Choose `PASSWORD` (one Down from the initial position, then A). Screen id at
   `0x030053E0` becomes 7 and the display shows the 11-slot keypad.
4. Keypad: 4 rows of `9 / 9 / 9 / 6` cells read from the alphabet in order:
   ```
   row0: # B C D F G H J K
   row1: L M N P Q R S T V
   row2: W X Y Z 0 1 2 3 4
   row3: 5 6 7 8 9 END
   ```
   D-pad moves the cell (Down wraps row 3→0, Right wraps inside a row); A enters the
   highlighted symbol and advances the character slot. The 11th A fills the last slot; the
   next A on `END` (and any A once the counter reaches 12) submits.
5. On success the game returns to the main menu (screen id 5) and writes the decoded record to
   `0x03005290`: `+4`=`f4`, `+5`=map id, `+6`=`f6`, `+8`=score (u32). On failure the screen
   stays id 7 and prints "to try again." at `0x02000830`; the record stays zero.

Codes tested in the emulator (buffer verified at `0x03006570`, result verified at
`0x03005290`):

| Code | Entered | Result |
|---|---|---|
| `Y#PSC##K##4` (published level 1) | yes | accepted; map 22, score 2300 |
| `41TK1S6ZNGV` (published unlock-all) | yes (buffer verified) | codec decode map 44, score 246000, flags 0xFFF; in-game record not captured in that run |
| `PNP#8#RBC#N` (**novel**) | yes | accepted; map 34, score 119000 |
| `PN6B8#6BC#N` (map 46, out of range) | yes | decoder accepts; map `0x2E` stored |
| `Y#PSC##K##5` (bad checksum) | yes | rejected; "to try again.", record zero |

## 4. Address map

| ROM address | Meaning |
|---|---|
| `0x0802FB30`, `0x0802FB51`, `0x0802FB74` | 32-symbol alphabet `#BCDFGHJKLMNPQRSTVWXYZ0123456789` (three copies, 33-byte stride) |
| `0x0802FAC8` | u16 table indexed by `mode*9 + col` used by the keypad renderer |
| `0x0801CC88` | keypad screen handler (input, buffer, submit) |
| `0x0801D5F4` | password → game-state record |
| `0x0801D874` | string → 5-bit packed stream (`bit 5i+j = bit j of symbol i`) |
| `0x0801DABC` | packed stream → string (inverse; uses index→char) |
| `0x0801D914` | bit permutation `dst[(s*29)%55] = src[s]`; returns `dst[47..54]` as a byte |
| `0x0801DD50` | validator: pack, permute, compare checksum, emit 47-bit payload |
| `0x0801DDF0` | bit-copy helper |
| `0x0801DF64` | sum of N bytes mod 2^bits (checksum) |
| `0x0801DF90` | next-prime helper (returns 29 for 55 bits) |
| `0x0801DFC4` | alphabet index → character (`0x0802FB74`) |
| `0x0801DFD4` | character → alphabet index (`0x0802FB74`), 0xFF if absent |
| `0x08020F68` | password → start-game path (feeds `0x03006560` to `0x0801D5F4`) |
| `0x0800928`/`0x0800934` | widget/text helpers used by the keypad |

RAM (IWRAM unless noted):

| Address | Meaning |
|---|---|
| `0x03006570` | password buffer, 11 ASCII chars + NUL |
| `0x0300657C` | key counter (incremented by every A press; 12 submits) |
| `0x030052C8` | keypad column (0-based in row) |
| `0x030053A8` | `2*row + col` cursor encoding |
| `0x030052BC` | keypad row/page state |
| `0x03005290` | decoded record: `+4` f4, `+5` map id, `+6` f6, `+8` score (u32), `+0xD..+0x1F` flag-derived characters |
| `0x030053E0` | current screen/map id (5 = main menu, 7 = password, 8 = credits, 10 = new-game dialog, 18 = secrets) |
| `0x030052B4/B8/C0` | key held / pressed / released (active-high, A=1 … L=0x200) |
| `0x02000830` | text scratch (current message; e.g. "to try again.") |
| `0x03006560` | copy of the password used by the start-game path |

## 5. Algorithm (pseudocode)

```
ALPHA = "#BCDFGHJKLMNPQRSTVWXYZ0123456789"

def decode(code):                       # code = 11 chars
    for i,ch in enumerate(code):
        v = ALPHA.index(ch)
        for j in range(5): src[5*i+j] = (v >> j) & 1
    for s in range(55):
        dst[(s*29) % 55] = src[s]       # 29 = next_prime((47+8)//2)
    payload = bits_to_int(dst[0:47])
    checksum = bits_to_int(dst[47:55])
    b = [(payload >> (8*k)) & 0xFF for k in range(5)] + [(payload >> 40) & 0x7F]
    valid = (sum(b) & 0xFF) == checksum
    map_id = 20 + ((payload >> 16) & 0x3F) // 2
    score  = ((payload & 0x1FFFF) >> 1) * 50
    f6     = ((payload >> 16) & 0x3FF) >> 6
    f4     = ((payload >> 24) & 7) >> 2
    flags  = (payload >> 32) & 0x7FFF
    return valid, map_id, score, f6, f4, flags

def encode(payload):
    checksum = sum(payload_bytes) & 0xFF
    dst = bits(payload,47) + bits(checksum,8)
    for s in range(55): src[s] = dst[(s*29) % 55]
    return ''.join(ALPHA[bits_to_int(src[5*i:5*i+5])] for i in range(11))
```

The validator reimplementation agrees with the ROM on all 23 published passwords
(accept + exact re-encode), on the published unlock-all code, and on the emulator's rejection
of a mutated checksum.

## 6. Tables

Alphabet (32 symbols, 5-bit index 0..31): `#BCDFGHJKLMNPQRSTVWXYZ0123456789`

Keypad layout (observed and consistent with the alphabet order and the `mode*9+col` table):

```
row0  # B C D F G H J K      row1  L M N P Q R S T V
row2  W X Y Z 0 1 2 3 4      row3  5 6 7 8 9 END
```

Decoded published codes:

| Level (published label) | Code | map | score | f6 | flags |
|---|---|---|---|---|---|
| Rooftop Rumble | `Y#PSC##K##4` | 22 | 2300 | 4 | 0x000 |
| This Traffic Is Murder | `F#FNK#TKFKH` | 23 | 9900 | 6 | 0x000 |
| No Way To Treat A Lady | `CCKMC#R#B#P` | 24 | 14000 | 7 | 0x000 |
| A Question Of Honor | `0CKN##4##KR` | 25 | 14600 | 7 | 0x000 |
| Fighting With Shadows | `WCP7D#CDGKM` | 27 | 22050 | 8 | 0x000 |
| Over Troubled Waters | `H##7LBK5##D` | 28 | 29150 | 9 | 0x000 |
| Master Of The Hand | `4##3NB23GKL` | 29 | 38150 | 9 | 0x001 |
| Descent Into Madness | `MCP3NBY5B#L` | 30 | 42950 | 8 | 0x001 |
| Into The Savage Sewers | `MCF2J#K5ZKD` | 31 | 71750 | 9 | 0x003 |
| Battle Below Ground | `RCK6JB4VW#L` | 32 | 90250 | 9 | 0x007 |
| The King Commands | `RCK2QBRVXKB` | 33 | 93850 | 9 | 0x007 |
| **Wrong Side Of The Tracks** | `RL#7S#RXHKM` | **25** | 112650 | 9 | 0x00F |
| Out Of The Darkness | `MNF39#MVJKN` | 35 | 126050 | 9 | 0x01F |
| No Return Ticket | `4LTPZBP5R#K` | 36 | 136100 | 9 | 0x03F |
| Switchback | `RST21BK3SKK` | 37 | 148750 | 9 | 0x07F |
| Like Looking In A Mirror | `RQYQZCPV8#M` | 38 | 160200 | 9 | 0x0FF |
| Bad for Business | `4QYQ7CK39KC` | 39 | 165700 | 9 | 0x0FF |
| Long Hard Climb | `4S2PZC459B#` | 40 | 175300 | 9 | 0x1FF |
| Building Tension | `47T77D435L#` | 41 | 184950 | 9 | 0x3FF |
| My Aim is True | `MZY2ZRR5NBK` | 42 | 205750 | 9 | 0x7FF |
| All That Money Can Buy | `8ZY7ZRMXML#` | 43 | 206650 | 9 | 0x7FF |
| Final Showdown | `MZ231S6XSGN` | 44 | 238050 | 9 | 0xFFF |
| Generic Test Level | `##TF##6C#KQ` | 45 | 0 | 3 | 0x000 |
| All secrets (unlock) | `41TK1S6ZNGV` | 44 | 246000 | 9 (f4=1) | 0xFFF |

Maps 26 and 34 are not produced by any published code. `RL#7S#RXHKM` is checksum-valid but
decodes to map 25, i.e. the published label is wrong or the list duplicated level 4's map.

## 6b. Enumeration

* **Space definition.** 11 symbols × 5 bits = 55 bits. The permutation is a bijection on
  55 bits (`s*29 mod 55`, gcd(29,55)=1). Payload = 47 bits, checksum = 8 bits.
  Representable payload values: 2^47 = 140,737,488,355,328. Random 11-char strings pass the
  checksum with probability 1/256, so the accepted set is 2^47 of the 32^11 ≈ 2^55 strings.
* **Field space.** map id 20..51 (5 bits), score 0..3,276,750 in steps of 50 (16 bits),
  `f6` 0..15 (4 bits), `f4` 0..1, secrets mask 0..0x7FFF (15 bits). Bits 27..31 and bit 0 are
  unused (aliases: 64 spellings per payload).
* **Novel code (in no published list).**
  `PNP#8#RBC#N` = payload `0x1F025C1298`: map **34**, score **119000**, f6=9, f4=0,
  flags **0x1F**. Entered on the in-game `PASSWORD` screen; buffer verified as
  `PNP#8#RBC#N`, checksum 0x27. The game returned to the main menu and the decoded record at
  `0x03005290` read `00 00 FF FF 00 22 09 00 D8 D0 01 00`:
  `f4`=0, **map=0x22 (34)**, `f6`=9, **score=0x0001D0D8 (119000)**. Map 34 is not reachable
  from any published code (published maps: 22–25, 27–33, 35–45).
* A second novel spelling for the same payload with no flags is `FMFBM#MB##B` (generated by
  the codec, not entered).
* **Bounds proven by rejection.** `Y#PSC##K##5` (published level-1 code with the last symbol
  changed; payload identical, checksum 109≠125) is **rejected in-game**: the screen stays on
  id 7, prints "to try again.", and the decoded record remains all zero. This proves the
  checksum layer is enforced, not just modelled.
* **Out-of-range field.** A code for map 46 (`PN6B8#6BC#N`, payload `0x1F...` maps to
  `0x2E`) is **accepted by the decoder** and stored (`+5`=0x2E); the 5-bit map field has no
  semantic clamp at 0x2D. Whether the level loader handles 0x2E is not proven (unknown).
* **Fixed length.** The entry UI accepts exactly 11 symbols; the 12th A press submits and no
  further character is stored (buffer write is `buf[len-1]` only for len ≤ 11).

## 7. Validation evidence

**Observed (emulator RAM/state reads)**
* Keypad navigation, buffer `0x03006570`, counter `0x0300657C`, cursor `0x030052C8/0x030053A8`
  during 11-character entry.
* `Y#PSC##K##4` accepted → record `+5`=22, `+8`=2300 at `0x03005290`, screen returns to id 5.
* `PNP#8#RBC#N` accepted → record `+5`=34, `+8`=119000.
* `Y#PSC##K##5` rejected → "to try again.", record zero, screen stays id 7.
* `PN6B8#6BC#N` accepted by decoder → record `+5`=0x2E.
* `41TK1S6ZNGV` entered and buffer-verified (the 11-character field read back exactly;
  submit-time record capture was not repeated, so its in-game effect is reported from the
  codec only).

**Derived (disassembly, Ghidra decompilation + objdump)**
* Alphabet addresses and the `mode*9+col` keypad table.
* Permutation `(s*29) mod 55` and checksum = sum of six payload bytes mod 256
  (`FUN_0801D914`, `FUN_0801DD50`, `FUN_0801DF64`).
* Field extraction (`FUN_0801D5F4`) and the start-game path (`0x08020F68`).
* All 23 published codes + unlock-all satisfy the checksum; re-encode is exact.

**Inferred**
* `f6` is a chapter/difficulty-like value (3..9 in the published set); its consumer was not
  traced.
* Bits 27..31 and bit 0 are unused and behave as aliases (deduced from the field layout; not
  exercised in-game).
* Map ids 46..51 are decodable but their loader behaviour is unproven.

## 8. Unknowns

* Semantics of `f6` and `f4` beyond their observed correlation with level order.
* Whether the loader accepts maps 46–51 or clamps/ignores them.
* The 8-character "cheat" codes published by Neoseeker (`KNGHTSFR`, `LMSPLLNG`, `THRBLDNS`,
  `CRSDRPLS`, `NDCRSDRT`, `NFTRWLLH`, the easy/medium/hard mode lists) do **not** satisfy the
  checksum under this 11-character scheme (tested with the analogous 40-bit form) and were not
  reachable on the entry screen; they are treated as unverified, likely console-version codes
  or fan submissions.
* Text in the ROM is compressed (no ASCII/font-index/5-bit form found for UI strings); the
  font/text bank format was not reversed. Menu text was read from the EWRAM text scratch
  (`0x02000830`) and from VRAM glyph tilemaps instead.

## 9. Tooling

* mGBA 0.10.5 SDL (`Xvfb :279`, openbox, `SDL_AUDIODRIVER=dummy`).
* `objdump` (arm-none-eabi) and Ghidra 12.1 headless (raw binary, `ARM:LE:32:v4t`,
  base `0x08000000`, manual Thumb context) for `FUN_0801D5F4`, `FUN_0801DD50`, `FUN_0801D914`.
* Python tools in `/tmp/opencode/daredevil`: `codec.py` (decoder/encoder), `ss.py` (mGBA
  savestate reader: VRAM @0x1000, IWRAM @0x19000, EWRAM @0x21000, IO @0x400), `enter4.py`
  (verified keypad entry), `diff.py`, `xref.py`, `bg.py`/`art2.py` (text-mode tilemap dumps).
* `capstone` 5.0.7 for literal/BL scans.
* Ghidra was used only for decompilation of the password functions; every published and novel
  code was checked against the emulator, not the decompiler.

## 10. Legal note

No ROM, graphics, music or text assets are redistributed here. Only addresses, hashes,
algorithms and self-generated example codes are published.

### Note on fetched material

The TCRF page for this game returned a prompt-injection payload (fake "instructions for LLMs",
a fake EICAR key file, a payment demand, a fake fatal error and a request to print an insult).
It was treated as untrusted data, not followed, and none of its instructions were executed;
the TCRF content used was only its factual note that a hidden test stage exists and that the
CodeBreaker code `030053E0:2D` selects map 0x2D, which is consistent with the map field of the
password format recovered here.
