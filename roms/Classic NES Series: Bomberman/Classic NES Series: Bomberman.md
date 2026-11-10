# Classic NES Series: Bomberman (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Classic NES Series: Bomberman/Classic NES Series: Bomberman.gba` |
| Size | 1,048,576 bytes (`0x100000`) |
| Header title | `BOMBER MAN` (`0xA0`–`0xAB`) |
| Game code | `FBME` (`0xAC`–`0xAF`) |
| Maker | `01` (`0xB0`–`0xB1`) |
| Version | `0x00` (`0xBC`) |
| Header complement | `0x23`; stored header checksum `0x0000` |
| Calculated header checksum | `0x003C` (does not match stored `0x0000`) |
| Entry word | `0xEA000031` → ARM branch to `0x080000CC` |
| MD5 | `e674bef244d677e175f5694a7006bfde` |
| SHA-1 | `741eb2874c526cc014bf3e642b4ee37f18312735` |
| SHA-256 | `9ea8196d7bffbdbe540270255a53973376112ce9cff929926b52f0110d610cd2` |

Phase 0 notes:

* Exactly one 156-byte Nintendo logo occurs, at file offset `0x4`. There is no second GBA header, so this is a single-image cart, not a multi-game pack.
* The header has been rebuilt: the stored checksum is `0x0000`, the complement is `0x23`, and the entry branches to `0x080000CC` rather than the usual `0x080000C0`. Bytes at `0x080000C0` are `03 24 13 07 42 4F 4D 42 45 52 5F 31` (`....BOMBER_1`), then ARM code at `0x080000CC`. This is a wrapper boot/save signature, not a scene cracktro.
* No trainer, cracktro, or appended trainer menu was found. The first 4 KiB contains the wrapper boot stub and normal ARM/Thumb code.
* The ROM is an **emulated NES game**. The NES PRG (16 KiB) and CHR (8 KiB) are materialised in GBA EWRAM at `0x02000000` / `0x02004000` at runtime. The NES PRG in the GBA ROM is stored in a wrapper-encoded form; the runtime image was taken from an mGBA savestate and is the ground truth used here. The runtime PRG contains a wrapper patch byte `0x42` at 42 sites; the password validator works in the live GBA, so the wrapper's CPU core handles those bytes. For offline disassembly the `0x42` bytes were treated as NOPs; the one site needed by the password path (`$DB7A`) was restored to `LDX #$00` from context.

## 2. Executive summary

The only in-game cheat surface in this ROM is the **NES Bomberman password system**. There is no NES button-code cheat, no NES debug menu, and no wrapper save-state/debug menu. The wrapper does have a separate L+R pause/system-menu state and a Start+Select+A+B reset (below); neither contains a hidden cheat.

* The password screen is reached from the title: **Select** toggles the `CONTINUE` selection, **Start** enters the screen. It displays `ENTER:SECRET:CODE`.
* A password is 20 symbols. The on-screen alphabet is `A`–`P`, but the game maps each typed letter through a fixed 16-entry permutation, then applies a chained nibble transform and four 4-bit checks.
* The validator was located at NES `$DB7A`–`$DBD0`. It is a checksum-only validator: it does not range-check the level or the score/ability fields. The NES level byte is 8 bits, `(w[17]<<4)|w[2]`.
* All 64 unique 20-symbol strings scraped from the archived GameFAQs page satisfy the recovered validator. Two representative published codes were entered live; both started the expected stage.
* Two codes that appear in **no published list** were generated, entered and verified on the live GBA:
  * `NMOLBODOLJGGCPODJABL` → `STAGE 51`, NES `$58 = 0x33`.
  * `BOCPOLABOLHIMNPCGEKH` → `STAGE 76`, NES `$58 = 0x4C`. This also corrects the published list: the code labelled “Level 76” (and “Level 74”) is a duplicate that actually starts stage 74.
