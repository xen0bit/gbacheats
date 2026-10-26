# 2-in-1: Hot Wheels — Velocity X & Hot Wheels — World Race (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `2-in-1 - Hot Wheels - Velocity X & Hot Wheels - World Race.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| MD5 | `9e95f7804e3b8011b89048f68e541db8` |
| SHA-1 | `80fccdb4f09640f4eef3f793a016664ce3c5b9ec` |
| SHA-256 | `df640e574ee25d92833a177a990caf05b9d954720b312d58c6fba788ebbba228` |
| Pack header (file `0x0`) | title `HWVX HWWR`, code `BHZE`, maker `78`, version 0, entry `0xEA1CFFFE` → `0x08740000` |
| Boot-selector header (file `0x740000`) | title `MULTIGAME`, code `XXXX`, maker `78`, entry `0xEA00002E` → `0x087400C0` |
| Velocity X header (file `0x800000`) | title `VELOCITYX`, code `AH8P`, maker `78`, version 0, entry `0xEA00002E` → `0x088000C0` |

### Cartridge layout (three GBA headers, found by scanning for the 156-byte Nintendo logo at `+4`)

| File range | Image | Base (ROM address) | Notes |
|---|---|---|---|
| `0x000000`–`0x73FFFF` | **Hot Wheels World Race** | `0x08000000` | standalone World Race image; header at `0x0` replaced by the pack builder |
| `0x740000`–`0x7FFFFF` | 2-in-1 boot selector | `0x08740000` | `MULTIGAME` stub, 768 KiB |
| `0x800000`–`0xFFFFFF` | **Hot Wheels Velocity X** | `0x08800000` | 8 MiB, complete image |

All in-image pointers are `0x08000000 + file_offset` (confirmed: the VX string `PASSWORD` at file `0xD66418` is referenced
by the literal `0x08D66418` at file `0xD6441C`). For the World Race half this is also `0x08000000 + offset`; for the
Velocity X half it means the code runs at `0x088xxxxx`–`0x08Dxxxxx`.

### Sub-image identity / build comparison

| Region | SHA-256 |
|---|---|
| World Race half, full `0x0..0x73FFFF` | `97847f8412225ddf1593aff6751f42cc5f2471125bdded509f579a58e8606e32` |
| World Race half, body `0x200..0x740000` | `a0f53d04094efb3c73c8cc50a66648c43b0282a2b825a027b65534c2d682022a` |
| Standalone `Hot Wheels World Race.gba`, `0x200..0x740000` | `a0f53d04094efb3c73c8cc50a66648c43b0282a2b825a027b65534c2d682022a` |
| Velocity X half, full `0x800000..0xFFFFFF` | `5ade8318d7f27af043c04f1731447a44e501e1cf2fc616919b289044cf6fc115` |
| Velocity X half, body `0x800200..0x1000000` | `17e197a2b7ea025951518347ccea7fb7cae93e459acdfea91eca0a67ec076cce` |
| Boot selector `0x740000..0x7FFFFF` | `a8d12effab78e9b258af47dba521300608a28ff5c726dc2bd98ac53aa7a3b2d1` |
| Stunt Track pack's World Race body (`0x80200..0xF40000`) | `714b084b4c46076d016e6e72e28a65ad551ce0c49f54a7a756c93ad60e15b21b` |

**World Race build answer: this cart's World Race half is byte-identical to the standalone US
`Hot Wheels World Race.gba` from `0x200` to `0x740000` (the standalone file is zero-padded above `0x740000`;
this pack truncates the image there). It is *not* the same build as the World Race half inside the
Stunt Track 2-in-1 pack** — the two bodies differ in 5,281,997 bytes over that overlap. The password
*algorithm* is nevertheless the same: the alphabet, per-position offsets and both bit tables at this
build's relocated addresses have exactly the values recorded in the Stunt Track report, and entering a
published code here produces the same progress-word change (see §6b and §7).

**Velocity X build:** the half is 8 MiB and runs from `0x08800000`. It is **not** byte-identical to the
standalone `Hot Wheels: Velocity X.gba` (1,090,833 differing bytes; equal bytes after `0x1000`:
7,293,999 / 8,384,512). Treat it as its own revision; every address below is for this file.

**Scope:** developer-intended in-game cheats only — the password systems and the developer sound-test
entries. No GameShark/CodeBreaker/memory codes. No ROM or game assets are redistributed.

---

## 2. Executive summary

Both halves contain a developer password system. **No prior reversal of Velocity X's code format was
available; it is fully reversed here.**

