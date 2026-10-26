# 007: Everything or Nothing (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-24.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

Scope note: **in-game / developer-intended cheats only**
(button sequences, hidden menus, passwords, unlockables).
GameShark/CodeBreaker/RAM-patch codes are out of scope.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/007: Everything or Nothing/007: Everything or Nothing.gba` |
| Size | 8 MiB (`0x800000`) |
| Header title | `BOND EON` |
| Game code | `BJBE` |
| Maker code | `69` |
| Software version | `0` |
| MD5 | `b63b2244edc2385ae1eab9c8ee448c6f` |
| SHA-1 | `fc6163f99b71b05c10686a0d29010b31274e1dc4` |
| SHA-256 | `45d0003d5612d4f0a4b57adcf7ddbe6bb10c1e7f7c01f02472967fc690cf6676` |

ROM addresses below are `0x08000000 + file_offset`. All findings are tied to
this exact hash; another revision may differ.

---

## 2. Executive summary

No developer cheat-code system (button sequence, password screen, debug menu)
was found in this ROM. The evidence:

1. **Public lists agree.** The GameFAQs GBA cheats page (via Wayback),
   SuperCheats, Vizzed and IGN list exactly one in-game unlockable for the GBA
   build — **Blackjack mode (earn 2,500 style points)** — and no button-sequence
   cheats. The PS2/GameCube/Xbox builds have pause-entered 5-button codes and
   platinum/gold unlock ladders; none of that exists on GBA.
2. **Title screen reads exactly one button.** The state-10 update handler
   (`0x08031B90`) and all five of its sub-handlers were disassembled in full:
   the only input tested anywhere in that code is **bit 0 (A)** of the
   newly-pressed word at `0x030049F0`. No modifier, counter, or sequence buffer.
3. **Main menu ignores modifiers.** Sixteen held-chord combos
   (Select / Start / L / R / L+R / L/R+Select / L/R+Start / Select+Start /
   L+R+Select / L+R+Start / L+R+arrows) were probed dynamically with the menu
   state read from RAM: no effect except L+R+Up/Down, which behave as normal
   Up/Down navigation.
4. **Pause menu has no sequence accumulator.** The state-6 update handler
   (`0x0803A8B9`) tests only single-press navigation masks (Up/Down, A
   confirm, B back,one Start/Select check); there is no press-history buffer or
   constant sequence table of the kind the console 5-button codes would need.
5. **Text is not searchable plaintext.** No ASCII/UTF-16/XOR/add-encoded copy
   of any on-screen sentence exists in the ROM (bounded pattern search, §5.3),
   so there is also no plaintext cheat/password table to find by strings.

Net: on this build, "cheats" = the single Blackjack style-points unlockable.
Everything else published for this title is a memory-editing (GameShark-class)
code, out of scope.

---

## 3. How to reproduce

### Emulator

```bash
sudo apt-get install -y mgba-sdl xvfb xdotool scrot imagemagick openbox
Xvfb :99 -screen 0 1024x768x24 &
DISPLAY=:99 openbox &
DISPLAY=:99 SDL_AUDIODRIVER=dummy mgba -3 "007: Everything or Nothing.gba" &
```

`openbox` (or any WM) is required: without it `xdotool windowfocus` does not
deliver keys to mGBA. Screenshots: `import -window <wid> out.png` (scrot crops
were unreliable here). Default mGBA keymap: A=`x`, B=`z`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows. Hold keys ~200 ms.

GDB stub: `mgba -3 -g ...`, then `gdb-multiarch -ex 'set architecture arm' -ex 'target remote :2345'`.
Batch mode stalls once the target runs; driving GDB through a command fifo
(`kill -INT` to interrupt, `continue` to resume) works. Hardware
**read** watchpoints did not fire on this stub; plain breakpoints
(e.g. `break *0x080193B0`) and memory reads work.

### Menu paths (observed)

```
Language select → English → copyright → Bond-barrel → title (START)
Title (A) → fade → Main menu (New Game / Load Game / Multiplayer / Options / GCN Link)
Options → Sound Volume / Music Volume / Difficulty / Language / Credits / Blackjack
Blackjack → "Earn 2500 Style Points to unlock Blackjack."
New Game → Mission: 1 / Open / Open → Confirm Overwrite → Yes → intro → Mission 1
Mission 1 (Start) → Paused (Continue / Inventory / Objectives / Controls / Options / Quit)
```

### Combos exercised (main menu, state read from RAM — no effect unless noted)

`Select`, `Start`, `L`, `R`, `L+R`, `L+Select`, `R+Select`, `L+Start`,
`R+Start`, `Select+Start`, `L+R+Select`, `L+R+Start`, `L+R+Left`,
`L+R+Right` → state `0x0B`, selection unchanged.
`L+R+Up` / `L+R+Down` → normal cursor move (selection 3→2→3).

---

## 4. Address map

| ROM address | What |
|---:|---|
| `0x08019318` | Input poll, called each frame from `0x0801A898` (LR observed in GDB) |
| `0x080193B0` | Key-transform core: `held = KEYINPUT ^ 0x3FF`, `pressed = held & (held ^ prev)` |
| `0x0804AEA0` | State dispatch table, 24 states × 12 bytes (init/update/render) |
| `0x08031B90` | State-10 (title) update; sub-dispatch via table at `0x0804F6D8` |
| `0x08031BB4`/`D40`/`DEC`/`F18`/`FA0` | Title sub-handlers 0–4 |
| `0x080319B8` / `0x08032018` | State-10 init / render |
| `0x080333AD` | State-11 (main menu) update |
| `0x0803A8B9` | State-6 (pause) update |
| `0x08012E28`, `0x08016C68` | Title tail callees (flag/DMA + sprite updater; no input reads) |

RAM used by the input path:

| Address | Use (derived) |
|---|---|
| `0x03004A78` | held (active-high button bits) |
| `0x03004A7C` | previous held |
| `0x030049F0` | newly pressed (canonical reader for menus) |
| `0x03004008` | newly pressed (copy) |
| `0x03004010` | held (copy) |
| `0x03004028` / `0x03004A80` | released |
| `0x03003910` | state index; `+8` = menu selection; `+0x10`/`+0x14` = sub-phase/timer |

GBA key bits (active-high after transform): 0 = A, 1 = B, 2 = Select,
3 = Start, 4 = Right, 5 = Left, 6 = Up, 7 = Down, 8 = R, 9 = L.

---

## 5. Algorithm / analysis detail

### 5.1 Key transform (`0x080193B0`, derived)

```c
u16 raw  = ~*(volatile u16*)0x04000130 & 0x3FF;  // invert active-low input
u16 prev = held;
held     = raw;
pressed  = raw & (raw ^ prev);    // -> 0x030049F0 and 0x03004008
released = prev & (raw ^ prev);   // -> 0x03004028
```

Literal pool confirms the mask (`0x080193FC`-relative word `0x3FF`) and every
address above (`struct.unpack_from("<I", ...)`; objdump prints pool words as
code, so raw reads are mandatory).

### 5.2 Title update (`0x08031B90`, derived)

Sub-phase dispatch on `[0x03003910+0x10]` (0–4) through `0x0804F6D8`:

* sub 0/2/4: timed animation steps; sub 4 expiry advances to state 4
  (transition into the main menu, state 11).
* sub 1 (`0x08031D40`): the `ands` at `0x08031DB4` tests **timer bit 0**, not a
  button (`r1` is `[state+0x14]`).
* sub 3 (`0x08031F18`): the `ands` at `0x08031F6C` tests **`(timer & 3) == 3`**.
* common tail (`0x08031FD4`): `ldrh r1,[0x030049F0]; ands r0,r1` with `r0 = 1`.
  Only **bit 0 (A)** is ever tested. On press: sound (`0x08022040`) + set
  state 4 (`0x0801A8F0`).

No other literal in `0x08031000–0x08033000` references any input global, and
both every-frame callees were verified input-free (§4). There is nowhere for a
modifier/sequence check to live on this screen.

### 5.3 Text encoding (bounded negative, derived)

* `strings -t x`: 108 k lines, all code/data noise; no menu, dialogue,
  password, cheat, or debug strings. One `$Id: player.c,v 1.4 ...` marker.
* LZ77/RLE BIOS-format scan of the whole image: 495 blocks, none containing
  text (only a `0x32`-fill block).
* Pattern-equality search (source-equivalence, not literal bytes) for six
  on-screen strings in both 8-bit and 16-bit stores: zero matches for every
  string longer than 8 characters (`set the charges`, `get out of there`,
  `Sahara Desert`, `Earn 2500 Style Points to unlock Blackjack.`);
  short strings (`New Game`, `Sound Volume`) match only at chance level.
* A `u16` identity ramp at `0x25A68C` and a glyph-index-like `u16` text bank
  around `0x500000` (small values, `0x0000 0x0000` separators) are consistent
  with tile-index text, as seen in other GBA titles — not pursued, since no
  cheat surface depends on it.

### 5.4 Pause handler (`0x0803A8B9`, derived)

Submenu dispatch on `[struct+16]`; observed mask tests are `& 2` (B),
`& 0xC0` (Up/Down navigation), `& 0x20`, single-bit Start/Select checks —
all single-press navigation/confirm/back. No history buffer, no multi-press
comparator, no constant sequence table. A console-style 5-press code has no
mechanism here.

---

## 6. Tables

State dispatch table (`0x0804AEA0`, init/update/render):

| # | init | update | render | role (observed/inferred) |
|---:|---|---|---|---|
| 0 | `...A9FD` | `...A9FD` | `...A9FD` | idle stub |
| 4 | `...C869` | `...CA31` | `...CBD9` | transition/fade (inferred) |
| 6 | `...A759` | `...A8B9` | `...AB3D` | pause menu (observed) |
| 10 | `...19B9` | `...1B91` | `...2019` | title (observed) |
| 11 | `...32C5` | `...33AD` | `...34DD` | main menu (observed) |

(States 1–3, 5, 7–9, 12–23 enumerated from the table but not identified;
see §8.)

---

## 7. Validation evidence

**Observed (emulator + screenshots)**
- Language/title/main-menu/Options/Blackjack-message screens (§3 paths).
- `L+R+Up/Down` move the main-menu cursor; all other modifier chords do nothing
  (RAM state reads, §3).
- Title advances on A; auto-advances on animation timeout (sub-4 path).

**Observed (GDB stub)**
- Input poll caller: `0x080193B0` called from `0x0801A898`.
- `0x03003910` = state index (10 title, 11 menu, 6 pause); `+8` = selection
  (2→3 on Down, 3→2 on Up).

**Derived (disassembly, Thumb, literals confirmed by raw reads)**
- Key transform, title-only-A check, pause navigation masks, input-free tail
  callees, 24-entry state table.

**Inferred**
- `0x03004A80/88` are second-player/released slots (multiplayer poll loop at
  `0x08019344` handles 4 pads; not exercised — no link cable).
- Glyph-index text encoding from the `u16` bank shape; decoder not reversed.

---

## 8. Unknowns

- Pause 5-press sequences were ruled out statically, not by exhaustively
  entering sequences dynamically.
- The 2,500-style-point Blackjack threshold was observed as a message but not
  earned in gameplay (would require a full playthrough or save editing —
  the latter out of scope).
- States 1–3, 5, 7–9, 12–23 unidentified (gameplay, driving, multiplayer,
  GCN-link, credits, etc.); a cheat handler could theoretically live in an
  unexamined state, but the public record gives no reason to believe one does.
- GCN Link screen not explored (needs link hardware).
- `Shift+F1` in mgba-sdl wrote a PNG screenshot (`.ss1`), not a loadable
  savestate — savestate-based experiment loops were therefore unavailable.

---

## 9. Tooling

| Script | Purpose |
|---|---|
| session `regscan.py` (not archived) | literal-pool + Thumb-LDR scan for I/O register readers |
| session `patsearch.c` (not archived) | equality-signature search for 8/16-bit text stores |
| session `lzscan.py` (not archived) | BIOS LZ77/RLE decompress-and-grep for text |
| session `probe.py` / `gba.py` (not archived) | xdotool key driver, `import`-based screenshots, RAM-state combo prober |

Environment notes (portable lessons): a window manager (`openbox`) is required
for xdotool key delivery; pixel-diff cheat probing fails on animated
backgrounds — read menu state from RAM via the GDB stub instead; GDB batch
mode stalls once the target runs, drive it via fifo + `kill -INT`.

No ROM, graphics, or text from the game is redistributed here; only addresses,
algorithms, and short identifiers needed to describe the findings.
