# Soccer Mania (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Soccer Mania.gba` (LEGO Soccer Mania, aka LEGO Football Mania EU) |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `SOCCER MANIA` (offset 0xA0) |
| Game code | `ALSE` (US, AGB-ALSE-USA); maker `69` |
| Version | 0x00; fixed byte 0x96 present; complement 0x78; header checksum 0x0000 |
| Entry word | `0xEA00002E` (stock GBA branch to 0x080000C0) |
| MD5 | `3ff6f06de88f0646e8cf85181ca2e10d` |
| SHA-1 | `05799b99395aba04dfe5ae8af019e4d70cb8e61b` |
| SHA-256 | `2f930badb11ec10b2e35450887f04b3d8823df8be642618d7a76adda8d33fedd` |

**Phase 0 scan:** exactly one Nintendo-logo/GBA-header hit, at file offset 0. No
embedded second image, multiboot stub, appended trainer, or cracktro — the entry
word is the stock `b 0xC0` and the first 4 KiB is a normal ARM crt0. The zero
header checksum is a common rebuild artifact; the complement byte is 0x78.

## 2. Executive summary

**There is no in-game code system in this GBA build.** No password screen,
button-code validator, on-screen keypad, or developer code generator exists.
The widely published "Soccer Mania" cheat codes (the Konami-style
`Up,Up,Down,Down,Left,Right,Left,Right,B,A,Start` "invisible opponents" code and
the "hold Select+B when choosing opponent / Up+B when choosing your team"
"cheat mode") belong to the **Game Boy** game of the same name, not this GBA SKU
(guide §16.11). I verified both statically (no key-mask byte sequences anywhere
in the 8 MiB image) and dynamically (entering the sequence on the GBA title
screen only navigated menus; no flag was set).

The GBA game does ship two **developer debug screens** (build-date screen and
palette test) documented by 3rd party cheat indexes, gated on a memory byte at `0x0300626C`. They
are triggered only by a GameShark memory write; I proved that (a) the game never
writes those values itself and (b) patching the byte at runtime does not change
the displayed screen, because the scene word is consumed once at a scene
transition. They are therefore gated debug content, not reachable by controller
input. The only developer-intended progression extras are the six Skill Zone
characters earned by beating Skill Zone challenges (a save-bit unlock, not a
code).

All reachable screens were walked with RAM evidence (Section 6b) and the
font/tile-indexed text bank was inspected (Section 9): the game has essentially
no ASCII text in ROM, and its labels are drawn from tile glyphs in VRAM.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under `Xvfb :318`, `SDL_AUDIODRIVER=dummy`, 3× scale.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys, L=`a`, R=`s`.
* Boot path: language select (9 languages) → A → title → Start → **Training**
  wheel. Press B to return to the **Main Menu** wheel.
* Main Menu wheel: Left/Right rotate; A enters. Order (from Training):
  Training, Friendly, The Quest, Multiplayer, Options, Restore. Rotation
  saturates at the two ends (there is no wrap).
* RAM evidence: save an mGBA state (`Shift+F1`), decompress the `gbAs` PNG
  chunk, read IWRAM at state offset `0x19000 + (addr-0x03000000)`. The scene
  word is `0x0300626C` at state offset `0x1F26C`.
* Button-code test: load a title-screen state, press
  `Up Up Down Down Left Right Left Right B A Start`, save a state, diff IWRAM —
  only normal menu navigation is observed; no new flag/screen.

## 4. Address map

| Item | Address / offset | Evidence |
|---|---|---|
| Scene/state word | IWRAM `0x0300626C` (32-bit) | Derived (writes at `0x0800E04C`, `0x0801E004`, thunks) + Observed (savestate reads) |
| Hold counter | IWRAM `0x03006B90` (32-bit) | Derived (`0x0800EB2`..`0x0800EBC`) |
| Debug gate flag | IWRAM `0x03004600` | Derived (`FUN_080016C6` sets 0xF) |
| Debug gate check | `0x0800ECC`–`0x0800EE2` | Derived: if counter == ±0x14 and scene == 0x5C → `BL 0x080016C6` |
| Scene setter | `0x08002380` (`str r0,[r1]`) | Derived; 33 thunks at `0x08002304`..`0x08002378` and `0x0801918C`..`0x080192CE` load the pointer then jump here |
| Scene write sites | `0x0800E048`, `0x0800F3F4`, `0x08010B66`, `0x080185DE`, `0x080191EC`, `0x080192C8`, `0x08019B62`, `0x0801E000`, `0x0801E028`, `0x0801E044`, `0x0801E114`, `0x0801E228`, `0x0801E252`, `0x0801E270`, `0x0801E294`, `0x0801E2B2`, `0x0801E2DE`, `0x0801E2FC`, `0x0801E30C`, `0x0801E38C`, `0x08021AA0`, `0x08027BE4`, `0x080288AE`, `0x0802945E` | Derived (Capstone scan) |
| Font glyph tiles | VRAM (visible in savestate VRAM tile sheet) | Observed |
| Text | tile-indexed (no ASCII in ROM) | Observed (`strings` finds only header/noise; character names absent in ASCII) |

