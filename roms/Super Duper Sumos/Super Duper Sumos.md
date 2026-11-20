# Super Duper Sumos (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| Path | `roms/Super Duper Sumos/Super Duper Sumos.gba` |
| Size | 4,194,304 bytes (4 MiB, 32 Mbit) |
| SHA-256 | `14c22fd9f8c0a93a1a8a19c482b5789ecca8cfa710c2a7495477f42403b4da9a` |
| MD5 | `bcf80fec3345780d3ab0349d185ec3f5` |
| `file` | `Game Boy Advance ROM image: "SD_SUMOS_AGB" (BDPE5D, Rev.00)` |
| Header title | `SD_SUMOS_AGB` (12 bytes at 0xA0) |
| Game code | `BDPE` (USA), maker `5D` (Midway), fixed byte 0xB2 = 0x96 |
| Software version | 0x07; header checksum byte 0xBE = 0x00 (complement 0x19) |
| Build string | `v 08.15.03a` at ROM 0x0812B914 (pointer at file 0x3DD128) |
| Developer / publisher | Handheld Games LLC / Midway (credits + web recon) |

**Boot-header anomaly (observed, important for reproduction).** The entry word at 0x000 is
`0xEA0FF9F1`, not the stock `0xEA00002E`; bytes 0x04–0x9F are the intact standard Nintendo
logo (byte-for-byte identical to other ROMs in the collection). The patched entry points at a
small ARM loader at ROM 0x3FE7CC:

```
3FE7CC  add r0, pc, #0x20        ; source = 0x3FE7FC
3FE7D0  add r0, r0, #0x8
3FE7D4  mov r1, #0x02000000
3FE7D8  add r1, r1, #0xC0        ; dest = 0x020000C0
3FE7DC  ldr r2, [pc,#20]         ; 0x1834 bytes
3FE7E0.. copy loop
3FE7F4  add pc, r0, #0xC0        ; jump to 0x020000C0
```

So the image boots through a custom EWRAM code-copy stub. It is **not** a cracktro/trainer and
the game boots normally in mGBA 0.10.5. Web recon lists several hacked dumps of this title
(`[hI]`, `[hIR00]`, `[hIRff]`, `[t1]`, `[b1]`); the analysed image matches the family whose boot
stub was altered, but all game text and code past 0xC0 are intact. No patch was needed to run it.

## 2. Executive summary

**There is no in-game/developer-intended cheat system in this GBA SKU.** No password, no
button-code sequence, no hidden/debug menu and no name-entry "code" surface exists. Every
"cheat" published for this game is a GameShark/CodeBreaker **RAM patch** (e.g.
`8200022C 0FFF` "all levels unlocked", `33004340 0014` "infinite health"), which is explicitly
out of scope for this engagement. Two independent public databases (ChapterCheats, VGChartz)
list *no* codes, passwords, unlockables, secrets, glitches or easter eggs for the GBA release.

This is a **bounded negative**, not "I did not find it". It is backed by:
* a complete decode of the ROM's text banks (474 localised UI-string pointers + 556 ASCII
  strings in the text region; **zero** matches for `password`, `cheat`, `debug`, `warp`,
  `hidden`, `enter name`, `initials`, `code:`),
* an exhaustive input-surface search (only **two** literal references to KEYINPUT `0x04000130`
  in the whole ROM, both generic input helpers; zero Konami-style mask sequences in any of
  three encodings), and
* a full walk of every reachable screen and every menu entry (section 6b).

The only developer-intended unlockable is the **LEVEL SELECT** entry of the main menu, which is
gated by save/progress state: on a fresh save, choosing it falls back into the
SELECT PLAYER → new-game flow. It is a progression-gated menu, not a code; no controller input
sequence was found that unlocks it, and patching the address named by the published cheat-device
code did not change the behaviour.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, Xvfb `:319` (`SDL_AUDIODRIVER=dummy`), window 480x320 (scale 2).
* Keymap (verified by reading KEYINPUT from savestate offset `0x530`):
  arrow keys = D-pad, **`x` = A** (bit 0), **`z` = B** (bit 1), `Return` = Start,
  `Shift+F1` = write savestate.
