# Animal Snap: Rescue Them 2 by 2 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Animal Snap: Rescue Them 2 by 2.gba` |
| Size | 4,194,304 bytes (`0x400000`, 4 MiB) |
| Header title | `ANIMAL SNAP ` (12 bytes, space-padded) |
| Game code | `AAQE` |
| Maker code | `7M` |
| Software version | `0x00` |
| Fixed byte `0xB2` | `0x96` |
| Complement check `0xBD` | `0x91` (valid) |
| Header checksum `0xBE` | `0x0000` (computed value would be `0x00C3`; see Unknowns) |
| Entry word | `0xEA00002E` → branch to `0x080000C0` |
| MD5 | `8a65cc927274981d1b431bc005fe185d` |
| SHA-1 | `899b9158f622ab145c6787b2af65abda902e6a95` |
| SHA-256 | `34f3fe260a7b33febbcf0b6b9fc15af1421477cddf9b909f30c57f85da2ae567` |

Embedded GBA-header scan: the 156-byte Nintendo logo occurs **once**, at file
offset `0x4` (header base `0x0`). This is a single 4 MiB image, not a
multi-game pack; there is no second title/game-code header.

Credits and the archived publisher page identify the game as developed by
Awesome Developments and published by Ignition Entertainment (GBA, November
2002). The credits screen in the ROM also names Ignition Entertainment.

## 2. Executive summary

The ROM contains exactly **one developer-intended button code**, entered on the
title screen:

> **Hold L and press Up, Down, Left, Right, Right, Left, Down, Up.**

It adds a fourth title-menu entry, **BLOCK BLASTER**, which starts the
Breakout-style bonus game immediately. The same code is printed verbatim in the
ROM's own text bank (`0x68DC`–`0x6960`) and is the only code on the archived
GameFAQs cheat page; the in-emulator test of that published code passed.

The validator is small and fully recovered. It is a *subsequence* matcher over
newly-pressed D-pad edges, gated on the L shoulder button being **held**:

* expected table: `0x0800A2FC` = `40 80 20 10 10 20 80 40`;
* progress index: byte `0x0300261C`;
* unlock flag: byte `0x03001320` (only store found: `1` at `0x08002130`);
* held-key mirror: halfword `0x03001040`;
* new-press edge word: halfword `0x03001324`.

There is no password system, no ASCII code alphabet, no table of password
strings, no debug menu and no gallery. Keyword searches for `password`,
`passcode`, `cheat`, `code`, `secret`, `unlock`, `gallery`, `debug` and `menu`
return zero hits in 28,411 printable ASCII runs.

The complete minimal input space is `4^8 = 65,536` sequences; exactly one is
accepted. Because the index is **not reset by a wrong press**, the accepted
input language is much larger than the published sequence: any stream that
contains the eight correct D-pad edges in order, with L held at each match, is
accepted. Two inputs that appear on no published list were minted and confirmed
in mGBA (a 15-press superset with decoy presses, and the minimal sequence with
**both** L and R held). Four rejection experiments bound the validator.

The unlock flag is session-only: resetting the game clears it, and the game
writes no save data (a 0-byte `.sav` is all mGBA creates).

## 3. How to reproduce

Emulator and display used:

```bash
export PATH=$PATH:/usr/games
Xvfb :138 -screen 0 1024x768x24 &
DISPLAY=:138 openbox &
DISPLAY=:138 SDL_AUDIODRIVER=dummy mgba -3 "Animal Snap: Rescue Them 2 by 2.gba" &
```

mGBA 0.10.5 (SDL frontend). Default mGBA SDL keymap:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Key presses were held 120–200 ms with 200–300 ms gaps. Window is 720×480
(`import -window <id>` gives the exact viewport). Reset is mGBA's `Ctrl+R`.

Exact menu path:

1. Boot and wait for the title menu (`TIME CHALLENGE`, `ARCADE MODE`, `OPTIONS`).
2. Hold `a` (L), then press `Up Down Left Right Right Left Down Up`.
3. `BLOCK BLASTER` appears as a fourth item. Move the cursor to it with the
   D-pad (it is the last entry) and press `x` (A). It starts immediately.
