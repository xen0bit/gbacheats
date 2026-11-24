# Tony Hawk's Pro Skater 4 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tony Hawk's Pro Skater 4.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `TONY HAWK 4!` |
| Game code | `AT6E` (USA) |
| Maker code | `52` |
| Version | `0x00` |
| Header checksum | `0x0000` (rebuilt-header artifact; complement byte `0xD0`) |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0` (not a cracktro) |
| MD5 | `e78e1f6c6fbe9a614e0406802fc6a7fd` |
| SHA-1 | `f4ba0be44899eb8d52869120fbbc4f46e2a3c668` |
| SHA-256 | `29d60b5b066d01963ec165333e8ed1f514a0bd697a9c6f06704024eccd7ff139` |

Boot splash identifies **Vicarious Visions Inc.** (observed in mGBA, `s0.png`–`s2.png`),
and the audio-engine banner `Shin'en Multimedia. Code: B.Wodok` is at file `0x7711C8` —
the same engine family as the sibling THPS2/THPS3 GBA SKUs, but all findings below were
derived from this image only.

## 2. Executive summary

**There is no typed cheat-code / password validator in this GBA image.** Every
developer-intended cheat is a binary unlock flag purchased with in-game cash in
**Skate Shop → Checklists → Secrets**, which is itself gated on completing a Pro
Challenge for that skater (guide §16.3 case 4). A fresh save shows an empty
Secrets list and only **8** OPTIONS rows (no `CHEATS` row); a completed/loaded
career is required before any cheat can be toggled.

The widely circulated `WATCH_ME_EXPLODE` / `MOON$HOT` / `FBIAGENT` / `SSBSTS`
strings are **console (PS2/PC/Xbox) cheats**. They are absent from this GBA ROM
in every encoding tested (§6b). The GBA-specific published sources
(GameFAQs GBA cheats page, Planet Tony Hawk GBA page, KirbyRockz GBA guide)
list only cash/Pro-Challenge unlockables and no code-entry screen; the SuperCheats
"GBA" page that repeats `Watch_me_xplode` is cross-platform contamination
(guide §16.7/16.11).

The only on-screen text-entry surface is the **save-name / Create-a-Skater name**
keyboard (40 glyphs: `0-9 A-Z -` plus three control glyphs). Its consumer is the
name field, not a comparison routine. The 14 cheat names exist in the ROM
(`0x080BE930`–`0x080BEA04`, string IDs 166–179) together with the flavour string
`new cheat unlocked` (`0x080BEED0`), but no validator, no accepted/rejected
message strings, no hard-coded code table and no button-mask code table were
found.

**Finding: bounded negative (no code system) + fully enumerated 14-flag cheat
state.** Confidence: high for "no typed code / no code-entry screen", high for
the 14-entry cheat set and the gated Secrets surface; the exact cash thresholds
are published (§3) but were not exercised in-game.

## 3. How to reproduce

* mGBA 0.10.5 under Xvfb `:315` + openbox, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
  Keymap verified by behaviour: D-pad = arrow keys, **A = `x`**, **B = `z`**,
  **L = `a`**, **Start = `Return`**. Menus in this build are committed with
  **Start** (`Return`), not A (A selects only in submenus); D-pad holds of
  60 ms move exactly one row (150 ms double-steps — guide §16.2).
* The CLI debugger (`mgba -3 -d game.gba`) was driven through a FIFO→pty bridge
  (`/tmp/thps4/dbg_bridge.py`); commands need a `\r` terminator and
  `Ctrl+C` to break into a running core.
* Screen path (all screens screenshotted in `/tmp/thps4/`):
  1. Boot → Vicarious Visions splash (`s2.png`).
  2. `SELECT SAVE SLOT`, 4×`NEW` (`title.png`).
  3. `ENTER SAVE NAME` keyboard, default `Player` (`menu1.png`); A → `SAVING`
     (`menu2.png`) → "to save your progress …" (`menu3.png`) → A.
  4. Main menu: `CAREER / TONY HAWK / GO COLLAPSE / SKATE SHOP / OPTIONS`,
     with `active game: Player` (`menu4.png`).
  5. OPTIONS: `SOUND / CONTROLS / BRIGHTNESS / BLOOD / NORMAL MODE / SAVE GAMES /
     RESET SCORES / CREDITS` — exactly **8** rows, wraps 8→1; **no CHEATS row**
     (`options.png`, `opts_down8.png`, `opts_down1.png`).
  6. Skate Shop: `CHANGE DECK / CHANGE OUTFIT / EDIT SPECIALS / EDIT STATS /
     CAREER BOARD / SCORE BOARD / VIEW MOVIES / CHECKLISTS` (`skateshop.png`).
  7. Checklists → GAPS and SECRETS tabs; with the fresh save both are empty
     (`checklists.png`, `checklists_secrets.png`). This is the cheat-purchase
     surface and it is gated.
  8. Start on `TONY HAWK` → free-skate/tutorial → in-game pause menu
     `CONTINUE / VIEW GOALS / VIEW TRICKS / SKATE SHOP / MAIN MENU` — no CHEATS
     row, unlike the console SKUs (`pause_menu.png`, `tonyhawk_start.png`).
