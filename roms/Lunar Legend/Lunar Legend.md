# Lunar Legend (GBA) — Reverse Engineering Report

## 1. Target identity

- **File**: `/mnt/gbacheats/roms/Lunar Legend/Lunar Legend.gba`
- **Size**: 8,388,608 bytes (8 MiB)
- **Header title**: `LUNAR LEGEND` · **Game code**: `ALNE` · **Maker**: `41` · **Version**: `0x00` · **Complement**: `0x7B` · **Header checksum**: `0x0000`
- **Entry word**: `0xEA00002E` (stock branch to `0x080000C0`)
- **MD5**: `ae5ee35f0aadf386cb6918a2d83f5a3b`
- **SHA-1**: `d7109fa4a03d50e24bd9e61446bdeb03b42732ff`
- **SHA-256**: `b38689b2315492d670724b34b6e7110340f18836517beaa775114c202f24a6e5`
- **Embedded GBA-header scan**: exactly **1** Nintendo-logo hit, at file `0x0` (the normal header). No second sub-image, no multiboot stub, no appended trainer/patch.
- **Region/revision**: English ("LUNAR LEGENDALNE41"), revision 0. `file(1)` reports `ALNE41, Rev.00`.

## 2. Executive summary

**There is no in-game / developer-intended cheat-code system in this ROM.** No password-entry screen, no code table, no cheat validator, no hidden debug menu, and no button-code sequence exists. The game is a battery-save (flash, 8192-byte `.sav`) RPG; all "cheats" published on the web are either **CodeBreaker/GameShark memory-edit codes** (explicitly out of scope), **story passwords given by NPCs** ("Green Earth" opens a gate in the plot — not a typed code), **bug exploits** (save/reload to refill HP/MP, equipment duplication), or a **save-flag unlock** (beat the game to enable Music/Sounds in Options). None is entered on a code screen.

The negative is bounded, not assumed: every reachable screen was walked to a save state and decoded through the game's tile-indexed text banks and RAM tilemaps; both text encodings were dumped and searched exhaustively; published lists were retrieved and their literals checked; common button-code sequences were pressed with before/after RAM diffs. The ROM's entire user-facing text surface contains only 14 distinct UI labels — none of them a password/cheat/debug entry point.

## 3. How to reproduce

