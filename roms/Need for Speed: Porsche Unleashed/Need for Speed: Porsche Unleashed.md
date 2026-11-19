# Need for Speed: Porsche Unleashed (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Need for Speed: Porsche Unleashed.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `NEEDFORSPEED` |
| Game code / maker | `AZFE` / `20` (EA / Destination Software) |
| Version | 0x00 (Rev.00) |
| Entry word | `0xEA00002E` — stock ARM branch to `0x080000C0` |
| MD5 | `7406c224589f1a2f57feff5eb3c177c3` |
| SHA-1 | `c57a0652017c47ac2d25a51bf351738cd634272b` |
| SHA-256 | `faef85fd862c60b4c60a756c19f91c8d91ac6db283f1de60306a083ffb010c70` |

`file` identifies it as `Game Boy Advance ROM image: "NEEDFORSPEED" (AZFE20, Rev.00)`.
Phase 0 checks: exactly **one** GBA header (156-byte Nintendo logo scan finds only
file offset 0), no embedded/extra images, no cracktro or appended trainer
(signature scan negative), stock crt0 entry. Header checksum `0x0000` and
complement `0x55` are as shipped; no evidence of a rebuilt/patched header.
The ROM folder's `INDEX.md` was not modified.

## 2. Executive summary

There is **one developer-intended cheat system**: two secret **player names**
entered on the normal "ENTER NAME" screen. Entering `NCC1701` or `THEHULK`
writes an all-ones 25-bit unlock mask (`0x01FFFFFF`) into one of two unlock
bitfields, unlocking the game's gated content (cars/tracks).

- `NCC1701` → `0x03005EEC = 0x01FFFFFF` (default `0x4023`)
- `THEHULK` → `0x03005AB0 = 0x01FFFFFF` (default `0x00000003`)

Both effects were observed in mGBA by decompressing `.ss1` savestates and
reading IWRAM; the name buffer at `0x03006590` was read back to prove the
exact typed string. Rejections (ordinary names, near-miss) leave both words at
their defaults.

The **entire reachable code space is exactly two values**. There is no
password screen, no button-code sequence, and no hidden/debug menu. The name
table is a 2-entry NULL-terminated pointer list; the validator compares
exactly 7 characters, and the on-screen keyboard hard-caps names at 7
characters, so the validator's 8th-character blindness (a latent alias bug)
is **unreachable through the UI**. No unpublished code can exist in the
reachable space; this is proven below rather than asserted.

All in-game text is tile-index encoded (a letter substitution, not ASCII), so
`strings` alone would miss every menu label. All five language banks were
decoded and enumerated; no debug/cheat/password labels exist in any of them.

Published-code research: GameFAQs, TCRF, cheatcc, DuckDuckGo, Bing, Google and
the Wayback Machine CDX API were attempted; all returned 403/503, a bot
challenge, or no results in this environment. The two names were therefore
derived from the ROM itself, not from a published list.

## 3. How to reproduce

1. Boot the ROM in mGBA on a dedicated display:
   `Xvfb :317 -screen 0 1024x768x24 &`, `DISPLAY=:317 openbox &`,
   `SDL_AUDIODRIVER=dummy mgba -3 game.gba &`.
2. Keymap (mGBA SDL default): A=`x`, B=`z`, Start=`Return`,
   Select=`BackSpace`, D-pad = arrow keys. Hold keys 100–150 ms.
3. At the title screen press **Start**, then choose **single player** — the
   game asks **ENTER NAME** (this is a player profile name, not a password).
4. Type `THEHULK` (or `NCC1701`) on the on-screen keyboard: letters are on two
   13-column rows (`A..M`, `N..Z`), the third row is `1..0`, blank, `DEL`,
   `END`. Finish by selecting **END**.
5. The name is accepted and the unlock bitfield is written immediately.

To read RAM, save a state (`Shift+F2`) and decompress the `gbAs` PNG chunk
(`zlib.decompress`); IWRAM begins at raw offset `0x19000` for this 4 MiB ROM.
`readstate.py` in the work dir does this. Observed values:

| Test | `0x03006590` (name) | `0x03005AB0` | `0x03005EEC` |
|---|---|---|---|
| Fresh game (no cheat) | — | `0x00000003` | `0x00004023` |
| `THEHULK` | `THEHULK\0` | **`0x01FFFFFF`** | `0x00004023` |
| `NCC1701` | `NCC1701\0` | `0x00000003` | **`0x01FFFFFF`** |
| `AAAAAAA` (reject) | `AAAAAAA\0` | `0x00000003` | `0x00004023` |

Screens walked with state/screenshot evidence: legal splash, title, ENTER NAME,
main menu (5 items), single-player submenu (3 items), quick-race menu, race
setup (track selection), garage (car/colour/transmission), options, records,
credit roll. No further screen exists in any decoded text bank.

