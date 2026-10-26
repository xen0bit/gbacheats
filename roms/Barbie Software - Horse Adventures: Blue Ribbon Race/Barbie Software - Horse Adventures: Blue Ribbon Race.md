# Barbie Software - Horse Adventures: Blue Ribbon Race (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-26.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Barbie Software - Horse Adventures: Blue Ribbon Race/Barbie Software - Horse Adventures: Blue Ribbon Race.gba` |
| Size | 4 MiB (`0x400000`) |
| Header title | `BARBIE` (NUL-padded) |
| Game code | `AI8E` |
| Maker code | `7D` |
| Software version | `0` |
| Entry branch | `0xEA00002E` → `0x080000C0` |
| Complement check (`0xBD`) | `0x2A` (valid) |
| Header checksum (`0xBE`) | `0x0000` (computed `0x00D6` — **invalid**) |
| MD5 | `b0c8edeae511c647f9617b32ddc37594` |
| SHA-1 | `7d8938d54eafb1558efce8bdfbc9db15ac2072e5` |
| SHA-256 | `52c26ad39379d79b39a8f8b3cb5e6ef7f4ef74b710d192952d70708d40f68f27` |

ROM addresses below are `0x08000000 + file_offset`. All findings are tied to
this exact hash; another revision may differ.

### Header / patch note (Phase 0)

* One and only one Nintendo logo / GBA header exists (logo at file `0x4`,
  header base `0x0`). This is **not** a multi-game cartridge and contains no
  second boot image.
* The fixed byte `0xB2` is `0x96`, the complement check is correct, and the
  logo/game code/maker code match the retail `AGB-AI8E-USA` identity.
* The header checksum word at `0xBE` is zero although the correct value is
  `0x00D6`. This is the only fingerprint anomaly. It is consistent with a
  header edit/normalization (or a dump that lost that one field); the entry
  point is the standard crt0 (`0x080000C0`), no trainer or injected boot code
  was found, and the code/data used below is self-consistent. Treat this as a
  modified header, not a modified game.

---

## 2. Executive summary

The game has exactly one developer-intended cheat/save system: a **9-character
password** entered from **Continue Game**.

* Alphabet: 32 symbols, 5 bits each
  (`BCDFGHJKLMNPQRSTVWXYZ23456789+-?` — no vowels, no `0`/`1`).
* Payload: **35 bits**, split into 13 fields
  (1 × 3 bits, 8 × 2 bits, 4 × 4 bits).
* Check field: **8 bits** that must equal a 1-bit checksum expressed as
  `0x00` or `0x08`. Because the field is only masked to 8 bits, the top **2**
  bits of the last symbol are outside the mask and are ignored by the
  validator, giving **4 accepted spellings per state**.
* The game contains both a decoder (`0x080B47E4`) and an encoder
  (`0x080B46EC`/`0x080B4700`/`0x080B47A4`), so arbitrary game states can be
  minted. The single published code (`BBBV8+SBB`, GameFAQs) is just the
  "everything complete" preset; it is **not stored as a literal** anywhere in
  the ROM.
* The password is also the save mechanism: the cartridge produces a 0-byte
  `.sav`, and the game contains a password-generator screen class
  (`0x080A98D0`, the code that renders the "Your password is" screen) that
  regenerates the code from the in-RAM state struct at `0x030025B8`.
* No button codes, debug menu, hidden screen, or second password system was
  found. The negative result is bounded by the menu walk, string scan,
  alphabet-literal scan, and key-mask scan in §6b/§7.

Novel codes were generated and accepted in mGBA:
`B6M-VQLBB` (mixed ribbons + four distinct counters),
`BCBV8+SLB` (one second-place ribbon), and the alias spellings
`BBBV8+SBL`, `BBBV8+SBV`, `BBBV8+SB5`. Rejected controls appear in §6b.

---

## 3. How to reproduce

### Emulator

