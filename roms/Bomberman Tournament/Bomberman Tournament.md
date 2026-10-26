# Bomberman Tournament (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-26.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Bomberman Tournament/Bomberman Tournament.gba` |
| Size | 4 MiB (`0x400000`) |
| Header title | `BOMSTORYUSA` |
| Game code | `ABSE` |
| Maker code | `52` (Hudson Soft) |
| Software version | `0` (Rev.00) |
| MD5 | `79aef9bbe1378adfbd688cd66e11a7be` |
| SHA-1 | `da44a5d65f1a00d75a57e5b46e30f9e4e2d18f6c` |
| SHA-256 | `e02e6cc3e91f4f4c7b50ae9558eddc93d43a7f894be0bb0cd46b0296327de902` |
| Complement check (`0xBD`) | `0x67` — **valid** (`(-(0x19 + sum(0xA0..0xBC))) & 0xFF`) |
| Reserved (`0xBE`–`0xBF`) | `0x0000` — as specified by the GBA header format |

ROM addresses below are `0x08000000 + file_offset`. All findings are tied to this
exact hash; another revision may differ.

**Header sanity (no trainer).** The complement check recomputes to `0x67`, and
the two reserved bytes at `0xBE` are `0x0000`; the header is therefore intact
(the two bytes at `0xBE` are *reserved*, not a second checksum — a common
misreading). The boot code at `0x080000C0` is the stock Nintendo crt0, the file
is exactly 4 MiB with no appended payload, and the two additional header copies
embedded in the ROM (`0x3857C0`, `0x3C0CFC`) are **byte-identical** to the
header at `0x0`. No trainer and no patch were found.

**Embedded-header scan.** Three copies of the 156-byte Nintendo logo/header
exist: file `0x0`, `0x3857C0` and `0x3C0CFC` (all `BOMSTORYUSA` / `ABSE`). Each
of the latter two is followed by a branch (`b .`-style stub at `+0xC0`), i.e.
they are **embedded multiboot/link child images** used by the "Send Data" /
"MULTI BOOT" path (`screenshots/06_send_data.png`, `screenshots/09_test_multiboot.png`).
Labelled *Inferred*; the observation is that the copies and their entry stubs
are present and otherwise unreferenced by the story code.

---

## 2. Executive summary

**There is no password system, no button code and no cheat menu reachable by
normal play in this game.** What exists is a **developer test menu** that is
compiled in and gated by a single build constant, exactly as TCRF documents.
This report goes past TCRF's one-line note: it maps the gate to the engine's
scene machine, enumerates all 16 menu entries and their effects, measures the
bounded sub-selectors (sound test, mini-game selector), and returns the first
description of the hidden **256-bit flag editor** and its RAM location.

1. **The gate.** At boot the game writes the initial *scene id* with
   `MOVS R0, #0x3C` at `0x08000CBA` and then calls the scene setter
   `0x08000C78(scene, arg)`. `0x3C` = 60 = the title/logo scene. Changing that
   immediate to `0x5A` (= 90) boots straight into `TEST SELECT`. The 81-entry
   dispatch table at `0x08000CE0` maps states 10..90 to handlers; state 90 maps
   to `0x08000F08` → screen setup `0x08042980`.
2. **The menu.** 16 entries, drawn from a 17-pointer string table at
   `0x0822581C` (`TEST SELECT` is the title) with a parallel 17×`u16`
   attribute table at `0x08225860`: FIELD, BATTLE, MULTI BOOT, CHAR BOMB,
   SOUND TEST, MINI GAME, OPENING, ENDING, DATA SAVE, DATA LOAD, BATTLE MINI,
   TITLE DEMO, GAME OVER, POWER ON, STAFF ROLL, FLAG SET. Every entry was
   entered and screenshotted; each maps onto the corresponding retail screen.
3. **Bounded sub-selectors.** SOUND TEST is a 101-value selector `000..100`
   that **clamps** at 100 (further presses do nothing — proven). MINI GAME is a
   4-value selector `0..3` that **wraps modulo 4** (`4 → 0`, proven by the game
   launched). FIELD is a warp selector to arbitrary map/interior ids (observed
   valid: 000, 004, 097 = house interior, 270 = shop); the upper id bound
   was not established (see §8).
