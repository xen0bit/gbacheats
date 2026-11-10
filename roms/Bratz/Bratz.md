# Bratz (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `/mnt/gbacheats/roms/Bratz/Bratz.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `BRATZ` (`0xA0`–`0xAB`) |
| Game code | `A2RE` (`0xAC`–`0xAF`) |
| Maker code | `41` (`0xB0`–`0xB1`) |
| Fixed byte `0xB2` | `0x96` |
| Main unit / device | `0x00` / `0x00` |
| Software version | `0x00` |
| Complement check | `0x5F` |
| Header checksum | `0x0000` (normal artifact of a rebuilt/zeroed header; see guide §16.1) |
| Entry word | `0xEA00002E` = stock `b 0x080000C0` (not a cracktro branch) |
| MD5 | `8b809080a689886e7877ec89eb82ae99` |
| SHA-1 | `7372324941f48f5d02f667099de4fafbc96cff86` |
| SHA-256 | `fb4811eac43aa8763d7ebae1ef8296bcbc71da9623331990a42c6209d1c7e93f` |

Embedded-header scan: the full 156-byte Nintendo logo occurs exactly once, at file
offset `0x4` (header base `0x0`). There is no second GBA header, no concatenated
multi-game image, no appended trainer, and no cracktro. The first 4 KiB decode as a
normal ARM crt0. The image is the retail `BRATZ`/`A2RE` Rev.00 build.

Save type: 512-byte SRAM image (`Bratz.sav`). After creating a profile it contains a
small header (the first `0x20` bytes) and `0x1E0` bytes of `0xFF`; no unlock bitfield
was observed in it. The cheat system below is independent of the save file; it writes
session state.

## 2. Executive summary

The game contains a hidden **CHEAT** screen. It is not shown in any normal menu and
has no published documentation. It is reached from the four-item main menu
(PRACTICE / CONTEST / MULTIPLAYER / OPTIONS) by holding **L** and pressing
**B, Up, A, Down** in that order. The screen copies the same letter-grid widget used
for profile-name entry, but with the localized title `CHEAT`
(`TRICHE` / `SECRETOS` / `TRUCCHI` / `PASSWÖRTER`).

The screen accepts **eight-character, uppercase ASCII** strings and compares them
against a fixed table of **15** literals at ROM `0x0833CA50`:

```
FASHIONS  MODELING  TOGETHER  CONTEMPO  TRENDSET  ATTITUDE  SIZZLING
DAZZLING  DECORATE  LIPGLOSS  EXPRESSU  DRESSNUP  CUTNEDGE  HAVINFUN  GOODTIME
```

There is **no checksum, no generator, and no algorithmic second format**. The
validator is exactly fifteen `strcmp`-style comparisons; a miss clears the input and
leaves the player on the CHEAT screen. Codes 0–9 set the Practice song-progress
nibble to 0–9; `GOODTIME` sets it to 10 (all eleven songs); `HAVINFUN` sets all song
and bonus flags; `EXPRESSU`, `DRESSNUP`, and `CUTNEDGE` set three non-song flag bits.

Because the accepted set is a closed 15-entry table, no value outside the table can
be minted. The enumeration deliverable is therefore the complete table, plus an
in-game demonstration of a table member recovered from the ROM and absent from every
published list (`TOGETHER`, progress 2), with the bounds proven by the in-game
rejection of one-character variants. The button-code space is also bounded: the
correct order opens the screen, while wrong order, an extra Right press, and the
absence of L do not.

## 3. How to reproduce

### Emulator and keymap

```bash
Xvfb :204 -screen 0 1024x768x24 &
DISPLAY=:204 openbox &
DISPLAY=:204 SDL_AUDIODRIVER=dummy mgba -3 /mnt/gbacheats/roms/Bratz/Bratz.gba &
```

Default mGBA SDL keymap used throughout:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

### Boot path to the main menu

