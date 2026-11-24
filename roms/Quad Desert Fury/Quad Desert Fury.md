# Quad Desert Fury (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Quad Desert Fury/Quad Desert Fury.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `QUAD DESFURY` |
| Game code | `BQDE` |
| Maker code | `5G` |
| Version / fixed byte | `0x00` / `0x96` |
| Complement / checksum | `0x4C` / `0x0000` (computed complement `0x65`; header non-standard but no patch found — see below) |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock Nintendo branch) |
| MD5 | `e003f4c06ad7f01d50dcdada5075a234` |
| SHA-1 | `70525638035faf22614676bd6fdfb69f03934737` |
| SHA-256 | `9a6887e27a6c41f9011573438bef69c4f885df97e0aa753bb58bed6f721b3923` |

**Embedded-header / patch scan (Phase 0):** a whole-file scan for the 156-byte
Nintendo logo found exactly **one** GBA header, at file `0x0`. This is a single
4 MiB retail image — not the 3-header 2-in-1 pack described in the guide §5.4b.
No appended trainer, no multiboot stub, no scene cracktro: the entry word is the
stock `0xEA00002E`. The non-matching header complement byte is therefore treated
as a header quirk, not evidence of a patch.

## 2. Executive summary

**There is no in-game / developer-intended cheat system in this ROM.** No
password screen, no button-code matcher, no hidden or debug menu, no unlockable
vehicle or track, and no secret content exists on any reachable screen.

The reachable screen graph is completely enumerated (§6b): a title screen, a
2-item main menu (Quick Race / Challenge Mode), a 7-item track selector
(1–7, wrapping), a Challenge Mode explanation screen, the race, and a 3-item
pause menu (Continue / Music on-off / Quit, wrapping). Every item was entered
and every ring bound was proven by wrap-around or by an inert direction key.
The game has no save memory in practice (mGBA creates only a 0-byte `.sav`) and
no vehicle selection at all — all racing is on one ATV with seven track
layouts.

Static analysis found no password alphabet/table, no key-mask sequence table,
no validator/checksum loop, no unlock flag, and no debug-named class or string.
The game's UI is baked into bitmap-mode (mode 3) screen art: the visible labels
`SELECT TRACK`, `PAUSE`, `QUIT`, `QUICK RACE`, `CHALLENGE MODE` and
`Press START` occur **nowhere** in the 4 MiB in ASCII, case-shifted ASCII,
UTF-16LE or UTF-16BE — there is no font/tile-indexed text bank to decode. The
only meaningful ASCII is a C++ RTTI / task-name bank at `0x0810BD8–0x0810E10`
(`7SysTask`, `9SysSprite`, `7AtvGame`, `3Atv`, `7Vehicle`, `8ThSprite`,
`TRACK TIMES`, plus standard C++ runtime names). No class named Password,
Cheat, Debug, Secret or Unlock exists.