```bash
sudo apt-get install -y mgba-sdl xvfb openbox xdotool scrot imagemagick
Xvfb :168 -screen 0 1024x768x24 &
DISPLAY=:168 openbox &
DISPLAY=:168 SDL_AUDIODRIVER=dummy mgba -3 "Barbie Software - Horse Adventures: Blue Ribbon Race.gba" &
```

Default mGBA keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
L=`a`, R=`s`, D-pad = arrows. Hold keys 100–200 ms.

### Menu path (observed)

```
Title ("Press START")
└─ Start
   └─ Main menu: Play / Continue Game / Options / How To Play
      └─ Continue Game → 9-slot password screen
         └─ A on the last slot → "Password Accepted" / "Password not Accepted"
            └─ A → course select (Let's Race)
```

Password entry mechanics: the red up/down arrows mark the current slot.
Up/Down change the letter, Left/Right move the cursor, A accepts the letter
and advances one slot; A on the ninth slot submits. Starting all nine slots
at `B`, a code is typed by pressing Down `index` times per slot
(`B=0 … ?=31`), then A.

Savestate used during analysis: `Barbie Software - Horse Adventures: Blue
Ribbon Race.ss1`, taken on the blank entry screen (Shift+F1 saves, F1 loads).
This reduces each experiment to one key sequence.

### Codes exercised

| Input | Result (observed) |
|---|---|
| `BBBV8+SBB` | **Password Accepted**; course select = Primrose Hill Final Race; all ribbons, gold trophy, gold coin strip. GameFAQs code. |
| `B6M-VQLBB` | **Password Accepted**; final race; trophy case shows 2 firsts, 2 seconds, 2 thirds, 2 empty and a faded trophy; coin strip gold. Novel. |
| `BCBV8+SLB` | **Password Accepted**; final race; one red (2nd) ribbon in the trophy case. Novel. |
| `BBBV8+SBL` | **Password Accepted**; identical state to `BBBV8+SBB` (alias using ignored bit 43). Novel. |
| `BBBV8+SBV` | **Password Accepted**; identical state (alias using ignored bit 44). Novel. |
| `BBBV8+SB5` | **Password Accepted**; identical state (alias using ignored bits 43+44). Novel. |
| `KBBV8+SBB` | **Password Accepted**; course select = Primrose Hill Village (field 0 = 7). Novel. |
| `BBBBBBBBB` | Password not Accepted — check byte `0x00`, required `0x08`. |
| `BBBV8+SBC` | Password not Accepted — check byte `0x20` (bit 40 set). |
| `BBBV8+SBG` | Password not Accepted — check byte `0x80` (bit 42 set). |
| `BBBV8+SVB` | Password not Accepted — check byte `0x10` (symbol 7 = 16). |

Entry was visually verified in the buffer before submission for the bound
tests (`verify_BBBV8pSVB.png`, `verify_BBBV8pSBL.png`), so the rejections are
not mis-typed inputs.

---

## 4. Address map

### ROM / tables

| File offset | ROM address | What |
|---:|---:|---|
| `0x163EDC` | `0x08163EDC` | 32-byte password alphabet, NUL-terminated at `0x163EFC` |
| `0x163EFD` | `0x08163EFD` | 13 field-width bytes `03 02 02 02 02 02 02 02 02 04 04 04 04` |
| `0x3BE004` | `0x083BE004` | ROM copy of the mask table `1,3,7,15,31,63,127,255` |
| `0x3B4760` | `0x083B4760` | ASCII "Password Accepted" (string bank; also FR/DE/IT/ES copies) |
| `0x3B478C` | `0x083B478C` | ASCII "Your password is" |
| `0x3BC200` | `0x083BC200` | "Version BETA BUILD GMC5US" build string (data bank, not displayed in any menu found) |
| `0x0B47E4` | `0x080B47E4` | `decode_password(obj, chars, widths, 13)` → `obj+0x28` or `0` |
| `0x0B4740` | `0x080B4740` | checksum: `(~sum) & 8` |
| `0x0B4700` | `0x080B4700` | `append_field(acc, value, width)` (64-bit accumulator) |
| `0x0B46EC` | `0x080B46EC` | encoder step (increment field count, append field) |
| `0x0B47A4` | `0x080B47A4` | encoder finalize: append 8-bit checksum, split into 9 × 5-bit symbols |
| `0x0B54AC` | `0x080B54AC` | load game state from password; calls decoder and writes the state struct |
| `0x0B51F0` | `0x080B51F0` | password-screen update / input dispatch |
| `0x0B52AC` | `0x080B52AC` | spinner: previous letter (value − 1 mod 32) |
| `0x0B53A8` | `0x080B53A8` | spinner: next letter (value + 1 mod 32) |
| `0x0A98D0` | `0x080A98D0` | "Your password is" screen class; regenerates the code from RAM |
| `0x0A99D2`..`0x0A9A92` | `0x080A99D2`.. | state-field reads + encoder calls of that screen |

