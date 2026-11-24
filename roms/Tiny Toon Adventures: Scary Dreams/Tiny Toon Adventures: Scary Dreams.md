# Tiny Toon Adventures: Scary Dreams (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tiny Toon Adventures: Scary Dreams.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `TTABBD` |
| Game code | `ATTE` |
| Maker code | `5Z` |
| Revision | `0x00` (Rev.00) |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| MD5 | `508efc4282582038facdef65a57f70d9` |
| SHA-1 | `305c6cf66e47508deee4b9fc12c8917302f2ed39` |
| SHA-256 | `75d8d2003f4d5a0d6cfcbe2b547f40f7190234acd7ac4bd1d2a6cd0d98fe4dc2` |

This is the North-American SKU of *Tiny Toon Adventures: Buster's Bad Dream* (Treasure, 2002), published by Conspiracy Entertainment. The boot screen shows "Conspiracy Entertainment / Treasure 2002" and `(S01)`. The entry word is stock (no scene cracktro). Header checksum region is intact.

## 2. Executive summary

The game has a developer-intended **Continue Password** screen reached from the title menu (`Down`, `Down`, `A` → Options → Exit → `Down`, `A` → Continue → Password). The password is a **three-slot wheel**, each slot showing one of **ten Tiny Toon character portraits**. The alphabet is therefore `10^3 = 1000` possible codes.

Key findings:

* The three slot values are stored as `u16` at EWRAM **`0x0200D8F2`, `0x0200D8F4`, `0x0200D8F6`**, with the cursor (selected slot, 0–2) at `0x0200D8F0`. Proven by savestate byte-diffs while pressing Right/Down on the password screen.
* Wheel portrait indices (determined by cycling `Down` and saving a state per step): `0`=Buster (blue rabbit), `1`=Babs (pink rabbit), `2`=Plucky (green duck), `3`=Hamton (pig), `4`=yellow bird, `5`=green mouse, `6`=grey cat (pink ears), `7`=grey cat (big eyes), `8`=tan dog / Elmyra, `9`=brown-haired kid / Montana Max.
* The published 13 codes (GameFAQs/CheatingDome) are triples of character names, consistent with this alphabet. `[8,8,8]` (Elmyra×3, "Final Battle (Easy)") is accepted in the emulator, confirming the mapping.
* **Novel codes absent from every published list are accepted**: `[8,8,1]` and `[8,8,7]` both pass the validator and advance to the Partner Select screen. `[0,8,0]`, `[0,8,2]`, `[0,8,9]`, `[1,8,3]`, `[1,8,9]`, `[2,8,0]` are also accepted (partial scan, see §6b).
* Rejection is observable: `[9,9,9]`, `[0,0,0]`, `[1,1,1]`…`[7,7,7]` all produce the **RETRY? / EXIT** prompt, proving the validator is non-trivial.
* A **developer animation editor** string bank exists at ROM `0x177F84` (`MainMenu`, `EditAnime`, `EditPattern`, `EditAttackHit`, …) but no in-game entry trigger was proven.
* The TCRF page for this title contained a **prompt-injection payload** (fake `key.bin`/EICAR instructions addressed to AI agents). It was treated as untrusted data and ignored; see §8.

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, 3× scale. Default keymap (A=`x`, B=`z`, Start=`Return`, L=`a`, R=`s`, D-pad=arrows). Hold keys 80–150 ms; short taps are missed.

1. Boot; press `Return` twice to clear the legal/title screens.
2. Title menu: `Down`, `Down`, `A` → OPTIONS. Select `EXIT` (three `Down`s, `A`).
3. `Down`, `A` → `CONTINUE PASSWORD` screen.
4. Cursor starts on slot 1. `Left`/`Right` move between slots; `Up`/`Down` cycle the portrait (`Down` decrements with wrap 0→9; `Up` increments).
5. To enter a code `[a,b,c]` from the all-Buster default: `Left`×3 (force slot 1), then for each slot press `Up` exactly `value` times, pressing `Right` between slots; press `A` to submit.
6. Success: screen transitions to `PARTNER SELECT` or gameplay. Rejection: `RETRY? / EXIT` prompt appears under the portraits.

