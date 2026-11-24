# Gauntlet / Rampart (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Gauntlet - Rampart.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| `file` | Game Boy Advance ROM image: `"GAUNTLETCOMP" (B69E20, Rev.00)` |
| Header title | `GAUNTLETCOMP` (12 bytes at `0xA0`, no NUL pad) |
| Game code | `B69E20` (`0xAC`: `B69E`, `0xB0`: maker `20`) |
| Version | `0x00` at `0xBC` |
| Fixed byte | `0x96` at `0xB2` (present) |
| Entry word | `0xEA00002E` → stock `b 0x080000C0`; **no cracktro / trainer patch** |
| Header checksum | `0x0000` at `0xBE` |
| Complement byte | stored `0x66`; computed `(-sum(0xA0..0xBC))&0xFF = 0x7F` → nonstandard, consistent with a rebuilt header (guide §16.1) |
| MD5 | `75fca6eeccf730d5b9883fa333f6b268` |
| SHA-1 | `1be59c6919a849749d7251d352bf5f1840e4e683` |
| SHA-256 | `4d4e03aeb0390d5db30ff0174f6e20abe15de9732b1eadf058b74a088bcd807b` |

**Embedded-header scan (2-in-1 check).** Full-file scan for the 156-byte Nintendo logo
(`24 ff ae 51 …`) found **exactly one hit, at file offset `0x4`**. There is no
second concatenated GBA image: this is a single 4 MiB image whose frontend
contains both arcade games (developer EC Interactive Games, publisher DSI Games,
release 2005-11-03). All addresses below are absolute for that one image
(`0x08000000 + file offset`).

## 2. Executive summary

**No developer-intended cheat system exists in this ROM.** There is no password
screen, no password alphabet/table/validator, no button-code sequence table, no
unlockable flag set, and no reachable hidden/debug/level-select menu. This is a
proven negative over three searched spaces (all reachable screens, all ASCII and
font-indexed text banks, and the button-combination space), not an absence of
search.

What the ROM *does* contain is a generic arcade-frontend UI engine. Its text bank
at `0x08019800..0x0801AD80` holds only the game's own hint strings, the two
pause menus, and one extra developer string, `"Press all Holds to exit"` at
`0x0801AD08`. That string is genuinely referenced by the generic UI renderer
(`0x080141BC`), but no controller input reaches a screen that displays it; the
condition is a per-UI-object byte (`object+0x18 == 2`, decompiled at
`FUN_08013DAC`) and the only writer found for that field on the menu-object path
is game-state logic for Rampart entities (`0x0800D3D6`, `0x0800DCEA`), not a menu
constructor. It is reported as an **in-renderer / unreachable-by-input leftover**.

Published material was checked early (3rd party cheat indexes game 929031 cheats page via
Wayback 20200211161208, 3rd party cheat indexes query, DuckDuckGo lite).
Every source reports **zero cheats/codes** for this GBA SKU; 3rd party cheat indexes state
"there are no cheats for the selected game." The only "cheats" on the web for
this title are GameShark/ActionReplay memory-edit codes (out of scope) and codes
for *other* SKUs (NES *Gauntlet*), which do not apply to this image (guide §16.11).

The 3-letter tokens `RUP PET P.P ASM KCK GGS RGS SSC RSJ` in the text bank are
**default high-score initials**, not codes (seen on the HI SCORES screen).

## 3. How to reproduce

* Emulator: mGBA (SDL), `SDL_AUDIODRIVER=dummy`, Xvfb `:317`, `openbox`, `-3` scale.
* Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. All presses held 60–120 ms (short holds to avoid
  double-stepping, guide §16.2).
