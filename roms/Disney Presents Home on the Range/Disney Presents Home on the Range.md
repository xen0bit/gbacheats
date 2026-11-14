# Disney Presents Home on the Range (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney Presents Home on the Range/Disney Presents Home on the Range.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title | `DISNEY HOTR` |
| Game code | `BHME` |
| Maker code | `4Q` |
| Software version | 0 |
| Complement check | `0x87` (valid: header bytes `0xA0..0xBC` recompute to `0x87`) |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| MD5 | `548c9e76f99fdec14c02021a72a011d8` |
| SHA-1 | `64d7da7ed3217c7181e93b14529668c712ca9800` |
| SHA-256 | `5eaf8ee50a45fec32881573a141da64bd3e10d93642f40d28d8bf6194177a90f` |

The 156-byte Nintendo logo occurs exactly once (file `0x4`); this is a single
GBA image, not a multi-game pack.

**This file is not the clean retail image.** It carries an appended/replacing
scene cracktro (see §2 and §7). Any code address in this report belongs to this
patched image.

Audio banner (stock): `GAX Sound Engine 3.05 (Aug 13 2003)` and
`Shin'en Multimedia. Code: B.Wodok` at file `0x18B20C` / `0x18B231`.

## 2. Executive summary

- The ROM is a licensed Disney platformer (Artificial Mind & Movement /
  Disney Interactive, 2004) whose GBA audio is Shin'en's GAX engine.
- **The image is a scene-patched release.** Boot sequence: a Mode-7 /
  "GLENBEY" cracktro ("iL Scn. 2004", greetz, `code+design: SABREC`,
  `logo: ASPHIX`, `graphics: MOONLORD`, `music: WAYNE KERR`,
  `player: CAPITULON`) runs first, then the stock Disney Interactive logo and
  the game. The stock entry word and header are intact; the cracktro is part of
  the patched ROM data, so this is a modified image rather than a clean dump.
  Treat this as a patch/trainer artifact, not game content (§16.1).
- Menus walked on `:309`: title `PRESS START` → main menu
  `NEW GAME / PASSWORD / OPTIONS / CREDITS` → **PASSWORD** screen with four
  letter slots, `B Cancel` / `A Select`, and a centred `INCORRECT` message when
  an entered code is rejected (observed).
- Fourteen 4-letter level passwords are published for this title (GameFAQs,
  ChapterCheats, GameGenie, VGChartz). None of them exists literally in the ROM
  in ASCII, in the menu font encoding (`letter-'A'+0x21`), as a byte
  letter-index, as the observed glyph tile index, or as a packed 5-bit word.
  Reason now known: the codes are four 4-bit nibbles over a custom 16-symbol
  alphabet and pass a seeded bit-permutation + MT19937 checksum (§5), so they
  are generated rather than stored.
- The ROM contains a complete developer debug/stage-select menu as strings and
  a record table (`Jeb Levels`, `Episodes`, `Bosses`, `Buck Rides`,
  `Buck Fighting`, `Obj Viewer`, `Asset Viewer`, `Music Player`, `Fx Player`,
  `Logo Screen`, `Main Menu`, `DayDream`, `Ride to PoH`, plus an
  `R Button: KeyRec Mode: Off/Playback/Record` overlay). No static pointer to
  the table base was found in 8 MiB; its gate was not located.
- **The password validator was recovered** (`0x08003204`, §5). It is not a
  literal-compare: the four symbols are four nibbles packed big-endian by
  position into one 16-bit code, the code selects a 40-step bit permutation
  seeded by just two of its own bits, and the permuted word must satisfy a
  7-bit check computed from a second MT19937 stream seeded by 12 bits of the
  permuted word.
- The accepted set is **closed and fully enumerated: exactly 165 codes**,
  one for each of 15 stage-data blocks × 11 sub-levels (§6b, appendix A).
  All 14 published codes are members; each lands in a different block, which
  is why the published list works.
