# Disney's American Dragon: Jake Long — Rise of the Huntsclan (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Disney's American Dragon: Jake Long - Rise of the Huntsclan.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title | `AM DRAGON` (`0xA0`, NUL padded) |
| Game code | `BAPE` |
| Maker code | `4Q` |
| Version | `0x00` |
| Complement check | `0x4B` (matches computed value; header not hand-edited) |
| Header checksum | `0x0000` (normal rebuilt-header artifact) |
| Entry word | `0xEA00002E` (stock ARM branch; no cracktro) |
| Nintendo logo | exactly one hit, header at file `0x0` (no second GBA header, no appended trainer) |
| MD5 | `8a46b929f0dc1522fc0cc378685d8337` |
| SHA-1 | `4701c8d26cc608109bc01d0ee189ab1fb646ead8` |
| SHA-256 | `4f904d42234bc6eb2f8f21ab97a0066c60090db6458df5a0e16735f23491bbce` |

Developer: WayForward; publisher: Buena Vista Games (2006). Image is the retail
UE multi-language build. No patch, trainer, or header edit detected.

## 2. Executive summary

This ROM has **no password / code-entry system**. A full text and menu sweep found
no password screen, no alphabet string, and no validator: `PASSWORD` 0 hits,
`CHEAT` 0, `UNLOCK` 0, `LEVEL SELECT` 0, `SECRET` 2 (story dialogue only),
`DEBUG` 1 (a menu label).

What it *does* contain is a complete, compiled-in **developer debug tree** with
three independent entry points:

1. **Boot debug menu** (state `0xC0`): `Beta v18  5/22/2006, 3:20pm` / `Startup` /
   `Unit Tests`.
2. **Scene-select menu** (state `0xCE`), reached from "Unit Tests": 20 records
   (`Tutorial`, `World1..5`, `Bosses`, `Gyms`, `Cut Scenes`, `Cut Ending Scenes`,
   `AnimText`, `Auto-save`, `Game Over`, `Select File`, `Legals`, `Level Up!`,
   `Win`, `Credits`, `Lives`, `Cyclops Cutscene`) with five nested sub-menus
   (Bosses 7, Gyms 20, Cut Scenes 20, Cut Ending Scenes 3, AnimText 1).
3. **In-game QA harness** (state `0xCD`): `World1..5`, `Final`, `Super`,
   `> level+`, `> debug`, `all friends`, `fill focus`, `< return`, plus
   `Level: a.b.c.d` and `Room: 1..15` test-matrix fields.

All three are gated by one byte, `0x03006AE0`. Its only writer in the image
stores **0** (`0x080128D4`); the two readers are the boot branch
(`0x08013778`) and the in-game combo check (`0x08041D10`-region, see §4). No
controller input can set it, so the tree is unreachable in the retail build.
The published CodeBreaker code "Access Debug Menu [Press Select+Up]" does not
use a game button code at all — it decrypts to `IF [0x04000130]==0x03BB THEN
[0x030019D0]=0xC0`, i.e. it writes the state byte by memory edit. That was
verified byte-for-byte and the menu does open.

The debug records, state ids, and effects were enumerated and RAM-verified
(§6b). Novel, unpublished results: the `Gyms` entity-test browser (20 entities),
the `Cyclops Cutscene` scene (state `0x31`), and the QA-harness `all friends`
toggle (`0x03006BD8..DA = 01 01 01`). Bounds were proven by rejection: state ids
outside 1..246 fall through to the default handler, and both menu lists wrap
instead of overrunning.

