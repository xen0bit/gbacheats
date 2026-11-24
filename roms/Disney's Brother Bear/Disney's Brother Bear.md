# Disney's Brother Bear (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney's Brother Bear/Disney's Brother Bear.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `BROTHER BEAR` |
| Game code | `BBRE` (USA) |
| Maker | `4Q` (Disney Interactive) |
| Version | 0x00 (Rev.00) |
| Fixed byte 0xB2 | 0x96 |
| Complement check 0xBD | 0x61 (valid) |
| Reserved 0xBE–0xBF | 0x0000 (normal for a GBA header) |
| Entry word | `0xEA00002E` → 0x080000C0 (stock branch) |
| Nintendo logo | one hit, at file 0x4 (single-image cartridge; no multi-game pack) |
| Save | EEPROM, 512-byte `.sav` produced by mGBA |
| MD5 | `b5c631b432a57920bb683145ec1d50c8` |
| SHA-1 | `4264520d6af1361fc860236f18717cd8d830c9ff` |
| SHA-256 | `14068917210ebde03cf3e3dabb7c3ec575488193d778a7c86913e8ef20582950` |

No trainer, cracktro, or appended payload: the entry branch is the retail
branch, the only Nintendo-logo hit is header 0, and the file is exactly 8 MiB.
The zero at 0xBE is the normal reserved field, not a rebuilt-header artifact
(the complement byte is correct).

## 2. Executive summary

**This ROM contains no in-game password, button-code, or reachable debug/cheat
menu.** It is a normal Vicarious Visions platformer with a save-slot screen, a
four-item pause menu, and four bonus games unlocked by ordinary play.

The only cheat-shaped artifact in the entire 8 MiB is the string **`cheats`**
(text id 60, string at 0x0807C9E0; its text-table entry at 0x0807C400). That
entry has **zero references** anywhere in the image. The same is true of the
lowercase string **`level`** (id 47, entry 0x0807C398, string at 0x0807C90C).
Both sit in the global text table immediately before the 24 level-name strings.
Every other screen label in that group is referenced by a static menu
descriptor; these two are not. The evidence is consistent with a **cut
level-select/debug screen** whose labels were left in the string pool and whose
code and menu descriptor were removed.

The game's screen system was fully enumerated: 13 menu descriptors, 31 menu
items, one static PAUSED descriptor with exactly four items, and 36 level/bonus
records. No descriptor, call site, string reference, or input handler can reach
a "cheats" screen. The published lists located (3rd party cheat indexes index) contain Action Replay memory-edit codes only (out of scope);
no published password or button code was found to verify.

## 3. How to reproduce

* Emulator: mGBA (`/usr/local/bin/mgba`), SDL build, scale 3.
* Display: `Xvfb :320 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`.
* Window: 720×480; capture the root and crop `720x480+153+164`.
* Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad arrows.

Boot and menu path (all observed):

1. Boot → Disney Interactive logo → attract movie → title (`Press START`).
2. `START` → **SLOT SELECT** (4 slots + ERASE).
3. `A` on slot 1 (`lives 5`, 3 gold berries in the test save) → level load.
4. First-time tutorial overlays (green/red/gold totem pages) are advanced with `A`.
5. In level, `START` → **PAUSED** (`resume`, `music`, `sleep`, `quit`).
6. `music` → **MUSIC** (`music on`, `music off`).
7. `sleep` → **SLEEP** (`cancel`, `sleep`; message "Press the R Button + L Button + Select to wake").
8. `quit` → **QUIT LEVEL?** (`cancel`, `quit`).
9. At SLOT SELECT, `ERASE` → **SLOT ERASE**; `A` on a slot → "Are you sure you want to erase slot N?" (`yes`, `no`).

Savestates were used so each probe cost one keypress; every screen above was
walked and screenshotted. The remaining static menus (GAME OVER, four BONUS
GAME prompts, the two-path hub menu) are listed in §6 from their descriptors;
none contains a cheat entry.

## 4. Address map

