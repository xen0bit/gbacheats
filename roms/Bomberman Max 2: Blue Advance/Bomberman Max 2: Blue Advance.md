# Bomberman Max 2: Blue Advance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Bomberman Max 2: Blue Advance/Bomberman Max 2: Blue Advance.gba` |
| Size | 8,388,608 bytes (`0x800000`, 8 MiB) |
| Header title (`0xA0`) | `MAX2BLUEADV` |
| Game code (`0xAC`) | `AMHE` |
| Maker (`0xB0`) | `5G` (Hudson Soft) |
| Software version (`0xBC`) | `00` |
| Complement check (`0xBD`) | `0x9F` (valid) |
| Entry word (`0x00`) | `0xEA1D6CFE` → `0x08075B400` (patched; see below) |
| MD5 | `4992498ccd861daaed0557a39b4d8487` |
| SHA-1 | `da468d0c1c5af603d4d1fa006f54dbc954c48f2d` |
| SHA-256 | `0e06219600e19f29a85f2cdea498dd6901e83ecbb93053e8bc4e576a3aaabb39` |

### Patch / trainer note

This image is **not a clean commercial dump**. It carries a Mode7 cracktro:

* The header entry word is `0xEA1D6CFE`, an ARM branch to `0x08075B400`.
  A clean image would branch to `0x080000C0` (`0xEA00002E`).
* At file offset `0x75B400` (ROM `0x0875B400`) there is an appended ARM
  block. It contains the ASCII strings at `0x75EEFA`:
  `MODE7 PRESENTS`, `ON 05/31/2002`, `BOMBERMAN MAX 2`,
  `BLUE ADVANCE`, `FROM MAJESCO`, `AND HUDSON`, `GBA/USA/64MBS`,
  `SUPPLIED BY: DROPCOM!`, `GREETINGS TO JEFF'S MOM AKA THE MILFOB`.
* The block is self-contained: it contains a pointer to `0x080000C0`
  at file offset `0x75B464`, and control returns to the original
  cartridge entry point after the intro. The original crt0 at
  `0x080000C0` is intact (`12 00 a0 e3 00 f0 29 e1 ...`).
* **No trainer menu or gameplay modification was found.** The intro has
  no choices; it scrolls text and jumps to the game. The only header
  change observed is the entry word.
* The Mode7 block occupies `0x75B400`–`0x75EFA9` (last non-`0xFF` byte
  at `0x75EFA9`), inside the ROM's unused tail.

### Embedded GBA header (not a second game)

A whole-file scan for the 156-byte Nintendo logo found exactly **two**
headers: the main header at `0x0` and a second at `0x7306EC`.

A second valid GBA header exists at file offset `0x7306EC`:

* Nintendo logo at `0x7306F0`; title `MAX2BLUEADV`, code `AMHE`,
  maker `5G`, fixed `0x96`, complement `0x9F`.
* Entry `0xEA00002E` → `0x0807307AC` (base + `0xC0`).
* The image extends from `0x7306EC` to about `0x75B1C6`
  (≈`0x2AADA` bytes), immediately before the Mode7 block.
* This is the **single-pak / multiboot child image** used by
  "Single-Pak Link", not a second game or a multi-game pack. It carries
  the same title and game code.

### Save hardware

mGBA created an **8,192-byte (8 KiB / 64 Kbit) `.sav`**. That is an
EEPROM save, not SRAM/Flash. The game saves progress automatically; no
password is displayed at boot or at game over. This is consistent with a
battery-backed design and is the first structural reason a password
system is unnecessary.

---

## 2. Executive summary

**No in-game password system, no in-game button cheat, and no reachable
debug menu exists in this ROM.** The game is a normal EEPROM-save title:

* A whole-ROM case-insensitive search finds **zero** occurrences of
  `password`, `cheat`, `debug`, `secret`, `unlock`, `code`, `sound`,
  `option`, or `continue`. The only ASCII UI bank outside the Mode7
  intro is the link-mode minigame/bonus selector
  (`MINIGAME SELECT`, `BONUSGAME SELECT`, eight romanized minigame names).
