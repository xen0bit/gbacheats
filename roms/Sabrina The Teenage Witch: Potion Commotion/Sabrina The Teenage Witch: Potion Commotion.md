# Sabrina The Teenage Witch: Potion Commotion (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Sabrina The Teenage Witch: Potion Commotion.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `SABRINA-THE` |
| Game code / maker / rev | `A3BE` / `41` / `0x00` |
| Fixed byte 0xB2 / complement / checksum | 0x96 / 0xE3 / 0x0000 |
| Entry word | `0xEA0FCE38` → `0x083F38E8` (non-stock) |
| MD5 | `bcabe3b207a3c3915c5de2112f741841` |
| SHA-1 | `a9418087193cbd8bd6649f3a8ce05c10349a0047` |
| SHA-256 | `7f7b2b6347f317f933bf0063fe7343d36dfdafc0f5fcb8b547c87a574d09b03d` |

**Release/patch note (§16.1).** This is the **Eurasia scene release** ("EURASIA PRESENTS ON … eurasia" splash observed on boot). The entry vector was patched from the stock `0xEA00002E` to a compressed overlay at `0x083F38E8`: it sets up stacks, writes DISPCNT, calls a custom bitstream LZ77-style decompressor at `0x083F392C` that unpacks the payload at `0x083F3D64` to EWRAM `0x02000000`, then `bx r0` into it. The real game/cheat code is uncompressed Thumb in ROM from `0x080000C0` onward. Only **one** GBA header (Nintendo-logo scan) exists; no appended trainer was found. The cheat material below is developer-intended and lives in the game's own ROM, not in the cracktro.

## 2. Executive summary

The game has a genuine, developer-intended **6-symbol password system**, reachable from the title menu's **Password** entry. The on-screen keypad uses a 32-symbol, vowel-free alphabet (a 5-bit-per-symbol code). RAM evidence (`0x030036DD`, six bytes of alphabet indices) was used to locate two independent validators:

1. **A 14-entry hard-coded cheat table** (`0x08057E68`) checked by `0x080004A8`. These are leetspeak developer codes (`D1N0ZR`, `STR0NG`, `SPY1NG`, …). Entry accepted on the real screen: `D1N0ZR` written flag word `0x03001F78 = 1`, level `0x14`, payload `0x000FFFFF` (all levels unlocked); `STR0NG` wrote flag `2`. This table is a small, closed set.

2. **The published-code system** — a **checksummed 25-bit algorithmic password**, validated by `0x08000358` via decoder `0x08047C50`. This is the interesting surface: **2,651,087** of the 1,073,741,824 possible 6-symbol strings are accepted, spanning 21 level fields and 20-bit payloads. Both published master codes were reproduced (`RTVBT4` → level 9 / payload 0xAB; `BSWFRW` → level 20 / payload 0xFBCAB), then a **novel code `TPHC19`** (level 20 / payload 0xABCDE), absent from every published list, was minted from the reversed algorithm, entered on the real Password screen, and confirmed by the resulting state change (level byte `0x14`, payload `0x000ABCDE`) and level-select map. Bounds were proven by in-game rejection of an out-of-range level, an oversized payload, and a corrupt checksum.

Published per-level codes were decoded and found to be off-by-one in their labels; one (`450qmm`) is rejected outright (§6).

## 3. How to reproduce

* Emulator: mGBA 0.10.5, Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`; keymap A=`x`, B=`z`, Start=`Return`, D-pad=arrow keys. Hold keys ~50–150 ms (shorter taps are missed; longer holds double-step).
* Boot: cracktro splash → press A; **language select** (English/Français/Español) → Start; **title** → Start; **main menu** → Down, A → **Password**.
* Keypad grid (cursor moves in 2D, A = select char, 6 slots then `OK`):
  `BCDFGHJK / LMNPQRST / VWXYZ-01 / 23456789 / OK`.
* Enter characters, move the cursor to `OK`, press A. A white paw = accepted, red paw = rejected.
* Savestates: Shift+F1…F10 save, F1…F10 load. A state saved on the Password screen makes each test a reload + 6 selections + OK.
* For validation without the UI: mGBA's CLI debugger (`mgba -d`) with a FIFO on stdin supports `r/1`, `w/1`, `w/r`, `b`, `continue`, `load <slot>`. Calling `0x08000358` with `r0` = pointer to six index bytes, a breakpoint at its return (`0x0800041C`), and reading `r0` (1 = accept, 0 = reject) is an exact offline oracle (§16.19). `0x080004A8` is the table-checker oracle (returns table index 0–13, or `-1`).
* Savestate RAM dumps: mGBA `.ssN` files are PNGs with a zlib `gbAs` chunk (raw 397,312 B); IWRAM begins at raw offset `0x19000`, EWRAM at `0x21000` (§16.13). The input buffer is IWRAM `0x030036DD`.

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`.

