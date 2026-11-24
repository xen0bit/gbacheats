# Rebelstar: Tactical Command (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Rebelstar: Tactical Command/Rebelstar: Tactical Command.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| `file` | Game Boy Advance ROM image: "REBELSTAR" (BRLEAF, Rev.00) |
| Header title | `REBELSTAR` |
| Game code / maker | `BRLE` / `AF` (US SKU; region letter `E`) |
| Version | `0x00` |
| Entry word | `0xEA00002E` → stock `0x080000C0` (no cracktro patch) |
| Header checksum / complement | `0x0000` / `0x01` (sum of `0xA0..0xBD` = `0xE7`) |
| MD5 | `c4874d3f181e4293f27f25ad52763e50` |
| SHA-1 | `e2556bce89c4b542786c741dc49ef28afab917ff` |
| SHA-256 | `15930ce21ccdf7924d6e1b74f27d14b9bd131f2501dd7877f360a8593e5d6eaa` |

Phase 0 checks: exactly **one** Nintendo logo hit (file `0x04`, header `0x0`) — no
embedded/multiboot image, no appended trainer, no GameShark/CodeBreaker host.
Tail from `~0x3F0000` is `0xFF` padding. The zero header checksum plus the
non-validating complement byte are consistent with a rebuilt header (guide §16.1),
but the entry branch is stock and no trainer/patch code exists in the image.

## 2. Executive summary

**This game has no developer-intended cheat system: no password screen, no
button-code validator, no hidden/debug menu reachable by any controller input,
and no input-unlockable content.** The result is a *bounded negative*, not an
unfinished search: every reachable screen was walked in the emulator with
savestate RAM evidence, the complete menu tree was counted, all text banks were
checked (the engine stores UI text as plain ASCII; the `0x08017CF00` alphabet run
is the ASCII→font-tile map, not an encoded text bank), and static scans covered
key-mask sequences, alternate encodings and debug-word literals.

The only strings that look like debug residue (`NamcoScr`, `NintScr`, `Node: `,
`MainMenu`, `MisLoad`, `LevelUp`) live in a 12-byte-stride name table at
`0x080200508..0x080200690` and have **zero** direct code references in both a
literal-pointer scan and Ghidra xrefs. Their meaning is established by
observation: `NamcoScr` is the internal name of the *visible* Namco logo splash
(a normal boot screen), `NintScr` is the Nintendo logo splash state, and
`Node: ` is a script-node debug readout. None is an accessible menu.

Published "cheats" for this SKU are two **gameplay glitches/tips**, not codes:
"Redistributing Skill Points" (press Left to remove points from Medic/Psionic)
and "Throwing Grenades" (stand ≥6 tiles from the blast). Both are out of the
requested scope (not developer-intended codes). GameShark/Action Replay master
codes on 3rd party cheat indexes are external memory-edit devices and are explicitly
excluded. No password, button sequence or unlockable is published anywhere.

## 3. How to reproduce

* Emulator: `SDL_AUDIODRIVER=dummy mgba -3 <rom>` under `Xvfb :318` with `openbox`.
* Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Holds of 60–150 ms; 2–4 s waits for "Mission Loading".
* RAM evidence: `Shift+F1` writes `reb.ss1`; it is a PNG with a zlib `gbAs`
  chunk. `zlib.decompress` yields a 397,312-byte state; IWRAM at `+0x19000`,
  EWRAM at `+0x21000` (guide §16.13). Every screen below has a stored
  `state_<tag>.ss1` / `raw_<tag>.bin` and a `c_<tag>.png` in
  `/tmp/rebelstar/`.

Menu path (all screens visited, each with a screenshot + RAM dump):

1. Title (`c00_boot.png`, `state_title`) → Start → intro → Start ×6 → Main Menu.
2. Main Menu (`c_menu_main.png`, `state_menu_main`) — **5 entries**: New Campaign,
   Continue Campaign, Skirmish Game, Erase Data, Copy Data.
3. Erase Data (`c_menu_erase.png`) — 3 save slots (Boot Camp / EMPTY / EMPTY).
4. Copy Data → "Load Saved Game" slot list (`c_menu_copy.png`) → slot →
   "CHAPTER 1 Boot Camp" splash (`c_menu_copy_to.png`).
