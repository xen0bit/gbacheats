# Britney's Dance Beat (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Britney's Dance Beat/Britney's Dance Beat.gba` |
| Size | 8,388,608 bytes (8 MiB), no appended data |
| Header title | `DANCE BEAT` |
| Game code | `ABYE` |
| Maker code | `78` (THQ) |
| Software version | 0 |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| Fixed byte `0xB2` | `0x96` (correct) |
| Complement check | `0xBD = 0x2A`; `(sum(0xA0..0xBC) + 0x19 + 0x2A) & 0xFF == 0` (intact) |
| MD5 | `bb1a8e9129d4d2dcb4bbb3e4879ee97b` |
| SHA-1 | `8f13503bf068dc13fa60ae8b4f5a83d07ffca5f4` |
| SHA-256 | `b228dcd13427b9f4514375eed1f7f69ca502777e35d8d032581844748d4a8075` |

Embedded-header scan: the 156-byte Nintendo logo occurs **once**, at file offset
`0x4`; there is no second/third GBA image, so this is a single-game cartridge
(not a multi-game pack). No trainer, cracktro, or scene patch was found: the
entry branch is the stock one, the header checksum is valid, the first 4 KiB
contains ordinary ARM crt0/IRQ code, and there are no release-group strings.
Boot shows the normal Links / ART / THQ / Britney Brands sequence.

## 2. Executive summary

Britney's Dance Beat (GBA) has a real, developer-intended **5-character
password system** (`Mode Select → Password`). The on-screen alphabet is the
20 consonants

```
B C D F G H J K L M
N P Q R S T V W X Z
```

stored internally as the byte values 0–19 in exactly that grid order.

The validator is at `0x08006FA0`. It has two layers:

1. **A hard-coded developer backdoor**: the literal 5 bytes
   `0F 05 0C 0E 0B` at `0x0837CF34` = **`THQSP`**. If the input matches it, the
   game sets status bit `0x10` and returns success *without* checking the
   checksum. This code is in no published list and was found only by reading
   the table. In the emulator it unlocks the bonus **Video** but not Concert
   Mode, and leaves the Tour Book empty.
2. **An algorithmic progress code** used by the three published passwords
   (`HMNFK`, `NXRFP`, `DWWFD`). Four of the five symbols carry the state and
   the fifth is a checksum:

```
v[0..4] = indices 0..19 of the 5 displayed letters
if code == "THQSP": status0 |= 0x10; accept          // fixed backdoor
if inv2[v4] != (v0+v1+v2+v3) mod 20: reject          // 5th symbol = checksum
a = inv1[v0]; b = inv2[v1]
X = 20*b + a                                          // 0..399, stored as a byte
if X & 0x10:  R = 20 + v2   (v2 must be <= 15)
else:         R = v2        (v2 must be <= 18)
status1 = (R/6) | ((R%6) << 4)
k = inv1[v3]                                          // 0..11, must be <= 11
mask = (1<<k) - 1
status0 = (X & 0xFF) & 0xEF
if mask == 0x7FF: status0 |= 0x10                     // all-items / Video flag
if ((status0>>1) & 7) > 2: reject                     // bits 1-3 must be 0..2
if status0 & 1: reject                                // bit 0 must be 0
accept
```

where

```
ALPHA = "BCDFGHJKLMNPQRSTVWXZ"
PERM1 = [2,4,6,8,10,12,14,16,18,0,1,3,5,7,9,11,13,15,17,19]   @0x0837CF39
PERM2 = [17,19,15,13,11,9,5,7,1,3,0,16,18,12,14,10,6,8,4,2]   @0x0837CF4D
inv1/inv2 are the inverse permutations.
```

The same ROM also contains the **encoder** for this format at `0x0800716C`.
It is called when the password screen opens and after progress updates, and it
writes the code that represents the current save state into the entry buffer
at `0x03002C40`. This is why the screen is pre-filled: on a fresh state it
pre-fills `WWRDF`; after a smaller unlock it pre-fills a different valid code
(e.g. `CTHQQ`). The encoder and validator agree bit-for-bit, which independently
confirms the model below.