| File offset / ROM addr | Role |
|---|---|
| `0x000000` | Header; patched entry `0xEA0FCE38` |
| `0x3F38E8` / `0x083F38E8` | Eurasia cracktro loader |
| `0x3F392C` / `0x083F392C` | Custom bitstream decompressor |
| `0x0304B6`/`0x080004B6` region | `0x08000420`: generator for two table codes (writes `PL4Y1T`, `STR1CT`) |
| `0x000358` / `0x08000358` | **Master password validator** (algorithmic) |
| `0x000420` / `0x08000420` | Table-code generator |
| `0x0004A8` / `0x080004A8` | **Cheat-table validator** (14-entry lookup) |
| `0x0035`8 region `0x0800358`–`0x080041C` | master validator: decode, field split, state writes |
| `0x047C50` / `0x08047C50` | 5-bit base32 decoder (XOR, multiply-subtract, checksum) |
| `0x05B634` / `0x0805B634` | XOR key bytes `05 09 02 04 0F 03` |
| `0x057E68` / `0x08057E68` | 14 cheat codes, 6 bytes each (84 bytes) |
| `0x0038E0` / `0x080038E0` | wrapper: copies 6 bytes from `[r7+0xDD]` to stack, calls both validators |
| `0x045EB0` / `0x08045EB0` | Password-screen setup; uses `0x03003600` as state base |
| RAM `0x030036DD` | 6-byte password input buffer (indices 0–31; 0xFF = empty) |
| RAM `0x03001E70` | decoded 20-bit payload (level-unlock mask) |
| RAM `0x03001E74` | decoded level byte |
| RAM `0x03001F78` | cheat flag word written by table validator |

## 5. Algorithm

### 5.1 Alphabet and input

`ALPHA = BCDFGHJKLMNPQRSTVWXYZ-0123456789` (indices 0–31; no vowels). The keypad writes 6 indices into `0x030036DD`; 0xFF marks an empty slot. A fully entered password is copied to a stack buffer and passed to the two validators in sequence (`0x080038E0` calls `0x080004A8` first, then, on `-1`, `0x08000358`).

### 5.2 Cheat-table validator (`0x080004A8`)

```
for entry in 0..13:                       # r7 = 14
    if input[0..5] == table[entry][0..5]: # table at 0x08057E68, stride 6
        modify flag word 0x03001F78 per entry (bit masks)
        return entry                      # 0..13
return -1
```

### 5.3 Master password validator (`0x08000358` + decoder `0x08047C50`)

```
KEY = [0x05,0x09,0x02,0x04,0x0F,0x03]      # ROM 0x0805B634

def decode(v):                             # v = 6 alphabet indices
    w = [ v[i] ^ KEY[i] for i in 0..5 ]
    for i in 0..4:
        w[i] = (w[i] - KEY[i]*w[5]) & 31
    if (sum(w[0..4]) & 31) != w[5]: return reject
    decoded = sum(w[i] << (5*i) for i in 0..4)   # 25-bit LSB-first pack
    return decoded

decoded = decode(v)
level   = (decoded >> 20) & 31
payload = decoded & 0xFFFFF
if level > 20: return reject
adj = level + 1 if level in {4,6,7,8,9,12,13,14,19} else level
if (payload >> adj) != 0: return reject    # note: zero is the ACCEPT branch
write payload -> 0x03001E70, level -> 0x03001E74, set unlock state, return 1
```

The final `(payload >> adj) == 0` branch (0x80003BC → 0x80003CC) is the accept path — this was verified against the ROM, not inferred from the source shape. The 5-bit pack writes at bit positions 0,5,10,15,20; bits 25–31 are never set.

### 5.4 Encoder (inverse, used to mint codes)

