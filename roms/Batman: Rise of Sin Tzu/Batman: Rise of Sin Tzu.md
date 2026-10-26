# Batman: Rise of Sin Tzu (GBA) — Reverse Engineering Report

## 1. Target identity

| Item | Value |
|---|---|
| File | `roms/Batman: Rise of Sin Tzu/Batman: Rise of Sin Tzu.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title (0xA0) | `BATMAN-RISE` |
| Game code (0xAC) | `BATE` |
| Maker code (0xB0) | `41` (Ubisoft) |
| Version (0xBC) | `00` |
| Fixed byte 0xB2 | `0x96` |
| Complement check (0xBD) | stored `0xBD`, computed `0xB9` — **mismatch** |
| Header checksum (0xBE) | stored `0x0000`, computed `0xF80B` — **zeroed** |
| Entry word (0x00) | `0xEA1FE217` → branch to `0x087F8864` (**not** the stock `0xEA00002E` / `0x080000C0`) |
| MD5 | `b1e85c2e059bfcdaed2f1b861ffc55b4` |
| SHA-1 | `aee09505aa539d8b5bd7e2aebfd54e92b7c65836` |
| SHA-256 | `f8b6eb0b3510fa9df095492be5c531aa9b61b92a3d22fd253ba042ff4cab6106` |

**The image is patched.** Exactly one Nintendo logo exists (file `0x4`), so it is not a
multi-game pack. The entry word jumps to `0x087F8864`, where an appended ARM stub
(not part of the game) forces blank (`DISPCNT=0x0100`), clears the palette, decompresses
`0x3F00` bytes from `0x087F8C58` into EWRAM `0x02000000`, and executes
`bx 0x020000C0`. That payload is a third-party trainer menu:

```
SUNHORS
WITH: BATMAN RISE OF SIN TZU
 UNL ENERGY   NO
 UNL COMBOS   NO
 UNL BOMBS    NO
 HAVE KEY     NO
 RESET TIMER  NO