- On the real password screen: `BBKD` and `DVHB` display `CORRECT`
  (both published); the unpublished `BTBB` also displays `CORRECT` and fades
  into the game's opening cutscene; `BTBC` (one symbol changed) displays
  `INCORRECT`. Captures: `bbkd_post2.png`, `dvhb_post2.png`, `m_after.png`,
  `btc_incorrect.png` in the session work dir.

## 3. How to reproduce

Emulator: `mgba` SDL, `-3`, under `Xvfb :309` + `openbox`,
`SDL_AUDIODRIVER=dummy`.

Keymap used (mGBA SDL defaults): `x`=A, `z`=B, `a`=L, `s`=R,
`Return`=Start, `BackSpace`=Select, arrows = D-pad. `Shift+F1..F9` saves a
state, `F1..F9` loads.

Exact path:

1. Boot; wait through cracktro (~20 s) and Disney Interactive logo.
2. Title: press `Start`.
3. Main menu: `Down` once to `PASSWORD`, `A`.
4. Password screen opens with the four cells on `B B B B`, cursor on the
   **leftmost** cell. `Up`/`Down` step the selected cell through the
   16-symbol alphabet `B C D F H J K L M N P Q R S T V`, wrapping at both
   ends (0→15 on `Down`, 15→0 on `Up`); `Left`/`Right` move the cursor
   between the four cells; `A` submits, `B` cancels.
5. A rejected code displays the `INCORRECT` banner and stays on the screen;
   an accepted code displays `CORRECT`, fades out and loads the stage data
   selected by the code (§5, §7).

**Input caveat (important for reproduction):** this build's menu accepts a
press only if the emulator window holds X focus at the instant of the XTEST
event; with focus drifting (openbox, Xvfb) more than half of sends were
silently lost. Calling `xdotool windowfocus $W` before *every* press and
holding ≥150 ms gave one step per press in a controlled 3-press test
(H→K, exactly +3). Frame-stepping through mGBA's `-d` debugger also works but
delivered key events inconsistently. This is a harness problem, not game
behaviour (§16.2).

## 4. Address map

File offsets; ROM address = `0x08000000 + offset`.

| Offset | What |
|---|---|
| `0x000000` | GBA header, stock entry word, valid complement |
| `0x0018B20C` | GAX Sound Engine 3.05 banner |
| `0x0018C0B0–0x0018C65C` | debug menu record table, stride `0x1C` |
| `0x0018C464` | record `Main Menu` (name ptr `0x08038DE0`) |
| `0x0018C4D4–0x0018C544` | records `Episode 1..5` |
| `0x0018C5D0` | record `Episodes` (child list `0x0818C28C`) |
| `0x0018C5EC` | record `Jeb Levels` (child list `0x0818C1E4`) |
| `0x0018C608/0x18C624/0x18C640` | `Buck Rides` / `Buck Fighting` / `Bosses` |
| `0x0018C65C` | record `Asset Viewer` |
| `0x0018C668` | `R Button: KeyRec Mode:` + `Off`/`Playback`/`Record` |
| `0x0038BB0–0x0038E98` | debug menu / stage-select string bank |
| `0x0077D000` | text/script bank (dialogue, ASCII + control codes) |
| `0x0077D8A8` | text record containing `PASSWORD` (menu font encoding) |
| `0x0077DEA0` | text record containing `INCORRECT` (menu font encoding) |
| `0x0077D810/0x77D848` | `NEW GAME` / `OPTIONS` |
| `0x08010660` | keypad wrapper: reads `KEYINPUT`, `&0x3FF`, calls `0x08010520` |
| `0x08003704` | password/main-menu screen update (state machine, jump table `0x08003888`) |
| `0x08003D44` | password-screen input state (state 4): cursor, letter stepping, submit |
| `0x08003F00` | 4-symbol → 16-bit code packer (base-16, leftmost = high nibble) |
| `0x08003204` | **password validator** (accepts/rejects, returns level-data pointer) |
| `0x08002E80` | code-seeded generator of the 40-step bit-permutation table |
| `0x08012C40` | MT19937 `sgenrand` (69069 LCG init) |
| `0x08012C84` | MT19937 `genrand` (twist + temper) |
| `0x08002BA4` | symbol index → glyph/class (adds 1 for 0..5, `+46` for 6..27) |
| `0x08002CA4` | class → stage-data pointer; `0x0` means reject |
| `0x08002B30` | menu-font glyph/tile converter (returns 1..27, wraps at 27) |
| `0x08002BA4` | converter dispatcher (27-entry jump table at `0x08002BB8`) |
| `0x08002C40` | second converter returning tile base values `6,52,53,...` |
| `0x08002CA4` | char → tile lookup used by the text renderer |
| `0x0802E80`, `0x08030xx`, `0x0803190` | text/metrics / renderer helpers |
| `0x02016310` | game input/key-state global written by the wrapper |
| `0x02016C10` | password-screen cursor (1..4; objects 2..5) |
| `0x02001584` | screen/sub-state byte (4 = password entry) |
| `0x02001574` | password busy/exit flag |
| `0x02001580` | post-submit sub-state (2 written on accept) |
| `0x020015AC` | accepted stage-data pointer (0 while pending) |
| `0x02001590` | object table; cells are objects 2..5 (`0x02001598..0x020015A4`) |
| `0x020015B0` | generated 40-entry bit-permutation table (read backwards at `+0x9C`) |
| `0x020173B0` | 1 KiB OAM shadow buffer (DMA source), rebuilt each frame |
| `0x03002600–0x03002810` | OAM assembler executed from IWRAM |
| `0x0201B3E4+` | array of preloaded password-screen text objects |

