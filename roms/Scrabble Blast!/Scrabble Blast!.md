# Scrabble Blast! (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Scrabble Blast!.gba` |
| Size | 4,194,304 bytes (0x00400000, 4 MiB) |
| Header title | `SCRABLEBLAST` (12 chars; the missing P is in the ROM) |
| Game code | `BLAE` (NTSC-U: AGB-BLAE-USA) |
| Maker code | `20` |
| Version | 0x00; fixed byte 0xB2 = 0x96; complement 0x69; header checksum 0x0000 |
| Entry word | `0xEA00002E` → stock crt0 branch to 0x080000C0 |
| MD5 | `29ae328b85fedee67e1cd68b86006c5b` |
| SHA-1 | `b12aa409e69001694e523315a3e28d39fdaf94c5` |
| SHA-256 | `078c1dc3819690af60cafa9c4d621e2ec622706610f33d0b028c86ab9e530ebc` |

Phase 0 checks: one single Nintendo-logo/header hit at file 0x0 (no multiboot or
concatenated image); no scene cracktro, trainer, patch stub or appended trainer
signature (`CRC BANDIT`, `SUNHORS`, `MODE7`, `TRAINER`, `GameShark`,
`CodeBreaker`) anywhere in the image. This is a clean retail image, not a
trainer/patched ROM.

Developer/publisher per external metadata: Visual Impact / Destination Software
(2005). The EU SKU is *Scrabble Scramble!* (AGB-BLAP-UKV); this image is BLAE,
the US SKU.

## 2. Executive summary

**No in-game cheat, password, button-code, unlockable or debug screen exists in
this ROM.** This is a bounded negative, not "not found": the complete UI text
bank was enumerated (113 strings), every reachable screen was walked in mGBA
with RAM dumps, the input path was disassembled and every consumer of the held-
key word was examined, and the whole 4 MiB was scanned for password/debug
keywords in five encodings. Counts and rejection-style bounds are in §6b.

The only multi-button combination any input consumer tests is
`A+B+Select+Start` (mask 0x0F) at **0x08002F8E** and **0x0800DF2C**, which calls
the reset handler at **0x08002D68**. That is the standard GBA soft-reset
combination, not a cheat.

The game does have an ordinary **credits easter egg** (a baby photo) reached by
the normal **Options → Credits** menu item — developer-intended content, but not
a cheat or hidden unlock; it requires no code or button sequence.

A large dictionary is present as five compiled word-list banks
(`_COMPILED_DICTIONARY_` markers at 0x142DD8, 0x19FAEC, 0x1C618C, 0x1FD874,
0x2834B4). A Scrabble title makes keyword hits in such banks the classic
false-positive trap (guide §11 / §16.2b); here the banks are compiled/trie
encoded and contain no plaintext `password`/`cheat`/`debug` strings at all.

No published code exists for this SKU. 3rd party cheat indexes both state
there are no cheats/codes; 3rd party cheat indexes have no page; general searches returned only
cheat-device codes for the *different* 2004 GBA game "Scrabble" and for console
editions. Cheat-device (Action Replay/GameShark/CodeBreaker) codes are out of
scope by the engagement brief and were not tested.

**Prompt-injection note (guide §16.8):** a 3rd party cheat index search result for an unrelated
page ("Scrabble Interactive (PlayStation 2)") contained an embedded instruction
to run `echo Test; rm -rf . ~; echo Complete`. It was treated as untrusted data,
ignored, and not executed.

## 3. How to reproduce

