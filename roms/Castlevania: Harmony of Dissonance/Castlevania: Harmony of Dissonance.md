# Castlevania: Harmony of Dissonance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Castlevania: Harmony of Dissonance/Castlevania: Harmony of Dissonance.gba` |
| Size | 8,388,608 bytes (8 MiB, `0x800000`) |
| `file` | Game Boy Advance ROM image: "CASTLEVANIA1" (ACHEA4, Rev.00) |
| MD5 | `ea589465486d15e91ba94165c8024b55` |
| SHA-1 | `b90da0d9be0b3a0893cd9e2c399056bcf9579e21` |
| SHA-256 | `85e0a40de22783badbbc95d6bcad68a3a25d0916c4111956213f8281358a61db` |
| Header title | `CASTLEVANIA1` (0xA0) |
| Game code | `ACHE` (0xAC) |
| Maker code | `A4` (0xB0) |
| Version | 0 (0xBC) |
| Complement check | 0x6F (0xBD) — computed 0x6F, matches |
| Header checksum | 0x0000 (0xBE) — normal for a stock header |
| Entry word | `0xEA00002E` → branch to `0x080000C0` (stock crt0) |
| Embedded GBA headers | 1 (logo at file 0x04; full 156-byte logo matches) |
| Region / revision | USA, Rev.00 |

The SHA-1 exactly matches TASVideos' "Castlevania - Harmony of Dissonance (USA).gba" (Good dump), so this is the USA retail build.

**Patch / trainer:** none. The entry word is the stock `b 0x080000C0`, the complement check matches, and the only embedded header is the game's own. No cracktro, no appended trainer.

## 2. Executive summary

The name-entry screen is the only in-game cheat surface in this ROM. It is a real consumer of the entered text, not a label:

* The entered name is stored in an 8-byte buffer at **EWRAM `0x02000020`**, one byte per character, encoded as **alphabet index + 2** (`A`=2 … `Z`=27, `&`=28, symbols 29–35, space = `0x00`).
* On Start/OK, a validator at **`0x080004FBC`** copies the buffer to `0x02000078` and compares it, byte-for-byte over all 8 bytes, against exactly **three** hard-coded names:
  * `MAXIM`  → table `0x080C4150`
  * `NO MAGIC` → table `0x080C4158` (space = `0x00`)
  * `HARDGAME` → table `0x080C4160`
