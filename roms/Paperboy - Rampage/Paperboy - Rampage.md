# Paperboy & Rampage (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Paperboy - Rampage.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `PAPERBOYCOMP` |
| Game code / maker | `B6BE` / `20` |
| Version / fixed byte | `0x00` / `0x96` |
| Entry word | `0xEA00002E` → stock `b 0x080000C0` (no cracktro/trainer) |
| Header checksum | stored `0x0000`, computed `0x0588`, complement byte `0x5F` — rebuilt-header artifact (§16.1), not a patch |
| MD5 | `122ec4309cb7aa7a13f880de1ec3e703` |
| SHA-1 | `6a18cc723a2ca74dd5974bf46192f0369f7e33e5` |
| SHA-256 | `052d53596da7b7d9b1631036dd4d69f0a555c7d053ef44a64d808e418f7ad6d6` |

Embedded-header scan: exactly **one** Nintendo-logo/header hit (file `0x0`, ROM `0x08000000`). No second image, no appended trainer. Compilation of two games (Paperboy + Rampage) by Frame Studios / 7th Sense, published by DSI Games (2005).

## 2. Executive summary

**There is no reachable developer-intended cheat, password, level-select or unlock system in this ROM.** What the ROM *does* contain is a **cut/dead button-code subsystem**: a complete three-entry, six-press matcher with an input-history buffer and a validator. The three stored sequences are:

1. `A B B B Up R`
2. `Up Up Down Down A R`
3. `A A B B Left Left`

Their "success" callbacks are all `BX LR` no-op stubs, and the only function that feeds the matcher has **no caller anywhere in the image** (no Thumb BL, no ARM BL, no function pointer in ROM or RAM). Consequently no button sequence produces any effect; the history buffer at `0x03004EC8` never fills in the emulator. This is a **cut feature** (§16.3), not a working cheat.

The title screen offers only Paperboy / Rampage / Credits; each game has a pause menu (Continue / Quit) and a quit-confirm screen. Paperboy additionally has an Easy St. / Middle Rd. / Hard Way difficulty selection with Score 1x/2x/3x — normal game options, not a cheat. All UI text is plain ASCII with direct 32-bit literal pointers; the two 72-byte tables at `0x0809F28C` / `0x0809F34C` are font glyph-order tables, not encoded text banks.

Published-code check: 3rd party cheat index cheats page (Wayback 2020 snapshot) is empty, 3rd party cheat index lists 0 cheats, 3rd party cheat index list only Action Replay / CodeBreaker **memory-edit** codes (`7711ce98 b828a075` etc.) — explicitly out of scope. 3rd party cheat indexes document only unused text and leftover "casa … Special Test" object names. No published in-game code exists to verify.

## 3. How to reproduce

- Emulator: `mgba -3` under `Xvfb :317`, `DISPLAY=:317 SDL_AUDIODRIVER=dummy`.
- Keymap verified against `KEYINPUT` (`0x04000130`, active-low): `x`=A(`0x01`), `z`=B(`0x02`), `BackSpace`=Select(`0x04`), `Return`=Start(`0x08`), arrows = D-pad (`Right 0x10`, `Left 0x20`, `Up 0x40`, `Down 0x80`), `s`=R(`0x100`), `a`=L(`0x200`). Active-high mirror is at IWRAM `0x03000774` (held) and `0x03000778`.
- Menu path: boot → legal + DSI + Frame Studios splash (≈6 s or Start to skip) → title. Press **A** on the title to launch the highlighted game (Start does nothing there). Paperboy → "Daily Sun / Press start to Play" → Start → Easy/Middle/Hard route screen → A → gameplay. Start in gameplay → PAUSE / CONTINUE / QUIT.
- RAM evidence: mGBA `.ss1`–`.ss9` savestates (PNG with zlib `gbAs` chunk); decompress and read IWRAM at state offset `0x19000 + (addr-0x03000000)`. Key addresses: title selection `0x0300671D`, key mirror `0x03000774/78`, code-module flag `0x03004EC0`, code input history `0x03004EC8`.
- Code test: load a gameplay savestate (flag = `0x08`), press each 6-button sequence, save a new state, read `0x03004EC8`. Result is `00 00 00 00 00 00` for every sequence including a novel one.

