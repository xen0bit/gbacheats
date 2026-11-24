# Street Jam Basketball (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Street Jam Basketball/Street Jam Basketball.gba` |
| Size | 4,194,304 bytes (0x00400000, 4 MiB) |
| Header title | `STREETJAM` |
| Game code | `A3ZE` (maker `20`, fixed `0x96`) |
| Version | 0x00; complement 0x2D; header checksum 0x0000 (rebuilt-header artifact) |
| Entry word | `0xEA00002E` (stock branch — **not** a cracktro/patched entry) |
| MD5 | `482e89458d0154ec7231e98c61378c0a` |
| SHA-1 | `7716d661cc8027f2a59c53dbf301365b82e86624` |
| SHA-256 | `7b025d0a469a0ced57b66c5036c611a3e9741dba4c83968dd3ccbb935c4bacd1` |
| Splash / credits | "Copyright 2003 ProGraph Research S.r.l."; "RESEARCH SRL", "DISTRIBUTED BY DESTINATION SOFTWARE INC", "DSI GAMES" |

Single retail image: one Nintendo logo / one header, no multiboot or 2-in-1 shell (§16.1, §5.4b checks passed).

## 2. Executive summary

**Bounded negative (§0.2 case 5): this SKU has no developer-intended in-game cheat surface.**
No password screen, no button-code, no hidden/debug menu, and no code-gated unlockable exists
on any reachable screen. The game is a 2003 3-on-3 street-basketball title with SRAM saves
(512-byte `.sav`, 5 named slots), so it has no need for a password/continue-code system.

What the search *did* find are three things that look like cheat systems but are not:

1. `LOSER / DUMMY / ROOKIE / BOSS / PRO / KING` at `0x080410F4`–`0x08041118` are **score-rank
   titles**, selected by the score-comparison ladder in the Thumb function at `0x08013628`
   (thresholds 100, 280, 420, 580, 720; `r5 = 0..5`). The main-menu readout `LOSER 0000`
   is rank + score, not a cheat code or difficulty password.
2. Several `A-Z0-9…` strings (`0x080410B8`, `0x08042314`, `0x08043C40`, `0x08043C80`,
   `0x08043E38`, `0x08043EF8`) are **font/glyph remap tables** used by the text renderer
   (`0x0801306C` ASCII→glyph index, `0x080130C0` text draw), not password alphabets.
3. Fifteen team-name strings exist but only **7** are selectable; the other 8 are Story-mode
   opponents (dialogue bank names BLACKNED, THE AUTHORITY, BOSS, GANG), not unlockables.

The negative is bounded by: (a) a complete walk of all 14 reachable screens with screenshots,
(b) exhaustive ASCII/text-bank and keyword counts over all 4 MiB, (c) input-mask table scans
in 1/2/4-byte encodings plus 6 live combo tests, and (d) enumeration of every menu's return
domain. Details and counts are in §6b.

Web reconnaissance was attempted (GameFAQs direct fetch → HTTP 403; websearch and two search
engines → no results / bot challenge). No published code list could be recovered for this SKU,
so no published code was available to verify or to use as an anchor; this is recorded as a
limitation, not as evidence for or against cheats (§3.4 rule 4, §16.11).

## 3. How to reproduce

- Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy mgba -3 <rom>`, Xvfb `:319`, openbox.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold 120–150 ms; menus debounce and need ~400–600 ms between presses.
- Boot → DSI splash (~4 s) → title "PRESS START".
- Slot manager: press A on an empty slot → on-screen keyboard (A–Z, 0–7, `←` backspace, `↵`
  confirm at bottom-right of the keyboard). Enter a name, navigate Down to `↵`, press A.
  Press A again on the named slot to enter the game.
- Main menu (4 entries, Down cycles): EXHIBITION → OPTIONS → VERSUS → STORY.
  - OPTIONS (4 entries): TIME (1:00), SFX, MUSIC, CREDITS.
  - EXHIBITION / STORY → SELECT TEAM (7 teams, Left/Right) → CHOOSE YOUR OPPONENT (same 7)
    → SELECT PLAYGROUND (6 entries) → VS screen → match.
  - VERSUS → "LINK GAME" screen (requires link cable; no offline surface).
  - In match: Start → PAUSE (2 entries: CONTINUE, QUIT).
- Savestates: `Shift+F1..F9` save; states are PNG with a zlib `gbAs` chunk, decompressed to
  397,312 bytes; IWRAM appears at state offset `0x19000`, EWRAM at `0x21000`
  (§16.13). Screenshots of every state were in `/tmp/streetjam/*.png`.

## 4. Address map

All addresses are ROM virtual addresses (`0x08000000 + file offset`) unless marked RAM/state.

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Stock entry branch `0xEA00002E` | Observed (header) |
| `0x0801306C` | ASCII→font-glyph index mapper; alphabet `0x080410B8`, 38 symbols; miss → index 50 | Derived (Thumb disasm) |
| `0x080130C0` | Text draw (x, y, string, palette); writes VRAM tile indices | Derived |
| `0x08013628` | Score-rank display; compares score vs 100/280/420/580/720 → rank 0..5 | Derived |
| `0x08022280` | Joypad poll: `held = 0x03FF ^ KEYINPUT`, `pressed = held & ~old` | Derived |
| `0x03005898` (RAM) | HELD mask, active-high (A=1,B=2,Select=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,R shoulder=0x100,L shoulder=0x200) | Derived |
| `0x030058A0` (RAM) | PRESSED (newly-pressed) mask, active-high | Derived |
| `0x080410B8` | Font alphabet `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.:` | Observed |
| `0x080410F4`–`0x0804111C` | Rank strings LOSER, DUMMY, ROOKIE, BOSS, PRO, KING | Observed |
| `0x08042314` | Alphabet `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,()@'` | Observed |
| `0x08043B8C`–`0x08043C3C` | 15 NUL-terminated team names | Observed |
| `0x0803F21A8` (file `0x3F21A8`) | 15-entry little-endian pointer table into the team-name block (reverse string order) | Derived |
| `0x08043C40`, `0x08043C80` | Alphabets `…0123456789.,:!-?` + accented bytes; `…0123456789.,%()` | Observed |
| `0x08043E38`, `0x08043EF8`, `0x08043F94` | Font glyph-order tables (partial upper/lower/digit banks) | Observed |
| SRAM `+0x00` | Slot-1 save; first byte = ASCII name (`0x41` = 'A' in the test save); 512 bytes total, 5 slots | Observed |
| Savestate `+0x190E8` | Byte observed 0x00 on title/team-select, 0x04 on main menu (non-unique screen marker) | Observed |

## 5. Algorithm

There is **no password/checksum validator to reimplement**. The two relevant algorithms are:

**Input sampling** (`0x08022280`, derived from Thumb):
```
raw   = *(u16*)0x04000130                 # active-low KEYINPUT
held  = 0x03FF ^ raw
press = held & ~old_held
*(u16*)0x03005898 = held
*(u16*)0x030058A0 = press
old_held = held
```
Every game/menu input consumer reads one of these two RAM words; a button cheat would have
to compare one of them against a mask table. No such table was found (§6b).

**Score-rank ladder** (`0x08013628`, derived):
```
if score <= 100: rank = 0, text = "LOSER"
elif score <= 280: rank = 1, text = "DUMMY"
elif score <= 420: rank = 2, text = "ROOKIE"
elif score <= 580: rank = 3, text = "BOSS"
elif score <= 720: rank = 4, text = "PRO"
else:              rank = 5, text = "KING"
```
This is a display-only rank, never a gate (no branch from `r5` reaches a hidden screen in the
enumerated paths).

## 6. Tables

### 6.1 Font / text alphabets (not password alphabets)

| Address | Symbols | Count | Role |
|---|---|---:|---|
| `0x080410B8` | `A–Z 0–9 . :` | 38 | ASCII→glyph mapper used by `0x0801306C` |
| `0x08042314` | `A–Z 0–9 . , ( ) @ '` | 41 | Title/credits text bank alphabet |
| `0x08043C40` | `A–Z 0–9 . , : ! - ?` + 15 high bytes (accented glyphs) | 56 | Localised dialogue alphabet |
| `0x08043C80` | `A–Z 0–9 . , % ( )` | 39 | HUD/stat text alphabet |
| `0x08043E38`, `0x08043EF8` | partial upper/lower/digit/punctuation orders | 78 each | Font tile-order remaps |

### 6.2 Score ranks (`0x080410F4`)

| Value | String | Threshold |
|---:|---|---:|
| 0 | LOSER | score ≤ 100 |
| 1 | DUMMY | 101–280 |
| 2 | ROOKIE | 281–420 |
| 3 | BOSS | 421–580 |
| 4 | PRO | 581–720 |
| 5 | KING | > 720 |

### 6.3 Teams (15 stored, 7 selectable)

Stored order at `0x0803F21A8` (pointer table, reverse of string order):
THE AMAZING, THE FAST TRIBE, MUSA, BINGO, BLACKNED, JUBALA, 5TH AVENUE, THE AUTHORITY,
SAND PILGRIM, T.K.3., DIOS DEL SOL, SCRATCH, GOBLINS, THE 13TH DAY, ARIZONA MASTERS.

Selectable in both EXHIBITION and STORY (7, carousel order observed):
GOBLINS → JUBALA → 5TH AVENUE → DIOS DEL SOL → THE FAST TRIBE → THE 13TH DAY → THE AMAZING → wrap.
The other 8 are Story opponents (their names occur in the dialogue bank, e.g. BLACKNED at
`0x08042C08`, THE AUTHORITY at `0x08042B34`). No selection index beyond 6 was reachable in
either mode after 14 Right presses (two full cycles).

### 6.4 Playgrounds (6)

SOUTH COAST, RANDOM! (the `?` tile), TRUCK PARK, DOWN TOWN, SKYSCRAPER, AIRPORT. The `?` is
the RANDOM selector, not a hidden court (confirmed after 10 Right presses = 1.67 cycles).

### 6.5 Menus

| Screen | Entries | Evidence |
|---|---:|---|
| Main menu | 4: EXHIBITION, OPTIONS, VERSUS, STORY | Observed (Down×5 wraps) |
| OPTIONS | 4: TIME, SFX, MUSIC, CREDITS | Observed |
| PAUSE | 2: CONTINUE, QUIT | Observed (Down×2 wraps) |
| Slot manager | 5 slots + clipboard/trash icons | Observed |
| Name-entry keyboard | A–Z, 0–7, `←`, `↵` | Observed |

## 6b. Enumeration

**Space definition for the searched surfaces (all counts are for this exact hash):**

| Surface | Space searched | Result |
|---|---|---|
| Reachable screens | 14 distinct states walked (boot splash, title, slot manager, name entry, main menu, OPTIONS, CREDITS, SELECT TEAM, OPPONENT SELECT, SELECT PLAYGROUND, LINK GAME, VS, match, PAUSE) | 0 hidden screens, 0 hidden menu entries |
| Menu return domains | main 4, OPTIONS 4, PAUSE 2, team 7, opponent 7, playground 6, slots 5 | fully enumerated; all wrap, no unlabelled 5th/8th entry |
| Text banks | all `strings -n 4` output = 28,357 runs; every ASCII run in `0x040000–0x045000` dumped (≈500 real strings) | 15 team names, 6 ranks, 6 alphabets/glyph tables, 5 language dialogue banks (EN/IT/DE/FR/ES) |
| Cheat keywords | 20 patterns (PASSWORD, CHEAT, DEBUG, SECRET, UNLOCK, BONUS, HIDDEN, EXTRA, CODE ENTRY, LEVEL/STAGE SELECT, SOUND TEST, WARP, MAP SELECT, …), case-insensitive, whole 4 MiB | **0 hits each** |
| Hard-coded name cheats | 24 candidate names (GOD, KING, DEBUG, CHEAT, SECRET, XXX, TEST, …) in upper+lower ASCII | 0 validator-like hits (hits were rank strings, credits names, team names, graphics noise) |
| Password validators | 32-bit pointers to each of 6 alphabet bases (incl. Thumb-bit `addr\|1`) | hit counts: ALPHA1 1, ALPHA2 2, ALPHA3 1, ALPHA4 1, FONT1 0, FONT2 0 — all consumers are text rendering (`0x0801306C`/`0x080130C0`), none compares user input |
| Button-code tables | Konami `UUDDLRLRBA`, `LRLR`, `UUDD`, `Start+Select`, `L+R+Start`, `A+B+Start`; 1-, 2-, 4-byte masks, both endian, forward+reversed | no plausible table; all 10 hits were random code/font bytes (e.g. `0x043FC0` = `40 40 80 80` inside a font table) |
| Live combo tests | 6 combos at title and 6 at PAUSE: L+R, Select+Start, L+R+Start, A+B+Start, L+R+Select, `UUDDLRLRB A` | 0 visual change, 0 new screen; title combos only moved the slot-manager cursor |
| Input consumers | 15 references to HELD `0x03005898`, 49 to PRESSED `0x030058A0`; scanned for `cmp/tst` with key-mask immediates | no compound-mask gate (no `0x300`, `0x0C`, `0x03`, `0x1FF` comparisons) |
| Unlockables | 15 team names vs 7 selectable; 6 playgrounds; 512-byte SRAM with 5 slots | 8 non-selectable teams are Story opponents; no unlock flag observed in save bytes |

**Novel code:** not applicable — no code system exists to mint. Per §0.2, a generated code is
required only when a validator/table exists; here the deliverable is the bounded negative above.

**Bounds proven by rejection:** the two candidate "codes" that a player might try were tested:
entering the name `AAAA` in slot 1 produced only a save-slot label (no unlock); pressing the
6 common button combos on title and PAUSE produced no state change. Both are observed rejections
of the hypothesis that these surfaces are cheat gates.

**Why the ASCII keyword count is not the whole proof:** visible menu labels (EXHIBITION,
OPTIONS, PRESS START, SELECT TEAM) do not occur in ROM as ASCII in any simple encoding
(plain, ±0x20, UTF-16LE/BE, reversed — all 0 hits); they are baked tile graphics. The negative
therefore rests primarily on the **complete visual screen walk** (§6b row 1) plus the decoded
ASCII banks and font tables, not on the keyword scan alone. This is the §15 "not all text is
ASCII" trap handled explicitly.

## 7. Validation evidence

- **Observed** — every screenshot in `/tmp/streetjam/` (title, slot manager, name
  entry, main menu, OPTIONS, CREDITS scroll, team select ×14, opponent select ×16, playground
  ×11, VS, match, PAUSE ×3, post-combo states); ROM hashes and header; 512-byte SRAM with
  slot-1 name byte `0x41`; savestate `gbAs` chunks (397,312 bytes) and diffs.
- **Derived** — Thumb disassembly of `0x0801306C`, `0x080130C0`, `0x08013628`, `0x08022280`;
  literal-pool decodes (e.g. `0x080410F4` = LOSER, not a mis-read `0x0804F410`);
  pointer table at `0x0803F21A8`; input RAM addresses.
- **Inferred** — the 8 non-selectable teams are Story opponents (supported by dialogue-bank
  names, but a full Story playthrough to confirm each appearance was not completed); the
  name-entry field is a label, not a validator (no comparison constants found, but no full
  decompilation of the name handler was done).

## 8. Unknowns

- A full Story-mode playthrough was not completed; it could reveal a post-game unlock that is
  save-flag-gated rather than input-gated. No such flag was visible in the 512-byte SRAM after
  creating a slot and playing one match.
- Menu labels are pre-rendered tile graphics; a complete glyph-index decode of every font bank
  was not attempted. Any hidden label would have to be on a reachable screen to matter, and all
  reachable screens were walked.
- Web recon could not be completed (403 / no results / bot challenge), so "no published codes
  exist" is **not** claimed — only that none were available to verify.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `strings -t x`, `xxd`, Python 3 (byte/pointer scans,
  savestate PNG `gbAs` zlib extraction, screenshot montage).
- `capstone` (Python) for Thumb `LDR [PC]/BL` and input-consumer scans;
  `arm-none-eabi-objdump -M force-thumb` for verified disassembly.
- mGBA 0.10.5 with `SDL_AUDIODRIVER=dummy` under Xvfb `:319` + openbox; `xdotool` XTEST input;
  `scrot` + ImageMagick `convert`/`montage`.
- `gdb-multiarch` was connected to the mGBA stub once (PC read at `0x030036c8`); the stub is
  single-client and `detach` is unsupported (`E07`), and a co-running agent's process cleanup
  killed that instance, so RAM evidence was gathered from savestate diffs instead (§16.13).
- Helper scripts: `/tmp/streetjam/{ui.py,ss.py,combos.py,scan_input.py}`.

No ROM or copyrighted asset is redistributed by this report; only hashes, addresses, and
observed state are published.
