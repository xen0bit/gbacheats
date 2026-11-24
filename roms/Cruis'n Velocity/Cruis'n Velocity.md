# Cruis'n Velocity (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Cruis'n Velocity/Cruis'n Velocity.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `CRUISN VELOC` |
| Game code | `ACFE` (USA) |
| Maker code | `5D` |
| Software version | 0x00 |
| Fixed byte 0xB2 | 0x96 |
| Entry word | `0xEA00002E` → `0x080000C0` (stock GBA crt0) |
| Complement check (stored) | 0x5C |
| Complement check (computed over 0xA0..0xBC) | 0x58 |
| Header checksum (0xBE) | 0x0000 |
| MD5 | `987308f23cea98609a77629cc1bfb23a` |
| SHA-1 | `762aabc26501dee4aa566e8327600433c8edbf7a` |
| SHA-256 | `558ea6cf3f5aa0739f20082fd399f16f7be38dbd278914e7c4aee394a71e6e05` |

Header scan: exactly one Nintendo logo (`24 FF AE 51 …`) at file offset 0x4, i.e. one
GBA image based at 0x08000000. No multi-game header. The entry branch and the
ARM crt0 at 0xC0 are the stock Nintendo/GCC startup (`mov r0,#0x12; msr cpsr_cxsf,r0;
ldr sp,…`), no cracktro, no appended trainer, and the file is exactly 4 MiB.
The header checksum 0x0000 plus the complement mismatch (0x5C vs 0x58) are the
usual artifact of a rebuilt header; the code and the Nintendo logo are intact.
The 0-byte `.sav` produced by mGBA is consistent with the game having **no
battery save**: progress is carried by the password system.

## 2. Executive summary

Cruis'n Velocity has a single, complete, in-game password system and **no**
button-cheat, debug-menu or secret-menu surface.

* The PASSWORD screen accepts exactly **8 characters from a 21-symbol alphabet**
  (space plus the 20 consonants `B C D F G H J K L M N P Q R S T V W X Z`).
* The 8 characters are two 4-letter words. The first word is one of **16**
  hard-coded words (table A); the second is one of **32** (table B).
* The accepted set is therefore exactly **16 × 32 = 512** strings, mapping
  bijectively to a 9-bit progress/unlock word at `0x0300203C`
  (`index = i | (j << 4)`). There is no checksum and no unused payload bit.
* The same tables drive the game's own password display ("YOUR NEW PASSWORD IS"),
  so the encoder and validator were both recovered and agree.
* Three published codes were re-entered in mGBA and produced exactly the
  predicted words: `HLDDRTSN` → `0x018`, `STRBHVGD` → `0x1FA`,
  `RLCRHVGD` → `0x1FF`.
* Two codes that appear in no published list were minted and accepted:
  `TRDNBDDH` (mask 0x001, BEAST) and `TTBRBDDH` (mask 0x002, HOT ROD). For the
  latter the locked→unlocked change was observed behaviourally: before the code,
  selecting car slot 2 in the car-select screen was ignored; after it, the same
  selection advanced the screen (state 14 → 7).
* Bounds were proven by rejection: a syntactically valid 8-character code whose
  first word is not in table A (`BBBBBDDH`) and a short code
  (`TRDNBDD` + space) both reach the INCORRECT screen and leave the word
  unchanged.

The published list is a strict subset (6 codes) of the 512-code space. Codes for
the other 506 masks — including single-car unlocks and arbitrary combinations of
cup/track bits — are unpublished; this report's enumeration makes all of them
constructible.

## 3. How to reproduce

Emulator/tooling: mGBA SDL (`mgba -3`) under `Xvfb :272` + `openbox`, with
`SDL_AUDIODRIVER=dummy`. Default mGBA keymap: **A = x, B = z, Start = Return,
Select = BackSpace, D-pad = arrows**.

Title → main menu: press **Start** (the boot sequence takes a few seconds; press
Start again if the logo screens are still running).

Main menu (`0x0300202C` = selected index):

| Index | Item | Result |
|---:|---|---|
| 0 | SINGLE PLAYER | state 5, then car select (state 14) |
| 1 | MULTI PLAYER | state 20 |
| 2 | PASSWORD | state 22 |
| 3 | OPTIONS | state 12 |

