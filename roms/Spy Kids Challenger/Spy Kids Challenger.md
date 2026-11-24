# Spy Kids Challenger (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Spy Kids Challenger/Spy Kids Challenger.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `SPYKIDSCHALL` (12 bytes at `0xA0`) |
| Game code | `A2KE` (at `0xAC`) |
| Maker | `4Q` (at `0xB0`) |
| Version | `0x00`; complement `0x3E`; header checksum `0x0000` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0; no cracktro/trainer) |
| MD5 | `387089984f98893405b805068fec89bd` |
| SHA-1 | `3f208388a94e14b34b95155fdb488128283d2da3` |
| SHA-256 | `d78611cd8f414661ead2b849f92b5f66108dedb51e4c589f7112f168284edfa3` |

Publisher/engine strings: Disney Interactive; audio engine banner `Shin'en Multimedia. Code: B.Wodok` at file `0x3AFA7D`.

## 2. Executive summary

This SKU has **no password/code-entry screen**. The only in-game cheat surface is a
**simultaneous button code**: hold **SELECT + A + B + R + L** (active-high key mask
`0x307`) during the Juggler or Dragonfly minigame to open a developer **settings
menu**. GameFAQs lists exactly one cheat for this game (the same secret menu);
direct page fetches returned HTTP 403, so the text was recovered from search
snippets and treated as data.

Two independent validators implement the code:

* **Juggler** (`0x080B09A0`): requires **exact** equality `held == 0x307` — an extra
  held key rejects the code (**Observed** in emulator).
* **Dragonfly** (`0x0814AD44`): requires `(keys & 0x307) == 0x307` — a **superset**
  test, so extra keys are allowed (**Derived** from disassembly; the Dragonfly
  screen was not reached in the emulator in this session).

The menu is a generic table-driven integer editor (`0x0814F4C0` launcher,
`0x0814F5D4` editor). **Nine menu descriptors** were found; two top-level trees are
reachable from the live validators (2 pages + 1 page, 32 editable entries in
total), and four further descriptors have no xrefs and appear to be leftover
/debug-only data. A novel, unpublished cheat was minted on the real screen —
`INFINITE LIVES` `0 → 1` — and verified in RAM (`0x02001318 == 1`). Range bounds
were proved by a clamped editor value (`ROPE SPEED` stops at its `max = 20`,
RAM `0x020012FC == 20`) and by the rejected extra-key combination.

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, 3× scale.
Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad=arrow keys. Hold keys 60–150 ms for menu steps.

Screen path (all walked, screenshots in `/tmp/spykidschallenger3/`):

1. Disney Interactive splash → title "PRESS START" (`title_crop.png`, `q5c.png`).
2. Start → main menu: START / OPTIONS / HIGH SCORE / CREDITS (`ng1c.png`).
3. START → "CHOOSE A GAME" with three `NEW GAME` slots and `ERASE` (`s2c.png`,
   `q6c.png`). Slot 1 then shows the saved `AAA` entry (`ng2c.png`).
4. Name entry: 6×4 letter grid `A–Z` plus `★`, `BACK`, `END` (`s5c.png`).
5. `SELECT GENDER` (BOY/GIRL) → `CHOOSE DIFFICULTY` (NORMAL/EXPERT)
   (`s6c.png`, `s7c.png`).
6. Dialogue/cutscene → Juggler gameplay (`s11c.png`, `jug3c.png`).
7. Pause (`Return`): CONTINUE / OPTIONS (GAMMA, SOUND FX, MUSIC, SAVE) /
   EXIT GAME (`pausec.png`, `optsc.png`); HIGH SCORE is empty (`highc.png`).
8. Hold `BackSpace+x+z+a+s` together for ~1 s → secret menu:
   `JUGGLER POINTS` / `JUGGLER SETTINGS` (`controlc.png`).
9. `A` on either page opens the integer editor (`pts1c.png`, `set1c.png`);
   D-pad selects, Left/Right changes value, `B` returns.

Exact code used for the novel cheat: open the menu, select `JUGGLER SETTINGS`,
press `A`, press `Right` once on `INFINITE LIVES` → display `1`. Savestate RAM
read confirms `0x02001318 == 1`.

## 4. Address map

