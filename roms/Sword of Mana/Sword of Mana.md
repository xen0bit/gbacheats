# Sword of Mana (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Sword of Mana/Sword of Mana.gba` |
| Size | 16,777,216 bytes (0x01000000) |
| Header title | `SWORD OF MANA` |
| Game code | `AVSE01` (USA, Europe), Rev. 00 |
| Maker | `01` (Nintendo); SQUARE ENIX developed, Brownie & Brown logo at boot |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) — retail image, no cracktro/trainer appended |
| Header fixed byte 0x96 | present at 0xB2; complement byte 0x00, checksum 0x8100 |
| MD5 | `c7e5d28e7c430454aeff766961095561` |
| SHA-1 | `a7ff0b4482c7c3b19467af37c3e277321cd9f1cd` |
| SHA-256 | `767d6139a8d5a9c79514384e77b6c651d31dc86036c6fee05b9ae64697c251b7` |

## 2. Executive summary

**No in-game/developer-intended cheat code system exists in this ROM.** There is no password
entry screen, no button-code sequence, no hidden debug menu and no unlockable code surface in
the reachable UI. Every published "cheat" for this title is a GameShark / CodeBreaker /
Action Replay device code (out of scope); no published in-game password, button code or
hidden menu could be found either.

This is a **bounded negative**, not "not tested":

* The title-screen main menu has exactly **one** selectable entry (`NEW GAME`); D-pad in all
  four directions does not move any cursor and no second entry is drawn, with or without a
  cartridge save present.
* The only on-screen alphabet is the **character-name keyboard** (5×7 grid). It is consumed
  as a character name (the typed value is echoed in dialogue as `BCC:` / `AAAAAAA`), i.e. a
  label field, not a validator — guide §16.2b.
* The in-game Start menu exposes **two** entries (`Weapons`, `Status`) at this point in the
  game; no debug/sound-test/level-select entry exists.
* Static enumeration over the full 16 MiB found no code alphabet, no validator, no
  comparison table, no button-mask sequence and no debug gate (counts in §6b).
* A GameFAQs walkthrough (FAQ 25327) states: *"There was originally a Password option on the
  Main Title screen."* This is consistent with a **cut feature**: the final ROM has no
  reachable password surface. (Claim from a third-party walkthrough — **Inferred** as to why;
  the ROM evidence for absence is independent of it.)

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
* Keymap used: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`,
  D-pad = arrow keys. Holds of 60–150 ms; 40–70 ms for single menu steps (guide §16.2).
* Screen path (all observed):
  1. Boot → "Brownie & Brown" logo → SQUARE ENIX logo → "PUSH START" title.
  2. Start → main menu: `NEW GAME` only. Pressed Down/Up/Left/Right repeatedly (12+ presses
     each) — cursor stays on `NEW GAME`, no other label appears.
  3. A → character select (hero / heroine). A → "Name your character." keyboard.
  4. Keyboard: 5-column grid `ABCDE/FGHIJ/KLMNO/PQRST/UVWXY`, extra rows `Z()[]` and
     lowercase. **Start** switches focus to the `OK` button; A confirms; Left→Yes confirms.
  5. Long scripted intro (dream → Granz Castle battle → naming the heroine).
  6. Free play in Granz Castle; Start → in-game menu. Right toggles the two entries
     `Weapons` ↔ `Status`; Down does not change the selection.
* RAM evidence: savestates were taken at character select (`.ss1`), name entry (`.ss2`),
  in-game menu open (`.ss3`) and menu closed (`.ss4`). Parsing the `gbAs` zlib chunk gives a
  397,312-byte state; IWRAM at raw 0x19000 → `0x03000000`, EWRAM at raw 0x21000 →
  `0x02000000` (guide §16.13). Menu open→closed changed, among others:
  `0x020003C0` `01→00`, `0x02000CB4` `06→02`, `0x02000CFC` `01→00`, `0x02000D28`
  `01→00`, `0x02000F98` `01→07`, `0x03002DDC` `0e 0e→02 02`. These are the concrete
  screen-state bytes recorded for the menu walk.

## 4. Address map

| Address | Meaning | Evidence type |
|---|---|---|
| `0x08000000`–`0x080001F0` | ARM crt0 / boot stub; stock entry `0xEA00002E` | Observed (header bytes) |
| `0x08002FC0`–`0x08005180` | Thumb code; tile/UI helpers | Derived (objdump) |
| `0x08005130` | Text/script parser: reads **16-bit big-endian** codes; `code-0xFD <= 14` is the control-code range; non-control codes go to `BL 0x08005898` | Derived (objdump) |
| `0x08004A32` | Byte→tile conversion for the name-entry/keyboard text path: `value -= 0x8D`, index table at `0x08371F20`, result stored as halfword | Derived (objdump) |
| `0x08371F20` | Character/tile conversion table (see §6) | Observed (ROM bytes) |
| `0x08371F30` | Ascending 0x00.. table (paired with the reversed 0x0F..0x00 at 0x08371F20) | Observed |
| `0x03000000`+ | IWRAM: game copies ARM routines here at boot (e.g. literals `0x08092AD9`, `0x08373364`, `0x08373164` seen in the savestate) | Observed (savestate RAM) |
| `0x02000000`+ | EWRAM: game state; menu-open bytes listed in §3 | Observed (savestate diff) |
| `0x04000130` | KEYINPUT (read `0x03FF` idle) | Observed (PTY debugger) |

Note: mGBA's GDB stub on port 2345 was occupied by another session, so a private `-d` PTY
debugger and savestate diffing were used instead (guide §16.2, §16.13).

## 5. Algorithm

There is no password/checksum algorithm to reverse. The relevant algorithm is the text
renderer, documented only to justify the negative:

```
# text stream: 16-bit big-endian codes
code = (rom[p] << 8) | rom[p+1]; p += 2
if 0xFD <= code <= 0x10B: handle control code (0x08005130 range test)
else: draw glyph through 0x08005898

