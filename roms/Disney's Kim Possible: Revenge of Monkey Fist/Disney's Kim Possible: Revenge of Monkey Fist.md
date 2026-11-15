# Disney's Kim Possible: Revenge of Monkey Fist (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Disney's Kim Possible: Revenge of Monkey Fist.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `KIM POSSIBLE` |
| Game code | `AEYE` |
| Maker | `4Q` |
| Version | 0 (Rev.00) |
| MD5 | `98ecdff2743665b2ab48147663b81b56` |
| SHA-1 | `1b8d09a885a7c407ad395616c12ffc53ab5d6c3d` |
| SHA-256 | `be0c53152abc02da4ab24713d4264fd7c51bee62877503c89f895cfff19b2113` |
| Complement check | stored `0x46`, computed `0x46` (valid) |
| Header checksum | stored `0x0000` (rebuilt-header artefact; complement byte is valid) |
| Entry word | `0xEA1FF66E` |
| Embedded GBA headers | exactly one (no multi-game shell) |

**Patch / trainer note (important).** The entry branch does **not** go to the stock
`0x080000C0` crt0. It goes to `0x087FD9C0`, an appended ARM loader that runs a custom
LZ bit-stream decoder from `0x087FDB60` into EWRAM `0x02000000` and jumps to
`0x02000001`. What runs is a **Mode7 cracktro**: observed screens read
`MODE7 PRESENTS`, `BRINGS THE SITCH BACK ON YOUR GBA SCREEN. DISNEY'S KIM POSSIBLE
GET BUENA VISTA`, `EXCLUSIVE MUSIC PERFORMED BY: MANTONX`. The trojan then warm-boots
the stock `0x080000C0` crt0; the Digital Eclipse logo and the game run normally.
There is no trainer menu and no key-patch: the stock code path and every address in
this report were verified against stock behaviour (the cracktro only occupies the
top ~9 KiB of the image). No header field other than the entry word and the
rebuilt header checksum differs from a stock header.

## 2. Executive summary

The game has a **7-slot portrait password screen** on the main menu. Each of the
seven slots cycles through exactly **8 portraits** (Kim, Monkey Fist, Dr. Drakken,
Guard, Shego, Ron, Wade, Rufus), so the raw input space is **8^7 = 2,097,152**
strings. The design is the "level password" system advertised on GameFAQs/IGN.

The validator at `0x08002688` is a **bit-plane packer plus a one's-complement
3-bit checksum**:

* slots 1–3 carry three 3-bit fields (level `A`, continues `B`, chapter `C`) in
  bit-planes 0/1/2;
* slots 4–6 carry the 8-bit picture-unlock mask `E` (planes 1/0) and the 3-bit
  checksum bit-plane 2;
* slot 7 contributes the top two bits of `E`;
* valid iff `checksum == 7 & ~((A+B+C+t) & 7)`.

Exactly **262,144** of the 2,097,152 strings pass (1 in 8), and they realise
**131,072 distinct effects**; every effect has exactly **two spellings**, because
one bit of slot 7 (bit 2) is never used. The fields control: chapter start
(`C`, 0–7), number of continues (`B+1`, 1–8), the 8-picture gallery mask (`E`),
and a level/resume counter (`A+1`, 1–8). The chapter's password also pre-unlocks a
number of movies derived from `C` (1,1,1,2,3,4,4,5 movies for `C`=0…7).