| ROM address | File offset | Meaning |
|---|---|---|
| `0x08000000` | 0x0 | GBA header |
| `0x080000C0` | 0xC0 | ARM crt0 entry |
| `0x080101BC` | 0x101BC | main KEYINPUT reader (0x04000130 at literal 0x080101E8) |
| `0x08029EB2` | 0x29EB2 | blocking Start-wait loop (second direct KEYINPUT read; title/screen wait, no cheat logic) |
| `0x02003768` | — | input struct: +0 repeat/timer word, +4 held keys, +8 newly-pressed keys |
| `0x080146FC` | 0x146FC | generic menu-object builder (40-byte descriptor, 12-byte item records) |
| `0x080222D0` | 0x222D0 | text-entry resolver: entry → slot → `char*` (language byte 0x02000334) |
| `0x0800D1CC` | 0xD1CC | pause-screen object builder; loads descriptor `0x0807DB78` at 0x0800D24A |
| `0x08021918` | 0x21918 | level/bonus table builder (continues at 0x08021DEC) |
| `0x020076BC` | — | 36 × 40-byte level/bonus table built at boot |
| `0x0807C220` | 0x7C220 | global text table, 128 entries × 8 bytes |
| `0x0807DAD8`–`0x0807DCB8` | 0x7DAD8+ | 13 menu descriptors (see §6) |
| `0x0807DDB8` | 0x7DDB8 | PAUSED item list: resume / music / sleep / quit |
| `0x0807C400` | 0x7C400 | text id 60 entry (`cheats`, string 0x0807C9E0) — **0 references** |
| `0x0807C398` | 0x7C398 | text id 47 entry (`level`, string 0x0807C90C) — **0 references** |

Runtime evidence for the pause menu: in a pause savestate the four item text
entry pointers are stored at EWRAM `0x02026B78`, `0x02026BD4`, `0x02026C30`,
`0x02026C8C` (stride 0x5C), with values `0x0807C3B0` (resume), `0x0807C3C0`
(music), `0x0807C3C8` (sleep), `0x0807C3D0` (quit). The PAUSED descriptor copy
is at `0x02026A00`-region. No fifth item exists in that list.

## 5. Algorithm

### 5.1 Text table and resolver (derived)

* Table base 0x0807C220, stride 8, 128 entries (ids 0–127).
* Each entry is a pointer to a 4-byte slot; the slot holds the `char*`.
* `0x080222D0(entry)` returns `*(char**)*(uint32_t*)entry`; language 1 uses the
  second word of an entry pair.
* Strings are ASCII, NUL-terminated. Item labels are copied to EWRAM by the
  menu builder; level names are kept as ROM `char*` pointers.

### 5.2 Menu builder (derived)

`0x080146FC(object, descriptor)` copies a 40-byte descriptor:

```
+0   u32  unknown (0x10 in the PAUSED descriptor)
+4   u32  title text-entry pointer (0 = no title)
+8   u32  param (0x020070A0)
+12  u32  x
+16  u32  y
+20  u32  vertical spacing
+24  u32  item-list pointer (12-byte records, 0-terminated)
+28  u32  unknown (0x0802E960 in PAUSED)
+32  u32  unknown (0x083F61DC in PAUSED)
+36  u32  flags (1 in PAUSED)
```

An item record is `{ u32 text_entry, u32 action, u32 param }`. The builder
allocates a 0x34-byte object per item and stops at a zero text pointer. There
are 14 call sites of `0x080146FC`; 13 descriptors were found, including four
BONUS GAME prompt descriptors.

### 5.3 Level/bonus table (derived + observed)

`0x08021918` (and its continuation at 0x08021DEC) builds 36 records of 40
bytes at `0x020076BC` at boot:

```
+0   char*  level/bonus name (resolved text id 61..84)
+4   u32    resource pointer
+8   u32    id
+12  u8     behaviour/type byte: observed 0, 1, 2 (1 common for pickup
            bonus games, 2 for chase levels; Mammoth Ride is 0, so the
            exact enum is not proven)
+16  u64    field A (totem/progress bits)
+24  u64    field B (unlock/progress bits)
+32  u32    resource pointer
```