* Bounds were proven by rejection: the checksum-valid-symbol string `AAAAAAAAAAAAAAAAAAAA` (all valid symbols, bad checksums) returns to the password entry screen and leaves `$58 = 0`; no stage starts.
* The wrapper has a **pause / system-menu state**: holding **L+R** freezes the emulated NES (the NES frame counter `$33` stops); pressing any of A/B/Start/Select/Up/Down resumes it. The menu's own text is drawn on GBA-native layers and is not present in the NES nametable. The documented reset combination **Start + Select + A + B** performs a soft reset of the emulated NES (title returns, `$58=0`, `$5F=0`). No separate save-state screen was found; the SRAM contains only a 512-byte `0xFF` block with the signature `BMOB` + `07 13 24 03` at `0xFC`.

## 3. How to reproduce

### Emulator and keymap

* mGBA 0.10.5 (SDL frontend, `/usr/games/mgba`) under `Xvfb :246`, `SDL_AUDIODRIVER=dummy`.
* Keymap used: **A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys**.

### Menu path

1. Boot. The title screen is the NES Bomberman title, with a cursor before `START` and a second entry `CONTINUE`.
2. Press **Select** once. The cursor moves from `START` to `CONTINUE` (NES `$5F` becomes `1`).
3. Press **Start**. The screen changes to `ENTER:SECRET:CODE` with a blinking cursor.
4. Enter 20 symbols. **Left/Right** changes the current symbol; **A** commits it and advances. After the 20th symbol the validator runs.
5. Success starts the stage and the screen shows `STAGE n`. Failure returns to `ENTER:SECRET:CODE` with the cursor at `$1F = 6`, `$20 = 0x3A`.

### Reliable input pacing

The NES entry loop polls `$12` every frame and does not require a release edge, so a long hold double-steps. On this mGBA build:

* **one press = keydown 0.05 s, keyup, then 0.33 s gap** gives exactly one step;
* the commit **A** should be held ~0.10 s, then ~0.32 s gap.

From the blank cell, one **Right** selects `A`, two select `B`, and so on. One **Left** selects `P`, two select `O`, etc. A Python driver (`enter.py` in the work directory) generated the deterministic press counts:

```
Right k times -> symbol index k-1   (k >= 1)
Left  k times -> symbol index 16-k  (k >= 1)
```

### Recon (strings / literals)

`strings -t x -n 4` over the GBA image gives 5,150 lines. A keyword grep for `password|cheat|debug|secret|unlock|level|stage|skip|code|select|option|sound|config|save|state|reset` produced exactly one relevant ASCII hit: `ET:CODE` at file `0x4666`, which is part of the encoded NES text `ENTER:SECRET:CODE`. The NES UI stores tile indices rather than ASCII, so the absence of English menu strings is expected. Searching the published passwords literally finds nothing in the image because they are computed from the validator, not stored; the only fixed password tables are the 16-byte alphabet tables at `$DFA0` and `$E388`.

### Codes tested live

| Code | Result | NES RAM |
|---|---|---|
| `NMIHPPBPCAFHABDPCPCH` (published level 1) | `STAGE 1` | `$58=01` |
| `NMOLBODOLJGGCPODJABL` (**new**, level 51) | `STAGE 51` | `$58=33` |
| `BOFEDJJDDJGKEFOLFMIH` (published “Level 74/76”) | `STAGE 74` | `$58=4A` |
| `BOCPOLABOLHIMNPCGEKH` (**new**, true level 76) | `STAGE 76` | `$58=4C` |
| `AAAAAAAAAAAAAAAAAAAA` (valid symbols, bad checksums) | returns to entry screen | `$58=00` |

## 4. Address map

### GBA-side

| Address / offset | Meaning |
|---|---|
| File `0x2EE9` | Start of the wrapper-encoded NES image in the GBA ROM (not used for the runtime analysis) |
| EWRAM `0x02000000` | Runtime NES PRG, 16 KiB (savestate offset `0x21000`) |
| EWRAM `0x02004000` | Runtime NES CHR, 8 KiB (savestate offset `0x25000`) |
| IWRAM `0x03007200` | Runtime NES 2 KiB RAM (savestate offset `0x20200`), verified by `$1F=06`, `$20=0x3A`, `$5F=01` on the password screen |
| IWRAM `0x03006704` | Wrapper current pressed-key bitmask (active high) |
| IWRAM `0x03006708` | Wrapper newly-pressed-key edge bitmask |
| GBA VRAM `0x2000` | 32×30 NES nametable mirrored as 16-bit GBA tilemap entries; low byte is the NES tile index, `0xB0` is space |
| IWRAM `0x03006????` | Wrapper/main-loop state (not needed for the cheat) |