## 3. How to reproduce

Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:318`, 3× scale.

Default mGBA SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows.

Menu path (retail, no debug): language select → Buena Vista logo → title
(`PRESS START`) → file select (3 slots, copy/clear) → intro cutscene → gameplay
→ `Start` pause (`CONTINUE` / `QUIT`).

Debug paths (need the gate byte, see §7 for the lab method):
* Boot menu: set `0x03006AE0=1` before state 1, or force `0x030019D0=0xC0`.
* Scene menu: boot menu → `Unit Tests` (`Start`).
* Sub-menus: scene menu → `Bosses` / `Gyms` / `Cut Scenes` / `Cut Ending Scenes` /
  `AnimText` (`Start`).
* QA harness: with `0x03006AE0=1`, hold `Select` and press `B` in gameplay.
* Quit prompt: with the flag set, hold `Select` and press `R` (`ARE YOU SURE? YES/NO`).

Savestates: mGBA `Shift+F1..F10` save, `F1..F10` load. The debug menu accepts
`Start`; the QA harness accepts `A` or `B`; the scene/sub-lists accept `Start`.

## 4. Address map

ROM address = `0x08000000 + file_offset`.

| Address | Role |
|---|---|
| `0x030019D0` (byte) | requested game state id |
| `0x0300373C` (byte) | committed state id |
| `0x080124B6`..`0x080124CE` | state dispatcher: `state-1`, bounds `cmp #0xF5`, `table[state-1]()` |
| `0x080124D4` | 246-entry `u32` state-handler table (ids 1..246) |
| `0x08013614` | default/commit handler (copies `0x030019D0` → `0x0300373C`) |
| `0x08013638`..`0x08013A0C` | debug overlay state machine (`cmp` chain 0xC0,0xC2..0xF6) |
| `0x08017ABC` / `0x08017D18` | list UI: input/repeat, redraw, confirm |
| `0x03006D74` | current list base pointer |
| `0x03006D6C` | current list count |
| `0x03006D78` | current list index |
| `0x03006D70` | sub-field cursor (`Level` value, 1..4) |
| `0x03003518` | input repeat timer |
| `0x03006AE0` (byte) | **debug-enable gate** (only writer stores 0) |
| `0x080128D0`/`0x080128D4` | boot clear: `[0x03006AE0]=0` |
| `0x08013778` | boot read: if gate != 0 → request `0xC0`, else `0xC8` |
| `0x08041D10`..`0x08041D72` | in-game read: if gate != 0 and `Select`, then A/B/R actions |
| `0x08041D9A`..`0x08041DD4` | `L+R` held 15 frames → soft reset (not a cheat) |
| `0x03001F34` (u16) | key state (A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200) |
| `0x030019D8` (u16) | per-frame key/edge state used by the gate check |
| `0x03006BD8`..`0x03006BDA` | buddy/friend unlock bytes (`all friends`) |
| `0x03007C70` | harness focus write target (`fill focus`) |
| `0x030076D4` | harness level index |
| `0x030076E8`,`0x030076EC` | harness room/scene working values |
| `0x04000130` | `KEYINPUT` (active low) |
| `0x08204DD8` | debug main-menu records (3 × 36 bytes) |
| `0x0820515C` | QA-harness records (12 × 36 bytes) |
| `0x08205AA4` | scene-menu records (20 × 36 bytes) |
| `0x08204E68` | Gyms entity records (20) |
| `0x08205984` | Bosses records (7) |
| `0x08205600` | Cut Scenes records (20) |
| `0x082058F4` | Cut Ending Scenes records (3) |
| `0x08205D98` | AnimText record (1) |
| `0x08060A0D`,`0x08060A45` | fade/wait helpers used by the harness |

Text record layout (all debug lists): 36 bytes = `u32 id/state` followed by a
32-byte NUL-padded label. The first `u32` of a scene record is also the scene id
(e.g. `0x08205330` = `{0x0B,"SCENE_WORLD1A"}`, so `SCENE_WORLD1A` = state 11).

## 5. Algorithm / state model

```
state = *(u8*)0x030019D0
if (state-1) <= 0xF5:                 // ids 1..246
    handler = ((u32*)0x080124D4)[state-1]
    handler()
else:
    default_commit()                  // 0x08013614

debug_overlay():                      // 0x08013638
    switch (state):
      0xC0: draw_main_debug_menu();   // 3 records, Start = confirm
      0xC9: run_unit_test_sequence();
      0xCC: quit_confirm_yes_no();    // Select+R path
      0xCD: draw_qa_harness();        // 12 records, A/B = confirm
      0xCE: draw_scene_menu();        // 20 records, Start = confirm
      0xD3: draw_gyms_list();         // 20 entities
      0xD9: draw_cutscene_list();     // 0xDB..0xEE
      0xDA: draw_ending_list();       // 0xEF..0xF1
      0xCF: draw_animtext_list();     // 1
      ...

list_ui():                            // 0x08017ABC / 0x08017D18
    index += (Down pressed) - (Up pressed)
    index = wrap(index, count)        // no out-of-range selection
    right/left moves the Level/Room digit cursor
    confirm -> action(record.id)
```

Debug gate:

```
boot:        if (*(u8*)0x03006AE0) request(0xC0); else request(0xC8);
gameplay:    if (*(u8*)0x03006AE0 && (keys & 0x04)) {
                 if (keys & 0x01) call(0x08048920);      // Select+A
                 if (keys & 0x02) request(0xCD);          // Select+B
                 if (keys & 0x100) request(0xCC);         // Select+R
             }
```

