# The Land Before Time (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Land Before Time.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `LANDBEFORETI` |
| Game code / maker | `ALAE` / `5Z` |
| Revision | 00 |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock crt0; header checksum 0x0040, complement 0x00) |
| MD5 | `318fd3dec910d491bace987795397bb5` |
| SHA-1 | `e546d90befc9fefc0dce4b72890791263ed40284` |
| SHA-256 | `16a71bd2b4c05b362cccdae91a74350fc50b3843f9c68cd6ecd1620e5e494f7b` |
| Developer / publisher | Full Fat / Conspiracy Entertainment (boot splash, observed) |

Revision is confirmed by the hashes; all addresses below apply to this image only.

## 2. Executive summary

The game has a **developer-intended icon password system** on the title screen
(PASSWORD). A password is **four icons**, each chosen from a 5-symbol alphabet
(Littlefoot, Cera, Spike, Ducky, Golden Tree Star), entered by Up/Down and
Left/Right and submitted with A. The validator at `0x08002FD6` treats the four
icon IDs as **decimal digits**: `N = 1000·a0 + 100·a1 + 10·a2 + a3`, then searches
`N` in a **12-entry `u16` allow-table at `0x08029F60`**. Therefore the input space
is exactly **5⁴ = 625** codes and **exactly 12 are accepted** (4 published, 8
absent from every published list). Every accepted code starts one of levels
1–4 of worlds 1–3; codes not in the table are silently rejected.

Novel code **`1320`** (Cera, Ducky, Spike, Littlefoot) was entered through the
real password UI and accepted, starting gameplay (`ngui_1320_fixed.png` →
`ngui_1320_result.png`). All 12 table codes were confirmed in-game, and six
non-table codes were confirmed rejected. No GameShark/CodeBreaker/AR codes were
used or reported.

The localized string banks also contain `SKIP LEVEL` menu labels in all five
languages, but the reachable in-game pause menu offers only CONTINUE GAME and
EXIT GAME; no input path to the SKIP LEVEL entry was found (§8).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `mgba -3`.
* keymap (mGBA SDL): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  arrows = D-pad. Hold keys ~120–150 ms; focus with `xdotool windowactivate --sync`.
* Path: title screen → **PASSWORD** (third item) → 4 icon slots.
  * **Up/Down** cycles the icon in the selected slot (5 symbols, wrapping).
  * **Left/Right** moves the selected slot (4 slots, wrapping). The selected
    slot is drawn large; the other three small.
  * **A** submits. A valid code leaves the screen and starts the level;
    a rejected code returns silently to the same screen. B exits to the menu.
* Published codes used as anchors (all verified against the ROM and emulator):
  `2104`, `4230`, `4412`, `3141` for advertised Levels 2–5.
* Novel code entered by hand: `1320` (see §6b). In-game proof screenshots are in
  `/tmp/landbeforetime/`.

## 4. Address map

| Address | Type | Meaning / evidence |
|---|---|---|
| `0x0801FA64` | ROM | ASCII `PASSWORD` (title-menu label) |
| `0x0802B024` | ROM | Pause-menu string group; `+0x28` = `SKIP LEVEL`, `+0x50` = `EXIT GAME` |
| `0x0802C08C` | ROM | Localized string-group pointer table (English at index 0) |
| `0x0801DE0` | ROM literal | `0x03004D6C`, used when initializing the password buffer |
| `0x0800BF14` | ROM/Thumb | Password input handler. Reads mirror at `0x03005F68`: bit `0x40`=Up (icon−1 mod 5), `0x80`=Down (icon+1 mod 5), `0x20`=Left (slot−1 mod 4), `0x10`=Right (slot+1 mod 4). Writes slot index to `0x03004F78` and icon to `0x03004D6C[slot]` at `0x0800C12C–32`. **Derived** (disassembly + write watchpoint) |
| `0x08002FD6` | ROM/Thumb | **Validator**: packs decimal code, searches 12-entry table |
| `0x08029F60` | ROM | 12×`u16` allow-table: `2104 4230 4412 3141 1320 3402 0311 4122 2410 4314 0124 1314` |
| `0x08003024` | ROM | `CMP r3,#12` — miss path (invalid) |
| `0x08003038` | ROM | Stores `index/4 + 1` (world) at `0x03004D6[+2]` |
| `0x08030A2/0C0/0DC/0F8` | ROM | Level-within-world setters (1/2/3/4) via `0x0800B9FC` |
| `0x03004D6C..6F` | IWRAM | 4 password icon bytes (`u8[4]`). **Observed** |
| `0x03004F78` | IWRAM | Selected slot index (0–3), `u8`. **Observed** |
| `0x03004D90` | IWRAM | Screen state. Password=0; accepted code briefly shows `20+level-within-world` (21–24); reject only shows 3. Used as in-game oracle. **Observed** |
| `0x03005F68` | IWRAM | Engine's mirrored key state read by the password handler |
| Savestate layout | file | mGBA `.ss1` `gbAs` zlib chunk (397,312 B); IWRAM begins at raw offset `0x19000`, so raw `0x1DD6C` ↔ `0x03004D6C`. **Derived/observed** |

