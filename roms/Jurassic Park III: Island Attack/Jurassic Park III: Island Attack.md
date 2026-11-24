# Jurassic Park III: Island Attack (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Jurassic Park III: Island Attack.gba` |
| Size | 8,388,608 bytes (`0x800000`, 8 MiB) |
| Header title | `JP3ISLANDATT` |
| Game code | `AJQE` |
| Maker code | `A4` (Konami) |
| Version | `0x00` |
| Entry word | `0xEA00002E` — **stock** GBA branch to `0x080000C0` (§16.1: not a patched/cracktro entry) |
| Fixed `0x96` | present at `0xB2` |
| Complement / header checksum | `0x4A` / `0x0000` (recorded as-is; sum of `0xA0..0xBD` = `0xE7`, i.e. the header is non-nominative, but the entry point and first 4 KiB are normal retail code) |
| MD5 | `ccae308baca9baecaba1ab670dcc27c8` |
| SHA-1 | `493349429d78ea040204f2a74526e790f3092dc2` |
| SHA-256 | `5fff6d260e429b1ad9c55c725878650d298e30fb748d7dc39ef8e0386ae7ef1c` |

**Embedded-header scan:** the 156-byte Nintendo logo occurs exactly **once** (file `0x4`, ROM `0x08000004`). This is a single-game image, not a 2-in-1/multiboot pack. No trainer/menu patch was found: the only executable entry is the stock crt0 at `0x080000C0`, and the first code words are the standard BIOS-copy/`main` bootstrap.

## 2. Executive summary

This title has **no password screen, no button-code system, and no reachable hidden/debug menu**. The only developer-intended "cheats" are four **save-gated unlockables**, all of which are reached by *playing the game*, not by entering a code:

* Stage Select — complete any one story level.
* BGM (Music) Test — complete story mode.
* SE (Sound-effects) Test — complete story mode.
* Survival Mode — complete story mode.

All text is **font/tile-indexed**, not ASCII: `strings` returns only code noise, and the real text bank is a stream of 16-bit little-endian words `glyph,0x20` with glyph `0x00` = space. After decoding, an exhaustive keyword search over the whole text bank (4,840 extracted sequences, ~0x60000–0xA0000) found **zero** occurrences of `password`, `cheat`, `debug`, `secret`, `unlock`, `code`, `select`, `music`, `stage select`, `sound test`, `survival`, etc. The on-screen keyboards/menus offer no input surface for a code.

The published "GBA cheats" for this SKU (3rd party cheat indexes) are **unlock conditions only**; there is no published password or controller sequence to verify as a literal. A CaH4e3 search snippet describing `303030`/`F0F0F0` "stage select" codes was traced to *Amazing Penguin*, not this game (§16.7/§16.11 caution). The CodeBreaker/GameShark codes sold for this title are external memory patches and are explicitly out of scope.

Because no code system exists, the deliverable here is a **proven negative** (§0.2 point 5): every reachable screen was walked with RAM evidence, the text and button spaces were searched with counts, all published material was checked, and six undocumented button combinations were entered in the emulator with no effect.

## 3. How to reproduce

* Emulator: `mgba -3` under `Xvfb :319` (`SDL_AUDIODRIVER=dummy`), Openbox window manager.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.
* Boot path used repeatedly:
  * Konami/Mobile21 splash → legal text → title (`PRESS START`).
  * `Return` → main menu: `STORY MODE`, `OPTIONS`.
  * `Down` + `x` on main menu → options: `BUTTON CONFIG`, `DATA CLEAR`, `EXIT`.
  * `x` on BUTTON CONFIG → button-mapping screen; `DATA CLEAR` → `Yes/No` confirmation; `EXIT` → main menu.
  * `Up` + `x` on main menu → story intro (plane cutscene, Isla Sorna map, long radio dialogue) → gameplay.
  * `Return` or `BackSpace` during gameplay → pause overlay: `STAGE / CREDIT / HIT / TIME` (no menu entries).
* Screen state is observable in RAM at `0x030077A0` (see §4/§7): main menu `0x00000004`, options `0x00000005`, gameplay and button-config `0x00000001`.
* Button combinations tested at the title screen (all rejected — no screen change): Konami sequence (`↑↑↓↓←→←→ B A`), `L+R`, `Select+A`, `A+B`, `↑↓←→`, `B A B A`. Also `Select`+`Start` and `Start`+`Select`+`A`+`B` tested in-game — no effect beyond the normal pause overlay.
* Savestates: mGBA `Shift+F1`..`F3`; `.ss1/.ss2` PNGs with a zlib `gbAs` chunk, decompressed to a 397,312-byte raw state (IWRAM at raw `0x19000`, EWRAM at raw `0x21000`).

## 4. Address map