The code space is **20^5 = 3,200,000** strings. Exactly **160,000** pass the
5th-symbol checksum, and **15,804** of those pass every range/flag check.
Adding the fixed `THQSP` gives **15,805 accepted strings**, collapsing to
**10,080 + 1 distinct machine states** (some states have two spellings).
Published lists give only 3 of these strings.

Novel codes confirmed on the real password screen:

| Code | Decoded state | Observed effect | Published? |
|---|---|---|---|
| `THQSP` | fixed branch, `status0|=0x10`, mask 0 | Video unlocked; Concert Mode still locked; Tour Book empty | **No** |
| `WWHQV` | `status0=0x02→0x22`, `status1=0x14`, `k=5` | Concert Mode opens; Tour Book has 5 of 12 pictures; Video stays locked | **No** |
| `WWHFT` | `status0=0x12`, `status1=0x14`, `k=11` | everything unlocked (5 songs, Video, 11 Tour Book pictures) | **No** |
| `JWHLJ` | `status0=0x02`, `status1=0x50`, `k=3` | 3 Tour Book pictures unlocked and Practice song list grows from 1 to 4 songs; Concert/Video stay locked | **No** |

Bounds were proven in-game by rejection: a bad checksum (`WWHQB`), an
out-of-range `k` (`BBBZD`), and an out-of-range status field (`XWBDL`) all
produce the game's **“Incorrect Password !”** message and leave the state
unchanged.

## 3. How to reproduce

**Emulator:** mGBA 0.10.5 SDL (`/usr/games/mgba`) under `Xvfb :213`, 3× scale,
`SDL_AUDIODRIVER=dummy`.

**Default keymap used:** A = `x`, B = `z`, Start = `Return`,
Select = `BackSpace`, L = `a`, R = `s`, D-pad = arrow keys.
Hold keys 100–200 ms; a 0.15–0.2 s gap avoids the menu double-stepping.

**Exact path to the password screen:**

```
boot → title screen → Start
Mode Select: Dance Mode / 2-Player / Puzzle / Password / Options
  Down ×3 → Password → A
```

Entry: the red cursor moves on the 2×10 letter grid with the D-pad; **A**
writes the highlighted letter into the current slot and advances the slot.
After the fifth letter the cursor jumps to **END**; press **A** to submit.
B leaves the screen. A successful code returns to Mode Select; a bad code
shows a red “Incorrect Password !” banner and stays on the screen.

**Testing the novel codes:**

* `THQSP`: Down, Right×5, A, Up, A, Down, Left×3, A, Right×2, A, Left×3, A, A.
* `WWHQV`: Down, Right×7, A, A, Up, Left×2, A, Down, Left×3, A, Right×4, A, A.
* `JWHLJ`: Right×6, A, Down, Right, A, Up, Left×2, A, Right×3, A, Left×2, A, A.
* `WWHFT`: Down, Right×7, A, A, Up, Left×2, A, Left×2, A, Down, Right×2, A, A.

Screenshots (kept on disk, not embedded):

