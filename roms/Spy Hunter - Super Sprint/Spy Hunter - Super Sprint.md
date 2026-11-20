# Spy Hunter / Super Sprint (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Spy Hunter - Super Sprint.gba` (4,194,304 B / 0x400000) |
| `file` | Game Boy Advance ROM image: "SPYHUNTCOMP" (B6AE20, Rev.00) |
| Header title | `SPYHUNTCOMP` (0xA0–0xAB) |
| Game code | `B6AE` (0xAC–0xAF) |
| Maker code | `20` (Destination Software / DSI Games, 0xB0–0xB1) |
| Fixed byte | `0x96` @0xB2; version `0x00` @0xBC; complement `0x87` @0xBD; header checksum `0x0000` @0xBE |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, no cracktro/trainer) |
| MD5 | `2b58ab05006a99c7b075a72141c39346` |
| SHA-1 | `b0b7c1bc5bc222eee353fc7889e591d87d33f0a2` |
| SHA-256 | `6e1eec252d093ccb1c94bac0b97296b1d410d3ab1157e9ee9b3630f376ca839c` |

**SKU warning (lesson §16.11).** This is the 2005 DSI Games / Black Lantern Studios
compilation of the two *arcade* games, not Midway's 2002 retail GBA `Spy Hunter`.
The boot screen's own legal text reads "Compilation ©2005 Midway Home
Entertainment Inc. … Distributed under license by Destination Software Inc."

## 2. Executive summary

**Bounded negative: this SKU has no developer-intended code/password system,
no hidden menu and no button-code validator.** Every reachable screen was
walked in mGBA and captured; the shell is driven by an exhaustive 9-entry
function-pointer table (27 Thumb pointers, 12 B/entry) at `0x08024494`. There
are five boot/logo screens, a language screen, a title, a game-select screen,
and exactly two playable game modes (Spy Hunter, Super Sprint), each with its
own HUD/pause overlays. No character-name field, password prompt, cheat menu,
debug overlay, sound test or level select exists in any of them.

All published "cheats" found on the web (BEST/GAME/EVER, EDACRA, G6155,
SUPERSPY, SPYHUNT, BUYMKDA, and the copyright-screen button sequences) belong
to the *other* GBA SKU or to other platforms. Fifty literal searches across five
encodings produced **zero** relevant hits in this ROM (the only `BEST`/`GAME`
hits are the ordinary English words "BEST LAP" and "GAME OVER" in the arcade
text bank). Eight keyword searches (`debug`, `password`, `cheat`, `secret`,
`test menu`, `sound test`, `level select`, `code`) produced **zero** hits.

The input layer has only immediate edge/held tests (9 BLs to the key-read
routine, 34 to `key_pressed`, 8 to `get_held`); there is no press-history ring,
mask sequence table, checksum, alphabet or validator. A novel 10-press sequence
was entered with RAM verification and produced no state change (§6b).

## 3. How to reproduce

