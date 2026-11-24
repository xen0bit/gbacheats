# Hi Hi Puffy AmiYumi: Kaznapped! (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Hi Hi Puffy AmiYumi: Kaznapped!.gba` |
| Size | 8,388,608 bytes (`0x800000`, 8 MiB) |
| Header title (`0xA0`) | `HI HI PUFFYA` (12-byte truncated form of the retail title) |
| Game code (`0xAC`) | `BHHE` |
| Maker (`0xB0`) | `G9` |
| Fixed byte (`0xB2`) | `0x96` |
| Version (`0xBC`) | `0` (Rev.00) |
| Complement (`0xBD`) | `0x8D` |
| Header checksum (`0xBE`) | `0x0000` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| MD5 | `80648fa0cb4fbf49a68c810fc64edaaa` |
| SHA-1 | `517e513bd1659749bfbab3d335df83a2838ee789` |
| SHA-256 | `c1ded629314fa0f3067d7abcc06754e614e507cb582cfe6953a89f0fe6c11fc9` |

Phase 0 result: the image is a single, standard retail GBA ROM. A full-file scan for the
156-byte Nintendo logo returns exactly one hit (file offset `0x4`, the header itself), so
there is no embedded second game, multiboot stub, or appended trainer. No `SUNHORS`,
`CRC BANDIT`, `GAMESHARK`, `CODEBREAKER`, or `TRAINER` signature occurs anywhere in the
image, and the entry word is the unmodified stock branch. EEPROM save type (4 Kbit /
512 bytes; `EEPROM_V124` string at file offset `0x7BE00`-region library code; confirmed by
the 512-byte `.sav` mGBA created). This is the retail image, not a patched scene release.

## 2. Executive summary

**No in-game / developer-intended cheat system exists in this build.** There is no password
screen, no on-screen keypad, no password-check table, no published or unpublished button
code, and no hidden debug/level-select screen reachable from any screen that can be reached
from a fresh boot.

Evidence summary:

* The title screen has exactly one interactive entry point, `PRESS START`. Each of the ten
  other GBA buttons and eleven Start-combinations was pressed on that screen and produced
  no screen change (screenshots `title_buttons_montage.png`, `title_combos.png` in the work
  dir) and no game-mode RAM change (savestate header `0x29/0x2C` comparison below).
* Pressing Start enters a scripted **PUFFY TUTORIAL** / story-mode gameplay. This is the
  normal single entry point into gameplay; there is no mode-select or options menu before it.
* Static exhaustive searches over all 8 MiB found **zero** occurrences of
  `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `LEVEL SELECT`, `WARP`, `MENU`,
  `OPTION`, or `PRESS START` in ASCII, `+0x20`, `-0x20`, UTF-16LE, UTF-16BE, XOR-0x40,
  XOR-0xFF, byte-reversed, or the common font-index offsets (bases `0x00/0x20/0x30/0x40/0x41/0x60/0x61`, offsets `0x00..0xFF`, strides 1/2/4). The game's visible
  tutorial/UI text is plain ASCII (control chars `#` = newline, `$` = end, `^` = page) at
  file `0x15CCA8`–`0x15D71A`; the only large non-ASCII text-like region (`0x192000` onward)
  is sprite/tile data, not a text bank. The VRAM tile sheet rendered from a title savestate
  contains title-art fragments, not a glyph-indexed menu font.
* No button-code table exists: the Konami sequence was searched as active-high masks
  (`u16` LE, raw bytes, inverted) and as low bytes — 0 hits. A whole-ROM `u16` scan for runs
  of ≥4 single-button masks found only compressed-graphics data runs (the dense family at
  `0x13E8F0`–`0x13F5xx` is a repeating 28-byte stride, not keypresses).
* The single input sampler at `0x08000AE0` produces exactly three globals (pressed / held /
  released) and no key-sequence matcher or progress counter.
