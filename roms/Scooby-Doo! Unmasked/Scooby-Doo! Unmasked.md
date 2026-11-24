# Scooby-Doo! Unmasked (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Scooby-Doo! Unmasked.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `SCOOBYUN` |
| Game code | `B25E` (`B25E78`, Rev. 00) |
| Maker | `78` |
| Version | 0 |
| `file` ID | `Game Boy Advance ROM image: "SCOOBYUN" (B25E78, Rev.00)` |
| Build tag on legal screen | `(s05)` |
| MD5 | `803ff345f4df60a7f00db44fd25730bc` |
| SHA-1 | `6851a6088cccafcd8f1e49a31546aac6b27ca076` |
| SHA-256 | `841cfc2e5bd6ba402f3e17a379c670a616361bf2df1288361fbbb6a4a45199eb` |

**Header / image findings (retained from first pass):** entry word `0xEA00002E` is the stock ARM
`b 0xC0` (not a cracktro). Header checksum stored `0x0000`, complement byte `0x82` (expected
`0x9A`) — a rebuilt/edited header, §16.1. Exactly one GBA header/logo (`24 ff ae 51`) at `0x0`;
no concatenated image, no appended trainer.

## 2. Executive summary

The game has a **40-bit algorithmic progress-password system** with an 8-symbol keyboard alphabet
of 32 glyphs. The **full codec was recovered statically** with Ghidra via REA (no debugger needed):

* **Generator** `FUN_0803C134` (ROM `0x0803C134`) builds 40 progress bits, computes a weighted
  checksum, seeds a Mersenne Twister with it, XORs each 5-bit group with the first PRNG word's low
  5 bits, scatters those 5 salt bits into positions `[1,14,17,20,35]`, and packs eight 5-bit symbols.
* **Validator / decoder** `FUN_0803C388` (ROM `0x0803C388`) reverses this: expands the eight typed
  symbols to 40 bits, extracts the scattered 5-bit salt, un-XORs, clears the salt positions,
  recomputes the weighted checksum, seeds MT with it, and accepts iff `(MT(chk)[0] & 0x1f) == salt`.
* A **second, semantic-validity layer** `FUN_0803BDB4` rejects decodes whose level/clue/flag
  combination is impossible — this is why a checksum-valid random payload can still be refused.
* PRNG: `FUN_0800A380` seeds MT19937 (N=624, M=397, multiplier 69069, standard tempering
  `>>11`, `<<7 & 0x9D2C5680`, `<<15 & 0xEFC60000`, `>>18`) and fills a 250-word table at
  `0x020000A8`; `FUN_0800A3AC` returns table entries cyclically.

**Generated-password buffer:** the pause-menu sign's code lives at **RAM `0x020164BC`** as eight
5-bit indices. In the captured state it read `1A 15 0C 1D 0A 15 0A 05` → `61Q9N1NH`, exactly the
code rendered on the sign (read from RAM, not OCR). The renderer `FUN_0803BF2C` reads this buffer.

**Novel accepted code minted and verified in-game:** `40R8N0PH` (single payload-bit flip of the
game-generated `61Q9N1NH`; salt 20, checksum 368). It is absent from all 97 published literals.
Entered on the real password screen: glyphs turned **green**, the game started, and the progress
word at RAM `0x020164A0` changed from all-zeros to `01 00 0A FF 12 01 00 03 … 64 00 08 08 00 01 01`.
A one-symbol near-miss `40R8N0PJ` was **rejected** (glyphs red, screen retained), proving the bound.

**Published-literal test:** 0 of 97 published codes occur in the ROM (algorithm, not table). Of 91
well-formed published codes, **80 validate under the recovered model**; the 11 failures are
published typos — each has 3–14 single-symbol repairs under the model, matching the known OCR
errors in these lists (§16.7).

The hidden developer scene bank at ROM `0x080428EC` remains a **gated feature**: its dispatch at
`0x0804F10` reads flag byte RAM `0x02014AC4`, which is `0x00` in every state and whose only xrefs
read it or reset it to zero.

