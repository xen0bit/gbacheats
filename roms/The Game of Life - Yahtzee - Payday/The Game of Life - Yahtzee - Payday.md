# The Game of Life - Yahtzee - Payday (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/The Game of Life - Yahtzee - Payday/The Game of Life - Yahtzee - Payday.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `THE GAME OF` (0xA0–0xAB) |
| Game code / maker | `B3UE` / `20` (Destination Software / Black Lantern Studios), rev `0x00` |
| Header flag | `0x96` at 0xB2; complement `0x00`, checksum `0x0000` (rebuilt header — normal, see guide §16.1) |
| Entry word | `EA00002E` → ARM entry `0x080000C0` (stock, not a cracktro) |
| MD5 | `a40e7bbd268202da470950335a6793f5` |
| SHA-1 | `167a454e4660629ed99b014c77bd3e4ae9eef294` |
| SHA-256 | `4ea791838f6422141f8087b960ab249e15ecf13be9c3a8f2b4f59571de084fdf` |

Nintendo-logo scan over all 4 MiB found **exactly one** header (logo at `0x00000004`), i.e. one linked image, not a concatenated multiboot/multi-cart pack. The compilation is implemented inside a single program.

## 2. Executive summary

**Bounded negative.** This ROM has no developer-intended cheat surface: no password/code system, no button-code sequence matcher, no hidden/debug menu, and no unlockable flag block. There is therefore no validator to reverse and no novel code to mint; §0.2's "negative results bounded" clause is the applicable deliverable, and §6b gives the counts that bound the negative.

Evidence summary:

1. **Published codes: none exist.** VGChartz lists "Total cheats available: 0"; Romspedia says "no cheats for the selected game"; ChapterCheats' *Life / Yahtzee / Payday* page has only a walkthrough; CheatingDome's sole "cheat" is a strategy tip ("choose the college way"), not an in-game code. The widely reported password `192845` belongs to a **different** Black Lantern GBA title (*Board Game Classics*, game code different) — this was checked and excluded per guide §16.11.
2. **The UI text bank is plain ASCII in five languages** (English, French, Italian, German, Spanish). Every menu label was decoded from ROM bytes rather than guessed from screenshots. A case-insensitive scan of all 4 MiB for `password|cheat|secret|debug|code|unlock|level select|game shark|codebreaker|konami` found **zero** hits in ASCII, uppercase, `+0x20` shifted, and UTF-16LE encodings (§6b).
3. **Menu tables have small, exact cardinalities** (2 main-menu entries, 3 games, 2 pause-menu entries) with no unlabelled slots (§6).
4. **The input system is a generic menu navigator.** The only key predicates used by the whole program are single virtual keys `{0,1,2,3,4,0xA}` tested in history slots `{0,1,3}` — 55 + 34 call sites enumerated, all single-key tests. No multi-key mask, no press history compared to a table, no sequence progress index (§4, §6b).
5. **All reachable screens were walked in mGBA** (12 distinct screens, §3) with savestate-derived IWRAM reads confirming distinct runtime states (§7).

