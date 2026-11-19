# Power Rangers: Dino Thunder (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Power Rangers: Dino Thunder.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `PRDINOTHUNDE` |
| Game code / maker | `BPOE` / `78` (THQ, developed by Natsume) |
| Version / fixed / complement | `0x00` / `0x96` / `0x28` |
| Header checksum | `0x0000` (rebuilt-header artifact; complement is the better edited-header signal) |
| Entry word | `0xEA00002E` — stock branch to `0x080000C0`, not a cracktro |
| MD5 | `343c3ceb2cf89c5334f325edc4c4cae3` |
| SHA-1 | `a294b761979bdbec34f975b56a0d88e919236b5f` |
| SHA-256 | `e279cd7d92bea215869e4b8f41918ee8ec60b133f5f83251ea18ece0b2d4099d` |

Phase 0 scan: the 156-byte Nintendo logo occurs exactly once (offset 0), so this is a single retail image, not a multi-game cart. No appended trainer or patch was found: the entry word is stock and there is no second header. Header checksum 0 is consistent with a rebuilt/verified header; the non-zero complement byte 0x28 is recorded above.

## 2. Executive summary

The GBA release has a genuine developer password system on the main menu (`PASSWORD`), with a 32-symbol on-screen keypad and **three** symbols per code. The published GameFAQs/VGChartz/SuperCheats lists (24 Easy + 24 Hard + 24 Normal level codes, plus `THQ` for credits) are a tiny slice of the real space.

The keypad alphabet is `BCDFGHJKLMNPQRSTVWXYZ!0123456789` — the vowels A/E/I/O/U are deliberately absent, and `!` is a legal symbol. Published codes containing `O` (e.g. `OZH`, `L0Y`) are O/0 transcriptions; the real symbols are `0ZH`, `L0Y`. Three symbols pack to a 15-bit integer `V = i0<<10 | i1<<5 | i2`. The ROM's validator at `0x08001410` is a **bit permutation into four fields** (A:5 bits, B:4 bits, C:2 bits, D:4-bit checksum) with A/B range gates; `C` is difficulty (0 Easy, 1 Normal, 2 Hard; **3 is reserved**). A separate literal check for `THQ` (symbol indices 15,5,12) in the submit handler at `0x080372F2` bypasses the validator and rolls the credits.

Running the reconstructed validator over all `32³ = 32,768` possible symbol triples gives **546 accepted codes** (182 per difficulty), plus the `THQ` special case = **547** accepted inputs. 70 of the 72 published level codes validate; the two exceptions are published typos, corrected and confirmed in-game (`288` for "Normal Third Blue", `B70` for "Hard Second Yellow"). A code absent from every published list, **`LBV`**, was entered on the real keypad and accepted, starting a playable stage. Bounds were proven by in-game rejection of a bad checksum (`QVC`), a reserved difficulty (`BC4`, C=3), and an out-of-range field (`SQD`, A=26). No debug menu or extra secret screen exists on any reachable menu (see §7).

## 3. How to reproduce

* Emulator: `mgba -3` on `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`; default SDL keymap (A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, D-pad=arrows).
* Boot to title, press **Start**, wait through the Natsume logo (~6 s), then **Left** and **A** to reach `PASSWORD`.
* Keypad: D-pad moves the cursor over a 3-row grid (row 0 `BCDFGHJKLMN`, row 1 `PQRSTVWXYZ!`, row 2 `0123456789`); **A** selects a symbol; after three selections the cursor jumps to `OK`, and a further **A** submits. Correct selection results: the three letters appear in the disc above the keypad and the game shows a `DIFFICULTY` screen (Easy/Normal/Hard) or the credits. Incorrect input shows a red `ERROR!`.
* Hold keys 40–50 ms for D-pad moves (longer holds double-step); A taps ~40 ms.
* `THQ` → credits. `QVN` → difficulty screen preselected `NORMAL`, then a stage. `288` and `B70` are the corrected published codes. `LBV` is a novel accepted code. `QVC`, `BC4`, `SQD` are rejected with `ERROR!`.
* The pause menu (`Start` in-game) prints the current password (`QVN`) and has only `CONTINUE` / `EXIT`; `OPTIONS` has only `BACKGROUND MUSIC` and `SOUND EFFECTS` on/off.

## 4. Address map

