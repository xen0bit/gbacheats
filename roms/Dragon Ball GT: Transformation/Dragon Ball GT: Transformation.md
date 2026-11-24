# Dragon Ball GT: Transformation (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Dragon Ball GT: Transformation.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `DBGTTRANSFOR` |
| Game code | `BT4E` (region E / USA), maker `70`, revision `00`, software version `0` |
| Entry word | `0xEA00002E` (stock branch to `0x080000C0`) |
| MD5 | `b60abac7fdbf012de5a3c9403ece89e8` |
| SHA-1 | `8dd4b6e95dca4554a919bff55128481a9a95b611` |
| SHA-256 | `66e27d7389368801f29b2dc59eb96800bb868e4fa0509cb73dd9c8aa0ded865c` |

**Phase 0 / patch check (§16.1):** one Nintendo logo and one GBA header only, at file offset `0`; no multiboot sub-headers, no appended trainer, no cracktro. The entry branch is the stock `0xEA00002E` and the first 4 KiB is a normal crt0. Header checksum is `0x0000` and the stored complement byte `0x4B` does not match the computed `0x64` — the usual rebuilt-header artifact; no code patch was found, so this is recorded as an observation, not evidence of a modified game image. Analysis was done on a byte-identical copy (`/tmp/dballgt/game.gba`) so no emulator artifacts were written to the ROM folder.

## 2. Executive summary

This game has **two developer-intended button-code systems** implemented as plain tables of 16-bit active-high key masks, plus **21 Zenie-purchased unlockables** in the SECRETS menu. There is no password/text-entry code system.

* **Eight in-game codes** (`0x0852FDC`–`0x0853082`): invincibility, one-hit kills, refill health, refill energy, max stats, super speed, infinite energy, infinite strength. Entered during play (not paused); a chime confirms acceptance.
* **Five main-menu character codes** (`0x085A660`–`0x085A6AE`): SS Goku (kid), Piccolo, SS Vegeta, SS4 Goku, Baby Vegeta. Temporary — they expire when the menu is left.
* **Seven additional undocumented button sequences** (`0x085A6B0`–`0x085A72A`) are stored in the same table region and appear in no published list. Their effect could not be isolated (see §8).
* The matcher is a **contiguous suffix matcher** over a ring buffer of recent presses: extra presses *before* a code are ignored, but an insertion *inside* it breaks it. Both directions were proven in-game (§6b).
* All 13 published button codes were verified byte-for-byte against the ROM. One published price was wrong: Multiplayer Robot Swarm costs **3000** Zenie in this image, not 4000 (§6).
* Exact press histories were read in RAM: menu buffer `0x030040E2`, in-game buffer `0x03004134` (both u16 masks). The validator function itself was not isolated; the tables, buffers and matcher semantics are fully characterised without it.

## 3. How to reproduce

**Emulator:** mGBA (SDL build), `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`, `Xvfb :315 -screen 0 1024x768x24`, `openbox`. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. **Hold each key 35–60 ms**; longer holds double-step menus (§16.2).

**Menus walked (all observed):**
1. Boot splash → title: `MULTIPLAYER` (greyed/locked), `OPTIONS`, `SECRETS`, `STORY MODE`, `????` (locked Single Player).
2. `OPTIONS`: Sound Volume, Music Volume, Text Speed (Fast), Credits.
3. `SECRETS`: `0% Unlocked`, 0 Zenie; 21 hidden entries in four groups (§6).
4. `STORY MODE`: Start New Game / Continue Game (disabled until a save point) / Difficulty (Easy, Medium, `????`×2 locked).
5. In-game pause (Start): Continue, View Stats, Exit. `View Stats` shows 10-segment Health/Strength/Power bars — the numeric observable used below.
6. No hidden/debug screen is reachable from any menu; the "test mode" items (Music/SFX/Sprite/Portrait) are ordinary paid SECRETS entries, not button-gated.

**Code entry path for the in-game codes:** Story Mode → Start New Game → advance the dialogue with A → gameplay. Press the sequence while **not** paused. Open pause → View Stats to read the effect.

**Codes used for proof (exact presses):**
* Valid: `Down,Down,Down,Up,Up,Up,Right,Right,Right,Up,Down,Right,Up,B` → stats 6/6/3 → 10/10/10.
* Rejected: identical but final `A` → stats unchanged 6/6/3.
* Novel: `Select` prefixed to the valid sequence (15 presses) → stats 10/10/10.
* Rejected: `Select` inserted after the first three `Down`s → stats unchanged 6/6/3.
* `Refill Health` `Down,Up,Left,Left,Up,Right,Down,B` → red HP bar partially filled → full.

