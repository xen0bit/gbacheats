# Gadget Racers (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Gadget Racers/Gadget Racers.gba` |
| Size | 4,194,304 bytes (0x00400000) |
| `file` | Game Boy Advance ROM image: "GADGETRACERS" (AQAE5Z, Rev.00) |
| Header title (0xA0) | `GADGETRACERS` |
| Game code (0xAC) | `AQAE` (USA) |
| Maker (0xB0) | `5Z` |
| Version (0xBC) | `0x00` |
| Fixed 0x96 (0xB2) | present |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock, **not** a cracktro) |
| Header checksum (0xBE) | `0x0000` |
| Complement byte (0xBD) | `0x3E` (recomputed from 0xA0..0xBC = `0x57` → header was rebuilt/edited) |
| MD5 | `484128abb48b33871c909403c90b9b04` |
| SHA-1 | `bef8444d0730b61e55883cc3edf754f884f7df61` |
| SHA-256 | `7501109d0e47dcb6fd74c017e97a952ff1da68216a0713d971f98d1a95872886` |

Also known as *Choro Q Advance* / *Choro Q HG* / *Penny Racers* (same Electronics Application / MTO engine family as GT Advance).

**Embedded-header / patch scan (Phase 0):** scanning the entire image for the 156-byte Nintendo logo (header +4) returns exactly one hit, at file offset `0x0`. There is no multiboot stub, no second game image, and no appended trainer/cracktro. The stock entry word and the edited header checksum/complement are consistent with a scene-rebuilt header only; game code itself was not patched at the entry point.

## 2. Executive summary

This is a **bounded negative** for a developer-intended password/cheat system in this USA build.

* The only "code-like" published GBA cheat is the **DRAGON name code** ("start a game, rename it DRAGON, then change it back to get the Dragon parts"). On this ROM it is **inactive**. A clean game created with the neutral name `AAAAAA` was renamed to `DRAGON` via Options → Change Name; the resulting save differs from the baseline in **exactly the five name bytes** at SRAM `0x0E000014..0x18` and in no flag byte. Every published DRAGON literal is also absent from the 4 MiB image under ASCII, UTF-16LE/BE, `+0x20` case shift, byte-reversal, every constant XOR (0x00–0xFF), nibble-swap, bit-reversal, and 5-/6-bit packings; it is likewise absent from decompressed IWRAM/EWRAM dumped from a savestate. The published list itself flags this code as "(JP)" — consistent with it being stripped from the US SKU.
* There is **no password screen, no debug menu, and no button-code table** on any reachable screen. The three published GBA "cheats" that do exist are trivial single-button triggers (title `B`, in-race `Up`) plus save-bit unlockables (medals / parts / courses). They were all exercised in the emulator.
* All reachable screens were walked with RAM evidence: Player Name Entry, Racer Body Entry, title attract + both prompts, Main Menu, Options, Change Name, Quick Race (course/racer/transmission/race/pause), Link-Play, and the World Map (New Game). No hidden screen was reached by any of the 14 button/combination probes at the title prompt.
* Because no validator exists, §0.2's "mint a novel code" deliverable is replaced by its negative-result counterpart: the input alphabet, name space, button space, and literal spaces are characterised and counted below, and the published literals are shown to be absent or inert.

## 3. How to reproduce

Emulator: `mgba -3 Gadget Racers.gba` under `Xvfb :318` with `SDL_AUDIODRIVER=dummy`. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. **Hold keys 35–60 ms**, not 150 ms: this engine double-steps on a 150 ms hold.

Menu path used for every test:

1. Boot (license → CAUTION → Player Name Entry). Type a name; `Start` jumps the cursor to `OK`; `A` confirms.
2. Racer Body Entry → pick Racer#1 → `A` → confirmation dialog → `A`.
3. Title attract → `A` at "Press A Button" → license/title cycle → `A`/`Return` at "Press START" → **Menu**.
4. Menu → Options → Change Name (the rename surface used to test DRAGON) / Return to Title.
5. Menu → Quick Race! → course (1–5) → racer (1–5) → transmission (AT/MT) → race → `Start` = Pause (Restart / Retire / Cancel).
6. Menu → New Game → World Map / Circuit Area (5 locked entries).
7. Menu → Link-Play → Rankings Mix / Link Competition.

Published codes tested: `DRAGON` (rename path), `B` at both title prompts, `Up` during a race, medal/tournament unlockables (verified as save-bit progress, not codes).

Screenshots were kept on disk under `/tmp/opencode/gadget/`; RAM/address proofs (below) are primary.

## 4. Address map

| Item | Address / offset | Notes |
|---|---|---|
| Header title | `0x080000A0` | `GADGETRACERS` |
| Game code / maker | `0x080000AC` / `0x080000B0` | `AQAE` / `5Z` |
| Stock entry branch | `0x08000000` | `0xEA00002E` |
| Nintendo logo scan | one hit at file `0x0` | no second header |
| Generic key-input handler | `0x080003AC` | `ldr r0,[pc,#52]` → `0x04000130`; `ldrh`; `eors r6,r1` with `0x03FF` → active-high current-key mask |
| Its literal pool | `0x080003E4`..`0x0800046A` | `0x04000130`, `0x03FF`, `0x03000000`, `0x0000080A`, `0x00000806`, `0x0000080F`, `0x0000080E`, `0x00000808`, `0x0000080C` |
| Button state globals (IWRAM) | `0x03000806` (held), `0x03000808` (pressed), `0x0300080A`, `0x0300080C` (released), `0x0300080E` (index), `0x0300080F` (repeat delay) | written by `0x080003AC` |
| Player-name buffer | IWRAM `0x03005018` (savestate raw `0x1E018`) | 8-byte field; 6 typed chars + `0x6D` blanks observed |
| Name in SRAM | `0x0E000014` (`.sav` file offset `0x14`) | same charset encoding |
| KEYINPUT | `0x04000130` (savestate raw `0x530`) | active-low, 16-bit |
| Font/code table region | ROM `0x35E310`–`0x35E430` | ascending glyph-index ramps (`0x00,0x01,…`, `0x20,0x21,…`, `0x60,0x61,…`), not text |
| Multiplayer lib signature | ROM `0x04892C` | `MultiSio010316` |

Savestate layout used for RAM proofs: mGBA `.ssN` is a PNG with a zlib `gbAs` chunk; decompressing gives 397,312 bytes for this 4 MiB ROM. IWRAM starts at raw `0x19000`, EWRAM at raw `0x21000`, KEYINPUT sits at raw `0x530`.

## 5. Algorithm

There is no password algorithm to reverse. The two mechanisms that exist are:

```
# Player name entry (the only user-typed 6-symbol field)
charset: 0x0A..0x23 -> 'A'..'Z'; 0x24..0x3D -> 'a'..'z'; 0x6D -> blank
buffer:  IWRAM[0x03005018] (8 bytes), mirrored to SRAM[0x0E000014]
confirm: Start -> OK cell; A -> accept name; B -> cancel
validator: none — the value is stored verbatim; no comparison against a secret string
```

```
# Button input, 0x080003AC
held  = 0x03FF ^ (u16 *)0x04000130            # active-high
pressed = held & (held ^ previous)
released = ~held & previous
state globals at 0x03000806/08/0A/0C/0E/0F
```

No comparison of `held`/`pressed` against a fixed sequence exists in any reachable handler that was found by static or dynamic search; the title/race button actions are immediate single-input branches.

## 6. Tables

**Name charset** (decoded empirically from savestate diffs; `AAAAAA` → `0A 0B 0C 0D 0E 0F`, `C` → `0C`, blank → `0x6D`):

