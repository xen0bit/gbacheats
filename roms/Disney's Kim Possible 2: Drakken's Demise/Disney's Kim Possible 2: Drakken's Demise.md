# Disney's Kim Possible 2: Drakken's Demise (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney's Kim Possible 2: Drakken's Demise/Disney's Kim Possible 2: Drakken's Demise.gba` |
| Size | 8,388,608 bytes (0x800000, exactly 8 MiB, no appended data) |
| Header title | `KIMPOSSIBLE2` (0xA0, NUL padded) |
| Game code | `BKME` (0xAC) |
| Maker code | `4Q` (0xB0) — Buena Vista / Disney |
| Software version | 0x00 (0xBC) |
| Main unit / device | 0x00 / 0x00 |
| Entry word | `0xEA00002E` → 0x080000C0 (stock ARM branch, unmodified) |
| Complement check | 0x39 (0xBD) — **correct** for 0xA0–0xBC (recomputed 0x39) |
| Header checksum | stored `0x0000` (0xBE) — many retail GBA images leave this field zero; the complement byte above is the reliable "edited header" signal and it is valid |
| Nintendo logo | canonical, **one** hit at file 0x4 — single image, not a multi-game pack |
| Save hardware | EEPROM 512 B (`EEPROM_V124` SDK id string at file 0x1248FC, `FLASH512_V131` id also present at 0x1249AC but the game creates a 512-byte `.sav`) |
| MD5 | `5bec89f235c7a558f7f79d1760d648da` |
| SHA-1 | `d2baaec3c20b48bebe79ebe27761cd107fd067bf` |
| SHA-256 | `40c5d612a3e499b4b69e2550377ff602e99ff16175e302c5cdb2956958b4cb8c` |

**Patch/trainer check.** Entry branch is the stock `b 0x080000C0`; the complement byte
is valid; there is no cracktro string (`SUNHORS`, `MODE7`, `CRC BANDIT`, `PDX` = 0
hits), no second header, no trainer menu, no appended payload. The image is a retail
build. Engine fingerprints: `A2M1` at file 0x12D753, `Logo_A2M` asset (A2M /
Artificial Mind & Movement engine), Shin'en `GAX Sound Engine 3.05` at 0x123DE8.

## 2. Executive summary

**There is no password, no keypad, no typed cheat code and no reachable debug menu in
this retail SKU.** What the ROM does contain is (a) a save-gated unlock tree
(Global Justice Simulator level select, a 63-position card gallery, gadgets/abilities,
training tutorials) and (b) a **complete developer debug-menu directory of 43 entries
that no code in the image references** — dead data left in the retail build.

Findings in order of importance:

1. **No code-entry surface exists.** Every screen reachable from boot was walked
   (title → main → slot select → profile → training/extras/options, and in-game
   pause → extras/options/quit). None contains a text field, alphabet, keypad or
   "enter code" row. The whole message bank (1,074 decoded strings, two charsets)
   contains **0** occurrences of `PASSWORD`, `CHEAT`, `CODE` (except the credit
   line `CAIMANS VIDEO CODEC`), `DEBUG` or `SECRET` as a feature label; the only
   `UNLOCK` string is the banner `YOU HAVE UNLOCKED` used by normal progression.
2. **The only undocumented input is the SDK soft reset**: holding
   **A+B+Select+Start** fades the screen and reboots to the Disney splash. This is
   implemented at `0x0800EA48` (`held & 0x000F == 0x000F`), not by the BIOS alone.
   It is a reset, not a cheat, and is listed here because it is a hidden button
   combination in the game's own code.
3. **A full A2M developer menu directory survives in ROM** at file
   `0x12D254–0x12D707` (43 records × 28 bytes): the 16 story levels, the 5 bosses,
   the 9 training tutorials, and eight developer viewers
   (`Movie1`, `Art Viewer`, `Obj Viewer`, `Fx Player`, `Music Player`,
   `Intro Episode 1..4`, `Asset Viewer`, `Tests`, `Intros`, `Levels`), with a
   level/boss id byte per entry (0x4C–0x7E). A whole-ROM pointer scan finds **zero**
   code references to the block (only 3 internal cross-references inside it), and
   the block's pointers never appear in EWRAM/IWRAM at runtime. It is dead data;
   the retail Extras screen exposes only Global Justice Sim / Card Collection /
   Credits.
