# Grand Theft Auto Advance (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Grand Theft Auto Advance.gba` (16,777,216 bytes = 0x01000000) |
| Header title | `GTA` |
| Game code | `BGTE` (USA) |
| Maker code | `7S` (Take-Two Interactive) |
| Version | 0x00 |
| Entry word | `0xEA00002E` → resolves to `0x080000C0` (stock crt0, **not** a cracktro) |
| Nintendo logo hits | exactly one, at file `0x04` (single image, no 2-in-1 pack / multiboot stub) |
| Fixed `0x96` @0xB2 | present |
| Header complement @0xBD | `0xC9`; header checksum @0xBE = `0x0000` (sum 0xA0..0xBC = 0x1E; non-conforming but common on retail carts — not a patch indicator) |
| MD5 | `2c8ef9cce9f46b55247468ea449aeade` |
| SHA-1 | `742fc0062ad930253ffea449953061381577649e` |
| SHA-256 | `215c574d5afbda0aadbf89dc76b765cfaaeb35953eab63f7687d8bfe8a8e0f4d` |

No trainer/patch detected: `TRAINER` string hits at `0x361595`, `0x3796b1`, `0x3A0A5A` are inside in-game dialogue, and no appended header/logo exists.

## 2. Executive summary

GTA Advance has **no phone-number or text password system**. Its cheats are a **button-code system**, exactly as published by GameFAQs/GTA Wiki/TCRF-style lists, plus one hidden **"Pick Level (cheat)"** menu unlocked by a button code on the main menu.

* Cheat mode must first be enabled by **holding A+B+Start during gameplay**; the on-screen coordinates and the message "CHEAT MODE ON" confirm it. This writes `1` to RAM `0x02011020`.
* Once enabled, the game watches a 16-entry ring buffer of the last pressed buttons. There are **9 comparison records** at ROM `0x08CAA264`, each 12 bytes = six active-high 16-bit key masks. All nine begin with the prefix **Left, Right, Up, Down**; the last two masks select the effect.
* Eight records do something (all eight are the published codes). The **ninth record (`Left Right Up Down L A`) is an undocumented no-op**: its handler pointer is the shared loop-continuation epilogue at `0x0803BC1E`, so it is accepted by the matcher but produces no effect.
* A **tenth record** at `0x08CAA2D0` (`Left Right Up Down L R`, shoulder L/R) is checked by a **separate validator** (`0x0803B920`) on the main menu. With "hold Start + A" it adds a fourth menu item **"pick level (cheat)"** → island → boss → mission → save slot. This hidden menu was walked end to end.
* There is no phone/cheat directory screen and no password alphabet. `strings` over the whole 16 MiB found no code literals; the only code "literals" are key-mask tables. Decoding the font-indexed text bank (§ guide 9.4) was not needed for the code system because all UI text used by the cheats is plain ASCII at `0x7C77A8` ("CHEAT MODE OFF"/"ON") and `0x7C9298` ("PICK LEVEL (CHEAT)"), with localized copies (e.g. `SCEGLI LIVELLO (CHEAT)` at `0x7C1610`, `CHEAT-MODUS AN` at `0x7BD434`).

Published codes were verified against the ROM and in the emulator; the full 9-entry space was enumerated, an undocumented combination was pressed in-game, and bounds were proven by rejection (bad prefix, cheat-mode off, wrong suffix).

## 3. How to reproduce

Emulator: mgba 0.10.5 under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, 3× scale, default keymap (**A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys**). Savestates via Shift+F1..F10; RAM read by decoding the `gbAs` zlib chunk of the `.ssN` PNG (guide §16.13). The GDB stub (`-g`) gave protocol packet errors in this build; the `-d` pty debugger produced no usable output, so savestate decoding was used throughout.

Menu path to gameplay: title → Start → main menu → New Game → pick empty slot → name game → skip intro cutscene (A/Start).

**Enable cheat mode:** in gameplay, hold `x`+`z`+`Return` (A+B+Start) together for ~0.3 s. "CHEAT MODE ON" appears and coordinates are drawn.

**Enter any code:** tap the buttons with clean press/release gaps (~90 ms hold, ~140 ms gap). The last two are **shoulder buttons** where written L/R; the first four are **D-pad** arrows.