## 4. Address map

| Address | Type | Role |
|---|---|---|
| `0x08000000` | ROM | entry branch (`0xEA00002E`) |
| `0x080BE018` | Thumb fn | keypad reader: reads `0x04000130`, stores held/pressed |
| `0x03006A38` | IWRAM | held keys, active-high (A=1,B=2,Sel=4,Start=8,R=0x10,L=0x20,U=0x40,D=0x80,R=0x100,L=0x200) |
| `0x03006A34` | IWRAM | newly-pressed keys, active-high |
| `0x03006590` | IWRAM | player-name buffer (8 bytes; UI accepts 7) |
| `0x080A8C8C` | Thumb fn | state-38 case containing the name-cheat validator |
| `0x080A8CB8` | literal | table base `0x083F6378` |
| `0x080A8CBC` | literal | name buffer `0x03006590` |
| `0x080A8D10` | literal | `0x03005EEC` (NCC1701 target) |
| `0x080A8D20` | literal | `0x03005AB0` (THEHULK target) |
| `0x080A8D24` | literal | value `0x01FFFFFF` written by either code |
| `0x083F6378` | ROM table | `ptr("NCC1701")`, `ptr("THEHULK")`, `NULL` terminator |
| `0x083CDB20` | ROM | `"NCC1701\0"` |
| `0x083CDB18` | ROM | `"THEHULK\0"` |
| `0x03005EEC` | IWRAM | unlock bitfield B (default `0x4023`) |
| `0x03005AB0` | IWRAM | unlock bitfield A (default `0x00000003`) |
| `0x080A56D4` | Thumb fn | new-game initializer: `0x03005AB0 = 3` |
| `0x080AA896` | Thumb fn | save initializer: `0x03005AB0 = 3`, `0x03005EEC = 0x4023` |
| `0x080A5714` | Thumb fn | counts set bits of `0x03005AB0` (loop 0..24) |
| `0x080A3CBE` | Thumb | tests a bit of the unlock word against a selectable-item list |
| `0x083CD800`–`0x3CD7FF` | ROM | five language text banks (font-index encoded) |

File offset = ROM address − `0x08000000`.

## 5. Algorithm

The cheat is a 2-entry string table, not a checksum generator. Reimplementation:

```python
TABLE = [0x083CDB20, 0x083CDB18]   # "NCC1701", "THEHULK"; terminated by NULL @0x083F6380
TARGET = [0x03005EEC, 0x03005AB0]  # one per table index
VALUE  = 0x01FFFFFF

def check(name: bytes):            # name = 8-byte buffer at 0x03006590
    for i, code_ptr in enumerate(TABLE):
        code = rom_str(code_ptr)
        if len(code) > 7:
            code = code[:7]
        if name[:7] == code:       # exact compare, indices 0..6 only
            iwram_write_u32(TARGET[i], VALUE)
            return True
    return False
```

Derived from the disassembly at `0x080A8C92`:

- `r7 = [0x03006590]` (first input byte); compare with first byte of each table
  string; on mismatch clear the match flag.
- Loop `r2 = 0..6`: compare `code[r2]` with `name[r2]`; exit early as a match
  when `code[r2] == 0` (NUL) or when `r2 > 6`.
- The input's byte 7 is never read — a latent alias (`THEHULKX` would validate).
- On a match, play a sound (`BL 0x0809CE10` with `r0=4`), then select the
  target by table index (0 → `0x03005EEC`, 1 → `0x03005AB0`) and store
  `0x01FFFFFF` there.
- Two side effects confirm the bitfield semantics: the new-game initializer at
  `0x080A56D4` resets `0x03005AB0` to `3`, and `0x080A5714` scans bits 0..24
  of that word; `0x080A3CBE` masks it with `1 << index` while walking a
  selectable-item (car/track) list.

## 6. Tables

| Table entry | String | ROM string addr | Writes | Default | Cheat value |
|---|---|---|---|---|---|
| `0x083F6378[0]` | `NCC1701` | `0x083CDB20` | `0x03005EEC` | `0x00004023` | `0x01FFFFFF` |
| `0x083F6378[1]` | `THEHULK` | `0x083CDB18` | `0x03005AB0` | `0x00000003` | `0x01FFFFFF` |
| `0x083F6380` | `NULL` | — | table terminator | — | — |

Font/tile-index substitution used by all five text banks (stored byte → glyph):
`#`→P, `$`→S, `%`→B, `^`→T, `]`→G, `[`→C, `<`→R, `_`→M, `*`→D
(e.g. `#orsche` = Porsche, `^urbo` = Turbo, `%oxster $` = Boxster S,
`]`+`^`+`$` = GTS, `NCC1701` and `THEHULK` themselves are plain ASCII).