## 4. Address map

All addresses are ROM (`0x08...`) unless marked RAM.

| Address | Size | Meaning |
|---|---|---|
| `0x0852FDC` | 166 bytes | In-game code table: 8 concatenated u16 mask sequences, 83 masks + `0x0000` terminator at `0x0853082` |
| `0x085A660` | 80 bytes | Main-menu character table: 5 sequences × 8 u16 masks |
| `0x085A6B0` | 124 bytes | Seven further B-terminated u16 mask sequences (undocumented; §6b) |
| `0x0852FA4`–`0x0852FC2` | 32 bytes | Decimal constants 10 / 100 / 1000 / 10000 / 100000 / 1000000 / 10000000 (not codes) |
| `0x085A644`–`0x085A65E` | 28 bytes | Table of 32-bit pointers into IWRAM (e.g. `0x030040D8`) and one ROM pointer; not the code metadata |
| `0x030040E2` (RAM) | 16 bytes | Main-menu press-history buffer, u16 active-high masks (observed holding the Piccolo sequence) |
| `0x03004134` (RAM) | 16 bytes | In-game press-history buffer, u16 active-high masks (observed holding the Refill Health sequence) |
| `0x030040D8` (RAM) | 1 byte | Press counter / ring index: starts `0x01`, +N after N presses (`0x09` after 8). **Not** an unlock flag |
| `0x03004164` (RAM) | ~32 bytes | Per-key timing ring (8 u32 handles after 8 presses); fires for accepted *and* rejected codes, so not an acceptance oracle |

Mask encoding (active-high, `~KEYINPUT & 0x3FF`): `A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010 Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200`.

## 5. Algorithm

Derived from the tables plus the in-game suffix experiments:

```
on each new key press p (active-high mask):
    hist = [ ...hist, p ]                 # ring buffer, newest last
    for each code C in the active table:  # in-game table while playing, menu table at title
        if len(hist) >= len(C) and hist[-len(C):] == C:
            apply C.effect
            break
```

* **Suffix, not whole-buffer:** a 15-press input ending in a 14-press code is accepted (§6b, shot 68).
* **Contiguous and exact:** inserting one press inside the 14-press code rejects it (§6b, shot 69); changing the final `B` to `A` rejects it (shot 67).
* **Length range:** 8–14 presses are proven accepted/rejected; the table also stores 3-, 11- and 17-press sequences (§6b).
* **Two separate buffers/tables** are selected by screen: title uses `0x085A660` / `0x030040E2`; gameplay uses `0x0852FDC` / `0x03004134`.
* No checksum, PRNG, XOR or encoding layer exists: the masks are stored literally. This is a pure lookup-and-compare system.

## 6. Tables

### 6.1 In-game button codes (all 8, verified in ROM)

| ROM address | Length | Presses | Published effect |
|---|---:|---|---|
| `0x08052FDC` | 10 | Up,Down,Left,Right,Up,Down,L,R,A,B | Invincibility |
| `0x08052FF0` | 13 | Up,Down,Down,Up,Left,Right,Right,Left,L,R,R,L,B | One-hit kills / break objects in one hit |
| `0x0805300A` | 8 | Down,Up,Left,Left,Up,Right,Down,B | Refill Health |
| `0x0805301A` | 9 | Down,Up,Right,Right,Right,Left,Right,Left,B | Refill Energy |
| `0x0805302C` | 14 | Down,Down,Down,Up,Up,Up,Right,Right,Right,Up,Down,Right,Up,B | Max Out Stats |
| `0x08053048` | 9 | Right,Up,Down,Right,Up,Down,Right,Up,B | Temporary Super Speed |
| `0x0805305A` | 10 | Up,Down,Up,Down,Left,Left,Right,Right,Up,B | Temporary Infinite Energy |
| `0x0805306E` | 10 | Right,Up,Right,Right,Up,Right,Up,Left,Left,B | Temporary Infinite Strength |

One published source rendered Super Speed as `Right,Up,Down,Right,Up,DownRight,Up,B` (an OCR run-together typo). The ROM literal is 9 separate masks as listed above.

### 6.2 Main-menu character codes (all 5, verified in ROM)

All share the prefix Left,Right,Left,Right and end in B:

| ROM address | Tail after prefix | Character |
|---|---|---|
| `0x0805A660` | Up,Up,Up,B | SS Goku (kid) |
| `0x0805A670` | Up,Up,Down,B | Piccolo |
| `0x0805A680` | Up,Down,Down,B | SS Vegeta |
| `0x0805A690` | Down,Down,Down,B | SS4 Goku |
| `0x0805A6A0` | Down,Down,Up,B | Super Baby Vegeta |

GamesRadar's note that SS Vegeta uses "only one up" is wrong for this image: the ROM stores `Up,Down,Down,B` exactly.

### 6.3 SECRETS unlockables (21 items, observed in-game)

| Group | Count / prices (Zenie) |
|---|---|
| Characters | Goku, Pan, Trunks, Uub free; 5 hidden @ 2000, 2000, 2000, 4000, 6000 |
| Game Modes | 6 hidden @ 2000, 4000, 3000, 2000, 4000, **3000** |
| Options | 4 hidden @ 1000 (Hard), 8000 (Saiyan), 1000 (Game Speed), 6000 (Explosive Touch) |
| Extras | 4 hidden @ 2000 (Portrait Gallery), 1000 (SFX Test), 1000 (Music Test), 5000 (Sprite Test) |

Total 59,000 Zenie. The final Game Mode price is **3000** in this ROM; several published lists say 4000 for Multiplayer Robot Swarm. Single Player (`????`) is not purchasable — it requires finishing Story Mode. These are save-bit purchases, not button codes (§16.18).

### 6.4 Non-code data nearby

`0x0852FA4`–`0x0852FC2` is a powers-of-ten constant table (10, 100, 1000, 10000, 100000, 1000000, 10000000) that happens to abut the in-game code table. Failing to separate these produces spurious "codes".

## 6b. Enumeration

**Space definition.** The code space is the set of u16-mask strings in the two literal tables, not a checksum space:

* In-game space: **8 codes**, lengths 8–14, total 83 stored masks (166 bytes incl. terminator).
* Menu space: **5 codes**, fixed length 8, total 40 masks (80 bytes).
* Undocumented space: **7 further stored sequences**, lengths 3, 3, 3, 8, 11, 17, 17 (124 bytes), all at `0x085A6B0`–`0x085A72A`, absent from GameFAQs, IGN, TCRF, VGChartz, CheatingDome, CheatCC and SuperCheats.

Because the matcher is a suffix matcher, the *effective* input space is unbounded above: any string ending in a table entry is accepted. This was demonstrated with a **novel 15-press code not in any published list** (§6b.1).

### 6b.1 Novel code, entered and RAM/visually verified

`Select, Down, Down, Down, Up, Up, Up, Right, Right, Right, Up, Down, Right, Up, B`

This is `Select` prefixed to the published Max Out Stats code. Entered in gameplay after loading a savestate with stats 6/6/3; pause → View Stats showed **Health 10/10, Strength 10/10, Power 10/10** (shot 68). No published list contains this 15-press sequence. It proves both that undocumented inputs are accepted and that the matcher ignores leading presses.

### 6b.2 Undocumented ROM sequences (not yet effect-mapped)

| ROM address | Length | Presses |
|---|---:|---|
| `0x0805A6B0` | 17 | Down,Up,Left,Left,Down,Up,Left,Left,Down,Up,Left,Left,Up,Up,Down,Up,B |
| `0x0805A6D2` | 3 | Up,Down,B |
| `0x0805A6D8` | 3 | Left,Right,B |
| `0x0805A6DE` | 3 | L,R,B |
| `0x0805A6E4` | 8 | Up,Left,Down,L,R,L,R,B |
| `0x0805A6F4` | 11 | Up,Up,Down,Right,Down,Right,Up,Left,Left,Up,B |
| `0x0805A70A` | 17 | Left,Up,Up,Down,Left,Up,Up,Down,Left,Up,Up,Down,Left,Up,Up,Down,B |

The 17-press sequence at `0x0805A6B0` was pressed in-game (no stat or HP change observed), so its consumer is probably a different screen or an unused/debug path. It is reported as an exact ROM literal, not as a claimed effect.

### 6b.3 Bounds proven by rejection

| Test | Input | Result | Screenshot |
|---|---|---|---|
| Correct Max Out Stats | 14 presses ending B | 6/6/3 → **10/10/10** | `shot_66.png` |
| Wrong final key | same 13, final **A** | unchanged **6/6/3** | `shot_67.png` |
| Novel extra prefix | Select + 14 (15 total) | **10/10/10** | `shot_68.png` |
| Mid-sequence insertion | Select after 3×Down | unchanged **6/6/3** | `shot_69.png` |
| Refill Health | 8 presses ending B | partial red bar → **full** | `shot_23.png` → `shot_24.png` |
| Refill Health near-miss | final **A** | no refill | `shot_61.png` |

