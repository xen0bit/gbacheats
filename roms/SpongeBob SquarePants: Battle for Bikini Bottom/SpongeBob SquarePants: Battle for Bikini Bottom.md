# SpongeBob SquarePants: Battle for Bikini Bottom (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `SpongeBob SquarePants: Battle for Bikini Bottom.gba` |
| Size | 8,388,608 bytes (0x00800000, 8 MiB) |
| Header title | `SBSPBATTLEBB` |
| Game code / maker / version | `BSQE` / `78` / `00` |
| Fixed byte 0x96 / unit / device | present / `0x00` / `0x00` |
| Header checksum (0xBE) | `0x0000`; complement (0xBD) `0x3F` (stock value would be `0x58`) |
| Entry word (0x00) | `0xEA1FEC7E` → ARM branch to `0x087FB200` |
| MD5 | `be31f4edfac7b00e814bda15245063cd` |
| SHA-1 | `ce77cb62b9cf185b561f418e83f2a208340b5f42` |
| SHA-256 | `08e963eacf2b35474384de3f61d860caa1f00e31a15d43eef0ea8f70d93f4524` |

**Patch / trainer finding (§16.1).** The delivered image is not a stock retail image. The entry word branches to `0x087FB200`, which contains a *second, foreign crt0* (strings `nonam`/`main`/`pret` at `0x087FB294`, a name-lookup routine at `0x087FB278`, palette clear and LDR literal loads). The normal crt0 is still intact at `0x080000C0` (`mov r0,#0x12; msr CPSR_fc; ldr sp,...; svc 0x...`). Booting the delivered ROM in mGBA 0.10.5 fails with:

```
GBA Memory: Jumped to invalid address: 01625C78
GBA: Illegal opcode: e710b710
The game crashed!
```

Restoring the four bytes at file offset `0x00000000` to the stock branch `2E 00 00 EA` (`0xEA00002E` → `0x080000C0`) on a **copy** makes the game boot to the THQ logo and play normally. Only those 4 bytes differ. All ROM addresses below are identical in the delivered and restored images (file offset + `0x08000000`). No separate cheat device/trainer menu is present; the only Nintendo-logo hit in the whole file is at `0x4`, so this is a single-image ROM, not a multi-game pack. No `.gba` patch file was supplied.

Web/ROM text was treated strictly as data; no instructions found in fetched pages or strings were acted on. No prompt-injection payload was encountered.

## 2. Executive summary

The game has a real, developer-intended **4-character password system** — an algorithm, not a lookup table. On the title screen, **Continue** opens an on-screen keyboard whose 32 symbols are exactly `BCDFGHJKLMNPQRSTVWXYZ0123456789?` (all 21 consonants + 10 digits + `?`). Four typed characters are packed into a 32-bit word, XORed with a hard-coded key, and interpreted as a **level number** (5 bits) plus an **8-bit collectible/unlock mask**. A "unary-group" validity rule (§16.5) bounds the mask by the level; seven payload bits are ignored, giving **128 aliases per distinct state**.

The whole space is characterised: 32⁴ = **1,048,576** possible codes, of which **250,112** (23.8525 %) are accepted, representing **1,954** distinct (level, mask) states. The published level codes were verified against the ROM: 28 of 30 decode to levels 1–28 in exact sequence; two published entries (`QGT3` for 1-3, `C934` for 2-1) are invalid and are transcription errors.

Three novel codes absent from every published list were generated from the reversed validator and accepted on the real password screen: **`R1K5`** (filler-bit alias of `Q2K5`, level 1-1), **`RXK5`** (level 1-3 — the correct code the published `QGT3` was meant to be), and **`R?3X`** (level 21 with mask 48). Out-of-range inputs `H1K5` (level 0), `R1FY` (level 29), `RXFY` (level 31) and `81K5` (mask 2 on level 1) were all rejected, proving the bounds.

Four lowercase debug labels (`level skip`, `cheats`, `complete level`, `level select`) survive in the string bank (indices 48–51) but no reachable menu, pointer or code path could be found for them; they are dead/gated developer labels in this retail build. The similarly worded `Press Select + L + R to wake` is **not** a cheat: it is the Sleep-mode wake prompt, confirmed on-screen and decoded from the font's control-code glyphs.

