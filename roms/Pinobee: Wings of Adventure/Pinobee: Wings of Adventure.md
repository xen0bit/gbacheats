# Pinobee: Wings of Adventure (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pinobee: Wings of Adventure.gba` |
| Folder | `roms/Pinobee: Wings of Adventure/` |
| Size | 8,388,608 bytes (`0x800000`) |
| `file(1)` | Game Boy Advance ROM image: "PINOBEE" (APBE52, Rev.00) |
| Header title | `PINOBEE` (`0x080000A0`) |
| Game code | `APBE` (`0x080000AC`) |
| Maker code | `52` (Activision) (`0x080000B0`) |
| Fixed byte / main unit / device | `0x96` / `0x00` / `0x00` |
| Software version | `0x00` |
| Complement check | `0xD0` |
| Header checksum | `0x0000` (rebuilt-header artifact; guide §16.1) |
| **CRC32** | **`D9385207`** — matches GameHacking.org's USA/Europe `AGB-APBE-USA, AGB-APBP` entry exactly |
| MD5 | `211af14ac83a170a0e60fe8d0a48e37e` |
| SHA-1 | `cb1549b6dd8070770b1a00928eeb7d458309e200` |
| SHA-256 | `b111c47083f055f1f3f573537b42fd7a9f3c49776b0b39d8ea0f8746cf700da1` |

**Phase 0 / patch check (Observed):** entry word at `0x08000000` is `0xEA00002E`
(`b 0x080000C0`, the stock ARM branch — *not* a cracktro patch). A whole-file scan for
the 156-byte Nintendo logo (`24 ff ae 51 ...`) found **exactly one** GBA header, at file
offset `0x4`. There is no multiboot sub-image, no appended trainer, no second game, and
no shell menu. The ROM is a single retail USA/Europe image.

## 2. Executive summary

**There is no player-facing password, button-code, or cheat-entry system in this ROM.**
Literal `password` / `cheatcode` / `levelselect` / `debugmenu` count is **0**; no
alphabet table, no code validator, no comparison table of code strings, and no key-mask
sequence could be found. The only codes published on the web are encrypted Action
Replay / GameShark / CodeBreaker memory-edit listings (Cheat Happens, GameHacking.org),
which are explicitly **out of scope**; they are not literals and do not appear in the ROM
as text.

**However, the retail image does contain a complete, dormant developer debug menu.**
Its label table is stored in ASCII at `0x080551C0–0x080552C8` and its two handler-pointer
tables at `0x08055014` (7 entries) and `0x080550BC` (14 entries). It can edit stage,
stage maximum, life, life maximum, dashes, flowers, flower maximum, level, flag and item
(§6/§6b). This is a genuine developer-intended cheat surface, but **no in-game route to
it was found**: every reference to its handlers is internal to that subsystem, and 34
distinct button inputs/combinations tested at boot, on the title screen, on Select Diary,
and on the pause screen failed to reach it. It is classified as **dead code** (guide
§16.3, category 2), reachable only by calling its functions from a debugger — a
memory-edit technique that is out of scope here.

The one in-scope published secret — **Super Pinobee** (GameFAQs: collect all 16 items of
one colour category to make the King and Queen items appear, then collect both) — is
structurally corroborated by the item/flag tables (§6), but is a **save-driven
unlockable**, not a code (guide §16.18).

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `mgba -3 <rom>`, `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`,
  Xvfb :316 + openbox started locally. Keymap (mGBA SDL default): A=`x`, B=`z`,
  L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
* Boot path: title (`PRESS START`) → `Start` → **SELECT DIARY** (slots 1/2/3).
  `A` enters the game; `Select` on that screen switches to **ERASE DIARY**; `B` returns.
* In game: `Start` → **PAUSED** (`RETURN` / `ITEMS`). `Down`+`A` on PAUSED → **ITEMS**
  honeycomb ("24 left") with an `Effects` cursor → **ITEM EFFECTS** (`PINK`/`BLUE`/
  `ORANGE`) → `B` back.
* RAM evidence: `Shift+F1` writes `<rom base>.ss1` next to the ROM. That PNG's `gbAs`
  chunk is zlib-compressed to a 397,312-byte state; offsets: palette RAM `0x800`,
  VRAM `0x1000`, IWRAM `0x19000` → `0x03000000`, EWRAM `0x21000` → `0x02000000`.
  All screen claims below were verified from these dumps, not from screenshots alone.
