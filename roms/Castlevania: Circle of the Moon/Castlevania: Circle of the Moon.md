# Castlevania: Circle of the Moon (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Castlevania: Circle of the Moon.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title (0xA0) | `DRACULA AGB1` |
| Game code (0xAC) | `AAME` (USA) |
| Maker code (0xB0) | `A4` (Konami) |
| Software version (0xBC) | `0` (rev 0) |
| Entry branch (0x00) | `0xEA00002E` → `0x080000C0` (stock crt0) |
| Fixed 0xB2 | `0x96` (valid) |
| Complement byte (0xBD) | `0xB1` |
| Computed header checksum | `0xB1` (matches 0xBD — header intact) |
| 16-bit header checksum (0xBE) | `0x0000` (unused, normal) |
| MD5 | `50a1089600603a94e15ecf287f8d5a1f` |
| SHA-1 | `d661b01eb94186435723ac03344792c11c20c522` |
| SHA-256 | `ad9fabaf4398e0f4a2a095bacddc6c0dc7e139903b41e088ca3590c44b684da0` |

**Embedded GBA-header scan.** The 156-byte Nintendo logo (`24 ff ae 51 …`) occurs exactly once in
the file, at file offset `0x04` (header at `0x0`). There are no secondary headers, no multiboot
stub, no cracktro and no appended trainer. The image is a clean US retail ROM.

**Patch/trainer check.** The entry word is the stock `b 0x080000C0`; the header complement is
valid; the first 4 KiB is the normal crt0 + BIOS-setup code. No scene-release patch is present.

## 2. Executive summary

The only in-game, developer-intended cheat system in this ROM is the **name-entry code table**.
It is not a password screen in the usual sense: the player types a *character name* on the
name-entry keyboard, and if the 8-byte buffer equals one of four hard-coded strings, the game
starts the new file in a special mode.

The four accepted names (stored as bytes `A=1 … Z=26`, compared as exactly 8 bytes) are:

| ROM file offset | ROM address | Name | Mode | Flag bit | Returned mode ID |
|---|---|---|---|---|---|
| `0xCAB40` | `0x080CAB40` | `CROSSBOW` | Shooter | 1 (mask `0x02`) | 1 |
| `0xCAB48` | `0x080CAB48` | `FIREBALL` | Magician | 2 (mask `0x04`) | 2 |
| `0xCAB50` | `0x080CAB50` | `GRADIUS\0` | Fighter | 3 (mask `0x08`) | 3 |
| `0xCAB58` | `0x080CAB58` | `DAGGER\0\0` | Thief | 4 (mask `0x10`) | 4 |

The validator is at `0x0800BF70`. It compares the 8-byte name buffer at game-state `+0x600`
against the four 8-byte table entries, and then tests one bit of the mode-unlock byte at
game-state `+0x634`. If the name matches **and** the bit is set, it returns the mode ID
(1–4); otherwise it returns 0. The mode ID is stored by the caller at `0x0202F453`.

The ROM contains **no** `JULIUS`, `MAXIM`, `HARD`, `SOUND`, `DEBUG`, `PASSWORD` or
`BOSS RUSH` literals in the name-table encoding, and no second name table exists. There is no
sound test and no debug menu in this US ROM. The published “Julius mode / Hard mode / sound
test” material belongs to other Castlevania games or to the PSP/DS port, not to this image.

**§0.2 deliverable status.** The four accepted names are all published (GameFAQs, Cheat Code
Central, Cheat Happens, IGN, RPGClassics, VGMuseum, mogelpower, and a Japanese guide), so this
is a **proven closed set of 4 published inputs with no novel in-game code**. The validator only
compares the first 8 bytes, so 9-character strings such as `FIREBALLX` are accepted at the
validator level, but the on-screen keyboard cannot store a 9th byte (8-byte buffer, length cap
with an error state), so those are labelled **derived-only, unreachable through the UI**. The
8-byte truncation and the byte-exact boundary are proven by rejection: `FIREBALX`, `GRADIUSZ`,
`DAGGERZZ` and `DAGGERXY` are rejected because their 8th byte differs from the table entry.

