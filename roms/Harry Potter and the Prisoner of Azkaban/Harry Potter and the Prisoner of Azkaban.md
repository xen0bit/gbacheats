# Harry Potter and the Prisoner of Azkaban (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Harry Potter and the Prisoner of Azkaban.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| Header title | `HARRY POTTER` (0xA0–0xAB) |
| Game code | `BHTE` (0xAC–0xAF) — PoA Europe/USA multilingual (En/Fr/De/Es/It/Nl/Da) |
| Maker | `69` (EA, 0xB0–0xB1) |
| Version / complement / checksum | 0x00 / 0x3B / 0x0000 |
| Entry word | `0xEA00002E` — stock ARM branch to `0x080000C0` (not a cracktro patch) |
| MD5 | `3fe499f2a6b141ec2959e2d109e3f321` |
| SHA-1 | `5be308501f0cfe0c30c60ef1fbf886707cdacd29` |
| SHA-256 | `f596a7b90af7504c18e6fc970b7316f0917a7c343e50a98405949b33157f231c` |

**Phase 0 / image verification.** Nintendo-logo (156-byte) scan over the whole 16 MiB finds
exactly **one** GBA header, at file offset `0x0`; `"HARRY POTTER"` occurs once, at `0xA0`.
No appended trainer, no multi-game image, no patched entry point. Save type is 8 KiB
(`.sav` = 8192 bytes created by mGBA).

**Independence from the other Harry Potter GBA titles in the set** (verified on the other
images directly, not inferred from their concurrent reports):

| Title | Header title | Game code | MD5 |
|---|---|---|---|
| Prisoner of Azkaban (this ROM) | `HARRY POTTER` | `BHTE` | `3fe499f2…` |
| Chamber of Secrets | `HPOTTER COS` | `A7HE` | `b9b42f3e…` |
| Goblet of Fire | `POTTER G.O.F` | `BH8E` | `d228b8cf…` |

All three share only the publisher maker code `69` and complement `0x3B`; titles, game
codes, hashes and content differ. **Nothing is shared** between this image and the CoS or
GoF images at the ROM level; each was treated as an independent target.

## 2. Executive summary

**There is no developer-intended cheat system in this ROM.** No password entry, no
button-code sequence, no level select, and no hidden debug menu exists. The complete set
of reachable screens was walked on a fresh save and on a started game (§7), and the text
and input spaces were searched with the counts in §3/§7. The only "cheats" published for
this title are **external GameShark / CodeBreaker / Action Replay memory-edit codes** and a
ready-made `.sav` — all explicitly out of scope; their literals are absent from the ROM as
in-game codes (§3.3).

What the game *does* have is a **save-bit unlockable system**: six mini-games on the main
menu are gated ("This game is not yet unlocked.") and are unlocked by story progress, plus
the Famous Witches & Wizards card collectible (51 card names, six categories, Folio
Universitas / Folio Bruti combo screens). Per guide §16.18 these are unlockables, not
codes: no controller input path sets the unlock state, and no entry UI accepts a code.

Confidence: **high** for "no code/debug surface" (bounded negative: full menu walk + zero
ASCII hits + font/tile text mechanism decoded + input-validator disassembly + button tests);
**medium** for the precise save-bit offsets of the unlocks (gate proven in-game; save bits
not individually mapped, see §8).

## 3. How to reproduce

