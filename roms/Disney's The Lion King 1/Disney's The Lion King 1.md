# Disney's The Lion King 1½ (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Disney's The Lion King 1/Disney's The Lion King 1.gba` |
| Size | 8,388,608 bytes (8 MiB), 0xFF padded |
| Header title | `LIONKING 1.5` |
| Game code | `BLKE` (USA) |
| Maker code | `4Q` |
| Version | 0 |
| Entry word | `0xEA00002E` (`b 0x080000C0`, stock crt0 branch) |
| Complement | `0x9F` (valid: `-(sum 0xA0..0xBC + 0x19) & 0xFF`) |
| Header checksum | `0x0000` (rebuilt-header artefact; complement still valid) |
| CRC32 | `EA5ED4C0` — matches the No-Intro `Disney's The Lion King 1.5 (U) [!]` dump |
| MD5 | `6a987dc5a8f0e87e1e055ee65f7e99c9` |
| SHA-1 | `382de6da61c5dc5c2844f5ffa28a1827d15319b1` |
| SHA-256 | `42fda2c2ee0048ab926b929de99176a5f47b740c8d68f03c59a9128b325aed7e` |

Phase-0 checks:

* Exactly one Nintendo logo hit (`0x04`); one GBA header. Not a multi-game cart.
* Entry is the stock `b 0x080000C0`; no cracktro/trainer menu. Searches for
  `SUNHORS`, `MODE7`, `CRC BANDIT`, `PDX`, `VENOM`, `PARADOX`, `RISING`,
  `TRAINER`, `CRACK` return nothing relevant (`pdx` hits are ordinary data).
* The last 8 bytes of the image are ASCII `baisoku!` at `0x7FFFF8` (inside the
  `0xFF` pad). This is a legitimate Vicarious Visions / Team Baisoku watermark,
  documented for other VV GBA titles (e.g. Batman Begins GBA at `FFFFF0`); it is
  **not** a patch signature. The image hashes as the known good dump.
* Audio middleware banner `GAX Sound Engine 3.03A (Jun 30 2003)` /
  `Shin'en Multimedia. Code: B.Wodok` at `0x7DC808`.

Developer: Vicarious Visions (credits). Engine: Vicarious Visions GBA engine
with Shin'en GAX audio.

## 2. Executive summary

**This GBA SKU has no password system, no button-code cheat system, and no
reachable debug menu.** The report below proves that as a bounded negative over
the whole image, and documents the two in-game surfaces that do exist: the
save-slot/level-select hub (with an `Options` cell) and the four-item in-level
pause menu.

* There is no password screen, no alphabet screen, no code-entry UI. Across
  105,224 ASCII strings (length ≥ 4) there are **zero** occurrences of
  `password`, `cheat`, `debug`, `secret`, `unlock`, `continue`, `pause`,
  `gallery`, `extras` (case-insensitive, and also as UTF-16LE/BE). The only
  `code` hit in the whole image is the audio middleware banner
  `Shin'en Multimedia. Code: B.Wodok`.
* The only text entry in the game is the 3-character **initials** field, and it
  is a save-slot label, not a validator: its 32-symbol alphabet accepts
  arbitrary symbols (`♠♣&` was entered and displayed as a slot name), and its
  value is copied to the save record and rendered.
* Published GBA "codes" for this title are only Action Replay / GameShark /
  CodeBreaker **memory** codes (e.g. the `0000414C 000A` enable code). Those are
  out of scope and are not in-game cheats.
* The 16-bit *Lion King* cheats (Genesis `Right,A,A,B,Start`; SNES
  `B,A,R,R,Y`; GB pause `B,A,A,B,A,A`) were re-tested in adapted form on the
  corresponding GBA screens. None produces a cheat screen, level skip or
  invincibility.
* The text bank contains the VV-engine debug strings **`defeat level`** and
  **`slow motion`**, but the retail pause menu builds exactly **four** items in
  RAM. No input path to the extra items exists in this build (see §6b/§7).
* In-game unlockables are the five bonus levels, five bonus movies, five
  worlds of 25 levels, and the `View Credits` cell of the level-select strip.
  They are unlocked by play, not by a code.

## 3. How to reproduce

Emulator: mGBA 0.10.x SDL, `DISPLAY=:340`, `SDL_AUDIODRIVER=dummy`.
Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows.

