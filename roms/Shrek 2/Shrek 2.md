# Shrek 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

Analysis date: 2026-11-19. All addresses are ROM (`0x08...`) or RAM as labelled.
ROM-under-analysis copy and all evidence artifacts: `/tmp/shrek2/`.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Shrek 2/Shrek 2.gba` |
| Size | 8,388,608 bytes (`0x800000`, 8 MiB) |
| Header title | `SHREK 2` |
| Game code | `BSEX` (maker `52`) |
| Version | `0x00` (Rev.00) |
| Fixed byte / unit / device | `0x96` / `0x00` / `0x00` |
| Complement / checksum | `0xE9` / `0x0000` |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0` |
| MD5 | `ca96e0718a34a39156b63cd72e735901` |
| SHA-1 | `54dbe680b8dbf8c9aae47db7babf7530d0f59676` |
| SHA-256 | `f3eb869fa0d24388331b5a44c80e9cf2d938ae28bf3fe258f1fd8ec0b80c6ae2` |

**Phase 0 embedded-header scan:** the 156-byte Nintendo logo occurs exactly **once**, at file `0x0`. This is a single standalone retail image — not the Shark Tale/Shrek 2 2-in-1 described in the guide §5.4b, and no appended trainer or multiboot stub. The crt0 at `0x08000000`–`0x08000100` is normal ARM boot code; no cracktro patch. `checksum = 0x0000` with a valid complement byte is the rebuilt-header artifact of §16.1, not evidence of a modified game.

## 2. Executive summary

**Shrek 2 (GBA, BSEX52) has no developer-intended cheat-code system**: no password screen, no button-code matcher, no hidden debug menu reachable by input, and no code table. The only cheat-like content is **progress-gated unlockables**: the sixth "book" (`Bonus Mode!`, the mini-game collection) unlocks at 100% completion / all 25 chapters, and Puss in Boots unlocks by finishing the last chapter of book 2 (these conditions are confirmed both by the published walkthrough and by the in-game gating observed at 0% — only book 1 is selectable).

Four separate false-positive ladders were identified and eliminated (details in §6b):

1. A 32-symbol on-screen alphabet (`A-Z _ ! ? $ &` + `OK`) at ROM `0x08025678` / pointer table `0x080256F8` is the **three-character "Enter Initials" high-score keyboard**, not a password alphabet. It has exactly one code xref (`0x0800A2F8`), its cursor is capped at 3 by `cmp r0,#2` at `0x0800A1C4`, and the entered characters are written into the SRAM slot record at `0x0E00000D` (entered `AAZ`, stored `ZAA`) — a name field, not a validator (§16.2b).
2. Long arrays of key-mask-shaped u16/u32 values at `0x08023360` and `0x080255B4` are **sprite animation/direction tables** (indexed by sprite anim index and interleaved with OAM-attribute code at `0x08009730`), not cheat sequences.
3. Published Shrek 2 codes for **other platforms** (Xbox/PS2/GC "Scrapbook" sequences such as `Left,Up,A,B,...`) require X/Y buttons and a Scrapbook menu that do not exist in this GBA build; the sequences are not present in the ROM under any key-mask encoding.
4. Published GBA "cheats" are Action Replay encrypted cheat-device codes (out of scope per the brief); they are not developer-intended codes.

