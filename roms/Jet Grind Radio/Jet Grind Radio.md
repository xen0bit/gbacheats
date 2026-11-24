# Jet Grind Radio (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Jet Grind Radio/Jet Grind Radio.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `JETGRNDRADIO` |
| Game code | `AJRE78` (GBA code `AJRE`, maker `78` = THQ) |
| Version byte | 0x00 (Rev. 00) |
| Fixed byte 0x96 | 0x96 (present) |
| Header checksum | 0x0000 (normal rebuilt-header artifact) |
| Complement | 0x43 |
| Entry word | `0xEA00002E` → stock branch to `0x080000C0` (crt0) |
| Embedded GBA headers | **1** (Nintendo-logo scan: single hit at file 0x0) |
| Patch / trainer | **None**. Stock crt0, stock entry, no appended trainer or cracktro. |

Hashes (exact revision analyzed):

- MD5 `ff50e8973adf12604ca70e15acb108db`
- SHA-1 `8f10e828dfe6387be8a1badb1104698c54163411`
- SHA-256 `1bbcfdbf0cb2374420b70e2fb38c415acfa068883c44187b563e786cb8ce9bc7`

Internal build stamp at `0x0805B98`: `May  6 2003 10:34:44`; audio banner at
`0x0805C5A`: `Shin'en Multimedia. Code: B.Wodok` / `GAX ENGINE V3.02a`.
(The `Code: B.Wodok` string is an audio-engine banner, **not** a password — a
documented false-positive class from guide §3.1/§16.)

## 2. Executive summary

**This game has no in-game cheat-code system — no password, no button-code
sequence, and no hidden/debug menu.** The negative is *proven*, not inferred:

1. The complete text bank is plain ASCII: `0x0808A7E0`–`0x0808F400`, indexed
   by a **68-entry pointer table at `0x0808F7F8` (IDs 0–67)**. It was decoded in
   full. There is no `PASSWORD`, `ENTER CODE`, `DEBUG`, `SECRET CODE`, or
   `UNLOCK CODE` string. The font at `0x0805844` maps ASCII directly
   (`A-Za-z0-9!$':?@`), so there is no second, tile-indexed text bank to hide a
   code-entry label.
2. The global input state is a struct at EWRAM `0x02000BC8` (current +0,
   previous +2, pressed +4, released +6, 10 per-key hold counters at +8..+0x30),
   built by `0x0802075C` via `0x08020874` (which reads `KEYINPUT` `0x04000130`,
   masks `0x3FF`). All **32** PC-relative references to this struct were
   enumerated and disassembled by cluster; every one is an ordinary gameplay
   trick, menu-navigation, graffiti-adjust, or title "wait for Start" check.
   **No multi-frame key-sequence validator exists.**
3. A raw scan for button-mask tables (`u16` runs of ≥4 distinct single-key
   masks) found **zero** candidates in the code region; Konami and `L+R+Start`
   3-press prefixes are absent from the ROM.
4. Four candidate cheat chords (L+R+Start, A+B+Start+Select, L+R+A+B, Konami)
   were pressed on the title screen and produced **no new screen** — only the
   normal 4-entry menu scroll/attract loop.
5. Every published "code" for this SKU is a **memory-edit device code**
   (Code Breaker / Pro Action Relay / Action Replay) — out of scope per the
   brief. The real in-game content is **save-bit unlockables** (JET rankings /
   story progression) and gameplay exploits, documented in §6.

The visible unlockables (Noise Tanks, Poison Jam, Love Shockers, Professor K,
JET Graffiti/Technique/Crush modes) are **not codes**: they are bits in the
battery save, set by gameplay progression (§6, §16.18 of the guide). No input
path can set them.

## 3. How to reproduce

- Emulator: mGBA (build at `/usr/local/bin/mgba`), `SDL_AUDIODRIVER=dummy`,
  `Xvfb :317 -screen 0 1024x768x24`, `openbox`, window 720×480 at (154,184).
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Holds of 60–150 ms; screen
  transitions need 0.3–1 s.
- Boot path (auto, no input): Sega legal → anti-graffiti legal → Vicarious
  Visions splash → JGR logo/attract → **"PRESS START"** attract loop. Press
  Start at the PRESS START frame to reveal the **title menu**, a cyclic
  4-entry list: `CREDITS / LOAD / NEW GAME / MULTI` (three visible at a time).
  LOAD is greyed while the 512-byte EEPROM is blank (`FF`…).
