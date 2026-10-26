# Backyard Baseball 2006 (GBA) — Reverse Engineering Report

Status: complete. Scope: in-game / developer-intended cheats only. No GameShark,
CodeBreaker, Action Replay or other memory-edit codes are proposed or relied on.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Backyard Baseball 2006/Backyard Baseball 2006.gba` |
| Size | 4,194,304 bytes (0x400000, 32 Mbit) |
| Header title | `BASEBALL2006` |
| Game code | `BCYE` |
| Maker code | `70` |
| Software version | `0x00` |
| Entry branch | `0xEA00002E` (ARM branch to `0x080000C0`) |
| Fixed header byte 0xB2 | `0x96` |
| MD5 | `4f34ee4d9014cd0b9c6ae52df1f72af2` |
| SHA-1 | `33223f5b05ddf6ec10a41527bbc3001c6a5414cd` |
| SHA-256 | `a51c28f4e2f8a33cb214334ac8977fa05beff3249f64dbc2b13829a773bcf133` |

Embedded-header scan: searching the whole 4 MiB file for the 156-byte Nintendo
logo (`24 ff ae 51 ...`, the exact bytes at file `0x04`–`0x9F`) finds exactly one
occurrence, at file `0x04`. This is a single-image cartridge, not a multi-game
pack.

Header integrity caveat: the stored complement check (`0xBD`) is `0xC9` but the
computed value is `0xC5`, and the stored header checksum (`0xBE`) is `0x0000`,
which does not match the header data under the usual byte-sum or halfword-sum
methods. The image therefore has a modified/invalid GBA header even though it
boots (mGBA ignores these fields). All addresses and hashes in this report are
for the exact SHA-256 above; a different dump may differ.

## 2. Executive summary

Backyard Baseball 2006 has a season-mode **coach-name code system** with exactly
**nine hard-coded entries**. Entering one of them as the new coach's name (Season
Play → New Coach → Enter Name → Done) unlocks the corresponding "goodie" and
shows a `YOU HAVE UNLOCKED ...` message before the Set Rules screen.

Two entries are publicly documented:

* `BABYBEAR` → Sammy Sosa
* `BIGFISH`  → Dontrelle Willis

This analysis recovered the complete table and the other **seven codes**, none of
which appears as a code on GameFAQs, VGChartz, TCRF, SuperCheats, Vizzed,
CheatingDome or the other lists searched:

| Code | Effect |
|---|---|
| `NACHOS` | Abner Dubbleplay |
| `HOOPS` | Barry Dejay |
| `LIBERTY` | Jim Thome |
| `ANCHOVY` | Mike Piazza |
| `SPACEMAN` | Quantum Field |
| `SHOWTIME` | Humongous Memorial Stadium |
| `ATLANTIS` | Aquadome |

All nine entries were entered on a real emulated keyboard and all nine effects
were observed (screenshots in §6b). The validator is a plain 8-byte table
compare — there is no checksum, no generator and no second algorithmic format.
Accordingly the accepted set is exactly nine strings, and the 7 codes above are
the complete unpublished part of the space.

The ROM also contains a complete developer **`Cheat Manager v1.0`** with four
pages (unlock players/fields, speed/gravity modifiers, power-ups and season
jumps). It is real code and real UI text, but in this retail build it is
**unreachable**: its launcher at `0x0803696C` has zero BL/BLX/pointer references
anywhere in the 4 MiB image, and its gate compares a runtime word
(`0x03000B1C`) against the magic `0x3080`; no writer of that value was found and
the word read `0x0000` at every screen checked. It is documented here (addresses
and item list) as dead developer content, not as a usable cheat. The nine name codes above set the same nine unlock flags that
the Cheat Manager's page 2 would have set, so the retail game retains the
developer's unlock shortcuts but not the menu.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL frontend), headless Xvfb. The emulator binary on this
host is `/usr/games/mgba` (not on `PATH` by default). Display used: `:153`
(1024×768×24), window manager `openbox`.

Default mGBA SDL keymap used throughout:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |
| L / R | `a` / `s` (not needed) |

Hold keys for about 100–200 ms; the name-entry grid needs discrete presses.

### 3.1 Exact path to the code screen

1. Boot the ROM. Let the Atari and Humongous logos pass.
2. On the legal screen press **A** (`x`).
3. On the title screen press **Start** (`Return`).
4. Main Menu: **SEASON PLAY** (one **Down**, then **A**).
5. Team Dugout: **NEW COACH** is selected; press **A**.
6. The ENTER NAME screen appears. The cursor starts on `A`.

### 3.2 Entering a code

The on-screen keyboard is four rows plus a button row:

```
1 2 3 4 5 6 7 8 9 0 <
A B C D E F G H I J
K L M N O P Q R S T U
U V W X Y Z . , - ! #
[ DELETE ] [ SPACE ] [ DONE ]
```

`<` is the left-arrow symbol cell; it appends a special glyph (stored as `0x08`)
and is not used by any code. Use the D-pad to move,
**A** to select a character, then move down past row 4 to the button row
(DELETE is the left button), **Right** twice to **DONE**, and **A**. The unlock
message appears immediately on a match, before SET RULES.

A one-character name plus DONE proves the path (Set Rules appears with no
unlock). For a negative test use `OCTOBER` (seven characters, present in ROM text
but deliberately not in the pointer table), `BABY` (prefix of `BABYBEAR`) or
`ZZZZZZZZ`; none produces an unlock message.

### 3.3 Published codes tested

| Code | Result |
|---|---|
| `BABYBEAR` | Accepted; `YOU HAVE UNLOCKED SAMMY SOSA` |
| `BIGFISH` | Accepted; `YOU HAVE UNLOCKED DONTRELLE WILLIS` |

Both match the GameFAQs/VGChartz lists and both are in the ROM table.

### 3.4 Rejection tests

| Input | Length | Result |
|---|---|---|
| `OCTOBER` | 7 | No unlock; proceeds to SET RULES |
| `BABY` | 4 | No unlock (no prefix matching); retested in a fresh session so the Sammy Sosa flag was still clear (`shots/113_baby_fresh.png`) |
| `ZZZZZZZZ` | 8 | No unlock |
| `SPACEMAN` as a Link Play *player* name | 8 | No unlock (validator is in the season coach-name path, not player-name entry) |

Screenshots: `shots/50_october_result.png`, `shots/78_baby_prefix.png`,
`shots/79_zzzz.png`, `shots/92_player_spaceman.png` in the work directory
`/tmp/opencode/bb2006`.

## 4. Address map

All ROM addresses are `0x08000000 + file_offset`.

| Item | ROM address | File offset | Notes |
|---|---:|---:|---|
| Name pointer table (9 × u32) | `0x083D7CF4` | `0x3D7CF4` | Entries point to the 9 code strings |
| Code string pool | `0x08136EB8`–`0x08136EFC` | `0x136EB8`–`0x136EFC` | Encoded `ASCII-0x21`, `0x5E` terminator |
| Unused decoy string `OCTOBER` | `0x08136EB0` | `0x136EB0` | Not referenced by the table; rejected in-game |
| String compare (8-byte, `0x5E`-aware) | `0x080249F0` | `0x249F0` | Byte loop; returns 1 on equal or on `0x5E` |
| Compare instruction that reads code byte | `0x08024A12` | `0x24A12` | `cmp r0,r1` inside the loop |
| Cheat-state builder / table loop | `0x08036678` | `0x36678` | Loops i = 0..8, calls `0x080249F0`, sets bit i |
| Name-entry UI / commit | `0x08030000`–`0x08030B40` | `0x30000`–`0x30B40` | On-screen keyboard, DELETE/SPACE/DONE, text render |
| Confirm/commit helper | `0x080306C0` | `0x306C0` | Stores destination pointer and length; copy follows |
| Copy/pad to profile field | `0x0803072C` | `0x3072C` | Copies from `0x03003EE0`, pads with `0x5E` |
| Name input buffer (8 bytes) | `0x03003EE0` | RAM | Letters/digits = ASCII − `0x21`; SPACE `0x00`; `<` `0x08` |
| Name length (u8) | `0x03003ECC` | RAM | 0..8 |
| Profile destination pointer | `0x03003F04` | RAM | Set at confirm; points at `0x03002F10` |
| Committed/padded name field | `0x03002F10` | RAM | 8 bytes, pre-filled `0x5E`; comparator operand |
| Cheat flag word | `0x03003F60` | RAM | Name bits are merged at bits 9..17 |
| Cheat-state applier | `0x0801BC9C` | `0x1BC9C` | Consumes the merged cheat state |
| Input/state register copy | `0x03003230` | RAM | 16-bit/structured state used by applier |

### 4.1 Cheat Manager (developer debug menu, unreachable)

| Item | ROM address | File offset | Notes |
|---|---:|---:|---|
| Launcher / gate | `0x0803696C` | `0x3696C` | Checks `*(u16*)0x03000B1C == 0x3080`, then calls main |
| Cheat Manager main | `0x08037EE8` | `0x37EE8` | 4-page UI, `Cheat Manager v1.0` |
| Page init table (4 × u32) | `0x083DA37C` | `0x3DA37C` | `0x08038361`, `0x08038389`, `0x080371C5`, `0x08037541` |
| Page draw/input table (4 × u32) | `0x083DA39C` | `0x3DA39C` | `0x08036F75`, `0x08037095`, `0x08037405`, `0x08037AB1` |
| Helper table (5 × u32) | `0x083DA3AC` | `0x3DA3AC` | `0x08036BD1`, `0x08036C7D`, `0x08036DA1`, `0x08036DA1`, `0x0803835D` |
| Gate word | `0x03000B1C` | RAM | Read as u16; observed `0x0000` at main menu and pause |
| ASCII UI strings | `0x08041F50`–`0x08042414` | `0x41F50`–`0x42414` | Plain ASCII, unlike the retail vector-font UI |

## 5. Algorithm

### 5.1 Character encoding

The name-entry screen stores each character as one byte. For letters and digits:

```
stored = ascii - 0x21
```

Two UI symbols are special-cased: the SPACE button stores `0x00`, and the
left-arrow `<` cell stores `0x08`. `0x5E` (ASCII `^` position) is the
terminator/pad byte. Examples:

| Character | ASCII | Stored |
|---|---:|---:|
| `A` | 0x41 | 0x20 |
| `B` | 0x42 | 0x21 |
| `Y` | 0x59 | 0x38 |
| `Z` | 0x5A | 0x39 |
| `N` | 0x4E | 0x2D |

This was confirmed in RAM: with `ZZZZZZZZ` on screen, IWRAM `0x03003EE0`
contained `39 39 39 39 39 39 39 39` and the length at `0x03003ECC` was `0x08`.
At screen init the committed field `0x03002F10` is eight `0x5E` bytes; on DONE,
`0x0803072C` copies the input there and pads the remainder with `0x5E`.

### 5.2 Comparator

`0x080249F0(a, len_a, b, len_b)` is the `0x5E`-terminated equality routine:

```c
int streq8(const uint8_t *a, uint8_t len_a,
           const uint8_t *b, uint8_t len_b) {
    uint8_t n = min(len_a, len_b);
    for (uint8_t i = 0; i < n; i++) {
        uint8_t ca = a[i], cb = b[i];
        if (ca != cb) return 0;
        if (ca == 0x5E) return 1;   /* terminator/pad on both sides */
    }
    return 1;                        /* n bytes equal */
}
```

The game calls it with `len_a = 8`, `len_b = 8`, `b = 0x03002F10` (committed
name field; `0x080245F0` simply returns that pointer), `a = table[i]` (ROM). The
compare loop is at `0x08024A0A`–`0x08024A26`; the compared byte load is
`0x08024A12`.

### 5.3 Table loop and flag merge

At `0x08036736`:

```c
uint16_t matched = 0;
for (int i = 0; i <= 8; i++) {
    const uint8_t *code = *(const uint8_t **)(0x083D7CF4 + 4*i);
    if (streq8(code, 8, (const uint8_t *)0x03002F10, 8))
        matched |= (uint16_t)(1u << i);
}
/* merge with button/state bits, then shift name bits to 9..17 */
flags = (flags & ~matched) | (matched << 9);   /* 0x03003F60 */
apply_cheat_state();                            /* 0x0801BC9C */
```

So table index *i* is flag bit *i*; all nine name matches occupy bits 9..17 of
the cheat-state word. The applier at `0x0801BC9C` then writes the corresponding
profile/unlock fields.

### 5.4 Why the accepted set is finite

There is no arithmetic, checksum, XOR key or generator anywhere in the path: the
only comparison is `streq8` against the nine pointers. Consequently exactly nine
strings are accepted, regardless of the theoretical name space.

## 6. Tables

### 6.1 The nine coach-name codes

| # | Code | ROM address | Encoded bytes | Bit | Unlock effect | Published as a code? |
|---:|---|---|---|---:|---|---|
| 0 | `NACHOS` | `0x08136EB8` | `2D 20 22 27 2E 32 5E` | 0 | Abner Dubbleplay | No |
| 1 | `HOOPS` | `0x08136EBF` | `27 2E 2E 2F 32 5E` | 1 | Barry Dejay | No |
| 2 | `BIGFISH` | `0x08136EC5` | `21 28 26 25 28 32 27 5E` | 2 | Dontrelle Willis | Yes (GameFAQs/VGChartz) |
| 3 | `LIBERTY` | `0x08136ECD` | `2B 28 21 24 31 33 38 5E` | 3 | Jim Thome | No |
| 4 | `ANCHOVY` | `0x08136ED5` | `20 2D 22 27 2E 35 38 5E` | 4 | Mike Piazza | No |
| 5 | `BABYBEAR` | `0x08136EDD` | `21 20 21 38 21 24 20 31` | 5 | Sammy Sosa | Yes (GameFAQs/VGChartz) |
| 6 | `SPACEMAN` | `0x08136EE5` | `32 2F 20 22 24 2C 20 2D` | 6 | Quantum Field | No |
| 7 | `SHOWTIME` | `0x08136EED` | `32 27 2E 36 33 28 2C 24` | 7 | Humongous Memorial Stadium | No |
| 8 | `ATLANTIS` | `0x08136EF5` | `20 33 2B 20 2D 33 28 32` | 8 | Aquadome | No |

The pointer array at `0x083D7CF4` is exactly:

```
0x08136EB8 0x08136EBF 0x08136EC5 0x08136ECD 0x08136ED5
0x08136EDD 0x08136EE5 0x08136EED 0x08136EF5
```

The byte string `OCTOBER` at `0x08136EB0` is not pointed to by this array and was
rejected in the emulator; it is a decoy/neighbour string, not a tenth code.

### 6.2 Cheat Manager item list (derived from ROM text at `0x08041F50`)

The complete menu text, retained as ASCII, is:

**Page 1**
* `Cheat Manager v1.0`
* `^or_=Select cheat item, <or>=Change item content`
* `{=Accept changes, }=Discard changes, [or]=Flip page`
* `Page 1 of 4`
* `ROM Version: Bb2AGB-065`
* `Remain Ext. Work RAM: ?????`
* `Corrupt save file`

**Page 2 (unlock flags; same nine goodies as the name codes)**
* `Un-lock ABNER DUBBLEPLAY`
* `Un-lock BARRY DEJAY`
* `Un-lock DONTRELLE WILLIS`
* `Un-lock JIM THOME`
* `Un-lock MIKE PIAZZA`
* `Un-lock SAMMY SOSA`
* `Un-lock QUANTUM FIELD`
* `Un-lock HUMONGOUS MEMORIAL STADIUM`
* `Un-lock AQUADOME`

**Page 3 (gameplay modifiers)**
* `Runner Base Speed`
* `Runner Speed Modifier`
* `Fielder Base Speed`
* `Fielder Speed Modifier`
* `Ball Fly Time Multiplier`
* `Ball Throw Time Multiplier`
* `Gravity`
* `Get all pitching power-ups`
* `Get all batting power-ups`

**Page 4 (season jumps; enabled only in a season game)**
* `Season game cheat...`
* `This page will only be enabled when playing season game.`
* `Don't change season week`
* `Advance to middle season game`
* `Advance to last season game (winning)`
* `Advance to last season game (losing)`
* `Advance to division playoffs (begin)`
* `Advance to division playoffs (end)`
* `Advance to league championship (begin)`
* `Advance to league championship (end)`
* `Advance to world series (begin)`
* `Advance to world series (end)`

