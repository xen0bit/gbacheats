# Danny Phantom: The Ultimate Enemy (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Danny Phantom: The Ultimate Enemy/Danny Phantom: The Ultimate Enemy.gba` |
| Size | 4,194,304 bytes (4 MiB, 0x400000) |
| Header title | `DANNYPHANTOM` (0xA0–0xAB) |
| Game code | `BUEE` (0xAC–0xAF) |
| Maker | `78` (0xB0–0xB1) |
| Version | 0x00 (0xBC) |
| Fixed byte 0xB2 | 0x96 |
| Entry word | `0xEA00002E` (stock ARM branch to 0x080000C0) |
| Complement byte | stored 0x30, computed 0x2C — **mismatch** |
| Header checksum | stored 0x0000, computed 0x00D0 — **not initialised** |
| MD5 | `5964add1d23b22f8947fc3372bd18306` |
| SHA-1 | `0760350c2d71cd9b7f3cfa9e2e30b682defe0901` |
| SHA-256 | `a88c36755e56a7732cde373d1f844fafad4b8fe2388218c3dc4e78c0557a2541` |

Nintendo-logo scan of the whole file returns exactly **one** header (file offset 0x4): single image,
not a multi-game pack. The entry word is stock and no cracktro/trainer strings (`CRC BANDIT`,
`SUNHORS`, `Mode7`) occur; the complement/checksum anomaly is the §16.1 "rebuilt header" artefact of a
dumper/trimmer.

## 2. Executive summary

**The Passwords screen was found and reversed.** It is screen-module **id 4**, reached from the
Options menu:

```
boot → title (id 17) → A → id 19 → A → id 2 (save/start menu)
  Start/Return → the 3-item menu
  Down (to item 1) → A → id 3 (Options, 5 items)
  Down (to item 1) → A → id 4 (Passwords)
```

The screen is a 3-row × 11-column letter picker. The player moves a cursor over a grid of
**background tile cells**, presses A to append the highlighted cell to a **four-slot** buffer, and
after the fourth letter the next A runs the validator. The validator is a chain of exactly **six
four-letter comparisons** and then a reject path.

**All six published four-letter codes are present, byte for byte, as cell comparisons**, and each was
entered on the real screen in mGBA and accepted:

| Code | k | In-game result observed |
|---|---:|---|
| `JAZZ` | 0 | returns to the unlock screen (id 6), then A → id 9 (Levitation mini-game) |
| `SEEK` | 1 | id 6 (Hidin' Ghost Seek mini-game unlock) |
| `DASH` | 2 | id 6 (Dash's Haunted Locker mini-game unlock) |
| `ECTO` | 3 | id 6 (Sam's X-ray Ecto Detector mini-game unlock) |
| `VLAD` | 4 | returns to the start menu (id 2) — difficulty unlock |
| `RUSH` | 5 | id 13 (Ghost Arena), A → id 0 (gameplay) |

The "absence" recorded in earlier drafts is now explained: the codes are not stored as text. Each
letter is stored as a **sprite pair `(tile, y)`** — the exact grid cell the cursor was on — and the
validator compares those pairs.

**The 5–7 letter GameGenie codes cannot be entered on this screen.** The commit path is hard-capped
at four letters (`cmp count,#3; bhi → validate`), the buffer is four 8-byte letter records, and the
validator contains exactly six four-letter blocks and no other accept branch. Entering a 7-letter
word leaves at most four committed letters; the fifth A validates (and fails) instead of appending.
A whole-ROM search found no second letter-entry widget, no second table in the same cell encoding,
and no text/packed/affine encoding of any of the nine long codes. That is a bounded negative
(§6b), not "not looked for". The public GBA FAQ explicitly claims those words for this screen; the
ROM disagrees. Either the list is contaminated from the DS version (which exists, also by Altron) or
the part codes use a surface that is not in the Options path. See §8.

**Status against §0.2: partially met, reported honestly.**
The four-letter space is fully characterised (33⁴ cell sequences, six accepted), the validator is
modelled exactly, and rejection is proven in-game. **No novel code can exist for a closed six-entry
lookup**; §0.2's "novel code" deliverable is structurally impossible for this screen. The 5–7 letter
surface remains the open gate of §8.

## 3. How to reproduce

Emulator: mGBA SDL under `Xvfb :277` (1024×768×24) + `openbox`, `SDL_AUDIODRIVER=dummy`, scale `-3`.
Keys: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad arrows.

**Important harness note.** mGBA's SDL window ignores XTEST events unless the window is truly
*activated*; `xdotool windowfocus` is not enough in this environment. Use
`xdotool windowactivate --sync <win>` before every key. Also hold keys only **40–60 ms**: a 90 ms
hold is seen twice by this game's menu code and moves the cursor two columns.

Exact path (each step confirmed by reading the current screen id from RAM; see §4.4):

1. Boot. Current screen id = 17 (title).
2. Press A (one press, `x`) → id 19; press A again → id 2 (start/save menu).
3. Press Start (`Return`). A three-item menu appears (40 sprites; the earlier drafts called this the
   "sprite-labelled menu").
4. Press Down once (cursor from item 0 to item 1), then A → id 3 (Options menu, 5 items).
5. Press Down once (Options item index 0 → 1), then A → **id 4, the Passwords screen**.
6. The cursor starts on row 0, column 0 (`A`). Left/Right move through columns
   `0x1E,0x2E,…,0xBE` (11 values); Up/Down move through rows `0x52,0x64,0x76`
   (A–K / L–V / V–Z + functions). A appends; after four letters the next A validates.
7. To type `DASH`: Right×3, A; Left×3, A; Right×7 + Down, A; Up, A; A.

Savestates: `Shift+F1..F7` (F8+ did not produce a file in this build). Savestates are mGBA `.ssN`
PNGs with a zlib-compressed `gbAs` chunk; the raw chunk is 397,312 bytes.

## 4. Address map

### 4.1 Screen-module system (corrected)

Every screen record is a 0x20-byte ROM record:

```
struct ScreenRecord {          // file layout
  u32 id;                      // +0x00
  u32 init;                    // +0x04  (Thumb pointer, bit 0 set)
  u32 update;                  // +0x08
  u32 draw;                    // +0x0C
  u32 zero, zero;              // +0x10, +0x14
  u32 exit;                    // +0x18
  u32 size;                    // +0x1C  (object size; not always meaningful)
};
```

The earlier draft had the fields shifted by one word (`size` first). The pointer table is at
`0x0810260C` (24 entries, index = screen id).

**Runtime object.** The per-screen object is *not* per-screen allocated: every screen struct points at
one shared object at **`0x03003990`** (IWRAM). The current screen struct pointer is the global
**`0x03000C08`**; the array of 24 screen structs is at `0x03000C10`, each 16 bytes
`{u16 state, u16 state2, u8 flag, u8 pad, u32 unused, u32 record}`. The dispatcher stores the
runtime object (0x03003990) at struct+8 and the record pointer at struct+12; record+4/8/12/24 are the
init/update/draw/exit functions.

Helper functions: `0x08001824` calls the current init, `0x0800183C` the update, `0x08001880` the
exit; `0x0800195C(id)` switches to a screen; `0x08001920` initialises the 24 structs.

### 4.2 The Passwords screen (id 4)

| Address | Meaning | Evidence |
|---|---|---|
| `0x08112854` | screen 4 record: id 4, init 0x0802A32C, update 0x0802A450, draw 0x0802A4A0, exit 0x0802A4B8, size 0x418 | Derived (ROM bytes) |
| `0x0802A084`, `A0E4`, `A14C`, `A1B0` | init helpers (load the keyboard tiles / panel) | Derived |
| `0x0802A450` | update: per-frame animation and the 8-slot draw loop | Derived |
| `0x0802A6A4` | draw one letter slot | Derived |
| `0x0802A7C0` | per-slot state machine (6 states) | Derived |
| `0x0802A9BC` | **A-button handler: appends a letter, then validates** | Derived + Observed |
| `0x0802AA98` | validator block 1 — `JAZZ` (k=0) | Derived + Observed |
| `0x0802AB18` | validator block 2 — `SEEK` (k=1) | Derived + Observed |
| `0x0802AB90` | validator block 3 — `DASH` (k=2) | Derived + Observed |
| `0x0802AC08` | validator block 4 — `ECTO` (k=3) | Derived + Observed |
| `0x0802AC80` | validator block 5 — `VLAD` (k=4) | Derived + Observed |
| `0x0802ACF8` | validator block 6 — `RUSH` (k=5) | Derived + Observed |
| `0x0802AD74` | reject path (sound 4; `obj+0x38F` feedback flag when 4 letters were entered) | Derived |
| `0x0802AF0C` | A/B input handler (mask 1 = A, mask 2 = B) | Derived |
| `0x0802B070` | d-pad handler (0x10 Left, 0x20 Right, 0x80 Down, 0x40 Up) and cursor clamping | Derived |
| `0x08000ED8` | **unlock-flag setter**, argument k=0..5 | Derived |

### 4.3 Object layout used by the password screen

Object base is `0x03003990`. Offsets:

| Offset | Meaning |
|---|---|
| `+0x38` | screen state byte (0..4: fade-in, idle, fade-out, ...) |
| `+0x3A` | exit request byte |
| `+0x40` | screen sub-state |
| `+0x44` | "exit after success" byte |
| `+0x46` | animation timer |
| `+0x48` | cursor blink counter |
| `+0x49..+0x50` | eight per-column "has a letter" flags (only 4 are ever set) |
| `+0xB0` | cursor X in pixels (starts 0x1F = 31) |
| `+0xD8` | **cursor tile id** (this is what gets stored as the letter's first dword) |
| `+0xDC` | **cursor row Y** (stored as the letter's second dword) |
| `+0x2E5 + i*0x44` | per-slot animation state for slot i (0..7) |
| `+0x3F4 + i*8` | letter slot i: `{u32 tile, u32 row}` (i = 0..3) |
| `+0x414` | number of committed letters (0..4) |
| `+0x415` | failure counter |
| `+0x416` | success flag (set to 1 when a code matched) |

### 4.4 Reading the current screen id

```
cur = *(u32*)0x03000C08            // current screen struct
rec = *(u32*)(cur + 12)            // record pointer
id  = *(u32*)(rec)                 // record+0 = id
```

### 4.5 Unlock flags

`0x08000ED8(k)`:

```
*(u8*)0x03001CDC = 1                       // "a password was used"
if k <= 3: *(u8*)(0x03001CCA + k) = 1
else:      *(u8*)0x03001CD1 = 1
           *(u8*)0x03001DF4 = 1
```

The per-code bits at `0x03001CCA+k` were observed for JAZZ/SEEK/DASH/ECTO exactly as the code
predicts. VLAD (k=4) was observed setting `0x03001CD1` and `0x03001DF4`. RUSH uses k=5; both
k>3 branches store to the same two bytes, so the *distinct* per-code effect is carried by the
screen/exit path, not by those two bytes.

## 5. Algorithm

### 5.1 Input and cursor (reimplementation)

```
grid:
  row 0 (Y=0x52): columns 0..10 -> tiles 0x1E,0x2E,...,0xBE  (letters A..K)
  row 1 (Y=0x64): columns 0..9  -> tiles 0x1E,0x2E,...,0xAE  (letters L..U)
                  column 10     -> 0xBE, a function cell
  row 2 (Y=0x76): columns 0..4  -> tiles 0x1E,0x2E,...,0x5E  (letters V,W,X,Y,Z)
                  columns 5..10 -> function cells

Right: tile += 0x10; wrap after 0xBE back to 0x1E
Left : tile -= 0x10; wrap before 0x1E back to 0xBE
Down : Y = 0x52 -> 0x64 -> 0x76 -> 0x52
Up   : Y = 0x52 -> 0x76 -> 0x64 -> 0x52
```

This gives 26 letters plus 7 function cells (one at row 1 col 10, six at row 2 cols 5–10). `SEEK`
confirms `S = (0x8E,0x64)` = row 1 col 7, which forces `L..U` on row 1; `VLAD` confirms
`V = (0x1E,0x76)` = row 2 col 0.

### 5.2 Commit and validate

```
on A:
  count = obj[0x414]
  if count <= 3:
      obj[0x3F4 + count*8 + 0] = obj[0xD8]     // tile
      obj[0x3F4 + count*8 + 4] = obj[0xDC]     // row Y
      obj[0x49 + (obj[0xB0]/24)] = 1
      obj[0x414] = count + 1
      play sound 0x2C
  else:
      validate()
```

`validate()` (0x0802A9BC, after the count check) compares the **eight dwords**
`obj+0x3F4 .. obj+0x410` (four `{tile,row}` pairs) against six constant sequences. Every one of the
eight comparisons must match. On a match:

```
sound(3)
obj[0x416] = 1
bl 0x08000ED8(k)                 // k = block index 0..5
obj[0x44]  = 1
return 1                          // caller animates out; the screen-exit path
                                  // then selects the next screen seen in §2
```

On failure: sound(4), a feedback flag, the buffer is cleared (`obj[0x414] = 0`) and the screen stays
on id 4.

### 5.3 Why the long codes cannot be entered here

The commit branch is guarded by `cmp count,#3; bhi validate`. The buffer is four 8-byte records at
`0x3F4..0x414`; the validator reads exactly those four records. There is no code path that reads a
fifth or later record. Entering a 7-letter word therefore commits at most four letters; the next A
validates the first four and fails. This was observed directly: after typing `PHANTOM` the buffer
held three letters and count had been reset by an intervening failed validation.

## 6. Tables

### 6.1 Cell map (derived, verified by the six codes)

| Row | Y | Col 0 | Col 1 | Col 2 | Col 3 | Col 4 | Col 5 | Col 6 | Col 7 | Col 8 | Col 9 | Col 10 |
|---|---:|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 0x52 | A 1E | B 2E | C 3E | D 4E | E 5E | F 6E | G 7E | H 8E | I 9E | J AE | K BE |
| 1 | 0x64 | L 1E | M 2E | N 3E | O 4E | P 5E | Q 6E | R 7E | S 8E | T 9E | U AE | fn BE |
| 2 | 0x76 | V 1E | W 2E | X 3E | Y 4E | Z 5E | fn 6E | fn 7E | fn 8E | fn 9E | fn AE | fn BE |

Cell = `(tile,Y)`; e.g. `DASH` = `(4E,52) (1E,52) (8E,64) (8E,52)`.

### 6.2 The validator's six blocks and effects

| Block address | Constant pairs (tile,Y) | Code | k | Observed result |
|---|---|---|---|---|
| `0x0802AA98` | `AE52 1E52 5E76 5E76` | JAZZ | 0 | id 6 (unlock screen); A → id 9 |
| `0x0802AB18` | `8E64 5E52 5E52 BE52` | SEEK | 1 | id 6 |
| `0x0802AB90` | `4E52 1E52 8E64 8E52` | DASH | 2 | id 6 |
| `0x0802AC08` | `5E52 3E52 9E64 4E64` | ECTO | 3 | id 6 |
| `0x0802AC80` | `1E76 1E64 1E52 4E52` | VLAD | 4 | id 2 (back to start menu) |
| `0x0802ACF8` | `7E64 AE64 8E64 8E52` | RUSH | 5 | id 13; A → id 0 (Ghost Arena) |

There is **no seventh block**. Branches after block 6 go to `0x0802AD74` (reject).

### 6.3 Screen flow (corrected)

| From | Action | To |
|---|---|---|
| 17 (title) | A | 19 → 2 |
| 2 (start/save menu) | Start, then item 1 | 3 (Options) |
| 3 (Options, 5 items) | item 0 | 7 |
| 3 | **item 1** | **4 (Passwords)** |
| 3 | item 2 | 6 (static promo/info page) |
| 3 | item 3 | stays 3; sets `obj+0x296` (a sub-page flag) |
| 3 | item 4 | brief 61-sprite page, then back to 28 |
| 4 | valid code | see §6.2 |
| 4 | invalid code | stays 4, buffer cleared |

The Options menu was located as screen **3** with 5 entries; its selected index is `obj+0x295`
(0..4). The previous report's "3-item menu" is the start/save menu (screen 2), not Options.

### 6.4 Fonts / text

Unchanged from the prior draft: seven font descriptors at `0x08107B48` with ASCII char lists; the
menu labels are graphics, which is why `strings` finds no `PASSWORD`/`OPTIONS`. That is no longer a
blocker: the password UI is graphics-driven and was reached by input, not by text search.

### 6.5 Screen descriptor table (24 modules)

Pointer table `0x0810260C`; records are 0x20 bytes with the layout of §4.1. The init/update/draw/exit
words are stored with the Thumb bit set (clear bit 0 to disassemble).

| id | record | init | update | draw | exit | size |
|---:|---|---|---|---|---|---:|
| 0 | 0x08107BD4 | 0x08008641 | 0x08008AFD | 0x08008EB9 | 0x08008F1D | 0x3E64 |
| 1 | 0x08111FF8 | 0x0801C48D | 0x0801C599 | 0x0801C6DD | 0x0801C715 | 0x1E4 |
| 2 | 0x08112814 | 0x08027711 | 0x08027849 | 0x08028099 | 0x080280B5 | 0x538 |
| 3 | 0x08112834 | 0x080294D9 | 0x08029621 | 0x0802A035 | 0x0802A051 | 0x2A0 |
| **4** | **0x08112854** | **0x0802A32D** | **0x0802A451** | **0x0802A4A1** | **0x0802A4B9** | **0x418** |
| 5 | 0x0811F718 | 0x080300D9 | 0x08030239 | 0x08030359 | 0x08030379 | 0x298 |
| 6 | 0x08121354 | 0x08030A91 | 0x08030B9D | 0x08030E19 | 0x08030E35 | 0x2CC |
| 7 | 0x08112874 | 0x0802B619 | 0x0802B751 | 0x0802B7A1 | 0x0802B7B9 | 0x2AC |
| 8 | 0x081136E8 | 0x0802C40D | 0x0802C6A9 | 0x0802C93D | 0x0802C959 | 0x3CC |
| 9 | 0x08121374 | 0x08031DD5 | 0x08031EE1 | 0x080320D1 | 0x08032101 | 0xA78 |
| 10 | 0x08121394 | 0x08035721 | 0x08035845 | 0x080358C1 | 0x080358D9 | 0x610 |
| 11 | 0x081213B4 | 0x08037001 | 0x08037181 | 0x08037369 | 0x08037385 | 0x5F0 |
| 12 | 0x08122468 | 0x0803AB4D | 0x0803ADBD | 0x0803AE71 | 0x0803AEB9 | 0xBEC |
| 13 | 0x081228B8 | 0x080404D5 | 0x08040655 | 0x08040829 | 0x08040841 | 0x2A4 |
| 14 | 0x081120C8 | 0x08021225 | 0x0802135D | 0x08021391 | 0x080213D1 | 0x834 |
| 15 | 0x081121C8 | 0x08021859 | 0x08021965 | 0x080219AD | 0x080219C5 | 0xB0 |
| 16 | 0x08112700 | 0x080221E1 | 0x08022339 | 0x08022481 | 0x080224A1 | 0x6F0 |
| 17 | 0x08112720 | 0x08023991 | 0x08023ABD | 0x08023AF9 | 0x08023B11 | 0x98 |
| 18 | 0x08112794 | 0x08025655 | 0x080257C5 | 0x080257F9 | 0x08025811 | 0x2F4 |
| 19 | 0x081127B4 | 0x08025F89 | 0x080260FD | 0x08026131 | 0x08026149 | 0x228 |
| 20 | 0x081127D4 | 0x0802674D | 0x080268B1 | 0x08026901 | 0x08026919 | 0x27C |
| 21 | 0x081127F4 | 0x08026FBD | 0x080270E9 | 0x08027175 | 0x0802718D | 0x6C |
| 22 | 0x08122A28 | 0x080412B5 | 0x08041419 | 0x080414B5 | 0x080414F1 | 0xB50 |
| 23 | 0x08122CE8 | 0x08044E95 | 0x08044FE9 | 0x08045089 | 0x080450A1 | 0x760 |

A second id-0 record exists at `0x0810C618` with different functions (init 0x0801B091, update
0x0801B13D, draw 0x0801B6E1, exit 0x0801BF81, size 0x1B281); it is not in the `0x0810260C` table and
is used by a separate dispatcher (a scroll/credits-style screen).

### 6.6 Encoding-search matrix

| Family | 6 short codes | 9 long codes |
|---|---|---|
| ASCII / lowercase / +0x20 / UTF-16LE/BE / UTF-32 / reversed | not present (they are cell pairs) | absent |
| affine byte map `a*idx+b` (a odd 1..255, b 0..255) | absent | absent |
| byte bias `idx+b`, `ord+b` (b 0..255) | absent | absent |
| single-byte XOR / ADD / SUB (1..255) | absent | absent |
| 4/5/6/7-bit packing, all alignments/orders, A=0/A=1 | absent | absent |
| u16/u32 cell pair `(0x1E+0x10c, 0x52/0x64/0x76)` | **present (id 4's six blocks)** | absent |
| base-26 integer, u16/u24/u32, both orders | absent | absent |
| simple hashes (sum, weighted sum, xor, poly 31/33/37/131/257, djb2, sdbm, fnv1a, crc32) in a contiguous table | no table | no table |
| 26-entry alphabet ramps / permutations | n/a | absent |

The hashes did produce false positives against the `0x12FAxx` u16 ramp (all small values occur
there); those were rejected because the region is a literal 0..0x7B counter table, not a code
table.

## 6b. Enumeration

### Space definition

The picker exposes `3 × 11 = 33` cells:
- 26 letter cells (`A`–`Z` in reading order: `A–K`, then `L–U`, then `V–Z`),
- 7 function cells (row 1 col 10, and row 2 cols 5–10; labels not needed, they are not accepted by
  the validator).

The buffer is 4 cells, so the raw input space is **33⁴ = 1,185,921** cell sequences (the intended
alphabet-only space is **26⁴ = 456,976**).

### Accepted set

The validator is a hard-coded chain of six exact 8-dword comparisons. Therefore:

**Accepted set = {JAZZ, SEEK, DASH, ECTO, VLAD, RUSH} — exactly 6 cell sequences**, all of which
are on the published GameFAQs/GameGenie list. This is a *closed lookup table*: the accepted set is
fully characterised, and there is no algorithmic payload, no checksum, and no field to vary.

### Rejection bound (Observed)

| Input | Result |
|---|---|
| `DASA` (4 letters, wrong word) | stays on id 4; buffer cleared; no transition |
| `AAAA` (4 letters) | stays on id 4; buffer cleared |
| 5th letter attempt (`AAAA` + A) | the A is consumed by `validate()`, not by `commit`; `obj+0x414` falls from 4 to 0, so a 5-letter code can never be assembled |
| `PHANTOM` (7 letters) | at most 4 letters can be committed; the 5th A validates and fails; buffer resets |

### Novel code

**No novel code exists for this screen**, because the accepted set is a six-entry lookup. Generating
one is not "hard"; it is impossible without a payload field. The §0.2 requirement is therefore
reported as unattainable for id 4, with the closed set proven by complete enumeration of the
validator's branches and by the in-game rejection of well-formed non-table inputs.

### Bounded negative: the 5–7 letter codes

Evidence that `ENEMY`, `FRIGHT`, `GHOST`, `GHOUL`, `PHANTOM`, `HAUNT`, `FENTON`, `PORTAL`, `DANNY`
are not accepted on id 4:

1. **Input cap.** Commit is guarded by `cmp count,#3`; the buffer is four 8-byte records
   (`0x3F4..0x414`); observed: a 5th A validates instead of appending.
2. **Validator size.** `0x0802A9BC–0x0802AD9A` contains exactly six 4-letter blocks and no other
   accept path; it reads only `0x3F4..0x410`.
3. **Whole-ROM encodings.** None of the nine long words exists as ASCII, lowercase, +0x20,
   UTF-16LE/BE, affine byte map, 4/5/6/7-bit packing, base-26, or the cell `(tile,y)` encoding used
   by id 4 (byte, u16 and u32 forms). Single-byte XOR/ADD/SUB tables were also absent.
4. **No second widget.** No other code in the image contains a cluster of `cmp` immediates in the
   id-4 tile set (`0x1E+0x10*i`, `0x52/0x64/0x76`) except id 4 itself and its own cursor clamp at
   `0x0802B0D2`. The id-4 helper routines are called only from id 4 (BL scan).
5. **No 5–7 slot letter buffer** was found: the only 8-slot loop in a password-like widget is id 4's
   animation loop, which is still limited to four committed letters.
6. **A mode-flag dead end.** Options item 3 (index 3) sets `obj+0x296 = 5` (an Options sub-page flag).
   Selecting item 3, then returning to Passwords (item 1), still gives the four-letter screen with
   the same `cmp count,#3` cap (A×5 trace: count 1→2→3→4→0). The flag does not unlock a long mode.

The public GBA FAQ claims these words for Options → Passwords. The ROM does not implement them on
that screen. The most likely explanations are (a) the list is contaminated from the DS version of the
same title (also developed by Altron, and the long words read like DS/console part unlocks), or
(b) the part codes use a different, still-unlocated surface. This is recorded as an unresolved gate
in §8, not as a proven absence of the codes from the title.

## 7. Validation evidence

**Observed (emulator/RAM)**
- Boot → 17; A → 19 → 2; Start → 3-item menu; item 1 → 3 (Options, 5 items); item 1 → 4.
- On id 4: `obj+0xB0=0x1F`, `obj+0xD8=0x1E`, `obj+0xDC=0x52`, `obj+0x414=0`, `obj+0x40=0`.
- Right changes `obj+0xD8` by +0x10 (11 columns, wrap at 0xBE→0x1E); Down changes `obj+0xDC`
  0x52→0x64→0x76→0x52.
- A appends `(obj+0xD8, obj+0xDC)` at `0x3F4+8*count`; observed `DASH` building
  `(4E,52) (1E,52) (8E,64) (8E,52)` and count 1→4.
- Accept: DASH→6, SEEK→6, ECTO→6, JAZZ→6 (then A→9), VLAD→2, RUSH→13 (then A→0).
- Reject: `DASA` and `AAAA` stay on 4; the validating A clears the buffer (count 4→0).
- 5-letter/7-letter attempts never commit more than four letters.
- `0x08000ED8` flag effects (derived from the setter and observed in RAM): JAZZ sets
  `0x03001CCA`, SEEK `0x03001CCB`, DASH `0x03001CCC`, ECTO `0x03001CCD`; VLAD sets
  `0x03001CD1` and `0x03001DF4`. The setter also writes the "a password was used" byte at
  `0x03001CDC`.

**Derived (ROM)**
- Screen record layout (id, init, update, draw, exit, size) and the pointer table at `0x0810260C`.
- Runtime object base `0x03003990` and current-screen struct pointer `0x03000C08`.
- Complete six-block validator and its constants; the reject path.
- The cell map in §6.1 (letters derived from the six accepted blocks; `W/X/Y` are the only
  row-2 letters not directly exercised by a code).
- The `0x08000ED8` flag layout.

**Inferred / not fully played**
- The exact mini-game launched by each of id 6's branches (the screen transition is observed; the
  mini-game was not played to completion).
- The row-2 function cells' labels.

## 8. Unknowns and the exact remaining gate

1. **Where the 5–7 letter part codes are entered.** The Options → Passwords screen is a 4-letter,
   six-entry lookup and cannot express them. If they are real for AGB-BUEE, the surface is not in the
   Options path: candidates not yet excluded are the Ghost Arena's in-game part/customisation menu
   (reachable after RUSH) and a post-credits/Mission Mode screen. The exact gate: screen 4's commit
   branch (`cmp count,#3` at `0x0802A9D0`) and its four-record validator (`0x3F4..0x410`).
2. **Which DS/GBA SKU the long list belongs to.** The 4-letter half of the published list matches
   this ROM exactly; the 5–7 letter half does not appear anywhere in the image under the encodings
   tested. A DS build would explain the mismatch.
3. **Header rebuild** is a dumper/trimmer artefact; the dialogue bank at 0x115xxx renders in-game,
   so the image is otherwise intact.
4. The `k>3` unlock path stores only two bytes (`0x03001CD1`, `0x03001DF4`); which downstream reader
   distinguishes VLAD from RUSH was not traced (the observed screen transitions already differ).

## 9. Tooling

- `mgba` SDL under `Xvfb :277` + `openbox`; `xdotool` (must use `windowactivate --sync`, 40–60 ms
  holds); `Shift+F1..F7` savestates.
- `arm-none-eabi-objdump -M force-thumb`; Capstone 5.0.7; NumPy for the encoding/hash searches.
- Scripts in `/tmp/opencode/dpultimate/`:
  - `ssx.py` — extract the zlib `gbAs` chunk from mGBA `.ssN` savestates.
  - `h.py` — key injection (window activation + short holds), savestate read, screen-id decode.
  - `probe.py`, `probe2.py` — boot a patched copy of the ROM directly into screen id N and record
    OAM/DISPCNT and key responses (used to enumerate the 24 screen modules).
  - `m2.txt` — full disassembly of the start/save menu update.
  - Inline Capstone/NumPy scans for the validator clustering, cell encoding, affine/packed/hash
    families.

Legal note: no ROM, graphics, audio or game text is redistributed here; only addresses, hashes,
derived tables and search statistics are published.