1. Copyright screen → `Start`.
2. DC Studios logo → `Start`.
3. `CHOOSE LANGUAGE` → English (or any) → `A`.
4. `PRESS START` title → `Start`.
5. `NAME:` entry → any name (or none) → navigate to `OK` → `A`.
6. `CHOOSE A SLOT` → slot 1 → `A`.
7. `CHOOSE DIFFICULTY LEVEL` → any → `A`.
8. Main menu: `PRACTICE`, `CONTEST`, `MULTIPLAYER`, `OPTIONS`.

### Hidden CHEAT screen

On the main menu, **hold L** (`a`) and press, in order:

```
B  ->  Up  ->  A  ->  Down
```

then release L. The CHEAT screen appears. Any `Right`, `Left`, or `R` press during
the sequence resets the progress counter; a wrong button also resets it; the screen
must be the main menu (the same sequence on OPTIONS backs out instead).

### Entering a code

The grid is 15 columns × 4 rows, plus a button row (`◀ B A OK`):

```
A B C D E F G H I J K L M N O
P Q R S T U V W X Y Z É Ä Å Ñ
_ - + , . ! ?   (rest are spaces)
1 2 3 4 5 6 7 8 9 0
◀  B  A  OK
```

Move with the D-pad, `A` selects the highlighted character, `B` backspaces. The
buffer is eight characters; selecting the eighth character automatically moves the
cursor to `OK`. Press `A` on `OK` to submit.

* **Valid code** → the state flags are written, the screen closes, and the main menu
  is shown again.
* **Invalid code** → the grid is cleared and the screen stays open (no error text).

### String reconnaissance and hit classification

`strings -t x -n 4` plus a case-insensitive scan of the whole ROM found:

* `CHEAT` (0x33365C), `TRICHE` (0x333662), `SECRETOS` (0x333669), `TRUCCHI`
  (0x333672), `PASSWÖRTER` (0x33367A) — a five-language menu-title block at
  `0x333648`. This is the real lead; its literal pointer is used by the shared
  text-entry function at `0x0800F0D4`.
* `YOU'VE UNLOCKED` / `You've unlocked` / `A New Combo,` (0x33369C, 0x3336F8,
  0x333754) — unlock-message blocks, consistent with a working cheat reward path.
* `OUTFIT` (0x332CA5), `Select Outfit` (0x33C361), `CHANGE`/`OUTFIT` in the results
  labels — UI labels, not a second code table.
* `SECRETOS` / `SECRET` hits are the Spanish word for "secrets" in the title block,
  not a debug menu. No `debug`, `password`, or `code` debug strings exist in ASCII;
  the German `PASSWÖRTER` is the only password word.
* The alphabet/password bank at `0x33C9D8` is not ASCII menu text in the usual
  sense: it is a 47-symbol character map followed immediately by the 15 passwords.
  Searching for a known code literally (`FASHIONS`, `MODELING`, `GOODTIME`) lands
  directly in this table.

The full 15-code table was recovered by following the `CHEAT` title block into the
text-entry function and reading the 9-byte stride loop, not by guessing a checksum.

### Exact tests used

```bash
# reach the CHEAT screen from a fresh boot (all timings in the helper scripts):
# hold L, tap z, Up, x, Down
python3 /tmp/opencode/bratz/combos.py z,Up,x,Down combo_right

# enter a code from the CHEAT screen:
python3 /tmp/opencode/bratz/typecode.py TOGETHER tog2
# then: A (PRACTICE), A (SELECT SONG), screenshot the song list
```

Screenshots are in `/tmp/opencode/bratz/`; the key ones are named in §§6b and 7.

## 4. Address map

File offset = ROM address − `0x08000000`.