## 5. Algorithm

Validator (`0x08002FD6`, Thumb), transcribed from disassembly:

```c
/* a[0..3] are the four icon IDs, each 0..4 */
uint16_t N = (uint16_t)(a[0]*1000 + a[1]*100 + a[2]*10 + a[3]);
const uint16_t table[12] = {2104,4230,4412,3141,1320,3402,
                            0311,4122,2410,4314,0124,1314};
int i;
for (i = 0; i < 12; i++) if (N == table[i]) break;
if (i == 12) return INVALID;                 /* branch at 0x08003024 */

world        = i / 4 + 1;                    /* stored 0x03004D6+2 */
level_in_world = i % 4 + 1;
/* level_in_world 1..4 selected by the dispatch at 0x0800303A..0x80030F8 */
```

Notable instruction details (all **Derived** from `arm-none-eabi-objdump`):
`a0*31 << 2` then `+a0` then `<<3` is the compiler's way of computing `a0*1000`
(0x08002FDA–E2); `a1*100` at `0x08002FE6`; `a2*5 << 1` = `a2*10` at
`0x08002FEE–F2`; result truncated to 16 bits at `0x08002FFA–FC`. The table is
searched as 12 consecutive halfwords, not hashed. There is **no checksum** and
no arithmetic beyond the decimal packing — the allow-table is the whole
validator. This also means each accepted code is a unique decimal spelling;
leading-zero codes (e.g. `0311`) are four-digit strings, not three-digit numbers.

## 6. Tables

### 6.0 Icon alphabet (order as cycled by Down; **Observed** in screenshots)

| ID | Icon | Published name |
|---:|---|---|
| 0 | brown long-neck | Littlefoot |
| 1 | orange triceratops | Cera |
| 2 | dark-green ankylosaur | Spike |
| 3 | light-green, big eyes | Ducky |
| 4 | yellow star | Golden Tree Star |

### 6.1 Complete accepted set (all 12; **Derived** from table + **Observed** in-game)

| Code | Icons (slot 1→4) | Index | World | Level-in-world | Source |
|---|---|---:|---:|---:|---|
| 2104 | Spike, Cera, Littlefoot, Star | 0 | 1 | 1 | GameFAQs "Level 2" |
| 4230 | Star, Spike, Ducky, Littlefoot | 1 | 1 | 2 | GameFAQs "Level 3" |
| 4412 | Star, Star, Cera, Spike | 2 | 1 | 3 | GameFAQs "Level 4" |
| 3141 | Ducky, Cera, Star, Cera | 3 | 1 | 4 | GameFAQs "Level 5" |
| 1320 | Cera, Ducky, Spike, Littlefoot | 4 | 2 | 1 | **novel** |
| 3402 | Ducky, Star, Littlefoot, Spike | 5 | 2 | 2 | **novel** |
| 0311 | Littlefoot, Ducky, Cera, Cera | 6 | 2 | 3 | **novel** |
| 4122 | Star, Cera, Spike, Spike | 7 | 2 | 4 | **novel** |
| 2410 | Spike, Star, Cera, Littlefoot | 8 | 3 | 1 | **novel** |
| 4314 | Star, Ducky, Cera, Star | 9 | 3 | 2 | **novel** |
| 0124 | Littlefoot, Cera, Spike, Star | 10 | 3 | 3 | **novel** |
| 1314 | Cera, Ducky, Cera, Star | 11 | 3 | 4 | **novel** |

Published lists label the first four codes "Levels 2–5"; the game's own internal
level-within-world from the dispatch is 1–4. The labels are offset by one —
report the code and the observed start state, not the wiki label (cf. guide §16.15).
The observed screen state is `21,22,23,24` for indices `0,1,2,3` and repeats
`21..24` for indices `4..7` and `8..11`, confirming the world/level split.

