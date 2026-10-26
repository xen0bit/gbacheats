# Big Mutha Truckers (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-26.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Big Mutha Truckers/Big Mutha Truckers.gba` |
| Size | 4 MiB (`0x400000`, 4,194,304 bytes) |
| Header title | `BIGMTRUCKER` |
| Game code | `B63E` |
| Maker code | `20` |
| Software version | `0` (Rev.00) |
| MD5 | `f1be09ac4b8d6a9e2c955cab741669ef` |
| SHA-1 | `6d48801835c211decd50244e38145823b0c82be5` |
| SHA-256 | `78a17fd1ed21f93a08e00c5de1038d16a068eba1680c137b87caf6fe98ff819b` |

Header bytes of note:

| Offset | Bytes | Meaning |
|---|---|---|
| `0x00` | `2e 00 00 ea` | ARM `b 0x080000C0` (normal entry) |
| `0xA0` | `BIGMTRUCKER\0` | title, NUL padded |
| `0xAC` | `B63E` | game code |
| `0xB0` | `20` | maker code |
| `0xB2` | `0x96` | fixed value, correct |
| `0xBC` | `0x00` | software version |
| `0xBD` | `0xC0` | complement check; recomputed = `0xC0`, **valid** |
| `0xBE` | `00 00` | header checksum **field is zero**; the standard algorithm over `0xA0..0xBC` gives `0xC0C0` |

Embedded-header scan: exactly **one** Nintendo-logo hit (file offset `0x4`, i.e. the
primary header). This is a single ROM image, not a multi-game pack, and there is no
second/stub header. The code at `0x080000C0` is the stock ARM crt0
(`mov r0,#0x12; msr cpsr…`), and no trainer/intro banner exists before it.
The zero header-checksum word is the only anomaly; the valid complement check and
clean entry point mean mGBA boots it normally. Recorded as a possible header edit,
not as a proven trainer (see §8).

ROM addresses below are `0x08000000 + file_offset`. All findings are tied to the
hash above.

---

## 2. Executive summary

The GBA port (Raylight Studios / Destination Games, 2005) **does not contain the
console versions' text cheat menu**. There is no `PASSWORD`/`CHEAT` string anywhere
in the 4 MiB image, the Options menu has only `Sound` and `Credits`, and the game
has no character/letter entry UI at all (no ASCII `A–Z` alphabet string exists in
the ROM).
All published *console* cheat words (`VARLEY`, `GINGERBEER`, `LOTSAMONEY`,
`ATJCEHJMJ`, `CHEATINGMUTHATRUCKER`, …) are absent from the image.

What the port **does** contain is a small, hidden **button-code table**:

* Installed once at boot from a 2-record table at `0x082812AC`.
* Only evaluated while the game is on the title screen (`Press START`, state 5).
* Two fixed sequences; on a full match the game plays an SFX, flashes the screen
  white and sets one bit in a cheat bitmap at `0x02000145`.

**Code 1 (published):** `Up L Right Right A B Down Down R` → sets bit 0. A new
game started afterwards uses **Evil Bob's truck**: the character-select screen
shows a different (silver/black) rig for the same character (Bobbie Sue).
This matches the only published GBA code (GameFAQs: "Access Evil Bob's Truck").

**Code 2 (not published anywhere):** `Up Down Left R B A Right L` → sets bit 1.
It is accepted by the same validator, produces the same flash/SFX, and is proven
in memory (`0x02000145` = `0x02` on a fresh boot). No consumer of bit 1 was found:
the only reader of the cheat bitmap located in the ROM is the profile/new-game
initialiser, and it masks bit 0 only. Entering code 2 does not change the
character-select truck. Bit 1 is most plausibly a second (2-player) unlock bit or
a leftover of the console cheat set (inference; see §8).

Enumeration result: the table has **exactly two** entries (verified by a whole-ROM
structural scan for `{seq_ptr,len,id}` records); there is no checksum, no
alphabet, no generator and no text entry. Bounds are proven by rejected inputs
(a wrong last button; an 8-of-9 prefix; the full sequence pressed outside the
title state), each leaving the cheat bitmap at `0x00`.

