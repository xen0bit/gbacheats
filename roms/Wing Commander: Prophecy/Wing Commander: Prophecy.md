# Wing Commander: Prophecy (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Wing Commander: Prophecy/Wing Commander: Prophecy.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `WING COMMAND` (`0xA0`–`0xAB`) |
| Game code | `AW9E` (USA/English), maker `20` |
| Version | `0x00` |
| Entry word | `0xEA0F6CF3` → branches to `0x083DB3D4` |
| MD5 | `ff5a6e8ba042d3b581dcc8df9ee28047` |
| SHA-1 | `b9e97e5caca9ab5fb736453af2d3f7954fe875d3` |
| SHA-256 | `38c0662382e50d8feaa7e3e437c888c16f6eeff821a7aa46ce304af547e8beec` |

**Important revision quirk (§16.1):** the header entry does **not** point to the
retail crt0 at `0x080000C0`; it points to `0x083DB3D4`, a scene-release
cracktro ("code by zuerifeld …") that scrolls for a few seconds before the real
game boots. The stock crt0 is still present at `0x080000C0` and the retail
`Press Start` splash is reached after the intro. The cheat system analysed below
belongs to the retail game, not to the cracktro. Header complement byte is
`0x00` and checksum `0x0085` — consistent with a rebuilt scene header.

## 2. Executive summary

This game has **no password/checksum code system and no hidden menu**. Its only
developer-intended cheat surface is a **button-code system** entered at the
retail "Press Start" splash. Exactly **three** 10–12 press sequences exist,
stored as a little ROM table at `0x083CDF34`. Each sequence unlocks one
persistent flag byte in IWRAM; a correct entry also plays sound 25 and forces a
~20-frame white flash.

All three published codes were verified in mGBA **with RAM evidence**: each
sets exactly one of `0x03005DF5/6/7` from `00` to `01`. A whole-ROM scan found
only three code-record tables and the dispatcher has exactly three flag-writing
branches, so the code space is closed at three. Four undocumented inputs
(last-button substitution, truncated prefix, reversed order, random sequence)
were pressed in the emulator and all left every flag at `0`.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap (mGBA SDL default): `A`=`x`, `B`=`z`, `L`=`a`, `R`=`s`,
  `Start`=`Return`, `Select`=`BackSpace`, D-pad = arrow keys.
* Hold each button ~55–70 ms with a similar gap; frames are polled once per
  frame, so very short taps are lost and long holds can double-step.
* Skip the cracktro (a few `Start` presses), wait for the `Wing Commander
  Prophecy` splash with flashing **Press Start**.
* Enter one of the sequences below **before pressing Start**; a white flash
  confirms acceptance. Flashing text is not a menu — no Start/Select needed.

Published codes (verified against ROM literals and in emulator):

| Effect | Sequence |
|---|---|
| God mode (invulnerability) | Up, Down, A, B, Left, Right, L, L, R, R, B, A |
| All missions in Flight History | Up, Up, L, R, Down, Down, A, A, B, A |
| Alien ships in Tactical Database | R, L, A, A, A, B, Up, Left, Down, Right, Up, A |