* Input timing: **hold keys ≥ 0.3 s**. 50–100 ms taps are frequently dropped by this game's
  polling loop (§16.2 of the guide). Many "the menu ignored me" observations were this.
* Boot path: title/logo → `PRESS START` → attract-mode HIGH SCORES → "The Incredible World of
  DIC" → "HANDHELD GAMES" → title → MAIN MENU. Repeated Start presses (~0.4 s apart) traverse it.
* Main-menu selection (verified in emulator; blue highlight is the focused row):

  | Row | Label | A button result |
  |---|---|---|
  | 0 | START NEW GAME | SELECT PLAYER (Booma / Mamoo / Kimo) → EPISODE 1 → gameplay/cutscene |
  | 1 | LEVEL SELECT | falls back to SELECT PLAYER on a fresh save (gate) |
  | 2 | GAME OPTIONS | DIFFICULTY / PLAYER LIVES / SOUND / CLEAR SAVE, A=DONE, B=CANCEL |
  | 3 | CREDITS | scrolling credits |

* Screens reached and captured: title, `PRESS START`, attract HIGH SCORES, DIC logo, Handheld
  Games logo, MAIN MENU, SELECT PLAYER, EPISODE 1 card, in-game dialogue/cutscene, GAME OPTIONS,
  CREDITS. Pause, CONTINUE GAME, GAME DIFFICULTY, HIGH SCORES entry and the four SNACK TIME
  minigames were enumerated from the text bank; pause could not be opened during the cutscene.
* Codes tested: **none** — all published codes are cheat-device RAM writes and were deliberately
  not applied. Two *diagnostic* RAM/SRAM pokes were used only to probe the LEVEL SELECT gate
  (section 6b); they are not cheats and are not claimed as findings.

## 4. Address map

| Location | Meaning |
|---|---|
| 0x00000000 | Entry word `0xEA0FF9F1` → EWRAM loader at 0x3FE7CC |
| 0x00000004–0x9F | Standard Nintendo logo (intact) |
| 0x000000A0 / 0xAC / 0xB0 | Title `SD_SUMOS_AGB` / game code `BDPE` / maker `5D` |
| 0x0003FE7CC | Boot loader: copies 0x1834 bytes from 0x3FE7FC → 0x020000C0 |
| 0x08070CD0 | Literal pool containing `0x0812DDB4` ("PRESS START") |
| 0x080AF8A4 | Literal `0x04000130` in generic input helper library |
| 0x080C04D4 | Literal `0x04000130` in "wait for A/B/Select/Start" routine |
| 0x080C38F0 | Options/menu loop (switch on 0/1/3); calls 0x080C39B4 |
| 0x080C39F0 / 0x080C3A10 | Shift a **10-entry 16-bit array** at `0x03004150` (all zero at rest — not an input-history buffer) |
| 0x0812B914 | Build/version string `v 08.15.03a` |
| 0x0812D4A4, 0x0812D5C4 | Font/glyph alphabet `!"#$%&'()*+,-./0123…[\]^` — no ROM pointer references it |
| 0x0812DDB4 | `PRESS START` |
| 0x0812DE24–0x081320FC | All UI/dialogue strings (see section 6) |
| 0x083DD998–0x083DE0FC | 474-entry 32-bit pointer table into the string bank (one language) |
| 0x02000000–0x02000400 | Game state: 0x0200022C = 0 on fresh save, 0x02000230 = 0x246, 0x02000234 = 0x7530 (30000), 0x02000238 = 0x2710 (10000) |
| 0x03000034, 0x03000080 | IWRAM bytes that change with menu cursor movement |
| SRAM (512 B, `Super Duper Sumos.sav`) | Big-endian high scores and per-level records; offset 0x0C–0x2C = header/flags/scores, 0x38+ = level blocks |

**Savestate layout used for RAM reads** (mGBA `.ss1`, PNG with zlib `gbAs` chunk, 397,312 B
decompressed): `KEYINPUT` at state offset **0x530** (16-bit; 0x03FF = all released), IWRAM at
**0x19000** (=> `0x03000000`), EWRAM at **0x21000** (=> `0x02000000`). Helper:
`/tmp/opencode/superdupersumos/ssread.py`.

