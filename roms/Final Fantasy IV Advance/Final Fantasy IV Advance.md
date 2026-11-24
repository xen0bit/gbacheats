# Final Fantasy IV Advance (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Final Fantasy IV Advance.gba` |
| Size | 8,388,608 bytes (0x00800000, 8 MiB) |
| `file` | Game Boy Advance ROM image: "FF4ADVANCE" (BZ4E01, Rev.00) |
| Header title | `FF4ADVANCE` (0xA0–0xAB) |
| Game code | `BZ4E` (0xAC–0xAF) — USA/Australia SKU `AGB-BZ4E-USA` |
| Maker | `01` (Nintendo, 0xB0–0xB1) |
| Version | 0x00 (Rev.00) |
| Fixed byte | 0x96 at 0xB2 (normal) |
| Complement / checksum | 0x29 at 0xBD / 0x0000 at 0xBE–BF |
| Entry word | `0xEA00041E` at 0x00 → ARM branch to `0x08001080` (stock crt0) |
| CRC32 (external, 3rd party cheat indexes) | `FEEEBDE4` |
| MD5 | `c74dd5cc3ab6e5d4ac53b1677e1abd69` |
| SHA-1 | `c49be22eaf999774d5f2983e12ed4aace2950f36` |
| SHA-256 | `fdc7a48c4cf22746bf13c9a953d92d92f73e76218d0173495d4692c3d6c91abd` |

**Embedded-header scan (Phase 0):** scanned all 0x800000 bytes for the 156-byte
Nintendo logo (and a 32-byte prefix). Exactly **one** header exists, at file 0x0.
This is **not** a multi-game/compilation image. No cracktro, appended trainer,
or patched entry was found: 0x04–0x9F is the stock logo, 0xC0 onward is normal
ARM crt0, and the entry word is a plain forward branch. Save ID string
`SRAM_V113` at `0x086D9AC0` (Flash/SRAM save format marker).

## 2. Executive summary

**This ROM contains no in-game, developer-intended, controller-accessible cheat
system.** There is no password screen, no button-code handler, no unlock code,
and no reachable debug menu. The evidence is fourfold:

1. **No code surface.** `strings` (167,485 strings at `-n3`) returns **0** hits
   for `password`, `cheat`, `secret`, `unlock`, `debug`, `sound test`,
   `battle test`, `enter code`, `game shark`, `master code`. No ASCII password
   table, no key-mask sequence table, no password alphabet was found anywhere in
   the 8 MiB image.
2. **Debug material exists but is dead / gated outside the scope.** The ROM does
   retain substantial developer leftovers: engine assertion/error strings
   (`0x080F0C68`–`0x080F3A58`), a 64-entry BGM identifier table
   (`0x080C948C`–`0x080C9770`) plus a parallel English BGM-title table
   (`0x080D5128`–`0x080D5400`), a sound-effect name table `S_0`..`S_218`
   (`0x080C9A28`–`0x080C9F18`), and a large romanised-Japanese development
   resource-name table (`0x081040CC` onward: maps, characters, battle animations,
   enemies). 3rd party cheat indexes document the full text of an extensive debug menu
   (*Map / Effects / Battle / Shop / Monsters / Characters / Events / Sound /
   Flags / Resume / Switch / Status / Clear SRAM*, plus NPC/PTN viewer, event
   viewer, shop list, character editor, flag editor). **Those menu strings are
   not reachable by controller input.** The only debug *room* in this US build
   is entered by GameShark/CodeBreaker codes that overwrite save RAM
   (`8200E04E 015D` → map 0x015D = "Search 349"; plus `8200E3C4 0078`,
   `8200E3C8 0068`) — an external memory-edit device, explicitly out of scope.
