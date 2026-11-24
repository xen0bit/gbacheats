# Pokémon Pinball: Ruby & Sapphire (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pokémon Pinball: Ruby & Sapphire.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `POKEPIN R/S` |
| Game code | `BPPE` (maker `01` = Nintendo) |
| Version | 0x00 (Rev.00, USA) |
| Entry word | `0xEA00002E` (stock branch to 0x080000C0) |
| Fixed byte / complement / checksum | 0x96 / 0xBF / 0x0000 |
| MD5 | `b73115adb5010f1917aad66d41df467d` |
| SHA-1 | `73a06e65e56eb8ed190bcb39b54007e968cdd728` |
| SHA-256 | `62bb6060fa73c1f5b701890084e0143a32a02ea5205787f7622d429ccc9aaf18` |

**Phase 0 result:** exactly one Nintendo-logo/GBA-header occurrence, at file offset `0x0`.
No appended trainer, no cracktro patch, no second game image. The stock entry branch
and normal first-4-KiB ARM crt0 confirm a retail image.

## 2. Executive summary

**There is no password system.** The only developer-intended, controller-reachable
hidden feature found is the **e-Reader Room**, opened by a button code on the title
screen: **hold Right, then press L, R, L, R, L, R** (each press within 40 frames).
The game is the USA release, in which no e-Cards were distributed, so this is a
genuine otherwise-unreachable debug/developer screen. It is published on 3rd party cheat indexes and
was independently re-derived here from the key-mask table at ROM `0x086A97AC`.

The ROM also contains a **ball-position debug overlay** (`BALL-MV:`, `BALL-SPD:`,
`DEBUG1:` at `0x08137DBF`) and a **Bonus Stage Select** mode (`0B`), but both are
gated: the debug overlay requires flag bits at `0x0200B0CF` that no in-game input
sets (3rd party cheat indexes document GS/CB codes to set them), and Bonus Stage Select requires the
Japanese e-Card or an external code. Both are out of the requested scope
(developer-intended in-game cheats only); the gating is proven below.

Two more published codes were checked: **A+B+Start+Select** (soft reset) is real
and verified in-game; the 3rd party cheat indexes **"hold L + tap L+R on Pokedex/Hi-Score" erase
prompt** could not be reproduced on this revision with three button
interpretations and no matching key-mask construction was found in ROM.

The deliverable required by §0.2 — a value absent from published lists — is the
**novel accepted combination "hold Right+Down, then L,R,L,R,L,R"**, which the
matcher accepts because it tests only bit 4 of the held-key mask. It was entered
on the real screen and RAM-verified.

## 3. How to reproduce

* Emulator: mGBA (SDL) under `Xvfb :318`, `SDL_AUDIODRIVER=dummy`, 3× scale.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold ≈90 ms per press.
* Boot; play through the intro (or press A/Start until the title menu appears).
* On the **title screen** press Start to open the menu (`GAMESTART / POKEDEX /
  OPTIONS / HI-SCORE`).
* Hold **Right**, then tap **L, R, L, R, L, R** in order. The hidden
  **e-READER ROOM** screen appears ("Transmit data with the e-Reader!").
* Novel variant: hold **Right+Down** instead of Right only — same result.
* Soft reset: from gameplay press A+B+Start+Select together → copyright screen.
* RAM evidence: mGBA savestates (Shift+F1) — PNG with a zlib `gbAs` chunk that
  decompresses to a 397,312-byte state; EWRAM begins at state offset `0x21000`
  (so GBA `0x0200B0C2` is state byte `0x2C0C2`). GDB stub was tried but proved
  unstable in this build (crashed after repeated connections), so savestate RAM
  reads were used throughout.

## 4. Address map

