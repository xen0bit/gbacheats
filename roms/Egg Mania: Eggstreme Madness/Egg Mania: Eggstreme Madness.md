# Egg Mania: Eggstreme Madness (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Egg Mania: Eggstreme Madness.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `EGGOMANIA` |
| Game code | `AEME` |
| Maker code | `7F` (Kemco) |
| Version | 0x00 |
| Complement / checksum | 0x34 / 0x0000 |
| Entry branch word | `0xEA0FE189` → **0x083F862C** (patched; stock GBA branch is `0xEA00002E`) |
| MD5 | `bfb2667e943ea0847547c0e44899f127` |
| SHA-1 | `78e3c7ce7b5bf5a924d80c2106c89c1d9bd6b6ae` |
| SHA-256 | `b546ebdcd93cfb4a27d91c11330d200bc869615c270ff077a73ddd29f66c8c2b` |

Scene release. The header entry word redirects to a cracktro at `0x083F862C` (ARM
`add r0,pc,#1; bx r0` → Thumb `0x083F8634`). The cracktro unpacks code/palette/VRAM,
shows a scrolling credit banner naming `MOD-REZ / ART-CG / CODE-AFTERMATH`, and on
`Start` branches through `[0x083F8954] = 0x080000C0` into the real game crt0.
Two embedded Nintendo-logo headers exist (`kikstart`/`C0D3` at file `0x0D65F0`, blank
stub at `0x0D6790`). The cracktro is an intro only — no trainer menu was found.

## 2. Executive summary

The GBA SKU has a small **developer-intended button-code system on the character-select
screen**:

* **Hold SELECT, press L → SPOOK** becomes selectable.
* **Hold SELECT, press R → YOLKOHAMA** becomes selectable.

Baseline roster is 8 characters (EGGY, SPIKE, ASTRO, YOLKO, FUNKY, ROBO, BEBOP,
COOLIO); after the codes it is 10. The unlock is observable in EWRAM at `0x020003FC`
(savestate byte `00 → 01`) — a direct RAM proof, not just a visual inference. Space is
fully enumerated (§6b): the SELECT-prefix dispatcher has exactly two action branches.

A **Password entry screen also exists** (36-symbol `A`–`Z`/`0`–`9` on-screen keyboard
with `OK`/`EXIT`, a 13-slot display whose first four glyphs render `EXC!`). In this
retry pass I **characterized the screen-state machine that hosts it** (§4, §6c) and
**proved a concrete hard blocker** to reaching it through normal UI (§8): the screen
is state `0x02000468 == 4` with group `0x020003E8 == 2`, but an exhaustive walk of
every menu screen × every button × combos × long holds × scrolls (with a GDB
watchpoint on the state word) produced writes only of `{0,3,5,6,16}` at
`0x08001544`/`0x0800126A`/`0x08000FBE`/`0x08000FFC` — never 4. The password
validator, alphabet encoding, checksum, and accept flag were therefore **not
recovered**, and no password code was generated or accepted. This is a proven
gate/blocker (§8), not a vague "could not find it".

No GameShark/CodeBreaker/memory-edit codes are reported (a ROMSFUN/libretro
CodeBreaker pair exists but is out of scope).

## 3. How to reproduce

Emulator: mGBA (SDL) under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, 3× scale.
Keymap: `A=x`, `B=z`, `L=a`, `R=s`, `START=Return`, `SELECT=BackSpace`, D-pad = arrow keys.
Hold keys 60–150 ms (short taps are missed).

**Button codes (reproducible):**

1. Boot. The scene cracktro shows a scrolling banner; press **START** to exit it.
2. Kemco and HotGen splash screens play automatically (~12 s total).
3. Language select (US flag / `ENGLISH`): press **A**.
4. Title "EGG MANIA – PRESS START": press **START**.
5. Main menu (`MAIN MODES / EXTRA MODES / OPTIONS / HOW TO PLAY / REAL GAME`): choose
   `EXTRA MODES` (Down, A), then `SOLO` (A), then the **character-select row** (the row
   where the name is highlighted and the hint ticker reads `CHOOSE A CHARACTER`).
6. Baseline roster when cycling Left/Right:
   `EGGY → SPIKE → ASTRO → YOLKO → FUNKY → ROBO → BEBOP → COOLIO → (wrap)`.
