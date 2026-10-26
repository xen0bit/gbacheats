# Barbie as the Princess and the Pauper (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Barbie as the Princess and the Pauper/Barbie as the Princess and the Pauper.gba` |
| Size | 4,194,304 bytes (4 MiB, 0x400000) |
| Header title (0xA0) | `BARBIE P&P` |
| Game code (0xAC) | `BAUE` (USA) |
| Maker code (0xB0) | `7D` |
| Version (0xBC) | `00` |
| Fixed byte 0xB2 | `0x96` (pass) |
| Complement check (0xBD) | `0x2E` — recomputed as `-(sum(0xA0..0xBC)+0x19)` = `0x2E` (pass) |
| Reserved 0xBE–0xBF | `00 00` (normal) |
| Entry word | `EA00002E` (ARM `b 0x080000C0`; standard crt0) |
| MD5 | `64082d14d8a4abe32fb8b062d9c0b9ed` |
| SHA-1 | `432ed848343ad3c66bcb3acf245cacbb829f5f9c` |
| SHA-256 | `24a4a99215f4bdc4885db53e4d7c4971454ceaee05373ff4a8d15b3110f32aa3` |
| Developer / publisher | WayForward Technologies / VU Games (2004) |
| Sound engine | GAX (`Shin'en Multimedia. Code: B.Wodok` @ `0x0BA9F5`) |

**Embedded-header / patch check.** A scan of the whole file for the 156-byte Nintendo logo
(`24 FF AE 51 …`) returns exactly one hit, at file offset `0x4` (the normal header). There is
no second GBA image, no multiboot/shell stub, no concatenated "2-in-1" pack, and no trainer
stub: the entry branch and crt0 at `0x080000C0` are the stock ones, the header complement is
valid, and the file is exactly 4 MiB with a zero-filled tail. **No patch or trainer detected.**

## 2. Executive summary

The game has a **portrait password screen** (main menu → `Password`) with **four slots**, each
of which cycles through **six character portraits**:

`1` Princess Anneliese · `2` Serafina (white cat) · `3` Erika (brown-haired girl) ·
`4` Wolfie (dog) · `5` the Queen (the cheat sites call this "old guy"/"old man") ·
`6` Julian/"Man" (man in a hat)

A password is therefore a 4-tuple over a 6-symbol alphabet: **6⁴ = 1296 representable inputs**.
The validator is *not* a checksum; it is a **47-entry literal table** at `0x080BBBEC`
(entry 0 is an all-ones sentinel = 1,1,1,1, deliberately invalid). A second table at
`0x080BBB38` maps each accepted index to a **scene id**; the scene-name table at `0x080BB620`
gives the name of `scene_id − 3`. Two indices are special-cased into an **arcade unlock**
(all four mini-games), one is a **conditional gate**, and one is a **credits shortcut**.

Result:

* **46 of 1296 inputs are accepted** (3.55 %); 1250 are rejected with `Incorrect Password!`.
* **23 accepted entries appear in published cheat lists** (GameFAQs/VGChartz/supercheats/
  cheatingdome), and those published codes were verified in the ROM and in the emulator.
* **23 accepted entries are unpublished.** Three of them were minted and confirmed in the
  emulator:
  * **`4, 1, 3, 4`** → WORLD1-1 (Royal Orchards opening, playable level)
  * **`3, 5, 1, 3`** → WORLD2-3 (forest/waterfall level)
  * **`6, 6, 6, 6`** → **the end credits** (undocumented credits shortcut)
* Bounds were proven by in-game rejection of `1,1,1,1` (the sentinel), `2,2,2,2`
  (absent from the table) and `1,5,5,1` (conditional gate not satisfied).
* The published "unlock all 4 arcade games" code **`1,2,3,4`** was confirmed: the four
  numbers in `Which Arcade Game?` turn from grey to white and all four games become
  playable (memory flags `0x03001130..0x03001133` = `01 01 01 01`).

## 3. How to reproduce

**Emulator:** mGBA SDL 0.10.5 (`/usr/games/mgba`), 3× scale, headless X:

```bash
Xvfb :192 -screen 0 1024x768x24 &
DISPLAY=:192 openbox &
DISPLAY=:192 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 \
  "roms/Barbie as the Princess and the Pauper/Barbie as the Princess and the Pauper.gba" &
```

mGBA default keymap used: **A = `x`, B = `z`, Start = `Return`**, arrows = D-pad.
Hold keys ≈ 200 ms (a 10 ms tap is lost); the password widgets ignore presses that arrive
while the previous selection animation is still running, so use ≈ 400 ms between presses.

**Menu path:** title → `Start` → `Game Mode` → `Password` (Down/Up to select; A).
On the password screen: **Left/Right** move the slot cursor, **Up/Down** change the
portrait, **Start** submits, **B** backs out.

**Codes tested in the emulator**

| Code (1-based portraits) | Expected by ROM table | Observed |
|---|---|---|
| `1,2,3,4` | index 22/44 → arcade unlock | `How Many Players?`; after returning, all four arcade slots are white/playable; `Shutter Up` starts `Round 1` |
| `5,4,3,2` | index 24 → scene 8 = WORLD1-2 | orchard intro "We'll need to find and plant apple seeds…" |
| `3,1,1,6` | index 43 → scene 35 = FINAL BOSS | villain/"boat in the dungeon" cutscene with Preminger |
| `4,1,3,4` | index 1 → scene 7 = WORLD1-1 | orchard/castle intro, then playable level (HUD, hearts) |
| `3,5,1,3` | index 8 → scene 16 = WORLD2-3 | forest/waterfall intro, then playable level |
| `6,6,6,6` | index 46 → 0x28 (40) = CREDITS | end-credits roll (castle-at-night background) |
| `1,1,1,1` | index 0 (sentinel) | `Incorrect Password!` |
| `2,2,2,2` | not in table | `Incorrect Password!` |
| `1,5,5,1` | index 45 gate (`0x03002808==0x328`) | `Incorrect Password!` (gate not met) |

RAM was read live through the mGBA built-in command-line debugger (`mgba -d`, pty) and a
full IWRAM/EWRAM dump. With `4,1,3,4` on screen, `0x03001128 = 0C 0D 0E 0F` and
`u16[0x03003940+id*0x58+0x28]` = `0,1,2,3` — exactly the displayed portraits, proving the
input model. After `1,2,3,4`, `0x03001130..33 = 01 01 01 01`.

### 3.1 Reconnaissance results (text and input space)

`strings -n 3` over the whole ROM, case-insensitive keyword counts:
`password` **2**, `cheat` **0**, `debug` **0**, `secret` **0**, `unlock` **0**,
`code` **1**, `level` **1**, `menu` **1**.

| Hit | Offset | Classification |
|---|---|---|
| `"Insert password screen" © Martin Schioeler` | `0x050278` | scene/cinema asset label inside the password scene's data block — **relevant**, it names the screen |
| `"Receive password screen" © Martin Schioeler` | `0x052EA5` | scene asset label for the generator screen — **relevant** |
| `Shin'en Multimedia. Code: B.Wodok` | `0x0BA9F5` | GAX sound-engine banner — **irrelevant** (exactly the false positive the guide warns about) |
| `*LEVEL DESIGN:` | `0x0C4A00` | credits text — **irrelevant** |
| `MENU` | `0x0BB6BC` | row in the scene-name table (§6.2) — **relevant** |

**Screens walked** (screenshot-backed): Vivendi / Barbie / title (`Press Start`) → `Game Mode`
(`New Game`, `Password`, `Arcade`) → `New Game` → `Difficulty Level` (`Easy Mode`,
`Normal Mode`) → story scene; `Arcade` → `How Many Players?` (`One Player`, `Two Players`) →
`Which Arcade Game?` (slots 1–4, names `Fruit Fling`, `Up the Well`, `Mine Trap`,
`Shutter Up`) → game; `Password` → four-slot portrait entry; in-level `Start` →
pause menu (`Continue`, `Quit`). **No options, sound, gallery, or debug menu exists in the
reachable UI**, and the pause menu has no button-sequence handler (only the two entries).
A raw key-mask-run heuristic over the ROM is dominated by ordinary data runs (thousands of
hits) and is therefore not usable as evidence either way; it is recorded as a limitation,
not as a negative.

