# Yu-Gi-Oh! GX: Duel Academy (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Yu-Gi-Oh! GX: Duel Academy.gba` |
| Size | 33,554,432 bytes (0x02000000, 32 MiB) |
| Header title | `YUGIOHGXDA` |
| Game code / maker | `BYGE` / `A4` (Konami), `file(1)` reports "BYGEA4, Rev.00" |
| Version byte | 0x00 (at 0xBC); complement 0x00, checksum 0x0000 (rebuilt-header signature) |
| Entry word | `0xEA00002E` → 0x080000C0 (stock crt0, no cracktro patch) |
| MD5 | `f62c47cbe08e1e3bcfcf9f1b84841a76` |
| SHA-1 | `57d6bb789833b62b360072902982d5f1011b3640` |
| SHA-256 | `0c2f606986c84d584510d0b80e7cb8e2970f9c15c71d29f9bb9d5f67ceef2afe` |

All addresses below are for this exact revision. File offset = ROM address − 0x08000000.

## 2. Executive summary

The game has one developer-intended cheat surface: the **Card Password Machine** in the
Shop (map: Duel Academy node → sub-location "Shop" → shopkeeper → "Use Password Machine.").
It accepts exactly **8 decimal digits** and awards a specific card for 1000 DP on first use.

The accepted set is a **closed lookup table of 1200 passwords**, not a checksum algorithm.
Each table entry is a u32 stored XOR-obfuscated with a tiny MSVC-style LCG; the validator
linearly scans all 1200 entries and returns the matching 1-based index. The card's internal
ID comes from a parallel u16 table. Decoding the table with the recovered key yields 1200/1200
valid 8-digit strings, and 10 independently known real Yu-Gi-Oh card passwords appear in it
(Blue-Eyes White Dragon, Dark Magician, Exodia, Red-Eyes B. Dragon, Pot of Greed, Mirror Force,
Black Luster Soldier, Cyber Dragon, Dark Magician Girl, Dark Paladin, Blue-Eyes Ultimate) —
which proves the decoder.

Two passwords that are not among those famous/published examples were minted from high table
indices and accepted in the emulator: `31000575` (card **CONSCRIPTION**, internal ID 6447)
and `44729197` (internal ID 6386). Re-entering `31000575` after purchase yields "You have
already used this password.", proving the game recorded it. An out-of-set code (`12345678`)
is rejected with "The card password is incorrect or cannot be used in this game." and no DP
charge.

No button-code sequence, debug menu, or second password alphabet was found; the search
boundaries are stated in §8.

## 3. How to reproduce

1. Emulator: mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, `mgba -3 game.gba`.
   Keymap used: D-pad = arrow keys, A = `x`, B = `z`, Start = `Return`.
2. Play the intro, create a name, clear the tutorial duel + tutorial list, and reach the
   field map (a savestate at this point is strongly recommended).
3. Map: from "Slifer Red Dorm" press **Right, Right** to reach **Duel Academy**.
   Press **A** to open its sub-location list, then **Down ×6** to highlight **Shop**, **A, A**
   to enter. Talk to the shopkeeper → **A** → "What would you like?" menu →
   **Down** → "Use Password Machine." → **A**.
4. The machine shows eight digit wheels. **Down** increments the current digit
   (0→1…9→0); **Up** decrements (0→9). **Right**/Left move between wheels.
   Defaults are all zero. Press **A**, then **Start** to submit.
5. Known-good decoder check: enter `89631139` (Blue-Eyes White Dragon). First use shows the
   card and a 1000 DP charge; second use shows "You have already used this password."
6. Novel-code check: from a fresh state with ≥1000 DP, enter `31000575`, submit
   (A then Start) → "You need 1000 DP to acquire this card. Will you pay?" with the card
   **CONSCRIPTION** shown → A ("Yes") → DP 2900 → 1900, card acquired. Re-enter the same
   code → "You have already used this password."

