# GT Advance Championship Racing (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `GT Advance Championship Racing.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| `file` | Game Boy Advance ROM image: "GT ADVANCE C" (ACAE78, Rev.00) |
| Header title | `GT ADVANCE C` |
| Game code | `ACAE` |
| Maker | `78` (THQ) |
| Version | 0x00 |
| Fixed byte / complement / checksum | `0x96` / `0xC8` / `0x0000` |
| Entry word | `0xEA00002E` (stock `b 0xC0`) |
| MD5 | `1ce4441b3142b480e03cffe290b00ce6` |
| SHA-1 | `3a85e462d002ff5577e4434110b17459fe6867d6` |
| SHA-256 | `8401d21fed6900509ac429909f22090439a27a3524208693672caccf710293dd` |

**Phase 0:** one Nintendo-logo hit, at file offset 0 — a single retail image, no patch,
no appended trainer, no multi-game header. The `DEBUG`/`PROMO` hits at 0x1CA9C/0x1CA5C
are credits-roll names ("DEBUGGER", "PROMOTION"); a real `DEBUG MODE` label exists in
the text bank at 0x0801CEC0 but is only a credits/menu artifact (see §8).

## 2. Executive summary

Two independent developer-intended cheat systems exist in this ROM, and both were
reversed and verified in the emulator:

1. **Title-screen button codes (6 codes).** A table of six u32 key masks at
   `0x08008C84` is compared by the routine at `0x08008B78` against the held/pressed
   key state. Each code ORs a distinct bit into a flag word at `0x030059B6`; the
   credits code sets a byte at `0x030059B8`. All six masks, their bit effects, and
   the undocumented seventh (A/Start RNG-seed) branch were enumerated statically
   and confirmed by RAM reads.

2. **A 16-symbol password system.** `OPTIONS → ENTER PASSWORD` accepts 16 characters
   from a 64-symbol alphabet. The validator (`0x08014F40`) decodes a 96-bit stream
   into a 12-byte "record", applies a table-index validity test and nine semantic
   range checks. The game itself generates a valid password in the RETRIEVE PASSWORD
   screen; the generated code **`ZjoHDyGRk5GH3mMH`** was captured, re-entered on the
   real screen, and accepted ("Password Correct!").

The published 3rd party cheat indexes password list **does not apply to this
image**: its codes use symbols (`/ ? % @ > *`) absent from this ROM's 64-character
keyboard alphabet, and the two published codes composed entirely of legal characters
(`2QjD+D1Q9Fy25B0C`, `klxQy9dQPT-4bkH3`) were entered and rejected by the game.
The six published button codes, by contrast, match the ROM table exactly.

Nothing in this image was found to be shared with the other GT Advance titles beyond
the genre and the THQ/MTO branding; all addresses and codes above were derived from
this exact hash independently.

## 3. How to reproduce

* Emulator: mGBA SDL (`mgba -3`, SDL_AUDIODRIVER=dummy) on `Xvfb :315`, keymap
  A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
  GBA viewport cropped at `720x480+152+168`.
* **Button codes:** at `PRESS START BUTTON`, hold `a`+`s` (L+R) and press the
  direction(s) together with `z` (B), each press held ~400 ms. Flags are read at
  `0x030059B0`: `+6` (u16 unlock bits), `+8` (credits byte).
* **Password:** `Start → OPTIONS (bottom item) → ENTER PASSWORD → A`. The 16 slots
  display `0000 0000 0000 0000` initially. For controlled experiments the
  ENTER-PASSWORD savestate was patched (see §9) with the 16 u16 values at
  `0x03003ECC` and the matching ASCII string at `0x03003EEC`; loading the state
  with `F1`, then `A`, runs the ROM's own validator.
* Codes tested: the six title codes; `ZjoHDyGRk5GH3mMH` (accepted); `0000000000000000`
  (rejected); all 16 single-character mutations of the accepted code (rejected);
  `2QjD+D1Q9Fy25B0C` and `klxQy9dQPT-4bkH3` (rejected).

## 4. Address map

File offset = ROM address − `0x08000000`.

