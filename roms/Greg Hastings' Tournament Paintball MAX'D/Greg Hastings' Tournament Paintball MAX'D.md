# Greg Hastings' Tournament Paintball MAX'D (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Greg Hastings' Tournament Paintball MAX'D.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| Header title | `GHTP MAXD` |
| Game code | `BGQE` (`file(1)` reports `BGQE52, Rev.00`; maker `52`) |
| Software version | 0 |
| Entry word | `0xEA00002E` — stock `b 0x080000C0` (no cracktro/patch) |
| Header checksum / complement | `0x0000` / `0x4E` (0x0000 is the usual rebuilt-header artifact) |
| MD5 | `86dca228afc2d455e958c4e52787d91e` |
| SHA-1 | `7f80cb2a3fa2c7fe2a7a1f9a7532eec7f72a682d` |
| SHA-256 | `10c3c34fc8b02a4c536bf2ca26e3057f4438a56ae7743a35b4facbe6ec084fa9` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly **once** (file offset `0x4`), so this is a single image, not a multi-game pack. No occurrences of `GAMESHARK`, `CODEBREAKER`, `TRAINER`, `CRC BANDIT`, `MODE7`, `SUNHORS`, or similar patch/trainer signatures. No battery-patch header. Save type is 8 KiB (SRAM/Flash), magic `AB 25 AB 25` (`0x25AB25AB`) at save offsets `0x10` and `0x1018`.

**Revision caveat:** all addresses below are for this exact hash. Published GBA codes are catalogued under serial `AGB-BGOE-USA` (CRC32 `649F7BB2`); this image carries code `BGQE`. The CodeBreaker codes are memory patches and were not assumed to transfer.

## 2. Executive summary

**This GBA SKU has no in-game/developer-intended cheat system.** There is no password screen, no text-entry surface, no button-code sequence table, no debug/hidden menu, and no cheat mode or cheat unlockable. The game's complete UI text bank (125 strings at `0x08010280`–`0x08010AC0`) contains **zero** occurrences of `password`, `cheat`, `code`, `debug`, `secret`, `unlock`, `god mode`, `slow motion`, `my character`, or `bonus` in ASCII, lower-case, or UTF-16LE/BE. There is no tile-indexed text bank with hidden strings: all rendered text is plain NUL-terminated ASCII copied into EWRAM at `0x0200BB4` (observed per screen). The rest of the 16 MiB is compressed graphics/audio plus standard C-library strings, not text.

The input subsystem was fully enumerated statically: the joypad reader at `0x08004040` produces a 10-bit active-high `held` word at `0x030016D4` and an edge word at `0x030016D8`. Across the entire ROM there are only **8** literal references to the held word and **9** to the edge word, resolving to **11 reader call sites**. None implements a cheat sequence: they are menu navigation (Start/B/Up/Down repeat), a Left+Right character-toggle at the character-select screen (`0x08002A46`), and the standard `A+B+Select+Start` soft reset (`0x08008C2`/`0x0800918`). Twelve classic button sequences were also pressed on the title screen with no effect.

The console (PS2/Xbox) versions' advertised cheats — the password `My Character` + L2, and the `My Character`→White-button God Mode / Slow Motion / Extra Logos toggles — are **absent** from this GBA image: `My Character` has 0 literal hits in any encoding, there is no L2 button, no password screen, and no "My Character" menu or bonus screen. GameFAQs lists no GBA cheats; all published GBA "codes" are CodeBreaker/GameShark memory patches (Access All Modes, Unlimited Ammo, Unlimited Bawls, Rapid Fire, Have All Trophies, Invincible), which are explicitly out of scope per the engagement rules and are external patch codes, not ROM content.

