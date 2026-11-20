# Ultimate Puzzle Games (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ultimate Puzzle Games/Ultimate Puzzle Games.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `ULTIMATE PUZ` |
| Game code | `BUAE` |
| Maker code | `5M` |
| Version / fixed / complement / checksum | `0x00` / `0x96` / `0x2E` / `0x0000` |
| Entry word | `0xEA00002E` → stock `0x080000C0` crt0 (no cracktro patch) |
| MD5 | `1edb0b88ee507f5176900c419c52b570` |
| SHA-1 | `eb3698c554bac2eba6e8cbd310e8414b7e6fba98` |
| SHA-256 | `4acb4512514c7478bf1b779011b94b75deb258095d93b6cd900ea2c10d045c18` |

Two full 156-byte Nintendo-logo hits: file `0x0` (main header) and file `0x1D19D8`
(embedded second header: code `AGBJ`, maker `01`, empty title, ARM crt0 at
`0x081D1AB8`). The second image is the **Game Copy** multiboot slave program
referenced by the literal pointer at file `0x79C` (`0x081D19D8`); it contains
SIO/multiboot constants (`0x04000120`, `0x020000AC`, `0x020002B0`,
`0x02010000`) and its own copy of the puzzle UI strings around `0x1D7EC5`.
It is a link-transfer payload, not a cheat device.

## 2. Executive summary

**No in-game cheat system exists in this ROM.** There is no password entry,
no button-code sequence, no hidden/debug menu and no unlockable content.
The only developer-intended "cheat-like" feature is the ordinary, ungated
**Solve Puzzle** / **Solve Letter** solution reveal in the in-game START menu,
plus solution marking of individual clues. Every puzzle type and all 50
Crossword puzzles are selectable from a fresh save (no locks, no gating flags).

This is a **bounded negative** (§0.2 point 5), not an absence of effort: all
reachable screen types were walked in mGBA with RAM evidence; the complete
UI string bank (51 strings) was enumerated and decoded; the whole ROM was
searched for code alphabets, mask sequences, debug keywords and validator
tables with explicit counts recorded in §6b. Published-code recon found
**zero** codes (CheatingDome lists "00"; all web FAQs are crossword-solution
charts). Consequently there is no validator to reverse and no code to mint —
§6b states the negative with counts instead.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `mgba -3`.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrow keys. Hold keys 120–200 ms; 60 ms moves the
  carousel cursor one slot.
* Path: boot → splash (A, A) → category carousel → A → puzzle list → A →
  puzzle grid → Start → tabs **Game** / **Options**.
* Built-in reveal: puzzle grid → Start → Game → **Solve Puzzle** → YES.
  Observed on Backword 1 and Crossword 1; no completion prerequisite.
* RAM evidence: mGBA savestates (Shift+F1..F5) parsed per guide §16.13
  (`gbAs` PNG chunk, zlib → 397,312-byte raw state; IWRAM at `0x19000`,
  EWRAM at `0x21000`). Holding A confirmed `0x03001CFC = 0x0001`, validating
  the IWRAM mapping.

## 4. Address map

| Address (ROM unless noted) | Meaning | Evidence |
|---|---|---|
| `0x08000000`–`0x080000C0` | ARM crt0, stock entry | Derived (header/disasm) |
| `0x08008CB0`, `0x08013C24` | Input-lock helpers: `KEYINPUT \|= 0x03FF` | Derived (disasm) |
| `0x0800ABAC` | Key routine: `held = ~KEYINPUT & 0x3FF`; `pressed = held & ~old` | Derived (disasm) |
| `0x03001CFC` (RAM) | held keys, active-high (`A=1,B=2,Sel=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,R=0x100,L=0x200`) | Derived |
| `0x03001D04` (RAM) | newly-pressed keys | Derived |
| `0x03002FF0` (RAM) | copy of held keys written by dispatcher | Derived |
| `0x0800ABDC` | 21-case scene dispatcher on byte at `0x030021CC`; jump table `0x0800AC0C` | Derived |
| `0x08026488`–`0x080268D0` | complete UI string bank (51 ASCII strings) | Derived (dump) |
| `0x080103F8`–`0x08010420` | Game/Options menu string-pointer pool | Derived |
| `0x08010470`–`0x0801048C` | alternate Game menu pool (Solve Letter, Save Puzzle, …) | Derived |
| `0x080E8F0`–`0x080E910` | confirmation-dialog string pool | Derived |
| `0x080A500`–`0x080A668` | Game Copy (link transfer) string pool | Derived |
| `0x081D19D8` | embedded AGBJ multiboot header (Game Copy slave) | Derived |
| SRAM `0x0E000000`, 512 bytes | save data; observed all `0xFF` on fresh boot (no unlock bits set) | Observed |

