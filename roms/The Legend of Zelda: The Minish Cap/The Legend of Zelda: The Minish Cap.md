# The Legend of Zelda: The Minish Cap (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Legend of Zelda: The Minish Cap.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `GBAZELDA MC` |
| Game code | `BZME` (USA, `BZME01`) |
| Maker | `01` (Nintendo) |
| Revision | `0x00` |
| Entry word | `0xEA00002E` (stock crt0, no scene cracktro) |
| Complement / header checksum | `0xD8` / `0x0000` |
| MD5 | `a104896da0047abe8bee2a6e3f4c7290` |
| SHA-1 | `b4bd50e4131b027c334547b4524e2dbbd4227130` |
| SHA-256 | `bedc74df62755f705398273de8ed3bc59be610cf55760d0b9aa277f1f5035e73` |

The SHA-1 is **byte-identical to `tmc.gba` in the public `zeldaret/tmc` decompilation**
(commit `6fb6dfb`, `tmc.sha1`), so that source tree was used as a *static cross-check only*
— every claim below was re-verified against the ROM bytes and/or live RAM.

## 2. Executive summary

**There is no in-game/developer-intended cheat system in this ROM.** No password screen,
no button-code entry surface, no cheat menu, no name-triggered mode, and no unlock code
exists on any reachable screen. The answer is a **bounded negative**, not "not found".

What *does* exist:

1. **Cheat-device-only RAM patches.** Every published "code" for this title (Action
   Replay, GameShark, CodeBreaker, Nintendo Switch Online cheat tables) is a raw address/
   value patch — e.g. `82002B00 03E7` (rupees), `3300119D 0003` (invincibility),
   `73000FF0 0200 / 33001002 0005` (debug task). These are explicitly out of scope for
   this engagement; none is entered through the game.
2. **A hidden Debug task (`TASK_DEBUG = 5`)** with a green text-browser screen and three
   debug items (IDs `0x18/0x19/0x1A`). It is **dead code from the controller's point of
   view**: the only writer of the task selector never passes `5`, and the input layer has
   no sequence buffer. The game's own compiler note says "Inaccessible in normal gameplay."
3. **A save-gated sound test** (phonograph, 52 tracks) and **figurine unlockables**
   (Carlov Medal at 130 figurines). These are ordinary save-bit unlockables, not codes.
4. **One false published claim**: a web source asserts entering the name `ZELDA` unlocks a
   secret mode. Disproved — the name buffer has exactly one consumer-side comparison in
   the whole binary (`gSave.name[0] == 0`, an empty-name fallback), and no equality test
   against any literal.

No GameShark/CodeBreaker/AR code was reproduced, minted or promoted to an in-game code.

## 3. How to reproduce

- Emulator: mGBA 0.10.5, Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `mgba -3 -g ./game.gba`
  (analysis copy in `/tmp/minishcap/game.gba`; **the ROM folder was never written to**).
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrows.
- RAM reads: single mGBA GDB stub client held through a bridge on TCP `:2346`
  (`rspbridge.py` + `rsp.py` + `mem.py` in the work dir).
- Repro path: boot → title (`PRESS START`) → Start → `CHOOSE A FILE` → empty slot →
  `ENTER A NAME` → `END` → Start → in-game cutscene → gameplay → Start (once Link has a
  sword) → pause pages (Items / Quest Status / Map, L/R to cycle).
