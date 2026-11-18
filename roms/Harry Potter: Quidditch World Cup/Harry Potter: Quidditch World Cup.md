# Harry Potter: Quidditch World Cup (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Harry Potter: Quidditch World Cup.gba` |
| Size | 8,388,608 bytes (0x00800000, 8 MiB) |
| `file` | Game Boy Advance ROM image: "QUIDDITCH WC" (BHPE69, Rev.00) |
| Header title (0xA0) | `QUIDDITCH WC` |
| Game code (0xAC) | `BHPE` |
| Maker code (0xB0) | `69` |
| Version (0xBC) | 0x00 |
| Fixed byte (0xB2) | 0x96 |
| Complement (0xBD) | 0x6A |
| Header checksum (0xBE) | 0x0000 |
| Entry word | 0xEA000030 → entry 0x080000C8 (normal commercial crt0) |
| MD5 | `211f243e032b967e01ff97907b29f56a` |
| SHA-1 | `7b7835b655f34efec44ed090821257d5e1378275` |
| SHA-256 | `6bfe1697ddf12438ea53fea2927c4927253f1d924a2ce3c81829bb134c5315e9` |
| Build tag @ 0x08060F38C | `HARRY POTTER\x01\x01Sep 10 2003  14:53:30` → US/Europe build (matches TCRF) |
| Developer / publisher | Magic Pockets / Electronic Arts (build strings + TCRF) |

Phase 0 findings:

* **Embedded-header scan**: the 156-byte Nintendo logo occurs exactly once, at file 0x04. There is **one** GBA header; no multiboot stub, no second game, no appended trainer. The file size is an exact power of two with no tail padding.
* **No scene cracktro / trainer**: entry word is a plain `b 0xC8` into a normal crt0; no Mode7/"CRC BANDIT"/SUNHORS signature, and no added menu. The zero header checksum and non-canonical complement byte (standard formula would give 0x82, not 0x6A) are header-record oddities, not evidence of a patch — the code and logo are intact and the build tag is consistent.
* **Other Harry Potter GBA images in the set** (fingerprinted independently): Goblet of Fire (32 MiB, `BH8E`, md5 `d228b8cf…`), Prisoner of Azkaban (16 MiB, `BHTE`, md5 `3fe499f2…`), Sorcerer's Stone (8 MiB, `AHRE`, md5 `4eaac54b…`). All four carry maker code `69` and three use a `B…E` game code — a shared publisher/engine family, **not** the same game. Literal sharing is limited to the Shin'en GAX audio banner `Code: B.Wodok` (present in QWC and Goblet of Fire) and the generic demo string `PRESS ANY KEY TO CONTINUE` (QWC and Goblet of Fire). No password, button-code or debug-table string is shared with any other HP image. Each image has distinct hashes, titles, sizes and code; addresses from sibling games must not be carried over (guide §16.11).

## 2. Executive summary

**There is no in-game password, button-code, or reachable cheat system in this image.** Every "cheat" published for this GBA SKU is a CodeBreaker/GameShark *memory patch* (e.g. `33003B57 0000`, `83003B34 3600`, `43004050 FFFF …`) — explicitly out of scope — and none of those literals is a password the game compares. There is no password-entry screen anywhere in the game. The only developer-intended progression mechanisms are ordinary save-file unlockables (Quidditch Cards, 105 total, gating teams/brooms/stadiums), which are gameplay rewards, not codes.

**However, the ROM contains a complete, fully translated developer debug menu in its text bank**, including `Debug Menu`, `Free Cam`, `Team Moves`, `Cut Scenes`, `Seeker View`, plus submenus of 15 team moves and 11 cut scenes. It was recovered by decoding the game's tokenised ROM text bank through its runtime-expanded copy in EWRAM (§4). All menu strings exist in English, German, French, Danish, Spanish and Italian banks. In the retail build this screen has **no reachable activation path that could be found**: it is not an Options item, is not reached by scrolling past the end of any menu ring, and none of the button combinations tested at the title, main-menu Options, cards, pause or in-game screens opened it. It is therefore reported as a **present-but-unactivated debug feature (gated/dead)**, with the exact activation status recorded as an Unknown in §8 rather than claimed as proven absent.

