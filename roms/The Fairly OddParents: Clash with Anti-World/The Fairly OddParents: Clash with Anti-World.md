# The Fairly OddParents: Clash with Anti-World (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Fairly OddParents: Clash with Anti-World.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `ODDPARENTS` |
| Game code / maker | `BFOE` / `78` (THQ), revision `00` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Version / complement / checksum | `0x00` / `0xD2` / `0x0000` |
| MD5 | `778eb070e354caa92a1ba7e8b5d5df29` |
| SHA-1 | `0a0baba3f66b7508236aee7d74f21188e3f6b315` |
| SHA-256 | `1cd3ae366a496115b6614c3033967fc98b5e93e6a9f2173a1d7e9bc0991ab61c` |

Stock retail image (no cracktro/trainer prefix; first 4 KiB and logo intact).

## 2. Executive summary

The game has a **real, developer-intended password system** on `Main Menu → Password`, plus a
**Pause Menu → Cheats** screen whose five entries are unlocked by those passwords. Passwords are
**8 characters from a 32-symbol consonant-and-digit alphabet**; they are *not* stored in a table —
a generator at `0x08004A88` and a validator at `0x08004B94` implement a base-32 payload with
four independent modulo checks. I recovered both routines and reimplemented them bit-for-bit.
All 21 published codes I could find validate under the model, and the model's encoder reproduces
them exactly.

The system is **not** a small list: **34,636,832 strings are accepted** (sum of `32^k`, k=1..5),
encoding **953,370 intended payload states** (difficulty × level × aux field × flags field ×
cheat count). I minted two codes absent from every published list, entered them on the real
screen, and observed the results: `QH8KRHTC` starts a **Hard-difficulty** level 5 (the published
level codes are all Medium/Easy), and `VQ7K48D4` unlocks **all five** cheats at once. A corrupted
checksum and a bad length prefix are rejected in-game, which bounds the format.

One string, `God Mode`, exists in the UI string table but has **no row in the five-entry Cheats
menu** — with a cheat-count of 5 all five visible rows are checked and no sixth appears.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under `Xvfb :317` + openbox, `SDL_AUDIODRIVER=dummy`; keymap
  A=`x`, B=`z`, Start=`Return`, D-pad=arrows.
- Wait for the `Press Start` title screen, press `Return`, then `Down Down`, `A` to reach
  `Main Menu → Password`. The keypad is an 8×4 grid; D-pad moves one cell, `A` types a symbol,
  and the code auto-submits on the 8th symbol. `B` is Back.
- Save a state at the empty password screen (`Shift+F1`) to avoid replaying the ~15 s intro.
- Published anchors used: `VDG*GNCJ` (Level 01), `Q17K99*W` (Level 15), `LVCDVVVV`
  (Gardener 1), `VT*CH3G3` (Triple Jump — SuperCheats prints `Vt*CH3G3`, a lowercase-t OCR
  error; the ROM alphabet is uppercase-only).
- Novel codes entered on that screen: `QH8KRHTC`, `VQ7K48D4`.
- Rejection tests: `QH8KRHTD` (one checksum symbol changed), `BBBBBBBB` (length prefix `B`
  → 0 digits).
- Evidence screenshots (saved in `/tmp/opencode/fairlyodd2/`): `nov1.png` (novel Hard level
  accepted), `ac_cheats.png` (all five cheats checked), `walk_cheats2.png` (cheat menu,
  one cheat), `reject1.png`, `reject_ndig.png`, `walk_mm.png`, `walk_opt.png`,
  `walk_pause2.png`, `q5.png` (keypad), `pw1.png`.

## 4. Address map

| ROM address | Meaning | Evidence |
|---|---|---|
| `0x08004A88` | Password **encoder** — builds 8 raw symbols from game state | Derived (disassembly) |
| `0x08004B94` | Password **validator** — checks and decodes to game state | Derived (disassembly) |
| `0x08004BBC` | validator reject return (`r0=0`) | Derived |
| `0x08004D28` | validator accept return (`r0=1`) | Derived |
| `0x080308B0` | unsigned 32-bit **divide** helper (`r0/r1`) | Derived |
| `0x08030928` | unsigned 32-bit **modulo** helper (`r0%r1`) | Derived |
| `0x08004E7C` | Cheats-list renderer; loads the alphabet literal at `0x0804EFC` | Derived |
| `0x08005E00` | Password-display screen routine | Derived |
| `0x08005E84`–`0x0805E9A` | raw symbol → alphabet character conversion, 8 iterations | Derived |
| `0x080897E4` | ASCII string `"Cheats"` | Observed (ROM bytes) |
| `0x080897F4` | **32-symbol alphabet** `"BCDFGHJKLMNPQRSTVWXYZ123456789!*"` | Observed |
| `0x08089818` | word pointer to `0x080897F4` | Observed |
| `0x0805E780`–`0x0805E910` | UI string-pointer table (`Cheat Unlocked:`, `Password:`, `Wanda`, `Cosmo`, `God Mode`, `Unlimited Lives`, `Unlimited Wishes`, `Triple Jump`, `Cheats`, `Pause Menu`, `Main Menu`, …) | Observed |

