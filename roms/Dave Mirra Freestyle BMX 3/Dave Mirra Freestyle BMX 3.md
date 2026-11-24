# Dave Mirra Freestyle BMX 3 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Dave Mirra Freestyle BMX 3/Dave Mirra Freestyle BMX 3.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `DAVE MIRRA 3` |
| Game code | `AB3E` (USA) |
| Maker | `51` (`0x35 0x31`) |
| Version | 0 |
| Complement byte | `0xE2` (matches computed value) |
| Header checksum field | `0x0000` (zeroed — header was rebuilt; complement is valid) |
| Entry word | `0xEA00002E` (stock GBA branch to `0x080000C0`) |
| Logo | intact, single hit at file offset `0x04` |
| Embedded-header scan | exactly one Nintendo logo in the image → single ROM, no pack |
| MD5 | `bce3926504e6fbc983463aa238ee5faf` |
| SHA-1 | `dcce47b536ace90a918d94d06698c92538d7e4d1` |
| SHA-256 | `c20d61f5f8524ee33b73697128143b0ab211996bc0972e03178446691ecf691d` |

No cracktro, trainer or patched entry branch: the entry word is the stock
`b 0x080000C0`, the first 4 KiB contains only the stock crt0/vector table, and
there is no ASCII banner in it. The only header anomaly is the zeroed checksum,
which is the expected artifact of a rebuilt-but-stock header (the complement
byte is correct).

## 2. Executive summary

This GBA SKU is a Full Fat production and a different game from the console
versions. It has **no password system and no cheat/debug menu**. It does have a
**title-screen button-code system** with **two wired 8-step codes**, a **third
code table that is dead data**, and (separately) a **4-step code in the
pause/replay overlay** that is present in code but whose screen was not reached
in this session.

The two live title codes are:

| Code (title screen) | Effect | Published? |
|---|---|---|
| `Down, Up, Down, Up, Left, Right, B, R` | Tiny-rider flag | Yes (guide/FAQ, in-game hint) |
| `R, R, L, L, B, B, L, R` | Unlock-all-riders profile field + max all 10 rider stats | Yes (in-game hint) |

The ROM's own end-of-game hint pages spell out both sequences literally
(`0x7B36D0`…`0x7B3724` and `0x7B39D4`…`0x7B3A24`), which anchors the sequences
independently of any fan list.

This sequel fixes the sibling's dead latch: the tiny-rider byte written by the
first code **has a reader** at `0x08040B1E` (it selects a camera/scale constant
`0x17C` vs `0xB4`). The second code writes the real profile field
`+0x1702` (`0x0008 → 0x000A`) and sets ten 0x80-byte rider records' `+0x18`
stat field from `1` to `0x3F`; both were RAM-verified.

A whole-ROM scan finds exactly three 8-entry key-mask tables; the third
(`0x080582A4`, `L,B,R,B,L,L,R,B`) has **zero** references in the image and its
sequence is rejected in the emulator. The widely published
`L,R,L,R,B,B,R,L` "all places" code is not present and is rejected; the real
first code is `R,R,L,L,B,B,L,R`.

A **15-press composite that is in no published list**
(`D,U,D,U,Left,Right,B,R, R,L,L,B,B,Left,R`) was generated from the validator
model, entered on the real title screen, and RAM-verified to set the tiny flag
and the all-riders/max-stat profile in the same run.

## 3. How to reproduce

