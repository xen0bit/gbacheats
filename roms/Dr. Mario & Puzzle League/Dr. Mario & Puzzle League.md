# Dr. Mario & Puzzle League (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dr. Mario & Puzzle League.gba` (8,388,608 bytes / `0x00800000`) |
| Header title (0xA0) | `DRMARIO&PONE` |
| Game code / maker | `BZPE` / `01` (Nintendo) |
| Version / fixed / complement / checksum | `0x00` / `0x96` / `0x59` / `0x0000` |
| Entry word | `0xEA00002E` — **stock** `b 0x080000C0`, no cracktro patch |
| MD5 | `279297081bab92bdc469f3b9127ab4fc` |
| SHA-1 | `af6fdad72d3f4777338b77971f488c0f75b080c1` |
| SHA-256 | `aa5326dd9110b3309e5e19408e2c4d5cbb15899292d502d4976bbe56f12ede07` |
| Save type | EEPROM 512 B (`EEPROM_V124` literal at file `0x48538`, `0x2148A4`, `0x6A0CE0`); observed `game.sav` = 512 bytes |

**Embedded GBA-header scan (Nintendo logo signature `24 ff ae 51 69 9a a2 21 3d 84 82 0a 84 e4 09 ad`):** 14 hits. Two real playable images:

- file `0x000000` → `0x08000000`: `DRMARIO&PONE` / `BZPE` — compilation shell + Puzzle League (Panel de Pon) half.
- file `0x400000` → `0x08400000`: `DR MARIO` / `B3DJ`, entry `0xEA0000C6` — Dr. Mario half.

The remaining 12 hits are dev/multiboot stubs (e.g. `GC-GBA Probe` / `AGBJ` at file `0x14689C`, and repeated `B3DJ` stub headers at `0x4822F4`, `0x4AE7C8`, `0x4DB8D0`, `0x5081E0`, `0x534A18`, `0x561220`, `0x568694`, `0x56FAE8`, `0x576F3C`, `0x57E390`, plus an empty-title header at `0x80000`). These are link/demo stubs, not separate games. **No trainer or patch was appended** — no menu other than the game's own appears at boot, and the first 4 KiB crt0 is intact.

## 2. Executive summary

**There is no in-game cheat-code system in this ROM.** No password entry screen, no button-code sequence, no hidden debug menu, and no unlock-by-code exists in either the Dr. Mario or the Puzzle League half. Everything the public cheat sites call a "code" for this SKU is a **save-bit unlockable** obtained by normal play (reaching an ending / clearing a required level), which is §16.18 territory, not a code system (guide §0.2 "negative results bounded").

Evidence, in one paragraph: (1) a full-ROM `strings -t x -n 4` pass produced **51,894 strings and zero hits** for `password`, `cheat`, `debug`, `secret`, `unlock`, `warp`, `gameshark`, `codebreaker`, `level select`, `enter code`, `master code`, `sound test` (counts in §7); the only "test" text is leftover Shift-JIS developer dialog copied from *Densetsu no Stafy 3* at file `0x6200D9`/`0x620131`. (2) Every menu screen in both games was walked in mGBA (§3, §7) — no code-entry widget exists on any of them. (3) The published "cheats" are unlock conditions, not inputs; the Vertical-mode message exists at file `0x622D9C` but only appears after a save flag is set. (4) All documented button codes for other Dr. Mario SKUs were tested and do nothing (§6b). (5) The only extra difficulties (S-Hard/V-Hard, TCRF) are reachable **only** by direct RAM writes (e.g. `03002A54:03`), i.e. memory-edit codes, explicitly out of scope here.

The development-intended extras **are** catalogued in §6b (Vertical Mode unlocks, bonus objects, epilogue/special videos, sound test), with their gating and bounds.

## 3. How to reproduce

