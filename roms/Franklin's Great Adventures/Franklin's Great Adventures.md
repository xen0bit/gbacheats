# Franklin's Great Adventures (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Franklin's Great Adventures/Franklin's Great Adventures.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| `file` | Game Boy Advance ROM image: "FRANKLIN" (BFLEGY, Rev.00) |
| Header title | `FRANKLIN` (0xA0–0xAB) |
| Game code | `BFLE` (0xAC–0xAF) |
| Maker code | `GY` (0xB0–0xB1) |
| Fixed byte | `0x96` (0xB2) — correct |
| Version | `0x00` (0xBC) |
| Complement check | `0x43` (0xBD); sum of 0xA0..0xBD is `0xE7`, so `+0x43 != 0` (non-conformant) |
| Header checksum | `0x0000` (0xBE–0xBF); computed Nintendo checksum `0x9C7A` |
| Entry word | `0xEA00002E` → stock `b 0x080000C0`; standard crt0, no boot patch |
| MD5 | `36eaf4fec9e81f3ea44869033996cedd` |
| SHA-1 | `2da756bed887dbd33fc0efdd3dcd01fbb92ae0dc` |
| SHA-256 | `9458fb793556202eab5b86d65f90b82c91f3c1b43f47d727ec8b5fcdd0dad3ef` |

**Phase 0 / embedded-header scan.** The full 152-byte Nintendo logo occurs exactly **once**, at file offset `0x4` (a 16-byte signature scan also returns exactly one hit). This is a single-image retail ROM, not a multi-game cart. No appended trainer, no scene cracktro, no secondary boot stub was found. The `0x0000` checksum plus bad complement are consistent with a rebuilt header (guide §16.1), but the entry word and crt0 are stock, so the analysis sees the real game code. Save hardware is **EEPROM_V124** (string at file `0x22482C`); mGBA produces a 512-byte `.sav`.

**Relationship to the sibling ROM (queue 312).** Checked independently by header/string inspection only: `Franklin the Turtle.gba` is `BFKE`/`GY`, MD5 `e582614d06f941ff491543a721a9acb0`, SHA-256 `0c1f565afc9d39786de4451d5dfffebf8d67a268525188c397cb9bfe05ece83b`. It contains a `CHEATER` string at file `0x3E8550`; this image contains **no** `CHEAT*`/`CHEATER` string (0 hits). It also has none of the `franklin_cState*` / `gbapi` RTTI names present here. Both share only the publisher/maker code `GY` (The Game Factory) and the standard Nintendo logo; the game code, RTTI engine, text banks and hashes differ. **Nothing functional is shared** between the two images.

## 2. Executive summary

**No in-game / developer-intended cheat system exists in this GBA SKU.** There is no password screen, no password validator or code table, no on-screen keyboard with a code alphabet, no button-code matcher, no debug/test state, and no hidden menu. Every collectible-gated mini-game is an ordinary save-bit unlock earned in Story Mode (10 letters, 220/280/180/40 apples, 10 flowers, 10 shells, etc.); per guide §16.18 a save-bit unlock is not a cheat code. No published GBA password/cheat list exists to verify; the only published "cheats" found are DS Action Replay memory codes (out of scope and their addresses do not exist in the GBA memory map).

The negative is bounded, not assumed: every reachable screen was walked in mGBA with RAM snapshots, all text was decoded (it is ASCII in a u16-offset bank with an ASCII→glyph font map, not a hidden tile-indexed cipher), the 46-entry engine class registry contains no debug class, the entire 4 MiB was searched for password/cheat/debug keywords (0 hits), for multi-button compare immediates (0 code hits), for referenced button-mask arrays (0 code-region hits), and for known published-code literals (0 hits). Ten button combinations were pressed on the pause screen with no hidden screen appearing. Details and counts are in §6b.

## 3. How to reproduce

