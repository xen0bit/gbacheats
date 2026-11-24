# Mucha Lucha! Mascaritas of the Lost Code (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mucha Lucha! Mascaritas of the Lost Code.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `MUCHA_LUCHA_` |
| Game code | `BMLE` (BMLE41) |
| Maker | `41` (Ubisoft licensee code) |
| Version | 0x00 (Rev.00, USA) |
| Entry word | `0xEA00002E` — stock GBA branch to `0x080000C0` |
| Header checksum / complement | stored `0x0000` / `0x33` (complement checks out: `-(sum(0xA0..0xBC)+0x19)&0xFF == 0x33`) |
| MD5 | `646242f1b5f0648cace7a0bafd16020f` |
| SHA-1 | `7055a58ff3cc9e6674a0c286cb8ca95d7ba3de45` |
| SHA-256 | `24aa95ef734d53dc757b98276674ac1212765497a46fcda9318aee4d26c501e6` |

Embedded-header scan (full 156-byte Nintendo-logo match over the whole image) found **exactly one** header, at file offset `0x0`. No multi-game shell, no appended trainer, no patched entry point, no scene cracktro. Saved game is 512-byte SRAM (`.sav`), first 0x20 bytes used, with `0F D0 7F FB`-style magic (`f0 0d` LE at `0x1C`).

## 2. Executive summary

This is a Digital Eclipse beat-'em-up with **no password/code-entry system and no reachable debug menu**. The complete set of in-game "cheat"/unlock content is:

1. **Six save-bit unlockables** (2 characters, 3 signature moves, 1 permanent meter reward), earned by story progress; their six English messages plus Spanish/French variants are a fixed pointer table at ROM `0x831C9DC..0x831CA30`.
2. **One published button code** — "10 Extra Lives" from GameFAQs (also mirrored on visualboyadvance.org): `Down, Select, Up, Down, L, R, Down, Up, R, L, Up, A`, claimed to be entered after pressing Start during gameplay. **This code did not reproduce** on this ROM: the literal sequence is absent in every encoding tried, and entering it on the pause screen, during gameplay, and on the title screen (with three timing profiles, verified keymap) left the lives counter unchanged at 3. It is reported as **unverified/rejected**, not as a working code.
3. **Mega attack** (`A+B` with full blue meter) and **second signature attack** (defeat first boss) are ordinary gameplay mechanics / save-bit unlocks, not codes.
4. GameShark/CodeBreaker master codes on GameHacking.org are memory-edit codes and are **out of scope** for this engagement.

No hidden character, hidden level, password screen, or debug screen was found on any reachable screen. The negative is bounded by: full screen enumeration (§3), ASCII + `strings` sweep (§3/§6), key-mask sequence scans in 9 encodings (§6), and a sweep of common hidden-menu button combos in-game (§6b).

## 3. How to reproduce

- Emulator: mGBA (SDL build at `/usr/local/bin/mgba`), `DISPLAY=:317` under Xvfb, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.
- Keymap (empirically verified by reading held-button RAM at `0x03001CA8`, savestate-derived):

  | GBA | xdotool | active-high bit |
  |---|---|---|
  | A | `x` | 0x001 |
  | B | `z` | 0x002 |
  | Select | `BackSpace` | 0x004 |
  | Start | `Return` | 0x008 |
  | Right / Left | `Right` / `Left` | 0x010 / 0x020 |
  | Up / Down | `Up` / `Down` | 0x040 / 0x080 |
  | R / L | `s` / `a` | 0x100 / 0x200 |

  (The held value has fixed high bits, e.g. Down reads `0xFC80`, L reads `0xFE00`.)

- Screen path (all reproduced with screenshots saved to `/tmp/muchalucha/`):
  1. Boot logo → language select (`ENGLISH` / `FRANCAIS` / `ESPANOL`), press A.
  2. "PRESS START" title → Start.
  3. Main menu, exactly four entries: `NEW GAME`, `LOAD GAME`, `OPTIONS`, `CREDITS` (Down wraps at CREDITS).
  4. `LOAD GAME`: `SELECT A SAVED GAME`, four slots, `EMPTY`.
  5. `OPTIONS`: only `MUSIC`, `SOUND` (Down does not advance past SOUND).
  6. `NEW GAME`: `SELECT A SAVE SLOT` (four slots) → `SAVING GAME / PLEASE DO NOT TURN THE POWER OFF!`
  7. `SELECT A MASCARITA`: `RIKOCHET` (colored/unlocked), `BUENA GIRL` and `THE FLEA` (gray silhouettes = locked).
  8. `SELECT A LEVEL`: `EPISODE 1, LEVEL 1`.
  9. Story dialogue → gameplay (HUD lives counter reads `3`).
  10. Start during gameplay → `PAUSE` screen with `TAG WRESTLER`, three health bars, `QUIT GAME`.

