# Army Men: Operation Green (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Army Men: Operation Green/Army Men: Operation Green.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title (0xA0) | `ARMY MEN OG` |
| Game code (0xAC) | `AMEE` |
| Maker code (0xB0) | `5H` |
| Main unit / device | 0x00 / 0x00 |
| Software version (0xBC) | 0x00 |
| Complement check (0xBD) | 0xCD (computed 0xCD — valid) |
| Header checksum (0xBE) | 0x0000 |
| Entry word (0x00) | `0xEA00002E` (ARM branch to 0x080000C0) |
| MD5 | `60eb386e45d38b41fa10cd2535f681d8` |
| SHA-1 | `b0fa4769cddbc66bc333ad45658524a4aeeec755` |
| SHA-256 | `c0e1f5f998728d02f81012e06e9e2342e7908ae4b5d42384ae11fd01d70889fa` |

Embedded GBA-header scan (Phase 0): the complete 156-byte Nintendo logo
(`24 ff ae 51 … d4 f8 07`) occurs **exactly once**, at file offset `0x4`
(header base `0x0`, ROM address `0x08000000`). Conclusion: this is a single
4 MiB image, not a multi-game pack; no second header or shell exists.

The ROM is the five-language European/US build (boot asks
ENGLISH / FRANÇAIS / DEUTSCH / ITALIANO / ESPAÑOL). The password system is
language-independent: one alphabet, one codec, shared by every language.

## 2. Executive summary

* The game's save system **is** the password system (a continuation/level
  select password, confirmed by the publisher's own description). The password
  screen is the second item of the title menu: **NEW GAME / PASSWORD /
  OPTIONS**.
* The password is **8 symbols from a 32-symbol alphabet**:

  ```
  BCDFGHJKLMNPQRSTVWXYZ*0123456789
  ```

  Encoding is **5 bits per symbol**, so 40 bits on the wire: 7 data symbols
  (35 bits) + 1 checksum/key symbol (5 bits). The recorded data are:
  level, two 0–100 numeric fields, lives, a second numeric nibble, a
  grenade count, and a 2-bit loadout selector.

* The validator (`0x080061B8`) and the encoder (exercised by the in-game
  pause menu, which re-derives and prints the password) were both reversed.
  My Python codec **round-trips all 22 published level passwords exactly**
  (`encode(decode(c)) == c`), and the game's own pause-menu display reproduced
  both a published alternate (`K*67LZZM`) and a minted code (`6J2PNX7S`)
  character-for-character.

* The published list (levels 2–12, two codes each) is only 22 points in a
  **3,898,605,568-code** accepted space. The published codes are ordinary
  points in that space; the "alternate" column is a second fixed loadout
  template repeated per level, not an independent secret.

* Two published strings are OCR errors: `FFOOWP36` is really **`FF00WP36`**
  (zero, not letter O) and `3SXRLWOJ` is really **`3SXRLW0J`**. Both corrected
  forms were accepted and start the advertised levels in mGBA. The
  SuperCheats "level 13" code **`GLDJLKHD`** fails the checksum and is
  **rejected** by the game.

* A second, hidden layer exists: a hard-coded 7-entry table checked before the
  algorithmic decoder. Its entries are leetspeak developer codes:
  **`CR3D1TZZ` → credits**, **`H4X0RD1Z` → a "1337" screen**,
  **`T4K34W4Y` → a developer photograph**, plus four codes that only set RAM
  flags (`D3BVGPLZ`, `H34LTHY*`, `W34P0NZZ`, `M3H34LTH`). None of these
  appears in any published cheat list I could find.

* Novel, previously unpublished codes were minted and entered in mGBA, e.g.
  **`6J2PNX7S`** (level 12, 15 lives, 30 grenades, both loadout bits) — shown
  starting *Operation TAN HO / "Spider's Web"* with a 15/30 HUD — and
  **`6DPG8HZV`** (lives 15), **`G6G8HZHD`** (grenades 30), **`DVD6G8H1`**
  (level-2 defaults).

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL), 3× scale, headless Xvfb, `SDL_AUDIODRIVER=dummy`.

Default mGBA SDL keymap: **A = `x`**, **B = `z`**, **L = `a`**,
**R = `s`**, **Start = `Return`**, **Select = `BackSpace`**, D-pad = arrows.
Save state slot *n* with **Shift+F*n***, load with **F*n***.

Exact path used:

1. Boot → language menu → **ENGLISH** (`x`) → intro logos → title menu.
2. Title menu: **NEW GAME / PASSWORD / OPTIONS**. Press **Down** once, then
   **A** on PASSWORD. (The middle item is the password entry; it is not
   disabled — unselected items are simply drawn grey.)
