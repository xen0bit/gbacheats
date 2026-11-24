# Tak 2: The Staff of Dreams (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tak 2: The Staff of Dreams.gba` (8,388,608 bytes / 0x800000) |
| `file` | `Game Boy Advance ROM image: "TAK&JUJUENG" (BT9E78, Rev.00)` |
| Header title | `TAK&JUJUENG` (0xA0) |
| Game code | `BT9E` (0xAC); maker `78` = THQ (0xB0) |
| Version | `0x00`; fixed byte `0x96` present; entry branch `0xEA000031` |
| Header checksum | `0x0000`; complement `0xB0` |
| MD5 | `05b2267bdf77e3d36d0b96c22d3af844` |
| SHA-1 | `f90219db6359332eb997a2717986a8c66eaded2b` |
| SHA-256 | `573bc027e97fe95b24d3e0b209fcc077b76e43fea85d6d62b73d6320ac5aed6b` |

The header is an intact retail image (no cracktro/trainer patch: standard entry word and intact
`0x96`/complement — guide §16.1). **SKU matters here:** this is the Helixe 2D-GBA build, not the
Avalanche 3D console build (§16.11). 3rd party cheat indexes all confirm GBA = Helixe, 2D
platformer, 1 player; GC/PS2/Xbox = Avalanche.

## 2. Executive summary

**Bounded negative: this GBA ROM contains no in-game code/password system, no controller
button-code system, and no controller-reachable hidden/debug menu.** There is consequently no
validator to reverse and no novel code to mint; the finding is a *counted* negative (§0.2, §16.3).
Evidence:

1. **All UI text is enumerated** — three complete string banks of exactly **321 string IDs each**
   (English at `0x08477438`, French `0x08479E3A`, German `0x0847AB8E`), each a `u16` offset table
   followed by NUL-terminated, 1-byte-prefixed ASCII. Every ID was scanned: **zero** labels for
   PASSWORD / CODE / CHEAT / DEBUG / OPTIONS / LEVEL SELECT / NAME ENTRY / UNLOCK / WARP in any
   language. The only menu labels are THE END, OK, CANCEL, NEW GAME, Continue, PRESS START,
   ERASE, OLD GAME?, PAUSED, QUIT, QUIT?, Yes/No, MOVE, SELECT, GAME OVER, Empty, PLAY, SHOP,
   YES, NO, EXIT, COMPLETE, plus level and item names.
2. **No code-entry surface.** The on-screen glyph set (`0x084B9AC`) is exactly
   `0123456789`, `QRSTUVWXYZ`, `ABCDEFGHIJKLMNOP` — 36 symbols (0–9, A–Z) and no special symbols;
   it is the dialogue font, not an on-screen keyboard. No screen with a text field was reached.
3. **No button-code tables.** Scans of the whole 8 MiB found **465** raw button-mask run
   candidates, only **13** with any 32-bit literal xref; all 13 are coincidental byte patterns
   inside compressed graphics/level blocks (e.g. `0x026F11B`, `0x0288BB3`, `0x02A1316`), not
   code tables. **0** plausible cheat sequences.
4. **No debug markers.** ASCII and `+0x20`-shifted searches for `debug`, `level select`,
   `password`, `cheat`, `unlock`, `warp`, `master code` all returned **0** hits. (The word
   "secrets" occurs once, in ordinary dialogue: `0x084797AA`.)
5. **No name-based developer trick.** The 512-byte save has no player-name field (magic `TAK2`
   at `+0x04`, then progress data), so the Helixe `HELIXE`-name level select known from the GBA
   *Scooby-Doo* games has no input surface here.
6. **Published-code recon:** 3rd party cheat indexes state "We currently don't have any ... cheats or
   cheat codes for Game Boy Advance"; the archived 3rd party cheat indexes GBA cheats page lists exactly one
   item, a *Yorbel Game* dial-timing gameplay trick (not a code system). The widely published
   "Universal Card" numbers (`48,62,19` etc.) belong to the console SKU and are **absent** from
   this ROM: zero ASCII hits for `UNIVERSAL`, `CARD`, `BUGS`, `CRYSTAL`, `FRUIT`. Action Replay
   codes found on 3rd party cheat indexes are cheat-device codes and out of scope.
7. **Developer leftovers do exist but are unreachable:** the test level name
   `JTest TEST Test.` is present in all three string banks (English `0x08480EE`), and scene names
   `credits_level`, `map_level`, `menu_level`, `minigame_level` survive, but no controller path,
   menu label, or code reaches them. No live L/R level-select behavior on the map screen.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold 150–300 ms; re-focus the window after each screenshot.
