# Asteroids / Pong / Yars' Revenge (GBA) — Reverse Engineering Report

Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

Scope: **in-game / developer-intended cheats only** (passwords, button codes,
hidden/debug menus, unlockables). GameShark/CodeBreaker/RAM patches are out of
scope; the one RAM edit in this report is used only as *evidence that a hidden
screen is unreachable*, never presented as a cheat.

Result in one line: **the cartridge has no password system and no button-code
matcher.** It has exactly one developer option space — `GAME TYPE` in the Yars'
Revenge menu, four values `0…3`, whose value `0` is present in the UI and in the
game logic but appears in no published list. The ROM also contains a complete,
**unreachable** Midnight Club: Street Racing front-end (scene 3) left in by the
build; no input can enter it.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Asteroids - Pong - Yars' Revenge/Asteroids - Pong - Yars' Revenge.gba` |
| Size | 4 194 304 bytes (`0x400000`, 32 Mbit) |
| Header title (`0xA0`) | `PONGCOMP` (8 chars, NUL padded) |
| Game code (`0xAC`) | `B64E` (matches the retail USA code for this compilation) |
| Maker code (`0xB0`) | `20` |
| Software version (`0xBC`) | `0` |
| Complement (`0xBD`) | `0x9B` — valid (`-(sum 0xA0..0xBC + 0x19) & 0xFF`) |
| Header checksum (`0xBE`) | `0x0000` (normal for this build; boot is not affected) |
| Entry (`0x00`) | `0xEA00002E` → ARM branch to `0x080000C0` |
| MD5 | `e0d9909f402dac923114675ce44d6b48` |
| SHA-1 | `b437e06d271115df5897ee68caf826bce87d3c2a` |
| SHA-256 | `04335e0ce15ec6114f6ec6893086b7d2aca649e9b0e3b5caf3adb2b25e9d7460` |

ROM addresses below are `0x08000000 + file_offset`. All claims are tied to this
exact hash.

### 1.1 One image, three games (not three concatenated ROMs)

The brief's multi-game check was done first: scanning the whole file for the
156-byte Nintendo logo at logo-relative offset 4 finds **exactly one** header,
at file `0x0`. A structural header scan (byte `0xB2 == 0x96`, printable title at
`0xA0`) returns only the real header; the remaining hits lack a Nintendo logo
and sit inside graphics/tables.
The 4-byte Nintendo logo prefix `24 FF AE 51` occurs once, at `0x4`.

So this is **one GBA program that implements three games as native modules**,
selected through an in-program scene/menu table — not a concatenation of three
ROM images. There is no second `main`, no second crt0, and no second set of
mirrored addresses to map.

### 1.2 ROM layout

| File range | Size | Contents |
|---|---:|---|
| `0x000000`–`0x0142EF` | 82 672 B | All executable code + literal pools (333 functions in Ghidra) |
| `0x0142F0`–`0x164FFF` | `0x150D10` | Zero fill (1.32 MiB) |
| `0x165000`–`0x17BFFF` | 176 KiB | Shell data: menu strings, 8×8 font, marquees, tilemaps, scoreboard tables |
| `0x17C000`–`0x3FFFFF` | 2.56 MiB | Midnight Club: Street Racing asset bank (text, cars, races, bios) + tables appended by this build (`0x28377C` scene table, `0x28618C` graphics, `0x3FF000` pointer/graphics table) |

The Midnight Club leftovers are documented on TCRF (`x1A10A0` onward). This
report goes further: the **menu code that consumes that bank is still linked
and executable** at scene 3 (§2.4).

### 1.3 Boot chain (observed)

1. Reset → ARM at `0x080000C0` (crt0: IRQ handler, stack, memory setup).
2. crt0 literal at header `+0x1C8` = `0x0800020D` → Thumb `main` at `0x0800020C`.
3. `main` initialises the key buffer, builds the scene dispatch pointer, then
   loops: `read keys → scene = byte[0x030010BE] → call scene_table[scene] → wait VBlank`.
4. Scene 0 draws **DSI Games**, then **EC Interactive Games**, then sets scene 1.
5. Scene 1 is the three-logo title (`PRESS START`); Start sets scene 2.
6. Scene 2 is the cabinet carousel; A starts the centred cabinet (scene 4/5/6).

---

## 2. Executive summary

### 2.1 No password / cheat-code system exists

* Zero `PASSWORD` and zero `CHEAT` strings in the whole file; the only
  password-family strings are `PASSCODE IS`, `PASSCODE ENTRY`, `Passcode` and
  `UNLOCK IT` at `0x1A1DBC`, `0x1A1FC8`, `0x1A2080`, `0x1A2068` — all inside
  the dead Midnight Club text bank (§2.4), with no code path from the Atari
  shell to them.
* There is no text-entry field in any reachable screen. The only typing-like
  input is the **high-score initials** screen (3 positions, 40-symbol alphabet).
* The complete input surface is: `A`, `B`, `Start`, `Up`, `Down`, `Left`,
  `Right`. `Select` (bit `0x4`), `L` (`0x200`) and `R` (`0x100`) are **never
  read** anywhere in the `0x0`–`0x142EF` code region (§6b.3).

### 2.2 No button-sequence matcher

All key reads funnel through one per-frame updater at `0x080003E0`, which keeps
only two buffers:

* `0x030010BA` — held keys (active-high, `~REG_KEYINPUT`, idle `0xFC00`)
* `0x030010BC` — keys newly pressed this frame (edge)

There are 33 read sites across 9 functions; every one tests a **single bit** or
the two documented combos `0x22` (Left|B) and `0x11` (Right|A). There is no
sequence index, no history buffer and no table of 4+ button masks anywhere in
the ROM (9 731 u8 runs and 1 168 u16 runs over the mask alphabet exist as
graphics/ASCII noise; the only 4 that are loaded as literals are runs of ASCII
space `0x20`). The published 13-press "Invulnerability" code was therefore both
statically impossible and empirically inert (§6b.6).

### 2.3 The one developer option: `GAME TYPE` 0…3 (Yars' Revenge)

The Yars' Revenge start/pause menu is
`CONTINUE GAME / 1 PLAYER GAME / 2 PLAYER GAME / GAME TYPE n / ABORT GAME`.
The value is a 2-bit field at `0x0300374A`, masked with `& 3`
(`0x080015C0: movs r0,#3; ands r0,r1; strh r0,[r2,#0xA]`), so the complete
space is **0,1,2,3** and nothing else. It is displayed literally (the menu can
and does show `GAME TYPE 0`), default `1`, and wraps `3 → 0`.