4. Start (`Return`) pauses the bonus game (`PAUSED`); `Return` resumes.
   Losing all balls gives `GAME OVER!` and returns to the title.

Codes tested (all in mGBA, screenshots in this folder):

| Input | Result |
|---|---|
| L + `U D L R R L D U` (published) | accepted, 4th menu entry |
| L+R held + `U D L R R L D U` (novel) | accepted, 4th menu entry |
| L + 15-press decoy superset (novel) | accepted, 4th menu entry |
| `U D L R R L D U` with no shoulder held | rejected, 3 items |
| R only + `U D L R R L D U` | rejected, 3 items |
| L + `U U U U U U U U` | rejected, 3 items |
| L + `U D L R R L D` (7 of 8) + wrong 8th | rejected; adding the correct 8th later accepts |

The last test also proves the progress index persists across a wrong press and
across releasing/re-holding L.

Other screens walked for the negative/enumeration result: Time Challenge story
cutscene and gameplay; pause menu (`CONTINUE GAME`, `FIND MOVE`, `START NEW
GAME`, `QUIT GAME`); arcade `TABLE 1`–`TABLE 4` select; Arcade gameplay and
pause; Options (`DIFFICULTY EASY`, `MUSIC ON`, `SOUNDFX ON`, `CREDITS`);
Credits; `BAD LUCK`; the Time Challenge timeout/continue dialog (`SORRY!`,
`TIME OUT.`, `5 CONTINUES`, `RESTART`, `QUIT`); Block Blaster gameplay,
`PAUSED`, `GAME OVER!`.

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`; all RAM addresses are
absolute GBA addresses.

| File offset | ROM address | Size | Meaning |
|---:|---:|---:|---|
| `0x000000` | `0x08000000` | `0xC0` | GBA header (entry, logo, title `ANIMAL SNAP `, code `AAQE`, maker `7M`) |
| `0x0020A8` | `0x080020A8` | ~`0x380` | Title/menu frame handler (title, Arcade table select, Options dispatch at `0x080022C0`) |
| `0x00210A` | `0x0800210A` | `0x2E` | Button-code validator: L gate, table load, edge compare, index, unlock |
| `0x002128` | `0x08002128` | `0x0A` | On 8th match: index := 0; `0x03001320` := 1; `bl 0x080007CC` (SFX with `r0=0x08008A70`) |
| `0x002138` | `0x08002138` | `0x5E` | Title menu down/up/A/B handling |
| `0x002152` | `0x08002152` | `0x0A` | item count = `3 + unlock_flag` |
| `0x00227C` | `0x0800227C` | `0x44` | literal pool used by title handler |
| `0x002288` | `0x08002288` | 4 | literal `0x0800A2FC` (sequence table) |
| `0x002290` | `0x08002290` | 4 | literal `0x03001320` (unlock flag) |
| `0x0022C0` | `0x080022C0` | — | submenu dispatch: `1` = Arcade table select, `2` = Options |
| `0x006374` | `0x08006374` | — | `main` (crt0 loads Thumb pointer `0x08006375` from literal `0x08000420`) |
| `0x005C30` | `0x08005C30` | ~`0x600` | story/hint state routine; hint branch at `0x080060FA`, selected by byte `0x0300205C` |
| `0x0061D4` | `0x080061D4` | `0x1C` | literal pool: seven pointers to the hint-text lines |
| `0x0060FA` | `0x080060FA` | `0x54` | draws the seven hint lines (the ROM's own code hint) |
| `0x006724` | `0x08006724` | — | Options/pause/status text bank |
| `0x0068DC` | `0x080068DC` | `0x84` | `On Title Screen` … `Block Blaster Game.` hint text |
| `0x006798` | `0x08006798` | 22 | `BONUS GAME COMPLETED!` |
| `0x0067C4` | `0x080067C4` | 10 | `GAME OVER!` |
| `0x00A268` | `0x0800A268` | `0x23` | locked title menu: `Time Challenge\rArcade Mode\rOptions` |
| `0x00A28B` | `0x0800A28B` | `0x31` | unlocked title menu: `…\rOptions\rBlock Blaster` |
| `0x00A2BC` | `0x0800A2BC` | `0x1C` | `Table 1\rTable 2\rTable 3\rTable 4` |
| `0x00A2FC` | `0x0800A2FC` | 8 | **sequence table**: `40 80 20 10 10 20 80 40` |
| `0x0039D4` | `0x080039D4` | ~`0x450` | Block Blaster bonus-game loop |
| `0x003CC2` | `0x08003CC2` | `0x1A` | completion counter; draws `BONUS GAME COMPLETED!` when counter == 10, else `LEVEL COMPLETED!` |
| `0x001984` | `0x08001984` | `0x1E` | input update: held = `~REG_KEYINPUT`; pressed = held & ~previous_held |
| `0x001A74` | `0x08001A74` | — | text draw helper used by the hint screen |

RAM (derived from the code and confirmed by behaviour):

| Address | Type | Meaning |
|---|---|---|
| `0x03001040` | `u16` | held keys, active-high (`~0x04000130 & 0x3FF`) |
| `0x03001324` | `u16` | newly pressed keys this frame (edge) |
| `0x03001320` | `u8` | **Block Blaster unlock flag** (0/1) |
| `0x0300261C` | `u8` | sequence progress index (0–7) |
| `0x0300000C` | `u8` | title menu selection index |
| `0x03000010` | `u8` | submenu selector: 1 = Arcade tables, 2 = Options |
| `0x030017E0` … `0x0300263C` | — | Block Blaster state (lives, paddle, ball, level); not fully mapped, not needed for the cheat |

Input model (derived at `0x08001984`):

```
held    = (~*(u16*)0x04000130) & 0x3FF
pressed = held & ~previous_held
previous_held = held
```

so `0x03001040` is "held" and `0x03001324` is "newly pressed".

## 5. Algorithm

Title-screen frame handler (`0x080020A8`), title branch:

```c
u16 held    = *(u16*)0x03001040;   // L=0x200, R=0x100, Down=0x80, Up=0x40,
u16 pressed = *(u16*)0x03001324;   // Left=0x20, Right=0x10, Start=0x08,
u8  flag    = *(u8*)0x03001320;    // Select=0x04, B=0x02, A=0x01
u8  idx     = *(u8*)0x0300261C;
static const u8 seq[8] = {0x40,0x80,0x20,0x10,0x10,0x20,0x80,0x40};

