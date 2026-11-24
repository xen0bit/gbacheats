# Virtua Tennis (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Virtua Tennis/Virtua Tennis.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `VIRTUATENNIS` |
| Game code | `AVTE` (EU/ROW) |
| Maker code | `78` (Sega) |
| Version | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` (stock crt0 branch — **not** a cracktro) |
| Fixed byte / main unit / device | `0x96` / `0x00` / `0x00` |
| Header checksum / complement | `0x0000` / `0x06` (normal rebuilt-header artifact) |
| MD5 | `bfb5a63fde75becb342f5d0e9a8e0da2` |
| SHA-1 | `2bf5363d24c4ec6de8aafae1bffc84113eaed0a2` |
| SHA-256 | `21d2ac2bc2dfaa0b87636eb9edb7e08807402ffcff071326dfe3666bb25acd25` |

Title/version verified against the boot screen and Sega logo.

## 2. Executive summary

**Bounded negative.** This GBA SKU has **no developer-intended password, button-code, or hidden debug-menu entry surface**. The only user text-entry widget is the World Tour *Player Edit → NAME* keyboard (alphabet `A-Z a-z 0-9 . _ END`); it is consumed as a profile label, not compared against any code constant. Every published "Virtua Tennis" code belongs to a **different SKU**:

- `BRA` / `CAN` / `IND` / `ITA` / `JPN` / `NED` / `SUI` / `CRO` are **PC/Dreamcast** three-letter character codes (GameFAQs' GBA page is a mis-tagged copy of the PC entry: it literally says "PC" and "(Not for PC)"). **None of these strings exists in the GBA ROM** in ASCII, UTF-16LE/BE, UTF-32, or packed-u32 form.
- "Hold L + Up,Down,Up,Down,Square,Triangle,Square" etc. are **PSP *Virtua Tennis: World Tour*** codes; the corresponding GBA button-mask tables are absent (0 byte-level hits).

The four additional characters advertised by the manual are unlocked by **gameplay** (Master via Arcade, King via World Circuit), not by input. The ROM contains 17 character records (16 named + a dummy `Fake`, internal ID `0x12`), but no code path writes their unlock state from the keypad.

Confidence: **high** for absence of a code system on this exact ROM; the search spaces and counts are in §6b.

## 3. How to reproduce

Environment: `Xvfb :315 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`, `mgba 0.10.5 -3`.
mGBA SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold 120–200 ms per press.

Menu path (all screens walked, in order):

1. Sega logo → title "PRESS START" → main **MENU**.
2. **TOURNAMENT** → SINGLES/DOUBLES → settings → character select.
3. **EXHIBITION** → SINGLES/DOUBLES → SINGLE/MULTI → SETTINGS (COM LEVEL, GAME COUNT, TIE BREAK, DEUCE, POSITION, OK) → character select ("CHALLENGER WANTED!", 6×2 grid).
4. **WORLD TOUR** → CONTINUE (disabled) / NEW GAME → PLAYER EDIT (NAME, BODY, PLAYS, HAND…) → NAME keyboard.
5. **OPTIONS** → GAME LEVEL (EASY/NORMAL/HARD/VERY HARD), GAME COUNT, TIE BREAK (OFF/ON), DEUCE (ON/OFF), BEST SCORE → RANKING, SOUND → MUSIC TEST ("Take The Field"), LANGUAGE → ENGLISH, EXIT.

Dynamic tests performed at the character-select screen: L alone, R alone, Select alone, L+R, Select+A, L+R+Start, Start+A — **no hidden menu appeared** (screens `probe_*.png`, `combo_*.png`). At the main menu, the PSP code `L + U,D,U,D,A,B,A` was entered — **no confirmation tone or state change** (`code_test1.png`).

Screenshots and scratch scripts were in `/tmp/virtuatenis/`; selected evidence frames: `s3.png` (main menu), `s4.png` (Options), `s5.png` (ranking), `s13.png` (Exhibition settings), `s15.png`/`cs4.png` (character select), `w4.png` (NAME keyboard), `code_test1.png` (rejected PSP code).

## 4. Address map

| Item | Address (ROM) | File offset | Notes |
|---|---:|---:|---|
| crt0 entry | `0x08000000` | `0x0` | ARM `0xEA00002E` |
| Key read (keypad → state) | `0x0800994` | `0x994` | Reads `0x04000130`, active-high; also copied to IWRAM |
| Key accessors (held/pressed/released) | `0x08009D0` / `0x08009DC` / `0x08009E8` | `0x9D0`/`0x9DC`/`0x9E8` | 22 BL call sites each |
| Key state words (IWRAM) | `0x03000800` (held), `0x03000802` (pressed), `0x03000804` (released), `0x03000000` (previous) | — | Observed via mGBA CLI debugger `r/2` |
| Options label strings | `0x0819FA18`–`0x0819FA5A` | `0x19FA18`–`0x19FA5A` | `GAME LEVEL`, `GAME COUNT`, `TIE BREAK`, `DEUCE`, `BEST SCORE`, `MUSIC TEST`, `LANGUAGE` |
| Options label pointer table | `0x0819FA60` | `0x19FA60` | 7 × `u32` → the above strings |
| First ASCII alphabet bank | `0x08176CF4` | `0x176CF4` | `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._=<>/: -` + width table |
| Name-entry alphabet | `0x0819A60C` | `0x19A60C` | `A-Z a-z 0-9 . _ =`; referenced by code at `0x0803EEF4` |
| Character records | `0x08199419` + `i*0x4C` | `0x199419` + … | 17 records; name at `record+0x40`, 1-byte ID at `record+0x3F` |
| Character IDs | — | — | `1,2,3,4,5,6,9,0xD,0x10,0xF,0xB,0xA,7,8,0xC,0xE,0x12`; `0x11` unused; ID `0x12` = `Fake` |
| Tournament name table | `0x0819B020` + `i*0x5C` | `0x19B020` + … | `CHALLENGERS 1..8`, `Gulf Open`, `SEGA Tournament`, etc. |
| Text rendered via ASCII→tile | `0x0803EEF4` loads `0x0819A60C` | `0x3EEF4` | Proves UI text is ASCII, not a hidden font encoding |

## 5. Algorithm

Not applicable — no validator exists. The keypad path is conventional:

```
KEYINPUT(0x04000130) --~--> held@0x03000800
                            pressed  = (cur ^ prev) &  cur  @0x03000802
                            released = (cur ^ prev) &  prev @0x03000804
