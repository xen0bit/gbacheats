# Soccer Kid (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Soccer Kid.gba` (4,194,304 bytes / 4 MiB) |
| Header title | `SOCCER KID  ` (padded) |
| Game code | `AK6E5M` |
| Maker | `5M` (Telegames) |
| Revision | 0x00 (Rev.00) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0) |
| Header checksum | `0xD100`, complement `0x00` |
| MD5 | `dedc14eac17a4bb6e043f09d5b793f99` |
| SHA-1 | `4e7dc4d47ef064131990fe3ebb340edeaed321ef` |
| SHA-256 | `6cd7023afe76ca57e2d6ddb08c38a6151f46fb23d9d063ad08502806862abafe` |

`file(1)` identifies it as a normal retail USA/Europe GBA image. No cracktro/trainer
prefix; first 4 KiB are standard ARM crt0. Analysis used a byte-identical copy in
the work dir so no emulator artifacts were created next to the ROM.

## 2. Executive summary

This GBA build has **two in-game/developer-intended cheat surfaces**, both fully
enumerated:

1. **A 12-character password system** on the title screen's PASSWORD menu. It is
   algorithmic, not a lookup table: 8 characters carry a 32-bit payload `W`, the
   last 4 carry a 16-bit checksum `fold(W)`. `W` is XOR-obfuscated with the constant
   `0x3EDFACB7` to give the game-state payload `P`. The alphabet is the 16 symbols
   `BCDFGHJKLMNPQRST` (4 bits/character). I reversed both the validator
   (`0x0801C290`) and the in-game generator (`0x0801BD80`), reimplemented them
   bit-for-bit, verified all 16 published 12-character codes, **minted a novel code
   absent from every published list (`MKCMRSSGHGKG`), entered it through the real
   UI and confirmed every decoded field in live RAM**. Exact accepted-space count:
   **4,294,967,295 codes** (2³²−1) out of 2⁴⁸ possible strings; the single rejected
   `W` is `W=0` ⇒ `BBBBBBBBBBBB` (the `fold(W) != 0` guard). Rejection bounds were
   proven in-game for a bad checksum, for `fold(W)==0`, and for an out-of-range
   stage field.

2. **A developer test menu on the normal OPTIONS screen** — `TEST FX 01..26` and
   `TEST MUSIC 01..22` (plus `SOUND FX`/`MUSIC` toggles and `EXIT`). It needs no
   cheat device or button code: title → OPTIONS. Every value was enumerated by
   driving the real UI and reading the EWRAM text buffers.

The published title-screen button codes on GameFAQs belong to the **SNES, 3DO and
Jaguar** SKUs (uniform colours = Jaguar; invincibility/credits/sound-test = SNES;
level select = 3DO). None of their button-mask sequences exist in this GBA image,
and L/R and the 3DO sequence produced no visible effect on the GBA title screen.
This is a **bounded negative for controller-code systems on this SKU**.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 SDL under Xvfb, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Default keymap verified: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=
  `BackSpace`, D-pad = arrow keys. Hold keys ~70–120 ms (150 ms can double-step).
* Boot: legal screens (~7 s) → intro globe → title (~11 s). Title menu:
  START / PASSWORD / OPTIONS.
* **Password entry:** title → Down → PASSWORD → A. The selector starts at EXIT
  (cursor=0 at IWRAM `0x0201F4AA`); Down moves to character 1, Down again to the
  START row (cursor=13). Left/Right move the cursor; **A decrements** the current
  symbol, **B increments** it (both wrap mod 16). The 12 symbols are drawn from
  `BCDFGHJKLMNPQRST`, initially all `B`. Press A on the START row to submit.
  Valid codes advance to the world map; invalid ones show `INVALID CODE`.
* **Test menu:** title → Down, Down → OPTIONS → A. Down twice to `TEST FX`,
  once more to `TEST MUSIC`; Left/Right cycle the 2-digit value.
* Savestate slots 1–9 (Shift+F*n* saves, F*n* loads) were used to keep each test
  deterministic; all evidence files were kept in `/tmp/soccerkid/`.

## 4. Address map

### File offset ↔ ROM address
`ROM = 0x08000000 + file_offset`. GBA flat 4 MiB image, no bank switching.

### Identity / data banks

| Item | File offset | ROM address | Notes |
|---|---:|---:|---|
| Alphabet string `BCDFGHJKLMNPQRST` | `0x2D88E4` | `0x082D88E4` | 16 bytes, NUL at `0x2D88F4`; copied to EWRAM `0x0201F440` |
| `ENTER PASSWORD` | `0x2D88F8` | `0x082D88F8` | |
| `INVALID CODE` | `0x2D8912` | `0x082D8912` | message id 17 |
| `TEST FX    01` | `0x2D8C5C` | `0x082D8C5C` | |
| `TEST MUSIC 01` | `0x2D8C6C` | `0x082D8C6C` | |
| `CREDITS 0` | `0x2D8CA4` | `0x082D8CA4` | no xref found; probably end-credit string, not an option |

