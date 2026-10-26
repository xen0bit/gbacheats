# Bionicle: Matoran Adventures (GBA) — Reverse Engineering Report

Work dir for artifacts: `/tmp/opencode/bionicle` (strings dump, disassembly, screenshots).
Scope of this engagement: in-game / developer-intended cheats only (passwords,
button codes, hidden/debug menus, unlockables). No GameShark/CodeBreaker/memory
codes are proposed or evaluated.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Bionicle: Matoran Adventures/Bionicle: Matoran Adventures.gba` |
| Size | 4,194,304 bytes (4 MiB = 32 Mbit) |
| Header title (`0xA0`) | `BIONICLE MAT` (12 bytes, no NUL; full name is in the logo art) |
| Game code (`0xAC`) | `A5AE` |
| Maker code (`0xB0`) | `69` |
| Fixed byte `0xB2` | `0x96` (valid) |
| Main unit / device | `0x00` / `0x00` |
| Software version (`0xBC`) | `0` |
| Complement check (`0xBD`) | `0x9F` — **valid** (recomputed `0x9F`) |
| Header checksum (`0xBE`) | stored `0x0000`; recomputed `0x14EE` — **invalid/zeroed** |
| Entry word (`0x00`) | `0xEA0FD03E` → branch to `0x083F4100` (not the normal `0x080000C0`) |
| MD5 | `9557b6320c71fdbdee0168704e43035e` |
| SHA-1 | `8526f677accac9c42894f39e0495e3a74c54af01` |
| SHA-256 | `95397c2638055ca91fb8fba5c31230ff4c7b82e836000af226c1d2e6344bbf4d` |

**Embedded GBA-header scan.** The 156-byte Nintendo logo
(`24 ff ae 51 69 9a a2 21 …`) occurs exactly **once** in the image, at file
offset `0x4`, i.e. a single header at `0x0`. This is **not** a multi-game /
double-pack cartridge. No stub header, no `XXXX`/`VV` multiboot image.

### 1.1 Patch / trainer note (important for every address in this report)

This image is a **scene release with an injected intro**, not a clean dump:

* The cartridge entry branch at `0x00` is `EA0FD03E`, i.e. `b 0x083F4100`, not the
  stock `b 0x080000C0`. `0x083F4100` is at the very end of the image and contains a
  small ARM bootstrap (`mov r0,#0x12; msr cpsr; …; ldr sp,=0x03007FA0; …;
  str 0x083FF7CD, [0x03007FFC]; bx 0x083FF7CD`) that installs its IRQ vector and
  jumps into Thumb code at `0x083FF7CD`.
* The intro draws: `MODE7 proudly presents:` / `Lego Bionicle Matoran Adv` /
  `50 MByte <- 100 Version` / `(c) Argonaut`, then a second scroll
  `Game supplied by: Nick Burns (GBB)` / `Released on: Oct 6th, 2002`,
  then `- Mode Seven -` / `Powered by Whatever We Feel Like!`.
* Strings: `MODE7` `0x3F41B8`, `Nick Burns` `0x3F431D`, `Argonaut` `0x3F424E`.
* Region `0x3F4000`–`0x3FFFFF` is the injected block; everything below
  `0x3F4000` is the original game (the stock crt0 is still intact at `0x080000C0`:
  `mov r0,#0x12; msr cpsr_c, r0; …`).
* The header checksum word `0xBE` is zeroed. This is also true of other ROMs in
  this collection (`Lego Bionicle`, `Lego Racers 2`), so it is a collection-wide
  pre-processing artifact rather than this game's patch; the complement check is
  still valid, so `0xA0..0xBC` is untouched.
* **No trainer, no cheat patch, no modified game code was found.** All game
  addresses below are original Argonaut code/data. Treat the 4 MiB image as the
  retail build plus an appended intro.

---

## 2. Executive summary

**Answer: the shipped build contains no reachable passcode / button-code / debug
menu. The one passcode string that exists is the residue of a cut feature.**

