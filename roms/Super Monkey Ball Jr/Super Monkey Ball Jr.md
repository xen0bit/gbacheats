# Super Monkey Ball Jr. (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| Path | `roms/Super Monkey Ball Jr/Super Monkey Ball Jr.gba` |
| Size | 4,194,304 bytes (0x400000, flat 4 MiB, no sub-images) |
| Header title | `MONKEYBALLJR` |
| Game code / maker | `ALUE` / `78` |
| Version / fixed byte | `0x00` / `0x96` |
| Header complement | `0x31` (recomputed `0x4A`; header checksum field `0x0000`) |
| Entry word | `0xEA00002E` → stock `0x080000C0`, stock ARM crt0, no cracktro strings in first 4 KiB |
| MD5 | `77edf4f506b3343e15efe61d64944eba` |
| SHA-1 | `0d994a58b7acdfe9357e5405acebe232128b80fe` |
| SHA-256 | `de40cac26ae34908b91885d1faaa60e5cf5cbd66b60b2ffdf9c96d354ca5e897` |
| In-game build date | `Oct  3 2002 17:14:24` (Mini FE screen) — U.S. revision |

The header checksum/complement mismatch is a header-rebuild artifact (guide §16.1); the boot path is the stock branch and the first 4 KiB contain no trainer/cracktro. File offset = ROM address − `0x08000000` everywhere.

## 2. Executive summary

This game has **no password/code-entry system**. Its developer-intended cheats are a single **title-screen button-code system**: a ROM table of exactly **4 press sequences** (masks as 32-bit words, stride 0x2C), matched by the validator at `0x08000D8A`. Three are documented publicly (Enable All, Blocky Mode, Nice Try). The fourth, **`mirrormode`** (`Right, Right, Left, Left, Right, Left, A`), is in **no published list**: the validator accepts it (`progress = 7`, `code index = 2`) but the dispatch switch has **no case for index 2**, so it has no effect — a shipped-but-unfinished cheat entry (a bounded dead-code result, not a "not found").

A second, separate surface exists: three developer debug menus (Mini FE, Tweak Screen, Advanced Options) gated by changing the FE screen index at RAM `0x030004B4` to `0x00`, `0x0A`, or `0x17`. They are **not reachable by any controller input**: the value is a menu-navigation screen ID overwritten every frame, published instructions require a CodeBreaker device (out of scope here), and there is zero in-engine L+R test. They are documented below as gated/debug-only, with the gate and effects proven.

