# Curious George (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Curious George/Curious George.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `GEORGE` |
| Game code | `B3JE` (region J, USA) |
| Maker | `AF` (Ubisoft) |
| Software version | 0x00 |
| Entry word | `0xEA000030` → `0x080000C4` (stock crt0) |
| Header checksum word | `0x0000` (normal artifact of a rebuilt/linked header) |
| Complement check | `0x0D`, recomputed `0x0D` (header not damaged) |
| MD5 | `b70a1cfd17b2194ad99b2abf558aadf2` |
| SHA-1 | `7153a1e2b246c1997a91257480c67ac8b54fe61b` |
| SHA-256 | `e3ea35e9a3500c2625d5a8b559af974913330cc04d1930b0ae53809ddb93b1ad` |

Identity checks: exactly **one** 156-byte Nintendo logo in the whole file (file offset
`0x004`), so this is a single GBA image, not a multi-game pack. The first 4 KiB is the
stock Torus/MPL crt0 (no cracktro branch, no appended trainer, no `SUNHORS`/`MODE7`
strings). A zero header-checksum word plus a correct complement byte is the normal
signature of a rebuilt header, not of a hack.

## 2. Executive summary

The game has a developer **password system**, reached from the front end. It is a
checksum-protected 8-symbol code over a 16-symbol alphabet. Every published GBA
password except one was verified against the ROM's own validator; the exception
(`TNSDBHAG`) contains a character that does not exist on the keypad and is a
transcription error in the published lists.

The format was reversed completely (alphabet, bit layout, obfuscation, checksum,
semantic gate), reimplemented, and the model was checked **against the ROM's own
functions** (0x080018D8 check, 0x0800198C apply) executed in a Unicorn ARM/Thumb
emulation. 11/11 enterable published codes validate and reproduce their advertised
level and golden-clock state. The whole space was then enumerated and codes that
appear in no published list were minted, including level 4 (no published code
exists for it), plain levels 5/7/9, level 2 with one clock, and levels 14–15 which
are outside the published range. Bounds were proven by feeding the ROM validator
out-of-range codes and recording its rejection.

The password entry UI itself (`UIPasswordWatcher`, class ctor `0x08017A20`, a
29-step entry state machine at `0x08018C18`) could not be reached from the
front-end states the emulator settled in during this session (reason and the
complete button/screen search are in §7.4). The screen was therefore not typed
into; every acceptance claim below is labelled either *Observed* (emulator RAM),
*Derived* (ROM instruction sequence) or *ROM-emulated* (the ROM's own validator
run on synthetic input). Nothing is presented as an on-screen observation that was
not observed.

## 3. How to reproduce

### 3.1 Emulator

```
Xvfb :275 -screen 0 1024x768x24 &
DISPLAY=:275 openbox &
DISPLAY=:275 SDL_AUDIODRIVER=dummy mgba -3 "Curious George.gba"
```