### Text encodings (derived, confirmed against bytes)

- Dialogue bank: literal ASCII; `0x01–0x1F` are control codes, `0xFFFC` is a
  space, `0xFFFE` ends a record. Example at `0x77D000`: `SIGH`, `NOW`, `WHAT`.
- Menu/3-D font strings use `byte = (letter - 'A') + 0x21`
  (`A→0x21 … Z→0x3A`). `PASSWORD` at `0x77D8AC` is
  `30 21 33 33 37 2F 32 24`; `INCORRECT` at `0x77DEA8` is
  `29 2E 23 2F 32 32 25 23 34`.
- The four password cells do **not** use this text encoding. They are
  separate 3-D sprites whose symbol index (0..15) is stored at
  `[[object+0x38]+0x2E]`; only 16 of the 26 letters have a glyph (§5.1).

## 5. Algorithm

The password is a **4-nibble checksum**, not a table of literal strings.

### 5.1 Input representation

- The four cells are objects 2..5 of the table at `0x02001590`. Each cell's
  symbol is the byte at `[[object+0x38]+0x2E]`, a value `v ∈ 0..15`.
- The symbol alphabet is exactly 16 glyphs:
  `A[0..15] = B C D F H J K L M N P Q R S T V`
  (letters A, E, G, I, O, U, W, X, Y, Z have no glyph).
- Therefore the input surface is `16^4 = 65,536` codes, not `25^4`.
- Packing (`0x08003F00`), left to right:
  `code = v0<<12 | v1<<8 | v2<<4 | v3`.

### 5.2 Validator (`0x08003204`)

```
validate(code):
    seed1 = 0x29A + 2*bit15(code) + bit0(code)
    mt.sgenrand(seed1)                       # MT19937, 69069 LCG init
    # 40 (src,dst) bit-position pairs, values 1..14, a != b
    for k in 0..39:
        a = 1 + (mt.genrand() & 15) ; while a > 14: redraw
        b = 1 + (mt.genrand() & 15) ; while b > 14 or b == a: redraw
    P = code
    for k in 39..0: swap bit a[k] and bit b[k] of P
    r9 = (P >> 10) & 0x1F          # selects the stage-data block
    L  = (P >>  1) & 0x0F          # selects the sub-level (0..10)
    B  = bit0(P) | bit15(P)<<6 | ((P & 0x3E0) >> 4)     # 7-bit check
    X  = P14<<8 | P13<<6 | P12<<4 | P11<<2 | P10
         | P4<<7 | P3<<5 | P2<<3 | P1<<1               # 12-bit seed
    mt.sgenrand(2*X)
    accept iff  (mt.genrand() & 0x7F) == B
            and r9 maps to a non-zero stage pointer (0x08002BA4/0x08002CA4)
            and L <= 10
    return stage-data pointer (0 on reject)
```

