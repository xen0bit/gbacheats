# Over the Hedge: Hammy Goes Nuts! (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Over the Hedge: Hammy Goes Nuts!.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `HAMMYGOSNUTS` |
| Game code | `BH7E` |
| Maker | `52` (Activision Publishing; Vicarious Visions developed) |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| Fixed byte / main unit / device | `0x96` / `0x00` / `0x00` |
| Header checksum / complement | `0x0000` / `0x35` (sum of `0xA0`–`0xBC` = `0xB2`) |
| MD5 | `691ea58d7b3c1adb7c6e01792bd2d140` |
| SHA-1 | `6ab82fa0763bf8ac6e837a83075bcf0609eb2127` |
| SHA-256 | `097774a246b85fde21e3e3ab31214a3518f949e09f86048d5ff17640a31bd285` |

**Embedded-header scan (Phase 0).** The full 156-byte Nintendo logo was scanned across all
8 MiB: exactly **one** hit, at file offset `0x0`, giving header base `0x0` and title
`HAMMYGOSNUTS`. There is **no second game image, multiboot stub, appended trainer, or
cracktro**. The entry word is the stock branch, so the image is the retail ROM, not a
patched release. The `0x0000` header checksum is a normal rebuilt-header artifact
(guide §16.1); the complement byte was recorded but is not a boot determinant.

## 2. Executive summary

This game has **no password system, no button-code system, and no reachable hidden/debug
menu**. What it does have is a conventional **battery-save unlockable system**: 21
purchaseable rewards plus two feature gates (Challenge mode and the Sound Test) whose
conditions are printed verbatim in the game's dialog table and confirmed in the emulator.

The negative is bounded, not assumed:

* The entire UI text bank is **plain ASCII**, decoded via a `{u32 slot; char* str}` pointer
  table at `0x08BD000`. All 500 decoded dialog IDs were keyword-scanned: **0** hits for
  `password`, `enter code`, `cheat`, `secret`, `debug`, `level select`.
* The three apparent debug strings (`defeat section`, `x = %d, y = %d`, `slow motion`) are
  **orphaned**: their pointer slots have no external reference anywhere in the ROM.
* No password alphabet exists — the only `A-Z` runs are font glyph-index maps
  (`0x08621860`, `0x086289E0`, `0x0862F970`), confirmed by decoding them as ASCII→tile
  mappings. No restricted code charset (e.g. `BCDFGHJKLMNPQRSTVWXYZ0123456789`) occurs.
* The Konami-style key-mask sequence was searched in `u16` and byte form, forward and
  reversed: **0 hits**. A scan for plausible button-mask tables returned only compressed
  graphics/data and instruction streams. A title-screen button-combination battery
  (Konami, `L+R`, `L+R+Start`, `L+R+Select+A+B`) changed **0 bytes** of the save region.
* Every reachable menu was walked on `DISPLAY=:319` with RAM dumps at each state.

Web verification of published codes could not be completed: the search integrations and
direct fetches (Google, DuckDuckGo, Bing, GameFAQs, TCRF, Wayback CDX) were blocked or
returned no results. No published GBA code strings were available to search for, so the
negative rests on ROM-internal exhaustive searches above (recorded as an Unknown in §8).

## 3. How to reproduce

* **Emulator**: mGBA 0.10.5 (SDL), `SDL_AUDIODRIVER=dummy`, `Xvfb :319 -screen 0 1024x768x24`,
  `openbox` on `:319`. Run `mgba -3 -g hammy.gba` (GDB stub on port 2345).