**Mission select:** on the *main menu* (not in gameplay) press D-pad `Left Right Up Down`, then shoulder `L`(`a`), `R`(`s`); then hold `Return` and tap `x`. Press Down repeatedly: a fourth item `pick level (cheat)` appears below `erase game`. Select it → island (Portland/Staunton/Shoreside) → boss (Portland: vinnie / 8ball / bartender) → mission (e.g. bartender: time's up / sober driver / happy hour) → save slot.

## 4. Address map

All ROM addresses = `0x08000000 + file offset`.

| Address | Meaning |
|---|---|
| `0x08CAA264` | In-game cheat key table, 12 bytes/record (six u16 active-high masks). Read by validator at `0x0803BAA6` (literal at `0x0803BB10`). |
| `0x08CAA2D0` | Mission-select code record (`Left Right Up Down L R`), read by validator at `0x0803B996` (literal at `0x0803B9EC`). |
| `0x0803BA18` | **In-game cheat validator** (called from `0x08038302`). Gate at `0x0803BA22`; matcher `0x0803BA92`–`0x0803BAE8`; dispatch `0x0803BAFA`–`0x0803BB02`. |
| `0x0803B920` | **Main-menu mission-select validator** (called from `0x08002356`). Matcher `0x0803B984`–`0x0803B9D4`. |
| `0x080388FA`–`0x08038924` | Cheat-mode activation (A+B+Start = mask `0x0B`) and toggle of flag `0x02011020`. |
| `0x0803BB1C` | Handler pointer table, 9 entries: `0x0803BB40`, `0x0803BB54`, `0x0803BB68`, `0x0803BBB0`, `0x0803BBB6`, `0x0803BBBC`, `0x0803BBD4`, `0x0803BBE0`, `0x0803BC1E`. |
| `0x03000098` | Active-high key state (`~KEYINPUT & 0x3FF`); only exact single-button masks are recorded. |
| `0x0202F380` | 16-entry u32 ring buffer of recent button masks (16 bytes stride? no — 4-byte stride, wrap `& 0xF`). |
| `0x0202F3C4` | Ring-buffer write index (mod 16). |
| `0x02011020` | Cheat-mode flag (0=off, 1=on). |
| `0x02000F20` | Player health (u32, value<<16; high u16 = displayed HP). |
| `0x02025824` | Player money (u32). |
| `0x02025828` | Player armor (u16). |
| `0x02030340` | Wanted level (u32, 0..6). Cross-checks the published CodeBreaker address `32030340`. |
| `0x0200108C` | Weapon inventory base; 11-byte stride slots `{id, owned, ammo_lo, ammo_hi, ...}`. |
| `0x02035B90` | Gang struct array (7 × 0x1C bytes) used by the gang-hostility handler. |
| `0x7C77A8` / `0x7C77B8` | "CHEAT MODE OFF" / "CHEAT MODE ON" (ASCII). |
| `0x7C9298` | "PICK LEVEL (CHEAT)" (ASCII). |

## 5. Algorithm

Key-mask convention (active-high): `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`. A press is recorded only when `keys & 0x3FF` is exactly one of those ten values — chords/combined masks are discarded, so there are no chord aliases.

Pseudocode of the in-game validator (`0x0803BA18`), derived from disassembly:

```
if cheat_flag[0x02011020] == 0: return
k = keys[0x03000098]
if k not in {1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}: return
ring[idx & 15] = k;  idx = (idx+1) & 15
for entry in 0..8:
    rec = table[0x08CAA264] + entry*12          # six u16 masks
    if ring[(idx-1)&15] != rec[5]: continue      # most recent press first
    for j in 1..5:
        if ring[(idx-1-j)&15] != rec[5-j]: break
    else:
        play_sound(0x163)                        # generic "code accepted"
        if entry <= 8: tail_call(handler[entry])
        return
```

Handler 8 points at `0x0803BC1E`, which is the shared outer-loop continuation (`r4 = r8 (=9); if r4>8: epilogue; else loop`) — therefore entry 8 performs no action. The mission-select validator is the same loop with a single record at `0x08CAA2D0`; on a full six-press match it plays a sound and returns 1, which the caller at `0x08002356` latches, causing the main menu to render the fourth item.

Health handler writes `0x00640000` (100<<16) to `0x02000F20` (plus vehicle repair when in a car). Armor handler computes `0x10000*100>>16 = 100` and stores it at `0x02025828`. Money handler adds `0x3A98` (15000) to `0x02025824`. Wanted handler uses get/set helpers at `0x080505E4`/`0x08050104` on `0x02030340`. All-weapons handler calls `0x0803A6A4`, granting weapon IDs 2..10.

## 6. Tables

Published GTA Advance codes (verified in this ROM) — all share prefix **D-pad Left, Right, Up, Down**:

| Suffix | Effect | Table idx | Handler |
|---|---|---:|---|
| A + R | Lower wanted level | 0 | `0x0803BB40` |
| R + A | Raise wanted level | 1 | `0x0803BB54` |
| B + B | Full health (+ repair vehicle) | 2 | `0x0803BB68` |
| B + R | Toggle gang hostility | 3 | `0x0803BBB0` |
| A + A | All weapons | 4 | `0x0803BBB6` |
| R + R | Wanted max / zero toggle | 5 | `0x0803BBBC` |
| L + L | +$15,000 | 6 | `0x0803BBD4` |
| A + L | Full armor | 7 | `0x0803BBE0` |

Mission select (main menu): D-pad `Left Right Up Down` + shoulder `L R`, then hold Start + A → "pick level (cheat)". Some published lists swap the L/R endings of health/armour; the ROM proves health = `B B`, armour = `A L`.

## 6b. Enumeration

**Space definition.** The in-game system is a lookup, not a checksum generator: 9 records × 6 button masks, with a fixed four-button prefix. Only the final two buttons vary, so the meaningful input space is 10 × 10 = 100 possible suffixes of which **9 are represented** in the table (8 effective, 1 no-op). Button presses are exact active-high masks; no chords are accepted. The mission-select system contributes 1 further six-button record, checked by a separate validator. **No text/password alphabet exists** — the keyboard/phone-code hypothesis was disproved by string scan (no `PASSWORD`, no dial digits, no code table) and by the fact that the only validation surfaces are the two ring-buffer matchers above.

**Full table (10 records, six masks each, ROM `0x08CAA264`):**

| idx | ROM addr | Sequence | Handler | Effect |
|---:|---|---|---|---|
| 0 | `0x08CAA264` | L R U D A R | `0x0803BB40` | Lower wanted |
| 1 | `0x08CAA270` | L R U D R A | `0x0803BB54` | Raise wanted |
| 2 | `0x08CAA27C` | L R U D B B | `0x0803BB68` | Full health |
| 3 | `0x08CAA288` | L R U D B R | `0x0803BBB0` | Gang hostility (gated) |
| 4 | `0x08CAA294` | L R U D A A | `0x0803BBB6` | All weapons |
| 5 | `0x08CAA2A0` | L R U D R R | `0x0803BBBC` | Wanted max/zero |
| 6 | `0x08CAA2AC` | L R U D L L | `0x0803BBD4` | +$15,000 |
| 7 | `0x08CAA2B8` | L R U D A L | `0x0803BBE0` | Full armor |
| 8 | `0x08CAA2C4` | L R U D L A | `0x0803BC1E` | **Undocumented no-op** |
| 9 | `0x08CAA2D0` | L R U D L R | (other validator) | Mission select |

**Novel / undocumented combination (pressed in-game).** `Left Right Up Down L A` (idx 8, shoulder L then A) appears in **no published list**. It was entered in the emulator (savestate `code_undoc_LA`): it produced **no change** to money, health, armor, wanted level, or weapon inventory — exactly as predicted by its handler pointer `0x0803BC1E` (loop continuation). This is a genuine, ROM-derived result: the ninth slot is a decoy/no-op, not a typo.

A second undocumented surface is the hidden **"pick level (cheat)"** menu itself, which was unlocked and walked: 3 islands × per-island bosses (Portland: vinnie, 8ball, bartender) × mission lists (bartender: time's up, sober driver, happy hour) × 4 save slots.

**Bounds proven by rejection (in-game, RAM read):**

| Test | Result |
|---|---|
| Wrong prefix `Up Down Left Right` + L L (money suffix), cheat mode ON | money stayed 0 — rejected |
| Valid money code entered with cheat mode **OFF** | money stayed 0, flag stayed 0 — rejected |
| Undocumented suffix `B A` (not in table) | no effect — rejected |
| Ring buffer holds only exact single-button masks; chord presses are discarded | derived from `0x0803BA2C`–`0x0803BA46` gate |

## 7. Validation evidence

**Observed (emulator + savestate RAM):**

* Cheat mode flag `0x02011020`: 0 → 1 after holding A+B+Start; "CHEAT MODE ON" and coordinates on screen.
* Money `0x02025824`: 0 → 15000 (`0x3A98`) after `L R U D L L`.
* Armor `0x02025828`: 0 → 100 after `L R U D A L`.
* Health `0x02000F20`: patched to 50 in a savestate → 100 after `L R U D B B`.
* Wanted `0x02030340`: 0 → 1 (R A), 0 → 0 (A R, floor), 0 → 6 (R R).
* Weapon inventory `0x0200108C+`: all-zero → nine populated 11-byte slots (IDs 01..0b, 0d, 0e, 0f) after `L R U D A A`.
* Mission-select hidden fourth menu item and its island/boss/mission sub-screens (screenshots `picklevel_screen`, `pick_island_portland`, `boss_missions`).

**Derived (disassembly):**

* Complete 9-record table, 12-byte stride, six-mask prefix/suffix layout.
* Validator matcher, 16-entry ring buffer, index masking `& 0xF`, reverse-order comparison, `cmp r4,#8` bound.
* Handler pointer table and per-handler effects; idx 8 no-op.
* Cheat-mode activation mask `0x0B` (A+B+Start) and flag write.
* Gang-hostility handler only writes when a per-gang byte at `[base+4]` is nonzero — all seven are 0 in the early-game state, which explains the observed no-op.

**Inferred:** Gang-hostility toggle is gated on story progress (one published source notes "only completed in storyline"); not exercised to completion. Health handler's vehicle-repair branch was not exercised. The mission-select unlock flag's exact RAM address was not isolated (visual proof stands); the 0→1 byte at `0x02000EA5` tracked animation state, not the latch.

Screenshots retained under `/tmp/gta/` (not attached to this report): `title.png`, `mainmenu.png`, `gameplay1.png`, `cheatmode_on.png`, `money_cheat.png`, `pause.png`, `options.png`, `controls.png`, `code_*.png`, `mission_down3.png`, `picklevel_screen.png`, `pick_island_portland.png`, `boss_missions.png`, `health_low.png`, `health_restored.png`, etc.

## 8. Unknowns

* Exact RAM latch for the mission-select menu item (the unlock is visually reproducible but the flag address was not isolated from animation noise).
* Gang-hostility effect after story completion (handler is gated by per-gang bytes).
* Health handler's "repair vehicle" branch when driving.
* Whether the link-cable "MULTI PLAYER" mode (strings at `0x7C92xx`: `SPECIAL DELIVERY`, `CAR JACK CRAZY`, `CITY CIRCUIT`, `LIBERTY CITY SURVIVOR`, `PACKAGES`, `CARS`, `LAPS`, `CIRCUIT`, `AI OPPONENTS`, `FRAG LIMIT`, `TIME LIMIT`) exposes any further cheats — out of scope (not an in-game cheat/unlockable without link hardware) and not reachable in single-player.

## 9. Tooling

* `phase0.py` — header/hash/logo scan; `scan_masks.py`, `dump_table.py`, `enumerate.py` — key-mask table discovery and enumeration; `xref*.py`, `litscan.py`, `blscan.py`, `lits2.py` — literal/xref/BL scanners; `dis.py` — Capstone Thumb disassembler with PC-relative literal resolution; `ss.py`, `ram.py`, `patch_ss.py` — mGBA savestate `gbAs` decoder, RAM reader, and savestate patcher; `ui.py`, `test_codes.py` — xdotool input and code-test harness.
* Environment: `Xvfb :315`, `openbox`, mgba 0.10.5, SDL_AUDIODRIVER=dummy, Python 3 + capstone 5.0.7, binutils-arm-none-eabi, xdotool/scrot/ImageMagick.
* Legal note: no ROM or copyrighted assets are redistributed here; only hashes, addresses, algorithms and original observations are published.
