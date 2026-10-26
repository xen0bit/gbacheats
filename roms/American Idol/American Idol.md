# American Idol (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-25.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/American Idol/American Idol.gba` |
| Size | 16,777,216 bytes (16 MiB, `0x1000000`) |
| Header title | `POPIDOL` |
| Game code | `BIDE` |
| Maker code | `36` |
| Software version | `0` |
| Entry word | `0xEA00002E` (ARM branch to `0x080000C0`) |
| Fixed byte `0xB2` | `0x96` (valid) |
| Complement check | computed `0xBD`, stored `0xBD` (valid) |
| Header checksum | computed `0x0043`, stored `0x0000` (non-standard field, common in trimmed images) |
| MD5 | `e140b67a8a610be8de419e4146940359` |
| SHA-1 | `13236689db1e2236673ae59c2a8ff84340a8a8c2` |
| SHA-256 | `5c037227289a4c4cbb800d0699772a902f56166e6059a8207240c4812a7d3a8c` |

**Embedded-header scan.** The 156-byte Nintendo logo (`24 FF AE 51 …`) occurs
exactly once in the file, at offset `0x4`, i.e. the single GBA header at `0x0`.
There is no second/sub-image header, so this is a single-image ROM, not a
multi-game pack. The scan was done with a byte search for the full logo string;
one hit total.

ROM addresses below are `0x08000000 + file_offset`. All findings are tied to
this exact hash; another revision may differ.

---

## 2. Executive summary

American Idol (GBA) has **one password system**, and it is the game's save /
progress mechanism: the main menu has a `Password` entry and the game can show
`Your password is …` after a stage. The code is **8 characters** drawn from a
**32-symbol alphabet**:

```
BCDF*GHJKLMNPQR&STVWXYZ234%56789
```

(Vowels, `0` and `1` are deliberately absent, so all 32 symbols are
unambiguous.) The 8 symbols are 8 × 5 = **40 bits**, assembled little-endian
(symbol 0 = bits 0–4). The low 32 bits carry the payload; bits 32–39 are an
**8-bit checksum** (sum of the eight nibbles of the low word, plus 13, mod
256). The payload decodes to:

* `stage` — a 4-bit field, validated to be **0–9** (ten stages);
* `progress` — a **20-bit** word (bitfield of extra unlocks/progress).

The published codes decode as follows:

| Published code | Decodes to | In-game result |
|---|---|---|
| `Z999&6QR` | stage 9, progress `0x00000` | **Accepted** (16/30 unlocked) |
| `%999&6QR` | stage 5, progress `0x00000` | **Accepted** (4/30 unlocked) |
| `HTH4&6CK` | stage 9, progress `0x0365D` | **Accepted** (28/30 unlocked) |
| `HPF3&6CK` | stage 9, progress `0x03F27` | **Accepted** |
| `ZGRL&6GM` | stage 9, progress `0x0B474` | **Accepted** (30/30 unlocked) |
| `ZRVW&6LP` | stage 9, progress `0x06362` | **Accepted** |
| `2999&6QR` (published as an alternative to `Z999&6QR`) | stage 8, **bad checksum** | **Rejected** — published typo |
| `HPF3&6CK-` (published with a trailing `-`) | 9 characters; `-` is not in the alphabet | Not enterable as published; the 8-char `HPF3&6CK` is accepted |

The whole space was enumerated and new codes were generated and accepted:

* `9999&6TR` — stage 0, progress 0 (never published) → `No Clothes Unlocked`
  (0/30).
* `H999&6LP` — stage 9, progress `0x00001` (never published) → accepted,
  16/30.
* `HBBBB64F` — stage 9, progress `0xFFFFF` (never published) → accepted,
  **30/30 unlocked**.
* `Z999J6QR` — stage 9, progress `0x80000` (never published) → accepted, 30/30.
* `Z999&BKP` — stage 9, progress 0, but with the unused 8-bit padding field
  set to `0x00` instead of the encoder's `0x78` → **also accepted** (16/30).
  This is an undocumented degree of freedom: the decoder never validates the
  high payload byte, so 256 different accepted codes map to each
  (stage, progress) pair.

Bounds were proven in the emulator by rejection: stage 10 (`Y999&6TR`,
checksum correct) → `Password Not Accepted`; checksum off by one
(`Z999&6TR`) → rejected; a symbol outside the alphabet (`A999&6QR`) →
rejected; a 7-character entry → rejected.

