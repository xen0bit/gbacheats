# ATV: Quad Power Racing (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/ATV: Quad Power Racing/ATV: Quad Power Racing.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `ATV QUAD POW` |
| Game code | `AQRE` |
| Maker code | `51` (Acclaim) |
| Software version | 0 |
| Entry word | `0xEA00002E` (ARM branch to 0x080000C0) |
| MD5 | `b295f02a07f00f80669352767242268f` |
| SHA-1 | `43a2c71b1f3b4085adee648e5a409be4517cd7bb` |
| SHA-256 | `38a4591cb8d1234ee9952d0d9444edc9772949f65db14cb94693196e4d042a90` |
| CRC32 | `9c1a7dcb` |

GBA-header (Nintendo logo) scan: exactly **one** logo hit, at file `0x4`
(header base `0x0`). This is a single-image cartridge, not a multi-game pack.

Caveat: the header is not pristine — the stored complement byte is `0x76`
while the computed value is `0x72`, and the header checksum at `0xBE` is
`0x0000`. The title/game code/maker/logo are correct and the game boots and
runs normally in mGBA 0.10.5, so the executable and data were treated as the
shipped game; all addresses below are for **this exact file**.

## 2. Executive summary

The earlier triage note “no in-game cheats” is **wrong**. The game has a
first-class password screen:

**Main menu → options → password**. It accepts five symbols drawn from a
five-icon alphabet (Lightning, Wheel, Helmet, Up-arrow, ATV/X). Symbols are
selected with the d-pad and confirmed one slot at a time with A; the fifth A
submits.

The password is a base-5 number `N` of five digits, validated by a
quotient/remainder relation (not a lookup table of code strings). The input
space is **5^5 = 3125** codes; exactly **26** are valid. Twenty-five of them
are the well-known published set (8 Stock + 8 Pro + 8 Open challenge
passwords plus the “unlock everything” code). The **26th code is not in any
published list**:

| | |
|---|---|
| **Novel code** | **Up-arrow, ATV, Wheel, Up-arrow, Up-arrow** (internal digits `3 4 1 3 3`, N = 2418, r = 0) |
| **Effect** | accepted; writes the minimum progress record (`0x1111`), i.e. Stock only, one ATV, lowest track/ATV counts |

It was entered in mGBA, the screen showed **PASSWORD ACCEPTED**, and the
effect was demonstrated by first applying the published “unlock everything”
code (Pro/Open selectable) and then the novel code (Pro/Open show **locked**),
with the IWRAM unlock masks changing from `0x0007/0x01FF/0x01FE` back to
`0x0001/0x0001/0x0002`.

Bounds were proven by rejection in-game: `U A W U T` (one symbol away from the
novel code) and `L L L L L` both show **PASSWORD INVALID**.

There is one and only one caller of the validator in the whole ROM
(`BL 0x081C83B8` from `0x081BC6CE`), so the password screen is the only entry
point for this code system.

This is a different title and a different code system from
*ATV: Thunder Ridge Riders* (10-symbol password); no addresses, alphabets or
tables are shared.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (`/usr/games/mgba`, SDL frontend) on `Xvfb :120`,
`SDL_AUDIODRIVER=dummy`, scale 3.

Keymap used: **A = `x`, B = `z`, Start = Return, Select = BackSpace, D-pad =
arrow keys, L = a, R = s**. Hold keys 120–200 ms.

Exact path:

1. Boot. Wait for the Tantalus splash to pass and the title to show
   `PRESS START`. Press **Start**.
2. Main carousel: `arcade` → `challenge` → `options` (Left/Right, A enters).
   Move to `options` and press **A**.
3. Options carousel: `music`, `sfx`, `speed units`, `password`, `credits`.
   Press **Right** three times from `music` and press **A**.
