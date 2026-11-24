# Sonic Advance 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Sonic Advance 2.gba` |
| Size | 16,777,216 bytes (`0x01000000`, 128 Mbit) |
| Header title | `SONICADVANC2` |
| Game code | `A2NE` (USA, En/Ja/Fr/De/Es/It) |
| Maker | `78` |
| Version / complement / checksum | `0x00` / `0x81` / `0x0000` |
| Entry word | `0xEA00002E` — stock `b 0x080000C0`, no cracktro or appended trainer |
| MD5 | `3fb865c5f142a8fc1f82105bfc6b8935` |
| SHA-1 | `7bcd6a07af7c894746fa28073fe0c0e34408022d` |
| SHA-256 | `f2b7a3329401a02706d87560f61da3e6da2ca42f2b9ae98a86d78e0529cb7260` |

The SHA-1 is byte-for-byte the `sa2.sha1` of the public SAT-R SA1/SA2 decompilation
(`github.com/SAT-R/sa2`, No-Intro USA Rev.00), so the source-level findings below refer to this
exact image. The `0x0000` header checksum is a normal rebuilt-header artifact (guide §16.1); the
entry word, logo and full hash match confirm a retail image.

## 2. Executive summary

**Sonic Advance 2 has no password system, no code-entry screen and no reachable hidden/debug menu.**
The only developer-intended in-game "codes" are two *single-chord* button gates in the shared Dimps
engine, plus a set of save-backed unlockables. The whole surface was enumerated:

* **In-game reset** — hold `A+B+Start+Select` in play → soft reset to the title screen. Observed.
  The validator masks the keypad with `0x30F` and compares for equality, so the six other keypad
  bits are ignored. A **novel alias absent from every published list**, `A+B+Start+Select+Up+L+R+Left`,
  was accepted in the emulator (title screen; savestate diff 59,706 changed state bytes).
  Rejections were proved: omitting `Select` merely pauses, omitting `Start` does nothing.
* **Boot intro skip** — the same chord held during engine init sets `FLAGS_SKIP_INTRO` (`0x1000`)
  and calls `CreateTitleScreenAndSkipIntro`. This is **derived** from the exact-ROM decomp
  (`src/core.c:279`, `src/game/game.c:179-194`); it was not reliably observable because the same
  chord also fires the VBlank soft-reset, producing a reset race (§8).
* **Unlockables** — seven flag bits in the flash save at `sector+0x1B` (Cream/Tails/Knuckles/Amy,
  Boss Time Attack, Sound Test, Tiny Chao Garden), with per-character level and emerald arrays and
  a completion bitfield at `sector+0x1A`. Every bit was mapped by patching a copy of the save
  (analysis only) and observing the UI; bit `0x10` was isolated to prove the Boss Time Attack gate.
* **Dead developer code** — a `DEBUG`-only `SELECT`-button shortcut to character select
  (`src/game/shared/stage/stage.c:495`) and `LoadCompletedSaveGame()`
  (`src/game/sa2/save.c:921`) have no retail caller and cannot be reached by any controller input.

All web "cheats" for this SKU are GameShark/CodeBreaker/Action Replay RAM pokes (out of scope), or
unlock descriptions that match the save bits above. Sibling button codes from Sonic Advance 1 and
Sonic Advance 3 were tested on this ROM and rejected (wrong SKU).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba -3`), Xvfb `:319` + openbox,
  `SDL_AUDIODRIVER=dummy`. Screenshots in `/tmp/sonicadvance2/`.
* Keymap: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`,
  D-pad = arrow keys. **80–100 ms holds and ~300 ms gaps are required**; this menu engine debounces
  faster taps (8 rapid Downs once advanced the cursor only one slot).
* Harness notes (guide §16.2): `mgba -d` exits immediately when stdin reaches EOF unless a FIFO
  writer keeps it open; with `-d` the viewport went black in this session, so the screen walk used
  plain `-3`. RAM evidence therefore came from `.ssN` savestates (Shift+F1 save, F1 load) and from
  the flash `.sav` file, not the GDB stub.
* Boot path: language screen → `A` → REG. NAME (type any name, cursor to END, `A`) → intro
  (`Start` repeated ~0.3 s apart) → title "PRESS START" → `Start` → Single Player → `A` → main menu.
* Novel code on the real screen: from gameplay hold
  `x`+`z`+`Return`+`BackSpace`+`Up`+`a`+`s`+`Left` together for ~300 ms → title screen.
  Canonical published form `x`+`z`+`Return`+`BackSpace` gives the same result.