No GameShark/CodeBreaker/Action Replay codes are reported as cheats.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, headless Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`, `mgba -3`. Save states via Shift+F1 (slot 1).
* Keymap (verified against `KEYINPUT` `0x04000130`): A=`x` (`0x3FE`), B=`z` (`0x3FD`), L=`a` (`0x1FF`), R=`s` (`0x2FF`), Up/Down/Left/Right = arrows (`0x3BF`/`0x37F`/`0x3DF`/`0x3EF`), Start=`Return` (`0x3F7`), Select=`BackSpace` (`0x3FB`).
* Boot to title ("Press START"), then press one of the sequences **on the title screen** with ~60–100 ms holds and ~100 ms gaps. Too-fast injection (< 0.05 s hold / 0.07 s gap under the `-d` debugger) drops presses; plain mGBA at full speed with 0.09/0.11 was reliable.
* Published codes:
  * Enable All — `Down, Down, Up, Up, Left, Right, Left, Right, B, A` → "Saving game data..." then `Super Enable All`; writes an 8 KiB EEPROM `.sav` (197 non-zero bytes).
  * Blocky Mode — `Left, Left, Right, Right, Down, Down, A` → `Super Blocky Mode` (title index 3).
  * Nice Try (Konami) — `Up, Up, Down, Down, Left, Right, Left, Right, B, A` → `Super Nice Try` (title index 4), visually confirmed.
* Novel/unpublished code (from ROM, no handler): `Right, Right, Left, Left, Right, Left, A`.
* Rejection test: same Nice Try sequence but final `B, A` swapped to `A, B` → no match.

Screenshots and savestates for every step are in `/tmp/opencode/supermonkey/` (e.g. `p_nice.png`, `nice_long.png`, `p_mirror.png`, `mirror_long.png`, `fd_00.png`, `fd_0a.png`, `fd_17.png`, `w_*.png`). They are working artifacts, not redistributed assets.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x083E9D64` | Button-code table base, 4 slots × 0x2C bytes | Derived (literal refs at `0x08000DBC`, `0x08000E4C`) |
| `0x083E9D64` / `90` / `BC` / `E8` | Slots 1–4: `enable_all` / `mirrormode` / `blockymode` / `_nice__try` | Derived (byte dump) |
| `0x083E9E14` | Name table, 5 × 40 bytes, each letter as `6D 5F 5F xx` | Derived (decoded by hand) |
| `0x08000D40` | Button-index → mask jump table, 13 entries | Derived |
| `0x08000D8A` | Code validator (Thumb) | Derived + live watchpoint hits |
| `0x08000D92`–`DB6` | First-press match loop over the 4 slots | Derived |
| `0x08000DC4`–`E82` | Continuation match, terminator test, dispatch | Derived + watchpoint trace |
| `0x08000DF2` / `E5C` / `E70` | Handlers for code index 1 / 3 / 4; **no case for 2** | Derived |
| `0x08000F28` | Title-name renderer (takes displayed-name index in `r0`) | Derived + live breakpoint (`r0=3` for Blocky, `r0=4` for Nice Try) |
| `0x03000680` | Displayed title index (0 = `MONKEYBALLJR`, 1 = enable_all, 3 = blocky, 4 = nice_try) | Observed (savestate RAM + debugger) |
| `0x030006CC` | Match progress (press count in current sequence) | Observed |
| `0x030006E0` | Matched code index (1-based slot) | Observed |
| `0x08037A68` | Generic input engine; `0x03FF & ~KEYINPUT` into `r5` | Derived |
| `0x030002B8` / `C0` / `C8` | Pressed (edge) / current / previous key arrays, 4 pads × u16 | Derived |
| `0x030004B0` | FE system struct base; `+0x64` → current-screen descriptor | Derived |
| `0x030004B4` | FE screen index (title/menu = `0x01`, select-game = `0x03`, options = `0x10`, debug `0x00`/`0x0A`/`0x17`) | Observed |
| `0x08045120` | Screen setter (value from FE navigation stack) | Derived (4 call sites enumerated) |
| `0x08044DC4` | Navigation-stack pop returning the next screen ID | Derived |
| `0x080450D0` | Screen-ID getter via `[0x030004B0+0x64]+4` | Derived |
| `0x030019D3` | Stage ID for Main Game / Golf (TCRF; literal at `0x080084A4`) | Derived + web recon |

## 5. Algorithm

Validator `0x08000D8A` (all values active-high GBA key masks):

```
BUTTON_INDEX_TO_MASK (jump table @ 0x08000D40, 13 entries):
  0->0x40(Up)  1->0x80(Down)  2->0x20(Left)  3->0x10(Right)
  11->0x02(B)  12->0x01(A)    all others -> no action

on each newly pressed button b -> mask m:
  if progress == 0:
      for slot in 0..3:                      # table @ 0x083E9D64 + slot*0x2C
          if m == u32[slot*0x2C]:
              code_index = slot + 1          # -> 0x030006E0
              progress   = 1                 # -> 0x030006CC
      return 0
  else:
      slot = code_index - 1
      if m != u32[slot*0x2C + progress*4]:
          progress = 0; code_index = 0       # reset, reject
          return 0
      progress += 1
      if u32[slot*0x2C + progress*4] != 0:   # not the terminator
          return 0
      # complete:
      if code_index == 1: unlock_everything(); show_title(1); reset(); return 1
      if code_index == 3: set_blocky_flag();  show_title(3); reset(); return 1
      if code_index == 4:                     show_title(4); reset(); return 1
      # code_index == 2 falls through: returns 0, no action, progress NOT reset
      return 0
```

There is no checksum, no alphabet conversion, no length puzzle: exact u32 comparison against a terminator-terminated word array. The name strings use a font/tile encoding where each character is a 4-byte group `6D 5F 5F 58` ("m__X"); decoding that bank was required before declaring the fourth entry a cheat (guide §11 "not all text is ASCII"). Decoded names: `monkeyball`, `enable_all`, `mirrormode`, `blockymode`, `_nice__try`.

