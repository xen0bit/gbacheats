# The Revenge of Shinobi (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/The Revenge of Shinobi/The Revenge of Shinobi.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `REVENGEOFSHI` |
| Game code | `A3RE` (maker `78`), i.e. USA `AGB-A3RE-USA` |
| Version | `0x00`; complement `0x52`; header checksum `0x0000`; entry branch `0xEA00002E` |
| MD5 | `95b8cb63649f7bb62a2f9a6a39bf7388` |
| SHA-1 | `22adb84902a1d1b3b63986eded3cc2a1bc9aa0b4` |
| SHA-256 | `f409136893839ced80b2035873e79ffd3c283978bec926f4c9e93ed5fec0ea8a` |

The entry word is the stock `0xEA00002E` and the first 4 KiB is ordinary ARM crt0 — no cracktro or appended trainer. The header checksum `0x0000` is normal for this build (complement byte is intact).

## 2. Executive summary

The game has a genuine, developer-intended **16-symbol password system** reached from
the title menu (`CONTINUE`). It is not a hard-coded string table: the ROM contains a
**base-31 big-integer codec** with a multi-field validator and a matching generator
(the in-game `Obtain Password` feature). No accepted password appears verbatim in the
ROM; all published codes are algorithmic.

* **Alphabet (31 symbols):** `BCDFGHJKLMNPQRSTVWXYZ&023456789` — no vowels and no digit `1` — at ROM `0x0805DAA0` (file `0x5DAA0`). The character `&` is a real 22nd symbol, not the A/B button glyph used elsewhere in the UI.
* **Input surface:** a 4×4 grid shown on the `ENTER PASSWORD` screen. D-pad moves the cursor; **L/R cycle the character** at the cursor (observed: L changes `R`→`Q`, matching the alphabet order); A submits.
* **Buffer:** 16 × 32-bit little-endian **alphabet indices (0–30)** at EWRAM `0x02000014`. (Confirmed dynamically — ASCII bytes are *rejected*; indices are *accepted*.)
* **Validator:** `0x0801939C`; checksum/field gate `0x08018E18`; state decoder `0x0801849C`.
* **Published codes verified:** 5 of 6 independent published codes validate; one widely-copied code (`DRZN ZV3X L7M9 20GP`) is rejected by this exact ROM revision and should be treated as unverified.
* **Novel code minted and confirmed in the emulator with RAM evidence:**
  `RTCZ5J5GKLG23N4M` — accepted (`r0 = 1`) and the decoder wrote
  `0x0200006C/6E = 0x6400`, `0x02000074 = 0x00050000`, `0x03000DC4/DC5 = 0x00640209`.
  It appears in **no** published list. Fifteen more novel accepted single-symbol
  variants are listed in §6b.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:316` with `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap (mGBA SDL default): A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys.
* Menu path (observed): boot → skip THQ/SEGA/Overworks/3d6 logos with Start → title `PRESS START` → main menu (`START GAME` / `CONTINUE` / `OPTIONS`) → `CONTINUE` → `ENTER PASSWORD` grid.
* On the grid: D-pad selects one of 16 cells, L/R change its character, A executes. The screen prints `CONTROL PAD MOVES CURSOR`, `L AND R BUTTONS CHANGE CHARACTER`, `SELECT / ENTER PASSWORD / TO EXECUTE`, and failure shows `INVALID PASSWORD`.
* **Oracle method (primary evidence):** mGBA's command-line debugger (`mgba -3 -d`) was driven through a PTY. Write 16 `u32` indices to `0x02000014`, set `cpsr=0x3f`, `r13=0x03007F00`, `r14=0x03000024`, `r15=0x0801939C`, set a breakpoint at `0x03000024`, `continue`, and read `r0` at the break: `1` = accepted, `0` = rejected. This uses the **game's own validator** as ground truth (guide §16.19). Every published code was cross-checked with it before minting novel ones.
* Screenshots and logs are in `/tmp/opencode/shinobi/` (`pw1.png`, `grid.png`, `default_result*.png`, `search1.log`, `search2.log`, `verify_final.py`).

## 4. Address map

All addresses are ROM (`0x08...`) unless marked RAM.