* Save-bit probe (analysis, not a code): edit `game.sav` newest sector (`MGGE`, version field),
  set byte `+0x1B`, recompute the u32-word checksum at `+0x374`, relaunch. Restore afterwards.

## 4. Address map

All `0x08......` are `0x08000000 + file offset`; save offsets are inside a 0x1000-byte flash sector.

| Item | Location | Evidence |
|---|---|---|
| Boot chord check (`gInput == 0x30F`) | decomp `src/core.c:279` → `game.c:179-194` | Exact-ROM source; sets `FLAGS_SKIP_INTRO` `0x1000` |
| In-game reset chord (`(~KEYINPUT & 0x30F) == 0x30F`) | decomp `src/core.c:872-890`, `VBlankIntr` | Exact-ROM source; `SoftReset(0x20)` |
| `DEBUG`-only SELECT → character select | decomp `src/game/shared/stage/stage.c:495-503` | Wrapped in `#if DEBUG`; no retail caller |
| `LoadCompletedSaveGame()` | decomp `src/game/sa2/save.c:839,921` | Zero call sites ROM-wide |
| Save sector magic `MGGE` | `.sav` `0x00000000`, `0x00001000` (`0x4547474D`) | Byte dump; version 1 / version 2 |
| Save sector count / stride | 10 sectors × `0x1000`, 64 KiB `.sav` | `save.c:91,462-485`; two live sectors observed |
| `SaveSectorData.completions` | sector `+0x1A` | `save.c:346-364`; patched `0xFF` → all endings |
| `SaveSectorData.unlocks` | sector `+0x1B` | `save.c:372-392`; patched `0x7F` → all UI unlocks |
| `unlockedLevels[5]` / `chaosEmeralds[5]` | sector `+0x1F` / `+0x24` | `save.c:432`, patched to `0x1F`/`0x7F` |
| `timeRecords` | sector `+0x2C`, 315 × u16 (`0x8CA0` = unfilled) | Byte dump: run `0x2C..0x2A2` |
| `multiplayerScores[10]` / `id` / `score` | sector `+0x2A4` / `+0x36C` / `+0x370` | Struct layout, 20-byte records |
| `SaveSectorData.checksum` | sector `+0x374` | Sum of u32 words `[0,0x374)`; verified `0xa9855ee9` |
| `SaveGame` RAM mirror | `gLoadedSaveGame` (EWRAM), fields `0x11..0x14` | `include/game/sa2/save.h:49-53` |

Literal `0x0000030F` occurs at ROM `0x080E18A8` (a constants table) and `0x08BA5444` (non-code
data); the comparison itself is compiled into an unmatched function, so an exact instruction
address is not claimed here (§8).

## 5. Algorithm

```python
# derived from same-SHA-1 decomp, src/core.c:279 and :872-890
MASK = 0x001 | 0x002 | 0x008 | 0x004      # A | B | START | SELECT = 0x30F

# boot (EngineInit)
if (~KEYINPUT & 0x3FF) == MASK:           # gInput snapshot
    gFlags |= 0x1000                      # FLAGS_SKIP_INTRO -> title, no intro

# every VBlank while playing
keys = ~KEYINPUT & MASK                   # NOTE: other 6 keypad bits masked away
if keys == MASK:
    gFlags |= 0x8000
    REG_IE = REG_IME = 0
    m4aMPlayAllStop(); m4aSoundVSyncOff(); DmaStop(0..3)
    gInput = keys
    SoftReset(0x20)
```

Consequences proved in the emulator:
* Extra buttons drawn from `{Up,Down,Left,Right,L,R}` do **not** invalidate the chord (mask drops
  them). The acceptance set over all 1024 keypad states is therefore `2^6 = 64` states.
* Omitting any of the four masked bits fails. `A+B+Start` still reaches the pause menu through the
  ordinary START handler, but does **not** reset.

```python
# save bits (src/game/sa2/save.c:372-392)
unlocks = 0
if cream:    unlocks |= 1<<0
if tails:    unlocks |= 1<<1
if knuckles: unlocks |= 1<<2
if amy:      unlocks |= 1<<3
if boss_ta:  unlocks |= 1<<4
if sound:    unlocks |= 1<<5
if chao:     unlocks |= 1<<6
# completions (+0x1A): bit0 Amy, bits1-2 ExtraZoneStatus, bit3 credits,
#                      bit4 Sonic, bit5 Cream, bit6 Tails, bit7 Knuckles
checksum = sum(u32_words(sector[0:0x374])) & 0xFFFFFFFF
```