Emulator: mGBA (SDL) under `Xvfb :281` + `openbox`, `SDL_AUDIODRIVER=dummy`,
3× scale. Keymap used: **A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`**, D-pad = arrow keys. Hold keys ~100 ms, gap ~350 ms for
code entry; the edge detector misses very short taps and the code matcher
rejects two keys that share a frame.

Observed path from a cold boot (no save):

1. Boot; wait for the title screen (`PRESS START` pointer at IWRAM
   `0x03007C8C`; the title alternates with an attract demo).
2. Enter a title code directly at `PRESS START` (do not open any menu).
3. Read `[0x030016D0]` and `[0x03001740]` from IWRAM:
   - profile `+0x1702`: baseline `0x0008`;
   - tiny flag `[0x03001740]+0xDD6`: baseline `0x00`.
4. The exact test protocol used: savestate the `PRESS START` screen, reload it
   (`F4`) before each test, enter the sequence, then savestate and read IWRAM.

Code entry needs one extra detail: the first key of a code may be consumed by
the 0x03000131 timer, so the clean protocol is to reload the title state and
wait ~0.4 s before the first press. The accepted run is reproducible from the
same savestate (see §7).

Pause menu: from gameplay press `Return` (`Start`); RAM-verified items are
`RESUME`, `SOUNDTRACK`, `EXIT` (string pointers `0x87AF510`, `0x87B3BB0`,
`0x87B3BA8` observed in EWRAM). A separate pause/replay overlay handler exists
at `0x08042D3C` and draws `PAUSE` (`0x7B3C44`).

## 4. Address map

| ROM address | File offset | Meaning |
|---|---|---|
| `0x0803025C` | `0x3025C` | Screen-state handler; case 1 is the title/attract screen |
| `0x080303DC` | `0x303DC` | Per-step 0x03000131 timer gate (128 frames) |
| `0x080303EA` | `0x303EA` | Reads the pressed-edge word `0x03006080` |
| `0x080303F4` | `0x303F4` | **Matcher 1** (table `0x08058284`, progress `0x0300012E`) |
| `0x08030410` | `0x30410` | Matcher-1 completion: writes tiny flag |
| `0x0803041E` | `0x3041E` | `[0x03001740] + 0xDD6 = 1` |
| `0x08030460` | `0x30460` | **Matcher 2** (table `0x08058294`, progress `0x0300012D`) |
| `0x08030480` | `0x30480` | Matcher-2 completion |
| `0x08030490` | `0x30490` | `+0x1702 = 0x000A`; ten records `+0x18 = 0x3F` |
| `0x0804C9B8` | `0x4C9B8` | Key poll: `pressed = held & ~prev`, stores `0x03006080` |
| `0x0804C9CE` | `0x4C9CE` | Stores `prev = held` at `0x03006084` |
| `0x03006080` | IWRAM `0x6080` | Pressed-this-frame edge word (active-high) |
| `0x03006084` | IWRAM `0x6084` | Held/previous-frame word (idle `0xFC00`) |
| `0x0300012E` | IWRAM `0x12E` | Matcher-1 progress (0..8) |
| `0x0300012D` | IWRAM `0x12D` | Matcher-2 progress (0..8) |
| `0x03000131` | IWRAM `0x131` | Step timer, reset to `0x80` on match/mismatch |
| `0x08058284` | `0x58284` | **T1** 8×u16 mask table (tiny) |
| `0x08058294` | `0x58294` | **T2** 8×u16 mask table (all riders/stats) |
| `0x080582A4` | `0x582A4` | **T3** 8×u16 mask table — zero references |
| `0x03001740` | IWRAM `0x1740` | Pointer to current game-state object `0x0200D8E4` |
| `0x030016D0` | IWRAM `0x16D0` | Pointer to profile object `0x020125BC` |
| `0x08040B1E` | `0x40B1E` | Tiny-flag reader: selects `0x17C` vs `0xB4` |
| `0x080427C4` | `0x427C4` | End-of-game path that also writes `+0x1702 = 10` |
| `0x08042D3C` | `0x42D3C` | Pause/replay overlay handler |
| `0x0804311A` | `0x4311A` | 4-step overlay-code completion (`obj+0x14 = 0x3FF`) |
| `0x0806C700` | `0x6C700` | 4×u16 overlay-code table (`Up, Left, L, R`) |

Key masks (active-high, matches `0x03006080`):
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200`.

## 5. Algorithm

### 5.1 Key poll (`0x0804C9B8`)

```
cur  = ~REG_KEYINPUT & 0xFFFF          # idle 0xFC00
prev = [0x03006084]
[0x03006080] = cur & ~prev              # pressed edges, exact-match source
[0x03006088] = prev
[0x03006084] = cur
```

### 5.2 Title-screen code matcher (`0x080303DC`…`0x08030460`)