* The reachable menus are: title/main menu (four items), Normal Game
  (gameplay + a menu-less "PAUSE" freeze), Battle Game and Pitch Area
  (both open the same link file-select / "Pitch Area" lobby), and
  Single-Pak Link (link check). There is no password screen, no
  alphabet keyboard, no options screen and no debug screen.
* The only simultaneous multi-button gate in the parent game's code is
  the standard **A + B + Select + Start → BIOS SoftReset** check at
  `0x0800E980`. It was confirmed in mGBA: the Mode7 intro replays.
  Subsets of that combination (L+R+Start, Select+Start, A+B+Start,
  A+B+Select) do nothing, proving the gate needs all four bits.
* The only published in-game secret for this title is a gameplay
  unlockable (100 jump-rope jumps → Turtle King), not a code. Public
  Action Replay / CodeBreaker lists exist but are memory edits and are
  outside this engagement's scope.
* The only "code-like" developer leftover is the ASCII
  minigame/bonus-game selector at `0x08011410` (mode `0x23` in the
  43-entry screen table). It is a link-mode screen, not a cheat menu.
  It is fully mapped in §4 and §6, including all eight labels.

Because there is no validator and no input alphabet, there is no novel
password to mint. The deliverable is the **bounded negative** required
by guide §0.2 item 5: the menu space, the text space, the alphabet
space and the button space are all enumerated below, with the accepted
and rejected inputs recorded.

---

## 3. How to reproduce

### Emulator and display

```bash
export DISPLAY=:191
export SDL_AUDIODRIVER=dummy
Xvfb :191 -screen 0 1280x900x24 &
DISPLAY=:191 openbox &
/usr/games/mgba -3 "roms/Bomberman Max 2: Blue Advance/Bomberman Max 2: Blue Advance.gba" &
```

mGBA 0.10.5 (`mgba-sdl`), 3× scale (720×480 viewport), 1280×900 Xvfb.
`mgba-qt` 0.10.5 was used only for its debugger console in the optional
mode probe; the menu evidence comes from the SDL build.

### Keymap (mGBA SDL defaults)

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Hold keys 120–200 ms. Use `Tab` (fast-forward) to pass the Mode7 intro.
Save/load state with `Shift+F1` / `F1`; a title-screen state is kept at
`roms/Bomberman Max 2: Blue Advance/Bomberman Max 2: Blue Advance.ss1`.

### Boot path

1. Mode7 cracktro (~50–60 s at 1×; `Tab` makes it ~10 s).
2. Press Start on the cracktro.
3. Hudson/Majesco story intro: press Start again.
4. Title / main menu: `Normal Game`, `Battle Game`, `Pitch Area`,
   `Single-Pak Link`.
5. `Normal Game` resumes the existing EEPROM save at Garden Stage
   `1-01` and plays the "Receive Charaboms through the Teleporter!"
   tutorial. Dialogue advances with A.
6. In a level, Start shows the animated `PAUSE` marker. The game
   freezes, but **no pause menu is drawn**; D-pad/A/Start only toggle
   the pause state.

### Menu paths tested

| Path | Result |
|---|---|
| Title → Normal Game | gameplay at 1-01 (save resumed) |
| Title → Battle Game | `Pitch Area` file select (`File 1/2/3`, 0 %) |
| File select → File 1/2 | `Pitch Area` lobby: `Select Area! GardenStage`, `Connecting…` / `Waiting for opponent.` |
| Title → Pitch Area | same file select and lobby as Battle Game |
| Title → Single-Pak Link | two-GBA icon screen with `Checking…` (loops with no cable) |
| Title → Select / L / R | no change |
| Title → pause → D-pad / A / Start | no menu; only freeze/unfreeze |
| Title → predecessor sound-test sequence | no sound test; final A selected Normal Game |
| Title → A+B+Select+Start | BIOS SoftReset; Mode7 intro replays |
| Title → L+R+Start / Select+Start / A+B+Start / A+B+Select | no reset, no visible change |

Evidence screenshots (GBA viewport crops unless noted, in
`/tmp/opencode/bmaxblue/`):

