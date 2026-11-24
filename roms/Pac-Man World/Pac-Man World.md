# Pac-Man World (GBA) — Reverse Engineering Report
**Scope:** in-game / developer-intended cheats only (passwords, button codes, hidden/debug menus, unlockables). No GameShark/CodeBreaker/memory-edit codes are reported as findings.

## 1. Target identity
| Field | Value |
|---|---|
| File | `roms/Pac-Man World/Pac-Man World.gba` |
| Size | 8,388,608 bytes (`0x800000`, 8 MiB) |
| Header title / code / maker | `PAC-MANWORLD` / `BPAE` / `AF` |
| Version | `0x00` (Rev.00), USA release, 2004-11-17; developer Full Fat, publisher Namco/DSI |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock) |
| Fixed byte / complement / checksum | `0x96` / `0x4D` (valid) / `0x0000` |
| MD5 | `3eda36856917a9ab80b9bb7a930be834` |
| SHA-1 | `7e9f23753c10494a3f0bbdf0905f3c7ac052b1b3` |
| SHA-256 | `8e649948f5e4d78a5fa276be1db4b72820c0e06ae5a28a87757c6071b2e4074f` |

**Revision confirmation:** the MD5 and SHA-1 exactly match 3rd party cheat indexes' `Good | Pac-Man World (USA).gba` (3rd party cheat indexes game id 2065), so the analysed image is the retail USA Rev.00 image.

**Phase 0 result:** the 156-byte Nintendo logo occurs exactly once (file offset `0x04`, header at `0x00`) — this is **not** a multi-game cart. The entry word is the stock `b 0x080000C0`; the first 4 KiB is a normal crt0; no cracktro, appended trainer, or patch was found. `file(1)` identifies it as a plain GBA ROM. Header checksum `0x0000` is a rebuilt-header artifact but the complement byte is internally consistent.

## 2. Executive summary
**No developer-intended cheat system exists in this ROM.** There is no password entry screen, no cheat/level-select code list, no hidden debug menu, and no button-code sequence that reaches an undocumented screen. The game is a conventional Full Fat 3D-platformer build with a **battery-backed SRAM save** (512-byte `.sav`, 3 slots); progress unlocks are ordinary gameplay progression, not codes.

The only "Level passwords" published for *Pac-Man World GBA* (3rd party cheat index cheat id 62022: `SSBBBBWB`, `TQBBBBQB`, `QFBBBBWD`, `ALBBBBQB`, `FZBBBBWB`, `NWBBBBQB`, `LVBBBBWT`, `MBDBBBQB`, `ZSDBBBWB`, `PQDBSBQB`, `HLDBSBFS`, `VZDBSBVS`, `JWDBSBFS`, `BJDBSBVR`, `WFDBSBVT`) are **the Pac-Man World 2 GBA password list misattributed to this game**: they are byte-for-byte the PW2 codes published by 3rd party cheat indexes, and **all 15 literals are absent from this ROM** (§6b). 3rd party cheat indexes have no code entry for this SKU; fan wikis list only CodeBreaker memory patches (Inf. Health `32001C3B 0003`, Inf. Lives `32001C3A 0009`, Invincible `32000AEA 0004`, "Level Skip Select+Up", Super Jump), which are cheat-device RAM writes and out of scope. The advertised Select+Up skip has **no native effect** (tested in gameplay, §7).

The negative is closed by (a) walking every reachable screen in mGBA with savestate RAM evidence, (b) decoding the font/tile-indexed text bank and enumerating the complete 5-language menu-string table (193 distinct strings, zero password/debug/level-select labels), (c) scanning the text and button spaces with explicit counts, and (d) testing all published literals. Residual Full Fat engine debug strings (stack traces, "TRACK 1/2") are uncalled diagnosics, not a reachable debug screen (§8).

