# 2-in-1 – Dragon Ball Z Gamepack: Buu's Fury & GT Transformation (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `2-in-1 - Dragon Ball Z Gamepack - Buu's Fury & GT - Transformation.gba` |
| Size | 16,777,216 bytes (`0x1000000`, 16 MiB) |
| Header title (`0xA0`) | `BUUGTCOLLECT` |
| Game code (`0xAC`) | `BUFE` |
| Maker code (`0xB0`) | `70` |
| Version (`0xBC`) | 0 |
| Complement (`0xBD`) | `0x3B` (valid: recomputes to `0x3B`) |
| Header checksum (`0xBE`) | `0x0000` (the collection linker left this field zeroed; a normal cart would carry the derived value) |
| Entry branch (`0x00`) | `0xEA00002E` (ARM branch) |
| MD5 | `89bbc0e48966feca4f22e2b31caad638` |
| SHA-1 | `3733adaff49866a8fe01e23526f4f52ca39cbf58` |
| SHA-256 | `6ae7ce9bb46c262423ea7a95f57cce742f1f05802f94b8706b174760e1791312` |

The file is a **multi-game image**, not a single GBA program. A scan for the
156-byte Nintendo logo (`24 ff ae 51 …`) at header offset `+4` finds three
GBA headers:

| File offset | ROM address | Title | Code | Maker | Version | Complement |
|---:|---|---|---|---|---|---|
| `0x000000` | `0x08000000` | `BUUGTCOLLECT` | `BUFE` | `70` | 0 | `0x3B` |
| `0x030000` | `0x08030000` | *(blank)* | `\0\0\0\0` | `01` | 0 | `0xF0` |
| `0x800000` | `0x08800000` | *(blank)* | `\0\0\0\0` | `01` | 0 | `0xF0` |

A 3-instruction dispatcher at file `0x704` (`0x08000704`) is the proof of the
layout:

```text
08000704: 4801  ldr r0,[pc,#4]   @ 0x0800070C -> 0x08030000
08000706: 4700  bx  r0
08000708: 4801  ldr r0,[pc,#4]   @ 0x08000710 -> 0x08800000
0800070a: 4700  bx  r0
0800070c: .word 0x08030000       @ game 1 = Buu's Fury image
08000710: .word 0x08800000       @ game 2 = GT Transformation image
```

So the cartridge is:

* `0x08000000–0x0802FFFF` — a 192 KiB **collection launcher** (game-select
  screen, "WinGBACore" engine; see the `M:\WinGBACore\*.cpp` strings at
  `0xA1C`, `0x10D4`, `0x25FC`, `0x32B8`).
* `0x08030000–0x087FFFFF` — **Dragon Ball Z: Buu's Fury** image (7.8 MiB of a
  8 MiB build; header title/code blanked by the linker).
* `0x08800000–0x08FFFFFF` — **Dragon Ball GT: Transformation** image (full
  8 MiB; header title/code blanked).

**All addresses inside the second game in this report are `0x800000`
(8 MiB) higher than in a standalone GT ROM.** File offset ↔ ROM address is
`rom = 0x08000000 + file_offset` for the whole 16 MiB file; game 2's
standalone addresses are `rom − 0x800000`.

Both games are built on Webfoot Technologies' engine
(`K:\Source\ByteCodeInterpreter\ByteCodeInterpreter.cpp` at `0x34160`,
`K:\Source\CharacterData.cpp` at `0x43BAC`, etc.).

---

## 2. Executive summary

The collection contains exactly **one developer-intended cheat system**, and
it lives in the **GT: Transformation** half: a set of button sequences read
during normal play and on the GT title menu. There is **no password entry
screen, no code-entry field, and no debug menu** in either game.

The system is data-driven and identical in construction to a classic
button-cheat table:

* An engine-level **input recorder** keeps a 64-entry ring of the last
  *newly pressed* 10-bit GBA key masks in IWRAM at `0x030040D8`.
* A shared **sequence matcher** `0x0883500E` compares the newest *N* ring
  entries against an array of `u16` key masks. It is called once per frame for
  each cheat, from two native handlers.
* Two tables hold the codes as `u16` masks, **not** NUL-terminated strings:
  * **In-game table** at ROM `0x08853244` (file `0x853244`) — 8 codes,
    entered at any time during gameplay (not paused).
  * **Title-menu table** at ROM `0x0885A8C8` (file `0x85A8C8`) — 9 codes,
    entered on the GT title screen: five unlock one hidden character each, a
    sixth unlocks all five at once, one adds Zeni, and two set option/secret
    flags.
