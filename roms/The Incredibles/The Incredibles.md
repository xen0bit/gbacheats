# The Incredibles (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Item | Value |
|---|---|
| File | `roms/The Incredibles/The Incredibles.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `INCREDBLEAGB` |
| Game code | `BICE` (Europe), maker `78` (THQ), version `0x00` |
| Entry word | `0xEA000031` (stock ARM crt0; no scene cracktro) |
| Header checksum | `0x0000`, complement byte `0x7D` (normal rebuilt-header artifact, §16.1) |
| MD5 | `97cc2aeb06142aedc38b672e90e04a11` |
| SHA-1 | `091f81ab8bdb4032b772b94e14292b9a2cde5151` |
| SHA-256 | `008e1d141cb764982568488b0262fe4bad64d5cc76bb3c8b9b2414af3f4313cf` |

Developer/publisher (from web recon): Helixe / THQ, 2004. No GameShark/CodeBreaker/AR material was examined; only in-game passwords and the level-select screen.

## 2. Executive summary

The game has a genuine **in-game password system** on the main-menu "Password" screen, with a 32-symbol on-screen keypad and four entry slots. The published level/cheat codes are **not** a string table: they are produced by a 20-bit algorithmic code (4 symbols × 5 bits) with a 5-bit parity checksum, a 4-byte XOR key, two XOR-folding passes, and a 2-byte packed payload (level byte + flags byte). The exact validator was recovered at `0x0805A578`, reimplemented in Python, and shown to agree with 56/56 published codes and to reject a modified code that the emulator also rejects.

Two further, independent code surfaces exist:

1. **Nine hard-coded shortcut passwords** in a ROM table at `0x085FB028`, with their 2-byte payloads at `0x085FB04C`. Two of these are published (`M!K3`, `J3FF`); **seven are absent from every published list** (`ZMB!`, `H3LX`, `CHRS`, `M4RK`, `BQD!`, `B!LL`, `RBYX`). `M4RK` was entered in the emulator and accepted.
2. **Internal marker strings** at `0x080663A0` (`SH!TTH!SBTCHB4CH`) used by three small check routines (`0x08042D30`, `0x08042E20`, `0x08042F9C`) plus a dedicated "credits" check for `CR3D` at `0x08042F08`. `CR3D` was entered and produced the credits roll; `SH!T` was rejected, bounding that surface.

Novel algorithmic codes were minted from the recovered encoder. **`3YKT`** (level 2-5-1 with a cheat flag combination that no published list advertises) and **`GBZZ`** (plain level 2-5-1) were both accepted on the real screen; the in-game banner read **"Level 2-5-1 / Password 3YKT"**. The space is fully characterised: 32,768 accepted codes out of 1,048,576 representable, and 32,768 distinct 2-byte payloads — the accepted-code set is in one-to-one correspondence with the reachable payload set (no aliases).

Rejection bounds were proven in-game: a checksum-valid but out-of-range level (`NNS6`, level byte `0xFF`) and a bad-checksum code (`MSW7`) both produced "Invalid".

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `mgba -3 -t <savestate> ./game.gba`. Default SDL keymap (A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, arrows = D-pad). Key holds of 90–150 ms.
* Boot path: intro → main menu (**New Game / Password / Sound**). Select **Password**, press A. The keypad grid is 8 columns × 4 rows; move the cursor with the D-pad and press A to enter a symbol, B to erase. The 4th entry triggers validation immediately.
* Savestate `game.ss1` (empty password screen) was used as the restart point for every code test. `python3 entercode.py <code>` navigates the grid and types a 4-character code using the alphabet below.
* Codes verified on-screen: `MSW5` (published level 1-1-1, accepted), `ZYQ8` (published level select, accepted → "111" bar appears on main menu; R changes it to "112"), `CR3D` (accepted → credits), `GBZZ`, `3YKT`, `M4RK` (novel, accepted), `NNS6` and `MSW7` (rejected with "Invalid"), `SH!T` (rejected).
* Screens walked (all with screenshots under `/tmp/incredibles/`): title/intro (`title2.png`, `boot2.png`), main menu (`title2.png`), password keypad + "Invalid" (`pw3.png`, `rej_checksum.png`), sound menu (`soundmenu2.png`), level-select bar (`lvlsel3.png`, `lvlsel_R.png`), level banner / gameplay (`novel_3ykt_play.png`, `novel_gbzz2.png`), credits (`cr3d_after.png`).
* Offline decoder/encoder: `python3 model.py` reproduces all 56 published checksum codes and regenerates each from its decoded payload.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`; bytes are little-endian.

