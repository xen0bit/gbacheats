# The Lord of the Rings: The Return of the King (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity
- **File**: `The Lord of the Rings: The Return of the King.gba`
- **Size**: 16,777,216 bytes (0x01000000)
- **Header title**: `RETURN KING` (0xA0)
- **Game code**: `BLRE`, revision `69` (0xAC); **maker**: `69` (0xB0)
- **Version**: 0x00; **complement**: 0x94; **header checksum**: 0x0000 (normal rebuilt-header artifact per guide §16.1)
- **Entry word**: `0xEA00002E` → stock branch to 0x080000C0 (no scene cracktro)
- **MD5**: `53dcb149b4593fba9955f842889445b4`
- **SHA-1**: `ec3d126d37ea6e2ad7030d8a99cf87c6e46c03fd`
- **SHA-256**: `b5f556593c5fbe3531a4354b047f0bed364a124ceee43f278a48f4d26b0ffa9c`
- **Emulator**: mGBA 0.10.5, Xvfb :316, openbox, `SDL_AUDIODRIVER=dummy`, `-3` scale

## 2. Executive summary

**No in-game/developer-intended cheat code system exists in this ROM.** There is no password screen, no button-code sequence, no hidden debug menu, and no code-entry surface of any kind. All content unlocks are **gameplay/state-gated save bits**, not codes. Every "cheat code" published for this title is a **GameShark/CodeBreaker/Action Replay device code**, which is explicitly out of scope for this engagement.

Evidence types:
- **Observed**: walked every reachable screen in mGBA with screenshots; tested 13 documented button combos; savestate RAM snapshots before/after each.
- **Derived**: static scans over all 16 MiB found zero password alphabets, zero password strings, zero debug functions, and no convincing button-mask table; the unlock logic was located and reversed at 0x080197DC.
- **Inferred**: the 6 flag bits in the unlock word correspond to the 6 starting heroes completing the game (consistent with published unlock conditions), but this was not verified by playing through all 6 campaigns.

All UI text is stored as **font/tile indices**, not ASCII — `strings` cannot find any menu label (guide §11 pitfall). This was confirmed by decoding sample text banks at 0x0B67F80 etc. (2-byte-per-character records with low byte = ASCII-like tile index, high byte = 0x20 attribute).

A 3rd party cheat index-family wiki fetch returned a **prompt-injection payload** (fake "LLM instructions", EICAR test signature, payment demand). It was ignored and treated as untrusted data per guide §16.8.

## 3. How to reproduce
1. Boot the ROM in mGBA: `SDL_AUDIODRIVER=dummy mgba -3 game.gba` under `Xvfb :316`.
2. Default keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
3. Walk: language select → (A) → intro → title ("Press START") → (Start) → main menu with six entries: New Game, Load Game, Multiplayer, Options, GCN Link, Bonus Maps.
4. In-game: (Select) opens pause menu: Save Game, Options, Artifacts, Quit Game.
5. No screen anywhere accepts a password, code, or hidden sequence.
6. Button combos tested (all at title/main menu, savestate RAM diffed): Konami code, L+R+Start, L+R+Select, L+R+A+B, A+B+Start, Up/Down alternation, Left/Right alternation, Start×2, Select+Start, R+L, Down+Up, A+B+A+B, L+A+R+B — none opened a hidden screen or set an unlock flag.
7. Savestate technique (guide §16.13): `Shift+F1` writes `game.ss1`; the PNG's `gbAs` chunk is zlib-compressed; decompress yields a 397,312-byte state with IWRAM at raw offset 0x19000. Unlock flags read at raw 0x1E81C (= 0x0300581C).

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| 0x08000000 | ROM | Stock ARM entry branch (`0xEA00002E`) |
| 0x080197DC | Thumb fn | Unlock-flag updater (8-case jump table) |
| 0x0801983C | data | Jump table, 8 × u32 Thumb pointers (cases 0..7) |
| 0x08019860..B0 | code | Six case handlers setting flag bits 8..13 |
| 0x080198C8 | code | `0xFC << 6 = 0x3F00` mask for the 6 hero flags |
| 0x080198EA | code | `if (flags & 0x3F00) != 0 → set bit 0x8` |
| 0x080198F4 | code | `if (flags & 0x3F00) == 0x3F00 → set bit 0x2` |
| 0x0B67F80 | data | Sample 2-byte-per-char text bank (font/tile indices) |
| 0x0300581C | IWRAM | Save-derived global unlock/state word |
| 0x0300581F | IWRAM | Related flag word |
| 0x03005823 | IWRAM | Artifact/character flag byte |
| 0x03003D7C.. | IWRAM | Character stat block (cheat-device targets; out of scope) |

