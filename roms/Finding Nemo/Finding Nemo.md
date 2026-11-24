# Finding Nemo (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Queue position 302. Analysed independently of the sibling *Finding Nemo: The
Continuing Adventures* image (position 303). This revision of the report closes
the §0.2 gap in the earlier pass: a **novel unpublished accepted password,
`2H52`, was minted from a black-box oracle sweep, typed on the real Password
screen, and RAM-verified** (level 8 / Jellyfish Forest).

## 1. Target identity

| Field | Value |
|---|---|
| File | `Finding Nemo.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `FINDING NEMO` |
| Game code | `AZIE` |
| Maker | `78` |
| Version | 0 (`Rev.00`) |
| MD5 | `69dfdf6e64dc05b2fbb3b9bd42bc93c9` |
| SHA-1 | `7e66699a3ca7caff6acf8fc667b752bcb44236a3` |
| SHA-256 | `c25701ac99344679ec5b1096dd19cc522640606c239dcb62b52f4456811ed2f9` |

`file` identifies a GBA ROM. Entry word `0xEA00002E` = stock `b 0x080000C0`,
not a cracktro patch. Fixed `0xB2=0x96`. Nintendo-logo scan finds exactly one
header (file offset `0x4`); no second image, trainer or boot selector.

## 2. Executive summary

The title-menu **Password** screen accepts four symbols from a 32-symbol
vowel-free alphabet (`BCDFGHJKLMNPQRSTVWXYZ0123456789?`) on an 8×4 keyboard:
32^4 = **1,048,576** representable strings. Each press stores a symbol *index*
(0–31) as one byte; four bytes are packed into one word and submitted through
the game's asynchronous message dispatcher.

There is **no plaintext code table**: none of the known codes appears in the
8 MiB image as ASCII, `+0x20`, 5-bit-packed, byte-per-index, byte-per-index with
a single additive/XOR key, or as a 20-bit word. The system is algorithmic.

The 4th symbol is a deterministic function of the first three: **14 complete
32-value sweeps** of `i3` over unpublished prefixes found **zero or one**
accepted completion per prefix. Crucially, most prefixes have *no* valid
completion, proving a semantic/range layer in addition to the symbol relation.

**Novel code (§6b):** prefix `(23,5,26)` yields exactly one completion,
`i3=23`, i.e. **`2H52`**. It is absent from 3rd party cheat indexes
(3rd party cheat indexes do list a *different*, also-accepted code `2?52` with `i1=31`, so
`2H52` is not a transcription of it). It was typed on the real keyboard,
accepted, and reached **Select Level → Jellyfish Forest**; RAM shows level 8
(`0x02002F60 = 0x08`, `0x02003414 = 0x08`). Screenshot: `novel2c.png`.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 SDL under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`,
  `mgba -3 -d <rom>` (CLI pty debugger, bridged to TCP 45678 by `dbg_fast.py`).
* Keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
  **Hold keys ~150 ms** — shorter taps are silently missed by this game's menu
  and keyboard handlers (guide §16.2).
* Boot: Start at title → **New Game / Password** menu. Cursor starts on
  *New Game*; Down then A enters Password.
* Password screen: move the 8×4 grid, A selects a symbol, B is Back. After the
  4th symbol the async validator runs: reject returns to the keyboard with the
  display reset to `Password: ____`; accept transitions to a success message
  and then **Select Level**.
* Oracle harness (test only, not a submitted cheat): a Thumb breakpoint at
  `0x0801564A` (the four-byte packing site). Set entry count to 3 at
  `0x02006200`, press one key to reach the breakpoint, overwrite
  `0x020061FC..FF` with the four candidate indices, resume, and read
  `0x02006D54` to detect accept (`Password:` absent) or reject. A debugger
  savestate at the clean keyboard made accept-recovery cheap.
* All 19 published codes plus the novel code were confirmed through this path;
  `2H52` was additionally typed manually, symbol by symbol, on the real
  keyboard (`typecode.py`).