3. The entry screen (`0x08005A08`, screen id `0x16`) is an 11-column × 3-row
   grid. Grid index = `row*11 + col`:
   * row 0: `BCDFGHJKLMN`
   * row 1: `PQRSTVWXYZ*`
   * row 2: `0123456789`
   * **A** appends the highlighted symbol, **B** deletes the last symbol (B on
     an empty entry exits the screen), **Start** exits. In this build **Select
     does nothing visible**: its handler (`0x08006028`) clears the dev-screen
     buffers `0x03000A5C`/`0x03000E84`, not the retail cursor `0x03001BA4`
     (verified: after two symbols, Select left the cursor at 2).
4. After the 8th symbol the decoder runs. Valid → ~2 s fade → mission
   briefing/HUD. Invalid → the grid clears with a buzz and the cursor resets
   (status word `0x03000F20 = 2`).
5. In-game, **Start** opens the pause menu: RESUME GAME / MISSION OBJECTIVES /
   MISSION MAP / OPTIONS / ABORT MISSION, plus a non-selectable
   `PASSWORD <8 chars>` line that re-encodes and displays the current config
   (this is the ROM's own encoder).

### 3.1 String reconnaissance (counts and classification)

`strings -t x -n 4` yields 36,570 runs for the whole ROM, but the retail UI is
drawn from an encoded text bank, so keyword hits are few and need context:

| Keyword (case-insensitive) | Hits | Classification |
|---|---:|---|
| `password` | 2 | `0x135DB1` `Password select`, `0x135DD1` `Password: --------` — ASCII developer/password bank (real) |
| `cheat` | 0 | — |
| `debug` | 0 | — |
| `secret` | 0 | — |
| `unlock` | 0 | — |
| `mission` | 0 | — |
| `code` | 1 | `0x26B990` `Code-#` — sits inside compressed/encoded graphics data, no pointer/reference: coincidence, not a cheat string |
| `level` | 3 | `0x135D30` dev label `Level   xxx xxxx`; `0x267038`/`0x267450` credits text ("Scripting and Level Design", "Level Mapping") |
| `select` | 1 | `0x135DBA` `Password select` |
| `menu` | 2 | `0x135D96` dev label `Main menu`; `0x269322` encoded main-menu text fragment |

Literal searches that anchored the analysis: the 32-symbol alphabet
`BCDFGHJKLMNPQRSTVWXYZ` occurs **once** (`0x135B45`); the position-order
string `BJ5PR93WSM…` once (`0x135BBA`); the unreferenced leftover
`HY66GKKY2RQNMDTWSM…` once (`0x135B24`); `ENTER P` once (`0x269334`, the
title's encoded "ENTER PASSWORD"). Published codes contain letters that the
alphabet cannot express (`O`), which is exactly how the two OCR errors were
found before any emulator run.

Web recon: the complete 22-code list was recovered from GameRevolution,
Ethereal Games, AbsoluteCheats, GameGenie, Vizzed and SuperCheats (the latter
also supplied the bogus "13 – GLDJLKHD"). Every published string was then
checked against the ROM model; two needed the `O → 0` correction.

Button/key-mask scan (bounded negative): a search for 2-byte-aligned runs of
≥5 u16 button masks (one bit per press, values 0x001…0x200) produced only three
candidates — `0x08300D94`, `0x0823AFB0`, `0x0825EA02`. None has a 32-bit
pointer to it and none is read by the title/pause/password handlers, so this
build has **no button-cheat table**. (Byte-sized "one mask per press" runs are
dominated by ordinary instruction bytes — 927 runs ≥5 — and carry no signal.)

Input timing note (reproducibility): under heavy load a 10–150 ms key tap is
often missed by the game's once-per-frame edge detector, and a 200 ms A hold
occasionally registers twice. A 0.5–0.6 s A hold with ≥0.55 s release gap was
reliable. The entry helper used here is closed-loop: it saves state with
Shift+F1 after every symbol and reads the cursor/buffer out of the savestate,
so a missed or doubled press is corrected instead of silently corrupting the
code.

Savestate format (useful because it gives deterministic RAM reads without a
GDB stub): `.ss*` is a PNG whose `gbAs` chunk is a zlib stream of 0x61000
bytes. Blocks: `+0x400` VRAM (0x18000), `+0x18400` palette, `+0x18800` OAM,
`+0x18C00` I/O, **`+0x19000` IWRAM (0x8000)**, **`+0x21000` EWRAM (0x40000)**.
All RAM addresses in this report are IWRAM offsets from `+0x19000`.

## 4. Address map

All addresses are ROM addresses (`file offset + 0x08000000`) in this exact
revision.

### Password engine

| Address | Role |
|---|---|
| `0x08005A08` | Password-screen frame handler (Thumb); substate dispatch on `0x03000E7C` |
| `0x08005A54` | substate 0: fade-in / setup |
| `0x08005A78` | substate 1: redraw + input (A/B/Select/Start/D-pad) |
| `0x08005C3C` | substate 2: post-entry fade timer (`0x03000A58`, 120 frames) |
| `0x08005CF0` | substate 3: result dispatch; status 2 → back to entry, status 1 → success |
| `0x08005958` | helper: display characters → alphabet indices, row/col split (/11) |
| `0x08005D74` / `0x08005DF4` | redraw helpers (grid / entry line) |
| `0x08006028` | Select handler: clears dev-screen buffers `0x03000A5C`/`0x03000E84`; no effect on the retail cursor in this build |
| **`0x080061B8`** | **password decoder / validator** (called only from `0x08005B14`) |
| `0x0800627C`–`0x0800631A` | normalisation + 5-bit checksum + range checks |
| `0x0800631C` | hidden-table match path (`bx` through `0x0824B9A4[idx]`) |
| `0x08006414` | success post-processing: copy decoded values to globals, clamp |
| `0x0800642C`–`0x080064F2` | clamping / field stores |
| `0x0800652C` | mission-start routine fed by the same globals (also used by dev menu) |
| `0x08006A54` | pause-menu builder; reads config `0x03004C00` and prints the password line |
| `0x080069C0`–`0x080069F0` | inverse copy: config struct → decoded globals (encoder side) |
| `0x08006B60` | developer menu builder (`Raster/Bullets/Health/…/Password select`), referenced from state tables at `0x0824B608`, `0x0824B960`, `0x0824BA24`, `0x0824BFB8`, `0x0824C080` — no runtime transition reaches it in this build |
| `0x08002708` | global input read: `~KEYINPUT & 0xFFFF` → raw/pressed/previous |

### Data

| ROM address | Length | Contents |
|---|---|---|
| `0x08135B24` | 33 | 32-character sequence `HY66GKKY2RQNMDTWSM*K7L1BB3CCDFGH` + NUL; no 32-bit literal points at it and the validator never reads it (unused) |
| **`0x08135B45`** | 33 | alphabet `BCDFGHJKLMNPQRSTVWXYZ*0123456789\0` (32 symbols) |
| **`0x08135B68`** | 81 | hidden-code table, 7 entries × 8 bytes used (56 bytes); rest is 3 unused entries + 1 byte (`BQN52B0R`, `FFG*HGL*`, `VHJJ6JGL`, `M`) |
| **`0x08135BBA`** | 67 | canonical position order (`SCRAM`): first 32 bytes are a permutation of the alphabet, the tail repeats symbols |
| `0x08135BFE` | 24 | pause-menu value layout (12 × u16 coordinate pairs) |
| `0x08135C30`–`0x08135DDF` | — | pause/dev menu ASCII labels (`Raster`, `Bullets`, `Health`, `Grenades`, `Weapons`, `Flame`, `Rockets`, `Fuelcans`, `CollDis`, `Lives`, `Minesweep`, `Level xxx xxxx`, `map miss`, `Start game`, `Main menu`, `Password select`, `Password: --------`) |
| `0x0824B9A4` | 28 | 7 Thumb handlers for the hidden codes |

Literal-pool xrefs for the key data (verified with `struct.unpack_from`):

* alphabet `0x08135B45` ← `0x080059EC`, `0x08005C38`, `0x0800605C`, `0x08006264`
* table `0x08135B68` ← `0x0800625C`
* SCRAM `0x08135BBA` ← `0x08006254`, `0x08006608`

### RAM (IWRAM)

| Address | Meaning |
|---|---|
| `0x030009D0` | 8 × u8: alphabet index of each entered symbol |
| `0x03004D20` | 8 × u8: display characters |
| `0x03001BA4` | entry cursor 0…8 |
| `0x03004CE8` | grid row 0…2 |
| `0x030009C4` | grid column 0…10 |
| `0x03000A58` | input repeat / fade timer |
| `0x03000A60` | raw `~KEYINPUT & 0x3FF` |
| `0x03000E8C` | keys pressed this frame (edge) |
| `0x03000E94` | previous raw keys |
| `0x03000E7C` | password-screen substate (0…3) |
| `0x03000ED4` | global screen id (0x16 password entry, 0x0E level start, 0x0F credits, 0x09 dev screens, 0x19 debug menu) |
| `0x03000F20` | decode status: 1 = valid, 2 = rejected |
| `0x03001B00` | decode scratch: b0…b6 then `off` in byte 7 |
| `0x030012B0` | decoded level |
| `0x03004C84` | b1 << 10 (later `>>8` = b1·4, 0…96) |
| `0x03001290` | b2 & 0x0F |
| `0x03001AE0` | b3 << 2 (0…100) |
| `0x030003E8` | b4 & 0x0F |
| `0x03000E70` | 2-bit loadout selector: bit0 = b2 bit4, bit1 = b4 bit4 |
| `0x030053E0` | (b5 & 0x0F) << 8 |
| `0x03001BC4` | b6 (grenades) |
| `0x03004C00` | mission config struct, filled by `0x08006B60` and consumed at level start: `+0x04` flag word, `+0x08` b1·4, `+0x0C` lives, `+0x10` b3·4, `+0x14` b4 low nibble, `+0x18` selector, `+0x1C` grenades, `+0x20` b5, `+0x28` extra, `+0x2C` level |
| `0x03004C74` | debug-enable flag set by hidden code `D3BVGPLZ`; checked at `0x08002794` but gated on `ROM[0x080000AC] == 0`, which is false (`AMEE`) |
| `0x03004C48` | flag set by `H34LTHY*` and `M3H34LTH`; copied to config `+0x04` |
| `0x030017A8` | flag set by `W34P0NZZ` |

## 5. Algorithm

### 5.1 Decoder (`0x080061B8`)

Input: eight alphabet indices `v[0..7]` (each 0…31) in `0x030009D0`,
built by the entry screen from the typed symbols.

```
# 1. hidden developer table, checked first (7 entries, 8 chars each)
for e in 0..6:
    if all( SCRAM[ v[i] ] == TABLE[e*8 + i] for i in 0..7 ):
        jump HANDLER[e]           # 0x0824B9A4 + 4*e, tail call via 0x0801BC8C
        return

# 2. algorithmic password
pos[i] = index of the typed symbol in SCRAM       # 0..31
off    = pos[7]

b[i] = (pos[i] - off - i) & 31        for i = 0..6

chk = sum( ((b[i] ^ 0xA3) ^ (2*i)) for i = 0..6 ) & 31
if chk != off:  status = 2 (reject)   # 0x03000F20
else:           status = 1

# 3. range checks (status stays 1 only if all pass)
if (b[1] << 10) > 0x6400:  status = 2     # b1 <= 25
if ((b[3] << 2) & 0xFF) > 100: status = 2  # b3 <= 25
if b[0] <= 1: status = 2
if b[0] > 12: status = 2
```

Note the key/checksum symbol is **also the subtractive key** used to normalise
every other symbol; that is why the checksum is not a separate trailing field
but a fixed point of the transform.

### 5.2 Success post-processing (`0x08006414`)

```
0x030012B0 = b[0]                      # level
0x03004C84 = b[1] << 10, clamp <= 0x6300  # b1 <= 24
0x03001290 = b[2] & 0x0F, clamp <= 15
0x03001AE0 = b[3] << 2, clamp <= 99        # b3 <= 24
0x030003E8 = b[4] & 0x0F, clamp <= 15
0x030053E0 = (b[5] & 0x0F) << 8, clamp <= 0x0F00
0x03001BC4 = b[6], clamp <= 30
0x03000E70 = ((b[2] >> 4) & 1) | (((b[4] >> 4) & 1) << 1)
0x03000E88 = 1
```

Then the screen code waits 16 frames and, if status == 1, sets screen id 14
(level start) and clears the substate; if status == 2 it clears the grid and
returns to entry.

### 5.3 Encoder (`encode(decode(c)) == c`)

```
def encode(b):          # b = 7 values, b0 = level
    off = sum(((b[i] ^ 0xA3) ^ (2*i)) for i in range(7)) & 31
    pos = [(b[i] + off + i) & 31 for i in range(7)] + [off]
    return "".join(SCRAM[p] for p in pos)
```

`SCRAM[0..31]` is a permutation of the alphabet, so every data vector has
exactly one 8-symbol spelling. The ROM re-derives the pause-menu password line
from the decoded config; for both `K*67LZZM` and the minted `6J2PNX7S` the
displayed string matched this function exactly, and
`encode(decode(c)) == c` holds for all 22 published codes.

## 6. Tables

### 6.1 Alphabet and canonical order

```
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ*0123456789"          @ 0x08135B45 (32 symbols)
SCRAM = "BJ5PR93WSM*K7LTY01VD6G8HZ2QNXCF4NPQRSDT*8X9356TH*YW2RHBZ2CY01VJ5PF4"
                                                     @ 0x08135BBA (67 bytes,
                                                     first 32 = permutation)
```

### 6.2 Field layout

| Field | Bits | Accepted range | Config destination | Observed meaning |
|---|---|---|---|---|
| b0 level | 5 | 2…12 | `0x030012B0`, config `+0x2C` | level / mission |
| b1 | 5 | 0…25 (clamped 24) | `0x03004C84` → config `+0x08` = b1·4 (0…96) | 0–100 numeric field; no HUD change observed |
| b2 low nibble | 4 | 0…15 | `0x03001290` → config `+0x0C` | **lives** (9→09, 15→15; 0 displays 03) |
| b2 bit4 | 1 | 0/1 | `0x03000E70` bit0 → config `+0x18` | loadout selector bit 0 |
| b3 | 5 | 0…25 (clamped 24) | `0x03001AE0` → config `+0x10` = b3·4 (0…96) | 0–100 numeric field; no HUD change observed |
| b4 low nibble | 4 | 0…15 | `0x030003E8` → config `+0x14` | numeric field; no HUD change observed |
| b4 bit4 | 1 | 0/1 | `0x03000E70` bit1 → config `+0x18` | loadout selector bit 1 |
| b5 | 4 | 0…15 | `0x030053E0` → config `+0x20` | numeric field; no HUD change observed |
| b6 | 5 | 0…31 (clamped 30) | `0x03001BC4` → config `+0x1C` | **grenades** (4→04, 9→09, 30→30; 0 displays 03) |
| b7 / off | 5 | 0…31 | normalization key + checksum | not stored |

The 2-bit selector changes the third HUD counter (the green canister icon):

| b2 bit4 | b4 bit4 | third counter |
|---|---|---|
| 0 | 0 | 10 |
| 1 | 0 | 01 |
| 0 | 1 | 02 |
| 1 | 1 | 03 |

(Observed with `DVD6G8H1`, `P5DR93WJ`, `P5PRG3WJ`, `VQKDR440`; the meaning of
the counter — weapon / fuel / item slot — is not proven.)

### 6.3 Published codes verified against the ROM

All 22 published codes were decoded with the ROM-derived model; all pass the
checksum and all decode to their advertised level. Thirteen were additionally
entered in mGBA and produced the advertised mission briefing (marked ✓).
`b` column = `b0..b6`.

| Level | Published code | Decoded b | Notes |
|---|---|---|---|
| 2 | `5VKPR6*B` | `[2,17,9,0,0,15,4]` | ✓ briefing "Workin' 9 Til 5" |
| 2 | `K*67LZZM` | `[2,0,9,0,0,10,9]` | ✓ alt; pause line echoes it |
| 3 | `5PK5LL*4` | `[3,3,10,0,10,9,5]` | ✓ briefing |
| 3 | `F58FWJ*N` | `[3,6,25,0,8,1,9]` | decoder-verified |
| 4 | `Y8DTF4HK` | `[4,10,6,0,15,15,6]` | ✓ briefing |
| 4 | `3MC9TS15` | `[4,6,25,0,8,1,9]` | decoder-verified (generic alt loadout) |
| 5 | `62BVXHXY` | `[5,9,15,0,9,3,7]` | ✓ briefing |
| 5 | `3SXRLW0J` | `[5,6,25,0,8,1,9]` | ✓ **corrected**: lists print `3SXRLWOJ` (letter O); the alphabet has no `O`. `3SXRLW0J` accepted |
| 6 | `MQ5310VP` | `[6,22,29,0,10,8,9]` | ✓ briefing |
| 6 | `Y0V7G6ZM` | `[6,6,7,0,8,6,9]` | decoder-verified |
| 7 | `SZQR6W1J` | `[7,22,23,0,15,1,10]` | ✓ briefing |
| 7 | `DLTYD4G7` | `[7,0,0,0,3,14,3]` | decoder-verified |
| 8 | `44BQQCWH` | `[8,7,7,0,31,1,10]` | ✓ briefing |
| 8 | `NJ98C3XD` | `[8,13,16,0,6,14,3]` | decoder-verified |
| 9 | `F4J1ZRWG` | `[9,9,10,25,31,10,12]` | ✓ briefing |
| 9 | `CG4PPSC6` | `[9,0,9,12,11,15,3]` | decoder-verified |
| 10 | `FF00WP36` | `[10,9,26,25,15,10,12]` | ✓ **corrected**: lists print `FFOOWP36` (letter O); accepted as `FF00WP36` |
| 10 | `5QFXBJJZ` | `[10,1,4,1,4,4,3]` | decoder-verified |
| 11 | `*HBNVVV4` | `[11,23,31,25,15,14,13]` | ✓ briefing |
| 11 | `52CN4BBH` | `[11,1,4,1,4,4,3]` | decoder-verified |
| 12 | `85M3QCF*` | `[12,23,29,25,12,14,14]` | ✓ briefing |
| 12 | `*BR53WWF` | `[12,1,4,1,4,4,3]` | decoder-verified |

Observation: the "alternate" codes are not independent random codes. Levels
3, 4 and 5 alternates share the identical tail `[·,6,25,0,8,1,9]`; levels
10, 11 and 12 alternates share `[·,1,4,1,4,4,3]`. They are generic loadout
templates stamped onto each level; the remaining alternates use level-specific
values.

Rejected public claim: SuperCheats lists "13 – GLDJLKHD". It fails the
checksum (`chk = 8`, `off = 19`); entered in mGBA it resets the grid (see
§6b bounds).

### 6.4 Hidden developer codes (checked before the algorithm)

The table is read as `SCRAM[alphabet_index(typed)] == TABLE[e*8+i]`, so the
**typed** string is the table string transformed through the two alphabets:

| # | Table entry @0x08135B68 | Typed code | Handler | Observed effect |
|---|---|---|---|---|
| 0 | `52B0RKS6` | `D3BVGPLZ` | `0x08006065` | sets `0x03004C74 = 1`, returns to entry; no visible effect (debug gate needs `ROM[0x080000AC]==0`) |
| 1 | `92QSY9DG` | `H34LTHY*` | `0x08006099` | sets `0x03004C48 = 1`, returns to entry |
| 2 | `JL25HY66` | `CR3D1TZZ` | `0x080060B9` | sets level = 24, screen 15 → **credits** (`Army men / Operation Green / © 2001 3DO / Gameboy Advance version by…`) |
| 3 | `12QK8*66` | `W34P0NZZ` | `0x080060D1` | sets `0x030017A8 = 1`, returns to entry |
| 4 | `M292QSY9` | `M3H34LTH` | `0x080060F1` | sets `0x03004C48 = 1`, returns to entry |
| 5 | `9QV8L5H6` | `H4X0RD1Z` | `0x08006111` | screen 9, sound 21 → white screen with **`1337`** |
| 6 | `YQW2Q1QD` | `T4K34W4Y` | `0x08006165` | screen 9, sound 23 → **developer photograph** (goggles/inflatable suit, office) |

The 81-byte blob has three further 8-character groups (`BQN52B0R`,
`FFG*HGL*`, `VHJJ6JGL`) that the validator never compares (loop bound is
entry 6). Their typed forms (`B45D3BVG`, `88*N1*RN`, `X1CCZC*R`) also fail the
checksum, so they are unreachable dead data.

These seven strings do not appear in any published password list found on
GameFAQs mirrors, GameRevolution, Ethereal Games, AbsoluteCheats, GameGenie,
Vizzed, SuperCheats, or the other cheat mirrors searched; they are effectively
unpublished.

## 6b. Enumeration

### Space definition

* Alphabet: 32 symbols (`ALPHA`), no aliases; the entry grid offers exactly
  those 32 symbols (11 + 11 + 10).
* Length: exactly 8 symbols. The 8th symbol is the subtractive key **and**
  the 5-bit checksum.
* Total input strings: `32^8 = 1,099,511,627,776` (2^40).
* Checksum-valid strings: exactly **`32^7 = 34,359,738,368`** (2^35).
  Equivalently, every 7-value data vector `b0..b6` has exactly one valid
  8-symbol spelling (the 8th symbol is `off = chk(b)`). In prefix terms the
  fixed points come in fours: over 200,000 random 7-symbol prefixes, 49,951
  admitted 4 valid checksum symbols and 150,049 admitted none (never 1, 2 or
  3), so the average is exactly one spelling per data vector.
* Range-accepted by the validator (`0x080061B8`):

  ```
  11 (level 2..12) × 26 (b1 0..25) × 32 (b2) × 26 (b3 0..25)
  × 32 (b4) × 16 (b5) × 32 (b6)
  = 3,898,605,568
  ```

  The post-processor clamps b6 31→30, so the number of *distinct in-game
  configurations* is `11 × 26 × 32 × 26 × 32 × 16 × 31 = 3,776,774,144`.
  The 22 published codes are 22 points in this space.

### Novel codes (absent from every published list) and in-game proof

All were generated with the encoder above and entered on the title PASSWORD
screen. "Accepted" means the mission briefing appeared; the HUD was then
photographed.

| Code | b0..b6 | Effect observed in mGBA |
|---|---|---|
| **`6J2PNX7S`** | `[12,24,15,24,15,15,30]` | level 12 briefing *OPERATION TAN HO / "Spider's Web"*; HUD **lives 15, grenades 30**; pause line re-displays `6J2PNX7S` (screenshots `novel12_brief.png`, `novel12_hud.png`, `pw_game_pause.png`) |
| `6DPG8HZV` | `[2,0,15,0,0,0,0]` | level 2; HUD lives **15** (`b15_hud.png`) |
| `G6G8HZHD` | `[2,0,0,0,0,0,30]` | level 2; HUD grenades **30** (`f30_hud.png`) |
| `DVD6G8H1` | `[2,0,0,0,0,0,0]` | level 2 baseline (lives 03, grenades 03) (`base2_hud.png`) |
| `VQKDR440` | `[2,9,25,0,16,10,9]` | level 2; both selector bits; HUD lives 09, grenades 09, third counter **03** (`flags2_hud.png`) |
| `P5DR93WJ` | `[2,0,16,0,0,0,0]` | selector bit 0 only; third counter **01** (`flag_b2_hud.png`) |
| `P5PRG3WJ` | `[2,0,0,0,16,0,0]` | selector bit 1 only; third counter **02** (`flag_b4_hud.png`) |
| `K5K7LTYM` | `[2,24,0,0,0,0,0]` | b1 = 24 (96 %); accepted, no visible HUD change (`a24_hud.png`) |
| `K*KRLTYM` | `[2,0,0,24,0,0,0]` | b3 = 24 (96 %); accepted, level-2 briefing (`c24.png`) |

`6J2PNX7S` is the strongest single artefact: it is a level-12 password whose
loadout no published list contains (the two public level-12 codes decode to
`b2 = 29` / `b2 = 4`, never 15, and to `b6 = 14` / `b6 = 3`, never 30), and
the game both accepted it and re-encoded it to the same string.

### Bounds proven by rejection

Each rejected code was entered on the title PASSWORD screen; in every case the
grid cleared and the cursor reset (status word 2, no briefing).

| Input | Why it must fail | In-game result |
|---|---|---|
| `GLDJLKHD` (public "level 13") | checksum: `chk=8`, `off=19` | rejected — grid reset (`rej_gld_2.png`) |
| `DD6G8HZV` | valid checksum, level `b0=1` (validator requires 2…12) | rejected (`rej_DD6G8HZV_2.png`) |
| `K4BJ5PRF` | valid checksum, level `b0=13` | rejected (`rej_K4BJ5PRF_2.png`) |
| `DVD6G8HZ` | one symbol changed at position 8 → checksum fails | rejected (`rej_DVD6G8HZ_2.png`) |

Additionally, the 8-symbol input path is bounded by construction: there is no
9th symbol to enter (the 8th A press immediately arms the decoder), and the
only per-symbol keys are A (append) and B (delete).

## 7. Validation evidence

### Observed (emulator screenshots / savestate RAM reads)

* Title menu items and the password grid layout, cursor movement, append and
  backspace behaviour (Select was tested and has no visible effect in this
  build).
* `5VKPR6*B` → *OPERATION BOWLER HAT / "Workin' 9 Til 5"* (level 2) and HUD
  09/04/10/00.
* Level codes for **all** levels 2–12: `5VKPR6*B` (2), `K*67LZZM` (2 alt),
  `5PK5LL*4` (3), `Y8DTF4HK` (4), `62BVXHXY` (5), `3SXRLW0J` (5 alt),
  `MQ5310VP` (6), `SZQR6W1J` (7), `44BQQCWH` (8), `F4J1ZRWG` (9),
  `FF00WP36` (10), `*HBNVVV4` (11), `85M3QCF*` (12) — each produced its
  advertised mission briefing.
* `6J2PNX7S`, `6DPG8HZV`, `G6G8HZHD`, `DVD6G8H1`, `VQKDR440`, `P5DR93WJ`,
  `P5PRG3WJ`, `K5K7LTYM`, `K*KRLTYM` accepted; HUD/briefing values as
  tabulated.
* Pause-menu password line re-displays `K*67LZZM` and `6J2PNX7S` exactly
  (ROM's own encoder).
* Rejections of `GLDJLKHD`, `DD6G8HZV`, `K4BJ5PRF`, `DVD6G8HZ`.
* Hidden codes: `CR3D1TZZ` → credits; `H4X0RD1Z` → `1337`; `T4K34W4Y` →
  developer photo; `D3BVGPLZ`, `H34LTHY*`, `W34P0NZZ`, `M3H34LTH` → RAM
  flags `0x03004C74=1`, `0x03004C48=1`, `0x030017A8=1`, `0x03004C48=1`
  respectively, then return to entry.
* Menu walk: language select, title (NEW GAME/PASSWORD/OPTIONS), options
  (MUSIC toggle and CONTROL row; CONTROL returns to play with no submenu),
  pause (5 items + password line), mission objectives, mission map, password
  entry, mission briefing, in-game HUD, credits, `1337`, developer photo.

### Derived (instruction sequence proves it)

* Decoder, checksum, key/normalizer and range checks at `0x080061B8`
  (disassembly reproduced in §5).
* Success post-processing and clamps at `0x08006414`.
* Hidden-table order (table before algorithm) and handler dispatch through
  `0x0824B9A4` / `0x0801BC8C`.
* Space sizes in §6b (combinatorics over the decoded layout).
* Encoder identity: the pause menu's displayed string is generated from the
  same config; my `encode()` reproduces 22/22 published codes and the two
  codes checked in-emulator.
* The developer menu `0x08006B60` is unreachable in this build: its debug gate
  requires `ROM[0x080000AC] == 0`, but the header game code is `AMEE`.

### Inferred (plausible, not fully exercised)

* b1 and b3 are percentage-like values (they are stored `×4` into 0–100
  fields and clamped at 99). No HUD difference was observed at 0 or 96, so
  their in-game role (health, armour, score, timer…) is not assigned.
* The third HUD counter affected by the 2-bit selector is some
  weapon/fuel/item count; the artwork is a green canister, and the debug menu
  contains both `Fuelcans` and `Flame`, but the exact item was not proven.
* The leetspeak hidden codes read as DEBUG PLEASE / HEALTHY / CREDITS /
  WEAPONS / ME HEALTH / H4X0R D1Z / TAKE AWAY, but the names are inference
  from the strings, not from code comments.

## 8. Unknowns

* Semantics of b1, b3, b4 (low nibble) and b5. All are accepted and stored in
  the mission config; none changed the initial HUD in the probes performed.
* What the 2-bit selector actually selects (only its effect on the third HUD
  counter is observed).
* In-game effect of `H34LTHY*`, `M3H34LTH`, `W34P0NZZ`, `D3BVGPLZ`: they are
  reachable only from the title PASSWORD screen, where they set RAM flags and
  reset the entry screen. Whether those flags were meant to be consumed by a
  live mission (the pause menu has no password input in this build) is not
  demonstrated.
* Level 24 (set by `CR3D1TZZ`) is never played: the handler switches to the
  credits screen instead. Whether any transition launches level 24 is open.
* The seven hidden codes set status 2, so the entry screen treats them as
  "invalid" and returns to the grid even when they perform a visible action;
  the reason for that UI decision is unknown.

## 9. Tooling

All scripts are in `/tmp/opencode/armygreen/` (reproducible, Python 3 +
capstone + arm-none-eabi binutils + mGBA 0.10.5):

| File | Purpose |
|---|---|
| `phase0.py` | hashes, header parse, complement check, embedded Nintendo-logo scan |
| `parse_region.py` | dumps/parses the password data bank and literal xrefs |
| `litval.py` | Thumb `ldr rX,=value` scanner (PC-relative literal pool, value compare) |
| `pwmodel.py`, `pwcodec.py` | decoder/encoder model, published-code round-trip |
| `ssdiff.py` | extracts VRAM/IWRAM/EWRAM from mGBA `.ss*` PNG+zlib savestates |
| `enter_code.py` | closed-loop password entry: savestate-verified cursor and symbol buffer |
| `type_code.py`, `k.py` | key injection and plan generation (xdotool on `:142`) |
| `run_code.py`, `verify_code.py` | enter a code, capture briefing/HUD |

Commands used for the static work:

```bash
arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 \
  --start-address=0x080061b8 --stop-address=0x080064f4 \
  -M force-thumb "Army Men: Operation Green.gba"
python3 pwcodec.py "5VKPR6*B"
python3 pwcodec.py "enc:12,24,15,24,15,15,30"
```

Emulator setup (own display only):

```bash
Xvfb :142 -screen 0 1024x768x24 &
DISPLAY=:142 openbox &
SDL_AUDIODRIVER=dummy DISPLAY=:142 mgba -3 "Army Men: Operation Green.gba" &
```

Screenshots referenced above are the PNGs in `/tmp/opencode/armygreen/`
(`s04_title`, `t05_pw_fresh`, `lvl2_a`, `v3d`, `v4`…`v12`, `novel12_brief`,
`novel12_hud`, `pw_game_pause`, `alt2_pause`, `hid_credits2`, `hid_h4x2`,
`hid_tak2`, `rej_*_2`, `b15_hud`, `f30_hud`, `base2_hud`, `flag_b2_hud`,
`flag_b4_hud`, `flags2_hud`, `a24_hud`, `c24`, `menu_objectives`, `map2`,
`s06_options`).

Legal note: no ROM, graphics, audio or game text is redistributed here; only
addresses, algorithms, hashes and my own generated codes are published.

## 10. Cleanup

The emulator, Xvfb and window manager started for this analysis were stopped
by explicit PID (mGBA 423955, Xvfb 418218, openbox 418221), as was an orphaned
`gdb-multiarch` helper (446046). `pgrep -x mgba` no longer lists the Army Men:
Operation Green process and `pgrep -x Xvfb` no longer lists `:142`.

Disclosure: one early restart used the probe `pkill -x mgba -f`. With `-x`
this matches only a process whose command name is exactly `mgba` and whose
full command line is exactly `mgba`; no such process existed, so it was a
no-op. The other sessions' mGBA processes were checked alive immediately
afterwards and were never signalled. No global `pkill -x mgba` was used.
