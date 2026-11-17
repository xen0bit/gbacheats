# FIFA World Cup: Germany 2006 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `FIFA World Cup: Germany 2006.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `FIFA WC` (0xA0) |
| Game code / maker | `B6WE` / `69` (Exient/EA regional SKU), fixed 0x96 at 0xB2 |
| Version / complement / checksum | 0x00 / 0xFE / 0x0000 (checksum 0 is a rebuilt-header artifact, §16.1) |
| Entry word | `0xEA00002E` → stock `0x080000C0` crt0 (no cracktro) |
| MD5 | `bb87013ec30bebf3dd7cb07ab6786262` |
| SHA-1 | `295580745787ba9593799213564484aaaa7fd463` |
| SHA-256 | `ee85d75fb26a9f3bbbcbc1b7f7bd7d0193c8254aacfdf6442b94c844717baa6b` |
| Developer | Exient Entertainment; publisher EA Sports |

**Embedded-header scan:** the 156-byte Nintendo logo occurs exactly **once**, at file 0. There is no
second game image, no appended trainer, no boot selector and no patch/trainer menu. This is a single
retail image.

## 2. Executive summary

**This GBA image has no developer-intended cheat-code system.** There is no password entry screen,
no button-code detector, no reachable debug/hidden menu and no cheat table. What the ROM does contain
is:

1. **Online-account string leftovers, not a cheat password.** The strings `Getting password`,
   `Changing password`, `Your Password is:`, `Retrieve Password`, `Change Password`, `New Password`,
   `Old Password` (0x086F3AA8–0x086F4210) sit inside a block of EA network-account messages
   (`Checking IMEI`, `Username already exists`, `Invalid Billing DLL`, `Authentication failed`,
   `Uploading`, `Logging in`) — the **N-Gage Arena** online-account service of the shared Exient
   handheld engine. They are an online login subsystem, never a game cheat screen. They
   are unreachable on a GBA cart with no network hardware; this is a cut feature, not a code system
   (§16.3 case 3).
2. **A dead debug screen from a sibling title.** `FUN_0802C628` (0x0802C628, 336 bytes) renders
   **"FIFA 05. Test Mode"** (string at 0x08203730) and runs its own D-pad/L/R input loop. It is
   **unreachable**: Ghidra `procedure_callers` = empty, whole-ROM Thumb `BL` scan = 0 hits, raw
   pointer scan for `0x0802C628`/`0x0802C629` = 0 hits. It is a leftover from **FIFA 05** on the same
   Exient handheld engine; the N-Gage login block and the unused `Test Hooks` string are shared with
   the sibling FIFA 05/06/07 handheld reports. The image itself was identified independently by the
   hash and header above, not by borrowing sibling addresses (which differ: e.g. FIFA 06 places the
   dead Test Mode function at 0x0801BF78 and `Test Hooks` at text ID 140, versus 0x0802C628 and ID
   141 here).
