# Aero the Acro-Bat: Rascal Rival Revenge (GBA) — Reverse Engineering Report

ROM analyzed: `roms/Aero the Acro-Bat: Rascal Rival Revenge/Aero the Acro-Bat: Rascal Rival Revenge.gba`
(header title `AEROACROBATX`, game code `AAOE`, the 2002 US release; the folder name uses the
2024 remaster title).

---

## 1. Target identity

| Field | Value |
|---|---|
| File size | 4,194,304 bytes (4 MiB, `0x400000`) |
| Header title (`0xA0`) | `AEROACROBATX` |
| Game code (`0xAC`) | `AAOE` |
| Maker code (`0xB0`) | `5N` |
| Software version (`0xBC`) | `0` |
| Entry branch (`0x00`) | `0xEA00002E` (`b 0x080000C0`) |
| Complement check (`0xBD`) | stored `0x3D`, computed from header `0x39` (mismatch) |
| Header checksum (`0xBE`) | stored `0x0000`, computed `0x00C3` (mismatch) |
| MD5 | `266e48e50827e202a9e74255bf29a554` |
| SHA-1 | `cdbc609df128127d05c435f59b781958c0e751fd` |
| SHA-256 | `2d1631c5568a589092f9ed854255977623171ebf62d8eb0dd24e616499c0998e` |

**Embedded GBA-header scan (Phase 0).** The 156-byte Nintendo logo
(`24 ff ae 51 … 21 d4 f8 07`) occurs exactly **once** at file offset `0x4`, i.e. one GBA image
based at `0x08000000`. No multi-game/pack headers, no sub-images, no shell. The logo bytes match
the canonical logo at `rom[4:0xA0]`.

**Header anomaly.** Both the complement check and the header checksum are wrong, and the stored
header checksum is zero. This is not a random dump error: the title ends in `X` and the checks
were not recomputed after the title was changed. Treat the image as a *patched* retail build.
The code and the level-select strings described below match the published retail layout
(TCRF documents the same screen and the same `0x03002C30` screen-id byte), so the patch did not
move the code we analyse.

---

## 2. Executive summary

This is the 2002 Atomic Planet GBA remake, not the SNES/Genesis original. The engagement asked
for in-game/developer-intended cheat systems: passwords, button codes, hidden/debug menus and
unlockables.

* **There is no password system.** The entire ROM contains no `PASSWORD`/`PASSWD`/`CHEAT`/`CODE`
  string, no input alphabet, no character table and no validator. All user-facing text is plain
  ASCII in one bank (`0x34B000`–`0x34F000`) and contains only menus, act names, objectives,
  results and credits.
* **There is no button-code system.** All key input is edge-detected into one variable
  (`0x03002D44`) and consumed by the individual screen handlers. All 89 reads of that variable
  were enumerated and inspected: each is a one-frame edge test for a menu item or a gameplay
  action. No handler keeps a press-sequence counter, and no expected-mask table was found by any
  scan (u16 mask runs, byte index runs, or the 89 read sites). The GBA pad also lacks the C/X/Y
  buttons used by the published Genesis/SNES codes.
* **Developer content that does exist:** a complete hidden **LEVEL SELECT** screen (screen id 13,
  handler `0x0801E514`) that displays `LEVEL / SELECT` and a 0–24 index, plus a **hard-mode
  unlock** (“CIRCUS ACT 1+”, 25 extra act-name strings) gated by a completion bit.
* The level select has **no in-game trigger**. All 85 code sites that load the screen-id address
  were enumerated; none writes 13. The only published trigger is the memory-write code
  `33002C30 000D` (TCRF), which is a GameShark-class action and therefore outside this
  engagement's “in-game cheats only” scope. We reproduced its *effect* with the mGBA debugger to
  reverse and enumerate the screen.