4. **The unlock system is save-gated, not code-gated.** On a save with no completed
   level, Extras → **Global Justice Sim** is drawn dimmed and the cursor **skips**
   it (observed on both frontend and pause Extras); Card Collection shows all 63
   slots face-down; the in-game Statistics screen reads `Collectibles 000/150,
   Enemies 00/25, Cards 0/5` for level 1-1. The published documentation (Nintendo
   manual, Shadio X's 3rd party cheat index FAQ) agrees: GJ Sim opens after finishing a level.
5. **Published "codes" for this SKU are out of scope memory patches only.**
   3rd party cheat indexes/CodeBreaker/Action Replay pages list only GameShark/AR writes
   (`32011442 0096`, `3201144B 0005`, master code `000067CE 000A`, …) plus a
   DS-connectivity Easter egg — no in-game password or button code. There is no
   published in-game code to verify; the negative below is bounded by the text,
   table and input space instead.

Per §0.2 this report therefore delivers the bounded negative (space definitions,
counts and rejection evidence in §6b) plus the one enumeration this ROM does offer:
the 43-entry dead debug directory and the complete menu/unlock tree.

## 3. How to reproduce

Emulator: mGBA SDL (`mgba -3`) on `Xvfb :325`, `SDL_AUDIODRIVER=dummy`, `openbox`.
Keymap used (verified against the game's key struct, §5.1): `x`=A, `z`=B, `a`=L,
`s`=R, `Return`=Start, `BackSpace`=Select, arrows=D-pad.
Hold keys 120 ms and leave ≥250 ms between presses — **this game drops short taps**
on some screens: leaving Card Collection needed a 400 ms B press, so the helper
script's `+key` form (400 ms) is used for "back". `Shift+F1..F10` saves state,
`F1..F10` loads it.

### 3.1 Screen walk (all observed on :325)

| # | Input | Screen | Items / notes |
|---:|---|---|---|
| 1 | boot | Disney Interactive logo → intro cut-scene → title `PRESS START` | 1 prompt |
| 2 | Start | Main menu | **New Game / Load Game / Options** (3) |
| 3 | A on New Game or Load Game | Slot select | 3 slots, each `Empty` on a fresh save |
| 4 | A on a slot | Profile menu | **Play / Training / Extras** (3) |
| 5 | A on Training | Training list | **Jump, Attack, Flagpole, Monkey Bars, Edge Grab, Hook, Glue Trampoline, Combo #1** (8; scrolls 4 at a time) |
| 6 | A on Extras (profile) | Extras | **Global Justice Sim** (dimmed, cursor-skipped), **Card Collection**, **Credits** (3) |
| 7 | A on Card Collection | Card Collection | 7×3 grid, **3 pages** (L/R wrap period 3 ⇒ 63 slots), all face-down |
| 8 | A on Credits | Credits roll (Disney Interactive / roles), B returns to Extras | — |
| 9 | A on Options (main) | Options | **Sound FX: ON, Music: ON, Language** (3) |
| 10 | A on Language | Language | **English / Français** (2) |
| 11 | Start in level | Pause (Kimmunicator) | **Continue / Extras / Options / Quit** (4) |
| 12 | A on Extras (pause) | Pause Extras | **Statistics / Cards** (2) |
| 13 | A on Statistics | Statistics | `Collectibles 000/150`, `Enemies 00/25`, `Cards 0/5` (level 1-1) |
| 14 | A on Options (pause) | Pause Options | **Sound FX: ON / Music: ON** (2 — no Language here) |
| 15 | Down×3, A on Quit | Confirm | `Are you sure you want to quit?` **Yes / No**; Yes → profile menu |

Menu sizes were measured by cursor clamping and by the scroll behaviour: the
Training list **scrolls** (4 rows visible, 8 items), so a 3-item list that does not
scroll cannot hide further entries. That is the argument used in §6b for the Extras
menu being complete at 3 entries.

### 3.2 Hidden input reproduced

| Test | Input | Result (observed) |
|---|---|---|
| Soft reset | A+B+Select+Start held 1 s in a level | screen fades to white, reboots to `©2004 Disney` splash |
| Title sequences | Konami (U,U,D,D,L,R,L,R,B,A), L,R,L,R,L,R, Select×3, U,D,U,D,B,A on `PRESS START` | no change; the title stays, no sound/menu/flag change (background animation only) |
| Pause/Extras | Up on Card Collection (tries to reach GJ Sim) | cursor stays on Card Collection — dimmed item is skipped |

### 3.3 Reading RAM without a debugger

mGBA `.ssN` files are PNGs with a zlib-compressed `gbAs` chunk. Extracted layout:
header/CPU 0x0, VRAM 0x1000, IWRAM 0x19000, EWRAM 0x21000 (state size 397,312 B
for this 8 MiB ROM). All RAM claims below were read this way (`/tmp/kp2/ss.py`).

## 4. Address map

`rom_address = 0x08000000 + file_offset`.

### 4.1 Input / engine

| Address | Meaning |
|---|---|
| 0x08003844 | Key-state updater: `(dst, mask)` → writes prev/held/changed/pressed/released |
| 0x08003984 | Polls `KEYINPUT`: `r0 = 0x02008850`, `r1 = 0x03FF & ~KEYINPUT`, calls 0x08003844 |
| 0x080039A0 | Literal `0x04000130` (KEYINPUT pool) |
| 0x02008850 | **Key state struct**: `+0` prev held, `+2` held, `+4` changed, `+6` pressed, `+8` released, `+10/+12` engine counters |
| 0x04000130 | KEYINPUT (active low) |
| 0x0800EA48 | **A+B+Select+Start** handler (soft reset) |
| 0x04000050/54 | BLDCNT / BLDY written by the fade-to-white |
| 0x08037FA4 | SDK soft reset: `IME(0x04000208)=0`, `SP=0x03007F00`, `SWI 1` (RegisterRamReset, r0=0xE0), `SWI 0` (SoftReset) |
| 0x02010EA4 | "buttons released once" flag used by the soft-reset handler |
| 0x0802C664 | Example level-id compare (`cmp r0,#0x54` = level 1-4) |

### 4.2 Developer menu directory (dead data)

| Address | Meaning |
|---|---|
| 0x0812D254–0x0812D707 | 43 records × 28 bytes: `{char *label; u32 link; u32 style; u8 pad, u8 id, u16 tag; u32 0; u32 0}` |
| 0x080398D4–0x08039A95 | ASCII labels for the above (`MapX`, `MapY` script variable names, then the menu strings) |
| 0x0812D714 / 0x0812D729 / 0x0812D73E | Shared style/colour blob: three 0x15-byte tables; the second is read by 0x08030CF8 for palette bytes |
| — | **0 code references** to any address in the record block (see §6b) |

### 4.3 Menus / text / save

| Address | Meaning |
|---|---|
| 0x0719D90–0x0725xxx | Message bank: variable-length records `{u32 text_offset; u16 1; u16 style; u32 0}` + text, `FF FE` terminator |
| 0x071E29C | `EXTRAS` |
| 0x071F264 | `OPTIONS` |
| 0x071E44C | `GLOBAL JUSTICE SIM` (charset 0xCF) |
| 0x071F230 | `GJ SIMULATOR` (short menu label used by the same feature) |
| 0x071E634 / 0x071F250 | `LANGUAGE` |
| 0x071F204/0x071E8B7 | `BACK` / `SELECT` (footer labels) |
| 0x071F3C8 | `YOU HAVE UNLOCKED` banner |
| 0x071F330–0x071F3A4 | unlock texts: `A NEW ANIMATION!`, `NEW ART!`, `A NEW CHALLENGE!`, `A NEW GADGET!`, `A NEW MOVE!`, `A NEW MOTIVE CLIP!`, `NEW MUSIC!` |
| 0x071F2A4 | `TOOLS` + `LEVEL PROGRAMMER` (unused string) |
| 0x071EF68 | `SECRETS` inside the alphabetical credits list (credit role, not a menu) |
| `.sav` 0x00–0x3F | Header: magic `1M2A` (= `A2M1` byte-reversed), `00 00 01 18`, then `00 00 05 09 05 08 05 07`, zeros, `FF FF` at 0x1E |
| `.sav` 0x40 / 0x88 / 0xD0 | 3 slot records, 0x48 bytes each, starting `00 <slot> 01 04 FF FF`, with the field group `05 01 01 FF` at +0x0C and `FF FF` at +0x2C; the rest 00/FF (empty) |
| 0x001248FC / 0x001249AC | SDK ids `EEPROM_V124` / `FLASH512_V131` |

## 5. Algorithm

### 5.1 Key state (reimplemented from 0x08003984 + 0x08003844)

```
held     = 0x03FF & ~KEYINPUT        # active-high 10-bit mask
prev     = key[+0]; key[+0] = key[+2]; key[+2] = held
changed  = held ^ prev            -> key[+4]
pressed  = held & changed         -> key[+6]
released = changed & ~held        -> key[+8]
```
Bit values: A=0x0001, B=0x0002, Select=0x0004, Start=0x0008, Right=0x0010,
Left=0x0020, Up=0x0040, Down=0x0080, R=0x0100, L=0x0200.

RAM check (observed): with Right+A held, `0x02008852` = `0x0011` and
`0x02008850` = `0x0011`; with nothing held both are `0x0000`. This both proves the
layout and confirms the emulator keymap (A = `x`, Right = arrow).

### 5.2 Soft reset (0x0800EA48)

```
if (held & 0x000F) == 0x000F:            # A+B+Select+Start
    if (*0x02010EA4 != 0):               # at least one frame with no button
        fade BLDY 0 -> 31 over ~30 frames (BLDCNT set first)
        BLDY = 31
        call 0x08037FA4                  # IME=0; SP=0x03007F00; SWI 1; SWI 0
else if (held & 0x000F) == 0:
    *0x02010EA4 = 1
```
The `else` branch is why the combo only fires when the previous frame had no
A/B/Select/Start held — an edge-trigger, the classic SDK soft-reset guard.

### 5.3 Message encoding (needed for the text-space search; generic to this engine)

Text is **not** plain ASCII; two charsets are used, selected per record by the
16-bit style field:

* style `0xCF` — **every** character is stored as `ASCII - 0x20`
  (`A NEW ANIMATION!` = `21 FCFF 2E 25 37 ...`).
* style `0xD1` / `0xD2` — only the **first character of each word** is stored as
  `ASCII - 0x20`; the rest is plain ASCII (`SIMULATOR` = `33 49 4D 55 ...`).

Common controls: `FF FC` = space, `FF FE` = end of message, `FF FD` = hyphen,
other `FF xx` = inline icon/glyph (button icons, `%` substitutions), `0E` = `.`,
`01` = `!`. This is why a plain `strings` run finds no UI text. The search in §6b
was run in **both** encodings, so it does not depend on getting the style right.

## 6. Tables

### 6.1 Key mask constants (from §5.1)

| Bit | Key | Bit | Key |
|---:|---|---:|---|
| 0x0001 | A | 0x0020 | Left |
| 0x0002 | B | 0x0040 | Up |
| 0x0004 | Select | 0x0080 | Down |
| 0x0008 | Start | 0x0100 | R |
| 0x0010 | Right | 0x0200 | L |

### 6.2 Developer menu directory, 0x0812D254 (43 records, 0x1C stride)

| Address | Label | id | tag | group |
|---|---|---:|---:|---|
| 0x0812D254 | 1-4 Rufus | 0x54 | 0x1B | level |
| 0x0812D270 | 2-4 Air Combat | 0x59 | 0x1B | level |
| 0x0812D28C | 3-4 Deep Sea | 0x5D | 0x1B | level |
| 0x0812D2A8 | 4-3 Rocket Blades | 0x4C | 0x1B | level |
| 0x0812D2C4 | 1-1 | 0x4D | 0x1B | level |
| 0x0812D2E0 | 1-2 | 0x4E | 0x1B | level |
| 0x0812D2FC | 1-3 | 0x51 | 0x1B | level |
| 0x0812D318 | 2-1 | 0x52 | 0x1B | level |
| 0x0812D334 | 2-2 | 0x53 | 0x1B | level |
| 0x0812D350 | 2-3 | 0x56 | 0x1B | level |
| 0x0812D36C | 3-1 | 0x57 | 0x1B | level |
| 0x0812D388 | 3-2 | 0x58 | 0x1B | level |
| 0x0812D3A4 | 3-3 | 0x5B | 0x1B | level |
| 0x0812D3C0 | 4-1 | 0x5C | 0x1B | level |
| 0x0812D3DC | 4-2 | 0x5E | 0x1B | level |
| 0x0812D3F8 | 4-4 | 0x50 | 0x1B | level |
| 0x0812D414 | Falsetto | 0x55 | 0x1B | boss |
| 0x0812D430 | Duff | 0x5A | 0x1B | boss |
| 0x0812D44C | Gemini | 0x5F | 0x1B | boss |
| 0x0812D468 | Shego | 0x60 | 0x1B | boss |
| 0x0812D484 | Drakken | 0x76 | 0x1B | boss |
| 0x0812D4A0 | Jump | 0x6A | 0x1B | tutorial |
| 0x0812D4BC | Attack | 0x77 | 0x1B | tutorial |
| 0x0812D4D8 | Long Jump | 0x7E | 0x1B | tutorial |
| 0x0812D4F4 | Wall Bounce | 0x6C | 0x1B | tutorial |
| 0x0812D510 | Flagpole | 0x79 | 0x1B | tutorial |
| 0x0812D52C | Monkey Bars | 0x6B | 0x1B | tutorial |
| 0x0812D548 | Edge Grab | 0x73 | 0x1B | tutorial |
| 0x0812D564 | Hook | 0x70 | 0x1B | tutorial |
| 0x0812D580 | Glue Trampoline | — | 0xFFFF | tutorial |
| 0x0812D59C | Movie1 | — | 0x1B | viewer |
| 0x0812D5B8 | Obj Viewer | — | 0x1C | viewer |
| 0x0812D5D4 | Music Player | — | 0x1D | viewer |
| 0x0812D5F0 | Fx Player | 0x01 | 0xFFFF | viewer |
| 0x0812D60C | Art Viewer | 0x46 | 0x0000 | viewer |
| 0x0812D628 | Intro Episode 1 | 0x47 | 0x0000 | intro |
| 0x0812D644 | Intro Episode 2 | 0x48 | 0x0000 | intro |
| 0x0812D660 | Intro Episode 3 | 0x49 | 0x0000 | intro |
| 0x0812D67C | Intro Episode 4 | — | — | intro |
| 0x0812D698 | Levels | — | — | root menu |
| 0x0812D6B4 | Intros | — | — | root menu |
| 0x0812D6D0 | Tests | — | — | root menu |
| 0x0812D6EC | Asset Viewer | 0x2D | — | root menu |

The `id` byte is a real engine id: gameplay code compares against it
(`0x0802C664: cmp r0,#0x54` = level 1-4), and ids 0x4C–0x60 are the room/level
numbers used by the level loader. The four "root menu" rows carry no id; their
second word points at another record inside the block (Levels→0x0812D610,
Intros→0x0812D584, Tests→0x0812D5A0), i.e. they are submenu links.

### 6.3 Menus and item counts (observed)

| Screen | Items |
|---|---|
| Title | 1 prompt (`PRESS START`) |
| Main | 3 |
| Slot select | 3 (slots) |
| Profile | 3 |
| Training | 8 (scrolls) |
| Extras (profile) | 3 |
| Card Collection | 63 slots (3 pages × 21) |
| Options (profile) | 3 |
| Language | 2 |
| Pause | 4 |
| Pause Extras | 2 |
| Statistics | 3 counters |
| Pause Options | 2 |
| Quit confirm | 2 |

## 6b. Enumeration

**Space definitions.**

* *Typed-code space:* **none — 0 representable accepted codes.** There is no input
  field, no alphabet constant, no length rule and no validator. The searched space
  is the complete message bank plus every 4–24-character alphanumeric run in the
  image (see the counts below). A password screen would require (a) an editable
  text buffer and (b) a comparison against user text; the game has neither — no
  screen in §3.1 offers text entry, and the message bank contains no
  `ENTER`/`CODE`/`PASSWORD` label.
* *Button-code space:* **none — 0 documented codes, and no sequence matcher.**
  The entire key surface is the struct in §4.1: 58 code sites reference its base
  address, and their surrounding code was disassembled. Only one performs a
  multi-key combination test — `held & 0x0F == 0x0F` at 0x0800EA48
  (A+B+Select+Start soft reset, §5.2). The `0x30`/`0xC0` compares at
  0x0800395C/0x08003970 are the left/right and up/down cursor-repeat pair masks
  inside the key updater itself. No site retains a press history, compares an
  ordered sequence, or dispatches on a prefix.
* *Save/unlock space (the system that does exist):* 512-byte EEPROM, magic `1M2A`,
  3 slot records of 0x48 bytes at 0x40/0x88/0xD0. The save gates the Extras items
  (observed: the GJ Sim entry is disabled on an empty save) and carries the card /
  gadget / tutorial set. The exact bit assignment was **not** needed for a code
  claim (there is no code) and is listed under Unknowns.

**Novel values found (not in any published list).**

There is no code to mint, so the deliverable is the two pieces of unpublished
content this ROM actually contains, both verified here:

1. **The 43-entry developer menu directory** (§6.2) — no FAQ, 3rd party cheat index page or wiki
   mentions a debug menu for this SKU, and none lists the level/boss id bytes.
   Verified status: present in ROM, **0 code references**, not present in RAM at
   runtime ⇒ not reachable; reported as dead data rather than as a cheat.
2. **The built-in soft reset** — `A+B+Select+Start` in gameplay, implemented in the
   game's own code (0x0800EA48) rather than only by the BIOS, reproduced on :325
   (fade → `©2004 Disney` splash). Not in any published cheat list for this title.

**Bounds proven by rejection / by exhaustive search.**

| Space searched | Method | Result |
|---|---|---|
| Message bank | 1,074 `FF FE`-terminated strings decoded across the image (1,043 in the 0x0719D90–0x0725xxx bank), both charsets | `PASSWORD` 0, `CHEAT` 0, `CODE` 0 (only `CAIMANS VIDEO CODEC` in credits), `DEBUG` 0, `SECRET` 2 (`Secrets`, a credit role, EN+FR), `UNLOCK` 1 (`YOU HAVE UNLOCKED` progression banner), `BONUS` 2 (French credit role) |
| Whole image, all three encodings | plain ASCII, first-char-masked and fully `ASCII-0x20` variants of each keyword (covers both charsets plus mid-word hits) | same result: no `PASSWORD`, `CHEAT`, `CODE ENTRY`, `ENTER CODE`, `DEBUG`, `HIDDEN` or `LEVEL SELECT` anywhere in the image |
| Code alphabet | 8–24 char `[A-Z0-9]` runs with ≥2 digits and ≥4 letters | 1,990 runs; sampled runs are SDK flash part numbers (`MN63F805MNP`, `AT29LV512`, `LE39FW512`), tile data and level/collision bytes; no `ABC…`/`012…` password charset exists (the only literal `ABCDEFGH` runs sit inside the font's ASCII→glyph table at 0x6337FF+) |
| Button-mask tables | whole-image scan for ≥4 consecutive u16 single-bit masks from `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}` | 3,178 runs; the only ten-entry mask list is at 0x08129226 (data, no code xref); the rest are tutorial button-prompt graphics (0x08198DB4+) and level/collision bytes — none is referenced by a comparison chain |
| Debug directory | all 4-byte-aligned addresses 0x0812D254–0x0812D707 searched as u32 across the image | 0 references from code or data outside the block; 3 internal (submenu links); 0 copies of the block or its label pointers in EWRAM/IWRAM in three savestates (Options screen, gameplay idle, gameplay with Right+A held) |
| Title-input space | 4 classical sequences + 3 single-key repeats typed on `PRESS START` | no state change; only Start's normal advance works |
| Published codes | 3rd party cheat indexes, CodeBreaker/AR lists | only host-side memory patches + the level-select unlock; no in-game code exists. The published AR/GS hex strings `32011442`, `82011410`, `03E7`, `3201144B`, `000067CE`, `000A` have 0 occurrences in the image, as expected for host-side patches |

**Reachable-screen enumeration** (all 15 rows of §3.1 observed): title, main,
slot-select, profile, training, extras, card collection, credits, options,
language, pause, pause-extras, statistics, pause-options, quit-confirm. No 16th
screen could be produced by input; the dimmed GJ Sim entry is skipped by the
cursor, and the 3-item Extras does not scroll while the 8-item Training list does.

## 7. Validation evidence

### Observed (emulator screenshots, RAM reads)

* Full screen walk per §3.1, on `:325`; every transition captured.
* Extras → Global Justice Sim is rendered dim while Card Collection/Credits are
  bright; Up from Card Collection does not move the cursor to it.
* Card Collection L/R pagination: the R-icon enabled/dim pattern repeats with
  period 3 presses, i.e. 3 pages of 21 = 63 positions; all cards face-down on a
  fresh save.
* Statistics for level 1-1: `000/150`, `00/25`, `0/5` (matches the published
  per-level card count of 5).
* Soft reset: A+B+Select+Start in a level → fade → `©2004 Disney` splash.
* Key struct read from a savestate: idle `0x02008850/52 = 0x0000/0x0000`;
  Right+A `0x0011/0x0011`.
* Quit → Yes returns to the profile menu; Credits → B returns to Extras.

### Derived (instruction sequence)

* Key-state derivation and the `0x03FF & ~KEYINPUT` poll (0x08003984/0x08003844).
* Soft-reset gate `held & 0x0F == 0x0F` plus edge flag at 0x02010EA4 (0x0800EA48).
* Debug directory record format (0x1C stride, label/link/style/id/tag) and the
  absence of any reference to it (pointer scan).
* Message-bank record format and the two charsets (§5.3).
* Save layout: 512 B, magic `1M2A`, 3 × 0x48-byte slots (from the `.sav` the game
  created and the EEPROM SDK ids).

### Inferred

* The debug directory is a left-over from the development build's level-warp /
  asset-viewer menu; the four "root menu" rows (Levels/Intros/Tests/Asset Viewer)
  suggest a two-level menu, but no renderer survives in this build (0 xrefs).
* The `TOOLS`/`LEVEL PROGRAMMER` message pair (0x071F2A4) belongs to the same
  removed developer UI; it has no screen.
* GJ Sim is enabled by "one level completed" (published manual + FAQ) and the
  disabled entry is save-driven; the exact bit was not isolated (Unknowns).

### Negative evidence with counts

* `strings -t x -n 4` → 123,797 lines; case-insensitive `password|cheat|debug|
  secret|unlock|level select|code` → **1** hit, the Shin'en banner
  `Shin'en Multimedia. Code: B.Wodok` (an audio-engine credit, §16 false positive).
* Whole image: `PASSWORD`, `CHEAT`, `DEBUG`, `HIDDEN`, `CODE ENTRY`, `ENTER CODE`,
  `LEVEL SELECT`: **0 hits each** in plain ASCII, first-char-masked and fully
  `ASCII-0x20` encodings. The only near-hits are `CAIMANS VIDEO CODEC` (credit
  line), `Secrets`/`BONUS` (credit roles, EN+FR) and `YOU HAVE UNLOCKED`
  (progression banner).
* Message bank: 1,074 strings, 2 charsets, 0 code/password/cheat entries.
* Key-mask scan: 3,178 candidate runs, all classified as prompt graphics or data.
* Debug directory: 0 xrefs (43 records, 0 code pointers).

## 8. Unknowns

* The save bit that enables **Global Justice Sim** was not isolated: unlocking it
  requires completing a level, and the 0x48-byte slot record layout (progress
  counters + checksum, if any) was not reversed. The gate itself is observed
  (dimmed + cursor-skipped on an empty save) and documented by the manual.
* The content behind the GJ Sim (per-level emblem screen, whether boss rooms are
  listed) could not be observed for the same reason; §6.2 shows which ids a
  developer build would have offered, but the retail list is unverified.
* Whether the 3-page card gallery holds 63 real cards or 63 slots with some unused
  was not proven; the page count (3) and the level-1-1 count (5) are observed, and
  the published per-level card counts sum to ≈42 across 13 levels, which suggests
  unused positions.
* The record at 0x0812D67C ("Intro Episode 4") ends with a 2-word tail at
  0x0812D23C that does not fit the 0x1C record shape; its meaning is unresolved.

## 9. Tooling

* `mgba -3` + `Xvfb :325` + `openbox`; `xdotool` (XTEST to the focused window),
  `import -window root` for screenshots, `convert` for crops.
* mGBA savestates parsed in Python (PNG `gbAs` chunk → zlib → 397,312-byte state;
  EWRAM at 0x21000) — `ss.py`.
* Python 3 + `capstone` for Thumb scans (literal pools, `CMP #imm`, key-mask
  runs); `arm-none-eabi-objdump -M force-thumb` for range disassembly.
* `textdump.py` / `text3.py` — message-bank extractor and two-charset decoder.
* `key.py` — input helper (120 ms taps, 400 ms "back" holds) and `pagecheck.py`
  for the pagination check. Work directory `/tmp/kp2` (transient).

## 10. Legal note

No ROM, graphics, audio or extracted game text is redistributed here. Only hashes,
addresses, record formats and reimplemented algorithms are published.
