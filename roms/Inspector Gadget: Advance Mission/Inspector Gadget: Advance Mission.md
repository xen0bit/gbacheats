# Inspector Gadget: Advance Mission (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Inspector Gadget: Advance Mission/Inspector Gadget: Advance Mission.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `INSPECTOR GA` |
| Game code / maker | `AIGE` / `6U` (USA, revision 00) |
| Version / fixed / main unit / device | 0 / 0x96 / 0 / 0 |
| Header checksum / complement | 0x0000 / 0x51 (computed complement 0x6A — header rebuilt, per §16.1) |
| Entry word | 0xEA000030 (stock branch, not a cracktro) |
| Embedded GBA headers | Exactly one (Nintendo logo scan: only offset 0) — no multi-game pack, no appended trainer |
| MD5 | `881dd5c2d845a8fef7fc7badcf47d617` |
| SHA-1 | `86d4f46980afd3a4627fb204910d36d592684c49` |
| SHA-256 | `36e6ae3a320c5487f6911e40eb6fc7587dc8ca797e01ecba87493c52c81d7052` |

## 2. Executive summary

The game has a **7-symbol password system** on the main menu (`New game / Tutorial / Game link / Password / Options`). It is a genuine algorithmic code system, not a lookup table: the 11 published level passwords are simply 11 points in a much larger space.

The 32-symbol keyboard alphabet is `0123456789BCDFGHJKLMNPQRSTVWXZ/*` (no vowels, no Y; `/` and `*`). Each symbol is a 5-bit index; the 7 symbols are packed MSB-first into 35 bits. An affine XOR bit-permutation (ROM `0x082796B0`) transforms the 5 packed bytes; a 5-bit checksum derived from the first four transformed bytes is compared with 5 bits at offset 30 of the transformed buffer. A 16-bit level field `N = get_bits(16, t, 0)` must satisfy `N <= 0xCE3F` (52,799 = 11·6·20·2·20 − 1), then is decomposed into five mixed-radix fields that set world/level and starting resources.

All 11 published codes were verified against the ROM and accepted in the emulator. Three **unpublished, minted codes** (`NT*5MSJ`, `QP*RMKG`, `**QRM94`) were generated with the offline decoder/encoder; the first two were typed on the real password screen and produced distinct in-game states. Bounds were proven by in-game rejection of a wrong-checksum code and by the game validator rejecting a checksum-valid but out-of-range code.

The published "hold L at start menu, press A B Up Down A Left Right → access to everything" code produced no effect (it simply selected New game) and its key-mask sequence does not exist in the ROM in any of four encodings — it is an unverified/bogus published code. No hidden debug menu was reachable; the debug-like strings in the decompressed text bank are level-intro labels with no separate screen.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 SDL, `SDL_AUDIODRIVER=dummy`, Xvfb `:317`, 3× scale.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
* Path: wait for title "Press Start to continue" (~8–10 s of emulation), press Start, select **Password** (4th item), press A.
* The keypad is a 4×8 grid: `0 1 2 3 4 5 6 7 / 8 9 B C D F G H / J K L M N P Q R / S T V W X Z / *`. D-pad moves the cursor; A commits the highlighted symbol; B deletes. The bottom row shows 7 slots; the leftmost glyph is a live preview of the highlighted key.
* Seven committed symbols are auto-submitted. Valid codes start the level; invalid codes show **"Incorrect password"** at the bottom of the screen.
* Savestates: Shift+F1..F3 save slot 1..3; F1..F3 load (worked in this build). Slot 1 was saved at the empty password screen.
* Entering a code in-game: for each symbol, navigate from the previous cursor position and press A. Scripts in `/tmp/inspectorgadget/`.

### Codes tested

* Published (all accepted): `*7*MM14`, `*3HML14`, `R3*3M64`, `R7H3L64`, `*CH3L24`, `*H*3M24`, `R5*3MR4`, `*3RM33P`, `RHRM37P`, `RC7M27P`, `*9R33XP`.
  * Note: published list writes `*3HMLI4` with an `I`; the ROM alphabet has no `I` and the game's validator accepts `*3HML14` (digit `1`). This is a published transcription error (§16.7).