## 3. How to reproduce

### Emulator / display

```
Xvfb :235 -screen 0 1024x768x24 &
DISPLAY=:235 openbox &
SDL_AUDIODRIVER=dummy mgba -d -3 "Castlevania: Circle of the Moon.gba"
```

mGBA 0.10.5, `-d` pty debugger, `-3` scaling. The pty debugger is driven through a Unix socket
by `daemon235.py` (this report’s Tooling section). All memory reads/writes below were done with
the mGBA debugger (`x/1`, `w/1`, `w/4`, `w/r`, `break/t`, `frame`).

### Measured keymap (mGBA SDL, this container)

The SDL keymap in this build varies with the X server/keyboard state, so it must be re-measured
before driving the menus. The second session’s measurement with `KEYINPUT` (`0x04000130`,
active-low) was:

| GBA button | Keyboard key | KEYINPUT bit |
|---|---|---|
| A | `x` | 0 |
| B | `z` | 1 |
| Select | `BackSpace` | 2 |
| Start | `Return` | 3 |
| Right | `Right` | 4 |
| Left | `Left` | 5 |
| Up | `Up` | 6 |
| Down | `Down` | 7 |
| R | `s` | 8 |
| L | `a` | 9 |

An earlier session measured a different (rotated) mapping on the same binary, so always confirm
with `KEYINPUT` before typing.

### Validator invocation used for the dynamic proof

The game’s own validator (`0x0800BF70`) was called in-place with the game’s own game-state
pointer. The procedure (all through the mGBA debugger):

```
w/4 0x02022490 <first 4 name bytes>   ; name buffer, game state +0x600
w/4 0x02022494 <next 4 name bytes>
w/1 0x020224C4 <mode-flag byte>       ; game state +0x634
w/r r0 0x02021E90                     ; game state pointer
w/r lr 0x080003CC                     ; return to the main loop
w/r pc 0x0800BF70                     ; validator entry
break/t 0x0800BFE8                    ; validator epilogue
frame 1
; r0 at the epilogue is the validator return value
```

This executes the ROM’s real comparison code, not a reimplementation.

### Real name-entry screen attempt (in-game confirmation)

The four names were also attempted through the real menus. Observed flow (screen IDs read from
the screen object at `0x020045D8`, field `+0x00`):

1. Boot → title screen (handler `0x08001978`).
2. Title confirm → screen 21 (`0x08002B38` → real handler `0x08002D7C`), a character-portrait
   screen with a text line.
3. D-pad Left on screen 21 → screen 23 (`0x0800A668`), a two-panel file/mode select. The
   handler reads the pressed-key halfword at game state `+0x1470` (`0x02023300`) and maintains
   a selection byte at game state `+0x636` (`0x020224C6`).
4. Forcing the screen object to ID 27 with handler `0x0800A9ED` produced a different text
   screen, but it was not the interactive alphabet keyboard (the keyboard’s own state was not
   initialised by this shortcut).

The on-screen alphabet entry of the four names was **not completed** in this session. The
blocker was menu navigation: the pressed-key halfword observed at `0x02023300` during key
presses (`0x4000` Down, `0x8000` Left, `0x2000` Right, `0x1000` A, `0x0100` Start) does not
match the bit positions the screen-23 handler tests (`0xC0`/`0x40`/`0x80`/`0x30`/`0x20`/
`0x10`), so the menu selection at `0x020224C6` never advanced and the name-entry screen could
not be reached with the measured keymap. The accept/reject results in §6b come from executing
the ROM’s own validator, and the on-screen keyboard path remains unexercised (see §8).

## 4. Address map

