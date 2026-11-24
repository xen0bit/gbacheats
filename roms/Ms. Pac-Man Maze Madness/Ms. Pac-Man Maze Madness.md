# Ms. Pac-Man Maze Madness (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Ms. Pac-Man Maze Madness.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `MSPAC-MANMM` |
| Game code | `BPCE` |
| Maker | `AF` |
| Version | 0x00 |
| Complement byte | 0x99 |
| Header checksum | 0x0000 |
| Entry word | `0xEA00002E` → stock `0x080000C0` |
| MD5 | `279af1b9d55efdcea19593a42f8ce23d` |
| SHA-1 | `1c28602604e760fffc09cb84db6377a9b148d103` |
| SHA-256 | `4b10ce1f8775f02604dfd020ac564d8b0cc2e0d867c4c8dcc5a0cf5a34e8a7dc` |

**Phase 0 result:** one Nintendo-logo hit at file 0x0 (the sole GBA header). No embedded
sub-images, no appended trainer, no cracktro: the entry word is the stock branch. The
complement byte 0x99 and zero checksum are header-rebuild artifacts only; no patch or
trainer code was found (scans for `GAMESHARK`, `CODEBREAKER`, `TRAINER`, `SUNHORS`,
`CRC BANDIT` all returned zero hits).

**Important context (§16.11):** the widely published cheat/unlockable information for
this title is for the N64, Dreamcast and PlayStation builds. This GBA SKU is a different
game (Full Fat, Nov 2004). Its ROM also contains large **leftover Beyblade banks** in the
shared engine: the localisation table at 0x08087700 contains `attack ring`, `weight disk`,
`blade base`, `spin gear`, `Bit Beast:`, `Let It Rip`, `Metal Ball Defense`, `Tiger Claw`,
`Phantom Hurricane`, `Fire Arrow`, `Spin Out`; the table at 0x08090B80 contains
`Go Ray!`, `Go Max!`, `Go Kai!`, `Race 24`, `Battle 8`, `Bonus Round 6`. All "unlock"
strings that a naive `strings` grep finds belong to that residue, not to Ms. Pac-Man
(see §6).

## 2. Executive summary

**This GBA ROM has no in-game developer-intended cheat system.** There is no password
screen, no password validator/table, no button-code matcher, no hidden/debug menu, and no
GBA unlockable accessible from any menu. This is a **bounded negative**, not an absence of
search: all reachable screens were walked with RAM state captured, the full text space
(118,708 strings) was searched with counts, 55 button-mask pattern/convention combinations
were scanned in the ROM, 12 runtime button combinations were tried, and every published
cheat source was checked (the only published GBA-page entries are explicitly tagged N64 or
Dreamcast; there is no GBA code list to test).

The "cheat-looking" strings in the ROM (`Congratulations, you have unlocked `,
`Beat Par times on Episode 6, Rounds 1 to 7 to unlock`, `unlock level %d`,
`unlock last boss`, `DEBUG_AI`) were all traced: the first four live inside the leftover
Beyblade localisation/log banks, and `DEBUG_AI` is an internal assert/logging string. None
is reachable from a Ms. Pac-Man menu. Consequently §7's enumeration delivers **no novel
code** — because no code space exists — and proves the negative with screen, text, button
and source counts.

## 3. How to reproduce

- Emulator: `mgba -3 game.gba` on `Xvfb :315 -screen 0 1280x960x24`, `DISPLAY=:315`,
  `SDL_AUDIODRIVER=dummy`, `openbox` as WM.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Holds of 120–200 ms with 200–300 ms gaps; menu transitions take 2–4 s.
- Boot path: ZOO Digital Publishing logo → intro cutscene (≈28 A presses) → **MAIN MENU**.
  MAIN MENU is a 4-item ring: `VS`, `OPTIONS`, `NEW GAME` (default), `LOAD GAME`.
