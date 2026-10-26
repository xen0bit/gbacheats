# Batman Begins (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Batman Begins/Batman Begins.gba` |
| Size | 16,777,216 bytes (16 MiB) |
| Header title | `BATMANBEGINS` |
| Game code | `BBGE` |
| Maker code | `69` |
| Software version | `0x00` |
| Entry | `0xEA00002E` (ARM branch to `0x080000C0`) |
| Fixed byte `0xB2` | `0x96` |
| Header complement | stored `0x67`, computed `0x63` |
| Header checksum | stored `0x0000`, computed `0x0099` |
| MD5 | `8c48059bf2c40a78b9739edf5ea411cb` |
| SHA-1 | `05c7c1bea2b0cb77976e07c8f2a8b0ef5d1f5685` |
| SHA-256 | `1cf4376fb235252b43b4365527914e356a9af9c6299eee90ab6b138bae05f6bd` |

The SHA-1/MD5 match the verified No-Intro/TASVideos dump for the US/EU
release, so the ROM is not a modified image. The complement and header
checksum fields are wrong **in the verified dump itself**; they are recorded
here as a shipped-header quirk, not evidence of a patch.

Embedded-header scan: searching the whole file for the 156-byte Nintendo logo
returns one hit only, at file offset `0x04`. The file is a single GBA image, not
a multi-game pack and not a concatenated image.

File offset ↔ ROM address: `rom_address = 0x08000000 + file_offset`.

## 2. Executive summary

Batman Begins (GBA) has **no password screen**. Its developer-intended cheat
entry is the **Pause menu**, and the mechanism is a hidden button-code object in
EWRAM:

* every newly pressed button while paused is translated into one character
  (`Up/Down/Left/Right` → `u/d/l/r`, `B` → `B`, shoulder `L/R` → `L/R`, every
  other key → space) and appended to a **10-byte ring buffer**;
* the object holds **8 slots**, each `{8-character string, one toggle flag}`;
* after every append the validator compares the **last 8 characters** of the
  ring with each of the 8 strings and, on a match, **XORs the slot flag**
  (i.e. each code is a toggle, not a one-shot unlock).

Slot contents (all 8 enumerated; strings at ROM `0x080374A0`):

| Slot | String | Flag (EWRAM) | Meaning | Status |
|---:|---|---|---|---|
| 0 | `LRLRuudd` | `0x02008054` | super jump (jump velocity doubled) | reachable code |
| 1 | `uuddlrlr` | `0x02008055` | hit reaction / damage path skipped | reachable code |
| 2 | `xxxxxxxx` | `0x02008056` | no reader found in this build | sentinel, unreachable |
| 3 | `rrrlllud` | `0x02008057` | super speed (movement value doubled) | reachable code |
| 4 | `xxxxxxxx` | `0x02008058` | debug HUD (`world/level/hard/flags`) | sentinel, unreachable |
| 5 | `udududLR` | `0x02008059` | HUD / graphics overlay hidden | reachable code |
| 6 | `xxxxxxxx` | `0x0200805A` | entity predicate (forced true) | sentinel, unreachable |
| 7 | `xxxxxxxx` | `0x0200805B` | entity predicate (forced true) | sentinel, unreachable |

The four real strings are exactly the four codes published on GameFAQs and
SuperCheats. All four were verified against the ROM literal and accepted by the
game. The claim on some fan pages that **Hard Mode must be unlocked first is
false**: every code worked on a fresh, 0 %-complete Game 1 save (observed).

Because the validator is a suffix match over a rolling buffer, the accepted
input space is larger than the published 8-press list. A 10-press sequence
`Up,Up,Up,Down,Up,Down,Up,Down,L(shoulder),R(shoulder)` (mapped string
`uuudududLR`) was entered on the same save, toggled slot 5, and made the HUD
disappear; that exact input is in no published list. Re-entering a code toggles
its flag back off (also not documented publicly).