4. The screen reads `enter password` with five icon cells.
   * **Up** or **Right** = next symbol (4 → 0 wraps).
   * **Down** or **Left** = previous symbol (0 → 4 wraps).
   * **A** = confirm the cell and advance; the **fifth A submits**.
   * The last code entered is kept if you leave and re-enter the screen.
5. Result is shown as `PASSWORD ACCEPTED` (orange) or `PASSWORD INVALID` (red).

Symbol ↔ value mapping (verified from the rendered icons, one value per
screenshot):

| value | icon | GameFAQs name | other published aliases |
|---:|---|---|---|
| 0 | yellow circle, black lightning bolt | Lightning (L) | Frog |
| 1 | dark wheel with spokes | Wheel (W) | Tire |
| 2 | dark helmet with visor | Helmet (H) | — |
| 3 | yellow circle, black up arrow | Up Arrow (Up) | Speed Burst |
| 4 | yellow circle, black ATV seen head-on | ATV / “looks like an X” (X) | — |

Codes tested in the emulator (all observed directly):

| Code (screen order) | Digits | Result |
|---|---|---|
| Lightning Lightning ATV Wheel Lightning | 0 0 4 1 0 | PASSWORD ACCEPTED (published Stock level 1) |
| ATV ATV Helmet Up Wheel | 4 4 2 3 1 | PASSWORD ACCEPTED (published Open level 8) |
| Wheel Wheel Lightning Lightning Up | 1 1 0 0 3 | PASSWORD ACCEPTED (published “unlock everything”) |
| **Up ATV Wheel Up Up** | **3 4 1 3 3** | **PASSWORD ACCEPTED (unpublished, r = 0)** |
| Up ATV Wheel Up ATV | 3 4 1 3 4 | PASSWORD INVALID |
| Lightning Lightning Lightning Lightning Lightning | 0 0 0 0 0 | PASSWORD INVALID |

## 4. Address map

All addresses are ROM (`0x08000000 + file offset`) unless marked RAM.

| Address | Role |
|---|---|
| `0x081BC694` | submit test: reads keys, `key & 1` (A) |
| `0x081BC6A6` | checks cursor; only cursor cell 4 submits |
| `0x081BC6C2` | `memcpy(sp+4, 0x02003848, 8)` (5 digits + cursor) |
| `0x081BC6CE` | **`BL 0x081C83B8`** — the only call to the validator |
| `0x081BC702` | `BL 0x081B9EDC` — applies the decoded progress index |
| `0x081BC81A`–`0x081BC84E` | increment symbol (Up/Right), wraps 4 → 0 |
| `0x081BC858`–`0x081BC8A6` | decrement symbol (Down/Left), wraps 0 → 4 |
| `0x081C83B8` | **validator** (`N`, `q`, `r` checksum) |
| `0x081B9480` | unsigned divide helper (`r0 / r1`) |
| `0x081B94F8` | unsigned modulo helper (`r0 % r1`) |
| `0x081B9EDC` | progress applier (unpacks the 16-bit record into masks) |
| `0x08293CEC` | 26 × u16 progress table, indexed by `r` |
| `0x02003848` | 5-byte symbol buffer (screen struct `r7 + 0xEF8`) |
| `0x02003850` | cursor cell (screen struct `r7 + 0xF00`) |
| `0x02003854` | validator return value (`r7 + 0xF04`) |
| `0x02003858` | busy flag (`r7 + 0xF08`) |
| screen struct base | `0x02002950` (`r7`) |
| `0x03000020` | mode-availability bitmask (bit0 stock, bit1 pro, bit2 open) |
| `0x03000022` | constant `0x01FE` written by the applier |
| `0x03000024/26/28` | per-mode track/count bit arrays |
| `0x0300002A` | global ATV bitmask |
| `0x0300002C/2E` | per-mode ATV bit arrays |

The buffer address is reached as `r7 + 0xEF8` where `r7` is the heap-allocated
screen object; there is no literal pointer to `0x02003848` anywhere in ROM or
RAM, which is why a literal scan for the buffer fails.