Exact path:

1. Boot → Vicarious Visions logo → title card with `Press Start`.
2. `Start` → `select a slot` (3 slots + `erase`). Choose a free slot → `enter initials: ___`
   (32 glyphs: `A-Z _ ! ? ♠ ♣ &`, 3 characters).
3. After the initials the **level-select hub** appears: a vertical film strip on
   the left, a preview panel on the right. `Up` from the first level selects the
   **`Options`** cell; `A` opens `options` → `credits`, `quit game`, `done`.
4. `A` on an unlocked level cell starts the level. In-level `Start` opens the
   pause menu: `resume`, `sleep`, `restart level`, `quit level`.
   * `sleep` → `sleep now?` panel with `resume`/`sleep` and the on-screen hint
     `press Select + L + R to wake`.
   * `quit level` → `quit level?` with `resume`/`quit level`; quitting returns
     to the level-select hub.
   * `restart level` restarts the level immediately (intro dialogue replays).
5. Slot screen `erase` → `erase a slot` → slot → `erase slot N?` with
   `cancel`/`erase`.

Savestates used: `lk1.ss1` (in level), `lk1.ss3` (pause open), `lk1.ss4`
(Options open). Screenshots were captured on the root window and cropped
`720x480+152+144`.

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`).

| Address | Meaning |
|---:|---|
| `0x0800E3C8` | Joypad update (Thumb). `held = (~KEYINPUT) & 0x3FF`; `pressed = held & ~previous`; stores `held` at `0x02002B10`, `pressed` at `0x02002B14`. |
| `0x04000130` | KEYINPUT register (literal in the update function and at `0x08026160`). |
| `0x02002B10` | Input state: +0 `held`, +4 `pressed` (8 bytes; no history buffer). |
| `0x0800B23C`, `0x0800B334`, `0x0800BABA`, `0x08014106`, `0x0801CCAA`, `0x0801CD56`, `0x0801EAC6` | The seven `BL` call sites of the joypad update. |
| `0x0800E3C8` readers | `0x08005650` (held bit 6), `0x08014F8C`/`0x08014FC8` (pressed & `0xF0`), `0x08015004`/`0x08015040`, `0x080109A8`, `0x08020E26` (pressed bit 0), plus update sites. |
| `0x08032C80` | String-pointer table, 164 entries. Entry *n* points at a 4-byte slot whose value is the `char*`. |
| `0x08032F14`… | String records: `[NUL-padded text][u32 pointer to that text]`. |
| `0x08033044` | `resume` |
| `0x08033050` | `restart level` |
| `0x08033064` | `quit level` |
| `0x08033074` | `sleep` |
| `0x08033080` | **`defeat level`** (text ID 26) |
| `0x08033094` | **`slow motion`** (text ID 27) |
| `0x080330A4` | `options` |
| `0x080330B0` | `credits` |
| `0x080330BC` | `quit game` |
| `0x080330CC` / `0x080330DC` / `0x080330EC` | `quit level?` / `quit game?` / `sleep now?` |
| `0x080330FC` | `press Select + [L] + [R]\nto wake` |
| `0x08033120` | `enter initials: ___` |
| `0x08034490`…`0x0803479C` | 37 level-select strings (see §6). |
| `0x02002BC0` | RAM mirror of a save slot record: name at +0x0A, marker `0x3F219FF2` at +0x10. |
| Save file | `.sav` 512 bytes: magic `0xC0DE600D` at 0x04; slot 1 name at 0x98; marker `0x3F219FF2` at 0xA0 (slot 2 at 0x14C). |
| `0x0816E8C`, `0x0817030`, `0x0817054` | Save-code literals `0xC0DE600D` and `0x3F219FF2`. |
| `0x7FFFF8` | `baisoku!` developer watermark (inside `0xFF` padding). |
| `0x7DC808` | GAX sound-engine banner. |

Observed menu objects (mGBA savestates, EWRAM):

| Menu | Item count word | Item-pointer array | Items |
|---|---:|---:|---|
| In-level pause | `0x02024D84` = **4** | `0x02024D98` | `0x02024E28` resume, `0x02024E68` sleep, `0x02024EA8` restart level, `0x02024EE8` quit level |
| Level-select Options | `0x02005FE8` = **3** | `0x02005FFC` | credits, quit game, done |

Item records are 0x40-byte widget objects; the menu's pointer array stores
`object+0x08` (the class word), and the displayed `char*` is at `object+0x0C`
(verified in both menus).

## 5. Algorithm

There is no code/validator algorithm to reimplement. The relevant machinery is:

### 5.1 Joypad

```c
u16 keys  = *(volatile u16*)0x04000130;
u16 held  = (~keys) & 0x3FF;          // active-high
u16 pressed = held & ~input->held;    // edge
input->held = held;                   // 0x02002B10
input->pressed = pressed;             // 0x02002B14
```

`0x0800E3C8` returns 0 when A+B+Select+Start (the low four held bits) are all
held, and 1 otherwise; no caller builds a sequence from it. The state is
8 bytes; there is no press-history ring buffer.

### 5.2 Menus

Menu items are 0x40-byte heap widget objects referenced from a count-and-array
menu object (see §4). Text comes from the string table at `0x08032C80`; each
entry is a `char**`. Observed menu contents are listed in §4. Nothing in the
menu system has a hidden-item or debug-item branch that is exercised by input.

### 5.3 Text input

The initials screen writes 3 characters into the save record and returns to the
hub. Any of the 32 glyphs is accepted; there is no comparison, checksum or
rejection path on the value.

### 5.4 Save marker

`0x3F219FF2` is a ROM constant (`0x0817030`, `0x0817054`) written into each
slot record; `0xC0DE600D` is the save-block magic. Neither is a password
checksum.

## 6. Tables

### 6.1 Menu/debug strings (text IDs from `0x08032C80`)

| ID | Text | Address |
|---:|---|---:|
| 10 | `Press Start` | `0x08032F88` |
| 11 | `select a slot` | `0x08032F98` |
| 14 | `new game` | `0x08032FD4` |
| 17 | `done` | `0x08033000` |
| 18 | `cancel` | `0x0803300C` |
| 19 | `Best Time` | `0x08033018` |
| 20 | `Locked` | `0x08033028` |
| 21 | `Time's Up` | `0x08033034` |
| 22 | `resume` | `0x08033044` |
| 23 | `restart level` | `0x08033050` |
| 24 | `quit level` | `0x08033064` |
| 25 | `sleep` | `0x08033074` |
| 26 | `defeat level` | `0x08033080` |
| 27 | `slow motion` | `0x08033094` |
| 28 | `options` | `0x080330A4` |
| 29 | `credits` | `0x080330B0` |
| 30 | `quit game` | `0x080330BC` |

