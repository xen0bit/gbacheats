# Caesars Palace Advance: Millennium Gold Edition (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Caesars Palace Advance: Millennium Gold Edition.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `CAESARPALACE` (0xA0–0xAB) |
| Game code | `ACPE` (0xAC–0xAF) |
| Maker code | `5G` (0xB0–0xB1) |
| Software version | 0x00 (0xBC) |
| Complement check | 0x67 (0xBD) — correct for bytes 0xA0–0xBC |
| Header checksum | 0x0000 (0xBE–0xBF) — zero, the usual artifact of a rebuilt header; complement byte is valid |
| Entry word | `0xEA00002E` (branch to 0x080000C0; stock, not a cracktro branch) |
| MD5 | `ce1b62b6673b0e4338fda5bcdd1e2366` |
| SHA-1 | `cd5dbb8b8361ca5d003ec496a99351020dabc329` |
| SHA-256 | `0695b3f7de3c995240d1d2063df7054588351dd7e053c17efa94671fc1730dff` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at file offset `0x4`
(header `0x0`). There is no second image, no concatenated pack, no multiboot stub, and no
appended trainer. The first 4 KiB is ordinary ARM/Thumb crt0 + startup code
(`0x080000C0` ARM, Thumb from `0x080001D0`); no cracktro strings. This is a single, unpatched
8 MiB image.

## 2. Executive summary

The game has **one real code surface** — the lobby's **Password** screen — and it contains two
independent developer-intended systems:

1. **A 13-symbol state password** over a 64-symbol alphabet. It encodes three little-endian
   base-64 fields: **money (24 bits), credit (18 bits), debt (18 bits)**, plus three 6-bit
   checksums (one per 18-bit group and one global). The format has **2^60** representable
   states and is fully algorithmic; it is not a lookup table. We reversed the encoder/decoder
   completely (all four published passwords re-encode byte-for-byte and all four were entered
   in mGBA, along with several minted codes).
2. **Two hidden developer-photo codes** on the same screen: `KB2FVP` (photo 1) and `K2SMN`
   (photo 2). Each displays a full-screen LZ77-compressed 240×160 photograph and returns to
   the lobby. They are not in any published cheat list and are not documented on TCRF.

The "constant middle" of the four published money passwords (`v#dbbbxb`) is **not** a
signature or a fixed salt. It is the encoding of the default starting state
(credit `$10,000`, debt `$0`), which every published code shares. Once the credit/debt fields
are understood, the published list is a tiny slice of the real space.

Money endpoints are also developer-intended: `$0` shows “You're broke! Maybe you'll have
better luck next time.”; money **≥ $10,000,000** shows “You're a billionaire — Time to
retire!”. `$9,999,999` does not trigger it. The published GameFAQs “millionaire above
$1,000,000” tip was **not** reproduced at `$1,000,000` or `$1,000,001`.

## 3. How to reproduce

### 3.1 Emulator

* mGBA 0.10.5 (`/usr/games/mgba`), SDL frontend, under `Xvfb :225` + `openbox`.
* `SDL_AUDIODRIVER=dummy`.
* Default mGBA keymap used: **A = x**, **B = z**, **Start = Return**,
  **Select = BackSpace**, d-pad = arrow keys.
* Hold keys ~80–120 ms; the password grid can double-step if a direction is held too long.

### 3.2 Boot and menu path

1. Two Interplay legal screens: press **Start** twice.
2. Majesco and Pipe Dream logos play automatically.
3. Title screen: press **A**.
4. `Player Sign In` name entry: press **A** to accept the default name `Player`.
5. Lobby (six panels): **Blackjack, Cashier, Slot Machines** (top row), **Table Games,
   Password, Video Games** (bottom row).
6. From a fresh boot the cursor is on Cashier; **Down, Down, A** opened Password in repeated
   runs. After visiting other panels the cursor may be elsewhere, so verify the highlighted
   panel before pressing A.

Menu tree actually walked (all reachable screens):