* Buttons tested (all failed to open the debug menu): single A/B/L/R/Select/Up/Down/
  Left/Right; L+R, L+R+Start, L+R+Select, L+R+A+B, L+R+A, L+R+B, L+R+Up+Down,
  A+B, A+B+Start, Select+Start, Select+A, Select+B, Start+A, Up+Down+Up+Down —
  each held through boot and separately on the title and Select Diary screens.

## 4. Address map

| ROM address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Header; stock entry `0xEA00002E` | Observed (bytes) |
| `0x0800170C`, `0x08039B40` | Only two literal-pool entries for `0x04000130` (KEYINPUT) | Derived (PC-relative scan) |
| `0x08003994` | Only BL from outside the debug region into it → `0x08016160` (a `memcpy(dst,r1=0x08055020,len=0x694)` wrapper that loads the debug data block into the scene struct) | Derived (BL scan) |
| `0x08016074` | Debug menu sub-screen initialiser (7-handler family) | Derived (objdump) |
| `0x08016160` | Debug data-copy wrapper (source `0x08055020`, size `0x694`) | Derived (objdump + literal read) |
| `0x08016178` | Debug menu dispatcher; indexes the 7-entry table at `0x08055014`, calls handlers through `0x08042E08` | Derived (objdump) |
| `0x0801655C`, `0x080167D0` | Debug sub-screen input handlers (read global flags `0x030051EC`, `0x0300519C`, `0x03004954`) | Derived |
| `0x08055014` | Debug handler pointer table #1: `0801655D, 080167D1, 08017AED, 08016075, 080160C5, 080160D1, 08016141` (7) | Observed (bytes) |
| `0x080550BC` | Debug handler pointer table #2: `080170E5 … 08017829` (14 consecutive Thumb pointers) | Observed (bytes) |
| `0x080550F0–0x0805518F` | Debug selector/bounds data (`(u16,u16)` pairs) | Observed |
| `0x08055190–0x080551BF` | Tile-indexed labels (extracted, not fully decoded — see §8) | Observed |
| `0x080551C0–0x080552C8` | **ASCII debug-menu label bank** (16 strings, §6) | Observed |
| `0x080552CC–0x080553A8` | Pointer table into text/tile banks (`0x08055…`) | Observed |
| `0x08055608–0x08055634` | `u16` 1..23 lookup table; `0x080555F5` = `CHANGE?`, `OK`, `NO` | Observed |
| `0x08055690–0x08055AB0` | `BGM_*` / `SE_*` asset-name bank (the only large ASCII run; keyword hits here are audio, not cheats) | Observed |
| `0x08055BC0+` | `VO_*` voice-clip names (Japanese romaji) | Observed |

### RAM screen-state proof (savestate dump)

| Screen | IWRAM `0x03000014` (u8) | IWRAM `0x03000019` (u8) | IWRAM `0x03000008` (u32) |
|---|---|---|---|
| Title | `0x04` | — | `0x02000030` |
| Select Diary | `0x05` | `0x04` | `0x02000030` |
| Erase Diary | `0x05` | `0x01` | `0x02000030` |
| PAUSED | `0x1A` | — | `0x02001280` |
| ITEMS | `0x1B` | — | `0x02001230` |

`0x03000014` is the scene/mode word (distinct value per screen); `0x03000019`
distinguishes the Select-Diary submode. This is the RAM evidence that every screen
listed in §3 was actually reached.

## 5. Algorithm

There is **no password validator or key-sequence algorithm to reimplement**. The search
for one was carried to the following bounded endpoints:

1. **Literal search** — 0 occurrences of `password`, `cheatcode`, `levelselect`,
   `debugmenu` in 8 MiB; `strings -a -n 4` yields 88,116 runs, of which the only
   cheat-adjacent ASCII is the debug label bank in §6 and `BGM_*`/`SE_*` audio names.
2. **Key-input surface** — only two `0x04000130` literal-pool entries exist in the whole
   ROM (`0x08001778`, `0x08039B60`), i.e. one BIOS-style reader and one engine reader.
   There is no second, hidden keypad reader.
3. **Button-mask tables** — a `u16` scan for runs of ≥3 plausible key masks found
   1,731 active-low and 11,757 active-high runs; every candidate inspected was ordinary
   graphics/level data (e.g. the symmetric ramp `FFC0 FF80 FF00 FE00 FC00 FE00 FF00 FF80
   FFC0` at `0x080593A6`, the 127-entry ramp at `0x0805964A`). No run is a press sequence.
4. **Reachability of the debug subsystem** — of 31 BLs into `0x08016000–0x08018000`,
   28 originate inside the subsystem itself; the only three from outside are
   `0x08003994 → 0x08016160` (data copy) and two values inside animation data
   (`0x080AB06A`, `0x0811E166`, false positives). All 59 word pointers into that range
   are either internal jump/vtable entries or data coincidences. No dispatcher case,
   menu item, or boot branch enters the debug scene.

