# Babar: To the Rescue (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Babar: To the Rescue/Babar: To the Rescue.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `BABAR_TTR` |
| Game code | `BBVE` |
| Maker code | `GY` |
| Software version | 0 |
| Complement check (`0xBD`) | `0xE1` (matches `-(sum(0xA0..0xBC)+0x19) & 0xFF`) |
| Header checksum field (`0xBE`) | `0x0000` (present as zero; mGBA 0.10.5 boots the image) |
| Fixed byte (`0xB2`) | `0x96` |
| Entry branch | `0xEA00002E` → `0x080000C0` |
| Save hardware | EEPROM (mGBA log: `Detected EEPROM savegame`); 512-byte `.sav` |
| Embedded headers | none — the Nintendo-logo prefix occurs once, at file `0x4`; single GBA image |

Hashes:

```
MD5     91ba6a4571e20dd9c7604d685d134607
SHA-1   80be43f995dc6e3c1b0003872ce4cb681fe35a4a
SHA-256 4939b00cfc6476f499a6dd6e020d0e298b796b18c55baba69b71ee3d2b9d7f96
```

## 2. Executive summary

**There is no in-game password, button-code, debug-menu, secret-code, or unlock-code system in this ROM.** The game is a save-based platformer with a fixed menu tree. All of the following were reached and walked in mGBA: language select, 75th Anniversary Collection splash, title menu, high-score table, credits, options, profile select, profile sub-menu, reset confirmation, level-selector map, briefing, tutorial, in-game HUD and pause menu.

The evidence is threefold.

1. **Text space.** The ROM contains 43,820 printable strings of length ≥ 4. Case-insensitive counts for `password`, `passwd`, `cheat`, `debug`, `secret`, `unlock`, `gallery`, `extras`, `bonus`, `sound test`, `level select`, `warp`, and `skip` are all **zero**. The localized equivalents (`mot de passe`, `Passwort`, `contraseña`, `código`, `truco`, `Triche`, `geheim`) are also **zero**. The complete English UI label bank is 38 strings plus `Credits`; every label is a menu item, a gameplay/result label, or a story string. There is no keyboard, alphabet grid, text box, or submit/backspace control anywhere in the label set.
2. **Button space.** The engine’s two key-input helpers were located at `0x080163D4` (edge-press with a `0x03001414` shadow word) and `0x08016484` (held query). A full ARM BL scan finds 68 calls to the edge helper and 51 to the held helper. The button indices passed are only `0,1,3,4,5,6,7` (A, B, Start, Right, Left, Up, Down). **Select (2), R (8), and L (9) are never read by menu code.** Each call tests a single button, and no progress/sequence counter is referenced by the helpers or their call sites. Dynamic probes at the title (Select, L, R, Up, Down, A+B, L+R, Select+Start, L+R+Start, Konami sequence) produced no hidden screen; only A/Start enter the normal Play path.
3. **Published sources.** VGChartz reports “Total cheats available: 0”. GameFAQs returns 403 and its archive snapshot is unavailable. The only published Babar codes are CodeBreaker/GameShark *memory-device* codes (Almar’s Guides, emucheatz), which are not enterable in-game and are outside this report’s scope. No published native password or button code exists to test.

The only unlockable content is normal save progression: the level-selector map shows a single starting node for a fresh profile, and the ROM contains nine level definitions (`level1.xml` … `level9.xml`) and nine level-title strings. Progression is stored in EEPROM; there is no code path that unlocks levels from button input.

Because the code space is empty, there is no unpublished code to mint. The bounded negative — zero alphabet, zero length, zero checksum, zero table, and the enumerated menu/button space — is the deliverable.

## 3. How to reproduce

### Emulator and keymap

```bash
Xvfb :151 -screen 0 1024x768x24 &
DISPLAY=:151 openbox &
DISPLAY=:151 SDL_AUDIODRIVER=dummy mgba -3 \
  "/mnt/gbacheats/roms/Babar: To the Rescue/Babar: To the Rescue.gba"
W=$(DISPLAY=:151 xdotool search --name mGBA | head -1)
DISPLAY=:151 xdotool windowfocus "$W"
```

mGBA 0.10.5 SDL default keymap used here: **A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrows.** Hold each key 150–250 ms; menu transitions take about 2–3 s. Savestates: `Shift+F1..F7` save, `F1..F7` load.

### Exact menu path