Evidence, in one paragraph: the English UI text table contains exactly one
`ENTER PASSCODE` string (file `0x1864C0`, table entry `0x185280`, index 18) and
one `UNLOCKED!` (`0x186770`). That pair of table slots (17 = `RESUME GAME`,
18 = `ENTER PASSCODE`) is filled with the literal placeholder `TEMP` in **all
seven** other language blocks (German, French, Spanish, Italian, Dutch, Danish,
Swedish). It is the only `PASSCODE` in the whole 4 MiB image (`PASSWORD`, `CHEAT`,
`DEBUG`, `SECRET`, `LEVEL SELECT` all return zero hits). No code path loads that
table slot: every one of the 23 literal-pool occurrences of the table base
`0x08185238` was disassembled and none forms an index-18 access. Every menu in
the game was walked in the emulator (boot → language → logos → title → main →
options → difficulty → slot select → overwrite dialog → character select →
level → pause → exit confirm → save) and no passcode screen is reachable. No
published passcode list exists for this title (GameFAQs' only cheat entry is a
throw-item glitch; the rest of the web offers CodeBreaker device codes, which are
out of scope).

What the ROM *does* implement is a six-character unlock system (Kongu is
available from the start, the other five Matoran are `????` until their mask
pieces are collected) and a 4-slot SRAM save (four 128-byte records in a 512-byte
`.sav`). The passcode screen appears to have been designed as the "enter a code
to unlock a Matoran" counterpart of that screen and then abandoned.

Because no entry surface exists in the shipped build, there is no code space to
enumerate and no input that can be accepted or rejected. Section 6b therefore
quantifies the hypothetical space (6⁵ = 7,776), states the implemented space (0),
and lists the searches that bound the negative — including the literal
`TEMP`-placeholder proof, which is stronger than an xref argument.

---

## 3. How to reproduce

### 3.1 Environment

```bash
Xvfb :184 -screen 0 1024x768x24 &
DISPLAY=:184 openbox &
cd "roms/Bionicle: Matoran Adventures"
DISPLAY=:184 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 "Bionicle: Matoran Adventures.gba" &
```

mGBA 0.10.5 (Debian `mgba-sdl`, binary at `/usr/games/mgba`). Window is
720×480 at `+154+184`; screenshots with `scrot` then
`convert -crop 720x480+154+184 +repage`.

Default mGBA SDL keymap used throughout: **A = `x`, B = `z`, L = `a`, R = `s`,
Start = `Return`, Select = `BackSpace`, D-pad = arrows.** Keys were held
150–350 ms; the menus sample input per frame and a 10 ms tap is missed.

> Operational note that cost time: after several emulator restarts the X server
> kept a stale mGBA window id, and `xdotool key` went to the dead window while
> `scrot` still captured the live one. Always re-run
> `xdotool search --name mGBA` before a key burst, and prefer one emulator
> instance per display.

### 3.2 Exact menu path (every screen in the game)

| # | Screen | Path / input | Screenshot |
|---|---|---|---|
| 1 | Mode7 intro | automatic, ~35 s, Start skips | `00_boot.png`, `03_screen.png`, `110` |
| 2 | Supplier splash | after intro | `01_title.png` ("Game supplied by Nick Burns (GBB)" / "Oct 6th, 2002") |
| 3 | Language select | A on `ENGLISH` | `07.png` (8 languages) |
| 4 | LEGO / EA / Nintendo legal | automatic | `08.png` |
| 5 | TURAGA splash | automatic | `10.png` |
| 6 | Title — `PRESS START` | Start | `13.png` |
| 7 | **Main menu** `NEW GAME / RESUME GAME / OPTIONS` | Start | `14.png`, `100.png` |
| 8 | Options `DIFFICULTY / SOUND FX / MUSIC` | main → `OPTIONS` | `15.png`, `17.png` |
| 9 | Difficulty `EASY / MEDIUM / HARD` | options → `DIFFICULTY` | `17_options3.png` |
| 10 | **SELECT SLOT** (`1.<name>` / `2.NEW GAME`) | main → `NEW GAME` or `RESUME GAME` | `28.png`, `102.png`, `230.png` |
| 10b | Resume loads straight into Le-Wahi | main → `RESUME GAME` → slot 1 | `304.png`, `306.png` |
| 11 | `OVERWRITE GAME ? YES / NO` | select an occupied slot | `144.png`, `183.png` |
| 12 | **Character select** (KONGU + five `????`) | new slot, or `NO`→main, or `YES`→save | `30.png`, `105.png`, `180.png`, `251_2.png` |
| 13 | Level intro `SEEK YOUR COMPANION! / LE WAHI` | A on character | `31.png`, `194.png` |
| 14 | Gameplay (Le-Wahi) | — | `150.png`, `151.png`, `195.png` (companion found) |
| 15 | `GAME PAUSED / CONTINUE / EXIT GAME` | Start in level | `32_pause.png`, `196.png` |
| 16 | `EXIT GAME ? YES / NO` | pause → `EXIT GAME` | `41_confirm.png`, `46.png` |
| 17 | `GAME SAVED!` | A on character select | `109.png`, `260_1.png` |
| 18 | Pause after **resume** (same two items) | Start in level | `307.png` |

