# Bubble Bobble Old & New (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Bubble Bobble Old & New/Bubble Bobble Old & New.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `BUBBLE BOBBL` |
| Game code | `AONE` |
| Maker code | `7N` (MediaKite / Taito) |
| Software version | 0x00 |
| Header complement | 0x7C (matches computed value) |
| Header checksum | 0x0000 (rebuilt-header artifact, not a trainer) |
| Entry word | `0xEA00002E` (standard branch to 0x080000C0, unpatched) |
| MD5 | `ebe1fc2780d93c4cf42f1fe5815a84bf` |
| SHA-1 | `efd718795fd29389942ae93611ac12546a6a3e86` |
| SHA-256 | `7262351705148496c102a361e3a68621884a104249f05b692971daceb2cbb500` |

Embedded-header scan (search for the 156-byte Nintendo logo through the whole
file) found three GBA headers:

| Base | Title | Code | Ver | Meaning |
|---|---|---|---|---|
| `0x000000` | `BUBBLE BOBBL` | AONE | 0 | Main game image |
| `0x3C10F8` | `BUBBLEBOBBLE` | AONE | 1 | Embedded multiboot link-play image A (114,468 bytes) |
| `0x3FD01C` | `BUBBLEBOBBLE` | AONE | 1 | Embedded multiboot link-play image B (12,260 bytes) |

Neither embedded image is a trainer or a cracktro: both have a normal
`0xEA00002E` entry, a valid complement and the same publisher/maker fields.
Image A contains the only `ROUND SELECT` string in the ROM (`0x3F0C6C`,
`0x083F0C6C` when the image is linked at its own base); image B is a small
link stub. No appended data exists after `0x400000`.

No patch or trainer was found: the entry point, header, logo and first 4 KiB
are stock; the 0x0000 header checksum is the known artifact of a rebuilt
header (§16.1 of the guide), and the complement byte is correct.

## 2. Executive summary

The GBA release reproduces the arcade title-screen button codes as an
**exact 8-press lookup table**. There are two 16-byte-stride tables, one for
OLD mode and one for NEW mode, at `0x08381228` and `0x08381298`. Each table
holds **six codes plus a sentinel**. Three codes are shared by both tables
(the two undocumented codes and EXTEND); the other three are version-specific.

The published GBA lists (GameFAQs/Vizzed) contain seven codes. All seven were
verified byte-for-byte against the two tables. The four OLD-mode public codes
(EXTEND, Original, Power-up, Super) were entered on the OLD title and their
flags read back; the three NEW-mode variants were matched against the NEW
table, and one (Super New) was used as a cross-version rejection test:

* EXTEND — Up, Up, Down, Down, Left, Right, Left, Right
* Original Mode (Old / New)
* Power-up Mode (Old / New)
* Super Mode (Old / New)

The table contains **two codes that appear in no published list**:

* `0x01` — **L, L, R, Select, Right, Left, Select, L**
* `0x02` — **L, R, Left, Right, Up, Down, R, L**

Both were entered on the real OLD title screen; both were accepted and set
their flag bit in RAM. `0x01` is a debug invincibility flag: two player/entity
collision routines read bit 0 and return "no collision" when it is set.
`0x02` sets bit 1 (no reader exists in the main image — it is a dead flag) and
writes `100` to two 8-bit counters (`0x03002FBC`, `0x03002FD8`) before playing
jingle 0x1E.

The two developer-intended mode codes are visually confirmed: entering the
`0x08` code prints **`ORIGINAL GAME ...`** at the bottom-left of the OLD title
screen, and the `0x10` code prints **`POWER UP!`**, exactly as in the arcade.
This is the hidden mode menu; it is not an emulator/debugger-only state.

The whole code space is therefore: 10 symbols, exactly 8 presses,
10^8 = 100,000,000 candidate strings, of which **9 distinct strings are
accepted** (12 version-code pairs). Bounds were proven in-game by rejecting a
7-press prefix, a non-code 8-press string, and a NEW-only code entered on the
OLD title screen.

## 3. How to reproduce

### Emulator and keymap