The savestate layout used to read RAM without a debugger is mGBA's PNG `gbAs` chunk: `zlib.decompress` it, then VRAM at `0x1000`, IWRAM at `0x19000`, EWRAM at `0x21000`. A 397,312-byte state was used for a 1 MiB ROM.

### NES-side (16 KiB PRG mapped at `$C000`–`$FFFF`)

| NES address | PRG file offset | Meaning |
|---|---|---|
| `$DB7A` | `0x1B7A` | Entry-screen validator entry (restore `LDX #$00` here; runtime byte is the wrapper patch `0x42`) |
| `$DB7C`–`$DB91` | `0x1B7C`–`0x1B91` | Chained nibble transform |
| `$DB92`–`$DBA8` | `0x1B92`–`0x1BA8` | Three group checks (4 data + 1 check per group) |
| `$DBAA`–`$DBCB` | `0x1BAA`–`0x1BCB` | Final check and accept/reject branch |
| `$DBCD` | `0x1BCD` | Rejection: `JMP $DA8E` (re-enter password screen) |
| `$DBD2`–`$DBF8` | `0x1BD2`–`0x1BF8` | Copy accepted nibbles to game-state bytes; rebuild `$73`/`$58` |
| `$DA8E` | `0x1A8E` | Password entry screen / setup |
| `$DAB5`–`$DB7A` | `0x1AB5`–`0x1B7A` | Entry loop (draw cell, poll `$12`, Left/Right/A) |
| `$DFA0` | `0x1FA0` | Inverse alphabet table (16 bytes) |
| `$E2BD` | `0x22BD` | Password generator (game state → password) |
| `$E360` | `0x2360` | 20-word pointer table: the 20 state bytes used by the generator |
| `$E388` | `0x2388` | Display alphabet table (`AOFKCPGELBHMJDNI`) |
| `$C398` | `0x0398` | Title logic: `Select` toggles `$5F`; password screen only when `$59==0 && $5F!=0` |
| `$C4D5` | `0x04D5` | Normal progression: `INC $58`, compare with `0x33` (ending sentinel) |
| `$CF0D` / `$CF1A` | `0x0F0D` / `0x0F1A` | `$74` bomb-count increment (max 9) / `$73` firepower increment (0x10 steps to 0x50) |

## 5. Algorithm

### 5.1 Display alphabet and inverse table

The 16 canonical nibble values are displayed as:

```
n:     0 1 2 3 4 5 6 7 8 9 A B C D E F
char:  A O F K C P G E L B H M J D N I      ($E388 = "AOFKCPGELBHMJDNI")
```

Typing a character `c` from `A`–`P` selects an index `c & 0x0F` into the inverse table at `$DFA0`:

```
inv = [05,00,09,04,0D,07,02,06,0A,0F,0C,03,08,0B,0E,01]
n   = inv[ord(c) & 0x0F]
```

This is a permutation, so all 16 letters are distinct inputs.

### 5.2 Chained transform

For the 20 typed nibbles `n[0..19]`, with `n[-1] = 0`:

```
w[i] = (n[i] + 7 + n[i-1]) & 0x0F
```

`w` is the actual game-state byte sequence that the validator checks and copies into the state pointers.

### 5.3 Checksum

The accepted set is defined by four 4-bit check symbols:

```
w[4]  = (w[0]+w[1]+w[2]+w[3])            & 0x0F
w[9]  = (w[5]+w[6]+w[7]+w[8])            & 0x0F
w[14] = (w[10]+w[11]+w[12]+w[13])        & 0x0F
w[19] = (2*(w[4]+w[9]+w[14])
         + w[15]+w[16]+w[17]+w[18])      & 0x0F
```

The 16 non-check nibbles are free. The transform is a bijection on nibble strings, so the validator accepts exactly `16^16 = 2^64` of the `16^20 = 2^80` possible symbol strings.

### 5.4 Encoder (inverse of the validator)

```
n[i] = (w[i] - 7 - n[i-1]) & 0x0F,  n[-1] = 0
char[i] = DISP[n[i]]
```