## 3. How to reproduce

### 3.1 Environment
- mGBA 0.10.5 (`/usr/local/bin/mgba`), Xvfb `:319`, `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
- Boot the **restored copy** (see §1); the delivered entry word crashes in mGBA.
- SDL keymap: `x`=A, `z`=B, `a`=L, `s`=R, `Return`=Start, `BackSpace`=Select, arrow keys = D-pad. Hold keys 60–150 ms (shorter holds double-step menus).

### 3.2 Exact menu path
1. Title (`PRESS START`) → **Start** → main menu `New Game / Continue / Options`.
2. **Down**, **A** on `Continue` → password entry keyboard (four `.` slots at top; grid rows `BCDFGHJK` / `LMNPQRST` / `VWXYZ012` / `3456789?`).
3. Move with D-pad; **A** appends the highlighted symbol; **B** deletes the last symbol. The 4th symbol auto-submits.
4. Success → level map for the decoded level; the pause screen (**Start**) then shows `Password: XXXX` (the entered code verbatim). Failure → the same empty password keyboard.
5. `Options` → `Sound` (Music/SFX) and `Credits`. Chapter map → `Photo Album` (8 slots, 6 filled by default; more unlock with different masks). Sleep prompt shows `Press Select + L + R to wake`.

### 3.3 Codes tested (all on the real screen)

| Code | Model decode | Observed | In published list? |
|---|---|---|---|
| `Q2K5` | L1, C0 | 1-1 When Robots Attack | yes (1-1) |
| `RXK5` | L3, C0 | **1-3 Robot from the Goo Lagoon** | **no** |
| `R1K5` | L1, C0 | 1-1 When Robots Attack | **no** (alias of Q2K5) |
| `R?3X` | L21, C48 | Squid Vicious (3-Boss) | **no** |
| `G050` | L28, C100 | SpongeBot SteelPants; Chapter 4 map unlocked | yes ("level select") |
| `H1K5` | L0, C0 | rejected (empty keyboard) | no |
| `R1FY` | L29, C0 | rejected | no |
| `RXFY` | L31, C0 | rejected | no |
| `81K5` | L1, C2 | rejected | no |
| `QGT3` (published 1-3) | L1, C12 (invalid) | rejected | yes — wrong |
| `C934` (published 2-1) | L12, C48 (valid but wrong level) | decodes to 2-5, not 2-1 | yes — wrong |

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`); the file is 8 MiB and not mirrored internally.

| Address | Purpose | Evidence |
|---|---|---|
| `0x08000000` | patched entry word `0xEA1FEC7E`; stock `0xEA00002E` | Derived (bytes) |
| `0x080000C0` | original ARM crt0 | Derived (disasm) |
| `0x087FB200` | injected foreign crt0 (crash on boot) | Observed (mGBA log) + Derived |
| `0x08031144` | password alphabet, 32 bytes + NUL: `BCDFGHJKLMNPQRSTVWXYZ0123456789?` | Derived (literal) |
| `0x08047F7C` | string-handle table, 98 entries of `char **` | Derived |
| `0x0804A3A4` | string 30, `Password: ....` | Derived |
| `0x0804A3B8` | string 31, `Press Select + %86 + %87\nto wake` | Derived + Observed (Sleep screen) |
| `0x0804A4DC` / `0x0804A4EC` / `0x0804A4F8` / `0x0804A50C` | strings 48–51: `level skip` / `cheats` / `complete level` / `level select` | Derived |
| `0x0804A588`–`0x0804A9C0` | level-name strings (1-1 … B-8), table indices 59–94 | Derived |
| `0x08004B80` | bitstream writer `write_bits(state*, u32 nbits, u32 value)` | Derived |
| `0x08004C3C` | bitstream reader `read_bits(state*, u32 nbits)` (LSB-first, byte-by-byte) | Derived |
| `0x08004CE4` | bitstream init `init(state*, void* bytes)` | Derived |
| `0x0800F210` | encoder core: game state → 32-bit code word | Derived |
| `0x0800F368`, `0x0800F4E0` | XOR key literal `0x1A071605` (both directions) | Derived (raw bytes) |
| `0x0800F364` | pointer `0x020041E4` (EWRAM word folded into filler bits) | Derived |
| `0x0800F360` | pointer `0x04000006` (VCOUNT, used as filler entropy) | Derived |
| `0x0800F36C` | **validator**: `(state*, u32 code) -> int` (1 = accept) | Derived + Observed |
| `0x0800F550` | encoder: `(state*) -> void`; writes alphabet chars to `state+0x90..0x93` | Derived |
| `0x0800F740` | `alphabet[index] -> char` (memcpy of 33 bytes then index) | Derived |
| `0x0800DFC0`–`0x0800E140` | password menu handlers; success/failure dispatch | Derived |
| `0x0800E006` / `0x0800E00C` | loads code word from UI object `+0xBC`, calls validator | Derived |
| `0x0800F828` | new-game state init (`+0x30=1`, `+0x34=0`, then encode) | Derived |
| `0x0800E6F8`, `0x08022A26` | encoder refreshed after progress events | Derived |
| `0x02000054` (EWRAM) | password-UI byte: `0x86` → `0xC8` on cursor Down, → `0x09` on A (savestate diff) | Observed |
| `0x03000FCE` (IWRAM) | UI state word: `0x0226` → `0x0048` → `0x0302` across those inputs (savestate diff) | Observed |

