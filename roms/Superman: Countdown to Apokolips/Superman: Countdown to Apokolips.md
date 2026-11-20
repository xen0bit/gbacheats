# Superman: Countdown to Apokolips (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Superman: Countdown to Apokolips/Superman: Countdown to Apokolips.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `SUPERMAN CTA` |
| Game code | `ASUE`; maker `70` (Infogrames/Atari); version `0x00` |
| MD5 | `4ca57c6b50b5cad07ae33ea0a5dfe3f0` |
| SHA-1 | `82ec3dcc12b5dd6f253902f5e46d90dde666b74e` |
| SHA-256 | `9beb0ef068c4aa675fc7adbeaef8ea0eaa73c304511fe026b5a4742924187fbe` |
| Header checksum | `0x0000`, complement `0x59` |

**Release caveat (guide §16.1):** the distributed image is a **EURASIA cracktro** release. Its entry word at `0x00000000` is `0xEA1DFCBE` (`b 0x0877F300`), not the stock `0xEA00002E` (`b 0x080000C0`). The cracktro displays "EURASIA ... supplied by TEAM EURASIA" and only then hands off. All analysis and emulation in this report used a **byte-identical working copy with the stock entry word restored** (`/tmp/opencode/superman/superman_restored.gba`); only the 4-byte entry word was changed. Game code/strings/tables are untouched.

## 2. Executive summary

The game has a genuine **6-character password system** on the main menu (`PASSWORD`), used to start at a later level / unlock content. It is **not** a hard-coded list: it is a 64-symbol, per-position substitution cipher plus a 32-bit packed payload with bitfield validation and a popcount-mod-3 check digit. The game also contains an encoder that mints passwords from game state.

- Input alphabet: 64 symbols `ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#1234567890?`; six positions, each with its **own 64-byte permutation** (table at `0x080A8D40`).
- Decoder `0x0803FBA8`: char → 6-bit index in the position's alphabet → 32-bit word `acc = v0<<26 + v1<<20 + v2<<14 + v3<<8 + v4<<2 + v5`, then a 29-bit rotate keyed by `acc & 7`.
- Validator `0x0803FC3C`: bit30 must be 1; nine 3-bit fields must form a nonzero prefix; checksum `(popcount(v>>3) mod 3) == (v & 7)`; special all-ones case for bit31=1.
- Encoder `0x0803FDF0`: inverse rotate + field extraction → 6 chars (NUL-terminated).

**Enumeration result:** 9,842 distinct valid 32-bit payloads → **157,467 accepted 6-character strings** out of 64^6 = 68,719,476,736 possible strings. Roughly 16 aliases per payload (the last two positions overlap by 4 bits in the packing). Three published codes were verified accepted; two published codes were **rejected by the ROM**. Novel codes were minted, confirmed by RAM reads and emulator screenshots, and bounds were proven by rejected inputs.

## 3. How to reproduce

**Emulator:** mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:316` + openbox, `-3` scale. Keymap A=`x`, B=`z`, Start=`Return`, D-pad=arrows.

Path: boot → title "Press START" → `Return` → logo → main menu → `Down Down x` → **PASSWORD** screen (six `?` slots). `Start` submits; `B` quits.

Because the game's key repeat is frame-rate sensitive, reliable arbitrary-code entry was done by **patching the input buffer in an mGBA savestate**:
1. Save a state on the PASSWORD screen (`Shift+F1` → `<rom>.ss1`).
2. The `.ss1` is a PNG with a zlib-compressed `gbAs` chunk. Decompress it; RAM `0x030000C2` (the six selector-index bytes) is at state offset `0x190C2`. Write the six index bytes `BASE.index(ch)`; recompress, fix chunk length + CRC.
3. Boot with `mgba -3 -t patched.ss1 superman_restored.gba`, press `Return`.
4. Save another state; read result byte at state offset `0x190CD` (RAM `0x030000CD`) and the accepted payload at `0x1C704` (RAM `0x03003704`).

Scripts: `/tmp/opencode/superman/{pwmodel.py,patchstate.py,testcodes.py,capture.py,enumerate.py}`.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08000000` | Entry word (patched to `0xEA1DFCBE` in distributed ROM; stock `0xEA00002E`) |
| `0x0803FBA8` | `str_to_val(char* s) -> u32` — password decoder (Thumb) |
| `0x0803FC3C` | `validate(u32 v) -> bool` — password validator (Thumb) |
| `0x0803FDC4` | `popcount(v >> shift) mod shift` helper |
| `0x0803FDF0` | `val_to_str(u32 v, char* out)` — password generator (Thumb) |
| `0x0804CE8` / `0x0804CF4` | Call sites of decoder / validator on the password screen |
| `0x0804D1C`, `0x0804D20`, `0x0804D24` | Literals: output buffer `0x030000D0`, ASCII table `0x080A6B7C`, input indices `0x030000C2` |
| `0x0804D28`, `0x0804D2C`, `0x0804D30` | Result flag `0x030000CD`, stored payload `0x03003704`, success flag `0x030000CC` |
| `0x08050000` | Pointer to base alphabet `0x0804F67C` (localization bank) |
| `0x080A6B7C` | 64-byte on-screen keyboard alphabet (selector index → ASCII) |
| `0x080A8D40` | Six 32-bit pointers to the per-position alphabets |
| `0x0804F844/800/7BC/778/734/6F0` | Position alphabets 0..5 respectively |
| `0x030000C2` | Six input selector indices (EWRAM/IWRAM mirror) |
| `0x030000D0` | Converted 6-char + NUL string passed to decoder |
| `0x030000CD` | Validator result (0 = "Invalid Password", 1 = accepted) |
| `0x03003704` | Accepted 32-bit payload, reused by the level/story setup |