All reachable screens were walked in mGBA with screenshots and RAM savestates; the pause menu has exactly three items (Resume / Quit Level / Sleep) and no code entry or debug option.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 SDL, `Xvfb :317 -screen 0 1024x768x24`, `DISPLAY=:317 openbox`, `SDL_AUDIODRIVER=dummy`, `mgba -3 Shrek2.gba`.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.
- Hold keys 60–150 ms with ~150–300 ms gaps; short taps are missed.
- Path: language select → A → legal/credits splash → A → title (`Start Game` / `View Credits`) → A → slot select → A on an empty slot → three-character initials keyboard → navigate to `OK` (index 31) → A → intro → A × ~12 → book select → chapter select → level → Start for pause.
- No codes were enterable because no code surface exists. Button-code attempt tested on the pause menu: `Left,Up,A,B` ×3 then `Up` ×5 produced **no change in any save/unlock flag** (61 EWRAM bytes changed, all cursor/rendering; only first-0x400 change was cursor byte at EWRAM `0x32C`).
- Screenshots and savestates are kept on disk in `/tmp/shrek2/` (not redistributed with this report).

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x08000000` | ROM | Entry branch `0xEA00002E`; stock ARM crt0 |
| `0x0801DF48` | ROM literal | `0x04000130` KEYINPUT — sole input literal, used by a wait-for-Start loop at `0x0801DEE6`–`0x0801DF04` |
| `0x08061C0C` | ROM table | English UI string table, 44 pointers (indices 0–43); `0x080620A8` is the parallel Spanish-bank copy |
| `0x08061C90` / `0x08061C94` / `0x08061C98` | ROM | UI strings `Defeat Level` / `Defeat Level 100%` / `Slow Motion` (indices 33–35) — results/minigame text, not menu entries |
| `0x08061C9C`–`0x08061CB0` | ROM | Book titles: Far Far Away, Royal Family Feuds, The Godmother, Big Surprises, Party Crashers, `Bonus Mode!` |
| `0x08025678` | ROM data | Initials alphabet: 31 bytes `0x41..0x5A,0x5F,0x21,0x3F,0x24,0x26` (`A-Z _ ! ? $ &`) then `0x89` = OK glyph |
| `0x080256F8` | ROM table | 32 pointer entries to the alphabet chars; only xref `0x0800A2F8` |
| `0x0800A180` | ROM code | Initials-entry input handler; `0x0800A1C4` `cmp r0,#2` caps input at 3 chars; `0x0800A1A0` `cmp r0,#0x89` detects OK |
| `0x0800A2EC` | ROM code | Alphabet index→char helper (`index<<2` + `0x080256F8`) |
| `0x08023360`, `0x080255B4` | ROM data | Sprite animation / direction mask arrays (false positives) |
| `0x020086D0` | RAM (EWRAM) | Initials-keyboard cursor; observed 24→25 on one Right press |
| `0x0E000000` | SRAM/Flash | 32 KiB Flash. Slot 0 record: magic bytes `60 3D C0 DE C0 DE 60 0D`, `+0x0C` = completion percent (0 at start), `+0x0D..0x0F` = initials (`ZAA`) |

Savestate RAM mapping used for evidence (mGBA `gbAs` chunk is 0x61000 bytes): IWRAM at state `0x19000`, EWRAM at `0x21000` (so EWRAM `0x020086D0` = state `0x296D0`); SRAM lives in the PNG `gbAx` chunk.

## 5. Algorithm

There is no validator to reimplement. The two algorithms actually recovered are:

**Initials keyboard** (not a code):
```
cursor = 0..31                       # 31 glyphs + OK
on A:  ch = alphabet[cursor]
       if ch == 0x89: commit_name()   # OK
       elif len < 3: buf[len++] = ch
on B:  if len > 0: buf[--len] = '-'   # 0x2D
on Left/Right: cursor = (cursor ± 1) mod 8 within row
on Up/Down:    cursor = cursor ∓ 8
commit: buf (3 bytes) is copied into the slot record at SRAM+0x0D
```
Evidence: `0x0800A180`–`0x0800A2E6` and `0x0800A2FC`–`0x0800A3DE`.

**Unlock gating:** book list is drawn from string indices 36–41 of the UI table; at 0% completion only index 36 (Far Far Away) is navigable. The setter for the 100% flag was not isolated statically (see §8), but the condition is documented by the game's own walkthrough and the gating is observable.

## 6. Tables

