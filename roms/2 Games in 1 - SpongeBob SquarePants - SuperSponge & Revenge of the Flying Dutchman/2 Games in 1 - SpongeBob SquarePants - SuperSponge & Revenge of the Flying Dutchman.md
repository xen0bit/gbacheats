# 2 Games in 1 — SpongeBob: SuperSponge & Revenge of the Flying Dutchman (GBA) — RE Report

Report generated from a local ROM analysis on 2026-10-24; Revenge half completed
2026-10-26.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

Scope note: **in-game / developer-intended cheats only.**
GameShark/CodeBreaker/RAM-patch codes are out of scope.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/2 Games in 1 - SpongeBob SquarePants - SuperSponge & Revenge of the Flying Dutchman/2 Games in 1 - SpongeBob SquarePants - SuperSponge & Revenge of the Flying Dutchman.gba` |
| Size | 16 MiB (`0x1000000`) |
| Header title | `SBREVENGEGBA` |
| Game code | `BDFE` |
| Maker code | `78` |
| Software version | `0` |
| MD5 | `fa11be8d9b3e6a4851d8f4538922082a` |
| SHA-1 | `c7610e41fc97358f4fe156bfc0ef3a33e87c8a73` |
| SHA-256 | `21282fb783d2e0bb2d4bb8875a43d1ec54b4902b981a5eb11406311ac4bf4085` |

### Layout

| Range | Contents |
|---|---|
| `0x000000`–`0x7FFFFF` | Revenge of the Flying Dutchman image (8 MiB) |
| `0x800000`–`0xBD028B` | SuperSponge image (header `SBSP SS`, code `ASPE`) |
| `0xBD028C`–… | `MULTIGAME` loader (`XXXX`) |

The boot selector ("SPONGEBOB SQUAREPANTS REVENGE OF THE FLYING DUTCHMAN" /
"… SUPER SPONGE") is in the first image.

---

## 2. Executive summary

Both halves have password systems. Both are now fully reversed, reimplemented
offline, and exercised on the retail ROM.

### SuperSponge — table lookup (unchanged)

* Menu: `Start New Game / Enter A Password / Options Menu / Credits`.
* Codes are **4 characters** over `A–Z` (`Enter A Password`, `Invalid Password`).
* The game does **not** generate codes: it compares the 4 characters against a
  **20-entry plaintext table** and returns the entry index (0–19) as the level.
  Validator: `0x08814A60` (loops 20 pointers from `0x08A72AC4`, 4-byte compare,
  returns index or −1).
* Table: 20 records × 8 bytes at `0x081F25C`; pointers at `0x08A72AC0`
  (descending into the table).

Exact ROM codes (index 0 = first table entry):

```
0  WMBT    5  HGCD   10  QHDG   15  PFYJ
1  JRST    6  LXHK   11  HDJQ   16  WKGR
2  PYHS    7  QGRV   12  XNRP   17  KYNF
3  LKKV    8  MNTL   13  WMCY   18  CLMB
4  CNXK    9  WFXM   14  NGPS   19  BGNR
```

Several published lists differ by a character or two (`WMCV`, `DFVJ`, `QGAV`,
`HPJQ`, `XNAD`, `WKGA`, `KVNF`, `JAST`, `PVHS`); the ROM is authoritative.
There is no checksum — any string not equal to one of the 20 is rejected.

### Revenge of the Flying Dutchman — solved (30-bit packed state)

* **6 symbols**, alphabet `BCDFGHJKLMNPQRSTVWXYZ0123456789?` (32 symbols,
  `0x080D1E28`), **5 bits per symbol, little-endian**: symbol 0 is the low
  5 bits of the 30-bit value, symbol 5 the high 5 bits.
* The 30-bit value is a fixed **bit permutation** of three game-state words:
  an 18-bit progress word `W` (`0x030019E4`), a 10-bit item/treasure bitmap
  `H` (`0x030019E0`) and a 1-bit flag `B` (`0x030007D0`). Bit 15 of the code is
  a **reserved hole that must be 0**.
* **There is no additive checksum.** Validity is structural: `W` contains three
  5-bit *unary* progress groups (`W` bits 1–5, 6–10, 11–15), each of which must
  hold one of `{0,1,3,7,15,31}` (0–5 stages, filled in order), plus a marker bit
  `W0` that must be 1 whenever any group is non-zero.
* `?` is **not a wildcard**. It is the 32nd alphabet symbol (index 31 =
  `0b11111`), i.e. the *maximum* unary value of a group. It is drawn as its own
  cell on the on-screen keypad and the game's own encoder emits it whenever a
  group is full — which is why every published "all levels" code is full of
  question marks.
* Valid set: **1,777,664 codes** out of 32^6 = 1,073,741,824 (0.166 %).
* An unpublished code `H0X1J2` (all progress groups full, no treasures) was
  minted and accepted. It is confirmed three ways: the select-chapter hub opens
  with level entrances, the level-intro screen re-prints `H0X1J2` from the
  game's own encoder, and IWRAM after entry reads
  `W=0x0000FFFF H=0x0000 B=0x00`.
* Rejected in-game: `BBBBBH` (non-unary group), `BBBCBB` (reserved bit 15),
  `BBBBNN` (naive entry of a published 5-symbol code). See §6b.

---

## 3. How to reproduce

```bash
sudo apt-get install -y mgba-sdl mgba-qt xvfb xdotool imagemagick openbox
Xvfb :199 -screen 0 1024x768x24 &
DISPLAY=:199 openbox &
DISPLAY=:199 SDL_AUDIODRIVER=dummy /usr/games/mgba-qt -3 "2 Games in 1 - ....gba" &
```

`mgba` on Debian is `/usr/games/mgba`; `mgba-qt` adds savestates and
fast-forward, which makes repeated password tests cheap.

Keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad arrows.
`openbox` is required for key delivery; capture with
`import -window <wid> <png>`.

### Paths

```
Boot selector: default = Revenge, Right = SuperSponge, then A
SuperSponge: Nickelodeon logo -> title -> Start
  -> MAIN MENU: Start New Game / Enter A Password / Options Menu / Credits
  -> Down, A -> "Enter A Password" (4 slots, shows one symbol at a time)
