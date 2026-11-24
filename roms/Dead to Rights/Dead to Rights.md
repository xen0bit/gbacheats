# Dead to Rights (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Dead to Rights/Dead to Rights.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `DEADTORIGHTS` |
| Game code / maker | `BDEE` / `AF` |
| Version / unit / device | `0x00` / `0` / `0` |
| Entry word | `0xEA000030` (branch to `0x080000C8`) |
| Header checksum field (`0xBE`) | `0x0000` |
| Complement byte (`0xBD`) | `0x38` (value computed from `0xA0..0xBC` is `0x64`) |
| MD5 | `f22ca50c999fddb4feef6bcb32b9d94a` |
| SHA-1 | `2e6e240bb80597f081550eb5e0478e3443cd685c` |
| SHA-256 | `fac1c69f9ca26615ddc4da7d6c2b5e15dbd2322fd0e6a097455868f8522aa0aa` |

- Nintendo logo at `0x04` is present and matches the stock vector at least through
  `0x1B` (`24 ff ae 51 69 9a a2 21 3d 84 82 0a 84 e4 09 ad 11 24 8b 98 c0 81 7f 21`).
- Embedded-header scan: the stock logo bytes occur exactly once, so this is a
  single GBA image, not a 2-in-1 pack or concatenated build.
- No trainer strings (`SUNHORS`, `CRC BANDIT`, `MODE7`, `TRAINER`, `PARADOX`,
  `VENOM`, `EURASIA`) exist in the image; the file ends in zero padding.
- The header was rebuilt by a tool: the checksum word is `0x0000` and the
  complement byte holds the correct checksum value (`0x38`) while the real
  complement is `0x64`. The entry word is also the non-stock `0xEA000030`
  (stock GBA entry is `0xEA00002E`, i.e. `0x080000C0`); this entry lands at
  `0x080000C8`, skipping the two instructions `mov r0,#0x12; msr cpsr_c,r0`.
  `0xC0..0xFF` is otherwise a normal crt0. The game boots and runs normally.
  This is recorded as a header/dump artifact; no cracktro or trainer code was
  found in the first 4 KiB.

## 2. Executive summary

The GBA port has a **developer-intended level-password system**:

- Main menu → `Password` opens a four-slot letter entry screen.
- The game stores the entered letters as ASCII in IWRAM at `0x0300025C`
  (one byte per slot, `A`=0x41 … `Z`=0x5A).
- After the fourth letter is entered and confirmed, the game runs an exact
  4-byte string comparison against a **hard-coded table of 17 four-letter
  codes**. The table is at ROM `0x0851DF8`, 8-byte records
  (`char code[4]; u32 0`), and a parallel pointer array is at `0x0856611C`.
  The pointer array is copied to IWRAM `0x03000FCC` at boot.
- There is **no checksum and no generator**. The validator's only test is
  `memcmp(entered, table[i], 4)` for `i = 0..16`; on a match it returns
  `i+1`, otherwise `-1`. The caller starts the level associated with `i`.
- Consequently the complete accepted set is exactly the 17 strings in the ROM:
  `QDJL ZZPD THKS MSLK KRPS VNVX YHXM FHMK LKJL RJHG RPGR WMVB KLPZ RVBS LMTQ GBGN YCGD`.
  Over the 26-letter alphabet the input space is `26^4 = 456,976`; exactly 17
  values pass.
- `QDJL` (table index 0) was entered on the real screen and the game
  transitioned to `PreLevelCutsceneState`; the RAM buffer read back
  `51 44 4A 4C`. A four-letter near-miss (`VFMP`) was rejected and the game
  stayed on the password screen (buffer `56 46 4D 50`).
- No published GBA password list was found (GameFAQs, VGChartz, TCRF and
  general web searches return only the console button cheats). The console
  button codes are **not present** in this ROM in either held-mask bytes or
  `u16` form, and no button-code dispatcher exists.
- A developer profiling/debug screen is compiled into the retail image
  (`"DeadToRights Debug Screen"`, `"Built: Sep 16 2004"`, menu strings
  `Main Menu / Profiling / Slow RAM Usage / Back`), registered from
  `0x08020160` through `0x0804001C`. No input gate that reaches it was found;
  it is treated as a shipped debug leftover (see §8).

## 3. How to reproduce

Emulator: mGBA 0.10.5 (`mgba -3`), SDL audio dummy, Xvfb `:285` + openbox.
Default mGBA SDL keymap on this build: `x`=A, `z`=B, `Return`=Start,
`BackSpace`=Select, arrows=D-pad, `a`=R, `s`=L.

Boot path and screen States (RAM-verified through the state object at
`0x0200D340`, whose `+0x20` field points at the state-name record):

1. `LicenseState` (legal screen) → `TitleScreenState` (press Start) →
   `MainMenuState`.
