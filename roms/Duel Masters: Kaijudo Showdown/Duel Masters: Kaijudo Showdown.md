# Duel Masters: Kaijudo Showdown (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Duel Masters: Kaijudo Showdown.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `DM KAIJUDO` |
| Game code | `BD6E` (AGB-BD6E-USA) |
| Maker | `70` (Atari) |
| Version | 0x00 |
| Fixed 0x96 @0xB2 | present |
| Header checksum | 0x0000; complement 0x31 (rebuilt-header artifact, §16.1) |
| Entry word | 0xEA00002E — stock `b 0x080000C0`, no cracktro/trainer patch |
| MD5 | `02f23bf2f90126574bc0de0752bed485` |
| SHA-1 | `4a818e070b9097ccfb0d73b2b13636ca4b774a4f` |
| SHA-256 | `6ce2363ad2a86e3d1f4d772509b03e20740c963479e465d3d90f9e22a80b3340` |

Embedded-header scan (156-byte Nintendo logo) found a **second, byte-identical header at file offset 0x1D50B0** (same title, game code, entry word) followed by ordinary Thumb code. It is a duplicated header/data region, **not** a second game image, multiboot stub, or trainer. No scene-crack markers (`CRC BANDIT`, `MODE7`, `SUNHORS`, `TRAINER`) present.

Internal build strings identify the engine: `C:/IQ_DEV/Productions/DuelMaster2_AGB/Src/*` (Mistic Software; Japanese *Duel Masters 2* engine).

## 2. Executive summary

This title has a **developer-intended name-entry cheat system**: the player name typed on the New Game "Enter your name" screen is compared against a fixed table of **11 magic names**. Entering one unlocks a preset 3-star deck, starting credits, shop/minigame/Duel-Room features, or an alternate Puzzle Power image. This is exactly the in-game/developer-intended scope; all GameShark/CodeBreaker entries found on the web are memory patches and were **not** used.

The full code space was enumerated: **exactly 16 `memcmp` call sites in ROM, 15 of which are name comparisons against 11 distinct literals; the 16th is an unrelated checksum**. Every uppercase literal referenced by code was scanned and the only name-like strings are those 11. There is no algorithmic generator and no unpublished name in the table.

The validator nevertheless has an **unadvertised prefix-match flaw**: it calls `memcmp(name, literal, fixed_len)` without verifying the trimmed name's full length. Therefore *any* name beginning with a magic word is accepted. Two codes absent from every published list were minted and confirmed on the real screen with RAM proof:

- **`FORESTX`** → sets the Nature preset-deck flag `0x03004550 = 1` (same effect as `FOREST`).
- **`RICHY99`** → doubles starting credits `0x030043BC: 0x012C (300) → 0x0258 (600)`.

Bounds were proven by rejection: `XFOREST` (magic word not at start) and `ZZZZ` produce no cheat flags.

## 3. How to reproduce

**Emulator**: mGBA (SDL), `SDL_AUDIODRIVER=dummy`, under `Xvfb :317 -screen 0 1280x1024x24`; keymap A=`x`, B=`z`, Start=`Return`, D-pad=arrows.

**Path**:
1. Boot; press through the Mistic/Hasbro/intro screens to the title.
2. Select **New Game** → "Enter your name" screen (default name `TOM`).
3. Press **B** three times to clear the default name.
4. Type the code on the on-screen keypad (D-pad to a cell, **A** to enter). Keypad grid:

   ```
   A B C D E F G H
   I J K L M N O P
   Q R S T U V W X
   Y Z 1 2 3 4 5 6
   7 8 9 0 - <space> <backspace> OK
   ```

   The unlabelled cell at row 5, column 6 is a **space** (proven: `DEV TEAM` enters as `44 45 56 20 54 45 41 4D`).
5. Navigate to **OK**, press **A**, then advance the bus-station cutscene with **A**.
6. Read the effects in IWRAM; for deck codes the flags are set once the game reaches the overworld.

**Published codes verified in ROM** (all 11 literals present at `0x081FB0C8+8*i`, see §6): `FOREST`, `FURY`, `WALTER`, `TOMB`, `BRIGHT`, `RICHY`, `HONEY`, `XRAY`, `GAMER`, `DUALIST`, `DEV TEAM`. 3rd party cheat index list only `FOREST` (deck), the five-tournament deck unlocks, and the beat-the-game Duel Room / Image Gallery; the remaining names were recovered from a community forum and verified against the ROM bytes.

**Out-of-scope published data**: libretro/3rd party cheat indexes CodeBreaker codes (e.g. `830043BC FFFF` infinite money, `430043C2 6262...` all cards) are external RAM patches. They were not applied; their target addresses independently corroborate the save/state fields identified here (money `0x030043BC`, cards from `0x030043C2`, preset decks `0x03004542+`).

## 4. Address map