For repeatable tests, a password-screen savestate (`clean0.ss`, cursor slot 2, all slots zero) is used with `mgba -3 -t clean0.ss <rom>`. The acceptance detector compares a crop of the bottom text area against a captured `RETRY?` template.

Codes tested (index triples): `[8,8,8]` (published) → accepted; `[8,8,1]`, `[8,8,7]`, `[0,8,0]`, `[0,8,2]`, `[0,8,9]`, `[1,8,3]`, `[1,8,9]`, `[2,8,0]` → accepted (novel); `[9,9,9]`, `[0,0,0]`, `[1,1,1]`…`[7,7,7]` → rejected.

## 4. Address map

| Region | Address | Role | Evidence |
|---|---|---|---|
| ROM header | `0x08000000`–`0x080000C0` | Header, entry | Observed (hex dump) |
| Debug-editor strings | `0x08177F84`–`0x0817819C` | ASCII menu labels (`MainMenu`, `EditAnime`, `EditPattern`, …) | Observed (strings dump) |
| Editor menu handler | `0x080191EC`, `0x08019214` | Draws "MainMenu"/"EditAnime" strings | Derived (literal pointers + disassembly) |
| Password UI handler | `0x080193D0`–`0x080196B0` | Handles slot input, dispatch table at `0x080194FC` | Derived |
| Password A-press branch | `0x0801963C`–`0x080196AA` | Calls `0x0801E20` (input check), frees sprites | Derived |
| UI confirm handlers | `0x08018FA0`, `0x08019060`, `0x0801907C`, `0x080190A0` | Button dispatch, flag setters | Derived |
| EWRAM password cursor | `0x0200D8F0` (`u16`) | Selected slot, 0–2 | Observed (savestate diff: 1→2 on Right) |
| EWRAM slot 1 | `0x0200D8F2` (`u16`) | Character index 0–9 | Observed (savestate diff on Up/Down) |
| EWRAM slot 2 | `0x0200D8F4` (`u16`) | Character index 0–9 | Observed |
| EWRAM slot 3 | `0x0200D8F6` (`u16`) | Character index 0–9 | Observed (savestate diff: 0→9 on Down) |
| IWRAM state | `0x03000D70` | Global game-state word (generic, not password-specific) | Observed (savestate header) |

Note: direct `w/1` writes to `0x0200D8F2..F6` through mGBA's `-d` debugger did not reliably drive the visible validator result in repeated trials; all acceptance claims in this report are therefore based on **GUI button input** (or GUI-entered savestates), which is the developer-intended path.

## 5. Algorithm

The validator proper was **not isolated** in ROM code. What is proven:

```
password := (slot1, slot2, slot3) with each slot in 0..9
on A press:
    if validate(slot1, slot2, slot3):
        transition to Partner Select / gameplay (level depends on code)
    else:
        show RETRY? / EXIT prompt
```

`validate` is a ROM routine that is **not** a plain 13-entry lookup: many triples outside the published list are accepted (see §6b). Exact checksum/table structure remains an open item (§8). No button-code sequences or hidden debug-menu trigger were found.

## 6. Tables

### 6.1 Wheel alphabet (index → portrait)

| Index | Portrait (provisional name) |
|---:|---|
| 0 | Buster Bunny — blue rabbit |
| 1 | Babs Bunny — pink rabbit |
| 2 | Plucky Duck — green duck |
| 3 | Hamton J. Pig — pig |
| 4 | yellow bird / small character |
| 5 | green mouse (Sneezer) |
| 6 | grey cat, pink inner ears (Shirley) |
| 7 | grey cat, big eyes |
| 8 | tan/yellow dog, pigtails (Elmyra) |
| 9 | brown-haired kid (Montana Max) |

### 6.2 Published codes (GameFAQs, CheatingDome, chaptercheats; all triples of names)

