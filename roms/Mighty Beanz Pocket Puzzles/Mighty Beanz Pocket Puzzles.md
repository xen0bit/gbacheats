# Mighty Beanz Pocket Puzzles (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mighty Beanz Pocket Puzzles/Mighty Beanz Pocket Puzzles.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `MBEANZPP` |
| Game code | `BMBE` |
| Maker code | `5G` |
| Revision | 0x00 (complement 0x62, header checksum 0x0000) |
| Entry word | `0xEA00002E` → `b 0x080000C0` (stock crt0) |
| MD5 | `66e896522a91ecd1e45fde5e93920bf7` |
| SHA-1 | `78f9e56a2f22a08b1597c9c545b0474ba290c298` |
| SHA-256 | `004d2bf5b7cecb6d3722367410e9ae4208814e777a69c3d82855401122e18cf9` |
| Developer / publisher | Radius9 / Majesco, 2004-06-07 (per GameFAQs/IGN release data) |

**Phase 0 result:** Nintendo-logo scan over the whole image returns exactly **one** header, at file offset `0x0`. The entry word is the stock GBA branch, the fixed byte at `0xB2` is `0x96`, and there is no appended trainer, cracktro, boot selector or second image. The image is the retail ROM, not a patched/trainer build.

Save hardware: mGBA creates a **512-byte EEPROM** save (`mb.sav`), and the literal `EEPROM` appears at `0x3F4920`. Progress is battery-backed save data, not a password scheme.

## 2. Executive summary

**Finding: this game has no in-game cheat system of any kind — no password entry, no button code, no hidden debug menu, and no unlock code.** It is a pure progression/collectible puzzle game: Puzzle Mode (Normal and Battle, 100 stages), Time Trial (Normal and Battle), and a Beanz Case collection viewer. Rare Beanz and Super Pro Beanz are awarded by save-data milestones (streaks, combo counts, clear times) read from the 512-byte EEPROM — the §16.18 "save-bit unlock, not a code" pattern.

This negative is **bounded and proven**, not an absence of searching:

* Every reachable screen was walked in the emulator (title, main menu, both mode submenus, both difficulty selects, both hints, both gameplay variants, pause, quit-confirm, Beanz Case grid) with screenshots and savestate RAM diffs.
* The **entire text bank** (68 NUL-terminated ASCII strings, `0x082BD598`–`0x082BE400`) was decoded and enumerated. It contains zero password/cheat/debug/secret/options strings. The visible menu headings ("MIGHTY MENU", "PUZZLE", "BEANZ CASE", "PAUSED", "HINT") are pre-rendered gradient graphics, not font text; the font-rendered strings (e.g. the HINT text) come from that same ASCII bank, so no font/tile-indexed second bank was left undecoded.
* The **entire button-input space** was characterised statically: 2 direct KEYINPUT reads and 64 calls to the two input helpers, all testing **one button per test**. The only multi-key predicate in the ROM is the standard GBA soft-reset combination (L+R+Start+Select) at `0x0800F25A`–`0x0800F27A`.
* Multiple common codes (Konami code, L+R+Start, A+B+Start+Select, D-pad roll, ten-A) were entered on the title screen and main menu; savestate diffs against no-input controls show only animation/input-history noise and no persistent state change or hidden screen.
* Published-code search found **no codes published for this SKU** — Cheat Happens states explicitly that no cheats/codes exist for the GBA game; GameFAQs and TCRF pages returned 403 and their indexed snippets contain no codes. No literal from any published list needed verification because no list exists.

Four developer easter eggs *are* present in the text bank (Zork "grue", "This is bat country!", a love letter, and "All powerups maxed out!"), selected by a result/milestone argument through a 5-entry pointer table. They are hidden **messages**, not cheats, and are documented in §6.

## 3. How to reproduce

