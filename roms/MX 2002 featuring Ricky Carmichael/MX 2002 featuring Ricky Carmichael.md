# MX 2002 featuring Ricky Carmichael (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `MX 2002 featuring Ricky Carmichael.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `MX 2002` |
| Game code | `A2XE` (maker `78`) |
| `file(1)` code | A2XE78, Rev.00 |
| Version / complement | 0x00 / 0x49 |
| Header checksum | 0x0000 |
| Entry branch | `0xEA00002E` → 0x080000C0 (stock) |
| MD5 | `0007d212d9b76a466c7ca003d50c8c74` |
| SHA-1 | `87914981ee89219a0fa28833fb9d9f6e9b606d57` |
| SHA-256 | `e01905f82a2fdb8fb1d6d8a6eb2c0ab9161a755a657af71bfa80245d60a81abf` |

**Phase 0 result:** clean retail image. A scan of all 4 MiB for the 156-byte Nintendo
logo finds exactly one header, at file offset `0x4` (the real one). No multi-game
pack, no appended trainer, no patched/cracktro entry word. The nonzero complement
byte (0x49) and stock entry branch further indicate an unmodified header.

## 2. Executive summary

The GBA SKU is a **different game** from the PS2 title: published PS2 button codes
("OPEN IT ALL", "level select via L2/R1 …") do not exist in this ROM. The only
developer-intended cheat surface in the GBA image is the **Restore (password)
screen**, which contains:

1. **A hidden debug code: `CHT`** (three keypresses on the on-screen keyboard).
   Entering it and pressing START displays **"Debug Mode On"** and sets an IWRAM
   flag. This is a genuine, previously undocumented in-game code.
2. **A full checksummed progress-password system** (19–20 symbols from a
   32-glyph alphabet, 5 bits per symbol). It is a *generator + validator* pair,
   not a fixed lookup table, so arbitrary career states can be minted. Multiple
   unpublished codes were generated and accepted on the real screen.

No GameShark/CodeBreaker codes are reported (out of scope); the web results for
this title are almost entirely such memory-patch codes plus PS2 button codes,
none of which apply to this ROM.

## 3. How to reproduce

Emulator: mGBA 0.10.5, `DISPLAY=:316` under Xvfb + openbox,
`SDL_AUDIODRIVER=dummy`, `mgba -3 mx2002.gba`. Key map used: A=`x`, B=`z`,
Start=`Return`, Select=`BackSpace`, arrows = D-pad. Screenshots via `scrot`
(`import -window root` renders black on this GLX canvas).

**Debug code (`CHT`):**
1. Title → START → START → MAIN MENU.
2. Highlight **Restore** (6th of 6 items: Championship, Quick Race, US Open,
   Options, Restore, Credits) → A.
3. Password keyboard appears (4 rows × 8 columns). Cursor starts at `B`.
4. Move to `C` (Right ×1) → A; move to `H` (Right ×4) → A; move to `T`
   (Right ×2, Down) → A. Display reads **CHT**.
5. START → **"Debug Mode On"** appears. (B = EXIT returns to MAIN MENU.)

**Generated progress code example:** `BDBBBBBBBBBBBBBBBBBJ`
(20 symbols). On Restore, enter B (A ×1), D (Right ×1, A), then B (Left ×1,
A ×17), J (Right ×6, Down, A); START. Result: password accepted, game jumps to
TRACK select showing **Budds Creek, Maryland** (track index 16).

Another accepted novel code: `hCBBBBBBBBBBBBBBBBBt` → TRACK select,
**Washougal, Washington**.

**Key-map note:** the on-screen alphabet (ROM UTF-16LE table at file `0x1A6CA`,
ROM `0x081A6CA`) is, in index order:

```
 0:B  1:C  2:D  3:F  4:G  5:H  6:J  7:K
 8:L  9:M 10:N 11:P 12:Q 13:R 14:S 15:T
16:V 17:W 18:X 19:Y 20:Z 21:b 22:d 23:f
24:g 25:h 26:j 27:m 28:n 29:r 30:t 31:y
```

## 4. Address map

### ROM (file offset + 0x08000000)

| Address | Meaning |
|---|---|
| `0x08000000` | Header; single clean GBA image |
| `0x08002A1C` | Main-menu item dispatcher (jump table at `0x08002A68`, 6 entries) |
| `0x08002DF0` | Render 20-symbol password from byte array (alphabet `0x081A6CA`) |
| `0x08003100` | Restore/password screen handler; shows "Debug Mode On" / "Incorrect Password" |
| `0x0800318C` | Literal pointer → IWRAM debug flag `0x0300152C` |
| `0x0800CFFC` | `write_bits(value, nbits)` — writes LSB-first into a 5-bit-per-byte stream |
| `0x0800D050` | `read_bits(nbits)` — reads `byte & 0x10` then `byte <<= 1`, 5 bits/byte |
| `0x0800D0A4` | Password **generator** (packs RAM fields, appends checksum + 0xFF) |
| `0x0800D228` | Password **validator** (entry: r2 = byte array of alphabet indices) |
| `0x0800D258`/`0x0800D25C` | Literals: special-code buffer / debug flag |
| `0x0810CD90` | UTF-16LE `"Incorrect Password"` |
| `0x0810CDB8` | UTF-16LE `"< RETRY  > EXIT"` |
| `0x0810CDDC` | UTF-16LE `"Debug Mode On"` |
| `0x081A6CA` | 32-symbol UTF-16LE password alphabet |