The only unlockable-like state is normal progression: three tournament trophies (Rookie/Amateur/Pro → Bronze/Silver/Gold) shown in the Trophy Room and stored in the save record. This is a save-bit progression feature, not a cheat.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (SDL), `SDL_AUDIODRIVER=dummy`, `Xvfb :319`, `openbox`, 3× scale.
* Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.
* RAM read method: mGBA savestates are PNGs with a zlib-compressed `gbAs` chunk; decompress to a 397,312-byte state. Physical `0x03000000` maps to state offset `0x19000`, so `0x030015EC` is state offset `0x1A5EC`. mGBA's `-d` CLI debugger under a pty was also used for static input-handler verification.
* Menu path (screen-state byte `0x030015EC` in parentheses):

  ```
  Boot logos -> Title 0x0E ("Press START")
    -> Main Menu 0x00
       - New Game -> Character select 0x0F -> Mode select 0x04
           - Free Play -> Difficulty 0x05 -> Gameplay 0x11
               -> on round end: Results (still 0x11; EWRAM text
                  "Free Play Results" / "You lost!") -> A returns to Difficulty
           - Tournament Mode -> Tournament select 0x06 (Rookie/Amateur/Pro)
               -> Tournament Menu 0x07 (Play/Save/Exit)
                   -> Play -> Pre-match 0x12 -> Gameplay 0x10/0x11
                   -> Save -> Save Game? 0x02 -> Slot select 0x13
                             -> Overwrite Slot? 0x08 -> Save successful 0x15
       - Load Game 0x01 (disabled until a save exists; slot select once saved)
       - Reset Game -> Reset Game? 0x03
       - Trophy Room 0x0C (Rookie -> Amateur -> Pro -> back)
       - Options 0x0D (Sound effects ON/OFF, Music ON/OFF)
       - Credits 0x14
    In gameplay: Start -> Pause Menu 0x0A (Return to Game / Quit)
                 -> Quit? 0x09 (Yes/No)
  ```
* Codes tested: none exist to enter; the console password and all published GBA codes were checked against the ROM/UI as described in §6b.

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x08000000` | ROM | Stock entry branch `0xEA00002E` |
| `0x08004040` | function | Joypad reader: `held = ~KEYINPUT & 0x3FF`; `pressed = held & ~prev` |
| `0x08004060` | literal | `0x04000130` (KEYINPUT), the only such literal in the ROM |
| `0x030016D4` | IWRAM word | `held` (active-high 10-bit mask) |
| `0x030016D8` | IWRAM word | `pressed` (newly-pressed edge mask) |
| `0x08002A46` | code | Left+Right (`0x30`) + screen==15 → toggles `0x03001608` (Keely/Greg character index) |
| `0x0801F92` | code | Start (`0x08`) + screen==14 → menu advance |
| `0x08024A4` / `0x0802614` / `0x0802830` | code | B (`0x02`) / Up (`0x40`) / Down (`0x80`) menu handlers |
| `0x08008C2` / `0x0800918` | code | `held & 0x0F == 0x0F` (A+B+Select+Start) → soft reset / legal screen |
| `0x030015EC` | IWRAM byte | Screen-state ID (table in §6) |
| `0x0200BB4` | EWRAM | Live text buffer: the current screen's strings copied from the UI bank |
| `0x08010280`–`0x08010AC0` | ROM | Complete ASCII UI text bank (125 strings) |
| `0x08010AA4` / `0x08010AB4` | ROM | `"Keely Watson"` / `"Greg Hastings"` character names |
| SRAM `0x10`, `0x1018` | save | Magic `0x25AB25AB`; 0x1000-strided records |

File offset ↔ ROM address: `0x08000000 + file_offset`. Savestate offset ↔ physical RAM: `0x19000 + (addr − 0x03000000)`.

## 5. Algorithm

There is no password validator, checksum, code table, or generator to reimplement. The only algorithmic content relevant to the cheat question is the input path, fully recovered from `0x08004040`:

```c
// called once per frame
uint16_t cur = *(volatile uint16_t*)0x04000130;  // KEYINPUT, active-low
uint16_t held = cur ^ 0x03FF;                     // active high: A=1,B=2,Sel=4,Start=8,
                                                 // R=0x10,L=0x20,U=0x40,D=0x80,Rtrig=0x100,Ltrig=0x200
