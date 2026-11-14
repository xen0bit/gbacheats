# Desert Strike Advance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Desert Strike Advance.gba` (4,194,304 bytes / 4 MiB) |
| Header title | `DESERTSTRIKE` |
| Game code / maker | `ADIE` / `69` (Electronic Arts) |
| Software version | `00` |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| Complement check | stored `0x36`; recomputed `0x36` (valid) |
| Header checksum field (`0xBE`) | `0x0000` |
| MD5 | `171e7bdf6b194cc9ae301f5424714a1a` |
| SHA-1 | `9fd7e323cfa2eebf5b01467ded6c96a0a2219bdf` |
| SHA-256 | `88a788d084770f38c9d6e5bfb9ae4beafbbbe37bf96cca3a4296e31351d0ebf3` |
| CRC32 | `0xCC1C1405` |

No trainer, cracktro or appended data: the entry word is the stock branch, the
Nintendo logo is present once at `0x0004`, the file ends in zero padding, and
the only non-game fill is the linker pattern `budcat01` (Budcat Creations, the
GBA port developer) from file `0x200000` onward. The `0xBE` field being zero is
a build artifact; the complement byte at `0xBD` is self-consistent, which is the
better "header edited" signal.

**Key structural finding:** the ROM contains a complete 2 MiB Super NES game
image at file offset `0x200000` (GBA address `0x08200000`). Its HiROM-style
header is at image offset `0x00FFC0` (file `0x20FFC0`) with the title
`DESERT STRIKE`. Addresses inside that image are plain image offsets, so an
image address `$02AC6B` is file `0x22AC6B` = GBA `0x0822AC6B`. The password
logic below is 65C816 code in that image; the GBA port reproduces it and keeps
the original low-RAM variable layout at EWRAM base `0x02000000` (verified by
savestate: the entered password buffer sits at `0x020009DA`).

## 2. Executive summary

Desert Strike Advance has a **7-character, 26-symbol password system**, reached
by holding **A** on the main menu (`CAMPAIGN MENU / ENTER PASSWORD`). The
alphabet is not A–Z/0–9; it is the permuted table

```
ZQMTH3L2J8RKBW94FP5SCNGX7D
```

Characters are selected with Up/Down, the cursor moves with Left/Right, and
**Start submits**. The seventh character is not auto-computed; it is an
editable checksum symbol.

A submission is accepted if either

1. it equals one of **four hard-coded special codes** (`B84GT7S`, `B74GT7S`,
   `BS9JS27`, `GTSTFTC`), or
2. it passes the generic validator: the ASCII sum of the first six characters,
   minus `390`, modulo 26, must equal the alphabet index of the seventh
   character, and the decoded fields must satisfy the campaign/score range
   checks.

The generic payload is a **campaign selector plus a starting score**:

* `campaign = (idx(c0) - idx(c5)) / 2 + 1` (1..4 selects campaigns 2..5; 5 is
  the ending sequence),
* the middle four characters decode to four decimal digits that become the
  starting score in thousands.

The complete accepted space is **40,004 inputs**: 40,000 generic codes
(4 campaign values × 10,000 scores) plus the four special codes. Only a handful
appear in any published list.

I entered the unpublished generic code **`RWJJKHG`** in the emulator: the menu
changed to **CAMPAIGN #4 NUCLEAR STORM**, and the in-game HUD showed
**SCORE 5003000**, exactly the decoded payload. RAM confirms
`$020018BC = 3` (campaign index), `$02002070 = 05 00 00 03` (digits 5,0,0,3),
and `$020020A6/$020020A8 = 0x004C56F8` (5,003,000). Bounds were proven by
rejection: the same payload with a wrong checksum (`RWJJKHB`) and a
checksum-valid but out-of-range campaign field (`RFFFPZC`, campaign index 5)
were both rejected and left the accepted state untouched.

The published GBA code `BS9JS27` ("10 lives") is **not** checksum-valid; it is
one of the four hard-coded special cases. Entering it and starting the campaign
gave **LIVES 10** in the HUD. Three unpublished special codes were also entered
and verified in RAM.

## 3. How to reproduce

### Emulator and keymap

Two frontends were used for cross-checking:

* **mGBA 0.10.5 SDL** (`SDL_AUDIODRIVER=dummy mgba -3 game.gba`): A=`x`,
  B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
* **Mednafen 1.32.1** (`mednafen -sound 0 -video.driver softfb game.gba`):
  built-in GBA gamepad defaults are A=`KP_3`, B=`KP_2`, L=`KP_5`, R=`KP_6`,
  Start=`Return`, Select=`Tab`, D-pad=`W/A/S/D` (scancodes 26/4/22/7). Menu
  presses must be held ~200–250 ms; 10 ms taps are frequently missed.