Savestate note: mGBA `.ss1` files are PNGs with a zlib `gbAs` chunk; for this 8 MiB ROM the decompressed state is 397,312 bytes with IWRAM at chunk offset `0x19000` and EWRAM at `0x21000` (§16.13). The GDB stub was used successfully once for register/RAM reads but was subsequently unavailable because another session held port 2345; the ROM's validator was therefore not callable as an oracle, and the algorithm was verified against 28 published codes plus 10 in-game accept/reject tests instead.

## 5. Algorithm

### 5.1 Input → 32-bit code word
Alphabet index map (`ALPHA`): `B=0, C=1, D=2, F=3, G=4, H=5, J=6, K=7, L=8, M=9, N=10, P=11, Q=12, R=13, S=14, T=15, V=16, W=17, X=18, Y=19, Z=20, 0=21, 1=22, 2=23, 3=24, 4=25, 5=26, 6=27, 7=28, 8=29, 9=30, ?=31`.

```
i[0..3] = ALPHA.index(char[0..3])
word    = i[0] | (i[1] << 8) | (i[2] << 16) | (i[3] << 24)
```

Each 5-bit index occupies the low five bits of one byte; bits 5–7, 13–15, 21–23 and 29–31 of `word` are structurally zero. (This is exactly the inverse of the encoder at `0x0800F550`, which extracts `word & 31`, `(word>>8)&31`, `(word>>16)&31`, `(word>>24)&31` and indexes the alphabet.)

### 5.2 Validator (`0x0800F36C`)

```
x = word ^ 0x1A071605

# 5-bit level, read LSB-first from these bit positions of x
L = ((x>>3 )&1)<<0 | ((x>>10)&1)<<1 | ((x>>18)&1)<<2 | \
    ((x>>24)&1)<<3 | ((x>>27)&1)<<4

# 8-bit collectible/unlock mask
C = ((x>>1 )&1)<<0 | ((x>>4 )&1)<<1 | ((x>>9 )&1)<<2 | ((x>>12)&1)<<3 | \
    ((x>>17)&1)<<1*4 ... == ((x>>17)&1)<<4 | ((x>>20)&1)<<5 | \
    ((x>>26)&1)<<6 | ((x>>28)&1)<<7

# unary-group bound (the disassembly's popcount tests are redundant with the mask)
B(L) = 1 if  L <= 3
       2 if  L <= 6
       3 if  L <= 10
       4 if  L <= 13
       5 if  L <= 17
       6 if  L <= 20
       7 if  L <= 24
       8 if  L <= 28

accept iff 1 <= L <= 28 and C < (1 << B(L))
on accept: state[+0x30] = L; state[+0x34] = C; return 1
otherwise return 0
```

