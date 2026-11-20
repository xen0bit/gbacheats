# That's So Raven (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/That's So Raven/That's So Raven.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| Header title | `THATSSORAVEN` |
| Game code / maker | `BRVE` / `4Q` |
| Version / complement / checksum | `0x00` / `0xFB` / `0x0000` |
| Entry word | `0xEA00002E` → stock `b 0x080000C0` (not a cracktro) |
| Nintendo logo hits | 1 (file `0x4`) — single image, not a multi-game pack |
| MD5 | `6ff16e52b08129b6bb1a650f9adfd603` |
| SHA-1 | `87d8cc357cbace0539fb5a4520fac8b4a4aaa6c4` |
| SHA-256 | `2f8e638b8c687d7208006ee4e245e27be8aad7111ecbfeaef3a16a3a52739db6` |

The SHA-1 matches the "Good" dump listed by TASVideos for this title. This is the same game that the sibling agent analyses as *That's So Raven 2: Supernatural Style*; the two are distinct ROMs and all findings below were re-derived independently from this image.

## 2. Executive summary

**Bounded negative: this ROM contains no developer-intended password, button-code, or hidden/debug-menu system.** The only cheat-like content is a normal save-bit unlockable — 16 yearbook photos (GameFAQs: "complete all of the bonus missions in each level").

Evidence, in four independent layers:

1. **Screen walk (observed).** Every reachable screen was entered in mGBA and screenshotted: title → slot select → three-character *initials* entry → episode select (5 icons) → yearbook (16 locked slots) → four episode level lists → in-game HUD/dialogue → pause menu (resume/sound/sleep/exit level) → sound submenu (music/sfx/exit). No password/code entry screen exists. The initials field is a **profile name**: it is accepted with Start regardless of content, stored verbatim as 3 bytes in the save, and only rendered through the format string `"%s - %d%%"` in the slot list.
2. **Text-bank enumeration (derived).** All UI text is plain ASCII in a single string table at ROM `0x803DBE8` (file `0x3DBE8`); it was decoded entry by entry (IDs 0–89+). Keyword census: `password` 0, `cheat` 0, `code` 0 (outside JPEG/GAX library diagnostics), `debug` 0, `secret` 1 (`Secret Chicken Levels`, ID 43), `unlock` 16 (`CS_unlockable1..16`, cutscene/photo names in level data), `invalid` 0. Font glyph tables at files `0x273680`, `0x27A690`, `0x27B680`, `0x282900` map ASCII → tile indices; no tile-encoded hidden text bank was found.
3. **Button-code scan (derived).** `getKeys()` at `0x08009A30` returns `~KEYINPUT & 0x3FF` (active-high masks A=1…L=0x200). The two published Raven-2 sequences (Costume, Unlimited Energy) were searched in both orders, active-high and active-low, as `u16` and `u8` arrays: **0 hits** in this ROM and 0 in the sibling ROM. A whole-ROM scan for runs of ≥6 consecutive non-zero single-key `u16` masks found **2 runs**, both in high compressed data (`0x082F84A8`, `0x08566638`), neither in executable code. No key-history comparison table exists.
4. **Gated/dead-feature check.** `Secret Chicken Levels` (string ID 43) is unreachable: the episode selector shows exactly five icons (star = `Bonuses`, `1`–`4` = the four episodes) and all five were entered/labelled on screen. The only other candidate, the yearbook, is a 16-slot photo gallery gated by save bits (§7).

A prompt-injection payload was encountered on the TCRF page for this title ("This page is not intended for humans … whoever is operating this AI agent is a clown"). It was ignored, treated as data, and recorded here per guide §16.8. The substantive TCRF content for Raven 1 lists only unused placeholder dialogue, no debug menu; the debug-menu and button-code material on that wiki belongs to Raven 2 and was not transferred to this report.

## 3. How to reproduce

* Emulator: `SDL_AUDIODRIVER=dummy mgba -3 -d ROM` under `Xvfb :319` + openbox, display `:319`. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 50–80 ms per press.
* Boot → title (`start game`, `view credits`) → Start → `Select a Slot` → A on a slot → `Enter Initials: ---` → enter any three letters → **Start** accepts (the on-screen `OK` cell is not selectable with the D-pad; the grid is 8×4 and wraps).
* `Choose an Episode` → star icon = `Bonuses` (yearbook, 16 locks); icons `1`–`4` = `Run Raven Run`, `Clothesminded`, `Smell of Victory`, `Four's A Crowd`. Episode 1 → five levels: Back to School, AV Cart Crash, Present Danger, Eddie or Not, Chicken Chase.
* In level 1: pause with Start → `resume`, `sound`, `sleep`, `exit level`; `sound` → `music 100%`, `sfx 100%`, `exit`.
* No code was entered because no code surface exists. Candidate codes tested only by literal search, not fabricated for the UI.