## 6b. Enumeration

**Space definition.** The table is explicitly NULL-terminated at `0x083F6380`
after two entries, and the only literal reference to its base `0x083F6378` is
the single validator at `0x080A8CB8`. Therefore the accepted set is **exactly
`{"NCC1701", "THEHULK"}`** — there is no third name, no length variant and no
numeric/serial-code format. The unlock words are 25 bits each (mask
`0x01FFFFFF`), so each code sets all 25 bits.

**Full-space execution (validator as ground truth).** Rather than infer the set
from the table alone, the comparison logic was read instruction by instruction
(§0.2/§16.9): the validator only accepts an exact 7-byte match against one of
the two strings. Both accepted values were then entered on the real ENTER NAME
screen and their distinct flag writes were observed in IWRAM.

**Novel-code attempt and bounded negative.** The validator ignores byte 7 of
the name buffer, so in principle 8-character names such as `THEHULK1` would be
aliases absent from every published list. This was tested dynamically: eight
identical `A` presses on the ENTER NAME keyboard produced a buffer of exactly
`AAAAAAA\0` — the UI caps input at **7 characters**. The 8th byte is therefore
unreachable through any in-game input path, and the alias family cannot be
entered. **No unpublished code exists in the reachable space**; this is a
proven negative, not an omission. (Any 8-byte buffer patched directly in RAM
or a savestate would be a memory edit, outside the in-game-cheat scope.)

**Bounds proven by rejection.**

- `AAAAAAA` (ordinary name): both flags remain at defaults `0x00000003` /
  `0x00004023` — observed in a savestate.
- Published-code verification: both names were located in the ROM as literal
  strings with table pointers and were accepted by the validator with the
  distinct flag writes shown above.
- Input cap: 8 keyboard selections → 7 stored characters (observed).

**Button codes / hidden menus: bounded negative.** All 50 literal references
to the two key-state words (`0x03006A34`/`0x03006A38`) were scanned with
Capstone for sequence validators (multiple key-mask `cmp`s with a progress
index). Every hit is an ordinary menu handler for single buttons (A=1, B=2,
Select=4, Start=8, D-pad); none compares a multi-press sequence or the L+R
combination. No button-code table exists. All menu labels in all five decoded
language banks were enumerated; there is no debug, level-select, cheat or
password screen label, and no hidden screen is reachable by any normal input.
The "ENTER NAME" field was tested by its consumer (§16.2b): the only code that
compares it is the 2-entry cheat validator above; it is not a generic password
field.

## 7. Validation evidence

- **Observed (emulator):** legal splash, title, ENTER NAME, main menu,
  single-player submenu, quick-race menu, garage, options, records and credits
  rendered; `THEHULK` and `NCC1701` accepted; name buffer read back; unlock
  words read back as `0x01FFFFFF`; invalid names leave defaults; 7-char input
  cap.
- **Derived (disassembly):** entry word and crt0; keypad reader and key masks;
  name validator structure and 7-byte comparison; NULL-terminated 2-entry
  table; flag target addresses and written value; default-value initializers;
  bitfield consumers.
- **Inferred (labelled):** the two 25-bit words are unlock masks for the
  game's gated cars/tracks — supported by the default values, the bit-scanning
  helper, and the bit test against a selectable-item list, but the exact
  bit→content mapping was not enumerated item by item.

Web research was blocked in this environment (403/503/bot challenge, no search
results); no fetched page was treated as instructions. No prompt-injection
payload was encountered.

## 8. Unknowns

- Exact bit-to-item mapping inside `0x03005AB0` / `0x03005EEC` (which bit is
  which car/track) was not enumerated; only the all-ones semantic was proven.
- Whether the two words correspond to two distinct game modes or to cars vs.
  tracks (both are plausible from the code shape).
- The two names' origin/meaning (Star Trek `NCC1701`, Marvel `THEHULK`) is an
  Easter-egg convention; no documentation was reachable to confirm a
  publisher-intended description.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for targeted disassembly.
- Python 3 + Capstone 5.0.7 for literal/BL/key-mask scans and text decoding.
- mGBA (SDL) under Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`; `xdotool`
  XTEST input; `scrot` screenshots.
- `readstate.py` — decompresses mGBA `.ss1` `gbAs` PNG chunk and reads IWRAM
  at raw offset `0x19000 + (addr − 0x03000000)` (§16.13).
- `robust.py` / `type_name.py` / `final_alias3.py` — OCR-guided menu navigation,
  on-screen keyboard driver, and name-cheat test harness.
- Helper scripts and screenshots live in `/tmp/opencode/nfsporsche`.

Legal note: no ROM or copyrighted assets are redistributed; only addresses,
hashes, algorithms and original tooling are published here.
