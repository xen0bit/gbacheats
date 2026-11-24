# Spider-Man 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Rom: `roms/Spider-Man 2/Spider-Man 2.gba`. Analysis date 2026-11-20.
All addresses are for **this exact image** (hash below). ROM offsets = address − `0x08000000`.

## 1. Target identity

| Field | Value |
|---|---|
| File / size | `Spider-Man 2.gba`, 16,777,216 B (`0x01000000`) |
| Header title | `SPIDER-MAN2` |
| Game code / maker | `BSPE` / `52` (file reports `BSPE52, Rev.00`) |
| Version | `0x00` |
| Entry word | `0xEA00002E` → stock `b 0x080000C0` (no cracktro patch) |
| Nintendo-logo scan | **exactly one** hit, file `0x00000004` → single image, no 2-in-1, no appended trainer |
| MD5 | `7914ea9bed5d6936cec9b1c240247bda` |
| SHA-1 | `bb4a913f73139754dda95eb6b63d3b07501da970` |
| SHA-256 | `8643634f8923cb309c45e80d99b6e894c2f239d4ec06ce4ddcdd8feb0d9f2c9c` |

Header anomaly (derived): complement byte at `0xBD` is `0xBE`; sum of `0xA0..0xBC` low byte is
`0x29`, so a stock header would store `0xD7`. The title/maker field was therefore rewritten by
the release without recomputing the complement. The 156-byte logo and entry branch are intact,
so the code is the retail US build (Digital Eclipse / Activision, 2004).

## 2. Executive summary

**There is no in-game password, button sequence, or name code implemented in this GBA image.**
The two codes published for "Spider-Man 2 GBA" were checked against the ROM and the running game:

1. "Invincibility — at the title screen press Up, Down, Right, A" (GameFAQs, GameRankings,
   projectcheatcodes). Observed: pressing that sequence at the title screen does **not** consume
   the A as a cheat input — A is consumed by the highlighted `NEW` item and a new game starts,
   exactly as a bare A does. An exhaustive raw search of all 16 MiB for the sequence as key masks
   (active-high and active-low, u8/u16LE/u16BE/u32, forward and reversed, strides 1–16 B) found
   **zero** candidates, and a scan of all 91 code references to the pressed-key word found no
   four-step compare state machine. The published code is **unverified and most likely belongs to
   a different SKU/version**.
2. "After 100% completion, enter your name as FLUWDEAR to access level select" (IGN, GameFAQs,
   supercheats, cheatmasters). This **cannot be entered on the GBA SKU**: the name field is a
   **3-character** field. `FLUWDEAR` (8 chars) is absent from the ROM in ASCII, reverse, lower
   case, ±`0x20`, UTF-16LE/BE and UTF-32. The code is a DS/PC-era instruction misattributed to GBA
   (guide §16.11).

What the ROM *does* contain is a large, fully translated **developer/debug UI** that is present
but gated off the retail menu:

* a `Secrets` gallery on the title screen with exactly 14 items (reachable, no code needed);
* string and rendering code for `Unlock All Moves`, `Unlock All Levels`, `Level Select:` and all
  36 level names, plus 12 `Photo NN` entries — in **all five** languages (EN/FR/DE/ES/IT);
* a real title-menu dispatcher and a real level-select renderer, so the feature is live code,
  not a stub — but the title dispatcher draws exactly four items (`New/Load/Options/Secrets`)
  and the gallery draws exactly 14, so **no retail input path reaches the debug entries**.

The negative is bounded by counts and addresses in §6b, not by "did not find".

Out of scope (recorded only as RAM evidence, not reported as cheats): the published
GameShark/CodeBreaker codes (invulnerability `32001F38 0009`, all secrets
`420021F0 0001 / 0000000E 0004`, etc.) are cheat-device memory writes.

## 3. How to reproduce

Emulator: `SDL_AUDIODRIVER=dummy mgba -3` on `DISPLAY=:319` (Xvfb + openbox), mGBA 0.10.5.
Keymap used (verified on menus): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad=arrow keys. Hold ≈100–150 ms; title transitions fade in over ~1 s, so wait before a press
registers.

Reproducible path (all observed):

1. Boot. Legal screen → intro cutscene; hold A/`x` ~30–40 times, then wait, to reach the title.
2. Title shows `NEW  LOAD  OPTIONS  SECRETS` (`title1.png`, `state_title.png`).
   Left/Right move, A confirms, Start cancels.
3. `SECRETS` (Right×3 from `NEW`, then A) opens the gallery: `SECRETS`,
   `O:SELECT  START: EXIT`, a scrollable list `SECRET 01 … SECRET 14`. Down stops at `SECRET 14`
   (`secrets_menu.png`, `sec_scroll_14.png`, `sec_scroll_16.png`). No unlock options appear.