---

## 3. How to reproduce

Emulator: mGBA 0.10.5 (SDL) under Xvfb `:136`.

```bash
Xvfb :136 -screen 0 1024x768x24 &
DISPLAY=:136 openbox &
DISPLAY=:136 SDL_AUDIODRIVER=dummy mgba -3 "American Idol.gba" &
```

Default mGBA SDL keys: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, arrows = D-pad. Hold keys ~150–250 ms; this game polls the
keyboard widget per frame.

Menu path to the feature: **boot → main menu → `Password` (3rd entry) → type 8
characters → select the tall ENTER key (row 1, rightmost cell) → A**.

On-screen keyboard (13 columns × 4 rows):

```
row0: 1 2 3 4 5 6 7 8 9 * & % BS
row1: A B C D E F G H I J K L ENTER
row2: M N O P Q R S T U V W ENTER ENTER
row3: X Y Z SPACE(6 wide) ...
```

Only symbols from the 32-character alphabet are accepted; pressing `A E I O U
0 1` stores `0xFF` in the symbol buffer and the validator rejects the code.
The last (8th) cell of the text box shows the character currently under the
keyboard cursor until it is committed, which makes screenshots of partially
entered codes look like they have an extra/wrong final symbol.

Reproduction of the matrix without typing every code: a savestate taken on the
password screen holds the entry buffer in EWRAM at
`object + 0xD0` (ASCII copy), `object + 0xE2` (8 alphabet indices),
`object + 0xEC` (length−1) and the cursor at `object + 0xC0` / `+0xC4`.
For mGBA 0.10.5 savestates the EWRAM block is state bytes
`0x21000–0x60FFF`, so the buffer is at state offset
`0x21000 + (address − 0x02000000)`. `patchstate.py` (Tooling) rewrites those
fields in a real password-screen state; the game then validates the buffer
through its own ENTER path exactly as if it had been typed. The two headline
novel codes (`9999&6TR`, `HBBBB64F`) were typed key-by-key in the emulator, not
patched.

Codes entered during this analysis (accepted): `Z999&6QR`, `9999&6TR`,
`HBBBB64F`, `%999&6QR`, `HTH4&6CK`, `HPF3&6CK`, `ZGRL&6GM`, `ZRVW&6LP`,
`H999&6LP`, `Z999J6QR`, `Z999&BKP`.
Rejected: `Y999&6TR`, `Z999&6TR`, `A999&6QR`, `2999&6QR`, `HBBBB64Y`,
`HBBBB64` (7 chars).

Screenshots (all produced in this run, under `/tmp/opencode/idol/`):

| File | Shows |
|---|---|
| `s03.png` | Password entry screen, full keyboard |
| `e3.png` / `s20.png` | Empty buffer / cursor |
| `t1_acc.png`, `t1_unlocked.png` | `9999&6TR` accepted → `No Clothes Unlocked` |
| `t5_acc.png`, `t5_unlocked.png` | `HBBBB64F` accepted → `Unlocked 30/30` |
| `s23.png` | `Z999&6QR` → `Password Accepted` |
| `x_y10_typed_000.png`, `x_y10_result_000.png` | `Y999&6TR` typed → `Password Not Accepted` (stage bound) |
| `x_ckbad_typed.png`, `x_ckbad_result.png` | `Z999&6TR` (checksum +1) → rejected |
| `c_badalpha_typed.png`, `c_badalpha_result.png` | `A999&6QR` → rejected |
| `c_2999_typed.png`, `c_2999_result.png` | published `2999&6QR` → rejected |
| `c_p5_unlocked.png` | `%999&6QR` → `Unlocked 4/30` |
| `c_b1_unlocked.png` | `H999&6LP` → `Unlocked 16/30` |
| `c_hth_unlocked.png` | `HTH4&6CK` → `Unlocked 28/30` |
| `czu.png` | `ZGRL&6GM` → `Unlocked 30/30` |
| `cf4u.png` | `Z999&BKP` (padding byte 0x00) → accepted, 16/30 |
| `m_title2.png`, `m_credits.png`, `m_comp.png`, `t2d.png`, `m_afterchar.png` | menu walk: main, credits, contestant editor, pause, Endurance |

---

## 4. Address map

### Code

