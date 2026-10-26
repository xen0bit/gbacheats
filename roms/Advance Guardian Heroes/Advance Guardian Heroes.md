# Advance Guardian Heroes (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Advance Guardian Heroes/Advance Guardian Heroes.gba` |
| Size | 8,388,608 bytes (8 MiB, 0x800000) |
| Header title | `ADVANCE GH` |
| Game code | `BGCE` |
| Maker code | `41` (Ubisoft) |
| Version | 0x00 (Rev.00) |
| Entry branch | `0xEA00002E` (ARM `b 0x080000C0`) |
| Header complement | 0x3A (matches computed) |
| Header checksum | 0x29D9 (matches computed) |
| MD5 | `a26c440065d89f56275644ffa34140ef` |
| SHA-1 | `d518d0a4818cc356ed79b29bc3c0e2264c0c2d07` |
| SHA-256 | `9b34f8aa61f9b3065bf5d2c5816f259c3ce348ba5a507c83aa9343690e0bdb4c` |

Embedded-header scan: the 156-byte Nintendo logo occurs exactly once, at file
offset `0x4` (header base `0x0`). This is a normal single-image ROM, not a
multi-game pack. File offset + `0x08000000` = ROM address throughout this
report.

## 2. Executive summary

The prior triage (“no in-game cheats”) is **wrong**. The ROM contains a
developer debug mode, reachable with an in-game button sequence, and the
sequence gate, the flag it sets, and the debug menu it unlocks were all
reversed and verified in mGBA.

The published code is:

> At the Treasure logo, quickly press **Right, Left, L, R, Up, Select,
> Select**.

It sets a single IWRAM byte, `0x03001D7D`, to 1. That flag is read by the
pause menu (Right opens an in-game DEBUG menu), by the story-mode screen
(displays a STAGE selector), and by the menu/options code (TIME ATTACK and
ENDLESS appear on the main menu, and OPTIONS gains LANGUAGE, SOUND TEST,
ANIMATION and EVENT CHECK).
The flag is RAM-only and is lost on reset, exactly as GameFAQs says.

The gate is not a table and not a checksum: it is a 7-state equality matcher at
`0x080042F8`, fed by the pressed-key word. It accepts **exactly one** 7-press
string out of 10^7 possible strings. Any other non-zero press at any position
sets a permanent fail bit; zero-key frames are ignored, so a key may be held
without breaking the sequence as long as the whole sequence finishes inside the
Treasure-logo task window.

Beyond the published code, the report delivers:

* the complete hidden stage table (110 entries, 108 reachable) including six
  openings, twelve endings, Game Over, Staff Edit, Endless, Time Attack,
  Manual and Tutorial entries;
* an unpublished stage value that was entered and observed: index **2 =
  `GOVER`** loads the GAME OVER sequence, and index **104 = `Op-1`** loads an
  opening cutscene;
* the complete in-game DEBUG menu semantics (9 rows), including the exact
  player fields written by HP/MP/AP/EXP MAX and the Get/Clear character-flag
  tables;
* an unpublished DEBUG-menu state (ClearLevel=SuperHard, Get/Clear HeavyGear=OK,
  Clear En=OK) and a demonstrated bound: the Get row refuses to toggle the last
  three character indices (En, Hyou, Rai), while the Clear row accepts them.

No GameShark/CodeBreaker/memory-edit code was used. All effects were produced
by the game’s own menus.

### Public codes checked

* GameFAQs (archived 2025-03-29) “Unlock All Characters”: *“At the Treasure
  logo … quickly enter Right, Left, L, R, Up, Select, Select. You’ll hear Zur
  laugh … Everything will be unlocked until you restart the game.”* This is
  the same sequence reversed in §5.1 and it was reproduced from a cold boot.
* GameFAQs unlockables (Time Attack = clear Normal, Endless = clear Hard, new
  characters): with debug on, the main menu showed **TIME ATTACK** and
  **ENDLESS**, and the RECORDS gallery showed all 21 character portraits.
* TCRF’s debug-mode page documents the same trigger and the debug menus; it was
  used to know where to look, and every claim repeated here was re-verified in
  this exact ROM revision.
