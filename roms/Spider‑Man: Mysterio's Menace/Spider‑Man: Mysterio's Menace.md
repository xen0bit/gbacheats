# Spider-Man: Mysterio's Menace (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Spider‑Man: Mysterio's Menace.gba` (U+2011 non-breaking hyphen in name) |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `SPIDERMAN MM` |
| Game code | `ASEE` (PAL), maker `52`, version `0x00` |
| Entry word | `0xEA00002E` (stock ARM reset branch) |
| Header checksum | `0x0000`; complement byte `0x6F` (strict spec would give `0x88`) |
| MD5 | `fbda16cbc7e3f81aa5b90da955d3e114` |
| SHA-1 | `ef80933054d6be9532d5d35bee6f715438301755` |
| SHA-256 | `009d1f54f5c25b88a5ebcf10be9937671611ebd9eaa384b0428f8438ff3c4287` |

Embedded-header scan: exactly one Nintendo-logo hit (file `0x4`, header at `0x0`) — a single clean retail image, not a 2-in-1, no appended trainer, no entry-point cracktro patch. The `Shin'en Multimedia. Code: B.Wodok` string at `0x7C926F` is the GAX audio-engine banner (known false positive).

## 2. Executive summary

The game has a **developer-intended 5-symbol password system** used for continue/level-select with preset cheat passwords. The on-screen keyboard uses a 32-symbol alphabet
`BCDFGHJKLMNPQRSTVWXYZ0123456789-` (consonants + digits + `-`), so a code carries 5×5 = **25 bits**. Those 25 bits are a state payload: 20 data bits plus a **5-bit parity checksum** at bit positions 0, 5, 18, 21, 24, followed by five consistency/range checks. The ROM validator at `0x08002388` stores the packed word at `G+0x8C` (where `G = [0x03001FE0] = 0x02000028`), verifies the checksum and range checks, then decodes the payload into difficulty (`G+0x94`), a 7-bit level-completion mask (`G+0x98`) and item flags (`G+0xE0`, `G+0xE1`).

Exact space: 33,554,432 printable codes → 1,048,576 checksum-valid → **86,016 accepted**. A separate hard-coded 5-symbol code `CRDT5` is checked outside this system.