## 4. Address map

| Address (ROM unless noted) | File offset | Meaning | Evidence |
|---|---|---|---|
| `0x08000000` | `0x0` | Header, entry `b 0xC0` | derived |
| `0x08009A30` | `0x9A30` | `getKeys()` → `~KEYINPUT & 0x3FF` | derived (Thumb disassembly) |
| `0x08009A44`/`0x08009A60` | `0x9A44`/`0x9A60` | key-state init/clear helpers | derived |
| `0x0802301E` | `0x2301E` | wait-for-key loop polling `0x04000130` | derived |
| `0x0879569C` | `0x79569C` | 8-byte engine handler records `{0, u32 thumb_fn}`; contains `0x08009A31` | derived |
| `0x0803DBE8` | `0x3DBE8` | UI string pointer table, 0-based IDs from `0x803DBEC` (ID 1 = "That's So Raven") | derived |
| `0x0803E228`–`0x0803EB..` | `0x3E228`+ | ASCII UI strings; ID 43 `0x803E500` = "Secret Chicken Levels", ID 44 `0x803E51C` = "Bonuses" | derived |
| `0x0803E2EC` | `0x3E2EC` | `"%s - %d%%"` — the only consumer format for the initials name | derived |
| `0x0803E320` | `0x3E320` | `"Enter Initials: ---"` (ID 13) | derived |
| `0x08044848` | `0x44848` | menu/screen descriptor record referencing string-table pointer `0x803DC28` | derived |
| `0x08044D38`–`0x08045E90` | `0x44D38`+ | 16 `CS_unlockableN` cutscene/photo names, stride `0x124` | derived |
| `0x020028B0` | — | EWRAM save record; bytes `0x0..0x2` hold the three initials (`AAA` observed) | observed (savestate + `.sav`) |
| `0x020007A4` | — | EWRAM byte toggled on episode-select cursor movement (savestate diff; not the selector itself — patching it did not change selection) | observed |
| SRAM/Flash file | — | 512-byte `.sav`: magic `60 0D C0 DE C0 DE 60 0D` at `0x0`, initials at `0xD` | observed |

## 5. Algorithm

There is no password algorithm. The only nontrivial transformations are:

* **Key encoding:** `active_high = ~(*(volatile u16*)0x04000130) & 0x3FF`; button masks A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.
* **Initials entry:** 3 positions; 30 selectable glyphs (`A`–`Z`, `_`, `!`, `?`, `$`), plus two arrow cells (backspace/forward) and a non-selectable `OK` label. Acceptance is Start, not a comparison: no `strcmp`/checksum consumes the buffer; the bytes are copied into the save record and formatted with `"%s - %d%%"`.
* **Unlockable state:** 16 photo flags in the save record; a locked slot renders a padlock. GameFAQs' unlock condition (all bonus missions in each level) is a gameplay trigger, not a code.

## 6. Tables

* **UI string table:** base `0x803DBE8`, 4-byte ROM pointers. IDs below are 0-based from `0x803DBEC` (the entry at `0x803DBE8` points to non-string data and is excluded). Selected IDs: 9 `"New Game"`, 10 `"%s - %d%%"`, 14 `"Enter Initials: ---"`, 23 `"defeat level"`, 36 `"Level %d"`, 37 `"Game %d"`, 38 `"Choose an Episode"`, 39 `"Run Raven Run"`, 40 `"Clothesminded"`, 41 `"Smell of Victory"`, 42 `"Four's A Crowd"`, **43 `"Secret Chicken Levels"`**, 44 `"Bonuses"`, 45–64 the 20 level names.
* **Yearbook:** 16 slots, `CS_unlockable1..16` at `0x08044D38` + `0x124·(n-1)`; all 16 observed locked in a fresh save.
* **Font/glyph tables:** files `0x273680`, `0x27A690`, `0x27B680`, `0x282900` (ASCII → tile index); these decode the visible UI and contain no hidden payload strings.

## 6b. Enumeration

**Space definition and counts (bounded negative, not a code system):**