| File offset | ROM address | Contents |
|---:|---:|---|
| `0x33C9D8` | `0x0833C9D8` | 256-byte text/password block copied by the entry screen: first 120 bytes (`0x78`) are the 15×4 uppercase/lowercase grid alphabet; the tail is the 15-entry password table |
| `0x33CA50` | `0x0833CA50` | **15-entry password table**, 9 bytes/entry (`8 ASCII + NUL`), 135 bytes, `0x0833CA50`–`0x0833CAD6` inclusive |
| `0x333648` | `0x08333648` | five pointers to the localized `CHEAT` title |
| `0x33365C` | `0x0833365C` | `CHEAT`; `0x08333662` `TRICHE`; `0x08333669` `SECRETOS`; `0x08333672` `TRUCCHI`; `0x0833367A` `PASSWÖRTER` |
| `0x33369C` | `0x0833369C` | `YOU'VE UNLOCKED` localized block |
| `0x3336F8` | `0x083336F8` | `You've unlocked` block |
| `0x333754` | `0x08333754` | `A New Combo,` block |

| ROM address | Function / role |
|---:|---|
| `0x0800F0D4` | Shared name/cheat text-entry screen. `param_2` = 0 → NAME mode; `param_2` = 1 → CHEAT mode. Contains the 15-entry comparison loop at `0x0800F816`–`0x0800F8E0`. |
| `0x0802E46C` | `strcmp`-style comparator used by the loop (exact, case-sensitive; byte `0x01` in the *table* is treated as a wildcard, but no table entry contains it). |
| `0x0800FC7A` | Main-menu handler; contains the hidden button-code detector at `0x0801009C`–`0x08010118`. |
| `0x080100A6` | Outer gate: loop runs while `KEYINPUT` bit 9 (L) is held. |
| `0x080100B8` | Step 1: B (bit 1). |
| `0x080100D0` | Step 2: Up (bit 6). |
| `0x080100E6` | Step 3: A (bit 0). |
| `0x080100FC` | Step 4: Down (bit 7); if the counter is 3, trigger. |
| `0x0801010C`–`0x08010114` | Sets `state[0x04] |= 0x40000000` (the "open CHEAT" request). |
| `0x080119D2` | Front-end state machine. |
| `0x08011EAE` | Calls the entry screen with `param_2 = 1` (CHEAT mode). `0x08011C46` calls it with `param_2 = 0` (NAME mode). |
| `0x08007516` | Song-select screen. Reads Practice progress from `state[0x0C] & 0x0F`, Contest progress from `(state[0x0C] >> 20) & 0x0F`. A song index is unlocked iff `index <= progress`; locked songs are drawn with sprite ID `0xB5`. |

RAM: the front-end state structure is stack-local in `FUN_080145DA`, passed to
`FUN_080119D2`; it has no fixed EWRAM/IWRAM address. The relevant fields are:

| Field | Meaning |
|---|---|
| `+0x04` bit 31 | bonus/outfit flag set by `EXPRESSU` and `HAVINFUN` |
| `+0x04` bit 30 | transient "open CHEAT screen" request (set by the button code, cleared after the screen) |
| `+0x08` bit 0 | bonus flag set by `DRESSNUP` |
| `+0x08` bit 1 | bonus flag set by `CUTNEDGE` |
| `+0x0C` bits 0–3 | Practice song progress, 0–10 |
| `+0x0C` bits 20–23 | Contest song progress, 0–9 |

## 5. Algorithm

### 5.1 Hidden button code (`0x0801009C`)

```c
// runs every frame while the main menu is displayed; keys is the game's
// logical key state (1 = pressed), not the raw active-low KEYINPUT word.
if (keys & L) {
    int step = 0;
    while (keys & L) {
        poll_keys();
        if (keys & B) {
            if (step == 0) step = 1; else step = 0;
        } else if (keys & Up) {
            if (step == 1) step = 2; else step = 0;
        } else if (keys & A) {
            if (step == 2) step = 3; else step = 0;
        } else if (keys & Down) {
            if (step == 3) {
                state[0x04] |= 0x40000000;  // request CHEAT screen
                break;
            } else step = 0;
        }
        if (keys & (Right | Left | R)) step = 0;
    }
}
```