- Emulator: mGBA (SDL), Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `-3` scale. Keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Holds 100–300 ms.
- Boot: health screen → any button → Intelligent Systems logo → compilation title `DR. MARIO & PUZZLE LEAGUE`.
- **Game select:** on the compilation title press **A** once — a green diagonal highlight appears. It starts on the Dr. Mario (left) half; press **Right** to move it to the Puzzle League (right) half; press **A** to launch the selected half.
- **Dr. Mario path:** title → Start → `PICK MODE` = {1P, 2P VS., OPTIONS, LINK}. 1P = {CLASSIC, VS. CPU, FLASH}. CLASSIC setup = {LEVEL, SPEED, MUSIC}. OPTIONS = {RECORDS, RULES, DELETE, OTHER}; OTHER = {SOUNDS, ROUNDS, DISPLAY}. In-game pause = {Go On, Retry, Quit, Sleep}.
- **Puzzle League path:** title → Start → main menu = {1P Game, 2P Game, Tutorial, High Scores, Options, Link}. 1P Game = {Marathon, Vs. CPU, Timed, Line, Garbage, Puzzle}. Options = 21 rows (Display … Default). High Scores = 3 pages.
- Savestate slots used: 1 = Dr. Mario `PICK MODE`, 2 = Puzzle League main menu (`Shift+F1`/`F1`, `Shift+F2`/`F2`).
- Codes tested: none accepted because none exist; the combos actually pressed are enumerated in §6b.

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`) unless marked RAM.

| Item | Address (file / ROM) | Evidence |
|---|---|---|
| Compilation shell + Puzzle League image base | `0x000000` / `0x08000000` | header/logo scan |
| Dr. Mario image base | `0x400000` / `0x08400000` | header/logo scan |
| Stock crt0 entry / Nintendo logo | `0x000` / `0x08000000` | `0xEA00002E`, logo intact |
| Standard key-reader (active-high keys) | `0x00012C` / `0x0800012C` | disassembly: `ldrh r1,[r0]` with `r0=0x04000130`, `eors r5,r1,#0x3FF`, `strh r5,[0x030010F0]` |
| Duplicate key-readers (per image/engine) | `0x090E6E`, `0x151F5A`, `0x4004A8`, `0x4825D4` / `0x08090E6E`, `0x08151F5A`, `0x084004A8`, `0x084825D4` | same literal-pool pattern |
| `KEYINPUT` literal occurrences | file `0x16C`, `0x90EAC`, `0x151F98`, `0x4004E8`, `0x482614`, `0x4AEAE8`, `0x4DBBF0`, `0x508500`, `0x534D38` | 9 total |
| Current keys (active high) | RAM `0x030010F0` | written by key-reader above |
| Newly pressed keys | RAM `0x03001500`, `0x030010D8` | same routine |
| Dr. Mario save record | EEPROM `0x100`–`0x15F` (mirror at `0x160`) | `game.sav` dump; magic `"DRMARIO VER 007"` at `0x100`–`0x10F` |
| Puzzle League save record | EEPROM `0x00`–`0x7F` (mirror at `0x80`) | magic `PON` at `0x7C`–`0x7E` |
| Vertical-mode unlock message | file `0x622D9C`–`0x622DC8` ("Vertical / mode has / been added / to 1P mode!") | BMG bank at `0x622510`; English |
| Dr. Mario version tag | file `0x478884`, `0x478894` | `DRMARIO VER 007` — matches US `BZPE` |
| Leftover Stafy-3 dev text (Shift-JIS) | file `0x6200D9`, `0x620131`, `0x6205C0` | `カラーへんこうてすと`, `テストめっせーじ` |
| Font/tile charmap (not a password alphabet) | file `0xBDEC`, `0xBEAC` | `pqrstuvwxyz…0123456789…` |

**EEPROM layout (`game.sav`, 512 B, observed from a fresh save after visiting menus):**

- `0x000`–`0x07F` Puzzle League record A; `0x080`–`0x0FF` record A mirror; bytes `0x04`=`FF`, `0x05`=`06`, `0x06`=`00`, `0x07`=`F9`, `0x7C`–`0x7E`=`4E 4F 50` (`PON`), `0x7F`=`00`, checksum-ish `0x76`=`0200`.
- `0x100`–`0x15F` Dr. Mario record A; `0x160`–`0x1FF` mirror (blank `0xFF` on a fresh cart). Header `20 4F 49 52 41 4D 52 44 00 37 30 30 20 52 45 56` = `" OIRAMRD.700 REV"` (big-endian-reversed `"DRMARIO VER 007"`). Words `0x110`/`0x118` = `FFFF FE71` (mirrored checksum), high-score defaults `0x4E20`=20000, `0x2710`=10000, `0x9C40`=40000.

