# Spyro: Season of Ice (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Spyro: Season of Ice/Spyro: Season of Ice.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `SPYRO` |
| Game code / maker | `ASYE` / `7D`, version `0x00` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`; **not** a cracktro, §16.1) |
| Header checksum / complement | `0x0007` / `0x00` |
| MD5 | `76aad0726be3ac24f3c5a7a8e64379d3` |
| SHA-1 | `a9768fa99ae74034ab19a45b30004306f1deff89` |
| SHA-256 | `d331abe19e3f02e2855aa4bbc2de14626810aca83e0c216862eb1d8ca8d024b0` |

Save hardware: 512-byte SRAM (`*.sav`, 5 nonzero bytes after boot) — the cheats are **button codes**, not passwords.

## 2. Executive summary

The game has one developer-intended cheat system: **eight fixed 8-press D-pad sequences** entered at the "PRESS START" title screen, each ending with a separate `A` confirm press. The sequences are stored as a contiguous table of 128 bytes (`0x0805DB74`–`0x0805DBF3`, eight records × 8 × `u16` active-high key masks). A single validator at `0x0800D1A0` copies the table to the stack, compares each record against a circular 8-entry input history, and on a match sets bit `i` (record index) of the IWRAM flag word at `0x03002254`; record 1 additionally sets bit 0.

All eight records were replayed in mGBA and each produced exactly the predicted flag bits (§6b). One record, **index 2 at `0x0805DB94` (`↑ ↑ → ↓ ↓ ↓ ← ↓` + A), appears in no published list**; it sets flag bit 2 (`0x00000004`) and visibly enables the previously dim `Dragonfly X` menu entry, which then opens a cutscene. Three negative tests (all-Up, a one-press near miss, and a 7-press truncation) were rejected with flag `0`. The search space is therefore closed: exactly 8 accepted sequences, strict full-length matching.

A second, separate published input surface exists (hold-`Select` weapon/key combos in Sparx levels, and `L`/`R` particle controls in menus/credits). No compact mask table for it was found by exhaustive prefix/permutation searches (§8); those claims remain web-sourced leads rather than independently proven codes.

## 3. How to reproduce

**Emulator**: mGBA 0.10.5 under Xvfb `:318` (`SDL_AUDIODRIVER=dummy`), `-g` GDB stub (handshake incompatible with installed `gdb-multiarch`; §16.13 fallback used).

**Keymap (verified)**: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, L=`a`, R=`s`, D-pad=arrow keys. Hold each key ~100 ms; ~100 ms gap.

**Code entry**: at the actual `PRESS START` title screen (not the intro logos — the validator is gated on a scene-state word), press the eight D-pad directions in order, then press `A`. Do **not** press Start before the sequence. `Ctrl+R` resets to the intro; the title screen must be awaited or restored from a savestate.

**RAM evidence without a working GDB stub**: mGBA `.ssN` states are PNGs with a zlib `gbAs` chunk (397,312 bytes here). Decompressing gives IWRAM at raw offset `0x19000`; the flag word `0x03002254` is therefore `raw[0x1B254:0x1B258]`. Save a baseline state at the title screen, enter a code, save another state, and read/diff that word. (Verified: baseline `0x00000000` → 99-lives code `0x00000008`.)

**Screens walked**: intro logos → title (`PRESS START`) → main menu (`Continue Game`, `New Game`, `Options`, `Dragonfly X`) → Options (`Music: On`, `Sound FX: On`, `Credits`) → Credits (`Developed by`; particle controls published) → newly unlocked `Dragonfly X` cutscene.

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x0805DB74` | ROM table | Cheat code table, 128 bytes: 8 records × 8 `u16` direction masks (active high: `R=0x10, L=0x20, U=0x40, D=0x80`) |
| `0x0805DBF4` | ROM data | Separate particle-parameter table used by the credits/menu background controller (values `0x0403,0x0201,…`) |
| `0x0800D1A0` | ROM/Thumb | **Validator**. Copies table to stack (`BL 0x0805D95C`, 0x80 bytes), loops `i=0..7`, `j=0..7`, compares `table[i*8+j]` with `ring[(head+j)&7]`, sets flag bit on full match, clears the 8-entry ring, calls `0x0803ED8` |
| `0x0800D200` | ROM/Thumb | Flag-set block: `flags \|= (1<<i)`; if `i==1`, also `flags \|= 1` |
| `0x0800E754` | ROM/Thumb | Sole caller: runs only when scene-state `==5` and another state `==0`; calls validator when `*(u16*)0x03001014 == 1` (A pressed), then writes that press into the ring and advances `head` |
| `0x03002254` | IWRAM | **Cheat flag word** (bit `i` = code `i` accepted) |
| `0x030014C8` | IWRAM | Pointer to game object base `r7`; ring at `r7+0x560`, head halfword at `r7+0xEC0` |
| `0x03001014` | IWRAM | Newly pressed key mask (active high); `==1` means A |
| `0x030010C0` | IWRAM | Key/state word read by a separate `L`-gated handler at `0x08011B74` (not triggered by the combos tested) |
| `0x0807DD4`, `0x0807FA4`, `0x08083A2`, `0x08046BFC`, `0x0801DF84`, `0x0800A2DE`, `0x0800BA8E`, `0x0800BC6E` | ROM/Thumb | Readers of the flag word: bit2 (portal/menu gating ×3), bit4, bit7 (`unlock all`), bit3 (`99 lives`, writes `0x63`), bit1, bit1/bit2 |
| `0x0805153A` | ROM/Thumb | Writer that stores `r6` into the flag word (reset path) |