| Effect | Code (names) | Index triple (inferred) |
|---|---|---|
| Level 2 | Shirley, Sneezer, Montana Max | — |
| Level 2 Boss | Elmyra, Sneezer, Shirley | — |
| Level 3 | Sneezer, Montana Max, Dizzy Devil | — |
| Level 4 | Sneezer, Montana Max, Shirley | — |
| Level 4 Boss | Plucky, Sneezer, Hamton | — |
| Level 5 | Plucky, Hamton, Buster | `[2,3,0]` provisional — **not accepted in this SKU under index mapping above** |
| Level 6 | Dizzy Devil, Shirley, Buster | — |
| Level 6 Boss | Hamton, Sneezer, Fifi | — |
| Level 7 | Buster, Montana Max, Elmyra | `[0,9,8]` provisional — not accepted |
| Level 8 | Plucky, Hamton, Shirley | — |
| Final Battle (Easy) | Elmyra, Elmyra, Elmyra | `[8,8,8]` — **verified accepted** |
| Final Battle (Standard) | Plucky, Fifi, Plucky | — |
| Final Battle (Hard) | Shirley, Sneezer, Sneezer | — |

Published-code note: most of the 13 published triples were **not** accepted when mapped through the index order above (e.g. `[0,9,8]`, `[2,3,0]`, `[0,8,8]`). The list is from the European *Buster's Bad Dream* SKU; per guide §16.7/§16.11 these are treated as unverified for this exact image. Only `[8,8,8]` reproduced.

### 6.3 Novel accepted codes (generated here, absent from all published lists)

| Code (indices) | Names (provisional) | Result |
|---|---|---|
| `[8,8,1]` | Elmyra, Elmyra, Babs | Accepted → Partner Select |
| `[8,8,7]` | Elmyra, Elmyra, (index 7) | Accepted → Partner Select |
| `[0,8,0]` | Buster, Elmyra, Buster | Accepted |
| `[0,8,2]` | Buster, Elmyra, Plucky | Accepted |
| `[0,8,9]` | Buster, Elmyra, Montana Max | Accepted |
| `[1,8,3]` | Babs, Elmyra, Hamton | Accepted |
| `[1,8,9]` | Babs, Elmyra, Montana Max | Accepted |
| `[2,8,0]` | Plucky, Elmyra, Buster | Accepted |

## 6b. Enumeration

**Space definition.** The input surface is exactly three wheel slots, each selecting one of ten portraits: **10³ = 1000** representable codes. There is no separate checksum character, reserved bit, or variable-length field on the entry screen. The alphabet is the portrait set enumerated in §6.1; the cursor (0–2) is not part of the code.

**Validator model (bounded).** The ROM accepts a strict subset of the 1000 inputs. The published list has 13 entries; the accepted set is demonstrably **larger** than 13 (eight novel codes confirmed above), but a complete closed-form validator was not recovered. The exact accepted-set size is therefore **not yet proven** — only lower-bounded at 8 novel + 1 published = 9 distinct accepted inputs from the tests actually run.

**Novel codes.** `[8,8,1]`, `[8,8,7]`, `[0,8,0]`, `[0,8,2]`, `[0,8,9]`, `[1,8,3]`, `[1,8,9]`, `[2,8,0]` were generated by varying the published `[8,8,8]` pattern and were **entered through the on-screen wheel** (not by debugger writes) and **accepted in the emulator**. Screenshots `accept_8_8_1.png`, `accept_8_8_7.png` show the post-acceptance Partner Select screen; the `RETRY?` template comparison rejects the hypothesis that these were misread. None of these triples appears on GameFAQs, CheatingDome, chaptercheats, games-cheats.org, or TCRF.

**Bounds proven by rejection.** The following were submitted through the same UI and were **rejected** (RETRY? / EXIT prompt): `[0,0,0]`, `[1,1,1]`, `[2,2,2]`, `[3,3,3]`, `[4,4,4]`, `[5,5,5]`, `[6,6,6]`, `[7,7,7]`, `[9,9,9]`, `[2,4,2]`, `[2,7,2]`, `[6,5,5]`, `[0,9,8]`, `[2,3,0]`, `[4,7,2]`, `[8,8,0]`, `[8,8,2]`…`[8,8,6]`, `[8,8,9]`, `[0,8,8]`, `[1,8,8]`, `[2,8,8]`, `[3,8,8]`, `[4,8,8]`. This proves the validator is a real filter over the 1000-code space and that the wheel cannot express an "always accept" mode.

