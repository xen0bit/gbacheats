# 2 Games in 1 — Power Rangers: Ninja Storm & Time Force (GBA) — RE Report

Report generated from a local ROM analysis on 2026-10-24; Time Force password
packing completed and verified on 2026-10-26.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

Scope note: **in-game / developer-intended cheats only.**
GameShark/CodeBreaker/RAM-patch codes are out of scope.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/2 Games in 1 - Power Rangers - Ninja Storm & Power Rangers - Time Force/2 Games in 1 - Power Rangers - Ninja Storm & Power Rangers - Time Force.gba` |
| Size | 16 MiB (`0x1000000`) |
| Header title | `PRNINJA&TF` |
| Game code | `BRZE` |
| Maker code | `78` |
| Software version | `0` |
| MD5 | `beaa0de66f48e52efcc97b50b7777dec` |
| SHA-1 | `e8d8fd1cdb48ec4b0f83c38a95109ef1ccfe715d` |
| SHA-256 | `3ff116124d13abb55966241e0becd12efc2cf03cf7241054019beae9278dcaf5` |

ROM addresses below are `0x08000000 + file_offset`. All findings are tied to
this exact hash; another revision may differ.

### Cart layout (derived)

| Range | Contents |
|---|---|
| `0x08000000`–`0x083FF43F` | Ninja Storm image (4 MiB); entry `0x080004E0` |
| `0x083FF440`–`0x087FA9F3` | Time Force image (4 MiB), header title `PRTF`, code `APRE` |
| `0x087FA9F4`–`0x088FFFFF` | `MULTIGAME` loader/menu image (title `MULTIGAME`, code `XXXX`) |
| `0x08900000`–`0x0FFFFFFF` | blank fill |

The loader's descriptor table at `0x087FD5C0` lists both games:
`0x080004E1` (Ninja Storm, Thumb) and `0x083FF440` (Time Force), followed by
the ASCII titles `POWER RANGERS NINJA STORM` / `POWER RANGERS TIME FORCE`.

---

## 2. Executive summary

Both halves have **algorithmic password systems** on a 32-symbol alphabet
(5 bits per character), reachable from each game's main menu (`PASSWORD`).

### Ninja Storm — fully reversed

3 characters = 15 bits: **11 data bits + a 4-bit checksum**, scrambled across
the three symbols.

* **level** 1–5 (3 bits): `c2.0`, `c0.3`, `c1.3` (level−1)
* **ranger** (2 bits): `c2.2`, `c1.1` — 0 = Wind, 1 = Thunder, 2 = Green
* **difficulty** (2 bits): `c2.3`, `c1.0` — 0 = Easy, 1 = Normal, 2 = Hard
* **checksum** (4 bits): `c1.2`, `c0.2`, `c2.4`, `c2.1`
* four reserved bits (`c0.0`, `c0.1`, `c0.4`, `c1.4`) must be zero

The encoder reproduces **23 of 24** published codes exactly. The single
mismatch (`GLW`) is a **typo in the published lists**: the algorithm yields
`GLG`, and `GLG` was accepted in the emulator (Crimson Thunder Ranger), while
the published Easy-Thunder-5 slot is otherwise inconsistent with every other
code. Difficulty **2 (Hard)** is permitted by the validator but no published
list uses it, so those codes are new (e.g. `BKB` = Green, level 1, Hard).

**Hidden developer code: `THQ`.** The validator has a special case at
`0x0804955C` that returns success for symbol indices `(15,5,12)` = `T`,`H`,`Q`.
Entering it plays the **credits** — confirmed in-game. This is the publisher's
initials (THQ) and is not in any published code list.

### Time Force — fully reversed

4 characters = 20 bits on the alphabet
`BCDFGHJKLMNPQRSTVWXYZ0123456789-` (note the final `-`, not `!`).
The value→text encoder at `0x0840229A` packs the 20-bit value
**little-endian 5 bits per character** (`c0 = value & 31`, then `>>5`, …).

The validator is `0x08401BB8`; the submission path is
`0x0840CC6C → 0x0840D77C → 0x08401BB8`. The 20 bits are:

* **1 marker bit** `v0`, which must be **1** (the validator returns it);
* **chapter** `A` — 3 bits, `0..6`;
* **mode** — 2 bits, `0..2`;
* **continues** `B` — 4 bits, `0..15`;
* **progress flags** `C` — 5 bits, `0..30`;
* **5 check bits** — `v6 = parity(A)`, `v12 = parity(B)`,
  `v4 = parity(mode)`, `v19 = parity(C)`, and
  `v16 = v6 ^ v0 ^ v12 ^ v4 ^ v19`.

That gives **7 × 3 × 16 × 31 = 10,416** structurally valid codes out of
`2^20 = 1,048,576`. All seven published codes decode cleanly, and every one is
a **canonical output of the ROM's own encoder** (§6.2) — the published list has
no typos. `HBLD`, `KD4Q`, `CNGF` and `8QSD` were also entered in mGBA.

**Novel code: `W3DB`** = chapter 6 (final chapter), mode 2, 0 continues, no
flags. It is absent from every published list (those use mode 0/1 only) and was
entered in mGBA: the game shows `VALID PASSWORD ENTERED!` and starts the
final-chapter crystal arena. Pausing then displays **`W3DB`** again, proving the
ROM's generator produces exactly this code for that state. Bounds are proven by
rejection: `HBLB` (one check bit flipped), `FNDB` (chapter 7), `CCW7` (all five
flags set), `MVBD` (mode 3), and `BBBB` (marker bit 0) are all rejected with
`INVALID PASSWORD`.

---

## 3. How to reproduce

### Emulator

```bash
sudo apt-get install -y mgba-sdl xvfb xdotool imagemagick openbox
Xvfb :99 -screen 0 1024x768x24 &
DISPLAY=:99 openbox &
DISPLAY=:99 SDL_AUDIODRIVER=dummy mgba -3 "2 Games in 1 - ....gba" &
```

`openbox` is required for xdotool key delivery; capture with
`import -window <wid>`. Default mGBA keymap: A=`x`, B=`z`, L=`a`, R=`s`,
Start=`Return`, Select=`BackSpace`, D-pad = arrows. Hold ~180 ms.

### Path

```
Boot menu: Ninja Storm (default) or Right -> Time Force, then A
 -> language (A = English) -> logos -> title (START)
 -> main menu: NEW GAME / PASSWORD / OPTION  (Down, A on PASSWORD)
