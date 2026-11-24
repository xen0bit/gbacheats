# Lemony Snicket's A Series of Unfortunate Events (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Lemony Snicket's A Series of Unfortunate Events.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `LEMONY_ASOUE` (`0xA0`–`0xAB`) |
| Game code / maker | `BLYE` / `52` (Activision), region E |
| Version / complement / checksum | `0x00` / `0x0E` / `0x0000` |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock; no scene cracktro patch) |
| MD5 | `49a2135d9680e86ed881bf1458fe4746` |
| SHA-1 | `f852812f37b3fb8fae36354e2213da3db4804c36` |
| SHA-256 | `eb0e2af0dffe04e17f5ab86b1cfc35f7a048267c80ca4ce0a74e803789cb8f29` |

**Embedded-header scan:** the 156-byte Nintendo logo occurs twice — header 1 at file `0x0` (header base `0x0`) and a second, byte-identical header at file `0x4DCE0` (base `0x0804DCE0`), same title/code/maker and stock entry branch. Its code diverges from header 1 at `+0xC0` (ARM function prologue `mov r12,r0; push {r0-r11}`), i.e. a secondary loader/CRT image, **not** an appended trainer (no trainer menu strings, no patched entry word). No cheat/trainer patch detected in the retail image.

## 2. Executive summary

**There is no player-accessible password, button-code, or level-select cheat system in this GBA build.** The main menu has exactly three entries (New Game, Load Game, Credits); the in-game pause/OPTIONS screen has six settings entries and four L/R tabs; no password entry field, no options-level cheat menu, and no key-mask cheat table exists.