* **Enumeration (new):** the level select edits the current save slot's level byte and covers
  **25 acts, 0–24**. Index 24 is `MUSEUM BOSS` (“EDGAR EKTOR'S DOMAIN”). Entering it in-game is
  shown below; it is not enumerated in any published source we found. The ring wraps 24→0 on
  Right and 0→24 on Left, so 25 is not representable.

---

## 3. How to reproduce

**Emulator and display.** mGBA 0.10.5 (`/usr/games/mgba`), Xvfb `:126`, openbox, 3× scale.
Keymap used by mGBA SDL: **A = `x`, B = `z`, L = `a`, R = `s`, Start = `Enter`,
Select = `BackSpace`, D-pad = arrow keys**. Keys must be held ≈150–300 ms; the title/menu fades
ignore input during transitions.

**Boot timing.** Power-on → Atomic Planet logo (screen 3) → Metro3D logo (screen 1) →
“AERO THE ACRO-BAT” splash (screen 4, waits for A) → intro cutscene (screens 5/6, A advances) →
title (screen 7, “PRESS START”). The boot to title takes ≈30 s in this environment. After ~16 s
of no input the game enters the attract/high-score loop (screen 8); Start returns to the title.

**Reaching the level select for analysis (not an in-game cheat).** Run mGBA with the CLI debugger:

```
DISPLAY=:126 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 -d "Aero the Acro-Bat: Rascal Rival Revenge.gba"
# at the debugger prompt, at any stable screen:
w/1 0x03002c30 0x0D      # screen id 13 = level select
w/1 0x030026dc 0x00      # substate 0 (required; stale substate >3 makes the handler no-op)
continue
```

This is the equivalent of TCRF's `33002C30 000D`, reproduced here only to inspect the screen.
The screen then accepts **Left/Right** to change the level and **A/Start** to confirm.

**Menu walk used for the screenshots.** Screens marked “poke” were opened with the debugger after
their normal entry condition was read from the code, because they are deep in a flow that would
have required erasing the test save; all other screens were walked with the pad.

| Screen | Path / how reached |
|---|---|
| Title | boot, wait for “PRESS START” (walked) |
| High scores / attract | wait ~16 s at title (walked) |
| Main menu | title → Start (walked) |
| New/Continue slot chooser | main menu → A on NEW GAME or CONTINUE (walked) |
| Name entry | NEW GAME → slot → A (walked) |
| Options | main menu → OPTIONS → A (walked) |
| Reset-save confirm / done (ids 11/12) | Options item 4 → screen 11 (code at `0x0801DFB8`); inspected by poke so the save was not erased |
| Copy Game (id 22) | slot chooser → COPY GAME; inspected by poke |
| Act card | start a game or level select → A (walked) |
| Gameplay | act card → A (walked) |
| Pause | gameplay → Start (walked) |
| Credits (id 37) | Options → CREDITS (code at `0x0801DFD4`); inspected by poke |
| Level select (id 13) | debugger write; no in-game trigger (see above) |

**Published-code test.** GBA-specific published codes: none. The GameFAQs GBA cheats page
(archived 2023-08-28) lists only **GEN** and **SNES** entries whose sequences use C/X/Y, buttons
that do not exist on the GBA; they are not expressible on this port. The only GBA-era published
item is TCRF's `33002C30 000D` memory write, verified above.

---

## 4. Address map

File offset → ROM address: `rom = 0x08000000 + file_offset`.

| Item | File offset | ROM/RAM address | Notes |
|---|---:|---|---|
| Screen-handler table | `0x34F298` | `0x0834F298` | 52 × u32 Thumb pointers |
| LEVEL SELECT table entry | `0x34F2CC` | `0x0834F2CC` | `0x0801E515` (entry 13) |
| LEVEL SELECT handler | `0x1E514` | `0x0801E514` | state 0..3 |
| “LEVEL” string | `0x34EE50` | `0x0834EE50` | `LEVEL@` |
| “SELECT” string | `0x34EE58` | `0x0834EE58` | `SELECT@` |
| Level-row function ptr table | `0x34EE64` | `0x0834EE64` | all entries `0x0801E8F5` |
| Act-name table (normal) | `0x34BC12` | `0x0834BC12` | 25 strings, 16-byte stride |
| Act-name table (hard “+”) | `0x34BDB2` | `0x0834BDB2` | 25 strings |
| Main-menu handler (id 9) | `0x1D0C4` | `0x0801D0C4` | NEW GAME/CONTINUE/OPTIONS |
| Options handler (id 10) | `0x1D4D4` | `0x0801D4D4` | MUSIC/EFFECTS/BRIGHTNESS/CREDITS/RESET |
| Reset confirm handler (id 11) | `0x1E034` | `0x0801E034` | “ALL DATA WILL BE ERASED” |
| Reset done handler (id 12) | `0x1E308` | `0x0801E308` | “SAVE DATA HAS BEEN ERASED” |
| Act-card handler (id 14) | `0x1E850` | `0x0801E850` | act name + objective |
| Pause handler (id 28) | `0x22938` | `0x08022938` | PAUSED + values |
| Credits handler (id 37) | `0x2396C` | `0x0802396C` | scrolling credits |
| Dispatch / screen call | `0x2C3A2` | `0x0802C3A2` | `table[*(u8*)0x03002C30]` |
| Key edge detector | `0x2C588` | `0x0802C588` | reads `0x04000130`, stores new keys |

RAM:

| Address | Width | Meaning |
|---|---:|---|
| `0x03002C30` | u8 | current screen id |
| `0x030026DC` | u8 | current screen substate (must be 0 to enter screen 13 cleanly) |
| `0x03003474` | u8 | pending screen id copied into `0x03002C30` |
| `0x03002D44` | u16 | keys newly pressed this frame (active high) |
| `0x030024C0` | struct | selected save-slot mirror; player name, level, flags |
| `0x030024CC` | u8 | **current act index** edited by the level select (slot base + `0x0C`) |
| `0x030024DE` | u8 | slot base + `0x1E`; **bit 7 = game-completed/hard-mode** (see §5) |
| `0x030026B8` | u8 | slot index used by the level select (`0` for first slot) |
| `0x03002C4C` | u16 | main-menu / confirm selection index |
| `0x03002C64` | u8 | menu row index used when drawing |

Key mask bits in `0x03002D44`: `A=0x01, B=0x02, Select=0x04, Start=0x08, Right=0x10,
Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`.

---

## 5. Algorithm

### 5.1 Screen manager

Every frame the dispatcher at `0x0802C3A2` does:

```
id     = *(u8*)0x03002C30
handler= *(u32*)(0x0834F298 + id*4)   // Thumb pointer, low bit set
call(handler)
```

Each handler is a state machine on `0x030026DC` (0 = init, 1 = fade in, 2 = input, 3 = fade
out/confirm). A handler changes screens by writing the id byte, usually `ldr r1,=0x03002C30;
movs r0,#N; strb r0,[r1]`.

### 5.2 Hidden level select (screen 13)

Handler `0x0801E514`, states 0–3. State 0 loads the “LEVEL”/“SELECT” strings
(`0x0834EE50`/`58`), creates the two title rows and loads sprites; state 2 is the input state.

Reconstructed input logic (addresses in comments):

```c
u8 *lvlp = (u8*)(0x030024C0 + 0x0C + *(u8*)0x030026B8);  // 0x0801E730
u8  lvl  = *lvlp;
u16 key  = *(u16*)0x03002D44;

if (key & 0x20) {                 // Left  (0x0801E724)
    lvl = (lvl == 0) ? 24 : lvl - 1;      // 0x0801E73C..758
} else if (key & 0x10) {          // Right (0x0801E75C)
    lvl = (lvl > 23) ? 0 : lvl + 1;       // 0x0801E774..788
}
if (key & 0x09) {                 // A or Start (0x0801E7BE)
    *(u8*)0x030026DC = 3;         // fade out
    // state 3: clear pending vars and set screen = 14 (act card) at 0x0801E832
}
*lvlp = lvl;
```

Consequences:

* The editable space is **0–24 inclusive**. `Right` at 23 stores 24; `Right` at 24 stores 0.
  `Left` at 0 stores 24. There is no path to 25.
* The value is the **save slot's current act byte**, not a transient selection: after using the
  screen, the slot chooser and the Copy Game screen show the changed act
  (`AZZ … MUSEUM BOSS` was observed after selecting 24).
* Confirming goes to screen 14 (act card), which reads the same act byte and looks the act name
  up in `0x0834BC12`; pressing A there starts the act.

### 5.3 Hard-mode (“+”) select

Act card / slot drawing at `0x0801FE4A`:

```
b = *(u8*)(slot + 0x1E);
if (b & 0x80) use table 0x0834BDB2   // “CIRCUS ACT 1+” … “MUSEUM BOSS+”
else          use table 0x0834BC12   // normal acts
```

This is the code behind the published “complete the game to see CIRCUS ACT 1+” unlockable.
Our test save had `0x03` at `0x030024DE` (bit 7 clear), so the normal list was shown.

---

## 6. Tables

### 6.1 Screen ids (from the 52-entry table at `0x0834F298`)

| id | handler | screen |
|---:|---|---|
| 0 | `0x0801B890` | copyright / legal text |
| 1 | `0x0801BA8C` | Metro3D logo |
| 2–3 | `0x0801BB7C`, `0x0801BC6C` | Atomic Planet logo sequence |
| 4 | `0x0801BD5C` | “AERO THE ACRO-BAT” splash (A) |
| 5–6 | `0x0801C0DC`, `0x0801C438` | intro cutscene pages |
| 7 | `0x0801C790` | title, “PRESS START” |
| 8 | `0x0801CC98` | high scores / attract |
| 9 | `0x0801D0C4` | main menu (NEW GAME / CONTINUE / OPTIONS) |
| 10 | `0x0801D4D4` | options (MUSIC / EFFECTS / BRIGHTNESS / CREDITS / RESET) |
| 11 | `0x0801E034` | reset-save confirm |
| 12 | `0x0801E308` | save-data-erased message |
| **13** | **`0x0801E514`** | **LEVEL SELECT** |
| 14 | `0x0801E850` | act card (name + objective) |
| 15 | `0x0801EC38` | act completed |
| 16 | `0x0801F460` | bonus results |
| 18 | `0x0801FD78` | choose game (new) |
| 19 | `0x08020238` | overwrite warning |
| 20 | `0x080205F8` | enter name |
| 21 | `0x08020D88` | name confirm (YES/NO) |
| 22 | `0x08021198` | copy game — select source |
| 23 | `0x08021630` | copy game — select target |
| 24 | `0x08021B38` | copy game — replace confirm |
| 25 | `0x08022008` | continue — choose game |
| 28 | `0x08022938` | PAUSED |
| 29 | `0x080234EC` | pause options / quit |
| 37 | `0x0802396C` | credits |
| 38 | `0x08023C98` | game cleared |

(ids 17, 26, 27, 30–36, 39–51 are internal game/act states, e.g. id 30
`0x0802587C` is the in-level gameplay state; the HUD appeared with screen id `0x1E` = 30.)

### 6.2 Act list (normal), `0x0834BC12`, index → name

| # | name | # | name |
|---:|---|---:|---|
| 0 | CIRCUS ACT 1 | 13 | FUNPARK BOSS |
| 1 | CIRCUS ACT 2 | 14 | WOODS ACT 1 |
| 2 | CIRCUS ACT 3 | 15 | WOODS ACT 2 |
| 3 | CIRCUS ACT 4 | 16 | WOODS ACT 3 |
| 4 | CIRCUS ACT 5 | 17 | WOODS ACT 4 |
| 5 | CIRCUS BONUS | 18 | MUSEUM ACT 1 |
| 6 | CIRCUS BOSS | 19 | MUSEUM ACT 2 |
| 7 | FUNPARK ACT 1 | 20 | MUSEUM ACT 3 |
| 8 | FUNPARK ACT 2 | 21 | MUSEUM ACT 4 |
| 9 | FUNPARK ACT 3 | 22 | MUSEUM ACT 5 |
| 10 | FUNPARK ACT 4 | 23 | MUSEUM BONUS |
| 11 | FUNPARK ACT 5 | **24** | **MUSEUM BOSS** |
| 12 | FUNPARK BONUS | | |

Hard-mode counterparts “CIRCUS ACT 1+” … “MUSEUM BOSS+” are at `0x0834BDB2` in the same order.

### 6.3 Text-bank inventory (`strings -t x -n 4` = 28,762 lines)

| Keyword (case-insensitive) | Hits | Context |
|---|---:|---|
| `password`, `passwd`, `cheat`, `code` | 0 | none anywhere |
| `select` | 4 | “USE A BUTTON TO SELECT”, “SELECT A GAME TO…”, `LEVEL@SELECT@` |
| `debug` | 1 | `AGB DEBUG ASSERT:` at `0x105A00` (Nintendo SDK assert text) |
| `secret` | 1 | “SECRET PASSAGE” — a level objective at `0x34C5B1` |
| `sound test`, `gallery`, `hidden`, `unlock` | 0 | none |

---

## 6b. Enumeration

**Space definition.** The hidden level-select edits one byte: the current save slot's act index
at `0x030024CC` (`slot_base + 0x0C`), displayed as a two-digit decimal in the screen centre.
Valid range is **0–24 (25 values)**; the byte is stored in the save data (observed: after
selecting 24 the Copy Game screen showed `1: AZZ … MUSEUM BOSS`).

**Field model.**

| Field | Bits | Values | Notes |
|---|---:|---|---|
| act index | 5 (stored in a byte) | 0–24 | 25–31 unreachable |
| hard-mode selector | 1 (`slot+0x1E` bit 7) | normal / “+” list | not editable from this screen |

**Complete enumeration (25 values).**

```
00 CIRCUS ACT 1     05 CIRCUS BONUS     10 FUNPARK ACT 4    15 WOODS ACT 2      20 MUSEUM ACT 3
01 CIRCUS ACT 2     06 CIRCUS BOSS      11 FUNPARK ACT 5    16 WOODS ACT 3      21 MUSEUM ACT 4
02 CIRCUS ACT 3     07 FUNPARK ACT 1    12 FUNPARK BONUS    17 WOODS ACT 4      22 MUSEUM ACT 5
03 CIRCUS ACT 4     08 FUNPARK ACT 2    13 FUNPARK BOSS     18 MUSEUM ACT 1     23 MUSEUM BONUS
04 CIRCUS ACT 5     09 FUNPARK ACT 3    14 WOODS ACT 1      19 MUSEUM ACT 2     24 MUSEUM BOSS
```

**Novel values (not enumerated in any published list we found).**
TCRF documents only the code that opens the screen; it does not enumerate it. We generated and
entered two values that exercise unadvertised corners:

| Value | In-game proof | Effect |
|---:|---|---|
| **24** (`0x18`) | act card “MUSEUM BOSS / EDGAR EKTOR'S DOMAIN”, then the museum boss arena | final act, reachable only because the screen wraps 23→24 |
| 12 (`0x0C`) | act card “FUNPARK BONUS / STAY ALIVE” | confirms the 16-byte act-name order |

**Bounds proven by rejection.**

* At index `24`, Right does **not** produce 25: it wraps to `00` (observed value in
  `0x030024CC` changed `0x18` → `0x00`, screen redrew `00`). So 25 is not representable.
* At index `00`, Left wraps to `24` (observed `0x00` → `0x18`, screen redrew `24`), so −1 is not
  representable.
* The handler's code contains no clamp branch that keeps 24 on increment; the “over-range” branch
  is the wrap (`cmp #23; bhi → movs r0,#0` at `0x0801E774`/`0x0801E788`), which is why 24 is
  reachable at all.

**Published-code comparison.**

| Source | Code | Test | Result |
|---|---|---|---|
| GameFAQs GBA cheats page | 4 blocks, marked GEN/SNES only | buttons C/X/Y absent on GBA | not expressible on this port |
| TCRF | `33002C30 000D` (GameShark write) | reproduced with debugger write of `0x0D` to `0x03002C30`, substate 0 | screen 13 opens; trigger is a memory edit, not an in-game code |
| GameFAQs unlockable | complete the game → “CIRCUS ACT 1+” | code path found at `0x0801FE4A` (bit 7 of `slot+0x1E`) | derived, not exercised (no completed save) |

---

## 7. Validation evidence

**Observed (emulator screenshots / memory reads).**

* Title `PRESS START`, main menu, slot chooser, name entry, options
  (`MUSIC 75 / EFFECTS 100 / BRIGHTNESS 2 / CREDITS / RESET SAVE DATA`), pause
  (`PAUSED`, same three values, `CONTINUE`, `QUIT`), act card, gameplay HUD, copy-game screen,
  credits screen and the reset-confirm/done dialogs were all displayed.
* Screen id at the main menu = `9`; options = `10`; pause = `28`; act card = `14`; gameplay = `30`;
  title = `7`; high scores = `8`; copy-from = `22` (read at `0x03002C30`).
* Level select: `00` → Left → `24`; `24` → Right → `00`; level byte at `0x030024CC` changed
  `0x00`→`0x18`→`0x00` accordingly. Index 24 produced “MUSEUM BOSS / EDGAR EKTOR'S DOMAIN” and
  then the museum boss arena; index 12 produced “FUNPARK BONUS / STAY ALIVE”.
* The level byte is persistent in the slot mirror: Copy Game displayed `AZZ … MUSEUM BOSS`.
* Key variable `0x03002D44` is edge-detected from `0x04000130` at `0x0802C588`.

**Derived (instruction sequence).**

* Screen dispatch via the 52-entry table at `0x0834F298` and the byte at `0x03002C30`.
* Level-select input map (Left `0x20`, Right `0x10`, A/Start `0x09`), the 0↔24 wrap, and the
  confirm path to screen 14.
* No store of immediate `13` to `0x03002C30` exists among the 85 enumerated stores; the only
  reference to the level-select handler is table entry 13. The published trigger is a raw
  memory write.
* Hard-mode list selection by bit 7 of `slot+0x1E` at `0x0801FE4A`.

**Inferred.**

* Screen names for ids 1–6 and 29–38 are from the strings/graphics they draw; the handler
  addresses and ids are exact.
* The completion bit is written by the end-of-game path; we did not complete the game, so the
  write site was not exercised (the *read* site is proven).

---

## 8. Unknowns

* Whether any release (JP `AAOJ`, EU `AAOP`) contains an in-game trigger for screen 13; only the
  US `AAOE` image was analysed. The level-select code is region-independent in this build.
* The exact writer of the completion bit at `slot+0x1E` bit 7. The reader and the resulting
  “+” list are proven; a completed save was not available.
* The save-slot stride for slots 2/3 and the checksum (if any) of the 512-byte `.sav` were not
  reversed; only slot 1's layout and the act/completion bytes were needed.
* Screen 13's artwork is loaded from banks that are also used by the act card; the screen works
  when entered by the debugger, but a cold entry at arbitrary times can leave a stale frame if
  `0x030026DC` is not zeroed (documented above).

---

## 9. Tooling

| Tool | Use |
|---|---|
| `xxd`, `file`, `md5sum`, `sha1sum`, `sha256sum` | identity/header |
| GNU `strings -t x` | text bank inventory |
| Python 3 + `struct` | header scan, pointer scans, act-table dump |
| Capstone 5.0.7 | literal-load / store / key-mask scans |
| `arm-none-eabi-objdump -M force-thumb` | handler disassembly |
| mGBA 0.10.5 SDL (`-3`, `-d`) | ground truth and CLI debugger (watchpoints, memory reads/writes, backtrace) |
| Xvfb `:126` + openbox + xdotool + scrot + ImageMagick | headless display, input, screenshots |

Helper scripts used in the work directory (not shipped with the ROM): a key/screenshot helper
(`ctl.py`) and literal/BL scanners (`scan.py`). Screenshots were taken from the 720×480 3×
viewport at window offset `+153+164`.

**Legal note.** No ROM, extracted graphics, music or text is redistributed with this report.
All addresses, tables, algorithms and generated values are original findings.

---

### Appendix A — store enumeration for the screen id

85 code sites that load the screen-id address were found. The immediate values actually stored
are:

```
0, 1, 2, 5, 6, 7, 9, 10, 14, 15, 17, 18, 20, 22, 27, 30, 31, 32, 33, 34, 35, 36, 37, 40
```

(plus one false positive, `120`, which is a sprite coordinate in a pool that happens to hold
`0x03002C30`). **No store of `13` (0x0D) exists.**

The apparently computed stores were each traced: every one is followed by a `movs r0,#N;
strb r0,[r1]` selection (values `9, 10, 11, 12, 14, 18, 19, 20, 22, 23, 24, 25, 27, 37`) or is a
copy of the pending-screen byte `0x03003474`. That pending byte is written with `0x0A`, `0x0E`,
`0x1B`, `0x26` and `0x03` only. This is the static basis for “no in-game trigger”; the dynamic
route (TCRF's code) is a memory write.

### Appendix B — exact proof points

* `0x0801E72A`: `ands r0, r1` with `r0=0x20` (Left) before the decrement block.
* `0x0801E774`: `cmp r0,#23`; `0x0801E776`: `bhi 0x0801E788`; `0x0801E788`: `movs r0,#0`.
* `0x0801E73C`: `cmp r0,#0`; `0x0801E758`: `movs r0,#24`.
* `0x0801E7BE`: `ands` with `0x09` (A|Start) → substate 3.
* `0x0801E832`: `movs r0,#0x0E; strb` → screen 14.
* `0x0801FE4A`: `ldrb r1,[r4,#0x1E]`; `ands` with `0x80`; branches to the `+` table
  `0x0834BDB2` vs the normal table `0x0834BC12`.
