# Mat Hoffman's Pro BMX (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mat Hoffman's Pro BMX/Mat Hoffman's Pro BMX.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `MH PRO BMX` |
| Game code | `AHOE52` (USA, revision 00) |
| Maker code | `52` (Activision) |
| Developer (published) | HotGen Studios |
| Header bytes | entry word `0xEA00002E` (stock `b .`), fixed `0x96` at 0xB2, main unit `0x00`, device `0x00`, version `0x00`, complement `0x20`, checksum `0x0000` |
| MD5 | `4f142c9621c9115d7107e7e6f02d99d3` |
| SHA-1 | `df0345c31ca3cad51cef7adae8c6fdadf81b3a97` |
| SHA-256 | `a2779b43120f80a4b6305185c01086655f4b2eec979f88b7d7b53023fce5c05d` |

**Phase 0 — patch/trainer check.** Exactly one Nintendo-logo hit, at file offset `0x4`; there are no embedded/second GBA headers and no appended trainer. The entry word is the stock `0xEA00002E`, and the crt0 at `0x080000C0` is a normal ARM reset handler whose Thumb `main` pointer is `0x080001D9`. This is a clean retail image, not a scene-patched/cracktro build (§16.1). The zero header checksum is the usual rebuilt-header artifact; the complement byte `0x20` is non-zero.

## 2. Executive summary

The GBA release has **no developer-intended password, cheat menu, or working button code that I could confirm in this ROM**. There is exactly one published GBA cheat — 3rd party cheat indexes both list *"Unlock Everything: at the main menu hold L+R and press A, B, Right, Up, Left, Down"* — but it is **not implemented (or is non-functional) in the analysed AHOE52 image**:

* entered on a clean boot at the main menu, with slow and fast timing, the sequence merely navigates the ordinary menus;
* the cover-gated level locks remain in place (e.g. **THE WORKS — "NEED 25 COVERS TO UNLOCK LEVEL"**, **LONDON UNDERGROUND — "NEED 11 COVERS TO UNLOCK LEVEL"**);
* a save made after entering the code is byte-identical to a save made without it (512-byte EEPROM);
* exhaustive literal searches in every plausible key-mask encoding found **no** stored copy of the sequence and no validator table.

The game *does* have an unlockable-progression system (secret "covers" unlock levels; medals are earned per level), but that is ordinary gameplay progression, not a cheat, and its state is driven by the save/career record, not by controller input (§16.18).

What the ROM *does* contain is a generic input-recording/playback subsystem (demo recording), documented below, and a lowercase ASCII text bank that exposes every menu label. All reachable screens were walked and screenshotted; no hidden/debug screen exists (the only debug-looking strings are trick-failure/help leftovers in a separate bank).

## 3. How to reproduce

**Environment.** Xvfb `:316` 1024x768x24, `openbox`, `SDL_AUDIODRIVER=dummy`, mGBA (SDL) at 3x scale, keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Window focused with `xdotool windowfocus`; keys held 100–600 ms (the title screen requires a longer Start hold than the demo screen).

**Boot path.** HotGen splash → demo ("DEMO MODE / PRESS START") → Start (short) → title logo ("PRESS START") → Start (long, ~0.6 s) → MAIN MENU.

**Menu path used for the unlock check.**
```
MAIN MENU
  -> 1P GAMES -> CAREER -> NEW -> SELECT RIDER -> SELECT LEVEL
  -> press Right four times -> THE WORKS -> "NEED 25 COVERS TO UNLOCK LEVEL"
```

**Published code tested (all four entry points).**
1. Main menu, cursor on TRAINING: hold `a`+`s` (L+R), press `x,z,Right,Up,Left,Down` at 200 ms/press; repeat at 50 ms/press.
2. Same sequence on the title screen and on the in-game PAUSE screen.
3. Same sequence with L+R **not** held (control run).
4. Reversed sequence (`Down,Left,Up,Right,B,A`) with L+R held.

Observations for all of the above: normal menu/gameplay navigation, **no unlock**. After (1) the game lands on SELECT RIDER with the last rider highlighted purely because the A/B/arrow presses navigate; the identical screen is reached in (3) without L+R. Starting a new career after (1) still shows THE WORKS locked. Saving under OPTIONS after (1) produced the same EEPROM as saving after (3).