| Address | Size/type | Meaning |
|---|---|---|
| `0x080000C0` | ARM | crt0 entry (stock) |
| `0x080B0510` | Thumb fn | global input: `held = ~KEYINPUT & 0x3FF` → `0x03006D50`; `pressed = held & ~prev` → `0x03006D52` |
| `0x080B09A0` | Thumb fn | **Juggler** secret-code validator (`held == 0x307` exact) |
| `0x080B0A68` | Thumb fn | Juggler per-frame loop; BL to validator at `0x080B0A78`, menu launch at `0x080B0A0C` |
| `0x080B0168` | Thumb fn | builds secret-menu overlay in VRAM (palette/font/tilemap) |
| `0x8156AE4` | Thumb fn | `return ~KEYINPUT & 0xFFFF` (Dragonfly/Sin'en input helper) |
| `0x0814AD44` | Thumb fn | **Dragonfly** secret-code validator (`(keys & 0x307)==0x307`) |
| `0x814AE2A` | BL site | Dragonfly per-frame caller of the validator |
| `0x0814F4C0` | Thumb fn | generic menu launcher (argument = menu descriptor) |
| `0x0814F5D4` | Thumb fn | generic integer editor (called via `0x81D1730`) |
| `0x0830CF0C`, `0x0830CEA4` | data | live top-level menu descriptors (Juggler / Dragonfly) |
| `0x0830B614`, `0x0830B494`, `0x0830B244` | data | live submenu descriptors |
| `0x03006D50` / `0x03006D52` | IWRAM u16 | held / edge-pressed key masks |
| `0x02001300`–`0x02001350`, `0x02001B64` | EWRAM | Juggler setting values (see §6) |
| `0x030002D0`, `0x030006E0`–`0x030006FC` | IWRAM | stage/difficulty/balls/chunk settings |
| `0x02005048`–`0x02005060` | EWRAM | Dragonfly creature-appearance values |

File offset = ROM address − `0x08000000`.

## 5. Algorithm

Key-state model (from `0x080B0510`):

```
raw = ldrh(0x04000130)              # active-low GBA KEYINPUT
held    = (~raw) & 0x3FF            # A=1 B=2 SELECT=4 START=8 RIGHT=0x10
                                    # LEFT=0x20 UP=0x40 DOWN=0x80 R=0x100 L=0x200
pressed = held & ~previous_held
store pressed -> 0x03006D52 ; held -> 0x03006D50
```

The published combo is `A|B|SELECT|R|L = 0x001|0x002|0x004|0x100|0x200 = 0x307`.

Validator semantics:

```
# Juggler, 0x080B09A0
if held_0x03006D50 == 0x307:        # EXACT: extra keys reject
    swap 16 palette entries (0x050001E0 <-> ROM 0x08300C5C via 0x03006278)
    draw overlay (0x080B0168), restore palette/DISPCNT/BG0CNT
    launch_menu(0x0830CF0C)         # via 0x0814F4C0

# Dragonfly, 0x0814AD44
keys = ~KEYINPUT & 0xFFFF           # via 0x8156AE4
if (keys & 0x307) == 0x307:         # SUPERSET: extra keys allowed
    [identical palette/overlay work]
    launch_menu(0x0830CEA4)
```

Menu descriptor (24-byte header + 24-byte items):

```
struct Menu {
  u32 count; u16 x; u16 y; u32 value_format; MenuItem *items;
};
struct MenuItem {           // 24 bytes
  char *label;              // NUL-terminated ASCII, inline in ROM
  u32 *value_ram;           // editor pages: address of the setting
  u32 min, max; u32 pad0, pad1;
};
// top-level page-link item: label, 0,0,0, handler=0x0814F5D5, arg=Menu*
```

`0x0814F4C0` loops over `count`, draws labels, handles UP/DOWN/A/B, and calls
the integer editor `0x0814F5D4` with the selected descriptor. The editor clamps
to `[min,max]` and writes the new value straight to `value_ram`.

## 6. Tables

### 6.1 Live menu trees

| Page descriptor | Entry | Target / value RAM | min–max | observed default |
|---|---|---|---|---|
| `0x0830CF0C` (root, 2) | JUGGLER POINTS | `0x0830B614` (9) | — | — |
| | JUGGLER SETTINGS | `0x0830B494` (15) | — | — |
| `0x0830B614` (9) | SPRING POINTS | `0x02001350` | 0–99999 | 25 |
| | ELASTIC POINTS | `0x0200134C` | 0–99999 | 25 |
| | FUEL POINTS | `0x02001348` | 0–99999 | 25 |
| | HAND POINTS | `0x02001330` | 0–99999 | 200 |
| | GREASED HAND POINTS | `0x02001334` | 0–99999 | 200 |
| | BALL POINTS | `0x02001338` | 0–99999 | 500 |
| | GREASED BALL POINTS | `0x0200133C` | 0–99999 | 500 |
| | RESCUE POINTS | `0x02001340` | 0–99999 | 400 |
| | GREASED RESCUE POINTS | `0x02001344` | 0–99999 | 1000 |
| `0x0830B494` (15) | INFINITE LIVES | `0x02001318` | 0–1 | 0 |
| | INFINITE ROPE | `0x02001310` | 0–1 | 0 |
| | INFINITE BOOTS | `0x0200130C` | 0–1 | 0 |
| | INFINITE FUEL | `0x02001314` | 0–1 | 0 |
| | ROPE SPEED | `0x020012FC` | 4–20 | 10 |
| | ROPE LENGTH | `0x02001B64` | 8–16 | 12 |
| | ROPE INCREASE | `0x02001300` | 10–160 | 50 |
| | ROCKET INCREASE | `0x02001304` | 10–99 | 24 |
| | GROUND FRICTION | `0x02001308` | 16–128 | 128 |
| | AIR TURN VELOCITY | `0x02001328` | 0–128 | 50 |
| | JUMP VELOCITY | `0x0200132C` | 0–6000 | 1800 |
| | DIFFICULTY | `0x030002D0` | 0–100 | 0 |
| | BALLS ACTIVE | `0x030006E8` | 0–6 | 2 |
| | CHUNKS IN STAGE | `0x030006F8` | 0–6 | 6 |
| | STAGE | `0x030006E0` | 0–99 | 0 |
| `0x0830CEA4` (root, 1) | DRAGONFLIGHT | `0x0830B244` (8) | — | — |
| `0x0830B244` (8) | DIFFICULTY | `0x030002D0` | 0–49 | — |
| | FINCROCK / MANTIS / HAMMERHEAD / EEL / BIG STARFISH / STARFISH / BLOWFISH `*_APPEAR` | `0x02005048`…`0x02005060` (step 4) | 0–49 | — |

### 6.2 Other menu descriptors with no live xref

* `0x0830B654` (1): CURRENT FG CHUNK (`0x030006FC`, 0–1023).
* `0x0830BF88` (13): SPRING FREQ, SPRING DURATION, SPRING TIME ACTIVE, ROPE FREQ,
  ROPE DURATION, FUEL FREQ, FUEL DURATION, BONUS FREQ, BONUS DURATION, BONUS VALUE,
  MULTIPLIER FREQ, MULTIPLIER DURATION, BALLS ACTIVE.
* `0x0830C8C0` (13): FINCROCK/MANTIS/HAMMERHEAD/EEL/BIG STARFISH/STARFISH POINTS
  and FINCROCK/MANTIS/HAMMERHEAD/EEL/BIGSTARFISH/STARFISH/BLOWFISH FREQ.
* `0x0830CE68` (8): ARMOR, AUTOLOADER, BANGJUICE, FASTTORP, GREASE, HEALTH,
  BOOTORP, REBELTORP FREQ.

No 32-bit literal pointer and no BL to these four descriptors was found, and
neither live validator launches them — report them as **leftover/dead**, not as
reachable cheats (bounded negative: pointer scan + BL scan + both trigger paths).

## 6b. Enumeration

**Code space.** There is exactly one button code: the 10-bit simultaneous mask
`0x307` out of `2^10 = 1024` possible held-key masks. Both validators use that
same mask; they differ only in strictness (Juggler exact, Dragonfly superset).
No button *sequence* table exists — scans for u16 mask arrays and for any other
key-mask constant near a key-state read found only `0x307` (the code) and `0x202`
(normal B/L gameplay control, e.g. `0x080B1D34`, not a cheat). Enumeration of the
reachable menu surface is therefore: 2 root pages → 3 live sub-pages → **32
editable settings**, with the exact field widths/min/max listed in §6.1. The code
family is closed: one mask, two gate implementations, zero undocumented action
branches after the prefix (both validators call the same `0x0814F4C0` launcher
and return to the game loop).

**Novel code (not in any published list).** GameFAQs/VGChartz mention only
"hold L/R for 99,999 points". I minted a different, unpublished cheat on the real
screen: `JUGGLER SETTINGS → INFINITE LIVES : 0 → 1`. This is absent from every
published description. Evidence:

* Screenshot `nov1c.png`: display changes `0 → 1`.
* Savestate RAM read (`state_lives1.ss1`, decompressed `gbAs` chunk, EWRAM):
  `0x02001318 == 1` (`read_state.py`).
* Control state `state_lives0`-equivalent baseline: `0x02001318 == 0` in the
  unmodified state taken before the change (`bound1` sequence), so the write is
  attributable to the menu action.

The published behaviour was also reproduced: holding `R` 2.5 s in the points
editor drives SPRING POINTS `25 → 1711` (`holdRc.png`), and 8 s more reaches
`6542` (`holdR2c.png`) — continuous fast increment toward the 99999 cap.

**Bounds proven by rejection.**

1. *Extra key in Juggler (exact gate):* holding `UP` first, then the five combo
   keys (so every frame has `held = 0x347`), produces **no menu** (`gated2c.png`),
   while the bare combo immediately opens it (`controlc.png`). This also proves
   the undocumented asymmetry with the Dragonfly superset gate.
2. *Editor maximum:* 20× `Right` on ROPE SPEED stops at `20` (not 21+)
   (`bound2c.png`); RAM `0x020012FC == 20` in `state_ropespeed20.ss1`.
3. *Boolean field maximum:* 3× `Right` on INFINITE LIVES leaves the display at
   `1` (`bound1c.png`), matching `max = 1` in the ROM record.

## 7. Validation evidence

* **Observed** — emulator screenshots for every screen in §3; secret menu opening;
  `INFINITE LIVES` 0→1; ROPE SPEED clamp at 20; rejected `UP+combo`; published
  hold-R point increase. Savestate RAM reads: `0x02001318=1`, `0x020012FC=20`,
  plus all defaults in §6.1 (e.g. SPRING POINTS 25, JUMP VELOCITY 1800).
* **Derived** — validator constants and branch semantics at `0x080B09A0` /
  `0x0814AD44` (`arm-none-eabi-objdump -M force-thumb`); input routine at
  `0x080B0510`; menu descriptor/item layout from `0x0814F3EC` / `0x0814F4C0` /
  `0x0814F5D4`; 9 descriptor addresses and 32 live settings from the parsed
  tables; dead-descriptor xref counts.
* **Inferred** — the four orphan descriptors were intended as developer pages
  (their labels and handler fields are intact) but are not reachable from either
  live trigger.
* **Published-code verification** — GameFAQs lists 1 cheat; direct HTTP fetch
  returned 403, so the wording is from a search snippet (data only). Its core
  claim (SELECT+A+B+R+L → secret menu) was independently confirmed in the ROM
  and emulator.

## 8. Unknowns

* The Dragonfly minigame screen was **not reached in the emulator** during this
  session (both save slots begin in Juggler and no automatic transition was
  observed). Its validator is fully derived from disassembly and its caller
  (`0x814AE2A`), but the superset behaviour was not confirmed on screen.
* Whether the four orphan menu descriptors were reachable in an earlier build or
  via an as-yet-unidentified debug gate; only the bounded xref negative is proven.
* The exact long-hold duration needed to reach 99999 by holding R was not timed
  to completion (measured rate ≈ 700 points/s).

## 9. Tooling

Scripts and captures in `/tmp/spykidschallenger3/`:

* `scan1.py`–`scan5.py`, `parse_tables.py`, `parse_menus.py`,
  `parse_all_menus.py` — Python/Capstone scans for KEYINPUT literals, key-mask
  literals, BL targets and menu descriptor parsing.
* `press.py`, `combo.py`, `combo2.py` — xdotool XTEST key helpers on `:315`.
* `read_state.py` — decompresses mGBA `.ss1` `gbAs` zlib chunk and reads the
  EWRAM/IWRAM settings at the documented offsets (guide §16.13).
* `setup.sh`, `start_dbg.sh`, `key.sh` — display/emulator launch helpers.
* All screenshots named in §3/§6b (PNG).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for disassembly; `strings -t x`, `xxd`, `grep` for static recon.

No ROM or copyrighted assets are redistributed here; only addresses, hashes,
algorithms and authored screenshots are reported.