The menu is real code (`0x08037EE8`, 4 page functions, 4 draw/input functions,
5 helpers). It is not reachable in normal play — see §6b.4.

## 6b. Enumeration

### 6b.1 Space definition

* Input surface: the season **coach name** field only.
* Alphabet: 43 selectable symbols — 42 grid cells (`A`–`Z`, `0`–`9`,
  `<`/left-arrow, `.`, `,`, `-`, `!`, `#`) plus the SPACE button. The `<` cell
  appends a special glyph stored as `0x08`; it is not used by any code. For
  letters and digits the storage is `ASCII − 0x21`.
* Length: 1–8 characters; the UI refuses a ninth character. Observed: after
  nine keypresses the length byte at `0x03003ECC` stayed `0x08` and the buffer
  held only eight bytes (`20 21 08 08 08 08 08 08`)
  (`shots/112_cap.png`).
* Storage: one byte per character; `ASCII − 0x21` for letters/digits, `0x00`
  for SPACE, `0x08` for `<`, with `0x5E` terminator/pad.
* Representable strings: `Σ(43^k, k=1..8) = 11,966,490,760,400` (≈1.20 × 10^13).
* Accepted values: **exactly 9**, the pointer table above. There is no
  checksum, key, or generator that would make other strings valid.

### 6b.2 Novel codes (absent from every published list searched)