* No password screen, password table or password alphabet exists in this ROM.
  The only published in-game code is the button sequence.

### Reconnaissance counts

* `strings -t x -n 3` over the 8 MiB image: 175,056 lines;
  `strings -t x -n 4`: 80,815 lines.
* Case-insensitive sweep for `pass|password|cheat|debug|secret|unlock|sound
  test|stage select|select stage|hidden|extra|bonus|gallery|option|code` over
  the `-n 3` output produced only two hits: `DEBUG` at file `0xE935C` and
  `STAGE ` at file `0xE9110`.
* A ±0x80-byte context dump showed a dedicated debug string bank at
  `0xE9354..0xE93F0`: `STEP`, `DEBUG`, `TASKDISP `, `ON`, `OFF`, `HP MAX`,
  `MP MAX`, `AP MAX`, `EXP MAX`, `BGM `, `ClearLevel `, `NG`, `Easy`,
  `Normal`, `Hard`, `SuperHard`, `Get `, ` NG`, ` OK`, `Clear `.
* Further ASCII label searches found the animation-checker bank at
  `0xEB15C+` (`ANIME CHECKER`, `CharNo:`, `AnimeNo:`, `Palet:`,
  `CenterMark`, `BackColor`, `[LOOP]`, `PAT`, `SPEED`, `TIME`, `ATIME`,
  `Damage`, `Body`, `Guard`, `Attack`, `HPD`, `MPD`) and the
  event/staff bank at `0x468700+` (`MSG NO:`, `STATUS:`, `EVENT CHECKER`).
* The visible in-game text is tile-encoded, so absent ASCII menu strings are
  expected and are not evidence against a menu.

## 3. How to reproduce

### Emulator and keys

* mGBA 0.10.5 SDL (`/usr/games/mgba`), 3× scale, `SDL_AUDIODRIVER=dummy`.
* Xvfb `:123` + openbox.
* Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys.
* Hold each key 60–120 ms and leave ~60–100 ms between presses.

### Getting debug mode

1. Boot the ROM and watch for the **Treasure** logo (it follows the Ubisoft
   logo and a black frame).
2. As soon as the Treasure logo appears, press, in order and quickly:
   `Right`, `Left`, `a` (L), `s` (R), `Up`, `BackSpace` (Select),
   `BackSpace` (Select).
3. Success is audible: sound effect `0xB8` plays (the “Zuru laugh”), and the
   main menu grows from 5 to 7 items (STORY MODE, VS MODE, TRAINING, TUTORIAL,
   **TIME ATTACK, ENDLESS**, OPTIONS).
4. Time the whole sequence to fit inside the logo task (~1.2 s of presses is
   comfortable). Starting after the logo, or stretching the presses over
   ~3 s, fails.

### Reaching the hidden screens

* **Options (debug)**: main menu → OPTIONS. Nine rows: DIFFICULTY, COMMAND
  LIST, STAFF LIST, DELETE SAVE, DELETE RECORD, LANGUAGE, SOUND TEST,
  ANIMATION, EVENT CHECK.
* **Stage select**: main menu → STORY MODE. The STAGE line appears at the
  bottom right; Left/Right change it. Accept 1 PLAYER, pick a character, start.
* **In-game DEBUG menu**: start any mode, press Start to pause, then press
  **Right**. Rows: TASKDISP, HP MAX, MP MAX, AP MAX, EXP MAX, BGM, ClearLevel,
  Get \<character\>, Clear \<character\>.
* **Records/gallery**: main menu → TIME ATTACK (or ENDLESS) → RECORDS.

### Flag verification without screenshots

mGBA savestates (`.ssN`) are PNG files with a `gbAs` chunk holding a
zlib-compressed state. In this ROM the decompressed layout is:

| State offset | RAM |
|---|---|
| `0x19000` | IWRAM `0x03000000..0x03007FFF` |
| `0x21000` | EWRAM `0x02000000..0x0203FFFF` |

Therefore `state[0x19000 + 0x1D7D]` is the debug flag. This was used to score
all acceptance/rejection tests below without walking menus.

## 4. Address map

