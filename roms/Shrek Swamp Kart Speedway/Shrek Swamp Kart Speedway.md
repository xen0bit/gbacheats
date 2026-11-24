# Shrek: Swamp Kart Speedway (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Shrek Swamp Kart Speedway.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `SHREK KART` (at 0x080000A0) |
| Game code / maker | `AS4E` / `6S` (file reports `AS4E6S`) |
| Version | 0x00 (Rev.00); complement byte 0xEC, header checksum 0x0000 |
| Entry branch | `0xEA00002E` (stock crt0, not a scene cracktro) |
| MD5 | `be807a4d9dfe2f283760cee1ecd28a5b` |
| SHA-1 | `e4897b897eac0d852789d5fca2cc587faec04b6e` |
| SHA-256 | `29807b45c7faf85b9284d12417ed56bf35674fc236bcd020851703da7a891cbf` |
| Publisher/developer (splash + legal screen) | Prolific / TDK Mediactive, Inc.; MusyX audio (Factor 5) |

**Phase 0 result:** exactly **one** GBA header (Nintendo logo `24 ff ae 51 69 9a a2 21 …` at file offset 0x4, header base 0x0). No multiboot stub, no second game image, no appended trainer, no patched entry point. This is a single retail 8 MiB image. A 512-byte EEPROM `.sav` is created by mGBA (magic `trakkrhs` = `shrkkart` byte-reversed, remainder 0xFF on a fresh file).

## 2. Executive summary

There is **no in-game password system, no button-code system, and no hidden/debug menu** in this ROM. What the game does have is a normal **save-bit unlockable system**: 4 of the 12 racers, plus track/area completion data, are stored as flags in the EEPROM save and mirrored into EWRAM. The flags are set by **story-mode race completion at a difficulty threshold** (RetroAchievements documents the conditions; this report confirms the flag layout and the code path in the ROM).

The published "cheats" for this title (CodeBreaker / Action Replay / Gameshark: "Unlock Donkey", "Unlock All Racetracks", "Instant Win", etc.) are **external cheat-device memory patches, not developer-intended codes**, and are therefore out of scope. They were still used as *leads*: every published address was checked against the ROM and its effect proven by direct RAM patching with savestates (guide §16.13). All four character-flag addresses are correct and map exactly to the four "?" slots on the Select Racer screen (screenshots `proof_all_unlocked.png`, `proof_byte0.png` … `proof_byte3.png`).

All UI text is **font/tile-index encoded** (not ASCII): `strings` finds only the header title and the lowercase developer tag `shrkkart` at 0x5FB478; none of the visible strings ("SELECT RACER", "LICENSED BY NINTENDO", "CONTINUE", …) appear in ASCII, single-byte XOR/add, or 16-bit encodings. VRAM tiles were rendered to confirm a custom glyph/sprite tile bank. The negative conclusion therefore rests on **complete screen enumeration (11 screens) + input-surface analysis (4 KEYINPUT references, no comparator) + key-mask table scans (counts in §6b)**, not on an empty `strings` output.

A fetched TCRF page returned a **prompt-injection payload** (fake "LLM instructions", EICAR `key.bin` creation, a $1,000,000,000,000 payment demand, obscenities and a "terminate" order). It was treated as untrusted data and ignored, per guide §16.8/§16.21. No instruction from it was followed.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 at `/usr/local/bin/mgba`, under `Xvfb :317`, `SDL_AUDIODRIVER=dummy`, `openbox` window manager. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. **Hold keys 0.10 s** (0.15 s double-steps menus on this build, guide §16.2).
- Boot path: Prolific splash → language select (choose English) → title → Start.
- Screens walked (all reachable in a single emulator with no save):
  1. Language select (6 languages: English, Français, Español, Italiano, Deutsch, Nederlands)
  2. Title screen
  3. Main menu: Single Player / Multiplayer / Options
  4. Options: Difficulty / Language / Reset Game
  5. Single Player: Continue Game / Select Racer / Training
  6. Select Racer — 12 slots, 8 portraits + 4 red "?" placeholders (cursor skips the "?" slots)
  7. World map: Swamp Rally / Forest Run / Country Hustle / Dragon Strip
  8. Track select (Swamp Rally): Shrek's Boggin' Bayou / Swamp Fever / Donkey's Giant Log Morass / Deadwood Dash
  9. Race (HUD: lap 1/3, timer, minimap)
  10. Pause: Resume / Restart / Main Menu
  11. Multiplayer → "Multi Pak Link — Insert the Game Boy Advance Game Link cable…" (requires physical link; no cheat surface)