mGBA 0.10.5, default SDL keymap (verified with `KEYINPUT` at `0x04000130`:
holding `Return` reads `0x3F7`, i.e. Start bit 3 low):

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L / R | `a` / `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Savestates: `Shift+F1..F9` writes `<rom>.ssN` next to the ROM. mGBA 0.10.5 writes a
PNG whose `gbAs` chunk is zlib-compressed; decompressing it yields the documented
397,312-byte state (`0x61000`), with I/O at `+0x400`, palette at `+0x800`, OAM at
`+0xC00`, VRAM at `+0x1000`, IWRAM at `+0x19000`, EWRAM at `+0x21000`.

### 3.2 Password screen

The published route is *main menu → Password*. In this session the front end never
left its two idle states (see §7.4), so the entry screen was not reached; the
static path to it is nevertheless fully identified (classes, alphabet table,
input buffer and validator in §4).

### 3.3 Codes tested

Published list (3rd party cheat indexes archive, 3rd party cheat indexes snippets):
`NPTJBHLQ`, `TNTDBHNQ`, `TNTDBHBQ`, `GPSDGHQP`, `PSTDHHSS`, `GQSDBHSP`,
`BGSDBHGP`, `TNSDBHAG`, `GCMJBHFP`, `HHGDBHQC`, `NPTDBHNG`, `BCHBBHSC`.

All were decoded and run through the ROM validator (§6). `TNSDBHAG` cannot be
entered (no `A` key); every other one validates.

## 4. Address map

File offset = ROM address − `0x08000000`. All addresses below are verified against
the bytes in this image.

| Address | Content |
|---|---|
| `0x02000000`+ | EWRAM: game/save struct, heap |
| `0x03000000`+ | IWRAM: engine globals; IRQ handler copied to `0x03002898` |
| `0x03000030` | **password input buffer**, 8 nibble slots (0–15), slot 0 = low nibble of the packed word |
| `0x03002080` | 16-word RAM copy of the keypad-letter pointer table (always present) |
| `0x0806BA38` | **keypad alphabet table**, 16 records × 8 bytes: `{u8 letter; 'B','B','B'; u32 0}` → `B C D F G H J K L M N P Q R S T` |
| `0x0803E2A74` | ROM pointer table of the 16 alphabet records (`0x0806BA38+8*i`) |
| `0x0806A8C8` | entity registry: `{0,0, ctor 0x0801B375, "UI_PasswordCharacter"}` |
| `0x0806A8D8` | entity registry: `{0,0, ctor 0x08017A21, "UI_PasswordWatcher"}` |
| `0x08017A20` | `UI_PasswordWatcher` constructor (Thumb) |
| `0x08018C18` | watcher step dispatcher, jump table at `0x08018C40` (29 entries). Step 0..28; invalid step → `0x0801A4A2` |
| `0x080188A0` | keypad-character handler: writes the selected nibble to `0x03000030 + slot` |
| `0x0801890C` | **packer**: reads 8 nibbles from `0x03000030`, builds `v = Σ nib[i]<<(4i)` |
| `0x0800198C` | **apply(password)**: `global` in r0, packed `v` in r1 → 1 accepted / 0 rejected |
| `0x080018D8` | **validator**: `global` in r0, *mixed* 32-bit value in r1 → 1/0 |
| `0x08001A94` | 7-bit checksum from the payload bytes (CRC-16/ARC + popcount fold) |
| `0x08050D10` | CRC-16/ARC over (buf,len), init `0xFFFF`, table at `0x083DA86C` |
| `0x08001504` | writes the 14-byte level-progress array at `global+0xB4`: `<L` → 2, `==L` → 1, `>L` → 0 |
| `0x080016CC` | golden-clock gate: for every set mask bit, requires `progress[i] > 1`, sets it to 4 |
| `0x08000C90` | **dead** debug-screen initialiser (`"Player Debug Screen"`, `0x0806A0FC`); no BL/BX/pointer reaches it in this build |
| `0x083D6000` | text bank base; `"PASSWORD"` at `0x083D88E9` |
| `0x081033C0` | scene entity-type name table (includes `UI_LevelSelect`, `UI_PasswordWatcher`) |

## 5. Algorithm

### 5.1 Decoding (ROM order)

```
ALPHA = "BCDFGHJKLMNPQRST"          # 16 symbols, keypad order
v = Σ_i ALPHA.index(code[i]) << (4*i)      # 32-bit packed word

# invertible obfuscation, constants from 0x0800198C
m  = mix(v)
mix(x):
  r2 = ((x>>1) ^ x) & 0x22222222 ; x = x ^ r2 ^ (r2<<1)
  r2 = ((x>>2) ^ x) & 0x0C0C0C0C ; x = x ^ r2 ^ (r2<<2)
  r2 = ((x>>4) ^ x) & 0x00F000F0 ; x = x ^ r2 ^ (r2<<4)
  r2 = ((x>>8) ^ x) & 0x0000FF00 ; x = x ^ r2 ^ (r2<<8)
  return x ^ 0xA07FBD36