Revenge:    Nickelodeon -> Vicarious Visions -> title -> Start -> attract demo
  -> Start -> MAIN MENU: New Game / Continue / Options
  -> Down, A (Continue with no save) -> 6-slot PASSWORD keypad
```

The Revenge keypad is an 8×4 grid of the alphabet in order:

```
row0  B C D F G H J K
row1  L M N P Q R S T
row2  V W X Y Z 0 1 2
row3  3 4 5 6 7 8 9 ?
```

D-pad moves the cursor (no wrap), A commits one symbol, B leaves the screen.
The six chosen symbols are drawn across the top; the sixth A commits the code.
Accepting a code leads to `SELECT CHAPTER`, where Left/Right walk the ring of
unlocked level entrances and A opens the level-intro card, which prints the
level name, `-LEVEL n-` (or `-FINAL LEVEL-`) and the **password the game
generates for the current state** — the single most useful verification screen.

Savestates used during this pass (mGBA Qt writes `<rom>.ssN` next to the ROM):
slot 1/3 = password keypad, slot 2 = main menu, slot 5 = level intro.

---

## 4. Address map

| ROM address | What |
|---:|---|
| `0x08814A60` | SuperSponge validator: 20-entry 4-char compare, returns index or −1 |
| `0x08A72AC0` | 20 pointers to the SuperSponge code strings (descending) |
| `0x081F25C` | SuperSponge code strings, 8-byte stride |
| `0x0801AA38` | Revenge encoder: state words → 30-bit value → 6 symbols |
| `0x0801AB80` | Revenge packer: 30-bit value in `r5` → 6 symbols at `*(0x03001954)` |
| `0x0801ABB8` | Revenge decoder/apply: 6 symbols → state words, returns 0/1/2 |
| `0x0801AEF4` | Encoder wrapper: `bl 0x0801AA38`, returns the code pointer |
| `0x08039EEC` | In-game code printer (pause/level card): sets `W|=0x20000`, encodes |
| `0x080D1E28` | Revenge alphabet `BCDFGHJKLMNPQRSTVWXYZ0123456789?` |
| `0x08020E94` | Password-screen call site: `bl 0x0801ABB8` on the 6-byte buffer |
| `0x08020C00`–`0x08021060` | Password keypad screen (6 slots; `cmp r3,#6` at `0x08020E8E`, validator call at `0x08020E94`) |
| `0x0802F72C` | `SELECT CHAPTER` hub scene builder |
| `0x0802E8F8`–`0x0802EA48` | Per-bit state query table: tests `W` bits and `H` item groups |
| `0x0800CE40`–`0x0800CED4` | Secret/bonus gate: requires `H` bits 1-3, 4-6, 7-9 all set |
| `0x0D2350` | Revenge `password:` string |
| `0x0D2AF0` / `0x0D2B08` | Revenge `select chapter` / `selectA`, `password` strings |
| `0x0D21DC`–`0x0D22AC` | The ten treasure names (matches the 10 `H` bits) |
| `0x0A783D0` | SuperSponge menu strings (`Start New Game`, `Enter A Password`, …) |