## 4. Address map

File offset = ROM address − `0x08000000`.

| Address (ROM) | Purpose |
|---|---|
| `0x08000000` | Stock ARM entry `0xEA00002E` → `0x080000C0` |
| `0x0802FD20`–`0x0802FEA8` | String-descriptor table (UI labels) |
| `0x0802FD7C` / `0x0802FE18` | `Password` / `Password: ____` |
| `0x08015600`–`0x0801573C` | Password-screen input handler (Thumb) |
| `0x0801564A`–`0x08015668` | Loads four symbol bytes, packs one byte each |
| `0x0801566C`–`0x08015676` | Builds msg `{0x08026F20,0x08035B64,packed}`, BL dispatcher |
| `0x08014998` | Message-dispatch wrapper (queues the struct) |
| `0x080147C0` | Iterates handler list rooted at `0x02003460` |
| `0x08012CE4` / `0x0800F0FC` | Keyboard index lookup / glyph conversion |
| `0x0859EA15` | Font table base (identity for 0x30–0x5A) |
| `0x07BFFEA` | `Shin'en Multimedia. Code: B.Wodok` — audio banner, not a password |

RAM (mGBA debugger reads):

| Address | Purpose |
|---|---|
| `0x0200614C`–`0x0200614F` | Four accepted/entered symbol indices (echo) |
| `0x020061FC`–`0x020061FF` | Four typed symbol indices, one byte each |
| `0x02006200` | Entry count (0–4) |
| `0x02006D54`–`0x02006D62` | `Password: xxxx` display string |
| `0x02002F60` | **Selected/starting level** (u32: 1 for `1H51`, 8 for `2H52`, 12 for `M6HM`) |
| `0x02002F64`–`0x02002F65` | **Gallery unlock bitmask** (12 bits; `M6HM` → `0x0FFF`, all 12) |
| `0x02002F58` | Level-progress field (1 → 7 → 11 as level rises) |
| `0x02003404` / `0x0200340C` / `0x02003414` | Level counters; `0x02003414` mirrors `0x02002F60` |
| `0x020039D8` | Unlock-mode field (1 for `1H51`, 2 for `2H52`) |
| `0x04000130` | KEYINPUT (active-low) |

## 5. Algorithm

Reconstructed input path (precise enough to reimplement the front end):

```
alphabet = "BCDFGHJKLMNPQRSTVWXYZ0123456789?"   # 8x4 grid, index = row*8+col
on A press:
    idx = cursor_symbol_index
    entry[count] = idx                  # entry at 0x020061FC, count at 0x02006200
    display[count] = alphabet[idx]       # 0x02006D5E + count
    count += 1
    if count == 4:
        packed = b0 | b1<<8 | b2<<16 | b3<<24
        msg = {0x08026F20, 0x08035B64, packed}
        dispatch(msg)                    # BL 0x08014998 -> 0x080147C0
        on reject: count=0, display="Password: ____", stay on keyboard
        on accept: success message -> Select Level
```

The accept predicate has two layers (guide §16.5):

1. **Symbol relation.** For each swept prefix `(i0,i1,i2)`, sweeping `i3`
   over 0..31 produced at most one accept. So `i3 = f(i0,i1,i2)` where defined.
2. **Semantic/range gate.** 12 of the 14 swept unpublished prefixes had **no**
   valid `i3` at all. The gate constrains the decoded state (level, gallery,
   mode fields in §4). A checksum-valid-looking string can still be rejected.

No simple closed form for `f` was found: exhaustive fits for affine forms
`a·i0+b·i1+c·i2+K (mod m)` (m=2..128), GF(2)-affine bit functions under four
packing orders, constant-residue `w mod m` for all 24 digit-weight permutations
(m<2000), and XOR-linear forms all failed on the 20 known accepted codes.
A *local* rule holds for the `i2=26` level family:
`i3 = (i0+i1+i2+1) mod 32` fits `(22,5,26)→22`, `(23,4,26)→22` and the novel
`(23,5,26)→23`, but it does not generalise to the other published families.
The async script-side validator was not isolated statically; the mapping is
therefore reported as a **black-box oracle table** (§6.3), which is sufficient
to mint and confirm novel codes.

