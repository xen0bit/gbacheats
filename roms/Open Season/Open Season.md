# Open Season (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Open Season/Open Season.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `OPEN SEASON` |
| Game code / maker | `BOAE` / `41` (`file(1)` prints `BOAE41, Rev.00`) |
| Version | 0x00 |
| Fixed byte / complement / checksum | 0x96 / 0xBA / 0x0000 |
| Entry branch | `0xEA00002E` → ARM entry `0x080000C0` (stock crt0) |
| MD5 | `64b19adca4ba8ebfca983c39c7f21c8c` |
| SHA-1 | `b12757e5315bc384cf40b5e621f956ca536a3e66` |
| SHA-256 | `f534d904a99b61e954f47c7356f248a1f2ecfca2cd2045465b9f395d06a0980d` |

Phase 0: the 156-byte Nintendo logo occurs **once** (file offset 0x04); the entry word is the
stock branch, not a scene cracktro patch (§16.1). No appended trainer or second GBA header was
found. Header checksum 0x0000 is a common rebuilt-header artifact; the image is a single retail
image. No patch/trainer applies.

## 2. Executive summary

The game has a developer-intended **pause-screen button-code system** ("Cheat Mode"), not a
text password. Pause with Start, hold **L**, and press a button sequence; "Cheat Mode" is drawn
bottom-left and flashes green on acceptance. A limit of three codes per save file is enforced.

The complete code set is a table of **11 fixed button-index sequences** at ROM `0x080767EC`,
with the packed button bytes in a blob at `0x080767AC`. Eight codes are documented publicly
(polar bear, +3 lives, 30 Woo-Hoo bars, five level skips); three further records exist in the
table. One of those (record 1) is permanently rejected by its eligibility predicate, one
(record 2) is level-gated, and one (record 5) is an invincibility code with no in-game
description.

The validator was reversed and used as an oracle (§16.19). It checks only `input_count >=
record_len` and then compares `input_count` bytes starting at the record pointer. Because the
sequences are packed contiguously, **concatenating adjacent records produces longer, accepted
codes that appear in no published list**. Two such codes were generated, entered on the real
pause screen, and RAM-verified. Bounds were proven by rejection at four independent layers.

## 3. How to reproduce

* Emulator: `SDL_AUDIODRIVER=dummy mgba -3 <rom>` under `Xvfb :319`.
* mGBA SDL keymap: A=`x`, B=`z`, Select=`BackSpace`, Start=`Return`, L=`a`, R=`s`,
  D-pad=arrow keys. Hold keys 100–150 ms.
* Path: language `English` → `PRESS START` → Start → `Start Game` → slot 1 → enter a 3-letter
  name → difficulty `Easy` → town/hub → **Start** to pause → hold **L** → press sequence.
* RAM evidence: mGBA `Shift+F1..F9` writes `Open Season.ssN`; the PNG carries a `gbAs` chunk.
  `zlib.decompress` yields 397,312 bytes; IWRAM `0x03000000` starts at raw offset `0x19000`
  (EWRAM at `0x21000`). Scripts were in `/tmp/openseason/`.
* Verified stat addresses (cross-checked against published CodeBreaker raw addresses and the
  on-screen HUD): bars `0x0300778A`, lives `0x030077E5`, health `0x030077E4`,
  invincibility `0x030077F8`, stage access `0x03007788`, abilities `0x03007790`.