| Address | Meaning |
|---|---|
| `0x080663A0` | 16-byte internal marker string `SH!TTH!SBTCHB4CH` (2 × 8-byte records); used as a comparison table, **not** an accepted-code table |
| `0x080663B0` | 32-byte input alphabet `BCDFGHJKLMNPQRSTVWXYZ123456789?!` (exact order of the on-screen keypad) |
| `0x08066420`–`0x0806652F` | 34 level-name records, 8-byte stride, descending (`3_7_3` … `1_1_1`), plus six `B M*` entries at `0x080663F0`–`0x08066418` |
| `0x08042CB4` | Apply decoded 2-byte payload → game-state struct at `0x0201D5F0` (writes `+0x10`…`+0x14`) |
| `0x08042D30` | Table check against marker-string second halves (`TH!S`, `B4CH`) |
| `0x08042E20` | Table check against marker-string first halves / alphabet |
| `0x08042F08` | Dedicated hard-coded check for `CR3D` (credits) |
| `0x08042F9C` | Password entry point from UI: `strlen==4`, marker-table checks, then decoder |
| `0x0805A578` | **Main password decoder** (XOR key, folding, 5-bit parity check, pack) |
| `0x087E0030` | 4-byte XOR key `0A 15 12 19` followed by 15 five-bit parity columns |
| `0x085FB028` | 9 hard-coded passwords, 4 raw bytes each |
| `0x085FB04C` | 9 corresponding 16-bit payloads |
| `0x02034CCC/D0/D4` | Runtime pointers to the two tables above and their count (`9`) |
| `0x0201D700` | Password-screen UI state base |
| `0x0201D734` | Number of symbols entered (0–4) |
| `0x0201D738` / `0x0201D73C` | Keypad cursor row / column |
| `0x0201D740` | 4-byte raw input buffer (`0x40 + alphabet_index` per symbol) |
| `0x0201D5F0` | Decoded game-state struct (level/flags fields written by `0x08042CB4`) |
| `0x080456BC` | Password-screen input handler; validation triggered when count reaches 4 at `0x080457B2` |

## 5. Algorithm

### 5.1 Symbol encoding

`index(c) = position of c in ALPHA` where `ALPHA = "BCDFGHJKLMNPQRSTVWXYZ123456789?!"`. The UI writes `buf[i] = 0x40 + index` into `0x0201D740`. (Verified by savestate diff: displaying `C` gave `0x41`, displaying `D` gave `0x42`.)

### 5.2 Decoder (`0x0805A578`), exact pseudocode

```
T = bytes at 0x087E0030 ; KEY = T[0:4] ; COL = T[0:15]
a[i] = (buf[i] - 0x40) XOR KEY[i]          for i = 0..3 ; fail if any buf[i] == 0
# pass 1 (j = 0..2): a[j] ^= a[j+1]        # uses progressively updated bytes
# pass 2 (j = 0..2): a[j+1] ^= a[j]
c0 = a0^a1 ; c1 = a0^a2 ; c2 = a0^a3 ; c3 = a0      # equivalent closed form
chk = c0 ^ c1 ^ c2
for k in 0..4:
    require parity(COL[k] & chk) == bit(4-k) of c3
P = c0<<15 | c1<<10 | c2<<5 | c3
out[0] = (P >> 12) & 0xFF
out[1] = ((P >> 4) & 0xFF) & 0xFE
```

`parity(x)` is XOR of bits 0–4. The 5 parity equations are the only checksum; the 5 low bits of `P` and bit 4 of `P` are discarded/not represented in the output. The decoder then calls `0x08042CB4`, which extracts level/flags fields from `out[0]`/`out[1]` and writes them into `0x0201D5F0 + 0x10..0x14`.

### 5.3 Inverse / encoder