* **Blackjack** — table screen (`Player Money: $…`, STAND / HIT / DOUBLE during a hand).
* **Cashier** — ATM screen showing `Player`, `Debt`, `Credit`, keypad, Borrow / Repay / Exit,
  plus a “Table Limit is $…” banner. The limit scales with money: `$100` at `$2,000`,
  `$1,000` at `$1,000,000`.
* **Slot Machines** — slot-machine selection (themed machines, first one “HALLOWEEN SPOOKY”).
* **Table Games** — submenu: **Craps**, **Roulette** (both tables reached).
* **Video Games** — submenu: **Video Poker**, **Video Keno**.
* **Password** — the 13-slot entry screen (see below).
* **Player Sign In** — A–Z / 0–9 name entry (label field only; not compared as a code).

No Options/Audio menu, no VIP/high-roller room, and no debug menu exist in the lobby tree.
“High roller” is represented only by the money-scaled table limit. The `Select an Option:`
string at `0x13CFAE` belongs to the Cashier loan submenu (Borrow/Repay/Debt/Credit).

### 3.3 Password entry

The keyboard is a 4-row grid; **Select toggles two 32-key pages**:

```
page 1 (values 32..63)          page 2 (values 0..31)
B C D F G H J K L               b c d f g h j k l
M N P Q R S T V W               m n p q r s t v w
X Y Z 0 1 2 3 4 5               x y z < = > ? % /
6 7 8 9 !                       + # @ - &
```

A types the highlighted key, d-pad moves (columns wrap/clamp; row 3 has only five keys),
**OK** at the bottom-right submits. The screen pre-fills the 13-byte buffer; on a fresh boot
the bytes are `v&bbv#dbbbxbF`, which decodes to `$2,000 / $10,000 / $0`.

### 3.4 Published codes tested

| Published effect | Password | Source | In-game result |
|---|---|---|---|
| Start with $5,900 | `q#cbv#dbbbxbM` | GameFAQs, SuperCheats, PlanetCheats | **Accepted**, Player `$5900`, Credit `$10000`, Debt `$0` |
| Start with $16,305 | `W9fbv#dbbbxbB` | same | **Accepted**, Player `$16305` |
| Start with $527,000 | `?Nbdv#dbbbxbs` | same | **Accepted**, Player `$527000` |
| Start with $8,527,030 | `1XCBv#dbbbxbM` | GameFAQs | **Accepted**, Player `$8527030` |

All four are reproduced exactly by the encoder in §5 (uppercase/lowercase are significant).
The only other published “cheat” (roulette negative-bet overflow) is a gameplay bug, not a
code, and is out of scope here.

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`) unless marked RAM.

| Item | File offset | Address | Notes |
|---|---:|---|---|
| Password keyboard renderer | 0x1578 | 0x08001578 | Uses both 32-char page tables; writes display bytes at `0x03005230+` |
| Hidden-code comparisons | 0x1960–0x19AA | 0x08001960–0x080019AA | Immediate `cmp` against `K,B,2,F,V,P` and `K,2,S,M,N` |
| 13-symbol decode / validate | 0x19BC–0x1B40 | 0x080019BC–0x08001B40 | Reads 13 bytes at `0x03005230`, writes decoded fields |
| Hidden-photo routine | 0x1BE4 | 0x08001BE4 | Selects image by flag at `0x03004010`; calls LZ77 decompressor |
| Page-2 alphabet (32 bytes) | 0x976ED | 0x080976ED | `bcdfghjklmnpqrstvwxyz<=>?%/+#@-&` |
| Page-1 alphabet (32 bytes) | 0x97712 | 0x08097712 | `BCDFGHJKLMNPQRSTVWXYZ0123456789!` |
| ASCII→6-bit table (256 bytes) | 0x97737 | 0x08097737 | Entry for each allowed ASCII char = 0..63 |
| Photo 1 (LZ77) | 0x8636C | 0x0808636C | Header `10 00 2C 01`: size 0x12C00 = 240×160×2 bytes |
| Photo 2 (LZ77) | 0x76104 | 0x08076104 | Same header/size |
| Input buffer (RAM) | — | `0x03005230` | 13 ASCII bytes, NUL padded |
| Input buffer mirror (RAM) | — | `0x0201DA30` | Observed in savestate at state offset 0x1E230 |
| Input length (RAM) | — | `0x03005180` | u16; `>12` decodes, `≤7` allows hidden codes |
| Hidden-code flag (RAM) | — | `0x03004010` | 1 = KB2FVP, 2 = K2SMN |
| Decoded money (RAM) | — | `0x03004030` | 32-bit store of 24-bit value |
| Decoded credit (RAM) | — | `0x03003544` | 32-bit store of 18-bit value |
| Decoded debt (RAM) | — | `0x03003498` | 32-bit store of 18-bit value |
| Decode scratch sums (RAM) | — | `0x030050BC` | u16 group accumulator |

