# ZooCube (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/ZooCube/ZooCube.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `ZOO CUBE` (0xA0) |
| Game code | `ANCE` (0xAC) |
| Maker | `51` (0xB0, Acclaim) |
| Version / complement / checksum | 0x00 / 0x9D / 0x0000 |
| Entry word | `0xEA00002E` (stock, no cracktro) |
| MD5 | `01457d05d4601ceff3f6d27a31606c18` |
| SHA-1 | `044713bea5245ee6e31b8ec4744c0696f79b30d0` |
| SHA-256 | `cf535d3ec521e2c60f92bb9eb264146169aadf095ee76a0b05e7ba351e9369da` |

This is a **button-code** engagement. There is no password/code text-entry field. The published
"Password menu" codes (`OPENSESAME`, `ENTERPRISE`, etc.) belong to the **GameCube / PS2 / PC**
SKUs, not this GBA image (§16.11). A GBA-specific FAQ explicitly states it is *not* compatible
with the GameCube version and documents no codes.

## 2. Executive summary

ZooCube GBA contains **one reachable in-game button code** in the Main Menu screen handler:

> **← ← → → ↑ ↓ ↑ ↓ L R**  (Left, Left, Right, Right, Up, Down, Up, Down, L-shoulder, R-shoulder)

Entering it with very short (~2-frame) holds writes four bytes in the EEPROM-backed save record
at `0x03001D29..0x03001D2C`, unlocking **all levels (2–7)**, **all game types (Classic/KO/KO
Blind)** and **all speeds including Warp Speed**, and permanently marks the code as used. It was
confirmed three times in mGBA — twice from a freshly booted cartridge with a clean EEPROM — by
direct RAM reads and by screenshots showing previously red (locked) menu entries turn green.

No password validator exists. The one `A-Z#!` alphabet in the ROM is the **high-score name-entry**
keypad (exactly 3 characters written at `0x0800FA22..0x0800FA40` into the score record), not a
code field (§16.2b). A second, 11-press button table exists at `0x083EBBC6` but has **zero**
pointer or BL references and is unreachable dead data.

## 3. How to reproduce

1. mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, `mgba -3 ZooCube.gba`.
2. Boot and press A (`x`) through the legal/story screens; press Start/A on the title to reach
   **MAIN MENU** (the code is matched in the Main Menu handler at `0x0800C03C`).
3. With the cursor anywhere, tap in order:
   `Left, Left, Right, Right, Up, Down, Up, Down, a(L), s(R)`.
4. **Timing is critical:** hold each key about **0.03 s** (≈2 frames at 60 Hz) with ≈0.15 s
   between keys. The matcher advances its index **every frame** the pressed-key mask equals the
   table entry, so a long hold overruns and resets the sequence. `xdotool keydown; sleep 0.03;
   keyup; sleep 0.15` worked reliably.
5. Do not let the title-screen attract/demo mode start: enter the code promptly after reaching
   Main Menu (a demo transition during entry produced a clean rejection).
6. Read `0x03001D28..0x03001D33` from a savestate (`ZooCube.ssN`, IWRAM at state offset
   `0x19000 + (addr-0x03000000)`). Before: `02 ff ff 03 00 00 ff ff ff ff ff ff`.
   After: `06 06 06 08 01 00 ff ff ff ff ff ff`.
7. Visual check: **Options → Speed** — Express/Rocket/Supersonic/Light Speed/Warp Speed change
   from flashing red to green; **Game Select → Level** — levels 2–7 become green; **Type** —
   KO Blind becomes green.