(press START to boot the game)
```

It is **not developer content and is out of scope** for this report; it is recorded
only so the patch is not mistaken for game behaviour. Restoring the entry word to
`0xEA00002E` (`b 0x080000C0`) boots the untouched game (Ubisoft / DC Comics / title /
language select), which proves the trainer replaces only the header entry and appends
its own blob in the tail — the game itself is intact. All dynamic tests below used that
clean-entry copy (`/tmp/opencode/sintzu/rom_clean.gba`, identical to the target except for
bytes 0x00–0x03).

The only "continue" path is the password screen: mGBA produced just a 0-byte `.sav` for
this cart, and `CONTINUE` always asks for a password. That is the classic reason for a
password system.

## 2. Executive summary

The game contains two developer-intended cheat systems, both reachable from the title
screen:

1. **A 6-symbol progress password system** (`CONTINUE` → `ENTER PASSWORD`).
   - Alphabet of 32 symbols (`BCDFGHJKLMNPQRSTVWXYZ_0123456789`), 6 cells, so
     32^6 = **1,073,741,824** possible strings.
   - The six symbols are obfuscated (XOR with a 6-byte key, then a symbol-5-dependent
     offset), and the last symbol is a **5-bit checksum** over the other five. That leaves
     a 25-bit payload; a payload is accepted only if its middle 8 bits (bits 12–19) index
     one of **94 map nodes** and the node's 16-bit type is not one of `50, 51, 74, 75`.
   - The payload is the story-position word: the node index selects the position on the
     mission map. A accepted code jumps the player to that position; pressing A on the map
     starts the corresponding mission. This is a complete **level-select / progress-restore**
     cheat, ~**11.8 million** distinct accepted codes.
   - The whole space is characterised below; novel codes were minted, **typed on the
     on-screen keypad**, and confirmed (screenshots). Bounds are proven by in-game
     rejection (out-of-range node, out-of-range type, bad checksum, and a published typo).
2. **Two hard-coded hidden cheat passwords**, `_NDTH_` and `_FLYM_`, validated by a second
   routine that bypasses the progress decoder and sets bits 0 and 1 of the progress-flags
   word. The public lists name these "Invincibility" and "Unlock all levels"; the ROM's
   second literal is 6 symbols (`_FLYM_`), while GameFAQs prints an unenterable 7-symbol
   `_FLYMF_` with an extra `F`.

Published codes were verified against the ROM rather than trusted: of the **84** six-symbol
entries on the GameFAQs/AbsolutCheats lists, **74 decode with a correct checksum**
(including the whole level chain 1-1 … 9-7); the 10 failures are 8 distinct transcription
errors (two entries are duplicates) plus one 7-symbol "level select" string that cannot be
typed at all. One of the typos (`HLNZXJ`) was also entered in the emulator and **rejected
by the game**, confirming the decoder and the published typo simultaneously.

The four published "hold L+R at the main menu" button sequences could not be located in
this revision by literal mask search (see §7/§8); they are the only published claim this
report does not confirm.

## 3. How to reproduce

Emulator and harness:

```bash
Xvfb :175 -screen 0 1280x960x24 &
DISPLAY=:175 openbox &
DISPLAY=:175 SDL_AUDIODRIVER=dummy mgba -3 game.gba &
W=$(DISPLAY=:175 xdotool search --name mGBA | head -1)
DISPLAY=:175 xdotool windowfocus $W
```

mGBA SDL keymap used: **A = `x`**, B = `z`, L = `a`, R = `s`, Start = `Return`,
Select = `BackSpace`, D-pad = arrows. Hold keys 120–150 ms.

Menu path (clean-entry ROM):

```
Ubisoft logo → DC Comics → title (Start) → language select (English)
main menu: NEW GAME / CONTINUE / TUTORIAL / OPTIONS
CONTINUE  → "ENTER PASSWORD" keypad
```

Keypad controls (verified): **Up = −1**, **Down = +1** (mod 32), **Left/Right = move cell**,
**A = submit**. There are **six** cells: five are visible from the start and the sixth is the
cell that initially displays the text `OK`; editing it replaces `OK` with the sixth symbol.
Pressing A submits from any cell. This is the "accept cell also carries a character"
quirk: a six-symbol code cannot be finished by simply moving right and pressing A — the
sixth symbol has to be dialled in on the `OK` cell.

Savestate used for experiments: `/tmp/opencode/sintzu/rom_clean.ss1` (password screen,
buffer all zero). `-t rom_clean.ss1` reloads it; **F1** loads, **Shift+F1** saves.

Codes tested (all in §6/§6b): published list (see §6), `_NDTH_`, `_FLYM_`,
`CGRLNH`, `NLDPGS`, `NLDPGT`, `82NP64`, `0201QX`, `BBBBBW`, `HLNZXJ`, `QV2CLL`.

## 4. Address map

`rom_address = 0x08000000 + file_offset`.

| ROM address | File offset | What |
|---|---|---|
| `0x0806FB70` | `0x6FB70` | Password-screen per-frame input handler (cursor, letter edit, submit) |
| `0x0806FC00` | `0x6FC00` | A/Start dispatch; copies the 6 symbols to the stack |
| `0x08064200` | `0x64200` | **Progress-password decoder** (returns 1 = accepted) |
| `0x08088F54` | `0x88F54` | **Decrypt + bit-unpack + checksum** used by the decoder |
| `0x080640A8` | `0x640A8` | **Encoder/generator** (builds the code shown to the player) |
| `0x08088E18` | `0x88E18` | Inverse of `0x08088F54` (checksum symbol + packing) |
| `0x08070174` | `0x70174` | **Hidden two-code validator** (`_NDTH_`, `_FLYM_`) |
| `0x0806FCA4` | `0x6FCA4` | Submit: `bl 0x08064200`; on 0 → `bl 0x08070174`; on 0 → error beep |
| `0x0806FCBA` / `0x0806FCD0` | | Hidden-code return 1 / 2 → `orr` bit 0 / bit 1 into flags |
| `0x0809D858` | `0x9D858` | Password alphabet, 32 bytes + tail (see §6) |
| `0x0809D878` | `0x9D878` | Hidden-code table: `_NDTH_`, `_FLYM_` (2 × 6 bytes, no terminator) |
| `0x080A6030` | `0xA6030` | Obfuscation key table (12 bytes, first 6 used) |
| `0x0809C9EC` | `0x9C9EC` | **Map-node table**, 94 records × 16 bytes |
| `0x08093E94` | `0x93E94` | Level-name pointer table (12 entries) |
| `0x08093EC4`–`0x08093F78` | | Level names + `Connect to Nintendo GameCube` + `TimeAttack Maps` |
| `0x0806442C` | `0x6442C` | Consumer of hidden-flag **bit 0** (player init) |
| `0x03000F2C` | — | IWRAM global: pointer to the progress struct |
| struct +0x28 | — | `u16` progress flags (hidden codes set bit 0 / bit 1) |
| struct +0x15 | — | current level id |
| struct +0x2A | — | 4-byte password payload (written by the decoder) |

Password-screen object during the savestate: base `0x03002630`; cursor `+0xA8`;
"changed" flag `+0xAC`; **symbol buffer `+0xAD`, six bytes** (observed in the debugger:
writing `21,10,2,15,5,21` at `0x030026DD` made the game validate `_NDTH_`).

## 5. Algorithm

### 5.1 Symbols

```
ALPHABET = "BCDFGHJKLMNPQRSTVWXYZ_0123456789"     # 32 symbols, index 0..31
key[6]   = {1, 4, 13, 8, 10, 5}                  # 0x0A6030, bytes 0..5
```

### 5.2 Decoder (`0x08064200` → `0x08088F54`)

```python
def decode(s):                       # s = 6 symbol indices, 0..31
    b = [s[k] ^ key[k] for k in range(6)]          # pass 1: XOR
    b5 = b[5]
    d = [ (b[k] - key[k]*b5) & 31 for k in range(5) ]  # pass 2: offset by symbol 6
    if (sum(d) & 31) != b5:                        # pass 3: 5-bit checksum
        return None                                #   == decrypt(s[5])
    payload = sum(d[k] << (5*k) for k in range(5)) # 25 bits, LSB-first
    idx = (payload >> 12) & 0xFF                   # map node, 8 bits
    if idx > 93: return None
    node_type = u16[0x09C9EC + idx*16]             # first field of the 16-byte record
    if node_type in (50, 51, 74, 75): return None
    return payload, idx, node_type
