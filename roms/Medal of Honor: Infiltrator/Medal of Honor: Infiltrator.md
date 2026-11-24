# Medal of Honor: Infiltrator (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Medal of Honor: Infiltrator.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `INFILTRATOR` |
| Game code | `BMHE` (US) |
| Maker code | `69` (Electronic Arts) |
| Software version | `0x00` |
| Header complement / checksum | `0x78` / `0x0000` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, not a cracktro) |
| Nintendo-logo scan | exactly **one** GBA header at file `0x0`; no embedded/second image |
| MD5 | `78db66a92f5f4405266e154de49eea8d` |
| SHA-1 | `47761911475e9548c81fed78e3d3336ddae89a58` |
| SHA-256 | `cb2afd12e286890fcffee82a0b394e1101fa2983e2b6c0cf7ab05b46622024eb` |

No trainer, cracktro, appended image or patch was found (§16.1). The ROM is a single
clean retail image. File offset ↔ ROM address: `ROM = 0x08000000 + file_offset`.

## 2. Executive summary

**There is a shipped, developer-intended in-game CHEATS menu in this ROM.** Its
strings are plain NUL-terminated ASCII (not font/tile-indexed) in the English text
bank and are duplicated in the German bank, so it is a real shipping feature and
not an accidental debug leftover. The menu consists of a header `CHEATS`, a
`RESUME` row, and **nine** toggle entries: Invulnerability, Full Unlocks,
Level Skip, Add Lives, Limitless Ammo, Increased Fire Rate, No Reloads,
Slower Germans, One Hit Kills. "Full Unlocks" is itself a cheat that is expected
to unlock the two gated Extras entries (Survival Mode, Max-GI mode) and the
"Omaha level unlocked"/"Maximum GI unlocked." messages present in the bank.

**There is no password system and no button-code system in this image.** The
searched spaces are made explicit in §6b: zero password alphabets, zero password
entry screens among the 15 walked screens, zero direct string references to the
cheat menu, and no plausible key-mask sequence table. The only reachable cheat
surface is the menu; its activation gate was not reproduced in normal play (see
§8 for the exact bounds of that negative).

Web verification (§3.4) could not be completed: the `websearch` integration
returned no results for nine queries and direct fetches of 3rd party cheat indexes, Google and
Bing were blocked (403 / Cloudflare "Just a moment..." / bot challenge). The
Wayback CDX API returned empty sets for `*infiltrator*` 3rd party cheat indexes URLs. No
published code string was found literally in the ROM. Fetched pages were treated
as data only; no instruction found in fetched content was acted upon.

## 3. How to reproduce

- Emulator: `mgba -3` (SDL build), display `:318`, `SDL_AUDIODRIVER=dummy`,
  `Xvfb :318 -screen 0 1280x1024x24`, `openbox` window manager.
- Keymap (verified on-screen): GBA **A = `x`**, **B = `z`**, **L = `a`**,
  **R = `s`**, **Start = `Return`**, **Select = `BackSpace`**, D-pad = arrow keys.
  Hold 60–150 ms; the game debounces and an attract timer returns to the title
  after ~60 s idle, so each screen was captured immediately after navigation.
- Savestates: `Shift+F1..F8` save, `F1..F8` load; `-t <state>` boots into a state.
- mGBA `.ss1` states are PNG with a zlib `gbAs` chunk; decompressing gives a
  `0x61000`-byte raw state. Layout verified: CPU/header `0x0`, VRAM `0x1000`,
  IWRAM `0x19000`, **EWRAM `0x21000` = GBA `0x02000000`**, so EWRAM address
  `A` maps to raw offset `0x21000 + (A - 0x02000000)`.
- Exact menu path walked:
  `Language select → (A) → Title "Press START" → (Start) → Main Menu`
  `→ Campaign → Campaign Data → The Beachhead → briefing (2 pages) → gameplay`
  `→ (Start) → Pause → Objectives`;
  `Main Menu → Options`; `→ Extras → Credits / Nintendo GameCube Link`;
  `→ Multi-player → Searching for Game Boy Advance`; `→ Quick Start → briefing`.