| Address | Meaning |
|---|---|
| `0x080CAB40` | Name table, 4 entries × 8 bytes (`CROSSBOW`, `FIREBALL`, `GRADIUS\0`, `DAGGER\0\0`) |
| `0x080CAB60` | Mode parameter table; `params[0..3] = 01 02 03 04` (shift amounts / mode IDs) |
| `0x080CAB1C` | Name-entry keyboard alphabet (`01..1A` = A–Z, `1B` `*`, `1C` space, `1D` `!`, `1E` `?`, `1F` `.`, `20` `-`, `21` `'`) |
| `0x0800BF70` | Name validator (entry point) |
| `0x0800BFE8` | Validator epilogue (return value in `r0`) |
| `0x0800A9EC` | Name-entry / mode-select screen handler |
| `0x0800B6C0` | Name-entry keyboard handler (stores characters, backspace `0xFE`, end `0xFF`) |
| `0x080088CC` | Title-screen input handler (Left/Right select, A/Start confirm) |
| `0x080007D8` | Input manager (reads `0x04000130`, updates EWRAM state) |
| `0x0866CE28` | Screen handler table (63 entries, ROM addresses) |
| `0x02021E90` | Game-state struct base (EWRAM) |
| `0x02022490` | Name buffer, 8 bytes (game state `+0x600`) |
| `0x020224C4` | Mode-unlock flags (game state `+0x634`; bits 1–4) |
| `0x020224C9` | “Name entry allowed” flag (game state `+0x639`) |
| `0x0202F453` | Mode ID result (halfword, written by the name-entry handler) |
| `0x0202332C` | Current key state, active-high (game state `+0x149C`) |
| `0x020232FC` | Pressed key state, active-high (game state `+0x146C`) |
| `0x020232FE` | Previous key state (game state `+0x146E`) |
| `0x03000000` | IWRAM utility-function table used by the screen system |

## 5. Algorithm

### Name encoding

The name buffer stores one byte per character, `A=1 … Z=26`. The keyboard alphabet table at
`0x080CAB1C` is `01 02 03 … 1A 1B 1C 1D 1E 1F 20 21`. Comparison is a raw byte compare; it is
case-sensitive and does not fold `0x1B`–`0x21` to letters.

### Validator (`0x0800BF70`, Thumb)

```
function validate(gs):            // gs = game state pointer, r0
    for entry in 0..3:            // r3
        ok = true
        for i in 0..7:            // r2
            if gs.name[i] != table[entry].name[i]:
                ok = false
        if ok: match = entry
    if match == 0xFF: return 0
    flag = gs.flags              // gs+0x634
    shift = params[match]        // params = 0x080CAB60, values 1,2,3,4
    if (flag >> shift) & 1:
        return shift             // 1..4
    return 0
```

The caller (`0x0800A9EC`) copies the 8-byte name buffer to `0x02025369`, calls the validator,
stores the result as a halfword at `0x0202F453`, and starts the new game in that mode.

### Mode gating

The mode byte at `0x020224C4` is written when the player completes the game in a mode
(published behaviour). The validator refuses a matching name if the corresponding bit is clear,
so a fresh file rejects all four codes. This was confirmed dynamically (Section 7).

## 6. Tables

### Accepted names (complete)

| Name | Bytes (`A=1…Z=26`) | Mode | Unlock bit | Mode ID |
|---|---|---|---|---|
| `CROSSBOW` | `03 12 0F 13 13 02 0F 17` | Shooter | `0x02` | 1 |
| `FIREBALL` | `06 09 12 05 02 01 0C 0C` | Magician | `0x04` | 2 |
| `GRADIUS` | `07 12 01 04 09 15 13 00` | Fighter | `0x08` | 3 |
| `DAGGER` | `04 01 07 07 05 12 00 00` | Thief | `0x10` | 4 |

### Keyboard alphabet (`0x080CAB1C`)

