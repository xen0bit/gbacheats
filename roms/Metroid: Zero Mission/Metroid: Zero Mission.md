# Metroid: Zero Mission (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Metroid: Zero Mission.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `ZEROMISSIONE` |
| Game code | `BMXE` (Europe) |
| Maker | `01` (Nintendo) |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock ARM branch — no cracktro patch) |
| Header fixed 0x96 | present at 0xB2 |
| Complement byte | stored `0x1D`; recomputed over 0xA0..0xBC = `0x36` (anomaly, noted; header checksum 0x0000) |
| MD5 | `ebbce58109988b6da61ebb06c7a432d5` |
| SHA-1 | `5de8536afe1f0078ee6fe1089f890e8c7aa0a6e8` |
| SHA-256 | `fc94f65380b65b870a30b9b04b39cca1dc63d6e46a4a373d3904adc0912ebc37` |

**Embedded GBA headers (Nintendo-logo scan, 156-byte logo):** four hits —
`0x000000` `ZEROMISSIONE/BMXE`, `0x754BD0` `ZEROMISSIONE/BMXE`,
`0x7566C4` `ZEROMISSIONE/BMXE`, and **`0x7D8000` `NES METROID` / game code
`0000` / entry `0xEB000033`**. The last is the embedded original-NES-Metroid
multiboot image (unlockable). No appended trainer/cracktro was found; the two
extra BMXE headers are data images, not bootable shells.

**Sibling comparison (Fusion, :318):** this image was analyzed independently.
The GBA engine conventions (Samus Data file screen, OPTIONS layout, font-indexed
text) are the same Nintendo R&D1 family, but no code address is shared/proven
here; the two cheat surfaces found below (button-code table and the NES
multiboot) are specific to this ROM. No cross-ROM address was carried over.

## 2. Executive summary

Zero Mission has **no in-game password entry for the GBA game itself** (it uses
32 KiB SRAM). It has two developer-intended cheat surfaces:

1. **One GBA button code** — at a *completed* file's "Start Game" screen,
   `Up, Left, Right, Down` reveals "New Time Attack". The key-mask table and its
   validator are present and were reversed: table `0x0845F452` =
   `[0x40,0x20,0x10,0x80,0xFFFF]`, validator `0x0807D588`, 30-frame per-press
   window. This is the **only** 4-press mask table in the whole 8 MiB. The gate
   is the completed-file flag (file record `+0x11`); with only an in-progress
   save available, the validator never fired (live breakpoint at
   `0x0807D588` did not hit), so the in-game effect is **proven static, gated
   dynamically**. No GameShark/CodeBreaker code was used or reported as a find.

2. **The NES Metroid password system** inside the unlockable original game
   (multiboot image at `0x087D8000`). The published 24-symbol format was
   reimplemented in Python (`metpass.py`) and **verified against five published
   codes** (checksum + roundtrip). The space is 2^136 accepted codes. Novel
   codes were minted and checksum bounds proven. Entering them on the real
   password screen is gated behind *beating the game once* (Original Metroid
   unlock); that gate was not crossed in this session, so the on-screen entry
   remains labelled **gated**, not "tested".

Hidden "Debug Menu" exists only as **dead/gated code**: the archived m2k2
thread uses a CodeBreaker RAM patch (`730016C4 0080` / `83000BF0 0006`), the
`DEBUG` string at `0x0854D27D` has zero pointers, and Wikitroid requires a
patched ROM/Action Replay. Out of scope (memory-edit code), recorded as a
negative finding.

## 3. How to reproduce

- Emulator: mGBA (SDL), Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, keymap
  A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
- Boot: `mgba -3 <rom>`; press Start at "PRESS START" → **Samus Data** file
  select. With a save present the bottom menu is **COPY / ERASE / OPTIONS**.
- OPTIONS → SOUND toggles speaker/headphones; **METROID FUSION LINK** opens a
  "Linking… Do not turn the power off" screen (requires a Fusion save/cart).
- Pause in-game (Start): map/Samus screen with **SLEEP** (L) and **STATUS** (R).
  SLEEP → "Activate Easy Sleep?" (Yes/No); exit combo **Select + L + R**
  simultaneously (documented in-game).
- Button code (static-proven, progression-gated): reach a completed file's
  Start Game screen and press Up, Left, Right, Down.
- Savestate RAM evidence (§16.13): `.ss1` is a PNG; the `gbAs` chunk is
  zlib-compressed. State layout for this 8 MiB ROM: CPU/header `0x00000`,
  VRAM `0x01000`, IWRAM `0x19000`, EWRAM `0x21000`, SRAM `0x59000`; total
  `0x61000`. `ssdiff.py` parses/diffs it.

## 4. Address map