Each was entered through the real on-screen keyboard and confirmed by the
in-game unlock message. Screenshot paths are relative to
`/tmp/opencode/bb2006/`.

| Novel code | Bit | Observed effect | Screenshot |
|---|---:|---|---|
| `NACHOS` | 0 | `YOU HAVE UNLOCKED ABNER DUBBLEPLAY` | `shots/70_nachos.png` |
| `HOOPS` | 1 | `YOU HAVE UNLOCKED BARRY DEJAY` | `shots/71_hoops.png` |
| `LIBERTY` | 3 | `YOU HAVE UNLOCKED JIM THOME` | `shots/72_liberty.png` |
| `ANCHOVY` | 4 | `YOU HAVE UNLOCKED MIKE PIAZZA` | `shots/73_anchovy.png` |
| `SPACEMAN` | 6 | `YOU HAVE UNLOCKED QUANTUM FIELD` | `shots/74_spaceman.png` |
| `SHOWTIME` | 7 | `YOU HAVE UNLOCKED HUMONGOUS MEMORIAL STADIUM` | `shots/75_showtime.png` |
| `ATLANTIS` | 8 | `YOU HAVE UNLOCKED AQUADOME` | `shots/76_atlantis.png` |

The two published codes were re-tested for completeness:

| Published code | Bit | Observed effect | Screenshot |
|---|---:|---|---|
| `BABYBEAR` | 5 | `YOU HAVE UNLOCKED SAMMY SOSA` | `shots/59_unlock.png`, `shots/67.png` |
| `BIGFISH` | 2 | `YOU HAVE UNLOCKED DONTRELLE WILLIS` | `shots/77_bigfish.png` |

