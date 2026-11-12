# Cubix: Robots for Everyone — Clash 'n Bash (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Cubix: Robots for Everyone: Clash 'n Bash.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| Header title | `CUBIX_GBA` (0xA0, space/NUL padded) |
| Game code / maker | `ACXE` / `5H` |
| Software version | 00 |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| Complement check | `0x0F` (matches computed value) |
| Header checksum field (0xBE) | `0x0000` (reserved field; normal) |
| Nintendo logo instances | 1, at file `0x4` (no second/sub-image header) |
| MD5 | `4a5a274a7c2514b21ebb43b2ceade091` |
| SHA-1 | `9e5aed84668e5838cb58a3c33e8d6db7a85fd536` |
| SHA-256 | `fb5a1df23b68730d7fe40ab3e70368a4c0aee108cb4c221328a029cbf4179660` |
| CRC32 | `4171C811` (matches the known USA Redump/No-Intro entry) |

No patch/trainer: the entry branch is the stock one, the first 4 KiB is the stock
crt0, and none of the known cracktro banners (Mode7, SUNHORS, CRC BANDIT)
is present. mGBA creates a 512-byte `rom.sav`, i.e. the EEPROM save type, and
the image is never written by the game during the tests below.

## 2. Executive summary

**This ROM has no in-game password, button code, debug menu or hidden input
screen.** The only text-entry surface is a 6-character player-name field whose
alphabet is `ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789`; its only cross-reference is
the name-entry append routine, and the buffer is drawn, never compared against
anything.

Every published cheat for this title is a CodeBreaker/GameShark **memory write**
(e.g. `33001411 0003`, `83001402 FFFF`, `42000608 FFFF 0000000D 0002`). None of
those opcode strings exists in the ROM (searched as ASCII, lower case and
UTF-16 in both endiannesses), and there is no screen that consumes such a
string. The *addresses* in those codes, however, are real progression fields,
and this report identifies them:

* `0x03001402` — 16-bit VS-location unlock bitmap (the game ORs `0x0080` into it
  after a location result at `0x08010F04`);
* `0x0300141F` — 8-bit robot unlock bitmap (one bit per robot, 8 robots; ships
  as `0x01`);
* `0x02000608` — 104-photo gallery bitmap, 2 bits per photo, pointer stored at
  progression-struct `+0x4C` (`0x030013FC`);
* `0x03001411` — progression/tier byte; the only ROM writer increments it
  0→1→2 and clamps at 2 (`0x080274DC`), so the published value `3` is a state
  the game itself cannot produce.

The interactive surface could not be exercised beyond the boot sequence: after
the legal screens the game enters screen state 6 and, in every run, ignored all
pad input (a controlled idle-vs-held comparison changed 0 VRAM bytes, 1 OAM byte
and 1 EWRAM byte). The state-6 handler's A/B branch is additionally gated on a
byte fetched by dereferencing the key word as a pointer (`0x08027D10`), which can
never fire on hardware or in emulation. This is reported as a bounded negative,
not as "I did not find it": the code-space searches in §6b are exhaustive over
the whole image.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL, `SDL_AUDIODRIVER=dummy`, 3× scale, Xvfb `:274`.
Analysis reads used mGBA's command-line debugger (`mgba -d`, `r/1`, `x/4`,
`save`/`load`) plus decoding of the `gbAs` chunk of `.ssN` savestates.

Keymap used (mGBA SDL defaults):

| GBA | key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Observed boot path:

1. Boot. Screen state `0x03000B78` (byte) = `0x1B` (27) for ~24 s: the
   boot/legal sequence at `0x08001174`, 11 sub-states in `0x0300143C`,
   observed as `2 → 3 → 4 → 6 → 8 → 9 → 10`.
2. Sub-state 10 counts 250 frames (`0x080015EC`) and hands off; it writes
   state `5` (`0x080015FE`), and the state-5 routine calls the overworld setup
   at `0x08027B60`, which writes state `6` (`0x08027C02`). The `5` step is
   derived from these instructions; the sampled states were `0x1B` then `0x06`.
