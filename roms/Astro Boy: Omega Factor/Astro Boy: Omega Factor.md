# Astro Boy: Omega Factor (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Astro Boy: Omega Factor/Astro Boy: Omega Factor.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title (`0xA0`) | `ASTROBOY` (space/NUL padded) |
| Game code (`0xAC`) | `BTAE` |
| Maker code (`0xB0`) | `8P` |
| Software version (`0xBC`) | `00` |
| Fixed byte `0xB2` | `0x96` |
| Complement check `0xBD` | `0x3A` (valid: `(0x19 − Σ0xA0..0xBC) & 0xFF`) |
| Reserved `0xBE..0xBF` | `0x0000` |
| Entry branch (`0x00`) | `EA00002E` → `0x080000C0` (ARM) |
| MD5 | `c518725055083f6096f3268cf608acda` |
| SHA-1 | `4d652c24979dd7a08ee683b32d1d8986a5511a87` |
| SHA-256 | `27d194147f65cc20319e8281e595f27309d7aef10571ba6fc13ab4375c4e9bcd` |

**Embedded GBA-header scan.** The 156-byte Nintendo logo (`24 ff ae 51 …`) occurs exactly once, at file offset `0x04` (header base `0x00`). The file is one image, not a multi-game pack; there is no second header, no `XXXX`/multiboot stub, and no warm-boot shell.

The ROM boots with six selectable languages (ENGLISH, FRANÇAIS, ITALIANO, DEUTSCH, ESPAÑOL, 日本語): this US-labelled image ships all six language banks.

## 2. Executive summary

**There is no password, code-entry, or in-game button-cheat system in this ROM.** The complete menu surface was walked in an emulator: language, title, main menu, options, Tezuka Character List (gallery), per-character bios, high-score tables (3 categories), save-slot select/copy/delete, 3-character name entry, difficulty select, pause menu, and the Omega Factor chart. No screen accepts a code, and no disassembly path implements a code validator.

The game's unlockables are progress-based, not code-based:

* **Tezuka Character List** — 47 entries, numbers `00`–`46` (table at `0x08128D10`). Entries become viewable as they are met in the story.
* **Omega Factor chart** (SELECT during gameplay) — a spatial roster that places characters into four categories (TENDERNESS / BRAVENESS / JUSTICE / EVIL), marked by large kanji nodes 善 and 悪.
* **STAGE SELECT Mode** — a fourth pause-menu item, unlocked by finishing the game on NORMAL (published). Its task class exists (`0x080149DC`) but the item is absent on a fresh save.
* **Difficulty** — EASY / NORMAL / HARD, chosen at new-game time.

A complete **developer debug subsystem** is present in the retail ROM: five editor sub-screens (character-select menu, object menu, body, damage, attack), a separate stage-select task, and a 21-string status/cheat overlay including `ENEMY CLEAR`, `GAGE MAX`, `MUTEKI` (invincible), and stat editors. It is **not reachable in the retail build**:

* its vtable `0x087BB588` is referenced from exactly two instructions, both inside the debug code itself (`0x080057A4`, `0x08007988`);
* the debug task is constructed only from `0x08005640`, whose sole caller `0x08004176` is inside the debug subsystem;
* there is no word-aligned `0x00000377` literal anywhere in the ROM (the only `0x377` byte patterns are unaligned data), and no code compares the key state against it;
* in the emulator, `Down+START` during gameplay opens the **ordinary pause menu** (`CONTINUE / RETRY / EXIT`), not the debug menu (screenshot `078_pause_try.png`).

The published access method (Sega Retro / TCRF, credited to “Labmaster”) is a CodeBreaker code that *injects* an ARM/Thumb stub into IWRAM: when `KEYINPUT == 0x0377` it writes `0x503` into `[[0x0300287C]+0x1B4]` and then resumes the intercepted indirect jump. That is external code injection, not an in-game cheat, and is out of scope here; it is decoded and mapped in §5 only as evidence for the gate.

## 3. How to reproduce

### 3.1 Environment

```bash
Xvfb :146 -screen 0 1024x768x24 &
DISPLAY=:146 openbox &
DISPLAY=:146 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 \
  "/mnt/gbacheats/roms/Astro Boy: Omega Factor/Astro Boy: Omega Factor.gba" &
```