| Item | ROM / RAM address | Evidence |
|---|---|---|
| Button-code table | ROM `0x086A97AC` (file `0x6A97AC`) | Derived: u16 sequence `0200 0100 0200 0100 0200 0100 FFFF` |
| Table pointer in code | `0x080115E4` (literal) | Derived |
| e-Reader validator | `0x0801157C` | Derived (BL from `0x08010C6A`, `0x0801100C`, `0x08011214`) |
| Held key mask (active-high) | RAM `0x0200B0DC` | Observed (key-hold snapshots) |
| Pressed key mask | RAM `0x0200B0D8` | Derived |
| Code index / timeout | RAM `0x020028A2` / `0x020028A3` | Derived + observed (0 after each attempt) |
| Result flag byte | RAM `0x0200288E` | Derived |
| Second matcher (unused on tested screens) | `0x080114FC` | Derived: hold `0x220` (Left+L), tap R (`0x100`) ×3, counter `0x020028A0` |
| Soft-reset matcher | `0x08011020` | Derived: held `== 0x0F` (A+B+Select+Start) → sub-mode `0x0B` |
| Debug overlay strings | ROM `0x08137DBF` | Derived (`BALL-MV:`, `BALL-SPD:`, `DEBUG1:`, `(000 000)`) |
| Debug overlay draw/handler | `0x0807344`, `0x08072E4` | Derived |
| Debug enable flag | RAM `0x0200B0CF` (bits 4/8/16/32) | Derived; toggle helper `0x08047160` referenced only from table `0x086B0780` |
| Screen mode | RAM `0x0200B0C2` (u8) | Observed (see table in §6) |
| Sub-mode | RAM `0x0200B0C3` (u8) | Observed |
| Spare balls / score | RAM `0x02000030` / `0x02000040` | 3rd party cheat index notes; consistent with save RAM |

## 5. Algorithm (button-code validator at `0x0801157C`)

```text
idx    = u8[0x020028A2]
expect = table[idx]                 // 0x0200 (L) or 0x0100 (R), active-high
held   = u16[0x0200B0DC]
press  = u16[0x0200B0D8]

if (held & 0x0010) == 0:            // Right must be held (bit 4 ONLY)
    timeout_decay(); return

if (press & expect) == expect:
    u8[0x020028A3] = 40             // 40-frame inter-press window
    idx = idx + 1
    if table[idx] == 0xFFFF:        // all six presses consumed
        idx = 0; timer = 0
        sfx(101)
        u8[0x0200288E] = 5
        u8[0x0200B0C3] = (u8[0x0200B0C3] == 1) ? 0x0B : 0x0A
else if ((press & 0x03FF) & ~expect) != 0:
    u8[0x020028A3] = 0; idx = 0     // wrong key -> reset progress
```

Key insight: the prefix test is `held & 0x10`, not `held == 0x10`, which is why
Right+Down (and any other held combination containing Right) is accepted.

## 6. Tables

