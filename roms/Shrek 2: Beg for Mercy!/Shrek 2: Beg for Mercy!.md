# Shrek 2: Beg for Mercy! (GBA) — Reverse Engineering Report

## 1. Target identity
- File: `Shrek 2: Beg for Mercy!.gba`, 8,388,608 bytes (0x800000), flat raw GBA image.
- `file`: Game Boy Advance ROM image: "SHREK 2.1" (BSIE52, Rev.00).
- Header: title `SHREK 2.1` @0xA0; game code `BSIE` @0xAC (EU), maker `52` @0xB0, fixed `0x96` @0xB2, version `0x00` @0xBC, complement `0x99` (bits ~0x66), header checksum `0x0000` (normal rebuilt-header artifact).
- Entry word `0xEA00002E` = stock `b 0x080000C0`. No cracktro/trainer patch; keyword scan for GAMESHARK/CODEBREAKER/TRAINER/CRACK/SUNHORS/MODE7 = 0 hits.
- Nintendo-logo scan over all 8 MiB: **exactly one** GBA header, at file 0x0 (ROM `0x08000000`). Not a multi-game pack; no second image, no shell.
- Hashes: MD5 `c8a0ce6010243c1b4a05458344c9fc31`; SHA-1 `c5873294bb79b9252da82b02cc53ee7e8f4e663c`; SHA-256 `7fe009a208fbe46ca523f8c1e553ca015a61c51810d284fe81602cbe8cbee0fb`.
- Developer Vicarious Visions, publisher Activision; distinct SKU from the April-2004 `Shrek 2` (GameFAQs id 919680; TCRF separate page) — confirmed independently for this image.

## 2. Executive summary
**No developer-intended in-game cheat-code system exists in this ROM.** There is no password screen, no password alphabet/table/validator, no button-code matcher or key-mask sequence table, and no reachable hidden/debug menu. This is a **bounded "no system" result** (guide §0.2 point 5), proven by counting the searched spaces and walking every reachable screen with RAM evidence, not by a failure to find something.

What the game *does* have is ordinary progression content: 25 levels in 5 "scrolls" and four mini-games unlocked by collecting 40 coins in every level of a scroll (GameFAQs; level names verified in ROM). It also contains **unused/cut debug leftovers**: the strings `Defeat Level`, `Defeat Level 100%`, `Slow Motion` and three test-level names (`Puss Test`, `Shrek Test`, `Donkey Test`) sit in the text bank but no retail input path reaches a menu that displays them (corroborated by TCRF, which lists the test levels as "possible test levels — to do: find out how to play these levels").

Published "Shrek 2 (GBA) Scrapbook button codes" found on the web are **not applicable to this SKU**: the string `Scrapbook` occurs 0 times in this ROM, the pause menu has no Scrapbook entry (only Resume / Quit Level / Sleep / Sound), and the published prefix `Left,Up,A,B` ×3 produced no effect when entered on the title, pause and play screens. Those codes belong to the console versions / the other GBA `Shrek 2` / the 2-in-1 pack, exactly the SKU-confusion trap of guide §16.11.