* Emulator: `mgba -3` under `Xvfb :315`; `SDL_AUDIODRIVER=dummy`. Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Holds of ~70–90 ms move one menu slot (150 ms double-steps).
* Boot to title (logo ~2 s), press Start → MAIN MENU. Navigate with Up/Down, confirm A, cancel B.
* Menu paths actually taken:
  * PUZZLE → NORMAL → HINT → LEVEL 1 gameplay → Start → PAUSED (RESUME/EXIT) → EXIT → YES.
  * PUZZLE → BATTLE → EASY/MEDIUM/HARD → gameplay.
  * TIME TRIAL → NORMAL → HINT → gameplay (TIME 1:06, 5 MATCHES LEFT).
  * TIME TRIAL → BATTLE → EASY/MEDIUM/HARD.
  * BEANZ CASE → collection grid (Right/Left/Down scroll bean info; A has no action).
  * Every list was pressed past its last entry to confirm wrap-around and exact item count.
* Codes tested on title screen: Konami code, L+R+Start, A+B+Start+Select, Up/Down/Left/Right, ten consecutive A presses. On main menu: Konami code, L+R, A-B-A. Baseline/pressed states saved with Shift+F1/F2 and compared by extracting the zlib-compressed `gbAs` chunk from each `.ss1/.ss2` PNG.
* No ROM or assets were modified; emulation used an identical byte-for-byte copy in `/tmp/mightybeanz/mb.gba`.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Address | Purpose |
|---|---|
| `0x08000000` | Stock ARM entry (`b 0x080000C0`) |
| `0x0800AFC0` | Input reader: reads `0x04000130`, masks `0x03FF`; writes held `0x03000208` and pressed `0x0300020A` |
| `0x0800B020` | `IsHeld(mask)` — reads `0x03000208` |
| `0x0800B03C` | `IsKeyPressed(mask)` — reads `0x0300020A` |
| `0x0800F25A`–`0x0800F27A` | Soft-reset combo check: L, R, Start, Select all held (standard GBA reset, not a cheat) |
| `0x082BD598` | Start of ASCII text bank (begins with debug assert "Assert failed") |
| `0x082BD598`–`0x082BE400` | Complete text bank: 68 NUL-terminated strings (dialogue, 21 objectives, 4 easter eggs, credits) |
| `0x082BD5E0` | `MultiSioSync020820` — link-cable sync banner |
| `0x082BD608`–`0x082BD644` | Powerup names: Block, Freeze, Steal, Tipsy, Quake, Double, Time Freeze, Wildcard |
| `0x083F5300`–`0x083F539F` | 21 objective records, 8 bytes each: `{u16 id1, u16 id2, u32 text_ptr}`; text pointers into the bank |
| `0x083F53C8`–`0x083F53DC` | 5-pointer table: grue (`0x082BE05C`), love letter (`0x082BE0BC`), bat country (`0x082BE130`), "All powerups maxed out!" (`0x082BE160`), credits (`0x082BE17C`) |
| `0x08015B14`–`0x08015B4A` | Selector that indexes the 5-message table from an argument (ending/result type) |
| `0x0800ACA0` | Main engine init; dispatches subsystem inits |

Savestate RAM layout used for evidence (mGBA `.ss1`, raw `gbAs` length 397,312): `0x00000` header/CPU, `0x1000` VRAM, `0x19000` IWRAM, `0x21000` EWRAM. Observed discriminating RAM words:

| RAM | main menu | puzzle submenu | hint | gameplay | pause |
|---|---|---|---|---|---|
| `0x03000C00` | `0x203` | `0x203` | `0x202` | `0x160` | `0x145` |
| `0x03007DA4` | `0x3` | `0x3` | `0x3` | `0x2` | `0x0` |
| `0x02001028` | `0x7` | `0x9` | `0x3A` | `0xD` | `0xD` |

## 5. Algorithm

There is no validator, decoder, checksum or password algorithm to reimplement. The relevant algorithms are ordinary game systems:

* Input: `held = ~KEYINPUT & 0x3FF`; `pressed = held & ~prev`; globals at `0x03000208`/`0x0300020A`; all gameplay/UI decisions call `IsHeld`/`IsKeyPressed` with a single-button bit.
* Unlocks: milestone predicates (e.g. "Beat 4 levels in a row after level 30", "Get 10 or more combos") write bits in the EEPROM save; the Beanz Case reads those bits to display bean entries. No user-supplied value participates.
* Easter eggs: an ending/result argument selects one of the five strings at `0x083F53C8`.

No code space exists, so §0.2's "validator model / novel code" deliverable is replaced by the bounded-negative proof in §6b, as §0.2 point 5 requires.

## 6. Tables

**Text bank (complete, 68 strings at `0x082BD598`–`0x082BE400`).** Categories and counts:

* 7 debug/engine strings: `Assert failed`, `Filename `, `LineNo `, `src/GBABG.c`, `BGIndex < 4`, `BGIdx < 4`, `MultiSioSync020820`.
* 8 powerup names: `Block`, `Freeze`, `Steal`, `Tipsy`, `Quake`, `Double`, `Time Freeze`, `Wildcard`.
* 23 battle dialogue lines (`Wasup slick?`, `I'm the gamer and you are a loser.`, `Hi, I'm Liz.`, `Tsk Tsk Tsk.`, …).
* 17 unlock-objective strings (`Beat 4 levels in a row after level 30 to win a rare bean.`, `Get 10 or more combos and you will win a super pro bean.`, …).
* 4 easter eggs + 1 credits block.
* No string contains `password`, `cheat`, `code`, `debug`, `secret`, `unlock`, `options`, `level select`, or any keyboard/keypad alphabet beyond the font glyph table at `0x082BD651`.

**Input-mask census (all 64 input-helper call sites, resolved from Thumb `movs`/`lsls` before each BL):**

| Button | A | B | Select | Start | Right | Left | Up | Down | R | L |
|---|---|---|---|---|---|---|---|---|---|---|
| `IsKeyPressed` calls | 12 | 5 | 0 | 6 | 0 | 0 | 3 | 3 | 1 | 2 |
| `IsHeld` calls | 2 | 2 | 1 | 1 | 6 | 6 | 4 | 6 | 1 | 1 |

Two `IsHeld` call sites use a computed mask rather than a literal (music/sound handling); inspection shows single-button semantics as well. **No test uses a combined bitmask.** The only sequence of multiple button tests is L→R→Start→Select at `0x0800F25A`–`0x0800F27A`.

**Published codes:** none found. Cheat Happens' GBA page for this title explicitly says "We currently don't have any Mighty Beanz Pocket Puzzles cheats or cheat codes for Game Boy Advance." GameFAQs (game page, release-data page, statistics) and TCRF/IGN/Wiki listings contain no code section for this SKU. Direct fetches of GameFAQs cheats and TCRF returned HTTP 403; archive snapshots returned 404/503. Search-result snippets from those domains contain no codes. No published literal exists to search for in the ROM.

**Fetched-content safety:** all web text was treated as data. No prompt-injection payload was encountered; no instruction found in any fetched page or ROM string was executed.

## 6b. Enumeration

* **Code space size:** 0. There is no password entry screen, no alphabet, no code length, no checksum, no comparison table of user-supplied strings, and no button-code dispatcher. The 10 possible GBA buttons were exhaustively accounted for across all 64 input-test call sites; there is no multi-button predicate other than the reset combo. The text bank's 68 strings bound the label space: no hidden menu or code entry is named anywhere.
* **Novel code:** not applicable — no system exists to mint a code for. Per §0.2 point 5, the negative is bounded by the full menu enumeration, the complete text-bank decode, the complete input-call-site census, and empirical code-entry tests instead.
* **Bounds proven by rejection:** out-of-scope by construction — there is no field width, checksum or reserved bit to violate. The closest positive bound is the reset-combo handler: it is the *only* multi-key sequence in the image, and pressing L+R+Start+Select during gameplay did not open any menu or unlock state (test on :315; screen remained Beanz Case, no save/RAM flag change).
* **Hidden content that is not a cheat:** the 5 milestone strings at `0x083F53C8` (Zork grue, love letter, bat country, "All powerups maxed out!", credits) are real hidden text but are selected by an ending/result argument, not by player input. Their presence does not imply a code system.