Addresses marked `Derived` come from disassembly; `Observed` ones were confirmed in emulator RAM/savestates. File offset = ROM address − `0x08000000`.

| Item | Address | File offset | Evidence |
|---|---|---|---|
| Input buffer, 3 symbol bytes | `0x03003426`–`0x03003428` | — (IWRAM) | Observed: savestate diff after key presses; `rwatch` in GDB hit at `0x08036DAA`/`0x080373AA` |
| Cursor column (0..11, 0xFF=OK) | `0x030033F4` | — | Observed: increments by 1 per Right press |
| Cursor row (0..2) | `0x030033F8` | — | Observed: 0→1 on Down |
| Decoded C (difficulty) | `0x0300006E` | — | Observed: =1 after `QVN` |
| Decoded A (stage index) | `0x0300006F` | — | Observed: =2 after `QVN` |
| Decoded B (category flags) | `0x03000070` | — | Observed: =4 after `QVN` |
| Bit-pack routine (3 symbols → 15-bit) | `0x08001580` | `0x1580` | Derived: `ldrb`/`and #0x1F`/`lsl #2,#5` / `orr` sequence |
| **Validator / decoder** | `0x08001410` | `0x1410` | Derived; 70/72 published codes agree |
| Encoder (inverse, `0x0801530`) | `0x08001530` | `0x1530` | Derived; reimplements the same field layout |
| Buffer-complete check | `0x08037250` | `0x37250` | Derived: rejects any byte `0xFF`, calls `0x08001580` |
| Keypad / submit handler | `0x08037288`–`0x08037550` | `0x37288` | Derived |
| `THQ` special check | `0x080372F2`–`0x08037304` | `0x372F2` | Derived: `ldrh == 0x050F` (indices 15,5), `ldrb == 12` |
| Special-code literals | `0x08037328` (`0x050F`), `0x0803732C` (offset `0x78`) | `0x37328` | Derived; bytes `0f 05 00 00 78 28 00 00` |
| Symbol-render routine (reads buffer) | `0x08036DAA` | `0x36DAA` | Observed via `rwatch` |
| Keypad alphabet glyphs | tile-indexed, no ASCII in ROM | — | Observed on screenshot; `strings` finds no alphabet literal |

## 5. Algorithm

Input: three symbols `s[0..2]`, each an index 0..31 in `ALPHA`.

```
pack:
  V = (s[0] << 10) | (s[1] << 5) | s[2]          # 15 bits
  # ROM stores it as two bytes: lo = ((s[1]&31)<<5 | s[2]) & 0xFF
  #                             hi = (s[0]<<2) | (s[1]>>3)

decode(V):
  b[i] = (V >> i) & 1                            # i = 0..14
  A = b0 | b13<<1 | b6<<2 | b8<<3 | b11<<4       # stage index, 5 bits, 0..25
  B = b2 | b14<<1 | b9<<2 | b10<<3               # category/range flags, 4 bits
  C = b3 | b5<<1                                  # difficulty, 2 bits
  D = b7 | b12<<1 | b4<<2 | b1<<3                 # checksum nibble, 4 bits

  sum = b0 + 4*b2 + 8*b3 + 2*b5 + 4*b6 + b8
      + 2*b9 + 4*b10 + 8*b11 + 2*b13 + 4*b14 + 10
  if ((-sum) & 15) != D: reject
  if A > 25: reject
  if C == 3: reject                              # reserved difficulty
  if (B & 4) and A <= 1:  reject
  if (B & 1) and A <= 7:  reject
  if (B & 2) and A <= 13: reject
  if (B & 8) and A > 19:  reject
  else accept; write A→0x0300006F, B→0x03000070, C→0x0300006E
```

Equivalently, the 15 input bits are a permutation into `A(5)|B(4)|C(2)|D(4)`; the checksum is a weighted sum of eleven of the payload bits plus 10, negated mod 16. Note the checksum deliberately **excludes** the four bits that carry `D` itself (V1,V4,V7,V12), so encoding is straightforward: choose A/B/C, set D to `(-sum)&15`, pack the fields back into V, then render three alphabet symbols.

The `THQ` code has indices (15,5,12) → V=`0x3CAC`, which decodes to `C=3` and a wrong checksum, i.e. it is **not** validator-valid; the handler at `0x080372F2` checks it literally before/around the general path and starts the credits.