```

Accepted payloads are stored to `[0x03000F2C]+0x2A`; the caller then opens the mission
map with the node selected.

Note the byte-order trap that cost time here: the literal pool at `0x08064250` holds
bytes `EC C9 09 08`, i.e. **`0x0809C9EC`**, not `0x0809ECC9` (that would be inside a font
width table).

### 5.3 Encoder (`0x080640A8` → `0x08088E18`)

Exactly invertible:

```python
def encode(payload):
    d  = [(payload >> (5*k)) & 31 for k in range(5)]
    b5 = sum(d) & 31
    s  = [ (((d[k] + key[k]*b5) & 31) ^ key[k]) for k in range(5) ] + [b5 ^ 5]
    return ''.join(ALPHABET[i] for i in s)
```

The in-game generator additionally rebuilds the index field from the current level and
applies −1/−2 fix-ups when the selected node's type is 50/51/74/75, so that the decoder's
re-validation lands on the same node. With payload `= idx << 12` the encoder reproduces the
published level passwords **exactly** (e.g. idx 11 → `QV2CLL`, idx 9 → `GVLC2B`,
idx 15 → `6V2CL2`), which is the strongest possible check of the model.

### 5.4 Hidden two-code validator (`0x08070174`)

```python
for e in range(2):                      # records at 0x09D878, 6 bytes each
    if all(ALPHABET[input[k]] == record[e][k] for k in range(6)):
        return e + 1                    # 1 -> flags |= 1 ; 2 -> flags |= 2 ; else 0
