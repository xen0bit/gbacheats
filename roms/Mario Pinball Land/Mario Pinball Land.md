# Mario Pinball Land (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mario Pinball Land/Mario Pinball Land.gba` |
| Size | 8,388,608 bytes (`0x00800000`) |
| Header title | `MARIO BALL` |
| Game code | `BMVE` (Europe, "Super Mario Ball" in EU/JP/AU) |
| Maker | `01` (Nintendo); developed by Fuse Games Ltd. |
| Version | `0x00` |
| Entry branch | `0xEA00002E` (stock branch to `0x080000C0`) |
| Header checksum | `0x0000`; complement byte `0x13` (sum of `0xA0..0xBD` = `0xE7`, i.e. not a canonical retail complement — header was likely rebuilt during dumping; no code patched) |
| MD5 | `08c41541eb69a1d652937ed3f88824be` |
| SHA-1 | `3fdcd3bb30d61b4dd6829dbdc1a0ac116618b87d` |
| SHA-256 | `a26faded57dd0938c39cc9d2c83641f81bbf5f0c209a44c21c4096bd38450b77` |

**Phase 0 result:** exactly one GBA header (Nintendo-logo scan found one logo at file `0x04` / header `0x0`). No second image, no appended trainer, no cracktro. `0x08` header scan: clean. Entry word stock. Cart has 512-byte EEPROM (`0x0E000000`), mapped at `0xD000000` per GBA size rules.

## 2. Executive summary

**There is no developer-intended cheat code, password, button sequence, or hidden debug menu in this ROM.** The only in-game "unlockables" are ordinary gameplay/save-gated content (Time Attack mode after beating two world bosses; a 35-star room and alternate ending after collecting all 35 stars), which is not a code system (§16.18).

The three things that superficially look like a code surface were all checked and eliminated:

1. **A 27-symbol alphabet** `ABCDEFGHIJKLMNOPQRSTUVWXYZ ` at `0x087FB870`. Its only consumers (`0x080298A0`–`0x08029A60`) increment a cursor over 0..26 and write the selected glyph into a 3-byte name buffer at `0x03003004`–`0x03003014`, then draw it via `setAnimationFrame`. This is the **high-score / best-time name-entry field**, not a password (§16.2b). No `strcmp`/`memcmp` reads that buffer for validation.
2. **An ASCII string bank** at `0x087FBE..0x087FC3..` holding all menu labels. Fully decoded (§6). It contains `CONTINUE / NEW GAME / LOAD GAME / ADVENTURE / TIME ATTACK / TIME ATTACK / HIGH SCORES / BEST TIMES / PAUSED / SAVE & QUIT / RETRY / YES / NO / STAFF CREDITS` and ending strings. There is **no** `PASSWORD`, `CHEAT`, `SECRET`, `UNLOCK`, `WARP` or `LEVEL SELECT` string in ASCII, `+0x20` case-shifted form, UTF-16LE or UTF-16BE (all counts = 0).
3. **Published "cheats"** are GameShark/CodeBreaker RAM patches (lives `0x03000000`, score `0x03000004`, stars `0x03000014`/`0x0300578C`, stage `0x03000030`, etc., documented by cturt) — explicitly out of scope (memory-edit codes), and not developer-intended. 3rd party cheat indexes' archived cheat page lists **only three unlockables**, no passwords or button codes.

Every reachable screen was booted and walked on the real emulator with RAM evidence (§7). The menu dispatcher's complete domain is `{0,1,2,3}` and its three 6-entry jump tables have only 5 unique targets each (duplicate defaults) — no unlabelled menu index. No novel code was minted because **no code space exists**; this is a proven negative, not an untested one.

## 3. How to reproduce

```bash
# Emulator (own display only)
Xvfb :319 -screen 0 1024x768x24 -nolisten tcp &
DISPLAY=:319 openbox &
export DISPLAY=:319 SDL_AUDIODRIVER=dummy
mgba -g -3 "roms/Mario Pinball Land/Mario Pinball Land.gba" &

# Persistent GDB client (stub is single-client and corrupts on batch detach)
gdb-multiarch -quiet -x gdb_init.gdb < gdbin > gdbout.log &
# gdb_init.gdb: set architecture arm / set pagination off / target remote :2345
# While running: "interrupt", read, then "continue&"
```