**Screens walked (screenshots retained in `/tmp/mathoffman1/`):** boot splash, demo mode, title screen, MAIN MENU (TRAINING / 1P GAMES / 2P GAMES / OPTIONS), 1 PLAYER GAMES (CAREER / TOURNAMENT / FREE RIDE / TIME TRIAL), CAREER MENU (CONTINUE greyed / NEW / LOAD greyed), SELECT RIDER (all 10 portraits), SELECT LEVEL (cover-gated), OPTIONS (MUSIC / SFX / SAVE / LOAD), SAVE GAME? prompt, 2 PLAYER GAMES ("LOOKING FOR LINK" — link cable required), RULES briefing, gameplay HUD, PAUSED (Continue / Retry / End Run). No other screen is reachable without a link cable or save data.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`; addresses below were verified against the actual bytes.

| Address | Purpose | Evidence |
|---|---|---|
| `0x08000000` | Stock ARM reset vector `0xEA00002E` | derived (header dump) |
| `0x080001D9` | Thumb `main` pointer in crt0 literal pool at `0x080001D0` | derived |
| `0x080063E0` | **Input handler**: reads `0x04000130`, inverts it, computes newly-pressed keys, remaps to an 8-bit custom encoding | derived (disassembly + literal scan) |
| `0x080064B8` | Literal `0x04000130` (KEYINPUT), the only reference in the ROM | derived |
| `0x03003A40` | RAW held keys, active-high (~KEYINPUT & 0xFFFF) | observed (savestate RAM) |
| `0x03003A44` | Newly-pressed keys (read by ~36 call sites, all screen handlers) | observed + derived |
| `0x03003A48` | Encoded key state, 8-bit: `Up=1, Down=2, Left=4, Right=8, A=0x10, B=0x20, L=0x40, R=0x80` | observed (holding L+R+A gave `0xD0`) |
| `0x03000D28`–`0x03000D40` | Demo-record/playback state machine (mode, counter, EWRAM write pointer, last key); buffer at `0x02000000` | derived (0x08006400–0x080066EC) |
| `0x08006640`, `0x08006688`, `0x080066A0`, `0x080066EC` | Record/playback helpers called only by the demo-recorder mode machine | derived |
| `0x0839FCC4`–`0x083A1EB4` | Lowercase ASCII UI text bank (all menu labels) | observed (`strings -t x`) |
| `0x083A4584` | Pointer table of the "need N covers to unlock level" message fragments (`0x83A0248`, `0x83A0250`, `0x83A0274`, `0x83A027C`) | derived (pointer scan) |
| `0x0801B82C`–`0x0801B8B8` | Level-select renderer switch that emits the cover-lock message | derived |
| `0x083A44B0`, `0x083A44FC`, `0x083A4500` | Pointers to "main menu", "select rider", "select level" strings used by screen code | derived |
| `0x083A4EE0`–`0x083A4F30` | Screen-name/string pointer table (contains "title screen", "start screen", "rider select", …) | derived |
| `0x082DC000`–`0x082DCB54` | Debug/help string bank: `MODE TOO HIGH`, `HELP EXTRAS XXXXXXX`, `HELP FAKIE XXXXXX`, `ODD COMMAND`, `CRAP PATTERN FRAME`, `CALL AN AMBULANCE`, … (trick/debug leftovers, not a menu) | observed |
| `0x083A1B4C` | `HGXFP101FLIPPERDIPPERHGX` — developer/build marker in the screen-name table, not a code | observed |

**Savestate RAM layout used (§16.13).** mGBA `.ssN` is a PNG with a zlib `gbAs` chunk; decompressed length `0x61000`. IWRAM `0x03000000` → raw `0x19000`; EWRAM `0x02000000` → raw `0x21000`. Confirmed by reading the encoded-key value `0xD0` at `0x03003A48` while holding L+R+A.

## 5. Algorithm

**Input path (derived).** Once per frame `0x080063E0` reads KEYINPUT, inverts it into `0x03003A40`, computes `newly = current & ~previous` into `0x03003A44`, and maps the eight buttons into a compact mask written to `0x03003A48`:

```
enc = 0
if up    : enc |= 0x01
if down  : enc |= 0x02
if left  : enc |= 0x04
if right : enc |= 0x08
if A     : enc |= 0x10
if B     : enc |= 0x20
if L     : enc |= 0x40
if R     : enc |= 0x80
```

The same routine gates a **demo-record/playback** state machine on `mode = [0x03000D2C]` (0 = idle, 1 = record, 2 = playback). In mode 1 it appends `(frame_counter, key_code)` word pairs to an EWRAM buffer at `0x02000000` and calls `0x08006640` when a counter exceeds `0x13FF`; in mode 2 it consumes the buffer and terminates when a countdown reaches zero. This subsystem records/simulates gameplay demos; it is **not** a cheat validator (no published code bytes appear in it, and no action branch writes an unlock flag).

**Unlock-progression path (derived).** Levels are gated by a "covers" counter in the career record. The level-select renderer at `0x0801B82C` switches on a case value and loads the message fragments through the table at `0x083A4584`; the two observed thresholds are 25 covers (THE WORKS) and 11 covers (LONDON UNDERGROUND). There is no code path from controller input to this counter — its writers are the career/save routines (§16.18).

**Cheat validator:** none found. Pseudocode therefore reduces to:

```
# every screen handler
poll_input()                      # 0x080063E0
if published_button_code_present: # no such test exists in this image
    set_unlock_all()              # no such writer exists
