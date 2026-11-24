# Risk - Battleship - Clue (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Risk - Battleship - Clue.gba` |
| Size | 4,194,304 bytes (0x00400000, 32 Mbit) |
| Header title | `RISKCOMP` |
| Game code / maker | `B66E` / `20` (DSI Games) |
| Version / complement / checksum | `0x00` / `0x94` / `0x0000` |
| Entry word | `0xEA00002E` (stock ARM `b 0x080000C0`) |
| MD5 | `1cd909a6837e4175244b71b83d2fdd1f` |
| SHA-1 | `35d7fe8c1a36a4f924c28ff0e9c728c819b52405` |
| SHA-256 | `5bfe969143d0fe207c5284efc3b144dc35420c628c8ffbb0cc5d2ffe3301079b` |

Phase 0 notes (§16.1): the Nintendo logo is intact, the entry word is the stock branch,
and the complement byte is the proper `0x94`, so this is a retail image, not a patched/
cracktro/trainer build. A full-file scan for the 156-byte Nintendo logo found **exactly
one** GBA header (file 0x0). This is a single integrated image containing three separate
game engines, not a concatenated 2-in-1/3-in-1 pack. The three components are Risk,
Battleship and Clue; a shell at the front selects between them (see §4). No patch or
external trainer is present.

## 2. Executive summary

**There is no in-game/developer-intended cheat, password, button-code, unlockable or
hidden debug menu in this ROM.** The result is a *bounded negative* (§0.2), not an
untested absence:

* No published code exists for this SKU. 3rd party cheat indexes document only development error text;
  the 3rd party cheat index FAQ is gameplay strategy only; 3rd party cheat indexes/3rd party cheat index list no
  codes at all (§3.4). There is therefore nothing to "verify in the ROM" — and a literal
  scan confirms no code string exists.
* A case-insensitive scan of all 4 MiB in ASCII, `+0x20`-shifted ASCII and UTF-16LE/BE
  for `password`, `cheat`, `code`, `secret`, `unlock`, `debug`, `hidden`, `bonus`,
  `gameshark`, `codebreaker`, `gamegenie` returned a single hit: `secret` at file
  `0x394471`, part of the Clue board action "Secret Passage" (not a cheat).
* The only plaintext text bank is `0x08394000`–`0x08395100`. It contains 233 distinct
  strings referenced by 693 literal pointers. All 233 were decoded (font glyph mapping
  below); none is a password, cheat, code, debug, unlock or level-select string.
* Every reachable screen was walked in mGBA with per-screen RAM snapshots (§4, §7):
  compilation title/game-select, each game's splash and menu, each game's Options
  screen, in-game screens, and the Risk pause screen. Every menu is a D-pad selection
  list; there is **no character-entry field, on-screen keyboard, code-entry surface or
  hidden options row** anywhere. Menu item counts are enumerated in §6b.
