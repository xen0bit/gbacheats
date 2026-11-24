# The Amazing Virtual Sea-Monkeys (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Amazing Virtual Sea-Monkeys.gba` |
| Size | 4,194,304 bytes (0x00400000) |
| Header title | `SEA MONKEYS` (0xA0) |
| Game code / maker | `A7ME` / `5Z` (0xAC / 0xB0) |
| Revision / version | Rev.00 (intro screen), version byte `0x00` |
| Header checksum / complement | `0x0000` / `0x99`, fixed byte `0x96` present |
| Entry branch | `0xEA00002E` (stock, no cracktro/trainer) |
| MD5 | `8989a8830651ca9705c676676aaf4894` |
| SHA-1 | `d596fe5c59b6639fc5e1840bcc90086bcb56f7d0` |
| SHA-256 | `f6f92ee32e1368ef6e1f24be7ee5bdd1d51e8581c64bc4b89f5abf57e94552de` |

File offset ↔ ROM address: `addr = 0x08000000 + file_offset`.

## 2. Executive summary

This is **not** a "no cheats" game. The title screen has a **Password** entry
screen (and a progress-gated **Select level** screen). The password system has
two layers:

1. **Algorithmic 9-symbol password** (the real code system). Each of the 9
   positions takes a value 0..31 from a *scrambled 32-symbol alphabet*
   `LZ01BCGH7JK2QR6M34PNVST5WF8XYD9*` (vowels A/E/I/O/U are deliberately
   absent). The on-screen keypad offers 37 symbols `A-Z * 0-9`; only the 32
   above map to nonzero values. The decoder subtracts the position index from
   each symbol value, packs the 9 values into a 45-bit payload and enforces a
   **6-bit checksum**. The 7-bit field `fA` is the **level number (0-based)**;
   a valid code unlocks that level and every level below it. Success path:
   `0x08007200`.
2. **Hard-coded master password** `MSTRPSWRD` at ROM `0x080c8be0`, compared
   byte-for-byte at `0x080073b6` as a fallback when the checksum fails. It is
   accepted but does **not** unlock levels (returned to title; Select level
   stayed at 1) — its effect is a separate flag path and is labelled unknown
   below.

