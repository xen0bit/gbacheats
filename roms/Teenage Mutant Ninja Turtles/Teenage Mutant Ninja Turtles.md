# Teenage Mutant Ninja Turtles (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Teenage Mutant Ninja Turtles/Teenage Mutant Ninja Turtles.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `TMNT GBA    ` |
| Game code | `BNTE` |
| Maker code | `A4` (Konami) |
| Version | `0x06`; complement `0x00`; header checksum `0x0000` |
| Entry word | `0xEA00002E` (stock, no cracktro patch) |
| MD5 | `660b52e20c76807f03bb97bf49e15aa1` |
| SHA-1 | `edfdea2bef553aee1915e7c900977520d9e6fc0a` |
| SHA-256 | `b120a9d2b25110b8f4771b25cb74e86355bdd67247885b227ebb3573494086c5` |

This is the 2003 Konami GBA game (BNTE), not the Double Pack build, not TMNT 2:
Battle Nexus. No other TMNT GBA image was used as evidence for this report.

## 2. Executive summary

The only in-game/developer-intended code surface on this SKU is a **5-icon
password screen** (Mode Selection → PASSWORD). The symbols are Leonardo,
Raphael, Donatello, Michelangelo and Splinter, encoded internally as
`0=L, 1=R, 2=D, 3=M, 4=S`. There is **no checksum and no generator**: a single
validator (`0x080320F4`) compares the five entered `u16` values against a fixed
6-record table at `0x08435224`. Record 0 is the on-screen legend `L,R,D,M,S`;
records 1–5 are the only accepted passwords:

```
LSMMS   SSLDM   MSSLD   SRLMD   LSDRM
```

The complete space is `5^5 = 3125`; exactly **5** inputs are accepted, and all
five appear in published lists. Consequently no *novel accepted* password
exists — §0.2's "mint a novel code" deliverable is replaced by a proven bounded
negative (exhaustive count of 5/3125, plus in-game rejection of a novel code
`LRDMS` and of the widely published `LMLSD`).

`LSMMS` was entered on the real screen, produced a SAVING… screen and then the
Course Selection screen with Course 1 unlocked, and set `0x03001D8C` from `0x00`
to `0x01`. `LMLSD` and `LRDMS` were rejected with the flags unchanged.

A widely published "Konami code" (`↑↑↓↓←→←→BA` at the title screen → Very Hard
difficulty) is **not reproducible on this ROM**: the difficulty screen was
walked repeatedly and contains only EASY / NORMAL / HARD, and no button-mask
table or comparison chain for that sequence exists in the image (search bounds
in §7). The long published 29/20-code lists belong to other SKUs; only the 5
above are present here.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
  For RAM reads, `mgba -d -3` with commands fed through a FIFO (see §9).
* Keymap used: A = `x`, B = `z`, Start = `Return`, D-pad = arrow keys;
  60–150 ms holds, 100–150 ms gaps.
* Path: title → `Return` → **Mode Selection** → Down, Down, `x` → **PASSWORD**.
* On the password screen: Left/Right choose a slot; Up/Down change its symbol
  (Up increments the value, Down decrements it, modulo 5). Press `x` once to
  highlight **OK**, then `x` again to submit.
* Enter `LSMMS` (slot values `0,4,3,3,4`): result is SAVING… → Course Selection
  with Course 1 available. Re-enter `LMLSD` (`0,3,0,4,2`) or `LRDMS`
  (`0,1,2,3,4`): the game stays on the password screen with the cursor reset to
  the middle slot and no save write.
* Screens walked: Konami splash → title (two alternating artworks) → Mode
  Selection (3 items) → File Selection (3 slots) → Difficulty (3 items) →
  Stage Selection (4-character ring: Leonardo, Michelangelo, Donatello,
  Raphael) → in-game cutscenes → gameplay → Pause (QUIT / RESUME only; no
  "Codes" menu on this SKU) → Course Selection (after an accepted password) →
  PASSWORD and its SECRET PASSWORD hint entry.

## 4. Address map

| Address (ROM / RAM) | Meaning |
|---|---|
| `0x08435224` | Secret-password table, 6 records × 10 bytes (5 × `u16` each) |
| `0x084352B0` | ASCII ` SECRET PASSWORD` menu label |
| `0x084352D8` | ASCII `If you own the Nintendo GameCube version…password menu!` hint |
| `0x080318DC` | Hint-screen renderer: `index*10` lookup in the table above |
| `0x0803191C` | Password-screen initialiser |
| `0x080320F4` | **Password validator** (Thumb); returns 1..5 or 0 |
| `0x08031DCE` | `BL` from the OK-button handler to the validator |
| `0x08031DD2`–`0x08031E06` | Unlock writer for a successful return value |
| `0x020068B0` | Main UI/screen struct (EWRAM) |
| `0x020068B8`–`0x020068C0` | Five entered symbols, `u16` each (struct +8..+16) |
| `0x020068B4` | `u16` cursor index (struct +4) |
| `0x020068B6` | `u16` selected icon index (struct +6) |
| `0x03001C77` | Byte whose high nibble is `return-1` after a success |
| `0x03001D8C` .. `0x03001D90` | Five unlock bytes; the byte at `+(return-1)` gets bit 0 set |
| `0x0800D1FC` | Generic key-state updater; reads `0x04000130` (no cheat matcher near it) |