3. State 6 is static: two seconds apart with no input produced **0 differing
   bytes in VRAM**, 1 byte in OAM and 1 byte in EWRAM. `0x030013A0` (frame
   counter) advances about 61 per second, so the CPU is running. A 200-second
   unattended run stayed in state 6 (frame counter `0x2BFC`). Booting with the
   save type forced to SRAM produced the same 512-byte EEPROM image and the
   same state-6 stall, so this is not a save-type-detection hang.
4. `0x03001E60` is a free-running UI/attract byte that alternates `0x00` and
   `0x90` on its own roughly once a second (observed with no input); it is not
   a pause flag.

RAM checks:

```
r/1 0x03000B78      ; screen state
x/4 0x030013A0      ; frame counter
r/1 0x03001E60      ; UI/attract byte
x/4 0x030013B0      ; progression struct (see §4)
```

Input rejection tests (all read back at `0x03000B78` / `0x03001E60`):

| Test | Result |
|---|---|
| Boot holding `Select` | state stays `0x1B` |
| Boot holding `Start` | state stays `0x1B` |
| Boot holding `A+B+Start+Select` | state stays `0x1B` |
| Boot holding `L+R+Start` | state stays `0x1B` |
| Boot holding `L+R+Select` | state stays `0x1B` |
| Boot holding `Start+Select` | state stays `0x1B` |
| Konami sequence at state 6 | state stays `0x06` |
| Six rounds of all-button mashing | state stays `0x06` |
| Hold Right for 2 s from a savestate | 0 VRAM, 1 OAM, 1 EWRAM byte differ from a 2 s idle run |

## 4. Address map

| Address | Meaning |
|---|---|
| `0x080000C0` | ARM crt0 entry |
| `0x080006C8` | `main` (Thumb) |
| `0x080008A4` | screen dispatcher: `ldrb` from `0x03000B78`, `sub #2`, `cmp #29` |
| `0x08000948` | 30-entry handler table, states 2..31 |
| `0x08001174` | boot/legal sub-state machine (11 entries, table `0x08001198`) |
| `0x08001890` | key sampler: `prev ← cur`, `cur ← ~KEYINPUT` |
| `0x080018AC` | only literal `0x04000130` (KEYINPUT) in code |
| `0x080019A0` | arena allocator used by screen setup |
| `0x080027B60` | state-6 (overworld) setup; writes state at `0x08027C02` |
| `0x08027CB4` | state-6 per-frame routine |
| `0x08027D10` | state-6 A/B gate: `ldr r0,[0x03001394]; ldrb r0,[r0]` (key word used as a pointer) |
| `0x08010E40` | front-end/result menu: ORs `0x0080` into `[0x03001402]` at `0x08010F04` |
| `0x080237BA` | reads `save[0x61]`, computes `14 << save[0x61]` (tier scaling) |
| `0x08024358` | name-entry character append; alphabet `0x0803D530`, capped at 6 chars |
| `0x080274C4` | tier counter writer: `if save[0x60]==save[0x61] and both <=2 then save[0x61]++`, then `save[0x60]=0` |
| `0x08031D6A` | gallery counter: entries 96..103, 2-bit fields at `[0x030013B0+0x4C]` |
| `0x0803D530` | `ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789` (36 symbols) |
| `0x08040BF4` | `" of 104"` (gallery text) |

RAM:

| Address | Meaning |
|---|---|
| `0x03000B70` | fade direction (signed) |
| `0x03000B74` | previous key word |
| `0x03000B78` | screen state (2..31) |
| `0x03000B7C` | fade level |
| `0x03001394` | current key word (`~KEYINPUT`, observed `0xFC00` idle, `0xFC08` with Start) |
| `0x030013A0` | frame counter |
| `0x030013B0` | progression struct base |
| `0x030013FC` (`+0x4C`) | u32 pointer to photo bitmap = `0x02000608` |
| `0x03001402` (`+0x52`) | u16 VS-location unlock bits |
| `0x03001410/11` (`+0x60/61`) | tier counter pair; `+0x61` is the "Extreme" target |
| `0x0300141F` (`+0x6F`) | u8 robot unlock bits |
| `0x02000608` | 104 × 2-bit photo bitmap (28 bytes used) |
| `0x03001E60` | free-running UI/attract byte (`0x00`/`0x90`) |

Progression-struct prefix (observed at boot): four 12-byte records beginning
with ASCII `'1'`, `'2'`, `'3'`, `'4'`, then counters, then the fields above.

## 5. Algorithm

### 5.1 Input

```
per frame:
    prev = cur                    ; 0x03000B74 = 0x03001394
    cur  = (~KEYINPUT) & 0xFFFF   ; 0x03001394
```

Only previous and current key words are kept. There is no press-history ring
buffer and no `strcmp`/`strncmp` against any input buffer.

### 5.2 Screen dispatch

```
state = *(u8*)0x03000B78
if 2 <= state <= 31:
    call jump_table_0x08000948[state-2]
```

### 5.3 State-6 A/B gate

```
0x08027D10:  ldr  r1, =0x03001394    ; key word storage
0x08027D12:  ldr  r0, [r1]           ; r0 = 0x0000FC00 (key word itself)
0x08027D14:  ldrb r0, [r0]           ; read byte at 0x0000FC00 (BIOS)
0x08027D16:  subs r0, #1
0x08027D1E:  cmp  r0, #1
0x08027D20:  bhi  skip               ; 0x00-1 -> 0xFF, always > 1
```

The A/B branch can never be taken with a real key word; this is why the pad does
nothing on state 6. (Derived from the instruction sequence; consistent with the
idle-vs-held observation.)

### 5.4 Gallery bitmap decode (`0x08031D6A`)

```c
u8* photos = *(u8**)0x030013FC;      /* == 0x02000608 */
int n = 0;
for (int i = 96; i <= 103; i++) {    /* one page of 8 entries */
    int v = (photos[i >> 2] >> ((i & 3) * 2)) & 3;
    if (v) n++;
}
```

Confirms 2 bits per photo and the 104-photo count string.

### 5.5 Tier counter (`0x080274C4`)

```c
u8 a = save[0x60], b = save[0x61];
if (b <= 2 && a <= 2 && a == b) save[0x61] = b + 1;
save[0x60] = 0;
```

Maximum value the game itself writes is 2; the published CodeBreaker code
writes 3.

## 6. Tables

### 6.1 Screen states (handler addresses from `0x08000948`)

| State | Handler | State | Handler |
|---:|---|---:|---|
| 2 | `0x080009C6` | 17 | `0x08000B28` |
| 3 | `0x080009C0` | 18 | `0x08000ABA` |
| 4 | `0x080009D8` | 19 | `0x08000B5E` |
| 5 | `0x080009F6` | 20 | `0x08000AC6` |
| 6 | `0x080009FC` | 21 | `0x08000ACC` |
| 7 | `0x08000A9C` | 22 | `0x08000B5E` |
| 8 | `0x080009DE` | 23 | `0x08000AD2` |
| 9 | `0x080009E4` | 24 | `0x08000B2E` |
| 10 | `0x080009EA` | 25 | `0x08000B3A` |
| 11 | `0x080009F0` | 26 | `0x08000B40` |
| 12 | `0x08000AA2` | 27 | `0x08000B46` |
| 13 | `0x08000AAE` | 28 | `0x08000B4C` |
| 14 | `0x08000AB4` | 29 | `0x08000B52` |
| 15 | `0x08000AD8` | 30 | `0x08000B5E` |
| 16 | `0x08000B5E` | 31 | `0x08000B64` |