## 3. How to reproduce

* Emulator: mGBA 0.10 (`/usr/local/bin/mgba`, SDL), Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `-3` scale, 720×480 window captured with `scrot -o` + `convert … -crop 720x480+154+184 +repage`.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. **Hold keys 60–150 ms**: 150–200 ms double-steps menu cursors; 60–80 ms moves one slot; <60 ms can be missed (guide §16.2).
* Boot path: license screen → language select (9 languages) → Saved Data (4 slots + Erase Data) → choose a slot → intro/house dialogue → Hogwarts training challenge → Start opens Pause Menu.
* Menus reached and verified on screen: language select; Saved Data; house choice; Hogwarts training; **Pause Menu** (`Continue / Options / Restart / Quit`, plus `Are you sure? / Yes / No`); **pause Options** (`Sfx : On`, `Sleep Mode` — a 2-item ring); **main menu** (`Go to Hogwarts`, `Exhibition Match` locked, `World Cup` locked, `Quidditch Cards`, `Options`); **main Options** (`Music: On`, `Sfx: On`, `Brightness: Normal`, `Credits`, `Sleep Mode` — a 5-item ring, no 6th entry); **Quidditch Cards** menu (`View Quidditch Cards`, `Trade Cards`) and the 105-slot card grid; **Sleep Mode** screen (`To exit Sleep Mode, press SELECT + L + R at the same time`).
* Codes tested: none applicable — no password UI exists. Published CodeBreaker/GameShark patches were checked against the ROM and rejected as out-of-scope memory edits (their addresses are RAM patch targets, not ROM literals).
* Button-combination probes (held simultaneously, with EWRAM reads before/after): at Saved Data title — L, R, L+R, L+R+A, L+R+B, L+R+Start, L+R+Select, L+R+Up, L+R+Down (EWRAM delta **0 bytes** for all); at main Options — L+R, L+R+Start, L+R+Select, L+R+A+B, L+R+L+R+Up+Down, Up+Up+Down+Down; at title — 8 longer sequences including Konami-style Up Up Down Down Left Right Left Right and L L R R Up Down Up Down; at the card grid — R, L, Select, Start, B. None produced the debug menu. Only observable effects were menu-cursor movement, the Save/Erase confirmation, gameplay entry, and the documented Sleep Mode screen (L+R+Select).
* Oracle/debug harness: because port 2345 was occupied by another session's mGBA, a 14-line `LD_PRELOAD` shim (`/tmp/opencode/hpqwc/portshift.c`) rewrote `bind(2345)`→`bind(2346)`, giving an exclusive GDB stub; RSP reads/writes/breakpoints/watchpoints were issued from a small Python client (`rsp.py`, `dbg.py`).

## 4. Address map