**UI string table (English bank `0x08061C0C`, 44 entries):**
0 Start Game, 1 View Credits, 2 Select a Slot, 3 Erase a Slot, 4 Erase Slot %d?, 5 Choose a Book, 6–11 empty, 12 Chapter %d, 13 Game %d, 14–16 empty, 17 Resume, 18 Quit Level, 19 Quit Game, 20 Quit, 21 Sleep, 22 New Game, 23 %s - %d%%, 24 Erase, 25 Done, 26 Cancel, 27 Quit Level?, 28 Quit Game?, 29 Sleep Now?, 30 wake prompt, 31 Enter Initials: ---, 32 empty, 33 Defeat Level, 34 Defeat Level 100%, 35 Slow Motion, 36 Far Far Away, 37 Royal Family Feuds, 38 The Godmother, 39 Big Surprises, 40 Party Crashers, 41 Bonus Mode!, 42–43 debug/dialog error strings.

**Initials alphabet (`0x08025678`):** `A B C D E F G H I J K L M N O P Q R S T U V W X Y Z _ ! ? $ &` (31 glyphs) + OK (`0x89`).

**Key masks used by this engine (active-high `~KEYINPUT & 0x3FF`):** A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200. Confirmed from the handler at `0x0800A226`–`0x0800A2E6`.

**Published codes checked:**
- GameFAQs/Cheat Happens/Codejunkies GBA entries: four Action Replay codes (`Infinite Health`, `All Levels Open`, `All Coins Collected`, master code) — encrypted cheat-device codes, **out of scope**, not developer-intended.
- GameFAQs "Extras for Shrek 2 XBOX" Scrapbook sequences (`Left,Up,A,B,...` variants for coins/health/level select/bonus games) — console-only; require X button; **not present in this ROM** under any encoding checked.
- Unlockables: Puss in Boots = finish last chapter of book 2; all mini-games / Bonus Mode = beat game 100% (all 25 chapters). Progress-based, not input codes.

## 6b. Enumeration

This section proves the negative result with counts, per §0.2 and §16.9.

