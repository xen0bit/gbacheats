# An American Tail: Fievel's Gold Rush (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/An American Tail: Fievel's Gold Rush/An American Tail: Fievel's Gold Rush.gba` |
| Size | 4,194,304 bytes (`0x400000`); data ends around `0x340000`, tail is `0x00` fill |
| Header title | `AMERICANTAIL` |
| Game code | `AFGE` |
| Maker code | `5Z` |
| Version | `0x00` |
| Fixed byte `0xB2` | `0x96` |
| Complement check `0xBD` | `0x45` — **valid** |
| Header checksum `0xBE` | `0x0000`; computed value would be `0xFA45` (dump artifact; mGBA boots it) |
| Entry branch | `0xEA00002E` → `0x080000C0`; Thumb main pointer `0x080001D1` at `0x1C8` |
| MD5 | `0051c7b9d4a3908afea19da18813fcbc` |
| SHA-1 | `f80528cc2265fea12e661b1dff1478bf9bda1c6c` |
| SHA-256 | `7397d79854a26e969add473cfeda87e5101422f34b613b703f05d0e296f7542b` |

Embedded-header scan: the full 156-byte Nintendo logo occurs exactly once, at file
offset `0x4` (header base `0x0`). This is a single GBA image, not a multi-game pack.

## 2. Executive summary

The game has a six-symbol password system:

* alphabet of **32** symbols: `BCDFGHJKLMNPQRSTVWXYZ0123456789*`
  (file `0x29D84`, ROM `0x08029D84`);
* each symbol is **5 bits**, packed little-endian into a **30-bit** word;
* bits 0–24 are a **25-bit payload**, bits 25–29 are a **5-bit checksum**;
* the payload is `score[17] | world[3] | lives[4] | hard[1]`.

The validator is at `0x08000414`; the matching encoder is at `0x08000530`. The
encoder is the routine used to *print* a password from the current state, so the
format is bidirectional. For every one of the `2^25` payloads exactly one of the
`32^6 = 2^30` six-symbol strings validates (1 in 32); I verified this bijection by
round-tripping 20,000 random payloads and by sampling 200,000 random strings.

Published codes were checked against the ROM. Worlds 2, 5 and 6 work exactly as
published. The published world-3 and world-4 codes are **typos**:
`HCM1HS` and `*VKSH2` are rejected by the game, while the canonical codes
`HCM1H5` (World 3) and `*VKSHZ` (World 4) are accepted. Both corrections are
confirmed in the emulator (screenshots listed in §7).

Two codes that appear in no published list were entered and observed:

* `FWLSP3` — World 2, 9 lives; starts `LEVEL 2-1` and the HUD shows ×9.
* `1DYD6X` — World 2, 9 lives, score field 12,345 (displayed `01234500`), hard
  flag set; preview and RAM both confirm all four fields.

Bounds were proven with accepted-but-out-of-range inputs: world 0 (`KWMSH7`) and
world 7 (`8BK1HX`) pass the checksum and are accepted by the password screen, but
the level loader produces a permanent white/hung screen; lives 0 and 15 are
accepted, stored verbatim, and the HUD caps its icon at ×9 for 15.

No button-code cheat table and no reachable level-select screen were found. The
string `LEVEL SELECT` / `level select` (text IDs 220/221) is present in the text
bank but no code reference was found; the level-intro screen is the only consumer
of the 24-level name table. The ROM also contains unused German, French and
Italian text banks; the language menu only offers English and Español.

## 3. How to reproduce

Emulator and display (this exact session used display `:137`):

```bash
Xvfb :137 -screen 0 1024x768x24 &
DISPLAY=:137 openbox &
DISPLAY=:137 SDL_AUDIODRIVER=dummy mgba -3 game.gba &
```

mGBA SDL keymap used: **A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad = arrows**. Hold keys ~100–200 ms.

Menu path:

1. Boot → language select (`English` / `Español`) → `A` on English.
2. Title → `Down` once to `Password` → `A`.
3. The entry screen starts with `MCN1H9` and the cursor on position 0.
   `Up` advances a symbol in the alphabet, `Down` retreats, `Left`/`Right`
   move the cursor. `A` validates.
4. A valid code shows `Valid password` plus `World`, `Lives`, `Score`;
   `A` again starts `LEVEL <world>-1`. An invalid code shows
   `Invalid password` and stays on the entry screen.

