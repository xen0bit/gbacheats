# Shaun Palmer's Pro Snowboarder (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Shaun Palmer's Pro Snowboarder.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title / code / maker | `SHAUNPALMER1` / `ASCE` / `52` |
| Version / fixed / complement / checksum | 0x00 / 0x96 / 0x5D / 0x0000 |
| Entry word | `0xEA00002E` (stock ARM `b 0x080000C0`, not a cracktro) |
| MD5 | `e08250206b5cf301c15417112f306a16` |
| SHA-1 | `c27bf70516d25040f63c937e5f5446847cf41b48` |
| SHA-256 | `3f5fd861df229dbcffa0a7f516babb11267513d057316415ca52c97d3d7f1ebe` |
| Build stamp | `09/21/2001 12:00` at file `0x7FFFF0` |

Single Nintendo-logo header at file `0x4`; no pack/trainer. This report supersedes the earlier one, which failed §0.2: its input-global addresses were digit-transposed and it did not locate the validator.

## 2. Executive summary

The game has a real **13-symbol algorithmic password system** (`PASSWORD` main-menu entry → 13-slot masked "Password Input" screen). The validator is **`FUN_08013114` at `0x08013114`**, called only when the on-screen `END` cell is accepted. It is a checksum over five interleaved bit-planes, not a code table: each of 13 glyphs contributes a 5-bit value, a rotation amount derived from the total popcount, a per-position XOR mask, and an 8-bit check split into a 4-bit arithmetic sum plus a 4-bit type-dependent mask.

The alphabet is 32 symbols: `BCDFGHJKLMNPQRSTVWXZ0123456789!?` (vowels A/E/I/O/U and Y are absent). Nominal space `32^13 = 2^65 ≈ 3.69e19`; the 8-bit check reduces it to ≈`2^57` checksum-valid strings before field semantics.

Reimplemented offline as an exact model: **7 of 8 published codes validate**; the eighth, `QFJ7MP9N?5CM4`, is a published typo — correcting its final `4`→`2` (`QFJ7MP9N?5CM2`) or its first `Q`→`6` (`6FJ7MP9N?5CM4`) makes it validate. A novel code **`929WS3850GP84`** was generated with a deliberately unadvertised field combination (type 3, `u1=0x155`, `u2=0x2AA`, `u3=0x0F0`, `u4=0x1C2`), entered on the real 13-slot screen, and accepted: RAM shows the exact designed fields written to `0x03006C6C`. A one-character near-miss `929WS3850GP85` was rejected on screen with "INVALID PASSWORD. TRY AGAIN." and wrote no fields. A published control code (`FR5RNR?M?KLHJ`) produced RAM bytes matching the model bit-for-bit.

## 3. How to reproduce

mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `-3`, XTEST keys (A=`x`, B=`z`, Start=`Return`, D-pad=arrows; holds of 80 ms — shorter holds double-step the cursor). Title → `Return` → `PASSWORD` (3× Down, `x`) → Password Input. Keyboard table is 5 columns; a glyph of 5-bit value `v` is at row `v//5`, column `v%5`; the control row is `[30,31,←,→,END]`, so submit by moving to row 6/col 4 and pressing A. Slots render the glyphs after entry (the earlier report's "masked" claim was wrong). Savestates: `Shift+F1..F9` save, `F1..F9` load; `ssread.py` extracts the zlib `gbAs` chunk (IWRAM raw offset `0x19000` ↔ `0x03000000`).

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| **Password validator / decoder** | **`0x08013114`** (`FUN_08013114`) | Derived (Ghidra decompile + objdump) |
| Password screen handler (calls validator at `+0x390`) | `0x08011878` (`FUN_08011878`) | Derived |
| Success / reject branch | `0x08011EA4` / `0x08011EB8` | Derived (return 1 → sound+advance; return 0 → red banner) |
| 13-glyph input buffer (mutated in place) | `0x03001648` | Observed (savestate diff) + derived |
| Untouched backup of the 13 glyphs | `0x03001658` | Derived (literal pool) |
| Held / pressed key words | `0x03003E10` / `0x030032F0` | Derived (keypad poll `0x08001F04`) — **corrects prior report** |
| Keyboard value table (5-wide rows) | `0x08425645` | Derived (`DAT_08011ee0`) |
| Font glyph string (64 chars) | `0x0842CADA` | Derived (prior report retained) |
| Decoded type global | `0x03006710` | Observed (savestate: 0 → 3) |
| Decoded payload slots (4 × 20 bytes) | `0x03006C30 + type*0x14` | Observed |
| Wildcard/flag bool | `0x03006CA0` | Derived |
| Goal/tutorial ASCII bank | `0x42C780–0x43300` | Observed (retained: `HIDDEN IN EVERY LEVEL.`, `FIND 2 HIDDEN AREAS`) |

Savestate RAM layout: raw 397,312 bytes; VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`. Entering a code changed only IWRAM.

## 5. Algorithm (`FUN_08013114`)

```
input: g[0..12]               # values from keyboard table, each <= 31
backup = copy(g) to 0x03001658
if any g[i] > 31: fail
rot = popcount5(g[0]) + ... + popcount5(g[12])  mod 5
if rot != 0:
    even i: g[i] = rotl5(g[i], rot)
    odd  i: g[i] = rotr5(g[i], rot)
XMASK = [0x10,0x04,0x01,0x08,0x02,0x01,0x08,0x02,0x10,0x04,0x04,0x10,0x02]
g[i] ^= XMASK[i]                       # 13 x 5-bit working values
b(i,k) = (g[i] >> k) & 1

type = b(4,0)<<1 | b(0,0)             # 0..3 -> mask {1,3,7,15}
u1 = Σ b(i,1)<<i          (i=0..9)     # 10 bits
p1 = b(10,1)|b(11,1)<<1|b(12,1)<<2    # 3 bits
c8 = b(8,0)                            # 1 bit
u2 = Σ b(12-j,2)<<j       (j=0..9)     # 10 bits, reversed source order
p2 = b(2,2)|b(1,2)<<1|b(0,2)<<2        # 3 bits
u3 = Σ b(i,3)<<i          (i=0..9)     # 10 bits
p3 = b(10,3)|b(11,3)<<1|b(12,3)<<2|b(1,0)<<3   # 4 bits
u4 = Σ b(12-j,4)<<j       (j=0..9)     # 10 bits, reversed
p4 = b(2,4)|b(1,4)<<1|b(0,4)<<2|b(2,0)<<3      # 4 bits

lhs = b(3,0) | b(5,0)<<1 | b(6,0)<<2 | b(7,0)<<3 |
      b(9,0)<<4 | b(10,0)<<5 | b(11,0)<<6 | b(12,0)<<7
rhs = (u1+p1+c8+u2+p2+u3+p3+u4+p4 & 0x0F) | ({0:1,1:3,2:7,3:15}[type] << 4)
if lhs == rhs:
    0x03006710 = type
    slot = 0x03006C30 + type*0x14
    slot+2=u1 (u16); +4=p1; +5=c8; +6=u2 (u16); +8=p2; +10=u3 (u16);
    +12=p3; +14=u4 (u16); +16=p4;  bool at 0x03006CA0 = (p3 & 8)!=0
    return 1
else:
    restore g from backup; return 0
```
Rotation verifies as a fixed point (`rot = popcount(original) % 5`); `FUN_0804196c` is the SDK modulo routine. An encoder inverts the field packing, XOR and rotation to mint codes.

## 6. Tables

**Alphabet (value → glyph), proven by entering values 0..31 and reading the display:**
`0:B 1:C 2:D 3:F 4:G 5:H 6:J 7:K 8:L 9:M 10:N 11:P 12:Q 13:R 14:S 15:T 16:V 17:W 18:X 19:Z 20:0 21:1 22:2 23:3 24:4 25:5 26:6 27:7 28:8 29:9 30:! 31:?`

**Published codes vs offline model:**

| Code | Model | Note |
|---|---|---|
| `6FJ7MP9N?5CM4` | OK | corrected form of published `QFJ7MP9N?5CM4` (final `4`→`2` also works) |
| `FR5RNR?M?KLHJ` | OK | also confirmed in-game (type 0) |
| `38LQNQ!DRQM2K` | OK | |
| `81S3196R88GQ1` | OK | type 3 |
| `SSK203?137VJ8` | OK | |
| `?ZQW5VQC!403W` | OK | type 1 |
| `5ZQ9X17R?8DWZ` | OK | |
| `SSF303!1?ZV28` | OK | |

## 6b. Enumeration

**Space:** 13 symbols × 5 bits = 65 bits (`3.69e19` strings). All 65 bits are used: 52 payload bits (planes 1–4) plus 13 bit-0 bits (2 type, 1 c8, 2 in p3/p4, 8 check). Eight check bits ⇒ ≈`2^57` checksum-valid strings, partitioned into 4 type families by a 2-bit field. Field semantics may narrow this further; that is the only remaining unknown.

**Novel code (in no published list): `929WS3850GP84`**
- values `1d 16 1d 11 0e 17 1c 19 14 04 0b 1c 18`; type 3; `u1=0x155 p1=2 c8=0 u2=0x2AA p2=5 u3=0x0F0 p3=9 u4=0x1C2 p4=3`.
- Entered on the real 13-slot screen and submitted with END. **On-screen:** success/advance to main menu. **RAM proof (savestate `game.ss9`, captured `accept_banner.png`/`success_*.png`):** `0x03006710 = 03`; `0x03006C6C = 03 00 55 01 02 00 aa 02 05 00 f0 00 09 00 c2 01 03 00` — i.e. exactly the designed fields.

**Bounds proven by rejection:** `929WS3850GP85` (one character changed, `4`→`5`) gives `lhs=0x4E`, `rhs=0xFD` in the model. Entered in-game: red **"INVALID PASSWORD. TRY AGAIN."** banner (`reject_banner.png`), `0x03006710 = 00`, and `0x03006C6C` fields all zero (savestate `game.ss2`). This bounds the 8-bit checksum gate at byte level.

## 7. Validation evidence

* **Observed** (emulator/savestates): full screen walk; keyboard glyph↔value map; novel code accepted with exact RAM fields; near-miss rejected with banner and zero fields; published code's RAM fields match model byte-for-byte.
* **Derived** (Ghidra decompile + objdump): validator at `0x08013114`, XOR mask, five bit-plane extractions, 8-bit check, output slot layout; keypad globals (corrected); keyboard table.
* **Inferred**: semantic meaning of the field names (rider/board/track/sponsor groups) from the published effects list; the type→mask mapping is derived from code, not from a spec.
* Fetched web pages were treated strictly as data; no prompt-injection content was encountered.

## 8. Unknowns

1. Human-readable names of each `u*`/`p*` field (rider/board/track/sponsor index) — the numeric layout is proven, the labels are inferred.
2. Whether the type-3 payload minted here corresponds to a visually distinct rider/track set; only the unlock-structure writes were RAM-verified.
3. Whether the published `QFJ7MP9N?5CM4` typo is the `4`→`2` or `Q`→`6` variant (both validate; cannot distinguish without the original source list).

## 9. Tooling

Ghidra 12.1.4 via REA MCP (`open_binary`, `list_procedures`, `analyze_function`, `procedure_pseudo_code`); `arm-none-eabi-objdump -M force-thumb`; Python 3 + capstone; custom scripts in `/tmp/opencode/shaunpalmer2/`: `model.py` (exact validator model), `encode.py` (constructive encoder), `enter_code.py` (screen navigation + RAM dump), `ssread.py` (mGBA savestate decoder), `ui.py` (xdotool driver), `mapglyph.py` (alphabet recovery). Screenshots `accept_banner.png`, `success_*.png`, `reject_banner.png`, `g0_12c.png`, `g13_25c.png`, `g26_31c.png`.

## 10. Legal note

No ROM image, extracted graphics, or copyrighted assets are reproduced here — only hashes, addresses, algorithms, and our own analysis and generated codes.

## 11. Cleanup

All processes started for this engagement (Xvfb `:315`, openbox, mGBA, helpers) were terminated by PID number; no `pkill` was used. Generated `.sav`/`.ss*` files were confined to the work directory and the ROM folder was left clean (only `.gba` and this report).