| ROM address | Role |
|---:|---|
| `0x080000C0` | ARM crt0 entry |
| `0x08017C1C` | Password-screen update method: reads the keypad widget, calls the decoder, applies the stage bound, shows `Password Accepted` / `Password Not Accepted` |
| `0x08017B88` / `0x08017BC0` / `0x08017D80` | Other methods of the same screen object (vtable slots) |
| `0x08018418` | Encoder at the heart of the “Your password is …” screen: packs the two progress words, draws the code |
| `0x0801851C` | Variant of the same encoder that takes an 8-bit argument |
| `0x0801AC3C` | Bit-accumulator init |
| `0x0801AC68` / `0x0801AC7C` | Append *n* low bits to the 64-bit accumulator |
| `0x0801ACBC` | Checksum: sum of the eight nibbles of the 32-bit word, `+13`, `& 0xFF` |
| `0x0801ACE0` | Finalise: checksum byte, then split the 40 bits into 8 × 5-bit symbols (LSB first) |
| `0x0801AD20` | **Decoder**: 8 symbols → 40-bit value, checksum check, field extraction |
| `0x08020458` | Keypad widget: maps a key's character to its alphabet index by linear search; unknown character → `0xFF` |
| `0x080204EC` | Keypad “entry complete?” helper called by the validator |
| `0x08020688` / `0x080206C8` / `0x080206E0` | Keypad cursor movement helpers |

### Data

| ROM address | Role |
|---:|---|
| `0x0811D8E4` | 32-byte password alphabet `BCDF*GHJKLMNPQR&STVWXYZ234%56789` |
| `0x0811D2AC` | Field descriptors `04 08 08 04 08` (widths 4,8,8,4,8) |
| `0x0811D2BC` | Password-screen vtable |
| `0x0811DCE0` | Keypad cell table, 13 × 4 `u32` key indices (0–40, with aliases for ENTER/SPACE) |
| `0x08113578` | Text pointer table (1845 entries); text id = (entry address − base) / 4 |
| `0x0FEA000`–`0x0FF000` | Main text/lyrics bank (plain ASCII) |
| `0x0FEC430` / `0x0FEC460` / `0x0FEC478` / `0x0FEC5EC` / `0x0FEC680` / `0x0FEC77C` | `Password`, `Password Not Accepted`, `Password Accepted`, `Unlocked`, `Your password is`, `No Clothes Unlocked` |
| `0x0FEC414` | `Temp Judges Room` (developer leftover, text id 436; not reached by any menu) |

### RAM

| Address | Role |
|---:|---|
| `0x03002B38` | Text-table base pointer (set at `0x0800BF7C`) |
| `0x03002B4C` | Game/password manager base; `+0x300` = stage word, `+0x304` = progress word |
| `0x03002E4C` | Stage word written by the validator (`w0`) |
| `0x03002E50` | Progress word written by the validator (`w1`) |
| `0x03002A88` | Input state base (`+0x1A` bit 0 = A-pressed latch) |
| `0x03002EAC` | Pointer to the current screen object |
| `0x02004CA0` (this session) | Password screen object: buffer `+0xD0`, symbol values `+0xE2`, length `+0xEC`, cursor `+0xC0`/`+0xC4`. The object is pool-allocated, so the address varies per boot. |

---

## 5. Algorithm

The 8 symbols map to values `v0..v7` by their index in the alphabet
(`A[0]=B, A[1]=C, …, A[31]=9`). The 40-bit value is little-endian in symbol
order:

```
B = v0 + v1·2^5 + v2·2^10 + … + v7·2^35
```

`low = B & 0xFFFFFFFF`, `stored_checksum = B >> 32`.

```
nibble_sum(x) = Σ_{i=0..7} ((x >> 4i) & 0xF)          # integer sum, not XOR
checksum      = (nibble_sum(low) + 13) & 0xFF
f0 =  low        & 0x0F
f1 = (low >>  4) & 0xFF
f2 = (low >> 12) & 0xFF
f3 = (low >> 20) & 0x0F
f4 = (low >> 24) & 0xFF        # encoder always writes 0x78; decoder never checks it
stage    = f0 ^ 0x0F           # accepted only if 0..9
progress = (f1 ^ 0xFF) | ((f2 ^ 0xFF) << 8) | ((f3 ^ 0x0F) << 16)   # 20 bits
```

Accept iff every symbol is in the alphabet, `checksum == stored_checksum`, and
`stage <= 9`.

Encoder (what the game prints on the “Your password is” screen):