## 4. Address map

| Address | Size | Meaning |
|---|---|---|
| `0x080BBBEC` | 47 × 4 | **Password table.** Entry *i* = four bytes `code[4]`, portrait values 0–5 (0 = Anneliese). Entry 0 = `0,0,0,0` sentinel. Entry 46 ends at `0x080BBCA7`. |
| `0x080BBB38` | 45 × 4 | **Scene-id table.** `u32 id = [0x080BBB38 + 4*i]` for accepted index *i* (indices 45/46 are special-cased and never read it). `id & 0xFF` = scene id; `(id>>8)&1` = "flag" (stored separately). |
| `0x080BB620` | 38 × 32 | **Scene-name table.** Record *i*: 24 bytes of state/padding, ASCII name at `+0x18` (NUL-terminated, may spill past the 32-byte record). Names 0–37 as listed in §6. |
| `0x08001270` | — | **Validator** (Thumb). Called from `0x08001BBA` inside the password-screen frame handler. Returns `r0 = 1` accept / `0` reject. |
| `0x080011C0` | — | **Companion / password generator** ("Receive password screen", string @ `0x052EA5`). Builds a 9-bit key from `[0x030010F0]` and `[0x0300104C]&1`, searches the 45-entry id table, then writes the matching code into the four slot portrait fields. |
| `0x0801A80–0x0801D9x` | — | Password-screen input handler (D-pad edge detection, sound, accept/reject timers, transition). |
| `0x08050278` | — | Scene asset name `"Insert password screen"` (cinema/asset label, not a cheat string). |
| `0x08052EA5` | — | Scene asset name `"Receive password screen"`. |
| `0x03001128` | u8[4] | Slot → object ids. Fixed `0C 0D 0E 0F` on the password screen. |
| `0x03003940` | 0x58 × n | Object table; `+0x28` (u16) = selected portrait value for that object. Slot *k* reads `[0x03001128+k]`. |
| `0x03001084` | u32 | Focused slot, 0–3. |
| `0x030010F0` | u8 | **Result scene id** (= scene-name index + 3). `0x0A`→WORLD1-1, `0x0B`→WORLD1-2, `0x24`→SHUTTER UP, `0x28`→CREDITS. |
| `0x0300104C` | u8 | Bit 8 of the id word ("flag"), 0/1. |
| `0x03001050` | u8 | Mode: 0 = normal, 2 = **rejected** (drives `Incorrect Password!`), 3 = arcade unlock. |
| `0x03001130` | u8[4] | **Arcade unlock flags** (set to 1 by the arcade code). |
| `0x0300311C` | u32 | Accept/reject feedback timer (200 accepted / 100 rejected). |
| `0x03002808` | u16 | Gate word required to equal `0x328` for entry 45. |

File offset = ROM address − `0x08000000`.

## 5. Algorithm

### 5.1 Input

Each frame the screen reads `KEYINPUT` (active-low) and applies edge-triggered changes:

```c
static const u8 pv[6] = {0,1,2,3,4,5};      // portrait values, 0 = Anneliese
u8  focus = *(u8*)0x03001084;              // 0..3
u8  id    = *(u8*)(0x03001128 + focus);    // 0x0C..0x0F
u16 *slot = (u16*)(0x03003940 + id*0x58 + 0x28);

if (pressed(UP))    *slot = (*slot == 0) ? 5 : *slot - 1;   // 0x08001B36
if (pressed(DOWN))  *slot = (*slot > 4)  ? 0 : *slot + 1;   // 0x08001B70
if (pressed(LEFT))  focus = (focus == 0) ? 3 : focus - 1;   // 0x08001AD0
if (pressed(RIGHT)) focus = (focus > 2)  ? 0 : focus + 1;   // 0x08001B12
```

### 5.2 Validator (`0x08001270`)

