# Sonic Pinball Party (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Scope: in-game / developer-intended cheats (passwords, button codes, hidden/debug
menus, unlockables). GameShark/CodeBreaker memory-write codes are **out of scope**
and are recorded only as web-recon context.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Sonic Pinball Party.gba` (8,388,608 bytes = 0x800000) |
| Header title | `SONICPINBALL` (0xA0–0xAB) |
| Game code | `A3VE` (0xAC–0xAF), maker `8P` (Sega), version `0x00` |
| `file(1)` | `Game Boy Advance ROM image: "SONICPINBALL" (A3VE8P, Rev.00)` |
| Entry word | `0xEA00002E` → `b 0x080000C0` (stock crt0; **not** a patched/scene entry) |
| Fixed byte 0xB2 | `0x96`; header checksum word `0x003C`; no trainer/patch prefix |
| MD5 | `de40b1738a7c670ca28ddf44bb908df6` |
| SHA-1 | `92b5c19cb4dee8fdfc15a8abdc699822d5373042` |
| SHA-256 | `5690eb0a58ac24616fd6747a8aedddc7777f28d6f3579cb4428ea8fa5d30208b` |

**Embedded-header scan (Phase 0).** The 156-byte Nintendo logo
(`24 ff ae 51 69 9a a2 21 3d 84 82 0a …`) occurs at file offsets
`0x4`, `0x6EEC10`, `0x6F23C8`, `0x719AAC`, `0x739174`. Only the hit at
`0x4` is a real GBA header (title `SONICPINBALL`, code `A3VE8P`). The other
four sit in asset data: the candidate headers at `0x6EEC0C`, `0x6F23C4`,
`0x719AA8`, `0x739170` carry an all-zero title / all-zero game code, so this
is **not** a multiboot/multi-game pack. No appended trainer was found; the
first 0x200 bytes are ordinary ARM crt0 (stack/IRQ setup, fast-copy loop).

## 2. Executive summary

**There is no in-game password system, no button-activated cheat code, and no
reachable hidden/debug menu in this exact ROM.** The retail-facing
developer-intended features are:

1. **Sound Test** (Options → third entry) — BGM tracks **001–050** and SE
   tracks, with wraparound at both ends (observed by entering 001…050 and
   pressing Left from 001). It is a track player, not a code-entry surface.
2. **Three story-completion unlockables** published by 3rd party cheat indexes — Bingo
   mini-game (beat Amy), Slots mini-game (beat Tails), Samba de Amigo table
   (beat Knuckles) — plus the "SuperSonic Stage / true last stage" secret
   (enter Ring Mode in every zone). These are gameplay/save-state unlocks,
   not input codes.
3. **Button Config** (Options → first entry) — a normal remapping screen.
4. **Chao Navi / Tiny Chao Garden** and the standard STORY/ARCADE/TUTORIAL/
   PARTY mode carousel.

A floating development text table at `0x080ADE1C` lists
`SONIC / NIGHTS / SAMBA / ROULETTE / BINGO / SLOT / ABORT / NAVI / LANG /
WRITE / STORY / DEFAULT` and has a renderer at `0x08028C44`. Its dispatcher
`0x08028DD8` has **zero** BL, branch, and 32-bit-pointer references anywhere
in the 8 MiB image (§5.4a/§16.21): it is dead development text, not an
accessible debug menu.

Every published "code" located via web recon is either (a) a GameShark /
CodeBreaker RAM write (e.g. `82035740 0017` "ball always saved" → EWRAM
`0x02035740`; `83002988 FFFF` "quick score") and therefore out of scope, or
(b) a cheat for a *different* Sonic SKU (the widely quoted character-select
level-select sequence belongs to **Sonic Advance** in the Combo Pack, and
`01,09,09,02,01,01,02,04` is the Sonic 2 debug code).

## 3. How to reproduce

```
cd /tmp/sonicpinball
cp "roms/Sonic Pinball Party/Sonic Pinball Party.gba" game.gba
Xvfb :319 -screen 0 1024x768x24 &          # PID recorded, own display only
DISPLAY=:319 openbox &
DISPLAY=:319 SDL_AUDIODRIVER=dummy mgba -3 game.gba &
W=$(DISPLAY=:319 xdotool search --name mGBA | head -1)
DISPLAY=:319 xdotool windowfocus "$W"
```

mGBA 0.10.5 SDL keymap used: `A=x`, `B=z`, `L=a`, `R=s`,
`Start=Return`, `Select=BackSpace`, D-pad = arrow keys. Hold each key
60–150 ms (45 ms double-steps some menus). `Shift+F1…F9` saves a state;
`F1…F9` loads it. The GBA viewport was captured with
`scrot` + `convert -crop 720x480+152+144 +repage`.

Menu path (observed): language select → title (`PRESS START`) → five-way
carousel **OPTIONS → ARCADE → STORY → TUTORIAL → PARTY** → OPTIONS contains
**Button Config / Language / Sound Test / Chao Navi**. Loading ARCADE starts
the Sonic table; STORY/TUTORIAL show story text/cutscenes; PARTY shows the
Hot Potato / paddle / air-hockey mini-game select.

RAM evidence was collected with the §16.13 savestate method: decompress the
PNG `gbAs` chunk with `zlib` (397,312-byte state), whose layout is
VRAM `+0x1000`, IWRAM `+0x19000`, EWRAM `+0x21000`. Example observed reads:

| Anchor state | Screen | RAM read |
|---|---|---|
| `game.ss1` | OPTIONS list | `0x03000E00 = 0x0001` |
| `game.ss2` | Sound Test | `0x03000E00 = 0x0001` |
| `game.ss3/4/5` | mode select / PARTY / mini-game select | `0x03000E00 = 0x0001` |
| `game.ss9` | ARCADE gameplay (Sonic table) | `0x03000E00 = 0x0003` |
| input engine | held/pressed key masks | `0x03000514` (held), `0x03000516` (pressed), active-high |

Byte-level diffs between consecutive screen states (EWRAM / IWRAM / VRAM):
OPTIONS→Sound Test 40,454 / 3,612 / 74,955; Sound Test→mode select
4,093 / 734 / 1,592; mode select→PARTY 3,218 / 308 / 7,079; PARTY→mini-game
select 4,227 / 576 / 1,542; OPTIONS→ARCADE gameplay 4,268 / 1,275 / 13,386.
These are measured RAM changes, not visual inference.

## 4. Address map

| Address (ROM/file) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | stock crt0 entry (`b 0x080000C0`) | Derived (header bytes) |
| `0x08002C9C` | joypad reader: `held = ~KEYINPUT & 0x3FF`; writes `0x03000514`, pressed delta `0x03000516` | Derived (Thumb disasm) |
| `0x0802C44` | renders the fixed 32-byte-stride text table at `0x080ADE1C` (10 rows × 30 chars, ASCII→font index `+0xE0`) | Derived |
| `0x0802DD8` | dispatcher for that text screen; **0 xrefs** | Derived (full-ROM BL/B/Bcond/u32 scan) |
| `0x080ADE1C` | development text table: `0 SONIC + / 0 NIGHTS + / 0 SAMBA + / 0 ROULETTE + / 0 BINGO + / 0 SLOT + / 0 ABORT + / 0 NAVI + / 0 LANG + / WRITE / STORY + / DEFAULT` | Derived (bytes + decoder) |
| `0x080ADF44` | adjacent Shift-JIS (`0x8140`-padded) text bank | Derived |
| `0x080CD9FC` | internal sound-effect/BGM names (`se_199`, `sng_…`, `SND_BGM_050` …) — 3rd party cheat index-confirmed | Derived + web |
| `0x080CCEF8` … | Samba-table word list `RIO/WAMBA/CHUMBA/BONGO/BINGO/LINDA/AMIGO/SAMBA` | Derived |
| `0x080CB78C` | SRAM magic `SONIC_PB`; referenced from `0x08048ED0`, `0x0804916C`, `0x0804962C` (save verify/CRC) | Derived |
| `0x066C3C`, `0x067080`, `0x0AA33C`, `0x0AB29A` | the only four ordered button-mask tables (Button Config display order / tutorial key-hints) | Derived |
| `0x03000E00`, `0x03000514`, `0x03000516` | game work sub-state, held keys, pressed keys | Observed (savestate reads) |
| SRAM `0x00/0x1000/0x2000` | three 0x1000-byte save slots, magic `SONIC_PB\x01/\x02/\x03`; high-score names at `+0x300` (`CHA/PIA/BON/CHU/ELL/NIG/TAI/KNU/SHA/ROU`) | Observed (`game.sav`) |

**File-offset ↔ ROM address:** `0x08000000 + file_offset` (no sub-image bases;
single header).

## 5. Algorithm

There is no password validator to reimplement. The relevant algorithms are:

* **Input** (`0x08002C9C`): `raw = halfword[0x04000130]`; `held = raw ^ 0x03FF`;
  `pressed = held & ~old_held`; store `held→0x03000514`, `pressed→0x03000516`.
  This is the only input front-end; the 85 literal references to `0x03000510`
  are per-screen consumers of these two words.
* **Sound Test index**: BGM is a 1-based counter over 50 entries
  (`SND_BGM_001 … SND_BGM_050`); Left from 001 wraps to 050, Right from 050
  wraps to 001 (observed transition 013→…→050→001→…→009 after 45 presses).
  SE uses the same pattern over `SND_SE_001 … SND_SE_199`.
* **Save slots**: 0x1000 bytes each; header magic + slot id + CRC; three copies.
  Unlock state is stored as bits in this record (§16.18 pattern), advanced only
  by story-mode progress — no input path writes those bits.

No checksum, substitution alphabet, key table, or code generator exists in
this image.

## 6. Tables

| Item | Value / layout |
|---|---|
| BGM indices | 1–50 (50 tracks, `SND_BGM_001`…`050`) |
| SE indices | 1–199 (`SND_SE_101`…`199` names present) |
| Top-level carousel | 5 entries: OPTIONS, ARCADE, STORY, TUTORIAL, PARTY |
| Options entries | 4: Button Config, Language, Sound Test, Chao Navi |
| Save slots | 3 × 0x1000 at SRAM `0x0000`, `0x1000`, `0x2000`; magic `SONIC_PB` |
| Button masks | A=0x001, B=0x002, Select=0x004, Start=0x008, R=0x010, L=0x020, Up=0x040, Down=0x080, Left=0x100, Right=0x200 (active-high) |
| Published in-game unlockables | Bingo mini-game, Slots mini-game, Samba de Amigo table, SuperSonic Stage — all gameplay-gated |

**Published-code verification.** Raw case-insensitive byte searches for
`password`, `cheat`, `secret`, `unlock`, `debug`, `code`, `level select` each
return **0** hits in all 8,388,608 bytes. The 3rd party cheat index pages (archived
2025-03-29), 3rd party cheat indexes "Hidden content" (oldid 306047), and 3rd party cheat indexes contain **no** in-game password or button code for this SKU:
3rd party cheat index lists only the three unlockables + SuperSonic secret; 3rd party cheat index
lists only CodeBreaker RAM writes; 3rd party cheat indexes document only internal sound names.
The widely copied "character select level select" sequence is for *Sonic
Advance* in the Combo Pack, and the "01,09,09,02,01,01,02,04" sound-test
sequence is the Sonic 2 debug code — both were rejected as wrong-SKU leads.

## 6b. Enumeration

This engagement is a **bounded negative** (guide §0.2 point 5, §16.3). The
whole plausibly-checkable space was enumerated; counts below are measured,
not estimates.

**A. Input surfaces enumerated (observed, mGBA on `:319`).** Reached and
captured: language select; title; the 5-entry mode carousel (all five
highlighted in turn); Options and all four of its sub-screens (Button Config
with its 8 rows, Language, Sound Test with BGM/SE/PLAY, Chao Navi); PARTY
mini-game select; STORY/TUTORIAL story text and cutscenes; ARCADE/Sonic table
gameplay with its bonus callouts. Savestates `game.ss1`–`game.ss9` and the
corresponding screenshots in `/tmp/sonicpinball/` preserve each
state; RAM diffs are tabulated in §3. No password-entry screen, no keyboard
alphabet, no code-confirmation prompt, and no debug menu item exists on any
of these screens.

**B. ASCII / literal-table space (derived).** 61,186 strings of length ≥4
were extracted. Keyword searches: 0 hits for each of the seven cheat-related
keywords. A regex sweep for 4–12 character NUL-terminated uppercase+digit
strings found **413** candidates; an equal-stride clustering pass (stride
4–32, ≥3 consecutive) found only **2** clusters, both in compressed asset
data (score-digit noise at `0x2CA5C2`, rhythmic notation at `0x2F1061`) —
**0 password tables**. The development text table at `0x080ADE1C` contains
12 menu-style strings and was fully decoded above; its dispatcher has
**0** BL, **0** branch, and **0** u32 pointer xrefs (including the Thumb
`addr|1` variant) in the whole ROM, so no input path reaches it.

**C. Button-code space (derived + dynamic).** A full-ROM u16 scan for runs of
single-button masks found **694** runs of length ≥4; after removing repeated
padding (`0x0001`, `0x0002`, … from graphics/audio data) only **4** ordered
tables remain (`0x066C3C`, `0x067080`, `0x0AA33C`, `0x0AB29A`), all Button
Config / tutorial key-hint tables. There is **no** progress-indexed key
sequence checker. Live probe: the undocumented 10-press sequence
`↑ ↑ ↓ ↓ ← → ← → B A` was entered on a live menu with a control savestate
taken immediately before; the resulting EWRAM/IWRAM deltas (5,792 / 1,651
bytes) are explainable by ordinary animation and state advancement, and no
new screen, flag, or menu appeared. No novel in-game code can be minted
because **no code system exists to mint into** — this is the §0.2 point-5
negative-result case, not an untested one.

**D. Unlockable set (observed + derived).** Enumerated from the published
lists and the save record: exactly 3 controller-input-independent unlock
conditions (Bingo, Slots, Samba de Amigo table) plus the Ring-Mode/SuperSonic
secret. Each is gated by story progress; the input front-end at `0x08002C9C`
feeds only per-screen UI handlers, and no code path accepts an externally
typed value. These are therefore unlockables in the §16.18 sense, not codes,
and no "unpublished code" can be generated for them.

**Novel-code requirement (§0.2):** not applicable — the searched space is
empty. A "code absent from published lists" would require a validator or a
code table; both were proven absent with the counts in B and C above. The
deliverable here is the bounded negative plus the complete feature inventory.

## 7. Validation evidence

* **Observed** — all screens in §6b-A; BGM 001→050 wraparound; the four
  ordered button-mask tables' bytes; savestate RAM reads and byte-diff
  counts; `game.sav` layout; stock entry word; 0 keyword hits.
* **Derived** — input front-end at `0x08002C9C` and its two RAM words;
  ASCII→font mapping in the renderer at `0x08028C44`; dead-code xref counts
  for `0x08028DD8`; save-slot geometry from the magic at `0x080CB78C`.
* **Inferred (labelled)** — that the unlock bits live in the save record is
  inferred from the three-slot `SONIC_PB` save format and the published
  unlock conditions; the exact bit offsets were not isolated because no
  story completion was performed. It is not used as a code claim.

## 8. Unknowns

* Exact SRAM bit offsets for the three story unlocks and the SuperSonic
  stage (inferred to be in the 0x1000-byte slot record; no setter call site
  isolated). This does not affect the cheat-code conclusion.
* Seven of the 50 BGM slots have no descriptive name in the internal name
  table; the Sound Test itself is functional and fully enumerated by index.
* The four embedded Nintendo-logo hits in the asset region were not
  decompressed individually; their headers are blank, so they are not
  playable sub-images.

## 9. Tooling

`mgba` 0.10.5 (`-3`, `-g` tried and retired for savestate reads), `Xvfb
:319`, `openbox`, `xdotool`, `scrot`, ImageMagick, `tesseract` (OCR used only
as a screen-label aid, never as proof), `gdb-multiarch` (input-word
verification), `strings`, `grep`, `xxd`, Python 3 (`capstone` not required),
`arm-none-eabi-objdump -M force-thumb`, and the two local helpers
`/tmp/sonicpinball/state.py` (zlib `gbAs` savestate RAM reader) and
`kb.py` (key/capture wrapper). No scripts were installed system-wide.

**Legal note:** no ROM data, graphics, music, or extracted game text is
redistributed here; only addresses, hashes, counts, and independently written
analysis are published.

**Cleanup:** all processes used by this analysis were terminated by their
recorded PIDs (`mgba`, `Xvfb`, `openbox` for display `:319`); no `pkill` was
used. The emulation copy and all generated `game.sav` / `game.ss1`–`.ss9`
files were kept in `/tmp/sonicpinball/`, not in the ROM folder; the ROM
folder contains only the original `.gba` and this report.