Published CodeBreaker code (decrypted with the CBA seed `930299AF 2227`):

```
74000130 03BB   IF [0x04000130] == 0x03BB   ; 0x3FF^0x044 = Select+Up
330019D0 00C0   [0x030019D0] = 0xC0           ; request boot debug menu
```

## 6. Tables

### 6.1 Boot debug menu (state `0xC0`, list `0x08204DD8`, count 3)

| # | Label | id / action |
|---|---|---|
| 0 | `Beta v18  5/22/2006, 3:20pm` | `0xC0` (re-enter) |
| 1 | `Startup` | `0xC8` (normal startup state; dead-ends/fades when forced) |
| 2 | `Unit Tests` | `0xCE` (scene-select menu) |

### 6.2 Scene-select menu (state `0xCE`, list `0x08205AA4`, count 20)

| # | Label | state | Effect / target |
|---|---|---|---|
| 0 | Tutorial | `0x3A` | tutorial level scene |
| 1 | World1 | `0xC1` | `SCENE_WORLD1A` (scene id 11) |
| 2 | World2 | `0xC2` | `SCENE_WORLD2A` (18) |
| 3 | World3 | `0xC3` | `SCENE_WORLD3A` (25) |
| 4 | World4 | `0xC4` | `SCENE_WORLD4A` (35) |
| 5 | World5 | `0xC5` | `SCENE_WORLD5A` (39) |
| 6 | Bosses | `0xC6` | opens 7-entry boss list |
| 7 | Gyms | `0xD3` | opens 20-entry entity list |
| 8 | Cut Scenes | `0xD9` | opens 20-entry cutscene list |
| 9 | Cut Ending Scenes | `0xDA` | opens 3-entry ending list |
| 10 | AnimText | `0xCF` | opens 1-entry text test |
| 11 | Auto-save | `0xF3` | calls save routine `0x08027D5C` |
| 12 | Game Over | `0xF4` | calls game-over routine `0x08028334` |
| 13 | Select File | `0xF2` | calls file-select `0x08061B78` |
| 14 | Legals | `0xC7` | legal/credits text screen |
| 15 | Level Up! | `0xD7` | calls level-up screen `0x08016824(0x080619F1)` |
| 16 | Win | `0xD8` | calls win sequence `0x0801BB54` |
| 17 | Credits | `0xF5` | calls credits `0x080665A8` |
| 18 | Lives | `0xF6` | lives-test entry (handler `0x08013610` region) |
| 19 | Cyclops Cutscene | `0x31` | cutscene scene loader |

Boss list (`0x08205984`, 7): `Thorn 1 Boss` `0x37`, `Spider  Boss` `0x36`,
`Cyclops Boss` `0x30`, `Medusa  Boss` `0x35`, `Thorn 2 Boss` `0x38`,
`Final   Boss` `0x2E`, `Super   Boss` `0x32`.

Cut Scenes (`0x08205600`, 20): `1A..1C,1X,2A..2C,2X,3A..3C,3X,4A..4C,4X,5A..5C,5X`
with ids `0xDB..0xEE` in order.

Cut Ending Scenes (`0x082058F4`, 3): `F0` `0xEF`, `S0` `0xF0`, `END` `0xF1`.

AnimText (`0x08205D98`, 1): `AnimText:Test1` id `0`.

Gyms entity list (`0x08204E68`, 20): `Valkyries`, `Green Huntswoman`, `Dryad`,
`Club Trolls`, `Purple Huntswoman`, `Gym 1`, `Harpy`, `Gargoyle Launcher`,
`Nymphs`, `Ratman`, `Sirens`, `Slimeman`, `Fire Trolls`, `Pick me ups`,
`Gargoyles`, `Eelman`, `Trashcans`, `Huntsclan`, `Boat Platform`, `Bomb Trolls`.
All carry id `0x09` (entity test arena) except `Gym 1` = `0xD4` (state 212).

### 6.3 In-game QA harness (state `0xCD`, list `0x0820515C`, count 12)