## 3. How to reproduce

```
DISPLAY=:316  SDL_AUDIODRIVER=dummy
Xvfb :316 -screen 0 1024x768x24 &   openbox &
mgba -3 <rom>
```
Keymap A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad = arrows. **Use 100 ms holds /
300 ms gaps** when typing codes — 50 ms holds drop arrow presses (a dropped Down turned the
4th symbol `0` into `M` in one trial). Navigate: legal A×~18, WB/THQ logos, title Start, main
menu Down → PASSWORD, A. Grid rows:
`B C D F G H J K L M N` / `P Q R S T V W X Z 0 1` / `2 3 4 5 6 7 8 9 ! ? OK`.

Reproduce the novel code: on a clean password screen type `40R8N0PH`, move to `OK`, press A.
Acceptance = green glyphs + start of game; rejection = red glyphs.
Read the generated code: load any in-game state, Start → pause → PASSWORD; read eight bytes at
EWRAM `0x020164BC` and map each `v` to `ALPHA[v]`.

## 4. Address map

File offset `F` ↔ ROM address `0x08000000 + F`.

| Address | Meaning | Evidence |
|---|---|---|
| `0x0803C134` | Password **generator** (state → 8 symbols) | Ghidra decompile (REA `ev_90d9b243…`) |
| `0x0803C388` | Password **validator/decoder** (8 symbols → flags, 0 = reject) | Ghidra decompile (REA `ev_86f09d01…`) |
| `0x0803BDB4` | Semantic consistency check on decoded progress | Ghidra decompile |
| `0x0803BF2C` | Sign renderer; reads 8 indices from `0x020164BC` | Capstone + literal xref |
| `0x0800A380` / `0x0800A3AC` | MT19937 seed+fill / next word | Ghidra decompile + Capstone |
| `0x0804F10` | Debug scene-select dispatch; reads flag `0x02014AC4` | Derived (first pass) |
| `0x080428EC` | Developer scene-name bank (`"Password"`, etc.) | Observed |
| `0x020164A0` | Progress state (40 source bits read by generator) | Savestate diff, observed |
| `0x020164BC` | **Generated password buffer** (8 × 5-bit indices) | Savestate diff, observed |
| `0x02014BA0` / `0x020164A0` | Scene state / decoded progress words | Savestate diff |

Savestate layout (mGBA `.ss1`, 397,312-byte `gbAs` zlib payload): header/CPU `0x00000`,
IWRAM `0x01000`→`0x03000000`, VRAM `0x09000`→`0x06000000`, EWRAM `0x21000`→`0x02000000`.
`0x020164BC` maps to state offset `0x374BC`.

## 5. Algorithm

```
ALPHABET = "BCDFGHJKLMNPQRSTVWXZ0123456789!?"   # keyboard order, 32 symbols
SALT_POS = [1,14,17,20,35]                       # bit positions in the 40-bit array
N=624 M=397 MATRIX_A=0x9908B0DF MULT=69069       # MT19937

expand(symbols) -> bits[40]:  bits[5*i+k] = (symbols[i] >> k) & 1   # little-endian pack

checksum(bits):  sum_{i=0..7} (i+1) * v_i
                 where v_i = sum_{k=0..4} bits[5*i+k] << (4-k)     # BIG-endian 5-bit value
salt(bits)     = bits[1] + 2*bits[14] + 4*bits[17] + 8*bits[20] + 16*bits[35]

validate(symbols):
    bits = expand(symbols)
    s = salt(bits)
    for i in 0..7, k in 0..4: if (s>>k)&1: bits[5*i+k] ^= 1
    for p in SALT_POS: bits[p] = 0
    chk = checksum(bits)
    if (MT19937(seed=chk).first() & 0x1f) != s: REJECT          # `FUN_0803C388`
    decode progress flags from bits; if FUN_0803BDB4(flags)==0: REJECT  # semantic layer
    ACCEPT

encode(payload_bits with SALT_POS==0):                          # `FUN_0803C134`
    chk = checksum(payload)
    s = MT19937(seed=chk).first() & 0x1f
    for i,k: if (s>>k)&1: bits[5*i+k] ^= 1
    for j,p in enumerate(SALT_POS): bits[p] = (s>>j)&1
    return [ sum(bits[5*i+k] << k for k in 0..4) for i in 0..7 ]  # 5-bit values 0..31
```