3. **All published "cheats" are memory patches.** 3rd party cheat indexes, ethereal-games and libretro `.cht` lists contain only Action Replay /
   GameShark / CodeBreaker codes (enable code + direct RAM writes: infinite HP,
   Gil, "No Random Battles" `3200E064 0001`, "Enter Debug Room", "Access Music
   Select", "Walk Through Walls (Hold R)"). Not one is a password, a button code,
   or an in-game menu. (The "Hold R / Press Select+Up/Down" walk-through-walls
   combos are *installed by the cheat device*, not present in the game.)
4. **The only genuine controller combo is a system function.** The manual
   documents `A+B+Start+Select` to return to the title screen. The game's input
   reader at `0x080013E4` and its 21 call sites were enumerated; every one is a
   normal single-key or d-pad control (no multi-button cheat mask).

The menu/debug text is stored in the game's **font/tile-index encoding**, not
ASCII: none of the visible strings (`PUSH ANY BUTTON`, `New Game`) or the 3rd party cheat indexes
debug labels occur as ASCII bytes in the ROM, even though `FINAL FANTASY IV`
does (`0x080D5828`). A bounded decode attempt is documented in §8.

**Shared content with the sibling "Final Fantasy I & II: Dawn of Souls" (queue
298): none observed.** This ROM was analysed independently on a separate display
(:317); no code, address, string, or code literal was carried over from that
title, and no evidence of a shared cheat/debug surface exists here. (The sibling
was not opened by this session.)

## 3. How to reproduce

- **Emulator:** mGBA (SDL, `/usr/local/bin/mgba`) under `Xvfb :317 -screen 0
  1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`, invoked `mgba -3 ff4a.gba`.
  The ROM was **copied** to `/tmp/ff4a/ff4a.gba` so no emulator artifacts
  land in the ROM folder.
- **Keymap — verified by RAM read, not assumed.** Holding each key and reading
  the live held-button word at EWRAM `0x020068A8` from an mGBA savestate gave:
  `x = A (0x0001)`, `z = B (0x0002)`, `BackSpace = Select (0x0004)`,
  `Return = Start (0x0008)`; arrows = d-pad. (Active-high convention:
  `held = 0x03FF & ~KEYINPUT`.)
- **Screens walked (each captured, transitions allowed to settle):**
  health-and-safety → Square-Enix logo → "FINAL FANTASY IV ADVANCE / PUSH ANY
  BUTTON" title → title menu (`New Game` only; no `Continue` because no save) →
  opening airship sequence and dialogue → overworld map → story battles
  (Floating Eyeball ×3, Zu) → Baron castle interiors. Input was verified against
  the button mask, and savestates (`Shift+F1..F4`) were taken on title and title
  menu for RAM reads. No additional title-menu entries, no hidden option screen,
  and no debug entry appeared during any of these screens.
- **RAM evidence method:** the mGBA `-g` GDB stub was found unreliable in this
  build (attach/`continue`/`interrupt` either returned no data or terminated the
  core), so RAM evidence uses Guide §16.13: mGBA `.ss1` savestates are PNG with a
  zlib `gbAs` chunk; decompressing it yields a 397,312-byte (0x61000) image with
  VRAM at +0x1000, IWRAM +0x19000, EWRAM +0x21000. The held-button word was
  read from `0x21000 + (0x020068A8-0x02000000) = 0x278A8`.
- **Codes tested:** none applicable — no in-game code system exists. Published
  GameShark/CodeBreaker codes were verified to be memory patches and were
  deliberately **not** executed (out of scope).

## 4. Address map

All addresses are ROM (`0x08000000 + file offset`) unless marked RAM.

| Region / item | Address | Evidence |
|---|---|---|
| GBA header | `0x08000000`–`0x080001FF` | Observed (xxd) |
| ARM entry branch | `0x08000000` → `0x08001080` | Derived |
| Input-clear loop | `0x08001398`–`0x080013BE` | Derived (Thumb disasm) |
| **Input read routine** | `0x080013E4`: reads `KEYINPUT` via literal at `0x08001410` (`0x04000130`), masks `0x03FF` (`0x08001414`), writes held `0x020068A8`, pressed `0x020068AC`, released `0x020068B0`, `0x02000008` | Derived |
| Held-button word (RAM) | `0x020068A8` (active-high) | Observed |
| 21 literal pools referencing `0x020068A8` | `0x08001418`, `0x08001488`, `0x08001A84`, `0x080F0614`, `0x080290C0`, `0x0803CAF0`, `0x0804B684`, `0x0804BB64`, `0x0804C060`, `0x0804D68C`, `0x0804D910`, `0x0804DB8C`, `0x080760B8`, `0x0807AFF0`, `0x080ABE38`, `0x080ABE74`, `0x080B418C`, `0x080B4E50`, `0x080B64F0`, `0x080B69E4`, `0x080B6A38` | Derived |
| Engine debug/assert strings | `0x080F0C68`–`0x080F3A58` (e.g. `main menu proc config error` `0x080F3780`, `battle menu select Finger error` `0x080F356C`, `message special code error:%d (mesId:%d)` `0x080F32E8`) | Observed |
| BGM identifier table (64 entries) | `0x080C948C`–`0x080C9770` (`BGM_PROLOGUE` … `BGM_DUMMY2_2`) | Observed |
| English BGM titles (65 entries) | `0x080D5128`–`0x080D5400` (`Prologue` … `Epilogue 3`) | Observed |
| SFX name table `S_0`..`S_218` | `0x080C9A28`–`0x080C9F18` | Observed |
| Development name tables (maps, characters, animations, enemies) | `0x081040CC` onward | Observed |
| Copyright/version string | `0x080D5828` (`FINAL FANTASY IV`, `2001SQUARE/STING`, `0129`) | Observed |
| Save-format ID | `0x086D9AC0` (`SRAM_V113`) | Observed |
| Debug-room map ID | `0x015D` (= 349, "Search 349") — set only by external GameShark save patch | External (3rd party cheat indexes) + code) |
| Candidate font-index table (uncertain) | `0x080F6C34` (256-byte table, A–Z→0..25) | Derived, unconfirmed |