3. **Save-bit unlockables, not codes.** Posters, Historic Challenges and Custom Challenge are earned
   by completing in-game objectives (Rewards screen: "Complete 2006 FIFA World Cup once to unlock
   this poster"); the corresponding 512-byte flash save is gameplay-gated (§16.18), not input-gated.
4. **"Test Hooks" is an unused string, not a menu.** It is localized string ID 141 in the 5-language
   table at 0x086D0288 (entry 0x086D0D8C; French slot = `NOT TO BE TRANSLATED`). The live in-game
   Pause Menu has exactly **6** items (Resume Match, Team Management, Instant Replay, Match
   Statistics, Game Settings, Quit Match) and wraps after the sixth; no "Test Hooks" entry exists.

Published GBA "cheats" are (a) Action Replay device codes — an external cheat cart, explicitly out of
scope — and (b) the same challenge unlockables. No in-game password or button code is published
anywhere for this SKU. The negative result is **bounded**: every reachable screen was walked with
savestate RAM evidence, the full string set was classified, the key-state consumers were enumerated,
and the only debug screen was proved dead.

## 3. How to reproduce

- Emulator: `mgba -3` under `Xvfb :316`, `SDL_AUDIODRIVER=dummy`.
- Keymap (mGBA SDL default): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad = arrows,
  L=`a`, R=`s`.
- Boot path: flag splash → EA Sports logo → **Choose Your Favourite Team** (A=select) →
  **Select Home Team** (A) → **Main Menu**.
- Screens walked (each captured as a screenshot and a savestate in `/tmp/opencode/fifawc06/states/`):
  title/intros, Choose Favourite Team, Select Home Team, Main Menu, FIFA World Cup, Game Modes
  submenu, Global Challenge team-select, Penalty Shootout, Multiplayer, My Cup submenu (Game
  Settings, Control Options, Favourite Team, Rewards, My Profile, Language, Credits), Match Options,
  Team Management, Game Controls, live match, in-game **Pause Menu** (6 items, wrap verified).
- RAM evidence: `Shift+F1` writes `FIFA World Cup: Germany 2006.ss1`. Each `.ss1` is a PNG with a
  zlib-compressed `gbAs` chunk (~397,312 bytes); IWRAM begins at state offset 0x19000, EWRAM at
  0x21000. Each menu transition changes 800–1,310 IWRAM bytes and ~12k–78k EWRAM bytes, confirming
  distinct screen states rather than a static attract loop.
- Dead-code check: in mGBA's `-d` debugger, `b/t 0x0802C628` + `c` never fires during any of the
  above navigation. (The `-d` console is write-only once `c` is issued, so the static xref/BL/pointer
  counts are the primary proof; no live hit was ever observed.)
- Codes tested: none applicable — Action Replay device codes are not in-game inputs; the GameCube
  manual's `R+Z` Team Mentality combo does not exist on the GBA button set; the magazine "Game Access
  Code" `15167` is a website registration code and has 0 literal hits in the ROM.

## 4. Address map

| Address (ROM) | File offset | Meaning |
|---|---|---|
| `0x08000000` | 0x000000 | Stock ARM entry branch `0xEA00002E` → crt0 at `0x080000C0` |
| `0x0802C628` | 0x02C628 | `FUN_0802C628` — dead "FIFA 05. Test Mode" debug screen (0x0802C628–0x0802C777) |
| `0x0802C794` | 0x02C794 | Literal pointer to the "FIFA 05. Test Mode" string |
| `0x0802C798` | 0x02C798 | Literal pointer to companion data at `0x08203744` |
| `0x08203730` | 0x203730 | `FIFA 05. Test Mode\0` |
| `0x086D0288` | 0x6D0288 | Localized string table base: 5 language pointers per row, 20-byte stride |
| `0x086D0D8C` | 0x6D0D8C | Row 141 = `Test Hooks` (fr slot at 0x6D0D90 = `NOT TO BE TRANSLATED`) |
| `0x086F3AA8`–`0x086F4210` | 0x6F3AA8– | Online-account "password"/login message block (network leftover) |
| `0x086E1728`, `0x086F8180`, `0x086F8258`, `0x086F8094` | 0x6E1728 etc. | Unlock messages (posters, Historic Challenge, Custom Challenge) |
| `0x02015C64` | — | Global game flag word (IWRAM/EWRAM workspace) |
| `0x0201A964` | — | Processed key state read by the debug screen's D-pad loop |

Save: `FIFA World Cup: Germany 2006.sav`, 512 bytes flash, predominantly `0xFF` (unwritten sectors).

## 5. Algorithm

Not applicable — no validator, encoder, decoder or checksum exists in this image. The only algorithmic
artifact is the dead debug screen's own input handling in `FUN_0802C628`, which is never entered.

## 6. Tables

**Button masks observed in the (dead) debug screen's input loop** — active-high `~KEYINPUT & 0x3FF`:

| Mask | Button |
|---:|---|
| 0x001 | A |
| 0x002 | B |
| 0x004 | Select |
| 0x008 | Start |
| 0x010 | Right |
| 0x020 | Left |
| 0x040 | Up |
| 0x080 | Down |
| 0x100 | R |
| 0x200 | L |

`FUN_0802C628` tests exactly 0x040/0x080/0x020/0x010/0x200/0x100 to scroll a viewer and exits only
when `(*0x02015C64 & 2) != 0` — a flag no reachable code path sets for this function.

**Live in-game Pause Menu (6 items, wrap at 6):** Resume Match, Team Management, Instant Replay,
Match Statistics, Game Settings, Quit Match.

**Main Menu (5 items):** Kick Off, FIFA World Cup, Game Modes, Multiplayer, My Cup.
**Game Modes (2):** Global Challenge, Penalty Shootout.
**My Cup (7):** Game Settings, Control Options, Favourite Team, Rewards, My Profile, Language, Credits.

## 6b. Enumeration

**Code space: empty.** There is no alphabet, no code length, no checksum, no lookup table and no
input surface to enumerate. The requested "mint a novel code and prove bounds by rejection" is
therefore impossible by construction; this is a proven negative, not an untested case.

Searches performed and their counts:

| Search | Result |
|---|---|
| `strings -t x -n 4` over full 8 MiB | 61,459 lines. Keyword classification: `password` → network-auth block only; `unlock` → challenge/poster strings only; `test` in code region (<0x300000) → exactly **1** hit, the dead `FIFA 05. Test Mode`; no `cheat`, `level select`, `debug menu`, `secret code`. |
| Font/tile-indexed text bank | **None required.** All 11 representative on-screen labels checked (`Main Menu`, `Select Home Team`, `Choose Your Favourite Team`, `Kick Off`, `Global Challenge`, `Penalty Shootout`, `My Cup`, `Multiplayer`, `Pause Menu`, `Your Password is:`, `FIFA 05. Test Mode`) are plain ASCII in the ROM. No tile-index-decoded UI text exists to decode. |
| Thumb `BL` scan for the debug function over all 8 MiB | **0** hits. |
| Raw 32-bit pointer scan for `0x0802C628` / `0x0802C629` | **0** hits. |
| Ghidra callers of `FUN_0802C628` | **0** (complete resolved-reference coverage). |
| Key-state consumers (`0x0201A964` literals) | **18** literal sites; disassembly shows only menu-index comparisons (0, 1, 2, 0xE, 0x10, 0x4C, 0x7C, 0x9F) — no multi-button mask sequence validator. |
| Naive u16 single-key-mask runs ≥4 | **278** runs; 8 representative runs spot-checked — **0** have any 32-bit literal pointer referencing them (coincidental data in high-entropy regions). No code-referenced button-code table. |
| Published literals | Action Replay master/SEL+LEFT/SEL+RIGHT codes are device-side encrypted codes, not ROM strings; Game Access Code `15167` = 0 hits. |
| Embedded GBA headers | **1** (file 0 only). No trainer/menu injection. |

**Proof of bounds:** the only two candidate "cheat" surfaces — a password screen and a debug screen —
are respectively a network-login leftover with no game entry UI, and a function with zero incoming
references. Every reachable screen was enumerated above; none presents an input field or a hidden
option. The 6-item pause menu was verified by cursor wrap. Unlockables were observed on the Rewards
screen to be objective-gated (save bits), not entered as codes.

**Novel code:** not generatable — there is no code space. A code that "is in no published list" cannot
be minted for a system that does not exist; inventing one and claiming acceptance would be false.

## 7. Validation evidence

- **Observed:** all screenshots in `/tmp/opencode/fifawc06/shot_*.png` and `state_*_crop.png`; 6-item
  pause menu and its wrap; Rewards screen objective text; 19+ savestate RAM diffs; single logo hit;
  512-byte save dump.
- **Derived:** full Thumb `BL` scan (0 callers), raw pointer scan (0 references), Ghidra
  `analyze_function` / `procedure_callers` on `FUN_0802C628`, key-mask table scan with pointer
  cross-check, localized-string table decode (row 141 = `Test Hooks`).
- **Inferred:** `FUN_0802C628` is a FIFA 05 engine leftover (string literally names FIFA 05) and the
  online-login block is a cut network feature; both are plausible but no build history was available
  to prove *when* they became dead.

## 8. Unknowns

- The exact visual behavior of `FUN_0802C628` was never executed because no caller exists; its
  parameter semantics are inferred from decompilation only.
- Whether `Test Hooks` was ever a live pause-menu row in an earlier Exient build is unknown; in this
  ROM it is unreferenced by any menu definition.
- The 512-byte save's individual unlock bit positions were not mapped; only the gameplay-gated nature
  of the unlockables was established (their setters are completion events, not controller input).

## 9. Tooling

- `strings -t x`, `xxd`, `grep -abo` for reconnaissance and literal verification.
- Python 3 + Capstone 5.0.7: whole-ROM Thumb `BL` scanner, PC-relative literal scanner, key-mask run
  scanner, GBA header/logo scanner.
- REA MCP (Ghidra 12.1.4): `open_binary` (raw ARM, base 0x08000000), `analyze_function`,
  `procedure_callers`, `close_binary` on `FUN_0802C628`.
- `arm-none-eabi-objdump` and a small Capstone disassembler (`gdis.py`) for address verification.
- mGBA under Xvfb :316 with `SDL_AUDIODRIVER=dummy`; `xdotool` + `import`/ImageMagick for input and
  screenshots; `Shift+F1` savestates parsed by zlib-decompressing the PNG `gbAs` chunk and diffing
  IWRAM (0x19000) / EWRAM (0x21000).

**Legal note:** no ROM image or copyrighted assets are redistributed here — only hashes, addresses,
algorithms and original tools.
