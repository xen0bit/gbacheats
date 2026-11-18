# Game & Watch Gallery 4 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Game & Watch Gallery 4.gba` (4,194,304 bytes = 0x400000) |
| Header title | `G&W GALLERY4` |
| Game code | `AQWE` (USA), maker `01` (Nintendo), version `0x00` |
| Entry word | `0xEA00002E` — stock `b` into crt0; **no scene cracktro / appended trainer** |
| Header checksum | stored `0x0000`, complement byte `0x9A` (raw values recorded; not a reliable edit signal — §16.1) |
| MD5 | `89bd27cd7228736d9c00461abd20c208` |
| SHA-1 | `56be8e044aba698f1d573053b5af8e0c0bfcc060` |
| SHA-256 | `8166a4d8a307999d8d37843a9b7ebc9cfbc18bd2a4376b2832daa08104ccb6ee` |
| Engine signature | `GBGforAGB 0.9.2` (ROM 0x080CCA28 / 0x080CCACC); save header `GBGforAGB 0.9.33`; `Compile Date: Jul 31 2002`, `Compile Time: 20:25:28` (0x080CAB7C) |

**Embedded GBA headers (§5.4b).** Scanning the full 156-byte Nintendo logo found 5 hits. Besides the real header at file 0x0, four identical headers with blank title, code `AGBJ`, maker `01`, entry `0xEA00002E` sit at file offsets `0x1C7D80`, `0x1E4A44`, `0x2044F4`, `0x224A00`. These are self-contained multiboot images (the classic Game & Watch titles bundled in the cartridge), each linked for its own base. They are part of the retail image, not trainers.

## 2. Executive summary

**No developer-intended cheat-code system exists in this ROM.** There is no password entry screen, no button-code sequence table, no code-bearing save field, and no reachable hidden/debug menu. The game's only unlockable content is **star-based**: the in-game text states "THIS MAY START OUT EMPTY, BUT IT WILL FILL UP WITH FUN STUFF AS YOU EARN STARS IN GAMES! GET AS MANY STARS AS YOU CAN!" Gallery unlocks are bit/byte flags in the SRAM save record at `0x0E000328..0x0E00042F` — a save-bit unlock, not a code (§16.18). No published GBA password/cheat list could be located (web research was blocked in this environment — see §8), and the ROM contains no code table against which such a list could be verified.

The negative is **bounded**: every reachable screen was walked with screenshot evidence (§7), the entire plaintext and LZ77-decompressed text space was searched (79 strings + 48 LZ77 blocks), the whole 16-bit button-mask space was scanned for code tables, the font/tile-indexed text system was located and decoded far enough to prove it is an ASCII↔tile conversion scheme (§5), and six classic debug button combinations were pressed on two different screens with no hidden screen resulting.

## 3. How to reproduce