### RAM

| Address | Size | Contents |
|---|---:|---|
| `0x030019E4` | u32 | progress word `W` (18 bits used) |
| `0x030019E0` | u16 | item/treasure bitmap `H` (10 bits used) |
| `0x030007D0` | u8 | single flag `B` (only bit 0 is carried by the code) |
| `0x03001954` | 6 B + NUL | encoder output buffer (last generated code) |
| `0x03000664` | u32 | word compared against the decoded value for the "special" return-2 path |
| `0x0300074C` | u8 | set to 1 by the password screen when a code is accepted |

IWRAM lives at file-savestate offset `0x19000` inside the decompressed `gbAs`
chunk, so `0x030019E4` can be read straight out of a `.ssN`
(`0x19000 + 0x19E4`). That is how the novel code's fields were verified.

---

## 5. Algorithm

### 5.1 SuperSponge (`0x08814A60`, derived)

```c
int password_index(char in[4]) {
    static char *codes[20];          // 0x08A72AC4, table at 0x081F25C
    for (int i = 0; i < 20; i++)
        if (!memcmp(in, codes[i], 4)) return i;   // -> level index
    return -1;
}
```

No checksum, no arithmetic: the code space is exactly the 20 stored strings.

### 5.2 Revenge (`0x0801ABB8` decode, `0x0801AA38` encode, derived + observed)

```python
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0123456789?"     # 32 symbols

def value(code):                                # 0x0801ABB8 symbol loop
    v = 0
    for i, c in enumerate(code[0:6]):           # i = 0..5, LSB first
        v |= ALPHA.index(c) << (5 * i)          # unknown symbol -> index 255, fails the checks
    return v

def valid(v):                                   # 0x0801ABFE..0x0801AD28
    if (v >> 15) & 1: return False              # reserved bit
    W, H, B = split(v)                          # bit permutation, §6.3
    groups = ((W >> 1) & 31, (W >> 6) & 31, (W >> 11) & 31)
    if any(g not in (0, 1, 3, 7, 15, 31) for g in groups): return False
    if any(groups) and not (W & 1): return False    # marker bit
    return True

def apply(code):                                # what the ROM does on success
    v = value(code)
    if not valid(v): return 0                   # UI clears the buffer, stays
    W, H, B = split(v)
    *(u32*)0x030019E4 |= W                      # note: OR, bits are only set
    *(u16*)0x030019E0 |= H
    *(u8 *)0x030007D0  = B
    return 1

def encode(W, H, B):                            # 0x0801AA38 -> 0x0801AB80
    v = join(W, H, B)
    return "".join(ALPHA[(v >> (5 * i)) & 31] for i in range(6))
```