Observed record 0 (Snow Forest 1): name `0x0807C9EC`, +4 `0x080313A4`,
+8 `8`, +12 `0`, +16 `4`, +24 `2`.
The table has 20 level entries (16 normal + 4 chase) and 16 bonus slots
distributed across the four hubs. The four bonus games are Matching Game,
Sliding Game, Salmon Run, Mammoth Ride; they are unlocked by collecting red
totems in specific levels (game text ids 124–126 state the rules). Bonus slots
are identified by name, not by the +12 byte. The table is referenced at
0x0800740C (direct code) and at the literal-pool sites 0x0800C8F8, 0x0800CCA4,
0x0800D358, 0x0800D454, 0x0800DA80, 0x080120A0, 0x08013410, 0x0801349C,
0x080139FC and 0x0801C170, plus the builder's own literal at 0x08021CF4. All
are gameplay, level-load, or unlock checks. None draws a menu.

### 5.4 Input (derived)

The per-frame input path is `0x080101BC`, which fills `0x02003768` (held at +4,
pressed at +8). A second, blocking KEYINPUT read at `0x08029EB2` waits for a
Start edge (title/screen wait); it sets up display registers and contains no
cheat logic. A u16 scan for the documented R+L+Select combination found no
contiguous triple in any of the six orders. The documented R+L+Select
combination (0x304) is the sleep wake check, not a cheat gate; pressing it at
the title, slot-select, pause and in-level screens produced no screen change.

## 6. Tables

### 6.1 Text ids 44–84 (observed/derived)

| id | text | referenced? |
|---:|---|---|
| 44 | `SLEEP` | SLEEP descriptor (0x7DBF0) |
| 45 | `MUSIC` | MUSIC descriptor (0x7DBC8) |
| 46 | `Are you sure you want to erase slot %d?` | code 0x1CCD8 |
| 47 | `level` | **0 refs** |
| 48 | `accept` | code 0x1496C |
| 49 | `back` | code 0x14980 |
| 50 | `resume` | item list 0x7DDB8 |
| 51 | `continue` | 0x7DE84 / 0x7DEE4 |
| 52 | `music` | 0x7DDC4 |
| 53 | `sleep` | 0x7DDD0 / 0x7DE48 |
| 54 | `quit` | 0x7DDDC / 0x7DE00 |
| 55 | `PAUSED` | PAUSED descriptor (0x7DB78) |
| 56 | `QUIT LEVEL?` | QUIT LEVEL? descriptor (0x7DBA0) |
| 57 | `music on` | 0x7DE18 |
| 58 | `music off` | 0x7DE24 |
| 59 | `Press the R Button + L Button + Select to wake` | code 0x1C344 |
| 60 | `cheats` | **0 refs** |
| 61–84 | 20 level names + 4 bonus names | level-table builder 0x21CF8–0x222A8 |

Of 128 text ids, 17 are unreferenced: `1,4,5,6,8,11,12,13,14,15,19,47,60,92,93,94,95`
(92–95 are the `english/fran/deutsch/espa` language names). Zero references
alone is therefore not unique; what singles out 47 and 60 is their position in
the menu-label group (44–60) and the fact that every other label in that group
is used by a descriptor or menu item.

String-pool layout around the cut label (file offsets):

```
0x7C9AC  "Press the R Button + L Button + Select to wake"   (id 59)
0x7C9DC  slot -> 0x7C9AC
0x7C9E0  "cheats"                                           (id 60, 0 refs)
0x7C9E8  slot -> 0x7C9E0
0x7C9EC  "Snow Forest 1"                                    (id 61, level data)
0x7C9FC  slot -> 0x7C9EC
```

The level-table builder loads id 61 at 0x08021CF8; it never loads id 60.

### 6.2 Menu descriptors (13, observed)

