# Gauntlet Dark Legacy (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Gauntlet Dark Legacy/Gauntlet Dark Legacy.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| `file` identification | Game Boy Advance ROM image: "GAUNTLET_DL" (AYGE5D, Rev.00) |
| Header title | `GAUNTLET_DL` (file 0xA0) |
| Game code | `AYGE` (file 0xAC) |
| Maker | `5D` (Midway, file 0xB0) |
| Version | `0x00`; fixed byte `0x96`; complement `0x5F`; header checksum `0x0000` |
| Entry word | `0xEA00002E` → `b 0x080000C0` (stock GBA crt0) |
| MD5 | `2c6411d76d5438da19f193b630da1c63` |
| SHA-1 | `3ea608f4ea2235886fa1d7256f6a9ae88c2c0e28` |
| SHA-256 | `0e047503cb6cbf837372a4cdf318b9eb6a7ceac2c8bf99837c9d8dd0b35b877f` |

### Independent check of the "2-in-1" brief

**This image is not a 2-in-1 compilation.** A whole-file scan for the 156-byte
Nintendo logo found exactly **one** header, at file offset `0x0`, with title
`GAUNTLET_DL` / code `AYGE`. No second logo, no second header, no sub-image
base, no appended trainer. The boot splash renders
"Gauntlet Dark Legacy (c)1998-2002 / Midway Games West Inc." and the attract
loop shows "Pocket Studios". Nothing related to Rampart exists in this ROM.
The brief's "2-in-1 (Gauntlet + Rampart)" therefore describes the sibling
image analysed at position 328 (`Gauntlet - Rampart.gba`), not this one;
at the container level nothing is shared (different single-header images).
No patch/trainer/scene cracktro is present: entry word and crt0 at 0xC0 are
stock, and the `0x0000` header checksum is the normal rebuilt-header
artifact (guide §16.1); no menu other than the game's own was observed.

## 2. Executive summary

**Finding: this GBA build has no in-game/developer-intended cheat code system.**
There is no password entry field, no code table, no validator, no key-mask
cheat sequence, and no hidden/debug menu. The negative is proven over the
whole searchable space, not inferred from a failed lookup (guide §0.2.5,
§16.3 "No system"):

* The game's text bank is ASCII with inline control bytes (not plain C
  strings, which is why `strings` found nothing). After decoding the whole
  8 MiB with control bytes stripped, **zero** occurrences of `PASSWORD`,
  `CHEAT`, `SECRET`, `UNLOCK`, `DEBUG`, `INITIAL`, `LEVEL SELECT`, `BONUS`,
  `HIDDEN`, or `TRAINER` exist.
* Every screen reachable with the full GBA button set was walked: legal
  splash, timed attract loop (high-score table, main menu, Pocket Studios
  splash, logo), main menu, OPTIONS → AUDIO and DIFFICULTY, character screen
  with its NEW/SAVE/LOAD/START ring, QUIT confirmation, gameplay, and the
  high-score table. RAM state changes were captured by savestate diffs.
* All published codes found on the web were verified against the ROM:
  44 distinct 6-letter codes, plus the console debug-menu names, absent in
  ASCII, case-folded, `+0x20`, UTF-16LE/BE, reversed, and
  control-byte-interleaved encodings. The widely published code list is for
  **PS2 / GameCube / Xbox / Arcade** (entered as a character *name*); the
  GBA SKU has no name-entry surface at all. Independent corroboration:
  3rd party cheat indexes' GBA page says "No Codes, No Passwords, No Unlockables";
  3rd party cheat indexes' only GBA-specific entry is an out-of-scope "walk through walls"
  gameplay exploit; a 3rd party cheat index's debug menus are PS2/Xbox/GameCube only.
* No novel code could be minted because no code system exists. Sections
  6b/7 therefore give the enumeration of the *empty* space with exact
  counts and rejection-style bounds (there is no accepted input to enter).

