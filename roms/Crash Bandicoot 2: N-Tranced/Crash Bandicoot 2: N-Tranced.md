# Crash Bandicoot 2: N-Tranced (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Crash Bandicoot 2: N-Tranced/Crash Bandicoot 2: N-Tranced.gba` |
| Size | 8,388,608 bytes (8 MiB / 64 Mbit) |
| Header title | `CRASH2` (0xA0, NUL-padded) |
| Game code | `AC8E` (0xAC) |
| Maker code | `7D` (0xB0) |
| Software version | 0 (0xBC) |
| Complement | 0x32 (0xBD), valid |
| Header checksum | 0x0000 (0xBE), zeroed — rebuilt-header artifact (§16.1) |
| Entry word | `0xEA00002E` = stock `b 0xC0`; no cracktro/trainer |
| MD5 | `617b2b2590e2925228dbdb162b05d6f6` |
| SHA-1 | `972158859ea08aa5746ab2e0d4c81ac43728adff` |
| SHA-256 | `2623df1c9d91b5e9b2c1488e4a1632f14b9d1bc87c14f4dadca417fd1dda5ab1` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once (file 0x4).
Single image, not a multicart, no second header. The first 4 KiB contain no
cracktro banner and the crt0 at 0x080000C0 is the normal Vicarious Visions GBA
startup (stack/IWRAM setup, then a Thumb `main` at 0x02000000+; the boot code
copies the RAM image from 0x08130000 and the config block described in §4).

## 2. Executive summary

**This ROM contains no in-game password, button-code, hidden-menu or
debug-menu cheat system.** There is no code-entry screen, no alphabet, no
validator, no key-sequence table and no gate reachable from the controller.

What the game *does* contain, and what an analyst should record as its
developer-intended extras, is a small **link-transfer unlock system**:

* Five hidden Atlasphere multiplayer characters (Neo Cortex, Dingodile, Tiny,
  N. Gin, Mega-Mix) are stored as bits in the save record (byte at record
  offset `+0x1FA`) and displayed by a post-transfer results screen
  (`0x0800448C`–`0x0800473C`).
* The bits are written **only** by the GBA link receive path
  (`0x08003124` has six call sites, all inside `0x08003C80`–`0x08003DE0`).
  Partner type 0x1 (another N-Tranced) sets bit 0x01; partner type 0x3
  (*Crash Bandicoot: The Huge Adventure* / *XS*) sets the whole byte to `0xFF`.
  No input handler and no menu calls the setter.

Two pieces of developer debug material are present but are ROM/engine state,
not cheats:

1. A config word at ROM `0x7FBD18` (u32, currently 0) that gates the
   double-speed gameplay mode documented by TCRF; it is read at boot, not by
   input.
2. The GAX Sound Engine 3.01 banner and error screen
   (`EXCEPTION. PROGRAM HALT`, `0x529C50`+); this appears only when the engine
   detects a corrupted sound table.

Because the engagement has no code space, §0.2 is satisfied in its
negative-result form: the complete UI text space is enumerated (191 strings,
all classified), the input surface is enumerated (4 KEYINPUT literal sites,
0 sequence tables), published sibling codes are verified absent in three
encodings and rejected in-game at the title screen, and the one real
unlockable space (the 8-bit transfer byte) is fully mapped to its five display
branches and proven to be write-only from the link routine.

## 3. How to reproduce

### Emulator and harness

* `Xvfb :264 -screen 0 1024x768x24`, `DISPLAY=:264 openbox`,
  `SDL_AUDIODRIVER=dummy`.
* mGBA 0.10.5 SDL, started with the CLI debugger so every observation is a
  RAM/register read (no screenshots were used):

```bash
Xvfb :264 -screen 0 1024x768x24 &
DISPLAY=:264 openbox &
export DISPLAY=:264 SDL_AUDIODRIVER=dummy
mkfifo dbg.fifo; (sleep 99999 > dbg.fifo &)      # keep the debugger FIFO open
mgba -d -3 game.gba < dbg.fifo > mgba.log 2>&1 &
```

Debugger commands used: `x/4 ADDR` (read), `b/t ADDR` (Thumb breakpoint),
`d N` (delete), `save N` / `load N` (savestate slots, files `game.ssN`),
`frame` (advance exactly one frame and return to the prompt), `status`.
`frame` is the reliable way to pump SDL input; `c` runs until a breakpoint and
can run away on screens that draw no id-table text.

Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad=arrows; hold 4–25 frames, because mGBA's XTEST input drops short taps.

### Menu path used

