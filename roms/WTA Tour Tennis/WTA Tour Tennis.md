# WTA Tour Tennis (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `WTA Tour Tennis.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `WTATOUR` |
| Game code | `ATEE` (serial AGB-ATEE-USA) |
| Maker | `A4` |
| Version | 0x00 (Rev.00) |
| Entry word | `0xEA00002E` → stock crt0 branch to `0x080000C0` (not a scene cracktro) |
| MD5 | `b9f78309dbce23a4262dc32c1def62a2` |
| SHA-1 | `56b1d64f9baf83d8ec73e2857da62cd5b0bd9851` |
| SHA-256 | `0186a981dab186579c61a46b5c3d7305d8b9899a8a06c604a40f78ae47599136` |
| Developer / publisher | Now Production / Konami (US release 2002-05-31) |
| Also known as | Pro Tennis WTA Tour (EU), WTA Tour Tennis Pocket (JP) |

Header complement byte is `0x87` (not `0x00`), header checksum `0x0000`; this is a normal retail image with a rebuilt-checksum-style header, not a patched entry point.

## 2. Executive summary

**Result: bounded negative for a player-facing cheat system.** This SKU has no password screen, no in-game button-code matcher, and no reachable hidden/debug menu. All 20 players are selectable from a fresh boot; the only progression is normal WTA Tour play (prize money / tournaments / ranking), which is game state rather than a cheat code.

The ROM **does** contain a substantial developer debug-menu residue: an ASCII string bank at `0x080449D0–0x08044B10` with labels `GO TOUR / GO EXHIBI / GO MENU / GO TITLE / GO DEMO / GO LOGO` (each in a plain `  ` and a selected `>>` form), plus `O BACKUP / O STATUS / O TUSIHN / O TOUR MODE / O EXHIBITION` with `ON`/`OFF` toggles, and `HARD ERROR` / `ID OVER ERROR`. These are referenced by a pointer table at `0x0830CC90–0x0830CDE0`. However:

* no code path from any reachable screen to that menu was found;
* a Thumb breakpoint on the most likely menu handler (`0x0801AD7C`) never fired across boot, all normal screens, and 12 held-button combinations;
* the game's only input consumer is a conventional 4-slot joypad reader (`0x08002D40–0x08002F..`, controller array `0x0300306C`, stride `0x24`, active-high `held` at `+2`) with hold counters — there is no sequence/history matcher;
* a 4 MiB scan for button-mask tables found 2,218 contiguous-u16 candidates, all of which are graphics/text/AI data, not button codes.

No published in-game code exists for the GBA SKU either: GameFAQs' GBA cheats page, TCRF, and ChapterCheats list none; every code found on the web is a GameShark/CodeBreaker/Action-Replay/GameGenie device code and is deliberately out of scope here.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:317`, 3× scale. Keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold keys 150 ms.
* Boot → WTA logo → title "Press START" → **Start** → Main Menu (4 tiles: EXHIBITION, WTA TOUR, LINK MODE, STATUS).
* Walked paths (all screenshots on disk in the work dir):
  1. EXHIBITION → Play Style (Singles/Doubles brackets) → Player Select (4×5 = 20 portraits) → R → player Status radar (POWER/SPEED/VOLLEY/SERVE/STROKE/LOG).
  2. WTA TOUR → Play Style → Player Select → R → player Status (second character, Justine Henin).
  3. STATUS → 20-player list → R → per-player stats (L/R scroll).
  4. LINK MODE → "Connecting… / Waiting for other player(s) to select Link Mode. Please wait…" — local link waiting screen; no menu beneath it.
