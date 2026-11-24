# The Sims 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/The Sims 2/The Sims 2.gba` |
| Size | 33,554,432 bytes (32 MiB) |
| `file` | Game Boy Advance ROM image: "THE SIMS 2" (B46E69, Rev.00) |
| Header title | `THE SIMS 2` (0xA0) |
| Game code | `B46E` (Europe), maker `69` (Electronic Arts), version `0x00` |
| Entry word | `0xEA00002E` → stock `0x080000C0` crt0 (no cracktro/trainer patched in) |
| Header bytes | `0xB2=0x96`, `0xBC=0x00`, `0xBD=0x62`, checksum `0x0000` (rebuilt-header marker per guide §16.1) |
| MD5 | `51455002b0daa27de8eaa5d9ad1afd6f` |
| SHA-1 | `702a109bd60d2e288814968d49caacdfd14ae2c6` |
| SHA-256 | `d92722d6c980b8fe661e765c2a2ec4ab4eae3c91611f82d0a6fe2ee1d324e2ac` |

Work files: `/tmp/thesims2/` (screenshots `shot00`–`shot50`, savestates, scripts).

## 2. Executive summary

**Bounded negative: this SKU has no developer-intended in-game cheat-code system.** It has no password
screen, no button-code sequence, no hidden/debug menu reachable by controller input, and no code
validator. The only text-entry surface is the Create-a-Sim name field, which is a *label* (a name), not
a validator: the field's buffer is never compared with any constant string in the image (§6b). All
published "cheats" for this GBA SKU are **save-gated unlockables** (episodes unlocked by plot points or
a GBA link cable) or gameplay glitches, not codes. The widely copied "enter codes with the D-pad /
Cheat Gnome" list belongs to the **GameCube/PC** versions, not the GBA image — verified against the
GameFAQs snippet and the GBA-specific cheat pages (Cyberly, SuperCheats).

No GameShark/CodeBreaker/Action Replay material was used or reported.

## 3. How to reproduce

* mGBA 0.10.5 on Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `-3`; keymap A=`x`, B=`z`, L=`a`, R=`s`,
  Start=`Return`, Select=`BackSpace`, D-pad = arrows. GDB stub was unavailable (port conflict); RAM
  evidence was obtained by decompressing the zlib `gbAs` chunk of mGBA `.ssN` savestates (guide §16.13).
* Boot → language select (English first entry) → copyright → title (`shot00`–`shot02`).
* Title `Start` → main menu: **Create-a-Sim / Load-a-Sim (disabled) / Options / Minigames** (`shot03`).
  * Options → **Music Volume / SFX Volume / Language (6 languages) / Credits** (`shot04`, `shot08`).
  * Minigames → **Establish Game Boy® Advance Game Link®** (`shot04`).
  * Create-a-Sim → name entry (on-screen keyboard, uppercase+digits and lowercase+symbols modes,
    `SELECT` toggles case) → 6 tabs: Gender/skin, Hair, Clothes, Leg wear, Aspiration, confirm
    (`shot12`–`shot31`). Entering a name and confirming `YES` drops into the boardroom intro.
  * In-game tutorial → free roam → `Start` opens a 4-tab notebook: **Plot Points / Cast / Props /
    Skills** (tabs switched with L/R, not the D-pad) (`shot45`–`shot47`). No cheat/code tab.
* Savestates used as RAM probes: slot 1 title (`The Sims 2.ss1`), slot 2 main menu (`ss2`), slot 3
  name entry (`ss3`), slot 4 typed name (`ss4`), slot 5 in-game dialog (`ss5`).

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| EWRAM active text buffer (current menu line / dialog text, ASCII) | `0x020028D0` (+ small prefix) | Observed: `ss1` = `Press START`; `ss2` = `Create-a-Sim`; `ss3` = `Done`; `ss5` = `Welcome to my boardroom, @1. You're here…` |
| EWRAM name-entry alphabet (95 bytes `0x20`–`0x7E`) | `0x02001254` | Observed in every state; generated at runtime (no copy of this table exists in ROM) |
| Global state struct base | `0x03003DFC` | Derived: 8 literal refs at `0x0800F63C`, `0x08012B40`, `0x08012F7C`, `0x08012F98`, `0x0801B964`, `0x080211CC`, `0x08021BD4`, `0x08040B74` |
| ASCII literal `CheaterX` | `0x08062AB4` (file `0x62AB4`) | Observed; exactly one pointer in the image |
| Dead function `strncpy(0x03003DFC, "CheaterX", 16)` | `0x080211B8` (literal pool `0x080211CC`/`0x080211D0`) | Derived from Thumb disassembly |
| `strncpy` implementation called by it | `0x08059C18` | Derived |
| KEYINPUT literal refs (`0x04000130`) | `0x080249CC`, `0x08047BB0` | Derived; both are generic input/VM readers, not validators |
| Input state machine (held/new/release) | `0x08024940`–`0x080249C6` | Derived: writes `+0x10/+0x14/+0x18/+0x20/+0x22` of an input struct |

