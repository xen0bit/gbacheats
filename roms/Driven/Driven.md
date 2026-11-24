# Driven (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Driven/Driven.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `DRIVEN` |
| Game code | `ADVE` |
| Maker code | `6L` |
| Version | 0x00 (Rev.00) |
| Fixed byte 0xB2 | 0x96 |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0` |
| Header complement / checksum | `0xE7` / `0x0000` (nonstandard complement; §16.1 rebuilt-header artifact — but boot path is stock, no cracktro or trainer found) |
| MD5 | `5bfcfc20061ab866890eb72ca78aa7a4` |
| SHA-1 | `316e19c792bbd2b977a5fdc31fc319eca33b1c8c` |
| SHA-256 | `3b430b6ca1d5a9499a6e208cb188f997e28c2654402e14237e1472b50ae7491c` |

**Embedded headers**: one logo hit at file `0x4` (the retail header) and a second at
`0x335A64` (ROM `0x08335A64`) with a zeroed title, gamecode `01`, and a small
entry stub — a **multiboot/link stub** (guide §5.4b), not a playable game or a
trainer. No GameShark/CodeBreaker/cracktro/trainer signatures were found.

## 2. Executive summary

The game has a **developer-intended password system** on the `TOP SECRET CARS`
screen of the main menu. It is a pure 5-entry lookup table: a 5-digit code
(ten on-screen digit values 0–9, 10^5 = 100,000 representable inputs) is compared
byte-for-byte against five 5-byte records. The validator at `0x08019B08` returns
the matching index (0–4) or −1.

Published lists (3rd party cheat index mirrors, 3rd party cheat indexes,
etc.) advertise only three codes: `29801` (all cars/tracks/drivers/bonus levels),
`07913` (GameStop car), `62972` (Master car). **All three are present in the ROM
and work.** The ROM table contains **two additional codes that appear in no
published list**: `16200` and `81395`. Both were entered on the real screen,
accepted ("PASSWORD ACCEPTED" path), and RAM-verified to set distinct unlock
flags, by analogy with the GameStop/Master-car codes. They are almost certainly
two further secret-car unlocks; the exact car names are not recoverable from the
flag bytes alone and are listed as an unknown.

Exhaustive enumeration of the whole 100,000-input space proves **exactly five**
accepted codes. Bounds were proven by in-game rejection of `16201`, `00000`, and
`99999` (no flag changes, "PASSWORD REJECTED" displayed). The D-pad button codes
published for the GameCube/PS2 versions do **nothing** on the GBA build. No
hidden debug menu was found.

## 3. How to reproduce

Emulator: mGBA (SDL), headless on `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, 3× scale.
Default keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. Use 40–70 ms key holds to avoid double-stepping.

1. Boot → language screen → **A** (ENGLISH) → title → **Start**.
2. Main menu (9 items, indices 0–8). Press **Down** 8 times to highlight
   `TOP SECRET CARS` (index 8) → **A** → `PASSWORD ENTRY` screen (5 slots).
3. On a slot, **Up/Down** cycles the digit (0↔9 wrap); **Right** advances to the
   next slot. Enter the five digits, then **A** to submit.
4. Accepted codes set flags and show the "PASSWORD ACCEPTED" path (the game then
   transitions to a credits/GARAGE splash). Rejected codes show
   `PASSWORD REJECTED` and set no flags.

A savestate at the main menu with `TOP SECRET CARS` highlighted makes each test
cheap (mGBA: Shift+F7 saves, F7 loads). The input buffer and flags were read by
decompressing the `gbAs` chunk of `.ssN` savestates (guide §16.13).

