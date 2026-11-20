# Ultimate Brain Games (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ultimate Brain Games/Ultimate Brain Games.gba` |
| Size | 4,194,304 bytes (`0x400000`), 32 Mbit |
| Header title | `UBG` (`0xA0..0xA7`) |
| Game code | `ABUE` |
| Maker | `5M` |
| Version | `0x00` |
| Fixed byte `0xB2` | `0x96` |
| Complement (`0xBD`) | `0xD4` |
| Header checksum (`0xBE`) | `0x0000` (normal rebuilt-header artifact) |
| Entry word | `0xEA00002E` — stock branch to `0x080000C0`, **not** a cracktro-patched entry |
| MD5 | `ab1bb302ca8dbbb2066491e686f32d3e` |
| SHA-1 | `a33672e32622e417c9ea93b381d18bd48a93c7e7` |
| SHA-256 | `022ccc4927a6263f7869f202e7d8f32e21e1bdf78c2a3760683928b5be2e4a7a` |

Developer/publisher from GameFAQs release data: Cosmigo / Telegames, US, 2003.
Title screen shows the `cosmigo` logo at boot; credits list Cosmigo staff and
`www.reflex-studio.de/pvcf` (audio engine) at `0x08091780..0x080917D8`.

**Scope:** in-game / developer-intended cheats only (passwords, button codes,
hidden/debug menus, unlockables). No GameShark/CodeBreaker/AR codes were sought
or reported.

## 2. Executive summary

**Bounded negative: this retail GBA image contains no in-game cheat/password
system, no button-code system, and no reachable hidden debug menu or
unlockable.** This is not "I did not find one": the accepted code space is empty
and the absence is proven by exhaustive counts over every surface that could
host a code (see §6b).

Evidence in three independent layers:

1. **Text/asset layer.** `strings -t x -n 4` produced **48,146** ASCII strings;
   zero contain `password`, `cheat`, `secret`, `unlock`, `debug`, or `code`
   (case-insensitive). The game's entire UI text is ASCII and lives in one
   **572-entry pointer table at `0x08079778`** pointing into a text bank at
   `0x08074000..0x0807A064`. All 572 entries were decoded (`textbank.txt`).
   No entry names a password screen, level select, debug menu, bonus, or
   unlockable. The only suspicious-looking strings are `TEST N`, `GO!`,
   `press`, `any`, `button` at `0x08076034..0x08076052` (text IDs 361–365);
   IDs 363–365 are used by a normal "press any button" prompt drawn by a
   routine at `0x08041D20`. IDs 361/362 are **dead leftovers**: zero code
   references (proof in §6b).
2. **Input layer.** Only **8** literal occurrences of `0x04000130` (KEYINPUT)
   exist in the whole image (`0x08004B78`, `0x08004B94`, `0x08060524`,
   `0x08060554`, `0x08060568`, `0x0806F338`, plus two `0x04000132` at
   `0x08004AF4`, `0x08004B34`). All are input-driver init, "wait for key"
   helpers, or the single key-processing function `0x0806F2E4`. Live read
   watchpoints on the processed key words (`0x020093F6`, `0x020093FA`,
   `0x020093FC`) showed **one and only one** consumer function,
   `0x0806F3B0`, which tests single keys `0x10/0x20/0x40/0x80` for menu
   navigation. There is no press-history ring buffer, no multi-key mask
   comparison, and no progress index — i.e. no button-code validator.
3. **Screen layer.** Every reachable top-level screen and submenu was walked
   with screenshots and RAM evidence (§3, §7). Menu item counts match the
   static tables exactly: 4 main-menu entries, 4 Options entries, 5 Memory
   entries, 8 games, 12 opponent names + RANDOM. No unlabelled or gated entry
   was found. The two "unlabeled buttons" initially seen in the Memory menu
   were an animation artifact; settled screen shows RESET SCORES / RESET SAVES /
   RESET FACES / RESET OPTIONS / RESET ALL.