All work was done on `Xvfb :302` (1024×768×24) with `openbox`; the game window
was captured per-window with `import -window` to avoid overlap from unrelated
windows on the same display.

### Exact path to the password screen

1. Boot. Wait for the title (`PRESS START`).
2. Press **Start** once → `MAIN MENU` (`A: CAMPAIGN`, `B: COPILOT`,
   `R: OPTIONS`).
3. **Hold A (`KP_3` in Mednafen) for ~250 ms** → screen fades to
   `CAMPAIGN MENU / ENTER PASSWORD`. (A short tap is ignored and can look like
   "A goes back to the title".)
4. Up/Down change the character under the underline; Left/Right move the
   cursor; **Start submits**.

### Codes tested live

| Code | Screen path | Result |
|---|---|---|
| `3ZJMZT7` | A → password → Start | **CAMPAIGN #2 SCUD BUSTER** (published) |
| `W3HWK8B` | A → password → Start | **CAMPAIGN #3 EMBASSY CITY** (published) |
| `BS9JS27` | A → password → Start, then Start → campaign | **LIVES 10** (published; special case) |
| `RWJJKHG` | A → password → Start | **CAMPAIGN #4 NUCLEAR STORM**, HUD `SCORE 5003000` (novel) |
| `RWJJKHB` | same | rejected; menu unchanged |
| `RFFFPZC` | same | rejected; campaign #4 and RAM state unchanged ($2C=5 is out of range) |
| `B84GT7S` | same | accepted; `$020020FE = 1` (novel, undocumented) |
| `B74GT7S` | same | accepted; `$02002100 = 1` (novel, undocumented) |
| `GTSTFTC` | same | accepted; `$0200217C = 1000` (novel, undocumented) |

### Menus walked (Phase 2)

Title/copyright, title with helicopter (`PRESS START`), `MAIN MENU`,
`COPILOT` dossier (B), `OPTIONS MENU` (R: BUTTONS GUNS/HYDRAS/MISSILES,
CONTROL WITH MOMENTUM), `CAMPAIGN MENU` password entry, campaign intro
(`THE MIDDLE EAST`, carrier and cutscenes), briefing, gameplay HUD, and the
in-game Start screen (carrier/map view). No hidden or debug menu was found;
the only debug-looking strings (`DMA CG/VM STACK OVERFLOW`, `NO RAM NODES`,
`OUT OF SPRITES`, `FG SUBTRACT`) are engine diagnostics with no reachable UI.

## 4. Address map

ROM addresses are `0x08000000 + file offset`. "image" = the embedded 2 MiB SNES
image at file `0x200000`; image offset = the 24-bit address used by its code.

| Function | Image offset | File offset | GBA address |
|---|---:|---:|---:|
| SNES-format header ("DESERT STRIKE") | `0x00FFC0` | `0x20FFC0` | `0x0820FFC0` |
| Password alphabet table (26 bytes) | `0x02AC6B` | `0x22AC6B` | `0x0822AC6B` |
| Checksum accumulate helper (`ADC` + table + store) | `0x02AC4F` | `0x22AC4F` | `0x0822AC4F` |
| Entry/input handler (vowel aliasing, char wrap, Start submit) | `0x02BF00` | `0x22BF00` | `0x0822BF00` |
| Hard-coded code 1 `B84GT7S` → `$20FE=1` | `0x02BF5C` | `0x22BF5C` | `0x0822BF5C` |
| Hard-coded code 2 `B74GT7S` → `$2100=1` | `0x02BF88` | `0x22BF88` | `0x0822BF88` |
| Hard-coded code 3 `BS9JS27` → `$20AC=10` | `0x02BFB4` | `0x22BFB4` | `0x0822BFB4` |
| Hard-coded code 4 `GTSTFTC` → `$217C=1000` | `0x02BFE0` | `0x22BFE0` | `0x0822BFE0` |
| Generic validator (checksum + fields) | `0x02C00C` | `0x22C00C` | `0x0822C00C` |
| Character → alphabet index (reverse search) | `0x02C11E` | `0x22C11E` | `0x0822C11E` |
| Encoder for the current game state (score/checksum) | `0x02AA00`–`0x02AB30` | `0x22AA00`–`0x22AB30` | `0x0822AA00` |
| Text `CAMPAIGN MENU` / `ENTER PASSWORD` | — | `0x30F016` / `0x30F038` | `0x0830F016` |

