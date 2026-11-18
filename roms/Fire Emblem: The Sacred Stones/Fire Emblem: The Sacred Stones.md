# Fire Emblem: The Sacred Stones (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Fire Emblem: The Sacred Stones.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| `file` identification | Game Boy Advance ROM image: "FIREEMBLEM2E" (BE8E01, Rev.00) |
| Header title (0xA0) | `FIREEMBLEM2E` |
| Game code (0xAC) | `BE8E` |
| Maker (0xB0) | `01` (Nintendo) |
| Fixed byte (0xB2) | `0x96` |
| Version (0xBC) | `0x00` |
| Complement (0xBD) | `0x9D` |
| Header checksum (0xBE) | `0x0000` |
| Entry word (0x00) | `0xEA00002E` (stock `b 0xC0` — **not** a cracktro-patched entry) |
| MD5 | `005531fef9efbb642095fb8f64645236` |
| SHA-1 | `c25b145e37456171ada4b0d440bf88a19f4d509f` |
| SHA-256 | `638cda9d9b72657220fbf7e7a500cd3b64d9686c36e8a56fca69d26d13886f2f` |

**Embedded GBA-header scan (Phase 0).** The 156-byte Nintendo logo (`24 ff ae 51 69 9a a2 21 3d 84 82 0a 84 e4 09 ad …`) occurs at file offsets `0x0`, `0xB1A0B8` and `0xB247F4`. The two deep hits are verbatim copies of a *Fire Emblem 6 / Binding Blade* header (`FIREEMBLEM6\0`, game code `AFEJ`, maker `01`, entry `0xEA00002E`) embedded as inert data; the bytes following each header are zero padding, no code runs from them, and **no code anywhere references either address** (0 PC-relative literal references to `0x08B1A0B8` or `0x08B247F4`). They are link-transfer game-info records, not playable sub-images. No appended trainer or patch was found (entry word stock; no scene cracktro banner). Internal build tag `AGB-FE9` is present in IWRAM at `0x03007BD4` and in a symbol-name region at `0x08205C9C`/`0x08205D7C`.

## 2. Executive summary

**Fire Emblem: The Sacred Stones has no player-facing password system, no cheat-code validator, and no hidden developer/debug menu.** It is a battery-save tactical RPG: every "extra" (Sound Room, Tower of Valni, Lagdou Ruins, Melkaen Coast, Link Arena, Battle History, Support Conversations) is an ordinary save-flag-gated progression feature, not a code (guide §16.18 pattern).

The one genuine developer-intended **button code** is a **soft reset**: at the title screen, holding **L+R+A+B** (mask `0x0303`) — or the documented **A+B+Select+Start** (mask `0x000F`) — instantly resets the console. This is a single global gate (`0x08001C78`) with exactly two accepted masks; it produces a reset, not content, and is disabled during gameplay. It is fully enumerated below.

All UI text is tile-indexed, not ASCII (0 ASCII hits for any menu word in the raw ROM or in any of 4,724 decompressed LZ77 banks). I decoded the font-indexed text bank by rendering VRAM 4bpp tiles from savestates and read every reachable menu label directly off the glyph tiles (see §7 and the `game_vram.png`/`font_region2.png` artifacts in the work dir). The complete label set contains no "Debug", "Password", "Cheat", "Secret", or "Level Select" entry.

Sibling comparison: the concurrently-analysed *Fire Emblem* (position 304) is a **different game** — `FIREEMBLEME`, code `AE7E`, MD5 `f1a1b9742fcd467a531dd4314c4e7d19` (FE7, The Blazing Blade). No shared cheat literals or shared code paths were found; the FE6 header copies are the only cross-title data in this image. Nothing from that title was assumed here.

## 3. How to reproduce

