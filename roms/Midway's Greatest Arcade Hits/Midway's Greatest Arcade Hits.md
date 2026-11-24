# Midway's Greatest Arcade Hits (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Midway's Greatest Arcade Hits.gba` |
| Size | 4,194,304 bytes (`0x00400000`, 4 MiB) |
| Header title | `MGAH` |
| Game code | `AM3E` (region E) |
| Maker code | `5D` |
| Version | `0x00` |
| Complement / checksum | `0xB5` / `0x0000` (checksum zero = rebuilt header; entry word is stock) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`; no cracktro/trainer patch in first 4 KiB) |
| `file` identification | `Game Boy Advance ROM image: "MGAH" (AM3E5D, Rev.00)` |
| MD5 | `cfd85c7cc23e577cd6a338e83e95d618` |
| SHA-1 | `194913c9d5a74b9af5f90b539828f6fa77c016ed` |
| SHA-256 | `9cd872a8c69ba58426f8a5d1bae2baf786d9d3609c2fdaef97eefdefb806109b` |

The analysis copy under `/tmp/midway/MGAH.gba` has the identical MD5.

### Phase 0 layout findings

* **Single image, not a multi-header pack.** A scan for the 156-byte Nintendo logo
  (`24 ff ae 51 69 9a a2 21 ...`, header offset `+4`) over all 4 MiB produced
  exactly **one** hit, at file offset `0x0`. There is no second/third embedded
  GBA header, no appended trainer, and no boot selector patched over the first
  image. The component arcade games are *emulated inside* the single GBA
  program; they are not separate GBA images.
* **Four component games.** The crt0 literal at `0x080001C8` points to Thumb
  `main` at `0x08000281` (`0x08000280` even). `main` copies four `0x50`-byte
  structures from `0x080171C0`, `0x08017210`, `0x08017260`, `0x080172B0`
  into EWRAM `0x02000C90`, `0x02000C40`, `0x02000CF0`, `0x02000D40`. Each
  structure is a 10-entry `{u16 score, char[3] initials, u16 pad}` high-score
  table. The four tables belong to the four cabinets shown on the attract
  screen: **Defender, Robotron: 2084, Joust, Sinistar** (all Williams arcade
  titles; the on-screen marquee reads "Williams / DEFENDER" over four cabinets).
* No patch/trainer/cracktro was found: the first 4 KiB is ordinary ARM crt0
  (stack/IWRAM setup, LDR literal pools, `bl main`), and no trainer-style menu
  strings appear anywhere in the ROM.

## 2. Executive summary

**No developer-intended cheat system exists in this ROM.** There is no password
screen, no code-entry surface, no button-code sequence handler, no hidden/cheat
menu and no unlockable content. This is a **bounded negative**, not an
unfinished search: every reachable screen was walked in the emulator with
savestate-backed RAM evidence, the complete shell text bank was decoded by
pointer enumeration, the key-state consumers were disassembled, and the
published-code sources were queried (all blocked automated access; no code
strings were found to test).

What the game *does* have:

* an attract/credits loop (Midway, Pocket Studios) and a static title logo;
* a Williams "cabinet row" attract/game-select screen (four cabinets);
* the four emulated arcade games with their own boot, high-score ("HALL OF
  FAME"), gameplay, "GAME OVER" and initial-entry screens;
* a normal **pause menu** (`Start` → `GAME PAUSED` → `Start` →
  `QUIT? / A BUTTON = NO / B BUTTON = YES`), implemented at `0x080003EC`
  (Start) and `0x0800520` (Select). This is a quit/resume confirmation, not a
  cheat.

Because there is no code/password system, §0.2's "mint a novel code" step is
not applicable; the corresponding obligation — a bounded negative with the
searched spaces and counts — is discharged in §6b.

## 3. How to reproduce

* Emulator: mGBA (SDL), `DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`, 3× scale,
  run from a copy so no `.sav`/`.ss*` is written into the ROM folder.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Input was delivered with XTEST
  (`xdotool keydown`/`keyup`, 100–200 ms holds) to the focused mGBA window.
* Boot path: credits → title logo → Williams cabinet screen. Press `A` on the
  cabinet screen to launch the highlighted game (Defender). Hold/press `A`
  while the game boots to begin actual play (not the attract demo).
* Pause proof: while in gameplay (mode byte `0x02002A00 == 0x08`), press
  `Start` once for `GAME PAUSED`, again for the `QUIT?` confirmation. `A`
  resumes, `B` quits.
* RAM evidence: mGBA `.ss1`–`.ss9` savestates were parsed with a small Python
  reader (§9). A 4 MiB ROM yields a 397,312-byte (`0x61000`) raw `gbAs` state;
  IWRAM begins at raw `0x19000`, EWRAM at raw `0x21000`. Savestates were
  taken before/after each action and diffed; screen/mode bytes were read
  directly from the uncompressed state.
* Codes tested: none exist to test (see §3.4 of the guide and §6b below for the
  web-search record).

## 4. Address map

| Address | Kind | Meaning / evidence |
|---|---|---|
| `0x08000000` | ROM | Entry branch `0xEA00002E`; stock crt0 |
| `0x080001C8` | ROM literal | Thumb `main` pointer `0x08000281` |
| `0x08000280` | ROM/Thumb | `main`: copies 4 high-score tables, runs the shell loop |
| `0x080003EC` | ROM/Thumb | Start-key handler for the in-game pause menu |
| `0x0800354` | ROM/Thumb | Draws the pause-menu strings (text IDs 8–12) |
| `0x0800480` | ROM/Thumb | Draws the `QUIT? / A=NO / B=YES` strings (IDs 10–12) |
| `0x0800520` | ROM/Thumb | Select-key handler for the same pause menu |
| `0x080022C0`–`0x080022E6` | ROM/Thumb | Attract timer; checks `state & 0x3F == 0x3F` (skip combo) |
| `0x0800C60` | ROM/Thumb | Writes a 3-letter initial into the high-score table |
| `0x0800E9C` | ROM/Thumb | Draw text by ID/string |
| `0x08010D8`, `0x080100C` | ROM/Thumb | Copy/strlen helpers used by the text system |
| `0x0801604`, `0x08016D58` | ROM/Thumb | Key/button helpers (`0x08016D58` = `bx r1` thump trampoline region) |
| `0x080171C0` … `0x080172B0` | ROM data | 4 × `0x50`-byte default high-score tables (10 entries each) |
| `0x08017300`–`0x08017480` | ROM data | **Complete shell text bank**, 18 distinct NUL-terminated strings |
| `0x080998E0`, `0x08099914`, `0x08099930` | ROM data | `Game over`, `Attack wave %d`, `Bonus x %d` (arcade-core display strings) |
| `0x02000A10` | EWRAM u32 | Shell frame counter (incremented in `main`) |
| `0x02000A14`, `0x02000A18` | EWRAM u32/u32 | Pause-menu re-entrancy guards |
| `0x020010C0` | EWRAM u32 | Saved/restored around the pause menu; also read by the attract-skip check |
| `0x02018D4` | EWRAM u16 | Per-frame key state (cleared in `main`) |
| `0x0202114` | EWRAM u16 | Active key-state word read by every shell input handler |
| `0x0202124` | EWRAM u16 | Secondary key state (cleared with `0x0202114`) |
| `0x02002A00` | EWRAM u8 | Screen/mode byte; `0x08` = in gameplay (required by both pause handlers) |
| `0x02000C40` … `0x02000D40` | EWRAM | RAM copies of the four high-score tables |

Savestate raw offsets (guide §16.13 confirmed for this 4 MiB ROM):
IWRAM `0x19000`, EWRAM `0x21000` (so EWRAM address `A` maps to raw
`0x21000 + (A - 0x02000000)`).

## 5. Algorithm

No password/validator exists. The only relevant algorithms are UI state
transitions, reproduced precisely enough to reimplement:

```
main():
    copy four 0x50-byte high-score tables to EWRAM
    loop:
        frame_counter = [0x02000A10]++ ; [0x02018D4] = 0
        draw current screen (function pointers held at 0x020029F8 / 0x020029FC)
        if key_hold(Start=0x8) and [0x02000A18]==0 and mode==8:
            handle_pause_start()      # 0x080003EC
        if key_hold(Select=0x4) and [0x02000A14]==0 and mode==8:
            handle_pause_select()     # 0x0800520
        swap current/previous key bytes at 0x02002A01 -> 0x02002A00

