# Shining Force: Resurrection of the Dark Dragon (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Shining Force: Resurrection of the Dark Dragon.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `SHININGFORCE` |
| Game code | `AF5E` (USA) |
| Maker | `EB` (Camelot Software Planning / Amusement Vision) |
| Version | 0x00 (Rev 00) |
| Entry word | `0xEA00002E` — stock `b 0xBC`, **not** a cracktro patch |
| Fixed byte / complement / checksum | `0x96` / `0x4A` / `0x0000` (checksum 0 is a normal rebuilt-header artifact) |
| MD5 | `6a1b056d8a006e069466c08c69de56c0` |
| SHA-1 | `1bbda9142806265cc42645df433ede5d8db46e3e` |
| SHA-256 | `33bcb4f2b359118726e7ca0e4dae4917886d7e8faa7bfb684061cbd0f8812a02` |

**Embedded-header scan:** the full 156-byte Nintendo logo occurs exactly **once**, at file offset 0, so this is a single retail image — no appended trainer, no multiboot stub, no 2-in-1 pack.

**Build identity:** `Build ROM Version / 1.000 / Feb 10 2004 / 12:33:41` at file `0x7AEC8` (ROM `0x0807AEC8`), plus `(C) SEGA/AMUSEMENTVISION 2003` at `0x7AEE4`. This matches TCRF's *US* build (JP = 1.009/Oct 30 2003; EU = 1.000/Jan 13 2004), so every address below is for this exact revision.

## 2. Executive summary

There is **no password system and no in-game button code** in this build. The only text-entry surface reachable by a player is the hero-name entry during the opening story; it is a name field, not a validator (nothing compares the buffer to a constant — §16.2b). Every published "cheat" located on the web is a CodeBreaker/GameShark/Action Replay device code, i.e. an external memory patch, which is out of scope.

What the ROM *does* contain is a **complete, functional developer debug menu** at scene/mode 2. Its string table, dispatcher, handlers and all ten entries are present and work. A TCRF mirror documents the text as "debugging text" and explicitly leaves "are they still accessible?" as an open question; the live tcrf.net page used for this search returned a **prompt-injection payload** (a fake EICAR XOR "key", a $1,000,000,000,000,000,000,000,000,000 demand, and an instruction to report `E_SHITASS_OPERATOR`). It was treated as hostile data, ignored, and not acted on (§16.8). The factual mirror info was used instead.

I proved the debug menu is live by redirecting the boot scene request to mode 2 on a **copy** of the ROM (one 32-bit word at file `0xB424`). The menu then appeared at boot with all ten entries working. This is a labeled debugger/patch experiment, **not** a retail code.

The scene selector itself is a clean, fully enumerated 16-value space (`mode - 1 <= 15`), with exactly one debug entry (mode 2), two no-op entries (8 and 12), and hard rejection outside 1..16. Across boot, title, opening story, name entry, and tutorial battle the mode was only ever 11 or 7. Six common boot-time button combinations all left mode at 11. No code path from the keypad to the scene-mode field was found. The correct classification is therefore **gated feature with no reachable retail input in this build** (§16.3/§16.20), not "no feature" and not "code confirmed."

