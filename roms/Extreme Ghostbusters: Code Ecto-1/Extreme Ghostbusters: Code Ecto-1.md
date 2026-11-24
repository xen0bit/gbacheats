# Extreme Ghostbusters: Code Ecto-1 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Extreme Ghostbusters: Code Ecto-1.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `EXTREME GHOS` (12-byte field, space/NUL padded) |
| Game code | `AEGE` (US) |
| Maker code | `6U` |
| Version | 0 (Rev.00) |
| Fixed byte 0xB2 | 0x96 |
| Entry branch | `0xEA000030` → entry 0x080000C8 (normal crt0; no cracktro/trainer branch) |
| Header checksum @0xBE | 0x0000 (rebuilt header artifact, §16.1) |
| Complement @0xBD | 0x49 (recomputed 0x62 from title/code bytes — header was edited) |
| MD5 | `ca03360842a7c269f9a46de25d5e779f` |
| SHA-1 | `a77eefc2d6dd9069e5f53612707d0389f7645e99` |
| SHA-256 | `efab03c5eeaa1a9eafe562b6bc2b39532e7a3490b2e4cbdc438fc6556068fe95` |
| Build stamp in ROM | `Apr 29 2002.11:29` at file 0x2DA550 (0x082DA550) |
| Developer | Magic Pockets (logo at boot); publisher DreamCatcher |

**Embedded-header scan (§0.2 / §11):** scanned all 4 MiB for the 156-byte Nintendo
logo (`24 ff ae 51 …`). Exactly **one** header, at file offset 0x0 (ROM base
0x08000000). This is *not* a multi-game pack and no appended trainer was found.
The 0x0000 header checksum plus wrong complement are consistent with a rebuilt
*header* only, not a patched game image: the entry word is a normal ARM branch
into the stock crt0, and the first instructions at 0x080000C0 are the standard
GBA interrupt/stack setup. No GameShark/CodeBreaker codes are present in the image
and none were used in this analysis.

---

## 2. Executive summary

The game has a real, developer-intended **9-symbol password system** reached from
the title menu (`PASSWORD`). It is **algorithmic**, not a lookup table: there is no
list of accepted passwords in the ROM (verified — all 18 published codes are
absent as ASCII, +0x20, 5-bit-packed and byte-substitution encodings). Instead the
validator converts each of the 9 characters to a 5-bit index, packs 45 bits, applies
a bit-level permutation, checks a 5-bit checksum folded into the permuted bytes,
and finally bounds-checks a 26-bit mixed-radix field word before unlocking the
level/character state.

Alphabet (32 symbols, file 0x2D9E10 / 0x0802D9E10):
`0123456789BCDFGHJKLMNPQRSTVWXZ/*`
(note `/` = index 30, `*` = index 31 — vowels A/E/I/O/U/Y are excluded).

The full validator was reimplemented in Python and cross-checked against the ROM's
own functions executed in Unicorn (§16.19), agreeing on **all 18 valid published
codes** plus the novel codes below and all rejection cases. The entire space is
 characterised in §6b. A novel code, **`WSF0JJJTJ`** (field tuple
`[9,4,12,3,12,3]`, never published), was entered on the real password screen and
accepted: the game transitioned into the racing level (screenshot evidence listed
in §7). Bounds were proven by testing a wrong checksum, an invalid character, and
three out-of-range field words — all rejected by the ROM.

A ninth published code, `WSJPJLZIV`, is **invalid** because it contains `I`, which
is not in the game's alphabet — a published-list typo (§16.7).

---

## 3. How to reproduce

**Emulator/setup:** mGBA (CLI SDL build) under Xvfb on `DISPLAY=:317`,
`SDL_AUDIODRIVER=dummy`, 3× scale, built-in `-d` command-line debugger driven over
a pty. Input via XTEST (`xdotool`). Menu cursor steps need ~100 ms holds; the
password keypad's A/B keys must be **instant** taps (`keydown` immediately followed
by `keyup`) — a 100 ms hold enters 2 characters because the game adds one per
frame while held.