2. Main menu items are laid out in the order
   `New Game` (first) and `Password` (second); the strings in the text bank are
   `New Game` `0x085524BC`, `Password` `0x085524C5`, `Options` `0x085524CE`,
   `Credits` `0x085524D6`.
3. From `MainMenuState`, press `Down` once and `A` to open the password screen.
   (Pressing `A` on the first item starts New Game and enters
   `PreLevelCutsceneState`.)
4. Password screen input:
   - Up/Down change the current slot's letter (the slot selector is a letter
     wheel; the four slots start at the default letter `B` in this build).
   - `A` stores the current letter into `0x0300025C[slot]` and advances.
   - After the fourth letter, one more `A` performs validation.
   - `B` returns to the main menu.
5. Confirmed entry (exact key counts used in this analysis):
   - Slot 0: 15×Down → `Q`, `A`
   - Slot 1: 2×Down → `D`, `A`
   - Slot 2: 9×Down → `J`, `A`
   - Slot 3: 10×Down → `L`, `A`, then `A`
   The buffer at `0x0300025C` then reads `51 44 4A 4C` and the state becomes
   `PreLevelCutsceneState`.
   Timing note: 45–80 ms key holds occasionally double-step the letter wheel
   (the engine accepts a held press on consecutive frames); always verify a
   slot by reading `0x0300025C` before confirming the next one.
6. Rejection control: an arbitrarily chosen `VFMP` (buffer `56 46 4D 50`) is
   rejected, the screen stays in `MainMenuState`, and `0x085525D0`
   *"That is not a valid password."* is the error string. (A run that aimed at
   `QDJK` landed on `QDJL` in the last slot because the wheel double-stepped;
   it started the level, which independently re-confirms the accepted path.)

## 4. Address map

### ROM

| Address | Contents |
|---|---|
| `0x0851DF8` | password table, 17 records of `char code[4] + 4 zero bytes` (stride 8); last record `YCGD` at `0x0851E78`; table ends at `0x0851E80` |
| `0x0856611C` | pointer array to the 17 strings (17 × u32, `0x0851DF8..0x0851E78`), terminated by `0x00000000` at `0x08566160` |
| `0x085524B0` | `"Press Start"` |
| `0x085524BC` | `"New Game"` |
| `0x085524C5` | `"Password"` |
| `0x085524CE` | `"Options"` |
| `0x085524D6` | `"Credits"` |
| `0x08552491` | `"Level Password:"` (level-end display) |
| `0x085525D0` | `"That is not a valid password."` (English) |
| `0x081D49AC` | same error string in the English password-screen script blob (5 language copies at `0x454` stride: `0x1D49AC`, `0x1D4E00`, `0x1D5254`, `0x1D56A8`, `0x1D5AFC`) |
| `0x08050628` | `"DeadToRights Debug Screen"` |
| `0x08050644` | `"Built: Sep 16 2004"` |
| `0x08050678` | `"Main Menu"` / `"Profiling"` / `"Slow RAM Usage"` / `"Back"` debug-menu strings |
| `0x08050D24` | class-name strings `UI_PasswordCharacter`, `UI_PasswordWatcher`, `UI_CheatFlagsObserver` |

### Code (Thumb)

| Address | Role |
|---|---|
| `0x08036190` | `UI_PasswordWatcher` update: stores the current letter at `buffer[index]` via `0x08036424`; when `index == 3` calls the validator `0x0803643C`; on valid result stores the table index and starts the level; on invalid jumps to the error branch |
| `0x08036424` | ASCII builder: `buffer[index] = letter_index + 0x41` (`strb r1,[r0]`, `adds r1,#65`), buffer base `0x0300025C` |
| `0x0803643C` | **validator**: 17-entry exact 4-byte compare against the IWRAM pointer array at `0x03000FCC`; returns `i+1` (1..17) or `-1` |
| `0x08036374` | password-module constructor: sets up the module and installs the table pointer at `0x03000FCC` |
| `0x08040644` | input reader: reads `KEYINPUT 0x04000130`, XORs `0x3FF`, stores held at `0x03000290+6` and newly-pressed at `0x03000290+8` |
| `0x08020160` | debug-screen registration/print helper: `0x0804001C("DeadToRights Debug Screen")`, then the build date and separator |
| `0x080373BC` / `0x0803767C` / `0x080373FC` | `MainMenuState` init / update / draw (state record at ROM `0x0851F40`) |

### RAM (IWRAM/EWRAM)

| Address | Meaning |
|---|---|
| `0x0300025C` | entered-password buffer, 4 ASCII bytes |
| `0x03000FCC` | copy of the 17-entry password pointer array (loaded at boot) |
| `0x03000290` | input object: `+6` held key state (active high), `+8` newly pressed |
| `0x0200D340` | active StateMachine object; `+0x0C/+0x14/+0x1C` = init/update/draw pointers, `+0x20` = state-name record pointer |

