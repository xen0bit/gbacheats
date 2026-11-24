# Yu-Gi-Oh! The Eternal Duelist Soul (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Yu-Gi-Oh! The Eternal Duelist Soul.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `YU-GI-OH!EDS` |
| Game code / maker | `AY5E` / `A4` (Konami), software version `0x00` |
| `file(1)` | Game Boy Advance ROM image: "YU-GI-OH!EDS" (AY5EA4, Rev.00) |
| MD5 | `9b68aaa9678e812afdae14528c08950f` |
| SHA-1 | `e092d4d30f79c9f458790af9942cfd796716cfcd` |
| SHA-256 | `16224aa9477011002e9e418e1bdec2f4a5bf92bea3cf4673a47e9824a38cd542` |

Header entry word is `0xEA1FEEFE` (`b 0x087FC000`), **not** the stock `0xEA00002E`. The ROM boots and plays normally under mGBA 0.10.5, so this is treated as a non-standard boot stub, not a broken/cracked image. Header checksum is `0x0000` with complement byte `0x9C`

## 2. Executive summary

The only in-game code system is the **8-digit card password** screen reached from the main menu. There are no button codes, debug menus, or other hidden code surfaces in this build (bounded negative, §6b/§8).

The password validator is a **pure lookup table**, not a checksum algorithm:

* The on-screen keypad packs 8 entered decimal digits (0–9) into four big-endian BCD bytes.
* It linearly scans a fixed table of **821 4-byte slots** at ROM `0x08623120` and returns the matching slot index. Slot 0 is `0x00000000` (an alias of "not found"); slots 1–820 are the card passwords, 757 real values and 63 `0xFFFFFFFF` sentinels for cards with no password.
* The returned index is a card ID. A returned `0` means rejection. A later game-state layer also rejects a card the player already owns (published behaviour, not isolated dynamically — §8).

**No novel code exists.** The accepted set is exactly the 757 published card passwords. An exhaustive C reimplementation of the validator over all **100,000,000** possible 8-digit inputs accepted exactly **757** inputs and every one is in the complete EDS password list. This is a proven bounded negative (§0.2 item 5, §16.9), not "I did not find one".

Two valid codes were driven through the real screen and verified in RAM: `89631139` → validator index **82** (Blue-Eyed White Dragon) and `46986414` → index **150** (Dark Magician). The invalid code `12345678` returned **0**.

A developer debug leftover survives in the retail screen: the accept path prints `Password: <8 digits>->%4X`, where `%4X` is the raw validator return value (`0x0807C704`–`0x0807C728`). A scramble routine (`0x0807C830`) replaces the keypad with 8 random digits after every submission — an anti-brute-force UI quirk, **not** part of validation.

## 3. How to reproduce

**Emulator/display (all PIDs owned by this job):**

```bash
Xvfb :315 -screen 0 1024x768x24 &          # pid 917405
openbox &                                   # pid 917409
DISPLAY=:315 SDL_AUDIODRIVER=dummy \
  mgba -3 -g "<rom>" &                      # pid 918416
```

mGBA 0.10.5's `-g` stub did **not** listen on port 2345 in this container; RAM evidence was obtained by decompressing the `gbAs` chunk of mGBA `.ss1`–`.ss9` savestates (§9).

**Keymap** (mGBA SDL defaults): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys 80–100 ms; shorter taps are dropped.

**Screen path (observed):**

1. Title → **New Game**.
2. Advance the Tea/Yugi cutscene with repeated A (≈100 presses).
3. Pick one of the three starter decks (black chosen here). This drops straight into a tutorial duel vs. Tea.
4. Main Phase 1: cursor onto your **Deck** icon (right side) → A → `Surrender` → A → `YES`.
5. Main menu (`Campaign / Link Battle / Deck Edit / Record / Calendar / Card Trading / Password`). Move to **Password** → A.

**Keypad grid** (observed; bottom row has only two cells):

```
7 8 9
4 5 6
1 2 3
0 GET CARD
```

D-pad moves the highlighted digit (Up/Down wrap by column; Down from the top row wraps to the bottom). L/R shoulders move the 8-digit input cursor. After the 8th digit the cursor auto-jumps to GET CARD. On submission the game **randomises the displayed digits** (`0x0807C830`), so screenshots of the display after submit are not evidence of what was validated — read RAM instead.

