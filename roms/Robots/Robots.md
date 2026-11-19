# Robots (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Robots.gba` (same folder as this report) |
| Size | 16,777,216 bytes (0x01000000) |
| `file` | Game Boy Advance ROM image: "ROBOTS" (BRTE7D, Rev.00) |
| Header title | `ROBOTS` |
| Game code | `BRTE` (USA) |
| Maker code | `7D` |
| Version | `0x00` |
| Fixed byte | `0x96` @0xB2 (present) |
| Complement byte | `0xD0` @0xBD |
| Header checksum field | `0x0000` @0xBE–0xBF |
| Entry word | `0xEA00002E` → branches to `0x080000C0` (stock Nintendo branch) |
| MD5 | `d41363a54aa5ac45ecaff2dafcb9372b` |
| SHA-1 | `d69a60a4bf7fca1dc4204c959143524274cc826a` |
| SHA-256 | `547fd647fc2a79542c6b748af3af314f6befa81c921943645c9c93c847508753` |

**Embedded-header scan:** the 144-byte Nintendo logo occurs exactly **once**, at file offset `0x4` (i.e. one header, base 0). The file is a single 16 MiB image — no multiboot/2-in-1 halves, no appended trainer image. The entry word is the stock branch and the code at `0x080000C0` is ordinary crt0; no scene cracktro or cheat trainer was found. The `0x0000` checksum field and non-standard complement byte suggest a rebuilt/edited header, but nothing in the boot path is a cheat menu.

Developer/publisher from the boot legal screen: Amaze Entertainment / Blue Sky Studios, 2005. This is the **Amaze GBA engine**, not the Eurocom PS2/GC/Xbox engine — the platform distinction matters for published codes (§16.11).

## 2. Executive summary

**The GBA version of Robots has no developer-intended cheat code system: no password screen, no button-code validator, no hidden debug/level-select menu.** The only in-game "extras" are ordinary **save-gated unlockables**: a 10-slot `GALLERY` of locked clips, an "extra bounce" upgrade earned by beating the third boss, and minigames earned by completing the game. No code can be minted because no validator exists; the negative is bounded by exhaustive screen enumeration, literal/binary searches of all 16 MiB, and static input-handler analysis.

The only text-entry surface is the **save-slot name** (A–Z + `*`, Del/OK). Its input buffer is plain ASCII at IWRAM `0x03004244`; arbitrary strings such as `Q*Y` were accepted and stored in the save, which proves it is a label field, not a password (guide §16.2b).

Published button codes for the *console* versions (Big head `UDDURRLR`, Unlimited health `URDULDRL`, Unlimited scrap `DDLUURUD`) are **not present in the GBA ROM** in any encoding (active-high/active-low u16 or per-press byte, forward or reversed) and produced no visible effect when keyed into the GBA pause menu. TCRF's `Robots (Game Boy Advance)` page served a prompt-injection payload (fake "decode key.bin" EICAR string, billion-dollar payment demand, fake fatal error); it was treated as untrusted data and ignored (guide §16.8).

## 3. How to reproduce

- Emulator: `mgba` (SDL build, `/usr/local/bin/mgba`), Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, 1024×768 X display with `openbox`. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.
- Hold keys **45–70 ms** for a single cursor step; 80 ms can double-step (guide §16.2). Gallery/menu navigation sometimes needs ~150 ms.
- Boot path: legal screen → A → character splash ("BIG WELD") → Start → **main menu**.
- Main menu D-pad ring has exactly **three** states: `SELECT GAME` / `COPY GAME` / `DELETE GAME`. `START GAME` is a label, not on the ring; a new game is begun by choosing an **empty slot** in `SELECT GAME` (panel reads `NEW GAME`) and confirming a name.
- Name entry: `A B C … Z *`, `Del`, `OK`. Typed `AAA` in slot 1 and `Q*Y` in slot 2; both accepted.
- In-game: Start → pause menu `CONTINUE / MUSIC / SOUND / GAMMA / GALLERY / SAVE & QUIT`. `GALLERY` → 10 locked `?` tiles (2 rows × 5); the green up/down arrows wrap, no extra page was reached.
- Button codes tested at the pause screen with 45 ms presses: `UDDURRLR`, `URDULDRL`, `DDLUURUD`. No chime/message/flag/visual effect was observed.
- Debug combos tested at the main menu (`L+R+Start+Select`, `Select+A+B`): no hidden screen.
- Screenshots (RAM-corroborated) are in `/tmp/opencode/robots/` (`f_main_c.png`, `sel_slot2_c.png`, `name_QZX_c.png`, `pause_again_c.png`, `gallery1_c.png`, `f_copy_screen_c.png`, `savequit1_c.png`, `code_scrap_c.png`, `dbg_combo1_c.png`).