| Bytes | Meaning |
|---|---|
| `0x0A`–`0x23` | `A`–`Z` |
| `0x24`–`0x3D` | `a`–`z` |
| `0x6D` | blank / unused slot |

**Published GBA codes, verification status:**

| Source | Code | ROM literal | In-game result |
|---|---|---|---|
| GameFAQs / Planet Cheats / AbsolutCheats / ChapterCheats | "Demo mode: press B when Press Start/Enter appears" | no key-mask table found | Pressed at both title prompts; no distinct effect vs. ordinary attract advance |
| Same sites | "Use horn: press Up during a race" | no key-mask table found | Pressed in race: KEYINPUT `0x03FF`→`0x03BF` (RAM-confirmed input), no HUD change; effect is audio-only, harness had `SDL_AUDIODRIVER=dummy` |
| Same sites | "Medals: collect all parts / bodies / engines, complete all areas" | n/a | Save-bit progress system, not a code |
| SuperCheats / AbsolutCheats / ChapterCheats | "Rename to DRAGON (JP), then back → Dragon parts" | absent from ROM in all tested encodings | Save diff after DRAGON rename = name bytes only; **inactive in AQAE** |

The GameFAQs "Codes" section (R1/R2/L1/L2 button sequences, 6400000 etc.) is **PlayStation 2** content — the page mixes both platforms; those codes do not apply to the GBA SKU. No GameShark/CodeBreaker codes are reported (out of scope).

## 6b. Enumeration

**Name / password space (bounded).** The only writable symbol field is the 8-byte player name; 6 positions are normally filled. Alphabet size = 52 letters + blank = 53 distinct glyphs (the on-screen keyboard offers exactly `A`–`Z`, `a`–`z`; blank is the unfilled state). For the 6-character case the representable name space is 53^6 ≈ 2.2×10^10 values; for the full 8-byte field, 53^8 ≈ 6.3×10^13. A validator, if present, would have to compare against a stored literal or compute a checksum. Two exhaustive searches were run over that space's *comparison material*:

* `DRAGON` encoded in the game charset (`0D 1B 0A 10 18 17`) was searched in the ROM under all 256 additive offsets, all 256 XOR keys, nibble-swap, bit-reversal, 5-bit and 6-bit packings, as UTF-16LE/BE, plain ASCII, lowercase, `±0x20` case-shift and byte-reversed — **0 hits**.
* A generic scan of the ROM (7,894 runs) and of decompressed RAM (83 runs) for any ≥6-byte string made only of valid charset bytes found only compressed-data noise and the `________` empty name — **no secret-name table**.
* The game's own `Change Name` path was used as the oracle: fresh `AAAAAA` game → rename to `DRAGON` → save diff = 5 name bytes only (`0x14,0x15,0x17,0x18,0x19`); no flag byte changed. Renaming back changed only bytes inside the 8-byte name field.

**Button-code space (bounded).** From a saved "Press A Button" title state, 14 inputs were applied with identical timing and their screens captured: `A`, `B`, `L`, `R`, `Start`, `Select`, `Up`, `Down`, `Left`, `Right`, `L+R`, `A+B`, `Start+Select`, `Up+Down`. Only `A` produced an immediate state change (advance to the license/title cycle). `B` — the published demo code — did not produce a distinct screen at that prompt; at "Press START" it also merely advanced the attract sequence. No undocumented combination produced a new screen, counter, or menu.

**Debug-menu space (bounded).** No screen in the walk (title, name entry, racer body entry, menu, options, quick race course/racer/transmission/race/pause, link-play, world map) exposes a debug entry. ASCII and tile-index charset searches for `DEBUG`, `SECRET`, `TEST`, `CHEAT`, `CODE`, `PASSWORD`, `HIDDEN`, `BONUS`, `SPECIAL`, `MENU` returned **0 hits** in both ROM and decompressed RAM (only incidental `CAR`/`win` byte patterns in compressed data).

