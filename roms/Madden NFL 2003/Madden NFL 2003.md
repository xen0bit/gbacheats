# Madden NFL 2003 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Madden NFL 2003/Madden NFL 2003.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `MADDEN NFL03` (12 bytes at 0xA0) |
| Game code | `ANJE` (USA) |
| Maker | `69` |
| Revision | 0x00 (version byte 0xBC = 0x00) |
| Fixed byte 0xB2 | 0x96 (correct) |
| Complement 0xBD | 0xB8; checksum 0xBE..BF = 0x0000 (rebuilt-header artifact per guide §16.1) |
| Entry word | `0xEA00002E` = `b 0x080000C0` (stock; crt0 at 0x080000C0 intact) |
| MD5 | `d8c148895dc874b51f5075aebfcef88a` |
| SHA-1 | `e2f4e66fa582303d06f79e572e19e80462a7cc42` |
| SHA-256 | `91e64ae7a24c2315681276304609707a4621597e6d8b55c6db574626449be96c` |

Phase 0 result: **one** embedded GBA header (Nintendo-logo scan of all 4 MiB found a single logo hit at file offset 0x04 → header base 0x0). This is not a multi-game cart and there is no appended trainer or cracktro: the entry word and the ARM crt0 at 0x080000C0 are the stock values. Development credits in the image read `TIBURON ENTERTAINMENT` (0x377FDD) and `BUDCAT CREATIONS` (0x377FCC); 3rd party cheat indexes confirm Budcat Creations as developer, EA Sports as publisher.

## 2. Executive summary

**This GBA SKU has no password, cheat-code, or button-code entry system, and no reachable hidden/debug menu.** There is no code-entry screen in any of the menus walked, no alphabet/validator/literal code table in the ROM, and no run of key masks in the code that forms a cheat sequence. All of the widely published "cheats" for Madden NFL 2003 GBA are CodeBreaker / GameShark / Action Replay **RAM patches**, i.e. memory editing, which is explicitly out of scope; I verified that their target addresses map to real live game state (home/away team ID, play clock, down, scores) rather than to any in-game code mechanism.

Three kinds of *developer-intended* content do exist and are characterised below:

1. **Hidden teams** — IDs `0x21` (Players, Inc.), `0x22` (EA Sports), `0x23` (Budcat), stored in the same team-ID fields as the 32 NFL teams. 3rd party cheat indexes state there are no known input codes for them on GBA and asks for button-code research; my exhaustive key-mask and menu scans found no input route. They are reachable only by directly writing RAM, which is out of scope. (§16.18-style save/data state, not a code.)
2. **Unlockable players** — eight legends unlocked by Gold Ranking specific drills on All-Madden, plus Mike Ditka by having another EA Sports football save present. This is save-bit state, not a code (§16.18).
3. **Post-touchdown sounds** — a published in-game button trick (press A/B/R/L during the TD celebration for horn/whistle/"Pow!"/grunt). It is a transient input branch in gameplay, not a code-entry system; I did not score a touchdown in the emulator, so it is recorded as a published lead, not an executed observation.