| Address | Kind | Meaning |
|---|---|---|
| `0x0805DAA0` | data | 31-character password alphabet, NUL-terminated |
| `0x0801939C` | function | **Password validator entry**; reads buffer, decodes, validates, calls decoder; returns 1/0 |
| `0x08018CCC` | function | Copies 64 bytes from `0x02000014` and applies three differential/subtraction passes modulo 31 to build 16 digit values |
| `0x08018B98` | function | 64-bit Horner evaluator: array of base-31 digits → `u64` |
| `0x08018E18` | function | **Checksum / field gate**; big-int div/mod by 3, 5, 11 etc., XOR-fold against `0x60323228`, parity checks, bitmask range checks |
| `0x0801849C` | function | **Decoder**; writes accepted fields into game-state RAM |
| `0x08018874` | function | **Generator** (used by `Obtain Password`); packs game state into the digit array |
| `0x08019460` | function | Generator caller; converts digits to characters |
| `0x08018DD0` | function | Digits → alphabet characters (uses `0x0805DAA0`) |
| `0x0802BDE0` | function | `memcpy(dest, src, n)` |
| `0x0802C030`, `0x0802C0F4` | functions | 32-bit modulo / modular helper (used with divisor 31) |
| `0x0802C280`, `0x0802C738` | functions | 64-bit divide/remainder helpers |
| `0x081D3FC0` | data | Text-string pointer table (339 entries); index 30 → `INVALID PASSWORD` at `0x081CFAFC` |
| `0x02000014` | RAM (EWRAM) | 16 × `u32` password digit indices (0–30) |
| `0x0200006C`, `0x0200006E`, `0x02000074`, `0x0200005C` | RAM | Decoded state fields (observed written by decoder) |
| `0x03000014`, `0x03000018`, `0x030006DC`, `0x03000DC4/DC5` | RAM | Decoded state fields / counters |

## 5. Algorithm

Precise enough to reimplement the decode half; the checksum's bit-level field tests were read but only their *effect* (accept/reject) was used for enumeration.

```
ALPHABET = "BCDFGHJKLMNPQRSTVWXYZ&023456789"      # ROM 0x0805DAA0, 31 symbols
buf[i]   = u32 at 0x02000014 + 4*i, i = 0..15    # each in 0..30

digits = buf.copy()                               # 0x08018CCC, memcpy 64 bytes
for i in 14 down to 0:
    digits[i+1] = (digits[i+1] - digits[i] + 31) mod 31
for t in 49 down to 0:
    j = (t + 16) & 15;  k = (t + 23) & 15
    digits[j] = (digits[j] - digits[k] + 31) mod 31
for i in 15 down to 0:
    digits[i] = (digits[i] - f(i*13+2) + 31) mod 31   # f = 0x0802C0F4 helper

A = base31_encode(digits[0:5])                    # 64-bit, 0x08018B98
B = base31_encode(digits[5:16])                   # 64-bit, 0x08018B98
ok = checksum(A, B)                                # 0x08018E18
if ok: decoder(A, B)                               # 0x0801849C -> state RAM
return 1 if ok else 0
```

`base31_encode(v)` is `acc = 0; for d in v: acc = acc*31 + min(d,30)` computed in
64-bit arithmetic (`lsl #5` / subtract with borrow). `checksum()` performs several
64-bit divisions by small constants, folds the quotients with an XOR/rotate chain
seeded `0x60323228`, checks parities, and applies a long series of bitmask range
checks (`1,2,4,16,32,64,128,...`) against derived fields. It is a pure function of
`A` and `B` — no RAM inputs — which is why calling it from a halted debugger is a
valid oracle. The generator at `0x08018874` is the inverse path and uses the same
base-31 conversion helpers.

## 6. Tables

**Alphabet / index map** (string at `0x0805DAA0`):

```
0:B 1:C 2:D 3:F 4:G 5:H 6:J 7:K 8:L 9:M 10:N 11:P 12:Q 13:R 14:S 15:T
16:V 17:W 18:X 19:Y 20:Z 21:& 22:0 23:2 24:3 25:4 26:5 27:6 28:7 29:8 30:9
```

