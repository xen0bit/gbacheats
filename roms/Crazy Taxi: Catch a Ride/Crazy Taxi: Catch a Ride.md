# Crazy Taxi: Catch a Ride (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Crazy Taxi: Catch a Ride/Crazy Taxi: Catch a Ride.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `CRAZY TAXI C` (12-byte field, space padded) |
| Game code | `A3CE` |
| Maker code | `78` |
| Software version | `0x00` |
| Complement byte `0xBD` | `0xA4` — recomputed value is also `0xA4` (header not edited) |
| Header checksum `0xBE` | `0x0000` (field zeroed by the dumping/repacking tool; the complement is the better edit signal and is valid) |
| Entry word | `0xEA00002E` → branches to `0x080000C0`; stock GBA crt0, no cracktro |
| Fixed byte `0xB2` | `0x96` |
| Embedded GBA headers | exactly **one** (Nintendo logo found only at file `0x4`; whole 8 MiB scanned) |
| MD5 | `8bcf4e0da6be539f2099c683ff897b43` |
| SHA-1 | `d41f8528e5d010637ece3a50f22c3c809e49b578` |
| SHA-256 | `39996ec9c561f68e16e5435b781bb7c73f4e0123c13002c109f8150ab6e89de5` |

Patch/trainer check: entry branch is the normal `b 0x080000C0`, the first 4 KiB is ordinary ARM crt0, the
header complement is self-consistent, and no trainer/menu text or appended stub exists at the end of
the image (last 64 KiB is graphics/sound data). **No patch or trainer.** The build banner
`Crazy Taxi v1.10` is present at file `0x49D650` but, unlike every menu label, it is **not in the
text-ID table and has no ROM pointer to it** (the only `u32` hits for its address/offset fall inside
glyph bitmaps at file `0x6CBBC`/`0x7E33C`, which are pixel data, not code). It is an unreferenced
developer version string.

## 2. Executive summary

**There is no password, cheat-code, or debug-menu system in this ROM.** The 8 MiB image contains
zero occurrences of `password`, `passwd`, `cheat`, `secret`, `debug`, `code`, `keycode`, `bonus` or
`hidden` in any ASCII string (one `unlock` hit: the UI message `City 2 unlocked`). The only text-entry
surface is the profile-name keyboard (41 symbols); its buffer is consumed by the record/save writer,
never by a comparison against constants. There is one `KEYINPUT` reader, and the held/edge key words
are read only by the menu system — there is no sequence comparator, no mask table and no gate that a
button code could drive.

What the game *does* have is **one developer-intended unlockable**: **City 2**, earned with a high
license score. The public description ("Get a Crazy License, $10,000+, in City 1 on normal rules") is
implemented by the license-class function at `0x0800C540`, which maps the run score to one of eight
classes and sets a "licensed" byte. The same ROM contains two dead menu rows, `Exit` on the two
menus and `Clear Memory` on the Options menu, which the cursor can never reach because each screen's
item count is one smaller than its text block.

This is a bounded negative: the whole string space, the whole 10-key button space, every menu screen
and every screen's item count were enumerated (see §6b).

## 3. How to reproduce

Emulator and display (never touch another display):

```bash
Xvfb :270 -screen 0 1024x768x24 &
DISPLAY=:270 openbox &
DISPLAY=:270 SDL_AUDIODRIVER=dummy mgba -3 "Crazy Taxi: Catch a Ride.gba" &
```

Default mGBA SDL keys: **A `x`**, **B `z`**, **Start `Return`**, **Select `BackSpace`**, **L `a`**,
**R `s`**, d-pad arrows. Confirmed against the game's own key mirror at `0x020034DE`
(active-high; `x`→`0x3FF&~1`, `z`→`~2`, `Return`→`~8`, `a`→`~0x200`, `s`→`~0x100`).
Hold 100–200 ms; **always also send a second `keyup`** — a lost keyup leaves a key latched and the
menus stop confirming (this cost several false "menu is dead" observations).

Exact menu path used:

1. Boot: publisher/logo screens run for ≈10 s (task pointer `0x02003878` is `0` until then).
2. Attract/title task `0x0801E275` appears. Press **Start** → main menu task `0x080174DC`.
3. Main menu index byte `0x0200387D` (ring 0–4). Press **A** on index 0 → task `0x08017741`
   ("Crazy Taxi" time-limit screen, index byte `0x0200387E`, ring 0–3).
