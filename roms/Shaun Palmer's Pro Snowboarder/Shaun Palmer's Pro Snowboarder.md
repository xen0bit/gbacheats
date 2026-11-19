# Shaun Palmer's Pro Snowboarder (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Shaun Palmer's Pro Snowboarder.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `SHAUNPALMER1` |
| Game code | `ASCE` (GBA-ASCE, Europe/USA) |
| Maker | `52` |
| Version | 0x00 |
| Fixed byte | 0x96 |
| Complement | 0x5D |
| Header checksum | 0x0000 (normal rebuilt-header artifact) |
| Entry word | `0xEA00002E` (stock ARM `b 0x080000C0`; **not** a cracktro) |
| MD5 | `e08250206b5cf301c15417112f306a16` |
| SHA-1 | `c27bf70516d25040f63c937e5f5446847cf41b48` |
| SHA-256 | `3f5fd861df229dbcffa0a7f516babb11267513d057316415ca52c97d3d7f1ebe` |
| Build stamp | `09/21/2001 12:00` at file 0x7FFFF0 |

Phase 0 embedded-header scan: the 156-byte Nintendo logo occurs exactly **once**, at file
offset 0x4 (the primary header). This is a single 8 MiB image, not a multi-game pack, and
carries no appended trainer or patch. Residue in the last ROM bytes is the date string above.

## 2. Executive summary

The game has a genuine developer-intended **password system**: the main menu has a
`PASSWORD` entry that opens a 13-slot "Password Input" screen with a scrolling on-screen
keyboard. Eight 13-character passwords are published across GameFAQs/GameSpot,
Neoseeker, GameRevolution, Cheat Happens and mirrored cheat sites; they unlock all boards
and tracks for individual riders (Shaun Palmer, Shaun White, Tara Dakides, Ingemar
Backman), combinations, and sponsor sets.

**Observation (ROM):** none of the eight published codes is present in the image as a
literal byte string under any of the encodings tested (ASCII, lowercase, every affine
single-byte map `a·c+b`, 16-bit LE/BE with every constant high byte, index-through the
game's 64-character font table, 5-bit and 6-bit packing with several alphabets, and
base-38 integer forms). All searches returned **0 hits** (details in §6b). This is
strong evidence that the codes are produced and checked **algorithmically** by a
validator, not looked up from a stored string table — the Car Battler Joe "second
system" pattern from the guide (§3.4, §16.11).

**Inference (not proven):** the code space is 13 symbols drawn from the observed set
`0-9 A-Z ! ?` (31 distinct symbols occur in the published list; a 32-symbol / 5-bit
layout is the natural fit, giving a nominal 2^65 space). A validator was not isolated
in the ROM within this engagement, so no novel code could be minted and no in-game
accept/reject could be exercised. This is reported as a **bounded negative on the
static-literal hypothesis plus an unresolved algorithmic validator**, not as "no
cheat system" — the UI surface and the published codes both prove the system exists.