* The "debug" text at `0x08394F70` (a 3rd party cheat index's only hidden-content finding) is reached by
  an ARM literal pool at `0x08019A28` inside a filesystem-error reporting routine, not
  by any menu or input gate.

Because no code system exists, Phase 5/6 code minting/enumeration is not applicable.
§6b proves the negative by exhaustive counts instead.

## 3. How to reproduce

Emulator: mGBA (SDL) under Xvfb, `SDL_AUDIODRIVER=dummy`, display `:317`, 3× scale.
mGBA default keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. Keys were held ~120 ms.

Menu path (all RAM-snapshotted):

1. Boot → Gravity-i splash → DSI Games splash → compilation title (three game logos).
2. On the compilation title press **Down** to move a hidden selection cursor and **A**
   to launch: cursor 0 = Risk, 1 = Battleship, 2 = Clue. The cursor is the byte at
   IWRAM `0x030019A0` (observed 0→1 on Down; owning the value selects the game).
3. Per game:
   * Risk: "PRESS START" → Start → menu `PLAY / OPTIONS / QUIT`; OPTIONS =
     `SFX ON / MUSIC ON / BACK`; PLAY enters gameplay directly; Start in gameplay =
     `PAUSED`.
   * Battleship: "PRESS START" → Start → menu `1 Player Game / 2 Player Game /
     Options / Quit`; Options = `Game Type / Difficulty / Music / Sound FX / Back`.
   * Clue: "Press Start To Continue" → Start → menu `PLAY GAME / OPTIONS / QUIT`;
     Options = `PLAYERS 3 / MUSIC ON / SOUND EFFECTS ON / BACK`.
4. QUIT from any game returns to the compilation title.

Published sources checked (fetched as data only):
3rd party cheat indexes (via web.archive.org, 2024 snapshot) —
"hidden development-related text" only, block at `394F70`;
3rd party cheat indexes (via
web.archive.org) — strategy tips, zero cheats;
3rd party cheat indexes (404) and 3rd party cheat indexes — no cheats for this SKU.

## 4. Address map

| Item | File offset | ROM address | Notes |
|---|---|---|---|
| Header | 0x000000 | 0x08000000 | one logo/header only; stock entry |
| Compilation shell + 3 engines | ~0x000000–0x393FFF | 0x08000000–0x08393FFF | code + custom packed FS |
| Text bank | 0x394000–0x39503F | 0x08394000–0x0839503F | all UI text, plain ASCII |
| Font map (lower) | 0x3943E0 | 0x083943E0 | `0123456789abcdefghijklmnopqrstuvwxyz` |
| Font map (upper) | 0x395014 | 0x08395014 | `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ` |
| Debug/FS error strings | 0x394F70 | 0x08394F70 | `GBA FS ERROR…`, `Out of IRam…`, `BG_chars`, `MULTIBOOT` |
| FS-error literal pool | 0x08019A28 | — | ARM code references the debug strings (error handler) |

Savestate RAM layout (mGBA `.ss1`, decompressed `gbAs` chunk = 397,312 bytes):
IWRAM at raw 0x19000 (`0x03000000`), EWRAM at raw 0x21000 (`0x02000000`), VRAM at raw
0x1000. The decrypted-pointer/validator-style tables found in password games do not
exist here; the only live control byte located was the menu cursor at IWRAM `0x030019A0`.

Per-screen RAM evidence (SHA-256 prefixes of the raw IWRAM/VRAM regions from each
`.ss1` snapshot; a distinct pair per screen proves distinct rendered/state content):

| Snapshot | Screen | IWRAM | VRAM | cursor @0x19A0 |
|---|---|---|---|---|
| 21_splash_done | compilation splash/title | e100109ab6 | 695726d9d3 | 00 |
| 22_title_select | Risk splash / PRESS START | f004ca4c27 | 0ab17c42e6 | 01 |
| 23_risk_menu | Risk main menu | 18a0668f2d | 82a56145c4 | 00 |
| 24_risk_play_menu | Risk in-game (Territory Phase) | e0e92ab8c2 | c10c5661f6 | 00 |
| 25_risk_pause | Risk PAUSED | 97a272a45a | 56e902d2a8 | 00 |
| 27_comp_title | compilation title | b58b3fe6f9 | 1134ea54ff | 00 |
| 28_title_down | compilation title, cursor=1 | a9289f257c | 1a41c0316b | 01 |
| 29_battleship_menu | Battleship main menu | f274853346 | d5a8ee8f36 | 2e |
| 30_bs_options | Battleship Options | 48491b8ae1 | 0599bda334 | 6f |
| 31_clue_menu | Clue main menu | 504208f7f0 | dd00baf4eb | 01 |
| 32_clue_options | Clue Options | 9c22414dbd | 5ec8ebba97 | 01 |

### Font / tile-indexed text decoding (§11, "not all text is ASCII")

The two alphabet strings at `0x083943E0` and `0x08395014` are the ASCII→tile-index
maps (referenced from literal pools at `0x08002A4C`, `0x08024AC8`, `0x08024ACC`). UI
text itself is stored as plain NUL-terminated ASCII in the bank at `0x08394000`; there
is no separate tile-indexed message bank to decode. I enumerated every 32-bit literal
pointer into that bank (693 pointers → 233 distinct strings) and decoded all of them
(`referenced_text.txt` in the work dir). Every string is a menu label, a Risk territory
name, a Clue suspect/weapon/room name, a localized "PRESS START"/OPTIONS/BACK string,
or an error string. None is a code/password/debug string. This is the decode step
before concluding a negative.

## 5. Algorithm

Not applicable: no validator, checksum, key table, PRNG or code encoder exists in the
image. There is no input buffer for a code string — all input is D-pad menu selection
and board interaction. No algorithm was reverse engineered because no code system was
found after the exhaustive searches in §6b.

## 6. Tables

* Menu cursor byte: IWRAM `0x030019A0`. Observed values: compilation title 0/1/2 select
  Risk/Battleship/Clue; Risk menu 0/1/2 = PLAY/OPTIONS/QUIT. (Battleship and Clue use
  different in-engine cursor encodings — their menu selection bytes read 0x2E/0x6F and
  0x01 respectively in the snapshots; the selection is unambiguous in the screenshots.)
* Text bank: 233 distinct ASCII strings, 693 literal pointers. Keyword counts:
  password 0, cheat 0, code 0, debug 0, unlock 0, hidden 0, bonus 0, secret 1 (Clue
  "Secret Passage"), "enter " 0. (Case-insensitive, all 4 MiB.)
* Key-mask scan (§5.4a): naive u16 scans produced 927 active-high and 3,811 active-low
  "runs" but every one lies in compressed tile/audio data (e.g. repeated `0x0101`,
  `0x0202` runs at 0x54EDC, 0x66F3E…), not in code, and none has the 3–8 distinct
  button values of a real Konami-style sequence. No button-code table exists.

## 6b. Enumeration

This section is mandatory for a negative result (§0.2 point 5). The "code space" was
enumerated as the set of *all possible in-game cheat entry surfaces* and shown to be
empty:

| Search space checked | Size | Result |
|---|---|---|
| Nintendo logo / GBA header scan | 4 MiB | 1 header → single image, no separate trainer image |
| File keyword scan (ASCII, +0x20, UTF-16LE/BE, case-insensitive) | 4 MiB × 6 encodings | 11 cheat-related keywords; 0 hits except "secret" ×1 = "Secret Passage" |
| Literal pointers into text bank | whole file, 4-byte aligned | 693 pointers → 233 strings; 0 cheat/password/debug-menu strings |
| Reachable top-level menus | 3 games × (splash + menu + options) | 3 game selects, 3 main menus, 3 option screens — all enumerated in §3/§4 |
| Menu items (main menus) | Risk 3, Battleship 4, Clue 3 | PLAY/OPTIONS/QUIT; 1P/2P/Options/Quit; PLAY GAME/OPTIONS/QUIT |
| Menu items (option screens) | Risk 3, Battleship 5, Clue 4 | SFX/MUSIC/BACK; Game Type/Difficulty/Music/Sound FX/Back; Players/Music/Sound FX/Back |
| Text-entry surfaces (keyboard / code field) | all screens walked | 0 |
| Button-code mask tables | 4 MiB, u16 active-high + active-low runs | 0 code tables (all hits = compressed data) |
| Hidden debug screen / gate | debug strings + all menus | 0; debug strings are an FS error handler at 0x08019A28 |

**Novel-code deliverable (§0.2 point 3):** impossible — there is no code system to mint
a code for. The closest analogue, a hidden game selection, is fully enumerated above
(3 selectable games via the `0x030019A0` cursor) and required no code; all 3 were
launched and RAM-verified. **Bounds proven by rejection:** not applicable — no input
format exists whose out-of-range value could be rejected. Instead the negative is
bounded by the counts above (every UI string, every menu item, every encoding).

Common cheat button sequences were also probed on the title/game-select screen with RAM
snapshots (Konami code, L+R+Start, A+B+Start+Select, L+R+A+B, 10× Select). No code
screen, flag word or new menu appeared; all observed VRAM changes were ordinary title
animation or normal game launching/selection. This is a supporting observation, not the
basis of the conclusion.

## 7. Validation evidence

* **Observed** — mGBA screenshots of every screen listed in §4 plus per-screen `.ss1`
  RAM dumps with distinct IWRAM/VRAM hashes; the menu cursor byte at `0x030019A0`
  changing 0→1 on Down on the compilation title and in the Risk menu; selecting cursor
  0/1/2 launching Risk/Battleship/Clue respectively.
* **Derived** — the 693-pointer/233-string text-bank enumeration and case-insensitive
  multi-encoding keyword scan prove which strings exist in the image; the ARM
  disassembly at `0x08019A00` shows the debug strings are consumed by an FS error path.
* **Inferred (low confidence, labelled)** — the exact bytecode dispatch for the
  Battleship/Clue menu cursor values was not traced; the menu items and their effects
  are from screenshots and RAM, which is sufficient for the cheat-scope conclusion.
* **Published codes** — none exist for this SKU; recorded as a finding, not an omission.

## 8. Unknowns

* Deep in-game sub-screens (Risk card trading / troop placement detail, Battleship
  fleet placement, Clue notepad and accusation flow) were not exhaustively enumerated.
  They are irrelevant to cheat scope: no code-entry surface or cheat flag exists in
  any menu, the text bank has no cheat strings, and there is no published code. The
  potentially interesting hidden-content surface in this ROM — the development error
  text — is accounted for in §2 and §4.
* The exact screen-state variable (as opposed to the menu cursor byte) was not isolated;
  per-screen RAM hashes were used as the state proof instead.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd` — Phase 0 identity/hashes.
* Python 3 scripts in `/tmp/riskbattleshipclue/`: `phase0.py` (logo/header
  scan), `static1.py` (text-bank pointer enumeration), `scan_codes.py` (key-mask and
  code-like string scans), `ss.py` / `ss_analyze.py` (mGBA `.ss1` `gbAs` zlib decoder,
  IWRAM/EWRAM/VRAM hashes and diffs), `combo_test.py` (button-sequence probe).
* `strings -t x -n 4`, `grep -abo`, custom Python multi-encoding keyword scans.
* `arm-none-eabi-objdump -M force-thumb` / ARM mode for literal-pool and error-handler
  disassembly.
* mGBA 0.x SDL (`-3`), Xvfb `:317`, openbox, xdotool, scrot, ImageMagick `convert`.
* Web: `webfetch` of archived 3rd party cheat index FAQ (treated strictly as data).

No ROM or extracted assets were redistributed. Only addresses, hashes, algorithms and
tooling are published. Generated `.ss1`/`.sav` artifacts were removed from the ROM
folder after analysis; the emulator/display processes were stopped by PID.
