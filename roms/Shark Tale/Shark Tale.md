# Shark Tale (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Shark Tale/Shark Tale.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `SHARK TALE` (offset 0xA0) |
| Game code | `BSUE` (EU), maker `52`, version `0x00` |
| Entry word | `0xEA00002E` (stock `b 0xC0` — **no** cracktro/trainer patch) |
| Fixed byte 0xB2 | `0x96`; complement 0xBD = `0xFC`; header checksum = `0x0000` |
| Embedded GBA headers | **1** (logo scan at 0x0 only). This is the standalone retail image, **not** the "Shark Tale & Shrek 2" 2-in-1 described in the guide. |
| MD5 | `1c69e4de75857e5a50c3f23cc093c296` |
| SHA-1 | `6aa57972465f342aa83d945b3d5f500360f1ff2e` |
| SHA-256 | `5c3bd987d3de0099845ea81626357fe4a64095b720b21940c6b407c353b3d876` |
| Developer (in-game credits) | Vicarious Visions |

Verified on the copy at `/tmp/sharktale/sharktale.gba` (byte-identical MD5).

## 2. Executive summary

**No developer-intended cheat system exists in this GBA image.** There is no password screen, no cheat-code entry, no level-select code, no button-code sequence, and no reachable hidden/debug menu. All published "Shark Tale" button cheats belong to the PS2/GameCube/Xbox/PC builds (Edge of Reality engine) and are entered while holding L1/LT/L on a *controller-help screen* that does not exist in the GBA (Vicarious Visions) build; GBA-specific cheat databases list zero codes. The only user-text entry surface is a 3-character **"ENTER INITIALS"** keypad used to name a save/high-score slot — its buffer (`0x02005408`) is written by the keypad handler, read back as a generic global, and cleared on confirm; it is never compared against a code table.

The strings that look most like debug leftovers — `Defeat Section`, `Defeat Section 100%`, `Slow Motion` (0x0803F4C4 / 0x0803F4D8 / 0x0803F4F0) — live in the **shared UI string-pointer table** at `0x0803F084` alongside the ordinary menu labels (`Start Game`, `Resume`, `Quit Level`, …). They are in-game stat/power-up labels ("defeat section 100%" is a completion readout formatted by `%s - %d%%`; "Slow Motion" is a gameplay pickup/mechanic), not debug-menu items: a full text-bank decode (§6b) found no debug/cheat/level-select strings anywhere in the ROM.

Every reachable screen was walked in mGBA with screenshots and savestate-RAM evidence (§7), and seven candidate hidden-menu button combinations were pressed on the title screen with no effect beyond ordinary menu navigation.

## 3. How to reproduce

```
Xvfb :318 -screen 0 1024x768x24 &
DISPLAY=:318 openbox &
export DISPLAY=:318 SDL_AUDIODRIVER=dummy
mgba -3 roms/"Shark Tale"/"Shark Tale.gba" &
```

Keymap verified empirically: **A = `x`, B = `z`, Start = `Return`, Select = `BackSpace`, D-pad = arrows, L = `a`, R = `s`**. Hold ≈50–150 ms (longer holds double-step the cursor).

Screen path (all observed):
1. Boot → DreamWorks SKG logo → Shark Tale title (`START GAME` / `VIEW CREDITS`).
2. `START` → `SELECT A SLOT` (3 × `NEW GAME`, `ERASE`, `B – BACK`).
3. `A` on a slot → `ENTER INITIALS: ---` keypad (A–Z, `-`, `!`, `?`, `$`, `@`, `OK`; `B` = backspace).
4. `OK` → level-intro card (`1-1 NEIGHBORHOOD DELIVERY`) → dialogue → gameplay (`'Round Da Hood`, 0/25 tokens, health HUD).
5. `START` in gameplay → pause menu (`RESUME`, `QUIT LEVEL`, `SOUND`, `SLEEP`).
6. `SOUND` → `MUSIC 100%`, `SFX 100%`, `EXIT`.
7. `VIEW CREDITS` from title → scrolling credits ("VICARIOUS VISIONS").

Savestate RAM reads used mGBA `.ss1` HTML-free PNG states; the zlib `gbAs` chunk decompresses to 397,312 bytes with **IWRAM at raw 0x19000 → 0x03000000** and **EWRAM at raw 0x21000 → 0x02000000** (guide §16.13).

## 4. Address map