The validator reads the **IWRAM** copy at `0x03005230`; a mirror of the entered ASCII appears
in EWRAM at `0x0201DA30` (verified by searching an mGBA savestate for the typed code).

## 5. Algorithm

### 5.1 Symbol values

Every input byte is translated through the 256-byte table at `0x08097737`. The 64 legal
symbols map to:

| Value | Characters |
|---|---|
| 0–20 | `b c d f g h j k l m n p q r s t v w x y z` |
| 21–31 | `< = > ? % / + # @ - &` |
| 32–52 | `B C D F G H J K L M N P Q R S T V W X Y Z` |
| 53–62 | `0 1 2 3 4 5 6 7 8 9` |
| 63 | `!` |

(Vowels are absent by design; case is significant.)

### 5.2 Decode (reimplementation)

```python
v = [table[c] for c in code]          # 13 values, each 0..63

if len(v) != 13: reject
if (v[4] + v[5] + v[6] + v[10]) & 63: reject    # group B checksum
if (v[7] + v[8] + v[9] + v[11]) & 63: reject    # group C checksum
if (sum(v[0:10]) + v[12]) & 63: reject          # global checksum

money  = v[0] | v[1]<<6 | v[2]<<12 | v[3]<<18   # 24-bit
credit = v[4] | v[5]<<6 | v[6]<<12              # 18-bit
debt   = v[7] | v[8]<<6 | v[9]<<12              # 18-bit
```

On success the ROM stores money/credit/debt to `0x03004030` / `0x03003544` / `0x03003498`,
calls `0x08002E00(6)` (screen change) and returns to the lobby. On any checksum failure it
plays sound `0x24`, clears the buffer and returns to the lobby **silently** (no error text).

### 5.3 Encode (reimplementation)

```python
d0 =  money        & 63
d1 = (money >> 6)  & 63
d2 = (money >> 12) & 63
d3 = (money >> 18) & 63
c0 =  credit       & 63
c1 = (credit >> 6) & 63
c2 = (credit >> 12)& 63
e0 =  debt         & 63
e1 = (debt >> 6)   & 63
e2 = (debt >> 12)  & 63

v10 = (-(c0 + c1 + c2)) & 63
v11 = (-(e0 + e1 + e2)) & 63
v12 = (-(d0 + d1 + d2 + d3 + c0 + c1 + c2 + e0 + e1 + e2)) & 63

code = alphabet[d0,d1,d2,d3,c0,c1,c2,e0,e1,e2,v10,v11,v12]
```

This encoder reproduces all four published codes and the in-game pre-fill exactly. The
apparent “fixed” middle `v#dbbbxb` is simply `credit = 10000`, `debt = 0`
(`c=[16,28,2]`, `e=[0,0,0]`), with `v10=18`, `v11=0`.

### 5.4 Hidden-code branch

Before the 13-symbol decode, the handler checks the buffer when its length is `≤7`:

* if `buf[0]=='K'` and `buf[1..5] == "B2FVP"` → hidden-code flag 1;
* if `buf[0]=='K'` and `buf[1..4] == "2SMN"` → hidden-code flag 2.

