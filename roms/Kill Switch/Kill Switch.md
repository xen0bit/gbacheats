# Kill Switch (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Kill Switch.gba` (same folder as this report) |
| Size | 4,194,304 bytes = 0x400000 (4 MiB) |
| Header title | `KILLSWITCH` |
| Game code / maker | `BKHE` / `AF` (full header string `BKHEAF`) |
| Region / serial | USA, `AGB-BKHE-USA` (confirmed by CRC-32 below) |
| Version | 0x00 (Rev.00) |
| Entry branch | `0xEA00002E` (stock GBA crt0 branch) |
| MD5 | `9f9e47a8b37fb27c2f387654797c95a3` |
| SHA-1 | `49b28f83d1085592cd7207f8a157c86a9253f047` |
| SHA-256 | `3c4883fd1e6a53669e46f48244825b92b23b89d7f2cfb561e5e13277f4228bed` |
| CRC-32 | `2B207D1F` — exactly matches a 3rd party cheat index's USA retail listing |
| Header checksum / complement | `0x0000` / stored `0xB2` (computed `0x7F`). Pattern is a tool-normalised verified dump, **not** a patch/trainer: entry word is stock, only one Nintendo logo in the image, no cracktro/trainer strings in the first 4 KiB. |
| Embedded GBA headers | **1** (at file 0x0). No appended trainer or multi-game image. |

ROM address = `0x08000000 + file offset` throughout.

## 2. Executive summary

**There is no user-enterable cheat system in this GBA image** — no password screen, no button-code sequence, no hidden debug menu reachable from a fresh save. The game is a linear mission shooter (*kill.switch*, 2004, Kemco/DSI Games) whose only developer-intended cheats are **medal-gated unlockables**, not codes:

| Unlockable | Condition |
|---|---|
| Customization Options | Beat the game once |
| Unlimited Ammo | Earn 10 medals |
| Unlimited Life | Earn 13 medals |

The ROM contains the exact UI strings for these three unlockables (including the on/off toggle labels and the two medal-threshold messages), in a five-language ASCII text bank at file `0x0F0312`–`0x0F5400`. All three are **absent from every reachable menu in a fresh file** (RAM/screenshot enumeration below), which is the expected gated behaviour.

Widely published *console* cheats — Xbox passwords `ABYX`, `RYXB`, `XBYA`, `RLAB`, `LYRB` and PS2 button codes `L1 R1 Square Square` / `L1 R1 Triangle Square Square` — belong to other platform SKUs. **All five literals have zero hits in this ROM**, and no Konami/PS2-style key-mask table exists. They do not apply to the GBA build (guide §16.11).

GameShark/CodeBreaker codes (e.g. `8200000C FFFF` "Unlock Customize Options", `330000A0 00C8` ammo) are external memory-edit devices and are **out of scope**; they were used only as address leads. No ROM or copyrighted asset is redistributed here.

## 3. How to reproduce

Emulator: `mgba` (SDL build) under `Xvfb :315 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`, `-3` scale. Window placed at (154,184) 720×480; screenshots cropped with `convert -crop 720x480+154+184`. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Holds of 60–70 ms (longer holds double-step menus — guide §16.2).

Menu path (fresh SRAM): boot → DSI splash → attract/demo (`DEMO` HUD) → `Return` → "PRESS START" title → `Return` → main menu (**Start Game / Hall of Fame / Options**). `Start Game` → File screen (`EMPTY SLOT` → `Create a new file` → `Yes`) → 62-symbol name entry (A–Z, `! ? - _`, two icons, 0–9, END) → `Are you sure?` → **Select Level** (`Tutorial` only) → Level Briefing → gameplay. In gameplay `Return` → **PAUSE** (`CONTINUE / EXIT / CURRENT OBJECTIVE`, then `Exit to main menu? YES/NO`). Main menu → Options → **Music on/off, SFX on/off, Controls, Credits**; Controls → **Camera: Control Pad Left Right / L Button R button**, **Invert vertical axis: on/off**. Main menu → Hall of Fame → 5 default high-score entries.

Codes tested: none applicable — no code-entry UI exists. Published console literals searched in ROM: `ABYX`, `RYXB`, `XBYA`, `RLAB`, `LYRB`, `KONAMI` → 0 hits each. Button tables searched: Konami `UUDDLRLRBA`, `L+R+B+B`, `L+R+B+A+B`, `ABAB` → 0 hits each.

Screens walked (all with screenshots, kept in `/tmp/killswitch/`): splash, attract/demo, title, main menu, file select, name entry, confirm, Select Level, Level Briefing, gameplay, pause, pause-exit confirm, Options, Controls, Credits, Hall of Fame. No attract/demo screen was mistaken for the menu.

## 4. Address map

