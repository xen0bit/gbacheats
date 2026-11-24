# DK: King of Swing (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/DK: King of Swing/DK: King of Swing.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `KINGOFSWING` |
| Game code | `BBKE` (maker `01`, i.e. `BBKE01`) |
| Version | 0 (Rev.00) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock GBA branch) |
| MD5 | `054223e916f9a4f543812ae795145cb5` |
| SHA-1 | `8f8b10b09d5169b097840df36cca5c67c216beda` |
| SHA-256 | `f24ee049e02652e4a6590a1566904a1ab8a5db880a4ea0ab5e2cda01c4874f5d` |

Header notes (Observed):

* Nintendo logo at `0x04`–`0x9F` is the standard logo; the entry branch and the
  first crt0 bytes (`0x080000C0` onward) are stock. No cracktro, no appended
  trainer, and the literal strings `CRC BANDIT`, `SUNHORS`, `MODE7`, `TRAINER`
  and `PATCH` are absent from the whole image.
* The header checksum field at `0xBE` is `0x0000` and the complement byte at
  `0xBD` is `0x96`; that value equals the checksum computed over `0xA0–0xBC`,
  not the standard complement sum over `0x00–0x9C` (which computes `0x87`).
  This is a rebuilt-header artifact also present in other images of this local
  collection; it is not a DK-specific patch. The executable content and save
  format behave normally.
* Embedded-header scan: the exact 156-byte Nintendo logo occurs at `0x04`,
  `0x66F4EC` and `0x6716C0`. The latter two are two additional complete
  `KINGOFSWING`/`BBKE01` headers at file offsets `0x66F4E8` and `0x6716BC`.
  Both are small multiboot/link stubs: their crt0 literal is not a plausible
  `main` pointer, and neither contains the password table, the password text,
  or any `password` string. They are not a second playable image.

## 2. Executive summary

The game has one in-game cheat surface: a hidden **password screen** reached
from the **title screen** by holding `L + Up + B` and then pressing `A`. The
screen accepts exactly **eight decimal digits (0–9)**, packs them as packed BCD
into one 32-bit word, and compares that word against a **three-entry table**:

| Input | Effect (ROM message) | Save flag |
|---|---|---|
| `65942922` | “Attack Battle 3 has been added to the Single-Player and Multiplayer Jungle Jams!” | flag byte 0 |
| `35805225` | “Obstacle Race 4 has been added …” | flag byte 1 |
| `55860327` | “Climbing Race 5 has been added …” | flag byte 2 |

There is **no checksum, no key table, no generator and no reserved bit**: the
validator is an exact 32-bit equality loop over those three constants. The
entire input space is 10⁸ = 100,000,000 values and the accepted set is exactly
those three values. All three are on GameFAQs and the Donkey Kong Wiki; the
published list is complete and correct for this ROM. Consequently **no
unpublished 8-digit password can exist** — this is an enumerated closed set,
not an untested gap (see §6b for the exhaustive run and the rejection tests).

The title gate itself is a button-code check and *is* broader than the published
text: it tests `(held & 0x243) == 0x243`, i.e. it requires the bits A, B, Up and
L and ignores every other button except that Start takes its own file-select
path first. An **unpublished combination, `L + Up + B + R + A`**, therefore opens
the same hidden screen and was confirmed in the emulator (§6b). That is the
novel accepted input for this title; the password set remains closed.

The three flags live at the end of the 0x3420-byte save block
(`0x0203F410`, SRAM `0x0E003410`), outside the per-file records, so they are
global rather than per-file. The game writes the save immediately when a
password succeeds (`0x08502C5C`), and on the next boot copies the 8-byte flag
field to IWRAM `0x030004F0`/`0x030004F4`.

## 3. How to reproduce

Emulator/tooling:

```bash
Xvfb :276 -screen 0 1024x768x24 &
DISPLAY=:276 openbox &
DISPLAY=:276 SDL_AUDIODRIVER=dummy mgba -3 "DK: King of Swing.gba" &
```

mGBA SDL default keys used: **A = `x`**, **B = `z`**, **L = `a`**, **R = `s`**,
**Start = `Return`**, **Select = `BackSpace`**, D-pad = arrow keys. Hold keys
for 60–200 ms; a 10 ms tap is sometimes missed.

Observation method (no screenshots were used): `Shift+F1`…`Shift+F10` save a
state, `F1`…`F10` load it. An mGBA `.ssN` is a PNG whose `gbAs` chunk is a
zlib-compressed 397,312-byte raw state. In this build the sections used were:

| Section | Offset in raw state |
|---|---|
| VRAM | `0x01000` |
| IWRAM (`0x03000000`) | `0x19000` |
| EWRAM (`0x02000000`) | `0x21000` |

Exact route used:

1. Boot and wait ~10 s. The screen-state byte `0x03000002` goes
   `27` (boot init) → `0` (logos) → `1` (**title screen**). Three `Start`
   presses over the intro reach state 1.
2. At state 1, hold `a` (L), `Up`, `z` (B), then press and hold `x` (A).
   On the next frame `0x03000002` becomes **`0x17` (23)**, the password screen.
3. The password screen object is allocated in EWRAM (base `0x02012000` in all
   fresh title-gate runs; one menu-heavy session used `0x02033000`). Stable
   fields: `+0x80` current digit, `+0x94` index 0–8, `+0x95` success byte,
   `+0xFC` packed-BCD word.
4. Digit entry: `Down`/`Right`/`R` increment the digit, `Up`/`Left`/`L`
   decrement it, `A` (or `Start`) commits the digit and advances the index,
   `B` backspaces. After the eighth commit the screen's internal state becomes
   3 and the validator runs.
5. Read the flags at EWRAM `0x0203F410` and the success byte at object `+0x95`.
   The SRAM file (`rom.sav`, 32 KiB) can be checked directly at offset
   `0x3410`.

Navigation routes verified by state byte (Observed):

| Screen | State (`0x03000002`) |
|---|---|
| Boot / logos | 27, 0 |
| Title | 1 |
| “Please select a file to play.” (file select) | 12 |
| Main menu (Adventure / Single JJ / Multi JJ / Extras) | 2 |
| Adventure entry | 3 |
| Extras (Cranky / Time Attack / Diddy) | 5 |
| Single Jungle Jam entry | 15 |
| Jungle Jam event grid | 8 |
| Multiplayer Jungle Jam link screen | 19 |
| Hidden password screen | 23 (`0x17`) |

Main-menu destinations are selected in `[fp+0x80]`; the confirm/key test is at
`0x08527694` and the selection branches at `0x085276A8–0x08527760` map
0→state 3, 1→state 15, 2→state 19, 3→state 5. State 1 → 12 on A; 12 → 2 on A.

## 4. Address map

File offset = ROM address − `0x08000000`.

| File offset | Address | Meaning |
|---:|---|---|
| `0x0002D0` | `0x080002D0` | State dispatcher: `ldrb r0,[0x03000002]`, `ldr r0,[table+r0*4]`, `bx r0` |
| `0x000394` | `0x08000394` | 30-entry screen-state table (state 23 entry at `0x080003F0`) |
| `0x523F6C` | `0x08523F6C` | Title-screen hidden-button gate |
| `0x524048` | `0x08524048` | Literal `0x00000243` (L\|Up\|B\|A) |
| `0x524054` | `0x08524054` | `state = byte_table[[fp+0xFF]]` |
| `0x524068` | `0x08524068` | State selector bytes `0c 0c 17 00` (index 2 → `0x17`) |
| `0x6E6224` | `0x086E6224` | Password screen init (clears digit buffer, loads text) |
| `0x6E6248` | `0x086E6248` | Three packed-BCD password constants |
| `0x6E6254` | `0x086E6254` | Message-pointer table: 3 success pointers, 2 zero, wrong, already |
| `0x6E644C` | `0x086E644C` | Password entry/update (keys, digit select, insert/backspace) |
| `0x6E6620` | `0x086E6620` | Digit insert: `word \|= digit << ((7-index)*4)` |
| `0x6E66DC` | `0x086E66DC` | Validator and unlock/duplicate dispatch |
| `0x6E6944` | `0x086E6944` | Literal pointer to table `0x086E6248` |
| `0x6E6948` | `0x086E6948` | Literal pointer to flags `0x0203F410` |
| `0x6E6954` | `0x086E6954` | Literal pointer to messages `0x086E6254` |
| `0x657EF2` | `0x08657EF2` | “Please enter a password.” |
| `0x657F22` | `0x08657F22` | “Wrong password!” |
| `0x657F49` | `0x08657F49` | “This password has already been entered.” |
| `0x6582CB` | `0x086582CB` | “Attack Battle 3 has been added …” |
| `0x658331` | `0x08658331` | “Obstacle Race 4 has been added …” |
| `0x658397` | `0x08658397` | “Climbing Race 5 has been added …” |
| `0x502C5C` | `0x08502C5C` | Save routine (checksum + SRAM write at `0x0E000000`) |
| `0x502D20` | `0x08502D20` | Copy `0x0203F410..F417` → `0x030004F0/F4` after load |

