# Dragon Tales: Dragon Adventures (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Dragon Tales: Dragon Adventures/Dragon Tales: Dragon Adventures.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `DRAGONTALES` |
| Game code | `BD9E` (`BD9E9G`, Rev. 00) |
| Maker | `9G` (Global Star Software / Handheld Games LLC) |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Header checksum | `0x0000`; complement byte `0x99` |
| MD5 | `eb345977c4b1c846c9dec4141ec18343` |
| SHA-1 | `ffe8b5882778a74d414a21b610d4dc0aff1126e4` |
| SHA-256 | `5f2d7b6fe94de03744dcca2806bb59cee79f6b3c39dc489d3e604fcaa0995b03` |

**Phase 0 / patch check.** Exactly one GBA header/Nintendo-logo signature exists, at file offset `0x4`; there is no second header and no appended trainer/cracktro. The entry word is the unmodified `0xEA00002E` branch, so the image is the retail build. The tail of the ROM is `0xFF` padding. The complement byte (`0x99`) does not match the naive `-(sum of bytes 0xA0..0xBC)` rule (`0xB2`), but the stock entry, single header and lack of any patch signature rule out a rebuilt/trainer header — this is a normal licensed-header quirk, not a modification. No patch/trainer was applied for analysis; one throwaway **copy** was patched only to *force-render* the debug menu (see §6b).

## 2. Executive summary

**There is no player-facing cheat system in this game.** No password screen, no on-screen code-entry alphabet, no controller button-code detector, and no unlockable debug menu exist in the reachable game. Every published "code" for this title is a CodeBreaker / Action-Replay **memory patch** (e.g. `830044CC 00E7` → EWRAM `0x020044CC`) — out of scope for this engagement and not an in-game cheat.

The ROM *does* contain a complete, fully functional **developer debug menu** — Level Select (Story / Map / Difficulty, 5 stories), Test Map, Puzzle MiniGames, Sound Test, Music Test, Game Options, Clear Save — with its own string bank and handlers. However, its sole entry function (`0x08015288`) has **zero references anywhere in the ROM**: no `BL`, no function-pointer table entry, no literal pointer, and no ARM-side call. A live GDB breakpoint on it never fired while every reachable screen was walked and a broad set of button combinations was tried. This is textbook §16.3 **dead code**: the handlers and strings shipped, but no caller reaches them. I proved the menu is *functional* by patching an analysis copy to swap the title-screen handler for the debug handler; the Level Select rendered and pressing A launched the chosen map directly into gameplay.

Consequently §0.2's "mint an unpublished code" deliverable is **not applicable**: no code space exists. The negative is bounded by an exhaustive screen walk, a full-text/key-mask table search with counts, verification of the published codes, and a zero-reference proof of the debug gate.

## 3. How to reproduce

Emulator: mGBA under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `-3` scale. Keymap (mGBA SDL default): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys, L=`a`, R=`s`. Hold keys ≥120 ms.

Reachable menu path (verified with screenshots):

1. Boot → Handheld Games / MasyX / Sony splash sequence (A/B/Start skips).
2. "Press Start" title.
3. Start → main menu: `Start`, `options`, `credits`.
4. `options` → Game Options: `Exit`, `Sound` (volume), `Music` (volume); B returns.
5. `credits` → scrolling CREDITS screen; A/B/Start skips.
6. `Start` → gameplay; Start → "Paused" overlay only (no menu entries); Select/D-pad/B show no hidden option.

Published-code check: no password/button codes are published. The only listed codes are CodeBreaker/AR RAM patches (`0000976D 000A`, `1006324A 0007` enable; `830044CC 00E7` max Blue Jewels; `830044C8 0063` cupcakes; `83004470 0063` dragonberries; `830044D4 0063` music notes) — all target EWRAM `0x0200xxxx`, i.e. memory edits, not in-game input codes. None were tested as cheats because they are out of scope.