mGBA 0.10.5 (SDL). Default keymap: **A = `x`**, **B = `z`**, **L = `a`**, **R = `s`**, **Start = `Return`**, **Select = `BackSpace`**, D-pad = arrows. Hold every key 150–350 ms; the game polls once per frame and drops short taps. The GBA viewport is the 720×480 3× area at `+152+144` on the 1024×768 root.

Savestates: `Shift+F1` saves slot 1, `F1` loads it. A state saved at 1-1 gameplay reloads deterministically (verified: walk right, `F1`, position restored).

### 3.2 Exact menu paths (all verified)

```
Power-on → language list (6) → title "PRESS START" → Start
  → START / OPTIONS
     START → SELECT DATA
         slot 1/2/3 → NAME? (3 chars) → DIFFICULTY? (EASY/NORMAL/HARD)
                   → IS THIS OK? (YES/BACK) → intro → gameplay
         COPY → COPY WHICH DATA? → COPY DATA TO WHERE?
         DELETE → confirmation
     OPTIONS → TEZUKA CHARACTER LIST → A = bio, B = back
             → HIGH SCORE → FROM BEGINNING | STAGE | BLOCK
             → LANGUAGE (6)
             → DELETE ALL DATA → "YOU WANT TO ERASE IT?" (YES/NO)
Gameplay:
  START → pause (the stage title card may appear first):
         CONTINUE / RETRY / EXIT
  SELECT → Omega Factor chart (pan with D-pad, B exits)
  pause EXIT → SELECT DATA (returns to slot select)
```

### 3.3 Published material tested

| Published item | Source | Test | Result |
|---|---|---|---|
| `Down+START` opens debug menu | Sega Retro / TCRF (with CodeBreaker active) | held `Down+START` 0.8 s in 1-1 | **No debug menu.** Ordinary pause menu opens (`CONTINUE/RETRY/EXIT`); screenshot `078_pause_try.png`. |
| Debug menu requires CodeBreaker | Sega Retro, TCRF | static decode of the published hook | Confirmed: it is an IWRAM code injection keyed on `0x0377`; not an in-game cheat. |
| STAGE SELECT from pause menu after finishing NORMAL | GameFAQs (misternull) | pause menu on a 1-1 save | 3 items only; cycling wraps `EXIT → CONTINUE`. Stage-select task exists at `0x080149DC` but is not offered. |
| Sharaku Hosuke is character #39 | GameFAQs (y3kman) | gallery table | Confirmed: index 39 in the display-name table is `Sharaku`. |
| Character list locations (Prima/IGN/Vizzed) | guides | gallery table | Names match, but guide “Character 04/24” ordering is a walkthrough order, **not** the in-game NUMBER (in-game NUMBER = table index). |

No GameShark/CodeBreaker/memory-edit code was executed; the CodeBreaker list is used only as a static lead for §5.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

### 4.1 Input and key state

| File | ROM | Meaning |
|---:|---:|---|
| `0x0C7E94` | `0x080C7E94` | per-frame key reader |
| — | `0x04000130` | `REG_KEYINPUT` (active-low) |
| — | `0x03003280` | pointer to primary key-state struct: `+0` last held, `+2` triggered, `+4` pressed, `+6` released |
| — | `0x03003298` | pointer to a second key-state struct (same layout) |
| — | `0x0300329C` | copy of the masked held word |
| — | `0x000003FF` | key mask (A,B,Select,Start,Right,Left,Up,Down,R,L) |

Held-mask values used in this report: `Down = 0x80`, `Start = 0x08`; active-low `Down+Start = 0x3FF & ~0x88 = 0x0377`.

### 4.2 Task / state machinery

| File | ROM | Meaning |
|---:|---:|---|
| — | `0x030012C0` | pointer to the current game-task object |
| `0x003858` | `0x08003858` | task dispatcher: reads `task[0]` (state), `cmp #0x16`, 23-entry jump table at `0x0800389C` |
| `0x003864` | — | `task[3]` is a one-shot “state changed / spawn” flag; cleared after use |
| `0x004164` | `0x08004164` | if `task[3] != 0`, allocates `0x40C8` bytes and calls `0x08005640` |
| `0x005640` | `0x08005640` | debug-subsystem constructor; stores vtable `0x087BB588` at `[obj+4]` |