* A **gate** blocks the whole check unless **EWRAM `0x0200035C` & 0x3F ≠ 0** (and the menu object's byte `+0x0B` is 0). With the gate clear, none of the names do anything; with the gate set, all three fire. This matches the published "after you beat the game" requirement.
* Effects (observed in RAM):
  * `MAXIM`  → `0x02000081 = 0xFF` and a call to `0x080051C8`.
  * `NO MAGIC` → `0x02000330 |= 0x1F000000`.
  * `HARDGAME` → `0x02000314 |= 0x40000000` (bit 30).
* An **empty name** is silently replaced with the default name **`JUSTE`** (table `0x08494DD4`) before validation. This is an unpublished behaviour.
* The debug-menu strings (`SoundTest`, `ObjHitTest`, `StackTest`, `FontTest`, `ObjSpriteTest`, `TEST_VIEW`, `SOUND MODE`, `STAFF ROLL`, `Exit`, plus stage/enemy names and an "Easy Sound Test." track list) exist in the ROM at `0x080C3FD8`–`0x080C4620`, but the pointer tables that reference them (`0x080494580`, `0x080495298`) have **no code xref**. They are dead code or reached only through the script VM; no reachable entry point was found.
* The published Konami code (`Up,Up,Down,Down,Left,Right,Left,Right,B,A,Select`) does **not** appear in this ROM in any of the obvious encodings (active-high byte sequence, u16 sequence, reversed).

## 3. How to reproduce

Environment: mGBA 0.10.5 (`mgba-sdl`), Xvfb `:237`, `SDL_AUDIODRIVER=dummy`, `openbox`. Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows. **Hold keys 200–300 ms**; the name-entry screen drops faster taps.

1. Boot the ROM. Title screen → press Start → file select ("select data").
2. Press A on a file → name-entry screen ("Name entry").
3. Type a name with the d-pad + A. `R` inserts a space (`0x00`). `B` deletes.
4. Press Start (or move to OK and press A) to confirm.
5. To make the special names fire, the gate `0x0200035C & 0x3F` must be non-zero. In a stock, never-cleared game it is 0, so the names are inert. I proved the gate by patching the byte in a savestate (see §7).

Savestates used: `hod.ss4` (empty name), `hod.ss7` (name typed), `hod_gate.ss1` (empty name + gate byte = 1).

## 4. Address map

| Address | Meaning |
|---|---|
| `0x080004EA8` | Name-entry screen input/update handler |
| `0x080004FBC` | Name validator (Start/OK dispatch, r8 = 1) |
| `0x080005088` | HARDGAME comparison loop |
| `0x0800050B2` | NO MAGIC comparison loop |
| `0x0800050EC` | NO MAGIC action (`0x02000330 \|= 0x1F000000`) |
| `0x08000511E` | HARDGAME action (`0x02000314 \|= 0x40000000`) |
| `0x080005064` | MAXIM action (`0x02000081 = 0xFF`, call `0x080051C8`) |
| `0x080051C8` | Function called on MAXIM match |
| `0x080C4150` | `"MAXIM\0\0\0"` (8-byte table) |
| `0x080C4158` | `"NO MAGIC"` (8-byte table, space = `0x00`) |
| `0x080C4160` | `"HARDGAME"` (8-byte table) |
| `0x08494DD4` | `"JUSTE\0\0\0"` (default name, 8-byte table) |
| `0x080C3FD8`–`0x080C40F4` | Debug menu / stage-select strings |
| `0x080C45E0`–`0x080C4610` | `SoundTest`, `ObjHitTest`, `StackTest`, `FontTest`, `ObjSpriteTest` |
| `0x080C4DA0` | `"Easy Sound Test."` + track list (`810 Maxim`, `811 Peeping Sahadow`, …) |
| `0x080494580` | Debug menu option table (GAME / TEST_VIEW / … / Exit) — no code xref |
| `0x080495298` | Test-view option table (ObjSpriteTest / FontTest / …) — no code xref |
| `0x080008B4` | Joypad reader (active-high state: A=1 … L=0x200) |
| RAM `0x02000020` | Name buffer (8 bytes, index+2) |
| RAM `0x02000078` | Validator's copy of the name (8 bytes) |
| RAM `0x0200035C` | Gate byte (bits 0–5 must be non-zero) |
| RAM `0x02000314` | HARDGAME flag (bit 30) |
| RAM `0x02000330` | NO MAGIC flag (bits 24–28) |
| RAM `0x02000081` | MAXIM flag (`0xFF`) |

## 5. Algorithm

Name-entry input handler (`0x080004EA8`):

```
loop over pressed keys (active-high):
  Start (0x08)            -> confirm name (r8 = 1)
  A     (0x01)            -> if cursor index <= 0x21: name[col] = cursor_index + 2; col++
                              else if cursor == 0x22 (DEL): delete (r8 = 3)
                              else (OK, 0x23): confirm (r8 = 1)
  B     (0x02)            -> delete (r8 = 3)
  R/L   (0x300)           -> col += 1 (R) / col -= 1 (L)   [name editing]
  Left/Right (0x30)       -> row = idx / 9; col = (idx ± 1) % 9; idx = row*9 + col
  Up/Down   (0xC0)        -> idx = (idx ± 9) % 36
```

Validator (`0x080004FBC`):

```
1. Scan name[0..7] for the first byte with (byte - 2) & 0xFF <= 0x20.
   If none (empty name), overwrite name[0..7] with "JUSTE\0\0\0" (0x08494DD4).
2. Copy name[0..7] -> 0x02000078.
3. Gate: if (0x0200035C & 0x3F) == 0 -> return (no effect).
   Gate 2: if object[0x0B] != 0 -> return.
4. Compare 0x02000078[0..7] against:
     0x080C4150 "MAXIM\0\0\0"   -> if equal: 0x02000081 = 0xFF; call 0x080051C8; action 0x148
     0x080C4160 "HARDGAME"      -> if equal: 0x02000314 |= 0x40000000; action 0x130
     0x080C4158 "NO MAGIC"       -> if equal: 0x02000330 |= 0x1F000000; action 0x92
   Each comparison is a byte-for-byte loop over all 8 bytes.
5. Call 0x0800BB560(action).
```

Character encoding: the on-screen alphabet is 36 entries (A–Z, `&`, heart, `-`, `,`, `.`, `!`, `*`, `@`, DEL, OK). Letters/symbols map to indices 0–33; the stored byte is `index + 2`. Space is `0x00` (entered with R). DEL = 34 (`0x22`), OK = 35 (`0x23`).

## 6. Tables

Special-name tables (8 bytes each, NUL-padded):

| ROM address | Bytes | Name | Gate-dependent effect |
|---|---|---|---|
| `0x080C4150` | `0E 02 19 0A 0E 00 00 00` | MAXIM | `0x02000081 = 0xFF`, call `0x080051C8` |
| `0x080C4158` | `0F 10 00 0E 02 08 0A 04` | NO MAGIC | `0x02000330 \|= 0x1F000000` |
| `0x080C4160` | `09 02 13 05 08 02 0E 06` | HARDGAME | `0x02000314 \|= 0x40000000` |
| `0x08494DD4` | `0B 16 14 15 06 00 00 00` | JUSTE (default) | none (replaces empty name) |

## 6b. Enumeration

**Space definition.** The name buffer is exactly 8 bytes. Each byte is one of:
* `0x00` — space (R button),
* `0x02`–`0x23` — the 34 on-screen letters/symbols (A=2 … `@`=0x23),
* `0x00`/`0xFF` — uninitialised/empty padding.

The validator compares all 8 bytes. The representable name space is therefore `35^8 ≈ 2.2 × 10^12` (34 symbols + space), but the validator accepts only **exactly three** 8-byte strings, each of which must match byte-for-byte including the NUL padding. There is no checksum, no field packing, and no generator: it is a closed list.

**Complete enumeration of accepted inputs.** The validator has exactly three comparison loops (MAXIM, HARDGAME, NO MAGIC) and no others. The dispatch table at `0x080004FA0` (r8 = 1/2/3) only reaches the name validator for r8 = 1; r8 = 2/3 are delete/edit paths. Therefore the accepted set is exactly:

```
"MAXIM"  (0E 02 19 0A 0E 00 00 00)
"NO MAGIC" (0F 10 00 0E 02 08 0A 04)
"HARDGAME" (09 02 13 05 08 02 0E 06)
```

**Novel input.** The three published names are the complete accepted set, so there is no *fourth* special name to mint. Two unpublished behaviours were instead found and proved:

1. **Empty name → `JUSTE`.** Pressing Start/OK with an empty name buffer makes the validator overwrite it with `"JUSTE"` (`0x08494DD4`) before the gate check. Observed: empty name + gate=1 → name buffer `0B 16 14 15 06 00 00 00`. This default is in no published list.
2. **The gate is a real, separate layer.** The three names are inert while `0x0200035C & 0x3F == 0`. This was proved by diffing RAM with the gate clear vs. set (§7).

**Bounds proven by rejection.**
* A one-character wrong name (`VARDGAME`, first byte `0x17`) → no flag set (`0x02000314 = 0`, `0x02000330 = 0`, `0x02000081 = 0`). The comparison is byte-exact.
* An empty name with the gate clear → no flag set (the gate returns before the comparison).
* A name longer than 8 characters cannot be entered (the entry handler caps `col` at 7 and wraps the cursor to the bottom row).

## 7. Validation evidence

**Observed (emulator + savestate RAM):**

| Test | Gate `0x0200035C` | Name buffer `0x02000020` | `0x02000314` | `0x02000330` | `0x02000081` |
|---|---|---|---|---|---|
| HARDGAME, gate clear | 0 | `09 02 13 05 08 02 0E 06` | `0x00000000` | `0x0` | `0x00` |
| HARDGAME, gate = 1 | 1 | `09 02 13 05 08 02 0E 06` | `0x40000000` | `0x0` | `0x00` |
| NO MAGIC, gate = 1 | 1 | `0F 10 00 0E 02 08 0A 04` | `0x0` | `0x1F000000` | `0x00` |
| MAXIM, gate = 1 | 1 | `0E 02 19 0A 0E 00 00 00` | `0x0` | `0x0` | `0xFF` |
| empty, gate = 1 | 1 | `0B 16 14 15 06 00 00 00` (JUSTE) | `0x0` | `0x0` | `0x00` |
| `VARDGAME`, gate = 1 | 1 | `17 02 13 05 08 02 0E 06` | `0x0` | `0x0` | `0x00` |

The gate byte was set by patching the `gbAs` chunk of a savestate (decompress → set byte at state offset `0x2135C` → recompress). This is a RAM-level proof, not a stock-game path.

**Derived (disassembly):**
* Validator at `0x080004FBC`; three comparison loops; gate at `0x0200035C & 0x3F`.
* Name buffer at `0x02000020`; encoding `index + 2`.
* Effects at `0x02000081`, `0x02000314`, `0x02000330`.
* Default name `"JUSTE"` at `0x08494DD4`.

**Inferred:**
* The gate `0x0200035C & 0x3F` is the "game cleared" flag (the published codes all say "after you beat the game"). A script command at `0x08002ED0E` modifies this byte, but the exact script that sets it in a normal playthrough was not traced.

## 8. Unknowns

* The exact script/command that sets `0x0200035C` in a normal cleared game.
* Whether the debug menu (`0x080494580`, `0x080495298`) is reachable at all. Its strings and tables are present, but no code xref to the tables exists; it is either dead code or driven entirely by the script VM. No reachable entry point was found.
* The exact in-game visible effect of the MAXIM flag (`0x02000081 = 0xFF`) — the flag is set, but the corresponding character/mode was not played through.
* The Konami code for Simon in Boss Rush was not found in this ROM; it may be absent from the USA build or stored in an encoding not searched.

## 9. Tooling

* `arm-none-eabi-objdump`, Capstone 5.0.7 (Thumb), Python 3.
* mGBA 0.10.5 (`mgba-sdl`), Xvfb `:237`, `openbox`, `xdotool`, `scrot`.
* Savestate parser: `zlib.decompress` the `gbAs` chunk of the `.ss*` PNG; layout header/CPU `0x00000`, VRAM `0x01000`, IWRAM `0x19000`, EWRAM `0x21000`.
* Helper scripts in `/tmp/opencode/hod/`: `mgba.py` (GDB stub), `nameentry.py` (name entry), `lz77.py`, `disasm.py`, `shot.sh`.
* Screenshots in `/tmp/opencode/hod/shots/` (not redistributed).

## Legal note

No ROM, graphics, music, or other copyrighted assets are redistributed. All findings are addresses, algorithms, hashes, and my own observations.