* mGBA 0.10.5, `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, `-3` scaling, Xvfb
  `:316` + openbox. Keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrow keys. Hold 70–150 ms.
* Boot path (≈10 s): legal notice → Midway logo ×2 → DSI Games → Black
  Lantern Studios → "PLEASE SELECT LANGUAGE" (5 flags; A confirms, D-pad
  moves highlight) → title "PRESS START".
* Title: `Start` → "SELECT GAME". `Left`/`Right` highlights a car; `A` starts
  that game; `B` returns to title. Default is Spy Hunter (highlight the red
  car with `Right` for Super Sprint).
* Spy Hunter: `Start` on the "GET READY" splash begins play; `Start` during play
  opens a `PAUSE / RESUME / QUIT` overlay; `B` quits to title.
* Super Sprint: `Start` on the splash → "PREPARE TO RACE / CHOOSE A TRACK"
  (9 track thumbnails, `EASY` difficulty); `A` starts the race.
* RAM ground truth was read from uncompressed mGBA `gbAs` savestate chunks
  (zlib, 397,312 B). IWRAM begins at state offset `0x19000`. Useful words:
  `0x03004A90` = screen index (5 title, 6 select, 7 Spy Hunter, 8 Super
  Sprint), `0x03004A94` = screen substate, `0x03003058` = `~KEYINPUT`,
  `0x03003060` = current virtual-key edge bits (0x1 Right, 0x2 Left, 0x4 Up,
  0x8 Down).

## 4. Address map

| Address (ROM) | Meaning |
|---|---|
| `0x08000000`–`0x08000300` | crt0 / entry, `main` at `0x0800218` (Thumb) |
| `0x080017AC` | only reader of `0x04000130` (KEYINPUT), returns active-low halfword |
| `0x08002000` | global input poll: stores `~KEYINPUT` to `0x03003058`, calls 0x1DE8/0x1EC8/0x1E68/0x1F64 |
| `0x08002088` | `key_pressed(index, mask)` — reads virtual-key mask table at `0x03003064` |
| `0x080020A8` | `get_held(mask)` — tests word at `0x0300305C` |
| `0x08002E2C` | `goto_screen(index, arg)` — writes `0x0300308C`, `0x030030A0`, `0x03003160` |
| `0x08002E58` | screen dispatcher/markup driver |
| **`0x08024494`** | **9 screen triplets `{init, update, draw}` × 12 B = 27 Thumb pointers** |
| `0x08024434`–`0x08024458` | virtual-key mask table (`0x0200/0x0100` = R/L, `0x0040/0x0080` = U/D, etc.) |
| `0x08041600`–`0x080421FB` | only ASCII text bank: 231 NUL/space-separated localised arcade UI strings |
| `0x08021DBEC` / `0x08021DC28` | newlib `vfprintf` leftovers (`0123456789ABCDEF`, `(null)`) — toolchain, not game data |

Screen triplets (index → first pointer):
0 `080031B5`, 1 `08003269`, 2 `08003331`, 3 `08002EE9`, 4 `08003109`,
5 `08003FED`, 6 `080035D9`, 7 `08003441`, 8 `08003529`.
The 12 `goto_screen` call sites use only immediates `0,1,2,3,5,6,7,8`;
index 4 was verified by a **patched throwaway copy** (two bytes changed at
file offsets `0x2F6A` and `0x3010` from `0x2005` to `0x2004`) and is the
language-select screen — reachable on a fresh save, not dead code.

## 5. Algorithm

There is no encoder/decoder. The relevant logic is a plain screen state machine:

```
poll_keys():  held = ~KEYINPUT & 0xFFFF; derive edge bits; update virtual masks
dispatch():   triplet = screen_table[current_screen]; triplet.update(); triplet.draw()
goto_screen(n, arg): previous = current; current = n; pending = 1
```

Input checks are single-edge tests, e.g. screen 4 at `0x08002FB1`:
bit1 → confirm/back, bit2 → decrement, bit8 → increment; screen 6 at
`0x08003389`: `key_pressed(0,10)` → `goto_screen(3,0)`. `0x08002F3D` (title)
tests `key_pressed(0,10)` → screen 5 and `key_pressed(3,10)` with a 179-frame
timer. No accumulated sequence, no comparison against a literal string, no
checksum, no flags written by input.

## 6. Tables

* Screen table: 9 entries × 3 Thumb pointers, `0x08024494`–`0x080244FF`.
* Virtual-key masks: `0x08024434` onward; raw `~KEYINPUT` global `0x03003058`.
* ASCII text bank (231 strings): `0x08041600`–`0x080421FB`. Representative
  entries: `PRESS START TO CONTINUE RACING`, `TRACK %d`, `BEST LAP`,
  `CHOOSE AN ITEM FOR YOUR CAR`, `HIGHER TOP SPEED`, in EN/FR/IT/DE/ES.
  **No password, code, cheat, debug or secret string.**
* Published codes for the *other* SKU/platform (all absent from this ROM):
  `BEST`,`GAME`,`EVER`; `EDACRA`; `G6155`; `SUPERSPY`; `SPYHUNT`; `BUYMKDA`;
  copyright-screen sequences `Up,Up,Down,L,R,L` and `Left,Left,Right,Left,R,R`.

## 6b. Enumeration

**Space definition.** There is no code space to enumerate: no alphabet, no
input length, no checksum width and no lookup table of accepted values. The
finite state space that could hide a feature is the shell screen table:
**9 screens** (5 boot/logo/language + title + select + 2 game modes) and
**2 in-game overlays** (Spy Hunter pause, Super Sprint "GET READY"/HUD).
Every one of the 9 screen pointers was either walked normally or forced with
a patched copy and screenshotted; the resulting states are in `sheet_forcedb`
/ `sheet_states` in the work directory.

**Novel sequence, entered and RAM-verified.** A 10-press combination appearing
in no published list was entered on the title screen:
`Up, Up, Down, Down, Left, Right, Left, Right, B, A`.
Before: screen index `0x5`, substate `0x3`, key-edge word `0x0`.
After: screen index `0x5`, substate `0x3`, key-edge word `0x1` (the final
`Right` edge) — **no screen change, no new flag, no hidden menu**.
Screenshot `novel_title_game.png`.

**Rejection bounds / counts.**
* 10 published code strings × 5 encodings (ASCII, lowercase, ±0x20, UTF-16LE)
  = **50 literal searches**, 0 relevant hits.
* 8 debug/cheat keyword searches (case-insensitive over 4 MiB), 0 hits.
* Standard alphabet runs (`A-Z`, `a-z`, `0-9A-Z`) absent; the only
  `0123456789ABCDEF` is newlib's printf table at `0x08021DC28`.
* 16 button tests (all 10 single keys plus LRS, A+B+Start+Select, L+R+A+B,
  Start+Select, and the two retail button sequences) were applied to each of
  8 saved game screens = **128 trials**; 12 further tests on the title and 6
  on the legal screen. No trial produced a screen index or substate outside
  the documented transitions.
* Input surface count: 9 BL to `0x08002000`, 34 to `0x08002088`, 8 to
  `0x080020A8`, 12 `goto_screen` calls. Every screen handler was disassembled
  (`input_handlers.txt`); none contains a mask array, history index or
  comparison literal beyond single-button branches and frame timers.
* A refined scan for ≥8 consecutive non-zero u16 values drawn from the GBA
  key-mask set found only repetitive entity/joypad-config structures; no
  long button sequence table exists in the 4 MiB image.

Therefore the absence of a code system is a statement about the complete
9-screen/2-overlay state space and the complete input-call-graph, not merely
"strings were not found".

## 7. Validation evidence

* **Observed** — mGBA screenshots of every screen (`sheet_states`,
  `sheet_freshsteps`, `sheet_forcedb`, `novel_title_game.png`); savestate RAM
  reads of `0x03004A90`/`0x03004A94`; 128+ button trials with no undocumented
  transition; patched-ROM proof that screen 4 is the language selector.
* **Derived** — screen table and dispatcher from raw Thumb disassembly
  (`objdump -M force-thumb`), BL-target scans, literal-pool reads confirmed
  with `struct.unpack_from`; input call counts from Capstone scan.
* **Inferred** — the legal screen's tile-encoded text was not letter-by-letter
  decoded; its content is quoted from the screenshot. This does not affect the
  negative because the boot sequence was walked frame-by-frame and the screen
  was exercised with the published and undocumented button sequences.

## 8. Unknowns

* The exact glyph mapping of the tile-encoded legal/language text banks was
  not reconstructed (only the ASCII bank at `0x08041600` was decoded).
* Whether any *retail* GBA `Spy Hunter` code works on a different SKU was not
  tested; irrelevant to this ROM.
* The 5th screen pointer triplet (language) was reached via a patched copy;
  on a fresh save it also appears naturally, so no unreachable content is
  being claimed either way.

## 9. Tooling

`arm-none-eabi-objdump -M force-thumb`, Capstone, Python 3 (`struct`, `zlib`,
`PIL`), mGBA 0.10.5 `-3`/`-g`/`-d`, Xvfb `:316` + openbox, xdotool, scrot,
ImageMagick. Helper scripts: `k2.py`, `probe.py` (savestate `gbAs` extraction
and RAM word reads). No ROM or copyrighted asset is redistributed; the
patched copy existed only in `/tmp/opencode/spyhunter` and was deleted.
