# Cartoon Network Speedway (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Cartoon Network Speedway/Cartoon Network Speedway.gba` |
| Size | 4,194,304 bytes (4 MiB, power-of-two padded) |
| MD5 | `b3f65540eea88983c63e454b34d3028e` |
| SHA-1 | `26afa157c527dcaa5a4fa0eccc772426156320d8` |
| SHA-256 | `d8e48a283fd0a813ecd85ba5992c035b562a256543b1246c7d14560d17270216` |
| Header title (0xA0) | `CN SPEEDWAY ` |
| Game code (0xAC) | `ANRE` |
| Maker code (0xB0) | `5G` |
| Version | 0 |
| Entry word (0x00) | `0xEA00002E` (stock `b 0x080000C0`) |
| Header complement (0xBD) | `0x7C` — valid: `-(sum(0xA0..0xBC)+0x19) & 0xFF` |
| Embedded GBA headers | 1 (Nintendo logo only at file offset 0x04) — single game, no multi-cart shell, no trainer |

The ROM is a stock, unpatched US retail image (DC Studios / Majesco, 2003). The
header checksum word at 0xBE is `0x0000`, which is normal for a rebuilt header;
the complement byte is correct and the entry branch is the stock crt0 branch, so
there is no cracktro or appended trainer (§16.1).

## 2. Executive summary

The game has a single in-game cheat surface: the **8-digit numeric password
system** on the main menu. There is no button code, no debug menu, no garage and
no save RAM (the cart uses passwords instead of a battery save).

The password is an 8-digit decimal number. Digit 0 is a checksum
(`sum(digits 1..7) mod 10`); the remaining 7 digits are a fixed permutation of
the decimal digits of a 21-bit payload `M` (`M < 2^21`). The validator is a
single Thumb function at `0x08015C94`; the generator is at `0x0800C42C`.

The accepted set is **exactly 2^21 = 2,097,152 codes** (proved by full
enumeration and round-trip). Every accepted code writes an 88-byte unlock
struct and a 12-bit item mask (`field30`) in EWRAM, and the caller also writes
12 score thresholds for any valid code.

A novel, unpublished code was minted and verified in the emulator:

- **`40052674`** → `M = 0x1F83FF` (all five 2-bit cup fields = 3, `r0` = 15,
  `field30 = 0xFFF`). It is not on GameFAQs, Cheat Happens, the Ed, Edd n Eddy
  wiki, or any other published list found. Entered on the real password screen,
  it is accepted, writes the unlock struct, and the Bonus Items → Characters
  screen shows all six character icons coloured (VRAM diff confirms the screen
  changed; RAM diff confirms `field30` 0x000 → 0xFFF).

Bounds were proved by rejection: a bad-checksum code (`00000001`) and an
out-of-range payload (`39999999`, `M = 9,999,999 ≥ 2^21`) are both rejected
and leave the unlock struct untouched.

## 3. How to reproduce

Environment: Debian/Ubuntu, `mgba-sdl` (`/usr/games/mgba`), `xvfb`, `xdotool`,
`scrot`, `python3`. Start a display and the emulator:

```bash
Xvfb :231 -screen 0 1024x768x24 &
DISPLAY=:231 openbox &
DISPLAY=:231 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 "Cartoon Network Speedway.gba" &
```

Default mGBA keymap: A = `x`, B = `z`, D-pad = arrow keys, Start = `Return`.
Hold keys 60–300 ms; long holds can double-step menus.

Menu path to the password screen:

1. Title screen → `Return` (Start).
2. Main menu has five icons: **Single Player, Two Player, Options, Bonus Items,
   Password**. Move with Left/Right, select with A.
3. **Password** → the "Enter Password" screen with 8 digit slots and an OK box.
4. Enter a code: **Up** increments the selected digit (0–9), **Right** advances
   to the next slot, **A** on OK submits, **B** goes back. (Down decrements,
   Left moves back.)
5. A valid code returns to the main menu and applies the unlocks; an invalid
   code stays on the password screen.

Codes tested in the emulator (all on the above screen):