The alphabet is loaded as a literal at `0x080A9BEC`, `0x080B53A4` and
`0x080B54A8`; the width table is the literal at `0x080B55B4`.

### RAM

| Address | Use |
|---|---|
| `0x03001398` | mask table used by encoder/decoder: `table[w-1] = (1<<w)-1`; observed `1,3,7,15,31,63,127,255` |
| `0x030025B8` | base of the global game/save struct (literal at `0x080B55B8` and ~240 other sites) |
| `0x030025B8+0x2C` | course / "horses sponsored" index, 1..8 (clamped to 8 on read) |
| `0x030025B8+0x34`..`+0x50` | 8 × `u32` ribbon ranks (3 = 1st/blue, 2 = 2nd/red, 1 = 3rd/white, 0 = none) |
| `0x030025B8+0x6A` | `u8` derived index = clamped(+0x2C) − 1 |
| `0x030025B8+0xD0,+0xD8,+0xE0,+0xE8` | 4 × `u32` coin/charity counters, 0..15 |
| `0x030025B8+0xCC,+0xD4,+0xDC,+0xE4` | ribbon-derived bit masks (0,2,4,8) |
| `0x030025B8+0xEC` | `u8` sum of the eight dwords above, `& 0xFF` (auxiliary total) |
| `0x03007DE4` (stack, observed) | width map copied by the decoder: `03 02 02 02 02 02 02 02 02 04 04 04 04 00` |

The decoder object lives on the stack (`obj = 0x03007DF4` in the traced
call); the 14th map byte is the NUL after the 13 widths and is `0x00`. It is
only used as a rotation amount for the last field; the last field's **mask**
is hardcoded (`0x080B48BC` loads `table[7] = 0xFF`).

---

## 5. Algorithm

### 5.1 Alphabet and field layout

```
index : 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
symbol:  B  C  D  F  G  H  J  K  L  M  N  P  Q  R  S  T
index : 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31
symbol:  V  W  X  Y  Z  2  3  4  5  6  7  8  9  +  -  ?
```

| Field | Bit range | Width | Encoding |
|---|---:|---:|---|
| `f0` | 0–2 | 3 | `stored = (f0 ^ 7) + 1` → course index 1..8 |
| `f1`..`f8` | 3–18 | 2 each | `stored = f ^ 3` → ribbon rank |
| `f9`..`f12` | 19–34 | 4 each | `stored = f ^ 0xF` → counter 0..15 |
| check | 35–42 | 8 | must equal the checksum byte `0x00` or `0x08` |
| ignored | 43–44 | 2 | outside the 8-bit mask; not tested |

Symbol 7 holds bits 35–39, symbol 8 holds bits 40–44. Therefore the
validator constrains only the low **3** bits of symbol 8; its high 2 bits are
free. The check byte is only ever `0x00` or `0x08`, so symbol 7 must be `B`
(check 0) or `L` (check 8), and symbol 8 must be `B`, `L`, `V` or `5`.

### 5.2 Encoder / decoder