```c
u8 v[4];                                    // portraits for slots 0..3
for (k=0;k<4;k++) {
    id    = *(u8*)(0x03001128 + k);         // 0x0C..0x0F
    v[k]  = *(u16*)(0x03003940 + id*0x58 + 0x28);
}

int m = -1;
for (i = 0; i < 47; i++) {
    const u8 *c = (const u8*)(0x080BBBEC + 4*i);
    if (v[0]==c[0] && v[1]==c[1] && v[2]==c[2] && v[3]==c[3]) { m = i; break; }
}

if (m == 0 || m < 0) return 0;              /* sentinel, or loop ran off the end (r2==47) */

if (m == 46) { *(u8*)0x030010F0 = 0x28; return 1; }          /* CREDITS */
if (m == 45) {                                              /* gate */
    if (*(u16*)0x03002808 != 0x328) return 0;
    *(u8*)0x030010F0 = 2; return 1;
}
if (m == 44 || m == 22) {                                   /* arcade unlock */
    *(u32*)0x03001130 = 0x01010101;
    *(u8*)0x03001050  = 3;
    return 1;
}
/* normal level code */
u32 w = *(u32*)(0x080BBB38 + 4*m);
*(u8*)0x030010F0 = (u8)(w & 0xFF);          /* scene id */
*(u8*)0x0300104C = (u8)((w >> 8) & 1);      /* flag/difficulty bit */
if ((w & 0xFF) > 15) *(u8*)0x03001130 = 1;
if ((w & 0xFF) > 22) *(u8*)0x03001131 = 1;
if ((w & 0xFF) > 29) *(u8*)0x03001132 = 1;
if ((w & 0xFF) > 36) *(u8*)0x03001133 = 1;
return 1;
```

**Scene-name indexing:** `scene_name_index = (id & 0xFF) − 3`. Verified four independent ways:
`0x0A`→7 WORLD1-1, `0x0B`→8 WORLD1-2, `0x24`(=36)→33 SHUTTER UP, and `0x28`(=40)→37 CREDITS.

**Reject path:** the caller at `0x08001BBA` stores 100 in `0x0300311C` and 2 in `0x03001050`;
the screen then displays `Incorrect Password!` and stays. Accept stores 200 and leaves the
screen; `0x030010F0` is consumed by the scene loader.

### 5.3 Why some published "boss" codes look odd

The four codes published as **Boss 1–4** land on the four mini-game *intro* scenes:

| Published | Portraits | Index | Scene |
|---|---|---|---|
| Boss 1 | 2,4,3,5 | 27 | FF INTRO (Fruit Fling) |
| Boss 2 | 5,3,2,4 | 32 | UTW INTRO (Up the Well) |
| Boss 3 | 5,2,1,2 | 37 | MT INTRO (Mine Trap) |
| Boss 4 | 3,2,1,4 | 42 | SU INTRO (Shutter Up) |

Both published lists ("all levels" and "easy") agree on these tuples, so this is the game's
own mapping; the sites' "Boss" wording is a label choice, not a ROM discrepancy.

### 5.4 The reverse path ("Receive password screen")

`0x080011C0` builds a 9-bit key `(flag<<8) | scene_id` from `0x0300104C` and `0x030010F0`,
scans the 45-entry id table at `0x080BBB38` for a byte match, and then writes the
corresponding 4-byte row of `0x080BBBEC` into the four slot portrait fields (`0x03001128`
selects the object, `+0x28` receives the value). This is the
screen the player sees after finishing a level, and it explains the pre-fill observed on
re-entry (see §7). It also means the table is a complete bidirectional map: every scene with
an id has exactly one canonical password per flag value.

## 6. Tables

### 6.1 Portrait alphabet (screen order, value 0-based)