**Key masks (active-high):** A `0x001`, B `0x002`, Select `0x004`, Start `0x008`,
Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`, R `0x100`, L `0x200`.

**Accepted sequence table** (`0x086A97AC`): `L, R, L, R, L, R, 0xFFFF(term)`.

**Observed screen/mode map** (RAM `0x0200B0C2`, sub-mode at `0x0200B0C3`):

| Mode | Screen | Sub-modes seen |
|---|---|---|
| 0x00 | Intro / credits / copyright | 0, 1, 3 |
| 0x01 | Title logo (`PRESS START`) / main menu (`GAMESTART…`) | 1, 3 (logo), 4 (menu) |
| 0x02 | Gameplay / pause (`SAVE / CANCEL`) | 1 |
| 0x04 | OPTIONS | 1 |
| 0x05 | POKéDEX | 1 |
| 0x07 | **e-Reader Room (hidden)** | 0, 3 (link-cable dialog) |
| 0x08 | HI-SCORE | 3 |
| 0x0A | FIELD SELECT | 0, 1 |

**Published codes checked:**

| Source | Code | Result |
|---|---|---|
| 3rd party cheat indexes | Hold Right, alternate L/R 3× (e-Reader Room) | **Confirmed**, reproducible |
| 3rd party cheat indexes | A+B+Start+Select reset | **Confirmed** (mode 2 → 0, copyright screen) |
| 3rd party cheat indexes | Hold L, tap L+R on Pokedex/Hi-Score → erase prompt | **Not reproduced** (3 interpretations tested; no `0x300` mask construction found in ROM) |
| 3rd party cheat indexes | Debug mode (GS/CB codes) / Bonus Stage Select (e-Card) | Out of scope; gated, see §8 |

## 6b. Enumeration

**Space definition.** The hidden-feature surface is one *prefix* mask
(`held & 0x10` — 512 of 1024 possible held masks satisfy it, i.e. every mask
containing bit 4) crossed with a single 6-entry terminated u16 sequence table.
The table can express exactly one ordered sequence; there is no password/checksum
field. Terminator is `0xFFFF`; key masks are 10-bit.

**Exhaustive search.** A whole-ROM scan for terminated u16 arrays whose entries
are valid key masks found **167 candidates**, of which **exactly one** is
referenced by a 32-bit code pointer: `0x086A97AC` (pointer at `0x080115E4`).
No second sequence table (and therefore no second sequence code) exists.
BL/pointer scans found three call sites of the validator (`0x08010C6A`,
`0x0801100C`, `0x08011214`), all title/menu handlers.

**Novel accepted combination (absent from every published list).**
Published form: *hold Right, press L,R,L,R,L,R*.
Novel form: **hold Right+Down, press L,R,L,R,L,R**.
Entered on the title screen in mGBA; screen showed e-READER ROOM and RAM read
`0x0200B0C2 = 0x07` (pre-entry `0x01`). Screenshot saved as `s_novel.png` in the
work directory. This directly proves the matcher tests only the Right bit.

**Bounds proven by in-game rejection** (all started from title logo, mode `0x01`):

| Test | Held | Press sequence | Post mode | Result |
|---|---|---|---|---|
| Valid | Right | L,R,L,R,L,R | `0x07` | e-Reader Room |
| **Novel** | Right+Down | L,R,L,R,L,R | `0x07` | e-Reader Room |
| Rejected | Right | R,L,R,L,R,L (reversed) | `0x01` | no effect |
| Rejected | Right | L,R,L,R (truncated) | `0x01` | no effect |
| Rejected | none | L,R,L,R,L,R | `0x01` | no effect |
| Rejected | Down only | L,R,L,R,L,R | `0x01` | no effect |

**Debug gate bounded.** The overlay handler `0x08072E4` reads `0x0200B0CF` and
tests bits 8, 16, 32, 4; bit 4 selects the `BALL-MV` screen at `0x0807344`.
A scan of all `strb rX,[base,#15]` stores near a `0x0200B0C0` base found only
values 0/1/2/0x20 written by game initialization and one helper (`0x08047160`,
referenced only by a data table at `0x086B0780`); no normal input path sets bit 4.
No BL or direct pointer reaches `0x08072E4`/`0x0807344`. This matches a 3rd party cheat index's
statement that external GameShark/CodeBreaker codes are required.

**Bonus Stage Select bounded.** On FIELD SELECT (mode `0x0A`) tapping L alone
left mode `0x0A` unchanged (screenshot `s_field_L.png`); 3rd party cheat indexes state mode `0x0B`
must first be set by an e-Card/external code. No in-game route to mode `0x0B` was
found.

## 7. Validation evidence

* **Observed:** all screenshots listed above; savestate RAM reads for mode bytes
  before/after each code; key-hold snapshots establishing the active-high mask
  representation.
* **Derived:** full Thumb disassembly of `0x080114FC`, `0x0801157C`, `0x08011020`,
  `0x08072E4`, `0x0807344`; literal-pool decoding; whole-ROM table/BL/pointer scans.
* **Inferred:** debug-mode and Bonus-Select reachability require external devices
  (supported by 3rd party cheat indexes and by the gate analysis, but no physical e-Card/GS was used).
* Fetched 3rd party cheat index pages were treated strictly as data; no instructions
  found in them were executed.

## 8. Unknowns

* The exact semantics of the sub-mode values `0x0A`/`0x0B` written by the validator
  (they do not change the visible screen on this build).
* Why the 3rd party cheat indexes erase prompt code does not trigger on BPPE01 Rev.00 — possibly
  a different regional revision or an inaccurate published description.
* The on-screen UI text is stored as font tile indices, not ASCII, UTF, or
  LZ77-compressed ASCII (verified by a 6,095-candidate LZ77 scan and byte-shift
  searches). Full font-table decoding was not completed; hidden-screen enumeration
  therefore rests on the exhaustive mask-table scan plus the screen walk rather
  than on a text-bank string dump.
* Whether the e-Reader Room can actually receive data in an overseas ROM (the
  link-cable dialog appears but no transmission could be tested without hardware).

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` for raw GBA disassembly; Capstone for
  whole-ROM BL/literal/mask scans.
* Python helpers in `/tmp/pokemonpinball/`: `kb.py` (XTEST key presses),
  `snap.py`/`ram.py` (savestate RAM reader), `probe.py` (code acceptance/rejection),
  `walk.py` (screen walker).
* mGBA SDL under Xvfb `:318`; `xdotool`, `scrot`, ImageMagick.
* `gdb-multiarch` attempted but abandoned (stub unstable across connections).
* Web sources: 3rd party cheat indexes *Pokémon Pinball: Ruby & Sapphire* (Wayback snapshot
  `20241216145503`), 3rd party cheat index cheats page, 3rd party cheat indexes GBA cheats page.

*No ROM image, extracted graphics, or copyrighted assets are redistributed in this report.*