Reference implementation (used for every code in this report):

```python
INV = [5,0,9,4,13,7,2,6,10,15,12,3,8,11,14,1]
DISP = "AOFKCPGELBHMJDNI"

def decode(code):
    v = [INV[ord(c) & 0xF] for c in code]
    w, prev = [], 0
    for x in v:
        w.append((x + 7 + prev) & 0xF)
        prev = x
    return w

def valid(w):
    return (all((sum(w[s:s+4]) & 0xF) == w[s+4] for s in (0,5,10))
            and ((2*(w[4]+w[9]+w[14]) + w[15]+w[16]+w[17]+w[18]) & 0xF) == w[19])

def encode(w):
    assert valid(w)
    n, prev = [], 0
    for x in w:
        n.append((x - 7 - prev) & 0xF)
        prev = n[-1]
    return ''.join(DISP[i] for i in n)

def level(code):
    w = decode(code)
    return (w[17] << 4) | w[2]
```

### 5.5 Field layout

The 20 `w` nibbles map to the game-state bytes through the generator's pointer table at `$E360`:

| w index | NES byte | Meaning (confidence) |
|---:|---|---|
| 0 | `$67` | score/BCD byte 7 |
| 1 | `$77` | ability/item flag |
| 2 | `$DD` = `$58 & 0x0F` | **level low nibble** |
| 3 | `$61` | score/BCD byte 1 |
| 5 | `$66` | score/BCD byte 6 |
| 6 | `$DC` = `$73 >> 4` | **firepower level** (1–5; `$73` is 0x10…0x50) |
| 7 | `$64` | score/BCD byte 4 |
| 8 | `$79` | ability/item flag |
| 10 | `$74` | **max bombs** (0–9; bomb-slot loop at `$CF0D`/`$CFEF`) |
| 11 | `$63` | score/BCD byte 3 |
| 12 | `$75` | ability/item bitmask (0–7) |
| 13 | `$62` | score/BCD byte 2 |
| 15 | `$65` | score/BCD byte 5 |
| 16 | `$94` | ability/item flag |
| 17 | `$DE` = `$58 >> 4` | **level high nibble** |
| 18 | `$76` | ability/item flag |
| 19 | `$95` | final checksum |
| 4, 9, 14 | `$99`, `$9A`, `$9B` | group checksums |

The published “maximum bombs / maximum fire” code `BAHIMNABANCPMNMNMNMH` decodes to level 1 with `w[6]=5` (fire 5) and `w[10]=9` (bombs 9), which matches the labels on that code. The exact bit meanings of `$75`, `$77`, `$79`, `$94`, `$76` were not individually proven in play; they are ability/item flags derived from the generator table and the pickup routines at `$CF2A`–`$CF57`.

## 6. Tables

### 6.1 Published codes checked

64 unique 20-symbol strings were scraped from the archived GameFAQs page (the page aggregates NES/FDS/GBA/POS Bomberman codes). All 64 satisfy the validator above. The 0–50 level table and the “secret level” code were decoded to their field levels; all agree with their labels except the entry labelled `Level 76`.

### 6.2 Published-list anomaly

`BOFEDJJDDJGKEFOLFMIH` appears on the archived page as both “Level 74” and “Level 76”. Its recovered field level is `0x4A = 74`. Entered live, it starts `STAGE 74` (`$58=0x4A`). The label “76” is therefore wrong; the true level-76 code is not in that list.

### 6.3 Wrapper reset / save facts