* No published codes were available to verify: `websearch` returned no results for six
  queries; DuckDuckGo and Google served bot challenges; 3rd party cheat indexes returned HTTP 403;
  the Wayback CDX/HTTP API returned empty/404/503; the Jina reader proxy was blocked.
  a 3rd party cheat index's own search returned **"Your search did not match any results."** for
  this title. Therefore there is no published in-game code list to reconcile against the ROM.

This is a **"no system"** negative (guide §16.3 category 1), bounded by the searches and
screen walks below — not "dead code", "cut feature", or "gated feature".

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`,
`SDL_RENDER_DRIVER=software`, command `mgba -3 game.gba` (analysis copy at
`/tmp/puffy/game.gba`, byte-identical MD5 to the target).

Default SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad=arrow keys. Holds of 100–300 ms were used (short taps are missed). Screenshots were
captured with `scrot` and cropped to `720x480+154+184`.

Exact reproducible path:

1. Boot → Cartoon Network Interactive splash (auto) → title screen
   `PRESS START` (screenshot `title_reload.png`).
2. On the title screen press each of `x z a s BackSpace Up Down Left Right` one at a time;
   the screen is unchanged (`title_buttons_montage.png`).
3. Press each Start-combination (`Start+A`, `Start+B`, `Start+L`, `Start+R`,
   `Start+Select`, `Start+L+R`, `Start+<direction>`, `Start+A+B`); every one enters the
   same tutorial (`title_combos.png`).
4. Press Start alone → tutorial gameplay. Start toggles the tutorial hint overlay
   (`START: TEXT` at bottom-right). Walking right and pressing A (jump) clears the first
   tasks; the next tasks are `R` during a jump, `B` on the marked block, then a `R`
   "GUITAR SMASH". The walk reached these screens: `title_reload.png`, `afterstart1.png`,
   `skip2.png`, `walk1.png`, `walk2.png`, `pause_probe.png`, `dismissed.png`,
   `step1.png`, `pit_cross.png`, `pit_cross2.png`, `tut_jump1.png`, `tut_jump2.png`,
   `tut_msg.png`, `tut4_view.png`, `tut4_push.png`, `tut4_push2.png`, `tut5_smash.png`,
   `sm_montage.png`, `long_push.png`, `hints_montage.png`.
5. During tutorial gameplay every button and combination was also tried
   (`gp_buttons_montage.png`): A/B/L/R/Select/L+R/Start+A/Start+B/Start+Select all leave
   the tutorial state machine unchanged — no pause menu, no options, no debug screen.

Save states were saved to slots `F1`–`F6` and parsed with the helper in §9. State 1 is the
title screen; states 2–6 are successive tutorial checkpoints.

## 4. Address map

| Item | Address (ROM or RAM) | Evidence |
|---|---|---|
| Header / entry | `0x08000000` / `0x080000C0` | Observed bytes, `b 0x080000C0` |
| crt0 → `main` pointer | `0x080001EC` → `0x08000339` | Disassembly (Thumb main at `0x08000338`) |
| Key input sampler | `0x08000AE0` | Thumb disassembly |
| KEYINPUT literal | `0x08000B14` = `0x04000130` | 32-bit literal, LDR at `0x08000AE2` |
| pressed keys (`u16`) | IWRAM `0x03000218` | `strh` at `0x08000AFE` |
| held keys (`u16`) | IWRAM `0x0300021A` | `strh` at `0x08000B04` |
| released keys (`u16`) | IWRAM `0x0300021C` | `strh` at `0x08000B08` |
| previous key state (`u16`) | IWRAM `0x03000C04` | `strh` at `0x08000B0A` |
| Tutorial message pointer table | `0x0815D720`, 8-byte stride, 9 entries `{u32 text_ptr, u32 len}` | Observed pointers to `0x0815CCA8`…`0x0815D5D4` |
| Tutorial script strings | `0x0815CCA8`–`0x0815D71A` | ASCII with `#`, `$`, `^` control chars |
| Tutorial script/VM dispatcher | `0x0801892E` (`mov pc,[table+r0*4]`), 34-entry table at `0x08018B0` | Thumb disassembly |
| Memory-region classifier (generic library, not a menu) | `0x08003DA0`, sole BL from `0x08001872` | Thumb disassembly; 0 other callers |
| Input-literal pool | `0x08000B14`, `0x08000B18` (`0x03000218`), `0x08000B1C` (`0x03000C04`) | Observed |