**Velocity X (second half, file `0x800000`).** The main menu item `PASSWORD` opens an 8-digit numeric keypad
(symbols `1`–`9` only; there is no `0`). The eight digits are read as a base-9 number
(`value = Σ (digit[i]-1)·9^(7-i)`). The 25-bit result is then passed through a fixed 40-round permutation
built from a 200-byte table at `0x0887B5D8` (rotate-left, bit-swap, bit-toggle, add, five table bytes per
round). The decoded 25-bit word is validated by

* bits 21–24 = `popcount(bits 0–20) & 0xF` (a 4-bit checksum),
* bits 15–20 = level field, must be ≤ 37 (`cmp r0,#0x25`, `0x088402D6`),
* bits 4, 7, 10 and 13 must be zero (four reserved bits),

and on success the level field is written to `0x03005AC0` and the 15 low bits to the byte array
`0x03005A90`. The space is exactly **9^8 = 43,046,721** strings; exhaustive enumeration shows
**99,058 are accepted**, mapping onto **77,824 distinct (level, flags) states** (38 levels × 2^11 flag
combinations). The encoder is the exact inverse: it reproduces the game's own blank-profile password
`123-17-543` and both published “unlock” codes bit-for-bit.

37 published level passwords were decoded. 34 match exactly (level field = published level − 1); **three are
single-digit typos in the published lists** and are rejected by the ROM. The corrected codes were generated,
entered, and accepted; the published forms were entered and rejected. Five codes that appear in no published
list were minted and accepted: `373-62-937` (level 15), `478-66-254` (level 18), `447-58-369` (level 26),
`784-87-571` (level 1 with progress flags `0x121`) and `365-62-218` (level 1 with all flags `0x5B6F`).
Bounds were proven in-game with four rejections:
wrong checksum (`373-62-927`), reserved bit set (`478-68-254`), wrong checksum (`477-58-369`), and
out-of-range level field 38 (`163-51-739`).

**World Race (first half, file `0x0`).** The prior Stunt Track-pack reversal is reused and re-confirmed:
8 symbols over the 32-symbol alphabet `BCDFGHJKLMNPQRSTVWXYZ0123456789*`, per-position additive rotation,
20 forbidden bits and 20 payload bits, no arithmetic checksum, 2^20 valid codes. In this cart the tables
are at `0x08714310`/`0x08714360`, offsets `0x08714438`, alphabet `0x08714458`, validator `0x08028324`.
`PVXR51JN` was typed on this cart's password screen and accepted; the progress word at `0x020007E8`
changed `0x000000004030C50A` → `0x00000000E139C50A`, exactly the change the Stunt Track report recorded
for the same code.

**Other developer content.** Velocity X's `OPTIONS` screen exposes `SOUND TEST` and `MUSIC TEST` (numeric
sound-bank selectors, 0-based, adjustable in place) next to `SOUND`, `MUSIC` and `CONTROL`; this is the only
developer/debug surface besides the passwords. A developer text Easter egg, `I LIKE MONKEYS …`, sits at file
`0x8885A0` in the Velocity X half (ROM `0x088885A0`), matching the GameFAQs note about an offset near
`0x885D0`. No button-sequence (Konami-style) cheat tables were found in either half.

---

## 3. How to reproduce

### 3.1 Emulator / display

```bash
Xvfb :110 -screen 0 1024x768x24 &
DISPLAY=:110 openbox &
cd "roms/2-in-1 - Hot Wheels - Velocity X & Hot Wheels - World Race"
DISPLAY=:110 SDL_AUDIODRIVER=dummy mgba -3 \
  "2-in-1 - Hot Wheels - Velocity X & Hot Wheels - World Race.gba" &
W=$(DISPLAY=:110 xdotool search --name mGBA | head -1)
DISPLAY=:110 xdotool windowfocus "$W"
```

mGBA SDL default keymap used throughout: **A = `x`**, **B = `z`**, **L = `a`**, **R = `s`**,
**Start = `Return`**, **Select = `BackSpace`**, d-pad = arrow keys. Hold keys 0.1–0.5 s.
Screenshots: `DISPLAY=:110 import -window root s.png`; viewport is 720×480 at +152+144 (3× scale).
Savestates: `Shift+F1..F9` save, `F1..F9` load (written next to the ROM as `.ssN`).

**Profile/save menus:** neither half has a profile or save-slot selector. Both create a single auto-save
(`.sav`) on boot; every menu entry in both halves was walked (title, main, options/extras, password,
gameplay and pause) except the non-gameplay `CREDITS` roll in World Race's options, which is a plain
credits display.

The pack boots to a **carousel selector** (~12 s): the Velocity X cover is centred and the caption reads
`HOT WHEELS VELOCITY X`; Left/Right changes selection (`HOT WHEELS WORLD RACE`) and A boots the chosen game.

### 3.2 Velocity X — reach and use the password screen