| Address | Kind | Evidence | Meaning |
|---|---|---|---|
| 0x08000000 | ROM | header | stock entry `0xEA00002E` → crt0 at 0x080000C0 |
| 0x0803F084 | ROM/data | pointer scan | shared UI string-pointer table (≈50 entries, `{u32 ptr}` records; each string literal is emitted immediately after its self-pointer) |
| 0x0803F4B0–0x0803F... | ROM/data | `strings` | UI strings: `%s - %d%%`, `Defeat Section`, `Defeat Section 100%`, `Slow Motion`, `Start Game`, `View Credits`, `Select a Slot`, `Resume`, `Quit Level`, `Sound`, `Sleep`, `Enter Initials: ---`, level/song names |
| 0x08016640 | ROM/code | xref from literal 0x08016680 | generic menu-screen builder; loads the table at 0x0803F084 (literal at 0x08016680), called from 0x08006AF4 / 0x08006E6A / 0x08007322 |
| 0x08007A74 / 0x08007A8C / 0x08007CE8 | ROM/code | literal xrefs | generic getters/setters for global EWRAM object at 0x02005408 — **not** a validator |
| 0x020034E4 | EWRAM | savestate diff | keypad cursor/index (00 → 01 when a character is picked) |
| 0x02005408 | EWRAM | savestate diff | current initials character (00 → `0x41` 'A'); cleared to 00 on confirm |
| 0x02005400 | EWRAM | literal xrefs | nearby game-state block (0x08005D34 … 0x08006248) |
| raw 0x19000 / raw 0x21000 | savestate | layout check | IWRAM 0x03000000 / EWRAM 0x02000000 |

## 5. Algorithm

Not applicable — no code/password validator or generator was found. The only algorithmic surface is the initials keypad, whose state transition is trivially `cursor ∈ 32 cells; A commits char; B backspaces; OK commits field`, with no checksum and no comparison against stored constants.

## 6. Tables

**Initials keypad alphabet (32 cells + OK)** — observed at the `ENTER INITIALS` screen:

| Row | Cells |
|---|---|
| 1 | A B C D E F G H |
| 2 | I J K L M N O P |
| 3 | Q R S T U V W X |
| 4 | Y Z `-` `!` `?` `$` `@` `OK` |

This is a **name-entry** alphabet (3 initials), not a 32-symbol password alphabet like Car Battler Joe's. The field's consumer writes one byte at `0x02005408` per selection and clears it on OK; no `strcmp`/table comparison against the entry buffer was located (the only three literal xrefs to 0x02005408 are getters/resetters at 0x08007A74 / 0x08007A8C / 0x08007CE8).

**Reachable menu item sets** (all strings decoded from the ASCII bank at 0x0803F084; tile-rendered on screen but stored as plain ASCII):

| Screen | Items | Count |
|---|---|---|
| Title | Start Game, View Credits | 2 |
| Slot select | New Game ×3, Erase, (B Back) | 4 + back |
| Pause | Resume, Quit Level, Sound, Sleep | 4 |
| Sound | Music, SFX, Exit | 3 |
| Initials | 32-symbol keypad + OK | 32 + OK |

No `Level Select`, `Cheat`, `Debug`, `Secret`, `Enter Code`, or `Password` entry exists in any menu.

## 6b. Enumeration

This section states the complete searched space and proves the negative (guide §0.2 point 5, §16.3, §16.18).

**1. Code/password space — size 0 (no system).**
- `strings -t x -n 4` over all 8 MiB: **104,442** strings. Case-insensitive grep for `password|cheat|debug|secret code|codebreaker|gameshark|action replay`: **0 hits**. Broader `secret|unlock` returned only 2 narrative dialogue lines (0x0803FDCF: "unlock a mini-game!" — a subway-token collectible; 0x08042757: "I won't tell your secret" — dialogue). Neither is a code.
- Full text-bank decode of 0x0803F480–0x08042000 (ASCII, not tile-indexed — the *display* uses a font but the stored bank is plain ASCII): every word-like string is a menu label, level name, song name, or character dialogue. No debug overlay, no code prompt, no unused menu label.
- Only one embedded GBA header (logo scan), so no second game/half with its own code system.

**2. Button-code space — size 0 (no table, no gate).**
- Exhaustive scan of ROM[0, 0x450000) for 3-consecutive u16 single-button masks (active-high and active-low): 73 raw candidates, **all false positives** — inspection shows structured animation/script data (values 1/2/4/0x4000, e.g. 0x0802D270–0x0802D35C) and coincidental instruction encodings, none with a validator xref or terminator structure. A similar scan over the whole 8 MiB found hits only in compressed graphics/audio regions (0x085xxxxx+, 0x08Cxxxxx+).
- Literal 3/4-press prefixes of every published console code (Konami, pearl→coin `B,A,B,B,B,A,B,B`, attack `B,B,B,B,A,B,B,B,B`, invincibility, L+R+Start+Select) searched as u16 arrays: **0 hits in code regions**.
- **Dynamic rejection:** seven combinations pressed on the title screen from a savestate — `L+R+Start+Select`, `A+B+Start+Select`, `L+R+A+B`, Konami (↑↑↓↓←→←→ B A), `L+R` held 2 s, `Select+Start`, `L+R+Start`. Result: six produced only the normal START→slot-select transition (verified screenshot), `A+B+Start+Select` and `L+R+A+B` produced **no change at all** (0 differing pixels). No hidden menu opened.

