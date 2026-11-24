# Wakeboarding Unleashed Featuring Shaun Murray (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Wakeboarding Unleashed Featuring Shaun Murray.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `SMPW!!!!!!!!` (scene-release `!` padding; retail title is not in the header) |
| Game code / maker | `AWDE` / `52` (Activision; boot splash: "Activision Sports Revolution", developed by Small Rockets Ltd.) |
| Version / complement / checksum | `0x00` / `0x7A` / `0x0000` (checksum 0 is the usual rebuilt-header artifact, §16.1) |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0`; no cracktro/trainer observed |
| MD5 | `04d7e6cd55b91ff493e8529fbcf82266` |
| SHA-1 | `9eb979282fb2084bd205282ea71f18409d5558e2` |
| SHA-256 | `2780e75de70d8ecf4fe4aa45bbe96c4742b08913d46143d7f9351a68558b31f4` |

All addresses below are for **this exact image**. File offset = ROM address − `0x08000000`.

## 2. Executive summary

This game has a genuine developer-intended password system: the **"ENTER HORSE WORD"** screen
in Multiplayer → Horse Mode → Horse Options. Its validator is a closed set of exactly
**three 8-character words**. Entering the right word sets one of three EWRAM flag words,
which `JUDGEAVAILABILITY` uses to unlock (a) the otherwise greyed-out **CHEATS menu** in
OPTIONS, (b) the **OCEAN WORLD** landscape, and (c) the two **secret riders LIL and P**.

| Word (exact case) | Flag set to 1 | Unlock |
|---|---|---|
| `!HAXORED` | `0x020099D8` | Enables **CHEATS** in OPTIONS → CHEATS MENU (8 toggles) |
| `GMAN@DEF` | `0x020099DC` | Enables all `LANDSCAPE` entries → 7th level **OCEAN WORLD** becomes selectable |
| `LILBURNT` | `0x020099E0` | Enables `SECRETCHARACTER` entries → riders **LIL** and **P** become selectable |

Any other word (e.g. `ZZZZZZZZ`) is stored as the Horse-game word but sets **no** unlock flag.
There is no checksum, generator, button code, or save-bit unlock in this system: the
validator is a three-way `strcmp` chain, so the accepted set is provably exactly three
strings (§6b). Web reconnaissance (four queries, GameFAQs-style terms) found **no published
code list for this SKU**, so these words should be treated as the complete native set.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap used: A=`x`, B=`z`, Start=`Return`, D-pad=arrow keys (XTEST events to the focused window).
* Fresh save: boot → Start → SELECT SAVE GAME → A (EMPTY) → enter a 3-letter name → END → A.
* Path to the password screen:
  **Main Menu → Up ×2 → MULTIPLAYER → HORSE MODE (A) → HORSE OPTIONS → WORD (Down ×2) → A → ENTER HORSE WORD**.
* Keypad grid (30 cells, linear order with wrap): row0 `A B C D E F G H I J`,
  row1 `K L M N O P Q R S T`, row2 `U V W X Y Z ! @ $ End`. Cursor **stays on the letter just
  typed**, so moves for the next letter are relative. Eight slots; B deletes the last char.
* Type a word, move to `End`, press A to submit. The game returns to HORSE OPTIONS.
* `!HAXORED` then: Main Menu → Up → OPTIONS → CHEATS is now bright (was grey) → A opens the
  8-toggle CHEATS MENU. Left/Right toggles a row, A commits (`setcheats`).
* `LILBURNT` then: Career → Start Career → SELECT RIDER; cycle with Right — `LIL` and `P`
  appear in the rider name box (default roster has 8 riders only).
* `GMAN@DEF` then: Career → Start Career → SELECT RIDER → CONTINUE → LEVEL SELECT; cycle
  with Right — `OCEAN WORLD` is now the 7th selectable landscape (baseline wraps from
  SAUSALITO back to LAKE TAHOE).

### Screenshots captured (work dir `/tmp/wakeboarding`, not committed)
`wordentry.png` (entry screen, 8 slots), `typed_lil2.png` (manual `LILBURNT` typed),
`lil_manual_submitted.png` (flag after manual submit), `lil_unlocked_full.png` (LIL + P in
rider select), `opts_unlocked.png` (CHEATS enabled) vs `s7.png` (CHEATS grey),
`cheatmenu.png` / `cheattoggle.png` (8 toggles, PERFECT BALANCE ON),
`levels_unlocked2.png` + `levelnames.png` (7 landscapes) vs `levels_base.png` +
`levelnames_base.png` (6, OCEAN WORLD locked), `manual_submit.png` (rejected `ZZZZZZZZ`
stored as word but no unlock).

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x0802D950` | Generic `strcmp` (word compares called from the opcode handler) | Derived (disasm) + Observed (read watchpoint hit here) |
| `0x08006A38`–`0x08006A42` | `checklamerword` opcode: compares script command name to `0x087F20A0` | Derived |
| `0x08006A44` | loads word buffer pointer `0x020098A0` into `r4` | Derived |
| `0x08006A46`/`0x08006A52` | compares buffer to `!HAXORED`; on match loads `0x020099D8` | Derived |
| `0x08006A68`/`0x08006A74` | compares buffer to `GMAN@DEF`; on match loads `0x020099DC` | Derived |
| `0x08006A80`/`0x08006A8C` | compares buffer to `LILBURNT`; on match loads `0x020099E0` | Derived |
| `0x08006A8E`–`0x08006A90` | `mov r0,#1; str r0,[r1]` — writes the flag | Derived + Observed |
| `0x087F20A0` / `B0` / `BC` / `C8` | token-pool strings `checklamerword`, `!HAXORED`, `GMAN@DEF`, `LILBURNT` | Derived (literal pool + bytes) |
| `0x0800B2C0`–`0x0800B45A` | `JUDGEAVAILABILITY`: gates menu entries by flag | Derived |
| `0x0800B338`/`0x0800B33C` | name `SECRETCHARACTER` / flag `0x020099E0` | Derived |
| `0x0800B39C`/`0x0800B3BC` | name `CHEATS` / flag `0x020099D8` | Derived |
| `0x0800B40C`/`0x0800B410` | name `LANDSCAPE` / flag `0x020099DC` | Derived |
| `0x02009890` | script variable `LAMER` (ASCII) | Observed (RAM dump) |
| `0x020098A0` | 8-byte word buffer + NUL at `+8` | Observed (savestate diff, debugger writes) |
| `0x020099D8 / DC / E0` | unlock flags (word-sized, `0` or `1`) | Observed (before/after RAM reads) |
| `0x054E12B` | script screen `LAMER WORD ENTRY` ("ENTER HORSE WORD", TEXTENTRY, 8 slots) | Derived (ASCII script bank) |
| `0x054EA1E` | script link `checklamerword` → `nextscreen` | Derived |
| `0x0545EC2` | script screen `CHEATS MENU` (8 `CHEAT n` rows) | Derived |
| `0x05456E0` | script screen `OPTIONS` (CHEATS row uses variable `CHEATS`) | Derived |
| `0x0800B338` area | name table for riders: `SHAUN`..`WRIGHT`, `LIL`, `P` at `0x087F23A8`–`0x087F2428` | Derived |