The bit numbers in the ROM are L=9, B=1, Up=6, A=0, Down=7, Right=4, Left=5,
R=8. The source tests the game's logical key state (1 = pressed), not the raw
active-low `KEYINPUT` word.

### 5.2 CHEAT validator (`0x0800F0D4`, mode 1)

```c
char input[9] = {0};       // eight characters + NUL
int  len = 0;

// ... grid input loop; on the 8th character len becomes 7 and the
// cursor is moved to OK.  Pressing A on OK executes:
if (mode == 1) {
    for (int i = 0; i < 15; i++) {
        if (strcmp(ROM_0833CA50 + i*9, input) == 0) {
            if (i < 10) {
                state[0x0C] = (state[0x0C] & ~0x0F) | i;      // Practice progress
            } else if (i == 10) {
                state[0x04] |= 0x80000000;                    // bonus flag
            } else if (i == 11) {
                state[0x08] |= 0x00000001;                    // bonus flag
            } else if (i == 12) {
                state[0x08] |= 0x00000002;                    // bonus flag
            } else if (i == 13) {
                state[0x04] |= 0x80000000;
                state[0x0C] = (state[0x0C] & ~0x0F) | 10;      // Practice = all
                state[0x0C] = (state[0x0C] & 0xFF0FFFFF) | 0x00900000; // Contest = 9
                state[0x0C] = (state[0x0C] & 0xFFFFFE0F) | 0x00000120;
                state[0x0C] = (state[0x0C] & 0xFFF07FFF) | 0x00088000;
                state[0x0C] = (state[0x0C] & 0xFFFF81FF) | 0x00004600;
                state[0x0C] = (state[0x0C] & 0xE0FFFFFF) | 0x08000000;
            } else if (i == 14) {
                state[0x0C] = (state[0x0C] & ~0x0F) | 10;      // Practice = all
            }
            state[0x18] = 1;                 // "changed" flag
            state[0x08] &= ~0x38;            // close the entry screen
            break;
        }
    }
    // No match: clear input and stay on the CHEAT screen.
}
```

The literal loop is implemented as a real loop: `0x0800F816` tests `i < 15`,
`0x0800F82A` calls the comparator, and the success writes are at
`0x0800F832`–`0x0800F8DE`.

### 5.3 Song-unlock consumer (`0x08007516`)

```c
if (mode == CONTEST) {
    progress = (state[0x0C] >> 20) & 0x0F;
    max_song = 9;                 // ten Contest songs
} else {
    progress = state[0x0C] & 0x0F;
    max_song = 10;                // eleven Practice songs
}
// For each of the seven carousel slots:
if (song_index > progress)
    draw_locked_song();           // sprite 0xB5
else
    draw_song_thumbnail(song_index);
```

This is why a progress nibble of 0 leaves only `All Eyes On Me` visible, 1 adds
`Mixin' N Matchin'`, 2 adds `Make Me Up`, and 10 reveals the whole strip.

## 6. Tables

### 6.1 The 15 accepted codes

