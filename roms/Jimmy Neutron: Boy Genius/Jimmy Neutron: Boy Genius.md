# Jimmy Neutron: Boy Genius (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Jimmy Neutron: Boy Genius.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `JIMMYNEUTRON` |
| Game code / maker | `AJNE` / `78` |
| Version | 0x00 (Rev.00), complement 0x13, header checksum 0x0000 |
| Entry word | `0xEA00002E` → stock `0x080000C0` |
| MD5 | `2acd2b101e2f03a3fb95ed41b187d5ec` |
| SHA-1 | `31ed7659e2e072d1c00baf95c0ee9c770e949900` |
| SHA-256 | `bf2c1899bb63797da6f54b5025a18749189e94c70e2f330558d90d1d77395836` |

Phase 0: `file` reports a single GBA image. Scanning the whole 4 MiB for the 156-byte
Nintendo logo (and for its first 16 bytes) finds exactly one header base, `0x0`, so
this is **not** a multi-game pack and has **no appended trainer**. The entry branch is
the stock `b 0x080000C0` (no cracktro patch). The zero header checksum is the usual
rebuilt-header artifact; the complement byte 0x13 is intact. Region is USA (AJNE).

## 2. Executive summary

The game has a **developer-intended 12-symbol password system** on
**Main Menu → Enter Code**. It is fully algorithmic — no code strings or index
records exist anywhere in the ROM. The 36-symbol input alphabet is
`1234567890BCDFGHJKLMNPQRSTVWXYZ?!+-$` at `0x08030BBC` (the on-screen grid also has
a 37th smiley glyph plus DEL/RND/OK, but the validator only searches the 36 ASCII
symbols).

The validator is at `0x08012550`. It maps each symbol to its alphabet index
(0–35), requires `sum(index[0..10]) mod 36 == index[11]`, then undoes a 32-bit LCG
keystream (`state = 0x41C64E6D*state + 12345`, XOR-free subtraction of `state & 31`
mod 36) on positions 1–10. It then range-checks the decoded fields and writes a
game-state struct at IWRAM `0x030014F0`. The decoded field `d[10] % 3` is the
**difficulty** (0 = Easy, 1 = Medium, 2 = Hard); `d[6]` is the level slot (1–9).

16 codes are published (8 Easy + 8 Hard). **14 of 16 round-trip exactly through the
recovered algorithm**, which validates the decoder; the other two published strings
fail its checksum and are not accepted by this ROM. Two codes absent from every
published list were minted and **accepted in the emulator**:
`WM5DR5H3MCMC` (Medium Asteroid Field; RAM difficulty field = 1 vs 0 for the Easy
code) and `WM5DR5G3MCL0` (level slot 1, a distinct Retroville scene never shown by
any published code). Bounds were proven by in-game `WRONG CODE` rejections for a bad
checksum and an out-of-range level field.

## 3. How to reproduce

* Emulator: `mgba -3` under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, keymap
  A = `x`, B = `z`, Start = `Return`, D-pad = arrow keys. Hold keys 120–150 ms with
  ~250–450 ms gaps; shorter taps are dropped and menus double-step.
* Boot path: press Start through the legal/THQ/Nickelodeon/Human Soft screens and
  the title, skip the intro, press B on **Tutorial/Easy/Medium/Hard** → **Main Menu**
  (Single Player / Multiplayer / Enter Code / Options / Credits) → **Enter Code**.
* On the code screen the cursor starts on `1` at grid (row 0, col 0). Move with the
  D-pad (row wraps mod 4, col wraps mod 10), press A to select a symbol. After the
  12th symbol the game **auto-moves the cursor to OK**; press A to submit.
* Screens walked with visual confirmation: title, all four splashes, difficulty
  select, main menu, Multiplayer → Select Game Type (Platform / Race / Return to
  Main), Options Menu (Music, Sound Fx, Return to Main), scrolling Credits, in-game
  pause menu (four-icon panel), code entry, `WRONG CODE`, and accepted-code level
  intros. No hidden/debug menu was reached by any of these paths.
