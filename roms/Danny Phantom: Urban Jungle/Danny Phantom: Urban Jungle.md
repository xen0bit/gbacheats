# Danny Phantom: Urban Jungle (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Danny Phantom: Urban Jungle/Danny Phantom: Urban Jungle.gba` |
| Size | 4,194,304 bytes (4 MiB, 0x400000) |
| Header title | `DANNYPHANTOM` (0xA0–0xAB) |
| Game code | `BQYE` (0xAC–0xAF) |
| Maker | `78` (0xB0–0xB1) |
| Version | 0x00 (0xBC) |
| Fixed byte 0xB2 | 0x96 |
| Entry word | `0xEA00002E` (stock ARM branch to 0x080000C0) |
| Complement byte | stored 0x20, computed 0x1C — mismatch (rebuilt-header artifact) |
| Header checksum | stored 0x0000, computed 0x0020 — not initialised |
| MD5 | `022cc7ccc60272a2b773071ad448bba9` |
| SHA-1 | `befaa0cd61653791beb9e2d6159aa2a8b0369d60` |
| SHA-256 | `57c00a4bd438781406c8a70e4fa0d340e53e9cd031b06cc76f9ea0df7bd7750a` |

Notes (Phase 0):

* A Nintendo-logo scan of the whole 4 MiB returns exactly **one** header (logo at
  file offset 0x4). Single-image cartridge, not a multi-game pack.
* No trainer/cracktro strings anywhere (`CRC BANDIT`, `SUNHORS`, `Mode7`, `CRACK`,
  `TRAINER` = 0 hits); entry word is stock. The complement/checksum state matches
  every other ROM in this collection (e.g. `007: Nightfire` shows the same +4
  complement delta and a zeroed header checksum), i.e. a regenerated 0x00–0xFF
  header block, not a gameplay patch. All analysis below used the image unchanged.
* This is **not** the SKU that owns the published four-letter Danny Phantom codes.
  Those are documented for *The Ultimate Enemy* (AGB-BUEE); this image is *Urban
  Jungle* (AGB-BQYE, 2006, Altron/THQ). See §6 and §6b.

## 2. Executive summary

`Danny Phantom: Urban Jungle` (GBA) contains **no password, cheat-code, debug-menu
or button-code system**. There is no entry screen, no alphabet, no code table and no
validator to reverse. The published four-letter set (`RUSH`, `VLAD`, `JAZZ`, `DASH`,
`ECTO`, `SEEK`) belongs to the other Danny Phantom GBA title, *The Ultimate Enemy*
(AGB-BUEE), whose own report documents a Passwords menu; none of those literals
exists in this image under any encoding tested, and this image's start menu has no
password item.

What the ROM does contain, and what was verified:

* A single front-end menu with **exactly three items**, matching the retail manual:
  NEW GAME, GAME DIFFICULTY, GHOST GALLERY (`NEW GAME - Begin a game…`,
  `GAME DIFFICULTY - Select a difficulty level of EASY, NORMAL, or HARD`,
  `GHOST GALLERY - View all…`). The count is proven at runtime: a 3-state selection
  ring in OAM (Down goes 0→1→2→0, Up goes 0→2→1).
* Item 0 starts a live game scene (D-pad moves state, A spawns effects). Items 1
  and 2 open two distinct front-end sub-screens (a 4×3/12-slot grid with a page
  counter, and a 3×3 icon panel).
* The only exact button combination in the whole image is `A+B+Select+Start`,
  which performs a **soft reset** (`SWI 0x01` RegisterRamReset + `SWI 0x00`), not a
  cheat. It is gated on `0x03001C52 != 0`.
* Unlockables (Ghost Gallery, Boss Battle, event scenes/endings, difficulty) are
  save-state driven, not code driven; no code can reach them.

The §0.2 deliverable (a generated code accepted in-game) is **not applicable**: the
representable code space is empty. The negative is bounded in §6b by the exact
searches (literal encodings, table shapes, keyword strings, compressed blocks,
button-mask gates) and by the enumerated UI states.

## 3. How to reproduce

Environment: mGBA 0.10.5 (SDL frontend), `Xvfb :283 -screen 0 1024x768x24`,
`openbox`, `SDL_AUDIODRIVER=dummy`, `mgba -3`. Only this display and this emulator
instance were used.

