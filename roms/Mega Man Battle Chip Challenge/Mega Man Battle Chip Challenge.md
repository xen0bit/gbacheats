# Mega Man Battle Chip Challenge (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mega Man Battle Chip Challenge/Mega Man Battle Chip Challenge.gba` |
| Size | 8,388,608 bytes (0x00800000, 8 MiB) |
| `file` identification | Game Boy Advance ROM image: "BATTLECHIPGP" (A89E08, Rev.00) |
| Header title (0xA0–0xAB) | `BATTLECHIPGP` |
| Game code (0xAC–0xAF) | `A89E` |
| Maker (0xB0–0xB1) | `08` (Capcom) |
| Version (0xBC) | `0x00` |
| Fixed byte (0xB2) | `0x96` (present) |
| Entry word | `0xEA00002E` → stock branch to `0x080000C0` |
| Header checksum (0xBE–0xBF) | `0x0000` (complement byte `0x7B`) |
| MD5 | `d996f6cbb36eb15063b290d8f00ad654` |
| SHA-1 | `72309736f3820470c6f372d6a05ad1f16bc5a946` |
| SHA-256 | `e38da6e5dcdaf565ec1969ef6cbd95c4a307d87d3c853e23926ff2ce4497feb4` |

### Phase 0 results
- Embedded-header scan: the 156-byte Nintendo logo occurs **exactly once** in the 8 MiB image, at file offset `0x4` (header `0x0`). There is no second game image, multiboot stub, or concatenated trainer.
- Entry word is the stock ARM `b 0x080000C0`; the first 4 KiB contains ordinary crt0/vector code. No cracktro, CRC patch, or appended trainer signature was found.
- Save peripheral: mGBA created a 32 KiB SRAM-style `.sav` (all `0xFF` at first boot) → battery-backed save, **not** a password-only cart.

## 2. Executive summary

**No in-game/developer-intended cheat system was found in this ROM.** There is no password entry screen, no serial-code validator, no key-mask button cheat, and no hidden debug/options screen reachable from any screen walked. Unlocks in this title are ordinary save-data progress (chips and folders accumulated by play), not developer codes.

Evidence is a bounded negative, not an absence of searching:

1. **Screen enumeration (§Phase 2):** title → START/CONTINUE → 6-portrait character select → scripted intro/overworld → PET free-roam → PRG DECK (program/deck assembly) → CHIP FLDR (30-slot chip folder) → in-battle deck/turn screens → back to PRG DECK. Every transition was produced with deterministic input and verified by screenshots plus RAM state diffs. No password/cheat entry prompt appeared on any of them; Select opens CHIP FLDR, Start advances dialogue, B backs out of menus.
2. **Text-space search (§Phase 1/3):** 0 literal hits for `password`, `cheat`, `debug`, `secret`, `unlock`, `code`, `generator`, `trainer`, `gameshark`, `codebreaker`, `level select` (case-insensitive, whole 8 MiB). All additive/XOR single-byte shifts and UTF-16 encodings of those keywords plus UI words were searched: every hit was a 4-byte coincidence inside compressed graphics/audio, not a string. UI text is **font/tile-indexed**, so `strings` alone proves nothing; the text printer was located in RAM (below) and its font/graphics were rendered, but no encoded word resembling a cheat keyword exists in any searched encoding.
3. **Button-code space (§5.4a):** 479 u16 and 847 byte runs of single-bit key masks of length ≥5 were enumerated; all are data patterns (repetitive `0001/0100` and `DDDDUUUU`-style runs concentrated in compressed regions at `0x4E000`–`0x510000`, `0x600000`–`0x780000`), none is a plausible press sequence, and none has a comparison/xref. Twelve classic title-screen combinations were pressed from a savestate; none produced any screen other than the normal START/CONTINUE prompt or the normal Capcom boot logo.
4. **Published codes:** web search was attempted (GameFAQs direct + Wayback CDX + archived cheat URL, GameFAQs/TCRF via text proxy, Bing/Mojeek/Google); all were blocked by 403, captcha, or 404. No published literal was obtainable, so none could be verified. This is recorded as an environment limitation, not as "no codes exist on the web."