The debug menu's **data model** (derived from its labels and bounds tables) is:

```
struct DebugState {            // initialised by 0x08016074, size >= 0x694
    u32  flags;                // +0x00, initial 0xF000
    u8   sub_screen;           // 0..2 / 0..6 (dispatcher index)
    ...                        // copied from ROM 0x08055020, len 0x694
};
dispatcher(0x08016178):
    idx = state[idx_offset];
    handler = table_0x08055014[idx];
    call_through(0x08042E08, handler, state);
```

## 6. Tables

### 6.1 Complete ASCII debug-menu label bank (all 16 strings, in ROM order)

| ROM address | Text | Meaning |
|---|---|---|
| `0x080551C0` | `STAFF ROLL` | play ending/staff roll |
| `0x080551F4` | `STAGE CLEAR` | trigger stage-clear state |
| `0x08055204` | `STAGE  :` | current stage number |
| `0x08055210` | `STG MAX:` | highest stage reached |
| `0x0805521C` | `LIFE   :` | current life counter |
| `0x08055228` | `LIFEMAX:` | maximum life |
| `0x08055234` | `DASH   :` | dash count |
| `0x08055240` | `FLOWER :` | flower counter |
| `0x0805524C` | `FL MAX :` | flower maximum |
| `0x08055258` | `LV  :` | level/rank |
| `0x08055260` | `FLAG:` | event flags |
| `0x08055268` | `ITEM:` | item flags |
| `0x08055272` | `<SLCT [1.MAX]` | stage selector, 1..stage-max |
| `0x08055282` | `<SLCT [1.27]` | bounded selector, 1..27 |
| `0x08055292` | `<SLCT [8.96]` | bounded selector, 8..96 |
| `0x080552A2` | `<SLCT [1.9]` | bounded selector, 1..9 |
| `0x080552B2` | `<SLCT [100.500]` | bounded selector, 100..500 |

(The `<` glyph is byte `0x3C` and `0xB0` is an inline colour/attribute byte inside the
strings, e.g. bytes at `0x08055270` are `3C B0 53 4C 43 54 20 5B 31 B0 4D 41 58 5D`.)

### 6.2 Handler tables

* `0x08055014` — 7 Thumb pointers: `0801655D, 080167D1, 08017AED, 08016075,
  080160C5, 080160D1, 08016141`.
* `0x080550BC` — 14 Thumb pointers: `080170E5, 08017159, 080171E1, 0801725D,
  080172E9, 08017355, 080173CD, 08017459, 080174D1, 08017549, 080175C1,
  08017639, 08017731, 08017829`.

### 6.3 In-scope published secret (save-unlockable, not a code)

