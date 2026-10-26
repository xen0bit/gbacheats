# Board Game Classics (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Board Game Classics/Board Game Classics.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `BOARDGAMES` (NUL-padded) |
| Game code | `B6EE` |
| Maker code | `20` |
| Software version | 0x00 |
| Main unit / device | 0x00 / 0x00 |
| Complement check | 0x18 (valid: `-(0x19 + sum(0xA0..0xBC)) & 0xFF = 0x18`) |
| Entry | `0xEA00002E` at 0x08000000 → 0x080000C0 → 0x080000E0 |
| MD5 | `871133b4e4e8b172f7538b0250c9bb45` |
| SHA-1 | `83ba1075b9170598fea26d0f1f9f1ecd3cf0d6d2` |
| SHA-256 | `3bef2ab6a83086c6cd52fc9f53e626ddbc5bb2fbd21b695532f34d622ddd2331` |

**Embedded-header scan (Phase 0).** The 156-byte Nintendo logo
(`24 ff ae 51 … 8a c0`) occurs exactly once in the 4 MiB image, at file
offset 0x04, i.e. one header at 0x08000000. There is no second image and no
“2 Games in 1”/shell header. The entry branch, crt0 chain and header
complement check are all consistent with an unmodified retail image; there is
no trainer, intro patch, or extra code between the header and crt0. The empty
`Board Game Classics.sav` (0 bytes) produced by mGBA confirms the cartridge
does not use battery save; progress is password-based.

## 2. Executive summary

This is the US release of *Board Game Classics* (DSI Games / Black Lantern
Studios, 2005): Chess, Checkers and Backgammon, each with the same
Game Select Options screen (Gameplay / Opponent / Difficulty / Timed or Scored
Game / Music), a Character & Board Select screen (10 characters, 5 board
themes × light/dark), Variant Rules, and a pause menu.

The only developer-intended cheat surface is the **numeric password screen**
on the main menu (10-key keypad, exactly six digits) plus the password that
the pause menu displays back. It is **not a checksum or generator**: the
validator at `0x08008D70` compares the six entered bytes against exactly
**three** NUL-terminated strings in ROM and nothing else. The whole
representable space is **10^6 = 1,000,000** strings; exactly **three** are
accepted.

The three accepted passwords are:

| Level | Password | Unlocks |
|---:|---|---|
| 1 | `000413` | Fantasy set (Glorp, Telem, Fantasy boards) |
| 2 | `192845` | Fantasy + Atlantis sets (Bubble, Chomp, Atlantis boards) † |
| 3 | `446218` | Fantasy + Atlantis + Genius difficulty |

† Level-2 acceptance and pause password were observed directly; the exact
level-2 Character Select state is derived from the monotonic grant table and
from the observed level-1/level-3 lock counts (§7).

`192845` and `446218` are published on GameFAQs. `000413` appears in **no
published list** found (GameFAQs, archived GameFAQs, VGChartz, TCRF, fan
wikis); it is the ROM's level-1 entry and was confirmed in mGBA. Because the
system is a three-entry literal table rather than an algorithm, `000413` is
the only unpublished member the space contains — there is no generator from
which a fourth code could be minted. Rejection was confirmed in-game for
`999999`, `000000` and a one-digit code; a seventh digit is silently dropped.

No debug menu, button-code sequence, secret menu, or unlockable gallery
exists. All extracted strings (`strings -n 3`: 82,789 lines) were classified;
`cheat`, `debug`, `secret`, `passcode`, `hidden`, `bonus` and `extra` occur
zero times.

## 3. How to reproduce

**Emulator.** mGBA 0.10.5 SDL (`/usr/games/mgba`, package `mgba-sdl`) at 3×
scale, under `Xvfb :189 -screen 0 1024x768x24` with `openbox` and
`SDL_AUDIODRIVER=dummy`. GBA viewport crop: `720x480+152+144`.

**Default SDL keymap used here:**

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| Start | `Return` |
| Select | `BackSpace` |
| L / R | `a` / `s` |
| D-pad | arrow keys |

Hold every key 150 ms; the game polls input per frame. `xdotool
windowfocus <id>` first; a 10 ms tap is often lost.

**Exact menu paths.**

