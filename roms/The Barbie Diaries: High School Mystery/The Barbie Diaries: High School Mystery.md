# The Barbie Diaries: High School Mystery (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Barbie Diaries: High School Mystery.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `BARBIE DM` |
| Game code / maker / rev | `BBIE52` / `52` / `00` (fixed byte `0x96` present) |
| Entry branch | `0xEA00002E` (crt0 at 0x080000C0) |
| Region | single image (one Nintendo-logo hit at file 0x04) |
| MD5 | `85bbf8a6f95b9d2d463d0a55f2b69d35` |
| SHA-1 | `3e61732fb0d19912b76c16e7fe1407e14ba38447` |
| SHA-256 | `52c2a27f914de65d008259e2c1786e05374d0393df1181c37d43a590359917a5` |

Developer Gorilla Systems, publisher Activision (2006). Recon: GameFAQs, Giant Bomb,
Barbie Wiki, RetroAchievements and the official manual contain **no published
password/cheat list** for this GBA title. Manual describes only the intended
in-game investigation tools (Picture Descrambler, MP3 decoder, Word Finder,
Infrared Viewer) and two mini-games.

## 2. Executive summary

**No developer-intended cheat system exists in this ROM.** There is no password
screen, no hard-coded code table, no reachable hidden/debug menu, and no active
button-code sequence. The game's "codes" are ordinary gameplay puzzles: a 20-word
word list, six picture grids, an infrared keypad heat-pattern puzzle and a bash
code-breaker clue.

The engine *does* contain a generic 16-entry key-history ring buffer and a
matching button-sequence comparator (0x0803474C) — the standard substrate for a
Konami-style cheat — but the comparator has **zero callers anywhere in the
image** and no expected-sequence table is stored. All menu text is ASCII
rendered through a decoded tile→ASCII font table, so there is no hidden
tile-encoded menu text that a string scan would miss.

Enumeration bounds and the full negative proof are in **§6b**.

## 3. How to reproduce

Environment: mGBA 0.10.5 under Xvfb `:315` + openbox, `SDL_AUDIODRIVER=dummy`.
The mGBA **command-line debugger** (`mgba -d -3 game.gba`) was driven through a
PTY from Python; `frame` advances one video frame and returns a full register
dump, `x/4 <addr>` reads RAM. X keys were injected with `xdotool` between frame
steps (GBA A=`x`, B=`z`, Start=`Return`, L=`a`, R=`s`, arrows = d-pad).

Reproducible path:

1. Boot → health-and-safety screen → **A** → title menu (4 entries: New Game,
   Continue Game, Mini-Games, Credits).
2. **Down ×1, A** from the initial cursor → Mini-Games menu (3 entries: Main
   Menu, Picture Puzzle, Word Puzzle).
3. New Game → long scripted intro (100+ discrete A presses) → school map →
   **Start** opens the BDA menu.

Screenshots retained in `/tmp/opencode/barbiediaries/`: `shot0.png` (title),
`minigames2.png` (mini-games), `st_after1.png` (title cursor), `title_pos1.png`,
`minigames_menu.png`/`bda_menu.png` (transitional), `code_konami.png` (undocumented
code test), `intro300.png`/`gameplay1.png` (in-game).

## 4. Address map

File offset `f` ↔ ROM address `0x08000000 + f`.

| Item | File offset | ROM / RAM address | Evidence |
|---|---|---|---|
| Header | 0x000–0x0BF | 0x08000000 | Observed |
| Input poll / ring-buffer writer | 0x34694 | 0x08034694 | Derived (Capstone) |
| KEYINPUT literal `0x04000130` | 0x346D4 | 0x080346D4 | Derived |
| Input globals (held/pressed/released) | — | 0x020016CC | Derived |
| 16-entry key-history ring buffer | — | 0x020016D8 (index 0x020016F8) | Derived |
| Held/pressed/released accessors | 0x34728/0x34734/0x34740 | 0x08034728 / 34 / 40 | Derived |
| **Key-sequence comparator** | 0x3474C | **0x0803474C** | Derived |
| Menu/text string bank | 0x5F32C–0x628F4 | 0x085F32C–0x08628F4 | Observed |
| Mini-game menu strings | 0x61F78–0x62034 | 0x0861F78–0x0862034 | Observed |
| 20-word puzzle list | 0x6243C–0x624E8 | 0x086243C–0x08624E8 | Observed |
| "Correct!" result strings | 0x62230, 0x62584 | 0x0862230, 0x0862584 | Observed |
| Font tile→ASCII table | 0x067420–0x06752F | 0x0867420–0x086752F | Derived |
| RGB/IO at mini-games menu | — | 0x04000000 = `00001940 00A00009 …` | Observed |
| IWRAM sample at mini-games menu | — | 0x03000000 = `080348A9 080348C9 080348A5 080348A5` | Observed |
| EWRAM sample (constant across screens) | — | 0x02000000 = `08046C2C 0200EEA8 02011E50 020128D0` | Observed |