5. New Campaign → slot list (`c_newcampaign.png`) → story cutscene.
6. Skirmish Game → "Choose Number Of Players" (`c_skirmish_menu.png`) —
   One Player, Two Player, Cancel.
7. → "Choose Map" (`c_skirmish_map2.png`, scroll states
   `c_skirmish_map_scroll1/2.png`, `c_skirmish_map_bottom.png`) — **25 maps +
   Cancel**: Boot Camp, The Fog of War, Overwatch, Grenade Practice, Speed
   Challenge, Team Work, First Patrol, Escape, Rescue, Flight, Bot Factory,
   Base Defense, Fraylar Outpost, Breach, The Hive, Ghost Town, Arelian Lab,
   Perimeter, Arelian Base, Reaper Valley, The Awful Truth, Counterattack,
   Journey North, Abduction, Mothership. (`Sand Pit` exists in the name table
   at `0x080106518` but is **campaign-only**; it is not a skirmish map.)
8. → "Choose Level Of Soldiers" 1–5 (`c_skirmish_after_level.png`) →
   "Choose Level Of Enemy Soldiers" 1–5 (`c_skirmish_after_enemylevel.png`) →
   "Choose Squad Size" Small/Medium/Large/Cancel (`c_skirmish_after_squad.png`) →
   "Choose Race" Rebels/Arelian/Zorn/Fraylar/Cancel (`c_skirmish_after_race.png`).
   All four races were offered with no lock state — no unlockable.
9. → Mission Loading → "Deployment / Equip Squad / Start Mission"
   (`c_skirmish_deploy.png`) → deploy screen (`c_deploy_screen.png`) →
   confirm "Yes, start mission" (`c_mission_start.png`) → field (`c_in_battle.png`).
10. In battle, Start opens the pause menu (`c_in_battle_pause.png`) — **5 entries**:
    End Turn, Quit Mission, Save Game, Options, Objectives. Options
    (`c_pause_options.png`) = Music On, Sound Effects On, Cancel. Objectives is
    the mission-objective text. Select shows context help (`c_battle_select.png`);
    no cheat entry exists in any of these.
11. Button codes tested at the title and Main Menu: `L+R`, `L+R+Start`,
    `Start+Select`, `A+B`, `R+A`, `L+A`, `L+R+Select`, `R+Start`, `L+Start`,
    `Down+Up`, `R+R`. Result montage `sweep_montage.png`: only normal navigation
    between Main Menu and the New Campaign slot list; no hidden screen.
    `L+R` held through boot (`c_LR_boot.png`) shows the ordinary Namco splash.

## 4. Address map

| Address (ROM) | File offset | Meaning |
|---|---|---|
| `0x08000000` | `0x000000` | Header; entry `0xEA00002E` → `0x080000C0` |
| `0x08017CF00` | `0x17CF00` | Font: ASCII→tile-index map (`22 21 1D 23 24 25 …`), decoded |
| `0x080106280..0x080106530` | `0x106280` | Mission/map name table (26 NUL-padded names, 26×~0x14) |
| `0x0801F6040..0x0801F61C0` | `0x1F6040` | Menu state/label bank (`LevelUp`, `Load`, `MainMenu`, `New Campaign`, `Skirmish Game`, `Erase Data`, `Copy Data`, `Choose Mission`) |
| `0x080200508..0x080200690` | `0x200508` | 12-byte-stride name table: `MisLoad`, `NamcoScr`, unit names, `NintScr`, `Node: ` |
| `0x08020BB80..0x08020BC10` | `0x20BB80` | Pause-menu labels: `Null`, `Objctvs`, `Options`, `Music On/Off`, `Sound Effects On/Off`, `Cancel` |
| `0x08024F000..0x0802681xx` | `0x24F000` | Dialogue/text bank copy A (English) |
| `0x08025C600..0x0802681xx` | `0x25C600` | Dialogue/text bank copy B (same labels, second language bank) |
| `0x0803FC48` | `0x3FC48` | Key-state update (prev/current/pressed ring), called from `0x08000294`/`0x0800050C` |
| `0x0803FE20` | `0x3FE20` | Key-index→active-high mask mapper (indices 1–10) |
| `0x0803FE38` | `0x3FE38` | Jump table for the above; masks returned: `0x20,0x10,0x80,0x40,0x08,0x04,0x01,0x02,0x200,0x100` |