A savestate at step 3 (`game.ss1` in the work directory) makes each test cost six
symbol changes plus `A`. The title-menu password screen is the entry point used
for all tests in this report; the in-game Start screen is a paused label, not a
menu.

Reproduction of one novel code (`FWLSP3`, world 2, lives 9):

```
F1 (load state) -> Up/Down/Right to spell F W L S P 3 -> A
  preview: World 2, Lives 9, Score 00000000
A
  "LEVEL 2-1", then HUD: lives ×9
```

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x08000414` | code | checksum/range validator, `(char *buf) -> 0 ok, 1 bad length, 2 bad char, 3 bad check` |
| `0x08000530` | code | encoder, current state → six symbols at `0x03003478` |
| `0x08029D84` | data | 32-byte password alphabet, NUL-padded after `*` |
| `0x0829D7C` | data | built-in default code `MCN1H9` (used to pre-fill the entry screen) |
| `0x08005766` | code | password-screen call site of the validator (`BL 0x08000414` at `0x08005776`) |
| `0x08010CCC` | code | screen function that calls the encoder (`BL 0x08000530` at `0x08010D28`) — password-display screen |
| `0x03003478` | RAM | six-byte input buffer (validator reads this) |
| `0x03003480` | RAM | six-byte display copy made by the password screen |
| `0x03003A74` | RAM | score, low 17 bits are encoded (display = value × 100) |
| `0x03000A98` | RAM | world, 3 bits (1–6 load; 0 and 7 hang) |
| `0x03003A98` | RAM | lives, 4 bits (0–15; HUD icon caps at 9) |
| `0x03003638` | RAM | difficulty, 1 bit (0 = NORMAL, 1 = HARD) |
| `0x03000AB0` | RAM | level inside the world, 1–4; set to 1 by the password path |
| `0x082D33D8` | ROM | text-bank base (loaded at runtime into `[0x03000AB4]`) |
| `0x082D33E0` | ROM | text-ID → offset table (u32, loaded into `[0x03000AB8]`) |
| `0x082D6CBA` | ROM | `LEVEL SELECT` = text ID 220; `0x082D6CC7` = `level select` = 221 |
| `0x08326184` | ROM | 24 × u16 level-name text IDs, 134–157 (`LEVEL 1-1` … `LEVEL 6-4`) |
| `0x08015AF0` | code | level-intro screen (uses `0x08326184` at `0x08015DAA`) |
| `0x08016754` | code | input reader; `KEYINPUT` literal at `0x08016818` |
| `0x08028F14` | code | soft reset (`sp=0x03007F00`, `svc 1`, `svc 0`) reached by A+B+Select+Start |

Text/resource note: the `ALLLANG` descriptor at `0x2D778` is
`name[8] + size=0xCE75 + offset=0x2A9534`. The observed runtime base
`0x082D33D8` equals `0x29EA4 + 0x2A9534`, so the bank is uncompressed and
contains the offset table followed by all five language blocks.

## 5. Algorithm

The ROM's validator (Thumb, `0x08000414`) and encoder (`0x08000530`) implement
exactly this:

```python
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0123456789*"      # 0x08029D84

def decode(s):                                  # validator 0x08000414
    assert len(s) == 6                          # return 1 otherwise
    W = 0
    for i, ch in enumerate(s):                  # return 2 on unknown char
        W |= ALPHA.index(ch) << (5 * i)
    chk  = (W >> 25) & 0x1F                     # bits 25..29
    b24  = (W >> 24) & 1                        # bit 24
    e0, e1, e2 = W & 0xFF, (W >> 8) & 0xFF, (W >> 16) & 0xFF
    p0 = (e0 - 11 - chk) & 0xFF
    p1 = (e1 - 10 - chk) & 0xFF
    p2 = (e2 - 11 - chk) & 0xFF
    payload = p0 | (p1 << 8) | (p2 << 16) | (b24 << 24)
    ok = chk == ((0x0C ^ ((p0 + p1 + p2 + b24) & 0xFF)) & 0x1F)
    return dict(ok=ok, payload=payload,
                score=payload & 0x1FFFF,        # displayed ×100
                world=(payload >> 17) & 7,
                lives=(payload >> 20) & 0xF,
                hard=(payload >> 24) & 1)       # return 3 if !ok