```
if [0x03000131] == 0:                   # window expired
    [0x03000131] = 0x80
    [0x0300012D] = 0                   # reset both programs
    [0x0300012E] = 0
    return
[0x03000131] -= 1

key = [0x03006080]                      # pressed edges only
if key == 0: return

# program 1
if key == T1[[0x0300012E]]:
    [0x0300012E] += 1
    if [0x0300012E] == 8:
        [0x0300012E] = 0
        [0x03000131] = 0x80
        play_sound(7)
        [ [0x03001740] + 0xDD6 ] = 1     # tiny-rider flag
        goto program2                     # same-frame fall-through
else:
    [0x0300012E] = 0
    [0x03000131] = 0x80

# program 2
if key == T2[[0x0300012D]]:
    [0x0300012D] += 1
    if [0x0300012D] == 8:
        [0x0300012D] = 0
        [0x03000131] = 0x80
        play_sound(7)
        p = [0x030016D0]
        *(u16*)(p + 0x1702) = 0x000A
        for i in 0..9:
            *(u16*)(p + i*0x80 + 0x18) = 0x3F
else:
    [0x0300012D] = 0
    [0x03000131] = 0x80
```

Notes:

* The comparison is **exact** against the pressed-edge word, not a subset
  test. Extra keys that are already held are tolerated (they produce no edge);
  two keys pressed in the same frame produce a two-bit word and never match.
* Each successful step resets the window to 128 frames (2.13 s at 60 Hz).
* Program 2 runs on the same frame that program 1 completes, so the 8th press
  of T1 (`R`) also advances program 2 by one step (`T2[0] = R`). This is the
  coupling used by the composite code in §6b.

### 5.3 Effects

```
tiny flag:  [0x03001740]+0xDD6 = 1
reader:     0x08040B1E: ldrb r0,[p2+0xDD6]; r1 = r0 ? 0xB4 : 0x17C
            -> 0x08041A60(0x030016E0, r1)

profile:    [0x030016D0]+0x1702 = 10           (0x0008 -> 0x000A)
            for i in 0..9: p1[i*0x80+0x18] = 0x3F   (1 -> 63)
```

The same `+0x1702 = 10` write exists in the first-completion message path at
`0x080427C4`, i.e. finishing the game once performs the profile half of the
cheat without the stat maxing.

## 6. Tables

### 6.1 Title code T1 — tiny riders (`0x08058284`, 16 bytes)

Raw: `80 00 40 00 80 00 40 00 20 00 10 00 02 00 00 01`

| # | Mask | Button |
|---:|---:|---|
| 1 | `0x080` | Down |
| 2 | `0x040` | Up |
| 3 | `0x080` | Down |
| 4 | `0x040` | Up |
| 5 | `0x020` | Left |
| 6 | `0x010` | Right |
| 7 | `0x002` | B |
| 8 | `0x100` | R |

In-game hint (credits/message page C): `DOWN, UP, DOWN, UP,` /
`LEFT, RIGHT, B BUTTON` / `R BUTTON...` at `0x7B39F8`/`0x7B39E0`/`0x7B39D4`.

### 6.2 Title code T2 — all riders + max stats (`0x08058294`, 16 bytes)

Raw: `00 01 00 01 00 02 00 02 02 00 02 00 00 02 00 01`

| # | Mask | Button |
|---:|---:|---|
| 1 | `0x100` | R |
| 2 | `0x100` | R |
| 3 | `0x200` | L |
| 4 | `0x200` | L |
| 5 | `0x002` | B |
| 6 | `0x002` | B |
| 7 | `0x200` | L |
| 8 | `0x100` | R |

In-game hint (message page A): `R BUTTON, R BUTTON,` / `L BUTTON, L BUTTON,` /
`B BUTTON, B BUTTON,` / `L BUTTON, R BUTTON...` / `TO UNLOCK ALL RIDERS...` /
`...ALL LEVELS,` at `0x7B3710`…`0x7B36A8`.

### 6.3 Dead table T3 (`0x080582A4`, 16 bytes)

Raw: `00 02 02 00 00 01 02 00 00 02 00 02 00 01 02 00`

Decoded: `L, B, R, B, L, L, R, B`.

Whole-ROM u32 literal scan: **0** references to `0x080582A4`. The only
references to the table region are the two literals used by the matcher
(`0x08030448` → `0x08058284`, `0x080304B4` → `0x08058294`); the code never
computes `base+0x20`. The sequence was entered at the title and rejected
(§6b). T3 is therefore a cut/unused third cheat, not a hidden code.

### 6.4 Pause/replay overlay code (`0x0806C700`, 8 bytes) — derived

Raw: `40 00 20 00 00 02 00 01` → `Up, Left, L, R`.