File offset = ROM address − `0x08000000`.

## 5. Algorithm

```python
# active-high masks in the table and the input ring
MASK = {R:0x10, L:0x20, U:0x40, D:0x80}

def validator(game, flags_ptr=0x03002254):
    table = rom[0x0805DB74:0x0805DBF4]          # memcpy
    for i in range(8):
        ring = game[0x560:0x570]                 # 8 halfwords
        head = game[0xEC0] & 0xFFFF
        for j in range(8):
            expected = ring[(head + j) & 7]
            actual   = u16(table[i*16 + j*2])
            if expected != actual:
                break
        else:
            flags |= 1 << i
            if i == 1:
                flags |= 1                       # special case in ROM
            ring[:] = [0]*8                      # consumed
            sound_effect(0x0803ED8)
    return flags
```

Input path (caller `0x0800E738`): the validator runs when the scene state is at the title value and `*(u16*)0x03001014 == 1` (A newly pressed). Before calling it, each nonzero press mask has already been written to `ring[head]` with `head = (head+1) & 7`. Because the check runs *before* A is appended, the eight records are exactly the eight preceding D-pad presses. The validator is gated on the title scene state: entering the same presses during the intro logos does nothing (this caused one initial false negative that was corrected by restoring a title-screen savestate).

## 6. Tables

All eight records, decoded from the ROM table and verified in the emulator. Presses are listed in entry order; append `A` to submit.

| i | Table addr | Sequence | Flag set (observed) | Published description / observed effect |
|---|---|---|---|---|
| 0 | `0x0805DB74` | `← → → ← ↑ ← ← →` | `0x01` | Warp to visited levels |
| 1 | `0x0805DB84` | `↓ ↑ ↓ ← → ↑ ← ↑` | `0x03` (bits 1 **and** 0) | Warp to any level |
| 2 | `0x0805DB94` | `↑ ↑ → ↓ ↓ ↓ ← ↓` | `0x04` | **NOT PUBLISHED** — see §6b |
| 3 | `0x0805DBA4` | `← → → → ↓ ↑ → ↑` | `0x08` | 99 lives (reader writes `0x63` at `0x0800A2F2`) |
| 4 | `0x0805DBB4` | `↓ ↑ ↑ ↓ ← → → ←` | `0x10` | Infinite health in Sparx levels |
| 5 | `0x0805DBC4` | `↓ → ↑ ← ← ↑ → ↓` | `0x20` | Infinite ammo in Sparx levels |
| 6 | `0x0805DBD4` | `→ ↑ → ← ↓ ↑ ← ↓` | `0x40` | Weapon-select enabler for the in-game combos |
| 7 | `0x0805DBE4` | `↓ ↓ ↑ ↑ ← → ↑ ↓` | `0x80` | Unlock all levels (reader at `0x0801DF8A`) |

