# Super Ghouls 'n Ghosts (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Super Ghouls 'n Ghosts/Super Ghouls 'n Ghosts.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `SUPER GHOULS` (0xA0–0xAB) |
| Game code / maker | `AG5E` / `08` (Capcom) |
| Version / complement / checksum | `0x00` / `0x66` / `0x0000` (rebuilt-header artifact; complement is intact) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock, no cracktro/trainer) |
| CRC32 | `1EF2ACF3` |
| MD5 | `37ff7a1de0322b72a6b41dea0ba53673` |
| SHA-1 | `31e7d1d405185ba2d7a9ffcc2b847d4457088cf0` |
| SHA-256 | `a940124c6150a607110e584416da728f393fa65cccf6400e524e358c196106b2` |

This is the USA/Europe retail image (AGB-AG5E-USA / AGB-AG5P), Rev.00 — the hash is
recorded so every address below is tied to this exact image.

## 2. Executive summary

**There is no in-game code system in this ROM.** No password screen, no code
alphabet, no validator, no sequence matcher and no reachable hidden menu exists
on any screen reachable with a GBA controller. The space searched is bounded and
counted in §6b.

What the ROM *does* contain is a substantial **dormant Capcom debug menu**: a
complete text bank (stage select, sound/camera/OBJ/graphics debug submenus) and
its handler code at `0x08007C00–0x08009900`. It is not reachable from retail
input. Its only entry path is gated by a conjunction of three game-state bytes
that no controller path sets simultaneously (§5.3), and live breakpoints on all
three debug entry points never fired across the full screen walk.