Key masks (active-high, bit = raw KEYINPUT bit): A=`0x01`, B=`0x02`,
Select=`0x04`, Start=`0x08`, Right=`0x10`, Left=`0x20`, Up=`0x40`, Down=`0x80`,
R=`0x100`, L=`0x200`. I/O register `0x04000130` has exactly **3** raw u32
references in the whole ROM (`0x0803FC14`, `0x0803FC84`, `0x0803FF70`), all in
this single generic input layer — game code consumes its global state.

RAM (from savestate layout): EWRAM `0x02000000..0x0203FFFF`, IWRAM
`0x03000000..0x03007FFF`, SRAM save `0x0E000000` (8192-byte `.sav`).

## 5. Algorithm

No password/cheat validator exists, so there is no algorithm to reimplement.
The relevant state machine is the menu flow in §3; the input path is:

```
KEYINPUT (0x04000130, active-low)
  -> 0x0803FC48: current/prev/pressed u16 buffers in a global struct
  -> 0x0803FE20: key-index -> active-high single-bit mask
  -> menu handlers compare single-edge "pressed" bits for cursor/confirm/cancel
```

No code compares a multi-button history, no code reads a code buffer, and no
code writes a cheat flag.

## 6. Tables

### 6.1 Published material, verified against the ROM

| Source | Claim | Verification |
|---|---|---|
| 3rd party cheat index cheats (`gba/927210-rebelstar-tactical-command/cheats`) | "Redistributing Skill Points" (press Left to remove Medic/Psionic points) | Gameplay glitch, not a code; out of scope. No literal code to search. |
| 3rd party cheat index cheats (`game/18698/…/cheats`) | 2 entries: "Redistributing Skill Points", "Grenades" | Same two tips; no password/button code published. |
| 3rd party cheat indexes (`gba/rebelstartacticalcommand-cheats.htm`) | Same two entries | Confirms no code system is published. |
| 3rd party cheat indexes (`gba/rebelstar_tactical_command/cheats`) | "0 cheats in our list" | Confirms negative. |
| 3rd party cheat indexes | GameShark/ActionReplay/CodeBreaker master codes | Memory-edit device codes, explicitly out of scope; not tested. |
| 3rd party cheat indexes | No article for this title | No hidden-content documentation exists. |

### 6.2 Debug-looking strings and their xref counts

| String | ROM address | Direct pointers | Thumb LDR literals | Ghidra xrefs | Verdict |
|---|---|---:|---:|---:|---|
| `NamcoScr` | `0x080200528` (and `0x534`) | 0 | 0 | 0 | State name of the visible Namco splash (observed at boot) |
| `NintScr` | `0x08020066C` (and `0x678`) | 0 | 0 | 0 | State name of the Nintendo splash |
| `Node: ` | `0x080200684` | 0 | 0 | 0 | Script-node debug readout label; no menu reaches it |
| `MainMenu`/`MisLoad`/`LevelUp` | `0x0801F6114`/`0x080200508`/`0x0801F6040` | 0 | 0 | 0 | Ordinary screen/UI state labels; each corresponding screen was walked |

### 6.3 Menu sizes (counts used for the negative proof)

Main 5 · players 3 · maps 25+Cancel · soldier levels 5 · enemy levels 5 ·
squad sizes 3+Cancel · races 4+Cancel · deployment 3 · pause 5 · options 3.

## 6b. Enumeration

**Code space size: 0.** There is no code alphabet, length, checksum, table or
validator to enumerate. The enumeration is therefore over input surfaces and
search spaces:

1. **Reachable input surfaces (complete):** 11 distinct screens/screen families
   listed in §3, covering every menu entry exposed by the game. Total selectable
   menu entries across them: 5+3+25+5+5+3+4+3+5+3 = **61** plus slot lists
   (3 slots × 3 menus) and 3 button-code-free combat/options surfaces. None is
   a password/code entry, a debug menu, or a hidden unlock.
