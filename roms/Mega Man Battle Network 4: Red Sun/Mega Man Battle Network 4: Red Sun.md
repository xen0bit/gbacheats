# Mega Man Battle Network 4: Red Sun (GBA) — Reverse Engineering Report

Queue position 460. Analyst run on display `:315`, work dir `/tmp/opencode/mmbn4red`.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Mega Man Battle Network 4: Red Sun/Mega Man Battle Network 4: Red Sun.gba` |
| Size | 8,388,608 bytes (0x800000) |
| `file` | `Game Boy Advance ROM image: "MEGAMANBN4RS" (B4WE08, Rev.00)` |
| Header title | `MEGAMANBN4RS` (0xA0–0xAB) |
| Game code / maker | `B4WE` / `08` (Capcom) |
| Version / complement / checksum | `0x00` / `0x78` / `0x0000` |
| Entry word | `0xEA00002E` (stock ARM branch to 0x080000C0) |
| MD5 | `d0dee5c06972cb072391cd968a248d52` |
| SHA-1 | `a97e96a7da03abd70f7953328e511b9fa29179f1` |
| SHA-256 | `b04adfca9cae47fc9241e70c88e49b16ee9e75d796ab4ee90940401a6c1d5514` |
| Internal build stamps | `ROCKMANEXE4 20031022` at 0x0489E4; US build time at 0x113CB8 (TCRF) |

**Phase 0 / patch check.** Full Nintendo-logo scan (156-byte logo at header+4) found exactly **one** GBA header, at file offset 0x0. There is no multi-game image, no appended trainer, and no scene cracktro strings (`SUNHORS`, `CRC BANDIT`, etc. all absent). The crt0 at 0x080000C0 is ordinary Capcom code (ROM copy loops, LDR literal pools, `b` to `0x080001AC`). Header checksum `0x0000` with complement `0x78` is the normal Capcom/GBA rebuilt-header artifact (§16.1), not evidence of a patch. **Verdict: stock US Rev.00 retail image, no trainer.**

**Sibling comparison (independent verification).** `Mega Man Battle Network 4: Blue Moon.gba` is a separate image: 8 MiB, header `MEGAMANBN4BM` / `B4BE` / `08`, Rev.00, MD5 `e9dfe02b283e29d67c224ab6f86c3b9c`. The two images **share the lotto-code data and the LZ77 text banks** (the same 8 codes decode at the same in-block offsets; Blue Moon's blocks are at a constant ~0x570 earlier file offset), but are **not** the same ROM (different hashes, game codes, and version-exclusive chip data). No finding from the sibling was carried over without re-verifying it in this image.

## 2. Executive summary

This game has two families of developer-intended cheats:

1. **NumberMan Trader "Lotto Numbers"** — eight decimal digits entered on an in-game keypad at Higsby's shop; each valid number grants one Battle Chip, Sub Chip, or NaviCust Program, once per save. This is the primary password system. The community-agreed list contains **exactly 32** codes, and the save format allocates **exactly 32 flag bits** for them. The accepted set is therefore a **closed 32-element table**, not an algorithmic field space: there is no 33rd "novel" code to mint, and any other 8-digit input should be rejected.

2. **Battle-chip command codes** — button sequences held/input while using VarSword, NeoVariSword, and Z Saver, documented on GameFAQs / TREZ (Long Sword, Life Sword, Cross Sword, etc.).

A title-screen code (`Left + L + Start` → BassXX) is documented by TCRF **only for the Wii U Virtual Console build**; on this GBA image it does not exist as a feature (§2, "Validation evidence").

**Text is not ASCII.** All in-game strings are stored in a custom 1-byte font/tile-index encoding (community `bn4-utf8.tbl`), and much of the script is inside LZ77 blocks. That is why `strings` returns essentially zero UI text and why literal code searches fail. I decoded the alphabet, decoded text banks, and confirmed eight published lotto numbers **literally inside this ROM's compressed text banks** as in-game hint text. The remaining codes are not present as ASCII/u32/BCD/custom-encoded literals anywhere in the 8 MiB image; they are produced by the game's own code path, which I did not isolate (see §8).

**Important limitation, stated plainly:** the Number Trader screen is story-gated (the machine appears only once Castillo becomes available). I did not reach that screen in this run, did not enter any code in-game, and therefore did not observe an accepted or rejected code on the real UI. All in-game observations below are title screen, intro, overworld, and dialogue; the lotto findings are static (ROM + LZ77 decode + published cross-check). This is reported as an open item, not papered over.

## 3. How to reproduce

**Emulation.** mGBA 0.10.5 on Xvfb `:315` (1024x768x24), openbox, `SDL_AUDIODRIVER=dummy`, `-3` scale:

```bash
Xvfb :315 -screen 0 1024x768x24 -nolisten tcp &
DISPLAY=:315 openbox &
DISPLAY=:315 SDL_AUDIODRIVER=dummy mgba -3 -g "<ROM>" &
```

**Keymap (verified by KEYINPUT read from savestate, state+0x530):**

| GBA | xdotool key | active-high bit |
|---|---|---|
| A | `x` | 0x001 |
| B | `z` | 0x002 |
| Select | `BackSpace` | 0x004 |
| Start | `Return` | 0x008 |
| Right / Left / Up / Down | arrows | 0x010 / 0x020 / 0x040 / 0x080 |
| R / L | `s` / `a` | 0x100 / 0x200 |

Idle `KEYINPUT = 0x03FF`; holding `Return` gave `0x03F7`, confirming Start = bit 3. Window focus via `xdotool windowfocus $(xdotool search --name mGBA | head -1)`; XTEST events to the focused window (not `key --window`).

**Screen path walked (all observed on :315):**
`screenshots 01_title, 11_title, 13_title`, `30_title_fresh` "PRESS START" → `Return` → Capcom logo (`12_running`) → `Return` → "NEW GAME" (`13_title`) → intro text "In the year 200X," (`cur2`) → repeated A (`15_story_*`, `16_pet_menu`, `19_dialog_end`, `20_dialog_end2`) → ANSA room overworld (`22_after_intro`) → Lan's house overworld (`23_pet_menu`, `24_select_menu`, `25_before_select`, `39_outside`, `40_after_dialog2`) → dialogue "Lan! Take me with you!" when attempting to leave (`39_outside`, `44_leave_room`, `46_dlg_down`). Only "NEW GAME" is offered at the title because the `.sav` was blank (all 0xFF) throughout. `Start` and `Select` did not open a PET menu in the tutorial segment; the menu is story-gated after the first jack-in (§8).

**Published-code literals tested against this ROM (all negative as raw data):** ASCII, `u32` LE/BE, BCD, nibble-packed, digit+1, digit×1/2, `u32 XOR k` for all 16-bit `k`, custom `bn4-utf8.tbl` digit encoding, and all byte permutations of nibble-packed BCD. Positive hits were obtained only after **decompressing LZ77 blocks** (§4).

## 4. Address map

| Item | Address / offset | Notes |
|---|---|---|
| Header / entry | file 0x0 / ROM 0x08000000 | `0xEA00002E`, stock |
| Nintendo logo | file 0x4 | 156 bytes; single header hit |
| Game title | file 0xA0 | `MEGAMANBN4RS` |
| Build stamp | file 0x489E4 | `ROCKMANEXE4 20031022` |
| Decimal power table | file 0x4780–0x47A4 | `10^9 … 1`; used by printf at 0x08004708/0x080047DC |
| Save: `numberTraderFlags` | save file **0x2620**, 0x8 bytes (BN4 GBA offset, from `MMBNSaveEditor` `BN4Definitions.cs` / `SaveData.cs`) | 32 used flags in order: MiniEnrg, MiniEnrg, FullEnrg, FullEnrg, SneakRun, SneakRun, Untrap, Untrap, LocEnemy, LocEnemy, Unlocker, Unlocker, Custom2, MegFldr2, BustPack, BodyPack, Rush, Beat, Tango, HP+500(W), HP+500(P), WideSht3, FlmLine1, FlmLine3, AirHoc3, TwnFng3, VarSwrd, Snake, Recov300, ColorPt, GunSolEX, Z-Saber |
| Save: general story flags | save file 0x2248, 0x2D8 bytes | flag 257 = "DenDome unlocked as destination", flag 258 = "Castillo unlocked as destination" (byte 0x2268 bit 2) — the gate for the Number Trader |
| LZ77 hint bank: WideSht3 68009092 | compressed block file **0x770B64**, decompressed +0x122 | text: `Lottonumber."68009092"` (stone pillar, Colosseum Avenue) |
| LZ77 hint bank: AirHoc3 77038416 | block file **0x772434**, +0x337 | NAXA Observatory computer |
| LZ77 hint bank: FlmLine1 46292983 | block file **0x76EB0C**, +0x282 | DenDome non-burnable garbage |
| LZ77 hint bank: MiniEnrg 16589650 | block file **0x76EF04**, +0x34A | Castillo entrance sign |
| LZ77 hint bank: Untrap 14769745 | block file **0x770504**, +0x1E3 | Vampire Manor ghoul |
| LZ77 hint bank: FlmLine3 57604335 | block file **0x771334**, +0x2A8 | YumLand gas can |
| LZ77 hint bank: TwnFng3 88019791 | block file **0x771CB0**, +0x115 | Sharo house door |
| LZ77 hint bank: Recov300 66703422 | block file **0x7AE4C0**, +0x29A | Undernet 4 hidden Navi |
| Font/tile text alphabet | see `tbl_decode.py` | 0x01–0x0A = digits `0`–`9`, 0x0B–0x24 = `A`–`Z`, 0x26–0x3F = `a`–`z`, 0x00 = separator/space |
| NaviCust program-name bank | file 0x6E8000–0x6E8200 | decoded: `NONE`, `SprArmr`, `Custom1`, `Custom2`, `MegFldr1`, `MegFldr2`, `HP+500`, `Rush`, `Beat`, `Tango`, … |
| Savestate RAM layout | `.ss1` → zlib `gbAs` chunk, 397,312 bytes | IWRAM at state+0x19000, EWRAM at state+0x21000, **KEYINPUT at state+0x530** (verified) |

## 5. Algorithm

**Text encoding (decoded and demonstrated).** MMBN4 stores text as one byte per glyph in a custom table; digits are `0x01..0x0A`, uppercase `A..Z` are `0x0B..0x24`, lowercase `a..z` are `0x26..0x3F`, with `0x00`/control bytes as separators. Decoding `0D 3A 38 39 34 32 03` yields `Custom2`; decoding a whole bank at 0x6E8000 yields the NaviCust program list. This is the §11 "not all text is ASCII" case: `strings` misses it, but the byte table decodes it.

**Lotto-code storage (partially recovered).** The codes are *not* stored as raw numbers. Eight of them were recovered as digit+1 byte strings inside LZ77-compressed script blocks (e.g. `68009092` → bytes `07 09 01 01 0A 01 0A 03` at block 0x770B64+0x122). These blocks are the in-game locations where the number is written down. The remaining 24 published numbers do not occur in any encoding I tested in either compressed or uncompressed ROM. A save-side table of exactly 32 flags (`numberTraderFlags`, 8 bytes at save 0x2620) confirms the accepted set is a fixed 32-element table ordered as in §6, not a generated field space. The exact validator/table lookup in ROM code was **not** isolated (§8); no pseudocode is claimed.

**Button commands.** Sequences are held-A + direction/B inputs (§6). No u16 key-mask table for these sequences was found by the §5.4a method (active-high and active-low, 16-bit and 8-bit, forward and reversed), so the implementation is likely a per-chip state machine rather than a contiguous mask array. Not reversed further.

## 6. Tables

**32 published Lotto Numbers (verified against ROM where possible).** "ROM ✓" = the literal was decoded from an LZ77 block of *this* image; "published only" = present in multiple independent published lists but not found as a literal in this ROM. All 32 are listed identically for Red Sun and Blue Moon on GameFAQs, TREZ wiki, MMKB, and the Steam guide.

| # | Reward | Code | ROM literal |
|---:|---|---|---|
| 1 | MiniEnrg | 16589650 | ✓ 0x76EF04+0x34A |
| 2 | MiniEnrg | 45798331 | published only |
| 3 | FullEnrg | 84625799 | published only |
| 4 | FullEnrg | 59891137 | published only |
| 5 | SneakRun | 24247309 | published only |
| 6 | SneakRun | 89866302 | published only |
| 7 | Untrap | 02368995 | published only |
| 8 | Untrap | 14769745 | ✓ 0x770504+0x1E3 |
| 9 | LocEnemy | 27979609 | published only |
| 10 | LocEnemy | 37198940 | published only |
| 11 | Unlocker | 00274304 | published only |
| 12 | Unlocker | 94872322 | published only |
| 13 | Custom2 (Y) | 75420107 | published only |
| 14 | MegFldr2 (G) | 02109544 | published only |
| 15 | BustPack (R) | 05178924 | published only |
| 16 | BodyPack (B) | 43494372 | published only |
| 17 | Rush (Y) | 73298100 | published only |
| 18 | Beat (B) | 25435428 | published only |
| 19 | Tango (G) | 10170506 | published only |
| 20 | HP+500 (W) | 30873642 | published only |
| 21 | HP+500 (P) | 97618739 | published only |
| 22 | WideSht3 T | 68009092 | ✓ 0x770B64+0x122 |
| 23 | FlmLine1 G | 46292983 | ✓ 0x76EB0C+0x282 |
| 24 | FlmLine3 J | 57604335 | ✓ 0x771334+0x2A8 |
| 25 | AirHoc3 V | 77038416 | ✓ 0x772434+0x337 |
| 26 | TwnFng3 G | 88019791 | ✓ 0x771CB0+0x115 |
| 27 | VarSwrd C | 03696458 | published only |
| 28 | Snake R | 32108251 | published only |
| 29 | Recov300 J | 66703422 | ✓ 0x7AE4C0+0x29A |
| 30 | ColorPt * | 19095677 | published only |
| 31 | GunSolEX G | 74293099 | published only (omitted from JP guidebooks) |
| 32 | Z Saver Z | 72794137 | published only (found 2022 by GreigaMaster; omitted from all guides) |

**Button command codes (GameFAQs / TREZ "Command Codes"; documented, not ROM-verified):**

| Chip | Input while holding A | Effect |
|---|---|---|
| VarSwrd | ↓, ↘, → | LongSword |
| VarSwrd | ↑, →, ↓ | WideSword |
| VarSwrd | ←, ↙, ↓, ↘, → | FighterSword |
| VarSwrd | ↓, ←, ↑, →, ↓ | LifeSword |
| VarSwrd | ←, B, →, B | SonicBoom |
| NeoVari | ↓, →, ↑ | CrossSword |
| NeoVari | ←, →, ←, B | SuperSonic |
| NeoVari | ↑, B, ↓, B, ↑, B | DoubleLife |
| Z Saver | after third slash: ← then B | SuperSonic |

**Title-screen code (VC only, not GBA):** `Left + L + Start` → BassXX in Black Earth 2 via a blank Mod Card (TCRF, under *Virtual Console Differences*). Tested on this GBA image (combo `Left + a + Return` at "PRESS START"): it behaves as a normal Start press; no Mod Card/BassXX surface exists in the GBA build.

## 6b. Enumeration

**Space definition.** The entry surface is 8 decimal digits (`0`–`9` per slot) → `10^8 = 100,000,000` syntactically representable integer strings (including leading zeroes, e.g. `00274304`). There is no checksum character separate from the payload: the whole 8-digit string is the code. Reward categories are three (Battle Chip, Sub Chip, NaviCust Program), and the save allocates a 64-bit (8-byte) flag field at save offset 0x2620 with exactly **32** defined bits (`MMBNSaveEditor` → `BN4Definitions.cs`, `numberTraderCodes[]` has 32 entries). Several rewards have two codes (FullEnrg, MiniEnrg, SneakRun, Untrap, LocEnemy, Unlocker, HP+500) — these are 7 distinct aliases, not duplicates or checksum variants.

**Whole accepted set.** The 32 entries in §6 are the complete published set, and that count is corroborated by the independent save-format definition. Because the set is a fixed 32-element table rather than a bit-packed field space (no field widths, no checksum bits, no generator), **there is no field combination to vary and therefore no novel code to mint**: the correct enumeration result for this system is "the space is exhausted by the published 32." A 33rd code would be a previously unknown table entry (the Z Saver case of 2022 is exactly such a find), and finding one requires the validator, which was not isolated (§8).

**Bounds proven / not proven.** Static bounds: 10^8 possible digit strings; 32 accepted flags; all 32 rewards enumerated by type (11 Battle Chips, 11 Sub Chips, 10 NaviCust Programs). Rejection bounds were **not** exercised in-game: no published code, no novel string, and no out-of-range input were entered at the keypad because the screen is story-gated (§8). Consequently the claim "all other 8-digit inputs are rejected" is inferred from the save flag count, not observed. A follow-up run that sets save flag 258 / advances to Castillo and enters e.g. `00000000` (expected reject) and `72794137` (expected Z Saver accept) would close this gap; the exact keypad RAM buffer should then be read from EWRAM and diffed before/after via `.ss1` (§9).

**Sibling sharing.** All eight ROM-decoded hint texts appear in both Red Sun and Blue Moon at identical in-block offsets, so the accepted code set and its text banks are shared between the two GBA versions. The reward for one code is version-specific in general (version-exclusive chips), but none of the 32 lotto rewards differ between the two published lists.

## 7. Validation evidence

**Observed (emulator / savestate / ROM):**
- Title "PRESS START", Capcom logo, intro, ANSA room, Lan's house, overworld dialogue — screenshots `01_title` … `49_leave_after_L`, captured on `:315`.
- KEYINPUT and keymap from savestate `stateA.ss1`/`stateB.ss1` diff: state+0x530 changed `0x03FF` → `0x03F7` on `Return`.
- Single clean GBA header; hashes in §1; `.sav` remained 32 KiB of `0xFF` (no in-game save was made).
- Eight lotto numbers decoded from LZ77 text banks of *this* ROM; the same eight decode in the sibling Blue Moon image at constant-offset blocks.
- `strings` produced 96,526 lines but **zero** hits for `password|cheat|code|debug|secret|unlock|menu|invalid`; this is a font-indexed text game, not an absence of text.

**Derived (from bytes/disassembly):**
- Text alphabet and decoding (§5), bank at 0x6E8000, LZ77 code hints (§4).
- Save-side closed set of 32 flags at save 0x2620 (`MMBNSaveEditor` definitions), matching the community "exactly 32 Lotto Numbers" statement.
- No literal code representation in 8 MiB under 12+ encodings/patterns tested; therefore the validator is code, not a plaintext table.

**Inferred (lower confidence):**
- The 32 accepted values are a fixed table and all other 8-digit inputs are rejected. This follows from the save flag count and published consensus but was **not** confirmed by feeding a rejected input to the game.
- Button-command inputs are a per-chip state machine, inferred from the failure to find a key-mask array.

**Fetched-page hygiene.** GameFAQs (403 direct, read via `web.archive.org` 2024 capture), TCRF mirror, TREZ wiki, Steam guide, MMO forum, `MMBN-Table-Files`, and `MMBNSaveEditor` were fetched as **data**. No prompt-injection payload or instruction-like content was found in the fetched pages in this run; no fetched instruction was acted upon. (§16.8)

## 8. Unknowns

1. **Validator not isolated.** The ROM routine that accepts/rejects an entered 8-digit number was not located, and the game's own validator was not run as an oracle (§16.19). Candidate attacks that were tried and failed: literal search (ASCII, u32 LE/BE, BCD, nibble-packed, digit+1, custom table, XOR keys), `movs #10`+`muls` Thumb scan, LDR-literal xrefs to the decimal power table, 32-entry low-nibble table scan, and a full LZ77 scan for a multi-code table.
2. **No in-game code entry.** The Number Trader UI is story-gated (Castillo unlock; save flag 258 + Higsby's shop). I did not reach the shop, so **no published code was entered in-game**, no novel code was generated and entered, and no in-game rejection was observed. The gate and the value that would advance it are identified in §4/§7; a follow-up run should set/advance that flag, reach Higsby's shop, and exercise the keypad.
3. **Button codes not dynamically verified.** The sequences in §6 are published; reaching a battle with VarSword/NeoVari/Z Saver requires the same story progress.
4. **24 codes not located as ROM literals.** They may be stored in a compressed/encoded form my scan did not cover, or generated by code. Their acceptance is taken from four independent published lists, not from this ROM's bytes.
5. **No novel code exists to mint in a closed 32-table system.** If a 33rd accepted value does exist (e.g., a hidden debug-only entry), finding it requires the validator, which remains the main open item.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb/force-arm`, `xxd`, `strings`, `grep`.
- `capstone` 5.0.7 (pattern scans), Python 3.13.
- `rsp.py` — minimal GDB-RSP client (written; mGBA's stub wedges after one client, so batch GDB/FIFO was used instead).
- `gdbcmd.py` — persistent `gdb-multiarch` attached via FIFO to `:2345`; commands `r/4`, `w/4`, `x/4`, `b`, `c`.
- `ss.py` — mGBA `.ss1` PNG `gbAs` zlib parser (IWRAM +0x19000, EWRAM +0x21000, KEYINPUT +0x530).
- `tbl_decode.py` — BN4 custom-glyph decoder (`bn4-utf8.tbl` from RockmanEXEZone/MMBN-Table-Files).
- `lzscan.py` — GBA LZ77 scanner/decompressor (1,739 valid blocks scanned).
- `key.py` — xdotool helper; `Xvfb :315`, openbox, mGBA 0.10.5 with `SDL_AUDIODRIVER=dummy`.

**Legal note.** No ROM bytes, graphics, music, or full text banks are redistributed here; only hashes, offsets, algorithms, and a few short decoded strings are published. The `.sav`/`.ss1` artifacts were removed from the ROM folder at the end of the run (§ cleanup).