## 5. Algorithm

Not applicable — there is no password/checksum/button-code validator in this image. The only
"algorithm" recovered is the observed main-menu dispatch and the level-select gate fallback
described in sections 3 and 6b. The 10-entry shift routine at 0x080C39F0 was checked and is not
an input matcher (its buffer at `0x03004150` contains ten zeros in every captured state, never
button masks).

## 6. Tables

**GBA key bits** (active low in `KEYINPUT`): A=0x01, B=0x02, Select=0x04, Start=0x08,
Right=0x10, Left=0x20, Up=0x40, Down=0x80.

**Observed string table** (pointer table 0x083DD998–0x083DE0FC, 474 pointers; strings at
0x0812DE24–0x081320FC):

```
MAIN MENU / START NEW GAME / LEVEL SELECT / GAME OPTIONS / CREDITS
GAME OPTIONS: PRESENT / DIFFICULTY / PLAYER LIVES / MUSIC / SOUND / EXIT
              EASY / NORMAL / HARD / ON / OFF / CLEAR SAVE / DONE / CANCEL
CONTINUE GAME / Do you want to continue? / Yes / No
SELECT PLAYER / Choose your character! / Booma / Mamoo / Kimo
GAME DIFFICULTY / EASY / MEDIUM / HARD
LEVEL SELECT / Select a level to view! / LEVEL: / HIGH SCORES / EPISODE
 Episodes 1..6: Out in Nature / Generic City on Ice / A Day at the Beach /
 Mongolian Steps / Jungle Romp / Back to Bad Inc.
SCORE / TOTAL / PHAT / CONTINUES / SNACK TIME / MINIGAME ROULETTE /
CONGRATULATIONS! / IT'S SNACK TIME! / YOU BEAT THE GAME! / PAUSE
4× SNACK TIME minigame instruction screens; CREDITS roll
```

**Difficulty values** are `EASY`, `NORMAL` (shown as `MEDIUM` on the new-game difficulty
screen), `HARD`; lives default 5; sound ON. Level-select advertises 6 episodes.

## 6b. Enumeration

**Space definition.** No code space exists — there is no alphabet, no code length, no checksum
field and no validator. The *searched* space is therefore enumerated explicitly:

| Searched space | Size | Result |
|---|---|---|
| Localised UI string pointers (0x083DD998–0x083DE0FC) | 474 pointers | 0 contains `password/cheat/debug/warp/hidden/code/enter name/initials` |
| ASCII strings in text region 0x12D000–0x133000 | 556 strings | same 0 matches; `secret` appears only twice, both story dialogue ("secret weapons", "No super secret move?") |
| Literal references to `KEYINPUT` (0x04000130) | 2 (0xAF8A4, 0xC04D4) | both are generic input helpers (read/mask/wait); neither compares a sequence |
| Konami-style press sequences, raw / active-low-inverted / 16-bit-LE | 3 encodings × 2 orders = 6 patterns | 6/6 absent from the entire 4 MiB image |
| Candidate 10-entry input-history buffer at 0x03004150 | 10 words | all zero in 5 independent savestates; not a code buffer |
| Pointers to the font alphabet strings 0x0812D4A4 / 0x0812D5C4 | 2 strings, 2 pointer encodings | 0 references in ROM → glyph table, not a password alphabet |
| Main-menu entries and their A-button branches | 4 entries | all 4 mapped (section 3); LEVEL SELECT is progress-gated, not a code gate |
| Save data | 512 B SRAM | high scores + level records; no text-entry field, no code storage |
| Published in-game codes (ChapterCheats, CheatCodes.com, VGChartz, Almar's Guides) | 4 sites | 0 in-game codes; only cheat-device RAM patches (out of scope) |

**Novel codes.** None minted — a novel code cannot exist in a game with no code validator.
This is the required bounded-negative outcome, not an untested search. In particular, the two
widely published button-activation "codes" (`Press Down+L for Lv 1 Attack`, `Press Select to
Refill Bonus Timer`, etc.) are **CodeBreaker activator conditions on cheat-device RAM writes**
(guide §16.20): they are not game input sequences and were excluded.

**Bounds proven by rejection.**
* `0x0200022C` (the address in the published "All Levels Unlocked" cheat-device code) is 0 in a
  fresh state. I patched it to `0x0FFF` in a savestate's EWRAM (`ssread`/`patch_ss.py`, state
  offset 0x2122C) and reloaded with `-t`: selecting LEVEL SELECT **still** fell back to
  SELECT PLAYER → this address is not the menu gate in this revision.