| Code | Result |
|---|---|
| `10000010` | accepted; Cartoon Speedway trophy unlocks (observed on Bonus Items → Trophies) |
| `96981951` | accepted; `field30=0xFFF`, `b0..b4=1`, `r0=12`, `f10..f14=1` (RAM) |
| `34711154` | accepted; `field30=0x40E`, `b0..b4=1`, `r0=4`, `f10..f12=1` (RAM) |
| `40052674` | **novel**, accepted; `field30=0xFFF`, `b0..b4=3`, `r0=15` (RAM + screen) |
| `00000001` | rejected (bad checksum) |
| `39999999` | rejected (`M` out of range) |

A savestate at the password screen and the analysis scripts are in
`/tmp/opencode/cnspeedway/` (`cnspeedway_before.ss1`, `cns_model.py`,
`enter_code.py`, `key.py`).

## 4. Address map

All ROM addresses are `0x08000000 + file offset`. RAM addresses are GBA
addresses. The scene object pointer in the tested state was `0x03004AB4`; the
derived struct base `r3 = [scene+0x3334] = 0x02000974`.

| Object | Address | Notes |
|---|---|---|
| Password validator | `0x08015C94` (Thumb) | called from `0x0801610E` |
| Password screen UI handler | `0x08015E2C` (Thumb) | contains the submit path |
| Screen dispatch call to password handler | `0x0801AB62` | |
| Password generator (encoder) | `0x0800C42C` (Thumb) | called from `0x0800C60E`, `0x080100C0` |
| Digit de-scramble table (DEC) | ROM `0x083D47F7` (7 bytes) | copied to IWRAM `0x03003727` |
| Digit scramble table (ENC) | ROM `0x083D47F0` (7 bytes) | copied to IWRAM `0x03003720` |
| `SHIFT` table | ROM `0x080630FC` (16 × u32) | field30 bit positions |
| Score-threshold table | ROM `0x08062F08` (12 × u32) | written on any valid code |
| `sprintf` wrapper | `0x08029C70` (Thumb) | `vsprintf` at `0x0802A318` |
| `memcpy` veneer | `0x08029F64` → ARM `0x08029F68` | |
| `mod 10` | `0x0802BEE8` → ARM `0x0802BEEC` | magic `0x66666667` |
| Scene object | `0x03004AB4` (IWRAM) | global passed to decoder/encoder |
| Struct base `r3` | `0x02000974` (EWRAM) | `[scene+0x3334]` |
| Unlock output struct | `0x02000A70` (EWRAM) | `r3 + 0xFC`, 88 bytes |
| `field30` item mask | `0x020009A4` (EWRAM) | `r3 + 48`, u16 |
| Score thresholds | `0x020009B0 + SHIFT[i]*4` | `r3 + 60 + SHIFT[i]*4`, 12 u32 |

## 5. Algorithm

### 5.1 Validator (`0x08015C94`)

Input: `r0` = scene pointer, `r1` = integer code, `r2` = output struct pointer.
Returns 0 = invalid, 1 = valid.

1. `sprintf(buf, "%08d", r1)` (after a redundant `memcpy(buf, "%08d", 9)`).
2. `sum = Σ (buf[i]-'0')` for `i = 1..7`; `ck = sum % 10`
   (`0x0802BEE8`). If `buf[0]-'0' != ck` → return 0.
3. `sp[4*DEC[i]] = buf[i+1]-'0'` for `i = 0..6`, with
   `DEC = [5,1,3,0,2,6,4]`.
4. `M = Σ sp[4*(6-r)] * 10^r` for `r = 0..6` (a 7-digit decimal number).
5. If `M >> 21 != 0` → return 0.
6. Extract fields from `M` (below) and write the output struct and `field30`.
7. Return 1.

### 5.2 Payload layout (21 bits)

| Bits | Field | Meaning (observed/derived) |
|---|---|---|
| 0–1 | `b0` | cup/championship flag 0 (published codes use 1) |
| 2–3 | `b1` | cup/championship flag 1 |
| 4–5 | `b2` | cup/championship flag 2 |
| 6–7 | `b3` | cup/championship flag 3 |
| 8–9 | `b4` | cup/championship flag 4 |
| 10 | `f10` | extra flag |
| 11 | `f11` | extra flag |
| 12 | `f12` | extra flag |
| 13 | `f13` | extra flag |
| 14 | `f14` | extra flag |
| 15–18 | `r0` | 4-bit progress/index (published codes use 0,2–9,12) |
| 19 | `g1` | `field30` bit 1 |
| 20 | `g10` | `field30` bit 10 |
| 21+ | — | must be zero (range check) |