### Code

| Item | Address | Evidence |
|---|---:|---|
| Password generator | `0x0801BD80` | Derived: builds W, XORs `0x3EDFACB7`, emits 8+4 chars |
| Password-screen init | `0x0801BF68` | Fills display buffer with `0x42`, index buffer with 0 |
| Password input handler | `0x0801C14C` | Cursor/char editing; alphabet EWRAM table |
| **Password validator** | `0x0801C290` | Derived + live-verified |
| Options handler | `0x0801EB80` | Menu dispatch, cases at `0x0801EC58` |
| Option-display formatter | `0x0801ED0C` | `(byte+1)` → two ASCII digits |
| XOR key constant | literal at `0x0801C3C0` / `0x0801BF34` | `0x3EDFACB7` |

### RAM (observed, savestate diff + game writes)

| Address | Content |
|---|---|
| `0x0201F440` | 16-byte alphabet copy (`BCDFGHJKLMNPQRST`) |
| `0x0201F4A4` | global 32-bit `W` (raw entered / then decoded `P`) |
| `0x0201F4A8` | global 16-bit checksum word |
| `0x03003ED0` | 12 ASCII display characters (`B`×12 initially) |
| `0x03003EE2` | 12 alphabet indices (0..15) |
| `0x0201F4AA` | 16-bit menu cursor (0=EXIT, 1..12=chars, 13=START) |
| `0x0201F7B8` | EWRAM copy of `TEST FX    01` string; digits at `+11/+12` |
| `0x0201F7C8` | EWRAM copy of `TEST MUSIC 01` string |
| `0x030040CC` / `0x030040CE` | signed bytes: TEST FX value / TEST MUSIC value (0-based) |
| `0x03002810 + 0x70C` | continues |
| `0x03002810 + 0x70D` | difficulty: `0`=hard, `0xFF`=easy |
| `0x03002810 + 0x70E` | lives |
| `0x03002810 + 0x70F` | `((P>>24)&3 + 1)*6` (timer/act field) |
| `0x03002810 + 0x710` | `((P>>8)&0xFFFF)<<12` (16-bit extra payload field) |
| `0x03002810 + 0x714` | `((P>>26)&3)+2` (hearts) |
| `0x03002810 + 0x715` | `P>>28` (starting stage) |
| `0x03002810 + 0x716` | accept/reject marker (written `0xFF` on accept, 0 on reject) |

Savestate `.ss*` layout used for RAM reads: PNG with zlib `gbAs` chunk → 397,312
bytes; VRAM at `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000`
(so IWRAM `0x03003ED0` ⇒ raw `0x1CED0`).

## 5. Algorithm

### 5.1 Alphabet and packing

```
ALPHA = "BCDFGHJKLMNPQRST"        # 16 symbols, index 0..15
char -> value: ALPHA.index(c)     # 4 bits
```

The on-screen 12 characters split into two groups: `c[0..7]` → 32-bit `W`,
`c[8..11]` → 16-bit checksum word `V`.

### 5.2 Validator (`0x0801C290`) — exact pseudocode

```
n[i] = ALPHA.index(c[i])  for i in 0..11        # enforced by UI

# phase 1: 8 nibbles -> W (rotate-left-4 fold)
W = 0
for i in 0..7:
    W = rol32(W | n[i], 4)

# phase 2: 4 nibbles -> V (rotate-left-4 fold within 16 bits)
V = 0
for i in 8..11:
    V = rol16(V | n[i], 4)

F = fold(W)
if F == 0 or V != F: reject()                    # "INVALID CODE"

P = W ^ 0x3EDFACB7
# write fields into game state (see address map)
accept()
```

`fold(W)` is a 16-bit additive mix of three 16-bit slices of `W`, transcribed
exactly from `0x0801C2D6..0x0801C2FC` (see `decode.py` in the work dir). All
arithmetic is 32-bit wrapping, then truncated to 16 bits.

### 5.3 Generator (`0x0801BD80`) — inverse

```
P  = desired 32-bit game-state payload
W  = P ^ 0x3EDFACB7
F  = fold(W)
# first 8 characters (inverse of phase 1):
n0 = W & 15;  n1..n7 = (W >> 28), (W >> 24), ... (W >> 4) & 15
# last 4 characters (inverse of phase 2):
n8 = F & 15;  n9 = (F >> 12) & 15;  n10 = (F >> 8) & 15;  n11 = (F >> 4) & 15
code = ''.join(ALPHA[x] for x in n)
```

