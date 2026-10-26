# Barbie Software: Groovy Games (GBA) — Reverse Engineering Report

Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

Scope: **in-game / developer-intended cheats only** (passwords, button codes,
hidden/debug menus, unlockables). GameShark/CodeBreaker/RAM patches are out of
scope and were not used.

Result in one line: **this cartridge has no password system, no button-code
matcher, no debug menu and no unlockables.** Every one of the nine minigames and
all seven characters are available on a cold boot, and no save data was written
in the tested path. The only hidden, developer-intended input is **`SELECT` on the
`Press Start` title screen, which opens the full credits roll** — a hidden
screen, not a cheat. The published "Unlimited Health" code is a generic fake
for a game that has no health stat; the `GROOVY100`/`FREEDRESS` codes on one
content-farm page are not in the ROM and cannot be entered.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Barbie Software: Groovy Games/Barbie Software: Groovy Games.gba` |
| Size | 4 194 304 bytes (`0x400000`, 32 Mbit) |
| Header title (`0xA0`) | `GROOVY GAMES` (12 chars, no NUL padding) |
| Game code (`0xAC`) | `AVBE` (Europe) |
| Maker code (`0xB0`) | `7D` |
| Software version (`0xBC`) | `0` |
| Fixed byte (`0xB2`) | `0x96` |
| Complement (`0xBD`) | `0x45` — valid (`-(sum 0xA0..0xBC + 0x19) & 0xFF`) |
| Header checksum (`0xBE`) | `0x0000`; the correct value would be `0x4545` |
| Entry (`0x00`) | `0xEA00002E` → ARM branch to `0x080000C0` |
| MD5 | `c1b8fbfc0f67a1f8e0c60543167b7dba` |
| SHA-1 | `055db9f8f3ba18358162a1411cf24300a6de6046` |
| SHA-256 | `6f1be00d689168a35c9a04f21dad9b26026423dd3bfa1225339ac4c2af1f99c8` |

All ROM addresses below are `0x08000000 + file_offset`; all claims are tied to
this exact hash.

### 1.1 Header scan and patch note

* Scanning the whole 4 MiB file for the 156-byte Nintendo logo finds **exactly
  one** header, at file `0x0` (logo at `0x4`). This is a single GBA image, not a
  multi-game concatenation; there is no second crt0, no second Nintendo logo and
  no "choose a game" shell.
* The complement check is valid. The **header checksum field is zero**, while
  the correct value is `0x4545`. That is the only header anomaly. It is
  consistent with other dumps in this workspace collection (e.g. the
  Asteroids/Pong/Yars' Revenge report also stores `0x0000`) and is most likely a
  dump/header-tool artifact. No cracktro, no altered title, no altered text and
  no code patch was found; the game boots from the standard `0x080000C0` entry
  and the startup logos are the retail ones. Label: **inferred** (header patch
  provenance not proven).
* Last non-`0xFF` byte is at file `0x3D248B`; the remaining ~183 KiB to the 4 MiB
  boundary is blank `0xFF`, normal cartridge padding. No hidden payload was found
  in the padding.

### 1.2 ROM layout (observed / derived)

| File range | Contents |
|---|---|
| `0x000000`–`0x2D0000` | ARM/Thumb code, literal pools, engine tables, graphics/audio data |
| `0x2D0000`–`0x3C0000` | game scripts/data, graphics, audio, level data |
| `0x3C0CA0`–`0x3D19F5` | ASCII text bank: five-language help text, Daisy Derby word lists, staff credits |
| `0x3D1A00`–`0x3D248B` | small tables/data after the credits; then `0xFF` padding |
| `0x3D248C`–`0x3FFFFF` | `0xFF` padding |

The executable code does **not** contain a password table or a code-entry
string. The only large ASCII bank is the text bank above; everything else that
looks like text is graphics/compressed data or the asset-name block discussed in
§8.

---

## 2. Executive summary

### 2.1 No password system

The complete reachable UI was walked. It has no password, passcode, code-entry,
name-entry or "continue with a code" screen:

* Text scan over the whole ROM: `password` 0, `passcode` 0, `passwd` 0, `code`
  0, `cheat` 0, `debug` 0, `unlock` 0, `hidden` 0, `level` 0, `menu` 0,
  `option` 0.
* The only `secret` hits (11) are the Daisy Derby help phrase "secret word" and
  the word `SECRET__` / `SECRETO_` in the localized word lists. The only
  `select` hits (6) are help text, and the only `sound`/`test` hits are
  "SOUND AND MUSIC" and "QA TESTERS" in the credits.
* The only alphabet entry in the game is **Daisy Derby's hangman letter
  picker**: one letter per turn from A–Z, used to guess a pre-chosen word. It
  does not accept a string and has no submit/validate step.

### 2.2 No button-code matcher

The keypad is read once per frame by one ARM routine at `0x08024BCC`, which
keeps exactly three 16-bit words (no other keypad-register read was
identified):

| Address | Meaning | Idle value |
|---|---|---|
| `0x03000000` | held keys, previous frame | `0xFC00` |
| `0x03000004` | held keys, current frame | `0xFC00` |
| `0x03000008` | keys newly pressed this frame (edge) | `0x0000` |

Bit 0–9 are active-high `A, B, Select, Start, Right, Left, Up, Down, R, L`;
bits 10–15 are always set because the register is inverted as a 32-bit value.
There is **no sequence index, no ring buffer and no history word**. A dump of
`0x03000000`–`0x030003FF` at boot shows only those three words nonzero; the rest
is zero.

The whole ROM was scanned for tables of three or more consecutive key masks, in
both active-high and active-low form. The only runs found are ordinary data
tables (values such as seven `0x0008`, seven `0x0040`, four `0x0080` in a
sprite/timing table at `0x080282E8`–`0x080283C6`, and one three-entry coincidence
inside graphics at `0x081F5E0E`). None is loaded as a key table, and no run has a
validator or terminator. The published six-press code is not present as a byte
or halfword sequence either.

### 2.3 One hidden screen: `SELECT` at the title opens the credits

On the `Press Start` title screen, pressing **Select** fades to a blue
`Credits` roll. It auto-scrolls through the ASCII credits text at
`0x083D11BF`–`0x083D19F5` and returns to the title after roughly 56 seconds
(measured at default emulator speed). **B** exits immediately. The same Select
press has no effect on the player select, character select, opponent select,
game select or in-game screens; in the pause menu Select simply resumes play.
This is a developer-intended hidden screen (an easter egg), **not** a gameplay
cheat: it changes no game state and unlocks nothing.

### 2.4 Everything is unlocked; nothing is saved

From a cold boot, with a zero-byte save:

* 9/9 minigames are selectable in the `Where Shall We Play?` wheel;
* 7/7 characters are selectable (Barbie, Lea, Kayla, Christie, Teresa, Becky,
  Ken, then wrap to Barbie);
* all 3 difficulties (easy, medium, hard) are selectable;
* no icon shows a lock, a price, a token count or a "?" slot.

A completed Bubble Machine match (played to the `play again? yes/no` result
screen) left the `.sav` at **0 bytes**, including after the emulator was
stopped. No persistent progress or unlock flags are written by the tested
path.

### 2.5 Published codes and their disposition

| Source | Code / claim | Result in this ROM |
|---|---|---|
| GameFAQs (archived) | `Up, Down, Left, Right, B, A` — "Unlimited Health" for 5 HP or less | No health stat or HUD exists. At the title the sequence only uses B to return to the attract; at pause it is ordinary cursor/flip input. **Inapplicable/fake.** |
| cheatingdome / games-cheats / 53lu | same Unlimited Health code | Same as above. |
| classicemu (machine-generated page) | `GROOVY100` (100 coins), `FREEDRESS` (all dresses free) | Literal search: **0 hits**. No coin, dress, shop or text-entry system exists. **Fabricated / not this game.** |
| mariogba / emuinfo (Barbie Superpack 2-in-1) | Secret Agent level passwords: `BBBBCG`, `CBBDCX`, `DBBFCM`, `FBBFFQ`, `GBBPFH`, `HBBPKN`, `JCBPKQ`, `KCBTKC`, `LCGTKJ`, `MCHTKL`, `NCHTTC`, `PCRTTN`, `TTTTTS` | All 13 literals: **0 hits** in this standalone `AVBE` ROM. They belong to the Secret Agent half of the 2-in-1, not this cartridge. |

The GameFAQs page was read through an archive snapshot because direct fetching
is blocked; the archived text is unambiguous (one cheat, contributed by
`tiamold2`).

---

## 3. How to reproduce

### 3.1 Emulator and keymap

```bash
Xvfb :167 -screen 0 1024x768x24 &
DISPLAY=:167 openbox &
DISPLAY=:167 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 \
  "roms/Barbie Software: Groovy Games/Barbie Software: Groovy Games.gba" &
