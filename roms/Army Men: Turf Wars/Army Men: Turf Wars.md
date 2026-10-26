# Army Men: Turf Wars (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Army Men: Turf Wars/Army Men: Turf Wars.gba` |
| Size | 8,388,608 bytes (8 MiB, 64 Mbit) |
| Header title | `A.M.TURFWARS` |
| Game code | `AY3E` (USA) |
| Maker code | `5H` |
| Software version | `0` (Rev.00) |
| Header complement (0xBD) | `0x5A` (recomputed `0x5A`) |
| Header checksum (0xBE) | `0x0000` (recomputed `0x0000`) |
| Entry word (0x00) | `0xEA1FD596` → ARM branch to `0x087F5660` (**patched**) |
| MD5 | `e4bb6e6a30395fccbbe9dc3cd40559d7` |
| SHA-1 | `fb0622cc8aa377da23d75b7ec5bbf6071f13ee7e` |
| SHA-256 | `c643344430cad802b1fa71d9aa6b855c327085c11ae47ade97062cf7a76dfbe3` |

**ROM provenance (important).** This is not a clean retail dump. The header entry
word was redirected from the normal `0xEA00002E` (`b +0xC0`) to `0xEA1FD596`
(`b 0x087F5660`). The appended block at `0x087F5660` is a scene cracktro
(“MODE7”, strings `MODE7`, `BLASTS THE OTHERS AWAY WITH:`,
`GAME SUPPLIED BY: THE CRC BANDIT`, `RELEASED ON: OCTOBER 4TH, 2002`,
`CODE & DESIGN: ♥ SEKRET ♥`). It sets up its own IRQ stack/handler, runs its
own Mode-7 show, and returns to the original game entry via the literal
`0x080000C0` at file offset `0x7F5C74`. The game body at `0x080000C0` and all
game-side addresses below are unaffected.

A second, valid GBA header exists at file offset `0x6AA80` (same title/game
code). Its entry is the normal `0xEA00002E` → `+0xC0`, and its code is an ARM
multiboot slave/receiver stub, not a second game image: it reads the GBA
serial I/O register `0x04000120` and buffers in `0x02000000`/`0x03007F00`.

Header/logo scan: the 156-byte Nintendo logo occurs exactly twice,
`0x04` (main header) and `0x6AA84` (multiboot stub header at `0x6AA80`).
No other GBA images are present; this is not a multi-game cartridge.

## 2. Executive summary

**No in-game password, button code, hidden debug menu, or unlock code is
reachable in the single-cart retail build of this ROM.** The result is a
bounded negative, not an untested gap:

1. **The password UI exists only as dead data.** The ROM contains a complete,
   coherent password-screen string set: a 21-symbol alphabet
   (`B C D F G H J K L M N P Q R S T V W X Y Z`, i.e. A–Z without the five
   vowels), `MENU`, `PW`, `Invalid password`, `Password accepted`, and a
   `PASSWORD` menu label. Every one of those strings is referenced **only by
   its own slot in the shared message-pointer table**. The table base itself
   is referenced by exactly one code site, and that site uses only IDs 0–2.
   The alphabet pointer array at `0x080680D4` is referenced by **nothing**.
2. **A menu label list for a developer menu is present but dead.** Entries
   152–162 of the message table are
   `Single player / Multi player / Password / Options / Main menu /
   Multiboot arena / Jeep Soccer / Start game / Level select /
   Choose character / Coop choose character`. IDs 152–155 name the retail
   menu items but are not drawn by the retail menu (its labels are baked into
   background art). IDs 156–162 are never indexed by code; no debug menu is
   reachable.
3. **All accessible menus were walked** (title, main, single-player,
   level-select, multiplayer, link-up, options, in-game pause, quit-confirm)
   and **23 button combinations on the title screen + 20 on the main menu +
   13 on the level-select screen** were tested with screenshot diffs. No
   hidden screen appeared; every A/Start press produced the normal next menu.
4. **The only developer-intended shortcut-like feature is Level Select**
   (`SINGLE PLAYER → LEVEL SELECT`). It draws 8 nodes; on a fresh boot only
   node 1 responds, nodes 2–8 reject input (no transition, screenshot
   evidence). This is a progress-select, not an all-levels cheat.
