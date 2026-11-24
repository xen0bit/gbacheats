# That's So Raven 2: Supernatural Style (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `That's So Raven 2: Supernatural Style.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `RAVEN2` |
| Game code | `BZSE` (serial AGB-BZSE-USA) |
| Maker code | `4Q` (Buena Vista Interactive) |
| Version / complement / checksum | `0x00` / `0xEA` / `0x0000` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock, not a cracktro) |
| Build stamp | `May 23 2005 21:02:17` at file `0x16D690` |
| Sound engine | `GAX Sound Engine 3.05A` at `0x169438` |
| MD5 | `da7fa09ca99fa6c7e6462a29494d991e` |
| SHA-1 | `1bcd8c3b455b4d1f8f850fdc8d25b0257bd3b5be` |
| SHA-256 | `2270d7e38057d9b17f900566395ff9dacc5fdae650ec3d9f9897956d1f8c0e36` |

Addresses in this report are ROM addresses (`0x08xxxxxx`); file offset = address − `0x08000000`.

## 2. Executive summary

**No in-game/developer-intended cheat-code system exists in this GBA image.** The two
published "Secret Mode Codes" (Costume Mode: `← → ↑ ↓ B B B ↑ ↓`; Unlimited Energy:
`B B L R ↑ ↓ ↑ ← →`, "at the Press Start screen") are platform-copy artifacts: they
are absent from the ROM under every encoding searched, and the GBA title screen has
no code-entry surface — every D-pad/Start press routes directly to the save-slot
"NoteBook" screen. Entering either published sequence on the splash or title screen
produced only menu navigation, never a persistent flag (savestate RAM diffs).

The ROM does contain **dead/unreachable cheat-debug resources** and a **GameShark-gated
debug menu**:
- Archive resource names `BasicCheatsMenu`, `DebugCheatsMenu`, `ExtraCheatsMenu`,
  `LevelSelectMenu` exist at file `0x64B3EC`, `0x652F4C`, `0x6536E4`, `0x65522C`;
  **zero** 32-bit pointers (normal or Thumb-bit `addr|1`) reference any of them.
- A debug-menu text bank at `0x3C330…` (`Level`, `MapX`, `Music Player`, 50+
  `World 0x - Level…` entries) has a single pointer table at `0x8170BC8…0x8170E00`
  with **zero** incoming code xrefs.
- TCRF documents a debug menu enabled by GameShark codes
  `F96A20FE 1DFD09E5 / 0C290150 13B8BB07` then Start+Select. Cheat-device
  activation is **out of scope** for this engagement and was not used.

Conclusion type (guide §16.3): **no system**, plus **dead resources** and a
**gated feature** whose gate is external to the game. Not "not tested".

## 3. How to reproduce

