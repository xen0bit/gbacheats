# Disney's Little Einsteins (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney's Little Einsteins/Disney's Little Einsteins.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title | `LEINSTEINS` |
| Game code / maker | `BEIE` / `4Q` |
| Software version | 0 |
| Complement byte `0xBD` | `0xB9` (recomputed 0xB9 — valid) |
| Header checksum `0xBE` | `0x0000` (recomputed 0xB9 — header field zeroed, rebuilt-header artifact) |
| Device type `0xB4` | `0x00` — **no backup memory declared** |
| Entry word | `0xEA00002E` → stock branch to `0x080000C0` |
| MD5 | `5a20b7af9d051a12d80986a2980fc1c2` |
| SHA-1 | `77554bd4a954a34023571d5976c5f0696b6fe744` |
| SHA-256 | `b2d41d3f6d9adbe50a50d0259a68706c5b5509879b783712ce06dec9e73ac6a5` |

Phase-0 integrity checks:

* Exactly **one** GBA header: the Nintendo logo occurs only at file offset `0x4`
  (header base 0). There is no second/embedded image and no multi-game pack.
* No cracktro/trainer: the entry branch is stock, the first 4 KiB contain a normal
  crt0 (`0x080000C0` → `0x080000E0` → Thumb at `0x08000100`), and there are no
  cracktro banner strings. Last non-zero byte is `0x7C6793`; everything from
  there to `0x800000` is zero fill, so nothing is appended to the image.
* The only header anomaly is the zeroed `0xBE` checksum field; the `0xBD`
  complement byte still validates, i.e. the header was rebuilt but the image
  is otherwise intact.

## 2. Executive summary

**This ROM has no password system, no button code, no hidden or debug menu, and
no code-gated unlockable.** The conclusion is not "nothing found"; the game's
entire input and menu surface was enumerated:

* **Seven screens + one modal pause**, all reached by normal play:
  boot logos → title → difficulty select (2 items) → mission select (7
  paintings) → per-mission menu (painting + 3 activity icons + back arrow) →
  gameplay (intro cutscene, activity, results) with a 2-item pause. A Start-menu
  opened from mission select offers exactly **3** entries: Difficulty Settings,
  Credits, Exit. Credits are multi-page (≥6 pages: Buena Vista Games staff, QA,
  InLight Entertainment staff).
* **No text-entry surface exists.** There is no on-screen keyboard, no letter
  grid, no cursor, and no validator. The whole 8 MiB contains **zero**
  occurrences of `password`, `passwd`, `cheat`, `debug`, `secret`, `unlock`,
  `code`, `enter`, `gallery`, `bonus`, `sound test`, `options`, `continue`,
  `credits`, `difficulty`, `quit`, `reset` or `erase` in ASCII
  (case-insensitive); the code-related terms were also checked in UTF-16LE
  (zero). The only `menu`/`setup` hits are the dead asset names `GAMEMENU`,
  `MISSIONMENU`, `MISSIONSETUP`.
* **All UI text is baked tile art.** The menu labels (`Continue`,
  `Mission Menu`, `Difficulty Settings`, `Credits`, `Exit`, `Easy`, `Hard`)
  do not exist as byte strings anywhere in the ROM; they are pre-rendered
  frames. This is why a `strings` search returns nothing for the menus and why
  the negative had to be established by screen enumeration plus the input
  census, not by keyword search alone.
* **The input layer never reads Select, L or R.** A full scan of the game's
  single input-query helper finds **106** call sites; the buttons queried are
  A (30), B (12), Start (2), Right (16), Left (16), Up (14), Down (15) and
  **Select (0), R (0), L (0)**. There is exactly one code access to
  `KEYINPUT` in the whole ROM (the poll routine at `0x08054AFC`). Any code that
  requires Select, L or R is therefore structurally impossible, and that
  closes all the classic L+R / Select-based combos.
* **All 45 button pairs and 10 multi-button sequences were pressed on the title
  screen**, and 6 sequences on the mission select; none produced a new screen
  (the engine's screen-stack depth byte stayed at 1–2 on the title and 2–3 on
  the mission select). The one undisplayed completion line
  (`You completed all the Missions!`) sits in a dead string block.