4. **The flag editor (undocumented before this report).** FLAG SET displays the
   game's 256 runtime flags as a 16×16 grid of bits. `A` sets the bit under the
   cursor; `B` leaves the screen. The array is 32 bytes at **`0x02035274`**
   (flag *n* = bit *n* of that array). Example verified from a savestate diff:
   setting the cursor to 2 and pressing `A` changes `0x02035274` from `0x00` to
   `0x04`. The flags are RAM-only: a reset (POWER ON / `Ctrl+R`) clears them.
5. **No code surface.** All 4 MiB were searched for `password`, `passcode`,
   `cheat`, `code`, `ABCDEFGHIJKLMNOPQRSTUVWXYZ`, and every menu was walked.
   Zero hits, zero password screens. GameFAQs has exactly **one** entry on its
   cheat page and it is a gameplay trick (``use elekong in muiltiplayer mode``),
   not a code; TCRF documents only the ROM patch. The code space is therefore
   **empty**, and §6b states that as a bounded negative rather than a guess.

---

## 3. How to reproduce

### Emulator and input

```bash
Xvfb :196 -screen 0 1024x768x24 &
DISPLAY=:196 openbox &
DISPLAY=:196 SDL_AUDIODRIVER=dummy mgba -3 "Bomberman Tournament.gba" &
```

mGBA SDL default keymap: `A`=`x`, `B`=`z`, `L`=`a`, `R`=`s`, `Start`=`Return`,
`Select`=`BackSpace`, D-pad = arrow keys. Hold keys ≥100 ms; the game polls
input once per frame. `Ctrl+R` resets the console (returns to the gate/
`TEST SELECT` in the patched build); `Shift+F1..F10` save state, `F1..F10` load.

### Normal-play menu tree (walked end-to-end, unpatched ROM)

```
Title ("Press Start")                            scene 60
 └─ Start → main menu: Quest / Battle            scene 50, sub-mode 5
     ├─ Quest → "New Game" (only entry with no save; 2 save slots exist)
     │        → intro cut-scene → ship interior → field/town gameplay
     └─ Battle → 1 Player / Group / [ Host a Game ]
          ├─ 1 Player → Pick Char (4 slots) → Rules → battle
          └─ Group    → "Send Data" link screen (2P/3P/4P "Not Linked")
```

No other menu exists: there is no Options screen, no password screen, no
sound-test entry, and no selectable characters/stages. `Start` in the field
only flashes a transient `Pause` label.

### Reaching the test menu (developer gate)

Patch **one byte** in a *copy* of the ROM — this is TCRF's documented build
constant, not a cheat code:

```
file offset 0x0CBA : 3C → 5A        (0x203C "movs r0,#0x3C" → 0x205A)
```

```bash
python3 - <<'EOF'
rom = bytearray(open("Bomberman Tournament.gba","rb").read())
rom[0xCBA] = 0x5A
open("bt_debug.gba","wb").write(rom)
EOF
```

Patched SHA-256: `5973074f6217ee3d7a3156d744af5fee7371e853b082601c550365e0d2d5634a`.
Booting that copy lands on `TEST SELECT` (`screenshots/07_test_select.png`).
`Ctrl+R` returns to it after any entry.

### Exact menu paths for each screenshot

| Screenshot | Path |
|---|---|
| `01_title.png` | boot, wait through intro, ignore "Press Start" |
| `02_main_menu.png` | title → `Start` |
| `03_battle_menu.png` | main → `Down` → `A` |
| `04_pick_char.png` | above → `A` on `1 Player` |
| `05_rules.png` | above → `A` |
| `06_send_data.png` | battle menu → `Group` → `A` |
| `07_test_select.png` | patched build boot |
| `08_test_battle.png` | test menu → `BATTLE` → `A` |
| `09_test_multiboot.png` | test menu → `MULTI BOOT` → `A` |
| `10_test_char_bomb.png` | test menu → `CHAR BOMB` → `A` |
| `11/12_sound_test*.png` | test menu → `SOUND TEST`; `Right`×N |
| `13..17_minigame_*.png` | test menu → `MINI GAME`, `Right`×0..4, `A` |
| `18/19_data_*.png` | test menu → `DATA SAVE` / `DATA LOAD` |
| `20_battle_mini_fishing.png` | test menu → `BATTLE MINI` |
| `21_game_over.png` | test menu → `GAME OVER` |
| `22..24_flag_set*.png` | test menu → `FLAG SET`; `Right`/`A` |
| `25/26_field_*.png` | test menu → `FIELD`, `Right`×N, `A` |
| `27/28_staff_roll/ending.png` | test menu → `STAFF ROLL` / `ENDING` |