`field30` is built as: bit 1 from `g1`, bit 10 from `g10`, plus bits
`SHIFT[2..r0-1]` for `r0 > 2`, where
`SHIFT = [1,10,2,3,6,7,0,8,5,11,9,4,6,0,2,3]`.

### 5.3 Output struct (88 bytes at `r3+0xFC`)

| Offset | Value |
|---|---|
| `+0x00` | `b0` (u8) |
| `+0x01` | `b1` |
| `+0x02` | `b2` |
| `+0x03` | `b3` |
| `+0x04` | `b4` |
| `+0x06` | `r0` (u16) |
| `+0x08` | `b0 == 1` |
| `+0x0C` | `f10` |
| `+0x10` | `b1 == 1` |
| `+0x14` | `f11` |
| `+0x18` | `b2 == 1` |
| `+0x1C` | `f12` |
| `+0x20` | `b3 == 1` |
| `+0x24` | `f13` |
| `+0x28` | `b4 == 1` |
| `+0x2C` | `f14` |
| `+0x30` | `bit19 && bit20` |
| `+0x34` | `r0 >= 4` |
| `+0x38` | `r0 >= 6` |
| `+0x3C` | `r0 >= 8` |
| `+0x40` | `r0 >= 10` |
| `+0x44` | `r0 > 11` |
| `+0x48` | `b0 != 0` |
| `+0x4C` | `b1 != 0` |
| `+0x50` | `b2 != 0` |
| `+0x54` | `b3 != 0` |

### 5.4 Caller side effects (`0x0801610E`)

For any code that returns 1, the caller also:

- writes the 12 score thresholds from ROM `0x08062F08` to
  `r3 + 60 + SHIFT[i]*4` (values `4000,5000,6000,7000,8000,10000,12000,
  14000,16000,18000,20000,22000` in `SHIFT` order);
- sets up a dialog/message (the string `You have unlocked:` exists at
  `0x0800C354`, not referenced by a 32-bit pointer — likely a text-ID bank);
- returns to the main menu.

### 5.5 Generator (`0x0800C42C`)

Builds `M` from the save struct (`b0..b4`, `r0`, `f10..f14`, `field30` bits 1
and 10), then `sprintf(buf, "%07d", M & 0x7FF)`, scrambles the 7 digits with
`ENC = [3,1,4,2,6,0,5]`, and appends the checksum digit.

> **Note / discrepancy.** The generator masks the payload to 11 bits
> (`M & 0x7FF`) at `0x0800C4F2`–`0x0800C4F4`. That cannot reproduce the
> published codes, which use the full 21-bit `M`. The validator accepts the
> full 21-bit space. The correct inverse (used for the novel code below) is
> `encode(M)` with the full `M`; it reproduces every published code exactly.
> The mask may be a developer bug or a deliberately reduced "resume" code; it
> was not exercised end-to-end (see §8).

## 6. Tables

### 6.1 Digit tables

```
DEC = [5, 1, 3, 0, 2, 6, 4]   # ROM 0x083D47F7 / IWRAM 0x03003727
ENC = [3, 1, 4, 2, 6, 0, 5]   # ROM 0x083D47F0 / IWRAM 0x03003720
SHIFT = [1,10,2,3,6,7,0,8,5,11,9,4,6,0,2,3]  # ROM 0x080630FC
```

### 6.2 Published codes (GameFAQs + Ed, Edd n Eddy wiki)