## 6. Tables

### 6.1 Input alphabet (screen order, 8 columns × 4 rows)

| | col0 | col1 | col2 | col3 | col4 | col5 | col6 | col7 |
|---|---|---|---|---|---|---|---|---|
| row0 | B | C | D | F | G | H | J | K |
| row1 | L | M | N | P | Q | R | S | T |
| row2 | V | W | X | Y | Z | 0 | 1 | 2 |
| row3 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | ? |

Vowels absent; the `1` glyph renders as a bare vertical bar and is frequently
transcribed `I` in published lists (normalised before testing).

### 6.2 Accepted published codes (all verified in-emulator)

`1H51`, `2G51`, `BGN1`, `MHP1`, `L2P1`, `4XP1`, `3N6J`, `MP3K`, `L67K`,
`45ZK`, `3NGH`, `4PHC`, `HZ51`, `ZZ51`, `8061`, `M6HM`, `H0C0`, `R00M`,
`?RP0`, plus the distinct 3rd party cheat index code `2?52` (accepted; `i1=31`).

### 6.3 Black-box oracle: full 32-value `i3` sweeps (14 prefixes, 448 probes)

| Prefix `(i0,i1,i2)` | Accepted `i3` | Result |
|---|---|---|
| (22,5,26) | 22 | `1H51` (published, level 1) |
| **(23,5,26)** | **23** | **`2H52` (NOVEL, level 8)** |
| (22,6,26) | none | range-gated |
| (22,5,27) | none | range-gated |
| (24,5,26) | none | range-gated |
| (25,5,26) | none | range-gated |
| (22,5,25) | none | range-gated |
| (0,0,0) | none | range-gated |
| (10,27,5) | none | range-gated |
| (9,27,6) | none | range-gated |
| (9,11,25) | none | range-gated |
| (8,27,27) | none | range-gated |
| (25,26,19) | none | range-gated |
| (24,10,5) | none | range-gated |

Each row is an exhaustive test of all 32 final symbols on the live screen.

### 6.4 RAM effects of the codes

| Code | Level (`0x02002F60`) | progress (`0x02002F58`) | mode (`0x020039D8`) | gallery mask (`0x02002F64`) |
|---|---|---|---|---|
| `1H51` | 1 | 0 | 1 | 0 |
| `2H52` (novel) | **8** | 7 | 2 | 0 |
| `M6HM` | 12 | 11 | — | `0x0FFF` (all 12) |

`2H52` therefore exercises a *different* payload/mode combination from the
published level-8 code `MP3K` (which also starts level 8 but with `i3=7`);
its `i3=23` symbol is not used by any published level code.

### 6.5 Rejected inputs (on-screen failure verified)

| Input | Reason | Screenshot |
|---|---|---|
| `1H5B` (22,5,26,0) | wrong checksum/gate completion | `rej_1H5Bc.png` |
| `1J51` (22,6,26,22) | out-of-range `i1`; sweep (22,6,26) has no completion | `rej_1J51c.png` |
| `1H41` (22,5,25,22) | out-of-range `i2`; sweep (22,5,25) has no completion | `rej_1H41c.png` |
| `BBBB` (0,0,0,0) | non-table combination / range-gated prefix | `rej_BBBBc.png` |
| `ZZZZ` (20,20,20,20) | non-table combination | `rej_ZZZZc.png` |
| `????` (31,31,31,31) | non-table combination | `rej_qqqqc.png` |

Every rejection returns to the keyboard with the display reset to
`Password: ____` — unambiguous on-screen failure (sample: `rej_1H5Bc.png`).

## 6b. Enumeration

* **Input space:** 32^4 = **1,048,576** strings.
* **Checksum dimension:** the 4th symbol is a function of the first three, so
  the nominal space is 32^3 = **32,768** prefixes, each with at most one valid
  completion.