* **No published codes exist to verify.** The GameFAQs cheats page for this SKU
  is empty in both the 2015 and 2020 archived snapshots, the VGChartz cheats tab
  is empty, and no fan/wiki list of Little Einsteins GBA codes could be found.
  There is consequently no public literal to search for in the image, and none
  of the plausible ones were found.

The game is a linear 7-mission edutainment title. Its "code space" is empty:
0 alphabets, 0 lengths, 0 checksum bits, 0 table entries. Section 6b gives the
space that *was* searched and the bounds proven by rejection.

## 3. How to reproduce

Emulator: mGBA (SDL), headless on `Xvfb :330`, `SDL_AUDIODRIVER=dummy`,
`mgba -3 game.gba`.

Default mGBA keymap (verified against `KEYINPUT` bits, see §4):

| GBA | key | mask (`held`) |
|---|---|---|
| A | `x` | `0x001` |
| B | `z` | `0x002` |
| Select | `BackSpace` | `0x004` |
| Start | `Return` | `0x008` |
| Right | `Right` | `0x010` |
| Left | `Left` | `0x020` |
| Up | `Up` | `0x040` |
| Down | `Down` | `0x080` |
| R | `s` | `0x100` |
| L | `a` | `0x200` |

**Important harness note:** holds of 100–150 ms can double-step this game's
menus. Use 45–55 ms taps with ≥0.3 s between taps; a 150 ms hold moved two
menu slots repeatedly during this analysis (the guide's §16.2 warning applies
verbatim).

Savestates: `Shift+F1..F9` saves, `F1..F9` loads. Savestates are PNG files with
a zlib `gbAs` chunk; the raw 397,312-byte state has IWRAM at `0x19000` and
EWRAM at `0x21000`, so all RAM claims below are reproducible with
`zlib.decompress`.

Exact menu path used:

1. Boot: InLight logo → Buena Vista Games logo → title (`PRESS START`).
2. Start → **difficulty select** (`1 Easy` / `2 Hard`). Exactly two entries;
   Right on `Hard` wraps to `Easy`, and no direction reveals a third panel.
3. A → **mission select**: 7 framed paintings on strings.
   Start → **Start menu**: `Difficulty Settings` / `Credits` / `Exit` (3 items).
   `Difficulty Settings` reopens the 2-item difficulty screen, `Credits` opens
   the multi-page credit roll (A advances pages), `Exit` closes the menu back to
   mission select. The menu cursor is layout-driven and its confirm is off by
   one press; the four sequences actually used and observed were
   `A` (no effect), `Right,A` (Difficulty), `Down,Down,A` (Credits),
   `Down,Right,A` (Exit).
4. A on a painting → **mission menu**: the painting plus three circular
   activity icons and a back arrow. Down moves the cursor into the icon row,
   Left/Right move along it, A starts that activity.
5. Inside an activity, Start → **pause**: `Continue` / `Mission Menu` (2 items).

Tests performed:

* Title screen: 10 single buttons + all 45 unordered pairs + 10 named sequences
  (`konami`, `LRLRLR`, `A+B+Start+Select`, `Start+Select`, `Select+Start`,
  `UDUD`, `LRLRBA`, `BBAA`, `L+R+Start`, `A+R+Select+Start`). Only A/Start
  navigated (to difficulty); everything else left the title untouched.
  Savestate RAM comparison between two idle loads is **byte-identical**
  (0 differing bytes), so the negative is exact, not a tolerance.
* Mission select: `konami`, `LRLRLR`, `A+B+Start+Select`, `Start+Select`,
  `BBAA`, `UDUD`. No input pushed a new screen (depth stayed 2–3).
* Every screen also tested with Select, L and R held/tapped: no effect anywhere
  (consistent with the static census: those bits are never queried).

## 4. Address map

File offset = ROM address − `0x08000000` throughout.

### 4.1 Input layer

| ROM address | Role |
|---|---|
| `0x08054AFC` | key poll: copies `0x03004FCC` → `0x03004FC8`, then writes `KEYINPUT & 0x03FF \| 0xFC00` to `0x03004FCC` |
| `0x080549F8` | input query `f(mode, button)` → 0/1; 10-entry button→mask table at `0x08054AE8`, plus a second (mode) jump table inside the same function |
| `0x03004FCC` | current raw key state (active-low, top bits set) |
| `0x03004FC8` | previous frame key state |
| `0x04000130` | `KEYINPUT` — exactly **one** code reference (`0x08054B20` literal pool; 11 other literal-shaped hits are inside compressed graphics) |