`Down` moves the index; `A` confirms. The order was confirmed both from the
string pointer table at `0x082B23F4` (SINGLE PLAYER, MULTI PLAYER, PASSWORD,
OPTIONS) and from the per-index jump table in the state-4 handler at `0x08007408`.

Password screen (state 22):

* `Up`/`Down` cycle the current slot through the 21 symbols
  (space → B → C → D → F → G → H → J → K → L → M → N → P → Q → R → S → T →
  V → W → X → Z → space).
* `Left`/`Right` move between the 8 slots; `Select` clears all slots.
* `A` (or Start) submits. Accept → returns to the main menu and ORs the decoded
  9-bit value into `0x0300203C`. Reject → state 23, which draws
  "PASSWORD" / "INCORRECT" / "PRESS ANY BUTTON"; any button returns to state 22.

Codes tested (all re-entered in the emulator):

| Code | Word split | Predicted mask | Observed `0x0300203C` |
|---|---|---|---|
| `HLDDRTSN` (published L1) | HLDD / RTSN | 0x018 | 0x00000018 |
| `STRBHVGD` (published Hot Rod) | STRB / HVGD | 0x1FA | 0x000001FA |
| `RLCRHVGD` (published “everything”) | RLCR / HVGD | 0x1FF | 0x000001FF |
| `TRDNBDDH` (novel) | TRDN / BDDH | 0x001 | 0x00000001 |
| `TTBRBDDH` (novel) | TTBR / BDDH | 0x002 | 0x00000002 |
| `BBBBBDDH` (invalid word A) | BBBB / BDDH | — | rejected, state 23, word unchanged |
| `TRDNBDD␠` (incomplete) | TRDN / BDD␠ | — | rejected, state 23, word unchanged |

## 4. Address map

| Item | ROM address | File offset | Notes |
|---|---:|---:|---|
| State dispatch table (120 entries) | 0x082B2200 | 0x2B2200 | `state → entry\|1`, 0x03002070 holds the state |
| Password screen handler | 0x08007A88 | 0x7A88 | state 22 draw; helper memcpy at 0x0800769C |
| Password validator | 0x08007B08 | 0x7B08 | state 59; compares 8 bytes at 0x03002010 |
| INCORRECT screen | 0x08007CFC | 0x7CFC | state 23 |
| Password display/encoder | 0x08008034 | 0x8034 | state 62; reads 0x0300203C, prints its code |
| Unlock toast | 0x08007D6C / 0x08007D8C | 0x7D6C/0x7D8C | state 24; name index 0x03002060 → table 0x082B2528 |
| Table A pointers (16) | 0x082B2468 | 0x2B2468 | each points at a 4-letter word |
| Table B pointers (32) | 0x082B24A8 | 0x2B24A8 | each points at a 4-letter word |
| Word strings A | 0x0815314–0x081538C | 0x15314 | 8-byte records, word + NUL padding |
| Word strings B | 0x0815394–0x081548C | 0x15394 | 8-byte records |
| Unlock-name table (9) | 0x082B2528 | 0x2B2528 | BEAST, HOTROD, SCORPION, 4X4, PRO CUP, VELOCITY CUP, CHAMPIONSHIP, HOLLAND 2, ALASKA 3 |
| Car-name table (11) | 0x082B2704 | 0x2B2704 | SPEEDER, COP, HOTROD, 4X4, JETCAR, HUNTER, TAXI, BEAST, SCORPION, SURF VAN, WOODY |
| Car-select lock gates | 0x080087A0–0x080087E4 | 0x87A0 | index 0x030045B0 → car table; bits of 0x0300203C |
| Progress/unlock word | RAM 0x0300203C | — | 32-bit, only low 9 bits used |
| Password input buffer | RAM 0x03002010 | — | 8 bytes, copied from display buffer |
| Password display buffer | RAM 0x03002058 | — | 8 bytes, edited by the screen |
| Car-select index | RAM 0x030045B0 | — | 0..10 |
| Current screen state | RAM 0x03002070 | — | byte, indexes 0x082B2200 |
| Settings byte (options) | RAM 0x030068D8 | — | bits toggled by the OPTIONS screen |
| Key state | RAM 0x03001040 | — | held buttons: A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200 |

The key-state layout was confirmed by holding one button and saving a state:
`B` → `0x0002`, `Start` → `0x0008`, `Select` → `0x0004`, `Right` → `0x0010`,
`Down` → `0x0080`, `R` → `0x0100`, `L` → `0x0200`.