# name-entry/keyboard byte path (0x08004A32)
tile = table_0x08371F20[byte - 0x8D]      # stored as 16-bit
```

No routine in the enumerated ROM reads a user-typed code buffer, compares it against a
constant/table, or writes a cheat flag. No validator was found, so none was reimplemented.

## 6. Tables

**Name-entry keyboard (observed, 5 columns):**

```
A B C D E
F G H I J
K L M N O
P Q R S T
U V W X Y
Z ( ) [ ]
a b c d e
```
`A`/`RE`/`OK` buttons above the grid; Start moves focus to `OK`.

**Character/tile conversion table at `0x08371F20`:** first 16 entries are reversed
`0F 0E 0D … 00`; from index 0x10 onward the table is mostly identity with `0x00` gaps,
e.g. index 0x30→`0x00`, 0x35→`0x34`('4'), 0x3F→`0x3F`('?'), 0x40→`0x40`('@'),
0x41→`0x41`('A'), 0x46→`0x42`('B'), 0x47→`0x43`('C'), 0x48→`0x44`('D'),
0x4A→`0x45`('E'), 0x4F→`0x52`('R'), 0x73→`0x48`('H'), 0x74→`0x49`('I'),
0x92→`0x4A`('J'), 0xB2–0xB7→`L M N O P Q`, 0xD3→`S`. The sparse/scattered layout is why a
single-offset ASCII decode fails; this is a font/tile table, not a cheat alphabet.

**Reachable menu entries (observed):**

| Screen | Entries |
|---|---|
| Title main menu | `NEW GAME` (1) |
| In-game Start menu | `Weapons`, `Status` (2) |

## 6b. Enumeration

**Space definition:** No code space exists. There is no alphabet of accepted symbols, no
code length, no field widths, no checksum and no lookup table of accepted codes. The only
alphabet in the game is the 26-letter (plus symbols/lowercase) **name-entry keyboard**, which
is a label field whose consumer is the save data/dialogue, not a validator. Representable
values for the "code system": **0**.

**Novel codes minted:** none — impossible; there is no validator or generator to mint from.
No code, novel or published, exists in this SKU. Published GameShark/CodeBreaker entries
(e.g. `B4A5FFDDBB64`, `9635298F…`) are cheat-device codes, explicitly out of scope, and do
not appear in the ROM as in-game strings.

**Rejection bounds:** not applicable — there is no input surface to submit a bad code to.
The bounded negative is established by the following **counts** (all over the exact ROM
hash in §1):

| Search | Space covered | Result |
|---|---|---|
| `strings -t x -n 4` + keyword filter (`password|cheat|debug|sound test|secret|unlock|menu|…`) | 16,777,216 bytes; 71,001 strings of length ≥5 | 0 meaningful hits (4 garbage matches in compressed audio/graphics) |
| Exact/offset encodings: ASCII, `+k`/`-k`/`xor k` (k=0..255) for `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `SOUND TEST`, `NEW GAME`, `CONTINUE`, `MANA` | 16 MiB × 768 transforms | 1 hit: header `SWORD OF MANA` at `0xA0`; 2 coincidences in compressed data |
| UTF-16LE / UTF-16BE for the same words | 16 MiB × 2 | only coincidental 4–8 byte matches in compressed blocks |
| GBA LZ77 decompression (`0x10`+24-bit size), scan decompressed payloads for the same words | **3,245** successfully decompressed blocks | 0 cheat/debug/password strings (3 incidental `TEST` in graphics) |
| Button-mask tables: runs of ≥5 `u16` values each one of the 10 GBA single-button masks | 16 MiB scanned; **970** candidate runs | 0 known code sequences; Konami prefix and its reverse: 0 hits; all runs fall in graphics/data regions |
| Button-code literals `MONKEYS`, `POLTER`, `BANANA`-style words under 768 transforms | 16 MiB × 3 words | 0 hits for `MONKEYS`/`POLTER`; 1 coincidence for `BANANA` |
| Screen walk | title menu, character select, 2 name-entry screens, intro, gameplay, in-game menu | 0 password/code/debug/sound-test entry points |

