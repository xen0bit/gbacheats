# Snood (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Snood/Snood.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `SNOOD` |
| Game code | `ASQE20` (region: USA) |
| Maker | `20` (Destination Software) |
| Version | `0x00` |
| Header checksum | `0x0000` (normal rebuilt-header artifact); complement `0x42` |
| Entry word | `0xEA00002E` → `b 0x080000C0` (stock, unpatched) |
| MD5 | `66f4a5a101822a779fdfecf366e73c96` |
| SHA-1 | `2c09548ae924ac0c1a3e15412d9a7aae7707a753` |
| SHA-256 | `2a52f77c0d01a37236265218b5125effbe5260b7d0c3e1d9c145d37a44122379` |

**Embedded-header scan (Phase 0):** scanning the whole image for the 156-byte Nintendo
logo (`24 ff ae 51 ...`) yields exactly **one** hit, at file offset `0x0`, whose
header is `SNOOD / ASQE20`. There is no second game image, no appended trainer,
no boot selector and no cracktro. The entry word and crt0 are stock. The only
unusual content is a 1 KiB developer "padding" message at file `0x349E0C`
(ROM `0x08349E0C`), which is data (credits/trivia), not a cheat.

## 2. Executive summary

**The original 2001 GBA *Snood* has no in-game cheat, password, button-code,
hidden-mode or debug-screen system.** Every reachable screen was booted and
walked with RAM evidence, and the static search spaces that could contain such a
system were enumerated: ASCII/encoded strings, single key-input read sites,
key-mask sequence tables, comparison sites, and the tile-indexed UI text system.
The counts are in §6b.

This is a *bounded negative*, not an untested guess:
* the GameFAQs "Enter password / level codes" lists found by web search belong to
  **Snood 2: On Vacation** (game code different, 2005, Gravity-i) — a different
  game (§16.11 of the guide). The only published cheat material for this SKU is
  **Action Replay RAM-patch codes**, which are an external cheat device and
  explicitly out of scope. GameFAQs game id `565768` (this game) lists no codes;
  there is no TCRF page for it.
* the game's UI text is **sprite/tile-indexed**, never ASCII; all encodings tried
  (ASCII, `+0x20`, UTF-16LE/BE, reversed, single-byte add/XOR, and five common
  permutation alphabets) contain **zero** occurrences of `PASSWORD`, `DEBUG`,
  `SECRET`, `CHEAT`, `LEVEL SELECT`, `UNLOCK` or similar.
* only **one** location in the whole ROM reads the joypad register, and it is a
  plain edge-detector; there is no multi-press matcher.

Since no code system exists, §0.2's "mint a novel code" step is replaced by the
mandatory bounded-negative enumeration (§6b): all 8 screen states, all 3+4+8+4+5+2
menu values and all search spaces are counted, and common published button
sequences were entered in-game and rejected.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 at `/usr/local/bin/mgba`, `DISPLAY=:317`,
  `SDL_AUDIODRIVER=dummy`, `Xvfb :317 -screen 0 1024x768x24`, `openbox`,
  `mgba -3 roms/Snood/Snood.gba`.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
  arrows = D-pad. Hold 80–300 ms (menus debounce; 0.3 s can double-step).
* Boot path: Destination Software splash → title `Snood / PRESS START TO PLAY`.
* Screen walk (each step verified by screenshot and by savestate RAM read):
  1. Title: press Start.
  2. Main menu: `SINGLE PLAYER`, `TWO PLAYER`, `OPTIONS`.
  3. `OPTIONS`: `GAME TYPE` (PUZZLE / TIME ATTACK / JOURNEY / CLASSIC),
     `DIFFICULTY` (CHILD / EASY / MEDIUM / HARD / EVIL; greyed out in PUZZLE and
     TIME ATTACK), `MUSIC` (ON / OFF), `SELECT CHARACTER`.
     Values change with Left/Right; A exits.
  4. `SELECT CHARACTER`: 8 characters — Jake, Spike, Geji, Numb Skull, Zod,
     Mildred, Sunny, Midoribe — then wraps to Jake.
  5. `SINGLE PLAYER`: Snood Factory cutscene → board. Puzzle mode shows
     `LEVEL 1`; Classic mode shows the difficulty banner ("MEDIUM").
  6. Start/Select/B in gameplay: **no pause menu** in either Puzzle or Classic.
  7. `TWO PLAYER`: `MULTIPLAYER / LOOKING FOR HOST / PRESS B BUTTON TO CANCEL`
     (link mode; B returns to the main menu).