### 4.3 Debug subsystem (present, unreachable in retail)

| File | ROM | Meaning |
|---:|---:|---|
| — | `0x087BB588` | debug vtable base |
| — | `0x087BB594` | vtable slot `+0x0C` = `0x08007934` (init), thumb bit set |
| — | `0x087BB59C` | vtable slot `+0x14` = `0x080078C0` (main) |
| `0x007934` | `0x08007934` | debug init; stores vtable `0x087BB588` |
| `0x0078C0` | `0x080078C0` | debug main loop (input wait → `0x080077C4` dispatch) |
| `0x0077C4` | `0x080077C4` | sub-screen dispatcher, switch on `obj[0x70]` values 2..8 |
| `0x0078F4` | `0x080078F4` | debug cleanup |
| `0x007730` | `0x08007730` | sub-screen: CharaSelect (labels `CharaSelect`, `Chara `, `Exit`) |
| `0x006D70` | `0x08006D70` | sub-screen: character menu (`Menu`, `Num`, `Kind`, `Insert`, `Erase`, `Ofs`, `Time`, `Pattern`, `Body`, `Damage`, `Attack`, `NewPtn`, `Arrange`, `Save`, `Ok`, `Exit`) |
| `0x006FD0` | `0x08006FD0` | sub-screen: body editor (`Left/Right/Up/Down`, `Adjust`, `Adjust_d`, `Body`, `Fix`, `Ground`, `Return`) |
| `0x0071E8` | `0x080071E8` | sub-screen: damage/guard box editor (`Rect`, `AtkErase`, `Guard`, `Return`) |
| `0x0073C0` | `0x080073C0` | sub-screen: attack editor (`Damage`, `HitWait`, `ResetHit`, `ResetId`, `Kind`, `Dir`, `Return`) |
| `0x00DD80`–`0x00E230` | `0x0800DD80`–`0x0800E230` | status/cheat overlay drawing and toggle logic |

Debug label strings live at `0x08102EFC`–`0x08103184`; stage-select labels at `0x08103474`.

### 4.4 Stage-select task (legit unlockable)

| File | ROM | Meaning |
|---:|---:|---|
| `0x0148EC` | `0x080148EC` | draw `STAGE SELECT` screen (`ROUND`, `STAGE`, `BLOCK`, `SECTION`, `EXIT`) |
| `0x0149DC` | `0x080149DC` | task main loop (waits for input, then exits) |
| `0x0149F8` | `0x080149F8` | task init; vtable `0x087BB790` |

### 4.5 Gallery / character tables

| File | ROM | Meaning |
|---:|---:|---|
| `0x1289C0` | `0x081289C0` | internal/Japanese-style name bank |
| `0x128BCC` | `0x08128BCC` | pointer table A (49 entries; entry 0 = `CHARACTER`, entries 1–47 = internal names, entry 48 = `MAX`) |
| `0x128C90` | `0x08128C90` | display (US) name bank |
| `0x128D10` | `0x08128D10` | pointer table B (48 entries; 0–46 = display names, 47 = `MAX`) |
| — | `0x128BC8` | literal `MAX` (count sentinel) |

### 4.6 Save

8 KiB EEPROM (`EEPROM_NOWAIT` descriptor string in ROM at `0x087BB574`); the written `*.sav` is 8192 bytes. A slot’s name is stored verbatim as three ASCII bytes (`AAA` observed at save-file offset `0x1289`, slot 1 base `0x1200`). The dump begins `"    MOTA"` / `"001"` followed by repeating 8-byte `FFFFFFFF 002D2D2D` records — a 16-bit-word layout artifact of the EEPROM driver, not a text field.

### 4.7 Reconnaissance counts

`strings -t x -n 4` yields 146,008 lines. Keyword counts below are raw byte subsequence counts in the whole 8 MiB image, then in a byte−1 transform of the whole image (which decodes most of the localized word/script bank). Counts are substring-inflated (e.g. `test` matches “latest”, “greatest”).