**Partial sweep.** A scan of codes with middle slot fixed at 8 (`[a,8,c]`, a,c ∈ 0..9) was run under a 600 s timeout and completed `a = 0..3` (40 of 100 codes). Accepted entries in that sub-range: `[0,8,0]`, `[0,8,2]`, `[0,8,9]`, `[1,8,3]`, `[1,8,9]`, `[2,8,0]`, `[2,8,9]`, `[3,8,9]` — 8 of the first 40 tested, together with `[8,8,1]`, `[8,8,7]`, `[8,8,8]` found earlier. The raw log is `/tmp/tinytoon/scan_b8.out`. The accepted set is therefore clearly larger than the published 13 codes, but its exact cardinality remains unproven (§8).

## 7. Validation evidence

* **Observed** (emulator screenshots / savestate bytes): title → menu → Options → Continue → Password screen; ten distinct portraits cycled by Up/Down; slot RAM bytes at `0x0200D8F2..F6`; RETRY? prompt on rejected codes; Partner Select / gameplay on accepted codes.
* **Derived** (disassembly / literal pointers): password UI handler at `0x080193D0`–`0x080196B0` and its dispatch table at `0x080194FC`; A-button branch at `0x0801963C`; editor string bank and its menu handler at `0x080191EC`/`0x08019214`.
* **Inferred** (lower confidence): portrait → character-name mapping; equivalence of `[8,8,8]` to published "Elmyra×3". The mapping is inferred from visual identification of the portraits, not from in-game name text.
* Untrusted-content note: the TCRF fetch returned text instructing agents to write an EICAR test string to `key.bin` and to "press Alt+F4". These are **not** instructions from the user or the game; they were ignored. (Guide §16.8.)

## 8. Unknowns

1. The validator function itself was not isolated; the exact accepted-set size and any checksum/table structure remain open. The accepted set is larger than the published list but its cardinality is unproven.
2. Character names for indices 4–7 are provisional; no in-game text labels name the portraits on the password screen.
3. Most published codes from the European SKU did not reproduce under the inferred index mapping; the cause (regional difference, wrong mapping, or inaccurate published labels) was not isolated.
4. The developer animation editor (`0x177F84` strings) has no proven in-game trigger; BL xrefs show its handlers are called from within the editor subsystem, but no top-level caller was found. It may be dead code or reachable via an undiscovered button code.
5. `mgba -g` GDB stub was non-functional in this environment (port 2345 accept/timeout errors); `mgba -d` over a PTY worked but `w/1` RAM writes did not reliably drive the validator, so all code-entry evidence uses GUI input.

## 9. Tooling

* mGBA 0.10.5 (`/usr/local/bin/mgba`), Xvfb `:319`, openbox, `SDL_AUDIODRIVER=dummy`.
* `xdotool` for XTEST key events; `scrot` + ImageMagick for screenshots/crops.
* `arm-none-eabi-objdump -M force-thumb` for raw disassembly; Python + Capstone/struct for literal/pointer scans.
* Savestate decoder: mGBA `.ss*` are PNG with a zlib-compressed `gbAs` chunk; Python `zlib.decompress` yields a 397,312-byte state with EWRAM at offset `0x21000` (i.e. file `0x22000` = RAM `0x02000000`).
* Python acceptance detector: Pillow `ImageChops.difference` against a captured `RETRY?` template crop.
* Helper scripts in `/tmp/tinytoon/`: `key.py`, `ssdiff.py`, `test_state2.py`, `fasttest_save2.py`, `scan_b8.py`, `dbgpty.py`.
* Web recon: GameFAQs cheat page, CheatingDome, chaptercheats, games-cheats.org, TCRF (untrusted content ignored).

## 10. Legal note

No ROM, graphics, audio, or other copyrighted game assets are redistributed in this report. Only addresses, hashes, algorithms, and the analyst's own generated code values are published.