Value `0` is not in any published list (GameFAQs documents only the fake
invulnerability code; TCRF documents only unused text). It was selected through
the normal menu and observed in gameplay (§6b.5). The four values are read by
the game logic at `0x08001B34`, `0x08001E2C`, `0x08001FD4`, `0x0800235C`,
`0x08002414`, `0x0800285C`, `0x080028FE`, `0x08002988`, `0x0800317C`;
`0` and non-zero differ at `0x08001FD4`, `≤1` vs `>1` differs at
`0x0800285C/0x080028FE`, `≤2` vs `3` at `0x08001E2C/0x08002414`, and `3` has
its own branch at `0x0800235C`.

The other two games have **no** game-type row: Asteroids uses an Atari-style
`1 PLAYER / 2 PLAYER` select screen (scene 4), Pong a 4-item menu without
`GAME TYPE` (scene 6).

### 2.4 A complete Midnight Club front-end is present but unreachable

Scene 3 of the dispatch table (`0x0800BBE8`) is Midnight Club: Street Racing's
`MAIN SELECT` menu (`Arcade / Career / Extras`), with working `CITY SELECT`
(`New York / London`), `RACE SELECT` (`Cruise / Head to head / Waypoint`),
car preview and `Biographies / Credits`. It renders correctly when the scene
byte is forced (savestate edit) but **no instruction in the ROM writes 3** to
`0x030010BE`; the complete write set is `{0,1,2,idx+4,5}` (§5.3). The only
"exit" in that scene writes 5, i.e. it was rewired to return to the Atari Yars
game. Starting a race from it freezes (screenshot static, input dead) because
the racing engine is not linked. It is a build leftover, not a hidden menu
reachable by the player — there is no input gate, no boot gate, and no scene-3
writer. It is excluded from the cheat result and documented as hidden content.

### 2.5 High scores are volatile

mGBA detects **no save hardware** (`GBASerializedState.savedata.type == 0xFF`,
`.sav` 0 bytes). The 5-entry high-score table and initials live in IWRAM only;
they are lost on reset. This is consistent with the arcade originals and means
there is nothing to unlock persistently.

