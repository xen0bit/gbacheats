# Ultimate Winter Games (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ultimate Winter Games/Ultimate Winter Games.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `UWINTERGAMES` |
| Game code / maker | `BUWE5M` / `5M` (Telegames), rev `0x00` |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0` (no cracktro/trainer) |
| MD5 | `7d8682e1193f8c6d1b0eb9e182d3165e` |
| SHA-1 | `90368346c52ec8cdbd134d370839de158a135eeb` |
| SHA-256 | `cb762391e4523b12be10295e50cae9695c3b12565b7512df9d52f063898bc0a3` |

## 2. Executive summary

The game has a real, developer-intended **8-digit numeric password system** on the main menu
(`Enter Password`). It is algorithmic, not a lookup table. The keypad offers only `1`–`9`
(9 symbols, values 0–8 in base 9); `0` does not exist as an input. Eight digits are packed
base-9 into a 26-bit integer `P`, XORed with the constant `0x000E5534`, divided by four
with a 2-bit packaged checksum, and then unpacked into five independent state fields:
`A` (difficulty, 0–2), `F` (sport, 0–2), `e` (track index, 1–9), and two free decimal
digits `b`, `c`, `d` (0–9 each) that seed the three per-tournament record slots.

The validator accepts **exactly 81,000 of the 43,046,721 possible 8-digit strings**:
`3 (A) × 3 (F) × 9 (e) × 10 (b) × 10 (c) × 10 (d)`.
This count was proven by running a bit-exact C reimplementation over the entire input
space and by dynamic confirmation of accepted and rejected codes.

No published password list exists for this SKU: the GameFAQs cheats page for game
`925079` is empty ("Know Something We Don't?"), and TCRF returns 403. Every code
reported below is therefore novel. Several generated codes were entered on the real
in-game screen, accepted, and verified by both screenshot and savestate RAM diff.
No button code or hidden debug menu was found (bounded negative, §8).

## 3. How to reproduce

* Emulator: `/usr/local/bin/mgba` 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`,
  `mgba -3 -t pw.ss1 <rom>` (the state file boots straight to the password screen).
* Keymap (mGBA SDL default): A=`x`, B=`z`, arrows = D-pad. Hold ~80–150 ms per press.
* Menu path: boot → title → **A** → main menu → **Left ×3** to `Enter Password` → **A**.
* On the keypad, navigate the 3-column grid 1-2-3 / 4-5-6 / 7-8-9 / OK with the arrows
  and press **A** on each digit, then on **OK**. Index map: 0–8 = digits 1–9, 9 = OK.
* Reject path: after OK the screen fades to black and returns to the main menu
  (`Practice` selected). Accept path: a tournament banner is shown; **A** starts the event.
* Codes confirmed in-game (all absent from every published list):

| Code | Payload | Observed banner / effect |
|---|---|---|
| `12532261` | A0 F0 (ski) e1 b4 c3 d2 | Skiing Track 2 Tournament, Time Limit 01:17:00; **A** starts Skiing Track 2 |
| `12294659` | A0 F1 (snowboard) e1 b4 c3 d2 | Snowboard Track 2, Time 01:30:00, Score 600 |
| `12294654` | **A1** F1 e1 b4 c3 d2 | Snowboard Track 2, Time 01:34:00, Score 400 |
| `11624123` | A0 F2 (bobsled) e9 b6 c7 d8 | Bobsled Track 10, Time 01:10:00 |

## 4. Address map

All addresses are ROM (`0x08…`) unless marked RAM. File offset = address − `0x08000000`.