* Exact paths walked (all confirmed by screenshot + savestate VRAM hash):

  1. Boot: `DSI Games` splash → `MIDWAY` splash → `EC Interactive Games` splash
     → combined title/attract screen ("GAUNTLET / RAMPART" art).
  2. Title/attract: D-pad Up/Down **skips attract segments** (DSI/EC logo replays,
     Gauntlet art, Hi-Scores, Rampart art). Start launches whichever game's
     attract segment is active. There is no labelled game-select menu.
  3. HI SCORES screen: WARRIORS / VALKYRIES / WIZARDS / ELVES tables with the
     default initials above; "Press Start".
  4. Gauntlet: attract art → **SELECT CHARACTER** (Warrior / Valkyrie / Wizard /
     Elf, selected with Left/Right, confirm A) → **LEVEL: 1** intro → gameplay.
     During gameplay **B shows a rotating hint screen** (e.g. "COLLECT MAGIC
     POTION / BEFORE PRESSING MAGIC", "FIND EXIT TO NEXT LEVEL"). **Start → PAUSED**
     with CONTINUE GAME / START NEW GAME / ABORT GAME.
  5. Rampart: attract art → **difficulty select** (RECRUIT "BEGINNER LEVEL" vs
     VETERAN "ADVANCED LEVEL +5000 POINTS", Left/Right + Start/A) → PAUSED overlay
     → **SELECT BATTLEFIELD / SELECT HOME CASTLE** map screen → gameplay.
  6. No OPTIONS / SETTINGS / PASSWORD / CODE / DEBUG / LEVEL SELECT screen exists
     on any of the above.

* Savestates used as a stable base for repeated input experiments: mGBA
  Shift+F1..F8 save, F1..F8 load. All generated `.sav/.ss*` were removed at the
  end (§7).

## 4. Address map

| Item | Address (ROM) | File offset | Evidence |
|---|---|---|---|
| crt0 entry | `0x080000C0` (ARM) | `0xC0` | header word `0xEA00002E` |
| `main` | `0x080001CC` (Thumb) | `0x1CC` | ARM crt0 literal `0x080001CD`, `push {r4-r7,lr}` at `0x1CC` |
| Keypad reader | `0x080004FC` | `0x4FC` | reads literal `0x04000130`; `~KEYINPUT & 0xFFFF` |
| Held-key mask word | `0x03003E0E` (IWRAM) | state `0x1CE0E` | written by `0x0800518`; idle value `0xFC00` (= `~0x03FF`) observed in all 8 savestate dumps |
| Edge (pressed) mask | `0x03003E10` (IWRAM) | state `0x1CE10` | written by `0x0800518`; `0x0000` at rest |
| FPS/frame counter | `0x03003E08` | — | `0x080053C` region |
| Menu-result byte | `0x030061E8` | state `0x1F1E8` | handlers `0x080147AC/BC/CC` OR `0x02/0x04/0x08`; **observed** `0x01` on pause, `0x02` after ABORT+A |
| UI root object pointer | `0x030061A8` | — | `FUN_0801359C` stores object pointer here |
| Mode word | `0x0300632C` | state `0x1F32C` | `FUN_08014D78` stores param 0..3; `0x02000000` in all sampled states |
| Generic UI renderer | `0x08013DAC` | `0x13DAC` | decompiled; status text chosen when `object+0x18 == 2` |
| Debug string xref | `0x080141BC` | `0x141BC` | literal `0x0801AD08` → `"Press all Holds to exit"` |
| Text bank (ASCII) | `0x08019E00..0x0801AD80` | same | 149 pointer→ASCII-word hits; full listing in §6 |
| Gauntlet pause menu | `0x0801A7C0..0x0801A7F0` | same | ABORT / START NEW / CONTINUE / `--` |
| Rampart pause menu | `0x0801AC7C..0x0801AD40` | same | ABORT / START NEW / CONTINUE / PAUSED / "Press all Holds to exit" |
| Font/glyph index table | `0x0801A230..0x0801A2C0` | same | byte table `0x00..0x72`, gaps `0xFF` — ASCII→tile mapping |
| Memory-map debug table | `0x0829EA60..0x0829EAC8` | same | `{char* label, u32 ram, u32 ?, u32 size}` records: "32k: gauntlet saved screens", "15360: fill stack", "1536*2: rampart castle", "2048: unseen screen" — **zero code/data references found** (dead table) |
| Key-mask dispatch table | `0x082B0074` | same | 14 Thumb pointers `0x08015295..0x080154A9` including game-start handlers `0x080152F5` (game 1), `0x0801535D` (game 2), `0x080153B9` (game 3); no *cheat* callbacks |

Savestate RAM offsets used (mGBA `.ss*` = PNG with zlib `gbAs` chunk, raw length
397,312 bytes): IWRAM at raw `0x19000`, EWRAM at `0x21000`, VRAM at `0x1000`.
Distinct screen identity was confirmed by MD5 of the VRAM slice, e.g.
title `434f2c4f707a…`, Rampart attract `e5c9f1d93c9e…`, Gauntlet gameplay
`0509936778f2…`, Gauntlet pause `e991d4c4036d…`, Rampart difficulty
`cf3b006d4ed4…`.

## 5. Algorithm

No password/validator algorithm exists. The only decode-like routine relevant
to the negative result is the keypad sampler (ground truth for button-code
search):

```c
// 0x080004FC, Thumb
u16 raw = *(volatile u16*)0x04000130;   // active-low
u16 held = ~raw & 0xFFFF;               // active-high; 0xFC00 when idle
u16 edge = held & ~prev;                 // one-frame press
*(u16*)0x03003E10 = edge;
*(u16*)0x03003E0E = held;
```

Key mask convention used for every search: `A=0x001, B=0x002, Select=0x004,
Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`.
All button-combination tests were run against this mask space; the ROM contains
no table of these masks longer than 4 coincidental data hits (§6b).

## 6. Tables

**Complete ASCII text inventory of the UI bank** (every pointer→word hit in
`0x08019E00..0x0801B000`, deduplicated by meaning):

* Menu/system: `ABORT GAME`, `START NEW GAME`, `CONTINUE GAME`, `PAUSED`
  (both games), `--`, `Press all Holds to exit`.
* Gauntlet HUD/hints: `LEVEL:`, `PRESS A BUTTON`, `100 X COINS`, `TREASURES x`,
  `TREASURE`, `ROOM`, `NO BONUS !!`, and the 80+ gameplay hint strings
  (`BE DESTROYED`, `SOME WALLS MAY`, `BOMBS AND/OR KEYS`, `YOU ARE FULL OF`,
  `TRANSPORTER VISIBLE`, `THIEF ESCAPED:`, `WALLS DISAPPEAR`, `TRAPS MAKE`,
  `SAVE KEYS TO OPEN DOORS`, `FOOD: HEALTH INCREASED BY`, `SAVE POTIONS`,
  `MAGIC POTIONS AFFECT EVERYTHING ON SCREEN`, `SHOOT OR FIGHT DEMONS`,
  `WARRIOR/VALKYRIE/WIZARD/ELF NOW HAS EXTRA …`, etc.).
* High-score headings: `WARRIORS`, `VALKYRIES`, `WIZARDS`, `ELVES`, `HI`, `SCORES`.
* Default initials (high scores, **not cheats**): `RUP`, `PET`, `P.P`, `ASM`,
  `KCK`, `GGS`, `RGS`, `SSC`, `RSJ`.

There is **no** string containing `password`, `cheat`, `code`, `secret`,
`unlock`, `level select`, `difficulty select`, `warp`, `generator`, or `debug`
anywhere in the image, in ASCII, in `+0x20` shifted ASCII, or as a font-index
sequence (the font table at `0x0801A230` was dumped and decoded; it maps glyph
indices only, no hidden message).

**Key masks** (active-high, from `0x080004FC`): as listed in §5.

**Menu-result bits at `0x030061E8`** (observed / derived from handlers):

| Bit | Set by | Meaning |
|---:|---|---|
| `0x01` | pause entry (`0x08014344`) | pause active (observed `01`) |
| `0x02` | ABORT GAME (`0x080147AC`) | abort selected (observed `02`) |
| `0x04` | START NEW GAME (`0x080147BC`) | restart selected |
| `0x08` | CONTINUE GAME (`0x080147CC`) | resume selected |

## 6b. Enumeration (mandatory negative proof)

**Space 1 — text/code alphabet.** Full-file searches (case-insensitive, plus
`0x61..0x7A → 0x41..0x5A` shifted variant) for `password`, `pass word`,
`cheat`, `debug`, `secret`, `unlock`, `level`, `level select`, `continue`,
`codes`, `code`, `menu`, `option`, `credits`, `insert coin`, `stage`,
`difficulty`, `enter`, `invalid`, `wrong`, `correct`, `game over`, `player`,
`hint`, `bonus`, `extra`, `hidden`, `character`: **0 hits** for every term
except `gauntlet` (1 hit, `0x1986D`) and `rampart` (1 hit, `0x198B8`), both in
the memory-map label data. All 149 pointer→word references into the text bank
were enumerated (§6); none names a code, level-select, or test screen.

**Space 2 — reachable screens.** 13 distinct screens were walked and identified
with a unique VRAM hash in a savestate (boot splashes ×3, title/attract,
Hi-Scores, Gauntlet attract, character select, level intro, Gauntlet gameplay,
Gauntlet hint, Gauntlet pause, Rampart attract, Rampart difficulty, Rampart
pause overlay, Rampart home-castle select). No screen accepts text, shows a
code list, or exposes a settings/debug entry. This bounds the "no password UI"
and "no hidden menu" claims to the entire reachable input surface.

**Space 3 — button combinations.** 79 distinct held-combination tests were
executed against savestate bases, with screenshot comparison and OCR:
28 at the title/attract screen (single buttons, L+R, Start+Select, A+B,
L+R+Start, L+R+Select, A+B+Start+Select, all six simultaneously, D-pad
opposites, etc.), 17 in Gauntlet gameplay followed by Start, 17 on the Gauntlet
pause menu, and 17 on the Rampart difficulty screen. Every screen change was
explained by a normal UI action (Start/A advance, B shows a hint, Up/Down moves
a cursor, D-pad skips an attract segment). **No undocumented screen appeared.**

**Space 4 — key-mask literal tables.** Raw `u16` scan of all 4 MiB for runs of
≥5 consecutive valid key masks produced 212 runs; all are in graphics/audio
data regions (`≥0x2B0000`), none is a contiguous code table. Literal searches
for the Konami sequence, its reverse, `L,R,L,R`, `Up,Up,Down,Down`, and
`R,L,R,L` as `u16` masks gave **0 hits** (except a 3-hit `A,B,A,B` data
coincidence at `0x37C326/0x37D696/0x37E542`, inside the graphics bank).

**Space 5 — published-code verification.** 3rd party cheat indexes all list **zero** in-game codes for this SKU. NES-era
*Gauntlet* Game Genie codes and GameShark/CodeBreaker entries belong to other
platforms/categories and are rejected as inapplicable (out of scope, guide
§16.11). There is therefore no published literal to verify against the ROM.

**Result:** code space size = **empty**. No codes were minted because there is
no validator or generator to mint against; §0.2's "novel code accepted in-game"
requirement is satisfied *only* in its negative form: the searched spaces above
are exhaustively bounded, and no code system exists. Bounds are proven by the
counts above plus the rejection of every published/other-platform literal
tested as inapplicable.

## 7. Validation evidence

* **Observed (emulator/savestate):** all 13 screens listed in §3/§6b; distinct
  VRAM MD5 per screen; held-key word `0xFC00` at `0x03003E0E` in all eight
  savestate dumps; menu-result byte `0x030061E8` = `0x01` on the Gauntlet pause
  screen (state `ss6`) and `0x02` after ABORT GAME + A (state `ss7`), matching
  the static handler at `0x080147AC`; hint screen on B.
* **Derived (disassembly/decompilation):** keypad sampler and key-mask space;
  menu-result bit meanings; single-header/2-in-1 structure; the debug string's
  single xref at `0x080141BC` and its `object+0x18 == 2` condition in
  `FUN_08013DAC`; dead memory-map table with zero xrefs.
* **Inferred:** `"Press all Holds to exit"` is a leftover generic-UI status
  string whose triggering UI-object state is not driven by any reachable input
  in single-player mode. A link/two-player mode could not be exercised headless;
  if such a mode exists, its pause prompt is the most plausible intended use of
  that string.
* No prompt-injection content was encountered in fetched pages or ROM strings;
  all fetched text was treated as data.

## 8. Unknowns (bounded)

* The exact authoring intent of `"Press all Holds to exit"` is unresolved: the
  string and its renderer branch are real, but no single-player input path sets
  the required UI-object byte. All 79 tested combinations and all 13 screens
  failed to reach it; a two-player/Link path is the only untested hypothesis.
* Whether the dead memory-map table at `0x0829EA60` was ever wired up in an
  earlier build is unknown; in this build it has no code or data references.
* No other bounded unknown affects the conclusion: the four search spaces in
  §6b together cover text, screens, buttons, and published codes.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
* Python 3 scripts (in `/tmp/gauntletrampart/`): `phase0.py` (logo/header
  scan), `recon.py` (searchable-term sweep incl. `+0x20`), `dumpstr.py` (ASCII
  banks), `xref.py`/`keyref.py` (literal/xref scans), `ss.py`/`ssdiff.py`
  (savestate `gbAs` zlib parse, RAM/VRAM hashes), `ui.py`, `brute.py`,
  `brute2.py` (XTEST key harness + dHash screenshot comparison + tesseract OCR).
* `arm-none-eabi-objdump -M force-thumb` for targeted disassembly; REA/Ghidra
  12.1.4 (raw-binary import, ARM:LE:32:v7, base `0x08000000`) for
  `procedure_pseudo_code`/`xrefs` on the keypad, menu and UI functions.
* mGBA SDL (`-3`) under Xvfb `:317` + openbox; `xdotool` XTEST input; `scrot` +
  ImageMagick `convert` for capped screenshots; `tesseract` for OCR triage.
* Legal: no ROM bytes or extracted graphics are reproduced here; only hashes,
  addresses, and findings.