**Unlock jump table decoded** (from 0x0801983C, verified against bytes):

| Case | Handler | Bit set in flags word | Likely meaning |
|---:|---|---|---|
| 0 | 0x08019840 | (default) | none |
| 1 | 0x08019860 | 0x0100 (bit 8) | hero A completed |
| 2 | 0x08019870 | 0x0200 (bit 9) | hero B completed |
| 3 | 0x08019880 | 0x0800 (bit 11) | hero C completed |
| 4 | 0x08019890 | 0x1000 (bit 12) | hero D completed |
| 5 | 0x080198A0 | 0x0400 (bit 10) | hero E completed |
| 6 | 0x080198B0 | 0x2000 (bit 13) | hero F completed |
| 7 | 0x080198B0 | 0x2000 (bit 13) | same as 6 |

Derived conditions in the same function:
- `flags & 0x3F00` > 1 → set 0x4000 (e.g. Smeagol / extra bonus map)
- `flags & 0x3F00` != 0 → set 0x8 (e.g. Moria bonus map)
- `flags & 0x3F00` == 0x3F00 → set 0x2 (e.g. Fanghorn, all heroes)

These are **gameplay achievements**, not codes: there is no writer of these bits reachable from controller input.

## 5. Algorithm

No password validator exists. The only "algorithm" present is the unlock-bit derivation:

```
# at 0x080197DC, called when a hero completes the game
hero_index = save.hero_completion_index   # 0..7
if hero_index < 8:
    case hero_index of
        1: flags |= 0x0100
        2: flags |= 0x0200
        3: flags |= 0x0800
        4: flags |= 0x1000
        5: flags |= 0x0400
        6: flags |= 0x2000
if popcount(flags & 0x3F00) > 1: flags |= 0x4000
if flags & 0x3F00 != 0:          flags |= 0x0008
if flags & 0x3F00 == 0x3F00:     flags |= 0x0002
```

## 6. Tables

- **Unlock jump table**: 8 entries at 0x0801983C (full decode in §4).
- **Artifacts**: 8 silhouette slots on the pause-menu Artifacts screen; all blank on a fresh save.
- **Bonus Maps**: main-menu "Bonus Maps" leads to the Load Game slot screen (4 empty slots on a fresh save) — maps are gated by the flags above.
- **No code alphabets or code tables exist in the image.**

## 6b. Enumeration

This is a **bounded negative** result. The "code space" for in-game cheats is empty; the enumeration below proves the bound rather than merely reporting "not found".