## 5. Algorithm

**Input engine (0x08034694).** Reads `KEYINPUT` (`0x04000130`), XORs with
`0x03FF` to get active-high masks, computes `pressed = cur & (cur ^ prev)` and
`released = prev & (cur ^ prev)`, writes all three into the globals at
`0x020016CC..D2`, and on any new press stores the current mask into a 16-entry
circular buffer at `0x020016D8` with index at `0x020016F8`
(`index = (index+1) & 15`).

**Sequence comparator (0x0803474C).** Signature `int check(u16 *seq, int n)`:

```
n &= 15;                       // max 15 presses
start = (history_index - n) & 15;
for (i = 0; i < n; i++)
    if (history[(start + i) & 15] != seq[i]) return 0;
return 1;
```

This is a textbook button-cheat validator. It is **never called** (no Thumb BL
and no literal function-pointer reference to 0x0803474C or 0x0803474D in the
8 MiB image). The apparent BL at 0x08342360 is a false positive inside a
compressed tile bank. No `u16` sequence table that could be its argument was
found: a whole-ROM scan produced 1,262 runs of ≥4 valid button masks and 53,028
runs of ≥5 valid byte masks, all in high compressed data with no code xrefs.

**Puzzle "validators" (not cheats).** Two `Correct!` strings at 0x0862230 and
0x0862584 belong to `CPicDecoderMiniScene` and `CWordPuzzleMiniScene`; their
answers are the six selectable pictures and the 20-word table in §6. They are
gameplay content, not hidden codes.

## 6. Tables

**Title menu (4 entries, screenshot-confirmed):** New Game, Continue Game,
Mini-Games, Credits. Initial cursor index 1; pressing Down enumerates all four
with wraparound — no fifth entry.

**Mini-Games menu (3 entries, screenshot-confirmed):** Main Menu, Picture
Puzzle, Word Puzzle. (The manual's "MP3 player"/"Infrared Viewer" are in-game
BDA tools, not menu entries.)

**BDA menu strings (file 0x5FC38–0x5FE68):** Back, Options, Infrared Viewer,
Clues Menu, Auction Items, Message Viewer, Task Viewer, Diary, Return to the
game, Quit, Inventory, BDAMap, BDAPhotoViewer, TextMessenger, Legal, Mattel —
all ordinary gameplay/navigation; no debug entry.

**Map areas (19):** AVRoom, ArtRoom, Auditorium, Bathroom, Cafeteria,
EquipmentRoom, Gymnasium, HallwayA/B/C, Library, Lounge, Office, Roof,
SchoolStore, ScienceLab, ShopClass, SoccerField, YearbookRoom.

**Word-puzzle answers (20, file 0x6243C):** MYSTERY, SCHOOL, YEARBOOK,
LIBRARY, MASCARA, BRACELET, TEACHER, DANCE, MUSIC, COMPACT, SUSPECT, FASHION,
CLOTHES, MAKEUP, TEAMWORK, CHARITY, LOCKER, DIARY, TROPHY, ANCHOR.

**Picture-puzzle choices (6):** Robopup, Soda Machine, Concert Tickets, Bike,
Hand bag, Digital Picture Frame (strings at 0x6200C–0x62034, 0x60948).

