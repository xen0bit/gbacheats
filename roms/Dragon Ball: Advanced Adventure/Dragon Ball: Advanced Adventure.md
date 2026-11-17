# Dragon Ball: Advanced Adventure (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dragon Ball: Advanced Adventure.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| `file` ID | Game Boy Advance ROM image: "DRAGONBALLAA" (BDVE70, Rev.00) |
| Header title (0xA0) | `DRAGONBALLAA` |
| Game code (0xAC) | `BDVE` (Europe) |
| Maker (0xB0) | `70` (Atari) |
| Version (0xBC) | 0x00 |
| Entry word | `0xEA00002E` → stock `b 0x080000C0`, **not** a cracktro |
| Fixed 0x96 / main unit / device | 0x96 / 0x00 / 0x00 |
| Complement (0xBD) / checksum (0xBE) | 0x71 / 0x0000 |
| MD5 | `442bab94b7b3ba7e4a8799d18de52731` |
| SHA-1 | `1338584d8cfa57402603197e65d2e2ff0184d24f` |
| SHA-256 | `89a13559f76cf708d679c2d4f1d90d97333205e27dae72b47a7200715c57702e` |

**Phase 0 result (Observed):** exactly one Nintendo-logo occurrence, at file offset `0x4`
(header base `0x0`, ROM `0x08000000`) → a single retail image, not a 2-in-1/multiboot
pack and no appended trainer. The final 0x80 bytes are all `0xFF` (normal padding).
The stock entry branch rules out a patched intro. A build string at file `0x0D701D1`
reads `Mon Dec 19 17:01:56  2005`. No ROM, save, or trainer patch was applied for
analysis.

## 2. Executive summary

This image contains **one complete, dormant button-code implementation** for the
widely published title-screen unlock code, but **the code is unreachable (dead
code) in this European build**: entering it, or any variant, has no observable or
RAM-visible effect.