---

## 3. How to reproduce

### 3.1 Emulator

```bash
Xvfb :145 -screen 0 1024x768x24 &
DISPLAY=:145 openbox &
DISPLAY=:145 SDL_AUDIODRIVER=dummy /usr/games/mgba -3 \
  "Asteroids - Pong - Yars' Revenge.gba" &
DISPLAY=:145 xdotool search --onlyvisible --name mGBA   # window id
```

mGBA 0.10.5. Keymap (defaults, verified by driving every menu): A=`x`,
B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows,
`Tab` (hold) = fast-forward, `Shift+F1` = save state, `F1` = load state.

Two practical notes that cost time here:

* send keys with `xdotool key --clearmodifiers`; a stuck `Shift` from the
  savestate hotkey otherwise makes menus ignore input;
* mGBA pauses on focus loss in this environment — `xdotool windowactivate --sync`
  before each batch.

### 3.2 Menu paths

```
BOOT:  DSI Games -> EC Interactive Games -> title
TITLE: "PRESS START" blinks; Start -> cabinet carousel; other buttons inert
CAROUSEL (scene 2): cabinet index 0..2 at 0x0302A34
        Left/Right = move (clamped, no wrap): 0 = Asteroids, 1 = Yars, 2 = Pong
        A = start centred cabinet -> scene = index + 4
ASTEROIDS (scene 4): "1 PLAYER / 2 PLAYER" -> A -> play
        Start -> pause: CONTINUE GAME / ABORT GAME (2 items)
        game over -> "PUSH START TO CONTINUE" -> Start -> initials -> HIGH SCORES
YARS (scene 5): menu CONTINUE / 1 PLAYER / 2 PLAYER / GAME TYPE n / ABORT (5)
        GAME TYPE: Right or A = +1, Left or B = -1, both mod 4 (0..3)
        Start in game -> same 5-item menu
PONG (scene 6): menu CONTINUE / 1 PLAYER / 2 PLAYER / ABORT (4, no GAME TYPE)
        Start in game -> the same 4-item menu
```

### 3.3 Savestate RAM inspection / patching (used for hidden-screen proof)

mGBA savestates are PNGs with a `gbAs` chunk. The chunk is zlib and expands to
exactly `0x61000` bytes with the documented layout: IWRAM at `0x19000`
(`0x03000000`), EWRAM at `0x21000`.

```python
import struct, zlib
d = open("Asteroids - Pong - Yars' Revenge.ss1","rb").read()
p = d.find(b"gbAs"); ln = struct.unpack(">I", d[p-4:p])[0]
raw = bytearray(zlib.decompress(d[p+4:p+4+ln]))      # 0x61000 bytes
iwram = 0x19000
def get(a): return raw[iwram + (a - 0x03000000)]
def setb(a, v): raw[iwram + (a - 0x03000000)] = v
# rebuild the chunk with a correct CRC, then load with F1
```

Addresses used: `0x030010BE` scene, `0x030010BF` mode,
`0x030010BA/BC` held/edge keys, `0x0302A34` cabinet index,
`0x03003740..0x0300374C` Yars game struct, `0x03000228` Yars menu cursor.

Forcing `scene=3` gives the Midnight Club menu; forcing `scene=4/5/6` with
`mode=0` gives each game's start screen.

### 3.4 Tests actually run

* 48 combinations of `scene ∈ {4,5,6}` × `mode ∈ 0..7`, screenshot each
  (§6b.4).
* Published invulnerability sequence `B A A B A B B A B B A B B` entered on the
  title screen, then Asteroids 1P played 45 s under fast-forward → `GAME OVER`
  (§6b.6).
* `Select` at the title, `L+R` at the title, and `Select` during Asteroids play
  -> no state change (identical screenshots).
* Yars `GAME TYPE` walked `1→2→3→0→1` with the cursor on row 3, then started
  with type 0 and with type 3.

---

## 4. Address map

### 4.1 Code (file offset = address − `0x08000000`)