## 6. Tables

| Slot | Code index | ROM address | Press sequence (masks) | Length | Published? | Handler |
|---:|---:|---|---|---:|---|---|
| 0 | 1 | `0x083E9D64` | `80 80 40 40 20 10 20 10 02 01` = D D U U L R L R B A | 10 | Yes (Enable All) | Unlock all + save + title 1 |
| 1 | 2 | `0x083E9D90` | `10 10 20 20 10 20 01` = R R L L R L A | 7 | **No** | **None (dead)** |
| 2 | 3 | `0x083E9DBC` | `20 20 10 10 80 80 01` = L L R R D D A | 7 | Yes (Blocky) | Blocky flag + title 3 |
| 3 | 4 | `0x083E9DE8` | `40 40 80 80 20 10 20 10 02 01` = U U D D L R L R B A | 10 | Yes (Nice Try) | Title 4 |

Mask legend: `01`=A, `02`=B, `10`=Right, `20`=Left, `40`=Up, `80`=Down. The on-screen keypad is not a text entry surface; Select, Start, L and R never appear in any table slot.

## 6b. Enumeration

**Space definition.** The complete in-game code space is the ROM table: **4 fixed sequences**, alphabet of 6 used button masks `{A,B,Up,Down,Left,Right}` drawn from the 10 possible GBA buttons, lengths 7 and 10, terminated by a zero word, one word (32 bits) per press, no checksum and no free field. Slot stride is 0x2C (44 bytes = 11 words); all four slots fit in `0x083E9D64`–`0x083E9E13`. A whole-ROM scan for every other run of ≥4 u32 words drawn from single-bit key masks found **exactly these four sequences** (other hits at `0x081AD594`, `0x082E1DA8`, `0x082E23A4`, `0x083F9F50`, `0x083FD4B0` are graphics/other data, not reachable button tables). Therefore the accepted button-code set is closed at 4 entries: 3 with effects, 1 dead.

**Novel code.** `Right, Right, Left, Left, Right, Left, A` (slot 1, name `mirrormode`) appears on none of TCRF, GameFAQs, IGN, Bananapedia, Sega Retro or Nintendo Fandom. Entered on the real title screen in mGBA; RAM after entry: `title index @0x03000680 = 0x00`, `progress @0x030006CC = 0x07`, `code index @0x030006E0 = 0x02`. A live change-watchpoint trace confirmed the sequence walks the continuation loop to the terminator and reaches `0x08000E80` (success path), with each press advancing progress 1→7. The title stays `SUPER MONKEY BALL JR` (`mirror_long.png`). **Derived** reason: the dispatcher at `0x08000DEE` tests indices 1, 3 and 4 only; index 2 has no case and returns 0. This is a shipped, accepted-but-unfinished developer code, not a typo in a published list.

**Published codes confirmed in-game** (full-speed mGBA, title screen, RAM read from the `gbAs` savestate chunk):

| Input | `0x03000680` | Visible result |
|---|---:|---|
| D D U U L R L R B A | `0x01` | "Saving game data…" → `SUPER ENABLE ALL`; 8 KiB EEPROM written |
| L L R R D D A | `0x03` | `SUPER BLOCKY MODE` |
| U U D D L R L R B A | `0x04` | `SUPER NICE TRY` (`nice_long.png`) |

**Bounds proven by rejection.** With the Nice Try sequence changed only in its last two presses (`… L R A B`), the game left `title index = 0x00`, `progress = 0x00`, `code index = 0x00` — the first press still matched slot 4 but the wrong 10th press reset the matcher. A separate wrong-6th-press variant of the novel code (`R R L L R R A`) also left `title = 0`, `progress = 0`. This proves exact-length, exact-order, no-wildcard matching and that no partial prefix opens anything.

