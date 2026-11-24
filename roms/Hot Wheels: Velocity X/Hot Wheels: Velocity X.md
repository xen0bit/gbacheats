# Hot Wheels: Velocity X (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Hot Wheels: Velocity X.gba` (8,388,608 bytes / 8 MiB) |
| Header title | `HOT WHEELS V` |
| Game code | `AH8E`; maker `78`; version `0` |
| Entry word | `0xEA00002E` — stock `b 0x080000C0` (no cracktro patch) |
| Nintendo logo | exactly one hit, file offset `0x4` → single retail image, no multiboot/multi-header, no appended trainer |
| Fixed `0x96` / complement | `0x96` present at `0xB2`; complement `0x93` at `0xBD`; header checksum word `0x0000` |
| MD5 | `5ea3eec1d71c05f46321ce090ca791ee` |
| SHA-1 | `e6a3ae1e4a58e47c78719a7f6a7e1ed0c37b34e6` |
| SHA-256 | `8ed33b088d3c1df517597fb5a725dbfc2e520dc3c1e9539e09a06f9dbc89ae16` |

Conclusion of Phase 0: clean single retail GBA image, no ROM patch or trainer detected.

## 2. Executive summary

The game has a **developer-intended numeric password system** on the main menu (`PASSWORD`).
Passwords are **8 digits, each 1–9** (displayed `NNN-NN-NNN`); digit `0` does not exist on the
keypad and no published code uses it. The validator is a compact algorithmic decoder at
`0x080401D8` — there is **no plaintext code table** in the ROM (all published literals were
searched as ASCII, packed BCD and u32/u64 and were absent).

The decoder packs the 8 base-9 digits into a 26-bit accumulator, runs a 200-byte
bit-twiddling transform (rotate / bit-swap / bit-flip / add, 40 rounds), then checks
`code == ((popcount(code & 0x1FFFFF) & 0xF) << 21) | (code & 0x1FFFFF)`, a 4-bit checksum over
a 21-bit payload. It additionally enforces `level = (code>>15)&0x3F <= 37` and reserves
payload bits 4, 7, 10 and 13 (must be zero).

**Complete space: 9^8 = 43,046,721 possible inputs; exactly 77,824 accepted passwords =
38 levels × 2^11 flag combinations.** Every accepted code writes an 11-bit unlock bitfield
to `0x03005A90` (bits 4/7/10/13 excluded) and the level to `0x03005AC0`.

All 40 published codes were verified against the ROM: **37 are valid; 3 are published
typos** with clean one-digit corrections (§6). A **novel code absent from every published
list**, `783-28-788` (`78328788`), was generated from the validator, accepted in the
emulator, and its exact predicted flags/level were read back from RAM. Bounds were proven
by three in-game rejections (bad checksum, level 38, reserved bit set).

## 3. How to reproduce

* Emulator: `mgba -3 <rom>` under Xvfb on `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`.
* Keymap (mGBA SDL defaults): D-pad = arrows, A = `x`, B = `z`, Start = `Return`,
  Select = `BackSpace`. Hold ~100–150 ms per press.
* Menu path: boot → Start → **MAIN** → down ×3 → **PASSWORD** → navigate the 3×3 keypad
  (1–9) with the D-pad, press **A** for each digit, then press **Start** to submit.
  Eight digits must be entered; the display updates left-to-right.
  **Allow ~2.5 s after opening the screen** — entering during the fade silently drops the
  first digit.
* Verified inputs (typed as 8 digits):
  * `72383462` ("unlock everything", published) → accepted, flags `101101101101101`, level 37.
  * `78328788` (novel) → accepted, flags `000000000000001`, level 7.
  * `71589439` (reserved bit 4) → rejected; `16351739` (level 38) → rejected;
    `82383462` (bad checksum) → rejected.
* RAM reads used mGBA savestates (`Shift+F1..F9`), decompressing the PNG `gbAs` chunk with
  `zlib.decompress`; state offsets (8 MiB image): IWRAM at `0x19000`, so
  `flags = raw[0x1EA90:0x1EA9F]`, `digits = struct.unpack_from('<8I', raw, 0x1EAA0)`,
  `level = struct.unpack_from('<I', raw, 0x1EAC0)`.

## 4. Address map