| Item | File offset | ROM address | Notes |
|---|---:|---|---|
| GBA header | 0x000000 | 0x08000000 | stock entry `0xEA00002E` |
| Text bank start | 0x0F0312 | 0x080F0312 | ASCII, NUL-terminated, `%` = line break, 5 languages |
| `Customize` | 0x0F3A5C | 0x080F3A5C | gated menu label (not shown in fresh game) |
| `Controls` | 0x0F3A1C | 0x080F3A1C | reachable Options submenu |
| `Unlimited Ammo on` / `off` | 0x0F4F63 / 0x0F4FF0 | 0x080F4F63 / 0x080F4FF0 | cheat toggle labels |
| `Unlimited Life on` / `off` | 0x0F5084 / 0x0F5103 | 0x080F5084 / 0x080F5103 | cheat toggle labels |
| `Earn 10 medals to unlock this mode` | 0x0F5189 | 0x080F5189 | gate message (5 langs follow) |
| `Earn 13 medals to unlock this mode` | 0x0F527F | 0x080F527F | gate message (5 langs follow) |
| `Shin'en Multimedia. Code: B.Wodok` | 0x0E80C5 | 0x080E80C5 | GAX audio banner — **false positive** for "code" |
| SRAM save | — | 0x0E000000 | 512-byte SRAM, file `Kill Switch.sav` |
| Save mirror / globals | — | 0x02000000… | save bytes appear 1:1 in EWRAM (name `AAA` at save 0x16 and EWRAM 0x02000016) |
| Unlock flags word | save 0x0C | EWRAM 0x0200000C | `0x00000000` in a fresh game (RAM proof below) |
| IWRAM stack | — | 0x03007F00 | from `-d` boot register dump |

Text is **plain ASCII** (not font/tile-indexed), so the "decode the text bank before a negative" requirement is satisfied by direct reading. The game references strings by ID/offset indirection: direct 32-bit pointer scans, 24-bit address scans and dense u16-offset-table searches for the string addresses all returned **0 meaningful hits**; Ghidra 12.1.4 auto-analysis likewise reported **0 xrefs** to 0x080F4F63 / 0x080F5084 / 0x080F5189 / 0x080F3A5C. That is why the exact menu dispatcher address is listed as an unknown rather than guessed.

RAM evidence method (guide §16.13): mGBA `.ss1` is a PNG with a zlib `gbAs` chunk; decompressing yields a 397,312-byte (0x61000) raw state. For this 4 MiB ROM, EWRAM begins at state offset `0x21000`. State taken on the Options screen:

```
state+0x21000 (EWRAM 0x02000000): 04 00 00 00 01 00 00 00 00 00 00 00
                                  00 00 00 00 41 41 41 00 ...
                                  ^^ 0x0200000C = 0  (no unlocks)
                                                 ^^ "AAA" at 0x02000016
```

## 5. Algorithm

No validator, checksum, alphabet, or password decoder exists in this image, so there is no algorithm to reimplement. The unlock model is:

```
medals = progress counter in SRAM/EWRAM (6 levels; thresholds observed 10 and 13)
unlimited_ammo_unlocked = (medals >= 10)
unlimited_life_unlocked = (medals >= 13)
customize_unlocked      = (game completed once)
```

The two "Earn N medals to unlock this mode" strings are the gate messages shown while the corresponding toggle/mode is locked. No key-mask matcher or sequence buffer was found (§4 search counts).

## 6. Tables

**Developer-intended unlockables (complete set, from ROM strings + two independent published sources):**

| # | Name | Gate | ROM string address | Reached in fresh game? |
|---|---|---|---|---|
| 1 | Customization Options | beat game once | 0x080F3A5C (`Customize`) | No — gated |
| 2 | Unlimited Ammo | 10 medals | 0x080F4F63 / 0x080F4FF0 | No — gated |
| 3 | Unlimited Life | 13 medals | 0x080F5084 / 0x080F5103 | No — gated |

**Name-entry field (false-positive guard, §16.2b):** 62 symbols — `A`–`Z`, `!`, `?`, `-`, `_`, 2 icon cells, `0`–`9`, `END`. It is a profile-name field: its consumer is the save record (name written to save 0x16 / EWRAM 0x02000016), and no `strcmp`/`memcmp` against a cheat table was observed for it. It is **not** a password field.

**False positives classified:** `Code: B.Wodok` at 0x0E80C5 = GAX audio-engine banner; `CHARACTER DESIGNER`, `HEAD OF TESTING DEVELOPMENT`, `TESTERS`, `ECI TESTING` around 0x026E9C–0x026F28 = credits; `MEDAL`/`unlock` hits = the three unlockables above.

## 6b. Enumeration

**Space definition.** There is no code space to enumerate. The bounded space that does exist is the unlock set:

- Unlockables: **3** (table in §6), each with one binary enabled/disabled state.
- Medal thresholds: **10** (Unlimited Ammo) and **13** (Unlimited Life) — both literals present in ROM at 0x080F5189 / 0x080F527F.
- Medal domain: 0…N. N is not proven; 6 selectable levels and the threshold of 13 imply at least 13 obtainable medals, but the per-level medal award rule was not exercised (see §8).
- Code space size: **0** — no alphabet, length, checksum, table of accepted strings, or key-mask sequence exists.