Seeding is deliberately weak: only two bits of the input enter the first
stream, so the 40-step permutation collapses to **four** distinct
permutations; the check then forces the remaining 14 bits through a
self-consistency equation. `r9` must be one of
`{1,2,3,4,8,11,14,17,21,22,23,24,25,26,27}` (15 non-zero stage pointers);
`L` must be `0..10`. Since the permutation is bijective, each
(stage pointer, L) pair has **exactly one** code.

### 5.3 Consequences

- The accepted set is a closed 165-code set (§6b, appendix A), not a sparse
  set of published literals.
- Any code can be checked off-line; see `pw.py` in the work directory for the
  reference implementation used to produce the appendix.
- The symbol that steers `r9`/`L` is not human-readable: the bit permutation
  mixes all 16 bits, so accepted codes look random.

### 5.4 Glyph rendering

The cell is a rotating 3-D glyph; the sprite's tile number is
`0x30 + 0x40*value + 4*animation_frame` and `value` itself is stored at
`[[object+0x38]+0x2E]`. Reading that byte while the roll settles is the
reliable way to identify a cell; the still image alone is ambiguous during
the roll.

## 6. Tables

### 6.1 Published level passwords (verified)

Sources: GameFAQs `920111` cheats page, ChapterCheats `12873` password page,
GameGenie GBA page, VGChartz `26744`. All fourteen use only symbols of the
16-letter alphabet. **All fourteen were confirmed accepted** by the ROM:

- in-emulator calls to `0x08003204` (all 14 return a non-zero stage pointer);
- on the real screen with typed input: `BBKD` and `DVHB` both show `CORRECT`
  (§7).

| Published | Symbols (nibbles) | Code | Stage block | Sub-level `L` |
|---|---|---|---|---:|
| `DVHB` | 2,15,4,0 | `2F40` | `0x0818FCA4` | 5 |
| `VCFK` | 15,1,3,6 | `F136` | `0x0818FD38` | 1 |
| `BQMF` | 0,11,8,3 | `0B83` | `0x0818FE94` | 0 |
| `HFKM` | 4,3,6,8 | `4368` | `0x08190070` | 1 |
| `DMCV` | 2,8,1,15 | `281F` | `0x081900DC` | 3 |
| `BBKD` | 0,0,6,2 | `0062` | `0x08190254` | 3 |
| `KNLC` | 6,9,7,1 | `6971` | `0x081904A0` | 2 |
| `BDJR` | 0,2,5,12 | `025C` | `0x08190504` | 1 |
| `BDRN` | 0,2,12,9 | `02C9` | `0x08190668` | 1 |
| `PSBH` | 10,13,0,4 | `AD04` | `0x08190790` | 1 |
| `QRNN` | 11,12,9,9 | `BC99` | `0x08190808` | 2 |
| `MMKN` | 8,8,6,9 | `8869` | `0x08190994` | 3 |
| `PSFH` | 10,13,3,4 | `AD34` | `0x08190AA0` | 1 |
| `DBVJ` | 2,0,15,5 | `20F5` | `0x08190B08` | 2 |

Each of the 14 published codes lands in a *different* stage block. The
published "level 1..14" ordering does not match block order; the table above
is the authoritative (block, sub-level) pair returned by the ROM.

### 6.2 Debug menu records (derived from bytes at `0x18C0B0`)