| Address | Role |
|---|---|
| `0x080000C0` | crt0 (ARM) |
| `0x0800020C` | `main`: init, then scene-dispatch loop |
| `0x080003E0` | key updater: `REG_KEYINPUT @0x04000130` → held + edge |
| `0x080013EC` | Yars' Revenge 5-item menu (CONTINUE/1P/2P/GAME TYPE/ABORT) |
| `0x080015C0` | `GAME TYPE` mask `& 3` and store |
| `0x08001678` | display-mode init used before starting a game |
| `0x080020DC` | Asteroids gameplay step (ship/rocks/shots) |
| `0x08002CDC` | Yars scene (menu mode 7 + game mode 4) |
| `0x08003314` | Pong 4-item menu (uses string bank `0x08166060`) |
| `0x08003C94` | Asteroids `1 PLAYER / 2 PLAYER` selector |
| `0x080046EC` | Pong scene (menu + game over + 2-item overlay) |
| `0x08004B04` | score digit-column draw (7 columns) |
| `0x080049E0` | initials lookup over 40-symbol alphabet at `0x08170568` |
| `0x08004A4C` | decimal score draw |
| `0x08005EB0` | high-score list draw (calls the 5-row setup `0x08005604`) |
| `0x080067D0` | Asteroids scene (start screen, game, 2-item pause) |
| `0x0800AD18` | scene 0: DSI + EC Interactive logos |
| `0x0800B09C` | scene 1: three-logo title, blink, Start |
| `0x0800B5B0` | scene 2: cabinet carousel |
| `0x0800BBE8` | scene 3: **Midnight Club front-end (unreachable)** |
| `0x0800BA9C` | carousel A: `scene = cabinet_index + 4` |
| `0x0800BDCA` | MC menu exit: `scene = 5` (rewired to Yars) |

### 4.2 Data

| Address | Contents |
|---|---|
| `0x0828377C` | scene dispatch table, 7 Thumb pointers (file `0x28377C`) |
| `0x08165FA8` | shell string bank #1: `GAME OVER`, `GAME TYPE %i`, `CONTINUE GAME`, `1 PLAYER GAME`, `2 PLAYER GAME`, `ABORT GAME` |
| `0x08166028` | `GAME OVER`, `PLAYER 1 WINS!`, `PLAYER 2 WINS!` |
| `0x08166060` | string bank #2: `CONTINUE GAME`, `1 PLAYER GAME`, `2 PLAYER GAME`, `ABORT GAME` (Pong menu) |
| `0x08170568` | 40-symbol initials alphabet `._ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789*` |
| `0x08170594` | `CONTINUE GAME`, `ABORT GAME` (2-item overlay) |
| `0x081705BC` | `PUSH START`, `HIGH SCORES`, `PUSH START TO CONTINUE` |
| `0x081A10A0` | start of Midnight Club text bank (TCRF-documented) |
| `0x081A1DBC` | `PASSCODE IS` (dead) |
| `0x081A1FC8` | `PASSCODE ENTRY` (dead) |
| `0x081A1E94` | `PAUSE MENU`, `RESET RACE`, `BACK TO MAIN MENU` (dead) |
| `0x081A2090` | `CAREER OPTIONS`, `VEHICLE SELECT` (dead) |

### 4.3 RAM (IWRAM)

| Address | Role |
|---|---|
| `0x03000228` | Yars menu cursor (0..4) |
| `0x03000364` | Pong menu cursor (0..3) |
| `0x0302A30` | carousel camera position |
| `0x0302A34` | cabinet index (0..2) — scene = value + 4 |
| `0x0300350` | Pong game struct (menu uses `+2` in-progress flag) |
| `0x03003740` | shared game struct: `+0` game id, `+4` started, `+8` game type (copy), `+0xA` game type counter, `+0xC` game-over timer |
| `0x0300374A` | Yars `GAME TYPE` counter (0..3, 2-bit) |
| `0x030010BA` | held keys (`~REG_KEYINPUT`, idle `0xFC00`) |
| `0x030010BC` | newly-pressed keys (edge) |
| `0x030010BE` | **scene** (0..6) |
| `0x030010BF` | **mode** within the scene |

---

## 5. Algorithm

### 5.1 Input pipeline (`0x080003E0`, every frame)

```c
u16 raw   = REG_KEYINPUT;              // 0x04000130, active low
u16 held  = ~raw;                      // bits 0..9 meaningful; idle 0xFC00
u16 edges = held & ~prev_held;         // newly pressed this frame
prev_held = held;
KEY_HELD  = held;                      // 0x030010BA
KEY_EDGE  = edges;                     // 0x030010BC
```