All in-game text is **UTF-16LE**; plain `strings` finds no UI words at all.
The text bank around `0x0810CC00`–`0x0810D200` was decoded in full before
concluding no other hidden-menu strings exist.

### RAM (from savestate `gbAs` chunks; IWRAM base = state offset `0x19000`)

| Address | Meaning | Observed |
|---|---|---|
| `0x03000820` | Screen-state word | 1 = Main Menu, 2 = Class, 3 = Rider, 4 = Track, 6 = Restore, 10 = password result, 12 = Pause, 27 = in-race after restore |
| `0x0300152C` | **Debug flag** | `00` → `01` after CHT |
| `0x03002480` | Special-code byte buffer | `FF` → `01 05 0F FF` after typing CHT |
| `0x03004480` | 20-symbol password display buffer | alphabet indices, `0xFF`-terminated |
| `0x03002214` | Pointer to validator input buffer | set by validator |
| `0x03002200` | bitstream nibble counter (0..4) | read/write_bits state |
| `0x03000320` | field f0 (6 bits) | written by validator |
| `0x03002420` | field f1 (5 bits) | written by validator |
| `0x030021E0` | flags struct f2..f7 | written by validator |
| `0x03001630` | key-input state (u16) | read by screens |

## 5. Algorithm

### 5.1 Special code (debug)

At `0x0800D228` the first check reads a *fixed* buffer at `0x03002480`:

```
if buf[0]==1 && buf[1]==5 && buf[2]==15 && buf[3]==0xFF:
    *(u32*)0x0300152C = 1     # debug flag
    return -1                  # UI shows "Debug Mode On"
```

`1,5,15` are the alphabet indices of `C`, `H`, `T`. The check requires the input
to be **exactly three symbols** (byte 3 = terminator).

### 5.2 Progress password

Encoding is 5 bits per symbol, MSB-first in each byte's bits 4..0:

* `write_bits(v,n)` (`0x0800CFFC`): `byte = (byte<<1) | (v&1); v >>= 1;`
  advance byte pointer every 5 bits.
* `read_bits(n)` (`0x0800D050`): `bit = byte & 0x10; byte <<= 1;`
  result `|= 1 << k` for the k-th bit read; advance every 5 bits.
  (Thus the byte stores the *bit-reversal* of the field.)

Validator pseudocode (returns **0 = accept**, **-1 = reject**):

```
if len < 3: reject                       # bytes 0,1,2 != 0xFF
checksum = (sum(bytes[0 .. L-2]) + 4) & 31
if bytes[L-1] != checksum: reject        # checksum is the LAST symbol

f0 = read_bits(6);  if f0 > 39: reject
f1 = read_bits(5);  if f1 == 12 or f1 > 16: reject
f2 = read_bits(1); f3 = read_bits(1); f4 = read_bits(1); f5 = read_bits(1)
f6 = read_bits(2);  if f6 == 3: reject
f7 = read_bits(2);  if f7 == 3: reject
# then a table-driven tail (0x0801B5CC indexed by f0) writes per-rider/per-track
# values; no further reject branch exists in 0x0800D228.
return 0
```

Generator (`0x0800D0A4`) writes the same field order from RAM variables, appends
`(sum+4)&31` and a `0xFF` terminator. My Python reimplementation (`pwgen2.py`)
reproduces the accepted all-zero code `BBBBBBBBBBBBBBBBBBG` exactly and predicts
every accept/reject listed below.

## 6. Tables

| Code | Meaning | Result |
|---|---|---|
| `CHT` | developer debug code | "Debug Mode On"; flag `0x0300152C = 1` |
| `BBBBBBBBBBBBBBBBBBG` | generated, all fields 0 | accepted → TRACK, Glen Helen |
| `BDBBBBBBBBBBBBBBBBBJ` | generated, f1=16 (track max) | accepted → TRACK, Budds Creek |
| `hCBBBBBBBBBBBBBBBBBt` | generated, f0=39 (rider/class max) | accepted → TRACK, Washougal |
| `BBBHBBBBBBBBBBBBBBBM` | generated, f6=f7=2 | accepted → TRACK, Glen Helen |

