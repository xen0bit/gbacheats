# Shining Soul II (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Shining Soul II.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| `file` identification | Game Boy Advance ROM image: "SHININGSOUL2" (AU2EEB, Rev.00) |
| Header title | `SHININGSOUL2` |
| Game code | `AU2E` (serial AGB-AU2E-USA — i.e. the USA/English release) |
| Maker code | `EB` (Atlus) |
| Version | 0x00 |
| MD5 | `f4a655e23638e79eacf44a456faee6a4` |
| SHA-1 | `541469b319a72ef4bc262483745526ac3eddd925` |
| SHA-256 | `b31c19d2d25683a0941d5d501912b5f21d4590cd7071fa01882e62aa5227a7c9` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock) |
| Fixed byte 0xB2 | `0x96` (present) |
| Embedded headers | exactly one, at file 0x0 (Nintendo-logo scan over the whole file) |
| Patch / trainer | none found — stock crt0, no appended trainer, no second logo |

Header oddity (recorded, not consequential): the complement byte at 0xBD is `0x38` and the checksum word at 0xBE–0xBF is `0x0000`; `(sum[0xA0..0xBC]+0x38)&0xFF = 0xE7 ≠ 0`. The game boots and runs correctly, so this is a dump/rebuild artifact, not a modified game image.

## 2. Executive summary

Two developer-intended cheat surfaces exist in this ROM, and both were reversed and confirmed in mGBA:

1. **Sound Test — a 13-press button code** at the boot logos, plus a second gate at the title/main menu. The expected key-mask sequence is a 13-byte table at ROM `0x0856F468`; the validator at `0x08091758` compares each press against a progress index and, when all 13 match, calls scene-setter `0x08058588(0x33)`. Published listings give 12 directions and often omit the **13th press, B**; the ROM proves B is required. Entered correctly in the emulator (including the trailing B), the game opens a **Sound Test screen** (piano keyboard, "shining soul II", L/R volume, A/B buttons) — observed directly.
2. **Name codes — a 16-entry lookup table** used at character creation. Entering a specific handle as the character name grants a starting bonus. The strings are stored as u16 font-glyph indices in the credits text bank; the pointer table is at ROM `0x083DA1D0`. Thirteen entries match published GameFAQs lists; **three entries (`Undead`, `Flying`, `Press`) are present in the ROM but absent from every published list**. `Yoshi` was verified in-game to grant DEX 20 (baseline 15), and `Undead` was verified in-game to be accepted (status screen renders `NAME:Undead`). The published spelling `Saophen` is a typo for the ROM's `Saohen`.

Save-bit unlockables (Advanced Mode, the secret Dark Wizard) also exist but are gated behind a completed playthrough, not a code; they are documented in §8 as inferred/gated, not as codes.

No password screen, cheat menu, or code-entry UI exists anywhere in the reachable game. The whole reachable screen graph was walked (§7).

## 3. How to reproduce

**Toolchain:** mGBA 0.10.5 (`/usr/local/bin/mgba`), Xvfb `:316`, openbox, `SDL_AUDIODRIVER=dummy`, `xdotool`, `scrot`, `arm-none-eabi-objdump`, Capstone, Python 3. mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold keys ≥60 ms; savestates `Shift+F1..F9`, load `F1..F9`.

### 3.1 Sound Test (verified)
1. Launch the ROM. During the **SEGA / ATLUS boot logos** (the validator only runs inside the boot loops at `0x0800242C/0x0800243E/0x08002454`), press, one per frame:
   `↑ ↓ ↑ ↓ ← → ← → ↑ → ↓ ←` then **B** (`z`).
2. Continue to the title ("PRESS START"), press Start to show `SINGLE PLAYER MODE / MULTIPLAYER MODE`.
3. With an option highlighted, **hold Start (`Return`) and press A (`x`)**.
4. Result: the Sound Test screen appears (screenshot proof in work dir `soundtest_c.png` / `st7_c.png`).

Timing note: each press must be a distinct key-down edge; rapid/overlapping arrows desynchronise the sequence. 0.06 s hold / 0.06 s gap entered at ~0.5 s after launch produced progress index 13 (accepted). Entering `b` (key name) instead of `z` (GBA B) left progress at 12 and did not open the screen — see §6b.

### 3.2 Name codes (verified)
1. Title → Single Player → free slot → New Game → choose class → colour → **name entry** (mixed-case on-screen keyboard, max 8 characters).
2. Enter a name, press Start, confirm YES. The bonus is applied and is visible on the in-game **Status** screen once the intro ends.
3. Baseline Warrior (`Eric`): STR/DEX/INT/VIT = 15/15/15/15, ATK 23, DEF 3.
4. `Yoshi` → STR/DEX/INT/VIT = 15/**20**/15/15 (published `dex +5` confirmed).
5. `Undead` → 15/15/15/15, status renders `NAME:Undead` (novel name accepted; no stat change observed).