The published "Easy Mode" password list is **largely wrong for this image**: of the
eight published entries only **two** satisfy the ROM's checksum and are accepted by
the game (the Level-3 and Level-6 rows); the Level-2 row was typed into the game and
rejected with `INCORRECT`. The other five rows fail the ROM's own checksum. Five
unpublished codes were minted from the recovered algorithm and accepted in mGBA,
including all-8-pictures, 8 continues, and chapter 7 (Dr. Drakken's Lair).
Bounds were proven by in-game rejection of a checksum-bad string and by the
selector's `& 7` masking (no symbol outside 0–7 is representable).

## 3. How to reproduce

* Emulator: `mgba` 0.10.5 (SDL), `SDL_AUDIODRIVER=dummy`, `Xvfb :327 -screen 0 1024x768x24`.
* Default mGBA keymap used: **A = `x`**, **B = `z`**, **Start = `Return`**,
  D-pad = arrows. Hold 70–200 ms; a 70 ms tap moves a menu cursor exactly one slot.
* Path: title → `Start` → main menu → `Down Down` → `PASSWORD` → `A`.
  On the password screen `Left`/`Right` move the cursor, `Up`/`Down` cycle the
  selected portrait (`(v-1)&7` / `(v+1)&7`), **`A` or `Start` submits**, `B` exits.
* A correct code prints `CORRECT`; `B` then starts the chapter at the map screen.
  A wrong code prints `INCORRECT`. The **all-Kim default also prints CORRECT** — the
  caller treats "sum of all symbols == 0" as "no password" and skips the validator.
* In-game `Start` opens the pause menu: `CONTINUE / PICTURES / MOVIES / QUIT`.
  The bottom row of that screen shows the **current password re-encoded from live
  progress** (`0x02011A68`), so the game tells you its own spelling of the state.

Codes used for the evidence below (indices are portrait indices, 0–7):

| Purpose | Code (slot 1→7) | Result |
|---|---|---|
| Published Level 2 | `7 6 0 4 0 0 0` | **INCORRECT** |
| Published Level 3 | `5 2 0 2 4 1 0` | CORRECT → Middleton High School |
| Published Level 6 | `7 6 1 6 2 0 0` | CORRECT → Monkey Temple Ruins |
| Novel, chapter 0 | `0 0 0 4 4 4 0` | CORRECT → Downtown Middleton |
| Novel, all pictures | `0 0 0 3 3 3 3` | CORRECT → 8/8 pictures |
| Novel, picture 2 only | `0 0 0 4 2 4 0` | CORRECT → pic 1 locked, pic 2 open |
| Novel, max state | `7 7 7 7 7 3 3` | CORRECT → Draken's Lair, 8 continues, 5 movies, 8 pictures |
| Alias check | `0 0 0 4 4 4 4` | CORRECT, identical to `… 0` |

## 4. Address map

| Address | Kind | Role |
|---|---|---|
| `0x0800CA0C` | Thumb func | Password-screen update/draw. Builds the 7-byte buffer at `sp+12` (= `0x03007DB8`), reads `0x020006E8` key shadow, cycles slots, calls the submit wrapper on A/Start (bit 0/bit 3), exits on B. |
| `0x0800CA8E..0x0800CABE` | code | Slot cycle: `(v-1)&7` (Up) / `(v+1)&7` (Down) — proves the alphabet is exactly 0–7. |
| `0x0800C948` | Thumb func | Submit wrapper: `sum = Σ slots[i] & 0xFF`; `sum==0` → returns 1 without validating; else calls `0x08002688`, plays SFX `0x08767EF4`, and returns its boolean. |
| `0x08002688` | Thumb func | **Validator.** Packs bit-planes, checks the checksum, writes the five progress words, returns 1/0. |
| `0x080027D4` | jump table | 8 pointers indexed by field `C` (chapter) selecting the movie-mask constant `{1,1,1,3,7,15,15,31}`. |
| `0x08002574` | Thumb func | Progress → password (re-)encoder; writes 7 bytes to `0x02011A68` (pause-screen row). |
| `0x0800C9B4..0x0800CA00` | code | Draws CORRECT (`0x08166DE0`) / INCORRECT (`0x08166DE8`) via pointers `0x0876AA74` / `0x0876AA70`, waits for B. |
| `0x0800CC00` | Thumb func | Main-menu handler (string table `0x0876AA40`). |
| `0x0800DAC0` | Thumb func | PICTURES screen: `if (!(mask & (1<<index))) draw "NOT AVAILABLE"`, mask at `0x02000B0C`. |
| `0x0800DC94` | Thumb func | MOVIES screen: counts set bits of `0x02000B00` (bits 0–6) and lists that many titles (`0x0876AD60`). |
| `0x08001100` | Thumb func | Game-over/continue screen: decrements `0x020006CC`; that is the continues counter. |
| `0x080054E2` | code | Level loader gate reading `0x02000B08` (`if level < 0` spin/transition). |
| `0x0876AA40` | ROM table | UI string-pointer table (START, OPTIONS, PASSWORD, MOVIES, PICTURES, … CORRECT, INCORRECT). |
| `0x08768508` | ROM table | 10 level-name pointers, story order descending (MIDDLETON … MONKEY RUINS, with `?????` and two blanks). |
| `0x0876AD60` | ROM table | 7 movie-title pointers `MOVIE 1..7`. |
| `0x03007DB8` | IWRAM | 7-byte entry buffer (stack local of `0x0800CA0C`). |
| `0x02000B08` | EWRAM | `A+1` — level/resume counter (read at `0x080054E2`). |
| `0x020006CC` | EWRAM | `B+1` — continues (decremented at `0x08001100`). |
| `0x020006D0` | EWRAM | `C` — chapter index (byte). |
| `0x02000B00` | EWRAM | `table[C]` — movie-unlock bitmask (script flag word; also set by script opcodes). |
| `0x02000B0C` | EWRAM | `E` — 8-bit picture-unlock mask. |
| `0x02011A68` | EWRAM | 8-byte re-encoded "current password" buffer. |
| `0x020006E8` | EWRAM | key shadow (active-high: A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80). |
| `0x02016258` | EWRAM | byte set to 1 by the validated path, 0 by the all-Kim path. |

File offsets: ROM address = `0x08000000 + file offset`. The validator is file
`0x2688`, the screen handler file `0xCA0C`.

## 5. Algorithm

```
slots s[0..6], each 0..7 (portrait index, left to right)

A = (s0 & 1) | ((s1 & 1) << 1) | ((s2 & 1) << 2)          # bit-plane 0 of slots 1-3
B = (s0>>1 & 1) | ((s1>>1 & 1) << 1) | ((s2>>1 & 1) << 2) # plane 1
C = (s0>>2 & 1) | ((s1>>2 & 1) << 1) | ((s2>>2 & 1) << 2) # plane 2

t   = (s3>>1 & 1) | ((s4>>1 & 1) << 1) | ((s5>>1 & 1) << 2)  # E bits 0-2
b3  = (s3 & 1)    | ((s4 & 1)    << 1) | ((s5 & 1)    << 2)  # E bits 3-5
chk = (s3>>2 & 1) | ((s4>>2 & 1) << 1) | ((s5>>2 & 1) << 2)  # stored check (plane 2)

E = t | (b3 << 3) | ((s6 & 3) << 6)                        # s6 bit 2 unused

valid  iff  chk == (7 & ~((A + B + C + t) & 7))
```

On success (`0x08002688`, in this order):

```
0x02000B08 = A + 1                       # level / resume counter
0x020006CC = B + 1                       # continues
0x020006D0 = C                           # chapter
0x02000B00 = {1,1,1,3,7,15,15,31}[C]     # movie mask (jump table 0x080027D4)
0x02000B0C = E                           # picture mask, bit i = picture i+1
return 1
```

The caller (`0x0800C948`) independently computes `sum = Σ s[i] mod 256` first:
`sum == 0` (all-Kim) short-circuits to "accepted" and starts the default chapter
without touching the progress words. Otherwise the value above decides
`CORRECT`/`INCORRECT`.

Encoder (verified against the ROM; also in `kp.py`):

```
s0..s2 : bit i of si = bit i of A, bit i of B, bit i of C (packed as 3 bits)
t=E&7; b3=(E>>3)&7; s6=(E>>6)&3
chk = 7 & ~((A+B+C+t)&7)
s3 = ((t&1)<<1)|(b3&1)|((chk&1)<<2), s4/s5 likewise for bits 1 and 2
```

## 6. Tables

### 6.1 Portrait alphabet (slot value → portrait)

| Index | Portrait | Notes |
|---:|---|---|
| 0 | Kim Possible | default |
| 1 | Monkey Fist | pointy-eared, wide monkey grin; the published Level-6 row validates with this index in its "Monkey" slot |
| 2 | Dr. Drakken | green face |
| 3 | Guard | dark-haired, big grin (by elimination against the published list) |
| 4 | Shego | black hair, headband |
| 5 | Ron Stoppable | blond |
| 6 | Wade Load | blue face, glasses |
| 7 | Rufus | pink naked mole rat |

The index is all that matters to the algorithm; indices 0/2/4/5/6/7 are pinned by
the in-game acceptance of the novel codes below, 1 and 3 are pinned to
Monkey/Guard by the published Level-6 row and elimination.

### 6.2 Chapter field `C` (observed title cards / map labels)

| `C` | Chapter | Title card |
|---:|---|---|
| 0 | Downtown Middleton | `DOWNTOWN DILEMMA!` |
| 1 | Middleton High School | `MIDDLETON HIGH HIGH-JINKS!` |
| 2 | Camp WannawEEP | `RETURN TO CAMP WANNAWEEP!` |
| 3 | Monkey Temple Ruins | world-map label `Monkey Temple Ruins` |
| 4 | Space Station | `SITUATION ON THE SPACE STATION!` |
| 5 | Paris | `PERILS IN PARIS!` |
| 6 | Factory | `FACTORY FOOLERY!` |
| 7 | Dr. Drakken's Lair | `DR. DRAKKEN'S EVIL LAIR!` |

The story-order pointer table at `0x08768508` (index 9 → 0) is
`MIDDLETON, FACTORY, HIGH SCHOOL, ?????, SPACE STATION, CAMP WANNAWEEP, PARIS,
MONKEY RUINS`, i.e. the on-screen chapter ids are not in story order.

### 6.3 Movie mask (`table[C]` at `0x02000B00`, popcount = movies listed)

| `C` | mask | movies |
|---:|---:|---:|
| 0,1,2 | 1 | 1 (observed for `C`=1) |
| 3 | 3 | 2 |
| 4 | 7 | 3 |
| 5,6 | 15 | 4 |
| 7 | 31 | 5 (observed) |

### 6.4 Field widths / values

| Field | Source | Width | Range | Effect |
|---|---|---:|---|---|
| A | plane 0 of slots 1–3 | 3 | 0–7 | `0x02000B08 = A+1` (level/resume) |
| B | plane 1 of slots 1–3 | 3 | 0–7 | `0x020006CC = B+1` continues |
| C | plane 2 of slots 1–3 | 3 | 0–7 | chapter |
| E | plane 1/0 of slots 4–6 + bits 0–1 of slot 7 | 8 | 0–255 | picture mask |
| chk | plane 2 of slots 4–6 | 3 | 0–7 | checksum |
| – | slot 7 bit 2 | 1 | 0–1 | **unused** (alias bit) |

### 6.5 Published password list vs this ROM

| Row | Slots 1→7 | Model | In-game |
|---|---|---|---|
| Level 2 | 7 6 0 4 0 0 0 | checksum 1 ≠ 0 → reject | **INCORRECT** (tested) |
| Level 3 | 5 2 0 2 4 1 0 | valid (A=1,B=2,C=1,E=33) | CORRECT → Middleton High School |
| Level 4 | 7 2 0 4 2 1 0 | reject (chk 1 ≠ 0) | not typed |
| Level 5 | 0 6 1 6 4 1 0 | reject (chk 3 ≠ 1) | not typed |
| Level 6 | 7 6 1 6 2 0 0 | valid (A=5,B=3,C=3,E=3) | CORRECT → Monkey Temple Ruins |
| Level 7 | 5 3 1 3 4 5 0 | reject (chk 6 ≠ 3) | not typed |
| Level 8 | 7 2 1 6 2 5 5 | reject (chk 5 ≠ 7) | not typed |
| All pictures | 5 0 0 3 3 3 3 | reject (chk 0 ≠ 6) | not typed |

Six of eight rows are invalid for this revision, and the two that work decode to
chapters 1 and 3, not to the published "levels". The list is therefore not a
reliable description of this SKU; only the two accepted rows are evidence of the
format.

## 6b. Enumeration

**Space.** 7 slots × 8 portraits = **2,097,152** representable inputs
(`8^7`). The validator accepts exactly **262,144** (`2^18`, 1 in 8) — enumerated
exhaustively with the recovered model (`enumerate.py`, full 8^7 sweep):

```
total inputs      2,097,152
valid codes         262,144
distinct effects    131,072   (A,B,C,E tuples)
aliases per effect        2   (s6 bit 2 is ignored)
```

**Reachability.** For every `(A,B,C)` all 256 values of `E` are reachable, because
`t`, `b3` and `s6&3` are free and the checksum adapts to `t`. Hence the behaviour
space is 8 × 8 × 8 × 256 = 131,072 states, each writable by exactly two strings.

**Novel codes (in no published list) and their in-game proof**

| # | Slots 1→7 | State | Observation |
|---:|---|---|---|
| 1 | `0 0 0 4 4 4 0` | A=0,B=0,C=0,E=0 | `CORRECT`; world map `Downtown Middleton`; chapter card `DOWNTOWN DILEMMA!`; new game state reached |
| 2 | `0 0 0 3 3 3 3` | A=0,B=0,C=0,E=255 | `CORRECT`; PICTURES browser: picture 1 and picture 2 both render (no `NOT AVAILABLE`), i.e. all 8 gallery bits set |
| 3 | `0 0 0 4 2 4 0` | E=2 | `CORRECT`; picture 1 = `NOT AVAILABLE`, picture 2 = playable → proves bit *i* ↔ picture *i+1* |
| 4 | `7 7 7 7 7 3 3` | A=7,B=7,C=7,E=255 | `CORRECT`; world map `Draken's Lair`; pause MOVIES lists `MOVIE 1..5`; pause HUD continue counter shows 8; PICTURES opens from picture 1 |
| 5 | `0 0 0 4 4 4 4` | same as #1 | `CORRECT`; proves the unused slot-7 bit 2 (alias) |

Screenshots kept in `/tmp/opencode/kp1`: `t1.png` (#1 `CORRECT`), `t2.png` (#1 map),
`u2.png`/`u4.png`/`u5.png` (#2 `CORRECT` and pictures 1–2), `e2p1.png`/`e2p2.png`
(#3 locked/open), `full_res.png`/`full_map.png`/`full_movies.png` (#4),
`alias_res.png` (#5), `s14.png`/`s16.png` (published Level 2 rejected),
`l3res.png`/`l3map.png` and `l6.png` (published rows accepted).

**Bounds proven by rejection.**

* Bad checksum inside a well-formed string: `7 6 0 4 0 0 0` (all symbols legal)
  → `INCORRECT` in mGBA (`s14.png`, `s16.png`). The same string also fails the
  reimplemented checksum (expected check 0, stored 1).
* Out-of-range symbol: not expressible. The selector applies `(v±1)&7`
  (`0x0800CABA`–`0x0800CABE`), so only 0–7 can ever be submitted; the screen has no
  path to an eighth value. The string `8 …` therefore cannot be entered at all.
* Reserved bit: slot 7 bit 2 never reaches any comparison (it only lands in the
  high bits of `0x02000B0C`), and both spellings of the same state are accepted.

## 7. Validation evidence

**Observed (emulator / memory)**
* `CORRECT` / `INCORRECT` for every code in §6.5 and §6b, typed on the real screen.
* Chapter title cards and world-map labels for `C`=0,1,2,4,5,6,7 (and the Monkey
  map label for `C`=3).
* PICTURES: `NOT AVAILABLE` with E=0, picture 1 open with E=1-bit-set behaviour
  (E=2 opened picture 2 and left picture 1 locked), pictures 1–2 open with E=255.
* MOVIES: 1 title with `C`=1 and 5 titles with `C`=7.
* Pause HUD continue digit 1 with B=0 and 8 with B=7.
* RAM after the `A=5,C=0` code: `0x02000B08=6`, `0x020006CC=1`, `0x020006D0=0`,
  `0x02000B00=1`, `0x02000B0C=0`, `0x02011A68 = 01 00 01 00 04 00 00`.
* Watchpoint on `0x03007DB8` fired on slot change from the handler at `0x0800CAC2`
  with `r0 = 0x03007DB8`, `r7 = cursor`, confirming the buffer address/semantics.
* Breakpoint at `0x0800CB00` (before the validator call) read the exact submitted
  bytes `07 06 00 04 00 00 00` for the published Level-2 string.
* Breakpoint at `0x08002796` (`cmp r0,r3`) for `0 0 0 1 1 1 1` showed
  `r0 = 5` (expected check) vs `r3 = 0` (stored) — exactly what the model predicts
  (`A=1,B=0,C=1,t=0 → 7&~2 = 5`).

**Derived (disassembly)**
* Field extraction, checksum, the five stores, and the chapter jump table from
  `0x08002688`/`0x080027D4`.
* Picture and movie screens read `0x02000B0C` / count bits of `0x02000B00`.
* Continue screen decrements `0x020006CC`.

**Inferred**
* `A` is a level/resume counter: it is stored as `A+1` and read as a `>=0` gate by
  the level loader, but `A`=0, 5 and 7 in two different chapters opened the same
  first room, so its visible effect was not isolated.
* Identity of portraits 1/3 (Monkey/Guard) rests on the published Level-6 row
  (which the ROM accepts with index 1 in its "Monkey" slot) plus elimination.

## 8. Unknowns

* Exact consumer of `A` (likely checkpoint/resume within a chapter); not isolated.
* Whether `0x020006D0` is read directly or through a struct base; the chapter
  mapping is observational.
* Origin of the published list (six of eight rows do not match this image's
  checksum; possibly another revision/region or transcription errors).
* The cracktro payload's internals (irrelevant to the game analysis).
* No hidden debug menu, no button-code (key-sequence) cheat and no sound-test were
  found: strings contain zero `debug`/`cheat`/`secret` hits, the only menus are
  title/main/options/password/pause/pictures/movies, and the password screen is the
  only code-entry surface.

## 9. Tooling

* `mgba` 0.10.5 (SDL) under `Xvfb :327` + `openbox`, `SDL_AUDIODRIVER=dummy`.
* mGBA **command-line debugger** (`mgba -d`, driven through a private `tmux -L kp1`
  session) for read/change watchpoints, breakpoints, register/memory reads and
  manual validator calls — used instead of the GDB stub (the stub in this build did
  not answer `qSupported`).
* `arm-none-eabi-objdump -M force-thumb`, Python 3 + `capstone`.
* mGBA savestates parsed as PNG with a zlib `gbAs` chunk (EWRAM at `0x21000` of the
  raw 397,312-byte state) to diff RAM without a debugger.
* Scripts in `/tmp/opencode/kp1`: `kp.py` (decoder/encoder), `enumerate.py`
  (full 8^7 sweep), `run_code2.py`/`batchA.py`/`batchC.py` (input harness),
  `drv.py` (debugger driver), `phase0.py` (header).

## 10. Legal note

No ROM, graphics, music or game text is redistributed here. Only hashes,
addresses, algorithms and the author's own generated codes are published.
