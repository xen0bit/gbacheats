# Elf Bowling 1 & 2 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Elf Bowling 1 & 2.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `ELFBOWL` |
| Game code | `BEBE` |
| Maker code | `7U` |
| Version | 0x00 |
| Fixed byte / main unit / device | 0x96 / 0x00 / 0x00 |
| Header checksum | 0x0000 (rebuilt-header artifact), complement 0xAC |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0` (no cracktro/trainer patch) |
| MD5 | `25cdcf14f0fce47d9c6c8155774948fa` |
| SHA-1 | `013f128c8d67f1165196b4f29297bcd4616c5033` |
| SHA-256 | `ea3954de1582c0f156ba48e12c05959b8fb1a2463cc4082fb3536fe395dec1c9` |

The MD5 matches the RetroAchievements set hash (`25cdcf14…`) for this exact SKU, confirming the revision.

**Embedded-header scan (§2 / §5.4b):** scanning all 0x400000 bytes for the 156-byte Nintendo logo found **exactly one** header, at file offset 0x0. Despite the "1 & 2" compilation title this is a single integrated image, not concatenated ROMs; both games are separate screens of one engine. No appended trainer or patch region was found.

## 2. Executive summary

**No in-game cheat system, password entry, code table, hidden character select, or reachable debug menu exists in this GBA image.** This is a *proven bounded negative* (§0.2 point 5), not "not tested":

* The only published *in-game* cheat for this title — a button code from Cheat Index, "hold L+R then press A A A B B B B A B for a big ball / perfect game, unlocking Santa Bowling" — was tested at all three plausible entry surfaces (title screen, game-select screen, and live gameplay) with frame-accurate XTEST input and savestate/RAM confirmation. It produces **no ball-size change, no unlock, and no debug screen**. A literal search of the whole ROM for the sequence under u8 button-index, u16 key-mask, active-high, active-low, L+R-held, and L/R-separate encodings returned **zero** hits. The published code is therefore unverified/rejected for this revision (it may belong to a different platform/version; the source is a low-quality cheat aggregator).
* The game's entire visible text is **font/tile-indexed**. `strings -n 4` returns only the header strings and garbage from ARM/Thumb code bytes; **no** English UI string exists in any tested encoding. Consequently a string-based cheat search cannot prove absence here — the negative rests on screen enumeration plus static analysis of the input subsystem.
* Static reverse engineering of the input path (`0x0801459C` joypad read → `0x08014BFC` per-frame update → accessors `0x08014C60/C84/CA4/CC0`) shows the game has **no button-sequence validator**: `CheckHistMask(0x08014C84)` is called from 31 sites and **every call passes mask `0x0A` (Start)** — ordinary menu navigation. No call compares history against A (`0x01`) or B (`0x02`) sequences, and no code table of a cheat sequence exists.
* The cart uses no save memory (`.sav` is 0 bytes); there is no save-bit unlock surface (contrast §16.18).
* Published *CodeBreaker* "strike on frame N" codes (`32004300 000A` …) are external memory-edit codes, **out of scope** by the engagement brief; they were located but are not in-game cheats and are reported only as out-of-scope findings.

## 3. How to reproduce

* Emulator: mGBA (SDL build), `-3` scale, headless on `Xvfb :317`, `SDL_AUDIODRIVER=dummy`. Because a sibling session repeatedly runs `pkill -x mgba`, the binary was copied to `./ebmgba` and launched under its own name so it survives; `setsid ./ebmgba -3 game.gba` with a working copy in `/tmp/opencode/elfbowling`.
* Keymap (verified against `KEYINPUT` at IWRAM `0x0300484C`): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows. Keys held 100–150 ms with equal gaps.
* RAM evidence: mGBA GDB stub was unreliable (§16.13); RAM was read instead by parsing the zlib `gbAs` chunk of `.ss1/.ss2` savestates (`Shift+F1/F2`). IWRAM begins at raw offset `0x19000`, EWRAM at `0x21000`; IWRAM `0x0300484C` maps to raw `0x1D84C` and holds raw active-low `KEYINPUT` (no keys = `0xFFFFFC00`, A = `…FC01`, L = `…FE00`).
* Menu path walked (all with RAM/screenshot evidence):
  1. Copyright screen → `Start` → Ignition splash → `Start` → NStorm splash → `Start` → **title "PRESS START"**.
  2. Title `Start` → **game select** (Elf Bowling 1 / Elves in Paradise – Elf Bowling 2).
  3. `A` → **1 PLAYER / 2 PLAYERS** select (Elf Bowling 2 branch shown).
  4. `A` → **Elf Bowling 1 gameplay** (bowling alley, 10 red pin-markers, moving aim indicator).
  5. `Start` → **PAUSED** sign (no menu entries; pressing A/B/D-pad produced no additional screen).
  6. Throw with `A` → **frame scorecard** (frames 1–10) → next frame.
  7. Elf Bowling 2 branch → **shuffleboard gameplay** (Santa vs Dingle, scoreboard) and its `Start` → **PAUSED** sign.
* Published code tests (all rejected):
  * Title "PRESS START" screen: hold `a`+`s` (L+R), press `x x x z z z z x z`, release, then `Start` → game starts normally, ball remains normal-sized.
  * Game-select screen: same sequence → normal navigation into gameplay, no change.
  * Live gameplay: same sequence then throw → ball renders at normal size (screenshots `gp_throw.png`, `final_throw.png`), no flag change attributable to the code, no unlock screen.
  * Combo sweeps `L+R+Select+Start` and `Select+A+B` on title/gameplay → no hidden screen.

## 4. Address map

| Region / item | Address | Evidence | Notes |
|---|---|---|---|
| Header / entry | `0x08000000` / `0x080000C0` | Observed | one header, stock crt0 |
| Joypad read (`ldrh` of `0x04000130`) | `0x0801459C` | Derived (objdump) | returns raw active-low `KEYINPUT` |
| Per-frame input update | `0x08014BFC` | Derived (Ghidra decompile) | `~KEYINPUT` → IWRAM `0x0300484C`, then builds history |
| Raw `KEYINPUT` (active-low) | IWRAM `0x0300484C` | Observed (savestate) | `0xFFFFFC00` idle; bit0 A … bit8 R, bit9 L |
| Player-key assignment array | IWRAM `0x0300597C` | Observed / Derived | `[0x0001,0x0002,0x0004,0x0008,0x0100,0x0200,…]` = A,B,Select,Start,R,L |
| Input history (per-player, 24-byte stride ×6) | IWRAM `0x03004794` | Derived | 8 halfword entries + current + counter |
| Translated key history (8 halfwords) | IWRAM `0x03004858` | Observed | values are internal key codes |
| Held / pressed words | IWRAM `0x03004850` / `0x03004854` | Observed | menu state |
| `GetHist16` | `0x08014C60` | Derived | `history[index]` |
| `CheckHistMask(idx,mask)` | `0x08014C84` | Derived (Ghidra) | `(history[idx] & mask) == mask`; 31 xrefs, all `mask=0x0A` |
| `CheckHeld(mask)` / `GetPressed()` | `0x08014CA4` / `0x08014C78` | Derived | menu input |
| Frame-score array (CB-codes target) | EWRAM `0x02004300 + 0x14*n`, n=0..9 | Observed (savestate `0xFFFFFFFF` unplayed) | used only by external CodeBreaker codes, out of scope |
| 8bpp font/tile graphics bank | ROM `0x0805CF00` onward | Observed (VRAM match) | 8bpp tiles, index `0x80` = transparent; full glyph→char map not completed |
| Input-helper literal pool | ROM `0x08014A54`-`0x08014E2C` | Derived | key-code constants `0x01,0x02,0x05,0x0A,0x15,0x22` at `0x08014AF8..0x08014B5C` |

## 5. Algorithm

There is no password validator to reimplement. The relevant *input* algorithm, recovered from the ROM and confirmed against RAM, is:

```
readKeys():                         # 0x0801459C
    return *(u16*)0x04000130        # raw active-low KEYINPUT