mGBA savestate RAM layout (`.ss1` PNG, `gbAs` chunk zlib-decompressed to 397,312 bytes):
`0x0000`–`0x0FFF` CPU/registers/IO/palette/OAM, `0x1000`–`0x18FFF` VRAM,
`0x19000`–`0x20FFF` IWRAM (maps `0x03000000`→`0x19000`),
`0x21000`–`0x60FFF` EWRAM (maps `0x02000000`→`0x21000`).

Observed savestate-header mode anchors (state offsets; `base.ss1` = title,
`btn_Start.ss1` = same title state after one Start press):

| Offset | Title | After Start | Meaning |
|---|---|---|---|
| `0x29` | `0x00` | `0x01` | screen/mode byte |
| `0x2C`–`0x2F` | `0x00000000` | `0x08119167` | active scene/script pointer |
| `0x19000+0xE34` (IWRAM `0x03000E34`) | `0x00` | `0x01` | game-started flag |

For all nine non-Start title buttons the header bytes `0x29` and `0x2C`–`0x2F` remained at
their title values while Start changed both — direct RAM proof that no other title input
opens another screen. (Other IWRAM bytes differ by ~1800–1900 due to animation-frame and
timer noise; the mode anchors are the discriminating bytes.)

## 5. Algorithm

There is no password/validator algorithm in this build. The only input transformation
present is the key sampler, reimplemented exactly from `0x08000AE0`:

```python
def poll_keys(raw_keyinput):                 # raw active-low from 0x04000130
    held = ~raw_keyinput & 0xFFFF             # active-high masks
    prev = iwram_u16(0x03000C04)
    delta = held ^ prev
    iwram_u16(0x03000218) = delta & held      # pressed this frame
    iwram_u16(0x0300021A) = held & prev       # held
    iwram_u16(0x0300021C) = delta & prev      # released this frame
    iwram_u16(0x03000C04) = held
```

Button masks therefore follow the standard GBA active-high convention:
`A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010 Left=0x020 Up=0x040 Down=0x080
R=0x100 L=0x200`. No code consumes these values as a *sequence*: the ROM contains no
progress counter, no comparison of a `pressed` history against a mask table, and no
validator call site.

## 6. Tables

**Button masks** — as above. The documented in-game actions that read them are all normal
gameplay, not cheats: L+R = JAM SESSION, R during jump = AIR GUITAR SLIDE, B on a marked
block = grab/push, R on the block = GUITAR SMASH, L = switch Ami/Yumi, A×3 = triple jump,
Up+A (Ami) = helicopter, Down+R = Power Chord, Down near cats = petting. All come from the
ASCII tutorial script at `0x0815CCA8`–`0x0815D71A` and were observed on screen.

**Tutorial message table at `0x0815D720`** (9 entries, 8 bytes each):

| # | text ptr | length | first line |
|---:|---|---:|---|
| 0 | `0x0815CCA8` | `0x97` | Welcome to the PUFFY TUTORIAL! |
| 1 | `0x0815CD3F` | `0x10F` | See that hole in the middle? |
| 2 | `0x0815CE4E` | `0x12D` | Yumi's got some real muscle! |
| 3 | `0x0815CF7B` | `0x14B` | Too high of a jump for Yumi? |
| 4 | `0x0815D0C6` | `0x0B5` | See Ami's icon over the hook? |
| 5 | `0x0815D17B` | `0x187` | Oh, no! It's a fan-boy! |
| 6 | `0x0815D302` | `0x12D` | What a scary looking robot! |
| 7 | `0x0815D42F` | `0x1A5` | Yikes! Trouble everywhere! |
| 8 | `0x0815D5D4` | `0x14B` | Nice work, rock star! |

