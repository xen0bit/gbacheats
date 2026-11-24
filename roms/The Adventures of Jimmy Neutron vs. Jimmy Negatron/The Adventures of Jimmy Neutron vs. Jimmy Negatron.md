# The Adventures of Jimmy Neutron vs. Jimmy Negatron (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Adventures of Jimmy Neutron vs. Jimmy Negatron.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `JIMMY2002AGB` |
| Game code | `AJXE` (CRC32 published for this SKU: D2CED674) |
| Maker | `78` |
| Version | `0x00` (Rev.00), complement `0xA6`, header checksum `0x0000` |
| Entry word | `0xEA00002E` (stock; no cracktro) |
| MD5 | `fce7adb1c33f9a75a03e1c425cb9930d` |
| SHA-1 | `5a4b0f5782e42f04040a4b0fc0073e726e725681` |
| SHA-256 | `20ea655f5ffe031183aaec8f9ad79253b0ce20e62a9413cf6928d62be1d414a7` |

Work dir / evidence: `/tmp/jimmynegatron/`.

## 2. Executive summary

This SKU has a **developer-intended 8-symbol password system** reached from the lab "Main Menu": press Down once until Jimmy says "Can I continue a game?", press A → `Enter Code`. It is **not** a hard-coded code table: it is an **algorithmic 48-bit encoder/decoder** with a 43-bit payload, a 5-bit checksum, a fixed bit-permutation network, a PRNG-driven permutation array regenerated from the first decoded field, and explicit semantic range checks. Exactly one code string maps to each accepted field combination (1,816,657,920,000 accepted strings out of 64^8 = 281,474,976,710,656).

The on-screen keyboard has 32 base symbols plus a circled variant of each (L button), i.e. 6 bits per symbol × 8 = 48 bits. The decoder was reimplemented bit-for-bit in Python (`decode.py`), a field-exact minter was built (`mint.py`), and its accept/reject decisions were checked against the ROM on 10+ inputs. A **code absent from every published list** was minted, typed on the real keyboard in mGBA, and accepted (loaded Dark Dimension with 979 starting coins). Bounds were proven by in-game rejection of bad-checksum and out-of-range-field codes.

The 12-character codes widely published for "Jimmy Neutron: Boy Genius" do **not** apply to this SKU (different alphabet/screen); the 8-character circled-letter codes DO apply and were structurally verified.

## 3. How to reproduce

1. mGBA 0.10.5 under Xvfb: `SDL_AUDIODRIVER=dummy mgba -3 <rom>` on `DISPLAY=:318`. Keymap A=`x`, B=`z`, Start=`Return`, D-pad=arrows, L=`a`, R=`s`.
2. Boot; press Start; advance the intro dialogue with **A (`x`)**, not Start; choose a difficulty (Easy/Normal/Hard) and start/continue; from in-game press Start → EXIT → confirm EXIT to return to the lab.
3. In the lab (computer shows a spinning blue atom), press **Down once** → tooltip "Can I continue a game?" → **A** → `Enter Code`.
4. Keyboard grid (base / circled via L):
   ```
   B C D F G H J K L
   M N P Q R S T U W
   X Y Z 0 1 2 3 4 5
   6 7 8 9 $ del OK
   ```
   Move with the D-pad, press A to append a symbol, `del` to backspace, `OK` to submit.
5. Novel proof code, typed exactly as shown (parentheses = circled variant, toggle with L):
   **`(P)(N)(F)4(J)(W)7(H)`** — byte values `2B 2A 23 19 26 31 1C 25`.
   Screenshot before submit: `/tmp/jimmynegatron/ui_typed2.png`; after submit: `/tmp/jimmynegatron/ui_final_crop.png` ("Dark Dimension", coins 979).