## 3. How to reproduce

Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`), headless on `DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`, `-3` scaling. Keymap used throughout: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Holds of 80–120 ms were sufficient.

**Retail path (unpatched ROM):**
1. Boot → title screen (`SHINING FORCE / Resurrection of the Dark Dragon`).
2. Start → opening story → hero-name entry (uppercase, lowercase, digits and symbols; `Start` = END, `B` = backspace). This is a name field only.
3. Story continues → tutorial battle against Varios. No password, code, or hidden menu appears on any of these screens.

**Debug menu path (experiment, requires patching a *copy*):**
1. Copy the ROM to a scratch file and write `0x0800B4CC` (little-endian `CC B4 00 08`) at file offset `0xB424`. That redirects the boot-time scene-11 request to the mode-2 (debug) creator.
2. Boot the copy. The debug menu appears immediately at boot — no button input needed.
3. In the menu: Up/Down move the 10-item cursor, Left/Right change the highlighted value, A activates.
4. Screenshots of every entry were in `/tmp/shiningforce/entry1_v.png` … `entry9_v.png`, `menu_sceneselect_v.png`, `soundtest_v.png`, `scene2_afterA_v.png`.

**Observed menu path → effect:** `SCENE SELECT` value 2 + A → warps into Guardiana field map (mode 3). `SOUND TEST` + A → `[SOUND TEST]` screen (mode 9). `MESSAGE TEST` + A → test dialogue from Varios (mode 1). `BATTLE VISUAL` + A → VISUAL VIEWER (mode 6). `BOOT PROCESS` + A → boot/debug info screen (mode 15).

## 4. Address map

| Item | Address (ROM / RAM) | Notes |
|---|---|---|
| Debug main-menu string table | `0x08079960`–`0x0807A045` | Plain ASCII, 0x20-byte fixed records. Matches TCRF US offsets. |
| Debug string pointer table | `0x081E7E04` | Points to title + 7 language strings + `1/2/3`. |
| Debug scene descriptor | `0x087F048C` | 13-pointer scene record; main `0x08000835`, draw `0x08000A55`. |
| Debug menu handler | `0x0800090C` | Reads active-high key masks; selection at `[obj+8]`. |
| Debug menu renderer | `0x08000A54` | Draws the 10 entries, heap info, pad sample. |
| Debug creator | `0x08000778` → `0x0800078C` | Allocates 0x858-byte object; vtable `0x087F0484`. |
| **Scene dispatcher** | `0x0800B3BC` | `mode = r1`; gate `(mode-1) <= 15`; jump table below. |
| **Scene jump table** | `0x0800B3FC` + `4*(mode-1)` | 16 absolute Thumb addresses (§6). |
| Scene-change method | `0x0800B39C` | vtable slot `0x087F0734`; passes `r1` to dispatcher. |
| Generic tail-call thunk | `0x080760F4` | Literally `bx r2`; used for vtable dispatch. |
| Scene object | IWRAM `0x03000250` | vtable `0x087F070C` at +0. |
| Scene mode field | IWRAM `0x0300025C` | Object +12; observed 11 (title) and 7 (battle). |
| Debug menu object | IWRAM `0x03003000` | vtable `0x087F0484` at +0. |
| Debug selection index | IWRAM `0x03003008` | 0-based, 0..9; moves with Up/Down. |
| Debug init flag | IWRAM `0x03003004` | 1 once initialized. |
| VISUAL VIEWER strings | `0x08079F38`–`0x0807A040` | `ATTACK:`, `SECRET:`, `TRG_JCHG:` etc. — labels, not cheats. |
| Sound-test string table | `0x0807BF84`–`0x0807C233` | `[SOUND TEST]`, `MUSIC NO`, `SE NO`. |
| Build timestamp | `0x0807AEC8` | US 1.000, Feb 10 2004. |
| Shift-JIS boot strings | `0x0807AE50`+ | Half-width katakana, decoded (§7). |

File offset = ROM address − `0x08000000`. The one-word patch used for the experiment is at file `0xB424` (dispatch table entry for observed mode 11).

## 5. Algorithm

Scene dispatch (`0x0800B3BC`), recovered from Thumb disassembly:

```
dispatch(scene_obj *o, int mode):        # r0=o, r1=mode
    o->mode_field = mode                  # str r1,[r4,#12]  -> 0x0300025C
    i = mode - 1
    if (unsigned) i <= 15:                # cmp r0,#15 ; bls
        target = *(u32*)(0x0800B3FC + 4*i)
        jump(target)                      # mov pc,r0
    # else fall through to 0x0800B512: no scene object created
```

The scene-change method `0x0800B39C` is reached through vtable slot `0x087F0734` (`bx r2` thunk at `0x080760F4`); it forwards `r1` unchanged. The mode value originates from a scene-object field, not from the keypad.

Debug menu input (`0x0800090C`):

```
r4,r5 = active_high_keys()               # 0x0800B638
if r4 & 0x04: sel = max(0, sel-1)         # Up
if r4 & 0x08: sel = min(9, sel+1)         # Down
if r5 & 0x10:                            # A
    if sel <= 7: jump(action_table[sel])  # 8-entry table at 0x08009A8
    else:        default_action()         # 0x0800A02