### Screenshot index

| File | Shows |
|---|---|
| `01_title.png` | title screen, "Press Start" |
| `02_main_menu.png` | Quest / Battle |
| `03_battle_menu.png` | 1 Player / Group / Host a Game |
| `04_pick_char.png` | Pick Char (4 slots) |
| `05_rules.png` | Rules (Computer/Rounds/Time/Tie Break/Shuffle/Skulls/Fishing/Revenge) |
| `06_send_data.png` | link "Send Data" screen, 2P/3P/4P Not Linked |
| `07_test_select.png` | TEST SELECT, 16 entries (patched build) |
| `08_test_battle.png` | entry 1 → Pick Char |
| `09_test_multiboot.png` | entry 2 → Send Data |
| `10_test_char_bomb.png` | entry 3 → Pick KARABON |
| `11_sound_test_000.png` | entry 4 → SOUND NO = 000 |
| `12_sound_test_max100.png` | after 120 `Right` presses from 000: clamps at 100 |
| `12a_sound_test_099_control.png` | one `Left` from 100 → 099 (live control) |
| `12b_sound_test_still_100.png` | `Right`, `Right` from 099 → 100, then stays 100 |
| `13_minigame_0_race.png` | entry 5, value 0 → race course |
| `14_minigame_1_ceedrun.png` | value 1 → Ceedrun duel |
| `15_minigame_2_arena.png` | value 2 → classic arena |
| `16_minigame_3_cannon.png` | value 3 → cannon game |
| `17_minigame_4_wraps_to_0.png` | value 4 → race course again (wrap) |
| `18_data_save.png` | entry 8 → Save Data, File 1/2 |
| `19_data_load.png` | entry 9 → Load Data, File 1/2 |
| `20_battle_mini_fishing.png` | entry 10 → fishing minigame |
| `21_game_over.png` | entry 12 → Game Over, Continue/Quit |
| `22_flag_set_empty.png` | entry 15 → FLAG SET, all 256 bits clear |
| `23_flag_set_16bits.png` | bits 0x00–0x0F set |
| `24_flag_set_bit2.png` | single bit 2 set, cursor on it |
| `25_field_097_house.png` | FIELD 097 → house interior |
| `26_field_270_shop.png` | FIELD 270 → shop |
| `27_staff_roll.png` | entry 14 → staff roll |
| `28_ending.png` | entry 7 → ending cut-scene |

---

## 4. Address map

### ROM

| File offset | ROM address | Contents |
|---:|---|---|
| `0x0000` | `0x08000000` | GBA header (`BOMSTORYUSA`/`ABSE`) |
| `0x00C0` | `0x080000C0` | ARM crt0 (stock) |
| `0x0C60` | `0x08000C60` | init: fills 100 bytes at `0x03002500` with 1 |
| `0x0C78` | `0x08000C78` | **scene setter** `fn(scene, arg)`: `[0x03004F30]=scene`, `[0x03002500+scene]=arg` |
| `0x0C8C` | `0x08000C8C` | **scene arg getter**: `u8[0x03002500 + [0x03004F30]]` |
| `0x0CA4` | `0x08000CA4` | main-loop scene dispatcher (`bl 0x08003660`, jump table) |
| `0x0CBA` | `0x08000CBA` | **boot scene constant** `movs r0,#0x3C` (60); `0x08000CBC` `movs r1,#1` |
| `0x0CE0` | `0x08000CE0` | 81-entry table: state 10..90 → per-screen setup (≈ `0x08000E24`+) |
| `0x0E20` | `0x08000E20` | table entry for state 90 → `0x08000F08` |
| `0x0F08` | `0x08000F08` | state-90 stub → sets next handler `0x08042981` |
| `0x42980` | `0x08042980` | **TEST SELECT** screen setup (copies 68 B string ptrs + 34 B attributes, draws 16 rows) |
| `0x43608` | `0x08043608` | shared sub-state dispatcher chained from the setup (sub-state 0 → `0x080430E0`) |
| `0x430E0` | `0x080430E0` | 16-row cursor/grid handler used by the test screens (reads key state `0x03005BFC`) |
| `0x42AA4` | `0x08042AA4` | SOUND TEST screen (uses `0x08225890`) |
| `0x42F94` | `0x08042F94` | numeric stepper used by FIELD (`Left`/`Right` −/+1, −/+10, −/+100) |
| `0x225760` | `0x08225760` | debug-menu string block (17 NUL-terminated ASCII strings) |
| `0x22581C` | `0x0822581C` | **17-entry pointer table** (title + 16 items) |
| `0x225860` | `0x08225860` | 17 × `u16` per-row attribute/icon table |
| `0x225884` | `0x08225884` | `"SOUND NO = "` |
| `0x225890` | `0x08225890` | 2-entry pointer table (`SOUND TEST`, `SOUND NO = `) |
| `0x215AE0`+ | `0x08215AE0`+ | main English text bank (story/dialogue) |