Both the `NEW GAME` and `RESUME GAME` branches were walked: resume loads the
saved Le-Wahi state immediately and its pause menu is identical to the
new-game one, so the 17/18 string pair is not reached from either.

No other screen exists behind Start/Select/L/R or any combination tested
(see §6b for the combination list). `MAIN → OPTIONS` is the only branch off the
main menu; the character select is the only branch after slot selection; the
in-level pause has exactly two items.

### 3.3 Testing setup that made the walk reproducible

* Two save slots are enough: one occupied by KONGU, one for a disposable game.
  A save is created by pressing A on the character-select screen (`GAME SAVED!`),
  and the `.sav` appears next to the ROM.
* On a slot that already contains a game the game inserts the
  `OVERWRITE GAME ?` dialog; `YES` re-saves and goes to the character select.
* All screenshots referenced above are in `/tmp/opencode/bionicle/shots/`.

---

## 4. Address map

File offset → ROM address is `0x08000000 + offset` throughout.

| Address / offset | Kind | Meaning |
|---|---|---|
| `0x08185238` (file `0x185238`) | table | UI string-pointer table, English block (43 × u32, ends `0x1852E0`) |
| `0x1852E4` | table | language-name table (`ENGLISH…SWEDISH`, 9 entries, then `????`, save/slot messages) |
| `0x185380` / `0x1854C8` / `0x185610` / … | table | per-language blocks, **stride `0x148` (328 bytes = 82 pointers)**; German base `0x185380`, French `0x1854C8`, Spanish `0x185610`, see §6 |
| `0x08186410`–`0x08186Axx` | data | English strings (`NEW GAME` … `CONTROLS B`, then `GAME PAUSED` … `EXIT GAME`) |
| `0x081864C0` | data | **`ENTER PASSCODE`** (table index 18) — the only occurrence in the ROM |
| `0x08186770` | data | `UNLOCKED!` |
| `0x081863C4` | data | `ENGLISH` (first language name) |
| `0x08185DB2` | data | 6-byte symbol permutation `00 02 04 01 03 05` (character-select alphabet) |
| `0x08185DB8` | data | second permutation `02 04 00 01 03 05` |
| `0x08163C74` | **ARM code** | character-select input/update handler (6-slot selector) |
| `0x08163E80` | ARM code | character-select drawing of the six masks |
| `0x08164E00` | ARM code | screen chooser: if `[0x03003218]!=0` → `0x08163C74`, else `0x081636E8` |
| `0x08164E68` | ARM code | character-select/slot init (clears unlock flags, loads gfx) |
| `0x08164B78` | ARM code | generic 2-item YES/NO dialog input handler |
| `0x08164A44`, `0x08164570` | ARM code | menu drawing helpers (text table at `0x08185238`, language stride `0x148`) |
| `0x0814D11C` | ARM code | save/load screen handler (`SAVING DATA`, `SELECT SLOT`, `OVERWRITE`) |
| `0x0815550C` | ARM code | sprite/OAM queue helper (used for every menu icon) |
| `0x081659D8` | ARM code | text draw helper (x, y, string pointer) |
| `0x03001878` | IWRAM | 6-byte "character available" flags (indexed 0..5) |
| `0x03001950` | IWRAM | selected character index (0..5) |
| `0x03001960` | IWRAM | 6-slot staging copy (u16 stride; the save path copies 6 bytes from it) |
| `0x03001EE0` | IWRAM | key-state mirror (active-high) |
| `0x030017B0` | IWRAM | pressed-this-frame key mask |
| `0x030031AC` | IWRAM | **current screen handler pointer** |
| `0x030031A8` | IWRAM | next-screen pointer for the 2-item dialog |
| `0x03003218` | IWRAM | screen selector flag used by `0x08164E00` |
| `0x03002C34` | IWRAM | packed 6-byte character/slot record (`+0..+5`) |
| `0x03002C40` | IWRAM | save/progress record (fields at `+0xC,+0xE,+0x10,+0x12,+0x14`) |
| `0xE000000` region | SRAM | `.sav`, 512 bytes = 4 slots × 128 bytes |