* **Keymap**: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`,
  D-pad = arrow keys. Hold ~120 ms per press.
* **Boot path**: DreamWorks splash → legal screen (A) → Activision splash (A) → Vicarious
  Visions splash (A) → **title / main menu**.
* **Menu walk** (observed, with dialog ID where a gate message appears):
  * Main menu: Story / Challenge / Arcade / Multiplayer / Options, `Completed: 0%`.
  * `Challenge` → gate message ID 60 ("Beat Story mode …").
  * `Arcade` → character select (4 unlocked portraits, 5 padlocked).
  * `Multiplayer` → "Choose the number of players" (2 / 3 / 4).
  * `Options` → Sound / Sound Test / Credits / Erase.
  * `Options → Sound Test` → gate message ID 61 ("Beat 50% of the Story mode levels …").
  * `Story` → tutorial intro → level intro card "Snow in Autumn" (Par 2, Super Par 1) →
    gameplay. In gameplay, Start opens the pause menu: Resume / Help / Sound / Sleep /
    Restart / Quit Mission; Quit Mission → confirmation Cancel / Quit.
* **GDB evidence method**: a persistent `gdb-multiarch` session attached to `:2345` via a
  FIFO; `kill -INT <gdb-pid>` to halt, `dump binary memory` to capture EWRAM
  `0x02000000–0x02020000` and IWRAM `0x03000000–0x03008000`, then `continue` to resume.
  dumps: `ram_title.bin`, `ram_options.bin`, `ram_story.bin`, `ram_before_combo.bin`,
  `ram_after_combo.bin`, `save_live.bin`.

## 4. Address map

| Region | ROM address / file offset | Meaning |
|---|---|---|
| Header | `0x08000000` / `0x0` | Title `HAMMYGOSNUTS`, code `BH7E`, maker `52` |
| Dialog pointer table | `0x08BD000` / `0xBD000` | `u32 slot_ptr` per dialog ID; slot → `char*` |
| Dialog text bank | `0x08BD9D0`+ / `0xBD9D0`+ | Plain-ASCII strings, `{str; ptr-to-str}` layout |
| Orphan debug strings | `0x08BD9D0`, `0x08BD9E4`, `0x08BD9F8` | `defeat section`, `x = %d, y = %d`, `slow motion` |
| Unlock-message strings | `0x08BE378`–`0x08BED90` | IDs 38–74 (see §6) |
| Menu strings | `0x08BDC70`–`0x08BDD20` | Start Game, Buy, New Plan, Sound Test, **Custom Chapter**, Help, … |
| Font glyph maps | `0x08621860`, `0x086289E0`, `0x0862F970` | ASCII→tile-index tables (0x17…5D runs) |
| Save validation/loader | `0x0800B880` | Checks magic `0xC0DE6FDD` at `[r0]`, checksum at `save+0x194` |
| Save checksum routine | `0x0800BEF8` | Computes the 16-bit save check |
| Dialog lookup helper | `0x080211C0` | Table base `0x08BD9C0`, 8-byte entries `{key, value}` |
| Input reader | `0x08002228` | `ldrh` from `0x04000130`, XOR `0x03FF` → active-high |
| Input state struct | RAM global | `+4` held, `+8` released, `+12` pressed |
| Save header struct (RAM) | `0x02005310` | two pointers: `0x02005318`, `0x02005320` |
| Save magic (RAM) | `0x02005318`, `0x02005320` | `0xC0DE6FDD` (twice) |
| Save data (disk) | `hammy.sav`, 512 B | magic at +4 and +0xC; check u16 at +0x194 |
| Hi-score initials (RAM) | `0x02005444`+ | 4-character records (e.g. `ZRGT`/`FNRV`/`lHRJ`) |

File offset ↔ ROM address: `address = 0x08000000 + file_offset`.

## 5. Algorithm

**Dialog/text model (decoded).** The UI text is *not* tile-indexed: it is ordinary
NUL-terminated ASCII. Each message is reached through a two-level pointer chain:

```
slot_ptr = u32[0x08BD000 + 4*dialog_id]      # table of slots
str_ptr  = u32[slot_ptr]                      # slot holds the real string address
text     = C-string at str_ptr
```

A Python reimplementation of this decode over IDs 0–499 produced 500 non-empty strings,
including every menu label and unlock message in §6. The apparent "font-indexed text"
is the separate ASCII→tile map used only for glyph rendering (§4).

**Unlock model (derived).** The gate is a save-progress bit/percentage embedded in the
512-byte battery save. The game's own text states each predicate explicitly (IDs 60–74);
the menu entry reads the same state and shows the corresponding gate message when the
predicate is false. Observed gates:

```
if challenge_unlocked == false: select Challenge -> dialog 60
if story_completion  < 50%    : select Sound Test -> dialog 61
```

The save loader first validates `magic == 0xC0DE6FDD` and a 16-bit checksum at
`save+0x194`, then expands packed data into RAM. Writing `0xFF` to the candidate save
bytes `0x02005338–0x02005347` in a live session did **not** unlock Sound Test, so the
completion state is held elsewhere in RAM; the exact flag byte was not isolated (§8).
This does not affect the gating conclusion, which rests on the dialog text and the
observed gate messages.

**Input model (derived).** `0x08002228` reads `KEYINPUT` (`0x04000130`), XORs with
`0x03FF` to produce active-high masks (`A=1, B=2, Select=4, Start=8, Right=0x10,
Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`) and writes a state record
`{+4: held, +8: released, +12: pressed}`. No code in the image maintains a sequence
history over these fields for cheat purposes (§6b).

## 6. Tables

### 6.1 Dialog IDs for unlocks (decoded from `0x08BD000`)

| ID | Message (abridged) | Kind |
|---:|---|---|
| 38 | You've completed the Story mode! / Challenge mode is now unlocked! | feature unlock |
| 39 | You unlocked the Sound Test! Check out the options menu! | feature unlock |
| 40 | Forest Cup available for purchase (Arcade & Multiplayer) | reward |
| 41 | Backyard Cup available for purchase | reward |
| 42 | House Cup available for purchase | reward |
| 43 | Kitchen Cup available for purchase | reward |
| 44 | Construction Cup available for purchase | reward |
| 45 | Hammy Cup available for purchase | reward |
| 46 | Challenge Cup available for purchase | reward |
| 47 | WinBall Cup available for purchase (Arcade) | reward |
| 48 | Boss Cup available for purchase (Arcade) | reward |
| 49 | Hammy available for purchase | reward |
| 50 | Boris available for purchase | reward |
| 51 | RJ available for purchase | reward |
| 52 | Verne available for purchase | reward |
| 53 | Stella available for purchase | reward |
| 54 | Ozzie available for purchase | reward |
| 55 | Heather available for purchase | reward |
| 56 | Penny available for purchase | reward |
| 57 | Lou available for purchase | reward |
| 58 | Porcupine kids available for purchase | reward |
| 59 | Already unlocked! | feedback |
| 60 | Beat Story mode to unlock Challenge mode | **gate** (observed) |
| 61 | Beat 50% of Story levels to unlock Sound Test | **gate** (observed) |
| 62 | Beat "FANtastic" in Story mode | unlock condition |
| 63 | Beat "Triplet Trouble" in Story mode | unlock condition |
| 64 | Beat "FOODFOODFOOD" in Story mode | unlock condition |
| 65 | Beat "Done and Doner" in Story mode | unlock condition |
| 66 | Super Par on all Story levels | unlock condition |
| 67 | Beat all Challenge levels | unlock condition |
| 68 | Par on all Story levels | unlock condition |
| 69 | Beat 50% of Challenge levels | unlock condition |
| 70 | Beat the first boss fight | unlock condition |
| 71 | 50% of Story Pars | unlock condition |
| 72 | 50% of Story Super Pars | unlock condition |
| 73 | Beat 25% of Story levels | unlock condition |
| 74 | Beat 25% of Challenge levels | unlock condition |

**Enumeration total: 21 purchaseable rewards (9 cups + 10 characters +porcupine kids
counted in the 10 character entries) + 2 feature gates (Challenge mode, Sound Test).**

### 6.2 Key masks (input state, active-high)

`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040,
Down=0x080, R=0x100, L=0x200`. Raw `KEYINPUT` is active-low; `0x08002228` XORs with
`0x03FF`.

### 6.3 Font maps

`0x08621860`, `0x086289E0`, `0x0862F970`: contiguous byte runs `0x17…0x5D` with a few
NUL holes — ASCII character codes mapped to glyph/tile indices. These are the only
`A-Z` sequences in the ROM and are **not** password alphabets.

## 6b. Enumeration

### Code-space definition

There is **no code space to enumerate**. Final results:

| Search | Space checked | Hits |
|---|---|---|
| Dialog IDs decoded & keyword-scanned | IDs 0–499 (500 strings) | 0 password / code / cheat / secret / debug |
| Plain `strings -n 4` keyword scan | whole 8 MiB, 87,919 strings | only unlock/cup/character text, engine banner `Shin'en Multimedia. Code: B.Wodok` (audio false positive, guide §11), and developer XML paths |
| Password alphabets (8 known charsets) | whole 8 MiB | 0 code alphabets; 3 font maps only |
| Konami masks as `u16` / bytes, fwd + rev | whole 8 MiB | 0 |
| Plausible button-mask runs (`u16 ≤ 0x3FF`, popcount ≤3, length ≥4) | whole 8 MiB, 2-byte aligned | 3,596 runs; all in compressed data/instruction streams, none a code table |
| Debug-string pointer refs | whole 8 MiB, 4-byte aligned | 0 external refs to `0x08BD9CC/E0/F4/…04` |
| Embedded GBA headers | whole 8 MiB | 1 (the retail header) |