| Code | `M` | `b0..b4` | `r0` | `f10..f14` | `field30` | Published effect |
|---|---|---|---|---|---|---|
| `10000010` | 1 | 10000 | 0 | 00000 | 0x000 | Cartoon Speedway trophy |
| `50000050` | 5 | 11000 | 0 | 00000 | 0x000 | ACME Axel Award trophy |
| `32000010` | 21 | 11100 | 0 | 00000 | 0x000 | Fender Bender Frenzy trophy |
| `52681314` | 1638421 | 11100 | 2 | 00000 | 0x402 | Johnny 2x4 |
| `38611791` | 1671189 | 11100 | 3 | 00000 | 0x406 | Edopolis |
| `25731079` | 1703957 | 11100 | 4 | 00000 | 0x40E | Down on the Farm / Muriel |
| `34711154` | 1711445 | 11111 | 4 | 11100 | 0x40E | All Five Championships Won |
| `12761357` | 1736725 | 11100 | 5 | 00000 | 0x44E | Farm Frolics |
| `98761719` | 1776981 | 11111 | 6 | 11100 | 0x4CE | Alpine Antics / Swanky |
| `84891097` | 1809749 | 11111 | 7 | 11100 | 0x4CF | Hot Rod Johnny |
| `81821475` | 1842517 | 11111 | 8 | 11100 | 0x5CF | Desert Drive / Little Suzy |
| `68851752` | 1875285 | 11111 | 9 | 11100 | 0x5EF | Scary Speedway |
| `96981951` | 1998165 | 11111 | 12 | 11111 | 0xFFF | Unlock Everything |
| `82010050` | 1025 | 10000 | 0 | 10000 | 0x000 | wiki: Cartoon Speedway championship password |

`38000050` (seen in a prior note, not on GameFAQs) decodes to `M = 85`
(`b0..b3 = 1`), consistent with "first four championships won", but is
recorded here as unverified against a primary list.

### 6.3 Score thresholds (written on any valid code)

`[4000, 5000, 6000, 7000, 8000, 10000, 12000, 14000, 16000, 18000, 20000,
22000]` at `r3 + 60 + SHIFT[i]*4`.

## 6b. Enumeration

- **Input space:** 8 decimal digits = 10^8 strings. The checksum digit is
  determined by the other seven, so 10^7 strings have a valid checksum.
- **Accepted set:** exactly the codes whose de-scrambled `M` is `< 2^21`.
  The digit permutation is a bijection on 7-digit strings, so the number of
  accepted codes equals the number of `M` in `[0, 2^21-1]`:
  **2,097,152 codes**.
- **Proof:** full enumeration of `M = 0 .. 2^21-1` with the reimplemented
  `encode`/`decode` gives 2,097,152 distinct codes and **0 round-trip
  mismatches** (`cns_model.py`). A random 200,000-code sample accepted 4,248
  and rejected 195,752, consistent with the 2^21/10^8 ratio.
- **Reserved bits:** bits 21+ of `M` must be zero; the only range check in the
  validator is `M >> 21 == 0`. There is no other semantic range check in the
  validator (out-of-range `r0`/`b` values are still accepted and written).

### Novel code

**`40052674`** — `M = 0x1F83FF` (2,065,407):

| Field | Value |
|---|---|
| `b0..b4` | 3,3,3,3,3 |
| `r0` | 15 |
| `f10..f14` | 0,0,0,0,0 |
| `g1`, `g10` | 1, 1 |
| `field30` | `0xFFF` (all 12 item bits) |

This combination appears in **no published list** (GameFAQs, Cheat Happens,
Ed Edd n Eddy wiki, speedrun/retroachievements pages). It exercises values
the published lists omit: `b0..b4 = 3` (published codes only use 0/1) and
`r0 = 15` (published codes use 0,2–9,12).

**In-game proof (observed):**

- Entered on the real password screen with Up/Right/A; the game accepted it and
  returned to the main menu.
- Savestate RAM diff before → after:
  `field30` `0x000 → 0xFFF`; output struct `+0x00..+0x04 = 3`,
  `+0x06 = 15`, `+0x30..+0x44 = 1`, `+0x48..+0x54 = 1`.
- Bonus Items → Characters screen after the code shows all six character icons
  on that screen coloured; the VRAM diff between the before/after Characters
  screens is 2,318 bytes (the icons/palette changed).

### Bounds proved by rejection (observed)

| Input | Reason | In-game result |
|---|---|---|
| `00000001` | checksum digit 0 ≠ sum(1..7)=1 | rejected; unlock struct stays all zero |
| `39999999` | `M = 9,999,999 ≥ 2^21` | rejected; unlock struct stays all zero |
| `00000000` | `M = 0`, checksum 0 | accepted (valid but empty) |