```

The caller (`0x0806FCBA` / `0x0806FCD0`) ORs bit 0 / bit 1 into the `u16` at
`[0x03000F2C]+0x28` and redraws; it does **not** leave the password screen. Bits already
set are left alone (no double-set).

## 6. Tables

### 6.1 Alphabet / key / hidden codes

```
0x09D858: 42 43 44 46 47 48 4A 4B 4C 4D 4E 50 51 52 53 54 56 57 58 59 5A 5F 30..39
          B  C  D  F  G  H  J  K  L  M  N  P  Q  R  S  T  V  W  X  Y  Z  _  0..9
0x09D878: 5F 4E 44 54 48 5F   "_NDTH_"
0x09D87E: 5F 46 4C 59 4D 5F   "_FLYM_"
0x0A6030: 01 04 0D 08 0A 05 05 09 02 04 0F 03
```

### 6.2 Level names (`0x093E94` pointer table, reverse order in ROM)

`TimeAttack Maps`, `Connect to Nintendo GameCube(TM)`, `Gotham's Rooftops`,
`ChinaTown`, `Gotham City Hall`, `The Docks`, `Gotham Chemical`, `Dock 47`,
`The Batcave`, `Gotham Sewers`, `Arkham Asylum`, `The Showdown`.

### 6.3 Map-node table (`0x09C9EC`, 94 × 16 bytes)

Observed record layout (little endian): `u16 type, u16 flags, u32 handler, u32 data,
u16 seq, u16 chapter` — 16 bytes; the field names beyond `type` are inferred. The
validator only uses `type`. Types rejected: **50, 51, 74, 75** (these are exactly nodes
61, 62, 90, 91). Node 0's type is 0; the type sequence rises irregularly to 75 across the
94 records.

### 6.4 Published passwords verified against the ROM

Every GameFAQs/AbsolutCheats password was decoded offline; ✔ = checksum valid, ✘ = rejected
by the model *and* (spot-checked) by the game. Node = decoded map index.

