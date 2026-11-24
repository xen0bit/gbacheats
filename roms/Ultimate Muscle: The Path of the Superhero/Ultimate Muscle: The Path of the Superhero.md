# Ultimate Muscle: The Path of the Superhero (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Ultimate Muscle: The Path of the Superhero.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| Header title | `UMUSCLE` |
| Game code | `AK2E` (USA, revision 00) |
| Maker code | `B2` |
| Version / complement / checksum | `0x00` / `0xBC` / `0x0000` |
| Entry word | `0xEA3ED462` → `0x08FB5190` (file `0xFB5190`) |
| MD5 | `2c06fd1d424db4b2cd6ffde2b5a7d8ff` |
| SHA-1 | `c701dd6e6042b550051ed2f476ada9b84538f412` |
| SHA-256 | `01a84afb5dc8444101fb64deb1560cf9353a80522d55da2ad3f990d069ceab97` |
| `file` identification | Game Boy Advance ROM image: "UMUSCLE" (AK2EB2, Rev.00) |
| GameHacking.org CRC32 | `BB85AD55`, serial `AGB-AK2E-USA` (matches this image) |

**Release integrity (§16.1):** this image is a **VENOM scene release with a cracktro**, not a stock retail boot. The entry word branches to file offset `0xFB5190`, and the boot screen shows "VENOM PRESENTS ULTIMATE MUSCLE! (C) BANDAI". The stock crt0 at `0x080000C0` is intact and the game runs normally after the intro is skipped. The header complement byte is `0xBC` where a stock header would compute `0xD5` over bytes `0xA0..0xBC`, confirming the header was edited by the release. The cracktro is a trainer-style intro, **not** an in-game cheat feature (no cheat options are exposed by it). The intro does not print ASCII (`VENOM` is tile-rendered), which is why `strings` finds no intro text.

## 2. Executive summary

**No in-game cheat-code system exists in this title.** There is no password entry, no button-code sequence handler, and no hidden/debug menu reachable by controller input. The only hidden content is **five locked character slots** in the Survivor/Versus character-select grid, which are **save-bit unlockables** (earned by completing game modes on specified difficulties), not codes. Everything published for this SKU is either (a) those save-based unlockables or (b) third-party GameShark/CodeBreaker RAM patches, which are explicitly out of scope.

This is a **bounded negative** (§0.2 point 5), not an untested guess. Evidence:

* All **seven** main-menu entries and their sub-screens were entered and documented; a menu-selection byte in IWRAM was read for each entry (§4). No screen contains a text/code input field.
* A whole-ROM census of cheat-related keywords in ASCII (case-insensitive), UTF-16LE, UTF-16BE, reversed, additive-`0x20` and XOR encodings returned **zero** semantically meaningful hits (§6b).
* No password alphabet is present. The 48 UTF-16LE `A-Z` runs found are a 1:1 8-bit codepage/fount table repeated per font bank, not a code alphabet (§6b).
* A targeted scan for button-mask sequence tables found 419 candidate single-button `u16` runs; of the 24 that are referenced by a 32-bit ROM pointer, **all are constant fills or non-code binary data** — none is a cheat sequence (§6b).
* The game's only input-reading code path (`0x04000130` literal at file `0x98E4`) belongs to a script/VM interpreter for move tutorials, not a cheat validator (§4).
* Common button sequences (Konami code, L+R+Start, L+R+A+B, Start+Select+A+B, A×9) were pressed on the title/menu: only normal menu and gameplay transitions were observed, no hidden screen (§7).