* Screen path: THQ splash → title "PRESS START" (`Return`) → intro/dialogue (press `x` repeatedly)
  → **main menu**. With no save: 1 item (NEW GAME). With a save: 2 items (CONTINUE, NEW GAME);
  pressing Down at NEW GAME wraps to CONTINUE, proving the item count is 2.
* In-game: `Return` → **PAUSED** menu (CONTINUE / QUIT, 2 items) → Down + `x` → **QUIT?**
  confirm (YES / NO, 2 items). Selecting CONTINUE from the main menu loads the save and shows
  the **map** screen (`TUTORIAL`); L and R were pressed there with no change (no level select).
* Input map verified by disassembly: the handler at `0x0803CB80` maps 10 buttons to indices
  using masks A=`0x01`, B=`0x02`, Select=`0x04`, Start=`0x08`, Right=`0x10`, Left=`0x20`,
  Up=`0x40`, Down=`0x80`, R=`0x100`, L=`0x200`; no sequence-comparison logic.
* Save state: mGBA `.ss1` parsed with the `gbAs` zlib chunk method (§16.13); raw state is
  397,312 bytes; header at raw `0x0`, IWRAM at `0x19000`, EWRAM at `0x21000`.

## 4. Address map

| Item | Address (ROM/file) | Evidence |
|---|---|---|
| Entry / crt0 | `0x08000000` (`EA000031`) | Derived (header) |
| Save magic writer literals (`2KAT`) | `0x08015920`, `0x080159DC`, `0x08015A48`, `0x08015B98`, `0x08015BE4` | Derived |
| Input update / key→index map | `0x0803CB80`–`0x0803CBEE` | Derived (Thumb disasm) |
| Per-button edge/repeat handler | `0x0803C9B4`–`0x0803CB60` | Derived |
| Input init | `0x0803CC68` | Derived (BL from `0x08041F50`) |
| KEYINPUT literal `0x04000130` | file `0x3CC4C`, `0x3CCC8` | Derived |
| English string-ID table | `0x08477438`, 321 `u16` IDs | Derived |
| French string-ID table | `0x08479E3A`, 321 IDs | Derived |
| German string-ID table | `0x0847AB8E`, 321 IDs | Derived |
| English UI strings | `0x084776BE` onward | Observed (screenshots) + Derived |
| Font glyph rows | `0x084B9AC`–`0x084B9C6` | Derived |
| Credits / developer names | `0x084B000`–`0x084BA00` | Derived (strings) |
| Save file | 512 bytes; magic `TAK2` at `+0x04` | Observed (mGBA `.sav`) |

## 5. Algorithm

Not applicable — **no validator, generator, checksum, or code table exists in this ROM.** The
relevant "algorithm" is the bounded-negative search described in §6b and the standard input
mapping in §3/§4.

## 6. Tables

**Complete menu-label inventory (English; French/German are translations of the same 321 IDs):**

| Screen | Labels |
|---|---|
| Title | PRESS START |
| Main menu (no save) | NEW GAME |
| Main menu (save) | CONTINUE, NEW GAME |
| Pause | PAUSED, CONTINUE, QUIT, MOVE, SELECT |
| Quit confirm | QUIT?, Yes, No |
| Map | level name only (e.g. TUTORIAL); no menu items |
| Other labels present | THE END, OK, CANCEL, ERASE, OLD GAME?, GAME OVER, Empty, PLAY, SHOP, YES, NO, EXIT, COMPLETE |

Absent from all three banks: PASSWORD, CODE, CHEAT, DEBUG, OPTIONS, LEVEL SELECT, NAME,
UNLOCK, WARP, SECRET (as UI), EXTRA, BONUS.

**Font/glyph alphabet (`0x084B9AC`):** `0123456789` + `QRSTUVWXYZ` + `ABCDEFGHIJKLMNOP` = 36
symbols (0–9, A–Z). No `!`, `?`, `-`, `#` etc., so the 32-symbol style of Car Battler Joe is not
present.

**Save layout (512 bytes):** `+0x00..03` unknown/zero; `+0x04..07` = `"TAK2"`; `+0x10..` progress
flags (`FF FF 00 AB ...`); no name string, no code slot.

## 6b. Enumeration

This engagement is a **bounded negative**, so the "space" is the candidate cheat surface that was
searched and counted, not a code space.