For a chosen level `L ≤ 20` and payload `P < 2^adj(L)`:
```
out = (L<<20) | P
w2[i] = (out >> (5*i)) & 31          (i = 0..4)
c     = sum(w2) & 31
v[5]  = c ^ KEY[5]
v[i]  = ((w2[i] + KEY[i]*c) & 31) ^ KEY[i]   (i = 0..4)
code  = ''.join(ALPHA[x] for x in v)
```
This reproduces `RTVBT4`/`BSWFRW` exactly and mints accepted novel codes (§6b).

## 6. Tables

### 6.1 32-symbol keypad alphabet
`BCDFGHJKLMNPQRSTVWXYZ-0123456789` — index 0 = `B`, 21 = `-`, 22 = `0`, 31 = `9`.

### 6.2 14-entry developer cheat table (ROM `0x08057E68`)

| # | Code | Observed effect / flag word |
|---|---|---|
| 0 | `D1N0ZR` | flag `0x03001F78 = 1`; level 20, payload `0x000FFFFF` — all levels unlocked (Observed) |
| 1 | `STR0NG` | flag `2` (Observed; specific gameplay effect not isolated) |
| 2 | `SPY1NG` | derived from table |
| 3 | `ZYRC0N` | derived from table |
| 4 | `H1GH-5` | derived from table |
| 5 | `2-W1LD` | derived from table |
| 6 | `GR1NCH` | derived from table |
| 7 | `X9Y8Z7` | derived from table |
| 8 | `M1SF1T` | derived from table |
| 9 | `STR1CT` | derived from table (also regenerated by `0x08000420`) |
| 10 | `PL4Y1T` | derived from table (also regenerated by `0x08000420`) |
| 11 | `CRD1TS` | derived from table |
| 12 | `H0WDD0` | derived from table |
| 13 | `PR0DST` | derived from table |

These 14 are **rejected** by the master validator (all return `None`), i.e. they are a separate code set, not aliases of the algorithmic passwords.

### 6.3 XOR key
`05 09 02 04 0F 03` at ROM `0x0805B634`.

### 6.4 Published codes verified against the ROM

| Published code | Source | Decoded level | Payload | ROM result |
|---|---|---|---|---|
| `RTVBT4` | GameFAQs / Neoseeker / VGChartz | 9 | `0xAB` | accepted; level map |
| `BSWFRW` | GameFAQs / A2ZCheats | 20 | `0xFBCAB` | accepted by oracle |
| `bbbb9d`…`91vb3n` | A2ZCheats | 1…15 (labels off by one) | mostly `0xAB`/`0x2D`/`0x1AD`/`0x1FFFF` | accepted by model |
| `450qmm` | A2ZCheats ("level 17") | — | — | **rejected** — bad checksum/typo |
| `y1lvro` | A2ZCheats | — | — | contains `O`, which is not in the alphabet — transcription error |

GameFAQs' "RTVBT4 = all levels and mini-games" label does not match the decoded payload (level 9, payload 0xAB); `BSWFRW` decodes to level 20 / 0xFBCAB. Report payloads, not published labels (§16.15).

## 6b. Enumeration

**Space.** Raw input space = 32^6 = **1,073,741,824** strings. Accepted algorithmic passwords: the decoder admits exactly one code per 25-bit decoded word (the checksum fixes the 6th symbol), and the `level ≤ 20` + `(payload >> adj(level)) == 0` filters leave:

```
level:  0  1  2  3  4   5   6    7    8     9    10    11    12    13    14    15    16     17     18      19       20
count:  1  2  4  8  32  32  128  256  512  1024  1024  2048  8192  16384 32768 32768 65536 131072 262144 1048576 1048576
TOTAL = 2,651,087 accepted passwords (0.247 % of the raw space)
```
(count confirmed both analytically and with an independent C loop). Also **exactly 14** cheat-table codes (§6.2).

**Novel codes minted (absent from GameFAQs, VGChartz, TCRF, Neoseeker, A2ZCheats and all other consulted lists):**

* **`TPHC19`** — level 20, payload `0xABCDE`, indices `[15,11,5,1,23,31]`. Entered on the real Password screen: accepted (green paw, level-select map). RAM proof: `0x03001E70 = 0x000ABCDE`, `0x03001E74 = 0x14` (cf. before-entry 0/0); the payload/level stayed constant while navigating the map. Screenshots: `novel_before.png`, `novel_after.png`.
* `MB0G25` — level 15, payload `0x1234` — accepted by the ROM oracle (return 1).
* `TZLVB0` — level 20, payload `0x1` — accepted by the ROM oracle.
* `2H4ZVT` — level 11, payload `0x1` — accepted by the ROM oracle.

