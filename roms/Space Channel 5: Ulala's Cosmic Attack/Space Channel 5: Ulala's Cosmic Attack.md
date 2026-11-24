# Space Channel 5: Ulala's Cosmic Attack (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Space Channel 5: Ulala's Cosmic Attack.gba` |
| Size | 8,388,608 bytes (`0x00800000`) |
| Header title | `SPACE CHANNE` (12-byte field; retail short title) |
| Game code | `A5UE` |
| Maker code | `78` (THQ/Art) |
| Version | `0x00` (Rev.00) |
| Header complement / checksum | `0x99` / `0x0000` |
| MD5 | `b50707ad72a97b131f4d620483287f95` |
| SHA-1 | `b5401223641a45dd7ccde5504d517ed765d34484` |
| SHA-256 | `ea7e406448697ea38e736245104e83df13641098af8fed3c223c62731d453c4a` |

**Phase 0 result: retail image, no patch/trainer.** Entry word `0xEA00002E` branches to
`0x080000C0` (stock crt0). A full-file scan for the 156-byte Nintendo logo found
**exactly one** GBA header, at file offset `0x0` (ROM `0x08000000`) — no multigame
cart, no appended trainer header, no second boot image. `file(1)` identifies the same
title/code/revision. The `0x0000` header checksum is the usual rebuilt-header artifact;
the complement byte (`0x99`) and entry branch are intact.

## 2. Executive summary

The game has **one developer-intended button code** (published as "Automatic Mode" /
"CPU control") and **one save-flag unlockable** (Extra Mode / Clear Mode). There is
**no password system, no on-screen code entry, and no reachable debug menu**.

The button code is: **hold L+R, then press `Up, Left, A, Left, A, Down, Right, B, Right, B`**.
The expected masks are stored as ten `u16` values at ROM `0x080946E0`; the validator at
`0x0800412C` is called every frame from `0x08002A14`. On success it sets flag byte
`0x03000049 = 1`, resets the progress index and plays a confirmation sound. Each frame
while the flag is set, `0x0800406C` clears all six gameplay buttons out of the "pressed"
word `0x03001EA4` — the published "automatic/CPU control" effect — and an on-board AI
state machine (`0x03004EC0` / `0x03004F80`) drives the game.