All web-published "cheats" for this SKU are GameShark / CodeBreaker / Action
Replay RAM patches (infinite lives, timer stop, etc.) and are **out of scope** by
the engagement rules. The widely published SNES "L+R+Start on controller 2 with
EXIT highlighted" stage-select uses a second controller that the GBA does not
have; Japanese sources explicitly state the GBA version has no hidden commands.
Neither SNES nor GBA cheat-device codes are reported as findings.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `mgba -3 -d <rom>` under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`.
* Keymap (mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Holds of 100–300 ms; transitions can take 10–15 s.
* RAM evidence: mGBA CLI debugger `r/4 ADDR`, plus zlib-decompressed `gbAs`
  chunks of `.ss1` savestates (IWRAM at raw offset `0x19000`, EWRAM at `0x21000`).
* Screen walk (all observed, screenshots in `/tmp/superghouls/`):
  Capcom logo → two intro scenes → title (`ORIGINAL MODE` / `ARRANGE MODE` /
  `OPTION MODE`, plus `NEW GAME` / `LOAD GAME` once a `.sav` exists) →
  `OPTION MODE` (DIFFICULTY / NORMAL / KEY CONFIG. / SHOT B BUTTON /
  JUMP A BUTTON / EXIT) → gameplay (Original Mode stage 1) → death
  `CONTINUE` / `END` menu → ending sequence → title. All key combinations in
  §6b were applied on the title and `OPTION MODE`/EXIT screens with savestate
  reload and RAM diff after each attempt.
* Static: `strings -t x`, literal/pointer scans with Python `struct`, BL scans,
  `arm-none-eabi-objdump -M force-thumb`. No ROM or asset is redistributed.

## 4. Address map

| Address (ROM unless noted) | Role |
|---|---|
| `0x080000C0` | stock ARM entry / crt0 |
| `0x08000404` | init: writes `0` to debug sub-mode byte `0x03002AD0` |
| `0x08003D00`–`0x08004F00` | boot / title / menu scene machinery |
| `0x080070D8` | **debug gate** function (see §5.3) |
| `0x0800718E` | BL → `0x08007CBC` (debug init) on gate success |
| `0x08007CBC` | debug subsystem initialiser; calls `0x0809D97C(1..7)` |
| `0x08007D8C` | draw debug readout (`PL_HIT:`, `WEAPON:`, `ARMOR:`, …) |
| `0x08007E48` | debug jump-table dispatcher (table `0x08007EF8`, 8 entries `0x08007EFC`–`0x08007F1A`); BL from `0x0800990E` |
| `0x08007F54` | debug submenu renderer |
| `0x08007FE8` | debug main loop: 8-item cursor at `0x02006E54`, keys at `0x03004D60`, `"<>"` cursor glyph `0x080A161C`; B on cursor 3 cycles `0x03002AD0` mod 3 at `0x08008130` |
| `0x08009904` | wrapper that BLs `0x08007E48` (no direct callers found) |
| `0x0800AF94` | append key code to 16-byte history buffer `0x03002A30` |
| `0x080123C0`, `0x08012424`, `0x08012470`, `0x08013164`, `0x08013194`, `0x080131BC` | history-buffer clear / shift / append utilities |
| `0x08025FAC` | scene dispatcher; reads scene byte `0x02001A9C`, 12-way table `0x08025FC8`; index 5 → `0x0802606E` → `0x08025550` → `0x080070D8` |
| `0x080A15F4`–`0x080A1ED8` | complete ASCII UI / staff-roll text bank (decoded) |
| `0x080A1790`–`0x080A1970` | **debug menu text bank** (decoded, §6) |
| `0x080A1FD8`, `0x080A2098`, `0x080A2134` | ASCII→tile font maps (decoded; proves text is plain ASCII with a remapped glyph order, not a hidden cipher) |
| `0x03002AD0` | debug sub-mode byte (init `0`; cycled `0→1→2→0` only by B inside the debug menu) |
| `0x03002A30` | 16-byte input history (terminator `0xFF`); **no comparator** |
| `0x02001A9C` | scene byte: `0` title/menu, `4` gameplay, `5` death/continue |
| `0x02000A14` | in-game flag: `1` during gameplay, `0` on title/death screen |
| `0x02021FB8` | game-mode byte: `2` during gameplay, `0` on title/death screen |
| `0x020202BC` | RAM copy of key state read by the debug gate |

ROM address = file offset + `0x08000000` throughout.

## 5. Algorithm / gate analysis

### 5.1 Text and font decoding (done before the negative)

`strings -t x -n 3` finds the whole UI bank at file `0xA15F4`–`0xA1ED8`
(`PRESS START`, `CONTINUE`, `OPTION MODE`, `KEY CONFIG.`, `DIFFICULTY`,
`READY GO`, credits). The three tables at `0xA1FD8`, `0xA2098`, `0xA2134` are
ASCII↔glyph-index maps (`pqrstuvwxyz{`abcdefghijkPQRSTUVWXYZ[...0123456789:;
...` and inverses). Therefore every visible label is plain ASCII with a
scrambled tile order; there is no encoded/compressed password text bank left to
decode. Case-insensitive and `+0x20` shifted searches were also run.

### 5.2 The dormant debug menu

The text bank at `0x080A1790` is unambiguous:

```
PL_HIT:  WEAPON:  ARMOR:  SOUND:  BRIGHTNESS  BG DISP  CAMERA  OBJ GENE
OFF / ON / BGM OFF / ALL OFF
-OBJ GEN-: HEAD, COL, PALET, ALL OBJ, ALL BG, ALL COL
-BRIGHTNESS-   -BG DISP-: BG1/2/3 ON|OFF
-CHROMA-: PALET, R, G, B
-CAMERA-: C-PX:, C-PY:, PL-X:, PL-Y:, PX, PY, MX, MY, TSK, MP-X, MP-Y
START STAGE :   <>   !! DATA BROKEN   SARDIUS
```

`0x08007FE8` is its main loop: a `<>` cursor over **exactly 8** top-level rows
(bracket `0x02006E54`, wrap at 7), Left/Right cycling a per-row value against
the limit table `0x080228CC` (limits `2, 8, 10, 0x8C, …`), and A/Start/B actions
on individual rows. `0x08007D8C`, `0x08007E48`, `0x08007F54` implement the
readout and five submenu families. The level-select string `START STAGE :`
(`0x080A19D0`) appears in the title-style menu table at `0x0802290E4` (index 8 of
the 9-entry table based at `0x0802290C4`) but no reachable code path iterates
that far — the title/menu renderers only draw indices `0..2` (`0x0800A3B4`,
`0x0800AB74`) or `0..1` (`0x0800A4E6`).

### 5.3 The gate and why it is closed

