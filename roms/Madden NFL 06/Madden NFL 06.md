# Madden NFL 06 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Madden NFL 06/Madden NFL 06.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `MADDEN 2006` |
| Game code | `B6ME` |
| Maker | `69` (EA) |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock; no cracktro/trainer patch) |
| Header checksum / complement | `0x0000` / `0x47` (normal EA rebuilt-header artifact) |
| MD5 | `37fe4eeab5274d244e5e6853881307ad` |
| SHA-1 | `4771f0a36d52f59f02e9da1f87cc89d9e179ba9f` |
| SHA-256 | `9a49fa18c9f8e76bfeeda3447ddccb7f57ec43e9ed1a70e318334bbf5c30571a` |
| Developer (per external metadata) | Exient Entertainment — **not** the console SKU developer (EA Tiburon/BudCat) |

**Phase 0 embedded-header scan:** Nintendo-logo scan over the entire image found exactly **one** header, at file offset `0x0`. This is a single-image retail ROM, not a multi-game cart. No appended trainer code was found. mGBA creates an 8,192-byte SRAM (`.sav`) at runtime — ordinary save memory, not a cheat device.

## 2. Executive summary

**There is no developer-intended password / code-entry / button-code / hidden-debug system in this GBA build.** The widely published "Madden Codes" (e.g. `555128`, `Z28X8K`, `B61A8M`, `2W4P9T`) belong to the **console/PC SKUs** of Madden NFL 06 (GC, Xbox, PS2, PC, PSP), which were developed by different studios. None of those literals — nor the phrase `MADDEN CODES` — exists anywhere in this 4 MiB GBA image, in ASCII, lowercase, UTF-16, +/-0x20-shifted, or tile-index-encoded form.

What the GBA build *does* have is a **token-driven card-collection unlockable system**: 161 cards (23 of which are gameplay-altering cheat cards such as `DA BOMB`, `DA BOOT`, `MR. MOBILITY`, `13 O'CLOCK`) are earned by completing Mini Camp tasks for tokens and buying packs in the Card Book. This is a progression system, not a code system, and is documented in §6/§6b.

Every reachable screen was walked in the emulator (title, Play Now flow including pause, Game Modes, all four My Madden subsections, Mini Camp, Extras, Link Play). No hidden menu appeared, and three common button combinations produced no debug screen. The text surface was searched exhaustively: 44,233 `strings` entries, plus a decode of the game's 39-glyph font index table. The input surface was searched at the code level (KEYINPUT reader and key-mask buffers). Bounded negative result — the "no code system" conclusion is a statement about this exact ROM image, not a guess.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (SDL) under Xvfb on `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, scale `-3`. Window at `154,184` 720x480; crop `720x480+154+162`.
* Keymap used: `A` = `x`, `B` = `z`, `Start` = `Return`, `L` = `a`, `R` = `s`, d-pad = arrow keys. Hold 90–150 ms with 180–250 ms gaps (longer holds double-step menus).
* Boot: two `Start` presses clear the EA splash and the legal scroll, then the main menu appears.
* Menu path to the would-be code screen: `My Madden` → `Madden Cards`. The screen has exactly **three** entries: `CHALLENGE STATUS`, `CARD BOOK`, `RESET CARDS`. There is no fourth `Madden Codes` entry.
* Published-code verification: `grep -abo` / Python byte-search for 56 published console codes in 7 encodings — all absent. No code can be entered, so none can be "tested" in-game; the codes themselves are verified absent from the image.
* Button combos pressed on the title screen: `L+R+Start`, `L+R+A+B`, and `Up Up Down Down Left Right Left Right B A`. All produced only normal menu navigation (e.g. `L+R+Start` simply invoked Play Now), no hidden screen.
* RAM evidence: mGBA savestates (`Shift+F1..F9`) are PNGs with a zlib `gbAs` chunk; `zlib.decompress` yields a 397,312-byte state. IWRAM begins at raw offset `0x19000`, EWRAM at `0x21000`. Diff of pause-menu states (cursor at index 4 vs index 8) showed IWRAM raw `0x1ef85` = RAM `0x03005f85` changing `0x0E → 0x12`, plus render-buffer diffs in EWRAM — confirming the menu state lives in RAM as expected, not in a hidden code flag.