RAM / SRAM:

| Address | Meaning |
|---|---|
| `0x03000002` | Current screen state byte |
| `0x03000040` | Held key state (active-high, 10 bits) |
| `0x03000042` | Newly pressed keys |
| `0x030004F0` | Copy of the 4 password-flag bytes (bit 0 = code 0, etc.) |
| `0x030004F4` | Copy of flag bytes 4–7 (unused: all zero) |
| `0x0203C000` | 0x3420-byte save block in RAM |
| `0x0203F410` | 3 password flags (+ 5 unused bytes) |
| `0x02012000` | Password screen object (base varies with allocation) |
| `0x0E000000` | 32 KiB SRAM |
| `0x0E003410` | Persistent password flags in SRAM |

## 5. Algorithm

### 5.1 Title gate

```c
held  = *(u16*)0x03000040;       // active-high key bits
pressed = *(u16*)0x03000042;
if ((held & 0x0243) == 0x0243) { // L=0x200, Up=0x040, B=0x002, A=0x001
    flag = 2;                    // [fp+0xFF] = 2
} else {
    flag = (pressed & 0x0009) ? 1 : 0;   // A/Start normal start path
}
// later: state = selector[flag];  selector = {0x0C, 0x0C, 0x17, 0x00}
// flag 2 -> state 0x17 = password screen
```

The mask test ignores every other held bit. `Start` is not harmless in
practice: the title also advances to file-select (state 12) when Start is
pressed, which pre-empts the gate (Observed with `0x24B`). `R` is ignored and
is a safe extra (Observed with `0x343`).

### 5.2 Password entry

```c
word = 0; index = 0; digit = 0;
while (index < 8) {
    if (pressed & (A|Start)) {          // 0x0009
        word = (word & ~(0xF << ((7-index)*4)))
             | ((digit & 0xF) << ((7-index)*4));
        index++;
    }
    if (pressed & B) {                  // 0x0002
        if (index > 0) index--;
    }
    if (held & 0x0190) digit = (digit + 1) % 10;  // R, Down, Right
    if (held & 0x0260) digit = (digit + 9) % 10;  // L, Up, Left
}
validate(word);
```

The insert uses `BIC` + `ADD` with a 0–9 digit, which is equivalent to OR.
The initial word is zeroed by the screen init (`str r1,[fp,#0xFC]`).

### 5.3 Validator

```c
u32   table[3] = {0x65942922, 0x35805225, 0x55860327};  // ROM 0x086E6248
u8   *flags   = (u8*)0x0203F410;                          // save block +0x3410
const char **msgs = ...;                                  // ROM 0x086E6254
int msg;
for (int i = 0; i < 3; i++) {
    if (word == table[i]) {
        u8 old = flags[i];
        flags[i] = 1;
        if (old) { msg = 6; success = 0; }   // "already been entered."
        else     { msg = i; success = 1; save_game(); }
        break;
    }
}
if (no match) msg = 5;                       // "Wrong password!"
display(msgs[msg]);                          // msg[0..2]=unlock, 5=wrong, 6=already
```

`save_game()` (`0x08502C5C`) sums the 0x3420-byte block, stores the checksum at
`+0x341C`, and writes the block to SRAM `0x0E000000`. `flags` is at block
offset `0x3410`, i.e. after the three 0xD00-byte file records (the loader
multiplies a file index by `0xD00` at `0x08502CF8`), so the unlock is global.

## 6. Tables

### 6.1 Password constants (`0x086E6248`)

Little-endian bytes shown as stored; value is the BCD word compared by the ROM.

| i | Bytes at `0x086E6248+4i` | BCD value | Published meaning | Message pointer |
|---:|---|---|---|---|
| 0 | `22 29 94 65` | `0x65942922` | Attack Battle 3 | `0x086582CB` |
| 1 | `25 52 80 35` | `0x35805225` | Obstacle Race 4 | `0x08658331` |
| 2 | `27 03 86 55` | `0x55860327` | Climbing Race 5 | `0x08658397` |