For fast probing, the name buffer was patched in mGBA savestates with `/tmp/opencode/shiningsoul2/patch_state.py` (raw state offset `0x24870`, EWRAM `0x3870`) and reloaded — this is an analysis probe only; the final confirmations above were driven through the real UI.

## 4. Address map

| Item | ROM address | File offset | Notes |
|---|---|---|---|
| Key-mask code table | `0x0856F468` | `0x56F468` | 13 bytes: `40 80 40 80 20 10 20 10 40 10 80 20 02` |
| Button validator | `0x08091758` | `0x91758` | Thumb; BL xrefs `0x0800242C`, `0x0800243E`, `0x08002454` |
| Scene-setter called on success | `0x08058588` | `0x58588` | `bl 0x08006884` with `r0=0x33` |
| Name string pointer table | `0x083DA1D0` | `0x3DA1D0` | u32 pointers; name entries are table indices 5–20 |
| Name strings (u16 glyphs) | `0x083D56B4`–`0x083D57DA` | `0x3D56B4`–`0x3D57DA` | each preceded by `FFFD 0000 0001`, terminated by `FFFF` |
| SE/sound-effect label bank | `0x0856D0A6`–`0x0856F44E` | `0x56D0A6`–`0x56F44E` | ASCII debug labels (sound test track names) |

| RAM / state | Address | Purpose |
|---|---|---|
| Name buffer | EWRAM `0x02003870` | 8×u16 glyph indices + `0xFFFD` terminator |
| Button-code progress | IWRAM `0x03000280` | u8, 0–13; reset on wrong press |
| Key-state snapshot | IWRAM `0x03001444` | u16 active-high mask read by validator |
| Scene/flag word | IWRAM `0x030028F0` | read by `0x08058588`, passed to `0x08006884` |

Savestate layout (guide §16.13): mGBA `.ssN` is a PNG with a zlib `gbAs` chunk → 397,312-byte raw state; IWRAM at raw `0x19000`, EWRAM at raw `0x21000`; name buffer therefore at raw `0x24870`.

## 5. Algorithm

### 5.1 Button-code validator (precise, `0x08091758`)

```
progress = u8 @ 0x03000280          # IWRAM
keys     = u16 @ 0x03001444         # active-high mask this frame
table    = bytes @ 0x0856F468       # 13 expected masks

if progress == 13: return
expected = table[progress]
if keys == expected:
    progress = progress + 1
else:
    if keys != 0:
        progress = 0                # any wrong non-empty press resets
    # keys == 0 (no button): keep progress
if progress == 13:
    scene_set(0x33)                 # bl 0x08058588, r0 = 0x33
```

Key-mask encoding is the standard active-high GBA map: A=0x01, B=0x02, Select=0x04, Start=0x08, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200. The table values are one byte per press (all sequence buttons are in the low byte).

The success action is a single fixed action: `0x08058588` reads `0x030028F0`, tests bit 5 (`0x20`), and if clear calls `0x08006884(0x33)`. No dispatcher with alternate actions exists at this gate (the three BL callers all run the same validator in boot loops).

Second gate (title/main menu): hold Start while pressing A. The scene value set by the first gate changes the menu's A-handler so the sound-test scene is entered. This was confirmed visually, not by isolating the handler (see §8).

### 5.2 Name-code lookup

```
# at character creation
name = u16[8] @ 0x02003870           # glyph indices, 0xFFFD terminated
for i in 5 .. 20:                    # string-table indices
    expected = get_text_string(i)    # pointer table 0x083DA1D0 + i*4
    if u16_strcmp(name, expected) == 0:
        apply_bonus(i)               # per-index stat/item grant
        break
```

Glyph mapping (derived from the live name buffer, EWRAM `0x02003870`, holding "Eric" = `05 00 32 00 29 00 23 00`):
* upper A..Z → `0x01..0x1A`
* lower a..z → `0x21..0x3A`
* digits 0..9 → `0x41..0x4A`
* terminator `0xFFFD`; empty/unused glyph `0x0000`.

The per-index bonus values were not recovered from code (no static xref to the RAM name buffer or the string table was found); the mapping below is from the published list plus in-game observation.

## 6. Tables

### 6.1 Sound Test button table (ROM `0x0856F468`, 13 entries)