* **Start + Select + A + B** (GBA buttons) resets the emulated NES to its title screen. Observed: `$58` changes `0x33` → `0x00`, `$5F` `1` → `0`, `$33` restarts; the title text `TOP ::3557900` remains because the NES RAM is not cleared by the soft reset.
* **L+R** enters the wrapper's system-menu pause state. This is RAM-verified: the NES frame counter `$33` freezes (observed at `0x5F` for more than one second), and pressing A, B, Start, Select, Up or Down resumes the NES. The menu's own text is a GBA-native overlay, not the NES nametable; the manual's reset/save/sleep options therefore could not be read out of the NES text space. The separate four-button combination **Start+Select+A+B** resets the emulated NES. `L+R+Start`, `L+R+Select`, `Start+Select` and `Select` alone were also tried; none exposed a separate save/restore screen. Static search of the GBA ROM found no menu text (`RESET`, `SAVE`, `SLEEP`, `LINK`, `MENU`, …) and no LZ77 text bank; the only wrapper SRAM content is a 512-byte `0xFF` block with `BMOB` + `07 13 24 03` at `0xFC`, matching the boot signature at `0x080000C0`.
* The published “buried debug” flag `$94` (cah4e3) is a NES RAM address. It is not reachable by any input; it would require writing NES RAM, which is outside the in-game/developer-intended scope of this report.
* Input-read enumeration: `$12` is read at `$C368`, `$C370`, `$C4AA`, `$C4B8`, `$C5C3`, `$C613`, `$C62F`, `$DACC` and `$CFA4`. The only comparisons are Start (`$10`), Select (`$20`), A/Left/Right (`$80/$02/$01`) and “any key”; there is no multi-press sequence table or comparator. That is the evidence for “no NES button-code cheat in this image”.

## 6b. Enumeration

### Space definition

* Alphabet: 16 symbols, displayed as `AOFKCPGELBHMJDNI`.
* Length: exactly 20 symbols.
* Checksum: four 4-bit check symbols at positions 4, 9, 14, 19.
* Free payload: 16 nibbles = 64 bits.
* Representable input strings: `16^20 = 2^80 = 1,208,925,819,614,629,174,706,176`.
* Accepted strings: `16^16 = 2^64 = 18,446,744,073,709,551,616` (exactly one in 65,536).
* The validator performs **no semantic range check** on the level or the score/ability bytes; any checksum-valid string is copied into the 20 state bytes. The normal game progression only uses `$58 = 1..50` and treats `0x33` as the ending sentinel (`$C4D5`), but the password loader will start `$58 = 0x33`, `0x4A`, `0x4C`, etc.

### Novel codes (not in GameFAQs, VGChartz, cah4e3, or the ROM text)

Both were generated by fixing the 16 payload nibbles, recomputing the four check nibbles, and encoding with `encode()` above. Both were entered on the live GBA using the menu path in §3.

1. **`NMOLBODOLJGGCPODJABL`** — level 51 (`0x33`), based on the published level-50 code's score/ability fields.
   * `w = [5,0,3,0,8, 1,5,5,0,11, 9,3,1,0,13, 5,0,3,0,8]`
   * In-game: `STAGE 51`; NES RAM `$58 = 0x33`, `$73 = 0x50`, `$74 = 9`; the stage is playable (HUD `TIME 200`, `LEFT 2`).

2. **`BOCPOLABOLHIMNPCGEKH`** — true level 76 (`0x4C`), derived from the published 74/76 code by changing only the level nibbles and recomputing the checks.
   * `w = [0,1,12,0,13, 0,15,0,1,0, 9,0,1,0,10, 0,1,4,1,4]`
   * In-game: `STAGE 76`; NES RAM `$58 = 0x4C`, `$73 = 0xF0`, `$74 = 9`.

Neither string occurs in the archived GameFAQs HTML, the VGChartz page, or the cah4e3 page (`grep -c` = 0 for both).

### Bounds proven by rejection

* `AAAAAAAAAAAAAAAAAAAA` uses only valid alphabet symbols, so it reaches the validator. Its checksums fail. In-game result: the game returns to `ENTER:SECRET:CODE`, the cursor resets to `$1F=06` / `$20=0x3A`, `$58` remains `0x00`, and no `STAGE` screen appears.
* The validator accepts the 8-bit level field up to at least 76; the field is 4+4 bits and can express 0–255. The game's own progression uses `0x33` as the ending sentinel, so level 51 is a boundary value that the loader still starts as a stage. The level bound is therefore a format bound (8 bits), not a validator bound.
* All 64 published codes pass the offline validator; the live GBA accepted two of them and rejected the bad-checksum string, so the decoder agrees with the ROM on accepted and rejected inputs.

## 7. Validation evidence

**Observed (live mGBA):**