```python
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ23456789+-?"
W     = [3, 2, 2, 2, 2, 2, 2, 2, 2, 4, 4, 4, 4]   # 35 bits

def pack(fields):
    v, sh = 0, 0
    for f, w in zip(fields, W):
        v |= (f & ((1 << w) - 1)) << sh
        sh += w
    return v

def checksum(v):
    lo = v & 0xFFFFFFFF
    s = ((lo >> 4) + (lo >> 8) + (lo >> 12) +
         (lo >> 16) + (lo >> 20) + (lo >> 28)) & 0xFFFFFFFF
    return (~s) & 8          # 0x00 or 0x08

def encode(fields):
    v = pack(fields)
    v |= checksum(v) << 35
    return "".join(ALPHA[(v >> (5 * i)) & 31] for i in range(9))

def decode(code):
    v = 0
    for i, c in enumerate(code):
        v |= ALPHA.index(c) << (5 * i)
    fields, sh = [], 0
    for w in W:
        fields.append((v >> sh) & ((1 << w) - 1))
        sh += w
    check = (v >> 35) & 0xFF      # 8-bit field; bits 43-44 are discarded
    return fields, check

def valid(code):
    f, check = decode(code)
    return check == checksum(pack(f))
```

The checksum is a **single bit** of information: only bit 3 of the sum
matters, and the encoder stores it as `0x00` or `0x08` in an 8-bit field.
The decoder's last-field mask is not the uninitialized 14th width byte; the
code at `0x080B48BC` hardcodes `table[7] = 0xFF`, which is why exactly 8
bits are compared.

### 5.3 Loading the state (`0x080B54AC`)

```
fields = decode_password(stack_obj, screen->password, widths, 13)
if fields == NULL: "Password not Accepted"
else:
    state[0x2C]       = (fields[0] ^ 7) + 1
    state[0x6A]       = clamp(state[0x2C], 8) - 1
    state[0x34+4i]    = fields[1+i] ^ 3      (i = 0..7)
    state[0xD0+8i]    = fields[9+i] ^ 0xF    (i = 0..3)
    state[0xCC/0xD4/0xDC/0xE4] = ribbon_bitmask(fields[1], [3], [5], [7])
    state[0xEC]       = sum(state[0xCC..0xE8]) & 0xFF
    "Password Accepted"
```

The password screen stores the 9 symbols as indices 0..31 at `obj+0xA0`,
not as ASCII; the display maps them through the alphabet table.

### 5.4 Encoder path (password display)

The screen class at `0x080A98D0` reads the same state fields, calls
`append_field(acc, value, width)` for each of the 13 fields in the order
above, then `finalize` appends the 8-bit checksum and splits the 43-bit
accumulator into nine 5-bit symbols. The generated code is displayed with
the same alphabet. This is the exact inverse of §5.2.

---

## 6. Tables

### 6.1 Field effects (observed)

| Field | Values | In-game effect |
|---|---|---|
| `f0` | 0..7 | Course/progress index: 0 → `+0x2C = 8` → **Primrose Hill Final Race**; 7 → `+0x2C = 1` → **Primrose Hill Village**. |
| `f1`..`f8` | 0..3 | Ribbon rank per event: `stored 3` = blue "1" (1st), `2` = red "2" (2nd), `1` = white/green "3" (3rd), `0` = empty tile. |
| `f9`..`f12` | 0..15 | Four counters. With all four non-zero the course-select coin strip is gold; with any one zero the whole strip is pale. Exact per-counter game variable not isolated. |

The trophy-case screen is the clean readout for `f1`..`f8`; the
course-select coin strip is the clean readout for `f9`..`f12`.

### 6.2 Check values

| Condition | Check byte | Symbol 7 | Symbol 8 (low 3 bits) |
|---|---:|---|---|
| `bit3(sum) == 1` | `0x00` | `B` (0) | `000` |
| `bit3(sum) == 0` | `0x08` | `L` (8) | `000` |

Allowed last-two-symbol spellings (model, five observed):
`BB`, `BL`, `BV`, `B5`, `LB`, `LL`, `LV`, `L5`.

### 6.3 Test vectors