| ROM address | File offset | Meaning |
|---|---|---|
| `0x080042F8` | `0x42F8` | Button-sequence matcher (Thumb) |
| `0x08004328` | `0x4328` | 7-entry jump table: `448, 452, 45C, 46A, 474, 47E, 48E` |
| `0x08004396` | `0x4396` | `*(u8*)0x03001D7D = 1` (debug enable) |
| `0x0800439C` | `0x439C` | plays SE `0xB8` |
| `0x080043AC` | `0x43AC` | sets permanent fail bit `task+0x7B = 1` |
| `0x08004198` | `0x4198` | caller: `BL 0x080042F8` in the logo/intro task |
| `0x08003F90` | `0x3F90` | logo/intro task state jump table |
| `0x03001D7D` | — | **debug-mode flag (IWRAM byte)** |
| `0x080122F0` | `0x122F0` | pause menu reads flag, Right → debug menu (state 5) |
| `0x0800593A` | `0x593A` | story screen reads flag, draws `STAGE <name>` |
| `0x080049E8` | `0x49E8` | stage-index clamp (`>109 → 2`, `<2 → 109`) |
| `0x0200003C` | — | current stage index (s16, EWRAM) |
| `0x082D8AD8` | `0x2D8AD8` | stage-name pointer table (110 entries) |
| `0x080128E8` | `0x128E8` | in-game DEBUG menu draw/update entry (string refs at `0x12A78`+) |
| `0x0801255C` | `0x1255C` | DEBUG row 1 handler: HP MAX |
| `0x080125B8` | `0x125B8` | DEBUG row 2 handler: MP MAX |
| `0x08012624` | `0x12624` | DEBUG row 3 handler: AP MAX |
| `0x0801266C` | `0x1266C` | DEBUG row 4 handler: EXP MAX |
| `0x080126D4` | `0x126D4` | DEBUG row 5 handler: BGM toggle |
| `0x08012708` | `0x12708` | DEBUG row 6 handler: ClearLevel |
| `0x0801274A` | `0x1274A` | DEBUG row 7 handler: Get \<char\> |
| `0x0801280C` | `0x1280C` | DEBUG row 8 handler: Clear \<char\> |
| `0x0201A6C4` | — | Get/Clear character-flag block (EWRAM) |
| `0x0201A6F6` | — | ClearLevel byte (EWRAM) |
| `0x03001D7C` | — | TASKDISP toggle byte (IWRAM) |
| `0x03001E28` | — | BGM enable byte (IWRAM) |
| `0x03001E98` | — | pointer to input struct; `+2` = pressed-key mask |
| `0x080E9354` | `0xE9354` | DEBUG menu string bank (`STEP`, `DEBUG`, `TASKDISP`, HP/MP/AP/EXP, BGM, ClearLevel, Easy/Normal/Hard/SuperHard, Get/Clear, ` NG`, ` OK`) |
| `0x080F481C` | `0xF481C` | character-name pointer table (21 entries) |
| `0x080F4720` | `0xF4720` | character-name strings (Dylan … Rai) |
| `0x08468760` | `0x468760` | event-checker strings (`MSG NO:`, `STATUS:`, `EVENT CHECKER`) |
| `0x080EB1xx` | `0xEB1xx` | animation-checker strings (`ANIME CHECKER`, `CharNo:`, …) |

Player struct fields touched by the DEBUG menu (base pointer obtained through
the current-player table; all offsets are byte offsets):

| Offset | Field | Written by |
|---|---|---|
| `+0x156` | current HP (s16) | `= +0x15C` |
| `+0x158` | current MP (s16) | `= +0x15E` |
| `+0x15A` | current AP (s16) | `= 100` |
| `+0x15C` | max HP (s16) | — |
| `+0x15E` | max MP (s16) | — |
| `+0x19C` | EXP/gem value (u32) | `= 999999 (0x000F423F)` |

Observed EWRAM copies of the EXP value after EXP MAX: `0x020150E4`,
`0x0203AFE0`, `0x0203AFE4` all became `3F 42 0F 00`.

## 5. Algorithm

### 5.1 Debug gate (exact)