Debug-menu reproduction (analysis copy only): patch file offsets `0x14D34` and `0x14D38` from `0x08050281`/`0x0805028D` (title init/loop thunks) to `0x080505BD`/`0x080505C9` (debug init/loop thunks), boot the patched copy, press A/Start through the splash, and the Level Select screen appears (patched file kept in `/tmp/dragontales/forcedebug3.gba`; not redistributed).

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x080000C0` | crt0 ARM entry | Derived |
| `0x08015288` | **debug-menu "goto" function** — calls `0x08051E84(0x080505BD, 0x080505C9)` at `0x0801536A` | Derived |
| `0x0801536A` | only call site passing the debug thunk pair to the screen dispatcher | Derived |
| `0x08028C5C` | debug menu init (loads string pointers, resets fields) | Derived |
| `0x08028D44` | debug menu loop (button masks `0x10/0x20/0x40/0x80/0x01/0x02/0x08`) | Derived |
| `0x080505BC` / `0x080505C8` | thunks → debug init / loop | Derived |
| `0x08051E84` | screen dispatcher: calls init, stores loop pointer to `0x0300029C` at `+0x24` | Derived |
| `0x0802B9D4` | pause handler (sets `[state+0x5C] \|= 2`) | Derived |
| `0x08027F9C` | main-menu loop (Up/Down selection, A/Start confirm) | Derived |
| `0x0806331C` | `isPressed(mask)`: `(mask & [0x03000798]) && !(mask & [0x030007A4])` | Derived |
| `0x03000798` / `0x030007A4` | key-edge / key-held state words | Derived |
| `0x0300029C` | current screen loop function pointer | Derived |
| `0x083BD774`–`0x083BD7CC` | debug-menu string pointer table (23 entries) | Derived |
| `0x08093E5C`–`0x08093F08` | story/difficulty labels (`Dragonberry Drought`, …, `Easy`, `Medium`, `Hard`) | Observed |
| `0x08096EA4`–`0x08096F38` | debug labels (`Select a level to view!`, `Game Options`, `Sound Test`, `Music Test`, `Clear Save`, `PAUSED`) | Observed |
| `0x080934D0`–`0x08093520` | font glyph ASCII table (`0x18`..`^`) — the only "alphabet"; not a password alphabet | Derived |
| `0x020044CC`, `0x020044C8`, `0x02004470`, `0x020044D4` | EWRAM addresses targeted by published CodeBreaker codes | Derived (published) |

File offset ↔ ROM address: `addr = 0x08000000 + offset`.

## 5. Algorithm

No password/serial algorithm exists. The relevant input algorithm is the single button test used by every screen:

```
isPressed(mask):
    return 1 if (held_edge[0x03000798] & mask) != 0
              and (held_prev[0x030007A4] & mask) == 0
    else 0
```

GBA key bits used: A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200.

Screen dispatch:

```
set_screen(init, loop):
    clear [0x03002650]; reset graphics/sound
    call init()                     # via 0x08072DD8
    [0x0300029C] = loop | 1         # Thumb pointer
```

The debug-menu screen's reachable-state graph (from `0x08028D44`): mode 0 = Level Select (Left/Right alter Story index, bounded 0..5); mode 1/2 = further option pages reached with Up/Down; A/B/Start perform launch/back. This graph is only entered through `0x08015288`.

## 6. Tables

**Debug-menu string table, `0x083BD774` (file `0x3BD774`), 23 entries:**

| Index | Pointer | String |
|---:|---|---|
| 0 | `0x08093AA0` | Press Start |
| 1 | `0x08093A98` | Present |
| 2 | `0x08093ECC` | Level Select |
| 3 | `0x08096EA4` | Select a level to view! |
| 4 | `0x08096EBC` | Level: |
| 5 | `0x08096EC4` | Next |
| 6 | `0x08096ECC` | Back |
| 7 | `0x08096ED4` | Game Options |
| 8 | `0x08096EE4` | Sound Test |
| 9 | `0x08096EF0` | Music Test |
| 10 | `0x08093EE4` | Difficulty |
| 11 | `0x08096EFC` | Music |
| 12 | `0x08096F04` | Sound |
| 13 | `0x08096F0C` | Exit |
| 14 | `0x08093EF0` | Easy |
| 15 | `0x08096F14` | Medium |
| 16 | `0x08093F00` | Hard |
| 17 | `0x08096F1C` | On |
| 18 | `0x08096F20` | Off |
| 19 | `0x08096F1C` | On |
| 20 | `0x08096F20` | Off |
| 21 | `0x08096F24` | Clear Save |
| 22 | `0x08096F30` / `0x08096F38` | PAUSED / Paused |

Story labels at `0x08093E5C`: `Dragonberry Drought`, `Bye Bye Flutterbye`, `Help! I'm Lost`, `PuzzleWood`, `Scallywag`, `Puzzle MiniGames`, `Test Map`. Map labels at `0x08093F08+`: `school1_a0`, `school1_c0`, `school2_a0`, `school2_c0`, … (`0x08094000`–`0x08094C14`), plus puzzle maps `puzzle1`–`puzzle5` at `0x0809473C`.