## 4. Address map

| ROM/file offset | ROM address | Meaning |
|---:|---:|---|
| `0x09EE94` | `0x0809EE94` | Button-code table, 3 records × 16 bytes (6 × u16 mask + u32 callback) |
| `0x01715C` | `0x0801715C` | Reset history: clear 6 halfwords at `0x03004EC8`, write arg to `0x03004EC0` |
| `0x017184` | `0x08017184` | New-press edge detector (reads `0x03000778`, masks 10 buttons) — **no callers** |
| `0x0171E8` | `0x080171E8` | Shift history left, append pressed key, call validator |
| `0x017210` | `0x08017210` | Validator: 3 records × 6 halfword compares, dispatch via `0x0801C4A8` (`bx r0`) |
| `0x01727C/80/84` | `0x0801727C/80/84` | The three success callbacks — all `BX LR` (no effect) |
| `0x0153BC` | `0x080153BC` | Screen setup that calls reset history with `r0=8` |
| `0x018A70` | `0x08018A70` | Title-input handler (Right/Left change selection, Start confirms) |
| `0x0196DC…` | `0x080196DC…` | Pause-menu text pointers (PAUSE/CONTINUE/QUIT) |
| `0x09F144/64` | `0x0809F144/64` | Unused text (matches 3rd party cheat indexes) |
| `0x09F28C/34C` | `0x0809F28C/34C` | Font glyph-order tables (72 bytes each) |
| `0x3B7E80…` | `0x083B7E80…` | "casa 101…120" object/test-name data (3rd party cheat indexes "Special Test"), no code pointers |

RAM: `0x03000774` held buttons, `0x03000778` pressed buttons, `0x0300671D` title selection index, `0x03004EC0` code-module flag (set to 8), `0x03004EC8` code history (6 halfwords). IWRAM savestate base = state offset `0x19000`.

## 5. Algorithm

Validator pseudocode, reimplemented from `0x08017210`:

```
history[6]        = RAM 0x03004EC8   # newest key appended at index 5
table[3][16]      = ROM 0x0809EE94   # 6 u16 masks + u32 callback
for i in 0..2:
    if all(history[j] == table[i].masks[j] for j in 0..5):
        cb = table[i].callback
        if cb != 0: call cb()        # cb is 0x0801727C/80/84 -> BX LR
```
Key numbers are the active-high GBA masks (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`). New presses are detected by `current & ~previous` at `0x08017184`. There is no checksum, no field decoding, and no generator — it is a pure 6-tuple compare.

## 6. Tables

| # | ROM record | Raw masks | Buttons | Callback | Effect |
|---|---|---|---|---|---|
| 1 | `0x0809EE94` | `01 02 02 02 40 0100` | A B B B Up R | `0x0801727D` → `BX LR` | none |
| 2 | `0x0809EEA4` | `40 40 80 80 01 0100` | Up Up Down Down A R | `0x08017281` → `BX LR` | none |
| 3 | `0x0809EEB4` | `01 01 02 02 20 0020` | A A B B Left Left | `0x08017285` → `BX LR` | none |

The apparent 4th record at `0x0809EEC4` (`4000 0000 0002 0000 0004`, +12 = `0x00003333`) is **not** an entry: the loop bound is `r8=3`, so only records 0–2 are compared; it is unrelated data.

Accessibility inventory:
- Input handler `0x08017184`: **0** Thumb BL, **0** ARM BL, **0** 32-bit pointer (ROM or savestate RAM) → unreachable.
- Validator `0x08017210`: called only from `0x08017202` (inside the unreachable `0x080171E8`).
- Reset `0x0801715C`: called from `0x0801544A` (live screen setup) — explains flag `0x08` on Paperboy screens, but does not make the matcher reachable.

## 6b. Enumeration

**Space definition.** 10 buttons × 6 positions = 10⁶ = 1,000,000 possible 6-press tuples (edge-triggered, single-button presses only). The table stores exactly **3** accepted tuples (§7 enumeration by running the validator's own comparison logic over the whole table; the table has 3 records by the `r8=3` loop bound). There is no checksum width or reserved-bit space; the format is a raw tuple compare.

**Accepted values:** the three tuples in §6. All three were entered in the emulator on the Paperboy gameplay screen where the module flag is initialized (`0x03004EC0 = 8`).

**Novel code (not in any published list and not in the ROM table):** `Left Right Left Right B A` (`20 10 20 10 02 01`). Entered in the emulator; result identical to the three ROM tuples: `history[0x03004EC8] = 00 00 00 00 00 00`, flag unchanged at `0x08`, no HUD/state/flag change beyond ordinary gameplay motion.

**Bounds proven by rejection.** All four tested tuples (3 stored + 1 novel) are rejected by the running game: the matcher's history buffer never receives a single button value, so no tuple can ever match. This is a *stronger* negative than checksum rejection — the accept path is not wired up. The ROM's own success callbacks are `BX LR`, so even a hypothetical match has no effect: **no code, published or novel, can change game state.**

Because the system is a cut feature with no effect, the §0.2 requirement of demonstrating a novel code's *effect* is unachievable here; it is reported as a bounded negative with the complete space enumerated, the accept path disproved statically (zero callers, no-op callbacks) and dynamically (all four inputs rejected).

## 7. Validation evidence

- **Observed** (emulator + savestate RAM): boot screens → title (Paperboy/Rampage/Credits), Paperboy Daily-Sun/route screen, Easy St./Middle Rd./Hard Way with Score 1x/2x/3x and NON-CUSTOMERS, Paperboy gameplay, PAUSE/CONTINUE/QUIT, quit-confirm, Rampage story intro, Rampage gameplay with Damage/Credits HUD, Rampage pause. Title selection index `0x0300671D` read as `0x00` at title; code flag `0x03004EC0 = 0x08` on Paperboy screens; history `0x03004EC8` = all zeros on every screen and after every code attempt.
- **Observed** (KEYINPUT): full keymap verified by holding each key and reading `0x04000130` / `0x03000774`.
- **Derived** (disassembly): button-code table, validator, edge detector, callback stubs, zero-caller proof (Thumb + ARM BL scan and pointer scan), screen init call with `r0=8`.
- **Inferred**: the subsystem was a developer/test hook removed before release (callback stubs + orphaned input path). The "casa … Special Test" strings are leftover level-editor/test-object labels per 3rd party cheat indexes, not a menu.
- **Web (data)**: 3rd party cheat index cheats page empty; 3rd party cheat indexes 0 cheats; 3rd party cheat indexes Action Replay codes only; 3rd party cheat index page documents unused text and the Special Test list only. No prompt-injection payload encountered in fetched pages.

## 8. Unknowns

- The original intent of the three button sequences (developer test hooks vs. planned cheat codes) is unknown; their callbacks are empty in this build.
- The "Hard Way" / Score 2x/3x route options were displayed but not fully played through; they are ordinary difficulty settings, not unlockables.
- `0x0809EEC4` and following bytes are unrelated data of unknown purpose.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for raw disassembly; Capstone 5.0.7 + custom Python scanners for Thumb PC-relative literal loads, BL targets and key-mask table runs.
- `strings -t x`, `grep -abo`, `xxd` for string/byte reconnaissance.
- `mgba -3` on `Xvfb :317` with `openbox`, `xdotool` XTEST input, `scrot` + ImageMagick crop, Tesseract OCR for screen identification.
- `ss.py`: mGBA `.ss1` PNG `gbAs` chunk zlib decompressor and IWRAM reader.
- `gba.py` / `walk.py`: keypress, screenshot, savestate and OCR helpers.
- `gdbdrv.py`: temporary GDB-stub driver (abandoned: mGBA's stub does not resume reliably here; all RAM evidence in this report comes from savestates).
- No ROM or copyrighted assets are redistributed in this report.
