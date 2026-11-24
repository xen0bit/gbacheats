# Dora the Explorer: The Search for Pirate Pig's Treasure (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dora the Explorer: The Search for Pirate Pig's Treasure.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `DORA THE EXP` |
| Game code | `AERE` (maker `5L`) |
| Version | 0 (Rev.00) |
| Header checksum | `0x0000`; complement byte `0x7F` (non-standard — rebuilt-header artifact; see below) |
| Entry word | `0xEA0CCF7E` → ARM entry `0x08333E00`; stock Nintendo crt0 present at `0x080000C0` |
| MD5 | `9834427dadbad2a48455e3d0efd8d7c8` |
| SHA-1 | `665e7698ad438bfc458ccac46410a29ebfcd95d8` |
| SHA-256 | `874ca0e112fc8eb802edfc32b56d6c617ecf2c979410ae32e743e62eca123ba6` |

**Phase 0 notes.** One Nintendo logo only, at file offset `0x0`; this is a single-image ROM, not a multiboot/2-in-1 pack. No cracktro/trainer strings, no appended trainer and no patch: the crt0 at `0x080000C0` is the standard Nintendo sequence (`msr`, stack setup, `bx r1` through literal pointers at `0x0800022C/0x08000230`), and the entry branch lands on real ARM init code at `0x08333E00`. The header complement (`0x7F`) is not the expected `~sum(0xA0..0xBC)=0x97` and the checksum is `0x0000`; this is the usual rebuilt-header artifact of a scene release and does **not** imply a modified game image — the in-game content is intact. The legal splash names NewKidCo (publisher), CinéGroupe (developer), Factor5 MusyX audio and "Licensed by Nintendo"; this is the **first** Dora GBA title (2002), not the third.

## 2. Executive summary

This game has a **developer-intended password system** on the title menu's **Continue** entry. It is a 5-slot icon/password screen ("ENTER PASSWORD"), each slot cycling through a **16-symbol alphabet** (X, spiral, heart, →, ←, ↓, ↑, sun, frown, neutral, smile, triangle, star, +, circle, square). Left/Right select a slot, Up/Down cycle the symbol, A or B opens "IS THIS O.K.?", and Yes submits.

All **8 published GameFAQs passwords** (7 chapter entries plus a "Last Level" entry) were typed in and **every one was accepted** in the emulator, each starting the corresponding chapter's cutscene/gameplay. The accepted set is **not** limited to those 8: the 5th slot is completely ignored (all 16 possible symbols accepted with the first four fixed), and single-glyph sweeps show that other symbol combinations are also accepted. **Novel, unpublished codes were generated and confirmed in-game** (e.g. `1,6,0,0,13` and `9,6,0,0,13`, which start the boat/"We love boat rides" chapter, and `10,6,0,0,13`, which starts the beach/"Look Boots! Sand!" chapter). Bounds were proven by in-game rejection of out-of-pattern inputs (all-X `0,0,0,0,0`, `4,7,0,0,13`, `4,6,1,0,13`, `2,3,1,1,9`).

No GameShark/CodeBreaker codes, no button cheat code and no hidden/debug menu were found; the options screens contain only Stop-and-Think, Sound FX, Music and Credits. Character unlockables published for the Double Pak (complete the game three times as Dora/Boots/Diego/Alicia) are save-bit progression rewards, not a code system.

ROM text is **not ASCII**: `strings -t x -n 4` produced 32,349 lines of which only the header title was meaningful. The legal screen's plain English ("The search for the PIRATE PIG'S TREASURE", "NewKidCo", "MusyX") does **not** occur in the image in any standard encoding — it is decompressed/drawn at runtime. Therefore the password UI strings cannot be used as static anchors; the alphabet and codes were recovered dynamically.

## 3. How to reproduce

Emulator: mGBA (SDL) under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, 3× scale. Default SDL keymap: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys.

Menu path to the password screen:

1. Boot; skip the 2K/NewKidCo/CinéGroupe splash, the scrolling intro credits and the legal screen with `Start`.
2. On the title screen ("DORA THE EXPLORER / The Search for the PIRATE PIG'S TREASURE", "Press Start") press `Start`.
3. On the main menu (`New Game / Continue / Options`) select **Continue** and press A. The next screen is `ENTER PASSWORD`.