---

## 3. How to reproduce

### Emulator

```bash
Xvfb :183 -screen 0 1024x768x24 &
DISPLAY=:183 openbox &
DISPLAY=:183 SDL_AUDIODRIVER=dummy mgba -3 "Big Mutha Truckers.gba" &
```

mGBA SDL 0.10.5. Default keymap used here:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Keys must be **tapped, not rolled**: the validator only accepts a press when the
previous frame had *no* button down (`(cur & 0x3FF) != 0` and `(prev & 0x3FF) == 0`).
Hold each button ~120–200 ms with a gap of similar length.

### Menu path to the cheat entry point

1. Boot and wait for the title screen (`Press START`).
2. Enter the sequence **while the title screen is showing** — not in the main menu.
3. The screen flashes white (one or more forced-blank frames; a fully white frame was
   captured) and an SFX plays.
4. Start → New Game → character select: with code 1 entered, the character's rig
   is the Evil Bob truck.

### Codes

| # | Sequence | Masks (`u16`) | Published? |
|---|---|---|---|
| 1 | Up, L, Right, Right, A, B, Down, Down, R | `0040 0200 0010 0010 0001 0002 0080 0080 0100` | Yes (GameFAQs GBA) |
| 2 | Up, Down, Left, R, B, A, Right, L | `0040 0080 0020 0100 0002 0001 0010 0200` | **No** |

### Memory proof (no GameShark/CodeBreaker used)

The CLI debugger built into `mgba -d` can read/write/break:

```
> b 0x0800497c          ; strb r1,[r0]  in the cheat-result handler
> c
(tap code 1 on the title screen)
Hit breakpoint 1 at 0x0800497C
 r0: 02000145   r1: 00000001 ...        ; address 0x02000145, value 1
> r/1 0x02000145
 0x00                                  ; before the store
> n
> r/1 0x02000145
 0x01                                  ; bit 0 set
```

A second, independent read can be taken from an mGBA savestate (Shift+F1 writes a
PNG-format state; the `gbAs` zlib chunk decompresses to the serialized machine,
EWRAM at decompressed offset `0x21000`):

```
0x02000145 -> state[0x21000 + 0x145]
```

Values observed from savestates: fresh boot `00`; after code 1 `01`; fresh boot
after code 2 only `02`; code 1 then code 2 `03`.

---

## 4. Address map

### Static

| Address | What |
|---|---|
| `0x08004B6C` | boot/init function that installs the cheat table |
| `0x08004C1C` | `bl 0x0802D920` with `r0 = 0x082812AC` (install call) |
| `0x0802D920` | **CheatInit(table)** |
| `0x0802D7D8` | **CheatUpdate()** — per-frame matcher, returns id or `-1` |
| `0x0802D98C` | **CheatMatch(entry)** — same prefix-compare logic factored out; no caller found in this ROM (dead duplicate) |
| `0x0802D8C4`..`0x0802D8EE` | full-match path inside CheatUpdate |
| `0x080048E8` | main-loop function that gates the call on state == 5 |
| `0x08004948` | `movs r0,#0; bl 0x0802D7D8` |
| `0x0800494C`..`0x0800497C` | result handler: sets `0x02001BC4`, plays SFX 0x45, ORs id into `0x02000145` |
| `0x080006B4` | profile/new-game initialiser |
| `0x080006D6` | `ldrb` of `0x02000145` (the only reader located in the ROM) |
| `0x080006DE` | `strb` to `0x0200013F` of `(flags & 1)` |
| `0x08005E42` | caller of `0x080006B4` (menu state-machine case; new-game path) |
| `0x080049C2` | second caller of `0x080006B4` (menu/profile path) |
| `0x0802BB44` | play-SFX routine |
| `0x08281288` | sequence 2 data (8 × `u16`) |
| `0x08281298` | sequence 1 data (9 × `u16`, then `0x0000`) |
| `0x082812AC` | cheat table entry 0 (`{0x08281298, 9, 1}`) |
| `0x082812B4` | cheat table entry 1 (`{0x08281288, 8, 2}`) |
| `0x082812BC` | table terminator (seq_ptr = 0) |