The pointer table at `0x086E6254` continues: `+0x0C` is zero, `+0x10` is
zero, `+0x14` is `0x08657F22` (“Wrong password!”) and `+0x18` is `0x08657F49`
(“This password has already been entered.”).

The ROM labels match the GameFAQs labels exactly. No published code was
rejected and no typo was found.

### 6.2 Flag bytes

| Byte | Code | Meaning |
|---:|---|---|
| 0 | `65942922` | Attack Battle 3 unlocked |
| 1 | `35805225` | Obstacle Race 4 unlocked |
| 2 | `55860327` | Climbing Race 5 unlocked |
| 3–7 | — | Unused, always `0x00` in every observed state; the loader copies all 8 to `0x030004F0/F4` |

### 6.3 Other unlockables (save/medal flags, not codes)

The same message bank records the medal/Crystal-Coconut unlocks. These are
save-state bits, not input codes: Time Attack after beating the game
(`0x08657E1E`), Diddy Mode after all medals (`0x08657E96`), Kremling at 6 gold
medals (`0x08657D84`), K. Rool at 12 gold medals (`0x08657DD1`), Wrinkly at
20 Crystal Coconuts (`0x0865852D`), Bubbles after all medals in Diddy Mode
(`0x086585C5`). No button sequence or password is associated with them in the
ROM; they are written by gameplay results and tested as save bits (Derived).

## 6b. Enumeration

### 6b.1 Password space

* Alphabet: `0`–`9` (10 symbols, enforced by the digit increment/decrement
  wrap in `0x086E6620`: values <0 become 9, values >9 become 0).
* Length: 8 symbols. Representation: one packed-BCD 32-bit word, one nibble
  per symbol, most significant nibble = first symbol.
* Space size: **10⁸ = 100,000,000** values. There is no checksum, no key,
  no reserved bit and no generator.
* Accepted set: exactly the 3 table entries above. An exhaustive C program
  (`enum.c`) read the three constants from the ROM at `0x6E6248` and evaluated
  all 100,000,000 digit strings against the same exact-equality predicate
  used by the ROM:

  ```
  table: 65942922 35805225 55860327
  MATCH 35805225 = 0x35805225 idx 1
  MATCH 55860327 = 0x55860327 idx 2
  MATCH 65942922 = 0x65942922 idx 0
  total accepted = 3 of 100000000
  ```

  Runtime: 0.30 s. Because BCD is bijective for digits 0–9, each accepted
  word has exactly one spelling; there are no aliases.

* **Novel password: impossible.** The accepted set is a hard-coded 3-element
  lookup; no unpublished 8-digit value can pass. This is a proven negative, not
  an untested gap: the table is exhausted, the comparison is exact, and the
  exhaustive run over the whole space returns the same three values.

* Public-code verification: all three published codes were entered through the
  real title gate and password screen. Each produced the expected flag byte:

  | Code | Word at object `+0xFC` | Success byte `+0x95` | Flags `0x0203F410` |
  |---|---|---|---|
  | `65942922` | `0x65942922` | `1` | `01 00 00` |
  | `35805225` | `0x35805225` | `1` | `00 01 00` |
  | `55860327` | `0x55860327` | `1` | `00 00 01` |

* Bounds by rejection (in-game, real screen):

  | Input | Word formed | Success byte | Flags | Result |
  |---|---|---|---|---|
  | `65942923` (one digit off a valid code) | `0x65942923` | `0` | unchanged `00 00 00` | rejected, internal state 3 (result screen) |
  | `00000000` | `0x00000000` | `0` | unchanged `01 00 00` | rejected |

  The first test proves the exact word was formed and still rejected: table
  membership, not input corruption, is the bound. The second bounds the
  zero/reserved-value case.

* Duplicate branch: after a successful `65942922` (flags `01`), returning to
  entry and re-entering `65942922` produced the correct word at `+0xFC`, left
  flags at `01`, and set success byte `0` — the ROM's “already been entered”
  branch (`i=6`, message `0x08657F49`). This proves the flag check and the
  duplicate path.

### 6b.2 Title button-gate space

* Read state: 10 held bits = **1,024** possible held masks.
* Predicate: `(held & 0x243) == 0x243`. Required bits: A=`0x001`,
  B=`0x002`, Up=`0x040`, L=`0x200`. The other six bits (Select `0x004`,
  Start `0x008`, Right `0x010`, Left `0x020`, Down `0x080`, R `0x100`) are
  masked out, so **64** of the 1,024 masks satisfy the predicate.