After entering all nine, the Extras → Unlockable Goodies list shows all nine
entries unlocked (portraits/field icons instead of `?`):
`shots/100_goodies_all.png`, `shots/101_goodies_all2.png`.

### 6b.3 Bounds proven by rejection

| Test value | Why it is outside the accepted set | In-game result |
|---|---|---|
| `OCTOBER` | 7 chars, present at `0x08136EB0`, not in the pointer table | No unlock; SET RULES appears (`shots/50_october_result.png`) |
| `BABY` | Valid prefix of `BABYBEAR`; comparator has no prefix mode. Retested after a reset with Sammy Sosa still locked | No unlock (`shots/113_baby_fresh.png`; earlier `shots/78_baby_prefix.png`) |
| `ZZZZZZZZ` | Valid 8-char string, not in table | No unlock (`shots/79_zzzz.png`) |
| `SPACEMAN` (Link Play player name) | Wrong entry point; validator is in the season coach-name path | Accepted as a link profile name, no unlock (`shots/92_player_spaceman.png`) |

These four rejections bound the system from both directions: a string can be
well-formed and even share a prefix with a valid code and still be rejected, and
the same string is inert on a different name-entry screen.

### 6b.4 Cheat Manager reachability (negative result, bounded)

The developer menu is **not** reachable in this build:

* Static: a full scan of all 4,194,304 bytes for Thumb `BL`/`BLX`, ARM `BL`/`BLX`
  and 32-bit little-endian pointers targeting `0x0803696C` / `0x0803696D`
  returns **zero** hits. The only caller of the menu main `0x08037EE8` is
  `0x0803698A`, inside the unreferenced launcher.
* Gate: the launcher reads a u16 at `0x03000B1C` and requires `0x3080`. No
  writer of `0x3080` to that word was identified; the word read `0x0000` at the
  main menu and at the pause menu, and the menu's gate never fired.
* Dynamic: hardware breakpoints on `0x0803696C` and `0x08037EE8` were installed
  and the following screens were traversed without a hit: title, legal screen,
  main menu, Pick-up Game rules/matchup/gameplay, pause menu and its quit
  confirmation, Season Play → Team Dugout → New Coach → Enter Name → Set Rules,
  Mini Games, Link Play → player-name → Link menu, Options, Extras (Player Cards
  `shots/122_playercards.png`, BBL Champions `shots/123_champions.png`,
  Unlockable Goodies, Credits `shots/124_credits.png`).
* The Cheat Manager's page 2 would set the same nine unlock flags that the name
  codes set, but no in-game path reaches it. It is reported as dead developer
  content, not as a cheat.