4. Press **A** on index 0 → gameplay loop `0x0800ABEC` starts (this is the "freeze": same task
   pointer, 3-D engine running). **Start** during play sets the loop-exit byte `0x02003895 = 1` and
   returns toward the menus.
5. **B** backs out of any submenu. At the main menu, B is ignored; the only way out is the idle
   timeout (`0x707` units of no key held, code at `0x08017634`–`0x08017648`) which returns to the
   attract demo.

Menu position is read from RAM after a savestate (`Shift+F2`, parse the PNG `gbAs` zlib chunk,
EWRAM at `0x21000`, IWRAM at `0x19000`), never from pixels.

## 4. Address map

### ROM

| Address | Meaning |
|---|---|
| `0x08000000` | header / entry `b 0x080000C0` |
| `0x080000C0` | ARM crt0 |
| `0x08005404` | `main` (Thumb), calls the dispatcher |
| `0x0801E1F0` | task dispatcher: `[0x02003878]()` until byte `0x02003892 != 0` |
| `0x08015C3C` | joypad module: reads `KEYINPUT`, builds edge/held/repeat arrays |
| `0x0800ABEC` | scene/gameplay loop; waits on exit byte `0x02003895` (`1`=leave loop, `2`=jump to `0x08017741`) |
| `0x0800B6A8` | sets task `0x08017741`, clears `0x02003895` (hard quit) |
| `0x0800C540` | license class function (score → class 0..7) |
| `0x0849D000` | **text bank base** (all UI strings, plain ASCII, NUL-terminated) |
| `0x0849DFE0` | text bank descriptor: `u32 count = 853`, then `u32 offset[854]` relative to base |
| `0x084A0CE8` | `--- Bad String ---` fallback string |
| `0x08028FE4` | text-ID resolver: `bank = table[0x02009A88]`, `bank[0]`=count, `bank[1+id]`=offset |
| `0x0849D624` | name-entry alphabet (41 chars, referenced by 13 pointers) |

### RAM

| Address | Meaning |
|---|---|
| `0x02003878` | current task function pointer (Thumb, low bit set) |
| `0x02003892` | task-exit request byte |
| `0x02003895` | shared scene exit byte (0 run, 1 leave, 2 quit-to-Crazy-Taxi) |
| `0x02003897` | per-screen init flag |
| `0x0200387D` | main menu index (0–4) |
| `0x0200387E` | Crazy Taxi submenu index (0–3) |
| `0x0200387F` | Options index (0–4) |
| `0x02003880`–`0x02003882` | other screens' indices (Save/Load, Records, Crazy Box; not individually sampled) |
| `0x020034DE` | held keys (active-high, `0x3FF` = none) |
| `0x020034E0` | edge ("newly pressed") mask |
| `0x020034F6[0..9]` | per-key repeat flags (index 0=A, 1=B, 2=Select, 3=Start, 4=Right, 5=Left, 6=Up, 7=Down, 8=R, 9=L) |
| `0x02003500[0..9]` | per-key menu-held flags |
| `0x0200177B` | menu confirm/block byte checked by every screen |
| `0x02001691` | "has license" byte (1 when class ≤ 2) |
| `0x02001693` | license class 0..7 |
| `0x02001698`, `0x0200169C` | run-score accumulators (dollars / carried hundreds) |

### Menu functions (entry, item count, header text ID, index byte)

| Screen | Entry | Count | Header ID | Index |
|---|---|---:|---:|---|
| Mode Selection (main) | `0x080174DC` | 5 | 40 | `0x0200387D` |
| Crazy Taxi (time limit) | `0x08017740` | 4 | 50 | `0x0200387E` |
| Options | `0x08017918` | 5 | 60 | `0x0200387F` |
| Save & Load | `0x08018120` | 5 | 70 | `0x02003880` |
| Records | `0x0801904C` | 3 | 100 | `0x02003881` |
| Crazy Box | `0x08019B7C` | 11 | 110 | `0x02003882` |

The count is the `movs r1,#N; strb r1,[sp,#…]` at each function's prologue
(`0x080174E8`=5, `0x0801774A`=4, `0x0801791C`=5, `0x0801812E`=5, `0x08019050`=3, `0x08019B8A`=11).
It is the wrap value used by the shared menu updater `0x0801C0C4`.