| Keyword | raw ASCII | byte−1 transform | Classification of hits |
|---|---:|---:|---|
| `password` | 0 | 0 | — |
| `pass word` | 0 | 0 | — |
| `cheat` | 0 | 2 | dialogue “HE CHEATED TO WIN” (`0x16AE84`, `0x16E839`), not a menu |
| `debug` | 0 | 0 | — (all debug UI text is plain ASCII labels, §6.2) |
| `secret` | 0 | 11 | word-list / dialogue vocabulary (`0xF757E`, …) |
| `unlock` | 0 | 1 | word-list entry “UNLOCK” (`0xF7FF5`) |
| `stage` | 2 | 6 | `STAGE SELECT` debug labels + dialogue |
| `sound` | 0 | 4 | dialogue (“SOUND SIMILAR TO…”) |
| `test` | 0 | 71 | substring noise (`latest`, `greatest`, …) |
| `mode` | 0 | 20 | substring noise |
| `extra` | 0 | 6 | substring noise |
| `gallery` | 0 | 0 | — |
| `code` | 0 | 0 | — |
| `menu` | 1 | 1 | plain `Menu` label in debug editor |
| `option` | 0 | 0 | — |
| `free` | 1 | 6 | word-list / dialogue |
| `boss` | 1 | 9 | word-list / dialogue |
| `select` | 2 | 1 | debug `CharaSelect`/`STAGE SELECT` labels |
| `continue` | 0 | 2 | word list (`0xF797C`, `0xF9D2B`) |
| `invalid` | 0 | 0 | — |
| `wrong` | 0 | 1 | word-list entry “WRONG” (`0xF7A21`) |

No keyword hit belongs to a code table: every non-debug hit is prose, a dictionary word, or part of a longer word.

## 5. Algorithm / gate model

### 5.1 Password / code validator

**None exists.** There is no `strlen`+`strcmp` validator, no alphabet/checksum table, and no keypad screen. The only text entry in the game is the 3-character save-slot label (§6.4), and its contents are stored verbatim with no comparison. The localized script banks are tokenized (common letters use sub-ASCII codes), so raw keyword counts are lower bounds only; the decisive evidence is the complete menu walk plus the absence of any code-entry screen or flag-writing validator.

### 5.2 Debug gate (derived from the published injection + static map)

Retail code has no trigger. The only known entry is the external CodeBreaker hook, decoded here as Thumb:

```
; injected at 0x03003F40, hooked over an indirect dispatch site
push {r0-r3}
nop
ldr  r0, =0x04000130          ; KEYINPUT
ldrh r0, [r0]
ldr  r1, =0x00000377          ; active-low Down+Start
cmp  r0, r1
bne  resume
ldr  r0, =0x0300287C
ldr  r0, [r0]                 ; current object pointer
ldr  r1, =0x000001B4
add  r1, r1, r0
ldr  r0, =0x00000503
str  r0, [r1]                 ; force field +0x1B4 = 0x503
resume:
pop  {r0-r3}
add  r1, r1, r0               ; (inferred) resume the intercepted indirect jump
ldr  r0, [r1]
bx   r0
```

The second published block writes an ARM stub at `0x030029D0` (`ldr r3,[pc,#0]; bx r3; .word 0x03003F41`) so the Thumb payload above is entered. `0x503` is a forced state value, not a ROM address; it is what makes the debug task appear. No in-game action writes `0x503` or `0x0377`.

### 5.3 Gallery clamp (observed)

The gallery exposes only indices `0 ≤ n ≤ unlocked_max`. On a save with only Astro (index 0) unlocked, `Left` and `Right` leave the display at `NUMBER 00` (screenshots `char_Left.png`, `char_Right.png`). The upper bound is the number of met characters; the table bound is 46.

## 6. Tables

### 6.1 Tezuka Character List — 47 entries (in-game NUMBER = table index)

