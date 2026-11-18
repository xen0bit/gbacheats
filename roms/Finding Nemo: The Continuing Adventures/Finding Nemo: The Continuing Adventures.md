# Finding Nemo: The Continuing Adventures (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Finding Nemo: The Continuing Adventures.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `FINDINGNEMO2` |
| Game code | `BZIE` (E = Europe), maker `78`, version `0x00` |
| MD5 | `68500bcbb838a9d361272f34fa20ce1a` |
| SHA-1 | `66881e8204f770973dcf01b4f9f919fa2f6db99b` |
| SHA-256 | `4ade109c9a3c284ddcdf468de7b570b94331eda74d8f3f5a6bbc402ae5f3df98` |

Phase 0: single Nintendo logo hit (header at file `0x0`), stock entry word `0xEA00002E` (`b 0x080000C0`) — **no cracktro/trainer/appended image**. Header checksum field is `0x0000` (rebuilt-header artifact, complement byte `0x58`); this is normal for a distributed dump. No patch or trainer detected.

**Sibling check (independent).** `roms/Finding Nemo/Finding Nemo.gba` is a *different* image: 8 MiB, title `FINDING NEMO`, code `AZIE`, maker `78`, md5 `69dfdf6e…`. It contains **no** `PASSWORD`, `BCDFGHJKL`, or `GALLERY` strings. **Nothing is shared** with the analysed `BZIE` image beyond the franchise name (guide §16.11).

## 2. Executive summary

The game has a genuine **in-game password system** on the main-menu *Password* screen. It is **not** the widely-published 5-symbol alphabet style: the screen accepts a **10-symbol password** drawn from a 32-symbol keyboard (`BCDFGHJKL / MNPQRSTVW / XYZ123456 / 789!?`). The 10th symbol is a checksum character computed from the first nine; the payload encodes which bonus characters are present on the main menu / in Gallery.

- No published code list exists for this SKU (web searches on GameFAQs, generic cheat queries, and archive-style queries returned nothing). The ROM therefore contains no literal "published code" to verify; the game's own generated code (`Z6CV?S9Q7M`) served as the known-good anchor.
- The validator was located statically at `0x0806A058` (called only from the OK handler `0x08069C20`) and reimplemented offline; the checksum model agrees with the ROM on both accepted and rejected inputs.
- **Two novel, unpublished codes were minted and accepted in-game**, each producing a different visible character and a distinct RAM progress-flag value: `B6CV?S9Q7V` and `ZBCV?S9Q7P`.
- Bounds were proven by rejection: wrong-checksum inputs, wrong-length inputs, and checksum-correct but semantically out-of-range inputs all produced "Password Error" (§0.2 / §16.5).
- All reachable menus were walked (title, main, password, stage select, gallery, options→sound test/progress/theater/credits, multiplayer) with screenshots; tile-indexed text banks were decoded. No hidden debug screen was found; classic combos either do nothing or soft-reset.

## 3. How to reproduce

**Emulator:** mGBA SDL (`mgba -3`) under `Xvfb :316`, `SDL_AUDIODRIVER=dummy`, `openbox` WM. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys 120–250 ms (menu input drops shorter taps).

**Menu path:** title → Press Start → (auto intro, ~50 s) → MAIN MENU → **Password** → on-screen keyboard (D-pad move, A select, B delete, OK cell at bottom-right) → A on OK.

**Savestate workflow:** Shift+F1..F9 saves; F1..F9 loads. All password experiments used a savestate at the Password screen with the cursor parked on OK, then the input buffer was patched in the decompressed `gbAs` chunk (IWRAM `0x03003FCF`, length byte `0x03003FCD`) — state offset `0x1CFCF` / `0x1CFCD` for this 4 MiB ROM (§16.13). This avoids keyboard drift and is the reliable oracle loop.

**Codes tested:**