## 5. Algorithm

Reimplementation of `0x081C83B8` (see `pwmodel.py`):

```python
# d[0..4] = the five symbols, left to right, each 0..4
N = d[0]*625 + d[1]*125 + d[2]*25 + d[3]*5 + d[4]   # base-5, 0..3124

q = N // 26                # unsigned
r = N % 26                 # unsigned
if q != ((r + 3) * 31) % 120:
    return 0               # PASSWORD INVALID
apply_progress(r)          # uses table[r] at 0x08293CEC
return 1                   # PASSWORD ACCEPTED, out = r
```

Equivalent search form: the valid codes are exactly
`N = 26*k + r` where `r ∈ [0,25]` and `k = ((r+3)*31) mod 120`.
Because `k < 120` for every `r`, there are exactly 26 valid `N` in `[0,3124]`.

Progress applier (`0x081B9EDC`), per table entry `v = table[r]`:

```
n3 = v >> 12          ; bits 0..n3-1 of 0x03000020   (modes)
n1 = (v >> 4) & 0xF   ; bits 0..n1-1 of 0x0300002A   (ATVs)
n2 = (v >> 8) & 0xF   ; per-mode array at 0x03000024
n0 = v & 0xF          ; per-mode array at 0x0300002C
0x03000022 = 0x01FE   ; constant
```

It also stores `r` into the profile structure
(`[[0x081CB7AC]+0xC]+0x24+0x14`).

## 6. Tables

### 6.1 The 26 valid codes (complete enumeration)

Format: `r`, N, symbols (L=Lightning, W=Wheel, H=Helmet, U=Up-arrow, A=ATV),
progress word.

| r | N | Code | Progress | Published meaning |
|---:|---:|---|---|---|
| **0** | **2418** | **U A W U U** | `0x1111` | **unpublished — minimum progress** |
| 1 | 105 | L L A W L | `0x1112` | Stock 1 |
| 2 | 912 | W H W H H | `0x1123` | Stock 2 |
| 3 | 1719 | H U U U A | `0x1224` | Stock 3 (+ new ATV) |
| 4 | 2526 | A L W L W | `0x1225` | Stock 4 |
| 5 | 213 | L W U H U | `0x1236` | Stock 5 |
| 6 | 1020 | W U L A L | `0x1337` | Stock 6 (+ new ATV) |
| 7 | 1827 | H A U L H | `0x1348` | Stock 7 |
| 8 | 2634 | A W L W A | `0x2141` | Stock 8 (+ Pro + ATV) |
| 9 | 321 | L H H A W | `0x2142` | Pro 1 |
| 10 | 1128 | W A L L U | `0x2153` | Pro 2 |
| 11 | 1935 | U L H H L | `0x2254` | Pro 3 (+ new ATV) |
| 12 | 2742 | A W A U H | `0x2255` | Pro 4 |
| 13 | 429 | L U H L A | `0x2266` | Pro 5 |
| 14 | 1236 | W A A H W | `0x2367` | Pro 6 (+ new ATV) |
| 15 | 2043 | U W W U U | `0x2378` | Pro 7 |
| 16 | 2850 | A H A L L | `0x3171` | Pro 8 (+ Open + ATV) |
| 17 | 537 | L A W H H | `0x3172` | Open 1 |
| 18 | 1344 | H L U U A | `0x3173` | Open 2 |
| 19 | 2151 | U H W L W | `0x3274` | Open 3 |
| 20 | 2958 | A U U W U | `0x3285` | Open 4 |
| 21 | 645 | W L L A L | `0x3286` | Open 5 |
| 22 | 1452 | H W U L H | `0x3387` | Open 6 |
| 23 | 2259 | U U L W A | `0x3388` | Open 7 |
| 24 | 3066 | A A H U W | `0x3399` | Open 8 |
| 25 | 753 | W W L L U | `0x3399` | “Unlock everything” |