Validator literal pool / RAM writes:

| Literal | Value | Role |
|---|---|---|
| `0x0804B28` | `0x030028A8` | pointer to state base |
| `0x0804B2C` | `0x9554` | state-base offset of difficulty byte |
| `0x0804B30` | `0x03002B7C` | level-index variable |
| `0x0804B34` | `0x03002B84` | auxiliary field variable |
| `0x0804B38` | `0x956C` | state-base offset of flags field |
| `0x0804B3C` | `0x030028B4` | cheat flag word |
| `0x0804CA4` | `321` | modulus for the flags field |

`file offset = ROM address − 0x08000000` throughout.

## 5. Algorithm

### 5.1 Alphabet and input

```
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ123456789!*"
index: B=0 C=1 D=2 F=3 G=4 H=5 J=6 K=7 L=8 M=9 N=10 P=11 Q=12 R=13
       S=14 T=15 V=16 W=17 X=18 Y=19 Z=20 1=21 2=22 3=23 4=24 5=25
       6=26 7=27 8=28 9=29 !=30 *=31
```

The on-screen keypad is exactly these 32 symbols in an 8×4 grid. The game stores **indices**
(0..31) in an 8-byte buffer; `0x08005E84` converts them to characters only for drawing.

### 5.2 Validator (`0x08004B94`) — precise model

```python
def validate(buf):                       # buf = 8 alphabet indices
    n = buf[0] >> 2
    if not (1 <= n <= 5): return False   # 0x0804BB6: (n-1) > 4 -> reject
    x = 0; mult = 1
    for i in range(1, n+1):              # base-32, LEAST significant first
        x += buf[i] * mult
        mult *= 32
    for i in range(n+1, 8):              # four/three/two/one check symbols
        m = 13*i + 7
        if ((x % m) & 31) != buf[i]: return False
    # accept: decode fields (0x0804BF0..)
    difficulty   = (x % 3) + 1           # 1..3, written to state+0x9554
    x //= 3
    level_index  = x % 15                # 0..14 -> displayed level 1..15
    x //= 15
    aux          = x % 11                # 0..10, written to 0x03002B84
    x //= 11
    flags_field  = x % 321               # 0..320, written to state+0x956C
    cheatcount   = x // 321
    flags = 0
    if cheatcount > 0: flags |= 0x40
    if cheatcount > 1: flags |= 0x100
    if cheatcount > 2: flags |= 0x200
    if cheatcount > 3: flags |= 0x800
    if cheatcount > 4: flags |= 0x1000
    return True
```

`%` and `//` are the ROM's own unsigned helpers at `0x08030928` / `0x080308B0`.
The check-symbol test is `(x % m) % 32`, implemented in the ROM as a signed
arithmetic-shift/modulo sequence at `0x0804BD4`–`0x0804BE0`.

### 5.3 Encoder (`0x08004A88`) — inverse

```python
def encode(difficulty, level_index, aux, flags_field, cheatcount):
    x = ((((cheatcount*321 + flags_field)*11 + aux)*15 + level_index)*3) + (difficulty-1)
    digits = []
    while x: digits.append(x & 31); x >>= 5
    out = [4*len(digits)] + digits
    for i in range(len(digits)+1, 8):
        out.append((x % (13*i+7)) & 31)   # x here is the ORIGINAL payload
    return ''.join(ALPHA[v] for v in out)
```

The first symbol is `ALPHA[4*ndigits]`, i.e. only `G` (1 digit), `L` (2), `Q` (3),
`V` (4), `Z` (5) can begin a valid password.

## 6. Tables

### 6.1 Published codes verified against the model (all 21 pass)