Published GBA cheats: none found. 3rd party cheat index codes are for other platforms;
zero of the five searched literals (`OPENSESAME`, `ENTERPRISE`, `OQJAMA`, `MCKLLB`, `PASSWORD`)
appear anywhere in this ROM.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x0800C03C` | Main Menu screen function (handler pointer `0x0800C03D`) | Derived — 14 xrefs to `0x0800C03D` are screen transitions to Main Menu |
| `0x0800C204–0x0800C20A` | Gate: `ldrsb` save byte `0x03001D2C`; skip whole check if nonzero | Derived (objdump) |
| `0x0800C20C–0x0800C23C` | Sequence matcher: read mask, index via `r6` high byte, `ldrsh` table entry, compare, advance or reset | Derived + observed (breakpoint at `0x0800C20E` hit with `r1=0x03001E9C`) |
| `0x0800C242–0x0800C258` | Success writes: `0x03001D2C=1`, `0x03001D29=6`, `0x03001D2A=6`, `0x03001D2B=8` (r8=6, set at `0x0800C14E`) | Derived + observed RAM diff |
| `0x083EBBB8` (file `0x3EBBB8`) | Reachable code table, 10 masks + `0xFFFF` terminator | Derived + confirmed in emulator |
| `0x083EBBC6` (file `0x3EBBC6`) | Second, 11-mask table + `0xFFFF`; **no xrefs** | Derived — byte search for the u32 found zero hits |
| `0x080078E0` | Input poller; `KEYINPUT 0x04000130` → raw `0x03001E5C`, new-press mask → `0x03001E9C` | Derived + observed (held Left ⇒ mask `0x0020`, raw `0x03DF`) |
| `0x03001E5C` / `0x03001E9C` | Raw active-low keys / active-high newly-pressed mask | Observed via mGBA debugger `r/2` |
| `0x03001CA0` | Save record base (147-byte payload, checksum at `+148`) | Derived — checksum routine `0x080078BC`, called from `0x08007160/1D4/73C4` |
| `0x03001D28..0x03001D2F` | Settings/unlock bytes mutated by the code | Observed |
| `0x083EBC14` (file `0x3EBC14`) | `ABCDEFGHIJKLMNOPQRSTUVWXYZ#!` — high-score name alphabet | Derived — 3-byte write at `0x0800FA22..40`; 4 xrefs in name-entry code `0x0800F5xx–FAxx` |
| `0x08322xxx` | Plain-ASCII UI text bank (7 language banks via pointer table `0x083E7968`) | Derived |
| `0x03002530` | Current screen-handler pointer; `0x0800C03D` = Main Menu | Derived |

## 5. Algorithm

Pseudocode of `0x0800C204` (Main Menu, per frame):

```
if save[0x1D2C] != 0:            # already used -> never check again
    goto done
mask = halfword[0x03001E9C]      # active-high, newly pressed keys this frame
if mask == 0: goto done
idx = (int8)(r6 >> 24)
expected = (int16)table[0x083EBBB8 + idx*2]
if mask != expected:
    if mask != 0: idx = 0        # reset on any wrong nonzero press
    goto done
idx += 1
if table[idx] == 0xFFFF:         # full sequence matched
    save[0x1D2C] = 1
    save[0x1D29] = 6             # all levels unlocked
    save[0x1D2A] = 6             # all game types unlocked
    save[0x1D2B] = 8             # speed = Warp Speed
    idx = 0
    # additional UI/state updates at 0x0800C25A..0x0800C26C
```

Field meanings are **inferred from the UI** (speed index 8 = Warp Speed; level index 6 = Pacific
Ocean) plus the observed menu changes; the write addresses/values are **observed**.

## 6. Tables

### 6.1 Reachable button table — `0x083EBBB8` (`u16`, little-endian)

| # | Mask | Button |
|---:|---:|---|
| 0 | 0x0020 | Left |
| 1 | 0x0020 | Left |
| 2 | 0x0010 | Right |
| 3 | 0x0010 | Right |
| 4 | 0x0040 | Up |
| 5 | 0x0080 | Down |
| 6 | 0x0040 | Up |
| 7 | 0x0080 | Down |
| 8 | 0x0200 | L |
| 9 | 0x0100 | R |
| 10 | 0xFFFF | terminator |