| File | Content |
|---|---|
| `ev01_mode7_intro.png` | Mode7 cracktro |
| `ev02_game_intro.png` | Hudson story intro |
| `ev03_title_menu.png` | four-item title/main menu |
| `ev04_normal_game.png` | Normal Game, Garden Stage 1-01 |
| `ev05_pause.png` | in-level `PAUSE` freeze (no menu) |
| `ev06_battle_file_select.png` | Battle Game file select |
| `ev07_pitch_lobby.png` | Pitch Area link lobby |
| `ev08_singlepak_check.png` | Single-Pak Link `Checking…` |
| `ev09_softreset_confirmed.png` | Mode7 intro after A+B+Select+Start |
| `ev10_prev_game_code_rejected.png` | predecessor code sequence did nothing; A started Normal Game |

---

## 4. Address map

File offset → ROM address is `rom_address = 0x08000000 + file_offset`.
All values below are little-endian.

### Header, patch, embedded image

| File offset | ROM address | Meaning |
|---:|---:|---|
| `0x000000` | `0x08000000` | ARM entry branch (`0xEA1D6CFE` → `0x08075B400`) |
| `0x0000C0` | `0x080000C0` | original crt0 entry, intact |
| `0x7306EC` | `0x087306EC` | embedded multiboot header (single-pak child) |
| `0x75B400` | `0x0875B400` | Mode7 cracktro entry |
| `0x75B464` | `0x0875B464` | literal pointer to `0x080000C0` inside cracktro |
| `0x75EEFA` | `0x0875EEFA` | `MODE7 PRESENTS` text |

### Input

| Address | Meaning |
|---:|---|
| `0x04000130` | GBA `KEYINPUT` (active-low) |
| `0x08001D70` | per-frame key scan: reads `KEYINPUT`, inverts it |
| `0x0800059E` | boot/multiboot helper: when `*(u8*)r3 == 2`, a held A triggers `RegisterRamReset(0xE0)` and a jump to `0x08000000` |
| `0x03005DE0` | `u16` held keys, active-high (`A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`) |
| `0x03005DE4` | `u16` newly pressed keys (`held & ~prev`) |
| `0x0800E980` | multi-button gate: held `& 0xC == 0xC`, `& 1`, `& 2` → SoftReset |
| `0x08067428` | BIOS SoftReset trampoline (`svc 0`) |
| `0x0873592A` | the multiboot child image's own key scan, writing `0x03004C68`/`0x03004C6C` |

### Screen state machine

| Address | Meaning |
|---:|---|
| `0x03002248` | `u16` current screen/mode index |
| `0x0806D794` | table of 43 mode handlers (`0x00`–`0x2A`), one `u32` each |
| `0x0800E9AC` | dispatcher: `handler = table[*(u16*)0x03002248]; blx handler` |
| `0x0800E9D0` | init/reset: clears several state blocks, sets mode `2` |
| `0x0806B924` | function pointer to the dispatcher in the per-frame callback table |

Observed: on the four-item title/menu screen,
`*(u16*)0x03002248 == 2`; table entry `0x02` is `0x0800EB25`.

### Minigame / bonus-game selector

| Address | Meaning |
|---:|---|
| `0x08011410` | handler (Thumb pointer `0x08011411`), mode `0x23` |
| `0x03004A3C` | category: `== 2` → minigame list, otherwise bonus-game list |
| `0x0800E688` | text draw helper, args `(x, y, string_ptr, buffer, 0)` |
| `0x0806DAE0` | `"MINIGAME SELECT"` |
| `0x0806DAF0` | `"NAWATOBI"` |
| `0x0806DAFC` | `"MATOATE"` |
| `0x0806DB04` | `"KENKENPAPA"` |
| `0x0806DB10` | `"NAKAMASAGASI"` |
| `0x0806DB20` | `"BONUSGAME SELECT"` |
| `0x0806DB34` | `"BAROMDARAKE"` |
| `0x0806DB40` | `"MOGURAHOREHORE"` |
| `0x0806DB50` | `"JUMPRACE"` |
| `0x0806DB5C` | `"BLOCKKICK"` |
| `0x0806DB68` | `u32 0x3E` followed by eight code pointers `0x0801310D`…`0x080131DA` |
| `0x0806D6C2` | 128-byte ASCII→tile map used by the text path |
| `0x08175980` | larger font/ASCII mapping tables (byte and u16 forms) |