| Address | Meaning | Evidence |
|---|---|---|
| `0x0800E39C` | Password-screen/validator function (prologue `push {r4-r7,lr}`), called from `0x0801CB8` | Derived (disassembly + BL xref) |
| `0x0800E50A` | A-key handler: digit append (`char = index + 0x31`) or OK submit | Derived |
| `0x0800E532` | 8-char pack loop: `r5 = r5*9 + (char-0x31)`, 8 iterations | Derived |
| `0x0800E54A` | XOR with literal `0x000E5534` (`0x0800E6F8`), sign test | Derived |
| `0x0800E556` | `q = X>>2` (arithmetic), `r = X - 4q` | Derived |
| `0x0800E5D2` | Checksum: `(q*123) % 4 == r` (0x7B multiplier, signed-mod idiom) | Derived |
| `0x0800E562`–`0x0800E5CC` | Field unpack via `/3`, `/10` helpers at `0x08015814` (div) and `0x080158A8` (mod) | Derived |
| `0x0800E624`–`0x0800E680` | Accept path: write globals, set unlock flag, printf `%d %d - %d %d %d` | Derived + RAM diff |
| `0x0800E5E6` | Special debug literal check `strncmp(buf, "1 5 9 6 3 5 7", 13)` (helper `0x08015B40`) | Derived |
| `0x0800E5F6` | Reject path: error sound + `printf("illegal password: %d %d %d\n")` | Derived |
| `0x0800E6F4`/`F8`/`FC`/`700` | Literal pool: `"x x x x x x x x"`, `0xE5534`, `"1 5 9 6 3 5 7"`, `"illegal password: …"` | Derived (verified with `struct.unpack_from`) |
| `0x087BB210` | 16-byte initial keypad buffer template `"x x x x x x x x\0"` | Derived |
| `0x087BB220` | Debug literal `"1 5 9 6 3 5 7"` | Derived |

RAM globals (written only on the accept path — confirmed by savestate diff `pw.ss1` → `after2.ss1`):

| RAM | Field | Before → after (code `11624123`) |
|---|---|---|
| `0x02001E88` | sport `F` (0 ski, 1 snowboard, 2 bobsled) | `5` → `2` |
| `0x02001E64` | `e+1` = track number | `10` → `10` (e=9; other test `e=1`: `10` → `2`) |
| `0x02001EDC` | difficulty `A` | `1` → `0`; with code `12294654`: `0` → `1` |
| `0x0202BDA4` | tournament-unlock flag | `0` → `1` |
| `0x03004C60/64/68` | three record slots seeded with `d`, `c`, `b` | `0,0,0` → `8,7,6` |
| `0x03006F04` | pointer written by the special "1 5 9 6 3 5 7" path | unchanged (`0xAA`) in our tests |

Savestate layout used for the diff: mGBA `.ss1` PNG → zlib `gbAs` chunk (397,312 bytes);
EWRAM `0x02000000` maps to state offset `0x21000`, IWRAM `0x03000000` to `0x19000`.

## 5. Algorithm

```python
XOR = 0xE5534
# input: 8 chars c[0..7], each '1'..'9'; value v = ord(c)-0x31, so v in 0..8
P = sum(v[i] * 9**(7-i) for i in range(8))
X = P ^ XOR
if X < 0: reject                       # never triggers for an 8-digit input
q, r = X // 4, X % 4
if r != (q * 123) % 4: reject          # 2-bit checksum
A = q % 3
t = q // 3
b = t % 10; t //= 10
c = t % 10; t //= 10
d = t % 10; t //= 10
e = t % 10; t //= 10
F = t % 3;  t //= 3
if t != 1: reject                      # final quotient must be exactly 1
if e == 0: reject                      # track 1 cannot be granted
accept(A, F, e+1, b, c, d)
```

Encoder (inverse, used for every code in this report):

```python
def mint(A, F, e, b, c, d):
    q1 = (3 + F)*10000 + e*1000 + d*100 + c*10 + b   # e in 1..9
    q  = 3*q1 + A
    r  = (q * 123) % 4
    X  = 4*q + r
    P  = X ^ XOR
    return ''.join(str(digit + 1) for digit in base9_8(P))
```