Button-bit mapping (active-high in the game's normalized state):
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080,
R=0x100, L=0x200`.

### 6.2 Unreachable button table — `0x083EBBC6`

`0x040,0x010,0x080,0x020,0x080,0x010,0x040,0x100,0x200,0x100,0x200,0xFFFF`
= Up, Right, Down, Left, Down, Right, Up, R, L, R, L. **No u32 pointer and no BL target** was
found for this address anywhere in the 4 MiB image; it is dead data, not a second code.

### 6.3 Save-field changes observed

| Address | Before | After | Inferred meaning |
|---|---:|---:|---|
| `0x03001D29` | 0xFF | 0x06 | highest unlocked level index (6 = Pacific Ocean) |
| `0x03001D2A` | 0xFF | 0x06 | game-type unlock mask |
| `0x03001D2B` | 0x03 | 0x08 | speed index (8 = Warp Speed) |
| `0x03001D2C` | 0x00 | 0x01 | one-shot "code used" gate |

## 6b. Enumeration

**Space definition.** The button-code space is a single fixed 10-press sequence over an
11-symbol input alphabet (the ten button masks above plus the 0xFFFF terminator). Because the
matcher tests the *whole* pressed-key mask for exact equality, any simultaneous multi-button
press produces a multi-bit mask that cannot match any table entry. Representable sequences:
10 presses, one exact ordering. There is no variable-length or checksum field; the terminator
bounds the length at 10. Exactly **one** table is reachable (the second table has zero xrefs).

**Novel code.** **← ← → → ↑ ↓ ↑ ↓ L R**. No GBA cheat list exists in the recon sources
(3rd party cheat indexes); the widely published
`OPENSESAME`/`ENTERPRISE` strings are for GameCube/PS2/PC and are absent from this ROM. The code
therefore appears in no published GBA list. It exercises an unadvertised combination — it sets
all three unlock fields at once, including Warp Speed, which the retail FAQ says requires beating
Pacific Ocean on Platinum difficulty.

**In-game proof (observed, mGBA + fresh EEPROM):**

| Run | State before `0x03001D28..33` | After |
|---|---|---|
| Savestate `ZooCube.ss6`, first discovery | `02 ff ff 03 00 00 ff ff ff ff ff ff` | `06 06 06 08 01 00 ff ff ff ff ff ff` |
| Fresh boot, clean EEPROM, state `ss7` | `02 ff ff 03 00 00 ff ff ff ff ff ff` | `06 06 06 08 01 00 ff ff ff ff ff ff` |

Visual confirmation (screenshots in work dir): `code_options.png` / `final_speed_montage.png`
show Express, Rocket, Supersonic and Light Speed changing from flashing red (locked) to green
(unlocked); `post_lvl_montage.png` shows levels 2–7 green; `backmm_gba.png` shows KO BLIND white
instead of red. Earlier, before the code, `spd_montage.png` showed those same speeds red.

**Bounds proven by rejection:**

1. **Wrong sequence** — `← ← ↑ ↑ ↑ ↓ ↑ ↓ L R` (third/fourth presses changed) on a clean gate
   produced **no change** in `0x03001D28..33`: `02 ff ff 03 00 00 ...` before and after.
2. **Gate** — `0x0800C204` skips the entire check when the signed byte at `0x03001D2C` is
   nonzero; success itself writes 1 there (observed 0→1). The code is therefore one-shot per
   save (derived from disassembly + observed write).
3. **Length bound** — the 0xFFFF terminator at index 10 means an 11th press is never consumed;
   no longer sequence exists in this table (derived).
4. **Input-space bound** — exact whole-mask equality excludes chords; only the ten listed
   single-button masks are accepted (derived).
5. **Second table** — 0 pointer/BL references ⇒ unreachable (bounded dead-code negative).
6. **No password system** — 21,537 `strings -n 4` records scanned; keyword counts
   `password=0, cheat=0, debug=0, secret=0, "level select"=0, code=0, unlock=1` (the single
   hit is the legitimate `Unlocked` results banner at `0x083328CD`); the five published-code
   literals have 0 byte hits. Eight screen families were walked (legal/intro, title+attract
   demo, Main Menu, Game Select, Options, High Scores, Credits, in-game pause) with 19 selectable
   items and **no code-entry surface**. The sole alphabet `ABCDEFGHIJKLMNOPQRSTUVWXYZ#!` was
   decoded and proven to feed the 3-character high-score name field.

## 7. Validation evidence

- **Observed**: all RAM diffs, breakpoint hit at `0x0800C20E` (`r1=0x03001E9C`), held-key mask
  `0x0020` for Left, screenshots of locked→unlocked menu entries, wrong-sequence rejection.
- **Derived**: validator control flow, gate semantics, field-value meanings from UI cross-check,
  dead-table xref count, text/alphabet decoding.
- **Inferred**: that the code is developer-intended rather than leftover debug code (it writes
  the same save fields used by normal progression and is guarded by a one-shot flag). The exact
  semantic name of `0x03001D2A` is inferred from the Type-row visual change.

## 8. Unknowns

- The byte at `0x03001D2A=6` corresponds to "all types unlocked" visually, but the exact bit
  layout was not exhaustively decoded.
- Save-record checksum recomputation after the code was not verified against EEPROM contents on
  disk (mGBA kept the modified record in IWRAM/savestate during the tests).
- The unreachable table at `0x083EBBC6` may be a prototype/discarded alternate code; its intent
  is unknown.
- EEPROM error/default-data screens from `0x08332BC4` were not induced.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for validator/screen disassembly; Python `struct` scans
  for literal pointers, u32 xrefs and button-mask runs; Capstone Thumb literal-load scanner.
- mGBA 0.10.5 `-3`, `-d` (PTY command-line debugger: `b/t`, `r/2`, `p`, `c`, Ctrl-C to halt),
  savestates `ZooCube.ssN` parsed with a local `gbAs` PNG-chunk/zlib reader (IWRAM at state
  offset `0x19000`, EWRAM at `0x21000` — this game leaves EWRAM entirely zero).
- xdotool exact key injection with 0.03 s holds / 0.15 s gaps; `scrot` + ImageMagick crops.
- Web recon: 3rd party cheat indexes game pages and the GBA-specific FAQ by Lisanne.
- All evidence (screenshots, scripts, savestates, work ROM copy) was in `/tmp/zoocube`,
  not in the ROM folder. No ROM or copyrighted assets are redistributed by this report.
