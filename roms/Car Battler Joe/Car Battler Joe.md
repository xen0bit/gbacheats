# Car Battler Joe (GBA) — Reverse Engineering Report

Report generated from a local ROM analysis on 2026-10-24.
Methodology: [`GBA_REVERSE_ENGINEERING_GUIDE.md`](../../GBA_REVERSE_ENGINEERING_GUIDE.md)

---

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Car Battler Joe/Car Battler Joe.gba` |
| Size | 8 MiB (`0x800000`) |
| Header title | `CARBATTLERJO` |
| Game code | `ACBE` |
| Maker code | `E9` |
| Software version | `0` |
| MD5 | `37a569f4b2ee0818f89117a5cc958e83` |
| SHA-1 | `5c9982a230ebf6c93b1706a242d2149fc052a37c` |
| SHA-256 | `e9d2ea68624080434d4aae30fcf0b16cca6d84c27a061d7a6b32cd4906624e4c` |

ROM addresses below are `0x08000000 + file_offset`. All findings are tied to
this exact hash; another revision may differ.

---

## 2. Executive summary

The game has **two password systems**, not one.

1. **Secret-machine passwords** — a table of 20 fixed 8-character ASCII strings
   stored in plaintext at `0x399A84`. Entering one in
   Battle League → 1P Only → Password unlocks the corresponding car.
   All 20 are publicly documented (GameFAQs, fan sites); the ROM table was
   verified to match the public list exactly.

2. **Custom-machine codes** — a general 8-character code over a 32-symbol
   alphabet ("1234KLMN5678PQRS9BCDTVWXFGHJYZ!?"), carrying a 40-bit payload
   (a body index plus four 7-bit part/stat fields) protected by a **5-bit
   checksum**. The game contains both an encoder and a decoder for this format,
   so **anyone can mint valid codes for arbitrary car configurations** — the 20
   fixed strings are only the developer presets.

The second system is the interesting surface: it is a full car editor reachable
from the normal password screen, not just a shortcut table. Evidence for it is
both static (encoder/decoder pair, alphabet, checksum) and dynamic (custom codes
generated from the reconstructed format were accepted by the emulator).

---

## 3. How to reproduce

### Emulator

```bash
sudo apt-get install -y mgba-sdl xvfb xdotool scrot imagemagick
Xvfb :99 -screen 0 1024x768x24 &
DISPLAY=:99 SDL_AUDIODRIVER=dummy mgba -3 "Car Battler Joe.gba" &
```

Default mGBA keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`,
D-pad = arrows. Hold keys ~200 ms; the password grid needs discrete presses.

### Menu path (observed)

```
Title (Start)
└─ Main menu
   └─ Battle League
      └─ 1P Only
         └─ Data entry for which?   → Guest
            └─ Select map           → Random → "This map OK?" → Yes
               └─ Use which machine?
                  └─ Password        → "Enter your machine password."
```

The entry grid is `0-9`, `A-Z`, `!`, `?`, plus `FWD / REV / ENTR / QUIT`.
After 8 characters the cursor jumps to `ENTR` automatically.

Savestate used during analysis: `Car Battler Joe.ss1`, taken at the entry
screen (Shift+F1 saves, F1 loads).

### Codes exercised

| Input | Result (observed) |
|---|---|
| `HAMA!333` | `Big Bang` — accepts the documented secret password |
| `11111118` | `Custom GV` — body 0, no parts |
| `2111111P` | `Custom GV` — body 1, different sprite |
| `4311111P` | `Custom GV` — body 67, different sprite |
| `1P611119` | `Custom GV` — body 0, field 1 = 76 (max) |
| `4RGLXYCS` | `Wrong password!` — body 67 with all four fields at 76 |

---

## 4. Address map

| File offset | ROM address | What |
|---:|---:|---|
| `0x399A84` | `0x08399A84` | Twenty 8-char passwords, 12-byte stride (8 chars + 4 NUL) |
| `0x3BDD78` | `0x083BDD78` | Password record table, 21 slots (index 0 = null), 8-byte stride |
| `0x3B04D8` | `0x083B04D8` | 68 car/body records, 16-byte stride |
| `0x3B5894` | `0x083B5894` | ASCII → tile-index map, 96 bytes (0x20–0x7F) |
| `0x3BDFF8` | `0x083BDFF8` | 32-char code alphabet |
| `0x01B0D8` | `0x0801B0D8` | `password_ptr(index)` → `u32` |
| `0x01B0E8` | `0x0801B0E8` | `name_offset(index)` → `s16` |
| `0x01B0F8` | `0x0801B0F8` | `detail_record(index)` → pointer into `0x083B04D8` |
| `0x01B114` | `0x0801B114` | `match_password(char*) → index` (1..20 or 0) |
| `0x01B160` | `0x0801B160` | `find_body(record*) → body index` (1..20 or 0) |
| `0x020F98` | `0x08020F98` | `encode_car(record*) → char*` |
| `0x0210E0` | `0x080210E0` | `decode_car(char*) → car* or 0` |
| `0x20DC0` | `0x08020DC0` | `body_count() = 68` |
| `0x20DC4` | `0x08020DC4` | `body_table() = 0x083B04D8` |