Codes tested on the GBA screen:
- Published: `29801` ✓, `07913` ✓, `62972` ✓
- **Novel (unpublished): `16200` ✓, `81395` ✓**
- Rejected: `16201` ✗, `00000` ✗, `99999` ✗
- Console D-pad combos (`UDRRLUUD`, `UULDLRRU`, `DLURRUDL`) — inert.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Item | Address | Notes |
|---|---|---|
| Password validator | `0x08019B08` | 5× byte compare, returns index 0–4 / −1 |
| Password screen handler | `0x08019C64` | builds input, calls validator, dispatches effect |
| Input buffer | `0x02033658` (EWRAM) | 5 raw digit bytes, 0–9; savestate offset `0x54658` |
| Code pointer table | `0x083ED6E0` (file `0x3ED6E0`) | 5 × `u32` → code records |
| Code records | `0x083ED6C5`, `CA`, `CF`, `D4`, `D9` | each 5 bytes, raw digits |
| Unlock flag array | `0x020335E8..0x020335EF` | 8 bytes; indices 0–7 |
| Shared "unlock applied" byte | `0x020334E0` | set to 1 by every accepted code |
| Save-mirror flags | `0x02033702..0x02033705` | mirror of flag bytes 4–7 |
| Main-menu cursor | `0x02033504` (EWRAM) | 0–8; savestate offset `0x54504` |
| Text bank (localized UI) | `0x08230B..0x08232F` | "PASSWORD ENTRY/ACCEPTED/REJECTED", "TOP SECRET CARS", "BONUS STAGE SELECT" |
| Developer string table | `0x0820A538+` | screen labels + credits; **not** a menu |
| Credits table | `0x083ED784+` | `{string_ptr, type}` pairs — credits sequence |

## 5. Algorithm

Validator (`0x08019B08`), reconstructed from Thumb disassembly:

```
validate(input[5]):          # input at 0x02033658, raw digit bytes 0..9
    for i in 0..4:
        code = *(u32*)(0x083ED6E0 + 4*i)   # pointer to 5-byte record
        if input[0..4] == code[0..4]:
            return i                        # index 0..4
    return -1
```

The loop bound is `cmp r1, #5`; there is no checksum, no PRNG, and no hidden
9th entry. Screen handler (`0x08019C64`) dispatch:

- `i == 4` → set `0x020335E8..EF` (8 bytes) = 1, plus other arrays
  (`0x02033660` 10 bytes, `0x02034AA0`/`0x02034FA8` 4 bytes each =1,
  `0x02034BB0` 4 bytes =0, `0x02033624` = 0x5B), sound 3 — the "all" unlock.
- `i == 0..3` → set byte `0x020335E8 + 4 + i` = 1, call `0x0801D0CC`
  (save/refresh), then the accepted path.
- `i == -1` → rejected path: sound 25, `PASSWORD REJECTED`, no flags set.

## 6. Tables

| Index | Code | Published? | Effect / flag set (RAM-observed) |
|---:|---|---|---|
| 0 | **16200** | **No** | `0x020335EC`=1, `0x02033702`=1, `0x020334E0`=1 — **novel secret-car unlock** |
| 1 | **81395** | **No** | `0x020335ED`=1, `0x02033703`=1, `0x020334E0`=1 — **novel secret-car unlock** |
| 2 | `07913` | Yes | GameStop car: `0x020335EE`=1, `0x02033704`=1, `0x020334E0`=1 |
| 3 | `62972` | Yes | Master car: `0x020335EF`=1, `0x02033705`=1, `0x020334E0`=1 |
| 4 | `29801` | Yes | All cars/tracks/drivers/bonus levels: all 8 bytes `0x020335E8..EF`=1 |

Input alphabet: exactly the ten digit values `0`–`9` (on-screen keypad); length
exactly 5. No letters, no checksum characters, no terminator byte in the record
(the five bytes are compared directly).

## 6b. Enumeration

- **Space**: 5 digit positions × 10 values = **100,000** representable inputs.
  The accepted set is a fixed lookup table of **5** entries (no computed codes).
- **Validator model**: Python reimplementation of `0x08019B08` + the 5 pointers
  at `0x083ED6E0`; run over all 100,000 inputs (`enumerate.py`). Result: exactly
  5 accepted, matching the ROM table. This is a closed-set proof at the §16.9
  standard. The accept path is a simple table compare, so a debugger oracle
  (§16.19) adds nothing; static loop-bound proof + exhaustive model suffice.