## 4. Address map

| Item | Address / offset | Evidence |
|---|---|---|
| ROM base / entry | `0x08000000` / `0x080000C0` | header, disassembly |
| Stock entry branch | `0x00000000` = `0xEA00002E` | observed |
| Input reader (KEYINPUT, `0x04000130`) | `0x0801E9C4`–`0x0801E9F6` (Thumb) | disassembly; `ldr r0,[pc,#48]` → pool `0x0801E9F8` = `0x04000130`, next word `0x000003FF` |
| Input state struct | pointer in `ip` (r12): `+0x10` held (active-high), `+0x14` newly pressed, `+0x16` released | `0x0801E9C4`–`0x0801EDA` |
| D-pad direction lookup | `0x0801EA30`–`0x0801EA46` (reads held `& 0xF0`, `>>4`, indexes byte table) | disassembly |
| Main-menu D-pad cursor | **IWRAM `0x03004200`** — `0`=`SELECT GAME`, `1`=`COPY GAME`, `2`=`DELETE GAME` | GDB reads with screenshots; 3-value wrap confirmed |
| Save-slot name input buffer | **IWRAM `0x03004244`**, plain ASCII, e.g. `51 2A 59` = `Q*Y` | savestate diff (`ss3` vs `ss4`), IWRAM offset `0x4244` |
| Name display tilemap (top/mid/bottom of each 8×24 glyph) | VRAM `0x0600E094`, `0x0600E0D4`, `0x0600E114` (mirrored at `0x0600F094` etc.) | VRAM diff: blank `0x017E`×6 → glyph triples `0x028C,0x028F,0x0292,…` |
| Glyph example rendered | base `0x28C` = `*`, `0x28F` = `Y` (3 stacked 8×8 tiles) | rendered from VRAM with live palette |
| Save file | 512-byte EEPROM (`Robots.sav`), magic `TBOR` @`0x04`, name `AAA` @`0x25` | save-file hex dump |
| mGBA savestate layout (16 MiB ROM) | `gbAs` zlib chunk → 0x61000 bytes: CPU/regs `0x0000`, VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000` | decompressed `Robots.ss2`–`ss4` |

## 5. Algorithm

There is no password/checksum algorithm to reverse. The relevant algorithms are:

```
; input sampling (0x0801E9C4), Thumb:
held_raw  = ldrh(0x04000130)
held      = held_raw ^ 0x03FF          ; active-high
pressed   = held & (held ^ previous)
released  = (~held) & (held ^ previous)
store held @ [ip+0x10], pressed @ [ip+0x14], released @ [ip+0x16]