Button→mask mapping recovered from the table at `0x08054AE8`
(`A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`).
Query modes 0, 2, 3 and 5 are used by callers (counts in §6).

Control-flow census (all 106 BL targets of `0x080549F8`):

| button | call sites |
|---|---|
| A | 30 |
| B | 12 |
| Start | 2 |
| Right | 16 |
| Left | 16 |
| Up | 14 |
| Down | 15 |
| Select | **0** |
| R | **0** |
| L | **0** |
| (argument not resolvable by the 6-instruction window) | 1 |

Start call sites are `0x08001450` (Start menu from mission select) and
`0x0800A014` (pause/gameplay). The latter also range-checks a small signed index
at `0x020007F8+8` to `0..11`; that index is not a level/mission selector (the
mission index lives in the mission menu code and has 7 values), and no input
path feeds it from a text or code field.

### 4.2 Screen-stack depth byte

`0x03000E88` increments when a screen is pushed:

| screen | value |
|---|---|
| title | 1 |
| difficulty select | 1 |
| mission select | 2 |
| mission menu (painting + icons) | 3 |
| Start menu (options) | 4 |
| gameplay | 5 |
| pause (in gameplay) | 5 |

This byte is the cheap "did anything new open?" oracle used in §6b. Its address
appears as a literal in the module at `0x087C3C2C`.

### 4.3 Script VM

| ROM address | Role |
|---|---|
| `0x080014F8` | opcode dispatch: `index = byte[0x02000B08+0x1A]`, bounds `0x125`, `handler = table[index]` |
| `0x08001900` | **293** Thumb handler pointers (all distinct, all inside `0x08000000–0x0804B7A9`) |
| `0x02000B08` | VM context base |

The engine is a bytecode-VM adventure shell; menus/cutscenes are scripts driven
from that table. This matters because it is where a hidden menu *would* live —
but no script or handler references the dead name block (§4.4).

### 4.4 Text resources

| File offset | Contents |
|---|---|
| `0x78C550` | start of the text/asset bank (after a `0x0A81`-byte `0xFF` gap at `0x78BACF`) |
| `0x78EB98–0x78F0D7` | **dead block**: 36 strings — completion lines, `EASY`, `HARD`, `Prepare for BLAST OFF!`, `Pat with us!`, 4 × `This is sample dialog N text.`, and 26 asset/scene names (`BUMPERS`, `CTBEES`, `CTBIRDS`, `CTBIRTHDAY`, `CTISLAND`, `GAMEMENU`, `INTRO`, `JABEES`, `JABIRDS`, `JAISLAND`, `MISSIONMENU`, `MISSIONSETUP`, `MPBEES`, `MPBIRTHDAY`, `MPCANYON`, `MPFOREST`, `RJCANYON`, `RJFOREST`, `RJPAINTING`, `RPCANYON`, `RPFOREST`, `RPPAINTING`, `TCBIRDS`, `TCBIRTHDAY`, `TCISLAND`, `TCPAINTING`) — **0 references** from anywhere in the ROM (no 32-bit pointer to any of the 36 string starts; the single 4-byte coincidence at `0x1C7BFA` is inside compressed graphics) |
| `0x78F0D8–0x7923EA` | live dialogue bank (mission intros, "Great job!" lines, art/music credits); lines are referenced by **absolute file offsets** (58 distinct values, e.g. `0x790000` referenced 32 times) |

The 26 dead names decompose exactly into **5 system scenes**
(`GAMEMENU`, `MISSIONMENU`, `MISSIONSETUP`, `INTRO`, `BUMPERS`) plus **21 mission
scenes** (`CT`×4, `JA`×3, `MP`×4, `RJ`×3, `RP`×3, `TC`×4), and 21 = the
**7 missions × 3 activity icons** seen on every mission menu. Even taken at face
value the name table contains no extra level.

### 4.5 Save

`0xB4 = 0x00` (no backup). The emulator creates a 0-byte `game.sav` and never
grows it across a full session. No save/load UI exists on any screen. All
progress (mission count) is session RAM only.