**Debug-menu enumeration (gated, not a controller code).** Three ROM-resident debug screens were opened by forcing the FE screen index at `0x030004B4` to the documented values and re-writing it each frame (a debugger stand-in for the published CodeBreaker activator; **not** an in-game cheat):
* `0x00` — "Super Monkey Ball GBA Mini FE": `Level: 1`, `Mode: Fight`, `Tweak Screen`, `Multiplayer`, `Build Date: Oct 3 2002 17:14:24` (`fd_00.png`).
* `0x0A` — "Tweak Screen": `Pinball bumper force 20`, `(Monkey) 3`, `(Draw Distance) 1`, plus the remaining physics/framerate parameters listed in TCRF (`fd_0a.png`).
* `0x17` — "Advanced Options": `Draw distance: Medium`, `Screen Resolution: Full (240x160)`, `Display framerate: Off`, `Unlock Everything`, `Add 2000 play points` (`fd_17.png`).

*Gated-feature negative, bounded:* the screen ID is set only by `0x08045120` from a navigation-stack pop (`0x08044DC4`); controller walks of title → main → options → select-game never produced `0x00`, `0x0A` or `0x17` (observed values: `0x01`, `0x03`, `0x10`). L+R pressed on title and main menu changed nothing. A full Thumb scan found **zero** `cmp/tst/ands …, #0x300` instructions, i.e. no in-engine L+R test. A single RAM write is overwritten on the next frame. The `L+R` in the published CB recipe is the cheat device's activation condition (guide §16.20), so these menus are developer/debug-only and outside the in-game cheat scope.

**Screens walked with RAM evidence:** title (`screen=0x01`), main menu (`0x01`), Game Options (`0x10`), Select-a-Game (`0x03` in an earlier walk), plus the in-game mini-game screens. No password entry or additional button-code screen exists on any of them.

## 7. Validation evidence

* **Observed** — emulator screenshots and savestate RAM for all three published codes, the novel code, the two rejection tests, L+R on title/main, and all three debug menus. Live watchpoint trace of the validator on the Nice Try and Blocky sequences (press-by-press r4 masks and PC through `0x08000DB4` → `0x08000E80`). Live breakpoint at `0x08000F28` with `r0=3` for Blocky. `KEYINPUT` verified for every mapped key.
* **Derived** — table addresses/stride, validator pseudocode, handler switch (including the missing case 2), screen-index gate and setter/getter, input engine buffers, absence of in-engine L+R test (zero `cmp #0x300`), whole-ROM mask-run scan.
* **Inferred** — that slot 1's missing handler is an unfinished feature rather than an intentional no-op; that the header checksum mismatch is a rebuild artifact (boot path is otherwise stock).

## 8. Unknowns

* Whether slot 1 (`mirrormode`) was intended to mirror the video output or was simply cut; no code references it beyond the matcher.
* Exact contents of the lower Tweak Screen parameters were read from TCRF rather than each scrolled page in the emulator; the three visible rows were confirmed on screen.
* Full list of reachable FE screen IDs was sampled by walking, not exhaustively enumerated from the layfile screen table.
* No attempt was made to complete normal-game progression to unlock mini-games legitimately; the unlock effect was verified via the title code's save write and the documented behaviour.

## 9. Tooling

* `mgba` 0.10.5 (`-3`, `-d` PTY debugger with `watch/c`, `break/t`, `r/4`, `w/4`, `save N`; plain full-speed runs with Shift+F1 savestates).
* Xvfb `:317` + openbox, `xdotool`, `scrot`, `SDL_AUDIODRIVER=dummy`.
* `arm-none-eabi-objdump -M force-thumb/-force-arm`, Capstone + Python scripts (`scan_buttons.py`, `seq_search.py`, `find_input.py`, `decode_codetable.py`, `decode_names.py`, `bl_scan.py`, `scan_lits2.py`, `scan_mask_tables.py`, `final_codes.py`, `plain_test.py`, `force_debug.py`, `walk2.py`) — all in `/tmp/opencode/supermonkey/`.
* Savestate RAM reader `parcess.py`: mGBA `.ss1` is PNG with a zlib `gbAs` chunk (397,312 bytes for this 4 MiB ROM); IWRAM at state offset `0x19000`, so e.g. `0x03000680` → `0x19680` (guide §16.13).

**Legal note:** no ROM image or copyrighted graphics/audio are redistributed; only addresses, algorithms, hashes and original analysis artifacts are reported.

**Cleanup:** all emulators and X servers started for this job were terminated by PID, and generated `.sav`/`.ss1` files were removed from the ROM folder.
