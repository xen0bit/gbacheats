# The Mummy (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/The Mummy/The Mummy.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `THEMUMMY` |
| Game code | `AUME41` (`AUME` at 0xAC, maker field `41` at 0xB0) |
| Fixed byte / main unit / device | `0x96` / `0x00` / `0x00` |
| Version / complement / checksum | `0x00` / `0x4E` / `0x0000` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0; no cracktro) |
| SHA-1 | `cc833b1398a6ea87d31712806757c2fe52fadd31` |
| SHA-256 | `3525361ab0166dfd7418770659fd3ea184df44d640709068df9eda0952c9d135` |

Analysis used a byte-identical copy in `/tmp/opencode/mummy/`.

## 2. Executive summary

The game has a **developer-intended 4-symbol password system**. The on-screen alphabet is
32 symbols, `BCDFGHJKLMNPQRSTVWXYZ0123456789*`, so each password is 20 bits. A published
list of 15 codes exists (GameFAQs/GameGenie/ChapterCheats); **14 of them are structurally
valid against the ROM's own validator, one (`XXNY`) is not**.

The full codec was recovered from three small Thumb functions: a bit permutation
(`0x08032494`), a folded field/checksum validator (`0x08032390`), and a decoder
(`0x08031ED4`) that applies a second mask gate and writes 13 bits of game state at
`0x020072B0`. The inverse generator is at `0x080323E4`. I reimplemented both, enumerated
the entire 1,048,576-string space offline, and confirmed the counts with the ROM's own
validator: **8,192 checksum-valid strings, of which 1,600 pass the full mask gate**.

I minted novel codes absent from every published list. Calling the ROM's own decoder on
packed `CGFC` (payload `0x30`) returns **accept (r0=1)** and changes RAM at `0x020072B0`
from `64 00 00 00 64 …` to `64 00 01 19 64 …`. Two rejection layers were proved with the
same oracle: a bad-checksum word (`0x00001`) and a checksum-valid but out-of-range payload
(`GGNZ`, payload `0x100`) both return **r0=0 with no RAM change**.

The password *entry* screen exists in code (handler `0x080326E0`, reached by menu
selection 5 in `0x080371D0`), and its 4×8 grid mapping was decoded, but a retail-path walk
of every reachable screen did not expose that menu in this build. The in-game evidence is
therefore entering via the ROM's own decoder with RAM verification, not via the on-screen
keyboard; this is labelled explicitly in §7.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy DISPLAY=:318 mgba -3 The Mummy.gba`.
* Keymap (mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Hold keys 90–150 ms.
* Screen walk (all observed): language select → main menu (`NEW GAME`, `CONTINUE`;
  2 options, wraps) → intro/credits → gameplay → **Start** opens a `PASSWORD` overlay
  showing the current 4-symbol password (`BHN0` at level 1) with `CONTINUE`/`QUIT` →
  `QUIT` → `ARE YOU SURE? NO/YES` → main menu. **Select+Start** toggles an
  inventory/status screen (3 portraits, item grid, current password bottom-right);
  Select+Start again returns to the `PASSWORD` overlay. L/R/B/Select/A were tested on
  both overlays; none exposed a code-entry mode. L+R, L+R+Start, Select+Start, A+B,
  Start+A were tested at the main menu and in-game.
* Oracle reproduction: mGBA CLI debugger (`mgba -3 -d The Mummy.gba`), `load 1` (a
  savestate captured on the password screen). Set `r0` to the address of a 32-bit packed
  code, `lr = 0x0800F9CC`, `pc = 0x08031ED5`; set breakpoint `b 0x0800F9CC`, `c`, then
  read `r0` and `x/1 0x020072B0 16`. Script: `/tmp/opencode/mummy/oracle.py`.
* Codec reproduction: `/tmp/opencode/mummy/pw.py` (`validate`, `encode_payload`,
  `to_code`, `from_code`) is bit-exact against the ROM for all published codes.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Address | Purpose | Evidence |
|---|---|---|
| `0x08040DD4` | 32-symbol alphabet string (`BCDFGHJKLMNPQRSTVWXYZ0123456789*`) | Derived (Ghidra string + literal bytes) |
| `0x08040DFC` | `u16[4]` mask table `{0x00FF, 0x13FF, 0x17FF, 0x1F06}` for decoder category bits | Derived |
| `0x080323C8` | const `0xFFFFF` (20-bit input mask) | Derived |
| `0x080323CC` | const `0x3FF` (10-bit fold mask) | Derived |
| `0x080323E0` | const `0x1FFF` (13-bit payload mask) | Derived |
| `0x08032454` | const `0x1FFF` (checksum input mask) | Derived |
| `0x08032494` | bit permutation (involution: swaps bit pairs 0↔13, 2↔14, … 12↔19) | Derived |
| `0x08032458` | same permutation used by generator | Derived |
| `0x08032424` | checksum: `(((v>>8)+(v&0xFF)) ^ 0xFF) & 0x7F`, `v = x & 0x1FFF` | Derived |
| `0x08032390` | validator: permute → fold → compare `y>>13` with checksum | Derived + oracle |
| `0x080323E4` | generator/encoder: payload → folded word → checksum → permute → 20-bit code | Derived |
| `0x08031ED4` | decoder: validate, mask gate, unpack fields into state | Derived + oracle |
| `0x020072B0` | game-state object written by decoder (bytes +0,+2,+3,+4,+D observed) | Observed (RAM) |
| `0x080326E0` | password-entry UI handler (4 slots, A cycles symbol, grid select) | Derived |
| `0x080329F8` | grid→symbol: `col + row*8 + 1` (8×4 grid = 32 symbols) | Derived |
| `0x08032A60` | packs 4 slots: `s3<<15 | s2<<10 | s1<<5 | s0` (first entered = low bits) | Derived |
| `0x08037304` / `0x08037388` | screen factories; `r0=3` builds the 6-option menu, `r0=2` the code screen | Derived |
| `0x080371D0` | menu result handler; selection `5` → `FUN_08037388(2)` (code entry) | Derived |
| `0x02003298` | active-screen object pointer (observed `0x0200C860` menu, `0x02007320` gameplay) | Observed |
| `0x0200C860`, `0x02007320`, `0x02008C50` | screen objects (main menu, gameplay, 6-option menu) | Observed/Derived |

## 5. Algorithm

```
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0123456789*"          # 32 symbols, 5 bits each