| Item | ROM / file offset | Runtime address | Evidence |
|---|---|---|---|
| GBA header | file 0x000 | 0x08000000 | Observed (xxd) |
| Build tag | file 0x60F38C | 0x0860F38C | Observed (TCRF cross-check) |
| Unused demo text | file 0x60F3D1 | 0x0860F3D1 | Observed |
| `* Engine by www.MagicPockets.com*` padding | file 0x7AF818 | 0x087AF818 | Observed |
| Shin'en GAX banner `Code: B.Wodok` | file 0x7AE89E | 0x087AE89E | Observed — audio engine banner, **not** a code (guide §16.11) |
| Tokenised text bank (English) | file 0x1800–0x18CF | source for EWRAM bank | Observed |
| Expanded text bank (English) | — | EWRAM 0x02000B80 (table) / 0x02000BA0+ (strings) | Observed via GDB and savestate `gbAs` chunk |
| `Pause Menu` / `Continue` / `Quit` / `Options` / `Restart` | ROM bank 0x0800181A… (compressed) | 0x02000BA1 / BAD / BB7 / BBD / BC6 | Derived (decoded bank) |
| `Music` / `Sfx` / `Sleep Mode` / `On` / `Off` | compressed bank | 0x02000C28 / C2F / C34 / C40 / C44 | Derived |
| **`Debug Menu` / `Free Cam` / `Team Moves` / `Cut Scenes` / `Seeker View`** | compressed ROM bank 0x08001870… (`DebugFCevCucSker View`) | 0x02000C4A / C56 / C60 / C6C / C78 | Derived + decoded |
| Team-move submenu (15 strings) | — | 0x02000C84–0x02000D4F | Derived |
| Cut-scene submenu (11 strings) | — | 0x02000D57–0x02000DE0 | Derived |
| Input handler (KEYINPUT → edge/held) | 0x085E0834 | — | Derived (`objdump -M force-thumb`) |
| `KEYINPUT` literal | 0x085E089C | I/O 0x04000130 | Derived |
| `pressed` (edge) global | literal 0x085E08A0 | IWRAM 0x030017AC | Derived + GDB |
| `released` global | literal 0x085E08A8 | IWRAM 0x0300179C | Derived + GDB |
| `held` global | literal 0x085E08A4 | IWRAM 0x0300214C | Derived + GDB |
| Flag word | literal 0x085E08AC | IWRAM 0x03001550 | Derived + GDB (live value 0x00048087) |
| Sleep-mode byte | literal 0x085E08B0 | IWRAM 0x03001790 | Derived + GDB (live value 0x55) |
| Sleep-mode gate (`held == L\|R\|Select`) | 0x085E0878–0x085E08C2 | — | Derived |

### Text-bank decoding (font/token bank)

The ROM stores UI text as a compressed bank: entries carry a `0x04` prefix, but words are abbreviated (`Continue`→`Contie`, `Options`→`Ops`, `Debug Menu`→`Debug`, `Free Cam`→`FC`, `Cut Scenes`→`Cuc`, `Seeker View`→`Sker View`). At boot the game expands it into EWRAM as `04 <NUL-terminated ASCII>` records. Decoding the **runtime** copy (via the savestate `gbAs` chunk and confirmed live with GDB) yields the complete strings; `strings` on the ROM alone finds only fragments (guide §11 / §16 "not all text is ASCII").

Recovered debug-menu item list (indices as stored in the expanded bank):

```
16 Debug Menu      17 Free Cam       18 Team Moves     19 Cut Scenes     20 Seeker View
21 Team Move GRY   22 Team Move SLY  23 Team Move HUF  24 Team Move RAV  25 Team Move JAP
26 Team Move GER   27 Others         28 Team Move NOR  29 Team Move USA  30 Team Move ENG
31 Team Move AUS   32 Team Move FRA  33 Team Move BUL  34 Others         35 Team Move SPA
36 C. S. Win       37 C. S. Lose     38 C. S. Start    39 C. S. Win Hog  40 C. S. Win World
41 C. S. Broom     42 Others         43 C.S. Door      44 C.S. Tower     45 C.S. Balls
46 C.S. Win All    47 Press $
```

The same 31-string block is present in the German (file 0x4E61E), French (0x55CDC), Danish (0x4C09A) and other language banks — this is a shipped, localised debug feature, not an accidental stray string.

### Input model (derived, verified live)

Active-high key mask from `~KEYINPUT & 0x3FF`: `A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010 Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200`.