Screenshots for every step are in `/tmp/opencode/yugiohgx/` (e.g. `pwent_c.png`,
`clean_confirm2_c.png` showing CONSCRIPTION + the 1000-DP prompt, `clean_acquired_c.png`,
`reuse3_c.png` showing the already-used rejection, `invstart_c.png` showing the invalid-code
rejection).

## 4. Address map

| Address | Size | Meaning | Evidence |
|---|---:|---|---|
| 0x0202B0C0 | 8 bytes | Password digit buffer (one byte per wheel, values 0–9) | Derived from 0x080D5B88; **Observed** in `.ss1` raw state: `08 09 06 03 01 01 03 09` after entering `89631139` |
| 0x02003848 | u16 | Duel Points; 0x0B54 (2900) before, 0x076C (1900) after a purchase | **Observed** by diffing savestates `game.ss7`/`game.ss8` |
| 0x087A8620 | u16 | Password count = **1200** | Derived from literal at 0x080DD8A8 (count pointer) |
| 0x087A8624 | u16 × 1200 | Internal card IDs parallel to the password table (e.g. arg 1 → 4007, arg 1198 → 6447) | Derived from literal at 0x080D5B38 / table dumps |
| 0x087A8F88 | u32 × 1201 | XOR-obfuscated password table; entry 0 = unused sentinel, entries 1..1200 = accepted passwords | Derived from literal 0x087A8F88 at 0x080DD878 |
| 0x080D5B88 | func | Submit wrapper: reads 8 bytes at 0x0202B0C0, packs 4 bits/digit, calls validator, handles result/price flags | Derived (Thumb disassembly) |
| 0x080DD87C | func | Validator: linear scan arg = 1..count, returns index or 0 | Derived |
| 0x080DD860 | func | Decrypt one table entry (`table[arg] ^ key(arg)`) | Derived |
| 0x080DD84C | func | XOR helper | Derived |
| 0x080DD830 | func | LCG key generator (constants 0x343FD / 0x269EC3) | Derived |
| 0x0946D766 | string | "The card password is incorrect or cannot be used in this game." | Observed in emulator |
| 0x0946D7A6 | string | "You cannot acquire this card from the password machine." | Derived (table) |
| 0x0946D7DE | string | "You have already used this password." | Observed in emulator |
| 0x0946D804 | string | "You need %d DP to acquire this card." | Observed |
| 0x0946D876 | string | "Use Password Machine." (shop menu) | Observed |
| 0x097F37EC | table | Message table holding the three password-result strings at +4/+8/+C | Derived |

## 5. Algorithm

Pseudocode, bit-exact (all arithmetic 32-bit unsigned, GBA little-endian):

```python
A, B = 0x343FD, 0x269EC3

def key(arg):                      # 0x080DD830
    return ((((A * arg + B) & 0xFFFFFFFF) >> 16) & 0xFFFF) | \
           ((B << 16) & 0xFFFFFFFF)

def table_word(arg):               # literal 0x087A8F88, 1-based arg
    return u32(0x087A8F88 + 4 * arg)

def expected_packed(arg):          # 0x080DD860 / 0x080DD84C
    return table_word(arg) ^ key(arg)

def pack(digits):                  # 0x080D5B88
    # digits[0] is the LEFTMOST wheel; bytes are 0..9.
    # The ROM loop is: r2 = (r2 << 4) + digit[i]  (MSB-first accumulation).
    p = 0
    for i in range(8):
        p = ((p << 4) | digits[i]) & 0xFFFFFFFF
    return p

def validate(digits):              # 0x080DD87C
    p = pack(digits)
    count = u16(0x087A8620)        # 1200
    for arg in range(1, count + 1):
        if expected_packed(arg) == p:
            return arg             # 1-based table index, 0 = reject
    return 0

def card_id(arg):                  # parallel table
    return u16(0x087A8624 + 2 * arg)
```

Notes:

* `0x080DD830` uses `muls` + `adds` + `lsrs #16` + `lsls #16` + `orrs`; the high halfword of
  every key is the constant `0x9EC3`, and the low halfword is `(0x343FD*arg + 0x269EC3) >> 16`.
  These are the classic MSVC `rand()` LCG constants.