if (held & 0x200) {                       // L must be held
    if (pressed == seq[idx]) {            // exact 16-bit edge equality
        idx++;
        *(u8*)0x0300261C = idx;
        if (idx == 8) {
            *(u8*)0x0300261C = 0;
            *(u8*)0x03001320 = 1;         // unlock
            play_sfx(0x08008A70);
        }
    }
}

if (pressed & 0x0080) menu = (menu + 1) % (3 + flag);   // Down
if (pressed & 0x0040) menu = (menu + 2 + flag) % (3 + flag); // Up
if (pressed & 0x0001) { /* A: launch selected item */ }
if (pressed & 0x0002) { /* B: cancel/reset transition */ }
```

Menu rendering:

```c
const char *menu = (*(u8*)0x03001320)
                 ? (const char*)0x0800A28B   // 4 items incl. Block Blaster
                 : (const char*)0x0800A268;  // 3 items
draw_multiline(menu, 0x3C, 0x56, 0);
```

Important properties, all derived from the assembly:

1. **L is a held-gate, not a sequence symbol.** If L were pressed in the same
   frame as the first Up, the edge word would be `0x240`, not `0x040`, and the
   first step would fail. The published instruction "hold L" is therefore
   mandatory.
2. **The full 16-bit edge word is compared with a byte constant** (`ldrh` then
   `ldrb` then `cmp`). A same-frame extra button on any step makes `pressed`
   differ, so that step is ignored.
3. **A mismatch does not reset progress.** The index is only incremented on a
   match; wrong presses leave it unchanged. This creates the superset language
   described in §6b.
4. **One writer found.** `0x03001320` is referenced by exactly two literals in
   the whole ROM (`0x080020E4`, `0x08002290`), both in this handler; the only
   store found is `strb r0,[r1]` at `0x08002130` with `r0=1`.
5. **The flag is not saved.** It lives in IWRAM and is cleared by reset; no save
   data was written in this session (mGBA left a 0-byte `.sav`).

Menu selection when index 3 (Block Blaster) is chosen at `0x080021E0`:
it clears graphics, sets `0x03001318 = 0`, loads the bonus-game tiles/background
and calls `0x080039D4`. The bonus game starts directly; there is no second
table-select screen for it.

## 6. Tables

### 6.1 Key masks (active-high, after `~REG_KEYINPUT`)

| Button | Mask |
|---|---:|
| A | `0x001` |
| B | `0x002` |
| Select | `0x004` |
| Start | `0x008` |
| Right | `0x010` |
| Left | `0x020` |
| Up | `0x040` |
| Down | `0x080` |
| R | `0x100` |
| L | `0x200` |

### 6.2 Sequence table `0x0800A2FC`

```
40 80 20 10 10 20 80 40
 U  D  L  R  R  L  D  U