No novel code could be minted because there is no code space to enumerate; the "enumeration" deliverable is therefore the complete screen/state enumeration plus the counted negative searches in §6b.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, `-3` scaling. GBA viewport is 720×480 at screen `(153,165)` in the 1024×768 root.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold ~60–100 ms per press (longer holds double-step menus).
* Boot: the VENOM cracktro appears; press Start/A to skip it, then let the ~20 s retailer intro play (or press A repeatedly) to reach the title. Press Start on the title to reach the main menu.
* A convenient savestate of the main menu (Story Mode highlighted) is preserved as `/tmp/ultimatemuscle/state_story.ss1`; mGBA `-t <state>` boots straight to it.
* Menu ring (Down cycles, wraps): **Story Mode → Survivor Mode → 3 VS 3 Team Battle → Versus Mode → Training → Directory → Options**. Press A to enter, B to return.
* Observations per entry:
  * Story Mode: `New game` / `Continue` (save-based; Continue immediately plays the opening cutscene).
  * Survivor Mode: `New game` / `Continue` → Character Select (8+8+3 selectable, 5 locked) → match.
  * 3 VS 3 Team Battle: `New game` / `Continue` / `VS` (link).
  * Versus Mode: `VS Computer` / `VS` (link).
  * Training: `Beginner` / `Advanced`; A shows a `Friendship` popup then starts the tutorial match.
  * Directory: character profile browser (`A Button:Tech List./Profile`, `B Button:Return`); Left/Right browses 19 profiles; A toggles a move-list screen showing button inputs for techniques.
  * Options: `Difficulty Level` EASY/NORMAL/HARD, `Commentary` ON/OFF, `Alarm` ON/OFF/OFF-while-connecting, `Auto Save` ON/OFF, `Data Trade` (returns to title; link feature), `Return`.
* No code/password field exists on any of these screens.

## 4. Address map / RAM evidence

| Item | Address | Evidence |
|---|---|---|
| Stock ARM crt0 | `0x080000C0` | Observed: valid `mov r0,#0x12 / msr CPSR_c` prologue; boots normally after cracktro skip |
| Entry branch target (cracktro) | `0x08FB5190` (file `0xFB5190`) | Derived: `0x08000008 + (0x3ED462<<2)` |
| Cracktro intro | file `0xFB5190+` | Observed: VENOM presents screen |
| ASCII dialogue text banks | file `0x77C00..0x8xxxx`, `0xCB0000..` | Observed: `strings`; e.g. "The son of king Muscle." at `0x77C5F` |
| Input register literal | file `0x98E4` = `0x04000130` | Derived: `ldrh` + `eor #0x03FF` inside a script/tutorial interpreter |
| **Menu selection byte** | **IWRAM `0x030058F4`** | **Observed: values `0x00..0x06` for the seven menu entries (savestate diff + direct read)** |
| Secondary menu copy | IWRAM `0x030058FA` | Observed: tracks selection with one-frame lag |
| Save file | SRAM/Flash 512 bytes (`*.sav`) | Observed: header `ELCSMTLU`, checksum pattern `a9 77 2a 33`, flag blocks `0x1C0` (`FF…`) and `0x1E0` (`01…`) |

**Menu-index verification (Observed):** savestates taken while stepping Down through the ring read `0x00,0x01,0x02,0x03,0x04,0x05,0x06` at `0x030058F4`, matching Story, Survivor, 3 VS 3, Versus, Training, Directory, Options respectively. This is the RAM evidence that every screen in the ring was actually reached, not inferred from screenshots alone.

## 5. Algorithm

Not applicable: no password validator, checksum, decoder, generator or button-code matcher exists in this image. The only state machine found is the menu ring:

```
menu_index = (menu_index + 1) mod 7      # Down; Up decrements mod 7
A -> dispatch[menu_index](); B -> return to parent screen
```

No comparison against controller-mask constants or user-entered text was found in any reachable handler (see §6b for the counted negative).

## 6. Tables

### Main menu (ring of 7)
| Index | Entry | Sub-screens |
|---:|---|---|
| 0 | Story Mode | New game / Continue → cutscene → gameplay |
| 1 | Survivor Mode | New game / Continue → Character Select → match |
| 2 | 3 VS 3 Team Battle | New game / Continue / VS |
| 3 | Versus Mode | VS Computer / VS |
| 4 | Training | Beginner / Advanced → tutorial match |
| 5 | Directory | 19 character profiles + per-character tech list |
| 6 | Options | 6 settings rows (no code entry) |

### Character Select (Survivor; Observed)
24 grid slots in 3 rows of 8. **19 selectable**, **5 locked** (rendered as dark silhouettes). The selector **skips** the locked slots: from row-2 col-2, pressing Right wraps to row-0 col-2 rather than moving into the locked cells. The locked slots therefore have no input path and are save-bit gated.