- Menu walk performed:
  - MAIN MENU (all 4 carousel positions, left/right) → screenshot `s_main3b.png`,
    `s_menu_left.png`, `s_menu_right.png`; state `st_main.ss1`.
  - OPTIONS → `AUDIO` (MUSIC/SFX sliders) and `CREDITS` (scrolling); `s_options` captured
    via `st_options.ss1`, `s_audio.png`, `s_credits.png`.
  - NEW GAME → world-select screen titled `CLEOPACTRA` with stars/score/time and gem icons;
    A starts its cutscene. `s_levelselect.png`, `s_level_A2.png`; state `st_levelselect.ss1`.
  - LOAD GAME → 3 slots (`- EMPTY -`), A=LOAD GAME / B=CANCEL. `s_loadgame2.png`,
    state `st_loadgame.ss1`.
  - VS → player-count ring `[back] / 2 PLAYER / 3 PLAYER / 4 PLAYER`. `s_vs2.png`,
    `s_vs4.png`, `s_vs5.png`; state `st_vs.ss1`.
  - Gameplay (Cleopactra level) → PAUSE (Resume / Exit only). `s_nav.png`, `s_pause.png`;
    states `st_nav.ss1`, `st_pause.ss1`.
- RAM-observation method: mGBA `.ss1` savestates; the PNG `gbAs` chunk is inflated with
  `zlib.decompress`, giving a 397,312-byte state with IWRAM at state offset 0x19000 and
  EWRAM at 0x21000 (§16.13). Savestates were taken on every screen; `st_*.ss1` are kept in
  `/tmp/mspacman/`. Plain F1 loads slot 1; copy a stored state over `game.ss1`
  first to restore a chosen screen.
- The screen-state RAM pair used as evidence is `(0x030001A0, 0x030002F4)` (see §4).

## 4. Address map

File offset = ROM address − 0x08000000.

| Item | ROM address | Evidence |
|---|---|---|
| GBA header | 0x08000000 | single logo hit |
| Entry branch (ARM) | 0x08000000 | `0xEA00002E` |
| Ms. Pac-Man menu string-pointer tables | 0x0808240C–0x08082CE8 | 5-language rows; `Main Menu` pointer at 0x080827DC → 0x083A30AC, `New Game` at 0x080825C4 → 0x083A2FE4, `Options` at 0x0808260C → 0x083A2F58, `Select level` at 0x08082630 → 0x083A3064 |
| World-name pointers | 0x08082654–0x080826C0 | Cleopactra / Crystal Caves / Pac Ping Harbor / Haunted Halloween |
| Save-slot UI table | 0x08082864–0x08082B70 | Load/Save/Cancel, `# Stars`, `#% Complete`, `Time #` |
| Generic Back/Select table | 0x08082CB4–0x08082CE8 | `Back`, `Select` |
| Leftover Beyblade l10n table | 0x08087700–0x08087C18 | `attack ring` … `You got:`; contains `Congratulations, you have unlocked ` at 0x0808796C → 0x083AAB38 and `Credits` at 0x0808798C → 0x083AAB8C |
| Leftover Beyblade level/button table | 0x08090B80–0x08090E80 | `Episode 6`, `Bonus Round 6`, `Beat Par times…to unlock` at 0x08090D48 → 0x083AC958, `Go Ray!/Max!/Kai!` |
| `DEBUG_AI` assert string | 0x083AFE98 | xref 0x08072780 in magic-word error logger (`0xDEADBEEF` check), not a menu |

### RAM states (Observed, from `.ss1` states)

| Screen | `0x030001A0` | `0x030002F4` | State file |
|---|---:|---:|---|
| MAIN MENU | 17 (0x11) | 8 | `st_main.ss1` |
| OPTIONS | 19 | 2 | `st_options.ss1` |
| AUDIO | 20 | 3 | `st_audio.ss1` |
| CREDITS | 23 | 4 | `st_credits.ss1` |
| LOAD GAME | 19 | 6 | `st_loadgame.ss1` |
| VS (player count) | 23 | 19 | `st_vs.ss1` |
| World select (CLEOPACTRA) | 38 | 8 | `st_levelselect.ss1` |
| Gameplay | 40 | 8 | `st_nav.ss1` |
| PAUSE | 40 | 8 | `st_pause.ss1` |

The pair is unique for every screen except gameplay vs. pause; those two were separated by
the rendered PAUSE overlay in `s_pause.png`. `0x030001A0=18` was observed only as the
1–3 s fade/transition state between menus, never as a screen with its own UI.

## 5. Algorithm

Not applicable: no password validator, checksum, key table, or code-matching routine exists
in this ROM. The only "matcher" classes examined were (a) string comparisons against the
menu/UI banks and (b) key-state comparisons; see §6b for the counts and the exact negative
result.

## 6. Tables

