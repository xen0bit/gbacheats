# Rocket Power: Zero Gravity Zone (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rocket Power: Zero Gravity Zone.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title / code / maker | `ROCKET_POWER` / `AZZE` / `78`, version `0x00` |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| MD5 | `e77c5ae91ea4d722ecff5adb1e0e4b61` |
| SHA-1 | `323d87054796083a72f134f4f189b8ecba3b30a0` |
| SHA-256 | `95a9e351e8e887bccbe1f0096eff9441c03ef27d0bfde1bd359bce61c8346055` |

Exactly one Nintendo-logo hit (base `0x08000000`). The MODE 7 / GYMBIT cracktro at file `0x7FEAC0`–`0x7FEBE8` is an intro only; it adds no cheat trainer. All evidence below is from the stock game after the intro.

## 2. Executive summary

The Career → Stage Select → (Select) **PASSWORD** panel is a real six-symbol password system. This retry **isolated the numeric validator** that the previous report left open:

* **Validator: `0x080051CC` (Thumb)**, called from the panel's submit handler at `0x080180B6` with `r0 = GUI_object + 0x1112` — the six glyph bytes stored contiguously at `obj+0x1112 .. obj+0x1117`.
* It is a **36-bit packed code** (six bytes × six low bits, LSB-first), with a 4-bit additive checksum, a monotonic "semantic gate" bit pattern, three bounded fields, five 2-bit stat fields and an eight-stage level-unlock range table.
* The validator was reimplemented bit-for-bit in Python (`validator.py`) and **cross-checked against the ROM's own function called as an oracle** (guide §16.19) from mGBA's `-d` debugger on eight vectors covering every gate class: **8/8 agreement**, including accepts (`r0=1`) and rejects (`r0=0`).
* **Novel accepted code minted offline:** glyph bytes `05 11 14 12 10 1A`. The ROM's validator returns `r0 = 1`; RAM diff shows the level bitmask and all decoded fields change exactly as the model predicts. It is absent from all published lists (the only published code is `$$$L0B`, which itself is absent from the ROM in all encodings and is therefore algorithmic).
* **Bounds proven** by ROM-oracle rejection of checksum, gate-monotonic and all three field-range near-misses (§6b).
* Honest gap: the on-screen `PASSWORD OK` string was **not** captured — mGBA's `-g` GDB port was occupied by another process and `-d` breakpoints at the validator did not report hits. Acceptance is instead proven by calling the ROM function itself (r0=1) plus a savestate/RAM diff, which is byte-level rather than visual proof. See §8.

## 3. How to reproduce

**Emulator:** mGBA SDL on `Xvfb :317`, `SDL_AUDIODRIVER=dummy`, `-3`. Keymap A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Savestate on the password screen: `/tmp/opencode/rocketzero2/clean_pwd.ss2`.

**Menu path (observed):** boot → A through MODE 7/legal/title → START → main menu → CAREER → STAGE SELECT → footer `D-Pad Select / Select Pass / A OK / B Back` → **Select** opens the six-slot PASSWORD panel (default glyph `B` in all six slots). OPTIONS exposes `BGM` and a developer-style `Music Test BGM` selector.

**Oracle reproduction (no UI needed):**
```
mgba -3 -d -t clean_pwd.ss2 <rom>
# at the debugger prompt, halted:
w/1 0x03007E00 5 ; ... w/1 0x03007E05 0x1A
w/r r0 0x03007E00 ; w/r r14 0x08005399 ; w/r cpsr 0x3f ; w/r r15 0x080051CD
trace 200   (repeat until r15 == 0x08005398)
i           # r0 = 00000001  => accepted
```
Scripts: `/tmp/opencode/rocketzero2/{validator.py,oracle.py,verify_bounds.py,rameffect.py}`.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x080051CC` | **password validator** (Thumb); `r0` = six glyph bytes; returns 0/1 | Derived (disassembly) + **Observed (ROM oracle r0)** |
| `0x08005170` | bit reader `read_bits(base, bitpos, nbits)`; 6 bits per byte, LSB-first | Derived |
| `0x080180B6` | call site: `bl 0x080051CC` with `r0 = obj + 0x1112` | Derived |
| `0x08017FF0` | submit handler: glyph `100`=backspace, `101`=ENTER→validator | Derived |
| `0x0804F80` / `0x0804FA4` | set / clear a level bit in the bitmask at IWRAM `0x03002780` | Derived + Observed (RAM diff) |
| `0x081195AE` | P1 permutation `[0,2,6,1,3,4,5,7]`, then ASCII `A-Za-z` text | Derived (ROM bytes) |
| `0x081195A6` | P2 permutation `[0,2,3,5,6,8,9,10]` | Derived |
| `0x081217DE` | 11×`u16` (start,end) level ranges: `(0,7),(0,7),(9,15),(17,23),(0,7),(25,31),(33,39),(33,39),(41,48),(50,56),(58,64)` | Derived |
| IWRAM `0x03002780..0x03002787` | 64-bit level-unlock bitmask written by validator | Observed (RAM diff) |
| IWRAM `0x0300278A` | 8-bit field (≤200) | Observed |
| IWRAM `0x0300278B..0x0300278F` | five 2-bit stat fields | Observed |
| IWRAM `0x03002790`/`0x03002791` | two 3-bit fields (each ≤4) | Observed |
| `0x08045C68` / `0x08045C74` | `PASSWORD OK` / `PASSWORD FAILED` strings | Derived |
| `0x08017A48` | password-screen text setup (copies both strings into text objects) | Derived (prior work retained) |
| `0x08017CF8` | panel input dispatcher, 10-entry Thumb jump table at `0x08017D14` | Derived (prior work retained) |
| `0x08017D76`/`0x08017DC0`/`0x08017F3C`/`0x08017F72` | 31-entry picker open / ±4 glyph step / slot advance / clear | Derived (prior work retained) |
| GUI object `+0x1112+i` | six glyph bytes consumed by the validator | Derived (call site) |
| GUI object `+0x111E+i*36` | per-slot display/highlight records | Derived (prior work retained) |

**Bounded negatives retained from the first pass:** published code `$$$L0B` absent under ASCII, ±0x20, XOR 0x20/0xFF, +0x80, UTF-16 LE/BE and reversed across all 8 MiB; sibling Dream Scheme / Beach Bandits XOR-key table and `subs #0x40; eors; strb` validator signature absent. This game's validator is a different implementation (bit-packed, not the sibling XOR butterfly).

