# Scooby-Doo 2: Monsters Unleashed (GBA) — Reverse Engineering Report

Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md).
Scope: **in-game / developer-intended cheats only** (passwords, hidden unlockables,
test screens). No GameShark/CodeBreaker/RAM-patch codes.

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Scooby-Doo 2: Monsters Unleashed/Scooby-Doo 2: Monsters Unleashed.gba` |
| Size | 8 MiB (`0x800000`) |
| Header title | `SCOOBY-DOO_2` |
| Game code | `BMUE` |
| Maker code | `78` (THQ); developer Altron |
| Software version | `0` |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| Fixed byte / complement / header checksum | `0x96` / `0x4A` / `0x0000` |
| MD5 | `36a7bb733c433afaf9e416e2c8c0ac9d` |
| SHA-1 | `98bf2bf16e3cb40569a9692680ca048fdab6cd29` |
| SHA-256 | `7c9706f494883bd36c8bf229e9c5fcdd3711f88f1b1f9f4f2fd1e12af472b635af` |

**Phase 0 / layout.** One Nintendo-logo hit (file `0x4`) → single 8 MiB image, no
multiboot second header. The entry word is the stock ARM branch; no cracktro or
appended trainer menu was detected. The header checksum field is `0x0000` and the
complement byte `0x4A` does not satisfy the usual `sum(0xA0..0xBD) == 0x100`
check (it evaluates to `0xE7`), i.e. the header was rebuilt without recomputing
those two bytes (guide §16.1) — but no game-code patch was found. The analysis ROM
was copied to a work dir before emulation so no `.sav`/`.ss*` artifacts were written
next to the original.

---

## 2. Executive summary

The game has a genuine **8-symbol password system** on its main-menu PASSWORD screen,
using a 32-symbol alphabet `BCDFGHJKLMNPQRSTVWXYZ123456789!?` (file `0x28BDA4`,
ROM `0x0828BDA4`) laid out as an 8×4 on-screen keypad. The 22 published codes
(20 progress passwords, a final-level code, an all-unlock code and a 3-character
movie code) are **algorithmic** — none occurs literally in the ROM in ASCII,
index-byte, glyph-byte or 5-bit-packed form.

The all-unlock code `!V?Y3T?8` was confirmed in-game: it changes the two locked
`???????` main-menu entries into **MINI GAMES** and **SPECIAL BATTLES**, and RAM
evidence shows the menu's enabled-item count going `3 → 5`. Critically, the code is
**not unique**: symbol 0 has a 4-way alias set. Three unpublished variants —
`4V?Y3T?8`, `6V?Y3T?8`, `8V?Y3T?8` — produce the identical unlock. `4V?Y3T?8`
was typed by hand on the real keypad and accepted. The remaining 28 substitutions
at that position are rejected, which bounds that alias set exactly.

The password engine's full validator arithmetic was **not** recovered: a read
watchpoint proved that the only code reading the visible 8-byte RAM buffer
(`0x030017B2`) is the glyph renderer, so the accept test operates on a different
in-memory representation. This is recorded as an explicit unknown, not brushed over.

---

## 3. How to reproduce

```bash
Xvfb :315 -screen 0 1024x768x24 &
DISPLAY=:315 openbox &
DISPLAY=:315 SDL_AUDIODRIVER=dummy mgba -3 "Scooby-Doo 2: Monsters Unleashed.gba" &
```

Keymap (mGBA SDL, verified on-screen): A=`x`, B=`z`, Start=`Return`,
D-pad = arrow keys; hold ~110 ms, gap ~140 ms. If the game ignores input, activate
the correct mGBA window first (`xdotool windowactivate --sync <wid>`) — with several
emulators open, stale windows silently steal focus.

Menu path: title → `Start` → **MAIN MENU** → **PASSWORD** → type 8 symbols →
move cursor to **OK** (auto-selected after the 8th symbol) → `A`.

Codes exercised (all entered through the on-screen keypad or injected into the
password buffer of a savestate, then submitted with OK):

| Input | Observed |
|---|---|
| `!V?Y3T?8` (published all-unlock) | accepted; MINI GAMES + SPECIAL BATTLES unlocked |
| `4V?Y3T?8` (**novel**, hand-typed) | accepted; identical unlock |
| `6V?Y3T?8`, `8V?Y3T?8` (**novel**) | accepted; identical unlock |
| `BV?Y3T?8`, `5V?Y3T?8`, `?V?Y3T?8`, … (28 other pos-0 symbols) | rejected → MAIN MENU |
| `SDBY3MT4`, `CBBCBBBB` (published progress codes) | entered without a rejection screen → MAIN MENU; no progress-state effect isolated |
| `KX?BBJVB`, `3BBBBBBG`, `?V?X3T?8` (XOR combinations of published codes) | rejected → not a linear XOR code |

---

## 4. Address map

| Address | What |
|---|---|
| `0x08000000` | entry branch `0xEA00002E` (ARM) |
| `0x0828BDA4` | 32-byte symbol alphabet `BCDFGHJKLMNPQRSTVWXYZ123456789!?` (file `0x28BDA4`) |
| `0x0829CD44` | glyph/tile lookup table (maps symbol index → font tile), used by renderer |
| `0x08057E6C` | password glyph renderer (Thumb); reads the 8 input bytes each frame |
| `0x08058D04` | password screen 20-state dispatcher; jump table at `0x08058D24` |
| `0x080592D8` | password screen main update handler (calls dispatcher + renderer) |
| `0x08059B0C` | input handler that appends a symbol to the buffer |
| `0x080592D9` (Thumb ptr at `0x0829C7EC`) | password screen handler in the screen table |
| `0x030017AC` | password screen struct |
| **`0x030017B2`** | **8-byte password input buffer** (struct+6): alphabet indices, one per symbol |
| `0x03000890` | dispatcher struct; state halfword at `+4` |
| `0x03001059` | main-menu enabled-item count: `3` locked → `5` unlocked |
| `0x03001088` | unlock flag byte: `0` locked → `1` unlocked |

The input buffer was located by savestate diffing (guide §16.13): typing
`SDBY3MT4` changes state-file offset `0x1A7B2` from eight `0x00` bytes to
`0E 02 00 13 17 09 0F 18`, exactly the alphabet indices of S,D,B,Y,3,M,T,4.
The buffer writer was then confirmed live with a write watchpoint (`0x08059B2C`).

---

## 5. Algorithm

Recovered input/UI model (precise):

```text
symbol_at(i) = "BCDFGHJKLMNPQRSTVWXYZ123456789!?"   # 32 symbols, indices 0..31
buffer[i]    = symbol_index(slot i), i = 0..7       # IWRAM 0x030017B2 + i
keypad: 8 columns x 4 rows, plus backspace (0,8), forward (1,8), OK (2,8)
Right/Left move column, Up/Down move row, A appends, B deletes
after the 8th symbol the cursor auto-parks on OK; A there submits
```

Validator model: **not recovered.** A read watchpoint on `0x030017B2` hit only
the renderer at `0x08057EA4` on every frame; skipping that renderer each frame
(the debugger's `w/r pc`) produced no other reader, yet the game still accepted
and rejected codes. Therefore the accept test reads a different representation
(copy/re-encoded array), and no offline reimplementation is claimed. Reusing the
sibling Cyber Chase title's key table `[10,5,8,5,12,14,3,2]` and 6 sliding parity
bits was tested against all 21 published codes and **fails** (scattered parity
mismatches), so that codec was not carried over unchanged.

---

## 6. Tables

### 6.1 Published codes verified against this ROM

Sources: 3rd party cheat indexes ("Unlock ALL…", "Level passwords", "Alternative ending
password") and the 3rd party cheat index walkthrough (Passwords section). The two
lists use different level labels for the same strings (a one-level offset —
guide §16.15); the strings themselves agree.

| Code | Published effect | This ROM |
|---|---|---|
| `!V?Y3T?8` | unlock all special battles / stages / badges | confirmed: MINI GAMES + SPECIAL BATTLES unlocked |
| `5DBY3MT8` | final level (Scooby vs Masked Guy) | literal absent from ROM; not entered in this run (post-game gate not reached) |
| `SD2` | alternative ending after beating the game | 3-character movie code; post-game gate not reached |
| `CBBCBBBB` … `SDBY3MT4` | 20 progress passwords, levels 1.2 … 5.4 | no rejection screen observed; no code typo found; progress effect not isolated |

3rd party cheat index lists exactly 20 progress passwords ending at `SDBY3MT4`; 3rd party cheat indexes
adds `5DBY3MT8` and `!V?Y3T?8`. The "Passwords for all levels" sub-list on
3rd party cheat indexes (`BDBCBBBB`, `LBGCLBBG`, `MBG1BVBJ`, `LDG1CVBG`, `MDGWPVBG`,
`LBB9TBBJ`, `MBB9TBBG`) is inconsistent with the main list and was treated as an
unverified submission, not as ROM evidence.

### 6.2 Password alphabet / keypad

```
B C D F G H J K      (row 0)      backspace  (0,8)
L M N P Q R S T      (row 1)      forward    (1,8)
V W X Y Z 1 2 3      (row 2)      OK         (2,8)
4 5 6 7 8 9 ! ?      (row 3)
```

### 6.3 Unlock proof (RAM)

| State | `0x03001059` (menu count) | `0x03001088` | Menu labels |
|---|---:|---:|---|
| locked (rejected code) | `0x03` | `0x00` | `???????`, `???????` |
| unlocked (`!V?Y3T?8` or any novel alias) | `0x05` | `0x01` | MINI GAMES, SPECIAL BATTLES |

---

## 6b. Enumeration

### Space

* Alphabet 32 symbols × exactly 8 positions → **32^8 = 2^40 =
  1,099,511,627,776** possible strings.
* The published set is 22 strings (20 progress + final + all-unlock + the
  post-game 3-symbol movie code). None is stored literally; validity is computed.
* The all-unlock code's first symbol has a bounded alias set (below); the codec
  therefore discards at least two bits of that symbol.

### Novel codes (absent from every published list)

| Code | Symbol-0 index | Effect | Evidence |
|---|---:|---|---|
| **`4V?Y3T?8`** | 24 | MINI GAMES + SPECIAL BATTLES unlocked | typed by hand on the keypad, OK submitted, screenshot + RAM |
| `6V?Y3T?8` | 26 | identical | savestate-injected, accepted |
| `8V?Y3T?8` | 28 | identical | savestate-injected, accepted |

`4V?Y3T?8` was verified end to end: the input slots rendered `4 V ? Y 3 T ? 8`,
the buffer held `18 10 1F 13 17 0F 1F 1C`, and after OK the main menu showed
MINI GAMES / SPECIAL BATTLES with `0x03001059 = 5`, `0x03001088 = 1`.

### Alias set and bounds proven by rejection

All 32 symbols were substituted at position 0 while positions 1–7 stayed at
`V?Y3T?8` (32 in-game trials). Exactly four were accepted:

```
accepted pos-0 symbols: 4 (24)  6 (26)  8 (28)  ! (30)
                         = { idx : idx >> 3 == 3 and (idx & 1) == 0 }