```bash
Xvfb :216 -screen 0 1024x768x24 &
DISPLAY=:216 openbox &
DISPLAY=:216 SDL_AUDIODRIVER=dummy mgba -3 "Bubble Bobble Old & New.gba" &
W=$(DISPLAY=:216 xdotool search --name mGBA | head -1)
DISPLAY=:216 xdotool windowfocus "$W"
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

Hold keys 60–350 ms. At the version-logo/title screen a 60 ms tap is enough
for code presses; `Start` needs ~350 ms.

### Exact menu path

1. Boot → Taito/Empire logos → attract → main title `BUBBLE BOBBLE OLD & NEW`.
2. `Start` → **Select save file**. Move to `OK!!` (`A`) and confirm (`A`).
3. **Game mode** → `Single Play` (`A`).
4. **Game version** → `OLD` or `NEW` (`A`). The chosen version’s logo/title
   screen appears. **This is the code-entry screen.**
5. Enter one 8-press code from §6. Each press must be within 1 s of the
   previous one. An extra press after the 8th makes the compared window too
   long and breaks the match; once the index exceeds 8 the buffer resets.
   `A` and `Start` are not part of any code — pressing either starts the game.
6. For the `0x08` / `0x10` codes, the label `ORIGINAL GAME ...` (blue) and/or
   `POWER UP!` (red) appears at the bottom-left. `Start` then begins that mode.

### Reproduction of the two new codes

At the **OLD** title screen (after step 4), enter:

```
novel 0x01:  L  L  R  Select  Right  Left  Select  L
             a  a  s  BackSp  Right  Left  BackSp  a

novel 0x02:  L  R  Left  Right  Up  Down  R  L
             a  s  Left  Right  Up  Down  s  a
```

Read the flag word with mGBA’s CLI debugger (`mgba -d`, stub-free) or GDB:

```
x/1 0x03002f40        # system block
r/4 0x03002fec        # cheat/flag word: 0x00000001 or 0x00000002
x/1 0x03001390        # 8-byte key buffer, ends with 0x0A
x/1 0x0300138b        # index (0 after a match)
```

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Address | Size | Meaning |
|---|---|---|
| `0x08381228` | 7×16 | OLD-mode code table (6 codes + sentinel) |
| `0x08381298` | 7×16 | NEW-mode code table (6 codes + sentinel) |
| `0x080060CC` | — | Key conversion + 8-press buffer builder + table compare |
| `0x08006178` | — | Match path: set timeouts, OR flag, dispatch |
| `0x080061BA` | — | Table selector: `(config[0x0E] & 0x30) == 0x10` → NEW, else OLD |
| `0x080061D8` | 4 | Literal pointer `0x08381228` (OLD) |
| `0x080061DC` | 4 | Literal pointer `0x08381298` (NEW) |
| `0x080061E0` | — | Compare loop (`memcmp(buf, record, index+1)`) |
| `0x0800622C` | 0x80 | Handler jump table indexed by `flag - 1` |
| `0x080062AC` | — | Flag 0x01 handler (sound 0x33) |
| `0x080062B6` | — | Flag 0x02 handler (sound 0x1E + 100-value writes) |
| `0x080062F0` | — | Flag 0x20 handler (EXTEND, sound 0x29) |
| `0x080062FA` | — | Flags 0x04 / 0x08 / 0x10 handler (defers menu draw) |
| `0x08006040` | — | Draws `ORIGINAL GAME ...` if flag&8 and `POWER UP!` if flag&0x10 |
| `0x08002EB0` | — | `test_flag(mask)` = `(*(u32*)0x03002FEC & mask) != 0` |
| `0x08002ECC` | — | `write_flag(mask, mode)` on `0x03002FEC` (0=OR, 1=ANDNOT, 2=STORE, 3=XOR) |
| `0x08012B68` | — | Player/entity collision check; returns 0 when flag bit 0 is set |
| `0x08013EC8` | — | Player/entity collision check; returns 0 when flag bit 0 is set |
| `0x08016B8C` | — | Caller: loops players 0/1 into `0x08012B68` |
| `0x0800D3B0` | — | Caller: loops players 0/1 into `0x08013EC8` |

RAM:

| Address | Size | Meaning |
|---|---|---|
| `0x03001390` | 9 | Key buffer: 8 indices + `0x0A` terminator |
| `0x0300138B` | 1 | Buffer index (0–8); >8 resets to 0 |
| `0x0300138C` | 1 | Inter-key timer, reloaded with 60 each press |
| `0x03001388` | 2 | Match/display timer, set to 600 on a successful code |
| `0x03002F40` | 0x100+ | System/save/option block |
| `0x03002F4E` | 1 | Version/flags byte (`&0x30 == 0x10` = NEW) |
| `0x03002F4F` | 1 | Bit 5 set by the 0x02 code (no reader found) |
| `0x03002FBC` | 1 | Counter written `100` by the 0x02 code |
| `0x03002FD8` | 1 | Counter written `100` by the 0x02 code |
| `0x03002FEC` | 4 | **Cheat flag word** = base `0x03002F40` + `0xAC` |
| `0x03003030` | 1 | Volume-table entry written `100` by the 0x02 code |

The embedded multiboot image A (`0x3C10F8`) contains its own copy of the
classic game and the `ROUND SELECT` string at `0x083F0C6C`; image B
(`0x3FD01C`) is a link stub. Neither is part of the main code path.

## 5. Algorithm

### 5.1 Key conversion

`0x080060CC` converts the pressed-key mask to a 4-bit index:

```
mask 0x0040 Up    -> 0     mask 0x0001 A     -> 4
mask 0x0080 Down  -> 1     mask 0x0002 B     -> 5
mask 0x0010 Right -> 2     mask 0x0100 R     -> 6
mask 0x0020 Left  -> 3     mask 0x0200 L     -> 7
mask 0x0008 Start -> 8     mask 0x0004 Select-> 9
```

### 5.2 Entry

```
i = *(u8*)0x0300138B
if i > 8:
    *(u8*)0x0300138B = 0
    *(u8*)0x0300138C = 0
    return