The in-game generator builds `P` from the live game-state bytes listed in §4,
XORs with `0x3EDFACB7`, and emits the characters through the same alphabet table.
The encoder derived from the validator reproduces every published code exactly,
so the two paths agree.

## 6. Tables

### 6.1 Payload `P` field layout (after XOR with `0x3EDFACB7`)

| Bits | Meaning | Observed range | Confidence |
|---|---|---|---|
| 0 | difficulty: 0=hard, 1=easy | 0,1 | Observed (RAM + screen) |
| 1–3 | continues | 0–7 | Observed |
| 4–7 | lives | 1–15 | Observed |
| 8–23 | extra 16-bit field (written `<<12` at `S+0x710`) | 0x0079…0x9999 | Layout derived; meaning inferred |
| 24–25 | act/timer selector → `(n+1)*6` | 0–3 | Arithmetic derived |
| 26–27 | hearts − 2 | 2–5 | Observed |
| 28–31 | starting stage | 0–4 seen, 15 accepted | Observed / range unvalidated |

### 6.2 Published codes decoded (all accepted by my model)

| Code | Stage | Diff | Cont | Lives | Extra | Hearts | P |
|---|---|---|---|---|---|---|---|
| `CFNRTTTLMMPM` | Italy | hard | 3 | 3 | 0x0053 | 3 | `04005336` |
| `BFSRTRHLDKGK` | Italy | easy | 3 | 3 | 0x0079 | 2 | `00007937` |
| `BDSRTDQLMPNP` | Italy | easy | 3 | 3 | 0x0080 | 2 | `10008037` |
| `BDSRTDSSPCRC` | Italy | easy | 3 | 5 | 0x0082 | 2 | `10008257` |
| `GFTRSLSNTHCG` | Russia | easy | 1 | 1 | 0x0122 | 2 | `01012213` |
| `BCTRSMNLKCMC` | Russia | easy | 3 | 3 | 0x0136 | 2 | `21013637` |
| `FFPRTDQNMSNS` | Russia | hard | 2 | 1 | 0x0080 | 3 | `05008014` |
| `GDLRSDLNDRFR` | Japan | easy | 1 | 1 | 0x0184 | 3 | `16018413` |
| `BBLRSDHLPLQL` | Japan | easy | 3 | 3 | 0x0189 | 3 | `36018937` |
| `FFLGJFHGJTJT` | Japan | hard | 2 | 15 | 0x9999 | 3 | `069999F4` |
| `BKMRRRRMFQHQ` | USA | easy | 3 | 2 | 0x0271 | 3 | `47027127` |
| `FFMGJFHGKTKT` | USA | hard | 2 | 15 | 0x9999 | 3 | `079999F4` |
| `CDNRTRHTTRCQ` | Italy | hard | 3 | 4 | 0x0079 | 3 | `14007946` |
| `CCPRSPGSSMBL` | Russia | hard | 3 | 5 | 0x0118 | 3 | `25011856` |
| `CBBRQPMDJPKP` | Japan | hard | 3 | 9 | 0x0315 | 5 | `3E031596` |
| `CKCRNMLKGHJH` | USA | hard | 3 | 12 | 0x0534 | 5 | `4F0534C6` |

None of the published codes appear as literals in the ROM (ASCII, case-shifted,
UTF-16, 4-bit packed or index-encoded) — confirming the forum report that the
passwords are algorithmic.

### 6.3 Debug/test menu (OPTIONS)

| Entry | Range / values | Effect |
|---|---|---|
| SOUND FX | ON / OFF | toggles SFX enable |
| MUSIC | ON / OFF | toggles music enable |
| TEST FX | 01–26 (wraps) | previews sound effect `(byte+1)` (SFX call at `0x080213F0`) |
| TEST MUSIC | 01–22 (wraps) | plays music track `(byte+1)` (call at `0x080213E8`) |
| EXIT | — | returns to title |

## 6b. Enumeration

**Space definition.** Alphabet 16 symbols ⇒ 4 bits/symbol; 12 symbols ⇒ 48 raw
bits (16¹² = 2⁴⁸ strings). Payload `W` is 32 bits (first 8 symbols); checksum
`V` is 16 bits (last 4 symbols). `V` is fully determined by `W`, so the accepted
set is one string per admissible `W`.

**Exact count (computed by exhaustive C run over all 2³² `W`, `count.c`):**

```
total W = 4,294,967,296
fold(W)==0: 1   (W = 0x00000000 only)
accepted codes = 4,294,967,295   (2^32 - 1)
```

The one rejected code is `BBBBBBBBBBBB` (`W=0`, `V=0`). All other 2³²−1
12-symbol strings with a correct checksum are accepted; the validator performs
**no semantic range check** on stage/hearts/act fields (proved below).

**Novel code (in no published list).**