## 7. Validation evidence

| Claim | Evidence | Type |
|---|---|---|
| Stock ROM, no trainer/cracktro | header complement `0x7C` valid, entry `0xEA00002E`, single logo | Observed (bytes) |
| Validator at `0x08015C94` | disassembly, called from `0x0801610E` | Derived |
| Checksum = sum of digits 1..7 mod 10 | disassembly of `0x08015C94` + `0x0802BEE8`; model agrees with ROM on all inputs | Derived |
| Digit permutation DEC/ENC | ROM tables at `0x083D47F7`/`0x083D47F0`; model reproduces all published codes | Derived |
| 2^21 accepted codes | full enumeration, 0 mismatches | Derived |
| Published codes accepted | `10000010`, `96981951`, `34711154` entered; RAM struct matched static decode; `10000010` unlocked the Cartoon Speedway trophy | Observed |
| Novel code `40052674` accepted | entered; RAM struct written; Characters screen changed | Observed |
| Novel code unpublished | GameFAQs/Cheat Happens/wiki searches; not in ROM as a literal | Observed |
| Bad checksum rejected | `00000001` entered; RAM struct unchanged | Observed |
| Out-of-range rejected | `39999999` entered; RAM struct unchanged | Observed |
| `field30` unlocks characters/tracks | RAM `field30=0xFFF` + Characters screen icons all coloured + VRAM diff | Observed (screen) + Derived (mapping) |
| Generator masks to 11 bits | disassembly `0x0800C4F2` | Derived; not exercised end-to-end |
| No debug/hidden menu | strings scan + menu enumeration (see §8) | Observed |

## 8. Unknowns

- **Generator mask.** The in-game generator at `0x0800C42C` masks `M` to 11
  bits. It was not triggered end-to-end (it normally runs after a cup win),
  so it is not proven whether the generated password loses the upper bits in
  practice. The published codes follow the full 21-bit inverse.
- **Exact `field30` bit → item mapping.** The 12 mask bits clearly gate
  unlockable content (the Characters screen shows all six character icons
  coloured with `field30=0xFFF`), but the per-bit character/track table was
  not fully reversed.
- **`b0..b4 = 2/3` semantics.** The published codes only use 0/1. The novel
  code uses 3; the decoder writes the `!=0` flags but not the `==1` flags.
  Whether `b=3` unlocks anything visually (e.g. the cup trophies) was not
  isolated.
- **`You have unlocked:` message.** The string at `0x0800C354` and the
  caller's dialog setup suggest a message after a valid code, but the observed
  behaviour was an immediate return to the main menu; the message was not
  captured.
- **Credits/pause menus.** The Options screen lists Sound Effects, Music and
  Credits; the Credits screen and the in-race pause menu were not entered
  (media budget). The strings scan found no debug/cheat entries there.

## 9. Tooling

- `mgba` (`/usr/games/mGBA`), `Xvfb :231`, `openbox`, `xdotool`, `scrot`,
  `imagemagick`.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for raw Thumb disassembly; Python `capstone` for scripted scans.
- `/tmp/opencode/cnspeedway/cns_model.py` — clean encoder/decoder and field
  model (the pre-existing `model.py` had incorrect bit labels for `f10..f14`
  and a broken encoder; use `cns_model.py`).
- `/tmp/opencode/cnspeedway/enter_code.py`, `key.py` — password-screen input
  (Up = increment digit, Right = next slot, A = OK).
- `/tmp/opencode/cnspeedway/cnspeedway_before.ss1` — savestate at the password
  screen before any code.
- Savestates are PNG files with a zlib-compressed `gbAs` chunk; the raw state
  is 397,312 bytes and contains header/VRAM/IWRAM/EWRAM (IWRAM at raw offset
  `0x19000`, EWRAM at `0x21000`). This made RAM diffs possible without a GDB
  stub (mGBA's GDB stub was unreliable in this environment).

Legal note: no ROM or copyrighted assets are redistributed; only addresses,
algorithms, hashes and original scripts are published.
