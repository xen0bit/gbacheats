# Silent Scope (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Silent Scope/Silent Scope.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `SILENT SCOPE` |
| Game code | `AIPE` (USA); second header `AIPJ` (Japan) |
| Maker | `A4` (Konami) |
| Version / fixed / complement / checksum | `0x00` / `0x96` / `0x54` / `0x0000` |
| Entry branch word | `0xEA00002E` → stock crt0 at `0x080000C0` |
| MD5 | `164e42954fe047552701ff62836642ae` |
| SHA-1 | `22d8d57ac4b274933adb492fee2b32bbc7b6e9bb` |
| SHA-256 | `256e139f304ded2e258ba5ce6f29c57b9075a76ccc6e7c6c1f7c967fa9be495c` |

**Embedded-header scan (full 156-byte Nintendo logo, every offset):** exactly **2** hits:

* file `0x00000000` → `0x08000000`, title `SILENT SCOPE`, code `AIPE` (boot image).
* file `0x007004C0` → `0x087004C0`, title `SILENT SCOPE`, code `AIPJ`, same entry word, followed by a complete second crt0 (ARM memory-copy loop, literals `0x04000120`, `0x020000AC`, `0x020002B0`, `0x02038000` at file `0x700660`). This is a real second (Japanese) image, not a multiboot stub. No boot selector was observed in the retail path; the second image is dormant in normal play.

No scene cracktro, appended trainer, or patched entry point: the entry word and first 4 KiB are stock ARM crt0. Header complement sum over `0xA0..0xBD` is `0xE7` rather than `0x00`, and the 16-bit header checksum is `0x0000` — the usual rebuilt-header artifact, not evidence of a cheat patch.

Save hardware: `EEPROM_V122` string at `0x6F6EAC`; mGBA creates a 512-byte `Silent Scope.sav`.

## 2. Executive summary

**There is no password, button-code, or hidden debug menu system in this GBA SKU.** The only 30-symbol alphabet in the ROM (`ABCDEFGHIJKLMNOPQRSTUVWXYZ.&? ` at `0x08700320`) is the *ranking name-entry* alphabet; its only code consumer is the pointer at `0x08053D1C`, i.e. the high-score name screen. No `PASSWORD`/`CHEAT`/`SECRET`/`UNLOCK` literal exists anywhere in the 8 MiB image, and the first three presses of every published button sequence produce **zero** key-mask table hits (§6b).

The developer-intended "cheat" surface is a **save-data unlockable system** (guide §16.18): one hidden mode (`ADVANCE STORY`) and a set of option values gated behind Shooting-Range SS ranks. 3rd party cheat indexes publish the intended gates: ADVANCE STORY = clear Arcade Mode; Continue 2/3 at 11/17 SS ranks; player life 6/7/8 at 1/3/5; Time Limit +20/+30 at 7/10. Those are *unlockables*, not codes.

The widely mirrored "Silent Scope GBA" button code (`Up, Right, Down, Left, Up, Square, Triangle`) is a **mislabelled PlayStation 2 code** — Square/Triangle do not exist on GBA — and the corresponding key-mask prefix has **0** hits in this ROM. Recorded as unverified/false for this SKU.

We minted a **published-list-free unlock**: setting EEPROM byte `0x3A` to `0xFF` before boot makes `ADVANCE STORY` appear on the main menu (Observed, screenshot + save-byte read). With byte `0x3A = 0x00` the entry is absent. This is a novel, reproducible method not on 3rd party cheat indexes; the published method (clear Arcade Mode) was not executed.

