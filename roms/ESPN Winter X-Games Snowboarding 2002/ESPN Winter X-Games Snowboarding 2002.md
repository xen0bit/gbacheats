# ESPN Winter X-Games Snowboarding 2002 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `ESPN Winter X-Games Snowboarding 2002.gba` (same folder as this report) |
| Size | 4,194,304 bytes (0x400000 / 4 MiB) |
| Header title (0xA0) | `ESPN XG SNOWAWXE` (display title `ESPN XG SNOW`) |
| Game code (0xAC) | `AWXE` (`AWXEA4`) |
| Maker (0xB0) | `A4` (Konami; on-screen credit: "Produced by Konami Computer Entertainment Osaka, Inc.") |
| Version / fixed / main / device | 0x00 / 0x96 / 0x00 / 0x00 |
| Complement (0xBD) / checksum (0xBE) | `0x4B` / `0x0000` (rebuilt-header artifact; complement mismatch also noted) |
| Entry word (0x00) | `0xEA00002E` — stock branch to crt0 `0x080000C0` |
| Embedded GBA-header scan | **1 header only** (Nintendo logo at file `0x4`). No trainer, cracktro, multiboot stub, or multi-game shell. |
| MD5 | `2f78a6ee027003fa5472eb90fc1322a7` |
| SHA-1 | `6012907965d45326beb27a98cade8efacef5e377` |
| SHA-256 | `db4fd5751f0067c455c6924454dd55f49b08a135aaad48212964cdb6a0e85086` |

`file(1)` reports `Game Boy Advance ROM image: "ESPN XG SNOW" (AWXEA4, Rev.00)`. The SHA-1 matches the BizHawk GBA database entry for **ESPN Winter X-Games Snowboarding 2002 (USA)** — this is the stock USA retail image.

## 2. Executive summary

**No developer-intended in-game cheat system exists in this ROM.** There is no password screen, no password/cheat literal, no code-entry keypad, no in-game button-code sequence, and no reachable hidden debug menu. This is a *bounded negative* result (guide §0.2), not an incomplete search:

* **No input surface / no text surface.** Every reachable screen was walked in the emulator (title, attract/demo, `WINTER X GAMES` menu, `OPTION` menu, gameplay, and the four scene-groups reached by savestate scene-index injection). No code field or hidden "cheat" option appeared. The game's UI text is bitmap/font-indexed, so a 128-sweep of 16 keywords × 8 encodings (ASCII, lower, upper, XOR 0x20, ±0x20, UTF-16LE/BE) over all 4 MiB returned **zero** hits.
* **No button codes.** The single joypad reader (`0x080005D0`) is referenced by 25 input-state code sites. The only multi-button gate in the whole ROM is the **standard GBA soft-reset chord**: held `A+B+Select+Start` (active-high mask `0x0F`, checked as `A` on the edge plus `B|Select|Start` held) at `0x080016BC`, which sets a flag at `0x030052C8` and switches to scene 28 (a reboot routine). This is a console convention, not a cheat (§16.3 "no system").
* **No debug menu gate.** Unlike *ESPN Final Round Golf 2002* (same collection), which has a 9-entry debug menu behind a RAM word `0x03002528 == 0x1F`, this ROM has **no** `cmp #0x1F`-style scene gate and no debug-label bank. The `OPTION` screen's `SOUND TEST` / `SCOPE RESET` entries are the closest developer-style options, but they are a normal, reachable options screen, not a hidden menu.
* **Published codes:** GameFAQs (archived) says "We don't have any cheats posted for this game yet"; Cheat Happens lists none. The only published "secrets" (hidden course at rank SS) are **PS2/Xbox**-only (§16.11). The only GBA "cheats" circulating are external **CodeBreaker memory patches** (e.g. `8300089C 0000` "Always Low Time", `830008A4 FFFF` "Quick Score Gain", `830008A4 869F` "Max Score", master `100005D0 0007`) — out of scope (memory edits, not developer-intended codes).