- mGBA 0.10.5, `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.
- Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys; 100–200 ms holds, 150+ ms gaps.
- Boot path: Disney logo → (Start) A2M splash → (Start) "PRESS START" title →
  (any D-pad/Start) NoteBook save slots.
- Savestates: `Shift+F1` save slot 1, `F1` load; `Shift+F2`/`F2` slot 2, etc.
  States are PNGs with a zlib `gbAs` chunk; raw size 397,312 bytes; IWRAM at
  raw `0x19000`, EWRAM at raw `0x21000`.
- Published-code tests: from a clean "PRESS START" title or Disney splash state,
  enter each 9-press sequence with the helper loop above, then save a second state
  and diff the `gbAs` payloads. Results: only menu/animation bytes changed.
- Debugger used: Ghidra 12.1.4 via REA (raw-binary, ARM, base `0x08000000`,
  1247 procedures, 1040 strings); mGBA CLI debugger (`-d`) and GDB stub were also
  exercised but the CLI Ctrl-C resets the core and the shared GDB port is
  contended, so savestate diffs were the primary RAM oracle.

## 4. Address map

| Item | Address / file offset | Evidence |
|---|---|---|
| ROM base / header | `0x08000000` / `0x0` | Observed |
| KEYINPUT literal #1 (boot IRQ) | `0x08004DD0` / `0x4DD0` | Derived (Ghidra xref `0x08004DB2`) |
| KEYINPUT literal #2 (title Start-wait) | `0x08038BDC` / `0x38BDC` | Derived (Ghidra xref `0x08038B82`) |
| Input-history buffer | `0x0200C420`, 15 entries × `0x4C` bytes | Derived, `FUN_08004DAC` |
| Input index / count / current keys | `0x0200C410`, `0x0200C59C`, `0x0200C550` | Derived |
| Input update function | `FUN_08004DAC` @ `0x08004DAC`, called only by `FUN_08007DB0` | Derived |
| Main loop | `FUN_08004EF4` @ `0x08004EF4` | Derived |
| Debug-menu text bank | `0x803C330…`, pointer table `0x8170BC8…` | Observed + Derived |
| Dead cheat-menu resource names | `0x864B3EC`, `0x8652F4C`, `0x86536E4`, `0x865522C` | Observed |
| Dialog text bank (ASCII + `0xFFFC` space, `0xFFFE` terminator) | `0x74C400…`, `0x74FBFE…` | Observed |

Screenshots (work dir `/tmp/raven2/`): boot, title, NoteBook, main menu,
Bonus, Special Material, Options, Select Level, gameplay, Pause, View Vision,
plus both published-code attempts.

## 5. Algorithm

No validator exists to reverse. The relevant recovered logic is the input path:

```
FUN_08007DB0():                         # main input pump
    while (head != tail):
        FUN_08004DAC()                  # sample KEYINPUT, update history
        FUN_0801290C()                  # unrelated fade
        FUN_080022B0()                  # unrelated sprite/UI work
        FUN_080067B4()                  # unrelated object work

FUN_08004DAC():
    keys = 0x3FF ^ *(u16*)0x04000130     # active-high key mask
    history[i] <- keys (stride 0x4C)
    index = (index + 1) % 15
    FUN_08001CB8(index << 10 | *(u16*)(keys_global + 2))
```

`FUN_08038A7C()` waits for **Start only** (`(0x3FF ^ KEYINPUT) & 8`) and is a
generic UI helper with 8 callers; it does not buffer or compare sequences.
No function reads the 15-entry history except the input pump itself.

## 6. Tables

**Published codes tested (all rejected / non-functional on this SKU):**

| Source | Code | presses | Observed result |
|---|---|---|---|
| GameFAQs / VGChartz / cheatingdome | Costume Mode | `← → ↑ ↓ B B B ↑ ↓` | Title: opens NoteBook / returns to splash; no flag. Splash: no effect. |
| GameFAQs / VGChartz / cheatingdome | Unlimited Energy | `B B L R ↑ ↓ ↑ ← →` | Title/splash: menu navigation only; no flag. |

**Key mask convention (derived):** `~KEYINPUT & 0x3FF`:
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200`.

**Named UI resources (13):** `BasicCheatsMenu`, `BonusMenu`, `DebugCheatsMenu`,
`ExtraCheatsMenu`, `LevelSelectMenu`, `LinkMenu`, `MainMenu`, `OptionsMenu`,
`PauseMenu`, `RavenBioMenu`, `SaveMenu`, `StoreMenu`, `SummaryMenu`.
Only the retail ones are instantiated by reachable screens; the four
cheat/debug-named ones have no code pointers.

## 6b. Enumeration

This is a **bounded negative**, not a code-system enumeration.

1. **Code-space size:** 0. No password alphabet, no checksum, no sequence table,
   no entered-code field exists. Representable values: none.
2. **Published-list check:** 2 codes × 2 orders (forward/reversed, since some
   engines store histories newest-first) × 5 encodings (active-high mask,
   active-low mask, 3 index maps) × widths `{2,3,4,5,6,8,9,10,11,12,16,32}`
   bits/symbol and u8/u16/u32 byte orders = 0 plausible table hits. Small-width
   collisions were verified to be truncated-mask nonsense (e.g. d-pad masks
   truncate to 0 at 4 bits). ASCII spellings (`LRUDBBBUD`, `BBLRUDULR`, lowercase,
   reversed) also: 0 hits.