Immediate-constant writers to `0x03000B78` were located for states
2, 3, 4, 5, 6, 7, 9, 10, 11, 13, 14, 16, 17, 19, 20, 21, 22, 23, 25, 26, 27,
28, 29, 30, 31. No writer sets a password/cheat flag.

### 6.2 Boot sub-states (`0x0300143C`, 11 handlers from `0x08001198`)

`2 → 3 → 4 → 6 → 8 → 9 → 10` observed; sub-state 10 counts 250 frames and
hands off to state 5, which sets up state 6.

### 6.3 Published codes and what they really touch

| Published code (CodeBreaker/GameShark) | Target | Field |
|---|---|---|
| `33001411 0003` "Open Extreme Mode" | `0x03001411` | tier byte `+0x61`; game range 0..2 |
| `83001402 FFFF` "Unlock All VS Levels" | `0x03001402` | 16-bit location bitmap `+0x52` |
| `3300141F 00FF` "Unlock All Robots" | `0x0300141F` | 8-bit robot bitmap `+0x6F` |
| `42000608 FFFF 0000000D 0002` "Unlock All Photos" | `0x02000608`, 14×u16 | 104 × 2-bit photo fields |
| Enable/master codes, infinite health/lives/laser/mines/rockets, max stats | `0x0300xxxx` gameplay vars | runtime, not progress |

The bitmap sizes line up exactly: 104 photos × 2 bits = 208 bits = 26 bytes,
inside the 28 bytes the code writes. At boot the robot byte reads `0x01` and the
photo bitmap is all zero.

### 6.4 Text banks

Only two ASCII text banks exist: `0x3C3C4–0x3D5xx` (licence/credits/tutorial)
and `0x409xx–0x417xx` (gallery names and multiplayer result strings). Menu
labels are drawn from graphics and never appear as bytes.

## 6b. Enumeration

### Space definition

* **Password space: empty.** The image contains no password field, no
  password alphabet, no length check and no validator. `PASSWORD`, `PASS`,
  `CODE`, `CHEAT`, `DEBUG`, `SECRET` occur 0 times in ASCII, 0 times in
  lower case, 0 times in UTF-16LE and 0 times in UTF-16BE across all
  8,388,608 bytes. `UNLOCK` occurs once, inside tutorial prose at `0x3CD9C`;
  the only lower-case `temp` hit is inside a compressed graphics block at
  `0x20AF1A`, not text.
* **Only alphabet in the ROM:** `ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789`
  at `0x3D530`, 36 symbols, one cross-reference (`0x08024358`, name entry).
  Entry is capped at 6 characters (`cmp #6`) and the buffer is drawn only.
* **Button-code space: no table.** A full 16-bit scan of the ROM (every 2-byte
  offset) for runs of 4+ single-button masks in the active-high encoding
  `{1,2,4,8,0x10,0x20,0x40,0x80,0x100,0x200}` found 148 runs; the longest are
  filler runs of one repeated value (e.g. 600 × `0x0001` at `0x071544`), and
  only 15 runs contain 3+ distinct values — all inside numeric data tables
  whose values are not button masks (e.g. `0x0100,0x0002,0x0100,0x0001` at
  `0x040A64`). The active-low complement encoding produced 0 runs. The Konami
  sequence in both polarities is absent. Because the input sampler keeps only
  previous/current key words, no last-N matcher can exist.
* **Unlock / progression space (the only "code-like" state):**
  * robots: 8 bits → 256 states (shipped `0x01`);
  * VS locations: 16 bits → 65,536 states (one bit per cleared location);
  * photos: 104 entries × 2 bits → 4^104 states (bitmap at `0x02000608`);
  * tier: 3 values the game writes (0..2), plus the out-of-range value 3 the
    published device code writes.

### Novel values

No in-game code can be minted, because no code is ever accepted. Tested
rejections (in mGBA, read back from RAM) are the nine rows in §3.