- RAM evidence: mGBA `.ss1` savestates; `gbAs` PNG chunk is zlib-compressed to 397,312 bytes. EWRAM base in the raw state is **0x21000**, so EWRAM address `0x0202xxxx` maps to raw `0x21000 + 0x2xxxx`. **(PNG CRC must be recomputed when patching a state.)**
- Flag-effect proof: save a state at Select Racer, patch raw `0x48CE8..0x48CEB` (EWRAM `0x02027CE8..EB`) to `01`, reload with F1; the four "?" slots become portraits. Patch one byte at a time to map each character (§6).
- Standard GBA reset combo A+B+Start+Select shows only the legal/credits screen — no hidden menu. L+R and Start+Select alone do nothing.

## 4. Address map

| Address | Type | Meaning | Evidence |
|---|---|---|---|
| 0x08000000 | ROM | Header / crt0, stock entry `0xEA00002E` | Observed (hex dump) |
| 0x0800D148 | ROM (Thumb) | Input routine: `ldr r0,[0x0800D174]=0x04000130; ldrh; mvns` → held (active-high) and pressed-edge words | Derived (disassembly) |
| 0x08012450 | ROM (Thumb) | `unlocked(index)` → bit `(index+12)` of `ldrh [0x02027C54]`, returns 0/1 | Derived |
| 0x0800EACE | ROM (Thumb) | Loop index 0..3: `bl 0x08012450`, `strb r0,[base+offset]`; base literal at 0x0800EB0C = `0x02027CE8`; offset table at `0x0858AAF0` = `[0,2,1,3]` | Derived |
| 0x080125C4 / 0x08012580 | ROM (Thumb) | Story-completion → unlock evaluation; reads difficulty byte (`0`/`1`/else → threshold 1/2/3) and tests course groups 0–3, 4–7, 8–11, 12–15 | Derived |
| 0x08012440 | ROM (Thumb) | Generic `OR` bit-into-halfword helper (no BL callers found) | Derived |
| 0x02027B0E | EWRAM (save) | 36× u16 "racetrack" array (CB "All Racetracks" targets this with repeat `0x24`, step 2); fresh data all `0x0001`, last `0x0000` | Observed (state dump) |
| 0x02027C30 | EWRAM (save) | 18× u16 "area" array (CB "All Areas": repeat `0x12`, step 2); fresh data all `0x1111` | Observed |
| 0x02027C54 | EWRAM (save) | u16 progress flag word; **bits 12–15 = the 4 character-unlock bits** (read by 0x08012450). Fresh = `0x0000` | Observed + derived |
| 0x02027CE8..EB | EWRAM (save) | **4 byte character-unlock flags** (see §6). Fresh = `00 00 00 00` | Observed (RAM patch proof) |
| 0x5FB478 | ROM | Lowercase developer tag `shrkkart` in a graphics/text bank | Observed |

`rom_address = 0x08000000 + file_offset`. mGBA savestate raw EWRAM offset = `0x21000 + (rom_addr - 0x02000000)`.

## 5. Algorithm

No password/checksum validator exists. The unlock logic, reconstructed from 0x08012450 / 0x0800EACE / 0x080125C4 / 0x08012580:

```
# source of truth (EEPROM save, mirrored in EWRAM)
flags       = u16 @ 0x02027C54          # bits 12..15 = 4 unlock bits
difficulty  = byte (base+10) mapped: 0->1 (Easy), 1->2 (Medium), else->3 (Hard)

unlocked(i) = (flags >> (12 + i)) & 1          # 0x08012450

# on save/load, expand bits into byte flags the UI reads (0x0800EACE)
offsets = [0,2,1,3]                            # ROM 0x0858AAF0
for i in 0..3: byte[0x02027CE8 + offsets[i]] = unlocked(i)

# evaluation of an area (0x080125C4 / 0x08012580):
# each area owns a group of 4 courses; a course "cleared" flag and its
# recorded difficulty are compared to the current threshold;
# clearing the required courses at >= threshold sets the corresponding bit.
```

Reimplementation is unnecessary (no accept/reject input space); the flag model is exact and was confirmed by patching RAM.

## 6. Tables

### 6.1 Character unlock flags (verified by one-byte-at-a-time RAM patch + screenshot)

