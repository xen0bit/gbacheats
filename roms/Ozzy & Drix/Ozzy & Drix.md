# Ozzy & Drix (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ozzy & Drix/Ozzy & Drix.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `OZZY&DRIX` (offset 0xA0) |
| Game code | `BOZE` (full header string `BOZE5D`), region `E` (USA) |
| Version / complement / checksum | `0x00` / `0xEF` / `0x0000` |
| Entry word | `0xEA00002E` → stock `b 0x080000C0` (not patched) |
| MD5 | `dfae85cbb4e9825bee214ff73ca9bbaa` |
| SHA-1 | `11491a5298ccad1cbc75749a5187525c73af5a1d` |
| SHA-256 | `a420ee02383d1a50055c23a494c57131502cbb45b29feab6ba999dff9f9f7b8e` |
| Embedded headers | exactly one Nintendo logo hit, at file `0x4`; no trainer, no cracktro, no multiboot stub |

Identity note (§16.1/§16.11): this is the retail USA Raylight/Midway GBA SKU. 3rd party cheat indexes say "Raylight Studios" while `file(1)` labels the maker `5D`; the code under analysis is the only header in the image.

## 2. Executive summary

The game has a genuine developer-intended **password system** on the **RESUME GAME** entry of the main menu (the screen literally reads `ENTER PASSWORD`, 5 slots). It is algorithmic, not a lookup table — none of the published code strings appear literally in the ROM.

The code is **5 characters** from a 32-symbol alphabet `BCDFGHJKLMNPQRSTVWXYZ0123456789?`. The first four characters carry a 20-bit packed word split into six fields (widths 4/4/4/2/3/3 at bit offsets 0/4/8/12/14/17); the fifth character is a 5-bit running-sum checksum. The validator accepts iff `|field1 - field3| == field5` (and the two range checks pass), then writes `field1` and `field3` into two RAM progress bytes at `0x020001AC` and `0x020001B0`, jumping the player to the corresponding scene/ending. Fields 0, 2 and 4 are ignored by the validator (free filler), so every meaningful `(field1, field3)` pair has 512 spellings.

The whole space is characterised: **1,048,576** checksum-valid 5-character strings, of which **40,960** are accepted (80 meaningful pairs × 512 filler aliases). All four published codes were verified in the ROM and emulator, and five codes absent from every published list were minted, entered on the real screen, and RAM-verified. Bounds were proven by an in-game `WRONG PASSWORD` on a bad checksum and by rejection of an out-of-range field with a correct checksum.

No button-code sequence, hidden debug menu or other unlockable code surface was found; the process table and string bank were enumerated and bounded (§7).

## 3. How to reproduce

Emulator: `mgba -3 -g <rom>` under `Xvfb :318` (my own display), `SDL_AUDIODRIVER=dummy`, window focused with `xdotool windowfocus`. Default keymap: A = `x`, B = `z`, Start = `Return`, D-pad = arrow keys, L = `a`, R = `s`.

Exact path: **title ("Press Start") → Start → MAIN MENU → RESUME GAME → ENTER PASSWORD**. The 5 slots are filled by Up/Down (cycle the 32 symbols), Left/Right (move slot), A (`x`) submits, B (`z`) deletes/back. Because RAM via GDB was unreliable, RAM reads were taken from mGBA `.ssN` savestates: decompress the `gbAs` PNG chunk; the state is 397,312 bytes with IWRAM at state `0x19000` and EWRAM at state `0x21000` (§16.13).

Codes tested on this screen (all entered with real button presses):

| Code | Origin | Decoded (f1,f3) | RAM after submit | Result |
|---|---|---|---|---|
| `Y3WF?` | 3rd party cheat indexes comment (gallery/all characters) | (1,8) | `P+0x18=01`, `P+0x1C=08`, `P+0x1D=00` | accepted → all-character gallery / ending |
| `WMVBN` | 3rd party cheat indexes, labelled "Level 1" | (3,2) | `P+0x18=03`, `P+0x1C=02` | accepted |
| `NXVBQ` | 3rd party cheat indexes, labelled "Level 2" | (4,2) | `P+0x18=04`, `P+0x1C=02` | accepted |
| `RNBC3` | 3rd party cheat indexes, labelled "Level 3" | (4,3) | `P+0x18=04`, `P+0x1C=03` | accepted |
| `YPWBT` | **novel, minted here** | (7,2) | `P+0x18=07`, `P+0x1C=02` | accepted → different boss scene |
| `V3WF7` | **novel filler alias** | (1,8) | `P+0x18=01`, `P+0x1C=08` | accepted, same effect as `Y3WF?` |
| `BLBBL` | **novel, min boundary** | (0,1) | `P+0x18=00`, `P+0x1C=01` | accepted |
| `T7R7Z` | **novel** | (8,1) | `P+0x18=08`, `P+0x1C=01` | accepted |
| `?GS7R` | **novel, max boundary** | (9,1) | `P+0x18=09`, `P+0x1C=01` | accepted |
| `Y3WFB` | bad checksum (last char changed) | — | unchanged (`02`,`01`) | `WRONG PASSWORD` on screen |
| `F9WF0` | correct checksum, `field1` raw = 12 (out of range) | — | unchanged (`02`,`01`) | rejected |