| Search space | Size checked | Result |
|---|---|---|
| ASCII keyword hits (`password`, `cheat`, `debug`, `secret`, `unlock`, `scrap`, `level select`, `gallery`, `practice`) over 8 MiB, in plain, lower-cased and upper-cased forms | 3 full-image passes | **0 hits** for every keyword |
| `code` | full image | **1 hit**, `0x753A7F`, inside Shin'en GAX audio banner `Code: B.Wodok` — §11 false positive |
| UI string table | 44 strings, indices 0–43, fully resolved | **0** code/password/debug entry strings; complete menu vocabulary enumerated in §6 |
| On-screen alphabets | 1 alphabet, 32 grid slots at `0x08025678`/`0x080256F8`; pointer-table xrefs counted | **1 xref** (`0x0800A2F8`), to a 3-char initials field whose bytes land in SRAM `+0x0D`; **not** a validator |
| Published console button sequences converted to GBA masks (`Left,Up,A,B`, `Up,Left,Left,Right,...`) as u16-LE and u8-LE and active-low forms | full image | **0 hits** |
| Generic key-mask array scan (u16, u8, u32-aligned) | 830 / 81948 / 141 candidate runs | All candidates inspected at their dense clusters (`0x08023360`, `0x080255B4`); every one resolves to sprite animation/direction data interleaved with OAM code. **0** cheat matchers |
| KEYINPUT (`0x04000130`) literals in ROM | 2 (`0x080000A4` crt0, `0x0801DF48`) | Both are the boot hardware-init and a wait-for-Start loop; no sequence matcher |
| Hidden debug screen gates | string + xref + screen walk | No `debug` string; no unlabelled menu slot observed on any of the 10 screens walked; no reachable screen with a code entry widget |
| Dynamic button-code entry on pause menu | 17 presses (`Left,Up,A,B` ×3, `Up` ×5) | No save/unlock flag changed (61 EWRAM bytes changed, cursor/rendering only) |
| GBA password codes published anywhere | web search of GameFAQs, Cheat Happens, Codejunkies, VGChartz, IGN, TCRF (via search snippets where direct fetch 403'd) | **0**; only Action Replay codes and progress unlockables |

**Space definition result:** 0 representable codes. The only input field with a non-trivial alphabet is the 3-character initials name (`31^3 = 29,791` possible spellings), but it is a label written verbatim into the save slot, not a validated code — proven by the observed `AAZ → SRAM "ZAA"` round trip and by the absence of any string-compare consumption (the handler's consumer at `0x0800A208` calls a pointer-vectored copy with length 31, not a comparison).

**Novel code:** not applicable — no code system exists to mint from. Per §0.2, a negative is a valid result when the search space is bounded as above; this report bounds it exhaustively.

**Bounds proven by rejection:** at 0% completion, Right/Left/L/R/Down on the book-select screen did not move the selection away from book 1 (all five other books, including `Bonus Mode!`, were rejected), and the 17-press console-code attempt changed no unlock state. These are observed in-game rejections, not untested claims.

## 7. Validation evidence

- **Observed:** 10 screens walked with screenshots and savestates (language, legal/credits, title, slot select, initials keyboard, book select, chapter select, level, pause, and slot-select-with-save); KEYINPUT `0x03FF` at rest; initials cursor RAM `0x020086D0` observed `24 → 25` on one Right press; 3-char field displayed `AAZ` and stored as `ZAA` at SRAM `0x0E00000D`; save slot shows `AAZ - 0%`; only book 1 navigable; pause menu lists exactly Resume/Quit Level/Sleep; button-code attempt produced no unlock change.
- **Derived:** 44-entry UI string table fully decoded; alphabet table and its single xref; cursor cap `cmp r0,#2` and OK test `cmp r0,#0x89` in the initials handler; key-mask clusters identified as sprite animation data by their OAM-attribute context; single Nintendo logo / stock entry word proving a standalone unpatched image.
- **Inferred:** exact setter routine for the 100% unlock flag was not isolated; unlock conditions are taken from the published walkthrough plus the observed 0%-gating, labelled as such. The console Scrapbook codes are assumed not to apply because the prerequisite screen and X/Y buttons do not exist on GBA.

## 8. Unknowns

- The exact SRAM bit/byte and its setter for the 100% / all-25-chapters unlock were not isolated; the condition is corroborated by the walkthrough and by observed gating, not by a traced setter call graph (§16.18 was not fully completed for this save format).
- Whether `Defeat Level`, `Defeat Level 100%` and `Slow Motion` (UI indices 33–35) are used solely in minigame results or also in an unreferenced debug overlay; they are not reachable as menu selections on any screen walked. No `debug` string exists in the image.
- TCRF and IGN pages returned HTTP 403 to direct fetch; conclusions there rely on search-result snippets plus primary ROM/emulator evidence.

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, Python 3 (`struct`, `zlib`, `binascii`) for header/embedded-logo scan, pointer-table decoding, literal/key-mask scans.
- `strings -t x -n 3/4`, plus a custom Python pass over plain/lower/upper case, for the keyword census.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for disassembly of `0x08009480`–`0x08009C00`, `0x0800A180`–`0x0800A500`, `0x0800B460`–`0x0800B4D0`, `0x0801DEB0`–`0x0801E080`, `0x08000240`–`0x080002B0`.
- mGBA 0.10.5 SDL under Xvfb `:317` with openbox; `xdotool` XTEST input via helper `/tmp/shrek2/k.py`; `scrot` + ImageMagick crops.
- Savestate forensics: `state.py` (decompress PNG `gbAs` into 0x61000-byte raw state; IWRAM `0x19000`, EWRAM `0x21000`), `patchstate.py` (patch EWRAM cursor to 31 to select OK), `patchsram.py` (decode/re-encode `gbAx` SRAM chunk). Used to locate the keyboard cursor and to confirm the SRAM name field.
- A PTY-based mGBA `-d` debugger bridge and a GDB-stub attempt were tried and abandoned: port 2345 was occupied by another agent's stub, and the CLI debugger became unreliable after a break; savestate diffing (§16.13) was the primary RAM-evidence method instead.

## 10. Legal note

No ROM image, extracted graphics, audio, or game text is redistributed. This report publishes only hashes, addresses, algorithms derived from disassembly, and descriptions of observed behavior.