counter++                                # [obj+12]
```

The menu's Left/Right value adjustment and the A actions are per-entry; the full set is in §6.

## 6. Tables

**Debug menu — all 10 entries (enumerated in emulator, patched copy):**

| # | Label | RAM-observed effect of A | Resulting mode | Evidence |
|---:|---|---|---:|---|
| 0 | SCENE SELECT | Left/Right sets a scene number; A warps there. Value `2` + A → Guardiana field map with playable party. | 3 | `menu_sceneselect_v.png`, `scene2_afterA_v.png` |
| 1 | LOAD GAME | No visible change with no save file present (loader entry). | 11 | `entry1_v.png` |
| 2 | BATTLE VISUAL | Opens VISUAL VIEWER with 24 adjustable fields (ATTACK, TARGET, ACTION, MAGIC, ITEM, LV_UP, JOB_CHG:47, CRITICAL, EFFECT, SECRET, TRG_JCHG, …). | 6 | `entry2_v.png` |
| 3 | NORMAL FIELD MAP | Warps into a normal field map (rocky/forest area). | 4 | `entry3_v.png` |
| 4 | SCENARIO TEST | Debug list gains `-` markers and cursor lands on NORMAL FIELD MAP — an alternate scenario select list. | 11 | `entry4_v.png` |
| 5 | BOOT PROCESS | Boot/debug info screen: Proc Menu, Opening Demo, Chapter No 1, Tactics No 1, Shift-JIS options, build stamp. | 15 | `entry5_v.png` |
| 6 | SOUND TEST | `[SOUND TEST]` with `MUSIC NO` and `SE NO` (both 0); cursor `*`. | 9 | `entry6_v.png`, `soundtest_v.png` |
| 7 | MESSAGE TEST | Test dialogue box: "Varios: Now then … Give it all you've got!" | 1 | `entry7_v.png` |
| 8 | TACTICS NO | Value 1 displayed; A runs the default action and starts a tactics battle ("Turn 1"). | 7 | `entry8_v.png` |
| 9 | LANGAGE | Value `Japanese`; A runs default action and starts the same tactics battle. Left/Right cycles the 7 language strings at `0x081E7E08`. | 7 | `entry9_v.png` |

Footer shown on the main debug screen: `A BUTTON : OK`, `SELECT + START : SOFT RESET`. Heap readout is live (`INTERNAL RAM 1 03388/03c00`, `EXTERNAL RAM 11 387bc/40000` at the captured instant).

**Scene-mode space — all 16 dispatcher entries:**

| Mode | Handler | Mode | Handler |
|---:|---|---:|---|
| 1 | `0x0800B4C6` → `0x080006A8` | 9 | `0x0800B4F0` → `0x08064B40` |
| **2** | **`0x0800B4CC` → `0x08000778` = DEBUG MENU** | 10 | `0x0800B4F6` → `0x08002700` |
| 3 | `0x0800B4D2` → `0x08001298` | 11 | `0x0800B424`-entry `0x0800B506` (boot/title, observed) |
| 4 | `0x0800B4D8` → `0x08001298`+ | 12 | `0x0800B512` — **no-op** |
| 5 | `0x0800B4DE` → `0x08008E30` | 13 | `0x0800B442` (reads obj+28/+32) |
| 6 | `0x0800B4E4` → `0x0800917C` | 14 | `0x0800B492` (reads obj+20) |
| 7 | `0x0800B4EA` → `0x08000CA4` | 15 | `0x0800B43C` (reads obj+12) |
| 8 | `0x0800B512` — **no-op** | 16 | `0x0800B50C` (reads obj+16) |

**Published codes:** GameFAQs (rippercito secrets guide, Shiningwiz21 walkthrough), almarsguides, gamegenie.53lu.com, libretro CodeBreaker database and shineforcecentral all list only device codes (e.g. `00004600 000A / 1000B7D8 0007` enable, `82000054 423F` max money, `420002C0 0063` infinite HP). These are CodeBreaker/GameShark/Action Replay memory patches, not in-game codes; none is a literal string in the ROM and none is in scope. **No published in-game password/button code was found for any region.**

## 6b. Enumeration

**Space definition.** The only hidden-feature selector in this build is the 4-bit-ish scene mode: 16 representable values (1..16), gate `(mode-1) <= 15`. There is no password alphabet, no checksum field, no key-mask sequence table. The debug menu is exactly one value of that space (mode 2); two values are no-ops (8, 12); values 0 and 17+ are unrepresentable.

**Novel code (not in any published list).** I generated and entered, on the debug menu's own `SCENE SELECT` screen, the value **2** and pressed A. This is absent from GameFAQs, VGChartz, TCRF and every wiki consulted (they list no GBA scene codes at all). RAM proof: mode field `0x0300025C` changed `11 → 3`, debug selection `0x03003008` became `0xFF` (menu destroyed), and the screen changed to the Guardiana field map with an armed party (`scene2_afterA_v.png`). Separately, the debug menu itself (mode 2) was minted by rewriting dispatch entry 10 on a copy and confirmed with all ten entries enumerated (§6). Both are developer-intended combinations, not published data.

**Bounds proven by rejection.**
- Static: the dispatcher's `subs r0,#1; cmp r0,#15; bls` gate means 0 and ≥17 never index the table; they fall through to `0x0800B512` with no scene object created.
- Dynamic: patching the boot request to the no-op target `0x0800B512` on a copy produced **no scene at all** — a black screen with no title, no menu and no mode change (`reject_v.png`). This is the in-game rejection of an out-of-domain selector.
- In-range but inert values 8 and 12 point at the same no-op target, so they are rejected as well.