The validator's bit reader consumes 32 bits with a 3-bit skip after every 5–6 data bits; the skipped bit positions are `0, 2, 8, 11, 16, 19, 25` — **seven ignored filler bits**. The encoder fills them from `(VCOUNT << 16 | [0x020041E4]) ^ 0x1A071605`, so they vary between invocations but never affect acceptance. The final XOR in the encoder uses the same key `0x1A071605` as the validator.

### 5.3 Encoder (state → password), for minting codes

```
x = 0
for (pos,bit) in zip([1,4,9,12,17,20,26,28], 0..7): x |= ((C>>bit)&1)<<pos
for (pos,bit) in zip([3,10,18,24,27],        0..4): x |= ((L>>bit)&1)<<pos
for (pos,bit) in zip([0,2,8,11,16,19,25],    0..6): x |= filler[bit]<<pos   # arbitrary
word = x ^ 0x1A071605
code = ''.join(ALPHA[(word>>(8*k)) & 31] for k in 0..3)
```

Python implementations of both directions were in `/tmp/spongebob2/model.py` and `encode.py`.

### 5.4 Level numbering

`L` is the 1-based level index: 1=1-1, 2=1-2, 3=1-3, 4=1-4, 5=1-5, 6=1-6, 7=1-Boss (Attack of the Steel Squirrel), 8=2-1 … 13=2-6, 14=2-Boss (Star Power), 15=3-1 … 20=3-6, 21=3-Boss (Squid Vicious), 22=4-1 … 27=4-6, 28=4-Boss (SpongeBot SteelPants).

## 6. Tables

### 6.0 Alphabet (32 symbols)
`BCDFGHJKLMNPQRSTVWXYZ0123456789?` at ROM `0x08031144`. Index→char routine `0x0800F740`; char→index is a linear scan of this literal.

### 6.1 Full published-level list decoded (all 30 entries)

| Level | Published | L | C | Valid? |
|---|---|---:|---:|---|
| 1-1 | Q2K5 | 1 | 0 | yes |
| 1-2 | HYK3 | 2 | 0 | yes |
| 1-3 | QGT3 | 1 | 12 | **no (typo)** |
| 1-4 | B1D3 | 4 | 0 | yes |
| 1-5 | L2F3 | 5 | 0 | yes |
| 1-6 | CXP5 | 6 | 0 | yes |
| 1-Boss | M5D3 | 7 | 0 | yes |
| 2-1 | C934 | 12 | 48 | **no (wrong level; =2-5)** |
| 2-2 | L2S6 | 9 | 0 | yes |
| 2-3 | BYK4 | 10 | 0 | yes |
| 2-4 | LXT6 | 11 | 0 | yes |
| 2-5 | C?P6 | 12 | 0 | yes |
| 2-6 | R?P6 | 13 | 0 | yes |
| 2-Boss | BYF4 | 14 | 0 | yes |
| 3-1 | Q5P4 | 15 | 0 | yes |
| 3-2 | H9SX | 16 | 0 | yes |
| 3-3 | M9JX | 17 | 0 | yes |
| 3-4 | BYTX | 18 | 0 | yes |
| 3-5 | R5JX | 19 | 0 | yes |
| 3-6 | B2FV | 20 | 0 | yes |
| 3-Boss | M1FV | 21 | 0 | yes |
| 4-1 | B5FV | 22 | 0 | yes |
| 4-2 | LXFV | 23 | 0 | yes |
| 4-3 | H?SY | 24 | 0 | yes |
| 4-4 | M2JW | 25 | 0 | yes |
| 4-5 | CYJW | 26 | 0 | yes |
| 4-6 | M5SY | 27 | 0 | yes |
| 4-Boss | C2FW | 28 | 0 | yes |
| "level select" | G050 | 28 | 100 | yes |
| "all levels" | g860 | 28 | 100 | yes (alias of G050) |

Other published strings: `18lw` → L28,C23; `196c` → L28,C163; `K2P2` → L28,C65 (all level-28 unlocks with different masks — same system, not a second mechanism); `G6K5` → L2,C0 (alias of `HYK3`, not "1-1" as one site claims). The `?` symbol is a real alphabet member (index 31), not a wildcard: `C?P6` and `H?SY` are literal codes and were decoded as such. Case differences in web listings (`g860`, `18lw`) are transcription style; the on-screen alphabet is upper-case only.