5. **No published password list exists.** Web sources (GameFAQs, TCRF,
   VGChartz, mirrors, Army Men wiki) publish only GameShark/CodeBreaker
   memory patches for this title; those are memory editors and are outside
   this engagement's scope. GameFAQs and TCRF returned HTTP 403 to direct
   fetches; the same pages' search snippets and the mirrored cheat pages
   (Ethereal Games, Almar's Guides, GameHacking.org, SuperCheats) were
   checked instead, and none lists a password or button code.

The password/menu strings are therefore a **cut feature**: the developer
left the UI data in the ROM, but removed or never linked the screen code.

## 3. How to reproduce

### Emulator and keymap

```bash
Xvfb :143 -screen 0 1024x768x24 &
DISPLAY=:143 openbox &
cd "roms/Army Men: Turf Wars"
DISPLAY=:143 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 "Army Men: Turf Wars.gba"
```

mGBA SDL default keymap (verified by observation):
A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`,
D-pad = arrow keys. Hold keys 150–350 ms; the menus debounce.

Window is 720×480 at `(153,164)`; crop with
`convert screen.png -crop 720x480+153+164 +repage game.png`.

### Exact menu path

1. Boot → MODE7 cracktro (`MODE7` / `THE CRC BANDIT`). Press A/Start through
   the slides; then the Möbius logo; then the title screen
   (`ARMY MEN / TURF WARS / START`).
2. Title → Start → **main menu**: `SINGLE PLAYER`, `MULTI PLAYER`, `OPTIONS`.
3. `SINGLE PLAYER` → `START GAME`, `LEVEL SELECT`, `MAIN MENU`.
   - `START GAME` starts the training level directly (no character select).
   - `LEVEL SELECT` draws nodes 1–8 in a 4×2 grid. Node 1 starts the training
     level; nodes 2–8 do not respond (locked).
4. `MULTI PLAYER` → `LINK-UP` → `MULTIBOOT ARENA`, `JEEP SOCCER`,
   `MAIN MENU`. Both game choices open the same four-slot
   `WAITING` lobby (player 1 only); without a second GBA the lobby never
   leaves the waiting state, and B/Start do not cancel it (savestate reload
   required).
5. `OPTIONS` → `BRIGHTNESS +0`, `SOUND +9`, `MUSIC +9`, `MAIN MENU`.
6. In game: Start → pause → `UNPAUSE`, `QUIT`. `QUIT` → `ARE YOU SURE?`
   `YES`/`NO`; `YES` returns to the title screen.

### Screenshots (session evidence, `/tmp/opencode/turf/`)

| File | Content |
|---|---|
| `s02.png` | MODE7 cracktro |
| `s09.png`, `s26.png` | main menu |
| `s13.png` | single-player menu |
| `s14.png`, `s31.png` | level select 1–8 |
| `ls_start1.png` | level 1 actually starts |
| `m_link_d.png` | link-up, Jeep Soccer highlighted |
| `s19.png`, `m_jeep3.png` | four-slot waiting lobby |
| `s11.png` | options |
| `s25.png` | in-game pause |
| `q2.png` | `QUIT / ARE YOU SURE? / YES / NO` |
| `q3.png` | title screen after quit |
| `btn_*.png`, `t_*.png`, `ls_*.png` | button-code scan frames |

### Published codes tested

There are no published in-game/password codes for this title. The only
published codes are GameShark/CodeBreaker memory patches (e.g. master code
`00005676 000A` / `10031296 0007`, `3300730C 0064`), which the engagement
scope explicitly excludes. No published code was executed, because executing
a memory patch would not answer the in-game-cheat question.

## 4. Address map

File offset ↔ ROM address: `rom_address = 0x08000000 + file_offset`.

| Address | Meaning |
|---|---|
| `0x087F5660` | MODE7 cracktro entry (patched header entry) |
| `0x087F5C74` | cracktro literal `0x080000C0` (return to game) |
| `0x0806AA80` | multiboot slave/receiver stub header (entry `+0xC0`) |
| `0x080000C0` | original game crt0 (ARM) |
| `0x08031248` | input poll: builds held/pressed/released |
| `0x03005FCE` | held keys (active-high, 16-bit) |
| `0x03005FD2` | newly pressed keys (active-high, 16-bit) |
| `0x03005FD0` | newly released keys (active-high, 16-bit) |
| `0x08067E48` | shared message/string pointer table (236 entries, `0x67E48–0x681F4`) |
| `0x0300794C` | RAM cell holding `0x08067E48` (written at `0x08040C14–1A`) |
| `0x08040B5C` | link-error screen; loads `[0x0300794C]`, uses IDs 0,1,2 |
| `0x08064890` | `draw_message(x, y, id, style)`: `id*4 + [0x0300794C]` |
| `0x0806489A` | the only dynamic-ID lookup: `lsls r2,#2; ldr r4,[r2,r1]` |
| `0x0806588C` | draw ASCII string (`r0` = char pointer, `r1/r2` = x/y) |
| `0x08067B28` | `"Password"` (table ID 154) |
| `0x08067CAC` | `"PASSWORD"` (ID 206) |
| `0x08067CE8` | `"PW"` (ID 210) |
| `0x08067CEC` | `"Invalid password"` (ID 211) |
| `0x08067D00` | `"Password accepted"` (ID 212) |
| `0x080680D4–0x08068124` | alphabet pointer array, IDs 163–183 |
| `0x08067BF4` | `"MENU"` (ID 184) |
| `0x08067B08` | `"Single player"` (ID 152) |
| `0x08067B3C` | `"Main menu"` (ID 156, dead) |
| `0x08067B94` | `"Coop choose character"` (ID 162, dead) |

## 5. Algorithm

### 5.1 Message/string table

The game addresses every UI/cutscene string through one 236-entry pointer
array:

```
base = *(u32*)0x0300794C          // set once to 0x08067E48 at 0x08040C1A
str  = *(u32*)(base + id*4)       // id 0..235
```

`draw_message` at `0x08064890` implements exactly this and then calls the
ASCII renderer `0x0806588C`. The mission dialogue system reads its current
message ID from a script context:

```
ctx  = *(u32*)0x03007950          // = 0x03003CD0 at the main menu
id   = *(u16*)(ctx + 0x5BC)       // written by the script VM
draw_message(x=0x78, y=0x50, id, style=1)   // 0x0806496A
```

### 5.2 Reachability of the password UI (the key result)

`0x08067E48` is referenced by exactly **one** four-byte literal in the whole
ROM (`0x40C80`, loaded at `0x08040C14`). The base is stored once
(`0x08040C1A`) and thereafter read from `0x0300794C` at exactly ten code
sites. A whole-ROM ARM-mode literal scan found no additional loads, and
ARM7TDMI has no Thumb-2, so the 16-bit Thumb scan is exhaustive. (Three of
the ten sites — the entity code at `0x080612F8`/`0x08062484`/`0x080626D8` —
use the cell as a generic pointer table with variable indices; they feed
sprite routines, not the text drawer.)

| Code site | Table ID(s) used |
|---|---|
| `0x08040B8E` | 0, 1, 2 (three-link-error message) |
| `0x08049BAA` | 228, 234 |
| `0x0804F5D4` | 192 |
| `0x08051770`, `0x08051848` | 229, 230, 231, 232, 233, 228 |
| `0x080612F8` | table value used as a pointer, not a string ID |
| `0x08062484`, `0x080626D8` | table value used as a pointer, not a string ID |
| `0x08064244` | 227 |
| `0x0806489A` | dynamic script ID (`ctx+0x5BC`) |
| `0x08064D42` | 228 |

So the complete set of string IDs reachable by constant indexing is
`{0,1,2,192,227,228,229,230,231,232,233,234}` plus script-supplied dialogue
IDs. The password region `154`, `163–183`, `184`, `210–212` and the debug
menu labels `156–162` are **never indexed**. There is no second base pointer:
the alphabet array `0x080680D4` has zero references anywhere in the ROM, and
each password string literal has exactly one reference — its own table slot.

Conclusion (derived): no code path can draw the password screen or validate a
password, because the alphabet and the screen's labels are unreachable data.
No literal or immediate encoding of the needed table offsets
(`0x268` for ID 154, `0x28C` for the alphabet base, `0x348/0x34C/0x350` for
IDs 210–212) exists anywhere in the ROM, so no code can compute those slots
either.

### 5.3 Level select

`LEVEL SELECT` is a real menu with 8 nodes. Node 1 starts the training level;
nodes 2–8 highlight on arrow input but A produces no transition (the input is
accepted by the cursor, then rejected by the unlock check). This is the only
developer-intended progression shortcut in the single-cart build, and it does
not expose later levels on a fresh boot.

## 6. Tables

### 6.1 Password/menu strings in the message table (IDs 152–235)

| ID | Address | String | Code refs |
|---:|---|---|---|
| 152 | `0x8067B08` | `Single player` | table slot only |
| 153 | `0x8067B18` | `Multi player` | table slot only |
| 154 | `0x8067B28` | `Password` | table slot only (dead) |
| 155 | `0x8067B34` | `Options` | table slot only |
| 156 | `0x8067B3C` | `Main menu` | table slot only (dead) |
| 157 | `0x8067B48` | `Multiboot arena` | table slot only (dead) |
| 158 | `0x8067B58` | `Jeep Soccer` | table slot only (dead) |
| 159 | `0x8067B64` | `Start game` | table slot only (dead) |
| 160 | `0x8067B70` | `Level select` | table slot only (dead) |
| 161 | `0x8067B80` | `Choose character` | table slot only (dead) |
| 162 | `0x8067B94` | `Coop choose character` | table slot only (dead) |
| 163–183 | `0x80680D4–0x8068124` | `B C D F G H J K L M N P Q R S T V W X Y Z` | alphabet array, 0 refs |
| 184 | `0x8067BF4` | `MENU` | table slot only (dead) |
| 185 | `0x8067BFC` | `Press A to start.` | table slot only |
| 186 | `0x8067C10` | `Load Game` | table slot only (dead) |
| 187 | `0x8067C1C` | `Version 1.0` | table slot only |
| 188 | `0x8067E20` | `         Waiting` | table slot only |
| 189 | `0x8067C28` | `multi-boot` | table slot only |
| 190 | `0x8067C34` | `Press A to accept.` | table slot only |
| 191 | `0x8067C48` | `Waiting  for  connection` | table slot only |
| 192 | `0x8067C64` | `WAITING FOR MASTER` | `0x0804F5D4` |
| 193–203 | `0x80681…` | `1`…`11` | number renderer, not IDs |
| 204 | `0x8067C9C` | `SINGLE` | table slot only (dead) |
| 205 | `0x8067CA4` | `LINK-UP` | table slot only (dead) |
| 206 | `0x8067CAC` | `PASSWORD` | table slot only (dead) |
| 207 | `0x8067CB8` | `OPTIONS` | table slot only (dead) |
| 208 | `0x8067CC0` | `Press the B button` | table slot only |
| 209 | `0x8067CD4` | `Press the A button` | table slot only |
| 210 | `0x8067CE8` | `PW` | table slot only (dead) |
| 211 | `0x8067CEC` | `Invalid password` | table slot only (dead) |
| 212 | `0x8067D00` | `Password accepted` | table slot only (dead) |
| 213–226 | `0x8067D14…` | `Start`, languages, `+`, `-`, options labels | unused by this build |
| 227 | `0x8067D88` | `Waiting for master` | `0x08064244` |
| 228 | `0x8067D9C` | `Press A button to continue` | `0x08049BAA`, `0x08051848`, `0x08064D42` |
| 229 | `0x8067DB8` | `Goals scored` | `0x08051770` |
| 230 | `0x8067DC8` | `Green team scored` | `0x08051770` |
| 231 | `0x8067DDC` | `Tan team scored` | `0x08051770` |
| 232 | `0x8067DEC` | `Green team wins!` | `0x08051770` |
| 233 | `0x8067E00` | `Tan team wins!` | `0x08051770` |
| 234 | `0x8067E10` | `Statistics` | `0x08049BAA` |
| 235 | `0x8067E1C` | `             Waiting` | table slot only |

### 6.2 Password alphabet

`B C D F G H J K L M N P Q R S T V W X Y Z` (21 symbols; vowels A,E,I,O,U
excluded). Pointer array at `0x080680D4`, stride 4, IDs 163–183. It is stored
as 21 separate single-character C strings, some aliasing the last letter of
longer strings (`C` at `0x67D64`, `D` at `0x67D5C`, `P` at `0x65ECC`).

## 6b. Enumeration

**What the password space would be.** 21 symbols ⇒ `21^L` strings for length
`L`. The ROM contains no length constant, no validator, and no generator:
`0x080680D4` has zero code references and no checksum/table code exists near
it (the neighbouring functions are link-lobby and dialogue code). The
**reachable** password space in this build is therefore **0 strings**.

**Message-ID space (fully enumerated).** 236 table entries were dumped
(`0x67E48–0x681F4`). Constant-indexed reachable IDs:
`{0,1,2,192,227,228,229,230,231,232,233,234}`. Dynamic reachable IDs: the
mission dialogue range fed by the script VM. Dead IDs: 152–191 and 193–212
(the menu/password/debug-label block). No table entry outside those ranges is
referenced by any literal pointer, any immediate index, or any data table.

**Menu space (full walk).**

| Screen | Entries observed |
|---|---|
| Title | `START` (A/Start) |
| Main | Single Player, Multi Player, Options |
| Single | Start Game, Level Select, Main Menu |
| Level Select | 1,2,3,4,5,6,7,8; only 1 accepted |
| Link-Up | Multiboot Arena, Jeep Soccer, Main Menu |
| Link lobby | player slots 1–4, `WAITING` (no cancel) |
| Options | Brightness +0, Sound +9, Music +9, Main Menu |
| Pause | Unpause, Quit |
| Quit confirm | Yes, No |
| Password/debug menus | none reachable |

**Button space (23 title-screen sequences + 20 main-menu sequences + 13
level-select sequences).** Tested: A, B, L, R, Select, Start, L+R,
L+R+Start, L+R+Select, A+B, A+B+Start, A+B+Select, Select×2,
Select+Start, Up+Down+Up+Down, L,R,L,R (×2 lengths), Konami (Up Up Down Down
Left Right Left Right B A and the reversed variant), A,B,A,B, B,A,B,A,
Select+A+B, Select+Start+A+B, arrows. **Result:** every A/Start-containing
sequence reached exactly the normal next screen (main menu / single-player
menu / level start); all other sequences left the screen unchanged apart from
background animation. No sequence produced a new screen. On the level-select
screen, B exited normally; L/R/Select/Start did nothing; A on nodes 2–8
produced **no transition** (the lock rejection).

**Novel codes / bounds.** No code can be minted because no code system is
reachable: there is no entry screen, no validator, no alphabet in code, and no
state that accepts a string. The equivalent “bounds proven by rejection” are:
(i) locked level nodes 2–8 reject selection (observed, no transition);
(ii) the password labels/alphabet cannot be reached by any input because the
only message-table base is indexed with IDs `{0,1,2,192,227–234}`;
(iii) 56 button sequences at the three likely gate screens produced no hidden
screen. This is a **proven absence for the single-cart retail build**, not a
“not tested” claim.

## 7. Validation evidence

**Observed**
- Boot shows the MODE7 / CRC Bandit cracktro, then Möbius logo, title, main
  menu (screenshots `s02`, `s09`, `q3`).
- Main menu has exactly three items; Up/Down/Left/Right wrap among them.
- Single-player menu starts the training level; Level Select shows 8 nodes;
  node 1 starts the level (`ls_start1.png`), nodes 2–8 do not.
- Multiplayer opens a four-slot `WAITING` lobby for either game choice; B and
  Start do not cancel it.
- Options pauses and Quit returns to the title screen.
- mGBA created a 512-byte `.sav`; it remained all-zero with an unchanged
  mtime through menu navigation, a level start, and Quit (no save write in
  these flows).

**Derived**
- The message table is a 236-entry `u32` pointer array; `0x0300794C` holds its
  base.
- `0x0806489A` is the only dynamic `id → string` lookup; its ID comes from
  `*(u16*)(*(u32*)0x03007950 + 0x5BC)`.
- The password alphabet and labels are dead because their pointers are
  referenced only from the table, and the table base is indexed only with the
  constant IDs listed in §6b.
- The first header is patched: entry `0xEA1FD596` → `0x087F5660`, returning
  through the literal `0x080000C0`.

**Inferred**
- The password screen was implemented and cut (strings + alphabet array +
  accepted/invalid messages all survive in one linker block).
- The all-caps `SINGLE / LINK-UP / PASSWORD / OPTIONS` menu belongs to the
  same cut/alternate UI, not to the retail menus.

## 8. Unknowns

- **Link-play payload.** The multiboot slave stub at `0x0806AA80` may receive a
  separate client program at link time. That program is not executed by a
  single-cart boot and cannot be exercised with one mGBA instance (the SDL
  frontend has no link-cable backend). No cart-side code references the
  password strings, so this does not affect the single-cart conclusion.
- **Unlock progression.** We did not complete a mission to see whether nodes
  2–8 unlock, or whether a password is ever *displayed* after a mission. No
  cart-side code can draw one, so a displayed password would have to be
  implemented by the cut code that is absent.
- **Published GameShark/CodeBreaker codes** were not executed (out of scope by
  instruction); they are memory patches, not in-game codes.
- **Unclassified hidden string.** `scabbywozhereok!` sits at `0x7E6768`, inside
  the graphics/asset bank, not in the message table and not reachable from any
  menu. It is most likely a graphics/tool signature rather than a cheat; it was
  not rendered in any walked screen.

## 9. Tooling

- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
- Python 3 + Capstone 5.0.7: literal-pool → code-site xref scan, BL-target
  scan, pointer scan, table dump, mGBA savestate (`gbAs` zlib chunk) parser.
- mGBA 0.10.5 (`/usr/games/mgba`), Xvfb `:143`, openbox, scrot, ImageMagick
  `compare`/`convert`, xdotool.
- Scripts used this session: `/tmp/opencode/turf/ui.py` (keys/screenshots),
  `state.py` (savestate decode), `btnscan.py`, `lsscan.py`, `titlescan.py`.

## 10. Legal note

No ROM, extracted graphics, audio, or text is redistributed. This report
contains only hashes, addresses, short quoted UI strings needed to identify
the dead feature, and negative results.