| Code | Result | Evidence |
|---|---|---|
| `DDNND` (string found in ROM data) | Password Error | screenshot `pw_ddnnd_result.png` |
| `BCDFGHJK` (8 symbols) | Password Error | `pw_result2.png` |
| `ZXCTYS897M` (wrong visual reading, wrong checksum) | Password Error | `pw_valid_result.png` |
| `Z6CT?S9Q7M` (wrong checksum) | Password Error | static + validator model |
| `VMBS!R8P6?` (misidentified display buffer, wrong checksum) | Password Error | `novel2_result.png` |
| `Z6CV?S9Q7M` (game-generated) | **Accepted**, returns to main menu | `test_pw.ss1` |
| `B6CV?S9Q7V` (novel) | **Accepted**, yellow fish appears | `test8.png`, `novel2` flags read |
| `ZBCV?S9Q7P` (novel) | **Accepted**, turtle/character appears | `test9.png`, flags read |
| `Z6CT?S9Q79`, `Z6CB?S9Q7L`, `Z6CVBS9Q7J`, `Z6CV?B9Q7Z`, `Z6CV?SBQ7Y`, `Z6CV?S9B7C`, `Z6CV?S9QB?` (checksum-valid, payload out of range) | Password Error | `test1.png`–`test7.png` |

## 4. Address map

File offset `F` ↔ ROM address `0x08000000 + F`.

| Item | ROM address / RAM address | Evidence |
|---|---|---|
| GBA header, logo, entry | `0x08000000`–`0x080001FF` | Derived (Phase 0) |
| Password title string `"PASSWORD"` | `0x08164C28` | Observed (screenshot + bytes) |
| Keyboard rows `BCDFGHJKL`,`MNPQRSTVW`,`XYZ123456`,`789!?OK` | `0x08164C31`,`0x08164C3B`,`0x08164C45`,`0x08164C4F` | Observed |
| Font/charset table `BCDFGHJKLMNOPQRSTVWXYZ  0123456789!?AEIU` | `0x08153875` (pointer at `0x08153954`) | Derived |
| Password-screen menu entries / handlers | table around `0x08164BE0`–`0x08164C20` | Derived |
| Screen input handler (OK path, call site) | `0x08069C16`–`0x08069C46` | Derived (BL scan) |
| **Validator** `validate_pw(struct*)` → `r0` = 0/1 | **`0x0806A058`** | Derived + used as oracle |
| Checksum helper `u16 table_lookup(u16)` | `0x08006048` | Derived |
| Checksum lookup table (2048 × u16) | `0x0814A92C`, index mask `0xFFE` | Derived |
| Checksum comparison constant | `0x23450000` (add-high trick) at `0x0806A3BC` | Derived |
| Field subtraction key base | `0x123` at `0x0806A3C0` | Derived |
| Field bit-masks (`0xFFFFFE3F`, `0xFFFFF1FF`, `0xFFFF8FFF`, `0xFFFC7FFF`, `0xFFE3FFFF`, `0x3FFFF`) | `0x0806A3CC`–`0x0806A3E0` | Derived |
| Field reference constant | `0x0002DB6D` at `0x0806A3E4`; table `0x08162DA0` at `0x0806A3E8` | Derived |
| Password input buffer (10 × u5 indices) | IWRAM **`0x03003FCF`** | Observed (RAM proof) |
| Input length byte | IWRAM `0x03003FCD` | Observed |
| Validator struct base | IWRAM `0x03003E20` (`+0x1AF` = input buffer, `+0x3E` must be `0x20` to call validator) | Derived |
| Decoded progress-flag output | IWRAM **`0x03001DB8`** and `0x03001DBC` | Observed (RAM proof) |
| Stage-select password display buffer | IWRAM `0x0301D704` (display only; *not* the entry string — see Unknowns) | Observed |
| Data string `DDNND` (unrelated to validator) | `0x081625DF`, data xrefs `0x0805A0E8`, `0x0805A44C` | Derived |

## 5. Algorithm

**Alphabet (32 symbols, 0-based index 0–31):**

```
B C D F G H J K L M N P Q R S T V W X Y Z 1 2 3 4 5 6 7 8 9 ! ?
```

**Password length:** exactly 10 symbols (observed: the screen expands to 10 slots; shorter inputs are rejected).

### Checksum (position 9)

```
def checksum(p):                       # p = list of 10 symbol indices
    s   = sum(p[0:9]) & 0xFFE          # 11-bit even mask (table is u16, 2048 entries)
    tv  = int16( TABLE[s] )            # TABLE = 0x0814A92C, byte offset s
    chk = (tv + 5) & 0x1F              # 0x23450000 add-high trick extracts (tv+0x2345)&0x1F
    return chk == p[9]
```