### 6.2 Mask width B(L) and state counts

| L range | 1–3 | 4–6 | 7–10 | 11–13 | 14–17 | 18–20 | 21–24 | 25–28 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B(L) | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
| valid C values | 2 | 4 | 8 | 16 | 32 | 64 | 128 | 256 |
| levels in band | 3 | 3 | 4 | 3 | 4 | 3 | 4 | 4 |
| states in band | 6 | 12 | 32 | 48 | 128 | 192 | 512 | 1024 |

Total distinct states = 1,954; accepted spellings = 1,954 × 128 = **250,112**.

### 6.3 Font/tile-indexed text bank (decoded)

The UI uses ASCII bytes plus control codes in the string bank at `0x08047F7C` (handles) / `0x0804A038` onward (strings):

| Code | Glyph | First observed |
|---|---|---|
| `0x82`, `0x83` | left / right arrow | `Music \x82 100% \x83` (Options → Sound) |
| `0x84` | A button icon | `Select \x84`, `Accept \x84` (password screen) |
| `0x85` | B button icon | `\x03\x85 Back` |
| `0x86`, `0x87` | L / R button icons | `Press Select + \x86 + \x87\nto wake` (Sleep prompt, confirmed on-screen) |
| `0x01`, `\n` | colour / newline control | level-name strings |

Strings were found because they are ASCII, but the password keyboard itself is rendered from the separate alphabet literal at `0x08031144`; both banks were decoded before concluding the negative about debug labels.

## 6b. Enumeration

### Space definition
- Alphabet size 32, length 4 → **32⁴ = 1,048,576** representable strings.
- Packed as four 5-bit indices in byte lanes 0/1/2/3; bits 5–7 of each byte are always 0 (12 structural zero bits).
- Payload = 5-bit level `L` (1–28) + 8-bit mask `C`; 7 filler bits are ignored by the validator.
- Check/bound = unary group: `C < 2^B(L)`. No separate checksum field; the bound *is* the validity test.

### Accepted-set size (proved by running the reimplemented validator over all 1,048,576 inputs)
**250,112 accepted (23.8525 %)**, exactly `128 × Σ_{L=1..28} 2^B(L) = 128 × 1,954`.
Per-level counts: L1–3: 256 each; L4–6: 512; L7–10: 1,024; L11–13: 2,048; L14–17: 4,096; L18–20: 8,192; L21–24: 16,384; L25–28: 32,768.

### Novel codes (not on 3rd party cheat indexes or any wiki) and in-game proof

| Generated code | Payload | How derived | In-game proof |
|---|---|---|---|
| `R1K5` | L1, C0 | flip ignored filler bit 0 of `Q2K5` | accepted → "1-1 When Robots Attack" (`test_R1K5.png`) |
| `RXK5` | L3, C0 | generated from validator; canonical level 1-3 | accepted → "1-3 Robot from the Goo Lagoon" (`test_RXK5.png`); proves published `QGT3` is a typo |
| `R?3X` | L21, C48 | generated for level 21 with non-zero mask | accepted → "Squid Vicious" (`test_level29.png`) |

All three are spellings the game accepts but that appear in no published list; `RXK5` additionally exercises a level whose published code is invalid.

### Bounds proved by in-game rejection

| Rejected code | Intended violation | Model result | Observed |
|---|---|---|---|
| `H1K5` | L = 0 (below range) | `1 <= L` fails | empty password keyboard, no level |
| `R1FY` | L = 29 (above range) | `L <= 28` fails | empty password keyboard |
| `RXFY` | L = 31 (5-bit max) | `L <= 28` fails | empty password keyboard |
| `81K5` | L = 1, C = 2 (mask exceeds 2^B(1)=2) | `C < 2` fails | empty password keyboard |
| `QGT3` | published typo: L1 with C12 | `C < 2` fails | rejected (verifies decoder against a published error) |

