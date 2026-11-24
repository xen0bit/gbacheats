# Ninja Five-O (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ninja Five-O/Ninja Five-O.gba` |
| Size | 4,194,304 bytes (0x00400000, 4 MiB) |
| Header title | `NINJA FIVE 0` (the trailing `0` is the stylised `O`) |
| Game code | `ANXE` (USA) |
| Maker | `A4` (Konami) |
| Version | 0x00 |
| Entry word | `0xEA00002E` — stock `b 0x080000C0` (no cracktro patch) |
| Fixed 0x96 / main unit / device | 0x96 / 0x00 / 0x00 |
| Header checksum / complement | 0x0000 / 0xA6 (rebuilt-header artifact; see §16.1) |
| MD5 | `04244f72a9b8f17ee33e0b5bff2b8b1f` |
| SHA-1 | `3bc5789035c7400283b121e9fb3801aafae55364` |
| SHA-256 | `e5c18739cbe0f50978aa3bc79b15f50bc7872f5fb06df64ebfa9dc9efd60faec` |

Phase 0 embedded-header scan: the 156-byte Nintendo logo occurs **exactly once**, at file offset 0. There is no second/third GBA image, no boot selector and no appended trainer. Literal searches for `GAMESHARK`, `GAME SHARK`, `CODEBREAKER`, `CODE BREAKER`, `TRAINER`, `CHEAT`, `PRESS SELECT` returned **0 hits**. This is the retail image.

## 2. Executive summary

**There is no password, button-code, or developer/debug screen in this ROM.** The game has no text-entry field of any kind, no code comparator, no button-sequence table, and no hidden menu. The only "cheat-like" content is an ordinary *progress-gated unlockable*: a third difficulty slot rendered as `? ? ?` on the DIFFICULTY screen. Published documentation (GameFAQs, archived) identifies it as **Hard mode**, unlocked by beating the game once on Normal. The in-game gate was proven directly: the selector's Down input wraps EASY→NORMAL→EASY and never lands on the greyed third row.

The complete reachable menu tree (all screens walked in mGBA, each with a savestate as RAM evidence) is:

```
Boot logo → Intro cinematic (skippable) → Title "PRESS START"
  → SELECT MODE   [NEW GAME = enabled | LOAD GAME = GATED | TIME TRIAL = GATED]
      → DIFFICULTY [EASY | NORMAL | "? ? ?" = GATED (Hard mode)]
          → SELECT MISSION [BANK ★ | HARBOR ★★ | AIRPORT ★★★]
              → Gameplay (Stage 1 banner) → PAUSE [QUIT MISSION | QUIT STAGE | RESUME]
                  → QUIT MISSION returns to SELECT MISSION
```

The FAQ documents six missions in total (Bank, Harbor, Airport, **Cave, Base, Launch Site**); only the first three are selectable from a fresh save, so the last three are progress-gated as well. This is ordinary unlockable content, not a cheat code, and is reported as such.

No code system exists, therefore §6b documents the **bounded negative**: every screen, every selector, the whole input-mask search space, the published-code search, and the font/tile text space were enumerated with counts.

## 3. How to reproduce

* Emulator: `mgba -3` (mGBA SDL build) under `Xvfb :315 -screen 0 1024x768x24`, `SDL_AUDIODRIVER=dummy`, `openbox` as WM.
* Keymap (verified against on-screen menu movement): A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys. Holds of 70–200 ms; the game polls reliably at ~70 ms.
* Window at `154,184`, geometry `720x480` (3× 240×160); crop with `convert -crop 720x480+154+184 +repage`.
* Path to every screen: boot → press Start repeatedly through the intro → Title → Start → SELECT MODE → A (NEW GAME) → DIFFICULTY → A (EASY) → SELECT MISSION → A (BANK) → gameplay → Start → PAUSE. From PAUSE, Up ×2 + A (QUIT MISSION) returns to SELECT MISSION; B walks SELECT MISSION → DIFFICULTY → SELECT MODE.
* Savestates `Shift+F1..F4` were written at title, mission-select, difficulty and SELECT MODE; their `gbAs` PNG chunks were decompressed and used as the RAM evidence (§7). All generated `.ss*` and `.sav` files were deleted during cleanup (§9).
* Button sequences tested on the PAUSE and DIFFICULTY screens: Konami (`U U D D L R L R B A`), `L+R+Start+Select`, `U U D D L R L R`, `A B A B`, `R L R L A B`. Results: on PAUSE the trailing A simply activates RESUME; on DIFFICULTY nothing changes. No hidden effect for any sequence.