```
// runs once per frame while the Treasure-logo task is active
void logo_check(Task *t) {                 // t = task base (r4)
    if (t->done_7B) return;                // 0x08004300
    u16 keys = *(u16*)(*(u32*)0x03001E98 + 2);  // pressed-key mask
    int i = (s8)t->idx_7A;                 // 0x0800430A
    if (i > 6) return;                     // 0x08004316
    switch (i) {
    case 0: if (!keys) return; if (keys != 0x010) goto fail; break; // RIGHT
    case 1: if (!keys) return; if (keys != 0x020) goto fail; break; // LEFT
    case 2: if (!keys) return; if (keys != 0x200) goto fail; break; // L
    case 3: if (!keys) return; if (keys != 0x100) goto fail; break; // R
    case 4: if (!keys) return; if (keys != 0x040) goto fail; break; // UP
    case 5: if (!keys) return; if (keys != 0x004) goto fail; break; // SELECT
    case 6:
        if (!keys) return;
        if (keys != 0x004) goto fail;
        *(u8*)0x03001D7D = 1;              // 0x08004396
        play_se(0xB8);                     // 0x0800439C
        return;                            // index stays 6
    }
    t->idx_7A++;                           // 0x08004386
    return;
fail:
    t->done_7B = 1;                        // 0x080043AC
}
```

Key facts:

* The comparison is **equality of the whole pressed-key word**, not a bit test.
  Pressing two expected keys in the same frame fails.
* `keys == 0` is explicitly ignored in every state (so waiting is allowed).
* A mismatch is absorbing: `done_7B` makes every later call return immediately.
* The flag is *set*, never toggled. Repeating Select after success is harmless
  (still state 6); pressing any other button after success only sets the fail
  bit and does not clear the debug flag.
* The task window is the Treasure-logo task; entering the same sequence at the
  title or after the logo does nothing.

### 5.2 Pause → in-game DEBUG menu

At `0x080122F0` the pause update does:

```
if (*(u8*)0x03001D7D != 0 && (keys & 0x010)) {  // debug on AND Right
    play_se(0x2A);
    state = 5;                                  // open DEBUG menu
}
```

Row navigation clamps to 0..8. The row actions are the handlers listed in §4:

```
row 0 TASKDISP : if (LEFT|RIGHT) *(u8*)0x03001D7C ^= 1;
row 1 HP MAX   : if (A && hp_cur>0) hp_cur = hp_max;      // +0x156 = +0x15C
row 2 MP MAX   : if (A && hp_cur>0) mp_cur = mp_max;      // +0x158 = +0x15E
row 3 AP MAX   : if (A && hp_cur>0) ap_cur = 100;         // +0x15A = 100
row 4 EXP MAX  : if (A && hp_cur>0) exp = 999999;         // +0x19C
row 5 BGM      : if (LEFT|RIGHT) *(u8*)0x03001E28 ^= 1;
row 6 ClearLevel: idx = clamp(idx + (RIGHT?1:-1), 0, 3);  // 0x0201A6F6
row 7 Get <c>  : if (LEFT|RIGHT) c = clamp(c + dir, 0, 20);
                 if (A && c < 18) get[c] ^= 1;            // base 0x0201A6C4+8+c
                 if (B) set get[0..20] = 1;
row 8 Clear <c>: if (LEFT|RIGHT) c = clamp(c + dir, 0, 20);
                 if (A) clear[c] ^= 1;                    // base+0x1D+c
                 if (B) set clear[0..20] = 1;
```

ClearLevel displays `NG` initially, then cycles `Easy → Normal → Hard →
SuperHard → Easy`; values 0..3 are reachable after leaving `NG`.

### 5.3 Hidden stage select

```
if (*(u8*)0x03001D7D) {
    draw_text("STAGE " + stage_names[stage_idx]);   // 0x0800593A/0x08005966
    if (keys & (LEFT|RIGHT)) {
        stage_idx += (keys & RIGHT) ? 1 : -1;        // 0x080049C8
        if (stage_idx > 109) stage_idx = 2;          // 0x080049E8
        if (stage_idx < 2)   stage_idx = 109;        // 0x080049F0
        *(s16*)0x0200003C = stage_idx;
    }
}
```

The selector is evaluated while the key is held, so a 30 ms tap can advance two
entries; short taps or single-frame presses advance one. The clamp itself is
unambiguous: 108 reachable values, `2..109`.