## 5. Algorithm

Validator (`0x08007B08`), exactly as the ROM does it:

```
buf = RAM[0x03002010 .. 0x03002010+7]        # 8 ASCII bytes
m = -1
for i in 0..15:
    if buf[0..3] == wordA[i]: m = i; break
if m < 0: reject()                            # -> state 23 (INCORRECT)
for j in 0..31:
    if buf[4..7] == wordB[j]: m |= (j << 4); break
if j == 32 (no hit): reject()
RAM32[0x0300203C] |= m                        # OR, never clear
go to state 4 (main menu)
```

Encoder / password display (`0x08008034`):

```
m = RAM32[0x0300203C]
code = wordA[m & 0x0F] + wordB[(m >> 4) & 0x1F]
print(code)                                   # "YOUR NEW PASSWORD IS …"
```

Properties:

* No checksum, no parity, no reserved bit: every 9-bit value 0..511 has exactly
  one spelling, and every 9-bit value is reachable.
* The OR semantics mean a password is a *set of flags*, not a snapshot; entering
  an already-set bit is idempotent and there is no in-game way to clear a bit.
* The player-facing alphabet (21 symbols) is larger than the words require; only
  the 48 stored words are accepted, so the effective input space is 512 strings.

Reference implementation (verified against every published code and every
in-emulator observation):

```python
A = ["DRVT","TRDN","TTBR","THTH","SDWN","DRSL","PSTN","TVRD",
     "HLDD","LCKD","STRB","RDRL","NLKV","RGNM","TRLG","RLCR"]
B = ["BDDH","RTSN","WRLN","SNST","RMNT","LNSW","TNSS","FLLW",
     "SMNT","DGTR","WDLG","NRLN","DSTR","MKTT","NMNN","THMN",
     "ZDFR","DNTT","HGRV","LVTT","LLPP","DNTP","RCHP","NDRH",
     "RTLS","LBNT","LKPR","DRXP","RSSD","RSLF","CHRS","HVGD"]

def encode(m):  return A[m & 15] + B[(m >> 4) & 31]
def decode(c):
    if len(c) != 8: return None
    try: i = A.index(c[:4])
    except ValueError: return None
    try: j = B.index(c[4:])
    except ValueError: return None
    return i | (j << 4)
```

## 6. Tables

### 6.1 Word table A (low nibble of the mask)

| i | word | ROM string |
|---:|---|---|
| 0 | DRVT | 0x081538C |
| 1 | TRDN | 0x0815384 |
| 2 | TTBR | 0x081537C |
| 3 | THTH | 0x0815374 |
| 4 | SDWN | 0x081536C |
| 5 | DRSL | 0x0815364 |
| 6 | PSTN | 0x081535C |
| 7 | TVRD | 0x0815354 |
| 8 | HLDD | 0x081534C |
| 9 | LCKD | 0x0815344 |
| 10 | STRB | 0x081533C |
| 11 | RDRL | 0x0815334 |
| 12 | NLKV | 0x081532C |
| 13 | RGNM | 0x0815324 |
| 14 | TRLG | 0x081531C |
| 15 | RLCR | 0x0815314 |

### 6.2 Word table B (bits 4..8 of the mask)

| j | word | ROM string | j | word | ROM string |
|---:|---|---|---:|---|---|
| 0 | BDDH | 0x081548C | 16 | ZDFR | 0x081540C |
| 1 | RTSN | 0x0815484 | 17 | DNTT | 0x0815404 |
| 2 | WRLN | 0x081547C | 18 | HGRV | 0x08153FC |
| 3 | SNST | 0x0815474 | 19 | LVTT | 0x08153F4 |
| 4 | RMNT | 0x081546C | 20 | LLPP | 0x08153EC |
| 5 | LNSW | 0x0815464 | 21 | DNTP | 0x08153E4 |
| 6 | TNSS | 0x081545C | 22 | RCHP | 0x08153DC |
| 7 | FLLW | 0x0815454 | 23 | NDRH | 0x08153D4 |
| 8 | SMNT | 0x081544C | 24 | RTLS | 0x08153CC |
| 9 | DGTR | 0x0815444 | 25 | LBNT | 0x08153C4 |
| 10 | WDLG | 0x081543C | 26 | LKPR | 0x08153BC |
| 11 | NRLN | 0x0815434 | 27 | DRXP | 0x08153B4 |
| 12 | DSTR | 0x081542C | 28 | RSSD | 0x08153AC |
| 13 | MKTT | 0x0815424 | 29 | RSLF | 0x08153A4 |
| 14 | NMNN | 0x081541C | 30 | CHRS | 0x081539C |
| 15 | THMN | 0x0815414 | 31 | HVGD | 0x0815394 |