6. A published-structure code verified in-game: `DBD7M7GZ` (the ambiguous 6th symbol is `7`, not circled V) → bytes `02 00 02 1C 09 30 04 14` → green Retroland area, 2 coins (`/tmp/jimmynegatron/orac_retro_real_crop.png`).

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Address | Role |
|---|---|
| `0x08000B10` | `ok_handler`: copies 10 bytes from `0x03000DC0` to stack, calls decoder, writes decoded fields, applies all range checks, clears the accept flag on failure |
| `0x08000DA8` | bit-permutation network (strides r9 = 7,6,5,4,3 over 48 bits, 8 bytes × 6 bits) |
| `0x08000D04` | inverse-direction bit-permutation network (strides 3..7); not exercised by the decode path |
| `0x08000C90` | builds the 48-byte permutation `P`: `P[i]=i`, 256 Fisher-Yates swaps with j∈[10,47] from LCG state at `0x03000E7C` |
| `0x08000EE0` | bit extractor: for output bit i, `v=P[i]; bit=(buf[v/6]>>(v%6))&1` |
| `0x08000F44` | clears the 5 bits selected by `P[43..47]` in the buffer before the checksum |
| `0x080379B8` | unsigned-divide helper (`__aeabi_uidiv`-style), called with divisor 6 |
| `0x0803BAF4` | `"Code:"`; `0x0803BAFC` `"Failed Code"`; `0x0803BB08` `"OK"`; `0x0803BB0C` `"del"`; `0x0803BB10` `"Enter Code"`; `0x0803BB34` `"DIFFICULTY"`; `0x0803BB2C/24/1C` `Easy/Normal/Hard` |
| `0x0809DB00..0x0809DC80` | pointer table for all menu/help strings used by this screen |
| `0x03000DC0` | 8-byte code input buffer (values 0..31 normal, 32..63 circled); 10 bytes copied by `ok_handler` |
| `0x03000DE0..0x03000E05` | decoded field struct: `+0x20=f5<<8`, `+0x22=f6<<8`, `+0x24=f9\|(f2<<10)`, `+0x26=f10`, `+0x2D=f1`, `+0x30=f4`, `+0x38=f2b`, `+0x43=f3`, `+0x44=f1b`; `+0x38` is zeroed on rejection |
| `0x03000E7C` | LCG state for permutation generation (u32) |

## 5. Algorithm

Precise pseudocode (verified against GDB intermediate dumps):

```
LCG_MUL = 0x41C64E6D ; LCG_ADD = 0x3039

permute48(buf[8]):            # 0x08000DA8
  for stride in 7,6,5,4,3:
    i = 0
    while i + stride <= 47:
      swap bit i of buf with bit i+stride   # bit b -> byte b/6, bit b%6
      i += 2*stride

gen_perm(seed):               # 0x08000C90
  P = [0..47]; state = seed & 0xFFFF
  repeat 256 times:
    j1 = next_bound(); j2 = next_bound()   # state=state*MUL+ADD; j=(state>>26)+10; retry if >47
    swap P[j1], P[j2]

extract(P, buf, pos, n):      # 0x08000EE0
  for k in 0..n-1:
    v = P[pos]; q=v//6; r=v%6; bit=(buf[q]>>r)&1
    result |= bit<<k; pos += 1

validate(input8, seed):
  buf = permute48(input8) + [0,0]
  P = gen_perm(seed)
  f10 = extract(P,buf,pos,10)          # pos = 10
  P = gen_perm(f10)                   # CHAIN: permutation regenerated from first field
  f6  = extract(P,buf,pos,6);  pos=16
  f5  = extract(P,buf,pos,5);  pos=21
  f3  = extract(P,buf,pos,3);  pos=24
  f9  = extract(P,buf,pos,9);  pos=33
  f2  = extract(P,buf,pos,2);  pos=35
  f1  = extract(P,buf,pos,1);  pos=36
  f4  = extract(P,buf,pos,4);  pos=40
  f2b = extract(P,buf,pos,2);  pos=42
  f1b = extract(P,buf,pos,1);  pos=43
  chkfield = extract(P,buf,pos,5)      # pos = 48
  for k in 0..4:                        # 0x08000F44, uses STALE pos=43
    v=P[43+k]; q,r=divmod(v,6); buf[q] &= ~(1<<r)
  s = 0
  for x in buf[0..9]: s = (s + x + (x>>4)) & 0xFF
  checksum = s & 0x1F
  accept iff:
    chkfield == checksum
    f6 != 0 and f6 <= 40
    f5 <= 20
    f10 <= 999
    f4 <= 10
    f2b != 0
    (f9 | f2<<10) <= 0x0C01   # vacuous for an 11-bit field
```