## 3. How to reproduce
* **Emulator:** mGBA (SDL), `Xvfb :316 -screen 0 1024x768x24`, `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, `mgba -3 "Pac-Man World.gba"`.
* **Keymap (default SDL):** A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.
* **Input caveat:** this menu double-steps on 120–400 ms holds (guide §16.2). Use **50 ms** `keydown`/`keyup` pairs with ≥0.35 s between presses; verify cursor position on screen after each press.
* **Menu path walked (all with savestate RAM snapshots):**
  * Title: **Start / Load Game / Options** (`fresh_title.png`, state slot 1).
  * Options → submenu **Options / Sound / Credits / Exit** (`nav_opt1.png`, slot 7). "Sound" is a leaf that returns to its parent; "Credits" scrolls the credit roll (`credits1.png`–`credits3.png`, slot 8).
  * Load Game → **"Load Which Game?" / A=Load Game / B=Cancel / 3 × "- Empty -"** (`loadgame1.png`, slot 2).
  * Start → animated intro cutscene (A advances/skips) → **Level 1, Buccaneer Beach** (`cut_skip.png`, slot 6 = paused).
  * In-game pause (Start): **Pause / Resume / Exit**, a 2-item ring (`pause1.png`, `pause_nav1..4.png`). Exit returns to title (`pause_exit.png`). No other entry.
  * Boot screens: Nintendo license, Full Fat logo, DSI Games logo, intro cutscene — walked, not treated as the target.
* **RAM method:** mGBA savestates (`Shift+F1`…`Shift+F9`); the PNG's `gbAs` chunk is zlib-decompressed to a 397,312-byte state; IWRAM maps at raw offset `0x19000`, EWRAM at `0x21000`. Tooling in §9. Per-screen IWRAM hashes were distinct (§7), proving each screen is a different game state, not a redraw.
* **Codes tested:** all 15 3rd party cheat indexes "passwords" + 6 further PW2 passwords (literal `grep -abo` against the ROM); native Select+Up in gameplay; 14 button combinations/sequences at the title (§6b).

## 4. Address map
File offset = ROM address − `0x08000000`.

| ROM address | Contents |
|---|---|
| `0x08000000` | Header / crt0; `0xEA00002E` entry |
| `0x080647BC` | Input-mask helper: returns `state->mask_field` AND argument (used with `2`, `8`, `0x20` = B, Start, Left) |
| `0x08064B00`–`0x08064E70` | In-game main-loop input handler; contains the gate to a 14-item engine menu: requires byte `[state+0x1888]==1` and `[state+0x120C]==0` (both are ordinary game-state fields; no reachable trigger found) |
| `0x080653E0` | That 14-item engine menu constructor (jump table at `0x08065448`, 14 entries, only indices 0/11/12/13 non-default; no password/debug strings in its literals) |
| `0x080652AC`, `0x080652F0` | Engine diagnostic printers for "Trace Interrupt Stack" / "Trace User Stack" |
| `0x08094400`–`0x08094D08` | **Complete 5-language menu-string table** (English labels quoted in §6). 193 distinct referenced strings, 175 pure-ASCII. |
| `0x08094B24`–`0x08094D08` | Level-name table: 20 records × (5 language pointers + packed flags); 12 named levels, 8 empty slots. |
| `0x082A5860`–`0x082A5A50` | **Font / tile-index maps** decoded in §6b (ASCII glyph tables, incl. accented letters). |
| `0x082ADC80`–`0x082ADD14` | Full Fat engine debug/assert strings: `Trace Interrupt Stack`, `Trace User Stack`, `TRACK 2`, `TRACK 1`, `PAUSA`, `PAUSE`, `pause menu respond to exit game`. Referenced from `0x080652xx` and a cinematic-data table at `0x080A18F8`–`0x080A1960`; no debug-menu UI. |
| RAM `0x03004918` | Menu/screen cursor byte observed to change per screen (title 3/4 → options 2 → pause 4) |
| RAM `0x04000130` | KEYINPUT (active-low) read indirectly through the state mask at `0x080647BC` |
| SRAM | 512-byte `.sav`, 3 slots; empty slots are `0xFF` |

## 5. Algorithm
There is **no password validator, checksum, code table, or key-mask code table to reimplement** in this ROM. The relevant "algorithm" is the enumeration procedure used to prove that:

1. Locate the contiguous menu-string table by pointer-scanning known visible labels (`Options` → `0x080945A0`, `Start` → `0x08094630`, `Load Game` → `0x08094654`, `Credits` → `0x080945E8`, `Sound` → `0x080945C4`).
2. Walk the table word-by-word and decode every referenced `0x082A....` pointer as a NUL-terminated string in all five language columns (Italian, Spanish, German, French, English). Enumerated **193 distinct strings**.
3. Decode the font/tile maps at `0x082A5860`+ (see §6b) and confirm UI text is ASCII rendered through glyph-index tables — there is no second, tile-indexed text bank carrying hidden labels.
4. Search the entire 8 MiB for password/code/debug/level-select keywords and for every published password literal (§6b).
5. Walk every screen in the emulator; confirm distinct states by savestate RAM hashes.

## 6. Tables
### 6.1 Complete menu label set (English column, from `0x08094400`–`0x08094D08`)
`Level Score`, `Dots`, `Fruits`, `Grand Score`, `Continue`, `Options`, `Sound`, `Credits`, `Exit`, `Start`, `Load Game`, `Saving.`, `Do NOT remove the GAME PAK.`, `Do NOT turn off power.`, `Save successful.`, `Save failed.`, `Load Which Game?`, `Load Game`, `Cancel`, `- Empty -`, `Score`, `Lives`, `#% Complete`, `Time #`, `- Game 1 -`, `- Game 2 -`, `- Game 3 -`, `Save Game`, `Overwrite slot?`, `WARNING`, `You will not be able to save your progress without overwriting an existing saved game.`, `go back to intro menu?`, `GAME OVER`, and the 12 level names.