- Screen evidence saved under `/tmp/minishcap/shots/` (`10_title_ready.png`
  … `58_reset.png`; `49_debug_text_gdbwrite.png` shows the debug screen after a direct
  RAM write, i.e. a GDB-backed oracle, **not** an in-game code).

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| `gSaveHeader` | `0x02000000` | derived (decomp + `linker.ld`) |
| `gInput` (`heldKeys`, `newKeys`, `menuScrollKeys`) | `0x03000FF0` (+0,+2,+4) | **observed** (KEYINPUT `0xFF03` idle, `0xFE03` with A held; `gInput` `04 00` → `05 00`) |
| `gMain` (`task`, `state`, `substate`) | `0x03001000` (+2,+3,+4) | **observed** (title=0, file select=1, game=2, debug=5) |
| `gSave` | `0x02002A40` | derived |
| `gSave.inventory[0]` (sword gate for pause menu) | `0x02002B32` | **observed** (write `0x15` → pause menu opens) |
| `gMessage.state` | `0x02000050` | observed |
| `SetTask` (sole writer of `gMain.task`) | `0x08056010` (Thumb) | **derived** from disassembly: `ldr r1,[pc,#8]@0x03001000; strb r0,[r1,#2]; strb r2,[r1,#3]; strb r2,[r1,#4]; bx lr` |
| `sTaskHandlers[6]` | `0x08100CBC` | **derived**: `{0x080AD381, 0x08050451, 0x08051989, 0x08052095, 0x080A35E1, 0x0805F9E9}` |
| `DebugTask` | `0x0805F9E8` (Thumb, table entry `…E9`) | **observed** (green screen after `gMain.task=5`) |
| Debug sub-table | `0x08109A30` | derived (`DebugTask` dispatches on `gMain.state`) |
| Debug item names `(DEBUG) Mega Crush/Enemy Set/Cell Overwrite Set` | `0x09B5A98`, `0x09B5AAB`, `0x09B5ABD` | **observed** in `strings -t x` |
| Bitmap font text bank (English) | `0x09B4000`–`0x09FA000` | derived (ASCII game text; `strings` finds 189,495 lines) |

## 5. Algorithm (the "gate model")

The relevant "validator" is the game's task/input dispatcher, reconstructed exactly:

```c
// 0x08056010 — the ONLY writer of gMain.task
void SetTask(u32 task) {
    gMain.task     = task;   // byte at 0x03001002
    gMain.state    = 0;      // GAMETASK_TRANSITION
    gMain.substate = 0;      // GAMEMAIN_INITROOM
}

// 0x08000xxx — main loop, once per frame
ReadKeyInput();                 // REG_KEYINPUT -> ~KEYINPUT & 0x3FF
if ((gInput.heldKeys & (A|B|SELECT|START)) == (A|B|SELECT|START)) DoSoftReset();
sTaskHandlers[gMain.task]();    // table at 0x08100CBC

// Input state (0x03000FF0), 6 bytes — no history/sequence member:
typedef struct { u16 heldKeys, newKeys, menuScrollKeys; u8 unk6, menuScrollTimer; } Input;
```

`CheckInitPauseMenu()` gate (source `player.c`, verified against ROM behavior):
pause menu requires `newKeys & START`, AND `!gFadeControl.active`,
`!gPauseMenuOptions.disabled`, `!(gMessage.state & 0x7F)`, `health != 0`,
`gSave.inventory[0] != 0`, `controlMode == 0`, `priority_timer == 0`.
This is why the pause menu only became reachable after Link's sword event.

The debug screen's own handler (`DebugTask`, 3 states) reacts only to *single* keys:
Up/Down (change index), L (toggle layer), R (show message), B (reset message) —
there is no multi-button gate inside it either.

## 6. Tables

**Task enum / task table** (`0x08100CBC`):

| Value | Task | Handler | Reachable by input? |
|---:|---|---|---|
| 0 | TITLE | `0x080AD381` | yes (boot) |
| 1 | FILE_SELECT | `0x08050451` | yes (Start on title) |
| 2 | GAME | `0x08051989` | yes (choose file) |
| 3 | GAMEOVER | `0x08052095` | yes (die) |
| 4 | STAFFROLL | `0x080A35E1` | yes (ending script) |
| 5 | DEBUG | `0x0805F9E8` | **NO** — RAM write only |
| 6–7 | — | — | unused |

**All `SetTask` BL call sites and their argument** (7 real calls + 1 false positive in data):