1. Boot → language screen (English selected) → A.
2. 75th Anniversary Collection splash → title. The title menu is a **horizontal carousel**; the initial item is `Play` at the bottom.
   - Right: `Play` → `High Scores` → `Credits` → `Options` → `Play`.
   - A opens the selected item; Left goes backwards.
3. `Options` → A: `Options Menu` with exactly two rows:
   - `Sound Effects Volume`
   - `Music Volume`
   - Up/Down selects a row; Left/Right changes the five-step bar; B returns to title.
4. `High Scores` → A: three rows, all `No High Score` on a fresh save; A or B returns.
5. `Credits` → A: rolling credits; B exits.
6. `Play` → A: `Select Profile`, a 2×2 grid of four slots: **Babar, Arthur, Flora, Zephir**. Empty slots show `Empty`; used slots show `Level N` and the level title.
   - A on an empty slot starts a new game (level map).
   - A on a used slot opens `Continue / Reset / Cancel`.
   - `Reset` opens `Are you sure you want to reset the game? … Press A for Yes and B for No.` B cancels; A would erase that profile.
   - B returns to title.
7. `Continue` / new game → level-selector map. A fresh profile shows one node, `Level 1.1 / Balloon Ride`, with a small `2` badge. A enters; B returns to profile select.
8. Level entry → cutscene → briefing (`Help Babar control the balloon…`) → A → tutorial (`Use the +Control Pad…`) → A → gameplay.
9. In gameplay, Start opens pause: `Continue` / `Quit`. Continue resumes; Quit returns to the map/profile flow.
10. The result/level-record screen is gameplay-only; its labels (`Level Completed`, `Level Record`, `Crowns`, `High score!`, `Overall score`) are present in the string bank, but no cheat or code entry exists there.

### Screenshot evidence

Full-window captures are in `/tmp/opencode/babar/shots/`; 720×480 GBA-viewport crops are in `/tmp/opencode/babar/crops/`:

```
title_play.png  title_options.png  options_menu.png  high_scores.png
credits.png     profile_select.png profile_submenu.png reset_confirm.png
level_selector.png briefing.png   tutorial.png      pause_menu.png
gameplay.png
```

They are analysis artifacts, not committed, to avoid redistributing game artwork.

## 4. Address map

File offset ↔ ROM address: `ROM address = 0x08000000 + file offset`.

| Item | File offset | ROM address | Notes |
|---|---:|---:|---|
| GBA header | `0x000000` | `0x08000000` | title `BABAR_TTR`, code `BBVE`, maker `GY` |
| ARM entry | `0x000000` | `0x08000000` | `b 0x080000C0` |
| Input edge helper | `0x0163D4` | `0x080163D4` | `r0` = shadow ptr, `r1` = button bit; returns newly pressed |
| Input held helper | `0x016484` | `0x08016484` | `r1` = button bit; returns held |
| Unused repeat variant | `0x01642C` | `0x0801642C` | no BL callers found |
| Key register literal | `0x0163E0` | `0x080163E0` | `mov r3,#0x04000000; add r3,#0x130` |
| Key shadow | — | `0x03001414` | active-high pressed bits; 53 ROM literal references |
| Profile/menu logic | `0x00CE88` | `0x0800CE88` | right/left checks, profile index clamp to 3 |
| Localized string pointer table | `0x0104D8` | `0x080104D8` | 32-bit ROM pointers; English labels at `0x105A8`+ |
| English UI string bank | `0x3E3C8C` | `0x083E3C8C` | 38 NUL-terminated labels |
| `Credits` label | `0x3E244C` | `0x083E244C` | title menu item |
| Level-title strings | `0x3E3E04` | `0x083E3E04` | nine titles, `Balloon Ride` … `Going Home` |
| Resource-name table | `0x0736D4` | `0x080736D4` | `level1.xml` … `level9.xml`, `menu.xml`, `credits_*.xml`, `levelselector.xml`, `briefing.xml`, `langselect.xml` |
| Resource names (secondary) | `0x3E1E18` | `0x083E1E18` | `level1.xml`, `level9.xml`, … |
| EEPROM signature | `0x3E1DD8` | `0x083E1DD8` | ASCII `EEPROM_V124` |
| Font/ASCII table | `0x0708AC` | `0x080708AC` | ASCII/font mapping table (observed; likely the label glyph map) |

## 5. Algorithm

### 5.1 Key input

The edge helper at `0x080163D4` is the only input primitive used by menus:

```c
u16 *shadow = (u16 *)r0;      // normally 0x03001414
u32 bit    = r1;               // 0..9
u16 mask   = 1u << bit;
u16 keys   = ~*(volatile u16 *)0x04000130;   // 1 = pressed
bool new   = (keys & mask) && !(*shadow & mask);
*shadow = (*shadow & ~mask) | (keys & mask);
return new;
```

The held helper at `0x08016484` returns `(~*(u16 *)0x04000130) & (1u << bit)` directly.

Button-bit convention (confirmed by the call sites and by watching the title/profile screens):

| Bit | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| Button | A | B | Select | Start | Right | Left | Up | Down | R | L |

Menu code calls the edge helper with only `{0,1,3,4,5,6,7}`. It calls the held helper with only `{0,1,4,5,6,7}`. **Select, R, and L are never queried.** The five register-driven edge call sites are menu-index loops; the immediate sites already cover every button the game’s menus use.

### 5.2 Menu state machine

There is no text buffer, no string comparison against a code table, and no checksum. Each screen is a fixed item list:

```
title:    [Play, High Scores, Credits, Options]        // horizontal, wraps
options:  [Sound Effects Volume, Music Volume]         // 2 rows, 5-step bars
scores:   [slot 0, slot 1, slot 2]                     // "No High Score" until played
profile:  [Babar, Arthur, Flora, Zephir]               // 2x2, 4 slots
submenu:  [Continue, Reset, Cancel]                    // only for a used slot
pause:    [Continue, Quit]
```

`Continue`/A on a slot enters the level-selector map. The map shows only the currently unlocked node(s); a fresh profile begins at `Level 1.1 / Balloon Ride`. The ROM contains nine level definitions and nine titles, so the intended unlockable surface is the nine-level save progression.

### 5.3 Save model

mGBA detects EEPROM and creates a 512-byte `.sav`. Profile progress is persisted and reloaded: after entering level 1.1 and returning, the Babar slot reads `Babar / Level 1 / Balloon Ride` instead of `Empty`. The exact EEPROM byte layout and the per-level unlock bitmask were not decoded; they are not needed to establish that no code system exists.

## 6. Tables

### 6.1 Title menu (observed order)

| Index | Label | String address | Action |
|---:|---|---:|---|
| 0 | `Play` | `0x083E3C8C` | profile select |
| 1 | `High Scores` | `0x083E3C94` | score table |
| 2 | `Credits` | `0x083E244C` | credits roll |
| 3 | `Options` | `0x083E3CA0` | options menu |

Right advances, Left retreats, and the list wraps. There is no fifth item.

### 6.2 Options menu

| Row | Label | Address | Control |
|---:|---|---:|---|
| 0 | `Sound Effects Volume` | `0x083E3CB8` | Left/Right, five steps |
| 1 | `Music Volume` | `0x083E3CD0` | Left/Right, five steps |

Down past row 1 does nothing; there is no third row.

### 6.3 Profile and sub-menu

| Slot | Default name | Address of name |
|---:|---|---:|
| 0 | `Babar` | `0x083E2310` |
| 1 | `Arthur` | `0x083E3DC8` |
| 2 | `Flora` | `0x083E3DD0` |
| 3 | `Zephir` | `0x083E3DD8` |

Sub-menu: `Continue` (`0x083E3CF0`), `Reset` (`0x083E3CFC`), `Cancel` (`0x083E3D04`). Reset confirmation: `0x083E3D5C`.

The ROM also carries the names `Celeste`, `Alexander`, `Isabelle`, and `Pom` (`0x083E3DE0`–`0x083E3E00`); these are additional character names/story labels, not extra save slots. The profile grid accepts only four slots (the index clamp at `0x0800CE94` is `cmp r3,#3; bls`).

### 6.4 Level titles (nine definitions)

| # | Title | Address |
|---:|---|---:|
| 1 | `Balloon Ride` | `0x083E3E04` |
| 2 | `Across the Rivers` | `0x083E3E14` |
| 3 | `Jungle Rally` | `0x083E3E28` |
| 4 | `The Savannah` | `0x083E3E38` |
| 5 | `Down the River` | `0x083E3E48` |
| 6 | `In the Snow` | `0x083E3E58` |
| 7 | `Motorcycle Rally` | `0x083E3E64` |
| 8 | `Off to the Island` | `0x083E3E78` |
| 9 | `Going Home` | `0x083E3E8C` |