* Published code: `L+Up+B` then `A` (`0x243`) → state `0x17` (Observed).
* Bound (missing one required bit): `L+Up+B` held with no A (`0x242`) for
  >1 s leaves the title at state 1; no password screen (Observed).
* **Novel, unpublished accepted input:** `L + Up + B + R + A`
  (held mask `0x343`). This superset is not on GameFAQs or the wiki (they list
  only L+Up+B+A) and it opens the hidden password screen: Observed state
  `0x03000002 = 0x17` (23), object allocated and ready.
* Start supersets are not equivalent in practice: `L+Up+B+Start+A`
  (mask `0x24B`) went to state 12 (`Please select a file to play.`) because
  Start's normal title path advances first (Observed). This is a timing/order
  bound, not a password bound.

## 7. Validation evidence

**Observed** (emulator/RAM/SRAM reads):

* State byte `0x03000002`: 1 at title; 23 after `0x243` and after `0x343`;
  stays 1 after `0x242`.
* Password screen object fields: digit at `+0x80`, index `+0x94` advancing
  1…8, word at `+0xFC` equal to the concatenated digits, success byte
  `+0x95`.
* All three published codes produced their corresponding flag bytes and
  success byte 1.
* `65942923` and `00000000` produced the correct words but no flag.
* Duplicate entry produced the correct word, no flag change, success byte 0.
* SRAM `rom.sav` offset `0x3410` became `01 00 00` after `65942922` and stayed
  `01` across a full emulator restart; after restart IWRAM `0x030004F0` read
  `0x00000001`.
* State routes: title 1 → file select 12 → main 2 → Single JJ 15 → event grid 8;
  main 2 → Multiplayer 19; main 2 → Extras 5.

**Derived** (instruction-level):

* The title gate is the only writer of the state selector value 2 at
  `[fp+0xFF]`; the selector table `0x08524068` maps it to `0x17`, the password
  screen (state table entry 23 at `0x080003F0`).
* The digit insert, validator loop, flag write, duplicate test, message
  selection and save call are exactly as in §5.
* The save loader copies the 8-byte flag field to `0x030004F0/F4`, and the
  flag field lies at save offset `0x3410`, outside the 0xD00-byte per-file
  records.
* `0x243` is the only required button mask; 64 of 1,024 held masks satisfy it.
* Exhaustive enumeration of the 10⁸ password space yields exactly 3 accepted
  values.

**Inferred**:

* The three flags are read by the Jungle Jam event-list builder through the
  `0x030004F0` copy or the save buffer; the exact reader was not isolated. The
  message text, the flag write and the persistence are observed; the final
  event-grid rendering step is inferred.
* Password unlocks are global/permanent because the flag field is outside the
  file records; file erasure was not exercised.

## 8. Unknowns

* The exact code that consumes `0x030004F0` to add the event to the Jungle Jam
  grid was not located; the unlock message and the flag/persistence are proven,
  the final list insertion is inferred.
* The on-screen glyph encoding uses a leading length/control byte and `0x0A`
  line breaks; the exact font/tile mapping was not needed and was not decoded.
* Pause/options: no options menu and no pause-specific code/password surface
  exist. The main menu has exactly four entries and Extras exactly three
  (state 2 / state 5 handlers and their text pointers); the string `OPTIONS`
  occurs nowhere in the image. The standard gameplay pause overlay is UI-only
  and is outside the input-code space characterised here.
* The header-rebuild origin (checksum `0x0000`) is not attributable to this
  title; it matches the local collection's batch header fix.

## 9. Tooling

* `mGBA` SDL (`/usr/local/bin/mgba`), Xvfb `:276` + openbox, `xdotool`,
  `SDL_AUDIODRIVER=dummy`.
* Python 3 scripts: `state.py` (PNG `gbAs` zlib decoder, 397,312-byte raw
  state; IWRAM `0x19000`, EWRAM `0x21000`), `pwtest.py` (title route, digit
  entry, RAM field reads), `nav.py` (state-byte navigation).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000` for ARM
  disassembly; Capstone 5.0.7 available but not required for the final map.
* `enum.c` / `enum` (gcc -O2): exhaustive 10⁸ password-space check.
* All evidence is text/RAM/address-based. No screenshots or image files were
  read or produced.

## 10. Legal note

No ROM, extracted graphics, audio, or copyrighted text is redistributed here.
The report contains hashes, addresses, algorithms, and code values required to
reproduce the analysis.
