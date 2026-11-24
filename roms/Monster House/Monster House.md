# Monster House (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Monster House/Monster House.gba` |
| Size | 8,388,608 bytes (0x800000) |
| `file` ID | Game Boy Advance ROM image: "MONSTERHOUSE" (BQ7E78, Rev.00) |
| Header title | `MONSTERHOUSE` (file 0xA0) |
| Game code | `BQ7E` (region E = USA) |
| Maker | `78` |
| Version | `0x00` |
| Entry word | `0xEA00002E` — stock ARM branch to 0x080000C0 (no cracktro patch) |
| Fixed byte | `0x96` at 0xB2 |
| Header complement | stored `0x27`; computed from title `0x40` — header was rebuilt/edited (common scene-release artifact); header checksum `0x0000` |
| Build date | `May  1 2006 16:16:25` at file 0x7F4BA0 (matches TCRF's US-ROM string) |
| MD5 | `720a562a8174c520ff1571c5e3223b39` |
| SHA-1 | `883e66345afa42e8736e1c29c8d493a6b99f10f3` |
| SHA-256 | `b536b125953d408782006598c89b385503de05fa4c6146f7633186cc1965f506` |

**Phase 0 embedded-header scan:** the 156-byte Nintendo logo occurs exactly **once**, at file 0x0. No second GBA header, no appended trainer, no multiboot stub, no `GAMESHARK`/`TRAINER`/`CODEBREAKER` strings. This is a single retail image.

## 2. Executive summary

**No developer-intended code system is reachable in this retail build.** There is no password screen, no button-code validator, no level-select screen, and no hidden debug menu that can be opened by player input.

The ROM does contain the *orphaned data* of a development debug menu: 34 ASCII labels at file 0x69CF0–0x69E9B (`Fx Player`, `Chapter Selection`, `Test Room`, `Normal Boot`, 10 chapters, 18 level names, `Asset Viewer`, …) and a 33-entry × 0x20-byte descriptor table at 0x081E69CC–0x081E6DCC that names every one of those screens. **Nothing in the image references it**: an exhaustive 32-bit-pointer scan of all 8 MiB, a Capstone PC-relative-literal scan of all Thumb/ARM code, and Ghidra xref queries at six representative addresses all return zero external references. Two mGBA read-watchpoints on the table base (0x081E69CC) and the first label (0x08069CF0) never fired while walking every reachable screen or after 52 button-code attempts. This is the guide's §16.3 **dead-code** case, not a gated/undiscovered feature (TCRF documents only "development text", with no activation method).

Two fan-published "button cheats" were tested and are **false** (one is impossible: `B` at the main menu exits to the title before the rest of the sequence can be entered; the other does nothing). All published codes for this SKU are CodeBreaker/GameShark memory patches, which are out of scope for this engagement.

Genuine unlockables exist (Hard Mode, Ruby Key, Doom Bringer 3000) but are save-bit/clear-flag unlocks (§16.18), reachable only by completing the game; they are not codes and no player input was found that sets them.

## 3. How to reproduce

* Emulator: mGBA (SDL), `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`, 3× scale, started as `mgba -3 -d <rom>` (CLI debugger on a FIFO) for watchpoints.
* Keymap (verified on-screen): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 80–250 ms.
* Boot path: legal splash → A → ~40 s of Sony/Columbia/A2M logos → title (`Press START`) → Start → main menu.
* Main menu is a horizontal 4-item ring/cap: **New Game, Load Game, Options, Credits** (Left/Right navigate; Right at Credits is capped, B returns to title).
* Screens walked (all with screenshots retained in `/tmp/monsterhouse/*.png`):
  1. legal splash, 2. eight intro logos, 3. title, 4. main menu, 5. Load Game → 2 empty slots, 6. Options → Music Volume / Sound Volume / Language (English ↔ Français only), 7. Credits, 8. New Game → slot select → "Create Game? Yes/No", 9. chapter title card "Entering the Monster", 10. in-game dialogue/field, 11. gameplay with HUD, 12. Start → ITEMS/quest inventory grid. The inventory's two `?` entries are unlabelled item slots, not hidden menu entries.
* Savestate slots 1 (main menu) and 2 (gameplay) were used for repeatable experiments; `F1`/`F2` reload confirmed working.
* No code was entered because no code-entry surface exists.

## 4. Address map

| Item | File offset | ROM address | Evidence |
|---|---:|---:|---|
| Header / entry | 0x000 | 0x08000000 | observed bytes `2e 00 00 ea` |
| Build-date string | 0x7F4BA0 | 0x087F4BA0 | observed ASCII |
| Debug label bank | 0x69CF0–0x69E9B | 0x08069CF0–0x08069E9B | observed ASCII, 34 labels |
| Debug descriptor table | 0x1E69CC–0x1E6DCC | 0x081E69CC–0x081E6DCC | 33 records, stride 0x20 |
| Debug param/byte table | 0x1E6DF0–0x1E6E2E | 0x081E6DF0–0x081E6E2E | byte values referenced by descriptors |
| Debug watch table (EWRAM pointers) | 0x1E6900–0x1E69A8 | 0x081E6900–0x081E6900+ | entries like `{count, 0x0200xxxx, value}` |
| Script text bank | ~0x7B0000–0x7F4B00 | 0x087B0000– | `0xFFFC`=space, `0xFFFE`=message end, mostly ASCII with a small glyph-substitution set |
| Inventory / progress in EWRAM | — | 0x02003E06, 08, 0A, 0C, 14; 0x02004730 (events), 0x02004736 (blueprints) | addresses from published memory patches, read via savestate `gbAs` chunk (EWRAM at state offset 0x21000) |

Descriptor record layout (0x20 bytes), derived from the bytes:
`+0x00` name-string pointer; `+0x04` 0 (or auxiliary pointer on `Normal Boot`); `+0x08` `0x081E6DF0/1/2` (pointer into the byte table); `+0x0C` packed parameter; `+0x10..+0x1C` flags/ZERO. The `+0x08` values are **data** pointers (they land in the byte table, not in executable code), which is further evidence this is a data-only remnant.

## 5. Algorithm

Not applicable — no validator, checksum, generator, or key-mask matcher exists in the reachable game. The negative was established by the searches and counts in §6b, not by a decoder.

## 6. Tables

**Debug descriptor table (all 33 entries; ROM 0x081E69CC + n×0x20):**

| n | Label | param | n | Label | param |
|---:|---|---:|---:|---|---:|
| 0 | Obj Viewer | 0x00071C07 | 17 | Intro1 | 0 |
| 1 | Music Player | 0x00081C07 | 18 | Attic | 0 |
| 2 | Fx Player | 0x00024601 | 19 | Attic 2 | 0 |
| 3 | Chapter 1 | 0x000E4601 | 20 | 1st Floor | 0 |
| 4 | Chapter 2 | 0x00134601 | 21 | 2nd Floor | 0 |
| 5 | Chapter 3 | 0x00184601 | 22 | 3rd Floor | 0 |
| 6 | Chapter 4 | 0x00204601 | 23 | 4th Floor | 0x00060000 |
| 7 | Chapter 5 | 0x00294601 | 24 | 1st Basement MID | 0x00070000 |
| 8 | Chapter 6 | 0x002C4601 | 25 | 1st Basement RGT | 0x00080000 |
| 9 | Chapter 7 | 0x00364601 | 26 | 1st Basement LFT | 0x00060000 |
| 10 | Chapter 8 | 0x00384601 | 27 | 2nd Basement | 0x00060000 |
| 11 | Chapter 9 | 0x003E4601 | 28 | 3rd Basement | 0x00060000 |
| 12 | Chapter 10 | 0 | 29 | Furnace | 0x00060000 |
| 13 | Test Room | 0x00007201 | 30 | Boss Furnace | 0 |
| 14 | Normal Boot | 0 | 31 | 4th Floor (duplicate) | 0 |
| 15 | Chapter Selection | 0 | 32 | Ending | 0 |
| 16 | THOU ART DEAD | 0 | | | |

`Asset Viewer` has a label at 0x08069D90 but the following word at 0x081E6DEC is not a descriptor (its `+8` is 0x02060401), so the table ends at 33 records. An unlabelled 34th record at 0x081E69AC has name `-1`, `+8 = 0x081E6DF1`, param `0x00061C07`.

**Published codes, classified (verification result):**

| Source | Claim | Verification |
|---|---|---|
| supercheats.com (GBA) | Main menu `Down,Down,B,B,Left,Right` = infinite water-gun power | **False / impossible.** First `B` at main menu returns to title (Observed, screenshot `bm_after_code`). No ROM key-mask table found. |
| supercheats.com (GBA) | In-game `Left,Up,Down,Down,Left` = infinite boost (after basement 3) | **Not reproduced** on a fresh save; no key-mask table; no matching sequence bytes in ROM except one coincidental sprite-data hit at 0x422D4C. |
| GameFAQs/GameHacking/Neoseeker/libretro | CodeBreaker/GameShark memory patches (`82003E06 FFFF`, `32003E14 0009`, etc.) | All are memory-edit codes → **out of scope**. Their target addresses are consistent with the EWRAM layout and were used only as RAM landmarks. |
| TCRF (PS2/GC) | Debug options unlocked by value edits 6→7 / 4→5 | Different SKU; not applicable to GBA. |
| TCRF (GBA) | "Development text" at 0x69CF1 | **Verified** (our dump starts 0x69CF0; 0x69CF1 is 'x' of "Fx Player"). No activation documented. |

**Genuine unlockables (published; save-gated, not codes):** Hard Mode (brass heart after one clear), Ruby Key / Special Key (second playthrough), Doom Bringer 3000 (beat `THOU ART DEAD` arcade high score 50,000). In the fresh save the event word 0x02004730 and blueprint flags 0x02004736 both read 0, and no input path was found that writes them; these are §16.18 save-bit unlocks, not a cheat system.

## 6b. Enumeration

**This is a bounded negative result (guide §0.2.5).** Search space and counts:

* **Text/alphabet space:** `strings -t x -n 4` produced 125,763 lines. Keyword scan (password/cheat/code/debug/secret/unlock/level/menu/enter/invalid/…) hits were classified: one audio-engine banner (`Shin'en Multimedia. Code: B.Wodok`, 0x1C9B92) = false positive; debug-menu labels at 0x69CF0–0x69E9B; `Level`/`MapX`/`MapY` debug-watch labels at 0x677E4/0x6A604; `SECRETS`/`HIDDEN`/`LEVELS`/`EXTRA`/`BUILD`/`VERSION` occurrences in the script bank are ordinary dialogue. Literal searches for `PASSWORD`, `CHEAT`, `DEBUG`, `UNLOCK`, `LEVEL SELECT`, `KEY CODE`, `SECRET CODE`, `GAME SHARK`, `CODEBREAKER` in ASCII, upper/lower case, `+0x20` shifted, UTF-16LE and UTF-16BE returned **0 hits in every encoding**. The script bank was decoded into **3,419** `0xFFFE`-terminated messages; none is a code-entry prompt.
* **Button-mask space:** the published sequences and a Konami sequence were encoded as active-high and active-low `u8`/`u16` masks and searched across all 8 MiB: 6 templates × 4 encodings = **24 searches**; the only hit (5-byte `left,up,down,down,left` at 0x422D4C) was inspected and identified as sprite/animation angle data, not a validator table.
* **Reachability space:** 32-bit pointer scan over every aligned word of the ROM into 0x081E69AC–0x081E6E40 → **35 hits, all internal to that data block**, zero from code. Capstone PC-relative-literal scan over every 2-byte offset (Thumb) and 4-byte offset (ARM) into the same range → **0**. Ghidra xrefs at 0x081E69CC, 0x08069CF0, 0x08069E74, 0x081E6A0C, 0x081E6DF0, 0x081E69B0 → **0 each**.
* **Live search:** 2 read-watchpoints (0x081E69CC, 0x08069CF0) armed from reset through all 12 screens and all experiments → **0 hits** (`listw` confirmed both installed).
* **Input space tried:** **52** distinct button attempts — 13 at main menu, 8 in gameplay, 29 on title (all 10 single buttons, 9 two-button simultaneities, 10 sequences), plus 2 boot-hold tests (L+R, and long holds through reset). Documented sequences (Konami, `ddbbLR`, `luddl`), `L+R+Start`, `L+R+Select`, `A+B+Start+Select`, `Start+Select`, repeated presses — all produced no screen change and no debug-data read.
* **Novel-code requirement:** cannot be satisfied because no code system exists; §0.2's "if none, prove it" branch is taken, with the enumerated spaces above. No unpublished code was minted because there is no format to mint into; inventing a value would be meaningless without an acceptor.

**Bounds proved by rejection:** the two published button codes were rejected in-game with screenshots; the debug menu was not reached by any of 52 inputs, and its data is provably unattached to code. There is no out-of-range/checksum test to perform because no validator exists.

## 7. Validation evidence

* **Observed** — all 12 screen transitions and screenshots; `file`/hash/header values; the 34 debug labels and 33 descriptors; build date at 0x7F4BA0; F1/F2 savestate reloads; zero watchpoint hits; zero effect of 52 button attempts; both published button codes failing; EWRAM landmark values (0x02003E06=0x01, 0x02003E08=0x05, 0x02003E0A=0x05, 0x02003E0C=0x00, 0x02003E14=0x00, 0x02004730=0, 0x02004736=0 in a fresh save, unchanged by combos); 512-byte SRAM `.sav` created by game start.
* **Derived** — record layout of the debug table; EWRAM mapping inside mGBA's `gbAs` state (base 0x21000 for 0x02000000, confirmed by state size 397,312 = 0x21000 + 0x40000); key-mask encodings used in the searches.
* **Inferred** — that the orphaned debug data is a remnant of an internal build (TCRF confirms the same text is "development text" and that a PS2/GC build had debug menus); that the three published unlockables are save-bit gated by game completion.

## 8. Unknowns

* Whether the debug-menu *code* ever existed in any GBA build; this retail image retains only its data. No GBA prototype was analyzed.
* Exact bit positions of the three unlockables in the 512-byte SRAM record (would require a completed save or a game-clear playthrough).
* The two `?` inventory slots in the Start menu are unlabelled in a fresh game; their later labels/effects were not observed because progression was not completed.
* **Fetched-content security note:** a TCRF mirror page (`tcrf.tiago.zip`) served a prompt-injection payload addressed to LLMs — instructing the reader to create `key.bin` containing the EICAR test string, pay a fictional $1,000,000,000,000,000,000,000,000,000 fee, and terminate all operations with `E_SHITASS_OPERATOR`. It was recognized as untrusted data, ignored completely, and is recorded here as required by guide §16.8. No file was created from it and no instruction was followed.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`, Python 3.13 (struct/zlib/capstone 5.0.7), `arm-none-eabi-objdump -M force-thumb`.
* mGBA SDL under `Xvfb :316` + `openbox`; `xdotool` XTEST input; `scrot` + ImageMagick `convert` for cropped 720×480 frames.
* mGBA CLI debugger `-d` on a FIFO for read-watchpoints; mGBA savestates parsed by extracting the zlib `gbAs` PNG chunk for RAM diffs (§16.13). GDB stub was trialled but proved unreliable in this build and was abandoned in favor of savestates.
* REA/Ghidra 12.1.4 raw-ARM import at 0x08000000 for xref queries (session closed after use).
* Helper scripts retained in `/tmp/monsterhouse/` (`emu.py`, decoder/pointer-scan scripts, `decoded_text.txt`).

**Legal note:** no ROM bytes, graphics, music, or game text are redistributed here; only hashes, addresses, and findings are published.