Resource names `level1.xml` … `level9.xml` are in the archive directory at `0x080736D4`; `levelselector.xml` is the map screen, `briefing.xml` the pre-level card, `langselect.xml` the boot language screen, and `menu.xml` the main menu. No `debug.xml`, `password.xml`, `cheat.xml`, or similar exists.

### 6.5 Complete English UI label inventory (38 strings + `Credits`)

`Play`, `High Scores`, `Options`, `Options Menu`, `Sound Effects Volume`, `Music Volume`, `Select Profile`, `Continue`, `Reset`, `Cancel`, `No High Score`, `Empty`, `Completed`, `Level`, `Crowns`, `High score!`, `Overall score`, the reset-confirmation sentence, `To the Rescue`, `Level Completed`, `Arthur`, `Flora`, `Zephir`, `Celeste`, `Alexander`, `Isabelle`, `Pom`, the nine level titles, `A game by`, `Level Record`, plus `Credits`. The same bank has no password, cheat, debug, secret, gallery, sound-test, or unlock label.

## 6b. Enumeration

### 6b.1 Code space

| Property | Result |
|---|---|
| Input alphabet | **none** — no text/keyboard screen exists |
| Code length(s) | **none** |
| Checksum / key table | **none** |
| Hard-coded code table | **none** |
| Representable code values | **0** |
| Novel code generated | **none possible** — there is no validator to satisfy |

### 6b.2 Search space checked

| Search | Count | Result |
|---|---:|---|
| `strings -a -n 4` total | 43,820 | complete printable-string set |
| `password` | 0 | no hit |
| `passwd` / `pass code` | 0 / 0 | no hit |
| `cheat` | 0 | no hit |
| `debug` | 0 | no hit |
| `secret` | 0 | no hit |
| `unlock` | 0 | no hit |
| `gallery` / `extras` / `bonus` | 0 / 0 / 0 | no hit |
| `sound test` / `level select` / `warp` / `skip` | 0 / 0 / 0 / 0 | no hit |
| `mot de passe` / `Passwort` / `contraseña` / `código` / `Triche` / `geheim` | 0 each | localized negative |
| UI labels in main bank | 38 + `Credits` | all classified as menu/gameplay/story labels |
| Edge-input call sites (`0x080163D4`) | 68 | indices `{0,1,3,4,5,6,7}`; 5 register-driven |
| Held-input call sites (`0x08016484`) | 51 | indices `{0,1,4,5,6,7}` |
| Calls to unused repeat variant (`0x0801642C`) | 0 | dead/unreferenced |
| `0x03001414` literal references | 53 | shadow-word uses, no sequence counter |
| Select/L/R reads in menu code | 0 | buttons 2/8/9 never requested |

A generic scan for password-like literals (6–12 chars of `A–Z0–9!?`) returns 816 distinct runs, but every inspected candidate is inside binary data (font/curve tables such as `0x397153`, tile IDs, or level object data such as `0x09F4FA`), not a NUL-terminated code string and not referenced by any UI screen. There is no candidate table to test.

### 6b.3 Dynamic button probes

At the title screen, with the menu focused, the following produced **no new screen**:

| Probe | Result |
|---|---|
| Select | no change |
| L | no change |
| R | no change |
| Up / Down | no change (title is horizontal) |
| A+B together | normal Play path (A wins) |
| L+R | no change |
| Select+Start | normal Play path (Start wins) |
| L+R+Start | normal Play path (Start wins) |
| `Up Up Down Down Left Right Left Right B A` | no change; still title |

At the options screen, Select/L/R also produced no change. At the profile and map screens, B returns; no other button opens a hidden screen. This is consistent with the static call-site set: there is no second input grammar to trigger.

### 6b.4 Published codes

| Source | Findings | Classification |
|---|---|---|
| VGChartz (`/game/26218/.../cheats`) | “Total cheats available: 0” | no published cheats |
| GameFAQs cheats page | HTTP 403; web-archive snapshot 404 | unavailable, no native list recovered |
| Almar’s Guides | Master Code, Access All Levels, 99 Crowns, Exit Key, Stop Timer | **CodeBreaker memory-device codes** |
| emucheatz | 99 Crowns, Score, 5× Combo | **CodeBreaker/GameShark memory-device codes** |
| Fan wikis / TCRF | no Babar code page found | no native codes |

The CodeBreaker/GameShark codes are memory writes applied by an external device or emulator cheat engine. They are **not enterable in the game**, are excluded by the stated scope, and are deliberately not reproduced here. There is no in-game screen on which to test them.

### 6b.5 Unlockable surface

