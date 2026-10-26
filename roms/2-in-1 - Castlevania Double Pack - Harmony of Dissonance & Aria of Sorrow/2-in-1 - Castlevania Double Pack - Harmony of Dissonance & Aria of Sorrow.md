# 2-in-1: Castlevania Double Pack — Harmony of Dissonance & Aria of Sorrow (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `2-in-1 - Castlevania Double Pack - Harmony of Dissonance & Aria of Sorrow.gba` |
| Size | 16,777,216 bytes (`0x1000000`, 16 MiB) |
| Header title (`0xA0`) | `CV 2 PACK` |
| Game code (`0xAC`) | `BXKE` |
| Maker code (`0xB0`) | `41 34` (`"A4"`) |
| Fixed byte `0xB2` | `0x96` (valid) |
| Software version (`0xBC`) | `0x00` |
| Complement check (`0xBD`) | `0x88` — recomputed `0x88` (valid) |
| Header checksum (`0xBE`) | `0x0000` (not a normal retail value; the shell rewrote the header) |
| Entry branch (`0x00`) | `EA00002E` → `0x080000C0` |
| MD5 | `90d5887eaefd16478525478410155dec` |
| SHA-1 | `1ba25e80cfbc3d667a0f5d4cbeb295580f586edb` |
| SHA-256 | `0471c34b0e30321ec4f6a6711a6f5bf5ac3d088320141918a0ca213d59e29af8` |

### Cart layout (multi-game image)

A scan for the 156-byte Nintendo logo (`rom[4:0xA0]`) over the whole file returns **exactly one hit, at file offset 0x04**. There is no second GBA header: this is a *single* 16 MiB image (the "2 Games in 1" shell) whose first 0xC0 bytes are the pack header, followed by two complete 8 MiB game builds:

| File range | ROM address range | Content |
|---|---|---|
| `0x000000`–`0x7FFFFF` | `0x08000000`–`0x087FFFFF` | Pack shell + **Harmony of Dissonance** build (`CASTLEVANIA1.00`) |
| `0x800000`–`0xFFFFFF` | `0x08800000`–`0x08FFFFFF` | **Aria of Sorrow** build (`CASTLEVANIA2-010`), header stripped |

Evidence:

* HoD build banner `CASTLEVANIA1.00` at `0x5140A4` (immediately after the pointer slot `0x085140A0` → `0x02000000`).
* AoS build banner `CASTLEVANIA2-010` at `0xCF0A18` (immediately after the pointer slot `0x08CF0A14` → `0x02000000`).
* AoS code begins at file `0x800000` with the ARM startup sequence `12 00 A0 E3 / 00 F0 29 E1 …`, i.e. the AoS header area was removed and the image rebased to `0x08800000`. All AoS absolute pointers are already `0x08xxxxxx` values (verified: `0x088E0AE4` is referenced by a literal at `0xCF0B3C`).
* The file is padded to a full 16 MiB. The last data in the HoD half ends around `0x73FFFF`; `0x740000`–`0x7FFFFF` is `0xFF` padding (low entropy ≈1.3).

Every game-scoped address below is either a **file offset** (hex) or a **ROM address** (`0x08…`); the conversion is `rom_addr = 0x08000000 + file_offset`.

## 2. Executive summary

Both halves keep the retail **name-entry cheat system** and the **Konami-logo button code**. Nothing here is a GameShark/memory cheat: every code below is entered through the game's own menus or boot screen.

| Half | Accepted names (exact, 8 glyphs) | Effect |
|---|---|---|
| HoD | `HARDGAME` | Hard mode: `0x02000314 |= 0x40000000` |
| HoD | `NO MAGIC` (space is a real `0x00`) | Five spell books disabled: `0x02000330 |= 0x1F000000` |
| HoD | `MAXIM` (NUL-padded) | Maxim mode: `0x02000081 = 0xFF` |
| AoS | `JULIUS` (NUL-padded) | Julius mode: `0x02013266 = 1` |
| AoS | `NOUSE` | Item use disabled: `0x02000344 |= 0x00100000` |
| AoS | `NOSOUL` | Souls disabled: `0x02000344 |= 0x00200000` |

All six were exercised in mGBA and their exact flag writes observed (§7). Invalid 8-glyph names (`HARDGAMX`, `JULIUSX`) are copied into the save-state name field but set **no** flag — the comparison is a fixed 8-byte table lookup, not a prefix match.