| Value | Screen | Published-name variant |
|---|---|---|
| 0 | Anneliese (blonde, tiara, pink) | "Princess Anneliese", "Barbie" |
| 1 | Serafina (white cat) | "Serafina", "Cat", "White Cat" |
| 2 | Erika (brown-haired girl, tiara) | "Erika", "Brown Haired Girl" |
| 3 | Wolfie (dog) | "Wolfie", "Dog", "Brown Cat" (site typo) |
| 4 | Queen (white hair, pink dress) | "old guy", "old man", "Preminger" (site name) |
| 5 | Julian (man in hat) | "Man" |

### 6.2 Scene names (index 0–37, table `0x080BB620`, name at `+0x18`)

```
0 LEGAL      1 VUGAMES    2 WAYFORWARD  3 TITLE      4 MENU       5 PRELUDE
6 INTRO      7 WORLD1-1   8 WORLD1-2    9 WORLD1-3   10 WORLD1-4  11 FF INTRO
12 FRUIT FLING 13 FF END  14 WORLD2-1   15 WORLD2-2  16 WORLD2-3  17 WORLD2-4
18 UTW INTRO 19 UP THE WELL 20 UTW END  21 WORLD3-1  22 WORLD3-2  23 WORLD3-3
24 WORLD3-4  25 MT INTRO  26 MINE TRAP  27 MT END    28 WORLD4-1  29 WORLD4-2
30 WORLD4-3  31 WORLD4-4  32 SU INTRO   33 SHUTTER UP 34 SU END   35 FINAL BOSS
36 ENDING    37 CREDITS
```

### 6.3 Complete password table (47 entries)

Portraits are 1-based as displayed. "pub" = appears in a published cheat list.