### Directory roster (Observed, 19 unique entries before wrap)
Kid Muscle, Terry Kinnikuman, Wally Tusket, Dik Dik Van Diemen, Jeager, Hydrazon, Eskara, Road Ramey(?), Chalbone(?), Pumpin(?), Kevin Maul, Tiranoc(?), Checkmate, Forkoless, Hanzo, Bone Kool(?), King Muscle, Ramenman, Buffaloman. (Names read from the rendered profile banner; ambiguous glyph readings marked `?`. Locked versions are *not* listed here.)

### Published unlockables (web recon; save-bit, not codes)
| Unlockable | Condition (GameFAQs / Neoseeker / AbsoluteCheats, consistent) |
|---|---|
| King Muscle | Complete the game without losing (Story) |
| Sgt. Kinnikuman | Win Survival Mode on Hard |
| Young Buffaloman | Win Survival Mode on Normal |
| Young Ramenman | Win 3-on-3 Mode on Normal |
| Young King Muscle | Win Story Mode on Easy without losing |

### Out-of-scope published material
GameHacking.org / CodeTwink / 53lu list GameShark, CodeBreaker and MaxCatz RAM patches (e.g. `33006E05 00FF` infinite health, master code `0000DE7B 000A 1003C398 0007`). These are cheat-device codes, not developer-intended in-game cheats, and were **not** tested or reported as findings.

## 6b. Enumeration

**Code space: empty.** This section records the complete negative search with counts, per §0.2(5).

### (a) Screen/state space — fully enumerated
* 7 main-menu entries, RAM indices `0x00..0x06` confirmed (§4).
* Every entry opened; all reachable sub-screens documented (§3). **Count of screens with a text/code input field: 0.**
* Character-select ring fully traversed: 19 reachable characters + 5 unreachable locked slots. Count of locked slots reachable by any D-pad path: **0** (selector wraps over them).
* Options ring: 6 rows; count of cheat/debug rows: **0**.

### (b) Text/encoding search space — whole 16 MiB ROM
| Search | Space checked | Meaningful hits |
|---|---|---|
| `password`, `cheat`, `secret`, `debug`, `unlock`, `level select`, `sound test` — ASCII, case-insensitive | 16,777,216 bytes × 7 terms | **0** |
| Same terms — UTF-16LE and UTF-16BE | 2 × 16,777,216 byte alignments | **0** |
| Same terms — byte-reversed | 16,777,216 bytes | **0** |
| `code`, `enter` — ASCII | whole ROM | 1 each: `code` at `0xFC148F` (inside compressed/audio data, context `edits\xc0\x17/code.\xa0\x00`), `enter` at `0x86EB0` (inside the word "center" in dialogue) — both false positives |
| UI words `PASSWORD/CONTINUE/OPTIONS/SECRET/CHEAT/DEBUG/TRAINING/DIRECTORY` under additive and XOR byte mappings, 8 words × 256 keys × 2 encodings = 4,096 patterns | whole ROM | 6 hits, all lowercase-dialogue additive-`0x20` matches or isolated XOR coincidences in compressed data (e.g. `DEBUG` XOR `0x46` at `0x15FADC`); **no UI code string** |
| Classic password alphabets (`A-Z`, `0-9A-Z`, `A-Z0-9`, `BCDFGHJKLMNPQRSTVWXYZ0123456789`, Car Battler Joe alphabet) — ASCII and case-insensitive | whole ROM | **0** |
| UTF-16LE `A-Z` / `a-z` runs | whole ROM | 48 / 43 hits, all part of a repeated 1:1 codepage table (`0x21,0x00,0x22,0x00,…`) beginning at file `0xCC3544` — a font/glyph list, **not** a password alphabet |

**Font/tile decode (§11 requirement):** the visible menu labels are tile-rendered and do not appear as ASCII; they were probed by brute-forcing additive and XOR byte mappings over eight known UI words (§6b table). No mapping produced a hidden code string. Conversely, the game *does* store its dialogue as plain NUL-terminated ASCII (verified at `0x77C5F`, `0x8422E`, `0xCB25FD`), so a code string would have been visible to the ASCII census had one existed. The 48 UTF-16 codepage blocks were decoded and shown to be a straight 8-bit→UTF-16 identity table, not an encoding of game text.