Referenced only from the overlay handler at `0x08043148`. Matcher state is
stack-local (`[sp+0xA8]` index, `[sp+0xAC]` 0xC0-frame arming timer); a mismatch
arms the timer, and on 4 matches `0x0804311A` calls `0x080408A8(0xC4)` and, if
that returns 0, writes `0x3FF` to `obj+0x14` (`obj = 0x0804071C()`) and sets
the timer to 0xC0. The overlay handler draws the `PAUSE`/`IN PAUSA` strings at
`0x7B3C44`/`0x7B3C4C`. This is a real code table, but the replay/pause overlay
that owns it was not reached from the observed menus (the `Start` pause menu is
a different, 3-item screen); see §8.

### 6.5 Menus observed (RAM label pointers)

| Screen | Items (RAM-verified pointers) |
|---|---|
| Title | `PRESS START` |
| File/PROQUEST menu | `continue game`, `new game`, `load game` (0 or 2/3 items depending on save) |
| Rider select | `continue`, `create a rider`, `select bike`, `edit stats`, `bio`, `trick book` |
| In-game pause | `RESUME`, `SOUNDTRACK`, `EXIT` |
| Options/other | parent list contains `PROQUEST`, `SESSION`, `FREERIDE`, `MULTIPLAYER`, `GAME OPTIONS` |

No `debug`, `password`, `secret menu`, or cheat-menu string exists. `CHEAT`
occurs only in the score-rating table (`CHEATING 2160`,
`REALLY CHEATING 2340`, `0x7B1F74`/`0x7B1F5C`) and in the two end-of-game hint
pages. The only text-entry alphabet in the ROM is a 36-symbol lowercase
alphabet at `0x5BD24` (`abcdefghijklmnopqrstuvwxyz0123456789`) used by the
name-entry/create-a-rider screen; no validator compares user text, so it is a
name field, not a password field (§16.2b).

## 6b. Enumeration

**Space definition.** The title system is two fixed lookup tables of eight
u16 key masks. Each accepted step is one of the ten GBA buttons (single-bit
edge), so the representable input stream space is `10^8 = 100,000,000`
ordered 8-press streams ignoring timing; timing adds a 128-frame per-step
window. There is no checksum, no alphabet and no payload -- the tables *are*
the whole code space. Exactly **two** 8-step tables are wired; a third
8-step table exists as dead data.

**Accepted set (in-game).**

| Input (title screen) | Progress evidence | Effect evidence |
|---|---|---|
| `D,U,D,U,Left,Right,B,R` (T1) | `0x0300012E: 1..7 → 0`; `0x0300012D` advances to 1 via fall-through | `[0x03001740]+0xDD6: 0x00 → 0x01` |
| `R,R,L,L,B,B,L,R` (T2) | `0x0300012D: 1..7 → 0` | `[0x030016D0]+0x1702: 0x0008 → 0x000A`; ten `+0x18` stat words `0x0001 → 0x003F` |

**Novel code (in no published list).** Because T1's last press also advances
T2 by one step, the following 15-press composite triggers **both** wired
codes in one run:

```
Down, Up, Down, Up, Left, Right, B, R,
R, L, L, B, B, L, R
```

This exact 15-press input does not appear on 3rd party cheat indexes
or the 3rd party cheat index mirrors (which list only the 8-press T1/T2
sequences). Entered on the real title screen in mGBA, it produced, in one
run:

* `tiny` = `0x01` at `0x0200E6BA`;
* `+0x1702` = `0x000A` at `0x02013CBE`;
* all ten rider stat words = `0x003F`.

This is an unadvertised combination (tiny riders **and** all riders/max stats),
not merely a replay of a published code.

**Bounds proven by rejection** (each test reloaded the same `PRESS START`
savestate, then entered the sequence at the real title screen):

| Test | Input | Result |
|---|---|---|
| Published "all places" code | `L,R,L,R,B,B,R,L` | tiny `0`, `+0x1702` `8`, stats `1` — rejected |
| Dead table T3 | `L,B,R,B,L,L,R,B` | tiny `0`, `+0x1702` `8`, stats `1` — rejected |
| T1 prefix (7 of 8) | `D,U,D,U,Left,Right,B` | tiny `0` — rejected |
| T1 wrong last step | `D,U,D,U,Left,Right,B,B` | tiny `0` — rejected |
| T2 on the file menu (wrong screen) | `R,R,L,L,B,B,L,R` | `+0x1702` `8`, stats `1` — rejected |
| T2 with an extra press | `R,Down,R,L,L,B,B,L,R` | `+0x1702` `8`, stats `1` — rejected |
| T1 with Select held throughout | `D,U,D,U,Left,Right,B,R` + Select held | tiny `1` — accepted (extra held keys tolerated, no edge) |