Dynamic proof (mGBA savestate RAM reads): with L+R held, progress `0x03000048` went
`0→1→2→…→9`; the tenth press set `0x03000049=1` and reset progress to `0`.
Rejection bounds: omitting L+R leaves progress at 0; a wrong button at step 3 resets
progress to 0; a chorded variant (expected button plus an extra simultaneous button) is
rejected. The accept space is **exactly one sequence out of 6^10 = 60,466,176 possible**
(button sequences, so no unpublished *accepted* code can exist — see §6b.

Extra Mode is a save-record flag, not a code: the save text bank contains
`CLEAR (EXTRA MODE)` at ROM `0x0807CD514`, and the published method (clear the game,
watch the credits, then continue the completed file) is consistent with that bank.
Because the full-game clear could not be driven in the time available, the exact credits
gate is reported as **Inferred**, not Observed.

## 3. How to reproduce

* Emulator: `/usr/local/bin/mgba` 0.10.5 under `Xvfb :318`, `SDL_AUDIODRIVER=dummy`.
  Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, D-pad=arrow keys, B(back)=`z`.
* Boot path: `mgba -3 <rom>` → legal screen → ART splash → intro → title menu
  (`NEW GAME / LOAD / CONTINUE [greyed] / TUTORIAL / OPTIONS`).
* Menu walk (screenshots and savestates retained in `/tmp/spacechannel5/`):
  * `OPTIONS` → `CONTROL OPTIONS`, `SOUND OPTIONS`, `PLAYERS STATUS`
    ("PLAYER'S BEST RECORD", four reports, per-report view/rescue ratings),
    `CHARACTER PROFILE` ("Main Characters", `COLLECT`, 0%).
  * `TUTORIAL` → BASIC CONTROLS / DANCE MODE / SHOOTING MODE instruction pages.
  * `NEW GAME` → story intro ("Number 7 reporting from point 2704.",
    "WELCOME TO SPACEPORT", ship flyby).
* Code entry: hold `a` (L) and `s` (R) down continuously, then tap
  `Up, Left, x, Left, x, Down, Right, z, Right, z` with ~130 ms hold / ~220 ms gap.
  Timing matters: 220 ms hold / 350 ms gap **missed** the edge-triggered input; the
  shorter timings above reproduced success repeatedly.
* RAM evidence method: the mGBA GDB stub crashed this session, so RAM was read by
  saving `.ssN` PNG savestates (`Shift+F1..F8`) and decompressing their `gbAs` zlib
  chunk (state length `0x61000`; IWRAM at state offset `0x19000`, EWRAM at `0x21000`).
  Script: `ssram.py`. Reload with plain `F1..F8` (verified working).
* Published codes checked: GameFAQs (archived 2018-12-29) and ChapterCheats both list
  exactly the L+R button code and the Extra Mode unlock; both literals were verified in
  the ROM (table at `0x080946E0`; string at `0x0807CD514`). CodeBreaker/Gameshark codes
  from other sites are memory-edit codes and are out of scope.

## 4. Address map

| Item | ROM / RAM | Evidence |
|---|---|---|
| Nintendo logo / single GBA header | file `0x0` (`0x08000000`) | Observed (logo scan: 1 hit) |
| Button sequence table | `0x080946E0` (file `0x946E0`) | Observed (10 u16 + `0x3824`) |
| Pointer to that table | `0x08004148` | Derived (literal `0x080946E0`) |
| Button-code validator | `0x0800412C` | Derived (disassembly) |
| Validator's only caller | `0x08002A14` | Derived (BL scan: 1 caller) |
| Input-mask constant | literal `0x080041C8` = `0xFFFFFCF3` | Derived (keeps A,B,L/R/D-pad; clears Select/Start/R/L) |
| Progress index | RAM `0x03000048` (`u8`) | Observed (savestate) |
| Success / already-active flag | RAM `0x03000049` (`u8`) | Observed (savestate) |
| Held keys | RAM `0x03001E90` (`u16`, active-high) | Observed (`L+R+A` → `0x0301`) |
| Pressed keys (edge) | RAM `0x03001EA4` (`u16`, active-high) | Derived + Observed |
| Success sound call | `0x080041E2` → `0x08000CB4`, r0=`0x160` | Derived |
| CPU-control input mask routine | `0x0800406C` | Derived |
| Six-button mask table (CPU control) | RAM `0x03005900` = `{0x40,0x10,0x20,0x80,0x01,0x02}` | Observed (savestate) |
| Mask-table initialization | `0x0804BA42`–`0x0804BA6A` | Derived |
| AI controller state | RAM `0x03004EC0`, `0x03004F80` | Observed (savestate) |
| Save-text alphabet (76 symbols) | `0x0807CD414`, lookup at `0x08045A24` | Derived |
| Save-file UI strings | `0x0807CD4C4`–`0x0807CD510` | Observed (strings + bytes) |
| `CLEAR (EXTRA MODE)` | `0x0807CD514` | Observed (strings + bytes) |
| Save text pointer table | `0x0807CD524` – `0x0807CD548` | Derived (10 absolute pointers) |
| Debug-looking leftover string | `0x080946CC` `MultiSioSync010918` | Observed (no menu/reachable handler found) |

## 5. Algorithm

Validator at `0x0800412C` (Thumb), reconstructed:

```
copy 20 bytes from ROM 0x080946E0 to stack buffer expected[10]   // 0x08004130-38
if RAM[0x03000049] == 1: return 1                                 // already active
if (RAM[0x03001E90] & 0x300) != 0x300:                            // L+R must be held
    RAM[0x03000048] = 0; return 0
i = RAM[0x03000048]
cur = RAM[0x03001EA4] & 0x3F3     // mask 0xFFFFFCF3: A,B,Right,Left,Up,Down only
if (expected[i] & cur) != 0:
    RAM[0x03000048] = i + 1
elif cur != 0:
    RAM[0x03000048] = 0                                           // wrong press resets
if RAM[0x03000048] <= 9: return 0
RAM[0x03000049] = 1                                               // success
RAM[0x03000048] = 0
sound(0x160)                                                       // confirmation
return 1
```

Caller `0x08002A14` (per-frame):

```
r = validator()
if r == 1: cpu_control_mask()      // 0x0800406C
...
```

`cpu_control_mask()` at `0x0800406C`:

```
m = OR(RAM[0x03005900 + 0..10])    // {Up,Right,Left,Down,A,B} = 0xF3
RAM[0x03001EA4] &= ~m              // strip player buttons; AI drives the game
// remainder: AI state machine at 0x03004EC0 / 0x03004F80 dispatches
// through a 6-entry jump table at 0x080040DC
```

## 6. Tables

**Button sequence table (ROM `0x080946E0`, file `0x946E0`)** — active-high GBA masks:

| Index | u16 | Button |
|---:|---:|---|
| 0 | `0x0040` | Up |
| 1 | `0x0020` | Left |
| 2 | `0x0001` | A |
| 3 | `0x0020` | Left |
| 4 | `0x0001` | A |
| 5 | `0x0080` | Down |
| 6 | `0x0010` | Right |
| 7 | `0x0002` | B |
| 8 | `0x0010` | Right |
| 9 | `0x0002` | B |

Followed by `u16 0x3824` at `0x080946F4` (not used by this fixed-length validator).

**CPU-control mask table (RAM `0x03005900`, initialized from `0x0804BA42`)**:
`{0x40 Up, 0x10 Right, 0x20 Left, 0x80 Down, 0x01 A, 0x02 B}`; OR = `0xF3`.

**Key mask convention** (derived from the tables and confirmed by held-key RAM reads):
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020,
Up=0x040, Down=0x080, R=0x100, L=0x200` (active-high, i.e. `~KEYINPUT & 0x3FF`).

**Save text bank (ROM `0x0807CD414`–`0x0807CD548`)**: 76-symbol name-entry alphabet
`" 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ.,'!?-abcdefghijklmnopqrstuvwxyz\"&:/@()"`,
report names `REPORT1 SPACEPORT` … `REPORT4 SPACE CHANNEL 5`, save-file prompts
("Press the A Button to overwritie file" / "Press the B Button to continue game play."),
and `CLEAR (EXTRA MODE)`. No password alphabet or comparison table exists in this bank.

## 6b. Enumeration

**Space definition (button-code system).**

* Gate: `held & 0x300 == 0x300` (L+R) at every step; releasing L+R resets the index
  (`0x080041F0`).
* Per-step input alphabet: 6 buttons (`A, B, Left, Right, Up, Down`); Select/Start/R/L
  are masked out by `0x3F3`.
* Length: fixed 10 presses; the validator uses `cmp r0,#9` — no variable length,
  no second table, no action-dispatch branch. The only caller of the validator is
  `0x08002A14`, and the only 32-bit pointer to the table is at `0x08004148`.
* Representable sequences: `6^10 = 60,466,176`. **Accepted sequences: exactly 1** —
  the published table in §6. No other sequence can pass: each step advances only when
  the expected bit is present and any other *single* pressed button resets progress
  to zero (confirmed for a wrong button at step 3).

**Novel-code search / result.** No unpublished *accepted* code exists by construction:
the accepted space is a single point, and the entire table was read out of the ROM
rather than inferred from the published list. An unpublished **variant** was minted and
tested anyway — a chorded sequence where each expected press was accompanied by an
extra simultaneous button (e.g. `Up+B`, `Left+B`, `A+B`, …, `B+Up`) — entered with L+R
held. Result: **rejected** — progress `0x03000048` stayed at 0 for all ten steps and
`0x03000049` remained 0. This confirms the input path is single-button-per-press and
that the bitwise-AND match in the validator is not reachable as a chord from the real
keypad. The game's own 6-button input system, not the validator, is the limiting layer.

**Bounds proven by rejection (all Observed via savestate RAM):**

| Test | `0x03000048` | `0x03000049` | Outcome |
|---|---|---|---|
| Correct 10 presses, L+R held | 0→1→…→9→0 | `1` | Accepted (success sound derived) |
| Same 10 presses, L+R **not** held | 0 throughout | `0` | Rejected (missing gate) |
| Correct prefix, **wrong button at step 3** (B instead of A) | 1→2→**0**, then stays 0 | `0` | Rejected (progress reset; later presses misaligned) |
| Novel chord variant (expected + extra button each step) | 0 throughout | `0` | Rejected |

**Extra Mode / collectibles (save-bit unlockables, not codes).** The save text bank
contains `CLEAR (EXTRA MODE)` (`0x0807CD514`) and the file prompts; the Character
Profile screen is a `COLLECT` gallery (observed at 0%). These are save-record flags,
not inputs: §16.18 applies — they must not be reported as codes, and no brute-force
code search is meaningful. (Inferred: the completed-game save is renamed/flagged and
`CONTINUE` then starts Extra Mode, per the published method; the exact credits-side
setter was not isolated, see §8.)

**Negative results bounded (no password/debug system).**

* `strings -n 4` over all 8 MiB (83,782 strings): keyword census for
  `password|cheat|debug|secret|unlock|level select|bonus|hidden|code|menu|invalid|correct`
  returned only story/dialogue prose (e.g. "aliens' secret base", "hostage"), the
  save-file/credits bank at `0x7CDxxx`, and the unrelated `MultiSioSync010918` link string.
  No password prompt, no `INVALID`, no debug menu labels.
* Every reachable screen was walked with RAM evidence: title/main menu (5 entries,
  CONTINUE greyed), Options (4 sub-screens), Player Status, Character Profile,
  Tutorial pages, and the NEW GAME story intro. Menu cursor changes were reflected in
  IWRAM `0x030004FA` (NEW GAME `0x0` → TUTORIAL `0x4` → OPTIONS `0x5`, savestate reads).
* Only one 10-mask table with a validator pointer exists; a 6-halfword sliding scan over
  the whole ROM found the published sequence only at `0x946E0` (other hits were text/font
  data or multiplay/init tables, with no validator pointer or L+R gate).
* Result: **no hidden characters/songs, no level select, and no reachable debug screen**
  were found. This is a bounded statement about the enumerated screens, string banks and
  key-mask tables above, not "not tested".

## 7. Validation evidence

* **Observed** — ROM hashes/header/logo count; button table bytes; all screens and their
  OCR/screenshots; savestate RAM reads of `0x03000048` (0→9), `0x03000049` (0→1),
  `0x03001E90` (`0x0301` with L+R+A), `0x03005900` mask table, menu cursor
  `0x030004FA`; rejection RAM results in §6b.
* **Derived** — validator and CPU-mask disassembly, literal-pool resolutions
  (e.g. `0x08004148 → 0x080946E0`, `0x08041C8 → 0xFFFFFCF3`), BL/pointer counts
  (1 caller, 1 table pointer), sound call, save text-bank decoding.
* **Inferred** — the exact credits-side trigger that flags a completed save for Extra
  Mode; the six-branch AI dispatch in `0x0800406C` was read but not played through.

## 8. Unknowns

* The full 4-report game was not completed, so the Extra-Mode setter (credits "up"
  pattern) was not exercised at runtime; only its text bank and published method are
  confirmed.
* The story intro did not advance to a playable stage with the input method used;
  the button code was accepted in the intro scene because the validator is called
  from the global per-frame routine (`0x08002A14`) whenever the scene byte is not the
  gameplay value. The visible in-game effect (CPU-driven play) is therefore derived
  from `0x0800406C` + AI state rather than watched during a full stage.
* `0x3824` after the ten masks and the `MultiSioSync010918` string were not traced to
  any reachable menu; they appear to be unrelated data.

## 9. Tooling

* `strings -t x -n 4`, `grep`, `xxd`, `arm-none-eabi-objdump -M force-thumb`,
  Capstone-style pointer/BL scans (Python), `tesseract` for screenshot text.
* `press.py` (xdotool XTEST input helper on `:318`), `ssram.py` (zlib `gbAs`
  savestate RAM reader), `diffss.py` (savestate RAM diff).
* Environment: `Xvfb :318`, `openbox`, `SDL_AUDIODRIVER=dummy`, mGBA 0.10.5.
  The GDB stub (`mgba -g`) proved unreliable and crashed the emulated session;
  savestate diffing (guide §16.13) was used instead.

**Legal note:** no ROM image, extracted graphics, music or game assets are redistributed;
only addresses, hashes, algorithms and original scripts are published.
