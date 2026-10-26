# Aggressive Inline (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Aggressive Inline/Aggressive Inline.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title (0xA0–0xAB) | `AGGRESSIVE I` (truncated; full game name is 16 chars) |
| Game code (0xAC–0xAF) | `AILE` |
| Maker code (0xB0–0xB1) | `51` |
| Fixed byte 0xB2 | `0x96` |
| Software version (0xBC) | `0` |
| Complement check (0xBD) | `0x77` (correct for the header bytes) |
| Header checksum (0xBE–0xBF) | `0x0000` (stored; not used by the game) |
| Entry branch (0x00) | `0xEA00002E` (ARM branch to `0x080000C0`) |
| Embedded GBA header scan | One Nintendo-logo hit, file offset `0x4` → one GBA image; **not** a multi-game cart |
| MD5 | `4e8b17bb4b77cd5568b678596c55a8bb` |
| SHA-1 | `df41ef94380e074257424f4725738f2ed7ae68b6` |
| SHA-256 | `a75c9d5f1508dd114749c4418900a745fd075e276da09e2f6778069755510f08` |

The 156-byte Nintendo logo occurs exactly once (`file offset 0x4`), so all addresses
below are direct `0x08000000 + file_offset`.

## 2. Executive summary

This revision has **no password system and no code-entry screen**. The only
developer-intended cheats are four fixed button sequences entered on the
**title screen while “PRESS START” is displayed**. They are implemented as a
literal lookup table plus a small per-frame state machine, not as a password
checksum.

The four accepted sequences and their exact effects are:

| # | Sequence | Effect | Profile write |
|---|---|---|---|
| A | `Up, Down, Up, Down, Left, Right, B, R` | all 14 levels, including the hidden 14th level **ACCLAIM GAMES** | `u32[+0x00] = 0x00003FFF`; `u8[+0x0B] = 14` |
| B | `L, L, B, B, R, R, L, R` | all 18 skaters (10 normal + 8 secret) | `u16[+0x2B2] = 0x0012` |
| C | `L, B, R, B` | levels 0–7 (through **DEADMAN'S SEWER**) | `u32[+0x00] = 0x000000FF` |
| D | `L, L, R, B` | levels 0–10 (through **BOB'S SCRAPYARD**) | `u32[+0x00] = 0x000007FF` |

Three of these (`A`, `B`, `C`) are in the widely published GBA lists. `D` is
printed inside the game's own level-intro text and appears on one old hacking
blog, but not in the mainstream lists. The validator has no free fields, so
there is no unpublished *literal* to mint. The enumeration therefore proves the
four-literal set exactly and demonstrates two unpublished input behaviours:

1. **Slow `L,B,R,B`** — a five-second pause after the first `L` still completes
   the code, because the timeout path clears the 8-press counters but not the
   4-press counters. A five-second pause in `UDUDLRBR` fails.
2. **Composed state** — `UDUDLRBR` followed by `LBRB` produces a state no
   published list describes: the level list has 14 entries, **ACCLAIM GAMES is
   visible but LOCKED**, and only eight levels are unlocked.

Hidden content found and exercised:

* **ACCLAIM GAMES** — a playable 14th level whose level-select art is the AKA
  Acclaim logo. It is absent from the normal 13-level list and from the
  published walkthroughs/cheat lists searched.
* **Eight secret skaters** — CHRISSY, JORDAN, THE CASTAWAY, THE NINJA, METALMAN,
  TUFFGUY, MR. ASTRO and SUPERDUDE (five of them are stat-maxed and THE CASTAWAY
  is 8/8/8/6/6; see §6).

Negative results (bounded, not “not tested”):

* No `password`, `passcode`, `debug`, `secret`, `gallery`, `sound test`, or
  `level select` strings exist in the ROM.
* No password alphabet or code-selection screen exists; the four key-mask
  tables are the complete accepted set.
* The published GBA “Get back juice” pause sequence has no table, no `juice`
  string, and no observable effect in this revision. It is almost certainly a
  copy of a console/PS2/GameCube code.
* Codes entered on the main menu, with an extra button held, or with a 2.5 s
  gap in an 8-press sequence are rejected.

## 3. How to reproduce

### Emulator and display

```bash
mkdir -p /tmp/opencode/inline
Xvfb :128 -screen 0 1024x768x24 &
DISPLAY=:128 openbox &
DISPLAY=:128 SDL_AUDIODRIVER=dummy mgba -3 \
  "/mnt/gbacheats/roms/Aggressive Inline/Aggressive Inline.gba" &
```

mGBA SDL default keymap used here:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

The title screen auto-advances to the attract demo after 900 frames (≈15 s),
and any D-pad/L/R press resets that timer (observed; derived from
`0x0803C8A2`–`0x0803C8C8`). Enter the codes while “PRESS START” is on screen.

### Exact menu path

```
Title (PRESS START)
  -> Start                         : MAIN MENU
     -> PLAY ARCADE
     -> FREESKATE
     -> MULTIPLAYER GAMES
     -> GAME OPTIONS

FREESKATE:
  -> skater stats/select (CHANGE with Left/Right, A accept)
  -> ACCEPT
  -> LEVEL select (Left/Right, A accept, B back)
  -> level loads

PLAY ARCADE:
  -> skater stats/select -> story dialogue -> level with 3:00 timer

GAME OPTIONS:
  -> CONTROL TYPE (A)
     MUSIC VOLUME
     SFX VOLUME
     CREDITS

In-game:
  -> Start = PAUSE (CONTINUE / END RUN)
```

Useful savestate: save at the title with `Shift+F1`, reload with `F1`. This makes
each code test two seconds instead of a full intro replay.

### Entering the codes

Tap each button in order (≈60–100 ms hold, ≈150 ms gap). Long holds also work
(1 s per button was tested successfully), but an extra button held at the same
time (for example A) makes every comparison fail. Enter the 8-press codes with
a gap of **less than 2.5 s** between presses (1.8 s succeeded, 2.5 s failed;
the handler's counter is `0x80` frames ≈2.13 s). The 4-press codes survive a
gap of at least five seconds because their counters are not cleared by the
timeout path (see §5); the exact upper bound was not tested.

### Codes tested in the emulator

All of the following were entered and their effects observed:

* `Up Down Up Down Left Right B R` → 14 levels incl. ACCLAIM GAMES.
* `L L B B R R L R` → 18 skaters incl. the eight secret skaters.
* `L B R B` → 8 levels through Deadman's Sewer.
* `L L R B` → 11 levels through Bob's Scrapyard.
* `L` … 5 s … `B R B` → 8 levels (slow 4-press behaviour).
* `Up` … 5 s … `Down Up Down Left Right B R` → no effect (8-press timeout).
* `Up Down Up Down Left Right B` (7 presses) → no effect.
* `UDUDLRBR` on the main menu → no effect.
* `UDUDLRBR` with A held → no effect.
* `L B R B` at pause (published “Get back juice”) → no effect.
* `L L R R L R Down Up Up Down` at pause/title → no effect.

### Search-space counts (recon)

A `strings -n 4`-equivalent scan (printable ASCII runs of ≥4 bytes) produced
**81,696** runs. Case-insensitive substring classification:

| Keyword | Hits | Classification |
|---|---:|---|
| `password` | 0 | absent |
| `passcode` | 0 | absent |
| `debug` | 0 | absent |
| `secret` | 0 | absent |
| `gallery` | 0 | absent |
| `sound test` | 0 | absent |
| `level select` | 0 | absent |
| `cheat` | 3 | 2 trick-score labels (`CHEATING`, `REALLY CHEATING`), 1 credits header (`TRY OUT THESE CHEATS`) |
| `unlock` | 4 | credits/level-intro hints, all listed in §4 |
| `code` | 2 | two engine error strings (`render code`, `Code needs writing`), not a code screen |
| `bonus` | 1 | `a time bonus for the next level` |
| `extra` | 1 | `EXTRA TIME` HUD label |
| `test` | 2 | `game testers` credit + engine string |

Additional negative checks:

* No `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `abcdefghijklmnopqrstuvwxyz`,
  `BCDFGHJKLMNPQRSTVWXYZ`, or similar alphabet run exists.
* A 4-byte literal-pool scan for every ROM pointer whose target begins with a
  run of ≥3 key masks returned exactly the four tables at `0x0806546C` (plus
  unrelated data/audio false positives, none referenced by the validator).
* `0x03000191` (the sequence cooldown) is written only from inside the
  validator at `0x0803C8FA`–`0x0803CA9C`.
* The title state handler (`0x0803C7A4`) dispatches only states 0, 1, 2 and 7;
  state 1 is the title screen and contains the only key-sequence checks. There
  is no debug-menu branch.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Address / file offset | Meaning |
|---|---|
| `0x0806546C` / `0x6546C` | code table A (8 × `u16`) |
| `0x0806547C` / `0x6547C` | code table B (8 × `u16`) |
| `0x0806548C` / `0x6548C` | code table C (4 × `u16`) |
| `0x08065494` / `0x65494` | code table D (4 × `u16`) |
| `0x0803C7A4` / `0x3C7A4` | title-screen state handler (state dispatch on `r1`) |
| `0x0803C87C` | title state (state 1) block; idle timer + code checker |
| `0x0803C8FA`–`0x0803CAE2` | code validator / dispatcher |
| `0x0803C914` | table A compare |
| `0x0803C97C` | table A mismatch: reset index, reload cooldown |
| `0x0803C930`–`0x0803C948` | table A success: sound 7, `profile[0]=0x3FFF`, `profile[0xB]=14` |
| `0x0803C980` | table B compare |
| `0x0803C9A0`–`0x0803C9BA` | table B success: `profile[0x2B2]=0x0012` |
| `0x0803C9E2` | table C compare |
| `0x0803CA02`–`0x0803CA12` | table C success: `profile[0]=0x000000FF` |
| `0x0803CA3A` | table D compare |
| `0x0803CA5A`–`0x0803CA6A` | table D success: `profile[0]=0x000007FF` |
| `0x0803CA9C` | timeout: reload cooldown, clear only `0x0300018D`/`0x0300018E` |
| `0x03005C70` (RAM) | key state word compared against tables (`u16`, active-high) |
| `0x0300018D` (RAM) | table B progress index |
| `0x0300018E` (RAM) | table A progress index |
| `0x0300018F` (RAM) | table C progress index |
| `0x03000190` (RAM) | table D progress index |
| `0x03000191` (RAM) | sequence cooldown byte (`0x80` frames) |
| `0x03000188` (RAM) | title-screen idle timer (900 frames) |
| `0x03000360` (RAM) | pointer to the current profile |
| `0x020119AC` (EWRAM) | profile base observed in this run (deterministic for this path) |
| `profile + 0x00` | `u32` unlocked-level bitmask |
| `profile + 0x0B` | `u8` number of level-list entries |
| `profile + 0x2B2` | `u16` skater roster count |
| `0x087B2FF8` | `TO UNLOCK ALL SKATERS...` |
| `0x087B3014` … `0x087B30AC` | credits cheat lines (`L BUTTON...`, `R BUTTON...`) |
| `0x087B30F0` | `TRY OUT THESE CHEATS` |
| `0x0806CF3C` | pointer table for the credits cheat block |
| `0x087B1CB2` | in-level hint for `L,L,R,B` (unlocks through Bob's Scrapyard) |
| `0x087B2154` | in-level hint for `L,B,R,B` (unlocks through Deadman's Sewer) |
| `0x087B0A84`–`0x087B0ADC` | secret-skater short names (reverse display order) |
| `0x087B1870` | `ACCLAIM GAMES` |
| `0x0806B948` | 10 language pointers to `ACCLAIM GAMES` |
| `0x087B0878` | `LOCKED` |

The profile pointer is loaded by the validator from `0x03000360`
(`0x0803C93E`, `0x0803C9B0`, `0x0803CA0C`, `0x0803CA64`). The GDB run caught
`r1 = 0x020119AC` at `0x0803C944` and read `0x0000000F` (baseline four-level
mask) before the write.

## 5. Algorithm

### 5.1 Tables (exact halfwords)

```text
A @ 0x0806546C, len 8:
  0040 0080 0040 0080 0020 0010 0002 0100
  UP   DOWN UP   DOWN LEFT RIGHT B    R

B @ 0x0806547C, len 8:
  0200 0200 0002 0002 0100 0100 0200 0100
  L    L    B    B    R    R    L    R

C @ 0x0806548C, len 4:
  0200 0002 0100 0002
  L    B    R    B

D @ 0x08065494, len 4:
  0200 0200 0100 0002
  L    L    R    B
```

Masks are active-high GBA key bits: `A=0x001`, `B=0x002`, `Select=0x004`,
`Start=0x008`, `Right=0x010`, `Left=0x020`, `Up=0x040`, `Down=0x080`,
`R=0x100`, `L=0x200`.

### 5.2 Validator pseudocode

```python
profile = read_u32(0x03000360)          # EWRAM pointer
key     = read_u16(0x03005C70)          # current key word

# Per-frame timeout (0x0803C8FA)
if u8[0x03000191] == 0:
    u8[0x03000191] = 0x80
    u8[0x0300018D] = 0                # clears B only
    u8[0x0300018E] = 0                # clears A only
    return                            # NOTE: C/D indices are NOT cleared
u8[0x03000191] -= 1

if key == 0:
    return

# A: 8 presses
if key == TABLE_A[u8[0x0300018E]]:
    u8[0x0300018E] += 1
    if u8[0x0300018E] == 8:
        u8[0x0300018E] = 0
        u8[0x03000191] = 0x80
        sfx(7)
        u32[profile + 0x00] = 0x00003FFF
        u8 [profile + 0x0B] = 14
else:
    u8[0x0300018E] = 0
    u8[0x03000191] = 0x80

# B: 8 presses
if key == TABLE_B[u8[0x0300018D]]:
    u8[0x0300018D] += 1
    if u8[0x0300018D] == 8:
        u8[0x0300018D] = 0
        u8[0x03000191] = 0x80
        sfx(7)
        u16[profile + 0x2B2] = 0x0012
else:
    u8[0x0300018D] = 0
    u8[0x03000191] = 0x80

# C: 4 presses
if key == TABLE_C[u8[0x0300018F]]:
    u8[0x0300018F] += 1
    if u8[0x0300018F] == 4:
        u8[0x0300018F] = 0
        u8[0x03000191] = 0x80
        u32[profile + 0x00] = 0x000000FF
else:
    u8[0x0300018F] = 0
    u8[0x03000191] = 0x80

# D: 4 presses
if key == TABLE_D[u8[0x03000190]]:
    u8[0x03000190] += 1
    if u8[0x03000190] == 4:
        u8[0x03000190] = 0
        u8[0x03000191] = 0x80
        u32[profile + 0x00] = 0x000007FF
else:
    u8[0x03000190] = 0
    u8[0x03000191] = 0x80
```

Important consequences:

* The four compares run in order A, B, C, D **every frame**. A press that
  matches one table may be rejected by the others, but each table has its own
  index and mismatch-reset.
* A partial match does **not** reload the cooldown; a mismatch or completion
  does. The `0x80`-frame cooldown is the only gap limit for A/B.
* When the cooldown expires (`0x0803CA9C`), only the A and B indices are
  cleared. C and D keep their progress indefinitely. This is why
  `L, (5 s), B, R, B` succeeds while `Up, (5 s), Down, Up, Down, Left, Right,
  B, R` fails.
* The writes are **overwrites**, not ORs. Applying C after D relocks levels
  8–10; applying C after A leaves the 14-entry list length but relocks entries
  8–13.

### 5.3 Profile fields

| Offset | Type | Baseline | After code | Meaning |
|---|---|---|---|---|
| `+0x00` | `u32` | `0x0000000F` | `0xFF`, `0x7FF`, `0x3FFF` | unlocked-level bitmask (bit *n* = level index *n*) |
| `+0x0B` | `u8` | `0x0D` (13) | `0x0E` (14) | number of level-list entries to build |
| `+0x2B2` | `u16` | `0x000A` (10) | `0x0012` (18) | skater roster count (initialised to 10 at `0x0804857A`) |

The level list is built from the first `u8[+0x0B]` level records and each is
shown as `LOCKED` if its bit is clear in `u32[+0x00]`. This model is confirmed
by the composed test in §6b: `0x3FFF`/14 then `0xFF` gives a 14-entry list with
eight unlocked entries and six `LOCKED` entries, including `ACCLAIM GAMES`.

## 6. Tables

### 6.1 Levels and bit indices

The observed internal/display order (13 normal levels, then the hidden one):

| Bit | Level |
|---:|---|
| 0 | HOMETOWN BACKYARD |
| 1 | WAYWOOD STREET |
| 2 | WAYWOOD GARDENS |
| 3 | SUPPLY WAREHOUSE |
| 4 | BELLPORT MALL |
| 5 | ESCALATOR RUSH |
| 6 | BELLPORT CAR PARK |
| 7 | DEADMAN'S SEWER |
| 8 | HOBO CITY |
| 9 | BEACH FRONT |
| 10 | BOB'S SCRAPYARD |
| 11 | FUN FAIR |
| 12 | BIG TOP CIRCUS |
| 13 | **ACCLAIM GAMES** (hidden) |

Baseline mask `0x0F` = bits 0–3. `0xFF` = 0–7. `0x7FF` = 0–10.
`0x3FFF` = 0–13.

### 6.2 Secret skaters (code B)

Display order after `L,L,B,B,R,R,L,R`, with stat bars read from the in-game
STATS screen (eight-block scale):

| Name | Speed | Spin | Jump | Air | Hang time |
|---|---:|---:|---:|---:|---:|
| CHRISSY | 6 | 5 | 5 | 4 | 3 |
| JORDAN | 6 | 6 | 5 | 2 | 3 |
| THE CASTAWAY | 8 | 8 | 8 | 6 | 6 |
| THE NINJA | 8 | 8 | 8 | 8 | 8 |
| METALMAN | 8 | 8 | 8 | 8 | 8 |
| TUFFGUY | 8 | 8 | 8 | 8 | 8 |
| MR. ASTRO | 8 | 8 | 8 | 8 | 8 |
| SUPERDUDE | 8 | 8 | 8 | 8 | 8 |

The normal ten (baseline) are S. DOCKHURST, S. FOGARTY, M. LINDENHAUPT,
M. SALERNO, E. YASUTOKO, S. YOST, J. GROS, T. KARIS, C. EDWARDS and F. MORALES.
Code B sets the roster count from 10 to 18, so the eight secret skaters are
appended after the normal six that precede J. GROS. The short-name string block
is at `0x087B0A84` in reverse order (`SUPERDUDE`, `MR. ASTRO`, `TUFFGUY`,
`METALMAN`, `THE NINJA`, `THE CASTAWAY`, `JORDAN`, `CHRISSY`).

### 6.3 Published-code cross-check

| Published code | Source | In ROM? | In emulator? |
|---|---|---|---|
| `UDUDLRBR` (all levels) | GameFAQs, Neoseeker, SuperCheats, Geocities, MegaGames | yes, table A | yes, 14 levels incl. ACCLAIM GAMES |
| `LLBBRRLR` (all skaters) | same lists | yes, table B | yes, 18 skaters |
| `LBRB` (through Deadman's Sewer) | GameFAQs, Neoseeker, SuperCheats | yes, table C | yes, 8 levels |
| `LLRB` (through Bob's Scrapyard) | in-game level-intro text; classicgamehacking.blogspot.com (2012) | yes, table D | yes, 11 levels |
| `Skeleton`, `BIGUPYASELF`, `Justin Bailey`, `QUEZDONTSLEEP`, park-theme `UUDDLRLRBABA` | GameFAQs/other-platform lists | **no** (no code screen / no such strings) | not applicable |
| `LLRRLRDUUD` (“Get back juice”) | GameFAQs/other-platform mixed list | **no table, no “juice” string** | no observable effect at pause or title |

## 6b. Enumeration

### Space definition

* **Alphabet:** 10 physical buttons (`A`, `B`, `Select`, `Start`, `Right`,
  `Left`, `Up`, `Down`, `R`, `L`), represented by the 10 active-high bits in
  `0x03005C70`.
* **Lengths:** 8 (A), 8 (B), 4 (C), 4 (D).
* **Table size:** 4 records, 24 `u16` entries, 48 bytes at `0x0806546C`.
* **Checksum / fields:** none. The validator is a literal equality lookup; it
  has no numeric payload, no checksum, and no reserved bits.
* **Accepted set:** exactly the four literals. No prefix alone triggers an
  effect; every table requires its index to reach the full length after
  starting from zero.

The naive string space for all length-8 sequences over the 10-symbol alphabet
is `10^8`; for length 4 it is `10^4`. The ROM accepts exactly 4 of those
strings (2 of length 4, 2 of length 8). It rejects every other value by table
mismatch, not by a range or checksum test.

### Novel / unpublished inputs

**(a) Slow four-press code — accepted.** Enter `L`, wait five seconds, then
`B`, `R`, `B`. The game unlocks eight levels through **DEADMAN'S SEWER**
(`profile[0] = 0xFF`). This is not in any published list, and it contradicts
the “enter one after another” wording: the 4-press indices survive the timeout.
Evidence: `evidence/16_slow_LBRB.jpg`.

**(b) Composed state — `UDUDLRBR` then `LBRB`.** The first code sets the list
length to 14 and the mask to `0x3FFF`; the second overwrites the mask with
`0xFF`. The result is a 14-entry level list where **ACCLAIM GAMES is present but
LOCKED**, and levels 8–13 (HOBO CITY, BEACH FRONT, BOB'S SCRAPYARD, FUN FAIR,
BIG TOP CIRCUS, ACCLAIM GAMES) are locked. No published list describes this
state. Evidence: `evidence/11_novel_alllevels_then_LBRB.jpg`.

**(c) Reverse composition — `LLRB` then `LBRB`.** The mask goes `0x7FF` → `0xFF`
and levels 8–10 are relocked. This proves the write is an overwrite, not an OR.
Evidence: `evidence/12_relock_LLRB_then_LBRB.jpg`.

**(d) Hidden level.** `ACCLAIM GAMES` is bit 13, string `0x087B1870`, with a
10-language pointer block at `0x0806B948`. It is reachable in our tests only
through code A; the normal baseline list has 13 entries and never shows it.
Entering it loads a playable indoor level with AKA/Acclaim branding.
Evidence: `evidence/06_acclaim_games_unlocked.png`,
`evidence/07_acclaim_games_ingame.png`.

### Bounds proven by rejection

| Test | Expected if bound is real | Observed |
|---|---|---|
| `Up Down Up Down Left Right B` (7 presses, final R omitted) | no effect | baseline 13 levels, no ACCLAIM GAMES (`evidence/13_reject_7press.jpg`) |
| `UDUDLRBR` on the main menu instead of the title | no effect | baseline (`evidence/14_reject_mainmenu.jpg`) |
| `UDUDLRBR` with A held for the whole sequence | no effect | baseline (`evidence/15_reject_extra_button.jpg`) |
| `Up`, 5 s gap, `Down Up Down Left Right B R` | 8-press progress cleared | baseline (`evidence/18_reject_5s_gap_8press.jpg`) |
| `Up`, 2.5 s gap, rest of `UDUDLRBR` | cleared (counter is 0x80 frames ≈2.13 s) | baseline (`evidence/20_gap_2.5s_rejected.jpg`) |
| `Up`, 1.8 s gap, rest of `UDUDLRBR` | accepted | all 14 levels (`evidence/19_gap_1.8s_accepted.jpg`) |
| 1 s hold per button of `UDUDLRBR` | accepted (one press per button) | all 14 levels (`evidence/21_holds_1s_accepted.jpg`) |
| `L B R B` at pause (“Get back juice”) | published list says “restore juice” | no visible change; no table/string in ROM |

The 5 s vs 1.8 s/2.5 s pair measures the gap bound to between 1.8 s and 2.5 s,
matching the `0x80`-frame counter at `0x03000191`.

## 7. Validation evidence

### Observed

* All four codes entered on the title screen and their level/skater effects
  captured in `evidence/` (listed above).
* GDB (`mgba -g`, `gdb-multiarch`, breakpoints at `0x0803C944`, `0x0803C948`,
  `0x0803C9B8`, `0x0803CA12`, `0x0803CA6A`) captured:
  * `CODE1_MASK_OLD r1=020119AC val=0000000F count_byte=0D`
  * `CODE1_COUNT_OLD r1=020119AC byte11=0D`
  * `CODE3_MASK_OLD r1=020119AC val=00003FFF`
  * `CODE4_MASK_OLD r1=020119AC val=000000FF`
  * post-run dump: `mask=0x000007FF`, `count_byte11=0x0E`, `skater_u16_2b2=0x0012`
  * logs: `evidence/gdb_levelmask_hit.log`, `evidence/gdb_allcodes_hits.log`
* Menu walk (screenshots in `evidence/`):
  * title / “PRESS START” — `01_title.png`
  * main menu (PLAY ARCADE, FREESKATE, MULTIPLAYER GAMES, GAME OPTIONS) —
    `02_main_menu.png`
  * Game Options (CONTROL TYPE A, MUSIC VOLUME, SFX VOLUME, CREDITS) —
    `03_options.png`
  * Freeskate skater select/stats — `04_skater_select_baseline.png`
  * Freeskate level select, all 13 normal entries — `05_levels_baseline.jpg`
  * Arcade skater select, story dialogue and 3:00-timer gameplay —
    `24_arcade_gameplay.png`
  * pause menu (CONTINUE / END RUN) — `17_pause_menu.png`
  * credits roll — `22_credits.jpg`
  * multiplayer link screen (“LINKING UP PLEASE WAIT”) —
    `23_multiplayer_link.png`
  * hidden ACCLAIM GAMES level-select slot and gameplay —
    `06_acclaim_games_unlocked.png`, `07_acclaim_games_ingame.png`
* No gallery, sound-test or debug menu was found on any of those screens.
* Baseline level list has 13 entries with bits 0–3 unlocked; after code A it has
  14 entries including ACCLAIM GAMES.

### Derived

* Table addresses and halfwords read directly from the ROM; the four literal
  pointers at `0x0803C968`, `0x0803C9C4`, `0x0803CA24`, `0x0803CA7C` resolve to
  `0x0806546C`, `0x0806547C`, `0x0806548C`, `0x08065494`.
* The success writes at `0x0803C944` (`0x3FFF`), `0x0803C948` (`14`),
  `0x0803C9B8` (`0x12`), `0x0803CA12` (`0xFF`), `0x0803CA6A` (`0x7FF`).
* The timeout path at `0x0803CA9C` clears `0x0300018D`/`0x0300018E` only,
  which explains the 4-press/8-press timing difference.
* The profile field initialisations: bitmask `0x0F`, length `0x0D`, roster
  count `0x0A` (the roster write at `0x0804857A` sets `+0x2B2 = 10`).

### Inferred

* The exact meaning of `profile + 0x2B2` is “skater roster count”. It is
  initialised to 10, code B writes 18, and the in-game roster grows from 10 to
  18; the value is therefore the count, not a bitmask.
* ACCLAIM GAMES is intended as a completion/bonus level (it has a full 10-
  language name block, a top score of 150,000, and its own level art), but we
  did not complete all normal levels to prove its normal-play unlock condition.
* The header checksum field `0x0000` is likely a dumping/patching artifact; the
  complement check is valid and the game boots.

## 8. Unknowns

* The exact input-layer representation (held mask vs. pressed edge) is not fully
  resolved. Empirically the handler consumes one press per button (1 s holds do
  not double-advance), an extra held button blocks recognition, and the
  inter-press gap must be < ~2.5 s for 8-press codes. The validator itself only
  reads `u16[0x03005C70]`.
* The 1.8 s/2.5 s bound was bracketed, not measured to the frame; the static
  counter is `0x80` frames (2.13 s at 60 Hz).
* Whether `ACCLAIM GAMES` becomes available after finishing the 13 normal levels
  (rather than only through code A) was not tested; the game has no save data
  in our run (`.sav` was zero bytes), so a full completion run was out of
  scope.
* The normal-play unlock path for the eight secret skaters (collect juice boxes
  / finish challenges, as the published lists suggest) was not tested.
* The published “Get back juice” code is absent as a table and shows no effect;
  whether a different, non-table implementation exists at pause was not found
  by literal scan, mask-run scan, or observation.

## 9. Tooling

* `mgba` 0.10.5 (SDL frontend, `/usr/games/mgba`), `Xvfb :128`, `openbox`,
  `xdotool`, `scrot`, ImageMagick.
* `gdb-multiarch` + mGBA `-g` stub for RAM/profile reads.
* `arm-none-eabi-objdump -M force-thumb` for validator disassembly.
* Python 3 + Capstone 5.0.7 for mask/table scans and header parsing.
* Helper scripts/logs: `/tmp/opencode/inline/key.py`, `gdb1.txt`, `gdb2.txt`,
  `logs/gdb1.log`, `logs/gdb2.log`.
* Evidence images: `roms/Aggressive Inline/evidence/` (24 PNG/JPG images +
  2 GDB logs).

Reproduce the key static checks:

```bash
cd "roms/Aggressive Inline"
python3 - <<'PY'
import struct
rom = open("Aggressive Inline.gba","rb").read()
for off,n in ((0x6546c,8),(0x6547c,8),(0x6548c,4),(0x65494,4)):
    print(hex(0x08000000+off),
          [hex(struct.unpack_from("<H",rom,off+2*i)[0]) for i in range(n)])
PY
arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 \
  --start-address=0x0803C8FA --stop-address=0x0803CB00 \
  -M force-thumb "Aggressive Inline.gba"
```

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed in this
report beyond short factual quotations needed to document the codes. The ROM
hash is provided for identification only.