**Deterministic code entry used for validation:** because the post-submit scramble makes keyboard-only entry hard to audit, the 8 digit bytes were written directly into a savestate (`0x0201F7B0`–`B7`), the cursor byte set to `0xA7` (GET CARD), the patched state loaded with F9, and the real GET CARD button pressed with A. The game's own validator and accept path then ran unmodified. The saved-game state is otherwise untouched.

**Codes tested:** `89631139` (accept), `46986414` (accept), `12345678` (reject), `00000000` (reject), `18591904` (accept, published).

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Address | Kind | Meaning |
|---|---|---|
| `0x08000000` | data | Entry word `0xEA1FEEFE` → `0x087FC000` |
| `0x0807C304` | thumb fn | `validate_password()` — exact BCD table lookup, returns u16 card index or 0 |
| `0x0807C35C` | literal | table base `0x08623120` |
| `0x0807C358` | literal | struct pointer `0x0201F7B0` |
| `0x0807C6D4` | thumb code | password-screen accept path (digit value > 9 ⇒ GET CARD) |
| `0x0807C6F2` | call | copies 8 input digits `struct+0` → `struct+8` before validation |
| `0x0807C704`–`0x0807C728` | code | prints `Password:`, 8 `%c` digits, then `->%4X` (debug return-value display) |
| `0x0807C830` | code | after submit: RNG loop fills 8 display digits (`0x08076F9C`, `0x0807EF6C`) |
| `0x08087F88` | string | `"Password:"` |
| `0x08087F94` | string | `"%c"` |
| `0x08087F98` | string | `"->%4X"` |
| `0x08087FA0` | string | `"Throw it in now !\n"` (debug-era remnant) |
| `0x08623120` | table | 821 × 4-byte BCD password slots (slot 0 … slot 820) |
| `0x0201F7B0`–`B7` | EWRAM | 8 displayed input digits (byte per digit, value 0–9) |
| `0x0201F7B8`–`BF` | EWRAM | validator's 8-byte copy, written at submit |
| `0x0201F7C0` | EWRAM | keypad cursor byte = `(selected_digit << 4) \| input_position` |
| `0x0201F7C4` | EWRAM | u16 validator result (card index; 0 = reject) |

Savestate raw-state offsets used: EWRAM base `0x21000`, so ROM-RAM `0x0201F7B0` is raw offset `0x407B0`.

## 5. Algorithm

Precise reimplementation of `0x0807C304`:

```python
# 8 entered digits at EWRAM 0x0201F7B0..B7 are copied to 0x0201F7B8..BF
def pack(digits):            # digits: list of 8 ints 0..9
    return bytes(((digits[2*i] << 4) | digits[2*i+1]) for i in range(4))

def validate(code):          # code: 8-char decimal string
    packed = pack([int(c) for c in code])
    for idx in range(0, 821):              # loop bound 0xCD << 2 (0x0807C362)
        entry = rom[0x08623120 + idx*4 : 0x08623120 + idx*4 + 4]
        if entry == packed:                # 4 exact byte comparisons
            return idx & 0xFFFF            # 0x0807C352 (zero-extend)
    return 0
```

Notes:

* `0x0807C312`–`0x0807C326` packs byte pairs into BCD with `(b[2i] << 4) | b[2i+1]`; no validation of the nibbles occurs in the validator — the keypad guarantees 0–9.
* The comparison is four plain `ldrb`/`cmp`/`bne` pairs (`0x0807C334`–`0x0807C350`). There is no checksum, XOR, permutation, or key schedule.
* Slot 0 (`0x00000000`) makes input `00000000` "match" index 0, which is indistinguishable from the not-found return — so it behaves as a rejection.
* Success/failure display and the post-submit RNG scramble are in the caller (`0x0807C6D4` onward), **after** the validator has already returned.

## 6. Tables

### Password table (ROM `0x08623120`)

| Property | Value |
|---|---|
| Slots | 821 (indices 0–820; step 4 bytes; end `0x08623DF4`) |
| Slot 0 | `00 00 00 00` — not-found alias / sentinel |
| Slots 1–820 | card passwords, one per card, same order as the published alphabetical card list |
| Real passwords | **757** |
| Empty markers | **63** slots = `FF FF FF FF` (cards with no password, incl. Egyptian Gods) |
| Encoding | four big-endian BCD bytes; e.g. `23771716` = `23 77 17 16` at `0x08623124` (slot 1, 7 Colored Fish) |
| Representative entries | slot 82 = `89 63 11 39` (`89631139`, Blue-Eyed White Dragon, ROM `0x08623268`); slot 150 = `46 98 64 14` (`46986414`, Dark Magician); slot 223 = `18 59 19 04` (`18591904`, Final Destiny); slot 820 = `86 10 07 85` (`86100785`, Zone Eater) |