- Button-code tests performed (all failed to change anything):
  - Published sequence on pause screen, 90 ms hold / 90 ms gap.
  - Published sequence on pause screen, 55 ms hold / 180 ms gap.
  - Published sequence during active gameplay, 90 ms hold / 90 ms gap.
  - Published sequence on the title screen before pressing Start (twice, including after English selection).
  - Undocumented combos on title/pause/gameplay: `L+R`, `L+R+Start`, `A+B+Start+Select`, `L+R+A+B`, Konami code.

## 4. Address map

| Item | Address (ROM) | File offset | Evidence |
|---|---|---|---|
| Stock entry point | `0x08000000` (`0xEA00002E` → `0x080000C0`) | 0x0 | Observed header |
| Joypad read routine | `0x08310984` | 0x310984 | Derived (Thumb disasm) |
| Held buttons (active-high) | RAM `0x03001CA8` | — | Derived + observed (savestate) |
| Previous held | RAM `0x03001CAC` | — | Derived |
| Current held | RAM `0x03001CB0` | — | Derived |
| New presses / edge | RAM `0x03001CB4` | — | Derived |
| Unlock-message literal pool (20 pointers) | `0x831C9DC..0x831CA30` | 0x31C9DC.. | Observed (pointer scan) |
| Save/results message literal pool | `0x831C940..0x831C994` | 0x31C940.. | Observed |
| English unlock strings | `0x831D8A0`, `0x831D954`, `0x831DA08`, `0x831DACC`, `0x831DB8C`, `0x831DCBC` | 0x31D8A0.. | Observed |
| EWRAM byte responsive to Down input | RAM `0x0200F710` | — | Observed (savestate diff) |
| SRAM save | `0x0E000000` (cart), mirrored to .sav | — | Observed (.sav) |

Joypad routine (`0x08310984`), Thumb:

```
r1 = 0x03001CAC ; r2 = 0x03001CB0
[r1] = [r2]                 ; shift old current -> previous
r1 = ~KEYINPUT (0x04000130) ; active-high held
[r2] = r1                   ; current held
r4 = 0x03001CB4 ; r3 = 0x03001CA8
r0 = r1 & ~[r3]             ; edge-triggered new presses
[r4] = r0 ; [r3] = r1
```

## 5. Algorithm

There is no password/checksum algorithm in this title. The only input-driven logic found is the ordinary joypad edge/held machinery above and standard menu/gameplay handlers (e.g. `0x0830202C`, `0x08302448`, `0x08304188`, `0x083093BC`, `0x0831132C` all read the held/pressed words for movement, attacks and menu navigation — none contains a multi-button cheat sequence comparison).

The unlockable system is a save-bit flag model (§16.18 of the guide): a message dispatcher indexes a fixed literal table of localized "CONGRATULATIONS! … HAS BEEN UNLOCKED." strings. Bits are set by story events (boss defeats, all-A+ grades), not by any controller input.

## 6. Tables

### 6.1 Published codes (web, verified literally against ROM)

| Source | Claim | ROM verification |
|---|---|---|
| GameFAQs / visualboyadvance.org | 10 Extra Lives: after Start, `Down, Select, Up, Down, L, R, Down, Up, R, L, Up, A` | **Not found** as literal in any of 9 encodings; **rejected** in emulator (lives stayed 3) |
| GGmania / CheatingDome / VGChartz | The Flea unlock: defeat final boss | Consistent with ROM string table + locked silhouette at character select |
| GGmania | Buena Girl unlock: defeat second boss (wiki: Ep.3 L1) | Consistent with ROM string table + locked silhouette |
| CheatingDome / VGChartz | Mega attack: A+B with full blue meter | Gameplay mechanic, no code surface |
| CheatingDome | Second attack: defeat first boss | Save-bit unlock |
| GameHacking.org | GameShark/CodeBreaker codes | Out of scope (memory-edit), not examined |

### 6.2 Unlockable message table (6 messages × 3 languages, pointers at `0x831C9DC..0x831CA30`)

| Bit / reward | English string (ROM addr) | Trigger (published) |
|---|---|---|
| Character: The Flea | `0x831D8A0` | Defeat 4th/final boss |
| Character: Buena Girl | `0x831D954` | Defeat 2nd boss / Ep.3 L1 |
| Signature move: Stink Bomb | `0x831DA08` | Story event |
| Signature move: Torch of Truth | `0x831DACC` | Story event |
| Signature move: Mirror, Mirror | `0x831DB8C` | Story event |
| Reward: A+ on every level → permanent full Devastation Meter | `0x831DCBC` | Earn A+ on all levels |

Spanish and French variants occupy the interleaved pointers between each English entry (20 pointers total, including two `CREDITS`/`Developer` strings at `0x831CA24`/`0x831CA30`). At a fresh save the character-select screen shows **RIKOCHET** colored and the other two as silhouettes — observed evidence that these two bits start clear.

### 6.3 Word-like false positives