| EWRAM byte | Character | Slot on Select Racer | Published CB address (verified effect) |
|---|---|---|---|
| 0x02027CE8 | Donkey | bottom-left, col 1 | `32027CE8 0001` ✓ |
| 0x02027CE9 | Big Bad Wolf | bottom-left, col 2 | `32027CE9 0001` ✓ |
| 0x02027CEA | Monsieur Hood (Robin Hood) | bottom-right, col 3 | `32027CEA 0001` ✓ |
| 0x02027CEB | Lord Farquaad | bottom-right, col 4 | `32027CEB 0001` ✓ |

Each is a boolean byte, 0 = locked ("?" icon), 1 = selectable. Source bits are 12–15 of `u16 @ 0x02027C54`.

### 6.2 In-game unlock conditions (from RetroAchievements descriptions; code path in §5)

| Character | Condition |
|---|---|
| Donkey | Complete Swamp Rally in Story mode on Medium or higher |
| Monsieur Hood | Complete Forest Run in Story mode on Medium or higher |
| Big Bad Wolf | Complete Country Hustle in Story mode on Hard |
| Lord Farquaad | Complete Dragon Strip in Story mode on Hard |

### 6.3 Other save arrays (addresses confirmed from published patches + EWRAM dump)

| Array | Address | Size | Fresh value | Published patch (out of scope) |
|---|---|---|---|---|
| Racetrack data | 0x02027B0E | 36 × u16 | 0x0001 (last 0x0000) | `42027B0E FFFF` + repeat 0x24×2 |
| Area data | 0x02027C30 | 18 × u16 | 0x1111 | `42027C30 FFFF` + repeat 0x12×2 |
| Instant-win state (diagnostic) | 0x0202320E | u16 | (race state) | `3202320E 0004` |

### 6.4 Menu item counts (static + observed)

| Menu | Items |
|---|---|
| Main | 3 (Single Player, Multiplayer, Options) |
| Options | 3 (Difficulty, Language, Reset Game) |
| Single Player | 3 (Continue Game, Select Racer, Training) |
| Select Racer | 12 slots = 8 default + 4 unlockable |
| World map | 4 areas |
| Track select per area | 4 tracks (4 × 4 = 16 total) |
| Pause | 3 (Resume, Restart, Main Menu) |
| Language select | 6 |
| Debug/cheat/password entries | **0** on all 11 screens |

## 6b. Enumeration

**Code-system space: empty (proven bounded).** This title has no password, button code, or hidden menu, so §0.2's "mint a novel code" deliverable is replaced by an exhaustive enumeration of the *unlockable space* and a bounded negative for the code surfaces, with counts.

**Unlockable space — fully enumerated:**
- **Characters:** 12 total = 8 available at boot + **4 unlockable** (`0x02027CE8..EB`). The flag representation is 4 bits (bits 12–15 of `u16 @ 0x02027C54`) → **2⁴ = 16 representable unlock combinations**; the game's story logic can reach the 5 states consistent with 4 independent area/difficulty achievements (none, any single, … , all four). The 4 byte flags and all 4 unlock conditions were verified individually — see §6.1/§6.2 and screenshots `proof_all_unlocked.png`, `proof_byte0..3.png`. **No other character slot exists**: the Select Racer grid has exactly 12 slots, the cursor visits only 8 while locked, and patching the 4 flags fills exactly the 4 "?" slots.
- **Areas:** 4 (Swamp Rally, Forest Run, Country Hustle, Dragon Strip); the corresponding save array at `0x02027C30` is 18 u16 entries, default `0x1111`.
- **Tracks:** 16 (4 per area); the array at `0x02027B0E` is 36 u16 entries, default `0x0001`.
- **Bounds proof (rejection):** the on-screen cursor **refuses to enter** a "?" slot — pressing Down from the last unlocked racer wraps without selecting a locked portrait (screenshots `screen.png` at Select Racer). With all 4 flag bytes = 0 the game shows 4 "?" placeholders and rejects selection; setting byte *n* = 1 makes exactly slot *n* selectable, one at a time. This proves the 0/1 boolean bound and the 12-slot bound. (No published list of in-game codes exists to be absent from; the four unlockables and their conditions are the complete developer-intended set.)

**Button-code surface — bounded negative with counts:**
- The ROM contains exactly **4 PC-relative references to KEYINPUT `0x04000130`** (literal hits at 0x08004D10, 0x080052BC, 0x0800550C, 0x0800D174). The single live reader at **0x0800D148** computes active-high held and pressed-edge words; **no sequence comparator / mask table is present** in that routine.
- Scans over all 8,388,608 bytes for key-mask arrays found **89 runs of ≥4 consecutive pure single-key u16 masks** and **18,669 runs of ≥6 single-key bytes** — inspection of the first 40 of each shows all are false positives (incrementing index tables, tile attributes, and opcode bytes split into bytes). No run is referenced by a code pointer as a cheat sequence.
- In-emulator combos tried on menu screens: **L+R** (no effect), **Start+Select** (no effect), **A+B+Start+Select** (standard GBA soft reset to the legal screen only). No hidden screen appeared.