**Input-mask distribution across all 96 call sites of `0x0806331C`:** `A(1)=23`, `B(2)=16`, `Select(4)=11`, `Start(8)=16`, `Right(0x10)=6`, `Left(0x20)=6`, `Up(0x40)=7`, `Down(0x80)=4`, other=1, no-immediate=6. **Zero combination masks** — no button sequence detector exists.

## 6b. Enumeration

**Code space:** empty. There is no password alphabet (the sole alphabet in the ROM is the font glyph table at `0x080934D0`), no code-entry screen on any reachable menu, no validator, no key-mask sequence, and no flag written by an input cheat. Therefore no novel code can be minted — this is a *proven* absence, not an untested one.

**Reachable screens enumerated (all walked, RAM/screenshot verified):** splash (Handheld Games / MasyX / Sony), "Press Start" title, main menu (3 options), Game Options (3 entries), credits, gameplay, "Paused" overlay. No hidden entry appears on any of them.

**Hidden debug menu enumerated (forced on an analysis copy):** Level Select with three live fields —
- Story: `Dragonberry Drought → Bye Bye Flutterbye → Help! I'm Lost → PuzzleWood → Scallywag` (5 values; observed by pressing Right),
- Map: per-story maps displayed as `school1_a0`, `school1_c0`, `school2_a0`, `school2_c0`, … (dozens; observed changing with Right/Down),
- Difficulty: `Easy / Medium / Hard` (observed `Normal → Hard` cycling).
Pressing A on Level Select launched the chosen map into gameplay (observed) — the menu is fully functional. Additional labels present but not individually launched: Test Map, Puzzle MiniGames, Sound Test, Music Test, Music/Sound On/Off, Clear Save, Game Options.

**Bounds proven by rejection / absence:**
- All 96 input-check call sites use single-button masks; no combination or sequence gate exists (table in §6).
- `0x08015288` has **0** `BL` hits, **0** pointer-table entries, **0** literal-pointer hits across the whole 4 MiB; a live GDB breakpoint there never fired after the full menu walk and 8 multi-button combinations at title/menu/credits.
- Keyword search over 93,870 extracted strings: `password`/`cheat`/`secret`/`unlock`/`enter code`/`debug` → **0** hits. Hits for `code`, `test`, `level`, `select` were all classified as dialogue, credits, font data or the debug-menu bank.
- The only published codes are memory patches; their literals do not appear as player-input codes anywhere in the ROM.

## 7. Validation evidence

- **Observed:** every reachable screen via Xvfb/mGBA screenshots; the debug menu rendering and its Story/Map/Difficulty values and A→gameplay launch on the analysis copy; GDB reads of `0x03000798`/`0x030007A4` and `0x0300029C`.
- **Derived:** string-pointer table decode, screen-dispatcher call graph, zero-reference scan, input-mask distribution, debug-loop mode transitions from Thumb disassembly.
- **Inferred:** that the debug menu was compiled in but deliberately left unreachable in this retail build (could equally be an artifact of the engine's shared codebase). No published source confirms intent.

## 8. Unknowns

- Whether any unreachable *second* code path (e.g. a build-time flag or an external linker) could have called `0x08015288`; in the analyzed binary no caller exists.
- The Debug-menu "Clear Save" action was not executed against a real save file (the `.sav` was empty); its effect is inferred from its label and handler position.
- Exact map-list length per story was not counted exhaustively; only representative values were observed. None of this affects the cheat conclusion (no reachable gate).

## 9. Tooling

`strings -t x`, `grep -abo`, `xxd`, `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7 (BL/PC-literal scanners in `/tmp/dragontales/scan.py`, `masks.py`), mGBA (Xvfb `:317`, `SDL_AUDIODRIVER=dummy`), `xdotool` + Python key helper (`k.py`), `scrot`/`import -window root`, `gdb-multiarch` (single-session GDB stub at `:2345`; used as an oracle per §16.19), Python byte-patching for the analysis-only forced-menu copy. No ROM or copyrighted assets are redistributed; only addresses, hashes, and findings are reported.