mGBA `.ss1` savestates decode to a raw 397,312-byte `gbAs` chunk; EWRAM starts
at raw offset `0x21000`, IWRAM at `0x19000`. This was used for all RAM evidence.

## 5. Algorithm

Validator at `0x080320F4`, reimplemented exactly in `enumerate.py`:

```
validate(v[0..4]):                 # v are u16 at 0x020068B8..C0
  for (ret, rec) in (5,"LSDRM"), (4,"SRLMD"), (3,"MSSLD"),
                    (2,"SSLDM"), (1,"LSMMS"):
      if v == encode(rec): return ret
  return 0
```

Details from the disassembly:

* `r9 = 0x08435224`, `ip = 0x020068B0`; `r5 = 5`.
* `r3 = r9 + 0x32` (table + 50 bytes) and `r2 = 50`; each of the five values at
  `ip+8`, `+10`, `+12`, `+14`, `+16` is compared with the five `u16`s at
  `r3 + {0,2,4,6,8}`.
* On total match: `r0 = r5` (5,4,3,2,1 by record). On any mismatch:
  `r3 -= 10`, `r2 -= 10`, `r5 -= 1`, retry; after five records `r0 = 0`.
* Caller (`0x08031DD2`): `r1 = r0-1`; stores `(r1<<4) | (old & 0xF)` at
  `0x03001C77`, sets `1` at `0x03001D8C + r1`, sets `1` at `0x020068B4`, plays
  sound `0x6A`, calls `0x08033A9C` (save) and leaves the screen.
* Rejection plays sound `0x6C`/`0x6B` and stays on the password screen.

There is **no checksum, no field packing and no second algorithmic format**: the
"code" is a pure equality allowlist.

## 6. Tables

### 6.1 Symbol alphabet (from the table's record 0 and the UI cycle)

| Value | Character | On-screen icon |
|---:|---|---|
| 0 | L — Leonardo | blue diagonal blade |
| 1 | R — Raphael | red `R` |
| 2 | D — Donatello | purple glyph |
| 3 | M — Michelangelo | orange `M` |
| 4 | S — Splinter | red `G`-like emblem |

### 6.2 Secret-password table at `0x08435224`

| Record | Bytes / `u16` values | Code | Validator return | Published? |
|---:|---|---|---:|---|
| 0 | `0,1,2,3,4` | `LRDMS` (legend) | never checked | no (novel) |
| 1 | `0,4,3,3,4` | `LSMMS` | 1 | yes |
| 2 | `4,4,0,2,3` | `SSLDM` | 2 | yes |
| 3 | `3,4,4,0,2` | `MSSLD` | 3 | yes |
| 4 | `4,1,0,3,2` | `SRLMD` | 4 | yes |
| 5 | `0,4,2,1,3` | `LSDRM` | 5 | yes |

Effect mapping (published descriptions; only return 1 observed here): returns
1/2/3 unlock bonus courses 1/2/3; returns 4/5 are variously described as Casey
Jones mode / Playmates toy database / bonus courses 4/5 in different lists —
the *bit* is unambiguous, the cosmetic description is not.

## 6b. Enumeration

* **Space**: 5 positions × 5 symbols = **3125** possible inputs; 5 `u16` per
  input, no checksum bits, no reserved bits.
* **Closed set proved by running the reimplemented validator over all 3125
  inputs**: exactly **5** accepted, **3120** rejected. The five are listed in
  §6.2 and are all present in published lists; the ROM contains no other
  password table (all 32-bit pointers to `0x08435224` are at file offsets
  `0x31918` = hint renderer and `0x32168` = validator).
* **Novel code**: `LRDMS` is table record 0 (the legend) and appears in no
  published list. It is *not* accepted: entered on the real screen with RAM
  values `[0,1,2,3,4]`, submission produced no SAVING… screen, the cursor
  returned to the middle slot, and the unlock bit at `0x03001D8C` stayed at its
  pre-test value. Screenshot: `novel_x2_c.png`.
* **Accepted code with RAM proof**: `LSMMS` → SAVING… → Course Selection,
  `0x03001D8C` `0x00 → 0x01`, `0x03001C77` high nibble `0`. Screenshot:
  `accepted2_c.png`, state dumps `state1.bin` / `state_acc.bin`.