| Item | ROM / RAM | Evidence |
|---|---|---|
| Password validator (entry) | `0x080401D8` | derived: BL caller at `0x08028778`; 37 published codes + novel code reproduced |
| Checksum helper | `0x08040188` | derived from disassembly |
| `swapbits(a,b,c)` | `0x080400B8` | derived |
| `flipbit(a,b)` | `0x08040114` | derived |
| `addmod(a,b)` (mod 2^25) | `0x08040138` | derived |
| `submod(a,b)` (inverse, unused here) | `0x08040160` | derived |
| Transform table (200 bytes) | `0x0807B5D8` | derived; literal at `0x080402BC` |
| Round count (`200`) | `0x0807B6A0` | derived; literal at `0x08040234` |
| Literal → digit buffer | `0x0804021C` holds `0x03005AA0` | derived |
| Literal → flag bytes | `0x08040314`, `0x08040330`, `0x08040358` hold `0x03005A90` | derived |
| Literal → level word | `0x08040370` holds `0x03005AC0` | derived |
| UI strings | `0x08056630C` "Password", `0x080566418` "PASSWORD" | `strings -t x` |
| **Digit buffer** | IWRAM `0x03005AA0` — 8 × u32, values 1–9 | observed (savestate diff `12317543` → `98765432`) |
| **Unlock flags** | IWRAM `0x03005A90` — 15 bytes (0/1) | observed (published + novel codes) |
| **Level word** | IWRAM `0x03005AC0` — u32 | observed (0 → 7 / 37 / 14) |

## 5. Algorithm

```python
MASK25 = 0x1FFFFFF

# 1. digits -> base-9 accumulator (MSB first)
acc = sum((d[i]-1) * 9**(7-i) for i in range(8))      # 0 .. 9^8-1

# 2. 40-round transform; table T = 200 bytes at 0x0807B5D8, n = 200
def rotl25(x,a): return ((x<<a)|(x>>(25-a))) & MASK25
def swapbits(x,b,c):
    bb,cc = (x>>b)&1, (x>>c)&1
    return (x & ~((1<<b)|(1<<c))) | (bb<<c) | (cc<<b)
code = acc & MASK25
n = 200
while n > 0:
    n -= 1
    code = rotl25(code, T[n])                 # rotate left by T[n], mod 2^25
    code = swapbits(code, T[n-1], T[n-2])     # exchange two bits
    n -= 2
    code ^= (1 << T[n-1]); n -= 1             # flip bit T[n-1]
    code  = (code + T[n-1]) & MASK25; n -= 1  # add T[n-1] mod 2^25

# 3. 4-bit checksum over the low 21 bits
low  = code & 0x1FFFFF
chk  = ((bin(low).count('1') & 0xF) << 21) | low
if code != chk:                      return REJECT   # no RAM writes
level = (code >> 15) & 0x3F
if level > 37:                       return REJECT   # no RAM writes

# 4. write 15 flag bytes (note: happens BEFORE the reserved-bit check)
for i in range(15): flags[i] = (code >> i) & 1
if any(flags[i] for i in (4,7,10,13)): return REJECT  # flags remain written

level_word = level
return ACCEPT
```

Inverse: each of the four operations is invertible (rotate right, same bit swap,
same bit flip, subtract mod 2^25), so applying the 40 groups in reverse order maps any
valid 25-bit `code` back to a unique `acc`. Since `2^25 < 9^8`, every 25-bit accumulator
is representable as eight 1–9 digits — hence exactly one password per accepted code.

Working reimplementation: `/tmp/hwvx/pw.py` (Python) and `enum.c` (C enumerator).

## 6. Tables

**Input alphabet:** `1 2 3 4 5 6 7 8 9` (keypad only; base-9, `0` unreachable).
**Payload layout of the 25-bit `code`:**

| Bits | Meaning | Domain / constraint |
|---|---|---|
| 0–14 | 15 flag bytes → `0x03005A90` | 11 usable bits (0,1,2,3,5,6,8,9,11,12,14); 4,7,10,13 reserved = 0 |
| 15–20 | `level` → `0x03005AC0` | 0–37 (38 values); 38–63 rejected |
| 21–24 | checksum | `popcount(bits 0–20) & 0xF` |

**Published codes verified in the ROM model (all 8-digit strings):**

| Effect (published label) | Code | Decoded level | Decoded flags (bits 14→0) |
|---|---|---|---|
| Unlock all cars | `49693993` | 37 | `111101101101101` |
| Unlock everything | `72383462` | 37 | `101101101101101` |
| Secret cars / story | `44687224` | 33 | `101101101101101` |
| Levels 2–5 | `14324813`, `14138985`, `24948723`, `29416277` | 1–4 | all zero |
| Levels 6–29 | `45751438` … `64118239` | 5–28 | `100000000000000` |
| Levels 30–38 | `39968584` … `78257387` | 29–37 | `100001001000000` |

**Published typos found (all one digit off, corrections validated by the decoder and the
corrected level-15 code re-entered in-game):**

| Published (rejected) | Corrected | Published label | Decoded internal level |
|---|---|---|---|
| `37362927` | `37362937` | level 15 | 14 |
| `47868254` | `47866254` | level 18 | 17 |
| `47758369` | `44758369` | level 26 | 25 |

Note: the GBA SKU has **no** `SMASHMOUTH` code — that literal belongs to the 2-in-1
Double Pack listing and is absent from this 8 MiB standalone image under every encoding
tried (§16.11). Gamecube-link unlock strings in the text bank are console features absent
from the GBA build.