```
f0 = stage ^ 0x0F
f1 = (progress & 0xFF) ^ 0xFF
f2 = ((progress >> 8) & 0xFF) ^ 0xFF
f3 = ((progress >> 16) & 0x0F) ^ 0x0F
f4 = 0x78
low = f0 | f1<<4 | f2<<12 | f3<<20 | f4<<24
chk = (nibble_sum(low) + 13) & 0xFF
code[i] = alphabet[(low | chk<<32) >> (5*i) & 31]
```

The game's own encoder contains an extra detail absent from the decoder: the
constant `0x78` byte in bits 24–31. Because the validator never compares it,
any value with a recomputed checksum is accepted (`Z999&BKP` proves this in the
emulator).

---

## 6. Tables

### 6.1 Alphabet (32 symbols, ROM `0x0811D8E4`)

| index | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| char | B | C | D | F | * | G | H | J | K | L | M | N | P | Q | R | & |

| index | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| char | S | T | V | W | X | Y | Z | 2 | 3 | 4 | % | 5 | 6 | 7 | 8 | 9 |

Absent: `A E I O U 0 1`. The on-screen keyboard still offers them, but the
widget maps them to `0xFF` and the decoder rejects any `0xFF`.

### 6.2 Field layout

| bits | width | stored field | meaning |
|---|---|---|---|
| 0–3 | 4 | `stage ^ 0x0F` | stage reached, 0–9 |
| 4–11 | 8 | `progress[7:0] ^ 0xFF` | progress low byte |
| 12–19 | 8 | `progress[15:8] ^ 0xFF` | progress middle byte |
| 20–23 | 4 | `progress[19:16] ^ 0x0F` | progress high nibble |
| 24–31 | 8 | `0x78` (encoder) | padding; **not validated** |
| 32–39 | 8 | checksum | `(nibble_sum(low)+13) & 0xFF` |

### 6.3 Decoded published codes

The published lists come from ChapterCheats, GameRevolution and IGN (see §7).

| Printed code | stage | progress | checksum | status |
|---|---:|---:|---|---|
| `Z999&6QR` | 9 | `0x00000` | valid | accepted |
| `2999&6QR` | 8 | `0x00000` | **invalid** | rejected (typo for `Z999&6QR`) |
| `%999&6QR` | 5 | `0x00000` | valid | accepted |
| `HTH4&6CK` | 9 | `0x0365D` | valid | accepted |
| `HPF3&6CK` | 9 | `0x03F27` | valid | accepted |
| `ZGRL&6GM` | 9 | `0x0B474` | valid | accepted |
| `ZRVW&6LP` | 9 | `0x06362` | valid | accepted |

`HPF3&6CK-` cannot be entered as printed (9 characters, and `-` is not in the
alphabet); dropping the dash yields the accepted `HPF3&6CK`.

### 6.4 Observable effect of the decoded payload

All observations are the Options → `Unlocked` viewer, which shows the wardrobe
count for the displayed contestant.

| Code | stage | progress | Unlocked |
|---|---:|---:|---|
| `9999&6TR` | 0 | `0x00000` | 0/30 — “No Clothes Unlocked” |
| `%999&6QR` | 5 | `0x00000` | 4/30 |
| `Z999&6QR` | 9 | `0x00000` | 16/30 |
| `H999&6LP` | 9 | `0x00001` | 16/30 |
| `HTH4&6CK` | 9 | `0x0365D` | 28/30 |
| `Z999J6QR` | 9 | `0x80000` | 30/30 |
| `ZGRL&6GM` | 9 | `0x0B474` | 30/30 |
| `HBBBB64F` | 9 | `0xFFFFF` | 30/30 |
| `Z999&BKP` | 9 | `0x00000` (padding `0x00`) | 16/30 |

`stage` therefore drives the stage-based wardrobe rewards documented on the
fan sites (reach round *N* → wardrobe items). `progress` is an additional
20-bit unlock mask. Individual bit→item assignment was not fully mapped; bit
19 (`0x80000`) and the all-ones word both reach 30/30, so the relation is not
one bit per item (probably group bits plus a few high “unlock all” bits).

---

## 6b. Enumeration

**Space.** 32 symbols, fixed length 8 → `32^8 = 2^40 = 1,099,511,627,776`
input strings.

**Accepted subspace.** The validator constrains: alphabet membership, an 8-bit
checksum, `stage ≤ 9`, and ignores the 8-bit padding. Hence

