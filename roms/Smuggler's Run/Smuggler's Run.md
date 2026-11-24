# Smuggler's Run (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Smuggler's Run/Smuggler's Run.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `SMUGGLERSRUN` |
| Game code / maker | `ASGE` / `20` |
| Version | `0x00` |
| Entry word | `0xEA00002E` → entry point `0x080000C0` (stock crt0; `main` Thumb pointer `0x08005455` at header `+0x1C8`) |
| Header checksum / complement | `0x0000` / `0x21` (checksum 0 is a rebuild artifact; complement is sane) |
| MD5 | `e639ef65c3638c0b5927a4d3fc947e3d` |
| SHA-1 | `a14efb987bfcf3f547db2650cd2cc6dca3adcf73` |
| SHA-256 | `6d6a5a5ec9f4b9df7e7569819ecf6295f05d3c456fcdbc4b0f25b7ee7610d57d` |

**Phase 0 checks:** `file` reports a normal GBA image. Scanning the whole 8 MiB for the
156-byte Nintendo logo found exactly **one** GBA header at file offset `0x0` — no
embedded second image, no appended trainer, no cracktro patch (entry branch is the
stock `b 0x080000C0`). Treated as the retail `ASGE` image.

## 2. Executive summary

The game has a **single password system**: a 30-entry, exact-match plaintext lookup
table. It is reached from **Smuggler's Mission → Select Level → (Down) Enter Password**.
The entry surface is a 26-letter `A`–`Z` on-screen keypad (no digits/symbols), with a
**maximum input length of 12 characters** (RAM-proven). The validator
(`0x08005BAC`) scans the 30 table entries with a case-sensitive `strcmp`
(`0x0801186C`) and, on a hit, sets a "correct" flag and raises the unlocked-level /
area variables.

**The accepted set is exactly the 30 codes already published on 3rd party cheat indexes.** Every
ROM entry matches the published list byte-for-byte (§6, §6b). There is **no checksum,
no generator/decoder pair, no second algorithmic format, no key-mask button code and
no reachable debug menu** (§6b, §8). Consequently **no novel accepted code exists** —
this is a proven, closed negative, not a failure to find one (see §6b for the counts
and the exhaustive argument).

Passwords unlock levels (stage areas), and indirectly the two extra vehicles in the
Garage (`TROPHY TRUCK`, `MILITARY VEHICLE`). A quirk: the code published as "stage 30"
(`SCULLY`) clamps to unlocked-level index `28`, so the highest actually selectable
mission is **29**, not 30.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb (`:317`), `SDL_AUDIODRIVER=dummy`, `-3` scale.
  Keymap used: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, L=`a`, R=`s`,
  D-pad = arrow keys. Keys held 70–150 ms.