Scene graph (derived from the setter call sites and confirmed in savestates):
`60` = title/logo, `50` = logo/menu overlay with sub-modes 2..9 (2=title after
fade, 3, 4, 5=main menu, 6, 7, 8, 9), `10` = quest/field, `40/41/42` = battle
menus, `90` = `TEST SELECT`.

### RAM

| Address | Width | Meaning |
|---|---|---|
| `0x03004F30` | `u32` | current scene id (verified in savestates: 60 at title, 50 at main menu) |
| `0x03002500 + id` | `u8` | per-scene sub-mode/argument byte |
| `0x03005BFC` | `u16` | key-state mirror read by menu code (active-low) |
| `0x02035274` | 32 B | **256 runtime flags**, 1 bit each (FLAG SET) |
| `0x020369A4` / `0x020369A6` | `u16` | FLAG SET cursor row / sub-state selector |
| `0x020369B0` | — | sound-test / grid display scratch |
| `0x030024C6` | `u16` | numeric selector counter (observed `+1` per FIELD `Right`; role on other rows unverified) |

The savestate layout used for RAM evidence (needed to reproduce the reads):
`0x400` header, `0x800` palette, `0xC00` OAM, `0x1000` VRAM (96 KiB),
`0x19000` IWRAM (32 KiB), `0x21000` EWRAM (256 KiB); total `0x61000`, stored
zlib-compressed in the PNG `gbAs` chunk of mGBA `.ssN` files. KEYINPUT sits at
state offset `0x530` (IO block base `0x400` + register `0x130`).

---

## 5. Algorithm

### 5.1 Boot and the gate

```
crt0 → 0x08000CA4 (main scene loop)
  if [0x03004F30] == 0:                 ; cold boot
      fill 0x03002500..0x03002563 with 1
      scene_set(0x3C, 1)                ; ← the patched instruction
  r0 = [0x03004F30]
  if (r0-10) <= 0x50: pc = table[r0-10] ; 0x08000CE0
```

`scene_set(n, a)` = `[0x03004F30]=n; u8[0x03002500+n]=a`.

State 90's table entry (`0x08000F08`) loads handler `0x08042981`, which is
`0x08042980` in Thumb:

```
0x08042980  push; sub sp,#0x6C
            memcpy(sp+0x00, 0x0822581C, 0x44)   ; 17 string pointers
            memcpy(sp+0x44, 0x08225860, 0x22)   ; 17 u16 attributes
            load BG/palette tiles; draw 16 rows
            bl 0x08042F1C ; bl 0x08042F74
            set per-frame handler 0x08043608
```

### 5.2 Menu entries → screens

Each selected row leaves `TEST SELECT` through the normal scene setter, i.e. it
is not a separate "debug" scene system — the entries simply jump to the retail
screens (or, for FLAG SET/SOUND TEST/MINI GAME, to internal test screens).
This is why every entry looks like the shipping UI: the debug menu is a shell
over the production state machine.

### 5.3 SOUND TEST value model

`SOUND NO` is a decimal value rendered as three font tiles. `Left`/`Right`
decrement/increment it; `A` plays it. Bound: **100** (saturating upper bound,
`0` lower). The screen draws from the 2-pointer table at `0x08225890` and the
sound-name table pointed to by its second entry.

### 5.4 MINI GAME selector model