### (c) Button-mask / debug-gate space
| Search | Space | Result |
|---|---|---|
| Runs of ≥4 consecutive `u16` values each a single GBA key bit (`1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200`) | whole ROM, 8,388,608 word positions | **419 candidate runs** |
| Of those, runs referenced by a 32-bit `0x08……` pointer | same | **24**, all inspected: constant fills (`0x1`, `0x200`) or binary sprite/tile data (e.g. `0x40578` is a bitmap, not a key sequence). **0 cheat tables** |
| Literal `0x04000130` (KEYINPUT) in code/data | whole ROM | **3** (`0x98E4`, `0x9A28`, `0x2D1CC`); disassembly at `0x08009780..0x08009930` shows a script/tutorial interpreter that reads keys and XORs with `0x03FF`, **no** comparison to a fixed cheat mask |
| Raw `u16` occurrences of classic gate masks `0x300`(L+R), `0x0C`(Start+Select), `0x3FF` | whole ROM | 15,438 / 2,426 / 717 — raw-data noise; none in a validator (the only key-reading function was disassembled) |

### (d) Dynamic button-code probe (Observed)
Five common sequences were pressed on the title/menu: Konami code (`↑↑↓↓←→←→BA` + Start), L+R+Start, L+R+A+B, Start+Select+A+B, and A×9. All produced ordinary menu/gameplay transitions (the final A×9 frame is a live wrestling match); **no hidden screen, menu, or flag change was observed.**

### (e) Novel code
**Not applicable — there is no code format to mint.** Per the guide's negative-result branch, the deliverable is the counted negative above rather than a fabricated code. No code was generated, and no ROM text or screen claims to accept one.

## 7. Validation evidence

* **Observed:** boot screen (VENOM cracktro), title, all seven menu screens, sub-screens, character-select locked slots, Directory roster, Options rows; menu index byte at `0x030058F4`; savestate diffs; button-sequence probe frames.
* **Derived:** entry-branch target arithmetic; KEYINPUT interpreter at `0x080098AE`; header complement mismatch; font-mapping brute-force results; pointer-referenced mask-run enumeration.
* **Inferred (labelled):** the five locked slots are save-bit gated — the in-game selector skipping them is observed, and the unlock conditions are from three consistent published sources, but no unlock setter was executed in the emulator (would require completing full game modes). The exact identity of each locked slot's character is inferred from the published list, not read from the ROM UI.
* Screenshots and raw dumps used as evidence were in `/tmp/ultimatemuscle/` (`walk00_small.png`, `story1_small.png`, `survivor_new_small.png`, `cs_locked2_small.png`, `options_screen_small.png`, `dir_names_sheet.png`, `state_raw.bin`, `ramA.ss1`/`ramB.ss1`, etc.).

## 8. Unknowns

* Whether any of the five locked character slots can be reached by a sequence longer/more obscure than those probed (no published claim exists; the selector wrap strongly indicates a save-bit gate).
* Exact character names for four Directory entries whose rendered glyphs were ambiguous (marked `?` in §6).
* Whether the retail (non-cracktro) build differs — only this VENOM-patched image was analyzed; all addresses are for MD5 `2c06fd1d…`.
* Internal save-flag bit positions for the five unlocks were not located (the 512-byte `.sav` shows flag blocks at `0x1C0`/`0x1E0`, but no setter was traced).

## 9. Tooling

* `md5sum`, `sha1sum`, `sha256sum`, `file`, `xxd`, `strings`, `grep -abo` for fingerprinting and text census.
* Python 3 (+ Pillow) for whole-ROM byte/pattern censuses, savestate `gbAs` zlib extraction and diffing, font-mapping brute force, and screenshot cropping.
* `arm-none-eabi-objdump -M force-thumb` for the `0x08009780` input interpreter.
* `gdb-multiarch` with mGBA's `-g` stub for VRAM/IWRAM/EWRAM dumps (note: detaching the stub can terminate this mGBA build; savestate diffing is the more reliable RAM fallback, §16.13).
* mGBA 0.10.5 under Xvfb `:316` + openbox; `xdotool` XTEST input; `scrot` screenshots; helper `/tmp/ultimatemuscle/ui.py`.

**Legal note:** no ROM bytes or copyrighted graphics/audio are reproduced here; only hashes, addresses, counts and original observations are published.

**Cleanup:** own processes terminated by PID (mGBA, Xvfb `:316`, openbox); `.sav` and `.ss*` artifacts removed from the ROM folder.