| Item | Address / offset | Evidence |
|---|---|---|
| Stock entry branch | `0x08000000` = `0xEA00002E` | Observed (header dump) |
| Main input handler | `0x08000B40`–`0x08000F20` (Thumb) | Derived (objdump) |
| `KEYINPUT` (`0x04000130`) literal reads | `0x08000B94`, `0x08000D28`, `0x08000E78` — all inside the single input handler | Derived (u32 literal scan) |
| Held/pressed/released state words | computed into IWRAM via `r7+0/+2/+4` at `0x08000C54`–`0x08000E2A` | Derived |
| Per-frame loop address used as debugger breakpoint | `0x08000350` (Thumb) | Observed (mGBA `-d`, `b/t 0x08000350`) |
| Screen-state word | IWRAM `0x030077A0` | Observed (savestate diff) |
| Text bank (English object/dialogue) | ROM `0x0806EF8C` onward | Derived (glyph decode) |
| Other localized text banks | ROM `0x08070000`–`0x080A0000` (~4,840 extracted sequences) | Derived |
| Save image | 512-byte `.sav`: magic `12elibom` (= `mobile21` reversed) at `0x00`, version string `50.0` at `0x0C` | Observed (hex dump) |

File offset ↔ ROM address: `ROM = 0x08000000 + file_offset` throughout (single image).

## 5. Algorithm

**Text encoding (derived):**
```
word_i = u16_le(rom[2i:2i+2])
glyph  = word_i & 0x00FF        # high byte is the constant 0x20 attribute
if glyph == 0x00: emit ' '
elif 0x21 <= glyph <= 0x3A: emit chr(glyph + 0x3D)   # lowercase a-z verified
elif 0x01 <= glyph <= 0x1A: uppercase range (separate bank-specific mapping)
```
Verified end-to-end: the Rom region `0x0806EF8C` decodes to readable English, e.g. `The door is locked.`, `It looks like the only path forward is through the exhibition hall.`, `You can't get through from here.`; the `0x0809xxxx` bank decodes (offset `0x3C`) to Italian, e.g. `in giro all'interno dell'edificio per`. The exact uppercase/punctuation sub-map is bank-dependent and was not needed for the negative result (all candidate keywords were searched over every uniform offset `0x00..0x5F`, not just the lowercase map).

**No validator exists to reimplement.** The input pipeline is: `KEYINPUT` → invert/mask to `0x3FF` → per-button remap through the button-config byte table → `held`, `pressed` (new), `released` words. There is no code buffer, no length check, no comparison table, and no flag word written by a code path.

## 6. Tables

### 6.1 Published material, verified against ROM/text

| Source | Claim | Verification |
|---|---|---|
| 3rd party cheat index cheats (archived 2018-11-26), 3rd party cheat indexes | Stage Select unlock: complete one story level | Consistent across 3 sources; in-game menu initially has only `STORY MODE`/`OPTIONS`, so the entry is gated |
| Same | BGM Test / SE Test unlock: complete story mode | Options initially has only `BUTTON CONFIG`/`DATA CLEAR`/`EXIT`; both test entries absent |
| Same | Survival Mode unlock: complete story mode | Not present initially; gated |
| CaH4e3 `gb_cheats.php` search snippet (`303030`, `019-D0D-E6A`, "select up to 40 levels") | Attributed by the search engine to this title | **False attribution** — the surrounding section is *Amazing Penguin* (and the `019-D0D-E6A` block is *Bubble Bobble Part 2*). Not applicable to this SKU. |

### 6.2 Text-space search counts (glyph-encoded bank, whole ROM)

Uniform-offset glyph-pattern search over all offsets `0x00..0x5F` (file `kwbrute.py`):

| Keyword | Hits |
|---|---:|
| password | 0 |
| cheat | 0 |
| debug | 0 |
| secret | 0 |
| unlock | 0 |
| code | 0 |
| select | 0 |
| music | 0 |
| bonus / hidden / survival / gallery / level | 0 |
| stage | 1 (`0x08078C4E`, ordinary dialogue "…the stage") |
| continue | 5 |
| sound | 5 (ordinary dialogue) |
| test | 24 (all in the offset-`0x3C` localized bank; Italian `testa`-type words) |

Independent decoded-text search (`fulltext.py`, 4,840 sequences) gave the same result: zero `PASSWORD/CHEAT/DEBUG/SECRET/UNLOCK/CODE/LEVELSELECT/STAGESELECT/SOUNDTEST/MUSICTEST/INVALID/BONUS/GALLERY/SURVIVAL`.

### 6.3 Button-code search counts