a 3rd party cheat index's only GBA finding — crash-handler text at `0x6F6E48` — is confirmed (`ASSERTION FAILED ...`, `WARING FILE=[%s] ...`). The main-menu `STATUS` entry renders only a logo card with `OK`, i.e. an unimplemented/cut screen.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba -3`), `DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`, Xvfb `:317` + openbox.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, arrows = D-pad. Hold keys ~0.15–0.2 s; shorter taps are dropped.
* Boot: Konami logo → title (~13–20 s) → **Start** → main menu.
* Walk: main menu → SHOOTING RANGE (stage row + Mode list) → OPTIONS (GAME CONFIG / BUTTON CONFIG tabs) → RANKING → STATUS → LINKED PLAY → ARCADE MODE (starts gameplay).
* **Novel unlock reproduction (save patch):**
  1. With mGBA stopped, delete `Silent Scope.sav` (a fresh one is regenerated on boot).
  2. Set byte `0x3A` of that 512-byte EEPROM to `0xFF` (all other bytes left at defaults). The 16-bit checksum at `0x26..0x27` may be left `0x0000`; the game accepted the patched file without complaint.
  3. Boot, press Start. Main menu now has 7 entries including `ADVANCE STORY` between `ARCADE MODE` and `SHOOTING RANGE`.
  4. Bounds check: repeat with `0x3A = 0x00`; the entry is absent (6-item menu).
  *Note:* the game rewrites the EEPROM on some menu transitions, so the patch must be applied before boot and the menu observed immediately.

## 4. Address map

| Region / address | Role (evidence) |
|---|---|
| `0x08000000`–`0x08000200` | Stock ARM crt0 / header; `main` Thumb pointer `0x08000339` in literal pool |
| `0x087004C0` | Second GBA header (Japan, `AIPJ`), own crt0 to `0x08700660` |
| `0x08700190` | `SAVE DATA FORMAT`, `YES`, `NO` strings; xref literal at `0x0804F548` |
| `0x08700204`–`0x0870029E` | Option value strings: `0`–`8`, `EXTRA`, `00`, `+10`, `+20`, `+30`, `NORMAL`, `MILD`, 5 languages |
| `0x087002A0`–`0x087002F8` | Pointer tables into the above strings ( Derived: bytes `72 02 70 08` = `0x08700272`, etc.) |
| `0x0870030C` | `RANKING` label; xref literals at `0x08052CF8`, `0x08053254` |
| `0x08700320` | 30-symbol alphabet + `0xFFFE` terminator; xref `0x08053D1C` (name entry) |
| `0x08659CE0` | Ranking column headers (`Rank Score Hit Name`), mode names (`ARCADE MODE`, `ADVANCE STORY`, `SHOOTING RANGE INDOOR1/2, OUTDOOR1/2, FARM, RIVER, CAVE`, `Normal Attack`, `Time Attack`, `Perfect Shot`, `Pop'up Target`, `Quick Shot`) |
| `0x086F6E48` | Crash-handler strings (`ASSERTION FAILED ...`, `WARING ...`); `EEPROM_V122` at `0x086F6EAC` |
| `0x0868C004` | `6CODED2` — inside a high-entropy ADPCM/audio block; **not** a code table |
| `0x085DEE8`, `0x08716A0C` | Only two `L,R,Start` byte-pattern hits; both are integer tables (`00 02 00 01 08 00 ...`), not key masks |
| EEPROM `0x16` | Player-life index (fresh `0x03` → shows `8`; `0x05` → shows `5`) — Observed by patch/UI diff |
| EEPROM `0x17` | Difficulty (fresh `0x04`; patched `0x01` → screen shows `1`) — Observed |
| EEPROM `0x26..0x27` | Save checksum (written by game on option exit: `0x3ECB`, `0x7EAA` in trials); value `0x0000` accepted |
| EEPROM `0x3A` | **ADVANCE STORY unlock byte**: `0x00` = absent, `0xFF` = present — Observed |
| EEPROM `0x100..` | High-score records (score/hit%/encoded name), e.g. `0x2710`=10000, `0x32`=50%, `0x0C48 2E 0C4B`=`H.K` |

## 5. Algorithm