## 6. Tables

### 6.1 Accepted button sequence

| # | Button | Pressed-key mask at `input+2` | Case address |
|---:|---|---:|---|
| 1 | Right | `0x010` | `0x08004348` |
| 2 | Left | `0x020` | `0x08004352` |
| 3 | L | `0x200` | `0x0800435C` |
| 4 | R | `0x100` | `0x0800436A` |
| 5 | Up | `0x040` | `0x08004374` |
| 6 | Select | `0x004` | `0x0800437E` |
| 7 | Select | `0x004` | `0x0800438E` |

### 6.2 Character table (`0x080F481C`, 21 entries)

| Index | Name | Get row toggles? | Clear row toggles? |
|---:|---|---|---|
| 0 | Dylan | yes | yes |
| 1 | Edo | yes | yes |
| 2 | Hahn | yes | yes |
| 3 | Cyclops | yes | yes |
| 4 | Soldier | yes | yes |
| 5 | Goblin | yes | yes |
| 6 | GobTank | yes | yes |
| 7 | Roper | yes | yes |
| 8 | HeavyGear | yes | yes |
| 9 | Zuru | yes | yes |
| 10 | Kanon | yes | yes |
| 11 | Sorcerer | yes | yes |
| 12 | Ginjirou | yes | yes |
| 13 | Gargoyle | yes | yes |
| 14 | Valger | yes | yes |
| 15 | SkyKnight | yes | yes |
| 16 | Celena | yes | yes |
| 17 | Nichole | yes | yes |
| 18 | En | **no** (A ignored) | yes |
| 19 | Hyou | **no** (A ignored) | yes |
| 20 | Rai | **no** (A ignored) | yes |

The Get bound is hard-coded at `0x080127A2..0x080127AC`:
`if (c == 0x12 || c == 0x14 || c == 0x13) skip`.

### 6.3 Stage table (`0x082D8AD8`, 110 entries)

| Idx | Name | Idx | Name | Idx | Name | Idx | Name |
|---:|---|---:|---|---:|---|---:|---|
| 0 | none | 1 | none | 2 | GOVER | 3 | SEDIT |
| 4 | 1-1-1 | 5 | 1-1-2 | 6 | 1-1-3 | 7 | 1-2 |
| 8 | 1-3 | 9 | 1-4 | 10 | 1-5 | 11 | 1-6 |
| 12 | 1-7 | 13 | 2-0 | 14 | 2-1 | 15 | 2-1a |
| 16 | 2-1b | 17 | 2-1c | 18 | 2-1d | 19 | 2-2a |
| 20 | 2-2b | 21 | 2-3 | 22 | 2-4 | 23 | 3-1 |
| 24 | 3-2 | 25 | 3-3 | 26 | 3-4 | 27 | 3-5 |
| 28 | 3-6 | 29 | 3-7 | 30 | 3-7a | 31 | 3-7b |
| 32 | 3-8 | 33 | 3-9 | 34 | 3-10 | 35 | 3-10a |
| 36 | 3-10b | 37 | 3-11 | 38 | 3-12 | 39 | 3-13 |
| 40 | 3-14 | 41 | 3-15 | 42 | 4-0 | 43 | 4-1 |
| 44 | 4-2 | 45 | 4-3 | 46 | 4-4 | 47 | 4-5 |
| 48 | 4-6 | 49 | 4-7 | 50 | 4-8 | 51 | 4-9 |
| 52 | 4-10 | 53 | 4-11a | 54 | 4-11b | 55 | 4-12 |
| 56 | 4-13 | 57 | 5-1a | 58 | 5-1b | 59 | 5-1c |
| 60 | 5-2 | 61 | 5-3a | 62 | 5-3b | 63 | 5-4 |
| 64 | 5-5 | 65 | 5-6 | 66 | 5-7 | 67 | 5-7b |
| 68 | 5-7c | 69 | 6-1 | 70 | 6-2 | 71 | 6-3 |
| 72 | 10_1 | 73 | 10_2 | 74 | 10_3 | 75 | 10_4 |
| 76 | 10_5 | 77 | 10_6 | 78 | 10_7 | 79 | 10_8 |
| 80 | 10_9 | 81 | 10_10 | 82 | 10_11 | 83 | 10_12 |
| 84 | 10_13 | 85 | 10_14 | 86 | 10_15 | 87 | 10_16 |
| 88 | ENDLE | 89 | TIMEA | 90 | MANUA | 91 | TUTOR |
| 92 | End-1 | 93 | End-2 | 94 | End-3 | 95 | End-4 |
| 96 | End-5 | 97 | End-6 | 98 | End-7 | 99 | End-8 |
| 100 | End-9 | 101 | End10 | 102 | End11 | 103 | End12 |
| 104 | Op-1 | 105 | Op-2 | 106 | Op-3 | 107 | Op-4 |
| 108 | Op-5 | 109 | Op-6 | | | | |