## 6b. Enumeration

**Space definition.** 4 slots × 5 symbols = **5⁴ = 625** representable codes,
digits 0–4 only; no reserved bits, no checksum, no length variants. The
validator's allow-table has **12 entries**, so the accepted set is exactly
12/625 (**1.92%**) — a closed set proven by reading every entry of the compare
table (`0x08029F60`) and by the `CMP r3,#12` miss branch at `0x08003024`.

**Novel codes.** Eight accepted codes appear in no published list (GameFAQs,
Cheat Happens, almarsguides, 53lu all list only the four Level-2–5 codes).
`1320` was selected for in-game proof:
* Entered with real UI keypresses: Right/Left to move slots, Down ×1/3/2/0 to
  set Cera/Ducky/Spike/Littlefoot, A to submit.
* `ngui_1320_fixed.png` shows the four entered icons.
* `ngui_1320_result.png` shows the game started a new level (playable forest
  scene, HUD and character present) — **Observed**.
* The other seven novel codes were each patched into `0x03004D6C..6F` and
  submitted with A in mGBA; each produced screen state 21–24 (level start).

**Bounds proven by rejection.** Six non-table codes were submitted through the
same UI path and all failed (`verify_results.json`):
`0000`, `4444`, `0001`, `2222`, `1234`, `0444` → state peaked at 3, screen never
left PASSWORD. `4444` is a useful boundary case: it uses only legal symbols but
no table entry, proving that symbol validity alone is insufficient. All 12 table
codes were re-run in the same session with a 22-frame state trace; every one
peaked at 21–24 while every rejected code peaked at ≤3. Full log:
`/tmp/landbeforetime/verify12.py` output and `verify_results.json`.

## 7. Validation evidence

* **Observed**: ROM hash/header; boot splash; title/pause/password screens;
  icon cycle and slot navigation via xdotool; `0x03004D6C` buffer contents;
  `0x03004F78` slot index; 12 accepted and 6 rejected codes with screen-state
  traces; novel code `1320` accepted with screenshot.
* **Derived**: validator decimal packing and 12-entry table from Thumb
  disassembly; input-handler key masks and wraparound from disassembly plus a
  write watchpoint at `0x0800C136`; savestate RAM offset mapping from live
  debugger reads; world/level split from the dispatch at `0x08003038`.
* **Inferred**: that the four published "Level 2–5" labels correspond to the
  game's level-in-world 1–4 (label offset by one); the exact displayed level of
  worlds 2 and 3 was not read from a banner, only from the screen-state code.

No prompt-injection content was found in the ROM strings or fetched pages;
fetched cheat pages were treated as data only.

## 8. Unknowns

* The five-language string bank contains `SKIP LEVEL` (`0x0801EF60` …) between
  CONTINUE GAME and EXIT GAME in the pause-menu string group at `0x0802B024`,
  strongly suggesting a debug menu entry. The reachable pause menu shows only
  CONTINUE GAME and EXIT GAME (`06_pause.png`). Tested L+R+Start on the pause
  screen did not reveal it. The gate was not isolated, so this is an unresolved
  gated-feature lead, **not** a confirmed hidden menu.
* The validator is inline code inside a large screen function, not an isolated
  callable; its return path was established by disassembly and the in-game
  oracle rather than by a direct debugger call.
* The GBC color passwords circulating under this title (`Gray, Green, …`) belong
  to the GBC SKU and do not apply to this 4 MiB GBA image; they were not tested.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` for static decoding; Python scripts in
  `/tmp/landbeforetime/`: `scan.py`, `dumpptrs.py`, `dbg2.py`,
  `probe3.py`/`probe4.py`, `watch.py`, `watchstate2.py`, `readwatch.py`,
  `oracle.py`, `verify12.py`, `novel_gui.py`.
* mGBA `-d` pty debugger driven from Python (`pty`, `select`) for live RAM reads,
  writes, frame advance and read/write watchpoints. GDB stub on port 2345 was
  unusable (single-client / stale connections), so the stub-free `-d` debugger
  was used.
* Savestate `gbAs` chunk decompressed with `zlib` to map raw offsets to RAM.
* Evidence artifacts: `00_title.png` … `reject.png`, `ngui_1320_*.png`,
  `verify_results.json`, `fullsweep*.log` (the two broad timing-based sweeps
  were abandoned as unreliable; their partial data is not used as evidence).

No ROM data or copyrighted assets are redistributed by this report.