- Emulator: `mgba -3 -g game.gba` on `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, Xvfb `:318` + openbox. Keymap verified against key RAM `0x03001F08` (active-high): A=`x` (0x001), B=`z` (0x002), Select=`BackSpace` (0x004), Start=`Return` (0x008), R=`s` (0x100), L=`a` (0x200), D-pad = arrow keys. Hold ≥100 ms (≈400 ms when the GDB breakpoint is active).
- Menu path (all screens walked):
  1. Language Selection (`ENGLISH`, red arrow) — press A.
  2. Boot logos: "Franklin's Great Adventures / Licensed by Nintendo" → The Game Factory → NEKO Entertainment.
  3. Title screen `PRESS START` — press Start.
  4. Main menu: `STORY MODE`, `MINI-GAMES MODE`, `OPTIONS`.
  5. `OPTIONS`: `LANGUAGE SELECTION`, `CREDITS` (scrolling; ends with NELVANA).
  6. `MINI-GAMES MODE`: a carousel whose every entry displays `???????` on a fresh save (locked); arrows at both ends.
  7. `STORY MODE`: village overworld with apple counter `x000` and compass; Start opens `PAUSE / CONTINUE / QUIT`.
- No code was entered because no entry surface exists. Published DS codes were tested only as literal searches, not typed (they target DS RAM addresses `0x02147xxx`).

## 4. Address map

| Item | File offset | ROM address | Notes |
|---|---:|---:|---|
| Header / logo | 0x000–0x1FF | 0x08000000 | logo at 0x4 only; stock entry |
| crt0 input routine | 0x00534 | 0x08000534 | reads `0x04000130`, masks `0x3FF`, writes cached keys |
| Key getters | 0x007BA8 / 0x007BB4 / 0x007BC6 | 0x08007BA8 / 0x08007BB4 / 0x08007BC6 | update / hold-timer / held-mask wrappers |
| Engine class registry | 0x0471DC–0x047A48 | 0x080471DC–0x08047A48 | 46 descriptors, stride 0x2C, name pointer at +0 |
| RTTI name strings | 0x048058–0x04879C | 0x08048058–0x0804879C | length-prefixed names (`23franklin_cStateMainMenu`, etc.) |
| English text bank base | 0x048FC8 | 0x08048FC8 | ASCII strings with control bytes (`0x1F`, `=`-codes) |
| Text offset table | 0x04CD14 | 0x0804CD14 | `u16` offsets into the above bank |
| `??????` (locked label) | 0x04CD0A | 0x0804CD0A | 11 language copies at 0x4CD0A, 0x50F40, … |
| Area/mini-game name table | 0x10DA68 | 0x0810DA68 | 22 records × 0x16 bytes, NUL/pad-filled ASCII |
| Font ASCII→glyph map | 0x1D540D | 0x081D540D | contiguous `0x20..0x7E` (` !"#$...~`) |
| EEPROM_V124 string | 0x22482C | 0x0822482C | 512-byte save |
| Key state (RAM) | — | IWRAM `0x03001F08` | held, active-high (observed 0x0B for A+B+Start) |
| Key pressed (RAM) | — | IWRAM `0x03001F0A` | newly-pressed edge (transient) |
| Key timers (RAM) | — | IWRAM `0x03001F0C` / `0x03001F0E` | hold accumulator / repeat counter (0xE1<<4 cap, 60 rate) |
| Save magic | — | EEPROM `0x00` | `00 00 01 25 4B 44 47 4E` ("KDGN") |

## 5. Algorithm

There is no password/checksum algorithm to reimplement. The two behaviours that matter:

**Input update (derived from Thumb disassembly at 0x08000534):**
```
raw   = ~*(u16*)0x04000130 & 0x3FF        ; active-high held
held  = *0x03001F08                       ; previous frame
press = raw & ~held                       ; 0x03001F0A
*0x03001F08 = raw
```
`0x03001F0C`/`0x03001F0E` implement a 60-frame repeat / 3600-frame cap. No other code region compares the key state with a multi-button immediate (0 hits — see §6b).

**Unlock model (observed + inferred):** collectible counts earned in Story Mode are compared against dialogue thresholds; on success a per-mini-game save flag is set and the NPC says "This mini-game is now available in mini-games mode." (`0x0804A5A0`). The mini-games carousel reads those flags; when a flag is clear it renders the literal `??????` from the text bank instead of the name-table entry. The individual setter/test call sites were not fully traced to named functions; this is the one material unknown (§8).