Excluded as out of scope: the community-reported *Payday* loan-overflow "money glitch" is a gameplay arithmetic exploit, not a developer-intended code; external cheat-device codes are excluded by the brief.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`), `SDL_AUDIODRIVER=dummy`, Xvfb display `:319` with openbox.
* Command: `mgba -3 game.gba` (the analysed copy lives at `/tmp/opencode/lifeYahtzeePayday/game.gba`; the ROM folder copy was not modified).
* Keymap used (default mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Holds of 120–300 ms; `xdotool windowfocus` to the mGBA window before each burst.
* Savestates: `Shift+F1` saves, `F1` loads. States were kept in the work dir, never in the ROM folder.

Menu path and screens walked (screenshots retained in `/tmp/opencode/lifeYahtzeePayday/`):

| # | Screen | Screenshot |
|---|---|---|
| 1 | Boot: DSI Games splash | `screen.png` |
| 2 | Boot: Black Lantern Studios splash | `gdb_crop.png` |
| 3 | Title — "PRESS START" | `t_title.png`, `splash2.png` |
| 4 | Main menu — Select Game / Credits + 3 game logos | `t_menu.png`, `menu1.png` |
| 5 | Credits (multi-page scroll) | `credits2.png`–`credits6.png` |
| 6 | Game of Life splash | `t_life_splash.png` (`t_life_players.png`) |
| 7 | Life — Select Number of Players {2,3,4} | `t_life_setup1.png` |
| 8 | Life — per-player Human/Computer, gender, colour | `t_life_human1.png`, `t_life_p2c.png` |
| 9 | Life — board / "Select A Card" | `multiA_7.png`, `t_life_board.png` |
| 10 | Life — Paused (Resume / Quit) | `t_life_pause.png`, `t_pause_right.png` |
| 11 | Payday splash + Select Number of Players {2,3,4} | `p_players3.png` |
| 12 | Payday — per-player setup; Select Number of Months; board | `p_setup.png`, `p_months.png`, `p_board.png` |
| 13 | Yahtzee — Select Number of Players {1,2,3,4}; setup; board/scorecard | `y_players.png`, `y_setup.png`, `y_board.png` |
| 14 | Yahtzee — Paused | `state_yahtzee_pause.ss1` |

Quit from any pause menu returns to the main menu (no results screen is shown on an early quit); end-of-game results screens were not reached, but their complete label set is enumerated statically in §6.

## 4. Address map

Addresses are ROM (`0x08...`) / IWRAM (`0x03...`) for this exact revision only.

| Address | Kind | Meaning |
|---|---|---|
| `0x08000000` | ROM | Header; entry `0x080000C0` (ARM) |
| `0x0801DFE4` | Thumb fn | `return ~?` helper — `ldr r1,=0x04000130; ldrh r0,[r1]; bx lr` (single KEYINPUT read) |
| `0x0801DFEC` | literal | `0x04000130` — the **only** KEYINPUT literal in the ROM |
| `0x0801E644` | Thumb fn | Key poll: calls `0x0801DFE4`, `mvns r2,r0`, stores to `0x03004700`, then refreshes six input-source groups |
| `0x0801E6A8` | Thumb fn | `u16 keyHistory[slot]` from `0x0300470C` (no callers found) |
| `0x0801E6CC` | Thumb fn | `bool historyHas(slot, virtKey)` — `r3=history[slot*2]; r3&=r1; return r3==r1`; **55 call sites** |
| `0x0801E6EC` / `0x0801E708` | Thumb fn | `bool globalHas(mask)` — `r1=word[0x03004704 / 0x03004708]; r1&=r0; return r1==r0`; 34 call sites |
| `0x03004700` | IWRAM | Current active-high key state (`~KEYINPUT`); observed `0xFFFFFC00` with no keys held |
| `0x0300470C` | IWRAM | Key history, 16-bit slots (observed 8 slots) |
| `0x03004704`, `0x03004708` | IWRAM | Global key-mask words |
| `0x03004648`, `0x030046D8` | IWRAM | Per-input-source state / key-map tables |
| `0x08033764`, `0x08033768` | ROM | Pointers to main-menu labels "Select Game", "Credits" |
| `0x08033A1C`, `0x08033A20`, `0x08033A24` | ROM | Pointers to pause labels "Paused", "Resume", "Quit" |
| `0x08033B48`–`0x08035000` | ROM | Five-language UI/credits string bank (plain ASCII, high-bit accented bytes) |
| `0x08037F2C`–`0x0803D560` | ROM | *Game of Life* card/house/career text bank (plain ASCII) |
| `0x0803D000`–`0x0803D560` | ROM | *Payday* / *Yahtzee* UI strings (Auction, Expenses, roll categories, "Select Number of Months") |
| `0x0804XXXX` | ROM | 4bpp tile graphics — the only "button-mask-looking" byte runs in the image (see §6b) |

## 5. Algorithm

There is **no password/checksum/button-code algorithm** to reimplement. The only algorithmic subsystem relevant to the search is the input frontend:

```
KEYINPUT (0x04000130, active-low)
  -> ~KEYINPUT stored at 0x03004700
  -> six input-source groups refreshed each frame (0x0801E42C x6,
     0x0801E4AC, 0x0801E50C x6, 0x0801E5A8)
  -> UI queries a *virtual key id* (small integer) with:
       historyHas(slot, virtKey)   [0x0801E6CC]
       globalHas(virtKey)          [0x0801E6EC]