| # | Mask | Button |
|---:|---:|---|
| 1 | 0x40 | Up |
| 2 | 0x80 | Down |
| 3 | 0x40 | Up |
| 4 | 0x80 | Down |
| 5 | 0x20 | Left |
| 6 | 0x10 | Right |
| 7 | 0x20 | Left |
| 8 | 0x10 | Right |
| 9 | 0x40 | Up |
| 10 | 0x10 | Right |
| 11 | 0x80 | Down |
| 12 | 0x20 | Left |
| 13 | 0x02 | **B** (omitted from many published listings) |

### 6.2 Name-code table (ROM `0x083DA1D0` string indices 5–20)

| Table idx | Name | Published effect | Verified? |
|---:|---|---|---|
| 5 | Yoshi | dex +5 | **Yes** — DEX 20 vs 15 baseline |
| 6 | Iyoku | RFR +30 | published only |
| 7 | Vjum | Atlus Ring | published only |
| 8 | VJxSS | Power Gloves | published only |
| 9 | Ninky | str +5 | published only |
| 10 | Mizupin | RIC +30 | published only |
| 11 | Taicho | VIT +5 | published only |
| 12 | Hachi | RPO +30 | published only |
| 13 | Nindri | Dream Hat | published only |
| 14 | Saohen | RLT +30 | ROM spelling (published "Saophen" is a typo) |
| 15 | Montaka | RDK +30 | published only |
| 16 | Genomes | Genome Ring | published only |
| 17 | Dengeki | int +5, RTH +30 | published only |
| 18 | **Undead** | *not published* | **Yes** — accepted; `NAME:Undead`; no stat change seen |
| 19 | **Flying** | *not published* | present in ROM (static) |
| 20 | **Press** | *not published* | present in ROM (static) |

Published sources checked: GameFAQs cheats page, Planet Cheats, GameRevolution, GameHacking.org, Almar's Guides, CodeJunkies, and an Action Replay patch document. GameShark/CodeBreaker/Action Replay codes on those pages are cheat-device memory patches and are **out of scope**; they were read only for address hints and are not reported as in-game cheats.

## 6b. Enumeration

**Button-code space.** The table is exactly 13 bytes and the validator only advances on a full match; there is no dispatcher and no alternate action. Total accepted sequences = 1 (the 13-press sequence above). The "space" that was checked: all 16 MiB scanned for the active-high byte sequence (one hit, `0x56F468`), for the u16 little-endian form (0 hits), for the active-low form (0 hits), and for 2/3/4-press prefixes; the validator's three BL callers and all literals were disassembled. The trailing **B** (mask `0x02`) is the 13th and final entry. A published 12-press transcription without B is incomplete.

**Name-code space.** 16 accepted strings (table indices 5–20, strings `0x083D56B4`–`0x083D57DA`); the alphabet is the 62+ symbol on-screen keyboard (upper/lower/digits/symbols), length ≤ 8 glyphs. All 16 entries were decoded and are listed in §6.2. Thirteen are published; **three (`Undead`, `Flying`, `Press`) are absent from every published list consulted**. The novel code **`Undead`** was entered in the real name-entry UI and confirmed in-game: the status screen renders `NAME:Undead` and the intro dialogue addresses the character by that name. Its observed stat block equals baseline (STR/DEX/INT/VIT 15/15/15/15), i.e. no stat bonus was observed; a possible non-stat effect (item/flag) remains uncharacterised (§8).

**Bounds proven by rejection.**
* Button code, wrong final key: entering the first 12 presses with `b` (key name) instead of `z` (GBA B) left progress = 12 (read from IWRAM `0x03000280` in a savestate) and the Sound Test did **not** open — the 13th press must be B.
* Button code, wrong cadence: faster/overlapping arrows left progress = 5 and no activation; the validator's per-frame comparison reset semantics explain this exactly.
* Button code, no input: with progress > 0, idle frames (keys == 0) preserve progress rather than advancing — the `cmp r1,#0` branch at `0x8091784`.
* Name codes: `Eric` (not in the table) produces no bonus — baseline status 15/15/15/15, confirmed with a full UI run. This bounds the accepted set to the 16 table entries for stat bonuses.
* Name length: buffer is 8 glyphs + `0xFFFD` terminator at EWRAM `0x02003870` (observed by savestate diff); longer names cannot be entered.