*Password entry:* title screen → `Return` → main menu → `Down` to
**Password** → `A` → keypad. The keypad is two rows (`0 1 2 3 4` /
`5 6 7 8 9`) with **Confirm** and **Cancel** below. The D-pad wraps at the
row edges; `A` enters the highlighted digit; at most six digits are retained.
A six-digit buffer is shown in the box under the keypad. Choose **Confirm**
and press `A`; the result box reads `Password Accepted` or
`Invalid Password`. `A` returns to the main menu.

*Progress check:* start any game (Select Game → icon → `A`; on the options
screen press `A` through the focus groups to the bottom-right arrow, then `A`
again), then `Start` → **Pause Menu**. The bottom line displays
`Password: <current level string>`.

*Character & Board Select:* Select Game → icon → set **Gameplay** to
**Custom** → advance focus to the arrow → Character Select. Locked characters
and boards are drawn as `?`.

**Codes entered in mGBA (all six digits):**

| Code | Result |
|---|---|
| `000413` | Accepted; level 1 |
| `192845` | Accepted; level 2 |
| `446218` | Accepted; level 3 |
| `999999` | Invalid Password |
| `000000` | Invalid Password |
| `4` (Confirm) | Invalid Password |
| `1234567` | 7th digit ignored, buffer stays `123456` |

Screenshots (kept as working artifacts in `/tmp/opencode/boardclassics/`):

* `q6_c.png` / `fa0_c.png` — password keypad, empty
* `fa2_c.png` — `Password Accepted` after `000413`
* `ha1_c.png` — `Password Accepted` after `192845`
* `a1_c.png` — `Password Accepted` after `446218`
* `w1_c.png` — `Invalid Password` after `999999`
* `x3_c.png` — `Invalid Password` after `000000`
* `y0_c.png` — `Invalid Password` after one digit
* `z0_c.png` — buffer `123456` after a seventh keypress
* `fd1_c.png` — pause menu, `Password: 000413`
* `hd1_c.png` — pause menu, `Password: 192845`
* `ai1_c.png` — pause menu, `Password: 446218`
* `gg1_c.png` / `lc1_c.png` — pause menu at level 0, `Password: ------`
* `fb1_c.png` — options at level 1: **Genius greyed out**
* `fi2_c.png` — character/board select at level 1: two `?` characters, two `?` boards
* `ac1_c.png` / `n1_c.png` — character/board select at level 3: no `?`
* `gd1_c.png` — character/board select at level 0: four `?` characters, four `?` boards
* `aa1_c.png`, `ab4_c.png` — Chess Variant Rules
* `fn1_c.png` — Checkers Variant Rules (Forced Jumps)
* `ga2_c.png` — Backgammon options (Scored Game)
* `lb1_c.png` — Checkers board; `fc1_c.png` — Chess board; `gf1_c.png` — Backgammon board
* `ae1_c.png` — Credits

## 4. Address map

All addresses are ROM addresses (`file offset + 0x08000000`).

| Address | What |
|---:|---|
| `0x08008D70` | Password validator (Thumb). Called once from `0x08008B74`. |
| `0x08008AF0` | Password-screen state machine (draw/input/confirm). |
| `0x08008B74` | Confirm branch: calls validator, maps result to accept/reject. |
| `0x08008600` | Password-screen init/draw; clears the input buffer. |
| `0x08008C14` | Clears seven bytes at `0x03003E18` and resets the screen state. |
| `0x0800A0EC` | Unlock-grant / “next password” routine: increments level, writes string pointer, plays sound. |
| `0x0804C7C8` | String `------` (level-0 display value; not an accepted input). |
| `0x0804C7D0` | String `000413` (level 1). |
| `0x0804C7D8` | String `192845` (level 2). |
| `0x0804C7E0` | String `446218` (level 3). |
| `0x0805024C` | UI text-pointer table base (all UI strings). |
| `0x08050288` | Password-block entry 0 (text table entry 15) → `0x0804C7C8` (`------`). |
| `0x0805028C` | Password-block entry 1 → `0x0804C7D0` (`000413`). |
| `0x08050290` | Password-block entry 2 → `0x0804C7D8` (`192845`). |
| `0x08050294` | Password-block entry 3 → `0x0804C7E0` (`446218`). |
| `0x0804CE5C` | UI string `Password Entry`. |
| `0x0804CE80` | UI string `Password Accepted`. |
| `0x0804CE94` | UI string `Invalid Password`. |
| `0x03003E04` | Password-screen state (0..4; 3 = confirm/accepted). |
| `0x03003E10` | Digit count / write index for the keypad. |
| `0x03003E18` | Six-digit input buffer, 7 bytes (six digits + NUL). |
| `0x030047FC` | Progress structure base. |
| `0x03004820` | `progress[0x24]`: current unlock level 0..3. Stored as `u32`. |
| `0x03004824` | `progress[0x28]`: maximum level / message guard. |
| `0x0300489C` | `progress[0xA0]`: pointer to the current password string (displayed in the pause menu). |
| `0x03003130` | Input/accept flag used while the message box is up. |