## 5. Algorithm / pseudocode

The opcode handler is a flat three-way string comparison — no arithmetic:

```c
// 0x08006A44..0x08006A90, r4 = 0x020098A0 (word buffer)
if (strcmp(word, "!HAXORED") == 0)  flag = &unk_020099D8;   // CHEATS
else if (strcmp(word, "GMAN@DEF")==0) flag = &unk_020099DC;  // LANDSCAPE
else if (strcmp(word, "LILBURNT")==0) flag = &unk_020099E0;  // SECRETCHARACTER
else return;                                                  // no unlock
*flag = 1;
```

The word buffer is filled directly by the TEXTENTRY screen from the on-screen keypad;
characters are stored as plain ASCII (visited letters remain the cursor position). The
word is also persisted as the Horse-game "WORD" value shown on HORSE OPTIONS even when
it is not a cheat word. `JUDGEAVAILABILITY` (0x0800B2C0) compares each menu row's variable
name with `CHEATS`, `LANDSCAPE`, `SECRETCHARACTER` and marks the row non-selectable when the
corresponding flag is 0 — this is why the visible options are gated until the word is used.

## 6. Tables

### 6.1 Accepted words (complete)
| # | String | ROM string addr | Flag addr | Gated variable / effect |
|---|---|---|---|---|
| 1 | `!HAXORED` | `0x087F20B0` | `0x020099D8` | `CHEATS` → CHEATS MENU enabled |
| 2 | `GMAN@DEF` | `0x087F20BC` | `0x020099DC` | `LANDSCAPE` → OCEAN WORLD (and all 7 landscapes) |
| 3 | `LILBURNT` | `0x087F20C8` | `0x020099E0` | `SECRETCHARACTER` → riders LIL and P |

### 6.2 CHEATS MENU entries (all 8, from script `0x0545F6D`–`0x0545F4C`)
`PERFECT BALANCE` (0), `PERFECT MANUAL` (1), `ALWAYS SPECIAL` (2), `STUD MODE` (3),
`SPEED UP MODE` (4), `MOON PHYSICS` (5), `GHOST MODE` (6), `KID MODE` (7). Each is an
independent ON/OFF toggle committed with A (`setcheats`); toggling PERFECT BALANCE to ON
was observed (`cheattoggle.png`).

### 6.3 Keypad alphabet
`A B C D E F G H I J / K L M N O P Q R S T / U V W X Y Z ! @ $ End`
— 26 letters + 3 punctuation = 29 printable symbols plus the `End` submit cell.

## 6b. Enumeration