### RAM / I/O

| Address | What |
|---|---|
| `0x02001BD4` | cheat table pointer (set by CheatInit) |
| `0x02001BD8` | one byte per entry: "already fired this session" |
| `0x02001BDC` | key-history buffer, 32 bytes = 16 × `u16` |
| `0x02001BE0` | `u16` history count |
| `0x02001BE4` | `u32` flash timer (loaded with `0xA4` on a match) |
| `0x02000145` | **cheat bitmap** (bit 0 = code 1, bit 1 = code 2) |
| `0x0200013F` | "use Evil Bob truck" byte = `cheat_bitmap & 1` |
| `0x02001BC4` | "a cheat matched this session" flag (set on any match) |
| `0x0200092C` | input module: `u16 cur`, `u16 prev`, … |
| `0x02003AA4` | current state object; `[[0x02003AA4]]` is the state id |
| `0x0300379C` | frame delta used to decrement the flash timer |
| `0x04000000` | DISPCNT (bit 7 forced blank is set for the flash) |

---

## 5. Algorithm

```c
typedef struct {            // 8 bytes, ROM table at 0x082812AC
    const u16 *seq;         // 0x08281288 / 0x08281298
    u16 len;                // 8 / 9
    u16 id;                 // 2 / 1
} CheatEntry;

static const CheatEntry *g_tbl;     // 0x02001BD4
static u8  *g_fired;                // 0x02001BD8  (one byte per entry)
static u16 *g_hist;                 // 0x02001BDC  (32 bytes, 16 slots)
static u16  g_hist_len;             // 0x02001BE0
static u32  g_flash;                // 0x02001BE4

void cheat_init(const CheatEntry *tbl) {            // 0x0802D920
    g_tbl = tbl;
    n = 0;
    while (tbl[n].seq) n++;                         // stride 8, terminator seq==0
    g_hist  = alloc(32);
    g_fired = alloc(n);
    memset(g_fired, 0, n);
    g_hist_len = 0;
    g_flash    = 0;
}

int cheat_update(void) {                            // 0x0802D7D8
    if (g_flash > 0) {
        g_flash -= *(u32*)0x0300379C;               // count the flash window down
    } else {
        DISPCNT &= 0x7FFF;                          // end-of-flash cleanup
    }
    u16 cur  = *(u16*)0x0200092C;                   // input module: current keys
    u16 prev = *(u16*)0x0200092E;                   // previous frame keys
    if ((cur & 0x3FF) == 0 || (prev & 0x3FF) != 0)  // edge only, and no other key held
        return -1;

    g_hist[g_hist_len++] = (cur ^ prev) & cur;      // single-button press mask

    int prefix_alive = 0;
    for (i = 0; tbl[i].seq; i++) {
        if (g_fired[i]) continue;                   // a code fires once per session
        int j = 0, r = 1;
        while (j < g_hist_len && j < tbl[i].len) {
            if (tbl[i].seq[j] != g_hist[j]) { r = 2; break; }  // mismatch
            j++;
        }
        if (r != 2) r = (j == tbl[i].len) ? 3 : 1;  // 1 = prefix, 3 = complete
        if (r == 1) prefix_alive = 1;
        if (r == 3) {
            g_hist_len = 0;
            g_fired[i] = 1;
            play_sfx(0x45);                         // 0x0802BB44
            DISPCNT |= 0x80;                        // forced blank -> white flash
            g_flash = 0xA4;
            return tbl[i].id;
        }
    }
    if (!prefix_alive) g_hist_len = 0;              // wrong first key resets history
    return -1;
}
```

Caller (inside the title-screen state) at `0x08004948`:

```c
int id = cheat_update();                 // returns -1 or 1..2
if (id != -1) {
    g_cheat_used = 1;                    // 0x02001BC4
    play_sfx(0x45);
    if ((u8)(id - 1) <= 1)               // ids 1 and 2 only
        *(u8*)0x02000145 |= id;          // 0x0800497C
}
```

New game / multiplayer profile init, `0x080006B4`:

```c
*(u8*)0x0200013F = *(u8*)0x02000145 & 1;   // only bit 0 is consumed
```