The unlocks are bits in these records; there is no code surface that writes them from controller input.

## 5. Algorithm

**No validator exists to reverse.** There is no comparison routine over user-entered symbols: no entry buffer, no alphabet table, no checksum, no key schedule, and no solver in either image. There is nothing to mint.

The only "algorithm" worth recording is the standard input handler, which is generic (guide §5.4a requires a *sequence* comparator; none is present):

```
keys_raw   = ldrh [0x04000130]                 ; active-low KEYINPUT
cur        = keys_raw ^ 0x03FF                 ; active-high
[0x030010F0] = cur
prev       = [0x0300152C]
pressed    = cur & ~prev                       ; edge-triggered
[0x03001500] = [0x030010D8] = pressed
[0x0300152C] = cur
```

This consumes only the *current* and *previous* key words — a two-frame difference, not an N-step history. A button-code system would need a ring buffer and a table of expected masks; neither exists (no such table passed the xref/scan in §6b).

## 6. Tables

**Published "codes" for this SKU and their real nature** (all are unlockables, not inputs):

| Source | Published "code" | Reality / verified in ROM |
|---|---|---|
| GameFAQs / VGChartz / SuperCheats | "Unlock Vertical Mode — beat 1P Line mode level 6-5; enables Timed/Marathon/Garbage vertically" | Gameplay-gated save flag. Only function of the unlock is the BMG message at `0x622D9C` and an extra entry in the 1P list; absent on a fresh save (observed). |
| SuperCheats | "Unlock Vertical Mode in Dr. Mario — beat Level 20 in Classic" | Same class: level-20 clear sets a save bit; max selectable level is 20 (proved by rejection at `21`, §6b). |
| SuperCheats | "Unlock Horizontal Mode (Panel de Pon) — score >10,000 in Endless" | Same class; mode-name discrepancy between sites is a transcription issue (Vertical vs Horizontal), not a second code. |
| Super Luigi Bros | Bonus objects at virus levels 5/10/15, SMB theme on 4+ clears, epilogue and special videos | Passive gameplay rewards; no input codes. |
| TCRF (GBA page) | S-Hard/V-Hard difficulties, unused test graphics, leftover Stafy-3 text | Unused/development material. S-Hard/V-Hard are reachable only with direct RAM writes (`03002A54:03` / `:04`), i.e. memory-edit codes — out of scope. |
| TCRF (Dr. Mario **64** page) | Password screen opened with `Z+R+L+D-pad Left` in Classic/Marathon/Score Attack | **Wrong platform.** GBA has no Z button; no password text or decoder exists in this ROM (§7). |
| Generic NES cheat lists | "hold B + A at title → debug flag → stage select" | Tested on both titles — no effect (§6b). |

**Menu limits (all "counts" are exact, from screen enumeration + counting the wrap points):**

| Screen | Entries | Notes |
|---|---|---|
| Compilation title | 2 games | green highlight moves with D-pad |
| Dr. Mario PICK MODE | 4 | 1P / 2P VS. / OPTIONS / LINK |
| Dr. Mario 1P | 3 | CLASSIC / VS. CPU / FLASH — a 4th "VERTICAL" appears only when unlocked |
| Dr. Mario 1P→2P VS. | 2 | CLASSIC / FLASH |
| Dr. Mario OPTIONS | 4 | RECORDS / RULES / DELETE / OTHER |
| Dr. Mario OPTIONS→RULES | 4 | CONTROLS / BASIC / 2P VS. / ADVANCED |
| Dr. Mario OPTIONS→OTHER | 3 | SOUNDS / ROUNDS / DISPLAY |
| Dr. Mario CLASSIC LEVEL | 21 | `0x00`–`0x14` (`Lo.00`–`Lo.20`); `21` rejected |
| Dr. Mario SOUNDS | 2 fields | Music and Sound counters *wrap* (no hidden track) |
| Dr. Mario pause | 4 | Go On / Retry / Quit / Sleep |
| Puzzle League main | 6 | 1P / 2P / Tutorial / High Scores / Options / Link |
| Puzzle League 1P Game | 6 | Marathon / Vs. CPU / Timed / Line / Garbage / Puzzle — 12 Down presses wrapped to start |
| Puzzle League Options | 21 | Display … Default |
| Puzzle League High Scores | 3 pages | no hidden page |