- Input spaces tested with the emulator (all with RAM/screenshot evidence):
  single keys and combos `{Start, Select, L, R, A, B, L+R, A+B, L+R+Start,
  L+R+A, L+R+B, L+R+A+B, Select+Start, Select+A, L+Start, R+Start,
  Up, Up+Up+Down+Down, Konami Up*2 Down*2 Left Right Left Right B A}` on the
  title/Main Menu, on the gameplay screen, and on the pause menu, plus a
  held-modifier + Start sweep (`L+Start`, `R+Start`, `L+R+Start`, `A+B+Start`,
  `L+R+A+B+Start`, `Up+Start`, `Down+Start`). None produced a new screen or
  an extra menu row.

## 4. Address map

| Item | ROM / file address | Notes |
|---|---|---|
| crt0 `main` pointer | `0x08000124` → `0x081BB6F8` (Thumb) | from header literal pool |
| Main dispatch | `0x081BB6A8` | reads state word `0x02003C04`, cases 2–6, jump table `0x081BB6C0` |
| Screen manager dispatch | `0x081E51A4` | 41-entry jump table at `0x081E5204`, index at `0x0200869C` (correlated, **not** a load-time selector — proven by patch test) |
| Key-input routine A | `0x081C200C` | literal `0x04000130` at `0x081C2098`; checks Start/A/B edges |
| Key-input routine B | `0x081EC634` | `0x04000130` at `0x081EC654`, mask `0x3FF` at `0x081EC658`; stores pressed keys at `0x02009606`, previous at `0x02009604` (Derived) |
| UI window table | `0x020082B4` (RAM) | 43 objects, stride `0x74C`, each with ROM string pointer at `+0x08` (Derived from `0x081E4F1C`) |
| Pause flag | `0x02003C30` (RAM, byte) | `0x00` gameplay → `0x01` pause (Observed, savestate diff) |
| Pause menu state | `0x02003C04` (RAM, u32) | `2` at language select and main menu (Observed, live debugger) |
| Text/string bank (EN) | file `0xEF0189`–`0xEF2D55` | plain NUL-terminated ASCII |
| Text/string bank (DE) | file `0xEF6DED`–`0xEF91xx` | mirrors of the cheat menu |
| Offset tables (per language) | file `0xEF0000` (98 entries), sub-tables `0xEF2E6C`… | top-level values carry the low-bit tag |
| Cheat-menu string block | file `0xEF2441`–`0xEF24CD` | see §6 |
| Unlock messages | file `0xEF028C`, `0xEF25A4`, `0xEF25B9`, `0xEF277E` | "Level unlocked in quick start", "Omaha level unlocked", "Survival mode unlocked", "Maximum GI unlocked." |

## 5. Algorithm

No checksum/serial-code algorithm exists in this image. The only algorithmic
assets reverse-engineered were the engine's data accessors:

- **String storage**: NUL-terminated ASCII in a language bank; top-level offset
  table at `0xEF0000` contains 98 32-bit values whose low bit is a tag; UI code
  selects strings through a RAM window table at `0x020082B4` / text IDs passed to
  `0x081E4F1C`.
- **Input model**: `KEYINPUT` (`0x04000130`, active-low) is XORed with the
  previous value to derive edges; pressed mask is stored at `0x02009606`.
  No comparison against a multi-press key table was found anywhere in the ROM.
- **Screen state**: correlated u32 at `0x0200869C` with observed values
  `{2 title/options, 3 main menu, 8 extras, 9 options, 10 campaign data,
  13 pause, 29 credits, 39 multiplayer, 41 gameplay}`. Patching this word in a
  savestate does **not** change the rendered screen, so it is a side effect,
  not a selector.

## 6. Tables

### 6.1 CHEATS menu — complete enumeration (English bank, file offsets)