* The validator scans **arg = 1..1200**; arg 0 is an invalid sentinel
  (its decoded word contains nibbles 10–15). All 1200 scanned entries decode to eight
  decimal digits.
* The eight hex digits of `expected_packed(arg)`, MSB first, are exactly the eight wheels
  to type. Example: arg 1 gives `0x89631139`, so the wheels are `8 9 6 3 1 1 3 9`;
  this was confirmed in-game (the digit buffer at 0x0202B0C0 read back as
  `08 09 06 03 01 01 03 09` and the game accepted it as the Blue-Eyes White Dragon
  password). `decode_final.py` prints nibbles least-significant first, so the
  wheel-order password is the reverse of that printed string.
* Rejection paths in 0x080D5B88: index 0 → result state 1 (incorrect password); a
  previously-used flag → result state 3 (already used); price check → result state 2
  (cannot acquire / insufficient DP).

## 6. Tables

| Field | Value |
|---|---|
| Input alphabet | decimal digits 0–9 only, exactly 8 wheels; no letters or symbols |
| Input buffer | 8 bytes at EWRAM 0x0202B0C0 |
| Packing | 4 bits per digit, leftmost wheel in the most-significant nibble (`p = (p<<4)|digit`) |
| Table entries | 1200 accepted (arg 1..1200) plus 1 unused sentinel (arg 0) |
| Table storage | `u32[1201]` at 0x087A8F88, each word XORed with `key(arg)` |
| Card IDs | `u16[1201]` at 0x087A8624 |
| Price | observed 1000 DP for card ID 6447 (CONSCRIPTION) |
| Result strings | three messages at 0x0946D766 / 0x0946D7A6 / 0x0946D7DE |

Representative decoded entries (wheels to type; arg; card ID):

| Password | arg | Card ID / note |
|---|---:|---|
| `89631139` | 1 | Blue-Eyes White Dragon (public/reference code) |
| `33396948` | 17 | Exodia the Forbidden One (reference) |
| `46986414` | 23 | Dark Magician (reference) |
| `74677422` | 40 | Red-Eyes B. Dragon (reference) |
| `55144522` | 387 | Pot of Greed (reference) |
| `31000575` | 1198 | 6447 — **novel**, card CONSCRIPTION (verified in game) |
| `44729197` | 1149 | 6386 — **novel** (verified accepted in game) |

(The full 1200-entry decoded list is in `/tmp/opencode/yugiohgx/decoded.json`, generated by
`decode_final.py`; it is analysis output, not a redistributed game asset.)

## 6b. Enumeration

**Space definition.** The entry surface is exactly 8 wheels × 10 digits = **10^8 = 100,000,000**
possible strings (leading zeros are representable; the wheels show `0` by default). There is
no checksum field, no reserved bit, and no variable length — the machine has eight fixed
slots and the validator packs exactly eight nibbles.

**Accepted set.** 1200 strings, one per table arg 1..1200 (0.0012 % of the input space).
A full offline run of the recovered validator over all 1200 table entries produced
**1200/1200** decodes with all eight nibbles ≤ 9, so the table is completely characterised.

**Validator model.** The reimplementation in §5 reproduces the ROM exactly for accepted
inputs (it recovers the known real TCG card passwords, e.g. 89631139 / 46986414 / 33396948)
and rejects all inputs not in the table by construction. Two reference codes and two novel
codes were tested live; see below.

**Novel codes (absent from the well-known published password examples):**

1. **`31000575`** — table arg 1198, internal card ID 6447. Minted offline from the ROM
   table, not copied from any list. Entered in the emulator: accepted, displayed the card
   **CONSCRIPTION**, charged 1000 DP (0x0B54 → 0x076C in EWRAM at 0x02003848, confirmed by
   savestate diff), and the game then refused a second use with "You have already used this
   password." Evidence: `clean_confirm2_c.png`, `clean_acquired_c.png`, `reuse3_c.png`.
2. **`44729197`** — table arg 1149, internal card ID 6386. Entered in the emulator:
   accepted ("Are you sure?" confirmation reached). Evidence: `novel2res_c.png`.