```

mGBA 0.10.5 (SDL). Default SDL keymap used throughout:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

The mGBA viewport is 720×480 at `+154+184` on this 1024×768 display; screenshots
were cropped with `convert -crop 720x480+154+184 +repage`.

### 3.2 Boot and menus

1. Boot. The startup logo reel is long: white → Barbie Software → Vivendi
   Universal → DICE Canada → intro/attract. Wait ~45–60 s under load; do not
   mistake the white transition between logos for a crash.
2. `Press Start` title. **Start** → player select. **B** → attract. **Select** →
   hidden credits (§3.4).
3. Player select: `1 player` / `2 players`. **A** on 1 player → character
   select.
4. Character select (`I Want to Be`): Left/Right cycles Barbie, Lea, Kayla,
   Christie, Teresa, Becky, Ken, then wraps. **A** → opponent select
   (`I'll Play Against`, same presentation).
5. **A** → game select (`Where Shall We Play?`). The wheel lists, in order:
   D.J. Booth, Tic-Tac-Toe, Four Scoops, Bubble Machine, Checkers, Daisy Derby,
   Groove and Move, Conga Line, Gems and Jewels, then back to D.J. Booth. Use
   Left/Right; the wheel ignores input while it is still spinning, so press
   once per ~1.5 s real time under emulator load.