| Record address | Name pointer | Payload word |
|---|---|---|
| `0x18C464` | `Main Menu` | `0x0000540A` |
| `0x18C480` | `Logo Screen` | `0x1B0F02` |
| `0x18C49C` | `DayDream` | `0x1B1202` |
| `0x18C4B8` | `Ride to PoH` | `0xFFFF0D02` |
| `0x18C4D4` | `Episode 1` | `0xFFFF0D02` |
| `0x18C4F0` | `Episode 2` | `0xFFFF0D02` |
| `0x18C50C` | `Episode 3` | `0xFFFF0D02` |
| `0x18C528` | `Episode 4` | `0xFFFF0D02` |
| `0x18C544` | `Episode 5` | `0xFFFF0D02` |
| `0x18C560` | `End` | `0x1B000D` |
| `0x18C57C` | `Obj Viewer` | `0x1C000D` |
| `0x18C598` | `Music Player` | `0x1D000D` |
| `0x18C5B4` | `Fx Player` | `0x1E000D` |

Group records (`Episodes` `0x18C5D0`, `Jeb Levels` `0x18C5EC`,
`Buck Rides` `0x18C608`, `Buck Fighting` `0x18C624`, `Bosses` `0x18C640`)
carry a child-list pointer in word 1. Leaf labels include `Tutorial`,
`Slim`, `Rico`, `Bill`, `Gill`, `Phil`, `Ride 1..5`,
`Buck Fight 01..05`, `New Jeb 1-1 .. 5-4`.

### 6.3 Debug key-recording strings (`0x18C668`)

`R Button: KeyRec Mode:` / `Off` / `Playback` / `Record` — a developer
input record/replay overlay. No in-game gate was found.

## 6b. Enumeration

- **Space definition (input surface):** four slots; each slot steps through
  the 16-symbol alphabet `B C D F H J K L M N P Q R S T V`
  (`A` is unreachable as a value). Representable inputs = `16^4 = 65,536`.
- **Validator model:** the reconstructed `0x08003204` was run over all
  65,536 codes. **Result: exactly 165 accepted codes**, i.e. 15 stage-data
  blocks × 11 sub-levels (`L = 0..10`), one code per pair. Appendix A lists
  the complete set; `accepted_codes.txt` in the work directory is the same
  data in machine-readable form.
- **Agreement with the published list:** all 14 published codes are members
  of the 165 (one per block, blocks B..O; block A has no published code).
- **Independent spot checks against the ROM's own validator:** `BTBB` →
  `0x0818FCA4`, `PBSS` → `0x0818F83C`, `NNMV` → `0x0818FCA4`; rejected:
  `BTBC`, `0x1234`, `BBBB` (all return 0).
- **Rejection bound (in-game):** `BTBC` — one symbol away from the accepted
  `BTBB`, fully inside the alphabet — was typed and produced `INCORRECT`
  (§7). This proves acceptance is not "any well-formed 4-symbol input".
- **Minted code:** `BTBB` (code `0x0E00`, block `0x0818FCA4`, sub-level 0)
  is absent from every published list. Typed on the real screen it shows
  `CORRECT`, fades out and starts the game's opening cutscene (§7). Blocks
  A's eleven codes (`PBSS`, `PHLV`, …) are an entire accepted family with no
  published representative.

## 7. Validation evidence

**Observed on `:309`**
- Boot order: cracktro (Mode-7/GLENBEY, `iL Scn. 2004`, greetz, credits) →
  Disney Interactive logo → title `PRESS START` → main menu
  `NEW GAME/PASSWORD/OPTIONS/CREDITS`.
- Password screen opens with `B B B B`, cursor on the leftmost cell
  (`0x02016C10 = 1`, all four cell bytes 0). `Up` increments the selected
  cell's byte by exactly 1 (verified `3→4→5`), `Down` decrements (and wraps
  `0→15`); `Left/Right` move the cursor; the cursor ring does not leak
  outside objects 2..5.
- Typed `B B K D` (8 steps) → red **`CORRECT`** banner.
- Typed `D V H B` (7 steps) → **`CORRECT`**.
- Typed `B T B B` → **`CORRECT`**, then a fade and the opening cutscene
  (goat at the windmill) — an unpublished code reaching gameplay.
- Typed `B T B C` (the accepted `BTBB` with the last symbol stepped once) →
  red **`INCORRECT`**.