* Codes entered in-game:
  * `WM5DR5H3MCLB` (published Easy Asteroid Field) → accepted, space-intro cutscene.
  * `WM5DR5H3MCMC` (novel) → accepted, same level, different difficulty field.
  * `WM5DR5G3MCL0` (novel) → accepted, distinct Retroville/Jimmy-and-Goddard scene.
  * `WM5DR5H3MCLC` (bad checksum) → `WRONG CODE`.
  * `WM5DR5R3MCLL` (level slot 10, out of range) → `WRONG CODE`.
  * `51867F7MJ5Y2` (single-character repair of a bad published code) → rejected.
* Dynamic RAM reads used mGBA's CLI debugger (`-d`) with a Thumb breakpoint at
  `0x080126E4` (the validator's accept return) and `stdbuf -o0` so output is not
  buffered. The GDB stub (`-g`) proved unreliable in this environment (packet
  errors / emulator exit) and was not used for the final evidence.

## 4. Address map

File offset = ROM address − `0x08000000`.

| ROM address | Kind | Meaning |
|---|---|---|
| `0x08000000` | code | header / entry branch to `0x080000C0` |
| `0x08030BBC` | data | 36-byte input alphabet `1234567890BCDFGHJKLMNPQRSTVWXYZ?!+-$` (file `0x30BBC`); followed by `14 15 16 17 25` (glyph/aux bytes) |
| `0x08030B80` | data | 15×4 byte table of values 1–8 immediately before the alphabet (grid glyph metrics) |
| `0x08032810` | text | ` WRONG CODE ` (English string table entry 62) |
| `0x08032924` | text | `Code:` |
| `0x08032ABC` | text | `Enter Code` |
| `0x080A56B0` | data | English string-pointer table (entry 0 = `ENGLISH`) |
| `0x08011DA4` | code | renders the 10×4 symbol grid using the alphabet |
| `0x080120B6` | code | symbol-select handler (`alphabet[(sel*37)>>8]`), auto-advances cursor to OK at 12 chars |
| `0x080121C0` | code | code-screen cursor/updater; columns `0..9`, rows `0..3` |
| `0x080121AC` | code | OK-cell call site: `bl 0x08012550`, `-1` → WRONG CODE |
| **`0x08012550`** | **code** | **password validator** (accept: r0 = 0; reject: r0 = −1) |
| `0x08012688` | literal | `0x03001511` = start of the 12-symbol buffer |
| `0x0801268C` | literal | `0x41C64E6D` (LCG multiplier) |
| `0x08012690` | literal | `0x3039` = 12345 (LCG increment) |
| `0x08012694` | literal | `0x080A4CFC` (difficulty/world pointer table) |
| `0x080302B4` / `0x0803032C` | code | unsigned divide / modulo helpers |
| `0x080304BC` | code | 16-byte copy helper |
| `0x080202B4` | code | unrelated base-37 hash of a NUL-terminated string (multiplayer `<Random>` world seed), **not** the password validator |
| `0x030014F0` | RAM | validator state struct (base `r5`) |
| `0x03001511`–`0x0300151C` | RAM | 12-symbol input buffer (`struct+0x21` … `+0x2C`) |
| `0x03001510` | RAM | `struct+0x20`: decoded difficulty (`d[10] % 3`) |
| `0x030014F0` | RAM | `struct+0x00`: decoded level slot (`d[6]`) |
| `0x030020D0` | RAM | key-input state (edge detection) |

## 5. Algorithm

Let `A` be the 36-char alphabet and `idx(c)` the index of symbol `c` in `A`.
The on-screen 37th glyph (smiley) is not in `A`; it survives the index conversion as
raw byte `0x14` and cannot produce a valid checksum, so it is not part of the code
alphabet.

```
validate(code[0..11]):
    # 1. ASCII -> alphabet index, in place (0x8012586..0x80125BA)
    for i in 0..11: v[i] = idx(code[i])          # linear scan; no match leaves raw byte
    # 2. checksum (0x80125BC..0x80125E2)
    if (sum(v[0..10]) & 0xFF) % 36 != v[11]: return -1
    # 3. undo LCG keystream on positions 1..10 (0x80125E4..0x801261C)
    d[0] = v[0]; state = v[0]
    for i in 1..10:
        state = (0x41C64E6D * state + 12345) & 0xFFFFFFFF
        d[i] = (v[i] - (state & 31)) mod 36
    # 4. semantic/range checks
    if d[6] not in 1..9:                 return -1       # 0x801261E..0x801262A
    if d[10] // 3 > 9:                   return -1       # 0x801262C..0x8012658
    if not (d[9] == 31 or table_ok(d)):  return -1       # 0x801265A..0x801267E
    # 5. state outputs (0x8012698..0x80126E0)
    struct[0x00] = d[6]                   # level slot
    struct[0x20] = d[10] % 3              # difficulty: 0 easy, 1 medium, 2 hard
    struct[0x26] = d[10] // 3
    struct[0x24] = d[9]
    struct[0x16] = d[7] | (d[8] << 5)     # 10-bit field
    h = folded base-9 over d[5],d[4],d[3],d[2],d[1]
    struct[0x12] = ((h // 20000) + 1) * 20000
    return 0
```

Encoder (inverse of step 3 + checksum), used to mint codes:

```
encode(d[0..10]):
    e[0] = d[0]; state = d[0]
    for i in 1..10:
        state = (0x41C64E6D*state + 12345) & 0xFFFFFFFF
        e[i] = (d[i] + (state & 31)) mod 36
    e[11] = sum(e[0..10]) mod 36
    return ''.join(A[x] for x in e)
```

Free fields: `d[0]` (LCG seed), `d[1..5]`, `d[7]`, `d[8]`, `d[9]` (use 31 as the
wildcard that bypasses the table check). Constrained: `d[6] ∈ 1..9`,
`d[10] ∈ 0..29`.

## 6. Tables

**Alphabet** (index → char):
`0:1 1:2 2:3 3:4 4:5 5:6 6:7 7:8 8:9 9:0 10:B 11:C 12:D 13:F 14:G 15:H 16:J
17:K 18:L 19:M 20:N 21:P 22:Q 23:R 24:S 25:T 26:V 27:W 28:X 29:Y 30:Z 31:?
32:! 33:+ 34:- 35:$`

**Published codes (GameFAQs / Freeola; 8 Easy + 8 Hard)** and decoder result:

| Level | Easy (published) | RT | Hard (published) | RT |
|---|---|---|---|---|
| Asteroid Field/Belt | `WM5DR5H3MCLB` | ok | `2040YL61TT0T` | ok |
| Yokian Moon | `KVZQG3Q50LZG` | ok | `GGP6WCC273-3` | ok |
| Yolkus | `51867F7MJ5YP` | **bad** | `2H?-!L81TT0K` | ok |
| Yokian Palace | `MMS-KXBVC4FS` | ok | `+R6H!L91TT0F` | ok |
| Dungeon | `N?+94T1?DJXW` | ok | `456N$DWBWM?F` | ok |
| Boss 1 Poutra | `939BSYT41N0Z` | ok | `XZ16F2F8NS$!` | ok |
| Boss 2 King Goobot | `BD5VVRDF3GXV` | ok | `GRZB87HNYFR2` | **bad** |
| Ending Scene | `3L!VPH26V7$8` | ok | `+CLT3LD1TTSF` | ok |

"RT" = exact round-trip through decoder→encoder. All 14 RT codes also have decoded
`d[6] = 2..9` (levels 1..8) and `d[10] % 3 = 0` (Easy) or `2` (Hard). The two
non-RT strings fail the checksum as published; the decoder's minimal last-character
repairs (`…5Y2`, `…FRB`) were generated, but entering `51867F7MJ5Y2` in the emulator
was **also rejected** (its decoded `d[6] = 28` is out of range), so those two
published strings are not valid for this exact ROM and cannot be repaired by a
single-character fix. No literal form of any published code (ASCII, +0x20, UTF-16,
alphabet indices, reversed, ±1, XOR) occurs anywhere in the 4 MiB image.

**Decoded published-code structure** (illustrative, Easy/Hard Asteroid):

| Code | d0 | d1 | d2 | d3 | d4 | d5 | d6 | d7 | d8 | d9 | d10 | d10%3 | d10//3 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `WM5DR5H3MCLB` | 27 | 31 | 23 | 26 | 0 | 0 | 2 | 0 | 0 | 31 | 9 | 0 (Easy) | 3 |
| `2040YL61TT0T` | 1 | 3 | 32 | 25 | 0 | 0 | 2 | 0 | 0 | 31 | 14 | 2 (Hard) | 4 |
| `WM5DR5H3MCMC` (novel) | 27 | 31 | 23 | 26 | 0 | 0 | 2 | 0 | 0 | 31 | 10 | 1 (Medium) | 3 |

All published codes use `d[9] = 31` (`?`, the wildcard) except Yokian Moon Easy
(`d[9] = 4`), which must satisfy the table check at `0x801265A` instead.

## 6b. Enumeration

**Space definition.** 12 symbols × 36 alphabet values = `36^12 ≈ 4.74×10^18`
spellings. The validator's effective space is the decoded payload: `d[0]` (6 bits),
`d[1..5]` (5×6 bits), `d[6]` (4 values after range, 1–9), `d[7]`,`d[8]` (5 bits each),
`d[9]` (6 bits, with 31 as wildcard), `d[10]` (30 values: q≤9, r∈{0,1,2}) and one
6-bit checksum. The 36 check bits reduce the accepted set to roughly `36^11 / 36 =
36^10 ≈ 3.66×10^15` checksum-valid spellings before semantic checks. There are
exactly three difficulty values (`d[10] % 3 ∈ {0,1,2}`), of which the published lists
cover only 0 and 2; **difficulty 1 (Medium) is the unadvertised dimension**.

**Validator-as-oracle check (§16.19).** The validator itself was used as the oracle
offline: decoding and re-encoding each published code reproduced 14 of 16 byte for
byte. In the emulator, a breakpoint at `0x080126E4` gave ground-truth accept/reject
and direct reads of the output struct.

**Novel codes (in no published list) and their in-game proof:**

1. **`WM5DR5H3MCMC`** — Level slot 2 (Asteroid Field) at **Medium** difficulty
   (`d[10] = 10`, `d[10] % 3 = 1`; published lists contain only Easy and Hard for
   this level). Entered on the real screen: accepted, level intro played. RAM at the
   accept breakpoint: `0x030014F0 = 0x02` (level), `0x03001510 = 0x01` (difficulty).
   The published Easy code `WM5DR5H3MCLB` gave `0x030014F0 = 0x02`,
   `0x03001510 = 0x00` at the same breakpoint — a controlled, byte-level proof that
   the minted code changes the difficulty field.
2. **`WM5DR5G3MCL0`** — **Level slot 1** (`d[6] = 1`), a slot no published code
   reaches (published codes start at `d[6] = 2`). Entered on the real screen:
   accepted, and it loaded a visibly different scene (Jimmy and Goddard outside the
   house in Retroville) instead of the Asteroid Field space intro.

**Bounds proven by rejection (in-game, `WRONG CODE` on the real screen):**

* `WM5DR5H3MCLC` — changes only the checksum symbol; rejected. Proves the
  `sum mod 36` check is live.
* `WM5DR5R3MCLL` — valid checksum and valid LCG structure but `d[6] = 10` (level
  slot 10, outside 1..9); rejected. Proves the level-range check is live.
* `51867F7MJ5Y2` — decoder-repaired last character of a bad published string but
  `d[6] = 28`; rejected. Proves a checksum-valid code still needs semantic validity.
* The 37th on-screen glyph (smiley) is not in the 36-symbol alphabet string and
  leaves a raw byte that cannot satisfy the checksum — it is therefore not a valid
  code symbol.

## 7. Validation evidence

* **Observed** (emulator screenshots / debugger reads): every screen listed in §3;
  acceptance of `WM5DR5H3MCLB`, `WM5DR5H3MCMC`, `WM5DR5G3MCL0`; `WRONG CODE` for
  the three rejection codes; breakpoint registers at `0x080126E4`
  (`r5 = 0x030014F0`, `r12 = 0x41C64E6D`, `r7 = 0x3039`); RAM bytes
  `0x03001510 = 0x01` (novel Medium) vs `0x00` (published Easy), with
  `0x030014F0 = 0x02` for both.
* **Derived** (disassembly): the entire validator algorithm, alphabet, checksum,
  LCG constants, field layout, range checks and return semantics; 14/16 published
  codes round-trip exactly; no code literals or index records exist in the ROM.
* **Inferred**: that `d[10] % 3` values 0/1/2 correspond to Easy/Medium/Hard — the
  mapping is consistent with the published Easy (0) / Hard (2) sets, the difficulty
  menu (Tutorial/Easy/Medium/Hard) and the new value 1, but no screenshot of a
  difficulty label inside the accepted level was captured because the level-intro
  cutscene does not advance under the test harness. That the two non-RT published
  strings come from a different revision or are multi-character typos is also
  inferred, not proven.

## 8. Unknowns

* Meaning of `d[1..5]`, `d[7]`, `d[8]` and the derived 10-bit field at `struct+0x16`
  and base-9 hash at `struct+0x12` (save-slot / world seed / score?) — they are not
  needed for acceptance and were left at published values when minting.
* The table-dependent alternative to `d[9] = 31` at `0x801265A` was not exercised;
  all accepted codes use the wildcard, so only that path is proven.
* The in-game effect of the Medium flag after the level intro (AI/enemy density)
  was not observed; only the RAM field is proven.
* `0x080202B4`'s base-37 hash is used by the multiplayer `<Random>` world path and
  was confirmed unrelated to passwords.
* No debug/build menu or button code was found; the string `not implemented yet`
  corresponds to the implemented `Return to Main` option in Options, not a hidden
  feature. Button-input spaces (all menus) were walked, but no exhaustive mask
  fuzzing was performed.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
* Python 3 + Capstone 5.0.7 for pointer/LDR/BL scans and the decoder/encoder;
  `arm-none-eabi-objdump -M force-thumb` for disassembly.
* `mGBA` (SDL) under `Xvfb :315` + `openbox`, driven with `xdotool` and `scrot`;
  screenshots cropped to the 720×480 GBA viewport.
* mGBA CLI debugger (`mgba -d`) with a FIFO command channel, `stdbuf -o0`, and a
  Thumb breakpoint at `0x080126E4` for RAM reads. Helper scripts created in
  `/tmp/opencode/jimmy/`: `phase0.py`, `xrefs.py`, `ldrscan.py`, `decode.py`,
  `encode.py`, `keys.py`, `goto_code.py`, `enter_code.py`.
* Web sources for published codes: GameFAQs (gamespot mirror), Freeola Retro Game
  Cheats, VGChartz search snippets. Fetched page content was treated strictly as
  data; no prompt-injection payload was encountered in the sources used.

No ROM image or copyrighted asset is redistributed here — only hashes, addresses,
algorithms and generated example codes.