6. **A** → difficulty (`easy` / `medium` / `hard`). **A** → ready
   (`How to Play` / `Start Game`). **A** on Start Game → per-game screen; for
   example Conga Line shows a further `Press A to Play Barbie` prompt, while
   Checkers first shows `Choose a Piece`.
7. In game: **Start** opens the pause box `continue / restart / exit`.
   **Select** in the pause box resumes immediately. Exit returns to the game
   select wheel.
8. Finish a game to see `play again? yes/no` (Bubble Machine reaches this after
   roughly 1.5–2 minutes of no input; the bubbles fall to the floor).

### 3.3 Exact input for the published code

`Up, Down, Left, Right, B, A` — hold each key ~150–250 ms, with ~250 ms between
presses. At the title this ends with B returning to the attract; at pause it
moves the cursor and flips a CD. Both were screenshotted; no health/stat change
exists.

### 3.4 Hidden credits

1. Cold-boot to `Press Start`.
2. Press **Select** once.
3. A white fade appears; after ~1 s the blue `Credits` screen starts scrolling.
4. It automatically returns to `Press Start` after ~56 s; **B** exits early.

### 3.5 Savestates used

A savestate at the title (slot 3) and at the game-select wheel (slot 4) made the
repeated tests cheap. Loading a slot is **F1–F10**; saving is
**Shift+F1–F10**. Under Xvfb, make sure the 720×480 mGBA window has focus before
sending hotkeys — a second 240×160 debugger window can steal them.

---

## 4. Address map