`MINI GAME n` where `n` is incremented/decremented by `Left`/`Right` and taken
**modulo 4**: after four `Right` presses the label reads `0` again and `A`
launches the value-0 screen (`screenshots/17_minigame_4_wraps_to_0.png`). The
label tracks the value; the launched screen and the label agree in all five
cases tested.

### 5.5 FLAG SET model

```
grid: 16 rows × 16 columns = 256 cells, cell (row r, col c) = flag (r<<4)|c
A pressed at cursor f:   0x02035274[f>>3] |= 1 << (f & 7)
B pressed:               leave screen
no clear/toggle control found; no persistence (RAM only, reset on power-on)
```

Verified with a savestate diff: cursor at 2, `A` → `0x02035274 + 0` changes
`0x00 → 0x04`; the grid cell at 0x02 changes from the empty glyph to the "1"
glyph (`screenshots/24_flag_set_bit2.png`). Setting 0x00..0x0F changes the whole
first row to "1" (`screenshots/23_flag_set_16bits.png`).

(The cursor is a 2-D index in scratch words at `0x020369A4`/`0x020369A6`; the
on-screen "FLAG SET 0000" label is static.)

---

## 6. Tables

### 6.1 Debug menu (state 90)

String table `0x08225760..0x08225819`; pointer table `0x0822581C` (17 entries,
`u32` LE); attributes `0x08225860` (17 × `u16`):

| # | Entry | Effect when entered |
|---:|---|---|
| — | `TEST SELECT` | title text |
| 0 | `FIELD` | warp to field/interior id shown (3 digits; `Left`/`Right` edit) |
| 1 | `BATTLE` | battle character select (`Pick Char`, 4 slots, 1P) |
| 2 | `MULTI BOOT` | `Send Data` link screen (2P/3P/4P "Not Linked") |
| 3 | `CHAR BOMB` | `Pick KARABON` screen (Karabon grid + stats + `Wins:`) |
| 4 | `SOUND TEST` | sound selector `000..100`, `A` plays |
| 5 | `MINI GAME` | `0`=race obstacle course, `1`=Ceedrun "fire up or down" duel, `2`=classic arena, `3`=cannon game (mod 4) |
| 6 | `OPENING` | replays the opening cut-scene |
| 7 | `ENDING` | plays the ending cut-scene |
| 8 | `DATA SAVE` | `Save Data`: File 1 / File 2, `Save Data`/`Exit` |
| 9 | `DATA LOAD` | `Load Data`: File 1 / File 2, `Choose a file to load.` |
| 10 | `BATTLE MINI` | fishing minigame (`Wanna know how to fish?`) |
| 11 | `TITLE DEMO` | returns to the title screen |
| 12 | `GAME OVER` | game-over screen with `Continue` / `Quit` |
| 13 | `POWER ON` | cold reset |
| 14 | `STAFF ROLL` | credits/staff-roll sequence |
| 15 | `FLAG SET` | 256-bit runtime flag editor |

Attribute table values: `0x45,0x87,0xA7,0xC7,0xE7,0x107,0x127,0x147,0x167,
0x187,0x1A7,0x1C7,0x1E7,0x207,0x227,0x247,0x267` (17 words; the first belongs to
the title row).

### 6.2 Scene ids (used by the gate)

| Id | Decimal | Screen |
|---:|---:|---|
| `0x0A` | 10 | quest/field |
| `0x28` | 40 | battle setup A |
| `0x29` | 41 | battle setup B |
| `0x2A` | 42 | battle setup C |
| `0x32` | 50 | logo/menu overlay (sub-modes 2..9) |
| `0x3C` | 60 | title/logo animation (**boot default**) |
| `0x5A` | 90 | `TEST SELECT` (**developer gate target**) |

### 6.3 Flag bitfield

| Item | Value |
|---|---|
| Base | `0x02035274` |
| Size | 32 bytes = 256 bits |
| Indexing | flag *n* = `byte[n>>3]`, bit `n&7` |
| Set | `A` at cursor |
| Clear | none on this screen |
| Lifetime | RAM only; cleared by reset |

### 6.4 Save-data screens (from the test menu)

Two files only (`File 1`, `File 2`), each showing `No Data` on a fresh cart.
The retail Quest menu hides everything except `New Game` until a save exists.