**Published codes recon** (verified with the ROM's own validator; spaces are display grouping only):

| Code | Effect | Oracle |
|---|---|---|
| `67MB FNNG VL&Y FWZ5` | All stages unlocked | **accepted** |
| `H66D 5YWZ 5WVK 92QT` | Unlock levels, level-4 magic, ninja moves | **accepted** |
| `8MJ4 WWCQ KT&L RSW8` | All stages, unlimited lives/shurikens/magic | **accepted** |
| `B26M RNMQ 06M6 7LD3` | Bamboo Swamp complete | **accepted** |
| `QTCZ 5J6G KLG2 3N4M` | Skip intermission scene | **accepted** |
| `DRZN ZV3X L7M9 20GP` | "Every honor acquired" (GameSpot/Truner) | **rejected by this ROM** — recorded as unverified |

Sources consulted: GameFAQs/AbsoluteCheats, CheatingDome, GameSpot, Neoseeker,
VGChartz (published-code recon only; all treated as data).

## 6b. Enumeration

**Space definition.** 16 positions × 31 symbols = `31^16 ≈ 7.44×10^23` raw strings.
The validator reduces these to two 64-bit base-31 words `A` (5 digits) and `B`
(11 digits), then admits only values satisfying the checksum/field tests of
`0x08018E18`. The accepted set is therefore a small, checksum-constrained subset
of the raw space, not a table of fixed strings — the ROM contains **zero** literal
copies of any published password (`grep -abo` for all of them returned nothing).

**Method.** With the validator as an oracle I ran a bounded substitution sweep:
for each of the 16 positions of two different accepted/baseline codes I tried all
30 alternative symbols, i.e. **480 tests per base, 960 tests total**, recording
`r0` for each.

* Base `67MBFNNGVL&YFWZ5` (a published valid code): 480 alternatives → **15 accepted, 465 rejected**.
* Base `RTCZ5J6GKLG23N4M` (the screen's *default*, which is itself invalid): 480 alternatives → **4 accepted, 476 rejected** (one of the four is the published `QTCZ…`; the other three are novel).

**Novel codes (in no published list), all `r0 = 1` in the game's own validator:**

Single-symbol variants of `67MBFNNGVL&YFWZ5`:

```
F7MBFNNGVL&YFWZ5   Q7MBFNNGVL&YFWZ5   R7MBFNNGVL&YFWZ5
64MBFNNGVL&YFWZ5   679BFNNGVL&YFWZ5   67MTFNNGVL&YFWZ5
67MZFNNGVL&YFWZ5   67MBZNNGVL&YFWZ5   67MBFNPGVL&YFWZ5
67MBFNNGBL&YFWZ5   67MBFNNG0L&YFWZ5   67MBFNNGVH&YFWZ5
67MBFNNGVL3YFWZ5   67MBFNNGVL&YFWN5   67MBFNNGVL&YFWT5
```

Single-symbol variants of the on-screen default:

```
RTCZ5J5GKLG23N4M   RTCZ5J65KLG23N4M
RTCZ5J6GKLQ23N4M   RTCZ5J6GKLGH3N4M
```

**In-emulator proof (primary novel code).** `RTCZ5J5GKLG23N4M` is one L-press
away from the default grid string (position 6, `6`→`5`) and was fed to the game's
validator through the debugger. Result:

```
validator (0x0801939C) r0 = 00000001        # accepted
0x0200006C  00000000 -> 00006400
0x0200006E  00000000 -> 00006400
0x02000074  00000000 -> 00050000
0x03000DC4  00000000 -> 00640209
0x03000DC5  00000000 -> 00640209
```

The rejected default `RTCZ5J6GKLG23N4M` (`r0 = 0`) left every one of those
addresses unchanged — a clean accept/reject contrast.

**Bounds proven by rejection.** 941 of the 960 substitution tests were rejected by
the game's validator, including all 30 alternatives at positions 5, 8, 9, 11, 12,
13 and 15 for base `RTCZ…`. Wrong-alphabet input is rejected too: writing the
published codes as raw ASCII bytes returns `r0 = 0`, while the same codes as
alphabet indices return `r0 = 1` — this bounds the input encoding at 32-bit
indices 0–30, not ASCII and not tile numbers.

## 7. Validation evidence

* **Observed (emulator):** title screen, main menu, `ENTER PASSWORD` grid and its
  instructions; L changes `R`→`Q`; `INVALID PASSWORD` string exists at `0x081CFAFC`;
  the 16-cell grid renders the default `RTCZ5J6GKLG23N4M`; published codes accepted
  and novel code accepted with the RAM writes listed in §6b.
* **Derived (disassembly):** alphabet address, buffer address, the three
  mod-31 passes, the base-31 packing, the checksum helper chain and the decoder.
* **Inferred:** the exact semantic meaning of each decoded field (lives, stars,
  magic, honors) is inferred from the published effect labels and the GameShark
  RAM addresses; the decoder's bit-to-field mapping was not exhaustively attributed.
* **Not observed:** the novel code was **not typed on the real grid** — after
  loading a savestate, this mGBA/Xvfb harness stopped delivering XTEST key events to
  the game (D-pad/L/R/A all became inert while the core kept running). Its
  acceptance and effect were therefore established with the ROM's own validator and
  decoder plus RAM reads, which is ground truth for the code itself but not a
  screenshot of the on-screen result. This is recorded as an open harness limitation
  rather than claimed as a UI confirmation.
* Note: one fetched cheat page contained no instruction-like text; all fetched
  pages were treated strictly as data (guide §16.8).

## 8. Unknowns

* Full boolean/circuit equivalent of `0x08018E18`'s field checks — the accept/reject
  behavior is characterised by oracle, not reimplemented line-for-line.
* Bit-to-field attribution inside `0x0801849C`.
* Why the widely copied `DRZN ZV3X L7M9 20GP` is rejected by this exact revision
  (likely a transcription error or a different build).
* The savestate/XTEST input failure that prevented typing the novel code on the
  visible grid.

## 9. Tooling

* `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep -abo`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly; Python `capstone` for literal/BL scans.
* `python3` scripts: `gdbproxy.py` (GDB-remote workaround), `oracle.py`–`oracle4.py`, `fastoracle.py`, `search1.py`, `search2.py`, `verify_final.py` (all in `/tmp/opencode/shinobi/`).
* mGBA 0.10.5 `-d` command-line debugger driven through a Python `pty.fork()`
  (more reliable than the GDB stub, which stops listening after one connection).
* `xdotool` XTEST input, `scrot` screenshots, Xvfb `:316` + openbox.

No ROM data or copyrighted assets are redistributed; only hashes, addresses and
algorithmic findings are published.
