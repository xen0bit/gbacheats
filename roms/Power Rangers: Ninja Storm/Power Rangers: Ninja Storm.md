# Power Rangers: Ninja Storm (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Power Rangers: Ninja Storm.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `PRNINJASTORM` |
| Game code | `BPWE` (USA; EU is `BPWP`) |
| Maker | `78` (THQ) |
| Version | 0x00 (Rev.00) |
| MD5 | `9043207a81a937a5e56bc96250545150` |
| SHA-1 | `18acbd5ee48b143d913338d1ad0d2f0bbf318601` |
| SHA-256 | `1d3c534e8e666e178f8901f38e28f21944408bed729432702d6e9912342c4969` |

Phase 0 notes:
- Entry word at 0x00 is the stock `0xEA00002E` → branch to `0x080000C0`; crt0 at 0xC0 is stock (sets SVC/IRQ/system stacks 0x03007E00 / 0x03007FA0 / 0x03007F00, copies the ROM header to 0x03000000).
- Only **one** Nintendo-logo hit, at file offset 0x00 → no embedded/multiboot headers, no appended trainer; tail from 0x3FFBB5 is 0xFF pad.
- However the **main pointer in the literal pool at 0x100 was patched to `0x083F7CD4`**, a scene cracktro ("WINNERS USE INTROS", "TOP 5 FIGHTERS", FBI warning) that runs first, self-decompresses into EWRAM and then returns into the stock game. Disassembly at `0x083F7CD4` (ARM) shows a push + LZ-style decompressor loop writing to `0x02000000`. This is a release intro, **not** an in-game cheat; it was left in place for analysis because the entry branch and all game code are untouched. Observed in mGBA before the Buena Vista logo.
- Header checksum 0x0000 / complement byte 0x0D is as shipped (no evidence of a cheat patch).

## 2. Executive summary

The game has a **developer password system** (no GameShark/CodeBreaker content was analyzed). Passwords are exactly **three characters** drawn from a 32-symbol, vowel-free alphabet `BCDFGHJKLMNPQRSTVWXYZ0123456789!` (5 bits/symbol, 15 bits/code). The system is **algorithmic**, not a lookup table: no copy of any valid code, nor any 45-entry table, exists in the ROM in ASCII, 5-bit-index, or packed form.

The code encodes three fields — team (Wind/Thunder/Green), level (1–5) and difficulty (Easy/Normal/Hard) — plus four scattered checksum bits, with four unused high bits forced to zero. The complete space is 45 valid codes (3 × 5 × 3); the structural space is 2^11 = 2048 forms of which 45 are accepted.

I recovered the exact bit layout and checksum equations (§5), reproduced **35 of 37** published 3rd party cheat index codes from it, showed the remaining two are published typos, and **generated five codes that appear in no published list** — all five were accepted on the real password screen (§6b). Six out-of-range/bad-checksum codes were rejected on the same screen (§6b). The in-game pause screen regenerates and displays the canonical code from its state (RAM proof at `0x030035B3`).

Scope check: all reachable screens were walked with screenshots (title, main menu, password entry, team select, character select, pause, options, gameplay, attract/demo). No hidden debug menu: no `DEBUG` / `LEVEL SELECT` / `TEST MODE` / `SECRET` / `CHEAT` / `WARP` string exists in the image in ASCII, case variants, or ±0x20 shifted form, and the combos tried (L+R+Start, etc.) only produce the normal attract/demo. All six rangers are selectable from the start; there is no unlockable to brute force.

## 3. How to reproduce

- Emulator: mGBA (SDL), `SDL_AUDIODRIVER=dummy`, Xvfb `:316`, `mgba -3 <rom>`. Default keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows. Hold each key ~150 ms with ~200 ms gaps; faster taps are dropped (guide §16.2).
- Path: title → `START` → main menu (`NEW GAME` / `PASSWORD` / `OPTION`) → `PASSWORD`.
- Keyboard (visually confirmed on the password screen):

  ```
  B C D F G H J K L M N
  P Q R S T V W X Y Z
  0 1 2 3 4 5 6 7 8 9 !
          CANCEL       OK
  ```