---

## 6b. Enumeration

### 6b.1 Password / cheat-code space: **0 values**

This is the primary negative result and it is bounded, not assumed:

| Search | Scope | Hits |
|---|---|---|
| `password` (case-insensitive) | whole 4 MiB | 0 |
| `pass word`, `passcode`, `pass code` | whole 4 MiB | 0 |
| `cheat` | whole 4 MiB | 0 |
| `code` (case-insensitive) | whole 4 MiB | 0 |
| `debug` | whole 4 MiB | 0 |
| `bonus` | whole 4 MiB | 0 |
| `extra` | whole 4 MiB | 0 |
| `ABCDEFGHIJKLMNOPQRSTUVWXYZ` | whole 4 MiB | 0 |
| `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` | whole 4 MiB | 0 |
| `abcdefghijklmnopqrstuvwxyz` | whole 4 MiB | 0 |
| `secret` | whole 4 MiB | 2 (story dialogue at `0x0821E281`, `0x082230B8`) |
| `hidden` | whole 4 MiB | 8 (story dialogue) |
| `unlock` | whole 4 MiB | 8 (item/door descriptions) |
| `sound test` / `staff roll` / `mini game` / `flag` | whole 4 MiB | 1 each (all inside `0x08225760`, the debug menu) |

Every menu reachable from the title (and from the debug shell, which exposes the
internal screens directly) was walked (§3). None contains a text-entry field, an
alphabet selector, a button-code prompt, or a secrets/gallery screen. The 1P
battle flow is `Pick Char` (four slots) → `Rules` → battle; no stage or character
select is presented, and the debug `CHAR BOMB` screen shows the Karabon grid
empty on a fresh cart. The story-mode pause surface did not expose a menu in the
sections played (only a transient `Pause` label).

**Published list check.** GameFAQs (archived page fetched, `477602`) lists
exactly one cheat for this game — `use elekong in muiltiplayer mode` (walk
through blocks after dying with Elekong equipped) — a gameplay trick with no
code. It is **not verified** here (requires a save with Elekong); recorded as
unverified rather than omitted. TCRF documents the test menu but publishes only
a GameShark code, which is out of scope as a code; its *target* was verified
(§6b.2). No password list exists on GameFAQs, TCRF, VGChartz or any wiki
searched, consistent with the binary.

### 6b.2 Debug menu: complete enumeration, 16 entries

All 16 entries were entered in the emulator and screenshotted (§6.1). The
string/pointer tables are the definition of the set, so the enumeration is
exhaustive by construction: 17 strings, 17 pointers, 16 selectable rows.

**Gate verification.** `0x08000CBA` holds `0x203C` in the retail ROM. With
`0x205A` the console boots directly into state 90 and the menu is fully
functional. Reproduced independently of any cheat device.

**Dead-branch analysis (why it needs the patch).** The only code sites that
write scene id `0x5A` are:

| Site | Condition |
|---|---|
| `0x08004F5C` | `scene_arg() == 0` |
| `0x0801AC30` | `scene_arg() == 1` (jump-table option 1) |
| `0x0801B3E2` | `scene_arg() == 1` |
| `0x080292E4` | `scene_arg() == 1` |
| `0x0802B5A6` | `scene_arg() == 1` (scene-50 exit dispatcher) |

`scene_arg()` is the *sub-mode byte of the current screen*, not a menu cursor.
All call sites that set scene 50 were enumerated and use sub-modes **2..9**
(`0x0800E56A`→8, `0x0801DC28`→6, `0x0802B572`→3, `0x0802B59C`→5,
`0x0803C8E6`→4, `0x08042862`→9, `0x08043340`→6, `0x08043A14`→2,
`0x080446A4`→7). Sub-mode 1 is never written for scene 50, so the
`arg==1 → scene 90` branch in the scene-50 exit path (`0x0802B538`) is
unreachable in normal play — *Derived*, and consistent with the full walk of
every menu, which never produced the test menu (*Observed*).

### 6b.3 SOUND TEST: space 101, bound proven by clamping

* Range `000..100` inclusive.
* `Right`×10 from `000` → `010` (1 per press: confirms step size).
* From `000`, `Right`×120 saturates at `100`
  (`screenshots/12_sound_test_max100.png`).