### 6b.5 Button-code search (negative)

No button-code cheat system was found:

* No published button code for this game appears on GameFAQs, VGChartz, TCRF or
  the other lists searched; the only public input codes are the two coach names.
* Static search found no contiguous array of 16-bit key masks and no
  prefix/index button-sequence table. The only input-driven cheat path is the
  name comparison at `0x08036678`; its other bits are game-state conditions, not
  a key sequence.
* Dynamic: the Konami sequence (`Up Up Down Down Left Right Left Right B A`) at
  the main menu produced no screen change (`shots/117_konami.png`). Holding
  L+R+Start at the main menu did not open a hidden menu; it produced the normal
  "start a game" transition (`shots/118_lrstart.png`). Breakpoints on the Cheat
  Manager stayed silent throughout.

The Cheat Manager's page 3/4 items are menu entries in unreachable code, not
button codes.

## 7. Validation evidence

**Observed (emulator screenshots / memory reads)**

* `BABYBEAR` → Sammy Sosa, `BIGFISH` → Dontrelle Willis, and the seven novel
  codes → their listed goodies; all nine messages were captured.
* After all nine, Unlockable Goodies shows all nine entries unlocked.
* `OCTOBER`, `BABY`, `ZZZZZZZZ` and a player-name `SPACEMAN` do not unlock.
* IWRAM `0x03003EE0` holds `39 39 39 39 39 39 39 39` for `ZZZZZZZZ`, and
  `0x03003ECC` holds `08`.
* `0x03000B1C` read `0x0000` at the main menu and pause; no Cheat Manager screen
  was reachable through any menu.
* Header fields and hashes in §1 were read directly from the file.

**Derived (instruction/table analysis)**