- Entry: from CANCEL press Up ×4 to reach `B`, move with the D-pad, press A to commit each symbol; after the third symbol the cursor auto-jumps to `OK`, press A again. A valid code shows a team/character selection screen; an invalid code returns to the password keyboard (no error text).
- Known-good anchors: `GG5` (Wind/Normal/L1), `BHV` (Wind/Hard/L1), `GGS` (Thunder/Normal/L1), `GJN` (Green/Normal/L1).
- Novel codes tested: see §6b.
- Savestates: mGBA `.ss1` files are PNG with a zlib `gbAs` chunk; `zlib.decompress` yields a 397,312-byte state (for this 4 MiB ROM). Region offsets used below: CPU/header `0x00000`, VRAM `0x01000`, IWRAM `0x19000`, EWRAM `0x21000` — IWRAM address = `0x03000000 + (state_offset - 0x19000)` (guide §16.13).

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Crt0 / `main` pointer (patched to cracktro) | `0x080000C0` / literal at `0x08000100` = `0x083F7CD4` | Derived (ARM disassembly) |
| Cracktro decompressor | `0x083F7CD4` | Derived |
| Password display buffer (3 bytes, indices 0–31) | IWRAM `0x030035B3`–`0x030035B5` | Observed (savestate diff, both `GG5`=[4,4,26] and `BKB`=[0,7,0]) |
| Code-table region | IWRAM `0x030035A4` (struct base, password at +0xF) | Observed |
| Font attribute table (low byte = ASCII, high byte = attribute) | `0x08318D50` onward | Derived (bytes) |
| ASCII credits roll (the only plaintext in the image) | `0x0326A7C`–`0x03271F4` | Observed |
| State bytes that change between Wind/Normal and Green/Hard | IWRAM `0x030035BC`, `0x0300266E`, `0x03002686`, `0x03007B3x` | Observed (diff) |

No hard-coded password table exists in ROM (searched ASCII, 3× 5-bit-index bytes, and packed 15-bit words for all 45 codes and for consecutive runs — all negative).

## 5. Algorithm

Alphabet (index 0–31): `B C D F G H J K L M N P Q R S T V W X Y Z 0 1 2 3 4 5 6 7 8 9 !`

Let the state be `t ∈ {0,1,2}` (0 = Wind, 1 = Thunder, 2 = Green), `l ∈ {1..5}`, `d ∈ {0,1,2}` (0 = Easy, 1 = Normal, 2 = Hard). Define:

```
L = l - 1;  L0=L&1, L1=(L>>1)&1, L2=(L>>2)&1
T0=t&1,     T1=(t>>1)&1
D0=d&1,     D1=(d>>1)&1

chk7  = L0 ^ L2 ^ 1
chk12 = L1 ^ D1 ^ 1
chk4  = (t==0) ^ (D1 & L1)
chk1  = D0 | (D1 & L1 & (t!=0))

c0 = (L1 << 3) | (chk12 << 2)                 # bits 4,1 of c0 unused (=0)
c1 = (L2 << 3) | (chk7 << 2) | (T1 << 1) | D1  # bit 4 of c1 unused (=0)
c2 = (chk4 << 4) | (D0 << 3) | (T0 << 2) | (chk1 << 1) | L0

password = alphabet[c0] + alphabet[c1] + alphabet[c2]
```

Bit layout of the 15-bit word `(c0<<10)|(c1<<5)|c2` (bit 14 = MSB):

| Bit(s) | Meaning |
|---|---|
| 0 | level−1 bit 0 (`L0`) |
| 13 | level−1 bit 1 (`L1`) |
| 8 | level−1 bit 2 (`L2`) |
| 2, 6 | team bits T0, T1 (2 = Thunder, 6 = Green) |
| 3, 5 | difficulty bits D0, D1 (3 = Normal, 5 = Hard) |
| 7, 12 | checksum bits: `L0^L2^1`, `L1^D1^1` |
| 1, 4 | nonlinear checksum bits (AND/OR of team, level, difficulty as above) |
| 9, 10, 11, 14 | always zero (unused) |