### 6.3 Bit map of `0x0300203C`

| Bit | Mask | Meaning | Evidence |
|---:|---:|---|---|
| 0 | 0x001 | BEAST car | `ANDS` at 0x080087C0: car index 7 requires this bit |
| 1 | 0x002 | HOT ROD car | `ANDS` at 0x080087AE: car index 2 requires this bit; published Hot Rod code sets it |
| 2 | 0x004 | SCORPION car | `ANDS` at 0x080087D2: car index 8 requires this bit |
| 3 | 0x008 | 4×4 car | `ANDS` at 0x080087E4: car index 3 requires this bit |
| 4 | 0x010 | PRO CUP | toast-name index 4 in 0x082B2528 (Derived) |
| 5 | 0x020 | VELOCITY CUP | toast-name index 5 (Derived) |
| 6 | 0x040 | CHAMPIONSHIP | toast-name index 6 (Derived) |
| 7 | 0x080 | HOLLAND 2 (secret track) | toast-name index 7 (Derived) |
| 8 | 0x100 | ALASKA 3 (secret track) | toast-name index 8 (Derived) |

The car bits 0–3 are proven twice: by the gate instructions (car table index →
required bit) and by the published Hot Rod code, which contains bit 1. Bits 4–8
follow the order of the 9-entry unlock-name table used by the toast screen; the
individual names are inferred from that table's order, not from a rendered
screen.

## 6b. Enumeration

**Space definition**

* Alphabet per slot: 21 symbols = space + `BCDFGHJKLMNPQRSTVWXZ` (A, E, I, O, U
  and Y are absent; the cycle length was measured at 21: 21 `Up` presses return
  to space).
* Length: exactly 8 slots; shorter/incomplete input is rejected.
* Structure: 4-letter word A[0..15] + 4-letter word B[0..31].
* Representable accepted values: **512** (one per 9-bit mask 0..0x1FF).
* Input strings of the same shape: 21^8 = **37,822,859,361**; only 512 are
  accepted (≈1.35 × 10⁻⁸ of the formal input space).
* Checksum: none. Reserved bits: none. Aliases: none (both word tables have
  distinct entries, so the map is a bijection).

**Published vs. enumerated**

The six published codes are the six combinations someone wrote down; decoding
them gives 0x018, 0x038, 0x0B8, 0x1F8, 0x1FA, 0x1FF. 506 masks have no published
spelling.

Published codes are not stored literally anywhere in the ROM (a byte search for
each 8-character string returns −1); they are composed from the two word tables,
which is why the tables are the real anchor.

**Novel codes generated and confirmed in mGBA**

| Novel code | Mask | Effect | In-game proof (Observed) |
|---|---:|---|---|
| `TRDNBDDH` | 0x001 | BEAST only | accepted; `0x0300203C` went 0x00000000 → 0x00000001 |
| `TTBRBDDH` | 0x002 | HOT ROD only | accepted; `0x0300203C` → 0x00000002. Before the code, car slot 2 (HOT ROD) refused `A` and the screen stayed at state 14; after the code, the same slot accepted `A` and the screen advanced to state 7 |
| `SDWNBDDH` | 0x004 | SCORPION only | decoder-generated, not entered (see Unknowns) |
| `HLDDBDDH` | 0x008 | 4×4 only | decoder-generated, not entered |

`TTBRBDDH` is deliberately different from the published Hot Rod code
`STRBHVGD`: the published code is mask 0x1FA (Hot Rod **plus** progress bits
3–8), whereas `TTBRBDDH` sets only bit 1.

**Bounds proven by rejection**

| Input | Why the format forbids it | Observed result |
|---|---|---|
| `BBBBBDDH` | `BBBB` is not one of the 16 A-words | state 23 (INCORRECT); `0x0300203C` unchanged |
| `TRDNBDD␠` | only 7 real symbols; space is not a B-word suffix | state 23; word unchanged |
| `A`/`E`/`I`/`O`/`U`/`Y` anywhere | not in the 21-symbol entry alphabet | cannot be selected at all (cycle measurement) |
| 9+ characters | UI has 8 slots and the validator compares exactly 8 bytes | no way to submit |