```

Ninja Storm grid (11/10/11):

```
B C D F G H J K L M N
P Q R S T V W X Y Z
0 1 2 3 4 5 6 7 8 9 !
```

Time Force grid (8×4):

```
B C D F G H J K
L M N P Q R S T
V W X Y Z 0 1 2
3 4 5 6 7 8 9 -
```

### Codes exercised

| Game | Input | Observed result |
|---|---|---|
| Ninja Storm | `GJN` | accepted — Green Ranger, level 1 |
| Ninja Storm | `GLG` | accepted — Crimson Thunder Ranger (published `GLW` is wrong) |
| Ninja Storm | `THQ` | **credits** (hidden publisher code) |
| Time Force | `HBLD` | "VALID PASSWORD ENTERED!", chapter 0 (prison facility) starts |
| Time Force | `KD4Q` | chapter 1 (city / "PICK UP THE CHRONO MORPHER") |
| Time Force | `CNGF` | chapter 2 (bank) |
| Time Force | `8QSD` | chapter 6, mode 1 (rooftop jetpack fight) |
| Time Force | `W3DB` | **novel**: chapter 6, mode 2 (crystal arena); pause round-trips to `W3DB` |
| Time Force | `HGLF` | chapter 0 with 15 continues; pause shows `CONTINUES 15`, `HGLF` |
| Time Force | `HQSB` | chapter 6, mode 0; crystal arena → ending credits |
| Time Force | `HBLB`, `FNDB`, `CCW7`, `MVBD`, `BBBB` | all rejected: `INVALID PASSWORD` |

---

## 4. Address map

### Ninja Storm

| ROM address | What |
|---:|---|
| `0x0804AE0C` | password-screen init (clears `B+0x2426..0x2429`) |
| `0x0804B1C6` | submit handler (calls validator, then THQ check) |
| `0x0804D090` | packer: 3 chars → 15-bit value (`P = c2 | c1<<5 | c0<<10`) |
| `0x0804CEA0` | core validator (bit fields + checksum, returns −1 or value) |
| `0x0804955C` | special case: returns 1 iff buffer = `(15,5,12)` = `THQ` |
| `0x0804B29A` | character-entry store (writes the buffer) |
| `0x0804D4A0` | render: draws the two/three entered symbols |

Ninja Storm RAM:

| Address | Use |
|---|---|
| `0x03005244` | pointer to the screen-state struct (`= 0x03000068` at the screen) |
| `0x0300248E` | password buffer, 3 bytes, 0-based alphabet indices (`B+0x2426`) |
| `0x0300247D`/`0x0300247E` | cursor / field counters (`B+0x2415`, `+0x2416`) |

### Time Force

| ROM address | What |
|---:|---|
| `0x08401BB8` | **validator**: 5 parity checks + 3 range checks; returns `v0` |
| `0x0840CC6C` | 4th-symbol handler: packs the entry, calls validator, sets valid/invalid screen state |
| `0x0840D77C` | pack 4 entered symbol indices → 20-bit value, then call validator |
| `0x08402260` | password generator/display: struct → 20-bit value → `0x030022F4` |
| `0x08401D14` | check-bit repair (writes `v6`, `v12`, `v4`, `v19`, `v16`) |
| `0x084021D8` | read chapter `A` from the value |
| `0x084021F4` | write chapter `A` into the value |
| `0x08402174` | read mode from the value (2 bits, `v3`/`v9`) |
| `0x08402120` | write mode into the value |
| `0x08402240` | read continues `B` from the value |
| `0x0840229A` | encoder: 20-bit value → 4 characters (5-bit little-endian groups) |
| `0x08401CA4` / `0x08401B38` | value ↔ five `C` progress flags (copy to/from `0x03002354+8/+20/+32/+44/+56`) |
| `0x084020EC` | range check: `C != 31` (sum of the five flag bits ≤ 4) |
| `0x08402098` | range check: mode bits `v3`,`v9` not both set (mode ≤ 2) |
| `0x084020C8` | range check: chapter `A ≤ 6` |
| `0x0840D664` / `0x0840D6F0` | valid / invalid message screens |
| `0x0859BAF4` | alphabet string `BCDFGHJKLMNPQRSTVWXYZ0123456789-` |
| `0x085A1134` | second copy of the alphabet (UI bank) |
| `0x085A1158` | `Valid Password` / `0x085A1170` `Invalid Password` |
| `0x085A35F4` | `Enter Password` |
| `0x030022F0` | pointer to the password-screen state struct passed to the validator |
| `0x030022F4` | ASCII 4-character output buffer written by `0x0840229A`; held `HBLD` in the RAM dump |
| `0x03002354` | progress-flag block; `+8/+20/+32/+44/+56` are the five `C` bits |

The password struct (`*0x030022F0`) has this layout: `+4` 20-bit value,
`+8` continues `B`, `+16` mode, `+20` chapter `A`. The in-game display
generator (`0x08402260`) uses the same field layout and writes the four
characters to `0x030022F4`; that is how the round-trip `W3DB` → pause →
`W3DB` was proven.

---

## 5. Algorithm

### 5.1 Ninja Storm bit layout (derived)

```python
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0123456789!"   # 32 symbols, 5 bits