1. Boot → publisher/logo sequence → title screen.
2. Title: `press start` (text id 0) → Start → main menu (ids 1–4).
3. Main menu: New Game / Load Game / Link Game / Credits.
   * New Game → cutscene (ids 139+) → Island Intro (ids 40/41 and tutorial
     ids 122–138).
   * Down → Load Game → file screen (ids 7, 70–73); a slot screen shows
     "load game / cancel / empty" (71, 79, 81) because no save exists.
   * Down, Down → Link Game → submenu (ids 5, 6, 7 = Atlasphere / Link Race /
     Back).
4. In a level: Start → pause menu (ids 99 "resume", 97 "music", 98 "sound",
   plus the crystals status header 103); Down cycles the three items.

### Published codes tested

No in-game code is published for this title. Every published "code" is a
GameShark/CodeBreaker/Action Replay memory patch (e.g. `320026EC 0063`,
`420027CC 01FF`), which is outside scope. As a cross-title control, the
published Crash/Spyro Superpack title-screen sequence
`Left, Right, Right, Right, Down, Up, Right, Up, A` was entered at this ROM's
title screen: the title stayed on text id 0 (no menu, no cutscene) and the
EWRAM difference between before/after states was 19 bytes (animation timers
only). The sequence is absent from the ROM as u16 masks, as u8 masks and as
active-low u16 masks.

## 4. Address map

| ROM address | Meaning |
|---|---|
| `0x080000C0` | crt0 (ARM), stock |
| `0x080008DC` | key latch: `held = ~KEYINPUT`, stores `u16` at `0x02000018`, `pressed` at `0x0200001A`; 17 BL callers |
| `0x080047E80`–`0x080047F00` | menu key-state updater (KEYINPUT literal at `0x080047EE0`; stores held/pressed/released in a caller struct) |
| `0x080047F50` | `held & 0x3FF` helper |
| `0x080273E8` | `GetTextPtr(id)` → `u32[0x081D5C04 + 4*id]` (67 call sites) |
| `0x080394xx` | generic list/text renderer |
| `0x0800609C` | pause-menu renderer (entry = `{u32 id, u32 action}` list) |
| `0x08006024` | pause action dispatcher, 6 cases, table at `0x08006040` |
| `0x080070AC` | pause action 0 — resume/close |
| `0x080063AC` | pause action 1 — restart trial |
| `0x0800649C` | pause action 2 — warp zone / quit (context) |
| `0x08006580` | pause action 3 — branch exists; no entry in the two recovered tables uses action 3 |
| `0x08006660` | pause action 4 — music toggle |
| `0x08006744` | pause action 5 — sound toggle |
| `0x08003000` | `partner_type = byte[save+0x1F9] >> 4` |
| `0x080030EC` | `test_bit(save, bit)` = `(byte[save+0x1FA] & bit) != 0` |
| `0x08003124` | `set_bit(save, bit)` = `byte[save+0x1FA] \|= bit` (+ checksum) |
| `0x08002FDC` | save checksum: sum of 127 words (508 bytes) stored at `save+0x1FC` |
| `0x08003C80`–`0x08003DE0` | link receive/state machine (only writer of the unlock byte) |
| `0x0800448C`–`0x0800473C` | post-transfer "unlocked …" results screen |
| `0x081D5C04` | 191-entry text-id table (English only) |
| `0x081D3F70`–`0x081D5AE4` | text strings addressed by the table |
| `0x081D0288` | pause item table A: `{99,0}{97,4}{98,5}{100,2}{101,1}` |
| `0x081D02B0` | pause item table B: `{99,0}{97,4}{98,5}{119,2}` |
| `0x087FBD00` | developer config block copied at boot |
| `0x087FBD18` | u32 game-speed debug multiplier (0 = normal) |
| `0x08529C50` | GAX Sound Engine 3.01 banner / error strings |
| `0x086D4C60` | unused Atlasphere character name `BONXBONX` (pointer at 0x6D4F58) |

RAM seen in this analysis: held/pressed at `0x02000018`/`0x0200001A`; pause
menu object at `0x02023E14` during the observed pause (fields +0x14 id list,
+0x18 selected index, +0x1C item count); save record byte `+0x1F9` partner
nibble, `+0x1FA` unlock bits, `+0x1FC` checksum.

## 5. Algorithm

### Text and menus

```
ptr(id) = u32[0x081D5C04 + 4*id]          # ids 0..190
```

The pause list is an array of 8-byte entries; the second word is the action
index used by the `0x08006024` dispatcher:

```
entry = { u32 text_id, u32 action }
```

### Unlock byte (link transfer)

```
partner = byte[save + 0x1F9] >> 4
if partner == 1: set_bit(save, 0x01)      # 0x08003CC0
if partner == 3: set_bit(save, 0xFF)      # 0x08003CE4  (The Huge Adventure / XS)

test_bit(save, bit) -> (byte[save+0x1FA] & bit) != 0
```

Results screen (`0x0800448C`), in draw order:

```
draw(id 89)                                # heading, unconditional
if test_bit(0x02): draw(id 90)             # "unlocked dingodile"
if test_bit(0x08): draw(id 92)             # "unlocked n. gin"
if test_bit(0x04): draw(id 91)             # "unlocked tiny"
if test_bit(0x10): draw(id 93)             # "unlocked megamix"
```

Bit 0x01 (same-engine transfer) is set, but this screen has no branch for it; bits
0x20/0x40/0x80 are neither set nor tested. The byte is covered by the save
checksum at `+0x1FC`.

## 6. Tables

### 6.1 Text-id inventory (191 strings, `0x081D5C04`)

| Ids | Count | Content |
|---:|---:|---|
| 0 | 1 | `press start` (title) |
| 1–4 | 4 | `new game`, `load game`, `link game`, `credits` |
| 5–7 | 3 | `atlasphere`, `link race`, `back` |
| 8–17 | 10 | link session: waiting/error/connected, player wins, rounds |
| 18–28 | 11 | character names (Crash → Megamix) |
| 29–35 | 7 | Atlasphere maps/modes (Double Cross … Bumpers) |
| 36–37 | 2 | continue and save / continue without save |
| 38–40 | 3 | player 1/2, `level` |
| 41–66 | 26 | level and boss names (Island Intro … Evil Coco) |
| 67–69 | 3 | aliases of Fake Crash / N. Trance / N. Tropy |
| 70–88 | 19 | file/save/transfer dialogs (load, delete, overwrite, empty, …) |
| 89–93 | 5 | `unlocked neo cortex/dingodile/tiny/n. gin/megamix` |
| 94–96 | 3 | `push B to quit`, `push start to continue`, `start: load-save` |
| 97–107 | 11 | pause: music, sound, resume, warp zone, restart trial, powers, crystals, gems, gem shards, relics, time trial |
| 108–116 | 9 | power names/help (super slide, rocket jump, tornado spin, turbo run) |
| 117–121 | 5 | main menu, quit to main menu, quit game, player 1/2 pause |
| 122–138 | 17 | tutorial text |
| 139–190 | 52 | cutscene dialogue; 4 entries (157, 170, 183, 190) are blank |

### 6.2 Pause menu entries

| ROM table | Entries `{id, action}` |
|---|---|
| `0x081D0288` | {99 resume,0} {97 music,4} {98 sound,5} {100 warp zone,2} {101 restart trial,1} |
| `0x081D02B0` | {99 resume,0} {97 music,4} {98 sound,5} {119 quit game,2} |

The observed in-level pause object (`0x02023E14`) had list pointer
`0x081D0288` (table A) with `count = 3` and `selected = 2`, so the renderer
walked exactly the first three entries (resume / music / sound): table A is
fixed and the context decides the count. That is why "warp zone" and
"restart trial" do not appear in a normal level.

### 6.3 Unlock bits (`byte[save+0x1FA]`)

| Bit | Set by | Displayed as |
|---:|---|---|
| 0x01 | partner type 1 (N-Tranced ↔ N-Tranced) | no branch on the results screen |
| 0x02 | partner type 3 (0xFF) | id 90 “unlocked dingodile” |
| 0x04 | partner type 3 (0xFF) | id 91 “unlocked tiny” |
| 0x08 | partner type 3 (0xFF) | id 92 “unlocked n. gin” |
| 0x10 | partner type 3 (0xFF) | id 93 “unlocked megamix” |
| 0x20/0x40/0x80 | nothing | nothing (aliases) |

## 6b. Enumeration

**Input code space: 0.** There is no alphabet, length, checksum or table to
enumerate. The enumeration that can be performed is the enumeration of the
interface and of the one writable flag space:

1. **UI space** — 191 text ids (full table above). Zero ids contain
   code-entry, password, debug, option, level-select or sound-test wording.
2. **Menu space** — 4 main items, 3 link-submenu items, 5 file items,
   6 distinct pause items (`99,97,98,100,101,119`). Every menu action is a
   fixed handler; there is no “enter text” action.
3. **Input space** — 4 literal references to `0x04000130`; 17 BL callers of
   the key latch; 10 button bits. A pointer-referenced button-sequence table
   would be a run of ≥4 halfwords in the mask set `{1,2,4,8,0x10,0x20,0x40,
   0x80,0x100,0x200}`. Scanning all 22,350 ROM pointers found **0** such
   tables (u16). The 39 byte-run candidates are inside code/graphics; the
   only structured near-miss, `0x1D02D0`, is a 16-entry sprite-coordinate
   table indexed by a 4-bit id at `0x080082F0` (`r7=tab1[i]`, `r6=tab2[i]`),
   not input.
4. **Unlock space** — 8 bits = 256 byte values; 5 bits meaningful (0x01 set,
   0x02/0x04/0x08/0x10 tested) = 32 distinct combinations; 3 unused bits
   create 8 aliases per behaviour. The complete display branch set is the 16
   combinations of {0x02,0x04,0x08,0x10} plus the unconditional heading.