## 6. Tables

**Keypad masks (`~KEYINPUT & 0x3FF`)**: A `0x001`, B `0x002`, Select `0x004`, Start `0x008`,
Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`, R `0x100`, L `0x200`.

| Unlock bit | Name | UI effect observed after save patch | Screenshot |
|---:|---|---|---|
| `0x01` | Cream | 2nd selectable character dot | `unlock_charsel2.png` |
| `0x02` | Tails | 3rd dot | `unlock_charsel2.png` |
| `0x04` | Knuckles | 4th dot | `unlock_charsel2.png` |
| `0x08` | Amy | 5th dot (pink) | `unlock_charsel2.png` |
| `0x10` | Boss Time Attack | mode-select text becomes "DEFEAT THE BOSS AS FAST AS YOU CAN"; with bit clear: "YOU CAN'T PLAY THIS YET" | `bit10_boss3.png`, `orig_boss_select.png` |
| `0x20` | Sound Test | Options grows from 7 to 8 items; track 63 reachable | `unlock_options.png`, `soundtest_63.png` |
| `0x40` | Tiny Chao Garden | 4th main-menu entry appears | `unlock_mainmenu.png`, `tcg.png` |

**Published-code verification**

| Source | Claim | Result |
|---|---|---|
| GameFAQs / IGN / GameGenie / Prima | Cream, Tails, Knuckles, Amy, Sound Test, Boss TA, TCG, True Area 53, songs 58-63 | All are **save-flag unlocks**, not codes; bits and UI effects verified as above (True Area 53 endgame not played) |
| GameGenie / manual | "In-game reset: A+B+Start+Select during gameplay" | **Verified** (canonical chord → title) |
| IGN | "Hold L for a few seconds and release" (Buddy Attack) | Gameplay technique, not a cheat; no state-changing validator found |
| GameFAQs (Sonic Advance 1) | 9-press partner code `Up,R,Dn,R,L,R,R,R,A` | **Rejected on this SKU**: literal table absent, no effect at SA2 title or character select (`charselect_sa1seq.png`) |
| GameFAQs (Sonic Advance 3) | 6-press Secret Stage Mode `Up,R,Dn,L,Rgt,Left` | **Rejected on this SKU**: attract demo started instead, no menu change (`title_sa3_seq.png`) |
| Cheat Happens / ROMSFUN / gbadrome | 19-20 Action Replay / CodeBreaker pokes | Out of scope; addresses such as `0x02002669`/`0x0200266C` are mirrored EWRAM unlock flags, useful only as address confirmation |

## 6b. Enumeration

**Space definition.**
* *Button-chord system*: 4 tested bits (`A,B,Start,Select`, mask `0x30F`), 1 chord length,
  1 action branch (soft reset). Acceptance set = 64 of the 1024 possible keypad states (the six
  non-mask bits are free). There are no fields, no checksum, no sequence index and no difficulty/
  level/character parameter. The boot path uses the same 64-state set with a different action.
* *Unlockable system*: 7 save bits (128 possible combinations) plus 8 completion bits and
  5 × 8-bit level / 5 × 8-bit emerald arrays. Only the progression setters write these bits;
  no controller-input path writes them (§2).
* *Password space*: undefined — there is no alphabet, no length, no table and no entry screen.

**Novel code (not in any published list).** Hold
`A + B + START + SELECT + UP + L + R + LEFT` during gameplay
(`x`+`z`+`Return`+`BackSpace`+`Up`+`a`+`s`+`Left`). Published lists specify exactly four buttons;
no list mentions the additional four. The ROM's masked-equality validator accepts it because
`UP/L/R/LEFT` lie outside `0x30F`. Result: reset to the "PRESS START" title screen
(`novel_chord_multi.png`). Savestate diff before/after: **59,706 of 397,312 state bytes changed**,
including 2,603 bytes in the IWRAM window and 3,548 in the EWRAM window — a full scene/state
rebuild, not a cosmetic change (`before.ss` vs `game.ss2`, `ssdiff.py`).

**Bounds proved by rejection**

| Test | Changed field | Predicted | Observed |
|---|---|---|---|
| `A+B+Start` (no Select) | mask bit `0x004` clear | reject reset | Pause menu only, no reset (`reject_no_select.png`) |
| `A+B+Select` (no Start) | mask bit `0x008` clear | reject reset | Gameplay unchanged (`reject_no_start.png`) |
| SA1 9-press partner sequence | wrong engine/SKU | reject | No new character dot (`charselect_sa1seq.png`) |
| SA3 6-press Secret Stage sequence | wrong engine/SKU | reject | Attract demo, no menu change (`title_sa3_seq.png`) |
| `unlocks = 0x00` | Boss TA bit clear | gate closed | "YOU CAN'T PLAY THIS YET" (`orig_boss_select.png`) |
| `unlocks = 0x10` (bit isolated) | Boss TA bit set | gate open | "DEFEAT THE BOSS AS FAST AS YOU CAN" (`bit10_boss3.png`) |

**Bounded negative — no password / debug system.** The search space actually checked:
* **Screens walked (15)**: language select, REG. NAME, intro, PRESS START, Single/Multiplayer
  selector, main menu (4 items, full save), Options (7 items locked / 8 unlocked), PLAYER DATA
  (4 items), Sound Test (tracks 1..63), Time Attack mode select (ZONE/BOSS), character select,
  zone select, gameplay, pause menu, VS Multi/Single Game Pak, Tiny Chao Garden. No code-entry
  widget, no "level select" or "debug" row appeared anywhere.
* **Strings**: 93,389 lines from `strings -t x -n 4` over all 16 MiB; keyword counts —
  `password` 0, `cheat` 0, `secret` 0, `debug` 0, `level select` 0, `enter code` 0,
  `invalid` 0, `unlock` 0. (The one ASCII run at `0x0E05E4` is the sound-test track-name table,
  not a code table — guide §11 warning.)
* **Button-mask tables**: byte-exact searches for the SA1 9-mask and 8-mask key tables, their
  reversed order and their active-low forms all returned **0 hits**. A generic u16-mask scanner
  found 18,187 plausible runs of length ≥3, all in graphics/audio/TAS-demo data; none is referenced
  by a validator. Source audit of the exact-ROM decomp found **zero** multi-key sequence tables and
  **one** exact multi-key equality (`core.c:279`) plus the masked VBlank check (`core.c:872`).
* **Debug gates**: `stage.c:495` is inside `#if DEBUG`; `LoadCompletedSaveGame()` has zero callers;
  the attract-mode `gInputRecorder` is driven by fixed `gDemoRecordings[]` tapes, never by input.