## 5. Algorithm

### 5.1 Menu model (verified)

`0x0801B1D4(header_id, y, &index, menu_object)` draws the header (`header_id`) and then, at
`0x0801B34A` onwards, draws one row per index while `index < count`; the selected row is highlighted.
Therefore:

```
row_text_id(i) = header_id + 1 + i          (i = 0 .. count-1)
```

`0x0801C0C4(&index, &count, 1, allow_cancel, &exit)` performs the wrap/cancel/confirm:
`index+1 == count` → 0 (wrap); B sets the exit byte to 2; A or Start sets it to 1.

### 5.2 License class (derived from `0x0800C540`)

The function sums the two score accumulators (with hundreds carry, BCD style) into `r1`, then:

```
class = 0 if score > 20000
      = 1 if score > 10000     (published "Crazy License" threshold)
      = 2 if score >  5000
      = 3 if score >  4000
      = 4 if score >  3000
      = 5 if score >  2000
      = 6 if score >  1000
      = 7 otherwise
store class -> 0x02001693
has_license = 1 if class <= 2 else 0   -> 0x02001691
```

Constants are literal-pool entries at file `0xC5DC` (20000), `0xC5EC` (10000), `0x0C5FC` (5000),
`0xC600` (`250<<4`=4000), `0xC618` (3000), `0xC61C` (`250<<3`=2000), `0xC628` (`250<<2`=1000).

### 5.3 City 2 unlock

When class ≤ 1 the result/message path inserts text ID 438 (`City 2 unlocked`) into the notification
group; ID 437 is `Awesome Cabbie!!`. The group is stored in the UI resource at file `0x7ABEA4`
(`u32 count=4`, then `u16` IDs `261, 262, 437, 438`). This is the only unlock message in the ROM —
there is **no** `City 3 unlocked` string, only the unused label `City 3` (ID 202).

## 6. Tables

### 6.1 Text bank (base `0x0849D000`, 853 IDs, contiguous ASCII)

| ID | Text | ID | Text |
|---:|---|---:|---|
| 30 | `DEMO` | 250 | `Combos` |
| 31 | `Press START` | 438 | `City 2 unlocked` |
| 32–37 | `Sound`,`BGM Volume`,`SFX Volume`,`Effect`,`Music`,`Exit` | 437 | `Awesome Cabbie!!` |
| 40 | `Mode Selection` | 440 | `Select Your Name` |
| 41–46 | `Crazy Taxi`,`Crazy Box`,`Options`,`Records`,`Save & Load`,`Exit` | 441–443 | `Register To`,`Register A New Name`,`Don't Register` |
| 50 | `Crazy Taxi` (submenu header) | 450 | `Paused` |
| 51–55 | `Normal Rules`,`3 Minutes`,`5 Minutes`,`10 Minutes`,`Exit` | 451–453 | `Resume`,`Restart`,`Quit` |
| 60 | `Options` | 454 | `Engine` |
| 61–66 | `Time`,`Time Diff`,`Traffic`,`Sound`,`Control`,`Clear Memory` | 455–456 | `Restart?`,`Quit?` |
| 70 | `Save & Load` | 457–458 | `Yes`,`No` |
| 71–77 | `Save`,`Load`,`Enter`,`Delete`,`Modify`,`Empty`,`Delete?` | 459–461 | `Draw Distance`,`Borders`,`Full Screen` |
| 80–82 | `Save Data`,`Load Data`,`Yes` | 200–202 | `City 1`,`City 2`,`City 3` |
| 100–103 | `Records`,`Total Records`,` Records`,`--- Records` | 105–108 | `C1`,`C2`,`C3`,`CB` |
| 110 | `Crazy Box` | 111–121 | `Name`,`Cabbie`,`Crazy Jump`,`Crazy Flag`,`Crazy Balloons`,`Crazy Drift`,`Crazy Turn`,`Crazy Bound`,`Crazy Rush`,`Crazy ZigZag`,`Crazy Pole` |

Pause/UI ID table is also duplicated at file `0x08A8818` and `0x08B2830`
(`450..461` plus `-Select` padding).

### 6.2 Reachable vs dead menu rows