* Novel (minted, absent from every published list): `NT*5MSJ` (fields 2,1,0,1,0 — In the Statue, 0 hearts/0 lives), `QP*RMKG` (12,3,7,2,15 — Egypt: The Great Pyramid with 3 hearts/15 lives), `**QRM94` (5,2,3,1,6 — validator-verified only).
* Rejected: `NT*4MSJ` (single-symbol change from `NT*5MSJ`, bad checksum → in-game "Incorrect password"); `59T2T1G` (checksum valid, N=0xE825 > 0xCE3F → validator returns 0).

## 4. Address map

| Address | Meaning |
|---|---|
| ROM `0x08289D18` | 32-byte input alphabet: `0123456789BCDFGHJKLMNPQRSTVWXZ/*` (then 4 zero bytes and the word 11 at `0x08289D3C`) |
| ROM `0x08289D3C` | Mixed-radix divisor table `[11, 6, 20, 2, 20]` for level-field decomposition |
| ROM `0x08278F00` | Password screen handler (input, D-pad grid, display) |
| ROM `0x082790FC` | `BL` to validator; `r0 = sp+12` (7-byte input buffer) |
| ROM `0x08279948` | **Validator**: char→index, 7×5-bit pack, transform, checksum, range check, field decode; returns 1 on accept, 0 on reject |
| ROM `0x082796B0` | Affine XOR bit transform on the 5 packed bytes |
| ROM `0x08271F6C` / `0x0827203C` | Bit writer / bit reader (big-endian bitstream, byte-swapped 32-bit words) |
| ROM `0x08280AA0` / `0x08280A28` | Unsigned division / modulo helpers |
| RAM `0x03007E7C` | 7-byte input buffer on the stack (state-file offset `0x20E7C`); blank slots are `_` (0x5F) |
| RAM `0x0200084E`+ | Decompressed ASCII text bank (menus, level names, "Incorrect password", debug-looking labels) |
| RAM `0x030027AC` | Decoded field `a + 2` (level/world index, published range 2..12) |
| RAM `0x03002AF8..AFB` | Decoded fields `b+1`, `c`, `d?1:2`, `e` |
| RAM `0x03002AF6` (u16) | Decoded 14-bit field from transformed bits 16..29 |

File-offset ↔ ROM-address mapping: `rom_address = 0x08000000 + file_offset`. Savestate `gbAs` chunk is zlib-compressed; its raw layout (397,312 bytes) maps IWRAM at state `0x19000` → `0x03000000`, EWRAM at state `0x21000` → `0x02000000`.

## 5. Algorithm

```
ALPHA = "0123456789BCDFGHJKLMNPQRSTVWXZ/*"      # 32 symbols
decode(code):
  idx[i] = ALPHA.index(code[i])   for i=0..6
  bitstr = concat( format(idx[i], '05b') )      # 35 bits, symbol 0 first
  packed = int(bitstr + "00000", 2).to_bytes(5,'big')
  t = AFFINE_TRANSFORM(packed)                  # 40-bit affine XOR map, 0x082796B0
  full = t + b'\x00\x00\x00'
  x  = t[0]^t[1]^t[2]^(t[3] & 0xFC)^0xB3
  x ^= (x & 0xAA) >> 1
  calc = (x & 0x1F) ^ (x >> 3)
  expected = get_bits(5, full, 30)              # exact bit reader at 0x0827203C
  if calc != expected: REJECT
  N = get_bits(16, full, 0)
  if N > 0xCE3F: REJECT                         # 52,799 = 11*6*20*2*20 - 1
  a = N % 11;  b = (N//11) % 6;  c = (N//66) % 20
  d = (N//1320) % 2;  e = (N//2640) % 20
  start_game(fields=(a+2, b+1, c, 1 if d==0 else 2, e))
  ACCEPT
```

`get_bits(n, buf, off)` is the ROM routine at `0x0827203C`: it loads two 32-bit words at `(off>>5)*4`, applies `bswap(ror(word,16))` to each, concatenates with shifts `off&31` and `32-(off&31)`, then shifts right by `32-n`. The affine transform's 40-bit matrix and base (0xD6223D48E0) were recovered by probing the ROM function bit-by-bit in the debugger; the full offline reimplementation was in `/tmp/inspectorgadget/{transform,bits,model}.py` and reproduces all 11 published codes and all tested rejects.