* Button-code tests at the title screen: the full Konami sequence
  `Up Up Down Down Left Right Left Right B A` was entered; the title screen did
  not change. No password or debug screen was reached by any menu path.

## 4. Address map

File offset = ROM address − `0x08000000` (single, flat image).

| ROM addr | Purpose | Evidence |
|---|---|---|
| `0x08000000` | Header; entry `0xEA00002E` → `0x080000C0` | derived (header bytes) |
| `0x080000C0`–`0x080001F0` | ARM crt0 | derived (`objdump -M force-arm`) |
| `0x080001EC` | crt0 literal `0x08000235` (Thumb `main` at `0x08000234`) | derived |
| `0x08000234`–`0x0800059C` | `main`; literal pools; mode/game globals | derived |
| `0x08003A20` | Input edge detector (reads KEYINPUT) | derived |
| `0x08003A40` | Literal `0x04000130` (KEYINPUT) — **only** such literal in ROM | derived |
| `0x08003A44` | Literal `0x000003FF` (10-button mask) | derived |
| `0x08003A48` | Literal `0x03000FB0` (pressed-key global) | derived |
| `0x08003A4C` | Literal `0x03000FA8` (held-key global) | derived |
| `0x0800C4E4`–`0x0800C59C` | Scene/screen dispatcher, states 1–8 | derived |
| `0x0800C5BC` | Literal `0x030061C0` (dispatch state word) | derived |
| `0x0800C5C0` / `0x0800DC64` | state 7 / state 8 handlers | derived |
| `0x08349E0C` (file `0x349E0C`) | Developer padding message (ASCII, data) | observed |
| `0x0834FB64` (file `0x34FB64`) | `BONUS ` ASCII | observed |
| `0x0834FB6C`+ (file `0x34FB6C`+) | C runtime strings (`ASSERTION FAILED...`, `WARING FILE=...`, `bug in vfprintf: bad base`, `_sbrk: Heap and stack collision`) | observed |

RAM (savestate-verified; mGBA `gbAs` chunk layout: IWRAM at state `0x19000`,
EWRAM at `0x21000`, palette at `0x00800`, OAM at `0x00C00`):

| RAM addr | Meaning | Evidence |
|---|---|---|
| `0x03000FA8` | Held keys, active-high (u16) — written by `0x08003A20` | derived + observed (`0x0010` while Right held) |
| `0x03000FB0` | Newly-pressed keys (u16) | derived |
| `0x030000F4` | Title/menu flag: `0x00` title, `0x01` menus | observed (savestate diff) |
| `0x03005B50` | Menu id byte: `0x00` title, `0x3F` main menu, `0xE3` options, `0xA4` character select | observed |
| `0x030061C0` | Dispatcher state word (value `1` in every sampled menu/gameplay state) | observed |
| `0x030061D0`+ | OAM shadow: attr0/attr1/attr2 per menu text sprite; attr2 tile indices `0x0000/0x0040/0x0080/...` | observed |
| `0x0300EAC` | Complementary title flag: `0x01` title, `0x00` menus | observed |

## 5. Algorithm

There is no validator to reimplement. The only input algorithm present is the
edge detector at `0x08003A20`, in C-equivalent form:

```
held_mask    = ~KEYINPUT & 0x3FF          ; active-high
pressed_mask = held_mask & ~prev_held    ; one-frame edge
*0x03000FA8  = held_mask
*0x03000FB0  = pressed_mask
prev_held    = held_mask                  ; at 0x03000FA8 before overwrite
```

The scene dispatcher at `0x0800C4E4` is:

```
switch (*(u16*)0x030061C0) {
  case 1: f = 0x08016440; break;  case 2: f = 0x080109B0; break;
  case 3: f = 0x08014DB4; break;  case 4: f = 0x0800F30C; break;
  case 5: f = 0x08012060; break;  case 6: f = 0x080136FC; break;
  case 7: f = 0x0800C5C0; break;  case 8: f = 0x0800DC64; break;
  default: f = NULL;
}
f();
```

No branch in this dispatcher, nor in the menu handlers, compares a stored
multi-button sequence or a typed string.

## 6. Tables

*Game type values (4):* PUZZLE, TIME ATTACK, JOURNEY, CLASSIC (cyclic).
*Difficulty values (5):* CHILD, EASY, MEDIUM, HARD, EVIL (cyclic; greyed and
inactive in PUZZLE / TIME ATTACK).
*Music values (2):* ON, OFF.
*Characters (8):* Jake, Spike, Geji, Numb Skull, Zod, Mildred, Sunny, Midoribe.
*Main-menu items (3):* Single Player, Two Player, Options.
*Key masks:* GBA standard, active-high after `~KEYINPUT & 0x3FF`:
A=`0x001`, B=`0x002`, Select=`0x004`, Start=`0x008`, Right=`0x010`,
Left=`0x020`, Up=`0x040`, Down=`0x080`, R=`0x100`, L=`0x200`.

Published-code verification:

| Source | Claim | ROM verification |
|---|---|---|
| GameFAQs, *Snood 2: On Vacation* (id `929551`) | 5-character colour passwords, Child/Easy/Hard/Evil/Normal | **Wrong SKU** (different game code, 2005). Not applicable to `ASQE20`. |
| Cheat Happens / Action Replay, "Snood" | `b9f532cb ...`, infinite lives, max score, never drown, start on level 50 | External RAM patches (cheat device). Out of scope; not developer-intended codes. |
| TCRF | no page for GBA *Snood* | no hidden/debug content published |
| GameFAQs id `565768` (this game) | no cheat entries | consistent with the negative result |

## 6b. Enumeration

**Screen state space.** The dispatcher at `0x0800C4E4` has exactly **8** cases
(states 1–8; `cmp r0,#1` … `cmp r0,#8`, then fall-through). All 8 handler entry
points are listed in §4. The states actually reached on screen are: title,
main menu, options, character select, multiplayer host-search, factory cutscene
and gameplay (Puzzle/Classic). No case implements a password entry, level
select, sound test or debug overlay; there is no ninth case to reach one.

**Menu value space (exhaustively cycled).** Main menu 3 items; Options 4 items;
Game type 4 values; Difficulty 5 values; Music 2 values; Character select 8
values. Total distinct selectable option values = `4 + 5 + 2 + 8 = 19`, plus
`3` main-menu items. Every value was observed on screen by cycling Right until
the first value repeated; no extra/unlabelled value appeared.

**String/text-bank search space.**
* `strings -t x -n 4`: 49,182 runs; keyword filter for
  `password|cheat|code|debug|secret|unlock|level|menu|invalid|hint|bonus|warp|master`
  produced **2** hits: the padding message at `0x349E0C` (mentions "levels"
  only in prose) and `BONUS ` at `0x34FB64`. No password/debug UI string.
* All in-game text is sprite/tile-indexed: OAM shadow at `0x030061D0+`
  (verified changing across all four menus), tile blocks referenced by attr2
  values `0x0000, 0x0040, 0x0080, ...`; no ASCII text bank exists in ROM.
  Encoding search over the full 4 MiB for `PASSWORD`, `DEBUG`, `CHEAT`,
  `SECRET`, `LEVEL`, `OPTIONS`, `PRESS START`, `JAKE`:
  plain ASCII 0 hits; UTF-16LE 0; UTF-16BE 0; reversed 0; `+0x80` 0;
  single-byte add `+k` (k=0..255) 0; single-byte XOR `k` 0; and five
  permutation alphabets (`A=0`, `A=1`, reversed, QWERTY, 32-symbol) 0 hits.
* C runtime strings at `0x34FB6C`+ are generic library messages, not game UI.

**Button-code search space.**
* Exactly **one** literal `0x04000130` (KEYINPUT) exists in the image, at
  `0x08003A40`, used only by the edge detector at `0x08003A20`.