For a desired payload `(out[0], out[1])`, enumerate `c0,c1,c2 ∈ 0..31`, derive `c3` from the five parity equations, compute `P` and compare to the target; invert with
`a0=c3; a1=c0^c3; a2=c1^c3; a3=c2^c3` and emit `sym[i] = ALPHA[((a[i]^KEY[i])&0x1F)]`. Implemented in `model.py::encode()`. It reproduces every published code exactly from its decoded payload.

### 5.4 Hard-coded fallback path

If the parity check fails, `0x0805A6F8` compares the four raw input bytes directly against the nine 4-byte strings at `0x085FB028`; on a match it copies the corresponding 2-byte payload from `0x085FB04C` to the output and returns success. This path bypasses the checksum entirely.

## 6. Tables

### 6.0 Alphabet (index → symbol)

```
0 B   1 C   2 D   3 F   4 G   5 H   6 J   7 K   8 L   9 M  10 N  11 P  12 Q  13 R
14 S  15 T  16 V  17 W  18 X  19 Y  20 Z  21 1  22 2  23 3  24 4  25 5  26 6  27 7
28 8  29 9  30 ?  31 !
```

No `A`, `E`, `I`, `O`, `U`, `0` — this matches every published code and the rendered keypad exactly.

### 6.1 Level-byte map (from decoding published codes)

`out[0] = 0xC0 | (chapter-1)<<4 | level_within_chapter`:

| Level | Byte | Published code | Level | Byte | Published code |
|---|---|---|---|---|---|
| 1-1-1 | C0 | MSW5 | 3-2-2 | E2 | 65NS |
| 1-1-2 | C1 | BK8V | 3-2-3 | E3 | YVKK |
| 1-2-1 | C2 | 69NN | 3-2-4 | E4 | KGTY |
| 1-3-1 | C3 | GFVY | 3-3-1 | E5 | SRD6 |
| 1-3-2 | C4 | V34K | 3-4-1 | E6 | Z3ZB |
| 2-1-1 | D0 | 94HR | 3-5-1 | E7 | 9?5M |
| 2-1-2 | D1 | ZWLG | 3-5-2 | E8 | FC73 |
| 2-1-3 | D2 | SP?? | 3-5-3 | E9 | NL2? |
| 2-2-1 | D3 | KDY3 | 3-6-1 | EA | VXBG |
| 2-3-1 | D4 | Y27F | 3-6-2 | EB | YWKJ |
| 2-3-2 | D5 | 6!2N | 3-6-3 | EC | GJQZ |
| 2-3-3 | D6 | BHBV | 3-7-1 | ED | KHP2 |
| 2-4-1 | D7 | MQR5 | 3-7-2 | EE | 313K |
| 2-4-2 | D8 | 3YTK | 4-1-1 | F0 | ?!JT |
| 2-4-3 | D9 | ?6DS | 4-2-1 | F1 | ML17 |
| 2-5-1 | DA | **(no published code)** | 4-3-1 | F2 | YXFC |
| 2-5-2 | DB | 6?SR | 4-4-1 | F3 | GHV1 |
| 2-5-3 | DC | SNJ5 | 4-5-1 | F4 | VW4C |
| 3-1-1 | E0 | MNW9 | 4-6-1 | F5 | YX!F |
| 3-2-1 | E1 | BF8Z | | | |

The ROM level table contains `2_5_1` at `0x080664B0` but no published list gives a password for it.

### 6.2 Flags-byte observations (from published codes)

| Code | `out[1]` | Published effect |
|---|---|---|
| MSW5 | 06 | plain 1-1-1 |
| 69DD | 16 | infinite lives |
| 96KR | 86 | invincibility / infinite meter / extra damage |
| FG6Y | 46 | red costume |
| ZYQ8 | 36 | level select |
| V3ML | 56 | extra damage |
| RNZR | 66 | infinite meter |
| KB!K | 26 | invulnerable |
| ?5K2 | 76 | super mode |
| SP77 | 4C | 2-2-1 with 6 lives |
| 94MC | 1E | 2-2-1 with unlimited lives |
| YX9C | 82 | final level + invincibility |
| FDT? | 1C | final level + unlimited lives |

Bits 1–4 of `out[1]` are explicitly read by `0x08042CB4` into `0x0201D604`/`0x0201D603`; higher bits are consumed elsewhere (not fully traced — see §8).

### 6.3 Nine hard-coded passwords (`0x085FB028` / `0x085FB04C`)