File offset ↔ ROM address: `addr = 0x08000000 + file_offset` for the main
image. The multiboot image is linked at `0x08000000` but loaded over SIO.

## 5. Algorithm / validator search

There is **no validator** to reimplement. The closest input-consuming logic is:

1. `0x0800ABAC` reads `KEYINPUT` (`0x04000130`), inverts it into an active-high
   10-bit mask, computes `pressed = held & ~previous`, stores both to globals.
2. `0x0800ABDC` copies held keys to `0x03002FF0`, then dispatches on a byte at
   `0x030021CC` through a 21-entry table. This is per-frame navigation, not a
   sequence matcher: there is no progress counter, no ring buffer and no
   comparison against a stored mask array.
3. Puzzle answer entry (e.g. Crossword clue entry) validates letters against
   the puzzle solution only. It is a puzzle-answer field, not a password gate:
   no `strcmp`/`memcmp` against a code table, and its buffer is not read
   outside the puzzle handler (guide §16.2b).

**Solution reveal (only cheat-like behaviour):** selecting Solve Puzzle writes
the known solution letters into the grid buffer. Savestate diff before/after
the reveal produced **272 changed byte ranges**; grid cells in IWRAM around
`0x1AF10`+ changed from `0x0000` to letter values, and the HUD/overlay region
`0x19480`–`0x1965D` changed wholesale. This is *Observed* (screenshot +
savestate diff); the writing function itself was not isolated (*Inferred*
that it is the generic solve routine near the UI pool at `0x080E8F0`).

## 6. Tables

**UI string bank (complete, 51 strings, `0x08026488`–`0x080268D0`):**
`Puzzle`, `Saved`, `Done`, `error`, `ACROSS`, `DOWN`, Game Copy prompts
(`Turn on and connect a Game Boy® Advance.`, `Transmitting game...`,
`Puzzle Complete`, `Saving`, …), `Select Save Slot`, `Solve Puzzle`,
`Reset Puzzle`, `New Puzzle`, `Quit`, `Save`, `Music`, `SFX`, `Background`,
`How To Play`, `Solve Letter`, `Save Puzzle`, `Select Puzzle Type`,
`Select Puzzle`, and their confirmation sentences. **None** mentions a
password, cheat, code, debug, secret or unlock.

**Game menu (generic):** Solve Puzzle / Reset Puzzle / New Puzzle.
**Alternate Game menu:** Solve Letter / Reset Puzzle / New Puzzle /
Save Puzzle / How To Play.
**Options menu (exactly 6, wrap-around confirmed):** Quit / Save / Music /
SFX / Background / How To Play.
**Category carousel (13 entries):** Crossword, Kriss Kross, Word Search,
Code Breakers, Backword, Cryptic, Diamonds, Easy Crossword, Number Jig,
Micro WS, Mini K, Mini WS, Game Copy.