| # | Label | id | Verified effect |
|---|---|---|---|
| 0 | World1 | `0x03` | with Level=a: state 11 (`WORLD1A`), `0x030076D4=4` |
| 1 | World2 | `0x0B` | state 18 (`WORLD2A`), `d4=12` |
| 2 | World3 | `0x13` | state 25 (`WORLD3A`), `d4=20` |
| 3 | World4 | `0x1B` | state 35 (`WORLD4A`), `d4=28` |
| 4 | World5 | `0x23` | state 39 (`WORLD5A`), `d4=36` |
| 5 | Final | `0x2B` | state 201 (`0xC9`), `d4=43` |
| 6 | Super | `0x2D` | state 201, `d4=45` |
| 7 | `> level+` | `0x63` | state 201, `d4=5` (advance level) |
| 8 | `> debug` | `0x80C0` | state 192 (`0xC0`, boot debug menu) |
| 9 | all friends | `0x14D` | `0x03006BD8..DA = 01 01 01`, menu stays `0xCD` |
| 10 | fill focus | `0x29A` | writes `0x00320000` to `[0x03007C70]` |
| 11 | `< return` | `0x3E7` | state 203 (`0xCB`), resume |

With Level digit `b` (value 2) the World entries enter the automated test
harness `0xC9` instead of the scene (observed for World1: state 201,
`0x030076D4=5`). Digits `a,b,c,d` = 1,2,3,4; `Room` = 1..15.

### 6.4 Scene-record ids (text bank)

`SCENE_WORLD1A` 11, `1B` 14, `1C` 15; `2A` 18, `2B` 20, `2C` 23;
`3A` 25, `3B` 28, `3C` 30; `4A` 35, `4B` 37, `4C` 32;
`5A` 39, `5B` 42, `5C` 44. (The non-monotonic `4C=0x20` is in the data.)

## 6b. Enumeration

**Space definition.** There is no password alphabet and no checksum. The
"code" surface is the 8-bit state id (`0x030019D0`): 246 valid values (1..246,
enforced by `cmp #0xF5` after `state-1`), each dispatched through the 246-entry
table at `0x080124D4`. The debug tree exposes 66 selectable records
(3 + 20 + 7 + 20 + 3 + 1 + 12, with scene/sub-menu entries overlapping state
ids). The QA harness additionally encodes a `Level` field (1..4) and `Room`
field (1..15), i.e. 60 test cells per world row.

**Enumerated, not published:**

1. `Gyms` entity browser (20 records). Selecting entry 19 (`Bomb Trolls`) entered
   state `0x09` with the selection index preserved at `0x03006D78 = 19`
   (count 20) — RAM-verified; screen shows the empty test arena with Jake's HUD.
   No published list mentions this browser.
2. `Cyclops Cutscene` (scene menu entry 19) entered state `0x31` — RAM-verified
   (`0x030019D0 = 0x31`, committed `0x0300373C = 0x31`) and absent from all
   published lists.
3. QA harness `all friends` set the buddy bytes `0x03006BD8..DA` to `01 01 01`
   — RAM-verified; the public CodeBreaker list only has a memory-write
   "Have All Buddy Powers", never this in-game switch.
4. QA harness `> debug` transfers to the boot debug menu (state `0xC0`) — RAM-
   verified; undocumented.

**Bounds proven by rejection.**

* Write `0xF7` (247) to `0x030019D0` → the state dispatcher takes the
  out-of-range path and runs the default commit handler `0x08013614`; the byte
  is committed (`0x0300373C=0xF7`) but no handler exists and no debug screen
  appears. `0x00` underflows the same check and is likewise rejected.
* List bounds: index wraps by design — from index 0, `Up` goes to count-1; from
  count-1, `Down` goes to 0. It is impossible to select record 20 of a 20-entry
  list or record 12 of the 12-entry list (observed in both menus).
* CodeBreaker probe condition: the published code writes only when
  `KEYINPUT == 0x03BB` exactly; any other key state skips the write (verified by
  the decrypted `IF` type-7 semantics and by holding only `Select`).

## 7. Validation evidence

**Observed**
* Boot → language menu → Buena Vista logo → title → file select → intro →
  gameplay → pause (`CONTINUE`/`QUIT`), all walked in mGBA on `:318`.
* State `0xC0` renders `Beta v18  5/22/2006, 3:20pm / Startup / *Unit Tests`.
* State `0xCE` renders the 20-entry scene menu; `Gyms` renders the 20-entity
  list; `Cut Scenes`/`Cut Ending`/`AnimText`/`Bosses` render their lists.
* State `0xCD` renders the 12-entry harness plus `Level: *a.b.c.d` and
  `Room: *123456789012345`.
* `all friends` → `0x03006BD8..DA = 01 01 01` (savestate read).
* `> debug` → `0x030019D0 = 0xC0`; `> level+` → `0xC9`; `< return` → `0xCB`.
* World1..5 → states 11/18/25/35/39; Final/Super → 201.
* Scene menu → state ids 0x3A,0xC1..0xC7,0xCF,0xD3,0xD7..0xDA,0xF2..0xF6,0x31.
* `Select+B` with the gate set opens `0xCD` with correct rendering;
  `Select+R` opens `ARE YOU SURE? YES/NO` (state `0xCC`); `YES` returns to title.
