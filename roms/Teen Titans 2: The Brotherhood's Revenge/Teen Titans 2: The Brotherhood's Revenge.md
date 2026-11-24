# Teen Titans 2: The Brotherhood's Revenge (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Teen Titans 2: The Brotherhood's Revenge.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `TEEN TITAN 2` (12 bytes at `0xA0`) |
| Game code | `BZUE` (`0xAC`); maker `5G` (`0xB0`) |
| Version | `0x00` (`0xBC`); complement `0x81` (`0xBD`); header checksum `0x0000` (`0xBE`) |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`), fixed `0x96` present |
| Build stamp | `Aug 17 2006 16:49:55` at file `0x7887C0` (`0x087887C0`) |
| MD5 | `c9ce90b98c6cc2f60847d6f39ecf11c5` |
| SHA-1 | `1cfca926300db1719aa671404386a19b55316054` |
| SHA-256 | `fd706b370ef5905f0ac225e03d154cc39c9e093d64366bcb419f4f1365cf3cc1` |
| Region | USA (En,Fr); serial AGB-BZUE-USA; CRC32 `CCACD823` per 3rd party cheat indexes |

The header complement/checksum are internally inconsistent with the standard formula
(sum of `0xA0..0xBD` = `0x66`, expected complement `0x99`, actual `0x81`, checksum `0`),
which suggests a rebuilt header; the entry word is stock so this is not a cracktro
(§16.1). No sibling Teen Titans title was consulted for any finding below.

## 2. Executive summary

**Bounded negative: this ROM has no in-game/developer-intended cheat-code system.**
There is no password entry screen, no code alphabet, no validator, no button-code
matcher and no hidden menu reachable by controller input on any reachable screen.
The single widely published "password", `7FB36FAC3B31`, is a **CodeBreaker /
GameShark SP / Xploder cheat-device code** ("Access All Levels", by MadCatz), not an
in-game code; 3rd party cheat indexes mislabels it as a "Level Password". Every published code for
this SKU is a cheat-device code and is out of scope.

The build does contain a substantial **unreached debug facility**: 85 menu entries and
five debug screens (Obj Viewer, Music Player, FX Player, a level-select menu and a
generic debug screen) with full ASCII text, handler tables and a global screen-table
slot. 3rd party cheat indexes explicitly records that access to this menu is unknown. Static xrefs and a
19-combination controller sweep found no retail path to those screens; the ROM's own
debug flags are only written by the debug handlers themselves. This is reported as a
*gated/unreachable development feature*, not as a cheat.

Because no accepted code exists, §0.2's "mint a novel code" deliverable is not
applicable; the required alternative — a bounded negative with counts — is delivered
in §6b.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 100–150 ms.
* Boot path: language select (English/Français) → Nintendo health warning → DC/A2M logos → "Press Start" title → main menu.
  * Main menu has exactly three entries: **New Game**, **Load Game**, **Options** (Left/Right selects; A confirms).
  * New Game and Load Game both present three save slots (`1/2/3`, all `No Data` on a blank save). No code field.
  * Options has exactly three settings: Music, FX, Language. No hidden entry after scrolling.
  * In-game pause menu (`Start` during play) has exactly five entries: Continue, Status, Action List, Options, Quit the game. Seven Down presses wrap from Continue to Action List (5-entry ring) — no unlabelled sixth entry.
* Button-code sweep: from the title screen, reload a savestate at the title, send a combination, wait 1 s, screenshot and compare. 19 combinations were tested (§6b).
* RAM evidence: mGBA `.ss1` savestates were parsed as PNG + `gbAs` zlib chunk. For this 8 MiB ROM the decompressed state is `0x61000` bytes, with IWRAM at state offset `0x19000` and EWRAM at `0x21000` (verified against a GDB read of `0x02007754` = `0x01`). The keypad state used by the debug handlers is `0x0200FE56` (word at `0x0200FE50`, offset `+6`).

## 4. Address map

All addresses are ROM addresses (`file offset + 0x08000000`) unless marked EWRAM.

| Item | Address / file offset | Evidence |
|---|---|---|
| Numeric debug text bank (level list) | `0x08047824` (file `0x47824`) | Derived: ASCII dump; level labels `0x08047874`–`0x08047A48`, challenge labels `0x08047A44`–`0x08047C58`, boss/`Normal Boot` labels `0x08047C60`–`0x08047D3C` |
| Debug menu table (header at `0x1BE4C0`, 32-byte slots) | `0x081BE4C0`–`0x081BF60C` | Derived: 85 slots, label pointer at `+0x0C`, sub-table pointer at `+0x14`, packed selector at `+0x18` |
| Viewer UI text | `0x0819D18C` | Derived: `OBJ VIEWER`, `Obj No:`, `Anim No:`, `Anim Mode:`, `Once/Loop/PingPong`, `MUSIC PLAYER`, `Music No:`, `FX PLAYER`, `Fx No:` |
| Viewer handler descriptors | `0x0819D128`, `0x0819D13C`, `0x0819D20C`, `0x0819D220`, `0x0819D234` | Derived: each is `{0xA8, fn, fn, fn, fn}` |
| Viewer handler code | `0x08000144`, `0x080002B0`, `0x080002C0`, `0x080003A8`, `0x080003BC`, `0x0800048D` | Derived: Thumb disassembly; reads keypad at `0x0200FE56` |
| Global screen table | `0x0819B178` | Derived: >100 descriptors; debug screens occupy indices 0–4 |
| Screen selector reader | `0x080148CC`, `0x08014A08` | Derived: `ldrh` of `u16` at object `+0xEE`, indexes `0x0819B178` |
| Debug-related EWRAM byte | `0x02007754` | Observed: byte `0x01` at boot; `0x080003A8` sets bit 0 (no BL callers found) |
| Build date string | `0x087887C0` | Derived |
| Keypad word (active-high `+6`) | `0x0200FE50` / `0x0200FE56` | Derived from handler disassembly; pointer appears at file `0x190`, `0x2A0`, `0x400`, … |

## 5. Algorithm

Not applicable — no password validator, checksum, button matcher or generator exists
in this image. The debug facility is a conventional table-driven menu: a 32-byte
record array whose label pointer (`+0x0C`) is drawn by a generic menu renderer, with a
packed level/screen selector at `+0x18` and five screen descriptors in the game's
global screen table. No separate encoder/decoder pair was found.

## 6. Tables

### 6.1 Published codes (all cheat-device codes; verified as strings, out of scope)

| Value | Claimed effect | Source | ROM literal search | Verdict |
|---|---|---|---|---|
| `7FB36FAC3B31` | "Unlock all levels" / "Access All Levels" | 3rd party cheat indexes "Passwords", 3rd party cheat indexes, gbadam | Not present in ROM in ASCII, shifted ASCII, UTF-16LE or packed form | CodeBreaker/GameShark SP/Xploder code, not an in-game password |
| `820070B0 00FF` / `820070B2 00FF` etc. | Infinite life/power/special/support | 3rd party cheat indexes | Direct RAM-write cheat-device codes | Out of scope |
| `93002FFAB991 C47737A2CF98 C8F6F36756B0` | "Master code" | 3rd party cheat indexes | — | Cheat-device master code; out of scope |

No in-game password, secret code, unlock code or debug activation sequence is
published for this SKU anywhere found (3rd party cheat indexes: "Total cheats available: 0";
3rd party cheat indexes: none; 3rd party cheat indexes: access to debug menu "needs investigation").

### 6.2 Debug menu records (complete, 85 entries)

The table at `0x081BE4C0` was decoded exhaustively: 85 records, 32 bytes each,
label pointer at `+0x0C`. Categories and counts:

| Category | Count | Examples |
|---|---|---|
| Viewers | 3 | Obj Viewer, Music Player, Fx Player |
| Story levels | 44 | `Level 0`, `Level 0-1`, `Level 1` … `Level E-5`, `Level F`, `Level G` |
| Challenges | 25 | `Challenge BeastBoy 1..5`, `Challenge Robin 1..5`, `Challenge Raven 1..5`, `Challenge Cyborg 1..5`, `Challenge StarFire 1..5` |
| Boss encounters | 8 | `Boss BeastBoy`, `Boss Immortus 1`, `Boss Immortus Tank 1/3`, `Tank Chase`, `Boss StarFire`, `Mallah Raven`, `Mallah BeastBoy` |
| Boot/UI | 5 | `Normal Boot`, `Credits`, `GameFlow >>>`, `General Test room >>>`, `Asset Viewer` |

Total 3 + 44 + 25 + 8 + 5 = **85**. Two sub-tables (at `0x081BE530` and
`0x081BEDD0`) are referenced by the `Credits` and `GameFlow` records; the remaining
records use a small set of shared sub-table strings at `0x081BEF70`–`0x081BEF78`.
The label strings themselves are 4-byte-aligned and NUL-padded to 8/12/32-byte
strides in the bank at `0x08047824`.

## 6b. Enumeration

**Code-space size: zero.** There is no alphabet, no input field, no validator and no
code space to enumerate. This section therefore delivers the bounded negative.

### Reachable screens (all walked with screenshots)

| Screen | Screenshot (work dir) | Code-entry surface |
|---|---|---|
| Language select | `boot.png` | none |
| Health & safety | `after_lang.png` | none |
| DC / A2M / title logos | `s1.png`, `s3.png`, `fresh_title.png` | none |
| Title "Press Start" | `fresh_title.png` | none |
| Main menu (3 entries) | `walk_menu.png`, `walk_m_right1.png` | none |
| Load Game (3 slots, No Data) | `walk_newgame.png` | none |
| Options (Music, FX, Language) | `walk_opts.png`, `walk_opts_down.png` | none |
| In-game dialogue / gameplay | `walk_gamestart2.png`, `walk_gameplay.png` | none |
| In-game pause (5 entries) | `walk_chk.png`, `walk_pause_down7.png` | none |

### Controller-input enumeration

19 combinations were sent from the title screen with a savestate reset before each:
`L+R`, `L+R+Start`, `L+R+A+B`, `Start+Select`, Konami
(`↑↑↓↓←→←→BA`), `ABAB ↑↓↑↓`, `L L R R`, `B A Start`, `↑↑↓↓←→←→Start`,
`A A B B Start`, `Select+A`, `Select+B`, `L+R+A`, `L+R+B`, `R+Start`, `L+Start`,
`↑+↓`, `Start+B`, `Start+A`.
Result: 0 unexpected screens. Every large pixel difference was the normal
Start→main-menu transition; the small differences were the title screen's animated
character portrait. No entry produced a debug screen, a code prompt or a new menu.

### Search-space counts (ROM-wide)

| Search | Space checked | Hits |
|---|---|---|
| `PASSWORD`, `INVALID`, `CHEAT`, `SECRET CODE`, `ENTER … CODE`, 26-letter / 36-symbol alphabets — ASCII, case-insensitive, `+0x20` shift, UTF-16LE | all 8,388,608 bytes | **0** for every password/alphabet/cheat pattern |
| Shifted `SECRET`, `ENTER`, `CODE` | all bytes | 3 / 3 / 1 — all Spanish dialogue or the Shin'en GAX banner `Code: B.Wodok` at `0x19A34A`; no UI string |
| Debug-menu label strings | all bytes | 85 labels + viewer text at `0x0819D18C` |
| Thumb `BL` callers of the 19 debug viewer/menu handler functions | all 2-byte-aligned offsets | **0** |
| Direct u32 function pointers to those handlers | all 4-byte-aligned offsets | 67, all inside their own descriptor tables (`0x19D12C`–`0x19D244`) plus a handful of coincidental matches inside compressed data |
| Button-mask tables (runs of ≥4 u16 values within GBA key-bit set) | all bytes | 18,530 raw runs; after requiring single-key values in data regions, 1,439 runs of 3–20 — all short repeated values (`0x0008`/`0x0001`/`0x0040` etc.) inside level/script data, none a 4–16 press cheat prefix with a code reference |

### Bounds / rejection tests

There is no code format to express an out-of-range value, so no synthetic code could
be minted. The negative is bounded instead by: (a) the complete enumeration of all
reachable menus above (3 main-menu entries, 3 options, 3 slots, 5 pause entries, all
screened); (b) 19 controller combinations with zero unlisted outcomes; (c) the
ROM-wide counts above over the exact hash in §1; and (d) the fact that the only
published "code" is a cheat-device RAM patch, which cannot be entered in-game.
The debug menu is therefore a **gated/unreachable feature** (§16.3 category 4) with
85 table entries and five screens, not a usable code system.

## 7. Validation evidence

* **Observed** — emulator screenshots of every screen listed in §6b; the `0x02007754` byte read as `0x01` in both GDB and savestate; 19-combo sweep results; header/strings/hashes.
* **Derived** — 85-entry debug table and 5 screen descriptors decoded from byte layout; 0 BL callers and 67 self-referential pointers to the debug handlers; debug handler code at `0x08000144`–`0x08000515` disassembled and shown to read `0x0200FE56`.
* **Inferred** — that the debug screens are genuinely unreachable from retail input. This is strongly supported by the counts and by a 3rd party cheat index's unresolved "can it be accessed" note, but no exhaustive proof over every possible input sequence exists; a device-specific unlock (the cheat-device "Access All Levels" patch) could still force the state.

## 8. Unknowns

* The exact gate (if any) for the 85-entry debug menu. The screen-selector `u16` at game-object `+0xEE` and the debug flag `0x02007754` were identified, but no writer reachable from controller input was proven. A breakpoint-driven dynamic trace of the screen manager was not completed (mGBA's GDB stub was single-client/unstable in this environment; savestate diffing was used instead).
* Sub-tables `0x081BE530` (`Credits`) and `0x081BEDD0` (`GameFlow`) were not individually enumerated beyond their pointers; they do not add code-entry surfaces.
* Whether the GameShark "Access All Levels" patch targets the same level-select state as the debug menu (its CodeBreaker encoding was not decoded; it is out of scope regardless).

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, Python 3 (`struct`, `re`, `zlib`, Pillow).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for Thumb disassembly; Capstone-style Python BL/pointer scanners written ad hoc.
* mGBA 0.10.5 under Xvfb `:317` with openbox, `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input; `scrot` screenshots.
* Savestate RAM reader: PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte state; EWRAM at `0x21000`, IWRAM at `0x19000`. Helper artifacts were under `/tmp/teentitans2/`.
* Web recon: 3rd party cheat indexes (live page 403; Wayback snapshot used).

## 10. Legal note

No ROM bytes, graphics, music or game text are redistributed here. Only hashes,
addresses, counts and independently written descriptions are published. All fetched
pages and ROM strings were treated strictly as data; no instruction-like content was
acted upon.