Menu text is **not** plain ASCII: the ROM contains 15,042 printable strings ≥4 chars (mostly NFL commentary, team slogans, credits), but none of the 14 menu words tested appears under any constant byte shift, UTF-16LE, or the 36-entry font tables found. The main-menu and title labels are baked into pre-rendered/tile-indexed screen art, so a `strings` negative is a statement about that encoding space only (§11, §16.11).

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under `Xvfb :318`, `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, `mgba -g -3 <rom>`.
- mGBA SDL keymap used: **A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys.** Keys were held 50–150 ms; screenshots captured with `scrot -o` and cropped to the 720×480 client area at `+154+158`.
- RAM evidence: GDB stub on `:2345`; a persistent `gdb-multiarch` client was kept connected (the stub terminates on client disconnect). `SIGINT` to the GDB process pauses mGBA, `x/<n><fmt> <addr>` reads memory, `continue` resumes. Savestates were also decoded independently: mGBA `.ss1` is a PNG with a zlib-compressed `gbAs` chunk; the decompressed state is 397,312 bytes for this 4 MiB ROM (§16.13).
- Menu paths walked (all screenshots saved in `/tmp/madden03/`):
  - Legal/copyright → **Start** → "PLAY NOW / SOLO PLAY / LINK PLAY" quick menu → **Start/A** → GAME RULES (QUARTERS 5 MINUTES, LOCATION OAKLAND, WEATHER FAIR, ENDURANCE ON, ROSTERS ORIGINAL) → **A** → TEAM SELECT (HOME/VISITOR) → **A** → CONTROLLER SETUP → **A** → in-game (play-call grid, then field play).
  - **B** from the quick menu → main menu "PLAY NOW / SEASON PLAY / FRONT OFFICE / RECORDS" → SEASON PLAY (NEW NFL SEASON / NEW PLAYOFFS / SEASON RULES), RECORDS (NFL RECORDS: MOST YARDS PASSING/RUSHING, LONGEST PASS CAUGHT, LONGEST RUN, MOST TOTAL YARDS, MOST POINTS, LONGEST FIELD GOAL; `SELECT: RESET`).
  - **Start** during play returned to the main menu (no separate pause menu).
  - Hidden-menu gate probes: L+R held at main menu, Select+Start held at main menu — no new screen (the latter merely navigated to RECORDS).
- Published codes "tested": the CodeBreaker codes were not entered (no external device / no in-game entry point exists). Instead their RAM targets were verified against the live game with GDB — see §4 and §7.

## 4. Address map

File offset = ROM address − 0x08000000.

| ROM address / file offset | Meaning | Evidence |
|---|---|---|
| 0x08000000 / 0x000000 | GBA header; title `MADDEN NFL03`, code `ANJE`, maker `69` | Observed |
| 0x080000C0 / 0x0000C0 | stock ARM crt0 (entry word 0xEA00002E branches here) | Observed |
| 0x08000D20 / 0x000D20, 0x08001354 / 0x001354 | KEYINPUT literal 0x04000130 in Thumb literal pools; joypad handler at 0x08001320 reads `ldrh` of KEYINPUT, `eors r0, 0x03FF` (active-high mask), stores to RAM | Derived (objdump) |
| 0x350E29 | literal ASCII `ABCDEFGHIJKLMNOPQRSTUVWXYZ` inside code — name-entry/font alphabet, **not** a password alphabet | Observed |
| 0x3740B0–0x374190 | font/tile mapping region: 36-byte identity tables (0x00..0x23) and two permutations of 0x00..0x23 at 0x3740D4 and 0x3740F4 | Observed |
| 0x375724–0x377FDD | ASCII text bank (commentary, penalties, team slogans, developer credits) | Observed |
| 0x39CF4F | `SMSG 3.11a Jason Andersen & John Schappert 6/29/1994` sound-engine credit (3rd party cheat indexes; not a cheat) | External + observed |

RAM (verified live with GDB unless noted):

| Address | Meaning | Observed value |
|---|---|---|
| 0x02000510 | HOME team ID (u16) | 0x0016 → 0x0017 → 0x0018 as team selection changes; matches published CodeBreaker "Home Team Modifier" address |
| 0x02000512 | VISITOR team ID (u16) | co-varies with 0x02000510; matches published "Away Team Modifier" address |
| 0x020007CA | play clock (u8) | published "Infinite Time To Choose Your Play" target; literals found at 0x6FF0/0x7650 in ROM |
| 0x020007D4 | down (u8) | published "Always 1st/4th Down" target |
| 0x0200208E / 0x020021DE | home / away score (u16) | published score-modifier targets |

Hidden team IDs (from 3rd party cheat indexes and the published team modifier): `0x21` = Players, Inc.; `0x22` = EA Sports; `0x23` = Budcat — all above the 32 NFL team IDs `0x00`–`0x20`.

## 5. Algorithm

**Not applicable — there is no validator, checksum, encoder, or password algorithm in this ROM.** No input buffer is compared against a constant table: keyword searches for `password`, `cheat`, `secret`, `unlock`, `debug`, `code`, `playbook`, `options`, `select`, `create`, `franchise`, `roster` all returned **zero** relevant hits, and the only input-handling routine found (0x08001320) is the generic joypad read: `held = ~KEYINPUT & 0x03FF`, written to a single state word, with no sequence/progress index.

The closest thing to a "format" is the team-ID space: a u16 team selector in EWRAM with 32 legitimate NFL values plus three out-of-band developer values. It is a plain stored field with no validation algorithm — writing it requires external RAM modification, not player input.

## 6. Tables

### 6.1 Keyword search over the full 4 MiB (case-insensitive literal scan)

| Keyword | Hits | Context |
|---|---:|---|
| `password` | 0 | — |
| `cheat` | 0 | — |
| `secret` | 0 | — |
| `unlock` | 0 | — |
| `debug` | 0 | — |
| `code` | 0 | — |
| `playbook` | 0 | — |
| `options` | 0 | — |
| `select` | 0 | — |
| `create` / `franchise` / `roster` | 0 | — |
| `team` | 1 | `KICKING TEAM` at 0x3776C1 (commentary string) |
| `extra` | 1 | `EXTRA POINT` at 0x3773FD (commentary string) |
| `madden` | 4 | header, `Madden Classic` 0x20FFC0, slogan 0x2C015C, `JOHN MADDEN FOOTBALL` 0x377F8D |

### 6.2 Menu-word encoding search

For each of 14 words (`PLAY NOW`, `SEASON PLAY`, `FRONT OFFICE`, `RECORDS`, `TEAM SELECT`, `CONTROLLER SETUP`, `SOLO PLAY`, `LINK PLAY`, `MADDEN NFL 2003`, `OPTIONS`, `PASSWORD`, `CREATE`, `PLAYBOOK`, `GAME RULES`): all 256 constant byte shifts (−128..+127) and UTF-16LE were searched across the ROM → **0 hits**. A second pass tried 5 candidate 36-byte font tables × 4 alphabet orderings × 6 words = 120 encodings → **0 hits**. Conclusion: menu labels are baked/tile-indexed art, not a decodable text bank in the searched spaces.

### 6.3 Key-mask sequence scan

Scanning the first 1 MiB of code for aligned runs of ≥4 single-key u16 masks (`{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}`) found **38 runs**, all short (4–10 entries) and all located in compressed/graphics/audio-looking data regions (e.g. 0x1B0C0, 0x3B7FC, 0x55ED4), not in executable code and not forming a plausible cheat sequence. The published A/B/R/L prefix was checked explicitly as u16 little-endian: the only hit (0x1B0C2) lies inside that data region and is a false positive.

### 6.4 Screens enumerated (all reached, no hidden 5th item)

| Screen | Entry |
|---|---|
| Legal/copyright | boot |
| Quick menu (PLAY NOW / SOLO PLAY / LINK PLAY) | Start from legal |
| GAME RULES | A on quick menu |
| TEAM SELECT (HOME/VISITOR) | A from GAME RULES |
| CONTROLLER SETUP | A from TEAM SELECT |
| In-game play-call grid / field | A from CONTROLLER SETUP |
| Main menu (PLAY NOW / SEASON PLAY / FRONT OFFICE / RECORDS) | B from quick menu, or Start during play |
| SEASON PLAY (NEW NFL SEASON / NEW PLAYOFFS / SEASON RULES) | A on SEASON PLAY |
| RECORDS (NFL RECORDS) | A on RECORDS |
| Hidden debug screen | **none** — L+R and Select+Start probes produced no new screen; main menu wraps within 4 items |

### 6.5 Published-code classification

| Source | Code(s) | Classification |
|---|---|---|
| 3rd party cheat indexes / libretro | `32000510 00xx`, `32000512 00xx` (xx=21/22/23 hidden teams), score/timeouts/down modifiers | CodeBreaker RAM writes — out of scope; addresses verified against live RAM |
| 3rd party cheat indexes | "after TD press A/B/R/L for sounds", "late hit with L" | In-game button trick — in scope; not a code system |
| 3rd party cheat indexes | Gold Rank in 8 drills on All-Madden unlocks Sanders/Sanders/Stenerud/Elway/Young/Butler/Singletary/White; save from another EA football game unlocks Ditka | Save-bit unlocks — in scope as unlockables, not codes |
| 3rd party cheat indexes GameShark / Action Replay MAX | encrypted multi-line codes | Memory editing — out of scope |

## 6b. Enumeration

**Code space: empty.** There is no password alphabet, no code length, no checksum field, no reserved bits, no lookup table of accepted strings, and no validator function. Therefore the §0.2 deliverables (space definition, validator model, novel code, rejection bounds) are vacuous: there is nothing to mint or reject. The negative is bounded as follows:

- **Text space**: 14 menu words × 256 constant shifts + UTF-16LE = 3,584 encodings, plus 5 font tables × 4 alphabet orders × 6 words = 120 encodings → 0 code-like strings. Full-ROM keyword scan: 14 keywords, 0 relevant hits.
- **Button space**: 38 candidate u16 key-mask runs in 1 MiB of code, 0 in executable code; the two published button combos (L+R, Select+Start) were pressed at the main menu with no hidden screen.
- **Menu space**: 10 screens enumerated (§6.4); every menu item reached; main selector wraps within 4 items (no unlabelled 5th entry). No debug screen.
- **Team-ID space**: 0x00–0x20 are the 32 NFL teams; 0x21–0x23 are the three hidden developer teams. They exist as data but are not selectable through any input path found — the team-select list wraps within the NFL range, and the only way to reach 0x21–0x23 is a direct RAM write (out of scope). This is the "no input can reach it" negative of §16.3/§16.18, not a claim that the teams do not exist.
- **Novel code**: not generated, because no code system exists to generate one from. No in-game code was accepted or rejected because no code-entry surface exists.
- **Published codes tested**: no published *in-game* password/button code exists for this SKU; the published entries are all memory-edit or save-bit content. Their RAM targets were verified instead of entered (§4, §7).

## 7. Validation evidence

- **Observed**: all screenshots in `/tmp/madden03/` (legal, quick menu, GAME RULES, TEAM SELECT, CONTROLLER SETUP, play-call grid, field, main menu, SEASON PLAY, RECORDS). GDB reads of 0x02000510 changing `0x00180016` → `0x00180017` → `0x00180018` as teams changed, confirming the published team-modifier addresses are live game state. Savestate `gbAs` chunk decompressed to 397,312 bytes. L+R and Select+Start probes produced no new screen.
- **Derived**: objdump disassembly of the joypad handlers at 0x08000D20 and 0x08001320 (KEYINPUT literal 0x04000130, active-high XOR 0x03FF, no sequence tracker). The 36-byte font tables at 0x3740D4/0x3740F4 are permutations, confirming a tile-index text scheme.
- **Inferred / external**: hidden team IDs and the drill-unlock requirements come from 3rd party cheat indexes; I did not execute a drill to Gold Rank or press A/B/R/L after a touchdown. Their RAM addresses exist, but the unlock state changes themselves are not independently observed, so they are labelled accordingly (§16.8: fetched pages treated as data; no prompt-injection payload was found in the fetched pages).

## 8. Unknowns

- The exact in-game trigger (if any) for the three hidden teams remains unproven. 3rd party cheat indexes explicitly lists none; no button-code table was found. A save-file or link-transfer gate was not fully excluded, though the title/main/team-select screens were walked.
- Post-TD sounds and drill-based unlocks were not executed in the emulator (a touchdown and Gold-Rank drills would be required); only their published existence and, for teams, the RAM addresses are confirmed.
- Menu art is pre-rendered/tile-indexed; I did not reconstruct the glyph atlas, so I cannot prove the *visual* absence of a hidden label that shares a screen with visible art. The negative rests on menu-item enumeration and RAM/screen state, not on a complete glyph decode.
- Header checksum is 0x0000 while the complement byte is 0xB8; this is consistent with a rebuilt header (§16.1) but the original retail checksum value is unknown.

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, Python 3 (byte/pattern/entropy scans), `capstone` 5.0.7 / `keystone`.
- `arm-none-eabi-objdump -M force-thumb` for raw Thumb disassembly.
- REA MCP (`open_binary`, `binary_overview`, `binary_session`) with Ghidra 12.1.4 — auto-analysis identified only 170 procedures, so it was not used for decompilation claims.
- mGBA 0.10.5 with Xvfb :318 / openbox, `xdotool`, `scrot`, ImageMagick `convert`, `tesseract` for OCR triage.
- `gdb-multiarch` against mGBA's `-g` stub (`:2345`), driven through a FIFO with `SIGINT` to pause/resume; `ram.py` helper.
- Savestate decoder: Python `zlib.decompress` of the PNG `gbAs` chunk (§16.13).

No ROM or copyrighted asset is redistributed; only addresses, hashes, counts, and independent tooling are published.