* Savestate at the title screen (`WTA Tour Tennis.ss1`) decoded: `gbAs` chunk inflates to 397,312 bytes; IWRAM at raw `0x19000`; scene word `0x03003032 = 0x0000` (title).
* Debugger checks (mGBA built-in `-d` pty debugger): `break/t 0x0801AD7C` then `continue`; combos held through XTEST: L+R+Start, L+R+A+B, L+R+Select, Select+Start, A+B+Start+Select, L+R, and an L+R+Up+Down+A+B blob. Zero breakpoint hits.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| ROM base / entry | `0x08000000` / `0x080000C0` | header |
| Debug ASCII string bank | `0x080449D0–0x08044B10` | `strings -t x`, `xxd` |
| `GO TOUR`…`GO LOGO` strings | `0x080449DC–0x08044A60` | literal bytes |
| `>>GO TOUR`…`>>GO LOGO` | `0x08044A24–0x08044A60` | literal bytes |
| `HARD ERROR` / `ID OVER ERROR` | `0x08044A6C` / `0x08044A7C` | pointer xrefs `0x0801C720`, `0x0801C86C` |
| `O BACKUP` / `O STATUS` / `O TUSIHN` / `O TOUR MODE` / `O EXHIBITION` | `0x08044ACC / AD8 / AE4 / AF0 / B00` | pointer table |
| Staff-roll text | `0x08044BF3+` | `strings -t x` (Director, Programming, Sound Production, names) |
| Debug/menu pointer table | `0x0830CC90–0x0830CDE0` | u32 scan for string pointers |
| GO-label sub-table | `0x0830CD60–0x0830CD90` | 12 pointers to the GO strings |
| Option-label sub-table | `0x0830CDB0–0x0830CDD4` | 10 pointers to the option strings |
| Table dispatcher | `0x0801AD5C` | `LDR r1,=0x0830CC90; LDR r0,=0x03003032; ldrh; lsls #2; ldr; BL 0x0803A860` |
| Scene/mode word | `0x03003032` (IWRAM, `u16`) | 200+ literal references; `0` at title in savestate |
| Joypad reader | `0x08002D40–0x08002F..` | 5 literal refs to `0x04000130` |
| Controller array | `0x0300306C`, 4 slots × `0x24` bytes | `0x08002D8A`, `0x08002DBC`, `0x08002DFE` |
| `held` (active-high) | controller `+2` | `0x04000130 ^ 0x3FF` at `0x08002D46/9C/38/7C` |
| Debug-ish handler (A+Start / 16-frame timer bumps scene) | `0x0801C96C`, `0x0801C9B0` | mask `0x9` check, `0x03003C0D` counter, `strh` to `0x03003032` |

## 5. Algorithm

There is **no password/checksum validator to model**. The relevant algorithms are:

1. **Input** (derived from `0x08002D40`): for each of 4 controller slots, `held = ~KEYINPUT & 0x3FF`, stored as `u16` at slot+2; bytes at `+0x1B..+0x1E` are per-button hold-duration counters. Buttons are sampled into a history only for hold counting — no prefix/sequence comparison exists anywhere in the input path.

2. **Scene dispatch** (derived from `0x0801AD5C`): `handler = *(u32*)(0x0830CC90 + 4 * (*(u16*)0x03003032))`; the result is passed as a function pointer to helper `0x0803A860`. The debug GO-labels live as data inside the same table region but no code literal loads their base, so no reachable renderer for them was identified.

3. **Debug scene-bump handlers** (derived): `0x0801C96C` checks `held & 0x09` (A+Start) and, after a delay driven by `0x03003C08`, executes `(*(u16*)0x03003032)++`; `0x0801C9B0` increments a byte at `0x03003C0D` and bumps the scene when it reaches `0x10`. These are handlers *inside* the debug region, not the entry gate.

No encoder, decoder, checksum, alphabet, or mask sequence exists to reimplement. Therefore no novel code can be minted; §6b records the bounded negative instead.

## 6. Tables

**Debug string bank (all ASCII, file `0x449D0` → ROM `0x080449D0`):**