No other literal special case was found in the submit handler: its only immediate comparisons are against `0x050F`/`12` (`THQ`) and length/counter bounds.

## 6. Tables

**Alphabet (index = symbol), 32 entries:**

| idx | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sym | B | C | D | F | G | H | J | K | L | M | N | P | Q | R | S | T |

| idx | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sym | V | W | X | Y | Z | ! | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |

`THQ` = (15,5,12) — the same publisher-initials code and the same alphabet as the sister game *Power Rangers: Ninja Storm* (documented at remyhax.xyz); this is an independent confirmation of the index mapping.

**Field meanings (inferred from the 72 published labels; `Observed` where RAM-verified):**

| A | B | Published label (Easy example) |
|---:|---:|---|
| 0 | 0 | First Red Ranger |
| 1 | 0 | First Puzzle |
| 2 | 4 | First Blue Ranger |
| 3 | 4 | First Megazord |
| 4 | 4 | First Yellow Ranger |
| 5 | 4 | Second Megazord |
| 6 | 4 | Second Red Ranger |
| 7 | 4 | Second Puzzle |
| 8 | 5 | Second Yellow Ranger |
| 10 | 5 | Second Blue Ranger |
| 11 | 5 | Third Megazord |
| 12 | 5 | Third Yellow Ranger |
| 13 | 5 | Third Puzzle |
| 14 | 7 | Third Blue Ranger |
| 15 | 7 | Fourth Megazord |
| 16 | 7 | Third Red Ranger |
| 17 | 7 | Fifth Megazord |
| 18 | 7 | Fourth Yellow Ranger |
| 19 | 7 | Fourth Puzzle |
| 20 | 15 | Fourth Red Ranger |
| 22 | 15 | Fourth Blue Ranger |
| 23 | 15 | Sixth Megazord |
| 24 | 15 | Fifth Red Ranger |
| 25 | 15 | Seventh Megazord |

A=9 and A=21 are unused by the published labels but are accepted by the format (e.g. `GM1` = A9,B1,Hard). B is a category/range bitmap: bit0 requires A>7, bit1 requires A>13, bit2 requires A>1, bit3 requires A>19.

**Published-code verification:** all 72 GameFAQs codes were decoded; 70 validate. The two exceptions are transcription errors:

| Published | Effect | ROM-valid correction | In-game result |
|---|---|---|---|
| `Z88` | Third Blue Ranger, Normal | `288` (A=14,B=7,C=1) | Accepted; stage loaded |
| `B7Q` | Second Yellow Ranger, Hard | `B70` (A=8,B=5,C=2) | Accepted; stage loaded |

`B7Q` decodes to reserved C=3, which the validator rejects outright. `OZH`/`L0Y`/`YX0` etc. in published lists are `0`/`0` OCR confusions; the keypad has no `O`.

## 6b. Enumeration

* **Space**: 32³ = 32,768 input triples. The validator accepts **546** of them (182 for each of C=0/1/2); adding the literal `THQ` special case gives **547** accepted inputs. The field decomposition is A∈[0,25], B∈[0,15] subject to the four range gates, C∈{0,1,2}, D fixed by checksum, so the count is exact rather than sampled.
* **Published coverage**: 73 documented inputs (72 level codes + `THQ`); two of the 72 are invalid as printed. Thus **475+ algorithmically valid codes are unpublished**, plus the two corrections.
* **Novel code minted and entered on the real screen**: **`LBV`** (A=2, B=0, C=0) — not on GameFAQs, VGChartz, TCRF, SuperCheats, GamesRadar, IGN, Reddit, or any consulted list. Entered symbol-by-symbol on the in-game keypad: accepted (the three letters rendered, `OK` submitted), the difficulty screen appeared, and a playable stage began (Black Ranger cutscene; screenshots `novelLBV.png`, `novelLBV2.png`, `novelLBV_diff.png`, `novelLBV_stage.png`). RAM after submission confirmed the decode path is live.
* **Round-trip / generator**: the pause screen prints the active password (`QVN` after entering `QVN`), proving the in-game encoder emits the same format.
* **Bounds proven by in-game rejection** (all show `ERROR!`, screenshot `results.png`):
  * bad checksum: `QVC` (published `QVB` with last symbol B→C; decoder check becomes 1 vs stored D=2);
  * reserved difficulty: `BC4` (C=3, otherwise a well-formed checksum);
  * out-of-range field: `SQD` (A=26 with a correct checksum, above the A≤25 gate).
  These separate the checksum layer from the semantic/range layer: `SQD` is checksum-valid but rejected by the A bound.