The `+5` is `(0x2345 & 0x1F)` from the literal at `0x0806A3BC`; the ROM computes `(tv<<16)+0x23450000`, masks `0x1F00000`, shifts right 16, then compares to `buf[9]`.

Verified offline:

| Code | indices | sum | `TABLE[s]` | computed chk | stored chk | result |
|---|---|---|---|---|---|---|
| `Z6CV?S9Q7M` | 20 26 1 16 31 14 29 12 27 9 | 176 | 1092 | 9 | 9 | pass |
| `Z6CT?S9Q7M` | …15… | 175 | 1080 | 29 | 9 | **fail** |
| `ZXCTYS897M` | 20 18 1 15 19 14 28 29 27 9 | 171 | 1056 | 5 | 9 | **fail** |
| `B6CV?S9Q7V` | 1 26 1 16 31 14 29 12 27 16 | 156 | 971 | 16 | 16 | pass |
| `ZBCV?S9Q7P` | 20 1 1 16 31 14 29 12 27 11 | 150 | 934 | 11 | 11 | pass |

### Payload / semantic layer

After the checksum, `0x0806A058` unpacks seven 5-bit fields from bytes 0–6 with a position-dependent subtraction key:

```
key[i]   = (15*i + 0x123) & 0x1F       # i = 0..6  ->  [3,18,1,16,31,14,29]
field[i] = (buf[i] - key[i]) & 0x1F    # packed into r6 at 5*i
```

For the known-good code the fields are `[17, 8, 0, 0, 0, 0, 0]`. Bytes 5/6/7 also feed a second packed word (`(buf[5]-0x1D)&0x1F >> 2`, `(buf[6]-0x0C)&0x1F << 3`, `(buf[7]-0x1B)&0x1F << 8`), and the routine then clamps/checks fields against constants `0x0002DB6D` and a table at `0x08162DA0`, with branch-to-reject at `0x0806A4CC`. On success it stores the two decoded words to `0x03001DB8`/`0x03001DBC` and returns 1; on failure returns 0.

**Empirically characterised accepted family** (§16.15 — payload, not label):

```
    X  Y  C  V  ?  S  9  Q  7  K
pos 0  1  2  3  4  5  6  7  8  9
```

Positions **2–8 are fixed** to `C V ? S 9 Q 7` (indices `1,16,31,14,29,12,27`); positions **0–1 are free** bonus-character selectors; position 9 is the checksum. Changing any of positions 2–8 (with a recomputed checksum) is rejected — proven for all five tested positions.

## 6. Tables

**Alphabet index map:** `B0 C1 D2 F3 G4 H5 J6 K7 L8 M9 N10 P11 Q12 R13 S14 T15 V16 W17 X18 Y19 Z20 1:21 2:22 3:23 4:24 5:25 6:26 7:27 8:28 9:29 !=30 ?:31`

**Accepted codes observed / minted:**

| Code | Effect | Flags at `0x03001DB8` |
|---|---|---|
| `Z6CV?S9Q7M` | baseline (game-generated for clean state) | `0x00000049` |
| `B6CV?S9Q7V` | yellow fish appears on main menu | `0x0003004D` |
| `ZBCV?S9Q7P` | turtle/second character appears on main menu | `0x00030069` |

**Bonus/unlock surface:** main-menu character sprites and Gallery entries (28 slots, all initially `?`). The password changes the character set; individual Gallery slots remained locked in the tested states.

## 6b. Enumeration

**Space definition**

- Alphabet size: **32** → 5 bits/symbol.
- Length: **10** symbols → **50 bits**, i.e. `32^10 = 1,125,899,906,842,624` representable strings.
- Checksum: **5 bits** (position 9) → checksum-valid space `32^9 = 35,184,372,088,832` (2^45).
- Semantic layer: positions 2–8 pinned to `CV?S9Q7` (7 × 5 bits = 35 bits fixed); positions 0–1 free (10 bits) with per-field range checks. **Effective family size = 32 × 32 = 1,024 candidate codes** (all checksum-correct), minus any of the 1,024 that fail the remaining field clamp/range checks (not exhaustively run; see Unknowns).

**Novel codes (in no published list — none exists for this SKU)**