def encode(level, ranger, diff):
    # level 1..5, ranger 0=Wind 1=Thunder 2=Green, diff 0=Easy 1=Normal 2=Hard
    L = level - 1
    L0, L1, L2 = L & 1, (L >> 1) & 1, (L >> 2) & 1
    R0, R1 = ranger & 1, (ranger >> 1) & 1
    D0, D1 = diff & 1, (diff >> 1) & 1
    # checksum: 4 bits, computed over the data bits only
    s = L0 + 4*R0 + 8*D0 + 2*D1 + 4*R1 + L2 + 2*L1 + 9
    K = (-s) & 0xF
    K0, K1, K2, K3 = K & 1, (K >> 1) & 1, (K >> 2) & 1, (K >> 3) & 1
    c0 = (K1 << 2) | (L1 << 3)          # bits 0,1,4 stay 0
    c1 = D1 | (R1 << 1) | (K0 << 2) | (L2 << 3)
    c2 = L0 | (K3 << 1) | (R0 << 2) | (D0 << 3) | (K2 << 4)
    return ALPHA[c0] + ALPHA[c1] + ALPHA[c2]
```

The validator computes the same checksum as
`(-( (b0 & 0x0D) + ((b0>>4)&6) + (b1 & 0x0F) + ((b1>>4)&6) + 9 )) & 0xF`
on the packed bytes and compares it with the four stored bits, then range
checks level ≤ 4 (0-based), ranger ≠ 3, difficulty ≠ 3, and the reserved bits.

### 5.2 Ninja Storm special case (`0x0804955C`)

```c
int thq_check(u8 *buf) {
    return buf[0] == 15 && buf[1] == 5 && buf[2] == 12;  // 'T','H','Q'
}
```

Reached when the normal validator fails; returning 1 routes the UI to the
credits sequence instead of the "invalid" path.

### 5.3 Time Force packing (`0x08401BB8`, `0x0840D77C`)

The 20-bit value is stored little-endian, five bits per symbol. The validator
at `0x08401BB8` computes all checks from bits of the value; the submission
handler `0x0840D77C` builds the same value from the four entered symbol indices.
`v[n]` below means bit `n` of the value (`v0` is the least significant bit).

```python
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0123456789-"   # 32 symbols, index = 5 bits