3. **Input-reader count:** exactly **2** code xrefs to I/O `0x04000130` in the
   whole 8 MiB image (`0x08004DB2`, `0x08038B82`); the second tests one bit
   (Start). Exactly **3** functions reference the input globals
   (`FUN_08004DAC`, `FUN_08004E74`, `FUN_08004E80`); none compares a sequence.
4. **String/text search:** 117,645 strings extracted; `password`, `enter code`,
   `cheat code`, `level select` → 0 in the dialog bank (the `COSTUME` hits at
   `0x74C43B…` are in-game pickup dialogue, not a code screen). UI text is
   font/tile-encoded; the visible labels were decoded by walking the screens.
   No 26/36-symbol code alphabet usable as an entry field was found — the
   `A…Z` runs near `0x64B8B9` are font resource metadata, not a validator table.
5. **Screen enumeration (12 screens, all reachable and walked):** Disney splash,
   A2M splash, "PRESS START" title, NoteBook (3 slots + Load/Delete),
   save-confirm, "Play" submenu (Select Level: L1 open, L2+ locked),
   main menu (Play/NoteBook/Bonus/Options/Credits), Bonus
   (Fashion Portfolio/Raven Store/Special Material), Special Material
   (Raven Bios/Raven Scrapbook), Options (Music/Sound/Hints/Language),
   gameplay HUD, Pause (Fashion Portfolio/View Vision/Quick Save/Options/Quit),
   View Vision. **None presents a text/code/button-sequence entry surface.**
6. **Rejection bounds:** the published sequences were entered on both the splash
   and title screens. Savestate RAM diffs (IWRAM `0x19000…`, EWRAM `0x21000…`)
   showed only cursor/timer/animation bytes; no persistent unlock flag changed.
   The level-select gate is progress-based (`Level 02 - LOCKED`), not code-based.
7. **Novel code:** not applicable — there is no validator to mint a code for.
   Per §0.2 this is reported as a proven bounded negative with the counts above,
   not as an unfinished confirmation.

## 7. Validation evidence

- **Observed:** header/hashes; all 12 screens in mGBA screenshots; both published
  code attempts and their savestate diffs; `strings` output; Ghidra inventory
  (1247 procedures / 1040 strings).
- **Derived:** the two KEYINPUT xrefs and their meanings; the 15×`0x4C` history
  layout; the dead-resource pointer counts; the `0xFFFC`/`0xFFFE` text encoding.
- **Inferred:** that the published codes belong to the console SKU (they match the
  console-style hint text and cannot be entered on this title screen). The exact
  console version was not tested.
- **Out of scope:** GameShark/CodeBreaker/Action Replay codes, including the
  TCRF debug-menu enabler. No cheat device was applied.

## 8. Unknowns

- Whether the console versions of the game really accept the two published codes
  (not tested; different SKU).
- Whether the dead `BasicCheatsMenu`/`ExtraCheatsMenu`/`DebugCheatsMenu` resources
  were ever wired in a prototype build.
- Exact reachability of the unused debug text bank at `0x3C330` if a GameShark
  patch were applied (excluded by scope).
- The GDB stub on shared port 2345 was contended by other sessions; memory was
  therefore read via savestate diffs rather than a live watchpoint. This does not
  affect the static xref counts.

## 9. Tooling

- `strings -t x -n 4`, `grep -abo`, Python (`capstone`, `struct`, `zlib`),
  `arm-none-eabi-objdump -M force-thumb`, Ghidra 12.1.4 via REA MCP, mGBA 0.10.5
  under Xvfb `:318` + openbox, `xdotool`, `scrot`, GDB stub / mGBA CLI debugger.
- Analysis scripts in `/tmp/`: `r2_scan.py`, `r2_pack.py`, `r2_pack2.py`,
  `r2_cmpscan.py`, `r2_keyinput.py`, `r2_state.py` (savestate `gbAs` extractor/differ).
- Screenshots in `/tmp/raven2/`.
- No ROM or copyrighted assets are redistributed; only addresses, hashes and
  findings are published.

## 10. Cleanup

All mGBA/Xvfb/openbox/GDB processes started for this job were terminated by PID;
`.sav`/`.ss*` artifacts were removed from the ROM folder (see coordinator reply).