| Code | Fields `f0..f12` | `V` | `lo` | `sum` | check | result |
|---|---|---|---:|---:|---:|---:|---|
| `BBBV8+SBB` | `0,0,0,0,0,0,0,0,0,7,7,7,7` | `0x3BBB80000` | `0xBBB80000` | `0x0C83BAFE` | `0x00` | accepted |
| `BCBV8+SLB` | `0,0,1,0,0,0,0,0,0,7,7,7,7` | `0x3BBB80020` | `0xBBB80020` | `0x0C83BB00` | `0x08` | accepted |
| `B6M-VQLBB` | `0,0,1,2,3,0,1,2,3,1,2,3,4` | `0x2190F2720` | `0x190F2720` | `0x01ABAD2B` | `0x00` | accepted |
| `KBBV8+SBB` | `7,0,0,0,0,0,0,0,0,7,7,7,7` | `0x3BBB80007` | `0xBBB80007` | `0x0C83BAFE` | `0x00` | accepted |
| `BBBBBBBBB` | all zero | `0x0` | `0x0` | `0x0` | `0x00` vs `0x08` | rejected |
| `BBBV8+SBC` | as published | `0x3BBB80000` | `0xBBB80000` | `0x0C83BAFE` | `0x20` vs `0x00` | rejected |
| `BBBV8+SBG` | as published | `0x3BBB80000` | `0xBBB80000` | `0x0C83BAFE` | `0x80` vs `0x00` | rejected |
| `BBBV8+SVB` | as published | `0x3BBB80000` | `0xBBB80000` | `0x0C83BAFE` | `0x10` vs `0x00` | rejected |

`BBBV8+SBL`, `BBBV8+SBV` and `BBBV8+SB5` keep `V`, `lo`, `sum` and the
required check byte identical to `BBBV8+SBB`; they differ only in the two
ignored bits and are accepted with the same state.

### 6.4 Published codes

| Source | Code | Status in this ROM |
|---|---|---|
| GameFAQs (GBA cheats page, archived 2018-11-26, contributed by ReyVGM) — "All horses and everything complete." | `BBBV8+SBB` | Verified accepted in mGBA; decodes to the complete state. |
| Giant Bomb wiki trivia — "Use the password BBBV8 SBB" | `BBBV8 SBB` (space) | Same code with a typo; the character set has no space, so the published form is not enterable. |

Only these two published strings were found. No other GBA password appears in
the published sources searched (GameFAQs, Giant Bomb, and the fan wikis
reached by search); no TCRF or VGChartz code page surfaced.

---

## 6b. Enumeration

### 6b.1 Space size

| Quantity | Value |
|---|---:|
| Alphabet size | 32 |
| Length | 9 |
| Raw string space `32^9` | `35,184,372,088,832` (`2^45`) |
| Payload states `2^35` | `34,359,738,368` |
| Check-field values accepted | 2 (`0x00`, `0x08`) |
| Ignored bits | 2 (bits 43–44) |
| Accepted strings `2^35 × 4` | `137,438,953,472` (`2^37`) |
| Published codes | 1 |

The check field is 8 bits wide but carries one bit of checksum, so 7 of its
bits are forced zero. The top 2 bits of the last symbol are outside the
decoder's hardcoded `0xFF` mask. Consequently **every state has exactly four
accepted spellings** (`BB`/`BL`/`BV`/`B5` when the check is 0,
`LB`/`LL`/`LV`/`L5` when it is 8).

### 6b.2 Novel codes generated and confirmed

These strings are in no published list. Each was typed through the normal
password screen; the screenshots are in the analysis work directory
(`/tmp/opencode/barbiehorse/`).

| Code | State encoded | In-game proof |
|---|---|---|
| `B6M-VQLBB` | course 8; ribbons `[1st,2nd,3rd,none,1st,2nd,3rd,none]`; counters `14,13,12,11` | `novel_result.png` = "Password Accepted"; `novel_course.png` = Primrose Hill Final Race; `novel_trophy.png` = 2 blue, 2 red, 2 white, 2 empty, faded trophy |
| `BCBV8+SLB` | course 8; `f2 = 1` (stored 2 = red); counters `8,8,8,8` | `pw_test_chk8.png` = accepted; `trophy2.png` = one red ribbon |
| `BBBV8+SBL` | identical complete state, alias spelling (bit 43) | `verify_SBL_result.png` = accepted; `alias_cont.png` = same final-race screen |
| `BBBV8+SBV` | identical complete state, alias spelling (bit 44) | `alias_SBV.png` = accepted |
| `BBBV8+SB5` | identical complete state, alias spelling (bits 43+44) | `alias_SB5.png` = accepted |
| `KBBV8+SBB` | course 1, complete otherwise | `pw_sp1_cont.png` = Primrose Hill Village |