RAM used by the code path:

| Address | Use |
|---|---|
| `0x02000CE0` | 8-byte password text buffer (also the encoder output) |
| `0x02000CE8` | 6 bytes copied from the chosen body record |
| `0x02000CEE` | four `u16` part/stat values (decoder output) |

---

## 5. Algorithm

### 5.1 Record table (`0x083BDD78`)

```
struct PwRecord {      // 8 bytes, index 0 unused
    u16 seq;           // 0x0030..0x0043 ('0'..'C')
    u16 name_off;      // 0x0548..0x0637, localized name offset
    u32 password_ptr;  // -> NUL-padded 8-char ASCII string
};
```

`0x0801B0F8` multiplies `seq` by 16 and indexes the 68-entry record table at
`0x083B04D8`, so `seq` is the car's internal record id, not just a label.

### 5.2 Matching a fixed password (`0x0801B114`)

```c
int match_password(char *in) {
    for (int i = 1; i <= 20; i++) {
        char *pw = password_ptr(i);
        int ok = 1;
        for (int j = 0; j < 8; j++)
            if (in[j] != ascii_to_tile(pw[j])) { ok = 0; break; }
        if (ok) return i;
    }
    return 0;
}
```

`ascii_to_tile` (`0x08011C04`) maps ASCII through the 96-byte table at
`0x083B5894`; bytes outside `0x20..0x7E` collapse to space.