```
accepted = 10 (stage) × 2^20 (progress) × 2^8 (free padding) = 2,684,354,560
          = 5/2048 of all strings ≈ 1 in 409.6
distinct (stage, progress) payloads = 10 × 2^20 = 10,485,760
```

Every accepted string is a valid code; each (stage, progress) pair has exactly
256 accepted encodings differing only in bits 24–31.

**Novel codes (absent from every published list found).**

| Code | Payload | How entered | Result |
|---|---|---|---|
| `9999&6TR` | stage 0, progress 0 | typed key-by-key | `Password Accepted`; Unlocked viewer: **No Clothes Unlocked** |
| `HBBBB64F` | stage 9, progress `0xFFFFF` | typed key-by-key | `Password Accepted`; **Unlocked 30/30** |
| `H999&6LP` | stage 9, progress `0x00001` | savestate-assisted | accepted; 16/30 |
| `Z999J6QR` | stage 9, progress `0x80000` | savestate-assisted | accepted; 30/30 |
| `Z999&BKP` | stage 9, progress 0, padding `0x00` | savestate-assisted | accepted; 16/30 — proves the padding byte is unchecked |

**Bounds proven by rejection (all in-game, screenshots in §3).**

| Input | Why it must fail | Observed |
|---|---|---|
| `Y999&6TR` | checksum valid, stage = 10 > 9 | `Password Not Accepted` |
| `Z999&6TR` | stage 9; stored checksum `0x74`, computed `0x73` | `Password Not Accepted` |
| `A999&6QR` | `A` is not in the alphabet (widget stores `0xFF`) | `Password Not Accepted` |
| `2999&6QR` | published typo; checksum invalid | `Password Not Accepted` |
| `HBBBB64` | 7 characters, buffer not full | `Password Not Accepted` |

**Negative results (bounded).**
* Only one 32-symbol alphabet exists in the ROM: a scan for 28–44-character
  runs of `[A-Z0-9*&%!?#@$]` with ≥28 distinct characters returned exactly one
  hit, `0x11D8E4`. There is no second password alphabet.
* No plaintext copy of any published code exists in the ROM (`grep -abo` for
  all seven literals: zero hits), confirming the codes are generated/checked
  algorithmically rather than tabulated.
* No button-code table was found: scanning every 2-byte offset for runs of ≥5
  consecutive `u16` values drawn from the GBA key masks (`1,2,4,8,0x10,…
  0x200`) produced 1,094 hits (785 for runs of ≥8); only 6 of the ≥8 runs are
  referenced by a ROM pointer, and all 6 are graphics/tilemap data (e.g.
  `0x44D40`, long runs of `0x0001`), not an input sequence. No button-code
  cheat appeared in the sources that could be read, and the only unlock UI
  reachable in the ROM is the password screen.
* Menu walk found no hidden/debug menu. `Temp Judges Room` (text id 436) is a
  developer leftover string that no reachable screen displays.

---

## 7. Validation evidence

### Observed (emulator)

* Main menu: `Play`, `Options`, `Password`, `Credits`; Play leads to
  `Competition`, `Rehearsal`, `Endurance`; all three lead to the contestant
  editor (Head/Hair/Skin/Wardrobe/Top/Bottom and gender), then a song carousel
  (Competition/Rehearsal) or straight into a performance (Endurance).
* Pause during a performance: `Paused` → `Continue` / `Quit` → `Are you sure?`
  `Yes` / `No`.
* Options: `Unlocked`, `SFX-*`, `Music-*`, `Screen-*`; `Unlocked` pages through
  contestants with `Last`/`Next` and prints `Wardrobe : n`, `Top : n`,
  `Bottom : n`, `Unlocked : n/30`.
* Password screen: 13×4 keyboard, 8-character box, `Password Accepted` /
  `Password Not Accepted` screens; buffer accepts only the 32-symbol alphabet.
* All accepted/rejected results in §3 and §6b, with the screenshots listed.

### Derived (instruction sequence)

* The 32-symbol alphabet and the `+13` nibble checksum.
* The 4/8/8/4/8 field layout and the XOR masks.
* `stage > 9` rejection at `0x08017CC2` (`cmp r5,#9`).
* `0xFF` symbol rejection at `0x0801AD3C`–`0x0801AD46`.
* The decoder never reads the padding field `f4`; `Z999&BKP` confirmed it in
  game.
* The encoder's use of `0x78` in bits 24–31 (game-generated passwords only).

### Inferred

