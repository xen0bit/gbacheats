# ChuChu Rocket! (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/ChuChu Rocket!/ChuChu Rocket!.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `CHUCHUROCKET` (space-padded) |
| Game code | `ACRE` |
| Maker code | `6W` |
| Software version | 0 |
| Entry word | `0xEA00002E` → `0x080000C0` (stock GBA branch) |
| Complement byte | `0x21` (`-(sum(0xA0..0xBC)+0x19) & 0xFF`) |
| Header checksum field | `0x0000` (zeroed; rebuilt-header artifact, see §16.1) |
| MD5 | `76bd3ac13808b1d6abea377815b10adb` |
| SHA-1 | `f204105308b7758df84f1a31919204459ea6e54f` |
| SHA-256 | `41a7fafd0ab67e28f822d2d8761a6155d7f53f6084a86617b46146ce6d555a8c` |

**Embedded-header scan.** The 156-byte Nintendo logo occurs twice: at file `0x4`
(header 0) and at file `0x3C8004` (header base `0x3C8000`). Both headers have the
same title, code, maker, complement and zero checksum. The second is a
**multiboot/link-cable image** of the same game, 0x38000 bytes, based at
`0x083C8000`; it is not a second title and adds no separate menu content. No
trainer, cracktro, or appended menu was found: the first 4 KiB decompile to a
normal crt0/IRQ setup, the entry branch is stock, and there is no non-game code
before the Nintendo logo.

**Text encoding note.** The ROM contains **no ASCII UI string bank**. The only
readable ASCII runs are the header and the words `CHUCHU`/`ROCKET` inside
compressed/art data. Every in-game label is pre-rendered 4bpp/8bpp tile art
(see §4). This is the single most important fact for the cheat question: there
is no text table in which a password could live.

## 2. Executive summary

* **There is no typed password / cheat-code system in this SKU.** There is no
  alphabet, no entry screen, no string validator, and no ASCII text bank. The
  only text the ROM contains is the 12-byte header title. A word/encoding scan
  of all 4 MiB (`PASSWORD`, `CHEAT`, `CODE`, `DEBUG`, `SECRET`, `UNLOCK`,
  `EDITOR`, `GALLERY`, `STAFF`, `SOUND`, `OPTION`, `EXTRA`, `BONUS`, `HIDDEN`,
  `JBA`, …) returns **zero** ASCII hits and only coincidental compressed-data
  hits under UTF-16 (see §6).
* **The title screen accepts exactly one button: Start.** Its input code
  (`0x0800C7D4`) tests `pressed & 0x08` only; there is no key history,
  sequence counter, or expected-button table anywhere in the title/menu image
  region (`0x0800B000–0x0800E000` contains **0** mask sequences of length ≥ 4).
* **The main menu is a fully enumerated 9-item grid (0..8).** Index RAM is
  `0x03002EE8`; the dispatch table is at `0x0800CB40`; the bound is `cmp r0,#8`
  at `0x0800CB1E`. All nine items were entered on the real screen and their
  destination scenes captured (§6b).
* **The Help/"Homepage" screen is a 6-entry hub (0..5)** with five content
  pages plus a return entry. All six were entered and captured. The fourth
  content page is the "download" page whose selection index is RAM `0x030033A8`
  and whose confirm byte is `0x03003D80` (observed 1→4).
* **Published GBA "cheats" are unlock conditions, not codes.** GameFAQs lists
  only: Hard/Special/Mania puzzle modes (progress), the Help-page reveals with
  three alternate skin sets, and holding B to speed the credits. None of these
  is a literal that can be searched or entered.
* The frequently-copied "JBA laboratory / secret body title-screen codes" list
  does **not** verify against this image: there is no `JBA` string in any
  encoding (the only `JBA` bytes are inside compressed art at `0x0804E69F`), no
  lab menu item among the nine, and no title-screen sequence matcher. It is
  recorded as unverified/misattributed, not as a rejected code.
* Therefore the deliverable is a **bounded negative**: code space = 0; the
  enumerable space is the menu/help/button surface, fully walked and bounded
  (§6b).

## 3. How to reproduce

Emulator: mGBA 0.10.5 (`/usr/games/mgba`), SDL frontend, 3× scale, under
`Xvfb :245 -screen 0 1024x768x24` with `openbox` and `SDL_AUDIODRIVER=dummy`.
Default keymap used: **A = `x`, B = `z`, Start = `Return`, Select = `BackSpace`,
D-pad = arrows, L = `a`, R = `s`**. Hold keys 120–250 ms; a 50 ms tap is
sometimes dropped by the menu's release-edge handler.

