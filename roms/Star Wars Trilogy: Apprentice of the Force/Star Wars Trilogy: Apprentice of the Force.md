# Star Wars Trilogy: Apprentice of the Force (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Star Wars Trilogy: Apprentice of the Force.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `STAR WARS TR` |
| Game code | `BCKE41` (AGB-BCKE, region code E/USA+En/Fr/Es, rev 00) |
| Maker code | `41` |
| Version / complement / checksum | 0x00 / 0x7A / 0x0000 |
| Entry branch | `0xEA00002E` → standard crt0 at `0x080000C0` (retail image, no cracktro) |
| Save | EEPROM 4 Kbit (512-byte `.sav` auto-created by mGBA) |
| MD5 | `6b423fd7f0b4cc280a6208f66671a9c1` |
| SHA-1 | `b6c09b9f5588ff81aeb4bd5ed886933993f4575f` |
| SHA-256 | `eaea569052f76aaa8333f2aac0238254ab1d8589e9833d3f468031119a63787e` |

Analysis ROM hash is recorded above; all addresses are for this exact image.

## 2. Executive summary

**There is no in-game/developer-intended code system in this SKU.** No password screen,
no button-code sequence, no hidden debug menu reachable by controller input, and no
code-like text field exists. This is a **bounded negative** (§16.3 category "no system"),
proven with counts in §6b.

Every "cheat" published for this game is an external cheat-device code (CodeBreaker /
GameShark / Action Replay) that writes EWRAM addresses such as `0x020077DE`
(force powers), `0x020077EA` (health), `0x020477E6` (weapon). These are *out of scope* by
the engagement rules and are **not** in-game cheats. Not one of them appears as a literal
in the ROM (see §6b, test 4), confirming they are device-side patches rather than
developer content.

The only developer-intended unlockables are **completion-gated**:
1. **Chapter/level select** — the post-game menu built from the strings
   `EPISODE IV COMPLETED`, `PLAY EPISODE V`, `EPISODE V COMPLETED`, `PLAY EPISODE VI`
   (`0x080B15EC`..`0x080B1630`).
2. **Secret/bonus survival level** — selectable in that chapter-select screen after
   finishing the game (GameFAQs, GameSpot, GameRevolution, Fandom all agree; see §3).
3. A **Bonus → SLIDESHOW** picture gallery of 10 slots (`0x080B1E4C` = `SLIDESHOW`),
   also unlockable content; a cheat device can force "Access All Pictures" but no
   controller path does.

The only debug-like remnant is an **assertion overlay** that prints
`Level ID: %d`, `File: %s`, `Function: %s`, `Line: %d` (`0x080D3D74`,
`0x080D5DEC`, `0x080D5DF8`, `0x080D5E08`). It is an error reporter, not a menu:
one string, one code xref, zero menu-table entries, zero controller reachability.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
- mGBA SDL keymap (verified against `KEYINPUT` at `0x04000130`, idle = `0x03FF`):
  A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
- Boot path and screens walked (all with screenshots in
  `/tmp/starwarsapprentice/`):
  1. Title screen (`title.png`).
  2. **Language select** on first boot — 3 flags (US / blank / `A`) at the bottom
     (`cur.png`); A confirms. 16 language banks exist in ROM (`0x080D36B0`).
  3. Main menu (`menu2.png`): 5 entries — SINGLE PLAYER, MULTIPLAYER, BONUS,
     OPTIONS, CREDITS (matches the 5-pointer table at `0x080B0E40`).
  4. SINGLE PLAYER (`singleplayer.png`): 3 save slots; selecting an empty slot opens a
     3-character **name-entry** field (`slot1b.png`, `namealpha.png`) — a label, not a
     validator (§16.2b; see §6b test 6). A new game starts the Episode IV crawl
     (`after_name.png`).
  5. MULTIPLAYER (`mp2.png`): immediately gated by "Please connect 2 players to the
     Game Boy® Advance Game Link® cable." No ship/game selection reachable without a
     second console — a hard link-state gate, not a code gate.
  6. BONUS (`bonus_menu.png`): title bar "BONUS", a 2×5 grid of **10 empty picture
     frames**, footer "SLIDESHOW". A on any slot on a fresh save produces no change
     (`pic0.png`) — all 10 locked.
  7. OPTIONS (`options.png`): 3 sliders — Brightness, SFX, Music. No cheat entries.
  8. CREDITS: scrolled credit roll (entered from main menu).