Notes:
* `r=24` (Open 8) and `r=25` (unlock everything) share the same progress word
  `0x3399`; the widely published “unlock everything” password is therefore
  redundant with Open level 8.
* The 24 challenge passwords and the unlock code are exactly the published
  GameFAQs/Danworld list; all 25 are reproduced by the formula, and three were
  also entered in the emulator (Stock 1, Open 8, unlock-everything).

### 6.2 Published list (source: GameFAQs via web.archive.org 2018 snapshot,
plus gamegenie.com/Danworld)

`Lightning=L, ATV/X=X, Wheel=W, Helmet=H, Up Arrow=Up`

```
Stock : LLXWL  WHWHH  HUUUX  XLWLW  LWUHU  WULXL  HXULH  XWLWX
Pro   : LHHXW  WXLLU  ULHHL  XWXUH  LUHLX  WXXHW  UWWUU  XHXLL
Open  : LXWHH  HLUUX  UHWLW  XUUWU  WLLXL  HWULH  UULWX  XXHUW
Extra : WWLLU  (unlock everything)
```

Every one of these 25 maps to `r = 1..25` in the table above; the 26th
(`UAWUU`, `r=0`) is absent from all published lists that were checked
(GameFAQs, gamegenie/Danworld, neoseeker, vizzed, supercheats, etherealgames,
cheatbook, solucionesytrucos).

### 6.3 Unlock mask evidence

IWRAM words after each code (read from savestates):

| address | after `WWLLU` (r=25) | after `UAWUU` (r=0) |
|---|---|---|
| `0x03000020` | `0x0007` | `0x0001` |
| `0x03000022` | `0x01FE` | `0x01FE` |
| `0x03000024` | `0x007E` | `0x0006` |
| `0x03000026` | `0x007E` | `0x0000` |
| `0x03000028` | `0x007E` | `0x0000` |
| `0x0300002A` | `0x01FF` | `0x0001` |
| `0x0300002C` | `0x01FE` | `0x0002` |
| `0x0300002E` | `0x01FE` | `0x0000` |

## 6b. Enumeration

* **Alphabet:** 5 icons → values 0..4 (Lightning, Wheel, Helmet, Up-arrow, ATV).
* **Length:** exactly 5 symbols. The spinner wraps 4→0 / 0→4, so no other
  symbol can be entered through the UI.
* **Space size:** `5^5 = 3125` representable codes. `N` is the base-5 value of
  the five symbols, weight 625/125/25/5/1 left to right; maximum `N = 3124`.
* **Checksum:** 1 relation, `q = ((r+3)*31) mod 120` with `q = N/26`,
  `r = N%26`; the check is exact (normal integer division and modulo, both
  unsigned).
* **Valid set:** exactly **26** of 3125 (`0.83 %`), enumerated in §6.1 and
  re-derived offline in `pwmodel.py`.
* **Novel code (not in any published list):**
  **Up-arrow, ATV, Wheel, Up-arrow, Up-arrow** (`U A W U U`, `N=2418`, `r=0`).
  * Entered in mGBA: **PASSWORD ACCEPTED** with the five icons visible
    (`/tmp/opencode/atvqpr/r0_msg.png`).
  * Effect: progress word `0x1111` — the minimum record. Demonstrated with a
    control: after the published `WWLLU`, challenge → class select offers
    `stock`, `pro`, `open`; after `UAWUU` the same screen shows **locked**
    for pro and open (`/tmp/opencode/atvqpr/ua_class2.png` vs
    `r0_class2.png`). Mask deltas in §6.3.
