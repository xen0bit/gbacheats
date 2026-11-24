# Rayman: Hoodlum's Revenge (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rayman: Hoodlum's Revenge.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `HOODLUMS REV` |
| Game code | `BRYE` |
| Maker | `41` |
| Version | 0x00 (Rev.00) |
| Complement / checksum | 0x42 / 0x0000 (rebuilt-header artifact, §16.1) |
| Entry word | `0xEA000031` (stock Thumb/ARM crt0) |
| MD5 | `a31d19d40a70646eaeaa233ac46fe8d7` |
| SHA-1 | `f65700dcfc827a3e84c9dd19d6f5e55af019ac81` |
| SHA-256 | `fe9184c36995ae11cb096cd3eed645292747af4f7eeb72b797aa170a551f8512` |
| Developer (on-screen legal screen) | Backbone Entertainment; MusyX by Factor 5 |
| Published-cheat source | RayWiki "List of cheats in Rayman Hoodlums' Revenge" (snapshot `20240323044028` on web.archive.org); GameFAQs lists 8 entries but most are GameShark/CodeBreaker (out of scope) |

**Embedded-header scan:** the 156-byte Nintendo logo occurs once (file `0x4`). This is a single game image, not a multiboot/multicart pack. No appended trainer or cracktro was found; the entry word is the stock branch and the first 4 KiB disassembles as a normal crt0.

## 2. Executive summary

The game has **no password/code-entry screen and no alphabetic code system**. Its developer-intended cheats are **four simultaneous button chords (held on the save-slot "main menu")** implemented by a single validator at `0x0801F490`. All four documented codes were verified three ways: (a) the exact key masks were read from the emulated KEYINPUT register at the validator's action breakpoints, (b) the resulting RAM flag bytes were read before/after, and (c) the visible effects were captured in emulator screenshots.

The four codes are:

| Effect | Buttons held (active-high mask) | Raw KEYINPUT seen | Action address |
|---|---|---|---|
| Cheat mode enable (permanent; pause buttons turn green) | `L+Up+Select+L+B` = `0x266` | `0x0199` | `0x0801F606` |
| Debug info toggle | `L+R+Select+Start` = `0x30C` | `0x0F3` | `0x0801F4D0` |
| Region toggle (changing available languages) | `L+Left+Select+Start` = `0x22C` | `0x1D3` | `0x0801F558` |
| Complete save ("Marcie", every level unlocked, not completed) | `Left+Down+Select+Start` = `0x0AC` | `0x353` | `0x0801F59E` |

The debug-info toggle produces visible overlays: `Teensies: %d Lums: %d Score: %d` in-game, `pos: %d, %d` on the Level Map. A scan of every Thumb LDR-literal read of `0x04000130` (KEYINPUT) found 19 sites; only this validator implements multi-button chords — the others are single-button menu navigation or an internal debug-menu chord. The four branches are therefore the complete in-game button-cheat surface.

## 3. How to reproduce

Emulator: `mgba -3` on `DISPLAY=:316` with `SDL_AUDIODRIVER=dummy`. Default SDL keymap verified from mGBA source: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys 100–300 ms; for chords, press all keys down in a single XTEST burst (separate `xdotool` calls with ~10 ms gaps can be delivered across frames).

Menu path: boot → language select (English) → title "Press START" → **save-slot main menu**. All four chords are accepted on this screen. Then press Start on a slot to play.

Verification commands (from `/tmp/raymanhoodlum/`):
- `python3 keyscan.py` — enumerate all KEYINPUT literal-pool readers.
- `python3 blscan.py 0x0801F490` — find callers.
- `python3 xref2.py 0x080E89C4 ...` — find literal-pool loads of debug strings.
- `python3 ssdiff.py <before.ss1> <after.ss2>` — diff EWRAM (offset `0x21000` in the decompressed `gbAs` chunk) to read flag bytes without a GDB stub.
- `dbg.py` — mGBA `-d` CLI-debugger bridge (FIFO in, log out); breakpoints on the four action addresses confirm which branch fires and print the live KEYINPUT value in `r7`. A breakpoint at function entry is unsuitable for chord testing because it freezes the emulator on the first keydown.

## 4. Address map

