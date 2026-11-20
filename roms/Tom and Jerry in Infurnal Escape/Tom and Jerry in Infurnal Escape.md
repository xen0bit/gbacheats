# Tom and Jerry in Infurnal Escape (GBA) — Reverse Engineering Report

## 1. Target identity
- File: `Tom and Jerry in Infurnal Escape.gba` (4,194,304 bytes = 4 MiB)
- Header title: `TOM AND JER` (full header string `TOM AND JERRAIFE5L`), game code `AIFE`, maker `5L`, version `0x00`
- Header fixed byte `0x96` present; complement `0x85`; checksum `0x0000` (rebuilt-header artifact, per guide §16.1)
- Entry word `0xEA00002E` → stock `0x080000C0`, **not** a cracktro
- MD5 `c63ea91402e560b3ede1242884d72f73`
- SHA-1 `fc27897d063720867fb21e41fd6642218257a6fb`
- SHA-256 `b5a113e210a124021c2654953614526b766e238644a64cab161d13c79c5f5a7a`

## 2. Executive summary
The game has a genuine developer-intended **11-symbol password system** reached from the title menu via **Continue**. The on-screen keyboard has exactly **32 glyphs** (`1`–`9`, `B C D F G H J K L M N P Q R T X`, swirl, ♣, ◆, ♥, ☺, ★, ♠), i.e. **5 bits per symbol**. The password is *algorithmic*, not a lookup table: pack 11×5 bits → XOR with two constants → apply a 55-entry bit permutation → CRC-8 (poly `0x31`, init `0xFF`) → split into 12 payload fields plus the 8-bit checksum. The decoded fields are per-level progress percentages and two flags, written to IWRAM `0x03000910`.

I reimplemented the full decoder in Python and verified it against all 9 published codes. I minted three novel codes with field combinations absent from every published list, entered **NOVEL-A** (`♠ swirl L ☺ B P ◆ 9 9 Q ♠`) in the emulator, and confirmed acceptance with the exact novel progress values `[20,20,20,20,5,5,5,5]` in RAM. Bounds were proven by two rejections: a bad checksum (rejected) and an out-of-range field value `f6=11` with a *valid* checksum (rejected). No hidden/debug menu or button code was found; the negative is bounded below.

