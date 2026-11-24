# The Adventures of Jimmy Neutron Boy Genius: Attack of the Twonkies (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Adventures of Jimmy Neutron Boy Genius: Attack of the Twonkies.gba` |
| Size | 4,194,304 bytes (0x00400000, 4 MiB) |
| Header title | `JIMMYNEUAOTT` |
| Game code | `BJYE` |
| Maker code | `78` |
| Fixed byte 0xB2 | `0x96` (valid) |
| Version / complement / checksum | `0x00` / `0x12` / `0x0000` (checksum 0 is a common rebuilt-header artifact; entry word `0xEA00002E` is the stock branch to `0x080000C0`, so this is **not** a scene-cracktro image) |
| Developer / publisher | Tantalus Interactive / THQ (confirmed by in-credits text at `0x0804C6AA` and 3rd party cheat indexes) |
| MD5 | `2c2e9b38c21fd511b4f1871b12183416` |
| SHA-1 | `16ba112f07d02484febd554f902bb18776144186` |
| SHA-256 | `18d516cf91a90d182c27e0d8d1378e06083041275b80fbb703844d3241d36f2c` |

**SKU warning (§16.11):** the widely published Jimmy Neutron GBA passwords
(`2040YL61TT0T`, `GGP6WCC273-3`, `2H?-!L81TT0K`, `+R6H!L91TT0F`,
`456N$DWBWM?`, …) belong to **Jimmy Neutron: Boy Genius** (the *first* GBA
game, a different engine/SKU). All five were searched literally in this ROM:
**0 hits each**. Treating them as this game's codes would be a SKU conflation.

## 2. Executive summary

**Finding: this GBA SKU has no in-game code system.** There is no password
screen, no text/keypad entry surface, no button-code sequence, no debug menu,
and no hidden "code" gate. The only developer-intended unlockables are
**progress/save-bit gated** (bonus challenges after Retroland, bonus jetpack
race after finishing the game, hidden invention pieces / Neutronium
collectibles). These are legitimate unlockables in scope, but they are not
codes: no input can be entered to obtain them.

The negative is **bounded**, not "not looked for":

* Every screen reachable from a cold boot was walked in mGBA with screenshots
  and savestate RAM diffs (§3, §7).
* The full 4 MiB was searched for code/password/debug keywords in **five**
  encodings (ASCII, lowercase, UTF-16LE, UTF-16BE, XOR 0x20): **0 hits** for
  `PASSWORD`, `CHEAT`, `SECRET`, `UNLOCK`, `WARP`, `DEBUG MENU`, `LEVEL SELECT`,
  `INVINCIBLE`. The only `code` hit is ordinary dialogue
  ("moral code, I am the one who", `0x08049114`), and `Code: B.Wodok`
  (`0x08051929`) is the Shin'en GAX audio-engine banner (§11).
* **0** alphabet/password-table strings, **0** 4–20-character uppercase/digit
  code-shaped strings in 140,983 extracted strings.
* The joypad state machine has exactly **8** per-button globals, each with
  **2** ROM xrefs (one writer, one reader, both inside the single input-copy
  routine at `0x08030EE8`) — i.e. no press-history/sequence comparator exists.
* Ghidra auto-analysis produced **1,508** functions; the menu and input code
  that were decompiled contain only screen dispatch and option toggles.
* a 3rd party cheat index's archived GBA page documents only leftover *text* (developer credits,
  splash-screen asset names, GAX error strings, an `EXCEPTION. PROGRAM HALT.`
  fragment) — no debug menu or cheat, consistent with our static result. Its
  "debugging functions" category is explained by those leftover strings, not
  by a reachable menu.

No validator exists to reverse, so no novel code could be minted; §6b states
this explicitly and enumerates the spaces that *were* checked (§0.2's
"bounded negative" branch).

## 3. How to reproduce