| Item | State |
|---|---|
| Level-selector map | observed; a fresh profile shows only `Level 1.1 / Balloon Ride` |
| Profiles | 4 slots, named Babar/Arthur/Flora/Zephir |
| Level definitions | 9 (`level1.xml` … `level9.xml`) |
| Level titles | 9, listed in §6.4 |
| Unlock mechanism | save progression (EEPROM); no button code or password |
| Hidden characters/gallery/sound test | none in the string bank; the four extra character names are story/NPC labels |

### 6b.6 Bounds and rejection

The honest bound is structural: **there is no text-input state to reject a string from.** Every input helper call site is a single-button poll for one of A, B, Start, or an arrow. No sequence-buffer accessor or progress counter is referenced by those helpers or their call sites, and no UI screen compares user-entered text. A password-shaped sequence typed at any menu can only move the fixed cursor; it is never accumulated, hashed, or compared. Likewise, the published CodeBreaker codes have no in-game entry field. That is the rejection proof for this title: the format “password/code” is not representable by the UI at all.

## 7. Validation evidence

| Claim | Evidence type | Evidence |
|---|---|---|
| Identity/hashes/header | **Observed** | `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd -l 0x200` |
| Single GBA header, no multi-game image | **Observed** | Nintendo-logo prefix occurs only at file `0x4` |
| Save hardware is EEPROM | **Observed** | mGBA log `Detected EEPROM savegame`; 512-byte `.sav` |
| Menu tree and item counts | **Observed** | screenshots `title_*`, `options_menu`, `high_scores`, `credits`, `profile_*`, `level_selector`, `pause_menu` |
| 4 profile slots, 3-item sub-menu | **Observed** + **Derived** | screen walk; index clamp `cmp r3,#3; bls` at `0x0800CE94` |
| Key helpers and bit convention | **Derived** + **Observed** | ARM disassembly at `0x080163D4`/`0x08016484`; read-watchpoint hit at `0x080163F4` with `r3=0x04000130`, `r1=0x3FF`, `LR=0x0800CE94` |
| Only A/B/Start/arrows are polled | **Derived** | BL scan: 68 edge + 51 held call sites; indices `{0,1,3,4,5,6,7}` |
| No text/code UI | **Derived** | complete 38+1 label bank; zero password/cheat/debug strings; no keyboard/alphabet/submit labels |
| No native published codes | **Observed** | VGChartz 0; GameFAQs 403; only CodeBreaker lists found |
| Save-based level progression | **Observed** | profile label changes from `Empty` to `Level 1 / Balloon Ride` after entering the level |
| Nine level titles/definitions | **Derived** | string bank `0x083E3E04`+; archive directory `0x080736D4` |

## 8. Unknowns

- **EEPROM layout.** The 512-byte save’s byte-level structure and its per-level unlock bitmask were not decoded. This does not affect the code-system conclusion; it only limits a save-editor description.
- **Exact meaning of the map’s `2` badge.** It is displayed next to the starting node and is probably a crown/child count, but it was not decoded from the level data.
- **CodeBreaker effects.** The published device codes (e.g. “Access All Levels”, “99 Crowns”) were not executed because they are external memory edits, outside the requested in-game/developer-intended scope.
- **Result/level-record screen.** Its labels are identified statically; a full nine-level playthrough was not required to prove that no cheat/code surface exists, and the report does not rely on gameplay completion for any claim.

## 9. Tooling

- mGBA 0.10.5 (SDL), Xvfb `:151`, openbox, `xdotool`, `scrot`, ImageMagick `convert`.
- `arm-none-eabi-objdump` (binutils-arm-none-eabi) for ARM disassembly.
- Python 3 with Capstone 5.0.7 (raw ARM scans), pexpect 4.9.0 (mGBA CLI debugger sessions).
- Scripts and logs in `/tmp/opencode/babar/`:
  - `recon.py`, `recon_out.txt` — string counts and UI label inventory.
  - `calls_summary.py`, `calls.py`, `calls2.py`, `calls3.py` — input-helper BL scans.
  - `scan_io3.py` — key-register access scan.
  - `dbg_session.py`, `memread*.py` — mGBA CLI debugger probes.
  - `shots/`, `crops/` — raw and cropped screenshots.

## 10. Legal note

No ROM, extracted graphics, music, or full game text is redistributed with this report. Only hashes, addresses, short factual UI labels, algorithm descriptions, and analysis screenshots (kept outside the repository) are included.