**Novel code.** Not applicable: no code system exists to mint from. Per §0.2 this negative is bounded by the counts and searches above rather than left as an untested claim. No code absent from a published list could be generated because there is no accepted-code set beyond the player's own name, which is not a cheat.

**Bounds proven by rejection.** Out-of-range inputs were exercised on the real screens: the World Map's five locked "???" entries cannot be selected (they are progress-gated, not code-gated), the Link-Competition partner search times out without a second console, and the DRAGON rename produces no flag change. The 14-input title probe is the rejection set for button-based codes.

## 7. Validation evidence

**Observed (emulator / RAM):**
* Name buffer `0x03005018` held `0A 0B 0C 0D 0E 6D` after typing `ABCDE` (savestate raw diff).
* Save at SRAM `0x14` = `0D 1B 0A 10 18 17 6D 6D` after renaming to DRAGON; baseline `0A×6 6D 6D` after creating with AAAAAA.
* Fresh-baseline → DRAGON diff: exactly offsets `0x14,0x15,0x17,0x18,0x19` (name glyphs); no other byte.
* KEYINPUT at savestate raw `0x530`: `0x03FF` (released) → `0x03BF` (Up held) during the race horn test.
* All 14 title-button probes screens captured (`b2_*.png`); only `A` changed state.
* Screens enumerated with RAM snapshots: name entry (`ss1`–`ss3`), main menu (`ss6`), pause (`ss9`), title prompt (`ss2`), race (`ss7`/`ss8`).

**Derived (disassembly):**
* `0x080003AC` reads `0x04000130`, XORs with `0x03FF` to form active-high masks, and stores held/pressed/released/index/state at `0x03000806`–`0x0300080F`.
* The character-at-key lookup loop at `0x080003FC`–`0x0800041C` indexes a table through the `0x03000810` base — normal name-entry input, not a cheat matcher.
* Stock ARM entry `0xEA00002E` with no patched first 4 KiB.

**Inferred (labelled):**
* The DRAGON code is JP-only and stripped from AQAE; the published "(JP)" annotation and the total absence of the literal support this, but the Japanese ROM was not available for a cross-check.
* The horn is an audio effect (published description + no HUD change observed with audio disabled); the sound itself was not captured.

**Prompt-injection check:** Fetched cheat pages were treated as data. No page contained instructions directed at the analyst; the only anomaly was a DuckDuckGo bot challenge and standard 403 responses from GameFAQs/cheatcc, both handled by using archived copies. Nothing was executed from fetched content.

## 8. Unknowns

* The Japanese build (Choro Q Advance) was not analysed; if the DRAGON code exists there, its validator/table could not be enumerated from this SKU.
* The exact bit that drives the title `B` attract variation was not isolated: savestate A/B diffs at the animated attract screen are dominated by demo motion, so no single stable flag was attributable to `B`.
* The medal/tournament unlock bits in the 32 KiB SRAM save were not individually mapped to their setter call sites; they are progress-gated content, not codes, and were left as save-format work.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python `struct`/`zlib` for header, logo scan, savestate `gbAs` decompression and byte diffs.
* `arm-none-eabi-objdump -M force-thumb` and Capstone (`CS_MODE_THUMB`) for literal-pool and key-input handler analysis.
* mGBA 0.x SDL under `Xvfb :318` + openbox, `xdotool` XTEST key events (35–60 ms holds), `scrot`/ImageMagick for crops and montages, PIL-based title-screen frame detector.
* mGBA `-d` CLI debugger (persistent Python daemon driving `cmds.txt`/`reply.txt`) for one-frame stepping and direct `r/4` RAM reads; GDB stub (`-g`) was tried but this build's stub is incompatible with `gdb-multiarch`.
* Web: DuckDuckGo/Bing result pages plus `web.archive.org` snapshot of the GameFAQs cheats page for published-code discovery.

## 10. Legal note

No ROM bytes, graphics, music, or extracted assets are redistributed here — only hashes, addresses, encodings, method, and findings.