| # | Display name (US table) | Internal name (JP-style table) |
|---:|---|---|
| 00 | Astro | Atom |
| 01 | Dr.O'Shay | Dr.Ochanomizu |
| 02 | Wato Chiyoko | Wato Chiyoko |
| 03 | Atlas | Atlas |
| 04 | North | North No.2 |
| 05 | Detective Tawashi | Detective Tawashi |
| 06 | Kennedy | Kenichi |
| 07 | Zoran | Uran |
| 08 | Rag | Rag |
| 09 | Prime Rose | Prime Rose |
| 10 | Epsilon | Epsilon |
| 11 | Mr.Tokugawa | Tokugawa |
| 12 | Brontus | Mont Blanc |
| 13 | Deadcross | Deadcross |
| 14 | Black Looks | Black Looks |
| 15 | Pluto | Pluto |
| 16 | Jetter Mars | Jetter Mars |
| 17 | Wally Kisagari | Higeoyaji |
| 18 | Alejo | Tamao |
| 19 | Fumoon | Fumoon |
| 20 | Pinoko | Pinoko |
| 21 | Sapphire | Sapphire |
| 22 | Pook | Pook |
| 23 | Denkou | Denkou |
| 24 | Rainbow Parakeet | Rainbow Parakeet |
| 25 | Dr.Tenma | Dr.Tenma |
| 26 | Ham Egg | Ham Egg |
| 27 | Don Dracula | Don Dracula |
| 28 | Kinsankaku | Kinsankaku |
| 29 | Skunk Kusai | Skunk Kusai |
| 30 | Blue Knight | Blue Knight |
| 31 | Magma | Ambassador Magma |
| 32 | Big X | Big X |
| 33 | Abercrombie | Shibugaki |
| 34 | Amazing Three | Amazing Three |
| 35 | Duke Red | Duke Red |
| 36 | Nuka | Nuka |
| 37 | Phoenix | Phoenix |
| 38 | Black Jack | Black Jack |
| 39 | Sharaku | Sharaku Hosuke |
| 40 | Drake | Lamp |
| 41 | Garon | Garon |
| 42 | Boon | Boon |
| 43 | Hecate | Hecate |
| 44 | Unico | Unico |
| 45 | Rock | Rock |
| 46 | Daichi | Daichi |
| — | `MAX` (count sentinel) | `MAX` |

Observed bio for 00 (screenshot `char_A.png`): “A super-robot powered by a 100,000 horsepower engine.”

### 6.2 Debug status/cheat overlay (21 strings, 17 functional entries, `0x081030D0`–`0x08103184`)

| Offset | Label | Effect |
|---:|---|---|
| `0x1030D0` | `STEP` | frame-step / pause control label |
| `0x1030DC` | `ENEMY CLEAR` | clears on-screen enemies |
| `0x1030E8` | `HIT DISP ` + `OFF`/`ON` | collision-box display |
| `0x1030FC` | `TASK DISP ` | task/entity debug display (effect undocumented; label only) |
| `0x103108` | `GAGE MAX ` | maxes life and super gauges |
| `0x103114` | `MUTEKI ` | invincibility |
| `0x10311C` | `POWER ` | stat panel header (L/R select, A +1, R max, L min) |
| `0x103124` | `LIFE` | life stat |
| `0x10312C` | `PUNCH` | punch stat |
| `0x103134` | `LASER` | laser stat |
| `0x10313C` | `SHOT` | shot stat |
| `0x103144` | `JET` | jet stat |
| `0x103148` | `SENSOR` | sensor stat |
| `0x103154` | `EVENT ` | event/cutscene viewer |
| `0x103160` | `BGM ` | music on/off |
| `0x103168` | `S ` | camera-coordinate display |
| `0x10316C` | `P ` | player-coordinate display |
| `0x103170` | `HeapAll ` | heap allocated |
| `0x10317C` | `HeapMax ` | heap maximum |
| `0x1030F4`/`0x1030F8` | `OFF` / `ON` | toggle values |

`TASK DISP`, `S`, `P`, `HeapAll`, `HeapMax`, and the six named stats are not described on the public hidden-content page, which documents only `ENEMY CLEAR`, `HIT DISP`, `TASK DISP` (“unknown”), `GAGE MAX`, `MUTEKI`, `POWER`, `EVENT`, `BGM`, and the coordinate/heap readouts.

### 6.3 Debug editors (5 sub-screens)