`0x0801ABB8` returns 0 (reject), 1 (accept, sets `0x0300074C`) or 2 when the
30-bit value equals the u32 at `0x03000664`. That word reads `0x1CF161A1`
(`≥ 2^30`) in every state sampled, so the comparison can never succeed for a
30-bit code: the return-2 path is effectively dead.

### 5.3 What the bits mean

`W` (18 bits) is a set of unlock flags. The game's own query table at
`0x0802E8F8`–`0x0802EA48` tests them one by one and in combinations:

| test | mask | reading |
|---|---|---|
| `0x0802E960` | `W & 1` | first-chapter flag |
| `0x0802E900`–`0x0802E998` | `W & 0x0002..0x4000` | twelve individual level/area unlocks |
| `0x0802E9A0` | `W & 0x20`, `0x400`, `0x8000` | "chapter complete" test — the top bit of each 5-bit group |
| `0x0802E9C8` | `W & 0x20000` | extra (bonus) unlock |
| `0x0802E9DC`–`0x0802EA48` | `H & 1`, `H & 0xE`, `H & 0x70`, `H & 0x380` | item groups |

So each 5-bit group is *four level flags plus a chapter-complete flag*, and the
unary constraint simply forces levels to be unlocked in order. The three groups
carry the chapter progression in the order the published lists use: the codes
published as "chapter 2" fill `W` bits 6–10, "chapter 3" fills 11–15, and
"chapter 4" fills 1–5 (§6.4).

`H` is a 10-bit item bitmap. The ROM lists exactly ten treasures
(`0x0D21DC`–`0x0D22AC`: medal of dishonor, 1st place bowling trophy, parrot
statue, ancient sword of enchantment, golden anchor from rock bottom, lucky
boxer shorts, special cup, Dutchman family photo album, peg leg, mermaid man
issue no. 1), and the bonus gate at `0x0800CE40` demands complete triples
(`H` bits 1-3, 4-6, 7-9) — a treasure-group completion test.

`B` is a single flag carried in bit 0 of `0x030007D0`. Published codes set it
only on the "all levels", "all bosses" and fan-wiki variants. It is **not** the
difficulty shown in the HUD: `9??925` (published "All Bosses Hard", `B=1`)
starts a level with `NORMAL` displayed, so the difficulty byte is a separate
variable set by the difficulty menu.

---

## 6. Tables

### 6.1 SuperSponge codes (ROM order)

| # | Code | # | Code |
|---:|---|---:|---|
| 0 | `WMBT` | 10 | `QHDG` |
| 1 | `JRST` | 11 | `HDJQ` |
| 2 | `PYHS` | 12 | `XNRP` |
| 3 | `LKKV` | 13 | `WMCY` |
| 4 | `CNXK` | 14 | `NGPS` |
| 5 | `HGCD` | 15 | `PFYJ` |
| 6 | `LXHK` | 16 | `WKGR` |
| 7 | `QGRV` | 17 | `KYNF` |
| 8 | `MNTL` | 18 | `CLMB` |
| 9 | `WFXM` | 19 | `BGNR` |

### 6.2 Revenge alphabet

```
index: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
char:  B  C  D  F  G  H  J  K  L  M  N  P  Q  R  S  T
index:16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31
char:  V  W  X  Y  Z  0  1  2  3  4  5  6  7  8  9  ?
```

`?` (31) is the maximum unary value, not a wildcard.

### 6.3 Revenge bit layout

Symbol `i` holds value bits `5i+4 .. 5i`. The 30 bits permute into the state
words as follows (`val` bit → RAM bit):

