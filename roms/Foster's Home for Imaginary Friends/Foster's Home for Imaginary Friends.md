# Foster's Home for Imaginary Friends (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Foster's Home for Imaginary Friends.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `FOSTERS HOME` |
| Game code | `BFYE` |
| Maker code | `4Z` (Crave Entertainment / published by Crave; developed by Collision Studios) |
| Version | 0x00 (Rev.00), region USA |
| Entry branch | `0xEA00002F` (stock), fixed byte `0x96` present, header checksum field `0x0000` (normal for a commercial ROM), complement `0x2E` |
| MD5 | `1207a415c9acfbd206e5580f34e73ba2` |
| SHA-1 | `9dcfddf55a2a60db2946e52959d82cb53c63e7df` |
| SHA-256 | `d47b8b19bd813ec54cf34560915286125e5cf9f9d9db9003f69fbb00b0837af2` |

**Phase 0 findings:** single Nintendo-logo hit at file offset `0x000004` — this is a single, unmodified retail image, **not** a multi-game cart, cracktro, or trainer-patched ROM. The entry word and first 4 KiB are stock ARM crt0 (confirmed by disassembly). No patch/trainer detected. In-game legal screen reads "LICENSED BY NINTENDO" (observed in mGBA).

## 2. Executive summary

**This GBA game has no developer-intended in-game cheat system.** There is no password entry screen, no button-code matcher, no hidden debug/level-select menu, and no unlock code list in the ROM. The three minigames (Wack-A-Bee, Skee-Ball, Paddleball) are unlocked by collecting in-game Game-Hive tickets, not by codes.

The published "cheats" for this title fall into two out-of-scope / wrong-SKU categories, both verified:

1. **CodeBreaker / GameShark SP / Xploder memory-edit codes** (3rd party cheat indexes) — six codes: master, Access All Stages, Have 100 Tickets, Infinite Health, Unlock Paddleball / Skee-Ball / Wack-A-Bee. These are external memory writes, explicitly excluded by the engagement scope. Decrypting them (Parasyte CBA algorithm) yields written values 0x000D (stage count), 0x0064 (=100 tickets), 0x1000, and three `0x0001` unlock bytes whose low-24-bit addresses cluster at `0x02005551`–`0x02005553`; those RAM bytes are `0x00` in a fresh game (savestate read, §7). This confirms they are memory patches to the game's own unlock/ticket variables, not in-game codes.
2. **PC/web-game codes from a different SKU** — `VIKING`, `OWLFLY`, `CREATE`, `BIGTOE`, `DVDBUD`, `IGLOOS`, `TOASTY`, `CANVAS`, `ROCKON`, `EGGLIT`, `VROOOM`, `HOLLOW`, `RIBBED`, `FOSSIL`, `HANGER`, `EAGLES`, `QUARRY`, `CAVERN`, `ELDEST`, `SECRET` are for *Foster's Home for Imaginary Friends: Big Fat Awesome House Party* (PC / Cartoon Network web game, "Notey" text-entry), not the GBA action-adventure. **All 20 literals are absent from this ROM** in ASCII, +0x20, UTF-16LE/BE, and constant XOR/add encodings. The fan-forum "secret codes" thread that mentions hat/buddy codes is explicitly about the PC/web game. A German aggregator's claim of an `IMAGINE` "password screen" code is SEO-generated (wrong publisher/date) and `IMAGINE` is absent from the ROM.

The one SEO-style claim specific to a "password screen" (`IMAGINE`) was tested and rejected at the literal level. Every reachable screen was walked in mGBA with savestate/RAM evidence (§3, §7); the complete UI text inventory is tile-indexed (§8) and was enumerated visually on every screen. Keyword search of the entire 4 MiB image in multiple encodings returns **zero** password/cheat/debug strings and only script-dialogue or audio-banner false positives (§6).

## 3. How to reproduce

**Emulator:** mGBA (SDL build), `SDL_AUDIODRIVER=dummy`, started as `mgba -g -3 <rom>` on `DISPLAY=:316` under Xvfb + openbox. Keymap used (verified against on-screen cursor movement): A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys. Holds of 100–300 ms; cursor highlight in this game blinks, so a frame may show no highlight.