* Published-code reconciliation (web recon, treated as data):
  * GameFAQs **GBA** page: only "Misc. Unlockables GBA" (Pro Challenge, movies,
    The Zone, Turbo Mode, secret characters) and "Unlockables GBA" — no typed codes.
  * Planet Tony Hawk **GBA** page: "Cheats … purchased … after you've completed
    a Pro Challenge … Skate Shop under Checklists … hit A … yellow circle".
  * KirbyRockz GBA guide §9–10: purchasable Stud Mode, Perfect Rail/Manual,
    Always Special, Moon Physics, Jet Pack, Matrix Mode, Alt Outfit; Secrets
    menu via Skate Shop → Checklists, gated on a Pro Challenge without Kid Mode.
  * `WATCH_ME_EXPLODE`, `doasuper`, `nospoon`, `superfly`, `MULLENPOWER`,
    `SSBSTS`, `MOON$HOT`, `FBIAGENT`, `I'MYELLOW`, `BELIKEERIC` are labelled
    PS2/PC/Xbox on every source that attributes them to a platform.

## 4. Address map

| Address | Size | Meaning | Evidence |
|---|---:|---|---|
| `0x08000000` | 4 | Entry branch `0xEA00002E` | Derived (header bytes) |
| `0x080AF150`/`0x080AF154` | 4 each | Text-entry constants `0x20`, `0x3F` (length bounds) | Derived (literals at `0x08015014`, `0x080152EC`) |
| `0x080AF158` | 18 | `Min. Length is %d` | Derived (ASCII; literal pointer `0x080152E8`) |
| `0x080AF16C` | 40 | On-screen keyboard alphabet `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-` + glyph bytes `A2 A3 A1` | Derived (ASCII; literal pointers `0x08014FC4`, `0x0801539C`) |
| `0x08014F78` | ~150 | Keyboard key handler: index ≤ 36 → `alphabet[index]` written into entry buffer | Derived (Thumb disassembly) |
| `0x08015308`–`0x08015398` | ~144 | Draws 40 keyboard glyphs (loop `r6=0..39`) | Derived (Thumb disassembly) |
| `0x080BE2D8` | 7 | UI string `Options` | Derived |
| `0x080BE3EC` | 6 | UI string `Cheats` | Derived (pointer `0x080C0FE8`) |
| `0x080BEA20` | 15 | UI string `select save slot` | Derived |
| `0x080BE930`–`0x080BEA04` | 14 strings | Cheat names: stud mode, perfect rail balance, always special, perfect manual balance, moon physics, jet pack mode, matrix mode, alt outfit, secret char 1–4, secret level, turbo mode | Derived (ASCII + pointer table `0x080C11B0`–`0x080C11E4`) |
| `0x080BEED0` | 17 | Flavour string `new cheat unlocked` | Derived (pointer `0x080C13D4`) |
| `0x080C0F18` | 471×4 | Global string-pointer table; "Cheats" = ID 52, cheat names = IDs 166–179 | Derived (contiguous pointer run) |
| `0x080AF190` | 4 | Alphabet tail `- A2 A3 A1` (control glyphs) | Derived |
| `0x02006550`… | 2×N | EWRAM identity table of string IDs loaded at boot | Observed (debugger `x/1`) |
| `0x04000130` | 2 | KEYINPUT (active low) | Derived (standard GBA; keymap confirmed behaviourally) |

**Negative search map** (all over the full 8 MiB): no accepted/rejected code
strings, no password table, no code validator, no button-mask code table, no
debug-menu entry strings (only `Developed by Vicarious Visions, Inc.` and a
credit-bank line `{VP Product Development:}`).

## 5. Algorithm

There is no validator to reimplement. The cheat state machine is:

```
career progress / cash earned in levels
    -> Skate Shop -> Checklists -> Secrets  (gated: requires Pro Challenge)
    -> purchase a cheat (14 fixed names, IDs 166..179)
    -> per-cheat binary enable flag in the save/EWRAM record
    -> "new cheat unlocked" flavour string 0x080BEED0 on acquisition
    -> Secrets tab shows the owned cheat; A toggles it (yellow circle per guide)
```

The save record is flash-backed; a fresh slot writes `game.sav` (8,192 bytes) whose
header contains the slot name (we observed `K4SPH` + reversed `TreyalP` for the
name `Player`). No field of that record is ever compared against user text: the
only text-entry consumers are the save-name and Create-a-Skater name fields.