| Address | Size | Contents |
|---|---|---|
| `0x08024AB8` | 0x2C | init of the three input words (writes `0xFFFF` to each) |
| `0x08024AF4` | 0x44 | accessor `pressed(mask)` — reads `0x03000008`, returns `arg & word` |
| `0x08024B3C` | 0x44 | accessor `held(mask)` — reads `0x03000004` |
| `0x08024B84` | 0x44 | accessor `previous_held(mask)` — reads `0x03000000` |
| `0x08024BCC` | 0xB0 | **keypad poll**, ARM; reads `0x04000130`, writes the three words |
| `0x08024C74` | call | key-repeat helper call to `0x08026FD4` with `r0 = 0xFF` when repeat counter reaches 15 |
| `0x08026FD4` | — | key-repeat/edge helper used by the poll |
| `0x03000000` | u16 | held keys, previous frame |
| `0x03000004` | u16 | held keys, current frame |
| `0x03000008` | u16 | newly pressed keys (edge) |
| `0x083C0CA0` | ~0x20 | first English help text (`Use the Control Pad …`) |
| `0x083C3DF9` | — | German help section (`Benutze …`) |
| `0x083C6C45` | — | French help section (`Utilisez …`) |
| `0x083CB973` | — | first word-list section (English words) |
| `0x083D11BF` | 0x836 | credits text (starts `0x80 0x0D 0x0A`, then `  Vivendi Universal Games`) |
| `0x083D19F5` | — | end of credits (`0x80 0x0D 0x0A 0x00 0x43`) |
| `0x082887C` | 0x4C | pointer table into the word-list/text bank (localized blocks) |
| `0x0829FF4` | 0x90 | pointer table into help/word-list strings |
| `0x0829E68` | 0x18C | asset-name/profanity-filter word block (see §8) |

There is **no password table, no validator, no code-entry buffer and no flag
word** to list. The only "flag-like" state is the screen/task state owned by the
engine; the credits screen is entered by a UI branch, not by a cheat flag.

The poll function is not reached by a direct `BL`/`BLX` in the ROM; it is called
through the engine's frame/task callback (the exact callback pointer was not
resolved). Its code is nevertheless self-contained and unambiguous; it is the
only keypad-register read identified in the image (it computes
`0x04000000 + 0x130`).

---

## 5. Algorithm

### 5.1 Keypad poll (reimplementation)

```python
# ARM routine at 0x08024BCC; 0x04000130 is active-low
raw    = ldrh(0x04000130)           # idle 0x03FF
held   = (~raw) & 0xFFFF            # idle 0xFC00; low 10 bits = pressed keys
prev   = ldrh(0x03000004)           # held last frame
[strh 0x03000000] = prev            # previous-frame held
pressed = held & (held ^ prev)      # rising edges this frame
[strh 0x03000008] = pressed
[strh 0x03000004] = held
# if a repeat counter reaches 15: call 0x08026FD4(0xFF)
```

Accessors are simply `arg & word` for the three words. There is no shift
register, no `seq[index]`, no comparison against a multi-key constant and no
table lookup in this path.

### 5.2 Screen/task behaviour

The game is a conventional task/screen engine: a title task, player/character/
opponent/game/difficulty/ready tasks, one task per minigame, a shared pause
box, a shared `play again?` box and the credits screen. The only key handling of
interest for this engagement is the title task's Select branch, which switches
to the credits screen. The branch address was not isolated (the credits text is
loaded from `0x083D11BF` by the text renderer, but the task dispatch is
indirect); behaviour is observed and reproducible.

### 5.3 No password algorithm exists

There is no encoder, decoder, checksum, alphabet table or comparison loop to
reimplement. The game does not ask for a code anywhere.

---

## 6. Tables

### 6.1 Game roster (observed, wheel order)

| # | Game | Help text present | Entered |
|---:|---|---|---|
| 1 | D.J. Booth | yes | yes |
| 2 | Tic-Tac-Toe | yes | yes |
| 3 | Four Scoops | yes | yes |
| 4 | Bubble Machine | yes | yes |
| 5 | Checkers | yes | yes (`Choose a Piece`, board) |
| 6 | Daisy Derby | yes | yes (horse select + letter picker) |
| 7 | Groove and Move | yes | yes |
| 8 | Conga Line | yes | yes (play + pause) |
| 9 | Gems and Jewels | yes | yes |

The wheel wraps 9 → 1. No tenth icon, "?" slot or locked entry exists.

### 6.2 Character roster (observed, player select)

`Barbie` (default), `Lea`, `Kayla`, `Christie`, `Teresa`, `Becky`, `Ken`, then
wrap to `Barbie` — 7 entries. Opponent select uses the same presentation and
character art (`I'll Play Against`); one opponent (Barbie/Kayla) was observed.

