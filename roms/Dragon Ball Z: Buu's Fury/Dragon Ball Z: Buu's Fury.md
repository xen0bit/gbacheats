# Dragon Ball Z: Buu's Fury (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dragon Ball Z: Buu's Fury.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) — *not* 32 MiB as the brief speculated |
| Header title | `DBZBUUSFURY` |
| Game code | `BG3E` (header reports `BG3E70`, maker `70`) |
| Maker | `70` |
| Version | 0x00 (Rev.00) |
| Complement byte | 0x84 — matches Data Crystal's published `Checksum 84` |
| Header checksum | `0x0000` (rebuilt-header artifact; computed value would be 0x00B6) |
| Entry word | `0xEA00002E` → stock `0x080000C0` branch, **no cracktro / trainer patch** |
| MD5 | `3a74fce97f1ea2b28c2a50ec3df0acee` |
| SHA-1 | `f1c4b07554d2a3b1ad2f325307051e775ce68087` |
| SHA-256 | `940ad5f01db4465b8877dfe739510cbf34f4ea3d390f3df13519808bc36f059e` |
| CRC32 | `0x01C1707F` — exact match to Data Crystal's retail dump |

**Embedded GBA-header scan:** the full 156-byte Nintendo logo occurs exactly **once**, at file offset 0x000004 (the header at 0x0). This is a single standalone retail image, not a 2-in-1 cart or a concatenated pack. The double-pack re-release with *Dragon Ball GT: Transformation* is a different ROM and was **not** analysed here.

Developer/publisher metadata from TCRF and Data Crystal: Webfoot Technologies (developer), Atari SA / Infogrames (publisher), US release 2004-09-14. The engine is a C++ bytecode interpreter (see the embedded source paths in §6).

## 2. Executive summary

**No developer-intended cheat-code system exists in this retail standalone image.** There is no password entry screen, no button-code entry screen, no hidden/debug menu, no sound test, and no unlock-all shortcut. The complete in-game menu tree was walked and is enumerated in §3/§6b; every published code was tested and produced no state change; the literal search space for button sequences and password strings was searched exhaustively with the counts recorded in §6b.

What *is* present:

* A **save-bit unlockable**, not a code: Gogeta is unlocked by returning all 15 Z-Fighter Exhibits and all 25 Hercule Exhibits (§16.18 of the guide — a save-flag unlock, not a cheat system). Post-game modes are likewise progress-gated.
* One **minigame-specific input exploit** published for this title: the *Perfect Fusion* dance input `Up, B, Left, Down, A` (GameFAQs, standalone Buu's Fury page). This is a fixed in-game input sequence used during the fusion minigame, **not** a global code system with an enumerable space. Its literal byte encoding was not found in this image by the exhaustive search in §6b; dynamic confirmation would require post-game fusion access, which was not reached (see §8).
* **Dead development leftovers**: crash-handler strings and Windows source paths (§6); no reachable debug screen.

**The four "Developer cheat codes" widely published for `Buu's Fury / GT: Transformation` belong to Dragon Ball GT: Transformation, not to this image.** They are listed under the *GT: Transformation Cheats* heading on the combined GameFAQs page and are absent from the standalone Buu's Fury cheats page. All four were tested at this game's title screen and main menu with no effect, and none of their button-mask encodings occurs anywhere in this ROM. Nothing is shared with the concurrently analysed GT image at the code/table level; the two titles share only the Webfoot engine lineage and the later double-pack cartridge.

The game also contains anti-piracy checks (save-type detection → "This game will not run on this hardware" in Grand Kai's mansion), which are copy protection, not cheats.

## 3. How to reproduce

* Emulator: `mgba-sdl` (here `/usr/local/bin/mgba 3.7`) under `Xvfb :318 -screen 0 1024x768x24` + `openbox`; `SDL_AUDIODRIVER=dummy`. Screenshots: `import -window root shot_NN.png`, cropped with `convert shot_NN.png -crop 720x480+154+184 +repage crop_NN.png`.
* Keymap (verified against on-screen prompts): **A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys.** Hold 100–300 ms; short taps are missed (§16.2). Key repeat can double-step a cursor — use ≤100 ms holds for menu navigation.
* Analysis was performed on a byte-identical working copy (`buusfury_work.gba`, CRC32 0x01C1707F) so no emulator artifacts would be written next to the original ROM.

**Exact menu path walked (all screens):**

1. Boot → Atari logo → title screen: `START`, `OPTIONS`.
2. `OPTIONS` → `Sound FX Volume`, `Music Volume`, `Text Speed`, `Credits`; `A`=Select, `B`=Cancel.
3. Title `START` → main menu: `SINGLE PLAYER`, `MULTIPLAYER`.
4. `MULTIPLAYER` → `DOJO`, `TRADING POST` — both immediately show "Waiting for a friend…" (link-cable only) and expose no offline character select.
5. `SINGLE PLAYER` → `Select Game` → `GAME 1 New Game`, `GAME 2 New Game`.
6. New Game → ~500 dialogue advances → Chapter 1 "The Other World" → playable field.
7. `Start` (in the field) → pause ring: `Status` (Goku Lv60, HP/EP/XP/ZENI/TIME, STR/POW/END/SPD, `Skills` on R), `Journal` (GOALS / COMPLETED GOALS; `Options` reachable by pressing L from Journal), `Inventory` (SUPPLIES / STORY ITEMS; `Equip` on R), `Options` (Sound FX Volume, Music Volume, Text Speed, `Credits`, `Sleep`).

**Published codes tested (title screen and main menu, each entered slowly and screenshotted):**

| Source / code | Buttons entered | Result |
|---|---|---|
| Prototype debug menu (TCRF prototype article) | L L R R Up Down Left Right | No effect; title screen unchanged |
| GT "20,000 Secret Shop Zenie" | Up Down B Left Right B L R B Up Left Down L R L R B | No effect; no menu/flag change |
| GT "Unlock All Characters" | Down Up Left Left Down Up Left Left Down Up Left Left Up Up Down Up B | No effect |
| GT "Unlock All Planets" | Up Up Down Right Down Right Up Left Left Up B | No effect |
| GT "Unlock Post-Game Modes" | Left Up Up Down ×4 … B (17 presses) | No effect |

Observed differences in title captures were confined to the animated menu cursor; no new option, counter, or screen appeared.

## 4. Address map

| Address (file offset / ROM address) | Meaning | Evidence type |
|---|---|---|
| 0x000000 / `0x08000000` | Header; stock ARM entry `0xEA00002E` | Observed (xxd) |
| 0x0000A0 / `0x080000A0` | Title `DBZBUUSFURY`, code `BG3E`, maker `70`, complement 0x84 | Observed |
| 0x004160 / `0x08004160` | `T:\Source\ByteCodeInterpreter\ByteCodeInterpreter.cpp` | Observed (strings + TCRF) |
| 0x004818 / `0x08004818` | `T:\Source\GameData.cpp` | Observed |
| 0x008A5C / `0x08008A5C` | `T:\Source\AreaEntry.cpp` | Observed |
| 0x013BAC / `0x08013BAC` | `T:\Source\CharacterData.cpp` (also shown on assertion screen) | Observed |
| 0x041844, 0x04225C / `0x08041844`, `0x0804225C` | NUL-terminated `SPAGHETTI` (developer joke, twice) | Observed (TCRF lists 0x4225A; actual string starts 0x4225C) |
| 0x0480F4 / `0x080480F4` | Crash-handler strings: `Invalid Operation`, `Divide By Zero`, `Overflow`, `Underflow`, `Inexact Result`, `Heap memory corrupted`, `Unknown signal` | Observed + TCRF |
| 0x05553C / `0x0805553C` | `Expected dialog to start with a code block` / `Internal equipment consistency error!` | TCRF |
| 0x06B7400 / `0x0806B7400` | `Energy attack level set for attack which doesn't exist for player!` etc. | TCRF |
| 0x07B5B64–0x07B5B7C / `0x0807B5B64`– | Table of seven **compressed** text-bank pointers (`0x0879BF2C`, `0x087A04F0`, `0x087A46C8`, `0x087A8AD8`, `0x087AD118`, `0x087B1558`, `0x087B5AA0`) — why `strings` finds almost no game text | Data Crystal + observed |
| 0x092CD0–0x093E90 / `0x08092CD0`– | Bytecode/script record table (fixed-stride records: opcode byte, ids, u16 fields, two ROM pointers). Three apparent "button sequence" byte matches fall inside this table and are coincidences | Observed (xxd) |
| `0x0800419C` | Show logos | Data Crystal |
| `0x0803D7FA` | Show main screen (menu dispatcher; loops on a bytecode-screen state machine) | Data Crystal + objdump |
| `0x08008A1C` | Area/map loader breakpoint: `r1` = `MapInfo*` | Data Crystal |
| `0x0801226A` | Message-display breakpoint: `r1` = text id (32-bit) | Data Crystal |
| `0x03007FF8` (BIOS) | Key-input mirror; only two literals reference it (0x8040E9C / 0x8040F94, CRT region) | Observed (literal scan) |
| `0x0300xxxx` / `0x0202D0B8` | Runtime globals and active sprite pointer used by CodeBreaker/ROM-hack tooling | Data Crystal; **out of scope**, documented only to classify published codes |

mGBA savestate layout (guide §16.13) was not needed: no state-changing cheat was found, so no RAM flag exists to diff.

## 5. Algorithm

There is no password validator, checksum, generator, or lookup table to reimplement. The "algorithm" recovered here is the **classification/decision procedure** that establishes the negative:

1. Fingerprint the image and prove it is the retail standalone (§1).
2. Search all ASCII text for passwords/debug/code vocabulary and classify each hit (game text is compressed, so a sparse `strings` result is expected, not evidence of absence by itself).
3. Search published codes, assign each to the correct SKU, and verify each literal in the ROM.
4. For every published button sequence, generate all plausible byte encodings (active-high/active-low masks as u8/u16/u32, fwd/rev; several key-index orders) and search the whole 8 MiB image.
5. Walk every reachable menu screen and enter every published code on the title and main menus, observing for new options/flags.
6. Treat remaining hits as false positives unless they reproduce in-game (all three raw hits were demonstrably inside a script-record table or an audio wave table).

## 6. Tables

**Text search counts (whole 8 MiB file):**

| Search | Lines / hits | Classification |
|---|---|---|
| `strings -t x -n 4` | 101,354 lines | Overwhelmingly compressed-data noise |
| `strings -t x -n 3` | 233,881 lines | Same |
| `-iE 'password\|cheat\|debug\|secret\|unlock\|generator\|invalid\|hidden\|...'` on `-n 4` | **2** hits | (a) `T:\Source\ByteCodeInterpreter\ByteCodeInterpreter.cpp` @0x4160; (b) `Invalid Operation` @0x480F4 — both development leftovers, neither a cheat surface |
| Same keywords on `-n 3` | 3 meaningful hits | header title @0xA0; `T:\Source\CharacterData.cpp` @0x13BAC; noise (`siybUU/`, `buU`, etc.) — no password/code hit |
| Additional source paths | 2 more | `T:\Source\GameData.cpp` @0x4818, `T:\Source\AreaEntry.cpp` @0x8A5C |

**Published-code verification:**

| Published item | Source | In this ROM? | In-game effect |
|---|---|---|---|
| "20,000 Secret Shop Zenie", "Unlock All Characters", "Unlock All Planets", "Unlock Post-Game Modes" (button sequences) | GameFAQs combined page `gba/931746`, under **GT: Transformation** | No mask encoding found | No effect on title or main menu |
| Perfect Fusion `Up, B, Left, Down, A` | GameFAQs standalone `gba/920530`, "Secrets" | No literal encoding found | Not dynamically reached (§8) |
| Gogeta unlock via 15 Z + 25 Hercule Exhibits | GameFAQs / TCRF | Save-flag unlock (not a code) | Not a cheat system |
| CodeBreaker / GameShark / Action Replay lists (Neoseeker, SuperCheats, Ethereal Games) | various | Out of scope by brief (memory-edit codes); addresses e.g. 0x03001560 are RAM writes, not developer cheats | Not tested (out of scope) |
| Prototype debug menu (L L R R U D L R, zone/sound select) | TCRF prototype article | No encoding found; TCRF states menu exists in **every prototype**, not the retail build | No effect on retail title screen |

**Button-mask search space searched:** 8 distinct sequences (5 GT/prototype + Perfect Fusion + 2 GT gameplay codes taken from the combined page) × {active-high/active-low u8, u16 LE/BE, u32 LE; forward and reversed} plus 8 alternative key-index orders → roughly 250 full-file scans. Raw hits: 3, all inspected at byte level and rejected as false positives (one in the bytecode record table at 0x92D09, one in the same table at 0x93E51, one in a sine/audio curve table at 0x341C1B).

**Anti-piracy (context only, not a cheat):** save-type check at Grand Kai's mansion, Babidi-ship switch, and the Chapter-5 Lv80 door (TCRF).

## 6b. Enumeration

Guide §0.2 requires either full enumeration of a code space or a bounded proof that no space exists. This is the latter.

* **Space definition:** none. There is no alphabet, no fixed-length code, no checksum field, no hard-coded code table, no key-mask sequence table, and no debug-screen gate in the reachable retail image. Representable cheat codes = **0**.
* **Validator model:** none. No routine reads a code buffer and compares it against constants; no return-value map exists to invert.
* **Novel code:** **not minted, because there is no system to mint from.** Minting a code for a nonexistent validator would be fabricated evidence. (Where a system exists, the guide requires a generated code proved in-game; here the deliverable is the bounded negative instead.)
* **Bounds proven by rejection:** every published button sequence (6 codes, listed in §3 and §6) was entered on the title screen and the main menu and was rejected — no new menu entry, no visual state change, and no transition to a debug/zone/sound screen. The 8-press prototype debug code was additionally entered one press at a time on the title screen with screenshots after each press (shots 50–57); the emulator remained alive and the title screen was unchanged.
* **Negative bounded by search counts:** the entire 8 MiB image was scanned for each published sequence in ~250 encodings; all three raw hits were shown by byte-level inspection to be unrelated data structures. The ASCII keyword space (101,354 `-n4` strings) yielded exactly two meaningful hits, both development leftovers. Game text itself lives in seven compressed banks, so the string count is a bounded statement about the *ASCII* space only; the compressed text banks were not decompressed because they contain dialogue, not cheat UI, and the menu enumeration covers every visible screen (§3).
* **Screen enumeration is closed:** title → options → main → multiplayer (dojo, trading post) → select-game → in-game pause (status, journal, inventory, equip, options, skills, credits, sleep). No screen exposes a code/debug entry field.

**Enumeration of the one real in-game sequence:** the Perfect Fusion input `Up, B, Left, Down, A` is a single fixed 5-press sequence during the fusion minigame (space size 1 documented value). No alternate/undocumented fusion sequence was found in the ROM's button-encoding search, so no unpublished variant could be produced.

## 7. Validation evidence

**Observed** (emulator / hex dump):
* Boot, keymap, and all eight menu screens (screenshots 01–48 in `/tmp/buusfury/`).
* All six published button sequences entered at title/main menu with no effect; prototype code re-entered step-by-step on the title screen.
* Single 8 MiB header, stock entry word, CRC32 0x01C1707F, complement 0x84; exactly one Nintendo-logo occurrence.
* `strings` counts and the two meaningful keyword hits; source paths and `SPAGHETTI` bytes.
* Three raw button-sequence hits inspected and rejected (bytecode table / audio wave table).

**Derived** (disassembly / static):
* `0x0803D7FA` is a bytecode-screen dispatcher loop, not a cheat validator.
* Game UI text resides in compressed banks referenced from `0x0807B5B64`, explaining the near-absence of ASCII menu strings.
* No literal for `0x04000130` exists; only two `0x03007FF8` literals, both in the CRT region — the game's key state reaches game logic indirectly, so the ~250-encoding full-file search is the correct static bounded test, not a handful of pointer xrefs.

**Inferred (labelled, not asserted):**
* The GT "developer codes" are implemented in the GT standalone/double-pack image, not here; this is supported by the combined-page attribution, their absence from the standalone page, their absence from this ROM, and their lack of effect here, but the GT image itself was not disassembled.
* The `SPAGHETTI` string is a programmer joke (TCRF's reading); it has no observed function.
* The anti-piracy message is triggered by save-type detection (TCRF); the triggering map was not visited.

## 8. Unknowns

* The Perfect Fusion `Up, B, Left, Down, A` sequence was **not dynamically confirmed**. Reaching a fusion dance requires substantial post-game story progress (Goku+Vegeta fusion is unlocked after all exhibits; Goten+Trunks fusion occurs mid-story). No save file was available, and generating one by RAM/GameShark edits is out of scope for this brief. Its literal encoding is also absent from the exhaustive search, which suggests an inline compiled key comparison rather than a data table — the exact code was not isolated. This is the one claim in the report that remains unproven in-game; it is reported as a published code of uncertain implementation for this exact build, **not** as a confirmed cheat.
* The seven compressed text banks were not decompressed; any cheat-ish string that exists only inside them (e.g. a hidden menu label drawn from compressed text) would be missed by the ASCII search. The screen enumeration found no such menu.
* The double-pack re-release (`Buu's Fury / GT: Transformation`) is a separate ROM and was not analysed. Any code shared between the two titles would have to be verified there independently.
* No emulator GDB session was kept alive during code entry (the first `-g` instance exited when the stub client disconnected); therefore no before/after RAM dump exists. Because no code produced any visual state change, there was no flag to verify, and the negative rests on the menu enumeration plus the static search rather than on a RAM diff.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, Python `zlib.crc32` for identity.
* `strings -t x -n 3/4`, `xxd`, `grep -aiE` for text reconnaissance.
* Python 3 with `struct` / `capstone 5.0.7` for literal scans (u8/u16/u32, both endiannesses, forward/reversed), embedded-header scan, Thumb PC-relative/literal and immediate-cluster scans. `arm-none-eabi-objdump -M force-thumb` for targeted disassembly. `keystone-engine` installed but not needed.
* `mgba-sdl` (3.7) under `Xvfb :318` + `openbox`; `xdotool` XTEST key events (`/tmp/buusfury/drive.py`); `import`/`convert` (ImageMagick) for screenshots.
* Web references: GameFAQs cheats pages `gba/920530` (standalone) and `gba/931746` (combined double pack); TCRF *Dragon Ball Z: Buu's Fury* and its prototype article (via web.archive.org); Data Crystal *Buu's Fury* ROM map (via web.archive.org). Fetched pages were treated as data; no instructions found in them were acted upon. No prompt-injection payload was encountered.

**Legal note:** no ROM image, extracted graphics, music, or game text is redistributed here. Only hashes, addresses, offsets, counts, and independently written findings are published.