If a flag is set and length `≤7`, it calls `0x08001BE4`, which LZ77-decompresses the selected
photo to `0x02000A00`, displays it as a full-screen 240×160 image and waits for a button.
The exact codes are **`KB2FVP`** and **`K2SMN`**. Because only the prefix is compared and the
length gate allows 5–7 characters, entries with extra trailing characters (e.g. `KB2FVPx`,
`K2SMNxx`) follow the same branch (**derived**; the exact 5/6-character forms were entered).

## 6. Tables

### 6.1 Field layout (13 symbols, 78 bits used, 60 payload bits)

| Symbols | Width | Meaning | Evidence |
|---|---:|---|---|
| v0..v3 | 24 bits | money, base-64 little-endian | pre-fill `$2,000`; all published codes; minted `$1,000,000`, `$16,777,215` |
| v4..v6 | 18 bits | credit, base-64 little-endian | pre-fill `$10,000`; minted `$50,000`, `$12,345` |
| v7..v9 | 18 bits | debt, base-64 little-endian | pre-fill `$0`; minted `$1,104`, `$678` |
| v10 | 6 bits | `-(v4+v5+v6) mod 64` | disassembly; all inputs |
| v11 | 6 bits | `-(v7+v8+v9) mod 64` | disassembly; all inputs |
| v12 | 6 bits | `-(v0..v9 sum) mod 64` | disassembly; all inputs |

### 6.2 Verified published codes (decoded)

| Password | money | credit | debt |
|---|---:|---:|---:|
| `q#cbv#dbbbxbM` | 5,900 | 10,000 | 0 |
| `W9fbv#dbbbxbB` | 16,305 | 10,000 | 0 |
| `?Nbdv#dbbbxbs` | 527,000 | 10,000 | 0 |
| `1XCBv#dbbbxbM` | 8,527,030 | 10,000 | 0 |

### 6.3 Hidden codes

| Code | Length | Effect |
|---|---:|---|
| `KB2FVP` | 6 | full-screen photograph 1 (LZ77 block 0x0808636C) |
| `K2SMN` | 5 | full-screen photograph 2 (LZ77 block 0x08076104) |

## 6b. Enumeration

**Space definition.** Alphabet = 64 symbols, length = 13. The raw space is `64^13 = 2^78`.
Three independent mod-64 checks fix the last three symbols, so the accepted set is exactly
`2^60 = 1,152,921,504,606,846,976` codes, one per `(money, credit, debt)` triple with
`money < 2^24`, `credit < 2^18`, `debt < 2^18`. There are no reserved bits and no unused
payload bits; every 64-symbol character is legal. The hidden-code branch is a separate,
pre-decode 5–7 character namespace with exactly two entries (`KB2FVP`, `K2SMN`); the rest of
that namespace falls through to normal decode or rejection.

### Novel codes minted and confirmed in-game (none appear in any published list)

All were typed on the Password screen in mGBA and the resulting Cashier/ending screen was
captured.

| # | Password | Encoded state | Observed effect |
|---:|---|---|---|
| 1 | `bmZfv#dbbbxbx` | money 1,000,000; credit 10,000; debt 0 | Cashier: `Player $1000000`, `Debt $0`, `Credit $10000` |
| 2 | `bmZfvrqbbb>b>` | money 1,000,000; credit 50,000; debt 0 | Cashier: `Credit $50000` |
| 3 | `bmZfv#dvwbx&W` | money 1,000,000; credit 10,000; debt 1,104 | Cashier: `Debt $1104` |
| 4 | `W38d4bfJnbgvQ` | money 777,777; credit 12,345; debt 678 | Cashier: `Player $777777`, `Debt $678`, `Credit $12345` |
| 5 | `!!!!v#dbbbxb=` | money 16,777,215 (24-bit max); credit 10,000; debt 0 | accepted; “You're a billionaire — Time to retire!” |
| 6 | `b/mJv#dbbbxbm` | money 10,000,000 | accepted; billionaire/retire screen |
| 7 | `!%mJv#dbbbxbp` | money 9,999,999 | accepted; no ending; Cashier `Player $9999999` |
| 8 | `cmZfv#dbbbxbw` | money 1,000,001 | accepted; no ending; Cashier `Player $1000001` |
| 9 | `bbbbv#dbbbxbx` | money 0 (= 16,777,216 mod 2^24) | accepted; “You're broke!” screen |