The only developer-intended configuration is ordinary OPTIONS: AUDIO
(MUSIC/SFX on/off) and DIFFICULTY (EASY/MEDIUM/HARD). These are settings,
not cheats.

## 3. How to reproduce

Emulator: `mgba` SDL build, `Xvfb :318`, `DISPLAY=:318`,
`SDL_AUDIODRIVER=dummy`, keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad=arrow keys. Savestates: `Shift+F1..F8` save,
`F1..F8` load (verified working).

Menu path:

1. Boot. Legal splash is timed; the game then enters a ~36 s attract loop:
   high scores → main menu (START/OPTIONS/CREDITS) → Pocket Studios splash
   → black → "Gauntlet Dark Legacy" logo → high scores. Most buttons merely
   advance this loop; `A`/`Start` on the main menu starts a new game.
2. From the main menu, **hold Down and tap A** → OPTIONS. (Plain D-pad does
   not move the attract-menu cursor; inside OPTIONS the D-pad works
   normally.) OPTIONS → AUDIO → MUSIC/SFX; OPTIONS → DIFFICULTY →
   EASY/MEDIUM/HARD (MEDIUM checked by default). Long-hold B (~1 s) backs
   out one level.
3. `A` on START → character screen: ARCHER, Strength 250, Speed 600,
   Armour 200, Magic 300, Level 1, Health 500. The bottom item is a ring
   NEW → SAVE → LOAD → START selected with Left/Right; START enters play.
   B opens QUIT? (YES/NO).
4. In play, the character appears in the first level with a boss dialogue;
   Start/Select did not open a pause menu while dialogue was active.
5. Published-code tests: none can be entered — there is no name/password
   field on any of these screens. The verification performed was literal
   ROM search under 7 encodings (Section 4/6).

Screenshots used as evidence were in `/tmp/gauntletdl/` (boot,
title_a2b_crop, press_start, optL_sheet, opt2b_crop, audiosub2_crop,
backmain_crop, s1_crop, opt_start_crop, loop_sheet, btn_sheet).

## 4. Address map

| File offset | ROM address | Meaning | Evidence |
|---:|---:|---|---|
| 0x000 | 0x08000000 | Header, stock crt0 entry `b 0x080000C0` | Derived (bytes) |
| 0x0A0 | 0x080000A0 | Title `GAUNTLET_DL`, code `AYGE`, maker `5D` | Derived |
| 0x113056 | 0x09113056 | Text bank: legal splash ("Gauntlet… (c) 1998-2002", MIDWAY, LICENSED BY NINTENDO) | Derived (decoded) |
| 0x11341F | 0x0911341F | Menu text "START"/"OPTIONS"/"CREDITS", followed by AUDIO/MUSIC/DIFFICULTY/MULTIPLAYER MODE | Derived (decoded) |
| 0x112000–0x115000 | 0x09112000–0x09115000 | Main text bank: menu, options, level names, credits, dialogue; ASCII interleaved with control bytes | Derived |
| 0x100000–0x10E000 | 0x09100000–0x0910E000 | Additional text/dialogue banks (high printable density) | Derived |
| 0x07369D | 0x0807369D | ASCII→font-tile mapping table (`A-Z0-9`, accented glyphs, lowercase) | Derived (bytes) |
| 0x03020 / 0x5DC428 / 0x5DC69C / 0x5DC944 / 0x74B5C4 | 0x08003020 etc. | The **only** five literal references to `0x04000130` (KEYINPUT) in the ROM | Derived (byte scan) |
| — | 0x030033A0, 0x030033A4 | IWRAM menu-state bytes: changed 1→2 and 1→3 across an OPTIONS navigation (savestate diff ss7→ss8) | Observed |
| — | 0x02006398+ | EWRAM tile-index arrays for text rendering; 10,558 bytes changed across the same transition | Observed |
| — | 0x02000000–0x0203FFFF / 0x03000000–0x03007FFF | EWRAM/IWRAM (state offsets 0x21000 / 0x19000 in decompressed `.ssN`) | Derived/Observed |