Default SDL keymap, verified against the game's own input globals
(`0x03001D50`, active-high; nothing pressed = `0xFC00`):

| GBA | Key | Held value observed |
|---|---|---|
| A | `x` | 0xFC01 |
| B | `z` | 0xFC02 |
| Start | `Return` | 0xFC08 |
| Select | `BackSpace` | 0xFC04 |
| L | `a` | 0xFE00 |
| R | `s` | 0xFD00 |
| D-pad | arrows | 0xFC10/20/40/80 |

All key presses were held 0.15–0.5 s; input was confirmed by reading
`KEYINPUT`/`0x03001D50` from a savestate taken while the key was down.

Screen walk (each step verified by a savestate, not by eye):

1. Boot; wait for the title screen (DISPCNT 0x1840, BG3 only).
2. Press **Start** → start screen. The 3-item ring is at OAM sprites 2/3.
3. **Down** ×1/2/3 (or **Up** ×1/2) moves the selection through
   item 0 → item 1 → item 2 → item 0.
4. **A** on item 0 → live game scene (tutorial/stage). `A` spawns effects,
   D-pad changes game state, Start only advances/skips tutorial text.
5. Reload the start screen, **Down** ×1, **A** → sub-screen 1.
6. Reload, **Down** ×2, **A** → sub-screen 2.
7. Reload, **Down** ×3, **A** → item 0 again (wraps).

Savestates: mGBA `.ss1` PNG with a zlib-compressed `gbAs` chunk; 397,312 bytes
(0x61000) for this 4 MiB ROM. Layout used (see §4):

```
0x00000 header/CPU/audio/video/save state
0x00400 I/O registers   (DISPCNT +0, BGxCNT +8..+E, KEYINPUT +0x130)
0x00800 palette RAM (1 KiB)
0x00C00 OAM (1 KiB)
0x01000 VRAM (0x18000)
0x19000 IWRAM (0x8000)  -> 0x03000000
0x21000 EWRAM (0x40000) -> 0x02000000
```

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x080000C0` | stock ARM crt0 | Observed (entry word `EA00002E`) |
| `0x080008B8` | **joypad reader**; only `0x04000130` literal in the image (file 0x8EC) | Derived |
| `0x03001D50` | key state: `pressed` +0, `held` +2, `released` +4, `previous raw` +6 | Derived |
| `0x03000C04` | last raw `KEYINPUT` (literal at file 0x8F4) | Derived |
| `0x08000520`–`0x08000548` | **soft-reset gate** (copies at `0x080005E4`, `0x08000692`): `held == 0xFC0F`, `prev & 0x3F0 == 0`, `[0x03001C52] != 0` → set `[0x03001C51]=1`, call `0x08085F20` with r0=0xFC | Derived |
| `0x08085F20` | soft-reset thunk: `IME=0` (0x04000208), `SP=0x03007F00`, `SWI 0x01` (RegisterRamReset, r0=0xFC), `SWI 0x00` (SoftReset) | Derived |
| `0x08005D5C` | dialogue/text-box scroll reader (Up/Down masks `0x00400040`/`0x00800080`) | Derived |
| `0x08009C50`–`0x08009D14` | menu navigation: converts Up/Down/Right/Left into direction codes 1/3/2/4 at `[menu+0x464]` | Derived |
| `0x0800A876`–`0x0800A89E` | lays out a **4 columns × 3 rows (12-slot)** item grid at x=0x50/0x70/0x90/0xB0, y=0x20/0x31/0x42 | Derived |
| `0x0800A8C8`–`0x0800A8D2` | draws the 12-slot list (`bl 0x08009D2C`) and the selected-slot detail (`bl 0x08009FCC`) | Derived |
| `0x088FBC` | 72-byte glyph-order table (index→ASCII) | Observed (bytes) |
| `0x08907C` | 72-byte inverse table (ASCII→glyph index) | Observed |
| `0x089118` | 24-byte secondary glyph-order table (`wvutgfed…`) | Observed |
| `0x088C84` / `0x088CEC` | plaintext message bank (uses `#` newline, `^` colour, `$` terminator) | Observed |
| `0x176010`–`0x1772xx` | tutorial message bank (same markup) | Observed |
| `0x16AD40` | repeated build leftover `sound/sNaga_Stage1.nbsa` | Observed |