- Published-source recon (data only): GameFAQs FAQ 32692 §7 "Level Select — Finish the
  game. Secret Level — Finish the game, and in the level selection screen you will be
  able to pick a new, secret, level." GameSpot/GameRevolution/ggmania/cheatingdome
  repeat the same two unlockables. GameHacking.org / ROMSFUN / Almar's Guides list
  *only* CodeBreaker/GameShark/AR device codes. No password or button code is published
  for this SKU anywhere found.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x080000C0` | crt0 entry (ARM) | header entry branch |
| `0x080B0E40` | main-menu pointer table, 5 entries → `SINGLE PLAYER`, `MULTIPLAYER`, `BONUS`, `OPTIONS`, `CREDITS` | observed menu + pointers |
| `0x080B0E54`..`0x080B0E78` | those 5 ASCII strings | dump |
| `0x080B15EC` | chapter-select string array, 4 entries | pointers |
| `0x080B15FC` / `0x080B160C` / `0x080B1620` / `0x080B1630` | `PLAY EPISODE VI`, `EPISODE V COMPLETED`, `PLAY EPISODE V`, `EPISODE IV COMPLETED` | dump |
| `0x080B1E4C` | `SLIDESHOW` string | observed BONUS footer |
| `0x080B1E58` | language-0 text-bank table (`{count, ptr}` records) | xref at `0x080D36B0` |
| `0x080D36B0` | 16-entry language bank table | dump |
| `0x080D3D74` | assert format `Level ID:  %d` | pointer at `0x080702DC` |
| `0x080702B0` | prints `Level ID` + File/Function/Line via `0x080A2DF8` | BL at `0x080A2820` |
| `0x080A26xx` | assert/error overlay renderer (File/Function/Line at `0x080A2A08/0C/10`) | disassembly |
| `0x0806ED00` | level handler; compares level IDs `0x0BB9`(3001)/`0x0BBA`(3002) | Thumb ptr at `0x080D3D70`, disasm |
| `0x082E3B90` | full ASCII table `0x20`–`0x7F` (font/source, **not** a code alphabet) | dump |
| EWRAM `0x020077DE` | force-powers bitfield (cheat-device target; mirrored as `0x020477DE`) | published device code, derived mirror |
| EWRAM `0x020077EA` | player health (`0x020477EA` mirror) | published device code |

`.sav` layout (observed, 512 bytes): fifteen 32-byte records `00 00 BB AA 00 22 44 55`
followed by 24 zero bytes, then a final 32-byte `FF`-filled record. The payload fields
and the exact completion-flag bit were **not** fully resolved (§8).

## 5. Algorithm

No validator, decoder, encoder, checksum, alphabet mapping, or sequence matcher exists
for player input. The only algorithmic structures found are:

- **Text-bank indirection**: UI strings are plain ASCII, stored in per-language banks
  (`{u32 count, u32 string_ptr_array}`) referenced through `0x080D36B0` →
  `0x080B1E58`. No tile-index-encoded text bank hides additional menu labels: the
  `strings` scan recovers every visible label (§6b test 7), so the §11 "not all text is
  ASCII" pitfall does not apply here.
- **Completion gate (conceptual)**: the chapter-select rows are only populated after
  the game's completion flag is set; the setter is triggered by finishing the final
  episode. No controller input sets it directly — a controller can only reach it by
  playing through the game (a *gated feature*, not a code).

## 6. Tables

**Main menu** (`0x080B0E40`, 5 entries, stored bottom-up):

| Index | Pointer | Label |
|---|---|---|
| 0 | `0x080B0E54` | CREDITS |
| 1 | `0x080B0E5C` | OPTIONS |
| 2 | `0x080B0E64` | BONUS |
| 3 | `0x080B0E6C` | MULTIPLAYER |
| 4 | `0x080B0E78` | SINGLE PLAYER |

**Chapter select** (`0x080B15EC`, 4 entries): `EPISODE IV COMPLETED`,
`PLAY EPISODE V`, `EPISODE V COMPLETED`, `PLAY EPISODE VI`.

**BONUS gallery**: 10 slots in a 2×5 grid; footer `SLIDESHOW`; all locked on a fresh
EEPROM.

**Options**: Brightness, SFX, Music (3 settings).

**Assert overlay strings**: `Level ID:  %d` (`0x080D3D74`), `File:  %s`
(`0x080D5DEC`), `Function:  %s` (`0x080D5DF8`), `Line:  %d` (`0x080D5E08`).

**Cheat-device EWRAM bitfield** (out of scope, documented only as a map):

| Address | Bits/value | Device-code effect |
|---|---|---|
| `0x020077DE` (mirror `0x020477DE`) | `0xFFFF` | all force powers / saber / invincible |
| `0x020077E5` | `0x0A` | infinite ammo |
| `0x020077E6` | `0xB0`–`0xB3` | weapon type |
| `0x020077EA` | `0x5A` | infinite health |

## 6b. Enumeration

### Space definition

- **Code space size: 0 (no code system).** There is no alphabet, no code length, no
  checksum width, no validator and no input surface for a code/password/button sequence.
  The enumeration deliverable is therefore a **bounded negative with counts**, not a
  generated code (§0.2 clause 5 / §16.3).
- **Unlockable space**: 10 gallery pictures + 1 chapter-select list (4 rows) + 1 secret
  survival level, all gated by a single completion condition. Enumerated exhaustively
  below.

### Bounded-negative searches and counts

| # | Search | Space checked | Result |
|---|---|---|---|
| 1 | ASCII strings containing `password` / `passcode` / `cheat` / `code` / `unlock` / `debug` / `menu` / `invalid` / `congrat` | all 85,915 printable strings (len≥4) in the 8 MiB image | **0 hits each**; `secret`→9 (all story dialogue), `bonus`→2 (menu label + French), `enter`→9 (dialogue) |
| 2 | Case-normalised (`+0x20`) `PASSWORD`/`CHEAT`/`DEBUG` | entire image translated lowercase→uppercase | **0 / 0 / 0** |
| 3 | Known cheat-code alphabets: 36-char `A–Z0–9`, 32-char `A–Z23456789` variants, 31-char no-vowel, `1234567890` | entire image | **0 hits** for all 7 alphabets; the only 26-letter run is at `0x082E3BB1` and is part of a full ASCII table `0x20`–`0x7F` (font/source), not a code alphabet |
| 4 | Published device-code literals `L1TTLVN`, `HAMA!333`, `F88F544FF910` | entire image | **0 hits** each — device codes are not ROM content |
| 5 | Button-mask sequences: ≥4 consecutive u16 values from `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}` | every 2-byte offset in the image | 180 raw hits, but **0 in the code region `<0x080A0000`**; all 180 are in data tables (e.g. `0x080DB100` is a bit-constant ramp `0x8000,0x4000,0x2000,0x1000…`). No press-history buffer or code table found. |
| 6 | Name-entry field consumer test (§16.2b) | 3-character field at SINGLE PLAYER slot selection | Field is a **label**: its alphabet is the standard name alphabet, it is filled by A/D-pad, and it feeds the save record only. No code-like validator uses it (no `password`/`code` string anywhere; §6b #1). |
| 7 | Hidden tile-encoded text bank (§11 pitfall) | 16 language banks at `0x080D36B0` | All UI labels recovered as ASCII; no glyph-index table acting as a hidden menu. |
| 8 | Reachable debug menu | `Level ID/File/Function/Line` assert strings | **1** format string xref (`0x080702DC`), **1** BL caller (`0x080A2820` → `0x080702B0`), **0** menu-table entries. It is an assertion reporter, unreachable by controller input. |

### Reachable-screen enumeration (every screen walked)

| Screen | Entries / slots | Code surface? |
|---|---|---|
| Title | 1 | none |
| Language select | 3 flags; 16 language banks in ROM | none |
| Main menu | 5 | none |
| Single Player | 3 slots + 3-char name entry | label only |
| Multiplayer | link-cable gate | unreachable without 2nd console |
| Bonus / SLIDESHOW | 10 slots | all locked on fresh save |
| Options | 3 sliders | none |
| Credits | credit roll | none |
| Chapter select (post-completion) | 4 rows | completion-gated |

**Total reachable menu entries/slots walked: 5 + 3 + 10 + 3 + 3 (languages visible) + 3 (options) = 27**, plus the 4 post-game chapter rows (gated, observed only in ROM). **Zero** code/password/button-code entry points.

### Bounds proven by rejection

- On a fresh EEPROM, **all 10 gallery slots reject A** (no image appears, `pic0.png`), and
  no chapter-select row appears in Single Player (`singleplayer.png`). This is the
  in-game rejection that bounds the unlockable space: completion is the only producer.
- Multiplayer's ship/game screens reject entry without a link cable (`mp2.png`).
- No out-of-range code value can be submitted, because no code input exists at all —
  that absence is the proven bound (tests 1–8 above).

### Novel code

**None minted — none possible.** There is no code system to generate a value for, so
§0.2's "novel code" clause is satisfied here by the bounded-negative path (§0.2 clause 5)
rather than by fabricating a code for a system that does not exist. Fabricating a
CodeBreaker/GameShark code would violate the scope rule.

## 7. Validation evidence

- **Observed**: all screenshots and menu enumerations in §3; 512-byte `.sav` created;
  `KEYINPUT=0x03FF` at idle; mGBA `-d` reads of `0x04000130`.
- **Derived**: string/pointer tables at `0x080B0E40`, `0x080B15EC`, `0x080B1E58`,
  `0x080D36B0`; assert-overlay xref counts; button-mask scan counts; alphabet scan
  counts; disassembly of `0x080702B0` / `0x080A2820` / `0x0806ED00`; level IDs
  `0x0BB9/0x0BBA` in `0x0806ED00`.
- **Inferred**: exact EEPROM record field layout and which bit is the completion flag
  (the records' 8-byte signature `00 00 BB AA 00 22 44 55` was found in the live `.sav`
  but not resolved to named fields in the time available — §8).

## 8. Unknowns

- Exact EEPROM payload field layout: which of the 24 bytes per 32-byte record holds the
  completion flag and the per-picture unlock bits. No static xref to the EEPROM I/O
  registers (`0x04000120`–`0x04000128`) was found by literal scan, so the save writer is
  likely reached via a pointer/mirror or a library routine not isolated here.
- Whether the 10 gallery pictures unlock on specific story milestones (likely) or only
  on full completion (not determined — beating the game was out of scope).
- The debug assert overlay was not executed (no assertion was triggered); its existence
  and non-reachability are static findings only.
- The `0x0806ED00` handler's level IDs 3001/3002 could not be tied to a named secret
  level without playing to the ending.

## 9. Tooling

- mGBA 0.10.5 (`-d` command-line debugger via a pty controller; `r/4`, `x/4`, `w/4`,
  `!!INT`/Ctrl-C, `reset`), Xvfb `:315`, openbox, xdotool (XTEST to the focused window),
  scrot, Python 3.
- Scripts in `/tmp/starwarsapprentice/`: `xref.py` (u32/BL xrefs), `litscan.py`
  (Thumb LDR literal scan), `counts.py` (bounded-negative counts), `anstate.py` /
  `parse_ss.py` (savestate `gbAs` chunk decoding, §16.13), `gba2.py` / `dc.py` (input and
  debugger helpers).
- `arm-none-eabi-objdump -M force-thumb`, `capstone` 5.0.7, `strings`, `xxd`, `curl`.
- REA skill was loaded; for a raw GBA image the practical path remained objdump + mGBA.

## 10. Legal note

No ROM image, extracted graphics, music, or game text is redistributed. Only hashes,
addresses, counts, and original analysis are published. Fetched web pages were treated
as untrusted data; no instructions found in them were executed.