**Text encoding note:** visible footer labels such as `CLUE`, `GRID`, `SELECT`
have **no** uppercase literal; they are stored as lowercase ASCII (`clue`,
`grid`, `select`) and drawn as capitals (guide §11's +0x20 shift). Therefore
all UI text is ASCII and there is **no font-index text bank left undecoded**.
`TELEGAMES`, `Puzzle.tv` and "Licensed by Nintendo" are bitmapped logos, not text.

## 6b. Enumeration

**Code space definition:** none. There is no alphabet, length, checksum,
field layout, lookup table or reserved-bit space to characterise. Space size
= 0 accepted cheat codes.

**Novel code:** not applicable — no code system exists from which to mint one.
This section therefore delivers the bounded negative required by §0.2 point 5.

**Screen enumeration (all walked, 13 screen types):**
boot splash; category carousel (13 entries); puzzle list (e.g. Crossword 1–50,
all enabled); puzzle grid; crossword clue-entry keyboard; START menu with two
tabs; five confirmation dialogs (solve/reset/new/quit/overwrite); save-slot
dialog; Game Copy link screen; How To Play (8 pages of "Codebreaker"
instructions); puzzle-complete/saving prompts. No additional screen appeared
after five common button combos on the carousel (`L+R+Start`,
`L+R+Start+Select`, `A+B+Start`, `Select+A+B`, full Konami sequence) — all
either did nothing or performed ordinary navigation.

**Search space checked, with counts:**

| Search | Space | Result |
|---|---|---|
| UI string bank `0x26488`–`0x268D0` | 51 strings | 0 password/cheat/debug/unlock/secret keywords; every string has 1–3 direct literal xrefs, all to known screens |
| Full-ROM case-insensitive keyword scan | 4 MiB | 60 hits examined (`CHEAT`, `Secret`, `Unlock`, `Special`, `Bonus`, `Solution`, `warp`, …): **all** crossword clues/word banks — false positives (§16.11) |
| Canonical code alphabets (`A-Z…`, `a-z…`, `0123456789…`, 5 patterns) | 4 MiB | 0 hits |
| Button-code sequences: Konami, active-high and active-low u16 encodings | 4 MiB | 0 hits |
| Runs of ≥4 consecutive single-button u16 masks | 4 MiB | 5 runs (`0x20F22`, `0x60BBA`, `0x10F1EC`, `0x10F1FC`, `0x10F254`); **0** in main code region `0x0`–`0x1D19D8`, all in data/multiboot — no mask table |
| Literal references to `0x04000130` (KEYINPUT) | 4 MiB | 3 (`0x08008CB0`, `0x0800ABAE`, `0x08013C24`) — two input locks + one key-state computation; no consumer chain |
| Literal references to key globals `0x03001CFC` / `0x03001D04` | 4 MiB | 2 / 1, all inside the input routine and its direct caller — no other reader, hence no sequence matcher |
| Debug-magic constants (`0xA5A5A5A5`, `0x12345678`, `0xDEADBEEF`) | 4 MiB | 3 / 0 / 0 hits, all in crossword data — no boot magic / gate |
| Published codes | web recon | CheatingDome "Ultimate Puzzle Games 00"; GameFAQs/Neoseeker host only crossword-solution charts; no password or button-code list found |

**Rejection bounds:** not applicable — no validator accepts or rejects a code.
A bounded behavioural check was performed instead: the letter-entry keyboard
accepts only puzzle letters and validates them against the current clue
(Observed, `bg_after.png`), not against any code table. "Select Puzzle Type" /
"Select Puzzle" strings exist in the main image (2 and 1 data-table xrefs) but
no reachable flow displayed that screen; an equivalent copy exists inside the
Game Copy multiboot, so the main-image copies are most plausibly dead or
link-mode-only (*Inferred*, recorded as an Unknown in §8).

## 7. Validation evidence

* **Observed (emulator):** boot, all 13 carousel entries, puzzle lists,
  puzzle grids, clue-entry keyboard, both START tabs and all six Options rows,
  Game Copy screen, How To Play pages; ungated Solve Puzzle on Backword 1 and
  Crossword 1; five button combos with no hidden effect; 512-byte `.sav` all
  `0xFF` on a fresh save; key global `0x03001CFC = 0x0001` while A held.
* **Observed (savestate RAM diffs):** 272 changed byte ranges for Solve Puzzle
  (grid + overlay), 28 changed IWRAM ranges for carousel→puzzle transition.
* **Derived (static):** input globals and routines; 21-case scene dispatcher;
  complete 51-string UI bank and every xref; absence of alphabet/mask/code
  tables by the bounded searches above; AGBJ image is a multiboot link slave.
* **Inferred:** the main-image "Select Puzzle Type" screen is dead or
  link-mode-only; the solve routine is the generic one near `0x080E8F0`.
* No prompt-injection content was encountered; all fetched pages and ROM
  strings were treated as data only.

## 8. Unknowns

* Whether the main-image "Select Puzzle Type"/"Select Puzzle" strings
  (`0x268AC`, `0x268C0`, referenced only from data tables at file `0x1A184`,
  `0x1A6FC`, `0x1A70C`) have any reachable caller — no retail input path
  reached them; reaching them would require a second GBA for Game Copy or an
  unreachable scene-dispatch case.
* Individual behaviour of the other 21 scene-dispatch cases not observed in
  the UI walk (all observed screens map into case `0x0F`). No evidence any is
  a debug screen, but they were not individually forced.
* Exact save-record layout: only the all-`0xFF` fresh state was inspected; no
  completed puzzle was saved, so no "Done" bit encoding was recovered. No
  unlockable content was observed, so this does not affect the conclusion.

## 9. Tooling

* `strings -t x`, `grep -abo`, `xxd`, Python byte/pattern scans and Capstone
  5.0.7 (`CS_MODE_THUMB`) for literal pools, alphabet/mask scans and xrefs.
* `arm-none-eabi-objdump -M force-thumb --adjust-vma=0x08000000` for the input
  and dispatcher routines.
* mGBA 0.10.5 + Xvfb `:315` + openbox + xdotool + scrot; `ui.py` (input helper),
  `ssdiff.py` (savestate `gbAs` zlib parser / RAM diff), `screenstate.py`.
* Save-state RAM-layout fact reused from guide §16.13 (IWRAM `0x19000`,
  EWRAM `0x21000`, 397,312-byte raw state).
* No GameShark/CodeBreaker/Action Replay codes were used or reported.
  No ROM or copyrighted assets are redistributed; only hashes, addresses and
  findings are published.

---

*Analyst note: all emulator/savestate artifacts were removed from the ROM
folder after the investigation; only this report remains.*