RAM values used as runtime proof:

| Address | Meaning | Values |
|---|---|---|
| `0x03003744` | sub-screen 1 page/scroll counter | 0,1,2,3,4 on successive Right presses |
| `0x03003746`, `0x03004340` | companion counters (same increments) | — |
| OAM sprite 2/3 attr2 | start-menu selection graphics | 0x041/0x021, 0x141/0x121, 0x181/0x161 |

## 5. Algorithm

### 5.1 Input path (shared engine routine at 0x080008B8)

```
raw      = ~*(u16*)0x04000130 & 0xFFFF      ; upper bits read as 0xFC00
prev_raw = *(u16*)0x03000C06                ; save/restore around update
*(u16*)0x03001D56 = *(u16*)0x03001D52       ; previous held
*(u16*)0x03001D50 = (raw ^ prev) & raw      ; pressed
*(u16*)0x03001D52 = raw & prev              ; held  (0xFC00 | keys)
*(u16*)0x03001D54 = (raw ^ prev) & prev     ; released
*(u16*)0x03000C04 = raw
```

Because the reader complements the active-low register without masking the upper
six bits, every "held" value carries a constant `0xFC00`. Exact-combination gates
therefore compare against `0xFC00 | mask` (the soft reset uses `0xFC0F`).

### 5.2 Soft-reset gate (0x08000520)

```
if (held == 0xFC0F)                       // A+B+Select+Start
 && (prev & 0x3F0) == 0                   // no D-pad/L/R in the previous frame
 && *(u8*)0x03001C52 != 0                  // reset allowed
 && held != prev:
        *(u8*)0x03001C51 = 1
        SoftResetThunk(0xFC)               // IME=0; SP=0x03007F00; SWI 01; SWI 00
```

This is the developer's soft reset, not a cheat. It is the **only** exact held-mask
gate in the image: enumerating all 110 literal references to `0x03001D50` and every
`cmp` against a loaded constant yields only `0xFC0F` (three copies of this gate) and
`0xFFFF00` (four sites inside text handling).

### 5.3 Code validator

None. No routine reads a character buffer, no table of codes exists, and no
comparison against four-letter constants exists (see §6b).

## 6. Tables

### 6.1 Published four-letter codes versus this ROM

| Code | ASCII | lower | +0x20 | UTF-16LE/BE | UTF-32LE/BE | reversed | base-26 / 5-bit / packed | present? |
|---|---|---|---|---|---|---|---|---|
| RUSH | 0 | 0 | 0 | 0 | 0 | 0 | incidental only | **no** |
| VLAD | 0 | 0 | 0 | 0 | 0 | 0 | 1 byte-coincidence | **no** |
| JAZZ | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **no** |
| DASH | 0 | 0 | 0 | 0 | 0 | 0 | 1 byte-coincidence | **no** |
| ECTO | 8 | 0 | 0 | 0 | 0 | 0 | 0 | **no** (see below) |
| SEEK | 0 | 0 | 0 | 0 | 0 | 0 | 0 | **no** |

All eight `ECTO` hits are inside the credits word `DIRECTOR,` / `DIRECTORS`:
file offsets 0x87454, 0x874B1, 0x8759B, 0x8761A and neighbours — text such as
`^DIRECTOR,$`, `SR.DIRECTOR,^DIGITAL GAMES$`. They are substrings, not codes.
Single-byte XOR/add/sub transforms and base-26/5-bit packings were swept for all
256 masks and every letter orientation; each produced at most isolated hits inside
graphics/audio data (e.g. VLAD index bytes at 0xCDAC6 sit in a signed-byte data
block; DASH 5-bit at 0x279329 sits in a u16 table), never a six-code set.

### 6.2 Keyword strings (whole image, case-sensitive and case-insensitive)