**Exhaustiveness of "no other code system".** `strings -t x` (114,387 strings ≥4 chars; 47,859 ≥8 chars) was searched case-insensitively for password/cheat/code/debug/secret/unlock/bonus/hidden/sound test/shark/breaker/class/character: no ASCII hits beyond the SE/sound-effect label bank (`0x56D0xx`–`0x56F4xx`). The ROM's visible UI text is font/tile-indexed (u16), not ASCII, so text was decoded via the glyph mapping in §5.2 and every reachable screen was walked with screenshots (§7). Multiplayer uses the same file-select screen and exposes no password field. No standalone password screen, debug menu gate, or key-mask sequence other than `0x0856F468` was found in a full-file byte scan.

## 7. Validation evidence

**Observed (emulator screenshots / RAM reads):**
* SEGA/ATLUS logos, title "PRESS START", main menu (Single/Multiplayer), file select (8 slots), character select (8 classes), colour select, name-entry keyboard, intro cinematics, gameplay, pause menu (Status / Window / spell / equipment icons), Sound Test screen.
* Sound Test screen after the 13-press code + hold Start+A: piano keyboard, "shining soul II", L/R and A/B button labels; pressing A/Left/Right changed the small display glyph.
* Progress byte `0x03000280` = 5 (wrong timing), 12 (wrong 13th key), 13 (correct sequence) — read from uncompressed savestates.
* Status screens: `Eric` 15/15/15/15, `Yoshi` 15/**20**/15/15, `Undead` 15/15/15/15 with `NAME:Undead`.
* Name buffer at EWRAM `0x02003870`: `Eric` = `05 00 32 00 29 00 23 00 fd ff`, `Undead` = `15 00 2e 00 24 00 25 00 21 00 24 00 fd ff`.

**Derived (disassembly / static):**
* Button table contents, validator control flow, success action `scene_set(0x33)`, boot-only call sites.
* Name pointer table at `0x083DA1D0`, all 16 name strings and the glyph encoding.
* Absence of any other code table/password validator in the searched spaces.

**Inferred (not fully exercised):**
* The exact per-index bonus routine for name codes (no xref recovered).
* The title-menu Start+A gate handler that reads the scene value.
* The specific effect (if any) of `Flying` and `Press`.

## 8. Unknowns

* **Per-index name-code effect dispatcher** — the code that maps string index → stat/item grant was not located (no static xref to the RAM name buffer or the string table; GDB stub was single-client and unreliable in this environment). Effects in §6.2 are from published lists plus the two in-game checks; only `Yoshi`'s DEX +5 is directly confirmed. `Undead` showed no stat change; an item or flag effect is not excluded.
* `Flying` and `Press` were confirmed only statically (present as table entries); their in-game effects were not exercised.
* Sound Test track count / complete control list: A, Left, Right were seen to change the display; B/exit and the full track count were not exhaustively enumerated (the ASCII SE-label bank suggests dozens of tracks).
* **Unlockables** (gated, not codes): GameFAQs documents Advanced Mode and a secret Dark Wizard ("???") unlocked by clearing normal mode with any character; Planet Cheats additionally names "Gilspie". These are save-bit unlocks gated behind a clear flag, not input codes; reaching them requires a full playthrough, which was not performed. Reported as leads, not confirmed cheats.
* The SEGA balloon easter egg (sacrificing S/E/G/A letters in the Temple of Light) is a gameplay easter egg requiring deep progression; not exercised.

## 9. Tooling

Scripts in `/tmp/opencode/shiningsoul2/` (analysis aids, not shipped with the report):
* `mgba_helper.py` — xdotool `key`/`focus`/`shot`, mGBA `.ssN` PNG/`gbAs` zlib state reader (IWRAM `0x19000`, EWRAM `0x21000`).
* `patch_state.py` — patches the u16 name buffer at raw `0x24870` in a savestate and rebuilds the PNG (used only as a probe).
* `gdbcli.py` / `gdbpersist.py` — minimal GDB RSP clients for mGBA's `-g` stub (used to read registers and set the `Z2` watchpoint that located the key-state address; the stub proved flaky and was abandoned in favour of savestate diffs).
* Python one-liners using `struct`/`bytes.find` for header/logo scan, literal searches, Thumb LDR/BL scans, and glyph decoding.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.

Screenshots (work dir): `soundtest_c.png`/`st7_c.png` (sound test), ` bs3_c.png` (Eric baseline), `y_stat2_crop.png` (Yoshi DEX 20), `u2_c.png`/`us2_c.png` (Undead accepted), `mm3_crop.png`/`mm4_crop.png` (menus), `bt_sheet.png` (boot timeline).

Legal note: no ROM image, extracted graphics, or game assets are redistributed; only addresses, hashes, algorithms, and original tooling are published.

**Cleanup:** all emulator/Xvfb/openbox processes started for this job were terminated by PID, and generated `.sav`/`.ss1`–`.ss9` files were removed from the ROM folder.