Ids 0 and 1 (`none`) exist in the table but are unreachable through the
selector because of the `2..109` clamp.

### 6.4 Debug options rows

| Row | Values | Notes |
|---|---|---|
| DIFFICULTY | Easy / Normal / Hard / SuperHard | present in retail too |
| COMMAND LIST | pages of basic controls | `BASIC CONTROL` screen |
| STAFF LIST | cast/staff credits | `CAST` screen |
| DELETE SAVE | Are you sure? NO/YES | destructive; viewed, not confirmed |
| DELETE RECORD | Are you sure? NO/YES | debug-only |
| LANGUAGE | ENGLISH / 日本語 | debug-only; both work |
| SOUND TEST | `000..418` (419 entries) | wraps; 33 music, 34–40 stop, rest SE |
| ANIMATION | ANIME CHECKER | CharNo/AnimeNo/BGM/SE/Palet/CenterMark/BackColor + stats |
| EVENT CHECK | MSG NO / text ID | `#DUMMY`, `#000`…; observed to 183 (`#821`) |

Animation-checker `CharNo` is not linear: observed 0–19 (characters), then
`100 (EFFECT)`, then `200 (BG_OBJ)`; TCRF reports `201` as `BG_OBJ2`, giving 22
values.

## 6b. Enumeration

### 6b.1 Gate space

* Alphabet: 10 buttons (`A, B, Select, Start, Right, Left, Up, Down, R, L`).
* Length: exactly 7 productive positions.
* Representable strings: **10^7 = 10,000,000**.
* Accepted strings: **1** (the sequence in §6.1), because every position
  demands equality with one fixed mask and any other non-zero press is an
  absorbing failure. Zero-key frames are not symbols and do not count.
* Therefore the probability that a random 7-press string is accepted is
  `1e-7`; the accepted set is `{ Right, Left, L, R, Up, Select, Select }`.
  That one string is the published GameFAQs/TCRF code; it was entered from a
  cold boot and accepted.

Acceptance/rejection was scored by reading `IWRAM[0x1D7D]` from a savestate
taken after the logo. Every test below is a fresh power-on.

| # | Test | Result | Flag |
|---:|---|---|---:|
| 1 | `Right, Left, L, R, Up, Select, Select` (80 ms spacing) | accepted | **1** |
| 2 | same, second independent boot | accepted | **1** |
| 3 | same with first Right held 0.4 s, rest fast | accepted (idle/held frames ignored) | **1** |
| 4 | `Left` first | rejected | 0 |
| 5 | `Right, Right, …` (wrong 2nd) | rejected | 0 |
| 6 | `Right, Left, R, L, …` (L/R swapped) | rejected | 0 |
| 7 | extra `A` before the sequence | rejected (absorbing fail) | 0 |
| 8 | only six presses (`…, Up, Select`) | rejected (incomplete) | 0 |
| 9 | last press `Start` instead of `Select` | rejected | 0 |
| 10 | correct sequence entered after the logo | rejected (outside task window) | 0 |
| 11 | correct sequence with 0.5 s spacing | rejected (window closes before completion) | 0 |
| 12 | correct sequence with first Right held 1.0 s | rejected (window) | 0 |

Test 3 versus 12 is the evidence for the model: the matcher itself ignores
held/zero frames (a 0.4 s hold still works), but the animation/logos task only
calls it for a limited window, so the whole sequence must fit.