```

## 6. Tables

**Published code (external evidence, not present in ROM):**

| Source | Effect | Code | Entry point |
|---|---|---|---|
| 3rd party cheat indexes (web.archive snapshot 2021-01-17), "Codes / Cheat Codes", contributor Starky27 | Unlock Everything | Hold L+R, press A, B, Right, Up, Left, Down | main menu |
| 3rd party cheat indexes GBA cheats page | "Unlock Everthing" | At the main menu hold L+R and press A, B, Right, Up, Left, Down | main menu |

3rd party cheat index lists exactly **one** GBA cheat for this game. The 35 "cheats" on the 3rd party cheat indexes *Game Boy Color* page belong to a different SKU and were correctly excluded (§16.11). CodeBreaker/GameShark lists (3rd party cheat indexes) are memory-edit codes and are out of scope.

**Key-state tables:** custom 8-bit encoding from `0x080063E0` (Section 5). Raw active-high GBA masks: A=`0x001`, B=`0x002`, Select=`0x004`, Start=`0x008`, Right=`0x010`, Left=`0x020`, Up=`0x040`, Down=`0x080`, R=`0x100`, L=`0x200`; with L+R = `0x300`. Encoded published sequence would be `D0 E0 C8 C1 C4 C2` (each press OR'd with L+R) or `10 20 08 01 04 02` bare.

**Unlockable content observed:** levels with cover thresholds (The Works 25, London Underground 11); medals gold/silver/bronze; 10 selectable riders; "find secret cover" goal text at `0x083A06F0`.

## 6b. Enumeration

**Button-code space searched (all negative).** Encodings derived from the game's own input handler, forward and reverse, with and without the L+R modifier:

| Representation | Patterns tried | Longest matching prefix found | ROM hits for full sequence |
|---|---|---|---|
| Raw active-high u16 LE / u8 / u16 BE / u32 | 30 | 2 presses (coincidental data bytes) | 0 |
| Raw active-low KEYINPUT u16 | 4 | 0 | 0 |
| HotGen 3-bit key indices (A=4,B=5,R=3,U=0,L=2,D=1) as bytes/u16/u32, with L,R prefix | 12 | 0 | 0 |
| HotGen 8-bit encoded masks (`D0 E0 C8 C1 C4 C2`, bare `10 20 08 01 04 02`) | 10 | 2 presses | 0 |
| 3-bit packed (18- and 24-bit) little/big endian | 8 | 0 | 0 |
| Inline Thumb `cmp rN,#imm` chains over the sequence values | 8 register variants + any-register regex | 0 | 0 |

Counts: for every representation the 3-press prefix occurs **0 times** in the 4 MiB image; the only 2-press hits are coincidental ASCII/graphics bytes. This bounds the negative to "no literal sequence table or immediate-comparison chain of the published code exists in this ROM".

**Undocumented combinations pressed in the emulator (bounds proven by rejection).**