* On a match the game plays sound effect `0x40` (the "small chime" the
  published cheat lists mention) and then toggles a flag, sets a bit in the
  save profile, or writes a stat.

Everything publicly documented for GT (GameFAQs/Cheat Code Central) was found
verbatim in the in-game table, plus **four menu codes that are not on any
published list**: the unlock-all-characters code, the +20,000 Zeni code, and
two secret-flag codes. Two of those four (unlock-all and Zeni) were confirmed
live in mGBA; the other two are derived from the handler and are the only
entries whose visible effect was not exercised.

The whole code space is the two fixed tables (17 sequences); there is no
checksum, alphabet or generator, so any sequence not equal to a table entry
does nothing. This is demonstrated with rejection tests at the title screen
and in gameplay (§7, §6b).

The unlock/Zeni values are **not persistent**. Entering Story Mode
re-initialises the profile from SRAM, and the SRAM save block was never
rewritten by the tested flows, so the values live only for the session in
which they are entered (§7).

The **Buu's Fury** half has no code table and no code-entry UI. Its five pause
tabs and three front-end menus were walked; the only publicly claimed input
cheat ("Perfect Fusion", `Up, B, Left, Down, A`) is not stored as a mask table
in this build and was not confirmed (see §8).

---

## 3. How to reproduce

### Emulator

```bash
Xvfb :107 -screen 0 1024x768x24 &
DISPLAY=:107 openbox &
cd "roms/2-in-1 - Dragon Ball Z Gamepack - Buu's Fury & GT - Transformation"
DISPLAY=:107 SDL_AUDIODRIVER=dummy mgba -3 \
  "2-in-1 - Dragon Ball Z Gamepack - Buu's Fury & GT - Transformation.gba"
```

This was done with mGBA 0.10.5 (SDL), 3× scale; the GBA viewport is a
720×480 window. Keymap used: **A = `x`, B = `z`, L = `a`, R = `s`,
Start = `Return`, Select = `BackSpace`, d-pad = arrow keys**. Hold keys
100–250 ms; the input recorder samples once per frame.

### Reaching the GT title menu

1. Boot → collection launcher shows two covers, Buu's Fury (left, colour) and
   GT (right, grey).
2. `Right`, then `A` → GT copyright screen → Webfoot logo → attract → press
   `Start`.
3. The GT main menu is a 5-item scrolling list:
   `SECRETS  STORY MODE  ????  MULTIPLAYER  OPTIONS`.

### Entering a menu code

On the main menu, enter e.g. `Left Right Left Right Up Up Up B`
(keys `Left Right Left Right Up Up Up z`). A chime is audible (audio muted
under Xvfb). The d-pad presses also move the menu cursor; that is harmless.
Then choose **SECRETS** and read `Secrets … % Unlocked`.

* `Left Right Left Right Up Up Up B` → SS Goku unlocked (observed 10 %
  together with the next)
* `Left Right Left Right Up Up Down B` → Piccolo unlocked (observed)
* `Down Up Left Left Down Up Left Left Down Up Left Left Up Up Down Up B`
  → **all five** hidden characters, `26 % Unlocked` (observed)

### Entering the Zeni code

From the title menu, in one uninterrupted sequence:

`Up Down B Left Right B Lb Rb B Up Left Down Lb Rb Lb Rb B`

(`Lb`/`Rb` = shoulder L/R; `Left`/`Right` = d-pad; the two `Left Right` at
positions 4–5 are **d-pad**, not shoulders — using shoulders there is the most
common way to make this code silently fail).

The RAM counter at `0x03001CDC` goes from 0 to `0x00004E20`, and choosing
**SECRETS** immediately afterwards shows `20000 Zeni` (`t21.png`).

### Entering an in-game code

Story Mode → Start New Game → pick `Imegga` on the Star Map → clear the
opening dialogue → during gameplay (not paused) enter:

`Down Down Down Up Up Up Right Right Right Up Down Right Up B`

Pause (`Start`) → **View Stats**: all three bars (Health/Strength/Power) go
from partially filled to completely filled. This is the reproduction used for
the observed confirmation in §7.

### Rejection test

Enter one button wrong and the code silently does nothing: no chime, no flag
write, no stat change. Tested variants:

* title: master-unlock code with the final `B` replaced by `Select`
  (`Down Up Left Left Down Up Left Left Down Up Left Left Up Up Down Up Select`);
* gameplay: invincibility code with the final `B` replaced by `A`
  (`Up Down Left Right Up Down Lb Rb A A`).