Mode index for the selector: `(0x0806D820 - 0x0806D794) / 4 = 0x23`.

### Save

| Item | Value |
|---|---|
| `.sav` size | 8,192 bytes (EEPROM 64 Kbit) |
| Boot behaviour | continues existing save; no file-select or name-entry screen |
| Save/load UI | none reachable in Normal Game; pause is freeze-only |

---

## 5. Algorithm

### 5.1 Per-frame input scan (0x08001D70)

```c
uint16_t raw  = *(volatile uint16_t*)0x04000130;  // active-low
uint16_t held = (~raw) & 0x03FF;
uint16_t pressed = held & ~prev_held;              // 0x03005DE4
prev_held = held;                                  // 0x03005DE0
```

The key state is global: any screen can read `0x03005DE0` (held) or
`0x03005DE4` (newly pressed). There is no per-screen remapping.

### 5.2 Soft-reset gate (0x0800E980)

Called once per frame from the mode dispatcher:

```c
uint16_t held = *(uint16_t*)0x03005DE0;
if ((held & 0x000C) == 0x000C &&   // Select + Start
    (held & 0x0001) != 0 &&        // A
    (held & 0x0002) != 0) {        // B
    soft_reset();                  // 0x08067428 -> BIOS svc 0
}
```

This is the only simultaneous multi-button gate in the parent game's
code. It does not require the four buttons to be the *only* keys held.

### 5.3 Screen dispatcher (0x0800E9AC)

```c
void dispatch(void) {
    uint16_t mode = *(uint16_t*)0x03002248;
    void (*handler)(void) = (void(*)(void))mode_table[mode]; // 0x0806D794
    handler();
    check_soft_reset();
}
```

### 5.4 Minigame/bonus selector (mode 0x23, 0x08011410)

```c
void screen_23(void) {
    setup_bg_and_palette();
    const char *title;
    const char *item[4];
    if (*(uint16_t*)0x03004A3C == 2) {
        title = "MINIGAME SELECT";
        item[0] = "NAWATOBI";      item[1] = "MATOATE";
        item[2] = "KENKENPAPA";    item[3] = "NAKAMASAGASI";
    } else {
        title = "BONUSGAME SELECT";
        item[0] = "BAROMDARAKE";   item[1] = "MOGURAHOREHORE";
        item[2] = "JUMPRACE";      item[3] = "BLOCKKICK";
    }
    draw_text(8, 2, title);
    for (int i = 0; i < 4; i++)
        draw_text(5, 6 + 2*i, item[i]);
}
```

This is a link-mode menu. It is not a cheat screen and contains no
password entry or flag-setting code. `0x03004A3C` takes values `0`, `1`
or `2` in the battle setup code; only `2` selects the minigame list.

### 5.5 Password validator

There is none. No routine in the ROM reads a character buffer, measures
a password length, or compares against a code table. The only UI path
that consumes the ASCII bank is the minigame-name draw above.

---

## 6. Tables

### 6.1 Title / main menu

The title screen exposes exactly four items; the cursor wraps within
these four and there is no fifth entry:

1. `Normal Game`
2. `Battle Game`
3. `Pitch Area`
4. `Single-Pak Link`

`Battle Game` and `Pitch Area` both lead to the same link file-select
(`File 1/2/3`, each 0 %) and then to the `Pitch Area` lobby. They are
link modes; the lobby prints `Connecting…` and then
`Waiting for opponent.` with no cable.

### 6.2 Minigame / bonus-game labels (ASCII, ROM-resident)

| Address | String |
|---:|---|
| `0x0806DAE0` | `MINIGAME SELECT` |
| `0x0806DAF0` | `NAWATOBI` |
| `0x0806DAFC` | `MATOATE` |
| `0x0806DB04` | `KENKENPAPA` |
| `0x0806DB10` | `NAKAMASAGASI` |
| `0x0806DB20` | `BONUSGAME SELECT` |
| `0x0806DB34` | `BAROMDARAKE` |
| `0x0806DB40` | `MOGURAHOREHORE` |
| `0x0806DB50` | `JUMPRACE` |
| `0x0806DB5C` | `BLOCKKICK` |