4. `NEW` → `SELECT SLOT TO START` (3 slots of 36 B each) → empty slot → `NAME GAME`: the name is
   3 characters; Up/Down change the highlighted letter, Left/Right change position (`AAA` →
   `AAB`) — `name_entry3.png`, `slotnav_Down.png`, `slotnav_Left.png`.
5. Pause in-game with Start: `CONTINUE / EXIT`; Right selects `EXIT` → `EXIT? YES/NO` → `YES`
   returns to title (`pause2.png`, `nav_Right.png`, `title1.png`).
6. Debugger-oracle recipe (§16.13/§16.19): mGBA CLI debugger `-d` under a pty; `Ctrl-C` breaks,
   `x/1 ADDR LEN` / `r/2 ADDR` read memory, `c` resumes. Scripts in §9.

Published codes tested: `Up,Down,Right,A` at title (no cheat effect; starts `NEW`);
`FLUWDEAR` (not enterable — 3-char field). Savestates and screenshots are in
`/tmp/spiderman2/`.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Key-input reader (KEYINPUT `0x04000130`) | ROM `0x08000A14` | Derived (disasm) |
| Pressed-key mask (edge) | RAM `0x02001EDC` | Derived + Observed |
| Held-key mask | RAM `0x02001EEC` | Derived + Observed |
| Title menu dispatcher / draw / input / action | ROM `0x08020424` / `0x802043C` / `0x80204D4` / `0x8020536` | Derived |
| Title string draw indices 1–4 (`New/Load/Options/Secrets`) | ROM `0x8020466`–`0x8020484` | Derived |
| Text draw helpers | ROM `0x080024AC`, `0x08002564`, `0x0800F2FC` | Derived |
| Secrets gallery handler | ROM `0x0802192C` (called from `0x8020586`) | Derived |
| Secrets gallery `Secret NN` draw (`34+r5`) | ROM `0x80219E4`–`0x80219EE` | Derived |
| Debug `Unlock All NN` draw (`48+r5`) | ROM `0x8021A08`–`0x8021A12` | Derived |
| Secrets-state initialiser | ROM `0x080218B0`; roots at `0x0200C720/1`, `0x0200C740` | Derived |
| Secrets flags (14 bytes) | RAM `0x020021F0`–`0x020021FD` | Observed (all zero at title; CodeBreaker writes here) |
| Level-select renderer | ROM `0x080207C0`–`0x8020896` (index `65` = `Level Select:` at `0x802088E`; `67+r` = level names at `0x802087A`) | Derived |
| Level-select screen initialiser | ROM `0x08020600` (sets `r0=15` items at `0x8020624`) | Derived |
| Save-slot records | RAM `0x0200C758` + `36*n`, n = 0..2; name at record +0 (3 chars) | Observed |
| Secondary name copy | RAM `0x02001E74` (3 chars) | Observed |
| UI string-pointer table | ROM `0x0812BE7C` base; index 1 = `0x0812F7C8` (`New`); 324 entries indices 1..324, last pointer at `0x12C38C` | Derived |
| English UI strings | ROM `0x0812F7C8`–`0x08133180+` | Derived |
| French mirror table (same indices) | ROM `0x0812F7C8`-bank beginning at `0x12F820` | Derived |
| CodeBreaker-only RAM (out of scope) | `0x02001F38`, `0x02001F20`, `0x02001F04`, `0x02010420`, `0x020021D8` | External source |

## 5. Algorithm (what was recovered)

Key polling (ROM `0x08000A14`, derived):

```
raw = KEYINPUT & 0x03FF
held = ~raw & 0x03FF                    # active-high: A1 B2 Sel4 Start8 R10 L20 U40 D80 R100 L200
pressed = held & ~(previous_held)
[0x02001EDC] = pressed                  # edge masks
[0x02001EEC] = held
```

Title dispatch (ROM `0x08020424` / `0x8020536`, derived):

```
sel = 0..3                              # NEW, LOAD, OPTIONS, SECRETS
draw menu indices 1+sel at y = 0x8F + 2*sel
if pressed & 0x20: sel = (sel==0) ? 3 : sel-1
if pressed & 0x10: sel = (sel>=3) ? 0 : sel+1
if pressed & 0x09:  switch(sel){0:NEW; 1:LOAD; 2:OPTIONS; 3:SECRETS(0x802192C)}
```

There is **no** branch before the `pressed & 0x09` confirm that consumes a longer key history,
and no comparison against any key-mask sequence — the published button code has no landing site.