1. Shell: leave `HOT WHEELS VELOCITY X` centred, press A.
2. A through the combined licence text and the Saffire logo to the title (`PRESS START`), then Start.
3. Main menu is a vertical list: `STORY MODE, RACE MODE, CHALLENGE, PASSWORD, DATABASE, OPTIONS`.
   Move down to `PASSWORD` and press A.
4. The screen is a numeric keypad 1–9 (3×3), the entered code at the top in the form `NNN-NN-NNN`,
   and the current/last accepted password pre-filled. The first digit press clears the pre-filled code.
   Digits are appended left to right; after the eighth digit the cursor jumps to the implicit submit
   (pressing A then validates). A rejected code clears the entry and stays on the screen; an accepted
   code returns to the main menu.
5. The blank-profile code is `123-17-543`; after accepting a code, the password screen re-displays it
   (the encoder regenerates the current password from the applied flags/level).

Fast iteration: a savestate on the password screen contains the eight digit values as **u32** at
`0x03005AA0` (IWRAM block of the mGBA PNG state at `0x19000+0x5AA0`); patch and reload instead of
typing. The validators write their result to `0x03005A90` (15 flag bytes) and `0x03005AC0` (level field).

### 3.3 World Race — reach and use the password screen

1. Shell: Left (caption `HOT WHEELS WORLD RACE`), A; A through licence/Climax logos to the title, Start.
2. The main menu is a rotating wheel. With `QUICK RACE` centred, a very short Up tap (≈20 ms) centres
   `PASSWORD`; A opens it. (Longer taps coast past it to `OPTIONS`.)
3. The screen is the 8×4 grid
   `B C D F G H J K / L M N P Q R S T / V W X Y Z 0 1 2 / 3 4 5 6 7 8 9 *` with `DEL` and `END`.
   Enter 8 symbols; after the eighth the cursor moves to `END`; A submits.
4. Entered code buffer is 8×u16 at `0x020008C0` (ASCII code units); the validated string is copied to
   `0x020008D0`; the progress/flag word is the 64-bit value at `0x020007E8`.

### 3.4 Codes entered in mGBA (all observed)

| Game | Code | Kind | Result |
|---|---|---|---|
| VX | `143-24-813` | published level 2 | accepted → main menu |
| VX | `777-77-777` | arbitrary | rejected (stays on password screen) |
| VX | `373-62-927` | published level 15 | **rejected** (bad checksum) |
| VX | `373-62-937` | **generated, unpublished** | accepted → main menu |
| VX | `478-68-254` | published level 18 | **rejected** (reserved bits 4,10) |
| VX | `478-66-254` | **generated, unpublished** | accepted → main menu |
| VX | `477-58-369` | published level 26 | **rejected** (bad checksum) |
| VX | `447-58-369` | **generated, unpublished** | accepted → main menu |
| VX | `784-87-571` | **generated, unpublished** | accepted → main menu (level 1 + flags `0x121`) |
| VX | `365-62-218` | generated (level 1, all flags) | accepted → main menu |
| VX | `163-51-739` | generated, level field 38 | **rejected** (level > 37) |
| WR | `PVXR51JN` | published | accepted → main menu; progress `0x4030C50A` → `0xE139C50A` |

After accepting `373-62-937`, a savestate read shows `0x03005AC0 = 14` and
`0x03005A90[0] = 1`, i.e. level field 14 (published level 15) with flag bit 0 — the validator's own
output. Entering `STORY MODE` afterwards lists six missions instead of the two listed with the level-2
code, the visible in-game effect.

---

## 4. Address map

All addresses are ROM addresses; file offset = address − `0x08000000` (for the World Race half this is also
the in-image offset; for Velocity X the image starts at file `0x800000` / ROM `0x08800000`).

### 4.1 Velocity X