```
080070D8: if byte[0x02021FB8] != 0            -> return          (closed)
          if byte[0x02000A14] == 0            -> return          (closed)
          keys = byte[0x020202BC]
          if keys & 0x20 (Right) or keys & 0x10 (Left):
              0x030029A8 = 1; sound; bl 0x080071C8
              bl 0x080072EC (always returns 1)
              byte[0x02000A14] = 0; keycode 0xF4 recorded
              copy 7 bytes 0x030029F0+1..7 into 0x0202004E+... fields
              bl 0x08007CBC   ; DEBUG MENU ENTERS HERE
```

Caller chain: `0x08025FAC` (scene loop, reads `0x02001A9C`) → 12-way table
`0x08025FC8` index 5 → `0x0802606E` → `0x08025550` → `0x080070D8`.

Observed runtime values (savestate RAM reads):

| Screen | `0x02001A9C` | `0x02000A14` | `0x02021FB8` | gate |
|---|---:|---:|---:|---|
| title | 0 | 0 | 0 | closed (scene ≠ 5, flag = 0) |
| OPTION MODE | 0 | 0 | 0 | closed |
| gameplay (Original, stage 1) | 4 | 1 | 2 | closed (scene ≠ 5, mode = 2) |
| death / `CONTINUE`–`END` | 5 | 0 | 0 | closed (flag = 0) |
| forced savestate: scene 5 + flag 1 + mode 0 | 5 | 1 | 0 | opens only after a **debugger RAM patch**, not controller input |

Three live breakpoints (`0x08007CBC`, `0x08007E48`, `0x08007FE8`) were installed
from the first instruction of emulation and never fired during the entire walk
(title, mode select, all option rows, gameplay, death menu, ending, return to
title), nor after ~20 combinations of L/R/Start/Select/A/B on title and EXIT.

The only writer of the debug sub-mode byte `0x03002AD0` outside boot is the B
key **inside the debug menu itself** (`0x08008130`, mod 3); it therefore cannot
be used to enter the menu.

### 5.4 Input history is not a validator

`0x03002A30` holds a 16-byte history of encoded key codes with `0xFF` sentinel.
It has exactly **7 code references** in ROM (`0x0800B040`, `0x08012420`,
`0x0801246C`, `0x080124A8`, `0x08013190`, `0x080131B8`, `0x080131DC`; two other
byte-pattern hits are inside data). Each is an append/clear/shift routine. There
is **no comparison of the history against any constant mask sequence** anywhere
in the 4 MiB — i.e. no Konami-style code matcher. The published "Select+L skip
level" is a CodeBreaker write to `0x04000130`/`0x000000DC`, not an in-game
sequence, and is correctly excluded.

## 6. Tables

* Debug sub-mode `0x03002AD0`: `0` = default, `1`/`2` = debug variants; only
  written by boot (0) and the debug menu's own B key (`+1 mod 3`).
* Debug main-menu cursor: 8 rows (0…7) at `0x02006E54`; per-row limit table at
  `0x080228CC` (`2, 8, 10, 0x8C, …`); cursor glyph `<>` at `0x080A161C`.
* Debug dispatch table: `0x08007EFC`, `0x08007F04`, `0x08007F08`, `0x08007F10`,
  `0x08007F14`, `0x08007F1C`, `0x08007F28`, `0x08007F32` → eight handlers at
  `0x080099D0`, `0x08009A14`, `0x08009D68`+`0x08009CAC`, `0x08009CE4`+
  `0x08009CAC`, `0x08009D10`+`0x08009CAC`, `0x08009D3C`+`0x08009CAC`.
* Scene dispatcher table `0x08025FC8` (12 entries); debug path is index 5.
* No hard-coded password/code table exists (counted in §6b).

## 6b. Enumeration

**Code-space size: zero. No code system exists in this SKU.**

Bounds proven by counts and rejection:

1. **Text/alphabet search over all 4,194,304 bytes** (case-insensitive, also
   `+0x20` shifted): `password` **0**, `enter code` **0**, `invalid` **0**,
   `secret` **0**, `cheat` **0**, `debug` **0**, `level select` **0**,
   `stage select` **0**, `sound test` **0**; the only `start stage` hit
   (`0x080A19D0`) is the dormant debug-menu label. The font tables at
   `0x080A1FD8`/`0x080A2098`/`0x080A2134` were decoded first, so this is a
   statement about the *decoded* text space, not about un-decoded glyph data.