Boot path to the target screens:

1. Launch the ROM; wait ~12 s (Sega/logo/attract). Title scene is
   `0x0800C774`, DISPCNT `0x1340` (BG0+BG1, 8bpp, 600/569 tiles).
2. Press **Start** → scene `0x0800CD98` → main menu scene `0x0800CABC`,
   DISPCNT `0x0140` (BG0 8bpp, 599 tiles), 9 items.
3. D-pad moves index `0x03002EE8`: Down `+1`, Up `-1`, both wrapping 0↔8;
   Left/Right jump by 4 in the 4+4+1 layout. **A or Start** dispatches item.
4. Item 8 opens the Help hub `0x08016AC4` (DISPCNT `0x1140`, 8bpp BG0 599
   tiles, 30×20 text window). D-pad changes Help index `0x030033AC` 0..5;
   A opens a page; B returns.

Save states used: `Shift+F1..F9` save, `F1..F9` load. States were decoded
offline (PNG `gbAs` zlib chunk → 397,312-byte raw state; IO at `0x400`,
palette `0x800`, OAM `0xC00`, VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000`;
layout per mGBA 0.10.5 `serialize.h`). No screenshots were used; all screen
evidence below is VRAM/OAM/RAM reads and static bytes.

## 4. Address map

### 4.1 Core engine

| Address | Meaning |
|---|---|
| `0x080006B8` | main loop: `bl 0x08025C74` (frame wait), `ldr r0,[0x030016D8]`, `bl 0x08026DA4`, `bl 0x08000808`, loop |
| `0x080006E0` | **scene setter**: `str r0,[0x030016A0]` |
| `0x030016A0` | current scene/update function pointer (Thumb, low bit set) |
| `0x08000808` | key update: reads `0x04000130`, builds held/pressed/released in `0x03001710` |
| `0x03001710` | input struct: `+0` held (active high), `+2` complement, `+4` pressed edge, `+6` released edge, `+8` repeat timer |
| `0x08001AB8` | shared menu/name-entry key worker (A/Start, Up/Down/Left) |
| `0x08024930` | play sound effect (r0 = ID) |

There are **211** `bl 0x080006E0` call sites and **104 distinct scene entry
callbacks** in the ROM (scan by Thumb `BL` target + preceding `ldr r0,=…`).
This is the complete scene vocabulary used by this image.

### 4.2 Title and main menu

| Address | Meaning |
|---|---|
| `0x0800C774` | title scene |
| `0x0800C7D4` | title input: `ldrh [0x03001710+4]`; `ands #8` (Start only) |
| `0x0800C7E4` | on Start: `[0x03002EE8]=1`, scene `0x0800CD98` |
| `0x0800CD98` | transition wrapper → `0x0800CABC` |
| `0x0800CABC` | **main menu** scene |
| `0x03002EE8` | main-menu selection index, 0..8 |
| `0x0800CB40` | 9×u32 dispatch table (`0x0800CB64 … 0x0800CC88`) |
| `0x0800CB1A`–`0x0800CB2C` | bounds `cmp r0,#8; bls` + `mov pc,r0` |
| `0x0800CC94` | D-pad navigation (released-edge masks: 0x40 Up, 0x80 Down, 0x20 Left, 0x10 Right) |
| `0x0800CB64`… | item handlers (see §6) |

The nine handlers set mode flags then enter a wrapper scene; the wrapper
initialises assets and sets the next scene. Observed destination scenes are in
§6b.

### 4.3 Help / Homepage

| Address | Meaning |
|---|---|
| `0x08016AC4` | Help hub scene (6-entry table) |
| `0x030033AC` | Help selection index 0..5 |
| `0x08016B30` | 6×u32 page table |
| `0x08017074` | hub navigation (Up/Down wrap 0↔5; B/Right exit) |
| `0x0801713C` | Help entry/wrapper (clears `0x03003D80`, draws homepage frame, sets `0x08016AC4`) |
| `0x08017244` | homepage frame drawing (alternate layout when `0x03003D80≠0`) |
| `0x08018520` | page 4, "download" page; index `0x030033A8`, confirm `0x03003D80` |
| `0x080172FC` | page 0 scene |
| `0x08017768` | page 1 scene |
| `0x08017B88` | page 2 scene |
| `0x08017EB8` | page 3 scene |
| `0x08018520` | page 4 scene |

### 4.4 Save memory

The cart uses **64 KiB SRAM**. mGBA's `.sav` contains two mirrored 32 KiB
banks: magic `"Waka"` at `0x0000` and `0x8000`; the live record is at
`0x0D14`–`0x0FDB` (first bytes `00 01 02 02 00 00 00 01 …`); checksum/pattern
area at `0x0FDC`–`0x0FFF` (`AB 35 F3 C2` + repeated `0A 67 54 F1`). The
`"Waka"` magic and the mirror are observed; the exact field semantics of the
0x2C8-byte record were not needed for this question.

## 5. Algorithm (menu dispatch)

```
; main menu, scene 0x0800CABC
if (pressed & (A|Start)) {                 ; 0x0800CAE8
    snd(5)
    idx = u8[0x03002EE8]
    if (idx > 8) goto default
    handler[idx]()                          ; table 0x0800CB40
}
else {                                      ; 0x0800CC94
    r = released_keys                       ; 0x03001716
    if (r & 0x40) { snd(3); idx = (idx==0)? 8 : idx-1; }   ; Up wraps
    if (r & 0x80) { snd(3); idx = (idx==8)? 0 : idx+1; }   ; Down wraps
    if (r & 0x20) { snd(3); if (idx>3 && idx!=8) idx-=4; } ; Left
    if (r & 0x10) { snd(3); if (idx<=3)         idx+=4; }  ; Right
}
```

Handler sketch (each sets a mode byte then calls the scene setter):

| idx | handler | mode writes | wrapper scene |
|---:|---|---|---|
| 0 | `0x0800CB64` | `[0x03003510]=1`, `[0x030034D0]=2` | `0x080192B8` |
| 1 | `0x0800CB84` | `[0x03002EE4]=0`, `[0x03002EF8]=0` | `0x0800D0BC` |
| 2 | `0x0800CB98` | `[0x03002EE4]=1`, `[0x03002EF8]=0` | `0x0800D0BC` |
| 3 | `0x0800CBB8` | `[0x03002F30]=0`, `[0x03002F34]=0` | `0x0800F53C` |
| 4 | `0x0800CBD8` | `[0x03002F54]=0`, `[0x03002F4C]=0`, `[0x03002F38]=0`, `[0x03002F44]=0` | `0x08010468` |
| 5 | `0x0800CC08` | `[0x030034D0]=0`, zero 20 halfwords `0x03003450`, `bl 0x08013258` | `0x08011C34` |
| 6 | `0x0800CC3C` | zero 20 halfwords `0x03003450` | `0x080144CC` |
| 7 | `0x0800CC70` | `[0x030034D0]=1` | `0x080159C0` |
| 8 | `0x0800CC88` | — | `0x0801713C` (Help) |

Help hub dispatch:

```
idx = u8[0x030033AC]
if (pressed & (A|Start)) {
    snd(5)
    if (idx > 5) goto default
    page[idx]()                     ; table 0x08016B30
}
Up:   idx = (idx==0)? 5 : idx-1
Down: idx = (idx==5)? 0 : idx+1
```

## 6. Tables

### 6.1 Main menu items (observed, all nine entered)

| idx | wrapper scene | observed scene | DISPCNT | BG structure | VRAM MD5 (first 8) |
|---:|---|---|---|---|---|
| 0 | `0x080192B8` | `0x0801874C` | `0x1140` | BG0 8bpp, 599 tiles | `807f9c6b` |
| 1 | `0x0800D0BC` | `0x0800CF90` | `0x0140` | BG0 8bpp | `df032cb6` |
| 2 | `0x0800D0BC` | `0x0800CF90` | `0x0140` | BG0 8bpp | `df032cb6` |
| 3 | `0x0800F53C` | `0x0800F11C` | `0x1F40` | BG0–BG3 4bpp, 240-tile grid | `f9c70704` |
| 4 | `0x08010468` | `0x0800FC88` | `0x1F40` | BG0–BG3 4bpp, 240-tile grid | `58ab4361` |
| 5 | `0x08011C34` | `0x0801179C` | `0x0140` | BG0 8bpp | `a11d4e46` |
| 6 | `0x080144CC` | `0x08014240` | `0x1740` | BG1 8bpp 600 + BG2 8bpp 256 | `8eae45cd` |
| 7 | `0x080159C0` | `0x080158AC` | `0x0140` | BG0 8bpp | `e06c0205` |
| 8 | `0x0801713C` | `0x08016AC4` | `0x1140` | Help hub, 6 entries | `1643b4f4` |

Items 1/2 share a wrapper and differ only in the mode byte `0x03002EE4`; they
are two variants of the same stage-select screen. Items 3/4 are the same
4bpp grid pair. Items 5/6 are the two editor/preview screens. Item 7 is the
settings-style submenu. Item 8 is Help (verified by its 30×20 text page and
6-entry table). Exact item captions are baked as 8bpp art and were not
transcribed; the scene IDs and RAM flags above are the reproducible identity.

### 6.2 Help hub entries (observed)

| idx | page scene | VRAM MD5 (first 8) |
|---:|---|---|
| 0 | `0x080172FC` | `c3567f6b` |
| 1 | `0x08017768` | `19b4f8c8` |
| 2 | `0x08017B88` | `a489e7e3` |
| 3 | `0x08017EB8` | `b7035c0e` |
| 4 | `0x08018520` | `2490bccc` |
| 5 | returns to hub `0x08016AC4` | `510493ee` |

The download page (idx 4) exposes a secondary index at `0x030033A8`; observed
values 1,2,3,4 as Down was pressed, and A on 4 stored `4` at `0x03003D80`
(confirm/selection latch).

### 6.3 Published material vs this image

| Published item | Kind | Verification |
|---|---|---|
| Hard mode after 25 normal puzzles | unlock condition | not a literal; no searchable string |
| Special mode after 25 hard puzzles | unlock condition | same |
| Mania mode after 25 special puzzles | unlock condition | same |
| Help page reveals (1st–5th visit) | UI reveal | hub and all 5 content pages exist and are reachable |
| Download skins: Cow/UFO, Balloon/Pin, Snow/Fire | hidden content | download page exists (Help idx 4); skin swap not exercised |
| Hold B to speed credits | input behavior | published; not exercised (requires clearing 25 puzzles) |
| "JBA laboratory" body codes (title) | button code list | **not present**: no `JBA` string, no lab menu item, title reads Start only |

## 6b. Enumeration

### Space definition

* **Typed code space: 0 values.** No character alphabet exists in the image
  (no ASCII bank; see counts below), no code-entry screen exists in the 9-item
  menu or its sub-scenes, and there is no string/byte validator against user
  text. A password system would need at least one alphabet table and one
  comparison loop; neither exists.
* **Button-code space: 0 sequences.** Candidate-button data scan: 992 runs of
  ≥4 u16 values drawn from `{A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,
  Up=0x40,Down=0x80,R=0x100,L=0x200}` exist in the 4 MiB image. **0** of them
  lie in the title/menu code+image region `0x0800B000–0x0800E000`. The 10 that
  lie in `0x08000000–0x080007FFFF` disassemble as ordinary Thumb instruction
  bytes, not tables (`0x0803ECAC`, `0x0804C63E`, `0x08056A6E`, `0x08056A96`,
  `0x080595CC`, `0x080595EA`, `0x0805EDB0`, `0x080672AC`, `0x08071A68`,
  `0x08073EE4`). The title handler tests only `0x08`.
* **Menu space: 9 states.** The main menu index is a single byte
  (`0x03002EE8`) with a hard bound `cmp r0,#8` and a 9-entry dispatch table.

### Novel values

No code can be minted because no code space exists. The equivalent novel,
unpublished probe for a menu system is a value outside every published list
and outside the nine advertised items; the menu rejects such values
structurally (the dispatch is `idx>8 → default`, and the cursor cannot reach
9). This is the bounded-negative counterpart to a generated password.

### Bounds proven by rejection

Observed in mGBA with a state read after each press (RAM, not visual):

* Down from index 1: `1,2,3,4,5,6,7,8,0,1,2,3,4` — wrapping proves the
  representable set is exactly 0..8. A 9th Down returns 0; there is no item 9.
* Up from index 1: `1,0,8,7,6` — Up at 0 wraps to 8, proving 0 is the lower
  bound.
* Help Down from 0: `0,1,2,3,4,5,0` — wrapping proves exactly six Help entries.
* Help selection 0..5 each entered: five distinct page scenes + the return
  entry; no hidden seventh entry is reachable.
* Static confirmation of both bounds: `cmp r0,#8` at `0x0800CB1E` (main menu)
  and `cmp r0,#5` at `0x08016B0E` (Help).

### Text/encoding search counts

Full 4 MiB scan (`recon_counts`), hits per encoding:

| Word | ASCII | lower | +0x20 | −0x20 | UTF-16LE | UTF-16BE | 1-byte XOR |
|---|---:|---:|---:|---:|---:|---:|---:|
| PASSWORD / PASS / CHEAT / DEBUG | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CODE | 0 | 0 | 0 | 0 | 0 | 0 | 2 (art noise) |
| SECRET | 0 | 0 | 0 | 0 | 3 | 2 | 0 |
| UNLOCK / EDITOR / GALLERY | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| SOUND / OPTION / EXTRA / BONUS | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| HIDDEN | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| JBA | 1 (art) | 0 | 0 | 5 | 0 | 0 | 0 |
| SEGA / PRESS / CHALLENGE / DOWNLOAD | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CHUCHU / ROCKET | 2 | 0 | 0 | 0 | 3 / 20 | 0 / 20 | 0 |
| PUZZLE / BATTLE | 0 | 0 | 0 | 0 | 32 / 2 | 32 / 2 | 0 |

The UTF-16 hits are repetitive tile bytes (symmetric two-byte patterns); they
do not form a text bank. Every hit was classified by dumping ±0x40 bytes.
Result: **0 usable text strings other than the header**.

### Published-literal tests

* No published GBA password exists to test; the GameFAQs page for this SKU
  lists only unlock conditions and the Help reveal. Therefore there is no
  literal that could be accepted or rejected.
* The "JBA laboratory / secret body" title codes were tested as a *class*: no
  `JBA` text, no menu entry, no title sequence table. This is a rejected
  published claim, not a rejected code.
* Literal search for the ONLY candidate code strings in the same family
  (`47214`, the 6-symbol rock/scissors/paper scheme) returns no matching
  alphabet or validator in this ROM; those entries belong to a different
  title and are recorded as misattributed.

## 7. Validation evidence

**Observed (mGBA + RAM/savestate):**

* Boot/title/main-menu/Help/page transitions listed above, with scene pointer
  `[0x030016A0]`, DISPCNT, VRAM hash.
* Main-menu index sequence and wrap, read from `0x03002EE8` after each press.
* Help index and wrap, read from `0x030033AC`; six entries entered.
* Download-page secondary index `0x030033A8` 1→4 and confirm byte
  `0x03003D80`←4.
* Input struct layout at `0x03001710` (held/pressed/released) confirmed by
  holding Up/Down and diffing savestates.

**Derived (static):**

* Scene setter `0x080006E0` stores `[0x030016A0]`; 211 call sites, 104 unique
  scene entries.
* Title input checks only Start (`0x0800C7D4`: `ands r0,#8`).
* Main-menu dispatch bounds and 9-entry table (`0x0800CB1A`–`0x0800CB2C`,
  `0x0800CB40`).
* Help hub 6-entry table and wrap.
* No ASCII text bank; no title/menu mask table.

**Inferred:**

* Item-to-mode naming (puzzle/challenge/battle/editor/options) from screen
  structure and the number/kind of submenus, not from transcribed captions.
* The three download skins correspond to Help idx 4; the page exists and has
  four selectable states, but the in-stage skin swap was not exercised.

## 8. Unknowns

* The printed captions for main-menu items are baked 8bpp art; the exact
  English words were not transcribed. Their scene identities and RAM flags are
  recorded instead.
* The save-record field semantics (progress bits for Hard/Special/Mania) were
  not decoded; the unlock conditions are reported from the published list, not
  from an in-game clear.
* The in-stage effect of the three download skins was not exercised (only the
  selection UI and its RAM latch were observed).
* The credits speed-up (hold B) was not exercised because it requires clearing
  25 puzzles in this session.

## 9. Tooling

All scripts are in `/tmp/opencode/chuchurocket/`:

| File | Purpose |
|---|---|
| `phase0.py` | hashes, header, embedded-logo scan |
| `st.py` | mGBA `.ssN` PNG → `gbAs` → RAM/VRAM/OAM/IO accessors |
| `render.py` | VRAM tilemap → 8bpp ASCII renderer (no images used) |
| `dbg.py`, `dbg3.py` | mGBA `-d` pty debugger harness (`x/`, `r/`, breakpoints) |
| `recon_counts.txt` | word × encoding hit table |
| `button_scan.txt` | button-mask run scan |
| `walk.py` | main-menu 0..8 walker (savestate-verified) |
| `helppage.py`, `dl.py`, `bounds.py` | Help page and cursor-bound experiments |

Installed/used: `mgba-sdl 0.10.5`, `binutils-arm-none-eabi`, `Xvfb`,
`openbox`, `xdotool`, Python 3, `capstone`. No images/screenshots were used;
all proofs are bytes, addresses, VRAM maps and RAM reads.

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed here. Only
hashes, addresses, algorithms, and original observations are published.