def encode(score, world, lives, hard):          # encoder 0x08000530
    payload = ((score & 0x1FFFF) | ((world & 7) << 17) |
               ((lives & 0xF) << 20) | ((hard & 1) << 24))
    p0, p1, p2 = payload & 0xFF, (payload >> 8) & 0xFF, (payload >> 16) & 0xFF
    b24 = (payload >> 24) & 1
    chk = (0x0C ^ ((p0 + p1 + p2 + b24) & 0xFF)) & 0x1F
    e0 = (p0 + 11 + chk) & 0xFF
    e1 = (p1 + 10 + chk) & 0xFF
    e2 = (p2 + 11 + chk) & 0xFF
    e3 = (2 * chk + b24) & 0xFF
    W = e0 | (e1 << 8) | (e2 << 16) | (e3 << 24)
    return "".join(ALPHA[(W >> (5 * i)) & 31] for i in range(6))
```

Why it works: the encoder biases each payload byte by `+chk` (plus 11/10/11)
and stores `chk` in the top five bits. The validator subtracts the same bias,
recovers the payload, and re-computes `chk` from the recovered payload bytes.
For a given payload the checksum is unique, so the mapping is a bijection.

Return values map to the caller at `0x08005766`: `0` → show `Valid password`
and continue to the level loader; non-zero → show `Invalid password`; the
length/character failures cannot be produced by the on-screen keypad, which
always emits exactly six alphabet symbols.

## 6. Tables

### 6.1 Field layout (25-bit payload)

| Bits | Width | Field | Observed mapping |
|---:|---:|---|---|
| 0–16 | 17 | score | raw value; screen renders raw × 100 (`0x3039` → `01234500`) |
| 17–19 | 3 | world | 1–6 load `LEVEL n-1`; 0 and 7 hang the loader |
| 20–23 | 4 | lives | 0–15 accepted; HUD icon caps at 9, RAM keeps the value |
| 24 | 1 | difficulty | 0 = NORMAL, 1 = HARD (`0x03003638`; the options screen writes the same byte on exit) |
| 25–29 | 5 | checksum | `(0x0C ^ ((p0+p1+p2+b24) & 0xFF)) & 0x1F` |

The word is exactly 30 bits (six 5-bit symbols); there are no spare bits.

### 6.2 Published codes (source: 53lu / SuperCheats list) and verification

| Published | Claimed | ROM result | Corrected canonical code | Verified |
|---|---|---|---|---|
| `FWLSH3` | Level 2 | **Valid**, World 2, Lives 3 | — | screenshot `60_fwlsh3_valid` |
| `HCM1HS` | Level 3 | **Invalid password** | `HCM1H5` → World 3 | `84_hcm1hs_invalid`, `72_hcm1h5_valid` |
| `*VKSH2` | Level 4 | **Invalid password** | `*VKSHZ` → World 4 | `85_vksh2_invalid`, `74_vkshz_valid` |
| `CCL1H1` | Level 5 | **Valid**, World 5, Lives 3 | — | `147_ccl1h1` |
| `6VJSHV` | Level 6 | **Valid**, World 6, Lives 3 | — | `148_6vjshv` |

The public list was recovered from 53lu and SuperCheats (GameFAQs and IGN
returned HTTP 403 to automated fetches); every recovered code was then tested in
the ROM/emulator rather than trusted as text.

The built-in default `MCN1H9` is the canonical World 1 / Lives 3 / Score 0 code;
`encode(0,1,3,0)` reproduces it byte-for-byte, which validates the encoder against
the ROM's own data.

### 6.3 Text IDs relevant to menus

| ID | String | Use |
|---:|---|---|
| 4/5 | `NEW GAME` / `new game` | title menu, selected/unselected |
| 8/9 | `PASSWORD` / `password` | title menu |
| 6/7 | `OPTIONS` / `options` | title menu |
| 10–16 | `OPTIONS`, `Difficulty`, `Music vol.`, `SFX vol.`, `Control setup`, `Credits`, `Return` | options screen |
| 17–20 | `PASSWORD`, `Enter password`, `Invalid password`, `Valid password` | password screen |
| 46 | `Pause` | pause label |
| 47/48 | `WORLD DONE` / `LEVEL DONE` | end-of-level screens |
| 56–60 | `GAME OVER`, `Continue?`, `YES/no`, `yes/NO`, `Password` | game-over/continue path |
| 134–157 | `LEVEL 1-1` … `LEVEL 6-4` | 24-level table at `0x08326184` |
| 220/221 | `LEVEL SELECT` / `level select` | no code reference found (see §6b) |

### 6.4 Language blocks in `ALLLANG`

English IDs 0–221, Deutsch 222–328, Français 329–460, Español 461–594,
Italiano 595–695 (696 NUL-terminated strings total). Only English and Español
are offered by the language menu; the other three banks are leftovers in this
USA build.

## 6b. Enumeration

**Space size.** Six symbols × 32 values = `32^6 = 2^30 = 1,073,741,824` possible
strings. Exactly one string per 25-bit payload validates, so the accepted set has
`2^25 = 33,554,432` codes. This was checked two ways:

* 200,000 random six-symbol strings → 6,173 valid (0.0309; expected 1/32 =
  0.03125).
* 20,000 random `(score, world, lives, hard)` tuples → `encode` → `decode`
  recovered every field with zero failures.

**Novel codes (not in any published list), entered and observed:**

| Code | Payload | Preview evidence | Gameplay evidence |
|---|---|---|---|
| `FWLSP3` | score 0, world 2, lives 9, normal | `86_lives9_valid` — World 2, Lives 9, Score 0 | `88_lives9_start2` — `LEVEL 2-1`; `89_lives9_game` — HUD ×9 |
| `1DYD6X` | score 12,345, world 2, lives 9, hard | `90_novel_valid` — World 2, Lives 9, Score `01234500` | `91_novel_start` / `93_novel_hud2` — `LEVEL 2-1`, HUD ×9; RAM read: `0x3039`, `2`, `9`, `1` |
| `FWLSC3` | score 0, world 2, lives 15 | `105_lives15` — Lives 15 shown | `107_lives15_hud2` — HUD ×9, RAM `0x03003A98 = 0x0F` |
| `YVGSCL` | score 0, world 2, lives 0 | `108_lives0` — Lives 0 shown | `110_lives0_start2` — HUD ×0 |

**Bounds proven by rejection / failure:**

| Input | Result | Evidence |
|---|---|---|
| `HCM1HS` (published, bad checksum) | `Invalid password` | `84_hcm1hs_invalid` |
| `*VKSH2` (published, bad checksum) | `Invalid password` | `85_vksh2_invalid` |
| `KWMSH7` (world 0, checksum-valid) | accepted; white/hung loader, no input response | `76_w0_valid`, `79_w0_later`, `143_w0_white`–`146_w0_up` |
| `8BK1HX` (world 7, checksum-valid) | accepted; white/hung loader | `81_w7_valid`, `82_w7_start`, `83_w7_start2` |
| `FWLSC3` (lives 15) | accepted; field is 4 bits, HUD caps at 9 | `105`, `107` |
| `YVGSCL` (lives 0) | accepted; playable with ×0 | `108`, `110` |

The six-character UI makes the validator's length check (`cmp #6`, return 1)
unreachable through intended input, and the keypad can only emit the 32 alphabet
symbols, so the bad-character path (return 2) is likewise unreachable by hand.
The reachable rejection is the checksum, demonstrated with the two published
typos above.