| # | String | File offset | ROM address | German mirror (file) |
|---:|---|---:|---:|---:|
| header | `CHEATS` | `0xEF2441` | `0x08EF2441` | `0xEF90EA` |
| 0 | `RESUME` | `0xEF2448` | `0x08EF2448` | `0xEF90F1` (`FORTSETZEN`) |
| 1 | `Invulnerability` | `0xEF244F` | `0x08EF244F` | `0xEF90FC` |
| 2 | `Full Unlocks` | `0xEF245F` | `0x08EF245F` | `0xEF910D` (`Alles freigeschaltet`) |
| 3 | `Level Skip` | `0xEF246C` | `0x08EF246C` | `0xEF9122` |
| 4 | `Add Lives` | `0xEF2477` | `0x08EF2477` | `0xEF912F` (`Bonusleben`) |
| 5 | `Limitless Ammo` | `0xEF2481` | `0x08EF2481` | `0xEF913A` |
| 6 | `Increased Fire Rate` | `0xEF2490` | `0x08EF2490` | `0xEF9151` |
| 7 | `No Reloads` | `0xEF24A4` | `0x08EF24A4` | `0xEF9160` |
| 8 | `Slower Germans` | `0xEF24AF` | `0x08EF24AF` | `0xEF916E` |
| 9 | `One Hit Kills ` | `0xEF24BE` | `0x08EF24BE` | `0xEF9182` |

The immediately following strings (`Waiting for opponent…`, `Link Error.`,
`Press { or | to return to main menu`) belong to the link-play UI, not to the
cheat menu. The menu therefore has exactly **10 rows**: 1 resume + 9 cheats.

The singular pause-menu string `Cheats` (file `0xEF2420`, ROM `0x08EF2420`,
German `0xEF90C3`) sits in the pause-menu string group:
`Game Paused / Resume / Restart Level / Options / Quit to Title / Cheats`.
Only four of those are drawn in the reachable single-player pause menu
(Resume, Quit to Title, Restart Level, Objectives) — see §8.

### 6.2 Unlockables (Extras)

Extras rows: `Survival Mode` and `Max-GI mode` are rendered greyed/locked,
`Credits` and `Nintendo GameCube Link` are selectable (Observed, screenshots
`s_extras_screen2.png`, `s_credits.png`, `s_gclink.png`).

### 6.3 RAM flags (Observed via savestate diffs)

| Address | Change | Meaning |
|---|---|---|
| `0x02003C30` (byte) | `0x00 → 0x01` | gameplay → paused |
| `0x02000003` (byte) | `0x00 → 0x01` | main menu → Extras |
| `0x02000004` (u32) | `0x000036CC → 0x00003758` | screen-time/animation counter |
| `0x02003798` (u32) | same as above | mirrored counter |
| `0x02004C10` (u32) | `0x00000791 → 0x00000818` | mirrored counter |

## 6b. Enumeration

**Code/password space: empty (proven).**