Screen enumeration (MAIN MENU = 6 items; OPTIONS = 8 items) was verified both
visually and by the screen-state word at `0x03000820`. No hidden menu item appears
with debug mode on; the pause menu is {Retire, Quit, Music, SFX, Return}.
The debug flag is read from eight code sites (e.g. `0x0800FFA`, `0x08027FE`,
`0x0805F7C`, `0x0807E8C`, `0x080A2AC`) and is cleared to 0 by the boot/reset
routine at `0x0800FF8`, so `CHT` is session-only (not stored in a save).

## 6b. Enumeration

**Alphabet/length:** 32 symbols, 5 bits each. Raw space for a 20-symbol code is
`32^20 ≈ 1.21×10^30` strings; for the observed 19-symbol form, `32^19 ≈ 3.8×10^28`.
Leading payload fields are f0 (6 bits), f1 (5), f2–f5 (1 each), f6/f7 (2 each) =
19 bits; the remainder is a table-driven per-rider/per-track tail. The checksum
is 5 bits in the final symbol (1/32 of candidates), and the field constraints
remove further fractions (`f0≤39`, `f1∈{0..11,13..16}`, `f6≠3`, `f7≠3`).
The special code is a *separate* 3-symbol space (exactly one value: `CHT`).
The exact accepted set of full passwords was **not** exhausted: the tail layer
uses a ROM table (`0x0801B5CC`) and is not fully isolated, so "N exact accepted
codes" is not claimed. What *is* proven is the accept/reject predicate at the
validator and the existence of many generated accepted codes.

**Novel codes (not on any published list — none exist for the GBA SKU):** the four
generated codes in §6 were produced offline by `pwgen2.py`, typed on the real
Restore screen, accepted, and observed to jump to TRACK select. `BDB…J`
(f1 = 16, the maximum track field) and `hCB…t` (f0 = 39, the maximum rider/class
field) are deliberately unadvertised combinations.

**Bounds proven by rejection** (each typed on the real screen, screenshot saved):

| Input | Expected failure | Observed |
|---|---|---|
| `BBBBBBBBBBBBBBBBBBBH` (last symbol `H` instead of `G`) | bad checksum | "Incorrect Password" |
| `BLVBBBBBBBBBBBBBBBBn` (f1 = 17) | f1 > 16 | "Incorrect Password" |
| `BBBgBBBBBBBBBBBBBBBn` (f6 = 3) | reserved value | "Incorrect Password" |
| `BBBJBBBBBBBBBBBBBBBN` (f7 = 3) | reserved value | "Incorrect Password" |
| `hFBBBBBBBBBBBBBBBBBB` (f0 = 39 **and** f1 = 16) | table-driven layer | "Incorrect Password" |
| `hCtBBBBBBBBBBBBBBBBn` (f0 = 39 **and** f2..f5 = 1) | table-driven layer | "Incorrect Password" |

The last two show an additional semantic coupling between f0 and the later
fields that the leading range checks alone do not explain; this layer is
reported as an **unknown**, not as a solved rule.

## 7. Validation evidence

**Observed** (emulator + savestate RAM):
- CHT → "Debug Mode On"; `0x0300152C` 00→01; special buffer `01 05 0F FF`.
- Six MAIN MENU items and eight OPTIONS items walked; screen-state word
  `0x03000820`: 1/6/2/3/4/12 for menu/restore/class/rider/track/pause.
- Generated codes accepted → TRACK select; rejected variants → "Incorrect Password".

**Derived** (disassembly): validator at `0x0800D228`, generator at
`0x0800D0A4`, bit reader/writer at `0x0800D050`/`0x0800CFFC`, alphabet and
string bank at `0x081A6CA`/`0x0810CD90`–`0x0810CDDC`, debug-flag readers.

**Inferred:** the exact semantic meaning of f0/f1 beyond "rider/class-ish" and
"track-ish" (they clearly drive which track screen is selected, but the table at
`0x0801B5CC` was not fully decoded). The in-race effect of the debug flag is
inferred only from its eight code xrefs; no extra visible debug HUD/menu was
observed.

## 8. Unknowns

- Full table-driven tail (`0x0801B5CC`) and therefore the exact cardinality of
  the accepted password set.
- Why f0=39 rejects when combined with f1=16 or with f2..f5=1 (bounds are
  observed, mechanism isolated only to "later semantic layer").
- Whether the debug flag changes anything visible during a race (no extra menu
  appeared; flag is cleared at reset).

## 9. Tooling

`xxd`, `strings`, `grep -abo`, `file`, `md5sum`/`sha1sum`/`sha256sum`,
`arm-none-eabi-objdump -M force-thumb`, Capstone (Python) for literal-xref
scans, mGBA 0.10.5 with `-3`, Xvfb `:316` + openbox, `xdotool`, `scrot`,
ImageMagick `convert`/`compare`, `tesseract` (OCR aid), Python scripts
`phase0.py`, `utf16strings.py`, `encdecode.py`, `pwgen.py`/`pwgen2.py`,
`enter_code.py`, and a `gbAs` savestate extractor (zlib) for RAM reads.
No copyrighted assets are redistributed; only addresses, hashes and codes are
published.