**Menu path (RAM-verified):**
1. Title → `Start` → main menu (`NEW GAME / PASSWORD / OPTIONS`).
2. Main menu → `Down`, `A` → PASSWORD screen: 4×8 on-screen keyboard of 32 symbols
   and a 9-slot input field. Cursor starts at symbol `0` (row 0, col 0).
3. Move cursor with D-pad, press `A` to append a symbol; 9th `A` submits.
   `B` deletes one symbol (and exits the screen if the field is empty).
4. Correct code → level starts; wrong code → "INCORRECT PASSWORD" and the field
   clears.

**Codes tested on-screen:**
* Published `HGBNL14VJ` (The Hall) → accepted, level started (`shot_25_code.png`).
* Novel `WSF0JJJTJ` → accepted, level started (`shot_45_novel.png`).
* Malformed entry (`7NH***0***`) → "INCORRECT PASSWORD" (`shot_31_state.png`).

**Other screens walked (all with screenshots):** title, main menu, password,
gameplay, pause (`PAUSE / CONTINUE? / QUIT`, `shot_46_pause.png`), quit confirmation
(`ARE YOU SURE? YES / NO`, `shot_47_quit.png`), options
(`MUSIC: YES / SOUND: YES / CREDITS`, `shot_50_options.png`) and scrolling credits
(`shot_52_credits.png`). **No hidden menu, debug screen, level-select, or button
code was found on any screen.** The only cheat surface is the password system.

**Offline validator (exact):** `validator3.py` in the work dir;
`mint2.py` mints codes for arbitrary field tuples; `oracle.py` executes the ROM's
own packer/permuter via Unicorn. The unmodified published list and novel codes were
also fed to the ROM's validator directly through Unicorn (`uc_emu.py`).

---

## 4. Address map

All addresses are ROM addresses (file offset = address − 0x08000000) unless marked RAM.