## 6. Tables

### Alphabet (keypad order, index 0..31)
`0 1 2 3 4 5 6 7 8 9 B C D F G H J K L M N P Q R S T V W X Z / *`

### Published codes, decoded

| Code | N | fields (a,b,c,d,e) | Level |
|---|---|---|---|
| `*7*MM14` | 0x6896 | (2, 5, 5, 1, 10) | Statue of Liberty — In the Statue |
| `*3HML14` | 0x6897 | (3, 5, 5, 1, 10) | Statue of Liberty — The Flame of Liberty |
| `R3*3M64` | 0x6898 | (4, 5, 5, 1, 10) | The Tower — The Tower Keeps Watch |
| `R7H3L64` | 0x6899 | (5, 5, 5, 1, 10) | The Tower — The Lift |
| `*CH3L24` | 0x689A | (6, 5, 5, 1, 10) | The Tower — Higher Than Anything |
| `*H*3M24` | 0x689B | (7, 5, 5, 1, 10) | The Great Wall — At the Foot |
| `R5*3MR4` | 0x689C | (8, 5, 5, 1, 10) | The Great Wall — On the Great Wall |
| `*3RM33P` | 0x689D | (9, 5, 5, 1, 10) | Big Ben — The Palace |
| `RHRM37P` | 0x689E | (10, 5, 5, 1, 10) | Big Ben — The Top |
| `RC7M27P` | 0x689F | (11, 5, 5, 1, 10) | Egypt — The Valley of Kings |
| `*9R33XP` | 0x68A0 | (12, 5, 5, 1, 10) | Egypt — The Great Pyramid |

Every published code has identical fields except `a`; the published list covers only the 11 consecutive N values 0x6896..0x68A0 out of 52,800 permitted N values.

## 6b. Enumeration

**Space definition.** 7 symbols × 5 bits = 35 bits → 32^7 = 34,359,738,368 possible strings. The packed 35-bit value is zero-padded to 40 bits and mapped bijectively by the affine transform. Acceptance requires (a) a 5-bit checksum match (≈1/32 of inputs) and (b) `N = get_bits(16,t,0) <= 0xCE3F` (52,800/65,536 ≈ 0.805 of the remainder). Expected accepted codes ≈ 2^35 / 32 × 52,800/65,536 ≈ **8.6 × 10^8**. The reachable level state is exactly the mixed-radix product 11 × 6 × 20 × 2 × 20 = 52,800 combinations of (a,b,c,d,e).

**Novel codes (not in any published list).**

| Code | fields | Verified | Effect |
|---|---|---|---|
| `NT*5MSJ` | (2,1,0,1,0), N=0x0000 | game validator = 1; typed on real password screen | "Statue of Liberty — In the Statue", 0 hearts, 0 lives |
| `QP*RMKG` | (12,3,7,2,15), N=0xA1C6 | game validator = 1; typed on real password screen | "Egypt — The Great Pyramid", 3 hearts, 15 lives |
| `**QRM94` | (5,2,3,1,6), N=0x3EB4 | game validator = 1 | unadvertised resource combination (validator-level proof) |

Generated by inverting the 40×40 GF(2) transform matrix and solving the 5-bit checksum constraint (`encode.py`). The field combination (b,c,d,e) differs from every published code, which all use (5,5,1,10).

**Bounds proven by rejection.**

* Checksum: `NT*4MSJ` (one symbol changed from `NT*5MSJ`) → game displays **"Incorrect password"** and resets the keypad.
* Range: `59T2T1G` has a correct checksum but N=0xE825 (>0xCE3F); the ROM validator called from the debugger returns 0, proving the range gate is separate from the checksum.
* Alphabet: symbols outside the 32-key alphabet (e.g. `A`, `E`, `I`, `O`, `U`, `Y`, `.`) are not on the keypad and cannot be entered through the UI.

## 7. Validation evidence