For savestate work: mGBA's `.ssN` PNG contains a zlib-compressed `gbAs`
chunk; after decompression the layout used here is
`IWRAM = 0x19000`, `EWRAM = 0x21000`, so IWRAM address `0x0300xxxx` maps to
state offset `0x19000 + (addr - 0x03000000)`.

## 5. Algorithm

The validator is a literal comparison, not a checksum. Reconstructed from the
Thumb code at `0x08008D70`:

```
validate(input[6]):
    base   = 0x08050288            # password-block entry 0 ("------")
    level  = 1
    entry  = base + 4              # entry 1 = "000413"
    while level <= 3:
        s = *(u32*)entry           # pointer to 6-char string
        ok = true
        for i in 0..5:             # exactly six bytes
            if input[i] != s[i]: ok = false
        if ok:
            progress[0x24] = level       # 0x03004820
            progress[0xA0] = s           # 0x0300489C (pause-menu string)
            return 1
        level++
        entry += 4
    return 0
```

Caller (`0x08008B74`): `if (validate()==1) { accept: state=3, sound, message
"Password Accepted" } else { reject: state=4, sound, message "Invalid
Password" }`.

Notes:

* The comparison is over **six bytes only**; there is no length call, no
  `atoi`, no multiplication, no XOR key, no checksum and no per-character
  alphabet table for the validator. The keypad itself only provides `0`-`9`.
* The buffer is seven bytes, zeroed at screen entry; six keypresses fill it.
  A seventh press is refused at count 0 and never stored (observed).
* Because every table string is exactly six digits, any shorter input is
  rejected by the zero-padded comparison.
* `progress[0xA0]` is what the pause menu prints after `Password:`. At level 0
  it points to `------`; after accepting `000413` it points to `000413`, etc.
  The level-0 string is display-only — the validator starts at entry 1, and
  `-` is not on the keypad.
* The grant routine at `0x0800A0EC` (inferred: called by the tournament
  unlock-message screen) increments
  `progress[0x24]`, writes `table[level]` into `progress[0xA0]`, and shows the
  next unlock message; it is not part of password entry.

Only four code references to the input buffer `0x03003E18` exist in the whole
ROM — init, digit store, clear, compare — which bounds the search: there is no
second validator or alternate entry path.

## 6. Tables

### 6.1 Passwords and levels

| Level | String | File offset | Text-table entry | Effect |
|---:|---|---:|---:|---|
| 0 | `------` | 0x4C7C8 | 0x08050288 | default; displayed only, never accepted |
| 1 | `000413` | 0x4C7D0 | 0x0805028C | Fantasy theme + Glorp/Telem + Fantasy boards |
| 2 | `192845` | 0x4C7D8 | 0x08050290 | level 1 + Atlantis theme + Bubble/Chomp + Atlantis boards |
| 3 | `446218` | 0x4C7E0 | 0x08050294 | level 2 + Genius difficulty |

Published status: GameFAQs (archived capture 2025-11-13) lists only `192845`
and `446218`. No page, archive or wiki found lists `000413`.

### 6.2 Unlock surface

Characters (10): Robbie, Earl (Traditional), Sam, Razor (Toys), Zeep, Klutch
(Science Fiction), Glorp, Telem (Fantasy), Bubble, Chomp (Atlantis).
Boards: Traditional, Toys, Science Fiction, Fantasy, Atlantis, each light and
dark (10 board tiles).

At level 0 the Character & Board Select shows four `?` characters and four `?`
boards. At level 1 it shows two `?` characters and two `?` boards (Fantasy
available). At level 3 no `?` remains.

### 6.3 Gameplay-option surface (developer toggles)