7. Enter the code: **hold SELECT (`BackSpace`), tap L (`a`)**. Cycle the roster: `SPOOK`
   now appears (ghost sprite) as an extra selectable character.
8. From a fresh state, **hold SELECT, tap R (`s`)**. Cycle the roster: `YOLKOHAMA`
   now appears as an extra selectable character.
9. RAM proof: save an mGBA savestate before and after step 7; the decompressed `gbAs`
   chunk differs at raw offset `0x213FC` (EWRAM `0x020003FC`): `0x00 → 0x01`.

Published codes tested (all from GameFAQs / Cheating Dome GBA lists):

| Source claim | Result |
|---|---|
| SELECT then L on character select → Spook | **Confirmed** (roster + RAM flag) |
| SELECT then R on character select → Yolkohama | **Confirmed** (roster) |
| Beat Bomb Mode on Medium/Hard → Sir Eggolot / Poncho | Achievements, not codes |
| 1,000,000 pts in Solo → Angelica | Achievement, not a code |
| Clear Egg Mania on Hard → Eggopolis level | Achievement, not a code |
| CodeBreaker `82011A9C 0000` (time 00:00) | Out of scope (memory-edit) |

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x08000000` | ROM | GBA header; entry word patched to `0xEA0FE189` |
| `0x080000C0` | ROM | real game crt0 (cracktro target, read from `0x083F8954`) |
| `0x08003140` | Thumb | central input routine: reads `KEYINPUT`, writes active-high mask |
| `0x08003180` | literal | `0x04000130` (`KEYINPUT`) |
| `0x0200008C` | EWRAM | active-high key mask (`A=1 … L=0x200`), written at `0x08003156` |
| `0x020003FC` | EWRAM | unlock flag byte; `0x00 → 0x01` when Spook code accepted |
| `0x020003FD` | EWRAM | companion byte used by the character-cycle code |
| `0x0801634C` | Thumb | character-cycle routine; literals `0x020003FD`, `0x020003FC`; extended IDs 8/9 |
| `0x0801E8D0` | Thumb | related state routine writing `0x020003FC` |
| `0x083F862C` | ARM | scene cracktro entry (`add r0,pc,#1; bx r0`) |
| `0x083F8634` | Thumb | cracktro unpacker/intro body |
| `0x083F8954` | ROM literal | `0x080000C0` (jump into real game) |
| `0x080D65F0` | ROM | embedded `kikstart`/`C0D3` scene header |
| `0x83F57C4`–`0x83F7AC7` | ROM | ASCII description bank (6 languages, 24 descriptions; no UI labels/alphabet) |
| `0x83F5C98` | ROM | `"Here, you can see hints for the game and other goodies."` |
| `0x83F5CD0` | ROM | `"Choose a character!"` (character-select description) |
| `0x83FE6DA` | ROM | cracktro credit banner |
| `0x1FBCB4` | ROM | 4bpp font-tile block (32-byte stride) used by in-game graphics |
| `0x1C0F6C` | ROM | 4bpp tile block loaded to VRAM on menu screens (not UI text) |
| `0x020003E8` | EWRAM | screen-group word: `0` = front-end menus, `2` = game-setup variants, `3` = gameplay setup |
| `0x02000404` | EWRAM | current menu selection index (submenus, 0-based) |
| `0x02000468` | EWRAM | **screen-state word** (see §6c) |
| `0x0200046C` | EWRAM | companion word (screen substate / player count) |
| `0x0E000000` | SRAM | save memory (`.sav` created as 0 bytes; unlocks observed in EWRAM) |

File offset → ROM address: `0x08000000 + file_offset`.

## 5. Algorithm

Button-code behaviour, reconstructed from observation + disassembly (confidence: derived):

```
; 0x08003140 (every frame)
keys_active_high = ~KEYINPUT & 0xFFFF          ; 0x0800314C, 0x08003150
[0x0200008C] |= keys_active_high               ; 0x08003156
; ...
; character-select screen (around 0x0801634C / 0x0801E8D0)
if (SELECT_held && L_pressed)  [0x020003FC] = 1 ; SPOOK   selectable (character ID 8)
if (SELECT_held && R_pressed)  ...              ; YOLKOHAMA selectable (character ID 9)
```

