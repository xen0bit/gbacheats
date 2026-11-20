# The Invincible Iron Man (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Invincible Iron Man.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `THE INVINCIB` |
| Game code | `AIOE` (`AIOE52`) |
| Maker | `52` (Activision) |
| Version | `0x00` |
| MD5 | `4befb747278df729dd6a0dfdf496cbf6` |
| SHA-1 | `2211324e6afc162daaed11dae278f98a456c4311` |
| SHA-256 | `cf7ff9fc0aafaed524b1146a0f5e386612bae053c0f7751164d7aca20d82b02a` |

**Not a clean retail image (§16.1).** Entry word is `0xEA0F96FE`, branching to
`0x083E5C00`, a scene cracktro that displays "EuroAsia 2002 / For pleasure /
not profit" before falling through to the stock crt0. Header complement byte at
`0xBD` is `0x79` (not `0xFF`) and checksum is `0x0000` — the header was rebuilt.
Input and all game code work normally through the cracktro, so no patch/copy was
needed for this analysis. The EEPROM-erase code (below) also matches this
scene-release context.

## 2. Executive summary

There is **no password/code-entry UI** in this game. The cheat surface is a set
of **six button codes** entered on the **title screen ("PRESS START")**. The
engine installs an invisible "cheat menu" listener from `TitleScreenState`'s
init; it records button presses in a 32-entry ring buffer and, on every new
press, compares the recent history against six mask sequences in a ROM table.

Four codes are published (Cheat Happens); **two are not**, and one published
code has the wrong length. The six codes and observed effects:

| # | Table addr | Buttons (chronological) | Length | Effect | Published? |
|---:|---|---|---:|---|---|
| 0 | `0x0804E258` | Select, Up, B, A, Right, Up | 6 | Opens **LEVEL SELECT** screen directly (8 stages: L01–L08, Blizzard, Crimson) | yes ("level select") |
| 1 | `0x0804E278` | Right, Up, Left, A, Right, Select | 6 | Invincibility flag | yes |
| 2 | `0x0804E268` | B, A, Left, Down, Up, Right | 6 | Unlimited chest-plate blasts flag | yes |
| 3 | `0x0804E288` | B, A, B, A, Right | 5 | Undocumented gameplay flag (effect not visually isolated) | **NO — novel** |
| 4 | `0x0804E296` | Up, Down, Left, Right | 4 | Powerful close-range shots flag | published form has an extra B (wrong) |
| 5 | `0x0804E2A2` | Up, Up, Down, Down, Left, Right, Left, Right, B, A, Select, Start | 12 | **Erases EEPROM** ("The contents of the EEPROM have now been erased. Please restart the unit.") then halts | **NO — novel** |

Code #5 is a Konami-style 12-press debug/reset code that has no published
description. Executing it destroys the save — treat it as destructive.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, scale 3.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, Select=`BackSpace`, Start=`Return`,
  D-pad = arrow keys.
* Boot to "PRESS START". Codes must be entered **on this screen** — the matcher
  is installed only by `TitleScreenState`. Press buttons one at a time with a
  full release between (≈120–150 ms hold, ≈180–220 ms gap); simultaneous presses
  produce a combined mask that cannot match.
* Set a breakpoint at Thumb `0x0803A718` (mGBA CLI debugger: `b/t 0x0803A718`).
  Every accepted code stops there with `r1` = code index (0–5) and `r3` =
  `sequence_pointer + 2`. This is a clean accept/reject oracle.
* Code #0 → screenshot `eff0a.png` (level select). Code #5 → screenshot `cur.png`
  (EEPROM erase). Code #3 → breakpoint capture `status` with `r1=3`.

## 4. Address map