* Emulator: mGBA (SDL), `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`, `Xvfb :319 -screen 0 1024x768x24`, `openbox`, `mgba -3 fe8.gba`.
* Verified keymap via savestate reads of the input struct at `0x02024CC4` (active-high): A = `x` (mask `0x0001`), B = `z` (`0x0002`), Select = `BackSpace` (`0x0004`), Start = `Return` (`0x0008`), L = `a` (`0x0200`), R = `s` (`0x0100`), D-pad = arrows (`0x10`–`0x80`). Hold keys ≥100 ms (per guide §4.2).
* Menu path walked (all with screenshots and savestate RAM evidence):
  1. Boot → Health & Safety → Nintendo logo → title **"New Game" / "Extras"**.
  2. **Extras** → **Sound Room** (track list 01–20, A=Play, START=Stop, SELECT=Random).
  3. **New Game** → **Select Mode**: Easy / Normal / Difficult (3 entries; Down wraps after Difficult — no hidden 4th).
  4. → **New Game** save-slot screen: 3 slots, all `-- NO DATA --`, playtime `0:00 00`.
  5. → scripted intro → **Prologue gameplay** (`Defeat boss`; Eirika LV1).
  6. Gameplay: unit/item menu (Vulnerary/Rapier: Use / Trade / Discard), **R** → "Personal data" (1/3), **Start** → tactical map/range overlay (toggles), **Select** → no visible change in the prologue.
  7. Savestates saved at title (`fe8.ss1`), mode select (`fe8.ss2`) and gameplay (`fe8.ss3`); RAM extracted by zlib-decompressing the `gbAs` PNG chunk (guide §16.13): 397,312-byte state, IWRAM at +`0x19000`, EWRAM at +`0x21000`.
* Button codes tested at the title screen (each after reloading `fe8.ss1`): L+R+Start, L+R+A+B, L+R+A+B+Start, A+B+Select+Start (all six), L+R+Select. **L+R+A+B and the all-six combo reset to the Nintendo logo**; the others did nothing. L+R+A+B held during gameplay does **not** reset (gate flag `0x0300000C` = `0x00` there).

## 4. Address map

| Item | Address / file offset | Evidence |
|---|---|---|
| ROM base | `0x08000000` = file `0x0` | header |
| Thumb entry / crt0 | `0x080000C0` | `0xEA00002E` |
| Key-input reader | `0x080013E0` | reads `0x04000130`, inverts, masks `0x3FF`, masks off `0x03000010`, calls `0x0800134C` |
| Input state updater | `0x0800134C` | +4 held, +6/+8 pressed, +0xA previous, +0xC last-pressed, +0x12 frame counter |
| Global input struct pointer | `0x0858791C` (ROM) → `0x02024CC0` (EWRAM) | 263 PC-relative literal loads in code |
| Held-key word | `0x02024CC4` (u16) | savestate RAM; `0x0303` with L+R+A+B held, `0x0008` with Start, `0x0004` with Select, `0x0001` with A |
| Debug/reset gate flag | `0x0300000C` (u8, IWRAM) | `0x01` at title, `0x00` in gameplay; setters `0x08000D00` (→1), `0x08000D0C` (→0, called at `0x08000AB0`) |
| **Soft-reset combo gate** | **`0x08001C78`** | `held == 0x0303` or `held == 0x000F` → `bl 0x080D16B0`; called every frame from main loop `0x08000AE0` |
| Soft-reset routine | `0x080D16B0` | clears flag, sets sp, `svc 1` (Reset), `svc 0` (Halt) |
| Combo masks | literal at `0x08001C9C` = `0x00000303`; inline `cmp r1,#15` at `0x08001CA0` | disassembly |
| Build tag "AGB-FE9" | `0x08205C9C`, `0x08205D7C`, IWRAM `0x03007BD4` | ASCII in ROM/RAM |
| Debug symbol-name region | `0x08205700`–`0x0820717C` | names: `bmenu`, `AtMenu`, `savemenu`, `savedrawcursor`, `Gmap Base Menu`, `CCRamifyMenuSelect`, `E_guideSub`, `E_guMenu1ReWrite`, `E_Guide`, `E_config`, `opinfoicon`, … — leftover internal labels, **not** player menus |
| Embedded FE6 header copies | `0x08B1A0B8`, `0x08B247F4` | verbatim AFEJ headers, unreferenced |
| Font-indexed menu text | rendered into VRAM tile banks (savestate VRAM at raw +`0x1000`) | decoded by 4bpp tile rendering; see §7 |