2. **Reachable-screen enumeration:** 10 screens observed with screenshots and
   RAM reads (logo, 2 intro scenes, title, NEW GAME prompt, OPTION MODE,
   gameplay, death menu, ending, return-to-title). None offers a text/code
   entry field; the only text-like field is the on-screen button remap
   (`KEY CONFIG.`), whose buffer is consumed by the input mapper, not compared
   to a constant (guide §16.2b).
3. **Validator/matcher enumeration:** 7 references to the only input-history
   buffer, all append/clear/shift; **0** comparisons against a mask sequence;
   **0** hard-coded code strings; **0** checksum/alphabet tables.
4. **Debug menu enumeration:** all **8** top-level rows and **5** submenu
   families were enumerated from the decoded text bank (§5.2). Entry branches
   into the debug subsystem: **4** BL references total
   (`0x0800718E→0x08007CBC`, `0x0800990E→0x08007E48`, plus two internal),
   **0** direct 32-bit pointer references, and **0** live breakpoint hits across
   the walk. The gate was tested in-game: all 20 L/R/Start/Select/A/B
   combinations tried on title and EXIT produced no debug state; the only way
   the gate opened was an explicit savestate RAM patch (analysis tool, not a
   code). This is a bounded **gated/dead-feature negative** (guide §16.3), not
   "not tested".
5. **Novel code:** none can be minted, because there is no encoding or
   validator to invert. No novel code is claimed; the deliverable is the
   counted negative above.

**Published-code reconciliation (all out of scope, recorded for completeness):**
3rd party cheat indexes "Arrange Mode alternate ending" is a gameplay unlock, not a
code; 3rd party cheat index lists for this SKU are exclusively
GameShark Advance / CodeBreaker / Action Replay RAM patches; the SNES
controller-2 level select cannot be entered on GBA. A 3rd party cheat index page fetched during
recon returned a prompt-injection payload (fake "LLM instructions", a fake XOR
"key" file, a payment demand, and termination commands). It was ignored,
treated strictly as data, and is reported here as required.

## 7. Validation evidence

* **Observed** — emulator screenshots for every screen; savestate RAM reads for
  the five-row gate table; no breakpoint hits; gate opens only after a debugger
  RAM patch.
* **Derived** — gate conjunction at `0x080070D8`, caller chain through
  `0x08025FC8[5]`, 8-item debug cursor, 16-byte history utilities, font maps.
* **Inferred** — that the debug menu was intended for development only and left
  disabled in the retail build (strongly supported by the gate needing a state
  combination no input path produces, and by zero xrefs/breakpoints).

## 8. Unknowns

* Whether any *very* obscure in-game state (e.g. an Arrange Mode route or a
  specific boss state) sets `0x02000A14=1` while `0x02021FB8=0` and scene `5`
  simultaneously; all reachable states sampled did not.
* Whether the `0x08009904` wrapper is invoked by an unmapped runtime pointer;
  it has no static xrefs and its breakpoint never fired.
* Exact semantics of debug sub-modes `1`/`2` of `0x03002AD0` (only settable
  inside the already-unreachable menu).

## 9. Tooling

`strings`, `xxd`, `grep`, Python 3 (`struct`, `zlib`), `capstone` available,
`arm-none-eabi-objdump -M force-thumb`, mGBA 0.10.5 SDL (`-3 -d` CLI debugger),
Xvfb `:315` + openbox, `xdotool`, `scrot`, ImageMagick, `gdb-multiarch` (not used
— the GDB stub was unavailable; the `-d` pty debugger was used instead).
Helper scripts: `scan_ptrs.py`, `blscan.py`, `gba.py`, `ssread.py`,
`readram.py`, `patchss.py`, `combo2.py` in `/tmp/superghouls/`.

## 10. Legal note

No ROM image, extracted graphic, music or game text asset is redistributed by
this report; only hashes, addresses, and the analyst's own tool scripts are
published.