IDs 26 and 27 are present in the bank but in no menu object built by the game.

### 6.2 Level-select strip (37 cells, `0x08034490`–`0x0803479C`)

| # | Cell | Kind |
|---:|---|---|
| 1 | `Options` | menu cell |
| 2-5 | Colony Life; When Hyenas Attack; The Lone Warthog; Warthog on my Shoulder | world 1 |
| 6 | `Timon Bonus Level 1` | bonus |
| 7 | `Bonus Movie 1` | movie |
| 8-11 | Pride Land Rush Hour; Cave Sweet Cave; Noisy Neighbors; The Sky is Falling | world 2 |
| 12 | `Pumbaa Bonus Level 1` | bonus |
| 13 | `Bonus Movie 2` | movie |
| 14-19 | The Land of Bones; Make a Run for It; Out of the Frying Pan; Oh no, Hyenas!; Land of the Blinding Sun; Stampede! | world 3 |
| 20 | `Team Bonus Level` | bonus |
| 21 | `Bonus Movie 3` | movie |
| 22-25 | Open House; Scaring the Buzzards; Hide N Seek; Nala! | world 4 |
| 26 | `Timon Bonus Level 2` | bonus |
| 27 | `Bonus Movie 4` | movie |
| 28-34 | Pumbaa's Stand; Finding Pumbaa; The Cavalry Arrives; LUAU!!!; The Big Fight; Digga Tunnah; Tunnel Escape | world 5 |
| 35 | `Pumbaa Bonus Level 2` | bonus |
| 36 | `Bonus Movie 5` | movie |
| 37 | `View Credits` | movie/credits |