These are the only English/romanized UI strings stored as plain ASCII
outside the cracktro. The normal game UI is stored as font/glyph
indices, which is why a raw `strings` scan does not find
`Garden Stage`, `Select Area!` or the menu labels.

### 6.3 Mode table (0x0806D794, 43 entries)

```
00 0800e9d1  01 0800eb21  02 0800eb25  03 0800ed0d
04 0800ef85  05 0800f2ad  06 0800f2d5  07 0800f469
08 0800f4c5  09 0800f51d  0a 0800f765  0b 0800f7dd
0c 0800f7e1  0d 0800f7fd  0e 0800fc2d  0f 0801007d
10 080100a9  11 08010305  12 0801038d  13 08010391
14 08010395  15 08010399  16 0801039d  17 080104dd
18 08010969  19 08010c7d  1a 08010e09  1b 08010ee9
1c 080112a9  1d 080112ad  1e 080112b1  1f 08011969
20 08011985  21 080119a9  22 08011319  23 08011411
24 080115f9  25 08011615  26 080117ed  27 08011829
28 08011835  29 08011879  2a 080118e9
```

`0x02` was observed active on the four-item title/menu screen.
`0x23` is the minigame/bonus selector. The remaining entries are
battle, story and UI handlers; no other handler references the ASCII
minigame bank, and no password/debug string was found among them.

### 6.4 Button masks

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

### 6.5 Keyword search counts

Whole-ROM, case-insensitive byte counts:

| Keyword | Count | Notes |
|---|---:|---|
| `password` | 0 | — |
| `cheat` | 0 | — |
| `debug` | 0 | — |
| `secret` | 0 | — |
| `unlock` | 0 | — |
| `code` | 0 | — |
| `sound` | 0 | — |
| `option` | 0 | — |
| `continue` | 0 | — |
| `bonus` | 1 | only `BONUSGAME SELECT` |
| `minigame` | 1 | only `MINIGAME SELECT` |
| `select` | 2 | the two selector titles |

`strings -t x -n 4` produced 49,164 candidate lines (graphics noise
dominates); a printable-run count gives 47,643 runs of ≥4 printable
bytes, 8,134 of ≥8, and 8,625 unique alphabetic tokens of length ≥4.
None of those tokens is a password, cheat, debug or secret label.
469 valid GBA LZ77 blocks were found and decompressed; none contained
`password`, `cheat`, `debug`, `secret`, `unlock`, `code` or `select`.

---

## 6b. Enumeration

### 6b.1 Space definition

| Space | Definition | Size / result |
|---|---|---|
| Password space | alphabet × length × checksum | **0** — no entry screen, no alphabet table, no length check, no validator |
| Button-sequence space | 10 buttons, ordered sequences and simultaneous chords | only one simultaneous gate exists: `0x0F` (A+B+Select+Start) → SoftReset. No ROM sequence table and no per-press progress counter were found. |
| Link minigame space | 4 minigames + 4 bonus games | 8 entries, all named and addressed in §6.2; link-gated |
| Unlockable space | gameplay flags | published Blue-version unlock: 100 jump-rope jumps → Turtle King. This is a gameplay counter, not a code. |
| Charabom slots | 30 slots, 2 unused | TCRF documents slots 29/30 (Fly Shark, Elemouse) behind RAM flags `0x02005CC0`/`0x02005CD0`; memory edit, out of scope |

No password alphabet exists. The only long printable tables in the ROM
are font/tile maps (e.g. `0x08175980`, `0x0806D6C2`), not input
alphabets. There is no 26/32/36-symbol code alphabet and no
fixed-length code buffer.

### 6b.2 Novel codes

**None can be minted, because no code validator exists.** This is not
an unfinished search: the negative is established by

1. an empty text space (`password`/`cheat`/`code`/`debug` = 0),
2. an empty alphabet space (no code alphabet table),
3. a disassembled input path with exactly one multi-button gate
   (the hardware SoftReset),
4. a fully walked reachable menu tree with no password or debug entry,
5. a save system that makes passwords unnecessary (8 KiB EEPROM).