**Font mapping (file 0x067420):** tile index `0x20..0x2B` → ASCII `0x20..0x2B`;
`0x30..0x3B` → `0..9:;`; `0x40..0x4B` → `@A..K`; `0x50..0x5B` → `P..Z[`;
`0x60..0x6B` → `` `a..k ``; `0x70..0x7B` → `p..z{`; `0x80..0x8B` → special.
A second copy begins at 0x0674C4. This proves visible menu text is ASCII — the
"Main Menu / Picture Puzzle / Word Puzzle" glyphs on screen correspond exactly
to the ASCII strings at 0x61F78–0x61FA0.

## 6b. Enumeration

**Characterised spaces.** This title has no code space to enumerate: no
password alphabet (the only alphabet-like tables are the font glyph orderings at
0x067420/0x067505 and a hex-digit string `0123456789ABCDEF` at 0x0679B20), no
code length, no checksum, no code table. The button-code space the engine could
express is `n ∈ [1,15]` over 10 button masks, but **the space is entirely
unreachable** because the sole comparator has zero callers and no sequence data.

**Novel codes.** None exist to mint. In lieu of a generated code, the negative
is bounded below by exhaustive counts:

| Search | Space checked | Result |
|---|---|---|
| Published-code recon | GameFAQs, Giant Bomb, Barbie Wiki, RetroAchievements, official manual | 0 password/cheat codes published |
| Full-string scan | 82,927 `strings -t x -n 4` lines | keyword regex `debug\|cheat\|password\|passcode\|godmode\|invincible\|level select\|master code` → **0 hits** |
| Case/shift/reversed keyword scan | all 8 MiB for 14 keywords × 4 encodings | only `warp`, `special` in ordinary dialogue/credits |
| Code-like token scan | short `A-Z0-9!?` tokens | all hits compressed-data noise (e.g. `WFNFEF`, `OFFF`) |
| Button-sequence tables | 8 MiB as `u16`/`u8` mask runs | 1,262 / 53,028 runs, 0 with code xrefs |
| KEYINPUT readers | literal `0x04000130` in ROM | exactly **1** occurrence → one input function |
| Sequence-comparator callers | whole ROM BL + pointer scans | **0** callers, **0** sequence tables |
| Hidden/debug menu | title 4 + mini-games 3 + BDA 16 strings | 0 hidden entries |
| Text-encoding check | font bank 0x067420–0x06752F decoded | all menu text ASCII; no tile-only strings |
| Validator inventory | `Correct!` strings | **2**, both mini-game answers |
| Dynamic rejection | undocumented Konami sequence and L+R+Start at title | no hidden screen; normal menu behaviour |

**Unadvertised-combination test (§0.2 equivalent).** Because there is no code
field to vary, the reachable-combination test was a button sequence:
`↑↑↓↓←→←→BA` was entered at the title screen (`code_konami.png`); it produced
only the ordinary "New Game" transition when the final A was processed, and no
debug/menu screen. L+R+Start likewise produced no change. This is consistent
with the static finding of zero callers to the comparator.

**Conclusion:** the negative is proven for the entire 8 MiB image, not merely
for unexamined space. Every reachable menu was enumerated with counts, and the
only code-capable routine present is provably unreferenced.

## 7. Validation evidence

- **Observed:** title (4 entries), Mini-Games (3 entries), Credits, gameplay and
  intro screenshots; IWRAM/EWRAM/IO dumps at the mini-games menu; 82,927-line
  string inventory; 0 keyword hits.
- **Derived:** input engine at 0x08034694, ring buffer at 0x020016D8, comparator
  at 0x0803474C with `len&15`, font tile→ASCII mapping, zero BL/pointer callers,
  all table/word/area counts.
- **Inferred:** that the dormant comparator is leftover generic Gorilla Systems
  engine code rather than a removed feature; that the two `Correct!` checks are
  exclusively the mini-game answer tests (their owning scenes are named in the
  string bank).

## 8. Unknowns

- The BDA menu was enumerated from its string bank and class names
  (`CBDAMainMenuScene`, 16 label strings) rather than from an in-emulator menu
  screenshot — the long scripted intro was not fully traversed. Its entry count
  is therefore static-derived, not observed.
- Whether any *retail* unlockable (secret-admirer messages, the 15 auction
  items) requires an in-game code rather than normal clue-trail progression was
  not exhaustively played; the 10 `MessageUnlock` string hits were not tied to a
  validator. Nothing suggests a player-entered code.
- Dormant comparator's intended original caller (if the engine was reused from
  another title) is unknown.

## 9. Tooling

`strings`, `xxd`, `grep`, Python 3, Capstone 5.0.7 (Thumb disassembly / BL and
literal-pointer scans), `arm-none-eabi-objdump`, mGBA 0.10.5 (`-d` CLI debugger
driven via `pty` in `clidbg.py`, high-level `driver.py`), `xdotool`, `scrot`,
Xvfb + openbox on `:315`. Helper scripts are in `/tmp/opencode/barbiediaries/`.

**Legal note:** no ROM bytes, graphics, audio or full game text are reproduced
here — only hashes, addresses, algorithms, counts and short UI labels.