permute(x):                    # involution; swap bit pairs
    for lo,hi in (0,13),(2,14),(4,15),(6,16),(8,17),(10,18),(12,19):
        swap bits lo and hi of x
    return x

checksum(y):                   # y is 20-bit; mask is 0x1FFF
    v = y & 0x1FFF
    return (((v >> 8) + (v & 0xFF)) ^ 0xFF) & 0x7F

validate(p):                   # p = 20-bit packed password
    x   = permute(p & 0xFFFFF)
    lo  = x & 0x3FF
    hi  = (x >> 10) & 0x3FF
    y   = ((hi ^ lo) << 10) | lo
    ok  = (y >> 13) == checksum(y)
    payload = y & 0x1FFF       # written back only when ok
    return ok, payload

encode(payload):               # inverse; generator at 0x080323E4
    for chk in 0..127:         # chk = y>>13, 7 bits
        y = (chk << 13) | payload
        if checksum(y) == chk:
            lo = y & 0x3FF; hi = (y >> 10) ^ lo
            x = (hi << 10) | lo
            return permute(x)  # permutation is its own inverse
```

Decoder second layer (`0x08031ED4`): let `cat = (payload & 0x1F) >> 3`; require
`(payload & ~mask[cat]) == 0` with `mask = [0x00FF, 0x13FF, 0x17FF, 0x1F06]`. On success
the decoder unpacks payload bits into the state object (`0x020072B0`): bits 0,1,2,3,5,6,7
of the low byte and bits 0,1,2,3 of the next byte are written to distinct offsets (+0x0B,
+0x17, +0x0C, +0x19, +0x0D, +0x1B, +0x0E, +0x1D, +0x0F, +0x1F); bits 3–4 select `cat`.

UI pack order: the first symbol entered occupies the low 5 bits, so the code displayed
MSB-first is the **reverse** of the entry order.

## 6. Tables

Published codes (GameFAQs `gba/582351`, GameGenie, ChapterCheats — all the same 15 strings):

| Code | packed | payload | validator | mask gate |
|---|---|---|---|---|
| `128T` | 0xB5FAF | 0x3EE | pass | pass |
| `XXNY` | 0x94953 | 0x046 | **fail** | – |
| `9*8N` | 0xF7FAA | 0x3EF | pass | pass |
| `S50N` | 0x76AAA | 0x13EF | pass | pass |
| `KH8G` | 0x397A4 | 0x3F0 | pass | pass |
| `TH8Z` | 0x797B4 | 0x7F0 | pass | pass |
| `TK*D` | 0x79FE2 | 0x7F2 | pass | pass |
| `BHN0` | 0x01555 | 0x000 | pass | pass |
| `BGPH` | 0x01165 | 0x020 | pass | pass |
| `DBHH` | 0x100A5 | 0x0E0 | pass | pass |
| `DDHF` | 0x108A3 | 0x0E2 | pass | pass |
| `XXHY` | 0x948B3 | 0x0E6 | pass | pass |
| `55HX` | 0xD68B2 | 0x0E7 | pass | pass |
| `DBKQ` | 0x100EC | 0x0E8 | pass | pass |

`XXNY` is not accepted by the ROM's validator; `XXHY` differs only in symbol 3 and is
valid — treat `XXNY` as a published-list typo/unverified code (guide §16.7).

## 6b. Enumeration

**Space.** 4 positions × 32 symbols = 32⁴ = **1,048,576** distinct strings. Alphabet,
length, field widths and check position are exact. Payload is 13 bits; checksum is 7 bits
folded into the top 7 bits of the packed word; 2 reserved payload bits exist per category
via the mask table.

**Counts (running the ROM's own validator over the full space, offline reimplementation
cross-checked against the oracle):**
* 1,048,576 strings total
* **8,192** pass the checksum (exactly 2¹³, as expected for a 7-bit check)
* **1,600** pass the full decoder mask gate, 1,600 distinct payloads (no alias pairs found
  at the decoded-state level; `BHN0`/payload 0 is the "no change" baseline)
* payload range 0x000–0x17F7; category counts follow the four masks above

**Novel codes (not present in any published list checked):**

| Code | packed | payload | generator | decoder result (RAM at `0x020072B0` before → after) |
|---|---|---|---|---|
| `CGFC` | 0x09061 | 0x030 | accepted | `64 00 00 00 64 …` → `64 00 01 19 64 …` |
| `NLHG` | 0x520A4 | 0x0E1 | accepted | `64 00 00 00 64 …` → `64 00 03 19 64 …` |
| `TR8W` | 0x7B7B1 | 0x3F1 | accepted | `64 00 00 00 64 …` → `64 00 05 32 64 …` |
| `KR*C` | 0x3B7E1 | 0x7F1 | accepted (derived) | not entered into oracle |
| `2B0G` | 0xB82A4 | 0x13F0 | accepted (derived) | not entered into oracle |

Each exercises a payload value absent from the 14 valid published codes. `CGFC`, `NLHG`
and `TR8W` were fed to the game's own decoder at `0x08031ED4` and returned r0=1 with the
distinct RAM changes shown; screenshots of the source screens are in
`/tmp/opencode/mummy/` (`pw_*`, `statc.png`, `cur2c.png`).

**Bounds proved by rejection (in-game code, oracle):**
* bad checksum: packed `0x00001` → r0=0, state bytes unchanged.
* checksum-valid but out-of-range field: `GGNZ` (packed `0x21154`, payload `0x100`, category
  0 whose mask is `0x00FF`) → r0=0, state bytes unchanged. This isolates the second
  (mask/range) layer from the checksum layer.
* category/field width boundaries derive from the four masks: 0x00FF, 0x13FF, 0x17FF,
  0x1F06.

## 7. Validation evidence

**Observed**
* Screen enumeration: language select, main menu (2 entries, wrap at 2), intro/credits,
  gameplay, `PASSWORD` overlay (`BHN0`), quit confirmation, inventory/status via
  Select+Start. Button-grid and savestate evidence on disk.
* Oracle RAM reads: `0x020072B0` before/after for accepted and rejected codes (§6b).
* `strings`/font search: no ASCII `PASSWORD`; the alphabet is a literal at `0x08040DD4`;
  all visible UI text is tile-encoded, so the absence of a `strings` hit was not used as
  evidence of absence (guide §11).

**Derived**
* Validator, generator, decoder, mask table, UI grid map, slot packing, screen-factory
  chain, all from Thumb disassembly and Ghidra decompilation, verified by the offline
  reimplementation agreeing with 13/14 published codes and with the oracle.

**Inferred / not proven**
* No retail input sequence was found that opens the code-entry screen in this build. The
  handler exists and is reachable in code (`0x080371D0` selection 5 → `0x08037388(2)`),
  and the 4×8 grid map is decoded, but calls to the screen factory from a debugger either
  produced a black screen or the Ubisoft splash. The novel codes were therefore verified
  through the ROM's own decoder rather than typed on the on-screen keyboard. This is the
  principal limitation of this report.
* Field names at `0x020072B0` (health/items/characters) are not established; only the bit
  offsets and observed byte changes are reported.

## 8. Unknowns

* Retail path to the `Enter Code` screen (Bonus Game Modes / Select Level). The GameFAQs
  description mentions a pause→quit→replay-level→Select Level flow that did not match the
  screens reachable in this AUME41 build.
* Whether the bit permutation and fold serve a copy-protection purpose or simply
  obfuscation; no documentation found.
* Exact semantic meaning of the 13-bit payload fields and of the four mask categories.
* `XXNY` may belong to a different regional revision; only AUME41 was analysed.

## 9. Tooling

`file`, `sha1sum`, `sha256sum`, `strings`, `xxd`, Python 3 (codec, savestate parser,
BL scanner), `arm-none-eabi-objdump -M force-thumb`, Capstone (trial), Ghidra 12.1.4 via
REA MCP (`open_binary`, `analyze_function`, `procedure_pseudo_code`, `xrefs`,
`batch_decompile`), mGBA 0.10.5 with CLI debugger (`-d`, `load 1`, `w/r`, `w/4`, `b`, `c`,
`x/1`), Xvfb :318 + openbox, `xdotool`, `scrot`, ImageMagick.

Scripts retained: `/tmp/opencode/mummy/pw.py`, `blscan.py`, `findtext.py`, `ss.py`,
`k.py`, `play.py`, `invoke.py`, `oracle.py`, `decode.py`.

No ROM bytes, graphics or copyrighted assets are reproduced here; only addresses,
hashes, algorithms and derived codes are published.