* `u32` literal `0x04000130` in executable range (`<0x850000`): **3** hits, all in one handler (`0x08000B94`, `0x08000D28`, `0x08000E78`). With the aligned input routine checked, there is no second key-state consumer.
* Konami prefix `↑↑↓↓←→←→ B A` encoded as consecutive active-high `u16` masks: **0** hits in the entire 8 MiB.
* `Select,Start` as `u16` masks: 11 raw hits (all in unrelated data/other banks, none xref'd from the input handler); `L,R`: 96; `A,B`: 518 — i.e. no single dedicated sequence table; matches are ordinary code/data constants.
* In-emulator rejection of six undocumented title-screen combinations: **6/6 rejected** (§3).

### 6.4 Save/unlock model

The 512-byte save begins with reversed developer magic `12elibom` = `mobile21` and version `50.0`; unlock state is stored in this save (the `DATA CLEAR` option erases it). This is a save-bit unlock system in the sense of §16.18 — **not** a code system. Four bits/fields exist (Stage Select, BGM Test, SE Test, Survival), all with single documented setters (story progress/clear).

## 6b. Enumeration

**Code space:** empty. There is no alphabet, no input length, no checksum, no comparison table, and no validator to enumerate. The only "input space" that could hide a code is (a) the game's text bank and (b) controller button sequences; both were searched with the counts in §6.2/§6.3.

**Novel code:** not applicable — no code generator or validator exists, so no unpublished code can be minted. This is a proven negative of the kind required by §0.2 point 5, not an omission.

**Bounds proven by rejection:**
* Six undocumented button sequences entered on the real title screen (Konami, `L+R`, `Select+A`, `A+B`, `↑↓←→`, `BABA`) — all rejected; screenshots `u_*.png` are byte-identical to the baseline apart from the blinking `PRESS START` cursor.
* `Select+Start` and `Start+Select+A+B` during gameplay produced only the normal stat overlay, never a debug screen.
* All four published "cheats" are conditions, not inputs; no literal exists to enter. CodeBreaker codes were deliberately not entered (out of scope: they are memory patches, not developer-intended codes).
* Every menu item was activated: BUTTON CONFIG (real configuration screen), DATA CLEAR (Yes/No confirmation), EXIT, STORY MODE (to gameplay and pause), OPTIONS. None opened a password/debug entry point.

## 7. Validation evidence

* **Observed** — emulator screenshots: title, main menu, options, button config, DATA CLEAR confirmation, pause overlay, story intro, gameplay, and post-code title screens (all under `/tmp/jp3island/`).
* **Observed** — RAM (savestate `gbAs` decompress): `0x030077A0` = `0x00000004` at main menu, `0x00000005` at options, `0x00000001` in gameplay/button-config; `0x03000000` = `0x003E0058` (menu) vs `0x001A0078` (gameplay). These prove the screens are distinct states rather than one screen redrawn.
* **Observed** — `.sav` dump with `12elibom` / `50.0` and unchanged progress bytes after failed stage attempts.
* **Derived** — text encoding from ROM bytes (verified against six in-game strings and an Italian bank), single key-input routine from literal/xref scan, absence of any validator or comparison table from the input-handler disassembly.
* **Inferred** — the four unlockables' precise save-bit positions and setter functions were not isolated; the trigger conditions are taken from three independent published sources and are consistent with the observed gated menus. I did not complete a story level, so the unlock transition itself was not observed in this session.

## 8. Unknowns

* Exact save-bit offsets and setter call sites for the four unlockables (the save image is present and gated menus were observed, but no setter was isolated).
* Full uppercase/punctuation sub-map of the font (the lowercase map is exact; the bank-dependent uppercase codes were not needed for the keyword search, which covered all uniform offsets).
* Whether a debug screen is reachable by an as-yet-undiscovered long sequence. The entire text bank and the controller-input code path were searched and six plausible combinations were rejected, so if one exists it has no text label and no dedicated key-mask table in the input handler — there is no positive evidence for it.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb`, `capstone` 5.0.7, Python 3.
* `strings`, `xxd`, `grep`; custom scripts in `/tmp/jp3island/`: `phase0.py`, `static1.py`, `textenc.py`, `lzscan.py`, `textbank.py`, `decode2.py`, `fulltext.py`, `kwsearch.py`, `kwlower.py`, `kwbrute.py`, `keyscan.py`, `ssdump.py`, `sssearch.py`, `ssregions.py`, `dbg.py`, `walk3.py`, `codetest.py`, `codetest_ui.py`, `ui.py`, `mash.py`.
* mGBA `-d` CLI debugger driven through a Python `pty` (`dbg.py`) for per-frame RAM reads; mGBA `Shift+F1/F2` savestates with a Python `zlib`/PNG `gbAs` decompressor for full-RAM snapshots.
* Web sources accessed as data only (3rd party cheat indexes via web.archive.org 20181126022852, 3rd party cheat indexes, CaH4e3). No instructions found in fetched content were followed. No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms, and derived findings are reported.