* **Menu path to the code screen:**
  1. Title `PRESS START` → press `Start`.
  2. Main Menu (3 items: SMUGGLER'S MISSION / TURF WAR / OPTIONS) → `A` on
     **SMUGGLER'S MISSION**.
  3. **SELECT LEVEL** screen (shows level number, stage preview, and the orange
     `ENTER PASSWORD` hint at the bottom). Press **Down** then **A**.
  4. **ENTER PASSWORD** screen: 3-row `A`–`Z` keypad. `Left`/`Right` move a linear
     26-cell ring (A=0 … Z=25; Left from A wraps to Z). `A` appends the highlighted
     letter; `B` deletes one character. Validation is automatic on each append — a
     correct code immediately shows **PASSWORD CORRECT**; wrong codes simply remain
     in the buffer (no visible INVALID message was ever triggered — see §8).
* **Codes tested (published, all verified in ROM):** `BEGIN` (stage 1),
  `SCULLY` (stage 30 label). Both accepted. Wrong inputs tested: `BEGIX`,
  `ZZZZ`, and 12×`A` — none accepted (§7).
* **A-Z keypad typing helper** (used to mint/enter codes deterministically):
  `typecode.py` in `/tmp/smugglersrun/` (follows the linear cursor ring).
* **RAM observation method:** GDB stub was unavailable (port 2345 occupied by another
  agent's mGBA), so evidence was gathered by mGBA savestate diffing: `.ss1` is a PNG
  with a zlib `gbAs` chunk; decompressing yields a 397,312-byte state with IWRAM at
  file offset `0x19000`. Script: `statediff.py`. `RAM address 0x0300xxxx` maps to
  state offset `0x19000 + 0xxxxx`.

## 4. Address map

| Item | Address (ROM / file) | Notes |
|---|---|---|
| crt0 / entry | `0x080000C0` / `0xC0` | stock ARM branch from header |
| `main` pointer | `0x08005455` / `0x5454` | Thumb, literal at header `+0x1C8` |
| Password string pool | `0x080147A8`–`0x080148D2` / `0x147A8`–`0x148D2` | 30 NUL-terminated uppercase strings, packed |
| Stage-30 string `SCULLY` | `0x080147A8` | last entry of the pool |
| **Password pointer table** | `0x085C49D0` / `0x5C49D0` | 30 × `u32`; index 0 = stage 1 (`BEGIN`), index 29 = stage 30 (`SCULLY`) |
| Unlock-threshold byte table | `0x080148D2` / `0x148D2` | 33 bytes, values 7–17; per-area level-count bounds used by menu code at `0x08006300`, `0x080063E0` — **not** a code table |
| **Validator** | `0x08005BAC` / `0x5BAC` | entry `push {r4,r5,lr}`; scans 30 entries |
| `strcmp` compare helper | `0x0801186C` / `0x1186C` | standard exact, case-sensitive C `strcmp` |
| Append-char handler | `0x08005C24` / `0x5C24` | appends `char(0x41 + keypad_index)` to input buffer |
| Delete-char handler | `0x08005C60` / `0x5C60` | removes last character |
| Clear-buffer handler | `0x08005C90` / `0x5C90` | zeroes 60 bytes at input buffer |
| Text bank (0x3C-byte slots) | `0x0805C7A20` / `0x5C7A20` | UI strings; slot 21 = `ENTER PASSWORD`, 50 = `PASSWORD CORRECT`, 51 = `PASSWORD INVALID` |
| `PASSWORD:` (mission summary) | `0x0805C7C00` / `0x5C7C00` | displayed after missions |
| **Input buffer (12 bytes)** | `0x030036B0` (IWRAM) | holds the typed password + NUL |
| **Input length byte** | `0x030037B0` (IWRAM) | number of typed characters |
| **Password-correct flag** | `0x030037AC` (IWRAM) | set to `1` on a valid code |
| Unlocked-level index | `0x03003498` (IWRAM) | set to matched table index (clamped to 28) |
| Area / stage-unlock var | `0x030034A0` (IWRAM) | 1 if level>10, 2 if >18, 3 if index>28 |
| Keypad cursor / screen vars | `0x0300419C`, `0x030041A4` | UI state |

## 5. Algorithm

Reimplementation of the validator (`0x08005BAC`):

```
validate(input):                       # input = NUL-terminated string at 0x030036B0
    flag_correct(0x030037AC) = 0
    for idx in 0 .. 29:                # cmp r4,#29 ; bls  -> 30 iterations
        expected = *(u32*)(0x085C49D0 + idx*4)
        if strcmp(input, expected) == 0:          # 0x0801186C, exact & case-sensitive
            flag_correct(0x030037AC) = 1
            unlocked = idx
            if idx > 28: unlocked = 28            # cmp r4,#28 ; clamp
            *(u8*)0x03003498 = unlocked
            area = 0
            if unlocked > 10: area = 1
            if unlocked > 18: area = 2
            if idx      > 28: area = 3
            *(u8*)0x030034A0 = area
            return ACCEPT
    return REJECT
```

Key properties:
* **Exact equality only.** The comparison is a plain case-sensitive `strcmp`; there
  is no alphabet remapping, no font/tile conversion, no case folding and no wildcard
  symbol. Two codes cannot be aliases of one another.
* **No checksum, no arithmetic, no permutation, no PRNG.** The "format" is simply
  "one of 30 hard-coded ASCII strings".
* Length is capped at 12 characters by the input routine (RAM evidence below); all
  30 valid strings are 4–9 characters long, so the cap does not hide any code.
* The UI calls the check after each appended character, so a code is accepted the
  instant its final character makes it equal to a table entry.
* **Text encoding checked:** all UI labels — including the keypad letters and
  `ENTER PASSWORD` / `PASSWORD CORRECT` / `PASSWORD INVALID` — are plain uppercase
  ASCII in a bank of fixed 0x3C-byte slots at `0x0805C7A20`; no font/tile-index
  encoding is used for menu text, so `strings` enumeration was complete for this
  surface (contrast guide §11). The keypad's displayed letters are generated from
  the keypad index (`'A' + index`, handler `0x08005C24`), not read from a text bank.

## 6. Tables

**The complete accepted set (extracted from the ROM pointer table; stage numbers are
the published labels):**

| Stage | Password | Stage | Password | Stage | Password |
|---:|---|---:|---|---:|---|
| 01 | BEGIN | 11 | INCOMING | 21 | OFFROAD |
| 02 | DELIVER | 12 | THEFUZZ | 22 | SNOWJOKE |
| 03 | FIRSTBLUD | 13 | DESERTED | 23 | ICYKILL |
| 04 | PACKAGE | 14 | SNATCH | 24 | LATENITE |
| 05 | OVERLAND | 15 | GRAB | 25 | CONTRA |
| 06 | BOYRACER | 16 | ROCKNROLL | 26 | FBEYE |
| 07 | THEHEIST | 17 | HEREWEGO | 27 | DANGER |
| 08 | BIGCHEESE | 18 | OVERKILL | 28 | ALLOVER |
| 09 | MONKEY | 19 | DIAMONDS | 29 | ATLAST |
| 10 | LEFTFIELD | 20 | RALLYRIOT | 30 | SCULLY |

All 30 were verified against the 3rd party cheat index list (archived topic
3rd party cheat indexes, captured 2020-08-06)
and all 30 literals are present in the ROM. A byte-for-byte comparison of the ROM
table strings to the published strings returned "all match: True".

**Field/flag layout**

| Variable | Address | Meaning |
|---|---|---|
| input string | `0x030036B0` | typed password, NUL-terminated, 12-byte capacity |
| input length | `0x030037B0` | `u8` count |
| correct flag | `0x030037AC` | `1` = accepted |
| unlocked level | `0x03003498` | 0-based index of highest unlocked mission; clamp 28 |
| area var | `0x030034A0` | `1`>10, `2`>18, `3`>28 (gates desert/snow and vehicles) |

## 6b. Enumeration

### Space definition and count
* **Alphabet:** 26 symbols (`A`–`Z`), the on-screen keypad. No digits, symbols,
  lowercase or wildcard.
* **Length:** 1–12 characters (12 is the RAM-proven input cap; 26^12 possible strings
  of maximum length).
* **Total representable input strings:** `Σ_{L=1..12} 26^L = 99,246,114,928,149,462`
  (≈ 9.925 × 10^16).
* **Accepted set:** exactly **30** strings — the 30 table entries listed in §6.
  Acceptance is pure equality, so the acceptance probability of a random string is
  `30 / 9.9e16 ≈ 3e-16`.
* **Validator model:** given in §5; it agrees with the ROM on every accepted code
  tested (`BEGIN`, `SCULLY`) and on every rejected input tested (`BEGIX`, `ZZZZ`,
  12×`A`).

### Novel codes
**No unpublished accepted code exists, and this is proven rather than assumed:**

1. The only comparison the game makes against user input is the loop at
   `0x08005BB8`–`0x08005C1C`, bounded by `cmp r4,#29 ; bls` — exactly 30 iterations.
2. The pointer table it walks, `0x085C49D0`, contains exactly 30 pointers, and
   those 30 targets are the only password strings in the image (the pool
   `0x080147A8`–`0x080148D2` contains no 31st string).
3. The comparator (`0x0801186C`) is exact `strcmp`: no alias, case-fold, truncation
   or wildcard can admit a 31st spelling.
4. All 30 entries equal the 30 published codes byte-for-byte (§6).

Therefore the set of accepted codes **is** the public list; there is nothing to mint
that is both accepted and unpublished. (Had a generator/decoder existed, this section
would carry a novel code + emulator proof; its absence is established by points 1–4
and by the exhaustive string/pointer scans above.)

### Bounds proven by rejection (Observed)
| Input | Length | Result | RAM evidence |
|---|---:|---|---|
| `BEGIX` (near-miss of valid `BEGIN`) | 5 | stayed on ENTER PASSWORD, no flag | screen capture `pw_begix.png` |
| `ZZZZ` | 4 | stayed on ENTER PASSWORD; `B` reduced length 4→3 | `before_B.ss1`/`after_B.ss1`: input `5a5a5a5a00…` → `5a5a5a00…`, len `04`→`03`, flag `0` |
| `AAAAAAAAAAAA` (13th `A` ignored) | 12 | stayed on ENTER PASSWORD | `invalid13.ss1`: `0x030036B0` = 12×`0x41`, `0x030037B0`=`0x0C`, `0x030037AC`=`0` |

### Accepted-code effect (Observed)
`SCULLY` (table index 29):
* `base.ss1` → `scully_correct.ss1` RAM diff:
  `0x030036B0 = "SCULLY\0"`, `0x030037B0 = 0x06`,
  `0x030037AC: 0x00 → 0x01`,
  `0x03003498: 0x00 → 0x1C (28)`,
  `0x030034A0: 0x00 → 0x03`.
* Screen: **PASSWORD CORRECT** (`pw_scully2.png`); afterwards SELECT LEVEL offers
  levels 26–29 on the SNOW STAGE (`after_correct_level.png`), and the Garage now
  offers `TROPHY TRUCK` and `MILITARY VEHICLE` (`garage_unlocked1.png`,
  `garage_unlocked2.png`) — before the code only `BUGGY` was selectable (`veh1.png`).
* `BEGIN` (index 0) similarly produced PASSWORD CORRECT (`pw_begin.png`).

### Published "stage 30" vs actual payload
`SCULLY` is published as the level-30 password, but index 29 is clamped to 28 by
`0x08005BDA–0x08005BE0`; the highest mission the game actually lets you select
afterwards is **29** (`level30b.png`, after repeated Right presses the selector stops
at 29). This is the payload-vs-label trap (guide §16.15).

## 7. Validation evidence

**Observed** (emulator + savestate RAM reads)
* All menus/screens walked: title, Main Menu (3 items), Options (music only),
  Select Level (level select + `ENTER PASSWORD`), Select Stage (Forest/Desert/Snow),
  Garage (3 vehicles), briefing, race, Pause (Resume/Restart/Quit), Enter Password.
  Screenshots are on disk in `/tmp/smugglersrun/`.
* `BEGIN`, `SCULLY` accepted; wrong inputs rejected; length cap 12; B = backspace;
  Left from A wraps to Z; Down on keypad does not reveal a hidden submit cell.
* RAM diffs as quoted in §6b.

**Derived** (disassembly)
* Validator structure, loop bound 30, table base, strcmp identity, flag/unlock/area
  writes, clamp at 28, 33-byte unlock-threshold table at `0x080148D2`.
* Password string pool and exact 30-entry pointer table.

**Inferred**
* The `PASSWORD INVALID` text (slot 51) exists but no reachable input was found that
  displays it: wrong codes simply remain in the keypad buffer. Its trigger is unknown
  (possibly dead/unused UI text). Also not established: whether the three pre-set
  password labels were intended to unlock vehicles directly or only via the
  level/area variables.

## 8. Unknowns

* Trigger for the `PASSWORD INVALID` string — not produced by wrong codes, backspace,
  Start, L, R or Select on the keypad. No debug/test menu string exists in the image.
* Whether any *unreachable* 31st password was cut from the build (no evidence of one:
  the table and pool both stop at 30).
* The meaning of the two extra bytes in the 33-byte threshold table at `0x080148D2`
  (the other 31 appear to be per-area level counts).
* No GameShark/CodeBreaker/memory-edit codes were investigated (out of scope).

## 9. Tooling

* `strings`, `grep`, `xxd`, `file`, `sha*` (Phase 0/1).
* Python + `struct`/`capstone` for literal/pointer/BL scans and table extraction.
* `arm-none-eabi-objdump -M force-thumb` for the validator and handlers.
* `webfetch` on the Wayback Machine copy of the 3rd party cheat indexes topic for the published list
  (3rd party cheat indexes themselves returns 403). Fetched page content was treated strictly as data.
* mGBA 0.10.5 (`-3`, SDL dummy audio) on `Xvfb :317` + `openbox`; `xdotool` XTEST
  input; `scrot` screenshots.
* `key.py` (timed key presses), `typecode.py` (linear keypad navigation),
  `statediff.py` (`.ss1` → `gbAs` zlib inflate → IWRAM/EWRAM diff) — all in
  `/tmp/smugglersrun/`.

## 10. Legal note

No ROM data or copyrighted assets are redistributed here. Only hashes, addresses,
algorithms, flag bits and the (already published) password strings are documented.