No validator function, code table, key-mask sequence table, or password
alphabet was found, so none can be listed.

## 5. Algorithm

Not applicable — no code algorithm exists in this build. The relevant
reverse-engineered behavior is the text encoding:

```
decode_text(bank):
    for byte in bank:
        if 0x20 <= byte <= 0x7E: emit ASCII(byte)
        else: emit control_code(byte)   # formatting / colour / spacing
```

The font renderer maps ASCII through the table at file 0x7369D to 4bpp tile
indices. Sample: bytes `47 61 75 6e 74 6c 65 00 74 20 44 61 72 6b 20 4c 03
65 67 61 63 79` → "Gauntlet Dark Legacy". This is why a `strings` scan
missed every in-game label (guide §11 "Not all text is ASCII", §11 "keyword
hits need context").

Savestate RAM reading (guide §16.13): `.ssN` is PNG with a `gbAs` chunk;
`zlib.decompress(chunk)` yields 397,312 bytes; IWRAM at +0x19000, EWRAM at
+0x21000. Diffs ss1↔ss2 (character screen ↔ gameplay) and ss7↔ss8 (AUDIO
navigation) provided the RAM observations above.

## 6. Tables

Menu structure (derived from decoded text + screenshots):

| Screen | Items | Effect |
|---|---|---|
| Main menu | START, OPTIONS, CREDITS | START → character screen; OPTIONS → settings |
| OPTIONS | AUDIO, DIFFICULTY | AUDIO → MUSIC / SFX toggles; DIFFICULTY → EASY / MEDIUM / HARD |
| Character screen | NEW, SAVE, LOAD, START | new character / save / load / enter game; B → QUIT? |
| High scores | 10 rows | static developer entries (CJR/L_E/CSS/S_J/D_C/T_H…), not input |

Character defaults observed: Strength 250, Speed 600, Armour 200, Magic 300,
Level 1, Health 500, class ARCHER (one of eight classes named in the text
bank: Warrior, Valkyrie, Archer, Wizard, Sorceress, Knight, Dwarf, Jester).

Published-code verification table (all **absent** from this ROM):

| Source | Codes | Result |
|---|---|---|
| 3rd party cheat indexes GBA cheats (GC-tagged table) | 40 6-letter codes (10000K, 1ANGEL, INVULN, 000000, BAT900, SJB964, EGG911, POJO, PEEKIN, …) | 0 literals in ROM under ASCII / case-fold / +0x20 / UTF-16LE / UTF-16BE / reversed / control-byte-interleaved |
| 3rd party cheat indexes PS2 passwords | 28 codes (BAT900, GAM666, NUD069, …) | 0 literals |
| 3rd party cheat indexes console debug menu | DBRNKR, AAAAAA, MNTHRX, ARIENT, ADMBLY, ZANZI, NICO | 0 literals (the 7 `AAAAAA` hits are compressed-graphics coincidence at 0x7697C etc.) |
| Generic password alphabets | 4 known alphabets | 0 hits; only the font map at 0x7369D |

## 6b. Enumeration

Per guide §0.2, an engagement with a code system must enumerate its whole
space. This build has an **empty** code space; the following bounds prove it
rather than merely asserting it.

* **Code space size: 0 accepted codes.** No validator, no accepted-input
  table, no input alphabet, and no entry field exist. Components required
  for any of the four cheat classes are all absent:
  * Password/name field: none on any walked screen; the decoded text bank
    contains no `NAME`, `ENTER`, `INITIAL`, `PASSWORD`, `CODE` string (0
    occurrences each after control-byte stripping). The 6-letter codes are
    a *character-name* feature of the PS2/GC/Xbox/Arcade SKUs, which this
    port does not implement.
  * Code table: 0 literal hits for 44 published codes × 7 encodings = 308
    searches; 0 hits for 7 console debug names × 2 encodings = 14 searches.
  * Button-code table: 62 candidate u16 arrays of single-key masks were
    found by scanning all 4 MiB of aligned u16 values; all are 4–5 elements
    long, located in compressed-graphics regions (e.g. 0x4D0434, 0x1EADF4),
    and none matches a known cheat sequence or sits behind a validator
    literal pointer. No published GBA button code exists to seed a prefix
    search (guide §5.4a requires a known prefix; none is available).
  * Debug menu: console debug names absent; no hidden menu item in the
    decoded option tables (main menu 3 items, OPTIONS 2 items, AUDIO 2
    items, DIFFICULTY 3 items, character ring 4 items — all enumerated in
    §6). Guide §16.3: this is class 1 "No system", not dead/gated/cut code.
* **Novel code:** impossible by construction; none is claimed. Guide §0.2's
  "mint an unpublished code" deliverable is replaced by its negative
  counterpart (§0.2.5): the whole representable space was checked.
* **Bounds proven by rejection:** there is no input syntax to submit a
  wrong checksum or out-of-range field to. The closest bounded test is the
  OPTIONS layer: DIFFICULTY accepts only Easy/Medium/Hard (verified by
  enumerating all three rows and observing the single checkmark), and the
  MUSIC/SFX toggles accept only on/off. No fourth difficulty and no
  "level select" row exists in the option list (decoded text + screenshot
  enumeration).
* **Save space:** the 512-byte SRAM (`.sav`) is normal character data
  (first bytes `00 10 00 09 00 04 00 01`, remainder `0xFF` on a fresh
  file); no code/checksum field, no hidden flag.

## 7. Validation evidence

* **Observed (emulator):** every screen listed in §3; the attract sequence
  (loop_sheet.png); all menu item rings (optL_sheet.png, opwalk_sheet.png,
  ow_sheet.png, opt2b_crop.png, audiosub2_crop.png); gameplay
  (opt_start_crop.png); QUIT dialog (back1_crop.png); RAM byte changes from
  savestate diffs (§4).
* **Derived:** ROM header/logo scan; text-bank decoding; font map at
  0x7369D; literal/encoding searches; key-mask scan; menu item counts from
  decoded text plus screenshots; SRAM layout.
* **Inferred (labelled):** the stand-alone CREDITS menu screen was not
  reached. Inputs tested from the main menu: A, Start, B, Select, L, R,
  Up, Down, held-direction+A (1–3 A taps), with and without 0.35 s holds;
  outcomes were only "start game", "enter OPTIONS", or "advance attract
  loop". Credit *content* is nevertheless fully documented from the decoded
  text bank (producer/developer/tester names) and the Pocket Studios splash
  observed in the attract loop. No cheat-related content appears in either.

No ROM or copyrighted assets are redistributed by this report; only
addresses, hashes, and findings.

## 8. Unknowns

* The standalone CREDITS menu screen could not be entered with the tested
  input set (see §7); its text content is covered by the decoded bank.
* Pause/menu behavior *during* active gameplay dialogue was not observed to
  open a settings screen with Start/Select; a pause menu after dialogue
  completion was not exhaustively replayed. No code surface is associated
  with it either way.
* Some high-entropy ROM regions are compressed graphics; text hidden inside
  them would not appear in the decoded-bank search. The generic alphabet
  and literal searches covered the whole 8 MiB regardless, mitigating this.

## 9. Tooling

* `file`, `xxd`, `strings -t x`, `grep -iE`, `sha1sum`/`sha256sum`/`md5sum`.
* Python 3 scripts: header/Nintendo-logo scan, control-byte text decoder,
  multi-encoding literal search, u16 key-mask scan, savestate `gbAs` zlib
  decoder and RAM diff.
* `mgba` SDL (`-3`), `Xvfb :318`, `openbox`, `xdotool`, `scrot`,
  ImageMagick (`convert`, `montage`, `compare`), `gdb-multiarch` (GDB stub
  unusable: fixed port 2345 occupied by another session; `-C gdb.port=`
  unsupported in this build; savestate diffing used instead).
* Working artifacts: `/tmp/gauntletdl/`.