* **Published code** (CheatCC, Neoseeker, ChapterCheats, CheatBook, GameFAQs Q&A,
  and a 2005 Kanzenshuu forum post quoting Bandai's official site):
  `L, R, Up, Down, L, R, Left, Right, R, R, Right` on the title screen → claimed to
  unlock a fourth mini-game, all bonus characters and extras. A SuperCheats Q&A on
  the same page reports "it doesn't work … Mine also don't work in any screen",
  which agrees with this image.
* **ROM evidence (Derived):** the exact 11-press sequence is stored once, as active-high
  `u16` key masks, at ROM `0x08A63B14`, terminated by `0x0000`. A validator at
  `0x080F2CD8` walks that table with a progress byte and, at index 11, writes save
  flags (`0x02029FC8[0..2] = 1`, `0x02029F32` bit 0 = 1) and calls `0x0810ADB8`.
* **The fatal gap (Observed):** the validator has **no callers** — zero Thumb `BL`
  xrefs into its whole code block `0x080F2C00–0x080F2E00`, no function-pointer
  literal, and a live breakpoint at `0x080F2CD8` never fires while other title-screen
  functions in the same block (`0x080F2C84`) fire immediately. A write watchpoint on
  the key-state address the validator reads (`0x03003F6C`) never fires, and that
  address reads `0x0000` even while L is physically held.
* **Dynamic result (Observed):** entering the published code, a changed first-two-
  presses variant, and an 11→5-truncated prefix on the title screen left the flag
  word at `0x02029FC8` at `0x00000000` in every case. No character, Collection
  entry, or menu changed.
* **Scope:** no password/code-entry UI exists; no ASCII UI text at all (the game uses
  font/tile indices). No hidden/debug menu was found on any screen.
* **Family context:** nothing is shared with the other GBA *Dragon Ball* images in
  this collection at the code-table level. Unlike *GT* (suffix-matched button codes)
  this build has a single fixed 11-press table with a 0x0000 terminator and no
  action-dispatch suffix; unlike *Taiketsu*'s dead debug menu there is no menu to
  walk — here the dead artifact is the validator itself. Treat this as an independent
  engine (Atari/Webfoot, game code `BDVE`).

## 3. How to reproduce

**Environment:** mGBA (SDL, `/usr/local/bin/mgba`), `Xvfb :315 -screen 0 1024x768x24`,
`openbox`, `SDL_AUDIODRIVER=dummy`. Keymap used (mGBA SDL defaults):
A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys.
Holds of 70–100 ms with 100–150 ms release gaps; verified by menu cursor movement
and by pressing `s` on the Collection screen (pages right).

**Menu path (all screens walked, each verified by screenshot):**
1. Title: "DRAGON BALL ADVANCED ADVENTURE" / "PRESS START". ← code entry point.
2. `Start` → **Data Menu**: DATA1 / DATA2 / DATA3, all "NO DATA"; `A` selects a slot.
3. Difficulty selector: EASY / REGULAR / HARD (`Left`/`Right`), `A` confirms.
4. **Game Menu**: STORY, ONE-ON-ONE, LINK MODE, OPTION (2×2 grid; `A` selects).
5. **OPTION**: COLLECTION, ERASE SAVE DATA?
6. **COLLECTION**: 2 pages (`L`/`R`) × 18 cells = 36 slots, all empty on a fresh save.
7. **ONE-ON-ONE** character select: 2×2 grid — GOKU (1P), KRILLIN (CPU), two "?" cells.
8. **STORY**: long text intro → side-scrolling platformer → world map ("Goku's House",
   several "?" nodes).
9. **PAUSE** (`Start` in-game): exactly two entries — "Back to game", "Back to map";
   the latter asks "Play data for this area will not be saved. Okay?" (No/Yes).
10. No hidden/debug screen appeared at any point, including after the code attempts.
    LINK MODE is present but is a link-cable multiplayer entry and was not entered
    (no second console available); no code behavior is documented there.

**Code entry tests (all on title screen, from a fresh savestate each time):**
* Published: `a s Up Down a s Left Right s s Right` (L,R,U,D,L,R,←,→,R,R,→).
* Unpublished variant minted for this report: swap first two presses →
  `s a Up Down a s Left Right s s Right` (R,L,U,D, …).
* Bounds test: 5-press prefix `a s Up Down a`.
* RAM read with mGBA's `-d` PTY debugger (`r/4 0x02029FC8`): `0x00000000` before,
  after the published code, after the variant, and after the prefix.
* Breakpoint walk: `b 0x080F2CD8`, then all of the above menu paths — zero hits;
  control breakpoint `b 0x080F2C84` hit at once, proving breakpoints work.

## 4. Address map

| Item | File offset | ROM / RAM address | Evidence |
|---|---:|---|---|
| Published code table (11×u16 + 0x0000) | `0xA63B14` | `0x08A63B14` | Derived (literal + exact byte match) |
| Validator (Thumb) | `0xF2CD8` | `0x080F2CD8` | Derived (disassembly) |
| Validator literal pool | `0xF2CF8` / `0xF2CFC` | `0x080F2CF8` = `0x03003F6C`; `0x080F2CFC` = `0x08A63B14` | Derived |
| Key-state word read by validator | — | `0x03003F6C` (u16) | Derived; **Observed always 0x0000** |
| Title-screen state struct (r4 in nearby live function) | — | `0x03003F94` (index at +5, flag at +6 in the validator's own struct) | Observed / Derived |
| Unlock flag triple written at index 11 | — | `0x02029FC8`, `0x02029FC9`, `0x02029FCA` ← 1 | Derived; Observed never set |
| Extra flag | — | `0x02029F32` bit 0 ← 1 | Derived |
| Post-unlock call | `0x10ADB8` | `0x0810ADB8(r0=0x388)` | Derived (sound/effect; not exercised) |
| Live title function (control) | `0xF2C84` | `0x080F2C84` | Observed breakpoint hit |
| Build string | `0xD701D1` | — | Observed (`Mon Dec 19 17:01:56 2005`) |

ROM address = `0x08000000 + file offset` throughout (single image, base `0x0`).

**Validator pseudocode (Derived, from `objdump -M force-thumb` at `0x080F2CD8`):**

```
check_code(state):                     # r0 = state struct pointer
    idx = state[5]                     # ldrb r3,[r4,#5]
    expected = *(u16*)(0x08A63B14 + 2*idx)
    current  = *(u16*)0x03003F6C       # active-high key mask, per table encoding
    if (expected & current) != 0:
        state[5] = idx + 1             # advance progress
    elif current != 0:
        state[5] = 0                   # wrong key -> reset
    # current == 0 (no key): hold progress
    if state[5] == 11:
        (u8*)0x02029FC8 = [1,1,1]
        *(u8*)0x02029F32 |= 1
        state[6] = 1
        call 0x0810ADB8(0x388)
        state[5] = 0
```

The match is `(expected & current) != 0`, so holding extra buttons alongside an
expected button would still advance — but this is moot because the function is
never invoked.

## 5. Algorithm

There is no password/checksum algorithm. The implementation is a fixed-sequence
button matcher:

1. Table = 11 consecutive `u16` key masks, then `0x0000` terminator:
   `0x0200` (L), `0x0100` (R), `0x0040` (Up), `0x0080` (Down), `0x0200` (L),
   `0x0100` (R), `0x0020` (Left), `0x0010` (Right), `0x0100` (R), `0x0100` (R),
   `0x0010` (Right).
2. One progress byte, advanced when `table[i] & current_keys` is nonzero, reset to
   0 on a different nonempty key state, unchanged on an empty key state.
3. Acceptance at `i == 11` writes two flag regions and resets progress.
4. Reachability gate: **none wired** — the routine has no caller in this build.
   Static caller analysis (0 `BL` xrefs over `0x080F2C00–0x080F2E00`, 0 pointer
   literals to `0x080F2CD8`/`0x080F2CD9`) and the live breakpoint test agree.

## 6. Tables

| Offset | Value | Meaning |
|---|---|---|
| `0x08A63B14` | 0x0200 | L (press 1) |
| `0x08A63B16` | 0x0100 | R (2) |
| `0x08A63B18` | 0x0040 | Up (3) |
| `0x08A63B1A` | 0x0080 | Down (4) |
| `0x08A63B1C` | 0x0200 | L (5) |
| `0x08A63B1E` | 0x0100 | R (6) |
| `0x08A63B20` | 0x0020 | Left (7) |
| `0x08A63B22` | 0x0010 | Right (8) |
| `0x08A63B24` | 0x0100 | R (9) |
| `0x08A63B26` | 0x0100 | R (10) |
| `0x08A63B28` | 0x0010 | Right (11) |
| `0x08A63B2A` | 0x0000 | terminator / no match at index 11 |

The bytes immediately before/after this table belong to a graphics/script data bank
(`0x08A63Axx–0x08A63Dxx`) referenced by many sprite routines; they are not additional
codes. State flags as in §4.

Published codes verified: the single 11-press sequence above is present **literally
and exactly once** in the ROM. No other published code string or button sequence was
found. Out-of-scope CodeBreaker/GameShark codes exist for this title (e.g.
`32029F36 0063`) and were deliberately not analyzed or tested.

## 6b. Enumeration

**Space definition.** Alphabet = the 10 active-high GBA key bits
(`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200`). The table has **1 entry**, fixed length
**11 presses**, each entry a single key bit, with a `0x0000` terminator. The raw input
space for an 11-press sequence is 10^11 ≈ 1×10^11; the table's accepted set is
exactly **1** sequence. There is no suffix/action dispatch, no variable length, no
checksum, and no second table: literal searches for the published sequence under
active-low encoding, reversed order, L/R-swap, Up/Down-swap, left/right-swap, and
one-byte-per-press all returned **0** hits; prefix lengths 3/4/5/6 each returned
**exactly 1** hit (the same table). A whole-ROM scan for runs of ≥4 consecutive
`u16` values with ≤2 key bits set returned 14,378 runs (nearly all compressed
graphics noise); only one is the published code table.

**Validator model / oracle limits.** The pseudocode in §4 is precise enough to
reimplement, but cannot be used as a live oracle: the function has no caller, and a
breakpoint at it never fires. Its key-state input `0x03003F6C` was observed `0x0000`
both idle and with L held, and a write-watchpoint there never fired during code
entry — so even a forced call with real button input would not advance.

**Novel code minted and tested.** `R, L, Up, Down, L, R, Left, Right, R, R, Right`
(the published sequence with the first two presses swapped) appears in no published
list. Entered on the title screen: **rejected** — `0x02029FC8` remained
`0x00000000` (Observed). Because the whole system is unwired, **no code, published
or novel, can produce an effect in this build**; this is a *dead-code* result, not a
claim that a working code generator was found.

**Bounds proven by rejection (Observed):**

| Input | `0x02029FC8` after | Effect |
|---|---|---|
| none (baseline) | `0x00000000` | — |
| published 11-press code | `0x00000000` | rejected |
| novel first-two-swapped 11-press code | `0x00000000` | rejected |
| 5-press prefix (out-of-length) | `0x00000000` | rejected |
| validator breakpoint across 14 menu states | n/a | 0 hits (control breakpoint: 1 hit) |

**Negative-result boundary (searched spaces, with counts):**
* `strings -t x -n 4` keyword sweep over password/cheat/debug/secret/unlock/guest/
  hidden/master/level select/sound test/press start/continue/option: **0 hits**.
* Literal searches (ASCII, +0x20 shifted, uppercase-folded) for `DRAGON`, `PRESS`,
  `START`, `ATARI`, `WEBFOOT`, `BANDAI`, `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`,
  `OPTIONS`, `UNLOCK`, `CHARACTER`, `CREDITS` etc. across all 16 MiB: only `DRAGON`
  at `0xA0` (header) and the build-year strings. The UI is font/tile-indexed, so a
  zero string hit is expected and does not alone prove absence (guide §11).
* Published 11-press sequence as `u16` LE active-high: 1 hit (`0xA63B14`); all 6
  alternate encodings: 0 hits.
* Thumb LDR-literal reads of the global key word `0x03003F6C`: **72 sites**; only
  the one inside `0x080F2CD8` is tied to the code table, and that function has
  **0** incoming `BL` xrefs (whole `0x080F2C00–0x080F2E00` block: 0 `BL` xrefs).
* Menus enumerated: 10 distinct screens/states (§3), including every pause entry;
  no hidden debug entry found.

## 7. Validation evidence

**Observed** (emulator / debugger / raw bytes):
* exact 11-mask table bytes at file `0xA63B14`;
* single Nintendo logo; stock entry word; hashes and header fields in §1;
* all 10 screens in §3, including 36 empty Collection cells and 2 locked "?" cells;
* entering published code, novel variant, and short prefix — no change to
  `0x02029FC8` (always `0x00000000`);
* validator breakpoint: 0 hits across 14 menu states; control breakpoint
  `0x080F2C84`: 1 immediate hit;
* `0x03003F6C` = 0 idle and with L held; write-watchpoint there: 0 hits.

**Derived** (disassembly / static analysis):
* validator control flow at `0x080F2CD8` and its literal pool values;
* unlock flag addresses and the call to `0x0810ADB8`;
* no `BL`/pointer xrefs to the validator; table count = 1, length = 11.

**Inferred:**
* the flag triple at `0x02029FC8` is most likely the "extras / mini-game / bonus
  character" save flags the published code claims to set, based on the three
  adjacent byte writes and the nearby save-data flag at `0x02029F32`. It was never
  observed set, so the exact in-game meaning of each byte remains unproven.
* the call `0x0810ADB8(0x388)` is probably a sound/notification effect; not heard
  (`SDL_AUDIODRIVER=dummy`) and not exercised because the validator never runs.
* the difference between this EUR build (`BDVE70`) and the build the codes were
  published for may be regional; only this image was analyzed.

## 8. Unknowns

* Whether any other regional revision of this game wires the validator up (only
  `BDVE70` was available). The published reports may refer to a USA/JP build.
* Whether `0x03003F6C` is a stale/shared field that some later game state populates;
  a write-watchpoint at the title screen never fired, but in-game states were not
  watched exhaustively.
* Exact semantic meaning of the three `0x02029FC8` flag bytes and of the
  `0x0810ADB8(0x388)` side effect — both unreachable here.
* LINK MODE contents (requires a second GBA/link cable); no code surface is
  documented there and no ROM literal matches any published code for it.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep` — Phase 0/1.
* Python 3 scripts in `/tmp/opencode/dballadv/`: `key.py` (XTEST input),
  `scan_masks.py` (whole-ROM key-mask table scan), `scan_keys.py` (live RAM key-state
  scan), `dbg.py` (mGBA `-d` PTY controller), `all_screens_bp.py` (breakpoint menu
  walk), `final_test2.py` (pre/post RAM proof), `gdbcli.py` (attempted raw GDB client).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* mGBA `-3` with `-d` PTY debugger; `Xvfb :315`, `openbox`, `xdotool`, `import`.
* Note: the mGBA GDB stub (`-g`) returned empty/malformed packets and crashed the
  instance on connection in this environment; the `-d` pty debugger was used
  instead (guide §16.2/§16.13). Savestate (`gbAs` zlib chunk) diffing was attempted
  first and abandoned as too noisy across animation frames.
* Web: search snippets plus Kanzenshuu forum; direct fetches of TCRF and GameFAQs
  returned HTTP 403 and are recorded as unverified-by-fetch (the code text is
  corroborated by four independent cheat sites found via search).

No ROM or copyrighted asset is redistributed here; only addresses, hashes, and
reconstructed logic are published.