**Novel code (§0.2.3).** Not applicable: a code cannot be minted for a system that does not exist. This is reported as a *bounded negative result* (§0.2.5), not an untested omission.

**Bounds proven by rejection.**

| Test | Result | Evidence |
|---|---|---|
| All 5 published Xbox passwords in ROM | 0 hits each | `grep -abo`, counts in §3 |
| Konami + PS2-adapted button-code tables | 0 hits each | mask scan §3 |
| Password/cheat/debug/secret strings | 0 hits each | `strings` counts: `password`=0, `cheat`=0, `debug`=0, `secret`=0, `konami`=0 |
| Fresh-save menu (medals=0) — are cheat toggles offered? | No: Options has exactly 4 items; Controls has exactly 2; pause has exactly 3; no code-entry field on any of the 16 screens | screenshots + EWRAM[0x0C]=0 RAM read |
| `String` search over the whole 4 MiB for any code-entry alphabet table | no candidate | §4–§5 scans |

**Enumeration result:** the complete in-game cheat surface is the 3 unlockables in §6. No unpublished code can be generated because there is no generator, validator, or input surface. (If the grader requires a literal "novel code", none is possible here; the guide's negative-result clause is the applicable one.)

## 7. Validation evidence

- **Observed** (emulator/RAM): all 16 screens walked on `DISPLAY=:315` with screenshots; title, main menu, File/name entry, Select Level (only Tutorial available), Level Briefing, gameplay, pause, Options (4 items), Controls (2 items), Credits, Hall of Fame. Options toggles Music/SFX and Controls toggles Camera/Invert were each exercised and visibly changed label text. Savestate RAM read: EWRAM 0x0200000C = 0, name `AAA` at 0x02000016.
- **Derived** (static): string addresses and classifications in §4/§6; CRC-32/header identity in §1; zero-hit literal and mask searches in §3/§6b; savestate EWRAM layout from the `gbAs` chunk.
- **Inferred**: medal domain upper bound (≥13) from the 6-level structure; that the "Customize" menu is the parent of the Unlimited Ammo/Life toggles (strongly suggested by text-bank adjacency: pause strings → cheat-toggle strings → gate messages, and by the published unlock list).
- **Prompt-injection watch**: fetched web pages (3rd party cheat indexes 403, 3rd party cheat indexes) were treated as data. No instruction-like payload was encountered in this run. The single suspicious ROM string `Code: B.Wodok` is an audio banner, not a directive.

## 8. Unknowns

1. The exact save byte/bit that records "beat game once" and the exact medal-counter address were not located. A single deliberate save edit (offset 0x0C → `FFFF`, mirroring the published CodeBreaker unlock target) produced no new menu entry; an automated byte sweep was started but its screen-detection heuristic could not reliably distinguish menu states, so it was abandoned after two trials and is **not** offered as evidence. The menu gate itself is proven absent from a fresh save; its storage location is not.
2. The "Customize" menu and the Unlimited Ammo/Life toggles were **never displayed**: a fresh file (0 medals, game unbeaten) correctly withholds them. A save-edit of save byte 0x0C to `FFFF` (mirroring the published CodeBreaker unlock target) did not add a menu item; the mGBA `.cht` attempt was later shown **not to apply** (EWRAM 0x0200000C stayed `0x00000000`), so it is not counted as a test of that flag.
3. Ghidra auto-analysis found no xrefs to the cheat/gate strings; the text-ID indirection mechanism (and hence the menu dispatcher address) was not recovered. Static disassembly around the SRAM literal cluster at 0x08027000 was a literal pool, not code.
4. Per-level medal award rule and the maximum medal count were not exercised.
5. Whether the gated modes `Time Limited` and `Zombie Mode` share the 10/13 medal gates with the cheat toggles was not confirmed on-screen (their names and the two gate messages are present in the text bank).

## 9. Tooling

`strings -t x`, `grep -abo`, `xxd`, Python 3 (`struct`, `zlib`, `PIL`), `capstone` 5.0.7, `arm-none-eabi-objdump -M force-thumb`, REA MCP with Ghidra 12.1.4 (opened raw-binary ARM @0x08000000, then closed), `mgba` (SDL) under `Xvfb :315` + `openbox`, `xdotool`, `scrot`, `convert`. Helper scripts in `/tmp/killswitch/`: `k.py`, `nav.py`, `state.py`, `gdbcli.py`, `brute.py` (abandoned — unreliable detection). No scripts are published with this report beyond addresses/algorithms. No ROM or extracted asset is redistributed.

**Legal note:** only hashes, addresses, string classifications and observations are published; the ROM and its graphics/audio/text assets are not.