**Level-select string and button codes (bounded negative).**

* `LEVEL SELECT` / `level select` are text IDs 220/221 at `0x2D6CBA` /
  `0x2D6CC7`. A search for text-ID references found none: the only consumers of
  the 24-entry level-name table `0x08326184` are three literals inside the
  level-intro screen (`0x08015DF8`, `0x0801602C`, `0x08016154`), and the
  `movs rN,#0xDC` sites in the code region (`0x080003AE2`, `0x080003D1C`,
  `0x0800040A2`, `0x080004700`, `0x0800592C`) all store the halfword constant
  220 to `0x030036BC`, which is read back as an X coordinate at `0x08003F36`,
  not as a text ID.
* The title menu has three items (`NEW GAME`, `Password`, `options`), the options
  screen six (`Difficulty`, `Music vol.`, `SFX vol.`, `Control setup`, `Credits`,
  `Return`), the password screen one input field, and the in-game Start screen
  only a blinking `Pause` label. No fourth title item, no pause menu, no
  sub-screen under `Control setup` (it is a 1/2 toggle).
* Button-mask scan: in the low 208 KiB (`0x08000000`–`0x08034000`, where the code
  and literal pools live) there are **zero** runs of four or more `u16` key masks
  (`1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200`).
  The only special combination in the input reader (`0x08016754`) is
  A+B+Select+Start, which calls the standard soft reset at `0x08028F14`.