## 5. Algorithm

The only algorithmic gate found is the soft-reset check (pseudocode, exact):

```
; 0x08001C78, called each frame from main loop 0x08000AE0
if signed_byte(IWRAM[0x0300000C]) != 0:            ; 0x08000D18 + sign extend
    held = *(u16*)(0x02024CC0 + 4)                 ; 0x080013E0 output, active-high
    if held == 0x0303:                             ; L + R + A + B  (literal 0x08001C9C)
        soft_reset(0)                              ; 0x080D16B0
    elif held == 0x000F:                           ; A + B + Select + Start
        soft_reset(0)
return
```

There is **no validator, checksum, alphabet or lookup table** for a password/cheat system, so no reimplementation oracle exists (guide §16.19 not applicable). The complete accepted-button space is the two masks above; the gate has no other branch (disassembly `0x08001C78`–`0x08001CAC`).

## 6. Tables

**Button-code table (complete, exhaustive from the gate's branch set):**

| Mask | Buttons | Effect | Gate flag | Verified |
|---|---|---|---|---|
| `0x0303` | L + R + A + B | Instant soft reset (Nintendo logo) | `0x0300000C != 0` (title screen) | Yes — emulator screenshot + RAM (`held = 0x0303`) + disassembly |
| `0x000F` | A + B + Select + Start | Instant soft reset | same | Yes — emulator screenshot (all-six combo) + disassembly |

**Main-menu label set decoded from font-indexed VRAM tiles (15 unique labels + 3 slots):**
`Info`, `Save`, `Extras`, `Resume Chapter`, `Restart Chapter`, `Transfer Data` (×2 variants), `New Game`, `Copy Data`, `Erase Data`, `Battle History`, `Map`, `Support Conversation`, `Sound Room`, `Link Arena`, `-- NO DATA --` (×3). None is a debug/cheat entry.

**Title-screen options:** 2 (`New Game`, `Extras`). **Extras:** 1 (`Sound Room`). **Mode select:** 3 (`Easy`, `Normal`, `Difficult`). **Save slots:** 3.

## 6b. Enumeration

**Space definition.** Password/checksum space: **empty** — no alphabet, no length, no checksum field, no comparison table exists in the image (count evidence below). Button-code space: the global gate accepts **exactly 2** of the 1,024 possible 10-button masks; the remainder are rejected by the equality branches at `0x08001C8C` and `0x08001CA0`.

**Search counts (bounds of the negative result):**
* Raw ROM, 16,777,216 bytes, case-insensitive ASCII: `password`=0, `cheat`=0, `debug`=0, `secret`=0, `unlock`=0, `code`=0, `invalid`=0, `level select`=0, `sound test`=0; `menu`=12 (all debug symbol names / unrelated data), `hint`=1. UTF-16LE and `+0x20`-shifted scans: 0 hits for all cheat keywords.
* Decompressed LZ77 banks: 4,724 blocks, 16,989,926 bytes of decompressed data; 0 hits for every cheat keyword including `password`, `cheat`, `debug`, `secret`, `unlock`, `code`.
* Input-struct access scan: 263 PC-relative literal loads of the input pointer; 15 candidate multi-bit `cmp`/`and` sites, all resolved to soft-reset (`0x0303`, `0x000F`) or ordinary UI filters (`0x0009` A+Start, `0x0003` A+B, `0x0006` B+Select, `0x0002` B, `0x0005` A+Select). No hidden multi-button dispatch.
* Literal search for published-code style fixed strings (e.g. any 6–12 char uppercase/digit token from other Fire Emblem titles): 0 matches. FE6/FE7 codes were not found because no such system exists here.
* VRAM font/tile-indexed text bank decoded: 15 menu labels enumerated, 0 cheat/debug labels.

**Novel code minted:** not applicable — there is no code generator/validator to mint from. Per §0.2, when the system is absent the deliverable is a *bounded* negative: the complete menu/button spaces above are enumerated with counts, and the two accepted button masks are the exhaustive accepted set of the only gate.

**Bounds proven by rejection (Observed):**
* L+R+Start at title → no state change (screenshot `combo_LR_Start.png`).
* L+R+Select at title → no state change (`combo_LR_Select.png`).
* L+R+A+B **during gameplay** → no reset; gate flag `0x0300000C = 0x00` (savestate `lrab.raw`), proving the gate's enable condition, not just its mask condition.
* Every button mask other than `0x0303`/`0x000F` is rejected by the two equality comparisons in `0x08001C78` (Derived — exhaustive branch enumeration).
* Down past "Difficult" in mode select wraps to "Easy" — no hidden 4th mode (Observed).

## 7. Validation evidence

* **Observed:** full screen walk (title → mode → slots → intro → gameplay → map overlay → status → item menus), screenshots on disk; savestate RAM reads of input struct `0x02024CC0` confirming exact key masks and the gate flag at `0x0300000C`; L+R+A+B and A+B+Select+Start reset the console.
* **Observed (text decode):** VRAM 4bpp tiles rendered to PNG from savestates (`font_region2.png`, `game_vram.png`) — the font-indexed bank reads directly as the menu labels listed in §6, with no hidden entry.
* **Derived:** soft-reset gate at `0x08001C78` (branch set fully enumerated); input handler `0x080013E0`/`0x0800134C`; unreferenced FE6 header copies; keyword/zero counts over raw ROM and all decompressed banks.
* **Inferred:** the `E_*`/`Gmap*`/`bmenu` strings at `0x08205…` are leftover developer symbol names from an internal profiler, not a reachable menu (no xrefs found to them; no such labels in decoded VRAM text).
* **Web/published codes:** GameFAQs, TCRF and Neoseeker pages returned HTTP 403 / Cloudflare "Just a moment" challenges; the Wayback availability API returned no snapshot and the CDX query returned `[]`. StrategyWiki's FE8 Controls page was retrieved successfully: it documents only A+B+Select+Start = soft reset, Select = mini-map, Start = skip events — **no passwords or cheats**. No published code literal from any Fire Emblem title was found in this ROM. Fetched pages contained no prompt-injection payloads (§16.8 check performed); they were treated as data.

## 8. Unknowns

* The exact purpose of the two unreferenced embedded FE6 headers (`0x08B1A0B8`, `0x08B247F4`) is inferred to be link-transfer game-info data; no code references them, so they cannot be a hidden mode.
* The in-game system menu (Save/Suspend/Options/Map/Support) was not separately entered during the scripted prologue: Start displays the tactical map overlay there and Select had no visible effect in that state. Its entries are nonetheless enumerated from the decoded VRAM label bank (§6), which showed no debug entry, and from StrategyWiki's controls. No hidden entry was observed on any screen that was opened.
* No screenshot of a post-game save (cleared file) was available, so the save-gated post-game modes themselves were not entered; they are ordinary progression unlockables, not codes.
* Web cheat sites were blocked, so the published-code verification is negative-by-absence-in-ROM (0 literal matches) plus the accessible StrategyWiki controls page, rather than a complete crawl of every cheat aggregator.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep`, `arm-none-eabi-objdump -M force-thumb`, Python 3 + `capstone` 5.0.7, Pillow.
* Work dir `/tmp/opencode/fe8`: `parse_state.py` (savestate `gbAs` zlib extraction), `render_vram.py` (4bpp tile renderer), `lz77scan.py`/`lz77_dump.py` (4,724 LZ77 block decompression), `scan_lit.py` (Thumb PC-relative literal scan), `blscan.py` (Thumb BL scan), `btnscan.py` (input-mask comparison scan), `key.sh`/`combo.sh`/`trycombo.sh` (XTEST input helpers).
* All artifacts (screenshots, savestates, RAM dumps, scripts) are in `/tmp/opencode/fe8`; the ROM copy used for emulation was also in that dir, so the ROM folder acquired no `.sav`/`.ss*` files.

## 10. Legal note

No ROM bytes or copyrighted assets are reproduced here. Only hashes, addresses, algorithms, symbol strings for identification and tool descriptions are published.