```

### 6.3 Titles and strings

| Address | String |
|---|---|
| `0x0800A268` | `Time Challenge\rArcade Mode\rOptions` |
| `0x0800A28B` | `Time Challenge\rArcade Mode\rOptions\rBlock Blaster` |
| `0x0800A2BC` | `Table 1\rTable 2\rTable 3\rTable 4` |
| `0x080068DC` | `On Title Screen` |
| `0x080068EC` | `Hold Left Shoulder` |
| `0x08006900` | `button down and press` |
| `0x08006918` | `Up, Down, Left, Right,` |
| `0x08006930` | `Right, Left, Down, Up.` |
| `0x08006948` | `To activate` |
| `0x08006954` | `Block Blaster Game.` |

The seven hint pointers at `0x080061D4`–`0x080061EC` are loaded individually
and drawn at `(x,y) = (0x44,0x34), (0x39,0x44), (0x2F,0x54), (0x2F,0x64),
(0x2F,0x74), (0x52,0x84), (0x2B,0x94)` by `0x080060FA`–`0x0800614A`.

### 6.4 Other screens/text (for the negative result)

Options: `Difficulty Easy/Medium/Hard`, `Music On/Off`, `SoundFX On/Off`,
`Credits`. Pause: `Continue Game`, `Find Move`, `Start New Game`, `Quit Game`.
Status: `PAUSED`, `LEVEL COMPLETED!`, `BONUS GAME COMPLETED!`, `GAME OVER!`,
`BAD LUCK`, `No More Moves.`, `Sorry!`, `Time Out.`, `Last Continue`,
`2 Continues` … `5 Continues`, `Restart`, `Quit`. No gallery, password, or
debug string exists.

The Time Challenge timeout dialog is a real menu, observed at
`TIME 00:00.00`:

```
SORRY!
TIME OUT.
5 CONTINUES
RESTART
QUIT
```

Selecting `RESTART` re-enters the stage (observed: the story cutscene plays
again). `QUIT` is the second entry; its return to the title is inferred from the
label and from the identical `QUIT GAME` behaviour in the pause menu.

## 6b. Enumeration

**Space definition.** The sequence is 8 D-pad steps over the alphabet
`{Up, Down, Left, Right}`; L is a separate held gate. The number of minimal
8-press sequences is `4^8 = 65,536`. Exactly **one** minimal sequence is
accepted: `UDLRRLDU`. The sequence table is 8 bytes at `0x0800A2FC`; there is no
checksum, no field packing, and no second table.

**Validator model.** A reimplementation that agrees with the ROM on accepted and
rejected inputs is:

```python
SEQ = [0x40,0x80,0x20,0x10,0x10,0x20,0x80,0x40]  # U D L R R L D U
def step(idx, held, pressed):
    if (held & 0x200) and (pressed == SEQ[idx]):
        idx += 1
        if idx == 8:
            return 0, True          # flag := 1
    return idx, False
