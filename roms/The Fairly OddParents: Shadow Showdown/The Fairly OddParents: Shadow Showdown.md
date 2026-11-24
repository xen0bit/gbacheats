# The Fairly OddParents: Shadow Showdown (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/The Fairly OddParents: Shadow Showdown/The Fairly OddParents: Shadow Showdown.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `FAIRLYODDAGB` |
| Game code / maker | `BF2E` / `78` (THQ; Helixe developed the GBA SKU) |
| Version | 0x00 (USA, AGB-BF2E-USA) |
| Entry word | `0xEA000031` (normal ARM branch to `0x080000CC`) |
| Header checksum / complement | `0x0000` / `0x7B` (byte sum `0x6C` expects `0x94`) — rebuilt-header artifact (guide §16.1); no cracktro or trainer observed |
| MD5 | `2d7e907c4e4741f1a2fcf4c4caae030e` |
| SHA-1 | `6dcab3a6a888cc992e0b9432b828e692424e404b` |
| SHA-256 | `e560a4e55220805d3590284c5953f7c5ffe3a0f32785bf14caddf00e7134dc6c` |

Web recon (3rd party cheat indexes, the 3rd party cheat indexes unlockables page) found **no published GBA cheat/password list** for this title; the widely published button codes belong to the PS2/GC build, and the 8-character passwords belong to the earlier *Breakin' Da Rules* GBA game. Treat those as different SKUs (guide §16.11). Fetched pages were treated as data only; no instruction-like content was acted on.

## 2. Executive summary

The GBA game has a real, developer-intended **PASSWORD** screen on the main menu. It accepts 6-character codes drawn from a 32-symbol alphabet `BCDFGHJKLMNPQRSTVWXYZ123456789!?`. Two independent code families live behind that one screen:

1. **Four hard-coded developer codes** (`BLVVVV`, `DNPYZQ`, `7B45XV`, `BRNTHM`) compared by `strcmp` against a 4-entry table. Each directly sets one persistent unlock bit at `0x0201D54C..0x0201D54F` (indices 0–3 respectively) and bypasses all algorithmic validation.
2. **An algorithmic 25-bit state-password system**. The six characters are packed to 30 bits, permuted, XOR-whitened, and masked to 25 bits. Seven bit-fields are extracted and range-checked; an accepted code writes the fields into a state struct at `0x0201D0B0` and starts the corresponding game state. The game also contains the matching *generator* (`0x080298B0` → `0x08029B58`), so the password is its normal progress-transfer feature, not a cheat device code.

I reversed both paths, enumerated the full space (858,000 valid 25-bit states; 27,456,000 accepted 6-character codes plus the 4 hard-coded ones), minted novel algorithmic codes, entered them on the real screen, and confirmed the resulting RAM state and screen transitions. Rejection bounds were proven with three out-of-range codes that the game refused.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, 3× scale.
* Keymap (mGBA SDL defaults): D-pad = arrow keys, A = `x`, B = `z`, Start = `Return`.
* Path: boot → title → `Start` → **Main Menu** (NEW GAME / PASSWORD / OPTIONS / CREDITS) → select **PASSWORD** → `A`.
* The keypad is a 4×8 grid of the 32 alphabet symbols; D-pad wraps within a row and within a column. `A` selects a character; after the **6th** character the game validates immediately. `B` deletes the last character; when the buffer is empty `B` returns to the main menu.
* Save a state on the password screen (Shift+F1) to make each trial one load + six selections.
* Accepted algorithmic code: `46Q!4B` → gameplay starts, state struct gets `f0=49,f1=8,f2=7,f3=2,f4=20,f5=5,f6=10`.
* Accepted algorithmic code: `LB?XSV` → transitions to the in-game credits screen.
* Rejected: `BL?6SV` (`f6=11`), `BB?D!V` (`f3=3`), `GB?2NV` (`f0=50`) — code remains displayed, no state/flag change.

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`); file offsets in the analysis scripts match directly.

| Address | Role |
|---|---|
| `0x08024A60` | Password-screen input handler (cursor, char entry, submit on count==6) |
| `0x080292B8` | State-word → field struct decoder + range validator (returns 0/1) |
| `0x08029364` | Apply accepted algorithmic password: copy fields to `0x0201D0B0+8..+14`, fire unlocks |
| `0x08029778` | Store trigger byte / screen transition |
| `0x0802988C` | Field packer (struct → 25-bit word) |
| `0x080298B0` | In-game password generator (calls encoder `0x08029B58`) |
| `0x08029B58` | Encoder: 25-bit word → 6-character string |
| `0x08029BC0` | Hard-coded-code matcher (`strcmp` loop over the 4-entry table) |
| `0x08029BF8` | Decoder: 6-character string → 25-bit word |
| `0x08029C8C` | Character → alphabet-index helper (`strchr`-based) |
| `0x0802A9F0` / `0x0802AA14` | Set persistent unlock flag bit |
| `0x08041EA4` / `0x08041F30` | `strchr` / `strcmp` (confirmed by disassembly) |
| `0x083093D0` | 32-byte alphabet `BCDFGHJKLMNPQRSTVWXYZ123456789!?` |
| `0x083093F0` | 4-entry pointer table (order: `BLVVVV`, `DNPYZQ`, `7B45XV`, `BRNTHM`) |
| `0x08044420` | Hard-coded code strings, 8-byte stride: `BRNTHM`, `7B45XV`, `DNPYZQ`, `BLVVVV` |
| `0x08309404` | 30-byte encoder permutation `T1` |
| `0x08309422` | 30-byte decoder permutation `T2` = inverse of `T1` |
| `0x0201D058` | Six-character input buffer copy (`BRNTHM` observed as `42 52 4E 54 48 4D 00`) |
| `0x0201D0B0` | Password state struct; `+8..+14` = `f0,f1,f2,f3,f4,f5,f6` after accepted code |
| `0x0201D54C..4F` | Persistent unlock bits set by the four hard-coded codes |

Literal constants recovered from the literal pools (all verified with `struct.unpack_from`, not from objdump's halfword rendering):

* XOR whitening key `0x2CA59635`
* Payload mask `0x01FFFFFF` (25 bits, bits 0–24)
* Permutation-range check constant `0x3FFFFFFF`

## 5. Algorithm

### 5.1 Character → payload

```
alphabet = "BCDFGHJKLMNPQRSTVWXYZ123456789!?"          # 32 symbols, index 0..31
idx[c] = position of c in alphabet                    # via strchr at 0x08041EA4
packed = Σ_{i=0..5} idx[code[i]] << (5*i)              # 30-bit value
```

### 5.2 Decoder (`0x08029BF8`)

```
w = 0
for i in 0..29:
    if packed has bit i: w |= (1 << T2[i])             # inverse permutation