The closest thing to an unpublished "code" is the link selector's
eight labels; these are menu entries, not accepted inputs. They are
enumerated here with addresses and the category variable that selects
the two lists.

### 6b.3 Bounds proven by rejection

| Input | Where | Result |
|---|---|---|
| A+B+Select+Start (`0x00F`) | title | **accepted**: BIOS SoftReset, Mode7 intro replays (`ev09`) |
| L+R+Start (`0x308`) | in-level | **rejected**: no reset, no visible change |
| Select+Start (`0x00C`) | in-level | **rejected**: no reset, no visible change |
| A+B+Start (`0x00B`) | in-level | **rejected**: no reset, no visible change |
| A+B+Select (`0x007`) | in-level | **rejected**: no reset, no visible change |
| Bomberman MAX (GBC) sound-test sequence: R,L,R,R,L,L,R,L,R,L,L,R,A | title | **rejected**: no sound test; the final A selected Normal Game (`ev10`) |

The Select+Start test is the important bound: `0x0C` is a subset of
`0x0F`, but it is rejected. The gate therefore requires all four
buttons, not just the Select/Start pair.

No published password or button code exists for this title to test.
The public lists are:

| Source | Content | Test result |
|---|---|---|
| GameFAQs cheats page (Wayback capture 2026-02-17) | three endings, Red-only jump-rope unlock | no code strings; nothing to enter |
| TCRF `Bomberman_Max_2` (Wayback capture 2025-04-15) | unused Charaboms 29/30 via RAM `02005CC0`/`02005CD0` | memory edit, outside scope |
| Japanese Bomberman cheat compendium (menokenkou) | Blue: 100 jump-rope jumps → Turtle King | gameplay unlock, no code |
| Ethereal Games / libretro `.cht` | Action Replay / CodeBreaker codes | memory edits, outside scope |

### 6b.4 Why the negative is complete for this ROM

* Every reachable screen was walked: title (4 items), Normal Game,
  in-level pause, Battle Game file select, Battle/Pitch lobby,
  Single-Pak Link check.
* No options entry was found on any reachable screen: Select/L/R on the
  title and all D-pad/A/Start inputs on the pause screen produced no new
  screen.
* The only unvisited screens are downstream of a successful link
  connection (battle setup and the minigame/bonus selector). Their
  entry screens were observed; their code and all eight labels are
  mapped statically in §4/§6.
* The entire button-input surface was classified. There are three
  direct `KEYINPUT` readers: the boot-time A check at `0x0800059E`,
  the main per-frame scan at `0x08001D70`, and the multiboot child's
  scan at `0x0873592A`. In the parent game, 16 code sites read the
  held word `0x03005DE0` and 71 read the pressed word `0x03005DE4`;
  only `0x0800E980` combines three masks into a simultaneous chord.
  All other multi-mask sites are ordinary Up/Down/A/B menu navigation.
  The boot check is single-button (A) and only resets the machine; the
  child scan belongs to the downloaded multiboot image, not the parent
  game.

---

## 7. Validation evidence

### Observed (emulator)

* Mode7 cracktro plays from the patched entry and hands control to the
  original game (`ev01`).
* Hudson story intro then four-item title menu (`ev02`, `ev03`).
* Normal Game resumes Garden Stage 1-01; dialogue and gameplay
  (`ev04`).
* Start freezes the game and draws only `PAUSE`; no menu appears
  (`ev05`).
* Battle Game → `Pitch Area` file select → link lobby with
  `Connecting…` / `Waiting for opponent.` (`ev06`, `ev07`).
* Pitch Area → the same file select/lobby.
* Single-Pak Link → two-GBA `Checking…` screen (`ev08`).
* A+B+Select+Start resets; the Mode7 intro replays (`ev09`).
* L+R+Start, Select+Start, A+B+Start and A+B+Select do not reset.
* The predecessor game's sound-test sequence does nothing; A then
  starts Normal Game (`ev10`).
* An 8,192-byte `.sav` is created (EEPROM).

### Derived (disassembly)

* `0x08001D70` is the per-frame key scan; `0x03005DE0`/`0x03005DE4`
  hold held/pressed state.