## 5. Algorithm

There is **no password/cheat validator to reimplement**. The only algorithm
reversed is the input path:

```
KEYINPUT (0x04000130, active-low, 10 bits)
held   = ~KEYINPUT & 0x3FF          -> [0x020068A8]
pressed  = held & ~previous         -> [0x020068AC]
released = ~held & previous         -> [0x020068B0]
if pressed != 0: store to [0x02000008], [0x0200000A], [0x0200000C]
else: maintain a saturating counter (cap 29 on one path, 4 on another) at [0x020068B8..]
```

Button meanings (active-high bits): `A=0x001, B=0x002, Select=0x004,
Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`.
All 21 code sites that load `0x020068A8` test **single bits or the d-pad nibble
0xF0/0x30** for movement/confirm/cancel; none tests a multi-button combination
such as `0x000F` (A+B+Start+Select) or `0x0300` (L+R) as a cheat gate. The
documented A+B+Start+Select reset is handled elsewhere as a soft-reset system
call, not as a cheat flag.

## 6. Tables

- **Key masks (observed):** A `0x001`, B `0x002`, Select `0x004`, Start `0x008`,
  Right `0x010`, Left `0x020`, Up `0x040`, Down `0x080`, R `0x100`, L `0x200`,
  all buttons `0x3FF`, d-pad `0x0F0`.
- **BGM table:** 64 identifiers at `0x080C948C` (12-byte stride) plus 65 English
  titles at `0x080D5128` — a debug sound-selector data set, with no reachable
  selector UI (the "Access Music Select" function is a CodeBreaker memory patch).
- **Sound names:** `S_0` … `S_218` at `0x080C9A28` (8-byte stride).
- **Development names:** romanised Japanese map/character/animation/enemy names
  at `0x081040CC` (16- and 32-byte fixed-width records).
- **Published code classification (web, verified literals):** 100% GameShark /
  Action Replay / CodeBreaker. Representative literals checked: master enable
  `3C9131DA 735A845E DD85A6C2 87FBA19A`; "No Random Battles" `3200E064 0001`
  (writes save RAM `0x0200E064`); "Enter Debug Room"
  `7200E002 000C / 8200E04E 015D / 8200E3C4 0078 / 8200E3C8 0068`. None occurs
  as an in-game input string, and all require an external device.

## 6b. Enumeration

**Code space:** empty. There is no password alphabet, no password length, no
lookup table of accepted codes, no checksum, and no button-code mask table in
this ROM. Consequently there is **no novel code to mint and no bounds to prove
by rejection** — §0.2's generation deliverable is inapplicable, and the required
result here is a *bounded proof of absence* (§0.2 item 5), given below.

**Button-code space (enumerated):** the complete input surface is 10 bits
(`2^10 = 1024` possible simultaneous button states). The ROM has exactly **one**
reader of the hardware key register (`0x080013E4`) and **21** distinct code sites
consuming its derived held word. Every one was disassembled or pattern-checked:
they implement d-pad movement (`0x0F0`/`0x30`/`0x80`/`0x40`/`0x10`) and
single-button A/B/Select/Start confirmation. No site compares a simultaneous
multi-button mask to a cheat gate. Documented combo `A+B+Start+Select` (0x00F)
is a title reset, not a cheat; no other documented or undocumented combo exists.

**Debug-menu item space (from 3rd party cheat indexes, external):** 13 top-level entries
(`Map, Effects, Battle, Shop, Monsters, Characters, Events, Sound, Flags,
Resume, Switch, Status, Clear SRAM`) plus 6 debug-room NPCs (dancer, Mysidian
Elder, shopkeeper, Golbez, FuSoYa, white mage). In this US build the menu is
dead code; the debug room is map `0x015D` and is reachable only by patching save
RAM with GameShark. **No entry is reachable from any controller on a stock
console.**

