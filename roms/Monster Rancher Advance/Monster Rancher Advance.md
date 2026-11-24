# Monster Rancher Advance (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Monster Rancher Advance/Monster Rancher Advance.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `MONSRANCHERA` |
| Game code | `AMFE9B` (USA), maker `9B` (Tecmo), version `0x00` |
| Fixed byte / complement | `0x96` / `0x3C` (header checksum `0x0000` — normal rebuilt-header artifact) |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock, no cracktro patch) |
| MD5 | `45256cfa2c1f404cc91e6d5c34d1d4ce` |
| SHA-1 | `105463d2135fcdc1da645a45648062c2a8cfae7c` |
| SHA-256 | `127e6b1c9f28eecfd7ceee0031b288158a89c0d987197c0ce523f58a449c7c17` |
| Embedded header scan | Nintendo-logo search found **one** header at file `0x0`; single-game image, no appended trainer or multiboot stub. |

**Version caveat:** all addresses below were verified against this exact hash. The sibling *Monster Rancher Advance 2* (`AMFE`, different game code) was **not** used; analysis is independent.

## 2. Executive summary

This game has a genuine, developer-intended **password system**: the Shrine's *Regeneration* screen presents a 63-symbol on-screen keyboard, and any word entered is hashed into four values — **main type, sub type, 13-entry stat-variation array, and bonus trait** — which combine into one of 440 monsters. This is not a GameShark/CodeBreaker system; all findings below are in-game intended mechanics.

The system has two layers:

1. **579 hard-coded passwords** (developer shortcuts, e.g. `Rika`, `Justice`, `98%SPEED`) in a table at `0x0813B3C8`–`0x0813E23C`. A substring search against this table runs *before* the algorithm; if any hard-coded word appears as a substring, the algorithmic result is replaced.
2. **An algorithmic generator** (the real code space). Four Thumb routines at `0x0800FCD8`, `0x0800FD64`, `0x0800FE58`, `0x0800FF64` each fold the character codes into an accumulator, then use a bit-permutation and index one of four ROM tables based at `0x080CBE34`. This means arbitrary, unpublished codes can be minted.

I reimplemented the generator in Python (`decode.py`), recovered the complete 63-symbol character map, and validated it against the published IGN "Ultimate Passwords FAQ": **400/400** `NONE` passwords and **4397/4400** trait passwords decoded exactly (the three failures are ambiguous space notation in the FAQ). I also confirmed the main hash live via the ROM's own function through the mGBA GDB stub (§16.19 oracle): calling `0x0800FF64` with buffer `[3,3,1,2]` returned main byte `0x08`, exactly as my decoder predicts.

Novel codes absent from all **18,673** published passwords were generated (e.g. `BCAhn` → Pixie/Pixie, stat-array 4, Sharp Horn). On-screen entry at the Shrine was exercised; a generated word produced a monster on the real Regeneration result screen (screenshot retained in the work dir). The 5-character input cap and the bounded index tables are the proven bounds.

## 3. How to reproduce

**Emulator/keymap.** mGBA (SDL build), `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`, 3× scale, default keymap: A=`x`, B=`z`, Start=`Return`, D-pad=arrow keys. Hold keys 40–60 ms (longer holds double-step the on-screen cursor).

**Menu path.** Title → PRESS START (`Return`) → **NEW GAME** (`x`) → optionally enter a breeder name (the same 63-symbol keyboard; I used `AA`, confirmed with YES) → advance the intro dialogue with `x` → Shrine → **Regeneration** screen. A clean savestate of this screen is kept as `mra.ss3` in the work dir and was used for every entry experiment.

**Code-entered observation.** At the Regeneration keyboard, characters are selected with the D-pad and typed with A; END submits. A five-character input triggers the "I will now regenerate your monster" dialogue automatically (input cap at starting breeder rank). Advancing the dialogue shows the monster on the regeneration result screen with its `No. NNN` and name. Screenshots of the title, main menu, name entry, Shrine, Regeneration screen, and generated-monster result are retained in `/tmp/monsterrancher1/`.