Raw bytes are `0x40 + alphabet_index`; the displayed code is shown here.

| # | Raw bytes | Displayed code | Payload | In published lists? |
|---|---|---|---|---|
| 0 | `I_GW` | `M!K3` | C0 16 | yes — infinite lives |
| 1 | `TI@_` | `ZMB!` | C0 26 | **no** |
| 2 | `EWHR` | `H3LX` | C0 36 | **no** |
| 3 | `AEMN` | `CHRS` | C0 46 | **no** |
| 4 | `IXMG` | `M4RK` | C0 56 | **no** — verified in-game |
| 5 | `@LB_` | `BQD!` | C0 66 | **no** |
| 6 | `@_HH` | `B!LL` | C0 76 | **no** |
| 7 | `FWCC` | `J3FF` | C0 86 | yes — "J3FF" invincibility |
| 8 | `M@SR` | `RBYX` | C1 86 | **no** |

### 6.4 Internal marker checks

`0x08042F08` accepts exactly `CR3D` (alphabet indices of `C`,`R`,`3`,`D` found by scanning the alphabet table for bytes `0x43`,`0x52`,`0x33`,`0x44`). The 16-byte string at `0x080663A0` supplies four 4-byte markers: `SH!T`, `TH!S`, `BTCH`, `B4CH`. `SH!T` was entered and rejected; these are treated as internal/reserved, not player codes.

## 6b. Enumeration

### Space definition

* Alphabet: 32 symbols (§6.0). Length: exactly 4 symbols. Representable space: `32^4 = 1,048,576`.
* Each symbol is 5 bits → 20-bit packed word.
* Checksum: 5 parity equations over `COL[0..4] & (c0^c1^c2)`, compared with the five bits of `c3`. This partitions the space into `2^5 = 32` cosets, one accepted per 32 inputs.
* Payload: 2 bytes. `out[0]` = level byte (`0xC0`–`0xF5` observed); `out[1]` = flags byte. Bit 0 of `out[1]` is forced to 0 by the decoder, so at most 128 flag patterns are representable. Brute force found 32,768 accepted codes and 32,768 distinct payloads: a bijection, with no spelling aliases.
* Additional, disjoint surfaces: 9 hard-coded fallback codes (§6.3) and the `CR3D` dedicated check (§6.4). Neither overlaps the algorithmic space (both published members `M!K3` and `J3FF` are rejected by the checksum decoder).

### Completeness proof

The decoder was run over **all 1,048,576** 4-symbol strings:

```
valid algorithmic codes : 32768        (= 1,048,576 / 32)
distinct 2-byte payloads: 32768
rejection rate          : 31/32
```

Every published code from 3rd party cheat indexes and the Kaas walkthrough was decoded; 56 matched the checksum algorithm and 2 (`M!K3`, `J3FF`) matched the fallback table. The remaining few published variants that decode to out-of-range level bytes (`FXTV` → `75 00`, a likely transcription error) are recorded as unverified.

### Novel codes generated and accepted in-game

1. **`3YKT`** — decoded by `model.py` to payload `DA 16`: level 2-5-1 with the infinite-lives flag (`0x16`), a combination absent from every published list. Entered on the real password screen; the game displayed **"Level 2-5-1 / Password 3YKT"** (`novel_3ykt_play.png`) and started the level. This is the primary novel code.
2. **`GBZZ`** — payload `DA 06`: plain level 2-5-1, for which no published password exists. Entered and accepted; gameplay screenshot `novel_gbzz2.png` shows the 2-5 jungle/rail stage.
3. **`M4RK`** — from the hard-coded fallback table (payload `C0 56`, extra-damage flags). Entered and accepted (`novel_m4rk.png`), proving the whole 9-entry table is live. Six sibling codes (`ZMB!`, `H3LX`, `CHRS`, `BQD!`, `B!LL`, `RBYX`) are equally novel but were not individually entered; the shared table path is proven by `M4RK`.
4. **`CR3D`** — dedicated credits check, confirmed by the credits roll (`cr3d_after.png`). It is published, but its validator was recovered independently.

### Bounds proven by rejection