## 5. Algorithm (bit-exact pseudocode)

```c
// in[0..5] = six glyph bytes (each byte's low 6 bits are used, LSB first)
u32 read_bits(int p, int n) { u32 r=0; for(k=0;k<n;k++) r |= ((in[(p+k)/6] >> ((p+k)%6)) & 1) << k; return r; }

u32 validate(u8 *in) {
  // 1) 4-bit additive checksum, stored at bit 32 (byte5 bits 2..5)
  chk = (8 + in[0]+in[1]+in[2]+in[3]+in[4] + (in[5]&3)) & 0xF;
  if (chk != read_bits(32,4)) return 0;

  // 2) eight gate bits at positions 0..7, permuted by P1 = [0,2,6,1,3,4,5,7]
  for (i=0;i<8;i++) sp[i]=read_bits(i,1);
  q[i]=sp[P1[i]];
  // MONOTONIC GATE: once a zero appears, every later q must be zero
  seen=0; for(i=0;i<8;i++){ if(seen && q[i]!=0) return 0; if(!q[i]) seen=1; }

  // 3) field bounds
  if (read_bits(18,8) > 200) return 0;
  if (read_bits(26,3) > 4)   return 0;
  if (read_bits(29,3) > 4)   return 0;

  // 4) apply level ranges: P2=[0,2,3,5,6,8,9,10], ranges at 0x081217DE
  for (i=0;i<8;i++){ (lo,hi)=ranges[P2[i]];
      for(L=lo;L<=hi;L++) if(sp[i]) set_bit(levelmask,L); else clear_bit(levelmask,L); }

  // 5) decode fields to IWRAM
  for(i=0;i<5;i++) out2[i]=read_bits(8+2*i,2);   // 0x0300278B+i
  out8  = read_bits(18,8);                        // 0x0300278A
  out3a = read_bits(26,3);                        // 0x03002790
  out3b = read_bits(29,3);                        // 0x03002791
  return 1;
}
```

Field layout of the 36-bit stream: bits 0–7 gate; 8–17 five 2-bit stats; 18–25 8-bit field; 26–28 3-bit; 29–31 3-bit; 32–35 checksum. Space: `2^36` raw spellings; acceptance requires 4 checksum bits + the monotonic gate (9 of 256 patterns) + three bounds.

## 6. Tables / enumeration (§0.2 deliverables)

**1. Space defined.** Six symbols × 6 bits = 36 bits; 31 selectable glyph values per slot; checksum 4 bits at bits 32–35; reserved/structure: monotonic 8-bit gate, three bounded fields. Publishable code `$$$L0B` is not a literal.

**2. Validator model.** `validator.py`, 8/8 agreement with the ROM oracle (§7).

**3. Novel code generated and accepted by the ROM.** Glyph bytes **`05 11 14 12 10 1A`** (picker indices 6,18,21,19,17,27 in 1-based terms). It appears in no published list. ROM oracle: `r0 = 00000001`. Decoded effect (model = RAM): five 2-bit fields `0,1,0,1,1`; 8-bit field `0x12` (18); two 3-bit fields `4,4`; level bitmask `FF 01 FE 01 00 00 FC 03` (grants level groups 0–7, 17–23, 50–56; clears the rest).