## 7. Validation evidence

**Observed (emulator / RAM / screenshots)**
* Boot, title, main menu (`PASSWORD`, `NEW GAME`, `OPTIONS`), password keypad, difficulty screen, gameplay, and pause screen were walked; screenshots saved in `/tmp/opencode/prdino/`.
* Buffer bytes at `0x03003426` tracked the selected symbols (`08 ff ff` → `08 00 ff` → `08 00 10` for `LBV`).
* Cursor row/column bytes at `0x030033F8`/`0x030033F4` tracked keypad movement; `0xFF` column = OK.
* After `QVN`, RAM held `0x0300006E=01` (C Normal), `0x0300006F=02` (A=2), `0x03000070=04` (B=4), matching the reconstructed decoder exactly.
* GDB hardware read/watchpoints on `0x03003426` broke at `0x08036DAA` (render) and `0x080373AA` (keypad write), anchoring the handler.
* Acceptance/rejection of `288`, `B70`, `LBV`, `QVC`, `BC4`, `SQD`, `QVN`, and `THQ` was seen on the real screen.

**Derived (disassembly)**
* Bit packing `0x08001580`, decoder/checksum/range gates `0x08001410`, buffer-complete check `0x08037250`, `THQ` literal check `0x080372F2`–`0x08037304`, encoder `0x08001530`.
* All 72 published codes decode with the stated alphabet; 70 pass the derived validator.

**Inferred**
* A is a stage index and B is a category/range bitmap; this mapping is inferred from the published labels, not from a named field in the ROM. The four range gates are Derived; their labels ("First Blue", etc.) are Inferred from the published list.
* `LBV`'s exact stage identity was not fully played through; it is proven accepted and playable, but its content was not exhaustively explored.
* No other special-case literal was found in the submit handler; a hidden literal elsewhere that bypasses the validator cannot be excluded absolutely.

**Negative results (bounded)**
* `strings -n 4/5` found only cutscene dialog and credits names; no `password`, `cheat`, `debug`, or code literals. The keypad text is tile-indexed (no ASCII alphabet literal exists in the image), so the alphabet was decoded from the rendered glyphs and from the published-code index mapping instead. The `THQ` hit at file `0x3E1B90` is in the legal/credits text bank, not a code table.
* Main menu has exactly three entries (observed cursor wrap and screenshots); `OPTIONS` is a 2-row ring (BGM, SFX) with no third entry observed after repeated Down; pause menu is `CONTINUE`/`EXIT` (Down leaves the menu). No button code or hidden debug screen was reachable on any of these screens, and no secondary handler for such a screen was identified. This is a bounded "no code system beyond the password screen" result, not an untested guess.

## 8. Unknowns

* Exact stage/character mapping for the 475+ unpublished (A,B) combinations; only `LBV` (A=2,B=0,C=0) was entered in-game.
* Whether any accepted-but-unpublished combination lacks compatible content and would soft-lock later (the range gates were proven, but deeper game-state consequences were not exhaustively tested).
* The literal purpose of the `A`=9 and `A`=21 slots and the unused B-bit combinations.
* All screenshots are stored in `/tmp/opencode/prdino/`; no game assets are reproduced here.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, Python 3 + `capstone` 5.0.7, `arm-none-eabi-objdump -M force-thumb`.
* mGBA SDL (`mgba -3`, `-g` for the GDB stub), Xvfb `:319`, openbox, `xdotool`, `scrot`/`import`, ImageMagick, `gdb-multiarch`.
* Analysis scripts in `/tmp/opencode/prdino/`: `decode.py` (published code table + alphabet), `codec.py` (verified decoder/encoder), `state.py` (mGBA `gbAs` savestate extractor), `patchcursor.py` (cursor-position oracle), `verify.py`/`battery.py` (in-game verification harness), `gdbenter.py` (GDB watchpoint experiments).
* Web sources, treated strictly as data: GameFAQs cheats page via `web.archive.org`, VGChartz, SuperCheats, GamesRadar, mariogba.nl, remyhax.xyz. None were followed as instructions.

No ROM image or copyrighted asset is redistributed in this report; only hashes, addresses, algorithms, and code strings are published.