### 6.3 Menus and options

| Screen | Entries | Effect |
|---|---|---|
| Title | `Press Start` | Start → player select; B → attract; **Select → credits** |
| Player select | `1 player`, `2 players` | A chooses; B back |
| Character select | 7 characters | A chooses; B back |
| Opponent select | same roster | A chooses; B back |
| Game select | 9 games | A chooses; B back |
| Difficulty | `easy`, `medium`, `hard` | A chooses; B back |
| Ready | `How to Play`, `Start Game` | A chooses; B back |
| Help | scrolling text, `Press START to Exit Help` | A advances the text; Start exits |
| In-game prompt | `Press A to Play Barbie` (Conga Line), `Choose a Piece` (Checkers/Tic-Tac-Toe) | A starts/chooses |
| Pause | `continue`, `restart`, `exit` | A selects; Select resumes |
| Result | `play again? yes / no` | A selects |
| Hidden | `Credits` (blue scroll) | Select at title; B exits; auto-return ~56 s |

### 6.4 Key masks

`A=0x0001, B=0x0002, Select=0x0004, Start=0x0008, Right=0x0010,
Left=0x0020, Up=0x0040, Down=0x0080, R=0x0100, L=0x0200` (active-high),
stored OR-ed with `0xFC00` in the two held words.

### 6.5 Published-code disposition

See §2.5. None of the published code strings occurs anywhere in this ROM; the
only occurrence of the word `GROOVY` is the cartridge title at `0xA0`.

---

## 6b. Enumeration

**No code can be minted because the cartridge has no code/password/matcher
system.** The deliverable is therefore the bounded negative below: every screen
was walked, every text and mask space was scanned, every published code was
tested or shown impossible, and the one hidden input was found and documented.

### 6b.1 Space definition

| Surface | Size | Evidence |
|---|---:|---|
| Password / passcode strings | **0** | whole-ROM string scan (counts §6b.2) |
| Password/passcode entry screens | **0** | all reachable screens walked |
| Text-entry fields | **0** | only Daisy Derby's single-letter hangman picker |
| Button-sequence matcher | **none representable** | 3 input words only; no mask table; §6b.3 |
| Hidden/debug screens | **1** (credits) | Select at title; §6b.5 |
| Unlockables | **0** | 9/9 games, 7/7 characters on cold boot; no save writes |
| Save bytes written | **0** | `.sav` stays 0 bytes through a completed match and emulator stop |
| Minigames | 9 | wheel table / visual enumeration |
| Characters | 7 | select-screen enumeration |
| Difficulties | 3 | easy/medium/hard |
| Keys read | all 10 captured | poll at `0x08024BCC` |

### 6b.2 Text space

* Printable runs (`[ -~]{8,}`) over the whole file: **28 261**; over the text
  bank `0x3C0000`–`0x3D3000`: **4 253**.
* Case-insensitive counts over the whole file: `cheat` 0, `debug` 0,
  `password` 0, `passcode` 0, `passwd` 0, `unlock` 0, `code` 0, `hidden` 0,
  `level` 0, `menu` 0, `option` 0, `secret` 11, `select` 6, `sound` 1, `test` 1.
* Classification of the non-zero hits: `secret` = ten Daisy Derby help phrases
  ("secret word") plus `SECRET__`/`SECRETO_` word-list entries; `select` = help
  text; `sound` = credits "SOUND AND MUSIC"; `test` = credits "QA TESTERS".
  None is a code, a validator or a menu label.
* The UI itself is largely baked graphics: words such as `Press Start`,
  `Where Shall We Play?`, `Pause` and `Play again?` do not exist as ASCII. The
  negative therefore rests on the screen walk (§6b.4), not on string absence
  alone.
* Text bank contents were fully classified: five-language help, localized Daisy
  Derby word lists (English/French/German/Spanish/Italian), and the credits.
  No unused "debug" text bank was found.

### 6b.3 Button-code space (whole ROM)