| Address | Type | Meaning |
|---|---|---|
| `0x080000C0` | ROM | stock entry / crt0 |
| `0x081FAF08` | ROM/Thumb | `memcmp(r0=a, r1=b, r2=len)`; 0 = equal (validator core) |
| `0x08151DC4` | ROM/Thumb | deck + money cheat check function (registered as callback at `0x081524DC`) |
| `0x08147CBA`, `0x08147EB2`, `0x08147F7A`, `0x08148168` | ROM | four `DUALIST` comparisons |
| `0x08150062`, `0x0815011E` | ROM | `GAMER` comparisons |
| `0x0815963E` | ROM | `HONEY` comparison |
| `0x0816BEA2` | ROM | `DEV TEAM` comparison / alternate Puzzle Power image |
| `0x08172084` | ROM | `XRAY` comparison |
| `0x081EC07A` | ROM | unrelated byte-sum checksum (not a name check) |
| `0x081FB0C8` | ROM | cheat-name string pool, 11 strings, 8-byte stride (replicated across compilation units through `0x081FF000`) |
| `0x030003F4` | IWRAM | trimmed player-name length (used by validator) |
| `0x030044F0` | IWRAM | player-name buffer (NUL-padded, 8 visible bytes) |
| `0x030043BC` | IWRAM | store credits, 32-bit (300 = `0x12C`) |
| `0x0300454D` | IWRAM | TOMB (Darkness 3★ deck) unlock flag |
| `0x0300454E` | IWRAM | FURY (Fire 3★ deck) unlock flag |
| `0x0300454F` | IWRAM | BRIGHT (Light 3★ deck) unlock flag |
| `0x03004550` | IWRAM | FOREST (Nature 3★ deck) unlock flag |
| `0x03004551` | IWRAM | WALTER (Water 3★ deck) unlock flag |

mGBA `.ssN` savestate layout used for RAM reads: PNG `gbAs` chunk is raw zlib state; IWRAM begins at raw offset `0x19000` (so `0x030044F0` → raw `0x1D4F0`), EWRAM at `0x21000`.

## 5. Algorithm

```
# entered name -> buffer at 0x030044F0; length -> 0x030003F4
length = trim_trailing_spaces(name_buffer, name_length)   # 0x08151DD8..0x08151E12

# deck/money checks, function 0x08151DC4:
if memcmp(name, "RICHY",  5) == 0: credits = credits << 1        # 0x030043BC
if memcmp(name, "BRIGHT", 6) == 0: flag[0x0300454F] = 1
if memcmp(name, "FURY",   5) == 0: flag[0x0300454E] = 1
if memcmp(name, "TOMB",   4) == 0: flag[0x0300454D] = 1
if memcmp(name, "FOREST", 6) == 0: flag[0x03004550] = 1
if memcmp(name, "WALTER", 6) == 0: flag[0x03004551] = 1

# other contexts (checked when their feature is used):
if memcmp(name, "DUALIST", 7) == 0:  unlock Duel Room         # 0x08147CBA etc.
if memcmp(name, "GAMER",   5) == 0:  unlock minigames          # 0x08150062
if memcmp(name, "HONEY",   5) == 0:  shop items free           # 0x0815963E
if memcmp(name, "XRAY",    4) == 0:  reveal opponent's cards   # 0x08172084
if memcmp(name, "DEV TEAM",8) == 0:  alternate Puzzle Power image (0x0816BEA2;
                                     image display is gated on 0x03000F04/05 per community)
```

**Critical flaw**: `memcmp` is called with the magic word's fixed length; `length` is used only to trim trailing spaces and is never compared to `len`. A longer name sharing the magic prefix therefore passes. Also, `memcmp` is case-sensitive exact bytes — the on-screen keypad offers only uppercase, so lowercase aliases are not reachable through the UI.

## 6. Tables

### 6.1 Complete cheat table (all 11 — exhaustive)

| Name | Length | Effect | Effect proof |
|---|---|---|---|
| `FOREST` | 6 | Nature 3★ preset deck | Observed `0x03004550=1` |
| `FURY` | 5 | Fire 3★ preset deck | Observed `0x0300454E=1` |
| `WALTER` | 6 | Water 3★ preset deck | Observed `0x03004551=1` |
| `TOMB` | 4 | Darkness 3★ preset deck | Observed `0x0300454D=1` |
| `BRIGHT` | 6 | Light 3★ preset deck | Observed `0x0300454F=1` |
| `RICHY` | 5 | Start with 600 credits | Observed `0x030043BC 0x12C→0x258` |
| `HONEY` | 5 | Shop items free | Derived from `0x0815963E` call path |
| `XRAY` | 4 | See opponent's cards in duel | Derived from `0x08172084` call path |
| `GAMER` | 5 | Unlock minigames | Derived from `0x08150062` call path |
| `DUALIST` | 7 | Unlock Duel Room | Derived from `0x08147CBA` call path; title-screen entry still greyed in tested save |
| `DEV TEAM` | 8 | Alternate Puzzle Power image | Derived from `0x0816BEA2`; display gated (community: `0x03000F04=1`, `0x03000F05=2`) |