| Index | Code | State write | In-game effect |
|---:|---|---|---|
| 0 | `FASHIONS` | Practice progress = 0 | 1 song (index 0 only; `All Eyes On Me`) |
| 1 | `MODELING` | Practice progress = 1 | 2 songs (indices 0–1; adds `Mixin' N Matchin'`) |
| 2 | `TOGETHER` | Practice progress = 2 | 3 songs (indices 0–2; adds `Make Me Up`) |
| 3 | `CONTEMPO` | Practice progress = 3 | 4 songs (indices 0–3) |
| 4 | `TRENDSET` | Practice progress = 4 | 5 songs (indices 0–4) |
| 5 | `ATTITUDE` | Practice progress = 5 | 6 songs (indices 0–5) |
| 6 | `SIZZLING` | Practice progress = 6 | 7 songs (indices 0–6) |
| 7 | `DAZZLING` | Practice progress = 7 | 8 songs (indices 0–7) |
| 8 | `DECORATE` | Practice progress = 8 | 9 songs (indices 0–8) |
| 9 | `LIPGLOSS` | Practice progress = 9 | 10 songs (indices 0–9) |
| 10 | `EXPRESSU` | `state[0x04] |= 0x80000000` | bonus flag; no song change observed |
| 11 | `DRESSNUP` | `state[0x08] |= 0x01` | bonus flag; no song change observed |
| 12 | `CUTNEDGE` | `state[0x08] |= 0x02` | bonus flag; no song change observed |
| 13 | `HAVINFUN` | Practice = 10, Contest = 9, `0x80000000`, packed bits | all 11 Practice songs; all bonus flags |
| 14 | `GOODTIME` | Practice = 10 | all 11 Practice songs (indices 0–10) |