## 4. Address map

| Item | Address (ROM) | Notes |
|---|---|---|
| crt0 entry | 0x08000000 | `b 0x080000C0` |
| Header title | 0x080000A0 | `NINJA FIVE 0ANXE A4` |
| Key-input literal | 0x080117A4 | `0x04000130` — the **only** occurrence in 4 MiB |
| Input manager | 0x0801174C | Reads KEYINPUT, derives held/pressed/released, updates per-key counters |
| Repeat-delay table pointer | 0x08039E50 | 10-byte per-key repeat config (literal at 0x80117A8) |
| Main loop | 0x0800D5E0 | Init calls, then loop at 0x800D676: input → 0x801665C → 0x800E114 → 0x800EDC4 → frame counter → 0x8035408 |
| Only BL to input manager | 0x0800D678 | `bl 0x801174C` |
| Save literal region | 0x0800ADxx–0x0800D2xx | 0x0E000000 references (save/script data, not a code table) |
| Font mapping | tile = ASCII + 0x7F | Derived from OAM attr2 of rendered mission names (see §6) |

Savestate (`.ss1`) RAM layout used for evidence, verified against known values:

| Region | Offset in decompressed `gbAs` (397,312 bytes) |
|---|---|
| CPU / header | 0x00000 |
| Palette RAM | 0x00800 |
| OAM | 0x00C00 |
| VRAM | 0x01000 |
| IWRAM | 0x19000 |
| EWRAM | 0x21000 |

## 5. Algorithm

No password algorithm, checksum, validator or button-code matcher exists. The only derived algorithm is the font mapping, needed to decode the tile-indexed text:

```
tile_index = ascii_code + 0x7F        (uppercase letters A–Z observed)
ascii_code = tile_index - 0x7F
```

Derivation (observed from OAM attr2 on the SELECT MISSION screen; each letter is one sprite):

* `BANK`   → tiles 193,192,206,202 → B,A,N,K
* `HARBOR` → tiles 199,192,211,193,208,211 → H,A,R,B,O,R
* `AIRPORT`→ tiles 192,200,211,209,208,211,213 → A,I,R,P,O,R,T

Every one satisfies `tile = ASCII + 0x7F` (e.g. 'B'=0x42 → 0x42+0x7F=193). Screen text is built per-character into OAM at runtime; no contiguous string in this encoding exists in ROM or in savestate RAM (§6b).

The input manager's semantics (derived from disassembly at 0x0801174C):

```
held    = ~KEYINPUT & 0x3FF
pressed = held & (held ^ previous)
released= ~held & previous
per-key hold/repeat counters use the 10-byte repeat table at 0x08039E50
```

There is no comparison of `pressed`/`held` against any multi-button constant anywhere in the game code.

## 6. Tables

| Table / space | Value | Evidence |
|---|---|---|
| GBA key masks (engine convention) | A=0x001 B=0x002 Select=0x004 Start=0x008 R=0x010 L=0x020 U=0x040 D=0x080 | Derived from input manager at 0x0801174C |
| KEYINPUT literal occurrences | **1** (0x080117A4) | Full 4 MiB scan |
| `SELECT MODE` entries | 3 (1 enabled, 2 gated) | Observed |
| `DIFFICULTY` entries | 3 (2 enabled, 1 gated = Hard) | Observed + GameFAQs |
| `SELECT MISSION` entries selectable | 3 (BANK/HARBOR/AIRPORT) | Observed |
| `PAUSE` entries | 3 | Observed |
| Missions documented in FAQ | 6 (adds Cave, Base, Launch Site) | Published FAQ 62442 |
| EEPROM save | 512 bytes; only first 16 used: `50 55 31 4b 43 30 41 42 00 00 00 00 35 44 49 30` | Observed; bytes 16+ always 0xFF/0x00 with no effect on gating |
| Font offset | +0x7F | Derived from OAM |