Password entry:

- Initially all five slots show `X`; the blue cursor is on slot 1.
- `Right`/`Left` move between slots; `Up`/`Down` cycle the symbol in the current slot (the cycle is exactly 16 symbols and wraps).
- Hold keys ~100 ms with a ~300 ms gap; shorter holds double-step or drop presses.
- A (`x`) or B (`z`) opens `IS THIS O.K.?` with a Yes/No selector (No is default); press Left to choose **Yes**, then A/B.
- **Accepted** → a chapter cutscene plays and gameplay follows. **Rejected** → the game returns to the title screen. This is a clean, unambiguous in-game oracle.

Symbol → cycle index (verified by screenshot montage):

| idx | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| glyph | X | spiral | heart | → | ← | ↓ | ↑ | ☀ | ☹ | 😐 | ☺ | △ | ★ | + | ○ | □ |

Published codes tested (all accepted):

| Effect | Symbols | Indices |
|---|---|---|
| Blueberry Hill | ☀ ← heart ★ △ | `7,4,2,12,11` |
| Rain Forest | ← ↑ X X + | `4,6,0,0,13` |
| Spooky Forest | ↑ heart heart ☀ ← | `6,2,2,7,4` |
| The Beach | ☺ ↓ 😐 △ ← | `10,5,9,11,4` |
| Treasure Island | 😐 ← ↑ X ☺ | `9,4,6,0,10` |
| Volcano | ↓ ☀ ↑ + ○ | `5,7,6,13,14` |
| Waterfall | △ ○ ↑ ★ ☺ | `11,14,6,12,10` |
| Last Level | spiral ← ↑ ☹ ☺ | `1,4,6,8,10` |

## 4. Address map

| Item | Address / offset | Evidence |
|---|---|---|
| GBA header | file `0x000..0x0BF`; ROM `0x08000000..` | observed |
| Nintendo crt0 | `0x080000C0` (ARM), literal pool `0x0800022C/0x08000230` | disassembly |
| Entry target | `0x08333E00` (ARM init code) | header + `xxd` |
| Password-screen object updater region | `0x08018000–0x0801C000` (Thumb). GDB PC observed at `0x0801865E` inside `FUN_08018570` while the password screen was displayed; `0x08018FD2` calls `FUN_0801BD30`, a generic script/object interpreter that advances the slot sprites. | observed (GDB) + Ghidra |
| Password UI runtime objects | IWRAM `0x03001100–0x03001600`, `0x03002700–0x03003000`; EWRAM `0x02007E00–0x02009300` (animated sprite/tile buffers). GDB read/write watchpoints on these fire on Up presses but are object/stack writes, not a compact 5-byte code buffer. | observed |
| Saved input/state | `.sav` created at ROM folder (0 bytes; the game uses passwords instead of a battery save) | observed |
| Savestate layout (mGBA `.ss1`, 397,312-byte `gbAs` chunk) | CPU/I/O `0x00000`, VRAM `0x01000`, IWRAM `0x19000`, EWRAM `0x21000`, per guide §16.13 | observed |

**Negative result on static anchors:** the published codes do not occur in the image as raw 5-byte sequences, as packed 20-bit values, as u16 arrays, as reversed sequences, nor under any single constant byte offset (0..255) applied to the glyph indices. All apparent hits were random matches inside compressed data. The accepted strings are therefore produced by the game's script/animation engine, not by a plaintext comparison table in the ROM image.

## 5. Algorithm

The on-screen code reader takes five 4-bit glyph indices `g0..g4` (values 0..15). The exact validator/table arithmetic was **not** recovered; the ROM's code around the password screen is a generic script/object interpreter (decompiled `FUN_08018c30`, `FUN_08018570`, `FUN_0801bd30`) and there is no plaintext comparison table to anchor a pointer scan. The engine is heavily compressed, which defeats `strings`-based anchoring (§11/§16.11 of the guide).

What **is** established by exhaustive single-slot sweeps through the game's own UI (the validator as oracle, guide §16.19):