Use the same method to re-check: a write watchpoint on the target flag
(`0x03001CF8` at the title, `0x0300270C` in gameplay) and on the profile
counter must never fire, while the same watchpoints do fire for the correct
sequence.

---

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`). "GT" values are
for the embedded second image; subtract `0x800000` for standalone-GT offsets.

### 4.1 Engine input + matcher

| ROM address | File | Kind | Meaning |
|---:|---:|---|---|
| `0x0834F68` | `0x834F68` | Thumb function | `input_sample(state, keys)`: edge-detect and append to ring |
| `0x083500E` | `0x83500E` | Thumb function | `seq_match(state, len, seq)`: compare newest *len* inputs with `u16 seq[]` |
| `0x030040D8` | — | IWRAM struct | input history state (see below) |
| `0x030040D8` | — | `u8` | `head` — next ring slot, 0…63 |
| `0x030040DA` | — | `u16` | current key state (active-high `~KEYINPUT & 0x3FF`) |
| `0x030040DC` | — | `u16` | keys newly **pressed** this frame |
| `0x030040DE` | — | `u16` | keys newly **released** this frame |
| `0x030040E0` | — | `u16[64]` | ring of press events (index `head-1` = newest) |

`input_sample` pseudocode (from `0x0834F68`):

```c
changed = (prev ^ keys) & 0xFFFF;
pressed = keys & changed;
released = prev & changed;
st->pressed = pressed;
st->released = released;
st->keys = keys;
if (pressed) {
    st->ring[st->head] = pressed;
    st->timestamps[st->head] = frame_counter;   /* parallel u32 log at +0x80 */
    st->head = (st->head + 1) & 63;
}
```

`seq_match` (from `0x083500E`):

```c
bool seq_match(InputState *s, int len, const u16 *seq)
{
    if (s->pressed == 0) return false;       /* [s+4] */
    int idx = (u8)s->head - 1;
    if (idx < 0) idx = 63;
    for (int i = len - 1; i >= 0; i--) {
        if (seq[i] != s->ring[idx]) return false;
        if (i == 0) return true;
        if (--idx < 0) idx = 63;
    }
}
```

### 4.2 GT cheat table + handlers

| ROM address | File | Meaning |
|---:|---:|---|
| `0x08853228` | `0x853228` | literal base used by the gameplay handler; `[+0]` = `0x030040D8` |
| `0x08853244` | `0x853244` | **in-game code table** (8 entries, `u16` masks) |
| `0x088532EA` | `0x8532EA` | end of table (`0x0000`) |
| `0x088047E0` | `0x8047E0` | gameplay per-frame cheat handler (checks at `0x08804816`…`0x08804A20`) |
| `0x0885A8C8` | `0x85A8C8` | **title-menu code table** (9 entries) |
| `0x0885A994` | `0x85A994` | end of table |
| `0x0880E1C8` | `0x80E1C8` | title-menu handler, start of the 9 `seq_match` checks |
| `0x0880E3E8` | `0x80E3E8` | last menu check |
| `0x0885A8AC` | `0x85A8AC` | UI/global struct; `+0x00` = input state ptr, `+0x18` = profile ptr |
| `0x088035AA` | `0x8035AA` | `set_flag_A(obj, id)`: `obj[0x2C + (id>>5)*4] |= 1<<(id&31)` |
| `0x088035C8` | `0x8035C8` | `set_flag_B(obj, id)`: `obj[0x28 + (id>>5)*4] |= 1<<(id&31)` |
| `0x08833170` | `0x833170` | `play_sfx(obj, id, 0x40, 0)` — called on every match |

### 4.3 GT state / flags

| Address | Meaning |
|---|---|
| `0x03001CD0` | profile / "Secrets" object (also what CodeBreaker "Access All Secrets" writes) |
| `0x03001CDC` | profile + `0x0C`: **Zeni** counter |
| `0x03001CF8` | profile + `0x28`: unlock bitfield A (bits 5–9 = hidden characters, 11–16 = option entries) |
| `0x03001CFC` | profile + `0x2C`: unlock bitfield B |
| `0x03002704` | pointer/handle to the current player entity |
| `0x0300270C` | invincibility toggle (`u8`, XOR 1) |
| `0x0300277C` | one-hit-kill / object-break toggle (`u8`, XOR 1) |
| `0x03002874` | flag written to `1` by menu code `+0x94` (purpose not identified) |

Literal references seen in code: `0x08814550` (pool holding `0x0300270C` and
`0x0300277C`, file `0x814550`), `0x08808FFC`, `0x088092FC` (both
`0x0300277C`). A 4-byte copy of `0x03001CDC` also occurs at file `0xF211C8`,
but that region is data, not the display routine, so it is not evidence of a
reader; the Zeni field's identity comes from the handler (`+0x0C` of the
`DBGT` profile object) and from the on-screen `20000 Zeni` after the write.

### 4.4 Other halves

| ROM address | Meaning |
|---:|---|
| `0x08000000` | collection launcher header + code |
| `0x08030000` | Buu's Fury image base |
| `0x080300C0` | Buu's Fury ARM entry |
| `0x08800000` | GT image base |
| `0x088000C0` | GT ARM entry |

---

## 5. Algorithm

### 5.1 Key-mask encoding

The tables store the GBA `KEYINPUT` bits **active-high**, one `u16` per
press:

| Button | Mask |
|---|---:|
| A | `0x0001` |
| B | `0x0002` |
| Select | `0x0004` |
| Start | `0x0008` |
| Right (d-pad) | `0x0010` |
| Left (d-pad) | `0x0020` |
| Up (d-pad) | `0x0040` |
| Down (d-pad) | `0x0080` |
| R (shoulder) | `0x0100` |
| L (shoulder) | `0x0200` |

Notation used in this report: `Up/Down/Left/Right` are **d-pad**
directions; `Lb/Rb` are the **L/R shoulder** buttons.

The recorder stores the **press edge**, so holding a button produces exactly
one entry; pressing two buttons in the same frame produces one combined entry
and will not satisfy a two-entry expectation.

### 5.2 Matching

Every frame, the active handler calls
`seq_match(0x030040D8, len, &table[offset])` for each entry. A match is
evaluated against the **last `len` press events** in chronological order;
the last button of the code must be the most recent press.

`seq_match` returns 0 immediately when the state's "newly pressed this frame"
field (`0x030040DC`) is zero, so a code can only fire on the frame that
contains a new press — in practice the frame of its final button. The ring is
not consumed, but a match cannot re-fire while no new key arrives; a code
therefore applies exactly once per entry and the Zeni entry adds exactly
20,000 (verified: the counter stayed at `0x4E20`, it did not grow per frame).

### 5.3 On match

Both handlers do, in order:

```c
play_sfx(sfx_obj, 0x089D0494, 0x40, 0);   /* the confirmation chime */
... handler-specific effect ...
```

Gameplay handler effects (`0x088047E0`):

| Table off. | Effect as compiled |
|---|---|
| `+0x1C` | `*(u8*)0x0300270C ^= 1` (invincibility toggle) |
| `+0x30` | `*(u8*)0x0300277C ^= 1` (one-hit toggle) |
| `+0x4A` | `*(u16*)(player+0x0A) = *(u16*)(player+0x0C)` (current = max) |
| `+0x5A` | `*(u16*)(player+0x10) = *(u16*)(player+0x12)` |
| `+0x6C` | `*(u16*)(p+0x16)=10; *(u16*)(p+0x18)=0; *(u16*)(p+0x1A)=10; *(u16*)(p+0x1C)=0; *(u16*)(p+0x0A)=100; *(u16*)(p+0x0C)=100; *(u16*)(p+0x0E)=0;` |
| `+0x88` | `*(u16*)(player+0x2A) += 0x04B0` |
| `+0x9A` | `*(u16*)(player+0x28) += 0x04B0` (also `call 0x0835BD4(p,100)`) |
| `+0xAE` | `*(u16*)(player+0x26) += 0x04B0` |

All stat writes use the engine's "write then read back until equal" idiom, so
the emulator's store is retried until the value sticks.

Menu handler effects (`0x0880E1C8`):

| Table off. | Effect |
|---|---|
| `+0x00` | `set_flag_B/A(profile, 5)` |
| `+0x10` | `set_flag_B/A(profile, 6)` |
| `+0x20` | `set_flag_B/A(profile, 7)` |
| `+0x30` | `set_flag_B/A(profile, 8)` |
| `+0x40` | `set_flag_B/A(profile, 9)` |
| `+0x50` | `set_flag_B/A(profile, 5,6,7,8,9)` — all characters |
| `+0x72` | `*(u32*)(profile+0x0C) += 0x00004E20` (20,000 Zeni) |
| `+0x94` | `*(u8*)0x03002874 = 1` |
| `+0xAA` | `set_flag_B/A(profile, 11,12,13,14,15,16)` |

BTW: "`set_flag_B/A`" means the handler calls both setters, i.e. the same id
bit is set in both bitfields at `profile+0x28` and `profile+0x2C`.

---

## 6. Tables

### 6.1 In-game codes — ROM `0x08853244` (file `0x853244`)

| # | Address | Len | Sequence | Public name | Effect (see §5.3) |
|---|---|---:|---|---|---|
| 1 | `0x08853244` | 10 | `U D L R U D L R Lb Rb A B` | Invincibility | toggle `0x0300270C` |
| 2 | `0x08853258` | 13 | `U D D U L R R L Lb Rb Rb Lb B` | Defeat enemies / break objects in one hit | toggle `0x0300277C` |
| 3 | `0x08853272` | 8 | `D U L L U R D B` | Refill health | `player+0x0A = player+0x0C` |
| 4 | `0x08853282` | 9 | `D U R R R L R L B` | Refill energy | `player+0x10 = player+0x12` |
| 5 | `0x08853294` | 14 | `D D D U U U R R R U D R U B` | Max out stats | writes 10/10/100 fields — **observed** |
| 6 | `0x088532B0` | 9 | `R U D R U D R U B` | Temporary super speed | `player+0x2A += 1200` |
| 7 | `0x088532C2` | 10 | `U D U D L L R R U B` | Temporary infinite energy | `player+0x28 += 1200` |
| 8 | `0x088532D6` | 10 | `R U R R U R U L L B` | Temporary infinite strength | `player+0x26 += 1200` |

`0x088532EA` = `0x0000` end marker. `L`/`R` are d-pad left/right
(`0x0020`/`0x0010`); `Lb`/`Rb` are the **shoulder** buttons
(`0x0200`/`0x0100`).

The public names come from the GameFAQs/CheatCC GT lists and are attached by
order; the byte-level effects are from the disassembly.

### 6.2 Title-menu codes — ROM `0x0885A8C8` (file `0x85A8C8`)

| # | Offset | Address | Len | Sequence | Effect |
|---|---|---|---:|---|---|
| 1 | `+0x00` | `0x0885A8C8` | 8 | `Left Right Left Right Up Up Up B` | unlock character id 5 (SS Goku) |
| 2 | `+0x10` | `0x0885A8D8` | 8 | `Left Right Left Right Up Up Down B` | unlock character id 6 (Piccolo) |
| 3 | `+0x20` | `0x0885A8E8` | 8 | `Left Right Left Right Up Down Down B` | unlock character id 7 (SS Vegeta) |
| 4 | `+0x30` | `0x0885A8F8` | 8 | `Left Right Left Right Down Down Down B` | unlock character id 8 (SS4 Goku) |
| 5 | `+0x40` | `0x0885A908` | 8 | `Left Right Left Right Down Down Up B` | unlock character id 9 (5th hidden character) |
| 6 | `+0x50` | `0x0885A918` | 17 | `Down Up Left Left Down Up Left Left Down Up Left Left Up Up Down Up B` | unlock **all** characters (ids 5–9) — **observed** |
| 7 | `+0x72` | `0x0885A93A` | 17 | `Up Down B Left Right B Lb Rb B Up Left Down Lb Rb Lb Rb B` | `profile+0x0C += 0x4E20` (Zeni) — **observed** |
| 8 | `+0x94` | `0x0885A95C` | 11 | `Up Up Down Right Down Right Up Left Left Up B` | `*(u8*)0x03002874 = 1` |
| 9 | `+0xAA` | `0x0885A972` | 17 | `Left Up Up Down Left Up Up Down Left Up Up Down Left Up Up Down B` | unlock ids 11–16 (option entries) |

There is **no terminator inside** this array; the caller passes explicit
lengths. The byte after the last entry (`0x0885A994`) is an IWRAM pointer
(`0x030040D8`), i.e. the next object.

Character ids recovered by observation (the Secrets list is ordered by id):
`5 = SS Goku`, `6 = Piccolo`, `7 = SS Vegeta`, `8 = SS4 Goku`; `9` was
unlocked by code 6 but its row is below the visible window of the captured
screen (public lists call it Super Baby Vegeta).

### 6.3 Literal pools used

| Address | Value | Use |
|---:|---|---|
| `0x08853228` | `0x030040D8` | gameplay handler base (`+0x1C` = table) |
| `0x0885A8AC` | `0x030040D8` | menu handler: input state |
| `0x0885A8B0` | `0x03004874` | menu UI object |
| `0x0885A8C0` | `0x08854E78` | ROM script pointer |
| `0x0885A8C4` | `0x03001CD0` | profile / Secrets object |
| `0x0880E47C` | `0x089D0494` | sound object |
| `0x0880E480` | `0x00004E20` | 20,000 Zeni |

---

## 6b. Enumeration

### 6b.1 The code space

There is **no alphabet, length field, checksum or generator**. The whole
surface is two fixed lookup tables holding **17 button sequences**:

| Table | ROM | Entries | Presses per entry | Entered at |
|---|---:|---:|---|---|
| In-game | `0x08853244` | 8 | 8–14 | any time during gameplay (not paused) |
| Title menu | `0x0885A8C8` | 9 | 8–17 | GT title screen |

Total representable codes = **17**. The matcher compares the last *N* press
events against a stored `u16` array, so a sequence is a code if and only if it
equals one of those arrays exactly (same buttons, same order, same length).
There is no wildcard, no partial credit, and no accepted prefix.

Because `seq_match` also requires a new press on the frame it runs, a code
fires exactly once per entry, on its final button.

### 6b.2 Published vs. novel

Every published GT code (GameFAQs, Cheat Code Central) is present and matches
the ROM byte-for-byte: all 8 in-game codes (the lists are split between the
two sources; "Refill health" is only on Cheat Code Central) and 5 title
character codes.

Four title-menu entries appear in **no published list**:

| # | Offset | Sequence | Effect | Status |
|---|---|---|---|---|
| 6 | `+0x50` | `Down Up Left Left Down Up Left Left Down Up Left Left Up Up Down Up B` | unlock all five characters (bits 5–9 of `0x03001CF8`/`CFC`) | **confirmed**: bits `0x0042041F → 0x004207FF`, Secrets `26 % Unlocked` |
| 7 | `+0x72` | `Up Down B Left Right B Lb Rb B Up Left Down Lb Rb Lb Rb B` | `profile+0x0C += 0x4E20` | **confirmed**: write watchpoint `0x03001CDC` 0 → 0x4E20, Secrets shows `20000 Zeni` |
| 8 | `+0x94` | `Up Up Down Right Down Right Up Left Left Up B` | `*(u8*)0x03002874 = 1` | derived from handler; effect not identified |
| 9 | `+0xAA` | `Left Up Up Down Left Up Up Down Left Up Up Down Left Up Up Down B` | unlock ids 11–16 | derived from handler; rows not checked |

The novelty is structural, not generated: the ROM itself contains these four
sequences and their handlers; no published source documents them.

### 6b.3 Bounds

* **Rejection is observed.** One altered button makes the sequence do nothing:
  no chime, no flag write, no memory change. Verified at the title
  (`… Up Down Up Select` vs `… Up Down Up B`) and in gameplay
  (`… Lb Rb A A` vs `… Lb Rb A B`); see §7.
* **No hidden accept path.** The two handlers call `seq_match` 17 times per
  frame, once per table entry; there is no other comparison against the input
  ring anywhere in either half.
* **No other code system.** `strings` finds no password/debug text; the only
  key-mask arrays in the 16 MiB file are the two tables above.
* **Buu's Fury negative is bounded.** Its three front-end menus, both file
  slots and all five pause tabs (Status, Inventory, Equip, Options, Journal)
  were walked: no code field, no debug page. A scan for any run of ≥6
  key-mask `u16`s finds only graphics data (`0x0001/0x0100` patterns). The
  one published input cheat ("Perfect Fusion", `Up B Left Down A`) exists in
  no contiguous `u16`, byte, active-low or nibble-packed form, so it is not a
  table-driven code in this build (see §8).

---

## 7. Validation evidence

### Observed (mGBA 0.10.5, screenshots retained in the session work dir)

1. **Menu code → character unlock, single:** entered
   `Left Right Left Right Up Up Up B` then `Left Right Left Right Up Up Down B`
   at the GT title menu. Secrets screen showed `10 % Unlocked`, with
   `SS Goku` and `Piccolo` added as character rows (`g19_secrets3.png`).
2. **Menu master code:** entered
   `Down Up Left Left Down Up Left Left Down Up Left Left Up Up Down Up B`,
   opened Secrets: `26 % Unlocked`, rows `SS Goku`, `Piccolo`,
   `SS Vegeta`, `SS4 Goku` all unlocked (`d09_secrets.png`).
3. **In-game max-stats code:** in Story Mode on Imegga, entered
   `Down×3 Up×3 Right×3 Up Down Right Up B`; Pause → View Stats changed
   from Health 6/10, Strength 6/10, Power 3/10 to all three bars full
   (`p01_stats.png` before, `p04_stats_after.png` after).
4. **Handler hit:** with a GDB watchpoint on `0x03001CF8`, entering
   `Left Right Left Right Up Up Down B` produced a store at PC `0x088035E0` (inside
   `set_flag_B`) with old `0x0042041F` → new `0x0042045F` (bit 6), returned
   to `0x0880E237` — exactly the menu entry `+0x10` handler.
5. **Matcher hit:** a read watchpoint on `0x0885A8D8` fired at PC
   `0x08835030` (inside `seq_match`) with `r2=0x0885A8D8`,
   `r0=0x030040D8`, `r14=0x0880E21B` (menu entry `+0x10` call site).
6. **Input recorder:** a write watchpoint on `0x030040D8` showed head
   incrementing 1→17 for a 17-press sequence, storing the expected masks
   (`0x40,0x80,0x02,0x200,0x100,0x02,0x200,0x100,0x02,0x40,0x20,0x80,
   0x200,0x100,0x200,0x100,0x02`) — confirming order, encoding and that B
   in mid-sequence does **not** clear the ring.
7. **Menu inventory of both halves** (screenshots): launcher
   (`m00_shell.png`); GT menu, Secrets, Options
   (`g04_menu.png`, `d09_secrets.png`, `g05_secrets.png`); GT Story Mode,
   Star Map, in-game pause `Continue/View Stats/Exit`
   (`f04_storymode.png`, `f10.png`, `p00_pause.png`); Buu's Fury title,
   front-end options, Select Game (`m04_after.png`, `m06_options.png`,
   `m14_filesel.png`); Buu's Fury pause tabs Status / Inventory / Equip /
   Options / Journal (`b07_pause.png`, `b16_inv.png`, `b09_rr.png`,
   `b14_options.png`, `b13.png`). No code-entry field, password prompt, or
   debug item appears anywhere.

8. **Title rejection (wrong button).** The master-unlock code with the final
   `B` replaced by `Select` was entered key-by-key at the title. A write
   watchpoint on the input head recorded all 17 presses
   (head 1 → 18), and:
   * the chime breakpoint at `0x0880E306` was **never hit**;
   * the watchpoints on `0x03001CF8` / `0x03001CFC` were **never hit**;
   * savestate-parsed RAM is byte-identical before and after:
     `0x03001CF8 = 0x0042041F 0x0042041F 0x012D2D2D`, `0x03001CFC` likewise
     (character bits 5–9 clear);
   * the screen only shows the menu cursor moved (`t03_reject_after.png`).

9. **Title acceptance (positive control).** The same instance/method with the
   correct final `B`: breakpoint **hit** at `0x0880E306`
   (`r0=0x03004E38, r1=0x089D0494, r2=0x40`, return `0x0880E2FB`), and the
   profile became `0x004207FF` (`0x0042041F | 0x3E0`, all five character
   bits). This proves the chime address and the watchpoint setup detect a real
   match, so the silence in (8) is a true rejection.

10. **Gameplay rejection (wrong button).** In gameplay, the invincibility code
    with the final `B` replaced by `A` (`… Lb Rb A A`):
    * no breakpoint at the chime `0x08804828`;
    * no write to `0x0300270C`;
    * savestate-parsed flag before and after: `0x0300270C = 0x00`,
      `0x0300277C = 0x00`;
    * input head advanced (29), so the presses did reach the recorder.

11. **Gameplay acceptance (positive control).** Correct code `… Lb Rb A B`:
    breakpoint hit at `0x08804828` (return `0x0880481B`), then a write hit on
    `0x0300270C` with old `0x00` → new `0x01` at PC `0x08804838`.

12. **Zeni code confirmed.** Correct 17-press sequence
    (`Up Down B Left Right B Lb Rb B Up Left Down Lb Rb Lb Rb B`):
    * breakpoint at the handler's post-chime instruction `0x0880E3A2` **hit**;
    * write watchpoint on `0x03001CDC` **hit**: old `0x00000000` →
      new `0x00004E20` (20,000), PC `0x0880E3B2`;
    * live RAM after the code: `0x03001CDC = 0x00004E20` (exactly once — the
      value did not grow per frame);
    * the Secrets screen then shows `20000 Zeni` (`t21.png`).
    * Failure mode found: entering shoulder `L/R` at table positions 4–5
      instead of **d-pad** `Left/Right` silently rejects the code. This is
      why an earlier pass reported it as unobserved.

13. **Persistence: not persistent.** After the master unlock
    (`0x004207FF`) the game was taken through Story Mode → Start New Game →
    Imegga → Pause → Exit → title:
    * on starting Story Mode the profile was rewritten to `0x0042041F`
      (unlock bits cleared) — parsed from a savestate at the first cutscene;
    * the SRAM save block at `.sav` offset `0x1C14` (magic `DBGT`) still reads
      `+0x28 = 0x0042041F`, `+0x0C = 0` (Zeni); the `.sav` mtime never changed
      during the session and was still unchanged after the emulator exited
      (so the game never wrote SRAM in this flow);
    * after exiting to the title, RAM was again `0x0042041F`.
    Conclusion: the codes write the **live RAM profile only**; the save path
    re-initialises that profile from SRAM when Story Mode starts, so the
    values are not written back and do not survive a reset.

### Derived (instruction-level, not exercised end-to-end)

* Exact effects in §5.3 for the seven other in-game codes and for menu
  entries `+0x94`/`+0xAA`: each effect is a straight-line sequence of
  loads/stores following the `seq_match` return, disassembled with
  `arm-none-eabi-objdump -M force-thumb`.
* Sound `0x40` is the per-code confirmation chime (now also observed as a
  hit for two entries).

### Inferred

* Character id 9 is the fifth hidden character shown in the Secrets list;
  the public name "Super Baby Vegeta" is attached from the published lists,
  not from a captured name row.
* Profile bits 11–16 (menu code `+0xAA`) correspond to the ten "Options"
  shop rows (portrait/music/etc.) visible in the Secrets list at
  1000–8000 Zeni; the row-to-bit mapping was not exercised.

---

## 8. Unknowns

Only items that remain genuinely unproven are listed. The former unknowns
"Zeni code not observed" and "unlock persistence" are now answered in §7
(items 12 and 13).

* **Menu entries `+0x94` and `+0xAA`.** Their handlers are known
  (`0x03002874 = 1`; unlock bits 11–16) but no visible effect was exercised,
  so what those bits unlock in the Secrets list is unproven. Entry `+0x94`
  in particular writes a flag whose readers were not traced.
* **Buu's Fury "Perfect Fusion".** `Up, B, Left, Down, A` is the only
  in-game input cheat published for the first game. No contiguous `u16`,
  byte, active-low, or nibble-packed copy of that sequence exists anywhere
  in the 16 MiB file, and the Buu's Fury half has no table of key masks
  (its apparent mask runs are `0x0001/0x0100` graphics data — a bounded
  negative, not a missing scan). The code is therefore either implemented
  with immediates inside the fusion minigame or is not present in this
  compilation. Not confirmed either way.
* **Menu item `????`.** A locked GT main-menu row; its unlock condition was
  not identified.
* **Profile re-initialisation points.** Starting Story Mode is observed to
  reset the profile from SRAM. Whether other screens (Options, Multiplayer,
  a stage completion) also do so was not mapped; the save that would write
  the profile back was never observed in the tested flow.
* **Secrets denominator.** The percentage suggests 19 entries
  (5/19 = 26 %), inferred from the displayed values, not from the counter
  code.

---

## 9. Tooling

* `mgba` 0.10.5 (SDL) under `Xvfb :107` + `openbox`; `xdotool` for input;
  `scrot` + ImageMagick `convert` for 720×480 viewport captures.
* mGBA's built-in CLI debugger (`mgba -d`) driven through a FIFO, with
  `b`, `delete`, `watch/w`, `watch/r`, `listb`, `listw` and `x/N`.
  Practical caveat: the debugger reads stdin only while stopped, and it is
  easy to desynchronise it with commands sent while the game runs; the
  reliable pattern is one `c` per stop, and using **savestates for RAM
  readback** rather than debugger `x/` commands.
* Savestate RAM extraction: mGBA `.ssN` files are PNGs whose `gbAs` chunk is
  a zlib stream of the full state. Decompressed, **IWRAM is at file offset
  `0x19000`**, so `0x03000000 + x` is read at `0x19000 + x` (e.g. profile
  `0x03001CD0` at `0x1ACD0`). This gives exact before/after memory images
  without the debugger.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000
  -M force-thumb` for every listed disassembly.
* Python 3 scripts (kept in the session work dir):
  * `logo_scan2.py` — 156-byte Nintendo-logo scan → three GBA headers.
  * `findcodes.py` — searches published code sequences as `u16` mask arrays.
  * `bldscan2.py` — full 25-bit Thumb `BL` decoder (J1/J2 aware) to find all
    17 call sites of `seq_match`.
  * `scanrefs.py` — Capstone PC-relative `LDR` literal scan for references
    into the two tables.
  * `state.py` — PNG `gbAs`/zlib savestate reader; `rd8/16/32` for IWRAM.
  * `dbg.py` — FIFO driver for the mGBA CLI debugger.

No ROM, extracted graphics, audio, or text is redistributed with this
report; only addresses, hashes, the 10-bit key masks, and observed
screenshots described in text.