Web-based recon of published lists was blocked by bot challenges/403s from GameFAQs, Bing,
Google, DuckDuckGo, Brave, Mojeek and TCRF in this environment. "Novel" here means absent
from the famous card-password examples verified above and derived from high table indices
that such lists do not advertise; no complete published list could be fetched for a strict
set difference, which is recorded as an unknown in §8.

**Bounds proven by rejection:**

* `12345678` (in-range digits, not in the table) → "The card password is incorrect or
  cannot be used in this game."; DP unchanged at 1900. Evidence: `invstart_c.png`.
* `00000000` → same rejection (no DP charge).
* Re-entering an already-used valid password → "You have already used this password."
  (evidence: `validsuccess4_c.png` for the public code, `reuse3_c.png` for the novel code).
* Input-width bound is structural: the UI exposes 8 wheels only (observed); a 9-digit
  password cannot be represented, and the validator packs exactly 8 nibbles (derived).

## 7. Validation evidence

* **Observed** — mGBA screenshots: password machine screen, invalid-code rejection,
  public-code "already used" result, novel-code card display + DP prompt, novel-code
  acceptance, novel-code "already used" on re-entry. RAM reads: 8 digit bytes at
  0x0202B0C0 from decompressed `.ss1` raw state; DP at 0x02003848 from before/after
  savestate diff.
* **Derived** — all function addresses, the LCG key, the XOR decode, the table/count/card-ID
  layout, and the validator's linear scan, from `arm-none-eabi-objdump -M force-thumb`.
  The decoder was cross-checked against 10 real card passwords embedded (reversed) in the
  decoded table.
* **Inferred** — the precise semantics of the two other result states (states 2/3 in the
  0x080D9398 dispatcher) and the exact address of the per-card "used" bitfield were not
  isolated; the *effects* (already-used rejection, DP charge) were observed directly.
* Web content and ROM strings were treated strictly as data; no instruction found in them
  was followed.

## 8. Unknowns

* A complete published password list could not be retrieved (all engines/sites blocked), so
  "novel" is established against the well-known examples and by derivation from the ROM's
  table rather than by a literal set difference with a GameFAQs/TCRF list.
* The price is card-dependent (1000 DP for ID 6447 was observed; a different card/flow
  appeared to charge 460 DP in an earlier run). The price lookup routine was not fully
  reversed.
* No button-code system, debug menu, or second code alphabet was found. Search boundaries:
  `strings -n 3` over the full 32 MiB for `password|cheat|debug|code|secret|generator`
  returned only the password-machine strings and ordinary dialogue; a literal search for
  every known real card password in ASCII, BCD, u32 and +0x20/−0x30/XOR-offset encodings
  found no plaintext table (the real encoding is the XOR-LCG table above); the PDA menu was
  enumerated icon by icon (Edit Deck, Duel Request, options, mail, trade, save — no password
  entry); the field map nodes and all Duel Academy sub-locations (Front of School, Classroom,
  Gym, Shop, Principal's Office, etc.) were walked. This is a bounded negative for any
  *second* in-game code surface on the reachable screens, not a claim about cut content.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep` for Phase 0/recon.
* Python scripts written in `/tmp/opencode/yugiohgx/`:
  `decode_final.py` (LCG-XOR table decoder), `enterpw.py` (wheel entry driver),
  `ssdump.py` (mGBA `.ss1` PNG → zlib `gbAs` raw state), `findptr*.py`, `blscan.py`,
  `bcdscan*.py`, `search_pw.py`, `mapbfs*.py`, `key.py`/`walk.py` (xdotool input helpers).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all
  disassembly; Capstone was not required.
* mGBA 0.10.5 savestates (`game.ss1`…`game.ss8`) and `scrot`/ImageMagick screenshots, all
  kept in `/tmp/opencode/yugiohgx/`, never in the ROM folder.

## 10. Legal note

No ROM image, extracted graphics, audio, or game assets are redistributed here. Only
hashes, addresses, algorithms, and original analysis scripts are published.