### State records

`0x0851F40` `TitleScreenState`, `0x0851F6C` `MainMenuState`,
`0x0851F94` `DemoState`, `0x0851FB8` `PreLevelCutsceneState`,
`0x0851FE8` `NewGameState`, `0x0852010` `LevelState`,
`0x0852034` `GameCompletedState`, `0x0852060` `SuccessScreenState`,
`0x085208C` `FailedState`; each record is `name + padding + 3 × (u32 0xFFFF0000, u32 thumb-function)`.

## 5. Algorithm

```
/* ROM: validator entry 0x0803643C (Thumb) */
int validate_password(u8 *buf /* 0x0300025C */) {
    int i;
    for (i = 0; i <= 16; i++) {
        u8 *s = (u8*)ptr_table[i];      /* ptr_table = 0x03000FCC, ROM 0x0856611C */
        if (buf[0] != s[0]) continue;
        if (buf[1] != s[1]) continue;
        if (buf[2] != s[2]) continue;
        if (buf[3] != s[3]) continue;
        return i + 1;                   /* 1..17 */
    }
    return -1;                          /* invalid */
}
```

- Input alphabet: `A..Z` (the builder adds `0x41` to the 0-based wheel index;
  the wheel wraps through 26 letters).
- Length: exactly 4 letters; the validator reads 4 bytes.
- There is no sum, XOR, parity, key table or reserved bit. The table is the
  definition of the accepted set.
- Return value: `1..17` selects the level tied to that table slot; `-1` drives
  the error state and the `"That is not a valid password."` message.

Offline model used for the enumeration below:

```python
CODES = ["QDJL","ZZPD","THKS","MSLK","KRPS","VNVX","YHXM","FHMK","LKJL",
         "RJHG","RPGR","WMVB","KLPZ","RVBS","LMTQ","GBGN","YCGD"]
def validate(s): return s in CODES
```

## 6. Tables

### 6.1 Password table (ROM `0x0851DF8`, 8-byte stride; pointer at `0x0856611C`)

| Index | Code | String address |
|---:|---|---|
| 0 | `QDJL` | `0x0851DF8` |
| 1 | `ZZPD` | `0x0851E00` |
| 2 | `THKS` | `0x0851E08` |
| 3 | `MSLK` | `0x0851E10` |
| 4 | `KRPS` | `0x0851E18` |
| 5 | `VNVX` | `0x0851E20` |
| 6 | `YHXM` | `0x0851E28` |
| 7 | `FHMK` | `0x0851E30` |
| 8 | `LKJL` | `0x0851E38` |
| 9 | `RJHG` | `0x0851E40` |
| 10 | `RPGR` | `0x0851E48` |
| 11 | `WMVB` | `0x0851E50` |
| 12 | `KLPZ` | `0x0851E58` |
| 13 | `RVBS` | `0x0851E60` |
| 14 | `LMTQ` | `0x0851E68` |
| 15 | `GBGN` | `0x0851E70` |
| 16 | `YCGD` | `0x0851E78` |

### 6.2 Sanity properties

- All 17 entries are four uppercase `A-Z` letters, NUL-free, followed by four
  zero bytes; all 17 pointer-table entries resolve to the expected string.
- None of the 17 appears anywhere in the ROM's own text banks; they are
  developer/dev-build level shortcuts, not story strings.
- No 4-letter string from the console versions (e.g. `L1TTLVN`-style) exists.

## 6b. Enumeration

**Space.** Alphabet `A-Z`, length exactly 4 → `26^4 = 456,976` representable
inputs. There is no checksum field, so no value is "reserved": every one of
the 456,976 is either one of the 17 table strings or is rejected at
`0x0803643C`.

**Accepted set.** Running the reimplemented validator over the entire
456,976-value space yields exactly **17** accepted values, the table above.
This is a closed set, not a sample.

**Unpublished code entered and RAM-verified.** The 17 codes are not published
on GameFAQs/VGChartz/TCRF or any wiki reachable in this engagement (search
results returned only the console button codes; the GameFAQs GBA cheats page
returns HTTP 403 and archive searches did not surface a GBA code list). The
first table entry `QDJL` was entered through the real menu on the emulator:

- RAM at `0x0300025C` = `51 44 4A 4C` (`QDJL`);
- StateMachine name pointer at `0x0200D340+0x20` = `0x0851F40`
  (`TitleScreenState`/`MainMenuState` record family) changes to
  `PreLevelCutsceneState` (`0x0851FB8`), i.e. the level load begins;
- the level associated with table index 0 begins (the pre-level cutscene).