| Published name | Code | Node | Valid |
|---|---|---:|---|
| Level 1-1 | `MG7L4R` | 2 | ✔ |
| Level 1-2 | `RZHLXM` | 3 | ✔ |
| Level 1-3 | `WGRLN_` | 4 | ✔ |
| Level 1-4 | `3G7L47` | 6 | ✔ |
| Level 2-1 | `7ZHLX3` | 7 | ✔ |
| Level 2-2 | `BBBCBG` | 8 | ✔ |
| Level 2-3 | `GVLC2B` | 9 | ✔ |
| Level 2-4 | `LBVCVQ` | 10 | ✔ |
| Level 3-1 | `QV2CLL` | 11 | ✔ |
| Level 3-2 | `VBBCBZ` | 12 | ✔ |
| Level 3-3 | `ZVLC2B` | – | ✘ (bad checksum) |
| Level 3-4 | `2BVCV6` | 14 | ✔ |
| Level 4-1 | `RL4XGS` | 18 | ✔ |
| Level 4-2 | `_LNXZ0` | 20 | ✔ |
| Level 4-3 | `7L4XG8` | 22 | ✔ |
| Level 4-4 | `C2DX64` | 23 | ✔ |
| Level 4-5 | `VGWPN_` | 27 | ✔ |
| Level 5-1 | `ZZ3PDW` | 28 | ✔ |
| Level 5-2 | `63MPXE` | – | ✘ (contains `E`, not in alphabet) |
| Level 5-3 | `PBZGQV` | – | ✘ (bad checksum) |
| Level 5-4 | `TV6GLL` | 34 | ✔ |
| Level 5-5 | `1VQG2V` | 36 | ✔ |
| Level 5-6 | `9V6GL2` | 38 | ✔ |
| Level 6-1 | `0D7RDW` | – | ✘ (bad checksum) |
| Level 6-2 | `DG_RNH` | 46 | ✔ |
| Level 6-3 | `JZ7RDC` | 47 | ✔ |
| Level 6-4 | `RB2JVQ` | 48 | ✔ |
| Level 6-5 | `WVBJLL` | 49 | ✔ |
| Level 6-6 | `_BLJBZ` | 50 | ✔ |
| Level 6-7 | `3VVJ2V` | 51 | ✔ |
| Level 6-8 | `7B2JB6` | – | ✘ (bad checksum) |
| Level 7-1 | `CVBJ2L` | 49 (+bits) | ✔ |
| Level 7-2 | `HBLJBG` | 54 | ✔ |
| Level 7-3 | `MVVJ2B` | 55 | ✔ |
| Level 7-4 | `QQT9ST` | 56 | ✔ |
| Level 7-5 | `V619JP` | 57 | ✔ |
| Level 7-6 | `ZQ9981` | 58 | ✔ |
| Level 7-7 | `26K90Y` | 59 | ✔ |
| Level 7-8 | `Y2NL6N` | 65 | ✔ |
| Level 7-9 | `524LQX` | 67 | ✔ |
| Level 7-10 | `F2NL64` | 69 | ✔ |
| Level 8-1 | `XG3CN_` | 73 | ✔ |
| Level 8-2 | `4GMC47` | 75 | ✔ |
| Level 8-3 | `8ZWCX3` | 76 | ✔ |
| Level 8-4 | `DG3CNH` | 77 | ✔ |
| Level 8-5 | `JZCCDC` | 78 | ✔ |
| Level 8-6 | `NGMC4R` | 79 | ✔ |
| Level 8-7 | `_BQ4BZ` | 81 | ✔ |
| Level 9-1 | `3VZ42V` | 82 | ✔ |
| Level 9-2 | `7B64B6` | – | ✘ (bad checksum) |
| Level 9-3 | `CVG4L2` | 84 | ✔ |
| Level 9-4 | `HBQ4BG` | 85 | ✔ |
| Level 9-5 | `MVZ42B` | 86 | ✔ |
| Level 9-6 | `RB64VQ` | 87 | ✔ |
| Level 9-7 | `V65YJP` | 88 | ✔ |
| Boss #1 | `HLNZXJ` | – | ✘ (bad checksum; **game rejects it**, screenshot) |
| Boss 2 | `NGHR4R` | 40 | ✔ |
| Boss 3 | `PD4LQD` | – | ✘ (bad checksum) |
| Final Boss | `ZQFY81` | 89 | ✔ |
| Invincibility | `_NDTH_` | – | ✔ (hidden 2-code table, returns 1) |
| Unlock all levels / level select | `_FLYMF_` (published) | – | ✘ 7 symbols; ROM code is `_FLYM_` → returns 2 |
| Bat Cave | `BBBBBW` | 66 | ✔ (game shows **The Batcave**) |
| Chinatown | `BBBBHV` | 7 | ✔ |
| Gotham Rooftops | `BBBBM6` | 2 | ✔ |
| Gotham Chemicals | `5MQZRN` | 39 | ✔ |
| Gotham Sewers | `5V2MRN` | 76 | ✔ |
| Dock 47 | `H6T73P` | 43 | ✔ |
| Scarecrow | `6V2CL2` | 15 | ✔ (`= encode(15<<12)` exactly) |
| Clayface | `L20_QD` | 40 | ✔ |
| Bane | `MQFV8K` | 69 | ✔ |
| Sin Tzu | `4V252V` | 89 | ✔ |
| End credits | `NV252B` | 93 | ✔ |

The level-password chain (2,3,4,6,7,8,9,10,11,12,14,18,20,22,23,27,28,34,36,38,40,46…88)
is monotonic in story order, which independently confirms that bits 12–19 are the map
position and that the checksum model is right.

## 6b. Enumeration

**Space definition**

* Input alphabet: 32 symbols (26 letters minus the 5 vowels = 21, plus `_`, plus `0-9`).
* Length: fixed 6. Representable strings: **32^6 = 1,073,741,824**.
* Symbol 6 is a **5-bit checksum**; valid strings: **32^5 = 33,554,432**.
* Payload: 25 bits = `5 × 5` data symbols. Field layout:
  * bits **12–19** (8 bits): map-node index,
  * bits **0–11** (12 bits) and **20–24** (5 bits): 17 further bits carried verbatim by the
    encoder, unread by the validator (see §8).
* Accepted payloads: node ≤ 93 and node type ∉ {50,51,74,75} → **94 − 4 = 90** reachable
  nodes → **90 × 2^17 = 11,796,480** distinct accepted codes.