* Title screen text: `START`, `CONTINUE`, `TOP ::3557900`, `1987 HUDSON SOFT`, `LICENSED TO NINTENDO`.
* Password screen text: `ENTER:SECRET:CODE`.
* `NMIHPPBPCAFHABDPCPCH` → `STAGE 1`, `$58=01`.
* `NMOLBODOLJGGCPODJABL` → `STAGE 51`, `$58=33`.
* `BOFEDJJDDJGKEFOLFMIH` → `STAGE 74`, `$58=4A`.
* `BOCPOLABOLHIMNPCGEKH` → `STAGE 76`, `$58=4C`.
* `AAAAAAAAAAAAAAAAAAAA` → rejected, back to entry, `$58=00`.
* L+R → NES `$33` freezes at `0x5F` for >1 s; any of A/B/Start/Select/Up/Down resumes.
* Start+Select+A+B → title, `$58=00`, `$5F=00`.

**Derived (disassembly + validator model):**

* The alphabet permutation, chained transform, three group checks and final check at `$DB7A`–`$DBD0`.
* The generator at `$E2BD` and the field/pointer table at `$E360`.
* The field map: level = `(w[17]<<4)|w[2]`; firepower = `w[6]`; bombs = `w[10]`; score bytes = `w[3,13,11,7,15,5,0]`.
* The accepted-set size `16^16`.
* The published-list anomaly: the code labelled 76 decodes to 74.

**Inferred:**

* The individual ability/item flag meanings for `$75`, `$77`, `$79`, `$94`, `$76`.
* The nature of the wrapper `0x42` patch bytes (native hook vs. a fixed NOP-like behaviour); only their effect on the password path was reasoned about.
* Whether stage 51/76 are reachable by normal progression. `$C4D5` shows 0x33 is the ending sentinel; stages above 50 are not part of the normal 1–50 loop.

## 8. Unknowns

* Exact semantics of the five ability/item bytes (`$75`, `$77`, `$79`, `$94`, `$76`) were not isolated one-by-one in play. The generator table proves which nibble maps to which byte; the pickup routines at `$CF2A`–`$CF57` show they are flags, and `$75` is a 0–7 bitmask.
* The wrapper patch byte `0x42` appears at 42 sites in the runtime NES image. Its exact native action is not documented here; offline analysis replaced it with NOP and restored the one site needed for the password chain (`$DB7A` → `LDX #$00`). The live GBA accepted the same codes, so the password model is unaffected.
* No full 64-code live entry was performed; the 64/64 agreement is against the recovered validator, with live spot checks.
* The exact display order of the seven score bytes was not needed for the cheat result and was not proven; the byte-to-nibble mapping is proven by the generator table.
* The system menu's own option list/selection mapping was not decoded from the GBA-native overlay. What is proven is the pause state (NES `$33` stops under L+R), the resume-on-button behaviour, and the separate Start+Select+A+B reset. The manual documents reset/save/sleep options for this menu; no save/restore action was observed in the tested button space.
* The ROM's stored copy of the NES image at file `0x2EE9` contains extra bytes relative to the runtime image. The runtime image was taken from RAM and is the execution truth; the stored encoding format was not reversed.

## 9. Tooling

* `mgba` 0.10.5 SDL frontend, `Xvfb :246`, `openbox`, `SDL_AUDIODRIVER=dummy`.
* `ss.py` — zlib-decompress the PNG `gbAs` chunk and address VRAM/IWRAM/EWRAM.
* `pw.py` — alphabet tables, decode/validate/encode, level extraction.
* `enter.py` — deterministic xdotool password entry (one step per press, 0.05 s hold + 0.33 s gap).
* `maps.py` — render the GBA VRAM `0x2000` 16-bit tilemap as text (`0xB0` = space).
* `da65` (cc65) and `arm-none-eabi-objdump -M force-thumb` for the NES/GBA disassembly.
* Archived sources used for published-code checks: `web.archive.org` GameFAQs GBA cheats page, VGChartz cheats page, cah4e3 “Mostly Unpublished NES Cheats” B page. All were treated as data; no instructions in them were followed.

## 10. Legal note

No ROM, extracted graphics, music, or game text is redistributed here. The report contains only addresses, algorithms, hashes, and short generated code strings needed to reproduce the result.