| ROM address | Text |
|---|---|
| `0x080449D4` | `ON` |
| `0x080449D8` | `OFF` |
| `0x080449DC`, `0x080449E8`, `0x080449F4`, `0x08044A00`, `0x08044A0C`, `0x08044A18` | `  GO TOUR`, `  GO EXHIBI`, `  GO MENU`, `  GO TITLE`, `  GO DEMO`, `  GO LOGO` |
| `0x08044A24`, `0x08044A30`, `0x08044A3C`, `0x08044A48`, `0x08044A54`, `0x08044A60` | `>>GO TOUR`, `>>GO EXHIBI`, `>>GO MENU`, `>>GO TITLE`, `>>GO DEMO`, `>>GO LOGO` |
| `0x08044A6C`, `0x08044A7C` | `  HARD ERROR`, `  ID OVER ERROR` |
| `0x08044A8C`, `0x08044A98`, `0x08044AA0`, `0x08044AAC`, `0x08044ABC` | `  back up`, `status`, `  tushin`, `  tour mode`, `  exhibition` |
| `0x08044ACC`, `0x08044AD8`, `0x08044AE4`, `0x08044AF0`, `0x08044B00` | `  O BACKUP`, `O STATUS`, `  O TUSIHN`, `  O TOUR MODE`, `  O EXHIBITION` |