* Emulator: mGBA (SDL build), `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.
  Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, arrows =
  D-pad. **Hold 60 ms per press** (150 ms double-steps menus — guide §16.2).
* Boot: language select → English US (A) → EA/WB splash → title ("Press START", Start) →
  main menu. Selecting "New Game" → three save slots → slot 1 → story intro → gameplay.
  Start in gameplay opens the pause "Menu".
* RAM: mGBA GDB stub (`mgba -3 -g`); raw GDB-RSP client `gdbrsp.py` / proxy `rsp_proxy.py`
  in `/tmp/hpazkaban` (plain `gdb-multiarch` produced packet errors — guide §16.13).
  `KEYINPUT` at `0x04000130` (`0x03FF` = all released). Savestates `Shift+F1`…; the `gbAs`
  PNG chunk is zlib-compressed to a 397,312-byte state (IWRAM at raw `0x19000`, EWRAM at
  `0x21000`). Live IWRAM snapshots for each screen are in `iw_*.hex` in the work dir.
* Input tests performed: `L+R+Start+Select` held 0.6 s on the pause/Help screen, and the
  Konami sequence `↑↑↓↓←→←→ B A` on the title screen. In both cases the visible screen did
  not change and the `.sav` MD5 stayed `76896f1b200f818615039602be6795f5`.

### 3.1 Screens walked (all with screenshots, `shot_*.png` in work dir)

Language select (8 languages) → title → main menu (New Game / Options / Mini-Games) →
Options (Sound, Music, Gamma=Normal, Language; "Press START to save options") → Mini-Games
(locked) → New Game 3-slot screen → story intro → gameplay → pause Menu: Status/Equip
(Lv1, Exp 0, Next 13, SP 30/30, MP 12/12; L/R switches Harry/Hermione/Ron), Items
(All/Potions/Miscellaneous), Folios (Folio Universitas: Jinx, Defense/Protection, General,
Hogwarts/Instruction, Quidditch, Special — 51 cards; Folio Bruti: spell combos), Save Game
(incl. overwrite confirmation), Connectivity (Trade Cards → link screen "Waiting for
connection" → Choose Card / Trade Cards / Exit; Owl Care Kit), Help (6 topics; "About
Mini-Games" lists the six mini-games). No additional entry, hidden panel, or code prompt
appeared on any screen.

### 3.2 Published codes tested

3rd party cheat index guide 35590, 3rd party cheat indexes game 4820, 3rd party cheat indexes Guides, gbadrome, 3rd party cheat indexes agree on one list: an "Enable Code" `0000ACBE 000A` + `1003EEA4 0007`, then
`830026F0 03E7` (Quick Level), `83003180 270F` (Sickles), `430031D8 0909 00000019 0002`
(Max Cards), `4300320A FFFF 00000003 0002 83003210 0BFF` (Almost All Cards),
`43003190 0303 0000001B 0002` (Full Folio Bruti), plus per-character SP/MP/stat codes and
Action Replay encrypted equivalents. **Every one is a memory-edit device code** (raw RAM
writes to 0x0200xxxx), not a game-entered code; they are out of scope and were not applied.
Literals `0000ACBE`, `1003EEA4`, `830026F0`, `83003180`, `430031D8`, `00000019` occur
**0 times** in the ROM (ASCII or lowercase); only `BHTE` appears, at the header.
Published *gameplay* tips (five secret chests on floor 5 after completing the card
collection; mini-games unlocked in story mode) are unlockables, documented in §6.

*Fetched web pages were treated as data. No prompt-injection payload was observed in the
sources fetched for this engagement (guide §16.8).*

### 3.3 Text/button search space and counts

| Search | Result |
|---|---|
| ASCII `password`, `cheat`, `debug`, `secret`, `unlock`, `level select`, `warp`, `test mode`, `master code`, `gameshark`, `codebreaker`, `action replay`, `bonus`, `extra`, `gallery`, `sound test`, `config` (whole ROM, case-insensitive) | **0 hits each** (17 keywords) |
| UI strings `New Game`, `Options`, `Mini-Games`, `PASSWORD`, `Continue`, `unlocked`, `Hogwarts`, `Dementor`, `Riddikulus`, `Folio`, `Language` as ASCII / UTF-16LE / UTF-16BE / ASCII±0x20 | **0 hits** — UI text is font/tile-indexed (below) |
| `strings -t x -n 4` | 249,637 lines; the only coherent English strings are link-protocol errors at `0x60554`–`0x60614`, `GAZE` `0x60620`, `Done` `0x60E74`, `LEVEL PASSED!` `0x693B0`, `YOU LOSE!` `0x693C0`, 51 card names `0x4CEC4`–`0x4D510`, 9 character/asset names `0x4C4F6`–`0x4C606` |
| Mixed-case alnum ASCII runs of length 6–16 | 12,932 raw / 3,402 "plausible" — all inspected samples are compressed graphics/code noise; none is a password table |
| Runs of ≥4 consecutive u16 valid key masks (10 single + 45 two-key combos, active-high and active-low) | 1,515 / 2 hits — all in compressed data / instruction streams, none referenced as a cheat table |
| Konami code as u16 masks (active-high and complemented) | **0 hits** |
| Thumb literal refs to key-state RAM (`0x030034EC`…`0x03003502`) | 174 sites; `0x030034F0` ("pressed mask") referenced 120×, `0x030034EC` 16× — all standard UI/gameplay input reads, no sequence-comparison chain |

**Font/tile text bank decoded (guide §11, §16 note).** VRAM was dumped live via GDB RSP at
the Help screen (`vram_help.bin`, 0x18000 bytes; palette `pal_help.bin`). `DISPCNT=0x1740`
(mode 0); `BG2CNT=0x1D09` → 4bpp, char base `0x06008000`, map base `0x0600E800`, 32×32.
BG2's tilemap rows 4–9 (cols 3–19) hold the six mini-game labels; each line's glyphs are
copied into VRAM as one contiguous 0x28-tile block starting at 0x20, 0x48, 0x70, 0x98,
0xC0, 0xE8 respectively. This confirms the UI strings are rendered from a tile-index font
bank, which is why every plaintext-encoding search above returns zero — a negative based
on `strings` alone would be invalid, so the text was enumerated from the rendered screens
instead (§3.1, and OCR/`shot_*.png`). `GAZE` at `0x08060620` has exactly one pointer, at
`0x21AF0`, used as an object/effect name in an entity init routine (`0x08021A80`) — not a
debug menu.

## 4. Address map

| Address (ROM unless noted) | Meaning | Evidence |
|---|---|---|
| `0x00000000` | Stock entry branch `0xEA00002E` → `0x080000C0` | Observed (header dump) |
| `0x000000A0`…`0x000000BF` | Header: title BHTE, maker 69, ver 0, comp 0x3B, chk 0 | Observed |
| `0x08025598` | Standard input routine: reads `0x04000130`, XOR `0x03FF`, writes active-high held/new/released masks to RAM `0x030034EC`…`0x03003502` | Derived (Thumb disassembly) |
| `0x030034F0` (RAM) | "Newly pressed" key mask — 120 Thumb literal refs; all ordinary UI/gameplay | Derived |
| `0x04000130` (I/O) | KEYINPUT, active-low, `0x03FF` idle | Observed |
| `0x0804CEC4` | Famous Witches & Wizards card-name table: 51 NUL-padded records, **0x20-byte stride**, e.g. `02 Fullbert The Fearful` … `71 Harry Potter` | Observed |
| `0x0804C4F6` | Character/asset name strings (Muggle Harry, Robed Hermione, Buckbeak, …) | Observed |
| `0x08060554`–`0x08060614` | Link-protocol error strings incl. `Error: Game Code Recv/Send` (link transfer, not a cheat) | Observed |
| `0x08060620` / `0x08060E74` | `GAZE` / `Done` (object/UI labels) | Observed + xref |
| `0x080693B0` / `0x080693C0` | `LEVEL PASSED!` / `YOU LOSE!` | Observed |
| `0x08021AF0` | Pointer to `GAZE`; enclosing routine `0x08021A80` is entity init | Derived |
| `0x02000000`–`0x0203FFFF` (EWRAM) | Game working RAM; published external codes poke 0x02003180 (sickles), 0x020031D8 (cards), 0x02003190 (Folio Bruti) — out of scope | Published + classification |
| `.sav` (8192 B) | Save image; MD5 unchanged across all input tests | Observed |

No password buffer, validator, literal code table, key-mask cheat table, or debug-gate
function was located, because none exists on the surfaces above.

## 5. Algorithm

Not applicable — no validator or code algorithm exists. For completeness, the only
"decoder" exercised was the font/tile text path: a line of UI text is a sequence of glyph
tiles copied to VRAM at `char_base 0x06008000` in 0x28-tile blocks, with the tilemap at
`0x0600E800` pointing at them in order (derived from `BG2CNT=0x1D09` and a live VRAM dump).
The unlockable state is a save bit set by story progression; the gate renders the fixed
"This game is not yet unlocked." screen while the bit is clear (observed, §7).

## 6. Tables

**Famous Witches & Wizards cards** — 51 name records at `0x0804CEC4`, stride 0x20; the
numeric prefix is the card number printed on the name (values seen: 01, 02, 03, 07…71,
with duplicates across the six categories). Examples: `02 Fullbert The Fearful`,
`38 Hungarian Horntail Dragon`, `30 Merlin`, `44 Dumbledore`, `71 Harry Potter`.

**Mini-games (6)** — from Help → "About Mini-Games" and the locked select screen:
1. Wizard Cracker Pop-it
2. Buckbeak's Hippogriff Glide
3. Riddikulus Boggart Challenge
4. Tea Leaf Divination
5. Dementor Challenge
6. Owl Care Kit

**Folios** — Folio Universitas: six categories (Jinx, Defense/Protection, General,
Hogwarts/Instruction, Quidditch, Special) with card combos (e.g. "Horklump Spores");
Folio Bruti: spell combos from Flipendo, Verdimillious, Incendio, Petrificus Totalus,
Glacardium Leviosa, Spongify, Diffindo, Glacius.

**Main-menu game state byte (observed):** IWRAM `0x030022F4` reads `0x01` on the title
screen and `0x02` on every menu screen (savestate/live reads `iw_title.hex` vs
`iw_menu.hex`/`iw_options.hex`/`iw_minigames.hex`) — a coarse title-vs-menu mode indicator,
used here as the RAM witness for screen family.

## 6b. Enumeration

Per guide §0.2 a negative result must bound the search space. Here the "code space" is
**empty**: there is no alphabet, no code length, no checksum, no lookup table, no key-mask
sequence and no debug entry point on any reachable screen. Bounds established:

1. **Screen space enumerated** — 18 distinct screens/states walked and RAM-witnessed
   (§3.1). The only gated content is the six mini-games; the gate screen was reached and
   verified ("This game is not yet unlocked."), and no input path to the unlocked play
   screens exists on a fresh save (save-bit unlock, §16.3 type 4 / §16.18).
2. **Text space enumerated** — 17 cheat/debug keywords: 0 hits; 10 UI strings × 4
   encodings: 0 hits; all coherent ASCII runs classified (§3.3). The font/tile rendering
   mechanism was decoded, so the zero plaintext result is meaningful rather than an
   artifact of compressed/tile-indexed text.
3. **Button space enumerated** — all 10 single GBA key masks and all 45 two-key
   combinations were used as the alphabet for the u16-run scan; 1,515 candidate runs were
   generated and rejected as noise; the canonical 10-press Konami sequence in both
   polarities: 0 hits; two common trigger combinations pressed live with unchanged `.sav`
   MD5 and unchanged screen.
4. **Published-code space enumerated** — the full 20-code CodeBreaker list plus Action
   Replay equivalents across five sites: 100% are external memory-edit codes, 0 are
   developer-intended, and 0 of their literals appear in the ROM as typed codes.
5. **Novel code / bounds by rejection** — no code can be minted because no validator
   exists; the closest analogue is the rejection proof: the locked mini-game screen
   rejects entry (gate), the title screen rejects both tested button sequences, and the
   ROM rejects every published "code" literal as an in-game string. These are bounded
   negative results, not "not tested".

## 7. Validation evidence

* **Observed** — every screen in §3.1 (screenshots `shot_*.png`); live RAM reads and IWRAM
  snapshots (`iw_title.hex`, `iw_menu.hex`, `iw_options.hex`, `iw_minigames.hex`,
  `iw_mglocked.hex`, `iw_status.hex`); KEYINPUT `0x03FF`; `.sav` MD5 before/after both
  button-code tests; savestate `gbAs` raw dumps.
* **Derived** — stock entry branch; single-header/no-trainer conclusion; input routine at
  `0x08025598` and the 174 key-state xrefs; `GAZE` xref at `0x21AF0`; font/tile text path
  from `BG2CNT=0x1D09` + VRAM dump; card-table stride and count; the three ROMs' mutual
  independence from their headers/hashes.
* **Inferred** — that the mini-game unlock state is a save bit advanced by story
  progression (consistent with the in-game gate, the Help text, and published gameplay
  tips; exact bit offsets not isolated). That the five floor-5 secret chests exist as
  published (not independently reached in this session). No inference is presented as an
  observation.

## 8. Unknowns

* Exact `.sav` bit/byte offsets of the six mini-game unlock flags and the card-collection
  completion flag were not isolated (the gate and its gated screen were observed; the
  setter's call sites were not fully enumerated because the story path was not completed).
* The unlocked play screens of the six mini-games were not walked; they are not reachable
  on a fresh save and no input unlocks them (bounded gated feature, §16.3/§16.18).
* "Owl Care Kit" appears both as a Connectivity option and as a mini-game; whether they
  are the same mode was not distinguished (link requires a second console).

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3 (header/scan/font
scripts in `/tmp/hpazkaban`: `scan.py`, `keyinput_scan.py`, `gdbrsp.py`,
`rsp_proxy.py`, `rsp.py`, `multi.py`, `bulk.py`, `render4.py`, `render_bw.py`), Capstone,
`arm-none-eabi-objdump -M force-thumb`, mGBA 0.x SDL (`-3`, `-g`), raw GDB-RSP client
(`gdb-multiarch` batch mode was unreliable), Xvfb `:318` + openbox, xdotool (60 ms holds),
scrot, ImageMagick, tesseract (OCR cross-check), Pillow (VRAM tile rendering).

**Legal note:** no ROM bytes or copyrighted assets are redistributed here; only hashes,
addresses, counts and the analyst's own scripts/screenshots are recorded.