- Main-menu ring (4 entries): `VS`, `OPTIONS`, `NEW GAME`, `LOAD GAME` — each confirmed both
  visually and by the `(0x030001A0,0x030002F4)` pair.
- OPTIONS entries (2): `AUDIO`, `CREDITS`.
- AUDIO entries (2): `MUSIC`, `SFX` (volume sliders only).
- PAUSE entries (2): `Resume`, `Exit`. **No Sound Test / Movie Player / Music Player.**
- VS ring (3 selectable + back): `2 PLAYER`, `3 PLAYER`, `4 PLAYER`, `back`.
- LOAD GAME: 3 slots, all `- EMPTY -` on the shipped save state.
- World select: `Cleopactra`, `Crystal Caves`, `Pac Ping Harbor`, `Haunted Halloween`
  (pointers at 0x08082654/78/9C/C0); no locked/overlay entry in the selectable ring.
- Save hardware: 512-byte `game.sav` created in the work dir (EEPROM-class).

**Published codes checked and classified (§3.4, §16.7):**

| Source | Claim | Verdict |
|---|---|---|
| Archived 3rd party cheat indexes GBA cheats page (`web.archive.org` capture 2026-01-29; direct fetch 403) | `Multiplayer Classic Mode N64`, `Movie Player / Music Player / Sound Test`, `Bonus Multi-Player Map N64` | All rows explicitly labelled **N64**, **DC** or in `Unlockables N64`/`Unlockables DC` sections. **Zero GBA entries.** Not applicable to this SKU. |
| Pac-Man Wiki / Source Gaming | Sound Test 40 stars or 14 high-score names; Movie Player 70 stars; Music Player 9 clocks; Pac-Jr./Pooka from Time Trial clocks; extra map from 50,000 in Pier Pressure | Console-version description. Disproved for GBA: the ROM contains **0** occurrences of `Sound Test`, `Movie Player`, `Music Player`, `gold star`, `gold clock`; the GBA PAUSE menu has only Resume/Exit. |
| 3rd party cheat indexes "CodeBreaker codes" (`…/cheats/segadreamcast/…`) | `Unlock All Levels 0423ED38 …`, `Have All Keys …` | Dreamcast memory-patch codes, not in-game developer codes — **out of scope** by task definition; not entered. |
| 3rd party cheat indexes GBA code lists | none found | no GBA password/button-code list exists to verify. |

No prompt-injection payload was encountered in the fetched web content; all fetched pages
were treated as data.

## 6b. Enumeration

**Result: the code space is empty — no developer-intended cheat system exists in this ROM.**
The negative is bounded by the following complete searches:

1. **Screens (runtime, RAM-verified):** 9 distinct states walked — MAIN MENU, OPTIONS,
   AUDIO, CREDITS, LOAD GAME, VS, world select, gameplay, PAUSE. Every enumerated menu
   entry was opened or visually inspected; no hidden, gated, or "?" entry appeared.
   The 4-item main ring, 2-item OPTIONS, 2-item AUDIO, 2-item PAUSE, 3+back VS ring and
   3-slot LOAD GAME were counted on screen and in their pointer tables (§4).
2. **Text space:** `strings -t x -n 3` → **118,708** strings. Case-insensitive counts:
   `password` **0**, `passcode` **0**, `cheat` **0**, `code` **1** (the debug log
   `resizeSpriteBlock: Reduce. Code needs writing.` at file 0x3D9214), `debug` **1**
   (`DEBUG_AI`, an assert string), `secret` **1** (`Secreto, secreto`, Spanish dialogue),
   `unlock` **5**, `sound test` **0**, `movie player` **0**, `music player` **0**,
   `gold star` **0**, `gold clock` **0**, `game shark` **0**, `codebreaker` **0**.
   All 5 `unlock` hits were traced: two are Beyblade bonus-round hints (0x083AC958,
   0x083ACC98, inside the table at 0x08090B80 with `Go Kai!`/`Battle 8`), one is the
   Beyblade unlock banner (0x083AAB38, in the table at 0x08087700 with `attack ring`),
   and two are internal level-load log strings (` unlock level %d` 0x083ADA50,
   ` unlock last boss` 0x083ADA84). The two `level select` hits are debug logs
   (`current level selected %d`, 0x083A2F00 / 0x083A42E8), not a menu.