`base9_8(P)` returns the eight base-9 digits of `P`, most significant first; every
digit is 0–8, so adding 1 always yields a keypad-reachable `'1'..'9'`.

## 6. Tables

* Input alphabet: exactly `123456789` (9 symbols; decoded value = char − 1). Length 8, fixed.
* `A` = `q mod 3` (0–2): difficulty; observed to change the per-track time/score limits
  (Snowboard Track 2: A0 → 01:30:00 / 600; A1 → 01:34:00 / 400).
* `F` = field after the four `/10` stages, mod 3 (0–2): 0 = Downhill Skiing,
  1 = Snowboarding, 2 = Bobsled. Curling is **not** reachable through this field.
* `e` = fourth decimal digit (1–9 after rejection of 0); `e+1` = track number 2–10.
  The per-track time/score limits vary with `e` (Snowboard: e1 01:30:00/600,
  e3 01:32:00/1000, e7 01:31:00/4000) — table-driven, not a simple linear formula.
* `b`, `c`, `d` = the three low decimal digits (0–9); written into the three record
  globals as `d`, `c`, `b`; they do not change the displayed banner limits.
* Debug literal `"1 5 9 6 3 5 7"` (strncmp n=13 at `0x0800E5E6`): sets
  `*[0x03006F04] = buf[14]*60 - 2896` then deliberately reports an illegal password;
  entered as `15963579` it returned to the main menu (rejected).

## 6b. Enumeration

**Space size.** Raw input space = 9^8 = **43,046,721** strings. The accepted set is
**81,000** strings (0.188 %), i.e. `3×3×9×10×10×10`. Every accepted string corresponds
bijectively to one `(A,F,e,b,c,d)` tuple; there are no aliases in the accepted set.

**Closure proof (§16.9).** `enum.c` (in `/tmp/opencode/wintergames/enum.c`) runs the
bit-exact validator over all 43,046,721 integers `P` in 0.2 s:

```
space=43046721 accepted=81000 badCs=32285041 badQ6=10671680 badE=9000 nonzeroA=54000
F=0 count=27000   F=1 count=27000   F=2 count=27000
e=1..9 count=9000 each
```

`badCs`, `badQ6` and `badE` are the three rejection layers (checksum, final quotient,
track-zero) and their counts sum exactly to the rejected space. `nonzeroA=54000`
documents that A is a genuine 3-valued field, not a constant — an early draft of the
decoder wrongly assumed `q` was always divisible by 3; the C sweep caught it.