| Dispatcher state | ROM | Labels (order in literal pool) |
|---:|---:|---|
| 2 | `0x08007730` | `CharaSelect`, `>`, `Chara `, `Exit` |
| 3 | `0x08006D70` | `Menu`, `>`, `Num `, ` 0x`, `Kind `, `Insert`, `Erase`, `Ofs `, `Time `, `Pattern `, `Body`, `Damage`, `Attack`, `NewPtn `, `Arrange`, `Save `, `Ok`, `0x`, `Exit` |
| 6 | `0x08006FD0` | `Body`, `>`, `Insert`, `Erase`, `Left `, `Right`, `Up   `, `Down `, `Adjust `, `On`, `Adjust_d `, `On`, `Body `, `On`, `Fix `, `On`, `Ground `, `On`, `Return` |
| 7 | `0x080071E8` | `Damage`, `>`, `Insert`, `Erase`, `Rect `, `Left `, `Right`, `Up   `, `Down `, `AtkErase `, `On`, `Guard `, `On`, `Return` |
| 8 | `0x080073C0` | `Attack`, `>`, `Insert`, `Erase`, `Rect `, `Left `, `Right`, `Up   `, `Down `, `Damage `, `HitWait `, `ResetHit `, `On`, `ResetId `, `On`, `Kind `, `Dir `, `Return` |

Values `4` and `5` in the dispatcher are no-ops (`0x08007826`).

### 6.4 Stage-select fields

`STAGE SELECT` (`0x080148EC`) edits four fields with `ROUND`, `STAGE`, `BLOCK`, `SECTION`, plus `EXIT`; this is the same screen family as the completion-unlocked pause item.

### 6.5 Key masks

| Input | Held mask |
|---|---:|
| A / B / Select / Start | `0x0001` / `0x0002` / `0x0004` / `0x0008` |
| Right / Left / Up / Down | `0x0010` / `0x0020` / `0x0040` / `0x0080` |
| R / L | `0x0100` / `0x0200` |
| Down+Start (active-low) | `0x0377` |

## 6b. Enumeration

### 6b.1 Space definition per candidate system

| System | Space | Evidence |
|---|---|---|
| Password / code entry | **0.** No entry UI, no validator, no alphabet table. | Full menu surface walked; no `PASSWORD`/`INVALID` literal; no validator path to a flag word. |
| Button code | 49 combinations tested; **0** non-menu effects. | Table below. |
| Debug menu | 5 editors + 21 status strings (17 functional entries) + 4 stage fields. | §6.2–6.4, static tables. |
| Gallery | 47 entries (`00`–`46`), 2 naming tables. | §6.1; clamp observed. |
| Save-name text | 3 character cells; alphabet includes `A–Z`, `0–9`, `-`, `.`, `/` (observed), stored verbatim. No validator. | `094_up11.png` (`/`), `095_up12.png` (`-`), `089_name_up1.png` (`9`); save-file `0x1289 = "AAA"`. |
| Pause menu | 3 items on a 1-1 save; 4 with STAGE SELECT unlocked. | Wrap test below. |
| Language / difficulty | 6 / 3 options, all selectable. | screenshots `013`, `022`. |

### 6b.2 Button-space test (49 combinations)

Method: savestate reload before each combo, hold 0.6–0.8 s, screenshot, compare. Screens: title (20), gallery (15), gameplay (6), pause (8).

* Title: `Start, A, B, L, R, Select, Down+Start, Up+Start, L+R+Start, L+Select, R+Select, L+R+Select, A+B+Start, A+B+Select, Select+Start, L+R+A+B, Down+Select, Up+Select, Left+Start, Right+Start`.
* Gallery: `L, R, Start, Select, A, B, L+R, L+R+Start, L+R+Select, Select+Start, A+B+Start, Down+Start, Up+Start, L+Start, R+Start`.
* Gameplay: `Down+Start, Up+Start, L+R+Start, Select, L+R+Select, A+B+Start`.
* Pause: `Down+Start, Up+Start, L+R+Start, L+R+Select, A+B+Start, Select+Start, L+Start, R+Start`.

Result: every combination lands on a normal screen (title menu, `SELECT DATA`, pause menu, gallery, or Omega chart). `Down+Start` in gameplay is the published debug trigger and does **not** open the debug menu.

### 6b.3 Bounds proven by rejection

