# Castlevania: Aria of Sorrow (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Castlevania: Aria of Sorrow/Castlevania: Aria of Sorrow.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| MD5 | `e7470df4d241f73060d14437011b90ce` |
| SHA-1 | `abd71fe01ebb201bcc133074db1dd8c5253776c7` |
| SHA-256 | `910f88d3701e6c9f99c0d63660c14c61d8b79b0c17bfd7b35a15185be36430a5` |
| Header title | `CASTLEVANIA2` |
| Game code | `A2CE` (US/EU) |
| Maker | `A4` |
| Software version | `0x00` |
| Entry word | `0xEA00002E` — stock ARM `b 0x080000C0` |
| Header checksum (0xBE) | `0x0000` (normal artefact of a rebuilt header) |
| Complement byte (0xBD) | `0x84` |
| Nintendo logo | Intact at `0x00000004` (only header in the file) |
| Cracktro / trainer | None. Entry word, logo and first 4 KiB are stock. |

**Header complement note.** The standard complement formula
`0x100 - (sum of 0xA0..0xBC)` gives `0x9D`, but the byte is `0x84`. This is
**not** a patch: the same `0x19` offset was measured on **all 891** ROMs in
this collection (histogram: `{231: 891}` for `stored - calc mod 256`), so it
is a property of the collection's dumps, not of this game. The header checksum
field is `0x0000`, which the guide notes is the normal artefact of a rebuilt
header.

## 2. Executive summary

The only in-game, developer-intended cheat system in this ROM is the
**name-entry screen**. It accepts **exactly three** names:

| Name | Effect | RAM proof |
|---|---|---|
| `JULIUS` | Start a new game as Julius Belmont | byte `0x02013266` = 1 |
| `NOUSE` | "Don't Use Items" | bit 20 (`0x00100000`) of `0x02000344` |
| `NOSOUL` | "Don't Use Souls" | bit 21 (`0x00200000`) of `0x02000344` |

All three are gated by a single "game completed" flag, bit 0 of the word at
`0x02000060`. In a fresh game that bit is 0 and the cheat comparison is
skipped entirely; it is set by the game-complete routine at `0x080137FC`
(which also saves it to save slot 6). This matches the published requirement
"beat the game with the good ending first".

A **debug menu** exists in this ROM (game state 20, code at `0x08038A38` /
`0x08038D38`, title string `DEBUG MODE --usr04531--`). It is reachable by
forcing the game state to 20 and it responds to the D-pad (the cursor byte at
`0x02025551` advances), but no in-game trigger was found and its text does not
render correctly from the name-entry screen.

A **sound test** exists as text (`BGM`, `VOICE`, `EXIT` in the text bank) and
as state-machine code, but its trigger was not found in this session.

**Tactics mode does not exist in this ROM** — the string `TACTICS` is absent,
and no code references it. (It is a feature of other Castlevania titles /
ports; the published lists that mention it are mixing versions.)

No button-code cheat, no password screen, no GameShark-style code and no
minigame flag was found. The name-entry field is a real validator (it is
compared against a table and writes mode flags), not a label field.

## 3. How to reproduce

Environment used:

* mGBA 0.10.5 (`/usr/games/mgba`), SDL frontend.
* `Xvfb :234 -screen 0 1024x768x24`, `DISPLAY=:234 openbox`.
* `SDL_AUDIODRIVER=dummy`.
* Default mGBA SDL keymap: **A = `x`**, **B = `z`**, **L = `a`**, **R = `s`**,
  **Start = `Return`**, **Select = `BackSpace`**, D-pad = arrow keys.
*Savestate slots: `Shift+F1..F10` save, `F1..F10` load.

Menu path to the cheat surface:

1. Boot. Press Start repeatedly to skip the opening cinematic.
2. Title screen: `GAME START` / `SOUL TRADE`. Choose **GAME START**.
3. `Select Data`: choose slot 1 (`NEW GAME`).
4. `Select the Difficulty Level`: `NORMAL` or `HARD` (a normal game option,
   not a cheat).
5. `Name Entry`: a 9x4 keyboard. Type the name and press **OK**.

Name-entry keyboard layout (cursor index = row*9 + col, character value =
index + 2):