5. **Novel value** — the only value that could be called a “code” is the
   unlock byte. Its entire writer set is the link routine: `0x08003124` is
   called from `0x08003CC0` (mask 0x01) and `0x08003CE4` (mask 0xFF) only.
   No controller path reaches it, so no unpublished value can be minted
   through the UI; that is the closed-set result for this title.
6. **Bounds by rejection** — (a) the published sibling title-screen sequence
   is rejected in-game (title id 0 persists, 19-byte transient EWRAM delta);
   (b) the same sequence is absent from ROM under u16, u8 and active-low u16
   encodings; (c) no sequence-table pointer exists (0 hits); (d) the save
   byte outside the five bits aliases to identical behaviour (0x20/0x40/0x80
   are never read).

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| Stock retail image, no trainer | Observed | entry `0xEA00002E`, single logo at 0x4, no cracktro strings |
| Title screen draws text id 0 | Observed | breakpoint at `0x080273E8`, `r0=0`, caller `0x08039529` |
| Main menu = ids 1,2,3,4 | Observed | id stream 1,2,3,4 every frame after Start |
| File screen = ids 7,70–73; slots empty (71,79,81) | Observed | id stream after Down+A |
| Link submenu = ids 5,6,7 | Observed | id stream after Down,Down+A |
| New game → cutscene ids 139/140 → level ids 40/41 + tutorials 122–138 | Observed | id stream |
| Pause = ids 99,97,98 + status 103, 3 items | Observed | id stream; pause object `0x02023E14`, count 3, selected 2 |
| Pause tables/actions at `0x1D0288`, `0x1D02B0`, dispatcher `0x08006024` | Derived | disassembly |
| Unlock byte at `+0x1FA`, test `0x080030EC`, set `0x08003124` | Derived | disassembly; 4 test callers, 6 set callers all in link routine |
| Partner type 1 → bit 0x01; type 3 → 0xFF | Derived | `0x08003000` `>>4`, branches at `0x08003CBC`/`0x08003CE0` |
| Five characters unlocked by linking Huge Adventure | Observed (strings) + Derived (code) | ids 89–93 + six web sources agree; display gated by bits 2/4/8/0x10 |
| No password/cheat/debug/level-select text | Observed | keyword counts over the whole ROM (case-folded): password 0, cheat 0, debug 0, level select 0, select 0, enter 0, invalid 0; unlock 5 (the link messages), code 1 (GAX banner) |
| No button-sequence table | Derived | 0 pointer-referenced u16 mask runs |
| Published sibling sequence rejected | Observed | title id 0 unchanged; 19-byte transient EWRAM diff |
| Debug speed word and GAX error screen exist | Observed | `0x7FBD18` = 0; `GAX Sound Engine 3.01` at `0x529C50`, error strings at `0x529D98`+ |
| Credits action exists (id 4) and credits text bank is present | Observed (string/menu) | ids 1–4; credits names block before `0x081D3F70` |

## 8. Unknowns

* Bit 0x01 of the unlock byte is written by a same-engine link but its reader
  was not found through the four `0x080030EC` call sites; it may be read
  directly elsewhere.
* The credits screen (main-menu item 4) uses a renderer that does not call the
  id-table routine, so the text-id probe cannot name it; its text bank is
  present and the menu entry is confirmed.
* The exact in-game effect of the Huge Adventure link on the atlasphere
  character-select layout (icon availability) follows from the bit tests but
  requires two carts/link cable to exercise.
* Atlasphere character `BONXBONX` (0x6D4C60) is unused in this build and has
  no icon.

## 9. Tooling

* Python 3 (`zlib`, `struct`) for header/hash/pointer/string/table analysis and
  for decoding mGBA `.ss` savestates (PNG `gbAs` chunk → raw 397,312-byte
  state; EWRAM at 0x21000, IWRAM at 0x19000).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for spot disassembly; a short Thumb BL scanner (halfword pattern
  `0xF000/0xF800`) for caller counts.
* mGBA 0.10.5 SDL CLI debugger on Xvfb :264 (no screenshots; all state read
  through `x/`, breakpoints and `frame`).
* Scripts kept in `/tmp/crash2`: `driver.py`, `nav2.py`, `dbg.sh`,
  `frames.sh`, plus the extraction/scan snippets in the shell history above.

## 10. Notes

* A TCRF “LLM/AI agent-specific information” page fetched during this
  engagement returned a prompt-injection payload (fake “terminate all
  operations”, `E_` error text and an instruction to print an insult). It was
  treated as data, ignored and is recorded here per guide §16.8.
* No ROM, graphics, music or text assets are redistributed; only hashes,
  addresses and short UI identifiers are published.