## 4. Address map

| Item | Address / offset | Evidence |
|---|---|---|
| ROM base | `0x08000000` = file `0x0` | header |
| Nintendo logo / header | file `0x0` (only hit) | logo scan |
| Card string-pointer table | `0x38ED3C` .. `0x38EFBC` (161 x u32) | derived: 161 consecutive pointers to `*` delimited card strings; count matches `COMPLETE SET 0/161` on the Card Book screen |
| Cheat-card descriptions | `0x38F80C` .. `0x390200` | `NAME*SHORT*DESCRIPTION****` records |
| Player-card stat strings | `0x390258` .. `0x392210` | same format |
| Font glyph map | `0x3F6B0D` | 39-byte table `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 *` (tile index -> glyph) |
| Generic alphabet strings | `0x38B7BF`, `0x38B7E6`, `0x38B800` (name-entry prompts) | ASCII |
| KEYINPUT literal | file `0x16C0` -> `0x04000130` | read by Thumb `0x08001644` |
| Key-state buffers (EWRAM) | held `0x0201AA98`, pressed `0x0201AA9C`, previous `0x0201AAA0`, controller map `0x0201AAB0` | derived from input routine at `0x0800163C` (~KEYINPUT & 0x3FF, then `(old^new)&new`) |
| Game menu-state word (IWRAM) | `0x03005F85` (raw savestate `0x1EF85`) | savestate diff of pause-menu cursor |
| SRAM save | 8,192 bytes; card/token progress likely in the zeroed `0x0A10..0x0BB8` region | save dump (unverified: no tokens were earned during this run) |

## 5. Algorithm

No password validator exists to reverse. The only algorithmic content relevant to cheats is the card unlock progression:

```
complete Mini Camp task -> award tokens (scale: Rookie=1, Pro=2, All-Pro=3, All-Madden=6)
accumulate tokens -> Card Book -> BUY NEW PACK (40 tokens) -> random card from the 161-card pool
RESET CARDS -> erase card/token progress (confirmed present as a menu option)
```

Card records are pure data: a pointer table of 161 u32 values, each pointing to a `NAME*SHORT*DESCRIPTION****` string. There is no checksum, no alphabet substitution, no bit-packing, and no comparison routine against a typed input — consistent with the total absence of a code-entry UI.

## 6. Tables

**Cheat-card subset (table indices 138..160; card strings at listed ROM offsets):**

| Idx | Card | Effect (abbreviated from ROM description) |
|---:|---|---|
| 138 | 1ST AND 20 | 20 yards needed for a first down |
| 139 | 1ST AND 5 | 5 yards needed for a first down |
| 140 | EXTRA CREDIT | +1 point per interception, +? per sack |
| 141 | GENEROUS MARKING | Ball spotted randomly within a few yards |
| 142 | THE ELECTRIC SIDE | Sideline force field launches players |
| 143 | CAN'T TACKLE THIS | Ball carrier breaks tackles with ease |
| 144 | STICKY FINGERS | Passes never dropped |
| 145 | FROG LEGS | Extraordinarily high jumping |
| 146 | DA BOOT | Kickers can make 75-yard field goals |
| 147 | DA BOMB | QBs have unlimited throwing power |
| 148 | COUCH POTATO | Players tire faster |
| 149 | FUMBLITIS | More fumbles on tackle |
| 150 | OUCH! | More injuries |
| 151 | BINGO | Easier interceptions |
| 152 | LIGHTNING | All players much faster |
| 153 | TIGHT SPIRAL | QB much more accurate |
| 154 | MR. MOBILITY | QB can never be sacked |
| 155 | BIG MONEY | FG = 7 points, TD = 10 points |
| 156 | OVERDRIVE | Enhanced speed bursts |
| 157 | SWITCH SIDES | Out-of-bounds players teleport across field |
| 158 | SHADY DEAL | CPU declines all penalties |
| 159 | SLIPPERY WHEN WET | Icy field, reduced traction |
| 160 | 13 O'CLOCK | Game and play clocks hidden |

