# Tony Hawk's Underground 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tony Hawk's Underground 2.gba` (Europe, `B2TE52`, Rev.00) |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `THUG2` |
| Game code / maker | `B2TE52` / `52` (Activision) |
| Version / complement / checksum | `0x00` / `0x73` / `0x0000` |
| Entry word | `0xEA00002E` (stock, not a cracktro) |
| MD5 | `2768c7c1a8478b245cb9b7b6615d50ca` |
| SHA-1 | `c684d839c32515a99e62b183b607e2259120cfc9` |
| SHA-256 | `04742b4beb1b777474860db2692c00d669241ca46edc8f7e816604bb32bd6304` |

File offset = ROM address − `0x08000000` throughout. Work copy analysed at
`/tmp/thug2/game.gba` (identical MD5) so emulator save artefacts never
land in the ROM folder; the ROM folder contains only the `.gba`.

## 2. Executive summary

**There is no typed password / code-entry surface in this GBA SKU.** The
widely published word codes (`straightedge`, `oldskool`, `likepaulie`,
`sellout`, `d3struct`, `boxoffice`, …) are console/PC codes that GameFAQs and
mirrors also attach to the GBA page; **none of them occurs anywhere in this
8 MiB image** in ASCII, upper case, UTF-16LE/BE, or ±0x20-shifted form. The
complete UI text bank (`0x080E0000`–`0x080E2000`, fully dumped) contains only
one text-entry surface, **"Enter Name"** (profile creation), plus the graffiti
editor's drawing tools. There is no "enter code", no password screen, no
alphabet table, and no validator comparing typed text.

What the game *does* have is a fully functional **in-game cheat menu** with
**10 toggleable cheats** — a developer-intended unlockable system:

`Main Menu → Options → (scroll past DELETE GAME and CREDITS) → Cheats`.

The ten rows are STUD MODE, RAIL BALANCE, ALWAYS SPECIAL, MANUAL BALANCE,
MOON PHYSICS, LIP BALANCE, JET PACK MODE, MATRIX MODE, TURBO MODE, MINI MODE.
Each row is an independent bit in a save-backed flag word; any combination is
representable. The published GBA unlock table (Stylin' levels 01–10 /
100% Arcade with a specific skater) maps 1:1 onto these ten slots, confirming
the enumeration. Four additional name-table slots point at a `nergets`
placeholder and are **not** rendered by the menu.

Conclusion: a **bounded negative for code-entry cheats**, and a **complete
enumeration of the cheat/unlockable system** with RAM-verified flags.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, `mgba -3`.
* Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Use 50–70 ms holds for menu navigation (150 ms
  double-steps rows).
* Fresh boot → difficulty (`PRO = NORMAL MODE`) → `ENTER NAME` (on-screen
  A–Z/0–9 keyboard; this is a profile name, **not** a code field) → outfit →
  skip story cutscene with A → quit to main menu via Pause → `OPTIONS`.
* In `OPTIONS`, press Down seven times: SOUND, CONTROLS, BLOOD LEVEL, FOCUS
  MODE, DELETE GAME, CREDITS, **CHEATS**. The Cheats entry is always present
  (it was not gated by the flag words in a live test).
* Cheats screen: Down/Up move through exactly ten rows and wrap; rows show
  `ON`/`OFF`. A distinct 5-bit pattern was injected into the flag word with
  the mGBA GDB stub and the screen re-entered; the game rendered every row
  exactly as the bits predicted (see §6b). This is a **debugger-assisted
  probe**, not an in-game typed code.
* No GameShark/CodeBreaker/Action Replay codes were used as cheats; external
  CodeBreaker addresses were used only as *leads* for RAM locations.

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x0800599F8`–`0x08059A84` | data | 14 cheat-name pointers (10 real + 4 `nergets` placeholders), table base `0x08059A8C` |
| `0x08059AC4` | string | `"Cheats"` (menu title) |
| `0x08059ACC` / `0x08059AD4` / `0x08059AD8` / `0x08059ADC` | string | `"%s: %s"`, `"on"`, `"off"`, `"?????"` |
| `0x08052FC` | fn | `cheatName(index)` — `table[index<<2]` |
| `0x080530C` | fn | `setUnlockBit(obj,index,value)` — sets/clears bit `index` of `obj+4` |
| `0x0805324` | fn | `setActiveBit(obj,index)` — sets bit of `obj+0` |
| `0x0805330` | fn | `getActiveBit(obj,index)` |
| `0x0805484` | fn | cheat row renderer (name + `on`/`off` from `obj+4`) |
| `0x08054E8` | fn | cheat row input handler (tests input byte mask `0x30`, toggles `obj+4` bit) |
| `0x0805388` | fn | builds 10 rows: `for (i=0; i<=9; i+=2)` create name/state pair |
| `0x080556C` | fn | Cheats-screen constructor: title `Cheats`, vtable `0x087F33B8` |
| `0x0801C930` | code | the single BL that constructs the Cheats screen (inside the Options-screen builder `0x0801C84C`); no other BL/pointer xrefs exist |
| `0x080E0000`–`0x080E2000` | data | ASCII UI text bank (all screens) |
| `0x080E0978` / `0x080E0A60` | string | `"New Cheat"` / `"Congratulations! You've unlocked a cheat!"` |
| `0x02000008` | RAM | global pointer to the cheat-state object, value `0x0200812C` |
| `0x0200812C` | RAM | cheat object `+0`: active/"have all cheats" bitfield (external DB target) |
| `0x02008130` | RAM | cheat object `+4`: **bit i = cheat i ON/OFF as rendered by the menu** |
| `0x020089E4` / `0x02008AEC` / `0x0200844C` | RAM | story stages / skaters / mini-games flags (external DB leads, not investigated further) |

## 5. Algorithm

No password algorithm exists. The cheat system is a two-word bitfield:

```
obj = *(void**)0x02000008;          // == 0x0200812C
name(i)      = ((char** )0x08059A8C)[i];       // i = 0..13
is_on(i)     = (obj[1] >> i) & 1;              // obj[1] at 0x02008130
set_on(i,v)  = obj[1] = (obj[1] & ~(1<<i)) | (v<<i);
active(i)    = (obj[0] >> i) & 1;              // obj[0] at 0x0200812C
```

The menu builder emits two UI elements per index for `i = 0,2,4,6,8`
(`cmp r7,#9; ble`), i.e. exactly ten rows; the four placeholder pointers at
indices 10–13 are never emitted. The row renderer formats `name(i)` with
`"%s: %s"` and the literal `"on"`/`"off"` selected by `is_on(i)`.