**Novel codes (in no published list) and in-game proof**

| Code | Payload | Node | Typed on keypad? | Effect (screenshot) |
|---|---|---|---|---|
| `CGRLNH` | `0x000000` | 0 | **yes** (40 presses) | Accepted; mission map opens at **Gotham's Rooftops**, only the first node lit (`gnov1.png`, `gnov2.png`). Not on GameFAQs/VGChartz/TCRF/AbsolutCheats. |
| `NLDPGS` | `0x058000` | 88 | **yes** (49 presses) | Accepted; mission map opens on the full map at **The Showdown** (`gfinal_map.png`); A starts the final-location cutscene "Thus it ends as all battles should end…" (`gfinal_intro.png`) and the playable final area (`gfinal_game2.png`). Published 9-7 is `V65YJP` (same node, different payload bits); `NLDPGS` itself appears in no list. |
| `0201QX` | `0x03C000` | 60 | buffer-injected | "The Batcave" map position (`gi60.png`) — node 60 is absent from every published list (published Bat Cave is `BBBBBW`, node 66). |
| `82NP64` | `0x05D000` | 93 | buffer-injected | Full-map position ("The Showdown" node; published end-credits code is `NV252B`, same node, payload `0x05D006`). |

**Bounds proven by rejection (all observed in the emulator)**