VRAM font glyphs are drawn at runtime into tiles based at `VRAM+0x4000`; the tilemap at
`VRAM+0xE000` uses 4bpp tile indices with `0x149` (tile 329) as the space glyph. The on-screen glyph
bitmaps could not be matched to any ROM byte sequence (no literal/uncompressed font found), which is
why the RAM text buffer above was used to decode text instead of `strings`.

## 5. Algorithm

No validator exists to model. The text pipeline is:

```
ROM script bank (encoded, not raw ASCII)  ->  runtime decoder  ->  EWRAM 0x020028D0 (ASCII)
                                          ->  glyph blitter   ->  VRAM tile RAM at 0x06004000
```

Name entry is a plain buffer: on-screen key → character from the 95-byte EWRAM alphabet at
`0x02001254` → displayed in the name field; `Done` commits it to the Sim record. No checksum, no
comparison against a code constant, no length gate other than the visible field width, and no flag
word is written on name commit (§6b).

## 6. Tables

**Enumerated reachable UI (all screens walked, RAM label read where applicable):**

| Screen | Items / tabs | Count |
|---|---|---|
| Language select | English, Nederlands, Français, Deutsch, Italiano, Español | 6 |
| Main menu | Create-a-Sim, Load-a-Sim (disabled), Options, Minigames | 4 |
| Options | Music Volume, SFX Volume, Language, Credits | 4 |
| Minigames | Establish Game Boy Advance Game Link | 1 |
| Create-a-Sim | Name, Gender/skin, Hair, Clothes, Leg wear, Aspiration + confirm | 6 + confirm |
| In-game notebook | Plot Points, Cast, Props, Skills | 4 |
| Name-entry keyboard | uppercase `A–Z` + `0–9`; lowercase `a–z` + `!@#$%&*()[]`; `Done` | 2 modes, 95-char alphabet |

**Unlockables (not codes):** Aliens Arrived / Weirdness plot (50 pts), There Was This Mummy /
Mystery plot (50 pts), It All Came to an End / Motorcycle plot (150 pts), A Very Special Reunion /
GBA link cable (or 100 points on all other episodes, per community reports). Source: Cyberly,
SuperCheats, warfreak GBA walkthrough. These are save/flag-gated, not controller-input-gated.

**`CheaterX`:** the single cheat-like literal in the image. It is the *source operand* of one
unreferenced `strncpy` at `0x080211B8`; it is never a comparison operand and never read as input.

## 6b. Enumeration

This is a **bounded negative**, not a code enumeration. Bounds and counts:

1. **Alphabet space checked.** Name entry uses the 95 printable ASCII characters `0x20`–`0x7E` at
   `0x02001254` (observed bytes, 95/95 present). The two keyboard modes render all 95 symbols.
   This is the *only* user-text surface in the game.
2. **Code-literal search (strings).** Whole 32 MiB scanned with `strings -t x`, `grep -abo`, and a
   custom encoder sweep (plain ASCII, reversed, XOR 0–255, add/sub 0–255, UTF-16LE/BE, nibble-swap,
   bit-reverse, complement, strides 1–5, additive bases 0–255, and GBA-LZ77 decompression of every
   plausible `0x10`-header block). Known PC/console cheat words (`motherlode`, `rosebud`, `kaching`,
   `boolProp`, `testingCheatsEnabled`, `PASSWORD`, `CHEAT`, `SECRET`, `DEBUG`, `GOD`, `unlock`) gave
   **0 hits**. Case-insensitive alphabetic runs ≥4 letters in the first 8 MiB: 65,786, all code/data
   byte coincidences; in the entire ROM, the only run matching a cheat-related word is `CheaterX`
   at `0x08062AB4` (**1 hit**), used only by the dead `strncpy` above.