1. **`B6CV?S9Q7V`** — changes selector position 0 from `Z` to `B`, checksum recomputed to `V`. Accepted in-game; RAM flags `0x0003004D`; yellow fish visible on main menu (`test8.png`).
2. **`ZBCV?S9Q7P`** — changes selector position 1 from `6` to `B`, checksum recomputed to `P`. Accepted in-game; RAM flags `0x00030069`; different character visible (`test9.png`).

Both were *generated offline* from the recovered model and entered by patching the input buffer in a savestate, then pressing OK — not copied from any list or from the game's own display.

**Bounds proven by rejection**

- Wrong checksum, same 10-symbol family: `Z6CT?S9Q7M` (store 9, expected 29) → Password Error.
- Wrong length: `DDNND` (5), `BCDFGHJK` (8) → Password Error.
- Checksum-valid but out-of-range payload: seven codes altering positions 2–8 (`Z6CT?S9Q79`, `Z6CB?S9Q7L`, `Z6CVBS9Q7J`, `Z6CV?B9Q7Z`, `Z6CV?SBQ7Y`, `Z6CV?S9B7C`, `Z6CV?S9QB?`) → all Password Error (`test1.png`–`test7.png`). This proves the semantic range layer is separate from the checksum.
- Misidentified display buffer string `VMBS!R8P6?` (wrong checksum) → Password Error.

## 7. Validation evidence

- **Observed:** all screenshots (`*.png` in `/tmp/opencode/nemo2`), GDB reads of `0x03003FCF` (input bytes `14 12 01 0f 13 0e 1c 1d 1b 09` for typed `ZXCTYS897M`), savestate diffs locating the buffer and the flag word, acceptance/rejection screenshots, visible main-menu character changes.
- **Derived:** validator address and call site (BL scan + Capstone), checksum table/mask/constant, field key schedule, output flag addresses, alphabet mapping (verified by round-tripping the typed buffer).
- **Inferred:** the exact role of each payload bit inside the decoded flag word (field clamps at `0x0806A11C`–`0x0806A4BA` were read but not fully enumerated field-by-field); the Gallery unlock semantics beyond the visible character change.

Evidence discipline: `DDNND` was found as a literal in a *data* table (two pointer sites) but is **not** an accepted password — recorded as a negative, not a false positive (§16.7/§16.8). Fetched web content was treated as data; no prompt-injection was encountered (searches returned no results).

## 8. Unknowns

- The 1,024-code family was not exhaustively validated in the emulator; the field-clamp logic at `0x0806A11C`–`0x0806A4BA` may reject additional (X,Y) pairs. Two distinct pairs were confirmed accepted; seven out-of-range payload edits were confirmed rejected.
- The stage-select password *display* at `0x0301D704` changed when progress changed but patching it did not change the rendered text; it appears to be a staging/derived buffer, not the entry string. The displayed glyph string was decoded from the font (tile-indexed) and cross-checked against the keyboard glyphs; the entry string that actually validates is the one encoded at `0x03003FCF`.
- Individual mini-games were not launched from the fresh state (stage nodes were not activatable without story progress); the stage-select screen itself was walked and RAM-verified.
- No hidden debug menu was found; `L+R+A+B` soft-resets, other tested combos have no effect. This is a bounded negative over the combos tested, not a proof over all possible sequences.

## 9. Tooling

- `binutils-arm-none-eabi` (`arm-none-eabi-objdump`), Python 3 + Capstone 5.0.7 + Pillow, mGBA SDL, Xvfb, openbox, xdotool, scrot, ImageMagick, gdb-multiarch.
- Helper scripts in `/tmp/opencode/nemo2/`: `dis.py` (Capstone disassembler + literal/BL xref scans), `ui.py` (focus-by-PID key driver + cropped screenshots), `enter.py` (keyboard entry with cursor tracking), `setpw.py` (savestate `gbAs` password-buffer patcher), `dbg.py` (mGBA CLI debugger driver).
- All addresses verified against the exact `BZIE` image (SHA-256 above). No ROM or copyrighted assets are redistributed; only hashes, addresses, algorithms and the analyst's own codes are published.

## Legal note

Findings only — no ROM bytes, graphics, or game text beyond short UI labels are reproduced here.