| Scan | Space | Result |
|---|---|---|
| u16 runs over key masks `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}`, length ≥3 | 69 runs | all are data/graphics runs (examples in the sprite/timing table `0x08027198`–`0x08028762`: seven `0x0008`, seven `0x0040`, four `0x0080`); none is loaded as a key table and none has a terminator/validator |
| Same over active-low complements `{0x3FF^m}`, length ≥3 | 1 run | `0x081F5E0E`: `0x3FD, 0x3FE, 0x3FD` (3 values) inside graphics; not a table |
| Published `UDLRBA` as u8 and u16 | 4 encodings | **0 hits** |
| Input-layer history buffer | `0x03000000`–`0x030003FF` | only 3 nonzero words at boot; no ring buffer/index |
| Reads of the edge word `0x03000008` | literal references | 3 real code refs (init `0x08024AEC`, accessor literal `0x08024B38`, poll literal `0x08024C88`); the many `0x2Dxxxx` hits are a false-positive pattern in script data (`08 00 00 03` across record boundaries) |
| Reads of `0x03000004` | literal references | 3 (`0x08024AF0`, `0x08024B80`, `0x08024C80`) |
| Reads of `0x03000000` | literal references | many, mostly data; real code refs include init and the poll |

A sequence gate of length ≥2 must either store the sequence (table) or retain a
progress index/history. The ROM has no such table in code, and the input layer
retains no such state. This makes the published six-press code impossible
independently of the empirical test below.

### 6b.4 Menu / screen space

Every reachable menu and top-level screen was walked and screenshotted (files
under `/tmp/opencode/barbie/shots`, this run):

| Screen | Trigger | Evidence file |
|---|---|---|
| Boot logos (Barbie Software, Vivendi, DICE Canada) | cold boot | `steps.png`, `b10_crop.png` |
| `Press Start` title | after logos | `b10_crop.png`, `cold2_crop.png` |
| Credits (hidden) | Select at title | `hidden_credits_crop.png`, `crl2_crop.png` |
| Player select | Start at title | `sel_psel_crop.png` |
| Character select (7, wrap) | A at player select | `chars.png`, `e_crop.png` |
| Opponent select | A at character select | `f_crop.png` |
| Game select (9, wrap) | A at opponent select | `gameselect_crop.png`, `games.png` |
| Difficulty (3) | A at game select | `h_crop.png` |
| Ready (`How to Play` / `Start Game`) | A at difficulty | `i_crop.png` |
| Help (scrolling) | Left+A at ready | `hp0..hp7` |
| D.J. Booth game | A Start Game | `tour0_game_crop.png` |
| Tic-Tac-Toe | wheel | `tour1_game_crop.png` (`Choose a Piece`), `ttt_board_crop.png` (board) |
| Four Scoops | wheel | `fs_end_crop.png` |
| Bubble Machine | wheel | `bub_play_crop.png`, `bw3_crop.png` |
| Checkers | wheel | `ck7_crop.png` (label), `checkers_game_crop.png` (`Choose a Piece`), `checkers_pause_crop.png` |
| Daisy Derby | wheel | `daisy_letter_crop.png` (horse select + letter picker) |
| Groove and Move | wheel | `tour8_game_crop.png` |
| Conga Line | wheel | `conga_play2_crop.png`, `conga_game_crop.png` (prompt) |
| Gems and Jewels | wheel | `full_gems_game_crop.png` |
| Pause (continue/restart/exit) | Start in game | `pz_crop.png`, `conga_pause2_crop.png` |
| Result (`play again?`) | finish Bubble Machine | `bx2_crop.png` |

No `Options`, `Sound Test`, `Level Select`, `Gallery`, `Trophy`, `Cheat` or
`Debug` screen exists anywhere in this inventory. The only per-game extra
screens are `Press A to Play Barbie` (Conga Line) and `Choose a Piece`
(Checkers/Tic-Tac-Toe).

### 6b.5 Hidden input: `SELECT` at the title

This is the one undocumented, developer-intended input found. It is **not a
cheat** (it changes no gameplay state, grants nothing and unlocks nothing), but
it is hidden content and is recorded here for completeness.