```

The index persists across mismatch and across L release; only the flag write
completes the code.

**Table uniqueness.** A scan of the whole 4 MiB image for runs of at least six
bytes whose values are all in the D-pad mask set `{0x10,0x20,0x40,0x80}` found
337 runs. Only **three** contain more than one distinct value:

| Offset | Bytes | Verdict |
|---|---|---|
| `0xA2FC` | `40 80 20 10 10 20 80 40` | the code table (all four directions, 8 bytes, in the title-menu code/data region) |
| `0x30BE2` | `40 40 20 20 20 20 20` | 7-byte fragment inside font/graphics data |
| `0xC017F` | `20 20 20 20 20 20 80` | 7-byte fragment inside graphics data |

No second plausible key table exists. The only store to the unlock flag found
by the literal scan is the one at `0x08002130`.

**No password alphabet.** A scan for contiguous `[A-Z0-9!?]` runs of 16 or more
characters returns 1,321 hits, all inside graphics/compressed data (runs such as
`3333…`, `CCCC…`, `JJ…`); none is a contiguous alphabet in the ASCII text banks,
and no screen accepts typed characters. The only ASCII text banks are the
UI/status/hint strings listed in §6.3–6.4. The in-game code space is therefore
the button sequence only, not a password format.

**Novel inputs (not in any published list).**

1. **Decoy superset, 15 presses.** Hold L throughout:
   `Up, Up, Down, Right, Left, Left, Right, Down, Right, Up, Left, Right, Down,
   Left, Up`.
   The correct eight edges appear in order; the extra decoy presses are ignored.
   Result: `BLOCK BLASTER` appears (screenshot
   `Animal Snap - novel decoy superset.png`). This is not the GameFAQs string;
   it is accepted because mismatches do not reset the index.
2. **Both shoulders held.** Hold L **and** R, then press `UDLRRLDU`. Result:
   `BLOCK BLASTER` appears (`Animal Snap - novel L+R.png`). This proves the gate
   tests only the L bit (`0x200`) and does not require an exact modifier mask.

**Bounds proven by rejection** (each from a fresh reset, 3-item menu):

| Test | Observed |
|---|---|
| Published 8 steps with no shoulder held | 3 items, no Block Blaster |
| Published 8 steps with R held instead of L | 3 items |
| L held + eight Up presses (wrong sequence) | 3 items |
| L held + first 7 correct steps + wrong 8th (`Down` instead of `Up`) | 3 items |
| Then, without reset, L held + the missing `Up` | 4 items — progress was retained |

The rejection screenshots are `Animal Snap - reject no L.png`,
`Animal Snap - reject R held.png`, `Animal Snap - reject wrong sequence.png`,
and `Animal Snap - reject prefix 7 of 8.png`; the resumption is
`Animal Snap - locked menu.png` → `Animal Snap - title unlocked.png`.

**Published-code verification.** The archived GameFAQs cheat page
(`https://web.archive.org/web/20251114043209/https://gamefaqs.gamespot.com/gba/583060-animal-snap/cheats`)
lists exactly one unlockable, contributed by Caustickhan:

> At the title screen, hold the "L" shoulder button and press UP, DOWN, LEFT,
> RIGHT, RIGHT, LEFT, DOWN, UP on the D-pad. — Block Blaster bonus game.

The literal sequence matches the ROM table and the ROM's own hint text; the
emulator accepted it on the first attempt. No other published code for this
game was found (GameFAQs, TCRF, VGChartz, Giant Bomb, HonestGamers).

**Effect of the hidden entry.** Selecting `BLOCK BLASTER` starts a
Breakout-style game with a brick field, a paddle, a ball, a lives/ball counter,
a level indicator, and a score/record HUD. `Start` pauses (`PAUSED`); losing all
balls shows `GAME OVER!` and returns to the title. Secondary sources describe
this bonus game as the normal reward for collecting the letter tiles B, O, N, U,
S in order during a stage, and as having eight levels; the ROM's completion
branch draws `BONUS GAME COMPLETED!` when its completion counter reaches 10,
otherwise `LEVEL COMPLETED!` (derived, not exercised).

## 7. Validation evidence

**Observed (emulator / screenshots):**

* Title menu has 3 items before the code and 4 after; the fourth is
  `BLOCK BLASTER` (`Animal Snap - locked menu.png`, `Animal Snap - title
  unlocked.png`).
* Published minimal code accepted; four rejection cases rejected; progress
  retained after a wrong press; both novel variants accepted.