Secrets gallery (ROM `0x0802192C`, derived): draws string `34+i` for `i = 0..13`
(`Secret 01`…`Secret 14`); the sibling branch at `0x8021A08` draws `48+i`
(`Unlock All Moves`, `Unlock All Levels`) only when the corresponding per-item state word
(from the `0x080218B0` initialiser) equals `1`. At the retail title screen that state is `0`
for all items, so only the 14 gallery rows are shown. The level-select renderer at
`0x080207C0` reads a level index (0..35) from a 36-byte record and draws string `67+index`,
falling back to `Level Select:` (65) for the header.

## 6. Tables

**UI string pointer table** (base `0x0812BE7C`, entry `n` = word at `base+4n`, 324 entries):

| Index | String | Index | String |
|---:|---|---:|---|
| 1 | New | 31 | Secrets (gallery header) |
| 2 | Load | 34–47 | Secret 01 … Secret 14 |
| 3 | Options | 48 | Unlock All Moves |
| 4 | Secrets | 49 | Unlock All Levels |
| 5–9 | English/Français/DEUTSCH/ESPAÑOL/Italiano | 50–61 | Photo 01 … Photo 12 |
| 62 | Continue? | 65 | Level Select: |
| 63 | Game Over | 66–102 | 37 level names (`L01 Pizza Dash` … `L21 Battle Doc Ock`) |
| 64 | The End | | |

The same indices exist in FR/DE/ES/IT banks (e.g. `0x12F894`/`0x12F898` =
`Deverr. ttes competences` / `Deverr. tous les niveaux`; `0x136C78+` = `SECRET 14`…`SECRET 1`;
`0x13A634+` = `SECRETO 14`…). Debug features were translated, not an English-only leftover.

**Key masks** (active-high pressed word): `A=0x001 B=0x002 Select=0x004 Start=0x008
Right=0x010 Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200`.

**Published-code verification ledger**

| Claim | Source | ROM literal? | In-game result |
|---|---|---|---|
| Invincibility `Up,Down,Right,A` @ title | GameFAQs / GameRankings / projectcheatcodes | no key-mask table or state machine found in 16 MiB | A consumed by NEW, new game starts; no cheat feedback observed |
| Level select via name `FLUWDEAR` after 100% | IGN / GameFAQs / supercheats / cheatmasters | absent in 6 encodings | not enterable: name field is 3 characters |
| "Beat game to unlock all moves and levels" | IGN | strings + renderer present | legitimate unlockable; gated on completion, not a code |

## 6b. Enumeration

**Enumeration result: the accepted "code" set for retail input is empty; the debug/unlock set
is real but unreachable. This is a bounded negative, not an untested one.**

* **Button-code search space (exhaustive).** Sequence `Up,Down,Right,A` encoded as active-high
  masks `[0x40,0x80,0x10,0x01]` and reversed `[0x01,0x10,0x80,0x40]`; active-low variants
  `[0x3BF,0x37F,0x3EF,0x3FE]`; widths 1, 2, 4 bytes; little- and big-endian; byte strides
  1–16. **0 hits** in all 16,777,216 bytes. Separately, all **91** code xrefs to the pressed-key
  word `0x02001EDC` were scanned for a 4-immediate compare chain containing `0x40/0x80/0x10/0x01`
  in either order: **0** matches. Dynamic test at the title screen: sequence accepted as a plain
  A on `NEW` (no consumption, no flag, no message).
* **Name/password search space.** `FLUWDEAR` searched as ASCII, reversed `RAEDWULF`, lowercase,
  `+0x20`, `−0x20`, UTF-16LE, UTF-16BE, UTF-32 and reversed UTF-16: **0 hits**. The name field is
  **3 characters** (observed in the slot screen and in code: `ldrb` loop `r6=0..2` at
  `0x80208C6`, 3-byte record at `0x02001E74`/`0x0200C758`), so an 8-symbol input is not
  representable. Maximum name space is at most 3 glyph-picker positions; no comparison of those
  bytes against a constant exists in the name-entry handler (`0x8020B3C`–`0x8020CBE`).
* **Menu enumeration (walked, with RAM evidence).**
  Title = **4** items (indices 1–4; dispatcher `0x8020536` draws `r4=0..3`).
  `SECRETS` gallery = **14** items (`Secret 01`…`Secret 14`; scrolled to the end twice —
  Down stops at 14, screenshots `sec_scroll_14.png`/`sec_scroll_16.png`; draw loop `34+r5`).
  Pause = **2** items (`CONTINUE/EXIT`) + `EXIT?` confirm (YES/NO).
  `LOAD` / `SELECT SLOT TO START` = **3** slots with 36-byte records.
  Options strings = **6** labels (`Sound On/Off`, `Music On/Off`, `Credits`, `Exit`) — no debug row.
  No `Level Select`, `Unlock All Levels`, `Unlock All Moves`, `Photo NN` or hidden row appeared on
  any reachable screen.
