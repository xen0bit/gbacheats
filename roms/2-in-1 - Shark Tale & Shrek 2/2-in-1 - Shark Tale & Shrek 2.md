# 2-in-1: Shark Tale & Shrek 2 (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-25.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/2-in-1 - Shark Tale & Shrek 2/2-in-1 - Shark Tale & Shrek 2.gba` |
| Size | 16,777,216 bytes (`0x1000000`, 16 MiB) |
| MD5 | `48d89fe21745e62460d22354111ea6e0` |
| SHA-1 | `226a4c2bbe400d00afd2fa1d02285fbd4ea5015c` |
| SHA-256 | `6898b2b87b3a555af867f59e77820f44de21f403a5b1cd1d4c9ffcea1623e427` |

### Cart layout (three GBA headers)

A scan for the 156-byte Nintendo logo (`24 ff ae 51 …`) over the whole file
returns **exactly three hits**, each at `header+4`:

| Header | ROM base | Title (`0xA0`) | Game code (`0xAC`) | Maker (`0xB0`) | Version | Complement (`0xBD`) | Header checksum |
|---:|---|---|---|---|---:|---|---|
| `0x000000` | `0x08000000` | `SHREK SHARK` | `BS7E` | `52` | 0 | `0xC3` (recomputed `0xBF`) | `0x0000` |
| `0x080000` | `0x08080000` | `SHARK TALE` | `BSUE` | `52` | 0 | `0xFC` (recomputed `0xF8`) | `0x0000` |
| `0x890000` | `0x08890000` | `SHREK 2` | `BSEE` | `52` | 0 | `0xFC` (recomputed `0xF8`) | `0x0000` |

All three entry words are `EA00002E` (`b 0x…00C0`), i.e. the normal GBA crt0
entry for each image. The complement check is wrong on every header and the
header checksum fields are zero: the packer edited the titles without
recomputing them. This is a **three-image pack**: a tiny boot selector plus two
complete game builds.

| File range | ROM address range | Content | Evidence |
|---|---|---|---|
| `0x000000`–`0x00DEC7` | `0x08000000`–`0x0800DEC7` | Pack shell ("choose a game") | crt0 at `0x080000C0`, C runtime, Sonix banner at `0x3548`; code/data ends `0xDEC7` |
| `0x00DEC8`–`0x07FFFF` | — | zero padding | 0x00 bytes |
| `0x080000`–`0x086EB67` | `0x08080000`–`0x0886EB67` | **Shark Tale** (`BSUE`) | own header, code, text bank, GAX banner at `0x867C84` |
| `0x086EB68`–`0x087FFF7` | — | `0xFF` padding (70,800 bytes) | constant `0xFF` |
| `0x087FFF8`–`0x087FFFF` | — | ASCII `baisoku!` + NULs | build/patch signature, not game data |
| `0x0880000`–`0x088FFFF` | — | zero padding | 0x00 bytes |
| `0x890000`–`0xFD08E7` | `0x08890000`–`0x08FD08E7` | **Shrek 2** (`BSEE`) | own header, code, text bank, GAX banner at `0xFCBF9C` |
| `0xFD08E8`–`0xFFFFFF` | — | zero padding | 0x00 bytes |

The `baisoku!` marker at the end of the Shark Tale half is a modification
artifact (it is outside every pointer and every string bank). It does not affect
either game.

**Addressing inside a half.** The halves are *not* linked at `0x08000000`.
Shark Tale runs at `0x08080000` and Shrek 2 at `0x08890000`; every absolute
pointer in each half already contains that base. Example: the Shark Tale text
table pointer is `0x080BF0D8` (file `0xBF0D8`), and the Shrek 2 table pointer is
`0x088D5A24` (file `0x8D5A24`). Add the half base when converting a file offset.

---

## 2. Executive summary

**There is no in-game cheat, password, code-entry, or debug-menu system in
either GBA half.** The prior triage statement is correct for this ROM, and the
negative is now bounded by a full text search, menu enumeration, a ROM-wide
button-table scan, and 200+ emulator input tests.

What the two games *do* have:

1. **Progression unlockables only** (no codes):
   * Shrek 2: 5 books × 5 chapters, 40 gold coins per chapter; all coins unlock
     **Bonus Mode!** (the mini-game set), Movie Stills at 70 missions, Puss in
     Boots at the end of Book 2, all mini-games at 100 % (published conditions;
     the coin/bonus strings are in the ROM).
   * Shark Tale: 5 map nodes, a sub-level select (four markers per node), 25
     subway tokens per level; collecting all tokens in a chapter unlocks a
     mini-game (stated in the game's own text at `0x0C0507`).
2. **A legitimate sleep/screensaver gate**: `SELECT + L + R`. The code programs
   `KEYCNT = 0xC304` and executes `SWI 3` (Stop); the wake mask is `0x304`
   (`SELECT|L|R`) with AND logic.
3. **Unused Shin'en debug strings** — `Defeat Section`, `Defeat Section 100%`,
   `Slow Motion` (Shark Tale) and `Defeat Level`, `Defeat Level 100%`,
   `Slow Motion` (Shrek 2) — plus `Bonus Mode!`. They sit in the text banks but
   the three `Defeat…/Slow Motion` entries are referenced *only by the text
   bank's own ID table*: no menu table, code literal, or other ROM word points
   at them. No input path into a debug menu exists.

**Published codes checked.** The button codes circulating for this pack are
Xbox/GameCube/PS2 codes copied onto the GBA page: they use X/Y/R buttons the GBA
does not have, name a "Scrapbook" screen that does not exist in the GBA build
(no such string anywhere), and their sequences are absent from the ROM in every
mask/ID encoding. The one code claimed specifically for GBA ("Left, Up, A, B ×3,
Up ×5" level select) was attempted at the Shrek 2 pause menu and again at the
chapter-select screen; on GBA the A presses are consumed by the menu (Resume,
then "start Chapter 1"), so the sequence cannot be typed at either place, and no
unlock occurred. The PS2 password strings `i am the best` and `yahoo` are
absent.

**Enumeration result (§6b).** There is no code space to enumerate (no alphabet,
no length, no checksum, no lookup table). What *was* enumerated is the 10-bit
button-mask space (1,024 values), the 30³ = 27,000 initials combinations (all
accepted; the field is a save name, not a validator), and the `0x304` sleep
gate: 128 of 1,024 masks satisfy it (any superset of `SELECT+L+R`), 896 are
rejected by the AND comparison. No novel cheat code exists to mint; the
deliverable is the bounded negative, not a generated code.

---

## 3. How to reproduce

### Emulator and keys

```bash
Xvfb :112 -screen 0 1280x1024x24 &
DISPLAY=:112 openbox &
DISPLAY=:112 SDL_AUDIODRIVER=dummy mgba -3 "<rom>.gba"
```

mGBA 0.10.5 SDL defaults: **A = `x`, B = `z`, L = `a`, R = `s`,
Start = `Return`, Select = `BackSpace`, D-pad = arrows**. Hold 100–300 ms;
menus debounce. Screenshots are 720×480 at 3× scale.

Savestates used: `rom.ss1` (Shrek pause), `rom.ss2` (Shrek title), `rom.ss3`
(Shark pause), `rom.ss4` (Shark title). They are not required to reproduce the
findings; the menu paths below are.

### Pack shell

Boot → the "choose a game" screen (Shrek 2 tile left, Shark Tale tile right).
`Left`/`Right` move the highlight; **B** launches the highlighted game (A also
launched it in the first session; B was reliable in the boot tests). No button
combination held at power-on changes this screen — `L+R+Select`, `A+B+Start+Select`,
`L+R+Start`, `Up+A`, `Down+B`, `Select`, `L+R+Up+Down`, and `B` were all tried;
the only effect was launching Shrek 2 when B/Start was part of the combo.

### Shrek 2 path

```
pack shell → Shrek 2
  → legal screen → Vicarious Visions logo
  → title: Start Game / View Credits
      View Credits ................ credits roll
      Start Game → Select a Slot (3 slots, Erase, B back)
                   → New Game → Enter Initials (A-Z _ ! ? $ &, 3 chars)
                   → Choose a Book ("Far, Far Away", … 5 books)
                   → Chapter select (Chapter 1..5, 0/40 coins)
                   → level → Start
                            → pause: Resume / Quit Level / Sleep
                                      → Quit Level? Cancel / Quit
                                      → Sleep Now? Resume / Sleep,
                                        "Press SELECT + L + R to wake"
```

The GBA pause menu has **three** entries. There is no Scrapbook, Bonus, Extras,
Gallery, Options, Sound, or password entry at any point.

### Shark Tale path

```
pack shell → Shark Tale
  → DreamWorks logo → title: START GAME / VIEW CREDITS
      View Credits ................ credits roll
      START GAME → SELECT A SLOT (3 slots, ERASE, B BACK)
                  → ENTER INITIALS (same 30-symbol grid)
                  → world map ('Round da Hood, 5 nodes)
                  → level select (1-1 Neighborhood Delivery, four markers, 0/25)
                  → level → Start
                           → pause: Resume / Quit Level / Sound / Sleep
                                     → Sound: Music 100%, SFX 100%, Exit
                                     → Sleep Now? Resume / Sleep,
                                       "Press SELECT + L + R to wake"
```

Select does nothing in gameplay (it does **not** open the console versions'
"controller screen"). The only interactive "system" screens are the two sound
sliders and the sleep dialog.

### Input tests actually run

* All published/console sequences, with and without L, R, and the
  Select-first console flow, at title, pause and (Shark) gameplay:
  `B,B,A,A,B,A,B,B`; `B,B,B,B,A,B,B,B`; `A,B,A,LEFT,LEFT,B,R,DOWN,B,B`;
  `B,A,B,B,B,A,B,B`; swapped-A/B variants; `LEFT,UP,A,B` ×3; ×3 + `UP`×5;
  ×3 + `UP,RIGHT,DOWN,LEFT,UP`; ×3 + `A,B`×3; the Konami code.
* All 28 non-navigating single/pair masks (7 buttons: Select, L, R, Up, Down,
  Left, Right) at four screens (Shrek title, Shrek pause, Shark title, Shark
  pause) = **112 tests**; every result was pixel-identical to the unmodified
  screen.
* 9 power-on combos, 12 Shark gameplay sequences, 36 `SELECT`+pair wake masks.
* Published code `LEFT,UP,A,B` ×3 + `UP`×5 was attempted at the Shrek 2 pause
  menu and at the chapter-select screen. On GBA both places consume A as a menu
  action (Resume / start Chapter 1), so the code cannot be completed; the
  chapter screen still shows only Chapter 1 unlocked (0/40).

All tests are in `screenshots/` (key screens) and in the session work directory
(`/tmp/opencode/shark/shots/sw_*`, `seq_*`, `gp_*`, `boot_*`).

---

## 4. Address map

ROM addresses below are `0x08000000 + file_offset`; a half's base is already in
the address (Shark `0x08080000`, Shrek `0x08890000`).

| Address | File offset | Half | Meaning |
|---:|---:|---|---|
| `0x080003AC` | `0x03AC` | shell | `KEYINPUT` read: returns `0x3FF ^ *(u16*)0x04000130` |
| `0x080003B8` | `0x03B8` | shell | literal `0x04000130` |
| `0x08089284` | `0x089284` | Shark | `KEYINPUT` read (same helper, active-high mask) |
| `0x08089290` | `0x089290` | Shark | literal `0x04000130`; `0x3FF` at `0x08089294` |
| `0x0809C6F0` | `0x09C6F0` | Shark | sleep routine: `KEYCNT=0xC304`, `IE|=0x1000`, `SWI 3` |
| `0x0809C75C` | `0x09C75C` | Shark | literals: `0x04000132` (KEYCNT), `0xC304`, `0x04000200` (IE) |
| `0x080BF0D8` | `0x0BF0D8` | Shark | text-ID table, **202 entries** (ends `0x0BF400`) |
| `0x0889A4A0` | `0x89A4A0` | Shrek | `KEYINPUT` read |
| `0x0889A430` | `0x89A430` | Shrek | input-object update: prev `[+4]`, pressed `[+8]`, held `[+0xC]` |
| `0x088ABD64` | `0x8ABD64` | Shrek | sleep routine (same constants) |
| `0x088ABDD0` | `0x8ABDD0` | Shrek | literals: `0x04000132`, `0xC304`, `0x04000200` |
| `0x088D5A24` | `0x8D5A24` | Shrek | text-ID table, **295 entries** (ends `0x08D5EC0`) |

### Text bank record format

Both games use the same Shin'en string format. The ID table is an array of
`u32`; entry *i* points 4 bytes before string *i*. Those 4 bytes hold the
address of the previous string (a backward link), and the actual NUL-terminated
ASCII string begins at `entry + 4`:

```
table[i] -> [u32 back-link] [ASCII text] [NUL] [padding to 4]
text_addr = table[i] + 4
```

Verified on `Start Game`: Shrek entry 9 = `0x088D5F3C`, text `0x088D5F40`
(`Start Game`); Shark entry 18 = `0x080BF634`, text `0x080BF638`.

Character codes are ASCII: the text banks store the bytes directly and the
`strings`/case-folded scan reads them without a cipher. Shark Tale also
contains several 256-byte auxiliary font/glyph tables that begin with
near-identity sequences (`0x05A2C75`, `0x05A3A5D`, `0x0BD4AED`, `0x0BDB975`,
`0x0BDC75D`); they are not code alphabets (their printable region is not a
consistent char→tile map, and no code path compares input against them). Bytes
`0x80`–`0x87` are control glyphs: `0x80` = A button, `0x81` = B button,
`0x86` = L, `0x87` = R (observed on the initials and sleep screens).

### The only key-mask gate (sleep)

```
*(u16*)0x04000132 = 0xC304   ; bit15=1 (AND), bit14=1 (IRQ), mask=0x0304
*(u16*)0x04000200 |= 0x1000  ; enable keypad IRQ in IE
SWI 3                        ; Stop
```

`0x304` = `SELECT (0x004) | L (0x200) | R (0x100)`. With AND logic the keypad
IRQ fires iff `(KEYINPUT & 0x304) == 0x304`, i.e. any mask that contains all
three buttons — 128 of the 1,024 possible 10-bit masks. This exactly matches the
displayed instruction `Press SELECT + L + R to wake`. It is a sleep gate, not a
cheat, but it is the only multi-button validator in either half.

**Emulator limitation:** mGBA 0.10.5 did not return from this screen under any
input, including the exact `SELECT+L+R` held for 3 s. The screen is static and
all 36 `SELECT`+pair masks (plus singles) produced pixel-identical frames. This
is consistent with a Stop/keypad-IRQ emulation limitation; the mask model above
is therefore **Derived**, not observed end-to-end.

---

## 5. Algorithm / pseudocode

### 5.1 Button state

```c
uint16_t keys_raw = *(volatile uint16_t*)0x04000130;  // active-low, bits 0-9
uint16_t pressed  = 0x3FF ^ keys_raw;                 // active-high (A=1 … L=0x200)
```

The engine object also keeps `prev`, `pressed = now & ~prev` and a held/edge
word at `[+0xC]` (Shrek `0x0889A430`). Every menu in the ROM uses this same
object; no cheat sequence table consumes it.

### 5.2 Sleep gate

```c
*(uint16_t*)0x04000132 = 0xC304;       // KEYCNT: IRQ on, AND, mask SELECT|L|R
*(uint16_t*)0x04000200 |= 0x1000;      // IE: keypad
__asm__("swi 3");                      // Stop
// wake: all three buttons held
```

### 5.3 Text lookup

```c
const char *text(int id) { return (const char*)(text_table[id] + 4); }
```

### 5.4 What is *not* present

No `strlen`/`strcmp` password validator, no alphabet table, no checksum, no
encryption/XOR key, no per-code flag word tied to an input buffer, and no
sequence-progress counter. The only `strcmp`-like loops in the halves are the
generic text/font routines.

---

## 6. Tables

### 6.1 Debug leftovers (no direct consumer found)

| Half | ID | Text address | String |
|---|---:|---:|---|
| Shark | 15 | `0x0BF5FC` | `Defeat Section` |
| Shark | 16 | `0x0BF610` | `Defeat Section 100%` |
| Shark | 17 | `0x0BF628` | `Slow Motion` |
| Shrek | 42 | `0x08D6110` | `Defeat Level` |
| Shrek | 43 | `0x08D6124` | `Defeat Level 100%` |
| Shrek | 44 | `0x08D613C` | `Slow Motion` |
| Shrek | 50 | `0x08D61B4` | `Bonus Mode!` |

The three `Defeat…`/`Slow Motion` strings in each half have **no reference
outside their own text table**: searching every `u32` in the ROM for their
string/trailer addresses returns only the table slot itself (Shark
`0x0BF114/118/11C`; Shrek `0x08D5ACC/AD0/AD4`). No menu descriptor, no code
literal, no script pointer. `Bonus Mode!` is the all-coins reward (see §6.3),
not a cheat activation message.

### 6.2 Menus (all walked, all items listed)

| Screen | Entries | Notes |
|---|---|---|
| Pack shell | Shrek 2 tile, Shark Tale tile | no options/cheats |
| Shrek title | Start Game, View Credits | — |
| Shrek slot | 3 slots, Erase, Back | — |
| Shrek initials | `A-Z _ ! ? $ &`, OK/Back | save name, 3 chars |
| Shrek book | 5 books | only Book 1 reachable on a fresh save |
| Shrek chapter | Chapters 1–5, 0/40 | locked chapters greyed |
| Shrek pause | Resume, Quit Level, Sleep | no Sound/Scrapbook |
| Shrek confirm | Quit Level? Cancel/Quit; Sleep Now? Resume/Sleep | — |
| Shark title | START GAME, VIEW CREDITS | — |
| Shark slot | 3 slots, ERASE, BACK | — |
| Shark initials | same 30-symbol grid | save name |
| Shark map | 5 nodes | progression |
| Shark level | 1-1 … (four markers, 0/25) | progression |
| Shark pause | Resume, Quit Level, Sound, Sleep | Sound = Music/SFX/Exit |
| Shark confirm | Quit Level?, Sleep Now? | — |

### 6.3 Unlockables (no code system)

| Game | Unlockable | Condition | Evidence |
|---|---|---|---|
| Shrek 2 | Chapters 2–5 / Books 2–5 | finish prior chapter/book; 40 coins per chapter | chapter screen greyed; published guide |
| Shrek 2 | `Bonus Mode!` mini-game set | all gold coins (100 %) | string `0x08D61B4`; GameFAQs walkthrough |
| Shrek 2 | Movie Stills | complete 70 missions | GameFAQs / pack page (published) |
| Shrek 2 | Puss in Boots | finish last chapter of Book 2 | GameFAQs (published) |
| Shrek 2 | all mini-games | beat the game 100 % (25 chapters) | GameFAQs (published) |
| Shark Tale | mini-game per chapter | collect all subway tokens in a chapter | in-ROM text `0x0C0507` |
| Shark Tale | further map nodes / sub-levels | tokens + level completion | map/level screens (`0/25`) |

### 6.4 Published codes and their verification result

| Source | Claim | Buttons | Test | Result |
|---|---|---|---|---|
| GameFAQs pack page (2018 archive) | 3 unlockables only | — | ROM strings + menus | consistent; no codes |
| GameFAQs pack page (current) | 4 "hold L" Shark Tale codes | X/Y/R (Xbox/GC) | impossible on GBA; sequences searched in ROM | GBA has no X/Y; absent from ROM |
| GamesRadar "GBA" | level select `Left,Up,A,B ×3,Up ×5` | A/B/d-pad | pause + chapter select | **not enterable** (A activates menu); no unlock |
| GamesRadar "GBA" | bonus games `…A,B,X,B…` | X | contains X | not a GBA code; absent |
| PS2 Shark Tale | passwords `i am the best`, `yahoo` | text | literal search (case-folded) | **absent** from ROM |
| VGChartz (Shark Tale GBA) | "0 cheats" | — | — | consistent |
| CodeBreaker/GameShark lists | memory patches | — | out of scope | not analysed |

The pack's GBA page mixes console codes into a GBA listing; the GBA games have
no Scrapbook screen (the word `SCRAPBOOK` occurs **zero** times in the 16 MiB),
so those codes cannot be entered as written.

---

## 6b. Enumeration

### 6b.1 Code/password space

**Size: 0.** There is no code field, alphabet, length rule, checksum, or lookup
table. The only text-entry surface is the 3-character save name:

* alphabet: 30 symbols (`A-Z`, `_`, `!`, `?`, `$`, `&`);
* length: 3 (fixed; OK/Start commits, B deletes);
* space: 30³ = **27,000** names;
* validator: none — the name is stored/displayed with the save percentage
  (`AA - 0%`), never compared against a table. All 27,000 are accepted.

Therefore no novel *code* can be minted. This is the exact, bounded statement
the guide asks for in the "no system" case.

### 6b.2 Text space searched

| Half | Bytes | Printable runs (raw) | Characters | Case-folded runs | Keyword hits |
|---|---:|---:|---:|---:|---:|
| shell | 0x80000 | 876 | 4,649 | 876 | 0 |
| Shark Tale | 0x7F0000 | 102,826 | 949,111 | 102,826 | 15 |
| Shrek 2 | 0x740000 | 127,331 | 1,160,803 | 127,331 | 7 |

Keyword scan (case-folded, whole ROM): `PASSWORD`, `PASSCODE`, `CHEAT`,
`CHEATED`, `SECRET`, `UNLOCK`, `DEBUG`, `CODE`, `CODES`, `BONUS`, `GALLERY`,
`OPTION(S)`, `EXTRAS`, `CONFIG`, `MINIGAME`, `MINI GAME`, `SOUND TEST`,
`LEVEL SELECT`, `INVINCIBLE`, `SLOW MOTION`, `DEFEAT`, plus localized terms
(`MOT DE PASSE`, `PASSWORT`, `KENNWORT`, `CONTRASE*`, `CLAVE`, `CODICE`,
`WACHTWOORD`, `LÖSENORD`, `SALASANA`, `SENHA`). Hits are only: dialogue (`I
won't tell your secret`, `unlock a mini-game`), scoring labels (`Time Bonus`,
`extraPoints`), audio banners (`Shin'en Multimedia. Code: B.Wodok`), script
labels (`LEVEL_1_4_DEFEAT`), and the debug strings above. No password/cheat UI.

The text banks themselves were fully decoded: **202/202** Shark strings and
**295/295** Shrek strings (including the 0x80–0x87 control glyphs). No cheat
string hides in the non-ASCII glyph range.

### 6b.3 Button-mask space

10-bit key state → **1,024** masks; sequence space for length *L* is 1024^L.

Static scan (all 8,388,608 aligned `u16` positions per region; contiguous runs
of ≥4 values in `1..0x3FF`):

| Region | popcount ≤1 | ≤2 | ≤3 | Pointer-referenced runs (≤2) |
|---|---:|---:|---:|---:|
| shell | 1 | 1 | 6 | 0 |
| Shark | 69 | 279 | 1,080 | 2 |
| Shrek | 28 | 302 | 1,368 | 10 |

Every pointer-referenced run was inspected: they are serial/index arrays
(`1,2,3,4,5,6`) or level-header/scene numbers (Shrek `0xA9A97C…` referenced by
the level table at `0x08DC320`), not button sequences. Scanning all byte
positions for the published sequences in two button-ID encodings produced only
coincidental 8-bit data matches (e.g. `1,1,0,0,1,0,1,1` in compressed art), no
code-adjacent table.

Dynamic scan: **112** single/pair masks (28 per screen × 4 screens) — all
pixel-identical after input; plus **16** targeted sequences at each pause screen
(Shrek/Shark), **16** at each title, **12** Shark gameplay sequences, **9**
power-on combos, and **36** `SELECT`+pair wake masks. Zero activations, zero
overlays, zero unlocks.

### 6b.4 The sleep gate (the only mask validator)

* `KEYCNT = 0xC304` → AND logic, mask `0x0304` = `SELECT | L | R`.
* Satisfying masks: any 10-bit mask whose bits include `0x304` and may add any
  of the other 7 buttons → **128** of 1,024.
* Rejected by the gate: the other **896** masks (missing at least one of
  SELECT/L/R). Empirically, all 36 `SELECT`+pair combinations and several single
  buttons failed to wake (consistent with the AND requirement), but the exact
  `SELECT+L+R` also failed because mGBA does not return from the Stop state — so
  this split is **Derived** from the register write, not observed end-to-end.

### 6b.5 Bounds proven by rejection

1. Published GBA level-select code cannot be entered: at the pause menu the
   first A activates Resume, and at chapter select the first A starts Chapter 1.
   After the attempt the chapter screen is unchanged with Chapters 2–5 still
   locked (`0/40`). Screenshot `04_shrek_chapter_select.png`.
2. Console Shark Tale sequences rejected at pause and in gameplay: HUD
   (`0/25`) and character state unchanged; no "cheat enabled" text exists in
   the ROM to display.
3. The console entry point (`Select` → controller screen) does not exist on
   GBA: `Select` in Shark Tale gameplay is a no-op (screenshot series
   `gp_*`/`sel1c.png`).
4. Wrong sleep masks rejected: 36 `SELECT`+pair masks all left the screen
   unchanged.

---

## 7. Validation evidence

### Observed (emulator)

* Three headers/bases; both games boot and are playable from the pack shell.
* Every screen in §6.2 was reached and screenshotted (see `screenshots/`).
* No cheat/password/debug menu on any screen; Select is a no-op in Shark
  gameplay; Shrek pause has only Resume/Quit Level/Sleep.
* Published sequences (console translations and the GamesRadar "GBA" code)
  produce no visible change, no unlock, no audio cue (audio dummy; state
  inspected visually).
* Sleep dialog appears in both halves; all input is frozen once it is shown.
* Chapter 2 remains locked after the level-select code attempt.

### Derived (disassembly)

* Key helper returns `0x3FF ^ KEYINPUT`; mask encoding A=1 … L=0x200.
* Sleep routine writes `KEYCNT=0xC304`, sets IE bit 12, executes `SWI 3`.
* Text-table format (`table[i] + 4`) and the full string lists.
* The three `Defeat…/Slow Motion` strings have no consumer outside the table.

### Inferred

* `Bonus Mode!` is the 100 %-coin reward (string + published walkthrough, not
  played to 100 % here).
* Movie Stills / Puss in Boots / all-mini-games thresholds are from GameFAQs;
  only the chapter/coin screens were exercised.
* The `baisoku!` marker is a build/patch artifact (no pointer references it).

---

## 8. Unknowns

* The 100 %-completion states (Bonus Mode, Movie Stills, Puss in Boots, all
  mini-games) were **not** ground-truthed by playing 70 missions; their
  conditions are published and consistent with the strings, but the exact
  threshold variables were not reversed.
* Sleep wake (`SELECT+L+R`) could not be observed returning to the game under
  mGBA 0.10.5; the 128/896 mask split is derived from `KEYCNT`, not dynamic.
* A hypothetical cheat path that requires a fully completed save (e.g. a
  post-100 % menu item) cannot be ruled out by the fresh-save walks, but the
  text/table/pointer searches found no code strings or sequence tables, and the
  published GBA pages list only unlockables.

---

## 9. Tooling

* mGBA 0.10.5 SDL (`/usr/games/mgba`), Xvfb :112, openbox, xdotool, scrot,
  ImageMagick 7.
* Python 3.13: `capstone` 5.0.7, `numpy` 2.5.4.
* mGBA CLI debugger (`-d`) for the input/KEYCNT checks; mGBA GDB stub (`-g`)
  for the key-object read; `objdump`/Capstone for disassembly.
* Scripts (session work dir `/tmp/opencode/shark/`): `recon.py` (text/mask/
  literal scans), `test_seqs2.py` + JSON test lists, `sweep2.py` (112-mask
  sweep), `wakescan.py` (36 wake masks), `d.py` (Capstone disassembler).
* Savestates `rom.ss1`–`rom.ss4`; screenshots in `screenshots/`.

`roms/INDEX.md` was intentionally not edited (per task instruction).

---

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed with this
report; only hashes, addresses, short quoted UI strings, and original analysis
are included.