* `0x0800E980` is the only simultaneous multi-button gate; it calls
  BIOS SoftReset at `0x08067428`.
* `0x0806D794` is a 43-entry handler table indexed by `0x03002248`;
  `0x0800E9AC` is the dispatcher.
* `0x08011410` is the minigame/bonus selector; its ASCII labels and
  category variable `0x03004A3C` are mapped.
* The Mode7 block is appended in unused space and returns to
  `0x080000C0`; the original crt0 is intact.
* The embedded header at `0x7306EC` is a multiboot child image, not a
  second game.
* `0x08000584`/`0x0800059E` is a boot/multiboot helper: when the byte
  pointed to by `r3` is `2`, holding A calls `RegisterRamReset(0xE0)`
  and jumps to `0x08000000`. It is a single-button reset helper, not a
  cheat sequence.

### Inferred

* The minigame/bonus selector is link-only. Its position in the mode
  table and its use of the battle-mode category variable strongly
  indicate this, but it was not reached in single-cart play because
  no second GBA/link peer was available.
* The eight labels correspond to the four minigames and four bonus
  games of the link mode; the exact in-game rules were not exercised.
* The 100-jump Turtle King unlock is a gameplay counter, not a code;
  it was not performed (would require completing 100 jumps in the
  link minigame).

---

## 8. Unknowns

* Downstream link-mode screens (battle setup, minigame/bonus selector)
  were not entered dynamically; only their entry screens and their
  static code/labels are documented. This does not affect the cheat
  conclusion, because those screens are not password/code gates.
* The mode table's 43 handlers were not each mapped to a named screen;
  only mode `0x02` (title) and mode `0x23` (selector) are pinned.
* The two unused Charaboms (Fly Shark, Elemouse) are reachable by RAM
  flags documented by TCRF; no in-game unlock was found and memory
  edits are outside scope.
* The Mode7 patch could in principle modify bytes other than the entry
  word; no such modification was observed, and the original crt0 and
  the intro's return pointer are intact.
* The multiboot child image at `0x7306EC` was identified and its key
  scan was located, but its own menus were not walked independently.
  It is the program downloaded to a second GBA for Single-Pak Link,
  not the main single-player game.

---

## 9. Tooling

* `mgba-sdl` 0.10.5 (`/usr/games/mgba`) under Xvfb `:191` + openbox.
* `mgba-qt` 0.10.5 debugger console (optional mode probe and memory
  reads; not used for the cheat conclusion).
* `arm-none-eabi-objdump -D -b binary -m arm -M force-thumb`.
* Python 3 + Capstone 5.0.7 scripts in `/tmp/opencode/bmaxblue/`:
  * `rtool.py` — Thumb disassembly with resolved PC-relative literals,
    BL-target scan, literal-pointer scan.
  * `scan_lit.py` — finds every Thumb `LDR` that loads a chosen literal
    and follows the code that uses it.
  * `lz.py` — GBA LZ77 (`0x10`) scanner/decompressor (469 blocks).
  * `k.py` — xdotool key helper.
  * `shot.sh` — window capture + 720×480 crop.
* `strings`, `xxd`, `md5sum`, `sha1sum`, `sha256sum`, ImageMagick,
  `xdotool`, `scrot`.

Reproduction of the static claims:

```bash
# 1. header + hashes
xxd -l 0x200 game.gba
md5sum game.gba; sha1sum game.gba; sha256sum game.gba

# 2. keyword counts (all zero except bonus/minigame/select)
python3 - <<'PY'
rom=open("game.gba","rb").read().lower()
for k in (b"password",b"cheat",b"debug",b"secret",b"unlock",b"code"):
    print(k, rom.count(k))
PY

# 3. input scan and SoftReset gate
python3 rtool.py d 0x08001d70 20
python3 rtool.py d 0x0800e980 20

# 4. mode table and selector
python3 rtool.py d 0x0800e9ac 20
python3 rtool.py d 0x08011410 60
```

---

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed with
this report. Only hashes, addresses, short menu labels needed for
identification, and the analyst's own screenshots of menu states are
included. The ROM remains the property of its rights holders.