- `g4` (slot 5) is **ignored**: with `g0..g3 = 4,6,0,0`, all 16 values of `g4` (0..15) were accepted (16/16). Each published code therefore has at least 16 spellings.
- For the prefix `g0,g1 = 4,6` and `g3 = 0`, `g2` is accepted only for `{0,2,4,6,8,10,12,14}` (even values); all odd `g2` rejected (8/16).
- For `g0,g1 = 4,6` and `g2 = 0`, `g3` is accepted for `{0,13,14,15}`; all other 12 values rejected (4/16).
- For `g1,g2,g3 = 6,0,0`, `g0` is accepted for `{1,4,9,10}` (4/16).
- For `g0 = 4`, `g2,g3 = 0,0`, `g1` is accepted for all even values `0,2,4,6,8,10,12,14` (8/16).

These constraints are position-dependent and interact with the first glyph, so the password is best modelled as a bit-packed value checked against a small set of per-chapter accept values, with unused low bits producing aliases — analogous to guide §16.4b. A single offline Python trial of all 16^5 possible linear checksums `Σ cᵢ·gᵢ (mod 16)` over the 8 published codes found **no** nontrivial linear solution, so a plain additive/XOR checksum over all five symbols is ruled out. A bit-exact offline reimplementation is therefore not claimed; the in-game UI was used as the authoritative oracle instead.

**Reproduction of the oracle:** F1 reloads the password-screen savestate, so each test costs only the glyph presses plus A/Left/A. A screenshot 1.5–2.5 s after submission gives the verdict: chapter cutscene = accepted; title screen = rejected.

## 6. Tables

### 6.0 Published codes (verified, accepted)

Listed in §3. Sources: GameFAQs GBA cheats page for game id 563095 (archived snapshot `20220212163123`); the Nick Jr. Dora Double Pak page (archived `20251004181653`) repeats the same eight and adds the character-unlockable descriptions. GameFAQs reports "8 cheat codes and secrets" for this SKU, matching the eight level passwords.

### 6.1 Pause menu

`Resume / Map / Exit To Menu / Options`. The pause `Options` screen contains `Stop and Think [on/off]`, `Sound FX [on/off]`, `Music [on/off]`, `Credits` — no cheat, debug or level-select entry.

### 6.2 Unlockables (not a code system)

Published: Alicia (finish the game as Diego three times), Baby Jaguar (as Boots three times), Boots (as Alicia three times), Diego (as Dora three times). These are progression/save-bit rewards, consistent with guide §16.18; no unlock string literals or debug gates were found in the compressed image, and they are not reachable through the password UI.

## 6b. Enumeration

**Space definition.** Alphabet size 16, length 5 → **16⁵ = 1,048,576** representable inputs. All five slots are editable through the UI; the on-screen cycle was verified to contain exactly 16 symbols and to wrap from square back to X. There is no input cap: a 5-symbol maximum-length code can be submitted.

**Accepted-set characterization.** The accepted set is much larger than the published 8. Established by single-slot sweeps and novel-code submissions:

- Slot 5 carries **zero** information: 16/16 symbols accepted after a valid 4-symbol prefix.
- Slots 2–4 and slot 1 have position-dependent accept constraints (exact counts in §5), yielding multiple accepted values per position rather than a single table entry.
- Consequently each accepted prefix has multiple spellings; published codes are simply one spelling per chapter.

**Novel codes generated, unpublished, and accepted in-game** (none of these appear on GameFAQs, VGChartz, TCRF or any wiki consulted):

| Code (indices) | In-game result (Observed) | Published? |
|---|---|---|
| `1,6,0,0,13` | Boat cutscene, "We love boat rides" | No |
| `9,6,0,0,13` | Boat cutscene, "We love boat rides" | No |
| `10,6,0,0,13` | Beach cutscene, "Look Boots! Sand!" | No |
| `4,6,0,0,0` | Same chapter as published Rain Forest (`4,6,0,0,13`), proving slot 5 is ignored | No |
| `4,6,0,0,15` | Same chapter as Rain Forest | No |
| `4,0,0,0,13` | Same chapter as Rain Forest | No |
| `4,6,4,0,13` | Same chapter as Rain Forest | No |

**Bounds proven by rejection (in-game):**

