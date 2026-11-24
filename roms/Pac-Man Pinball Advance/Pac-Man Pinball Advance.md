# Pac-Man Pinball Advance (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pac-Man Pinball Advance.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `PAC PINBALL` |
| Game code | `BP8E` (maker `AF`) |
| Maker | `AF` (Namco Hometek publishing) |
| Version | 0x00 (Rev.00) |
| Entry word | `0xEA00002E` → stock `0x080000C0` (ARM) |
| Header checksum field | `0x0000` (rebuilt-header artifact, §16.1); complement byte `0xC5` |
| MD5 | `4d7b955b9c19b13d1d776e35ce007f78` |
| SHA-1 | `dfd93f861e571153e0ae0a65799c5d44e5154373` |
| SHA-256 | `63aa68a4fc09ddae078ea11f8185c37ea7d874465114282d29f699d545fb401a` |

**Phase 0 patch/trainer scan (Observed):** Nintendo-logo scan (156-byte logo from header+4) found exactly **one** hit at file offset `0x4` — a single normal header, no multiboot stub, no concatenated image. No `CRC BANDIT`, `TRAINER`, `GAMESHARK`, `CODEBREAKER`, `PROMO`, or `168 HOURS` marker anywhere in the image. Entry branch is the stock `b 0xC0`. File(1) identifies it as `"PAC PINBALL" (BP8EAF, Rev.00)`. **Conclusion: retail, unpatched image; no appended trainer.**

## 2. Executive summary

**This game has no developer-intended in-game cheat system.** There is no password screen, no button-code sequence, no hidden/debug menu, and no unlockable table/character gated by input. Every published "cheat" for this title is an external Action Replay / GameShark / CodeBreaker memory-patch list (out of scope by the engagement rules); 3rd party cheat index lists **"Total cheats available: 0"**, 3rd party cheat indexes' cheats page contains no codes, 3rd party cheat indexes have no page for this game, and the official manual (OCR'd) documents only ordinary gameplay bonuses.

The negative is **bounded, not assumed**:

* **9 reachable screens/states** were walked in mGBA under Xvfb, each with a saved state and extracted RAM (screenshots + RAM signatures in §7).
* **2 ASCII text banks** were decoded in full: the UI bank at `0x0838B30` (16 strings) and the in-game/tutorial bank at `0x1B4B8` (~70 strings). Every string is accounted for by a screen actually reached; the only unrendered strings are four foreign language names (`Deutsch/Francais/Espanol/Italiano`, PAL leftovers in this US build). The custom Pac-Man tile glyphs are a *rendering* layer over ordinary ASCII — there is no hidden tile-indexed text bank.
* **Zero** hits for `password/cheat/code/debug/secret/unlock/hidden/bonus/level select/master` in ASCII, lower, upper, UTF-16LE/BE, or `+0x20`-shifted encodings across the whole 4 MiB.
* **11** common/undocumented button sequences were pressed on the title screen with RAM verification; none changed the screen object pointer (`IWRAM 0x030035CC`).
* A raw key-mask scan returned 2,832 `u16` candidate arrays plus `u8` candidates, **all** false positives inside compressed graphics/audio; no validator function references any of them.
* Published AR/GameShark code literals are absent from the ROM as data (they are cheat-device codes, not in-game codes).

Scope note from §16.11: the SKU was confirmed first (header `BP8E`, maker `AF`, Human Soft / Namco Hometek strings at `0x0838BFE`) so that published lists for the *Pac-Man Collection* GBA or other Pac-Man titles were not misapplied.

## 3. How to reproduce