`0x030031AC` is the useful hook: every screen is a function pointer stored here
and re-read by the main loop, so a screen transition is a write to this word
(e.g. `0x08164E00` writes `0x08163C74` or `0x081636E8`; `0x081652C8` writes
`0x08163C74`).

---

## 5. Algorithm

### 5.1 Character-select / unlock state machine (derived)

```
selected = [0x03001950]          ; 0..5
keys     = [0x03001EE0]
if keys & 0x60:                  ; Up|Left
    selected = (selected + 5) % 6
if keys & 0x90:                  ; Right|Down
    selected = (selected + 1) % 6
symbol = perm6[selected]         ; perm6 = {0,2,4,1,3,5} at 0x08185DB2
while available[symbol] == 0:    ; 0x03001878[symbol]
    advance selected until an available slot is found
if A or Start pressed:
    pack six bytes of 0x03002C34 = available[]
    advance to level / save
```

`available[]` is the "which Matoran are unlocked" array: Kongu's byte is non-zero
in a fresh save, the other five are zero, which is exactly why the cursor will
not leave `KONGU` and why the five rows render as `????`
(string index 54, `0x08186460`).

### 5.2 Save format (derived, partial)

`.sav` is 512 bytes = 4 slots of 128 bytes. Used part of each slot is the first
`0x18` bytes; the rest is `0xFF` padding. Observed records (offsets within slot):

```
+0x00..06 : 00 00 00 00 00 00 00
+0x07     : 03        ; level/difficulty-ish
+0x08..0A : 00 02 00
+0x0B     : 03
+0x0C..0F : 00 00 00 00
+0x10     : 0E/0D/01 ; depends on slot
+0x11..17 : 00 01 00 01 00 00
+0x18..7F : FF …
```

The differing byte at `+0x10` (`0x0E`, `0x0D`, `0x01` in slots 0–2) is a
progress/counter field. No ASCII, no passcode field, and no checksum byte was
found in the record; the game re-saves the whole slot at `GAME SAVED!`.

### 5.3 The passcode machinery that is *not* there

There is **no** encoder/decoder pair, no 5-symbol input buffer, and no
comparison table for a passcode:

* The only multi-byte copy in the save path is
  `for i in 0..5: buf2[i] = buf1[2*i]` at `0x0814D2C0`, copying the six
  character-availability bytes — not a code.
* `0x03003218` is not a passcode flag: only two instructions ever write it
  (`strb r1,[r2]` at `0x08164118` with `r1 = 2 - dialog_sel`, and `strb r0,[r2]`
  at `0x08164158` with `r0 = 0`), i.e. it is the yes/no-dialog result reused by
  the screen chooser at `0x08164E00`.
* No code indexes the string table at `+0x48` (index 18). See §6b.

---

## 6. Tables

### 6.1 English UI string table (base `0x08185238`, 43 entries)