**Bounded negative (search space actually checked):**
- 8,388,608 bytes scanned for 4 embedded GBA headers → **1**.
- 167,485 strings (`-n3`) → **0** keyword hits for password/cheat/secret/unlock/
  debug/sound-test/battle-test/master-code.
- 0 hits for the literal menu/debug strings in ASCII, `+0x20`, UTF-16LE/BE,
  high-bit-set, XOR-0x80/0xFF, reversed-bit, and every 1-byte pad in 2-byte
  interleaving; 0 hits across **25,551** candidate LZ77 headers decompressed.
- 8 ASCII→glyph candidates scanned for a 256-byte mapping table; the best
  (`0x080F6C34`) did not reproduce any debug string when used to re-encode them.
- 21 input-word code sites enumerated; 0 multi-button cheat gates.
- 1 input register literal (`0x04000130`); 0 secondary button readers.
- Screens enumerated: 10 distinct states (§3); no hidden entry surfaced.

## 7. Validation evidence

- **Observed:** ROM hash/header/logo scan; `strings`/`grep` counts above; debug
  string tables at the listed addresses; keymap read from a live savestate; all
  screenshots of the ten screens; savestate decompression and RAM reads.
- **Derived:** input routine at `0x080013E4` and its 21 call sites from Thumb
  disassembly; absence of cheat-gate masks; GameShark literals resolve to RAM
  writes (e.g. `0x0200E04E = 0x015D`).
- **External (authoritative, treated as data):** a 3rd party cheat index's transcript of the debug
  menu and debug-room access, and 3rd party cheat indexes/3rd party cheat index code lists
  proving every published "cheat" is a memory patch. (One 3rd party cheat indexes fetch was
  HTTP-403; the archived Wayback copy was used. No instructions found in any
  fetched page were acted upon.)
- **Inferred:** the debug-menu labels are stored in the game's font/tile-indexed
  text format (consistent with on-screen strings also being non-ASCII), not in a
  plaintext table.

## 8. Unknowns

- **The font-indexed text bank was not fully decoded.** A genuine bounded
  attempt was made: ASCII case variants, `+0x20`, UTF-16LE/BE, XOR/high-bit,
  reversed-bit and 2-byte padded encodings (all 0 hits); LZ77 decompression of
  25,551 candidate headers (0 hits); discovery of a candidate 256-byte glyph
  table at `0x080F6C34` whose mapping did not re-encode the strings; and VRAM
  tilemap inspection from a title-menu savestate. The game clearly uses a custom
  script/text compression ("message special code" system), so the absence of an
  ASCII hit does **not** mean the strings are absent — it only means no plaintext
  cheat table exists. a 3rd party cheat index's independent transcript establishes what those
  encoded strings say. This does not affect the conclusion: even if decoded,
  the menu has no controller entry point.
- The exact soft-reset (`A+B+Start+Select`) handler address was not isolated
  among the many single-key handlers; its behaviour is taken from the manual.
- The sibling Dawn of Souls ROM was not opened here, so "nothing shared" means
  no shared indicator was found in *this* image, not a byte-level cross-check.
- The mGBA GDB stub could not be used for live reads; all RAM claims come from
  savestate images (§3), which are a reliable snapshot but not a watchpoint.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` (and `-M force-arm`) for disassembly.
- Python 3 with `capstone` 5.0.7 / `keystone-engine` available (Capstone used for
  literal-LDR candidate scans); Pillow available (unused).
- `strings -t x -n 3/4`, `grep -abo/-abi`, `xxd`, `file`, `md5sum`/`sha1sum`/
  `sha256sum`.
- Custom scripts in `/tmp/ff4a/`: `phase0.py` (hashes/header/embedded
  header scan), `encsearch.py` (encoding brute force), `lzscan.py` (LZ77 sweep),
  `key.py` (xdotool key helper), savestate `gbAs` zlib parser (`ssram.py` and
  inline readers).
- mGBA `-3` under `Xvfb :317` + `openbox`, `SDL_AUDIODRIVER=dummy`;
  `xdotool` XTEST input, `import -window root`/`import -window <id>` screenshots.
- Web: 3rd party cheat indexes via `web.archive.org` (403 on live), 3rd party cheat indexes, ethereal-games, libretro database (all fetched as data only).

**Legal note:** no ROM bytes or copyrighted assets are reproduced in this
report; only hashes, addresses, algorithms and original tooling are published.