Emulated game RAM (EWRAM; SNES low-RAM addresses preserved):

| Variable | Address | Meaning |
|---|---:|---|
| Password buffer (7 bytes, ASCII) | `0x020009DA` | characters as typed |
| Decoded 4 digits | `0x02002070`..`0x02002073` | most significant first |
| Campaign selector `$2C` | `0x020018BC` | 1..4 → campaign 2..5 |
| Score low/high (32-bit) | `0x020020A6` / `0x020020A8` | digits × 1000 |
| Lives (special code target) | `0x020020AC` | normal 3; `BS9JS27` writes 10 |
| Special flags | `0x020020FE`, `0x02002100`, `0x0200217C` | see §6 |

## 5. Algorithm

### 5.1 Character set and index

Only the 26 bytes at image `0x02AC6B` are valid; the routine at `0x02C11E`
searches them from index 25 down to 0. If a character is not found it unwinds
(returns to the caller's caller), i.e. the code is rejected.

```
ALPHA = "ZQMTH3L2J8RKBW94FP5SCNGX7D"     # 26 symbols, index 0..25
idx(c): return ALPHA.index(c) or INVALID
```

The on-screen keypad, however, cycles the ASCII range `0-9A-Z` with the vowels
and Y aliased away (the input handler at `0x02BF00` decrements `E,I,O,U,Y` to
the previous consonant and wraps `0-1`/`A-1`), so the visible cycle is

```
B C D F G H J K L M N P Q R S T V W X Z 1 2 3 4 5 6 7 8 9
```

That is 29 symbols. `V`, `1` and `6` are offered by the UI but are **not** in
`ALPHA`, so any code using them is rejected by the index lookup. This is the
trap that makes the on-screen alphabet look larger than the real one.

### 5.2 Special codes (checked first)

Four literal 7-character comparisons against the input buffer:

```
B84GT7S : [$20FE] = 1
B74GT7S : [$2100] = 1
BS9JS27 : [$20AC] = 10          # "10 lives", published
GTSTFTC : [$217C] = 1000
```

They are compared as three 16-bit words plus one byte; a match sets the target
and returns before the checksum. `BS9JS27` fails the generic checksum, which is
why a naive checksum model rejects the published 10-lives code even though the
game accepts it.

### 5.3 Generic validator (image `0x02C00C`)

```
on submit(code[0..6]):
    if special(code): apply; return ACCEPT

    if any c not in ALPHA: return REJECT
    a = [idx(c) for c in code]                    # 7 values 0..25

    # checksum: SNES divider $4204/$4206, remainder $4216
    if ((sum(ord(code[0..5])) - 390) % 26) != a[6]: return REJECT

    if a[0] + a[5] < 8:                return REJECT
    if a[0] < a[5]:                    return REJECT
    if (a[0] - a[5]) & 1:              return REJECT
    c = (a[0] - a[5]) // 2
    if not (1 <= c <= 4):              return REJECT      # cmp #5 / bcs
    base = (c - 1) * 4
    if any(a[i] - base < 0 for i in 0..4): return REJECT  # BMI
    d = [a[1]-base, a[2]-base, a[3]-base, a[4]-base]
    if any(x > 9 for x in d):          return REJECT      # 4 decimal digits
    if d[3] != a[5] + c - 4:           return REJECT      # $2073 vs $24

    $18BC = c
    score = int(str(d[0])+str(d[1])+str(d[2])+str(d[3])) * 1000
    $20A6/$20A8 = score (32-bit)
    if high_word(score) >= 2: $20F8 = 0
    return ACCEPT        # campaign = c + 1, starting score = score
```

`c = 1..3` selects campaigns 2–4. `c = 4` selects campaign 5, which is the
ending sequence (`F9N5CJ8` decodes to this). `c = 5` is excluded by the
`CMP #$0005 / BCS` bound and was rejected live.

### 5.4 Encoder (current game state, for reference)

The routine at `0x02AA00` builds a code from the live state: it takes the four
decimal digits, forms `number*1000`, divides by 26, uses the remainder as an
index into the same table and emits the seventh symbol. This is the "show my
current password" path; it is narrower than the validator in the sense that it
only produces states the game itself reached.

## 6. Tables

### Alphabet (`0x0822AC6B`, 26 bytes)

```
index: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25
char:  Z  Q  M  T  H  3  L  2  J  8  R  K  B  W  9  4  F  P  5  S  C  N  G  X  7  D
```

### Field layout

```
c0 c1 c2 c3 c4 c5 c6
 |  |  |  |  |  |  +-- checksum symbol, idx = (sum(ascii c0..c5) - 390) % 26
 |  |  |  |  |  +----- a5; with a0 sets campaign and the d3 constraint
 |  |  |  |  +-------- a4 = base + d3
 |  |  |  +----------- a3 = base + d2  \
 |  |  +-------------- a2 = base + d1   > 4 decimal score digits, d0 most significant
 |  +----------------- a1 = base + d0  /
 +-------------------- a0 = a5 + 2*c
base = (c-1)*4 ; campaign = c+1 ; score = d0d1d2d3 * 1000
```

### Published-code verification

`idx`/checksum model results; ✅ = live-tested in the emulator.

| Published code | Claimed effect | GBA result |
|---|---|---|
| `3ZJMZT7` | Level/campaign 2 | ✅ generic valid: campaign 2, score 820,000 |
| `W3HWK8B` | Campaign 3 | ✅ generic valid: campaign 3, score 1,097,000 |
| `9Z2M8BL` | Campaign 2 (GBA list) | generic valid: campaign 2, score 729,000 |
| `F848PRL` | Campaign 4 (GBA list) | generic valid: campaign 4, score 1,719,000 |
| `JR8P8M8` | Level 4 | generic valid: campaign 4, score 2,191,000 |
| `93LLBR5` | Embassy City | generic valid: campaign 3, score 1,228,000 |
| `F9N5CJ8` | Ending | generic valid: campaign index 5 (ending), score 2,968,000 |
| `BS9JS27` | 10 lives | ✅ special case: `$20AC=10`, HUD LIVES 10 |
| `K32L82R` | Level 3 (GBA list) | **bad checksum** — model rejects |
| `9R894JH` | Nuclear Storm (SNES list) | **bad checksum** — model rejects |
| `K9CF4T4` | Winner's screen (SNES) | **field underflow** — model rejects |
| `LQAHQRL`, `ILLBWBY`, `BTOBKLW` | Genesis campaign codes | **bad symbol** (`A/I/O/U/Y` are not in the GBA alphabet) |

The literal strings are absent from the ROM in every encoding; these are
algorithmic codes. The Genesis/SNES lists are a different SKU and must not be
copied to GBA (the checksum split makes that measurable).

## 6b. Enumeration

### Space definition

* Alphabet: 26 symbols (`ZQMTH3L2J8RKBW94FP5SCNGX7D`).
* Length: exactly 7; the seventh is a checksum over the first six.
* Checksum: `(sum of ASCII of c0..c5 - 390) mod 26`, compared to the alphabet
  index of c6. No reserved bits, no key table.
* Field constraints: `a0 >= a5`, `a0-a5` even and in `{2,4,6,8}`,
  `1 <= (a0-a5)/2 <= 4`, `a1..a4 >= (c-1)*4`, each of `a1..a4` in
  `base..base+9`, and `d3 == a5+c-4`.

Counting the field space: for each campaign value `c ∈ {1,2,3,4}` there are 10
valid `a5` values and 10^3 choices of the first three digits; the fourth digit
is forced. That gives exactly **40,000** generic codes. Adding the four
hard-coded specials gives **40,004 accepted inputs**. The UI presents
29^7 = 17,249,876,309 strings; everything using `V`, `1` or `6`, a bad check
character, or an out-of-range field is rejected.

### Novel codes (in no published list)

| Code | Kind | Payload | In-game proof |
|---|---|---|---|
| **`RWJJKHG`** | generic | campaign 4, score 5,003,000 | Menu: `CAMPAIGN # 4 NUCLEAR STORM`; HUD: `SCORE 5003000`; RAM `$020018BC=3`, `$02002070=05 00 00 03`, `$020020A6/$A8=0x004C56F8` |
| **`B84GT7S`** | special | `$020020FE=1` | Submitted; menu unchanged; RAM flag = 1 |
| **`B74GT7S`** | special | `$02002100=1` | Submitted; RAM flag = 1 |
| **`GTSTFTC`** | special | `$0200217C=1000` | Submitted; RAM `21 7C = E8 03` |
| `BS9JS27` | special (published) | `$020020AC=10` | HUD `LIVES 10` |

`RWJJKHG` was chosen to combine a campaign not covered by the published GBA
list (`$2C=3`) with an arbitrary score (5003) absent from every list, so it
cannot be a transcription of a known code.

### Bounds proven by rejection

| Input | Why it is outside the model | Observed result |
|---|---|---|
| `RWJJKHB` | correct payload, incorrect check character (`B` instead of `G`) | returned to the menu unchanged (campaign 1 at the time) |
| `RFFFPZC` | checksum-valid but `(a0-a5)/2 = 5`, outside `1..4` | returned to the menu with campaign #4 unchanged; RAM still `$18BC=3`, `$2070=05 00 00 03`, score 5,003,000 |
| `K32L82R`, `9R894JH` | checksum invalid | model rejects (not separately re-entered) |

The `RFFFPZC` test is the strongest one: the code passes the checksum layer but
fails the campaign range check, and the previously accepted state survives
untouched, so the rejection is a semantic range rejection, not a parse failure.

## 7. Validation evidence

**Observed**

* `3ZJMZT7` → main menu `CAMPAIGN # 2 SCUD BUSTER`.
* `W3HWK8B` → main menu `CAMPAIGN # 3 EMBASSY CITY`.
* `RWJJKHG` → main menu `CAMPAIGN # 4 NUCLEAR STORM`; on starting the campaign,
  HUD `LIVES 3`, `SCORE 5003000`.
* `BS9JS27` → after starting the campaign, HUD `LIVES 10` (and HUD score
  1,097,000 from the previously accepted `W3HWK8B`).
* `B84GT7S`, `B74GT7S`, `GTSTFTC` accepted; RAM flags `$20FE=1`, `$2100=1`,
  `$217C=1000`.
* Rejections of `RWJJKHB` and `RFFFPZC`; accepted state preserved.
* RAM reads from Mednafen `.mc0` (gzip) savestates: password buffer, decoded
  digits, campaign index, 32-bit score.
* Menus listed in §3 were each captured.

**Derived**

* The 26-symbol alphabet, checksum formula, field constraints and the 40,000
  generic code count, from the 65C816 listing at `0x02C00C` and reproduced by
  the independent Python model (`model.py`), which agrees with all live tests.
* `BS9JS27`/`B84GT7S`/`B74GT7S`/`GTSTFTC` are compared before the checksum;
  this is why the published 10-lives code is accepted despite a bad checksum.
* `$20FE` is read at image `0x1884E` in the life-decrement path (a nonzero value
  skips the decrement and reloads the life counter) — inferred "infinite
  lives / invulnerability".
* `$217C` is copied to `$2098` and clamped to 25 at image `0x18914` — inferred
  weapon/ammo parameter.
* `F9N5CJ8` decodes to campaign index 5 (ending sequence), consistent with its
  published label.

**Inferred / not proven**

* Whether the GBA executes this 65C816 code directly (interpreter/translator)
  or an ARM translation; the observable algorithm and RAM layout match the
  65C816 listing either way.
* The exact gameplay effect of `B74GT7S` (`$2100`): no direct reader was found
  in the 2 MiB image, so it is a write-only/unknown flag.
* `GTSTFTC`'s visible effect beyond `$217C=1000` (the value feeds the weapon
  path, but the in-game result was not exercised to a target).