Reachable screens walked: title, game logo, main menu (TUTORIAL / NEW GAME / PASSWORD / SECRETS / CREDITS), PASSWORD, SECRETS (Gallery Mode / Levels), "Unlocked levels", Gallery Mode profiles, Credits, in-game intro cutscenes. No hidden debug menu or button code was found in the reachable screens or in the strings/disassembly (no debug-menu string bank, no key-mask sequence table).

## 5. Algorithm

Position alphabets (exact 64-byte strings, read from ROM):

```
T0 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#1234567890?"
T1 = "#1234567890?ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
T2 = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ#1234567890?"
T3 = "abcdefghijklmnopqrstuvwxyz#1234567890?ABCDEFGHIJKLMNOPQRSTUVWXYZ"
T4 = "NOPQRSTUVWXYZabcdefghijklmABCDEFGHIJKLMnopqrstuvwxyz#1234567890?"
T5 = "nopqrstuvwxyzABCDEFGHIJKLM#1234567890?NOPQRSTUVWXYZabcdefghijklm"
```

**Decode (string → payload):**
```
acc = 0
for p in 0..5:
    i = index of s[p] in T[p]        # 0..63 (65 if not found)
    acc += i << (26 - 6*p) if p < 5 else i
a = acc & 7;  Y = acc >> 3
v = ((((Y >> a) | ((Y & ((1<<a)-1)) << (29-a))) & 0x1FFFFFFF) << 3) | a
return v & 0xFFFFFFFF
```

**Validate (v):**
```
if v == 0 or bit30(v) == 0: reject
for i in 0..7:
    f = (v >> (3+3*i)) & 7
    if f == 0: continue              # ends the nonzero prefix
    if f > 3: reject
    if f == 1: count += 1
    require chain bit i set; set chain bit i+1
f8 = (v >> 27) & 7
if f8 > 1: reject
if f8 == 1: require bit31(v); count += 1
if bit31(v) and count != 9: reject
if (popcount(v >> 3) mod 3) != (v & 7): reject
accept
```
Consequence: fields 3..29 (nine 3-bit fields) must be a nonzero prefix followed by zeros; bit30 is always 1; the low 3 bits are the checksum. Field 8 (bits 27-29) can only be 0 or 1. The bit31=1 case forces all nine fields to 1, which has exactly one solution: `0xC924924A` = `J9jjbp` (the bonus-level code).

**Encode (payload → string):** inverse 29-bit rotate, then for p=0..4 take `(acc >> (26-6*p)) & 63` into `T[p]`, and for p=5 take `acc & 7` into `T5`; append NUL. Note positions 4/5 overlap in `acc` (bits 2-5), so decode is many-to-one — this is the source of the aliases in §6b.

## 6. Tables

**Published codes from the web, verified against this ROM** (all are 6 chars, case-sensitive):

| Published code | Claim | ROM result | Payload (if accepted) |
|---|---|---|---|
| `J9jjbp` | Hidden/bonus level, all levels + profiles | **accepted** | `0xC924924A` |
| `A#asAp` | Level 4 | **accepted** | `0x4000049A` |
| `APlsXp` | Level 7 / "unlocks levels 1-7" | **accepted** | `0x406CB48A` |
| `Q#aaTa` | Level 2 | **rejected** (`result=0`) | — |
| `g#ab2o` | Level 3 | **rejected** (`result=0`) | — |

The two rejected codes are absent from the ROM under this codec. One-character corrections that *are* accepted: `Q#aaTX`/`Q#aaTf`/`Q#aaTn` (for `Q#aaTa`) and `g#abKo`/`g#abZo`/`g#aboo` (for `g#ab2o`) — likely OCR/transcription errors or a different revision's encoding. Recorded as findings, not asserted as canonical.