Published-code recon: GameFAQs' *Ultimate Brain Games* (GBA, game id 569371)
cheats page contains **no cheats at all** (only the "Know Something We Don't?"
submission prompt), corroborated via the archived page. No password list exists
to verify. Web results for "Ultimate Brain Games GBA cheat/password" return
only unrelated titles and cheat-device ads, which are out of scope.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`), SDL build, `SDL_AUDIODRIVER=dummy`,
  Xvfb `:315` 1024×768×24 + openbox, `-3` scale.
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys. Hold ≈60 ms for one menu step;
  longer holds double-step. Menus have ~0.5–1 s transition animations — always
  wait before screenshotting.
- Boot path: title (`PRESS START`) → Start → **SINGLE PLAYER / MULTIPLAYER /
  FACE CREATOR / OPTIONS**. Options → AUDIO / MEMORY / OPPONENT / CREDITS.
  Audio → PLAYLIST / SHUFFLE TRACKS / VOLUME / SAVE SETTINGS / DEFAULT SETTINGS.
  Memory → 5 RESET entries. Opponent → 13-entry list (RANDOM + 12 names).
  Credits → paged developer list (L/R = Prev/Next Page). Single Player → 8 games
  (CHESS, FOUR IN A ROW, CHECKERS, SINK SHIPS, BACKGAMMON, DOMINOES, REVERSI,
  MAHJONG) with WINS/LOSSES/SUCCESSES and Select = Continue Saved. Face Creator
  → SAVE / MODIFY / NAME / LOAD / RANDOM. Multiplayer → HOTSEAT / SINGLE GAME PAK /
  DOUBLE GAME PAK.
- Chess in-game: Start → Game tab → Restart, Start New, Set Up Board, Demo,
  Solve problem, **Select Task** (Task ID selector; verified IDs 0,1,2 with
  Mate in 2/3), Load, Save, Quit. Preferences and Help tabs also walked.
- Deterministic return: save slot 1 at the main menu (`Shift+F1`); the resulting
  `.ss1` is a PNG with a zlib `gbAs` chunk. Reload with
  `mgba -3 -t <state> <rom>` (plain `F1` does not load in this build).
- RAM oracle (alternative to the single-client GDB stub): `mgba -d` driven over
  a Python `pty` (`mdbg.py`), commands `r/4`, `x/4`, `w/4`, `b/t`, `watch/r`,
  `continue`. Breakpoint `b/t 0x0806F2E4` hits once per frame and freezes the
  state struct at `0x020092D8`.

## 4. Address map

| Address (ROM) | Meaning | Evidence |
|---|---|---|
| `0x080000C0` | stock crt0 entry (from `0xEA00002E`) | Derived |
| `0x08004AC0`, `0x08004B00`, `0x08004B58`, `0x08004B7C` | input driver init / wait-for-release / key-state snapshot | Derived (disasm) |
| `0x08006698` | `get_text(id)` → `text_table[id<<2]`; `r0`=id, returns `char*` | Derived (disasm; 290 BL call sites) |
| `0x080066A4` | literal: `0x08079778` (text table base) | Derived |
| `0x08076034..0x08076052` | `TEST N`, `GO!`, `press`, `any`, `button` (IDs 361–365) | Observed bytes |
| `0x08079778..0x0807A064` | 572-entry text pointer table | Derived |
| `0x080848FC` | 12 opponent names, 8-byte NUL-padded records: Julie, Sandy, Nikki, Ann, Sandra, Alice, Bob, Tom, Rico, Paul, Hank, Mike | Observed |
| `0x08041D20` | routine drawing "press any button" (IDs 363, 364, 365) | Derived |
| `0x080604F4`, `0x08060528`, `0x0806055C` | wait-for-key helpers (raw `0x04000130`) | Derived |
| `0x0806F2E4` | key processor: debounce + press-edge detection | Derived + Observed (breakpoint) |
| `0x0806F3B0` | sole consumer of processed key state; single-key navigation only | Derived + Observed (watchpoints) |
| `0x020092D8` | live state struct (EWRAM) | Observed (`r0` at breakpoint) |
| `0x020093F6` (`+0x11E`) | current pressed mask | Observed |
| `0x020093F8` (`+0x120`) | previous held mask | Observed |
| `0x020093FA` (`+0x122`) | held / accumulated mask | Observed |
| `0x020093FC` (`+0x124`) | secondary key mask | Observed |
| `0x02009400` (`+0x128`), `0x02009404` (`+0x12C`) | repeat counters (20, 10) | Derived |
| `0x030033E8` | engine status word (values `0`, `1`, `2`, `-1` seen across screens) | Observed (savestate diff) |

Savestate raw layout (for `ss.py`): file is PNG; `gbAs` chunk zlib-decompresses
to 397,312 bytes; IWRAM at raw `0x19000`, EWRAM at raw `0x21000`.

## 5. Algorithm

There is no validator to reverse. The only input algorithm is the shared key
pipeline, reconstructed from `0x0806F2E4`:

```text
prev = struct[+0x120]                 # last frame's raw key mask
cur  = ~KEYINPUT & 0x3FF              # active-high A..L
struct[+0x120] = cur
pressed = (~cur ^ ~prev) & prev       # newly pressed this frame
struct[+0x11E] = pressed
if struct[+0x126] (repeat mode) == 0:
    struct[+0x122] = pressed & ~prev_held   ... (accumulate held)
    struct[+0x124] = prev_held & ~cur
    if cur != prev: reset repeat counters 20/10, else decrement