Every consumer uses `KEY_EDGE & mask` for menu actions and `KEY_HELD & mask`
for continuous movement (paddle/joystick). Masks used anywhere:
`0x01 A`, `0x02 B`, `0x08 Start`, `0x10 Right`, `0x20 Left`, `0x40 Up`,
`0x80 Down`, plus `0x11` (Right or A) and `0x22` (Left or B) for the game-type
row. `0x04 Select`, `0x100 R`, `0x200 L` are never tested.

### 5.2 Scene dispatch (`0x0800020C`)

```c
scene_table[7] = { 0x0800AD18, 0x0800B09C, 0x0800B5B0, 0x0800BBE8,
                   0x080067D0, 0x08002CDC, 0x080046EC };
for (;;) {
    read_keys();
    ((void(*)(void))scene_table[*(u8*)0x030010BE])();
    wait_vblank();
}
```

### 5.3 Scene writes (the complete set)

| Site | Value written | When |
|---|---|---|
| `0x080002EC` | `0` | reset/init |
| `0x0800AFFE` | `1` | logo sequence finished |
| `0x0800B388` | `2` | title → carousel (Start) |
| `0x0800BA9C` | `cabinet + 4` | carousel A (cabinet 0..2 → 4..6) |
| `0x08003208` | `1` | Yars scene exit |
| `0x08004754` | `1` | Pong scene exit |
| `0x0800BDCA` | `5` | Midnight Club menu "back" (dead code) |

No writer emits `3`. The Midnight Club scene can only be entered by editing
RAM/savestate.

### 5.4 Yars' Revenge menu (`0x080013EC`)

```c
idx = *(s8*)0x0300228;                     // 0..4, clamped, wraps
Up    -> idx--; if (idx<0) idx=4;
Down  -> idx++; if (idx>4) idx=0;
if (idx == 3) {                            // GAME TYPE row
    if (edge & 0x22) type--;               // Left or B
    if (edge & 0x11) type++;               // Right or A
    type &= 3;                             // 0..3, wraps 3 -> 0
    // value is printed literally by "GAME TYPE %i"
}
if (edge & 0x01) switch (idx) {            // A confirm
    case 0: continue_game(); break;
    case 1: start(1, type); break;
    case 2: start(2, type); break;
    case 4: scene = 1; break;              // abort
}
```

Note the coupling: `A` both advances the game type (when row 3 is selected) and
confirms the other rows. `B` both decrements the game type and does nothing
elsewhere.

### 5.5 Pong menu (`0x08003314`) and Asteroids menu (inside `0x080067D0`)

Pong: identical structure with cursor `0x03000364`, 4 rows (no game type), and
1P/2P immediately start the session. Asteroids: `1 PLAYER / 2 PLAYER` select at
`0x08003C94` before play, and a 2-row `CONTINUE GAME / ABORT GAME` pause overlay
(no game type, no player-count change mid-game).

### 5.6 Midnight Club leftover (scene 3, `0x0800BBE8`)

The MC front-end is a full scene with its own modes. Its menus are data-driven
from the 2.5 MiB bank: `MAIN SELECT` → `CITY SELECT` → `RACE SELECT` → car
preview. Its only external transition writes `scene = 5` (`0x0800BDCA`), the
Yars scene, confirming it was adapted as a dead branch. Forcing a race start
freezes the CPU (static frames, no input response), so the race engine appears
not to be linked (inferred).

---

## 6. Tables

### 6.1 Scenes

| `0x030010BE` | Handler | Screen | Reachable |
|---:|---|---|---|
| 0 | `0x0800AD18` | DSI Games → EC Interactive Games | yes (boot) |
| 1 | `0x0800B09C` | three-logo title, blinking `PRESS START` | yes |
| 2 | `0x0800B5B0` | cabinet carousel (Asteroids/Yars/Pong) | yes |
| 3 | `0x0800BBE8` | Midnight Club `MAIN SELECT` + submenus | **no writer** |
| 4 | `0x080067D0` | Asteroids: 1P/2P select, game, 2-item pause | yes |
| 5 | `0x08002CDC` | Yars: 5-item menu, game | yes |
| 6 | `0x080046EC` | Pong: 4-item menu, game | yes |

### 6.2 Menus and item counts (all observed)