| Descriptor | Title | Items |
|---|---|---|
| 0x0807DAD8 | SLOT SELECT | 1, 2, 3, 4, ERASE |
| 0x0807DB00 | SLOT ERASE | 1, 2, 3, 4 |
| 0x0807DB28 | SLOT ERASE | yes, no |
| 0x0807DB50 | (none) | Green Path, Red Path (hub fork) |
| 0x0807DB78 | PAUSED | resume, music, sleep, quit |
| 0x0807DBA0 | QUIT LEVEL? | cancel, quit |
| 0x0807DBC8 | MUSIC | music on, music off |
| 0x0807DBF0 | SLEEP | cancel, sleep |
| 0x0807DC18 | GAME OVER | two empty-label (icon) items |
| 0x0807DC40 | BONUS GAME | continue |
| 0x0807DC68 | BONUS GAME | two empty-label items |
| 0x0807DC90 | BONUS GAME | two empty-label items |
| 0x0807DCB8 | BONUS GAME | continue |

Total: 31 item entries. None is `cheats`, and no descriptor points at text id 60
or at the level-name entries.

### 6.3 Unlockable slots (observed)

36 records at 0x020076BC, in table order:

```
0 Snow Forest 1        1 Matching Game       2 Snow Forest 2
3 Sliding Game         4 Snow Forest 3       5 Snow Forest 4
6 Mammoth Ride         7 Salmon Run          8 Snow Forest Chase
9 Ice Cave 1          10 Ice Cave 2         11 Mammoth Ride
12 Ice Cave 3         13 Matching Game      14 Ice Cave 4
15 Ice Cave Chase     16 Valley of Fire 1   17 Matching Game
18 Valley of Fire 2   19 Sliding Game       20 Valley of Fire 3
21 Mammoth Ride       22 Valley of Fire 4   23 Valley of Fire Chase
24 The Mountain 1     25 The Mountain 2     26 Salmon Run
27 The Mountain 3     28 Sliding Game       29 The Mountain 4
30 Matching Game      31 The Mountain Chase 32 Sliding Game
33 Matching Game      34 Sliding Game       35 Sliding Game
```

These are the only "unlockables": 20 levels plus 4 bonus games in 16 bonus slots
(see text ids 124–126 for the red-totem unlock rule). They are driven by
ordinary collection, not by a code. The same names are drawn in the in-level
HUD (e.g. `Snow Forest 1` at the top right), confirming they are ordinary level
data rather than cheat-only labels.

## 6b. Enumeration

### Space definition

* **In-game code space: empty.** There is no password alphabet, no length rule,
  no checksum, and no validator. The only `ABCDEFGHIJKLMNOPQRSTUVWXYZ` /
  `0123456789` runs are the ASCII/font maps in the 0x4598xx–0x46EExx region,
  not an entry alphabet. The main input reader is 0x080101BC; the only other
  direct KEYINPUT read is the blocking Start-wait loop at 0x08029EB2. A u16
  scan for the R+L+Select triple in all six orders found no contiguous key-mask
  triple in the image. More decisively, no screen exists to consume a cheat
  sequence (see below).
* **Text space:** 128 ids × 8-byte entries (0x0807C220–0x0807C61F). 17 ids are
  unreferenced; the only cheat-shaped one is id 60 (`cheats`).
* **Menu space:** 13 descriptors, 31 items. The pause descriptor is static and
  has exactly four items; there is no conditional append in the builder.
* **Unlockable space:** 36 level/bonus records (20 level entries, 16 bonus
  slots); 4 distinct bonus games. The +12 byte takes values 0/1/2 but is not a
  clean bonus flag (Mammoth Ride is 0); the exact enum is unproven.

### Novel code(s)

**None can exist**, because no accepted-input system exists. The equivalent
positive result for this title is the cut-screen identification: `cheats`
(0x0807C400) and `level` (0x0807C398) are text ids that no code, descriptor,
script text pointer, or item list references. If a later prototype or a
different revision restores that screen, its descriptor will be a 40-byte
record in the 0x0807Dxxx table whose +4 title pointer is 0x0807C400 and whose
+24 item list points at the 24 level-name entries (0x0807C408–0x0807C4C0).

### Bounds proven by rejection