**Environment:** mGBA 0.10.5 under Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`,
3× scale. Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad=arrow keys. The ROM was **copied** to
`/tmp/jimmyneutron2/game.gba` byte-for-byte (MD5 verified) so emulator
artifacts never touched the ROM folder.

**Cold-boot walk (all screens observed):**

| # | Screen | Trigger | Evidence file |
|---|---|---|---|
| 1 | Nick Games splash | boot | `boot.png` |
| 2 | Title logo | ~10 s | `menu1.png` |
| 3 | Attract-mode gameplay demo + "DEMO PRESS START" | idle on title | `mainmenu.png` |
| 4 | "Press START" title prompt | interrupt demo | `pause2.png` |
| 5 | Intro cutscene ("There it is Carl.") | Start → slot → confirm | `afterslot2.png`, `cut3.png` |
| 6 | Save-slot select ("Please select the game you wish to continue playing", 3 slots) | Start from title | `aftercombos.png`, `gameplay.png` |
| 7 | Overwrite confirm ("Previous progress will be lost!") | A on occupied slot | `slot1.png` |
| 8 | Hub gameplay (Jimmy's house, HUD, snowflake counter) | advance cutscene | `gameplay3.png` |
| 9 | Pause menu: **resume / restart / quit** | Start in gameplay | `pausemenu.png` |
| 10 | Quit confirm: **no / yes** | quit → A | `quitmenu.png` |

Additional negative probes: Select in gameplay (Brainblast) produced no menu
at this early progress state (`brainblast.png`); Select on the title did
nothing (`title_select.png`); L+R, L+R+Start, Up×2+Down×2, A+B+Start,
Start+Select, L+R+A+B, R+L+Up+Down and triple-Start on the title produced
**no** hidden screen — every resulting savestate showed the same screen-state
word (below).

**RAM evidence (savestate diffs, §16.13):** mGBA `.ssN` states are PNGs with a
zlib `gbAs` chunk; decompressed size 397,312 bytes. IWRAM begins at state
offset `0x19000`, EWRAM at `0x21000`. The word at **IWRAM `0x0300000C`** is a
clean screen-state discriminator:

| State | `0x0300000C` |
|---|---|
| Title / attract | `0x00000005` |
| Save-slot select | `0x00000001` |
| Cutscene / gameplay | `0x00000000` |

Interface diffs: title→slot-select 6,644 IWRAM bytes changed; slot-select→
gameplay 12,489 bytes; gameplay (dialogue)→gameplay (free roam) 2,226 bytes.
Raw states kept as `state_*.bin` in the work dir.

**No codes were entered** because no entry surface exists. To demonstrate the
absence rather than assert it, the button-combo battery above was pressed on
the title and verified via the RAM state word: no combo produced a value
outside `{5, 1, 0}` or any new menu.

## 4. Address map

| Address (ROM) | Meaning |
|---|---|
| `0x08000000` | Stock entry branch `0xEA00002E` → `0x080000C0` |
| `0x08016000`-`0x08017000` | Level-table accessors: `0x08016DF4` count (returns 25), `0x08016E10` name pointer, `0x08016E30`/`0x08016E40` field accessors |
| `0x08030E78` | Button-bit unpacker; writes globals `0x0300066C`…`0x03000688` |
| `0x08030EE8` | Input-copy routine; sole reader of those globals, copies into a per-object struct at offsets `0x70/0x78/0x7C/0x80/0x8C/0x90/0x94` |
| `0x0803A8A4` | Literal pointer to `NEW GAME` string (`0x0804ABF3`) |
| `0x0803B300`-`0x0803B5D8` | Save-slot / level-list render code; strides the level-name bank by `0x2E` (46 bytes) |
| `0x0804AFD1` | Level-name bank (46-byte padded records), referenced from `0x0803B354` and `0x0803BC88` |
| `0x0814DA18` | **Level definition table**, 25 × 8-byte records `{u32 name_ptr, u16 type, u16 world_index}` |
| `0x08049114` | Dialogue containing the only lowercase "code" hit ("moral code…") |
| `0x0804F8EC` | Leftover developer note `Use U/D/LTRIG/RTRIG` (1 pointer, at `0x0803DB08`) |
| `0x08051904`, `0x08051D8E`, `0x08051D70` | GAX engine banner, `EXCEPTION. PROGRAM HALT.`, `FUNCTION NAME:` — leftover text; `EXCEPTION` has **0** pointers |
| `0x0300000C` (IWRAM) | Screen-state word (5 title / 1 slot-select / 0 in-game) — observed |
| `0x0300066C`-`0x03000688` (IWRAM) | 8 button globals, 2 xrefs each — *no* sequence matcher |

Save format: 512-byte SRAM (`game.sav`), three slot headers. A 512-byte SRAM
was produced by normal play; no file-based password was found.

## 5. Algorithm

No code validator exists. The only "decoder" found is the level-list renderer:
`name = 0x0804AFD1 + (index * 0x2E)` for the 46-byte-padded display names, and
`level_record = 0x0814DA18 + (index * 8)` for the canonical 25-entry table.
Accessor functions at `0x08016DF4`/`0x08016E10`/`0x08016E30`/`0x08016E40`
enumerate and dereference that table. There is no checksum, alphabet, key
schedule, or comparison against user-typed data.

## 6. Tables

**Level definition table at `0x0814DA18`** (25 entries, `{name_ptr, type,
world_index}`); `type=3` marks the three race/"challenge" stages:

| # | Name | type | world |
|---:|---|---:|---:|
| 1 | The Atoms Family | 2 | 0 |
| 2 | Space Chase | 3 | 0 |
| 3 | The Genius Has Landed | 2 | 1 |
| 4 | They're Here! | 2 | 2 |
| 5 | Sheen's Serenade | 2 | 3 |
| 6 | Bully For You | 2 | 4 |
| 7 | "You Can't Stop The Music" | 2 | 5 |
| 8 | Look Who's Twonking | 2 | 6 |
| 9 | Thunderstruck | 2 | 7 |
| 10 | Little Genius | 2 | 8 |
| 11 | DeBUGging | 2 | 9 |
| 12 | A Small Problem in the Lab | 2 | 10 |
| 13 | Hamstergeddon | 2 | 11 |
| 14 | Particle Acceleration | 3 | 1 |
| 15 | Retroland After Dark | 2 | 12 |
| 16 | Keep Gromps Within Car | 2 | 13 |
| 17 | Back Into Heck | 3 | 2 |
| 18 | Substitute Creature | 2 | 14 |
| 19 | Deck the Malls | 2 | 15 |
| 20 | Chillin' in the Lab | 2 | 16 |
| 21 | Gromper Stompers | 2 | 17 |
| 22 | Retroville Renovation | 2 | 18 |
| 23 | Urban Renewal | 2 | 19 |
| 24 | Dark Matter Days | 2 | 20 |
| 25 | It Gets WORSE? | 2 | 21 |

(`DeBUGging` is a pun in a level title, **not** a debug-menu marker.)

**Button globals** (`0x0300066C` + 4·n, n=0..7): bits 16/17/21/20/25/24/23/22
of the engine's 32-bit key word. Each has exactly two literal-pool references
(one writer at `0x08030EC8`-`0x08030EE4`, one reader at `0x0803F40`-`0x0803F5C`).

**Unlockables (in scope, but save-gated, not codes):** bonus challenges unlock
after *Retroland After Dark*; bonus jetpack-race level unlocks after finishing
the game (3rd party cheat indexes, consistent across SKUs); 12 invention
names at `0x0804441A`-`0x08044532`; collectible Neutronium / invention pieces
(dialogue at `0x080447F8`, `0x080480B4`); `HINTS` option string at `0x0804ACD3`
(0 direct pointers — reached through an offset-addressed UI string bank).

## 6b. Enumeration

**Code space size: none exists.** This is the §0.2/§16.3 "No system" case,
proven by counts rather than asserted.

| Space searched | Count | Result |
|---|---:|---|
| Strings extracted from full 4 MiB (`strings -n 3`) | 140,983 | 0 `password`, 0 `cheat`, 0 `level select`, 0 `secret code`, 0 `debug menu` |
| Keyword encodings tried (ASCII, lower, UTF-16LE/BE, XOR 0x20) | 9 terms × 5 | all 0 except the two explained `code` hits |
| Uppercase/digit code-shaped strings (4–20 chars) | 0 | no candidate codes |
| Password alphabets / code tables (`ABCDEFGHIJKLMNOPQRSTUVWXYZ…`) | 0 | no alphabet bank |
| First-game published passwords searched literally | 5 | 0 hits each (different SKU) |
| Ghidra-analyzed functions | 1,508 | decompiled menu/input routines: dispatch + toggles only; no validator |
| Joypad globals and their ROM xrefs | 8 globals × 2 | both xrefs in one input-copy routine; **no** press-history/sequence table |
| Level-definition records enumerated | 25 | complete level list dumped above |
| Save slots | 3 | only 1 populated after normal play; no code-entered slots |
| Reachable screens walked (cold boot → gameplay → pause → quit) | 10 | enumerated in §3; no text/keypad entry screen, no hidden menu |
| Button combos pressed on title, RAM-state checked | 8 | screen-state word stayed in `{5,1,0}`; no new screen |

**Novel code:** not applicable — there is no validator or entry surface from
which to mint one. Per §0.2 this is reported as the bounded-negative branch:
the enumeration above is the proof, and inventing a "code" would be dishonest.

**Bounds proven by rejection:** no rejection test can be performed because the
game exposes no field to submit. The closest bounded tests performed were the
eight title-screen button combos, each checked in RAM: none changed the screen
state to any value outside the observed three-state set
(`{title=5, slot-select=1, in-game=0}`). The ROM likewise contains no
comparison constant that could serve as a rejected password: the code-shaped
string search returned 0 and the keyword search returned 0 in every encoding.

**Search-space limitations (stated, not hidden):** late-game screens reached
only by clearing levels 1–25 (results/summary, bonus challenges, bonus level)
were not played through; their existence is supported by the ROM strings and
the published unlock conditions, not by our own screenshots. Any code system
that existed *only* behind a completed-game save was therefore not observed
directly — but it would still need an entry surface, and none exists in any of
the 10 reachable screens or in the UI string bank.

## 7. Validation evidence

* **Observed** — emulator screenshots (`*.png` in `/tmp/jimmyneutron2`)
  for all 10 screens in §3; savestate RAM diffs giving the `0x0300000C` state
  word `5 → 1 → 0`; 512-byte SRAM written by normal play.
* **Derived** — `objdump -M force-thumb` disassembly of the input routines and
  level-table accessors; Python pointer scans giving the exact xref counts in
  §4/§6b; Ghidra 12.1.4 auto-analysis (1,508 functions) and decompilation of
  the frontend menu function `0x0803AEA4`; the 25-record level table parsed
  directly from `0x0814DA18`.
* **Inferred** — that the `EXCEPTION. PROGRAM HALT.` / `Use U/D/LTRIG/RTRIG`
  strings are leftover developer text rather than a reachable debug overlay
  (supported by 0 pointers for `EXCEPTION` and by a 3rd party cheat index's archived page, but
  no live breakpoint was available to prove the single xref of the other note
  never fires). Unlock conditions for bonus content are from published sources
  plus ROM strings, not from a full playthrough.

**Prompt-injection / page-as-data note:** 3rd party cheat indexes were fetched only through the
Internet Archive snapshot (direct fetch returned 403 / CAPTCHA). Its content
was treated strictly as data; no instruction found in a fetched page or ROM
string was executed.

## 8. Unknowns

* The `OPTIONS` / `HINTS` / `BRIGHTNESS` / `VIEW CREDITS` strings
  (`0x0804A577`…`0x0804ACFF`) have no direct 32-bit pointers and no menu
  entry was reachable in our walk. They may belong to an unused language-
  select path or a build-time-removed menu; the exact reach path is unknown.
* No full playthrough was performed, so late-game results/bonus screens were
  not screenshotted. Their state is inferred from strings + published unlocks.
* The single live xref to `Use U/D/LTRIG/RTRIG` (`0x0803DB08`) was not
  breakpoint-verified as unreachable; it is a literal in menu-render code.
* The mGBA GDB stub proved unreliable here (modern GDB `qSupported` packet
  errors and a wedged stub after one session), so RAM reads used the
  savestate-diff method (§16.13) instead.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep` for Phase 0
  and the bounded string searches.
* Python 3 scripts (in `/tmp/jimmyneutron2`): `allstrings.txt` dump,
  pointer/xref scanner (`struct.find` of little-endian 32-bit constants),
  `ss.py` for zlib-decompressing mGBA `gbAs` chunks and diffing IWRAM.
* `arm-none-eabi-objdump -M force-thumb` for raw Thumb disassembly.
* Capstone for the Thumb PC-relative literal scan of `0x04000130` (0 literal
  hits; 3 raw occurrences).
* REA MCP / Ghidra 12.1.4: raw ARM import at base `0x08000000`, default
  auto-analysis (42 s), 1,508 procedures, decompiled `0x0803AEA4`.
* mGBA 0.10.5 (`-3`), Xvfb `:317`, openbox, xdotool, scrot.
* Web: websearch plus web.archive.org snapshot of the 3rd party cheat indexes GBA page
  (direct 3rd party cheat indexes fetches were blocked).

No ROM bytes or copyrighted assets are redistributed in this report; only
hashes, offsets, algorithms and our own observations are published.