updateInput():                      # 0x08014BFC, called once per frame
    held_raw = readKeys()
    *(u32*)0x0300484C = ~held_raw   # active-high: A=1,B=2,Sel=4,Start=8,R=0x100,L=0x200
    for p in 0..5: buildHistory(p)  # 0x080149E4, 24-byte records at 0x03004794
    foldDpad()                      # 0x08014A64, d-pad at 0x03004824
    for p in 0..5: translate(p)     # 0x08014AC4 -> internal codes at 0x03004858
    updateMenuState()               # 0x08014B60

internal key codes (from literal pool 0x08014AF8..0x08014B5C):
    A=0x01  B=0x02  Select=0x05  Start=0x0A  R=0x15  L=0x22

CheckHistMask(idx, mask):           # 0x08014C84
    return (hist[idx] & mask) == mask
```

Every one of the 31 `CheckHistMask` call sites passes `mask=0x0A` (Start). There is no branch that consumes an A/B/L/R sequence, no checksum, no alphabet, and no lookup table of accepted codes. The published button-string has no representation in this engine.

## 6. Tables

* **Internal key codes:** A `0x01`, B `0x02`, Select `0x05`, Start `0x0A`, R `0x15`, L `0x22` (literals at `0x08014AF8`, `0x08014AFC`, `0x08014B5C`, `0x08014B3C`, `0x08014B58`, `0x08014B40`; observed as history values).
* **CheckHistMask call sites (31):** `0x08003580, 080043AC, 0800523E, 08005954, 080060F2, 08006A7C, 08006EE4, 0800E22E, 0800E254, 0800EDC0, 0800EE7A, 0800F38A, 0800F6EA, 0800F810, 08010010, 08010570, 080105A0, 08010FAA, 08011726, 08011FA6, 08012A1A, 08012A4A, 08012A56, 08012C46, 08012C68, 08012DAA, 08012DCC, 08012E6A, 08012E8C, 08012FB2, 08012FDC` — **all** `mask = 0x0A`.
* **Cheat code table:** none exists (empty space characterized in §6b).
* **No hidden characters / unlockable modes** were observed on either game's select screens.

## 6b. Enumeration

**Space definition and search bounds (negative result):**

1. **Button-code space.** The game tracks 6 buttons (A, B, Select, Start, R, L) in an 8-entry history. A code checker would necessarily call `CheckHistMask`/`CheckHeld`/`CheckPressed` with the target masks. Enumeration of **all 31** `CheckHistMask` xrefs and **all 5** `CheckHeld`/`GetPressed` xrefs shows the only masks used are `0x0A` (Start) and `0x0A`/menu constants — **zero** references to A (`0x01`), B (`0x02`), R (`0x15`), or L (`0x22`) as sequence elements. No cheat sequence table exists in the ROM under any of 8 encodings tested (button-index u8/u16, active-high/active-low masks, L+R combined `0x37`, L/R separate, byte-reversed): all zero hits. The button space is therefore *structurally empty* for a sequence cheat.
2. **Published-code test (bounds by rejection).** The one published in-game sequence was entered at three screens (title, game-select, gameplay) with exact key holds and verified against `KEYINPUT` and frame screenshots. It was **rejected** — no big ball, no unlock, no debug screen. This satisfies §0.2 point 4 in the negative direction: a candidate code was tested and failed.
3. **Novel code minting.** Not applicable — no code system exists to mint from. §0.2's "generate an unpublished accepted code" obligation is replaced by the §0.2 point-5 negative proof: the menu enumeration (11 screens listed in §3), the button-space count (31 validator call sites, zero cheat masks), the text-space count (0 ASCII UI strings; 11 known UI strings × 6 encodings = 66 literal searches, zero hits), and the rejected published code together bound the absence.
4. **Text/tile space.** `strings -t x -n 4` over 4 MiB produced 32,072 lines, of which exactly 2 are the header strings (`ELFBOWL`, `BEBE7U`); all others are code/data byte patterns, **no** English words. Literal searches (ASCII, `+0x20`, `-0x20`, UTF-16LE, UTF-16BE, reversed) for `1 PLAYER`, `2 PLAYERS`, `PAUSED`, `PRESS START`, `SANTA`, `PERFECT`, `STRIKE`, `OPTIONS`, `CONTINUE`, `ELF BOWLING` returned **zero** hits. An 8bpp tile/font bank was located at `0x0805CF00` (matched byte-for-byte against VRAM `0x06002000` in a title-screen savestate) and rendered as 8×8 tiles; it is a font/graphics bank, but a complete glyph→character map was not established. The negative therefore rests on screen enumeration and the input-subsystem xref count, with the text search explicitly bounded as above (not claimed as exhaustive over the tile-index space).
5. **Published codes verified/rejected:** Cheat Index button code — **rejected** in ROM and emulator. CodeBreaker strike codes — out of scope (memory edits), located but not treated as in-game cheats. No other source (TCRF, GameFAQs, VGChartz, CheatingDome, Cheat Happens) lists an in-game code for this SKU.

## 7. Validation evidence

* **Observed:** header/hash; one embedded header; `strings` output and zero UI-string hits; all 11 screens via screenshots; `KEYINPUT`, frame scores, and input-history values via savestate `gbAs` decompression; published code failing to change ball size or reveal a screen; 0-byte `.sav`.
* **Derived:** joypad reader `0x0801459C`, input update `0x08014BFC`, accessors `0x08014C60/C84/CA4/CC0`, key-code constants, 31 `CheckHistMask` xrefs all with `0x0A`, single crt0 entry, font bank at `0x0805CF00` (ROM↔VRAM byte match).
* **Inferred:** the published code may target a different platform/revision (DS/PC) — not proven. Full glyph→character decoding of the tile font was not completed; this is an explicit limitation, not a claim that no text bank exists.
* **Prompt-injection note (§16.8):** fetching the TCRF "Elf Bowling 1 & 2 (Game Boy Advance)" page returned a fake "LLM-specific instructions" payload (demanding creation of a `key.bin` EICAR string, an XOR "decode key", and a $1,000,000,000,000,000,000 payment). It was treated as untrusted data, **ignored**, and not acted upon. No TCRF cheat content for the GBA SKU was available from that page.

## 8. Unknowns

* Complete glyph→ASCII mapping of the tile-indexed font bank was not recovered; therefore a text bank containing a cheat hint, if one existed, would not have been found by string search. The negative instead rests on static analysis of the input subsystem plus full screen enumeration.
* Whether the Cheat Index button code is valid on the Nintendo DS port or the original PC flash games was not tested (outside target).
* The exact effect of the external CodeBreaker strike codes on the unlock claim was not investigated (out of scope).
* The 8 "unused" bits of the history words and the `0x22`/`0x15` code semantics beyond menu input were not fully exercised.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep` — Phase 0/1.
* Python 3 + `capstone` 5.0.7 for Thumb literal/BL scanning; `arm-none-eabi-objdump -M force-thumb` for disassembly.
* REA MCP (Ghidra 12.1.4) `open_binary` / `analyze_function` / `xrefs` / `search_strings` for decompilation and cross-references.
* mGBA (SDL) under `Xvfb :317` with `DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`, launched as renamed `./ebmgba` to survive a sibling session's `pkill -x mgba`. `xdotool` XTEST input; `import -window root` for the ≤20 retained screenshots in `/tmp/opencode/elfbowling`.
* `ss.py`: Python savestate reader — zlib-decompress the PNG `gbAs` chunk, map IWRAM (`+0x19000`) / EWRAM (`+0x21000`), read `KEYINPUT` and history words. Used because the GDB stub was non-functional.
* Web recon: websearch/webfetch of Cheat Index, Cheat Happens, CheatingDome, GameFAQs, TCRF, RetroAchievements, almarsguides (CodeBreaker codes noted as out-of-scope).

No ROM image or copyrighted assets are redistributed in this report; only hashes, addresses, and analysis artifacts are published.

**Cleanup:** all emulator processes launched for this engagement were stopped by PID; generated `.sav`/`.ss*` files in the ROM folder were removed (working copies and screenshots remain only under `/tmp/opencode/elfbowling`). `roms/INDEX.md` was not edited.