```
/tmp/opencode/britney/shots/05_password_entry.png   password screen + alphabet
/tmp/opencode/britney/shots/42_concert_base.png     baseline lock state (submenu)
/tmp/opencode/britney/shots/92_practice.png         baseline: 1 song unlocked
/tmp/opencode/britney/shots/61_zz_reject.png        "Incorrect Password !"
/tmp/opencode/britney/shots/69_wwhqv.png            WWHQV typed in
/tmp/opencode/britney/shots/71_dance_wwhqv.png      WWHQV effect: Concert open, Video locked
/tmp/opencode/britney/shots/73_tour_wwhqv.png       WWHQV: Concert list with 1 song
/tmp/opencode/britney/shots/75_tour_wwhqv.png       WWHQV: 5 Tour Book pictures
/tmp/opencode/britney/shots/76_pw_bbbzd.png         encoder output CTHQQ pre-filled after WWHQV
/tmp/opencode/britney/shots/49_thqsp.png            THQSP typed in
/tmp/opencode/britney/shots/51_dance_thqsp.png      THQSP effect: Video open only
/tmp/opencode/britney/shots/121_jwhlj.png           JWHLJ typed in
/tmp/opencode/britney/shots/124_tour_jwhlj.png      JWHLJ: 4 songs in Practice list
/tmp/opencode/britney/shots/126_tour_jwhlj.png      JWHLJ: 3 Tour Book pictures
/tmp/opencode/britney/shots/78_bbbzd_reject.png     checksum-valid, k>11 rejected
/tmp/opencode/britney/shots/80_xwbdl_reject.png     checksum-valid, status bits invalid rejected
/tmp/opencode/britney/shots/104_concert_dww.png     DWWFD: all 5 songs
/tmp/opencode/britney/shots/108_concert_nxrfp.png   NXRFP: all 5 songs
/tmp/opencode/britney/shots/58_tour_hmnfk.png       HMNFK: 11 Tour Book pictures (12th still locked)
/tmp/opencode/britney/shots/97_pause.png            pause menu
/tmp/opencode/britney/shots/83_options.png          options screen
/tmp/opencode/britney/shots/87_2p.png              2-Player link error
/tmp/opencode/britney/shots/89_puzzle.png           Puzzle menu
```

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`.

| Address | Meaning |
|---|---|
| `0x08000000` | ARM entry (stock branch to `0x080000C0`) |
| `0x08001050` | keypad read routine; reads `0x04000130`, computes `0x3FF ^ keys` |
| `0x03000DF8` | current **held** active-high key mask (written by above) |
| `0x03000E00` | newly **pressed** active-high key mask |
| `0x03002BD0` | progress/save struct base |
| `0x03002BE6` | struct +22, byte bitmask (≤ `0x1F`; set by password validator) |
| `0x03002BE8` | struct +24, u16 item bitmask (0..`0x7FF`; set by password validator) |
| `0x03002C28` | status0 byte (low 8 bits of `X`, then `&0xEF`, then all-items bit `0x10`) |
| `0x03002C29` | status1 byte: `(R/6) | ((R%6)<<4)` |
| `0x03002C40` | **5-byte password buffer**, values 0–19, grid order |
| `0x03002C48` | error-message flag set on failed submit (`=1`) |
| `0x08006F80` | helper: index-of-byte in a 20-byte table |
| `0x08006FA0` | **password validator** (checksum, field decode, range checks) |
| `0x0800716C` | **password encoder** (state → 5 characters) |
| `0x0837CF34` | fixed 5-byte code `0F 05 0C 0E 0B` = `THQSP` |
| `0x0837CF39` | `PERM1` (20 bytes) |
| `0x0837CF4D` | `PERM2` (20 bytes) |
| `0x0837CF61` | 36-byte identity table `0x00..0x23`; validator uses `[0..18]` / `[20..35]`, encoder uses `[R]` |
| `0x0837CF75` | `TABLE+20` (`0x14..0x23`), the validator's high-range `v2` table |
| `0x08014520` | signed division helper |
| `0x080145B8` | modulo helper |
| `0x08007912` | caller: submit password, branches on validator return |
| `0x08007966` | failure path: sets `0x03002C48 = 1` (shows “Incorrect Password !”) |
| `0x08007608` | encoder call: password-screen init (pre-fills buffer) |
| `0x0800BFC4` | encoder call in the progress-update path (state changes → regenerated password) |
| `0x08001274` / `0x080012FC` | post-success screen/mode dispatch, selected by `status1` nibbles |

Instruction-level confirmations:

* `0x08006FA4`–`0x08006FBE`: five-byte compare against `0x0837CF34`; on match
  `0x08006FC2`–`0x08006FCC` ORs `0x10` into `0x03002C28` and returns 1 — the
  fixed backdoor, before any checksum.
* `0x08006FDC`–`0x08007008`: `inv2(buf[4])` compared with
  `(buf[0]+buf[1]+buf[2]+buf[3]) % 20` — the checksum.
* `0x0800700E`–`0x0800702E`: computes `X = 20*inv2(buf[1]) + inv1(buf[0])`
  and writes it to `0x03002C28`.
* `0x08007030`–`0x08007054`: tests `X & 0x10`, decodes `R` and writes
  `status1 = (R/6) | ((R%6)<<4)`.
* `0x080070A2`–`0x080070CE`: `k = inv1(buf[3])`, builds `(1<<k)-1`, stores at
  struct +24.
* `0x08007116`–`0x08007148`: `status0 &= 0xEF`, restores bit `0x10` when the
  mask is `0x7FF`, then rejects `((status0>>1)&7) > 2`, `mask > 0x7FF`, and
  `status0 & 1`.

## 5. Algorithm

### 5.1 Validator (reimplementation)

```python
ALPHA = "BCDFGHJKLMNPQRSTVWXZ"          # grid order, byte value = index
PERM1 = [2,4,6,8,10,12,14,16,18,0,1,3,5,7,9,11,13,15,17,19]
PERM2 = [17,19,15,13,11,9,5,7,1,3,0,16,18,12,14,10,6,8,4,2]
INV1 = {v:i for i,v in enumerate(PERM1)}
INV2 = {v:i for i,v in enumerate(PERM2)}