Because `0x08000F44` clears exactly the bits that encode `chkfield`, the checksum is independent of the check field; a valid code can always be minted for any in-range field tuple.

## 6. Tables

**Alphabet (index → glyph).** Base 0..31: `B C D F G H J K L M N P Q R S T U W X Y Z 0 1 2 3 4 5 6 7 8 9 $`. Circled value = base index + 32 (L button). 64 values = 6 bits.

**Field layout (43-bit payload + 5-bit check):**

| Field | Bits | Range enforced | Observed meaning / confidence |
|---|---|---|---|
| f10 | 10 | 0..999 | **Observed:** starting coins (coded 979 → HUD 979; coded 500 → HUD 500; coded 2 → HUD 2) |
| f6 | 6 | 1..40 | Unknown (must be nonzero) |
| f5 | 5 | 0..20 | Unknown |
| f3 | 3 | 0..7 | Unknown |
| f9 | 9 | combined bound vacuous | Unknown |
| f2 | 2 | combined bound vacuous | Unknown |
| f1 | 1 | 0..1 | Unknown flag |
| f4 | 4 | 0..10 | **Observed:** destination level/world selector. 0 = green Retroland-type area, 1 = Dark Dimension, 3 = Cindy's Dream, 7 = Quantum Dimension, 8 = Jelly Dimension, 9 = Rocket Launch Site |
| f2b | 2 | 1..3 | Unknown, must be nonzero |
| f1b | 1 | 0..1 | Unknown flag |
| chkfield | 5 | == checksum | Checksum |

**Novel code (not in any published list):** `(P)(N)(F)4(J)(W)7(H)` = `2B 2A 23 19 26 31 1C 25`. Fields: f10=979, f6=6, f5=7, f3=6, f9=87, f2=0, f1=1, f4=1, f2b=1, f1b=0, chk=7. Accepted in-game via the real keyboard UI.

**Published codes checked:**
- 3rd party cheat indexes 8-char circled codes belong to this SKU. `DBD7M(V)GZ` has exactly one valid decoder mapping when the ambiguous `(V)` is `7` → `02 00 02 1C 09 30 04 14`, f4=0, f10=2; in-game it loads the green Retroland area with 2 coins. `NBODLH(D)L` has two valid mappings (f4=3). `D(B)(Y)B4V(H)V` has many; `xcqdkvlp` has none under this keyboard's alphabet — likely transcription errors from a different region/font.
- The 12-char `?+!-$` codes on the same 3rd party cheat index page are for the sibling game *Jimmy Neutron: Boy Genius*; no literal appears in this ROM and the symbols are absent from this SKU's keyboard. Recorded as not applicable, not as "broken".

## 6b. Enumeration

**Space definition.** 8 symbols × 6 bits = 2^48 = 281,474,976,710,656 representable strings. Payload 43 bits, checksum 5 bits.

**Accepted set (fresh state, seed = 0):**

```
f10 1000 values × f6 40 × f5 21 × f3 8 × (f9,f2) 2048 × f1 2 × f4 11 × f2b 3 × f1b 2
= 1,816,657,920,000 accepted strings  (~1 in 154.9)
```

The `(f9,f2) <= 0x0C01` comparison is vacuous because the field is only 11 bits; this was corrected after an in-game acceptance of f9=269 proved the initial `0x010C` reading wrong.

**Chaining.** The permutation seed is read from `0x03000DE6` (f10 of the previously entered code). All enumeration figures above assume a fresh state (seed 0), as in a new game / clean savestate. After a successful code, the same 8-byte string can decode differently if re-entered, because `P` is regenerated from that code's f10.

**Novel codes generated and accepted:**

| Code (bytes) | Keyboard form | Fields | Result |
|---|---|---|---|
| `2B 2A 23 19 26 31 1C 25` | `(P)(N)(F)4(J)(W)7(H)` | f10=979, f4=1 | Typed on the real UI → Dark Dimension, 979 coins (`ui_final_crop.png`) |
| `25 29 23 13 01 01 19 3F` | `4  N  F  2  M  1  Y  $` (mix of base/circled) | f10=500, f9=269, f4=1 | Savestate-oracle → Dark Dimension, 500 coins; proved the vacuous bound |