Ram verification recipe: save a state on the splash, enter a code, save a
second state, extract each PNG's `gbAs` chunk with `zlib.decompress`, and read
raw offset `0x19000 + (addr - 0x03000000)` (IWRAM). Flags live at
`0x03005DF5` (god), `0x03005DF6` (missions), `0x03005DF7` (ships).

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` | code | retail ARM crt0 (not the header entry) |
| `0x083DB3D4` | code | scene cracktro entry (header branch target) |
| `0x083CDEF0` | data | Mission-select sequence, 10 × u16 masks |
| `0x083CDF04` | data | God-mode sequence, 12 × u16 masks |
| `0x083CDF1C` | data | Alien-ship sequence, 12 × u16 masks |
| `0x083CDF34` | data | cheat table, 3 records × 8 bytes, then terminator |
| `0x08028F68` | code | `cheat_check()` — key recorder + comparator + accept path |
| `0x0802900C` | code | inner comparison loop (returns partial/full/mismatch) |
| `0x080290AC` | code | table/buffer initialiser, called once at splash setup |
| `0x0801A788` | code | per-frame caller; gates on screen state and dispatches action ID to flag byte |
| `0x03005E4C` | RAM | screen-state word; validator only runs when `== 2` |
| `0x03005EBC` | RAM | game's key-state copy (active-high button mask) |
| `0x030053F4` | RAM | post-flash frame timer (set to 20, `0x14`) |
| `0x030053F8` | RAM | number of recorded presses (zeroed on full match/mismatch) |
| `0x030053FC` | RAM | 32-entry u16 press-history ring buffer |
| `0x03005400` | RAM | pointer to cheat table |
| `0x03005404` | RAM | 3-byte per-code "already unlocked" flag array |
| `0x03005DF5/6/7` | RAM | persistent God / Mission / Alien flags |

Button masks are **active-high** (`~KEYINPUT & 0x3FF`): `A=0x001, B=0x002,
Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080,
R=0x100, L=0x200`.

## 5. Algorithm

Table layout at `0x083CDF34`, stride **8** bytes (not 12 — a 12-byte stride
would misalign record 1):

```
083CDF34: ptr=0x083CDEF0  len=0x000A  action=0x0000   ; Mission Select
083CDF3C: ptr=0x083CDF04  len=0x000C  action=0x0001   ; God Mode
083CDF44: ptr=0x083CDF1C  len=0x000C  action=0x0002   ; Alien Ships
083CDF4C: ptr=0x00000000  len=0x0000  action=0xFFFF   ; terminator
```

Pseudocode of `cheat_check()` (`0x08028F68`), reconstructed from Thumb
disassembly and Ghidra decompilation:

```
if screen_state(0x03005E4C) != 2: return -1              # caller-side gate
if key_mask(0x03005EBC) & 0x3FF == 0: return -1          # no new press
n = ++press_count (0x030053F8)
press_history[n*2] = key_mask                            # 32-entry ring
for rec in table until rec.ptr == 0:
    if unlocked[rec.index]: continue
    k = 0
    while k < press_count and k < rec.len:
        if press_history[k] != rec.seq[k]: break        # -> mismatch
        k++
    if k != press_count:                                 # partial match
        keep press_count; return -1
    if k == rec.len:                                     # FULL MATCH
        press_count = 0
        unlocked[rec.index] = 1
        play_sound(25) if a global enables it
        DISPCNT |= 0x0080                                # forced blank = white
        timer(0x030053F4) = 20                           # ~20 frames
        return rec.action                                # 0, 1 or 2
    press_count = 0                                      # mismatch resets