## 7. Validation evidence

**Observed (emulator RAM reads from mGBA savestates, `gbAs` chunk):**

* `0x0300203C` = 0x00000000 before any password.
* `HLDDRTSN` → 0x00000018; `STRBHVGD` → 0x000001FA; `RLCRHVGD` → 0x000001FF.
* `TRDNBDDH` → 0x00000001; `TTBRBDDH` → 0x00000002.
* Car select (state 14), index 0x030045B0 = 2 (HOT ROD), `A` pressed:
  * with `0x0300203C` = 0: state stayed 14 (lock gate), and the car index stayed 2;
  * with `0x0300203C` = 2: state advanced 14 → 7.
* `BBBBBDDH` and `TRDNBDD␠`: state 22 → 23 (INCORRECT) and `0x0300203C` unchanged.
* Key mask values: holding `B` gives 0x0002 at 0x03001040, `Start` 0x0008,
  `Select` 0x0004, `Right` 0x0010, `Down` 0x0080, `R` 0x0100, `L` 0x0200.

**Derived (instruction-level):**

* Validator and encoder table indices and the `i | (j<<4)` packing
  (`0x08007B08`, `0x08008034`).
* Car-lock gates at `0x080087A0`–`0x080087E4` (car index → required bit).
* Main-menu item order and routing (`0x08007408`: index 0 → state 5,
  1 → state 20, 2 → state 22, 3 → state 12).
* OPTIONS screen (state 12, `0x08008E24` + `0x08009448`) has five entries; entry
  0 toggles bit 4 of `0x030068D8`, entry 1 toggles bit 5 and calls the music
  start/stop routines `0x080126C4`/`0x080127B4`, entry 2 toggles bit 7, entries
  3 and 4 switch to states 35 and 28. Labels DAMAGE / MUSIC / SOUND FX are
  inferred from the only three toggle strings in the bank
  (`DAMAGE: ON/OFF` 0x152AC, `MUSIC: ON/OFF` 0x152C4, `SOUND FX: ON/OFF`
  0x152E0); the music calls make entry 1 = MUSIC certain.
* Pre-race configuration screen (state 11, `0x08008CC4`) has a 7-way dispatch on
  `0x030068D2`; its string bank contains exactly the seven fields NAME /
  TRACK / CAR TYPE / RACE INTRO / GEAR TYPE / GAME TYPE / MAIN MENU
  (0x154DC–0x15520), and its handlers cycle the 14-track permutation tables at
  0x2B28A4 and 0x2B28B2.

**Inferred (not directly exercised):**

* The names attached to mask bits 4–8 (cup/track names) come from the toast-name
  table order, correlated with the proven car bits 0–3.
* Which of bit 4 / bit 7 is DAMAGE vs SOUND FX on the OPTIONS screen.

## 8. Unknowns

* The precise semantic of each cup/track bit during a championship series was
  not played through; only the bit → name mapping from the toast table is given.
* `SDWNBDDH` (0x004) and `HLDDBDDH` (0x008) are decoder-generated but were not
  re-entered (the two entered novel codes already establish the mapping and the
  two-sided car gate evidence).
* The pause overlay was not enumerated field-by-field: pressing Start in the
  pre-race screen enters state 11 (`0x08008CC4`), whose 7-slot dispatch ignores
  D-pad navigation in the tested build, and Start selects slot 0 and returns to
  the race flow via the delay state 37 (`0x08007360`). No cheat/debug entry
  exists in that state.

## 9. Tooling

* `Xvfb :272 -screen 0 1024x768x24`, `openbox`, `mgba -3` (SDL), `xdotool`
  (XTEST key events), `SDL_AUDIODRIVER=dummy`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python 3: `zlib` to extract the `gbAs` chunk from mGBA `.ss1` files
  (397,312-byte state; IWRAM at 0x19000, EWRAM at 0x21000), `struct` for the
  table/pointer scans, `capstone` for the key-read-site scan.
* Helper scripts used during the session: `ss.py` (savestate RAM dumper),
  `keys.py` (xdotool key driver), `typecode.py` (password entry driver).

## 10. Legal note

No ROM, graphics, audio or extracted game text is redistributed here. Only
addresses, hashes, tables of short developer-authored code words, the recovered
algorithm, and my own generated codes are published.