| Search | Space checked | Result |
|---|---|---|
| Password alphabets | whole 16 MiB; literal `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `0123456789ABCDEF`, `1234567890`, `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` | **0 hits** for every pattern |
| Keyword strings (`strings -t x -n 4`, 128,637 lines) | `password` 0, `cheat` 4 (all 4 belong to the CHEATS menu strings), `debug` 0, `unlock` 6, `secret` 13 (all "Find Secret Documents" mission objectives), `code` 4 (SDK "Invalid error code"/"Invalid mem type" + `Codec.` copyright) | no password/cheat-code UI string |
| Direct 32-bit string pointers | whole 16 MiB at 2- and 4-byte alignment to `0x08EF2440..0x08EF24D0` | **0 hits** (cheat menu reached via IDs, not pointers) |
| Key-mask tables | all u16 runs in `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}` and active-low complements; ≥3 consecutive anywhere (7,203 runs) and ≥5 consecutive in data region `0x800000..0x1000000` (4,354 runs) | all runs are code operands or compressed graphics; **no** table with distinct keys + terminator |
| Input combinations in emulator | ~40 sequences on title/Main Menu/gameplay/pause (listed in §3) | no hidden screen, no extra menu row |
| Published codes | 9 websearch queries + 3rd party cheat indexes/Bing/Google/Wayback fetches | search blocked (403/bot challenge); **no** published code literal found in ROM |

**Menu space (the actual cheat surface): fully enumerated** — 10 rows, all
named above, with the 9 cheat effects named by the shipped UI. "Full Unlocks"
is the unadvertised combination that ties the cheat menu to the Extras
unlockables; its effect is **Derived** from the string set
(`Full Unlocks`, `Omaha level unlocked`, `Survival mode unlocked`,
`Maximum GI unlocked.`) and was **not** executed in-game because the menu could
not be opened through the tested input space (§8). No code was minted because
there is no code format to mint; per §0.2 the equivalent menu enumeration is
complete, but the in-menu toggle effects remain unverified.

## 7. Validation evidence

- **Observed** (emulator/screenshots/RAM): every screen listed in §3, the 4-row
  pause menu and its wrap (6 Down presses → index 2), greyed Extras entries,
  the GameCube-link and multiplayer waiting screens, HUD values (99 health,
  23 lives, 30/150 ammo), savestate diffs in §6.3, live `0x02003C04 = 2` at
  language select via mGBA's `-d` debugger with a breakpoint at `0x081BB6A8`.
- **Derived** (disassembly): key-input routines and RAM input addresses,
  crt0 `main`, the 41-state screen manager and the 98-entry text-offset table,
  the mapping of all 10 cheat-menu rows from contiguous ASCII.
- **Inferred**: that `Full Unlocks` sets the Extras/unlock flags; that the
  `Cheats` pause-menu string is used by a menu configuration not reached in
  single-player play (possibly the link/multiplayer pause menu, unreachable
  in a single-console setup).

A prompt-injection check was applied to all fetched web content: one
Cloudflare/DuckDuckGo bot challenge was encountered and ignored; no instruction
from fetched content was followed. No instruction-like text was found in the
ROM strings dump.

## 8. Unknowns

- **Activation of the CHEATS menu was not achieved.** The negative is bounded
  to: (a) all 15 reachable screens walked; (b) ~40 key sequences and held
  modifiers on title, Main Menu, gameplay and pause; (c) a full-ROM key-mask
  table scan; (d) no direct string pointer. A gate that requires a save-bit
  set by campaign completion, a second GBA/Nintendo GameCube link, or an input
  outside the tested space remains possible. The shipped `Cheats` pause string
  and the `Options` pause string that were never drawn are the strongest lead.
- Individual toggle effects (invulnerability, infinite ammo, etc.) were not
  exercised in-game, so their runtime flag addresses are unproven.
- Web-published code lists could not be retrieved from this network; no claim
  is made about what external lists contain.
- The 41 screen-manager states were not individually reachable through normal
  input; patching `0x0200869C` did not select a screen, so it is not a usable
  gate.

## 9. Tooling

Scripts created in `/tmp/mohinfiltrator/`:
`phase0.py` (hash/header/logo scan), `ptrscan.py`, `strptrs.py`, `ldrsan.py` /
`ldrscan.py` (PC-relative literal xrefs), `keyscan.py` (button-mask scan),
`ss.py` / `gbAs` parser, `diffss.py` (savestate RAM diff), `findstr.py`,
`uitext.py`, `statesweep.py`, `helper.py`, `dbg.py`, `m.py`, `dbgnav.py`,
`nav.py`, `combtest.py`, `mdbg_server.py` (pty-based mGBA `-d` debugger driver).

Toolchain: `binutils-arm-none-eabi` (`arm-none-eabi-objdump -M force-thumb`),
Capstone 5.0.7 / Keystone, mGBA (SDL), Xvfb, openbox, xdotool, scrot,
ImageMagick, Python 3.13. The GDB stub on port 2345 was occupied by another
agent's mGBA, so mGBA's stub-free `-d` CLI debugger over a pty was used for
live RAM reads; savestate `gbAs` diffs were the primary RAM evidence.

No ROM or copyrighted asset is redistributed by this report.