Derivation evidence: bit-0 is 1 exactly for even levels, bit-13 exactly for levels 3–4, bit-8 exactly for level 5, bit-2 exactly for Thunder, bit-6 exactly for Green, bit-3 exactly for Normal, bit-5 exactly for Hard (across all 37 consistent published codes). The two linear checksum bits were solved by GF(2) elimination with zero mismatches; the two nonlinear bits were fitted from the state/carry table. The model then reproduced 35/37 published codes exactly.

Decoder (inverse): read the 7 data bits above to recover `l, t, d`; verify `chk7, chk12, chk4, chk1` and the four zero bits. A code is accepted iff all checks pass.

## 6. Tables

Complete valid space (all 45 codes), generated by the model. Bold = **not present in any published list** (3rd party cheat indexes checked).

| Difficulty | Team | L1 | L2 | L3 | L4 | L5 |
|---|---|---|---|---|---|---|
| Easy | Wind | GGV | GBW | **LGV** | LBW | GLV |
| Easy | Thunder | **GGG** | GBH | **LGG** | LBH | **GLG** |
| Easy | Green | **GJB** | GDC | LJB | LDC | GNB |
| Normal | Wind | GG5 | GB6 | LG5 | LB6 | GL5 |
| Normal | Thunder | GGS | GBT | LGS | LBT | GLS |
| Normal | Green | GJN | GDP | LJN | LDP | GNN |
| Hard | Wind | BHV | BCW | QHB | QCC | BMV |
| Hard | Thunder | **BHG** | BCH | QH1 | QC2 | BMG |
| Hard | Green | **BKB** | BFC | QKX | QFY | BPB |

Published-code verification (3rd party cheat index cheats page, 7 lists; 3rd party cheat index walkthrough 49223; 3rd party cheat indexes; 3rd party cheat index cheat list):
- 35 of 37 passwords reproduced exactly by the model.
- `IGW` (Wind/Easy/L3) → correct code **`LGV`**; accepted on screen.
- `GLW` (Thunder/Easy/L5) → correct code **`GLG`**; accepted on screen.
- The 3 CodeBreaker codes on 3rd party cheat indexes (`330026AF 00C0`, `3300268C 00C8`, `3300005D 0009`) are GameShark-style memory patches, explicitly out of scope; they were not used or verified.
- `GGS` is published as both Thunder/Normal/L1 and Thunder/Hard/L1; the model gives `BHG` for Thunder/Hard/L1, which the game accepts.

## 6b. Enumeration

**Space size.** Alphabet 32 symbols, length 3 → 32^3 = 32,768 spellings. Four bit positions are structurally zero (bits 9,10,11,14) → 2^11 = 2,048 possible forms; checksum equations reduce this to exactly **45 accepted codes** = 3 teams × 5 levels × 3 difficulties. There are no aliases: all 45 generated codes are distinct.

**Novel codes (absent from every published list) generated and confirmed in-game:**

| Code | Intended state | Emulator result |
|---|---|---|
| `BKB` | Green, Hard, L1 | Accepted → single Green Ranger selection; game starts as Green at Lv.1; pause regenerates `BKB` (RAM `[0,7,0]` at `0x030035B3`) |
| `BHG` | Thunder, Hard, L1 | Accepted → Thunder Rangers selection (two-ranger panel) |
| `GGG` | Thunder, Easy, L1 | Accepted → Thunder Rangers selection |
| `LGV` | Wind, Easy, L3 | Accepted → Wind Rangers selection (corrects published `IGW`) |
| `GLG` | Thunder, Easy, L5 | Accepted → Thunder Rangers selection (corrects published `GLW`) |