`A–Z` = `01–1A`, `*` = `1B`, space = `1C`, `!` = `1D`, `?` = `1E`, `.` = `1F`, `-` = `20`,
`'` = `21`. Backspace is `0xFE`, End/confirm is `0xFF` (handled at `0x0800B72C` / `0x0800B78C`).

## 6b. Enumeration

**Space definition.** The validator is a 4-entry lookup with a fixed 8-byte compare. The
representable accepted set is therefore exactly the four 8-byte strings above; the input buffer
is 8 bytes and the keyboard caps the *stored length* at 7 but still writes an 8th character
before raising its “length > 6” error state (`0x0800B7E0`), so 8-byte names are enterable.

**Complete accepted set (proven by running the ROM validator).**

| Input (bytes written) | Flags | Return | Meaning |
|---|---|---|---|
| `FIREBALL` | `0x1E` | 2 | accepted, Magician |
| `CROSSBOW` | `0x1E` | 1 | accepted, Shooter |
| `GRADIUS` | `0x1E` | 3 | accepted, Fighter |
| `DAGGER` | `0x1E` | 4 | accepted, Thief |
| `FIREBALL` | `0x1A` (bit 2 clear) | 0 | rejected by flag gate |
| `GRADIUS` | `0x16` (bit 3 clear) | 0 | rejected by flag gate |
| `DAGGER` | `0x0E` (bit 4 clear) | 0 | rejected by flag gate |
| `CROSSBOW` | `0x1C` (bit 1 clear) | 0 | rejected by flag gate |
| `NOTACODE` | `0x1E` | 0 | rejected, no table entry |
| `FIREBAL` (7 chars + NUL) | `0x1E` | 0 | rejected, 8th byte must be `L` |
| `fireball` (lowercase) | `0x1E` | 0 | rejected, case-sensitive |
| `GRADIUSX` | `0x1E` | 0 | rejected, 8th byte must be NUL |
| `DAGGERX` | `0x1E` | 0 | rejected, 7th byte must be NUL |
| `DAGGER ` (space) | `0x1E` | 0 | rejected |
| `GRADIUS ` (space) | `0x1E` | 0 | rejected |

**Inputs longer than 8 bytes are derived-only and unreachable through the UI.** The name
buffer is exactly 8 bytes (`game state +0x600`), and the keyboard handler (`0x0800B6C0`)
stores a character at `name[length]` and only increments `length` while `length <= 6`
(`cmp r0, #6; bgt error` at `0x0800B716`). An 8th character is written to `name[7]` and then
the handler jumps to its error state (`0x0800B7E0`, state 35). The on-screen keyboard therefore
cannot store a 9th byte, so the following validator-level accepts are **not enterable codes**:

| Input | Validator return | UI status |
|---|---|---|
| `FIREBALLX` | 2 | derived-only, unreachable (9 chars) |
| `FIREBALLZ` | 2 | derived-only, unreachable (9 chars) |
| `CROSSBOWX` | 1 | derived-only, unreachable (9 chars) |
| `CROSSBOWZ` | 1 | derived-only, unreachable (9 chars) |
| `FIREBALL ` (trailing space) | 2 | derived-only, unreachable (9 chars) |
| `FIREBALL.` (trailing period) | 2 | derived-only, unreachable (9 chars) |

They are still useful as a proof of the 8-byte truncation bound, but they are not novel
in-game codes.

**Published status of the four accepted names.** All four are published, so the accepted set
is a **proven closed set with no novel in-game code**:

* GameFAQs cheats page — “Play in Magician mode … enter FIREBALL as your name”, “… enter
  GRADIUS …”, “… enter CROSSBOW …”, “… enter DAGGER …”.
* GameFAQs walkthrough by Tarrun — “04.1 Magician … Password: FIREBALL”, “04.2 Fighter …
  Password: GRADIUS”, “04.3 Shooter … Password: CROSSBOW”, “04.4 Thief … Password: DAGGER”.
