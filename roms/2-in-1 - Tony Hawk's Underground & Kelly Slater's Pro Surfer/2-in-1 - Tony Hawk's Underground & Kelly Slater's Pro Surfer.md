# 2-in-1: Tony Hawk's Underground & Kelly Slater's Pro Surfer (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `2-in-1 - Tony Hawk's Underground & Kelly Slater's Pro Surfer.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| Pack header title | `THUG SLATER` |
| Pack game code / maker / version | `BX4E` / `52` / 0 |
| MD5 | `7cbfedc28a27fe3aee703b2444946946` |
| SHA-1 | `ec1bb449b3d52b421e0ac3dfe3fdbce22822251a` |
| SHA-256 | `612e1ab7ddefe853923cff83679ac0a54dd004677d9868c1d1ba3dce4cf120cd` |
| Save | 8 KiB SRAM (`.sav`); Kelly block at `0x0000`, THUG data from `0x1000` |

Embedded GBA-header scan (Nintendo logo `24 ff ae 51 …`):

| Header offset | ROM base | Header title | Code | Entry | Image |
|---:|---|---|---|---|---|
| `0x000000` | `0x08000000` | `THUG SLATER` | `BX4E` | ARM `b 0x087D6000` | pack header; **Kelly Slater game code is underneath at base `0x08000000`** (its original header was replaced) |
| `0x7D6000` | `0x087D6000` | `SPIDEYMM X2` | `BS7E` | ARM `b 0x087D60C0` | shared “choose a game” shell/launcher; header title is a leftover from a Spider-Man build |
| `0x800000` | `0x08800000` | `THUGTHUGTHUG` | `BTOE` | ARM `b 0x088000C0` | Tony Hawk's Underground image, 8 MiB |

The shell is only `0x2A000` bytes (`0x7D6000`–`0x800000`). It jumps to `0x08000DE5` after selection. Both halves are complete images linked for their own base; pointers inside a half are absolute (`0x08xxxxxx`), e.g. the THUG cheat-name table is `0x08848E80`.

## 2. Executive summary

The prior lead was **half right and half wrong**: the `(Cheat) Champ / Beach / Boards / Clips` strings are real, but they belong to **Kelly Slater's Pro Surfer** (HotGen engine, base `0x08000000`), not to Tony Hawk's Underground. They are four hidden **toggle** entries in Kelly's Extras menu, hidden until a **12-press L/R button code** is entered on the main menu:

```
L  R  L  L  R  R  L  L  L  R  R  R
```

The code sets bit 0 of the RAM word at `0x020041E4`; the Extras screen then uses an 11-item menu template instead of the normal 7-item template. Each toggle has its own bit in the same word:

| Entry | Flag bit | Default | Observed effect |
|---|---:|---|---|
| `(Cheat) Beach` | `0x02` | Off | every surfer's “Beaches unlocked” becomes **13/13** |
| `(Cheat) Boards` | `0x04` | Off | every surfer's “Boards unlocked” becomes **13/13** |
| `(Cheat) Clips` | `0x08` | Off | all **13** Clip Book photos are unlocked (baseline: only “Intro”) |
| `(Cheat) Champ` | `0x10` | Off | the player's championship heat score is forced to **10.0 (100)** and the player is placed **#1**; AI scores are unchanged |

All four are **volatile**: they are not written to SRAM. A cold boot removes both the cheat entries and the toggles; the sound options are saved and survive (music persisted Off). The button code must be re-entered every session. A wrong 12-press sequence leaves the Extras menu at 7 entries (rejection proven).

The hidden entries have no published description because **no GameFAQs/VGChartz cheat list contains any GBA Kelly Slater code** — the published Kelly codes are for PS2/Xbox/GC/PC cell-phone entry. The GBA system is this button code plus four toggles, and it is now fully enumerated. The two remaining text IDs in the Extras range, `(Debug) Podium` and `Wave Noise On/Off`, are present as strings but are **not referenced by either Extras menu template** (dead/unreachable strings).