**3. Hidden/debug menu — 0 entries reachable, 0 debug strings.**
- All menu item sets enumerated in §6; none contains a debug/cheat entry. The three "Defeat Section / Slow Motion" strings are in the shared bank but have no menu item that selects them — they are in-game stat/power-up labels (the `%s - %d%%` formatter at 0x0803F4B4 is used for completion percentages).
- The subway-token collectible → minigame unlock is a **save-bit progression feature** (dialogue at 0x0803FDCF), not a code system and not controller-triggerable; per §16.18 it is out of scope and not a code.

**4. Published GBA codes — verified absent.**
- GameFAQs (standalone GBA SKU 919968): no cheats section. GameFAQs 2-in-1 GBA page: all listed codes are XBOX/PS2/GC controller-screen sequences. VGChartz GBA page: "Total cheats available: 0". Cheat Happens GBA: "no cheats or cheat codes". GameHacking.org / Codejunkies "Debug Menu" entries are PS2/GameCube cheat-device codes (L1+L2 / L+Z), not GBA and not developer-intended.
- No published code literal appears in the ROM under any encoding searched (ASCII, `+0x20`, u16 button masks).

**Conclusion.** The accepted-code space is exactly the empty set; there is no alphabet/length/checksum to enumerate, no novel code to mint, and no bounds to prove by rejection because no validator exists. Bounds were instead proven on the *search* (counts above) and on the *input surfaces* (7 rejected button combos, 1 non-password text field whose buffer is never compared).

## 7. Validation evidence

**Observed** (emulator/screenshot/savestate):
- Boot logo, title, slot select, initials keypad, level-intro card, dialogue, gameplay HUD, pause menu, sound menu, credits — screenshots in `/tmp/sharktale/*.png`.
- Initials RAM proof: savestate diff `st_initials.ss1` → `st_initials_A1.ss1` changed EWRAM `0x020034E4: 00→01` (cursor) and `0x02005408: 00→41` ('A'); after OK, `0x02005408` reads `00` again in `st_ingame.ss1`.
- Button-combo tests: pixel-diff counts recorded above; nothing beyond normal navigation.
- Crop geometry obtained from `xdotool getwindowgeometry` (window 720×480 at 154,184 on :318).

**Derived** (static):
- Single retail header, stock entry word; string-pointer table and menu-builder xrefs; text-bank decode; button-mask scan counts; literal xrefs to the initials buffer.

**Inferred** (labelled):
- "Defeat Section"/"Slow Motion" are stat/power-up labels (code path not fully decompiled; no debug-menu selector references them).
- Subway-token minigame unlock is a save-bit progression feature.

## 8. Unknowns

- The post-completion state (all chapters cleared) was not played through; a level-select or gallery *could* appear there. No such string, menu item, or gate was found statically, and all published GBA sources list none, so this is a narrow residual unknown rather than a tested negative.
- "Slow Motion" exact gameplay effect was not isolated (pickup name inferred from the text bank).
- The save format (SRAM/Flash) and unlock-bit layout were not reversed — out of scope (progression, not cheats).

## 9. Tooling

- `strings`, `grep`, `xxd`, `python3` (hash/header/logo scan, pointer/xref scans, button-mask scan, text-bank decode).
- `arm-none-eabi-objdump -M force-thumb` for code at 0x08016640 / 0x08007A74 / 0x0802Dxxx.
- `mGBA 0.10.5` under `Xvfb :318` + `openbox`, `scrot`, `xdotool`, ImageMagick `convert` (window-relative crops and pixel diffs).
- `ssdiff.py` — decompresses the mGBA `.ss1` `gbAs` zlib chunk and diffs IWRAM/EWRAM.
- `ui.py`, `gshot.py`, `xref.py`, `button_scan.py` — input, capture, pointer/xref, and mask-table scanners (all under `/tmp/sharktale/`).
- GDB stub note: this mGBA build hardwires `-g` to port 2345, which another concurrent agent owned; all RAM evidence here therefore uses savestate diffs (guide §16.13) rather than the stub. No other agent's processes or displays were touched.

No ROM content or copyrighted assets are redistributed; this report contains only hashes, addresses, counts, and observations.