Practice song order (from the ROM's song-name block at `0x08339CF8`):
`All Eyes On Me`, `Mixin' N Matchin'`, `Make Me Up`, `Settin' Sail`, `Strut It`,
`Check You Out`, `Cruisin' By`, `Start the Party`, `Love Lookin' At Me`,
`Funk It Up`, `Lookin' Good!`.

### 6.2 Input alphabet

The CHEAT screen's grid is 47 distinct symbols:

```
ABCDEFGHIJKLMNO PQRSTUVWXYZÉÄÅÑ _-+,.!? 1234567890
```

The stored codes use only `A`–`Z`. The comparator is exact and case-sensitive; the
lowercase alphabet exists only in NAME mode (the case-toggle branch is inside the
`param_2 == 0` path and has no effect in CHEAT mode).

### 6.3 Localized CHEAT title

| Language | Pointer | String |
|---|---|---|
| English | `0x0833365C` | `CHEAT` |
| French | `0x08333662` | `TRICHE` |
| Spanish | `0x08333669` | `SECRETOS` |
| Italian | `0x08333672` | `TRUCCHI` |
| German | `0x0833367A` | `PASSWÖRTER` |

## 6b. Enumeration

### Space definition

* Input length: 0–8 symbols (the buffer is zero-initialised, so byte 8 is always
  NUL; the ninth symbol cannot be entered). Only an 8-symbol input can equal an
  entry; shorter inputs are prefixes and are rejected.
* Alphabet: 47 symbols (see §6.2), ASCII/Latin-1 bytes, case-sensitive.
* Representable 8-symbol space: `47^8 = 23,811,286,661,761` (≈`2.38 × 10^13`).
* Validator: 15 exact `strcmp`s; no checksum, no key table, no generator, no
  reserved bits. Accepted set size: **15**.

### Offline validator

`/tmp/opencode/bratz/validate.py` reimplements the table and comparator directly
from the ROM bytes:

```
table entries: 15
 0 0x0833CA50 FASHIONS  accepted=True
 ...
14 0x0833CACE GOODTIME  accepted=True
hamming-1 tests: 5520, unexpected accepts: 0
random tests: 200000, hits: 0
probe 'TOGETHE'      accepted=False
probe 'TOGETHERX'    accepted=False
probe 'FASHIONZ'     accepted=False
UI alphabet size: 47; 8-symbol space: 23811286661761 (2.381e+13); accepted: 15
```

The 5,520 tests are every one-character substitution of every table entry across the
47-symbol alphabet (15 × 8 × 46). None is accepted. This is a full Hamming-distance-1
neighbourhood proof and a strong closure check; the structural argument (only one
accept path in `0x0800F0D4`) proves it for the whole space.

### Novel / unpublished code entered in-game

`TOGETHER` (entry 2) was recovered by enumerating the ROM table; it appears in no
reachable published Bratz GBA cheat list (see the published-code search below). Entered through
the hidden CHEAT screen it produced Practice progress 2: the thumbnails for song
indices 0, 1, and 2 are revealed (`All Eyes On Me`, `Mixin' N Matchin'`, `Make Me
Up`), while the positions left of centre are still `?`.

* `tog2_song.png` — observed effect (three consecutive revealed thumbnails).
* `tog2_menu.png` — return to the main menu after acceptance.

Published-code search: GameFAQs returned 403 for this title; archive.org was
temporarily offline; VGChartz lists 0 cheats for the related `Bratz: Rock Angelz`
GBA. Searches for the 15 literals and for "Bratz GBA password/cheat" returned only
`Rock Angelz` / `Forever Diamondz` material (`SIZZLN`, `FLAUNT`, `YASMIN`, `FIERCE`,
etc.), which uses different 5–8 letter codes on a different engine. None of the 15
literals above appears in any reachable published list.

Because the system is a closed table rather than a generator, a value outside the 15
cannot be minted. This is stated as the bound, not as a failure: the complete
accepted set is exactly the 15 entries above.

### Bounds proven by rejection

| Test | Input | Observed |
|---|---|---|
| one-character variant of a valid code | `TOGETHEX` | CHEAT screen stays (input cleared; `rej_clear2.png` shows the screen still active after an invalid submit); Practice song list still shows only song 0 (`togx_song.png`) |
| another near-miss | `FASHIONZ` | same; song list unchanged (`rej_songs.png`) |
| short prefix | `TOGETHE` (7 chars) | rejected by the offline validator; a 7-character input cannot equal an 8-character entry |
| wrong button order | L + B, A, Up, Down | main menu remains; no CHEAT screen (`combo_wrong_after.png`) |
| extra Right in sequence | L + B, Up, Right, A, Down | main menu remains; Right resets the sequence (`combo_reset2_after.png`) |
| correct button order | L + B, Up, A, Down | CHEAT screen opens (`combo_right_after.png`) |

The offline validator's 200,000 random 8-symbol strings produced zero accepts; the
5,520 Hamming-1 probes produced zero accepts.

## 7. Validation evidence

### Observed (emulator screenshots / game behaviour)

* Hidden CHEAT screen opens only with L + B, Up, A, Down on the main menu;
  `combo_right_after.png`.
* Wrong order and an extra Right press do not open it;
  `combo_wrong_after.png`, `combo_reset2_after.png`.
* Without L the same button presses are consumed as ordinary menu navigation and do
  not open the CHEAT screen (`combo_noL_after.png`).
* `FASHIONS` leaves one Practice song; `MODELING` reveals one more; `TOGETHER`
  reveals two more; `GOODTIME` and `HAVINFUN` reveal the whole visible strip;
  `tog2_song.png`, `good_song.png`, `enum_13_HAVINFUN.png`.
* Invalid `TOGETHEX` and `FASHIONZ` leave the song list unchanged;
  `togx_song.png`, `rej_songs.png`. An invalid submit does not return to the main
  menu; the CHEAT screen stays active (the same A press is then seen starting a
  new entry, `rej_clear2.png`).
* All normal menus walked: language, name entry, slot select, difficulty, main
  menu, Practice song select, gameplay, pause, Options (Erase, Languages,
  Difficulty, High Scores, Credits), Multiplayer connection screen, Help, CHEAT.
* The CHEAT screen title is literally `CHEAT`; the same widget with mode 0 shows
  `NAME:`.

### Derived (disassembly / decompiler / ROM bytes)

* The password table is 15 records of 9 bytes at `0x0833CA50`; the loop tests
  `i < 15` and calls the comparator.
* Code index 0–9 writes the Practice progress nibble; index 10/13 sets `0x80000000`;
  index 11/12 sets `0x08` bits 0/1; index 13/14 set Practice progress 10; index 13
  also sets Contest progress 9 and the extra packed bits.
* `FUN_08007516` consumes the Practice and Contest progress nibbles and draws locked
  songs with sprite `0xB5` when `index > progress`.
* The button sequence is a four-step counter gated on L, with reset on
  Right/Left/R.

### Inferred (plausible, not fully exercised)

* The three non-song flags (`0x04` bit 31, `0x08` bits 0/1) are bonus/outfit
  unlocks. Their consumer screen was not reached in the evaluated boot/menu space;
  see §8.
* The extra packed bits written by `HAVINFUN` (`0x0C` bits 5, 8, 9, 10, 14, 15, 19,
  27) are additional unlock flags for the same bonus system.

## 8. Unknowns

1. **Exact target of the three bonus flags.** `EXPRESSU`, `DRESSNUP`, and
   `CUTNEDGE` are accepted and their bit writes are proven, but the UI that consumes
   those bits was not reached. Practice has no outfit-change screen in the boot/
   menu flow; the game's bottom-bar hint `Select Outfit` belongs to the Contest
   character screen, whose outfit carousel we could not open from a fresh save
   without completing a Contest song. The pause menu remains `CONTINUE`/`QUIT`
   even with `HAVINFUN` applied (`pause_hav.png`), so the flags do not add pause
   entries.
2. **Persistence.** The cheat writes session state, not the 512-byte save image; the
   `.sav` remained essentially empty (`0x20`-byte header, `0x1E0` bytes `0xFF`), with
   no unlock bitfield observed. Whether the next Contest auto-save copies the flags
   into the save file was not exercised.
3. **Contest song count.** The consumer uses Contest progress 0–9 (ten songs) and
   Practice progress 0–10 (eleven songs). The one extra Practice song
   (`Lookin' Good!`) is not addressable by any single table code except
   `GOODTIME`/`HAVINFUN` (progress 10).
4. **The `0x01` wildcard.** The comparator treats byte `0x01` in the *table* as a
   wildcard, but no table entry contains `0x01` and the on-screen keyboard cannot
   produce it. It is not a reachable extension of the code space.

## 9. Tooling

* `mgba` 0.10.5 (SDL), Xvfb `:204`, openbox, scrot, ImageMagick.
* `arm-none-eabi-objdump` (Thumb disassembly), Python 3 + Capstone for literal/BL
  scans, REA/Ghidra 12.1.4 for decompilation and xrefs.
* Helper scripts (all in `/tmp/opencode/bratz/`):
  * `keys.py` — focus, key hold/tap, screenshot + crop.
  * `combos.py` — main-menu button-code driver with optional L hold.
  * `typecode.py` — grid navigator/typer for the CHEAT screen.
  * `validate.py` — offline table + comparator + Hamming-1/random enumeration.
  * `enumerate.py` — 15-code acceptance/effect capture.
* Key screenshots: `combo_right_after.png`, `combo_wrong_after.png`,
  `combo_reset2_after.png`, `tog2_song.png`, `tog2_menu.png`, `rej_clear2.png`,
  `togx_song.png`, `rej_songs.png`, `good_song.png`, `enum_13_HAVINFUN.png`,
  `pause_hav.png`, `credits_en.png`.
* Menu-walk screenshots: `boot4.png` (language), `menu1.png` (title),
  `mm5.png` (name entry), `mm9.png` (slot), `mm10.png` (difficulty),
  `mm11.png` (main menu), `pr2.png` (Practice song select), `pause1b.png` (pause),
  `opts_en.png` (Options root), `w_erase.png` (Erase slot), `w_lang.png`
  (Languages), `w_scores.png`/`cur3.png` (High Scores), `credits_en.png` (Credits),
  `w_mp.png` (Multiplayer), `combo_right_after.png` (CHEAT).

## 10. Legal note

No ROM, graphics, music, or text assets are redistributed. This report contains
only hashes, addresses, algorithms, the 15 developer password literals, and
screenshots of the game's own UI for evidence.