| Screen | Options |
|---|---|
| Game Select Options (all games) | Gameplay: Quick Play / Tournament / Custom / Watch; Opponent: Computer / Human; Difficulty: Easy / Normal / Hard / Genius; Music: 1 / 2 / 3 / 4 / Off |
| Chess / Checkers | Timed Game: Off / 5 / 10 / 15 / 20 / 30 minutes |
| Backgammon | Scored Game: Off / 3 / 5 / 10 / 25 / 50 |
| Watch mode | two independent difficulties (Difficulty 1, Difficulty 2) |
| Chess Variant Rules | Castling On/Off; En Passant On/Off; Battle Animations On/Off |
| Checkers Variant Rules | Forced Jumps On/Off |
| Backgammon Variant Rules | Backgammon Value (Double/Triple = European/North American); Automatic Doubles On/Off (strings at 0x4DA50/0x4DA64; manual p.8/10) |
| Pause menu | Player 1 Computer/Human; Player 2 Computer/Human; Music 1-4/Off; Battle Animations On/Off (Chess only); Resume Game; Quit Game; `Password:` line |

`Genius` is greyed out until level 3; it is not selectable at levels 0–2.

## 6b. Enumeration

**Space.** Six positions, alphabet `0`–`9` only (the keypad has ten cells).
Full-length inputs: `10^6 = 1,000,000`; counting every shorter keypad string
as well gives `10^0+…+10^6 = 1,111,111`. The validator only matches six-byte
strings, and the buffer is zero-padded, so all 111,111 shorter prefixes are
rejected (one such case, `4`, was confirmed in-game). Longer strings are
truncated at six by the keypad handler.

**Validator model.** `password_model.py` (reproduced in §9) implements the
three-entry compare, reads the actual strings from the ROM at 0x4C7D0/D8/E0
and was run against all 1,000,000 six-digit strings:

```
level-0 display value: ------
accepted strings: ['000413', '192845', '446218']
space size: 10^6 = 1000000
accepted count: 3
accepted: [('000413', 1), ('192845', 2), ('446218', 3)]
```

**Novel (unpublished) code: `000413`.** It is in the ROM's level-1 slot and
was entered on a clean boot in mGBA:

* `fa2_c.png` — `Password Accepted`.
* `fd1_c.png` — pause menu reads `Password: 000413`.
* `fb1_c.png` — options screen with **Genius still greyed out**.
* `fi2_c.png` — Character & Board Select with only two `?` characters and
  two `?` boards: the Fantasy set (Glorp/Telem/Fantasy boards) is unlocked,
  Atlantis and Genius are not.

This code is absent from the GameFAQs password table (which lists only
`192845` and `446218`), from the archived GameFAQs capture, and from the
TCRF/VGChartz/fan-wiki searches performed. It is a literal, not a generated
value: the table has exactly three accepted members and no encoder exists, so
`000413` is the only unpublished code the space contains. That is stated as a
property of the system, not as a minting success.

**Published codes verified.** `192845` → `Password Accepted`
(`ha1_c.png`), pause `Password: 192845` (`hd1_c.png`), Genius greyed
(`hb1_c.png`). `446218` → `Password Accepted` (`a1_c.png`), pause
`Password: 446218` (`ai1_c.png`), all characters/boards available and Genius
selectable (`ac1_c.png`).

**Bounds proven by rejection.**

| Input | In-game result | Evidence |
|---|---|---|
| `999999` | `Invalid Password` | `w1_c.png` |
| `000000` | `Invalid Password` | `x3_c.png` |
| `4` (one digit) | `Invalid Password` | `y0_c.png` |
| `1234567` | 7th press discarded; buffer `123456` | `z0_c.png` |
| `------` | not enterable (`-` absent); validator ignores table[0] | keypad screenshot + disassembly |
| `0004130` | cannot be submitted; capped at six | `z0_c.png` |

No out-of-range numeric field exists to reject, because there is no numeric
field: the comparison is textual over the ten-symbol keypad. The three
non-table values above are the strongest available bound tests, and all were
rejected in-game.

## 7. Validation evidence

**Observed (emulator, screenshots listed in §3).**
* Keypad is digits only; six-digit display; `Confirm` / `Cancel`.
* `000413`, `192845`, `446218` each produce `Password Accepted`.
* `999999`, `000000`, one-digit `4` produce `Invalid Password`.
* Six-digit cap; seventh keypress ignored.
* Pause menu prints the current level string: `------`, `000413`, `192845`,
  `446218`.