Totals: 25 normal levels (worlds of 4/4/6/4/7), 5 bonus levels, 5 bonus
movies, 1 credits entry, 1 Options cell. The hub shows a `0/40` bug counter for
the selected level, a heart/life count, and `% complete` per slot.

### 6.3 16-bit *Lion King* codes re-tested (adapted to GBA buttons)

| Source | Original | GBA mapping tested | Result |
|---|---|---|---|
| Genesis | Options: `Right, A, A, B, Start` | same | No cheat screen; back on `options` |
| Genesis | Options: `Right, A, B, C, Start` | `C`→R: `Right, A, B, R, Start` | No change |
| SNES | Options: `B, A, R, R, Y` | `Y`→L: `B, A, R, R, L` | Started credits reel, no secret menu |
| SNES | Options: `B, A, R, R, Y` | `Y`→Select: `B, A, R, R, Select` | Started credits reel, no secret menu |
| SNES | Hold `A+B` on Options | hold A+B 1.5 s | Started credits reel, no secret menu |
| GB | Pause `B, A, A, B, A, A` | same (B closes GBA pause) | No level skip; still Colony Life |
| SMS/GG | Rotate D-pad clockwise at Sega logo | clockwise sweep ×3 on title | No sound, no change (no Sega logo in this SKU) |

In the two SNES rows and the A+B row the credits reel started because the first
`options` item is `credits` and A activates it; no secret menu was created. The
GBA `options` screen has only `credits`, `quit game`, `done`.

Published GBA lists (GameHacking.org, CodeTwink) contain only memory codes
(Action Replay MAX, GameShark/CodeBreaker, Xploder). They are deliberately not
used or reproduced here. The 16-bit codes above come from GameFAQs' Genesis,
SNES and GB cheat pages; the GBA `options` screen is a different, three-item
menu, so the 16-bit codes are not expected to map literally, but were tested
anyway to close the "code from another version" question.

Sources consulted: GameHacking.org `game/5136` (memory codes only), CodeTwink
`view-cheats-1270`, GameFAQs Genesis/SNES/GB *Lion King* cheat pages, and the
TCRF mirror page for *Batman Begins* GBA (same VV engine; documents the
`baisoku!` watermark and the `Defeat Level`/`Slow Motion` debug leftovers).

## 6b. Enumeration

**Space definition.** There is no code space.

* Alphabet/length/checksum: none. No string in the image advertises an entry
  surface (`password`/`cheat`/`code entry`); the only textual `code` is the
  audio banner. No input screen other than the 3-character initials label
  exists.
* The initials field: alphabet `A-Z _ ! ? ♠ ♣ &` (32 glyphs), length 3 →
  **32³ = 32,768 representable strings**. It is a label, not a validator:
  `AAA` and the extreme glyphs `♠♣&` are both accepted and rendered in the
  `select a slot` list (`AAA - 0%`, `♠♣& - 0%`). There is no rejection path.
* Button input: the whole input state is `held`/`pressed` (8 bytes,
  `0x02002B10`), updated once per frame by `0x0800E3C8`; the update stores only
  those two words. The seven `BL` call sites of the update were located. The
  consumers disassembled (`0x08005650`, `0x08014F8C`, `0x08014FC8`,
  `0x08015004`, `0x08015040`, `0x080109A8`, `0x08020E26`, `0x0801EAC4`) each
  test one single-frame bit or nibble (D-pad mask `0xF0`, A bit, held bit 6);
  none keeps a press-history array. No multi-press state exists in the input
  structure or in the menu objects observed.
* Static mask-table search: an 8 MiB scan for aligned `u16` runs of ≥4 values
  drawn from the 55 single/double-button masks found 529 runs. The runs in level
  data are repeated button-glyph prompt patterns (e.g. `R+Right` at
  `0x233BB4`); the rest sit inside compressed graphics. No run in an executable
  literal pool forms a 4-step cheat sequence.

**Novel code.** None can be minted because the code space is empty. This is the
§0.2 point-5 case: the deliverable is the bounded negative, not a code.

**Bounds proven by rejection.**

1. The initials field cannot express an invalid string: every glyph is
   accepted; `♠♣&` (glyph indices 29, 30, 31) is stored and displayed. There is
   no "invalid initials" state.