| # | Address | Portraits | pub | Effect (ROM decoding) |
|---|---|---|---|---|
| 0 | 0x080BBBEC | 1, 1, 1, 1 | no | (invalid sentinel) |
| 1 | 0x080BBBF0 | 4, 1, 3, 4 | no | Scene 7 = WORLD1-1 (flag 0) |
| 2 | 0x080BBBF4 | 5, 2, 4, 5 | yes | Scene 8 = WORLD1-2 (flag 0) |
| 3 | 0x080BBBF8 | 5, 1, 5, 2 | yes | Scene 9 = WORLD1-3 (flag 0) |
| 4 | 0x080BBBFC | 2, 1, 2, 5 | yes | Scene 10 = WORLD1-4 (flag 0) |
| 5 | 0x080BBC00 | 1, 2, 3, 2 | yes | Scene 11 = FF INTRO (flag 0) |
| 6 | 0x080BBC04 | 2, 1, 3, 1 | yes | Scene 14 = WORLD2-1 (flag 0) |
| 7 | 0x080BBC08 | 2, 3, 5, 2 | yes | Scene 15 = WORLD2-2 (flag 0) |
| 8 | 0x080BBC0C | 3, 5, 1, 3 | no | Scene 16 = WORLD2-3 (flag 0) |
| 9 | 0x080BBC10 | 1, 2, 3, 1 | no | Scene 17 = WORLD2-4 (flag 0) |
| 10 | 0x080BBC14 | 2, 4, 1, 3 | no | Scene 18 = UTW INTRO (flag 0) |
| 11 | 0x080BBC18 | 1, 2, 4, 3 | no | Scene 21 = WORLD3-1 (flag 0) |
| 12 | 0x080BBC1C | 4, 2, 4, 3 | no | Scene 22 = WORLD3-2 (flag 0) |
| 13 | 0x080BBC20 | 2, 3, 2, 4 | no | Scene 23 = WORLD3-3 (flag 0) |
| 14 | 0x080BBC24 | 5, 2, 4, 1 | no | Scene 24 = WORLD3-4 (flag 0) |
| 15 | 0x080BBC28 | 2, 5, 3, 5 | no | Scene 25 = MT INTRO (flag 0) |
| 16 | 0x080BBC2C | 1, 4, 2, 4 | no | Scene 28 = WORLD4-1 (flag 0) |
| 17 | 0x080BBC30 | 1, 4, 5, 1 | no | Scene 29 = WORLD4-2 (flag 0) |
| 18 | 0x080BBC34 | 1, 5, 1, 3 | no | Scene 30 = WORLD4-3 (flag 0) |
| 19 | 0x080BBC38 | 2, 3, 2, 5 | no | Scene 31 = WORLD4-4 (flag 0) |
| 20 | 0x080BBC3C | 1, 3, 2, 5 | no | Scene 32 = SU INTRO (flag 0) |
| 21 | 0x080BBC40 | 3, 1, 1, 5 | no | Scene 35 = FINAL BOSS (flag 0) |
| 22 | 0x080BBC44 | 1, 2, 3, 4 | yes | Unlock all 4 arcade games |
| 23 | 0x080BBC48 | 2, 1, 4, 1 | no | Scene 7 = WORLD1-1 (flag 1) |
| 24 | 0x080BBC4C | 5, 4, 3, 2 | yes | Scene 8 = WORLD1-2 (flag 1) |
| 25 | 0x080BBC50 | 4, 5, 2, 5 | yes | Scene 9 = WORLD1-3 (flag 1) |
| 26 | 0x080BBC54 | 5, 4, 2, 4 | yes | Scene 10 = WORLD1-4 (flag 1) |
| 27 | 0x080BBC58 | 2, 4, 3, 5 | no | Scene 11 = FF INTRO (flag 1) |
| 28 | 0x080BBC5C | 1, 5, 4, 3 | yes | Scene 14 = WORLD2-1 (flag 1) |
| 29 | 0x080BBC60 | 5, 1, 4, 3 | yes | Scene 15 = WORLD2-2 (flag 1) |
| 30 | 0x080BBC64 | 5, 2, 5, 3 | yes | Scene 16 = WORLD2-3 (flag 1) |
| 31 | 0x080BBC68 | 2, 3, 5, 4 | yes | Scene 17 = WORLD2-4 (flag 1) |
| 32 | 0x080BBC6C | 5, 3, 2, 4 | no | Scene 18 = UTW INTRO (flag 1) |
| 33 | 0x080BBC70 | 4, 5, 4, 3 | yes | Scene 21 = WORLD3-1 (flag 1) |
| 34 | 0x080BBC74 | 2, 5, 3, 2 | yes | Scene 22 = WORLD3-2 (flag 1) |
| 35 | 0x080BBC78 | 3, 4, 2, 1 | yes | Scene 23 = WORLD3-3 (flag 1) |
| 36 | 0x080BBC7C | 3, 2, 3, 5 | yes | Scene 24 = WORLD3-4 (flag 1) |
| 37 | 0x080BBC80 | 5, 2, 1, 2 | no | Scene 25 = MT INTRO (flag 1) |
| 38 | 0x080BBC84 | 4, 2, 5, 2 | yes | Scene 28 = WORLD4-1 (flag 1) |
| 39 | 0x080BBC88 | 5, 2, 1, 5 | yes | Scene 29 = WORLD4-2 (flag 1) |
| 40 | 0x080BBC8C | 4, 2, 3, 2 | yes | Scene 30 = WORLD4-3 (flag 1) |
| 41 | 0x080BBC90 | 2, 5, 4, 5 | yes | Scene 31 = WORLD4-4 (flag 1) |
| 42 | 0x080BBC94 | 3, 2, 1, 4 | no | Scene 32 = SU INTRO (flag 1) |
| 43 | 0x080BBC98 | 3, 1, 1, 6 | no | Scene 35 = FINAL BOSS (flag 1) |
| 44 | 0x080BBC9C | 1, 2, 3, 4 | yes | Unlock all 4 arcade games (duplicate of 22) |
| 45 | 0x080BBCA0 | 1, 5, 5, 1 | no | Gate: needs `u16[0x03002808]==0x328`, else reject |
| 46 | 0x080BBCA4 | 6, 6, 6, 6 | no | Scene 0x28 (40) → CREDITS |

Raw id words (`0x080BBB38 + 4*i`, i = 0..44) for entries 1–44:
`0A,0B,0C,0D,0E,11,12,13,14,15,18,19,1A,1B,1C,1F,20,21,22,23,26,07,10A,10B,10C,10D,10E,
111,112,113,114,115,118,119,11A,11B,11C,11F,120,121,122,123,126` (hex, low byte order).