| `val` bits | → | word |
|---|---|---|
| 0, 2, 3, 5, 7, 9, 11, 14, 16, 17, 19, 21, 22, 23, 25, 26, 27, 29 | → | `W` bits 10, 3, 17, 2, 14, 9, 7, 8, 6, 13, 11, 4, 12, 16, 5, 0, 15, 1 |
| 1, 4, 6, 8, 10, 13, 18, 20, 24, 28 | → | `H` bits 5, 4, 7, 8, 3, 2, 6, 9, 1, 0 |
| 12 | → | `B` bit 0 |
| 15 | → | reserved, must be 0 |

The inverse map is what the encoder at `0x0801AA38` uses; the two functions are
exact inverses (`encode(decode(c)) == c` for all 1,777,664 valid values).

Field table:

| Field | Bits | Range | Meaning |
|---|---|---|---|
| `W` bit 0 | 1 | 0/1 | first-chapter flag; must be 1 if any group is non-zero |
| group A | `W` 1–5 | unary 0…5 | four level unlocks + chapter-complete (published "chapter 4") |
| group B | `W` 6–10 | unary 0…5 | four level unlocks + chapter-complete (published "chapter 2") |
| group C | `W` 11–15 | unary 0…5 | four level unlocks + chapter-complete (published "chapter 3") |
| `W` 16–17 | 2 | 0…3 | extra unlock flags used by the "all levels"/"all bosses" codes |
| `H` | 10 | 0…1023 | ten treasure/item flags |
| `B` | 1 | 0/1 | extra flag (set on all-levels/all-boss/wiki-family codes) |

### 6.4 Published codes decoded

`A,B,C` are the three unary groups as *encoded* values; subtract 1 to get the
number of stages (0,1,3,7,15,31 → 0,1,2,3,4,5). `free` = `W` bits 16–17.

| Code | Published effect | A,B,C | mark | free | `H` | `B` |
|---|---|---|---:|---:|---:|---:|
| `BBBBBB` | Ch1 L1 (published as 5 chars `BBBBB`) | 0,0,0 | 0 | 0 | `0x000` | 0 |
| `BBBBBN` | Ch2 L1 (published as 5 chars `BBBBN`) | 0,0,0 | 1 | 0 | `0x001` | 0 |
| `VBBDBN` | Ch2 L2 | 0,1,0 | 1 | 0 | `0x011` | 0 |
| `XBXDBN` | Ch2 L3 | 0,7,0 | 1 | 0 | `0x031` | 0 |
| `VVXNBN` | Ch3 L1 | 0,15,0 | 1 | 0 | `0x051` | 0 |
| `VXX5BN` | Ch3 L2 | 0,15,1 | 1 | 0 | `0x0D1` | 0 |
| `V5X9GN` | Ch3 L3 | 0,15,7 | 1 | 0 | `0x1D1` | 0 |
| `V9X9HS` | Ch4 L1 | 0,15,31 | 1 | 0 | `0x3D1` | 0 |
| `V9X909` | Ch4 L2 | 1,15,31 | 1 | 0 | `0x3D3` | 0 |
| `2?5909` | Ch4 L3 | 7,31,31 | 1 | 0 | `0x3F7` | 0 |
| `V9X9HN` | Boss: Alaskan Bullworm | 0,15,15 | 1 | 0 | `0x3D1` | 0 |
| `XVXNBN` | Boss: Plankton | 0,15,0 | 1 | 0 | `0x071` | 0 |
| `2?6929` | Boss: Wild Jellyfish | 15,31,31 | 1 | 0 | `0x3FF` | 0 |
| `V5X5GN` | Bonus: Kara-tay | 0,15,3 | 1 | 0 | `0x1D1` | 0 |
| `XBDDBN` | Bonus: Krabby Patty | 0,3,0 | 1 | 0 | `0x031` | 0 |
| `V?5909` | Bonus: Jellyfish roundup | 3,15,31 | 1 | 0 | `0x3D7` | 0 |
| `9??99?` | All levels except Bullworm | 31,15,31 | 1 | 3 | `0x1FF` | 1 |
| `???91?` | All levels (Easy) | 31,31,31 | 1 | 2 | `0x1FF` | 1 |
| `???92?` | All levels (Hard) | 31,31,31 | 1 | 2 | `0x3FF` | 1 |
| `9??925` | All bosses (Hard) | 15,15,15 | 1 | 2 | `0x3FF` | 1 |
| `9?6925` | All bosses (Normal) | 15,15,15 | 1 | 2 | `0x3FF` | 0 |
| `??692?` | Final level (Normal) | 31,31,31 | 1 | 2 | `0x3FF` | 0 |
| `QCRBX6` | Fan-wiki Ch3 L1 | 31,0,0 | 1 | 2 | `0x00F` | 1 |
| `QFRVX6` | Fan-wiki Ch3 L2 | 31,0,1 | 1 | 2 | `0x08F` | 1 |
| `QPRZ16` | Fan-wiki Ch3 L3 | 31,0,7 | 1 | 2 | `0x18F` | 1 |
| `QTRZ2?` | Fan-wiki Ch4 L1 | 31,0,31 | 1 | 2 | `0x38F` | 1 |
| `7TR12?` | Fan-wiki Ch4 L2 | 31,1,31 | 1 | 2 | `0x39F` | 1 |