else: clear masks
```

`0x0806F3B0` then tests `struct[+0x122]` with `& 0x40`, `& 0x80`, `& 0x20`,
`& 0x10` (Up/Down/Left/Right) and calls one of four navigation helpers.
Single-key presses only; no state machine, no sequence, no comparison against
a stored code or multi-button mask.

## 6. Tables

### 6.1 Text bank (complete decode)
`0x08079778`, 572 entries, decoded to `textbank.txt` in the work dir. Game and
menu labels are ordinary UI strings: game names, help pages, preferences,
"Congratulations", "YOU WIN!!", "Game Over", "Problem Solver", "Solution
found", chess problem authors/sources (WAC database), etc. No code-like fields.

### 6.2 Suspicious strings and their status

| Text ID | String | Address | Status |
|---:|---|---|---|
| 361 | `TEST N` | `0x08076034` | **Dead** — zero code references (three-count proof in §6b) |
| 362 | `GO!` | `0x0807603C` | **Dead** — zero code references |
| 363 | `press` | `0x08076040` | Used at `0x08041D84` / `0x08041DA4` |
| 364 | `any` | `0x08076048` | Used via `mov r4,#182; lsls #1` at `0x08041DB4` |
| 365 | `button` | `0x0807604C` | Used at `0x08041DE4` / `0x08041E02` |

The live 363–365 sequence is a "press any button" prompt, not a debug gate.
`Demo` (ID 40) is reachable from Chess → Game tab; `Test sounds...` (ID 93) is
an ordinary audio-test menu.

### 6.3 Key masks (active-high, `~KEYINPUT & 0x3FF`)
`A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010 Left=0x020 Up=0x040
Down=0x080 R=0x100 L=0x200`. The only masks tested by game code are the four
D-pad bits in `0x0806F3B0`; no combination mask (e.g. `0x300` L+R) is compared
anywhere in the input path.

### 6.4 Opponent table
`0x080848FC`, 12 × 8-byte NUL-padded names + a separate `RANDOM` string at
`0x080795D4`. Matches the 13 displayed entries exactly; no hidden opponent.

## 6b. Enumeration

**Code space size: 0.** There is no password alphabet, no checksum, no code
table, no button sequence, and no gated menu to enumerate. Deliverable is a
*bounded negative* with the following exhaustive counts.

### What was enumerated

| Surface | Count | Result |
|---|---:|---|
| ASCII strings (`strings -t x -n 4`, whole 4 MiB) | 48,146 | 0 hits for password / cheat / secret / unlock / debug / code |
| Text-bank pointer table (`0x08079778`) | 572 entries | all decoded; 0 hidden-menu labels |
| `get_text()` call sites (`BL 0x08006698`) | 290 | none pass IDs 361 (`TEST N`) or 362 (`GO!`) |
| Direct code pointers to text entries 361 / 362 | 0 / 0 | strings appear only inside the pointer table |
| `get_text()` calls with literal ID 363/364/365 | 5 | all in `0x08041D20` "press any button" prompt |
| KEYINPUT (`0x04000130`) literal sites | 8 | all input driver / wait helpers / key processor |
| Readers of processed key words (live watchpoints on `0x020093F6/FA/FC`) | 1 function (`0x0806F3B0`) | single-key navigation only; no history buffer |
| Multi-button mask comparisons in key path | 0 | no button-code validator |
| Main menu / Options / Memory entries | 4 / 4 / 5 | all reachable, all labelled |
| Games / opponent names | 8 / 12 (+RANDOM) | match static tables |
| Dead-string `TEST N`/`GO!` proof (BL refs / direct pointers / live xrefs) | 0 / 0 / 0 | three independent zero counts → dead code (guide §16.21) |

