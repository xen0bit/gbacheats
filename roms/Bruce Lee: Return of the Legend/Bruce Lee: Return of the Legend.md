# Bruce Lee: Return of the Legend (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Bruce Lee: Return of the Legend/Bruce Lee: Return of the Legend.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `BRUCE LEE   ` |
| Game code | `ALEE` |
| Maker code | `7D` |
| Version | `0x00` |
| Entry word | `0xEA00002E` = stock ARM `b 0x080000C0` |
| Complement check | `0xF8` (valid: sum(0xA0..0xBD)+0x19 = 0 mod 256) |
| Stored header checksum | `0x0000` (should be `0x00F8`; zeroed field — the usual artifact of a rebuilt/patched header) |
| MD5 | `73d90562373b2b0882354986aabdd61f` |
| SHA-1 | `ebf28bfbf6932e386c261b28555294f183a08435` |
| SHA-256 | `ecfd25e7b6f9d5c5e2038a741e2df2ed96ee005363c2b89c0f372352ed2e4e8f` |

Embedded-header scan: exactly **one** Nintendo logo (file offset `0x04`), i.e. one GBA image, not
a multi-game pack. Entry `0x080000C0` is the stock crt0 (BIOS `swi`, IRQ setup, stack switch); the
first 4 KiB contains no cracktro/trainer strings (`CRC BANDIT`, `SUNHORS`, `Mode7`, `TRAINER`,
`crack` all absent). The only anomaly is the zeroed header checksum field, which is a header-level
artifact, **not** a gameplay patch or trainer.

The ROM text bank is stored as **lowercase ASCII** and rendered as capitals by the game
(`resume`, `level skip`, `director's cut`, …). A case-sensitive search for upper-case UI text
finds nothing; all searches below were run case-insensitively.

## 2. Executive summary

The game has **one developer-intended code system**: seven-press button sequences entered on the
**Select a Slot** screen while holding **L**. It is a fixed 12-entry lookup table, not a checksum
or password format.

All twelve sequences in the ROM table are the twelve codes that circulate publicly (Director's
Cut, Time Challenge, Gallery, the three outfits, Invincible, unlimited weapons, the three
enemy-set codes and random enemies). Every published literal was found verbatim in ROM at
`0x08028C98`, so the public lists are genuine for this SKU.

The system was fully reversed:

* recorder `0x08004658` (gated on L held),
* matcher `0x080044E0` (rotate 7-byte ring buffer, `strcmp` against 13 records),
* 12-way action dispatcher at `0x08004568`,
* records at RAM `0x020094C8` (12-byte stride) sourced from ROM `0x08028C98` (8-byte stride),
* settings/unlock byte `0x02008F34` (bits: DC, Time, Dragon, Gold, Bruce '73, Gallery).

The **whole space is enumerated**: input alphabet is the seven recordable symbols
`{u,d,l,r,R,L,s}`; a 7-symbol window gives `7^7 = 823,543` possible sequences and the table accepts
**exactly 12** of them. The matcher tests the *last seven* recorded symbols, so the accepted
language also contains arbitrary prefixes. That yields **novel accepted inputs that appear in no
published list**:

* `Up, Up, R, Select, R, Up, Select, Select` (8 presses) → Director's Cut, confirmed in mGBA;
* `Up, R, Select, R, Up, Select, Select, Down, Up, Down, R, R, Select, Left` (14 presses) →
  Director's Cut **and** Gallery at once (`0x02008F34 = 0x8D`), confirmed;
* all six unlock codes chained in one session → `0x02008F34 = 0xFF`, i.e. the exact state the
  published CodeBreaker code `32008F34 00FF` writes, reached with the game's own input only.

Bounds are proven by in-game rejection (short input, case-swapped R/Right, reversed sequence,
non-alphabet input), and the two extra strings in the ROM table are proven inert/unreachable.

No level-select, debug menu or hidden training room exists in this build: the tempting strings
`level skip`, `next section`, `next level`, `next...`, `slow motion`, `super jump`
(`0x08025B18`–`0x08025B54`) are **dead text**. The only text accessor is `get_string`
(`0x08002948`); its 41 call sites never request IDs 63–68, and no menu descriptor contains those
IDs. They are cut developer strings.

## 3. How to reproduce

Emulator: mGBA 0.10.5 SDL, `Xvfb :215` + `openbox`, `SDL_AUDIODRIVER=dummy`,
`mgba -3 "<rom>.gba"` (3× scale). Default mGBA SDL keymap:

| GBA | Key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Exact path:

1. Boot → info screen → title (`PUSH START`). Press **Start**.
2. **SELECT A SLOT** (`SLOT 1..4`, `ERASE`). This is the code-entry screen.
3. Hold **L** (`a`) and press the seven-symbol sequence (see §6). Presses are edge-triggered and
   recorded in the order pressed; the seven most recent recorded symbols are compared.
4. The effect is immediate (a jingle is audible on hardware; audio was dummy in this harness).
5. Press **A** on a slot → **SELECT MODE**; the unlocked modes are drawn bright, locked ones grey.
   **A** on a mode → **SELECT OUTFIT**; same brightness rule.

Sequence alphabet (the character each button records):

```
Up=u  Down=d  Left=l  Right=r  R-shoulder=R  L-shoulder=L  Select=s
A and B are NOT recorded (no handler feeds them to the recorder).
```

Savestate oracle: mGBA `.ssN` files are PNGs with a private `gbAs` chunk (zlib). After
decompression the layout is `VRAM 0x18000 | IWRAM 0x8000 | palette/OAM/IO 0x1000 | EWRAM 0x40000`;
EWRAM starts at file offset `0x21000`. Each test below is a RAM diff of
`0x02000000+0x21000+offset` between the pristine state and the state saved after entering a code.

## 4. Address map

### ROM

| ROM address | File offset | Meaning |
|---:|---:|---|
| `0x08001514` | `0x1514` | key update: `held = ~*(u16*)0x04000130`, stores held → `0x0200015C`, newly-pressed → `0x02000160` |
| `0x08002948` | `0x2948` | `get_string(id)`: `return ((u32*)0x08028940)[id]` |
| `0x08028C98` | `0x28C98` | **source cheat table**, 14 × 8-byte records (`7 chars + NUL`) |
| `0x08028940` | `0x28940` | 213-entry text-pointer table (base used by `get_string`) |
| `0x080044E0` | `0x44E0` | **matcher / unlock apply**: rotate ring, `strcmp` 13 records, dispatch |
| `0x08004568` | `0x4568` | action jump table, 12 words (types 1..12) |
| `0x08004658` | `0x4658` | **recorder**: L-gated append + call matcher |
| `0x0800243A..0x08002576` | — | the seven button handlers that call the recorder with `u,d,s,R,L,r,l` |
| `0x08025B18` | `0x25B18` | dead debug text block (`level skip`, …) |

### RAM

| Address | Meaning |
|---:|---|
| `0x0200005C` | pointer to cheat struct; observed `0x020094A4` |
| `0x020094A4 + 0x20` | ring write index (`0` after a complete sequence) |
| `0x020094A9..0x020094AF` | 7-byte ring buffer (`struct+5`) |
| `0x020094B1..0x020094B7` | rotated 7-byte compare buffer (`struct+0x0D`) |
| `0x020094C8` | 13 records, 12 bytes each: `{char seq[7]; u8 pad; u32 type}` |
| `0x02008F34` | settings/unlock byte (article pointer at global `0x020000A4`) |
| `0x020094B9` | unlimited weapons/ammo flag |
| `0x020094BA` | random-enemy flag |
| `0x020094BB` | invincible flag |
| `0x020094BC` | enemy-set selector byte (`0xE8` Jamal, `0xB8` Big Thug, `0x50` Texas) |
| `0x0200015C` / `0x02000160` | held / newly-pressed key state (active high) |

## 5. Algorithm

```
# key update, once per frame (0x08001514)
held   = (~*(u16*)0x04000130) & 0x3FF
pressed= held & ~prev_held
*(u32*)0x0200015C = held
*(u32*)0x02000160 = pressed
prev_held = held

# recorder, called by each button press handler (0x08004658)
if (held & 0x200) == 0:            # L must be held
    return
s = struct_at(0x0200005C)          # 0x020094A4
i = s->index                       # s+0x20
s->ring[i] = button_char           # s+5+i, chars: u d l r R L s
i = (i + 1) % 7
s->index = i
match_and_apply(s)                 # 0x080044E0, called after EVERY recorded press

# matcher (0x080044E0)
n = strlen(s->ring)                # 7 after the ring is full
for k in 0..6:
    s->rot[k] = s->ring[(s->index + k) % n]   # chronological window
for r in 0..12:
    if strcmp(s->rot, table[r].seq) == 0:
        t = table[r].type                    # 0 = no-op
        if 1 <= t <= 12:
            dispatch[t-1]()                  # 0x08004568
```

The comparison goes through the BIOS/libc trampoline at `0x08000218`; it is an exact,
case-sensitive `strcmp`. A code is therefore accepted iff the **last seven recorded symbols**
equal one of the twelve table strings. Because the recorder also records the L press itself, the
practical entry is `L` + seven symbols, and any extra presses before the seven are tolerated.

### Action dispatch (types 1..12)

| Type | Table string | Jump target | Effect |
|---:|---|---:|---|
| 1 | `RuRuRuR` | `0x08004598` | `struct+0x15 = 1`; mirrors to `0x020094B9 = 1` (unlimited weapons/ammo) |
| 2 | `rrrrrrr` | `0x080045B0` | enemy-set pointers; `0x020094BC = 0xE8` (Jamal) |
| 3 | `rlrlrlr` | `0x0800459E` | enemy-set pointers; `0x020094BC = 0xB8` (Big Thug) |
| 4 | `udlrudl` | `0x080045C4` | enemy-set pointers; `0x020094BC = 0x50` (Texas) |
| 5 | `uRsRuss` | `0x080045E4` | `0x02008F34 |= 0x01` (Director's Cut) |
| 6 | `uduRuds` | `0x080045F4` | `0x02008F34 |= 0x02` (Time Challenge) |
| 7 | `rddRRsl` | `0x08004604` | `0x02008F34 |= 0x40` (Bruce '73) |
| 8 | `rudRusl` | `0x08004614` | `0x02008F34 |= 0x10` (Dragon) |
| 9 | `ruuRRsl` | `0x08004624` | `0x02008F34 |= 0x20` (Gold) |
| 10 | `urdRRsl` | `0x080045D8` | `struct+0x16 = 1`; `0x020094BA = 1` (random enemies) |
| 11 | `ddRRuus` | `0x080045DE` | `struct+0x17 = 1`; `0x020094BB = 1` (invincible) |
| 12 | `dudRRsl` | `0x08004634` | `0x02008F34 |= 0x80` (Gallery) |

## 6. Tables

### 6.1 ROM source table `0x08028C98` (14 × 8 bytes)

```
0x08028C98  aaaaaaa  \0     (type 0 placeholder; A is not recorded -> unreachable)
0x08028CA0  bbaaaaa  \0     (initial value of the rotated buffer, not a table record)
0x08028CA8  rlrlrlr  \0     Big Thugs
0x08028CB0  rrrrrrr  \0     Jamal
0x08028CB8  udlrudl  \0     Texas
0x08028CC0  RuRuRuR  \0     unlimited weapons
0x08028CC8  uRsRuss  \0     Director's Cut
0x08028CD0  uduRuds  \0     Time Challenge
0x08028CD8  rddRRsl  \0     Bruce '73
0x08028CE0  rudRusl  \0     Dragon
0x08028CE8  ruuRRsl  \0     Gold
0x08028CF0  urdRRsl  \0     Random enemies
0x08028CF8  ddRRuus  \0     Invincible
0x08028D00  dudRRsl  \0     Gallery
```

The runtime record table at `0x020094C8` re-orders/shifts these into 13 records
(`aaaaaaa` type 0 followed by the 12 actions), i.e. the two strings at `0x08028C98`/`0x08028CA0`
are not action records.

### 6.2 `0x02008F34` unlock bits

| Bit | Value | Meaning | Initial |
|---:|---:|---|---|
| 0 | `0x01` | Director's Cut | clear |
| 1 | `0x02` | Time Challenge | clear |
| 2 | `0x04` | Easy | **set** |
| 3 | `0x08` | Normal | **set** |
| 4 | `0x10` | Dragon outfit | clear |
| 5 | `0x20` | Gold outfit | clear |
| 6 | `0x40` | Bruce '73 outfit | clear |
| 7 | `0x80` | Gallery | clear |

Initial value `0x0C`. Entering the six unlock codes yields `0xF3 | 0x0C = 0xFF`, exactly the
value written by the published CodeBreaker code `32008F34 00FF`.

### 6.3 Published list corrections

* "All Jamal Enemies: press Right six times" (ggmania) is **wrong** for this ROM: Right ×6
  leaves `0x020094BC = 0x00` (no effect); Right ×7 sets `0xE8`. The seven-press row is correct.
* All other published literals match the ROM table byte-for-byte.

## 6b. Enumeration

### Space and validator

* Alphabet: `{u, d, l, r, R, L, s}` — 7 symbols (Up, Down, Left, Right, R-shoulder,
  L-shoulder, Select). `A` and `B` never reach the recorder: the seven handlers call
  `0x08004658` with immediates `0x75,0x64,0x73,0x52,0x4c,0x72,0x6c` only.
* Window length: 7 symbols (the ring buffer is 7 bytes and `strcmp` compares seven characters).
* Representable 7-symbol space: **7^7 = 823,543**.
* Accepted set of 7-symbol strings: **exactly 12** (the type 1–12 rows above). The type-0 row
  `aaaaaaa` is not expressible (no `a`) and is a no-op even if reached.
* Because the matcher runs after every press, the accepted language is
  `Σ* · code` for each of the 12 codes: **any prefix is tolerated**, so the physical input
  language is infinite while the minimal codes are exactly the 12 rows.

This is a closed set, not a checksum format: there is no field, no checksum and no generator.
Enumerating all 823,543 seven-symbol strings against the 13-record `strcmp` table returns exactly
the 12 rows in §6.1 (derived directly from the ROM table and the matcher at `0x080044E0`).

### Novel accepted inputs (not on GameFAQs / VGChartz / TCRF / 53lu / TASVideos)

These are unpublished **input strings** that the game accepts; the *effects* they reach are the
published actions, because the table is closed.

| Novel input (Hold L, then press) | Length | Result (observed) | Evidence |
|---|---:|---|---|
| `Up, Up, R, Select, R, Up, Select, Select` | 8 | `0x02008F34` `0x0C→0x0D`; **Director's Cut** bright in Select Mode | `proof_novel8_mode.png` |
| `Up, R, Select, R, Up, Select, Select, Down, Up, Down, R, R, Select, Left` | 14 | `0x02008F34` `0x0C→0x8D`; **DC + Gallery** simultaneously | RAM diff `states/double_dc_gal.ss` |
| `DC, Time, Bruce '73, Dragon, Gold, Gallery` (six codes in one session) | 42 | `0x02008F34 = 0xFF`; all modes and all outfits bright | `proof_all_modes.png`, `proof_all_outfits.png`, RAM diff `states/all_unlocks.ss` |

The third row is the in-game equivalent of the published CodeBreaker "Unlock All Modes & Outfits"
memory write — produced without any memory edit.

### Bounds proven by rejection (all entered in mGBA, all left the target bytes unchanged)

| Rejected input | Reason | Observed |
|---|---|---|
| `Up, R, Select, R, Up, Select` (6 presses) | too short; window != any row | `0x02008F34 = 0x0C` |
| `Up, Right, Select, Right, Up, Select, Select` | case swap `R`↔`r`; `strcmp` is case-sensitive | `0x02008F34 = 0x0C`, DC grey in `proof_reject_mode.png` |
| `Select, Select, Up, R, Select, R, Up` (reversed DC) | not a row; no cyclic aliasing | `0x02008F34 = 0x0C` |
| `Right ×6` | Jamal needs seven | `0x020094BC = 0x00` |
| `B ×7` | `B` is not recorded; ring retains junk | `0x02008F34 = 0x0C`, `0x020094BC = 0x00` |
| `aaaaaaa` / `bbaaaaa` | `A`/`B` are never passed to the recorder | unreachable; `aaaaaaa` is type 0 (no-op) anyway |

## 7. Validation evidence

**Observed (emulator):**

* All 12 published sequences entered on Select a Slot; every one produced its documented byte:
  * `RuRuRuR` → `0x020094B9 = 0x01` (unlimited weapons)
  * `rrrrrrr` → `0x020094BC = 0xE8`
  * `rlrlrlr` → `0x020094BC = 0xB8`
  * `udlrudl` → `0x020094BC = 0x50`
  * `uRsRuss` → `0x02008F34 = 0x0D`
  * `uduRuds` → `0x02008F34 = 0x0E`
  * `rddRRsl` → `0x02008F34 = 0x4C`
  * `rudRusl` → `0x02008F34 = 0x1C`
  * `ruuRRsl` → `0x02008F34 = 0x2C`
  * `urdRRsl` → `0x020094BA = 0x01`
  * `ddRRuus` → `0x020094BB = 0x01`
  * `dudRRsl` → `0x02008F34 = 0x8C`
* Menus walked end-to-end: title → Select a Slot → Erase a Slot (`SLOT 1..4`, `RESET MEMORY`,
  `BACK`) → Select Mode → Select Outfit → intro/cutscene → gameplay → Game Paused
  (`RESUME`, `CONTROLS`, `MUSIC`, `SLEEP`, `QUIT`) → Select Controls (`KICK=R`, `PUNCH=B`,
  `BLOCK=L`, `JUMP=A`, `DEFAULT`, `DONE`) → Music on/off → Sleep (`PRESS R + L + SELECT TO WAKE`,
  wake combo verified). Select/B/R/L on Select a Slot do nothing; no hidden option surfaced.
* Gallery bit set correctly, but no Gallery entry appeared on the slot, mode or pause screens in
  this build.

**Derived (instruction sequence):** recorder gating on L, ring-buffer rotation, `strcmp` against
13 records, 12-way jump table, unlock-bit mapping, the closed 7-symbol/12-code enumeration.

**Inferred:** the enemy-set byte values `0xE8/0xB8/0x50` are taken to mean Jamal / Big Thug /
Texas because they are produced by the corresponding published codes; the exact spawn-table
pointers set by types 2–4 were not decoded. The Gallery bit's consumer was not located.

## 8. Unknowns

* The Gallery bit (`0x02008F34` bit 7) is set but no Gallery screen was reachable from the tested
  menus. It is either gated by a completed save / another flag, or the menu surface is cut.
* Types 2–4 set pointers at `struct+0x18/0x1C`; the enemy spawn tables behind them were not
  decoded beyond the selector byte.
* The three-line sleep message uses text IDs 13–15; the pause/controls/music screens build their
  labels through a path not fully traced (only the `get_string` path was needed for the negative
  result on IDs 63–68).
* `aaaaaaa` is a reachable-in-principle type-0 record, but A is not recordable; it is a no-op.
  `bbaaaaa` is buffer initialization, not a record.

## 9. Tooling

* mGBA 0.10.5 SDL (`/usr/games/mgba`) on `Xvfb :215` + `openbox`, `SDL_AUDIODRIVER=dummy`,
  driven by `xdotool`.
* mGBA `-d` command-line debugger over a Python `pty` (`dbgdrive.py`) for breakpoints and the
  key-update function; software watchpoints proved unusable because they freeze SDL input, so
  **savestate diffing** was the dynamic oracle.
* `savestate.py`-style parser: PNG `gbAs` chunk → `zlib.decompress` → EWRAM at `0x21000`.
* `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7 for BL/literal scans.
* Scripts and evidence in `/tmp/opencode/brucelee/`: `phase0.py`, `matrix.py`, `testcodes.py`,
  `testvariants.py`, `dbgdrive.py`, `states/*.ss`, and screenshots
  `proof_novel8_mode.png`, `proof_reject_mode.png`, `proof_all_modes.png`,
  `proof_all_outfits.png`, `w3_pause.png`, `w4_controls.png`, `w7_sleep.png`, `w7_wake.png`,
  `w8_erase.png`.

## 10. Legal note

No ROM, extracted graphics, music or game text is redistributed. Only hashes, addresses,
algorithms, field layouts and the analyst's own screenshots/notes are published. Published code
lists are cited as external evidence and were re-verified against this image; the memory-write
codes were **not** used to produce any result.