- Earlier pass: an alphabet-valid wrong code from arbitrary stepping also
  showed `INCORRECT`.

**Reproduced against the ROM's own code**
- `0x08003204` was called directly in-emulator with interrupts disabled
  (`IME=0`), from the running game. Results match the Python model exactly on
  every code tested: the 14 published codes return non-zero stage pointers;
  `BTBB`, `PBSS`, `NNMV` return non-zero; `BTBC`, `0x1234`, `0x0000` return 0.
- At `0x0803312` (after the permutation, before the check) the live registers
  for `DVHB` were `B=0x38, L=5, r9=8`, exactly what the model computes.

**Derived**
- Full validator, permutation generator, MT19937 use, symbol→class and
  class→stage-pointer tables (§4, §5).
- The accepted set (165 codes) and the fact that it is exactly
  15 blocks × 11 sub-levels.
- The previous pass's "25-symbol alphabet" was a sampling error: the
  alphabet is 16 symbols, and the codes are 4 nibbles, not 4 ASCII letters.
  This is why no literal search could ever find them.

**Inferred**
- The two-bit seeding (`bit0`, `bit15`) is an anti-casual-cheat obfuscation:
  it makes the permutation depend on the code itself while keeping the
  table small enough to regenerate at runtime.
- The 15 stage blocks are the game's episode/level-set records; `L = 0..10`
  is the level within a block. Block A (`0x0818F83C`) is accepted by the
  validator but has no published code, so it is probably an unreferenced or
  bonus block.

## 8. Unknowns

- **Debug menu gate:** the record table at `0x18C0B0` has no literal pointer in
  the image. Whether it is dead code (§16.3 case 2) or a gated screen was not
  settled; no breakpoint/watchpoint trace of its construction succeeded.
- **Stage block contents:** the 15 pointers are valid stage-data table heads
  (`0x0818F83C .. 0x08190B08`), but the mapping from block pointer + `L` to a
  human level name was not decoded. Block A's role (accepted by the
  validator, no published code) is unconfirmed.
- **`r9` class names:** the `0x08002BA4/0x08002CA4` tables were decoded as
  index→pointer, not as in-game names, so the four classes `{1,2,3,4}` that
  are accepted at low indices are not labelled.
- **Post-`CORRECT` flow:** `BTBB` reaches the opening cutscene; whether every
  block loads a cutscene, a level, or a menu was not tested exhaustively.
  No accepted code produced a hang or a crash in testing.

## 9. Tooling

- `mgba` (SDL) under `Xvfb :309` + `openbox`, `SDL_AUDIODRIVER=dummy`.
- `xdotool` for XTEST input, `scrot` for captures.
- `arm-none-eabi-objdump -M force-thumb` for raw Thumb disassembly.
- **mGBA CLI debugger (`mgba -d`) driven over a pty** for breakpoints,
  `frame` stepping, register/memory reads and writes (`r/1`, `r/4`,
  `w/r`, `w/2`). The GDB stub (`-g`) was unusable here (same failure mode as
  §16.13).
- **Calling ROM functions from the debugger:** the validator is pure with
  respect to `r0`. To invoke it, break in the idle loop
  (`0x08008D46`), set `r0=code`, `lr=0x08008D47`, `r0`/`pc` to `0x08003204`,
  step one instruction (`n`) so the prologue runs, then `c`. Interrupts must
  be masked first (`w/2 0x04000208 0`), otherwise the VBlank handler
  hijacks the trace. This gives a ground-truth oracle for any code.
- Python 3 with `zlib` to decode mGBA `.ssN` savestates: PNG with a
  zlib-compressed `gbAs` chunk, 397,312 bytes for this 8 MiB ROM.
  Layout used: CPU/header `0x00000`, VRAM `0x01000`, IWRAM `0x19000`,
  EWRAM `0x21000`, OAM `0x00C00`, palette below that.