```
 0 0x08186410 NEW GAME          11 0x0818647C DIFFICULTY      22 0x08186550 MUAKA
 1 0x0818641C OPTIONS           12 0x08186488 CONTROLS        23 0x08186558 TA WAHI
 2 0x08186424 RESUME GAME       13 0x08186494 CREDITS         24 0x08186560 KO WAHI
 3 0x08186430 JALA              14 0x0818649C EASY            25 0x08186568 PO WAHI
 4 0x08186438 MATORO            15 0x081864A4 MEDIUM          26 0x08186570 RAHI
 5 0x08186440 KONGU             16 0x081864AC HARD            27 0x08186578 GA WAHI
 6 0x08186448 MAKU              17 0x081864B4 RESUME GAME     28 0x08186580 ONU WAHI
 7 0x08186450 HUKI              18 0x081864C0 ENTER PASSCODE  29 0x0818658C BARAG
 8 0x08186458 ONEPU             19 0x081864D0 LEVEL COMPLETE  30 0x08186594 THE END
 9 0x08186468 MUSIC             20 0x081864E0 COMPLETE        31 0x0818659C SEEK YOUR
10 0x08186470 SOUND FX          21 0x08186548 LE WAHI         32 0x081865B4 FACE & DEFEAT
                                                                … 40 CONGRATULATIONS
                                                                41 CONTROLS A  42 CONTROLS B
```

Indices 0–2 are the main menu; 3–8 the Matoran; 9–16 options; **17/18 the
unimplemented two-item menu (RESUME / ENTER PASSCODE)**; 19–20 level-complete
labels; 21–30 level names; 31–40 objective banners.

### 6.2 The smoking gun: indices 17/18 are `TEMP` outside English

Each language block has the same 43 slots. English-only content:

| idx | English | German (base `0x185380`) | French (`0x1854C8`) | Spanish (`0x185610`) |
|---:|---|---|---|---|
| 17 | `RESUME GAME` | `TEMP` | `TEMP` | `TEMP` |
| 18 | `ENTER PASSCODE` | `TEMP` | `TEMP` | `TEMP` |

Italian/Dutch/Danish/Swedish show the same `TEMP` pair (all four point at the
shared `TEMP` strings `0x08186838`/`0x08186840`). A live menu label would never
ship as `TEMP` in 7 of 8 languages, and the English string has no
localisation counterpart at all: `strings` finds **one** `PASSCODE` in the
whole ROM.

### 6.3 Six-symbol alphabet (character-select icons)

```
perm6 @ file 0x185DB2 : 00 02 04 01 03 05      ; display order -> symbol id
perm6b @ file 0x185DB8: 02 04 00 01 03 05
```
The six ids index the character table (JALA, MATORO, KONGU, MAKU, HUKI, ONEPU)
and the six mask graphics drawn by `0x08163E80` at the hexagon positions
`(0x30,4) (0x3E,25) (0x58,50) (0x30,79) (0x3E,105) (0x58,124)`.

### 6.4 What a passcode *would* have looked like

If the cut screen had shipped, the natural format is 5 symbols over this
6-symbol alphabet (the input handler steps a 0..5 index and the mask row is the
only 6-way selector in the game), i.e. 6⁵ = 7,776 combinations. This is an
inference from the design, not a decoded format: there is no evidence of a
checksum and **no table of valid codes exists in the ROM**, so it cannot be
turned into a usable system. It is recorded here only so a future analyst does
not have to re-derive the reasoning.

---

## 6b. Enumeration

### Space definition

| Property | Value |
|---|---|
| Implemented code space in this build | **0 codes** (no entry screen, no validator, no table) |
| Hypothetical intended space | alphabet 6 symbols × 5 positions = **7,776** |
| Stored code table | none found (see searches) |
| Reserved/checksum bits | none found |
| Entry surface | none reachable (see below) |

### Published codes (checked before reversing)

* GameFAQs cheats page for this title: **1 entry**, a throw-item glitch
  (`roms`-external; archived copy fetched via `web.archive.org` because direct
  fetch returns 403). No passcodes.
* GameFAQs FAQ index: **0 guides/FAQs** (archived capture 2023-12-24).
* `supercheats`, `almarsguides`, `gamehacking.org`, `cheathappens`: only
  GameShark/CodeBreaker/Action Replay device codes
  (`[M] 9B7728C26615`, `C6D2131136F1`, `E6D613132571`, `A6D61253A561`,
  `683758B6E396`, `0559BB7D308D`) — out of scope by the engagement rules and
  **not** in-game codes.
* `cheatcc`, IGN wiki, LEGO Games Wiki, Wikipedia, TCRF: no passcodes, no
  hidden-menu documentation for this title. (TCRF's `L,L,R,L,Select,Start,A`
  cheat menu belongs to the *other* GBA Bionicle game, not this one.)