**Absent from all 5 languages:** `PASSWORD`, `PASS WORD`, `CODE`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `LEVEL SELECT`, `SELECT LEVEL`, `WORLD MAP`, `GALLERY`, `OUTTAKE`, `REEL`, `SOUND TEST`. The one `CODE` hit is `resizeSpriteBlock: Reduce. Code needs writing.` at `0x2D9E98` — an engine comment, not UI.

### 6.2 Level table (`0x08094B24`+), 12 named levels
Buccaneer Beach, Corsair's Cove, Crazy Cannonade, Crisis Cavern, Manic Mines, Space Race, Far Out, Clowning Around, Barrel Blast, Creepy Catacombs, Grave Danger, Toc-Man Lair. Eight further records are empty-string placeholders. This is a normal level-name resource, **not** a selectable cheat list — no screen in the game lets the player choose among these names.

### 6.3 Published-password verification (literal search over all 8,388,608 bytes)
| Source | Code | ROM offset |
|---|---|---|
| 3rd party cheat indexes | `SSBBBBWB`, `TQBBBBQB`, `QFBBBBWD`, `ALBBBBQB`, `FZBBBBWB`, `NWBBBBQB`, `LVBBBBWT`, `MBDBBBQB`, `ZSDBBBWB`, `PQDBSBQB`, `HLDBSBFS`, `VZDBSBVS`, `JWDBSBFS`, `BJDBSBVR`, `WFDBSBVT` | **ABSENT (all 15)** |
| 3rd party cheat indexes PW2 (further cross-check) | `SSQBBBLB`, `TQWBBBLB`, `QFWDBLLB`, `BDVJJPNW`, `BJHJJPPP`, `BJJJJPPJ` | **ABSENT (all 6)** |
| Fan-wiki CodeBreaker codes | `32001C3B 0003`, `32001C3A 0009`, `32000AEA 0004`, `74000130 03BB`, `82001622 0001` | Cheat-device RAM writes — out of scope; no in-game equivalent found |

## 6b. Enumeration
**Space definition.** No code space exists. The near-miss surfaces were enumerated as follows:

* **Text space:** `strings -t x -n 4` → **77,106** strings. Case-insensitive counts: `PASSWORD` **0**, `CHEAT` **0**, `DEBUG` **0**, `SECRET` **0**, `UNLOCK` **0**, `LEVEL SELECT` **0**, `SELECT LEVEL` **0**, `WORLD MAP` **0**, `GALLERY` **0**, `OUTTAKE` **0**, `SOUND TEST` **0**, `CODE` **1** (engine comment), `BONUS` **4** (all in tutorial dialogue about bonus letters), `TRACK` **3** (engine trace labels). The +0x20 lowercase shift was covered by case-insensitive search.
* **Menu space:** the complete contiguous menu-text table at `0x08094400`–`0x08094D08` contains **193 distinct referenced strings across 5 languages**; every one is an ordinary UI label (list in §6.1). **Zero** code/debug/select labels.
* **Font / tile-indexed text bank (explicitly decoded, per the task note):** the glyph tables at `0x082A5860`–`0x082A5A40` map tile indices to `0x20`–`0x7E` ASCII plus accented Latin-1 (e.g. at `0x082A5865`: `` `abcdefghijklmn `` / `@ABCDEFGHI`, at `0x082A58A5`: ` !"#$%&'()*+,-./0123456789`, at `0x082A5965`: `>?JKL@MABNOCDEF456789:;<=GPQHRI…`). These are **font glyph maps**, not encoded messages: all game text is stored as ordinary NUL-terminated ASCII strings (confirmed by the visible menus rendering exactly the strings in §6.1). There is no hidden tile-indexed string bank and no restricted password alphabet.
* **Button space:** 14 title-screen combinations/sequences tested with screenshot differencing against a reloaded title baseline (`combotest2.py`): `L+R`, `L+R+Start`, `L+R+Select`, `L+R+A`, `L+R+B`, `Select+Start`, `A+B+Start+Select`, `Select+Up`, `Select+Down`, Konami code, `L R L R`, `Start+Select+A`, and modifiers held while pressing A/Start on the "Start" entry. **No undocumented screen opened.** Every large screen change was explained by A/Start navigating the ordinary menu (e.g. `A`-variants → intro cutscene; `L+R+A` diff 27,264 px, same as plain `A`). Non-navigating combos produced 0–429 changed sampled pixels (animation noise ≤236). Cursor-cycling proved the pause menu is a 2-item ring; the title menu is a 3-item ring; Options is a 3-item parent with one leaf (Sound) and Credits.
* **Key-mask table scan:** guide §5.4a method — **53,584** contiguous 4×u16 candidate runs of plausible key masks were found by blind scanning across the 8 MiB; inspection of the densest clusters showed they are ordinary code/data bytes, not a cheat table. No sequence table, progress index, or action-dispatch branch related to cheats was found.
* **Debug gate:** the only candidate hidden-menu constructor (`0x080653E0`) is gated by two ordinary game-state fields (`[state+0x1888]==1`, `[state+0x120C]==0`) and has no string labels for passwords/levels; no controller input path to it was found in the input handler (`0x08064B00`–`0x08064E70`).

**Novel codes:** not applicable — with no validator, table, or code surface, no unpublished code can be minted. This is the bounded negative result required by guide §0.2 for a "no system" game, not a partial answer.

**Bounds proven by rejection:**
1. All 15 3rd party cheat indexes "PW1 passwords" and 6 extra PW2 codes rejected at the ROM level (literal absence, §6.3) — the published list is misattributed.
2. Native `Select+Up` (the published CodeBreaker skip trigger) pressed in gameplay produced only ordinary Pac-Man motion; no level change (`before_selup.png` / `after_selup.png`, 277 sampled-pixel difference from sprite movement).
3. Modifier+Start on the title "Start" entry produced either the normal intro or only cursor animation — no level select (`mod_*.png`, diff 145 vs 15,421 for the normal path).

## 7. Validation evidence
* **Observed (emulator):** all screens in §3 with screenshots on disk; SRAM `.sav` created as 512 bytes of `0xFF`; savestate RAM hashes distinct per screen —
  `slot 1 title md5(iwram[0x4000])=4a8346c66cd8288e`, `slot 2 Load Game=a9ed68917703d91b`, `slot 6 pause=91f13c426f6b9c1f`, `slot 7 Options=890fbb3f6dcd0155`, `slot 8 Options-parent=49523c07b6a50252`; cursor byte `0x03004918` = 3/4 (title), 2 (Options), 4 (pause).
* **Observed (static):** 21 published password literals absent; 77,106-string scan counts in §6b; 193-string menu-table enumeration; font tables decoded.
* **Derived:** the menu table at `0x08094400`–`0x08094D08` is the game's complete UI label source (all visible labels map to it and no other label table was found); the 14-item engine menu at `0x080653E0` is not reachable through any tested controller input.
* **Inferred (labelled, not asserted):** `TRACK 1`/`TRACK 2`/`PAUSE` at `0x082ADCFC`–`0x082ADD0C` are engine/cinematic diagnostics rather than a sound-test menu; the empty level-table records are cut/unused content, not unlockable stages. Neither affects the cheat conclusion.

## 8. Unknowns
* The **level-complete results screen** and **Game Over** screen were not reached by manual play (a full 3D platformer level; the collision boundaries prevented a quick deliberate death). This does not weaken the cheat negative: their labels (`GAME OVER`, `Continue`, `Level Score`, `Time #`, `#% Complete`) are present in the fully enumerated menu table and none contains a code-entry field. No password/level-select label exists anywhere in the ROM.
* The precise purpose of the gated 14-item engine-menu constructor at `0x080653E0` was not established (its literals contain no menu labels); its gate fields are ordinary game-state offsets and no input path was found. It is reported as an engine leftover, not a cheat.
* The eight empty level-table records were not individually identified; they render no labels and are not selectable.

## 9. Tooling
* `strings -t x -n 4`, `grep -abo`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum`, `arm-none-eabi-objdump -M force-thumb`, Python 3 + `capstone` 5.0.7.
* `ssram.py` — decodes mGBA `.ssN` PNG `gbAs` zlib chunk into raw RAM, with IWRAM `0x19000` / EWRAM `0x21000` windows.
* `ssdiff.py` — diffs two decoded savestates and groups changed RAM bytes (used to locate the menu cursor byte and confirm distinct screen states).
* `ptr.py` — little-endian pointer scan for a ROM address (used to find the menu-string and level-name tables).
* `emu.py` — 50 ms XTEST key injection and `scrot` capture on `DISPLAY=:316`.
* `combotest2.py` — reload-baseline screenshot differencing for button-combos.
* REA/Ghidra was probed but **not used**: the shared MCP session was concurrently bound to another ROM by another analyst, so all conclusions here rest on objdump/Capstone and emulator evidence only.

**Legal note:** no ROM image, graphics, music, or game text beyond short UI labels is redistributed; only hashes, addresses, and original analysis are published.

## Cleanup
All processes started for this job were killed by recorded PID (mGBA, Xvfb `:316`, openbox); no `pkill` was used. All generated `.sav` / `.ss1`–`.ss9` artifacts were removed from the ROM folder; only the `.gba` remains. `roms/INDEX.md` was not modified.