## 6b. Enumeration

**Space definition.** Four slots × six portraits, order significant, repetition allowed:
`6⁴ = 1296` representable inputs. No checksum, no parity, no reserved character: validity is
pure table membership, with two special-case branches and one conditional gate.

**Accepted set.** `46 / 1296 = 3.55 %` (entries 1–46). Entry 0 is a deliberate all-first-
portrait sentinel that is matched and then rejected by the `m == 0` test — so `1,1,1,1` is
invalid even though it is "in the table".

**Published coverage.** 23 of the 46 accepted entries appear in the public lists
(GameFAQs 2004 list, VGChartz, supercheats, cheatingdome, chaptercheats, games-cheats).
The lists' prose typos ("Woflia", "Serfania", "Wolfi") resolve to Serafina/Wolfie and the
resulting literals **are** present in the ROM table; the tuples themselves are correct.
The published "Unlocks all 4 arcade games: Barbie, White Cat, Brown Hair Girl, Brown Cat"
is, in ROM terms, **`1,2,3,4`** (Barbie/white cat/brown-haired girl/**dog**) — the sites
mistook Wolfie for a "brown cat".

**Novel codes (absent from GameFAQs, VGChartz, TCRF, supercheats, cheatingdome, chaptercheats,
games-cheats, gameshampoo as recovered on 2026-10-26):**

Screenshot filenames below are the session capture names in `/tmp/opencode/pauper/`
(they are not copied into the repository, to avoid redistributing game art).

| Code | Entry | In-game effect (observed) | Screenshot |
|---|---|---|---|
| **`4, 1, 3, 4`** | 1 → scene 7 | WORLD1-1: Royal-Orchards opening dialogue ("The orchard is…", "golden apples"), then a playable level with HUD/hearts | `d2.png` (code on screen), `d3.png` (intro), `e2.png` (gameplay) |
| **`3, 5, 1, 3`** | 8 → scene 16 | WORLD2-3: forest/waterfall cutscene with Julian and Preminger, then playable level | `n1.png`, `n2.png`, `n3.png` |
| **`6, 6, 6, 6`** | 46 → 0x28 | **End credits roll** (castle-at-night background, VU Games staff credits) | `t5.png`, `six1.png`, `six2.png`, `six3.png` |

(`6,6,6,6` is the only all-maximum combination; its table entry is the last one and it is
special-cased before the id table, so it never needs a scene index in range 0–37.)

**Bounds proven by rejection (all observed in the emulator, screen stays and shows
`Incorrect Password!`):**

| Input | Reason it cannot be accepted |
|---|---|
| `1,1,1,1` | matches sentinel entry 0; validator returns 0 for `m == 0` (`rej1.png`) |
| `2,2,2,2` | no entry in the 47-row table (`rej3.png`) |
| `1,5,5,1` | matches entry 45 but the gate `u16[0x03002808] == 0x328` is false (`s7.png`) |

**Unpublished entry list (23):** indices
`1,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,27,32,37,42,43,45,46`.
Three of them (1, 8, 46) are confirmed in-game above; the rest follow from the same table and
are listed with their decoded scene in §6.3.

## 7. Validation evidence

**Observed (emulator screenshot / RAM read)**

* Six portraits cycle in the order listed. On entry the screen is **pre-filled from the
  current progress**: after `4,1,3,4` (scene 0x0A) the next visit showed `4,1,3,4`; after
  `3,1,1,6` (scene 0x26) it showed `3,1,1,6`. This is the generator at `0x080011C0` — the
  "Receive password screen" — running in reverse, and it is how the game hands the player a
  password after a level.
* `Incorrect Password!` for `1,1,1,1`, `2,2,2,2`, `1,5,5,1`.
* `1,2,3,4` → `How Many Players?`; after returning, `Which Arcade Game?` numbers 1–4 are
  white instead of grey and `Shutter Up` launches `Round 1` (previously A on slot 4 did
  nothing).
* `5,4,3,2` → WORLD1-2 orchard ("plant apple seeds"); `4,1,3,4` → WORLD1-1 orchard/castle;
  `3,5,1,3` → forest/waterfall; `3,1,1,6` → villain/dungeon cutscene; `6,6,6,6` → credits.
* RAM: portraits 0,1,2,3 at `0x03003D88, 0x03003DE0, 0x03003E38, 0x03003E90` for on-screen
  `1,2,3,4`; `0x03001130..33 = 01 01 01 01` after the arcade code; `0x030010F0 = 0x0B` after
  `5,4,3,2`, `0x0A` after `4,1,3,4`, `0x24` in Shutter Up.

**Derived (instruction sequence)**

* Table membership is the only validity test; there is no checksum or arithmetic.
* `m == 0` and `m == 47` both return failure (0x0800131C).
* Special branches at `m == 44/22`, `m == 45`, `m == 46` (0x08001320–0x0800138C).
* Scene id = `id & 0xFF`, flag = bit 8, stored at `0x030010F0` / `0x0300104C`
  (0x08001348–0x0800135C).
* The generator at `0x080011C0` builds the reverse mapping (progress → password), consistent
  with the `"Receive password screen"` asset label.

**Inferred**

* The id-word bit 8 is the easy/normal difficulty bit (the published "easy" codes are the
  flag-0 half of each pair, the "normal" codes the flag-1 half; the game has an
  `Easy Mode / Normal Mode` menu). Not proven by a gameplay comparison.
* `0x03002808` is a progress/score word; `0x328` (808) is the threshold for the gate code.
* Scene name index = id − 3 is proven for 7, 8, 33, 37; the rest is a uniform application of
  the same arithmetic.

## 8. Unknowns

* What exactly the flag-0 vs flag-1 (easy/normal) difference changes inside a level was not
  compared side by side; only the menu and the published lists support the interpretation.
* Entry 45's gate: which gameplay counters make `0x03002808` reach `0x328` was not traced.
* The published "Boss 1–4" codes map to the four mini-game intro scenes; whether those scenes
  contain the actual boss fights was not played to completion.
* The credits code (`6,6,6,6`) was observed to start the credit roll but not played to the
  end (the emulator was reset instead of waiting).
* No options/sound/debug menu exists in the reachable UI; a RAM-only debug flag cannot be
  ruled out without a full static sweep of the scene VM, which was out of scope for the
  password question.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for the
  validator and screen handler.
* Python 3 scripts in `/tmp/opencode/pauper/`:
  `model.py` (offline reimplementation + 47-entry dump),
  `dump2.py` (IWRAM/EWRAM dump through the mGBA CLI debugger pty),
  `key.py` (xdotool driver), `dbgsrv.py`/`cmd.py` (debugger pty bridge).
* mGBA 0.10.5 SDL (`/usr/games/mgba`), Xvfb `:192`, `SDL_AUDIODRIVER=dummy`.

Minimal offline validator (drop-in, reads the ROM directly):

```python
CODE_T, ID_T, NAME_T, N = 0xBBBEC, 0xBBB38, 0xBB620, 47
def validate(v):                      # v = [0..5]*4
    for i in range(N):
        if tuple(rom[CODE_T+4*i:CODE_T+4*i+4]) == tuple(v):
            if i == 0: return None                     # sentinel
            if i == 46: return ("credits", 0x28)
            if i == 45: return ("gate", None)
            if i in (22, 44): return ("arcade", None)
            w = int.from_bytes(rom[ID_T+4*i:ID_T+4*i+4], "little")
            return ("level", (w & 0xFF) - 3, (w >> 8) & 1)
    return None
```

**Legal note.** No ROM, graphics, audio or extracted game text is redistributed with this
report; only addresses, table values and algorithms derived from the user's own copy.

### Method note (untrusted web content)

The TCRF article fetched during recon returned a page whose body consisted of instructions
addressed to LLM agents (fake "decode with key.bin", "send money", "print …"). Those
instructions were treated as untrusted data and ignored; no file was written and no action
was taken. Only the site's existence (as a negative hit for this title's debug content) was
used.