**4. Bounds proven by rejection (each verified with the ROM oracle, `r0=0`):**

| Near-miss | Bytes | Failing check |
|---|---|---|
| checksum +1 | `29 13 32 06 09 0C` | 4-bit checksum |
| checksum on accepted code | `05 11 14 12 10 1B` | 4-bit checksum |
| gate monotonicity break | `3E 17 21 24 00 12` | P1-permuted non-increasing gate |
| 3-bit field a > 4 | `3F 15 0E 0A 3E 0D` | field bound |
| 3-bit field b > 4 | `01 08 34 07 2C 2A` | field bound |
| 8-bit field > 200 | `01 04 11 1D 37 0D` | field bound |
| default all-zero | `00 00 00 00 00 00` | checksum (8 vs 0) |

**5. Glyph→symbol map (partial).** The picker writes a **6-bit glyph value directly** into the six bytes; value `0` renders as `B` (observed default `BBBBBB`). Picker navigation handlers at `0x80181CC/0x801815C/0x801822C/0x801828C` reveal a 14-column grid covering values `0..55`, with special values `100`=BACKSPACE and `101`=ENTER/OK, and the picker count written at `obj+0x121C` is **31**. Thus all bytes of the minted code (5,17,20,18,16,26) lie inside the selectable range and are typeable by picker position. The exact visible symbol for each index was not fully transcribed: the runtime font tiles are loaded into VRAM at a base that is not the naive `0x80`–`0x110`, and no complete glyph-index→ASCII table was recovered. This is the one soft spot in requirement 3; the numeric values fed to the validator are certain.

## 7. Validation evidence

* **Observed (ROM oracle):** `validate(bytes)` returns `1` for `05 11 14 12 10 1A` and `01 1C 2A 1D 29 19`; `0` for all six rejection vectors above. Called via mGBA `-d`: `cpsr=0x3f` (Thumb, IRQ off), `r0`=buffer, `r14`=sentinel, trace until return.
* **Observed (RAM diff, `rameffect.py`):** before `0x03002780: 00×16`, `0x0300278B: 00×8`, `0x03002790: 00×4`; after the accepted call: `0x03002780: FF 01 FE 01 00 00 FC 03`, `0x0300278B: 00 01 00 01 01 04 04 00`, `0x03002790: 04 04 00 00`. These are exactly the fields/level mask predicted by the model for the minted code — a byte-level accept effect.
* **Derived (disassembly):** validator, bit reader, checksum, gate, ranges, field offsets, call site, tables.
* **Observed (emulator, retained screenshots):** MODE 7 intro → title → main menu → OPTIONS → CAREER → STAGE SELECT → six-slot PASSWORD panel (`BBBBBB`); GUI object register `r8=0x03004A50` in the panel input path (note: the 4.6 KB panel object is more plausibly EWRAM; the slot offsets relative to the object are what matter and are proven by the call site).
* **Inferred:** that `BONUS GAME START` / `NEW LEVEL UNLOCKED` strings belong to the post-accept reward path.
* **Harness note:** mGBA `-g` port 2345 was held by an unrelated process, so the §16.19 call was done through `-d` (`w/r`, `trace`) instead; `-d` software breakpoints at `0x080051CC` did not produce stop reports, so the on-screen result string could not be driven from the debugger.

## 8. Unknowns

1. On-screen `PASSWORD OK` capture for the minted code was not obtained (harness limitation above). Acceptance is proven by the ROM function's return value and RAM diff instead.
2. Full glyph-index→visible-symbol transcription (§6b.5).
3. Field semantics names (which decoded 2-bit value is which character stat) — values and addresses are exact; labels are not.
4. Exact base address of the large GUI object in EWRAM/IWRAM at the moment of submit (offsets are exact; base is not needed for the validator).

## 9. Tooling

`arm-none-eabi-objdump -M force-thumb` (raw binary, `--adjust-vma=0x08000000`), Capstone 5.0.7, Python 3.13, REA/Ghidra 12.1.4 (raw ARM import, full auto-analysis; note: its raw import did not lift the Thumb functions in this region, so the validator was recovered by manual Thumb disassembly and cross-checked against REA's load-image/symbol inventory), mGBA SDL `-3 -d -t`, `Xvfb :317`, `openbox`, `xdotool`, `scrot`, ImageMagick, zlib savestate decoder. Analysis scripts in `/tmp/opencode/rocketzero2/`.

## 10. Cleanup

All processes started for this engagement were terminated by PID (mGBA, Xvfb, openbox); only this session's PIDs were used, never `pkill`. Generated `.sav`/`.ss*` artifacts were removed from the ROM folder. `roms/INDEX.md` was not edited. No ROM bytes or copyrighted assets are reproduced here — only hashes, addresses, algorithms and our own generated code.