```
pressed = held_now & ~held_prev      -> 0x030017AC   (edge)
released= (held_now ^ held_prev) & held_prev -> 0x0300179C
held    = held_now                  -> 0x0300214C
if (held & 0x00F) == 0x00F: call 0x086082DC(0xFF)   ; all four D-pad dirs -> BIOS svc, not a cheat
if (flags@0x03001550 & 0x10000) && (byte@0x03001790 == 0x55):
    if ((held & 0x3FF) == 0x304):                    ; L + R + Select
        flags |= 0x20000
if (flags & 0x20000): call 0x085E06F0; flags &= ~0x20000   ; documented Sleep Mode entry
```

Measured live at the pause screen: `0x03001550 = 0x00048087` (bit 0x10000 **clear**), `0x03001790 = 0x55`. The only button gate found in the input handler is the documented Sleep Mode exit; no debug flag write was found in it.

## 5. Algorithm

No password/checksum/button sequence algorithm exists. The only algorithmic content found is:

1. **Text expansion** (boot): tokenised ROM bank → NUL-separated `04`-prefixed ASCII records in EWRAM; decoding rule recovered by direct comparison of ROM 0x08001818 and EWRAM 0x02000BA0 (§4).
2. **Input edge detection** (0x085E0834): pseudocode in §4. All key-state globals were read live with GDB and matched the disassembly.

## 6. Tables

* **Published cheat data**: GameFAQs (archived 2023, `gba/914744…/cheats`), ROMSFUN (11 "cheats"), Cheat Happens, TCRF. Every entry is a CodeBreaker/GameShark RAM patch (e.g. `33003B57 0000`, `83003B34 3600`, `33003A85 00FF`, `83004022 FFFF`) or a platform-specific unlockable; **none is a password or button code**, and none was found as a literal in the ROM. Verified as out of scope.
* **Unlockables (developer-intended, in scope as game design)**: 105 Quidditch Cards earned through matches/challenges; card thresholds unlock brooms (Nimbus 2000/2001, Firebolt), teams (Bulgaria at 65 cards) and stadiums/World Cup. These are earned save-data bits, not codes; collected count observed as `0/105` on the HUD.
* **Button masks**: table in §4.
* **Debug-menu strings**: table in §4 — 4 top-level entries + 26 submenu entries, enumerated exhaustively.

## 6b. Enumeration

**Code space**: none — there is no password alphabet, no checksum, no key-mask sequence table, and no passphrase entry screen in any of the 9 screens walked. Therefore the §0.2 "mint a novel code, enter it, prove bounds by rejection" deliverable is **not applicable**; the required negative result is instead a bounded search, given here.

**TextBox / button-space search with counts**:

| Search | Space examined | Result |
|---|---|---|
| `strings -t x -n 4` whole ROM | 8,388,608 bytes; 144,379 lines | 0 in-game password prompts; keyword hits classified: "Debug" (14 language banks), `Debug Menu`-style tokens, `INITLEVEL: NO LEVEL` @ file 0x7ADAA8, `Game paused` @ 0x7ADAC1, `Code: B.Wodok` @ 0x7AE89E (audio banner, false positive), "secret/unlock/cheat" only in unlockable descriptions |
| Tokenised text bank fully decoded from EWRAM | 48 strings (indices 0–47) in the pause/options bank, plus further banks | 1 debug menu header + 4 top-level actions + 26 submenu labels; no password entry label, no "Enter Code", no cheat menu label |
| 32-bit literal scan for RAM text-bank pointers | whole ROM, 4-byte aligned | 3 hits (0x08118988, 0x08356BB4, 0x085A69B4), all in compressed data — no menu table of direct string pointers |
| u16/u8 string-ID table scan for `[0x10..0x14]` | whole ROM | matches only in generic sequential ID/font tables (0x0804AD39, 0x08064746, 0x08219AE0, 0x0824B6F1, 0x0825C691) and one compressed-data false positive (0x083B4E8C); no menu definition table containing the debug-menu IDs |
| Button-mask table scan (`u16` runs of 1–2 bit masks, length ≥4) | whole ROM, 2-byte steps | 604 runs; all are compressed graphics/sound data runs of a repeated mask (0x87A…–0x87AD…) or BIOS stubs — **no button-code table** |
| Button-combination probes | title (9 combos incl. L/R variants), main Options (6), cards (5), pause/in-game (3) | no debug screen; RAM EWRAM delta = 0 for all title L/R combos |
| Menu-ring enumeration | pause Options (2 slots), main Options (5 slots) | wrapped to slot 0 with no hidden 6th entry |
| Published-code verification | GameFAQs/ROMFUN/TCRF/CheatHappens | all codes are out-of-scope memory patches; 0 password strings, 0 button sequences |