## 5. Algorithm

There is no code validator to reimplement. What the ROM does implement, and
what was modelled to prove the negative, is the input layer:

```
poll():                      # 0x08054AFC, once per frame
    prev = cur               # 0x03004FC8 <- 0x03004FCC
    cur  = KEYINPUT & 0x3FF | 0xFC00

query(mode, button):         # 0x080549F8
    m = MASK[button]         # 10-entry table, 0x08054AE8
    return f(mode, m)        # mode 0/2/3/5 semantics (pressed / held / ...)

depth = byte[0x03000E88]     # screen stack, 0..5 observed
```

Consequently a "code" would have to be (a) a text string compared somewhere,
(b) a table of button masks compared against a press history, or (c) a screen
gate. Each was searched:

* (a) no text entry exists; 0 password keywords; no `strcmp` consumer of a text
  buffer (there is no text buffer; see §3).
* (b) 591 u16 runs of button-mask values exist in the image (≥3 presses); 135
  are ≥5 and 40 are ≥8. Only **7** are referenced by a 32-bit literal pointer,
  and all 7 sit inside data blocks reached from a data-pointer table
  (`0x4E8F4`, `0x4EE60`, `0x4EE68`, `0x4EE84`, `0x50CB8`, `0x618AE4`,
  `0x7C3BC0`), not from code; they are animation/palette index arrays
  (e.g. `0x8DDD0: 01 00 40 00 01 00 01 00 00 00 …`). None is a cheat table.
* (c) the only unlisted screens that exist are the ones enumerated; the dead
  name block has no reference, so no gate reads it.

## 6. Tables

### 6.1 Button space (the entire input alphabet)

| index | button | mask | queried? |
|---|---|---|---|
| 0 | A | `0x001` | yes (30) |
| 1 | B | `0x002` | yes (12) |
| 2 | Select | `0x004` | **never** |
| 3 | Start | `0x008` | yes (2) |
| 4 | Right | `0x010` | yes (16) |
| 5 | Left | `0x020` | yes (16) |
| 6 | Up | `0x040` | yes (14) |
| 7 | Down | `0x080` | yes (15) |
| 8 | R | `0x100` | **never** |
| 9 | L | `0x200` | **never** |

### 6.2 Screens and option counts (all observed)

| Screen | Entries | Bound proof |
|---|---|---|
| Title | 1 prompt | B/dirs do nothing; only Start/A leaves |
| Difficulty select | 2 | Right on Hard wraps to Easy (screenshot `d_2`); no third panel |
| Mission select | 7 paintings | 7 distinct arts entered by successive Right presses (Rousseau *Exotic Landscape*, Gauguin *There is the Marae*, Seurat *Seine at La Grande Jatte*, Lascaux cave, Van Gogh *Irises*, Van Gogh *Starry Night*, Seurat *Seascape at Port-en-Bessin*) |
| Mission menu | 3 icons + back | 3 icons drawn and reachable per mission; icon sets differ per painting (e.g. birdhouse/bird/island; boat/guitar/notes; notes/flower/bee); 7×3 = the 21 mission scene names |
| Start menu | 3 | Difficulty Settings / Credits / Exit; `Down,Right,A` activates Exit → returns to mission select; `Down,Down,A` opens Credits |
| Credits | multi-page | ≥6 distinct pages observed (Buena Vista Games staff, QA/certification, InLight staff); A advances |
| Pause | 2 | Continue / Mission Menu; Down past the last item does not add a third |

### 6.3 Dead asset-name table (evidence of cut shell content, not reachable)

```
0x78EC98 BUMPERS      0x78EE1C GAMEMENU      0x78EF04 MPBEES
0x78ECB8 CTBEES       0x78EE3C INTRO         0x78EF24 MPBIRTHDAY
0x78ECD8 CTBIRDS      0x78EE5C JABEES        0x78EF48 MPCANYON
0x78ECF8 CTBIRTHDAY   0x78EE7C JABIRDS       0x78EF68 MPFOREST
0x78ED1C CTISLAND     0x78EE9C JAISLAND      0x78EF88 RJCANYON
0x78ED3C sample dlg 0 0x78EEBC MISSIONMENU    0x78EFA8 RJFOREST
0x78ED74 sample dlg 1 0x78EEE0 MISSIONSETUP  0x78EFC8 RJPAINTING
0x78EDAC sample dlg 2 0x78EFEC RPCANYON      0x78F00C RPFOREST
0x78EDE4 sample dlg 3 0x78F02C RPPAINTING    0x78F050 TCBIRDS
0x78F070 TCBIRTHDAY   0x78F094 TCISLAND      0x78F0B4 TCPAINTING
```