`QDJL` is not present in any published Dead to Rights list; nor is its
level-0 meaning documented. (A code that is accepted but *absent from the ROM
table* cannot exist: the validator has no other comparison.)

**Bounds proven by rejection.** `VFMP` (a four-letter value not in the table)
was entered with the same procedure. The buffer held `56 46 4D 50`, the game
stayed on the password screen in `MainMenuState`, and the error path at
`0x08036200` was taken instead of the level-start path. Because the validator
at `0x0803643C` is a plain 4-byte exact match with no tolerance, any one-letter
near-miss of a table code (e.g. `QDJK` for `QDJL`) necessarily fails the same
comparison; this is derived from the instruction stream, and the observed
rejection is the `VFMP` run above.

**Acceptance bound.** No 3-letter or shorter input can pass: the validator is
called only when slot index 3 has been stored, and it unconditionally reads
four bytes. No input character outside `A-Z` can be produced by the wheel.

## 7. Validation evidence

**Observed (emulator + RAM/savestate reads)**

- Boot sequence states: `LicenseState` → `TitleScreenState` → `MainMenuState`,
  read from the state object's name pointer.
- Password screen reachable from `MainMenuState` via Down + A; the password
  pointer array is resident at `0x03000FCC` (`0x0851DF8, 0x0851E00, …`).
- The entered-letter buffer at `0x0300025C` is written by the game from the
  on-screen wheel (e.g. one Down + A wrote `0x42`; 15 Downs + A wrote `0x51`).
- `QDJL` entry produced buffer `51 44 4A 4C` and `PreLevelCutsceneState`.
- `VFMP` entry produced buffer `56 46 4D 50` and stayed in `MainMenuState`
  (password screen), with the error text path taken.
- Start during `LevelState` opens a menu overlay (background fingerprint
  changes while the state stays `LevelState`).

**Derived (disassembly)**

- The validator at `0x0803643C` compares 4 bytes against up to 17 pointers
  loaded from `0x03000FCC`; it returns `index+1` or `-1`.
- The ASCII builder at `0x08036424` writes `letter + 0x41` into
  `0x0300025C[index]`.
- The watcher at `0x08036190` triggers validation only when `index == 3`
  (fourth slot), otherwise it advances.
- The pointer array at `0x0856611C` resolves one-to-one to the 17 strings.

**Inferred**

- The table index maps to the level loaded by the caller (the caller passes
  the return value to `0x08020750`, then starts the level via `0x080239B8`);
  the exact level content for each of the 17 indices was not compared
  one-by-one.
- The debug/profiling screen is a developer leftover with no retail input gate
  (see §8).

## 8. Unknowns

- **Per-index level identity:** we proved `QDJL` starts the first level and
  that the return value is the table index, but did not play all 17 to compare
  level contents. The mapping index→level is derived from table order.
- **Pause-menu item list:** Start in `LevelState` opens an overlay that shares
  the menu background; its individual items were not enumerated.
- **Debug screen gate:** the debug screen is registered at init
  (`0x08020160` → `0x0804001C`) and its strings and formatting code exist, but
  no input path (KEYINPUT consumer or state transition) reaches it. The only
  literal reference to `"DeadToRights Debug Screen"` is the registration site;
  there is no button-code table in the image. It is reported as a shipped
  debug leftover, not an in-game cheat.
- **Header provenance:** the checksum/complement/entry anomalies match a
  rebuilt header. No trainer code or appended payload was found, and the game
  runs stock; the origin of the rebuild is unknown.

## 9. Tooling

- `mgba 0.10.5` (SDL) under `Xvfb :285` + `openbox`, `SDL_AUDIODRIVER=dummy`,
  `xdotool` for XTEST key events.
- `python3` savestate tooling: mGBA `.ss1` PNG `gbAs` chunk → `zlib.decompress`
  → raw 397,312-byte state; VRAM at `0x1000`, IWRAM at `0x19000`, EWRAM at
  `0x21000` (buffer `0x0300025C` = state offset `0x1925C`).
- State identification: parse the StateMachine records at `0x0851F40` and read
  the live state object at `0x0200D340`.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for raw Thumb disassembly.
- Helper scripts written during this engagement (in `/tmp/deadtorights`):
  `ss.py`/`ctl.py` (savestate extraction/diff), `cur.py` (state name),
  `fp.py` (VRAM fingerprints), `nav*.py` (menu/password entry with RAM
  feedback), `states.py` (state-record parser).
- Web searches: GameFAQs (GBA cheats page HTTP 403), VGChartz, TCRF, general
  search; no GBA password list located.

## 10. Legal note

No ROM image, extracted graphics, audio, or game text is redistributed with
this report. Only hashes, addresses, disassembly-derived algorithms, and the
17 short developer codes needed to reproduce the result are published. The ROM
and all emulator artifacts were removed after the analysis.