| Input at main menu | Result |
|---|---|
| Published sequence with L+R held (200 ms/press, fresh boot) | No unlock; THE WORKS still "NEED 25 COVERS"; level select normal |
| Published sequence with L+R held (50 ms/press) | Same — no unlock |
| Reversed sequence with L+R held | No unlock; only normal menu navigation |
| Sequence without L+R | Identical screen and identical EEPROM save to the L+R run — L+R changes nothing |
| L+R + A only | Simply selects TRAINING (rider select); no hidden screen |
| Code on title screen / on PAUSE screen | No unlock; only normal navigation |

**Novel-code requirement (§0.2, button-code equivalent).** There is no code *generator* to mint an unpublished value from, so the equivalent deliverable is an undocumented combination that the game rejects: the reversed sequence, the no-modifier sequence, and the L+R+A-only input were all entered on the real screen and all failed to unlock anything. The accepted set exercised in-game is therefore the ordinary menu actions only; the published "unlock everything" claim is rejected by this ROM revision.

**Universe of hidden screens.** Every screen reachable without a link cable or save data was visited (Section 3). The screen-name table at `0x083A4EE0` enumerates the engine's screens (title, start, single/career/multi start, rider select, location select, start screen, etc.); none is an undocumented debug menu, and the only `debug`-flavoured strings are the trick-help leftovers at `0x082DC000`–`0x082DCB54`, which have no menu entry.

**Text/button-space search counts.** `strings -t x -n 4` produced 33,538 lines; a second pass at `-n 2` covered short labels. Case-insensitive keyword scan for `password|cheat|debug|secret|unlock|rider|hidden|menu|code` returned five relevant hits: `HELP EXTRAS XXXXXXX` (0x2DCA94), `unlock` (0x3A0274), `> find secret cover` (0x3A06F0), `rider select` (0x3A1E14), and the UI text-bank labels. No password prompt, no "enter code" screen, no level-select cheat screen. No `strings` hit for the published button names in any encoding.

## 7. Validation evidence

* **Observed:** clean retail header (one logo, stock entry word); every screen in Section 3; level locks with their exact thresholds; all six code-entry experiments and their negative outcomes; EEPROM save identical with/without code; encoded key `0xD0` while holding L+R+A.
* **Derived:** input handler at `0x080063E0` and its 8-bit key encoding; demo record/playback state machine at `0x080063E0`–`0x080066EC`; text bank, screen-name table, unlock-message table and renderer; absence of any literal or immediate-coded published sequence in exhaustive encoding searches.
* **Inferred:** the published 3rd party cheat index code is erroneous, or belongs to a different revision/region/platform build whose sequence detector was removed from AHOE52. This is the most economical explanation of "published claim + zero ROM trace + zero in-game effect", but I did not test another regional ROM, so it is labelled inferred rather than derived.

No prompt-injection content was encountered in the fetched 3rd party cheat indexes/DuckDuckGo pages; fetched text was treated as data.

## 8. Unknowns

* Whether a non-USA revision of the game implements the published code (only AHOE52 was available).
* Whether a link-cable multi-player mode exposes any hidden menu (untestable headless without a second console/link).
* Whether career-progression "covers" can be advanced by any shortcut other than normal gameplay; no controller-driven writer was found.
* The exact `mode` values that start demo record/playback were not exercised in-game (the state machine is derived from disassembly only).

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep` — Phase 0/1 fingerprinting.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` and Capstone 5.0.7 Python scripts — literal-pool, BL-target, and key-mask scans; validator search.
* Python custom scanners: PC-relative LDR literal resolver, Thumb BL scanner, multi-encoding button-sequence searcher.
* mGBA (SDL) under Xvfb `:316` + openbox, `xdotool` XTEST key injection, `scrot` + ImageMagick crop — screen walk and screenshots.
* mGBA savestates: Python PNG/`gbAs` zlib decoder plus raw-RAM differencing (IWRAM at raw `0x19000`, EWRAM at raw `0x21000`) — RAM evidence and with/without-code comparison.
* mGBA CLI debugger (`-d`) over a Python PTY driver and GDB stub experiments were attempted; neither yielded reliable watchpoint output, so conclusions rest on static disassembly plus savestate RAM diffs and screenshots.
* Web: web.archive.org snapshot of the 3rd party cheat indexes GBA cheats page, 3rd party cheat indexes, DuckDuckGo/Bing result pages.

**Legal note:** no ROM bytes or copyrighted assets are reproduced in this report; only hashes, addresses, and findings are published.