| Screen | Items | Notes |
|---|---:|---|
| Title | 0 (Start only) | A/B/L/R/Select inert |
| Carousel | 3 cabinets | Left/Right clamped 0..2; A starts |
| Asteroids select | 2 (`1 PLAYER`, `2 PLAYER`) | triangle cursor, ©1979 Atari |
| Asteroids pause | 2 (`CONTINUE GAME`, `ABORT GAME`) | no game type |
| Yars menu | 5 | includes `GAME TYPE 0…3` |
| Pong menu | 4 | no game type |
| Game over (Asteroids) | 0 | `GAME OVER` + `PUSH START TO CONTINUE` |
| Initials | 3 positions × 40 symbols | D-pad selects letter, B confirms (on-screen text says so; observed) |
| High scores | 5 rows | score + 3 initials, volatile |
| Midnight Club | Arcade/Career/Extras → submenus | unreachable; race start freezes |

### 6.3 Yars `GAME TYPE` values

| Value | Displayed | Reachable | Behavioural class (derived) |
|---:|---|---|---|
| 0 | `GAME TYPE 0` | Right/A or Left/B from 1 | distinct at `0x08001FD4`; grouped with 1 elsewhere |
| 1 | `GAME TYPE 1` | default | same as 0 except `0x08001FD4` |
| 2 | `GAME TYPE 2` | +1 | `≤2` vs `3` branches differ from 3 |
| 3 | `GAME TYPE 3` | +1 | own branch at `0x0800235C`/`0x080028FE` |

Mask: `& 3` at `0x080015C0`. No value ≥ 4 is representable; pressing Right at
3 wraps to 0 (observed).

### 6.4 Initials alphabet (40 symbols, `0x08170568`)

The table is exactly 40 bytes:

```
index  0     1     2..27            28    29..38        39
byte  '.'   '_'   'A'..'Z'         ' '   '0'..'9'      '*'
```

so the reachable initials space is 40³ = 64 000 names; the value is a
high-score name, not a code. The on-screen instructions around it are drawn
from tile indices, not ASCII (`YOUR SCORE IS ONE OF THE FIVE BEST`,
`PLEASE ENTER YOUR INITIALS`, … are not in any string encoding in the ROM).

### 6.5 Shell strings (complete, ASCII)

`GAME OVER`, `GAME TYPE %i`, `CONTINUE GAME`, `1 PLAYER GAME`,
`2 PLAYER GAME`, `ABORT GAME`, `PLAYER 1 WINS!`, `PLAYER 2 WINS!`,
`PUSH START`, `HIGH SCORES`, `PUSH START TO CONTINUE`, plus the scoreboard
format strings `P%i %8i %3i %3i`, `P%i %8i %3i`. The initials instructions
(`YOUR SCORE IS ONE OF THE FIVE BEST`, `PLEASE ENTER YOUR INITIALS`, …) are
**tile indices, not ASCII**, which is why a string scan alone would miss them.

### 6.6 Published codes — verification status

| Source | Code | Result |
|---|---|---|
| GameFAQs (GBA 929035) | `B A A B A B B A B B A B B` — "Invulnerability at mode selection" | **Rejected.** Entered at the title (the only screen where A/B are inert, since every menu confirms with A), then Asteroids 1P played 45 s fast-forward: ship destroyed, `GAME OVER`, score 280 (`t_after45.png`). No mask table or sequence matcher exists in the ROM (§6b.3). |
| GameFAQs (same page) | `CHEATONX` password + `Select` for level select | **Rejected.** Literal absent (`grep -abo "CHEATONX"` = not found); there is no password field; `Select` is never read; "zone/level select" does not exist in this compilation. |
| GameFAQs glitch | fly behind the Asteroids scoreboard | Not a code (2600/arcade gameplay quirk); out of scope. |
| GameFAQs easter egg | `HSWWSH` in Yars | 2600 in-game trick, not ASCII in this ROM; not verified (§8). |
| Ethereal Games | Action Replay / GameShark codes | Memory patches, out of scope; not usable as in-game input. |
| TCRF | unused Midnight Club text | Confirmed independently; extended here with the executable scene-3 menu. |

---

## 6b. Enumeration

**There is no password/code system, so no code can be minted.** The one
developer option space (`GAME TYPE`) *was* fully enumerated, and every negative
below is a statement about a measured space.

### 6b.1 Space definition