- Reference model `pw.py`, enumeration `accepted_codes.txt`, and the
  frame-accurate debugger driver `run_dbg.py` are in the session work dir.

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed with this
report. Only hashes, addresses, encodings, and short identifiers needed to
reproduce the analysis are published.

## Appendix A — complete accepted set (165 codes)

Alphabet: `B C D F H J K L M N P Q R S T V` = values 0..15.
Each row is one stage-data block; columns are `L = 0..10`.
Every code not listed here is rejected (`INCORRECT`).
`*` marks a published code.

| Block | `L=0` | `1` | `2` | `3` | `4` | `5` | `6` | `7` | `8` | `9` | `10` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A `0x0818F83C` | `PBSS` | `PHLV` | `SHJK` | `NCLH` | `PCJS` | `FNLB` | `PNSL` | `NQJH` | `PKJS` | `CNVH` | `NHSH` |
| B `0x0818FCA4` | `BTBB` | `BNCQ` | `DMFC` | `NMDV` | `DDBB` | `DVHB`* | `NNMV` | `NSPJ` | `CFCC` | `RCPP` | `HVMK` |
| C `0x0818FD38` | `HCTJ` | `VCFK`* | `VMJK` | `KCRS` | `TJSL` | `QLCH` | `KHRJ` | `KRTV` | `JNTL` | `CBVR` | `TPJF` |
| D `0x0818FE94` | `BQMF`* | `BBPN` | `TRKB` | `DNPQ` | `PKDB` | `TQBD` | `RNBC` | `RNPF` | `TRPB` | `TSMD` | `FCMC` |
| E `0x08190070` | `QRDM` | `HFKM`* | `VRMQ` | `QCKM` | `DQDR` | `KTKR` | `VPKP` | `DKVN` | `VHMP` | `QSMM` | `VPMJ` |
| F `0x081900DC` | `HQCB` | `HTJB` | `DDCL` | `DMCV`* | `DPCB` | `DLJB` | `DLFL` | `MQKT` | `BFNB` | `MSPR` | `RBRT` |
| G `0x08190254` | `BHDH` | `HCKB` | `NHKD` | `BBKD`* | `DJDB` | `DMKB` | `STHB` | `PSPJ` | `CFHC` | `SSMD` | `PPBL` |
| H `0x081904A0` | `QHRS` | `HFJQ` | `KNLC`* | `SJJM` | `NTFM` | `SQCP` | `KVLF` | `LKKK` | `QKHQ` | `QKKJ` | `NBVP` |
| I `0x08190504` | `BQNJ` | `BDJR`* | `HVCT` | `SMFJ` | `TTBT` | `BKQS` | `DTCP` | `TFKT` | `PHMT` | `HDSR` | `TBRT` |
| J `0x08190668` | `BSDM` | `BDRN`* | `HSDT` | `QSKB` | `BRRC` | `TJDQ` | `VPKB` | `DSKT` | `CMTC` | `HBTM` | `BBPT` |
| K `0x08190790` | `RBNF` | `PSBH`* | `DMMJ` | `PNHH` | `BHPJ` | `BSMV` | `PTKH` | `DNJP` | `RKCS` | `BJSR` | `RPNF` |
| L `0x08190808` | `NRDR` | `QHQQ` | `QRNN`* | `QRQQ` | `QCNS` | `SVDR` | `SKHT` | `DTLV` | `QKCQ` | `HDVB` | `SMTR` |
| M `0x08190994` | `MBRV` | `CRHB` | `MRRQ` | `MMKN`* | `LCBH` | `RLFB` | `RPJB` | `LJHK` | `JQDF` | `MKKJ` | `RHSD` |
| N `0x08190AA0` | `TBFH` | `PSFH`* | `TRJK` | `PJLH` | `FCCM` | `LBJM` | `PPJH` | `PVJK` | `CMNM` | `RDLC` | `CRNT` |
| O `0x08190B08` | `VHCS` | `BNVS` | `DBVJ`* | `HPLP` | `VJNJ` | `DTLR` | `VNNF` | `DSVS` | `VKNN` | `CFVV` | `FMVL` |