Keymap (verified against `KEYINPUT` `0x04000130`: held A -> `0x3FE`, released -> `0x3FF`): GBA A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold keys 100–150 ms.

Exact screen path (attract loops forever until a key is pressed):
* Boot -> Nintendo/Fuse logos -> character attract -> **title "PRESS START"** (`0x087FBEC8` pattern; screen-state `0x03001628 = 3`).
* Title + Start with **no save** -> Mario intro -> gameplay (stage `0x03000030 = 0`, lives `0x03000000 = 2`, score `0x03000004 = 0`).
* Title + Start with **a valid save** -> `LOAD GAME / NEW GAME` menu (state `1`).
* In gameplay + Start -> `PAUSED / CONTINUE / SAVE & QUIT`; Down + A on `SAVE & QUIT` writes a 512-byte EEPROM save and returns to title.
* Title attract cycles through `HIGH SCORES` (names ADE/CMP/KEV/CAI/KAA), `BEST TIMES` and multi-world gameplay demos.
* Static-only menus (types `0` = `ADVENTURE/TIME ATTACK`, `2` = `YES/NO`) are reachable from the save-present title flow; their labels and item counts are proven from `0x0801700C` literal pools (§4).

Codes tested: none exist to test; common GBA button-code attempts (`L+R+Start+A+B`, Konami sequence, `L+R+Start`) on the title screen produced **no** state change beyond the normal attract progression (`0x0300162c` only counted down).

## 4. Address map