Every one of these 27 published strings passes the offline validator, and every
one that was typed into the ROM was accepted (§7, §6b).

---

## 6b. Enumeration

### Space

| Quantity | Value |
|---|---|
| Alphabet | 32 symbols (`BCDFGHJKLMNPQRSTVWXYZ0123456789?`) |
| Length | 6 |
| Raw space | 32^6 = 2^30 = **1,073,741,824** |
| Reserved-bit-15 survivors | 2^29 = 536,870,912 |
| **Valid codes** | **1,777,664** (0.166 % of raw, 0.331 % of bit-15-clean) |

The valid count is exact, not sampled. It follows from the layout and was
confirmed by exhaustive construction:

```
(2 + (6^3 - 1))   marker/group combinations (all-zero groups allow either marker)
      x 2^2       W bits 16..17
      x 2^10      H bitmap
      x 2         B flag
= 217 x 4 x 1024 x 2 = 1,777,664
```

A Python enumeration of that product produced exactly 1,777,664 distinct values,
all accepted by the validator, all round-tripping through `encode(decode(v))`,
and a 300,000-sample uniform draw over 32^6 passed 474 times (0.158 %),
consistent with the model within sampling noise.

### Novel code (not in any published list)

`H0X1J2` — all three progress groups full, **zero** treasures, `B=0`:

```
H0X1J2  ->  val 0x2E6B4AA5  ->  W = 0x0000FFFF, H = 0x0000, B = 0
```

No published list contains a code with all groups saturated and `H = 0`
(every published "all levels" code carries `free = 2/3` and `H ≥ 0x1FF`).

Observed on the retail ROM:

1. Entered on the 6-slot keypad, the code is accepted and the
   `SELECT CHAPTER` hub appears with level entrances beyond the single one a
   fresh `BBBBBB` state offers (`hub_novel_H0X1J2.png` vs
   `hub_allzero_BBBBBB.png`).
2. Opening a level shows `GARY, COME HOME!` / `-LEVEL 1-` and the game's own
   encoder prints **`H0X1J2`** on the level card (`novel_H0X1J2_intro_echo.png`).
   The ROM therefore decodes the string to state and re-encodes the same state
   back to the identical string — a full round-trip through the real codec.
3. Reading IWRAM out of a savestate taken on that card gives
   `0x030019E4 = 0x0000FFFF`, `0x030019E0 = 0x0000`, `0x030007D0 = 0x00`,
   exactly the fields the offline decoder predicts. The encoder's output buffer
   `0x03001954` holds `"H0X1J2"`.

A second novel value, `XNMLWL` (`W=0`, `H=0x3FF`, `B=0` — every treasure, no
level progress), is also accepted and reaches the hub
(`treasures_XNMLWL_hub.png`), confirming `H` is independently settable.

### Bounds proven by rejection