Published codes tested in the ROM and in the emulator: all eight from 3rd party cheat indexes
(including the 2012 "unknown effect" blog's polar-bear alias) are present as exact byte records.

## 4. Address map

| ROM address (file offset = addr − 0x08000000) | Meaning |
|---|---|
| `0x08040B24` (`0x40B24`) | Cheat validator (Thumb; Thumb pointer `0x08040B25` stored at `0x08040AE4`) |
| `0x08040B3C` | L-key gate (`0x200` active-high mask; key-state pointer global `0x03001480`) |
| `0x08040B6E`–`0x08040BC8` | 11-record comparison loop against `{ptr,len}` table |
| `0x080406D4` / table `0x080406F0` | Per-record eligibility dispatcher (11 predicates) |
| `0x08040788`, `0x08040734`, `0x0804078A`, `0x0804071C`, `0x0804076C` | Reject / level-data / accept / counter / level-match predicates |
| `0x080767AC` (`0x767AC`) | Packed button-index blob (11 sequences, 5–11 bytes each) |
| `0x080767EC` (`0x767EC`) | 11 × `{u32 seq_ptr, u32 len}` record table |
| `0x08076844` (`0x76844`) | 20-entry function-pointer table (effect/handler resources) |
| `0x08071580` | ASCII string `Cheat Mode` (French `Mode Triche` at `0x08071D68`) |
| `0x0807156C` | Pause menu string table: `PAUSE, Resume, Quit Area, Quit Game, Cheat Mode` |
| `0x0807146C` | 11 screen-name strings: `LOCALIZATION, TITLE SCREEN, SELECT GAME, OPTIONS, CREDITS, SELECT DIFFICULTY, AREA CLEARED!, GAME OVER, STAGE SELECT, CONGRATULATIONS, ELLIOT SHOP` |
| `0x08071808` | Master menu-definition list (`{u16/u32 count, ptr}` pairs) |
| `0x08073660` (`0x73660`) | Debug string `Level ID:  %d` |
| `0x0803E75C` / `0x0806827A` | Debug level-ID formatter and its UI caller |

RAM (GBA addresses; IWRAM `0x03..`):

| Address | Meaning |
|---|---|
| `0x03001480` | Pointer to the input/UI state struct (observed `0x03000EF0`) |
| state+`0x114` | Button-index history (one byte per press) |
| state+`0x136` | Button history count (cleared on successful match) |
| state+`0x135` | Last matched cheat index |
| `0x0300778A` / `0x030077E5` / `0x030077F8` | Bars / lives / invincibility |
| `0x030077E4` / `0x03007788` / `0x03007790` | Health / stage flags / abilities |

## 5. Algorithm

Button encoding (one byte per press, derived from all published sequences matching the ROM
blob): `A=0, B=1, Select=2, Start=3, Right=4, Left=5, Up=6, Down=7` (R=8, L=9 by extension of
the GBA key-bit order). The L hold is a gate, not part of the stored sequence.

```
record[i] = { seq_ptr (u32), len (u32) }          # i = 0..10, table @ 0x080767EC

on_each_frame(mode=1):
    held, pressed = key_state()                    # via global ptr at 0x03001480
    if (pressed & KEY_L) & ~(held & KEY_L):        # 0x08040B3C
        for i in 0..10:                            # 0x08040B66..0x08040BC8
            n = history_count
            if n < record[i].len: continue
            if history[0:n] == bytes(record[i].seq_ptr, n):
                if eligible(i):                    # 0x080406D4
                    last_cheat = i
                    set cheat flags; flash green; return 2
                else: reject
    else:
        append newly pressed button index to history (cap 11), 0x08040C9E
```

`eligible(i)` uses a jump table at `0x080406F0` keyed by `i` with the dispatch sub-`1`:

| Record | Contents | Predicate | Acceptance |
|---|---|---|---|
| 0 | `Down,Up,Down,B,A` | default (`0x0804078A`) | always accept (polar bear skin) |
| 1 | `A,Left,Up,Right,A` | `0x08040788` | **always reject — dead code** |
| 2 | `B,Left,Right,Right,Left,B` | `0x08040734` | level-data flag nonzero (level-gated) |
| 3 | `Up,Up,Down,Down,Left,Right,Left,Right,B,A,Start` | `0x0804078A` | always accept (+3 lives) |
| 4 | `Up,Right,Down,Left,Up,Select,Start` | `0x0804071C` | state+0x46 gate (30 bars in hub) |
| 5 | `A,B,A,B,Up` | `0x0804078A` | always accept (invincibility) |
| 6–10 | `Start,Select,B,A,{Up,Down,B,Right,Left}` | `0x0804076C` | must be on the matching level (skips) |

**Space / count.** The alphabet is 10 button indices; the accepted set is the 11 table records,
of which 10 are reachable under the predicates. Per-button input is capped at 11 presses
(`cmp r0,#11` at `0x08040CA6`). The equality test is `count >= len` followed by an *unbounded*
byte compare of `count` bytes from `seq_ptr` — it does not require `count == len`. Since the
records are packed back-to-back, an accepted input of length L can be extended with the next
L'-L bytes of the blob. This is the source of the novel codes below.

## 6. Tables

All 11 raw records (.decoded button names, ROM `0x080767AC` blob):

| # | seq_ptr | len | Sequence | Published? | Observed effect |
|---|---|---|---|---|---|
| 0 | `080767AC` | 5 | `Down,Up,Down,B,A` | 3rd party cheat indexes easter egg (and +A alias on 2012 blog) | polar bear skin (visual, not RAM-proven) |
| 1 | `080767B1` | 5 | `A,Left,Up,Right,A` | blog lists the shifted alias `Left,Up,Right,A,B`, not this form | **rejected** (dead predicate) |
| 2 | `080767B6` | 6 | `B,Left,Right,Right,Left,B` | blog lists the 5-press alias `Left,Right,Right,Left,B` | level-gated, not accepted in hub |
| 3 | `080767BC` | 11 | `Up,Up,Down,Down,Left,Right,Left,Right,B,A,Start` | yes | lives 12 → 15 (RAM) |
| 4 | `080767C7` | 7 | `Up,Right,Down,Left,Up,Select,Start` | yes | bars 0 → 30 (RAM) |
| 5 | `080767CE` | 5 | `A,B,A,B,Up` | 2012 blog, effect unknown there | `0x030077F8` 0 → 32 (invincibility) |
| 6 | `080767D3` | 5 | `Start,Select,B,A,Up` | yes (Skip Rabbit Land) | level-gated; rejected in hub |
| 7 | `080767D8` | 5 | `Start,Select,B,A,Down` | yes (Skip Skunk Land) | level-gated |
| 8 | `080767DD` | 5 | `Start,Select,B,A,B` | yes (Skip Squirrel Land) | level-gated |
| 9 | `080767E2` | 5 | `Start,Select,B,A,Right` | yes (Skip Beaver Land) | level-gated |
| 10 | `080767E7` | 5 | `Start,Select,B,A,Left` | yes (Skip Duck Land) | level-gated |

Published 3rd party cheat index codes were checked literally against the blob; all are present.
CodeBreaker/GameShark raw-address codes (e.g. `3300778A 0063`) are external memory edits, out of
scope, but their addresses were reused as RAM probes.

A fetched 2012 blog page contained no instructions directed at the analyst; it was treated as
data. Its "unknown" 5-press codes are shifted aliases of records 1 and 2 in the packed blob.

## 6b. Enumeration

**Space size:** 11 stored records, 10 reachable; length 5–11; 10-symbol alphabet; 11-press input
cap; three accepted cheats per save. The `count >= len` + unbounded compare adds a family of
concatenation exploit codes limited only by the 11-press cap.

**Novel codes generated from the validator model and accepted on the real pause screen:**

1. `A,B,A,B,Up,Start,Select,B,A,Up` (10 presses) — record 5 bytes followed by record 6 bytes.
   Enumerated nowhere: 3rd party cheat indexes, the 2012 blog and the CodeBreaker
   lists contain neither this sequence nor any 10-press code.
   **RAM proof:** `0x030077F8` 0 → **32** (invincibility). Same effect as record 5, proving the
   packed-blob over-read model.
2. `Up,Right,Down,Left,Up,Select,Start,A,B,A,B,Up` (11 presses) — record 4 + record 5 bytes.
   **RAM proof:** `0x0300778A` 0 → **30** (bars).

Both were entered while paused in the hub with L held, via `xdotool`, after loading a savestate
at the pause screen; the effects were read from the following savestate's IWRAM.

**Bounds proven by rejection:**

| Test | Result | Layer proven |
|---|---|---|
| 4th cheat after 3 accepted (bars code re-entered) | bars stayed 30; no effect | 3-per-save cap |
| `Start,Select,B,A,Up` in the hub | no effect | level-match gate on skips |
| `A,Left,Up,Right,A` (record 1) in the hub | no effect | permanently false predicate `0x08040788` |
| `A,A,B,A,B,Up` and `B,A,B,Up` (prefix/suffix variants of record 5) | no effect | exact count and prefix required |
| `A,B,A,B,Up,Start,Select,B,A,Down` (one button wrong in the novel 10-press code) | no effect | byte-for-byte compare over the whole extended length |

## 7. Validation evidence

* **Observed** — screenshots at every menu transition (language, title, main, options,
  select-game, name entry, difficulty, hub HUD, hub pause with/without L-held `Cheat Mode`,
  confirmation dialog, credits). Savestate IWRAM reads: lives 12→15, bars 0→30, invuln 0→32;
  rejections left all three unchanged. All captured under `DISPLAY=:319`.
* **Derived** — validator and eligibility dispatch from `objdump -M force-thumb` at the listed
  addresses; record table and button mapping from raw bytes; menu/screen inventory from the
  ASCII pointer tables at `0x0807146C`/`0x0807156C`/`0x08071808`.
* **Inferred** — polar-bear visual effect of record 0 (published, not separately RAM-proven);
  R as an alternate hold key (published on the 2012 blog, not retested); the exact semantics of
  state+`0x45/+0x46` used by the gate predicates.

Text was **not** tile-indexed here: all UI labels are plain NUL-terminated ASCII in the banks
at `0x08071498+`, which were dumped and decoded directly, so the screen-name inventory rests on
decoded text, not on guesswork.

## 8. Unknowns

* Screens listed in ROM but not reached in this run (require gameplay progression): `STAGE
  SELECT`, `AREA CLEARED!`, `GAME OVER`, `CONGRATULATIONS`, `ELLIOT SHOP`. The in-level pause
  variant (with `Quit Area`) was not reached; hub pause offers only Resume/Quit Game.
* No reachable hidden debug menu was found. A debug resource exists (`Level ID: %d` at
  `0x08073660`, formatter `0x0803E75C`, called from `0x0806827A`) and an 11-entry screen-name
  table exists, but no input path to a debug screen was exercised. This is a bounded negative
  for the screens walked, not a proof of absence across all gameplay states.
* Record 2's exact 6-press form was not accepted in the hub; its required level condition
  (predicate `0x08040734` reading a level-data word at `0x08076728`-indexed tables) was not
  isolated.
* Record 1 may be an intentional placeholder or a cut cheat; only its always-false predicate is
  proven.

## 9. Tooling

Scripts in `/tmp/openseason/`: `phase0.py` (identity/header/logo scan), `mask_search.py`,
`find_masks.py`, `scan2.py` (button-encoding scans), `dump2tables.py`/`dump_cheat2.py` (record
tables), `blscan.py`/`xrefs.py` (xrefs), `ssread.py`/`diffstate.py`/`ramread.py`/`cheatstruct.py`
(savestate `gbAs` decode and RAM reads), `press.py`/`trycode.py` (XTEST input + savestate loop),
`dump_menus.py` (ASCII menu tables). Toolchain: `arm-none-eabi-objdump`, Capstone, xdotool,
scrot, ImageMagick, mGBA SDL, Xvfb. No ROM or copyrighted asset is redistributed; only
addresses, hashes, algorithms and screenshots kept locally in the work directory.