The cheat update is only reached when `[[0x02003AA4]] == 5`. In the emulator the
sequences are accepted on the `Press START` title screen and are *not* consumed on
the `New Game / Load Game / Multiplayer` menu (there the same keys just drive the
menu), which identifies state 5 as the title screen.

---

## 6. Tables

### 6.1 Button masks (as stored in the table)

| Button | Mask |
|---|---|
| A | `0x0001` |
| B | `0x0002` |
| Select | `0x0004` |
| Start | `0x0008` |
| Right | `0x0010` |
| Left | `0x0020` |
| Up | `0x0040` |
| Down | `0x0080` |
| R | `0x0100` |
| L | `0x0200` |

The recorded press value is the full 10-bit key state (`& 0x3FF`), so Select and
Start are legal symbols for the matcher even though neither is used by the two
shipped codes.

### 6.2 The cheat table (bytes as in ROM)

```
0x08281288: 40 00 80 00 20 00 00 01 02 00 01 00 10 00 00 02   seq #2 (8 entries)
0x08281298: 40 00 00 02 10 00 10 00 01 00 02 00 80 00 80 00
0x082812A8: 00 01 00 00                                        seq #1 (9 entries) + 0
0x082812AC: 98 12 28 08 09 00 01 00                            {seq=0x08281298, len=9, id=1}
0x082812B4: 88 12 28 08 08 00 02 00                            {seq=0x08281288, len=8, id=2}
0x082812BC: 00 00 00 00 00 00 00 00 ff ff                       terminator
```

### 6.3 Published-code cross-check

The only published GBA code found (GameFAQs, GBA cheats page; archived
2018-11-26 snapshot) is:

> Access Evil Bob's Truck — press **Up L Right Right A B Down Down R** at the title
> screen; the screen will flash if done correctly.

It matches the table's first record (id 1) exactly (9 masks). IGN's and GameFAQs' *console* pages
list a text cheat menu (`VARLEY`, `GINGERBEER`, `PUBLICTRANSPORT`, `USETHEFORCE`,
`LOTSAMONEY`, `LAZYPLAYER`, `VICTORS`, `JINGLEBELLS`, `ATJCEHJMJ`,
`CHEATINGMUTHATRUCKER`); none of those strings exists in this ROM in any case
(19 literals searched case-insensitively, all zero as standalone codes), and the
GBA Options menu contains no such screen.

### 6.4 Search-space counts for the negative results

| Search | Result |
|---|---|
| `strings -n 4` inventory | 65,998 strings |
| `password`, `cheat`, `secret`, `unlock`, `code` (case-insensitive, whole ROM) | 0 hits |
| `debug` (case-insensitive) | 1 hit: `MPDebugProcess` descriptor name (`0x043DA4`) |
| `cash` (case-insensitive) | 5 hits, all HUD/loan/mission text (`Cash`, `CASH BONUS`, …) |
| `ABCDEFGHIJKLMNOPQRSTUVWXYZ` | 0 hits → no on-screen letter keyboard |
| `0123456789ABCDEF` | 1 hit at `0x0477EC`, a numeric/hex formatting table |
| 19 published console cheat words | 0 present as codes; substring hits only inside mission/HUD text (`MISSIONS won`, `WHEN BIKERS ATTACK`, `CASH BONUS`, `BRIDGE` in mission prose) |

The visible UI text of this game is plain ASCII (`Press START`, `MAIN MENU`,
`OPTIONS MENU`, …), so a hidden `CHEAT`/`PASSWORD` screen would have appeared in
the string scan. None exists.

---

## 6b. Enumeration

### Space definition

* Format: fixed **table**, not an algorithm. 2 records, 8 bytes each, terminated
  by `seq_ptr == 0`.
* Symbols: 10 (the full keypad, `0x001`–`0x200`; 10-bit state).
* Lengths: 9 and 8 presses.
* Checksum / parity / key schedule: **none**.
* Reserved state: one "fired" byte per entry at `0x02001BD8`; a code can fire only
  once per session. History buffer 16 × `u16`.