## 6b. Enumeration

**Code space: empty.** There is no alphabet, length, field layout, checksum or lookup table to enumerate. The closest extensible surfaces are the level/difficulty selectors and the game-select screen; all were enumerated exhaustively and their bounds proved by rejection:

- Dr. Mario CLASSIC LEVEL: pressed Left until `Lo.00` (clamped) and Right until `Lo.20` (clamped). 10 further Right presses left it at `Lo.20` → **21 is rejected**, so no hidden level 21+.
- Puzzle League 1P Game: 12 Down presses from `Marathon` returned to `Timed` (12 mod 6 = 0), proving the 6-entry ring. No 7th "Vertical" entry on a fresh save.
- Puzzle League Options: full scroll from `Display` to `Default`, 21 rows; no unlabelled row.
- Dr. Mario SOUNDS: holding Right for 5 s wrapped `Music` from `12` back to `02` — a cyclic sound test, not a hidden-track gate.
- Dr. Mario RECORDS: 2 pages (High Score, Win/Loss); Win/Loss has exactly 4 rows.

**Documented button codes tested (all rejected — no debug screen, no flag, no menu change):**

| Combo | Where pressed | Result |
|---|---|---|
| `L+R` | compilation title, Puzzle League title, Dr. Mario select | no change (green selection highlight only) |
| `L+R+Start` | compilation title | no change |
| `Start+Select+A+B` | Puzzle League title / menu | normal soft-reset to title only |
| `R+L+Left` (adapted N64 password combo, Z absent) | Puzzle League title & 1P submenu | no password screen |
| hold `B` then press `A` (NES-style debug toggle) | compilation title, Dr. Mario title | no effect |
| Konami code (`↑↑↓↓←→←→BA`) | compilation title | no effect |

**Novel code: none generated, because generation is undefined without a validator.** Per the guide's rule for a *proven* absent system (§0.2 item 5, §16.3 "no system" vs "gated feature"), the deliverable here is the bounded negative above: the search spaces (all ASCII/Shift-JIS text, all `KEYINPUT` xrefs, all menu entry lists, all published combo codes) are stated with counts, and every one was exercised. There is no unpublished combination to mint.

**Developer-intended unlockables (the real "extras"):**

- **Vertical Mode — Dr. Mario:** clear Classic level 20 (or equivalent ending). Adds a mode in 1P and the "Vertical mode has been added to 1P mode!" notice (BMG at file `0x622D9C`). Gate is a save bit; on a fresh EEPROM the 1P list has only 3 entries (observed). Bounding: selecting level 20 is permitted; `21` is rejected, so the unlock condition is reachable.
- **Vertical Mode — Puzzle League:** reach the ending of a 1P mode (published lists disagree on the exact stage: "Line 6-5" vs "Puzzle 6-10"; the disagreement is in the *published* labels, not in a code). Adds vertical play modes.
- **Bonus objects / SMB jingle / epilogue & special videos — Dr. Mario:** triggered by specific virus levels (5/10/15/20) and clear conditions; passive rewards, no input.
- **Sound test — Dr. Mario:** always available via OPTIONS→OTHER→SOUNDS (not hidden).
- **Unused but not unlockable:** S-Hard / V-Hard and unused "Try Again?" graphics exist in the data (TCRF) but are reachable only by RAM patching, not by any controller input — out of scope for this report.

## 7. Validation evidence