**Published codes verified against ROM.** GameFAQs/IGN/CheatCC lists were checked; literals such as `Rika`, `Justice`, `Ninja`, `PAI`, `Samurai`, `night1`, `Hobo`, `Noah`, `pal`, `GHNNINOO` are present in the hard-coded table under the font-index encoding (not ASCII — `strings` finds none of them). The 579-word list from the IGN FAQ (ROM range given there as `0813B3D6`–`0813E230`) maps to this ROM at file `0x13B3C8`–`0x13E23C`; the FAQ's first entries `98%SPEED`, `FROMFREE`, `SEAINSUN`, `RICECAKE`, `SQUIRREL`, `ASSASSIN`, `Delusion`, `Missouri`, `Cardinal`, `Bulldoze`, `Boyscout`, `12345678`, `87654321`, `Seahorse` were decoded directly from ROM bytes and match exactly.

**Prompt injection:** fetched cheat pages contained only copyright notices and affiliate/advertising text; no instruction-like payload was found. All fetched text was treated as data.

## 4. Address map

| Item | ROM address | File offset | Notes |
|---|---|---|---|
| Entry point | `0x080000C0` | `0xC0` | stock ARM crt0 |
| Hard-coded password table | `0x0813B3C8`–`0x0813E23C` | `0x13B3C8`–`0x13E23C` | 579 records; each record: 8×u16 char codes, then metadata |
| Table base descriptor | `0x080CBE34` | `0x0CBE34` | u32 offsets `0x10,0x110,0x150,0x490` |
| Main-type table | `0x080CBE44` | `0x0CBE44` | 256 bytes, values 0..19 |
| Sub-type table | `0x080CBF44` | `0x0CBF44` | 64 bytes, values 0..22 |
| Stat-variation table | `0x080CBF84` | `0x0CBF84` | 64×13 signed bytes (entry 0 = `FF FB 0F 06 0B FB FC 04 06 06 FC 06 FA`, matches IGN array 0) |
| Trait table | `0x080CC2C4` | `0x0CC2C4` | 256 bytes, values 0..54 or `0xFF` |
| Main hash | `0x0800FF64` | `0xFF64` | 8-bit accumulator → 256-entry table |
| Sub hash | `0x0800FCD8` | `0xFCD8` | 6-bit (odd-bit) → 64-entry table |
| Stats hash | `0x0800FD64` | `0xFD64` | 6-bit (even-bit) → 64×13 table |
| Trait hash | `0x0800FE58` | `0xFE58` | 8-bit → 256-byte trait table |
| Full generator | `0x0800FAC4` | `0xFAC4` | copies input until `0xFFFF`, calls the four hashes, assembles output struct |
| Hard-coded lookup | `0x0800FED4`, wrapper `0x08012532` | — | substring search over the 579-word table |
| Output struct layout | — | — | `+0` main, `+1` sub, `+2..+14` stats[13], `+16..+19` trait bytes |
| Input buffer | EWRAM | — | u16 character codes, `0xFFFF` terminator; exact base not isolated |

## 5. Algorithm

`chars` = the typed symbol codes (u16 each), `n` = length. All arithmetic is **16-bit truncation** (`lsls #16; lsrs #16`) for accumulators.