| Address | Size | Meaning |
|---|---|---|
| `0x088401D8` | Thumb | `validate_password()`: base-9 decode + 40-round unscramble + checksum/level/reserved checks; writes `0x03005A90` and `0x03005AC0`, returns 0 = accept, 1 = reject |
| `0x088400B8` | Thumb | `swap_bits(v, p, q)` — exchange two bits of the 25-bit word |
| `0x08840114` | Thumb | `toggle_bit(v, p)` — `v ^= 1<<p` |
| `0x08840138` | Thumb | `add_masked(v, n)` — `(v + n) & 0x1FFFFFF` |
| `0x08840160` | Thumb | `sub_masked(v, n)` — `(v - n) & 0x1FFFFFF` (inverse helper) |
| `0x08840188` | Thumb | `rebuild_checksum(v)` = `(v & 0x1FFFFF) | ((popcount(v & 0x1FFFFF) & 0xF) << 21)` |
| `0x088401D8`+`0x…2A0` | — | 40-round loop: `c=200; while c>0 { rotl25(T[c-1]); swap(T[c-2],T[c-3]); xor T[c-4]; add T[c-5]; c-=5 }` |
| `0x08840384` | Thumb | `build_current_password()` — encoder: flags from `0x03005A90`, level from `0x03005AC0`, checksum, inverse scramble, digit conversion |
| `0x08828778` | Thumb | password-screen update: when input count reaches 8, `bl 0x088401D8`; on reject plays SFX 0x14 and clears the entry |
| `0x0882852E` | Thumb | `bl 0x08840384` — draws the current password when the screen opens |
| `0x0887B5D8` | 200 B | scramble table `T[0..199]` (values 0–24) |
| `0x0887B6A0` | 4 B | loop constant `200` |
| `0x0887B6A4` | 4 B | pointer `0x03005AA0` (digit buffer) |
| `0x03005A90` | 15 B | decoded flag bits 0–14 as byte 0/1 |
| `0x03005AA0` | 8×u32 | entered digits (values 1–9) |
| `0x03005AC0` | u32 | accepted level field (0–37) |
| `0x03005AC4` | u8 | accept/progress latch used by the screen handler |
| `0x08D66418` | — | `PASSWORD` menu string in the VX string bank (`0x08D6xxxx`) |
| `0x088885A0` | — | developer text Easter egg `I LIKE MONKEYS …` |

### 4.2 World Race (this cart's build)

| Address | Size | Meaning |
|---|---|---|
| `0x08028324` | Thumb | `validate_and_apply(input, len)` |
| `0x0802833A` | — | loop over the 20 forbidden bits; any set → return 1 |
| `0x080283B2` | — | loop over the 20 payload bits (10 pairs) granting/testing flags |
| `0x08028462` | — | second payload-pair loop (two-bit counters via `set_progress`) |
| `0x080280FC` | Thumb | `char_value(char, pos)` — alphabet index + per-position rotation |
| `0x0802853C` | Thumb | helper used by `char_value` |
| `0x08714310` | 20×u32 | forbidden bits `0,1,2,5,9,10,11,12,14,15,16,18,19,20,25,30,33,34,36,39` |
| `0x08714360` | 20×u32 | payload bits `26,4,23,21,13,38,7,28,22,3,6,35,17,32,8,31,27,29,24,37` |
| `0x08714438` | 8×u32 | per-position offsets `21,24,14,19,6,10,26,22` |
| `0x08714458` | 33 B | alphabet `BCDFGHJKLMNPQRSTVWXYZ0123456789*` + NUL |
| `0x020008C0` | 8×u16 | input symbols |
| `0x020008D0` | 9 B | validated ASCII code |
| `0x020007E8` | 8 B | 64-bit progress/flag word |
| `0x020007F0` | — | `u16` per-event count array |

*The Stunt Track report's addresses (`0x080A7BB8`, `0x087920C4`, …) belong to the other build; the table
*values are identical but relocated here.*

---

## 5. Algorithm

### 5.1 Velocity X codec (exact; reimplemented in `vx_pw.py`)

```python
T = rom[0x887B5D8:0x887B5D8+200]          # 200 bytes, values 0..24
M25 = (1<<25)-1

def rotl25(v,b):  return ((v<<b)|(v>>(25-b))) & M25   # b != 0
def swap_bits(v,p,q):
    bp,bq = (v>>p)&1, (v>>q)&1
    return (v & ~((1<<p)|(1<<q))) | (bp<<q) | (bq<<p)

def scramble(v):                          # ROM 0x088401D8 loop
    v &= M25
    c = 200
    while c > 0:
        c -= 1
        v = rotl25(v, T[c])
        v = swap_bits(v, T[c-1], T[c-2])
        v ^= 1 << T[c-3]
        v = (v + T[c-4]) & M25
        c -= 4
    return v

def unscramble(v):                        # inverse (encoder)
    v &= M25
    for c_before in range(5, 205, 5):     # undo rounds in reverse order
        c = c_before - 1
        v = (v - T[c-4]) & M25
        v ^= 1 << T[c-3]
        v = swap_bits(v, T[c-1], T[c-2])
        v = rotl25(v, (-T[c]) % 25)
    return v

def digits_to_raw(code):                  # 8 chars '1'..'9'
    v = 0
    for ch in code: v = v*9 + (int(ch)-1)
    return v

def raw_to_digits(raw):
    return "".join(str((raw // 9**k) % 9 + 1) for k in range(7,-1,-1))

def decode(code):
    v = scramble(digits_to_raw(code))
    low  = v & 0x1FFFFF
    chk  = ((bin(low).count("1") & 0xF) << 21) | low
    level  = (v >> 15) & 0x3F
    flags  = v & 0x7FFF
    ok = (v == chk) and level <= 0x25 and not (flags & ((1<<4)|(1<<7)|(1<<10)|(1<<13)))
    return ok, level, flags

def encode(level, flags):                 # inverse; level 0..37, flags subset of 15 bits
    v = (flags & 0x7FFF) | (level << 15)
    low = v & 0x1FFFFF
    v = ((bin(low).count("1") & 0xF) << 21) | low
    return raw_to_digits(unscramble(v))
```