Exact menu path (all screens reached and screenshotted):

```
Boot -> Crave logo -> "LICENSED BY NINTENDO" legal screen -> Start
Main Menu:  Start | Continue | Options | Game Hive
  Start        -> New Game 1 | New Game 2 | New Game 3 | Main Menu
  Options      -> Sound | Music | Credits | Main Menu
  Game Hive    -> Wack-A-Bee [grey] | Skee-Ball [grey] | Paddleball [grey] | (Main Menu label); B = back
  New Game 1   -> "HOUSE OF BLOO'S" title card -> story dialogue -> in-game
In-game HUD:    Bloo portrait, 3 candy health, key/ticket icons
  Start(pause) -> Continue | Options | Main Menu
  pause Options-> Sound | Music | Back
In-game button probes: A, B, L, R, Select, Start, and 9 candidate chords/sequences (§6b)
```

Published codes tested against the ROM (none entered in-game because all are out of scope): the 6 CodeBreaker memory writes above, the 20 PC-game literals, and `IMAGINE`. No in-game code-entry surface exists on any of the ~12 screens walked, so there is no screen on which to type a code.

**RAM verification method:** the mGBA build's GDB stub did not bind a port, so §16.13 savestate-diffing was used. mGBA `.ss1`–`.ss9` files are PNGs with a zlib-compressed `gbAs` chunk; `zlib.decompress` yields a 397,312-byte state with IWRAM at file `0x19000` and EWRAM at `0x21000` (validated against the method in the guide). Savestates were taken on each screen and before/after each button probe.

## 4. Address map

| Item | File offset | ROM address | Notes |
|---|---:|---:|---|
| ROM header | 0x000000 | 0x08000000 | Title `FOSTERS HOME`, code BFYE, maker 4Z |
| crt0 entry | 0x0000C0 | 0x080000C0 | Stock ARM reset handler |
| Button-icon → key-mask table | 0x030380 | 0x08030380 | u16 table; values are active-high key masks (A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200). **Not a cheat table.** |
| Table accessor | 0x02F4A8 | 0x0802F4A8 | Thumb: `ldrb` from script table → `lsls #1` → `ldrh [0x08030380]`; script UI button-icon lookup (0x0802F4B4 literal) |
| ASCII story/script bank | 0x2A75FC–0x2B9xxx | 0x082A75FC… | Plain NUL-terminated dialogue (e.g. `Wack-A-Bee` at 0x2A952A, `Game Hive` at 0x2A95F0, `unlock games` at 0x2A9617) |
| Audio engine banner | 0x3DD6F8 | 0x083DD6F8 | `Shin'en Multimedia. Code: B.Wodok` — known false positive (GAX engine) |
| Uncompressed graphics asset | 0x287FA4… | 0x08287FA4… | VRAM tiles from the Game Hive screen match here byte-for-byte |
| EWRAM unlock bytes (from out-of-scope CB codes) | — | 0x02005551–0x02005553 | `0x00` in fresh game; targeted by Unlock Wack-A-Bee / Skee-Ball / Paddleball memory writes |
| EWRAM ticket variable (decoded CB target) | — | ~0x02000F74 | `0x00` in fresh game; "Have 100 Tickets" writes 0x64 (low-confidence high byte) |
| IWRAM / EWRAM savestate offsets | file 0x19000 / 0x21000 | 0x03000000 / 0x02000000 | Used for all RAM evidence |

## 5. Algorithm

**No password/checksum validator exists to reverse.** There is no input buffer that is ever compared against a constant: ROM-wide counts of `password`, `cheat`, `debug`, `level select` are all zero (§6), no code-entry screen exists on any walked screen (§3), and no button-code table exists (§6b).

The only relevant decoding performed was:

1. **Script text bank** — plain ASCII, NUL-terminated, read directly; 54 `secret` hits all decode to story dialogue about the "Secret Door" (a plot device), and the single `unlock` hit is dialogue "we can unlock games at the Game Hive."
2. **Script button-icon table** — function `0x0802F4A8` indexes a u16 table at `0x08030380` to map a script byte to a key mask used to draw button glyphs in dialogue (e.g. `select`). This is a UI helper, not a cheat matcher; it is the sole structure in the ROM that resembles a key-mask table, and its purpose is proven by its caller and values.