**Environment:** `Xvfb :318 -screen 0 1024x768x24`, `openbox`, `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, mGBA 0.10.5 (`mgba -3 <ROM>`). Window client area `720x480+154+184`. Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys 60–150 ms.

**Menu path (deterministic from a fresh boot):**

1. Namco logo → title (`PRESS START`). Press **Start**.
2. Intro cutscene (Professor Pac / Pac-Finder, then "Nighttime in Pac-Village"). Press **Start** ~3× to advance.
3. **Main menu** (4 items): START GAME, TUTORIAL, OPTIONS, CREDITS.
4. OPTIONS → SOUND ON / MUSIC ON (2 items only; no language row in this US build). B to return.
5. CREDITS → scrolling name list (matches strings at `0x0838BFE+`). B to return.
6. START GAME or TUTORIAL → **CHOOSE A TABLE**: PAC VILLAGE and HAUNTED BOARDWALK (2 tables, both available from boot — no unlock gate).
7. Select a table → table intro/tutorial overlay (tutorial text from `0x1B7xx–0x1BFxx`, options CONTINUE / EXIT).
8. CONTINUE → gameplay (`Press A Button to Start!`) → press A to launch.
9. **Start** during play → **PAUSE MENU**: CONTINUE / RESTART / MAIN MENU.
10. RESTART → confirmation `Do you really want to Restart?` (No/Yes). MAIN MENU → confirmation `Return to the Main Menu?` (No/Yes).
11. Let 3 balls drain → **game over**: `Your Game is Over.` with RESTART / MAIN MENU.

**RAM capture:** mGBA savestate (`Shift+F1`) → `.ss1` PNG → `zlib.decompress` the `gbAs` chunk (§16.13) → 397,312-byte raw state. IWRAM maps at raw `+0x19000`, EWRAM at `+0x21000` (verified against known IWRAM pointers). Scripts in §9.

**Published codes tested:** none applicable — all published entries are external cheat-device codes. Sample literals (`cddbddc0`, `8c19a124`, `2e4d17b2`, `02d1e328`, `6e4ba334`, `87fad599`, from 3rd party cheat indexes' AR list) searched as raw bytes and `u32` little-endian: **0 hits** in the ROM. 3rd party cheat indexes/manual: no in-game codes.

## 4. Address map

| Address (ROM/file unless noted) | Meaning | Evidence |
|---|---|---|
| `0x00000000` | Header; single logo at `0x4`; stock entry `0xC0` | Observed (Phase 0) |
| `0x08000470` | Joypad read routine: `ldrh` from literal `0x04000130`, `mvns`, `strh` to `0x030016A4` | Derived (Thumb disasm) |
| `0x030016A4` (IWRAM) | Active-high key state (`~KEYINPUT & 0x3FF`); A=1,B=2,Sel=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,R=0x100,L=0x200 | Derived |
| `0x0838B30`–`0x0838BFE` | UI text bank: Start Game, Tutorial, Options, Credits, Choose a table, Sound, Music, On, Off, Main menu, Restart level, Pac village, Haunted, Boardwalk, English..Italiano, credits names | Observed |
| `0x1B4B8`–`0x1BFC0` | In-game/tutorial text bank: scoring events, in-game messages, pause/game-over prompts, table tutorials ("Pac Village", "Haunted Boardwalk"), character names | Observed |
| `0x030035C4` (IWRAM) | Constant RAM state pointer `0x0300359C` (all screens) | Observed |
| `0x030035C8` (IWRAM) | Screen handler pointer: `0` title; `0x0801C564` menu family; `0x0801C6B8` table select; `0x0801E8A8` gameplay family | Observed |
| `0x030035CC` (IWRAM) | Per-screen EWRAM object pointer (distinct for most screens — see §7) | Observed |
| `0x02000000`–`0x0203FFFF` (EWRAM) | Screen/heaps objects; snapshot SHA-256 is a per-screen fingerprint | Observed |

No password validator, code table, alphabet table, key-mask dispatch table, or debug flag writer was found — by construction there is nothing to put in this map beyond the above.

## 5. Algorithm

**Not applicable — no code algorithm exists.** For completeness, the input path was traced: `0x08000470` reads `KEYINPUT` at `0x04000130`, inverts it and stores the active-high mask at `0x030016A4`. Screen dispatch is via the handler/object pointer pair at `IWRAM 0x030035C8/0x30x35CC`, set per screen. No function compares the key-state word against any sequence beyond ordinary menu D-pad/A/B handling; no password buffer, `strlen`/`strcmp` chain, checksum, or key/PRNG table exists in the image.

## 6. Tables

**UI text bank (`0x0838B30`, `\r\n`-delimited, all 16 entries decoded):**

| Off | String | Screen where rendered |
|---|---|---|
| +0x00 | Start Game | Main menu |
| +0x0C | Tutorial | Main menu |
| +0x16 | Options | Main menu |
| +0x1F | Credits | Main menu |
| +0x28 | Choose a table | Table select |
| +0x36 | Sound | Options |
| +0x3D | Music | Options |
| +0x44 | On | Options |
| +0x48 | Off | Options |
| +0x56 | Main menu | Pause / Game over |
| +0x62 | Restart level | Pause |
| +0x73 | Pac village | Table select |
| +0x80 | Haunted | Table select |
| +0x89 | Boardwalk | Table select |
| +0x92..0xB5 | English, Deutsch, Francais, Espanol, Italiano | **PAL leftovers — not rendered in US build** |
| +0xC0.. | Credits roll (NAMCO HOMETEK INC., names) | Credits |

**Menu cardinalities (derived from rendered screens + text bank):** Main menu 4, Options 2, Table select 2, Table intro 2 (Continue/Exit), Pause 3, Confirmations 2 each, Game over 2. No row exists beyond these — Down wraps rather than revealing an unlabelled entry (verified by stepping past the last item on Options, Table select, and Pause).

**In-scope published codes:** none exist. Out of scope (documented only): 3rd party cheat indexes AR codes, 3rd party cheat indexes GameShark/CodeBreaker master codes.

## 6b. Enumeration

§0.2 requires full characterisation of the "code space". For this title that space is **empty**, so the enumeration is of the *search surfaces* that could have hosted a cheat system, with counts:

| Search surface | Space checked | Result |
|---|---|---|
| Password/cheat/keyword strings | 4 MiB × 7 encodings (ASCII, lower, upper, UTF-16LE, UTF-16BE, +0x20 shift, regex word list) | **0 hits** |
| UI text bank | 16 strings at `0x0838B30` | 0 code/debug strings; 4 PAL-only language leftovers |
| In-game text bank | ~70 strings at `0x1B4B8` | 0 code/debug strings |
| Button-code `u16` mask tables | every 2-byte offset in 4 MiB, arrays ≥5 with ≥4 distinct plausible masks | 2,832 raw candidates — **all** false positives in compressed data; 0 with a validator/xref |
| Button-code `u8` mask tables | every byte offset, arrays ≥6 with ≥4 distinct 1–2-bit masks | candidates all in compressed data; 0 in code |
| Hidden button sequences pressed in-game | 11 sequences (Konami forward/reverse, `L+R+Start+Select`, `Start+Select+A+B`, all-D-pad, `L+R`, `L,R,R,L`, 8-way pad loop, Select+Start, UpUpDownDownLR) on title | **11/11 rejected** — `IWRAM 0x030035CC` unchanged, no new screen |
| Reachable screens | 9 distinct states walked with saved states + RAM | 9/9; no hidden/debug screen |
| Published in-game codes | 3rd party cheat indexes, manual OCR (bonuses only) | 0 |

**Novel code (§0.2 item 3):** not applicable — there is no code system from which to mint a novel value. The equivalent deliverable here is the *negative* enumeration above, which is bounded by explicit counts rather than by absence of effort.

**Bounds proven by rejection (§0.2 item 4):** the 11 undocumented button sequences were entered on the title screen and RAM-verified as rejected (no screen-object change). Unlock bounds: both tables were available immediately from a fresh boot (no gated table to unlock). Menu bounds: pressing Down past the last item wrapped on Options (2), Table select (2), and Pause (3) — no hidden 5th/4th row.

## 7. Validation evidence

**Screen-by-screen RAM signatures** (saved `.ss1` states; IWRAM handler = word at `0x030035C8`, object = word at `0x030035CC`; EWRAM SHA-256 over raw `+0x21000..+0x51000`). These are the RAM proofs that each screen was actually reached and not inferred from a demo/attract frame:

| Screen | Handler | Object pointer | EWRAM SHA-256 (first 16) |
|---|---|---|---|
| Title (`PRESS START`) | `0x00000000` | `0x0200262C` | `4351b2bfcfe9a804` |
| Main menu | `0x0801C564` | `0x020004E8` | `1890e59295b8fc2e` |
| Options | `0x0801C564` | `0x020004C8` | `93fba4008128f51f` |
| Credits | `0x0801C564` | `0x02000588` | `c6a3a4e89182c85a` |
| Choose a table | `0x0801C6B8` | `0x02000620` | `f4934106cb8ab2c0` |
| Table intro/tutorial | `0x0801E8A8` | `0x02000720` | `982850035ec0814b` |
| Gameplay | `0x0801E8A8` | `0x02000730` | `a4a3d8137b865c9d` |
| Pause menu | `0x0801E8A8` | `0x02000718` | `828a227747dd2776` |
| Restart confirmation | `0x0801E8A8` | `0x02000718` | `dc3fef95fc2baa5a` |
| Main-menu confirmation | `0x0801E8A8` | `0x02000718` | `943e1a8b16c5ab3f` |
| Game over | `0x0801E8A8` | `0x02000730` | `d5563e50d4f2a006` |

The three menu-family screens share handler `0x0801C564` but have distinct heap object pointers; the gameplay-family screens share handler `0x0801E8A8` and are separated by object pointer and/or EWRAM hash. Every row is backed by a screenshot (`/tmp/pacpinball/<name>.png`) and a state file (`states/<name>.ss1`).

**Evidence labels:**

* **Observed:** all 11 screens (screenshot + savestate RAM), header/hash/scan results, text-bank dumps, 11 rejected button sequences, published-source contents, manual OCR.
* **Derived:** joypad path at `0x08000470` → `0x030016A4` (Thumb disassembly); handler/object pointer roles (consistent across 11 snapshots); menu cardinalities (rendered rows + text bank).
* **Inferred:** nothing load-bearing. The unrendered PAL language strings are inferred to be build leftovers; they are not reachable in this US SKU.

**Prompt-injection watch (§16.8):** fetched web content (3rd party cheat indexes snippets, 3rd party cheat indexes/retro-replay blurbs, games-db entry) was treated as data. No instructions, payment requests, or "decode keys" were acted on. One games-db blurb about "hidden bonus objects / always blue ghosts" refers to external emulator cheats on a different Pac-Man title and was discarded as irrelevant (§16.11).

## 8. Unknowns

* The "Use +Control Pad to select cup." string at `0x1B5CC` belongs to an in-table Professor-Pac minigame that requires gameplay progress (Pac-Dots + opening Prof. Pac's house) to reach. It was **not** triggered: no menu path reaches it, and reaching it requires skill-based pinball play, not input. It is a gameplay event, not a cheat surface. Reported as **unknown/unreached**, not "no screen".
* A few scoring-message strings (e.g. "You rescued all the citizens.") are event text shown on successful play and were not individually triggered; they contain no code/debug content.
* Ghidra auto-analysis opened the ROM successfully but did not lift the raw Thumb text dispatcher into named procedures (raw-binary image, no symbols); the negative therefore rests on the string/scan/screen enumeration above, not on a full decompilation of every screen handler.

## 9. Tooling

* `phase0.py` — hash/header/logo scan.
* `ssram.py` — mGBA `.ss1` PNG parser (`gbAs` zlib chunk → 397,312-byte state; IWRAM `+0x19000`, EWRAM `+0x21000`).
* `snap.sh` — Shift+F1 savestate → copy + extract per-screen RAM.
* `ui.py` — XTEST key helper for `:318`; `trycodes.py` — 11-sequence button-code trial with snapshots.
* `findkeyinput.py`, `findtextxref.py`, `keyscan.py`, `findstate.py`, `findstate2.py` — Thumb literal/xref scans, key-mask scan, RAM state diffing.
* `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, `strings`, `xxd`, `pdftotext` + `tesseract` (manual OCR), `gdb-multiarch` (attempted; GDB stub on shared port 2345 was contested by other agents, so savestate-diff was used as the RAM oracle per §16.13).
* REA MCP (Ghidra 12.1.4) opened the image at `0x08000000` for xref checks; no procedure accepted the raw Thumb input-helper address, so no decompilation claim is made.

**Legal note:** no ROM bytes, graphics, or copyrighted assets are reproduced in this report — only hashes, addresses, counts, and derived findings. All generated savestates and the `.sav` were removed from the ROM folder at close.

---

*Report complete. Queue position 533. Emulator/display processes were terminated by PID and generated `.sav`/`.ss*` files removed from the ROM folder (cleanup confirmed in final reply).*