Validator flow (`0x088401D8`):

```
raw = Σ (digit[i]-1)*9^(7-i)              # digit buffer 0x03005AA0, i=0 is the leftmost digit
v   = scramble(raw)                       # 40 rounds, table 0x0887B5D8
if v != ((popcount(v & 0x1FFFFF)&0xF)<<21 | (v & 0x1FFFFF)): return 1     # 0x088402C4
if ((v >> 15) & 0x3F) > 0x25: return 1                                    # 0x088402D6
for i in 0..14: byte[0x03005A90+i] = (v >> i) & 1
if byte[+4] or byte[+7] or byte[+10] or byte[+13]: return 1               # 0x08840334
dword[0x03005AC0] = (v >> 15) & 0x3F
return 0
```

The screen handler (`0x08828778`) calls the validator when the eighth digit has been entered; return 1
clears the entry (audible error cue, no state change), return 0 applies the flags/level and leaves the
screen. The encoder (`0x08840384`) is used when the screen opens and after an accept to display the
current password.

### 5.2 World Race codec (reused; re-confirmed)

```python
ALPHABET   = "BCDFGHJKLMNPQRSTVWXYZ0123456789*"
POS_OFFSET = [21,24,14,19,6,10,26,22]
ZERO_BITS  = [0,1,2,5,9,10,11,12,14,15,16,18,19,20,25,30,33,34,36,39]
DATA_BITS  = [26,4,23,21,13,38,7,28,22,3,6,35,17,32,8,31,27,29,24,37]

def decode_wr(code):
    s = [(ALPHABET.index(c) + POS_OFFSET[i]) % 32 for i,c in enumerate(code)]
    v = sum(x << (5*i) for i,x in enumerate(s))       # 40-bit value
    if any((v >> b) & 1 for b in ZERO_BITS): return None
    return {b for b in DATA_BITS if (v >> b) & 1}     # progress payload
```

No arithmetic checksum: every 40-bit value with all `ZERO_BITS` clear is accepted, hence 2^20 valid
codes. This build implements the same tables at `0x08714310`/`0x08714360` (values identical to the
Stunt Track report) and the same validator structure at `0x08028324`.

---

## 6. Tables

### 6.1 Velocity X — published level passwords, decoded

`L` = published level; `field` = the 6-bit level field in the decoded word; `flags` = the 15-bit flag
set. All rows except the three flagged ones satisfy checksum, level ≤ 37 and reserved bits 0.

| L | Published code | field | flags | Status |
|---:|---|---:|---|---|
| 02 | `143-24-813` | 1 | `0x0000` | verified |
| 03 | `141-38-985` | 2 | `0x0000` | verified |
| 04 | `249-48-723` | 3 | `0x0000` | verified |
| 05 | `294-16-277` | 4 | `0x0000` | verified |
| 06 | `457-51-438` | 5 | `0x0001` | verified |
| 07 | `112-86-545` | 6 | `0x0001` | verified |
| 08 | `447-65-112` | 7 | `0x0001` | verified |
| 09 | `368-54-466` | 8 | `0x0001` | verified |
| 10 | `718-59-438` | 9 | `0x0001` | verified |
| 11 | `363-95-545` | 10 | `0x0001` | verified |
| 12 | `373-65-848` | 11 | `0x0001` | verified |
| 13 | `171-49-211` | 12 | `0x0001` | verified |
| 14 | `373-59-216` | 13 | `0x0001` | verified |
| 15 | `373-62-927` | 26 | `0x1B61` | **rejected** (bad checksum) → correct code `373-62-937` |
| 16 | `718-42-276` | 15 | `0x0001` | verified |
| 17 | `358-59-355` | 16 | `0x0001` | verified |
| 18 | `478-68-254` | 19 | `0x041C` | **rejected** (reserved bits 4,10) → correct code `478-66-254` |
| 19 | `573-77-683` | 18 | `0x0001` | verified |
| 20 | `188-58-352` | 19 | `0x0001` | verified |
| 21 | `766-46-341` | 20 | `0x0001` | verified |
| 22 | `187-98-394` | 21 | `0x0001` | verified |
| 23 | `188-12-234` | 22 | `0x0001` | verified |
| 24 | `786-84-747` | 23 | `0x0001` | verified |
| 25 | `466-59-979` | 24 | `0x0001` | verified |
| 26 | `477-58-369` | 31 | `0x3AB4` | **rejected** (bad checksum) → correct code `447-58-369` |
| 27 | `447-62-191` | 26 | `0x0001` | verified |
| 28 | `614-81-432` | 27 | `0x0001` | verified |
| 29 | `641-18-239` | 28 | `0x0001` | verified |
| 30 | `399-68-584` | 29 | `0x0121` | verified |
| 31 | `662-84-635` | 30 | `0x0121` | verified |
| 32 | `476-63-843` | 31 | `0x0121` | verified |
| 33 | `616-67-341` | 32 | `0x0121` | verified |
| 34 | `384-97-475` | 33 | `0x0121` | verified |
| 35 | `363-13-298` | 34 | `0x0121` | verified |
| 36 | `521-71-135` | 35 | `0x0121` | verified |
| 37 | `543-17-658` | 36 | `0x0121` | verified |
| 38 | `782-57-387` | 37 | `0x0121` | verified |

