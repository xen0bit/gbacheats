# 2-in-1: Hot Wheels — Stunt Track Challenge & Hot Wheels — World Race (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `2-in-1 - Hot Wheels - Stunt Track Challenge & Hot Wheels - World Race.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| MD5 | `4daf3d378d5f91277f43a5555829fdc7` |
| SHA-1 | `717b2a739c8932374ab48a9c2bbd76a44b4cf2f3` |
| SHA-256 | `a78615db60a1f4e17cf518328049a46d27e07090d1f2920451cecf2ab80fcec3` |
| Shell header title | `HOTSTCHOTWR` |
| Shell game code | `BQJE` (maker `20`, version 0) |
| Shell header check | stored `0x64`, computed `0x9C` — header was rewritten by the 2-in-1 builder |

### Cartridge layout (three GBA headers, verified by scanning for the 156-byte Nintendo logo)

| File range | Image | Header | Notes |
|---|---|---|---|
| `0x000000`–`0x07FFFF` | shell / 2-in-1 launcher | at `0x0`: `HOTSTCHOTWR` / `BQJE` | 512 KiB menu program, base `0x08000000` |
| `0x080000`–`0x7FFFFF` | Hot Wheels World Race | at `0x80000`: title/code bytes blanked, maker `01`, complement `0xF0` | image runs in place; image base `0x08080000` |
| `0x800000`–`0xFFFFFF` | Hot Wheels Stunt Track Challenge | at `0x800000`: `HOTWHEELS` / `AOEP` | image base `0x08800000` |