* Cheat Code Central, Cheat Happens, IGN, RPGClassics, VGMuseum, mogelpower and the Japanese
  guide at `cotm.retromeme.nobody.jp` all list the same four names.

**Bounds proven by rejection.** `FIREBALX` (8th byte `X` ≠ `L`), `GRADIUSZ` (8th byte `Z` ≠
NUL), `DAGGERZZ` (7th byte `Z` ≠ NUL), `DAGGERXY` (7th byte `X` ≠ NUL) are all rejected. This
proves the compare is byte-exact at the 8-byte boundary and that the alphabet is not folded.

**Negative results (searched, not found).**

* No `JULIUS`, `MAXIM`, `HARD`, `SOUND`, `DEBUG`, `PASSWORD`, `BOSS`, `RUSH`, `ARENA`,
  `CASTLEVANIA`, `CIRCLE`, `KONAMI` literal exists in the ROM in the name-table encoding
  (`A=1…Z=26`), in plain ASCII, in ASCII±`0x20`/`0x40`, XOR/ADD/SUB-constant forms, nibble
  swap, bit reverse, UTF-16LE/BE, or reversed byte order. The only hits for the four mode names
  are the table at `0x080CAB40`.
* An LZ77 scan of the whole image (82,607 candidate blocks decompressed with the standard GBA
  `0x10` header) found none of the above strings either. The game’s UI text is not stored as
  plain ASCII or as standard GBA LZ77.
* The name table is referenced from exactly one pointer (`0x080CAB40` at file `0xBFC0`), and
  the validator loops `entry = 0..3`. There is no fifth entry and no second table.
* No sound-test screen and no debug menu were reached or found. The screen table at
  `0x0866CE28` has 63 entries; the screens reached in this session were the boot/logo screen,
  the title screen (entry 19, handler `0x08001978`), the post-title menu (entry 21, handler
  `0x08002B38` → real handler `0x08002D7C`), the two-panel file/mode select (entry 23,
  handler `0x0800A668`) and one further text screen. The name-entry keyboard (entry 27,
  handler `0x0800A9EC`) was not reached.

## 7. Validation evidence

**Observed (emulator / RAM).**

* Header, hashes and embedded-logo scan (Section 1).
* The name table bytes at `0x080CAB40` (Section 6) — read directly from the ROM.
* The validator return values in Section 6b — produced by executing the ROM function at
  `0x0800BF70` in mGBA with the game-state pointer `0x02021E90`; `r0` was read at the
  function epilogue `0x0800BFE8`.
* The mode-flag gate — clearing the matching bit makes the same name return 0.
* The input manager at `0x080007D8` and the EWRAM key state at `0x0202332C` / `0x020232FC`
  (measured with `KEYINPUT` at `0x04000130`).
* The title-screen input handler at `0x080088CC` (Left/Right change a 0/1 selection at
  `[screen+0x4C]`, A/Start confirm).
* Screen handlers observed live: title `0x08001978`; post-title menu `0x08002B38`
  (thunk) → `0x08002D7C` (object-list update).
* Two further menu screens were walked after the title screen: a two-panel file/mode select
  (left and right panels, each with a labelled box) and a following screen with a large
  left panel and a right-hand text column. Their exact labels were not decoded under the
  session time budget; the screen IDs were tracked with breakpoints on the 63-entry handler
  table at `0x0866CE28`.
* The screen-23 menu handler (`0x0800A668`) reads the pressed-key halfword at game state
  `+0x1470` (`0x02023300`) and maintains a selection byte at game state `+0x636`
  (`0x020224C6`). Key presses were confirmed in `KEYINPUT` but the menu selection never
  advanced (see §3 “Real name-entry screen attempt”), so the real name-entry keyboard was
  not reached.
* Published status of the four names was checked against GameFAQs (cheats page and Tarrun’s
  walkthrough), Cheat Code Central, Cheat Happens, IGN, RPGClassics, VGMuseum, mogelpower and
  `cotm.retromeme.nobody.jp`; all four names appear in all of them (Section 6b).