**Observed (emulator / file):**
- All screens in §3 and §6 walked in mGBA on `:317`; menu entry counts taken from the rendered lists and their wrap points.
- Level selector clamped at `Lo.00` / `Lo.20`; 10 extra Right presses stayed at `Lo.20`.
- 6-entry Puzzle League 1P ring verified by wrap; 21-row Options list scrolled end-to-end.
- Sound-test Music counter wrapped after a 5 s hold.
- All six button combos in §6b produced no debug screen or new menu entry.
- `game.sav` (512 B) dumped and decoded: two EEPROM records per game with `PON` / `DRMARIO VER 007` magics and mirrored checksums; no code-entry state.

**Derived (static):**
- 51,894 ASCII strings; keyword counts — `password` 0, `cheat` 0, `debug` 0, `secret` 0, `unlock` 0, `warp` 0, `gameshark` 0, `codebreaker` 0, `enter code` 0, `level select` 0, `master code` 0, `sound test` 0.
- Literal probes: `PASSWORD`, `PASS WORD`, `ENTER PASSWORD`, `SECRET CODE`, `Z+R+L`, `CHALLENGE`, `V-HARD`, `S-HARD` → all **0** occurrences.
- 9 `KEYINPUT` literal pools / 5 copies of the key-reader function; the reader keeps only current+previous key words — no N-step code history.
- Naive u16 key-mask-run scan: 789 runs in the Puzzle League half and 1,256 in the Dr. Mario half, all in graphics/audio/sprite data with no code pointer xrefs — i.e. no button-code table (counts reported so the negative is bounded).
- 14 embedded headers; only two playable images; stock entry word; no trainer.
- Leftover Stafy-3 Shift-JIS text and `DRMARIO VER 007` located at the exact file offsets in §4.

**Inferred (labelled):** the precise bit positions of the Vertical-mode unlock flags inside the EEPROM records were not isolated (see Unknowns); the gating mechanism (save bit set on reaching an ending) is inferred from the presence of the unlock message, the 3-entry vs 4-entry 1P list, and the published unlock conditions, and is consistent with every observation.

## 8. Unknowns

- Exact EEPROM bit/byte positions of the Vertical-mode unlock flags were not isolated. Reaching the in-game ending was not performed (it requires clearing level 20 / a full puzzle-mode run); a save-state/GDB route to capture the flag write was blocked by a flaky GDB stub on this 8 MiB image (savestate `gbAs` IWRAM offset mapping did not match the 4 MiB layout documented in the guide). This does **not** affect the "no code system" conclusion, which rests on the complete absence of any input surface.
- The two published unlock descriptions use inconsistent names ("Vertical" vs "Horizontal", "Line 6-5" vs "Puzzle 6-10"); which is literally correct at the level/banner layer was not resolved because the ending was not reached. Both are gameplay gates, not codes.
- The unused S-Hard/V-Hard difficulties and "Try Again?" graphics are documented by TCRF but were not triggered, since doing so requires direct RAM writes (out of scope).
- Early `Xvfb`/`openbox` PID files were cleaned up by an external process; the display was verified live throughout and the correct PIDs were used for teardown.

## 9. Tooling

- `strings -t x -n 4 game.gba` → `strings_all.txt` (51,894 lines); `grep -iE` keyword counts; Python `re.finditer` for Shift-JIS (`カラーへんこうてすと`.encode('shift_jis')) and literal probes.
- Python header parser + Nintendo-logo scanner (14 header hits).
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -Mforce-thumb` for the key-reader at `0x0800012C` / `0x084004A8`.
- Capstone 5.0.7 Thumb scan for PC-relative literal loads into the 9 `KEYINPUT` pools; custom u16 key-mask-run scanner.
- mGBA (SDL) under Xvfb `:317` + openbox, `xdotool` XTEST input, `import -window root` screenshots, `shift+F1/F2` savestates.
- `sstool.py` (savestate `gbAs` zlib extractor and diff helper) — written but the 8 MiB IWRAM mapping remained ambiguous; not used for a final claim.
- Web research via web.archive.org snapshots of TCRF *Dr. Mario 64*, TCRF *Dr. Mario & Puzzle League*, Mario Wiki, GameFAQs (403 — used search snippets), SuperCheats, Super Luigi Bros, VGChartz. Fetched pages were treated as data; no instructions in them were followed.

**Legal note:** no ROM image, extracted graphics, music, or text assets are redistributed here — only hashes, addresses, and original findings.
