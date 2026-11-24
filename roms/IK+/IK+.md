# IK+ (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/IK+/IK+.gba` |
| Size | 4,194,304 bytes (0x400000) |
| `file` | Game Boy Advance ROM image: "IK PLUS" (A3KE7M, Rev.00) |
| Header title | `IK PLUS` (0xA0) |
| Game code | `A3KE` (0xAC); maker `7M` (0xB0) |
| Version | 0x00 (0xBC); complement 0xD1 (0xBD); header checksum 0x0000 (0xBE) |
| MD5 | `cce22f4507ceab482392247b74a8b55a` |
| SHA-1 | `99075504699400430e9817feb4192a6e153fbc9a` |
| SHA-256 | `fe2a07ee47ba1082131ba9fc8cc441e7c4f15903e0b2ac2e1b561d266b7423ad` |

**Embedded-header / patch scan (Phase 0).** The 156-byte Nintendo logo occurs exactly once, at file `0x04` (header base `0x00`) — a single-image ROM, no multiboot/multicart header. Entry word `0xEA00002E` is the stock `b 0x080000C0`; fixed byte `0x96` at `0xB2` is present. No appended trainer/cracktro markers (`CHEAT`, `TRAINER`, `GAMESHARK`, `CODEBREAKER`, `CRC BANDIT`, `MODE7`, `ACTION REPLAY`) were found; the last 64 bytes are `0xFF` padding. Header checksum `0x0000` with complement `0xD1` is consistent with a rebuilt header (guide §16.1); no functional patch was found. crt0's `main` pointer at `0x410` is `0x0800EC31` (Thumb `0x0800EC30`).

## 2. Executive summary

**There is no developer-intended cheat system in this GBA build.** No password screen, no typed-word cheat, no button-code detector, no hidden/debug menu, and no unlockable character/level exists. The four-item main menu and four-item Options menu were walked exhaustively with RAM evidence; every reachable screen was enumerated. The only "secrets" in the image are **leftover Amiga hint strings** ("HAVE YOU TRIED THE B KEY…", "S KEY TO ALTER SHADOW COLOR", "ASTERISK KEY FOR DIFFERENT RIPPLES", "T KEY WHEN MEN ARE INACTIVE", "PRESS SPACE BAR WHILST FIGHTING…"). These are data inherited from the 1987 original and are not wired to any GBA input: Select does nothing, L/R only change game speed, Start only toggles PAUSED.

A 3rd party cheat index FAQ for this game ID describes a **Password** menu and "Invert Y Axis" — those belong to a different SKU/port and do not exist in this ROM (details in §6/§8). The Amiga/Atari typed cheats `FREZ`, `PAC`, `FISH`, `BIRD`, `PERI`, `FUCK`, `CUNT` are all absent from the image. The only on-screen alphabet (`0x08018D98`) is a **Hall of Fame name-entry** field: its consumer copies three characters into a name buffer and performs no comparison.

Because no code system exists, the guide's §0.2 enumeration deliverables are satisfied as a **bounded negative**: §6b states the searched spaces and counts, proves the menu/text/button spaces closed, and records every published-code literal that was tested and rejected by absence.

## 3. How to reproduce