```
MKCMRSSGHGKG
P = 0x4F4242FE  W = 0x719DEE49  fold(W) = 0x4745
```

Payload: stage 4 (USA), hard, 7 continues, 15 lives, 5 hearts, act field 3,
extra field `0x4242` — a combination absent from GameFAQs, cheatingdome,
AtariAge and absolutecheats. Entered through the real password screen; the game
advanced to the world map with USA selected and the trophy display changed
(`after_novel_c.png`). Live RAM after entry:

```
global P @0x0201F4A4 = 0x4F4242FE
S+0x70C continues = 7     S+0x70D difficulty = 0 (hard)
S+0x70E lives = 15        S+0x70F act field = 24
S+0x714 hearts = 5        S+0x715 stage = 4
S+0x710 word = 0x04242000  (extra field 0x4242 << 12)
```

Every field matches the model. Other minted-but-untested examples:
`MBCQRMLGTPBN`, `RCGRTHFQFCHC`, `JKSNLRPNKNMN`.

**Bounds proven by in-game rejection.**

| Test | Code | Model result | In-game result |
|---|---|---|---|
| Bad checksum (last char `G`→`H`) | `MKCMRSSGHGKH` | `V=0x4755 ≠ fold=0x4745` | `INVALID CODE` (`rej_badchk_c.png`) |
| `fold(W)==0` guard | `BBBBBBBBBBBB` | `fold=0` even though `V==fold` | `INVALID CODE` (`rej_allB_c.png`) |
| Out-of-range stage field (15) | `MQCMRSSGHMKM` | decoder accepts, `S+0x715=15` | **accepted**, map reached — proves no semantic stage bound |

**Debug-menu bounds.** Right-press enumeration over 120 presses found wrap
periods of 26 (FX: 01…26) and 22 (Music: 01…22), with no gaps in either range.

**Button-code negative (bounded).** Searched the whole 4 MiB image for the
published sequences as `u16` GBA key masks (active-high and active-low):
`B,A,R,L,R,A` (SNES invincibility) and `U,D,U,D,L,U,D,U,D,R` (3DO level select)
— 0 hits each. A scan for any 6 consecutive single-button masks found only
repetitive graphics data (e.g. 0x200 runs), no controller table. In emulation,
L/R on the title caused no colour change and the 3DO sequence left the title
screen unchanged. The published codes are explicitly tagged JAG/SNES/3DO on
GameFAQs; they are not GBA codes. (The SNES sequences containing A cannot be
isolated on the GBA title because A also activates the START menu item.)

## 7. Validation evidence

* **Observed** — mGBA screenshots of title, password, OPTIONS/test menu, world
  map; `INVALID CODE` after the two rejected codes; exact RAM bytes read from
  decompressed savestates before/after code entry and option changes.
* **Derived** — validator and generator transcription from Thumb disassembly at
  `0x0801BD80`/`0x0801C290`; XOR key `0x3EDFACB7` read from literal pools;
  exact `fold()` count from exhaustive C execution of the transcribed function;
  field meanings from the writes at `0x0801C326..0x0801C39E` cross-checked
  against the published descriptions and live RAM.
* **Inferred** — meaning of the 16-bit extra field at bits 8–23 (likely inventory/
  score scratch) and of the `(n+1)*6` field at bits 24–25; the `CREDITS 0` string
  has no xref and was not shown to be reachable. The precise audio produced by
  TEST FX/MUSIC could not be heard (`SDL_AUDIODRIVER=dummy`); only the sound
  engine calls were observed statically.

## 8. Unknowns

* Semantic meaning of payload bits 8–23 and 24–25 beyond their RAM destinations.
* Whether the `CREDITS 0` string belongs to a reachable end-credit path (the
  published glitch says the last boss crashes before the good ending).
* No GBA-specific title button code was found; absence is bounded by the mask
  searches above, not proven for an arbitrary future discovery.

## 9. Tooling

Scripts and evidence in `/tmp/soccerkid/`: `recon.py` (string/pointer
recon), `litscan.py` (PC-relative literal scan), `ss.py` (savestate `gbAs`
extractor), `decode.py` (exact validator model + decoder/encoder), `mint.py`
(code generator), `count.c` (exhaustive accepted-space count), `enter.py` /
`keymap.py` / `enum_options.py` (XTEST UI drivers), `k.py` (key helper), plus
cropped screenshots (`after_novel_c.png`, `rej_allB_c.png`, `rej_badchk_c.png`,
`title_sel_crop.png`, `pass_screen_crop.png`, `opt_screen_c.png`,
`testfx_strip.png`). Tools: mGBA 0.10.5, arm-none-eabi-objdump, Capstone 5.0.7,
Python 3, gcc, Xvfb + openbox, xdotool, scrot, ImageMagick.

No ROM or copyrighted assets are redistributed by this report.