Published in-game combos (web-sourced; entered after code 6, in Sparx levels): `↑+Select` shield, `↓+Select` homing missiles, `←+Select` widespread bullets, `→+Select` purple wipeout, `L+Select` all keys. Menu/credits particle controls: `L+Select` randomness, `L`/`R` + direction/buttons for direction, speed, gravity, lifespan; `L+R` reset; `B` exit credits; `Start` toggle scroll. Quick start: `L+R+Start` at power-on. These are **not** part of the eight-record table.

**Published-code discrepancy**: the widely listed "Level portals opened" sequence `↑ ↑ ↓ ↓ ← → ↑ ↓` does **not** occur anywhere in the 8 MiB ROM as a packed `u16` mask sequence (full 16-byte search: 0 hits). The nearest real records are i7 (`↓↓↑↑←→↑↓`) and i2. Treat that published line as a transcription error.

## 6b. Enumeration

**Space definition.** Exactly **8 records**, each **8 presses** drawn from a 4-symbol D-pad alphabet (`R/L/U/D`, active-high masks `0x10/0x20/0x40/0x80`), stored as `u16` little-endian. Nominal sequence space = `4^8 = 65,536` per record; the ROM accepts exactly one 8-press string per record (8 accepted inputs total out of the 65,536 possible 8-press strings), plus a separate `A` submit press that is not part of the compared string. The flag word is 8 bits (bit 0..7), but only nine distinct values are reachable because record 1 sets bits 1 and 0 together: `{0x01,0x03,0x04,0x08,0x10,0x20,0x40,0x80}` plus `0x00`. No variable-length, checksummed or generated code path exists: the validator's loop bounds are `i<=7`, `j<=7` (`0x800D232`, `0x800D1F8`) and the table is a fixed 128-byte copy.

**Novel code.** Record 2 (`0x0805DB94`) is absent from darkSpyro, GameFAQs, ggmania, GameRevolution, AbsoluteCheats and every other consulted list. Generated from the table layout and replayed on the real title screen:

```
↑ ↑ → ↓ ↓ ↓ ← ↓  A
```

- Decoder: accepted as record 2 (`0x04`).
- Emulator: flag word `0x00000000 → 0x00000004` (savestate RAM read, two independent runs).
- Visible effect: the dim `Dragonfly X` menu entry becomes bright/gold, and selecting it opens a full-screen cutscene; the same navigation on an un-cheated baseline stays in the Options screen. Bit-2 readers at `0x08007DD8`, `0x08007FA8`, `0x080083A2` bypass portal/menu-state constraints, consistent with an unlock flag.

**Complete accept/reject enumeration** (each row: load clean title-state savestate, enter 8 presses + A, read flag word):