3rd party cheat indexes also lists 7 codes for `AGB-BOZE-USA`; those are GameShark/Cheat-device memory patches, out of scope for this engagement, and were not tested as in-game codes.

## 4. Address map

All addresses are ROM (`0x08...`) or RAM (`0x02...`, `0x03...`); file offset = ROM address − `0x08000000`.

| Address | Meaning |
|---|---|
| `0x0802FE7C`–`0x0802FFD8` | UI ASCII text bank (`ENTER PASSWORD`, `PASSWORD ALLOWED!`, `WRONG PASSWORD`, `LEVEL`, `SCENE`, …) |
| `0x08799A78` | string-pointer table (pointers at `0x08799AE4`–`0x08799B00` are the password strings) |
| `0x0802FB28`–`0x0802FE40` | process descriptor array, 16 records of 0x2C bytes (`name[16]`, self-ptr, init, main, handler, …) |
| `0x0802FD8C` | `PasswordProcess` descriptor; code pointers `0x0800E398` (init) and `0x0800E628` (frame handler) |
| `0x0800E398` | password screen init (builds field table, seeds UI) |
| `0x0800E628` | password screen frame handler; at `0x0800E69A` copies 5 input bytes, `BL 0x0800E2F8`, on success writes flags and returns to game |
| `0x0800E2F8` | **main validator**: reads fields 1/3/5, checks `abs(f1-f3)==f5`, writes `P+0x18`, `P+0x1C`, `P+0x1D`; returns 1/0 |
| `0x0800E200` | **generator**: seeds fields from `P+0x18`/`P+0x1C`, random filler for 0/2/4, builds a code |
| `0x08022D94` | field-table initialiser `(state, defs, 6, 5)` |
| `0x08022DF8` / `0x08022E80` | field set / field get (bit-packing with `+min`, max bound) |
| `0x08022EE8` | build 5-char code from packed word; appends checksum and NUL |
| `0x08022F48` | checksum validator (char→value via `0x0801D9F0`, sum of first 4 = last, value ≤ 31) |
| `0x0801D9F0` | index of a character in the alphabet string (returns 32 if not found → rejected) |
| `0x0804D40C` | alphabet string, NUL-terminated, 32 symbols |
| `0x08799BF0` | field-definition table, 6 × 12 bytes `{key, min, max}` |
| `0x0879FD84` | pointer to the alphabet string |
| `0x02000194` (`P`) | progress/state struct; `+0x18` = f1, `+0x1C` = f3, `+0x1D` = 0 on accept |
| `0x020111FC` | 5-byte typed password buffer (`0x2A` = empty slot) |
| `0x0200043C` | main-menu selector (wraps 3→0) |
| `0x03006B80` (`T`) | password codec state: `+0` defs, `+4` bit-width table, `+8` count=6, `+12` packed word, `+16` last index=4, `+20` buffer |
| `0x030005C3C` | pointer to UI input object (object + 32 = typed buffer) |

## 5. Algorithm

```
alphabet A = "BCDFGHJKLMNPQRSTVWXYZ0123456789?"      # 32 symbols, index 0..31
value(c)   = index of c in A                         # 0x0801D9F0

# Fields (key, min, max, width, bit offset) from 0x08799BF0 + width helper 0x0801D878:
#   key0: min 57, max 72, 4 bits @0
#   key1: min  0, max  9, 4 bits @4
#   key5: min  0, max  9, 4 bits @8
#   key2: min108, max111, 2 bits @12
#   key3: min  1, max  8, 3 bits @14
#   key4: min 72, max 79, 3 bits @17

pack(vals):  w = OR over fields of ((val[key]-min) << offset)          # 0x08022DF8
build(w):    c[i] = A[(w >> (5*i)) & 31] for i=0..3                    # 0x08022EE8
             c[4] = A[(sum(value(c[i]) for i=0..3)) & 31]
             return c[0..4] + NUL

validate(code):                                                       # 0x08022F48 + 0x0800E2F8
    if any value(c[i]) > 31 for i in 0..4: reject
    if value(c[4]) != (sum(value(c[0..3])) & 31): reject               # WRONG PASSWORD
    w = OR over i=0..3 of (value(c[i]) << (5*i))
    f[k] = ((w >> off_k) & ((1<<width_k)-1)) + min_k for each field
    if f[1] > 9 or f[5] > 9: reject        # get_field returns -1 on bound failure
    if abs(f[1]-f[3]) != f[5]: reject
    P[0x18] = f[1]; P[0x1C] = f[3]; P[0x1D] = 0
    return ACCEPT
```