* Representable values: every press string over 10 symbols up to the 16-slot
  history, i.e. `Σ(10^k)` for k = 1..16; **exactly 2** are accepted (the two
  shipped sequences). There is no encoder, decoder, generator or alphabet table.

A whole-ROM structural scan for 8-byte `{rom_ptr, len 1..16, id 1..64}` records
whose pointer targets a run of button masks returns only:

```
0x082812AC  ptr 0x08281298  len 9  id 1
0x082812B4  ptr 0x08281288  len 8  id 2
```

(14 further hits were asset-table false positives with `len=1, id=4`.)

### Code 1 — published, verified

`Up L Right Right A B Down Down R`

| Evidence | Result |
|---|---|
| Breakpoint `0x0800497C` | hit with `r0=0x02000145`, `r1=0x00000001` |
| `0x02000145` | `0x00` → `0x01` |
| Screen | full-white flash frame (evidence `14-code1-flash-white.png`) |
| New game | character-select rig changes to the silver/black Evil Bob truck (`12-code1-evil-bob-truck.png`) |

### Code 2 — unpublished, minted and confirmed

`Up Down Left R B A Right L`

| Evidence | Result |
|---|---|
| Fresh boot, savestate read of `0x02000145` | `0x00` → `0x02` |
| Breakpoint `0x0800497C` | hit with `r1=0x00000002` |
| After code 1 in the same session | `r1=0x00000003` (`0x01 \| 0x02`) |
| Screen | full-white flash frame (evidence `15-code2-flash-white.png`) |
| New game | character-select rig **unchanged** (blue default; `13-code2-truck-unchanged.png`) |
| Read watchpoint on `0x02000145` through the new-game and multiplayer-profile init paths | fires only in `0x080006B4`, whose mask is `1` |

This code is in the shipped table, so it is developer-intended. It is **not** in
any published list (GameFAQs GBA page has only the Evil Bob code; the console
cheat pages list text words that do not exist in this build).

### Bounds proven by rejection

| Input | Result |
|---|---|
| Sequence 1 with the last button changed to B (`… Down Down B`) | no match; `0x02000145` stays `0x00` |
| Sequence 1 prefix only (8 of 9, ending at the second `Down`) | no match; `0x02000145` stays `0x00` |
| Correct sequence pressed while the main menu (not the title) is open | not consumed; menu acts on the keys instead |
| Re-entering a code that already fired in the session | ignored (`g_fired[i] != 0`) |

The two sequence rejections were verified with savestate byte
`0x02000145 == 0x00` after the attempt.

---

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| Table at `0x082812AC` holds 2 button sequences, ids 1/2 | Observed (bytes) | ROM dump + structural scan |
| Matcher is prefix-based, edge-triggered, resets on mismatch | Derived | `0x0802D7D8` disassembly |
| Code 1 sets `0x02000145` bit 0 | Observed | breakpoint `0x0800497C` (`r1=1`), savestate byte |
| Code 2 sets bit 1 | Observed | breakpoint (`r1=2`), fresh-boot savestate `0x02` |
| Full match blanks the screen white and plays SFX 0x45 | Observed + Derived | white frame captured; `DISPCNT |= 0x80` / `play_sfx(0x45)` in the match path |
| Code 1 changes the new-game truck to Evil Bob's rig | Observed | `12-code1-evil-bob-truck.png` vs `03-character-select.png` |
| New-game init copies only bit 0 to `0x0200013F` | Derived | `0x080006D6`/`0x080006DE`; watchpoint shows only this reader |
| Bit 1 (`0x0200013F`-style consumer) has no consumer | Derived + bounded test | only reader of `0x02000145` located in the ROM is `0x080006B4`; read watchpoint across the new-game and multiplayer-profile init paths; whole-ROM offset scans for `base+0x141` find one site |
| GBA port has no text password/cheat menu | Observed + bounded search | string scans (§6.4), Options menu walk, full menu enumeration |
| Console cheat words are absent | Observed | 19 literal searches, zero hits |

Screenshots (all 720×480, 3× scale) are in `evidence/`:

```
01-title.png                  title / Press START
02-main-menu.png              New Game / Load Game / Multiplayer
03-character-select.png       Bobbie Sue default (blue) rig — no cheat
04-ingame-main-menu.png       Trial by truckin' / Mission Mode / Options / Exit
05-options-menu.png           Sound / Credits only
06-sound-menu.png             Music / SFX
07-pause-menu.png             Resume / Driving License / Music Tracks / Sat Nav / Exit
08-garage.png                 Refuel / Repair / Upgrade / Change Trailer
09-house-menu.png             Talk To Mom / Sibling Ranking / Leave
10-multiplayer-profile.png    Profile settings (6 slots) — multiplayer path
11-connecting.png             "Please wait while connecting"
12-code1-evil-bob-truck.png   cheat 1 applied -> silver/black rig
13-code2-truck-unchanged.png  cheat 2 applied -> default blue rig
14-code1-flash-white.png      full-white flash frame after code 1
15-code2-flash-white.png      full-white flash frame after code 2
```

Menu enumeration for the negative result: title, main menu, character select
(4 characters), in-game main menu, options, sound, credits, pause, garage,
house menu, location menu, multiplayer profile, connecting/error, quit
confirmation, save-lost confirmation. No `Cheat`, `Password`, `Debug` or `Codes`
entry appears anywhere.

---

## 8. Unknowns

1. **Consumer of cheat bit 1.** Code 2 sets `0x02000145` bit 1, but nothing in the
   ROM reads that bit during title, menus, new game, character select or
   multiplayer-profile init. It may be a 2-player unlock that is applied later in
   a link game, or a leftover from the console cheat set. Not claimed as working.
2. **`MPDebugProcess`.** A process-descriptor block at `0x082843B4` names
   `MPDebugProcess` with four function pointers (`0x0801F7B1`, `0x0801F7AD`,
   `0x0801F7B5`, `0x080474C4`), but no word anywhere in the ROM points into the
   `0x08284300–0x08284440` descriptor block, and no debug screen was reachable
   through any menu. Treated as dead data in this build.
3. **`Controller` option.** The strings `CONTROLLER`, `Accelerate`,
   `Brake/Reverse`, `Change Gear`, `Change View`, `Steer`, `Pause`, `Default`
   exist at `0x044164`–`0x0441BC`, but the shipped Options menu contains only
   `Sound` and `Credits`. Probably a cut menu; no way to open it was found.
4. **Header checksum zero.** The GBA header checksum word at `0xBE` is `0x0000`
   while the complement is valid; no trainer code or second header was found.
   Whether this is an original mastering quirk or a header edit is unresolved.
5. **Effect of code 2 in a real 2-player link game.** Out of scope for this
   single-instance session (no second GBA or link); the bit-1 consumer therefore
   remains unknown.

---

## 9. Tooling

* `mGBA 0.10.5` (`mgba-sdl`) under `Xvfb :183`, Openbox; `xdotool` for input,
  `ImageMagick import` for window captures.
* mGBA's built-in CLI debugger (`mgba -d`): breakpoints at `0x0800497C`,
  read watchpoint on `0x02000145`, `r/1`, `n`.
* mGBA savestates (PNG container with a `gbAs` zlib chunk) parsed in Python with
  `zlib`; EWRAM found at decompressed offset `0x21000` by locating the cheat-table
  pointer `0x082812AC` at `0x21000 + 0x1BD4`.
* `arm-none-eabi-objdump -D -b binary -marm -M force-thumb` for the ranges in §4.
* Python scanners in the work directory: raw Thumb `BL`/literal scans, the
  `{seq_ptr,len,id}` structural scan, and byte-pattern scans for `base+0x141`
  address construction.

No ROM, graphics, music or game text is redistributed; only addresses,
algorithms, hashes, our own generated codes and emulator screenshots are
published here.

---

### Quick reference

```
Title screen ("Press START") — state 5 only

Code 1 (published, Evil Bob truck):  Up L Right Right A B Down Down R
Code 2 (unpublished):                Up Down Left R B A Right L

On match: SFX 0x45, one white frame, 0x02000145 |= id
New game: 0x0200013F = 0x02000145 & 1  -> Evil Bob truck model
```