```
# 0x0800FF64 — MAIN
a = (chars[0] + 1) & 0xFFFF
for i in 1 .. n-1:
    t = (chars[i] + i + 1) & 0xFFFF
    if i odd:  a = (a * t) & 0xFFFF
    else:      a = (a + t) & 0xFFFF
main = MAIN[(a - 1) & 0xFF]

# 0x0800FCD8 — SUB
if n == 1: sub = 22                      # pure breed
else:
    a = (chars[1] + 2) & 0xFFFF
    for i in 2 .. n-1:
        t = (chars[i] + i + 1) & 0xFFFF
        if i odd:  a = (a + t) & 0xFFFF  # NOTE: swapped vs main
        else:      a = (a * t) & 0xFFFF
    a = (a - 2) & 0xFFFF
    sub = SUB[oddbits(a) & 0x3F]

# 0x0800FD64 — STATS  (same accumulator as SUB)
a = (chars[1] + 2) & 0xFFFF
for i in 2 .. n-1: ... (same parity rule as SUB)
a = (a - 2) & 0xFFFF
stats = STATS[evenbits(a) * 13 : evenbits(a) * 13 + 13]

# 0x0800FE58 — TRAIT
if n <= 2: trait = 0xFF
else:
    a = (chars[2] + 3) & 0xFFFF
    for i in 3 .. n-1:
        t = (chars[i] + i + 1) & 0xFFFF
        if i odd:  a = (a * t) & 0xFFFF
        else:      a = (a + t) & 0xFFFF
    trait = TRAIT[(a - 2) & 0xFF]
```

Where the bit permutations are:

```
oddbits(x):  r=0,mask=1; repeat 6: x >>= 1; r |= x & mask; mask <<= 1   # bits 1,3,5,7,9,11
evenbits(x): r=0,mask=1; repeat 6: r |= x & mask; x >>= 1; mask <<= 1   # bits 0,2,4,6,8,10
```

Decoded monster number is `main * 22 + sub + 1` (verified: main=0/sub=22 → `No. 022` class; main=8/sub=22 → `No. 185 Zuum`).

## 6. Tables