Special published codes:

| Code | Decoded as | Meaning |
|---|---|---|
| `496-93-993` (“unlock all cars”) | field 37, flags `0x5B6F` | `encode(37, 0x5B6F)` reproduces it exactly |
| `723-83-462` (“unlock everything”) | field 37, flags `0x5B6D` | `encode(37, 0x5B6D)` reproduces it exactly |
| `123-17-543` (blank profile, shown on entry) | field 0, flags `0x0000` | `encode(0, 0)` reproduces it exactly |

### 6.2 Velocity X — field layout

| Field | Bits | Rule |
|---|---|---|
| progress flags | 0–14 | bits 4, 7, 10, 13 must be 0; the other 11 bits are free |
| level | 15–20 | 0..37 (`> 0x25` rejected); published level = field + 1 |
| checksum | 21–24 | `popcount(bits 0–20) & 0xF` |

Observed flag conventions (inferred meanings): `0x0000` = prologue state (levels 2–5), `0x0001`
(bit 0) = first chapter cleared (levels 6–29), `0x0121` (bits 0,5,8) = later chapters cleared (levels
30–38), `0x5B6F` = every flag (all-cars code), `0x5B6D` = every flag but bit 1 (all-items code). The
validator applies the bits to `0x03005A90`; only whole-code effects were observed, so individual bit
names remain inferred.

### 6.3 World Race — code used in this cart

| Code | Symbols (0–31) | Payload bits | Observed effect |
|---|---|---|---|
| `PVXR51JN` | `00 08 00 00 00 00 00 00` | `{8}` | accepted; `0x020007E8` `0x4030C50A` → `0xE139C50A` |
| `F15W3ZQ2`* | `24 14 08 04 30 30 06 13` | all 20 payload bits | (from prior report: all flags, Elite league) |
| `6VXR51JN`* | `16 08 00 00 00 00 00 00` | `{4,8}` | (from prior report: one extra flag vs `PVXR51JN`) |

\* Not re-entered here; decoded with this cart's tables to confirm the table values match.

---

## 6b. Enumeration

### Velocity X

* **Input space.** Eight positions, each `1`–`9` (no `0` key): **9^8 = 43,046,721** strings.
* **Validator model.** Base-9 decode → 40-round table scramble → 25-bit word; accepted iff
  4-bit popcount checksum matches, level field ≤ 37, and bits 4/7/10/13 are clear.
* **Accepted set (exhaustive).** A C program over all 43,046,721 strings (40 scramble rounds each)
  counted **99,058 accepted strings** and **77,824 distinct decoded (level, flags) states** — exactly
  `38 × 2^11`. 77,824 states have one canonical encoder output; 21,234 of those states are also
  reachable by a second digit string (the 9^8 input space is larger than the 2^25 internal word), so the
  total accepted string count is 99,058.
* **Novel codes (in no published list), all accepted in mGBA:**
  * `373-62-937` — level 15, flags `0x0001`. Accepted → main menu; `STORY MODE` then lists six
    missions (level-2 code lists two); RAM `0x03005AC0 = 14`, `0x03005A90[0] = 1`.
  * `478-66-254` — level 18, flags `0x0001`. Accepted → main menu.
  * `447-58-369` — level 26, flags `0x0001`. Accepted → main menu.
  * `784-87-571` — level 1, flags `0x0121` (arbitrary flag minting, not a level correction). Accepted
    → main menu; `STORY MODE` starts the mission-1 intro because the level field is 0.
  * `365-62-218` — level 1 with all flags `0x5B6F`. Accepted → main menu.
* **Published-list corrections proven in-game.** The published level-15, -18 and -26 codes are
  single-digit typos; each published form was entered and **rejected**, and each corrected form was
  entered and **accepted**:

  | Level | Published (rejected) | Corrected (accepted) |
  |---:|---|---|
  | 15 | `373-62-927` | `373-62-937` |
  | 18 | `478-68-254` | `478-66-254` |
  | 26 | `477-58-369` | `447-58-369` |