| Item | ROM / file offset | RAM / notes |
|---|---|---|
| GBA header | `0x000000` | entry `0xEA00002E` |
| Button-code table | file `0x045F452` → `0x0845F452` | u16 masks `[0x40,0x20,0x10,0x80,0xFFFF]` |
| Button-code validator | `0x0807D588` (call `0x0807DA64`) | key mirror `0x03001380`; index at menu struct `+0x6D`; flag `+0x6C`; timer `+0x6E`=30; success `r0=1` at `0x0807D5FE` |
| Menu struct pointer | literal `0x08754BC4` | `0x0300016C4`; gate byte `+0x3F` = file index |
| File records | literal `0x0845F448`/`0x03000C24` | 24-byte stride; **byte 17 = completed-file gate**; bytes 0/18 also tested by caller |
| "NES METROID" label | file `0x045F440` → `0x0845F440` | 17-byte string compared at `0x807AAF8` against the multiboot header copy |
| NES METROID multiboot | file `0x07D8000` → `0x087D8000` | image executed in place via `bx r1` at `0x0808ABFC`; call site `0x0807ABAC` with `r0=0x08000000`, `r1=0x087D8000` |
| Debug leftover | file `0x054D27D` → `0x0854D27D` | ASCII `DEBUG`; **zero pointers** (dead) |
| SRAM | — | 32 KiB; written to zm.sav; mirrored into state at `0x59000`; magic `ZeroMissionUSAver005` at 0x1C, `ZERO_MISSION_010` at 0x80 |

## 5. Algorithm

### 5.1 Button-code validator (`0x0807D588`) — pseudocode

```
keys = *(u16*)0x03001380                 # active-high key mirror
s = *(void**)0x08754BC4                  # menu struct
if (s[0x6C] == 0):                       # not yet started
    if (timer s[0x6E] != 0): timer--; return 0
    if (keys == table[0]):               # 0x40 = Up
        s[0x6C] = 1; s[0x6D] = 1; return 0
    if (keys != 0): s[0x6E] = 30         # 30-frame window starts
    return 0
i = s[0x6D]
if (keys == table[i]):
    i++; s[0x6D] = i
    if (table[i] == 0xFFFF): return 1    # full sequence accepted
    return 0
if (keys != 0):                          # wrong key -> reset
    s[0x6C] = 0; s[0x6D] = 0; s[0x6E] = 30
return 0
```

Caller gate: `if (file_record[selected].b17 != 0) call validator;` on success
sets `s[0x2F]=2`, `s[0x70]=1`, `s[0x40]=8` (and a later branch chooses 15/16).

### 5.2 NES Metroid password (verified reimplementation, `metpass.py`)

```
alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz?-"
symbol -> value: index; ' ' -> 255.
decode: 24 symbols -> 144 bits (MSB-first, 6 bits each; for ' ', force the
        preceding symbol's low 2 bits to 1 and use value 63) -> 18 bytes.
        byte16 = shift.  Unrotate bytes 0..15 by 'shift' (rotate left across
        the 16 bytes with carry). checksum = sum(bytes[0..16]) & 0xFF;
        valid iff checksum == byte17.
encode: payload(16 bytes) + shift; rotate bytes 0..15 right by 'shift';
        append checksum; emit 24 x 6-bit symbols.
```

Field layout (published NES documentation, GBA port preserves the checksum):
bits 0–63 world state and pickups; 64–66 start location; 67 reset bit;
71 swimsuit; 72–79 items; 80–87 missile count; 88–119 game age; 120–127 bosses.

## 6. Tables

**Published GBA codes verified against this ROM**

| Claim (source) | ROM evidence | Verdict |
|---|---|---|
| Time Attack code Up,Left,Right,Down (3rd party cheat indexes) | table `0x0845F452` exactly `[0x40,0x20,0x10,0x80,0xFFFF]`; unique in 8 MiB | **verified in ROM**; on-screen path gate-blocked |
| NES debug password `BOMBS_ MISSLE SCREW_ ATACK_` (3rd party cheat indexes) | not stored as literal; special hardcoded NES code | published; not literal-searchable |
| NES `999999 999999 KKKKKK KKKKKK` = Hard Mode | decodes valid, shift 69, checksum 0x14 | **verified by decoder** |
| NES `000000 000020 000000 000020` Suitless | decodes valid, shift 0, checksum 0x80 | **verified by decoder** |
| NES `000000 000008 000000 000008` Reset | decodes valid, shift 0, checksum 0x08 | **verified by decoder** |
| NES `000000 000000 200000 000008` Screw Attack | decodes valid, shift 0, checksum 0x08 | **verified by decoder** |
| all-zero code | decodes valid, shift 0, checksum 0x00 | **verified by decoder** |

No GameShark/CodeBreaker code is reported as a finding. The 3rd party cheat indexes
"Alarm Never Sounds 600BC5C0 000091E0" and m2k2 debug-menu codes are
memory-edit codes and are explicitly out of scope.

**Text bank:** all in-game UI text is font/tile-indexed, so `strings` finds
almost none of it. Only ASCII hits are `NES METROID` (0x45F440, 0x7D80A0),
`DEBUG` (0x54D27D), and string fragments in the save file. A 3-byte-record
glyph/attribute/character table exists at `0x45F3D8..0x45F429`. UI labels
(PRESS START, SAMUS DATA, Start Game, Difficulty Setting, EASY/NORMAL, COPY,
ERASE, OPTIONS, SOUND, METROID FUSION LINK, Activate Easy Sleep?) were decoded
visually on real screens, not inferred from ASCII.