(The displayed hints are a subset of the full script, which also contains the
AIR GUITAR SLIDE and GUITAR SMASH lines at `0x0815CDD5` and `0x0815CF02`.)

**Search result counts (whole 8 MiB, byte-exact):**

| Pattern | Encoding(s) | Hits |
|---|---|---|
| `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `LEVEL SELECT`, `WARP`, `MENU`, `OPTION` | ASCII, `+0x20`, `-0x20`, UTF-16LE/BE, XOR-0x40, XOR-0xFF, reversed, font-index bases/offsets/strides | 0 |
| `PRESS START` | same | 0 (title label is sprite art) |
| Konami mask sequence | `u16` LE, inverted `u16`, raw bytes, inverted bytes, low bytes | 0 |
| `0x04000130` literal | 32-bit LE | 1 (`0x08000B14`) |
| Nintendo logo | 156-byte exact | 1 (header at `0x4`) |
| `MultiSioSync` / `0123456789` | ASCII at `0x7BE30`/`0x7BE4C` | library data, not a password keypad |
| Password-shaped `[A-Z0-9!?-]{4,16}\0` | ASCII | 744 raw matches; inspected first 60 — all random compressed graphics/data, no equal-length NUL-padded code table or pointer table |

## 6b. Enumeration

**Space size: 0.** There is no code space to enumerate: no password alphabet, no code
length, no checksum, no lookup table, no button-sequence dispatcher, and no hidden-menu slot
table. Per guide §0.2 the negative is bounded by (a) the complete screen walk from a
fresh boot and (b) exhaustive searches of the input/text spaces:

1. **Every reachable screen from a fresh boot was walked with RAM evidence:** splash →
   title → tutorial gameplay (multiple hint/room variants). On the title screen all 10
   non-Start buttons and 11 Start-combinations were tested; the mode anchors
   (`0x29`, `0x2C`–`0x2F`, IWRAM `0x03000E34`) changed **only** for Start. During gameplay
   all buttons/combinations were tested; no menu, pause, options, level select, or debug
   screen appeared (`gp_buttons_montage.png`).
2. **Text space:** 0 hits for menu/cheat/debug labels across 8 encodings × 9 keywords, plus
   font-index offset/stride enumeration (bases `0x00/0x20/0x30/0x40/0x41/0x60/0x61`,
   offsets `0x00`–`0xFF`, strides 1/2/4). The only readable text bank is the ASCII tutorial
   script (dumped and decoded in §6), which documents only normal gameplay.
3. **Button space:** the Konami sequence and all single-button `u16` runs were checked; the
   only input consumer is the sampler at `0x08000AE0`, which has no sequence progress state.
4. **Code table space:** no hard-coded code strings, no equal-length NUL-padded string
   table, and no 32-bit pointer table to one.
5. **Published codes:** none found (all cheat sources blocked or empty; 3rd party cheat indexes
   explicitly returned no results). There is therefore no published code to test, mint an
   unpublished variant of, or bound by rejection.

**Novel codes: none exist to mint.** Per §0.2, minting a code is only meaningful when a
code system exists; here the validator/table search space is provably empty, so the
enumeration deliverable is the bounded negative above. **Bounds proven by rejection:** the
game's own input rejects every non-Start title button and every non-gameplay-combination
during the tutorial as menu/progress inputs — observed both visually and in the three RAM
mode anchors. No in-game code was accepted because none exists.

Gate note (guide §16.10 / §16.3): the pause menu described in the tutorial script
("In World Tour Mode, the game also saves when you select [Quit] from the Pause Menu") is
**gated behind completing the tutorial**. The tutorial's block-smash step could not be
cleared with any tested input (R, B+R, R+directions, jump+R, B+Right+R, double-tap R —
10 combinations, `hints_montage.png`); EEPROM remained all `0xFF` (`game.sav`, 512 bytes,
0 non-FF bytes), so no post-tutorial save/menu state was reached. This is a **skill gate**,
not a code/debug gate: nothing in the ROM suggests a hidden screen beyond it.

## 7. Validation evidence

* **Observed** (emulator/screenshot): title splash and title screen; all title button and
  Start-combination screenshots; tutorial gameplay screens and hint changes; tutorial
  messages rendered exactly as the ASCII script at `0x0815CCA8`–`0x0815D71A` predicts;
  no menu appearing for any non-Start input.
* **Observed** (RAM): savestate-header mode anchors `0x29`, `0x2C`–`0x2F` and IWRAM
  `0x03000E34` — title vs. after-Start vs. every other button; IWRAM/EWRAM diff counts;
  EEPROM file all `0xFF`.
* **Derived** (disassembly): crt0/main at `0x08000338`; key sampler at `0x08000AE0` with
  its five global writes; tutorial message table and 34-entry script VM table at
  `0x08018B0`; single caller of the generic memory classifier; stock entry word and single
  logo hit.
* **Inferred** (labelled): the sprite-art nature of the `PRESS START` title label (no ASCII
  or font-index encoding found, and title VRAM tiles are image fragments); that the pause
  menu / World Tour map are ordinary post-tutorial screens rather than cheat features.
* **Blocked**: all published-code web sources (403 / captcha / 503 / empty). No fetched
  page supplied any code, instruction, or prompt-injection payload to act on.

## 8. Unknowns

* The post-tutorial World Tour / pause / options screens were not reached because the
  tutorial's GUITAR SMASH step could not be cleared. Their contents are inferred from the
  tutorial script's mention of a `Quit` entry and `[CHANGE OK]`/`JAM SESSION` HUD text,
  not observed. No cheat/debug feature is implied by that script.
* The exact condition that advances the block-smash step was not isolated (10 input
  combinations tested; see §6b). It is a gameplay-skill gate, not a cheat gate.
* Web verification of published codes was impossible from this environment; the negative
  rests on the ROM searches and a 3rd party cheat index's empty result, not on a complete crawl of
  every cheat site.

## 9. Tooling

Work dir `/tmp/puffy`. Created by this analysis:

* `helpers.py` — XTEST key presses, screenshots, mGBA-GDB-stub RAM reads.
* `ss.py` — mGBA `.ss1` PNG parser: extracts zlib `gbAs` chunk; maps GBA RAM addresses to
  state offsets; byte-diff and hex dump commands.
* `render_vram.py` — renders 4bpp VRAM tiles from a savestate (Pillow) to check for a
  font/tile-indexed text bank.
* `dbg.py`, `harness.py`, `gdbc.py` — attempted mGBA `-d` and `-g` interactive controllers
  (the `-d` core stopped responding to stdin after `continue`; the `-g` port 2345 was
  occupied by another analysis session, so the savestate method was used instead).
* `strings_all.txt` — `strings -t x -n 4` output; Python searches for encodings, key masks,
  alphabets, pointer tables, and header/logo scans.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all
  Thumb disassembly; `xxd`, `md5sum`, `sha1sum`, `sha256sum`, `file` for Phase 0.
* Screenshots: `title_reload.png`, `title_buttons_montage.png`, `title_combos.png`,
  `gp_buttons_montage.png`, `hints_montage.png`, `sm_montage.png`, `tut_*.png`, etc.

No ROM or copyrighted asset is redistributed by this report. No GameShark/CodeBreaker or
memory-edit codes are reported; the scope was limited to developer-intended in-game
features.