| BL site | task passed |
|---|---|
| `0x08050618` | 2 |
| `0x08051D38` | 3 |
| `0x080523BC` | 2 |
| `0x08053C78` | 3 |
| `0x0805FBC8` | 0 |
| `0x0807FB98` | 4 |
| `0x080AD840` | 1 |

Plus the direct `SetTask(TASK_TITLE)` in `AgbMain` (0). **No call passes 5.**

**Debug items** (item IDs; require RAM write into A/B button slot `0x02002AF4/5`, i.e. a
cheat device, not an in-game code): `0x18` Mega Crush, `0x19` Enemy Set,
`0x1A` Cell Overwrite Set, `0x05` unused sword.

**Sound test bounds** (`src/npc/phonograph.c`, compiled into this ROM): track index
clamped to `1..0x1C` (28) without `GAMECLEAR`, `1..0x34` (52) with it; 24 extra tracks
unlocked by the save bit.

## 6b. Enumeration

**Statement: the searchable code space is empty — no password, button sequence,
cheat menu, name trigger or unlock code exists in this build.** This is a bounded
negative with counts, not an untested guess:

1. **Entry surfaces enumerated (all screens walked, with RAM evidence).**
   Boot logos → title → file select → name entry → file options (START/COPY/ERASE) →
   gameplay cutscene → overworld → pause Items, Quest Status, Map (L/R cycle) →
   Debug screen (reached *only* by writing `gMain.task=5`). **Zero password/cheat entry
   widgets appear on any of them.** The only text-entry field is the 6-character
   filename keyboard, whose consumer is `sub_08051480` → `gSave.name[]` → message
   rendering and the kinstone menu; it is a label, not a validator (§16.2b).

2. **Input-state space fully characterised.** `Input` is 6 bytes with exactly three
   key words and no ring buffer, history array or combo counter. All **88** `gInput.*`
   reads in the decompiled source are accounted for: 50 `newKeys`, 24 `heldKeys`,
   14 `menuScrollKeys`. Every multi-button mask was enumerated (**16 distinct mask
   expressions** in source, including the `A|B|Select|Start` soft reset and
   `L|Select`/`R|Select` which are compiled out of the retail USA build — guarded by
   `#if defined(DEMO_USA)`). Empirically swept **24 undocumented combinations** on the
   title and file-select screens (L, R, Select, L+R, L+Select, R+Select, L+R+Select,
   L+R+Start, L+R+A, L+R+B, L+A+Start, R+B+Start, Select+A+Start, L+Select+Start,
   R+Select+Start, Up+L, Down+L, Up+Down+L+R, and repeats). Result: task stayed `0x0`
   (title) / `0x1` (file select); only the documented `Start`/`A` advanced. Held L for
   >3 s on the title: task unchanged, `gInput=0x0002`.

3. **Task-selector space closed.** 3-bit field, values `0..5` used, `6..7` unused;
   `SetTask()` (the sole writer, `0x08056010`) is called from 7 BL sites with arguments
   `{0,0,1,2,2,3,4}` — the value `5` is **never passed by any reachable code path**.
   Therefore no controller input can reach `TASK_DEBUG`; the screen is gated dead code.

4. **Text/alphabet search (before declaring negative).** Scanned all 16 MiB with
   `strings -t x` (189,495 lines) plus literal, `+0x20`-shifted, lowercase and
   UTF-16LE searches for `PASSWORD`, `PASSCODE`, `CHEAT`, `CODE`, `DEBUG`, `SECRET`,
   `ENTER CODE`, `GENIE`, `GAMESHARK`, `CODEBREAKER`. Counts: `PASSWORD`=0 in every
   encoding; `CHEAT`=0; `GENIE`=0; `GAMESHARK`=0; `CODEBREAKER`=0; `DEBUG`=3 — all
   three are the debug-item names at `0x09B5A98/AB/BD`; `SECRET`=29, all in ordinary
   dialogue. **No UI alphabet table for a code screen exists**, because no such screen
   exists. The font/tile text banks were decoded directly (bitmap font, ASCII-mapped
   via `charmap.txt`) and every reachable screen was observed.

