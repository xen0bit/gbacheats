# Tweety & the Magic Gems (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tweety & the Magic Gems.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `TWEETY MAGIC` |
| Game code | `ATME` |
| Maker code | `7F` |
| Fixed byte `0xB2` | `0x96` |
| Software version | `0x00` |
| Complement (`0xBD`) | `0x00` |
| Header checksum (`0xBE`) | `0x004A` |
| Entry word | `0xEA00002E` → stock crt0 at `0x080000C0` (no cracktro/trainer) |
| MD5 | `2a76e96be1fdb58ea4e4bafa62556a5a` |
| SHA-1 | `cb892ac87ee4fcd627949d23ce66acd56ec00feb` |
| SHA-256 | `078096c1c312875ce40ee82c640faff34f748d298db2e5a93e49a80c71669419` |
| Publisher / developer | Kemco / Kotobuki System, 2001 |

## 2. Executive summary

**Finding: bounded negative.** This SKU has no in-game/developer-intended cheat surface — no
password, no button code, no hidden/debug menu, and no unlockable gated behind a code. The only
published "cheats" are cheat-device RAM patches (CodeBreaker/Action Replay) and one 3rd party cheat indexes
gameplay tip; both are out of scope per the brief. The game is a Mario Party-style board game with
exactly one code-like surface, the five-icon board toolbar, and every entry in it is documented
in the game's own tutorial.

Evidence for the negative is fourfold:

1. **Text banks fully decoded.** The in-game font is *not* ASCII: every glyph is a tile index with
   `glyph_index = ASCII + 0x3F`, and the word separator is byte `0x6F` (not `0x5F`). After decoding
   the whole text bank (`0x38B000`–`0x399500`, 2,150 unique strings), literal counts are
   `PASSWORD=0, DEBUG=0, CHEAT=0, SECRET=0, CODE=0, BONUS=0, UNLOCK=0, WARP=0, LEVEL SELECT=0`.
   The only `SERVICE` hit is ordinary city trivia ("cable car started its service in 2984").
2. **Screen walk complete.** Title (4 entries), tutorial MENU (10 entries + RETURN), 6-character
   select, player/difficulty setup (EASY/MEDIUM/HARD), board, all five board icons, city/shop,
   Juke Box (51 tracks, enumerated to wrap), Game Link status screen. No hidden entry point.
3. **No button-code table.** Konami-style u16/u32 mask strings searched in both active-high and
   raw active-low forms: 0 hits. The ROM's input history buffer at `0x03000A88` is a two-frame
   ring used by the normal D-pad/A repeat logic; its companion "code" buffer at `0x03000C20` is
   all zeros in both the title-screen and in-game savestates. The state machine at `0x08001B4C`
   has 5 branches, none of which is a cheat dispatcher.
4. **Dynamic button-code tests.** 13 combinations on the title screen and 13 during gameplay
   (including L+R, L+R+Start, A+B+Start+Select, Konami, L/R+Start, 10×A, 10×Select, Start×2)
   produced only documented menu transitions and map zoom; no new screen, flag, or overlay.