The four Max Out Stats trials use the same savestate and the same observable, so they isolate the matcher semantics cleanly.

## 7. Validation evidence

**Observed (emulator / RAM):**
* Title and every menu screen enumerated by screenshot (`shot_31`–`shot_48`, `shot_62`–`shot_64`).
* SECRETS shows 21 hidden entries, prices read directly from the rendered screen.
* All 13 literal code strings located in the ROM at the addresses in §4, decoded as u16 key masks.
* Menu press buffer `0x030040E2` observed holding `20 00 10 00 20 00 10 00 40 00 40 00 80 00 02 00` (the Piccolo code) after entry; all-zero before.
* In-game press buffer `0x03004134` observed holding the exact Refill Health mask sequence after entry; all-zero/0x0001 before.
* Stats 6/6/3 → 10/10/10 on valid + novel inputs; unchanged on both rejected inputs.
* Health bar partial → full on Refill Health; unchanged on its near-miss.

**Derived (from ROM bytes plus the suffix experiments):** the mask encoding, table bounds, suffix-match algorithm, and the split between gameplay and title tables.

**Inferred:** the seven extra sequences in §6b.2 are button inputs intended for some game or debug path; their consumer was not found. The precise validator function address and the internal action-dispatch branches were not isolated — the table plus the suffix behaviour fully determines acceptance, so they are not needed to reproduce any result here.

**Web-derived (verified against the ROM):** public code/price lists from GameFAQs (cheats + PsyHacker script), IGN, CheatingDome, CheatCC, Cheathappens, SuperCheats, GamesRadar. Every published button sequence was checked literally against the ROM; the three discrepancies noted in §6 are corrections, not unverified additions. GameShark/Action Replay/raw-memory codes from those pages were explicitly **not** tested or reported — they are outside the in-game/developer-intended scope.

## 8. Unknowns

* The consumer and effect of the seven undocumented sequences at `0x0805A6B0`–`0x0805A72A`.
* The validator function address. No direct pointer, Thumb/ARM PC-relative literal or BL reference to either table was found (the tables are probably copied to RAM via a block copy before use). A read watchpoint on the press buffer did not fire in the mGBA GDB stub. Acceptance was therefore characterised behaviourally rather than by single-stepping the comparator.
* The in-game flag address for each effect. `0x030040D8` was ruled out as a cheat flag: it is a per-press ring index (+8 after eight presses). Effects were verified through their visible, numeric state (stats, HP bar) instead.
* The exact duration/temporariness of each in-game effect (published as "temporary" for three codes) was not timed.
* The character-code effect could not be seen directly because Single Player is gated behind completing Story Mode; the 5 menu sequences are proven present in ROM and are fully registered into the menu press buffer, but their on-screen character swap was not observed.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd` for Phase 0; a Python header parser and Nintendo-logo scanner for embedded headers.
* `strings -t x -n 4/6/8` and case-insensitive variants: **no readable ASCII menu/debug text** in the 8 MiB image; this game stores UI text as font/tile indices (§16.11). The negative result is therefore based on screen enumeration + literal mask-table discovery, not on strings.
* Python + `capstone` scans: raw pointers, Thumb `LDR [PC,#imm]`, ARM literal loads, Thumb `BL`, and unaligned u32 scans against the table addresses (all negative — recorded).
* `arm-none-eabi-objdump -M force-thumb` for spot disassembly.
* Custom scripts in `/tmp/dballgt`: `phase0.py`, `search_masks.py`, `dump_tables.py`, `tables_full.py`, `final_enum.py`, `ssdiff.py`, `diff_states.py`, `scan_validator.py`, `scan_arm.py`, `scan2.py`, `key.py`, `probe2.py`, `cleantest.py`, `ingame_probe.py`.
* mGBA `-g` GDB stub driven through a persistent FIFO session (`gdb-multiarch`, `dump binary memory`, `x/uh`); savestate PNG `gbAs` zlib extraction as a fallback for RAM inspection (§16.13).
* Screenshots `shot_00`–`shot_69.png` (root capture, cropped to the 720×480 GBA viewport) retained in `/tmp/dballgt`; key frames cited above.

**Legal note:** no ROM bytes or copyrighted assets are redistributed here — only hashes, addresses, decoded button sequences and original observations.