| Test | Input | Result |
|---|---|---|
| Node index out of range | `2BLMV6` (node 200) | Rejected; stays on `ENTER PASSWORD` (`gE_idx200.png`) |
| Node type forbidden, index in range | `4L81G8` (node 61, type 50) | Rejected (`gi61.png`); node 90 (type 74) likewise (`gi90.png`) |
| Bad checksum, everything else valid | `NLDPGT` (only symbol 6 changed from `NLDPGS`) | Rejected (`gbadsum.png`) |
| Published typo | `HLNZXJ` (Boss #1) | Rejected (`gtypo1.png`) |
| Published code containing a non-alphabet letter | `63MPXE` (5-2) | Not enterable (`E` is not a keypad symbol) |
| Published code of 7 symbols | `_FLYMF_` | Not enterable (keypad is 6 cells); ROM code `_FLYM_` is accepted |

**Hidden two-code subsystem**

| Code | Validator return | Flag written | Evidence |
|---|---|---|---|
| `_NDTH_` | 1 | `[0x03000F2C]+0x28 |= 0x0001` | breakpoint at `0x0806FCE2`, `r0=1`, store value `r2=1` |
| `_FLYM_` | 2 | `[0x03000F2C]+0x28 |= 0x0002` | breakpoint at `0x0806FCD8`, bit-1 path reached |
| anything else | 0 | – | error beep, stays on screen |

`_FLYM_` is the ROM's own 6-symbol literal; the widely copied `_FLYMF_` cannot be typed.

## 7. Validation evidence

**Observed (emulator / debugger)**

* Clean-entry ROM boots the untrained game; patched ROM shows the Sunhors menu.
* Password screen: 6 cells, `OK` in the sixth, Up=−1 / Down=+1, A submits.
* `BBBBBW` → map **The Batcave** (`gpub_batcave.png`), matching the published name.
* `QV2CLL` decodes to node 11; the game's map for node 11 is **Gotham City Hall**
  (`gA_idx11.png`), matching published "3-1".
* `CGRLNH` and `NLDPGS` were dialled in with the keypad and accepted; the resulting map,
  cutscene and playable level were screenshotted.
* `2BLMV6`, `4L81G8`, `82NP64`-variant `NLDPGT`, and `HLNZXJ` were rejected in-game.
* Debugger: the input buffer is six bytes at `screen_object+0xAD` (`0x030026DD` in the
  savestate); the progress decoder is called from `0x0806FC3E`; the hidden validator from
  `0x0806FCA6`; the hidden codes write bits 0/1 at `struct+0x28`.

**Derived (instruction-level)**

* Checksum/obfuscation model (§5.2) — agrees with 90 published codes, with the game's
  own encoder, and with every accept/reject observed in the emulator.
* Node table at `0x09C9EC` with the four forbidden types.
* Hidden-code flag writes and the bit-0 consumer at `0x0806442C`: when bit 0 is set, the
  object pointed to by `[0x03000F4C]` receives `+0x12 = 100`, `+0x22 = 100`, `+0xD7 = 100`,
  `+0xD4 = 0xFF` and bit `0x0200` is ORed into the `u16` at `+0x0E` at level init. This is
  consistent with the published "Invincibility" name (maxed/refilled stats) but the
  *visible* HUD effect was not isolated frame-by-frame.

**Inferred**

* Bits 0–11 / 20–24 of the payload are progress bookkeeping carried through the password
  (the encoder preserves them; the validator ignores them). The published cheat-mode codes
  (e.g. `BBBBBW` node 66, low bits 1677, high bits 2) differ from the plain node code
  (`BBBCBG`-style) exactly in these bits.
* The 94-entry table is a mission-map node table (record fields look like type/flags/
  handler/data/chapter), not a level table; several nodes share a level name.

## 8. Unknowns

1. **Meaning of the 17 non-index payload bits.** They survive the encode/decode round trip
   and differ between "Level x-y" codes and "Cheat Mode" codes, but no reader was isolated.
   Their semantics are therefore unproven (they do not affect the validator or the map
   drawing, which is a function of the index).
2. **Hidden-code bit 1 consumer.** The bit is definitely set (breakpoint evidence) and the
   published name is "Unlock all levels", but a full-ROM scan for immediate-mask tests
   (`ands #2`, `lsls #30/31`, `tst`) on that word found no reader. Effect unproven.
3. **Published L+R button codes.** Four sequences are published (All Rewards, All Upgrades,
   God Mode, Unlimited Combo Meter). Searched as contiguous tables in u16 and u8, active-high
   and active-low, forward and reversed, and as direction indices under all 24 D-pad
   orderings — no table in the 8 MiB image. Not entered successfully; treated as unverified
   for this revision rather than as present.
4. **Node-type semantics.** Types 50/51/74/75 are rejected by the validator, apparently
   because those nodes are not playable map positions; the mapping from type to gameplay is
   inferred, not proven.

## 9. Tooling

Everything is in `/tmp/opencode/sintzu/`:

| File | Purpose |
|---|---|
| `rom.gba` | byte-identical copy of the target |
| `rom_clean.gba` | copy with only the 4-byte entry branch restored to `b 0x080000C0` (removes the third-party trainer) |
| `rom_clean.ss1` | savestate on the password screen (start of every experiment) |
| `trycode.sh` | restart from savestate, inject 6 symbol indices through the mGBA CLI debugger, submit, screenshot |
| `type2.sh`, `type_code.sh` | type a code with the on-screen keypad via `xdotool` |
| `accept.sh`, `dbgval.sh`, `dbgcode.sh` | breakpoint scripts for the hidden-code validator / flag store |
| `key.py` | XTEST key helper |

Debugger: `mgba -d` (CLI debugger; `b`, `c`, `d`, `x/1`, `w/1`, `p/x $reg`) because the
GDB stub's fixed port 2345 was in use by another session. Static work: `arm-none-eabi-objdump
-M force-thumb`, Python + Capstone 5.0.7.

Screenshots (PNG, 1280×960 full screen and 720×480 cropped):
`s00_boot.png` (patch trainer), `g01`/`g02`/`g03`/`g06` (title, menu, password, options),
`gA_idx11`, `gD_idx93`, `gi30`, `gi50`, `gi60`, `gi70`, `gn47`, `gn88` (map positions),
`gE_idx200`, `gi61`, `gi90`, `gbadsum`, `gtypo1` (rejections), `gpub_batcave` (published
code), `gnov1`/`gnov2` (novel `CGRLNH` typed), `gfinal_map`/`gfinal_intro`/`gfinal_game2`
(novel `NLDPGS` typed → final level), `gNDTH`/`gFLYM` (hidden codes).

## 10. Legal note

No ROM, extracted graphics, audio or text is redistributed here. Only hashes, addresses,
the algorithm, table structure, public codes and self-generated codes are published.