## 6. Tables

**Collectible thresholds (from decoded English text bank, file 0x496A6–0x4A00A):**

| Item count | Unlock | NPC dialogue offset |
|---:|---|---:|
| 10 letters | Sailing boat | 0x496A6 / 0x496E1 |
| 220 apples | Orchard | 0x499C5 / 0x49A1B |
| 10 flowers | Paper airplane | 0x49B4E / 0x49B8D |
| 10 shells | Sand castle | 0x49C9E / 0x49CDC |
| 280 apples | Knight | 0x49D8C / 0x49E1C |
| 40 apples | Bicycle race | 0x49EAA / 0x49EF3 |
| 180 apples | Butterfly hunt | 0x49F8B / 0x4A00A |

**Name table at ROM 0x0810DA68 (stride 0x16):** 8 areas (`Village`, `Franklin's Garden`, `Country Road`, `Pond`, `Hill`, `Beach`, `Diamond Mines`, `Autumn Forest`) followed by 14 mini-game names (`Tidy your room`, `Fly, kite, fly`, `The bicycle race`, `The Sailboat`, `King of the paintbrush`, `Pick up the branches!`, `The vegetable garden`, `Skateboard Descent`, `The Paper Airplane`, `The Sandcastle`, `The Butterfly Hunt`, `Building a Tree House`, `Franklin the Knight`, `The Canoe Race`). This is ordinary ASCII, not a cipher.

**Engine class registry (46 entries, ROM 0x080471DC+):** 3 `gs_c*` engine classes, 16 `franklin_gba_cStateMG*` mini-game states, `franklin_gba_cMenu`, `franklin_cScript`, `franklin_cState`, `cStateLogo`, `cStateMainMenu`, `cStatePf`, `cStateSelector`, `cStateVillage`, 18 `cEntity*` classes and `cMenu`/`cEntityMGText`. **No** `Debug`, `Test`, `Cheat`, `Secret` or `Password` class exists.

**Published codes:** none for this SKU. Web search (3rd party cheat indexes GBA 930435, 3rd party cheat index-style sources,-ROMSFUN, cheat indexes) returned only: 3rd party cheat indexes have no GBA cheat page for this game; 3rd party cheat index lists 8 *DS* Action Replay codes (`Max Apples 22147457 000000E7 / 22147458 00000003`, `All Minigames 22147411 000000FF / 22147412 000000FF`, plus backlight codes using button combos). Those are memory-edit codes for a different platform and were treated as out of scope. Literal checks: `22147457`, `22147458`, `22147411`, `22147412` each occur **0 times** as 32-bit words in this ROM. No fresh password list was found for the GBA image.

## 6b. Enumeration

Per §0.2 there is no code system, so this section bounds the negative instead of minting a code.

**Screen space (all walked, with RAM):** logo/title, Language Selection, Main Menu, Options, Credits, Mini-Games carousel (all entries `???????` on a fresh save), Story overworld, dialogue prompt, Pause. A labeled 32 KiB IWRAM snapshot was captured at each screen via the mGBA GDB stub (breakpoint at `0x08000534`, `dump binary memory ... 0x03000000 0x03008000`); files `ram_lang.bin`, `ram_title_final.bin`, `ram_menu2.bin`, `ram_story_intro2.bin`, `ram_pause.bin`, `ram_dialogue*.bin` in `/tmp/franklin2`. Key state at `0x03001F08` was read live and matched every sent keypress (e.g. 0x0200 for `a`/L). No screen beyond those listed appeared.