**Shared architecture with sibling ESPN GBA titles:** the KCEO/Konami engine here shows the same overall pattern as *Final Round Golf*, *Great Outdoor Games: Bass*, *International Winter Sports* and *X Games Skateboarding*: a font-indexed UI, a scene-index state machine driven from a main loop, a single joypad reader with an active-high mirror in IWRAM, and the soft-reset chord. **No cheat/password/debug-gate constant is shared**: Final Round Golf's `0x03002528 == 0x1F` debug gate and International Winter Sports' unused debug text bank were verified **absent** from this image (the literal `0x03002528` does not occur in this ROM; no debug-string bank exists). Each ROM's negative result was independently established.

Per §0.2, with no code system the space is defined by the **29-entry scene dispatch table** (2³² representable scene-word values, 29 meaningful entries) and the **10-bit joypad mask space** (1,024 values). Bounds are proven by enumerating all 29 scene handlers via savestate scene-index injection and by testing every published code literal against the ROM.

## 3. How to reproduce

### Environment
- `Xvfb :318 -screen 0 1024x768x24`, `DISPLAY=:318 openbox`, `SDL_AUDIODRIVER=dummy mgba -3 <rom>`.
- mGBA 0.10.5 (SDL). Default keymap verified against `KEYINPUT` (`0x04000130`): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys 80–150 ms.
- The title runs a long (~15–20 s) boot/attract sequence; start input before the `PRESS START` prompt is ignored. The prompt alternates with the copyright overlay; `gomenu.py` waited for a white-pixel signature in the prompt band before pressing Start.

### Observed screens (Observed)
1. Boot logos: ESPN "the games", KONAMI (×2).
2. Title: `winter Games snowboarding 2002` logo with `PRESS START` and ©2002 Konami / Disney / ESPN overlay.
3. After Start: alternating attract/splash frames — snowboarding footage, `WINTER X GAMES` title card, and the `©2002 Disney` ESPN photo board.
4. `WINTER X GAMES` menu (scene 6) — visible heading and two bullet lines, but the item labels are drawn beyond the right edge of the 240×160 viewport in this mGBA build (see §8).
5. `OPTION` menu (scene 10) — `SOUND = ON`, `SOUND TEST = 0`, `SCOPE RESET`, `EXIT` (screenshot `scene_10.png`).
6. Gameplay demo (scene 1) and several fade/transition scenes (2,3,4,5,7,8,9,11,13,14,15,17–22).

### Scene enumeration technique (Derived; reproducible)
The main loop at `0x08000210` increments a frame counter at `0x0300B852` and dispatches through a 29-entry Thumb function-pointer table at `0x08196978`; the scene index is the word at **`0x030052BC`** (saved in the mGBA state header at `0x30` as the pointer to `0x030052B8`). I dumped the title-screen savestate (`gbAs` PNG chunk, zlib-decompressed to 397,312 bytes; IWRAM at state offset `0x19000`), patched the scene word at state offset `0x19000 + (0x030052BC - 0x03000000) = 0x1E2BC`, rebuilt the PNG with a corrected CRC (`patchstate.py`), and booted each `mgba -3 -t scene_N.ss1 game.gba`. This reached every handler 0–28; screenshots retained in `/tmp/opencode/espnxgames/scene_*.png`. This is RAM injection for analysis only — **not** an in-game code (§16.10).

### Codes tested
No in-game code was found or published for the GBA SKU, so none could be entered. The following were checked and excluded:
- GameFAQs PS2 "Hidden course" (rank SS, Japan `???` square) → wrong platform (§16.11).
- CodeBreaker memory patches (ROMFSUN/libretro) → external memory edits, out of scope.
- GBA soft-reset chord `A+B+Select+Start` → confirmed as a system reset, not a cheat.

## 4. Address map