2. Locked levels cannot be selected: with only `Colony Life` unlocked, the
   cursor will not move below it; the remaining cells are drawn as `???`
   frames. `Locked` (id 20) exists as text but the selection bound rejects the
   move.
3. The 16-bit codes are rejected in every adapted form tested (§6.3): no new
   menu, no level skip, no invincibility.

**Debug-items bound.** The retail pause menu object contains **4** items
(`0x02024D84 = 4`), and its array holds exactly resume/sleep/restart/quit. The
strings `defeat level` and `slow motion` are in the text bank (IDs 26/27) but
not in any built list. `defeat level`/`slow motion` are the same unused debug
leftovers TCRF documents in *Batman Begins* GBA (another VV/Team Baisoku
title), where the debug display is enabled by an external memory poke, not by
game input. No in-game path was found here.

## 7. Validation evidence

**Observed (emulator / RAM):**

* Title, slot select, initials, level-select hub, Options cell, options menu,
  credits, in-level pause, sleep confirm, quit confirm, erase confirm — all
  walked and screenshotted; `Options` is reached with `Up` from the first
  level; `quit level` returns to the hub; `restart level` replays the intro.
* Pause menu RAM count = 4 with the four item pointers listed in §4.
* Options menu RAM count = 3.
* Slot names `AAA - 0%` and `♠♣& - 0%` in the slot list.
* The 16-bit codes and button combinations listed in §6.3 produce no cheat
  screen/level skip.
* The `.sav` record: `C0DE600D` magic, slot name, `3F219FF2` marker.

**Derived (instruction / data evidence):**

* No password/cheat/debug/secret/unlock string in ASCII, lowercase, UTF-16LE
  or UTF-16BE (0 hits each over 8 MiB; 105,224 ASCII strings ≥4).
* The joypad state is 8 bytes with no history buffer (`0x0800E3C8`).
* The joypad consumers examined are single-frame conditions (disassembly at the
  addresses in §4); none maintains a press sequence.
* The 529 button-mask runs are not referenced by input code.
* `0x3F219FF2` and `0xC0DE600D` are ROM constants used by the save code, not
  password checksums.

**Inferred:**

* `defeat level` and `slow motion` are developer/debug pause items from the
  shared VV engine, disabled in this retail build. The RAM count of 4 and the
  absence of any input path support this; the exact debug flag address was not
  located.
* Unlock triggers (40 bugs → puzzle piece; world completion → bonus level and
  movie) follow the on-screen counters and the published design description;
  the per-item save bit layout was not decoded because it is not part of the
  code question.

## 8. Unknowns

* The address and writer of the hypothetical VV debug flag. The equivalent
  Batman Begins GBA debug display is enabled by poking RAM; in this ROM the
  flag was not found, and no in-game input sets it.
* Whether an undiscovered *single-name* easter egg exists on the initials
  field. No comparison constants or code path were found; the field is a label.
* The exact checksum/validity meaning of `0x3F219FF2` (constant marker vs seed)
  beyond its use in the save code.
* Full 100% unlock behaviour (bonus levels/movies) was not the subject of the
  cheat question; the cell list and counters are proven from the ROM and hub UI.

## 9. Tooling

* `binutils-arm-none-eabi` (`objdump -M force-thumb`), Capstone 5.0.7 for raw
  Thumb scans.
* mGBA SDL under `Xvfb :340` + `openbox`; `xdotool` for input; ImageMagick
  `import`/`convert`/`compare` for screenshots.
* Python 3 scripts: literal/pointer searches, key-mask run scan, mGBA savestate
  (`gbAs` zlib chunk) parser and EWRAM diffs.
* Artifacts in `/tmp/lionking1`: `ctl.py`, `strings4.txt`,
  `refs.txt`, savestates `lk1.ss1/ss3/ss4`, screenshots (`shot_*.png`,
  `opt2_c.png`, `credits2_c.png`, `ls3_c.png`, `sleep_c.png`, `erase2_c.png`,
  `gen1_c.png`, `gen2_c.png`, `snes1_c.png`, `snes2_c.png`, `gb1_c.png`,
  `sweep_c.png`, `slots2_c.png`, `init2_c.png`), and the ROM copy used for
  testing.

## 10. Legal note

No ROM, graphics, music or game text is redistributed here. Only hashes,
addresses, layout, and the analyst's own observations are published.