### 6.2 Input alphabet

Keypad cells, 8×5 grid: `A–Z`, `1 2 3 4 5 6 7 8 9 0`, `-`, unlabelled **space**, backspace, OK. 39 selectable cells. Magic names use only `A–Z` and space.

## 6b. Enumeration

**Space definition.** This is a fixed lookup table, not a checksum system: 11 magic strings over a 39-symbol keypad, each compared with a fixed `memcmp` length. There is no checksum, no bit packing, and no generator function. The complete representable set of *accepted magic words* is exactly 11.

**Closure proof (§0.2 / §16.9).** Instead of inferring from the string pool alone, the game's own comparison sites were enumerated and run over:
- 16 call sites to `memcmp` at `0x081FAF08` in the whole 8 MiB image.
- 15 are name comparisons; their literals resolve to exactly 11 distinct strings (DUALIST ×4, GAMER ×2, the five deck names + RICHY, HONEY, XRAY, DEV TEAM ×1 each). The 16th (`0x081EC07A`) is a byte-sum checksum.
- A sweep of every 32-bit word in code (`<0x1F0000`) pointing at a plausible uppercase NUL-terminated string returned **exactly** those 11 names and no others.
- All 11 were entered on the real keypad; each produced its expected buffer and at least one distinguishing RAM change (§6.1).

**Novel codes (not in any published list).** The validator's fixed-length `memcmp` permits prefix extensions. Generated and entered on the real screen:

| Novel code | ROM evidence | In-game RAM proof |
|---|---|---|
| `FORESTX` | name buffer `46 4F 52 45 53 54 58 00`; `memcmp(...,"FOREST",6)` matches | `0x03004550 = 01` (Nature flag set); money unchanged |
| `RICHY99` | name buffer `52 49 43 48 59 39 39 00`; `memcmp(...,"RICHY",5)` matches | `0x030043BC = 58 02 00 00` = 600 (doubled from 300) |

These spellings appear on 3rd party cheat indexes, and the community forum: **nowhere**. They exercise an unadvertised combination (prefix acceptance) that the published lists omit.

**Bounds proven by rejection.**
- `XFOREST` (magic word present but not at offset 0) → flags all 0, money `0x012C`; rejected. (Observed, savestate `ss2`.)
- `ZZZZ` (no magic word) → flags all 0, money `0x012C`; rejected. (Observed, control `ss4`.)
- Trailing-space spelling `FOREST␠␠` is accepted but the **entry UI** stores it as canonical `FOREST\0\0` (trailing spaces dropped before the buffer is written): the validator's trim path is real in code but not reachable with trailing spaces from this keypad. It is an alias, not a distinct code (§16.4b).

## 7. Validation evidence

- **Observed**: 11 names typed on the real keypad; name buffers read from IWRAM `0x030044F0` in mGBA savestates. Five deck flags and the money field changed exactly as predicted; two novel prefix codes and two rejected inputs were measured. Screenshots were captured at title, name entry, cutscene, and overworld (work dir `/tmp/duelmasters/shot_*.png`).
- **Derived**: `memcmp` semantics at `0x081FAF08`; the 16 call sites and 11 literals; callback registration at `0x081524DC`; flag/effect addresses; the missing full-length check that enables prefix codes. `HONEY`, `XRAY`, `GAMER`, `DUALIST`, `DEV TEAM` effects are derived from their call paths — their trigger conditions were observed (name buffer accepted) but the downstream feature screens were not all visited.
- **Inferred**: the community report that `DEV TEAM`'s alternate image requires forcing `0x03000F04=1`, `0x03000F05=2`; not independently reproduced. The reason `DUALIST` did not visibly enable the title-screen Duel Room in the tested save is unresolved (possibly written to EEPROM after a later save event, or the "Main Menu" in the unlock message refers to the in-game Pocket Gizmo).

## 8. Unknowns

- Downstream screen-level confirmation of `HONEY`, `XRAY`, `GAMER`, `DUALIST`, `DEV TEAM` (their comparison and name acceptance were observed; the shop/duel/minigame/Duel-Room effects were not all played through).
- Whether the deck flags at `0x0300454D–51` are the same field the CodeBreaker "Have All Preset Decks" code writes at `0x03004542+` (adjacent but not identical addresses).
- The second header at `0x1D50B0` was not fully typed (duplicate data region vs. intentional mirror); it is not a separate playable image.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, Python 3 byte scans.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for validator disassembly.
- Python `capstone` available but not required; raw BL scanner and literal-pointer scanner used instead.
- mGBA (SDL) + Xvfb `:317` + xdotool; savestate RAM reads via a Python `gbAs`/zlib parser (`ss.py`), with IWRAM at raw `0x19000`.
- Scripts: `/tmp/duelmasters/{k.py,enter_name.py,testname.py,batchtest.py,ss.py}`.

**Legal note**: no ROM bytes or copyrighted assets are reproduced here; only hashes, addresses, algorithms, and generated code strings are published.