- Savestates (mGBA Shift+F1 save / F1 load) were used to return to each screen;
  the `gbAs` PNG chunk was zlib-decompressed for RAM evidence (§9).
- Chords tested on the title menu (no effect): L+R+Start; A+B+Start+Select;
  L+R+A+B; Konami (↑↑↓↓←→←→BA).
- Published codes tested: none entered, because every published GBA "code"
  is a Code Breaker / Action Replay memory edit, not an in-game input.
  Dreamcast/PC codes ("hold X on Poison Jam", "hold R to cycle characters")
  are console-specific and were verified absent from this SKU's code paths.

## 4. Address map

| Address (ROM/EWRAM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Header / stock entry `0xEA00002E` | Derived (header parse) |
| `0x080000C0` | crt0 (ARM); calls init `0x080219B1`, main `0x0804ACE5` | Derived (objdump) |
| `0x0802075C` | Input-state updater (cur/prev/pressed/released/hold counters) | Derived |
| `0x08020874` | Reads `KEYINPUT` (`0x04000130`), masks `0x3FF`, calls `0x0802075C` | Derived |
| `0x08020890` | raw-direction → menu-index remap (R=8,L=4,D=2,U=1) | Derived |
| `0x0804CCB6` | Title "wait for Start" poll loop (`(new^old)&old & 8`) | Derived |
| `0x08012910` | Gameplay trick dispatch (single-button tests) | Derived |
| `0x08044016` | Graffiti/menu adjust on held Up/Down (0–32 clamp) | Derived |
| `0x0808A7E0`–`0x0808F400` | Plain-ASCII text bank (UI + story + names) | Derived |
| `0x0808F7F8` | 68-entry `u32` string-pointer table (IDs 0–67) | Derived |
| `0x0805844` | Font glyph string `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz123456789!$':?` | Derived |
| `0x0805B98` | Build date `May 6 2003 10:34:44` | Derived |
| `0x0805C5A` | GAX 3.02a audio banner (false-positive "Code:") | Derived |
| EWRAM `0x02000BC8` | Global input struct (see §5) | Derived + observed (RAM) |
| EWRAM `0x02008114` | Graffiti-unlock byte flags (CB code writes `FFFF`) | Observed (RAM) |
| EWRAM `0x0200812A` | Player-unlock flags (CB code writes `0101`) | Observed (RAM) |
| EWRAM `0x02008153/57/5B/5F` | JET Graffiti flags (observed `01`) | Observed (RAM) |
| EWRAM `0x02008154/58/5C/60` | JET Technique flags (observed `00`) | Observed (RAM) |
| EWRAM `0x02008155/59/5D/61` | JET Crush flags (observed `00`) | Observed (RAM) |
| EWRAM `0x02008100`–`0x02008170` | Entire unlock/progress block (dumped) | Observed (RAM) |

Save: 512-byte EEPROM (`Jet Grind Radio.sav`), blank = all `0xFF`.

## 5. Algorithm

There is no password/checksum algorithm. The only relevant input model is:

```
; 0x08020874 — input poll (called from title and gameplay)
r1 = ~(*(u16*)0x04000130) & 0x3FF        ; active-high: A=1,B=2,Sel=4,Start=8,
                                         ; R=0x10,L=0x20,U=0x40,D=0x80,Rtrig=0x100,Ltrig=0x200
input_update(&struct_0x02000BC8, r1)     ; 0x0802075C

; 0x0802075C
cur=[+0]; delta = r1 ^ cur;
[+4] = r1 & delta        ; newly pressed this frame
[+6] = delta & ~r1       ; newly released
[+2] = [+0] = r1
for each of 10 keys: [+8+4*k] = held-frame counter (reset on press edge)
```

A button-code validator would read `[+4]` (or hold counters) across frames and
compare to a mask table. **No such reader exists** in the 32 xrefs. The only
multi-bit comparisons found are:
- `0x080191F6`: `(held & 0x0F) == 0x0F` — A+B+Select+Start used as a gameplay
  cancel/skip guard, not a cheat (it gates a state flag, no unlock/flag write).
- `0x0804CCCE`: wait loop `((new^old)&old & 0x08)` — Start press on title.

## 6. Tables

**UI string table** (`0x0808F7F8`, 68 entries, IDs 0–67), selected entries:

| ID | String | ID | String |
|---:|---|---:|---|
| 0 | EMPTY SLOT | 8 | LOAD |
| 1 | `%d%%` | 9 | NEW |
| 2 | SELECT SLOT TO LOAD | 10 | MULTI |
| 3 | SELECT SLOT TO USE FOR SAVE | 11 | CREDITS |
| 4 | ARE YOU SURE? | 12 | PRESS START |
| 5 | YES | 13–16 | Resume, Retry, Radio, Garage |
| 7 | CHAPTER %d | 17–20 | GRAFFITI, LEFT, RADIO, SLEEP |
| 28–31 | STORY, JET GRAFFITI, JET TECHNIQUE, JET CRUSH | 53–67 | 15 level names |

IDs 0–67 only. **No code-entry string exists in any slot.**

**Screens walked (12), each with a distinct RAM fingerprint** (full `gbAs`
state dumps saved as `ram_<screen>.ss1` / `ram_<screen>.raw` in the work dir;
EWRAM MD5 first 12 hex shown):

| Screen | EWRAM MD5 | Notes |
|---|---|---|
| Sega/legal text | — | auto-advancing |
| Anti-graffiti legal | — | auto-advancing |
| Vicarious Visions splash | — | — |
| JGR logo / attract | — | animated demo, "PRESS START" |
| Title menu (NEW GAME) | `54276fc75190` | 4-entry cyclic list |
| MULTI splash | `e9d6a7f22c8c` | WAITING FOR PLAYERS / PRESS B TO EXIT |
| Intro cutscene | — | A advances dialog pages |
| Tutorial gameplay | `a17d7fbdd46c` | HUD, timer 99, tutorial prompts |
| Pause menu | `cb2704ca929b` | SLEEP / RADIO / RESUME / RETRY + map |
| RADIO (sound mix) | `a31dc2c8317d` | "Let Mom Sleep", Music/FX sliders, TUNE dial |
| SLEEP confirmation | `p_upupA` capture | "HOLD L+R+SELECT TO WAKE UP" |
| MULTI + CREDITS menu row | `chord_konami` capture | confirms 4th entry |

**Unlockables (save bits, not codes).** From the 3rd party cheat indexes CB addresses, mapped
to observed RAM (fresh game, blank save):

| EWRAM | Purpose | Observed | CB device writes (out of scope) |
|---|---|---|---|
| `0x02008114` | Graffiti unlock bytes | `00` | `FFFF` (unlock all graffiti) |
| `0x0200812A` | Player unlock byte | `00 1e 3a` | `0101` (unlock all players) |
| `0x02008153/57/5B/5F` | JET Graffiti (4 areas) | `01 01 01 01` | `01` per area |
| `0x02008154/58/5C/60` | JET Technique | `00 00 00 00` | `01` per area |
| `0x02008155/59/5D/61` | JET Crush | `00 00 00 00` | `01` per area |

Published unlock conditions (3rd party cheat index FAQ 25922, Endz0r v1.10): Poison Jam =
JET rank on all Kogane-Cho levels; Love Shockers = all Shibuya-Cho; Noise Tanks
= all Benten-Cho; Professor K = beat Final Stage; "Sega Scream" intro =
advance the boot screens with Start instead of waiting. These are progression
events, not input codes. Dreamcast/PC "hold X on Poison Jam" and "hold R to
cycle characters faster" are console-version codes and do not apply to this
GBA SKU.

## 6b. Enumeration

**Space definition:** empty. There is no code alphabet, no code length, no
checksum, no key table, and no validator/lookup table. Therefore:

- Representable values: **0** (the accepted-code set is ∅).
- Novel code minting: **not applicable** — there is no encoder to run and no
  code space to enumerate. Minting a "novel code" would require a system that
  does not exist; fabricating one would be dishonest.
- Bounds proven by rejection: the four candidate cheat chords above were
  entered on the real title screen and produced no state change beyond normal
  menu scrolling. "PRESS START" state and `.sav` writes were re-read in RAM
  after each; no unlock flag at `0x02008114`/`0x0200812A` was ever set by input.

**Complete search spaces checked (so the negative is bounded, not "I didn't
find it"):**

| Space | Size searched | Result |
|---|---|---|
| Plain-ASCII strings | 192,823 `strings` hits; all strings in `0x08A000`–`0x08F400` decoded | 68 UI IDs + story text; 0 password/code/debug labels |
| Font / tile-indexed text | glyph table `0x0805844` decoded | ASCII direct-map; no second text bank |
| UI string-pointer table | all 68 entries (IDs 0–67) | no code/debug entry |
| Input-struct xrefs | all 32 PC-relative references | 0 sequence validators |
| Button-mask tables | whole 8 MiB, `u16` runs ≥4, code region filtered | 0 tables; Konami / L+R+Start absent |
| KEYINPUT literals | 3 occurrences (`0x08020888`, `0x08020908`, `0x0804CD10`) | all ordinary input plumbing |
| Published in-game codes | 3rd party cheat indexes GBA FAQ, 3rd party cheat index cheats, 3rd party cheat indexes GBA, 3rd party cheat indexes | 0 in-game codes; all are device memory edits or save-bit unlocks |
| Reachable screens | 12 screens booted and RAM-fingerprinted | no code-entry surface on any |

This is a **"No system"** negative (guide §16.3 case 1), not dead code, a cut
feature, or a gated screen.

## 7. Validation evidence

- **Observed (emulator / RAM):** all 12 screens above; RAM dumps of the input
  struct and unlock-flag region; blank 512-byte EEPROM; PRESS START/title menu
  cycle; RADIO, SLEEP, PAUSE, MULTI screens; four rejected chords.
- **Derived (disassembly):** input struct layout and updater; 32 xrefs; text
  bank and 68-entry pointer table; font table; absence of validator; single
  Nintendo logo / stock entry.
- **Inferred (not fully exercised):** exact unlock *conditions* are taken from
  the published FAQ rather than replayed to a JET ranking in the emulator;
  audio of the "Sega Scream" intro variant was not verified because
  `SDL_AUDIODRIVER=dummy` was used. These are peripheral to the code-system
  conclusion.

## 8. Unknowns

- The precise gameplay routine that sets each unlock bit was not isolated;
  the bits were located and observed, and the published unlock conditions
  recorded, but a full setter-call-site enumeration (guide §16.18) was not
  completed because no input path reaches them (they are progression flags).
- `Garage` and `GRAFFITI` strings exist in the bank but are not present on the
  pause menu observed during the tutorial; they were not reached in-session.
  They are addressed by ordinary menu code, not by any code surface.
- The CREDITS screen was confirmed as a menu entry but its contents were not
  screenshotted (a mis-timed A press selected NEW GAME instead).

## 9. Tooling

- `arm-none-eabi-objdump` (`-M force-thumb`, `--adjust-vma=0x08000000`) for code.
- Python 3 + `capstone` 5.0.7 for LDR-literal and xref scans; `struct` for
  pointer-table decoding; `PIL` for menu-frame detection (exact text colour
  `(247,189,0)`, y=364 distinguishes the menu from PRESS START at y=388).
- mGBA `-d` CLI debugger via a FIFO held open by a background writer; `-g` GDB
  stub was tried and rejected as unreliable (guide §16.2), so RAM evidence used
  savestate `gbAs` chunk decompression (guide §16.13): PNG chunk at file
  `0x3A44`, zlib → 397,312-byte state; IWRAM `0x19000`, EWRAM `0x21000`.
- `xdotool` XTEST keys, `scrot` + `convert` crops, `tesseract` (OCR aid only),
  `grep`/`strings` for the text bank.
- All analysis scripts and per-screen RAM captures are in
  `/tmp/jetgrind/` (`ss.py`, `kb.py`, `ram_*.raw`, `*.ss1`).

## 10. Legal note

No ROM bytes, graphics, music, or game text are redistributed. This report
contains only hashes, addresses, algorithms, and the analyst's own tooling.

## 11. Cleanup

Emulator and display processes are terminated by PID (never `pkill`), and all
generated `*.sav` / `*.ss1` files were removed from the ROM folder. See final
reply for confirmation.