* **Bounds proven by rejection (in mGBA).**
  * Wrong checksum: `373-62-927`, `477-58-369` — entry cleared, screen unchanged.
  * Reserved bit set: `478-68-254` (decodes to field 19, flags `0x041C`, checksum valid but bits 4 and
    10 set) — rejected.
  * Level field out of range: `163-51-739` decodes to field 38 with a correct checksum
    (`0x25` is the maximum) — rejected in mGBA, matching `cmp r0,#0x25` at `0x088402D6`.
  * Arbitrary string `777-77-777` — rejected.
* **Encoder exactness.** `encode(37,0x5B6F) = 49693993`, `encode(37,0x5B6D) = 72383462`,
  `encode(0,0) = 12317543`; all 34 valid published codes round-trip byte-for-byte through
  `encode(decode(code))`.

### World Race

* **Input space.** 8 symbols from the 32-symbol alphabet = 32^8 = 2^40 strings; the validator rejects
  any value with a forbidden bit set, leaving exactly **2^20 = 1,048,576** structurally valid codes
  (no arithmetic checksum). This is the figure from the Stunt Track report; this cart's tables are
  value-identical, so it applies unchanged.
* **Build check.** Body `0x200..0x740000` is byte-identical to the standalone World Race ROM and differs
  from the Stunt Track pack's World Race body in 5,281,997 bytes. The password tables/algorithm are the
  same; the published-code result is identical in both builds.
* **In-game proof in this cart.** `PVXR51JN` was entered on this cart's password screen and accepted;
  the progress word at `0x020007E8` changed from `0x000000004030C50A` to `0x00000000E139C50A` — the
  exact transition recorded for the same code in the Stunt Track pack.

---

## 7. Validation evidence

### Observed (emulator)

* **Boot selector** (`shell_selector_vx.png`, `shell_selector_wr.png`): carousel with both covers; captions
  `HOT WHEELS VELOCITY X` / `HOT WHEELS WORLD RACE`; A boots the choice.
* **Velocity X menus:** title (`vx_title.png`), main menu (`vx_main.png`), story intro and mission select
  (`vx_baseline_story2.png`, `vx_fixed15_story.png`, `vx_allflags_story.png`), car select
  (`vx_after_start2.png`), race mode (`vx_baseline_story.png` — RACERS/LAPS/LEVEL/DIFFICULTY), challenge
  (`vx_challenge3.png` — Level 1, Battle/Tag), database browser (`vx_database.png`, `1 of 30`), options
  (`vx_options.png`, `vx_control_b.png`: SOUND TEST, MUSIC TEST, SOUND, MUSIC, CONTROL/Beginner), pause
  (`vx_pause2.png`: GAME PAUSED, Start=return, Select=quit, objective), password screen and current-code
  display (`vx_password.png`, `vx_pw_after143c.png`), sound test adjusted 0→1 (`vx_sound_test2.png`),
  music test adjusted 0→1 (`vx_music_test_b.png`).
* **Velocity X codes:** `143-24-813` accepted; `373-62-937`, `478-66-254`, `447-58-369`, `784-87-571`,
  `365-62-218` accepted; `777-77-777`, `373-62-927`, `478-68-254`, `477-58-369`, `163-51-739` rejected
  (screens: `vx_typed_143b.png`, `vx_after_143b.png`, `vx_fixed15_typed.png`, `vx_fixed15_after.png`,
  `vx_lvl18_fixed_accept.png`, `vx_lvl26_fixed_accept.png`, `vx_novel_flags_accept.png`,
  `vx_typo_after.png`, `vx_lvl18_typo_reject.png`, `vx_lvl26_typo_reject.png`,
  `vx_field38_reject.png`, `vx_all7_afterA.png`).
* **Velocity X RAM** (savestate reads): digit buffer `0x03005AA0` holds the eight u32 digits
  (`00000001 00000004 00000003 …` for `143-24-813`); after accepting
  `373-62-937`, `0x03005AC0 = 0x0E` and `0x03005A90[0] = 1`; the blank state has
  `0x03005AC0 = 0`, `0x03005A90 = 0`, and the screen shows `123-17-543`.
* **World Race menus:** title (`wr_title4.png`), main wheel (`wr_main5.png`), options
  (`wr_options.png`: MUSIC VOLUME, SFX VOLUME, CREDITS), password screen (`wr_pw_screen.png`), race line-up
  and in-race (`wr_race3.png`), pause (`wr_pause2.png`: RESUME/RETRY/QUIT).
* **World Race code:** `PVXR51JN` typed on-screen (`wr_typed_pvxr51jn.png`), `END` pressed, accepted
  (`wr_after_end.png`); savestate before/after: `0x020007E8` `0x4030C50A` → `0xE139C50A`; input buffer
  `0x020008C0` = `50 00 56 00 58 00 52 00 35 00 31 00 4a 00 4e 00` (`P V X R 5 1 J N`).