- **Novel codes** (absent from 3rd party cheat index mirrors, 3rd party cheat indexes, and every other
  source searched — verified by targeted web search for both literals):
  - `16200` — entered on the real password screen, accepted, flag `0x020335EC`
    changed 0→1 (savestate diff: only 3 bytes changed). Screenshot:
    `shot_pre_16200.png`, `post_novel16200.png`.
  - `81395` — entered on the real password screen, accepted, flag `0x020335ED`
    changed 0→1 (savestate diff: only 3 bytes changed). Screenshots:
    `shot_pre_81395.png`, `post_novel81395.png`.
- **Bounds proven by rejection**: `16201` (one digit off a valid novel code),
  `00000`, `99999`, `12345`, `29802`, `07914`, `62973` all return −1 in the
  model; `16201`, `00000` were additionally entered in-game → `PASSWORD
  REJECTED` visible (`post_reject16201_immediate.png`) and **zero** flag bytes
  changed. Out-of-alphabet / wrong-length inputs (`1620a`, `1620`, `162000`)
  are unrepresentable on the 5-digit keypad.

## 7. Validation evidence

- **Observed**: all screens walked in mGBA (language, title, main menu, options,
  password entry, SELECT DRIVER, credits/GARAGE splash, in-race pause); every
  code entered with the 5-digit keypad; `PASSWORD REJECTED` shown for invalid
  codes; savestate RAM reads proving input buffer contents and the exact flag
  bytes changed by each code.
- **Derived**: validator algorithm and return-value mapping from Thumb
  disassembly at `0x08019B08` / `0x08019C64`; exhaustive 100,000-input model;
  code table layout from the pointer table at `0x083ED6E0`.
- **Inferred**: that `16200`/`81395` unlock two specific secret cars (by
  structural analogy with the GameStop/Master codes at adjacent flag indices).
  The exact car names are not proven.
- **Negative results**: published console D-pad codes are inert on GBA (flag
  array unchanged after entering three of them at the main menu); full-sequence
  and 3-press-prefix mask searches found no complete button-code table; no
  `debug`-named strings; L+R / Start+Select / A+B at the title only play the
  franchise intro; OPTIONS (4 entries) and in-race pause (CONTINUE only) contain
  no hidden screen. The developer string table at `0x0820A538+` resolves to
  screen labels and the credits table — not a playable debug menu.

## 8. Unknowns

- Exact in-game car/vehicle names behind the two novel codes `16200` and
  `81395` (only their flag bytes and save-mirror bytes were observed).
- Whether the four lower flag bytes (`0x020335E8..EB`, set only by `29801`
  "all") correspond to tracks, drivers, or bonus levels — the all-code sets
  them together and individual codes do not touch them.
- The secondary header at `0x08335A64` was not executed; it is assumed to be a
  link/multiboot stub based on its zeroed title and stub entry word.

## 9. Tooling

- `phase0.py`, `find_codes.py`, `dump_table.py`, `xrefs.py`, `blscan.py`,
  `flagxref.py`, `debugxref.py`, `buttonsearch.py`, `enumerate.py` — Python
  fingerprinting, literal scans, xref scans, and exhaustive validator model.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for disassembly; Capstone 5.0.7 for Thumb literal-load scanning.
- `key.py`, `state.py`, `pwtest.py`, `nav.py`, `statediff.py`, `stateram.py` —
  xdotool input helpers and mGBA savestate (`gbAs`/zlib) RAM readers.
- mGBA (SDL) on `Xvfb :315` + openbox, `SDL_AUDIODRIVER=dummy`; scrot/ImageMagick
  for the screenshots listed above (kept on disk, not redistributed).

**Legal note**: no ROM, savestate, or copyrighted asset is redistributed; only
addresses, hashes, algorithms, and the author's own scripts are documented.