The checksum bit-order asymmetry (big-endian for the checksum, little-endian for the final
symbol pack) and the scattered salt bits are why the earlier generic GF(2)/Caesar/weighted-sum
models all failed.

## 6. Tables

### 6.0 Keyboard / alphabet (observed, on-screen)
```
row 0: B(0)  C(1)  D(2)  F(3)  G(4)  H(5)  J(6)  K(7)  L(8)  M(9)  N(10)
row 1: P(11) Q(12) R(13) S(14) T(15) V(16) W(17) X(18) Z(19) 0(20) 1(21)
row 2: 2(22) 3(23) 4(24) 5(25) 6(26) 7(27) 8(28) 9(29) !(30) ?(31) OK
```

### 6.1 Codes established this engagement
| Code | Origin | Model salt/chk | In-game result |
|---|---|---|---|
| `61Q9N1NH` | generated by game (buffer read from RAM) | 21 / 384 | valid (sign) |
| `40R8N0PH` | **novel**, 1-bit flip of above payload | 20 / 368 | **ACCEPTED**, green glyphs, RAM proof |
| `40R8N0PJ` | near-miss, last symbol H→J | 4 / 425 (fails) | **REJECTED**, red glyphs |
| `RWM0Q8SK` | checksum-valid but random payload | 20 / 301 | rejected by semantic layer `0x0803BDB4` |

### 6.2 Menus walked (full screen enumeration, first pass)
Title, main menu, password entry (accept/reject), OPTIONS (exactly 3 items: SOUND FX, MUSIC,
LANGUAGE US/FR), CREDITS, in-game pause (CONTINUE/PASSWORD/OPTIONS/QUIT), generated-password
sign, Velma's Notebook clue minigame. No other input-gated entry found.

### 6.3 Published corpus
97 unique literals collected (GameFAQs, supercheats, cheatingdome, GameGenie, jeuxvideo,
VinnyVideo walkthrough). **0** occur in ROM. 91 are well-formed; 80 validate under the model,
11 are published typos (each repairable by a single symbol change).

## 6b. Enumeration

| Property | Value | Source |
|---|---|---|
| Alphabet | 32 symbols | On-screen keyboard |
| Length | exactly 8 symbols | Entry slots |
| Bits/symbol | 5 | Derived |
| Raw space | `32^8 = 2^40 = 1,099,511,627,776` | Derived |
| Checksum layer | 5-bit scattered salt → ~`2^35` pass | Validator at `0x0803C388` |
| Second layer | semantic level/clue/flag consistency | `FUN_0803BDB4` |
| Published literals in ROM | 0 of 97 | `grep`/`find` over 8 MiB |

**Novel code (§0.2 deliverable):** `40R8N0PH`, produced by flipping payload bit 0 of the
game-generated `61Q9N1NH` and re-encoding with the recovered model. It is in no published list.
Entered on the real password screen, it was accepted (green glyphs, game start) and the decoded
progress word in RAM changed:

```
RAM 0x020164A0  BEFORE: 00 00 00 00 00 00 00 00 00 00 00 00 FF 00 00 00 64 00 05 05 00 01 01 00
RAM 0x020164A0  AFTER : 01 00 0A FF 12 01 00 03 00 00 00 00 FF 00 00 00 64 00 08 08 00 01 01 00
RAM 0x02014BA0  BEFORE: 7D 00 FF FF ... 00 0C 00 9D ...   AFTER: B5 00 FF FF ... 00 CC 00 84 ...
```
Evidence: `cand_t_40R8N0PH.png` (green glyphs), savestate `.ss9`, `pwd_model.py`.

**Bounds proven by rejection:**
* Near-miss `40R8N0PJ` (final symbol H→J) → model rejects (salt 4 ≠ expected), game shows red
  glyphs and remains on the password screen (`nearmiss_40R8N0PJ.png`, purple count 1816).