**Bounds proven by rejection (ROM oracle, return 0):**

| Input | Property tested | Result |
|---|---|---|
| `RTVBT5` | corrupt checksum (last symbol +1) | rejected |
| `QZLV90` | level field 21 (out of range) | rejected |
| `886296` | level field 31 (out of range) | rejected |
| `1Y1QVM` | level 9 with payload `0x400 = 2^adj(9)` | rejected |
| `K1Q27G` | level 9 with payload `0x3FF = 2^adj(9)-1` | **accepted** |
| `FBBBBD` | level 0 with payload 1 (`1 >> 0 != 0`) | rejected |

These bound both the checksum layer and the semantic payload/level layer (§16.5, §16.4b).

**Cheat-table set:** exactly 14 entries; two confirmed live on the real screen (`D1N0ZR`, `STR0NG`), the rest read from the table and its validator's 14-iteration bound (`r7 = 14`, `cmp r5,#10` dispatch covering entries 0–10 plus 11–13).

## 7. Validation evidence

* **Observed** (emulator/screenshots + RAM): all reachable screens walked — Eurasia cracktro, language select, title, main menu (`New Game`/`Password`), Password keypad, New-Game cutscene, and the level-select map reached by `RTVBT4` and by novel `TPHC19`. Input buffer `0x030036DD` verified for `RTVBT4` (`0D 0F 10 00 0F 1A`) and `STR0NG` (`0E 0F 0D 16 0A 04`). Accepted novel code produced `0x03001E70 = 0x000ABCDE`, `0x03001E74 = 0x14`; `STR0NG` produced `0x03001F78 = 2`; `D1N0ZR` produced `0x03001F78 = 1`, level `0x14`, payload `0x000FFFFF`.
* **Derived** (disassembly + debugger oracle): both validators, the decoder/key/algorithm, the 14-entry table, the accept/reject branches, the field widths, all bounds and the enumeration count. The Python decoder/encoder agreed with the ROM oracle on every code tested; round-tripping `RTVBT4`/`BSWFRW` reproduced them exactly.
* **Inferred**: the exact gameplay meaning of each of the 14 cheat-table flag bits (only flags 1 and 2 were observed; the table-valuator's jump table modifies `0x03001F78` with AND/OR masks); the level-select's visual representation of the 20-bit unlock mask. Text on several screens is font/tile-indexed; the letter glyphs and keypad alphabet were decoded from the rendered grid, and code strings were confirmed by the RAM buffer rather than by `strings` (§11 note: no ASCII hits for any password literal).

## 8. Unknowns

* Gameplay effects of cheat-table entries 2–13 were not individually isolated (a full 14-code UI sweep timed out; entries are proven to exist and the validator's dispatch was read statically).
* The meaning of the adjusted-level skip set `{4,6,7,8,9,12,13,14,19}` (likely mini-game/bonus stages absent from the retail level list) was not determined by playing those stages.
* The level-select map's icon-to-level mapping was observed visually but not exhaustively annotated.
* No debug menu was found; the 14-entry table is reachable from the Password screen's first validator, so it is not dead code, but a separate hidden menu is not claimed.

## 9. Tooling

`strings`, `grep -abo`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum`, `arm-none-eabi-objdump -M force-thumb`, Capstone (available), Python 3 + Pillow (savestate PNG chunk parsing, cursor detection), mGBA 0.10.5 in Xvfb with SDL dummy audio, `xdotool`, `scrot`, `gdb-multiarch` (GDB stub proved unreliable; CLI `-d` debugger with a FIFO used instead), gcc (enumeration cross-check). Analysis scripts in `/tmp/sabrina/`: `phase0.py`, `parse_state2.py`, `enter_pw.py`, `reliable_submit.py`, `model.py` (decoder/caller model), `encode.py` (encoder), `oracle.py` (debugger oracle), `count.c`.

**Legal note.** No ROM or extracted copyrighted assets are redistributed. Only hashes, addresses, algorithms, code strings and original tooling are published.