## 6b. Enumeration

**Space definition.** There is no code alphabet, no code length, no checksum,
no reserved bits and no lookup table:

| parameter | value |
|---|---|
| alphabets | 0 (no text entry anywhere) |
| lengths | 0 |
| checksum width/position | none |
| table size (accepted literals) | 0 |
| representable codes | **0** |

**What the enumeration covers instead** (this is the closest analogue for a
button-code system, per §0.2):

| space | size | method | result |
|---|---|---|---|
| single-frame button masks | 1023 non-zero of 1024 | static: every call site of the only input helper | never reads Select/L/R → 7 usable buttons only (`A,B,Start,←,→,↑,↓`) |
| 2-button combinations on title | 45 | pressed all pairs, savestate compare | no new screen, depth ≤ 2 |
| named sequences on title | 10 (incl. Konami, `A+B+Start+Select`, `LRLRLR`, `BBAA`) | pressed, savestate compare | no new screen; depth ≤ 2 |
| sequences on mission select | 6 | pressed, depth byte + full RAM compare | no new screen; depth ≤ 3 (mission menu) |
| u16 button-mask runs ≥3 | 591 (135 ≥5, 40 ≥8) | ROM-wide scan | 7 referenced by literal pointer, all data arrays, none a code |
| u8 button-ID runs ≥4 | 41 022 (mostly zero bytes) | ROM-wide scan | no referenced candidate code table |
| button-keyword literals | 0 | ASCII + UTF-16LE census over all 8 MiB | 0 hits for password/cheat/debug/secret/unlock/code |
| published lists | 0 codes | GameFAQs archive 2015 + 2020, VGChartz, web search | pages exist but contain no codes |

Published-code sources checked (all empty for this SKU):

* `https://web.archive.org/web/20151009103945/http://www.gamefaqs.com/gba/933115-disneys-little-einsteins/cheats`
* `https://web.archive.org/web/20200216062156/https://gamefaqs.gamespot.com/gba/933115-disneys-little-einsteins/cheats`
* `https://www.vgchartz.com/game/26746/disneys-little-einsteins/cheats/` (tab exists, zero entries)
* Web searches for `<title> GBA password / cheat / unlock` returned only the longplay and
  the fandom summary page; no code list was found. The fandom page was not
  machine-readable (HTTP 403), so its text was not used as evidence.

**Bounds proven by rejection (observed in-game):**

1. `Select` pressed on title, difficulty, mission select, Start menu, mission
   menu and pause: no effect on any screen. Static corroboration: the bit is
   never queried by any of the 106 input call sites.
2. `L` and `R` pressed likewise: no effect anywhere; bits never queried.
3. Difficulty select: Right on `Hard` wraps to `Easy`; no direction reveals a
   third difficulty (2-item ring proven by wrap).
4. Pause: `Continue` / `Mission Menu` only; repeated Down/Up never reveal a
   third item.
5. Start menu: 3 items; `Down,Right` on the third (`Exit`) returns to mission
   select rather than opening anything else.
6. Title: all pairs and the 10 sequences leave the screen-stack depth at 1
   (`A`/`Start` alone → difficulty, depth 2); no depth ≥ 3 was ever reached
   from the title.
7. Mission select: sequences leave depth at 2 or 3 (mission menu); no hidden
   depth-4/5 screen is reachable from it except the Start menu (4) and games (5).

**Novel codes.** None can be minted: the format is empty. The deliverable for
this engagement is the closed negative with the space above, not a generated
code. Where a code would live is provably absent — the only candidate text
(dead block, §4.4) has zero references, and the only candidate input bits
(Select/L/R) are never read.

## 7. Validation evidence

**Observed (emulator screenshots / RAM reads):**