The 63 `FFFFFFFF` slots are unreachable through the decimal keypad (nibbles A–F cannot be entered), which is a structural bound on the input space.

### Keypad / cursor

| Cell | Up | Down | Left | Right |
|---|---|---|---|---|
| 7 | 4 | 0 | 3 | 8 |
| 8 | 5 | GET | 7 | 9 |
| 9 | 6 | GET* | 8 | 1* |
| 4 | 1 | 7 | 6 | 5 |
| 5 | 2 | 8 | 4 | 6 |
| 6 | 3 | 9 | 5 | 4 |
| 1 | 4 | 0 | 3 | 2 |
| 2 | 5 | GET | 1 | 3 |
| 3 | 6 | GET* | 2 | 1* |
| 0 | 1 | 7 | GET | — |
| GET CARD | 8* | 9* | 0* | — |

\* Observed clamping at the 2-cell bottom row: Down from 3 lands on GET CARD rather than a third bottom-row cell. All other cells verified directly from the cursor byte in savestates.

## 6b. Enumeration

**Space definition.** Input is exactly 8 decimal digits, alphabet `0-9`, length fixed at 8. Packing is a bijection from the 100,000,000 strings to 4-byte BCD, so the space has **10^8** representable inputs. The validator accepts a value iff its packed BCD equals one of the 821 table slots. Slot 0 is the not-found alias; slots with `FFFFFFFF` are unrepresentable; therefore the **accepted set has exactly 757 members**.

**Validator model / whole-space run.** `enum2.c` (§9) loads the 757 BCD values from the ROM table and runs the exact pack-and-compare logic over every integer `0 … 99,999,999`:

```
loaded 757 passwords
accepted: 757 / 100000000
  89631139 -> ACCEPT
  46986414 -> ACCEPT
  12345678 -> reject
  00000000 -> reject
  18591904 -> ACCEPT
```

**Novel codes: none exist.** Every one of the 757 accepted values appears in the complete published EDS password list (`ooh44`/Teara 3rd party cheat index FAQ 19748 v1.5, which lists exactly 757 passwords among 820 cards). I first suspected `18591904` (slot 223, Final Destiny) was unpublished because a *generic cross-game* list omits it; the dedicated EDS list and 3rd party cheat index cheats page both contain it. That false lead is recorded per §16.7/§16.11 rather than reported as a novel code. Because the validator is an exact fixed-table lookup with no algorithmic generator, the §0.2 "mint a novel accepted code" deliverable is **impossible for this target** and is replaced by this exhaustive bounded negative.

**Bounds proven by rejection (observed in emulator):**

| Input | Validator result (RAM `0x0201F7C4`) | Interpretation |
|---|---|---|
| `89631139` | `82` (`0x0052`) | accepted — slot 82 = Blue-Eyed White Dragon |
| `46986414` | `150` (`0x0096`) | accepted — slot 150 = Dark Magician |
| `12345678` | `0` | rejected — not in table |
| `00000000` | `0` (offline) | rejected — slot-0 alias collides with not-found |
| `18591904` | `0x01` expected (offline ACCEPT) | published Final Destiny password, present in ROM |

`12345678` differs from a real password in all eight digits, so this bounds the obvious "arbitrary 8 digits are accepted" hypothesis. The exhaustive run bounds every remaining value.

**Other code surfaces (bounded negatives):**

* **Button codes:** all reachable screens were walked (title, cutscene, deck select, duel + surrender, main menu, Password, Record, Deck Edit entry). The published instruction manual and three independent FAQs state Select and Start are unused; no key-mask sequence table was found (literal searches for common mask prefixes and debug strings returned nothing). The only documented button trick — holding **R** during the pre-duel rock-paper-scissors to speed up the duel — is a published gameplay speed trick, treated as **published/unverified** (Inferred), not a validator.
* **Debug menu:** the only developer leftover is the `%4X` validator-result display embedded in the password screen (Derived from `0x0807C704`–`0x0807C728`); it is not a separate menu and grants nothing.
* **Unlockables:** tier duelists and booster packs (Egyptian Gods, Millennium Puzzles, promo cards) are save-flag/campaign gated, not code entry; out of scope for a code report and not brute-forced.