## 6. Tables

**Keyword census — whole 4 MiB ROM, case-insensitive (Observed):**

| Term | ASCII | +0x20 shifted | UTF-16LE | Classification |
|---|---:|---:|---:|---|
| password | 0 | 0 | 0 | none |
| cheat | 0 | 0 | 0 | none |
| code | 1 | 1 | 0 | `0x3DD72F`, audio-engine banner — false positive |
| debug | 0 | 0 | 0 | none |
| level select | 0 | — | — | none |
| secret | 54 | 54 | 0 | all story dialogue ("Secret Door") |
| unlock | 1 | 1 | 0 | `0x2A9625`, story dialogue |
| ticket | 5 | — | — | Game-Hive ticket storyline |
| enter | 2 | 2 | 0 | story dialogue |

**Published-code verification (all out of scope / wrong SKU, none usable in-game):**

| Source | Codes | Verdict |
|---|---|---|
| 3rd party cheat indexes | 6 CodeBreaker/GameShark SP/Xploder codes | Memory writes, excluded by scope. Decrypted targets documented in §2/§4. |
| 3rd party cheat indexes / awesomehouseparty.fandom / fansite (20 codes: VIKING, OWLFLY, … SECRET) | PC/web "Big Fat Awesome House Party" | Wrong SKU; 0/20 literals present in this ROM under ASCII, +0x20, UTF-16, XOR/add, or letter-shift. |
| 3rd party cheat indexes (`IMAGINE` "password screen") | 1 claim | Literal absent (0 hits); source metadata is wrong (publisher/date). Rejected. |

## 6b. Enumeration

Because **no code system exists**, the §0.2 space is empty (0 accepted in-game codes). The negative is bounded by exhausting the three spaces that could have hosted one:

1. **Text space (exhaustive):** entire 4 MiB scanned for 12 keywords × 4 encodings (ASCII case-insensitive, `a-z`→`A-Z` +0x20, UTF-16LE, UTF-16BE, plus per-string constant-add/XOR brute force k∈[0,255] and short repeating keys of length 1–4). Result: 0 password/cheat/debug/level-select/code-entry strings. The 1 `code` hit is the GAX audio banner; the 54 `secret` hits are one repeated dialogue phrase; `Collision Studios`, `Philippe Erwin`, `Craig Stewart` and all menu labels are absent as ASCII — confirming UI text is font/tile-indexed (documented as an Unknown, §8). UI inventory was therefore taken visually from every screen (§3).
2. **Button space (exhaustive over structure):** raw scan of every 2-byte-aligned u16 for runs of ≥5 values in `0x0001..0x03FF` (the active-high 10-bit GBA key-mask domain) → 3,478 runs; only 8 had ≥3 single-button masks. All 8 were dumped and classified: the only plausible-looking one, `0x08030382`, is the script button-icon table of §5 (accessor proven at `0x0802F4A8`); the rest are arithmetic/compressed-data noise. Dynamic probe: 9 candidate chords/sequences pressed from a clean main-menu savestate with pre/post RAM diffs — `L+R`, `L+R+Start`, `L+R+Select`, `Start+Select`, `Start+Select+A+B`, `L+R+A+B`, the 10-press Konami sequence, `L,L,R,R,L,R,L,R`, `A,B,A,B` — every one produced only the normal volatile IWRAM/EWRAM deltas (animation counters, audio state, tilemap) and **no new screen, no persistent flag, no hidden menu** (post-probe screenshot remained the main-menu/New-Game flow).
3. **Published-space (exhaustive over available lists):** 6 memory-edit codes + 20 wrong-SKU codes + 1 fabricated "IMAGINE" claim all tested at literal level; 0 in-game codes found.

**Novel code / minted code:** not applicable — with no validator and no accepted set, there is nothing to mint, and §0.2's "generate a novel accepted code" requirement is satisfied only for games that have a code system. **Bounds proven by rejection:** the out-of-scope `IMAGINE` "password" claim is rejected (0 literals), and the 20 PC-game codes are rejected (0 literals). No in-game input ever reached a validator, so no in-game rejection screen exists to demonstrate.