* Boot logos (InLight, Buena Vista Games) → title → difficulty → mission select
  → mission menu → activity intro → gameplay → pause; Start menu and credits
  from mission select.
* Seven distinct paintings, each with three distinct activity icons.
* Savestate RAM at `0x03004FCC` mirrors `KEYINPUT` exactly for all ten keys
  (A `0xFFFE`, B `0xFFFD`, Select `0xFFFB`, Start `0xFFF7`, Right `0xFFEF`, …),
  confirming the keymap and the input layer address.
* Two idle savestates on the same screen are byte-identical (0 differing bytes
  in IWRAM `0x03003000-0x03008000` and EWRAM), which makes the combo negatives
  exact rather than thresholded.
* Screen-stack depth byte `0x03000E88` = 1/1/2/3/4/5/5 across title,
  difficulty, mission select, mission menu, Start menu, gameplay, pause.
* `.sav` remains 0 bytes through a full session.

**Derived (instruction-level):**

* Single `KEYINPUT` poll at `0x08054AFC`; all input flows through
  `0x080549F8` (106 call sites).
* Select (index 2), R (index 8) and L (index 9) are never passed to the query
  function; button→mask table at `0x08054AE8`.
* 293-entry Thumb dispatch table at `0x08001900` (bytecode VM), dispatched from
  `0x080014F8` on `byte[0x02000B08+0x1A]`.
* Dead block `0x78EB98–0x78F0D7` (36 strings incl. 26 asset names and 4
  "sample dialog" placeholders) has **no** 32-bit reference anywhere; the live
  dialogue bank starting `0x78F0D8` is referenced by absolute file offsets.
* Header device type 0x00; no save code path exercised.

**Inferred:**

* The 26 dead names are the shipping build's leftover asset/scene list from the
  InLight tool chain; the 6 two-letter prefixes are the six activity types and
  the 21 `prefix+suffix` names are the 21 playable mini-games (7 per-art
  missions × 3). The 7×3 mapping matches the 7 paintings and 3 icons observed,
  and matches the public longplay's 7-level list, but each individual
  prefix→icon assignment was not proven.
* The "You completed all the Missions!" line was intended for a completion
  screen that is not reached in this build (no reference), or is drawn from an
  ID table that was not located.

## 8. Unknowns

* The exact string-ID mechanism for the live dialogue lines: 58 lines are
  referenced by absolute file offset directly from code; the remaining ~246
  lines in the bank are selected by a mechanism not located (likely a per-scene
  script table). This does not affect the negative: no text is ever *entered*.
* Whether the dead 26-name/4-sample-dialog block corresponds to a developer
  scene-select screen that was removed before mastering. The block is
  unreachable in this image (0 references, no input bits for it, no UI art for
  it), so it cannot be triggered.
* The 26 KiB data module at `0x7C0000–0x7C6793` (no strings, sparse data) was
  identified as non-code padding/library data but not mapped field by field.

## 9. Tooling

All commands run from `/tmp/littleeinsteins` against a copy of the ROM
(`game.gba`). No ROM or extracted asset is redistributed.

* `md5sum` / `sha1sum` / `sha256sum`, `file`, `xxd`, `strings -t x`.
* Python 3 with `capstone 5.0.7`: BL-target scan for `0x080549F8` (106 sites),
  call-site argument census, literal-pool verification, u16/u8 mask-run scans,
  reference scans for the dead string block.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for the input poll/query, the two Start handlers and the VM dispatch.
* mGBA SDL under `Xvfb :330` + `openbox`; `xdotool` input (45 ms taps);
  `import -window root` screenshots; savestate PNG → zlib `gbAs` → raw RAM
  (IWRAM `0x19000`, EWRAM `0x21000`).
* Scripts: key helper, title combo matrix, RAM combo matrix, mission walker,
  navigation/classification, RAM diff (all in the work directory; the
  reproducible core is the savestate decode + the two address tables above).

## 10. Legal note

No ROM, graphics, music or game text is redistributed with this report. Only
hashes, addresses, counts, derived algorithms and my own observations are
published.

## 11. Cleanup

Emulator `mgba` (PID recorded at launch), `Xvfb :330` and `openbox` were stopped
by PID; generated `game.ss*`, `game.sav` and screenshots were kept only in the
temporary work directory and removed from the ROM folder.