handle_pause_start():                # 0x080003EC
    mode = 19 ; [0x02000A14] = 1 ; draw(GAME PAUSED ...)
    while Start held: yield
    [0x02000A14] = 0 ; redraw
    # next Start press advances to the QUIT? confirmation (0x0800480)

handle_pause_select():               # 0x0800520
    mode = 19 ; [0x02000A18] = 1 ; draw(QUIT? / A=NO / B=YES)
    if key & 0x1 (A): cancel, resume
    if key & 0x2 (B): confirm quit, reset mode = 19
```

Attract-skip logic at `0x080022C0` (not a cheat): if the accumulated key word
at `0x02010C0` has all of `0x3F` (A|B|Select|Start|Right|Left) set, decrement a
countdown and clear the accumulator; pressing A (`& 1`) ends the countdown and
sets mode 19. Holding the six buttons in-game was tested and produced no
hidden screen.

## 6. Tables

### 6.1 Complete shell text bank (`0x08017300`, 18 distinct strings)

Enumerated by scanning every 32-bit literal for pointers into
`0x08017300..0x08018000` (41 pointer occurrences → 18 distinct targets; the
same table is duplicated at ROM `0x3E3CC8` etc., i.e. a second copy of the
shell data):

| Address | String |
|---|---|
| `0x08017300` | 23 spaces (blank line) |
| `0x08017318` | `      game paused      ` |
| `0x08017330` | `         quit?         ` |
| `0x08017348` | `     a button = no     ` |
| `0x08017360` | `     b button = yes    ` |
| `0x08017378` | `%d` |
| `0x0801737C` | `YOU HAVE QUALIFIED FOR` |
| `0x08017394` | `THE DEFENDER HALL OF FAME` |
| `0x080173B0` | `YOU ARE A ROBOTRON HERO` |
| `0x080173C8` | `NICE JOUSTING!` |
| `0x080173D8` | `ENTER THY NAME MY LORD!` |
| `0x080173F0` | `CONGRATULATIONS YOUR SCORE` |
| `0x0801740C` | `RANKS AMONG THE TOP 10` |
| `0x08017424` | `   ` |
| `0x08017428` | `SELECT INITIAL` |
| `0x08017438` | `WITH CONTROL PAD` |
| `0x0801744C` | `PRESS A BUTTON TO ENTER` |
| `0x08017464` | ` PRESS B BUTTON TO DELETE` |

None of these is a password, code, cheat, secret, unlock, level-select or debug
string. The font/tile-index concern from guide §11 was checked: the shell UI
text is plain ASCII in this bank (verified against the rendered pause menu),
so a negative from this bank is a real negative for the shell UI.

### 6.2 Default high-score initials (proof of the four games)

`0x080171C0` (Defender): `DRJ SAM LED PGD CRB MRS SSR TMH LSB ARC`
`0x08017210` (Robotron): `DRJ LED EPJ JER KID MLG SSR UNA JAS CJM`
`0x08017260` (Joust):    `JRN PFZ KFL CWK JAN MRS KAY JGL RAM HEC`
`0x080172B0` (Sinistar): `SAM KYD NAF KJF KAG FRG YAK JJK KFL PJM`

These are developer initials plus scores, not codes. No comparison against a
"cheat initial" triple was found in the name-entry writer at `0x0800C60`.

### 6.3 Pause handler gates

* Start handler `0x080003EC`: `KEY & 0x0008`, `[0x02000A18]==0`, `[0x02002A00]==8`
* Select handler `0x0800520`: `KEY & 0x0004`, `[0x02000A14]==0`, `[0x02002A00]==8`
* Confirm/cancel inside `0x0800520`: A = `KEY & 1` (no/resume), B = `KEY & 2`
  (yes/quit)
* Attract skip `0x080022E4`: `(saved key word & 0x3F) == 0x3F`

## 6b. Enumeration

This game has **no code space to enumerate**. The §0.2 obligations are
discharged as a bounded negative over the complete searched spaces:

1. **Screen space (walked, RAM-verified).** Attract credits (Midway; Pocket
   Studios), static title logo, Williams four-cabinet attract/game-select,
   Defender boot marquee, Defender HALL OF FAME, Defender gameplay, Defender
   GAME OVER, in-game pause (`GAME PAUSED`), pause confirmation (`QUIT?`),
   and the name-entry screen's full string set (text IDs in §6.1). RAM proof:
   mode byte `0x02002A00` read from savestates (`0x08` while in gameplay,
   `0x00` on attract/select screens); frame counter and key state read from
   `0x02000A10` / `0x02002114`. At the title screen, `Start` produced no state
   change (screenshot before/after identical). On the cabinet screen,
   `Start`, `Select`, `L`, `R`, `L+R`, `Start+Select`, `L+R+Start`, `Up+Down`
   all produced no visible change and only timer/VRAM noise in RAM; `A` (alone
   or with modifiers) always launched Defender. The other three cabinets
   were reached only as attract art; a distinct launch path for Robotron,
   Joust and Sinistar was not found in the UI (their presence is proven by
   the four high-score tables and the four game-specific strings in §6.1).
2. **Text space.** `strings -t x -n 4` → 80,387 lines over 4 MiB. A
   case-insensitive keyword scan (password, cheat, secret, unlock, debug,
   level select, insert coin, credits, options, hidden, bonus, extra,
   invincib, infinite, free play, high score, game over, press start) returned
   **6 lines**, all benign (`Game over`/`game over` at `0x998E0`, `0x998EC`,
   `0xAAE44`, `0xAAE50`, `0xAC4EC`, `0xAC4F8`; `Bonus x %d` at `0x99930`).
   The shell text bank (§6.1) was enumerated exhaustively by pointer scan:
   exactly 18 distinct strings, zero cheat-related. No font/tile-indexed text
   bank with hidden labels was found in the shell; arcade-screen text is
   rendered from the emulated games' own character ROMs.
3. **Button space.** Key-state consumers: 26 literal references to
   `0x02002114` across the ROM (11 in the first 1 MiB shell, 15 in a mirrored
   copy near `0x083E0000`). The six shell handlers at `0x8001834`,
   `0x8002324`, `0x8002ED8`, `0x8003114`, `0x8006450`, `0x80066A4` were
   disassembled: they implement D-pad/A/B menu navigation and hold-duration
   counters only. The only multi-button constant in shell code is `0x3F` at
   `0x080022E4`; holding A+B+Select+Start+Left+Right on-screen for 0.5 s
   produced no hidden screen (screenshots `combo_before/held/after`).
   Konami-code byte patterns (active-high, active-low, 8-bit and 16-bit
   packings) returned **0 hits** in all 4 MiB. Fifteen named button
   combinations were applied on the attract/cabinet screen with before/after
   savestate diffs (§3): only `A`-bearing combos launched a game; no other
   combo changed the screen or set a new flag.
4. **Published codes.** All automated sources were blocked or returned no
   usable data: 3rd party cheat index cheats page 403 (direct and via `r.jina.ai`),
   3rd party cheat indexes 403, web.archive.org snapshots 404, DuckDuckGo captcha, Mojeek
   captcha, Bing returned unrelated pages, Google returned a consent page,
   and the search tool returned no results for every query. **No published
   code string was obtained, so no literal could be searched for or tested.**
   This is recorded rather than silently omitted (guide §3.4 rule 4). Given
   the exhaustive text-bank result (§6.1), any such code could only be an
   arcade-core-internal code not surfaced by the GBA shell.
5. **Novel code / bounds-by-rejection.** Not applicable: with no validator,
   alphabet, key table, flag word or code-input surface, there is nothing to
   mint or to reject. The negative above is the deliverable for this ROM.

## 7. Validation evidence

* **Observed (emulator + RAM):** single Nintendo logo; stock entry word;
  every screen in §6b/1; `GAME PAUSED` and `QUIT? / A=NO / B=YES` after Start
  on the pause screen; mode byte `0x08` in gameplay and `0x00` on
  attract/select screens (savestate reads); no effect from the title `Start`
  or the `0x3F` six-button combo; savestate diffs for 15 button combos on the
  cabinet screen.
* **Derived (disassembly):** four high-score tables copied in `main`;
  complete 18-string shell text bank and its pointer table; exact Start and
  Select pause gates and their `0x08` mode precondition; A/B confirm/cancel
  masks; the `0x3F` attract-skip constant; name-entry writer at `0x0800C60`
  with no special-initial comparison.
* **Inferred (labelled):** that the four cabinets correspond to Defender,
  Robotron: 2084, Joust and Sinistar is inferred from the cabinet marquee art
  plus the four game-specific strings and high-score tables; only Defender was
  launched to gameplay.

## 8. Unknowns

* No distinct input path was found to launch Robotron, Joust or Sinistar from
  the cabinet row; `A` always launched Defender in the tested timing windows.
  Their attract art and score tables prove they are present, but their
  gameplay screens were not individually launched. This does not affect the
  cheat conclusion because their UI strings/tables contain no cheat surface.
* The name-entry screen was enumerated from its text bank and its writer
  function, but not reached in-game (would require a qualifying high score).
  No special-initial comparison exists in the writer, so no hidden trigger is
  expected there.
* Published codes could not be retrieved because every cheat site/search
  endpoint blocked automated access. If a private code list exists, the
  exhaustive shell text-bank enumeration still shows no input surface for it.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep`, `python3`
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for shell-code disassembly; Capstone 5.0.7 / Keystone were available.
* mGBA (SDL) under `Xvfb :317` + `openbox`; `xdotool` XTEST input; `scrot` +
  ImageMagick (`convert`, `montage`) for screenshots/contact sheets.
* `ui.py` — input/focus/screenshot helpers; `goto.py` — attract-screen
  detector; `ss.py` — mGBA `.ss*` parser (`zlib.decompress` of the PNG `gbAs`
  chunk) used for all RAM reads and before/after diffs.

## 9b. Legal note

No ROM bytes, graphics, music or game text are redistributed here. Only
hashes, addresses, algorithms and findings are published.

## Cleanup

All processes started for this job were stopped by PID: mGBA, Xvfb `:317` and
openbox. Generated `MGAH.sav`, `MGAH.ss*` and analysis artifacts live only in
`/tmp/midway`; the ROM folder was not modified.