* The 9-entry pointer array at `0x083D7CF4` and the nine encoded strings.
* `0x080249F0` is an 8-byte, `0x5E`-aware equality function; the call at
  `0x0803674C` passes `8, 8` and the current name pointer.
* The loop at `0x08036736` sets bit *i* for table entry *i*; the merge at
  `0x08036804` shifts those bits to 9..17 in `0x03003F60`.
* The Cheat Manager launcher has no references; its gate is `0x3080` at
  `0x03000B1C`.

**Inferred**

* The exact mapping from the nine bits to the profile/season fields (the applier
  at `0x0801BC9C` is large and was not fully reimplemented; the effects were
  observed instead).
* The intended effects of Cheat Manager pages 3–4 (strings and code structure
  only; not exercised, because the menu is unreachable).
* The origin of the invalid GBA header checksum (likely a patch/trim, not proven).

## 8. Unknowns

* Whether the Cheat Manager is reachable in a prototype/dev build, through a
  development cartridge, or by a value written by hardware this image does not
  contain. In this image it is dead code.
* The precise writer/semantics of `0x03000B1C`; it behaves like an audio/palette
  runtime word, and no path sets it to `0x3080`.
* Whether the nine unlock flags persist in SRAM across power cycles; the session
  flags were observed, but save persistence was not isolated from the emulator's
  `.sav` state.
* Regional/revision differences. All findings are for SHA-256
  `a51c28f4...bcf133`; the invalid header suggests this dump may be patched.

## 9. Tooling

* mGBA 0.10.5 SDL (`/usr/games/mgba`), `-3` scale, `SDL_AUDIODRIVER=dummy`.
* Xvfb `:153` (1024×768×24) + openbox; `xdotool` for input; ImageMagick
  `import` for screenshots.
* `gdb-multiarch` against mGBA's `-g` stub (port 2345): hardware read
  watchpoints on `0x03003EE0`, `0x03003F04` and `0x08136ED8`–`0x08136EE0`
  identified the comparator and the table accesses; EWRAM/IWRAM dumps were
  compared between `A`, `AB` and `ZZZZZZZZ` states.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* Python 3 for table decoding, pointer scans, BL/BLX scans and hash/header work.
* Helper scripts in `/tmp/opencode/bb2006`: `key.py` (press helper),
  `type_name.py` (grid navigation + DONE), `next_test.py` (message → next code).

Minimal table reproducer (prints the nine codes from the ROM directly):

```python
import struct
rom = open("Backyard Baseball 2006.gba", "rb").read()
PTR = 0x3D7CF4                     # file offset of 0x083D7CF4
for i in range(9):
    addr = struct.unpack_from("<I", rom, PTR + 4*i)[0] - 0x08000000
    s = rom[addr:addr+8].split(b"\x5e")[0]
    print(i, "".join(chr(c + 0x21) for c in s))
```

Output:

```
0 NACHOS
1 HOOPS
2 BIGFISH
3 LIBERTY
4 ANCHOVY
5 BABYBEAR
6 SPACEMAN
7 SHOWTIME
8 ATLANTIS
```

Legal note: no ROM, extracted graphics, music or other copyrighted assets are
redistributed here. Only hashes, addresses, algorithms, the nine short
developer-authored code words and my own screenshots/notes are published.

## 10. Reproduction checklist

- [x] Hash and header the ROM; exact SHA-256 recorded.
- [x] Search strings and locate the ASCII Cheat Manager remnants.
- [x] Search web for published codes; verify `BABYBEAR` and `BIGFISH` in ROM and
      emulator.
- [x] Boot on a private display; walk title, main, every mode, options, extras,
      name entry, gameplay and pause.
- [x] Locate the 9-entry table, comparator and bit merge.
- [x] Enumerate all nine entries and observe all nine effects.
- [x] Enter seven codes that appear in no published list.
- [x] Prove bounds with four rejected inputs.
- [x] Prove the Cheat Manager unreachable (zero xrefs + no dynamic hit).
- [x] Write this report next to the ROM.
- [x] Stop only this session's mGBA/gdb/Xvfb/openbox processes by PID.