* Trigger: `Press Start` title, press **Select** once.
* Effect: white fade, then a blue `Credits` roll; text comes from the ASCII
  bank at `0x083D11BF`–`0x083D19F5` (`Vivendi Universal Games`, producers, QA,
  special thanks).
* Duration/exit: auto-returns to `Press Start` after about 56 s; **B** exits
  immediately. Reproduced on a cold boot twice.
* No other screen responds to Select: player select, character select, opponent
  select, game select and in-game are unchanged; in the pause box Select
  resumes the game; on the title it is the credits branch.

The credits roll is also the only place in the game where the strings
`SOUND AND MUSIC` and `QA TESTERS` appear (§6b.2), which ties the hidden screen
to the credits bank.

### 6b.6 Published-input and rejection tests

| Test | Exact input | Result |
|---|---|---|
| "Unlimited Health" (GameFAQs/cheatingdome/53lu) | `Up, Down, Left, Right, B, A` at title | U/D/L/R no-op; **B returned to attract**; A no-op. No health exists; no state change (`ti_after2_crop.png`) |
| Same at pause | `Up, Down, Left, Right, B, A` while paused | Select (pressed first to test) resumed the game; the sequence moved the cursor and flipped a CD as normal input (`pause_udlrba_crop.png`); no cheat state |
| Konami sequence | `Up Up Down Down Left Right Left Right B A` at title | normal navigation; no hidden screen (`titlecodes`/`tx` sheets) |
| Select at non-title screens | player, character, opponent, game select, in-game | screen unchanged (identical screenshots) |
| Select in pause | pause box | resumes play (normal UI action) |
| `GROOVY100`, `FREEDRESS` (classicemu) | literal search + entry attempt | 0 literal hits; no text-entry field exists; **cannot be entered** |
| 13 Superpack Secret Agent passwords | literal search | 0 hits each; wrong half/product |
| Multi-letter text entry | any screen | no free-text field; Daisy Derby accepts exactly one A–Z guess per turn |

No out-of-range "field" exists to reject. The closest representation bound is
the button space: a six-press sequence cannot be stored by this input layer, and
the only 1-press hidden action (`Select` at the title) has exactly one effect.

### 6b.7 Why the negative is conclusive

1. **No entry screen:** all reachable screens are enumerated in §6b.4; there is
   no password/passcode/name/code field. The only alphabet input is a hangman
   letter guess.
2. **No code text:** the complete ASCII bank is classified; all non-zero
   keyword hits are help/word-list/credits text. The visible UI labels are
   graphics, but the screen walk covers them.
3. **No matcher:** the entire keypad state is three 16-bit words with no history;
   the ROM contains no key-mask table loaded by code, and no `UDLRBA` literal in
   either byte or halfword form.
4. **No unlockables:** all 9 games, 7 characters and 3 difficulties are present
   on a cold boot with a zero-byte save; a completed match wrote nothing.
5. **Hidden space enumerated:** the only hidden trigger is `Select` at the
   title, and it opens credits, not a cheat/debug menu.
6. **Published codes tested:** the only in-scope published code is the fake
   health sequence; the other published strings are absent from this ROM or
   belong to the Secret Agent half of the 2-in-1.

Within these measured spaces, no developer cheat exists to mint. There is no
"unpublished code" deliverable because there is no code system; the unpublished
input that *does* exist (Select → credits) is documented above.

---

## 7. Validation evidence

### Observed (emulator, screenshots, memory)

* Cold boot reaches the title through the four-logo reel; Start reaches player
  select; the full menu path in §3.2 was walked.
* 9 games in the wheel, 7 characters with wrap, 3 difficulties, scrolling help,
  3-entry pause, `play again? yes/no` result.
* `Select` at the title opens the credits; `B` exits; auto-return in ~56 s.
* `Select` elsewhere does nothing (except resume from pause).
* The published `UDLRBA` sequence at the title ends with B returning to attract;
  at pause it acts as ordinary input.
* `.sav` remains 0 bytes after a completed Bubble Machine match and after the
  emulator was stopped.
* mGBA debugger at boot: `0x03000000=0xFC00`, `0x03000004=0xFC00`,
  `0x03000008=0x0000`; `0x03000010`–`0x030003FF` all zero;
  `0x02000000`–`0x020000FF` all zero.