**Space definition.** The word field is 8 bytes (`0x020098A0`..`0x020098A7`, NUL at `+8`),
drawn as 8 slots. The keypad offers 29 printable symbols (`A`–`Z`, `!`, `@`, `$`); `End` is a
control, not a word character. Fixed-length 8-symbol space = `29^8 = 500,246,412,961`
(≈5.0×10¹¹); including all shorter lengths 1..8 gives `518,112,356,280`. There is no
checksum, key table, permutation, or encoding layer — the validator compares raw ASCII.

**Validator model / space closure.** `0x08006A44`–`0x08006A8A` contains exactly three `strcmp`
calls followed by a single `str r0,[r1]`; the fall-through at `0x08006A92` writes no flag.
I ran the game's own validator indirectly over its whole branch chain by (a) reading every
literal in the chain and the three string constants, and (b) entering all three accepted
words plus one out-of-set word on the real screen with RAM reads. **Accepted set size = 3,
exactly.** Density in the 8-symbol space ≈ 6.0×10⁻¹².

**Novel code.** None can exist: this is a closed three-string lookup, not a generated/
checksummed format, so there is no 4th value to mint. Rather than claim a nonexistent novel
code, the negative is *bounded and counted*: 3 literals in the entire validator chain
(`0x087F20B0/BC/C8`), all 3 exercised and accepted in-game, one non-member exercised and
rejected. A ROM-wide scan found only these three strings using the keypad's punctuation
(`!`/`@`/`$`), so there is no additional hidden word. This is a "no algorithmic code space"
result (guide §16.3: **no system beyond the closed set**), not an untested gap.

**Rejection bounds proven in-game.**
* `ZZZZZZZZ` (fully manual keypad entry, `typed_lil2`-style sequence): accepted as the Horse
  word only; flags at `0x020099D8/DC/E0` all remained `0`; no menu/level/rider unlocked
  (`manual_submit.png`).
* Case/character space: literals are exact ASCII including `!` and `@`; a single changed
  character fails the corresponding `strcmp` (direct consequence of the disassembly).
* No button-code table found: a scan of the first 1 MiB for runs of ≥4 consecutive 10-bit
  GBA key masks produced 17 coincidental data runs, none a plausible cheat sequence; no
  alternate debug menu was reached on any of the walked screens.

**Codes absent from published lists.** Four web searches for this SKU's GBA passwords
returned no results at all; therefore no public list was available to compare against. The
three words above are reported as the complete native set, not as reproductions of a
published list.

## 7. Validation evidence

* **Observed** (emulator): `!HAXORED` set `0x020099D8 = 1` (watchpoint at `0x087F20B0` hit
  inside `strcmp` at PC `0x0802D966`, LR `0x08006A4F`, buffer `r2=0x020098A0`); OPTIONS
  `CHEATS` changed from grey (`s7.png`) to bright (`opts_unlocked.png`); CHEATS MENU
  enumerated with 8 rows and PERFECT BALANCE toggled ON.
* **Observed** (emulator): `GMAN@DEF` set `0x020099DC = 1`; LEVEL SELECT gained the 7th
  landscape OCEAN WORLD (`levelnames.png` vs `levelnames_base.png`).
* **Observed** (emulator): `LILBURNT` — entered **entirely with xdotool keypad presses**
  (`typeword2.py`, 55 keypresses, `typed_lil2.png`) — set `0x020099E0 = 1` on submit
  (`lil_manual_submitted.png`); riders LIL and P appeared in SELECT RIDER
  (`lil_unlocked_full.png`). For the other two words, the 8-byte buffer was written with
  mGBA's debugger `w/1` and the word was then submitted with A on the real screen; the flag
  write was performed by the game's own code.
* **Derived**: validator chain `0x08006A38`–`0x08006A90`; `JUDGEAVAILABILITY` name/flag
  mapping at `0x0800B338`/`B39C`/`B40C`; script screen definitions and CHEATS row list.
* **Inferred**: the exact gameplay effect of each CHEATS MENU toggle beyond its ON/OFF
  label was not played out in a race.

## 8. Unknowns

* Whether the unlock flags persist to SRAM (`.sav`) or are EWRAM-only until a career save;
  savestates were used for repeated experiments.
* The gameplay mechanics behind the 8 cheat toggles (only their labels and ON/OFF state
  were verified).
* No published code list exists to confirm whether fans know these three words.

## 9. Tooling

`strings -t x`, `grep -abo`, Python pointer/literal scans, `arm-none-eabi-objdump -D -b binary
-marm --adjust-vma=0x08000000 -M force-thumb`, mGBA 0.10.5 CLI debugger via Python `pty.fork`
(read watchpoint on `0x087F20B0` located the validator), mGBA savestate `gbAs` zlib-chunk
diffing (`ssdump.py`) to locate the word buffer, xdotool XTEST input (`key.sh`, `typeword2.py`),
scrot/ImageMagick for evidence frames. No ROM or copyrighted asset is redistributed here;
only addresses, hashes, and observations are published.