## 8. Unknowns

* The GBA-side ARM implementation (if any) was not disassembled; only the
  original 65C816 logic in the embedded image was read. Addresses above are
  image/ROM offsets, not ARM function addresses.
* `$2100` has no direct reader in the image.
* Campaign 5 (`$2C=4`) was not entered live; its mapping to the ending is
  model-derived.
* No hidden debug menu or button code was found; the negative is bounded by the
  full menu walk plus the string/table search described in §3/§9.

## 9. Tooling

* `mgba 0.10.5` and `mednafen 1.32.1` under `Xvfb :302` + `openbox`;
  `xdotool` for XTEST input, `scrot`/`import` for per-window captures.
* `python3` scripts in `/tmp/opencode/desertstrike`:
  * `model.py` — alphabet/checksum/field validator and exhaustive counter
    (returns 40,000 generic codes),
  * `ent3.py` — password entry driver that reads the live buffer from a
    Mednafen savestate and selects the shorter Up/Down path,
  * `ss.py` — mGBA `gbAs` PNG/zlib savestate reader (EWRAM at `0x21000`),
  * Mednafen `.mc0` savestates are gzip; EWRAM base was located at state offset
    `0x24E6C` by matching the 7-character buffer.
* `da65` (cc65) was installed but does not support 65816; the validator region
  was decoded by hand from the byte listing (opcodes verified against the
  65C816 reference).
* Static tools: `strings`, `grep -abo`, `xxd`, Python `struct`/`zlib`/`gzip`.

## 10. Legal note

No ROM, graphics, music or game text is redistributed here. All screenshots and
savestates referenced were produced locally for verification and remain
generated artifacts.