* Block Blaster starts from the hidden entry, pauses with `PAUSED`, and ends
  with `GAME OVER!` after the ball supply is exhausted.
* Arcade `TABLE 1`–`TABLE 4`, Options, Credits, pause menus and `BAD LUCK` were
  reached and photographed; the Time Challenge timeout dialog (`SORRY!` /
  `TIME OUT.` / `5 CONTINUES` / `RESTART` / `QUIT`) appeared at `TIME 00:00.00`
  and `RESTART` re-entered the stage.
* Reset clears the unlock; a 0-byte `.sav` is created (no save data).

**Derived (instruction-level):**

* Table at `0x0800A2FC`; index at `0x0300261C`; flag at `0x03001320`; L gate
  via `0x03001040 & 0x200`; edge compare via `0x03001324`; menu count
  `3 + flag`; only one store to the flag.
* Input update at `0x08001984` computes held and pressed as described.

**Inferred:**

* The hint text at `0x080068DC` is the game's own in-build hint for the code.
  It is drawn by the state routine at `0x08005C30` (entered from `main` at
  `0x08006374`, hint branch selected by byte `0x0300205C`), which loads all seven
  pointers at `0x080060FA`. The state that selects this hint page was not
  reached by normal play in this session; the text itself is shipping data.
* `BONUS GAME COMPLETED!` is the completion message for the bonus game's final
  round; the branch is visible at `0x08003CD2`, but the screen was not reached.
* The "eight levels" figure for Block Blaster comes from the HonestGamers
  review, not from an independent in-game count.

## 8. Unknowns

* **Block Blaster completion screen not exercised.** The string and the
  completion branch at `0x08003CC2` were recovered statically; reaching it
  requires clearing the bonus game's rounds. The exact number of rounds (8 per
  the review, 10 in the counter comparison) was not reconciled in play.
* **In-ROM hint screen not exercised.** The ROM text, its draw routine
  (`0x080060FA`) and its state routine (`0x08005C30`) were located, but the
  state that selects the hint page was not reached in this session. The text is
  present in the shipping image regardless of the trigger.
* **Header checksum word is zero.** The complement check is valid (`0x91`), but
  the stored header checksum at `0xBE` is `0x0000` instead of the computed
  `0x00C3`. mGBA boots the image; a real GBA BIOS may reject it. This is an
  image/identity caveat, not a cheat-system finding.
* The exact allocation/meaning of the Block Blaster state words (lives, level,
  paddle, ball, bricks) was not fully mapped; it is not required by the cheat.
* No memory read via GDB was used (the default GDB port was occupied by another
  unrelated emulator session). The held/edge model is derived from
  `0x08001984` and corroborated by the superset behaviour, not by a live memory
  dump.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd` — identity/header.
* `strings -t x` plus a Python ASCII-run census — text reconnaissance.
* Python 3 (standard library) — pointer scans, Thumb BL-target scan, key-mask
  run scan, literal/table extraction.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000
  -M force-thumb` — validator and input-update disassembly.
* mGBA 0.10.5 SDL, Xvfb `:138`, openbox, `xdotool`, ImageMagick `import` —
  dynamic verification and screenshots.
* Screenshots in this folder: `Animal Snap - locked menu.png`,
  `Animal Snap - title unlocked.png`, `Animal Snap - block blaster gameplay.png`,
  `Animal Snap - block blaster paused.png`,
  `Animal Snap - block blaster game over.png`,
  `Animal Snap - arcade table select.png`, `Animal Snap - options.png`,
  `Animal Snap - credits.png`, `Animal Snap - time out continue.png`,
  `Animal Snap - reject no L.png`, `Animal Snap - reject R held.png`,
  `Animal Snap - reject wrong sequence.png`,
  `Animal Snap - reject prefix 7 of 8.png`,
  `Animal Snap - novel decoy superset.png`, `Animal Snap - novel L+R.png`.

No ROM, extracted graphics, music or text banks are redistributed. Screenshots
are emulator observations used as evidence.

## 10. Legal note

The ROM was inspected locally; no ROM image or extracted copyrighted asset is
included in this report. All addresses, tables and generated inputs are
analysis results.