```
A B C D E F G H I      ( 0.. 8)
J K L M N O P Q R      ( 9..17)
S T U V W X Y Z @      (18..26)
. - ' !  ☠  ✝  _ DEL OK   (27..35, index 33 is an empty cell)
```

Because the cheats are gated by the "game completed" bit, a fresh game will
**not** trigger them. To exercise them in the emulator, set the gate byte and
the name buffer with the debugger and press OK (this is test-harness setup,
not a cheat code):

```
w/4 0x02000060 0x00000001      ; gate = game-completed
w/1 0x02000020 0x0b            ; J
w/1 0x02000021 0x16            ; U
w/1 0x02000022 0x0d            ; L
w/1 0x02000023 0x0a            ; I
w/1 0x02000024 0x16            ; U
w/1 0x02000025 0x14            ; S
w/1 0x02000026 0x00
w/1 0x02000027 0x00
w/1 0x020004ef 0x00            ; [state+11] must be 0
; move cursor to OK (Down x3, Right x8) and press A
```

Observed result for `JULIUS`: the new game starts as **Julius Belmont**
(red/brown outfit, long hair, cross weapon, HP 800 instead of Soma's 400).
Observed result for `NOUSE` / `NOSOUL`: the corresponding mode bit is set.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x080000C0` | ROM entry (ARM) |
| `0x08000500` | Main state dispatcher (reads game state byte at `0x02000010`) |
| `0x08000524` | State jump table (21 entries, states 0..20) |
| `0x08004A48` | State-2 handler (name entry), sub-state machine |
| `0x08004A84` | Name-entry sub-state jump table |
| `0x08005268` | Name-entry sub-state 9 handler (input + OK) |
| `0x080083C8` | **Name confirmation / cheat validator** |
| `0x080E0DCC` | Cheat table 1 = `JULIUS` |
| `0x080E0DD4` | Cheat table 3 = `NOUSE` |
| `0x080E0DDC` | Cheat table 2 = `NOSOUL` |
| `0x084F0D84` | Default name table = `SOMA` (used when 8 valid chars are typed) |
| `0x080137FC` | Game-complete routine: sets bits 0/1 of `0x02000060`, saves slot 6 |
| `0x08038A38` | Debug-menu state machine |
| `0x08038D38` | Debug-menu init |
| `0x080E281C` | Debug event table (18 entries of `{u32 name_ptr, u32 id}`) |
| `0x080E28AC` | Debug title string `DEBUG MODE --usr04531--` |
| `0x02000000` | Global base pointer (stored at `0x084F0B14`) |
| `0x02000010` | Game state byte |
| `0x02000011` | Name-entry sub-state byte |
| `0x02000012` | Debug-menu sub-state byte |
| `0x02000018` | Joypad state word (bit 3 = A) |
| `0x02000020` | **Name buffer** (8 bytes) |
| `0x02000060` | Mode/flag word; **bit 0 = cheat gate ("game completed")** |
| `0x02000094` | Confirmed name (8 bytes, copied from `0x02000020`) |
| `0x02000344` | Mode bits; bit 20 = NOUSE, bit 21 = NOSOUL |
| `0x020004E4` | Name-entry state struct |
| `0x020004E4+21` = `0x020004F9` | Keyboard cursor index |
| `0x020004E4+23` = `0x020004FB` | Name length |
| `0x020004E4+11` = `0x020004EF` | Must be 0 for the cheat check to run |
| `0x02013266` | **Julius mode flag** (set to 1 by `JULIUS`) |
| `0x02025550` | Debug-menu state |
| `0x02025551` | Debug-menu cursor/selection |

## 5. Algorithm

Name-entry confirmation (`0x080083C8`, OK path at `0x080084E2`):

```
copy 8 bytes from name buffer (0x02000020) to 0x02000094

; the name is copied verbatim; the 8th byte is forced to 0 only AFTER the check
if (all 8 bytes are valid character codes 2..34):
        overwrite the buffer with the default name "SOMA"   ; 0x084F0D84

if ( *(u32*)0x02000060 & 1 ) and ( byte[0x020004EF] == 0 ):
        if name[0..7] == table_JULIUS:   *(u8*)0x02013266 = 1;        sound 0x1E5
        elif name[0..7] == table_NOSOUL: *(u32*)0x02000344 |= 0x200000; sound 0x199
        elif name[0..7] == table_NOUSE:  *(u32*)0x02000344 |= 0x100000; sound 0x1B5
return 1   ; name accepted
```

The comparison is a **byte-exact 8-byte compare** (`ldrb`/`cmp` loop) against
three contiguous 8-byte records. There is no checksum, no bit packing and no
case folding. The input alphabet is the 34 on-screen symbols; the stored
character value is `keyboard_index + 2` (`A`=2 … `Z`=27, `@`=28, `.`=29,
`-`=30, `'`=31, `!`=32, skull=33, cross=34).

The cheat gate is set by `0x080137FC`:

```
*(u32*)0x02000060 |= 3;          // bits 0 and 1
write 4 bytes at 0x02000060 to save slot 6
```

## 6. Tables

Cheat name records (contiguous, 8 bytes each, at `0x080E0DCC`):

| ROM address | Bytes | Text |
|---|---|---|
| `0x080E0DCC` | `0b 16 0d 0a 16 14 00 00` | `JULIUS` |
| `0x080E0DD4` | `0f 10 16 14 06 00 00 00` | `NOUSE` |
| `0x080E0DDC` | `0f 10 14 10 16 0d 00 00` | `NOSOUL` |

Default name record at `0x084F0D84`: `14 10 0e 02 00 00 00 00` = `SOMA`.

Debug event table at `0x080E281C` (18 entries, `{u32 name_ptr, u32 id}`),
pointing at the strings at `0x080E26B0`..`0x080E2804`:
`EVENT02:GRA`, `EVENT03:YOKO`, `EVENT04:JB`, `EVENT05:GRA :HYOUHEN`,
`EVENT06:YOKO:TSUISEKI`, `EVENT07:YOKO:SANGEKI`, `08:JB:KIOKU`,
`EVENT09:GRA :VS GRAHAM`, `EVENT10:JB :VS BELMONDO`, `EVENT11: :VS CHAOS`,
`EVENT12:ENDING_BAD`, `EVENT13:ENDING_TRUE`, `EVENT14:SYOUNIN`,
`EVENT16:YOKO HINSHI`, `EVENTJB:ENDING_BELMONDO`, `EVENT09_05:VS GRAHAM2`,
`EVENTED:ENDING CHAOS`.

## 6b. Enumeration

**Space definition.** The name field is 8 bytes. The on-screen alphabet has
**34 symbols**; the character value is `index + 2`, so a byte can only hold
2..34 when typed. The comparison is a byte-exact 8-byte equality against three
fixed records. Therefore the accepted set is **exactly the three table
entries**, i.e. **3 representable accepted inputs** out of the 34^8 ≈ 1.78e12
byte strings the field could hold. There is no checksum, so there are no
near-miss aliases and no unused bits to exploit.

**Novel / unpublished code.** None exists in this system: the accepted set is
*identical* to the published list (GameFAQs, IGN, GameRevolution, Castlevania
Crypt all list exactly `JULIUS`, `NOUSE`, `NOSOUL`). Because the validator is a
closed 3-entry equality table with no algebraic structure, no value outside
that list can be accepted. This is stated as a proved negative, not as an
untested gap: the three records were read out of the ROM, the comparison loop
was disassembled (`0x08008540`..`0x080085FA`), and the gate was exercised
dynamically (below).

**Bounds proven by rejection (in-emulator, RAM-verified).** With the gate set
and the same code path, the following were entered through the real name-entry
OK handler:

| Input | `0x02013266` | `0x02000344` | Result |
|---|---|---|---|
| `JULIUS` | `00000001` | `00000000` | **accepted** (Julius mode) |
| `JULIUSX` | `00000000` | `00000000` | rejected (7th byte non-zero) |
| `JULIUS@` | `00000000` | `00000000` | rejected (7th byte non-zero) |

This proves the 7th byte must be the NUL terminator and that the field is a
real validator (a one-character difference is rejected).

**Gate behaviour.** With the gate cleared (`0x02000060 = 0`) the same name
`JULIUS` does **not** set `0x02013266`; the comparison is skipped. With the
gate set, it does. This isolates the gate as the only additional condition.

**Debug menu.** Game state 20 (`0x02000010 = 0x14`) dispatches to the debug
state machine `0x08038A38`. Observed: the debug state byte `0x02025550`
becomes 1, the selection byte `0x02025551` advances from 0 to 3 after three
D-pad Down presses, and the screen shows the debug overlay (green border). The
text is garbled / absent because the overlay is drawn on top of the name-entry
screen, which has not loaded the debug font/palette. No in-game trigger for
state 20 was found.

**Sound test.** The text bank contains `BGM`, `VOICE`, `EXIT` and state-machine
handlers exist for states 17/18 (`0x08035930`, `0x08036670`). The published
trigger is "beat the game with the good ending"; no trigger was located in
this session.

**Tactics mode.** Not present. `TACTICS` does not occur anywhere in the ROM
(ASCII, `+0x20`, or UTF-16), and no handler references such a string.

## 7. Validation evidence

| Claim | Evidence | Type |
|---|---|---|
| ROM is stock, no cracktro/trainer | entry `0xEA00002E`, logo intact, 8 MiB | Observed |
| Header complement `0x19` offset | measured on 891/891 collection ROMs | Observed |
| Name buffer at `0x02000020`, 8 bytes | debugger reads after typing | Observed |
| Character encoding = keyboard index + 2 | `0x08008416` (`adds r1, #2`) | Derived |
| Cheat tables are `JULIUS`/`NOUSE`/`NOSOUL` | bytes at `0x080E0DCC`/`D4`/`DC` | Observed |
| Cheat gate is bit 0 of `0x02000060` | `0x08008540`..`0x0800854A` | Derived |
| Gate is the game-completed flag | `0x080137FC` sets bits 0/1 and saves slot 6 | Derived |
| `JULIUS` accepted, flag `0x02013266`=1 | debugger read after OK | Observed |
| `JULIUS` starts Julius mode (red outfit, HP 800) | screenshot `shots2/16_julius_effect2.png` | Observed |
| `NOUSE` sets bit 20 of `0x02000344` | debugger read after OK | Observed |
| `NOSOUL` sets bit 21 of `0x02000344` | debugger read after OK | Observed |
| `JULIUSX`, `JULIUS@` rejected | debugger read after OK | Observed |
| Debug menu exists and responds to D-pad | state 20 forced; `0x02025551` 0→3 | Observed |
| No Tactics mode | string scan of the whole ROM | Observed |

Evidence labels: **Observed** = read from the emulator or the ROM bytes;
**Derived** = read from disassembled instructions; **Inferred** = not used for
any claim above.

## 8. Unknowns

* **Debug-menu trigger.** The code and strings exist and the screen responds to
  input when state 20 is forced, but no in-game action that sets the game state
  to 20 was found. It may be unreachable in this build, or reached through a
  path not exercised here.
* **Sound-test trigger.** Text and handlers exist; the trigger (published as
  "beat the game with the good ending") was not located.
* **NOUSE / NOSOUL in-game behaviour.** The flags are proved to be set, but the
  downstream gameplay effect (items/souls disabled) was not played through.
* **Header complement.** The `0x19` offset is uniform across the collection, so
  it is a dumping artefact, but the exact cause was not investigated.
* **Save-slot 6 layout.** `0x080137FC` writes the 4 flag bytes to slot 6; the
  full save structure was not mapped.

## 9. Tooling

Scripts written for this engagement (in `/tmp/opencode/aos/`):

* `drive234.py` — xdotool focus/key/screenshot helper for display `:234`.
* `dbg234.py` — mGBA `-d` pty debugger driver (`cmd`, `pause`, `resume`,
  `key`, `shot`).
* `type.py` — name-entry keyboard driver (9x4 grid, cursor read-back).
* `test_all_cheats.py` — enters each cheat through the real OK handler and
  reads the mode flags.
* `test_reject2.py` — rejection tests (`JULIUS` vs `JULIUSX` / `JULIUS@`).
* `test_julius_effect.py` — starts a game with `JULIUS` and screenshots the
  result.
* `test_dbg_title.py`, `test_dbg_interact.py` — force game state 20 and inspect
  the debug menu.

Static analysis: `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7
raw Thumb scanning, `strings -t x`, `grep -abo`, `xxd`.

No ROM or extracted game asset is redistributed by this report; only offsets,
algorithms, hashes and the analyst's own screenshots are included.