rejected: the other 28 symbols, e.g. B (1), 5 (25), ? (31)
```

So bits 4 and 3 of symbol 0 must be `11`, bit 0 must be `0`, and bits 2 and 1 are
ignored — a 4-way alias. Position 7 was brute-forced the same way over all 32
symbols: **only the published `8` is accepted** (31 rejections), so that symbol is
fully constrained. These are bounded positive+negative enumerations of those two
fields, not samples. XOR combinations of published codes (`KX?BBJVB`,
`3BBBBBBG`, `?V?X3T?8`) were also rejected, proving the accept test is not a
simple GF(2)-linear function of the raw 40-bit value.

---

## 7. Validation evidence

**Observed (emulator / screenshots / RAM)**
* Title, MAIN MENU, PASSWORD keypad, AREA 1 map, OPTIONS (MUSIC TEST `1`,
  SFX TEST, MUSIC/SEFX ON, TEXT ON, CREDITS), MINI GAMES and SPECIAL BATTLES
  (boss fight) all reached on `:315`.
* `!V?Y3T?8` and the three novel aliases unlock MINI GAMES / SPECIAL BATTLES.
* 28 rejected pos-0 substitutions return to MAIN MENU with the entries still `???????`.
* Buffer `0x030017B2` contents confirmed by savestate diff and live debugger read.

**Derived (disassembly / debugger)**
* Alphabet address and contents; buffer address and writer (`0x08059B2C`);
  renderer (`0x08057E6C`) is its only reader; screen dispatcher (`0x08058D04`)
  and 20-state jump table (`0x08058D24`); menu handlers at `0x080592D8`,
  `0x08058B8D`, `0x08057C39`.

**Inferred**
* The three novel codes are behaviourally identical to the published all-unlock
  code (same menu labels and same RAM flags); no difference in unlocked content
  was observed.
* Progress passwords likely unlock areas/stages (per manual and walkthrough);
  the level-select side effect was not isolated in RAM and is not claimed as proved.

---

## 8. Unknowns

* **Validator arithmetic:** the accept test does not read `0x030017B2` directly;
  its input representation and checksum were not identified, so no offline
  encoder/decoder is provided. Keys/parity from the sibling Cyber Chase title do
  not apply unchanged.
* Whether positions 1–6 of the all-unlock code also have alias sets. Positions 0
  and 7 were brute-forced over all 32 symbols (§6b); positions 1–6 were only
  spot-checked against the published symbols.
* The 3-symbol movie code `SD2` is post-game gated; its accept path was not
  exercised (no cleared save was available).
* Per-level effect of each of the 20 progress passwords on the AREA/STAGE SELECT
  screens; entry acceptance was observed, selection state was not.

---

## 9. Tooling

| Tool / script | Purpose |
|---|---|
| `strings -t x`, `grep -abo`, Python byte search | strings, literal tables, encoded-code search |
| `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum` | Phase 0 fingerprint |
| `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7 | Thumb disassembly, xref/BL scans |
| mGBA 0.10.5 `-d` driven through a Python PTY | read/write watchpoints, `w/r pc`, memory reads |
| Python PNG/`gbAs` zlib parser | savestate RAM diffing and password-buffer patching |
| `oracle.py`, `batch.py`, `type_code.py` (work dir) | fast code trials and hand-entry automation |
| `xdotool`, `scrot`, Xvfb `:315`, openbox | input and screenshots |

No ROM, graphics, music or game text is redistributed here — only addresses,
hashes, algorithms and the short code strings needed to document the cheats.