`TUSIHN` is the romanisation of 通信 ("communications" = the game's Link Mode), confirming these are internal developer labels for the game's own screens.

**Pointer table** at `0x0830CC98–0x0830CDD4` (26 confirmed string pointers, listed in §4). Entries are little-endian `u32` ROM addresses; the interleaved values in `0x0830CCA0–0x0830CD58` and `0x0830CD94+` are Thumb function pointers (`addr|1`).

**Playable roster:** 20 players (4 rows × 5), all selectable on a fresh boot at Player Select and Status. No locked silhouettes, no `?` entries, no unlock messages were observed on any walked screen. (The GameCube SKU's "20 unlockable players" fact does not transfer to this GBA SKU — see guide §16.11.)

## 6b. Enumeration

**Cheat-space definition:** empty. There is no code alphabet, no code length, no checksum width, no hard-coded accepted-code table, and no button-sequence table. Consequently no code can be generated, and the deliverable for this engagement is a **bounded negative with counts**, not a novel code.

**Enumeration of what was checked (all counts from this ROM hash):**

| Search space | Count / result |
|---|---|
| ASCII strings ≥5 chars in the 4 MiB image | 13,074; only ~30 are meaningful ASCII (26 in the debug bank `0x449D0–0x44B10`, plus the staff roll at `0x44BF3+`). All visible in-game UI labels are **font/tile-index rendered** — confirmed by screenshots (Main Menu, Player Select, Status, Link Mode all render text as pixel glyphs with no corresponding `strings` hit). Text-bank status: decoded by rendering, not by `strings`; a "no string hit" was therefore never treated as "no UI". |
| Published in-game codes (GameFAQs GBA, TCRF, ChapterCheats, web searches incl. JP/EU titles) | 0. Every code returned is a cheat-device (GameShark/CodeBreaker/AR/GameGenie) code → out of scope. |
| Literal `u32` pointers into the debug string bank | 26, all in the single table `0x0830CC98–0x0830CDD4`; 2 additional error-string xrefs at `0x0801C720` / `0x0801C86C`. |
| Code refs (`LDR` literal) into the debug table region `0x0830CC80–0x0830CE20` | 14, at `0x0801AD5E`, `0x0801B0EE`, `0x0801B332`, `0x0801B4C2`, `0x0801B876`, `0x0801B8BE`, `0x0801BD9E`, `0x0801BDE6`, `0x0801C58C`, `0x0801CD2C`, `0x0801CD50`, `0x0801D516`, `0x0801ED32`, `0x0802262E`, `0x08027002`. **None** references the GO-label sub-table base `0x0830CD60`. |
| Direct BL calls to the candidate handlers `0x0801AD7D`, `0x0801AF6A`, `0x0801C96D`, `0x0801AD5D` | 0 each — they are reached only through the table dispatcher. |
| References to input hardware `0x04000130` | 5 (`0x08002D78`, `0x08002DB0`, `0x08002E58`, `0x08002ED4`, `0x0802C2AC`); all are standard joypad polling. |
| Button-mask table candidates (contiguous ≥4 `u16`s, each ≤`0x3FF`, popcount ≤4, scanned across all 4 MiB) | 2,218 runs; inspected the plausible ones (`0x0804093C`, `0x08042EF0`, `0x08043CF8`, `0x08043E76`, etc.) — all are graphics/tile/AI data, none is a press sequence. |
| Button combinations held in-emulator at Main Menu / title | 12 (L+R+Start, L+R+A+B, L+R+Select, Select+Start, A+B+Start+Select, L+R, L+R+Up+Down+A+B, Start, plus D-pad combos); 0 hidden screens, 0 menu changes beyond normal navigation. |
| Breakpoint `break/t 0x0801AD7C` during boot + 12 input tests | 0 hits. |
| Reachable screens walked with RAM/screenshot evidence | 9 distinct screens (title, Main Menu, Play Style, Player Select, player Status radar, WTA-Tour Player Select, Status roster, Status stats, Link Mode waiting). |

**Bounds proven:** the cheat input surface is empty — no alphabet to enumerate, no validator to call, no code table to exhaust. The debug residue is bounded as *data with no reachable renderer*: 26 string pointers, 0 code literals to their sub-table, 0 BL xrefs to the candidate handlers, 0 breakpoint hits, 0 activation combos. This is a **"dead/gated code"** negative in the sense of guide §16.3 (strings and handlers exist, no caller/table entry reaches them), not merely "not tested".

## 7. Validation evidence

* **Observed (emulator):** all 9 screens listed in §3/§6b; screenshots saved; all 20 player portraits available on a fresh boot; Link Mode only waits for a second console.
* **Observed (RAM):** savestate `gbAs` inflate → 397,312 bytes; IWRAM at raw `0x19000`; `0x03003032 = 0x0000` at title; `0x03003C08 = 0x3E0`.
* **Derived (disassembly):** input formula `held = ~KEYINPUT & 0x3FF` at `0x08002D46/9C/38/7C`; dispatcher `0x0801AD5C`; scene-bump handlers `0x0801C96C` / `0x0801C9B0`; absence of sequence matching in the 5 KEYINPUT-referencing regions.
* **Derived (static counts):** string/pointer/BL/xref counts in §6b.
* **Inferred (not observed):** that the GO-label table was once wired to a debug scene selector. The labels and their two-state (`  ` / `>>`) forms are characteristic of a menu, but no live renderer was reached, so this is explicitly an inference.
* No novel code was entered because no code format exists; no rejection test applies. This is reported as a bounded negative, not as an unattempted generation.

## 8. Unknowns

* It was not proven that the GO-label debug menu is permanently unreachable under *every possible* condition (e.g., a save-flag set only after clearing all tournaments, a link-partner signal, or a boot-time hold not among the 12 tested). The evidence supports "dead/gated residue with no found gate", not a mathematical proof of unreachability across all game states.
* The exact original purpose of `HARD ERROR` / `ID OVER ERROR` and the `ON`/`OFF` toggle variables (`0x03003C08`, `0x03003C0D`, `0x03003C44`, `0x03003C46`) was not fully traced; they are consistent with debug/development instrumentation.
* WTA Tour progression (prize money, ranking, Grand Slam unlocks) was not played to completion; it is normal game progression, not a cheat surface.

## 9. Tooling

* `md5sum` / `sha1sum` / `sha256sum`, `file`, `xxd`, `strings -t x` (Phase 0/1).
* `arm-none-eabi-objdump -M force-thumb` and Capstone 5 (Python) for literal/BL/xref scans; helper scripts in `/tmp/opencode/wtatennis/`: `scan_ptr.py`, `scan_tbl.py`, `scan_bl.py`, `scan_masks.py`, `scan_codetable.py`, `dis.py`, `lits.py`, `find_lit.py`, `find_range.py`, `parse_state.py`.
* mGBA 0.10.5 under Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input, `scrot` screenshots; `-d` pty debugger for breakpoints; savestate `gbAs` zlib chunk decoded with Python for RAM evidence.
* REA/Ghidra 12.1.4 was opened on the raw image (747 procedures) but its ARM/Thumb auto-analysis did not map the candidate Thumb addresses, so conclusions rest on objdump/Capstone + emulator, per the guide's raw-GBA path.
* No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms, and observations are published.