### 6b.3 Bounds proven by rejection

| Input | Why it is out of bounds | Observed |
|---|---|---|
| `BBBBBBBBB` | check byte `0x00`, checksum demands `0x08` | "Password not Accepted" (`pw_BB.png`) |
| `BBBV8+SBC` | symbol 8 = 1 → check byte `0x20` (bit 40) | "Password not Accepted" (`pw_test_hi.png`) |
| `BBBV8+SBG` | symbol 8 = 4 → check byte `0x80` (bit 42) | "Password not Accepted" (`pw_sbg.png`) |
| `BBBV8+SVB` | symbol 7 = 16 → check byte `0x10` | "Password not Accepted" (`verify_SVB_result.png`, buffer visually verified as `BBBV8+SVB`) |

**Width bound.** `BBBV8+SBG` (bit 42 set) is rejected, so the mask includes
bit 42 → width ≥ 8. `BBBV8+SBL` (bit 43 set) is accepted, so bit 43 is
outside the mask → width ≤ 8. Therefore the check field is exactly 8 bits,
not 10 and not 6. `BBBV8+SBV` and `BBBV8+SB5` extend the alias set to both
high bits.

---

## 7. Validation evidence

### Observed

* Published `BBBV8+SBB` accepted; course select = Primrose Hill Final Race.
* Generated codes accepted; trophy case and course select change exactly as
  the decoded fields predict (`novel_trophy.png`, `trophy2.png`,
  `pw_sp1_cont.png`).
* Rejections of bad checksum and bad check-byte values (§6b.3).
* The blank `.sav` (0 bytes) plus the working "Your password is" screen code
  show the password is the save mechanism.
* Under the mGBA CLI debugger, breakpoint at `0x080B48A4` during
  `BBBV8+SBL`: `r8 = 0x03007DE4` pointed at
  `03 02 02 02 02 02 02 02 02 04 04 04 04 00`, `r10 = 13`,
  `r12 = 0x03001398` held `1,3,7,15,...`, and the comparison saw the
  checksum value `0` with the last field masked by the hardcoded `0xFF`.
* Menu walk: title, main, Continue/password, Options (sound/music/screen/
  credits), How To Play, hub, Stables (Dressing Room, Choose A Horse,
  Charity Photo Album, Trophy Case), Mini-Games (Horseshoes, Happy Trails,
  Shoe Shuffle, Maze Valley + instruction screens), Let's Race (course
  select, pre-race briefing, in-race HUD, pause, Exit confirm), Credits.
* Six title-screen button combinations (Select+Start, L+R+Start, Up+Start,
  Down+Start, A+B+Start, B-then-Start) all lead to the normal main menu.

### Derived

* Field widths/order and the XOR biases from the encoder (`0x080B46EC`)
  and decoder (`0x080B47E4`).
* The 8-bit check field from the hardcoded `table[7] = 0xFF` load at
  `0x080B48BC`.
* The checksum expression from `0x080B4740` and its `0x08` mask.
* The state struct offsets from `0x080B54AC` and the "Your password is"
  reader at `0x080A99D2`.

### Inferred

* That the four `f9`..`f12` counters are charity/coin counters; only their
  effect on the coin strip is proven.
* That `+0x2C` is the "horses sponsored"/progress index; the course-select
  mapping is observed, the label is inferred from the string bank.
* That the all-nonzero condition lights the strip; intermediate values
  (1 vs 8 vs 15) all produced the same gold strip.

### Negative-result searches (counts)