File offset ↔ ROM address: `0x08000000 + file_offset` (single 8 MiB image, base 0).

## 5. Algorithm

There is no password algorithm to reimplement. The relevant state machine is:

```
scene_word = *(u32*)0x0300626C
# written once per transition by setter thunks (r1 = &scene_word, r0 = id)
# consumer: a single dispatch on scene_word at each transition

# debug-gate lead (derived, unreachable — see §8):
counter = *(s32*)0x03006B90          # sign-extended hold counter
if counter > 0: counter++
if counter < 0: counter--
if (counter == -20 or counter == +20) and scene_word == 0x5C:
    FUN_080016C6()                   # *(u32*)0x03004600 = 0xF; counter = 0; jump table
```

The two documented debug screens require `scene_word == 0x00` (build date) or
`0x6D` (palette test) to be injected externally at boot. Neither value is ever
produced by the game's own setters (Section 6b).

## 6. Tables

**Reachable scene words (Observed, from savestates):**

| Scene | Screen |
|---|---|
| 0x2 | Intro / logos |
| 0x3 | Language select (9 languages) |
| 0x5 | Title |
| 0x6 | Main Menu wheel / Multiplayer position |
| 0x8 | Training wheel |
| 0x9 | Quest world map |
| 0xB | Friendly → Team Select |
| 0xD | Options wheel |
| 0xE | Pitch Select (`LEGO Stadium`) |
| 0xF | The Quest → Choose Team |
| 0x46 | Match in progress |
| 0x49 | Restore (3 slots, all `(empty)`) |
| 0x59 / 0x5D | Match / Quest match states |

**Main Menu wheel (6 items):** Training, Friendly, The Quest, Multiplayer,
Options, Restore.
**Training wheel (6):** Dribbling, Shooting, Tackling, Passing, Setup, Statistics.
**Options wheel (6):** Number of Players, SFX, Music, Half Length, Control,
End Switching.
**Team Select (7 teams):** City Stars, City, Wild West, Pirates, Knights,
Arctic, Adventure.
**Quest teams (3):** City, Knights' Kingdom, Wild West.
**Pause menu:** Paused / Continue / Quit.
**Restore slots:** 3 (0, 1, 2 — all empty on a fresh save).
**Save data:** a 512-byte `Soccer Mania.sav` is created by mGBA; unlocks are
save bits, not codes.

**Published codes verified against this ROM:**

| Published claim | Source | Result on GBA build |
|---|---|---|
| Konami code → invisible opponents | 3rd party cheat indexes/world-of-nintendo (Game Boy) | **Not present**: 0 hits for mask sequence (u8/u16/u32, forward and reversed); emulator test only navigated menus |
| Hold Select+B / Up+B → cheat mode | Game Boy sites | GB-only; no matching key-mask table found |
| Build-date screen via `0300626C00` | 3rd party cheat indexes | Debug screen exists; value is gated, not controller-reachable (see §6b/§8) |
| Palette test via `0300626C6D` | 3rd party cheat indexes | Same gate |
| 6 Skill Zone characters | 3rd party cheat indexes | Gameplay unlock (beat challenges 1–6); not a code; names absent as ASCII (tile text) |

## 6b. Enumeration

**No code space exists — this is a proven negative, bounded as follows.**

1. **Password/code input surface:** enumerated every reachable screen
   (Section 6): 9 language entries, title, 6 main-menu items, 6 sub-wheels ×2,
   7 teams, 3 quest teams, 3 restore slots, 3 pitch options, pause. None
   contains a password/keypad entry field or a code comparator.
2. **Scene-word space:** the state word at `0x0300626C` is 32-bit
   (4,294,967,296 representable values), but the union of **all** values this
   build ever writes — 37 inline `mov`+`str` sites (Capstone scan), 33 setter
   thunks, and the runtime-observed values — is exactly **44 distinct values**:
   `0x2, 0x3, 0x5, 0x6, 0x7, 0x8, 0x9, 0xB, 0xC, 0xD, 0xE, 0xF, 0x10, 0x11,
   0x1E, 0x1F, 0x24, 0x27, 0x2A, 0x2B, 0x34, 0x3D, 0x40, 0x42, 0x44, 0x46,
   0x47, 0x48, 0x49, 0x4A, 0x4C, 0x4D, 0x4E, 0x4F, 0x50, 0x52, 0x53, 0x55,
   0x56, 0x57, 0x59, 0x5D, 0x62, 0x63`.
   The 3rd party cheat indexes debug values **`0x00` and `0x6D` are not in this set** — no code
   path can produce them. Bounds proven by that exhaustive write-site count.