**Menus walked (Observed):** MAIN (STORY MODE, RACE MODE, CHALLENGE, PASSWORD, DATABASE,
OPTIONS), PASSWORD keypad, DATABASE (car records, "1 of 30"), CHALLENGE (Level/Battle/Tag
missions, "CHALLENGE!!"), RACE MODE settings (RACERS / LAPS / LEVEL / DIFFICULTY), mission
/pause overlays ("Game Paused", "Press Start to Return to Game", "Press Select to Quit
Mission"), OPTIONS (CONTROL, MUSIC, SOUND, MUSIC TEST, SOUND TEST, DIFFICULTY). The two
`* TEST` entries are developer audio-test screens and are not cheat-related. No separate
hidden "cheat menu" screen exists. UI text is plain ASCII (`strings`); the password
display and keypad digits are tile-indexed, decoded here via the u32 RAM buffer rather
than by glyph tables.

## 6b. Enumeration

* **Input space** = `9^8 = 43,046,721` 8-digit strings.
* **Accepted space** = `38 levels × 2^11 flag combinations = 77,824` passwords
  (enumerated exhaustively in `enum.c`; full list written to `all_codes.txt`).
  The screen's default display `123-17-543` is itself a valid level-0 / no-flags code.
* **Novel code (not on 3rd party cheat indexes):**
  `783-28-788` → `78328788`, derived by choosing `level=7`, flags `000000000000001`
  (only bit 14), recomputing the checksum and inverting the transform.
  In-game proof: RAM flags `000000000000001`, level word `7` (savestate `ss6`).
  Published level-8 code is `44765112`; no published list contains a bit-14-only code.
* **Additional generated codes** (decoder-valid, unpublished):
  `25725867` (level 11, flags bits 2+11), `36562218` (level 0, all 11 flags),
  `37362937` / `47866254` / `44758369` (corrected published typos).
* **Bounds proven by in-game rejection:**

| Input | Intended violation | Observed RAM |
|---|---|---|
| `82383462` | bad 4-bit checksum | flags all 0, level 0 — rejected, no writes |
| `16351739` | level field = 38 (>37) | flags all 0, level 0 — rejected at level check |
| `71589439` | reserved payload bit 4 set | flags `000010000000000`, level 0 — flags written, then rejected; level not written |

## 7. Validation evidence

* **Observed** (emulator/savestate): keypad entry flow; `72383462` → flags
  `101101101101101` + level 37; novel `78328788` → flags `000000000000001` + level 7;
  `37362937` → flags `100000000000000` + level 14; all three rejection rows above;
  default display `12317543` and digit-buffer RAM contents.
* **Derived** (disassembly + bit-exact reimplementation): validator `0x080401D8`,
  helpers, 200-byte table/round count, all literal pointers, base-9 packing, checksum and
  constraints. The model reproduces 37/37 valid published codes, rejects the 3 typos,
  and its predicted flags/level match the emulator for every accepted code tested.
* **Inferred** (not individually exercised): exact semantic labels of each of the 11 flag
  bits. The bit pattern comparison strongly suggests bit 1 is the extra "all cars" flag
  (it is the only difference between the "all cars" and "unlock everything" codes) and
  bits 5+8 correlate with the late-story level codes, but no single-bit code was mapped to
  a specific car/challenge/gadget unlock on screen.

## 8. Unknowns

* Per-flag semantics (which specific car, challenge, gadget or stunt each of the 11 bits
  unlocks) were not individually attributed; the bitfield itself and its RAM destination
  are proven.
* No button-code table or debug gate was found on the title/options screens beyond the
  two audio `* TEST` options entries; a static key-mask search and a live menu walk found
  no separate hidden cheat screen. (This is a bounded negative over the ASCII/tile text
  bank and the reachable menus, not a claim about every possible runtime state.)
* Header checksum word is `0x0000` and the complement byte does not satisfy the usual
  retail check; no functional difference was observed, and the stock entry word and
  single logo argue against a patched image.

## 9. Tooling

* `binutils-arm-none-eabi` (`arm-none-eabi-objdump -M force-thumb`), Python 3, GCC.
* `/tmp/hwvx/pw.py` — validator model + published-code check.
* `/tmp/hwvx/enum.c` — exhaustive enumerator (77,824 codes).
* `/tmp/hwvx/ui.py`, `ocr.py`, `testcode.py` — input, screen capture/OCR and
  savestate-RAM verification helpers.
* mGBA SDL `-3`, Xvfb `:316`, openbox, xdotool, scrot, ImageMagick, tesseract.
* Web sources consulted as **data only** (no instructions followed): 3rd party cheat indexes GBA cheats,
  3rd party cheat index cheat 8364/8025, 3rd party cheat indexes. No prompt-injection payload was
  encountered in the fetched pages.

**Legal note:** no ROM bytes, graphics, audio or game text are redistributed here; only
hashes, addresses, algorithms and derived codes are published.