Published "cheats" for this title are absent: 3rd party cheat indexes explicitly lists
none; the only hits are GameShark/CodeBreaker `.cht` database entries
("1197 – Quad Desert Fury (US) Translated Cheats", "2333 – 2 Games in 1 – Quad
Desert Fury + Monster Trucks (EU)"), which are external memory-edit codes and
out of scope. A widely published "Frog, Frog, Helmet, …" ATV password belongs
to the different game *ATV Quad Power Racing* and is a false positive.

## 3. How to reproduce

* Emulator: mGBA SDL (`mgba`), `SDL_AUDIODRIVER=dummy`, on `Xvfb :319` at
  `1024x768x24` with `openbox`; `mgba -3 <rom>` gives a 720×480 client area
  captured with `import -window <id>`.
* Default mGBA SDL keymap: A = `x`, B = `z`, L = `a`, R = `s`,
  Start = `Return`, Select = `BackSpace`, D-pad = arrow keys. Holds of
  100–200 ms with ~300–400 ms gaps gave reliable one-step menu movement
  (shorter holds occasionally double-stepped).
* Exact menu path (all verified on screen and by savestate RAM reads):
  1. Title `Press START` → **Return** → main menu.
  2. Main menu: **Right/Left** selects Quick Race / Challenge Mode;
     **Down** is inert (proves 2 items).
  3. Quick Race → **x (A)** → `SELECT TRACK`; **Right/Left** cycles
     `1..7` and `7 → 1` (proves 7 tracks); **x** starts the race;
     **z (B)** backs out.
  4. Challenge Mode → **x** → "Win a race on each track to advance…"
     explanation → **x** → race on track 1.
  5. In race: **Return** → PAUSE (`Continue` / `Music on` / `Quit`);
     **Down** cycles and wraps `Quit → Continue` (proves 3 items);
     **x** activates. **Quit** returns to the title.
* Button-code probes on the title screen (with savestates before/after):
  `L+R+A+B`, `L+R+Start`, and the full Konami sequence
  `Up Up Down Down Left Right Left Right B A`. None produced a new screen or a
  persistent RAM flag; `L+R+Start` simply entered the normal main menu.
* Codes tested: none exist to enter (no entry field on any screen).
* mGBA hotkeys: `Shift+F1…F9` save states; states were written beside the ROM
  and removed during cleanup.

## 4. Address map

File offset = ROM address − `0x08000000` (flat 4 MiB image).

| Item | ROM address | File offset | Evidence |
|---|---|---|---|
| Entry point / crt0 | `0x08000000`–`0x08000100` | `0x0`–`0x100` | Observed bytes; `b 0x080000C0` |
| `main` (Thumb) | `0x08001110` | `0x1110` | Observed: crt0 literal `0x08001111` at header `+0x1C8` (file `0x1C8`); disassembled `push {r4,lr}` then task init and `bl 0x08001194` |
| Low-level task/DMA system | `0x08000970`, `0x0800A9C`, `0x0800AC8`, `0x0800B18`, `0x0800B30`, `0x0800B4C` | `0x970`+ | Observed Thumb disassembly; uses globals `0x030000A0` (counter) and `0x030000AC` (system flag), task slots indexed 0..99 (`cmp #0x64`) |
| Key-input register literals | `0x0800A49C`, `0x0800A61C`, `0x0800A9E8`, `0x0800F4B4`, `0x0800FFDC`, `0x0801008C`, `0x080102A4` | `0xA49C`+ | Observed 4-byte literal `0x04000130` (KEYINPUT) in literal pools; readers are ordinary input polling, no sequence matcher found |
| RTTI / task-name bank | `0x0810BD8`–`0x0810E10` | `0x10BD8`–`0x10E10` | Observed: `7SysTask`, `9SysSprite`, `TRACK TIMES`, `7AtvGame`, `3Atv`, `7Vehicle`, `8ThSprite`, C++ runtime names. No 32-bit xref to `TRACK TIMES` at `0x0810BF4` (or to the class-name strings) anywhere in the ROM |

RAM (from mGBA `.ss*` states decompressed per guide §16.13: `gbAs` zlib chunk →
397,312-byte raw state; IWRAM at raw `0x19000`, EWRAM at `0x21000`):

| RAM | Meaning | Values observed | Confidence |
|---|---|---|---|
| `0x03007AF8` | menu-selection state (IWRAM) | `6` = Quick Race, `3` = Challenge Mode; `7` = track-select 1, `0` = track-select 2, `248` = race, `155` = pause | Observed across 9 savestates; semantics of the numeric encoding not proven |
| `0x030000AC` | engine system flag (not a cheat flag) | toggles 0/1 with frame/task activity | Observed; disassembled at `0x08000970`/`0x0800A6E` |
| `0x030000A0` | engine task counter | increments continuously | Observed; disassembled at `0x0800A70` |

The menu selector was verified with an alternating-state test: four states
captured in the order Quick / Challenge / Quick / Challenge yielded
`0x03007AF8 = 6,3,6,3` while every other IWRAM/EWRAM byte either stayed fixed
or changed non-alternating.

## 5. Algorithm

Not applicable — no password, checksum, encoder/decoder or button-code
validator exists. The "algorithm" of interest is the menu ring logic, which is
plain bounded index arithmetic (verified by wrap-around in §6b), e.g. track
index `i = (i ± 1) mod 7`, main-menu index `i = (i ± 1) mod 2`, pause index
`i = (i ± 1) mod 3`. No hidden dispatch branch was found: every observed menu
index has a visible label and a working action.

## 6. Tables

| Table / set | Address or source | Contents | Count |
|---|---|---|---|
| Main menu | screen enumeration + RAM `0x03007AF8` | Quick Race, Challenge Mode | **2** (exhaustive; Down inert, Right/Left wrap) |
| Track select | screen enumeration | 1, 2, 3, 4, 5, 6, 7 | **7** (exhaustive; `7 → 1` wrap) |
| Pause menu | screen enumeration | Continue, Music on/off, Quit | **3** (exhaustive; `Quit → Continue` wrap) |
| Vehicle roster | none | one ATV only; no selection screen reachable | **1** |
| Save data | none | mGBA produced a 0-byte `.sav`; progress explicitly not saved | **0** |
| Password alphabet / code table | none found | searches for `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `0123456789A…Z`, the Pirates alphabet and the Car Battler Joe alphabet all returned zero hits | **0** |
| Button-code mask table | none found | scan of all `0x400000/2` u16 words for runs of ≥4 low-population key masks: 1299 runs, all inside code or graphics data with no validator reference; Konami 3-press prefix `40 00 40 00 80 00` absent | **0** |
| RTTI / task names | `0x0810BD8`–`0x0810E10` | 7SysTask, 9SysSprite, TRACK TIMES, 7AtvGame, 3Atv, 7Vehicle, 8ThSprite, bad_alloc, `__class_type_info`, … | no cheat/debug class |

## 6b. Enumeration

**Scope of the space.** Because no code/password system exists, the
enumerated space is the complete reachable UI state space, plus the static
search spaces that were checked for a hidden system:

* **Reachable screens (7 distinct states, all entered and RAM-saved):**
  title; main menu; track select; Challenge Mode intro; race; pause.
  (The two splash/logo screens are non-interactive startup art, not menus.)
  Savestates `ss1`–`ss9` were captured at these screens and their raw RAM
  compared; `0x03007AF8` and the surrounding IWRAM stack region differ by
  screen, and no savestate anywhere contained a text-entry buffer, a code
  alphabet, or a code-validity flag.
* **Menu ring sizes are exact, not assumed:** main menu 2 (Down inert, Left/
  Right exchange the two labels); track select 7 (Right at 7 wraps to 1 —
  no eighth/hidden track); pause 3 (Down at Quit wraps to Continue — no
  fourth/hidden option). These are the "bounds proven by rejection" for this
  title: an out-of-range index is either inert or wraps, never selects a
  hidden entry.
* **Button-code space checked:** all single/combination active-high key masks
  `0x001..0x3FF` were considered as u16 words; a full-ROM scan found 1299
  runs of ≥4 plausible consecutive mask words, every one of them in code or
  compressed graphics with no PC-relative reference from an input handler.
  The two canonical prefixes searched explicitly (Konami `0x0040,0x0040,
  0x0080`; `L+R+Start` = `0x0308`) had no meaningful table hit. Dynamically,
  `L+R+A+B`, `L+R+Start`, and the full Konami sequence were pressed on the
  title screen; RAM diffs showed only normal animation/timer churn and no new
  screen or latch.
* **Password space checked:** zero candidate strings in ASCII, `+0x20`
  case-shifted ASCII, UTF-16LE or UTF-16BE for `PASSWORD`, `CHEAT`, `SECRET`,
  `UNLOCK`, `DEBUG`, `ENTER`, `SELECT TRACK`, `QUICK RACE`, `CHALLENGE`,
  `PAUSE`, `MUSIC`, `QUIT`, `CONTINUE`, `VEHICLE`; zero occurrences of four
  known password alphabets; no on-screen keyboard or text-entry widget on
  any of the screens above.
* **Novel code:** none can be minted, because no code format, validator or
  unlockable state exists. Per guide §0.2's negative-result clause, the
  absence is bounded by the complete screen enumeration above and by the
  explicit search spaces/counts in this section — not by an untested guess.

## 7. Validation evidence

* **Observed** (emulator screenshots, saved in `/tmp/quaddesert/`):
  title, main menu (both selections), track select (1 and 7 and wrap to 1),
  Challenge Mode intro, race HUD, pause menu (all three selections), and the
  post-probe title screen. Every button-code probe left the game on the same
  screen.
* **Observed** (RAM): 9 mGBA savestates decompressed and compared;
  `0x03007AF8` alternated `6,3,6,3` across Quick/Challenge/Quick/Challenge;
  no savestate contained a password buffer or cheat flag.
* **Derived** (disassembly): `main` at `0x08001110`; task/DMA globals
  `0x030000A0`/`0x030000AC`; seven KEYINPUT literal sites; no xref to the
  `TRACK TIMES` string or any cheat-named RTTI class.
* **Inferred** (lower confidence): the numeric encoding of `0x03007AF8`
  (6/3/7/0/248/155) is a per-screen task/stack value, not proven to be the
  canonical screen enum. This does not affect any conclusion because screen
  identity is established directly by screenshots.
* All fetched web pages were treated strictly as data. No instructions found
  in fetched content or ROM strings were followed.

## 8. Unknowns

* The 3rd party cheat index claim of a "Time Trial" mode is not borne out by this ROM's
  UI: only Quick Race and Challenge Mode are selectable, and no Time Trial
  entry appears after selecting a track. Treated as an article error for this
  SKU, not an undiscovered screen.
* The semantic meaning of the numbers held at `0x03007AF8` was not pinned to a
  named enum (it is a stack-resident task value).
* A results/records screen after completing a race was not reached (finishing
  a 3-lap race was not automated). The `TRACK TIMES` task-name string has no
  ROM xref, so no hidden screen is inferred from it; this remains the only
  unexercised in-game event. Given the complete menu enumeration and the
  absence of any save data, this cannot gate a code system.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings` for Phase 0/1.
* Python 3 + `capstone` 5.0.7 for literal scans, Thumb LDR/BL scans and the
  u16 key-mask/password-alphabet scans (`static1.py`, `static2.py`,
  `static3.py` in `/tmp/quaddesert/`).
* `arm-none-eabi-objdump -M force-thumb --adjust-vma=0x08000000` for manual
  disassembly of `main` (file `0x1110`) and the low-ROM task system.
* `xdotool` (XTEST keydown/keyup to the focused mGBA window) and
  `import -window` for input and screenshots.
* `/tmp/quaddesert/ss.py` — mGBA `.ss*` `gbAs` zlib decompressor and
  IWRAM/EWRAM reader (guide §16.13).
* `/tmp/quaddesert/helper.py` — reproducible input/screenshot helper.

**Legal note:** no ROM image, extracted graphics, music or game text is
reproduced here; only hashes, addresses, instruction snippets and analysis
tools are published.