3. **Debug screens — runtime bound (Observed):** patching the byte at
   `0x0300626C` to `0x00` or `0x6D` in savestates taken at language select,
   title, main menu and team select, then loading each, produced **no visual
   change** in any of the 8 trials (screenshots `forcegrid.png`). The scene is
   dispatched once per transition, so a mid-scene write cannot reach the debug
   screens. Combined with (2), they are gated memory-edit-only content.
4. **Button-code space:** the 11-press published sequence was searched as
   u8/u16/u32 little-endian, both forward and newest-first, across all
   8,388,608 bytes: **0 hits** in every encoding. The alternative active-low
   key representation was also covered by the u16/u32 scans. Dynamic test on
   the title screen produced only ordinary menu navigation (scene 0x5 → 0xB),
   with no novel flag.
5. **Novel code:** not applicable — there is no validator to mint a code for.
   Per guide §0.2, the negative itself is the deliverable and is bounded by the
   counts above (44 written scene values, 6+6+6 menu items, 7 teams, 0 code
   literals, 0 key-mask hits, 8/8 failed runtime debug triggers).

## 7. Validation evidence

* **Observed:** hashes/header; one embedded header; all screens and their
  scene-word values from decompressed `gbAs` state; 6-item/6-item/6-item wheel
  labels by stepping one press at a time; 7 teams; 3 restore slots; pause menu;
  no effect from the Konami sequence; no effect from 8 runtime scene patches.
* **Derived:** scene-word setter at `0x08002380` and its thunks; the 37 inline
  write sites; the `±0x14 & scene==0x5C` gate at `0x0800ECC`–`0x0800EE2`;
  absence of `0x00`/`0x6D` from the complete write set.
* **Inferred:** the Skill Zone unlockable characters (published by 3rd party cheat indexes)
  are save-bit unlocks rather than codes — consistent with the 512-byte `.sav`
  and with the absence of any code surface, but the individual bits were not
  mapped. The `scene==0x5C` gate's purpose is unknown (see §8).

## 8. Unknowns

* The `0x03006B90` hold counter reaching ±20 on scene `0x5C` calls
  `FUN_080016C6()` (sets `0x03004600 = 0xF`, jumps through an unrecovered jump
  table). No reachable setter writes scene `0x5C`, so this looks like dead or
  computed-state code; I did not identify a controller input that reaches it,
  and I do not claim it as a cheat.
* The 6 Skill Zone character names are stored as tile-index glyphs (no ASCII
  in ROM); the individual save-bit offsets were not mapped.
* The build-date and palette-test screens were not displayed: the GameShark
  memory edits are outside the in-game scope, and mGBA's CLI `-c` cheat path
  did not apply the VBA-format raw write in this build (verified by reading the
  byte back as 0x2/0x3 rather than the patched value). a 3rd party cheat index's claim that these
  screens exist is recorded as an external reference, not an observation.
* VRAM font glyphs were located and rendered, but the tile-index→letter mapping
  and the ROM text bank were not fully decoded; the screen enumeration rests on
  rendered labels plus RAM evidence, not on a decoded string table.

## 9. Tooling

* `ss.py` / `patchss.py` — mGBA `.ss*` PNG `gbAs` chunk decompress/recompress and
  IWRAM byte patch (state layout: CPU/header `0x0`, VRAM `0x1000`, IWRAM
  `0x19000`, EWRAM `0x21000`; total 0x61000 bytes).
* `scanlit.py`, `thunks.py`, `findwrite.py` — Capstone literal/xref and
  `mov`-immediate→`str` scanners for the scene word.
* `btnsearch.py` — key-mask sequence search across the whole ROM.
* `font.py` — 4bpp VRAM tile renderer (font-glyph inspection).
* `key.py`, `snap.py`, `walk.sh`, `enter_all2.sh`, `subs.sh`, `teams.sh`,
  `konami.sh`, `forcescene.sh` — Xvfb/xdotool walk and RAM-capture helpers.
* REA (Ghidra 12.1.4) raw-ARM import at base `0x08000000` for xrefs and
  pseudocode of `FUN_08000DA8`, `FUN_080016C6`, `FUN_0800193A`,
  `FUN_08002038`.
* ROM and extracted assets were **not** redistributed; only addresses,
  hashes, and original observations are published.