| Input | Why it should fail | In-game result |
|---|---|---|
| `MSW7` | changes one symbol of valid `MSW5` → parity check fails | "Invalid" (`rej_checksum.png`) |
| `NNS6` | checksum-valid, decodes to level byte `0xFF` (past every level record) | "Invalid" (`rej_range.png`) — proves a semantic range check **after** the checksum |
| `SH!T` | marker-table string, not a player code | "Invalid" (`joke_shit.png`) |
| `MSG5` | checksum-valid by an earlier (incorrect) model, actually invalid | "Invalid" (`msg5.png`) — also confirms the corrected model |

The `NNS6` result is the key bound: a correct checksum is **necessary but not sufficient**; the decoded level byte must map to a real level record.

### Published-list corrections

* `M!K3`, `J3FF`: accepted, but via the hard-coded table, not the checksum decoder.
* `FXTV` ("final level" alternative): decodes to level byte `0x75`, out of range — unverified; likely an error in the published list.
* `SNDF`, `ZYQ8`, `MSMC`, `YCP6` are all advertised as level select; only `ZYQ8` and `SNDF` decoded successfully (`MSMC` and `YCP6` are not checksum-valid; they may belong to a different revision).
* Divergent level codes in the Kaas walkthrough (e.g. `NTX9` for 2-1-1 instead of `94HR`) decode to different payloads with the same level byte (different flag bits), or are unverified for this revision; the decoder is injective on accepted codes, so two different valid strings cannot share one payload.

## 7. Validation evidence

* **Observed** (emulator screenshots / savestate RAM): boot, main menu, password keypad, "Invalid" banner, sound menu, level-select "111"→"112", credits roll, level 2-5-1 banner with the entered code, acceptance of `MSW5`, `ZYQ8`, `CR3D`, `GBZZ`, `3YKT`, `M4RK`, rejection of `MSW7`, `NNS6`, `SH!T`, `MSG5`; savestate diff located the input buffer at `0x0201D740` and length at `0x0201D734`; raw input bytes `44 40 54 54` for `GBZZ` read from savestate `game.ss8`.
* **Derived** (disassembly, bit-exact reimplementation): alphabet/keypad mapping, 4-byte key, two folding passes, 5-bit parity check, packed payload layout, level-byte and flags-byte fields, 9-entry fallback table, `CR3D` comparator. The decoder model agrees with 56/56 published checksum codes and regenerates each published string from its payload.
* **Inferred** (not individually exercised): the exact meaning of every flag bit above bit 4; the effect of the six unentered fallback-table codes; whether `B4CH`, `TH!S` and `BTCH` trigger any hidden path (the two that were tested, `SH!T` and the marker checks, produced "Invalid"). The "6 lives" interpretation of `SP77` comes from the published description, not from a HUD observation.

## 8. Unknowns

* Bit meanings of `out[1]` above bit 4 beyond the published-code correlations; `0x08042CB4` only reads bits 1–4 directly.
* The six remaining fallback-table codes were not individually entered; their payloads imply the published effects but that is an inference.
* `MSMC` / `YCP6` (advertised as level-select/debug) are not valid under this revision's decoder; no alternate entry path was found.
* The six `B M*` level names at `0x080663F0`–`0x08066418` were not reached by any password; their payload bytes were not determined.
* The mGBA 0.10.5 build here did not open a GDB stub on port 2345, so `trace`/savestate diff were used instead; dynamic evidence for the decoder's intermediate values is therefore indirect (the model is validated by input/output agreement, not by single-stepping the decoder).

## 9. Tooling

* `strings -t x`, `xxd`, `grep -abo`, `objdump`/`arm-none-eabi-objdump -M force-thumb`, custom Capstone xref scanner (`xref.py`).
* Python model `model.py` (`decode`, `encode`, full-space enumeration), `decode.py` (earlier iterations), `entercode.py` (keypad navigation via XTEST).
* mGBA 0.10.5 under Xvfb `:315` + openbox, `SDL_AUDIODRIVER=dummy`; CLI debugger (`mgba -d`) used for `trace`, `w/1`, `w/r`, `x/1`; savestate `gbAs` chunks decompressed with `zlib` and diffed in Python (§16.13 technique).
* No copyrighted ROM data or game assets are reproduced here; only addresses, hashes, and the 32-character alphabet are published.

## 10. Legal note

Analysis was performed on a locally supplied ROM for research. No ROM image, extracted graphics, music, or game text are redistributed in this report.