```
# Unlock gate (derived from save-byte binary search + in-game observation)
if eeprom[0x3A] != 0:            # 0xFF confirmed; exact truthiness untested for other values
    menu.insert(1, "ADVANCE STORY")

# Option value sets (derived from pointer tables at 0x087002A0..F8)
DIFFICULTY   = [1..8]                       # observed selectable 1..8
PLAYER_LIFE  = {index -> label}             # eeprom 0x16; observed 3->8, 4, 5
CONTINUE     = [1, 2, 3, EXTRA]             # EXTRA string at 0x08700243
TIME_LIMIT   = [00, +10, +20, +30]          # 0x0870024A..0x08700260
LANGUAGE     = [ENGLISH, SPANISH, FRENCH, ITALIAN, GERMAN]

# SS-rank gates (published on 3rd party cheat indexes, USA; thresholds not isolated in ROM during this run)
life 6/7/8  <- 1/3/5 SS ranks
time +20/+30 <- 7/10 SS ranks
continue 2/3 <- 11/17 SS ranks
```

There is **no validator** to reimplement: no comparison against user-entered text exists. The name-entry buffer at the ranking screen is consumed only by the high-score writer (guide §16.2b).

## 6. Tables

**Main menu** (6 entries; 7 with `ADVANCE STORY` unlocked):
`ARCADE MODE`, `[ADVANCE STORY]`, `SHOOTING RANGE`, `LINKED PLAY`, `OPTIONS`, `RANKING`, `STATUS`.

**OPTIONS / GAME CONFIG** (Observed): DIFFICULTY 1–8, PLAYER LIFE (default shows 8), CONTINUE (default 1), TIME LIMIT (default 00), LANGUAGE (default ENGLISH). Tabs switched with Left/Right; rows with Up/Down; L+R simultaneously = default setting.

**OPTIONS / BUTTON CONFIG** (Observed): SHOOT=R, SCOPE=B, QUICK=L, SLOW=A, SCOPE TYPE=PUSH.

**SHOOTING RANGE** (Observed): stage carousel `INDOOR`, `INDOOR`, `FARM`, … (scroll right); modes `Normal Attack`, `Time Attack`, `Perfect Shot`, `Pop'up Targets`, `Quick Shot`; RECORD / RANK columns.

**RANKING** (Observed, ARCADE MODE table): 1st 10000 50% H.K … 9th 3000 15% TGG — defaults match the ASCII bank at `0x08659EC0`.

**Published GBA unlockables (3rd party cheat indexes, archived 2022 snapshot):** as listed in §5. The PS2-only button codes on 3rd party cheat indexes (Hidden mode, Pink mode, No crosshair, Voyeur Mode, etc.) are **not** GBA codes; they use Square/Triangle/Circle/L1/R1 and have no GBA key-mask table (§6b).

## 6b. Enumeration

**Code-space / surface definition**

* Password space: **none**. Alphabet = 30 symbols at `0x08700320`; it is consumed at `0x08053D1C` (ranking name entry), not by any validator. `strings`/binary literal counts: `PASSWORD`=0, `password`=0, `CHEAT`=0, `SECRET`=0, `UNLOCK`=0, `CODE`=1 (`6CODED2`, audio data false positive).
* Button-code space: searched all 2-byte little-endian key-mask forms (active-high `A=1…L=0x200` and active-low complements) for the published prefixes:
  * `Up,Right,Down` → **0** hits (both polarities)
  * `Up,Up,Down,Down` → **0** hits
  * Konami-like `Up,Up,Down,Down,Left,Right,Left,Right` → **0** hits
  * `L,R` → 454 raw byte hits; `L,R,Start` → 2 hits, both inspected and shown to be integer tables, **not** key-mask sequences.
  This bounds the negative: no button-code table or key-mask dispatcher exists for those sequences.
* Hidden/debug menu: no `debug` literal; the only leftover development text is the crash handler at `0x6F6E48` (dead text, no menu). `STATUS` is reachable and renders only a logo card — an empty/unimplemented screen, not a hidden menu.

**Unlockable space (the actual system)**