def decode(code):
    v = [ALPHA.index(c) for c in code]
    if code == "THQSP":
        return True, 0x10, None, None          # status0, status1, k
    if INV2[v[4]] != (v[0]+v[1]+v[2]+v[3]) % 20:
        return False, "checksum"
    a, b = INV1[v[0]], INV2[v[1]]
    X = 20*b + a
    if X & 0x10:
        if v[2] > 15: return False, "v2>15"
        R = 20 + v[2]
    else:
        if v[2] > 18: return False, "v2>18"
        R = v[2]
    k = INV1[v[3]]
    if k > 11: return False, "k>11"
    mask = (1 << k) - 1
    status0 = (X & 0xFF) & 0xEF
    if mask == 0x7FF: status0 |= 0x10
    if ((status0 >> 1) & 7) > 2: return False, "status bits 1-3"
    if status0 & 1: return False, "status bit 0"
    status1 = (R // 6) | ((R % 6) << 4)
    return True, status0, status1, k
```

### 5.2 Encoder (the ROM's own generator, `0x0800716C`)

The encoder order matters: it first decides the `R` range and sets a
*temporary* bit 4 in `status0`, then uses that working `X` for the
`PERM1`/`PERM2` split, and finally restores the original bit 4 in the stored
`status0`.

```
input: status0 (byte at 0x03002C28), status1 (byte at 0x03002C29),
       item mask M (u16 at 0x03002BD0+24)

# 0x08007174-0x08007184
saved_bit4 = status0 & 0x10
status0 &= 0xEF                       # clear bit4 in the stored status0

# 0x08007196-0x080071A2: clear buffer[0..4]

# 0x080071A4-0x080071B8
R  = (status1 >> 4) + 6 * (status1 & 0x0F)
v2 = TABLE[R]                         # TABLE @0x0837CF61 = 0x00..0x23 (0..35)
buf[2] = v2

# 0x080071BA-0x080071CE: decide the high R range FIRST
if v2 > 19:
    buf[2] = v2 - 20
    status0 |= 0x10                   # working X, e.g. 0x02 -> 0x12

# 0x080071D0-0x080071F2: split the working X, not the canonical status0
X = status0
buf[0] = PERM1[X % 20]
buf[1] = PERM2[X / 20]

# 0x080071F4-0x08007214
k = count_trailing_ones(M)            # M must be (1<<k)-1
buf[3] = PERM1[k]

# 0x08007216-0x0800723A
buf[4] = PERM2[(buf[0]+buf[1]+buf[2]+buf[3]) % 20]

# 0x0800723C-0x08007248: restore the original bit4 in the stored status0
status0 = (status0 & 0xEF) | saved_bit4
```

Worked examples (both generated by this ROM and both pass the validator):

* fresh state `status0=0x02`, `status1=0x35`, `M=0`: `R=33 >= 20`, so the
  working `X` is `0x12`; `PERM1[0x12 % 20] = 17 ('W')`,
  `PERM2[0x12 / 20] = 17 ('W')`, `v3=PERM1[0]=2 ('D')`,
  `v4=PERM2[9]=3 ('F')` → **`WWRDF`**; the stored `status0` returns to `0x02`.
* post-WWHQV state `status0=0x22`, `status1=0x14`, `M=0x1F`: `R=25`, working
  `X=0x32`; `PERM1[10]=1 ('C')`, `PERM2[2]=15 ('T')`, `v3=PERM1[5]=12 ('Q')`,
  `v4=PERM2[13]=12 ('Q')` → **`CTHQQ`**; the stored `status0` returns to `0x22`.

The output is written to `0x03002C40` and drawn on the password screen. This
is why the entry field is always pre-filled, and why the pre-filled code
changes as the save state changes.

### 5.3 Field/bit layout

| Symbol | Bits | Meaning |
|---|---|---|
| `v0` | 0–4 | split of `X` into `a` (0–19) |
| `v1` | 0–4 | split of `X` into `b` (0–19) |
| `v2` | 0–4 | `R` low range 0–18 or high range 20–35 (selected by bit4 of `X`) |
| `v3` | 0–4 | `k` = number of unlocked Tour Book pictures (0–11) |
| `v4` | 0–4 | checksum `PERM2^-1[(v0+v1+v2+v3) % 20]` |
| `status0` | 8 | low byte of `X`; bits 1–3 must be 0–2; bit 0 must be 0; bit 4 = all-items/Video flag after canonicalisation |
| `status1` | 8 | base-6 packing of `R`: low nibble = `R/6`, high nibble = `R%6` |
| `M` | 16 | `(1<<k)-1`, item bitmask (0x7FF = 11 items) |
| struct+22 | 8 | `(1<<k)-1` for `k<=4`, else `0x1F` (secondary mask) |

## 6. Tables

### 6.1 Fixed hard-coded code

```
0x0837CF34: 0F 05 0C 0E 0B     -> THQSP  (developer backdoor)
```

### 6.2 Published codes, verified against the ROM

| Code | Decoded fields | Status | In-game result |
|---|---|---|---|
| `HMNFK` | `X=0x70`, `R=30`, `k=11`, `status1=0x05` | accepted | all 5 songs, Video, Concert, 11/12 pictures |
| `NXRFP` | `X=0xF4`, `R=33`, `k=11`, `status1=0x35` | accepted | all 5 songs, Video, Concert |
| `DWWFD` | `X=0x00`, `R=17`, `k=11`, `status1=0x52` | accepted | all 5 songs, Video, Concert |
| `THQSP` | fixed literal | accepted | Video only |

Published label for `DWWFD` claims “unlock all songs, puzzles the video,
concert mode and 12 pictures.” Observation: all four puzzle thumbnails are
already visible at baseline, and the password opens 11 of the 12 Tour Book
cells; the 12th stays dark. `HMNFK` behaves identically in the menus. The “12 pictures”
part of the published description is therefore **not** reproduced by this
revision's passwords and should be treated as a label error (or as content
gated by play, not by the code).

### 6.3 Symbol table and permutations

```
ALPHA   = B C D F G H J K L M N P Q R S T V W X Z     (indices 0..19)
PERM1   = 02 04 06 08 0A 0C 0E 10 12 00 01 03 05 07 09 0B 0D 0F 11 13
PERM2   = 11 13 0F 0D 0B 09 05 07 01 03 00 10 12 0C 0E 0A 06 08 04 02
TABLE_D = 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
          10 11 12 13 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F
          20 21 22 23            (36 bytes, 0..35) @0x0837CF61
TABLE_C = TABLE_D[20..35] = 14 15 16 17 18 19 1A 1B 1C 1D 1E 1F 20 21 22 23
```

### 6.4 Pre-filled codes produced by the ROM's encoder

| Incoming stored state | Working `X` (feeds PERM1/PERM2) | Stored `status0` after the call | Generated code |
|---|---|---|---|
| fresh: `status0=0x02`, `status1=0x35` (`R=33`), `k=0` | `0x02 \| 0x10 = 0x12` | `0x02` (bit4 restored to 0) | `WWRDF` |
| after WWHQV: `status0=0x22`, `status1=0x14` (`R=25`), `k=5` | `0x22 \| 0x10 = 0x32` | `0x22` (bit4 restored to 0) | `CTHQQ` |

Both were observed on the password screen (`WWRDF` on first entry; `CTHQQ`
after the WWHQV unlock). In the fresh case the `0x12` that feeds
`PERM1`/`PERM2` is the temporary `X`, not the stored `status0` (which returns
to `0x02`); using the stored `0x02` as the split input would give the
non-existent `JWRDF`. Decoding `CTHQQ` with the model above gives exactly the
state that WWHQV had set, so the model and the ROM's encoder are consistent.

## 6b. Enumeration

**Space definition.** Five symbols, each one of 20 values, so
`20^5 = 3,200,000` representable strings. The alphabet is fixed by the
on-screen keyboard (the 20 consonants above); the UI offers no other symbol,
and there are exactly five slots. The fifth symbol is fully determined by the
first four through the checksum, so only `20^4 = 160,000` strings are
checksum-valid.

**Validator model.** Fully reimplemented above and run over all `20^4`
prefixes:

* checksum-valid strings: **160,000**
* accepted by the semantic layer: **15,804**
* accepted in total when the fixed literal `THQSP` is added: **15,805**
* distinct machine states `(status0, status1, k)`: **10,080** (+1 fixed)
* codes per `k`: **1,317** for every `k = 0..11`
* aliases: every state has 1 or 2 accepted spellings (the `X` vs `X+256`
  truncation), never more

**Novel codes (not in GameFAQs / VGChartz / SuperCheats / IGN / GameRevolution /
any list found):**

| Code | k | state | In-game proof |
|---|---|---|---|
| `THQSP` | fixed | `status0=0x12` | Video becomes selectable; Concert still greyed; Tour Book still empty (`49_thqsp.png`, `51_dance_thqsp.png`) |
| `WWHQV` | 5 | `(0x22,0x14,5)` | Concert Mode opens with 1 song; Tour Book shows 5 of 12 pictures; Video remains locked (`69/71/73/75_*.png`) |
| `JWHLJ` | 3 | `(0x02,0x50,3)` | Tour Book shows 3 pictures; Practice song list grows from 1 to 4 songs; Concert/Video locked (`121/124/126_*.png`) |
| `WWHFT` | 11 | `(0x12,0x14,11)` | everything unlocked: 5 songs, Video, 11 pictures (`109/111/112_*.png`) |

`WWHQV` is the recommended showcase: it is accepted, it produces a state the
published codes cannot produce (Concert open but Video locked and only 5
pictures), and the game itself confirms the decoded state by re-generating
`CTHQQ` on the next visit to the password screen.

**Bounds proven by rejection (all shown in-game, state unchanged):**

| Input | Why it must fail | Observed |
|---|---|---|
| `WWHQB` | checksum: `inv2[0]=10 != (17+17+5+12)%20=11` | “Incorrect Password !” (`68_after_wwhqb.png`) |
| `ZZZZZ` | checksum: `inv2[19]=1 != (19*4)%20=16` | “Incorrect Password !” (`61_zz_reject.png`) |
| `BBBZD` | checksum valid, but `k=inv1[19]=19 > 11` | “Incorrect Password !” (`78_bbbzd_reject.png`) |
| `XWBDL` | checksum valid, `k=0`, but `status0=0x08`, `(0x08>>1)&7=4 > 2` | “Incorrect Password !” (`80_xwbdl_reject.png`) |

`BBBZD` and `XWBDL` are the important ones: both are checksum-correct, so they
prove that the ROM enforces the `k<=11` and `status bits 1–3` range checks
independently of the checksum. Conversely `THQSP` is checksum-incorrect yet
accepted, which proves the fixed backdoor is a separate compare.

## 7. Validation evidence

**Observed (emulator):**

* Password screen alphabet and 2×10 grid; cursor/letter/END behaviour.
* `HMNFK`, `NXRFP`, `DWWFD` all accepted and all unlock Concert Mode, Video,
  and 5 songs. `HMNFK` was opened in Tour Book and shows 11 of 12 pictures;
  `NXRFP` and `DWWFD` decode to the same `k=11` mask (`0x7FF`).
* `THQSP` accepted; Video becomes selectable while Concert stays greyed and
  Tour Book remains empty.
* `WWHQV` accepted; Concert opens with 1 song, Tour Book shows 5 pictures,
  Video locked. Re-entering the password screen pre-fills `CTHQQ`.
* `JWHLJ` accepted; 3 pictures and 4 songs in Practice, Concert/Video locked.
* `WWHFT` accepted; full unlock.
* `WWHQB`, `ZZZZZ`, `BBBZD`, `XWBDL` rejected with “Incorrect Password !”.
* Menu walk: title, Mode Select (Dance/2-Player/Puzzle/Password/Options),
  Dance submenu (Practice/Concert/Tour Book/Video), song select, gameplay,
  pause (“Press START to Continue / A EXIT”), Tour Book, Video, 2-Player
  (“Communication Error / Main Menu”), Puzzle (“3X3” + 4 images), Options
  (Music Volume, SFX Volume, Difficulty Easy/Normal/Hard, Game Credits).

**Derived (instruction bytes):**

* Checksum, `X` split, `R` packing, `k` extraction, bit tests, and the fixed
  `THQSP` compare, at the addresses in §4.
* The encoder at `0x0800716C` and its call sites; its output matches the
  observed pre-filled codes.
* Only one Nintendo logo, one header, stock entry word → retail single image.

**Inferred (not fully proven):**

* `status0` bits 5–6 appear to be a concert/progress tier: `WWHQV` came back
  with bit5 set (`0x22`) and Concert unlocked with 1 song, while `THQSP`
  (`0x12`) left Concert locked. `k=11` codes also unlock Concert. The exact
  rule (“Concert opens at `k>=5`”, song count = `k+1` capped at 5) is
  consistent with all observations but was not isolated to one instruction.
* The 12th Tour Book cell is not reachable from any password (`k<=11` gives
  at most 11 set bits); it is presumably gated by gameplay/credits.
* The semantic meaning of `R`/`status1` is not proven; it selects the post-
  success screen path via its nibbles (`0x08001274`/`0x080012FC`) but the
  user-visible difference between the published codes was not found in menus.

## 8. Unknowns

* Why the published label says “12 pictures” when only 11 are set by the
  password masks; likely the 12th is a completion reward.
* Exact consumer of struct+22 vs struct+24 (two bitmasks are written; the
  Tour Book count tracks `k` and the Practice song count grows as `k+1`, but
  the split between the two masks is not isolated).
* Whether `status0` bits 5–6 are written by the menu layer or by the progress
  update routine; the observed values are recorded but the writer was not
  breakpointed to a single instruction after WWHQV.
* `R`'s gameplay meaning.
* No button-code system was found; see the negative bound below.

**Bounded negative results (no button/debug cheat):**

* Menu enumeration above found no debug/test/hidden screen and no extra entry
  point besides the one Password screen.
* ASCII scan of all 8 MiB: 120,629 printable runs ≥4 bytes; **0** occurrences of
  `password`, `cheat`, `debug`, `secret`, `unlock`, `gallery`, `jukebox`,
  `hidden`, `bonus`, `extra`, `sound`, `mode`, `song` (also 0 after the
  `0x61–0x7A → 0x41–0x5A` shift and in UTF-16LE). `music` and `test` occur only
  in the credits text (“Music Composer”, “Lead Tester”).
* Button-mask scan: searched the ROM as u16/u8/u32 for Konami
  (Up Up Down Down Left Right Left Right B A and A/B variant), Up Down Up Down
  B A, Select+Start, A B A B, L R L R, Up+Start — **0** hits for the sequences.
  A broader scan for runs of 3+ distinct button masks found only animation/
  curve data and gameplay input tables (`0x0837CDD8` is the A/B + direction
  move table, not a cheat). The Konami sequence was also entered on Mode
  Select: it only moved the cursor and opened Dance Mode.
* Only **one** 5-byte literal is compared by the password validator
  (`0x0837CF34`); there is no second hard-coded code table.

## 9. Tooling

* `mgba` 0.10.5 SDL (`/usr/games/mgba`) with `Xvfb :213` + `openbox`,
  `SDL_AUDIODRIVER=dummy`; `xdotool` for keys, `import` for window captures.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* `gdb-multiarch` against mGBA's GDB stub (`-g`, port 2345) for RAM reads and
  a read watchpoint on `0x03002C40`; the watchpoint is what located the
  validator (`0x08006FB4`).
* Python 3 model/encoder/enumerator: `/tmp/opencode/britney/britney_pw.py`.
* Screenshots: `/tmp/opencode/britney/shots/`.
* No ROM or game assets are redistributed here; only addresses, hashes,
  algorithms, and self-generated codes are published.

## 10. Legal note

Only the ROM image supplied in this workspace was inspected. No ROM, music,
graphics, or game text is reproduced in this report. The codes and algorithm
are the analyst's own reimplementation.