uint16_t pressed = held & ~prev;                 // edge detect
*(uint16_t*)0x030016D8 = pressed;
*(uint16_t*)0x030016D4 = held;
prev = held;
```

Every consumer of `pressed`/`held` was located and disassembled (11 call sites). The complete decision set is: menu cursor movement, a 2-frame auto-repeat counter (`0x0300160C`), the Left+Right character toggle, and the four-face-button soft reset. No sequence history buffer, no password buffer, no comparison table, and no flag setter for a cheat exists.

## 6. Tables

**Screen-state IDs (`0x030015EC`), all observed in RAM:**

| ID | Screen | ID | Screen |
|---|---|---|---|
| 0x00 | Main Menu | 0x0E | Title |
| 0x01 | Load Game | 0x0F | Character select |
| 0x02 | Save Game? confirm | 0x10 | Gameplay countdown |
| 0x03 | Reset Game? confirm | 0x11 | Gameplay active / Results (EWRAM text distinguishes) |
| 0x04 | Mode select | 0x12 | Pre-match info |
| 0x05 | Difficulty select | 0x13 | Save slot select |
| 0x06 | Tournament select | 0x14 | Credits |
| 0x07 | Tournament Menu | 0x15 | Save successful |
| 0x08 | Overwrite Slot? confirm | | |
| 0x09 | Quit? confirm | | |
| 0x0A | Pause Menu | | |
| 0x0C | Trophy Room | | |
| 0x0D | Options | | |

(0x0B was not reached; see §8.)

**Button combos tested (Observed):** Left+Right at character select toggles the selected character (Greg↔Keely, hidden flag `0x03001608` 0→1, `0x03001698` 0→1) — this is selection, not a cheat; A+B+Select+Start at any time shows the legal/copyright screen and soft-resets to the ESRB screen/title — a standard system reset, not a cheat.

**Published codes checked (all out of scope, none are ROM content):**

| Source | Codes | ROM verification |
|---|---|---|
| almarsguides / gamehacking.org (GBA) | Master `90F66381 7339 …`; Access All Modes `F4EFAAA7 BBEA`; Unlimited Ammo `1F005559 4697`; Unlimited Bawls `265D785F 81F2`; Rapid Fire `2A348C53 7089`; All Trophies `B7557A56 F03A …`; Invincible `A2741852 0069 …` | CodeBreaker/GameShark encrypted patch codes. Not ASCII/text; no corresponding in-game entry surface. Explicitly excluded by scope. |
| GameFAQs/GameSpot (PS2/Xbox) | Password `My Character` + L2 → God Mode / Slow Motion / Extra Logos; `My Character` → White button | 0 literal hits for `My Character` in ASCII/case/UTF-16; no password screen or My Character menu on GBA. Different SKU/engine. |
| TCRF | — | HTTP 403; no GBA-specific secrets found via mirrors/search. |

**Save/unlockables:** only trophy progression (Rookie/Amateur/Pro → No trophy/Bronze/Silver/Gold). No cheat flags, no hidden characters/teams/modes beyond the two selectable characters and three tournaments.

## 6b. Enumeration

**Space definition.** The cheat-code space for this SKU is empty: no alphabet, no length, no checksum, no lookup table, and no text-entry surface exists (§2, §7). The *button-input* space was nevertheless enumerated exhaustively:

* The active-high key space is 10 bits (1,024 masks). `pressed` and `held` are the only two key-state words in the game (8 + 9 literal references ROM-wide).
* Every reader of those words was disassembled: **11 call sites**, itemised in §4/§5. Their branch conditions cover exactly the masks `0x08` (Start), `0x02` (B), `0x40` (Up), `0x80` (Down), `0x30` (Left+Right), and `0x0F` (A+B+Select+Start). There is no other mask-test branch, so no unadvertised button sequence can exist.
* **12 sequences** were entered on the title screen in the emulator (Konami `UUDDLRLRBA`, `UUDDLR`, `lrlr`, `l,r held`, `ABAB`, `L+R+Start`, `Select+Start`, `UUDD`, `BBBA`, `lrUDlr`, `L+A`, `R+B`) and on menu/gameplay screens; none opened a hidden screen. Screens were verified by the `0x030015EC` state byte and EWRAM text buffer, not by the attract animation.
* **Published codes tested:** the console password is inapplicable (0 ROM hits, no screen); the GBA codes are external memory patches (out of scope). No in-game code was found because no code system exists.

**Novel codes.** Not applicable — there is no system from which to mint a code. Per §0.2 the deliverable here is the *proven bounded negative*: every reachable screen was walked with RAM evidence, the complete text bank was searched (125 strings, 0 cheat keywords in 3 encodings × 12 keywords), the entire key-state reader set was enumerated (11/11 call sites), and every published code was checked.

**Bounds proven by rejection.** Out-of-space inputs were tested: arbitrary 4–10 key sequences on the title screen were ignored (state stayed `0x0E`); the only state changes observed were the expected Start/A advances into the menus. No acceptance path exists to bound further.

## 7. Validation evidence

* **Observed** — emulator screenshots and savestate RAM reads for all reachable screens (title, main, char select, mode, difficulty, gameplay, Results, pause, quit confirm, options, trophy room, credits, tournament select, tournament menu, pre-match, save confirm, slot select, overwrite confirm, save successful, load game, reset confirm); `0x030015EC` values in §6; text buffers at `0x0200BB4`; Results screen showing `Free Play Results / You lost!`; hidden flag `0x03001608` 0→1 on Left+Right; legal/ESRB screen on A+B+Select+Start; save creation producing `Save was successful!` and enabling Load Game; 12 title-screen combos with no hidden state.
* **Derived** — input routine `0x08004040` and all 11 key-state reader call sites disassembled with `arm-none-eabi-objdump -M force-thumb`; literal pools decoded with `struct.unpack_from`; no cheat sequence/gate present in the closed reader set. Complete text bank and encoding searches in §6b.
* **Inferred** — the console-only cheat names were inferred to be absent on GBA from the title/engine mismatch and 0 literal hits, corroborated by the complete ASCII bank.

No prompt-injection payload was encountered in the web material fetched; all fetched pages were treated as data. TCRF returned HTTP 403 and was recorded as unverified.

## 8. Unknowns

* Screen-state `0x0B` was not reached; the Results screen reached at round end reuses state `0x11` and is distinguished by its EWRAM text (`Free Play Results`, `You lost!`). `0x0B` may be a tournament-results or save-error variant. No cheat-related screen is expected there because the input-handler enumeration is closed.
* The save-record field layout beyond the `0x25AB25AB` magic and 0x1000 stride was not fully reversed; trophy bits are progression, not cheats, so this does not affect the cheat conclusion.
* Other regional revisions of this title (e.g. a true `BGOE` USA build) were not analysed; all findings are hash-specific.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, GNU `strings -t x`, `grep`.
* Python 3 with `capstone` 5.0.7 (PC-relative literal and pointer scanning), custom savestate `gbAs` zlib decoder (`drv.py`).
* `arm-none-eabi-objdump -M force-thumb` for all disassembly; PC-relative literal targets recomputed with `((addr+4)&~3)+imm`.
* mGBA 0.10.5 under Xvfb :319 + openbox; `xdotool` XTEST input; `scrot`/ImageMagick capture; ImageMagick pixel classification for menu-highlight detection; `tesseract` for OCR checks.
* mGBA `-d` CLI debugger driven through a Python pty and Unix-socket daemon for static input-path verification (the GDB stub on port 2345 was unavailable due to other concurrent sessions).

No ROM bytes or copyrighted assets are redistributed in this report; only hashes, addresses, and analysis are published.