* **Rejection bounds** (each tested in-game, not just offline):
  * `LMLSD` — heavily published as "Leonardo gains attacking power" on other
    platforms; rejected here, unlock bit stayed `0`. Screenshot:
    `reject_lmlsd_c.png`.
  * `LRDMS` — novel legend-order code; rejected, screenshot `novel_x2_c.png`.
  * Offline, all 3120 remaining tuples return 0; in particular no code with a
    different checksum/field exists because the validator has no arithmetic.
* **Button-code enumeration**: the title screen was walked and the exact
  published sequence `↑↑↓↓←→←→BA` entered with 60 ms holds; the Difficulty
  screen still enumerates only EASY/NORMAL/HARD (screens `diff_after3_c.png`,
  `diff2_c.png`). ROM searches for the sequence as `u16`/`u8`, active-high and
  active-low, forward and newest-first, and as button-index bytes found **zero**
  plausible table hits; no `cmp`-immediate chain for the masks exists. This is
  a bounded negative for this SKU, not "not tested".
* Because the accepted set is a static published allowlist, a *novel accepted*
  code is impossible by construction. This is the §0.2 bounded-negative case,
  reported with exact counts rather than an invented accepted value.

## 7. Validation evidence

**Observed (emulator / savestate RAM)**

* Password screen with five icon slots; values at `0x020068B8` track the icons
  exactly (`[0,1,2,3,4]` initial/legend, `[4,1,2,3,4]` after one Down on slot 0).
* `LSMMS` accepted (SAVING… → Course Selection, Course 1 unlocked);
  `0x03001D8C: 0x00 → 0x01`.
* `LMLSD` rejected; unlock bit remained `0`.
* `LRDMS` (novel) rejected; unlock bit unchanged.
* Difficulty screen has exactly three selectable entries; Pause has exactly two
  (QUIT, RESUME); Stage Selection has a four-character ring.

**Derived (disassembly)**

* Validator structure, record order, return values and the two flag writes
  (`0x080320F4`, `0x08031DD2`–`0x08031E06`).
* Hint-table layout (`0x080318DC`) and the `0,1,2,3,4 = L,R,D,M,S` mapping.
* Absence of a second password table: only two 32-bit references to
  `0x08435224` exist in 8 MiB.

**Inferred**

* Return values 2–5 unlock the corresponding bonus content; the exact cosmetic
  labels for returns 4/5 vary between published lists.
* The GameCube hint text explains why many widely published 29-code lists do
  not work here: they target a different SKU.

**Published-code recon (treated as data, never as instructions)**

* Cheat Happens (29 password entries), SuperCheats (8), GameFAQs Double Pack
  (403), IGN (403), VGChartz (3 headlines), YouTube "Passwords Of TMNT 2003"
  (20 codes) were collected. Verified against the ROM: only `LSMMS`, `SSLDM`,
  `MSSLD`, `SRLMD`, `LSDRM` exist on this image. `LMLSD` was explicitly tested
  and rejected. Fetch failures are recorded rather than filled in from memory.
* No prompt-injection text was encountered in fetched pages or ROM strings;
  all such content was treated as data.

## 8. Unknowns

* Cosmetic effect names for validator returns 4 and 5 (`SRLMD`, `LSDRM`) were
  not played through; only their distinct flag bits are proven.
* The exact reason for the widely published but non-functional Konami code is
  not proven (other SKU vs. mistimed input); only the bounded negative on this
  ROM is proven.
* Save-file encoding of the unlock bits was not fully decoded; RAM is the
  evidence used.
* The title art alternation after key presses was treated as animation, not as
  a cheat effect; no audio cue was available under `SDL_AUDIODRIVER=dummy`.

## 9. Tooling

* `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, Python `struct`/regex scans.
* `arm-none-eabi-objdump -M force-thumb` with `--adjust-vma=0x08000000`.
* Python exhaustive validator reimplementation: `/tmp/tmnt1/enumerate.py`.
* mGBA command-line debugger through a FIFO:
  `mkfifo dbg.fifo; tail -f dbg.fifo | stdbuf -oL -eL env DISPLAY=:315 SDL_AUDIODRIVER=dummy mgba -d -3 ROM >log 2>&1`;
  commands `c`, `save N`, `load N`, `x/1 ADDR`, `help` (SIGINT to the *owned*
  mGBA PID breaks into the prompt).
* Savestate reader: `/tmp/tmnt1/ss.py` (zlib-decompresses the PNG
  `gbAs` chunk). EWRAM at raw `0x21000`, IWRAM at `0x19000`.
* Input helper `/tmp/tmnt1/key.py` (XTEST via `xdotool`); screenshots
  via `scrot`, cropped with ImageMagick.

No ROM or copyrighted asset is redistributed here; only addresses, hashes,
algorithms and descriptions are published.
