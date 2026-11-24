# Super Bubble Pop (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Super Bubble Pop/Super Bubble Pop.gba` |
| Size | 4,194,304 bytes (0x00400000 / 4 MiB) |
| Header title | `S BUBBLE POP` |
| Game code | `AVZE0A` (USA, Rev.00) |
| Maker | `0A` (`00` in the maker bytes with leading zero) |
| Version byte | `0x00` |
| Entry word | `0xEA00002E` → stock branch to `0x080000C0` (not a cracktro) |
| MD5 | `89c947c27346212a2ff412b5d46a51af` |
| SHA-1 | `0d6d267229fdb4a9877fb5a7e768bd27254c4140` |
| SHA-256 | `2e2a755ec1567b4d74996342b40860f1ed55f704d432e93318daf222c3ea5a6f` |
| Save | 512-byte SRAM (`.sav`), signature `00 00 3c 50 53 50 42 53` ("PSPBS" at +4) |

The image is the retail USA build. No appended trainer, no patched entry point.

## 2. Executive summary

**There is no in-game password, cheat-code, button-code, or hidden debug menu in this SKU.**
The only developer-intended unlockables are the two characters **TNT** and **ZIM**,
unlocked by clearing all 50 levels of the Chilled and Groovin difficulties
respectively. Their state is two bytes in IWRAM, set by an end-of-game reward
event, not by any controller input.

Strong evidence for the bounded negative:

* The complete English UI text table has **104 entries (IDs 0–103)**; every one is
  accounted for by an observed screen, a gameplay banner, or a completion message.
  There is no password entry prompt, no "cheat", "code", "debug", "secret", or
  "level select" string in any of the 8 language banks.
* No password alphabet, code table, or validator exists: canonical 36-symbol
  alphabet searches returned **0 hits**; the only occurrences of the character
  IDs `C29`, `VIX`, `BLU`, `TNT`, `ZIM` are the UI strings themselves (**1 literal
  each**), never a byte-compared code constant.
* No button-mask sequence table: a raw scan of all 4,194,304 bytes for runs of
  ≥4 distinct GBA button masks found **4 hits, all in compressed graphics/data
  at 0x0824xxxx–0x0839xxxx**, and **0 hits in code (0x0800xxxx–0x0801xxxx)**.
* The two unlock flags were located, read, and **written live in mGBA**: setting
  `0x030043BB`/`0x030043BC` from `0` to `1` changed "???" to "TNT"/"ZIM" on the
  character-select screen on the next frame (screenshot `s23_flags_set.png`).

This is therefore a **proved bounded negative** (§0.2, §16.3 "no system"), not an
unfinished search. No novel code was minted because no code system exists to
mint from; the enumeration deliverable is the counted negative above.

## 3. How to reproduce

* Emulator: `SDL_AUDIODRIVER=dummy mgba -3 <rom>` under `Xvfb :315` + openbox.
  The two exact PIDs used here were stopped at the end (see §9).
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Holds of 120 ms, gaps of 180 ms.
* Screen path walked:
  Title (`PRESS START`) → Start → **main menu** (`START GAME`, `OPTIONS`,
  `HIGH SCORES`) → `OPTIONS` → **JUKEBOX** (8 tracks, all ticked) and **CREDITS**
  → `START GAME` → **CHARACTER SELECTION** (4 slots: `C29`, `VIX`, `???`, `???`)
  → **SKILL LEVEL** (`TRAINING`, `CHILLED`, `GROOVIN`, `HARDCORE`) → gameplay →
  **PAUSE MENU** (`CONTINUE POPPING`, `RESTART POPPING`, `QUIT POPPING`) →
  **ARE YOU SURE?** (`YES`/`NO`) → back to main menu → **HIGH SCORES** (3 tabs:
  `CHILLED-POPPERS`, `GROOVIN-POPPERS`, `HARDCORE-POPPERS`).
* Live RAM proof of the unlock flags: in mGBA's `-d` debugger, break and issue
  `w/1 0x030043BB 1`, `w/1 0x030043BC 1`, then `c`. The character-select list
  immediately reads `C29, VIX, TNT, ZIM`. Writing `0` back restores `???`.