* `strings -n 4`: **44,158** strings. The
  `password|cheat|debug|secret|unlock|level` scan returned **19** lines,
  all classified: password UI in 5 languages, "Level Design:" credit roles,
  "LEVEL COMPLETE", and "secret shortcut/area" hint text. **No** `cheat`,
  `debug`, `unlock`, or `code` strings.
* Alphabet-literal scan: **1,200** runs of ≥9 alphabet characters, **290**
  exactly 9 characters, **0** NUL-terminated 9-character records, **0**
  copies of `BBBV8+SBB` or any other valid code. The system is algorithmic,
  not a table.
* Key-mask scan (`u16` values in `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}`):
  **1,040** contiguous runs ≥4; **8** are referenced by a literal pointer,
  and all 8 are runs of `0x0001` inside graphics/audio data, not button
  sequences. The input word is read once from `0x04000130` at `0x0806EDA0`;
  no sequence comparator/table was found.
* Menu walk found no hidden/debug screen. The only developer build banner is
  `Version BETA BUILD GMC5US` at `0x083BC200`, in a data bank, not reachable
  from any menu.

---

## 8. Unknowns

* Exact game meaning of the four 4-bit counters (`f9`..`f12`). They are
  independent in the password and all-nonzero lights the course-select coin
  strip; the individual counter names are not isolated.
* The trophy case's on-screen slot order is not the field order (field 1
  with value 3 produced the bottom-right empty slot). The permutation was
  not needed for the validator and was left unnamed.
* Origin of the zero header checksum. It is a header-only anomaly; the code
  and data behave like the retail game.
* The "Your password is" completion screen was located and its generator
  read, but a full event was not played to the results screen. The encoder
  was instead validated by reproducing the published code and by accepted
  generated codes.
* Other regional revisions (EU release) may relocate tables; all addresses
  here are tied to SHA-256 `52c26ad3…f68f27`.

---

## 9. Tooling

| Tool | Use |
|---|---|
| mGBA 0.10.5 (SDL) | Ground truth; `-3`, Xvfb `:168`, `SDL_AUDIODRIVER=dummy` |
| Xvfb + openbox + xdotool + scrot + ImageMagick | Headless display, key injection, cropped screenshots |
| Capstone 5.0.7 | Literal/literal-pool and key-mask scans |
| Ghidra 12.1.4 via REA MCP | Decompilation of `0x080B46EC`, `0x080B4700`, `0x080B4740`, `0x080B47A4`, `0x080B47E4`, `0x080B51F0`, `0x080B54AC` |
| mGBA CLI debugger (`mgba -d`) | Breakpoint at `0x080B48A4`, stack map and mask-table reads (GDB port 2345 was occupied by another session) |
| Python 3 | Encoder/decoder reimplementation and test-vector generation |

Analysis scripts (work directory `/tmp/opencode/barbiehorse/`):

* `pw.py` — alphabet, pack/checksum/encode/decode/valid, state mapping.
* `enter.py`, `verify_entry.py`, `typeonly.py` — deterministic password entry.
* `gba.py` — Xvfb/mGBA screenshot and key helper.
* `ss_raw.bin` — decompressed mGBA savestate used to read the RAM mask table.

Savestate: `Barbie Software - Horse Adventures: Blue Ribbon Race.ss1`
(entry screen). Screenshots referenced above: `title_now.png`, `menu02.png`,
`pw01.png`, `pw_BB.png`, `pw_known.png`, `pw_sp1_cont.png`,
`novel_result.png`, `novel_course.png`, `novel_trophy.png`, `trophy2.png`,
`none1_trophy.png`, `verify_SBL_result.png`, `alias_cont.png`,
`alias_SBV.png`, `alias_SB5.png`, `pw_sbg.png`, `verify_SVB_result.png`,
`pause2.png`, `options1.png`, `stables1.png`, `album_p1.png`,
`howto2.png`, `credits_a.png`.

---

## Legal note

No ROM, extracted graphics, music, or game text is redistributed with this
report. Only hashes, addresses, field layouts, algorithms, and the analyst's
own generated codes are published.