```

Observed virtual-key ids actually queried by all 89 call sites: `{0, 1, 2, 3, 4, 0xA}`. Observed history slots: `{0, 1, 3}`. Every predicate is a **single-key** test; there is no loop over a sequence, no comparator against a stored mask array, and no progress counter. This is a menu navigator, not a cheat matcher.

## 6. Tables

**Main menu** (pointer table at `0x08033764`, one label per language × 2 entries):

| Index | English label | Localisations |
|---:|---|---|
| 0 | `Select Game` | `lection de jeu`, `Seleziona Gioco`, `Spiel wählen`, `Elige juego` |
| 1 | `Credits` | `Crédits`, `Riconoscimenti`, `Mitarbeiter`, `Créditos` |

**Game select:** exactly 3 entries — *The Game of Life*, *Payday*, *Yahtzee*.

**Player-count selectors:** Life `{2,3,4}`, Payday `{2,3,4}`, Yahtzee `{1,2,3,4}`. Payday additionally has a "Select Number of Months" calendar selector (observed value 1).

**Pause menu** (pointer table `0x08033A1C`): exactly 2 entries — `Resume`, `Quit` (+4 localisations each).

**Results/end-game label set** (pointer table `0x08033A80`): `Final Ranking`, `Final Scores`, `Final Cash Value`, `Winner`/`Winners`, `Results`, `Rank: 1st`, `Score: %d`, `Cash Value: %$` (+ localisations). No "score code", "password", or "continue code" label exists in this set.

**Input virtual keys used:** `{0, 1, 2, 3, 4, 0xA}`; history slots `{0, 1, 3}`. Counts: `0x0801E6CC` 55 calls (slot 0 ×33, slot 1 ×14, slot 3 ×10; key `0xA` in every case); `0x0801E6EC` 34 calls (key `0xA` ×33, `4`/`1`/`2` ×1 each).

## 6b. Enumeration

Because the code space is empty, the enumeration is of the **entire candidate surface** that could have hosted a cheat, with counts that make the negative bounded (guide §0.2 point 5, §16.3/§16.9).

**A. Text/alphabet space (searched, zero hits):**

| Encoding searched | Pattern set | Hits in all 4 MiB |
|---|---|---:|
| ASCII (case-insensitive) | password, cheat, secret, debug, code, unlock, level select, game shark, codebreaker, konami | 0 |
| Uppercase ASCII | same | 0 |
| `+0x20` shifted (uppercase-as-lowercase, guide §11) | same | 0 |
| UTF-16LE | same | 0 |

Counts: printable ASCII strings ≥4 bytes in the UI bank `0x33B00`–`0x3D600` = **1,011**; whole-ROM printable strings ≥4 bytes = **62,131**. All 1,011 UI-bank strings are the 5-language versions of the labels listed in §6 and the Life/Payday event text; **none** is a code, password, debug label, or alphabet/keypad row. Font/tile text was decoded as ASCII first (the bank is readable in `strings`), so the negative is not a "strings missed tile-encoded text" artifact (guide §11/§16.11).

**B. Input surface (searched, zero sequence matchers):**

| Search | Result |
|---|---|
| KEYINPUT literals in ROM | 1 (`0x0801DFEC`) |
| Key-predicate helpers | 3 (`0x0801E6CC`, `0x0801E6EC`, `0x0801E708`) |
| Total predicate call sites | 89 (55 + 34); `0x0801E708` unreferenced |
| Distinct masks/virtual keys queried | 6: `{0,1,2,3,4,0xA}` |
| Distinct history slots queried | 3: `{0,1,3}` |
| Multi-key / combined mask tests | **0** |
| Sequence-progress indices or mask-array comparisons | **0** |
| Button-mask table scan (runs of ≥4 plausible `u16` masks in first `0x60000` bytes) | 119 candidate runs; **all 119 resolved to 4bpp tile pixel data or Thumb instruction encodings** (e.g. `0x08044CDC` = tile rows `01 01 01 02…`, verified by `xxd`), i.e. 0 real mask tables |

**C. Menu/screen surface (fully enumerated):**

| Surface | Exact entry count |
|---|---|
| Main menu | 2 |
| Game-select | 3 |
| Life player counts | 3 ({2,3,4}) |
| Payday player counts | 3 ({2,3,4}) |
| Yahtzee player counts | 4 ({1,2,3,4}) |
| Payday months selector | 1 wheel (values ≥1; no hidden code branch) |
| Pause menu | 2 |
| Results/end labels | 8 semantic labels ×5 languages |
| Distinct screens walked in emulator | 12 (§3) |

No screen exposes an alphabetic/numeric keypad, no "Enter code" prompt, and no entry that changes label text in response to input other than the documented selectors.

**D. Novel codes / rejection bounds:** Not applicable — there is no code system to mint or reject against. Per §0.2 this is reported as a proven bounded negative rather than silently omitted. The closest published "code" (`192845` from a different Black Lantern title) was searched literally in this ROM: **0 hits**.

## 7. Validation evidence

* **Observed (emulator):** all 12 screens in §3, including the three splash screens, both setup styles, all three boards, both pause menus, Credits scrolling, and Quit → main menu. Screenshots listed in §3.
* **Observed (savestate RAM):** mGBA `.ss1` `gbAs` chunks decompressed to 397,312-byte states. IWRAM reads (raw offset `0x19000 + (addr-0x03000000)`):

  | RAM | Main menu | Yahtzee board | Yahtzee pause |
  |---|---|---|---|
  | `0x03004648` | `04 00 86 06 07 00 1F 00` | `07 00 1F 00 07 00 24 00` | `07 00 1F 00 07 00 24 00` |
  | `0x030046D8` | `01 00 00 00 08 00 00 00` | `08 00 00 00 08 00 00 00` | `08 00 00 00 08 00 00 00` |
  | `0x03004700` | `00 FC FF FF 01 00 00 00` | `00 FC FF FF 01 00 00 00` | `00 FC FF FF 01 00 00 00` |
  | `0x0300470C` | `01 00 01 00 01 00 01 00` | `01 00 01 00 01 00 01 00` | `01 00 01 00 01 00 01 00` |

  `0x03004700 = 0xFFFFFC00` (no keys held → `~0x03FF`) confirms the decoded input path; `0x03004648`/`0x030046D8` change between menu and in-game states, confirming the screens are distinct runtime states, not static screenshots.
* **Derived (disassembly):** key poll at `0x0801E644`; all three predicate helpers and their 89 call sites; literal values at `0x0801DFEC`, `0x0801E6A4`, `0x0801E6B0`, `0x0801E704`, `0x0801E720`, verified with `struct.unpack_from("<I", …)` (guide §11 literal-pool pitfall avoided).
* **Derived (table decode):** all 5-language menu tables dumped as 32-bit ROM pointers and followed to their ASCII strings (§4, §6). ByteArray at `0x0804xxxx` identified as 4bpp tiles by raw-byte inspection.
* **Inferred (low confidence):** end-of-game results screens are rendered from the `0x08033A80` label table; their exact layout was not observed because no game was played to completion and early Quit returns directly to the main menu.

## 8. Unknowns

* End-of-game results screens were not reached visually; their labels are enumerated statically only.
* Deep in-game sub-screens (Life card-draw variants, Payday auction/bill-payment dialogs, Yahtzee scorecard row selection) were observed only at their entry points, not exhaustively. None offers a code-entry field, but a fully exhaustive playthrough was not performed.
* The 0-byte `game.sav` mGBA auto-creates in the work dir was not analysed; no battery-save-dependent unlock was found and no save-format strings exist.
* A debugger-assisted search for *dead* code (e.g. an unreachable handler with no strings) was not exhaustive; the negative is specifically about reachable screens, the complete decoded text bank, the enumerated input predicates, and searched byte patterns.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x -n 4`, Python byte/pointer scans.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for Thumb ranges.
* Capstone (`CS_ARCH_ARM`, `CS_MODE_THUMB`) for BL/B target scanning and call-site context.
* mGBA 0.10.5 with `-3`, `-g` (GDB stub exercised: `target remote :2345`, reads of `0x02000000` and IWRAM succeeded); Xvfb `:319`, openbox, `xdotool` XTEST input, `scrot`.
* Savestate forensics: Python PNG chunk walk → `zlib.decompress(gbAs)` → 397,312-byte raw state → IWRAM diff (guide §16.13).
* Helper scripts: `/tmp/opencode/lifeYahtzeePayday/key.py`, savestate dump scripts; screenshots and `state_*.ss1/.raw` retained in that directory.

## 10. Legal note

No ROM image, extracted graphics, music, or game text are redistributed by this report. Only hashes, addresses, algorithms, counts, and the analyst's own screenshots/scripts are published. Fetched web pages were treated strictly as data; no instruction found in a page or ROM string was executed.