**Conclusion of enumeration:** the accepted in-game code set for this ROM is the empty set.
A second analyst can reproduce this by re-running the searches above and by the screen path
in §3; no code needs to be typed.

## 7. Validation evidence

* **Observed** — boot logos and all screens listed in §3; title menu with one entry and an
  unmoving cursor after 12 presses in each D-pad direction; name keyboard layout; typed
  `BCC`/`AAAAAAA` echoed in dialogue; in-game menu entries `Weapons`/`Status`; savestate RAM
  bytes in §3; header bytes and hashes in §1.
* **Derived** — text parser at `0x08005130` (16-bit BE codes, control range 0xFD–0x10B) and
  the byte→tile conversion at `0x08004A32` using the table at `0x08371F20`; IWRAM code copy
  evidenced by pointers in the savestate.
* **Inferred** — the walkthrough's "originally a Password option" is a cut feature; the
  sparse font table explains why ASCII scans fail. Neither claim is required for the
  negative.
* No generated code exists to confirm in-game; the negative is supported by the counts in
  §6b and the screen enumeration, per guide §0.2 ("negative results bounded").

## 8. Unknowns

* The game's full dialogue/script bank was not exhaustively decoded to plaintext; the text
  engine uses a sparse custom font table and a 16-bit code VM. The keyword searches therefore
  cover ASCII/UTF-16/offset/LZ77 forms and the font table used by the UI, not a complete
  glyph-by-glyph transcription of every script line. A hidden *line of dialogue* containing
  a "code" could in principle have been missed; no screen exposes anywhere to enter one.
* Whether the cut `Password` option left dead code in the ROM was not proven either way;
  no reachable path and no validator were found.
* Later-game unlockables (e.g. New Game+ style carry-over, black enemies after 999 kills,
  Niccolo's super items) are gameplay progression, not codes, and were not exhaustively
  enumerated.
* The in-game Start menu was sampled early in the story (Granz Castle); additional entries
  may appear later. No entry observed is a cheat/debug entry.

## 9. Tooling

* `file`, `xxd`, `md5sum`, `sha1sum`, `sha256sum` — Phase 0 fingerprinting.
* `strings -t x -n 4`, `grep -iE` — ASCII/encoding keyword scans.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` —
  disassembly of `0x08002F80`, `0x080034E0`, `0x08004A00`, `0x08005130`.
* Python 3 scripts in `/tmp/opencode/swordofmana/`: `lzscan.py` (3,245-block LZ77 scan),
  `read_ss.py` (mGBA `gbAs` savestate parser), plus inline scans for encodings, tables and
  button masks.
* mGBA 0.10.5 under Xvfb `:318` with openbox; `xdotool` XTEST input; `scrot` + ImageMagick
  `convert`/`montage` for screenshots.
* A private mGBA `-d` PTY debugger (`pty_dbg.py`) was used for register/KEYINPUT reads
  because the GDB stub port 2345 was held by another session.

**Legal note:** no ROM or copyrighted assets are redistributed; only addresses, hashes,
counts and the analyst's own tooling are published.