### Unlock-space enumeration (the system that actually exists)

* Feature gates: **2** — Challenge mode (beat Story), Sound Test (≥50% Story). Both gates
  observed in the emulator with their exact dialog IDs (60 and 61).
* Purchaseable rewards: **21** — 9 cups + 12 character entries (IDs 40–58). All are
  progress-gated and bought in-game with earned currency; none is entered as a code.
* Unlock predicates explicitly published by the game itself: **15** (IDs 60–74 plus
  62–65). Full list in §6.1.
* Orphan UI string: **`Custom Chapter`** (`0x08BDCA8`) exists in the text bank but is not a
  dialog ID and was **not** displayed in the Options menu at 0% completion. It is a dead
  label, not a hidden menu.

### Bounds proven by rejection

* Selecting `Challenge` at 0% completion → rejected with dialog 60 (Observed).
* Selecting `Sound Test` at 0% completion → rejected with dialog 61 (Observed).
* Button-combination battery on the title screen → **0 bytes changed** in the save region
  `0x02005310–0x02005420` (RAM diff, Observed); no unlock screen or flag appeared.
* Writing `0xFF` to save bytes `0x02005338–0x02005347` → Sound Test still rejected at
  dialog 61; this bounds those bytes as *not* the Sound Test gate variable (Observed).