- **Emulator**: mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, 3× scale. Keymap (SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Screenshots cropped to `720x480+153+164`.
- **Menu path**:
  - Boot → press Start through the "ENGLISH TRANSLATION" splash → `PRESS START` → Start → title menu (`NEW GAME` / `LOAD GAME` / `OPTIONS`).
  - `OPTIONS` → 4 rows: `???`, `???`, `CARDS`, `GALLERY` (the two `???` are `MUSIC` and `SOUNDS`, locked until game completion).
  - `LOAD GAME` → three slots, all `NO DATA` on a fresh cart.
  - `NEW GAME` → story scenes → field; Start opens the in-game (pause) menu: icon carousel with `Save/Load Game`, `Status Display`, `Nall's Skills`, `Battle Settings`, `Back`.
- **RAM proof method**: mGBA savestates (`.ss1`) are PNG with a zlib `gbAs` chunk; decompress to a 397,312-byte state. Per §16.13 the IWRAM image begins at state offset `0x19000` (so `0x03000000` maps to state `+0x19000`), EWRAM at `+0x21000`. Tilemap rows at EWRAM `0x02005840/80`, `0x02005900/40/c0` were decoded with the font mapping below.
- **Codes tested**: none applicable (no code surface). Button codes tested on the title screen: `L+R`, `Start+Select`, `A+B+Start+Select`, Konami `Up Up Down Down Left Right Left Right B A`, `L+R+Start`.
- **Sources checked**: GameFAQs cheats/walkthrough, GameFAQs Genome_X guide, GamingDome, VGChartz, LunarNET Secrets Guide, TCRF (fetch 403; CDX snapshot query returned no result).

## 4. Address map

| Item | File offset | ROM address | Evidence |
|---|---:|---:|---|
| Header / entry | `0x000` | `0x08000000` | observed (stock `0xEA00002E`) |
| Title text bank (`PRESS START`, `NEW GAME`, `LOAD GAME`, `OPTIONS`) | `0x09A7D2`–`0x09A7FA` | `0x0809A7D2`– | derived (font decode) |
| Main UI/script string bank (`OPTIONS`, `GALLERY`, `SAVE`, `LOAD`, `TITLE`, `FORMATION`, `TACTICS`, `MUSIC`, `SOUNDS`, `CARDS`) | `0x09A4C2`–`0x09A670` | `0x0809A4C2`– | derived (font decode) |
| String-bank pointer table xref (title labels) | `0x121C4`, `0x123B0`, `0x1256C`, `0x13288`, `0x13308`, `0x1345C` | `0x080121C4`… | derived (u32 pointer scan) |
| Text renderer (A=0xAC bank, terminator `0xFF`) | `0x12180`–`0x12214` | `0x08012180`– | derived (Thumb disassembly) |
| RAM tilemap rows (title/options/load/menu) | — | `0x02005840`, `0x02005880`, `0x02005900`, `0x02005940`, `0x020059C0` | observed (savestate decode) |
| RAM screen/state words | — | `0x03000048`, `0x0300004C`, `0x03000050`, `0x03000054` | observed (differ across screens) |
| Save data (flash) | — | `0x0E000000` (8192-byte `.sav`) | observed |

**Font mapping (derived from live tilemaps):** GBA 4bpp tiles; tile index = `0x156 + 2*letter_position`, so `A`=`0x158`, `B`=`0x15A`, … `Z`=`0x190`; the odd variants `0x159`…`0x191` are the palette-shifted highlight form; `0x001` = blank; `0x19E`/`0x19F` = `?`. This was validated by decoding visible `OPTIONS` and `LUNAR` rows exactly.

**Text encoding (two banks, both derived):**
- Bank A (title): `space=0x00`, `A..Z = 0x0B..0x24`, terminator `0xFF` — e.g. `NEW GAME` = `18 0F 21 00 11 0B 17 0F FF` at `0x09A7E1`.
- Bank B (main UI/script): `space=0x00`, `A..Z = 0xAC..0xC5`, terminator `0xFF`, preceded by a 2-byte entry id — e.g. `OPTIONS` = `01 01 0B BA BB BF B4 BA B9 BE FF FF` at `0x09A4D0`.

## 5. Algorithm

Not applicable — there is no validator, checksum, generator, or code table. The only algorithmic content recovered is the text-decoding rule in §4 (`char_index = (tile_index - 0x156) / 2`; `code = base + letter_position` with `base` 11 or 172 depending on bank), sufficient to enumerate every string the game can display.

## 6. Tables

Complete list of distinct user-facing UI strings recovered from both banks (this is the whole bounded search space; values are letter-position codes, not codes the player enters):

| Screen | Strings (decoded) |
|---|---|
| Title | `PRESS START`, `NEW GAME`, `LOAD GAME`, `OPTIONS` |
| Options | `???` ×2, `CARDS`, `GALLERY` (underlying locked labels: `MUSIC`, `SOUNDS`, `CARDS`, `GALLERY`) |
| Save/Load | `SAVE`, `LOAD`, `TITLE`, `NO DATA`, `Lv 1 Burg` (slot contents) |
| In-game (pause) menu | `Save/Load Game`, `Status Display`, `Nall's Skills`, `Battle Settings`, `Back`, `Who?`, `System` |
| Script bank | `FORMATION`, `TACTICS`, `YES`, `NO`, `LUNAR` |

**Save flag**: the two locked Options rows are gated by game completion (published sources: "Beat the Game Once to Unlock Sound and Music Test"). This is a save-bit unlock, not a code — per §16.18 it is not reported as a cheat system.

**Published codes (web) verified against ROM**: none present. All GameFAQs/VGChartz/GamingDome listings are CodeBreaker RAM patches (`83004AC2 03E7` etc.), bug exploits, or save-flag unlocks. The story word "GREEN EARTH" (Phacia's Ruid password, a plot item) was searched literally and in both text encodings — **0 hits**: it is dialogue, not an input.

## 6b. Enumeration

Space definition: **the code space is empty**. Concretely:

1. **Text space** — `strings -t x -n 4`: 92,228 ASCII strings, **0** containing `password/cheat/code/debug/secret/unlock` (case-insensitive). Because UI text is tile-indexed, both encoded banks were decoded and fully enumerated: bank A (`0x0B`+letter) yielded 1,643 runs; bank B (`0xAC`+letter) yielded 23 runs. Union of distinct UI labels = 14 (table in §6). None is a code-entry prompt.
2. **Literal code space** — `grep -abo` for `PASSWORD`, `GREEN EARTH`, `SOUND TEST`, `MUSIC TEST`, `DEBUG`, `CHEAT`, `SECRET` in ASCII, uppercase-lowercase shifted, UTF-16LE, and both tile encodings: **0 hits** for all.
3. **Button-code space** — u16 key-mask sequences for the Konami code, `L+R`, `L+R+Start`, `Start+Select`, `A+B+Start+Select` were searched as active-high, active-low, little- and big-endian halfwords. No plausible table (only incidental `L+R` byte pairs in unrelated data at `0x089C71` etc., inside script tables). Five common combos were pressed on the title screen with before/after RAM diffs; every resulting change was an ordinary screen transition (title fade / splash), and no hidden screen appeared after a 2.5 s settle.
4. **Menu space** — every reachable screen was entered and its tilemap decoded: splash, title menu, Options (4 rows, two locked), Load (3 slots), New Game scenes, field, dialogue, in-game/pause menu (icon pages enumerated: `Save/Load`, `Status`, `Nall's Skills`, `Battle Settings`, `Back`). No entry accepts a code.
5. **Novel code / bounds-by-rejection** — not applicable: with no validator and no accepted set, there is nothing to mint and nothing to reject. Per §0.2's negative-result clause, §7 records the enumerated search spaces and counts that prove absence. This is a "no system" result (§16.3 case 1), not "dead code", "cut feature", or "gated feature".

## 7. Validation evidence

- **Observed**: title/options/load/pause/field/dialogue screens screenshotted; RAM tilemaps at `0x02005840…` decoded to exact English words; save states written and reloaded reproducibly; `.sav` created with slot data (`100RANUL…`). Button-combo attempts produced only normal transitions in RAM diffs.
- **Derived**: font/tile mapping and both text encoding schemes (validated by exact decode of visible labels); string-bank pointer xrefs from u32 literal scan; Thumb disassembly of the A=0xAC text renderer at `0x08012180`.
- **Inferred**: the two `???` rows are `MUSIC`/`SOUNDS` (matching published unlock descriptions) and gated by a completion save flag; the battle and menu screens were located via the decoded UI bank but not reached interactively in the time budget (see Unknowns). These do not affect the no-code conclusion.
- **Prompt-injection handling**: TCRF returned HTTP 403 and the archive CDX query returned no snapshot; no fetched page contained injected instructions. Web content was treated strictly as data.

## 8. Unknowns

- A full battle screen and the battle-specific submenu (`FORMATION`/`TACTICS` labels exist in the decoded bank) were not reached by live play from a fresh save; reaching them requires substantial story progress. Their UI labels are present in the enumerated string bank and contain no code-entry or debug entries, so the no-code conclusion holds, but the screens themselves were not screenshotted.
- The exact save-bit offset for the Music/Sounds unlock was not isolated; only the externally-published unlock condition (game completion) is recorded.
- The `GALLERY` and `CARDS` Options rows did not open on a fresh save (story-gated); their contents are collectible card/picture lists, not code entry.

## 9. Tooling

`strings`, `grep -abo`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum`, Python 3 (`zlib`, `struct`, `re`, `Pillow`), `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7 (available, not required), mGBA 0.10.5 under Xvfb `:319` + openbox, `xdotool`, `scrot`, ImageMagick. Helper scripts in `/tmp/opencode/lunarlegend/`: `h.py` (input/screenshot), `ramstate.py` (savestate→RAM), `evidence.py` (tilemap decode), `renderfont.py`, `ssram.py`.

**Legal note**: only hashes, addresses, algorithms, and original tools are published; no ROM bytes or copyrighted assets are redistributed.
