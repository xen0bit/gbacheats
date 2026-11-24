# Tom Clancy's Splinter Cell (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Item | Value |
|---|---|
| File | `Tom Clancy's Splinter Cell.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `SPLINTERCELL` |
| Game code | `AO4E` |
| Maker | `41` |
| Fixed byte | 0x96 (valid) |
| Version | 0 |
| Complement / checksum | 0x52 / 0x0000 |
| Entry word | `0xEA1FF4CA` → branch to `0x0807FD330` (non-standard crt0 location; the bytes at 0xC0 are not the entry point) |
| MD5 | `d1ebcafb73e5160b0b3fd0c98f27456e` |
| SHA-1 | `f49348fc14a3ea8215e4fc76e140aa50427cfe6d` |
| SHA-256 | `63f365d654e4f46bb42b502271373345365eb843d614299930e3e61470a6f602` |

**Phase 0 result:** one GBA header only; no appended image, no multiboot stub, no
scene cracktro/trainer. This is the US retail revision (`AO4E`), **not** the PAL
debug prototype documented by Hidden Palace.

## 2. Executive summary

**Bounded negative: this retail ROM has no in-game cheat system.** There is no
password screen, no button-code matcher, no hidden/debug menu, and no code-driven
unlock. The only "code-like" input in the whole game is a **3-character save-slot
name field** (default `AAA`), which is a label, not a validator — no comparison
against its buffer exists anywhere in the ROM.

Every published "cheat" for this SKU is an external **CodeBreaker / GameShark /
Action Replay** patch (out of scope by the engagement rules). The only
developer-intended unlockables are the **bonus missions**, earned by ordinary
gameplay (completion percentage, opening all safes, or a GBA–GameCube link); a
"SECRET" mission-name slot exists but is permanently gated behind those
achievements and cannot be entered.

A separate **PAL debug prototype** does contain an L-button level select, a
Cheat Manager and quickwarp, but those features are **absent from this ROM**:
all four documented gates were pressed in the emulator and produced no effect,
and none of their menu strings exist in the image in six encodings.

Because no validator exists, no code could be minted; §6b gives the bounded
negative with search counts instead.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (SDL), `SDL_AUDIODRIVER=dummy`, Xvfb `:317` + openbox,
  `-3` scale. **Run mGBA under a renamed binary** — other agents in this workspace
  run `pkill -x mgba` in loops, which otherwise kills this session's emulator.
* Keymap (verified): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold ≥0.15 s for menu presses.
* Path walked (all screens, with screenshots in `/tmp/splintercell/`):
  1. Ubi Soft intro → language select (US/ES/FR flags) → A = English.
  2. Main menu: **SELECT GAME**, **OPTIONS**.
  3. SELECT GAME → three slots (`---`) → New → **3-character name entry**
     (Up/Down cycles A→B→…; A advances/commit) → slot shows `ABA`.
  4. Start new game → mission intro T'BILISI → gameplay.
  5. Start → **INVENTORY** (VISION / NORMAL / WEAPON / PISTOL / ABORT MISSION).
     L → **MISSION OBJECTIVES**. Start → back. ABORT MISSION → YES.
  6. **SELECT MISSION** → 14 cursor positions; positions 0–1 show TRAINING and
     T'BILISI, positions 2–13 show black/grey thumbnails (locked). A on a locked
     mission does nothing.
  7. Main menu → OPTIONS → **MUSIC / SFX / CREDITS**.
* Debug gates pressed (no effect on this ROM): L on title/language screen;
  L, R and Select in INVENTORY / MISSION OBJECTIVES.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Address | Meaning |
|---|---|
| `0x080797A4` | input init: reads `0x04000130`, stores active-high held mask at `[r0+4]` |
| `0x080797CC` | input update: `pressed = held ^ prev` at `[r3+6]`, `held = ~KEYINPUT` at `[r3+4]` |
| `0x0807FE20` / `0x0807FE28` | text `OPTIONS` / `SELECT GAME` |
| `0x0807FE9C` | text `SELECT MISSION` |
| `0x0807FFB0`–`0x08080028` | mission-name pointer table (TRAINING, T'BILISI, POLICE STATION, DEFENSE MINISTRY, CIA, CASPIAN OIL REFINERY, SHIPYARD, NUCLEAR PLANT, ABATTOIR 1, ABATTOIR 2, SECRET) |
| `0x08080B2C` / `0x08080B3C` | text `INVENTORY` / `MISSION OBJECTIVES` |
| `0x080810F4`–`0x0808119C` | unlock-condition text block: `TO UNLOCK`, `WITH 4% SUCCES RATE`, `COMPLETE MISSION 2 TO 3`, `IN THE GAME`, `UNLOCK ALL SAFES`, `ON NINTENDO GAMECUBETM`, `COMPLETE MISSION 2 AND 3`, `BONUS` |
| `0x080811C0` onward | localisation/text record table `{u32 text_ptr, u16 len, u16 0}` |
| `0x0846C842`, `0x086D8E4C` | save magic bytes `00 22 44 55` (data, not code) |
| `0x02FFFF...` / `0x0300767A`, `0x030076FA` | save data mirrored in IWRAM (observed in savestate); 3-char name at `0x0300767A` |

No password table, no alphabet table, no mask sequence, no validator and no
debug-menu renderer were found.

## 5. Algorithm (input path; no validator exists)

The only general input consumer is the standard GBA joypad reader:

```
init(0x080797A4):
  held[struct+4] = ~KEYINPUT & 0x3FF      ; active-high mask
  pressed[struct+6] = 0
  ptr[struct+8] = 0