* **Semantic layer:** the gate is much stricter than a simple range on one
  field. Of 14 exhaustively swept unpublished prefixes, only one produced an
  accepted code; the other 13 were rejected for every one of the 32 final
  symbols. The layer bounds observed are: level ∈ 1..12 (`0x02002F60`),
  gallery mask ∈ 0..`0x0FFF` (12 pictures), and constrained `i1`/`i2`
  combinations. Exact arithmetisation of the gate was not recovered.
* **Accepted-set count:** nominal 32,768 checksum candidates; the semantic
  gate removes the large majority. **At least 21 codes are confirmed accepted**
  (20 published + the novel `2H52`). An exact closed-form count of the gated
  set was not reachable through the UI oracle (32 probes per prefix); this is
  an explicit bound, not a claim of completeness.
* **Novel code:** **`2H52`** = indices `(23,5,26,23)`, minted from the
  `(23,5,26)` sweep. It is on no published list (and is distinct from the
  accepted 3rd party cheat indexes string `2?52`). Typed on the real screen it reaches
  **Jellyfish Forest** with level 8 in RAM; screenshot `novel2c.png`, RAM dumps
  `ram_2h52.json` (vs `ram_1h51.json`, `ram_m6hm.json`).
* **Bounds proven by rejection:** six distinct rejected inputs (§6.5), plus
  13 prefixes with zero valid completions across all 32 `i3` values.

## 7. Validation evidence

* **Observed:** screenshots of the title, menus, password keyboard, all six
  rejections, the novel code being typed (`Password: 2H52`), the resulting
  Select Level (`Jellyfish Forest`, `Password: 2H52`), and the Gallery. RAM
  reads of `0x020061FC..FF`, `0x0200614C`, `0x02006D54`, and the level/gallery
  flags in §4.
* **Derived:** byte packing at `0x0801564A`–`0x08015668`; deterministic `i3`
  from the 14 full sweeps; absence of a plaintext/simple-XOR table from
  exhaustive literal searches; two-layer accept predicate.
* **Inferred:** that the async script validator computes a nonlinear, biased
  symbol relation and a state-range gate. The local `(sum+1) mod 32` rule fits
  three samples only and is reported as such, not as the general law.
* **Prompt-injection hygiene:** fetched cheat pages were treated as data; no
  instruction found in a page or ROM string was executed. The `Code: B.Wodok`
  string is an audio-engine credit banner.

## 8. Unknowns

* Exact closed form of the symbol relation `f(i0,i1,i2)` and of the semantic
  gate; the async script validator was not isolated statically. The black-box
  oracle table (§6.3) is the operative characterisation.
* Exact cardinality of the gated accepted set (lower bound 21 confirmed).
* `?KT2` (alternate "unlock all" listing) was not retested this pass; the
  distinct code `2?52` was confirmed accepted.
* The gallery screen renders all twelve thumbnails after both `1H51` and
  `2H52`; the per-picture *unlock* bits were located (`0x02002F64`) but only
  the all-set value (`0x0FFF` after `M6HM`) was exercised.

## 9. Tooling

`file`, hashes, `xxd`, `strings -t x`, Python 3.13, Capstone 5.0.7,
`arm-none-eabi-objdump -M force-thumb`, mGBA 0.10.5 `-d` pty debugger,
Xvfb `:315`, openbox, xdotool (150 ms holds), scrot, ImageMagick.
Scripts in `/tmp/nemo1b/`: `dbg_fast.py` (debugger bridge),
`oracle3.py`/`run_sweep.py` (oracle + 32-value sweeps), `typecode.py` (real
keyboard entry), `rejects.py`, `dumpall.py`, `fitanalysis.py`/`fitorders.py`.
Screenshots and RAM dumps in the same folder.

## Legal note

No ROM bytes or copyrighted assets are reproduced here. Only hashes, addresses,
algorithmic descriptions, the oracle table and the code literals are published.