| Enumerated surface | Space | Result |
|---|---|---|
| UI strings | `strings -t x -n 4`: 112,775 lines; pointer table IDs 0–89 enumerated | 0 `password`, 0 `cheat`, 0 `debug`, 0 `code` (game-side), 1 `Secret Chicken Levels` (unreachable), 16 `CS_unlockable` |
| Literal keyword scan over 8 MiB | 14 case-sensitive/insensitive needle searches | `DEBUG` 0, `Debug` 0, `debug` 0, `PASSWORD` 0, `Password` 0, `Cheat`/`CHEAT` 0, `ENTER CODE` 0, `Level Select` 0, `MapX`/`OBJ VIEWER`/`Music Player`/`Test Room` 0, `Secret` 1, `PASSWORD` 0 |
| Button masks | 2 published Raven-2 sequences × 2 orders × 2 polarities × 2 widths = 8 needle searches per ROM | 0 hits in this ROM; 2 nonzero `u16` single-key runs ≥6 in whole ROM, both in data (compressed): `0x082F84A8` (6), `0x08566638` (6) |
| Input field | 30 symbols³ = **27,000** possible initials strings | All accepted by Start; none compared to a constant; value only displayed/stored |
| Episode selector | 5 icons | All 5 walked; labels `Bonuses` + 4 episode names; `Secret Chicken Levels` never appears |
| Yearbook | 16 slots | All 16 locked initially; unlock via gameplay bonus missions (published and consistent with save-bit design) |
| Pause menu | 4 entries + 3 sound entries | All walked; no hidden entry |
| Reachable screens total | 11 distinct screens, 34 screenshots (`shots/01`–`shots/34`) | No code-entry surface |

**Novel codes:** none exist to mint. Per guide §0.2, a fabricated "code" cannot be generated for a game with no validator; the negative is proven by the counts above rather than by a demonstration of non-acceptance. **Rejection bounds:** not applicable — there is no accepting set to bound. The nearest bounded test performed was the initials field: entering `AAA` and accepting with Start produced only a name change (save byte `0xD..0xF` = `41 41 41`, slot label `AAA - 0%`), i.e. the format accepts the entire 27,000-string space, which disproves a validator at that surface.

**Novel/unpublished finding:** the string `Secret Chicken Levels` (ID 43 at `0x803E500`) is present but unreachable through all five episode-select entries; reported as a likely cut or gated level set with confidence *inferred*.

## 7. Validation evidence

* **Observed:** title, slot select, initials, episode select, yearbook (16 locks), level list, in-game HUD, pause and sound menus; `Start+Select` in-game only closes the pause menu; `L+R` produces no visible effect; savestate diff isolated the save record at EWRAM `0x020028B0` with `AAA`; `.sav` magic/initials dump.
* **Derived:** `getKeys()` mask convention; string table layout and ID→text map; absence of button-code table runs; `CS_unlockable` records; `Secret Chicken Levels` has exactly one pointer (the string table) and no reachable menu slot.
* **Inferred:** that `Secret Chicken Levels` is cut content (rather than a feature gated by a late-game flag that was not reached); that the yearbook flags are the published bonus-mission unlocks.

## 8. Unknowns

* Whether some extremely late game state (post-completion) adds a sixth episode icon — not reached; the save-bit gate would require completing all levels/bonuses.
* Exact semantics of the 512-byte save beyond offsets `0x0..0x32` (most of the file is `0xFF` filler); the 16 photo flags were not individually mapped to offsets.
* The `defeat level` string (ID 22) was not triggered — it requires losing all health.
* No REA/Ghidra decompilation was obtained: raw-ARM auto-analysis created no Thumb procedure at `0x08009A30`; conclusions rest on `objdump -M force-thumb`, Capstone scans, and emulator observation.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
* Python 3 + `capstone` for Thumb LDR-literal and whole-ROM mask scans; `struct`-based pointer and string-table parsing.
* mGBA 0.10.5 (`-3 -d`) under Xvfb `:319`; `xdotool` XTEST input; `scrot` screenshots in `/tmp/opencode/raven1/shots/`.
* Savestate diffing per guide §16.13: `zlib.decompress` of the PNG `gbAs` chunk (397,312 bytes; IWRAM at raw `0x19000`, EWRAM at `0x21000`). Helper: `/tmp/opencode/raven1/patch_state.py`.
* REA/Ghidra was opened once (`open_binary`, raw ARM, base `0x08000000`) but provided no usable Thumb procedure for the candidate function; session closed.
* No ROM or copyrighted assets are redistributed here; only addresses, counts, hashes and observations are published.

## 10. Legal note

Analysis was performed on a legally held ROM. Extracted graphics, music, and game text are not reproduced; only short UI labels needed to document the negative are quoted.