## 7. Validation evidence

- **Observed (emulator):** all ~12 screens listed in §3 reached and screenshotted on `DISPLAY=:316`; Game Hive minigames visibly greyed/locked; pause menu has only Continue/Options/Main Menu; ASCII credits scroll (Collision Studios, Philippe Erwin, Craig Stewart, Dean Lee, …); soft-reset attempt and 9 button probes produced no hidden screen.
- **Observed (RAM):** mGBA savestates parsed per §16.13 (397,312-byte `gbAs` payload). Fresh-game EWRAM `0x02005551`–`0x02005553` and `~0x02000F74` are all `0x00` (match the out-of-scope CB unlock/ticket writes). Controlled UP-press diffs changed ~450 RAM bytes in IWRAM/EWRAM (animation/audio/tilemap), consistent with ordinary menu redraw — no stable cheat flag. A single D-pad move on the Game Hive screen changed EWRAM `0x020005C8`–`0x02000640` (tilemap) and `0x02000ACC`, `0x02000E94` (state/timers); no flag word controlling a hidden screen was found.
- **Derived (static):** ROM header/logo scan proves a single unpatched image; disassembly at `0x0802F4A8` proves the `0x08030380` table is a script UI helper; keyword census across encodings; CB decryption of the six memory-edit codes yields plausible RAM targets/values; VRAM tiles from the Game Hive screen match uncompressed data at `0x0287FA4`.
- **Inferred (labelled):** exact high bytes of the decrypted CodeBreaker addresses are uncertain (the CBA implementation reproduced values correctly but the top address byte differs from the expected `0x02`); the addresses are reported as low-24-bit clusters only. The PC/web-game codes' *effects* (Viking hat etc.) are irrelevant to this SKU and were not exercised.

## 8. Unknowns

- The menu/credits text in this game is **font/tile-indexed** — menu labels and credit names are not stored as ASCII in any encoding tested, and the simple per-byte/XOR/add/glyph-offset decodings all failed. The font bitmap is present uncompressed in ROM (VRAM tiles correlate at `0x0287FA4`), but the full ASCII/tile-index mapping table was not reversed. UI text was therefore enumerated visually on every reachable screen instead of from a decoded bank; this does not affect the negative conclusion because every screen was walked and no code-entry surface exists on any of them.
- It was not possible to enter the out-of-scope CodeBreaker codes (they require an external cheat device / emulator memory editor, excluded by scope), so their *effects* were verified only at the literal/address level.
- The exact Byte-3/address decryption of the CB codes is approximate (see Inferred above).
- No battery-save file was produced during the ~12-screen walk within the time budget, so no save-resident unlock flag was searched for a code-like setter; the in-game unlock path (tickets) is the documented one in the script bank.

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo` — Phase 0/1 fingerprinting and keyword census.
- `python3` + `re`, `struct`, `capstone` 5.0.7, Pillow — multi-encoding string scans, u16 key-mask table scan, Thumb literal/BL scans, VRAM tile rendering, CBA decryption (`cbdecrypt.py`).
- `arm-none-eabi-objdump -M force-thumb` — disassembly of `0x0802F4A8`.
- `Xvfb :316`, `openbox`, `mgba` (SDL, `-g -3`), `xdotool` (XTEST), `scrot`, ImageMagick — Phase 2 screen walk (~56 screenshots, key frames read via the read tool).
- Custom helpers in `/tmp/fosters/`: `gba.py` (input/capture), `ssd.py` (gbAs savestate parser), `probe.py` (button-sequence RAM-diff harness), `render_vram.py`/`render8.py`, `cbdecrypt.py`.
- REA `reverse-engineer-anything` skill loaded and its evidence discipline (Observed/Derived/Inferred, prompt-injection-as-data) applied throughout; fetched cheat pages were treated as untrusted data. No prompt-injection payload was encountered in the fetched content.

**Legal note:** no ROM image, graphics, music, or game text is redistributed here; only hashes, addresses, algorithms, and the analyst's own tools/observations are published.