* Enumerated every reachable screen: title, main menu (6/7 items), OPTIONS (2 tabs, 5+5 rows), SHOOTING RANGE (stage + 5 modes), gameplay, RANKING, STATUS, LINKED PLAY, ARCADE MODE start. Screenshots retained in `/tmp/silentscope/`.
* Save-data unlock field at EEPROM `0x3A` is a **single byte = 256 representable values**. Tested `0x00` → ADVANCE STORY **absent** (6-item menu) and `0xFF` → **present** (7-item menu). The novel value `0xFF` appears in no published list; the published unlock method (finish Arcade Mode) was not used.
* Option value sets are fully enumerated from the ROM pointer tables at `0x087002A0..0x087002F8` (see §5/§6): nothing beyond `EXTRA` / `+30` / `8` / 5 languages is representable.
* **Bounds proven by rejection:** unpatched (`0x3A = 0x00`) and the original fresh EEPROM both reject the ADVANCE STORY entry — it is not drawn. Also, patching every byte in `0x18..0x3F` to `0xFF`, and separately `0x40..0xFF` to `0xFF`, left CONTINUE=`1` and TIME LIMIT=`00` (Observed screenshots), i.e. the SS-rank gates for those values are not simple stored flags in those regions. They are likely derived from per-mode rank records; that exact accumulator was **not** isolated (§8). This is a bounded negative for the byte regions tested, not "not tested".

## 7. Validation evidence

* **Observed (emulator/save RAM):** title → Start → main menu; OPTIONS fields and their values; BUTTON CONFIG mapping; SHOOTING RANGE stage/mode screen; gameplay HUD; RANKING table; STATUS and LINKED PLAY logo cards; ADVANCE STORY appearing after `eeprom[0x3A]=0xFF` and absent with `0x00`; DIFFICULTY changing from 4 to 1 after patching `eeprom[0x17]`; player-life index `0x16` changing 3→5 with the displayed value changing 8→5.
* **Derived (disassembly/tables):** option value pointer tables at `0x087002A0..F8`; alphabet consumer at `0x08053D1C`; save-format string xref `0x0804F548`; ranking xrefs `0x08052CF8`/`0x08053254`; second header/crt0 at `0x087004C0`; crash-handler strings at `0x6F6E48`; zero-length key-mask scans.
* **External evidence (data, not instructions):** 3rd party cheat indexes archived cheats page (unlock thresholds, ADVANCE STORY method); 3rd party cheat indexes archived page (crash handler). Both fetched pages were treated purely as data; no embedded directives were followed.
* **Inferred (labelled):** the `0x3A` byte is a flag/nonzero test rather than a count (only 0x00 and 0xFF probed); the `6CODED2` string is audio data; the second (AIPJ) image is dormant in the retail USA path.

## 8. Unknowns

* Exact truth set of `eeprom[0x3A]` (only `0x00` and `0xFF` tested) and which in-game event sets it (published claim: clearing Arcade Mode — not executed).
* The SS-rank accumulator and the exact code comparing it with 1/3/5/7/10/11/17; consequently CONTINUE `2/3/EXTRA` and TIME `+20/+30` were not observed selected, only enumerated from tables. We did **not** finish a Shooting-Range stage, so no SS rank was earned.
* The save checksum algorithm at `0x26..0x27` (not required: value `0x0000` was accepted).
* How (or whether) the second `AIPJ` image can be selected on USA hardware; the purpose of the empty `STATUS` screen.
* Whether any hidden content exists behind `ADVANCE STORY` beyond the extra menu entry (not played through).

## 9. Tooling

* mGBA 0.10.5 (`-3`, `-g`, `-d` trials), Xvfb `:317`, openbox, xdotool, scrot, ImageMagick.
* `strings`, `xxd`, `grep`, Python 3 (struct/zlib/PIL), `arm-none-eabi-objdump -M force-thumb`.
* REA MCP (Ghidra provider) opened/closed for xref queries; auto-analysis did not yield additional xrefs in time.
* Helper scripts in `/tmp/silentscope/`: `drive.py` (input + cropped capture), `ssdecode.py` (mGBA `.ss1` `gbAs` zlib decoder), `probe_unlock.py`/`binsearch.py` (save-byte unlock search), `probe_opts.py`, `gdbread.py` (GDB stub attempts). Savestate diffing was attempted but noisy (VRAM/audio churn); EEPROM byte diffs and screenshots were used instead.

No ROM image or copyrighted assets are redistributed by this report.