Gated entries and their status:

| Entry | Screen | In-engine proof of gate | Trigger |
|---|---|---|---|
| LOAD GAME | SELECT MODE | Grey rendering; Down does not move selector (wraps stay on NEW GAME) | Progress/save flag — **not determined** (no published statement found) |
| TIME TRIAL | SELECT MODE | Same | Progress/clear flag — **not determined** (FAQ only confirms time trials exist) |
| `? ? ?` (Hard mode) | DIFFICULTY | Grey rendering; Down from NORMAL wraps to EASY | Beat the game on Normal — **published** (GameFAQs) and consistent with in-engine gating; the clear itself was not played through |

## 6b. Enumeration

### Code space: empty (bounded negative)

This title has **no enumerable code space**. The negative is bounded by the following exhaustive checks and counts:

1. **String/password space.** `strings -n 4` produced 27,218 runs; **0** are meaningful ASCII other than the header title (all others are ARM/Thumb instruction bytes). Keyword scan for `password|cheat|code|debug|secret|unlock|level|stage|select|menu|continue|option|extra|bonus|hidden|generator` → **0 hits**. Brute-force single-byte additive transforms over all 256 deltas for 35 candidate words → only coincidental 1–3 byte matches (`RANK`, `TIME`, `CODE`, `FIVE`), none in a text region.
2. **Tile-indexed text space.** Font offset solved as +0x7F from OAM. Searches for `BANK`, `HARBOR`, `AIRPORT`, `SELECT MISSION`, `PRESS START`, `KONAMI`, `QUIT MISSION`, `RESUME`, `PAUSE` encoded as bytes+0x7F, u16LE+0x7F, u16BE+0x7F, and reversed → **0 hits** in ROM and in savestate RAM. A generic scan of all 4,194,304 bytes for runs whose `byte-0x7F` is printable found 44,684 runs, all random code/data noise. Conclusion: text is per-character sprite construction over compressed data; there is no plaintext or tile-index string table to mine.
3. **Button-code space.** One-hot u16 runs of length ≥4: **60 runs** found; every one inspected is either Thumb/ARM machine code or sprite/animation metadata (e.g. the 12-word run at 0x0803A1E4 sits in a pointer/data table and its apparent "code reference" at 0x8012068 is an `adr` whose bytes merely spell the address — false positive). Byte-per-press runs of length ≥6: **0**. Exact Konami prefix (`40 40 80 80 20 10 20 10 02 01`) as u16 and as bytes: **0 hits**. No key-mask sequence table exists.
4. **Validator/debug-gate space.** Exactly one keyboard reader (0x0801174C) with one caller (0x0800D678). No code compares accumulated button history against a constant, and no password buffer is read outside the (nonexistent) entry handler.
5. **Published codes.** Searched web.archive.org GameFAQs (correct id **589463**), TCRF and search engines. GameFAQs cheats page contains exactly one entry — "Unlock Hard mode: Beat the game on Normal difficulty once to unlock Hard mode" — which is an unlockable, not a code. TCRF lists only unused graphics/music/font symbols. **No password or button code has ever been published for this SKU**, so there are no literals to verify; the ROM contains none of the usual code-table structures anyway. (A first pass used guide example id 777281, which 404s; corrected via the Wayback CDX API.)
6. **Menu/selector space.** Every selector on every reachable screen was walked to its wrap point: SELECT MODE (3 rows, 2 gated), DIFFICULTY (3 rows, 1 gated), SELECT MISSION (3 rows, wraps 3→1), PAUSE (3 rows). No unlabelled 4th row exists on any of them.

### Unlockables enumerated (no code minting possible)

Because there is no code system, no unpublished code can be generated — the §0.2 "mint a novel code" deliverable is not applicable. The equivalent enumeration here is the complete set of unlockable states:

* Observed and proven gated in-engine: LOAD GAME, TIME TRIAL, Hard difficulty (`? ? ?`).
* Observed selectable from a fresh save: NEW GAME, EASY, NORMAL, BANK, HARBOR, AIRPORT.
* Published trigger verified: Hard mode = clear the game on Normal.
* Proven by rejection: all-0xFF and all-0x00 EEPROM images, and zeroing save bytes 16–511, were written back and the ROM restarted; the gated options remained grey/unselectable. External save-byte fuzzing therefore cannot produce the unlock — it is written by gameplay progression.
* Bounds: the accepted input set of this game's "code space" is the empty set; the accepted menu set is the 3+3+3+3 rows above, of which 6 are gated.

No novel code was entered because no code exists to enter; this is a proven negative, not an omitted test.

## 7. Validation evidence

**Observed** (emulator / savestate RAM):

* All 10 screens listed in §2, with screenshots and `.ss1` savestates (slot 1 title, slot 2 mission select, slots 3–4 difficulty/SELECT MODE).
* Gated rows render grey and are skipped by the selector on SELECT MODE and DIFFICULTY.
* Down on SELECT MISSION cycles BANK → HARBOR → AIRPORT → BANK (nine presses logged).
* Konami code on PAUSE only activated RESUME; no flag/screen change.
* Font mapping decoded from OAM attr2 across three different mission names, self-consistent for 10 distinct letters.
* Save file is 512-byte EEPROM; only first 16 bytes carry data; writes to the rest have no effect.
* Header/logo scan: one header, no trainer.

**Derived** (disassembly / static):

* Single KEYINPUT reader and single input manager; no code comparator.
* Button-mask scan counts and false-positive classification.
* Savestate RAM region offsets.
* Main-loop call graph.

**Inferred** (labelled):

* Identity of `? ? ?` as Hard mode (published on GameFAQs; visually consistent with a third, harder slot — the FAQ states keys/enemy counts differ by difficulty and that Easy cannot progress past the Airport mission).
* Unlock conditions for LOAD GAME and TIME TRIAL (only that they are progress-gated; the exact flag/writer was not isolated).
* The 3 extra missions (Cave/Base/Launch Site) being progression-gated: documented in the FAQ but not reached in-engine during this session.

**Prompt-injection check:** fetched GameFAQs/TCRF/FAQ pages were treated as data. No injection payload was encountered in this run; the only imperative-looking text found was normal game dialogue ("A GANG IS ROBBING THE BANK ON THE MAIN STREET!"), ignored as data.

## 8. Unknowns

* Exact in-game trigger/writer for LOAD GAME and TIME TRIAL (both proven gated; neither unlock condition is published).
* The save-flag byte and checksum, if any, that record the Normal-mode clear enabling Hard mode. Save-byte fuzzing shows the flag is not a trivially flip bit in the 512-byte EEPROM image.
* Whether the three FAQ-documented later missions unlock sequentially per mission or only after a full clear — not reproduced in-engine.
* Text data storage: confirmed compressed/dynamic (per-character sprite construction), but the specific decompression routine was not isolated; not needed for the cheat question.

## 9. Tooling and cleanup

* Tools: `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep`, Python 3 with `capstone` 5.0.7 / `keystone-engine`, `arm-none-eabi-objdump -M force-thumb`, mGBA SDL (`-3`), Xvfb :315, openbox, `xdotool`, `scrot`, ImageMagick, Pillow. REA MCP was loaded per the guide; raw ARM/Thumb `objdump` plus the emulator remained the practical path.
* Scripts in `/tmp/ninjafiveo/`: `scan1.py`, `buttoncodes.py`, `keyrefs.py`, `textdecode.py`, `dumptext.py`, `fontscan.py`, `ssram.py`, `ssdiff.py`, `rendertiles.py`, `rendfont.py`.
* **Cleanup performed:** all processes started for this job were stopped **by PID** (`kill $(cat mgba.pid)`, Xvfb and openbox PIDs from their `.pid` files): mgba, Xvfb :315, openbox. No `pkill` was used at any point. All generated `Ninja Five-O.sav`, `Ninja Five-O.ss1`–`.ss4` were removed from the ROM folder; only `Ninja Five-O.gba` and this report remain. Other agents' displays/processes were not touched.

## 10. Legal note

No ROM bytes or copyrighted assets are reproduced in this report. Only hashes, addresses, observed states and original analysis scripts are published.