* Result: **there is no published list to reproduce**, which is consistent with
  the cut-feature finding.

### Negative proof — what was actually searched and how

1. **String space.** `strings -t x -n 3` → 63,357 lines. Keyword counts:
   `PASSWORD` 0, `PASSCODE` **1** (`0x1864C0`), `CHEAT` 0, `DEBUG` 0,
   `SECRET` 0, `LEVEL SELECT` 0, `CODE` 1 (inside the same PASSCODE string),
   `UNLOCK` 1 (`UNLOCKED!` 0x186770). The German/Italian unlock strings
   (`FREIGESCH.!` `0x186B8C`, `SBLOCCATO!` `0x18777C`) show the *unlock* message
   was localised; the *passcode* label was not.
2. **Literal / pointer space.** The table entry for `ENTER PASSCODE`
   (`0x185280`) is referenced only by the table itself. The table base
   `0x08185238` occurs 23 times, all as literal-pool words. Each pool was
   disassembled ±0x400 with `objdump -M force-arm`; **none** contains an index-18
   access (`mov rX,#72`, `add rX,rY,#72`, or `ldr rX,[rY,#0x48]` as a table
   index). The only `#72` immediates are screen coordinates in the save/options
   drawers.
3. **Button-code space.** Searched the raw image for key-mask arrays:
   `L,L,R,L` as u16 (`00 02 00 02 00 01 00 02`) and as one byte per press
   (`00 00 01 00`), `Select,Start,A` (`04 00 08 00 01 00`), and
   `Up,Up,Down,Down,Left,Right,Left,Right`
   (`40 00 40 00 80 00 80 00 20 00 10 00 20 00 10 00`). **Zero hits.**
4. **Menu space.** 18 distinct screens/states walked (§3.2). No screen with a
   five-symbol row, no "ENTER PASSCODE" label, no sixth menu item on the main
   menu (three items), slot screen (two items), options (three), pause (two),
   or character select (six characters, five locked).
5. **Button space on every menu.** At the main menu and the character select,
   the following were pressed with a screenshot after each: `Select`,
   `L`, `R`, `L+R`, `L+R+Select`, `Select+Down`, `A+L+R`, `A+L+R+Start`,
   `Start+Select`, `BackSpace+A`, and the sequence
   `L,L,R,L,Select,Start,A`. None produced a screen change beyond the normal
   menu transitions (highlight blink, `GAME SAVED!`, level start).
6. **RAM/state space.** The dynamic hook `[0x030031AC]` (current screen
   handler) and `[0x03003218]` (dialog result used by the chooser at
   `0x08164E00`) were instrumented under the mGBA GDB stub. In a normal
   play-through `0x03003218` only ever takes the values written by the YES/NO
   dialog (`2 - sel`, then `0`), never a passcode-enable state; no write comes
   from any other site (only two writers exist, `0x08164118` and `0x08164158`).

### Bounds / rejection

Bounds testing by rejected input requires an input surface. In this build no
surface accepts a code, so a rejection cannot be recorded; the equivalent bound
is §6b(1)–(6): the feature has **no screen, no table, no reader and no localised
label**, and 7 of 8 language blocks ship the literal `TEMP` placeholder for the
two slots that would have hosted it. That is a stronger statement than "the game
rejected code X": it means no representable value in the hypothetical 6⁵ space
can be accepted, accepted *or* rejected, because the parser was never linked to
a screen.

### Codes

**None minted.** No in-game code exists in this build, so there is no novel code
to generate, no effect to screenshot, and no acceptance to prove. This is
reported as a bounded negative rather than an untested area: the searches above
cover the full 4 MiB string space, every literal reference to the text table,
four common button-code encodings, all 18 screens/states, and the relevant RAM
state variables.

---

## 7. Validation evidence

**Observed (emulator / screenshot):**
* The complete menu tree of §3.2 and its behaviour; `GAME SAVED!` on character
  select; `OVERWRITE GAME ?` on an occupied slot; `GAME PAUSED` with exactly
  `CONTINUE`/`EXIT GAME`; character select showing `KONGU` plus five `????`;
  pressing Down/Up does not move off Kongu; A starts Le-Wahi.