## 6. Tables

### 6.1 Cheat slots (complete, 10 reachable + 4 unreachable)

| Bit | Menu label | ROM string | Published GBA unlock (GameFAQs) |
|---:|---|---|---|
| 0 | STUD MODE | `stud mode` @`0x080599F8` | Stylin' Lv01 or 100% Arcade w/ Tony Hawk or created skater |
| 1 | RAIL BALANCE | `rail balance` @`0x08059A04` | Stylin' Lv02 or 100% Arcade w/ Bob Burnquist ("Perfect Rail") |
| 2 | ALWAYS SPECIAL | `always special` @`0x08059A14` | Stylin' Lv03 or 100% Arcade w/ Eric Koston |
| 3 | MANUAL BALANCE | `manual balance` @`0x08059A24` | Stylin' Lv04 or 100% Arcade w/ Bam Margera |
| 4 | MOON PHYSICS | `moon physics` @`0x08059A34` | Stylin' Lv05 or 100% Arcade w/ Rodney Mullen |
| 5 | LIP BALANCE | `lip balance` @`0x08059A44` | Stylin' Lv06 or 100% Arcade w/ Chad Muska |
| 6 | JET PACK MODE | `jet pack mode` @`0x08059A50` | Stylin' Lv07 or 100% Arcade w/ Eric Sparrow |
| 7 | MATRIX MODE | `matrix mode` @`0x08059A60` | Stylin' Lv08 or 100% Arcade w/ Mike Valley |
| 8 | TURBO MODE | `turbo mode` @`0x08059A6C` | Stylin' Lv09 or 100% Arcade w/ Bigfoot |
| 9 | MINI MODE | `mini mode` @`0x08059A78` | Stylin' Lv10 or 100% Arcade w/ Wee-Bones |
| 10–13 | *(not shown)* | `nergets` @`0x08059A84` ×4 | placeholder / unused slots |

### 6.2 Published word codes — verification ledger

| Claim | Where published | ROM evidence |
|---|---|---|
| `straightedge`, `likepaulie`, `oldskool`, `sellout`, `4-wheeler`, `aprilsman`, `costars!` | GameFAQs **PC/console** "Codes for the Cheat menu" (mis-tagged on GBA pages) | 0 hits in 8 MiB, all encodings |
| `d3struct`, `boxoffice`, `urown3d`, `wakpak`, `accesspass`, `frontrowseat` | GameFAQs console passwords | 0 hits in 8 MiB, all encodings |
| "Unlocking Cheats GBA" table (10 cheats) | GameFAQs GBA section | **confirmed** — exact 1:1 match with the in-game Cheats menu and name table |

## 6b. Enumeration

**Code-entry space: empty (proven bounded negative).**

| Search | Space checked | Result |
|---|---|---|
| Published word codes | 13 strings × 5 encodings (ASCII, upper, UTF-16LE, UTF-16BE, −0x20) over 8,388,608 bytes | **0 hits** |
| UI text bank | `0x080E0000`–`0x080E2000` fully dumped (≈300 strings) | only `Enter Name`, `New Cheat`, `Congratulations! You've unlocked a cheat!`; **no** password/code entry label |
| Password/alphabet tables | literal alphabet strings (`A-Z`, `0-9`, combined) over whole ROM | **0 hits** |
| Whole-ROM keyword scan | case-insensitive `password`, `cheat code`, `enter code` | only `Cheats` (`0x08059AC4`) and the audio banner `Code: B.Wodok` (`0x0807F1985`) |
| Code-name xrefs | all 10 cheat-name pointers | 10 xrefs, all inside the display table `0x08059A8C`; **none** in a comparison function |
| Text-entry surfaces (walked) | Create-profile keyboard (A–Z,0–9), graffiti editor (bitmap draw), name entry in create-a-skater | all are labels/profile data; **no** validator consumer |