| Input | Flag observed | Expected | Result |
|---|---|---|---|
| i0 `←→→←↑←←→` | `0x00000001` | `1<<0` | accept |
| i1 `↓↑↓←→↑←↑` | `0x00000003` | `1<<1 \| 1<<0` | accept |
| **i2 `↑↑→↓↓↓←↓`** | `0x00000004` | `1<<2` | **accept (novel)** |
| i3 `←→→→↓↑→↑` | `0x00000008` | `1<<3` | accept |
| i4 `↓↑↑↓←→→←` | `0x00000010` | `1<<4` | accept |
| i5 `↓→↑←←↑→↓` | `0x00000020` | `1<<5` | accept |
| i6 `→↑→←↓↑←↓` | `0x00000040` | `1<<6` | accept |
| i7 `↓↓↑↑←→↑↓` | `0x00000080` | `1<<7` | accept |
| all-`↑` ×8 | `0x00000000` | reject | **rejected** |
| near miss (one press changed from i2) | `0x00000000` | reject | **rejected** |
| i2 truncated to 7 presses | `0x00000000` | reject | **rejected** |

This proves strict 8-press, exact-match acceptance and bounds the code space to the 8 ROM records. The earlier false negative for i2 (flag stayed 0) was diagnosed as entering the sequence on the intro *logo* screen instead of the title screen — the validator's scene gate — and disappeared after restoring a title-state savestate.

## 7. Validation evidence

* **Observed**: title/menu/Options/Credits/Dragonfly-X screenshots; keymap confirmed by Start navigation; flag-word transitions read from decompressed `.ssN` states (table above); novel code changes menu item color and opens cutscene; 512-byte SRAM created by the game.
* **Derived**: validator loop bounds, table copy size, flag-bit mapping and the `i==1` double-set come from Thumb disassembly at `0x0800D1A0`–`0x0800D234` and its sole caller at `0x0800E754`; bit→effect mapping from flag readers (99 lives `0x0800A2E4`, unlock-all `0x0801DF8A`, portals `0x08007DD8`/`0x08007FA8`/`0x080083A2`).
* **Inferred**: the semantic label "portals/unlock" for bit 2 is inferred from those readers plus the visible menu unlock; the precise in-game meaning of `Dragonfly X` (cutscene/bonus episode) was not played through.

## 8. Unknowns

* The in-game `Select` weapon/key combos and `L`/`R` particle controls are published but were **not** independently verified. No contiguous combo mask table exists in the ROM under active-high, active-low, 8-bit or 16-bit encodings (exhaustive permutations of the five published combos: 0 hits), and a key-state handler at `0x08011B74` (`0x030010C0 & 0x2000`) did not change its output bytes (`0x030014D4/E4/0x03001658`) when `L+Select` was pressed at the menu. They may be inline comparisons reachable only inside Sparx levels; reaching those levels was not attempted.
* Credits particle diffs after `L+Select` were indistinguishable from idle animation (503 vs 530 IWRAM words changed), so that control is unconfirmed rather than disproved.
* Game text is **not** stored as text: `PRESS START`, `PASSWORD`, `OPTIONS`, `CREDITS`, `DEBUG`, etc. were searched in ASCII, lowercase, `+/-0x20` shifted, UTF-16LE and UTF-16BE with zero hits (only one incidental `MENU` at `0x08086A3D`, inside non-UI data). The font/tile bank was located in VRAM but the rendered tile dump was too noisy to map glyphs; a compressed text bank is possible. This is why the negative for "no password screen" rests on the complete validator/table enumeration, not on string searches.
* Effects of bits 0, 1, 4, 5, 6 were not individually played through; only their flag writes were observed.

## 9. Tooling

Scripts written in `/tmp/spyroice2/`: `find_masks.py` (mask-sequence search), `keys.py` (XTEST key helper), `stateutil.py` (gbAs parser / IWRAM reader), `test_code.py`, `verify_all.py` (8-code + 3-rejection sweep), `find_bitreaders.py`, `text_search.py`, `font_dump.py`. Tools: `arm-none-eabi-objdump -M force-thumb`, Python/capstone, mGBA 0.10.5, Xvfb `:318`, openbox, xdotool, scrot. GDB stub was unavailable (protocol handshake errors), so all RAM claims use savestate diffs.

No ROM or copyrighted assets are redistributed here; only addresses, hashes, masks and our own scripts are documented.