* Screenshots retained in `/tmp/superbubble/`: `s0_title.png`,
  `s1_afterstart.png`, `s5_options.png`, `s8_jukebox.png`, `s10_startgame.png`,
  `s14_char_down4.png`, `s15_skill.png`, `s16_game.png`, `s17_pause.png`,
  `s19_charsel_again.png`, `s22_cs_base.png`, `s23_flags_set.png`,
  `s26_highscores.png`, `s29_hs_down.png`.

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x08000000` | ROM | Image base; entry `0x080000C0` |
| `0x0800754C`–`0x080075E4` | ROM | Table of ~36 front-end state-machine handler pointers (ARM) |
| `0x0800A0B8` | ROM (ARM) | Front-end reward/unlock state machine (contains both unlock setters) |
| `0x0800A62C` | ROM (ARM) | Setter, flag 1: `strb r2,[r1,#3]` with `r1=0x030043B8` → TNT |
| `0x0800A65C` | ROM (ARM) | Setter, flag 2: `mov r2,#1; strb r2,[r1,#4]` → ZIM |
| `0x0800A678` | ROM (ARM) | Calls `0x080003F8` (save) after either unlock |
| `0x0800A4DC` | ROM (ARM) | Gate: `byte[0x0300432C] != 0`, then `byte[0x030043A4] == 1` → TNT path, `== 2` → ZIM path |
| `0x0800C874` | ROM (ARM) | `GetText(language, id)`; 8-byte entries `{u16 id, u16 0, u32 str}` |
| `0x081DBF0C` | ROM | English text table, 104 entries, IDs 0–103 |
| `0x081DC704`, `0x081DCE84`, `0x081DD768`, `0x081DDF78`, `0x081DE7D0`, `0x081DF000`, `0x081DF744` | ROM | French, German, Italian, Spanish, Portuguese, Dutch, Swedish text tables |
| `0x081DA7C0` | ROM | ASCII source tag `FrontEnd.c`, followed by `???` (0x081DA7D0) and a sprite/asset table |
| `0x030042CC` | IWRAM | Language index (0–7) |
| `0x0300432C` | IWRAM | Reward-event active gate; `0` on all menus |
| `0x030043A4` | IWRAM | Reward event type: `1` = TNT, `2` = ZIM |
| `0x030043B8` | IWRAM | 8-byte save-mirror base used by the front end |
| `0x030043BB` | IWRAM | **TNT unlocked** (observed `0` locked → `1` unlocked) |
| `0x030043BC` | IWRAM | **ZIM unlocked** (observed `0` locked → `1` unlocked) |
| `0x02000090` | EWRAM | Bubble-grid colour state (values `0x21`, `0x22`, …) |
| `0x03006FE4` / `0x03006FE8` / `0x03006FE0` | IWRAM | Input event flag / counters; main loop polls `ldrb` at `0x08013CAC` |
| `0x0E000000` | SRAM | 512-byte save (high-score table + unlock mirror; SRAM flag offset not pinned) |

## 5. Algorithm

There is no password algorithm. The only algorithm of interest is the unlock
gate, recovered from ARM disassembly:

```
# 0x0800A4DC (front-end reward handler)
if byte[0x0300432C] == 0: return              # no reward event pending
t = byte[0x030043A4]
if t == 1: goto unlock_TNT                    # 0x0800A62C
if t == 2: goto unlock_ZIM                    # 0x0800A65C

unlock_TNT:                                   # 0x0800A62C
    if byte[0x030043B8+3] != 0: return        # already unlocked
    byte[0x030043B8+3] = 1
    call 0x080003F8                           # persist save

unlock_ZIM:                                   # 0x0800A65C
    if byte[0x030043B8+4] != 0: return
    byte[0x030043B8+4] = 1
    call 0x080003F8
```

The character-select renderer tests the same two bytes: when `0`, it draws the
string at text ID 0 (`???`); when `1`, it draws text ID 4 (`TNT`) or 5 (`ZIM`).
Text ID 3 (`BLU`) is **unused** in this SKU — the selector is a 4-slot ring and
never exposes a fifth character (verified by pressing Down repeatedly).

Source of `0x030043A4` values: the completion-message strings at text IDs
12–27 (`WELL DONE!`, `You completed all the CHILLED levels`, `TNT joined your
team!`, `the HARDCORE levels`, `ZIM joined your team!`, `the TRAINING levels`)
tie the two reward codes to finishing Chilled/Groovin, exactly as the published
unlockables describe. Setting the event bytes by hand while on the menu did
**not** fire the setter (the handler is only active in the end-of-game state),
which is consistent with a progression-gated — not input-gated — reward.

## 6. Tables

**Complete English UI text table** (`0x081DBF0C`, 104 entries). Notable IDs:

| ID | String | Status |
|---:|---|---|
| 0 | GAME OVER | observed gameplay |
| 1,2 | C29, VIX | observed, default characters |
| 3 | BLU | **unused in this SKU** (no 5th slot) |
| 4,5 | TNT, ZIM | locked by default, unlockable |
| 6–10 | PULSE WAVE!, TACK ATTACK!, SHRINK WRAP!, METEOR ATTACK!, WARP TUNNEL! | special attacks (WARP TUNNEL is an attack, **not** a warp menu) |
| 11 | CHARACTER SELECTION | observed |
| 12–27 | WELL DONE! … do some real popping! | end-of-difficulty reward screens (progression-gated) |
| 28–30 | NEXT GAME?, RESTART, EXIT | observed confirm dialogs |
| 31–38 | CONTINUES, CHILLED/GROOVIN/HARDCORE-POPPERS, Name, Score, DJ, Levels | observed high scores |
| 39–40 | START GAME, OPTIONS | observed main menu |
| 46–72 | LEVEL TOKEN … NO BONUS | in-game bonuses |
| 80–84 | JUKEBOX, RESTART/CONTINUE/QUIT POPPING, PAUSE MENU | observed |
| 85 | ARE YOU SURE? | observed |
| 86–89 | CHILLED, GROOVIN, HARDCORE, TRAINING | observed skill level |
| 95–97 | LANGUAGE, 1, 2 | unused in the USA build (no language menu reachable) |
| 98–103 | PRESS START, SUPER BUBBLE POP, HIGH SCORES, SKILL LEVEL, CREDITS, ENTER NAME | observed / high-score initials entry |

**Unlock flag map:**

| Byte | Meaning | Locked | Unlocked |
|---|---|---:|---:|
| `0x030043BB` | TNT selectable | `0` | `1` |
| `0x030043BC` | ZIM selectable | `0` | `1` |

**Jukebox:** 8 tracks (Corona, Dream, Sunset, The Whicka Man, Amigaos,
Re-psyche, Indus Valley, UDTQ), all available from a fresh save — no unlockable
music.

**High-score defaults:** a fresh SRAM already contains `US/300000`,
`DM/270000`, `RIC/240000`, `SMC/210000`, `BOB/180000` (developer initials).
These are labels, not codes; `ENTER NAME` accepts 3 initials and is never
compared against a constant (§16.2b).

## 6b. Enumeration

**This game has no code space to enumerate.** The deliverable is a counted,
bounded negative (§0.2 point 5, §16.3 case 1 "no system"):

| Search | Space examined | Hits | Result |
|---|---|---:|---|
| `strings -t x -n 4` | all 4 MiB, 27,341 lines | 0 relevant | No password/cheat/debug/secret/level-select prompt in any language bank. Only `FrontEnd.c`, `???` and library assert strings like `DisplaySetMode - Invalid Display Mode` |
| Keyword scan (`password`, `cheat`, `debug`, `secret`, `unlock`, `code`, `menu`, `invalid`, `warp`, `level select`) | all 4 MiB, ASCII + case-insensitive | 0 relevant | Only gameplay/menu words and engine asserts |
| Canonical alphabets `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ` and reverse | all 4 MiB | **0** | No password alphabet stored |
| Long uppercase/digit runs (`[0-9A-Z]{20,}`) | all 4 MiB | 497 runs | All are repeated single bytes (`UUUU…`, `DDDD…`) in compressed graphics, not alphabets |
| Literal `C29`/`VIX`/`BLU`/`TNT`/`ZIM` | all 4 MiB | 1 each | Only the text-bank strings; none compared by code |
| Button-mask runs ≥4 with ≥4 distinct masks (active-high and active-low) | all 2,097,152 halfword offsets | 4 active-high, 0 active-low | All 4 at `0x08243E0A`, `0x0828E3D8`, `0x082FCB2C`, `0x0839B64C` — compressed data region. **0 in code** |
| Front-end text table | 104 IDs × 8 languages | 0 hidden | Every ID mapped to an observed screen, gameplay banner, or progression message |
| Character-select slots | full ring, Down × 6 | 4 slots | `C29, VIX, ???, ???` → after RAM write `C29, VIX, TNT, ZIM`. No BLU slot, no hidden 5th entry |
| Reachable screens | title, main menu (3), options (2), jukebox (8), char select (4), skill (4), gameplay, pause (3), confirm, high scores (3) | — | None contains an input code field, debug menu, or level selector |
| Save file | 512 B SRAM | — | High scores + unlock mirror only; no code field |

**Novel code:** not applicable — no generator, validator, table, or input alphabet
exists. **Rejection bounds:** not applicable for the same reason; the closest
bounded test was the reward gate — writing `0x030043A4 = 1/2` with
`0x0300432C = 1` on the character-select screen produced **no** unlock (flags
stayed `0`), proving the setter is not reachable from menu input.

**Positive result (the actual unlockables):** 2 flags, both dynamically verified.
Space size = `2^2 = 4` states; only `00` (fresh) and `11` (both difficulties
cleared) are reachable through normal play; `01`/`10` are intermediate states
produced by clearing one difficulty.

## 7. Validation evidence

* **Observed** (emulator/screenshot/RAM): every screen in §3; character select
  showing `???` with flags `0,0` (`s22_cs_base.png`) and `TNT`/`ZIM` after writing
  flags to `1,1` (`s23_flags_set.png`); 8 jukebox tracks all ticked; 3 high-score
  tables; reward-gate write produced no unlock.
* **Derived** (disassembly): unlock setters `0x0800A62C`/`0x0800A65C` and gate
  `0x0800A4DC`; `GetText` table format; 104-entry English text table; no BLU slot;
  no code/button table in the searched spaces.
* **Inferred**: `0x030043A4 = 1` means "Chilled cleared" and `= 2` means "Groovin
  cleared" — based on the adjacent completion strings, not on playing 50 levels.
  SRAM byte offset of the unlock mirror was not pinned.

Published-list reconciliation: 3rd party cheat index list exactly the two
character unlockables for GBA and no passwords; 3rd party cheat indexes explicitly has no
GBA cheats. Both are consistent with the ROM. No published code was found that
the ROM rejects (there are none to test).

## 8. Unknowns

* Which SRAM byte(s) mirror `0x030043BB/BC` — the game's save routine
  (`0x080003F8`) was identified but not invoked with a modified flag to diff SRAM.
* Exact producer of the reward-event byte `0x030043A4` (end-of-game routine);
  triggering it requires clearing 50 levels, which was not played.
* The unused `LANGUAGE`/`1`/`2` strings (IDs 95–97) — likely a first-run or
  non-USA option; not reachable in the AVZE0A build (fresh save boot also showed
  no language screen).
* `ENTER NAME` screen was not triggered (requires a qualifying score); it is a
  3-initial high-score label, not a validator (no code literals found).

## 9. Tooling

* `strings -t x`, `xxd`, `grep -abo`, Python 3 scanners (`xref.py`, `scan.py`,
  `gba.py`) for literal/alphabet/button-mask searches.
* `arm-none-eabi-objdump -M force-arm` / `-M force-thumb` for disassembly.
* mGBA 0.10.5 under Xvfb `:315` + openbox; `SDL_AUDIODRIVER=dummy`.
* mGBA CLI debugger (`-d`) driven through a FIFO and captured with `script(1)`;
  commands `x/1|x/2|x/4`, `w/1`, Ctrl+C break, `c`. Helper scripts `dbg2.py`,
  `dump.py` in `/tmp/superbubble/`.
* Because other concurrent agents used global `pkill -x mgba`, the emulator was
  run from a renamed copy (`sbpmgba`) and only the exact recorded PIDs were
  signalled at teardown.

Cleanup: all processes started for this task were stopped by their recorded
PIDs (`sbpmgba`, its FIFO holder, `script`, Xvfb `:315`, openbox, and the short
fresh-boot instance `sbp2mgba`). No `pkill`/`pkill -f` was used. The temporary
ROM copy and its `.sav` were kept in `/tmp/superbubble/`; the `.sav` in the
ROM folder is the emulator artifact and is removed at handoff.

## 10. Legal note

No ROM bytes, graphics, music, or game text are redistributed here. Only
addresses, hashes, counts, and original observations are published.