**Space searched (counts):**
1. **Literal string/alphabet search**: all 16,777,216 bytes scanned for `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `ENTER CODE`, uppercase/lowercase alphabets `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `0123456789ABCDEF...`, UTF-16LE/BE, and `+0x20` shifted variants → **0 hits**.
2. **LZ77-compressed banks**: all offsets with a valid 0x10 header scanned/decompressed looking for the same keywords → **0 hits**.
3. **Button-mask tables**: all 8,388,608 u16-aligned offsets scanned for runs of ≥6 GBA key-mask values (A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200) → dozens of hits, **all in high-entropy graphics/audio data**; none in code regions with a validator xref.
4. **Ghidra auto-analysis** (REA, Ghidra 12.1.4, ARM:LE:32:v7, base 0x08000000): procedure-name search for `debug|password|cheat|secret|unlock|code|menu` → **0 functions**; string search for `password` → **0 strings**.
5. **xrefs to unlock flags**: 15 xrefs to 0x0300581C found; all in gameplay/state code (combat, hero-select, menu), none in a code-entry/validator path.
6. **Screen enumeration**: 11 distinct screens walked with screenshots (language select, intro, title, main menu, hero select, in-game HUD, pause menu, Options, Artifacts, Bonus Maps/Load Game, Credits). **None contains a text-entry field, keypad, or code prompt.**
7. **Button combos**: 13 documented/console-style sequences pressed at title/menu with savestate RAM diff → **0 hidden screens, 0 unlock flags set**. (Apparent flag changes after combo 4 were traced to accidentally starting New Game, not a cheat.)
8. **Published-code verification**: web recon of 3rd party cheat indexes → **every published "cheat" is a GameShark/CodeBreaker device code**; zero passwords, zero button codes, zero debug-menu instructions. No literal from any published list appears in the ROM (device codes are patch addresses, not in-game input).

**Conclusion**: the in-game cheat code space has **cardinality 0** — there is no alphabet, no length, no checksum, no validator, and no code table to enumerate. The unlockable space consists entirely of save-bit achievements (6 hero-completion bits → derived unlock flags), none reachable by controller input. No novel code can be minted because there is no code system to mint into; the negative is proven by the counts above and by the absence of any input surface across all reachable screens.

## 7. Validation evidence

- **Observed**: mGBA screenshots of all 11 screens; savestate RAM snapshots (`cb_base.ss1`, `cb_*.ss1`, `x*.ss1`, `y*.ss1`, `w*.ss1`); 13-combo test with flag diffs.
- **Derived**: unlock jump table at 0x0801983C decoded from raw bytes; conditions at 0x080198E4/0x080198F4 read from Thumb disassembly; 2-byte tile-index text encoding decoded from banks at 0x0B67F80.
- **Inferred**: bit→hero mapping (cases 1..6) and bit→unlock mapping (0x8/0x2/0x4000) are consistent with published achievement conditions but were not verified by 6 full playthroughs.
- **Untrusted**: 3rd party cheat index-family wiki returned a prompt-injection payload; ignored (guide §16.8).

## 8. Unknowns
- Exact mapping of each of the 6 flag bits to a specific hero (requires 6 playthroughs).
- Whether the GameCube-link unlocks (Sam, Ancient Artifacts) are implemented as the same save-bit mechanism or a separate link-transfer routine (no GCN hardware available).
- Precise effect of flag 0x4000 vs 0x8 vs 0x2 on which bonus map/character is gated (visual confirmation on an unlocked save not performed).

## 9. Tooling
- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings` (Phase 0)
- `arm-none-eabi-objdump -M force-thumb` (unlock routine disassembly)
- Python 3 scripts: `scan.py` (strings/alphabets/LZ77/button-mask scan), `state.py` (savestate `gbAs` zlib diff), `emu.py`/`walk*.py`/`combos*.py` (input & screenshots)
- REA MCP with Ghidra 12.1.4 (procedure search, xrefs, decompilation) — session closed
- `Xvfb :316`, `openbox`, `xdotool`, `scrot`, ImageMagick `convert`, mGBA 0.10.5
- Web recon via search integration (3rd party cheat indexes)

## 10. Legal note
No ROM image, extracted graphics, music, or game text is redistributed. Only hashes, addresses, algorithms, and original analysis scripts are published.

## 11. Cleanup
Emulator processes started by this analysis were stopped by PID; Xvfb :316 and openbox were stopped by PID. `.sav` and `.ss*` artifacts were removed from the ROM folder (working copies remain only in `/tmp/lotr rotk/`). No `pkill`/`pkill -f` was used.