Consequence: comparison happens on **tile indices**, not raw ASCII. Aliases in
the map (`#`/`$`/`*`, `;`/`\`/`^`/`|`, `[`/`{`, `]`/`}`, `_`/`~`) are
interchangeable at this layer. The in-game keyboard only offers `0-9A-Z!?`,
so this is not reachable through the UI, but it matters for RAM-injected input.

### 5.3 The custom-machine code

Alphabet (32 symbols, 5 bits each):

```
1234KLMN5678PQRS9BCDTVWXFGHJYZ!?
```

Payload: five 7-bit fields = 35 bits, split into seven 5-bit characters.
Character 8 is a checksum.

Field layout:

| Field | Bits | Meaning (derived) |
|---|---|---|
| 0 | 7 | body index, must be `< 68` |
| 1–4 | 7 each | part/stat words, stored biased (`0` stays `0`, `n>0` becomes `n-1`; decoder restores `n+1`) |

Decoded values above 75 are rejected. Because of the bias, `0` and `1` encode
identically — `11111118` is the code for "no parts" and for "part value 1".

#### Encoder (`0x08020F98`)

```python
ALPHABET = "1234KLMN5678PQRS9BCDTVWXFGHJYZ!?"

def encode(body, f1, f2, f3, f4):
    fields = [body] + [0 if v == 0 else v - 1 for v in (f1, f2, f3, f4)]
    bits = 0
    for i, v in enumerate(fields):
        bits |= (v & 0x7F) << (7 * i)
    ch = [(bits >> (5 * k)) & 0x1F for k in range(7)]
    ck = 11
    for i in range(6):
        ck = (ck ^ ch[i]) if (i & 1) else ((ck + ch[i]) & 0xFF)
    ch.append(ck & 0x1F)
    return "".join(ALPHABET[c] for c in ch)
```

The routine first checks `find_body()`; if the car matches one of the 20 preset
records it simply returns that preset's string instead of generating a code.
So the presets are a fast path, not a different format.

#### Decoder (`0x080210E0`)

```python
def decode(code):
    if (idx := match_password(code)) != 0:
        return preset(idx)                 # fixed secret-machine path
    v = [ALPHABET.index(c) for c in code]  # via tile conversion, not raw ASCII
    ck = 11
    for i in range(6):
        ck = (ck ^ v[i]) if (i & 1) else ((ck + v[i]) & 0xFF)
    if (ck & 0x1F) != v[7]:
        return None
    bits = 0
    for k in range(7):
        bits |= v[k] << (5 * k)
    fields = [(bits >> (7 * i)) & 0x7F for i in range(5)]
    if fields[0] >= 68 or any(f > 75 for f in fields[1:]):
        return None
    return fields
```

Only 5 checksum bits protect the format, so roughly 1 in 32 random strings
passes the checksum; the body/field range checks reject most of the rest.

---

## 6. Tables

### 6.1 The 20 secret-machine passwords

Ordered by table index. `seq` is the internal record id (`0x30`–`0x43`);
the car name is the one the game displays, as reported by the public lists.

| # | seq | Password | Car |
|---:|---|---|---|
| 1 | `0` | `BOM!BOM!` | WNN Special |
| 2 | `1` | `TK000056` | Takah's LSR |
| 3 | `2` | `MARRON!!` | MRIN's Dream |
| 4 | `3` | `KINNIKU!` | MSSL Dolly |
| 5 | `4` | `MR!HURRY` | Matsu K MK4 |
| 6 | `5` | `90!60!92` | Millennium 90 |
| 7 | `6` | `8998981!` | Issue X |
| 8 | `7` | `HAMA!333` | Big Bang |
| 9 | `8` | `CUREWAND` | Cavalier |
| 10 | `9` | `GO!HOME!` | Piston GH |
| 11 | `:` | `M!M!M!M!` | Mega M |
| 12 | `;` | `CDMACAPA` | Copa Zone 23 |
| 13 | `<` | `GANKOMAX` | MAX-K |
| 14 | `=` | `NAGOYADB` | Long Valley Z |
| 15 | `>` | `!KOKICHI` | Casey's WHLS |
| 16 | `?` | `TODOROKI` | Jim Joe Zero |
| 17 | `@` | `RED!GUNS` | Solid Wind |
| 18 | `A` | `SHISYO!!` | Blue Gate EV |
| 19 | `B` | `GUARANT!` | Queen Dohmo |
| 20 | `C` | `EMPIRE!!` | EMP Force X |

`TODOROKI` is also the "Battle League password" mentioned in community notes;
here it is simply index 16 of the same table.

### 6.2 Code alphabet

```
index: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
char:  1  2  3  4  K  L  M  N  5  6  7  8  P  Q  R  S
index:16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31
char:  9  B  C  D  T  V  W  X  F  G  H  J  Y  Z  !  ?
```

The excluded letters spell the vowel set + a few others (no A/E/I/O/U), which
keeps codes readable and avoids ambiguous glyphs.

### 6.3 Body table

68 records of 16 bytes at `0x083B04D8`. The first six bytes are the body
identity compared by `find_body`; the next eight bytes are the four default
part words.

Two indexings reach the same array:

* a custom code's field 0 is a direct body index `0..67`;
* a password record's `seq` (`0x30..0x43`) is multiplied by 16 and added to the
  base, i.e. the 20 preset cars are body records **48..67**.

So preset bodies are not special-cased in the table — the 20 secret machines
occupy the top of the same 68-entry array, and a custom code can reference the
same records with different part fields.

---

## 7. Validation evidence

**Observed (emulator, savestate at the entry screen)**

- `HAMA!333` → screen titled `Big Bang`, caption `Password:HAMA!333`.
- `11111118` → `Custom GV` (custom sprite).
- `2111111P`, `4311111P`, `1P611119` → `Custom GV` with distinct sprites.
- `4RGLXYCS` → `Wrong password!`.

**Derived (disassembly)**

- The 20-entry table, its record layout and the exact string bytes.
- `match_password` comparing 8 characters through the tile map.
- The encoder/decoder pair, alphabet, bit packing and 5-bit checksum.
- Range checks: body `< 68`, fields `<= 75` after decoding.

**Inferred**

- Field semantics (body vs. parts vs. paint) from the bias and the 16-byte
  body records; the exact part slots were not exercised one by one.
- Why body 67 with all four fields at 76 is rejected: the decoder's checks pass,
  so a later car-construction check rejects the combination. Not isolated.

---

## 8. Unknowns

- Meaning of each of the four 7-bit fields (parts? colour? durability?).
- Whether a custom machine obtained this way persists in save data or is
  guest-only.
- Whether all 68 body indices correspond to finished art (indices 0, 1 and 67
  render; none crashed).
- In-game UI text is not plaintext ASCII in this ROM — `strings` only surfaced
  debug-menu labels. The menu text encoding was not identified; it is likely a
  different tile map from the password map at `0x083B5894`.

---

## 9. Tooling

| Script | Purpose |
|---|---|
| `car_code.py` (this folder) | Encoder/decoder for the custom-machine format; reproduces every code in §3 |
| session scripts (not archived) | xdotool key/screenshot driver, literal/pointer/BL scans |

`car_code.py` encodes and decodes the 40-bit format and validates the checksum:

```bash
python3 "roms/Car Battler Joe/car_code.py" encode 0 0 0 0 0   # -> 11111118
python3 "roms/Car Battler Joe/car_code.py" decode HAMA!333    # -> preset Big Bang
```

No ROM, graphics or text from the game is redistributed here; only addresses,
algorithms and short identifiers needed to describe the passwords.