```

All 22 screen handlers that call the key accessors (`0x8002DA6`, `0x80079A4`, `0x80096A4`, `0x800A760`, `0x800CE90`, `0x8029518`, `0x802A184`, `0x802ED4C`, `0x8034EA6`, `0x80399EC`, `0x803DACC`, `0x803E850`, `0x8042024`, `0x8045C4E`, `0x804BFC6`, `0x804D262`, `0x8050D2A`, `0x8066932`, `0x806A002`, `0x806E206`, `0x80703AA`, `0x8071EB6`) were disassembled ±0x50 bytes; each is a plain navigation getter (D-pad / A / B / L / R). **None contains a mask table, sequence index, or code comparison.**

## 6. Tables

| Table | Address | Size | Purpose |
|---|---:|---:|---|
| Options labels | `0x0819FA18` | 7 NUL-terminated strings | Normal OPTIONS screen, not a debug menu |
| Options label pointers | `0x0819FA60` | 7 × u32 | `GAME LEVEL`, `GAME COUNT`, `TIE BREAK`, `DEUCE`, `BEST SCORE`, `MUSIC TEST`, `LANGUAGE` |
| Character records | `0x08199419` | 17 × `0x4C` bytes | Names `A.Carter … L.Graf` + `Fake` |
| Name-entry alphabet | `0x0819A60C` | 66 chars | Only text-input alphabet in the game |
| Tournament names | `0x0819B020` | ≥16 × `0x5C` | Normal tournament list |

**No code table, password table, checksum table, or button-mask table was found.**

## 6b. Enumeration

This section states the searched space and the counts that bound the negative.

**A. Published codes vs. ROM (space: all 3-letter ISO-style codes from every published Virtua Tennis list).**
Searched: `BRA, CAN, IND, ITA, JPN, NED, SUI, CRO` (PC/DC list) plus `KING, MASTER, DEBUG, SECRET, CHEAT`.
Encodings checked: ASCII NUL-terminated, UTF-16LE, UTF-16BE, UTF-32, and packed 4-byte little-endian integer in the code region `0x0–0x7FFFF`.
Result: **0 code strings in any encoding in the code region.** Raw ASCII `BRA` occurs once at file `0x345D9D` (inside compressed data, not a NUL-terminated table), `IND` once at `0x7AE71`, `JPN` once at `0x15DCF1`; `CAN`, `ITA` occur 0 times. These are coincidental byte sequences, not tables.

**B. String/text space.**
`strings -t x -n 4` → **49,564 lines**. Case-insensitive whole-word grep for `password|cheat|debug|secret|level select|unlock` → **0 hits**. The only debug-ish string, `MUSIC TEST` (`0x19FA49`), is a normal OPTIONS item and was reached in-game (`s4.png`). `master` (7 hits) and `king` (2 hits) are tournament/English words, not cheats.

**C. Font/tile text banks decoded before the negative.**
The game stores UI text as ASCII and converts at draw time: the renderer at `0x0803EEF4` loads the alphabet pointer `0x0819A60C`, and the OPTIONS labels are plain ASCII at `0x19FA18`. Seven full ASCII alphabets exist at `0x176CF4`, `0x176D0E`, `0x176E1A`, `0x176EBC`, `0x176F5A`, `0x177094` and `0x19A60C`. Therefore a hidden font-index-only message would have to be a byte table that is never referenced by an ASCII string — none was found. This removes the "text is font-encoded, strings misses it" escape hatch.

**D. Button-code / mask-table space.**
- Keypad literals: `0x04000130` occurs **exactly once** in the ROM (`0x9C4`).
- Key accessors `0x08009D0`/`0x08009DC` have **22 call sites each**; all 22 contexts disassembled — **0 mask comparisons, 0 sequence counters**.
- Published PSP mask sequences searched as little-endian u16 arrays: `L+U,D,U,D` (`0x240,0x280,0x240,0x280`), `L+R,L,R,L,R`, `L+U,U,U`, `L+R,R,R,U,U,U` → **0 hits** each.
- Byte-scan for runs of ≥4 consecutive u16 values in the valid mask range (`1..0x3FF` or `0xFC00..0xFFFF`) over the first `0x80000` bytes returned 1,295 runs, all inside ordinary ARM/Thumb instruction streams or data — no structured code table.

**E. Hidden/debug menu space.**
Screen dispatch was enumerated by walking all reachable screens (§3). The "debug-looking" option rows are all reachable through OPTIONS/Exhibition. No screen with `DEBUG`, `SECRET`, `CODE`, `WARP`, or `LEVEL SELECT` text exists, and no unlabelled menu entry was observed on any of the 12+ screens.

**F. Unlockables (the only hidden content).**
17 character records exist (IDs listed in §4). The manual states 12 selectable + 4 unlockable; the character-select grid shows exactly 12. Unlock is gameplay-driven (Master: complete Arcade; King: complete World Circuit) per the GBA manual and the SDA community guide for this exact SKU. No code-driven writer of the unlock state was found. ID `0x12` (`Fake`) is a dummy/debug leftover record, not an input-reachable character.

**G. Rejection / non-acceptance evidence (bounds).**
- PSP button code `L+U,D,U,D,A,B,A` entered on the GBA main menu → **no tone, no state change** (`code_test1.png`). This bounds the PSP-style code family as inapplicable.
- Published three-letter codes cannot be submitted at all: the character-select screen has **no text field**, and L/R/Select/L+R/Select+A combinations there do not open one (`combo_*.png`). This bounds the PC code family as unreachable, independent of whether the ROM stores them (it does not, per A).

**Conclusion of enumeration:** code-space size = **0 accepted values** for both published families; searched spaces A–G above are exhaustive for their stated encodings/screens. This is a bounded negative, not "not tested".

## 7. Validation evidence

- **Observed**: all screens listed in §3 via screenshots; savestates `ss1` (main menu) and `ss2` (OPTIONS) decompressed from the mGBA PNG `gbAs` chunk — 397,312 bytes each, 38,440 differing bytes in 2,055 runs (`ssdiff.py`), confirming live RAM/VRAM state changes per screen. mGBA CLI debugger reads of `0x03000800..0x03000804` and `0x03000000` (`keyprobe.py`, `rmem.py`). Rejection of the PSP code and of L/R/Select combinations on character select.
- **Derived**: keyread/accessor addresses and all 22 BL sites from raw Thumb disassembly (`arm-none-eabi-objdump -M force-thumb`); string/pointer tables from `strings -t x` and `struct.unpack_from` pointer scans; character record stride and IDs from raw bytes.
- **Inferred (lower confidence)**: unlock conditions (Master/King) come from the retail manual and community guides for this SKU, not from an executed gameplay completion in this session. The `Fake` record is labelled a dummy from its name and ID gap, not from a disassembly of its consumer.
- **Unverified**: no published code was successfully entered, because no entry surface exists; the GameFAQs GBA page's "PC" codes are treated as mis-tagged, not as rejected GBA codes.

## 8. Unknowns

- The exact consumer and unlock predicate for the `Fake` (ID `0x12`) record were not traced to a setter; its consumer may be dead code.
- The precise save-flag bit layout for character unlocks was not reverse-engineered (save is 512-byte SRAM, observed blank `0xFF` before gameplay).
- No full gameplay unlock was executed to observe a character being added to the grid; the unlock method is from documentation, not observation.

## 9. Tooling

- `strings -t x -n 4`, `grep -ic`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum`
- Python 3 scripts in `/tmp/virtuatenis/`: `k.py`/`k2.py` (XTEST key driver + screenshot crop), `ssdiff.py` (mGBA `gbAs` zlib chunk diff), `rmem.py`/`keyprobe.py`/`mgba_debug.py` (mGBA `-d` pty debugger), `mgba_probe.py`
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
- Python `struct` scans for literal pointers, packed code strings, and button-mask runs
- mGBA 0.10.5 (`-3`, `-g`, `-d`, savestates F1/F2), Xvfb :315 + openbox, `xdotool`, `scrot`, ImageMagick
- REA/Ghidra 12.1.4 was opened on the ROM but raw-ARM auto-analysis did not create Thumb functions; all conclusions rest on objdump + emulator evidence instead. The REA session was closed.
- Web recon: GameFAQs cheats/FAQ, SuperCheats, cheatinfo.de, IGN/Sega Retro, Speedrun Demos Archive forum (GBA unlock discussion), PSP code sites (correctly excluded as different SKU). Fetched pages were treated as data only.

## 10. Legal note

No ROM bytes, graphics, audio, or game text were redistributed. Only addresses, hashes, algorithms, and original analysis scripts are published.

## 11. Cleanup

All mGBA / Xvfb / openbox processes started for this engagement were stopped by PID; generated `.sav` and `.ss1`/`.ss2` files were removed from `roms/Virtua Tennis/`.