The generator (`0x0800E200`) is the exact inverse for the meaningful fields: `f1 = (i8)P[0x18]`, `f3 = (u8)P[0x1C]`, `f5 = |f1-f3|`; `f0`, `f2`, `f4` are pseudo-random filler (the `0x0801D85C` RNG calls at `0x0800E276`/`0x0800E28E`/`0x0800E2B4`). This is why multiple spellings decode to the same `(f1,f3)`: the validator never reads fields 0, 2 or 4.

Reimplementation: `codec.py` in the work dir `/tmp/ozzydrix/` matches the ROM on every published code, every generated code and both rejection classes.

## 6. Tables

**Alphabet** (`0x0804D40C`), index = 5-bit value:

```
0:B 1:C 2:D 3:F 4:G 5:H 6:J 7:K 8:L 9:M 10:N 11:P 12:Q 13:R 14:S 15:T
16:V 17:W 18:X 19:Y 20:Z 21:0 22:1 23:2 24:3 25:4 26:5 27:6 28:7 29:8 30:9 31:?
```

**Field layout** (see §5): widths 4,4,4,2,3,3 = 20 bits, packed into characters 0–3; character 4 is the checksum.

**Published code payloads** (decoded, not trusting the printed labels — §16.15):

| Code | f0 | f1 | f5 | f2 | f3 | f4 | Published effect | RAM effect |
|---|---|---|---|---|---|---|---|---|
| `Y3WF?` | 60 | 1 | 7 | 108 | 8 | 72 | gallery/all characters | `P+0x18=1, P+0x1C=8` |
| `WMVBN` | 58 | 3 | 1 | 108 | 2 | 72 | "Level 1" | `3, 2` |
| `NXVBQ` | 67 | 4 | 2 | 108 | 2 | 72 | "Level 2" | `4, 2` |
| `RNBC3` | 70 | 4 | 1 | 108 | 3 | 72 | "Level 3" | `4, 3` |

The 3rd party cheat indexes "Level n" labels do not equal either field directly; the payloads above are the ground truth. `Y3WF?` (f3=8, the largest published scene field) jumps to the all-character gallery/ending, which is why the 3rd party cheat indexes comment describes it as an all-characters unlock.

## 6b. Enumeration

**Space definition.** Raw 5-character strings over 32 symbols: `32^5 = 33,554,432`. Checksum-valid strings: `32^4 = 1,048,576` (the last character is determined by the first four). Across the 20 payload bits, the field ranges restrict acceptance:

* `f1` (4 raw bits) must be ≤ 9 — raw 10..15 fail the get-field max bound;
* `f5` (4 raw bits) must be ≤ 9 — same bound;
* `f3` (3 bits, min 1, max 8) always in range; `f0`, `f2`, `f4` always in range;
* validator constraint `abs(f1-f3) == f5`, with `f1 ∈ [0,9]`, `f3 ∈ [1,8]` → `f5 ∈ [0,8]`, always representable.

**Validator run over the whole space** (the Python model, cross-checked against the ROM on 11 inputs): exactly **40,960** accepted codes = **80** valid `(f1,f3)` pairs × **512** filler spellings each. Every pair has exactly 512 spellings; no reserved-bit holes inside the 20-bit payload. This turns "I found 4 published codes" into an exact count.

**Novel codes (absent from 3rd party cheat indexes or any wiki), all entered on the real RESUME GAME screen and RAM-verified:**

| Code | f1 | f3 | RAM after entry | Effect |
|---|---|---|---|---|
| `YPWBT` | 7 | 2 | `P+0x18=07`, `P+0x1C=02` | different boss scene (observed on screen) |
| `V3WF7` | 1 | 8 | `01`, `08` | alias of published `Y3WF?` — proves filler bits are unused by the validator |
| `BLBBL` | 0 | 1 | `00`, `01` | minimum boundary |
| `T7R7Z` | 8 | 1 | `08`, `01` | mid-range |
| `?GS7R` | 9 | 1 | `09`, `01` | maximum boundary |

**Bounds proven by rejection:**