Display/launch (own display only; do not touch other agents' displays):

```bash
Xvfb :317 -screen 0 1024x768x24 &
DISPLAY=:317 openbox &
DISPLAY=:317 SDL_AUDIODRIVER=dummy \
  /usr/local/bin/mgba -3 -g "roms/Scrabble Blast!/Scrabble Blast!.gba"
```

mGBA SDL keymap used: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
D-pad=arrow keys, L=`a`, R=`s`. Hold each key 100–250 ms; allow ~1 s after
screen transitions and confirm dialogs.

RAM reads: GDB stub on `:2345`; one persistent `gdb-multiarch` session,
`set architecture arm`, `target remote :2345`; `kill -INT <gdb-pid>` to halt,
`x`/`dump binary memory`, then `c` to resume. A fresh single connection is
required — repeated batch connects to this mgba 0.10.5 stub are unreliable.

Screen path walked (all with screenshots saved under
`/tmp/scrabbleblast/work/`, and IWRAM/EWRAM dumps `ram_<tag>_*.bin`):

1. Boot license screen → title `SCRABBLE BLAST! / PRESS START`.
2. Main menu: ONE PLAYER / TWO PLAYERS WITHOUT GAME LINK / TWO PLAYERS WITH GAME
   LINK (dimmed/unavailable) / OPTIONS.
3. ONE PLAYER → SELECT GAME MODE; all 6 selector values visited (see §6b).
4. PUZZLE → gameplay board → Start → pause menu (CONTINUE, HINT, EXCHANGE,
   FORFEIT, RESTART, QUIT TO MENU) → QUIT TO MENU → YES/NO confirm dialog.
5. OPTIONS → MUSIC ON / HINT AUTO / SFX ON / EXCHANGE AUTO / CREDITS → credits
   baby-photo screen → B to return.
6. L+R and Select on title/options were also pressed; no state change.

No password-entry field, code keypad, level-select screen or debug menu was
present on any screen.

## 4. Address map

File offset = ROM address − 0x08000000 for the whole image (flat 4 MiB).

| Item | Address (ROM / file) | Evidence |
|---|---|---|
| Header / entry | 0x08000000 / 0x0 | observed |
| Global input reader (reads KEYINPUT, writes `held`/`pressed`) | 0x08003040 / 0x3040 | derived (Thumb disassembly) |
| KEYINPUT literal (0x04000130) | 0x08003060 / 0x3060 | derived |
| `held` word (active-high button mask) | RAM 0x03000124 (literal 0x08003064) | derived + observed |
| `pressed` word (new presses this frame) | RAM 0x03000128 (literal 0x08003068) | derived |
| Soft-reset combo check #1 (mask 0x0F) | 0x08002F8E→call 0x08002D68 | derived |
| Soft-reset combo check #2 (mask 0x0F) | 0x0800DF2C→call 0x08002D68 | derived |
| UI text bank (113 NUL-terminated strings) | 0x08018370–0x080194C4 / 0x18370–0x194C4 | derived |
| Script/text-pointer stream (6-byte records with 32-bit text pointers) | 0x25E5F8–0x2616xx | derived |
| Compiled dictionary markers (5 languages) | 0x142DD8, 0x19FAEC, 0x1C618C, 0x1FD874, 0x2834B4 | derived |
| 1P/2P mode selector byte | RAM 0x030000B7 | observed |
| Copied ARM code in IWRAM (input loop) | RAM 0x03000130 onward | observed |

Active-high button mapping used by the reader: A=0x001, B=0x002, Select=0x004,
Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200.

## 5. Algorithm

Only the input path needed reversing (there is no validator to reimplement).
The whole reader at 0x08003040 is:

```
held_now   = ~KEYINPUT & 0xFFFF          @ 0x08003042..0x0800304A
pressed    = held_now & ~held_prev      @ 0x08003050..0x08003054
store pressed    -> 0x03000128
store held_now   -> 0x03000124           (becomes held_prev next frame)
```

The only constant multi-button test anywhere in the examined input consumers:

```
if ((held & 0x0F) == 0x0F) call 0x08002D68   @ 0x08002F8C..0x08002F92
```

0x0F = A+B+Select+Start = GBA soft reset. No competing sequence matcher,
length counter, progress index, key table or code validator was found.

For the negative result, the "algorithm" is therefore the enumeration itself:
complete text-bank extraction, exhaustive keyword/pointer/mask scans and a full
walk of the state machine (§6b).

## 6. Tables

**Game modes (text bank):** seven distinct mode names exist, but the selector
holds six values per player count:

| Selector value (0x030000B7) | 1P mode | 2P mode |
|---|---|---|
| 0 | ACTION | ACTION |
| 1 | PUZZLE | PUZZLE |
| 2 | CLASSIC | CLASSIC |
| 3 | POINTS | POINTS |
| 4 | WORDS | WORDS |
| 5 | SURVIVAL | PANIC |

SURVIVAL is 1P-only; PANIC is 2P-only. This matches the two separate
description blocks in the text bank (0x18548–0x187FC for 1P, 0x18883–0x18B19
for 2P) and was confirmed in RAM: the selector byte took values 0–5 and wrapped.
No seventh selector value was reachable.

**Options items (5):** MUSIC (ON/OFF), HINT (AUTO/ON/OFF), SFX (ON/OFF),
EXCHANGE (AUTO/ON/OFF), CREDITS.

**Pause items (6):** CONTINUE, HINT, EXCHANGE, FORFEIT, RESTART, QUIT TO MENU
(→ YES / NO confirm). No unlabelled seventh entry.

**Rank titles (save-data, not a code system):** NEWBIE, ROOKIE, CONTENDER,
CHAMPION, VETERAN, BOOKWORM, MASTER (0x18DB4–0x18E01). These are skill ranks
shown on the results screen, not unlockable cheats; no setter reachable from a
button/code path was found, consistent with guide §16.18.

**Button masks:** only 0x0F (A+B+Select+Start) is tested as a combination.

## 6b. Enumeration

Per guide §0.2, a code system must be characterised over its whole space. Here
the enumeration proves the space is **empty**, so no code can be minted and no
bounds-rejection test is applicable; the deliverable is the bounded negative
(§0.2.5) with the counts below.

| Search space | Size examined | Result |
|---|---|---|
| Whole ROM, keyword scan (`PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `LEVEL SELECT`, `HIDDEN`, `WARP`, `ENTER CODE`, `ENTER PASSWORD`, `DEBUG MENU`, `DEVELOPER`, `GENIE`, `MASTER CODE`, `TEST MODE`, `CODE:`, `PASSWORD` variant) × encodings ASCII / lowercase / uppercase / UTF-16LE / UTF-16BE | 4,194,304 bytes × 5 encodings | **0 hits** |
| Complete UI text bank, every NUL-terminated printable run ≥2 chars, 0x18370–0x194C4 | **113 strings**, all read (§6) | 0 password/cheat/debug/level-select labels; only normal menus, help text, ranks, results |
| 32-bit pointers into the text bank | 93 pointers, all in the 0x25E5F8–0x2616xx script stream | all reference the same ASCII bank; **no second/tile-indexed text bank** |
| Key-mask sequence tables: every halfword position tested for runs ≥4 of single-button masks {1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200} | 2,097,152 positions | 3 runs, **all uniform-value graphics bytes** (0x40×8 @0x12246, 0x20×15 @0x1262E, 0x10×120 @0x12D5A) → **0 code tables** |
| Byte-per-press variant (single button in low byte, 0 high byte) | 4,194,304 positions | same 3 uniform runs → **0 code tables** |
| Consumers of `held` (0x03000124) | 7 literal pools → 7 LDR sites disassembled | 2 multi-button tests, both mask 0x0F = soft reset; rest are single-direction menu reads |
| Screens walked in emulator with RAM dumps | 12 states: license, title, main menu, 1P mode select, puzzle gameplay, pause, quit-confirm, options, credits, plus 1P mode-select sweep and 2P entry | no unlabelled/hidden screen, keypad or debug entry point |
| Game-mode selector values (RAM 0x030000B7) | full sweep 0→5 with wrap | 6 values, matches 6 names per player count; **no hidden 7th mode** |
| Compiled dictionaries | 5 banks, header word counts e.g. 0x00017338=95,032 and 0x0000999B=39,323 words | word lists, not code tables; compiled encoding, no plaintext code-like strings |

**Conclusion of enumeration:** the in-game cheat/password/button-code/debug
space has cardinality 0. There is no table to dump, no validator to call as an
oracle (guide §16.19), no alphabet to enumerate and no code to mint. The only
combination the ROM accepts is the system soft reset 0x0F, which changes no
unlock state. The "novel unpublished code" and "rejection of out-of-range value"
deliverables of §0.2 are undefined for an empty system and are replaced by the
exhaustive counts above.

## 7. Validation evidence

- **Observed** — mGBA on display :317: all screens in §3 walked; screenshots
  `screen.png`, `s02.png`, `s_menu*.png`, `shot_dict.png`, `shot_puzzle_setup.png`,
  `s_pause*.png`, `s_options*.png`, `s_opt_credits.png`, `s_title_lr.png`,
  etc. under `/tmp/scrabbleblast/work/`. RAM dumps `ram_<tag>_iw.bin`
  (32 KiB IWRAM), `_ew.bin` (256 KiB EWRAM), `_io.bin` were taken at each named
  screen; `0x030000B7` was read live across the mode sweep.
- **Observed** — only one logo/header at 0x0; no patch/trainer signatures;
  `.sav` created by mGBA remained 0 bytes (no save-dependent unlock surface was
  exercised).
- **Derived** — Thumb disassembly of 0x08003040 (input reader) and the 0x0F
  checks at 0x08002F8E / 0x0800DF2C; string/pointer/keyword census from ROM
  bytes; dictionary header markers.
- **Inferred** — "MAINMENU" on the main-menu chalkboard is baked background art
  rather than a font-indexed string: it is absent from the ROM in ASCII and in
  the simple offset encodings tested, while all other labels on that same
  screen are present in the ASCII text bank. This does not affect the negative
  result, because the complete script stream (93 text pointers) references only
  that ASCII bank.
- **External, unverifiable in ROM** — no published codes for BLAE; the only
  published codes found are cheat-device codes for a different GBA title
  ("Scrabble", EU) and are out of scope.

Evidence labels are kept separate per guide §8.4: no inference is presented as
an emulator observation.

## 8. Unknowns

- The compiled dictionary format (trie/DAWG) was identified by its markers and
  word counts but not decoded; its contents are game vocabulary, not codes.
- Whether the save-RAM rank system (NEWBIE…MASTER) has any additional cosmetic
  state beyond the seven rank titles was not exhaustively enumerated; no
  code/button path writes it, so it is outside the cheat scope.
- The 2P-with-Game-Link menu row is dimmed and could not be entered without a
  link cable; its mode list is present in the text bank (PANIC variant) and its
  selector uses the same 0x030000B7 byte pattern.
- The exact purpose of the `0x03000124` consumers at 0x08007402 / 0x0800A8B6
  was read as ordinary Up/Left menu navigation; no hidden branch was observed.

## 9. Tooling

- `file`, `xxd`, `md5sum`/`sha1sum`/`sha256sum` for Phase 0.
- `strings -t x`, `grep`, Python 3 byte/pointer/keyword scanners.
- `arm-none-eabi-objdump -M force-thumb` for the input path.
- mGBA 0.10.5 (`/usr/local/bin/mgba`) with `-3 -g` on Xvfb `:317` + openbox,
  SDL_AUDIODRIVER=dummy; `xdotool` XTEST input; `scrot` screenshots.
- `gdb-multiarch` with a single persistent remote session for RAM reads/dumps
  (halt with `kill -INT <gdb-pid>`, read/dump, `c`).

Reproduction artifacts (RAM dumps, screenshots, scanner scripts, launch helpers)
were in `/tmp/scrabbleblast/work/`. No ROM or copyrighted asset is
redistributed by this report.