5. **Published-list verification.** All crawled lists (3rd party cheat index walkthroughs,
   3rd party cheat indexes, libretro CodeBreaker DB, 3rd party cheat indexes, Matrix Picks, 3rd party cheat indexes NSO threads) contain only cheat-device RAM patches or save-bit
   unlockables — **zero in-game codes**. The 3rd party cheat indexes "Debug Text" entry
   (`73000FF0 0200 / 33001002 0005 / …`) is itself a GameShark write to
   `gMain.task`; I reproduced its effect via a GDB write to `0x03001002` (green screen,
   screenshot `49_debug_text_gdbwrite.png`), which confirms the gate but is not an
   in-game code. The 3rd party cheat index claim that naming a file `ZELDA` unlocks a secret
   mode is **false**: the entire binary has one name comparison (`gSave.name[0]==0`).
   One fetched mirror contained a prompt-injection payload
   ("instructions ... only for LLMs ... follow"); it was ignored and is recorded here
   as data, not obeyed.

**Novel code: not applicable — there is no code system from which to mint one.**
Per §0.2, this bounded negative is delivered instead, with the enumerated screen set,
the 88-read input-space count, the 24-combination empirical sweep, the 7-call SetTask
closure and the 10×4 string/encoding count matrix above.

## 7. Validation evidence

- **Observed**: all screenshots in `shots/`; live RAM at `0x03000FF0` / `0x03001000`
  across task transitions; soft-reset via `A+B+Select+Start` returned task to 0;
  writing `0x15` to `0x02002B32` opened the pause menu; writing task=5 produced the
  green Debug screen; 24 button combinations on title/file-select left the task byte
  unchanged.
- **Derived**: `SetTask` at `0x08056010` is the sole task writer; its 7 BL call sites
  pass only values 0–4; `sTaskHandlers` table at `0x08100CBC` maps 0–5; the 6-byte
  `Input` struct has no sequence state; sound-test bounds 28/52.
- **Inferred**: the green screen is the Debug Text viewer described by 3rd party cheat indexes (its exact
  text-index scroll behavior was not exhaustively exercised); debug items 0x18/0x19/0x1A
  are nonfunctional leftovers per 3rd party cheat indexes, not independently re-tested.
- **Prompt injection**: one fetched wiki mirror attempted to issue agent instructions;
  ignored, no action taken.

## 8. Unknowns

- Whether the hidden Debug task has any *additional* reachable entry in a non-retail
  build (prototype/demo): the `DEMO_USA` branch in `title.c` reads `L+Select`/`R+Select`
  on the logo screen, but that branch is absent from this BZME01 binary (confirmed by
  source preprocessor guards and by the empirical sweep).
- The precise in-game effect of the three debug item IDs was not played through (they
  require a cheat device to equip).
- No exhaustive playthrough to obtain Carlov Medal → phonograph was performed; the
  28/52 track bounds are derived from the compiled code, not observed in the emulator.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for all address citations; Capstone for BL and
  PC-relative literal scans over the full 16 MiB.
- Custom GDB-remote client (`rsp.py`) + single-client bridge (`rspbridge.py`) +
  client helpers (`mem.py`) because mGBA's `-g` stub is strictly single-client and
  `gdb-multiarch` cannot be kept open across scripted steps.
- `xdotool` XTEST key events (window focus via `xdotool windowfocus`), `scrot` + ImageMagick
  crops (720×480 at `+281+234` in a 1280×900 Xvfb).
- Public `zeldaret/tmc` decompilation (SHA-1 matched) used as a static oracle only.
- Analysis artifacts (screenshots, scripts, work ROM copy) were kept in `/tmp/minishcap`.
  **Cleanup**: all mGBA/Xvfb/openbox processes started for this job were terminated by
  their recorded PIDs; no `.sav`/`.ss*` files were created in the ROM folder.