Indices 0..137 are player cards (individual NFL players with stat lines), e.g. index 0 = `AREX GROSSMAN`, index 137 = `JKEVIN WILLIAMS`.

**Menu trees observed (complete, with entry counts):**

* Main menu (6): PLAY NOW, LINK PLAY, GAME MODES, MY MADDEN, MINI CAMP, EXTRAS
* Game Modes (4): SEASON, TWO MINUTE DRILL, PRACTICE, SITUATION
* My Madden (4): ROSTERS, MADDEN CARDS, NFL RECORD BOOK, SETTINGS
* Madden Cards (3): CHALLENGE STATUS, CARD BOOK, RESET CARDS ← **no MADDEN CODES**
* NFL Record Book (4): INDIVIDUAL, TEAM, COACHING, SUPER BOWL™ HIST.
* Settings (4): GAMEPLAY, CUSTOMIZE AI, PENALTY SETTINGS, SOUND OPTIONS
* Mini Camp (4): FIELD GOAL KICK, PASSING, RUNNING, TACKLING
* Extras (2): CREDITS, MADDEN BOWL™
* Pause menu (10): RESUME GAME, CALL TIMEOUT, INSTANT REPLAY, SUBSTITUTIONS, STATS, CHALLENGE STATUS, NFL RECORDS, AUDIBLES, CONTROLS, SETTINGS
* Card Book controls: `BUY NEW PACK – 40 TKS`, page navigation over 18 pages, GOLD/SILVER/BRONZE counters, `COMPLETE SET 0/161`, `TOKENS REMAINING 0`
* In-game Play Now flow: SELECT TEAM → SELECT SIDE → COIN TOSS → PLAY SELECTION (SIDELINE/WEDGE/JUMBO) → gameplay → PAUSE

## 6b. Enumeration

**Code space size: 0 (empty set).** No password field, no alphabetic key mask sequence, no unlockable-code lookup exists in this image. There is therefore no code to mint and no bounds to prove by rejection — the required §0.2 enumeration is replaced by the bounded negative proof below.

* **Text-space enumeration.** `strings -t x -n 4` produced 44,233 entries. Case-insensitive grep for `password|cheat|debug|secret|unlock|code` returned only: `CODE` at `0x38AC68` (part of the `audset.c` audio-settings identifiers `SEAS USPR AREC USET CODE SINJ 2MIN`) and `CODE` at `0x3EA2E0` (inside `../game_psx/sfxseq.c`). Neither is a cheat. Exact searches for the strings `MADDEN CODES`, `PASSWORD`, `CHEAT`, `ENTER CODE`, `SECRET`, `DEBUG` returned **0 hits**.
* **Font/tile-indexed text decode.** The font table at `0x3F6B0D` maps tile indices 0..38 to `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 *`. Encoding `MADDEN CODES`, `PASSWORD`, `CHEAT`, `ENTER CODE`, `CODE`, `SECRET`, `DEBUG` as tile-index bytes and searching the ROM produced **0 hits** for every phrase. The UI's visible text is plain ASCII (verified by matching rendered screens against the ASCII string offsets listed in §4), so there is no second text bank hiding a code screen.
* **Published-code verification.** 56 distinct 6-character console codes collected from 3rd party cheat indexes were searched in the ROM using seven encodings (ASCII, lowercase, UTF-16LE, UTF-16BE, byte ±0x20, and font tile indices). **All 56 were absent in all encodings.** This is the expected result for a different-SKU port; it is recorded as a finding rather than silently omitted.
* **Button-space enumeration.** The input path was located statically: `0x0800163C` reads `0x04000130` (KEYINPUT), inverts and masks with `0x3FF`, and writes active-high held/pressed buffers at `0x0201AA98`/`0x0201AA9C`. Searching all 2-byte-aligned ROM positions for 4-tuples of valid key masks with >=3 distinct values produced 29 candidate runs; inspection showed them to be font/prompt tables (e.g. the `1,1,4,8` prompt-icon runs at `0x38B894`) and instruction/data noise, **not** a code sequence table. No multi-button gate with a progress index was found. Three common combos were pressed on the title screen with no hidden result (§3).
* **Unlockable-space enumeration (the system that does exist).** The card pool is fully enumerated: **161 cards** at `0x38ED3C` — 138 player cards + 23 cheat cards (§6). All 23 cheat effects were decoded from their `NAME*SHORT*DESCRIPTION` strings. This set is complete because the pointer table is contiguous, its entry count exactly equals the UI's `0/161` counter, and no further pointer run follows it (`0x38EFC0` begins an unrelated minigame-name table).