**Names are not stored as ASCII.** The glyph encoding is `code = ASCII − 0x3F` (`A`=0x02 … `Z`=0x1B, space = 0x00). That is why `strings`/`grep` for `HARDGAME` finds nothing and why the system initially looked absent.

| Half | Table (3 × 8 bytes) | Validator |
|---|---|---|
| HoD | `0x08143C48` | `0x08084F60` gate, compares at `0x08084F86` / `0x08084FEA` / `0x08085010` |
| AoS | `0x088E0CCC` | `0x08808480` gate, compares at `0x088084A2` / `0x088084F0` / `0x08808528` |

**The gate (the important new result).** Both validators are gated. The gate is a **save-file field**, not a debug leftover:

* **HoD** — the settings block at **SRAM `0x0E000BF8`** (0x4C bytes, validity bit 3 of `0x0E00000F`) is copied into EWRAM **`0x0200035C`** by the function at `0x0808BA58`. Bits 0–5 of `0x0200035C` are the gate. On a virgin save the byte is `0x00` and every name code (and the Konami code) is silently skipped; with `0x0BF8 = 0x01` in the `.sav`, the gate reads `0x01` at boot and all three HoD codes work with **no runtime patching**. This was observed end-to-end.
* **AoS** — the slot loader at `0x08812684` copies 0x190 bytes from slot `+0x000` to EWRAM `0x02000040`, so gate byte `0x02000060` = **save slot `+0x20`**, slot base `0x0E004010 + slot × 0x47C`. This mapping is derived from the disassembly; the AoS tests wrote the gate byte at runtime because no real slot was available.

In player terms: the gate bytes are permanent-progress flags written by the game as the save records milestones (public guides: clear the regular game once, then start a new game). The practical prerequisite is a **progressed save**, not a debug build.

**Konami code** — both halves contain the identical 10×u16 table `Up, Up, Down, Down, Left, Right, Left, Right, B, A` (`0x08143BD8`, `0x088E0BAC`). The progress counter is only armed (`=1`) when the gate is non-zero (`0x08081F2E`); each matching held-key mask advances it, and at 11 the game plays its confirmation sound (HoD SE 27, AoS sound 428). Both were driven in-emulator and the counter observed stepping 1→11, with the success call observed at `0x08082066` (r0=27) and `0x08802A78` (r0=0x1AC).

**Enumeration result (§6b).** These are fixed-string lookup systems, not generators. Each half accepts **exactly three** names (the table rows); there is no fourth comparison and no checksum/field space to explore. A name not equal to one of the three rows is ignored. Consequently there is no "novel accepted code" to mint, and that is proven by the table bounds plus the rejected inputs, not merely asserted.

**Debug leftovers.** Both halves contain complete debug string banks and menu tables (HoD stage select / sound test / `TEST_VIEW`; AoS `OBJTEST`/`SDTEST`/`ENEMY`/`VOICE`/`VRAM HIT TEST`/`LINK TEST` and the `Enter "JULIUS"` hint), and the pack shell ignores Select/Start/L/R. No in-game input path into those screens was found; they are not part of the player-reachable cheat set.

## 3. How to reproduce

### Emulator and keys

```bash
Xvfb :105 -screen 0 1024x768x24 &
DISPLAY=:105 openbox &
DISPLAY=:105 SDL_AUDIODRIVER=dummy mgba -3 "<rom>.gba"
```

mGBA 0.10.5 SDL default keymap: **A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`, D-pad = arrows**. Hold keys 100–300 ms; menus debounce.

### Satisfying the gate

* **HoD:** in the `.sav`, `0x0BF8 = 0x01` (settings byte; ensure bit 3 of `0x0F` is clear). Boot, select Harmony, and the gate is live from SRAM with no emulator patch.
* **AoS:** a saved slot whose byte `+0x20` has bit 0 set. For analysis we wrote `0x02000060 = 0x01` after the slot screen; the validator then run normally. (A completed AoS save is the intended in-game route.)

### Harmony of Dissonance

Shell → `A` on Harmony → title → `Start` → file menu → `Select data` → `DATA1` → `NEW GAME` → **Name Entry**.
The name screen is a 9-column keyboard: rows `A–I`, `J–R`, `S–Z &`; bottom row `. - ' ! ★ © DEL OK`. Vertical navigation goes one *row* per press: from `A` press `Down` three times to reach the bottom row, then `Right` eight times to `OK`.
Names are up to 8 glyphs; `DEL` erases; `R` inserts the `0x00` used by `NO MAGIC`.