The published `L,R,L,R,B,B,R,L` code is **not in the ROM in any encoding**
(u16, u32, byte-mask, reversed) and is rejected; the in-game hint for the same
unlock spells `R,R,L,L,B,B,L,R`.

## 7. Validation evidence

**Observed** (mGBA, RAM reads from decompressed `gbAs` savestates):

* `PRESS START` state has `[0x030016D0]+0x1702 = 0x0008`,
  `[0x03001740]+0xDD6 = 0x00`, all ten `+0x18` stat words `0x0001`.
* T1 entered at the title: tiny byte `0x00 → 0x01`; `0x0300012E` ran `1..7`
  then wrapped to `0`, and `0x0300012D` became `1` (fall-through).
* T2 entered at the title: `+0x1702` `0x0008 → 0x000A`; the ten `+0x18`
  words `0x0001 → 0x003F`; tiny stayed `0`.
* Composite 15-press code: tiny `1`, `+0x1702` `0x000A`, ten stats `0x3F`
  in the same savestate.
* Rejections in §6b left the baseline values unchanged.
* Start opens the 3-item pause menu (`RESUME`, `SOUNDTRACK`, `EXIT`) in
  gameplay; RAM label pointers observed.
* Key poll: holding Down alone produces `0x03006084 = 0xFC80`; idle is
  `0xFC00`. A and B were each confirmed by holding (`0xFC01` = A, `0xFC02` = B).

**Derived** (disassembly, exact bytes):

* Matcher algorithm, exact mask comparison, 0x80-frame timer, progress bytes,
  and both action blocks at `0x080303DC`…`0x080304AE`.
* Tables T1/T2/T3 and the absence of any reference to T3; single logo/header.
* Tiny-flag consumer at `0x08040B1E`.
* 4-step overlay table `0x0806C700` and its completion block at `0x0804311A`.
* End-of-game hint pages and the `+0x1702 = 10` write at `0x080427C4`.

**Inferred**:

* `+0x1702` is a rider/secret count (baseline 8 = eight default riders;
  10 = all ten after the code); `+0x18` is the per-rider stat word.
* The overlay 4-step code is a replay/debug action (camera/state 0x3FF) whose
  owning screen was not reached.
* The published "2 create-a-player slots" wording is a fan description of the
  same all-riders/max-stat write; the observed write is ten 0x80-byte records.

## 8. Unknowns

* The pause/replay overlay code `Up, Left, L, R` (`0x0806C700`) was not entered
  in the emulator: the replay overlay that owns the handler was not reached
  from the observed menus. It is a bounded static finding (one table, one
  reference, one completion block), not a confirmed in-game cheat.
* The exact gameplay meaning of `obj+0x14 = 0x3FF` in that overlay is not
  observed.
* The `SESSION`/`FREERIDE`/`MULTIPLAYER` level-select screens were reached only
  partially; their item lists are not fully enumerated in RAM.
* Whether the composite code's tiny flag persists across a save/load cycle was
  not tested (the image declares no save device in the header and mGBA created
  a zero-length `.sav`).

## 9. Tooling

* `mgba` (SDL) under `Xvfb :281` + `openbox`, `SDL_AUDIODRIVER=dummy`.
* `xdotool` for input; mGBA savestates (`.ssN`) decompressed with Python
  `zlib` (`gbAs` chunk) for RAM reads and diffs.
* `arm-none-eabi-objdump -M force-thumb` for targeted disassembly.
* Python 3 scripts: pointer/string scanner, mask-table scanner, savestate
  loader/differ, code-sequence driver (kept in `/tmp/davemirra3`).
* Web sources checked for published literals: 3rd party cheat indexes; all listed only the 8-press T1/T2
  sequences (plus a rejected `L,R,L,R,B,B,R,L` variant).

No ROM, graphics, music or extracted text is redistributed.