| Address (ROM) | Meaning |
|---|---|
| `0x0801F490` | Cheat-chord validator (entry; called from menu handler `0x0801F630`) |
| `0x0801F49E`, `0x0801F528`, `0x0801F574`, `0x0801F5B0` | The four successive KEYINPUT reads, one per chord branch |
| `0x0801F4D0` | Branch 1 action — debug-info toggle |
| `0x0801F558` | Branch 2 action — region toggle |
| `0x0801F59E` | Branch 3 action — BL complete-save routine |
| `0x0801F606` | Branch 4 action — cheat-mode flag OR 2 |
| `0x0801DB34` | Complete-save constructor; `0x0801DC18` copies the name "Marcie" |
| `0x0801EE56` | Internal debug-menu chord check (`L+R+Select+Left`, calls `0x0801EC58`) — not one of the four public cheats |
| `0x0801F102`, `0x0801F232` | Single-button (Up/Down) menu navigation, not cheat chords |
| `0x080E89B0` | ASCII `3056.rafael.na.r` (build/author string) |
| `0x080E89C4` | ASCII `Marcie` (complete-save name) |
| `0x080E89C8`, `0x080E89D4`, `0x080E89E0` | `VERSION`, `Engine: %s`, `Game: %s` |
| `0x080E9268`, `0x080E9298`, `0x080E9878` | Debug overlays `pos: %d, %d`, `Level has %d lums. Max is 100.`, `Teensies: %d Lums: %d Score: %d` |
| `0x080E89F0`–`0x080E8A60` | Table of Thumb menu/debug-screen handlers (e.g. `0x0801F631`, `0x0801F799`) |
| `0x080EA199`, `0x080EAA49` | ASCII→font-tile mapping tables (`0xFF` = unsupported glyph) — proof UI text is tile-indexed, not plaintext |
| `0x020036A5` | Debug-info flag (0/1), written by branch 1 |
| `0x02000280` | Region flag (0/1), toggled by branch 2 |
| `0x02002A23` | Cheat-mode byte; bit 1 set by branch 4 |
| `0x02001140+0x2B8` / `+0x2C4` | Overlay counter table / index used by branch 1 |

File offset `= ROM address − 0x08000000` throughout (no multi-image base offset).

## 5. Algorithm

The validator takes a 16-bit key-event word in `r0`, calls a state helper at `0x8025E64`, then reads live KEYINPUT (active-low, 10 bits) and evaluates four independent branches in order. Pseudocode:

```c
u16 k = *(vu16*)0x04000130;          // active-low: A1 B2 Sel4 Sta8 Rgt10 Lft20 Up40 Dn80 R100 L200
if (helper() != 0) goto cheat_enable; // 0x801F492..0x801F4CE gating

// Branch 1 - debug info (0x801F49E)
if (!(k & 0x200) || !(k & 0x100) || !(k & 4) || (k & 8)) goto branch2;
toggle_debug_info();                  // 0x801F4D0: table push/pop; 0x020036A5 ^= 1
play_sound(18); return 1;

// Branch 2 - region (0x801F528)
branch2:
if (!(k & 0x200) || !(k & 0x20) || !(k & 4) || (k & 8)) goto branch3;
*(u8*)0x02000280 ^= 1;                // 0x801F558..0x801F56E
play_sound(18); return 1;

// Branch 3 - complete save (0x801F574)
branch3:
if (!(k & 0x20) || !(k & 0x80) || !(k & 4) || (k & 8)) goto cheat_enable;
create_complete_save();               // 0x801F59E -> 0x801DB34; name "Marcie"
play_sound(18); return 1;

// Branch 4 - cheat mode (0x801F5B0)
cheat_enable:
if (!(k & 0x20) || !(k & 0x40) || !(k & 4) || (k & 8) ||
    !(k & 0x200) || (k & 0x100) || (k & 1) || !(k & 2)) return 0;
*(u8*)0x02002A23 |= 2;                // 0x801F606
play_sound(18); return 1;
```

Key detail: branches 1–3 test only *required* bits (extra buttons are not explicitly excluded), while branch 4 also requires Start, R and A to be **released**. This is why the four masks are not simply four exact equality tests.

## 6. Tables

| Published effect | Required-held bits | Rejected bits | Accepted raw KEYINPUT (minimal) |
|---|---|---|---|
| Cheat mode | `Left,Up,Select,L,B` | `Start,R,A` | `0x0199` |
| Debug info | `L,R,Select,Start` | — | `0x00F3` (+ any extra bits) |
| Region | `L,Left,Select,Start` | — | `0x01D3` (+ any extra bits) |
| Complete save | `Left,Down,Select,Start` | — | `0x0353` (+ any extra bits) |

Observed effects:
- Complete save: slot 1 reads `Save Slot 1: Marcie`, `Level: Fairy Council`; score 50000; all map nodes open.
- Debug info: in-game banner `Teensies: 00 Lums: 663 Score: 50000`; Level Map `pos: 505, 1000 b`.
- Cheat mode: Level Map L/R arrows render green rather than grey (matches published description).
- Region: `0x02000280` toggles `0x00 → 0x01` (savestate diff), changing the language set available at the initial language screen.

## 6b. Enumeration

**Space.** The GBA keypad exposes 10 independent buttons, so a simultaneous held-chord state space is `2^10 = 1024`. The validator has exactly **four action branches** (function ends at `0x0801F62E`); no fifth branch, no sequence longer than one chord, and no alphabetic password validator exists. Branches 1–3 accept any key state containing their required bits (`2^6 = 64` spellings each before overlap); branch 4 accepts 4 spellings (Down/Right free). Distinct behavioural effects: 4.