* Dynamic spot checks: the Konami sequence on the title simply ended on `A`,
  which selected `NEW GAME` (normal load); L+R+Start, Select, and L/R on the
  title/password screens produced no new screen (`122_konami`, `125_lrstart`,
  `126_select`, `149`–`151`).

The password system itself is the only developer-intended level-selection
mechanism found: any world 1–6 can be jumped to at level 1, with a chosen
score/lives/difficulty.

## 7. Validation evidence

**Observed (emulator screenshots and RAM reads):**

* Language select, title, options, control setup, credits, password entry,
  valid/invalid screens, level-intro screen, pause label — screenshots
  `12`, `15`, `03`, `97`, `99`, `04`, `60`, `72`, `74`, `84`, `85`, `88`, `111`.
* `FWLSH3` → World 2; `CCL1H1` → World 5; `6VJSHV` → World 6.
* `HCM1HS` → Invalid; `*VKSH2` → Invalid.
* `HCM1H5` → World 3; `*VKSHZ` → World 4.
* `FWLSP3` → World 2, Lives 9, `LEVEL 2-1`, HUD ×9.
* `1DYD6X` → World 2, Lives 9, Score `01234500`; gameplay RAM at
  `0x03003A74 = 0x3039`, `0x03000A98 = 2`, `0x03003A98 = 9`,
  `0x03003638 = 1`, `0x03000AB0 = 1`.
* World 0 / world 7 → white, unresponsive screen.
* Lives 0 / 15 → accepted and reflected in HUD/RAM.
* Options `Difficulty: HARD` → after returning to the title,
  `0x03003638 = 1` (the same byte the password's bit 24 writes).

**Derived (instruction-level):**

* Validator and encoder addresses, the byte biases 11/10/11, the checksum
  formula, and the 5-bit packing (disassembly at `0x08000414` / `0x08000530`).
* Text base/table pointers `0x03000AB4 = 0x082D33D8` and
  `0x03000AB8 = 0x082D33E0`; text IDs and the 24-level table.
* No text-ID consumer was found for `LEVEL SELECT`; no button-mask table exists.
* Soft reset combination from the input reader.
* Difficulty: selecting HARD in the options screen and returning to the title
  leaves `0x03003638 = 1`; the password's bit 24 writes the same byte (observed
  with `1DYD6X`).

**Inferred:**

* `0x08010CCC` is the screen that prints a password from the current state
  (it calls the encoder and copies the six bytes into the input buffer). Its
  exact trigger (likely `LEVEL DONE` / `WORLD DONE`) was not reached.
* The in-game effect of the difficulty flag on enemy behaviour was not measured.
* The score field counts in units of 100; the preview multiplies by 100.
* `LEVEL SELECT` is a leftover/unused string from a removed screen.

**Screenshots** are in `/tmp/opencode/fievel/shots/` (session work directory);
the report is the durable artifact.

## 8. Unknowns

* The condition that displays the game-generated password screen
  (`0x08010CCC`) was not reached; only the encoder itself was verified.
* The gameplay-outcome screens (`GAME OVER` / `Continue?`, and the
  `LEVEL DONE` / `WORLD DONE` password display) were not reached in this
  session. They are not menus reachable from the title; their text IDs are
  listed in §6.3. All menu screens reachable from the title were walked.
* Whether `LEVEL SELECT` is reachable under a condition not exercised here
  (e.g. completing the game, a specific save state) is unknown. No code path,
  menu entry, text-ID reference, or button table was found for it.
* The gameplay effect of the hard flag is unmeasured.
* The five language blocks exist, but only English/Español are selectable in this
  build; whether the other three were reachable in another revision is unknown.
* The header checksum field is zero; this is noted but does not affect play.

## 9. Tooling

* mGBA 0.10.5 SDL (`/usr/games/mgba`), Xvfb `:137`, openbox, scrot, ImageMagick,
  xdotool, `arm-none-eabi-objdump`, `gdb-multiarch` (mGBA `-g` stub on `:2345`).
* Python 3 scripts in `/tmp/opencode/fievel/scripts/`:
  `fievel_pw.py` (encoder/decoder above), `type_code.py` (types a six-symbol code
  from the built-in `MCN1H9`), `key.py` (keypress/screenshot helper).
* Search/verification: literal `grep -abo`, pointer scans, Thumb `BL` scans,
  Capstone checks, RAM dumps from the mGBA GDB stub, and `zlib`/header checks.
* No ROM, graphics, music or text assets are redistributed here; only short UI
  labels are quoted for identification.