## 3. How to reproduce
- Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy mgba -3 <rom>` on `Xvfb :318` + openbox. Default SDL keymap (A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows).
- Boot, hold `Start` through the Vicarious Visions/story intro, tap `A` through the story pages, reach level 1 ("Into the Forest").
- Menu path verified: Title (Start Game / View Credits) → Select a Slot (3 slots: New Game ×2, Erase) → gameplay → **Start** → pause menu (Resume / Quit Level / Sleep / Sound) → Sound submenu (Music/SFX Volume 100%) and Sleep Now? ("Press SELECT + L + R to wake"). Quit Level → confirmation (Cancel / Quit) → level select (Level 1–5, crown counter 0/40, level name) → **B** → "Choose a Scroll" (Job Hunt with 5-level scroll) → **B** → Select a Slot. Credits: Title → View Credits (scrolling developer/tester list).
- Button-code tests: entered published prefix `Left,Up,A,B,Left,Up,A,B,Left,Up,A,B` with suffixes `Up×5` (level select), `B×6` (coins), `U,R,D,L,U` (health) on title, pause and play screens — no sound, no screen change, no flag change. Title-screen combos `L+R`, `L+R+Start`, `Start+Select`, Konami code — no debug screen.
- RAM observation: mGBA savestates (`Shift+F1..F6`), `gbAs` PNG chunk zlib-decompressed (guide §16.13); EWRAM = state offset `0x21000` → `0x02000000`.

## 4. Address map
| Item | Address | Evidence |
|---|---|---|
| GBA header / stock entry | `0x08000000` / `0x080000C0` | Derived (bytes) |
| Key-input reader (`KEYINPUT & 0x3FF`) | literal `0x04000130` @`0x0800E3DC`, reader ~`0x0800E3CE` (`ldr r0,[pc,#8]; ldrh r1,[r0]; ldr r2,[pc,#8]=0x3FF; and; bx lr`) | Derived (disassembly) |
| Text/string-ID bank | `0x080AB794`–`0x080ABF38` (~92 `{u32 ptr, char[]}` records; pointer table at `0x080AB794+`) | Derived (pointer scan) |
| UI glyph bytes in text bank | `0x80`=A, `0x81`=B, `0x84`, `0x86`=L, `0x87`=R (e.g. `0x080ABC30` "Press SELECT + \x86 + \x87 to wake"; `0x080ABB28` "\x81 back \x80 select") | Derived (screen + bytes) |
| Debug action strings | `Defeat Level` `0x080ABC68`; `Defeat Level 100%` `0x080ABC7C`; `Slow Motion` `0x080ABC94` | Derived (strings) |
| Scroll-name strings | Job Hunt `0x080ABCA4`; Cat and Mouse `0x080ABCB4`; The Showdown `0x080ABCC8`; The Moral of the Story `0x080ABCDC`; Bonus `0x080ABCF8` | Derived |
| Test-level strings (unused) | Puss Test `0x080ABD04`; Shrek Test `0x080ABD14`; Donkey Test `0x080ABD24` | Derived + TCRF |
| 25 real level names | `0x080ABD34`–`0x080ABF38`, 4-byte-aligned records | Derived |
| Save | 512-byte Flash/SRAM at `0x0E000000` (`.sav`), checksum words `0xC0DE`/`0x600D` | Observed (file) |
| RAM screen bytes (savestate) | EWRAM `0x02007420`, `0x02002F3C` — values in §6b | Observed |

## 5. Algorithm
No code algorithm exists to reimplement. The only input-processing routine located is the ordinary key reader:
```
u16 keys = *(volatile u16*)0x04000130 & 0x03FF;   // active-low KEYINPUT
```
No code that shifts a key history, compares a button-mask run, checks a password alphabet, or computes a checksum was found anywhere in the 8 MiB. The debug-looking strings are data in the text bank with no reachable consumer on any retail screen.

## 6. Tables
- **Scrolls (8 name records, 5 accessible):** Job Hunt, Cat and Mouse, The Showdown, The Moral of the Story, Bonus, *Puss Test, Shrek Test, Donkey Test* (last three unreachable in retail play).
- **Levels (25):** Into the Forest, Cat Scratches, Rough and Tumble, Swamp Cat, Cat's Cradle / Duck and Cover, Tippytoes, Strength of an Ogre, Fire and Brimstone, Sticks and Stones / Water Slide, Barrel Blockade, Get to the Grove, Kickback, Playing Catch-Up / Woodland Chase, Treetop Flight, Ogre Slayer, Paws of Fury, Leaps and Bounds / Gatecrasher, One Step at a Time, Whiskers of Steel, Tweedle Dum and Dumber, Mine Mice.
- **Unlockables (not codes):** Duck and Cover, Barrel Blockade, Ogre Slayer, Mine Mice mini-games — 40 coins in every level of scrolls 1–4 respectively (GameFAQs, verified level names in ROM).
- **Debug action strings (no reachable menu):** Defeat Level, Defeat Level 100%, Slow Motion.
- **False positives classified:** `Code: B.Wodok` @`0x77BC35` = Shin'en GAX 3.05 audio-engine banner; `secret` @`0xAC368` = story narration ("holds the secret of killing an ogre"); `bonus` = the Bonus scroll name.

## 6b. Enumeration
**Result: 0 code systems found; space size = 0 codes.** Counted searches (each is a bounded negative, guide §0.2/§16.9):

| Space searched | Method | Hits relevant to a cheat system |
|---|---|---|
| All 8 MiB ASCII text | `rom.count()` for `password`, `cheat`, `code`, `secret`, `unlock`, `debug`, `scrapbook`, `level select`, `gameshark`, `codebreaker`, `action replay`, `bonus` | password 0, cheat 0, code 1 (audio banner), secret 1 (story), unlock 0, debug 0, scrapbook 0, level select 0, cheat-device 0, bonus 1 (scroll name) |
| Same, case-insensitive / `+0x20`-shifted / UTF-16LE | Python | 0 additional relevant hits |
| Button-mask sequence table | 4-press prefix `L,U,A,B` as u16/u8/u32, LE & BE, active-high (`0x20,0x40,0x01,0x02`) and active-low (`0x3DF,0x3BF,0x3FE,0x3FD`), forward/reverse, plus bit-index/enum byte encodings | 0 |
| Any run of ≥4 single-key masks | scan all 8 MiB for runs of active-low single-key values `{0x3FE,0x3FD,0x3FB,0x3F7,0x3EF,0x3DF,0x3BF,0x37F,0x2FF,0x1FF}` (u16 LE/BE) | 0 runs |
| Same for active-high masks | scan all 8 MiB | 59 (LE)/125 (BE) runs, all in compressed graphics ranges `0x0834xxxx`–`0x0860xxxx`, none a `Left,Up,A,B` prefix — classified as graphics noise |
| Password literal tables / alphabets | string scan + pointer scan for code-table-shaped records | 0 |
| Published codes verified literally | published codes are button sequences (no literal); associated UI word `Scrapbook` | 0 occurrences; entry screen absent; prefix empirically rejected |
| Embedded GBA headers / trainers | 156-byte logo scan + entry-word check + trainer keyword scan | 1 header (stock), 0 trainers |

**Every reachable screen walked, with RAM evidence** (state-offset → EWRAM; values are `0x02007420 / 0x02002F3C`):

| Screen | Evidence | 0x02007420 | 0x02002F3C |
|---|---|---|---|
| Title (Start Game / View Credits) | screenshot + savestate | 0x03 | 0x14 |
| Select a Slot (3 slots, Erase) | screenshot + savestate | 0x02 | 0x1F |
| Choose a Scroll (Job Hunt, 5-level scroll) | screenshot + savestate | 0x02 | 0x38 |
| Level select (Level 1–5, 0/40 crowns) | screenshot + savestate | 0x01 | 0x3D |
| Gameplay (level 1, HUD 0/40) | screenshot + savestate | 0x07 | 0x0C |
| Sleep Now? (SELECT+L+R wake prompt) | screenshot + savestate | 0x02 | 0x3C |
| Pause menu / Sound submenu / Quit confirmation / Credits | screenshots (no distinct scene byte; menu overlays) | — | — |

No 6th scroll, debug menu, password field, code-entry panel, or character-select appeared on any screen; D-pad/L/R on the scroll screen never changed "Job Hunt"; the three test-level names never rendered. **Novel-code minting is not applicable**: with 0 code systems there is no validator to call as an oracle and no code space to enumerate; bounds are proven by the rejection tests above (published prefix entered and ignored; out-of-vocabulary inputs have no matcher to call). This is a "no system" result, not an untested one.

## 7. Validation evidence
- **Observed:** all 8 screens in mGBA; savestate RAM bytes; 0/40 crown counter; no effect from any published/undocumented button combination; "Scrapbook" absent from the ROM.
- **Derived:** header/logo count; keyword and key-mask counts; key-reader disassembly; string/pointer tables; glyph-byte meanings; TCRF corroboration of unused test levels.
- **Inferred:** the debug action strings (`Defeat Level`, `Slow Motion`) and test-level names are cut/unreachable content. Confidence moderate-high: no retail screen displays them, no direct pointer xref found beyond their own records, and TCRF classifies them as unused. No gate was proven, so this is a bounded "no reachable path found" (guide §16.3), not absolute proof of dead code.

## 8. Unknowns
- Whether a debug build/prototype or a non-retail loader could reach the three test levels or the `Defeat Level`/`Slow Motion` options; the gate, if any, was not identified. TCRF likewise leaves this as a to-do.
- Hidden developer credits (TCRF category) were not fully captured; the visible credits roll is ordinary and no credits-trigger code was found.
- The exact save-field encoding for the 40-coin unlock flags was not reversed (progression content, not a cheat code).

## 9. Tooling
`strings`, `grep -abo`, `xxd`, Python 3 (struct/re/zlib), `arm-none-eabi-objdump -M force-thumb`, Capstone (LDR-literal and BL-target scans), mGBA 0.10.5 under Xvfb :318 + openbox, xdotool, scrot, savestate `gbAs` zlib parsing. Web: GameFAQs cheats (live 403 → web.archive.org snapshot), TCRF "Shrek 2: Beg for Mercy" and "Shrek 2 (GBA)" (archive), megagames/planetcheats/projectcheatcodes (published button codes — classified as other SKUs). Fetched page text was treated as data only; no prompt-injection encountered.

**Legal note:** no ROM or copyrighted assets are redistributed; only hashes, addresses, and findings are published.