* Emulator: mGBA (SDL) on `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`, `-3` scaling; Xvfb `:319` + openbox. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold ~100–150 ms (shorter taps double-step menus — §16.2).
* Boot path: title ("PRESS A BUTTON OR START") → START → AUTOSAVE notice → title menu: **PLAY THE GAME** / **VIEW THE GALLERY** (Left/Right to choose, A to confirm).
* PLAY THE GAME → GAME SELECT: circular list (observed: DONKEYKONGJR, DONKEYKONG3, FIRE, BOXING, RAINSHOWER, MARIO'S CEMENT FACTORY; VRAM also holds OCTOPUS, FIRE ATTACK, CHEF, MARIO BROS. logo tiles for the classic variants). Each entry has a MODERN / CLASSIC toggle with a character preview. A → rules screen(s) → gameplay. START → pause: CONTINUE / EXIT (Left/Right), plus HI SCORE display. No other pause entries exist (Down does not move the cursor; Right moves CONTINUE→EXIT and back).
* VIEW THE GALLERY → GALLERY CORNER notice → Gallery Corner room (star meter, 6 slots) → MESSAGE BOARD (messages incl. `AUTOSAVE`, HINTS AND TECHNIQUES board).
* Savestate slots used: F1 = title, F2 = game select. States are `.ss1/.ss2` PNGs with a zlib `gbAs` chunk; decompressed length 397,312 bytes; VRAM at state +0x1000, palette +0x800, OAM +0xC00, IWRAM +0x19000, EWRAM +0x21000 (§16.13).
* No code was tested because no code-entry surface exists anywhere in the walk.

## 4. Address map

| Item | Address (file / ROM / RAM) | Evidence |
|---|---|---|
| ROM header | file `0x0` / `0x08000000` | Observed |
| Engine strings | file `0xCA70E`, `0xCAB7C`, `0xCCA28`, `0xCCA94`, `0xCCACC`, `0x80D05A4`, `0x80D05DC` | Observed (Ghidra + `strings`) |
| Multiboot headers | file `0x1C7D80`, `0x1E4A44`, `0x2044F4`, `0x224A00` | Observed |
| KEYINPUT reader / key-state setter | `0x08014EC8` (reads `0x04000130`, XOR `0x03FF`, stores pressed `0x03002518` / held `0x0300251C`) | Derived (disassembly) |
| Other key-state readers | `0x080173C4`, `0x08017528` (same held/pressed derivation), plus copies at `0x0800889E/A4`, `0x0800B7BA/C0`, `0x0800FC30/36`, `0x08013418/1E` | Derived |
| Font/character tables | ROM `0x080D3E80` (92-byte tile→char table) and `0x080D3F20` (256-byte char→tile table, pointed to by literal at `0x080C579C`) | Derived |
| Font-width/interpolation routine | `0x080C5720`–`0x080C579A` (indexes the 0x080D3F20 table; clamps to 130; 16-entry s16 fixed-point table at `0x080D3FA4`; returns value + 0x800) | Derived |
| Save magic | SRAM `0x0E000000`: `47 42 47 66 6F 72 41 47 42 20 30 2E 39 2E 33 33` = `GBGforAGB 0.9.33` | Observed |
| Save record (stars/unlocks) | SRAM `0x0E000328`–`0x0E00042F` (264 bytes; nonzero flags at +0x28, +0x4C, +0x5D/5F/60, +0x84, +0x8A..8D, +0xEA/EB) | Observed |
| Key state RAM | IWRAM `0x03002518` (pressed), `0x0300251C` (held) | Derived |
| Screen-state RAM (title vs select) | IWRAM around `0x03001140`–`0x03001198`; EWRAM around `0x02000230`–`0x0200029C` — 4,087 / 54,099 bytes differ between the two savestates | Observed (savestate diff) |

## 5. Algorithm / text encoding

There is no validator to reverse. The text system is worth recording because it defeated `strings`:

1. On-screen text (menus, messages, rules) is drawn from 8×8 4bpp tiles in VRAM; it is **not** stored as obvious ASCII, which is why `strings -t x -n 4` returned only the header title and 42,615 lines of code-byte noise (§11).
2. VRAM was rendered from the savestate with its own palette (state +0x800): the tile bank contains the game-logo art (FIRE, BOXING, RAINSHOWER, MARIO'S CEMENT FACTORY, DONKEYKONGJR, DONKEYKONG3, etc.), the MODERN/CLASSIC panel glyphs, and the character font (verified by rendering tiles 352–480 with palette — the words "MODERN" and "CLASSIC" resolve to individual glyph tiles).
3. Two conversion tables were located: `0x080D3E80` (92 bytes, values `0x78,0x79,0x7A,0x7B,0x60..0x6B,0x50..0x5B,0x40..0x4B,0x30..0x3B,0x20..0x2B,0x10..0x1B,0x00..0x0B`) and `0x080D3F20` (256 bytes, a char→tile permutation with a `+4` gap every 12 entries). `0x080C579C` holds a pointer to the latter; `0x080C5720` consumes it. Attempts to encode known words ("PRESS", "MODERN", "DEBUG", "SECRET", "PASSWORD", "AUTOSAVE") through either table and find them literally in ROM produced zero hits, so the message strings are stored in a further-compressed/custom form; the exact message-bank encoding is an **unknown** (§8), but this does not affect the cheat conclusion: the tiles are a font, not an alphabet-of-code-entry, and no entry widget exists on any screen.

## 6. Tables

* **Key masks** (derived from `0x08014EC8`): active-high `A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`; raw active-low is the XOR with `0x03FF`. Held/pressed words live at `0x0300251C` / `0x03002518`.
* **Save flags**: SRAM record `0x0E000328..0x0E00042F`; the values are small integers/flags (stars and gallery unlock bits). No field in this record is ever fed by a code-entry comparison — it is written by the gameplay/results path (`cSaveLoad::WritePauseData` diagnostic string at `0x080CCA94`).
* **Codes**: none. No published or generated code exists to tabulate.

## 6b. Enumeration

* **Space size**: not applicable — there is no code alphabet, no input buffer, no validator and no code table. To bound the *button-code* space instead, every `u16` aligned value in the 4 MiB ROM was tested against the active-high and active-low key-mask sets and all runs of ≥4 consecutive mask-like values were extracted (6,773 active-high runs, 713 active-low runs). Every early "candidate" (e.g. `0x08002238`, `0x08002386`) was inspected and proved to be a misaligned fragment of a 32-bit RAM pointer such as `0x03000028` / `0x03000030`, not a cheat sequence. **No button-code table was found.**
* **Novel code**: cannot be minted, because no encoding exists. The §0.2 deliverable "generate a code absent from every published list" is therefore replaced with the §0.2(bound) deliverable: a *proven negative* — every screen enumerated, text/code spaces searched with counts, and published-code verification attempted.
* **Bounds proven by rejection**: no code-input surface exists to accept or reject a value, so no in-game rejection test is possible. The nearest proof is the button-combo test: six classic debug combinations (`L+R+Select+Start`, `L+R+A+B`, `Start+Select+A+B`, `L+R+Start`, `L+R+Select`, `Up,Up,Down,Down`) were pressed simultaneously on two different screens; none produced a hidden screen — the input was consumed as ordinary gameplay (e.g. `L+R+Select+Start` on GAME SELECT launched the highlighted game and showed normal gameplay, not a debug menu).

## 7. Validation evidence

**Observed (screenshots / RAM):**
* Title, AUTOSAVE notice, title menu, GAME SELECT with MODERN/CLASSIC panel, Boxing rules + Modern Boxing rules, Boxing gameplay, pause menu (CONTINUE/EXIT/HI SCORE), Gallery Corner notice and room, MESSAGE BOARD (AUTOSAVE message). Screenshots stored in `/tmp/opencode/gw4/` (e.g. `boot_c.png`, `s01b_after_start_c.png`, `s04b_c.png`, `pause2_c.png`, `gal4_c.png`, `msg3_c.png`).
* SRAM save record contents (32,768-byte `.sav`): magic at 0x0, data only at 0x328–0x42F, rest erased (`0xFF`).
* Savestate RAM diff: title vs game-select differ by 4,087 IWRAM bytes and 54,099 EWRAM bytes (screen state genuinely changes).
* VRAM tile render showing font/game-logo tiles; four embedded `AGBJ` headers.

**Derived (disassembly / tools):**
* KEYINPUT reader at `0x08014EC8`; key words at `0x03002518`/`0x0300251C`.
* 79 Ghidra strings and 48 decompressed LZ77 blocks, none containing `password`, `cheat`, `secret`, `debug`, `unlock`, `enter code`, or an alphabet `ABCDEFGHIJKLMNOPQRSTUVWXYZ`.
* Font tables at `0x080D3E80`/`0x080D3F20` and width routine at `0x080C5720`.
* No pointer to a cheat/code table; no comparator against a user-entered buffer.

**Inferred:** The gallery/star flags are the game's only "unlock" mechanism and are advanced by earning stars in gameplay; the exact star thresholds per gallery item were not exhaustively played out (would require completing games).

## 8. Unknowns

* **Web verification of published codes: not completed.** `websearch` returned no results for all queries; direct fetches were blocked (TCRF 403, GameFAQs via Wayback 404/CDX 503, Google/Bing/DDG unusable from this environment). Per §16.8 this is recorded rather than silently omitted. Because the ROM has no code-entry surface or code table, the absence of a verified published list does not change the conclusion.
* Exact custom encoding of the gallery message-bank strings (font tiles and conversion tables were located, but message bytes were not reversed to ASCII). This is a text-format unknown, not a cheat-system gap.
* The precise star threshold that unlocks each Gallery Corner item was not played through; the flags themselves were located in SRAM.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep` (Phase 0/1).
* `arm-none-eabi-objdump -M force-thumb` and Capstone 5.0.7 (literal/BL/key-mask scans).
* Ghidra 12.1.4 via REA MCP (`open_binary` raw ARM @ `0x08000000`, `binary_overview`, `list_strings`, `list_procedures`, `xrefs`); 795 procedures, 79 strings; session closed with `close_binary`.
* mGBA SDL + Xvfb `:319` + openbox + xdotool + scrot + ImageMagick; mGBA `-g` GDB stub and `-d` pty debugger were trialed; mGBA savestate (`gbAs` zlib chunk) decompression for VRAM/RAM evidence.
* Custom scripts in `/tmp/opencode/gw4/`: `gw.py`, `walk_list.py`, `scan_input.py`, `scan_masks.py`, `lzscan.py`, `render_full.py`, `render_map.py`, `diffstate.py`, `mgba_pty.py`.

## 10. Legal note

No ROM bytes, graphics, music, or game text are redistributed here — only hashes, addresses, and the analyst's own observations/tools.