### Aria of Sorrow

Shell → `Right` + `A` → title → `Start` → `GAME START` → `Select Data` → `NEW GAME` → **Name Entry**.
Keyboard rows `A–I`, `J–R`, `S–Z @`; bottom `. - ' ! | ? + DEL OK` (same `Down`×3, `Right`×8 to `OK`).

### Konami code

At the **white/orange KONAMI logo** after "Licensed by Nintendo" (not the pack's red banner), tap the sequence with short presses. The validator compares the *held* key mask and keeps progress while no key is held; holding a button for three or more frames advances twice and then resets.

## 4. Address map

### Harmony of Dissonance (base `0x08000000`)

| Address | File offset | Meaning |
|---|---|---|
| `0x08143C48` | `0x143C48` | `MAXIM` (`0E 02 19 0A 0E 00 00 00`) |
| `0x08143C50` | `0x143C50` | `NO\0MAGIC` (`0F 10 00 0E 02 08 0A 04`) |
| `0x08143C58` | `0x143C58` | `HARDGAME` (`09 02 13 05 08 02 0E 06`) |
| `0x08143BD8` | `0x143BD8` | Konami table, 10 × u16 |
| `0x08084F60` | `0x084F60` | name-code gate: `(state[0x35C] & 0x3F) != 0 && ctx[11] == 0` |
| `0x08084F86` | `0x084F86` | 8-byte compare vs `MAXIM` |
| `0x08084FA8` | `0x084FA8` | MAXIM accept: `state[0x81]=0xFF`, SE `0x148` |
| `0x08084FEA` | `0x084FEA` | literal load of `HARDGAME` table |
| `0x08085010` | `0x085010` | literal load of `NO MAGIC` table |
| `0x08085030` | `0x085030` | NO MAGIC accept: `state[0x330] \|= 0x1F000000`, SE `0x92` |
| `0x08085062` | `0x085062` | HARDGAME accept: `state[0x314] \|= 0x40000000`, SE `0x130` |
| `0x0808507C` | `0x08507C` | common tail: `bl 0x0813B054` (sound driver) |
| `0x08081F2E` | `0x081F2E` | Konami arm: progress `= 1` only if `state[0x35C] & 0x3F` |
| `0x08081FDC` | `0x081FDC` | Konami validator loop |
| `0x08082066` | `0x082066` | Konami success: `movs r0,#27; bl 0x0813B054` |
| `0x0808BA58` | `0x08BA58` | **gate loader**: SRAM `0x0E000BF8` → `state+0x35C` (0x4C bytes) |
| `0x0808BA2C` | `0x08BA2C` | **gate saver**: `state+0x35C` → SRAM `0x0E000BF8` |
| `0x080AEA86` | `0x0AEA86` | gate-bit writer (sets bit 1 and clears bit 6 during a story/clear event) |
| `0x08080E74` | `0x080E74` | save signature check (`"CASTLEVANIA1.00"`) |
| `0x08080EC4` / `0x08080F04` / `0x08080F44` | `0x080EC4`… | set / clear / test bit in SRAM `0x0E00000F` |
| `0x0808B62C` | `0x08B62C` | save-slot loader: SRAM slot → `state+0x78`, `state+0x8C`, `state+0x18770` |
| `0x0813B054` | `0x13B054` | SE/music driver (`r0` = id ≤ 0x3FF) |
| `0x085140A0` | `0x5140A0` | pointer slot → EWRAM `0x02000000` |

RAM (EWRAM, base `0x02000000`):

| Address | Meaning |
|---|---|
| `0x02000010` | Konami progress (0 → 11, then `0xFF`) |
| `0x02000016` | held key mask (A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200) |
| `0x02000020` | on-screen name buffer, 8 glyph codes |
| `0x02000078` | name copied on OK, 8 bytes |
| `0x02000081` | Maxim flag (`0xFF`) |
| `0x02000314` | bit 30 = Hard mode |
| `0x02000330` | bits 24–28 = five spell books disabled |
| `0x0200035C` | gate byte (bits 0–5) = mirror of SRAM `0x0E000BF8` |

Save (SRAM `0x0E000000`, 16 KiB region used by HoD):

| Field | Meaning |
|---|---|
| `0x0E000000` | signature `CASTLEVANIA1.00` (15 bytes) |
| `0x0E00000F` | validity bitfield; bit 3 clear = settings block valid |
| `0x0E000BF8` | **settings/permanent-flags block, 0x4C bytes**; byte 0 bits 0–5 = cheat gate |
| `0x0E000010 + slot×0x3F8` | save slot records |

### Aria of Sorrow (base `0x08800000`)

| Address | File offset | Meaning |
|---|---|---|
| `0x088E0CCC` | `0x8E0CCC` | `JULIUS` (`0B 16 0D 0A 16 14 00 00`) |
| `0x088E0CD4` | `0x8E0CD4` | `NOUSE` (`0F 10 16 14 06 00 00 00`) |
| `0x088E0CDC` | `0x8E0CDC` | `NOSOUL` (`0F 10 14 10 16 0D 00 00`) |
| `0x088E0BAC` | `0x8E0BAC` | Konami table, 10 × u16 |
| `0x08808480` | `0x808480` | name-code gate: `(state[0x60] & 1) != 0 && ctx[11] == 0` |
| `0x088084A2` | `0x8084A2` | 8-byte compare vs `JULIUS` |
| `0x088084C6` | `0x8084C6` | JULIUS accept: SE `0x1E5`, `state[0x13266] = 1` |
| `0x088084F0` | `0x8084F0` | 8-byte compare vs `NOSOUL` |
| `0x08808528` | `0x808528` | 8-byte compare vs `NOUSE` |
| `0x0880854C` | `0x80854C` | NOUSE accept: SE `0x1B5`, `state[0x344] \|= 0x00100000` |
| `0x08808564` | `0x808564` | NOSOUL accept: SE `0x199`, `state[0x344] \|= 0x00200000` |
| `0x0880857C` | `0x80857C` | `bl 0x088D7810` (sound driver) |
| `0x08802884` | `0x802884` | Konami validator loop |
| `0x08802A78` | `0x802A78` | Konami success: sound `428` |
| `0x08812684` | `0x812684` | **slot loader**: SRAM slot `+0x000` → `state+0x40` (0x190 bytes) |
| `0x08800FD4` | `0x800FD4` | save signature check (`"CASTLEVANIA2-010"`) |
| `0x08CF0A14` | `0xCF0A14` | pointer slot → EWRAM `0x02000000` |
| `0x088E1E54` | `0x8E1E54` | debug menu string/struct block (`OBJTEST`, `SDTEST`, `ENEMY`, `VOICE`, …) |
| `0x088F8B72` | `0x8F8B72` | debug text bank incl. `Enter "JULIUS"` |

RAM (EWRAM, base `0x02000000`) and save (SRAM `0x0E004000`, region shared with HoD in the same 32 KiB `.sav`):

| Address | Meaning |
|---|---|
| `0x02000016` | held key mask |
| `0x02000060` | gate byte (bit 0) = save slot `+0x20` |
| `0x02000094` | name copied on OK, 8 bytes |
| `0x02000344` | bits 20/21 = items disabled / souls disabled |
| `0x0200A075` | Konami progress |
| `0x02013266` | Julius flag (1) |
| SRAM `0x0E004000` | signature `CASTLEVANIA2-010` |
| SRAM `0x0E004010 + slot×0x47C` | save slot; byte `+0x20` bit 0 = gate |

## 5. Algorithm

### 5.1 Gate loading (what a player must have)

```
HoD, at boot / save-system init:
    if signature(0x0E000000) != "CASTLEVANIA1.00": format/zero
    if bit3(0x0E00000F) != 0: skip                 # 0 = settings valid
    memcpy(state+0x35C, 0x0E000BF8, 0x4C)          # via 0x0808BA58
    # gate = state[0x35C] & 0x3F

AoS, when a save slot is loaded:
    slot_base = 0x0E004010 + slot*0x47C
    memcpy(state+0x40, slot_base+0x000, 0x190)     # via 0x08812684
    # gate = state[0x60] & 1  ==  slot_base[0x20] & 1
```

`0x0808BA2C`-side saving mirrors `state+0x35C` back to `0x0E000BF8`; `0x080AEA86` sets bit 1 of the byte during a story/clear event. On a virgin cart both fields are zero, which is why the codes are inert until the save has recorded progress.

### 5.2 Name-entry codes

```
on OK:
    state = *(u32*)POINTER_SLOT          # 0x085140A0 / 0x08CF0A14
    copy 8 bytes of the entry buffer -> state + NAME_OFF   # HoD 0x78, AoS 0x94

    if (state[GATE_OFF] & GATE_MASK) == 0:  goto play_sound(default); return
    if ctx[11] != 0:                        goto play_sound(default); return

    for each 8-byte row E in TABLE:
        if memcmp8(state + NAME_OFF, E) == 0:
            apply(E.action); play_sound(E.se_id); return
    play_sound(default); return
```

Per-row action (observed writes):

| Game | Name | Effect | Sound |
|---|---|---|---|
| HoD | `MAXIM` | `*(u8*)(state+0x81) = 0xFF`; `bl 0x0808510C` | `0x148` |
| HoD | `HARDGAME` | `*(u32*)(state+0x314) \|= 0x40000000` | `0x130` |
| HoD | `NO MAGIC` | `*(u32*)(state+0x330) \|= 0x1F000000` (bits 24–28) | `0x92` |
| AoS | `JULIUS` | `*(u8*)(state+0x13266) = 1` | `0x1E5` |
| AoS | `NOUSE` | `*(u32*)(state+0x344) \|= 0x00100000` | `0x1B5` |
| AoS | `NOSOUL` | `*(u32*)(state+0x344) \|= 0x00200000` | `0x199` |

`MAXIM`/`JULIUS`/`NOUSE`/`NOSOUL` rows are NUL-padded; the compare is a full 8 bytes, so trailing positions must be empty. `NO MAGIC` contains a literal `0x00` between `NO` and `MAGIC`; the keyboard inserts it with **R**.

### 5.3 Konami code

```
progress = state[PROG_OFF]          # HoD 0x10, AoS 0xA075
key      = *(u16*)(state + 0x16)    # active-high held-key mask

if (u8)(progress - 1) > 9:  goto after
if key == TABLE[progress - 1]: progress += 1
else if key != 0:              progress = 0
state[PROG_OFF] = progress

after:
    if progress == 11: play_sound(SUCCESS_ID)   # HoD 27, AoS 428
                       state[PROG_OFF] = 0xFF
```

The progress counter is armed to `1` when the logo state starts **only if the gate is non-zero** (HoD `0x08081F2E`; the AoS state-machine setup is analogous but was not separately located); otherwise it stays 0 and `(progress−1) > 9` skips every comparison.

## 6. Tables

### 6.1 Name-code tables (`ASCII − 0x3F`, space = 0x00)

```
HoD  0x08143C48:  0E 02 19 0A 0E 00 00 00     M A X I M
     0x08143C50:  0F 10 00 0E 02 08 0A 04     N O _ M A G I C
     0x08143C58:  09 02 13 05 08 02 0E 06     H A R D G A M E

AoS  0x088E0CCC:  0B 16 0D 0A 16 14 00 00     J U L I U S
     0x088E0CD4:  0F 10 16 14 06 00 00 00     N O U S E
     0x088E0CDC:  0F 10 14 10 16 0D 00 00     N O S O U L
```

Glyph codes: `A`=02, `B`=03 … `Z`=1B (`code = ASCII − 0x3F`); space = 00.

### 6.2 Konami table (10 × u16, little-endian)

```
0x08143BD8 / 0x088E0BAC:
  0040 0040 0080 0080 0020 0010 0020 0010 0002 0001
  Up   Up   Down Down Left Right Left Right B    A
```

Key masks: `A=0x01 B=0x02 Select=0x04 Start=0x08 Right=0x10 Left=0x20 Up=0x40 Down=0x80 R=0x100 L=0x200` (active-high held state).

### 6.3 Mode flags

| Word | Bit | Meaning | Confidence |
|---|---|---|---|
| HoD `0x02000314` | 30 | Hard mode | Observed |
| HoD `0x02000330` | 24–28 | Spell books 1–5 disabled | Observed |
| HoD `0x02000081` | byte | Maxim mode | Observed |
| AoS `0x02013266` | byte | Julius mode | Observed |
| AoS `0x02000344` | 20 / 21 | Items disabled / souls disabled | Observed |
| HoD `0x0200035C` | 0–5 | gate, mirror of SRAM `0x0E000BF8[0]` | Observed |
| AoS `0x02000060` | 0 | gate, save slot `+0x20` bit 0 | Derived |

## 6b. Enumeration

| Property | Harmony of Dissonance | Aria of Sorrow |
|---|---|---|
| System type | fixed 8-byte string lookup | fixed 8-byte string lookup |
| Input alphabet | 27 glyphs (`A–Z`,`&`) + punctuation; 8 positions | 27 glyphs (`A–Z`,`@`) + punctuation; 8 positions |
| Nominal input space | ~28^8, but irrelevant: no transform/checksum | same |
| **Effective accepted space** | **exactly 3 values** (table rows at `0x08143C48`) | **exactly 3 values** (table rows at `0x088E0CCC`) |
| Table terminator | none; exactly three 8-byte compares in the validator; the bytes after the third row (`0x143C60: 02 02 04 02 …`) are unrelated data | none; exactly three compares; bytes after `0x8E0CE4` are unrelated |
| Rejected bounds | `HARDGAMX` copied to `0x02000078`, no flag set; all other non-table names fall through | `JULIUSX` copied to `0x02000094`, no flag set |
| Novel codes | none exist by construction: the space is a 3-entry lookup, not a generator. A value not equal to a row cannot be accepted. | same |
| Gate condition | SRAM `0x0E000BF8[0] & 0x3F != 0` (progressed save) | SRAM slot `+0x20 & 1` (progressed save slot) |
| Rejection proof | observed (no flag, name still copied) | observed |

Because both systems are lookups with a fixed 8-byte comparison, "enumeration" means enumerating the table, and the bounds are demonstrated by a rejected 8-glyph input in each half. There is no checksum, field packing, or generator to expand beyond the three documented names.

## 7. Validation evidence

### Observed (emulator + memory reads)

**HoD gate and codes (natural gate from the patched `.sav`, no runtime gate write):**
* `.sav` `0x0BF8 = 0x01` → after boot, EWRAM `0x0200035C = 0x01` (read). SRAM `0x0E000BF8 = 0x01`.
* `HARDGAME` (written to the live name buffer `0x02000020`, displayed by the game) → OK → `0x02000078 = 09 02 13 05 08 02 0E 06`, `0x02000314 = 0x40000000`.
* `MAXIM` → `0x02000081 = 0xFF`, name `0x02000078 = 0E 02 19 0A 0E 00 00 00`.
* `NO MAGIC` → `0x02000330 = 0x1F000000`, name `0x02000078 = 0F 10 00 0E 02 08 0A 04`.
* `HARDGAMX` → name copied to `0x02000078 = 09 02 13 05 08 02 0E 19`, but `0x02000314 = 0`, `0x02000330 = 0`, `0x02000081 = 0` (no flag, no mode change).

**AoS codes (gate byte written to `0x02000060 = 1` because no real slot was available):**
* `JULIUS` → name `0x02000094 = 0B 16 0D 0A 16 14 00 00`, `0x02013266 = 0x00000001`.
* `NOUSE` → name `0x02000094 = 0F 10 16 14 06 00 00 00`, `0x02000344 = 0x00100000`.
* `NOSOUL` → name `0x02000094 = 0F 10 14 10 16 0D 00 00`, `0x02000344 = 0x00200000`.
* `JULIUSX` → name `0x02000094 = 0B 16 0D 0A 16 14 19 00`, `0x02013266 = 0`, `0x02000344 = 0`.
* Screenshots show the AoS name field rendering `JULIUS` from the buffer before OK, and the AoS Select Data preview likewise.

**Konami code, both halves (frame-stepped with controlled key masks, gate armed):**
* HoD: at the logo, progress read `1`; injecting `40 40 80 80 20 10 20 10 02 01` advanced it `2,3,4,5,6,7,8,9,10,11`; forcing the logo timer to expire hit `0x08082066` with `r0 = 0x1B` (27) — the SE call.
* AoS: same procedure at `0x0880288E`; progress `1 → 11`; success stop at `0x08802A78` with `r0 = 0x1AC` (428).
* With the natural HoD gate, the logo state arms progress to `1` by itself (`0x02000010 = 0x01` read at the logo).
* The confirmation **sound call** is observed at the driver entry; audio was not captured (`SDL_AUDIODRIVER=dummy`).

**Menus observed:** pack shell (two game choices; Select/Start/L/R do nothing); HoD title, file menu (`Select data`, `Change name`, `Copy data`, `Delete data`), slot screen (`DATA1/2/3`, `NEW GAME`), name entry; AoS title (`GAME START`, `SOUL-TRADE`), `Select Data`/`Copy Data`/`Delete Data`, slot screen with preview, name entry.

### Derived (disassembly)

* HoD gate loader/saver `0x0808BA58` / `0x0808BA2C`: signature check, settings-validity bit 3 of `0x0E00000F`, 0x4C-byte copy to/from `state+0x35C` and SRAM `0x0E000BF8`.
* AoS slot loader `0x08812684`: slot stride `0x47C`, base `0x0E004010`, 0x190-byte copy to `state+0x40`; therefore `0x02000060` = slot `+0x20`.
* Both validators: exactly three 8-byte compares, then flag writes and a sound call; gate checks at the top.
* Konami arm (`0x08081F2E`) and loop (`0x08081FDC` / `0x08802884`); success handling at `0x08082066` / `0x08802A78`.

### Inferred

* The individual meanings of gate bits 0–5 (HoD) and slot `+0x20` bit 0 (AoS) are not isolated; `0x080AEA86` sets bit 1 during a story/clear event, and public guides describe the prerequisite as "complete the game once". The practical rule is: a progressed save.
* HoD's `MAXIM` is documented as requiring a completed game; our observation is consistent (the gate is part of the same progressed-save data).
* The Simon Belmont effect of the HoD Konami code is documented but was not reached, because Boss Rush is not available on the available save; only the code path (SE 27) was observed.

## 8. Unknowns

* **Exact milestone semantics of the gate bits.** The byte is proven to be the gate and to come from the save (`0x0E000BF8` / slot `+0x20`), but which specific clear/ending event sets each of bits 0–5 was not isolated. `0x080AEA86` is one writer (sets bit 1); the others were not exercised.
* **AoS gate not loaded from a real slot.** The slot `+0x20` mapping is derived from the loader; the AoS code tests used a runtime write of `0x02000060`. Producing a real progressed AoS save and repeating the tests through CONTINUE is the remaining confirmation.
* **Simon Belmont / Boss Rush.** Boss Rush is gated behind a completed save; the HoD Konami success was observed, but the subsequent Simon effect was not.
* **Debug menus.** Strings and tables exist in both halves, but no reachable input path was found; whether a hidden trigger exists in another revision was not proven either way.
* **Audio confirmation.** The sound-driver calls and IDs were observed; actual audio output was not captured under the dummy audio driver.
* **Downstream visual effects.** The mode flags were observed being written (the game's own effect), but the resulting gameplay was not played out: Julius's sprite/moveset after the shared intro, and the no-item/no-soul restrictions in normal play, are derived from the flags and their readers, not from a completed playthrough.

## 9. Tooling

* `mgba 0.10.5` (Debian `mgba-sdl`) under `Xvfb :105` + `openbox`, `SDL_AUDIODRIVER=dummy`, 3× scale.
* `xdotool` for input, ImageMagick `import`/`convert` for 720×480 screenshots, `tesseract 5.5.0` for menu OCR.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`; Capstone 5 for scripted decode.
* `gdb-multiarch` and a custom minimal GDB-RSP client (`rsp.py`) over mGBA's stub (`mgba -g`, port 2345): memory read/write, register read/write (`P` packets, little-endian values), breakpoints, single-frame continue.
* Custom scripts in `/tmp/opencode/cv`: `phase0.py` (hashes/header/logo scan), `rsp.py`, `nav.py`/`nav2.py` (xdotool + OCR), `run3.py` (boot → name entry → code test), `konami6/7.py` and `konami_aos.py` (frame-stepped Konami sequence), `dumpall.py` (chunked RAM dumps).
* Public sources consulted for code lists: vgmuseum `code-hod.htm`, castlevaniadungeon `hod/secrets.htm`, CBR "Castlevania Advance Collection Name Entry Screen Cheat Codes", IGN/GameFAQs snippets for AoS. Every published code was verified against the ROM in its encoded form and then in the emulator.

## 10. Legal note

No ROM, graphics, music or game text is redistributed with this report. Only hashes, addresses, algorithms and the short cheat names (functional interface strings) are published.