### Derived (disassembly)

* Velocity X checksum function at `0x08840188` is `(v & 0x1FFFFF) | ((popcount(v & 0x1FFFFF) & 0xF) << 21)`;
  the validator compares this to the word at `0x088402C4`.
* The 40-round loop at `0x0884022A`–`0x088402BA` uses the five table bytes per round exactly as
  pseudocoded in §5.1; the table is the 200 bytes at `0x0887B5D8` (all values ≤ 24), counter 200 at
  `0x0887B6A0`.
* The level bound is the `cmp r0,#0x25; bls` at `0x088402D6`; the reserved-bit test is the four byte
  checks at `0x08840334`–`0x08840354`.
* The screen-handler call at `0x08828778` is guarded by input count == 8; reject path plays SFX 0x14 and
  clears the entry; accept path sets the latch at `0x03005AC4`.
* World Race validator at `0x08028324` iterates the 20-entry forbidden table at `0x08714310`
  (`return 1` on any set bit) then the payload pairs at `0x08714360`; the char decoder at `0x080280FC`
  uses offsets `0x08714438` and alphabet `0x08714458`. These table values equal the Stunt Track report's.
* The developer message at file `0x8885A0` is plaintext inside the Velocity X image (`I LIKE MONKEYS`,
  followed by the “200 monkeys” story); it is data, not a cheat.

### Inferred

* Individual meanings of Velocity X flag bits: the observed patterns per published level and the two
  “unlock” codes imply bit 0 = first chapter, bits 5/8 = later chapters, and the rest = optional
  cars/stunts/challenges, but per-bit effects were not exercised one at a time. Only whole-code effects
  are observed.
* The 40-round scramble is presumably a deliberate obfuscation of a plain base-9 progress number; no
  game logic depends on the individual round structure, only on the composition.
* World Race per-bit flag names remain those of the prior report.

---

## 8. Unknowns

* The exact per-bit meanings of the Velocity X 15 flag bits and of the World Race 20 payload bits were
  not proven individually; the whole-code effects and the published level progression were matched.
* The four reserved Velocity X bits (4,7,10,13) are never set by any published or generated valid code;
  their original purpose (possibly a two-bit counter in another mode) is unknown.
* The Velocity X alias codes (21,234 states reachable by two different digit strings) were counted
  exhaustively but not individually listed; an alias has the same decoded state as its canonical code.
* The pack boot selector's exact mechanism for switching the active image was not reversed; only its
  user-visible behaviour (carousel + A) was exercised.
* World Race's generated “NEW PASSWORD:” path was not exercised by finishing a league in this cart;
  the codec is confirmed by the accepted code and the progress word.

---

## 9. Tooling

Python 3 + capstone + mGBA 0.10.5 (SDL) + Xvfb/xdotool/scrot/ImageMagick, plus `arm-none-eabi-objdump`
for cross-checks.

* `phase0.py` — size/hashes/header parse and Nintendo-logo scan (found 3 headers at `0x0`, `0x740000`,
  `0x800000`).
* `compare.py` — sub-image hashing and block comparison against the standalone ROMs and the Stunt Track
  pack.
* `thumbdis.py` — capstone Thumb disassembler for arbitrary ROM ranges.
* `vx_pw.py` — Velocity X decoder/encoder, field model and self-test against all published codes.
* `count.c` — exhaustive 9^8 enumeration of the Velocity X validator (99,058 accepted / 77,824 states).
* `state.py` / `state_patch.py` — read and patch IWRAM/EWRAM inside mGBA PNG savestates.
* `ctl.py`, `k.py`, `typepw.py`, `typewr.py` — xdotool input and on-screen keypad typing helpers.

Screenshots referenced by name in §7 were captured to `/tmp/opencode/hwvx/shots/` during the session
(session artifacts, not required for reproduction).

Reproduce the key Velocity X result:

```bash
python3 - <<'EOF'
from vx_pw import decode, encode
print(decode("37362937"))      # ok, level field 14, flags 1
print(encode(14, 1))           # '37362937'
print(encode(37, 0x5B6F))      # '49693993'  (published "all cars")
print(encode(0, 0))            # '12317543'  (game's blank-profile code)
EOF
```

Then reach VX `PASSWORD`, type `373-62-937`, press A: accepted. Type `373-62-927`, press A: rejected.

---

## 10. Legal note

This report documents addresses, formats, algorithms and short code strings needed to reproduce the
analysis. No ROM image, graphics, audio, or other copyrighted asset is included or redistributed. The
quoted developer text is a short excerpt used only as evidence of the Easter egg.