```

`unmix` is the same reduction in reverse order (verified round-trip on 2^32 samples).

### 5.2 Field layout of `m` (little-endian bytes b0..b3)

| Bits | Width | Meaning |
|---|---|---|
| 0–6 | 7 | field **A** (stored to `global[0] = min(A+1, 99)`) |
| 7–13 | 7 | **checksum** |
| 14–27 | 14 | **golden-clock mask**, bit *i* = level *i*+1 completed |
| 28–31 | 4 | **level**−1 (0 → level 1 … 14 → level 15) |

### 5.3 Checksum

```
payload bytes = [ b0 & 0x7F, b1 & 0xC0, b2, b3 ]     # payload only, check bits cleared
crc  = CRC16_ARC(payload, init=0xFFFF)               # table 0x083DA86C
pc   = popcount(crc)                                 # 1..16
chk  = ((crc % pc) + 1) | ((pc & 1) << 6) | ((crc & 1) << 5)   # 7 bits
valid_chk = (chk == (b0>>7) | ((b1 & 0x3F) << 1))
```

`0x08001A94` implements the fold with BIOS `SWI 6` (Div); the wrapper at
`0x08066CCE` returns the **remainder**, not the quotient (`svc 6; adds r0,r1; bx lr`).

### 5.4 Semantic layers (in order, all inside `0x0800198C`)

1. `0x080018D8`: checksum equality; `A+1 ≤ 99`; `(b3>>4) ≤ 14`.
2. `0x08001504(global, b3>>4)`: rewrites the progress array (levels below current = 2, current = 1, later = 0).
3. `0x080016CC(global, 14-bit mask)`: for each set mask bit *i*, requires `progress[i] > 1` and then stores 4. Any mask bit at or after the current level fails and the function returns 0.

Consequence: a code with a valid checksum but an impossible mask still **writes the
level progress** before it is rejected, so the UI would say "try again" while the
save has already advanced.

### 5.5 Encoding (mint a code)

```
choose level L (1..15), mask M (0 .. 2^(L-1)-1), A (0..98)
m = A | (M << 14) | ((L-1) << 28)
m |= checksum(m) << 7
v = unmix(m)
code[i] = ALPHA[(v >> (4*i)) & 15]
```

## 6. Tables

### 6.1 Keypad alphabet (ROM `0x0806BA38`, order matters)

```
index : 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15
letter: B C D F G H J K L M N  P  Q  R  S  T
```

There is no `A`, `E`, `I`, `O`, `U`, `V`, `W`, `X`, `Y`, `Z` on the keypad.

### 6.2 Published codes decoded and run through the ROM

| Published code | Level | Clock mask | A | ROM validator | ROM apply → progress array |
|---|---|---|---|---|---|
| `NPTJBHLQ` | 1 | 0 | 2 | accept | `1 0 0 …` |
| `TNTDBHNQ` | 2 | 0 | 5 | accept | `2 1 0 …` |
| `TNTDBHBQ` | 3 | 0 | 5 | accept | `2 2 1 0 …` |
| `GPSDGHQP` | 5 | 15 (4 clocks) | 16 | accept | `4 4 4 4 1 0 …` |
| (none published) | 4 | — | — | — | — |
| `PSTDHHSS` | 6 | 0 | 15 | accept | `2 2 2 2 2 1 0 …` |
| `GQSDBHSP` | 6 | 31 (5 clocks) | 28 | accept | `4 4 4 4 4 1 0 …` |
| `BGSDBHGP` | 7 | 63 (6 clocks) | 30 | accept | `4×6 1 0 …` |
| `GCMJBHFP` | 8 | 127 (7 clocks) | 32 | accept | `4×7 1 0 …` |
| `HHGDBHQC` | 9 | 255 (8 clocks) | 25 | accept | `4×8 1 0 …` |
| `NPTDBHNG` | 10 | 0 | 2 | accept | `2×9 1 0 …` |
| `BCHBBHSC` | 10 | 511 (9 clocks) | 2 | accept | `4×9 1 0 …` |
| `TNSDBHAG` | — | — | — | **cannot be entered** | `A` is not a symbol |

Progress values: 0 = locked, 1 = current, 2 = completed, 4 = completed with the
level's golden clock collected.

`TNSDBHAG` is a published-list error. The only 1-character substitution of that
string that validates is `TNSDBHQG` (level 9, mask 0), so the "Level 8" entry in
the published lists cannot be reconstructed from the string as given.

## 6b. Enumeration

**Space definition.** 8 symbols × 4 bits = 32 bits, partitioned as
A (7 bits, 99 legal values 0–98) × clock mask (14 bits, but at level *L* only bits
`0..L-2` are legal) × level (4 bits, 15 legal values → levels 1–15) × checksum
(7 bits, fully determined by the payload).

```
|accepted| = 99 × Σ_{L=1..15} 2^(L-1) = 99 × (2^15 − 1) = 3,243,933 codes
```

Reserved/illegal: level nibble 15 (would be level 16) is rejected by
`0x0800193A`; A = 99..127 is rejected by `0x08001930`; mask bits at or after the
current level are rejected by `0x080016CC`.

**Novel codes (in no published list) and their ROM-verified effects.** These were
generated with §5.5 and executed through the ROM's apply function
`0x0800198C`; the returned value and the 14-byte progress array at
`global+0xB4` are the effect.

| Novel code | Level | Clocks | Effect (ROM apply) | Result |
|---|---|---|---|---|
| `SPTJCHKQ` | 4 | 0 | `2 2 2 1 0 …` (advance to level 4) | accept |
| `QPTJBHDM` | 4 | 3 | `4 4 4 1 0 …` (levels 1–3 clocks) | accept |
| `SPTDHHLS` | 5 | 0 | `2 2 2 2 1 0 …` | accept |
| `SPTJCHHS` | 7 | 0 | `2×6 1 0 …` | accept |
| `SPTDBHLG` | 9 | 0 | `2×8 1 0 …` | accept |
| `SPTJCHTR` | 2 | 1 | `4 1 0 …` | accept |
| `NPNDCGGM` | 3 | 2 | `4 4 1 0 …`, A=50 | accept |
| `SPTJCHNJ` | 14 | 0 | `2×13 1 0` | accept |
| `SPTDHHBJ` | 15 | 0 | `2×14` (max level) | accept |
| `BCCMNTGF` | 15 | 14 (all) | `4×14` | accept |

**Bounds proven by rejection (ROM validator).**

| Input | Why illegal | Result |
|---|---|---|
| `JPTJCHDQ` | level 4 (index 3) but mask bit 3 set → clock for the level being entered | checksum OK, apply = **0** (progress still written: `2 2 2 1 …`) |
| `GPTJCHKM` | level 4, mask 15 | checksum OK, apply = **0** |
| `SPTJCHKJ` | level nibble 15 (level 16) | validator = 0, nothing written |
| `PPPKGHKQ` | A = 99 | validator = 0 |
| `PSNKGHDQ` | A = 127 | validator = 0 |

**Coverage check.** 150 random `(L, mask, A)` payloads in the legal ranges were
encoded, decoded by the model, and applied by the ROM function: 150/150 accepted
with exact level/mask/A round-trip. The 11 enterable published codes agree with the
ROM bit-for-bit.

## 7. Validation evidence

### 7.1 Observed (emulator / savestate RAM)

* ROM header, single logo, stock entry, complement check.
* The 16-word alphabet pointer table is live in IWRAM at `0x03002080` in every
  savestate from boot onwards (state offset `0x1B080`), proving the password
  subsystem is initialised at boot and not lazily.
* `KEYINPUT` (`0x04000130`) = `0x3F7` with `Return` held (Start bit low), so the
  keymap and input path used by the front end are correct.
* `0x03000030` (the password buffer) is all zero in every captured state.
* `global` (`*(u32*)0x03000C20`, the object the password apply uses) is 0 in every
  front-end state captured.

### 7.2 Derived (instruction sequence)

* Alphabet table, packer (`0x0801890C`), buffer address (`0x03000030`), apply
  (`0x0800198C`), validator (`0x080018D8`), checksum fold (`0x08001A94`), CRC table
  and init (`0x083DA86C`/`0xFFFF`), progress writer (`0x08001504`) and mask gate
  (`0x080016CC`) were read from the disassembly listed in §4.
* The `Player Debug Screen` (`0x0806A0FC`) initialiser `0x08000C90` has **no BL,
  BX or pointer reference** anywhere in the image (full-file BL scan and literal
  pointer scan), so the debug menu is dead code in this build.

### 7.3 ROM-emulated

The ROM functions `0x080018D8`, `0x08001A94` and `0x0800198C` were executed in
Unicorn 2.1.4 (ARM/Thumb, ROM mapped at `0x08000000`, EWRAM/IWRAM mapped, `SWI 6`
implemented as the ARM Div SWI). This is not a reimplementation guessing: it is
the shipped code path, including its CRC table and its BIOS div wrapper.

### 7.4 Password screen reachability (negative, bounded)

The front end was walked with `KEYINPUT`-verified presses. The stable states were:

* `DISPCNT = 0x1340` (BG0+BG1+OBJ) — title/menu screen, sparse BG0 tile block at map
  `0x2800` (tiles `0..0x87`), BG1 frame at map `0x3000`, 63–69 OAM sprites;
* `DISPCNT = 0x1F40` (BG0..BG3+OBJ) — animated 4-layer scene (BG maps
  `0xB800/0xB000/0xC800/0xC000`), stable for minutes with no input.

Buttons tested on every reachable state: `A, B, L, R, Start, Select, Up, Down,
Left, Right`, in single presses, repeated presses, and with 2–3 s waits between
presses; `Start` toggles between the two display states, `A`/`B` restart the
animated scene. No transition produced a non-zero `0x03000030`, a pointer array in
EWRAM to the 16 keypad records, or a non-zero `global`.

Hardware breakpoints were exercised through the mGBA GDB stub: a control
breakpoint on the per-frame IRQ handler `0x03002898` fires on every frame, and a
breakpoint on `UIPasswordWatcher` ctor `0x08017A20` was held while the whole
button set above was pressed; it did not fire. The blocker is therefore the
front-end navigation path, not the password code: the password classes and
validator are present and correct, but this session could not drive the front end
to the menu that instantiates them.

### 7.5 Reproducing the offline validation

```
pip install --break-system-packages unicorn
python3 model.py          # mix/unmix self-test
python3 - <<'PY'
from model import *
from emu import Emu
e = Emu()
# 0x080018D8 takes the *mixed* word; 0x0800198C takes the *packed* nibbles
print(e.call(0x080018D8, [0x02010000, decode("SPTJCHKQ")]))      # -> (1, None)
print(e.call(0x0800198C, [0x02010000, 0x...packed word...]))     # progress array
PY
```

`emu.py` maps the ROM at `0x08000000`, EWRAM at `0x02000000`, IWRAM at
`0x03000000`, and replaces the `SWI 6` div wrapper at `0x08066CCE` with the ARM
`Div` semantics (`r0/r1`, remainder returned to match `svc 6; adds r0,r1; bx lr`).

## 8. Unknowns

* **Field A's meaning.** `apply` stores `min(A+1,99)` at `global+0`. Its readers
  were not identified; it is probably a counter/score, not a level or clock field.
  All published codes carry small values (2–32), and A=0..98 are legal.
* **Exact front-end path to the Password entry.** The published route is
  "main menu → Password"; the front-end state machine in this session never
  advanced to an interactive map/password scene, so the on-screen entry could not
  be performed. The screen's code path (§4) is identified but was not exercised.
* `TNSDBHAG` (published "Level 8") is not enterable; its intended characters
  cannot be recovered from the string. The nearest valid substitution is
  `TNSDBHQG` (level 9).

## 9. Tooling

* mGBA 0.10.5 (SDL), Xvfb :275, openbox, xdotool.
* `state.py` — extracts the zlib `gbAs` chunk from `.ssN` savestates.
* `screen.py` — GBA I/O/palette/OAM/VRAM decoder (BG tilemaps, text-mode offsets).
* `pwd.py`, `model.py` — alphabet, mix/unmix, CRC-16/ARC, checksum fold,
  encode/decode; `emu.py` — Unicorn harness for `0x080018D8/0x08001A94/0x0800198C`.
* `probe.py`, `gdbrpc.py`, `gdbd.py` — GDB-stub helpers used for live checks
  (`KEYINPUT`, breakpoint watch on the watcher ctor).
* No ROM, graphics or game text is redistributed; only addresses, code paths and
  generated codes appear above.

## Legal note

No ROM image or extracted asset is included. All examples are either published
codes quoted for verification or codes generated by the algorithm in this report.