| Address | Contents | Evidence type |
|---|---|---|
| `0x08000000` | Stock GBA header / ARM crt0 (`0xEA00002E`) | Observed (bytes) |
| `0x080005D0` | Joypad reader: reads `KEYINPUT` (`0x04000130`, literal at file `0x638`), XORs with `0x03FF`, writes held (`0x0300087C`) and newly-pressed (`0x03000888`) masks; D-pad repeat logic. | Derived (disassembly) |
| `0x080016BC` | Soft-reset chord gate: `A` edge + `B\|Select\|Start` held → set `0x030052C8 = 1`, set scene 28. | Derived |
| `0x08000210`–`0x0800023A` | Main loop: frame counter `0x0300B852`, scene index `0x030052BC`, dispatch via `0x0800FAD8` (`bx r0`) to table `0x08196978`. | Derived |
| `0x08196978` | Scene dispatch table, 29 Thumb pointers (indices 0–28); index 29 is non-pointer data. | Derived |
| `0x08001BB4` (scene 0) | Boot/logo handler; sets scene 1. | Derived |
| `0x08001C60` (scene 1) | Title/attract handler; checks A/Sound, transitions to scene 2. | Derived |
| `0x08001E44` (scene 2) | 5-option menu setup (jump table at `0x08001E88`). | Derived |
| `0x08002841` (scene 6) | `WINTER X GAMES` menu setup. | Derived |
| `0x08006071` (scene 10) | `OPTION` menu handler (SOUND / SOUND TEST / SCOPE RESET / EXIT). | Observed + Derived |
| `0x08005A5C` (scene 16) | One-frame setup, immediately sets scene 17. | Derived |
| `0x08001698` (scene 28) | Reboot: `IME=0`, jump to reset (`0x0800F6AC`). | Derived |
| RAM `0x0300087C` / `0x03000888` | Active-high held / newly-pressed joypad masks (halfwords). | Derived |
| RAM `0x030052B8` / `0x030052BC` / `0x030052C8` | Scene base pointer / scene index / soft-reset flag. | Derived (savestate + disassembly) |
| RAM `0x03004EB0` | Global game-state base (`+0x418` = soft-reset flag; `+0x410` used by menu branches). | Derived |

## 5. Algorithm

No password/checksum algorithm exists. The only game logic relevant to cheats is:

```
; main loop (0x08000210)
frame++                         ; [0x0300B852]
read_joypad()                   ; 0x080005D0 -> held/pressed mirrors
check_soft_reset_chord()        ; 0x080016BC
scene = [0x030052BC]            ; 29-entry dispatch
call table[scene]               ; 0x08196978

; soft-reset gate (0x080016BC)
if (held & 1) and ((held & 0x0E) == 0x0E):        ; A + B|Select|Start
    if (pressed & 1) or (pressed & 0x0E):
        [0x03004EB0 + 0x418] = 1
        [0x030052BC] = 28                          ; reboot scene
```

## 6. Tables

**Input masks (active-high, GBA convention):** `A=0x001`, `B=0x002`, `Select=0x004`, `Start=0x008`, `Right=0x010`, `Left=0x020`, `Up=0x040`, `Down=0x080`, `R=0x100`, `L=0x200`. Soft-reset chord = `0x00F`.

**Scene dispatch (`0x08196978`, 29 entries):** 0 `08001BB5`, 1 `08001C61`, 2 `08001E45`, 3 `0800205D`, 4 `08002835`, 5 `08002839`, 6 `08002841`, 7 `08002B09`, 8 `08002C61`, 9 `08002C65`, 10 `08006071`, 11 `08006221`, 12 `08005149`, 13 `08005259`, 14 `0800838D`, 15 `080084ED`, 16 `08005A5D`, 17 `08005B0D`, 18 `08008091`, 19 `08008101`, 20 `08001715`, 21 `0800178D`, 22 `0800179D`, 23 `08001831`, 24 `08001D75`, 25 `08001DE9`, 26 `08001709`, 27 `0800170D`, 28 `08001699`. (Pointers shown with Thumb bit; handlers start at `ptr & ~1`.)

**Published GBA codes:** none exist. **Wrong-SKU/external codes:** PS2 hidden-course secret; CodeBreaker patches `8300089C 0000`, `830008A4 FFFF`, `830008A4 869F`, master `100005D0 0007` — all excluded.

## 6b. Enumeration

**Space definition.** With no code system, the two candidate spaces are:
1. **Scene state:** 32-bit word at `0x030052BC` → 2³² = 4,294,967,296 representable values; the dispatch table gives **29 meaningful scenes (0–28)**. All 29 were injected and observed; scene 28 is reboot, scene 10 is the `OPTION` menu, scene 6 is the `WINTER X GAMES` menu. No scene exposes a code entry, a password keypad, or an undocumented debug menu.
2. **Button state:** 10-bit joypad mask → 1,024 possible held combinations; 25 code sites read the mirrors. **Exactly one** multi-button gate exists (soft-reset chord, value `0x00F`); every other site tests a single button (`0x001`, `0x002`, `0x008`) or D-pad direction. No stored button-mask sequence table exists: targeted searches for the Konami code (`40 40 80 80 20 10 20 10 02 01`), the L/R-alternating "big head" sequences from the PS2 game, and 3-/4-press u16 prefixes found **no** hits in code regions (one u16 `LR` hit at file `0x907BA` is inside a data table of texture/vertex values, not code).