Screenshots for each were in `/tmp/prninjastorm/r_<CODE>.png` (contact sheet `sheet2.png`). Note: screenshots are local analysis artifacts and are not attached to this report.

**RAM verification of effect.** Two pause states were diffed: `GG5` (Wind/Normal/L1) vs `BKB` (Green/Hard/L1). At IWRAM `0x030035B3..B5` the bytes change `[4,4,26]` → `[0,7,0]`, i.e. exactly the indices of the two codes; companion state bytes at `0x030035BC`, `0x0300266E`, `0x03002686`, `0x03007B3x` also change, consistent with a different team/difficulty/character. This proves the game itself regenerates the canonical password from its internal state rather than echoing the typed string.

**Bounds proven by rejection.** All submitted on the same password screen, each returned to the keyboard (no character select):

| Rejected | Reason |
|---|---|
| `BBB` | structurally invalid (zero data fields + bad checks) |
| `BKC` | `BKB` with c2 low bit flipped — level-parity/checksum violation |
| `BLB` | `BKB` with c1 incremented — team/difficulty field corruption |
| `GG6` | `GG5` with c2 incremented — checksum violation |
| `GH5` | `GG5` with c1 incremented — checksum violation |
| `CKB` | `BKB` with c0 incremented — checksum violation |

Together these bound the accepted set to the model's 45-code space: a one-bit change to any of the three digits is rejected.

## 7. Validation evidence

- **Observed** (emulator/screenshots): title, main menu, password keyboard & alphabet, all three team-select options, character select, pause screen showing the live password, options screen, gameplay, attract/demo. Five novel codes accepted; six invalid codes rejected; keyboard navigation and the auto-jump to OK.
- **Observed** (RAM/savestates): password buffer `0x030035B3` holds `[4,4,26]` for GG5 and `[0,7,0]` for BKB; state-byte diffs listed in §4.
- **Derived** (bytes/disassembly): stock entry and patched `main` pointer; cracktro at `0x083F7CD4`; font attribute table; absence of any literal code table; bit-field/chacksum model (GF(2) solution + state-table fit).
- **Inferred**: exact machine-code address of the password generator/validator was **not isolated** — the static search for a literal reference to the buffer found no clean xref, and the mGBA `-g`/`-d` debug stubs proved unreliable in this headless environment (single-client stub / FIFO EOF). The model is nonetheless validated behaviourally by 11 in-game tests and by exact reproduction of 35 published codes. Field *names* (team/level/difficulty) are confirmed by the on-screen team/character panels and the HUD `Lv. 1` label.
- No prompt-injection content was encountered in fetched pages or ROM text; all fetched material was treated as data.

## 8. Unknowns

- Exact ROM address and disassembly of the generator/validator function (behaviour fully modelled instead).
- Whether the two nonlinear checksum bits arise from a carry-chain of an arithmetic checksum or an explicit AND/OR formula; the fitted equations in §5 reproduce every observed code.
- The two ON/OFF settings on the OPTION screen were not individually labelled by OCR (panel is partially clipped); they are unrelated to the password system.
- The cracktro's return-to-game jump target was not followed past its self-decompressor; it returns into the stock game as observed.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep` for Phase 0/1.
- Python 3 standard library for header parse, logo scan, savestate `gbAs` zlib extraction, bit-field analysis, GF(2) solve, and code generation (`analyze.py`, `bits.py`, `field.py`, `solve.py`, `tab.py`, `model.py`, `enter2.py`, `ss.py`, all in `/tmp/prninjastorm`).
- `arm-none-eabi-objdump` for crt0 / cracktro disassembly.
- mGBA (SDL) under Xvfb `:316` with `openbox`, `xdotool`, `scrot`, ImageMagick for Phase 2/5/6.
- Web sources: 3rd party cheat index cheats & walkthrough 49223, 3rd party cheat indexes.
- No copyrighted assets are redistributed; only addresses, hashes, equations, and generated codes are published.