3. **Text encoding check (§11):** all visible UI labels WERE found as ASCII with live
   32-bit pointer xrefs — e.g. `Main Menu` 0x083A30AC ← 0x080827DC, `New Game`
   0x083A2FE4 ← 0x080825C4, `Options` 0x083A2F58 ← 0x0808260C, `Select level`
   0x083A3064 ← 0x08082630. Therefore the UI text path is ASCII, not a font/tile-indexed
   text bank; no font-index decoding is required to make this negative, and a
   font-indexed secret-message bank is not used by any screen reached above.
4. **Button-code space (static):** 11 candidate sequences (Konami + reverse, `L+R`,
   `L+R+Start`, `Start+Select`, `A+B`, `B,B,A,A`, `L,R,L,R,A`, etc.) × 5 mask conventions
   (active-high u16, active-high u8, active-low u16, active-low u8, nibble-compressed) =
   **55 raw byte-pattern searches** over all 4 MiB. Hits occurred only in numeric/animation
   data tables (e.g. the `B,B,A,A` u16 pattern at 0x0808E848 sits in a parameter table
   `0200 0200 0100 0100 0300 0300…`; the nibble pattern at 0x080931A8 is tile/animation
   data). None is a key-state matcher table.
5. **Button-code space (runtime):** **12** input experiments from a restored main-menu
   state — `L+R+Start`, `L+R+Select`, `L+R`, `Start+Select`, `A+B+Start+Select`,
   `L+R+A+B`, `Up+Down+L+R`, `R+Start`, `L+Start`, `R+Select`, `L+Select`, and the full
   Konami sequence. The 9 combinations without A left `(17,8)` unchanged; the 3 containing
   A only advanced the ordinary menu-activation fade `(18,8)`. No hidden screen, flag, or
   counter appeared.
6. **Published codes:** the archived GBA cheat page has zero GBA codes (§6); every
   published effect is N64/DC and the GBA ROM contains no strings for the corresponding
   features. Nothing remained to enter or test.

**Bounds proven by rejection:** there is no accepted input to reject. The nearest analog to
a "range check" is the menu ring itself: the selector wraps 4→0 on MAIN MENU and 4→back on
VS, and no out-of-ring index is selectable. Away from those rings, all button inputs leave
the recorded RAM state unchanged, which is the in-game rejection of every candidate code.

## 7. Validation evidence

- **Observed:** emulator screenshots (`s_*.png`, `cmb_*.png` in `/tmp/mspacman/`)
  for all 9 screens and all 12 button experiments; RAM state pairs from 9 `.ss1` states;
  single GBA header and stock entry word from the raw file; 512-byte `game.sav`.
- **Derived:** pointer xrefs from the menu l10n tables to the ASCII UI strings (§4/§6b);
  the 55 button-mask pattern scans and their classification as data-table hits; the
  Beyblade attribution of the 0x08087700 and 0x08090B80 tables from their neighbouring
  strings.
- **Inferred:** that the Beyblade banks are shared-engine/debug residue rather than a
  playable second game — supported by the single GBA header and by no menu path reaching
  them. This does not affect the cheat conclusion.

## 8. Unknowns

- The build provenance of the leftover Beyblade banks was not established; it is irrelevant
  to the cheat result because no Ms. Pac-Man menu references them.
- The fine-grained pause-menu selection byte was not isolated; gameplay and pause share
  the coarse pair `(40,8)` and were distinguished visually. All other screens have unique
  pairs.
- In-level collectible/star mechanics were observed only through the HUD (lives, dots,
  stars) during the Cleopactra level; no code-like input was found to affect them.

## 9. Tooling

`mgba` 0.x SDL (`-3`), `Xvfb :315`, `openbox`, `xdotool`, `scrot`, ImageMagick `convert`,
`arm-none-eabi-objdump -M force-thumb`, `strings -t x`, `xxd`, Python 3 + `zlib`/`struct`.
Scripts kept in `/tmp/mspacman/`: `phase0.py` (header/logo scan), `gba.py`
(input/screenshot), `ssread.py` (gbAs state decoder and diff), `ptr.py` (pointer xref scan),
`tbl.py` (localisation-table resolver), `btnsearch.py` (55 button-mask patterns),
`findstate.py`/`unique.py` (RAM state mining), `combo.py` (runtime button experiments),
`cap.sh` (capture helper).

No ROM or copyrighted assets are redistributed; only hashes, addresses, algorithms and
observations are published.