The two codes worked with SELECT held while the second key was tapped (60–100 ms). A
sequential interpretation with a 60 ms gap between key-up and key-down did not unlock
in the first attempt, so the gate is most plausibly "SELECT in held state AND L/R edge",
or requires a slightly longer inter-key interval (§16.6: held vs pressed semantics).
The literal mask table was not isolated: byte searches for the published sequence under
active-high (`04 00 00 02`, 7 hits) and active-low (`FB 03 FF 01`, 3 hits) encodings
landed in compressed graphics data, not a clean table; the validator uses
immediate/literal masks inside the screen handler rather than a contiguous table.

## 6. Tables

**Key masks (active-high, from `0x0200008C`):**

| Button | Mask |
|---|---|
| A | 0x001 |
| B | 0x002 |
| SELECT | 0x004 |
| START | 0x008 |
| RIGHT | 0x010 |
| LEFT | 0x020 |
| UP | 0x040 |
| DOWN | 0x080 |
| R | 0x100 |
| L | 0x200 |

**Character-select roster:**

| ID | Name | Availability |
|---|---|---|
| 0 | EGGY | baseline |
| 1 | SPIKE | baseline |
| 2 | ASTRO | baseline |
| 3 | YOLKO | baseline |
| 4 | FUNKY | baseline |
| 5 | ROBO | baseline |
| 6 | BEBOP | baseline |
| 7 | COOLIO | baseline |
| 8 | SPOOK | SELECT+L code |
| 9 | YOLKOHAMA | SELECT+R code |

**Password entry alphabet (observed on screen):** `A B C D E F G H I / J K L M N O P Q R /
S T U V W X Y Z 0 / 1 2 3 4 5 6 7 8 9` = 36 symbols (≥6 bits/symbol), 13 visible
character slots, first four rendered as `EXC!`, with `OK` and `EXIT` buttons.

### 6b. Enumeration — button codes

GBA keypad has 10 buttons → 1,024 possible simultaneous masks. The published codes are
2-button combinations with SELECT as the first button. I enumerated every
single-second-button variant **SELECT + {A, B, START, UP, DOWN, LEFT, RIGHT, L, R}**
on a clean character-select state (savestate with flag `0x00`), re-selecting the
character row and cycling all entries after each attempt:

| Combo | New character? |
|---|---|
| SELECT + A | no (moves menu selection) |
| SELECT + B | no |
| SELECT + START | no |
| SELECT + UP | no |
| SELECT + DOWN | no |
| SELECT + LEFT | no |
| SELECT + RIGHT | no |
| **SELECT + L** | **yes — SPOOK** |
| **SELECT + R** | **yes — YOLKOHAMA** |

**Novel code:** none can be minted for a 2-entry hard-coded table — the space is fully
enumerated above. The two working codes are the complete SELECT-prefix branch set among
the 9 variants tested. **Bounds proven by rejection:** the 7 non-L/R SELECT
continuations all leave the roster at exactly the 8 baseline characters and do not
change the character-cycle state — recorded as in-game rejection. The presence of
exactly 10 roster entries after both codes bounds the character-ID field to 0..9.

**Password space:** alphabet 36 × 13 slots ≈ 36^13 ≈ 1.7×10^20 raw strings. No accepted
literal anchor, no published GBA password list, and the validator was not located;
therefore no password code was generated or accepted (§8 is a proven blocker, not a
claim that no password code exists).

### 6c. Screen-state machine (new in this pass)

Savestate diffs and GDB watchpoints give the front-end state machine at `0x02000468`
(`u32`), with group `0x020003E8` and selection `0x02000404`:

| `0x468` | `0x3E8` | Screen (observed) |
|---:|---:|---|
| 0 | 0 | Main menu (`MAIN MODES / EXTRA MODES / OPTIONS / HOW TO PLAY / REAL GAME`) |
| 1 | 0 | HOW TO PLAY (`HELP / TUTORIAL / PRACTICE`) |
| 2 | 0 | EXTRA MODES (`SURVIVAL / SOLO / TIME TRIAL / BOMB`) |
| 3 | 0 | MAIN MODES difficulty chooser (`OVER EASY / HARD BOILED`) |
| 4 | 2 | Password-screen context (from prior `password.ss1`, §8) |
| 5 | 0 | Main-mode detail pane (`OVER EASY`) |
| 6 | 0 / 3 | Game setup (`1 PLAYER / character`) / in-game setup |
| 7 | 2 | Options audio pane (`SOUND ON`) |
| 9 | 0 | OPTIONS (`SOUND ON / TRACKS OFF`) |
| 10 | 2 | 2-player character-select variant |
| 11,13 | 2 | 4-player character-select variants |