* The held-key global `0x03000FA8` has **4** literal references
  (`0x08002BC0`, `0x08003A18`, `0x08003A4C`, `0x080C0A8`); all are the input
  reader or menu counters (e.g. the `/10` wrap at `0x08002B78`). None is a
  sequence matcher.
* Konami prefix search as `u16` active-high and active-low masks for lengths
  2, 3, 4, 5, 6 and 10: **0** hits.
* Scan of the code region (`0x08000000`–`0x08027000`) for runs of ≥4 consecutive
  single-button-mask `u16` values: **0** hits (all 240 whole-ROM hits lie in
  graphics/padding regions ≥`0x2B0000` and are data false positives).
* In-game rejection: Konami sequence entered at title → title unchanged.

**Comparison space.** No string-comparison routine is called on any user input;
there is no text-entry field at all in the game. `strcmp`/`memcmp`-style
comparison sites against user data: 0.

**Conclusion of enumeration.** Space of reachable in-game "cheat surfaces"
= 8 screen states × (3 + 19 menu values) with 0 password fields, 0
button-sequence matchers, 0 hidden menu entries, and 0 code strings in any of
the encodings searched. The negative is therefore bounded by explicit counts,
not by absence of testing.

## 7. Validation evidence

* **Observed** — boot splash, title, all three main-menu items, all four Options
  rows with all 4/5/2/8 values, 8 characters, the Snood Factory cutscene,
  Puzzle `LEVEL 1` and Classic `MEDIUM` boards, the multiplayer host-search
  screen, absence of a pause menu (Start/Select/B in both modes), and no change
  after the Konami sequence. Screenshots were saved under
  `/tmp/snood1/` (e.g. `view.png`, `diffs.png`, `chars_montage.png`).
* **Observed (RAM)** — savestate `gbAs` diffs: `0x030000F4` = 0 (title) / 1
  (menus); `0x03005B50` = `0x00` / `0x3F` / `0xE3` / `0xA4` for title / main
  menu / options / character select; `0x03000FA8` = `0x0010` with Right held vs
  `0x0000` released; OAM shadow at `0x030061D0`+ changes with each menu.
* **Derived** — the single KEYINPUT reader and the two globals from disassembly
  at `0x08003A20`–`0x08003A3E`; the 8-case dispatcher at `0x0800C4E4`;
  zero key-mask tables and zero literal password strings from whole-ROM scans.
* **Inferred** — the (plausible) mapping of dispatcher states to named screens
  was not needed for the result; the negative rests on the case count and the
  screen walk, not on naming all 8 handlers.

## 8. Unknowns

* Exact VRAM byte-ordering used inside mGBA's `gbAs` chunk prevented a clean
  pixel-perfect reconstruction of the sprite font from savestates; however the
  OAM shadow and tile-index stride were read directly, and the encoding searches
  cover the string-based failure mode that would matter for a password.
* Which of the 8 dispatcher states correspond to unused cutscene/demo handlers
  was not resolved by name; all reached states were walked, and none exposes a
  code-entry surface.
* Web pages were treated as data. No prompt-injection payload was encountered
  in fetched pages or ROM strings.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `strings -t x`, `grep -aob`, `xxd`, Python 3.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb|force-arm`.
* Capstone (Python) for Thumb literal/BL scans; `render2.py`/`rendv*.py`/`findfont*.py`
  under `/tmp/snood1/` for savestate and ROM tile rendering.
* mGBA 0.10.5 `-3`, `Shift+F1..F4` savestates; `gbAs` PNG chunk decompressed
  with `zlib` to read IWRAM/RAM at state offset `0x19000`.
* `Xvfb :317`, `openbox`, `xdotool` (XTEST), `scrot`, ImageMagick `convert`/`montage`.
* The GDB stub did not bind a TCP port on this build, and the `-d` CLI debugger
  stops accepting commands after `continue`; savestate RAM diffing (guide §16.13)
  was used instead, and gave direct RAM evidence.

**Legal note:** no ROM or copyrighted assets are redistributed here; only
addresses, hashes and findings are published.