**Novel codes (none appears in any published list; GameFAQs' cheats page is empty).**
All were typed on the real Enter Password screen and accepted:

| Code | A | F | e | b,c,d | Screenshot | In-game result |
|---|---|---|---|---|---|---|
| `12532261` | 0 | 0 | 1 | 4,3,2 | `after_code1_c.png`, `after_start2_c.png` | Skiing Track 2 tournament; event launched (screenshot of live slalom) |
| `12294659` | 0 | 1 | 1 | 4,3,2 | `F1test_c.png` | Snowboard Track 2, time 01:30, score 600 |
| `12294654` | 1 | 1 | 1 | 4,3,2 | `A1code_c.png` | Snowboard Track 2, time 01:34, score 400; RAM `0x02001EDC` = 1 |
| `11624123` | 0 | 2 | 9 | 6,7,8 | `ramtest2_c.png` | Bobsled Track 10, time 01:10; RAM diff below |
| `12284463` | 0 | 1 | 3 | 4,3,2 | `e3_c.png` | Snowboard Track 4, time 01:32, score 1000 |
| `11874818` | 0 | 1 | 7 | 4,3,2 | `e7_c.png` | Snowboard Track 8, time 01:31, score 4000 |

**Bounds proven by in-game rejection** (each from a clean `-t pw.ss1` boot; pre-entry
screen verified by screenshot):

1. *Wrong checksum* — `12532262` (valid `12532261` with last digit incremented):
   black fade → main menu, no banner (`badcs2_pre.png`, `badcs2_late_c.png`).
2. *Valid checksum, out-of-range field* — `12213265` (A0 F1 **e0** b4 c3 d2, checksum
   recomputed): rejected to main menu (`e0clean` / `e0late_c.png`). This proves the
   `cmp r7,#0` range gate at `0x0800E628`, i.e. track 1 is unattainable by password.
3. *Debug literal* — `15963579` (prefix `1 5 9 6 3 5 7`): rejected to main menu
   (`spec2late_c.png`), proving the special path is not a cheat code.
4. *Unrepresentable sport* — F=3 (curling) cannot be encoded: F is `t mod 3`, so the
   encoder's F domain is exactly {0,1,2}; the C sweep confirms 27,000 accepts per F
   and none for any fourth sport.

**RAM proof of effect** (savestate diff `pw.ss1` vs `after2.ss1`, code `11624123`):
`0x02001E88: 5→2`, `0x02001EDC: 1→0`, `0x0202BDA4: 0→1`,
`0x03004C60/64/68: 0/0/0→8/7/6`, `0x02001E64` stays 10 because e=9 was already set.
With `12294654` the same diff gives `0x02001EDC = 1` (A=1) and `0x02001E64 = 2`.

## 7. Validation evidence

* **Observed** (emulator): boot, all seven main-menu entries, password screen, keypad
  navigation, six accepted codes and three rejected codes, event launch, RAM savestate diffs.
  Screenshots are in `/tmp/opencode/wintergames/*.png`.
* **Derived** (disassembly): validator arithmetic, helper identities (`0x08015814` = signed
  divide, `0x080158A8` = signed remainder, `0x08015B40` = strncmp), literal pool, global writes.
* **Inferred**: field *names* "difficulty" for A and "record seed" for b/c/d are inferred
  from the written globals and observed limit changes; exact per-(sport,track,A) limit
  table was not fully disassembled. The banner prints the debug line
  `%d %d - %d %d %d` (F, e, d, c, b) over the emulator debug console.

## 8. Unknowns / bounded negatives

* **Button codes / hidden debug menus: bounded negative.** The seven reachable main-menu
  entries were walked (`mw1.png`–`mw9.png`: Practice, Credits, Options, Enter Password,
  Link Mode, 2 Player Duel, Championship — cycle length 7). `strings -t x` over all 8 MiB
  found no button-code/debug-menu labels; the only debug leftovers are the password
  validator's `illegal password` / `char not found` strings, both reached only on the
  password screen. No L+R / Start+Select gate was observed. Curling has no password path.
* **No published code list exists** for this SKU (GameFAQs 925079 cheats page empty;
  TCRF 403), so there is no external list to cross-check; verification rests on the ROM
  validator plus in-game acceptance.
* Exact per-(sport,track,A) time/score limit tables were treated as game data and not
  fully reversed; only the sampled entries in §6 are claimed.
* Gameplay screens beyond the first seconds of Skiing Track 2 were not exhaustively walked.

## 9. Tooling

* `strings -t x`, `grep -abo`, `xxd`, `arm-none-eabi-objdump -M force-thumb`, Python
  (`struct`, `zlib`) for pointer/literal xrefs and savestate diffs.
* `/tmp/opencode/wintergames/genpw2.py` — bit-exact encoder used to mint all codes.
* `/tmp/opencode/wintergames/enum.c` — full 43,046,721-input validator sweep.
* `/tmp/opencode/wintergames/enter.py`, `batch.py`, `clean.py`, `kg.py` — Xvfb/xdotool
  drivers (BFS over the keypad grid, clean state reloads, screenshots).
* mGBA `-g` GDB stub was tried but proved unreliable (stale listener on 2345 owned by
  another session; detach left the target halted), so RAM evidence used savestate diffs.

**Legal note:** no ROM bytes or copyrighted assets are reproduced here — only hashes,
addresses, algorithms, and findings.