## 7. Validation evidence

* **Observed:** every screen listed in §6 (screenshots saved under `/tmp/madden06/`); the Madden Cards menu with exactly three entries; Card Book `0/161`, `0` gold/silver/bronze, `BUY NEW PACK – 40 TKS`, `TOKENS REMAINING 0`; Challenge Status token scale 1/2/3/6; pause menu with ten entries; no debug screen from any button combo.
* **Observed (RAM):** mGBA `gbAs` savestate decompresses to 397,312 bytes; IWRAM/EWRAM offsets confirmed by cursor-state diff (§3). KEYINPUT reader and key buffers located by literal scan plus Thumb LDR-literal verification.
* **Derived:** card table base/size/count from pointer-run analysis; card count cross-checked against the UI's own `0/161` display; key-mask meanings from the standard active-low GBA KEYINPUT encoding and the `~KEYINPUT & 0x3FF` instruction sequence.
* **Inferred:** the exact SRAM offset holding card/token flags (likely `0x0A10..0x0BB8`); no tokens were earned during this session, so a before/after card-flag diff was not obtained. This does not affect the code-system conclusion.
* **Not observed:** any password/code entry, any validator, any hidden debug menu — after the exhaustive searches documented in §6b.

## 8. Unknowns

* The exact SRAM byte layout for card ownership/token count was not mutated during the run (a mini-game was not completed to earn tokens). The table of 161 cards and their effects is complete; the save-field mapping is not.
* Whether the card *art* contains any hidden image is unverified — card art requires tokens to reveal in-game; the string table is fully decoded.
* mGBA's SDL build in this environment could not expose a usable GDB stub (port `2345` is held by another process and this build hardcodes it) or a responsive CLI-debugger pty; §16.13 savestate diffing was used instead and is sufficient for the RAM claims made.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, Python 3 byte/literal scanners.
* `arm-none-eabi-objdump -M force-thumb` and Capstone 5.0.7 for Thumb disassembly of the input routine (`0x0800163C`).
* mGBA 0.10.5 SDL under Xvfb `:315` + openbox; `xdotool` for input; `scrot`/ImageMagick for the (up-to-20) screenshots; savestate `gbAs` chunk parsing via Python `zlib` for RAM diffs.
* Scripts retained in `/tmp/madden06/`: `ui.py` (input/screenshot helper), `ss.py` (savestate parser), `state.py` (state diff), `dis.py` (Capstone disassembler).

**Legal note:** No ROM bytes, graphics, or copyrighted assets are reproduced in this report — only hashes, offsets, algorithms, and the game's own short card-effect descriptions quoted for identification.