| Surface | Size | Evidence |
|---|---:|---|
| Scenes | 7 entries, **6 reachable** | table at `0x0828377C`; write set §5.3 |
| Modes per scene | 8 (`0..7`) | `0x030010BF` byte; 48-combination sweep §6b.4 |
| Cabinets | 3 (`0..2`) | `0x0302A34`, clamped at `0x0800B9xx` |
| Yars game types | **4 (`0..3`)** | 2-bit mask at `0x080015C0` |
| Menu rows | 5 / 4 / 2 (Yars/Pong/Asteroids pause) | observed + static count |
| Initials | 40³ = 64 000 | alphabet at `0x08170568` |
| Keys read | 7 of 10 (`A,B,Start,←,→,↑,↓`) | 33 read sites; masks §5.1 |
| Button sequences | **none representable** | no table/index; §6b.3 |

### 6b.2 Text space

* `strings -t x -n 4` over the whole file → **24 555** printable runs
  (Python scan; `-n 6` → 13 699).
* Case-insensitive keyword classification (whole file):
  `PASSWORD` 0, `CHEAT` 0, `DEBUG` 0, `HIDDEN` 0, `INVALID` 0,
  `PASSCODE` 3 (`0x1A1DBC`, `0x1A1FC8`, `0x1A2080` — all in the dead MC bank),
  `CODE` 3 (same region), `UNLOCK` 1 (`0x1A2068`, MC menu), `SECRET` 1
  (`0x1A2220`, "SECRETIVE RACER" bio), `MENU` 2, `OPTION` 2, `SELECT` 5 — every
  non-zero hit is at `0x1A1C74…0x1A22D0`, i.e. Midnight Club data.
* The reachable UI vocabulary is the 13 strings of §6.5 plus tile-indexed text
  for the initials screen. There is no `PASSWORD`, `CHEAT`, `DEBUG`, `INVALID`
  or code-entry string anywhere the player can reach.

### 6b.3 Button-code space (whole ROM)

| Scan | Space | Result |
|---|---|---|
| u8 runs over single-bit masks `{1,2,4,8,0x10,0x20,0x40,0x80}`, length ≥4 | 9 731 runs | only 4 run starts are LDR-literal targets (`0x166054`, `0x1705C8`, `0x1A3618`, `0x3E35F8`); all four are runs of ASCII space `0x20` |
| u16 runs over masks `{1…0x200}`, length ≥4 | 1 168 runs | none loaded as a table by code |
| Published sequence (A=1, B=2, both orders) as u8 and u16 | 4 encodings | **0 hits** |
| Multi-button masks tested at a key read (`cmp/ands/tst`) | all 33 sites in 9 functions | only single bits plus `0x22` (Left|B) and `0x11` (Right|A), both documented game-type controls |
| `Select` / `L` / `R` bits | all code | **0 references** |
| Boot-time gate | scene 0 (`0x0800AD18`) | no key read at all |

Consequence: a 13-press cheat cannot be represented, let alone matched. The
published sequence is not in this build.

### 6b.4 Menu / screen space

Every reachable screen was walked and screenshotted: boot logos, title,
carousel ×3, Asteroids 1P/2P select, Asteroids game/pause/game over/initials/
high scores, Yars menu (`GAME TYPE` 0/1/2/3)/game/pause, Pong menu/game/pause.

A forced sweep of `scene ∈ {4,5,6}` × `mode ∈ 0..7` (48 states, each loaded from
a savestate and screenshotted twice) produced only the screens above plus
overlapping-draw artifacts from invalid state combinations — no new menu, no
text field, no debug screen.

### 6b.5 Option space — novel value `GAME TYPE 0`

The complete 2-bit space was enumerated:

```
start 1 -> Right 2 -> Right 3 -> Right 0 -> Right 1 -> Right 2
```

with the cursor on row 3. `GAME TYPE 0` was displayed (`yt3.png`) and then used
to start a 1-player game (`yars0play.png`: HUD reads `P1 0 4`, blue Qotile
zone). `GAME TYPE 3` was started the same way for comparison
(`yars3play.png`). Bounds:

* **Representation bound:** `type &= 3` at `0x080015C0`; `4` cannot be stored.
* **UI bound:** the row wraps `3 → 0`; there is no fifth value.
* **Published-list bound:** no published source lists any `GAME TYPE` value at
  all, so `0` (and 2/3) are absent from every published list.

This is the report's "unpublished combination confirmed in-game" for the only
option system the cartridge has.

### 6b.6 Published-input tests (rejections)