**Bound:** pressing a wrong key at any of the seven positions is rejected;
there is no second accepted string, no prefix acceptance, no wrap, and no
timeout inside the task.

### 6b.2 Stage-select space

* Table: 110 entries.
* Reachable: **108** (`2..109`), by the clamp at `0x080049E8`.
* Unreachable despite existing: 0 and 1 (`none`).
* Novel values entered in the emulator (absent from GameFAQs/TCRF stage lists):

| Value | Entered as | Observed effect |
|---:|---|---|
| `2 = GOVER` | story screen, STAGE GOVER, 1 PLAYER, start | **GAME OVER** screen |
| `104 = Op-1` | story screen, STAGE Op-1, 1 PLAYER, start | opening cutscene line “You think everything happened by luck?” |

Both screens were reached and photographed; the planned “start stage” path
accepts these table ids directly. The remaining special ids
(`SEDIT`, `ENDLE`, `TIMEA`, `MANUA`, `TUTOR`, `End-1..End12`, `Op-2..Op-6`)
are enumerated by the table but were not launched one by one.

### 6b.3 In-game DEBUG menu space

* Rows: 9 (`0..8`), clamp proven at `0x080124C8`.
* Value domains:
  * TASKDISP: 2 states (OFF/ON), `0x03001D7C`.
  * BGM: 2 states, `0x03001E28`.
  * ClearLevel: 4 cycle values (`Easy..SuperHard`) plus initial `NG`.
  * Get \<character\>: 21 names, but only indices **0..17** toggle; 18/19/20
    (En/Hyou/Rai) ignore A.
  * Clear \<character\>: all 21 indices toggle.
  * HP/MP/AP/EXP: one-shot actions, no stored menu value.
* Novel state entered (not in any published list): `ClearLevel = SuperHard`,
  `Get HeavyGear = OK`, `Clear HeavyGear = OK`, `Clear En = OK`.
* Bound proven in-game: on `Get En`, A was pressed and the value stayed `OK`
  (no toggle); on `Clear En`, A changed `NG → OK`. This is the per-row bound
  hard-coded at `0x080127A2`.
* Character cycling was observed to wrap at 20 → 0 (clamp code), and
  ClearLevel at SuperHard → Easy.

### 6b.4 Options/debug extras

* SOUND TEST: 419 entries (`000..418`), observed wrap; this matches TCRF.
* LANGUAGE: 2 values, both rendered (English and Japanese).
* ANIMATION: 22 CharNo values (`0..19,100,200,201` per observation + TCRF);
  AnimeNo 0..254; other fields as listed in §6.4.
* EVENT CHECK: message index and text id advance together; observed
  `0 = #DUMMY`, `1 = #000`, `181 = #819`, `182 = #820`, `183 = #821`.

## 7. Validation evidence

### Observed (emulator / RAM)

* Screen walk (debug on where relevant): boot logos (Ubisoft, Treasure),
  copyright, intro, attract `PRESS START`, main menu (5-item retail form and
  7-item debug form), STORY MODE 1P/2P + STAGE selector, character select,
  VS MODE `PLAYER ENTRY` link screen, TRAINING 4-slot character select and
  gameplay, TUTORIAL gameplay, TIME ATTACK, ENDLESS, RECORDS gallery, OPTIONS
  (4-row retail form and 9-row debug form), LANGUAGE (English/Japanese),
  SOUND TEST, ANIMATION checker, EVENT CHECK, COMMAND LIST, STAFF LIST,
  DELETE SAVE confirmation, pause menu, and the in-game DEBUG menu.
* Correct sequence → SE 0xB8, main menu 7 items, options 9 items, pause → Right
  shows DEBUG; wrong sequences/positions → no debug (table in §6b.1).
* Flag byte `IWRAM[0x1D7D]` = 1 after the sequence, 0 after every rejected test.
* Setting `IWRAM[0x1D7D] = 0` with a debugger on a live debug-enabled state
  removed the pause-menu debug entry (pressing Right then did nothing),
  confirming the byte is the gate, not a side effect.