**Novel code minting**: impossible by design — no validator to invert. **Bounds by rejection**: the only in-game input gate discovered (L+R+Select) was exercised and produced the documented Sleep Mode screen, not a debug screen; all other tested combinations were rejected by the UI (no state change, EWRAM delta 0). The debug menu's own bounds are fully enumerated above (4 top-level + 26 submenu labels), so if a future build exposes it the complete item set is known in advance.

## 7. Validation evidence

* **Observed**: header bytes, hashes, file identity and build tag; all 9 screens via screenshots; menu ring sizes and item labels; `0/105` card count; EWRAM text bank decoded at raw 0x21BA0 of the `gbAs` savestate chunk and cross-checked live at 0x02000BA0 with GDB; live globals `0x03001550=0x00048087`, `0x03001790=0x55`, `0x0300214C=0xFC00`; EWRAM delta 0 for title L/R probes; Sleep Mode screen after L+R+Select.
* **Derived**: Thumb disassembly of 0x085E0834 input handler and its literal pool; active-high key mask mapping; edge/held variable addresses; the L+R+Select condition; tokenised→expanded text-bank transformation; debug-menu string set and submenu inventory; unchanged entry word/logo proving no trainer.
* **Inferred**: that the debug menu is unreachable in the retail build — supported by exhaustive screen/combination probing and static searches, **not** by a proof that no code path can ever set its screen state. The activation gate, if one exists, was not located. The exact effects of each debug action (Free Cam etc.) were never observed on screen and are not claimed.

## 8. Unknowns

* The activation path for the localised debug menu (if any) was not found. It is not a menu item, not reachable by over-scrolling, and not triggered by the tested combinations. A save-bit, card threshold, link/cable event, or a code path not covered by the static scans could still gate it. This is a **gated/dead-feature** question (guide §16.3), not a "no system" conclusion for the debug text itself.
* Whether the compressed text bank's token expansion has alias collisions exploitable only by RAM editing — not investigated (out of scope).
* Effects of the 4 debug actions and 26 submenu labels: not observed.
* Header checksum/complement anomaly: recorded but not explained; no functional effect observed.
* No prompt-injection content was encountered in fetched web pages (TCRF via web.archive.org, GameFAQs via web.archive.org, ROMSFUN, Cheat Happens). All fetched text was treated as data. The `Code: B.Wodok` ROM string is an audio-engine banner, not an instruction.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo` — fingerprinting/recon.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` — Thumb disassembly.
* Python 3 + `capstone` 5.0.7 — literal/BL/pattern scans (input globals, button masks, string IDs).
* mGBA 0.10 under Xvfb `:317` + openbox; `xdotool` XTEST input (60–150 ms holds); `scrot` + ImageMagick `convert` for 720×480 viewport crops; `tesseract` available (not needed).
* Custom tooling in `/tmp/opencode/hpqwc/`: `gba.py` (input/screenshot helper), `portshift.c` → `portshift.so` (`LD_PRELOAD` bind 2345→2346 for an exclusive GDB stub), `rsp.py` / `dbg.py` (GDB RSP client), `watchprobe.py` (watchpoint probes), `savestate` `gbAs` zlib parser.
* Savestates used as evidence sources: `state1.ss1` (pause Options), `titledata.ss2` (Saved Data title), `mainmenu.ss4` (main menu).
* No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms and the author's own tools are published.