## 3. How to reproduce
1. `Xvfb :317 -screen 0 1024x768x24 &`, `export DISPLAY=:317 SDL_AUDIODRIVER=dummy`, `openbox &`.
2. `mgba -3 <rom>` (rename the binary to avoid other agents' `pkill -x mgba`). Window at `+154+184`, 720×480; crop with `convert -crop 720x480+154+184`.
3. Press `Return` through the legal splash, CineGroupe logo and title. Main menu: **New Game / Continue / Options** (`A`=`x`, `B`=`z`, `Start`=`Return`, `D-pad`=arrows).
4. Press `Down` to **Continue**, `A` → **Password** screen (11 slots). `Left/Right` selects a slot; `Up/Down` cycles its glyph (32-glyph wrap); `A` submits; `B` cancels.
5. Enter a code and press `A`. A valid code starts gameplay with the decoded progress; an invalid code leaves you on the Password screen.
6. Savestates: `Shift+F1..F9` save, `F1..F9` load. `.ssN` files are PNGs with a zlib `gbAs` chunk; `zlib.decompress` yields a 397,312-byte raw state. Password buffer at raw `0x190E8` (IWRAM `0x030000E8`), decoded fields at raw `0x19910`.

Published codes verified in the ROM (all accepted by my decoder): L2 `2C★♠♣3♣75T6`, L3 `433★XN◆8♥6G`, L4 `LCHHK3◆NXQ☺`, L5 `Q47JXM◆8~◆G`, L6 `2H5J♠1◆8~~G`, L7 `L7H4♥3◆8B~G`, L8 `2HHM♥M◆8B♣F`, L9 `1HH3♥3D8DXF`, plus the speedrun-community "all levels" code `1G◆♠HP♣4♠♥F`. (`~` = swirl.)

## 4. Address map
File offset → ROM address = `0x08000000 + offset`.

| Address (ROM or RAM) | Role |
|---|---|
| `0x080038A0` | 55-bit permutation engine; `r0=0` decode, `r0=1` encode |
| `0x0800394C` | Encoder (game-state → password), writes 11 symbols to `0x03000900` |
| `0x080039E4` | Decoder front end: pack 11×5 bits → XOR → permute |
| `0x08003A84` | Validator: field extraction, normalization, CRC compare, range checks, writes game state |
| `0x08013E34` | CRC-8 routine (poly `0x31`, init `0xFF`) |
| `0x08006524` / `0x080065FC` | Password-screen renderer / A-button submit handler (BL to `0x08003A84`) |
| `0x080067E4` / `0x08006828` | Glyph increment / decrement (wrap at 31) |
| `0x0829C56C` (file `0x29C56C`) | 55-byte bit-permutation table (a full permutation of 0..54) |
| `0x030000E8` | 11-byte raw password buffer (IWRAM) |
| `0x03000900` | 11-byte copied password |
| `0x03000930` / `0x03000934` | packed/XORed and permuted 64-bit words |
| `0x03000910..0x17` | 8 decoded per-level progress bytes |
| `0x03000920`, `0x03000940`, `0x03000944`, `0x03000948` | decoded level field, flags f10/f11, f0 |
| `0x0300078E`, `0x0300076B`, `0x03000790`, `0x03000794/5`, `0x030007A8`, `0x03000910` | gameplay RAM confirmed by published CodeBreaker codes (health, lives, weapons, bones, mice, timer, level table) |

## 5. Algorithm
Alphabet value `v` (0..31) → glyph: `1 2 3 4 5 6 7 8 9 B C D F G H J K L M N P Q R T X ~ ♣ ◆ ♥ ☺ ★ ♠` where `~`=swirl. (UI cycle order is the reverse-ish tile order `★ ☺ ♥ ◆ ♣ ~ X T R Q P N M L K J H G F D C B 9 8 7 6 5 4 3 2 1 ♠`; stored value = `(30 - cycle) mod 32`, proved by savestate diff: all-`1` → `00`, all-`★` → `1E`.)

Decode (symbol values `b[0..10]`):
```
w0 = b0<<27 | b1<<22 | b2<<17 | b3<<12 | b4<<7 | b5<<2 | ((b6>>3)&3)
w1 = (b6&7)<<29 | b7<<24 | b8<<19 | b9<<14 | b10<<9
w0 ^= 0xF1E2D3C4 ;  w1 ^= 0x781B2000
Q  = 64-bit value of (w0,w1); for i in 0..54: Q_out[i] = Q_in[PERM[i]]   # MSB-first stream
crc = crc8(bytes of Q with high word masked by 0xFFFC0000)              # poly 0x31, init 0xFF, no xorout
fields = extract MSB-first widths [4,4,5,5,5,5,4,4,4,4,1,1,8] from Q    # 54 bits; bit 54 unused
valid = (fields[12] == crc) and all range checks
```
Range checks: `f0,f1 <= 9`; `f2..f5 <= 30` (31 → sentinel `0xFF`); `f6..f9 <= 10` (11–14 rejected, 15 → sentinel `0xFF`); `f10,f11` are 1-bit flags. Valid payload bytes are copied to the game-state fields above; invalid ones become `0xFF`.

Encode is the exact inverse: build the 54-bit stream from fields with recomputed CRC, apply the inverse permutation, XOR, unpack to 11×5-bit symbols.

## 6. Tables
- **Alphabet (32 symbols)** and numeric mapping: see §5. `strings` finds **no** in-game text: all UI text is font/tile-index based, so ASCII scanning gives no hits for menu labels, debug words, or codes.
- **Published codes**: 8 level codes + 1 "all levels" code (§3), all validated by the decoder.
- **Decoded field meaning** (inferred from in-game RAM effects): `f0` and `f1` are small indices (published values 1..9); `f2..f9` are the 8 per-level progress values (camp levels ≤30, castle levels ≤10, `0xFF` = locked); `f10/f11` are flags. The "all levels" code decodes to `f0=3,f1=8,progress=[28,28,29,29,8,8,10,8],f10=0,f11=1`.

## 6b. Enumeration
- **Raw input space**: `32^11 = 36,028,797,018,963,968` (2^55) 11-symbol strings.
- **Effective space**: one CRC bit per payload, so `2^46` field combinations with range constraints. Counting allowed values per field (`f0,f1` 10 each; `f2..f5` 32 each incl. sentinel; `f6..f9` 12 each incl. sentinel; `f10,f11` 2 each) gives **8,697,605,529,600** checksum-valid, range-valid codes. Bit 54 of the permuted word is always zero and is an unused/alias bit.
- **Published set**: exactly 9 codes (GameFAQs/supercheats level codes + the speedrun "all levels" code). All 9 appear in no ROM literal table — they are algorithmically generated, confirming a generator-based system, not a hard-coded lookup.
- **Novel codes minted** (absent from every published list; generated by re-encoding modified fields and recomputing the CRC):
  - **NOVEL-A** — display `♠ swirl L ☺ B P ◆ 9 9 Q ♠`, cycle indices `31,5,13,1,21,10,3,22,22,9,31`, fields `[4,8,20,20,20,20,5,5,5,5,1,1]`, CRC `0x55`. **Entered in emulator and accepted.** Screenshot `novelA_after.png`; RAM after submit: `0x03000910 = 14 14 14 14 05 05 05 05 00 ff ff ff` (exactly the novel progress values), `0x03000920 = 08`, `0x03000948 = 04`, `0x03000940 = 01`, `0x03000944 = 01`. The game started a level with 4 lives and a 2:00 timer.
  - **NOVEL-B** — display `1 ★ H D ♥ R D 8 D ★ H`, fields `[5,8,30,29,30,30,10,10,10,10,1,0]` (maxed progress with unadvertised `f0=5` and `f10=1`), CRC `0xEB`.
  - **NOVEL-C** — display `Q 2 6 G ♣ B 7 ☺ 5 Q J`, fields `[4,1,15,15,15,15,5,5,5,5,0,1]`, CRC `0x08`.
- **Bounds proven by rejection** (each entered through the real on-screen keyboard):
  - Bad checksum: NOVEL-A with the last symbol changed `♠ → ♣` (stored CRC `0x55`, computed `0x95`) → **rejected**, screen stayed on Password.
  - Out-of-range field with *valid* CRC: `f6 = 11` (allowed 0..10 or sentinel 15), code `D K L ☺ 9 P D 9 B T ♠`, CRC valid → **rejected**, screen stayed on Password.
  - Sentinel semantics: `f6 = 15` with valid CRC → **accepted**, decoded to `0xFF` ("not applicable") — establishes 15 as a sentinel rather than an out-of-range value.

## 7. Validation evidence
- **Observed**: legal splash, CineGroupe logo, title, main menu (New Game / Continue / Options), Options (Music/SFX/Credits), Credits, Password screen, gameplay, pause menu (Resume / Select Level / Exit to Menu), level-select screen (levels 1..8, only those unlocked by progress are movable), and the two rejection outcomes — all via screenshots in `/tmp/opencode/tomjerry/`.
- **Observed (RAM)**: savestate diffs located the password buffer; the game's own decoded `Q` after entering the L2 code was `0x11F03FFFFFF2F400`, byte-for-byte equal to my decoder's output. Decoded field bytes for L2 and both novel codes matched the reimplementation exactly.
- **Derived**: validator, permutation, CRC and field layout from disassembly at `0x080038A0`/`0x080039E4`/`0x08003A84`/`0x08013E34`; all 9 published codes satisfy the reimplementation.
- **Inferred**: semantic names of `f0/f1` and flags (level index and progress state) from the in-game level-select gating and the decoded RAM layout; the exact meaning of `f11` beyond "all-levels flag" was not isolated.
- **Bounded negative**: no hidden/debug menu or button code. ASCII scan of the full 4 MiB returned **zero** occurrences of `password|cheat|debug|secret|hidden|level select|warps|invinc|godmode`; all UI text is font/tile-index based (verified by decoding the 32-symbol password glyph bank from the rendered keyboard), so ASCII absence is expected rather than conclusive by itself. A u16 button-mask scan (10 masks, all 100 ordered 2-press pairs, plus common combos `0x003/0x00C/0x300/0x30C/0x0F0/0x3FC/0x3FF`) found only isolated matches in code/compressed data — no clustered 3+-press table and no mask-sequence dispatcher. Every reachable screen from title → menu → Continue/Password/Options → gameplay → pause → level select was walked; no undocumented menu entry appeared. This is a bounded "no in-game button code / hidden menu" result, not "not tested".

## 8. Unknowns
- Semantic identity of `f0`, `f1`, `f10`, `f11` beyond their numeric behavior and the all-levels flag.
- Whether the unused permuted bit 54 is ever checked by some later code path (it is zero for all generated codes).
- The full font/tile text bank was not exhaustively rendered; the password glyph bank was decoded and the ASCII negative is supplemented by full screen enumeration, but a hypothetical unreferenced debug label in an unused tile bank cannot be excluded.
- Published labels "Level 2..9" are community labels; the decoded payload fields are the ground truth (guide §16.15).

## 9. Tooling
- `arm-none-eabi-objdump -M force-thumb` for ROM disassembly; Capstone for pointer scans.
- `python3` reimplementation `codec.py` / `mint.py` / `ss.py` in `/tmp/opencode/tomjerry/`.
- mGBA 0.10.5 under Xvfb `:317` with `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input; `scrot` + ImageMagick capture/crop; savestate `gbAs` zlib extraction for RAM reads.
- The mGBA GDB stub was unusable (port 2345 occupied by a concurrent agent); savestate diffing (guide §16.13) was used instead.
- No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms and self-generated codes are published.

## 10. Legal note
Only findings, addresses, hashes, algorithms and author-generated codes are recorded. No ROM bytes, extracted graphics, or game text assets are reproduced here.