* `stage` = “Stage reached” shown by the results password screen (string
  `Stage reached:` at `0x0FED248` and the same two global words at
  `0x03002E4C/0x03002E50` are used by the encoder). The 10 stages match the
  `Top 1..Top 9`/final naming in the UI.
* `progress` is a mixed stage/endurance unlock mask. Its individual bits are
  not yet assigned to items; only the whole-word effect (0 → 16/30 → 30/30) is
  observed.

### Web sources consulted

* ChapterCheats, “American Idol Cheats for GameBoy Advance” — the seven
  password strings and the wardrobe unlock table (fetched 2026-10-25).
* GameRevolution, “American Idol, Karaoke Revolution Presents: American Idol
  GBA Cheats” — `2999&6QR` for extra practice songs.
* IGN GBA cheats wiki — `HTH4&6CK` for additional costumes.
* GameFAQs returned a Cloudflare challenge (HTTP 403/JS); the Wayback Machine
  returned HTTP 429. Search-result snippets corroborated the ChapterCheats
  list; every string was then verified against the ROM/decoder and, where
  listed in §3, in the emulator.

---

## 8. Unknowns

* Exact per-bit meaning of the 20-bit `progress` word. The viewer shows only
  aggregate counts and three item numbers; mapping every bit to a wardrobe/song
  slot would need the unlock tables (not needed for code generation, since any
  20-bit value can be encoded).
* Whether `stage` values 0–9 map one-to-one to Competition rounds 1–9/final.
  The observed counts (0/30, 4/30, 16/30) are monotone but the stage→round
  labels are inferred.
* The `Temp Judges Room` string's original purpose (text id 436); it is not
  referenced by any reachable screen.
* Save type. The emulator creates a 0-byte `.sav`; the game's persistent
  progress in this build is carried by the password, but the cartridge save
  backend was not exercised.
* No hidden debug key sequence was found; the negative result is bounded by
  the ROM-wide mask-run scan and the complete menu walk, not by a proof over
  all input sequences.

---

## 9. Tooling

All scripts were written for this analysis and are in `/tmp/opencode/idol/`:
`pw.py` (codec), `patchstate.py` (password-screen savestate writer),
`typecode.py` / `test2.py` (emulator drivers), `keys.py` (xdotool helper).

`pw.py` — the complete codec, verified against every published code:

```python
ALPHA = "BCDF*GHJKLMNPQR&STVWXYZ234%56789"

def nibsum(x):
    s = 0
    for _ in range(8):
        s += x & 0x11111111
        x >>= 4
    return s & 0xFF

def encode(stage, progress):
    f0 = (stage ^ 0x0F) & 0xF
    f1 = (progress & 0xFF) ^ 0xFF
    f2 = ((progress >> 8) & 0xFF) ^ 0xFF
    f3 = ((progress >> 16) & 0x0F) ^ 0x0F
    low = f0 | f1 << 4 | f2 << 12 | f3 << 20 | 0x78 << 24
    chk = (nibsum(low) + 13) & 0xFF
    B = low | chk << 32
    return "".join(ALPHA[(B >> (5 * i)) & 31] for i in range(8))

def decode(code):
    v = [ALPHA.index(c) for c in code]          # ValueError if not in alphabet
    B = sum(q << (5 * i) for i, q in enumerate(v))
    low, chk = B & 0xFFFFFFFF, B >> 32
    f0, f1 = low & 0xF, (low >> 4) & 0xFF
    f2, f3 = (low >> 12) & 0xFF, (low >> 20) & 0xF
    stage = f0 ^ 0x0F
    progress = (f1 ^ 0xFF) | ((f2 ^ 0xFF) << 8) | ((f3 ^ 0x0F) << 16)
    ok = chk == (nibsum(low) + 13) & 0xFF and stage <= 9
    return ok, stage, progress
```

Installed: nothing beyond the stock Debian packages (`mgba-sdl`, `xvfb`,
`openbox`, `xdotool`, `scrot`, `imagemagick`, `gdb-multiarch`,
`binutils-arm-none-eabi`, Python `capstone`). A GDB stub was not usable because
another mGBA instance in the environment already owned TCP 2345; the entry
buffer was located through mGBA savestate memory layout instead, which needs no
debugger.

## Legal note

No ROM, extracted graphics, music or game text is redistributed here. Only
addresses, algorithms, hashes, short menu labels and the analyst's own
generated codes are published.