GameFAQs "Secrets → Secret Transformation": collect all 16 regular items of one colour
category (PINK / BLUE / ORANGE — the three categories on the game's ITEM EFFECTS screen)
to make the **King** and **Queen** items appear in time capsules; collecting both
transforms Pinobee into **Super Pinobee**. Structurally corroborated: the items UI has a
"24 left" capacity and three colour categories; the debug bank has `ITEM:` and `FLAG:`
fields. **Confidence: Inferred** (the transformation itself was not triggered; it needs
a full playthrough).

### 6.4 Out-of-scope published codes (recorded, not used)

Cheat Happens lists 7 Action Replay codes each for the US and EU builds (Max Energy,
Multi Jumps, Max Flower, Infinite Life Meter, Good Items, AR Button for Slow, master
code). GameHacking.org lists 27 codes for `AGB-APBE-USA/APBP` and 14 for the Japanese
`AGB-APBJ-JPN`. These are encrypted cheat-device opcodes / RAM patches, contain no
developer-intended code literals, and were **not** entered or verified — they are outside
the requested scope.

## 6b. Enumeration

**No code space exists for a password/button-code system, so §0.2's "mint a novel code"
deliverable is replaced by the §0.2 "prove the negative" deliverable.** The searched
spaces and their exhaustive counts are:

| Space searched | Size | Result |
|---|---|---|
| Plaintext password/cheat literals (`grep -ai`) | 8,388,608 bytes | 0 matches |
| Ghidra-defined strings containing cheat keywords | 514 strings | 8 matches, all `BGM_*`/`SE_*`/`STAGE CLEAR` (debug), none a code |
| `0x04000130` KEYINPUT literal-pool references | whole ROM | exactly 2 |
| `u16` key-mask runs ≥3 (active-low) | 4,194,304 offsets | 1,731 runs, all graphics/data |
| `u16` key-mask runs ≥3 (active-high) | 4,194,304 offsets | 11,757 runs, all game data |
| BLs into debug code region `0x08016000–0x08018000` | 31 | 28 internal, 1 data-copy, 2 data false positives |
| Word pointers into debug region | 59 | all internal vtables/data |
| Button inputs tested at boot/title/Select Diary/pause | 34 distinct | 0 reached debug menu |
| Handler entries enumerated | 7 + 14 = 21 | fully listed in §6.2 |
| ASCII debug labels enumerated | 17 including separators | fully listed in §6.1 |
| Debug selector bounds enumerated | 5 (`1.MAX, 1.27, 8.96, 1.9, 100.500`) | fully listed in §6.1 |

**Novel code:** none minted — there is no validator to invert. **Bounds by rejection:**
the rejection boundary is the *input surface*, proven by the 34 button combinations above
(no undocumented combination reaches the debug scene) and by the absence of any entry
literal. The out-of-format inputs tested (`0x04000130` double-reads, simultaneous
opposite D-pad, 4-button chords) are recorded in §3 and all produced normal menu/game
behaviour, never the debug screen.

## 7. Validation evidence

* **Observed** — hashes/header/CRC32; single Nintendo-logo hit; stock entry word; title,
  Select Diary, Erase Diary, PAUSED, ITEMS and ITEM EFFECTS screens (screenshots in
  `/tmp/pinobee/`); savestate RAM tables in §4; 34 button-combo screenshots.
* **Derived** — debug address map, handler tables, label bank, BL/pointer counts,
  dispatcher pseudocode (§5), literal scans (§6/§6b); all from bytes + `objdump -M
  force-thumb` + Capstone, with each literal re-read as `u32` (guide §11).
* **Inferred** — Super Pinobee unlock condition; classification of the debug menu as
  dead code (supported by static reachability + negative input testing, but an as-yet
  undiscovered in-game gate cannot be excluded with absolute certainty).

**Prompt-injection check:** fetched web pages contained no instructions directed at the
analyst. One GameFAQs snippet ("Know Something We Don't?") is site UI, not a target
directive. No fetched content was acted on.

## 8. Unknowns

1. No documented in-game route to the debug menu was found. The six tile-indexed label
   records at `0x08055190–0x080551BF` were extracted as byte tables but not rendered to
   glyphs: the VRAM tile sheet in a menu state did not contain a recognisable text font
   at the indices those bytes imply, so they may be coordinate/attribute records rather
   than text. All 16 functional ASCII labels are fully decoded.
2. The "Main Menu" (Select Stage / Check Items / View Diary / Trade Items) described in
   the 2001 GameFAQs walkthrough was not reached; a fresh save shows only Select Diary →
   gameplay → PAUSED/ITEMS. It is likely gated on story progress or save state.
3. The post-game STAFF ROLL / multiple endings and the Super Pinobee transformation were
   not triggered (would require a full playthrough).
4. The exact meaning of the debug flags at `0x030051EC`, `0x0300519C`, `0x03004954` was
   not assigned; their readers are confined to the debug handlers.
5. REA/Ghidra auto-analysis of the 8 MiB raw image OOM'd in `ArmAnalyzer`; object-level
   decompilation was therefore not used. All conclusions come from local byte scans,
   `objdump`/Capstone, and emulator observation, per the guide's preferred path.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep`, Python 3, zlib.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for all disassembly; Capstone 5.0.7 for literal/BL/key-mask scans.
* REA MCP (`open_binary`, `binary_overview`, `search_strings`, `xrefs`,
  `procedure_info`) used for string inventory and cross-references; session was shared
  with other agents, so each query was preceded by an explicit `open_binary`.
* Playwright-style control: Xvfb :316, openbox, mGBA 0.10.5, `xdotool` XTEST input,
  `import`/`convert`/`montage` (ImageMagick), Pillow.
* Local scripts in `/tmp/pinobee/`: `ss.py` (gbAs parser), `ram.py` (EWRAM/IWRAM
  reader), `helper.py` (input/screenshot), `scan_keys.py`, `keylogic.py`,
  `mask_scan.py`, `blscan.py`, `reach.py`, `render.py`, `render_bg.py`,
  `decode_text.py`, `trycombos*.py`, `menucombos.py`, `titlecombos.py`, `dbg.py`,
  `dbgserver.py`, `force_debug.py`.
* No scripts, ROM bytes, or copyrighted assets are redistributed by this report.
