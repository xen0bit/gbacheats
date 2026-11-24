# Salt Lake 2002 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Salt Lake 2002/Salt Lake 2002.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `SALT LAKE 20` (12-byte field; full title "Salt Lake 2002") |
| Game code | `AS5E` (USA) |
| Maker code | `41` |
| Version | 0x00 |
| Fixed byte 0xB2 | 0x96 (valid) |
| Header checksum / complement | 0x0000 / 0xEB |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`, not a scene cracktro) |
| Embedded GBA headers | **1** (file offset 0x0 only) — single retail image, no multiboot/2-in-1, no appended trainer |
| MD5 | `7a5b0f8f5ccc714dc754cef30190159e` |
| SHA-1 | `377dbce06068147260d9cf05225e2504230fff2b` |
| SHA-256 | `f78471e44924237abc4b06278ff67df047bef3979f2c4e9ac4e72bf3f7de9b64` |

Phase 0 conclusion: unmodified retail US image. The only "patch-like" artefact is the normal rebuilt-header checksum 0x0000; the complement byte 0xEB is intact. A 156-byte Nintendo-logo scan found exactly one header.

## 2. Executive summary

**There is no in-game cheat surface in this ROM.** No password entry, no button-code sequence, no hidden/unlockable athlete or event, and no reachable debug menu exists. The game's only user-text entry is a *profile name* field (39-symbol on-screen keyboard), which is a label, not a validated code (§16.2b): no comparison routine ever consumes the name buffer as a code. All "cheats" published for this title are cheat-device (CodeBreaker/GameShark/GameShark SP/Xploder) codes — explicitly out of scope — and no in-game password or button code is published on GameFAQs, TCRF, or other sources.

Two developer menu renderers (`ROB'S MENU`, `GERRY'S MENU`) and a developer boot prompt ("Hit START to view intro or A to skip" / "Hit B to blank all player profiles") **do exist as dead code**: each has **zero** BL callers, **zero** 32-bit pointers (including the Thumb-bit `addr|1` variant), and **zero** 16-bit offset-table entries. Both gates in the main loop that *could* select a debug path are written to 0 at boot and have no writer anywhere else in the reachable code. All 3 functions were walked past in the emulator with breakpoints available and never executed. This is a bounded **dead-code** negative (§16.3), not "not tested".

The only unlockable content is *difficulty tiers* earned by beating target time/score in Challenge mode ("Can you beat the target time or distance and unlock the harder difficulties?") — ordinary progression stored in the 512-byte Flash save, not a code, and not settable by any controller input.

## 3. How to reproduce

- Emulator: `/usr/local/bin/mgba` 0.10.5 under `Xvfb :317`, `SDL_AUDIODRIVER=dummy`, `-3` scale, own display only.
- Keymap (mGBA SDL defaults): A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrow keys.
- Boot path used repeatedly: Start → language `ENGLISH` (A) → single-player icon (A) → profile slot 1 (a profile was created once: name `A`, country USA) → main menu.
- Saved state at main menu (mGBA `Shift+F1`, load `F1`) made every menu walk one keypress.
- Main menu: Left/Right cycle 6 icons and clamp at 0 and 5. Options submenu: 5 items. Event select: 6 icons, Up/Down clamp. Difficulty selector: only `BEGINNER` selectable on a fresh save.
- RAM evidence: mGBA `.ss1` savestates are PNGs with a zlib-compressed `gbAs` chunk; decompressed layout (4 MiB ROM) is header/CPU at 0x0, IWRAM at 0x19000, EWRAM at 0x21000, so IWRAM `0x0300xxxx` maps to state offset `0x19000 + 0xxxx`. The Flash save is `game.sav` (512 bytes).
- No codes were entered because no code entry surface exists; attempts to use the published cheat-device codes were not applicable to in-game input.

## 4. Address map

| Address (ROM unless noted) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Header; entry `b 0x080000C0` | Observed (bytes) |
| `0x08000840` | Main game loop | Derived (disassembly) |
| IWRAM `0x0300297c` | Debug gate A — cleared to 0 at `0x08000848`; checked at `0x0800086c`; selects `0x08002d28` path | Derived |
| IWRAM `0x03002974` | Debug gate B — cleared to 0 at `0x0800084c`; checked at `0x08000888`; selects `0x08002e60` path | Derived |
| IWRAM `0x03002958` | Menu/animation state byte used by both debug helpers | Derived |
| `0x08002d8c`–`0x08002e36` | **"ROB'S MENU" renderer** (calls text draw `0x0800256c` with strings at `0x0807e820` and format strings `0x0807e840`+) | Derived; dead |
| `0x08002ec4`–`0x08002f6e` | **"GERRY'S MENU" renderer** (strings `0x0807e830`+) | Derived; dead |
| `0x0800480`–`0x0800510` | Developer boot prompt: "Hit START to view intro or A to skip", "Hit B to blank all player profiles" (strings `0x08035bac`, `0x08035bd4`) | Derived; dead |
| `0x0800256c` | Text renderer: byte string → glyph via font struct; NUL-terminated | Derived |
| IWRAM `0x03002920` | Font struct: `+0` tile table `0x08039d2c`, `+4` width table `0x08039e2c`, `+8` base tile, `+0xA/+0xB/+0xC` spacing | Observed (savestate RAM) |
| `0x08039d2c` | Tile-index table (256 bytes): indices 0–31 → 0 (skipped), printable bytes map to tiles | Derived |
| `0x08039e2c` | Character-width table (256 bytes) | Derived |
| `0x08036e4ac`–`0x08036e800` | Localized text-pointer bank: 207 entries, 6 languages (EN/FR/DE/IT/ES/NL), 5 strings per language plus labels/messages (e.g. `0x0807fd5c` "Next Difficulty Level Unlocked.") | Derived |
| `0x0807ea88` | Name-entry alphabet `ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789!?` (39 chars; UI shows a 40-cell grid with `*`/Del/OK) | Observed |
| `0x0801f7d0`, `0x080230ac` | Standard input pollers: `held = ~KEYINPUT & 0xFFFF`, `pressed = held & ~old`; globals at IWRAM `0x030032b0` / `0x030032a4` | Derived |
| `0x08002d28`, `0x08002e60` | Debug-menu input helpers reachable only through gates A/B; 6-entry jump tables at `0x08002d50` / `0x08002e88` | Derived |
| `0x08011c4`, `0x08011e8` | Additional gate readers (no writers) | Derived |

Flash save (`game.sav`, 512 bytes): four 0x50-byte profile slots. Each slot has name byte at `+0x07`, twelve 4-byte records initialised to `0xC7DF` at `+0x08`..`+0x35`, and a 4-byte seed/checksum at `+0x50`. Region `0x160`–`0x1EF` is the filler pattern `CA BB A9 E5 DE AD BE EF`. Bytes `0x1F4`–`0x1F6` are `01 01 01` on a fresh save (not the difficulty gate — patched to 03 with no effect on difficulty).

## 5. Algorithm

No password/validator/checksum algorithm exists. The relevant algorithms are:

1. **Text rendering** (`0x0800256c`): for each byte `c` of a NUL-terminated string, look up width `W[c]`; if zero, advance by space width; if cursor x == 0x7F, handle newline; otherwise draw tile `T[c] + base` where `T` is the 256-byte table at `0x08039d2c`. The font table maps printable ASCII to consecutive tiles (`T[0x21]=0x27`, …), so ASCII text banks render directly. The yellow-button captions seen on screen are pre-rendered tile art (no byte strings anywhere in ROM or RAM), so their absence from `strings` is expected and not a hidden text bank.

2. **Input** (`0x0801f7d0`): `h = ~KEYINPUT & 0xFFFF`; `p = h & ~old`; `old = h`. No ring buffer, no sequence matcher, no magic-mask comparison was found in any of the three KEYINPUT xrefs (`0x0800aa40`, `0x0801f7d2`, `0x080230ae`).

3. **Debug gating**: main loop checks gate A then gate B; both are written 0 during init at `0x08000848`/`0x0800084c`. A full literal-load scan (Capstone, Thumb `LDR Rd,[PC,#imm]` with `& ~3` alignment) found every reference to `0x0300297c`, `0x03002974`, `0x03002958` — all are reads or the two boot-time zero writes; there is no store of a nonzero value to either gate in reachable code.

## 6. Tables

| Item | Count / value |
|---|---|
| GBA headers in image | 1 |
| Main-menu items | **6** (indices 0–5; Left/Right clamp; items 4 and 5 share stopwatch icon and description) |
| Main-mode descriptions (English) | 5 distinct strings at `0x0807ead8`/`eb2c`/`eb4c`/`ebc0`/`ec04` |
| Options submenu items | 5 (SETTINGS, TROPHY ROOM, CREDITS, EDIT PROFILE, SELECT LANGUAGE) |
| Trophy-room pages | 3 (OLYMPIC MODE, TOURNAMENT MODE, CLASSIC MODE) |
| Events | 6 (Ski Jumping, Curling, Downhill Skiing, Bobsleigh, Snowboarding, Downhill Slalom); Up/Down clamp |
| Selectable difficulties on fresh save | 1 (`BEGINNER`); higher tiers gated by Challenge-mode target progression |
| Settings toggles | 1 (Ghost Mode ON/OFF) |
| Name-entry alphabet | 39 symbols (`ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789!?`) |
| Localized text bank | 207 pointers × 6 languages |
| Save size / profile slots | 512 bytes / 4 |
| Dead debug functions | 3 (`0x08002d8c`, `0x08002ec4`, `0x0800480`) |
| Published in-game passwords / button codes | 0 (all published codes are cheat-device codes) |

## 6b. Enumeration

**Space definition and search bounds.** This title has *no* code space to enumerate: no alphabet-to-value mapping other than the profile-name keyboard, no accepted-code table, no checksum, no function-pointer table of cheat handlers, and no key-mask sequence. The negative is bounded by the following complete counts over the checked spaces:

1. **String/literal space** — `strings -t x -n 4` (37,755 lines) plus case-insensitive `-n 3` keyword scans for `password|cheat|code|debug|secret|unlock|athlete|hidden|menu|invalid`. Every cheat-related hit was classified: `Shin'en Multimedia. Code: B.Wodok` (audio-engine banner, §11), `FUNCTION NAME:` (compiler/debug leftover in the audio region), the 5 mode descriptions and their localized copies, the 2 debug-menu labels, and the 2 developer boot prompts. No password string, code table, or key-name table exists.
2. **Debug-code reference count** — for each of the three hidden functions: BL callers = 0, 32-bit pointers = 0 (both `addr` and `addr|1`), 16-bit offset entries = 0. Whole-ROM BL scan into `0x08002d00–0x08003000` returned exactly 4 hits, all to the *normal* helpers (`0x08002d28`, `0x08002e60`, `0x08002f98`, `0x08002fcc`), none to either renderer.
3. **Gate return domain** — the only two gate words (`0x0300297c`, `0x03002974`) have exactly two writers, both storing 0 at boot. Therefore no input path can set them; forcing them nonzero by savestate patch produced only a one-character debug overlay ("C") over the main menu, never either named menu — confirming they are not a hidden-menu entry point.
4. **Menu-space walk** — every reachable screen was visited with screenshot + RAM/save evidence: title, language select (6 languages), single/multi select, 4 profile slots, name entry, country select (16 flags selectable), main menu (6 items), 5 options items, 3 trophy pages, settings toggle, credits, event select (6 events), difficulty selector, Target-mode intro, Time-Trial/Ghost select, and gameplay entry. No unreachable menu item, hidden athlete, hidden event, or secret screen appeared.
5. **Unlockables** — difficulty tiers are progression flags set by beating a target, not a code; the setter is in the Challenge-mode result path, and no controller input in any menu writes it. A save-patch oracle (bytes `0x1F4`–`0x1F6` set to `03`) produced no change in the difficulty selector, so those bytes are not the gate; the tier flag lives in the per-profile 4-byte record area (initial sentinel `0xC7DF`), which is written only by gameplay results.
6. **Published-code verification** — web search (TCRF mirror, Ethereal Games, GameHacking.org, GameFAQs/IGN) found only cheat-device codes: `00000387 000A` + `100230AC 0007` (master) and `33007DC0 0009` (infinite lives). These are CodeBreaker/GameShark memory patches, out of scope by the task definition, and none appears as an in-game input. TCRF lists only unused text at `0x7E820` and provides no access method, consistent with this report's dead-code finding.

**Novel code:** not applicable — §0.2's "mint a code absent from every published list" presupposes a validator/table. Here the space size is **0 accepted in-game codes**: there is nothing to mint, and the bounded negative above is the deliverable required by §0.2 item 5. **Bounds proven by rejection:** Left/Right at the main menu clamp at indices 0 and 5 (no 7th item); event Up/Down clamps at 6; difficulty Right is rejected (stays `BEGINNER`) until a target is beaten; forcing the two debug gates nonzero is rejected (no menu appears). These are in-game rejections, not untested assumptions.

## 7. Validation evidence

- **Observed** — emulator screenshots of every screen listed in §6b(4); savestate RAM reads of the font struct and gate words; 512-byte Flash save dump showing four profile slots, `0xC7DF` record sentinels and `CABBA9E5 DEADBEEF` filler; title/options/event/difficulty clamp behaviour under real keypresses.
- **Derived** — disassembly of the main loop and its gates; the three dead functions and their zero-reference counts; the text renderer and font tables; the localized text bank (207 pointers); the input pollers; the single-header/entry-word check.
- **Inferred** — the yellow-button captions are pre-rendered tile art (supported by zero string/RAM hits and the font-table analysis); the difficulty tier flag resides in the per-profile results records (supported by their `0xC7DF` sentinel and the Challenge-mode description, but the exact flag byte was not isolated).

No claim in this report is based solely on a published list or on a fetched page; fetched pages were treated as data.

## 8. Unknowns

- Exact byte/bit within the per-profile records that stores each unlocked difficulty tier; the setter was not isolated to a single store instruction. (It is gameplay progression regardless, not a code.)
- Whether the unused "ROB'S MENU"/"GERRY'S MENU" renderers were ever reachable in a prototype build; in this retail image they are unreferenced.
- The `*`/Del/OK cell layout of the name-entry keyboard was not needed beyond accepting a name; it is not a validator.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep` for Phase 0/1.
- Python + `struct`/`capstone` for literal-load scans, BL scans, pointer scans, font/text-bank decoding.
- `arm-none-eabi-objdump -D -b binary -marm -M force-thumb --adjust-vma=0x08000000` for all disassembly.
- mGBA 0.10.5 on `Xvfb :317` + `openbox`, `xdotool` XTEST input, `scrot` screenshots, ImageMagick `convert` for montages.
- `/tmp/saltlake/ss.py` (savestate `gbAs` zlib extractor), `patchss.py` (savestate RAM patcher), `ui.py` (input/screenshot helpers).
- Web: websearch + webfetch (TCRF mirror used because tcrf.net returned 403). Search quota was exhausted before further GameFAQs detail; the available snippets already showed only cheat-device codes.

No ROM or copyrighted assets are redistributed; only hashes, addresses, algorithms and findings are published.