## 6. Tables

**Cheat-name table** (ROM `0x080BE930`, pointer table `0x080C11B0`, IDs 166–179):

| # | ID | String | Published GBA acquisition |
|---:|---:|---|---|
| 0 | 166 | `stud mode` | $240 in Checklists after Pro Challenge |
| 1 | 167 | `perfect rail balance` | $240 |
| 2 | 168 | `always special` | $240 |
| 3 | 169 | `perfect manual balance` | $240 |
| 4 | 170 | `moon physics` | $40 |
| 5 | 171 | `jet pack mode` | $40 |
| 6 | 172 | `matrix mode` | $40 |
| 7 | 173 | `alt outfit` | $40 |
| 8 | 174 | `secret char 1` | 3 Pro Challenges (Mindy) |
| 9 | 175 | `secret char 2` | 3 Pro Challenges (Frycook) |
| 10 | 176 | `secret char 3` | 3 Pro Challenges (Momo) |
| 11 | 177 | `secret char 4` | 3 Pro Challenges (Roger) |
| 12 | 178 | `secret level` | collect all 90 hidden packages (The Zone) |
| 13 | 179 | `turbo mode` | all gaps except The Zone |

Acquisition thresholds are published (Planet Tony Hawk GBA / KirbyRockz), not
verified in-emulator; the names, order, gated surface and absence of a code-entry
screen are **observed/derived** from this ROM.

**On-screen keyboard alphabet** (`0x080AF16C`, 40 entries):
`0 1 2 3 4 5 6 7 8 9 A B C D E F G H I J K L M N O P Q R S T U V W X Y Z - A2 A3 A1`
(the last three are the left-arrow, right-arrow and confirm glyphs shown in
`menu1.png`; the handler at `0x08014F78` only accepts indices 0–36).

## 6b. Enumeration

**Space definition.** Typed-code space: **empty** — no code-entry surface, no
alphabet-to-code mapping, no checksum, no validator, no accepted/rejected strings.
The only developer-intended cheat space is **14 binary unlock flags** owned per
career save: 2¹⁴ = 16,384 by-construction configurations, reached by purchase and
Pro-Challenge completion, not by typing. No code is "representable" beyond those
14 fixed acquisitions, so there is no novel code to mint; the deliverable here is
a bounded negative (guide §0.2 case 5).

**Published-code sweep (counts).** 37 distinct published code strings from all
platforms of THPS4 (including the GBA-mislabelled `Watch_me_xplode`) × up to 8
encodings — ASCII, lowercase, uppercase, UTF-16LE, UTF-16BE, `+0x20`, `-0x20`,
XOR `0xFF` — = **288 pattern searches over 8,388,608 bytes ≈ 2.42×10⁹ byte-position
comparisons**. Result: **6 apparent hits**, all for `ssbsts` in the `-0x20`
encoding at `0x084C077E`, `0x084C311E`, `0x084C54DE`. Dumping the bytes shows the
pattern `33 33 22 33 34 33` (ASCII `33"343`) inside level/geometry data — a
coincidence, not a code string. **All 37 published codes are absent from the GBA
image in every encoding tested.**

**Text-bank sweep (counts).** `strings -t x -n 4` yields **98,701** strings.
Keyword filter `password|cheat|code|secret|debug|unlock|invalid|wrong|correct|
enter|menu|skater|level select` returned only UI/flavour text: `Cheats`, `Secrets`,
`new cheat unlocked`, `new level unlocked:`, `You've unlocked a secret character!`,
`secret char 1..4`, `secret level`, `turbo mode`, plus `[Codename Cracksmith]` and
`[Cheat Codes Bring...]` (career-goal names at `0x080993E4`/`0x08099478`) and the
audio banner. **No acceptance/rejection prompt, no code table, no debug menu.**
The visible UI text was matched to this ASCII bank (e.g. `select save slot`
`0x080BEA20` ↔ `title.png`; `Cheats` `0x080BE3EC` ↔ options string table), so a
"no text" false negative (guide §11) is excluded: the game's text *is* ASCII in
ROM and was decoded before the negative was asserted.

**Button-code sweep (counts).** Generic active-high mask scan (`A=1,B=2,
Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`) over
every `u16` alignment: **12,491** runs of ≥4 plausible mask values (over-approximation;
most are Thumb code/data such as the recurring `0x0200` L-modifier). No published
GBA button sequence exists for this SKU to match against, and no run forms a
valid 5–14-press sequence with a terminating dispatch. Byte-per-press scan:
176,665 candidate runs — likewise noise, no code table.