update(0x080797CC):
  cur = ~KEYINPUT & 0x3FF
  pressed = cur ^ held                   ; edge-triggered
  held = cur
```

There is **no progress index**, **no expected-mask array**, and no comparison of
`pressed`/`held` against a stored sequence in any reachable code path. The
3-character field is consumed only as a save-slot label.

Save format (from the 512-byte `.sav`, derived): three slots of 0x88 bytes at
`0x00`, `0x88`, `0x110`; each begins `{u8, u8, u16 checksum, u32 magic 0x55442200,
u32, u8, char name[3]}` followed by all-zero progress bytes on a fresh file.
The unlock bitfield is not populated on a new save; published cheat-device
literals point at the IWRAM mirror around `0x03007700` (inferred from patch
addresses, **not** an in-game code and **not** independently verified).

## 6. Tables

* **Mission slots (observed):** 14 selectable positions; #0 TRAINING, #1
  T'BILISI unlocked at start, #2–#13 locked (black thumbnails). Name table
  contains a further `SECRET` slot (`0x0807FFA8`).
* **Unlock conditions (observed text, `0x080810F4`–`0x0808119C`):**
  `COMPLETE MISSION 2 TO 3 … WITH 4% SUCCES RATE`, `COMPLETE MISSION 2 AND 3`,
  `UNLOCK ALL SAFES`, `ON NINTENDO GAMECUBETM`, `BONUS`. These are displayed in
  the results screen; they are gameplay achievements, not typed codes.
* **Published codes (recon, all out of scope):** CodeBreaker
  `83007700 BFFF` (open all missions), `8300770A 0999` (ammo), `3300766C 0000`
  (alarms), `83007710 0000` / `33007712 0000` / `33007714 0000` (statistics);
  GameShark `1203F704 000001AF`, `0300770A 00000090`, `0300766C 00000000`;
  Action Replay master `1f788eb1 36f03524 …`. None is a keyboard-enterable code.

## 6b. Enumeration

**Space definition:** no code space exists. The nearest candidate surface, the
3-character save name, has alphabet A–Z (26 symbols) × 3 = 26³ = 17,576 possible
strings, but its consumer is a display label — enumerated `strcmp`/`memcmp`
scan found **zero** comparisons against that buffer, so none of those 17,576
values is "accepted" or "rejected" by a validator. It is excluded from the cheat
space per guide §16.2b.

**Validator model:** N/A — no validator found; the bounded negative below is the
deliverable in place of a novel code.

**Novel code:** none possible. No published or unpublished in-game code is
accepted by this ROM, so the §0.2 "mint a novel code" deliverable is replaced by
the bounded negative with the counts below (per the engagement brief).

**Bounds proven by rejection / gate tests (Observed):**
* L on title/language screen — no screen change, no flag change (screenshot
  `s11_L.png`).
* R in INVENTORY — no change (`s23_Rinv.png`).
* Select in MISSION OBJECTIVES — no change (`s25_SelInv.png`).
* A on a locked mission — no change (`s30_lockedA.png`).
* All four prototype debug gates therefore produce in-game *rejection* (no-op).

**Search space checked (counts, Derived/Observed):**
1. Screens walked: **10** distinct states (intro, language, main menu, save slots,
   name entry, gameplay, INVENTORY, MISSION OBJECTIVES, abort-confirm, SELECT
   MISSION, OPTIONS) — every reachable menu entry visited.
2. Strings: **152,857** ASCII strings extracted. Keyword hits in the whole 8 MiB,
   case-insensitive: `password` 0, `cheat` 0, `debug` 0, `level select` 0,
   `cheat manager` 0, `invincib` 0, `god mode` 0, `unlimited` 0, `infinite` 0,
   `press l/r` 0, `master code` 0, `code generator` 0, `enter code` 0,
   `invalid code` 0.
3. Cross-encoding search for 7 debug-menu strings (`LEVEL SELECT`, `CHEAT
   MANAGER`, `INVINCIBILITY`, `DEBUG MENU`, `MISSION SELECT`, `QUICKWARP`,
   `TELEPORT`) in ASCII, lowercase, UTF-16LE/BE, XOR 0x20, and +0x20: **0 hits**.
4. Button-code mask scan: Konami-style sequences in u16/u8, active-high and
   active-low, with and without a trailing Start — **12 pattern variants × 0
   hits** in 8,388,608 bytes.
5. Input-handler analysis: **2** joypad routines (`0x080797A4`, `0x080797CC`);
   **0** progress-index/mask-array comparisons.
6. `SECRET` occurrences: **2** (`0x0807FFA8` English mission name,
   `0x083DD8` Spanish `SECRETO`) — both localised mission labels, not a code.
7. "PASS CODE" strings (e.g. `0x082AF4`, `THE PASS CODE WILL BE ON A`): gameplay
   hints for finding a guard who carries a door code — not a cheat surface.

This is a **no-system** negative (guide §16.3 case 1) for the retail `AO4E` SKU,
closed by screen enumeration plus the counts above. The gated debug features are
a **separate-ROM** finding, not a gated feature of this image.

## 7. Validation evidence

* **Observed:** all screenshots and key presses listed in §3; 3-char entry
  behaviour (Up changes A→B, A advances); save file `sc.sav` structure;
  IWRAM save mirror in decompressed mGBA `gbAs` state.
* **Derived:** input-handler disassembly; string/pattern scan counts; mission-name
  pointer table parse; entry-word target `0x0807FD330`.
* **Inferred:** save-slot field layout and the meaning of published cheat-device
  patch addresses; GameFAQs unlock descriptions (4% vs the walkthrough's 60% is
  unreconciled — report the ROM string, not the wiki).

## 8. Unknowns

* The exact numeric completion threshold for bonus missions (ROM text says `4%`,
  the GameFAQs walkthrough says `60%`); not exercised because it requires
  finishing missions.
* Whether the `SECRET` mission slot can ever be selected after all achievements;
  only its locked state was observed.
* A savestate patch of the suspected unlock field was attempted and rejected by
  mGBA, so the unlock bit offset is not RAM-verified.

## 9. Tooling

`strings`, `xxd`, `python3` (Capstone 5.0.7 for literal/BL scans),
`arm-none-eabi-objdump -M force-thumb`, mGBA 0.10.5 under Xvfb :317,
`xdotool`, `scrot`, ImageMagick, zlib savestate (`gbAs`) decoder.
Scripts: `/tmp/splintercell/{scanlit.py,finalscan.py,key.py,
patchstate.py}`. No ROM or copyrighted asset is redistributed; only addresses,
hashes and derived findings are published.

## 10. Legal note

Analysis only. No ROM image, extracted graphics, music, or game text are
redistributed by this report.