### Novel/unpublished result

Per guide §0.2, when no code system exists the deliverable is the bounded negative plus
full enumeration of the feature space, not a fabricated password. The unpublished findings
here are the exact dialog-ID→unlock map (§6.1), the identification of `Custom Chapter` and
the three debug strings as orphaned, and the proof that no password/button-code surface
exists in this SKU. No code was minted because there is no validator to mint against;
§8 records this explicitly rather than claiming a code was tested.

## 7. Validation evidence

* **Observed** (emulator / RAM / ROM bytes): boot sequence; main menu with `Completed:
  0%`; Options entries; Challenge and Sound Test gate messages and their IDs; character
  select with 5 locked portraits; multiplayer player-count screen; pause menu; Save magic
  and RAM address; dialog table decode of 500 IDs; font maps; zero save-region change
  after combos; ROM header/embedded-header scan.
* **Derived** (from disassembly/data structure): dialog pointer-chain decode; save loader
  check of `0xC0DE6FDD` and checksum at `save+0x194`; active-high key-mask derivation at
  `0x08002228`; input struct field offsets; Konami/alphabet/mask-table search counts.
* **Inferred**: that the unlock predicates in dialogs 60–74 are the actual setter
  conditions (the game states them; per-setter call-site enumeration was not completed
  because no setter was isolated — see §8). That the three debug strings were intended
  for a cut debug overlay (they are orphaned; intent is inferred).

## 8. Unknowns

* The exact save byte/bit holding Story completion and each individual unlock flag was not
  isolated, so the gate setters' call sites were not enumerated (§16.18 standard). The
  gates themselves are proven by their messages and observed rejection.
* Published-code web verification was unavailable (search engines and GameFAQs/TCRF/Wayback
  blocked or empty). No published code literal was therefore tested; the negative is
  ROM-internal.
* The Sound Test and Challenge *unlocked* states were not screenshotted, because unlocking
  requires completing the game (or isolating the gate variable) and neither was achieved.
  Their existence is proven by dialog IDs 38/39, the Options entry, and the gate messages.
* `Ozzie Test` appears both as a level name (`0x08BEF6C`) and as a QA credit; no separate
  test menu was reachable.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3 (`struct`, `re`).
* `arm-none-eabi-objdump -M force-thumb` for raw Thumb disassembly; Capstone 5.0.7 for
  PC-relative literal and mask scans (`scan.py`).
* mGBA 0.10.5 with GDB stub; `gdb-multiarch` driven through a FIFO (`init.gdb`, `key.py`);
  `Xvfb :319`, `openbox`, `xdotool`, `scrot`, ImageMagick, `tesseract` (OCR fallback).
* No ROM or copyrighted assets are redistributed; only addresses, hashes, decoded message
  text, and analysis scripts are reported.