* Debug-only rows/screens: LANGUAGE, SOUND TEST (000..418), ANIMATION, EVENT
  CHECK, DELETE RECORD, TIME ATTACK, ENDLESS, STAGE selector, in-game DEBUG.
* HP MAX: partially depleted red HP bar refilled.
* AP MAX: partially depleted green AP bar refilled to full.
* EXP MAX: `999999` appeared at EWRAM `0x020150E4`, `0x0203AFE0`,
  `0x0203AFE4`; absent in the pre-action states.
* TASKDISP ON: white task-load lines appear across the scene.
* ClearLevel cycle and Get/Clear per-character toggling as in §6b.3.
* Stage `GOVER` → GAME OVER; stage `Op-1` → opening cutscene.

### Derived (instruction sequence)

* Exact 7-state equality matcher, fail bit, SE id and flag write (§5.1).
* Player-field semantics of HP/MP/AP/EXP MAX and the Get/Clear flag tables
  (§5.2, §4).
* Stage clamp `2..109` and the `STAGE` draw gate (§5.3).
* MP MAX is the same code shape as HP MAX (`cur = max`); the MP bar happened to
  be full during the test, so no visible delta was photographed.
* BGM row is a boolean XOR of `0x03001E28`; the menu label changed ON/OFF in the
  source listing, and the code path is direct.

### Inferred

* `SEDIT` probably means a staff/edit or sound-edit screen; `MANUA` probably a
  manual viewer. The names are in the table but those two scenes were not
  launched.
* The Get/Clear bits are save-profile flags; their persistence to SRAM was not
  exercised because the test profile was disposable and debug mode itself is
  RAM-only.
* The bottom-left DEBUG hex value (`4fc8`) is a runtime counter/task id; not
  reversed.

## 8. Unknowns

* Exact meaning of the bottom-left hex readout in the DEBUG menu.
* Upper bound of EVENT CHECK (the checker continued past 183; the message bank
  is larger and its exact count was not established).
* Visual effect of MP MAX (derived only; MP was full when tested).
* `SEDIT` and `MANUA` scenes were enumerated but not launched.
* Whether Get/Clear flags survive a save to the cart; they are clearly separate
  per-character bytes in EWRAM and the Clear row accepts all 21 characters.
* The 30 ms tap advancing two stage entries is an input-rate artifact of the
  held-key handler; exact frame timing under different emulator speeds may
  differ by one entry per tap.

## 9. Tooling

* mGBA 0.10.5 SDL, 3× scale, Xvfb `:123`, openbox, `SDL_AUDIODRIVER=dummy`.
* `xdotool` for input, `scrot` + ImageMagick for screenshots.
* `capstone` 5.0.7 for Thumb disassembly (`thumdis.py`).
* `parse_state.py` — extracts IWRAM/EWRAM from mGBA `.ssN` PNG savestates
  (`gbAs` zlib chunk; IWRAM at `0x19000`, EWRAM at `0x21000`).
* `test_seq.py` / `test_seq2.py` — boots the ROM, detects the Treasure logo by
  red-pixel fraction, enters a test sequence, saves slot 5 and reads
  `IWRAM[0x1D7D]`.
* `test_hold.py` / `test_hold2.py` — hold-time variants.
* Screenshots (work dir `/tmp/opencode/agh`): `main7c.png`, `op_c.png`,
  `story_c.png`, `stages.png`, `stageleft.png`, `wrap.png`, `vs_c.png`,
  `tr_c.png`, `tu_c.png`, `ta_c.png`, `en_c.png`, `lang_c.png`, `snd1c.png`,
  `snd2c.png`, `anim_c.png`, `char19c.png`, `char20c.png`, `evt2c.png`,
  `msg1c.png`, `msg2c.png`, `rec_c.png`, `dbgmenu_c.png`, `td3c.png`,
  `hp_after_c.png`, `ap_cmp.png`, `clearlevels.png`, `getcycle.png`,
  `gt3v.png`, `g_en2v.png`, `g_en3v.png`, `gov_game_c.png`, `op1run_c.png`,
  `cmd_c.png`, `staff2_c.png`.

Legal note: no ROM, extracted graphics, music or text is redistributed with
this report; only addresses, algorithms, menu labels and hashes are published.