* Control that the presses are being received: at `100`, one `Left` gives
  `099` (`screenshots/12a_sound_test_099_control.png`); one `Right` returns to
  `100`; a further `Right` leaves it at `100`
  (`screenshots/12b_sound_test_still_100.png`). **Upper bound proven by
  rejection with a live control.**
* `Left` at `000` leaves it at `000` (lower clamp, same mechanism; tested).

### 6b.4 MINI GAME: space 4, bound proven by wrap

| Value | Screen (observed) |
|---:|---|
| 0 | Race obstacle course with score bar (`screenshots/13_minigame_0_race.png`) |
| 1 | Ceedrun duel: `Will Ceedrun spit fire up or down?` (`screenshots/14_minigame_1_ceedrun.png`) |
| 2 | Classic timed Bomberman arena (`screenshots/15_minigame_2_arena.png`) |
| 3 | Cannon game: `Fire the cannon to bomb the enemy.` (`screenshots/16_minigame_3_cannon.png`) |
| 4 | **= 0** (race course again) — bound proven (`screenshots/17_minigame_4_wraps_to_0.png`) |

The selector is a 2-bit field (mod 4); a fifth mini-game cannot be expressed.

### 6b.5 FIELD: warp selector, ≥271 values

Observed accepted ids and effects:

| Value | Result |
|---:|---|
| `000` | outdoor field (grass/water/trees) |
| `004` | town with houses/NPCs |
| `097` | house interior with NPC (`screenshots/25_field_097_house.png`) |
| `270` | shop interior, prices `250G`/`100G` (`screenshots/26_field_270_shop.png`) |

`Left` at `000` clamps. The field is a 3-digit decimal, so the *displayable*
space is 000..999 and at least `000..270` is expressible (both ends tested);
four ids were entered and all four loaded a scene. The number of valid ids and
the behaviour for an invalid id were not established — see §8. This makes FIELD
the only entry that produces a state unreachable from a fresh save (arbitrary
map warp).

### 6b.6 FLAG SET: space 2^256, 256 individually addressable bits

* Enumeration: 16 rows × 16 columns = 256 cells, all individually settable —
  proven by setting 0x00..0x0F and by the single-bit test at 0x02.
* Storage: `0x02035274` bit n (verified by savestate diff).
* Effect of a minted value: `A` at flag 2 → RAM `0x02035274` `0x00→0x04` and the
  grid glyph changes to `1`; 16 consecutive `A` presses → first row all `1`
  (`screenshots/23_flag_set_16bits.png`). This is the **new, unpublished state
  demonstration** for this engagement: no public source documents this screen's
  behaviour, its storage address, or that it is a bit-per-flag editor.
* Lifetime: reset clears all bits (verified by `Ctrl+R` + re-entry) — the flags
  are the runtime world/story flags, not the battery save.

### 6b.7 What "novel code" means for this title

There is no string/keypad code space to mint from, so the guide's
"unpublished code accepted in-game" deliverable is satisfied in the only honest
form available:

1. the **unpublished mechanism** (gate instruction + scene 90 + full 16-entry
   table) reproduced from a one-byte build constant, and
2. the **unpublished state** (`FLAG SET`, `0x02035274`) minted and observed
   in-game, with the storage location proven by a binary diff of emulator
   savestates, and
3. **bounded negative results** for every advertised code type (password,
   passcode, cheat code, button code), each with the search space stated.

No GameShark/CodeBreaker/memory-patch codes are presented as cheats; the byte at
`0x08000CBA` is the developer's build switch, documented by TCRF and verified
here against the instruction stream.

---

## 7. Validation evidence

**Observed (emulator screenshots / savestate reads)**

* Boot of the unpatched ROM reaches title → main menu → Quest/Battle subtrees;
  screenshots `01`–`06` are from that unpatched walk, `07`–`28` from the
  patched build.
* Boot of the one-byte-patched copy (`0xCBA: 3C→5A`) reaches `TEST SELECT`;
  every one of its 16 entries was entered (`07`–`28`).
* Savestate reads: scene id `60` on the title, `50` on the main menu
  (`0x03004F30`), sub-mode byte `5` for the main menu (`0x03002500+0x32`).
* `0x08000CBA` bytes = `3C 20` (`movs r0,#0x3C`), `0x08000CBC` = `01 21`
  (`movs r1,#1`), followed by `BL 0x08000C78`.