| Input | Model verdict | In-game result | Screenshot |
|---|---|---|---|
| `BBBBBH` | counter A = 16, not unary | buffer cleared, stays on keypad | `reject_BBBBBH_cleared.png` |
| `BBBCBB` | reserved bit 15 set | buffer cleared, stays on keypad | `reject_BBBCBB_cleared.png` |
| `BBBBNN` | counter A = 8, not unary | buffer cleared, stays on keypad | `reject_pub5_BBBBNN_cleared.png` |

`BBBBNN` is the bound that also proves the published-list defect: the lists
give `BBBBN` as a *five*-symbol code, but the screen has six slots, so a player
who types five symbols and commits produces `BBBBNN`, which the ROM rejects.
The six-symbol form `BBBBBN` is accepted and lands on chapter 2's first level
(`SPECIAL DELIVERY`, `-LEVEL 1-`), which is exactly the effect the lists
advertise for `BBBBN` (`pub_BBBBBN_ch2_special_delivery.png`). The same holds
for `BBBBB` → `BBBBBB` (chapter 1, `GARY, COME HOME!`).

### Published-code behaviour observed in the ROM

| Code | Observed |
|---|---|
| `BBBBB`/`BBBBBB` | hub, chapter 1 only; one level entrance |
| `BBBBN`/`BBBBBN` | chapter 2, `SPECIAL DELIVERY`, `-LEVEL 1-` |
| `VBBDBN` | `WALKING THE PLANKTON` hub, `SPECIAL DELIVERY`, `-LEVEL 1-` |
| `V9X9HS` | `OUT AND ABOUT` hub, `CLAMBAKE`, `-LEVEL 1-` |
| `2?5909` | accepted, hub with chapters 1/2/bonus/3/4 |
| `???91?` | accepted, `ROLL OUT THE BARREL`, **`-FINAL LEVEL-`** |
| `9??925` | accepted, starts a level with `NORMAL` in the HUD |

`???91?` is the cleanest proof that `?` is a literal symbol: the game prints
`???91?` back on the level card, i.e. it *generated* the question marks itself
from a state whose three groups are saturated (`W = 0x2FFFF`, `H = 0x1FF`,
`B = 1`, read back from IWRAM).

Note on the published chapter numbers: the lists' "chapter 2/3/4" labels are
offset by one relative to the game's own chapter banners (a code the lists call
"Chapter 2, Level 2" opens the `WALKING THE PLANKTON` hub at its first level).
The bit layout above is unaffected; only the human labels disagree.

---

## 7. Validation evidence

**Observed (emulator)**
- SuperSponge main menu contains `Enter A Password`; entry screen shows 4 slots
  and cycles symbols (`B` → `9` observed).
- Revenge keypad is 8×4, 6 slots, exactly the 32-symbol alphabet plus `?`.
- `BBBBBB` → chapter 1 (`GARY, COME HOME!`, `-LEVEL 1-`).
- `BBBBBN` → `SPECIAL DELIVERY`, `-LEVEL 1-` (published `BBBBN`, chapter 2 L1).
- `???91?` → `ROLL OUT THE BARREL`, `-FINAL LEVEL-`, code re-printed as `???91?`.
- `H0X1J2` → hub with all entrances, code re-printed as `H0X1J2`.
- `BBBBBH`, `BBBCBB`, `BBBBNN` → entry cleared, still on the keypad.
- IWRAM after `H0X1J2`: `0x030019E4=0x0000FFFF`, `0x030019E0=0x0000`,
  `0x030007D0=0x00`; after `???91?`: `0x0002FFFF`, `0x01FF`, `0x01`.
- `9??925` starts a level showing `NORMAL`.

**Derived (disassembly)**
- SuperSponge validator is a pure 20-entry table compare returning the index.
- Revenge codec: 5 bits per symbol, LSB first; bit-permuted into `W`/`H`/`B`;
  reserved bit 15; three unary groups; marker bit; no additive checksum.
- The game's own state query table (`0x0802E8F8`) tests those exact bits,
  including "chapter complete" as the top bit of each group.