assert (w & 0x3FFFFFFF) == w                           # permutation sanity check
state = (w ^ 0x2CA59635) & 0x01FFFFFF                  # 25-bit payload
```

### 5.3 Field extraction and validation (`0x080292B8`)

```
f6 = (state >>  0) & 0x1F     # bits 0..4
f5 = (state >>  5) & 0x07     # bits 5..7
f4 = (state >>  8) & 0x1F     # bits 8..12
f2 = (state >> 13) & 0x07     # bits 13..15
f3 = (state >> 16) & 0x03     # bits 16..17
f0 = (state >> 18) & 0x7F     # bits 18..24
f1 = class(f0):               # 0:0-4, 1:5, 2:6-14, 3:15-21, 4:22-30,
                              # 5:31-34, 6:35-43, 7:44-46, 8:47+

accept iff  f1 <= 8  and f0 <= 49  and f2 <= 7  and f4 <= 20
        and f4 <= 4*f5  and 1 <= f5 <= 5  and f3 <= 2  and f6 <= 10
```

`0x08029364` re-checks the identical predicate and then copies `f0..f6` (with `f1`) into `0x0201D0B8..+14`. Field *names* are structural labels from the bit layout; their game-facing meaning (level, character, difficulty, etc.) was not proven and is left as **Inferred**.

### 5.4 Encoder (`0x08029B58`, called by `0x080298B0`)

```
r = (state ^ 0x2CA59635) & 0x01FFFFFF
p = 0
for j in 0..29:
    if r has bit j: p |= (1 << T1[j])
code = ''.join(alphabet[(p >> (5*i)) & 31] for i in 0..5)
```

The generator always emits the canonical spelling with packed bits 25–29 zero; the validator does not require those five bits to be zero (see §6b).

### 5.5 Hard-coded path

On the 6th character `0x08024C66` calls `0x08029BC0`; if it returns an index `>= 0`, the game plays sound 18, clears the six display slots and calls `0x0802A9F0(index)`, which sets byte `0x0201D54C + index` to 1 if clear. This path never touches the decoder — all four strings decode to words that **fail** the algorithmic field checks, confirming they are separate developer shortcuts.

## 6. Tables

### Alphabet and permutations

```
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ123456789!?"

T1 @ 0x08309404 = [3,8,13,18,23,28,1,6,11,16,21,26,10,4,9,14,
                   19,24,29,2,7,12,17,22,27,0,5,25,15,20]
T2 @ 0x08309422 = [25,6,19,0,13,26,7,20,1,14,12,8,21,2,15,28,
                   9,22,3,16,29,10,23,4,17,27,11,24,5,18]