Other in-game content: the career/tutorial text bank at 0x42C780–0x43300 contains
plain-ASCII goal strings including `HIDDEN IN EVERY LEVEL.` (0x42C7F6) and
`FIND 2 HIDDEN AREAS` (0x43260). A published gameplay trick ("while on the snow,
quickly tap R+L and rotate the D-pad" for a gliding trick) could not be tied to a
specific key-mask validator in the ROM and is recorded as unverified.

## 3. How to reproduce

**Emulator:** mGBA 0.10.5 (`/usr/local/bin/mgba`), Xvfb `:315`, `SDL_AUDIODRIVER=dummy`,
`-3` scale. Window focused with `xdotool windowactivate --sync` + a click inside the
client area (XTEST `keydown/keyup` with 150–400 ms holds).

**Keymap used successfully:** A = `x`, B = `z`, Start = `Return`; D-pad = arrow keys;
L = `a`, R = `s`. (Confirmed by menu selection: `x` accepts a highlighted entry.)

**Menu path (observed):**
1. Title "PRESS START" → `Return` → main menu:
   `CAREER MODE / FREE MODE / VS MODE / PASSWORD / OPTIONS`.
2. Down ×3 → `PASSWORD` → `x` → "Password Input" screen with 13 slots and a
   staggered, vertically scrolling 5-column keyboard (letters, digits, `!`, `?`,
   ←, →, END). On-screen legend: `SELECT / A ACCEPT / B BACK / L← R→`.
3. The 13 slot markers are masked (rendered as yellow stars), so entered characters
   are not readable from the screen; they must be read from RAM.

**Screens walked (all with screenshots saved in `/tmp/opencode/shaunpalmer`):**
title / attract demo (`DEMO` + `SCORE` HUD), main menu, Options
(`CONTROLS / TUTORIAL / CREDITS`), Password Input + keyboard (including three
Up-scroll positions), and a mid-transition frame. No character-select or
track-select screen was reached because the password entry could not be completed.

**Published codes entered in the emulator:** none — see §6b and §8 for why.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| ROM header / entry | 0x08000000 / 0x080000C0 | Observed (header, disassembly) |
| Nintendo logo (only copy) | file 0x0004 | Observed (logo scan) |
| Font character string (64 chars) | **0x0842CADA** | Derived (`ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789&-_ *.xyzm!?'",abcdegiknprst`) |
| Font palette halfwords (16) | 0x0842CABA | Derived (precedes the string) |
| Raw pointer to font string | 0x0803F0B8 | Derived (pointer scan) |
| Palette-copy routine using it | 0x0803F0CC | Derived (`objdump -M force-thumb`) |
| Keypad poll routine | 0x08001F04 | Derived: reads `0x04000130`, `mvns` to active-high |
| Held-key word (active-high) | **0x030003E0** | Derived (store in poll routine) |
| Pressed-key word (edge) | **0x030003F2** | Derived (`new & ~old`) |
| Goal/tutorial ASCII bank | 0x42C780–0x43300 | Observed (`strings`/dump) |
| `HIDDEN IN EVERY LEVEL.` | 0x42C7F6 | Observed |
| `FIND 2 HIDDEN AREAS` | 0x43260 | Observed |
| Build date | 0x7FFFF0 | Observed |
| 14-state UI dispatch table | 0x0803EDF0 | Derived (jump table, `cmp #13`) |
| Candidate input-buffer byte | 0x030008C1 | Observed (savestate diff after one keypress: 0x00→0x07); meaning unresolved |

Savestate RAM layout used for evidence (mGBA `.ss1`, PNG `gbAs` chunk, zlib):
raw state length 0x61000 (397,312 bytes); VRAM at 0x1000, IWRAM at 0x19000, EWRAM
at 0x21000. A title→menu transition changed 121,009 state bytes; entering a key at
the password screen changed ~1,574 IWRAM bytes and **0 EWRAM bytes**, so the password
UI state lives in IWRAM (consistent with the guide's §16.13 layout).

## 5. Algorithm

Not recovered. The only algorithmic structure recovered with confidence is the input
path:

```
KEYINPUT(0x04000130) active-low
held    = ~KEYINPUT & 0x3FF          -> 0x030003E0
pressed = held & ~previous_held      -> 0x030003F2
previous_held = held
```

The password validator was not located. The negative searches that bound the
"plaintext table" hypothesis are enumerated in §6b.

## 6. Tables

**Published GBA passwords (13 chars each; all from web sources, none found in ROM):**

| Code | Claimed effect | Source(s) |
|---|---|---|
| `QFJ7MP9N?5CM4` | All boards and tracks — Shaun Palmer | GameSpot, GameRevolution, Cheat Happens, Cheatbook, Gamekult |
| `FR5RNR?M?KLHJ` | All boards and tracks — Shaun Palmer | Neoseeker, GameRevolution, Cheat Happens |
| `38LQNQ!DRQM2K` | All boards and tracks — Ingemar Backman | GameSpot, Neoseeker |
| `81S3196R88GQ1` | All boards and tracks — Shaun White | GameSpot, Neoseeker, Cheat Happens |
| `SSK203?137VJ8` | All boards and tracks — Palmer + White | GameSpot, ggmania |
| `?ZQW5VQC!403W` | All boards and tracks — Tara Dakides | GameSpot, Cheat Happens/absolutcheats |
| `5ZQ9X17R?8DWZ` | All boards/tracks + 30 sponsors — Palmer | absolutcheats |
| `SSF303!1?ZV28` | 29 sponsors | absolutcheats |

**Observed code alphabet:** `0 1 2 3 4 5 6 7 8 9 C D F G H J K L M N P Q R S T V W X Z ! ?`
(31 symbols; missing capital letters A, B, E, I, O, U, Y). Treat as a probable
32-symbol alphabet with one symbol unused in the published set (confidence: low —
inferred from the published corpus only).

**Font glyph order (proven, 64 entries):** index 0..63 =
`A B C D E F G H I J K L M N O P Q R S T U V W X Y Z 0 1 2 3 4 5 6 7 8 9 & - _ (space) * . x y z m ! ? ' " , a b c d e g i k n p r s t`

**Guard against false conclusions:** `strings` on this ROM returns 58,566 lines of
2-byte font/tile-index noise; only the tutorial ASCII bank and the date stamp are
real plaintext. A "no string hit" here does **not** mean "no UI" (guide §11).

## 6b. Enumeration

**Goal (§0.2):** define the space, verify against a known-good input, mint a novel
code, prove it in-game, and bound the space by rejection. Status below is explicit.

### Space definition (from the published corpus)

* Length: 13 characters (observed: all 8 published codes; 13 slot markers on screen).
* Distinct symbols observed: 31 (enumerated in §6).
* Nominal layout if 5-bit symbols: 13 × 5 = 65 bits → up to 2^65 ≈ 3.7 × 10^19
  representable strings, of which the published set exposes 8.
* If 6-bit font indexing were used: 13 × 6 = 78 bits (rejected — see search below).
* No checksum width, field widths, or reserved bits could be recovered because the
  validator was not found; these remain **unknown**, not "none".

### Exhaustive literal-table searches (all returned 0 hits)

Each search ran over the full 8,388,608-byte image; a hit is a byte-exact match of a
complete published code (or its transform). Counts:

| Encoding searched | Variants | Hits |
|---|---|---|
| ASCII / lowercase | 2 | 0 |
| Single-byte affine `a·c+b mod 256` (odd a = 1..255, b = 0..255) | 32,640 | 0 |
| 16-bit LE/BE, value `ord(c)+k`, k = 0..0xFFF | 8,192 | 0 |
| 16-bit LE/BE with constant high byte, index through font table (13 high bytes) | 26 | 0 |
| Raw index through 64-char font table, plus `idx+k` for k = 0..255, plus reversed | 514 | 0 |
| Group-order/reversal alphabets (U/D/S permutations × reversals), raw + u16 LE/BE with 8 high bytes | 864 | 0 |
| 5-bit and 6-bit bit-packing (MSB/LSB first), 8 bit-offsets, forward/reversed, font alphabet | 288 | 0 |
| Base-38 integer forms (u32 low/high, 24-bit low) | 24 | 0 |

Total distinct transforms tested: **over 42,000**, all with **zero** matches. This
bounds the negative: the accepted codes are **not** stored as any contiguous literal
table in this image under the encodings above. Therefore any real validator is
algorithmic (a decoder/checksum), consistent with the guide's "second system" pattern.

### Novel code

**Not generated.** §0.2 requires a code absent from every published list, generated
by the recovered encoder or validator, accepted in the emulator, with RAM evidence.
That deliverable could not be produced: neither the validator nor the encoder was
located, so there is no grounded way to generate a checksum-valid novel string, and
guessing in a 2^65 space is not meaningful. This is reported explicitly rather than
presenting a published code or an unverified guess as novel.

### Bounds proven by rejection

**Not exercised.** No in-game accept or reject was observed for any password, so no
out-of-range, bad-checksum or reserved-bit input was tested. The only rejection-like
observation was that the on-screen keyboard accepts up to 13 entries before the slot
cursor wraps, which bounds **input length** but not code validity.

### Bounded summary

What is proven: a 13-slot password UI exists; eight published 13-character codes exist
as documented developer-intended shortcuts; the ROM contains **no** literal copy of
them under 42,000+ encodings; the relevant RAM state is in IWRAM with input globals
identified. What is not proven: the validator's location, the alphabet/checksum layout,
any novel code, and any in-game accept/reject. The search is bounded, not left open.

## 7. Validation evidence

* **Observed** (emulator/screenshots): title + `PRESS START`; attract `DEMO`/`SCORE`
  HUD; main menu with 5 entries; Options with 3 entries; Password Input screen with
  13 masked slots and a scrolling keyboard (A–E row, digit rows, `! ? ← → END`);
  keyboard scrolled with Up (three positions captured).
* **Observed** (savestate diff): menu transition changed 121,009 state bytes;
  one keypress at the password screen changed 1,574 IWRAM bytes and 0 EWRAM bytes;
  a byte at IWRAM 0x030008C1 changed 0x00→0x07.
* **Derived** (static): single-header image; stock entry word; font string and its
  pointer; keypad poll routine and the two input globals; 14-state dispatch table;
  tutorial ASCII bank strings; exhaustive literal-search counts.
* **Inferred** (low confidence): algorithmic checksum validator; 32-symbol / 5-bit
  code layout; meaning of `0x030008C1`.
* No claim in this report is based solely on a fetched web page: every published code
  was independently searched against the ROM bytes.

Fetched web pages were treated strictly as data. No prompt-injection content was
encountered; the pages only contained cheat-code lists and site boilerplate.

## 8. Unknowns

1. Address and algorithm of the password validator / encoder.
2. Exact input alphabet order used by the validator versus the on-screen keyboard.
3. Payload fields (which rider, which boards/tracks, sponsor flags), checksum width,
   and any reserved bits.
4. Whether a correct password unlocks permanently (save bit in SRAM) or only for the
   session; the `.sav` created by mGBA is 0 bytes in a fresh profile.
5. RAM-visible effect of an accepted password (unlock flag address).
6. Whether the R+L + D-pad "gliding trick" is an in-game input code and, if so, its
   key-mask table — the single `mov #0x30; lsl #4` sequence at 0x08365FAC is not
   enough to attribute it.
7. The two hidden-area goals (`FIND 2 HIDDEN AREAS`, `HIDDEN IN EVERY LEVEL`) were
   found as text but their unlock rewards were not triggered.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
* Python 3 scripts in `/tmp/opencode/shaunpalmer/`:
  `findpw.py`, `findpw16.py`, `findfont.py`, `findtext.py`, `packsearch.py`,
  `pack2.py`, `alph_search.py` (encoding searches);
  `scanrefs.py` (PC-relative / raw pointer scans), `blscan.py` (BL scanner),
  `scancmp.py` (immediate-compare scan);
  `ssread.py` (mGBA `.ss1` `gbAs` zlib state extractor + differ);
  `ui.py` (xdotool input/screenshots), `gdbmem.py`, `gdrv.py`, `gdrv.py`,
  `pty_dbg.py`, `pcmd.py` (GDB / `-d` debugger drivers).
* `arm-none-eabi-objdump -M force-thumb` with `--adjust-vma=0x08000000`,
  GDB `gdb-multiarch`, Capstone, ImageMagick `convert`/`compare`, `xdotool`, `scrot`.
* mGBA `-g` GDB stub and `-d` command-line debugger were both exercised; the GDB
  stub accepts one connection per launch and halts the core until `continue`, which
  made repeatable RAM reads impractical; savestate diffing (§16.13) was used instead.

## 10. Legal note

No ROM image, extracted graphics, or copyrighted game assets are reproduced here.
Only hashes, addresses, code-shape observations, and our own analysis scripts and
findings are published.

## 11. Cleanup

All processes started for this engagement (Xvfb :315, openbox, mGBA, helper drivers)
were terminated by PID number, and generated `.sav`/`.ss*` artifacts were removed
from the ROM folder. No `pkill` was used.