| Address | Kind | Meaning |
|---|---|---|
| 0x08000000 | header | entry branch 0xEA000030 |
| 0x082DA550 | data | `"Apr 29 2002.11:29"` build stamp |
| 0x0802D9E10 | data | 32-symbol password alphabet `0123456789BCDFGHJKLMNPQRSTVWXZ/*` (NUL at +0x20) |
| 0x0802D9E34 | data | mixed-radix divisor table `[19,20,13,11,13,11]` (u32 each) |
| 0x0802D9E48 | data | keyboard/permutation auxiliary byte tables |
| 0x082D23C8 | data | pointer → 0x0802D9E10 (alphabet used by password screen) |
| 0x082D2418 | data | pointer → 0x0802D9E10 (alphabet used for 9th symbol) |
| 0x082D337C | fn | **password validator** `FUN_082D337C(char* code9)` → r0 = 1 accept / 0 reject |
| 0x082D3438 | data | pointer → alphabet (validator's search table) |
| 0x082D343C | data | bound `0x007691FB` (max 26-bit field word) |
| 0x082D3440 | data | pointer → divisor table 0x0802D9E34 |
| 0x082D3500 | data | ptr → RAM 0x03002620 (level-name index) |
| 0x082D3504 | data | ptr → divisor table (stride 4, six divisors) |
| 0x082D3508 | data | ptr → RAM 0x03000680 (field 1) |
| 0x082D350C | data | ptr → RAM 0x03000744 (field 2, +1 → field 4) |
| 0x082D3510 | data | ptr → RAM 0x03000748 (field 3, +1 → field 5) |
| 0x082D3514 | data | ptr → RAM 0x03000754 (14-bit value ×100) |
| 0x082D2224 | fn | password-screen handler (builds 9-char stack buffer, calls validator) |
| 0x082D8E18 | fn | bit writer `FUN_082D8E18(width,val,dst,bitoff)` |
| 0x082D8EE8 | fn | bit reader `FUN_082D8EE8(width,src,bitoff)` |
| 0x082D8E18 / E4 | const | endian masks `0xFF00FF00` / `0x00FF00FF` used by packer |
| 0x082D8F48 / 4C | const | same masks for reader |
| 0x082D3060 | fn | **bit permutation** of the 6-byte packed buffer |
| 0x082D9654 | fn | unsigned modulo (restoring division) |
| 0x082D95DC | fn | unsigned divide |
| 0x082D8FFC | fn | VBlank/frame wait (called in input loop) |
| 0x08096E04 | data | tokenised/compressed English text bank (menus, level names, credits) |
| 0x080D0A00 | data | tokenised French text bank |
| RAM 0x03007Exx | stack | password input buffer (9 bytes). Observed at 0x03007E74 in one frame; stack depth varies (locate live via breakpoint at 0x082D337C → r0) |
| RAM 0x03002620 | state | level-name index written by validator (novel code → 0x11) |
| RAM 0x03000680 / 0x03000744 / 0x03000748 | state | decoded mixed-radix fields |

**File-offset↔ROM-address:** all hits from `strings -t x`/`grep -abo` were converted
with `rom = 0x08000000 + file_offset`. The alphabet literal was found by
`strings -t x` → file 0x2D9E10, then confirmed by `search_bytes` in Ghidra at
0x082D9E10 with 7 xrefs (0x082D22C2, 0x082D22E6, 0x082D23A0, 0x082D23DE,
0x082D2478, 0x082D335C, 0x082D339E).

---

## 5. Algorithm

Pseudocode precise enough to reimplement (verified against the ROM function):

```
ALPHA = "0123456789BCDFGHJKLMNPQRSTVWXZ/*"   # 32 symbols; '/'=30, '*'=31
BOUND = 0x7691FB
DIVS  = [19, 20, 13, 11, 13, 11]

def validate(code):                  # code: 9 characters from ALPHA
    idx  = [ALPHA.index(c) for c in code]
    # 1) pack 9×5 = 45 bits MSB-first, placed in the top 45 bits of an 8-byte word
    v45  = 0
    for s in idx: v45 = (v45 << 5) | s
    packed = (v45 << 19).to_bytes(8,'big')       # bits 0..44 of the 64-bit word
    # 2) bit-level permutation of the first 6 bytes (FUN_082D3060)
    q = permute(packed[0:6]) + packed[6:8]        # 8 bytes
    # 3) checksum
    t  = q[0]^q[1]^q[2]^q[3]^q[4] ^ 0x3B
    t  = ((t & 0xAA) >> 1) ^ t                    # 8-bit
    check = (t & 0x1F) ^ (t >> 3)                 # 5 bits
    expected = (int.from_bytes(q,'big') >> 19) & 0x1F   # 5 bits @ virtual offset 40
    if check != expected: return REJECT
    # 4) 26-bit field word read MSB-first from permuted bits 0..25
    word = int.from_bytes(q,'big') >> (64-26)
    if word > BOUND: return REJECT
    # 5) mixed-radix decomposition → six game fields
    fields = []
    rem = word
    for d in DIVS:
        fields.append(rem % d)
        rem //= d
    return ACCEPT with fields
```

Notes on the exact bit layout (§6.4):
* `FUN_082D8E18`/`FUN_082D8EE8` operate on 32-bit words after a full byte swap
  (`>>16|<<16` then byte-swap masks `0xFF00FF00`/`0x00FF00FF`), i.e. the effective
  bitstream is big-endian, MSB-first. The 3-bit offset observed when probing a
  *single* field is an artefact of the word-swap; for the complete 9-field write
  the result is exactly `(v45 << 19)` as an 8-byte big-endian word (confirmed on
  all 18 published codes by emulating the writer).
* The permutation `FUN_082D3060` is **affine over GF(2)** — not a byte shuffle.
  It was reimplemented from the Thumb assembly (the Ghidra decompilation had two
  wrong masks: the `p[2]` mask is `0xEF`, not `0xCF`, from `subs r5,#0x31` applied
  to `0x20`). `permute(0) = d7 bda3 4486 40` in its 6-byte output; the GF(2) matrix
  is built by probing each of the 45 symbol bits (`mint.py`).
* The checksum and bound tests use the **permuted** buffer, not the typed code —
  the 9th symbol is mixed into byte 5 by the permutation. Reading it from the
  original code (an early mistake) rejected every published password; fixing this
  made the model agree with the ROM on all 18.

Encoder (minting): both constraints (word bits 0..25 = target, checksum bits =
permuted bits 40..44) are affine in the 45 symbol bits. Solving the resulting
31×45 GF(2) system reproduces published fields (up to the 2^14 unused-bit aliases,
§16.4b) and mints arbitrary valid codes (`mint2.py`).

---

## 6. Tables

**Alphabet (index → symbol):** 0-9 → `0`–`9`; 10→B, 11→C, 12→D, 13→F, 14→G,
15→H, 16→J, 17→K, 18→L, 19→M, 20→N, 21→P, 22→Q, 23→R, 24→S, 25→T, 26→V,
27→W, 28→X, 29→Z, 30→`/`, 31→`*`. Vowels A/E/I/O/U/Y are not representable.

**On-screen keyboard layout (4 rows × 8 cols, row-major):**
```
0 1 2 3 4 5 6 7
8 9 B C D F G H
J K L M N P Q R
S T V W X Z / *
```
(row 1 col 2 is `B`, col 3 `C`, col 4 `D` — the stylised slime font makes `B`/`D`
look similar; the ROM alphabet string is authoritative.)

**Published codes (3rd party cheat indexes, all cross-checked against the ROM):**

| Level | Code | Fields (verified by decoder) |
|---|---|---|
| The Hall | `HGBNL14VJ` | \[0,3,0,3,0,3\] |
| Corridor | `5PMDTF/K2` | \[1,3,2,0,0,4\] |
| Office | `21QSR9JTS` | \[2,3,2,3,0,4\] |
| Big Building Boss | `8G20S86SC` | \[16,4,2,4,1,4\] |
| Racing 2 | `30J82JBMB` | \[12,4,2,4,1,2\] |
| The Main Aisle | `BNKN34SMW` | \[3,4,2,4,1,2\] |
| The Crypt | `V8JNNVGLC` | \[4,4,3,3,2,3\] |
| Closer to the Underworld | `MD*XN7KTJ` | \[5,4,12,3,12,3\] |
| Racing 3 | `VD*PJKFTS` | \[13,4,12,3,12,3\] |
| In the Wings | `MDZ9KK/T8` | \[6,4,12,3,12,3\] |
| 3rd party cheat indexes Ball | `MD2TK4XTK` | \[7,4,12,3,12,3\] |
| On Stage | `WS0PJ6LTC` | \[8,4,12,3,12,3\] |
| Broadway Star Theater Boss | `VS31JL9TW` | \[17,4,12,3,12,3\] |
| Racing 4 | `LDK9K6HTC` | \[14,4,12,3,12,3\] |
| Don't Forget the Guide | `WSJPJLZIV` | **INVALID** — contains `I` (ROM rejects, r0=0) |
| Carnivorous and Hungry | `WSFKP6WT3` | \[10,4,12,3,12,3\] |
| The Final Confrontation | `MS29P7JTW` | \[11,4,12,3,12,3\] |
| Final Boss | `VSFPPMHT8` | \[18,4,12,3,12,3\] |
| The Ending | `LXK8KKFTL` | \[18,3,12,3,12,3\] |

All 18 valid codes are absent from the ROM as literal strings (searched as ASCII,
lowercase, +0x20, 5-bit packed LSB/MSB, and alphabet-index bytes) — confirming an
algorithmic validator rather than a table.

**Field meaning (inferred conservatively):** the six radices 19/20/13/11/13/11
most plausibly encode level (0–18) plus five character/trap/costume/variant
selectors; the level-name index written to RAM 0x03002620 proves field 0 drives
level selection. The exact semantics of fields 1–5 were not exhaustively exercised
in gameplay and are labelled *inferred*.

---

## 6b. Enumeration

**Space definition**
* Alphabet: 32 symbols; length: 9 characters → **32^9 = 35,184,372,088,832**
  (≈3.5×10¹³) representable strings.
* Checksum: **5 bits** (1/32 of inputs pass).
* Field word: **26 bits** with mixed radices \[19,20,13,11,13,11\] (product
  7,770,620) bounded by `BOUND = 0x7691FB = 7,767,547` (the top 73 field tuples
  are excluded). Bound fraction = 0.11579.
* Expected number of accepted strings ≈ 35.18×10¹³ / 32 × 0.11579 ≈
  **1.27×10¹¹** (checksum-valid, in-bound). The system is therefore *algorithmic*,
  not a finite list: public level codes are only a tiny curated subset.
* Aliases: with 45 input bits and 31 linear constraints, ~2¹⁴ spellings exist per
  (field tuple, checksum) equivalence class (§16.4b). Two different minted codes
  can be behaviourally identical.

**Novel codes generated (absent from every published list)**, all verified by the
ROM's own validator (`r0=1`) via Unicorn and in the address map:

| Code | Field tuple | v | Verified |
|---|---|---|---|
| **`WSF0JJJTJ`** | \[9,4,12,3,12,3\] (field 0 = 9 is unpublished) | 0x2A9595 | **Entered on real password screen → game accepted, level started (`shot_45_novel.png`); RAM state written** |
| `VD/JKJ0TJ` | \[15,4,12,3,12,3\] | 0x2A959B | ROM validator r0=1 |
| `CP201S0KJ` | \[9,2,5,1,7,2\] | 0x1B77AB | ROM validator r0=1 |
| `H//J88L/0` | \[0,0,0,0,0,0\] | 0x0 | ROM validator r0=1 |

**Bounds proven by rejection (all via the ROM's validator, r0=0):**

| Rejected input | Reason |
|---|---|
| `HGBNL14VK` | wrong checksum (last symbol changed on a valid code) |
| `WSJPJLZIV` | character `I` is outside the 32-symbol alphabet (published typo) |
| `WS4JLJ2H0` | valid checksum but 26-bit word = `0x7691FC` = BOUND+1 (out of range) |
| `VXW0KJJHJ` | valid checksum but 26-bit word = `0x7695E3` = BOUND+1000 |
| `TFQ0MJ0HJ` | valid checksum but 26-bit word = `0x7791FB` = BOUND+65536 |

These separate the checksum layer from the semantic range layer (§16.5): a code can
pass the checksum and still be rejected by the bound check.

**Completeness of the negative result (no other cheat surface):** every reachable
screen enumerated in §3 with screenshots; each text bank searched with `strings`,
case-insensitive and `+0x20` transforms. The two large text banks at 0x08096E04 and
0x080D0A00 use a tokenised encoding (high bytes 0xE0–0xFF as dictionary selectors)
which `strings` renders as garbled fragments such as `asswd` inside `New game`;
the password-relevant strings were decoded via the on-screen font tiles (the
keyboard alphabet string at 0x0802D9E10 is plaintext and matches the rendered
glyphs exactly). No `debug`, `cheat`, `level select` or hidden-menu string was
found in either bank or elsewhere in the 4 MiB image. No button-code table exists:
the pause/menu handlers only process D-pad/A/B/Start for the documented options.

---

## 7. Validation evidence

**Observed** (emulator / screenshots / RAM):
* Title, main menu, password, gameplay, pause, quit-confirm, options, credits
  screens — `shot_00`–`shot_52` in `/tmp/ecto1/`.
* Published `HGBNL14VJ` accepted → level gameplay (`shot_25_code.png`).
* Novel `WSF0JJJTJ` accepted → level gameplay (`shot_45_novel.png`).
* Malformed entry → "INCORRECT PASSWORD" (`shot_31_state.png`).
* RAM read after novel code: 0x03002620 = 0x11, 0x03000748/9 = 0x03/0x03
  (validator output fields written). Input buffer located at r0 on breakpoint
  (0x03007E74 in one frame) and its contents matched the typed bytes.

**Derived** (disassembly / Unicorn):
* Validator algorithm, alphabet, divisor table, BOUND, bit layout and permutation
  — `FUN_082D337C` and helpers, cross-checked by executing the ROM bytes in
  Unicorn (`uc_emu.py`) and by Ghidra decompilation.
* All 18 published codes accepted; `WSJPJLZIV` and all four rejection cases
  rejected by the ROM function directly.
* Python model (`validator3.py`) reproduces the accept/reject and field
  decomposition for every tested input.

**Inferred:**
* Exact gameplay meaning of decoded fields 1–5 (character/trap/costume/variant
  selectors) — not exhaustively played.
* The purpose of the auxiliary byte tables at 0x082D9E48/0x082DA480 (likely font
  metrics and a scan-order table) — not required to characterise the code space.

**Prompt-injection check:** fetched cheat pages (3rd party cheat indexes snippets,
3rd party cheat indexes) were treated as data; no embedded instructions, payment requests or
fake "decode keys" were encountered (contrast §16.8).

---

## 8. Unknowns

* The semantic labels of the five non-level fields are inferred from radix sizes
  and observed RAM writes but not individually verified by playing each variant.
* The token map of the compressed text banks was not fully decoded; the negative
  result rests on screen enumeration plus the alphabetical/pattern searches
  described in §6b, not on a complete dictionary reconstruction. (The positive
  password finding does not depend on this.)
* The 73 excluded top field tuples (word values 7,767,548–7,767,619) are rejected
  by the bound check; their intended meaning, if any, is unknown.
* No attempt was made to enumerate the ~2¹⁴ spelling aliases per field tuple.

---

## 9. Tooling

* `binutils-arm-none-eabi` (`arm-none-eabi-objdump`), `capstone` 5.0.7,
  `keystone-engine`, Python 3, `unicorn` 2.1.4 (installed with
  `pip install --break-system-packages unicorn`) — used to execute ROM functions
  as an oracle.
* REA/Ghidra MCP (`open_binary` raw-binary, ARM/Thumb, base 0x08000000) —
  `search_bytes`, `xrefs`, `procedure_pseudo_code`, `procedure_assembly`; the
  permutation was corrected against the assembly after the decompiler produced
  two wrong masks.
* mGBA CLI `-d` built-in debugger over a Python pty controller
  (`mgba_pty.py`, `dbg.py`) for memory reads (`x/1`, `r/4`), breakpoints
  (`break/t`), register reads (`status`/`w/r`), and SIGINT-based pause.
* Xvfb `:317` + openbox + XTEST (`xdotool`) for reproducible input and
  `import -window root` for screenshots.
* Scripts in `/tmp/ecto1/`: `validator.py`→`validator3.py` (model),
  `perm_asm.py` (permutation from assembly), `oracle.py` (ROM pack/permute),
  `mint.py`/`mint2.py` (GF(2) solver and minting), `uc_emu.py` (Unicorn harness),
  plus the input helpers.
* No ROM or extracted asset is redistributed; only addresses, hashes, algorithms
  and self-authored scripts are published.

---

## Legal note

Analysis only. The ROM and any screenshots of copyrighted assets remain local to
this workspace; this report contains no ROM data, graphics, audio or full game
text — only hashes, addresses, algorithms and original tooling.