| Screen | Count | ID range drawn | Dead row (never drawn/selectable) |
|---|---:|---|---|
| Main | 5 | 41–45 | **46 `Exit`** |
| Crazy Taxi | 4 | 51–54 | **55 `Exit`** |
| Options | 5 | 61–65 | **66 `Clear Memory`** |
| Save & Load | 5 | 71–75 | 76 `Empty` is a slot label, 77 is a confirm |
| Records | 3 | 101–103 | 104 blank |
| Crazy Box | 11 | 111–121 | none (9 events + 2 header rows) |

Main-menu index→screen was verified in the emulator: 0→`0x08017741`, 1→`0x08019B7D`,
2→`0x08017919`, 3→`0x0801904D`, 4→`0x08018121`.

### 6.3 Name-entry alphabet

`ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.&!?@ ^` — **41 symbols** (26 letters, 10 digits, `. & ! ? @ space ^`).
It is a profile keyboard only. No other alphabet exists in the ROM.

### 6.4 Save medium

mGBA detects a **512-byte EEPROM** (4 Kbit). Virgin image is `0xFF` throughout. A record written by
"Save & Load → Save" begins at EEPROM offset 0; the observed 16-byte prefix was

```
00 00 32 00 44 40 20 00 00 00 00 11 01 41 41 2e      rest 0x00
```

The profile-name field and the record count live in this prefix. City 2's persistent bit was not
isolated (see §8); the file is 512 bytes with `0x00` fill after the header, so the save is a small
fixed-layout profile, not a password carrier.

## 6b. Enumeration

### 6b.1 Space definition

There is **no code space**, so there is no alphabet/length/checksum to state for one:

* **Text space** — 91,707 ASCII runs ≥ 4 bytes in 8,388,608 bytes. Keyword hits:
  `password` 0, `passwd` 0, `cheat` 0, `code` 0, `keycode` 0, `secret` 0, `debug` 0, `bonus` 0,
  `hidden` 0, `unlock` 1 (`City 2 unlocked`). No screen label, prompt, error string or table name
  for a code entry exists.
* **Text-ID space** — the UI bank holds 853 IDs; all 853 were decoded and classified. The only
  string-input surface is the 41-symbol profile keyboard (§6.3), whose consumer is the save/record
  writer (`Select Your Name` / `Register To` path), not a validator.
* **Button space** — 10 keys = 1,024 simultaneous combinations. The entire ROM was scanned for
  runs of ≥ 4 aligned `u16` values that are valid key masks (A=1, B=2, Select=4, Start=8,
  Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200, and their OR-combinations):
  **3,468 runs** found; **34** are referenced by a ROM `u32` pointer; all 34 were read and are
  graphics/sound tables (`0x0101…`, `0x120…`, ascending index lists), not press sequences.
* **Input readers** — `KEYINPUT` (`0x04000130`) has exactly **1** literal reference (`0x08015CB0`),
  inside the joypad module. The held word `0x020034DE` has 2 readers (joypad module + the main-menu
  idle timer at `0x08017634`); the edge word `0x020034E0` has 1 reader. There is no global
  cross-frame sequence comparator anywhere: every other input consumer is one of the 11 menu
  screens or the driving control code, and each reads only the current frame's mask.

### 6b.2 Published list check

3rd party cheat indexes' only entry for this SKU (archived 2025-08-19) is the **Unlock City 2** row:
"Get a Crazy License ($10,000+) in City 1 on normal rules". a 3rd party cheat index's page carries the same single
unlockable ($10,000+ in normal rules / 3 / 5 / 10 minutes). **No password, button code or debug code
is published for the GBA SKU**, and none was found, so there was no literal to grep and no published
code to reproduce.

The Dreamcast/PS2 Crazy Taxi lists (bike/rickshaw character-select code, "Another Day" etc.) were
explicitly **not** applied: those platforms have a character-select screen that this ROM does not
contain (no `Select Cabbie`, no driver-select alphabet, and the cabbie block 100–121 is only the
Crazy Box header rows).

### 6b.3 Novel values / bounds

Because there is no generator there is no code to mint; the deliverable is the closed enumeration:

* **Menu rows:** 5 + 4 + 5 + 5 + 3 + 11 = 33 rows, of which **3 are unreachable**
  (main `Exit`, Crazy Taxi `Exit`, Options `Clear Memory`) — proven by the hard-coded count and the
  `index+1 == count → 0` wrap: the cursor never equals the dead row's index.