| Keyword | ASCII hits | Classification |
|---|---|---|
| PASSWORD / password | 0 | — |
| CHEAT / cheat | 0 | — |
| SECRET / secret | 0 | — |
| DEBUG / debug | 0 | — |
| CODE / code | 0 | — |
| INVALID | 0 | — |
| WRONG / ERROR / TRY AGAIN / ACCEPT / CONFIRM / INPUT / OPTION | 0 | — |
| ENTER | 1 | inside credits `ENTERTAINMENT PRODUCTS$` (0x87627) |
| GALLERY | 2 | tutorial messages 0x88CEC/0x88D6C and 0x1764F6 |
| SOUND | 1 | credits `SOUND ARTIST$` (0x88124) |
| TUTORIAL | 0 | (tutorial text spells it in lower case inside messages) |

LZ77 sweep: 22 valid GBA-LZ77 blocks decompressed; none contains any of the above
keywords. No Huffman/RLE text bank was found; the two plaintext message banks above
account for all dialogue.

### 6.3 Glyph tables

`0x088FBC` and `0x08907C` are a 72-entry permutation pair over the printable set
`space !"#$%&'()*+ 0-9 :; @ A-Z [ ` a-z {` (glyph index ↔ ASCII). `0x089118` is a
24-entry variant. These are font-order tables used by the message renderer; they are
present in every Altron GBA title and are not a cipher or password alphabet.

## 6b. Enumeration

**Space definition.** None. There is no alphabet, length, checksum, reserved bit or
lookup table for a code in this image:

* 0 occurrences of `PASSWORD`/`CHEAT`/`SECRET`/`DEBUG`/`CODE` in either case.
* 0 tables matching “three or more 4-uppercase-letter NUL-padded records”
  (regex `(?:[A-Z]{4}\x00){3,}`) anywhere in 4 MiB.
* 0 published literals present under ASCII, lowercase, `+0x20`, UTF-16LE/BE,
  UTF-32LE/BE, byte-reversed, all 255 single-byte XOR/add/sub transforms, base-26
  (both letter bases, both orders) or 5-bit packing.
* 0 code validators: the joypad-reference set (110 literal loads of `0x03001D50`)
  contains exactly one exact-combination gate, the soft reset `A+B+Select+Start`.
* No character-input consumer was found: the input handlers identified are menu
  navigation (0x08009C50), dialogue scroll (0x08005D5C) and the soft-reset gate;
  none of them writes a text buffer or compares one against stored strings.

**UI enumeration (all reachable states, RAM-verified).**

| # | State | DISPCNT | BG0/BG1/BG2/BG3 CNT | VRAM SHA-256 prefix | Notes |
|---|---|---|---|---|---|
| 1 | Title | 0x1840 | 1F41 1E46 3D4B 3DC7 | 2389B13F0F | BG3 + OBJ only; waits for Start |
| 2 | Start menu (3 items) | 0x1840 | 1F41 1E46 3D4B 3DC7 | 709E4E7B07 | OAM sprites 2/3 = selection |
| 3 | Item 0 → live stage | 0x1840 | 1F41 1E46 3D4B 3BC3 | A5478297CA | D-pad changes EWRAM; A changes sprite count 33→35→35→31 |
| 4 | Item 1 → 12-slot grid | 0x1740 | 1F40 0F47 4649 524E | 45E84562C9 | Right increments page counter 0x03003744 (0→1→2→3→4) |
| 5 | Item 2 → 3×3 panel | 0x1C40 | 1F41 1E46 3E46 3F43 | 3496EB9713 | Up/Down scrolls sprite strips |

Start-menu ring proof (OAM sprite 2/3 `attr2 & 0x3FF`):

```
item 0 : 0x041 / 0x021
item 1 : 0x141 / 0x121      Down: 0 -> 1 -> 2 -> 0
item 2 : 0x181 / 0x161      Up  : 0 -> 2 -> 1
```

**Pause probe.** In state 3, `Start`, `Select`, `A` and `B` were each held 0.25–0.5 s:
DISPCNT, BGxCNT, VRAM and the visible-sprite list did not change, while the frame
counter advanced (202 frames in 3 s), i.e. the scene stayed live and no menu layer
appeared. Start only advances/skips tutorial text; no pause menu state was reached.

**Novel codes.** Not applicable: with no alphabet, length or validator there is no
unpublished code to mint. The “prove the negative by rejection” requirement is met
instead by (a) the exhaustive literal/table/keyword scans above and (b) the fact
that the start menu has exactly three items and none of them is an entry field.

**SKU ownership of the published set.** The four-letter codes are published for
*Danny Phantom: The Ultimate Enemy* (GBA, AGB-BUEE), whose in-game Options menu
contains a Passwords item; that title's companion report independently documents a
letter-entry handler in its front-end code. *Urban Jungle* (this image, AGB-BQYE)
has a different engine build (joypad globals at 0x03001D50 instead of BUEE's
0x03001F60), a three-item start menu with no password item, and no code surface at
all. The published list therefore belongs to BUEE, not BQYE; a literal search of
BUEE also fails on plaintext (its storage format remains that report's open item).

## 7. Validation evidence

**Observed**

* Title → start screen on Start; three selection states, ring period 3 on both
  Down and Up, read from OAM while the menu was open.
* Item 0 → live scene: D-pad input changes EWRAM (`4B387AA410` → `60B2F266`),
  A presses change the visible sprite count 33/35/31 while VRAM/DISPCNT stay fixed.
* Items 1 and 2 → two distinct DISPCNT/BG configurations and VRAM images (table
  above); Right on item 1 increments RAM counters at 0x03003744/46/e0.
* Start/Select/A/B in the live scene produce no menu layer (DISPCNT, BGxCNT, VRAM
  constant; frame counter advancing).
* Save file created by mGBA is 512 bytes and entirely 0xFF (EEPROM-class image, no
  save data yet), consistent with save-based rather than password-based progress.

**Derived**

* Input path at 0x080008B8 and the `0xFC00`-biased held values (verified by reading
  0x03001D50 while each key was held).
* Soft-reset gate at 0x08000520 and the reset thunk at 0x08085F20: `0xFC0F`
  comparison, D-pad guard, `SWI 01`+`SWI 00`. Not executed (it would clear state);
  the code is unambiguous.
* Absence of any other exact held-mask gate (all 110 joypad literal sites scanned).
* 12-slot grid layout at 0x0800A876 (4 columns × 3 rows).

**Inferred**

* Item 0/1/2 names NEW GAME / GAME DIFFICULTY / GHOST GALLERY follow the retail
  manual's own list; the on-screen labels are pre-rendered tile art, so the mapping
  of item 1 vs item 2 to “GAME DIFFICULTY” vs “GHOST GALLERY” is inferred from
  behaviour (a paged 12-slot grid is the gallery-like screen; the 3×3 icon panel is
  the other function), not read from text.
* The 12-slot grid is the Ghost Gallery because the game's gallery has 18 ghosts
  (published list) and a 12-per-page layout gives two pages; medium confidence.

## 8. Unknowns

* The start menu, HUD and all menu labels are baked into pre-rendered 4bpp/8bpp
  tile art; no ASCII label bank exists, so labels could not be read from the ROM or
  from screen text. Item names rest on the retail manual plus the observed
  destinations (marked Inferred above).
* The in-game pause menu was not reached. In the only live scene reached, Start,
  Select, A and B produced no menu layer; whether a pause menu exists later in the
  game (after the tutorial) is unresolved here. This does not affect the code
  question: no pause menu can contain a validator that does not exist in the image.
* The save layout (gallery bits, difficulty byte) was not decoded because the
  generated save stayed empty (0xFF); the game does not write one just by entering
  the first stage.
* The exact encoding of BUEE's password table is that SKU's open item, not this
  one; its own report records the same literal-search negative.

## 9. Tooling

* `mgba` 0.10.5 (SDL), `Xvfb`/`openbox`/`xdotool`, `SDL_AUDIODRIVER=dummy`.
* Python 3 + `capstone` 5.0.7 for Thumb disassembly and scans; `objdump`
  (`arm-none-eabi`) for spot checks.
* `state.py` (mGBA `.ss1` PNG `gbAs` extraction), `render.py`/`composite.py`
  (text-mode BG/OBJ rendering used only for orientation), `lz.py` (GBA LZ77 sweep),
  `summ.py`, `snap.sh`/`load.sh` (savestate automation).
* All findings above are address- and byte-based; no screenshots were used as
  evidence.

## Legal note

No ROM, extracted graphics, audio or game text is redistributed with this report;
only hashes, addresses, algorithms and short factual strings are recorded.