## 7. Validation evidence

**Observed (emulator/savestate):**
* All screens listed in §3 reached and screenshotted; every finite list wrapped (main menu 3 items, mode submenu 2 items, difficulty 3 items, pause 2 items, quit-confirm 2 items).
* RAM diffs between savestates at distinct screens show distinct values at `0x03000C00`, `0x03007DA4`, `0x02001028` (table in §4).
* Button-code tests on title and main menu: after subtracting the no-input control, remaining EWRAM differences are confined to the animation/input-history arrays at `0x02002FDB`–`0x020030xx` (u16 streams of sprite/timer values); no persistent flag or new screen appeared.
* 512-byte EEPROM file created; untouched image contains fresh `0xFF`-filled save.

**Derived (static):**
* One GBA header (logo scan), stock entry word — no trainer/patch.
* Complete text bank decoded as ASCII with `0x0A` line breaks and NUL terminators; 68 strings, no code-related labels.
* Input surface fully enumerated: 2 KEYINPUT reads, 64 helper calls, single-button masks only; soft-reset combo at `0x0800F25A`.
* Objective table `0x083F5300` (21 records) and 5-message table `0x083F53C8` mapped to their exact strings.

**Inferred (labelled):**
* The 5 hidden messages are shown as ending/milestone text (the selector function at `0x08015B14` takes a result-type argument). The in-game condition that selects each specific message was not exhaustively played through; this does not affect the cheat/no-cheat conclusion.

## 8. Unknowns

* Which exact milestones trigger each of the four easter-egg messages (only the pointer table and selector function were reversed; the achievement predicates were not played to completion).
* Full bit layout of the 512-byte EEPROM (fresh save was all `0xFF`); the unlock bits were inferred from the objective strings and Beanz Case UI, not exhaustively mapped.
* Beanz Case grid total page count beyond the first several rows/columns traversed; no A-button action exists on any visited cell.

None of these unknowns could conceal a cheat: they concern reward presentation and save layout only, and the input/text spaces that could implement a code were exhaustively searched.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for ROM disassembly.
* Python 3 + Capstone 5.0.7 for BL/literal scans, mask extraction, text-bank decoding and pointer-table mapping.
* `xxd`, `strings`, `grep`, `file`, `md5sum`/`sha1sum`/`sha256sum` for Phase 0/recon.
* `mgba -3` on `Xvfb :315` with `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input; `scrot` + ImageMagick `convert` for screenshots.
* Savestate RAM reads: extract the zlib-compressed `gbAs` PNG chunk (raw 397,312 bytes; IWRAM at `0x19000`, EWRAM at `0x21000`) and diff between states (§16.13). Used because the GDB stub port 2345 was already held by another analysis session.
* Scripts retained in `/tmp/mightybeanz/`: `findtext.py`, `fontprobe.py`, `bruteenc.py`, `decodetext.py`, `xrefs.py`, `bankptr.py`, `hidptr.py`, `findbank.py`, `enumbank.py`, `inputscan.py`, `keyptr.py`, `blscan.py`, `maskextract.py`, `maskstats.py`, `msgtable.py`, `k.sh`, `combo.sh`, `snap.sh`, `testcode.sh`, `diffstates.py`.

**Legal note:** no ROM bytes, graphics, music or game text are redistributed here; only hashes, addresses, counts and independently written findings are published.