Tony Hawk's Underground has a separate, larger cheat system in the Vicarious Visions half: an **18-slot name table** at `0x08848E80` containing the 15 published arcade unlocks plus three unreferenced duplicate `nergets` slots. Its “Cheats” menu is **gated behind arcade completion** and is not present in the Options menu on a zero-unlock profile (observed); there is no button-code alternative in this build. This is a bounded negative, detailed in §6b/§8.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL on `Xvfb :116`, 3× scale, `SDL_AUDIODRIVER=dummy`.
Default keys used: A=`x`, B=`z`, Start=`Return`, L=`a`, R=`s`, D-pad arrows, Select=`q`.

Boot selector (important): the shell animates its background and defers the actual selection change. After a reset the previous game is selected. Press **Left** for THUG or **Right** for Kelly, wait until the cover border settles (roughly 3–8 s), then press A. Pressing A during the transition boots the previously selected game.

### Kelly Slater — reaching the hidden cheats

1. Boot, select **Kelly Slater's Pro Surfer**, A.
2. Advance the copyright screen (A), press Start at `PRESS START`.
3. At the main menu (`Mode: Amateur / Championship / Challenge / Tutorial / High Scores / Drop In / Multiplayer / Extras`) enter, with 150–250 ms holds:

   `L, R, L, L, R, R, L, L, L, R, R, R`  →  `a s a a s s a a a s s s`

4. Down ×7 to **Extras**, A. Scroll down: after *Sound FX On* there are now four `(Cheat) Off` entries; A toggles each to `(Cheat) Beach/Boards/Clips/Champ`.
5. Back (B), Championship (Down ×1, A), A at surfer select, A at beach select, advance tutorial cards, Start → pause → Down ×2 → **End Run** → A → championship standings.