**Novel input and rejection bound.** An undocumented 10-press combination
`B,B,Up,Up,Start,B,Left,Down,Start,A` (A=`x`, B=`z`, Start=`Return`) was entered
at the main menu with 60–80 ms holds (`novel_seq_after.png`). It launched the
highlighted `AMATEUR TOUR` as ordinary Start presses do and produced **no**
`new cheat unlocked` message, no new row in OPTIONS (still 8 rows,
`options_after_novel.png` context) and no populated Secrets tab. Separately,
arbitrary text typed into the only text-entry surface (the save-name keyboard,
`menu1.png`) changed only the slot name (`K4SPH…TreyalP` in `game.sav`) and never
the cheat list. Thus both candidate input paths were exercised and rejected:
there is an **in-game rejection bound for typed strings and undocumented button
presses**, and the searched static spaces (288 code-string searches, 98,701
strings, ~8.4 M mask positions) contain no code system.

**Completeness of the cheat set.** The 14 names in §6 are consecutive string IDs
166–179 in the global string table (`0x080C0F18` base, entries at
`0x080C11B0`–`0x080C11E4`), matching exactly the 14 GBA cheats in the published
GBA guides (8 purchasable + 4 secret characters + secret level + turbo mode).
No 15th cheat name, no hidden "enter code" row and no leftover debug screen was
found on any reachable screen.

## 7. Validation evidence

* **Observed** (emulator screenshots): boot splash, save-slot selector, save-name
  keyboard, main menu, 8-row OPTIONS with no CHEATS, Skate Shop, empty
  Checklists→Secrets, free-skate/tutorial, 5-row pause menu with no CHEATS,
  post-novel-sequence state. Files: `s0.png`, `s2.png`, `title.png`, `menu1.png`–
  `menu4.png`, `options.png`, `opts_down8.png`, `opts_down1.png`, `skateshop.png`,
  `checklists.png`, `checklists_secrets.png`, `tonyhawk_start.png`,
  `pause_menu.png`, `novel_seq_after.png`, `after_pause_main.png`.
* **Observed** (debugger `x/1`): EWRAM dump `ewram_before.bin`/`ewram_pre_toggle.bin`
  (256 KiB each), string-ID table at `0x02006550`, IWRAM execution at
  `0x030019D0`.
* **Derived** (Thumb disassembly): keyboard handler `0x08014F78` and renderer
  `0x08015308`–`0x08015398`; 40-symbol alphabet and its literal pointers;
  string pointer table base `0x080C0F18` with IDs 52/166–179.
* **Derived** (byte analysis): 288 literal searches with hit classification;
  12,491 + 176,665 mask-run candidates; contiguous 14-name pointer table.
* **Inferred**: the exact cash amounts and Pro-Challenge thresholds (published
  GBA guides), and that the Secrets tab is the toggle surface after purchase —
  the tab was observed empty and gated, but a completed career was not played
  through, so the toggle itself was not exercised.
* **Not observed**: any successful typed code, any successful button code, any
  `new cheat unlocked` event from controller input.

## 8. Unknowns

* The exact unlock thresholds stored in the save record were not swept (the
  gate was only observed in the locked state).
* The per-cheat flag bytes in the EWRAM/flash record were not isolated: an
  EWRAM diff across an option toggle was dominated by rendering changes
  (2,063 changed bytes), so no flag address is claimed.
* The 6 `ssbsts` `-0x20` hits are classified as coincidental level data by byte
  inspection, not by an exhaustive proof over all possible encodings (e.g.
  5-bit packing was not applied to all 37 codes — but the GBA build has no
  code-entry screen to consume such a packing).
* Console code lists may apply to other SKUs; no claim is made about THPS4 on
  PS2/PC/Xbox/GameCube.

## 9. Tooling

* `strings -t x -n 4` + `grep -iE` — full text-bank enumeration.
* Python scripts in `/tmp/thps4/`: `search_codes.py` (multi-encoding
  literal sweep), `find_tables.py`, `xrefs.py`, `scan_ptrs.py`,
  `find_cheat_code.py`, `iwram_ptrs.py`, `button_scan.py` (mask runs),
  `ui.py` (xdotool key/shot), `dump_ram.py` + `dbgcmd.py` + `dbg_bridge.py`
  (mGBA CLI debugger over a FIFO-driven pty).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for the keyboard routines; REA/Ghidra raw-binary import (SHA-256 confirmed the
  same image) for pointer xrefs — Ghidra recognised only data references, as
  expected for a raw Thumb image (guide §5.5).
* Screenshots are kept on disk in `/tmp/thps4/`; only 2–3 were viewed
  at a time to conserve context (guide §16.2).

## 10. Legal note

No ROM bytes, graphics, music or game text are redistributed here; only
addresses, hashes, counts and the analyst's own tooling are published.