- Encoder `0x0801AA38` and decoder `0x0801ABB8` are exact inverses.

**Inferred**
- Group↔chapter assignment. The published chapter-2/3/4 runs each advance one
  group (B, C, A respectively), which is the basis for the labels in §6.3. The
  hub cannot isolate a single group — its ring is count-driven, so a one-bit
  test such as `BBBBBX` (`W=3`) also shows chapter 2's banner — therefore the
  per-group chapter name rests on the published-code correlation, not on a
  one-group-at-a-time visual test.
- `H` bit→treasure identity is inferred from the ten treasure strings and the
  3-bit group checks; individual bits were not matched to individual names.

---

## 8. Unknowns

Nothing about the *format* is open: alphabet, length, packing, field layout,
validity rule, `?` semantics, valid-set size, a novel accepted code and three
rejections are all established above.

Remaining bounded gaps, stated so they are not mistaken for open questions:

- `B` (`0x030007D0` bit 0) and `W` bits 16–17 are carried by the code but no
  published code isolates them, so their in-game labels are unproven. `B` is
  **not** the HUD difficulty (proven: `9??925`, `B=1`, shows `NORMAL`).
- Per-bit treasure names in `H` were not mapped individually (the group
  structure and the ten names are proven; the 1:1 order is not).
- The `return 2` path at `0x0801ABB8` compares against `0x03000664`, which is
  `0x1CF161A1` (≥ 2^30) in every sampled state and therefore unreachable for a
  30-bit code. It is reported as dead, not as a feature.
- SuperSponge per-symbol entry semantics (A/B behaviour) were not fully mapped;
  the code table itself is complete and authoritative.
- The MULTIGAME loader's role (link-play menu) was not examined.

---

## 9. Tooling

| Method | Purpose |
|---|---|
| header/logo scan | split the 16 MiB image into the two games + loader |
| `grep -abo` | found the SuperSponge code table and the Revenge alphabet |
| literal-pointer search | located the SuperSponge validator through its pointer table |
| Thumb disassembly (`arm-none-eabi-objdump -M force-thumb`) | validator, encoder, decoder, state query table |
| mGBA Qt + Xvfb/openbox + xdotool | keypad entry, hub/level-card screenshots, savestates |
| savestate PNG `gbAs` chunk (zlib) | raw IWRAM dump to confirm decoded fields |
| Python codec + exhaustive enumeration | `rev_codec.py`, 1,777,664 valid codes constructed and round-tripped |

`rev_codec.py` (kept at `/tmp/opencode/spongebob/rev_codec.py` during the
session) implements `symbols_to_val`, `split`, `join`, `check`, `decode`,
`encode` and reproduces every published code and every rejection above:

```python
VAL2W = {0:10, 2:3, 3:17, 5:2, 7:14, 9:9, 11:7, 14:8, 16:6, 17:13,
         19:11, 21:4, 22:12, 23:16, 25:5, 26:0, 27:15, 29:1}
VAL2H = {1:5, 4:4, 6:7, 8:8, 10:3, 13:2, 18:6, 20:9, 24:1, 28:0}
VAL2B = {12:0}
UNARY = (0, 1, 3, 7, 15, 31)
```

Screenshots referenced by name in §6b/§7 were captured to
`/tmp/opencode/spongebob/shots/` during the session
(`pw_screen.png`, `hub_allzero_BBBBBB.png`, `hub_novel_H0X1J2.png`,
`novel_H0X1J2_intro_echo.png`, `pub_BBBBBN_ch2_special_delivery.png`,
`pub_???91?_final_level.png`, `reject_BBBBBH_cleared.png`,
`reject_BBBCBB_cleared.png`, `reject_pub5_BBBBNN_cleared.png`,
`pub_9??925_gameplay_normal.png`, `treasures_XNMLWL_hub.png`).

No ROM, graphics, or text from the games is redistributed here; only addresses,
algorithms, and short identifiers needed to describe the passwords.