**Novel code:** none can be minted because no code system exists. Per §0.2 this is the correct negative deliverable: a password/validator would be required for a novel code, and none is present.

**Bounds proven by rejection:**
* All 29 scene indices were injected; out-of-range values are not selected by the dispatch (table ends at 28; index 29 is data, and the table's natural bound is the last pointer). Only the documented scenes were observed.
* 128 keyword×encoding searches over the full 4 MiB returned 0 code-system literals.
* All 25 input-state code sites were examined: 24 are single-key/menu checks, 1 is the soft-reset chord. No hidden multi-press branch exists.
* Every published code literal was checked: no GBA in-game code exists; PS2 secrets and CodeBreaker patches are wrong-SKU/out-of-scope.
* The soft-reset chord's effect was RAM-verified: it writes `0x030052C8 = 1` and switches to scene 28 (reboot). Pressing it in the emulator returns to the title.

## 7. Validation evidence

* **Observed:** emulator screenshots of boot, title, attract, `WINTER X GAMES` menu, `OPTION` menu, gameplay; all 29 scene-injection screenshots; savestate RAM dumps (scene index `0x030052BC`, soft-reset flag `0x030052C8`).
* **Derived:** disassembly of `0x080005D0` (joypad), `0x080016BC` (soft-reset), `0x08000210` (main loop), `0x08196978` (scene table), scene handlers 0/1/2/6/10/16/28; literal-pointer scans.
* **Inferred:** that the off-screen `WINTER X GAMES` menu labels are a renderer/font-tile artifact (the handler sets up a menu; the tile data for the labels was not visible in the captured viewport). This does not affect the cheat conclusion.
* **Evidence discipline:** no instruction found in ROM text, strings, or fetched web pages was executed or followed; all fetched pages were treated as data (§16.8). No prompt-injection payload was encountered.

## 8. Unknowns

* The `WINTER X GAMES` menu's item labels render beyond the 240×160 viewport under mGBA 0.10.5; the four visible bullet lines could not be read, so the exact menu item names were not enumerated visually. Static disassembly of scene 6/2 handlers shows a normal mode-select structure with no code-entry branch.
* Full in-game progression (rank SS, all courses, Snowboarder-mode unlockables) was not played through; any unlockables would be save-data progression flags (guide §16.18), not codes, and were not brute-forced.
* The screenshot of scene 16 showed a boarder sprite and data rows, but its handler immediately sets scene 17; it is a one-frame transition, not a stable debug screen. No stable hidden screen exists in the table.

## 9. Tooling

* `strings`, `xxd`, `grep`, `file`, `md5sum`/`sha1sum`/`sha256sum` — Phase 0/1.
* `arm-none-eabi-objdump -M force-thumb` and Capstone 5.0.7 — disassembly and literal-pointer scans.
* Python 3 scripts in `/tmp/opencode/espnxgames/`: `key.py` (XTEST input), `gomenu.py` (title detection via white-pixel band), `patchstate.py` (savestate `gbAs` patch + PNG CRC rebuild), `scenes.sh` (scene-index enumeration), plus `state_*.bin` RAM dumps.
* mGBA 0.10.5 under Xvfb `:318` with `SDL_AUDIODRIVER=dummy`; savestate format: PNG `gbAs` chunk zlib-decompressed to 397,312 bytes, IWRAM at `0x19000`, EWRAM at `0x21000` (§16.13).
* Web: web.archive.org GameFAQs snapshot (confirmed empty cheats page), GameFAQs current cheats page (PS2/Xbox-only secrets), Cheat Happens, Ethereal Games (Action Replay index, no GBA codes), BizHawk GBA database (hash match), TCRF (no article for this GBA SKU).

## 10. Legal note

No ROM, extracted graphics, music, or in-game text assets are redistributed. This report contains only hashes, addresses, algorithms, and the author's own scripts/observations.