| Test | Exact input | Result |
|---|---|---|
| Invulnerability code | `B A A B A B B A B B A B B` at title, then Start → Left → A → A → 45 s fast-forward | ship destroyed, `GAME OVER` (`t_after45.png`) |
| Same sequence on the Asteroids 1P/2P screen | `B A A …` | the first `A` in the sequence starts the game immediately — the code cannot be entered on any confirming screen; no invulnerability |
| `Select` | title, and during Asteroids play | screen unchanged (identical PNGs) |
| `L + R` | title | screen unchanged |
| `CHEATONX` | literal search | absent from ROM; no entry field |

### 6b.7 Why the negative is conclusive

1. No password/code entry screen exists in any reachable scene (§6b.4).
2. The only text-bearing bank is fully classified; all code words are in the
   dead Midnight Club region (§6b.2).
3. A button code needs a mask table or a sequence index; the ROM has neither,
   and all 33 key reads are single-bit tests (§6b.3).
4. `Select`, `L` and `R` are never read, so gates keyed on them are impossible.
5. The only option field is enumerated to its 2-bit bound and a novel value was
   exercised in-game (§6b.5).
6. The only hidden menu-like screen (scene 3) is proven unreachable by the
   complete scene-write set (§5.3).

---

## 7. Validation evidence

**Observed (emulator screenshots / memory):**

* boot logos, title, carousel (all three cabinets), each game's menu, gameplay,
  pause, game over, initials entry, high-score table;
* `GAME TYPE` values 0,1,2,3 displayed and selected; type 0 and 3 gameplay;
* published invulnerability sequence → death;
* Select/L/R inert;
* savestate RAM values for scene/mode/menu/type (e.g. scene 2 mode 4 at the
  carousel, scene 4 mode 4 at the Asteroids pause, scene 5 mode 7 at the Yars
  menu, scene 6 mode 4 at the Pong pause);
* savestate save-type byte `0xFF` (no save hardware).

**Derived (instruction-level):**

* key pipeline and 33 read sites; mask set; no Select/L/R;
* scene table and the complete scene-write set (no writer of 3);
* `type &= 3` bound and the type-dependent branches;
* `scene = cabinet + 4` mapping;
* 40-symbol initials alphabet and 5-row scoreboard.

**Inferred:**

* behavioural difference of `GAME TYPE 0` vs `1` (stated only where the branch
  at `0x08001FD4` proves *some* difference; exact gameplay effect not isolated);
* the Midnight Club scene being a build leftover (supported by the scene-write
  set and the freeze at race start, but the build history is not in the ROM).

---

## 8. Unknowns

* The exact gameplay effect of each Yars `GAME TYPE` value (0/1/2/3) was not
  isolated; only menu selection, storage and the branch sites are proven.
* The `HSWWSH` 2600 easter egg may be reproduced by the native Yars logic, but
  the initials are tile-rendered and were not triggered/verified here.
* The Midnight Club leftover freezes when a race is started; whether a
  different (unforced) entry point once existed is not knowable from this ROM.
* EU revision (`Zoo Digital`, 5 languages) was not analysed; addresses may
  differ.
* The 4 KiB table at `0x3FF000` and the graphics at `0x28618C` were used by the
  build but not decoded asset-by-asset (not needed for the cheat question).

---

## 9. Tooling

* mGBA 0.10.5 (SDL) under Xvfb `:145` + openbox; `xdotool`, `scrot`,
  ImageMagick `convert`/`montage`; `Tab` fast-forward.
* Python 3 with `capstone` 5.0.7, `keystone` 0.9.2, `zlib` for savestate
  decoding/patching.
* GNU `arm-none-eabi-objdump` 2.44 (`-M force-thumb`) and `strings`.
* Ghidra 12.1.4 via REA (`open_binary` raw-binary, ARM, base `0x08000000`) for
  xrefs and pseudocode; all key claims were re-checked with objdump against the
  bytes.
* Scripts written for this job (in `/tmp/opencode/asteroids`):
  `an.py` (Thumb literal/BL scans), `k2.py` (input), `st.py` (savestate RAM
  read), `sx.py` (savestate rebuild/patch), `sweep.py` (48-scene/mode sweep).

Reproduction artifacts (screenshots) were taken on display `:145`; the durable
artifact is this report plus the exact key sequences in §3.

---

## 10. Legal note

No ROM, extracted graphics, music or game text is redistributed here. Only
hashes, addresses, algorithms and short UI labels needed to identify the
systems are recorded.