The corresponding screenshots in the work directory are
`g5.png` (#1), `af2.png` (#2), `ab5.png` (#3), `aw4.png` (#4), `ae2.png` (#5),
`ac2.png` (#6), `ax1.png` (#7), `aj5.png` (#8), `ai3.png` (#9), plus
`al3.png` and `an3.png` for the two hidden photos. `ay1.png`, `bc_16305.png`,
`bc_527000.png`, `az1.png` are the four published-code confirmations.

### Bounds proven by rejection / endpoint tests

* **Wrong checksum → rejected.** `bmZfv#dbbbxbb` has the correct payload
  (money 1,000,000, credit 10,000, debt 0) and a global checksum off by one (`b` instead of
  `x`). The screen returned to the lobby silently and the Cashier still showed the loaded
  state's `$2,000` (`ah3.png`). The same happened for `bmZfv#dbbbxcw`, where a credit/debt
  symbol was changed without a compensating global checksum.
* **Middle symbols are payload, not a signature.** `bmZfv#dBbBxbx` changes two debt/credit
  symbols from `b` to `B` while keeping every checksum valid; it was **accepted** and produced
  `Player $1000000` with a changed debt (`aa3.png`). This is the differential test that proves
  there is no fixed “v#dbbbxb” literal check.
* **24-bit money field bound.** `16,777,216` cannot be represented; the same code as
  `money = 0` (`bbbbv#dbbbxbx`) is what the format produces after the 24-bit truncation. It
  was accepted and produced the `$0` / “You're broke!” ending (`ai3.png`). Money values
  `16,777,215` and `10,000,000` are accepted, so the field is full 24-bit width.
* **Semantic money threshold.** `$9,999,999` (`!%mJv#dbbbxbp`) is accepted and shows the
  normal Cashier (`ax1.png`); `$10,000,000` (`b/mJv#dbbbxbm`) triggers the retire ending
  (`ac2.png`). The threshold is therefore **≥ 10,000,000**.
* **Hidden-code exactness.** `?2SMN` (correct last four characters but no leading `K`) did
  **not** display a photo; it fell through and returned to the lobby. `K2SMN` displayed
  photo 2. The branch requires the leading `K` as well as the compared tail.

### Negative results, bounded

* `strings -t x -n 4` over the 8 MiB image (94,912 extracted runs) plus case-insensitive
  and `+0x20`-shifted searches found **zero** occurrences of `PASSWORD`, `PASSCODE`,
  `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `COMP`, `GALLERY`, `HIGH ROLLER`, and `VIP` in text
  (the 26 `VIP` byte hits are inside compressed graphics noise, not strings). The single
  `CODE` hit is the GAX audio banner at `0x756BE7` (“Shin'en Multimedia. Code: B.Wodok”),
  a false positive. The on-screen `Password` label is bitmap art, not ASCII — which is why a
  string search alone would have declared “no password screen”.
* Button-code scan: 52 candidate runs of ≥4 consecutive `u16` values drawn from the GBA
  key-mask set were found. Only one was referenced by a literal pointer (`0x08493E00`), and
  disassembly of its user (`0x080197D8`) shows it indexed by `[0x030036E8]*8` and used as
  sprite/parameter words, not a button sequence. No button-code validator exists in this ROM.
* Menu enumeration: every lobby panel and submenu listed in §3.2 was entered and screenshotted
  (Blackjack, Cashier, Slot selection, Craps, Roulette, Video Poker/Keno, Password, Player
  Sign In). No additional hidden/debug/VIP screen was reachable.

## 7. Validation evidence

### Observed (emulator / RAM)

* All four published codes accepted with the stated money; Cashier screenshots
  `ay1.png` ($5,900), `bc_16305.png` ($16,305), `bc_527000.png` ($527,000),
  `az1.png` ($8,527,030).
* Novel codes #1–#9 accepted with the exact money/credit/debt in §6b; the two hidden codes
  displayed full-screen photographs (`al3.png`, `an3.png`).
* Wrong-checksum code left money unchanged at `$2,000` (`ah3.png`).
* `$0` ending, `$10,000,000`/`$16,777,215` retire ending, and `$9,999,999` no-ending were
  observed.
* A savestate taken at the Password screen contains the typed 13-byte string at EWRAM
  `0x0201DA30` (state offset `0x1E230`), confirming the input buffer.

### Derived (instruction sequence)

* Field extraction and the three checksum equations are read directly from
  `0x080019BC–0x08001B40`; the `str` destinations are `0x03004030` (money), `0x03003544`
  (credit), `0x03003498` (debt).
* The 64-symbol alphabet and its value order come from `0x08097737`, with the two 32-char
  page strings at `0x080976ED`/`0x08097712`.
* The hidden-code comparisons are `cmp` immediates at `0x08001966–0x080019AA`; the photo
  routine is `0x08001BE4`; both photo blocks have a valid GBA LZ77 header (`0x10`) and a
  24-bit decompressed size of `0x12C00` (240×160×2).
* The encoder in §5.3 reproduces all published codes and the in-game pre-fill; the decoder
  agrees with every accepted and rejected input tested.

### Inferred

* The 5–7 character alias behavior of the hidden codes (extra trailing characters ignored)
  follows from the `cmp #7` length gate and the fixed-prefix comparisons; only the exact
  `KB2FVP` and `K2SMN` forms were entered.
* The debt display quirk at very large values (see §8) is a display/semantic overflow, not a
  checksum failure; the underlying 18-bit field decoded correctly.

## 8. Unknowns

* **Debt display overflow.** A code with `debt = 131,104` (`bmZfv#dBbBxbx`) was accepted and
  the Cashier displayed `Debt $-1104`. The 18-bit field decodes to 131,104; the displayed
  value is not a simple 16-bit truncation. The exact debt-display rule/cap was not isolated.
  Normal values (`0`, `678`, `1,104`) display 1:1.
* **Credit/debt semantic caps.** The fields are 18-bit in the password; the game may reject,
  clamp or mis-display values above its intended gameplay range. Only the values above were
  exercised.
* **The published “millionaire” tip.** GameFAQs says money above `$1,000,000` shows a
  millionaire message. This ROM did not do so at `$1,000,001`; only the `$10,000,000+`
  “billionaire” ending was observed. Whether a separate “millionaire” screen exists at an
  intermediate threshold is unresolved.
* **Save type.** mGBA created a 0-byte `game.sav`; the game's persistence appears to be the
  password system, but EEPROM/Flash saving was not exercised.
* **Photo subjects.** The two hidden images are photographs of people (presumably developers).
  They are documented as hidden content only; no attempt is made to identify them, and the
  images are not reproduced in this report.

## 9. Tooling

* `mgba` 0.10.5 (SDL), `Xvfb :225`, `openbox`, `xdotool`, `scrot`, ImageMagick `convert`.
* `arm-none-eabi-objdump` (binutils-arm-none-eabi) for Thumb disassembly;
  Capstone 5.0.7 for immediate/compare scans.
* Python 3 scripts in the work directory:
  * `type_code.py` — drives the 32-key grid from a text string (page toggle, cursor model,
    robust OK route). This was used for every code entry.
  * `gen.py` / inline encoder — the 13-symbol encoder/decoder (reproduces all published
    codes).
  * `rsp.py` — minimal GDB-remote client used for initial RAM checks.
  * Savestate parsing: mGBA `.ssN` is a PNG whose `gbAs` chunk is zlib-compressed; decompressed
    state was searched for the input buffer.
* Work directory: `/tmp/opencode/caesars` (screenshots and scripts; not part of the repo).

## 10. Legal note

No ROM, extracted graphics, music, or photographs are redistributed here. Only hashes,
addresses, algorithms, field layouts, and our own generated code strings are published.