**Observed (emulator/screenshots/RAM):**
* Title, main menu, password keypad, options (Music/Sound/Credits), level-intro screen, and "Incorrect password" message all captured on screen; full screenshots retained in `/tmp/inspectorgadget/`.
* Input buffer at `0x03007E7C` observed changing from `30 5f 5f...` to `31 32 33 34 20 5f 5f` after entering `1234` (savestate diff, state offsets `0x20E7C`).
* All 11 published passwords accepted in-game (`*7*MM14` → Statue of Liberty: In the Statue).
* Novel `NT*5MSJ` and `QP*RMKG` accepted in-game with visibly different starting hearts/lives; `NT*4MSJ` rejected with on-screen "Incorrect password".
* Debugger call of the validator at `0x08279948` with `r0` pointing at a 7-byte ASCII buffer returned 1 for all published and novel codes, 0 for wrong-checksum and out-of-range inputs; RAM writes at `0x030027AC` etc. confirmed the decoded fields.
* Options menu has exactly three entries (cursor wraps after Credits); no 4th hidden entry.

**Derived (disassembly/oracle):**
* Validator algorithm, transform matrix, checksum formula, bit reader semantics, mixed-radix field layout, alphabet table address, and field-divisor table — all reimplemented offline and cross-checked against the ROM function and every published code.
* Rebuilt-header signal from complement byte mismatch.

**Inferred (not fully exercised):**
* Mapping of fields (c,d,e) to specific in-game pickups/resources is inferred from the differing level-intro numbers (hearts/lives) and the text-bank labels; the exact game-side reader of each field was not individually breakpointed.
* The exact effect of the 14-bit field at `0x03002AF6` was not traced.

## 8. Unknowns

* No hidden/debug menu was found. The decompressed text bank contains debug-like strings (`World:`, `Level:`, `% life:`, `Number of lives:`, `Pieces:`, `Precious objects:`, `Treasures:`, `Music: YES/NO`, `Sound: YES/NO`), but a bounded search found no reachable screen displaying them as a menu, and the Options screen has only 3 items. Pointers to `Level:` at `0x082618F4` etc. are literal pools in level-intro drawing code, not a debug dispatch table.
* The published L-held button code could not be enabled: entering `A,B,Up,Down,A,Left,Right` at the main menu while holding L simply selected New game; the corresponding key-mask sequence (and L-prefixed variant) is absent from the ROM in little-endian u16, big-endian u16, and one-byte-per-press encodings (searched exhaustively). If it applies to a different screen or a different ROM revision, that screen was not identified.
* Game-link and Tutorial screens were navigated but contained no code entry or unlock surfaces; pause-menu text exists in the bank but the pause screen was not captured in this session.
* No collectible/unlock code system beyond the password level select was found in the 196 ASCII strings of the decompressed text bank (`cheat`, `debug`, `secret`, `unlock`, `generator`, `level select` each occur 0 times; `password` 2, both the menu label and the error message).

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` for ROM disassembly; Capstone 5.0.7 / Keystone available.
* mGBA 0.10.5 SDL under Xvfb `:317` + Openbox; `xdotool` XTEST input; `scrot` + ImageMagick for screenshots.
* mGBA `-d` command-line debugger bridged over a local TCP socket (`dbgsrv2.py`) for register/memory writes and oracle calls: set `r0` = buffer address, `lr` = trapped Thumb address `0x0828A001`, `cpsr` T-bit, `pc` = function address, `c`, then read `r0`.
* Savestate `gbAs` chunk parsed with Python `zlib` for RAM/VRAM reads and diffs (`state.py`).
* Analysis scripts in `/tmp/inspectorgadget/`: `game.py`, `enter.py`, `state.py`, `dbg2.py`, `oracle.py`, `callfn.py`, `transform.py`, `bits.py`, `model.py`, `encode.py`, `verify.py`, `explore.py`, `menuwalk.py`.
* No ROM or copyrighted assets are redistributed; only addresses, algorithms, hashes and tool scripts are published.

### Cleanup

All processes started for this job were stopped by explicit PID: Xvfb `:317`, Openbox, the ordinary mGBA instances, the mGBA `-d` debugger instances, and both debugger bridge servers. Generated `.sav`, `.ss1`, `.ss2` and `.ss3` files in the ROM folder were removed. `roms/INDEX.md` was not modified.