**Derived (disassembly).**

* The validator loop, table layout, parameter table and flag-bit mapping (Section 5).
* The keyboard handler’s character storage, backspace (`0xFE`) and end (`0xFF`) semantics.
* The screen handler table and the screen-ID field at `[screen+0x00]`.

**Inferred (not fully exercised).**

* The in-game *effect* of each mode (starting stats, DSS cards, Homing Dagger, etc.) is taken
  from the published descriptions; it was not replayed through a full game in this session.
* The published “Memory Wipe” button code (hold L+R+A+B, press Select on the title screen) was
  not exercised dynamically; the title-screen input handler was located but the code path was
  not triggered.

## 8. Unknowns

* The four mode names were entered by writing the game’s name buffer and calling the game’s
  own validator through the debugger. They were **not** typed on the on-screen name-entry
  keyboard in this session. The real menu flow was walked as far as the two-panel file/mode
  select (screen 23), but the menu selection byte at `0x020224C6` never advanced because the
  pressed-key halfword observed at `0x02023300` did not match the bit positions the screen-23
  handler tests; the name-entry screen was therefore not reached (Section 3). The comparison
  code executed is the ROM’s, so the accept/reject results are authoritative; only the
  on-screen keyboard-entry path and the `0x0202F453` caller result are unexercised.
* Because the four names are published (Section 6b), this engagement’s §0.2 deliverable is a
  **proven closed set**: exactly 4 accepted inputs, all published, with byte-exact comparison,
  flag gating and rejection bounds proven. There is no novel in-game code to mint.
* The exact starting-stat differences of Magician/Fighter/Shooter/Thief modes were not
  measured in-game.
* Whether the Japanese (`AAMJ`) or European (`AAMP`) revisions contain additional names or a
  sound test was not checked; this report covers only the US `AAME` image named above.
* The “Memory Wipe” button code and any other button sequence were not verified.

## 9. Tooling

All scripts are in `/tmp/opencode/cotm/` (not part of the repository):

| File | Purpose |
|---|---|
| `phase0.py` | header parse, header-checksum verification, embedded-logo scan, hashes |
| `encscan.py` | search the ROM for known strings under XOR/ADD/SUB/nibble/bit-reverse/UTF-16 transformations |
| `lzscan.py` | scan every byte for GBA LZ77 (`0x10`) blocks, decompress and search for strings |
| `daemon235.py` | mGBA pty-debugger driver over a Unix socket (`key`, `tap`, `readbytes`, `w/1`, `w/4`, `w/r`, `break/t`, `frame`, `frameq`, `raw`) |
| `mem.py` | Python memory-read helper with retry/flush |
| `screen.py` | render the live 240×160 screen from VRAM/palette as ASCII (used for menu walking; no image files were read or produced) |
| `c235.py` | one-shot socket client for the driver |

Commands used for the dynamic proof:

```
Xvfb :235 -screen 0 1024x768x24 &
DISPLAY=:235 openbox &
SDL_AUDIODRIVER=dummy mgba -d -3 "Castlevania: Circle of the Moon.gba"
python3 daemon235.py          # driver on /tmp/opencode/cotm/daemon235.sock
python3 c235.py raw "w/4 0x02022490 0x05120906"
python3 c235.py raw "w/4 0x02022494 0x0C0C0102"
python3 c235.py raw "w/1 0x020224C4 0x1E"
python3 c235.py raw "w/r r0 0x02021E90"
python3 c235.py raw "w/r lr 0x080003CC"
python3 c235.py raw "w/r pc 0x0800BF70"
python3 c235.py raw "break/t 0x0800BFE8"
python3 c235.py raw "frame 1"        # r0 at the epilogue = mode ID
```

No ROM, asset or copyrighted data is redistributed by this report.