`Copy Editor` at `0x831D33E` is a **credits job title**, not a debug menu. `OFFICIAL CODE OF MASKED WRESTLING` (`0x831DF0C`, `0x831EDA8`, etc.) is story dialogue about a stolen book, not a password. The repeated mixed-case runs near `0x289170`–`0x289300` (e.g. `lMiNiLaKeYeXeYmXmLiKmKaLeXaYaXiYiKiLmJe`) are animation/tile data (interleaved with `0x05`, `0xD4`, `0x8F` control bytes), not a code alphabet.

## 6b. Enumeration

**Code-space size: zero passwords.** No entry alphabet, no length/checksum format, no validator, no password screen exists. Bounded by: all reachable screens walked (§3); `strings -t x -n 4` (36,466 lines) swept for `password|cheat|code|debug|secret|unlock|character|select|menu|hidden|level|edit|bonus|key|combo`, with every hit classified (§6.3); no on-screen symbol keyboard anywhere.

**Button-code space.** Only one published sequence exists. The expected mask sequence (active-high, verified keymap) is
`0x080, 0x004, 0x040, 0x080, 0x200, 0x100, 0x080, 0x040, 0x100, 0x200, 0x040, 0x001`.
Searched as: u16 LE, u16 BE, u8, u32 LE, active-low (`~mask & 0x3FF`), fixed-high-bit RAM form (`0xFC00|mask`), reversed order, 0-based and 1-based button-index encodings (4 orderings each), and all prefixes — **zero full-sequence matches** in the 4 MiB image. Prefix hits were random data (e.g. `0x55080`, `0x36BF3E`) in record/audio tables, not validators. The game's own joypad reader (`0x08310984`) stores only held/edge words; the xrefs to those words are gameplay/menu handlers, none of which contain a ≥3-button comparison chain.

**Undocumented combinations pressed in-game (novel inputs, all rejected):** `L+R`, `L+R+Start`, `A+B+Start+Select`, `L+R+A+B`, Konami code (`↑↑↓↓←→←→BA`). None opened a hidden screen or changed any HUD value — main menu/pause screen remained the documented four/two entries.

**Bounds proven by rejection:** the published code was rejected on three screens (pause, gameplay, title) at two hold timings; wrong first button (`Up`) leaves the one RAM byte that does respond to `Down` (`0x0200F710`) at 0, while `Down` sets it — so that byte is ordinary menu/input state, not a completing cheat counter (after the full sequence it reads `0x02`, lives unchanged at `0x03`). No out-of-range password test is possible because no password format exists.

**Unlockable set is closed at six** by the 20-pointer literal table: 6 rewards × 3 languages + 2 UI strings. Two are visibly locked at a fresh save; the other four are signature moves / meter reward with no on-screen selectable surface until earned.

## 7. Validation evidence

- **Observed:** all screenshots (title, main, load, options, character select, level select, gameplay, pause, post-code HUD); saved `.sav` (512 bytes); savestate RAM reads; empirically verified keymap via held-button RAM; lives counter before/after code (3 → 3).
- **Derived:** joypad routine and RAM addresses from Thumb disassembly at `0x08310984`; unlock-message pointer table from literal scan; absence of multi-button comparison chains from xref analysis of `0x03001CA8/0x03001CB4`.
- **Inferred:** precise save-bit positions and boss→bit mapping (the messages and locked silhouettes prove the bits' *existence*, but defeating each boss was not played through, so the exact bit indices and triggers remain inferred from the published guide).
- **Rejected/unverified:** the GameFAQs 10-extra-lives button code (evidence above).
- **Prompt-injection watch:** no fetched page contained instructions directed at the analyst; TCRF/wiki text was treated as data. GameHacking.org content was read only as a list of out-of-scope memory codes.

## 8. Unknowns

- Exact SRAM bit indices that store each unlock (no full game completion was performed; the six messages and locked character portraits prove the flags exist but not their byte/bit layout).
- Whether the published button code is a typo for a different revision/region, or belongs to another SKU. Its literal is absent from this BMLE41 image under every encoding tried.
- EWRAM `0x0200F710` is input-responsive but was not proven to be part of any cheat path; it is most likely pause-menu/input state.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for joypad/handler disassembly; Capstone 5.0.7 for literal/BL/xref scans.
- Python helpers in `/tmp/muchalucha/`: `phase0.py`, `btnsearch.py`, `btnsearch2.py`, `xref.py`, `xref2.py`, `xref3.py`, `dumpf.py`, `unlock_xref.py`, `ss.py` (mGBA `.ss1` `gbAs` zlib parser), `probe.py`, `probe2.py`, `keymap.py`, `ui.py`.
- mGBA savestate-diff RAM reading (guide §16.13) because the GDB stub port was contended by other sessions; no GDB stub was used against this ROM.
- Web sources: GameFAQs cheat page (403 on direct fetch; content obtained from search index), visualboyadvance.org, GGmania, CheatingDome, VGChartz, GameHacking.org, Mucha Lucha fandom wiki.

## 10. Legal note

No ROM images, graphics, music, or extracted game assets are redistributed. Only addresses, hashes, tool scripts and findings are published.