A novel, checksum-valid code absent from every published list was generated:
**`YGQ*RB0LB`** (fA = 42). Entered through the real UI, it was accepted and
unlocked **level 43**, verified both on the Select-level screen and on the
level intro screen ("Level: 43, Maximum time: 04:20, Sea-Monkeys to be saved:
4"). A one-symbol change breaking the checksum (`YGQ*RB0LC`) produced
"Invalid password", and an out-of-range but checksum-valid payload
(`Y301BCGH7`, fA = 120) followed a different code path ("Highscore:0") rather
than unlocking level 70.

Web recon found **no published in-game passwords at all** for this SKU
(GameFAQs cheats: no codes; Project Cheat Codes: "no known codes"; VGChartz: 0;
ROMSFUN/libretro and CodeBreaker lists are GameShark-style device codes,
out of scope). Therefore any generated code is novel by construction.

## 3. How to reproduce

Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy mgba -3 <rom>` under Xvfb.
Default keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
arrows for D-pad. Hold keys ~90–150 ms (key repeat can double-step a cursor).

Menu path:

1. Wait through the "Licensed by Nintendo" / Conspiracy / copyright splash
   (~20 s) until the title menu appears.
2. Press **Down ×3**, then **A** → "Enter password:" screen (nine `A`s).
3. **Left/Right** move the cursor between the 9 slots; **Up/Down** cycle the
   symbol at the cursor in the order `A..Z * 0..9` (37 symbols, wrapping).
4. **A** or **Select** submits; **B** backs out to the title menu.
5. A rejected code displays "Invalid password"; an accepted level code returns
   to the title menu. Then choose **Select level** (Down ×2, A) to see the
   highest unlocked level, and **A** on a level number to start it.

To enter `YGQ*RB0LB` from a fresh all-`A` screen, for positions 0..8 press
Right once between positions and Up (alphabet index of target char) times:
24, 6, 16, 26, 17, 1, 27, 11, 1 presses respectively. Verify the RAM buffer at
`0x03002240` before submitting.

## 4. Address map

### ROM (all addresses are `0x08000000 + file offset`)

| Address | Meaning |
|---|---|
| `0x08000000` | Stock ARM entry branch `0xEA00002E` |
| `0x080071d0` | Symbol→5-bit-value lookup; linear scan of the 32-byte table, returns 0 when not found (i.e. vowels/illegal symbols become 0) |
| `0x08007200` | **Password validator** (no arguments; reads buffer at `0x03002240`, returns level/sentinel in a local word) |
| `0x080073b6` | Hard-coded 9-byte comparison with the master password |
| `0x0800745c` | Password-screen setup; `BL 0x0800b9e8` at `0x08007488` copies the default `AAAAAAAAA` into the buffer |
| `0x080075b0`–`0x0800772c` | Password-screen input handler; `BL` to validator at `0x08007678` (A) and `0x080076ee` (Select) |
| `0x0800b9e8` | Generic strcpy used to initialise the buffer (watchpoint hit here at `0x0800b9f4`, LR = `0x0800748d`) |
| `0x080c8be0` | `MSTRPSWRD\0\0\0` — hard-coded master password |
| `0x080c8bec` | `AAAAAAAAA\0` — default password string |
| `0x080c93cc` | 32-byte validator alphabet `LZ01BCGH7JK2QR6M34PNVST5WF8XYD9*` |
| `0x0c8c04`+ | Level-data records (20-byte stride: time limit, level index, flags) |

### RAM (from mGBA savestate `gbAs` dumps; raw offset = `0x19000 + (addr-0x03000000)`)

| Address | Meaning |
|---|---|
| `0x03002240` | **9-char ASCII input buffer + NUL** (observed `MSTRPSWRD`, `YGQ*RB0LB`, etc.) |
| `0x03002220` | Input-state word, changes with Left/Right/Up/Down (cursor/animation counter) |
| `0x03003F88` | Byte `0x46` = 70 — maximum level count; clamps decoded level to 69 |
| `0x03003BDC`/`DD`/`DE`, `0x030036AD`, `0x03003BA4`, `0x03003428` | Other fields written by the success path (flag bits, highscore/score data) |
| `0x030036AE` | Level field written by the validator (observed `0x0b` after fA=0 code) |

## 5. Algorithm

Precise reimplementation (see `pwmodel.py` in the tooling section):

```
ALPHA32 = "LZ01BCGH7JK2QR6M34PNVST5WF8XYD9*"        # 0x080c93cc

charval(c) = index of c in ALPHA32, else 0

# decode 9 input characters (buffer at 0x03002240)
for i in 0..8:
    v[i] = (charval(pw[i]) - i) & 31

# pack (32-bit w, plus three bits carried in a second word)
w  = (v[0]<<27) | (v[1]<<22) | (v[2]<<17) | (v[3]<<12) | (v[4]<<7) | (v[5]<<2)
w |= (v[6] >> 3)

sb = w & 7
ip = v[8] & 3
fA = (w >> 19) & 0x7f                       # LEVEL (0-based)
fB = (w >> 3)  & 0xffff
r6 = (((v[8] >> 2) & 7) << 1) | ((v[6] >> 2) & 1)
r5 = (v[7] & 0x7f) | ((v[6] & 7) << 5)
chk = (w >> 26) & 0x3f
sum = (fA + fB + r6 + r5 + sb + ip) & 0x3f
VALID = (chk == sum)
```

On success the level field `fA` is clamped to
`min(fA, byte[0x03003F88]-1)` = `min(fA, 69)` and returned; the screen handler
stores it and the Select-level menu then offers levels 1..fA+1. On failure the
validator returns `-1` and the UI shows "Invalid password". Separately, if the
checksum fails, the input is compared byte-for-byte with `MSTRPSWRD`; a match
takes the hard-coded success path at `0x080073ea`.

The 37-symbol UI alphabet is produced by the input handler:
`A..Z` (0x41–0x5A) → `*` (0x2A) → `0..9` (0x30–0x39) → wrap to `A`; Down walks
it backwards. Only the 32 symbols in `ALPHA32` contribute nonzero values.

## 6. Tables

| Item | Value |
|---|---|
| UI alphabet (37) | `ABCDEFGHIJKLMNOPQRSTUVWXYZ*0123456789` |
| Validator alphabet (32) | `LZ01BCGH7JK2QR6M34PNVST5WF8XYD9*` |
| Excluded from validator | vowels `A E I O U` (map to value 0) |
| Password length | 9 symbols, ASCII + NUL in RAM |
| Position transform | `v[i] = (charval - i) mod 32` |
| Checksum width / position | 6 bits, top of packed word (`w >> 26`) |
| Checksum formula | `(fA+fB+r6+r5+sb+ip) mod 64` |
| Level field | `fA`, 7 bits, clamped to 0..69 |
| Hard-coded password | `MSTRPSWRD` at `0x080c8be0` |
| Default string | `AAAAAAAAA` at `0x080c8bec` |
| Max levels | `0x46` = 70 (`0x03003F88`) |
| Submit keys | A (`0x08007678`) or Select (`0x080076ee`) |

## 6b. Enumeration

**Space definition.** The on-screen keypad offers 37 symbols over 9 positions
= `37^9 = 129,961,739,795,077` possible typed strings. The validator only
understands 32 of those symbols, so the meaningful code space is
`32^9 = 35,184,372,088,832` symbol strings (35.2 trillion). The position
subtraction is a bijection, so the decoded payload space is the same size.
The 6-bit checksum accepts 1 in 64 of them:

```
expected valid codes = 32^9 / 64 = 549,755,813,888  (~5.5e11)
```

The level field `fA` is 7 bits (0..127) but the game clamps it to the
`maxlevel-1 = 69` bound (70 levels); codes with fA>69 do not unlock level 70.
One additional, non-algorithmic code exists: the hard-coded `MSTRPSWRD`.

**Validator cross-check.** Brute-forcing the free first two symbol values with
all others fixed (`v[2..8]=0`) gave exactly **16 valid codes out of 1,024**
(1/64), confirming the checksum model: fA ∈ {0,8,16,…,120} with one code each,
e.g. `LZ01BCGH7` (fA=0), `B001BCGH7` (fA=8), `Y301BCGH7` (fA=120).

**Novel code (not in any published list).** Web recon found no published
in-game password list for this SKU at all; the only online "cheats" are
GameShark/CodeBreaker device codes, explicitly out of scope. Generated with
the reimplemented validator:

| Code | Payload | In-game proof |
|---|---|---|
| `YGQ*RB0LB` | fA=42, checksum valid | Accepted; Select level showed **43**; starting it showed "Level: 43 / Maximum time: 04:20 / Sea-Monkeys to be saved: 4" (screenshot `lvl43_ingame.png`) |
| `MSTRPSWRD` | hard-coded fallback | Accepted (no "Invalid password"), returned to title; **no level unlock observed** — effect remains unknown |
| `LZ01BCGH7` | fA=0, checksum valid | Accepted; Select level stayed at 1 (level 1), as predicted |

**Bounds proven by rejection / out-of-range behaviour.**

| Test input | Expected | Observed |
|---|---|---|
| `AAAAAAAAA` (default; vowels → 0, checksum wrong) | reject | "Invalid password" |
| `YGQ*RB0LC` (one symbol changed from valid code; checksum broken) | reject | "Invalid password" (screenshot `badchecksum.png`) |
| `Y301BCGH7` (fA=120 > 69, checksum **valid**) | range/clamp path | Accepted but did **not** unlock level 70; password screen showed "Highscore:0" (screenshot `overrange_submitted.png`) |
| Select level after `YGQ*RB0LB` | max = 43 | Right arrow would not advance past 43 (screenshot `lvl42_select_right2.png`) |

**Enumeration of hard-coded strings.** A full ROM regex scan for NUL-terminated
9-character strings over `[A-Z0-9*]` found 83 candidates, but all except two
are compressed graphics/audio noise in high offsets (`>0xc9400`). In the
password data bank near `0x0c8be0` there are exactly two: `MSTRPSWRD` and the
default `AAAAAAAAA`. There is no hidden table of per-level passwords — the
level passwords are algorithmic.

## 7. Validation evidence

* **Observed (emulator / savestate):** title menu with Password and Select
  level; 9-symbol all-`A` input; symbol cycling order; buffer bytes at
  `0x03002240` verified after every typed character via mGBA `gbAs` dumps;
  acceptance/rejection messages; level 43 unlocked and started; cursor stops
  at 43; out-of-range code shows "Highscore:0"; `MSTRPSWRD` accepted but no
  level unlock.
* **Derived (disassembly):** validator algorithm, alphabet table, checksum
  formula, level field, submit-key call sites, master-password comparison,
  input stripping of vowels. Watchpoint on `0x03002240` hit at `0x0800b9f4`
  with LR `0x0800748d`, connecting the buffer to the password-screen setup.
* **Inferred (not fully exercised):** the precise meaning of the other fields
  (`fB`, `r5`, `r6`, `sb`, `ip`) and the "Highscore:0" screen reached by
  fA=120; the exact effect of `MSTRPSWRD` beyond acceptance. The master
  password writes different RAM globals (`0x030036A4/A5`, `0x03003BE1`,
  `0x03003428`) than the algorithmic path, so it is a distinct feature, not
  simply "unlock all levels".

No prompt-injection content was encountered in fetched pages or ROM strings.
Fetched web content was treated strictly as data.

## 8. Unknowns

* Whether `MSTRPSWRD` unlocks a non-level feature (e.g. a highscore/hidden
  menu) reachable from another screen; its accepted path was followed only as
  far as the title menu.
* Semantic labels for `fB`, `r5`, `r6`, `sb`, `ip` (they affect score/highscore
  state and were not individually exercised).
* Whether levels above 69 can ever be reached through normal gameplay (the
  ROM's max-level byte is 70).
* The 5 GameShark/CodeBreaker device codes published online were **not**
  tested — they are out of scope for this engagement.

## 9. Tooling

All analysis scripts were in `/tmp/seamonkeys/`:

* `ss.py` — extract mGBA `.ssN` savestates (`gbAs` zlib chunk) to a raw 397,312-byte RAM dump; used for all RAM evidence and savestate diffing.
* `ui.py`, `typepw.py` — XTEST input driver and verified password entry via savestate buffer reads.
* `pwmodel.py` — Python reimplementation of the validator and a code generator.
* `scan_refs.py`, `disasm.py` — Capstone reference scans and Thumb disassembly.
* `gdbtm.py` / tmux-hosted gdb-multiarch — hardware watchpoint on `0x03002240` located the buffer writer (`0x0800b9f4`, LR `0x0800748d`).
* `arm-none-eabi-objdump -M force-thumb`, `xxd`, `strings`, `grep`, `scrot`, `convert`, `xdotool`, Xvfb, mGBA 0.10.5.

Screenshots supporting each claim are kept in `/tmp/seamonkeys/`
(`typed_master.png`, `master2_submitted.png`, `master2_select.png`,
`lz_submitted.png`, `lvl42_submitted.png`, `lvl42_select.png`,
`lvl43_ingame.png`, `badchecksum.png`, `overrange_submitted.png`, etc.).

**Legal note:** no ROM image, extracted graphics, or copyrighted assets are
redistributed here — only addresses, hashes, algorithms and original tooling.