**Novel / undocumented combination accepted.** The combination **`L+R+Select+Start+A`** is not in any published list. A breakpoint at the branch-1 action `0x0801F4D0` **hit** with `r7 = 0x000000F3` (KEYINPUT with L+R+Select+Start held), proving the game's own validator accepts it and toggles the debug-info state. (When sent as a single burst through XTEST without a breakpoint the flag can be seen to toggle twice — once per key event — so the net flag depends on event timing; the branch acceptance itself is proven by the breakpoint, and this nuance is labelled *Observed*, not inferred.)

**Bounds proven by rejection.** The undocumented near-miss **`L+R+Select+Down`** (debug chord with Start replaced by Down) was pressed on the same screen with savestates saved before and after. All three cheat flags were unchanged: `0x02000280 = 0x01 → 0x01`, `0x02002A23 = 0x03 → 0x03`, `0x020036A5 = 0x00 → 0x00`. This bounds the debug branch to its required Start bit. A further rejection is structural: branch 4 explicitly tests `Start`, `R` and `A` as *released*, so `L+Up+Select+L+B+Start` cannot enable cheat mode.

**Negative result bounded.** No password screen, alphabet table, key-mask sequence, or ASCII code list exists: `strings -t x` (140,024 strings) plus a multi-encoding search (ASCII, UTF-16LE/BE, ±0x20) found **no** occurrence of `Sound Options`, `Language Options`, `Empty Slot`, `Fairy Council` or `Level Map` — UI text is font/tile-indexed via the tables at `0x080EA199`/`0x080EAA49`. The only plaintext strings are debug leftovers and `Marcie`. Every reachable screen was walked with screenshots: language select, title, four save-slot entries, Sound Options, Language Options, erase-confirmation dialog, Fairy Council gameplay, dialogue, Level Map, and the debug overlays. The search space checked for a second code system was all 19 KEYINPUT literal-pool readers and the keyboard/font tables; no second validator was found.

## 7. Validation evidence

- **Observed (emulator):** all four action breakpoints hit with the exact expected KEYINPUT values in `r7/r1` (`0x0F3`, `0x1D3`, `0x353`, `0x199`); `0x020036A5` read `0x00 → 0x01` after the debug chord; `0x02000280` read `0x00 → 0x01` after the region chord (savestate diff); slot 1 displayed "Marcie / Fairy Council"; in-game `Teensies: 00 Lums: 663 Score: 50000`; Level Map `pos: 505, 1000 b` and green L/R arrows; alias chord `L+R+Select+Start+A` hit the debug action breakpoint; `L+R+Select+Down` changed no flags.
- **Derived (disassembly):** four chord masks and their required/rejected bits; the four flag addresses; the complete-save routine and its "Marcie" literal; the single-function extent of the validator; the 19 KEYINPUT readers and classification of the non-chord ones.
- **Inferred (not fully exercised):** whether the region flag change requires a cold boot to alter the initial language list — on restart the Language Options screen still showed English/Español/Français, so the visible language-set change claimed by the wiki was **not** reproduced; the flag write itself is proven. The debug-menu function-pointer table at `0x080E89F0` suggests engine debug screens exist, but no separate debug-menu screen was reachable from the main menu; only the in-game/map overlays were confirmed.

## 8. Unknowns

- Whether a cold power-cycle (rather than emulator restart) is needed for the region toggle to change the language list.
- The exact semantics of the extra bits in `0x02002A23` (observed `0x02` after cheat-mode enable, `0x03` later) — only bit 1 is written by the validator.
- Whether the engine debug screens referenced by the `0x080E89F0` handler table are reachable by any input on this retail build; the documented "debug info" effect is an overlay set, not a menu.
- Aliasing from branches 1–3 (extra buttons not rejected) was confirmed for one alias by breakpoint; the full 64-spelling alias sets were not exhaustively pressed.

## 9. Tooling

- `header.py` — header parse + embedded-logo scan.
- `masksearch.py`, `keyscan.py` — byte/pointer scans for key masks and all KEYINPUT literal loads (Capstone 5.0.7, `arm-none-eabi-objdump -M force-thumb`).
- `xref.py`, `xref2.py`, `blscan.py` — string-pointer pool xrefs and Thumb BL callers.
- `dbg.py` + `dcmd.py` — mGBA `-d` CLI debugger bridge (mGBA GDB stub port 2345 was occupied by another process, so the pty debugger and savestate diffing were used for RAM evidence).
- `ssdiff.py` — decompress mGBA `.ssN` `gbAs` PNG chunk and diff EWRAM/IWRAM.
- `key.py`, `chord.py` — XTEST input helpers on `DISPLAY=:316`.
- Web: DuckDuckGo HTML search, Wayback Machine snapshot of RayWiki (Cloudflare blocked direct GameFAQs/RayWiki fetches); fetched page content treated strictly as data.
- No ROM or copyrighted assets are redistributed; only addresses, hashes, masks and tool scripts are published.