* Emulator: mGBA (SDL) on `Xvfb :317`, `SDL_AUDIODRIVER=dummy`, 3× scale.
* Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace` (also tried `shift`, `Delete`, `Tab`), D-pad=arrows.
* Boot path: AIA logo → Ignition logo → IK+ title/attract (credits → demo fight → Hall of Fame → tutorial moves) → `Start` → main menu. The attract cycle is automatic; `Start` skips it.
* Main menu path: `Down`/`Up` moves the white highlight; `A` selects. Items in order: **SINGLE PLAYER**, **TWO PLAYER**, **OPTIONS**, **TUTORIAL**; the selector wraps (no fifth slot).
* Options path: `Down Down`, `A`. Items: **DIFFICULTY** (A cycles EASY → MEDIUM → HARD → EASY; exactly 3 values), **MUSIC** (A toggles ON/OFF), **SOUND FX** (A toggles ON/OFF), **CREDITS** (A opens scrolling credits). Left/Right do nothing.
* In-game: L = SPEED SLOW, R = SPEED NORMAL → SWIFT (HUD top right); `Start` toggles `PAUSED` on/off; A/B at pause do nothing. Select has no effect despite the attract hint.
* Codes tested (all rejected/no effect): published-FAQ "Password" entry (no such screen), Amiga typed words `FREZ/PAC/FISH/BIRD/PERI`, Konami sequence `Up Up Down Down Left Right Left Right B A` on the menu, `L+R+Start`, `A+B+Start+Select`, ten consecutive `Down` on the menu, and Select via four different key bindings.
* Savestates were used for repeatability (`Shift+F1..F7` save, `F1..F7` load). RAM was read either live through mGBA's CLI debugger (`-d`, pty, `r/4`/`x/4`) or by decompressing the `gbAs` zlib chunk of `.ssN` files (guide §16.13).

## 4. Address map

| File offset | ROM address | Meaning |
|---:|---:|---|
| `0x000` | `0x08000000` | Header; stock entry `b 0x080000C0` |
| `0x410` | `0x08000410` | Thumb `main` pointer `0x0800EC31` |
| `0x1CA8` | `0x08001CA8` | **Input routine**: reads `0x04000130`, `held = ~KEYINPUT & 0xFFFF` → `0x030019C4`; `pressed = held & ~prev` → `0x03001CC4` |
| `0x259C` | `0x0800259C` | Font/text renderer; control bytes 10–12 index colour/belt/menu strings |
| `0x3048`–`0x3700` | `0x08003048`–`0x08003700` | Menu/UI button handlers (simple per-button `ands`/`cmp`) |
| `0xCDE` | `0x0800CADE` | Reads pressed mask, tests `& 0xF` (D-pad activity → demo timeout reset) |
| `0x10280` | `0x08010280` | Options text bank: `SoundFX On/Off`, `Music On/Off`, `Diffuculty Hard/Medium/Easy` (note the typo), belt ranks `BLACK 1..8` … `WHITE 1..3` |
| `0x13244` | `0x08013244` | `WHITE\0RED\0…BLUE` (belt colour names) |
| `0x13256` | `0x08013256` | Main-menu labels: `0 (Single Player)\rTwo Player\rOptions\rTutorial` |
| `0x18834` | `0x08018834` | **68-entry message pointer table** (strings in `0x08017F7A`–`0x080187DF`) |
| `0x18D7B` | `0x08018D7B` | `POS NAME BELT SCORE` (Hall of Fame header) |
| `0x18D98` | `0x08018D98` | Alphabet `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,-+.` (39 symbols) |
| `0x194A2`–`0x196D0` | `0x080194A2`–`0x080196D0` | Title/attract credits (`ORIGINAL VERSION`, `ARCHER MACLEAN`, `DAVE LOWE`, …) |
| `0x7F30` | `0x0807F30` | Audio sample filenames (`Koto.wav`, `snare1.wav`, …) — not text |

RAM (IWRAM, observed live and in savestates):

| Address | Use |
|---:|---|
| `0x030019C4` | Held button mask (active-high) |
| `0x03001CC4` | Newly-pressed button mask |
| `0x0300400C` | Options-screen submode (0 menu, 1 options) |
| `0x03004054`, `0x030040F0`, `0x030040F4` | Screen/mode values: options `0x23/0x47/0x03`, tutorial `0/0/0x0E`, single-player `0/0/0x0A`, two-player `0/0/0x06` |
| `0x03004140`, `0x030053A8` | Menu selector position (increments by `0x14` per `Down`) |
| `0x03004628` | Menu selector secondary value |
| `0x0300417C` | Menu/options sub-state |
| `0x03004020`, `0x03005380` | RAM lookup tables used by the font renderer |

Savestate layout (mGBA, 397,312-byte `gbAs` chunk): IWRAM at state offset `0x19000`, EWRAM at `0x21000`.

## 5. Algorithm

No validator, checksum, code table or generator exists, so there is no algorithm to reimplement. The relevant logic is:

1. **Input** (`0x0801CA8`): `held = (~(*u16*)0x04000130) & 0xFFFF`; `pressed = held & prev`; `prev = held`. Games read either `held` or `pressed` with a single bit mask (A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200). There is no history buffer, timer window, or sequence counter anywhere in the input path (BL/literal scans of `0x030019C4` and `0x03001CC4`).
2. **Menu dispatch**: four main items and four Options items, each a direct single-button handler. The selector wraps; no hidden slot exists.
3. **Text**: control byte 11 in the font renderer selects one of the four main-menu labels from the packed string at `0x08013256`; control bytes 10/12 select colour/belt strings via RAM tables. All 68 message-bank entries are plain ASCII with `\r` line breaks and `\x0e`/`\x17`/`\x18` colour/highlight control codes — not tile indices in disguise.

## 6. Tables

**Main menu (4 entries, verified visually and via selector RAM):** SINGLE PLAYER, TWO PLAYER, OPTIONS, TUTORIAL.

**Options (4 entries):** DIFFICULTY {EASY, MEDIUM, HARD}, MUSIC {ON, OFF}, SOUND FX {ON, OFF}, CREDITS.

**Message bank (`0x08018834`, 68 slots; slot 0 = malformed `0x00090906`, slots 1–67 valid):** gameplay result lines (1–23), Amiga hint lines (24–32), link/wait lines (33–44), tutorial move names (45–64), `PAUSED` (65), `DEMO MODE` (66), `PRESS THE A BUTTON` (67). Full decode was produced by a script (see §9). The Amiga-only lines are:

| # | Text | GBA behaviour |
|---:|---|---|
| 24 | HAVE YOU TRIED THE B KEY DURING BALL BONUS SCREEN! | text only |
| 25 | HAVE YOU TRIED THE P KEY DURING PAUSE MODE! | text only |
| 26 | L AND R BUTTONS ALTER GAME SPEED! | **real**: L/R change SPEED |
| 27 | PRESS SPACE BAR WHILST FIGHTING TO PAUSE GAME | equivalent is Start |
| 29 | HAVE YOU TRIED THE S KEY TO ALTER SHADOW COLOR! | text only |
| 30 | HAVE YOU TRIED THE ASTERISK KEY FOR DIFFERENT RIPPLES | text only |
| 31 | FOR A LAUGH: PRESS THE T KEY WHEN THE MEN ARE INACTIVE | text only |
| 46 | PRESS SELECT AT ANY TIME TO PRACTISE | **not functional** on this SKU |
| 63 | PRESS SELECT TO RETURN TO TUTORIAL MODE | **not functional** on this SKU |

**Alphabet (`0x08018D98`):** 39 symbols `A-Z 0-9 , - + .`; consumer at `0x0807588` (ROM `0x08007588`) loads the pointer and copies bytes 0/1/2 of an index array into a 3-character name buffer. No `cmp`/`strncmp` against the buffer, no flag write — **name entry, not a password** (guide §16.2b).

**Belt ranks (`0x080102F0`–`0x080103F8`):** BLACK 8→1, BROWN 3→1, PURPLE 3→1, GREEN 3→1, YELLOW 3→1, WHITE 3→1 — Hall of Fame progression, not unlockables.

## 6b. Enumeration

**Code space size: 0.** No alphabet length, field width, checksum, key table or accepted-code set exists to enumerate. Bounds are therefore proven on the *UI/text/button* spaces instead:

| Space searched | Method | Count / result |
|---|---|---|
| Embedded GBA headers | Nintendo-logo scan over 4 MiB | 1 hit (file `0x04`) → single image |
| Menu entries, main | Visual walk + selector RAM (`0x03004140` steps of `0x14`, wraps) | 4 entries; no fifth slot |
| Menu entries, Options | Visual walk with A on each row | 4 entries; no hidden row |
| Difficulty values | A pressed 7× on DIFFICULTY | 3 values, period 3 |
| Message-bank strings | Pointer table decoded from `0x18834` | 68 slots (67 valid strings), none a password |
| Word-like ASCII runs < `0x1A000` | Regex + letter-ratio filter | 202 runs; real text confined to `0x10280` (options), `0x18000`–`0x18945` (messages), `0x18D98` (alphabet), `0x194A2`–`0x196D0` (credits) |
| Keyword literals | Case-insensitive raw, `+0x20`, UTF-16LE/BE, UTF-32LE | `password`, `cheat`, `secret`, `unlock`, `debug`, `code` → **0 hits** in every encoding |
| Amiga typed cheats | Literal search | `FREZ`, `FISH`, `BIRD`, `PERI`, `FUCK`, `CUNT`, `ACIEED` → **0 hits** (`PAC` only as part of `SPACE BAR`) |
| Button-code mask tables | `u16` runs in code region `0x200`–`0x30000` | 3,564 zero-inclusive / 313 non-zero candidate runs; all are compressed-art/audio false positives (e.g. repeated `0x0011/0x0110`), none is a press sequence |
| Input sequence detector | All literal refs to `0x030019C4` (8) and `0x03001CC4` (18) disassembled | only single-button `ands`/`cmp`; no history/counter/checksum |

**Screens walked with RAM evidence** (each observed visually, with the `0x030040F4`/`0x0300400C` state signature recorded): title/attract (including credits, demo fight, Hall of Fame scoreboard and tutorial move demos), main menu, OPTIONS, CREDITS, TUTORIAL, SINGLE PLAYER (fight), TWO PLAYER (fight / WAITING), PAUSED. The Hall of Fame **name-entry** screen is derived statically from the alphabet consumer (not reached naturally; see §8).

**Published codes tested and their disposition:**

| Source | Claim | Result |
|---|---|---|
| 3rd party cheat index FAQ 28683 (GBA, Devis0r) | "Password — Enter a password for some special things to happen"; Options include "Invert Y Axis", "View Credits", "Music Volume", "Sound Volume" | **Wrong SKU**: direct fetch returned HTTP 403; recovered via search snippets. This ROM's Options are DIFFICULTY/MUSIC/SOUND FX/CREDITS and there is no Password menu or Invert Y Axis. Treated as data. |
| Amiga/Atari-ST cheats (KTH list, Amiga Reviews, 3rd party cheat indexes) | Type `FREZ`, `PAC`, `FISH`, `BIRD`, `PERI`, rude words during play | All literals absent from the ROM; no typed-input handler exists. |
| Attract text (in-ROM) | Select → practise; S/ASTERISK/T keys | Select binds to nothing in this build; keyboard-letter hints are Amiga leftovers. |
| 3rd party cheat indexes "cheats" page | Claims a 323 KB / 2013 ROM with cheat codes | Auto-generated/unreliable metadata (this ROM is 4 MiB); treated as data, no literals used. |

**Novel code minted:** not applicable — with a code space of zero there is no unpublished code to generate. The §0.2 deliverable is met by proving the *absence* of the space across the counts above rather than by minting a fake code.

**No prompt-injection** was encountered in fetched web pages or ROM strings; low-quality/incorrect pages were recorded as data only.

## 7. Validation evidence

* **Observed**: mGBA screenshots of every screen listed in §6b; menu selector RAM incrementing by `0x14` per `Down`; `0x030040F4` = 0x03/0x0E/0x0A/0x06 for options/tutorial/single/two-player; `0x0300400C` = 0/1 for menu/options; SPEED HUD cycling SLOW/NORMAL/SWIFT under L/R; `PAUSED` overlay toggling on Start; no effect from Select (4 bindings), Konami code, L+R+Start, or A+B+Start+Select.
* **Derived**: `0x0801CA8` computes held/pressed masks; font renderer at `0x0800259C` uses control bytes and the `0x08013244`/`0x08013256` string pointers; `0x08007588` copies 3 alphabet characters into a name buffer with no comparison; message table at `0x08018834` decoded into 68 strings; all keyword encodings yield zero hits.
* **Inferred**: the FAQ's Password menu belongs to another port (supported by "Invert Y Axis" and the mismatch with the four actual Options rows, but the exact port was not identified); the Amiga hints are unimplemented leftovers.

## 8. Unknowns

* The Hall of Fame **name-entry** screen was reached only statically (alphabet + consumer at `0x08007588`); a natural high-score qualification was not produced in the emulator, so its on-screen appearance is inferred, not observed.
* Bonus rounds (ball/bomb) were not entered naturally; they are ordinary gameplay, not cheat surfaces. Attract/demo footage shows the fight and Hall of Fame scoreboard only.
* Header complement `0xD1` does not match the standard GBA formula while the checksum is `0x0000`; this looks like a rebuilt header, but the rebuilding tool is unidentified. No functional patch was found.
* The exact identity of the port described by 3rd party cheat index FAQ 28683 is unresolved (it is not this GBA image).

## 9. Tooling

* `md5sum`, `sha1sum`, `sha256sum`, `file`, `xxd`, `strings`, `grep` for Phase 0/1.
* Python 3 with `capstone` 5.0.7 and `keystone-engine` for literal/PC-relative/BL scans.
* `arm-none-eabi-objdump -M force-thumb` for raw Thumb disassembly.
* mGBA 0.x SDL (`mgba -3`) under `Xvfb :317` + `openbox`; `xdotool` XTEST input; `scrot` + ImageMagick `convert`/`montage` for screenshots.
* mGBA CLI debugger (`mgba -3 -d`) driven over a Python `pty` with prompt-synchronised `frame`, `r/2`, `r/4`, `x/4`, `w/2`, `load` commands for live RAM reads.
* `/tmp/ikplus/ss.py` — decompresses the `gbAs` PNG chunk of mGBA savestates into raw RAM (guide §16.13).
* `/tmp/ikplus/dbg.py`, `live.py`, `gba.py`, `ramdump.py`, `walk.py` — analysis helpers written for this engagement.

**Legal note:** no ROM image, extracted graphics, music, or full game text is redistributed here; only addresses, hashes, algorithms, and the analyst's own scripts are published.

## 10. Cleanup

All emulator/debugger processes started for this job were terminated by PID, and generated `IK+.sav` / `IK+.ss1`–`IK+.ss7` files were removed from the ROM folder. The Xvfb display `:317` and its openbox instance were stopped. No other display, process, or `roms/INDEX.md` entry was touched.