## 7. Validation evidence

Labels: **Observed** = emulator screenshot/RAM read; **Derived** = instruction sequence proves it; **Inferred** = plausible but not exercised.

| Claim | Evidence | Confidence |
|---|---|---|
| Table at `0x08623120`, 821 slots, 757 real + 63 `FFFFFFFF` | Derived (loop bound `0xCD<<2` at `0x0807C362`; literal at `0x0807C35C`) + direct ROM dump | Observed/Derived |
| Validator packs 8 digits and compares 4 BCD bytes | Derived (`0x0807C304`–`0x0807C372`) | High |
| `89631139` accepted, index 82 | Observed: RAM result `0x0052`, digit buffers = `08 09 06 03 01 01 03 09`, slot 82 = `89631139` | High |
| `46986414` accepted, index 150 | Observed: RAM result `0x0096` | High |
| `12345678` rejected, result 0 | Observed: RAM result `0x0000` | High |
| Exactly 757 of 10^8 inputs accepted | Derived: exhaustive run of faithful reimplementation | High |
| Post-submit digit scramble | Derived (`0x0807C830` RNG loop) + Observed (display changes to random digits after submit) | High |
| `->%4X` debug print | Derived from string `0x08087F98` and its xref at `0x0807C71E`; not seen rendered (right panel stayed black in captures) | Medium |
| "Already owned" second-layer rejection | Published behaviour (3rd party cheat indexes); not isolated dynamically | Inferred |
| Hold-R fast duel | Published (3rd party cheat indexes trivia / instruction-style cheat lists); not exercised | Inferred |
| No hidden button-code sequence / debug menu | Bounded negative: screen walk + string/mask scans (§6b) | Medium |

## 8. Unknowns

* The second acceptance layer (card already in Trunk/Deck/Side Deck ⇒ "ERROR") was not isolated: the validator index was read but the downstream ownership check was not watched. A valid-but-owned re-entry was not cleanly distinguished because the screen scrambles its display after submit.
* Whether the `->%4X` debug text is actually drawn on the right-hand panel; the code is present and referenced, but no capture showed it (possibly a missing font/tile in this build).
* The purpose of the non-standard header entry word (`0xEA1FEEFE` → `0x087FC000`) was not disassembled; the game runs correctly, so it is recorded only for image identification.
* Save-format details: `.sav` is 32 KiB; a return to the main menu changed four bytes relative to the pre-accept image, but the card-ownership array layout was not decoded.

## 9. Tooling

All scripts and evidence were kept in `/tmp/yu_gi_oh_eternal_duelist_soul/` (nothing in the ROM folder except the report):

* `keys.py` — xdotool key helper (DISPLAY=:315).
* `probe.py` — reads cursor/digit/result bytes from a savestate; used to map the keypad.
* `patchstate.py` — decompresses the PNG `gbAs` zlib chunk, patches digit bytes and cursor, recompresses with correct PNG CRCs, writes slot 9.
* `enter*.py` — keyboard entry attempts; `enter3.py` contains the corrected keypad-grid navigation.
* `enum2.c` — exhaustive validator over all 100,000,000 8-digit inputs (757 accepted); `gcc -O2`, ~6.5 s.
* `rom_table_820.json`, `rom_passwords.txt` — dumped ROM password table.
* `s0.png`–`s49.png`, `pw_*.png`, `res*.png`, `submit*.png`, `patched_*.png`, `reject_*.png` — screen evidence; `state_*.ss*` and `sav_*.bin` — RAM/save snapshots.

Toolchain: `arm-none-eabi-objdump -M force-thumb`, `capstone` (available), `mgba` 0.10.5, `Xvfb`, `openbox`, `xdotool`, `scrot`, `gdb-multiarch`, `gcc`, Python 3 + zlib/struct. No Ghidra/REA session was needed: the validator was found by following the `Password:` string literal pool at `0x0807C740` back to its enclosing code.

**Legal note:** no ROM bytes, card art, or game text are redistributed here; only addresses, algorithms, hashes, counts, and original tooling are published.