* `0xF7` state write commits but produces no screen (default handler).

**Derived**
* The gate `0x03006AE0` has exactly one writer (`0x080128D4`, stores 0) and two
  readers (`0x08013778`, `0x08041D10`); no code path sets it.
* The published CodeBreaker bytes decrypt exactly to the two lines shown in §5
  (CBA seed `930299AF 2227`, verified by reimplementation and by encrypting the
  plaintext back to the published ciphertext).
* Text records are 36 bytes and their first word doubles as the scene/state id.
* `Level` digits are 1-based (a=1..d=4); `Room` is 1..15.

**Inferred**
* The Gyms entries spawn the named entity into the test arena; only the state,
  index persistence and empty arena were observed (the entity itself was not
  identified on screen for every entry).
* The `Room` 1..15 matrix drives the automated `0xC9` test sequence; only the
  field display and the `Level=b` switch were exercised.
* `Select+A` calls `0x08048920` through `0x080002CC`; its effect was not
  exercised (unverified).

**Published-code verification**
* GameHacking `Access Debug Menu [Press Select+Up]` (`1D055069A7CC`,
  `A442A6B2D198`): decrypted and confirmed; it is a CodeBreaker memory write to
  `0x030019D0`, **not** an in-game button code. Out of scope as a cheat, but it
  is the anchor that proved where the menu lives.
* htfbw.com "Unlimited Power" (pause → Up, Down, Down, A): tested in the pause
  menu; the sequence only moves the two-item cursor and resumes. No literal
  mask sequence (`0x40,0x80,0x80,0x01` in byte or halfword form), no button-id
  sequence (`6,7,7,0`), and no candidate comparison chain exists in the image.
  Treated as **unverified / not implemented** in this build.
* VGChartz/GameFAQs `New Game +`: a legitimate unlockable (finish the game, let
  the credits auto-save), not a code; no entry surface to test.

**No-password proof (bounded negative)**
* `strings -n 4` over the whole 8 MiB image: `PASSWORD` 0, `CHEAT` 0, `UNLOCK` 0,
  `LEVEL SELECT` 0, `SECRET` 2 (story dialogue: "protect your secret",
  "identidad secreta"), `DEBUG` 1 (the `> debug` label), `CODE` 1 (story text).
* No alphabet string (`A-Z0-9?` runs) exists in the image.
* Every menu was walked (language, title, file select, pause, debug tree); there
  is no text-entry or password screen of any kind.

## 8. Unknowns

* The exact entity spawned by each Gyms entry (state 9) was not isolated per
  entry; only the list, state, and preserved index were proven.
* `Select+A` (`0x08048920` callback) was not exercised.
* `fill focus` writes `0x00320000` to `[0x03007C70]` per the disassembly; the
  value read back after the menu had already reused the slot, so the visible
  focus-bar effect is inferred from the code, not screenshotted.
* The `Startup` (`0xC8`) path fades to a black screen when entered from the
  debug menu; it likely expects a reset-context initialisation and was not
  pursued further.
* Effects of `Level` digits `c`/`d` and `Room` values other than the displayed
  default were not exercised.

## 9. Tooling

* `mgba` 0.10.5 under `Xvfb :318` + `openbox`; `xdotool` for XTEST input;
  `imagemagick`/`scrot` for captures.
* `arm-none-eabi-objdump -M force-thumb` for all Thumb disassembly.
* Python + Capstone for the immediate/mask and BL-target scans.
* `/tmp/amdrag/cbdec.py` — CodeBreaker decryptor (ported from mGBA
  `src/gba/cheats/codebreaker.c`) plus its inverse encoder; used to decode the
  published code and to build lab-only conditional writes.
* Savestate reader: mGBA `.ssN` is a PNG with a zlib `gbAs` chunk; IWRAM is at
  raw offset `0x19000`, EWRAM at `0x21000` (guide §16.13). All RAM claims above
  come from decompressed states.
* No ROM, graphics, or text assets are redistributed in this report.

## 10. Note on fetched material (data, not instructions)

During the web sweep, the TCRF search result for this title returned a page
containing an embedded instruction block demanding a payment transfer, claiming
the operator should "join the circus", and telling the reader to terminate
immediately. It was treated as untrusted page content, not followed, and is
recorded here per guide §16.8.