def pack(chapter, mode, continues, flags):
    """chapter 0..6, mode 0..2, continues 0..15, flags 0..30 -> 4 chars"""
    assert 0 <= chapter <= 6 and 0 <= mode <= 2
    assert 0 <= continues <= 15 and 0 <= flags <= 30
    v = 1                                   # v0: marker, always 1
    a = [(chapter >> i) & 1 for i in range(3)]
    v |= a[0] << 1 | a[1] << 8 | a[2] << 11
    v |= ((continues >> 0) & 1) << 2 | ((continues >> 1) & 1) << 7 \
       | ((continues >> 2) & 1) << 13 | ((continues >> 3) & 1) << 15
    v |= ((mode >> 0) & 1) << 3 | ((mode >> 1) & 1) << 9
    v |= ((flags >> 0) & 1) << 5 | ((flags >> 1) & 1) << 10 \
       | ((flags >> 2) & 1) << 14 | ((flags >> 3) & 1) << 17 \
       | ((flags >> 4) & 1) << 18
    b_par = continues.bit_count() & 1
    m_par = ((mode >> 0) ^ (mode >> 1)) & 1
    v |= (a[0] ^ a[1] ^ a[2]) << 6                       # v6  = parity(A)
    v |= b_par << 12                                     # v12 = parity(B)
    v |= m_par << 4                                      # v4  = parity(mode)
    v |= (flags.bit_count() & 1) << 19                   # v19 = parity(C)
    v |= ((a[0] ^ a[1] ^ a[2]) ^ 1 ^ b_par
          ^ m_par ^ (flags.bit_count() & 1)) << 16       # v16 = overall
    return "".join(ALPHA[(v >> (5 * i)) & 31] for i in range(4))

def unpack(code):
    if len(code) != 4:
        return None
    try:
        v = sum(ALPHA.index(c) << (5 * i) for i, c in enumerate(code))
    except ValueError:
        return None                      # symbol not on the 32-symbol grid
    b = [(v >> i) & 1 for i in range(20)]
    return dict(value=v,
                chapter=b[1] | b[8] << 1 | b[11] << 2,
                mode=b[3] | b[9] << 1,
                continues=b[2] | b[7] << 1 | b[13] << 2 | b[15] << 3,
                flags=b[5] | b[10] << 1 | b[14] << 2 | b[17] << 3 | b[18] << 4,
                check=(b[6], b[12], b[4], b[19], b[16]))

def valid(code):
    d = unpack(code)
    if d is None:
        return False
    b = [(d["value"] >> i) & 1 for i in range(20)]
    return (b[0] == 1
            and (b[1] ^ b[8] ^ b[11]) == b[6]
            and (b[2] ^ b[7] ^ b[13] ^ b[15]) == b[12]
            and (b[3] ^ b[9]) == b[4]
            and (b[5] ^ b[10] ^ b[14] ^ b[17] ^ b[18]) == b[19]
            and (b[6] ^ b[0] ^ b[12] ^ b[4] ^ b[19]) == b[16]
            and d["chapter"] <= 6
            and d["mode"] <= 2
            and d["flags"] <= 30)