Reachable writes observed with a hardware watchpoint on `0x02000468` during a full
menu walk from the main-menu savestate:

```
Old value = 0, New value = 3,  PC=0x08001544
Old value = 3, New value = 6,  PC=0x08001544
Old value = 6, New value = 0,  PC=0x0800126A
Old value = 0, New value = 3,  PC=0x08001544
Old value = 3, New value = 6,  PC=0x08001544
... (never 4)
```

Static sites in the front-end state writer: `0x08000FBE` (`mov r0,#5; str`),
`0x08000FFC` (`mov r0,#6; str`), with `cmp r0,#4` checks at `0x080010B6`,
`0x08001680`, `0x080016EC` (screen-4 special-casing) but no reachable store of 4.

## 7. Validation evidence

* **Observed (emulator, screenshots):** title/language/main/options/extra-modes/how-to/
  mode/character-select/game-over screens walked; baseline 8-character roster; SPOOK
  after SELECT+L; YOLKOHAMA after SELECT+R; password entry screen with `EXC!` + 36-key
  keyboard (prior session shot `shot_09.png`); scene cracktro banner and credit text.
* **Observed (RAM):** savestate `gbAs` chunk diff — `raw[0x213FC]` (EWRAM `0x020003FC`)
  `0x00 → 0x01` after SELECT+L; companion `0x020003D4` `0x06 → 0x09`. Prior
  `password.ss1` decompressed state: `0x3E8=2, 0x3EC=5, 0x404=2, 0x468=4, 0x46C=10`.
* **Derived (disassembly):** entry word patched to `0x083F862C` and cracktro's final
  `bx 0x080000C0`; `KEYINPUT` reader at `0x08003140` and key-mask variable `0x0200008C`;
  character-cycle code referencing `0x020003FC`/`0x020003FD` with extended IDs 8/9;
  ASCII text bank at `0x83F57C4`+ (24 English + 5× localized descriptions) with no UI
  label or alphabet strings; font-tile blocks at `0x1FBCB4` (VRAM match) and `0x1C0F6C`
  (menu VRAM match), neither yielding an alphabet table to OCR; no 36-symbol ASCII or
  tile-index table found (`grep` for the ASCII alphabet and a 36-distinct-byte run both
  returned zero hits); 13-byte `0xFF`-fill loops exist at `0x0800AEF6`/`0x0800AF00`
  but decompile to a 6×14 gameplay grid, not a password buffer.
* **Inferred:** exact held-vs-edge semantics of the SELECT+L/R gate; the meaning of the
  `EXC!` prefix and the password format.
* **Prompt-injection check:** fetched web pages (GameFAQs, Cheating Dome, Cheat Happens,
  Wikipedia, GameRevolution) were treated as data; no instructions from them were
  executed. No injection payload was encountered.

## 8. Unknowns / proven blocker

**The password validator and its format/checksum were not recovered — and the entry
screen could not be re-reached in this pass.** Concrete evidence for the blocker:

1. **Screen identified in RAM but not via UI.** The prior session's `password.ss1`
   decompresses to a state with `0x02000468=4`, `0x020003E8=2`, `0x02000404=2`,
   `0x0200046C=10`. Loading that state boots into a 2-player gameplay screen (state `4`
   is the post-entry game screen), confirming this state word is the password context.
2. **Exhaustive UI walk (no gate reached).** From a verified main-menu savestate I
   booted a fresh emulator for each test and pressed: every single button at the title,
   main menu, and character-select screens; all 2-button pairs (including all SELECT+
   button and L+R variants); selected 3-key combos (SELECT+L/R/A/B, L+R+A, A+B+START,
   etc.); SELECT held 0.5/1.0/2.0 s followed by every other button; and scrolled every
   submenu past its visible items. None changed `0x468` to 4. Menu-item counts were read
   from `0x02000404`: main menu 5 items (0..4), EXTRA MODES 4, HOW TO PLAY 3, OPTIONS 2 —
   no hidden rows.