**Text space (decoded):** the visible text is ASCII with control codes in a bank at `0x08048FC8`, indexed by a `u16` offset table at `0x0804CD14`; the font at `0x081D540D` maps ASCII `0x20..0x7E` directly to glyphs. The `??????` locked label and all 22 names were decoded from these tables. Raw 4 MiB byte counts (case-insensitive lower/upper/`+0x20`-shift/UTF-16LE): `password` 0/0/0/0, `cheat` 0, `debug` 0, `secret` 0, `unlock` 0, `level select` 0, `sound test` 0, `enter code` 0, `game shark`/`action replay` 0/0; `code` = 1, which is `Codeurs` in the French credits (`0x5B494`) — a false positive. No password alphabet literal exists (`ABCDEFGHIJKLMNOPQRSTUVWXYZ` occurs once, at `0x1D542D`, as part of the font glyph map, not an input alphabet).

**Button space:** `0` Thumb `CMP #imm` instructions whose immediate has ≥2 of the 10 key bits set (full 4 MiB Thumb scan). `1078` candidate `u16` key-mask arrays of length ≥4 exist under a permissive filter, but all are font/tile/animation data (dominated by repeated `0x0001`); **0** of them are referenced from the code region (`<0x08100000`). Ten combos held ≥1 s on the Pause screen — L+R, L+R+Start, L+R+Select, Start+Select, A+B+Start+Select, L+R+A+B, all four directions, L+Up, R+Down, Select+A — produced no hidden screen (contact sheet `combo_contact.png`).

**Class/state space:** 46 class-registry entries enumerated; none is a debug/test screen.

**Published codes:** 0 applicable to this SKU; 4 DS memory-edit addresses verified absent as literals.

**Result:** the searched spaces contain no developer-intended code, so §0.2's "mint a novel code" deliverable is not applicable; the bounded negative above is the deliverable.

## 7. Validation evidence

- **Observed:** all screens and their transitions on mGBA `:318` (screenshots `walk_*.png`, `menu_*.png`, `pause_menu.png`, `minigames_menu.png`, `mg_contact.png`, `credits*.png`); live key-mask reads at `0x03001F08`; IWRAM dumps at each screen; save file created as 512-byte EEPROM; 10 button combos with no hidden screen.
- **Derived:** input routine `0x08000534` and key-word semantics; header/entry-word parse; class-registry and name-table layouts; text-bank base/offset-table decode; keyword/mask/array/pointer scan counts; DS code literal absence; independence from the sibling ROM by header/hash/string comparison.
- **Inferred:** collectible-threshold → save-flag → mini-game-unlock dataflow (dialogue strings plus locked-label rendering; setter/test call sites not individually traced). The `0x0000` header checksum is inferred to be a rebuild artifact, not a functional patch.

## 8. Unknowns

- Exact save-record offsets for the 14 mini-game unlock flags and the writer/tester call sites were not isolated; the 512-byte EEPROM contains a `KDGN` header and mostly zeros/0xFF on a fresh file. No attempt was made to brute-force or synthesise a save, since that would be a memory/save edit, not an in-game cheat.
- The mini-games carousel count was not pinned to a single integer from RAM; a fresh save shows `??????` at every position visitable (≥15 positions observed in the 16-frame sweep `mg_sel1..16.png`).
- DS-leftover strings (`stylus`, `game card removed`, `CREATE A GAME`/`JOIN A GAME`, L/R rowing) are present in the text banks but have no GBA UI surface; they were treated as cut/shared-asset text, not cheats.

## 9. Tooling

- Scripts (all in `/tmp/franklin2`): `phase0.py` (hash/header/logo scan), `recon.py`, `textbank.py` (text decode), `patterns.py` / key-mask & keyword scans, `ptrscan.py`, `keylinks.py`, `gdbbrk.py` (GDB breakpoint + `dump binary memory` driver), `ui.py` / `cap.py` (xdotool + scrot), `ssparse.py` / `diffstate.py` (savestate `gbAs` parser, §16.13 fallback).
- Native tools: `arm-none-eabi-objdump` (`-M force-thumb`/`force-arm`), `capstone` 5.0.7, `gdb-multiarch`, `mgba -3 -g`, `Xvfb :318`, `openbox`, `xdotool`, `scrot`, ImageMagick, Python/Pillow.
- No game assets are redistributed; only addresses, hashes, counts and the author's own tooling are published.