* `.sav` = 512 bytes, four 128-byte records, `0xFF`-padded, created on
  `GAME SAVED!`.
* Injected Mode7 intro text and the redirect of the entry branch.

**Derived (instructions/data):**
* `0x08185238` is the English UI table; stride `0x148` per language; the
  `ENTER PASSCODE` entry is index 18 and exists only once in the image.
* All seven other language blocks put `TEMP`/`TEMP` in slots 17/18.
* `0x08163C74` + `0x08163E80` implement the six-character selector, using the
  permutation `00 02 04 01 03 05` and the availability array `0x03001878`.
* The chooser `0x08164E00` selects between `0x08163C74` and `0x081636E8` from
  `0x03003218`, which is only ever written by the generic YES/NO dialog.
* No literal-pool for the text table contains an index-18 access.
* Header entry word redirects to `0x083F4100`; the stock crt0 at `0x080000C0`
  is intact.

**Inferred:**
* The pair `RESUME GAME` / `ENTER PASSCODE` (indices 17/18) was intended as a
  two-item pause/file menu for a passcode feature, localisation of which was
  never done for 7 languages and whose screen code was removed before shipping.
* The intended format was most likely 5 symbols over the 6-character alphabet
  (6⁵ = 7,776), because the only multi-slot buffer in the code is six bytes and
  the input handler steps a 0..5 index. No checksum is evidenced.

---

## 8. Unknowns

* Whether a *different* retail revision/region (this is `A5AE`, Rev 00, the
  USA/Europe 8-language build) shipped the passcode screen. Only this image was
  analysed; the `TEMP` placeholders suggest the feature was dropped across the
  whole localisation set, not just this region.
* What the intended effect of a correct code would have been (unlock a Matoran
  is the natural reading of `UNLOCKED!`, but there is no code to prove it).
* The exact semantics of the save field at slot `+0x10` and the three-byte
  sequence at `+0x08..0x0A`; only the differing values are reported.
* Whether the scene-release intro replaced any original bytes below `0x3F4000`.
  Only the entry word and the header checksum word are demonstrably modified;
  the rest of the game code looks self-consistent, but a clean-dump diff would
  settle it.
* The role of the `0x03003218 → 0x08164E00` chooser pair. It is demonstrably the
  yes/no-dialog result path, but the two screens it chooses between (character
  select vs. `0x081636E8`) were not both exercised; the second function appears
  to be an alternate character/slot view. Reported as unresolved rather than
  guessed.

---

## 9. Tooling

All artifacts in `/tmp/opencode/bionicle`:

| Path | Purpose |
|---|---|
| `strings.txt` | `strings -t x -n 3` of the ROM (63,357 lines) |
| `arm_code.txt` | `objdump -D -b binary -marm -M force-arm 0x08000200..0x08200000` |
| `tools/ctl.py` | xdotool key/screenshot helper (focus, hold 180 ms) |
| `tools/sel.py` | menu-highlight detector (orange-band scan over 4 frames) |
| `tools/scan.py`, `tools/scan2.py`, `tools/xref.py` | Thumb/ARM literal-pool and xref scanners |
| `tools/ptrscan.py` | 32-bit pointer scanner |
| `gdb_*.cmd`, `gdb_*.log` | mGBA `-g` GDB-stub sessions used to read/instrument `0x030031AC`, `0x03003218` |
| `shots/` | 100+ screenshots; the ones cited in §3.2 are the evidence set |

Environment: Debian, `mgba-sdl 0.10.5` (`/usr/games/mgba`), `binutils-arm-none-eabi`,
`Xvfb`, `openbox`, `xdotool`, `scrot`, ImageMagick, `gdb-multiarch 16.3`,
Python 3 + Pillow, Capstone 5.0.7.

Reproduction shortcut: the whole negative result can be re-verified without the
emulator from `xxd`/`strings` plus the two table dumps in §6.1–6.2; the emulator
walk in §3.2 is what proves there is no hidden screen.

---

## 10. Legal note

No ROM, graphics, music or extracted text is redistributed with this report.
All quoted strings are short UI labels required to identify the feature. The
ROM itself is not part of the repository (`.gba` is git-ignored); only this
report is.