### Derived (code / data)

* Keypad poll at `0x08024BCC` reads `0x04000130` once per frame and writes only
  `0x03000000/04/08`; accessors at `0x08024AF4/B3C/B84` are `arg & word`.
* Header scan finds exactly one GBA header; last non-`0xFF` at `0x3D248B`.
* Text bank `0x3C0CA0`–`0x3D19F5`; credits at `0x083D11BF`; word-list pointer
  tables at `0x082887C`/`0x0829FF4`.
* Mask-run scan: 69 active-high runs, all data; 1 active-low run, graphics.
* Literal searches: `GROOVY100`, `FREEDRESS`, all 13 Superpack codes and the
  `UDLRBA` mask encodings have 0 hits.

### Inferred

* The zero header checksum is a dump/header-tool artifact (the complement is
  valid, the entry and logos are retail, and other ROMs in the collection show
  the same zero field).
* The credits screen is a developer easter egg (observed behaviour; intent
  inferred from its placement on Select at the title and its staff-roll content).
* The absence of unlockables is inferred from a complete cold-boot inventory
  plus zero save writes; a hidden event that never writes state could in
  principle exist, but no screen or flag for one was found.
* The asset-name/profanity block at `0x0829E68` is internal/unused data; its
  consumer was not identified (§8).

---

## 8. Unknowns

* The exact code address of the title's `Select` → credits branch was not
  isolated; the behaviour is observed and reproducible, and the credits text
  address is known.
* Whether the credits can also be reached by a completion condition: no such
  trigger was observed; the Select route is the documented and reproducible one.
* The header checksum zeroing cause (dump tool vs. patch) is not proven.
* The purpose of the 8-character asset-name/profanity block at `0x0829E68`
  (names such as `BUBBLES_`, `BALLOON_`, `SNOWMAN_`, followed by a profanity
  list) is unresolved. It has no direct pointer and no reachable screen uses it;
  it may be a development-time asset/name filter.
* Per-game end states: the `play again? yes/no` box is shared engine UI and was
  reached and screenshotted in Bubble Machine. All nine games were entered; the
  shared pause box was observed in D.J. Booth, Bubble Machine, Checkers and
  Conga Line, and the help template was walked for D.J. Booth (nine per-game
  help blocks exist in the text bank). No game-specific end menu or code prompt
  was observed.
* No save-based unlock was observed; a save routine exists (`0x0E000000`/SRAM
  accesses), but no tested action wrote data. A specific in-game event that
  writes SRAM cannot be ruled out beyond the tested path.

---

## 9. Tooling

* **Emulator:** mGBA 0.10.5+dfsg-1, SDL frontend at `/usr/games/mgba`, 3× scale
  under `Xvfb :167` (1024×768×24) with `openbox`; `SDL_AUDIODRIVER=dummy`.
* **Input/screenshots:** `xdotool` (keydown/keyup with 150–300 ms holds),
  ImageMagick `import`/`convert`/`montage`/`compare`.
* **Static:** `arm-none-eabi-objdump` (`-M force-arm` and `-M force-thumb`),
  Python 3 + Capstone 5.0.7 for literal/PC-relative scans.
* **Dynamic memory:** mGBA's command-line debugger (`mgba -d`), scripted with
  `b 0x08024bcc` + repeated `c` to advance one frame per continue, then
  `x/4 0x030000xx` and `x/4 0x020000xx` dumps. This is also how the "only three
  input words" result was measured.
* **Scripts (this run, `/tmp/opencode/barbie`):** `scan_codes.py` (identity,
  keyword, mask-table and input-reference scans), `ui.py` (focus/key/screenshot
  helper), `test2.py`/`titlecodes.py` (button-code tests), `tour.py`/`tour2.py`
  (game-screen walk). Screenshots: `/tmp/opencode/barbie/shots/`.
* **Savestates:** title slot 3, game-select slot 4; `F1`–`F10` load,
  `Shift+F1`–`F10` save.

No ROM, extracted graphics, music or game text is redistributed with this
report; only hashes, addresses, algorithms and behavioural observations are
published.