* `Y3WFB` — same first four symbols as the published code but wrong checksum character `B`; on screen: `WRONG PASSWORD` (captured); `P+0x18/P+0x1C` remained `02/01`.
* `F9WF0` — checksum recomputed correctly for its first four symbols (so it passes `0x08022F48`) but the 4-bit `field1` raw is 12, above the max of 9; the game rejected it and left `P` unchanged. This isolates the *semantic range layer* from the checksum layer (§16.5).

**Button codes / hidden menus:** no key-mask sequence, cheat dispatcher or debug process exists. The 16-entry process table at `0x0802FB28` was enumerated: Agblogo, Intro, Race, Platform, GotoNext, Mainmenu, Gallery, PlatBossL3, Options, Credits, Continue, Stats, ML, CutScene, Password, StartScene, MouthBoss — all normal gameplay/UI. A case-insensitive scan of all 34,559 strings for `debug|cheat|code|secret|unlock|hidden|test|level|edit` found only gameplay dialogue and `Levels/Text Editing`, which is a **credits-roll category** at file `0x4C210`, not a debug menu. The UI text bank is plain ASCII at `0x0802FE7C`–`0x0802FFD8` (34 strings), so no font/tile-indexed text bank needed decoding before concluding the negative (§11).

## 7. Validation evidence

**Observed (emulator / savestate RAM):**
* Title → main menu (4 entries, selector `0x0200043C` wraps 3→0) → each entry walked: START GAME → Tonsils cutscene; GALLERY → 3D model viewer (L/R rotate, arrows cycle, locked = single Ozzy model); OPTIONS → MUSIC YES/NO, FX YES/NO, CREDITS, EXIT; RESUME GAME → `ENTER PASSWORD`.
* Entering `Y3WF?` on that screen: typed buffer `Y3WF?`, then `P+0x18=01`, `P+0x1C=08`, `P+0x1D=00` in state RAM, followed by the all-character gallery, ending dialogue and credits.
* The four 3rd party cheat index codes and five novel codes produced exactly the `P` bytes predicted by the model; the two bad inputs produced `WRONG PASSWORD` / no state change.
* The full options and gallery screens, the post-password gallery/ending and the credits roll were walked visually.

**Derived (static disassembly):**
* Alphabet, field table, bit packing, checksum, validator constraint and flag writes, from `0x0801D9F0`, `0x08022D94`, `0x08022DF8`, `0x08022E80`, `0x08022EE8`, `0x08022F48`, `0x0800E2F8`, `0x0800E200`.
* The 40,960-code enumeration is the model run over the entire 20-bit payload; the model agrees with the ROM on 11/11 tested inputs.

**Inferred (not fully exercised):**
* The semantic names of `P+0x18` / `P+0x1C` ("scene" / "level") are suggested by the adjacent `LEVEL` and `SCENE` strings in the password UI bank and by the observed scene jumps, but the exact in-game level numbering used by the credits/dialogue was not exhaustively mapped for all 80 pairs.
* The generator at `0x0800E200` fills fields 0/2/4 with values derived from an RNG; only its inverse structure was verified, not the RNG seed sequence.

## 8. Unknowns

* Whether the two decoded bytes have any persistent save-memory effect beyond the immediate scene jump (the cart uses battery save; a long-term progression experiment was not run).
* Exact human-facing names/numbering of the 80 `(f1,f3)` scene pairs — only the 11 tested pairs were observed on screen.
* No hidden debug screen was found, but absence can only be bounded to the enumerated process table and ASCII string bank; a screen baked entirely into bitmap art without any text or process record would evade this search (none was seen on any walked screen).

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, GNU `strings -t x` (34,559 strings), `grep -abo`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly; Capstone 5.0.7 + Keystone available.
* `Xvfb :318`, `openbox`, `mgba -3 -g`, `xdotool`, `scrot`, ImageMagick (`convert`, `compare`).
* `/tmp/ozzydrix/codec.py` — Python codec (pack/unpack/encode/decode) and full-space enumeration.
* `/tmp/ozzydrix/helper.py`, `test_codes.py` — xdotool input driver and savestate-RAM reader (zlib-decompress mGBA `gbAs` chunk).
* Web: 3rd party cheat index cheats page via `web.archive.org/web/20150920021750/http://www.gamefaqs.com/gba/914926-ozzy-and-drix/cheats` (3 passwords) and the 3rd party cheat indexes comment (`Y3WF?`); 3rd party cheat indexes checked. Fetched pages were treated as data; no prompt-injection payload was encountered in this run.

**Legal note:** no ROM, extracted graphic, music or game asset is redistributed here — only addresses, algorithms, hashes and self-authored code are published.