Because no code system exists, there is no validator to reverse and no novel code to mint. Section
6b records the bounded negative with explicit counts instead.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, `Xvfb :316`, `openbox`, `-3` scale.
* Default SDL keymap: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`,
  D-pad = arrow keys. Hold keys ~60–90 ms; menus double-step on longer holds.
* Boot path used: boot → KEMCO logo → story pages (A) → tutorial MENU → RETURN TO TITLE SCREEN →
  title. Character select needs A on a portrait, then A again on the star animation, then YES on
  the "IS THIS OK?" screen, then SLOW/NORMAL/FAST, then OK.
* Savestates used as reset points: slot 2 (title, cursor on GAME LINK PLAY), slot 4 (title, cursor
  on HOW TO PLAY), slot 5 (board, mid-game). Hotkeys: `F<n>` load, `Shift+F<n>` save.
* Button-combo harness: `combotest.py` (title) and `gamecombos.py` (board), both in the work dir.
  Each run loads a slot, performs one recorded sequence, waits 0.6 s, and captures the 720×480
  viewport at `+154+184`.

## 4. Address map

| Address | Type | Meaning | Evidence |
|---|---|---|---|
| `0x08000000` | ROM | Entry `0xEA00002E`, stock crt0 | Observed (header dump) |
| `0x08001288` | Thumb fn | Low-level byte/IO reader used by boot code | Derived (BL xrefs) |
| `0x08001344` | Thumb fn | Counter/timer updater for 4 slots | Derived |
| `0x08001390` | Thumb fn | Boot-time A/B/Start key check plus `0x03000C20` value test against `0x8100`/`0xFF00` (save-data shaped, not a code validator) | Derived |
| `0x08001490` | Thumb fn | Writes two-frame input history: `0xFC00+count` tag at `0x03000A88`, `~KEYINPUT & 0xFFF7` mask at `0x03000A8A` | Derived |
| `0x08001B4C` | Thumb fn | 5-entry jump table state machine (`0x08001B68`); states call `0x08001390`, `0x0800129C`, or `0x08009AC`. No cheat branch. | Derived |
| `0x08009AC` | Thumb fn | Sound/SFX setup (writes sound registers), **not** a comparator despite being called with `0x03000A88`/`0x03000C20` pointers | Derived |
| `0x03000860` | IWRAM | Main engine/global struct (first bytes `FF 00 … FF 00`); `+0x60` holds held-key mask | Observed (savestate) |
| `0x03000900` | IWRAM | Engine state byte (`0x00` at title, `0x01` in game) | Observed |
| `0x03000A88` / `0x03000A8A` | IWRAM | Input-history ring: tag `0xFF00`, mask `0x8000` | Observed |
| `0x03000C20` | IWRAM | 4×8-byte companion buffer, all zeros in both states | Observed |
| `0x03000F88` | IWRAM | `0x00` at title, `0x01` in game | Observed |
| `0x02000B04` | EWRAM | Moves remaining (`0` on board) — the target of the published CodeBreaker patch | Observed |
| `0x38B000`–`0x399500` | ROM | Encoded text bank (`glyph = ASCII + 0x3F`, space = `0x6F`) | Derived, decoded |

## 5. Algorithm

**Text encoding (the only nontrivial format found).** For a byte `b` in the text bank:

```
c = (b - 0x3F) & 0xFF
if b == 0x6F: c = ' '          # word separator
elif 0x20 <= c < 0x7F: render glyph c
else: control/punctuation glyph (0x7E, 0xFA, 0xFD, 0xFF, 0xC9, ...)
```

`strings` returns nothing for the game text because of this offset; the header title is the only
plain ASCII run. Decoder (a one-line `bytes.translate`) produced the 2,150-string inventory used
for the keyword counts in §6b.

**Input history.** `0x08001490` stores a moving two-slot history of the active-high keypad value
with bit 3 (Start) excluded: `slot[i].tag = 0xFC00 | frame_counter`, `slot[i].mask = ~KEYINPUT &
0xFFF7`. This is a debounce/repeat aid, not a code matcher: no ROM table of expected sequences is
referenced by any of the five handlers in `0x08001B4C`.

## 6. Tables

**Published material (recon, all verified as non-in-game):**

| Source | Content | Disposition |
|---|---|---|
| 3rd party cheat index cheats | 1 "secret": pulling an Ace or 7 lets you pick a card's item for free | Gameplay tip, not a code |
| 3rd party cheat indexes / libretro | 2 CodeBreaker codes (`0000693E 000A`, `10025E10 0007`; `D0000020 0004`, `33000B04 000A`) | Cheat-device RAM patches — out of scope |
| 3rd party cheat indexes | 8 Action Replay codes (gems, points, "AR Butt For 10 Moves") | Cheat-device patches — out of scope |
| 3rd party cheat indexes | No page exists for this title (403 / no article) | No published debug-menu claim |

**In-game enumerations:**

| Surface | Count | Items |
|---|---:|---|
| Title menu | 4 | HOW TO PLAY, SINGLE PLAYER, GAME LINK PLAY, JUKE BOX |
| Tutorial MENU | 10 + RETURN | OBJECT OF THE GAME, MODES, HOW MANY PLAYERS?, ICONS, NAVIGATION, HOW TO ENTER A CITY, GEMS, SHOP, MINI GAMES, MATCH GAMES, RETURN TO TITLE SCREEN |
| Characters | 6 | Sylvester, Bugs Bunny, Daffy Duck, Yosemite Sam, Marc Antony, Porky Pig |
| Difficulty | 3 | SLOW (EASY), NORMAL (MEDIUM), FAST (HARD) |
| Board icons | 5 | Cards, Items, Routes, System, Guide (per in-game tutorial) |
| Juke Box tracks | 51 | Enumerated by 51 Right presses to first-track wrap; includes TITLE, INTRO 1/2, ENDING, city and minigame themes |

## 6b. Enumeration

This section states the searched space and proves the negative with counts, as required by §0.2
for a no-code result.

**Code space:** empty. There is no alphabet, no code length, no checksum, no comparison table, and
no entry widget anywhere in the reachable UI. Consequently the representable-code count is 0, not
a finite field to enumerate, and the "mint a novel code" step is inapplicable.

**Enumerator results (counts, not impressions):**

| Check | Space examined | Result |
|---|---|---|
| Decoded text keywords | 2,150 unique strings over `0x38B000`–`0x399500` | `PASSWORD` 0, `DEBUG` 0, `CHEAT` 0, `SECRET` 0, `CODE` 0, `BONUS` 0, `UNLOCK` 0, `WARP` 0, `LEVEL SELECT` 0, `TEST MODE` 0 |
| Short code-like tokens | All `\b[A-Z0-9]{4,10}\b` tokens in the text bank | 100% ordinary words (top: POINTS 128, WORLD 115, HERITAGE 95); zero isolated password-shaped tokens |
| Konami mask sequence | 10 presses × (u16, u32) × (active-high, active-low) = 4 literal searches | 0 hits |
| Keypad literal `0x04000130` | 4 MiB scanned | 4 hits: `0x14DC` (code), `0x25E3C`, `0x25E1A5`, `0x25E801` (data) |
| Button-code state machine | 5 branches at `0x08001B68` | 0 cheat/unlock branches; all 5 are normal input/SFX/save handling |
| Input-history companion buffer | `0x03000C20`, 8 bytes, read from title and in-game savestates | `00 00 00 00 00 00 00 00` in both — no stored sequence |
| Title-screen button combos | 13 sequences, each from a fixed slot-4 reset | 0 hidden screens; only HOW TO PLAY / Game Link transitions |
| In-game button combos | 13 sequences, each from a fixed slot-5 reset | 0 hidden screens; only map zoom / card draw / pause |
| Juke Box | 51 selection steps to wrap | 51 tracks, no unlabeled slot, no hidden 52nd entry |
| Character select | All 6 portraits | All available at boot; no gated/hidden 7th slot |

**Rejection/bound tests:** not applicable — with no validator there is no accepted set to bound and
no checksum to violate. The equivalent bound here is that exhaustive keyword and mask searches
return zero and that every reachable menu entry was opened.

## 7. Validation evidence

* **Observed**: all screenshots in `/tmp/tweety/` (`tbase_crop.png`, `combo_montage.png`,
  `gcombo_montage.png`, `jb2_crop.png`, `jr*_crop.png`, `w2_crop.png`, `bb8_crop.png`, etc.);
  savestate-derived IWRAM/EWRAM reads; emulator response to all 26 button sequences.
* **Derived**: text-bank encoding, function boundaries and branch counts from `objdump -M
  force-thumb`, literal-pool values re-read with `struct.unpack_from`, keypad mask semantics.
* **Inferred**: that `0x08001390` is save-data validation rather than a code check (its constants
  `0x8100`/`0xFF00` and the all-zero buffer are consistent with that, but no save-generation path
  was exercised). This does not affect the negative: neither path is reachable from controller
  input.

## 8. Unknowns

* `0x08001390`'s precise role (save-data check vs. boot self-test) was not pinned down; its two
  constants are not button masks and its companion buffer stays zero in both examined states.
* The 51 Juke Box track names were captured while their marquee was scrolling; a few long names
  were read only by prefix. This does not affect the count (wrap was observed at step 51).
* No retail-vs-"DEMO" build comparison was made. The `DEMO` badge is drawn on every screen as
  artwork and is not present in the decoded text bank, so it is not a debug-menu label.

## 9. Tooling

* Tools: `arm-none-eabi-objdump` (`-M force-thumb`/`force-arm`), Capstone, Python 3 (`struct`,
  `zlib`, Pillow), mGBA 0.10.5 SDL with `-3`, `-g` and `-d`, `xdotool`, `scrot`, ImageMagick,
  Xvfb `:316` + openbox, GDB.
* Scripts in `/tmp/tweety/`: `key.py` (XTEST input), `combotest.py`, `gamecombos.py`
  (button-combo harnesses), `ptydbg.py`, `ptyrun.py` (mGBA pty-debugger drivers), plus the
  one-off text decoder and savestate `gbAs` extractor.
* Savestate parsing: `.ss*` files are PNGs with a zlib `gbAs` chunk; the decompressed 397,312-byte
  blob has IWRAM at `0x19000` and EWRAM at `0x21000`, which is how the RAM reads above were taken
  without relying on the GDB stub.

**Legal note:** no ROM bytes or copyrighted assets are reproduced here; only hashes, addresses,
algorithms, counts, and observations are published.