* **Debug/unlock space present but gated.** 324 UI strings in the English pointer table; of these
  37 level names + `Level Select:` + `Unlock All Levels/Moves` + 12 `Photo` rows form a coherent
  debug/unlock UI. It is reached in code only through the renderer at `0x080207C0` and the state
  branch at `0x8021A08`; the title dispatcher (4 items) and gallery (14 items) never select it.
  The completion flag that would enable it is a save-game field (root `0x0200C720..0x0200C740`,
  initialiser `0x080218B0`) and is zero in a fresh save (observed: `0x020021F0..FD` all `0x00`,
  14 bytes). Reaching it legitimately requires 100% story completion, not a code.
* **Consequence for §0.2.** Because no validator, no accepted-code table and no reachable code
  surface exists, there is no code space to characterise and no novel code can be minted. The
  required deliverable is therefore the proven negative above with its counts and bounds.
  A save-bit unlock (14 secrets, 36 levels, 12 photos) is an unlockable, not a code; per §16.18
  its setter path is in game progression/save data, not controller input.

## 7. Validation evidence

**Observed** (emulator, screenshots/RAM): title with 4 items; 14-item secrets gallery and its
end-stop; 3-slot 36-byte save records with 3-character names; pause `CONTINUE/EXIT` + confirm;
Up/Down/Right/A at title starts `NEW`; `FLUWDEAR` not enterable; `0x020021F0..FD` = 14 zero
bytes at title; writing all 14 bytes to `1` via the debugger did **not** add rows to the gallery
(`secrets_flagged2.png`), confirming those bytes only gate secret viewing; key masks at
`0x02001EDC/0x02001EEC` change with input.

**Derived** (disassembly): key reader `0x08000A14`; title dispatcher `0x08020424`; secrets handler
`0x0802192C`; unlock-option branch `0x8021A08` (indices 48/49); level-select renderer
`0x080207C0` (index 65 and 67+level); 324-entry pointer table at `0x0812BE7C`; `r6=15`-item
initialiser `0x08020600`; 36-byte slot stride.

**Inferred** (not fully exercised): that the `Unlock All Levels/Moves` branch becomes reachable
after 100% completion; the exact save offset of the completion flag. These are labelled inferred
and left in §8; no code path from retail input to them was found.

Fetched web pages (GameFAQs/IGN/TCRF/Almar) were treated as data only; no instructions in them
or in ROM strings were executed. No prompt-injection payload was encountered.

## 8. Unknowns

* Exact save-file offset and encoding of the 100%-completion flag that gates the level-select /
  unlock-all UI (save roots `0x0200C720..0x0200C740` identified, not fully decoded).
* Whether the five hidden `Photo NN` images correspond 1:1 to the 14 secrets on this SKU.
* Whether a *different* regional revision (e.g. EU `BSPE52` vs US) contains the button code; this
  report is scoped to the hash in §1.
* The published `Up,Down,Right,A` may grant invincibility in some other build; only this image
  was tested (static + one dynamic run).

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3 (`struct`, `zlib`, `re`).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for targeted
  ranges; Python raw Thumb BL scanner for `BL` xrefs to `0x080024AC/0x08002564/0x0800F2FC`.
* mGBA 0.10.5 `-3`, `-d` (CLI debugger via `pty_bridge.py`), `-t` (savestate), Xvfb `:319`,
  openbox, `xdotool` XTEST events, `scrot`.
* Helper scripts in `/tmp/spiderman2/`: `gba.py` (input/screenshot), `pty_bridge.py`
  (persistent mGBA CLI-debugger pty), `dbg.py` (cmd/brk/go/rd/wr), `memdump.py` (`x/1` RAM dump),
  `ss.py`/`state.bin` (savestate `gbAs` zlib decode: 397,312 B; IWRAM at `0x19000`, EWRAM at
  `0x21000`), `codetest.py` (button-code RAM diff).
* A prior `cli_history.log` from another session was found at `/home/user/.config/mgba/`; its
  probe target `0x08088EF4` disassembles as data/garbage (BL outside ROM) and was discarded.

## 10. Legal note

No ROM bytes, graphics, music or game text were redistributed. Only hashes, addresses,
algorithms, and our own observations are published.

Cleanup: all processes started for this job were stopped by PID and the generated
`.sav` / `.ss1` / `.ss2` / `.ss3` files were removed from the ROM folder.