* Level 1: Genius greyed, two `?` characters, two `?` boards.
* Level 3: no `?`, Genius selectable.
* Level 0: four `?` characters, four `?` boards, `Password: ------`.
* Chess and Checkers variant pages; Backgammon options page; pause menus for
  Chess, Checkers and Backgammon; Credits.

**Derived (disassembly).**
* Validator at 0x08008D70 compares six bytes against table entries 1..3 only.
* Table strings and text-table pointers at 0x0805028C..0x08050294.
* Input buffer 0x03003E18 has exactly four readers; no second validator.
* No checksum/key/generator; no `atoi`; no length-dependent branch beyond the
  six-byte compare.
* Unlock level written to 0x03004820; string pointer to 0x0300489C.

**Inferred.**
* Level 2 unlocks Fantasy + Atlantis but not Genius: derived from the
  monotonic level table plus the observed level-1 (Atlantis locked) and
  level-3 (all unlocked) states, and matching the published GameFAQs entry.
  The level-2 Character Select screen itself was not captured.
* `progress[0x28]` is the maximum level / message guard; both 0x24 and 0x28
  read 3 in the level-3 savestate.
* The Backgammon Variant Rules page was not reached through the UI in this
  session; its two options are present in the text table (0x4DA50, 0x4DA64)
  and in the manual, so the screen exists, but the on-screen layout is
  inferred.

## 8. Unknowns

* Whether entering a lower password after a higher one downgrades the level.
  The validator writes the matched level unconditionally; this was not tested
  in-game.
* Exact semantic of `progress[0x28]` (maximum vs. last-granted level).
* The Backgammon Variant Rules page layout/values were not captured on screen.
* No debug menu or button-code system was found; the negative is bounded by
  the full string scan (cheat/debug/secret/passcode = 0 hits), the four
  buffer xrefs, and the exhaustive 10^6 enumeration. Buttons were exercised
  across the title, main menu, options, Character & Board Select, in-game and
  pause screens (`A`, `B`, `Start`, `Select`, `L`, `R`, four D-pad
  directions), with no hidden screen or counter. A multi-button sequence that
  has no text, no ASCII table and no reuse of the password buffer cannot be
  excluded by static analysis alone; the observed input surface is the
  documented menus only.
* Regional/PAL revisions (e.g. the EU “Chess & Draughts & Backgammon” title)
  may differ; this report is for SHA-256
  `3bef2ab6a83086c6cd52fc9f53e626ddbc5bb2fbd21b695532f34d622ddd2331`.

## 9. Tooling

* mGBA 0.10.5 SDL, Xvfb :189, openbox, `SDL_AUDIODRIVER=dummy`.
* `xdotool` (input), `scrot` + ImageMagick `convert` (240×160 viewport crop).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000
  -M force-thumb`.
* Python 3 + Capstone 5.0.7 for pointer/BL scans; mGBA `.ssN` savestates were
  decompressed (zlib `gbAs` chunk) to read IWRAM and confirm
  `0x03003E18 = "446218"`, `0x03004820 = 3`, `0x0300489C = 0x0804C7E0`.
* WEB: GameFAQs cheats page via `web.archive.org` (direct fetch is 403);
  searches for TCRF/VGChartz/fan-wiki pages and for the literal `000413`.

Enumeration model used (also at `/tmp/opencode/boardclassics/password_model.py`):

```python
import itertools, struct
rom  = open("Board Game Classics.gba","rb").read()
BASE = 0x08000000
def cstr(a):
    o = a - BASE
    return rom[o:rom.index(b"\0", o)].decode()
entries = [0x0805028C, 0x08050290, 0x08050294]
pw = [cstr(struct.unpack_from("<I", rom, e-BASE)[0]) for e in entries]
assert pw == ["000413","192845","446218"]
def validate(s):
    if len(s) != 6: return 0
    for i, p in enumerate(pw, 1):
        if s == p.encode(): return i
    return 0
acc = [(bytes(t).decode(), validate(bytes(t)))
       for t in itertools.product(b"0123456789", repeat=6)
       if validate(bytes(t))]
print(len(acc), acc)   # 3 [('000413',1),('192845',2),('446218',3)]
```

**Legal note.** No ROM, extracted graphics, audio or game text is
redistributed here; only hashes, addresses, the three short password literals,
and the analyst's own model/screenshots are recorded.