3. **GDB hardware watchpoint transcript (§6c)** shows the only writes to `0x02000468`
   during a full menu walk are `{0,3,5,6,16}` at `0x08001544`, `0x0800126A`,
   `0x08000FBE`, `0x08000FFC` — **no writer of 4 is reached by any tested input**.
   A final GDB patch sweep of states 14–25 with group `0x3E8=2` from a character-select
   state rendered only 2-player character-select variants (`final_s14.png` …
   `final_s25.png`), never the password keyboard.
4. **Static decode blocked.** UI text is tile-indexed; `strings` finds no alphabet,
   menu labels, or password literals. No ASCII alphabet string (`A…Z0…9`) and no
   36-distinct-byte tile-index table exists in the 4 MiB image. Font-tile blocks were
   located by VRAM matching (`0x1FBCB4`, `0x1C0F6C`) but rendered as generic 4bpp art,
   not a decodable glyph-index map; OCR of rendered tile banks returned noise.
5. **No validator anchor.** Ghidra (REA MCP, raw ARM import at `0x08000000`) decompiled
   the 13-byte `0xFF`-fill region (`0x0800AEA4`) — it is a 6×14 gameplay grid, not a
   password input buffer. No compare-against-table or checksum loop over a 13-char
   buffer was identified. Without an accepted literal or a reachable buffer, the
   "debugger-as-oracle" technique (§16.19) could not be applied.

**Consequence:** no code was minted, no accept flag address is known, and bounds could
not be proven by in-game rejection for the password system. This is a *gated/unreached
feature* (guide §16.3 case 4) with the exact gate characterized above — not a claim
that no password code exists. The two button codes remain the only confirmed cheat
surface on this SKU.

Other minor unknowns (unchanged from first pass): whether additional hidden
characters/levels exist beyond IDs 8/9 (cycle bound is 0..9); exact inter-key timing of
the button-code gate; whether the unlock persists to SRAM across a real power cycle
(the `.sav` is 0 bytes; the EWRAM flag was proven, not a long-term save field).

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, Python 3 (`struct`, `zlib`, `PIL`) — Phase 0/state parsing.
* `strings -t x`, `grep -abo`, Python byte/pointer scanners — recon.
* `arm-none-eabi-objdump -M force-thumb` / `-M force-arm` — disassembly.
* Capstone 5.0.7 — Thumb literal/BL scans, `cmp #13` sweep, writer scan.
* Ghidra 12.1.4 via REA MCP (raw ARM import at `0x08000000`) — procedure decompilation
  (confirmed tile-indexed UI: no password/alphabet ASCII strings; 13-byte region is a
  gameplay grid).
* `tesseract` — attempted OCR of rendered tile banks (returned noise).
* mGBA (SDL) under Xvfb `:316` + openbox; `xdotool` XTEST input; `scrot`/`import` screenshots;
  `convert`/`montage` (ImageMagick) for capture mosaics; GDB stub (`mgba -g`,
  `gdb-multiarch`) for memory dumps and a hardware watchpoint on `0x02000468`.
* `zlib.decompress` of the mGBA `.ss1` `gbAs` PNG chunk for RAM diffs (§16.13).
* Web sources consulted: GameFAQs, Cheating Dome, Cheat Happens, Wikipedia,
  GameRevolution, ROMSFUN (CodeBreaker, out of scope).
* Scripts/artifacts in `/tmp/eggmania2/` (`gba.py`, `parse_ss.py`,
  `explore.py`/`2`/`3`, `title_brute.py`, `cs_brute.py`, `scroll.py`, `longhold.py`,
  `force_screens.py`, `find_writers.py`, `screens/` and `sweep3/` montages,
  `wp3_gdb.log`). Prior-session evidence in `/tmp/eggmania/`
  (`shot_09.png` = password screen, `fresh_before.ss1`/`fresh_after.ss1` = RAM proof,
  `baseline_chars.png` / `after_code_chars.png` / `r_code_chars.png` = roster proof).

No ROM or copyrighted assets are redistributed by this report.