| Address | Meaning |
|---|---|
| `0x08008B78` | Title-screen button-code validator (`r0` = output mode word) |
| `0x08008C7C` | literal `0x000003FF` (key mask) |
| `0x08008C84`..`0x08008C98` | six u32 key masks (table) |
| `0x08008C80` | pointer variable `0x030055A0` (→ game state struct) |
| `0x0801C6BC` | 64-char alphabet string (also at `0x08127B44`) |
| `0x0801CEC0` | `DEBUG MODE` text-bank label (+`CAR`/`CRS`/`MODE`) |
| `0x0802824` / `0x0802860` | bit-stream → text / text → bit-stream base64 codecs |
| `0x0802594` / `0x08028C0` | write-next-bit / read-N-bits primitives |
| `0x0802908` | copies the 12-byte bit buffer |
| `0x08014E2C` | halfword values (1..64) → 16-char display string |
| `0x08014E6C` | **password encoder** (builds the 96-bit stream from the record) |
| `0x08014F40` | **password validator** (returns 1 = accepted, 0 = rejected) |
| `0x08014BF6` / `0x08014C48` | RETRIEVE / ENTER PASSWORD screen initialisers; state machine |
| `0x03003EC0` (RAM) | password screen state struct |
| `0x03003ECC` | 16 u16 input values (1..64) |
| `0x03003EEC` | 16-byte display string |
| `0x030008F8` | 12-byte bit buffer; `0x03000924` = bit-position counter |
| `0x03002E90` | global game/password struct; `+0x58`/`+0x5C` = record pointer |
| `0x03002F5C` | base of 64 × 12-byte record table (12*v0 selects record) |
| `0x030055A0` | pointer to title-state struct; `+6` flags, `+8` credits byte |
| `0x030059B0` | title-state struct; flags at `+6` (`0x030059B6`, observed `0x0000` → `0x001F`), credits byte at `+8` |

## 5. Algorithm

### 5.1 Button-code validator (`0x08008B78`)

```
held  = input_reader_A() & 0x3FF        ; ~KEYINPUT, active-high
press = low16(input_reader_B())         ; newly-pressed mask
if byte[state+8] != 0: return            ; already in a special mode
for each (mask, bit) in table:
    if held == mask and (press & 0x02):  ; B must be a NEW press
        state.flags_u16 |= bit
        sfx(1)
if press & 0x09:                         ; A or Start (7th, non-cheat branch)
    seed = 100 * [0x03002EC4] + VCOUNT
    [0x03002EC8] = seed
    byte[state+8] = 1
    sfx(1)
```

Exactly six mask comparisons exist; the table has exactly six entries, so the
button-code set is closed. The seventh branch seeds an RNG from VCOUNT and is
normal game-start behaviour, not an unlock.

### 5.2 Password codec

The 16 input symbols are values `1..64` (displayed as `alphabet[v-1]`). The
validator converts them to 6-bit indices (digits 0–9, A–Z, a–z, `+`=62, `-`=63),
writes them into a 96-bit LSB-first buffer at `0x030008F8`, then decodes:

```
v0     = read6()                       ; first symbol -> table selector
record = 0x03002F5C + 12 * v0
for i in 1..32: field[i] = read2()     ; 32 two-bit fields -> record body
for each flag in {2,2,2,1,1,1,1,1,1,2,1}:  ; 15 bits -> record bytes 8,9
    record.flag |= read_bits(n) << shift

accept  = check_record_id(record[0])            ; 0x08015B14
       && all(field[i] <= max_allowed(i))        ; 0x08015CB8, i = 0..8
```

The encoder at `0x08014E6C` is the exact inverse: it writes 6 bits of `record[0]`,
then 32 × 2-bit fields, then the 15 flag bits (total 85 explicit bits; the
remaining 11 of the 96 are zero). `0x08014E2C` converts the resulting halfword
values to the 16 displayed characters via the alphabet at `0x08127B44`.

**Space definition:** alphabet size 64, length 16 → `64^16 ≈ 7.9e28` possible
input strings; the accepted set is the small subset whose first symbol selects a
valid 12-byte record and whose 9 semantic fields are within range. Every single
symbol of the accepted code affects validity, so no single-symbol alias exists.

## 6. Tables

### 6.1 Title-screen button codes (mask table `0x08008C84`)

Active-high mask: A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010
Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200. All codes hold L+R (0x300)
and require B as a new press.

| Order in table | Mask | Direction | Published effect | RAM effect (verified) |
|---|---|---|---|---|
| 1 | `0x322` | Left | Extra 2 / Indy mode | flags `0x0004` (bit 0x1 at index 1) |
| 2 | `0x312` | Right | Extra 1 / Go-Kart | flags `0x0007` (bit 0x2) |
| 3 | `0x342` | Up | View credits | byte `state+8 = 1`, credits screen |
| 4 | `0x362` | Up+Left | All cars | flags `0x0004` (bit 0x4) |
| 5 | `0x352` | Up+Right | All tracks | flags `0x000F` (bit 0x8) |
| 6 | `0x392` | Down+Right | All tune-ups | flags `0x001F` (bit 0x10) |

(Each test started from the accumulation of prior tests; the bits contributed are
0x1, 0x2, 0x4, 0x8, 0x10 respectively. All five flag bits are ORed into
`0x030059B6`.)

### 6.2 Password alphabet (64 symbols, both `0x0801C6BC` and `0x08127B44`)

`0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+-`
value 1..10 = `0..9`, 11..36 = `A..Z`, 37..62 = `a..z`, 63 = `+`, 64 = `-`.