```

Both are bijections of `0..29`; `T2 == inverse(T1)` (verified in Python).

### Hard-coded codes (file offset `0x44420`, table `0x083093F0`)

| Table index | Code | Flag set | RAM after entry |
|---:|---|---|---|
| 0 | `BLVVVV` | `0x0201D54C = 1` | input buffer `42 4C 56 56 56 56 00` |
| 1 | `DNPYZQ` | `0x0201D54D = 1` | input buffer `44 4E 50 59 5A 51 00` |
| 2 | `7B45XV` | `0x0201D54E = 1` | input buffer `37 42 34 35 58 56 00` |
| 3 | `BRNTHM` | `0x0201D54F = 1` | input buffer `42 52 4E 54 48 4D 00` |

None of these four strings appears in any published GBA list for this game (3rd party cheat indexes, general web search); they are reported here for the first time.

### Class thresholds

| `f0` range | 0–4 | 5 | 6–14 | 15–21 | 22–30 | 31–34 | 35–43 | 44–46 | 47–49 |
|---|---|---|---|---|---|---|---|---|---|
| `f1` | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |

## 6b. Enumeration

### Space definition

* Raw payload: 25 bits = **33,554,432** states (`0..0x01FFFFFF`).
* Valid states after all range checks: **858,000**. Confirmed two ways — combinatorially (`50 × 8 × 3 × 65 × 11`, where 65 = Σ₍f5=1..5₎(min(20,4·f5)+1)) and by a C brute-force over all `2^25` words.
* Aliases: the mask discards bits 25–29 of the permuted 30-bit value, so **32 distinct 6-character codes decode to each accepted state** (guide §16.4b). The game's own generator emits only the canonical spelling.
* Total accepted on the real screen: **27,456,000 algorithmic codes + 4 hard-coded codes**.

### Novel codes generated and confirmed in-game

| Code | Fields (`f0,f1,f2,f3,f4,f5,f6`) | Published? | In-game result | RAM proof |
|---|---|---|---|---|
| `46Q!4B` | `49,8,7,2,20,5,10` | No (minted from the validator) | Accepted; gameplay starts directly (castle level, timer 1:00) | `0x0201D0B8` = `31 08 07 02 14 05 0A`; input buffer `34 36 51 21 34 42 00` |
| `LB?XSV` | `0,0,0,0,1,1,0` | No | Accepted; transitions to the in-game credits screen | input buffer `4C 42 3F 58 53 56 00`; state fields written |

`46Q!4B` deliberately exercises the maximum of every field (`f0=49`, `f4=20`, `f5=5` so `f4=4·f5`, `f6=10`) — a combination absent from any list and never emitted by ordinary play at the title screen.

### Bounds proven by rejection

| Code | Intended field | Violation | Observed result |
|---|---|---|---|
| `BL?6SV` | `f6=11` | `f6 > 10` | Rejected — code stays in the display, no screen change, no flag or state change |
| `BB?D!V` | `f3=3` | `f3 > 2` | Rejected — same |
| `GB?2NV` | `f0=50` | `f0 > 49` | Rejected — same |

Each rejection was captured both as a screenshot (password screen with the code still visible) and as a savestate RAM diff against the clean password-screen baseline (unlock flags and state struct unchanged). These bound the field ranges independently of the checksum/permutation layer; a bad *character* is additionally impossible to submit because the on-screen keypad exposes only the 32-symbol alphabet.

### Validator-as-oracle cross-check

The Python models `pw.py` (`decode_code`, `encode_word`, `valid`) agree with the ROM on all four published/hard-coded strings, both accepted novel codes, and all three rejected codes. Encoding a decoded word reproduces the same code for payloads inside the 25-bit mask (round-trip verified for every generated code above).

## 7. Validation evidence

* **Observed** — emulator screenshots of the title, main menu, PASSWORD keypad, OPTIONS, CREDITS, accepted gameplay (`46Q!4B`), accepted credits transition (`LB?XSV`), and three rejections. Savestate RAM diffs (`ssdiff.py`, decompressing the `gbAs` PNG chunk) gave the flag writes, input-buffer bytes, and the exact state-field struct.
* **Derived** — disassembly of `0x080292B8`, `0x08029364`, `0x080298B0`, `0x0802988C`, `0x08029B58`, `0x08029BC0`, `0x08029BF8`, `0x08024A60`, `0x0802A9F0`; literal-pool values re-read with `struct.unpack_from`; tables dumped at their ROM addresses; brute-force count of the valid space.
* **Inferred** — human-readable meanings of `f0..f6` (likely level/index, group, difficulty, counters) were not established; the report keeps the structural bit-field names only.

## 8. Unknowns

* The exact bonus content gated by unlock bits 0–3 was not played to completion; the bits are proven to be set and persist, but their on-screen reward mapping is not enumerated.
* The semantic mapping of the seven password fields to level/character/counters was not confirmed by gameplay observation. `f1` is definitely the derived class of `f0` (its value `8` appeared in RAM for `f0=49`), but what `f1` drives is unknown.
* The header checksum/complement mismatch is consistent with a rebuilt header; the underlying retail revision could not be identified from the image alone.
* `LB?XSV` reached the credits screen; whether that is the intended semantics of `f0=0` or a fallback for an out-of-content state was not separated.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
* Python + capstone for literal/BL/xref scans; `pw.py` (encoder/decoder/validator model), `enter.py` (grid navigation and code entry), `ssdiff.py` (savestate `gbAs` diff).
* `count.c` / `count2.c` — combinatorial and brute-force counts of the valid payload space.
* REA skill was loaded; for a raw GBA image the practical path remained objdump + mGBA as directed by the guide.
* No copyrighted ROM text or graphics are redistributed here; only addresses, constants, hashes, and self-generated codes are published.