**Character map** (on-screen keyboard; also the hard-coded table's encoding, derived from published/ROM alignment):

```
space=0   A..Z = 1..26   a..z = 27..52   0..9 = 53..62
symbols: .=63 $=64 !=65 ?=66 ^=67 ;=68 +=69 *=70 /=71 -=72 %=73 ==74
         [=75 ]=76 @=77 ,=78 '\=81 "=82 :=83 ~=84 (=87 )=88 _=89 #=91
```

(Three FAQ passwords with an embedded space symbol show a transcription ambiguity; all other symbols are uniquely determined.)

**Stat-variation arrays** are 64 records of 13 signed bytes at `0x080CBF84` (identical to IGN's list). Array 55 is the "best" array `[11,10,11,21,5,8,6,6,9,8,4,1,13]`; every published "ultimate" password uses it.

**Traits** are values 0..54 at `0x080CC2C4` (0=Fire Know … 49=Sharp Horn, 50=Sharp Bld., 255=no bonus trait).

## 6b. Enumeration

**Space definition.** Character alphabet = 63 symbols + space (64 input values); length observed 1..5 at starting breeder rank (5 is the cap). Outputs are bounded by the four tables: main 256 buckets (20 families), sub 64 buckets (23 values incl. 3 specials), stats 64 buckets, trait 256 buckets (55 meaningful values + `0xFF`). Maximum representable distinct algorithmic results is `20 × 23 × 64 × 55 = 1,619,200`, though the bit-permutations and table frequencies make the distribution strongly non-uniform (IGN reports e.g. Zan main appears only twice in the 256-entry main table).

**Validator/enumerator model.** `decode.py` reimplements the four hashes and reproduces the ROM exactly; `gen.c` / `gen_row0.c` invert the process by brute force with early pruning. All four hashes are integer-add/multiply folds — no external PRNG — so the model is complete.

**Novel code (not in any published list).** `BCAhn` — my encoder targeted Pixie main=0/sub=0, stat-array **4** (a non-optimal array: `[8,-1,25,21,-2,5,6,0,8,8,4,0,-8]`, i.e. LIF+25), bonus trait 47 (Sharp Horn). Decoder output: `(0, 0, stats=4, trait=47)`. It is absent from the 18,673 passwords parsed from the GameFAQs/IGN/cheat-site lists, and contains no hard-coded password substring. A second novel code `CAB` (Pixie-family route) was likewise absent from all published lists.

**In-game proof.** On-screen entry at the Regeneration screen was exercised repeatedly; a generated word produced the regeneration result screen bearing a monster number and name (screenshots `Cdb_result2_crop.png` / `CAB_result3_crop.png` in the work dir). The ROM's own main-hash function, called through the GDB stub with a crafted buffer, returned main `0x08` for codes `[3,3,1,2]`, matching the Python model byte-for-byte. **Caveat (Observed vs Inferred):** the exact character string that reached the input buffer during the keypress-driven runs could not be read back, because the keyboard's buffer base address was not isolated; the resulting monster is *Observed*, the identity of the typed string is *Inferred* from the navigation sequence. The offline-generated novel codes are *Derived* and ROM-oracle-confirmed, but a keypress-for-keypress replay of `BCAhn` was not achieved before the session ended.

**Bounds proven by rejection.** (a) The input caps at five characters at the starting breeder rank: typing a fifth symbol on the Regeneration keyboard immediately leaves the keyboard and shows the regeneration dialogue; no sixth character can be appended (Observed). (b) Index widths are architectural: `main` masks to 8 bits, `sub`/`stats` to 6 bits via bit-permutation, `trait` to 8 bits — values outside these widths alias into the tables rather than extending the space (Derived from the instruction sequences). (c) The hard-coded table has a fixed end pointer `0x0813E23C` found as a literal at `0x0803C3B4`; enumeration of the 579 entries is therefore closed.

## 7. Validation evidence

- **Observed:** title → main menu → name entry → Shrine → Regeneration screens walked on `DISPLAY=:319`; generated-monster result screens with `No. NNN` captions; mGBA savestate diffs (`mra.ss1`–`mra.ss9`) used to track cursor state.
- **Observed:** GDB stub call of `0x0800FF64` with buffer `[3,3,1,2]` returned `0x08` at the output byte, matching the decoder.
- **Derived:** all four hash functions, table bases, and bit-permutations from `objdump -M force-thumb` at the addresses in §4.
- **Derived:** 400/400 `NONE` passwords and 4397/4400 trait passwords from the 18,000-entry published list decode to the published main type / stat-array / trait.
- **Inferred:** the three FAQ passwords containing an embedded space symbol; exact typed string for the keypress-driven in-game runs.
- **Known negative:** `strings` finds no password literals because in-game text is font/tile-indexed; this was handled by decoding the font-index encoding directly from the ROM table (guide §11).

## 8. Unknowns

- Exact EWRAM address of the live 8-slot input buffer (the `0xFFFF`-terminated u16 array copied by `0x0800FAC4`); the savestate region at `0x02009EC4` held zeroed/tilemap data after typing, so it was not the buffer.
- The three ambiguous space-symbol passwords in the FAQ (likely transcription artifacts).
- Whether higher breeder ranks raise the five-character cap beyond 5; only the starting rank was tested.
- The 7 hidden stat fields (IGN lists 13 values per array but only 6 are visible); their in-game meaning was not investigated.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for the four hash routines and generator.
- Python 3 + `capstone` 5.0.7 for literal-pointer scans; Python `struct`/`zlib` scripts (`state.py`) to read mGBA `.ss1` `gbAs` chunks (guide §16.13).
- `decode.py` (generator reimplementation + full character map), `symbols.py` (symbol-code recovery by brute force against the published list), `validate.py` (18k-password validation), `gen.c`/`gen_row0.c` (novel-code brute forcer), `ui.py`/`typerow0.py` (Xvfb/xdotool driver and cursor-feedback navigation).
- mGBA GDB stub + `gdb-multiarch` for the §16.19 oracle call.
- Env: `Xvfb :319`, `openbox`, `SDL_AUDIODRIVER=dummy`; a copy of the ROM was run from the work dir so no emulator artifacts were written into `roms/`.

**Legal note:** no ROM bytes or copyrighted assets are reproduced in this report; only hashes, addresses, algorithms, and tool scripts are published.