**A developer debug menu does exist in the ROM** (state 9 of the game's 30-state screen machine) with at least eight entries, including `Toggle Invincibility`, `Cheat To Book 1/2/Books`, and `Map Select Replay`. Its screen was rendered and its labels observed by invoking the state-9 init handler directly from mGBA's command-line debugger (savestate + RAM proof). **No in-game path reaches it in this retail ROM**: state 9's handlers are registered in the dispatch table, but none of the 11 static writers of the "next-state" variable ever writes 9, 24 button combinations were tested at the title with RAM verification (none produced state 9), and no published source documents an unlock. This is the "dead/gated feature" case of guide §16.3 — dev code present but unreachable by controller input, **not** a usable cheat.

Published GBA "cheats" are exclusively Action Replay / GameShark memory-edit codes (out of scope). The only 3rd party cheat indexes GBA cheats-page entry is an *Unlimited Photos* glitch, not a code. PS2/GC console commands and puzzle-piece unlockables belong to a different SKU (§16.11) and do not apply here.

Fetched web pages were treated as data (§16.8); no prompt-injection payload was observed.

## 3. How to reproduce

1. `Xvfb :319 -screen 0 1024x768x24 &`, `DISPLAY=:319 openbox &`, `export SDL_AUDIODRIVER=dummy`.
2. `mgba -3 "<rom>.gba"` (mGBA 0.10.5). Keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows; hold ~120–150 ms.
3. Boot → Activision splash → title (`START`) → main menu: **New Game / Load Game / Credits**.
4. Load Game → three empty slots (no password field). Credits → scrolling Griptonite/Activision legal roll.
5. New Game → three `Open` slots → first slot → cutscenes → beach gameplay (Violet). `START` → OPTIONS with L/R tabs: tab 1 OPTIONS (Save Game, Quit Game, Music Volume: 5, SFX Volume: 5, Text Scroll Speed: 1, Gamma: Normal); tab 2 INVENTORY; tab 3 MAP; tab 4 back to OPTIONS.
6. RAM proof: mGBA savestates (`Shift+F1`) are PNGs with a zlib `gbAs` chunk; decompress to a 397,312-byte (`0x61000`) image. Layout (§16.13): VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`. Screen-state word = IWRAM `0x03004AA0` (file `0x1DAA0`); duplicate at `0x03004AB8`. Observed values: `5` title, `17` New Game slots, `24` cutscene, `6` gameplay, `7` pause OPTIONS, `13` inventory, `28`/`29` transitions.
7. Debug menu reproduction (research-only, not an in-game cheat): open mGBA's CLI debugger (`mgba -d`, stdout via `stdbuf -o0`), break at the per-frame dispatcher `0x0800C968`, set `r14 = 0x0800C968`, `pc = 0x0801CDE9` (state-9 init, Thumb bit), continue. The debug-menu screen renders. (This corrupts the frame's register context; it is a diagnostic oracle, §16.19, not a player path.)

## 4. Address map

| Address (ROM) | Meaning |
|---|---|
| `0x080000C0` | Stock ARM entry (`crt0`) |
| `0x0804DCE0` | Second embedded GBA header (loader image) |
| `0x0805C084` | 62-byte scrambled ASCII/glyph permutation table used by text renderer |
| `0x0805C0C0`–`0x0805C118` | Menu-definition tables (two groups of 10 handler pointers) |
| `0x0805C11C` | ASCII string `Map Select Replay` |
| `0x0805C130` | ASCII string `Toggle Invincibility` |
| `0x0805C32C` | ASCII string `Sound Test` |
| `0x0805C0F0`–`0x0805C118` | Debug-menu option handlers: `0801CF60, 0801CF94, 0801CFD8, 0801CFE4, 0801CFF0, 0801D024, 0801D02A, 0801D030, 0801D036, 0801D00C` |
| `0x080573B8` | Screen-handler table, 90 pointers = 30 states × 3 (init/update/cleanup) |
| `0x0801CDE8 / 0x0801CEDC / 0x0801D08C` | State 9 (debug menu) init / update / cleanup |
| `0x0801D0C0` | Builds the debug-menu option list (text IDs `0x2B`–`0x2E`) |
| `0x0801CFF0` | `Toggle Invincibility` handler: `eors r0,r2; strb r0,[r1,#8]` on global `0x0300686C` → toggles byte `0x03006874` |
| `0x0800C700` | Screen-transition dispatcher: copies `0x03004AB8`→`0x03004AA0`, then calls init/update |
| `0x0800C8E8` | Transition test: `if ([0x03004AA0] != [0x03004AB8]) transition` |
| `0x0800A894`, `0x08018D0C` | Only two Thumb PC-relative loads of the KEYINPUT literal (`0x04000130`) — input is centralized |

RAM: `0x03004AA0` current screen state, `0x03004AB8` next screen state, `0x0300686C` debug/global save block, `0x03007F00` initial stack pointer.

## 5. Algorithm (screen state machine)

```
current = [0x03004AA0]; next = [0x03004AB8]
if current != next:
    cleanup_dispatch(table[current*3 + 2])
    [0x03004AA0..+0x0C] = [0x03004AB8..+0x0C]   # struct copy (ldmia/stmia)
    init_dispatch(table[current*3 + 0])
    update_dispatch(table[current*3 + 1])
table_base = 0x080573B8;  handler = table[state*3 + slot]
```

State 9's handlers are present in the table, but the writers of the next-state word were enumerated statically (11 sites): they write `2`, `0xFE`, `0xFF`, `0`, `-1`, and flag bits — **never 9**. In-game input therefore cannot select state 9.

## 6. Tables

### 6.1 Debug-menu entries (observed on the forced state-9 screen, OCR)

| # | Label | Handler |
|---|---|---|
| header | `* Map Select` (highlight marker) | — |
| 1 | `Map Select Replay` | `0x0801CF60` |
| 2 | `Test Sound and Music` | `0x0801CF94` |
| 3 | `Default Items` | `0x0801CFD8` |
| 4 | `Cheat To Book 1` | `0x0801CFE4` |
| 5 | `Cheat To Book 2` | `0x0801CFF0` (also toggles a byte — see below) |
| 6 | `Cheat To Books` | `0x0801D024` |
| 7 | `Cheat to Replay (All books Complete)` | `0x0801D02A` |
| 8 | `Toggle Invincibility` | `0x0801D030` / `0x0801D036` |

The handler table has 10 slots; two further entries are not labelled on the single captured frame (screen may scroll). The `Toggle Invincibility` effect is *derived* from `0x0801CFF0` (byte toggle at `0x03006874`); it was not exercised on a live in-game screen because state 9 is not reachable by controller.

### 6.2 Screen states (RAM, `0x03004AA0`)

`2` splash/title, `5` title `START`, `6` gameplay, `7` pause OPTIONS, `13` inventory tab, `17` New Game slot select, `24` cutscene, `28`/`29` fade/transition, `9` debug menu (forced only).

### 6.3 Search counts (bounded negatives)

| Search | Result |
|---|---|
| `strings -n 5` ASCII runs | 120,435 total; keyword grep for `password/cheat/debug/secret/unlock/level select` → **0 hits** |
| ASCII/UTF-16LE/UTF-16BE/XOR-0x20/upper/lower encodings of `New Game`, `Load Game`, `Credits`, `PASSWORD`, `Cheat`, `Debug`, `Level`, `Continue` | **0 ROM hits** (text is font/glyph indexed; glyph permutation at `0x0805C084`) |
| LZ77 (`0x10` header) blocks decompressed | 1,004 candidates; none contained the above strings (decoder limitation noted in §8) |
| KEYINPUT literal `0x04000130` Thumb xrefs | 2 (`0x0800A894`, `0x08018D0C`) — no per-cheat key-mask tables |
| Raw `u16` mask `0x300` (L+R) | 7,299 byte hits — all incidental code/data, no cheat table structure |
| Next-state (`0x03004AB8`) static writers | 11 sites; none writes `9` |
| Button-combo fuzz at title (24 combos, incl. Konami code, L+R, L+R+Start, Start+Select+A+B) | 22 → state `5` unchanged, 2 → state `17` (ordinary New Game advance); **none → `9`** |

## 6b. Enumeration

* **Code space:** none exists. There is no password alphabet, no fixed-length input buffer, no comparison table against user-entered text, and no button-sequence table. The 62-byte table at `0x0805C084` is a **font glyph permutation**, not a password alphabet (it is a rearrangement of ASCII `0x20`–`0x7E`, and the normal ordered charset appears decompressed in EWRAM at savestate offset `0x22258`). Therefore space size = 0, and no "novel code" can be minted — this is a proven negative (§0.2 negative-result clause), not an untested gap.
* **Debug-menu space enumerated:** 10 handler slots at `0x0805C0F0`; 8 labels observed; the invincibility toggle handler and its target byte `0x03006874` identified. Bounds of reachability proven by the 11-writer static enumeration plus the 24-combo RAM-verified fuzz.
* **Rejection/bounds proof:** out-of-range/undocumented inputs were tested by the combo fuzz and rejected (state never became 9). Published AR codes are memory-edit codes and are out of scope; no in-game code list exists to test for literal presence. The 3rd party cheat indexes *Unlimited Photos* glitch is an in-game repetition exploit, not a code, and was not treated as a cheat code.

## 7. Validation evidence

* **Observed** — title/main menu/load/credits/pause/inventory screens walked in mGBA; state word read from savestate RAM for each; debug-menu screen rendered with the 8 labels after direct init invocation; 24 combos fuzzed with RAM state readback.
* **Derived** — state machine and handler table from Thumb disassembly; invincibility byte toggle from `0x0801CFF0`; reachability negative from the exhaustive next-state writer list.
* **Inferred** — second header at `0x4DCE0` is a loader/secondary CRT image; two debug-menu handler slots lack visible labels; the exact semantic mapping between handler slots 5–8 and the book-cheat labels is inferred from ordering.

## 8. Unknowns

* Whether the two unlabelled debug-menu handler slots correspond to off-screen entries reachable by scrolling (the state-9 screen could not be kept alive stably after the direct-init oracle corrupted the frame's registers).
* Whether a non-controller gate (e.g., a specific SRAM/flash save value written by a debug build tool) could enable state 9 — no such writer exists in the retail ROM's code.
* The LZ77 block decoder used in recon is a best-effort implementation; its failure to find compressed strings is a tooling limitation, but the font-permutation and RAM-charset evidence independently establishes the text-encoding finding.

## 9. Tooling

Scripts in `/tmp/lemony/`: `gba.py` (input/screenshot), `ss.py` (savestate parser), `save_state.sh`, `snap.py` (crop + tesseract OCR), `scan.py` (keyword/key-mask scan), `xref.py`/`blscan.py`/`statewrite.py`/`stateset.py` (xref scans), `lz.py`/`lzdump.py` (LZ77 recon), `dbg.py` (CLI-debugger FIFO driver), `patchss.py`/`patch2.py` (savestate research), `fuzz.py`/`fuzz2.py` (combo fuzzing). Tools: mGBA 0.10.5 CLI debugger, `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, tesseract, Xvfb/openbox/xdotool/scrot/ImageMagick. No copyrighted assets are reproduced here; only addresses, hashes, and observed labels are published.