* SOUND TEST clamp at 100 and step of 1 (pixel-level reading of the counter).
* MINI GAME 4 launches the value-0 game.
* FLAG SET bit 2 sets bit 2 of `0x02035274`; 16 consecutive bits set the first
  row; reset clears them.
* FIELD warps at 000/004/097/270 land on four distinct maps.

**Derived (instruction-level)**

* Scene setter/getter semantics (`0x08000C78` / `0x08000C8C`), dispatch table
  at `0x08000CE0`, state-90 route `0x0F08 → 0x08042981`.
* The 17-entry string/pointer table and 16 selectable rows.
* Scene-50 sub-modes are only ever 2..9, so the `arg==1 → 0x5A` branch on that
  path cannot fire in normal play.
* FLAG SET writes bit `n` of `0x02035274` (`A`), `B` leaves the screen.

**Inferred**

* The two extra header copies (`0x3857C0`, `0x3C0CFC`) are multiboot child
  images used by `MULTI BOOT`/`Send Data` (they are header-identical and start
  with a branch stub, but the link path could not be exercised without two
  consoles).
* FLAG SET flags are the game's story/world progression flags (they reset with
  power; their readers were not individually traced).

---

## 8. Unknowns

* **FIELD upper bound / validity table.** The four ids entered (000, 004, 097,
  270) all load a real scene, and the selector accepts any value up to at least
  270 (reached by `Right`). The total number of valid ids and the behaviour for
  an invalid id (blank map vs. rejection) were not established. The display is
  3 decimal digits, so 000..999 is expressible.
* **Flag semantics.** The 256 bits at `0x02035274` are readable/writable but
  their individual meanings (which bit unlocks which event) were not mapped.
  No public documentation exists for them.
* **Unreachable-mode confirmation for all five `0x5A` sites.** Only the
  scene-50 path was proven dead statically; the other four sites are gated on
  `arg==0/1` of their own screens and were not individually driven to a state
  with that sub-mode.
* **GameFAQs Elekong trick** was not reproduced (needs an Elekong save).
* **Two-player link features** (`Group`, `Host a Game`, `MULTI BOOT`) were only
  observed in their "Not Linked" state.

---

## 9. Tooling

Everything is plain Python 3 + binutils; scripts live in
`/tmp/opencode/btournament/` for this session.

| Script | Purpose |
|---|---|
| `phase0.py` | size/hashes/header/complement/checksum, Nintendo-logo scan, `BOMSTORY`/`ABSE` copies |
| `hdr.py` | per-copy header check, byte-identical copy proof |
| `gba.py` | ROM helpers (`u8/u16/u32`, Thumb BL scanner, literal-user scanner) |
| `lit.py` | fast Thumb `LDR Rd,[pc,#imm]` scan restricted to literal-pool contents |
| `jt.py` | dump the 81-entry scene dispatch table at `0x08000CE0` |
| `callers.py` | for every `BL 0x08000C78`, show the `r0`/`r1` arguments |
| `state.py` | read mGBA PNG savestates (`gbAs` → zlib) and diff two states |
| `state_patch.py` | rewrite an mGBA savestate (analysis only) |
| `ctl.py`, `keys.py` | xdotool key/screenshot/savestate helpers for `:196` |

Tools installed: none beyond the standard toolchain already present
(`mgba-sdl 0.10.5`, `binutils-arm-none-eabi`, `xdotool`, `scrot`,
`imagemagick`, `python3` + `capstone`).

The savestate layout (§4) was derived empirically: mGBA writes
`0x400` header + `0x400` I/O + palettes/OAM/VRAM + IWRAM + EWRAM, compressed in
a PNG `gbAs` chunk (`0x61000` bytes uncompressed). KEYINPUT appears at state
offset `0x530`, which fixes the I/O block at `0x400`; scene ids read from
IWRAM `0x19000+0x4F30` match the code exactly.

Key screenshots are in `screenshots/` next to this report.

---

## 10. Legal note

No ROM, graphics, audio or text assets are redistributed here. The report
contains addresses, algorithms, table layouts and screenshots of game screens
taken during analysis. The one-byte modification discussed is applied to a
private working copy for analysis only; it is not a distributed patch and it
grants nothing a retail player can use.