* **Bounds proven by in-game rejection:**
  * `U A W U T` (`3 4 1 3 4`, `N=2419`): one symbol from the novel code,
    fails `q` (93 ≠ 4) → **PASSWORD INVALID**
    (`/tmp/opencode/atvqpr/bad_msg.png`).
  * `L L L L L` (`0 0 0 0 0`, `N=0`): lowest possible value, fails
    (q 0 ≠ 93) → **PASSWORD INVALID**
    (`/tmp/opencode/atvqpr/lllll_msg.png`).
  * Out-of-range field: a symbol >4 cannot be expressed — the spinner wraps
    at 4, and `N ≥ 3125` needs a sixth base-5 digit, so the space is closed
    at 3124. This is a property of the input widget, observed in RAM
    (`0x02003848` only ever holds 0..4) and in the control flow
    (`cmp r0,#3 / bhi → 0` at `0x081BC83A`).

## 7. Validation evidence

**Observed (emulator):**
* Menus walked: title → main carousel (arcade/challenge/options) → options
  (music/sfx/speed units/password/credits) → password screen; arcade →
  class select (`stock`) → ATV select (`type 1`) → track select
  (`the sand trap`) → race → pause (`paused… resume/restart/quit`); challenge
  → class select with `locked` entries.
* `PASSWORD ACCEPTED` / `PASSWORD INVALID` screens for the six codes listed in
  §3.
* Icon identities per symbol value 0..4 (one capture per value).
* IWRAM masks before/after unlock-everything and the novel code (§6.3).

**Derived (disassembly + RAM):**
* The 5-symbol buffer at `0x02003848` and cursor at `0x02003850` (watchpoint
  on `0x02003848` caught the write at `0x081BC852`, `LR=0x08002E8F`).
* The validator at `0x081C83B8` and its single caller at `0x081BC6CE`.
* Base-5 packing, `/26`, `%26`, and the `((r+3)*31)%120` check.
* The 26-entry progress table at `0x08293CEC` and the mask writes.
* Offline model agrees with all 25 published codes and rejects 3099 values.

**Inferred:**
* Exact human meaning of each progress nibble (mode count / track count /
  ATV count) — consistent with the all-unlock entry, but not individually
  exercised.
* Whether entering `UAWUU` is intended as a “reset progress” developer code
  (it is in the shipped table, so it is at least intentional data).

## 8. Unknowns

* The nibble semantics in §5 are inferred from the applier and the
  all-unlock entry; the per-level track/ATV mapping was not played through.
* The ROM header is non-standard (complement mismatch, zero header checksum);
  whether this copy differs from a pristine No-Intro dump in data outside the
  header was not established. All findings above were verified against this
  file.
* No `.sav`/EEPROM content was written during the session, so persistence of
  the applied progress across power-off was not tested.
* The published code lists name the icons loosely (Frog/Tire/Speed Burst vs
  Lightning/Wheel/Up Arrow); the mapping in §3 is the one observed on screen.
* Other regions/revisions were not tested; addresses are for `AQRE` Rev 0.

## 9. Tooling

* `mGBA 0.10.5` (SDL) under `Xvfb :120` + `openbox`, `xdotool` for input,
  `import`/ImageMagick for screenshots.
* `/tmp/opencode/atvqpr/pwmodel.py` — independent reimplementation and full
  3125-code enumeration.
* `/tmp/opencode/atvqpr/state.py` — mGBA PNG savestate reader (the `gbAs`
  chunk is zlib-compressed; `0x19000..0x20FFF` = IWRAM, `0x21000..0x60FFF` =
  EWRAM), used to read RAM without a debugger.
* `arm-none-eabi-objdump -M force-thumb` for the disassembly; a temporary
  `gdb-multiarch` session against `mgba -g` for the write watchpoint.
* Screenshots referenced above live in `/tmp/opencode/atvqpr/` (not part of
  the repository): `r0_msg.png` (novel code accepted), `r0_class2.png` /
  `ua_class2.png` (locked vs unlocked), `bad_msg.png`, `lllll_msg.png`,
  `open8_acc.png`, `unlock_all_msg.png`, `walk_*.png`.

*Legal note: no ROM, graphics, music or game text is redistributed here; only
addresses, algorithms, code strings and hashes are published.*