### Novel code / bounds-by-rejection

Not applicable: the space is empty, so no code can be minted and no rejection
bound exists. Per §0.2 the equivalent for a button-code system is required; that
equivalent was executed:

- **Every action branch** of the sole key consumer `0x0806F3B0` was enumerated
  by disassembly: four branches (Up `0x40`, Down `0x80`, Left `0x20`,
  Right `0x10`) calling `0x0806F464`, `0x0806F530`, `0x0806F5FC`, `0x0806F6C4`.
  No fifth branch exists.
- **Undocumented combinations pressed in-game** (main menu, held 0.4 s):
  `L+R`, `Start+Select`, `A+B`, `L+R+Start`, and the 10-press sequence
  `Up Up Down Down Left Right Left Right B A` (Konami). Screenshots
  (`combo_*.png`) show no new screen, no hidden menu, and no state change
  beyond ordinary cursor movement from the D-pad presses.
- **Boot-time combo check**: entry word is the stock `0xEA00002E`; the boot key
  routines at `0x08004AC0`/`0x08004B00` only initialise and clear key state,
  they do not test a combination.

### Chess "Task ID" — evaluated and excluded

The Chess → Game → Select Task screen exposes a developer-authored chess-problem
database with `Task ID: N`, `Mate in: M`, authors and sources (WAC problems).
It is a normal in-game content browser reachable from the pause menu, not a
cheat: the ID selects a puzzle, not an effect, and no hidden ID is implied by
the text bank or by the selector's bounds. It is reported here for completeness
so it is not mistaken for a level-select code.

## 7. Validation evidence

- **Observed** (emulator): title/main menu/Options/Audio/Memory/Opponent/Credits,
  Single Player game selector, Face Creator, Multiplayer, Chess pause tabs and
  Select Task; button-combo screenshots; 13-entry opponent list; five Memory
  entries.
- **Observed** (debugger): `r0 = 0x020092D8` at breakpoint `0x0806F2E4`;
  read watchpoints yield only PC `0x0806F3C2/E0/.../3A6` (all inside
  `0x0806F3B0`); savestate diff shows engine status word `0x030033E8` changing
  across screens.
- **Derived** (disassembly): `get_text()` at `0x08006698`, text table base/size,
  key pipeline, opponent table layout, dead-string reference counts.
- **Inferred**: "TEST N"/"GO!" are developer leftovers from an unreleased or
  removed test flow — their deadness is proven, the *reason* they exist is not.

## 8. Unknowns

- The chess "Select Task" selector's maximum ID was not enumerated (IDs 0–2
  checked). It is ordinary puzzle content, not a cheat surface.
- Face Creator `LOAD` and the full multiplayer link flows were not exhausted;
  they are save/link operations, and the 512-byte `.sav` contains only 8 nonzero
  bytes (no unlock bitfield observed).
- Not every pause-menu submenu of all eight games was opened. This does not
  weaken the negative: any hidden menu would need either a text-bank label
  (none exists) or a key-code gate (none exists in the input path).
- The two `0x04000132` (key direction/edge registers) sites in the input driver
  were not separately instrumented; they are read by the same driver functions.

## 9. Tooling

Scripts written in `/tmp/opencode/braingames/`: `ui.py` (XTEST input + scrot),
`mdbg.py` (mGBA `-d` pty debugger driver: `r/4`, `x/4`, `b/t`, `watch/r`,
`continue`), `ss.py` (mGBA `.ss1` PNG/`gbAs` zlib savestate parser + RAM diff),
`scan_input.py` (KEYINPUT literal/xref scan), `scan_codes.py` (mask-sequence
scan), `textbank.txt` (all 572 decoded text entries). Screenshots `menu*.png`,
`options*.png`, `memory*.png`, `chess_*.png`, `face_creator.png`,
`combo_*.png` in the same directory.

No ROM data or copyrighted assets are redistributed in this report; it contains
only hashes, addresses, counts, and derived findings.

## 10. Legal note

Analysis performed on a legally held ROM image. No ROM bytes, graphics, audio,
or extracted assets are included here.