; name entry:
buffer @ 0x03004244 := ASCII bytes (A-Z, '*')   ; no comparison to any constant
render: ASCII -> glyph table -> 3 stacked 8x8 tiles -> VRAM tilemap
```

The menu navigation is a 3-state ring (`cursor = (cursor ± 1) mod 3`) stored at `0x03004200`; `START GAME` is not a member of that ring. Unlockables are save bits in the 512-byte EEPROM; no input path writes them.

## 6. Tables

| Table | Contents |
|---|---|
| Main-menu cursor (`0x03004200`) | 0=`SELECT GAME`, 1=`COPY GAME`, 2=`DELETE GAME` |
| Pause menu (visual enumeration) | `CONTINUE`, `MUSIC`, `SOUND`, `GAMMA` (Normal), `GALLERY`, `SAVE & QUIT` |
| Gallery | 10 locked entries, 2 rows × 5, all `?` on a fresh save |
| Name-entry alphabet | `A`–`Z`, `*`, plus `Del` and `OK` (27 glyphs) |
| Save magic | `32 31 30 30 54 42 4F 52` = `"2100TBOR"` at EEPROM offset 0 |
| Published console codes (not in this ROM) | big head `UDDURRLR`; health `URDULDRL`; scrap `DDLUURUD` |

## 6b. Enumeration

**Code-space size: zero.** There is no password alphabet, no key-mask sequence table, no validator function and no hidden-menu gate reachable by input in this image. Consequently no novel code exists to mint; per guide §0.2 the negative is bounded by the counts below.

**Screen space enumerated (all with screenshots + RAM/savestate corroboration):**
1. Legal / copyright splash
2. Character splash ("BIG WELD")
3. Sky intro (Start skips)
4. Main menu (3-state D-pad ring; RAM cursor at `0x03004200`)
5. `SELECT GAME` slot screen (3 slots, `NEW GAME` panel)
6. `COPY GAME` slot screen (3 slots)
7. `DELETE GAME` slot screen (3 slots, `EMPTY`)
8. Name entry (27-glyph keyboard, ASCII buffer at `0x03004244`)
9. In-game gameplay
10. Pause menu (6 items)
11. `GALLERY` (10 locked tiles)
12. `GAME SAVED SUCCESSFULLY!` confirmation

**Search-space counts for the negative:**
- 16,777,216 bytes scanned for `password|cheat|code|debug|secret|unlock|level|menu|invalid`: **0** meaningful plaintext hits (all keyword-looking hits were compressed-data noise). Brute-forced 256 additive, 256 subtractive and 256 XOR byte transforms of `PAUSE`, `CONTINUE`, `GALLERY`, `MUSIC`, `SOUND`, `GAMMA`: **0** coherent text hits; also 0 hits for UTF-16LE/BE and every single-byte interleaving. This proves the UI uses a font/tile-index renderer, not an ASCII text bank.
- The rendering path was decoded anyway: text is drawn as 3 stacked 8×8 tiles (8×24 glyphs) loaded into VRAM at runtime; glyph bases `0x28C`=`*` and `0x28F`=`Y` were rendered and identified from live VRAM + palette. Name input is ASCII at `0x03004244` and is converted to glyph indices for display.
- Published console button codes: full 8-press sequences searched as u16 active-high, u16 active-low, per-press bytes, and reversed, at 2-byte alignment over all 16 MiB: **0** matches for all three codes. Only a 2-press prefix (`U,D`) had coincidental noise hits in compressed data.
- Generic button-mask table scan (runs of ≥4 consecutive u16 values ≤ `0x3FF`): **8,127** runs found, none equal to any published sequence — they are animation/pose/palette data (e.g. `0x80444C8`: `0x100,0x302,0x302,0x100,…`), not input validators.
- Only **two** literal pools contain `0x04000130` (`0x0801E9F8`, `0x08033BAC`); both belong to the generic input sampler/dispatcher. No comparator against a stored key sequence was found in either.
- Debug-combo keypresses at the main menu produced no new screen.
- Unlockables are save-bit gated (gallery 10/10 locked on a fresh save; extra bounce and minigames are story-completion rewards per publisher documentation), and are **not** controller-input codes.

**Bounds proven by rejection:** there is no numeric code format, so the usual "reject an out-of-range field / bad checksum" test is inapplicable. Rejection was instead demonstrated at the input layer: the three published console codes were entered on the real pause screen and produced no state change (accepted nowhere), and the name-entry field accepted arbitrary ASCII (`Q*Y`) with no validity message — the behaviour of a label, not a validator.

## 7. Validation evidence

- **Observed:** every screen listed in §6b via screenshots on mGBA `:316`; main-menu cursor byte changes at `0x03004200` correlated with the highlighted item; ASCII name bytes in savestate IWRAM; gallery 10/10 locked; no effect from any button code or debug combo; no effect from arbitrary name text.
- **Derived:** input sampler at `0x0801E9C4` reading KEYINPUT and computing held/pressed/released; name→glyph conversion to 3-tile 8×24 glyphs; save file layout (512-byte EEPROM, `TBOR` magic); absence of full code sequences and validators from exhaustive binary search.
- **Inferred:** the exact semantics of individual EEPROM bits for gallery/minigame unlocks were not isolated (no completed-game save was produced); the unlock conditions are taken from publisher/FAQ documentation and the all-locked fresh-save gallery.

## 8. Unknowns

- Which exact EEPROM bit(s) gate each of the 10 gallery entries and the two story bonuses; a completed-game save was not generated.
- Whether the `Big Weld's Mansion` combination-lock puzzle (4 pads × 4 settings = 256 combos) exists in the GBA build; the only documentation found is for the console versions.
- Whether the gallery scroll arrows reach more than the 10 visible tiles in some gated state; with a fresh save they wrap to the top row.
- The complete glyph→tile-index table for all 27 keyboard characters was not dumped (only the text-rendering mechanism and two glyphs were verified); no hidden text string was found by any other search.

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3 (`struct`, `zlib`, `Pillow`).
- `arm-none-eabi-objdump` (`-M force-thumb`) for Thumb disassembly.
- `mgba` SDL under `Xvfb :316` + `openbox`; `xdotool` key events; `scrot` + ImageMagick `convert`/`montage` screenshots.
- `gdb-multiarch` against mGBA's `-g` stub (note: the stub accepts one clean connection and wedges after detach — a fresh emulator start was needed per read session). Savestate `gbAs` zlib decompression was the reliable RAM/VRAM alternative (guide §16.13).
- Web sources: VGChartz (2 GBA entries are gameplay tips, not codes), GameFAQs/CheatCC/supercheats (button codes and unlockables are for PS2/GC/Xbox/DS), TCRF GBA page (prompt injection, ignored), chaptercheats/GameGear (identity confirmation).
- No ROM or copyrighted assets are redistributed by this report; only hashes, addresses, algorithms and observations.