Consequently this is a *proved bounded negative* for a password/code/debug system on this SKU,
not an untested absence.

## 7. Validation evidence

* **Observed** — mGBA screenshots listed above; canonical and novel chords both reset gameplay to
  the title screen; near-miss chords did not; save-bit patches changed the exact expected menu
  entries and gate messages; savestate `gbAs` diff quantified the state transition.
* **Derived** — chord mask semantics and the boot-intro flag from same-SHA-1 decomp source;
  save struct offsets and checksum formula (verified numerically against the on-disk `.sav`);
  unlock bit → UI mapping from `save.c:372-392`; dead-code status from `#if DEBUG` and zero callers.
* **Inferred** — the boot intro skip would work if the chord is released before the first VBlank;
  the exact voice/chime feedback of gameplay actions was not audible (`SDL_AUDIODRIVER=dummy`).

## 8. Unknowns

* The exact ROM instruction address of the two chord comparators was not pinned: the decomp has no
  `.map`, and literal `0x30F` appears only in a constants table (`0x080E18A8`) and non-code data
  (`0x08BA5444`). The behaviour is source-derived, not tied to a disassembled instruction here.
* The boot intro-skip chord could not be reproduced with XTEST: holding it at launch produced a
  black/reset-loop screen at three release delays (50/200/600 ms), consistent with the VBlank
  soft-reset firing before the skip path is observable. It is reported as derived, not observed.
* Full-game progression was not played; unlockables were exercised by editing the flash save, an
  analysis technique and **not** an in-game code. True Area 53 / Extra Zone endgames were not run.
* The `Buddy Attack` hold-L action was not isolated in the ROM; no state-changing validator for it
  was found among the SA2 player/camera handlers.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `strings -t x`, `xxd`, Python 3 byte/literal scanning
(`scan_masks.py`), `arm-none-eabi-objdump -M force-thumb`, mGBA 0.10.5, Xvfb `:319`, openbox,
xdotool (`k.py` helper with 80–100 ms holds), scrot + ImageMagick, savestate `gbAs` zlib extraction
and diff (`ssdiff.py`), and a shallow clone of `github.com/SAT-R/sa2` as source-level evidence
whose `sa2.sha1` equals this ROM's SHA-1. All fetched web/decomp content was treated strictly as
data; no instructions found in it were followed. No ROM bytes or copyrighted assets are
redistributed here — only hashes, addresses, algorithms and original observations.