These turn "the game rejects out-of-range values" into measured results for both field layers (level range and mask range). The seven filler bits were proven ignored by the accepted alias `R1K5`.

### Negative results, bounded
- **No second code system.** The input alphabet (32 symbols) matches the alphabet literal used by the encoder/decoder exactly. The only alphabet xrefs are the encoder (`0x0800F550`) and the index→char accessor (`0x0800F740`). Published "special" codes all decode to `(L28, C*)` in the same format, so there is no separate unlock mechanism.
- **No reachable debug menu.** Strings 48–51 exist at `0x0804A4DC`/`EC`/`F8`/`50C`, but a whole-ROM scan found **zero** 32-bit pointers to their handle-table entries (`0x0804803C/40/44/48`), zero direct pointers to the strings outside the self-pointer table, and no reachable screen after walking title, main menu, Continue/password, Options/Sound/Credits, chapter maps 1–4, level maps, Photo Album, pause, Sleep and level gameplay. `Select+L+R` on the pause screen did not open a menu; on the Sleep screen it is the documented wake combination. Classification: dead/gated developer labels (§16.3), confidence *inferred* for the dead-code claim, *observed* for the absence of a reachable entry.
- **Not a cheat-device artifact.** No GameShark/CodeBreaker codes were used; everything above is developer-intended input on the real screen.

## 7. Validation evidence

- **Observed** (emulator screenshot / file bytes): boot crash of the delivered ROM and clean boot of the 4-byte-restored copy; every menu screen listed in §3.2; acceptance of Q2K5, R1K5, RXK5, R?3X, G050; rejection of H1K5/R1FY/RXFY/81K5; pause screen displaying the entered password; Sleep prompt glyphs; Photo Album contents; savestate byte changes at EWRAM `0x02000054` and IWRAM `0x03000FCE`.
- **Derived** (disassembly / reimplementation): all function addresses and roles; the XOR key `0x1A071605`; bit positions for L and C; the seven ignored filler bits; the unary bound B(L); exact enumeration count; the 28/30 published-code decode table; the two published typos; the font control-code meanings.
- **Inferred**: that `C` is a per-level collectible/photo-unlock mask (different masks change Photo Album contents, but individual bit→photo mapping was not exhaustively proven); that strings 48–51 are dead developer labels rather than a gated menu reachable by an undiscovered combination.
- Cross-check: the reimplemented decoder agrees with all 30 published codes (28 valid, 2 identified as errors), with the 5 accepted in-game codes and the 5 rejected in-game codes; no disagreement was found.

## 8. Unknowns

- Exact semantics of each of the 8 `C` bits (likely golden-spatula / photo-album unlock flags; the bit→photo mapping was not exhaustively enumerated).
- Whether any input combination on a screen not visited (e.g. during a cutscene or after full game completion) exposes the four debug labels; no such screen was reachable in the tested states.
- The purpose of the injected crt0 at `0x087FB200` (appears to be a defective scene cracktro/loader); it was bypassed for analysis, not repaired.
- The ROM's own validator could not be called as a GDB oracle because port 2345 was occupied by another session; the enumeration therefore uses the reimplementation, cross-checked in-game.

## 9. Tooling

- `md5sum`, `sha1sum`, `sha256sum`, `file`, `xxd`, `strings -t x`, `grep -aboF` (Phase 0/1).
- Python 3 + `capstone` for literal/BL xref scans (`xref.py`, `model.py`, `encode.py`, `enter.py`) in `/tmp/spongebob2`.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb/-M force-arm` for disassembly (note: this build rejects `-M force-arm`; ARM ranges disassemble correctly by default).
- mGBA 0.10.5 under Xvfb `:319` with openbox; `xdotool` XTEST input; `scrot` screenshots; `gdb-multiarch` (one successful register/RAM read at PC `0x08017746`).
- mGBA `.ss1` savestates parsed by extracting the zlib-compressed `gbAs` PNG chunk for RAM diffs (§16.13).
- Web sources consulted as data: 3rd party cheat indexes password lists for this GBA SKU; all literals verified against the ROM.
- Legal note: no ROM bytes, graphics, music or game text are redistributed here; only hashes, addresses, algorithms and independently generated codes are published.