The four `xxxxxxxx` slots are **not reachable from the controller**. The
key→character mapper has no branch that produces `x`; `x` is outside the
reachable alphabet. Slot 4 (`0x02008058`) is the debug-HUD flag documented by
TCRF under CodeBreaker address `02008058:01`; that is a memory edit and is out
of scope here. Slots 2, 6 and 7 are likewise only settable by memory edit.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL (`/usr/games/mgba`), `-3` scale, under
`Xvfb :174 -screen 0 1024x768x24`, with `SDL_AUDIODRIVER=dummy` and `openbox`.
Default mGBA keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrow keys. Hold keys 100–200 ms; a 10 ms tap can be
missed.

Boot path:

1. Language screen → `A` (ENGLISH).
2. EA / Warner logos → `Start` (skip).
3. Main menu (`START GAME`, `VIEW CREDITS`) → `START GAME`.
4. `SELECT A GAME` → `GAME 1` (or a `NEW GAME` slot) → `A`.
5. In the prologue, press `Start` to open `PAUSE` (`RESUME`, `QUIT LEVEL`,
   `SLEEP`, `SOUND`).

Code entry / test:

1. Open `PAUSE`. Enter the button sequence. Every press is captured by the
   cheat object **and** still moves the pause cursor, so the cursor ends where
   the net Up/Down count says. All four canonical codes have net movement 0 and
   therefore leave the cursor on `RESUME` when it started there; press `A` to
   resume and observe the effect.
2. To verify the flag directly, save a state (`Shift+F1`…`Shift+F10`) while
   still paused and parse it (see §9).

Published codes (GameFAQs archive snapshot 2023-07-25, SuperCheats) and result:

| Effect | Published presses | Mapped string | In ROM? | Result |
|---|---|---|---|---|
| Enemies can't hit you | Up,Up,Down,Down,Left,Right,Left,Right | `uuddlrlr` | yes `0x080374AC` | flag 1 set |
| Remove graphics | Up,Down,Up,Down,Up,Down,L,R *(shoulders)* | `udududLR` | yes `0x080374C4` | flag 5 set, HUD off |
| Super Jump | L,R,L,R,Up,Up,Down,Down *(shoulders)* | `LRLRuudd` | yes `0x080374A0` | flag 0 set, jump higher |
| Super Speed | Right,Right,Right,Left,Left,Left,Up,Down | `rrrlllud` | yes `0x080374B8` | flag 3 set, faster run |
| “Super Jump” (9-press variant, great-games snippet) | L,R,L,R,Up,Up,Up,Down,Down | `LRLRuuudd` | **no** | rejected, flag 0 |

Unpublished-code test:

```
PAUSE
Up Up Up Down Up Down Up Down L(shoulder) R(shoulder)
Up Up          # compensating cursor movement (net prefix moved cursor -2)
A              # resume
```

Result: HUD (bat emblems / counter) absent, slot-5 flag = 1.

### 3.1 Reconnaissance and published-code verification

ASCII searches over the whole 16 MiB (case-insensitive) and their classification:

| Needle | Hits | Classification |
|---|---:|---|
| `password`, `passcode`, `cheat`, `debug`, `level select` | 0 | absent as text — no password/cheat screen |
| `pass code` | 1 | story dialogue (“you'll need a pass code to enter”), not an input screen |
| `secret` | 3 | story dialogue |
| `code` | 5 | story dialogue |
| `unlock` | 9 | story dialogue + `HARD MODE UNLOCKED!` `0x98620`, `MENUS UNLOCKED!` `0x98648` (plus FR/DE/IT/NL copies) |
| `select a stage` | 1 | `0x9394C` — debug leftover, no reachable menu |
| `enter initials` | 1 | `0x93B1C` — debug leftover, no reachable menu |
| `xxxxxxxx` | 56 | mostly graphics data; the cheat-table instance is `0x080374D0` |
| `uuddlrlr`, `LRLRuudd`, `rrrlllud`, `udududLR` | 1 each | the four live cheat strings (`0x080374AC`, `A0`, `B8`, `C4`) |

Other debug leftovers found in the same string bank and checked against the
walked UI: `Select a Stage` (`0x9394C`), `Defeat Level` (`0x93B50`),
`Defeat Level 100%` (`0x93B64`), `Slow Motion` (`0x93B7C`), `Enter Initials`
(`0x93B1C`), and `world:%d  level:%d  hard:%d flags:%x` (`0x66B04`). None is
reachable from a menu; the pause menu exposes only Resume/Quit Level/Sleep/
Sound, and the title exposes only Start Game/View Credits.

Published-source handling: GameFAQs returned 403 directly and was read from the
Wayback snapshot of 2023-07-25; SuperCheats was fetched directly; TCRF returned
403 directly and was read from the 2024-12-17 Wayback snapshot; the fandom page
returned 403, so only its search snippet was used and its claims were tested
against the ROM/emulator. VGChartz was not needed. Every published code was
checked as a literal in the ROM before being tested in-game.

Key-mask scans were also run: the published sequences encoded as `u16` button
masks (`0x0040,0x0040,0x0080,…`), as `u8` masks, as 32-bit masks, and as 4-bit
button indices all returned **zero** hits. The codes are not stored as masks;
they are ASCII strings compared against the pause-menu character buffer. This
is why the first literal scan for `UUDDLRLR` also failed while lowercase
`uuddlrlr` hit `0x374AC` immediately.

Rejection tests:

* `Up Down Up Down Up Down Left Right` (arrow keys for the last two, i.e.
  lowercase `l r`) → buffer `udududlr`, no flag.
* 9-press variant above → buffer ends `RLRuuudd`, no flag.
* `Up` × 8 → buffer `uuuuuuuu`, no flag.
* `Up Down Left Right B L R B` → buffer `udlrBLRB`, no flag; proves no `x`.
* All sentinel flags remained 0 in every test.

## 4. Address map

### ROM / data

| Address | Content |
|---|---|
| `0x080374A0` | `"LRLRuudd"` slot-0 code string (12-byte NUL-padded record) |
| `0x080374AC` | `"uuddlrlr"` slot-1 code string |
| `0x080374B8` | `"rrrlllud"` slot-3 code string |
| `0x080374C4` | `"udududLR"` slot-5 code string |
| `0x080374D0` | `"xxxxxxxx"` sentinel, shared by slots 2/4/6/7 |
| `0x08066B04` | `"world:%d  level:%d  hard:%d flags:%x"` debug-HUD format |
| `0x080D1950` (len `0x100`) | buffer/id passed to sound engine after a match |

### EWRAM cheat object — base `0x02008034`

| Offset | Size | Meaning |
|---:|---:|---|
| `+0x00` | `0x20` | 8 × `char*` code strings |
| `+0x20` | 8 | 8 toggle flags (`flags[0]` at `0x02008054`) |
| `+0x28` | 4 | ring-buffer index (0…9) |
| `+0x2C` | 10 | character ring buffer |
| `+0x36` | 1 | NUL terminator for the comparison copy |

### Code / functions

| Address | Role |
|---|---|
| `0x080130E4` | key read: `~REG_KEYINPUT & 0x03FF` (active-high mask) |
| `0x020081A8` | input object; `+0x10` = newly-pressed key mask |
| `0x08014370` | pause-menu key handler; if `pressed != 0` calls the mapper with the cheat object |
| `0x08002C70` | **key → character mapper + append + validate call** |
| `0x08002AA4` | **validator** (8 slots, suffix match, toggle flag) |
| `0x08002CFC` | object reset (flags = 0, buffer = 10 × `'-'`, index = 0) |
| `0x08002CEC` | slot setter (`obj->codes[i] = ptr`) |
| `0x08002BE4` | constructor variant with hard-coded object `0x02003480`; that EWRAM area already holds level data in the boot savestate, so this variant does not populate the retail cheat object |
| `0x08002D84` | live constructor (object pointer argument; it is the one that populated `0x02008034` at boot — observed in a boot savestate) |
| `0x080349F8` | string length helper |
| `0x08034948` | string compare helper |
| `0x08000278` / `0x08000282` | multiply/divide-or-modulo helpers used for the ring index and compare index |
| `0x08002CF4` | flag getter: `return *(u8*)(base + 0x20 + i)` |

### Flag readers (readers of `flags[i]`)

| Slot | Reader address | What it gates |
|---:|---|---|
| 0 | `0x0801CBCA` | if flag 0: doubles a jump value (`ldr r0,[sp]; lsls r0,#1`) |
| 1 | `0x0801ACE4`, `0x0801D418`, `0x0801D542` | hit-reaction/damage paths jump to the function epilogue when set |
| 3 | `0x0801D3BA`, `0x0801DEB4` | if flag 3: doubles a movement value before the movement helper |
| 4 | `0x0800E5F2` (in `0x0800E5E8`), `0x0800E684` (in `0x0800E660`) | debug-HUD drawing; `0x0800E660` formats `0x08066B04` |
| 5 | `0x0800E61A`, `0x0800E638` | skips the HUD/overlay draw call (`0x08014C6C`) when set |
| 6 | `0x0800D990` (inside `0x0800D988`) | returns `obj->byte14 != 0 \|\| flag6` |
| 7 | `0x0800DCE0` (inside `0x0800DCD8`) | returns `obj->byte28 != 0 \|\| flag7` |
| 2 | — | no reader found |

## 5. Algorithm

### 5.1 Character mapping (`0x08002C70`)

```c
void cheat_key(Cheat *c, u16 pressed) {       // pressed = newly pressed, active-high
    u8 ch = 0x20;                             // default: space (A, Start, Select, combos)
    switch (pressed) {
        case 0x0040: ch = 'u'; break;         // Up
        case 0x0080: ch = 'd'; break;         // Down
        case 0x0020: ch = 'l'; break;         // Left
        case 0x0010: ch = 'r'; break;         // Right
        case 0x0002: ch = 'B'; break;         // B
        case 0x0100: ch = 'R'; break;         // R shoulder
        case 0x0200: ch = 'L'; break;         // L shoulder
    }
    c->buf[c->idx] = ch;
    c->idx = (c->idx + 1) % 10;
    cheat_validate(c);
}
```

`pressed` comes from the engine input object at `0x020081A8 + 0x10`; the raw
keypad register is read at `0x080130E4` as `~REG_KEYINPUT & 0x03FF`, so the
masks above are the standard GBA order (`A=1, B=2, Select=4, Start=8,
Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200`).

### 5.2 Validator (`0x08002AA4`)

```c
void cheat_validate(Cheat *c) {
    for (int slot = 0; slot < 8; slot++) {
        const char *code = c->codes[slot];
        int n = strlen(code);                 // all entries are 8
        char tmp[12];
        int start = (c->idx - n) % 10;        // index arithmetic via 0x08000282
        if (start < 0) start += 10;
        for (int j = 0; j < n; j++)
            tmp[j] = c->buf[(start + j) % 10];
        tmp[n] = 0;
        if (strcmp(tmp, code) == 0) {
            c->flags[slot] ^= 1;              // TOGGLE
            play_sound(0x080D1950, 0x100);    // sound-engine call at 0x08024B54/0x080249C4
        }
    }
}
```

There is **no checksum, no length check and no range check**. A match is an
exact 8-character suffix of the 10-character ring; the only “rejection” is the
absence of a match (silent, apart from the sound cue on success). The index is
always in `0..9`; codes shorter/longer than 8 are handled by the same logic but
none exist in this table.

### 5.3 Toggle semantics

The flag update is `flags[slot] ^= 1`, not `= 1`. Entering any code twice in a
row returns its flag to 0. All four effects can therefore be switched off in
game without a reset (observed for slot 5; flag evidence for the others).

## 6. Tables

### 6.1 Slot table (complete)

```
slot  code       ROM string   flag address   reader(s)
0     LRLRuudd   0x080374A0   0x02008054     0x0801CBCA
1     uuddlrlr   0x080374AC   0x02008055     0x0801ACE4,0x0801D418,0x0801D542
2     xxxxxxxx   0x080374D0   0x02008056     (none)
3     rrrlllud   0x080374B8   0x02008057     0x0801D3BA,0x0801DEB4
4     xxxxxxxx   0x080374D0   0x02008058     0x0800E5F2,0x0800E684
5     udududLR   0x080374C4   0x02008059     0x0800E61A,0x0800E638
6     xxxxxxxx   0x080374D0   0x0200805A     0x0800D990
7     xxxxxxxx   0x080374D0   0x0200805B     0x0800DCE0
```

### 6.2 Button → character map

| Key | Mask (pressed) | Char | Hex |
|---|---:|---|---:|
| Up | `0x0040` | `u` | `0x75` |
| Down | `0x0080` | `d` | `0x64` |
| Left | `0x0020` | `l` | `0x6C` |
| Right | `0x0010` | `r` | `0x72` |
| B | `0x0002` | `B` | `0x42` |
| R shoulder | `0x0100` | `R` | `0x52` |
| L shoulder | `0x0200` | `L` | `0x4C` |
| A / Start / Select / any combo | `0x0001`/`0x0008`/`0x0004`/… | space | `0x20` |

Case matters: `l`/`r` (D-pad) are not `L`/`R` (shoulders).

### 6.3 Published lists vs ROM

* GameFAQs (archive 2023-07-25): four codes, exactly the four ROM strings.
* SuperCheats: same four; a second submitter gives the 8-press super jump
  (`L,R,L,R,Up,Up,Down,Down`), which is the one in the ROM.
* great-games.fandom search snippet: gives a 9-press super jump
  (`L,R,L,R,Up,Up,Up,Down,Down`) and says codes require Hard Mode. The 9-press
  string is absent from the ROM and was rejected in the emulator; Hard Mode was
  not unlocked and all four real codes worked.
* TCRF: `CodeBreaker 02008058:01` enables the debug display. `0x02008058` is
  slot-4’s flag; the display format string and reader are mapped above. This is
  a memory-edit route, not a controller code, and is out of scope.

## 6b. Enumeration

**Space definition.** 8 slots; 4 distinct 8-character strings plus one
sentinel string repeated in 4 slots. Input buffer is 10 characters. Reachable
character alphabet from buttons is 8 symbols (`u d l r B L R space`); the four
real codes use only `u d l r L R` (6 symbols). There is no checksum and no
length field; acceptance is “last 8 mapped characters equal one of four
strings”. Flag state space is `2^8 = 256`; the controller can reach only the
four bits for slots 0,1,3,5, i.e. **16 flag combinations**. For a fixed length
of 10 presses there are 4 codes × 8² prefixes = **256 sequence strings**, of
which 4 are the canonical 8-press codes and 252 are longer variants; a prefix
that itself contains a complete code can produce an earlier toggle, so the net
effect of a few of the 256 can be “off” rather than “on”.

**Novel code (not in any published list), confirmed in-game.**

```
Up, Up, Up, Down, Up, Down, Up, Down, L, R      (10 presses)
mapped buffer: u u u d u d u d L R
```

This is the published 8-press `udududLR` code preceded by `uu`. The validator
uses only the last 8 characters, so it matches slot 5:
`getter(0x02008034,5) == 1` and the HUD disappeared on resume
(`Batman Begins - unpublished code effect no HUD.png`). Re-entering the
canonical 8-press code twice produced flags `00 00 00 00 00 00 00 00` and the
HUD returned (`Batman Begins - cheat re-entry toggles off.png`).

**Bounds proven by rejection.** All of the following were entered in the same
pause state; each left every flag 0 and was rejected:

| Input | Mapped suffix | Result |
|---|---|---|
| `Up Down Up Down Up Down Left Right` (D-pad, not shoulders) | `udududlr` | rejected — case/alphabet |
| `L R L R Up Up Up Down Down` (9-press published variant) | `RLRuuudd` | rejected — not in table |
| `Up` × 8 | `uuuuuuuu` | rejected |
| `Up Down Left Right B L R B` | `udlrBLRB` | rejected; buffer contains no `x` |

The four sentinel slots are **unrepresentable inputs**: the mapper’s only
outputs are `u d l r B L R` and space; there is no `x` producer anywhere in the
string→char path, and the traced buffer writer is the mapper only. This is why the
debug flags can only be reached by editing `0x02008054..0x0200805B`. The
sentinel string is shared by slots 2/4/6/7, so even if an `x` could be produced
one input would toggle four flags at once; the retail input path cannot get
there.

**State evidence (savestate parse, flags `0x02008054..0x0200805B`).**

| Test | Input | flags bytes | ring buffer |
|---|---|---|---|
| T0 | none | `00 00 00 00 00 00 00 00` | `" ---------"` |
| T1 | `udududLR` canonical | `00 00 00 00 00 01 00 00` | `" udududLR-"` |
| T2 | `LRLRuudd` canonical | `01 00 00 00 00 00 00 00` | `" LRLRuudd-"` |
| T3 | `rrrlllud` canonical | `00 00 00 01 00 00 00 00` | `" rrrlllud-"` |
| T4 | `uuddlrlr` canonical | `00 01 00 00 00 00 00 00` | `" uuddlrlr-"` |
| T5 | `uuudududLR` novel | `00 00 00 00 00 01 00 00` | `"RuuudududL"` (idx 1) |
| T6 | lowercase `udududlr` | `00 00 00 00 00 00 00 00` | `" udududlr-"` |
| T8 | 8 × Up | `00 00 00 00 00 00 00 00` | `" uuuuuuuu-"` |
| T9 | `udlrBLRB` | `00 00 00 00 00 00 00 00` | `" udlrBLRB-"` |
| T10 | canonical no-graphics × 2 | `00 00 00 00 00 00 00 00` | `"dududLRLRu"` |
| T11 | 9-press super jump | `00 00 00 00 00 00 00 00` | `" LRLRuuudd"` |

## 7. Validation evidence

**Observed**

* All four published codes enter and toggle the expected flag bytes
  (table in §6b); no Hard-Mode save is required (fresh 0 % Game 1).
* `udududLR` and the 10-press `uuudududLR` both hide the HUD; re-entry restores
  it (`Batman Begins - unpublished code effect no HUD.png`,
  `Batman Begins - cheat re-entry toggles off.png`).
* Super jump: identical input timing after the code produces a clearly higher
  jump and a different camera position
  (`Batman Begins - jump baseline.png` vs
  `Batman Begins - super jump code effect.png`).
* Super speed: identical 1.2 s hold-right moves Batman farther
  (`Batman Begins - speed baseline.png` vs
  `Batman Begins - super speed code effect.png`).
* Every reachable menu was opened: language select, logos/legal, title, main
  menu, `SELECT A GAME`, `ERASE A GAME` (including the erase-mode relabel of
  `ERASE` to `CANCEL`), credits, prologue gameplay, `PAUSE`, `QUIT LEVEL?`,
  `SLEEP NOW?`, `SOUND` volume screen. The `NEW GAME` entries are visible in
  `SELECT A GAME`; starting either leads to the same prologue. No mission,
  password, gallery or options menu exists in the reachable UI.
* Screen list matches the string bank: `START GAME`, `VIEW CREDITS`,
  `SELECT A GAME`, `ERASE A GAME`, `GAME %d - %d%%`, `NEW GAME`, `ERASE`,
  `CANCEL`, `RESUME`, `QUIT LEVEL`, `SLEEP`, `SOUND`, `MUSIC VOLUME`,
  `SFX VOLUME`.

**Derived** (instruction-level)

* Character map, ring index modulo 10, suffix comparison, and XOR toggle
  (§5.1–5.3).
* Slot-4 debug HUD: `0x0800E660` reads flag 4 and formats `0x08066B04`
  (`world:%d level:%d hard:%d flags:%x`).
* Slot-5 hides the HUD/overlay by skipping the draw call at `0x08014C6C`.
* Slot-0 doubles a jump value; slot-3 doubles a movement value.
* Slot-1 makes hit-reaction/damage paths jump to their epilogue.

**Inferred**

* Slots 6/7 forcing entity predicates true corresponds to debug “defeat/skip
  entity” behaviour; slot 2 has no reader and is unused in this build.
* The sentinel slots were probably the four debug cheats whose menu strings
  survive (`Defeat Level`, `Defeat Level 100%`, `Slow Motion`,
  `Enter Initials`) but they were not wired to the controller in the retail
  build.

## 8. Unknowns

* Exact original purpose of sentinel slots 2, 6 and 7. Slot 4 is identified by
  code and by TCRF; slot 2 has no reader; 6/7 are broad entity predicates.
* The sound cue emitted after a match was not characterised (the call site and
  buffer are recorded, but the audio was run with `SDL_AUDIODRIVER=dummy`).
* Slot 1 (no-hit) flag is verified in RAM and its reader paths are mapped, but
  the prologue thug still plays a flinch animation with the flag set; the
  unmodified hit-reaction path that remains is not fully traced.
* Progression unlocks (`HARD MODE UNLOCKED!`, `MENUS UNLOCKED!`, level select
  after 16 bat symbols) are save/progress state, not input codes; the 8-slot
  code table contains no strings for them, and none of those menus appears in
  the reachable UI.

## 9. Tooling

* mGBA 0.10.5 SDL, Xvfb :174, openbox, xdotool, scrot, ImageMagick.
* `arm-none-eabi-objdump -D -b binary -marm -M force-thumb`, Capstone 5.0.7
  for scans, `gdb-multiarch` against mGBA’s `-g` stub for RAM dumps.
* `tools/keys.py` — deterministic key injection and screenshots.
* `tools/state.py` — mGBA savestate reader: the `.ssN` file is a PNG whose
  `gbAs` chunk is zlib-compressed state; decompressed EWRAM begins at
  raw offset `0x21000` and IWRAM at `0x19000`, so EWRAM address `A` is at
  `raw[0x21000 + (A - 0x02000000)]`. This was used for every flag-byte check.
  The essential reader is:

  ```python
  import struct, zlib
  def load_state(path):
      f = open(path, "rb").read()
      pos = 8
      while pos < len(f):
          n = struct.unpack(">I", f[pos:pos+4])[0]
          typ = f[pos+4:pos+8]
          if typ == b"gbAs":
              return zlib.decompress(f[pos+8:pos+8+n])
          pos += 12 + n
  raw = load_state("Batman Begins.ss2")
  ewram = raw[0x21000:0x21000 + 0x40000]
  flags = ewram[0x8054:0x805C]      # flags[0..7] for 0x02008054..0x0200805B
  ```

  mGBA hotkeys in this build: `F1`–`F10` **load** a slot, `Shift+F1`–`Shift+F10`
  **save** it. (Mix these up and the “anchor” used for a test is overwritten;
  that happened once during this analysis and the experiment was repeated.)
* Screenshots next to the ROM:
  `Batman Begins - title.png`, `- select a game.png`, `- pause menu.png`,
  `- sound options.png`, `- credits.png`, `- jump baseline.png`,
  `- super jump code effect.png`, `- speed baseline.png`,
  `- super speed code effect.png`, `- unpublished code effect no HUD.png`,
  `- cheat re-entry toggles off.png`.

No ROM, graphics, music or game text is redistributed; only addresses,
algorithms, our own screenshots and the ROM hashes are recorded.

## 10. Legal note

Analysis performed on a locally owned ROM image. No copyrighted assets are
included in this report; the screenshots are minimal in-game captures used as
behavioural evidence.