Screenshots (crops, `/tmp/opencode/thug/`): `right1_g.png` (11-item Extras with four Off), `t2_g.png`/`t4_g.png` (all four active), `beach_only_g.png` (13/13 beaches), `boards_only_g.png` (13/13 boards), `clip_on_g.png` (all 13 clips), `ch_stand_g.png` (Champ: player 10.0, #1), `base_heat2_g.png`/`end_off2_g.png` (baseline 0.0, #7), `wrong2_g.png` (wrong code: no cheat entries), `pers5_g.png` (cold boot: no cheats, music Off persisted).

### THUG — reaching Options

1. Boot, Left, wait, A. Advance logos (A, A, Start). The top-level menu is `STORY / ARCADE / FREE SKATE / HEAD-2-HEAD / SKATE SHOP / OPTIONS`.
2. Options → A. Observed list on a zero-unlock profile: `SOUND, CONTROLS, BLOOD LEVEL: 3, DIFFICULTY, DELETE GAME` — **no CHEATS**.
3. Continuing a story and pausing gives pause → `OPTIONS` → `SOUND, SLEEP` — also **no CHEATS**.

## 4. Address map

### Kelly Slater (base `0x08000000`)

| Address | Meaning |
|---|---|
| `0x08002C68` | text-ID → string pointer: `base=[[0x02003FB4]]`, language record `base+8*lang`, word0 & ~3 = offset of u32 offset table |
| `0x083E9A7C` | text bank header (8 records × 8 bytes); language 1 is English (`+8`, word0=`0x38`) |
| `0x083E9AB4` | English text-offset table; string = `0x083E9AB4 + entry` |
| `0x083EA53F` | `"Extras"` (text ID 14) |
| `0x083EA5DA` | `"(Cheat) Off"` (IDs 28/30/32/34) |
| `0x083EA5E6/600/61A/635` | `"(Cheat) Champ/Beach/Boards/Clips"` (IDs 29/31/33/35) |
| `0x083EA5CB` | `"(Debug) Podium"` (ID 27, unreferenced by both Extras templates) |
| `0x083EA693` / `0x083EA67B` | `"Wave Noise On/Off"` (IDs 43/42, unreferenced) |
| `0x08015B48` | generic list builder: takes a table pointer, builds up to 9 row objects, counts 12-byte records until text ID 0 |
| `0x08015DA0` | list draw: reads `[0x02009060]` count / `[0x02009064]` table, 12-byte records `{u32 text_id, u32 handler, u32 arg}` |
| `0x080102A0` | Extras entry handler: tests `0x0800A8A4(1)` (bit 0 of word B); selects RAM table `0x020000FC` (no cheats) or `0x0200015C` (cheats) |
| `0x02009060` | current menu struct: `{count, item_table_ptr, …, selected}` |
| `0x02000090` | main-menu item table (built at runtime; Mode row inserted first) |
| `0x020000FC` | Extras table A (7 items, no cheats) |
| `0x0200015C` | Extras table B (11 items, with cheats) |
| `0x087D1AD8` | ROM template for Extras A (7 × 12-byte records + 0 terminator) |
| `0x087D1B38` | ROM template for Extras B (11 × 12-byte records + 0 terminator) |
| `0x087C9978` | option struct Champ `{off=0x1C, on=0x1D, get=0x08010130, set=0x0801013C, mask=0x10}` |
| `0x087C998C` | option struct Beach `{0x1E,0x1F,…,0x02}` |
| `0x087C99A0` | option struct Boards `{0x20,0x21,…,0x04}` |
| `0x087C99B4` | option struct Clips `{0x22,0x23,…,0x08}` |
| `0x087C99C8` | option struct Mode `{0x13,0x14,get 0x08010148,set 0x08010158,0}` |
| `0x087C99DC` | option struct Speech `{0x24,0x25,…,0x02}` |
| `0x087C99F0` | option struct Music `{0x28,0x29,…,0x01}` |
| `0x087C9A04` | option struct Sound FX `{0x26,0x27,…,0x04}` |
| `0x08010354` | generic toggle handler: read state, invert, write state, refresh printed text ID |
| `0x0800A880` / `0x0800A8A4` | write / read word B at `0x020041E4` (bit mask in r0) |
| `0x0800A728` / `0x0800A74C` | write / read word A at `0x020041E0` (audio options) |
| `0x020041E0` | word A: sound options |
| `0x020041E4` | **word B: cheat state** (bit0 unlock, `0x02` Beach, `0x04` Boards, `0x08` Clips, `0x10` Champ) |
| `0x020041E8` | current option index |
| `0x020041EC` | option value array; `[0]` = difficulty (0 Amateur, 1 Pro) |
| `0x080103EC` | button-code matcher (12 × u16 expected masks, edge input) |
| `0x087C9A60` | expected sequence table: `0200 0100 0200 0200 0100 0100 0200 0200 0200 0100 0100 0100` |
| `0x0200061C` | sequence progress index (reset on mismatch) |
| `0x080105A0` | per-frame caller; only runs the matcher when current menu table == `0x02000090` |
| `0x08010416` | unlock path: `0x0800A880(mask=1, on=1)` → sets word B bit 0 |

Effect readers:

| Cheat | Reader | Behaviour |
|---|---|---|
| Beach | `0x0801776C`, `0x080177F6` | read mask `0x02`; force beach index `13` / treat every beach as unlocked |
| Boards | `0x08010778`, `0x08017830`, `0x0801B268` | read mask `0x04`; skip the per-item unlock test |
| Clips | `0x0800AF78` | read mask `0x08`; return “all clips available” |
| Champ | `0x08017A36` (inside `0x080179FC`) | read mask `0x10`; return `100` immediately from the 0–100 run-score function |

### THUG (base `0x08800000`)

| Address | Meaning |
|---|---|
| `0x08848E80` | 18-entry pointer table of cheat names |
| `0x08848DAC…0x08848E78` | name strings (lowercase, drawn uppercase) |
| `0x08848EC8` | `"Cheats"` menu title string |
| `0x08848ED0` | `"%s: %s"` format for `name: on/off` |
| `0x08848ED8` / `0x08848EDC` | `"on"` / `"off"` |
| `0x08848B34` | `"New Cheat"` notification string |
| `0x08804B5C` | `get_cheat_name(index) = *(0x08848E80 + index*4)` (Thumb) |
| `0x0200D364` | value named by the standalone CodeBreaker “all cheats unlocked” code (`8200D364 FFFF`); **0 on a fresh profile, and setting it does not expose the menu in this build** |

## 5. Algorithm

### 5.1 Kelly text lookup (needed to enumerate the menu)

```
base = *(u32*)0x02003FB4;            // text bank (0x083E9A7C)
lang = *(u32*)0x02003FB8;            // 1 = English
rec  = base + 8*lang;
tbl  = base + (*(u32*)rec & ~3);     // 0x083E9AB4
str  = tbl + *(u32*)(tbl + 4*id);    // NUL-terminated ASCII
```

### 5.2 Kelly Extras selection

```
on_extras_pressed(arg):
    arg = 0x020000FC
    if read_wordB_bit(1) != 0:       // word B bit 0 = cheats unlocked
        arg = 0x0200015C             // 11-item template
    menu_ptr = arg
    build_list(arg)                  // 0x08015CF4/0x08015B48
```

### 5.3 Kelly toggle handler

```
toggle(struct *s):
    cur = s->get(s->mask)            // bit read
    s->set(s->mask, cur ? 0 : 1)     // inverted write
    refresh_label(s->off_id / s->on_id)
```

### 5.4 Kelly hidden button code

```
if current_menu_table == 0x02000090:           // main menu only
    for each key-press edge:
        if key == seq[index]: index++
        else:                 index = 0
        if index == 12:
            index = 0
            wordB |= 1                          // unlock cheat menu
            play_sound(3)
seq = [L,R,L,L,R,R,L,L,L,R,R,R]                 // 0x0200,0x0100,…
```

### 5.5 Kelly Champ effect

```
run_score_percent():
    if wordB & 0x10: return 100
    ... compute 0..100 from the five surfer stats and the 0/1000/2000/…/30000
        thresholds at 0x087CB7E4, mapped through 0x087CB814 {80,85,90,92,94,96,98,99,100}
```

The championship results screen stores that value into the heat table (0–10 display = value/10), so Champ forces 10.0 and first place.

## 6. Tables

### 6.1 Kelly Extras text IDs

| ID | Text | ID | Text |
|---:|---|---:|---|
| 23 | `Extras Menu` | 34 | `(Cheat) Off` |
| 24 | `Clip Book` | 35 | `(Cheat) Clips` |
| 25 | `Credits` | 36 | `Speech Off` |
| 26 | `Erase Progress` | 37 | `Speech On` |
| 27 | `(Debug) Podium` (unused) | 38 | `Sound FX Off` |
| 28 | `(Cheat) Off` | 39 | `Sound FX On` |
| 29 | `(Cheat) Champ` | 40 | `Music Off` |
| 30 | `(Cheat) Off` | 41 | `Music On` |
| 31 | `(Cheat) Beach` | 42 | `Wave Noise Off` (unused) |
| 32 | `(Cheat) Off` | 43 | `Wave Noise On` (unused) |
| 33 | `(Cheat) Boards` | 44 | `Back` |

### 6.2 Kelly Extras menu tables

Template A (ROM `0x087D1AD8`, 7 rows; also copied to `0x020000FC`):

| # | Text ID | Handler | Arg |
|---:|---:|---|---|
| 0 | 25 Credits | `0x08010304` | `6` |
| 1 | 26 Erase Progress | `0x080102A0` | `0x087C9A18` |
| 2 | 24 Clip Book | `0x08010304` | `7` |
| 3 | 36 Speech Off | `0x08010354` | `0x087C99DC` |
| 4 | 40 Music Off | `0x08010354` | `0x087C99F0` |
| 5 | 38 Sound FX Off | `0x08010354` | `0x087C9A04` |
| 6 | 44 Back | `0x080102A0` | `0x02000090` |

Template B (ROM `0x087D1B38`, 11 rows; copied to `0x0200015C`): the same 7 rows with three cheat rows inserted before Back:

| # | Text ID | Handler | Arg |
|---:|---:|---|---|
| 6 | 30 `(Cheat) Off` → Beach | `0x08010354` | `0x087C998C` |
| 7 | 32 `(Cheat) Off` → Boards | `0x08010354` | `0x087C99A0` |
| 8 | 34 `(Cheat) Off` → Clips | `0x08010354` | `0x087C99B4` |
| 9 | 28 `(Cheat) Off` → Champ | `0x08010354` | `0x087C9978` |
| 10 | 44 Back | `0x080102A0` | `0x02000090` |

On screen the four entries appear in the order **Beach, Boards, Clips, Champ**.

### 6.3 Kelly cheat bit map (`0x020041E4`)

| Bit | Mask | Meaning | Default |
|---:|---:|---|---|
| 0 | `0x0001` | cheat menu unlocked (button code) | 0 |
| 1 | `0x0002` | Beach | 0 |
| 2 | `0x0004` | Boards | 0 |
| 3 | `0x0008` | Clips | 0 |
| 4 | `0x0010` | Champ | 0 |

### 6.4 THUG cheat-name table (`0x08848E80`, 18 slots)

| # | Name | String address | Published unlock (GBA) |
|---:|---|---|---|
| 0 | `stud mode` | `0x08848DAC` | 100% Arcade with Tony Hawk |
| 1 | `rail balance` | `0x08848DB8` | 100% Arcade with Bob Burnquist |
| 2 | `always special` | `0x08848DC8` | 100% Arcade with Steve Caballero |
| 3 | `manual balance` | `0x08848DD8` | 100% Arcade with Kareem Campbell |
| 4 | `moon physics` | `0x08848DE8` | 100% Arcade with Rune Glifberg |
| 5 | `lip balance` | `0x08848DF8` | 100% Arcade with Eric Koston |
| 6 | `jet pack mode` | `0x08848E04` | 100% Arcade with Bucky Lasek |
| 7 | `matrix mode` | `0x08848E14` | 100% Arcade with Bam Margera |
| 8 | `turbo mode` | `0x08848E20` | 100% Arcade with Rodney Mullen |
| 9 | `eclipse` | `0x08848E2C` | 100% Arcade with Chad Muska |
| 10 | `crazy lights` | `0x08848E34` | 100% Arcade with Andrew Reynolds |
| 11 | `mini mode` | `0x08848E44` | 100% Arcade with Geoff Rowley |
| 12 | `No damage` | `0x08848E50` | 100% Arcade with Elissa Steamer |
| 13 | `Monkey mode` | `0x08848E5C` | 100% Arcade with Jamie Thomas |
| 14 | `Programmer Art` | `0x08848E68` | 100% Arcade with Paul Rodriguez, Arto Saari or Mike Vallely |
| 15 | `nergets` | `0x08848E78` | **none published** |
| 16 | `nergets` (duplicate) | `0x08848E78` | **none published** |
| 17 | `nergets` (duplicate) | `0x08848E78` | **none published** |

## 6b. Enumeration

### Kelly Slater — excluded space and complete Extras inventory

* Menu templates in ROM: exactly **two** Extras templates — 7 rows (`0x087D1AD8`) and 11 rows (`0x087D1B38`). The 11-row template is selected only by bit 0 of `0x020041E4`.
* Text IDs in the Extras range: 23–44. Reachable by at least one template: **23 (title), 24, 25, 26, 28–35, 36–41, 44**. Never referenced by either template: **27 `(Debug) Podium`, 42 `Wave Noise Off`, 43 `Wave Noise On`** (proven by the two table dumps above; no third template exists in the ROM — the only 12-byte menu templates near this bank are the main menu, Extras A, Extras B, and the two Yes/No popups at `0x087C9A18`/`0x087C9A3C`).
* Toggle entries: **exactly four** (`Champ`, `Beach`, `Boards`, `Clips`), each with one off string and one active string, each with its own bit.
* **Novel/unpublished result:** the entire GBA system in this section is absent from GameFAQs/VGChartz (their Kelly codes are PS2/Xbox/GC/PC cell-phone numbers). The button code `L R L L R R L L L R R R` and the four toggles are therefore an unpublished combination; the “only Champ” state produces 10.0/#1, and “Beach only” / “Boards only” produce 13/13 on exactly one counter.
* **Bounds by rejection:** a wrong 12-press sequence (12× L) leaves the Extras menu at 7 rows (`wrong2_g.png`); the code is checked only on the main menu, so pressing it in Extras or in a submenu cannot unlock it.
* **Inert entries proven:** `(Debug) Podium` and `Wave Noise` have strings and text IDs but no table row and no option struct in the Extras templates; comparing the RAM table at `0x020000FC`/`0x0200015C` (7/11 rows) with the text-ID map proves they cannot be selected.

### THUG — excluded space and complete cheat inventory

* Name slots: **18** (table at `0x08848E80`), of which 16 strings are distinct and the last three slots all point to `nergets`. Published lists name 15; `nergets` (×3) has no published description.
* The Options menu on a fresh profile contains **5** items and no `Cheats` row; the pause Options contains **2** items and no `Cheats` row. The gating is arcade completion, not a button code, in this build.
* Unlock storage test: the standalone CodeBreaker “all cheats” address `0x0200D364` is zero in a live THUG state; forcing it to `0xFFFF` and reloading the state does **not** add a `Cheats` row to either Options menu. The real gate is therefore not that word in this pack build (see §8).
* `nergets` inertness: the three slots are textual duplicates with no distinct string; whether they have distinct effects cannot be decided without reaching the gated menu (recorded as an unknown, not as “no effect”).

## 7. Validation evidence

**Observed**

* Kelly, cold boot, wrong code → Extras has 7 rows (`wrong2_g.png`); correct code → 11 rows with four `(Cheat) Off` (`right1_g.png`). Reproduced after a full emulator restart.
* Toggling each entry changes its label to `(Cheat) Beach/Boards/Clips/Champ` (`t2_g.png`, `t4_g.png`).
* Beach only: Select a Surfer shows `Beaches unlocked: 13/13`, `Boards: 1/13` (`beach_only_g.png`).
* Boards only: `Beaches: 3/13`, `Boards: 13/13` (`boards_only_g.png`).
* Clips on: Clip Book shows all 13 photos; baseline shows only `Intro` (`clip_on_g.png` vs `clip_base_g.png`).
* All four on: championship heat 1 standings put the player (`M`) at **10.0** and #1; AI scores 7.8, 6.7, 6.5, 6.5, 5.8, 3.7 are unchanged (`ch_stand_g.png`). Baseline (all off) puts the same player at **0.0** and #7 (`end_off2_g.png`).
* Cold boot removes the cheat rows; the saved Music Off survives (`pers5_g.png`). Toggling a cheat does not change the `.sav` hash; toggling Music does (save header counter/checksum at `0x04`–`0x0F` changes).
* THUG Options and pause Options lack `CHEATS` with zero unlocks (`optp3_g.png`, `pp1_g.png`). Patching `0x0200D364` to `0xFFFF` and reloading still lacks it.

**Derived**

* The button code only runs when `[0x02009060+4] == 0x02000090` (`0x080105A0` → `0x080161A0`), which is why the main menu is the only valid entry point.
* The four toggles are the only readers of word B bits 1–4; the five effect readers listed in §4 map each bit to its list/scoring path.
* Champ is the only reader of mask `0x10`; its return of `100` feeds the 0–100 run-score function, hence the 10.0 display.

**Inferred**

* `nergets` is a developer/test placeholder (three identical slots, no published unlock, Latin-script lowercase like the other menu strings).

## 8. Unknowns

* THUG's real “cheats unlocked” condition in this pack build. Published GBA documentation says 100% Arcade with each skater; a zero-unlock profile hides the menu entirely. The standalone CodeBreaker word `0x0200D364` is not the gate here. I did not complete Arcade mode (that is the only documented legitimate route), so no THUG cheat could be toggled or screenshotted in this session. What is proven: the 18-slot table, the 15 published mappings, the three `nergets` placeholders, and the menu's absence on a zero-unlock profile.
* Whether the three `nergets` slots have distinct effects or are pure duplicates; they cannot be reached without the gated menu.
* The exact purpose of the unused Kelly `(Debug) Podium` / `Wave Noise` strings (likely a debug build or an option that was cut).

## 9. Tooling

* `mGBA 0.10.5` (SDL), `Xvfb :116`, `openbox`, `xdotool`, `scrot`, ImageMagick `convert`.
* `arm-none-eabi-objdump -M force-thumb` / default ARM mode; Python 3 + `capstone 5.0.7` for pointer/BL scans.
* Custom scripts in `/tmp/opencode/thug/`: `key.py` (input + cropped screenshots), `ptrscan.py`, text-ID mapper, mGBA PNG-savestate reader/writer (the `gbAs` zlib chunk is at the end; EWRAM is the last `0x40000` bytes, i.e. offset `len-0x40000`; `ss9` was used only as an analysis aid to test the `0x0200D364` hypothesis).
* No GameShark/CodeBreaker code was used to produce any reported effect; the only memory write was the explicitly labelled `0x0200D364` negative test, which had no effect.

## 10. Legal note

No ROM, extracted graphics, audio, or game text is redistributed here beyond short identifiers needed to document the cheat system. Screenshots are emulator output retained only as local evidence in `/tmp/opencode/thug/`.