**Payload bit fields** (as consumed at `0x080061D0`-`0x0800629E`): nine 3-bit fields at bit offsets 3,6,9,12,15,18,21,24,27; each extracted with `(v << (29-3k)) >> 29` into a settings byte. Exact semantic labels (which field is level vs. difficulty vs. unlock flag) are **inferred**, not observed.

## 6b. Enumeration

**Space definition.**
- Surface: 6 symbols from a 64-symbol alphabet → 64^6 = **68,719,476,736** possible strings.
- Internal payload: 32 bits with the constraints in §5 → **9,842 valid values** (1 with bit31=1, 9,841 with bit31=0; the latter count equals `1 + 3 + 3^2 + ... + 3^8 = (3^9-1)/2 + 1`... specifically `sum_{k=0}^{8} 3^k = 9841` nonzero-prefix field patterns).
- Accepted strings: **157,467** (computed by digit-DP over the packed-word preimages: 9,841 payloads × 16 aliases + one payload `0x4000000A` × 11 aliases). Verified by reconstructing all preimages for sample payloads and re-running `str_to_val` + `validate` on each — all matched.
- Alias source: positions 4 and 5 overlap in bits 2-5 of `acc`; altering both indices in concert leaves `acc`, hence the payload, unchanged. These are true aliases, not distinct codes.

**Validator model agreement.** The Python model `pwmodel.py` agrees with the ROM on every tested input: the three accepted published codes produced the exact payloads the ROM stored at `0x03003704`; the two rejected published codes were rejected by both model and ROM; all novel and negative tests below matched.

**Novel codes (not in GameFAQs, ChapterCheats, PlanetCheats, GameGenie, IGN, TCRF).**

| Code | Payload | Emulator result | RAM evidence |
|---|---|---|---|
| `g#aaNo` | `0x40000001` | accepted; intro cutscene ("ROCKETED TO EARTH AS ...") | `result=1`, value `0x40000001` at `0x03003704` |
| `A#bjXp` | `0x4000124A` | accepted | `result=1`, value `0x4000124A` |
| `A9jjXp` | `0x4024924A` | accepted (model) | — |

Screenshots: `cap_novel_before.png` (code on screen), `cap_novel_after.png` (accepted cutscene), both in `/tmp/opencode/superman/`.

**Bounds proven by rejection.**

| Input | Why it must fail | ROM result |
|---|---|---|
| `APlsXq` | last char changed → checksum bits wrong (`v=0xA0365A43`) | `result=0`, "Invalid Password" (screenshot `cap_reject_after.png`) |
| `J9jjbq` | checksum corrupted on the all-ones bonus code | `result=0` |
| `A#aaIp` | field 0 = 4, outside allowed {0,1,2,3} (`v=0x40000022`) | `result=0` |
| `Q#aaTa`, `g#ab2o` | published codes that fail the field/check constraints | `result=0` |

Thus both failure layers are demonstrated separately: a checksum-only violation and a field-range violation, in addition to out-of-list inputs.

## 7. Validation evidence

- **Observed:** main-menu/password/Secrets/Gallery screens (screenshots); `result` byte and stored payload read from decompressed mGBA savestates; all accept/reject outcomes above; EURASIA cracktro on the unmodified ROM.
- **Derived:** decoder/validator/encoder algorithms and all addresses from Thumb disassembly with Capstone/objdump; alphabet tables dumped from ROM bytes; 9,842 valid values and 157,467 accepted strings by structural enumeration + digit DP with preimage reconstruction cross-check.
- **Inferred:** semantic names of the 3-bit setting fields; that the two rejected published codes are transcription errors from a different revision.

## 8. Unknowns

- The exact game-state meaning of each of the nine 3-bit payload fields was not fully traced through the level-setup code; only the extraction addresses are proven.
- Whether other languages (French/German/Spanish/Italian banks at `0x070000`+) use a different on-screen alphabet was not tested; the English bank at `0x080A6B7C` was used throughout.
- No button-code or hidden debug menu was found on the reachable screens; this is a bounded negative over the screens listed in §4 and a strings/mask-table scan, not a proof over unreachable code paths.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` (address ranges above); Capstone 5.0.7 for literal/BL scans.
- Python 3 with Pillow for glyph strips; `pwmodel.py` (codec), `enumerate.py` (space), `patchstate.py`/`testcodes.py`/`capture.py` (savestate oracle).
- mGBA 0.10.5 under Xvfb `:316` + openbox, `SDL_AUDIODRIVER=dummy`; GDB stub used once (single-session limitation in this build) to locate the RAM buffer inside the savestate.
- No ROM, savestate, or copyrighted asset is redistributed; only findings, addresses, and original scripts are published.