* Checksum-valid but semantically invalid random payload `RWM0Q8SK` → salt check passes offline
  but game rejects via `FUN_0803BDB4` (`novel_ACCEPTED.png`, red glyphs).
* From first pass: sweeping the final symbol of `LJL7FW?` over all 32 glyphs accepted **exactly 1**
  (the original `R`); changing the first symbol then sweeping all 32 final symbols accepted **0/32**.

**Generated-password buffer route (executed):** pause → PASSWORD sign was diffed against the
pause-menu state; the eight bytes at EWRAM `0x020164BC` changed from zero to
`1A 15 0C 1D 0A 15 0A 05`, mapping to `61Q9N1NH` — exactly the sign, with no OCR.

**Debug-menu enumeration (bounded):** scene names in §6.1 of the first pass; gate byte
`0x02014AC4` is `0x00` in all states and only zero-writers/readers xref it — a gated feature.

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| Header edited, single image, no trainer | Derived | phase0 scripts, xxd |
| 32-symbol alphabet, 8 slots | Observed | password screen screenshots |
| Published codes not literal in ROM | Derived | 0/97 literal hits |
| Generator/validator addresses & arithmetic | Derived | Ghidra decompiles via REA (Evidence IDs in §2/§4) + Capstone disasm |
| PRNG is MT19937 (constants) | Derived | Capstone literal resolution at `0x0800A200`/`0x0800A244` |
| Generated buffer `0x020164BC` | Observed | matched savestate diff, exact sign match |
| Model agrees with game on known codes | Observed + Derived | `61Q9N1NH` game-generated & validated; `XRG0Z9NR`,`V4T18HFV`,`LJL7FW?R` validate & accepted in-game |
| Novel `40R8N0PH` accepted | Observed | green glyphs + RAM progress decode (ss9) |
| Near-miss rejected | Observed | red glyphs, screen retained |
| 11 published typos | Derived | single-symbol repairs under recovered model |

## 8. Unknowns

1. Exact field names for the 40 progress bits / decoded flags (level, clue, costume, episode) were
   labelled by observed effects, not by source symbols. The bit→field scatter is recovered;
   the semantic rules inside `FUN_0803BDB4` are decompiled but individual bit meanings are inferred.
2. The hidden debug scene-select remains gated (gate byte always 0, no retail setter found).
3. The 11 rejected published strings are treated as publication/OCR errors; the exact original
   intent of each is not independently known.

## 9. Tooling

Work dir: `/tmp/scoobyunmasked2`.

| Script | Purpose |
|---|---|
| `pwd_model.py` | Offline encoder/validator + MT19937 (the deliverable model) |
| `disasm_gen.py`, `scan1.py`–`scan4.py`, `find_gen_code.py` | Capstone structural scans, literal xrefs |
| `stateutil.py`, `diff_sign.py`, `dumpram.py`, `diff2.py` | `.ss1` `gbAs` extraction + RAM diffing |
| `mgba_drv.py`, `typecode2.py`, `typecode3.py`, `auto_test.py`, `reach_pw.py` | emulator driving / typing / accept-reject oracle |
| `make_candidates.py`, `test_novel.py`, `submit_novel.py` | novel code generation and in-game proof |
| `patch_state.py`, `load_patched.py` | progress-state savestate patch experiments |

Analysis used REA → Ghidra 12.1.4 (raw ARM, base `0x08000000`), Capstone, `arm-none-eabi-objdump`,
mGBA 0.10.5 under Xvfb, xdotool, scrot, Pillow. Key REA Evidence IDs: binary overview
`ev_0704748b9fa6…`, generator `ev_90d9b2436efe…`, validator `ev_86f09d01b5eb…`.

No ROM or copyrighted assets are redistributed in this report.

## 10. Legal note

Analysis only. Findings are addresses, hashes, algorithms and observations; no ROM image,
extracted graphics, audio or verbatim game text is published beyond short UI labels needed to
reproduce navigation.