| Test | Input | Observed rejection |
|---|---|---|
| Gallery lower bound | `Left` at `NUMBER 00` | stays `NUMBER 00 Astro` (`char_Left.png`) |
| Gallery upper bound | `Right` with only Astro met | stays `NUMBER 00 Astro` (`char_Right.png`) |
| Pause item count | `Down`×3 then `Up` | `CONTINUE→RETRY→EXIT→CONTINUE`, `Up→EXIT`; exactly 3 items, circular (`079_dn1.png`, `079_dn2.png`, `080_up.png`) |
| Debug trigger | held `Down+Start` | ordinary pause menu, no debug overlay (`078_pause_try.png`) |
| Name field length | `Right` past cell 3 | cursor stops at cell 3; field is exactly 3 characters (`093_name2.png`) |

### 6b.4 Novel codes

**None can be minted, because the ROM has no code space.** This is a bounded negative, not a skipped step: the full menu surface was walked, the text/UI spaces were searched with counts, the published button trigger was executed and rejected, and the only hidden subsystem (debug) was proven unreachable by cross-reference and by the inert published trigger. Producing a “novel code” here would require external code injection (CodeBreaker), which the engagement scope excludes.

## 7. Validation evidence

**Observed (emulator screenshots, `/tmp/opencode/astroboy/shots/`):**
* Language list (6), title, main menu, options, gallery `NUMBER 00 Astro`, bio text, high-score `FROM BEGINNING`/`STAGE`/`BLOCK`, save select, `COPY` two-step flow, delete confirmation, name entry, difficulty, `IS THIS OK?`, 1-1 gameplay, pause menu, Omega chart (`EVIL`/`JUSTICE` kanji nodes), stage card.
* `Down+START` → normal pause menu (`078_pause_try.png`).
* Gallery clamps at `00` both directions (`char_Left.png`, `char_Right.png`).
* Pause menu wraps exactly 3 items (`079_dn1/2.png`, `080_up.png`).
* Name entry accepts and stores arbitrary 3-character names; `/` and `-` are reachable symbols.

**Derived (static):**
* Input reader and mask `0x03FF` at `0x080C7E94`.
* Debug vtable `0x087BB588` referenced only at `0x080057A4` and `0x08007988`.
* Debug constructor `0x08005640` called only from `0x08004176` (debug dispatcher).
* No literal `0x00000377` and no `cmp` against it anywhere in code; the only occurrences of `0x377` are data bytes.
* 47-entry gallery table and 48-entry display table; `MAX` sentinel.
* 21 status label strings (17 functional entries), 5 sub-editor label sets, 4 stage-select fields.
* Stage-select task class exists at `0x080149DC`/`0x080149F8`.

**Inferred (not exercised):**
* The exact gameplay effect of `TASK DISP` (label present; no published description; screen not entered).
* The save-flag bit that enables the pause `STAGE SELECT` item (published condition: finish NORMAL; task exists; item absent on the test save).
* Full semantic decoding of the localized script token encoding.

## 8. Unknowns

* The precise meaning of the forced `0x503` value in the published hook (state index vs. field), beyond “it is what makes the debug task appear”.
* Whether any regional build changes the debug gate. This exact USA `BTAE` Rev 00 image has no in-game gate.
* The exact character→quadrant mapping of the Omega Factor chart (only Astro unlocked; chart shows quadrant markers, no other nodes).
* The `TASK DISP` overlay contents (would require entering the unreachable debug menu).
* The specific save byte that records “game completed on NORMAL”.

## 9. Tooling

* mGBA 0.10.5 (`mgba-sdl`), Xvfb `:146`, openbox, `xdotool`, `scrot`, ImageMagick (`convert`, `compare`).
* `arm-none-eabi-objdump` (`-M force-thumb`) and Python `capstone` 5.0.7 for scripted disassembly.
* Python 3.13 scripts in `/tmp/opencode/astroboy/`: `ctl.py` (key/screenshot), `combos.py` (savestate + combo harness), `disa.py` (Thumb disassembler with correct address base).
* `strings -t x`, `grep -abo`, and custom ROM scanners for literal pointers, Thumb `BL` targets, and `ldr rX,[pc,#imm]` literal pools.

## 10. Legal note

No ROM, graphics, music, or extracted text is redistributed with this report. Only hashes, addresses, algorithms, menu enumerations, and the analyst’s own generated screenshots are documented.