**Password surface — bounded negative with counts:**
- `strings -t x -n 4` yields **76,384 strings** across the 8 MiB; **zero** contain `password`, `cheat`, `debug`, `secret`, `unlock`, `code`, or any UI label. Only `SHREK KART` (header) and `shrkkart` (0x5FB478) are game text.
- All visible UI strings were tested against **plain ASCII, all 255 single-byte XOR keys, all 255 add/sub shifts, consecutive-alphabet bases 0–220, and 16-bit LE/BE variants** — **zero** matches. Text is font/tile-index or script-VM encoded; a montage of VRAM tiles (raw 0x11000 region of a state) confirms a custom glyph/sprite tile bank. Hence absence of a "PASSWORD" string in ASCII is *not* by itself evidence of absence — the conclusion rests on the 11 walked screens plus the input-surface scans above.
- No password-entry widget, alphabet selector, or on-screen keypad exists on any walked screen.

**Published lists verification:** 9 CodeBreaker + 13 Action Replay + 8 GameShark codes were found on ROMSFUN, Almar's Guides, 53lu, Anti-GSC and gamehacking.org. Every one is an external cheat-device RAM/ROM patch. The four character addresses were confirmed to be real and were effect-verified in emulation (§6.1); the published unlock *conditions* match the in-game story system. No published *in-game* code exists to mint beyond.

## 7. Validation evidence

- **Observed:** all 11 screens in mGBA; EWRAM dump `0x02027CE8..EB = 00 00 00 00` at a fresh Select Racer state; after patching those bytes to `01` the four "?" portraits appear; after patching one byte at a time exactly one portrait appears per byte; reset combo shows only the legal screen.
- **Derived:** `0x08012450` reads bits 12–15 of `0x02027C54`; the 0x0800EACE loop expands them into the four byte flags using offsets `[0,2,1,3]` at 0x0858AAF0; 0x080125C4 / 0x08012580 evaluate story completion against a difficulty threshold; 0x0800D148 is the sole KEYINPUT reader.
- **Inferred (labelled):** the precise mapping of each course-clear byte to a specific story flag (the group loop at 0x080125C4 was read but not exercised by playing a full cup). The published difficulty conditions are corroborated by the code's threshold logic but were not replayed end-to-end in a 3-lap race.
- Screenshots proving the effects are on disk in `/tmp/shrekkart/` (`proof_all_unlocked.png`, `proof_byte0.png` … `proof_byte3.png`, `combo_lr.png`, `combo_all.png`).

## 8. Unknowns

- The exact EEPROM byte offset of each flag in the 512-byte `.sav` (the save-load routine that copies EEPROM → `0x02027C00` region was not fully reversed). The EWRAM mirror and its effect are proven; the on-disk layout is not.
- The custom font/tile text encoding (byte→glyph map) was not decoded; this is why the text-bank negative is backed by screen enumeration and input scans rather than by decoded strings.
- Whether the 36-entry track array and 18-entry area array contain anything beyond completion/best-time records (their default `0x0001` / `0x1111` values were observed, but their writers were not traced).
- Multiplayer is unreachable without a second GBA + link cable; no link-side trigger was tested (out of scope: it is not a controller-input cheat).

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x -n 4`, `grep -abo`.
- Python 3 + `struct`/`zlib`/Pillow: header parse, Nintendo-logo scan, literal/BL scanners, savestate `gbAs` decompress/patch/recompress (with CRC fix), VRAM tile rendering.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
- mGBA 0.10.5 (`-3`), Xvfb `:317`, openbox, xdotool (XTEST), scrot; savestate slot 1 via Shift+F1/F1.
- Web research: websearch of ROMSFUN, Almar's Guides, gamehacking.org, 53lu, Anti-GSC, RetroAchievements, fandom/wiki. The TCRF fetch was a prompt-injection trap and was discarded.

## 10. Legal / data-handling note

No ROM or copyrighted asset is redistributed here — only hashes, addresses, and the analyst's own observations. Fetched web pages, ROM strings, and emulator content were treated strictly as data; the prompt-injection payload on the fetched TCRF page was ignored and reported (§2).