| Address (ROM) | Meaning |
|---|---|
| `0x08000000` | Patched entry branch to cracktro `0x083E5C00` |
| `0x08001FE5` | `TitleScreenState` init; BL to `0x0801172C` at `0x08001FEE` |
| `0x0801172C` | Builds the six code listeners; stores them at menu+`0x28` |
| `0x08011850` | Pointer block: six code-record pointers at `0x08011854`–`0x08011868` |
| `0x0803A578` | Registers one code: reads `{u16 first, seq..., 0xFFFF}`, writes 12-byte object `{u16 first, u16* seq, u16 len}` |
| `0x0803A5C0` | Per-frame matcher (32-entry ring buffer at menu+`0x30`, index at menu+`0x44`) |
| `0x0803A718` | Match action, called as `(menu_object, index)` |
| `0x0804E250` | Empty sentinel record (`0000 FFFF`) |
| `0x0804E258`,`268`,`278`,`288`,`296`,`2A2` | The six code records |
| `0x0804E440` | EEPROM-erase message string |
| `0x08012DE0` | EEPROM-erase / halt function (reached from code #5) |
| `0x0804D304`… | State-name table (`TitleScreenState`, `CheatMenuState`, `BonusMenuState`, `LevelSelectMenu_Options`, …) — ASCII state descriptors, not cheat text |
| `0x0200A604`, `0x0200A710` | EWRAM menu objects seen as `r0` at the action breakpoint (flag system rooted at `0x03000E80`) |

Screens walked: cracktro, legal, title, main menu (New Game / Continue / Sound /
Bonus), Bonus (Gallery, Level Select, Credits), Gallery (8 locked images),
Level Select, new-game intro, credits demo. No password/keypad screen exists.

## 5. Algorithm

```
init():                                  # 0x0801172C, from TitleScreenState::init
    menu = alloc_menu()
    for i, ptr in enumerate(code_ptr_table):   # 0x08011854..0x08011868
        obj[i] = { first: u16[ptr+0], seq: ptr+2,
                   len: count_of_u16_until_0xFFFF }
    register matcher on menu

on_new_key_press():                      # 0x0803A5C0
    if key_event_count == 0: return
    ring[menu.ring_index] = current_key_mask     # active-high GBA mask
    menu.ring_index = (menu.ring_index + 1) & 31
    for i, obj in enumerate(code_objects):
        ok = true
        if obj.first != 0 and !(current_key_mask & obj.first): ok = false
        for j in 0 .. obj.len-1:
            if obj.seq[obj.len-1-j] != ring[(menu.ring_index-1-j) & 31]:
                ok = false
        if ok: action(menu, i)            # 0x0803A718
```

The code record format is `{u16 first_mask, u16 buttons..., 0xFFFF}`.
`first_mask` is an optional "current frame must include" gate; all six shipped
records set it to `0`, so the effective code is just the button sequence.
The matcher compares the **last N distinct press events** exactly, so it is
suffix-based (extra presses before a code are harmless) and exact-length.

## 6. Tables

Button masks (active-high, `~KEYINPUT & 0x3FF`):
`A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010 Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200`.

Raw u16 records (little-endian), with `0x0000` first field and `0xFFFF` terminator:

```
0x0804E258: 0000 0004 0040 0002 0001 0010 0040 FFFF   # Sel U B A R U
0x0804E268: 0000 0002 0001 0020 0080 0040 0010 FFFF   # B A L D U R
0x0804E278: 0000 0010 0040 0020 0001 0010 0004 FFFF   # R U L A R Sel
0x0804E288: 0000 0002 0001 0002 0001 0010       FFFF   # B A B A R      (undocumented)
0x0804E296: 0000 0040 0080 0020 0010             FFFF   # U D L R        (short form)
0x0804E2A2: 0000 0040 0040 0080 0080 0020 0010 0020
            0010 0002 0001 0004 0008             FFFF   # U U D D L R L R B A Sel Start (EEPROM erase)
```

Pointer-table order (this is the action index): `0x0804E258 → 0`, `0x0804E278 →
1`, `0x0804E268 → 2`, `0x0804E288 → 3`, `0x0804E296 → 4`, `0x0804E2A2 → 5`.

## 6b. Enumeration

**Space definition.** Alphabet = the 10 GBA buttons (one mask per press event);
six records of lengths {6, 6, 6, 5, 4, 12}. Because the comparator requires
exact equality of each of the last N masks, each record has exactly **one**
spelling — there are no permutations or aliasing within a record. The complete
accepted set is **6 sequences / 6 indices**; there is no checksum field and no
algorithmic generator. `first_mask == 0` for every record, so no extra gate
variants exist. This was proven by enumerating the pointer table (6 entries at
`0x08011854`–`0x08011868`) and by exercising every entry at the action
breakpoint: `r1 = 0, 1, 2, 3, 4, 5` observed for the six sequences above.

**Novel codes (absent from Cheat Happens and every other published list):**
1. `B, A, B, A, Right` (index 3, `0x0804E288`) — accepted on the title screen;
   breakpoint hit with `r1=3`, `r3=0x0804E28A`.
2. `Up, Up, Down, Down, Left, Right, Left, Right, B, A, Select, Start`
   (index 5, `0x0804E2A2`) — accepted with `r1=5`, `r3=0x0804E2A4`; continuing
   produced the in-game EEPROM-erase screen and halt (observed, screenshot
   `cur.png`). This is a destructive hidden reset, not a documented cheat.

**Bounds proven by rejection** (same breakpoint oracle, title screen, same
hold/gap timings):
* `Up, Down, Left, Up` — wrong 4th button for code #4 → **no breakpoint hit**.
* `Up, Down, Left, Right, B` — the *published* 5-button "powerful close-range
  shots" sequence → **no breakpoint hit**. The ROM stores only 4 buttons for
  this code, so the published fifth `B` makes it invalid. This is a
  verified error in the published list (§16.7).

**Published-list verification:** codes #0, #1 and #2 match published button lists
exactly and are present as literals in the ROM. #3 and #5 are unreported. #4's
published form is rejected; the ROM's 4-button form is accepted.

## 7. Validation evidence

* **Observed (emulator):** all six codes stop at `b/t 0x0803A718` with the
  expected index; code #0 opens the LEVEL SELECT screen; code #5 erases EEPROM
  and halts; the two rejected inputs do not stop at the breakpoint.
* **Derived (disassembly):** code-record format, pointer table, ring-buffer
  matcher, exact-length comparison, `first_mask` gate, and the mapping from
  record pointer to action index.
* **Inferred:** effects of codes #1–#4 on gameplay (invincibility / blasts /
  shots / the undocumented flag #3) follow the published descriptions and the
  fact that distinct indices are dispatched, but the in-game visual effect was
  not isolated for each of these four. Code #3's exact gameplay effect is
  therefore **unknown**, not "nothing".

## 8. Unknowns

* Exact gameplay semantics of indices 1–4 were not individually isolated
  (no visible on-screen confirmation while playing a level).
* The generic flag/reference system rooted at `0x03000E80` that the action
  function `0x0803A718` manipulates was not fully reversed; it allocates a
  bitmask-tagged flag object and increments per-menu counters.
* Whether the cracktro altered any game behaviour beyond the header/entry;
  the EEPROM-erase code may be a scene addition rather than a retail debug
  feature. It is present in the shipped image analysed here.

## 9. Tooling

* `strings -t x`, `xxd`, `grep` for recon; Python + Capstone for literal/BL
  scans; `arm-none-eabi-objdump -M force-thumb` for disassembly.
* mGBA 0.10.5 CLI debugger (`-d`) driven over a local PTY bridge
  (`/tmp/opencode/ironman/debug_server.py`, `dbg.py`) for breakpoint oracle.
* `xdotool` XTEST key events with explicit hold/gap timings
  (`/tmp/opencode/ironman/press.py`).
* Savestate `gbAs` zlib extraction (`/tmp/opencode/ironman/ss_extract.py`) per
  guide §16.13 (GDB stub was occupied by another session).
* Screenshots: `/tmp/opencode/ironman/eff0a.png` (level select), `cur.png`
  (EEPROM erase), `gallery2.png`, `bonusmenu.png`, `mainmenu.png`.

No ROM data or copyrighted assets are redistributed by this report.