return -1
```

Caller `0x0801A788` maps the returned action ID:

```
action 0 -> write 1 to 0x03005DF6   # all missions
action 1 -> write 1 to 0x03005DF5   # god mode
action 2 -> write 1 to 0x03005DF7   # alien ships
other/-1 -> no write
```

Edge semantics (derived): a prefix that still matches keeps the press counter
so the sequence may be completed on later frames; a true mismatch resets it to
zero. Repeating an already-unlocked code is ignored (the `unlocked[]` check).

## 6. Tables

| # | Length | Masks (ROM order) | Action | Flag byte | Published? |
|---|---|---|---|---|---|
| 0 | 10 | `40 40 200 100 80 80 1 1 2 1` | 0 | `0x03005DF6` | yes (mission select) |
| 1 | 12 | `40 80 1 2 20 10 200 200 100 100 2 1` | 1 | `0x03005DF5` | yes (god mode) |
| 2 | 12 | `100 200 1 1 1 2 40 20 80 10 40 1` | 2 | `0x03005DF7` | yes (alien ships) |

Text bank: all UI/menu strings are plain ASCII at file offsets `0x30000`–
`0x30C00` (e.g. `New Game`, `Continue Game`, `Options`, `ENTER CALLSIGN`,
`Flight History`). No password/debug strings exist anywhere in the ROM
(`strings` scan: 51,602 strings; keyword hits for `password`/`cheat`/`debug`
were absent).

## 6b. Enumeration

**Space definition.** This is a table-driven button-code system, not a
checksum/password system. The complete space is: 3 records; sequence lengths
10, 12 and 12; alphabet of 10 GBA buttons (active-high masks listed in §4);
action IDs 0, 1, 2. There is no checksum, no field packing and no generator —
so there is no "novel password" to mint. The §0.2 button-code equivalent
(undocumented combination + full branch enumeration) was performed instead.

**Whole-space proof (closed set).**
1. Table terminator at `0x083CDF4C` has `ptr == 0`; both the initialiser
   (`0x080290AC`, count loop `0x080290CE`) and the validator stop there, so
   exactly **3** sequences can ever be compared.
2. The dispatcher at `0x0801A790`–`0x0801A7C8` has exactly **three** flag-write
   branches (actions 0/1/2); every other return value reaches `0x0801A7D0`
   with no flag write.
3. A ROM-wide scan for `{u32 seq_ptr, u16 len≤32, u16 action<0x100}` records
   whose target is a run of valid button masks returned **exactly the same 3
   records** at `0x83CDF34/3C/44` and no fourth table. A separate scan for u16
   mask runs ≥6 produced only compressed-data false positives.
4. `BL` scan found exactly one call to the validator (`0x0801A796`) and one
   call to the initialiser (`0x0801AA96`): no second, gated cheat path.

**Novel / undocumented combination (pressed in emulator, not in any published
list):** God-mode with the final `A` replaced by `START`
(`U,D,A,B,L,R,L,L,R,R,B,START`) → flags `(0,0,0)`, rejected. This is the
button-system equivalent of a minted code: it exercises an unadvertised
combination and proves the last press is matched, not ignored.

**Bounds proven by rejection** (all from the splash state, flags read from
savestates):

| Input | Result `(god, mission, alien)` |
|---|---|
| God mode as published | `(1, 0, 0)` — accepted |
| Mission select as published | `(0, 1, 0)` — accepted |
| Alien ships as published | `(0, 0, 1)` — accepted |
| All three in sequence | `(1, 1, 1)` — accepted |
| Last button `A` → `START` | `(0, 0, 0)` — rejected |
| First 8 presses of God mode only (partial) | `(0, 0, 0)` — rejected |
| God mode reversed | `(0, 0, 0)` — rejected |
| Random 12-press sequence incl. `Select` | `(0, 0, 0)` — rejected |

**Visual proof:** `flash_0.png`–`flash_2.png` show the full white forced-blank
frame immediately after an accepted entry; `flash_3.png` shows the normal
splash restored (≈3 frames later in the capture), matching the 20-frame timer
and `DISPCNT |= 0x80` in the accept path.

## 7. Validation evidence

* **Observed** (emulator / savestate RAM): splash screen, main menu, Options,
  save-slot and callsign screens walked; all three flags change `00 → 01` on
  correct entry and stay `00` on the four rejected inputs; white flash captured.
* **Derived** (disassembly + Ghidra pseudocode): table structure and terminator,
  mask encoding, comparator return semantics, action→flag mapping, `DISPCNT`
  flash and 20-frame timer, screen-state gate, single call sites.
* **Inferred** (published descriptions + flag semantics): actual gameplay
  effects (invulnerability, all missions unlocked, alien ships in database).
  The flags were observed; a full mission and the two database terminals were
  not played through (see Unknowns).

## 8. Unknowns

* No full mission was flown, so invulnerability, mission availability and the
  alien-ship database entries were not confirmed visually — only their flag
  writes were observed.
* Navigation stopped at the `ENTER CALLSIGN` screen; the Flight History and
  Tactical Database terminals were not reached. The callsign field is ordinary
  name entry (§16.2b): the ROM has no comparison against its buffer.
* A separate 4-entry key-state helper at `0x0802916C` (called from
  `0x080152EA`) contains nibble-pattern checks, but no cheat action branch or
  table was proven reachable from it; it is reported as unknown, not as a code.
* The cracktro is third-party scene content and was excluded from scope.

## 9. Tooling

* mGBA 0.10.5 (`-3`, `-g` tried and abandoned: this build's GDB stub dies on
  I/O-register reads; savestate diffing used instead — §16.13).
* Xvfb `:316` + openbox; `xdotool` XTEST input; `scrot` screenshots.
* `arm-none-eabi-objdump -M force-thumb` for all disassembly; Capstone 5.0.7
  for BL/pointer/xref scans; Ghidra 12.1.4 via REA for pseudocode (session
  closed).
* Local scripts in `/tmp/wingcommander/`: `search_codes.py`,
  `xref.py`, `blscan.py`, `scan_tables.py`, `ssdiff.py`, `press.py`,
  `test_code.py`, `rsp.py`.
* No ROM or copyrighted assets are reproduced in this report; only addresses,
  hashes, button sequences and derived behaviour.

## 10. Legal note

Only findings, addresses, hashes and derived algorithms are published. No ROM
image or extracted game asset is redistributed.