3. **Table search.** u16 run scan for button-mask arrays: 36 candidate runs of ≥4 single-button
   values in the first 1 MiB, 1,072 in the first 8 MiB. Manual inspection of the earliest hits
   (`0x08060A60`, `0x08060A90`, `0x08060AC0`, …) shows `(index, value)` pairs of a state-machine
   transition table (values `0,1,2,3,4,5`), **not** button sequences. No array of ≥4 consecutive
   GBA button masks exists in code/data. Only two literals `0x04000130` exist in the image and both
   sit in generic input readers.
4. **Validator search.** The name buffer is never the operand of a comparison: the image contains no
   code/cheat string to compare against; the only cheat-like literal has a single xref used as a
   `strncpy` source. By guide §16.2b the field is a *label*, not a password field.
5. **Novel-code / rejection tests performed.** No published GBA code exists to mint a variant from,
   so the equivalent tests were: (a) novel Sim name `AAA` entered through the real keyboard and
   committed — accepted as a name, with `$0` still shown in the HUD and no flag/UI change (`shot13`,
   `shot32`, `shot40`); (b) `L+R+Start` held on the title screen — only Start acted, no hidden menu
   (`shot49`); (c) `↑↑↓↓←→←→BA` on the title screen — no effect (`shot50`); (d) PC/GCN words
   searched in the ROM and found absent (item 2). Bounds: the representable name space is 95^N for
   the visible field width, but **none of it is a code space** — acceptance is unconditional, so
   there is no accepted/rejected partition to enumerate and no checksum to invert.
6. **Dead-code gate.** The only debug-flavoured function (`0x080211B8`) has **0** Thumb `BL`
   references and **0** 32-bit pointers, including the Thumb-bit variant `0x080211B9` (scanned over
   all 32 MiB). It is unreachable; the "CheaterX" marker cannot be produced by any input.
7. **Result type (guide §16.3).** This is **"no system"** (no alphabet, table, validator or input
   surface for codes), not "dead code", not "cut feature", not "gated feature". The unlockables are
   real but are save/progress-gated, and are reported separately in §6, not as codes.

## 7. Validation evidence

* **Observed** — emulator screenshots `shot00`–`shot50`; EWRAM text-buffer reads from savestates
  (`Press START`, `Create-a-Sim`, `Done`, dialog text); 95-byte alphabet in EWRAM; HUD `$0` after
  committing a novel name; no effect from the two button sequences.
* **Derived** — Thumb disassembly of `0x080211B8`/`0x08059C18` (`strncpy` of `CheaterX`), the two
  KEYINPUT literal xrefs, the BL/pointer counts, the string/LZ77/encoding sweeps, the button-mask
  run scan.
* **Inferred** — ROM script bank encoding is non-ASCII and likely compressed; the exact text codec
  was not recovered. The state-machine table at `0x08060A60` is interpreted as transitions, not
  inputs, from its `(index,value)` structure. Community claims of "100 points unlock Reunion" were
  not exercised in-game (only the link-cable route is in the published GBA-specific list).

## 8. Unknowns

* The ROM's script/text compression format is unresolved. It was bypassed by reading the ASCII text
  buffer the game writes to EWRAM, which is sufficient to enumerate every screen label reached.
* No save-editor or link-cable test was run, so the unlockable flag bits were not mapped to RAM.
* mGBA's GDB stub could not bind (default port held by another session; `-C gdb.port=…` ineffective),
  so RAM reads came from savestate diffs rather than a live debugger. CLI `-d` debugger also stopped
  responding after `continue`.

## 9. Tooling

Scripts in `/tmp/thesims2/`: `ss.py` (savestate `gbAs` zlib extractor), `ui.py` (xdotool
input/screenshots), `findenc.py` (encoding sweep), `bscan.py` (literal/BL xrefs), `lzscan.py`
(GBA-LZ77 block scan), `vram.py`/`fontgrid.py`/`render_map.py` (VRAM glyph/tilemap rendering).
System tools: `mgba` 0.10.5, Xvfb, openbox, xdotool, scrot, ImageMagick, `strings`, `xxd`,
`grep`, `arm-none-eabi-objdump`, capstone, Python 3. No third-party cheat tables were installed.

**Legal note:** no ROM bytes, graphics, or game text are redistributed here; only hashes, addresses,
and the analyst's own observations are published.
