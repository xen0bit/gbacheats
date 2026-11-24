# VeggieTales: LarryBoy and the Bad Apple (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `VeggieTales: LarryBoy and the Bad Apple.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `BAD APPLE` |
| Game code | `BZTE4Z` (Rev. 00) |
| Maker code | `4Z` |
| Version / complement | `0x00` / `0x35` |
| Header checksum | `0x0000` |
| Entry word | `0xEA00003E` → `0x08000100` (stock crt0, not a scene cracktro) |
| MD5 | `4462ba1869564537610250d522287815` |
| SHA-1 | `3f6f229d719a2e533aba538763802a64c2025bd9` |
| SHA-256 | `9bb14a7ea8e89bf89a29989f655d30b81be532b0cc6d3bfbd593af28efc7284e` |

## 2. Executive summary

**No developer-intended password, button-code, or hidden debug menu exists in this ROM.**
This is a children's platformer with EEPROM profiles; the only text-entry field is a
64-symbol **profile-name keyboard**, not a password field. The only unlockable content
is progression-gated world/mission selection: the ROM contains 8 world labels and 9
mission labels, but a fresh profile exposes exactly 1 of each. All reachable screens
were walked in mGBA and every menu item was enumerated (§6b). Static searches returned
zero hits for every cheat-related keyword, zero password-style alphabets, zero
key-mask code tables, and no validator that compares user text to a constant.
Only cheat-device (Action Replay MAX) codes are published for this title; those are
out of scope and are not implemented by the game.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:318`, default keymap
  (A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, arrows).
* Boot → legal screen (A) → title (`PRESS START`). Start → `Profiles`
  (`Create Profile` / `Load Profile`) → create a slot → on-screen keyboard:
  rows are per-line rings (`A..M`, `N..Z`, `a..m`, `n..z`, `0..9`, backspace, DONE);
  use **DOWN** to change row, not 51 RIGHT presses. Enter a name → `Difficulty`
  (Beginner/Normal/Expert) → main menu (`Select World`, `Options`, `Credits`).
* `Select World` → `Bumblyburg Tower` → `Mission` → `Level 1` → gameplay
  (tutorial "Press START to skip", then "Ready!" needs A) → Start → pause
  (`Continue`, `Retry`, `Exit level`).
* `Options` = Sound FX, Music, Difficulty. `Credits` is a scroll-only screen.
* Button probes: 12 chords/sequences on the pause screen and 9 on the title screen
  (including `L+R`, `L+R+Start`, Start+Select+A+B, and the Konami sequence). None
  opened a new screen; Start+Select+A+B only performed a normal console reset.
* All emulator artifacts were removed after the run (§9).

## 4. Address map

| Item | File offset | ROM address | Notes |
|---|---:|---|---|
| World-label pointer table | `0x035928` | `0x08035928` | 8 `u32` → ASCII labels |
| Mission-label pointer table | `0x0359FC` | `0x080359FC` | 9 `u32` → `Level 1`…`Level 9` |
| Difficulty-label pointer table | `0x035A68` | `0x08035A68` | 3 `u32` → Beginner/Normal/Expert |
| Numeric mission/world tables | `0x0359CC`–`0x035B2C` | `0x080359CC`–`0x08035B2C` | level-index arrays |
| Map-name pointers | `0x035B60` | `0x08035B60` | CandyCave … End (debug-looking, used by game) |
| Main menu/state machine | `0x014090` | `0x08014090` | 16-case switch at `0x08014310` |
| Generic menu renderer | `0x01C2C2` | `0x0801C2C2` | called with `0x080148F0` menu struct |
| State-3 name entry | `0x014400` | `0x08014400` | builds 6-char space-padded name buffer |
| Menu struct for Select World | `0x0148F0` | `0x080148F0` | `Difficulty`, `Select World`, `Mission` + RAM pointers |
| EEPROM_V124 string | `0x0383C0` | `0x080383C0` | 512-byte EEPROM profile store |
| Profile name in IWRAM | — | `0x030067DC` | 8 bytes (`"0      "` observed) |
| Profile data mirror | — | `0x030067E4`–`0x030067EB` | 8 bytes, byte-reversed vs `.sav[8..15]` |
| World-label RAM copy | — | `0x03006038` | 8 pointers, matches ROM table |
| World-list count fields | — | `0x0300622C` / `0x03006230` | `7` / `8` in fresh-profile savestate |

## 5. Algorithm

No password/serial algorithm exists. The relevant algorithm is ordinary menu state
selection: the 16-case dispatcher at `0x08014310` transitions between profile,
difficulty, world, mission and gameplay states, and a progression field in the
EEPROM profile filters the 8/9 ROM label tables down to the entries shown. No
checksum, XOR key, substitution alphabet, or comparison against user-entered text
was found.

## 6. Tables

* **Profile keyboard alphabet (64 symbols, observed on screen):** `A..M`, `N..Z`,
  `a..m`, `n..z`, `0..9`, backspace, DONE. It is a name-entry field: the entered
  string becomes the profile label shown in `Load Profile` and is written to
  `.sav[0..7]`. Per §16.2b it is *not* a password field.
* **World labels (8):** Bumblyburg Tower, Bumblyburg Funhouse, Larry Song 1,
  Virtual HandyPod, Four Seasonings Hotel, Larry Song 2, Candy Cave,
  Freestyle Keyboard.
* **Mission labels (9):** Level 1 … Level 9.
* **Difficulty labels (3):** Beginner, Normal, Expert.
* **Save record (EEPROM, 512 B, first 16 used):** `u8[8] name`, 8 data bytes;
  remaining 496 bytes are `0xFF` on a fresh card.

## 6b. Enumeration

**Code/password space: empty (0 codes). Bounded negative, proven as follows.**

1. **Published-code recon (web):** 3rd party cheat indexes are 403; Brave/Google/DDG searches and
   3rd party cheat indexes were fetched as data. No in-game password/button code is published.
   The only results are two **Action Replay MAX** device codes
   (`UYGJ-AJV6-7B85K`, `WJW8-1297-B3VBF`) — cheat-device codes, explicitly out of
   scope and not part of the game.
2. **String/keyword counts over all 4,194,304 bytes** (case-insensitive raw scan):
   `debug`=0, `cheat`=0, `password`=0, `secret`=0, `code`=0, `warp`=0,
   `unlock`=0, `level select`=0, `test mode`=0. `service`=6 (5 duplicated
   dialogue lines + 1 credits job title). The visible UI is ASCII (menu labels,
   credits, mission titles), so a font/tile-only debug label would not explain
   these zeros; the text bank at `0x358FC`–`0x383C0` was decoded directly.
3. **Alphabet/table scan:** 27,438 ASCII strings total; the only long
   `[A-Z0-9]` runs ≥16 chars are audio/compression curve tables
   (e.g. `0x2FBC1 ACEGIKLNPQSTVWYZ`, `0x298C0 0123456789ABCDEF`). No
   password alphabet, code table, or generator/decoder pair exists.
4. **Button-code mask scan:** 0 runs of ≥5 consecutive single-bit active-high
   key masks in the code region (file `<0x40000`); 2 active-low runs, both
   repeated constants (`0x1FF`×5, `0x3FD,0x3FD,0x3FE,0x3FE,0x3FE`) in data, not
   code sequences. Literal Konami/AB-Start patterns as `u16`/`u8`/raw-active-low:
   0 code-region hits; the 7 `u16` `Up,Up,Down,Down` hits are inside compressed
   graphics/audio at `0x1EDFEC`+.
5. **Screen/menu enumeration (all reachable screens, item counts):**
   Legal 0 items; title 0; Profiles 2; Difficulty 3; main menu 3;
   Select World **8 labels / 1 visible**; Mission **9 labels / 1 visible**;
   Options 3; Pause 3; Credits 0; gameplay HUD 0. No unlabelled selector slots:
   DOWN five times on Pause stopped at `Exit level` (index 2).
6. **Button probes:** 21 total (12 pause + 9 title), including all conventional
   secret sequences; 0 new screens.
7. **Unlockables (the only gated content):** 8 worlds and 9 missions are
   advertised in ROM but a fresh profile shows 1 of each. The gate is profile
   progression in EEPROM (profile struct at `0x030067DC`, data mirror at
   `0x030067E4`), not a code: no input path compares a typed/entered value to
   these fields, and no button-code table reaches them. Debugger writes of
   `0xFF` to candidate profile bytes did not change the visible list without a
   profile reload, consistent with a list built at profile load. This is
   reported as a **gated feature** (§16.3 case 4), not a code system.
8. **Novel code / rejection bounds:** not applicable — there is no code system to
   mint a value for. The negative is bounded by the counts above (0 keywords,
   0 code tables, 0 validators, 8/9 gated labels, 21 button probes, 10 screens
   walked), which is the §0.2 requirement for a no-code ROM.

## 7. Validation evidence

* **Observed (emulator):** every screen and menu count in §6b; profile-name entry
  and its reappearance in `Load Profile`; the single visible world/mission;
  21 button probes; normal reset on Start+Select+A+B.
* **Observed (RAM):** IWRAM `0x03006038` holds all 8 world-name pointers;
  `0x0300622C`=`7`, `0x03006230`=`8`; profile name at `0x030067DC`;
  KEYINPUT register confirmed live (`0x03EF` while Right held) so XTEST input
  was reaching the game.
* **Derived (static):** pointer tables at `0x08035928`/`0x08035AFC`/`0x08035A68`;
  16-case menu dispatcher at `0x08014310`; menu renderer at `0x0801C2C2`;
  name-entry state at `0x08014400`; no `strcmp`-style validator against user
  text anywhere in the reachable code paths.
* **Inferred:** the exact EEPROM byte/bit that stores the world/mission unlock
  count (profile bytes at `0x030067E4` look checksum-like); the specific
  completion event that sets it. No claim is made about its exact offset.

## 8. Unknowns

* Exact save bitfield layout for world/mission unlocks (not needed to establish
  that no code reaches it).
* `Minigames` is present in the text bank (`0x37853`) but was not reachable in a
  fresh profile; it is likely another progression-gated menu.
* The 18 music sheets mentioned on 3rd party cheat indexes were not enumerated in-game;
  no code-related strings for them exist in the ROM.

## 9. Tooling

`strings`, `grep`, `xxd`, Python 3 regex/struct scanners (`scans.py`, `xref.py`,
`ssdump.py`), `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, mGBA 0.10.5
under Xvfb `:318` + openbox, mGBA CLI debugger (`-d`) for RAM reads/writes,
`gdb-multiarch` + mGBA GDB stub, `xdotool` XTEST input, `scrot` screenshots,
Brave web search (read-only). All scripts and screenshots are under
`/tmp/larryboy/`.

**Cleanup (confirmed):** display `:318` (Xvfb PID 767629) and openbox (767633)
stopped; every mGBA instance and debugger helper started for this job killed by
PID number; `pgrep -x mgba | grep LarryBoy` and `pgrep -x Xvfb | grep :318` both
empty. The ROM folder contains only the `.gba` — the generated `.sav` and `.ss1`
–`.ss3` savestates were deleted. Other agents' displays and emulators were not
touched.

## 10. Legal note

Findings, hashes, addresses and tool scripts are published; no ROM bytes,
copyrighted graphics, music, or extracted text assets are redistributed here.