**Bounds proven by in-game rejection (all produced "Failed Code"):**

| Test | Field change | Model | ROM |
|---|---|---|---|
| good control | `25 2D 27 13 08 09 09 3D` | accept | accepted |
| f4 = 11 (>10) | `25 2D 37 13 0A 01 0D 2D` | reject | Failed Code |
| f4 = 15 (>10) | `25 2D 37 1B 0A 01 0D 3D` | reject | Failed Code |
| f6 = 0 (must be nonzero) | `25 2D 27 13 08 01 08 2C` | reject | Failed Code |
| f6 = 41 (>40) | `25 2D 27 11 18 05 38 2C` | reject | Failed Code |
| f5 = 21 (>20) | `25 2D 26 17 08 01 19 3D` | reject | Failed Code |
| f2b = 0 (must be nonzero) | `25 2D 37 13 08 09 11 2D` | reject | Failed Code |
| f10 = 1000 (>999) | `11 2F 36 27 10 17 08 18` | reject | Failed Code |
| bad checksum (one check bit flipped on a valid code) | `25 2D 37 13 08 09 09 3D` | reject | Failed Code |

All 9 rejection cases agreed with the Python model; acceptance/rejection agreement is exact over the 10 tested inputs.

## 7. Validation evidence

- **Observed:** mGBA screenshots of the title, lab, DIFFICULTY menu, `Enter Code` keyboard (normal + circled), typed novel code, and the resulting "Dark Dimension" gameplay with 979 coins; "Failed Code" for each rejection; success screens for f4 variants mapping to named worlds; green animated text `0F4Y7H…` on the lab computer.
- **Observed (RAM):** GDB read `0x03000DC0` = `00 01 02 03 04 05 06 07` after typing `BCDFGHJK`; circled `B` = `0x20`; breakpoint dumps confirmed `permute48` output `2f 15 15 28 05 02 30 37`, the 48-byte `P` table, the chained seed (= first decoded field), all decoded field writes at `0x03000DE0+`, the post-`F44` buffer, and the final checksum `0x8A & 0x1F = 0x0A` against extracted field `0x0A` for a code where the old model predicted a different check field.
- **Derived:** the complete validator algorithm in §5, the field layout, the accepted-set count, and the minter (which reproduces a known accepted code byte-for-byte).
- **Inferred:** field names for f6, f5, f3, f9, f2, f1, f2b, f1b are positional labels only; their gameplay semantics were not isolated. f10=coins and f4=level are observed.

## 8. Unknowns

- Semantics of f6, f5, f3, f9, f2, f1, f2b, f1b (ranges are proven; meanings are not). The inverse permutation at `0x08000D04` suggests an encoder exists, but no in-game generator surface was found for the 8-symbol codes.
- The green animated text on the lab computer (`0F4Y7H…`, cycling with a partial reveal) is a separate display: the input buffer at `0x03000DC0` remained `FF×8` while it was shown, so it is not the code buffer. It may be an unfinished "continue" feature (the same string bank contains "Now it is not implemented."); not resolved.
- Published lowercase code `xcqdkvlp` has no valid mapping under this SKU's alphabet/decoder; could be a different regional keyboard.
- Which exact world names correspond to f4 = 0, 2, 4, 5, 6, 10 (these loaded levels but showed no captured name banner).

## 9. Tooling

- Custom scripts in `/tmp/jimmynegatron/`: `decode.py` (validator reimplementation), `mint.py` (field-exact code minter), `patchstate.py` (mGBA `.ss` `gbAs` chunk patcher, preserves PNG CRC), `oracle.sh` (patch → boot → OK → screenshot), `k.py` (xdotool key helper), `enter_code.py` (UI entry sequence).
- `arm-none-eabi-objdump -M force-thumb`, `gdb-multiarch` against mGBA's GDB stub, `capstone` for literal/BL scans, `tesseract` for screen OCR, `scrot`/ImageMagick for captures.
- Note: other agents' processes held GDB port 2345 intermittently; the working stub was verified by `netstat` PID before each run. The emulator binary was copied to `emu_jn` to avoid other agents' process-wide cleanup.
- No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms, and generated codes are published.