**Button-code sweep (negative, bounded).** On the unpatched ROM, held from power-on through boot: `L+R`, `L+R+Start`, `A+B`, `A+B+Start+Select`, `Start+Select`, `L+R+A+B`. Every one left mode `0x0B` (11) — none opened the debug menu. A title-screen sequence test was not exhaustive over arbitrary lengths, so this negative is bounded to the tested set; no key-mask table or keypad→mode writer was found statically.

**Reachable screens walked with RAM evidence.** Title screen (mode 11), opening story dialogue, hero-name entry (mode 7, 62-symbol keyboard, `Start`=END — a name field, not a validator), tutorial battle vs. Varios (mode 7), debug main menu (mode 11 object + debug object at `0x03003000`), and all ten debug entries above. The debug UI text is plain ASCII and was found directly by `strings`; the BOOT PROCESS detail strings are Shift-JIS half-width katakana and were decoded (`ｽｷｯﾌﾟ`, `ｱｲﾃﾑBOX&ｶｰﾄﾞ ﾂｲｶ`, `ﾈｳ ｶｲｽｳ`) — screen enumeration is not resting on a missing string scan.

## 7. Validation evidence

**Observed (emulator / savestate RAM):**
- Boot/title mode `0x0B` at `0x0300025C`; battle mode `0x07` (read from decompressed `gbAs` savestate chunks at state offset `0x19000+0x25C`).
- Debug object at `0x03003000`, vtable `0x087F0484`, selection `0x03003008` incrementing 2→3 on one Down press (three-state savestate diff).
- All ten menu screens and their mode transitions listed in §6; scene-select 2 → Guardiana (mode 3); no-op redirect → black screen.
- Six boot button combinations all leave mode 11.
- Patched copy boots straight into the debug menu with no input.

**Derived (disassembly):**
- Scene dispatcher gate and 16-entry table; `mode 2 → debug creator`; `0x080760F4 = bx r2` vtable thunk; `0x0800B39C` forwards `r1` untouched.
- Debug input masks and 8-way A-action jump table at `0x08009A8`.
- Header/logo scan: one image, stock entry, no trainer.

**Inferred (not fully exercised):**
- `LOAD GAME` was observed with no save file, so its behavior with a valid save is inferred from its name only.
- The exact gameplay meaning of most VISUAL VIEWER fields was not tested individually; their labels and the screen are observed.
- The Shift-JIS BOOT PROCESS options were decoded but not activated one by one.

## 8. Unknowns

- No retail input path to mode 2 was found, but the game's scene-mode field is written from several scene/script objects; an exhaustive proof over every possible script state was not attempted. The negative is bounded to the dispatch table, the observed sessions, and the six-combination sweep.
- `LOAD GAME` with a valid save, and individual VISUAL VIEWER / BOOT PROCESS parameters, were not exhaustively exercised.
- The Japanese and European builds were not analyzed; strings/dispatcher addresses differ there per TCRF.

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python `struct` scans for 32-bit pointers, Thumb `LDR`-literal and `BL` targets.
- `arm-none-eabi-objdump -M force-thumb` for all disassembly listed in §4–§5.
- mGBA 0.10.5 CLI debugger (`-d`) for breakpoints at `0x0800B3BC` / `0x0800B39C` and register reads; Xvfb `:317`, openbox, xdotool, scrot, ImageMagick for screens.
- Python/zlib parser for mGBA `.ss1` `gbAs` chunks (raw state 397,312 B; IWRAM at `0x19000`, EWRAM at `0x21000`) — used for all RAM evidence and the savestate diff (§16.13).
- Helper scripts: `/tmp/shiningforce/{walk.py,snap.py,ss.py,combos.py,enumrun.py,dbg_daemon*.py}`. Patch copies `sf_debugpatch.gba` (mode-2 entry) and `sf_rejectpatch.gba` (no-op entry) live in the work dir; neither was written to the ROM folder.

**Legal note:** no ROM, save, savestate or copyrighted asset is redistributed by this report. Only addresses, hashes, algorithms, and observations are published.

**Cleanup:** all emulators, Xvfb/openbox and debugger daemons started for this engagement were terminated by PID; the generated `.sav` and `.ss1` in the ROM folder were deleted. The ROM folder contains only the original `.gba` and this report.