* **Unlockable:** 1 (City 2), threshold table above; the message is ID 438.
* **Rejected/unreachable tests (bounds):** from the main menu, 7 consecutive **Down** presses give
  `4,0,1,2,3,4,0` — index 5 is never produced, so the `idx==5` branch at `0x080176AE` (exit) is dead
  code; the same wrap proves Options index 5 (`Clear Memory`) is unreachable (ring `1,2,3,4,0,1,2`).
* **Button code test:** all 34 pointer-referenced mask runs were inspected; none is a sequence
  table, so no undocumented press combination exists to test.

## 7. Validation evidence

**Observed (emulator, RAM reads through savestates):**
* Task pointer transitions `0x0801E275` (attract) → `0x080174DC` (main) → `0x08017740` (Crazy Taxi)
  → `0x0800ABEC` (gameplay) with Start/A at the menu positions above.
* Main-menu ring at `0x0200387D`: `0→1→2→3→4→0→1→2` with Down, `4→3→2→1→0` with Up (7/5 presses).
* Crazy Taxi ring at `0x0200387E`: `0→1→2→3→0`.
* Options ring at `0x0200387F`: `1,2,3,4,0,1,2`.
* Joypad mirror `0x020034DE`: `x`→`0x3FE`, `z`→`0x3FD`, `Return`→`0x3F7`, `a`→`0x1FF`,
  `s`→`0x2FF`, `BackSpace`→`0x3FB`; edge word `0x020034E0` takes the corresponding single bit.
* Start in gameplay drives the exit byte `0x02003895` from 0 to 1 (loop at `0x0800ABEC` then
  returns to the menu); B backs out of every submenu.
* A fresh save via the Save & Load menu produced the 16-byte prefix and 512-byte EEPROM file listed
  in §6.4 (the file starts as `0xFF` on a virgin cart).

**Derived (instruction sequence):**
* Menu counts and the `row = header + 1 + index` rule (§5.1) match every observed index→task mapping.
* License classes, thresholds and the licensed flag (§5.2).
* Dead rows from counts vs. text blocks (§6.2).
* No code surface: `KEYINPUT` single reader; no `strcmp`-style consumer of the name buffer; the
  41-symbol alphabet is only a keyboard.

**Inferred:**
* The City 2 notification is ID 438 and is inserted when class ≤ 1 (the group table places 437/438
  together, and 438 only exists in that group).
* The pause overlay's text set is IDs 450–461 (table at `0x08B2830`); the live pause index was not
  isolated because Start ends the gameplay loop instead of holding it (see §8).

## 8. Unknowns

* The exact EEPROM bit/byte that records "City 2 unlocked" was not isolated. The save is a
  512-byte profile; the license class and score are computed live in `0x02001693`/`0x02001698`.
  Reaching class 1 requires a real $10,000+ run (the published path), which was not played to
  completion in this engagement. The threshold logic itself is proven; the persistent bit is not.
* The pause screen's live index address. The overlay is reached from the in-race Start path (the
  shared exit byte `0x02003895` moves to 1), but in this emulator session that returned to the
  Crazy Taxi menu before a stable pause state could be sampled. The overlay's complete text set
  (450–461) and sub-confirmations (455–458) are enumerated from the table, but the index byte is
  unproven.
* `City 3` (ID 202) has a label but no unlock message and no third destination set; it is treated
  as cut/unused, not as an unlockable.

## 9. Tooling

* `mgba` (SDL), `Xvfb :270`, `openbox`, `xdotool` for input; `SDL_AUDIODRIVER=dummy`.
* Python 3: `zlib`/`struct` parsing of mGBA `.ssN` PNG states (`gbAs` chunk; EWRAM `0x21000`,
  IWRAM `0x19000`), `capstone` 5.0.7 for spot checks, plus small scripts for:
  header/logo scan, `strings` classification, text-ID table decode, key-mask run scan,
  Thumb `BL` target scan, and raw `objdump -M force-thumb` dumps.
* `arm-none-eabi-objdump`, `strings`, `md5sum`/`sha1sum`/`sha256sum`.
* No game assets are redistributed here; only addresses, algorithms, text-ID labels and hashes.