| Effect | Code | difficulty | level_index | aux | flags_field | cheatcount |
|---|---|---:|---:|---:|---:|---:|
| Level 01 | `VDG*GNCJ` | 2 | 0 | 2 | 8 | 1 |
| Level 02 | `VHJYDRY7` | 2 | 1 | 1 | 172 | 0 |
| Level 03 | `Q8ZPSZBN` | 2 | 2 | 1 | 24 | 0 |
| Level 04 | `QK5KN3JH` | 2 | 3 | 1 | 16 | 0 |
| Level 05 | `QG8KQGSB` | 2 | 4 | 3 | 16 | 0 |
| Level 06 | `QK8KTKWF` | 2 | 5 | 3 | 16 | 0 |
| Level 07 | `Q96KHHK7` | 2 | 6 | 2 | 16 | 0 |
| Level 08 | `QJ4KG2HG` | 2 | 7 | 0 | 16 | 0 |
| Level 09 | `VRHYD9VF` | 2 | 8 | 0 | 172 | 0 |
| Level 10 | `VLF4CBMZ` | 2 | 9 | 0 | 116 | 0 |
| Level 11 | `QM7KWWYH` | 2 | 10 | 2 | 16 | 0 |
| Level 12 | `VJSPDJN!` | 2 | 11 | 0 | 156 | 0 |
| Level 13 | `V79*CYWF` | 2 | 12 | 2 | 132 | 0 |
| Level 14 | `QDD*M6Z6` | 2 | 13 | 2 | 64 | 0 |
| Level 15 | `Q17K99*W` | 2 | 14 | 2 | 16 | 0 |
| Gardener 1 | `LVCDVVVV` | 1 | 1 | 1 | 0 | 0 |
| Gardener 2 | `QP9F6YV7` | 1 | 2 | 1 | 8 | 0 |
| Gardener 3 | `QP2PD7T3` | 1 | 3 | 2 | 24 | 0 |
| Pirate 1 | `QQTTLQNN` | 1 | 4 | 0 | 32 | 0 |
| Pirate 2 | `QK8F2TC3` | 1 | 5 | 0 | 8 | 0 |
| Triple Jump | `VT*CH3G3` | 2 | 0 | 1 | 14 | 1 |

Source: SuperCheats list plus the Great Games Wiki mirror (403 on direct fetch, recovered from
search snippets and the SuperCheats page). All 21 literals were checked against the ROM model;
none appears as an ASCII string in the image (algorithmic codes, not a lookup table).

### 6.2 Cheat flags ↔ Cheats menu

The Pause Menu → Cheats screen has exactly **five** rows, in this display order:
`Triple Jump`, `Unlimited Wishes`, `Unlimited Lives`, `Cosmo`, `Wanda`. The validator sets
flag bits `0x40`, `0x100`, `0x200`, `0x800`, `0x1000` for cheatcount `1..5` respectively;
`cheatcount = 5` checks all five rows. The string `God Mode` (`0x0805E800`) is present in the
string table but has no menu row — no sixth entry appears even with all flags set.

## 6b. Enumeration

**Space definition.** Fixed length 8 over a 32-symbol alphabet → `32^8 = 1,099,511,627,776`
possible strings. The length prefix restricts the first symbol to 5 of 32 values, and the
`7 − n` modulo checks fix the remaining symbols for each payload, so the **accepted set is
exactly `sum(32^k for k in 1..5) = 34,636,832` codes**. There is no hidden preset table: every
accepted string is a legitimate start. The intended field space is
`3 × 15 × 11 × 321 × 6 = 953,370` distinct payload states.

**Generator verified against the published set.** The encoder reproduces all 21 published
codes bit-for-bit from the decoded fields, so the novel codes below are genuine forward tests,
not perturbations of known strings.

**Novel codes (absent from SuperCheats, GameFAQs, Great Games Wiki and every consulted list),
typed on the real PASSWORD screen and confirmed in mGBA:**

| Novel code | Decoded fields | In-game proof |
|---|---|---|
| `QH8KRHTC` | difficulty **3 = Hard**, level_index 4 (level 5), aux 3, flags_field 16, cheatcount 0 | Accepted; started a Hard-difficulty level with orange sky / dark-green foliage, visually distinct from every published Medium/Easy level code. Screenshot `nov1.png`. Decoder/pack: `x=8069`. |
| `VQ7K48D4` | difficulty 2, level_index 0, aux 0, flags_field 0, **cheatcount 5** | Accepted; `Pause → Cheats` shows **all five rows checked** — a state no published code grants (published codes grant at most one flag). Screenshot `ac_cheats.png`. `x=794476`. |