## 6b. Enumeration

### Button-code space
- Alphabet: GBA key masks (active-high), table width 1 halfword per press.
- Length(s): one sequence only — 4 presses + `0xFFFF` terminator.
- A whole-ROM scan for every 2+ press mask run ending in `0xFFFF` found
  **exactly one** multi-press table (`0x45F452`); all other hits are single
  masks or false positives. Enumerated space = 1 accepted sequence.
- Action branches in the dispatcher: `s[0x2F]=2 / s[0x70]=1 / s[0x40]=8`
  (reveal New Time Attack) and a secondary branch setting `s[0x39]=15|16`,
  `s[0x40]=9`. Both were read from code at `0x0807DA64..0x0807DAFE`.
- Rejection: wrong key resets index/flag/timer (`0x0807D60C..0x0807D620`);
  a live breakpoint at `0x0807D588` did **not** fire with an in-progress file,
  proving the completed-file gate rather than "code rejected".

### NES password space
- 24 symbols, 6 bits each = 144 bits; 16 payload bytes + 1 shift byte + 1
  checksum byte → **2^136 checksum-valid codes** (each shift gives 2^128).
- Novel codes minted with the reimplemented encoder (not in any published
  list — verified by absent literal and by distinct payload/shift):

  | Code | Shift | Decoder | Note |
  |---|---:|---|---|
  | `200W00W01001C808G0010W5Y` | 1 | accept, payload roundtrip | novel bit mix |
  | `2200W00W01001C808G0010Te` | 7 | accept, payload roundtrip | novel bit mix |
  | `01C808G0010WW0800800G4Mc` | 69 | accept, payload roundtrip | same shift as published Hard code, different payload |

- Bounds proven by rejection:
  - `401001002002OG0GW002101Y` (published-valid payload, checksum symbol +1)
    → decoder **rejects** (checksum mismatch).
  - `00000000003W08000000001W` → checksum **accepts** but start-location bits
    = `0b111` (reserved/invalid); per the documented validator this is the
    reset condition the game refuses — checksum and semantic bounds are
    separate layers (§16.5).
- **In-game entry of a novel NES password was not performed**: Original
  Metroid is gated by beating Zero Mission once (save flag), and no completed
  save exists for this ROM. This is reported as a gate, not as a negative
  result; the codec itself is validated against five published codes.

## 7. Validation evidence

- **Observed** (emulator/screenshots on `:319`): title (`s22`), Samus Data with
  save + COPY/ERASE/OPTIONS (`s23`), difficulty (`s06`), in-game (`s09`),
  pause/SLEEP (`s10`, `s11`), Easy Sleep prompt (`s13`), OPTIONS with SOUND and
  METROID FUSION LINK (`s26`, `s28`), Fusion Link screen (`s30`).
- **Observed** (RAM): file records at IWRAM `0x03000C24` (rec0 bytes
  `00…00 01 02 01…`), key-mirror reads, menu struct at `0x0300016C4`
  (`+0x40=0x1E` at file select). SRAM mirrored at state `0x59000`.
- **Derived** (disassembly, verified bytes): button table/validator/gate,
  loader `bx r1` to `0x087D8000`, `DEBUG` string with zero xrefs.
- **Inferred / gated**: on-screen New Time Attack reveal (gate byte 17 not
  satisfiable with an in-progress save); NES password acceptance on the real
  password screen (progression gate). Novel codes are accepted by the
  reimplemented validator and by published-code cross-check, not by the
  gated in-game screen.
- **Negative bounded**: only one button table in 8 MiB; no literal published
  password strings; debug menu requires RAM patch (out of scope).

## 8. Unknowns

- Which exact save-flag byte marks "game completed"/green-yellow Samus symbol
  (needed to drive the Time Attack gate without a full playthrough).
- Whether the GBA port changed NES password *field* semantics (the checksum
  format matches, but bit-to-item mapping could differ; published codes'
  descriptions were used, not a live decode of Samus state).
- The 3-byte glyph table at `0x45F3D8` was not fully decoded to a glyph map.
- Header complement byte anomaly (0x1D vs recomputed 0x36) — likely a
  rebuild artifact; entry word is stock so no execution impact observed.

## 9. Tooling

`strings`, `xxd`, `grep`, `arm-none-eabi-objdump -M force-thumb`, Python 3 +
`capstone`/`PIL`, mGBA SDL under Xvfb `:319` + openbox, `xdotool`, `scrot`,
`convert`, `gdb-multiarch` (stub unreliable), mGBA `-d` pty debugger
(`dbg.py`), `ui.py` (input/screenshot helper), `ssdiff.py` (savestate gbAs
parser/differ), `metpass.py` (NES password codec), `unlock_sweep.py`
(inconclusive SRAM probe). Working copy and artifacts in `/tmp/metroidzm`.

No ROM or copyrighted asset is redistributed; only hashes, addresses, and
original analysis scripts are published.