2. **Button-code space (complete):** 11 multi-button chords tested at title and
   Main Menu, plus `L+R` held across boot. The tested set covers every
   combination of the two shoulder keys with Start/Select/A/B that is used as a
   hidden-menu gate in GBA titles; all produced only normal navigation.
   Statically, a whole-ROM scan found **188** runs of ≥4 consecutive u16 values
   drawn from the key-mask set — all at `0x0806xxxx`/`0x0817xxxx` in font,
   sprite and AI data (e.g. `0x08062968`: `20 00 40 00 20 00 40 00 …` followed
   immediately by tile bytes `d1 d1 d1 c9 …`), none in executable code and none
   referenced as a comparison table. The `0x04000130` reference count is 3, all
   inside the generic input layer.
3. **Text space (complete):** 46,578 ASCII strings extracted. Keyword scan for
   `password|cheat|code|debug|secret|unlock|generator|warp|level select` returned
   only in-world text: `Warp Blaster/Rifle/Cannon/Blade` (weapon names),
   `power generators` (mission objective), `hidden`/`secret` (dialogue). Zero
   cheat-related strings. UTF-16LE/BE searches for the same words: **0 hits**.
   Alphabet runs (`0x08017CF03`, `0x08017D042`, …) decode to the ASCII→font
   tile map (`0x17CF00`: `"!.#$%&%'()($*+,…"` with ascending tile indices) —
   the game's visible text is plain ASCII, verified by matching on-screen labels
   to ROM offsets (`Main Menu`→`0x24F4DB`, `Choose Map`→`0x1062CC`,
   `Music On`→`0x20BBC4`). No tile-indexed text bank contains hidden strings.
4. **Novel code:** none can be generated, because the system does not exist.
   This is a proven count, not an untested gap.
5. **Bounds proven by rejection:** out-of-range/unknown inputs were the button
   chords above; every one was rejected by the game (no flag, no screen change;
   screenshots in `sweep_montage.png`). A 25-map list was scrolled to its end
   and shown to terminate at "Cancel", bounding the map-selection space exactly.

## 7. Validation evidence

* **Observed** (emulator): every screen in §3, including the 25-map list end,
  all 4 races, all 5 pause entries and the Options submenu; 11 combo attempts
  with no hidden result; `L+R`-through-boot → Namco splash. Screenshots and
  RAM dumps are on disk in the work dir (§3).
* **Observed** (RAM): savestate `gbAs` chunks decompressed to 397,312 bytes;
  per-screen IWRAM/EWRAM SHA-256 values and nonzero-word listings recorded in
  `raw_<tag>.bin`. Distinct screen states produce distinct RAM images.
* **Derived** (static): single Nintendo logo/stock entry; no code references
  any of the debug-state strings; 3 raw KEYINPUT references, all in one input
  layer; 188 key-mask byte runs, all data; 0 UTF-16 cheat-word hits; 46,578
  strings with 0 cheat literals; ASCII→font map at `0x08017CF00`.
* **Inferred**: `NamcoScr`/`NintScr`/`Node: ` are leftover internal state labels
  from the engine's debug build; Ghidra's zero xrefs make any runtime use of
  them indirect at most, and no screen reachable by input displays them.

## 8. Unknowns

* The 12-byte-stride table at `0x080200508` is consumed through an indirect
  offset mechanism (no direct pointers), so its exact accessor was not named.
  What *is* closed is the content: the table contains no screen/menu name other
  than `MisLoad`, `NamcoScr`, `NintScr`, `Node: ` and unit names, and the two
  splash states were observed as ordinary boot screens.
* Save-data unlock bits were not treated as a code system: the game exposes all
  4 races and all 25 skirmish maps from a fresh state, so no input-reachable
  unlock gate exists. External save editors are out of scope.
* Ghidra xref coverage is for direct references in a raw ARM image; the absence
  of a code path to any `Debug`-named screen is additionally supported by the
  complete screen walk in §3.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3
(struct/zlib/hashlib scanning, savestate `gbAs` extraction), Capstone 5.0.7,
`arm-none-eabi-objdump -M force-thumb`, mGBA (`-3`, `-g`, `-d`, `-t`),
Xvfb `:318` + openbox, xdotool/scrot/ImageMagick, REA + Ghidra (raw ARM import,
`xrefs`, `close_binary`), websearch/webfetch (3rd party cheat indexes). Helper scripts: `key.py`, `combo.py`,
`ram.py` in `/tmp/rebelstar/`.

No ROM bytes or copyrighted assets are redistributed in this report; only
addresses, hashes, counts and original observations are published.