buf = (u8*)0x03001390
buf[i] = index(key)
buf[i+1] = 0x0A
*(u8*)0x0300138B = i+1
*(u8*)0x0300138C = 60          ; 60-frame inter-key window
```

### 5.3 Validator

```
table = ((*(u8*)0x03002F4E & 0x30) == 0x10) ? 0x08381298 : 0x08381228
i     = *(u8*)0x0300138B
for rec = table; rec->flag != 0; rec += 16:
    if memcmp(buf, rec->seq, i+1) == 0:
        write_flag(rec->flag, OR)          ; 0x08002ECC(flag, 0)
        *(u8*)0x0300138B = 0
        *(u8*)0x0300138C = 0
        *(u16*)0x03001388 = 600             ; match/display timer
        dispatch(rec->flag)
        return
```

The comparison deliberately includes the byte after the 8 sequence bytes,
which is the record’s `u32 0x0A` length field. A code therefore matches only at
`i == 8`; a shorter prefix cannot match because a table byte is never 0x0A,
and an extra 9th press makes the compared window 10 bytes long, which cannot
match either. The `flag` field doubles as the record ID and as the bit written
to `0x03002FEC`; the sentinel has `flag == 0` and terminates the loop.

Pseudocode for the whole table (record layout):

```c
struct rec { u8 seq[8]; u32 ten; u32 flag; };   /* ten == 0x0A, flag != 0 */
```

### 5.4 Handler dispatch

`0x0800622C` is indexed by `flag - 1`:

| Flag | Handler | Action |
|---|---|---|
| `0x01` | `0x080062AC` | play sound 0x33 on channel 2 |
| `0x02` | `0x080062B6` | `base[0x0F] |= 0x20`; `base[0x7C]=100`; `base[0x98]=100`; volume table entry = 100; play sound 0x1E |
| `0x04` | `0x080062FA` | defer menu draw (SUPER) |
| `0x08` | `0x080062FA` | defer menu draw (ORIGINAL) |
| `0x10` | `0x080062FA` | defer menu draw (POWER UP) |
| `0x20` | `0x080062F0` | play sound 0x29 (EXTEND) |

`0x08006040` then draws the hidden mode labels from the flag word:

```
if (*(u32*)0x03002FEC & 0x08) draw "ORIGINAL GAME ..."   ; 0x08170730
if (*(u32*)0x03002FEC & 0x10) draw "POWER UP!"           ; 0x08170724
```

Flag bit 0 is tested by `0x08012B68` and `0x08013EC8`; both return 0
immediately when it is set. Their callers (`0x08016B8C`, `0x0800D3B0`) loop
over the two player entities and call them against the current entity, so bit
0 suppresses player/entity collision (invincibility). No caller of
`0x08002EB0` passes mask 2, and no other direct reader of the flag word masks
bit 1: flag 0x02 is dead in the main image.

## 6. Tables

### 6.1 OLD table — `0x08381228`

| Flag | Presses (8) | Raw bytes |
|---:|---|---|
| `0x01` | **L, L, R, Select, Right, Left, Select, L** | `06 06 07 09 02 03 09 06` |
| `0x02` | **L, R, Left, Right, Up, Down, R, L** | `06 07 03 02 00 01 07 06` |
| `0x20` | Up, Up, Down, Down, Left, Right, Left, Right | `00 00 01 01 03 02 03 02` |
| `0x04` | Left, R, Left, Select, Left, L, Left, Select | `03 07 03 09 03 06 03 09` |
| `0x08` | L, R, L, R, L, R, Right, Select | `06 07 06 07 06 07 02 09` |
| `0x10` | Select, R, L, Left, Right, R, Select, Right | `09 07 06 03 02 07 09 02` |
| `0x00` | sentinel | `0A 00 …` |

### 6.2 NEW table — `0x08381298`

| Flag | Presses (8) | Raw bytes |
|---:|---|---|
| `0x01` | **L, L, R, Select, Right, Left, Select, L** | `06 06 07 09 02 03 09 06` |
| `0x02` | **L, R, Left, Right, Up, Down, R, L** | `06 07 03 02 00 01 07 06` |
| `0x20` | Up, Up, Down, Down, Left, Right, Left, Right | `00 00 01 01 03 02 03 02` |
| `0x04` | Right, R, Left, L, Select, R, Select, L | `02 07 03 06 09 07 09 06` |
| `0x08` | L, R, L, R, Left, Select, Right, Select | `06 07 06 07 03 09 02 09` |
| `0x10` | Left, Left, Left, L, Right, R, R, L | `03 03 03 06 02 07 07 06` |
| `0x00` | sentinel | `0A 00 …` |

Bold rows are absent from every published list checked (GameFAQs, Vizzed,
Game Revolution, TCRF, arcade-history). The other four per version are the
public codes (seven distinct public strings in total); the OLD rows were
confirmed dynamically by their flag values, the NEW rows are table-derived:

| Public code | Version | Flag | Evidence |
|---|---|---:|---|
| EXTEND | both | `0x20` | observed on OLD (same string is in both tables) |
| Original Mode | OLD | `0x08` | observed |
| Original Mode | NEW | `0x08` | table only |
| Power-up Mode | OLD | `0x10` | observed |
| Power-up Mode | NEW | `0x10` | table only |
| Super Mode | OLD | `0x04` | observed |
| Super Mode | NEW | `0x04` | table only (and rejected on OLD) |

## 6b. Enumeration

**Space definition.** Alphabet: 10 symbols (A, B, Select, Start, Right, Left,
Up, Down, R, L). Length: exactly 8 presses. Candidate strings:
10^8 = **100,000,000**. The table’s comparison length is `index+1` where
`index` is the number of stored presses; because the ninth compared byte is
the record’s `0x0A` length field, only `index == 8` can match. A press that
takes the index past 8 resets the buffer. The inter-key window is 60 frames
(≈1 s).

**Accepted set.** Exactly six records per version. The first three records
(flag 0x01, 0x02, 0x20) are identical in both tables, so the number of
*distinct accepted strings* is **9**; the number of version/code pairs is
**12**. There is no algorithm, checksum, or wildcard: the accepted set is the
hard-coded table.

**Novel codes (not in GameFAQs / Vizzed / Game Revolution / TCRF):**

1. **`L, L, R, Select, Right, Left, Select, L`** → flag `0x00000001`.
   Entered on the OLD title screen; mGBA debugger read of `0x03002FEC`
   returned `0x00000001`; the 8-byte buffer at `0x03001390` contained
   `06 06 07 09 02 03 09 06 0A`. The bit is read by the two player/entity
   collision routines (`0x08012B68`, `0x08013EC8`), which return "no
   collision" when it is set: a debug invincibility flag.
2. **`L, R, Left, Right, Up, Down, R, L`** → flag `0x00000002`.
   Same title screen; flag read returned `0x00000002`; buffer contained
   `06 07 03 02 00 01 07 06 0A`. The handler also writes `100` to
   `0x03002FBC`, `0x03002FD8` and a volume-table byte at `0x03003030`, and
   plays jingle 0x1E. Bit 1 has no reader in the main image (exhaustive
   caller scan), so this code’s only live effects are the 100-value writes
   and the jingle.

**Bounds proven by rejection (all in the emulator, on the OLD title):**

| Test | Result |
|---|---|
| 7-press prefix `L,L,R,Select,Right,Left,Select` | buffer reached index 7; flag stayed `0` (no match) |
| 8-press non-code `Left,Right,Left,Right,Left,Right,Left,Right` | buffer index 8, bytes `03 02 03 02 03 02 03 02 0A`, flag `0` |
| NEW-only code `Right,R,Left,L,Select,R,Select,L` on the OLD title | buffer matched the NEW record byte-for-byte, flag stayed `0` (version-table rejection) |
| 9th press after a code | the compared window becomes 10 bytes and cannot match; index > 8 resets to 0 |
| `A` or `Start` inside a sequence | not in any table; starts the game instead |

Thus the accepted set is closed: it is exactly the six records per version,
and both non-table strings and the wrong-version table are rejected.

**Menu / hidden-content enumeration.** Every reachable screen was walked:
publisher logo → Nintendo logo → attract → main title → Select save file →
Game mode (Single Play / Single Pak multiplayer / Multi-Pak multiplayer) →
Game version (OLD / NEW) → version logo/title → round-start screen →
in-game pause menu (`RETURN`, `GIVE UP`) → game over. The pause menu has only
those two entries. No sound-test, option, or round-select screen was found in
the main image; the only `ROUND SELECT` string in the ROM belongs to the
embedded multiboot link image A and is not reachable in a standalone boot.

## 7. Validation evidence

**Observed (emulator / memory read)**

* The four OLD-mode public codes were decoded from the table and accepted in
  the emulator, setting the expected flag bits (table in §6.2). The three
  NEW-mode public sequences were matched against the NEW table, and NEW-only
  Super was rejected on the OLD title (flag stayed 0).
* The `0x08` code draws `ORIGINAL GAME ...` at the bottom-left of the OLD
  title; the `0x10` code draws `POWER UP!`; both together show both labels
  (screenshots `q1`–`q4`, `r2`–`r4`, `o1`–`o3`).
* The two new codes were entered and their flags read from `0x03002FEC`
  (`0x01`, `0x02`), with the matching 8-byte buffers at `0x03001390`.
* Rejection tests: 7-press prefix, non-code 8-press string, and a
  NEW-only code on the OLD title all left `0x03002FEC` at 0.
* Menu walk: title, save select, game mode, game version, version logo,
  round screen, pause menu (`RETURN` / `GIVE UP`), game over.

**Derived (instruction sequence)**

* The table selector, comparison loop, flag write and handler jump table at
  `0x080060CC`–`0x0800631E`.
* Flag bit 0 is consumed by `0x08012B68` / `0x08013EC8`, both of which return
  0 when it is set; their callers are the per-player collision loops.
* Flag bit 1 has no consumer among the call sites of `0x08002EB0`, and the
  flag word is not read directly elsewhere with mask 2.
* `0x08000C3C` is the sound/jingle helper; its arguments in the handlers are
  channel 2 and sound IDs 0x33 / 0x1E / 0x29.

**Inferred**

* `0x03002FBC` and `0x03002FD8` are two per-player counters (0x1C apart),
  most plausibly lives/continues; the 0x02 code sets both to 100. Their exact
  UI meaning was not isolated.
* The two new codes are leftover debug codes; 0x01 is clearly a collision-off
  (invincibility) flag, 0x02 is partly dead.

## 8. Unknowns

* The exact gameplay meaning of the two 100-valued counters written by the
  0x02 code; no HUD change was observed in the first round.
* The classic "secret word" ending feature is present as text
  (`0x0817DBCC` `THIS IS A KEY OF SECRET GAME.`, `0x0817DC28`
  `& ENTER THE SILVER DOOR !!`, `0x0817DC44` `YOU WILL FIND "ABCD..."`), but it
  is gated by clearing rounds 1–20 without missing a life and entering the
  silver door. It was not reached in this engagement; it is a gameplay-gated
  letter entry, not a title-screen code.
* The embedded multiboot image A’s `ROUND SELECT` screen (`0x083F0C6C`) was
  not exercised: the image boots to a link-wait screen when run standalone.
* The tunes at sound IDs 0x1E, 0x29 and 0x33 were not named.

## 9. Tooling

* `mgba-sdl` 0.10.5 under `Xvfb :216` + `openbox`, `SDL_AUDIODRIVER=dummy`.
* mGBA CLI debugger (`mgba -d`, stub-free) for memory reads, frame stepping
  and screenshots; `xdotool` for input, `scrot` for capture.
* `arm-none-eabi-objdump -M force-thumb`, Python 3 + Capstone for raw scans
  (BL targets, PC-relative literals, table patterns).
* Helper scripts (in `/tmp/opencode/bubblebobble`): `key.py`, `runkey.sh`,
  `runstate.sh`, `dbg3.py`, `blscan.py`.
* Screenshots kept outside the ROM folder: title/menu walk, hidden labels
  (`o1`–`o3`, `q1`–`q4`, `r2`–`r4`), pause menu (`i1`–`i3`), round screen
  (`t1`–`t3`).

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed. This report
contains addresses, algorithms, button sequences and hashes only.