I reimplemented the validator exactly (cross-checked against the ROM's own validator under Unicorn on 1,000 accepted and 1,000 random inputs, zero disagreements), generated a **novel unpublished code `TW3-R`** (Easy + all seven levels + all items), entered it on the real password screen, and confirmed both the visible result (game displays `PASSWORD: TW3-R`, "LEVEL COMPLETED", all four suits/upgrades/containers) and the RAM payload/fields from an mGBA savestate.

## 3. How to reproduce

- Emulator: `/usr/local/bin/mgba` 0.10.5 under `Xvfb :318`, `SDL_AUDIODRIVER=dummy`; keymap A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
- Menu path: title → **PASSWORD** (cursor is the white menu label; DOWN from NEW GAME) → 4×8 symbol keypad labelled `A - ACCEPT / B - BACKSPACE`. Each of the five symbols is picked with the D-pad and confirmed with A; the fifth confirmation submits automatically.
- Codes are entered with the 32-symbol alphabet above; the game echoes the accepted code on the in-game Select/inventory screen (`PASSWORD: <code>`).
- Novel code tested: `TW3-R`. Published codes re-tested offline against the ROM validator: `TB31T`, `C0-LQ`, `RV80S`, `JV31-`, `7V84Z`, `RV8WJ`, `SP1DY`, `SM11W`, `SMXXW`, `JV37T`, `JV33R` — all accepted. `ZVZ30` (published "skip 5 levels") is **rejected** by this PAL image's validator.
- Rejection tests: `JX31-` (bad checksum), `H-7W2` (valid checksum, invalid difficulty field); both rejected by the ROM validator.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x084B86F0` | Alphabet string, data bank (`BCDFGHJKLMNPQRSTVWXYZ0123456789-`) |
| `0x084C11FC` | Alphabet string, password-UI bank (same 32 bytes + NUL) |
| `0x084C11F4` | Hard-coded `CRDT5` cheat literal |
| `0x08002CEC` | Password **generator** (state → 25-bit word → 5 symbols), runs when Select is pressed in-game; helpers at `0x080025F8`, `0x0802674`, `0x0802714`, `0x080282C` (parity encoder) |
| `0x08003358` | Same generator writing symbols into caller buffer (`r1`) |
| `0x0801C4A0` | Packs the five entered alphabet indices into a 25-bit word (`b<<5 \| idx`, high index = char 4) and calls `0x08002388` |
| `0x08002388` | **Password validator / decoder** (5-bit checksum, range checks, field decode) |
| `0x080032FC` | Range helper: `(payload16 & 0x8208) ∈ {0x8208, 0x200, 0x08}` |
| `0x0802990` | Range helper: four additional bit-consistency checks |
| `0x0801C454` | `CRDT5` special-code checker (5 indices compared to literal) |
| `0x0801BC42` | Caller: tries main validator first, then `CRDT5`, then sets screen state |
| `0x03001FE0` | Pointer to state struct `G` (value `0x02000028` in EWRAM) |
| `G+0x8C` | Decoded 25-bit password payload |
| `G+0x94` | Difficulty: `0`=Easy, `1`=Normal, `2`=Super Hero |
| `G+0x98` | 7-bit level-completion mask (bit n = level n complete) |
| `G+0xE0`, `G+0xE1` | Item/suit/upgrade flags |
| Savestate `gbAs` layout | IWRAM at chunk offset `0x19000`, EWRAM at `0x21000` (so `G+0x8C` is at `0x210B4`) |

## 5. Algorithm

```
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ0123456789-"
idx(c) = position of c in ALPHA          # 0..31
payload(code) = Σ_{i=0..4} idx(code[i]) << (5*i)     # char 0 is bits 0..4
code(payload) = ''.join(ALPHA[(payload >> (5*i)) & 31] for i in 0..4)

b_k(x) = (x >> k) & 1
B0 = payload & 0xFF; B1 = (payload>>8)&0xFF; B2 = (payload>>16)&0xFF; B3 = (payload>>24)&0xFF
```

Checksum — all five equalities must hold (these are the five comparisons at `0x08002472`–`0x0800249C`):

```
b0  == b1(B0) ^ b3(B1) ^ b4(B2) ^ b4(B0) ^ b3(B0)         # target payload bit 0
b5(B0) == b2(B0) ^ b7(B0) ^ b4(B2) ^ b0(B1) ^ b7(B1)      # target payload bit 5
b2(B2) == b2(B1) ^ b0(B2) ^ b4(B2) ^ b4(B0) ^ b7(B1)      # target payload bit 18
b5(B2) == b0(B0) ^ b4(B1) ^ b1(B2) ^ b7(B2) ^ b1(B1)      # target payload bit 21
b0(B3) == b5(B0) ^ b2(B2) ^ b3(B2) ^ b6(B0) ^ b3(B0)      # target payload bit 24
```

Range checks (both helpers, `0x080032FC` and `0x0802990`):

```
(payload & 0x8208) ∈ { 0x8208, 0x0200, 0x0008 }
if b23: require b22 == 1 and b4 == 0 and b8 == 0
require not (b22 and b6)
require not (b8 == 0 and b13 == 0)
require (b4 or b14)
```

On success the ROM writes the payload to `G+0x8C` and decodes it into `G+0x94 / +0x98 / +0xE0 / +0xE1`; `0x0801C4A0` returns 1 and the caller starts the game at the encoded level set.

Generator inverse (for minting codes): treat all payload bits except `{0,5,18,21,24}` as 20 free data bits; solve the five triangular XOR equations above for those five check bits, then apply the range checks. The shipped encoder `0x08002CEC` does this from live game state.

## 6. Tables

| Published code | Decoded state (difficulty, level mask, items) | ROM validator |
|---|---|---|
| `TB31T` (ultimate) | (2 Super Hero, 0x7F, 0xFF/0x03) | accepted |
| `JV31-` (all levels+items) | (1 Normal, 0x7F, 0xFF/0x03) | accepted |
| `C0-LQ` (level select) | (1 Normal, 0x7F, 0x00/0x00) | accepted |
| `RV80S` (level select / last level) | (0 Easy, 0x7F, 0x96/0x01) | accepted |
| `7V84Z` (super password 1) | (0 Easy, 0x37, 0x16/0x01) | accepted |
| `RV8WJ` (super password 2) | (0 Easy, 0x3F, 0x16/0x01) | accepted |
| `SP1DY` (super password 3) | (2 Super Hero, 0x09, 0x4F/0x02) | accepted |
| `SM11W` (super password 4) | (2 Super Hero, 0x0B, 0xCF/0x03) | accepted |
| `SMXXW` (super password 5) | (2 Super Hero, 0x0B, 0x6F/0x03) | accepted |
| `JV37T` (super password 6) | (1 Normal, 0x7F, 0xBF/0x03) | accepted |
| `JV33R` (super password 7) | (1 Normal, 0x7F, 0x3F/0x03) | accepted |
| `ZVZ30` (published "skip 5 levels") | — | **rejected** (checksum fails; likely typo/other region) |
| `CRDT5` (ROM literal) | special hardcoded code; not a 25-bit payload | handled by `0x0801C454` |

State-field semantics observed in-game: `G+0xE0` bits cover thermal/armor/electric/symbiote suits and fluid/compressor/heavy-impact upgrades; `G+0xE1` covers the two web-container slots; `G+0x98` is the 7-level completion bitmask; `G+0x94` is difficulty.

## 6b. Enumeration

**Space definition.** Alphabet 32 symbols, length exactly 5 → 32⁵ = **33,554,432** representable codes (25-bit payload). Of these, 5 bits are a parity checksum (positions 0, 5, 18, 21, 24) leaving 20 payload bits: 2²⁰ = 1,048,576 checksum-valid codes.

**Exhaustive count** (Python model, validated against the ROM validator on 1,000 accepted + 1,000 random samples with zero mismatches):

| Category | Count |
|---|---|
| All printable 5-symbol codes | 33,554,432 |
| Checksum-valid | 1,048,576 |
| **Accepted after all range checks** | **86,016** (0.2563 % of all codes) |
| Rejected: difficulty mask `0x8208` | 655,360 |
| Rejected: check1 (bit23 group) | 172,032 |
| Rejected: check2 (b22 & b6) | 61,440 |
| Rejected: check3 (b8/b13) | 43,008 |
| Rejected: check4 (b4/b14) | 30,720 |

Counts are exact (full 2²⁰ enumeration). Every accepted payload decoded to a distinct state in a 3,000-sample survey. Adding the special `CRDT5` literal gives 86,017 accepted player inputs total.

**Novel code (not in any published list).** `TW3-R`, payload `0x0DFE22F`, decoded state `(difficulty 0 = Easy, level mask 0x7F = all seven levels, items 0xFF/0x03 = all upgrades)`. Published all-items codes exist only for Normal (`JV31-`) and Super Hero (`TB31T`); the published Easy code `RV80S` has partial items. `TW3-R` therefore exercises an unadvertised combination. It was accepted by the ROM validator (oracle = 1), entered on the real password screen, and produced:
- level-select screen with "DOWNTOWN / LEVEL COMPLETED",
- gameplay with the black/symbiote suit and `x5` web cartridges,
- in-game Select screen literally reading `PASSWORD: TW3-R` and listing THERMAL SUIT, ARMOR SUIT, ELECTRIC SUIT, SYMBIOTE SUIT, FLUID UPGRADE, COMPRESSOR, HEAVY IMPACT and full WEB CONTAINERS.
- Savestate RAM proof after acceptance: `G+0x8C = 0x0DFE22F`, `G+0x94 = 0` (Easy), `G+0x98 = 0x7F`, `G+0xE0 = 0xFF`, `G+0xE1 = 0x03`.

**Bounds proven by rejection.** All tests were run through the ROM's own validator function `0x08002388` under Unicorn (ground-truth ROM code, not my model):

| Input | Failure layer | ROM result |
|---|---|---|
| `JX31-` (one data bit flipped from `JV31-`) | checksum | rejected (0) |
| `H-7W2` | checksum OK, difficulty mask `0x8208` invalid | rejected (0) |
| `86-F7` | check1 | rejected (0) |
| `LD59Q` | check2 | rejected (0) |
| `101NH` | check3 | rejected (0) |
| `ZVZ30` (published code) | checksum | rejected (0) |

An in-game bad-code attempt also left the RAM payload at `0x00000000` (fresh game, no password applied), consistent with rejection.

## 7. Validation evidence

- **Observed (screenshots, kept in `/tmp/mysteriosmenace2/`)**: title `NEW GAME / PASSWORD / SOUND`; difficulty select `EASY / NORMAL / SUPER HERO`; 4×8 password keypad; level-select map with "LEVEL COMPLETED"; gameplay HUD (`x5` cartridges, black suit); Select/inventory screen showing `PASSWORD: TW3-R` and all items; pause menu `RESUME / SOUND / QUIT GAME`; Sound settings `BACK / MUSIC / SFX`.
- **Observed (RAM)**: mGBA `gbAs` savestate decompressed; EWRAM `G = 0x02000028`, `G+0x8C = 0x0DFE22F`, `G+0x94 = 0`, `G+0x98 = 0x7F`, `G+0xE0 = 0xFF`, `G+0xE1 = 0x03` after entering `TW3-R`; same fields zero in the pre-entry state.
- **Derived (disassembly / Unicorn)**: all checksum equations and range checks, the 86,016 count, the 5-symbol base-32 format, `CRDT5` being a separate literal comparison at `0x0801C454` called only when the main validator rejects, and its effect of setting screen state 10.
- **Inferred**: screen state 10 set by `CRDT5` is the credits screen (based on the literal `CRDT5` and the credited-employees trivia); not visually confirmed.

## 8. Unknowns

- The exact scatter mapping from individual payload data bits to each decoded field bit was not named bit-by-bit; the validator equations and decoded RAM fields are fully characterised, which is sufficient to generate/validate codes.
- `CRDT5`'s destination screen was not reached in the emulator (screen state 10 inferred as credits); its accept path is proven statically.
- `ZVZ30` is rejected by this PAL (`ASEE`) image; it may be a transcription error or belong to another region/revision.
- No separate hidden debug menu was found; all password-related handlers (`0x0801C37C`, `0x0801C454`, `0x0801C4A0`, `0x0801C4DC`, `0x0801C54C`, `0x0801C58C`) are reached from the single password-screen dispatcher at `0x0801BB80`, and every reachable menu screen was walked.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3 (`struct`, `zlib`, `PIL`), `arm-none-eabi-objdump -M force-thumb`, Capstone, **Unicorn 2.1.4** (`pip install --break-system-packages unicorn`) used to execute the ROM's validator as an oracle, mGBA 0.10.5 with Xvfb `:318` / openbox, `xdotool`, `scrot`, `convert`. Scripts: `/tmp/mysteriosmenace2/{validator,oracle,enumerate,decode_states,pick_codes,enter2,trace_all}.py`.

Legal note: no ROM, extracted graphics, music, or game text were redistributed; only hashes, addresses, algorithms, and generated codes are published.