```

`pack(0, 0, 5, 0)` = `HBLD`, `pack(1, 0, 5, 30)` = `KD4Q`,
`pack(2, 0, 8, 0)` = `CNGF`, `pack(6, 1, 7, 0)` = `8QSD` and
`pack(0, 1, 3, 0)` = `8GBB` (the code the game itself displayed after the
`HBLD` chapter had advanced). This is the ROM's generator, not merely a
checksum-compatible encoder.

### 5.4 Time Force field semantics

* **Chapter `A` (3 bits).** `A = 0` is the prison facility, `A = 1` the city
  ("pick up the Chrono Morpher"), `A = 2` the bank, and `A = 6` the final
  chapter. The seven published codes map to `A = 0..6` with no gaps.
* **Continues `B` (4 bits).** The pause screen prints `B` as the two-digit
  `CONTINUES` value. Verified in-game: `B = 15` → `CONTINUES 15` (`HGLF`),
  `B = 7` → `07` (`8QSD`), `B = 5` → `05` (`KD4Q`), `B = 0` → `00` (`W3DB`).
  The counter is live, so a pause taken after play can show fewer continues
  than the value that was originally encoded.
* **Mode (2 bits).** Chapter variant/scenario selector, values 0/1/2. At
  chapter 6, `mode = 1` (`8QSD`) starts the rooftop jetpack fight while
  `mode = 0` (`HQSB`) and `mode = 2` (`W3DB`) start the crystal arena.
* **Flags `C` (5 bits).** Five one-bit progress flags copied between the
  password value and the save-state block at `0x03002354+8/+20/+32/+44/+56`
  by `0x08401CA4` / `0x08401B38`. All 31 combinations are representable; `31`
  (all five set) is explicitly rejected by `0x084020EC`.

---

## 6. Tables

### 6.1 Ninja Storm — published codes and decoded fields

| Code | Level | Ranger | Difficulty |
|---|---:|---|---|
| `GJN` | 1 | Green | Normal |
| `GDP` | 2 | Green | Normal |
| `LJN` | 3 | Green | Normal |
| `LDP` | 4 | Green | Normal |
| `GNN` | 5 | Green | Normal |
| `GGS` | 1 | Thunder | Normal |
| `GBT` | 2 | Thunder | Normal |
| `LGS` | 3 | Thunder | Normal |
| `LBT` | 4 | Thunder | Normal |
| `GLS` | 5 | Thunder | Normal |
| `GG5` | 1 | Wind | Normal |
| `GB6` | 2 | Wind | Normal |
| `LG5` | 3 | Wind | Normal |
| `LB6` | 4 | Wind | Normal |
| `GL5` | 5 | Wind | Normal |
| `GDC` | 2 | Green | Easy |
| `LJB` | 3 | Green | Easy |
| `LDC` | 4 | Green | Easy |
| `GNB` | 5 | Green | Easy |
| `GBH` | 2 | Thunder | Easy |
| `LBH` | 4 | Thunder | Easy |
| `GLG` | 5 | Thunder | Easy (published `GLW` is a typo) |
| `GBW` | 2 | Wind | Easy |
| `LBW` | 4 | Wind | Easy |
| `GLV` | 5 | Wind | Easy |

New (not published): any difficulty-2 code from §5.1, e.g.

| Level | Green | Thunder | Wind |
|---:|---|---|---|
| 1 | `BKB` | `BHG` | `BHV` |
| 2 | `BFC` | `BCH` | `BCW` |
| 3 | `QKX` | `QH1` | `QHB` |
| 4 | `QFY` | `QC2` | `QCC` |
| 5 | `BPB` | `BMG` | `BMV` |

Only structural validity is proven for difficulty 2; none was entered in the
emulator (see §8).

### 6.2 Time Force — published codes and decoded fields

Every published code passes the validator and is exactly `pack(chapter, mode,
continues, flags)` — no typos, no alternate encodings.

| Code | Claimed | Chapter `A` | Mode | Continues `B` | Flags `C` | In-game |
|---|---|---:|---:|---:|---:|---|
| `HBLD` | Access level 0 | 0 | 0 | 5 | 0 | **verified** — chapter 0 (prison) |
| `KD4Q` | Access level 1 | 1 | 0 | 5 | 30 | **verified** — chapter 1 (city) |
| `CNGF` | Access level 2 | 2 | 0 | 8 | 0 | **verified** — chapter 2 (bank) |
| `FLLF` | Access level 3 | 3 | 0 | 12 | 0 | validator + canonical encoder |
| `HDSF` | Access level 4 | 4 | 0 | 13 | 0 | validator + canonical encoder |
| `KGNF` | Access level 5 | 5 | 0 | 15 | 0 | validator + canonical encoder |
| `8QSD` | Last boss | 6 | 1 | 7 | 0 | **verified** — chapter 6 rooftop jetpack fight |

New (not published): every code with mode 2, e.g. `W3DB` (§6b.2).

---

## 6b. Enumeration

### 6b.1 Time Force — space and valid set

* Alphabet: the 32 on-screen symbols
  `BCDFGHJKLMNPQRSTVWXYZ0123456789-` (5 bits each); length **exactly 4**.
* Representable inputs: `32^4 = 2^20 = 1,048,576` values (the entry screen
  cannot produce a symbol outside this alphabet).
* Fixed structure: `v0 = 1`; 3-bit chapter `A`; 2-bit mode; 4-bit continues
  `B`; 5-bit flags `C`; five check bits. Check bits are deterministic, so each
  payload has exactly one encoding.
* Accepted payloads: `7 (A) × 3 (mode) × 16 (B) × 31 (C) = 10,416`.
  Equivalently: 1,488 valid codes per chapter × 7 chapters.
* Rejected payloads: `1,048,576 − 10,416 = 1,038,160` (all check failures plus
  the out-of-range chapter 7, mode 3 and `C = 31` values).

### 6b.2 Time Force — novel code confirmed in-game

**`W3DB`** = chapter 6, mode 2, 0 continues, flags 0. It is **not** in the
GameFAQs / ChapterCheats Time Force list (which uses only mode 0 and 1, and
chapters 0–6 with the fixed B/C values in §6.2).

* Entering `W3DB` from `PASSWORD` shows `VALID PASSWORD ENTERED!`
  (`screenshots/tf_novel_W3DB_valid.png`).
* The game then starts the final chapter in the **crystal arena**
  (`screenshots/tf_novel_W3DB_final_scene.png`).
* Pausing immediately shows `PASSWORD W3DB` and `CONTINUES 00`; the ROM's own
  generator reproduces the novel code exactly
  (`screenshots/tf_novel_W3DB_pause_roundtrip.png`). That round-trip is the
  proof that the codec is the real encoder, not merely a checksum match.
* The pause display is generated, not an echo of the typed code: starting from
  `HBLD` and pausing after the prison intro shows `8GBB`, which is exactly
  `pack(chapter 0, mode 1, 3 continues, 0 flags)`. The ROM's state had advanced
  and the generator produced the new, still-valid code
  (`screenshots/tf_generator_HBLD_to_8GBB.png`).

Mode is a real chapter variant: at chapter 6, published `8QSD` (mode 1) starts
the rooftop jetpack fight (`screenshots/tf_mode1_8QSD_rooftop.png`), while
`HQSB` (mode 0) and `W3DB` (mode 2) start the crystal arena
(`screenshots/tf_mode0_HQSB_arena.png`).

### 6b.3 Time Force — bounds proven by rejection

All rejected inputs were typed on the in-game password grid and produced the
`INVALID PASSWORD` screen (`screenshots/tf_reject_*.png`).

| Input | Structure | Why it is out of bounds | Result |
|---|---|---|---|
| `HBLB` | `HBLD` with `v16` flipped | all four field parities still match, but the overall check fails | `INVALID PASSWORD` |
| `BBBB` | value 0 | all parities trivially pass, but the `v0 = 1` marker is 0 | `INVALID PASSWORD` |
| `FNDB` | `A = 7`, mode 0, `B = 0`, `C = 0` | chapter `A ≤ 6` check (`0x084020C8`) fails | `INVALID PASSWORD` |
| `CCW7` | `A = 0`, mode 0, `B = 0`, `C = 31` | all five flags set; `0x084020EC` requires the sum ≤ 4 | `INVALID PASSWORD` |
| `MVBD` | mode 3 (`v3 = v9 = 1`) | `0x08402098` rejects both mode bits set | `INVALID PASSWORD` |

`FNDB`, `CCW7` and `MVBD` have **valid checksums** (verified offline with the
Python model); the game rejects them only through the range checks, which
proves the checksum layer and the range layer separately. `HBLB` is the
complement: range-valid but checksum-invalid.

---

## 7. Validation evidence

**Observed (emulator, screenshots)**
- `GJN` accepted → Green Ranger screen → level 1.
- `GLG` accepted → Crimson Thunder Ranger screen (proves the typo).
- `THQ` accepted → credits scroll with THQ staff names.
- `HBLD` accepted in Time Force → `VALID PASSWORD ENTERED!` → chapter 0
  (prison facility).
- `KD4Q` accepted → chapter 1 (city, "PICK UP THE CHRONO MORPHER"); pause
  shows `PASSWORD KD4Q`, `CONTINUES 05`.
- `CNGF` accepted → chapter 2 (bank); pause shows `PASSWORD CNGF`.
- `8QSD` accepted → chapter 6, mode 1 (rooftop jetpack); pause shows
  `PASSWORD 8QSD`, `CONTINUES 07`.
- `W3DB` (novel) accepted → chapter 6, mode 2 (crystal arena); pause shows
  `PASSWORD W3DB`, `CONTINUES 00`.
- `HGLF` accepted → chapter 0; pause shows `CONTINUES 15`, proving `B` is the
  continues field.
- `HQSB` accepted → chapter 6, mode 0 (crystal arena → ending credits),
  distinguishing mode 0/2 from mode 1 at chapter 6.
- `HBLB`, `BBBB`, `FNDB`, `CCW7`, `MVBD` rejected with `INVALID PASSWORD`.

**Observed (GDB)**
- Write watchpoint on `0x0300248E` fired at `0x0804B29A` when a symbol was
  entered, confirming the buffer and the entry path.
- The buffer held `04 06 0A` after typing `GJN` (0-based alphabet indices).
- RAM dump held ASCII `HBLD` at `0x030022F4` for Time Force.

**Derived (disassembly)**
- Ninja Storm packing, field/checksum layout, range checks, THQ special case.
- Code generation reproduced 23/24 published codes byte-exactly.
- Time Force 5-bit little-endian packing, alphabet address, validator at
  `0x08401BB8`, submission packer at `0x0840D77C`, check-bit repair at
  `0x08401D14`, and the four field accessors.
- The Python codec reproduces the ROM's own generator output for every
  observed state (`HBLD`, `KD4Q`, `CNGF`, `8QSD`, `HGLF`, `8GBB`, `W3DB`) and
  computes the 10,416-code valid set.

**Inferred**
- Mode is a chapter-variant selector (observed at chapter 6; the accessor
  `0x08402174` reads only `v3`/`v9`).
- The five `C` bits are progress flags; their individual in-game labels were
  not needed to complete the codec.
- Difficulty-2 Ninja Storm codes are valid (validator allows it) but untested
  in play.
- The `GLW`→`GLG` conclusion rests on the algorithm plus one in-game check.

---

## 8. Unknowns

- Time Force: the packing, validator, checksum and generator are complete
  (§5.3–§5.4, §6b); nothing about the code format remains open. The only
  unresolved detail is the individual in-game label of each of the five `C`
  flag bits — they are reachable and round-trip, but not named here.
- Difficulty-2 Ninja Storm codes were generated but not entered in the
  emulator (the grid cursor is modal and slow to drive; one test attempt was
  inconclusive). This is a Ninja Storm play-test gap, not a Time Force one.
- Where the 3-step Ninja Storm entry cursor is stored in the state struct
  (screen offsets `+0x2415`/`+0x2416` are the field counters, not the grid
  cursor).
- Whether `THQ` has any effect beyond the credits.
- Save data written by this cart is 512 bytes (`.sav` created during testing);
  its layout was not examined.

---

## 9. Tooling

| Method | Purpose |
|---|---|
| header/logo scan | found the three embedded GBA images |
| `strings -t x` | located Time Force password UI strings and alphabet |
| literal-pool search for RAM buffer | found both password buffers |
| GDB write watchpoint | tied the Ninja Storm buffer to the entry code |
| Thumb disassembly (`objdump -M force-thumb`) | packer, validator, checksum, THQ check |
| `time_force_password.py` (Python, §5.3) | Time Force pack/unpack/valid; `--selftest` reproduces the ROM's generator and enumerates 10,416 valid codes |
| xdotool + `import -window` | code entry and screenshot evidence |
| web (GameFAQs via Wayback, ChapterCheats) | published code lists to test |

Time Force evidence screenshots are in `screenshots/` (`tf_novel_*`,
`tf_reject_*`, `tf_published_*`, `tf_mode*`).

No ROM, graphics, or text from the games is redistributed here; only
addresses, algorithms, and short identifiers needed to describe the passwords.