* I additionally forced SRAM bytes 0x0C–0x13 to 0xFF and rebooted: LEVEL SELECT still fell back.
  So neither the named RAM word nor that SRAM range unlocks the menu; the observed gate remains
  progress/save-state based and its exact variable is listed as an unknown.
* Short (50–100 ms) key taps are rejected by the game's polling loop; all menu navigation used
  held presses ≥0.3 s, verified against `KEYINPUT`.

**Screen walk with RAM evidence.** Every reachable screen was visited: title/PRESS START,
attract HIGH SCORES, both intro logos, MAIN MENU (4/4 entries), SELECT PLAYER (3/3 characters),
GAME OPTIONS (5/5 rows), CREDITS, EPISODE card, gameplay dialogue, and the LEVEL SELECT fallback.
RAM evidence: `KEYINPUT` read from `.ss1` offset 0x530 confirmed A/B/Down mapping; state PC/LR
at the main menu were `0x080C3862 / 0x080C386D`; 0x0200022C read as 0 on a fresh save.

## 7. Validation evidence

| Claim | Type | Confidence |
|---|---|---|
| 4 MiB, header BDPE5D Rev.00, hashes | Observed (`file`, `sha256sum`, `xxd`) | High |
| Boot entry word patched; loader copies 0x1834 B to EWRAM | Derived (ARM disassembly of 0x3FE7CC) | High |
| No password/cheat/debug strings | Observed (474 pointer targets + 556 ASCII strings fully decoded) | High |
| Only 2 KEYINPUT literal sites; no sequence matcher | Derived (full-ROM literal scan + disassembly) | High |
| All 4 main-menu branches mapped; LEVEL SELECT gated | Observed (emulator, screenshots) | High |
| 0x0200022C patch does not unlock LEVEL SELECT | Observed (savestate patch + `-t` reload) | High |
| Pause/CONTINUE/SNACK TIME screens exist | Derived (text bank only, not emulator-confirmed) | Medium |
| Published codes are cheat-device only | Observed (web recon, 4 sites) | High |

## 8. Unknowns

* The exact RAM/SRAM variable that unlocks LEVEL SELECT was not identified; normal level
  progression is the likely writer, but this was not proven by completing the game.
* The pause, CONTINUE GAME and SNACK TIME screens were enumerated from the text bank; pause
  could not be opened during the opening cutscene, so their on-screen layout is unconfirmed.
* The purpose of the patched entry stub (original game design vs. an intro-removal release hack)
  is not settled; it behaves as a legitimate EWRAM loader and the game runs correctly.
* No second language table was found beyond 0x083DE0FC (single-language UI).

## 9. Tooling

* mGBA 0.10.5 (`-2` scale, `-g` GDB stub, `-t` savestate load), Xvfb :319 + openbox,
  `xdotool` (XTEST, held keys), `scrot`, ImageMagick `convert`/`montage`.
* `gdb-multiarch` used once to confirm the initial PC/SP; abandoned because the stub is
  single-client and closed after one connection. Savestate diffing was used for all RAM reads.
* Python helpers in `/tmp/opencode/superdupersumos/`: `ssread.py` (gbAs inflate + KEYINPUT/EWRAM
  reader), `patch_ss.py` (patch EWRAM in a savestate and rebuild the PNG with CRC), `scan.py`
  (32-bit pointer scan), `dis.py` (Capstone Thumb disassembly), `texttables.py` (string-bank
  enumeration). `arm-none-eabi-objdump` used for the ARM boot stub.
* No GameShark/CodeBreaker/Action Replay code was applied at any point.