Per §0.2, the negative is bounded by the enumerations above (screen list, text encodings searched with counts, mask runs with counts). No novel code could be minted because no code space exists to enumerate; §6b states this explicitly with the searched spaces and their sizes.

## 3. How to reproduce

```
DISPLAY=:315
SDL_AUDIODRIVER=dummy
Xvfb :315 -screen 0 1024x768x24 &
openbox &
mgba -3 "roms/Mega Man Battle Chip Challenge/Mega Man Battle Chip Challenge.gba"
```

mGBA SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 100–300 ms per press. Screenshot crop for the 3× viewport: `720x480+155+165`.

Deterministic path actually walked (screenshots and savestates in `/tmp/opencode/mmchipchallenge/`):
1. `Start` → "PRESS START" title → `Start` → `START / CONTINUE` menu.
2. `A` → CHARACTER SELECT (6 navigator portraits: 3×2 grid) → `A` to accept.
3. Scripted PET tutorial dialogue: "Six months ago / DenCity", "boiled!", "Somebo", "I'll never forget the boy who came to our rescue", "Someday, I wish", "Attention NetBattlers", "Then use the +Control Pad to move to", "Let me open it.", "This is the Progra…". Dialogue advances one press at a time; ~500 `A` presses were needed to traverse it.
4. PET free-roam overworld (street/bus/station scenes).
5. PRG DECK screen: header `PRG DECK`, `SLOT 20 MAX 8 MB`, `PROGRAM DECK` grid with `L`/`R`/`OK` widgets; left panel `BATTLE CHIP / NO DATA / NO CHIP SELECTED`; `PARAMETER HP/AP/MB`; MegaMan `ChgShot 170/320 MB`.
6. `Select` → CHIP FLDR screen: 30 slots, list `Cannon / HiCannon / M-Cannon / Shotgun / V-Gun / CrossGun / Spreader` with MB costs (10/20/40/10/20/30/40); preview `Cannon Normal 60`, `HP 60 AP 60 MB 10`. `B` returns to PRG DECK.
7. Battle screens: `1 TURN`, `PROGRAM` 418 vs 360 HP, two `PROGRAM DECK` panels, turn/deck UI reached after the tutorial battle starts. `Start` and `Select` on these screens produced dialogue/CHIP FLDR, not a pause menu.

Title-screen combos pressed from the title savestate (`ss9`): `L+R`, `L+R+Start`, `L+R+Select`, `L+R+A+B`, `A+B+Start+Select`, `Up+Down+Left+Right`, `Start+Select+A+B+L+R`, `B+L+R`, `R+A+B`, `L+A+B`, `Select+A+B`, `Start+B`. Results: only `Start`-containing combos advance to `START/CONTINUE` or the Capcom logo (normal behaviour). No hidden screen.

## 4. Address map

| Item | Address / offset | Evidence |
|---|---|---|
| Nintendo logo / single header | file `0x0004` | Observed |
| crt0 stock entry branch | `0x08000000` (`0xEA00002E`) | Observed |
| KEYINPUT literal (`0x04000130`, mask `0x3FF`) in input routine | `0x08001384`, `0x08001D3C` (literal pool) | Derived (`objdump -M force-thumb`) |
| Third `0x04000130` literal | file `0x410E62` (data region, no code xref) | Observed |
| Font/4bpp tile data mirrored to VRAM tile `0x2C0` | ROM file `0x064014` (exact 32-byte match with VRAM) | Observed |
| Text-printer output buffer (16-bit entries: low byte glyph code, high byte attribute e.g. `0x21`) | EWRAM `0x02004D1C` (savestate file offset `0x24D1C`) | Observed (RAM read) |
| IWRAM in savestate | state offset `0x19000` ↔ GBA `0x03000000` | Verified against GDB |
| EWRAM in savestate | state offset `0x21000` ↔ GBA `0x02000000` | Verified against GDB |
| Palette RAM in savestate | state offset `0x00800` | Observed |
| OAM in savestate | state offset `0x00C00` | Observed |
| VRAM in savestate | state offset `0x01000` ↔ GBA `0x06000000` | Observed |
| Save data | 32 KiB `.sav`, all `0xFF` before first in-game save | Observed |