* `0x0807C400` (the text-table **entry** for id 60, not the string at
  0x0807C9E0) occurs **0 times** as a 32-bit word in all 8,388,608 bytes
  (its Thumb-bit form 0x0807C401 also occurs 0 times); the only reference to
  the neighboring sleep entry (0x0807C3F8) is the sleep screen at 0x0801C344,
  which uses it directly and never adds 8.
* The 24 level-name entries are referenced only by the level-table builder
  (0x08021CF8–0x080222A8); no menu descriptor and no drawing routine uses them.
* Button-space rejection: 48 probe runs were sent on real screens:
  * title: L+R+Select, A+B, A+B+Start, A+B+Select, Konami, LRLR, Select×5,
    Up/Down×2, L+R+Select×2 — the only screen transition was A acting as Start;
  * SLOT SELECT: Select, L, R, L+R, L+R+Select, A+B, Start+Select, Select+Start,
    L+Select, R+Select, Up+Select, Down+Select, B, B×3, Select×3, Konami,
    LRLR, RRLR, Up×2, Down×2 — no new screen (A+B accepted the slot; Up/Down
    moved the cursor);
  * PAUSED: same set plus L+R+Select held 1.5 s, A+B, A+B+Select,
    Start+Select, Select×2, Konami, LRLR, RRLL, Up/Down — no new screen
    (A accepted the highlighted item);
  * in-level: R+L+Select held 1.2 s — no effect.
* The published GBA codes for this game are Action Replay (memory writes), not
  input codes: 3rd party cheat index lists 6 EU codes, 3rd party cheat indexes 2 US codes; all are
  memory-edit/Master codes and are excluded by the task's scope. An encrypted AR
  payload has no plaintext literal to search in the ROM, and no in-game screen
  accepts it. No published password or button code exists to test.

## 7. Validation evidence

**Observed**
* Title, SLOT SELECT, SLOT ERASE, erase confirmation, in-level HUD, tutorial
  pages, PAUSED, MUSIC, SLEEP and QUIT LEVEL? screens were walked on :320 and
  screenshotted.
* PAUSED has exactly four items; MUSIC two; SLEEP two; QUIT LEVEL? two.
* EWRAM at pause holds four item pointers at 0x02026B78/BD4/C30/C8C.
* 36 level/bonus records at 0x020076BC, including the names and +12 type bytes.
* The R+L+Select message is the sleep wake text; selecting `sleep` enters that
  screen and the same combo wakes it.

**Derived**
* Text table 128 entries; resolver 0x080222D0; 8-byte stride.
* Menu builder 0x080146FC; 40-byte descriptor and 12-byte item layout; 13
  descriptors, 31 items.
* Zero references to 0x0807C400 / 0x0807C398 in the whole image.
* Main KEYINPUT reader plus one blocking Start-wait loop; no R+L+Select mask
  triple.

**Inferred**
* The `cheats` and `level` strings are leftovers of a cut level-select/debug
  screen. The level names themselves are genuine game data and are used by the
  level table, so their presence is not evidence of the cut screen.

## 8. Unknowns

* The original source order of the cut screen (title + 24 items) is inferred
  from string adjacency; no code or descriptor survives to prove its layout.
* The GAME OVER and BONUS GAME prompts were enumerated statically (descriptors
  0x0807DC18/40/68/90/B8) but not forced on screen; they contain no cheat entry.
* Whether an unreleased prototype implements the cut screen is outside this
  image. No save flag, gate byte, or unlock condition in this ROM adds a fifth
  pause item (the builder call at 0x0800D24A is unconditional).

## 9. Tooling

* `python3` + `struct` for header/string/xref scans.
* `capstone` 5.0.7 for Thumb literal-pool and call-site scans.
* `arm-none-eabi-objdump -M force-thumb` for manual confirmation.
* mGBA SDL under `Xvfb :320` + `openbox`; `xdotool` for XTEST input; `scrot`
  and ImageMagick for captures; mGBA `.ss` PNG savestates (`zlib` `gbAs` chunk,
  397,312 bytes; IWRAM at 0x19000, EWRAM at 0x21000) for RAM proofs.

No ROM, graphics, music, or text assets are redistributed in this report.