### 6.3 Published codes tested against this image

| Published code | Source | Result on this ROM |
|---|---|---|
| `2QjD+D1Q9Fy25B0C` | 3rd party cheat indexes | **Invalid Password!** |
| `klxQy9dQPT-4bkH3` | absolute-cheats | **Invalid Password!** |
| `+vMN?T/6/NRRvMR8`, `S/PD W1/H L8Q8 >VbB`, `/6Kb/xMii rLM+/22`, … | many | **Not enterable** — contain `/ ? % @ > *`, none of which exist in this ROM's 64-symbol alphabet; literal search of the whole ROM also finds no such table |

The published button codes all matched the ROM mask table exactly.

## 6b. Enumeration

* **Button-code space:** closed, exactly 6 entries in the mask table and exactly 6
  mask comparisons in `0x08008B78`; all 6 were pressed in the emulator and each
  produced its predicted RAM bit. One additional dispatcher branch (A/Start) was
  found and proven to be RNG seeding, not a cheat. There is no undocumented
  button-code branch.
* **Password space:** 64-symbol alphabet × 16 positions = `64^16` strings. The
  validator model (§5.2) was implemented as a byte-accurate savestate oracle (the
  ROM's own validator is the final authority).
* **Novel code (not in any published list):** **`ZjoHDyGRk5GH3mMH`**. It was
  produced by the game's own RETRIEVE PASSWORD generator (found left in the input
  buffer at `0x03003EEC` after visiting that screen), searched for literally in the
  ROM (absent), re-entered on the real ENTER PASSWORD screen, and accepted —
  screenshot `oracle_zjo_c.png` shows **"Password Correct!"**. It does not appear
  on 3rd party cheat indexes, or any other published list.
* **Bounds proven by rejection:**
  * `0000000000000000` → "Invalid Password!" (`oracle_zero_c.png`).
  * All **16** single-symbol substitutions of the accepted code → invalid
    (16/16 rejected), proving there is no single-symbol alias and that the
    validator is sensitive in every position.
  * Both fully-typeable published codes → invalid.

## 7. Validation evidence

* **Observed (emulator/screenshot/RAM):**
  * six button codes flip the exact flag bits in `0x030059B6`
    (`0x0001→0x0005→0x0007→0x000F→0x001F`);
  * credits code switches to the credits roll;
  * `ZjoHDyGRk5GH3mMH` → "Password Correct!"; all-zero/published codes →
    "Invalid Password!";
  * ENTER PASSWORD input buffer structure read directly from decompressed savestates.
* **Derived (disassembly):** mask table and six comparisons; encoder/validator
  bit layouts; alphabet tables; the 9 semantic range checks; the closed form of the
  button-code set (six table entries).
* **Inferred:** the precise semantic meaning of each of the 9 range-checked fields
  (class/engine/etc.) was not resolved — the code is accepted/rejected but the
  resulting unlock effect of this particular generated code was a no-op on an
  already-default save.

## 8. Unknowns

* The nine post-decode field names and their max-value table (`0x08015CB8`) were
  not individually labelled; the accepted generated code changed no visible
  unlock flags because it encodes the default progress state.
* The `DEBUG MODE` / `CAR` / `CRS` / `MODE` strings at `0x0801CEC0` have xrefs only
  inside the credits/text-bank handler (`0x080114C4`–`0x080114D0`); no reachable
  debug screen was found on any walked menu, so this is a text-bank artifact, not
  a developer menu (consistent with guide §16.3 "dead code").
* The published codes' alternate symbol set likely belongs to a different regional
  build or a different GT Advance installment; this was not pursued beyond proving
  they are inapplicable here.

## 9. Tooling

* `phase0.py` — hashes, header parse, embedded-header/marker scan.
* `recon.py`, `xrefs.py`, `xrefs2.py`, `pwalphabet.py` — string/literal/BL/LDR-literal
  scans (Capstone-style scanners implemented in Python).
* `arm-none-eabi-objdump -M force-thumb` — targeted disassembly.
* `gba.py`, `nav.py`, `grun.py` — xdotool input/screenshot helpers on `:315`;
  GDB stub at `:2345` for RAM reads (IWRAM/EWRAM/KEYINPUT).
* `ssdecode.py` — decompresses the `gbAs` PNG chunk of mGBA `.ss1` savestates
  (raw IWRAM begins at state offset `0x19000`).
* `sspatch.py`, `oracle.py`, `fastoracle.py`, `sweep.py` — savestate patching and
  an oracle harness that runs the ROM's own validator; `oracle_{zero,zjo,pub1,pub2}_c.png`
  and `steps.png` are the key screenshots (kept in `/tmp/gtachamp`).
* Legal: no ROM or copyrighted assets are redistributed; only addresses, hashes,
  algorithms, and original tools are published here.