### Bounds proven by rejection/limits

* The tier writer refuses values above 2 (`0x080274DC`: `cmp r2,#2 ; bhi`), so
  the published "Extreme" value `3` is outside the game's own domain.
* The VS bitmap is a `u16`; the published `FFFF` sets all 16 bits, the whole
  representable space.
* The robot bitmap is one byte; `FF` covers all 8 bits.
* The gallery code masks every entry with `& 3`, so `FFFF` fills 2-bit fields
  with the maximum value; there is no fifth state.
* The only text field (6-char name) has no comparison against it, so there is
  no accepted-input space to enumerate.

## 7. Validation evidence

**Observed**

* mGBA boot: `0x03000B78` = `0x1B`, then `0x06`; `0x030013A0` increments
  ≈61/s.
* `0x03001394` = `0xFC00` idle and `0xFC08` while Start is held, proving the
  key sampler runs and sees the pad.
* Two seconds of idle vs two seconds of held Right from the same savestate:
  0 VRAM bytes changed, 1 OAM byte, 1 EWRAM byte.
* `0x03001E60` alternates `0x00 ↔ 0x90` with no input.
* `0x030013FC` contains `0x02000608`, the exact address in the published photo
  code.
* `[0x030013B0+0x6F] = 0x01` and the photo bitmap is all zero at boot.

**Derived**

* Screen dispatcher and 30-entry table at `0x08000948`.
* Key sampler at `0x08001890` (only KEYINPUT read).
* State-6 A/B gate dereferences the key word (`0x08027D10`), so it cannot be
  taken with `0xFC00`.
* Photo 2-bit decode at `0x08031D6A`; 104-photo count string.
* Tier clamp at `0x080274C4`; tier reader `14 << save[0x61]` at `0x080237BA`.
* VS bitmap OR of `0x0080` at `0x08010F04`.
* Name entry capped at 6 chars and never compared.

**Inferred**

* State 6 is the Bubble Town overworld (its setup allocates map buffers and the
  tutorial text refers to pausing "IN MAP"); why it ignores input is explained
  by the dead A/B gate, but Start/D-pad handling in the rest of that routine
  was not traced to a single consumer.
* The four 12-byte records at the struct base are per-player records (they
  begin with ASCII `'1'..'4'`, consumers not traced).
* The `+0x61` byte is a difficulty/progression tier; the increment at
  `0x080274C4` and the scaling read at `0x080237BA` fit that reading, but no
  on-screen difficulty label was decoded.

## 8. Unknowns

* What state 6 is waiting for (if anything). All pad input is ignored; the
  screen is static; the CPU and frame counter run. The dead A/B gate explains
  A/B but not Start/D-pad.
* The exact semantics of the `+0x60/+0x61` pair (difficulty vs. chapter
  counter); only the write range 0..2 and the read scaling are proven.
* Whether the published "Extreme" value `3` has a visible effect; it is outside
  the game's writer range and the label screen was not reached.
* Save-file encoding/checksum inside the 512-byte EEPROM image was not
  reversed; progression work was done on the live IWRAM copy.
* Menu labels are graphics, so no menu-item text could be enumerated; the
  negative for codes does not depend on them.

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` for all disassembly.
* Capstone 5.0.7: literal-pool scans (`ldr =0x03000B78`, `=0x03001E60`),
  `strb` immediate-constant writer scan, key-mask run scan.
* mGBA 0.10.5 SDL with `-d` command-line debugger for `r/1`/`x/4` reads,
  watchpoints and `save`/`load` slots.
* Python: `.ssN` PNG `gbAs` chunk (zlib) decoder and a GBA BG/OBJ compositor
  used to inspect text layers as ASCII; no image files were used as evidence.
* Xvfb `:274` + openbox + xdotool for input.

## 10. Legal note

No ROM, extracted graphics, audio or text assets are redistributed here.
Only hashes, addresses, decoded field layouts and behavioural observations
are published.