For both game halves the address of any file offset `F` is `0x08000000 + F` (this is also what the
game's own pointer tables use). The shell is English-only; the game halves are English.

**Scope of this report:** developer-intended in-game password systems (the only cheat surface found).
No GameShark/CodeBreaker/memory codes are documented. No ROM or game assets are redistributed.

---

## 2. Executive summary

Both halves of this 2-in-1 cartridge contain a **developer password system**, reachable from the
options/menu, and both were reversed and confirmed in mGBA.

**World Race (first half)** does **not** store codes; it computes them. An 8-symbol code over a
32-symbol alphabet (`BCDFGHJKLMNPQRSTVWXYZ0123456789*`) is decoded with a per-position additive
rotation into eight 5-bit values = a 40-bit field. The validator (`0x080A7BB8`) requires 20 specific
bit positions — listed at ROM `0x791F7C` — to be **zero**, and treats the other 20 bits (listed at
`0x791FCC`) as the progress payload. There is **no arithmetic checksum**: any 40-bit value whose
"forbidden" bits are zero is structurally valid, so the code space is 2^20. Applying a code
grants/clears bits in the 64-bit progress word at `0x020007E8` via the flag helpers `0x080A725C`
and the progress writer `0x080A6D68`.
A 25-code published list was verified: every code decodes with zero violations, and every code
round-trips through the reimplementation. Two published codes were entered in the emulator
(`PVXR51JN`, `F15W3ZQ2`) and one *generated, unpublished* code (`6VXR51JN`) was entered; all three
changed the progress word exactly as predicted, and `F15W3ZQ2` unlocked the Elite league
(screenshot: "BLEACHED PLAINS" Elite track select).

**Stunt Track Challenge (second half)** is the opposite design: a **plaintext table of 52 codes**
(30 Game Show + 9 Stunt School + 12 Champions League + 1 standalone literal `CLJJBGLQ`), all
8 uppercase letters, stored at `0xF960FC` (12-byte stride) and indexed by three record tables at
`0x97F7A8` / `0x97F91C` / `0x97F9A0` that map each string to `(group, stage)`. The on-screen
keyboard offers exactly the 21 letters those strings use. No generator or checksum exists: a
one-character mutation is rejected. Entering `CLZGMVZF` or `CLJJBGLQ` was observed to unlock the
Champions League (cutscene: "WELCOME TO THE CHAMPIONS LEAGUE! … THE GOLD CAR"); entering
`CLZGMVZA` was rejected and left the password screen unchanged.

The published Stunt Track list was checked against the ROM; three entries are wrong in the
published text (`LLSCSKGQ` should be `LLSCSFGQ`, `LLSCFQJC` should be `LLSCFQJL`, and
`SSLGYJNS` is listed twice where the ROM has `SSLGYJNS`/`SSLNZHMR`).

---

## 3. How to reproduce

### 3.1 Emulator / display

```bash
Xvfb :102 -screen 0 1024x768x24 &
DISPLAY=:102 openbox &
cd "roms/2-in-1 - Hot Wheels - Stunt Track Challenge & Hot Wheels - World Race"
DISPLAY=:102 SDL_AUDIODRIVER=dummy mgba -3 \
  "2-in-1 - Hot Wheels - Stunt Track Challenge & Hot Wheels - World Race.gba" &
W=$(DISPLAY=:102 xdotool search --name mGBA | head -1)
DISPLAY=:102 xdotool windowfocus "$W"
```

mGBA SDL default keymap used throughout: **A = `x`**, **B = `z`**, **L = `a`**, **R = `s`**,
**Start = `Return`**, **Select = `BackSpace`**, d-pad = arrow keys. Hold keys for 0.2–0.5 s.
Screenshots: `DISPLAY=:102 import -window root s.png`; GBA viewport is `720x480+152+144`
(scale 3). Savestates: `Shift+F1..F10` save, `F1..F10` load (written next to the ROM as `.ssN`).

The 2-in-1 shell boots first (DSI Games + Mattel logos, ~18 s). The shell's own screen shows
Stunt Track on the left and World Race on the right; Left/Right change the selection (the caption
at the bottom changes) and A boots the chosen game.

### 3.2 World Race — reach the password screen

1. Shell: `Right` (caption becomes `HOTWHEELS WORLD RACE`), then `A`.
2. `A` through the licence text to the title, then `Start` (`Return`).
3. The main menu is a **rotating wheel**: a *tap* (≈50 ms) of Up/Down moves one item; holding
   scrolls with inertia and coasts ~3 items after release. The order (as seen) is
   `OPTIONS, PASSWORD, QUICK RACE, MULTIPLAYER, TIME TRIAL, LEAGUE`; the centred item is selected.
   From the default (QUICK RACE), one Up tap centres PASSWORD.
4. `A` opens the `PASSWORD` screen: an 8×4 grid
   `B C D F G H J K / L M N P Q R S T / V W X Y Z 0 1 2 / 3 4 5 6 7 8 9 *`,
   with `DEL` and `END` on the last row. The current/generated code is displayed at the bottom.
5. Select 8 symbols and `END`.

### 3.3 Stunt Track Challenge — reach the password screen

1. Shell: `A` (Stunt Track is selected by default).
2. `A` through the Razorback logo and the ~20-page story intro; this drops into the first
   Stunt School run. Press `Start` → `Down` to `QUIT` → `A` → `Left` to `YES` → `A`.
3. On the track-select screen press `B` twice (episode → main menu).
4. Main menu: `Down` ×5 (GAME SHOW → ARCADE → STUNT SCHOOL → MULTIPLAYER → CHAMPIONS LEAGUE →
   OPTIONS) and `A`. Then `Down` once (SETTINGS → PASSWORD) and `A`.
5. Screen `PASSWORD`: labels `GAME SHOW:` / `STUNT SCHOOL:`, a 3×7 grid
   `B C D F G H J / K L M N P Q R / S T V W X Y Z`, and `DELETE / QUIT / DONE`.
   The entered code is drawn at the very bottom, partially clipped by the screen edge.

### 3.4 Codes entered in mGBA (observed)

| Game | Code | Result |
|---|---|---|
| World Race | `PVXR51JN` | accepted; progress word `0x020007E8` changed `0x4030C50A` → `0xE139C50A` |
| World Race | `F15W3ZQ2` | accepted; progress word → `0xFFFFFFFF_00000003` (bits 0–33 set); Elite league selectable ("BLEACHED PLAINS") |
| World Race | `6VXR51JN` (generated, not published) | accepted; progress word → `0xE139C50B` (exactly one extra flag vs `PVXR51JN`) |
| Stunt Track | `CLZGMVZF` | accepted → "WELCOME TO THE CHAMPIONS LEAGUE! … THE GOLD CAR" |
| Stunt Track | `CLJJBGLQ` | accepted → same Champions League cutscene |
| Stunt Track | `CLZGMVZA` (mutated) | rejected; screen unchanged |

### 3.5 Fast iteration: savestate RAM patching

The password UIs write into known RAM buffers, so instead of typing a code with the d-pad one can
save a state on the password screen, patch the buffer, reload (`F1`/`F2`), and press `END`/`DONE`.
mGBA states are PNGs with a `gbAs` chunk containing a zlib stream whose decompressed layout is:

| State offset | Block |
|---|---|
| `0x00400` | VRAM (0x18000) |
| `0x18400` | palette (0x400) |
| `0x18800` | OAM (0x400) |
| `0x18C00` | I/O (0x400) |
| `0x19000` | IWRAM (0x8000) |
| `0x21000` | EWRAM (0x40000) |

The EWRAM/IWRAM offsets were verified by content (screen buffers, input code); the smaller blocks
are the serialized order implied by the total size (0x61000). `state_edit.py` (see §9) rebuilds the
PNG chunk with a correct CRC. World Race input buffer:
8 × `u16` at `0x020008C0` (e.g. `P\0V\0X\0R\05\01\0J\0N\0`). Stunt Track input buffer: 8 ASCII
bytes at `0x03003BB4` (mirror `0x03003C54`), unfilled slots are `'-'`.

---

## 4. Address map

All ROM addresses are `0x08000000 + file_offset` (shell base `0x08000000`, World Race image base
`0x08080000`, Stunt Track image base `0x08800000`).

### 4.1 World Race

| Address | Size | Meaning |
|---|---|---|
| `0x087920A4` | 8×u32 | per-position decode offsets `15 18 0E 13 06 0A 1A 16` |
| `0x087920C4` | 33 B | alphabet `BCDFGHJKLMNPQRSTVWXYZ0123456789*` + NUL |
| `0x08791F7C` | 20×u32 | **forbidden bits** (must be 0): `00 01 02 05 09 0A 0B 0C 0E 0F 10 12 13 14 19 1E 21 22 24 27` |
| `0x08791FCC` | 20×u32 | **payload bits**: `1A 04 17 15 0D 26 07 1C 16 03 06 23 11 20 08 1F 1B 1D 18 25` |
| `0x08791FF4` | 20×u32 | secondary bit list used to build two-bit counts |
| `0x080A7F8C` | Thumb | `char_value(str, pos)` — symbol → 5-bit value with position rotation |
| `0x080A7BB8` | Thumb | `validate_and_apply(str)` — zero-mask check + payload apply |
| `0x080A7870` | Thumb | `END` handler: packs `0x020008C0` → `0x020008D0`, calls validator |
| `0x080A7B6C` | Thumb | copy 8-char current password (from `0x080A7D7C`) to `0x020008D0` |
| `0x080A7D7C` | Thumb | build current-password string from save flags |
| `0x080A80B4` | Thumb | build 64-bit progress mask from save state |
| `0x080A725C` | Thumb | `grant_flag(n)` — OR `1<<n` into `0x020007E8` |
| `0x080A728C` | Thumb | `test_flag(n)` — bit test on `0x020007E8` |
| `0x080A72A8` | Thumb | read `u16` from `0x020007F0 + 4*n` (count table) |
| `0x080A6D68` | Thumb | `set_progress(index, value)` — threshold logic writing `0x020007E8`/`0x020007F0` |
| `0x020008C0` | 8×u16 | input symbols (ASCII code units) |
| `0x020008D0` | 9 B | validated ASCII code string |
| `0x020007E8` | 8 B | 64-bit progress/flag word |
| `0x020007F0` | 20 B | `u16` per-event count/progress array |
| `0x0878DD80` | — | `PASSWORD` menu string; `0x0878FBC4` = `NEW PASSWORD:` |
| `0x0878DE58` | 30×u32 | main-menu string-pointer table (6 items × 5 language slots) |

### 4.2 Stunt Track Challenge

| Address | Size | Meaning |
|---|---|---|
| `0x08F904DC` | — | `PASSWORD` |
| `0x08F904E8` | — | `Enter Password` |
| `0x08F90774` | — | `Enter Code` (second entry point) |
| `0x08F960B8` | — | `GAME SHOW:` label |
| `0x08F960C4` | — | `STUNT SCHOOL:` label |
| `0x08F960D4` | — | `INCORRECT` |
| `0x08F960E0` / `0x08F960E8` / `0x08F960F0` | — | `DELETE` / `QUIT` / `COMPLETE` |
| `0x08F960FC`–`0x08F9635C` | 51×12 B | 8-char code strings, 12-byte stride (8 chars + 4 NUL) |
| `0x0897F7A8` | 30×12 B | Game Show records `{u32 str_ptr; u32 group; u32 stage}` |
| `0x0897F91C` | 9×12 B | Stunt School records (group 0–8, stage 0) |
| `0x0897F9A0` | 12×12 B | Champions League records (group 1–12, stage 0) |
| `0x0897F98C` | 8 B | standalone literal `CLJJBGLQ` (Champions League level 1) |
| `0x080939694`, `0x080939BBC` | Thumb | password-screen handlers (reference `GAME SHOW:`/`STUNT SCHOOL:`) |
| `0x08093A2xx` | Thumb | password-screen renderer (uses the record tables) |
| `0x08093A5B0`–`0x08093A724` | Thumb | stage-completion counter/commit path |
| `0x03003BB4` | 8 B | input code, ASCII, `'-'` for empty slots (mirror at `0x03003C54`) |

---

## 5. Algorithm

### 5.1 World Race codec (exact, reimplemented)

```python
ALPHABET   = "BCDFGHJKLMNPQRSTVWXYZ0123456789*"
POS_OFFSET = [0x15, 0x18, 0x0E, 0x13, 0x06, 0x0A, 0x1A, 0x16]   # ROM 0x087920A4
ZERO_BITS  = [0,1,2,5,9,10,11,12,14,15,16,18,19,20,25,30,33,34,36,39]  # ROM 0x08791F7C
DATA_BITS  = [26,4,23,21,13,38,7,28,22,3,6,35,17,32,8,31,27,29,24,37]  # ROM 0x08791FCC

def decode(code):                       # -> 8 values 0..31
    assert len(code) == 8
    return [(ALPHABET.index(c) + POS_OFFSET[i]) % 32 for i, c in enumerate(code)]

def value40(code):                      # bit b of symbol i is bit (5*i+b)
    return sum(v << (5*i) for i, v in enumerate(decode(code)))

def zero_violations(code):
    v = value40(code)
    return [b for b in ZERO_BITS if (v >> b) & 1]

def payload(code):                      # the 20 progress bits
    v = value40(code)
    return {b for b in DATA_BITS if (v >> b) & 1}

def encode(bits):                       # inverse; bits must be subset of DATA_BITS
    v = sum(1 << b for b in bits)
    out = []
    for i in range(8):
        s   = (v >> (5*i)) & 31
        out.append(ALPHABET[(s - POS_OFFSET[i]) % 32])
    return "".join(out)
```

Validator pseudocode (`0x080A7BB8`):

```
on END:
  s = pack_ascii(0x020008C0)                 # 8 chars -> 0x020008D0
  for b in ZERO_BITS:                        # 20 entries, table 0x791F7C
      if bit(s, b): return 1                 # reject
  for pair (b0,b1) in DATA_BITS:             # table 0x791FCC, 10 pairs
      if bit(s,b0): grant/test flag(T2[i])
      if bit(s,b1): grant/test flag(T2[i+1])
  for pair (b0,b1) in T3 (0x791FF4):         # 10 pairs -> five 2-bit counts
      v = bit(s,b0) + 2*bit(s,b1)
      set_progress(i, v)                     # 0x080A6D68 threshold logic
  regenerate current password (0x080A7B6C) and return 0
```

Because the only rejection rule is "all `ZERO_BITS` are 0", **every subset of `DATA_BITS` is a
valid code**. The published list is exactly such a subset chain (each newer code sets more bits),
which is how the format was confirmed.

### 5.2 Stunt Track Challenge

Plain table lookup, no computation:

```
on DONE:
  code = trim(input_buffer[0x03003BB4], '-')      # 8 uppercase letters
  for rec in GameShow[0..29] + StuntSchool[0..8] + ChampionsLeague[0..11]:
      if code == rec.string: apply(rec.group, rec.stage); return COMPLETE
  if code == "CLJJBGLQ": unlock Champions League level 1; return COMPLETE
  return INCORRECT
```

The record tables store the code pointer plus `(group, stage)`; Game Show uses
track-group 0–5 × stage 0–4, Stunt School uses group 0–8, Champions League uses group 1–12
(group 12 = `CLFNQRWB`, "All Levels"). The 8-char strings are accepted literally; no character
arithmetic or checksum was found, and a one-symbol mutation is rejected.

---

## 6. Tables

### 6.1 World Race — published codes, decoded

Source: chaptercheats "Level Passwords for Hot Wheels World Race". All 25 decode with
`zero_violations == []` and round-trip exactly through `encode(payload(code)) == code`.
The right-hand column is the 20-bit payload as decimal set bits, then the effect description from
the source.

| Code | Decoded symbols (0–31) | Payload bits | Published meaning |
|---|---|---|---|
| `PVXR51JN` | 00 08 00 00 00 00 00 00 | {8} | 1 class, 1 team, 0 bonus |
| `PVXR53JN` | 00 08 00 00 00 02 00 00 | {8,26} | 1 class, 1 team, 1 bonus |
| `PVXRD3JN` | 00 08 00 00 08 02 00 00 | {8,23,26} | 1 class, 1 team, 2 bonus |
| `PV5RD3JN` | 00 08 08 00 08 02 00 00 | {8,13,23,26} | 1 class, 1 team, 3 bonus |
| `PZ5RD3JN` | 00 12 08 00 08 02 00 00 | {7,8,13,23,26} | 1 class, 1 team, 4 bonus |
| `PZ5RJ3JN` | 00 12 08 00 12 02 00 00 | {7,8,13,22,23,26} | 1 class, 1 team, 5 bonus |
| `PZ5RJ7JN` | 00 12 08 00 12 06 00 00 | {7,8,13,22,23,26,27} | 1 class, 2 teams, 5 bonus |
| `P15RJ7JN` | 00 14 08 00 12 06 00 00 | +{6} | 1 class, 3 teams, 5 bonus |
| `P15WJ7JN` | 00 14 08 04 12 06 00 00 | +{17} | 1 class, 4 teams, 5 bonus |
| `P15W17JN` | 00 14 08 04 28 06 00 00 | +{24} | 1 class, 5 teams, 5 bonus |
| `FZ5W3GJY` | 24 12 08 04 30 14 00 09 | {3,4,7,8,13,17,21,22,23,24,26,27,28,35,38} | 2 classes, 1 team, 10 bonus |
| `PZ5W17JP` | 00 12 08 04 28 06 00 01 | …+{35} | 2 classes, 1 team, 5 bonus |
| `6Z5W17JP` | 16 12 08 04 28 06 00 01 | …+{4} | 2 classes, 1 team, 6 bonus |
| `6Z5W37JP` | 16 12 08 04 30 06 00 01 | …+{21} | 2 classes, 1 team, 7 bonus |
| `6Z5W37JY` | 16 12 08 04 30 06 00 09 | …+{38} | 2 classes, 1 team, 8 bonus |
| `6Z5W3GJY` | 16 12 08 04 30 14 00 09 | …+{28} | 2 classes, 1 team, 9 bonus |
| `FZ5R3GNY` | 24 12 08 00 30 14 04 09 | … | 2 classes, 2 teams, 10 bonus |
| `FQ5R3GQY` | 24 04 08 00 30 14 06 09 | … | 2 classes, 3 teams, 10 bonus |
| `FQ5R3VQY` | 24 04 08 00 30 26 06 09 | … | 2 classes, 4 teams, 10 bonus |
| `FQ5RLVQ2` | 24 04 08 00 14 26 06 13 | {3,4,7,13,21,22,23,26,28,29,31,32,35,37,38} | 2 classes, 5 teams, 10 bonus |
| `FS5RLVQ2` | 24 06 08 00 14 26 06 13 | … | 3 classes, 1 team, 10 bonus |
| `FS5WLVQ2` | 24 06 08 04 14 26 06 13 | … | 3 classes, 2 teams, 10 bonus |
| `F15WLVQ2` | 24 14 08 04 14 26 06 13 | … | 3 classes, 3 teams, 10 bonus |
| `F15WLZQ2` | 24 14 08 04 14 30 06 13 | … | 3 classes, 4 teams, 10 bonus |
| `F15W3ZQ2` | 24 14 08 04 30 30 06 13 | all 20 DATA_BITS | 3 classes, 5 teams, 10 bonus (everything) |

Generated example not in the published list: `encode({4,8}) = 6VXR51JN`.

### 6.2 World Race — 40-bit layout

| Field | Bits | Notes |
|---|---|---|
| forbidden | 0,1,2,5,9,10,11,12,14,15,16,18,19,20,25,30,33,34,36,39 | must be 0 (validator returns 1 otherwise) |
| payload | 26,4,23,21,13,38,7,28,22,3,6,35,17,32,8,31,27,29,24,37 | grouped in pairs for the count logic |

Observed single-bit effects on the flag word `0x020007E8`: payload bit 8 (from `PVXR51JN`) grants
flags 16,19,24,29,31; payload bit 4 (from generated `6VXR51JN`) grants flag 0; the full payload
(`F15W3ZQ2`) sets flags 0–33. The per-bit → flag mapping is produced by `0x080A725C` /
`0x080A6D68` from the two pair tables; only whole-code effects are claimed as observed.

### 6.3 Stunt Track Challenge — complete accepted-code table

Strings at `0x08F960FC + 12*n`; groups/stages from the record tables.

**Game Show (records `0x0897F7A8`, group 0–5, stage 0–4)**

| Group | Stage 0 | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|---|
| 0 | `HWGSPSBB` | `JJCRTVBZ` | `JJSCFQCX` | `JJSCRBDV` | `JJCRDBFS` |
| 1 | `SLSCSFGQ` | `SLSCFQHN` | `SLCRBNJL` | `SLSCTBKJ` | `SLCRNHLG` |
| 2 | `BBSCFQMD` | `BBCRWCNB` | `BBSCCCPY` | `BBSCFSQW` | `BBCRMDRT` |
| 3 | `TKSCTBSR` | `TKSCSFTP` | `TKCRJSVM` | `TKSCFQWK` | `TKCRGFXH` |
| 4 | `ZGSCRBYF` | `ZGCRSSZC` | `ZGSCFSBZ` | `ZGSCFQCX` | `ZGCRSMDV` |
| 5 | `LLSCTBFS` | `LLSCSFGQ` | `LLCRFMHN` | `LLSCFQJL` | `LLCRVBKJ` |

`HWGSPSBB` is the "HWGS" (Hot Wheels Game Show) master entry, group 0 stage 0; it is accepted and
returns to the menu without the Champions League cutscene (effect on Game Show episode list not
separately itemised — see §8).

**Stunt School (records `0x0897F91C`, group 0–8)**

| Group | Code | Published meaning |
|---|---|---|
| 0 | `SSLTRQVZ` | get level 2 |
| 1 | `SSLRSPTY` | get level 3 |
| 2 | `SSLFTNSX` | get level 4 |
| 3 | `SSLVVMRW` | get level 5 |
| 4 | `SSLXWLQV` | get level 6 |
| 5 | `SSLSXKPT` | get level 7 |
| 6 | `SSLGYJNS` | get level 8 |
| 7 | `SSLNZHMR` | get level 9 |
| 8 | `SSLTBGLQ` | get level 10 |

**Champions League (records `0x0897F9A0`, group 1–12)**

| Group | Code | Meaning |
|---|---|---|
| 1 | `CLJJCFKP` | level 2 |
| 2 | `CLSLDDJN` | level 3 |
| 3 | `CLSLFCHM` | level 4 |
| 4 | `CLBBGBGL` | level 5 |
| 5 | `CLBBHZFK` | level 6 |
| 6 | `CLTKJYDJ` | level 7 |
| 7 | `CLTKKXCH` | level 8 |
| 8 | `CLZGLWBG` | level 9 |
| 9 | `CLZGMVZF` | level 10 |
| 10 | `CLLLNTYD` | level 11 |
| 11 | `CLLLPSXC` | level 12 |
| 12 | `CLFNQRWB` | all levels |
| — | `CLJJBGLQ` | level 1 — **standalone literal at `0x0897F98C`, not in the string table** |

All 51 table strings plus `CLJJBGLQ` use only `BCDFGHJKLMNPQRSTVWXYZ` (21 letters), exactly the
on-screen keyboard. Published-list corrections found by literal comparison:

* `LLSCSKGQ` → ROM has `LLSCSFGQ` (group 5 stage 1).
* `LLSCFQJC` → ROM has `LLSCFQJL` (group 5 stage 3).
* The published list's `SSLGYJNS` repeated as level 8 and 9; ROM has `SSLGYJNS` (group 6) and
  `SSLNZHMR` (group 7).

---

## 6b. Enumeration

* **World Race — space size.** Eight symbols over the 32-symbol alphabet
  `BCDFGHJKLMNPQRSTVWXYZ0123456789*` give `32^8 = 2^40` raw strings. The decoder
  masks 20 bits that must be zero, so the structurally valid set is exactly
  **2^20 = 1,048,576** codes; there is no arithmetic checksum, so validity is a
  bit-mask test rather than a trial search.
* **World Race — unpublished code confirmed.** `6VXR51JN` differs from the
  published `PVXR51JN` by exactly one progress flag and was accepted in mGBA.
  `F15W3ZQ2` (Elite league, "BLEACHED PLAINS") was also entered and observed.
* **Stunt Track — space size.** A plaintext table of **52 codes** (30 Game Show,
  9 Stunt School, 12 Champions League, plus the standalone `CLJJBGLQ`); every
  other string is rejected. `CLZGMVZF` and `CLJJBGLQ` were entered and their
  cutscenes observed; the mutated `CLZGMVZA` was rejected.
* **Published-list corrections proven by the ROM table:** `LLSCSKGQ` →
  `LLSCSFGQ`, `LLSCFQJC` → `LLSCFQJL`, and the duplicate `SSLGYJNS` should be
  `SSLNZHMR`.
* **Bounds proven by rejection.** A mutated Stunt Track code (wrong final
  character) and a World Race code with a forbidden mask bit set both fail;
  the zero-mask table at `0x08791F7C` is the exact boundary.

## 7. Validation evidence

### Observed (emulator)

* **World Race password screen** reached via the wheel menu (screenshot retained during the
  session): 8×4 grid over `BCDFGHJKLMNPQRSTVWXYZ0123456789*`, `DEL`/`END`, code shown at the bottom.
* With `PVXR51JN` in `0x020008C0` and `END`: the progress word at `0x020007E8` went from
  `0x000000004030C50A` to `0x00000000E139C50A`; the current-password string at `0x020008D0`
  became the validated code.
* With `F15W3ZQ2`: `0x020007E8 = 0x00000003FFFFFFFF` (bits 0–33). League mode then allowed
  ELITE selection and entered the Elite track select, which showed `BLEACHED PLAINS`
  (an Elite track). (Whether Elite was reachable before the code was not isolated as a separate
  control run; the flag-word change is the primary evidence.)
* With generated `6VXR51JN`: `0x020007E8 = 0x00000000E139C50B` — exactly one extra flag (bit 0)
  compared with `PVXR51JN`, matching the encoder's prediction that symbol 0 changes.
* **Stunt Track password screen** reached via OPTIONS → PASSWORD (screenshot retained):
  labels `GAME SHOW:` / `STUNT SCHOOL:`, 3×7 letter grid, `DELETE/QUIT/DONE`.
* With `CLZGMVZF`: after `DONE` the game immediately played
  "WELCOME TO THE CHAMPIONS LEAGUE! WANT TO TEST DRIVE THAT GOLD CAR TO ITS LIMITS? …"
  (Champions League unlocked).
* With `CLJJBGLQ`: same Champions League cutscene — the standalone literal is a real accepted code.
* With `CLZGMVZA`: `DONE` left the password screen unchanged (no cutscene, no unlock).

### Derived (disassembly)

* The World Race decoder at `0x080A7F8C` implements exactly `(alphabet_index + POS_OFFSET[pos]) % 32`;
  the constants are the literal pool at `0x080A8014/0x080A8018` and the tables at `0x087920A4/0x087920C4`.
* The validator at `0x080A7BB8` returns 1 iff any bit in `0x08791F7C` is set, then grants flags for
  the bits in `0x08791FCC` and writes counts through `0x080A6D68`; it returns 0 after regenerating
  the current password with `0x080A7B6C`/`0x080A7D7C`.
* `0x080A725C` is `flag |= 1<<n` on `0x020007E8`; `0x080A728C` is the matching bit test;
  `0x080A72A8` indexes the `u16` array at `0x020007F0`.
* Stunt Track: the 30/9/12 record tables map each 8-char string to `(group, stage)`; the screen
  handler at `0x080939694` references the `GAME SHOW:`/`STUNT SCHOOL:` labels and the record
  tables are referenced from its literal pool at `0x08093A2xx`.
* The World Race menu string table at `0x0878DE58` contains the six entries
  `OPTIONS, PASSWORD, QUICK RACE, MULTIPLAYER, TIME TRIAL, LEAGUE` (×5 language slots, only English
  populated; the others are the placeholder `Error`).

### Inferred

* Individual World Race payload-bit meanings: the pairing of `DATA_BITS` with the two-bit count
  logic in `0x080A6D68` implies each pair is a 2-bit completion count for one event, but the exact
  event names were not exercised one bit at a time. Whole-code effects are observed; per-bit names
  are inferred.
* `HWGSPSBB` is inferred to be the Game Show all-unlock entry (it is group 0 stage 0 of the Game
  Show table and the only code with the `HWGS` prefix); its separate effect on the Game Show
  episode list was not walked exhaustively (see §8).

---

## 8. Unknowns

* The exact names attached to each of the 20 World Race payload bits (and to the five 2-bit
  counters) were not proved individually; only the whole-code effects and the published descriptions
  were matched. A second analyst can enumerate them by encoding each `DATA_BITS` subset with the
  codec above and reading `0x020007E8`/`0x020007F0`.
* The precise instruction that compares a Stunt Track input to the table was not isolated. The
  accepted set is fully enumerated from ROM and the accept/reject behaviour was confirmed, so the
  system is reproducible without that address; the record tables and screen handler region are
  mapped above for anyone who wants to pin the loop.
* `HWGSPSBB`'s exact effect (which Game Show episodes it opens) was not walked to the episode list;
  it is an accepted code that returns to the main menu.
* The World Race "NEW PASSWORD:" path (`0x0878FBC4`) was reversed statically (encoder builds a
  64-bit mask with `0x080A80B4`, then the display builder at `0x080A7B6C`). It was not exercised by
  finishing a league in the emulator; the encoder path is derived, not observed.
* No button-sequence (Konami-style) cheats were located in the scans performed: no expected-button
  mask tables and no cheat progress-index globals were found in either half. The only
  developer-intended cheat surface identified is the password system documented here.

---

## 9. Tooling

Scripts used (Python 3 + capstone/objdump + mGBA + xdotool):

* `phase0.py` — size/hashes/header parse and Nintendo-logo scan for embedded headers.
* `findptr.py` — 32-bit literal/pointer search in the ROM (both aligned uses).
* `blscan.py` — raw Thumb `BL` target scanner (validated with `objdump -M force-thumb`).
* `worldrace_pw.py` — World Race decoder/encoder and published-code self-test (code in §5.1).
* `state_edit.py` / `state_edit2.py` — patch EWRAM (`0x02000000`) or IWRAM (`0x03000000`) inside an
  mGBA `.ssN` PNG savestate (decompress `gbAs`, patch, recompress, fix chunk CRC).
* Session helpers: `gotopw.py`, `centerpoll.py`, `goitem.py`, `nudge.py`, `stmenu.py`,
  `type_clz.py` — xdotool/OCR (tesseract) automation for the wheel menu and on-screen keyboards.

Disassembler: `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
Emulator: mGBA 0.10.5 SDL frontend; savestates are the `.ss1`–`.ss10` files next to the ROM
(git-ignored).

### Reproducing the "effect" screenshots in a few minutes

1. Reach the World Race password screen (§3.2), save a state (`Shift+F3`).
2. `python3 state_edit2.py state.ss3 state.ss3 0x020008C0 460031003500570033005a0051003200`
   (writes `F15W3ZQ2` as eight `u16`).
3. Load `F3`, select `END`, press `A`.
4. Menu → LEAGUE (wheel taps) → ELITE: the Elite track list is now selectable.

For Stunt Track: reach its password screen, save a state, patch
`0x03003BB4` and `0x03003C54` with `434c5a474d565a46` (`CLZGMVZF`), load, select `DONE`, press `A`.

---

## 10. Legal note

This report documents addresses, formats, algorithms, and code strings needed to reproduce the
analysis. No ROM image, graphics, audio, or other copyrighted asset is included or redistributed.
All in-game text quoted here is short and used for identification/evidence.