| Search space | Size / method | Result |
|---|---|---|
| UI string IDs (3 languages) | 321 × 3 = 963 IDs, 1-byte-prefixed ASCII, keyword scan all | 0 code/debug/name/options labels |
| Font symbol set | 36 glyphs (`0x084B9AC`) | No on-screen keyboard; no special-symbol alphabet |
| Whole-ROM ASCII keyword scan | 8,388,608 bytes, case-insensitive + `+0x20` shift | 0 `debug`, `password`, `cheat`, `level select`, `unlock`, `warp`, `master code`; 1 incidental "secrets" in dialogue |
| Whole-ROM UTF-16LE/BE keyword scan | 8 MiB | 0 hits |
| Button-mask run candidates | 465 raw runs of ≥4 distinct single-bit key masks followed by a terminator | 0 code tables |
| ... xref-filtered | 13 candidates with a 32-bit literal reference | All inside compressed asset blocks; 0 in code |
| Password alphabets | 5 canonical patterns (A–Z, 0–9, consonants, reversed) | 0 on-screen-keyboard alphabets; only the font rows and coincidental data |
| Menus walked live | Title (1), main no-save (1), main with-save (2), pause (2), quit-confirm (2), map (0), gameplay/dialogue (0) | No hidden/unlabelled entry; selector wraps at the observed bounds |
| Save-file name field | 512 bytes, magic at +4 | None → no name-triggered developer cheat |

**Novel code:** none exists to mint. A code system requires an alphabet + entry UI + validator;
all three are absent, so no value can be accepted or rejected. **Bounds proven by rejection:**
not applicable for a code system; the equivalent negative bound is the exhaustive string-ID and
mask-sequence enumeration above (zero candidates in the searched spaces).

**Positive in-game trick (not a code system, recorded for completeness):** the sole published GBA
cheat (3rd party cheat indexes, contributor supersid) is the *Yorbel Game* dial trick — at the `SPIN?` prompt
choose YES, and while the triangular dial revolves press A on the item **opposite** the desired
one to stop it there. It is a gameplay timing exploit in a minigame, not a password/button code;
it was not exercised because reaching the Yorbel game requires story progression (see §8).

## 7. Validation evidence

* **Observed** — mGBA screenshots: title, intro, main menu with and without save, pause, QUIT?
  confirm, map, gameplay. `tak2.sav` (512 B, `TAK2` magic). mGBA savestate `gbAs` chunk decompressed
  to 397,312 B; header shows `TAK&JUJUENG` / `BT9E`, EWRAM/IWRAM contents read.
* **Derived** — Thumb disassembly of the input handler (`0x0803CB80`) and the three 321-entry
  string tables; all scan counts in §6b; save-magic literals at `0x080159xx`.
* **Inferred** — the `JTest TEST Test.` level name and `*_level` scene names are developer
  leftovers; no reachable path was found, so their intended access method is unknown.
* **Tooling caveat** — the mGBA GDB stub (`-g`) produced "Ignoring packet error" and crashed the
  core on connect, so RAM evidence uses savestate diffs (§16.13) and the `.sav` file instead.

## 8. Unknowns

* Live screens not walked (require full playthrough): Yorbel Store/shop, Yorbel Game minigame,
  credits, game over, item/power-up switch UI. Their labels are present in the enumerated string
  bank and none is a code-entry UI, but they were not visually confirmed.
* The exact trigger (if any) for the leftover `Test TEST Test.` test level is unknown; it is not
  reachable from any menu label or from L/R on the map screen.
* A code gate faster than the title reset window (§16.12) cannot be fully excluded without a
  frame-by-frame input sweep; with zero debug strings, zero mask tables and zero code-entry UI,
  such a gate would have no observable effect and is treated as out of scope.

## 9. Tooling

* `strings -t x`, `grep -abo`, `xxd`, Python `re`/`struct` scanners
  (`scan.py`, `scan_structs.py`, `targeted_scan.py`, `banks.py`, `textbanks.py`).
* `arm-none-eabi-objdump -D -b binary -marm -M force-thumb --adjust-vma=0x08000000` for input code.
* mGBA 0.10.5 under Xvfb `:316` + openbox; `xdotool` XTEST input; `scrot` screenshots;
  savestate `gbAs`/zlib parser (`parse_state.py`).
* All artifacts and scripts were in `/tmp/tak2`; screenshots `s*.png`, `m2_*.png`.
* No ROM or copyrighted assets are redistributed; this report contains only hashes, addresses,
  algorithms and counts.