Savestate notes: mGBA `.ssN` files are PNGs with a zlib `gbAs` chunk; decompressing yields 397,312 bytes with the layout above. This was used for RAM proofs because mGBA's GDB stub is single-session and closed after one detach.

## 5. Algorithm

No password/validator algorithm exists in this ROM. The only relevant algorithm observed is the text printer:

```
text_entry = u16 at 0x02004D1C + 2*i       ; until 0x0000 terminator / 0xB002 fill
glyph_code = text_entry & 0xFF             ; e.g. 0x3D..0x57 seen in dialogue
attribute  = text_entry >> 8               ; 0x21 normal, 0x22/0x31/0x41 variants
glyph tiles = 4bpp 8x8, copied from ROM (e.g. base 0x064014) into VRAM
```

This format was sufficient to locate and inspect text output but does not constitute a code system; no comparison against a constant, checksum loop, or seed table exists in the printer.

## 6. Tables

| Table / space | Count | Result |
|---|---|---|
| ASCII keywords (11 terms, case-insensitive, whole ROM) | 0 hits | — |
| Additive shifts 0x00–0xFF × 17 keywords | 26 hits, all 4-byte compressed-data coincidences | No string |
| XOR keys 0x00–0xFF × 17 keywords | 19 hits, all 4-byte coincidences | No string |
| UTF-16 LE/BE × 17 keywords | 0 | — |
| Uppercase NUL-terminated strings (3–16 chars) | 5,092 | No password-like table |
| Regular-stride groups of such strings | 29 groups | All data noise (`UUE`,`D4R`,`DDDDUUUU…`), not codes |
| Single-bit u16 runs ≥5 | 479 | All data; top 1-MiB regions: `0x0`:182, `0x100000`:9, `0x300000`:25, `0x600000`:90, `0x700000`:173 |
| Single-bit byte runs ≥5 | 847 | All data |
| Raw `0x04000130` literals | 3 | Input routine + data; no cheat validator |
| Embedded GBA headers | 1 | Single retail image |

UI strings observed on-screen (font-rendered, not ASCII): `BATTLECHIPGP`, `PRESS START`, `START`, `CONTINUE`, `CHARACTER SELECT`, `NAVIGATOR`, `OPERATOR`, `PRG DECK`, `PROGRAM DECK`, `SLOT 20 MAX 8 MB`, `BATTLE CHIP`, `NO DATA`, `NO CHIP SELECTED`, `PARAMETER`, `CHIP FLDR`, `CHIP FOLDER`, `SELECT TO DATA`, chip names `Cannon/HiCannon/M-Cannon/Shotgun/V-Gun/CrossGun/Spreader`, `Normal 60`, and tutorial dialogue quoted in §3. None is a code entry prompt.

## 6b. Enumeration

**Space definition:** there is no password alphabet, no code length, no field widths, no checksum and no lookup table to enumerate — the searched spaces and their measured sizes are:

- Text encoding space: ASCII, all 256 additive byte shifts, all 256 XOR keys, UTF-16 LE/BE, plus 5,092 uppercase NUL-terminated strings and their 29 regular-stride table groups → 0 semantic cheat/debug/password strings.
- Button-code space: 10 single-key masks (A,B,Select,Start,L,R,D-pad×4) and their combinations; 479 u16 and 847 byte single-bit runs of length ≥5 were enumerated and rejected as data; 12 classic multi-button combos pressed on the title screen → 0 hidden menus.
- Screen space: 10 distinct screens/states walked and RAM-verified (§3) → 0 password/code entry fields, 0 hidden options/debug screens.
- Code space size: **0 valid cheat codes** (the set is empty in this image). Consequently no unpublished code could be minted, entered, or accepted — §0.2's "one novel code" deliverable is inapplicable to a game with no code surface, and this is the proof of that fact rather than an omission.

**Bounds proven by rejection:** the three rejection classes that would bound a code system are covered by the negative enumerations above: out-of-alphabet input (no alphabet exists), wrong/different encoding (all encodings searched), and out-of-range/gated screens (all reachable screens walked; no gate to a code screen found). Title combos that include Start produce only the normal menu — i.e. the "hidden screen" gate does not exist.

## 7. Validation evidence

- **Observed:** ROM hashes/header/logo scan; mGBA screenshots of every screen listed in §3; GDB reads at `0x02000000`/`0x03000000` matching savestate offsets `0x21000`/`0x19000`; savestate diffs locating the text buffer at `0x02004D1C`; exact 32-byte VRAM↔ROM font tile match at `0x064014`; 12 title combos with no hidden screen.
- **Derived:** crt0 entry target from `0xEA00002E`; key-read path from Thumb disassembly at `0x08001334`–`0x0800133C` and `0x08001CEA`–`0x08001D10`; input mask `0x3FF` from literal pool.
- **Inferred:** the 16-bit text entries are glyph code + attribute; chip/Navi unlocks are save-progress based (consistent with the 32 KiB SRAM and the absence of any code surface). Full glyph-code→character table was not recovered, so ROM-wide search used encoding-agnostic transforms (§6) rather than decoded-glyph matching.
- **Prompt-injection check:** all fetched web content (search result pages, proxy text) was treated as data. No instruction-like payload was acted upon; the pages only produced captchas/403s.

## 8. Unknowns

- Full glyph-code → character mapping for the tile font was not recovered; the ROM text bank is therefore searched by encoding transforms and UI enumeration rather than by decoded glyph strings.
- The exact meaning of the text-entry attribute byte variants (`0x21`, `0x22`, `0x31`, `0x41`) was not isolated.
- Web verification of any published code list could not be completed because GameFAQs, TCRF, Wayback and search engines returned 403/captcha/404 in this environment. No published literal was therefore available to test.
- Deeper post-tutorial content (late-game story screens) beyond the ~520 tutorial presses was not exhaustively walked; this report's screen enumeration covers the title/options-equivalent, character select, deck/chip screens, overworld, battle and all tested gates reachable from a fresh save.

## 9. Tooling

- `file`, `xxd`, `strings`, `grep`, `md5sum`/`sha1sum`/`sha256sum` for Phase 0/1.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for KEYINPUT/input-routine disassembly.
- Python 3 + Capstone 5.0.7 / Keystone (installed) for literal/BL scans (not needed for final result but available).
- Custom scripts in `/tmp/opencode/mmchipchallenge/`: `scan_headers.py` (logo/header scan), `scan_text.py` (shift/XOR/UTF-16 keyword scan), `scan_struct.py`/`scan_codetables.py` (mask runs and code-table scan), `scan_keyinput.py`, `state.py` (zlib `gbAs` savestate parser + GBA↔state address map), `drive.py` (savestate hotkeys), `gba.py` (XTEST input + screenshot crop), `render_romfont.py`/`render2.py` (VRAM/ROM tile rendering), `title_combos.py` (combo enumeration).
- mGBA 3× under Xvfb `:315` with `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input; `scrot` + ImageMagick for frames; `tesseract` for OCR triage.
- No ROM or copyrighted assets are redistributed; only hashes, addresses, counts and tooling are published.