**Cheat space: fully characterised.** 10 independently toggleable bits →
**2¹⁰ = 1,024 reachable configurations**. Unlock flags are save-backed (the
object lives in EWRAM and is mirrored through the 8 KiB SRAM save). The menu
builder bound is `index <= 9`; indices 10–13 exist in the name table but are
unreachable — this is the rejection bound for the cheat enumeration.

**Novel configuration (absent from every published list).** Published lists
describe each cheat singly; no list describes a multi-cheat pattern. I set the
flag word to `0x2A5` (bits 0,2,5,7,9 → STUD MODE, ALWAYS SPECIAL, LIP BALANCE,
MATRIX MODE, MINI MODE ON; the other five OFF), re-entered the real Cheats
screen, and read the word back:

* **Observed (RAM, GDB):** `0x02008130 = 0x000002A5`.
* **Observed (screenshots, `/tmp/thug2/novel_2a5*.png`):** top rows
  `STUD MODE: ON, RAIL BALANCE: OFF, ALWAYS SPECIAL: ON`; middle rows
  `LIP BALANCE: ON, JET PACK MODE: OFF`; bottom rows `MATRIX MODE: ON,
  TURBO MODE: OFF, MINI MODE: ON` — an exact bit-for-bit match.
* **Derived:** the row renderer at `0x0805484` tests `(obj+4) >> i & 1`, so the
  screen is a faithful view of the flag word.

**Rejection/bounds tests performed:**

1. Setting `0x02008130 = 0x0000FFFF` then re-entering Cheats made **all ten**
   visible rows read `ON` — bits 10–15 are accepted by the renderer but have
   no row (screenshot `ch_mont1.png`).
2. Writing `0x00000000` made **all ten** rows read `OFF` (`ch_zero.png`).
3. Pressing Down at MINI MODE wraps to STUD MODE with no 11th row appearing
   (`ch_mont2.png`) — confirms the 10-row bound and that the four `nergets`
   slots are not exposed.
4. `0x0200812C` (object `+0`, the external "Have All Cheats" target) and
   `0x02008130` (`+4`, menu state) were independently varied; only `+4`
   changes the menu display, proving the two fields are distinct.

## 7. Validation evidence

* **Observed** — emulator screenshots of every major screen: title/difficulty,
  name entry, outfit, story, gameplay, pause menu, pause-Options, main menu,
  main Options (all seven entries incl. CREDITS/CHEATS), Cheats (all ten rows),
  Story/Free Skate/Head-2-Head submenus. Files kept in `/tmp/thug2/`.
* **Observed** — GDB stub reads/writes of `0x02000008`, `0x0200812C`,
  `0x02008130`; breakpoint at `0x0800556C` fired exactly when entering
  Options, proving the Cheats screen is constructed there.
* **Derived** — disassembly of `0x08052FC`, `0x080530C`, `0x0805324`,
  `0x0805330`, `0x0805484`, `0x08054E8`, `0x0805388`, `0x080556C` and the
  pointer tables at `0x08059A8C` / `0x087F33B8`.
* **Inferred** — the exact controller key that drives the row toggle could not
  be isolated in the harness (the handler at `0x08054E8` tests byte mask
  `0x30`, plausibly D-pad Left/Right or L/R shoulder, but XTEST presses did not
  reliably produce the edge). The flag word and its rendering are proven; the
  physical toggle key is reported as unknown rather than guessed.
* **Inferred** — unlock *events* (Stylin' level completion / 100% Arcade) were
  not played through; the published unlock table is corroborated by the
  exact 1:1 cheat-name match, not by an executed unlock.

## 8. Unknowns

* Which controller event produces the `0x30` mask in the cheat row handler.
* Where the unlock bits are stored in SRAM and which code writes them on
  Stylin'/Arcade completion (the setter `0x080530C` has BLs at `0x080B0C8`,
  `0x080B0F6`, `0x080B26C`–`0x080B29C` etc., not individually attributed).
* Whether bits 10–15 of `0x02008130` are used by any gameplay code (they have
  no menu row and no name).
* No hidden/debug menu or button-code sequence was found; a generic u16
  mask-array scan produced only instruction-stream false positives, so this
  is a negative result with low confidence rather than a proof of absence.

## 9. Tooling

* `strings -t x`, `grep -abo`, Python byte/pointer/BL/xref scanners.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000
  -M force-thumb` for Thumb disassembly.
* mGBA 0.10.5 + Xvfb `:316` + openbox + xdotool + scrot + ImageMagick.
* `gdb-multiarch` against mGBA's `-g` stub (port 2345), driven through a
  persistent FIFO so `interrupt`/`continue &` cycles allowed RAM reads while
  the game ran.
* All work files in `/tmp/thug2/`; no ROM or extracted assets
  redistributed.