| Address (ROM/RAM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | header / entry `0xEA00002E` | Observed (header dump) |
| `0x0801700C` | menu renderer; writes menu type to `0x03001628`; type 0=`ADVENTURE/TIME ATTACK`, 1=`LOAD GAME/NEW GAME`, 2=`YES/NO`, 3=none | Derived (disassembly + literal pools) |
| `0x08017414`–`0x080175C0` | title/menu state machine; 3 jump tables at `0x081DF2B8/2D0/2E8`, 6 entries each, 5 unique targets | Derived |
| `0x080298A0`–`0x08029A60` | 27-symbol name-entry cursor over alphabet at `0x087FB870` | Derived |
| `0x0802CD00`–`0x0802D14` | `restoreLoadedData`; save-valid word `0xC769D9A9` vs `0x38962656` | Derived (cturt cross-check) |
| `0x080363??` | DMA3 wrapper / EEPROM copy | Derived (cturt) |
| `0x0801E6C8 / 0x0801E9F0 / 0x0801E8DC` | `setupStage` / `mainGameFunction` / `clearUpStage` switch dispatch | Derived (cturt + BL scan) |
| `0x087FB870` | name alphabet `ABCDEFGHIJKLMNOPQRSTUVWXYZ ` + NUL | Observed |
| `0x087FBEC8`–`0x087FC39C` | ASCII text/credit bank (§6) | Observed |
| `0x087F6F4C` | 80-entry attract/menu decision table | Derived |
| `0x87FCCD8` | resource pointer table | Derived (cturt) |
| `0x03000000 / 04 / 08 / 14 / 2C / 30 / 34` | lives / score / yellow coins / stars / item / stage / stageFlags | Observed (GDB) + cturt |
| `0x0300578C` | alternate star count (save copy) | Derived (cturt) |
| `0x03001600`–`0x03001630` | menu text/sprite state, menu type (`0x03001628`), timer (`0x0300162C`) | Observed (GDB) |
| `0x03003004`–`0x03003014` | 3-byte name-entry buffer + cursor | Derived |
| `0x04000130` | KEYINPUT (active-low) | Observed (GDB) |
| `0x0E000000` (512 B) | EEPROM save: magic `05 F6 50 4D 6F 4D E6 5F`, scores @8/148, game state @152/500 | Derived (cturt; magic bytes present at `0x080295A0` etc.) |

## 5. Algorithm

No password/checksum algorithm exists. The only "algorithmic" surfaces are:

* **Menu type dispatch:** `render(type)`: `type==3` -> draw nothing; `type==1` -> draw `LOAD GAME`/`NEW GAME`; `type<1` -> draw `ADVENTURE`/`TIME ATTACK`; `type>=2` -> draw `YES`/`NO`. Item selection is a single index into a 2-entry list; no hidden third entry (each menu renderer loads exactly two string pointers, e.g. `0x08017084`/`0x08017088` and `0x08017150`/`0x08017154`).
* **Name entry:** cursor `i` in `0..26`; `buf[pos] = alphabet[i]`; glyph frame = ASCII byte (space -> 0) via `setAnimationFrame(0x0802F0C4)`. No comparison against a stored code.
* **Save validity:** `saveValid` word at save offset 496; `0xC769D9A9` on load, `0x38962656` on `SAVE & QUIT`. This gates the save-present menus; it is set only by game flow, never by controller input in the cheat sense.

## 6. Tables

**Complete ASCII text bank (`0x087FBEC8`–`0x087FC39C`)** — every string, in order:
`CONTINUE`, `CONGRATULATIONS!`, `ALL EVENTS CLEARED!`, `TOTAL`, `SCORE`, `BALL BONUS`, `BEST TIMES`, `HIGH SCORES`, `SAVE & QUIT`, `PAUSED`, `RETRY`, `SAVING...`, `SAVED GAME WILL BE ERASED. OK?`, `YOUR GAME WON'T BE SAVED. OK?`, `WELL PLAYED!!!`, `A NEW HIGH SCORE!`, `A NEW BEST TIME!`, `ADVENTURE`, `TIME ATTACK`, `LOAD GAME`, `NEW GAME`, `STAFF CREDITS`, `YES`, `NO`, then the Fuse/Nintendo credit roll. Alphabet at `0x087FB870`. **No code-like string in the bank.**

**Menu items (complete):**

| Menu type | Items | String addresses | Reachable |
|---|---|---|---|
| 0 | ADVENTURE, TIME ATTACK | `0x087FBFE0`, `0x087FBFEC` | Yes (save flow) |
| 1 | LOAD GAME, NEW GAME | `0x087FBFF8`, `0x087FC004` | Yes (observed on :319) |
| 2 | YES, NO | `0x087FBFA0`, `0x087FBFA4` | Yes (save overwrite / quit prompts) |
| 3 | (none) | — | Yes (title, attract, gameplay) |

**Pause menu:** `CONTINUE`, `SAVE & QUIT` (`0x087FBEC8`, `0x087FBF38`). No hidden fourth option.

**Published unlockables (verified against archived sources):**

| Unlockable | Condition | Type |
|---|---|---|
| Time Attack mode | Defeat the bosses of two worlds | gameplay/save-gated |
| 35-Star Room | Collect all 35 stars; room in Bowser's Castle with 4 pillars, no enemies | gameplay/save-gated |
| Special ending | Collect all 35 stars | gameplay/save-gated |

These are not codes; they are save-bit/content gates. cturt's "cheats" list (lives/score/stars/stage RAM addresses) consists of external memory-edit patches, out of scope.

## 6b. Enumeration

**Space definition:** No code system exists, therefore the representable-code count is **0**. The bounded negative is established over these searched spaces:

| Space searched | Bounds / count | Result |
|---|---|---|
| ASCII text bank and whole 8 MiB ROM | `strings -n 4` -> 108,247 lines; keyword filter over `password\|cheat\|code\|debug\|secret\|unlock\|level\|menu\|table\|option\|continue\|invalid\|bonus\|test\|warp` | 5 hits, all `CONTINUE`, `BALL BONUS`, and three `TESTING*` credit lines; zero code/debug labels |
| Cheat keywords in ASCII / `+0x20` / UTF-16LE / UTF-16BE | 12 keywords x 4 encodings | **0** occurrences for every keyword |
| On-screen alphabet | 27 symbols at `0x087FB870`, only 6 xrefs (`0x08029894/9914/9950/99B8/99F8/9A60`) | All in name-entry cursor `0x080298A0`–`0x08029A60`; no validator consumer |
| Hard-coded literal code tables | literal-pool scan for every menu string; `strcmp`-style comparison search | No accepted-code string table; only UI labels |
| Button-mask sequences | every `u16` in ROM tested against active-low masks with 1–4 buttons: **1,291** runs of >=3 consecutive valid masks; **112** runs containing exact single-button masks | All runs are sequential byte patterns (`0x15D,0x15E,0x15F`, etc.) in compressed graphics/audio at `>=0x08041302`; no alternating button-mask table, no progress index/validator |
| Menu state domain | dispatcher `0x0801700C`; 3 six-entry jump tables at `0x081DF2B8/2D0/2E8` | Domain `{0,1,2,3}`; 5 unique targets per table (duplicated defaults); no unlabelled menu |
| Embedded images / patches | Nintendo-logo scan across 8 MiB | 1 header only; no trainer or second game |
| Published codes | 3rd party cheat indexes, cturt reverse-engineering notes | 3 gameplay unlockables, 0 passwords/button codes; GameShark/CodeBreaker codes are memory edits (out of scope) |

**Novel code:** not applicable — no code space to mint from. **Bounds proven by rejection:** attempted title-screen button codes (`L+R+Start+A+B`, Konami sequence, `L+R+Start`) did not open any screen or change menu state; only the normal attract timer (`0x0300162C`) advanced. Unknown-menu-index injection is impossible because the dispatcher maps every value `>=2` to the same `YES/NO` menu (no hidden branch).

## 7. Validation evidence

* **Observed** (emulator + GDB, display `:319`): boot logos, character attract, title `PRESS START`, `HIGH SCORES` with names ADE/CMP/KEV/CAI/KAA, multi-world attract gameplay, gameplay at stage `0` with lives `2`/score `0`, `PAUSED / CONTINUE / SAVE & QUIT`, `LOAD GAME / NEW GAME`, save-file creation (512 B EEPROM), return to title with save, and unaffected state after three button-code attempts. `KEYINPUT` verified active-low.
* **Derived** (disassembly): menu renderer and its two-item literal pools; title state machine and complete jump tables; 27-symbol name-entry loop; string bank contents; resource table; save layout; EEPROM magic in ROM.
* **Inferred** (not fully exercised): `ADVENTURE/TIME ATTACK` and `YES/NO` menus were proven from their literal pools and reachable code paths but were not captured in a clean screenshot because the attract loop kept advancing during manual navigation; their item counts and strings are nevertheless exact. The save-bit unlock setters were not exhaustively enumerated; 3rd party cheat indexes' three conditions are taken as published truth and are consistent with the `stars`/`stage` RAM variables.

No prompt-injection payload was found in the fetched 3rd party cheat index pages; fetched content was treated as data only.

## 8. Unknowns

* The exact save-bit index for each of the three unlockables was not isolated (§16.18 treatment would require enumerating the test/setter helper call sites); they are gameplay-gated content, not codes, so this does not affect the cheat verdict.
* Two clean screenshots of menu types 0 and 2 were not captured; their strings and two-item counts are proven statically.
* The non-canonical header complement byte (`0x13`) was not traced to a specific dumping tool; it does not affect any address in this report (entry and logo are stock).

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
* Python 3 scripts (in `/tmp/mariopinball/`): header/hash fingerprint, literal-pointer scan, Thumb `BL` target scan, keymask-run scan, ASCII/UTF-16 keyword scan, screenshot-difference attract detector.
* mGBA `-g -3` under `Xvfb :319` + `openbox`; persistent `gdb-multiarch` on port 2345 with `interrupt` / `x/..wx` / `continue&`; XTEST input via `xdotool`; `scrot` + ImageMagick `convert`/`montage`.
* Cross-reference: archived 3rd party cheat index cheats page (2018-11-26 snapshot), 3rd party cheat indexes `Notes:Mario Pinball Land`, cturt.github.io/pinball.html (reverse-engineering notes).
* No ROM or copyrighted assets were redistributed; only addresses, hashes, algorithms and tool scripts are published.