A third decoder-valid novel code, `VZCFHG4J` (Hard, level 5, cheatcount 1, `x=166964`), was
generated but not entered in the emulator.

**Bounds proven by in-game rejection:**

| Code | Reason | Result | Screenshot |
|---|---|---|---|
| `QH8KRHTD` | last check symbol changed from `C` to `D`: `x % 98 & 31` no longer matches | Rejected — stays on the password screen, field clears | `reject1.png` |
| `BBBBBBBB` | first symbol `B` → `buf[0]>>2 = 0` digits, outside 1..5 | Rejected — stays on the password screen | `reject_ndig.png` |

All 34,636,832 accepted strings are reachable on the screen (the keypad offers the full
alphabet and accepts 8 symbols), so there is no input-cap or progress gate on this feature.

**Screen walk (all reachable screens enumerated with evidence):**
Title / Press Start → Main Menu (`Play Game`, `Options`, `Password`, `Credits`; screenshot
`walk_mm.png`) → Difficulty (`Easy`/`Medium`/`Hard`) → Password keypad (`q5.png`) → gameplay →
Pause Menu (`Return to Game`, `Options`, `Cheats`, `Quit Game`; `walk_pause2.png`) → Options
(`Music On`, `Sound Effects On`; `walk_opt.png`) → Cheats (`walk_cheats2.png`,
`ac_cheats.png`) → Credits. No other menu entry exists on any of these screens; a 6th Cheats
row does not appear when all flags are set.

## 7. Validation evidence

- **Observed** — emulator screenshots for the 8-symbol keypad, the accepted novel codes, the
  all-cheats menu, and both rejections; published `VDG*GNCJ` starts level 1 in mGBA.
- **Derived** — encoder/validator address map, alphabet, base-32 layout, modulo check
  `13*i+7`, field divisors `3/15/11/321`, flag bits, and the exact accepted-code count, all
  from Thumb disassembly plus `objdump`/Capstone cross-checks. The decoder accepts 21/21
  published codes and the encoder reproduces each of them.
- **Inferred** — field *names*: `level_index` (matches published level labels exactly),
  `difficulty` (2=Medium matches the published "Medium difficulty" note; 1=Easy matches the
  Gardener/Pirate codes), `cheatcount` (controls the five checkmarks). The `aux` and
  `flags_field` fields are decoded but their in-game semantics were not isolated.
- The literal `God Mode` is a **string-table observation**, not a reachable menu entry.

## 8. Unknowns

- Semantics of the `aux` (mod 11) and `flags_field` (mod 321) payload fields beyond their
  validated ranges; they are carried into RAM at `0x03002B84` and `state+0x956C` but I did not
  isolate their readers.
- `cheatcount > 5` is not rejected by the validator (all such values set the same five flag
  bits), so those are aliases of `cheatcount = 5`, not distinct unlock states.
- The SuperCheats submission `vgsvh8y` (lowercase, 7 characters) is outside the format and was
  treated as an invalid/unverified public submission, not a code variant.
- No button-code sequence or debug menu was found in addition to the password system; the
  search space was the full UI string-pointer table (`0x0805E780`–`0x0805E910`), the 32-symbol
  alphabet and its xrefs, and every reachable menu screen.

## 9. Tooling

- `strings -t x -n 4`, `xxd`, Python `struct` scans for literal pointers, BL/LDR xrefs.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`, Capstone.
- mGBA 0.10.5 (`-3`, savestates `Shift+F1..F3`), Xvfb `:317`, openbox, xdotool (keymap
  A=`x`, B=`z`, Start=`Return`), scrot, ImageMagick.
- mGBA CLI debugger (`mgba -d`) used for ROM/RAM reads; the GDB stub proved unreliable for
  `find`/`dump` and was abandoned in favour of static analysis plus emulator ground truth.
- Scripts in `/tmp/opencode/fairlyodd2/`: `encoder.py` (validator + encoder, offline),
  `decode.py`, `analyze.py`, `brute_model.py`, `fields.py`, `xref.py`, `enter.py` (keypad driver),
  `dumplive.py`/`dumpdbg.py` (CLI-debugger memory dumps).

## 10. Legal note

No ROM image, extracted graphics, or copyrighted game assets are redistributed here. Only
hashes, addresses, algorithms, and analyst-authored tools/findings are published. Fetched
web pages were treated strictly as data; no instructions found in them were followed.

---

*Report completed as part of the GBA cheat-enumeration sweep. Coordinator rule observed:
`roms/INDEX.md` and the reverse-engineering guide were not modified.*