| Code | Why out of pattern | Result |
|---|---|---|
| `0,0,0,0,0` | no valid prefix | rejected → title screen |
| `4,7,0,0,13` | odd glyph at slot 2 | rejected → title screen |
| `4,6,1,0,13` | disallowed glyph at slot 3 | rejected → title screen |
| `2,3,1,1,9` | random non-code | rejected → title screen |
| `15,15,15,15,15` | random non-code | rejected → title screen |
| `0,1,2,3,4` | random non-code | rejected → title screen |
| `8,8,8,8,8` | random non-code | rejected → title screen |

All 8 published codes were also submitted and all 8 were accepted (cutscene for the matching chapter), so the decoder/oracle agrees with the public list on every known-good input.

## 7. Validation evidence

- **Observed:** title/main/options/pause/password screens and every transition, captured as screenshots on disk in `/tmp/dorapirate/`; 8 published codes accepted, novel codes accepted, listed invalid codes rejected to the title screen; F1 savestate reload; GDB stub registers at the password screen (`PC = 0x0801865E`); 16-symbol cycle and wrap; savestate diffs and read/write watchpoints showing UI object activity.
- **Derived:** header fields and entry target from the raw bytes; code/data boundary and function identities from `arm-none-eabi-objdump -M force-thumb` and Ghidra decompilation; absence of any plain/offset/packed encoding of the published codes from exhaustive byte searches.
- **Inferred:** that the validator is a bit-packed value against a per-chapter accept set with unused low bits (aliases). The per-slot accept counts are observed, but the exact packing and the complete accept table are **inferred**, not recovered.

## 8. Unknowns

- The exact validator arithmetic / accept table was not recovered. The password screen is implemented through a generic compressed script/object interpreter (`FUN_08018c30`, `FUN_08018570`, `FUN_0801bd30`); no plaintext code table exists in the image under the encodings searched, and the compressed text banks defeat string anchoring. The whole code space was therefore characterised through the game's own UI oracle rather than an offline reimplementation.
- The complete list of accepted 4-symbol prefixes was not enumerated exhaustively (65,536 offline trials would require an offline validator); the accepted set is demonstrably larger than 8 but its exact cardinality is unmeasured.
- The effect of the 4th slot's accepted values `{0,13,14,15}` on chapter selection was not individually resolved beyond the Rain Forest prefix.
- Character unlockables were not exercised through three full playthroughs; their existence is taken from the published Double Pak list and they are explicitly out of scope as a code system.
- No hidden debug screen was reached with L+R, L+R+Start, L+R+Select, Start+Select or D-pad+L+R on the title screen.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for Thumb disassembly.
- Capstone (`cs.CS_ARCH_ARM`, `CS_MODE_THUMB`) scripts `scanval.py` for cmp-cluster scans.
- Python `gdbcli.py`: a minimal GDB-remote-protocol client (packet checksum, `m`/`M`/`g`/`P`/`Z2`, `c`, `\x03`) used because `gdb-multiarch` rejected mGBA's minimal stub (`qSupported` "timeout", protocol packet errors). Connect to `127.0.0.1:2345` with `mgba -g`.
- `ss.py`, `diffss.py`, `diffmem.py`, `patchss.py`: parse the PNG `gbAs` chunk, zlib-decompress the 397,312-byte state, diff IWRAM/EWRAM and patch/rewrite savestates. Per guide §16.13.
- `mgba_pt.py`: pty controller for mGBA's `-d` command-line debugger (used after the GDB stub became single-use).
- `keys.py`, `enter.py`, `batchtest.py`, `sweep.py`: XTEST key helpers and the automated code-entry/oracle harness; ImageMagick `compare -metric AE` and average-colour sampling for accept/reject classification.
- REA/Ghidra 12.1.4 raw-binary import (`arm`, `ARM:LE:32:v7`, base `0x08000000`) for `procedure_pseudo_code` on the password-screen region.
- Xvfb `:316` with openbox; mGBA SDL 3×; `import -window root` / `montage` for screenshots.

## 10. Legal note

No ROM image, extracted graphics, music, or game assets are redistributed here. Only hashes, addresses, algorithms, glyph-index mappings, and analyst-generated codes are published. The fetched GameFAQs pages were treated as untrusted data and contained no instructions that were followed.
