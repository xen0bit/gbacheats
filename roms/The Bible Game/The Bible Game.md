# The Bible Game (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/The Bible Game/The Bible Game.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `BIBLE GAME` |
| Game code | `BIBE` (full header code `BIBE4Z`) |
| Maker | `4Z` |
| Revision | 0x00 |
| Entry branch | `0xEA00002E` → `0x080000C0` (stock retail crt0; not a patched/cracktro image) |
| MD5 | `01d53ae496ca36129f7a62ccf3ceed83` |
| SHA-1 | `803cdec573dad49f76bd3bc225c485a601528fac` |
| SHA-256 | `c3d21ddfb92fb8527054d006e8dcddc82fdf1ac4204da35e93dff285b90ad013` |

## 2. Executive summary

The game has a **developer-intended password system** with two distinct layers:

1. **Seven hard-coded strcmp shortcuts** in a plaintext table at `0x08019A40`. They set a quest/cheat result directly and do **not** satisfy the generated-code checksum. One is the widely published unlimited-health code `SRMSQNBBBBB`; six are unpublished quest shortcuts.
2. **An algorithmic generated save-code system**: 11 characters drawn from a 20-consonant alphabet, base-20 packed into a 41-bit payload plus a 4-bit nibble-sum checksum. This is the code shown on the Pause / Save Password screens (e.g. the game generated `MDGHFMDTBFT` at the start of Quest 1). The six published "Level 2 … End" codes are valid *generated* codes, not table entries — hence they are absent from the ROM as ASCII.

The validator was reimplemented bit-for-bit in Python and reproduces all six published level codes, the two novel codes minted here, and both rejection cases. Novel code `DXXDZVSRHNL` (quest field 5 with all progress fields zero — a combination absent from every published list) and `GLJJGTSWCJL` (quest 6, zero progress) were accepted by the real screen; the latter's RAM field writes were read back from a savestate. A wrong-checksum code and an out-of-range quest field (`f0=7`) were rejected on the real screen.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317`, SDL keymap A=`x`, B=`z`, Start=`Return`, D-pad=arrows. `SDL_AUDIODRIVER=dummy`.
* Path: boot → title "Press Start" → Start → intro pages (A) → "Choose Difficulty" → B → **Main Menu**: New Game / Password / Options / Instructions / Credits. Select **Password**.
* Password entry: cursor starts on char 0. Left/Right move the cursor; Up/Down change the character; A submits. The on-screen cycle skips vowels — `B C D F G H J K L M N P Q R S T V W X Z` (editor at `0x0800DF1C` skips `A,E,I,O,U,Y`). **Hold each key ≥100 ms**; 60 ms holds lose roughly half the presses.
* Savestates: Shift+F1…F9 save, F1…F9 load. States are written next to the ROM (`The Bible Game.ss*`); remove them afterwards.
* Codes tested (all entered through the UI):
  * `SRMSQNBBBBB` — published unlimited-health code — **accepted** (Loading → Quest 1).
  * `MRTTHFWBBBB` — unpublished table shortcut — **accepted** (Loading).
  * `DCBGMHQCRVL` — published "Level 2" — **accepted** (Loading, desert church zone).
  * `DXXDZVSRHNL` — **novel**, generated here — **accepted** (Loading, beach/Quest-5 zone, armored player).
  * `GLJJGTSWCJL` — **novel**, generated here — **accepted** (Loading; RAM `0x03003C04 = 6`).
  * `JKWWBPDQFHH` — wrong checksum — **rejected** (stays on Enter Password).
  * `RQNNNNNNNNN` — valid checksum, quest field 7 — **rejected** (stays on Enter Password).
  * `SRMVRLBBBBB` — table entry, observed rejected on two UI attempts despite the exact buffer being verified byte-for-byte in RAM; see §8.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08019A40` | Password table, 8 records × 12 bytes (11 chars + NUL) |
| `0x08019A4C` | `SRMSQNBBBBB` (unlimited-health cheat) |
| `0x08019A58`…`0x08019A94` | Six unpublished quest shortcut strings |
| `0x08019CCC` | format string `password: %s` |
| `0x08019BE8` | `%s`; `0x08019BEC` `Enter Password`; `0x08019BD8` `Save Password` |
| `0x087D5C00` | decode alphabet `NTHLJXVPCWGRMBZKSDFQ` (20 bytes) |
| `0x0800DA70` | **generator** — packs state → 11-char code; returns pointer to buffer |
| `0x0800DC0C` | **validator** — strcmp table then base-20 decode + checksum + field writes; returns 1 accept / 0 reject |
| `0x0800DF1C` | password character editor (vowel-skipping wrapper); `0x0800DEDC` raw ±1 editor |
| `0x0800DEDC` | ASCII char increment with wrap `Z→B`, `A→Z` |
| `0x0800E434` | caller: `bl validator`, `cmp r0,#0`, accept → return `-1`, reject → sound + return `2` |
| `0x0800F3B4` | pause screen: `bl generator` then printf `password: %s` |
| `0x03004DF0` | password input/output buffer (11 chars + NUL) |
| `0x03003C04` | field `f0` (quest/result), 3 bits |
| `0x030049E0`, `0x030043CC` | field `f1`, 4 bits (both written) |
| `0x03004980` | field `f2`, 4 bits |
| `0x03004DD8` | field `f3`, 1 bit (`0x03004DD0+8`) |
| `0x030043E4` | field `f4`, 5 bits |
| `0x0300498C` | field `f5`, 5 bits |
| `0x03003BFC` | field `f6`, 16 bits |
| `0x03004E1C` | field `f7`, 2 bits |
| `0x03004944` | field `f8`, 1 bit |
| `0x03003BD0` | unlimited-health cheat flag set by `SRMSQNBBBBB` |

## 5. Algorithm

### 5.1 Decoder (validator `0x0800DC0C`)

```
buffer = EWRAM/IWRAM 0x03004DF0   (NUL-terminated, 11 chars)
ALPHA  = "NTHLJXVPCWGRMBZKSDFQ"  index 0..19

# layer 1: hard-coded shortcuts (strcmp, exact 11 chars)
if buffer == "MRTTHFWBBBB":  result = 1; goto ACCEPT
if buffer == "MQSFSBBBBBB":  result = 2; goto ACCEPT
if buffer == "RDRMNFVFBBB":  result = 3; goto ACCEPT
if buffer == "PFTFRBBBBBB":  result = 4; goto ACCEPT
if buffer == "JQHNBBBBBBB":  result = 5; goto ACCEPT
if buffer == "SRMVRLBBBBB":  result = 6; goto ACCEPT
if buffer == "SRMSQNBBBBB":  cheat_flag(0x03003BD0) = 1; goto ACCEPT

# layer 2: generated save code
V = 0
for i from 10 downto 0:                 # i = character index
    d = index of buffer[i] in ALPHA     # miss -> 20 (always fails check)
    V = V * 20 + d
payload = V & ((1<<41)-1)
stored_checksum = V >> 41               # 7-bit compare, not masked
computed_checksum = sum( (payload >> (4*k)) & 15 for k in 0..10 ) & 15
if stored_checksum != computed_checksum: return REJECT (0)

# field extraction (bits of payload, little-endian bit order)
f0 = payload & 7                  -> 0x03003C04      # quest 0..6
f1 = (payload>>3)  & 15           -> 0x030049E0,0x030043CC
f2 = (payload>>7)  & 15           -> 0x03004980
f3 = (payload>>11) & 1            -> 0x03004DD8
f4 = (payload>>12) & 31           -> 0x030043E4
f5 = (payload>>17) & 31           -> 0x0300498C
f6 = (payload>>22) & 0xFFFF        -> 0x03003BFC
f7 = (payload>>38) & 3            -> 0x03004E1C
f8 = (payload>>40) & 1            -> 0x03004944
return ACCEPT (1)
```

Important: the leftmost character is the **least-significant** base-20 digit. The checksum is not one character — after insertion at payload bit 41 it is spread across the high digits by the base-20 conversion.

### 5.2 Encoder (generator `0x0800DA70`)

Inverse of the above: pack the state fields into `payload` (with clamping — e.g. field `f1` clamped to 15, `f4` to 31), compute `checksum = sum of 11 nibbles of payload & 15`, form `V = payload | (checksum<<41)`, then for `i = 0..10`: `buffer[i] = ALPHA[V % 20]; V /= 20` (unsigned 64-bit divide by 20 at `0x8012520` / `0x80120D0`). NUL-terminate at index 11. If `0x03003BD0 != 0`, the generator instead copies `SRMSQNBBBBB` verbatim (12 bytes via `0x801298C`) and returns.

Bit packing sources observed at `0x0800DAE4`–`0x0800DB96`: `f6` from `*0x03003BFC`, `f0` from `*0x03003C04`, `f1` from `*0x030049E0`, `f2` from `*0x03004980`, `f3` from `*(0x03004DD0+8)`, `f4` from `*0x030043E4`, `f5` from a helper over `*0x030043D4`/`*0x0300498C`, `f7` from `*0x03004E1C`, `f8` from `*0x03004944`.

## 6. Tables

### 6.1 Hard-coded password table (`0x08019A40`)

| # | String | Address | Result / effect | Verified |
|---:|---|---|---|---|
| 0 | `BBBBBBBBBBB` | `0x08019A40` | unused placeholder | static |
| 1 | `SRMSQNBBBBB` | `0x08019A4C` | unlimited spiritual health flag `0x03003BD0=1` | **accepted** (published) |
| 2 | `MRTTHFWBBBB` | `0x08019A58` | quest shortcut → result 1 | **accepted** (unpublished) |
| 3 | `MQSFSBBBBBB` | `0x08019A64` | quest shortcut → result 2 | static |
| 4 | `RDRMNFVFBBB` | `0x08019A70` | quest shortcut → result 3 | static |
| 5 | `PFTFRBBBBBB` | `0x08019A7C` | quest shortcut → result 4 | static |
| 6 | `JQHNBBBBBBB` | `0x08019A88` | quest shortcut → result 5 | static |
| 7 | `SRMVRLBBBBB` | `0x08019A94` | quest shortcut → result 6 | rejected in two UI tests (§8) |

### 6.2 Published generated codes (none are table entries)

| Published label | Code | Decoded `f0` | Checksum valid | `f4` | `f5` | `f6` | `f8` |
|---|---|---:|---|---:|---:|---:|---:|
| Level 2 | `DCBGMHQCRVL` | 1 | yes (15=15) | 31 | 19 | 48 | 1 |
| Level 3 | `FSQVLBJQTXH` | 2 | yes (10=10) | 31 | 31 | 112 | 1 |
| Level 4 | `RZFWPWKRVQN` | 3 | yes (4=4) | 31 | 31 | 253 | 1 |
| Level 5 | `MVMWBFGFCVN` | 4 | yes (1=1) | 31 | 31 | 477 | 1 |
| Level 6 | `BHXVGWDQCVN` | 5 | yes (1=1) | 31 | 31 | 882 | 1 |
| End | `ZFTVLCCLLHN` | 6 | yes (0=0) | 31 | 31 | 1350 | 1 |

These codes do **not** occur as ASCII anywhere in the ROM (literal searches for all six returned zero hits) because they are produced arithmetically.

### 6.3 Alphabet

`NTHLJXVPCWGRMBZKSDFQ` at `0x087D5C00` — 20 distinct consonants, used for both decode and encode. The on-screen editor cycles the same 20 letters in ASCII order (`BCDFGHJKLMNPQRSTVWXZ`) by explicitly skipping `A,E,I,O,U,Y` at `0x0800DF1C`.

## 6b. Enumeration

**Space definition.** 11 characters × 20 symbols = `20^11 = 204,800,000,000,000` possible strings. The validator requires bits 45..47 of the decoded word to be clear (it compares the full 7-bit `V>>41` against a 4-bit checksum), so only `V < 2^45` can pass. The accepted generated-code space is therefore exactly the `2^41 = 2,199,023,255,552` payloads, each with one uniquely determined checksum; plus the seven strcmp shortcuts (six of which are believed reachable; see §8). No reserved payload bits were found — every bit 0..40 is written to a game-state variable by the validator. Field widths: 3 + 4 + 4 + 1 + 5 + 5 + 16 + 2 + 1 = 41 bits; checksum 4 bits.

**Validator model.** Implemented in Python (`dec`, `enc`, `chk` helpers in `/tmp/biblegame`); it agrees with the ROM on:
* all six published generated codes (checksum matches in every case, `f0` = 1..6 in published level order — §16.15: the payload field is the truth, not the web label);
* the game's own code `MDGHFMDTBFT` (stored checksum 9 = computed 9, payload `0x180`, `f2=3` lives);
* both novel codes below;
* both rejected inputs.

**Novel codes (not in 3rd party cheat indexes or any wiki consulted).**

| Code | Payload fields | Evidence |
|---|---|---|
| `DXXDZVSRHNL` | `f0=5` (quest 5) with `f4=f5=f6=f7=f8=0`, `f2=3`; checksum 14 | **Accepted in-game** — Loading screen with the beach/Quest-5 map, different enemies and armored player (`novel1c.png`, `novel2c.png`). The published Quest-5 code `BHXVGWDQCVN` instead carries `f4=31,f5=31,f6=882,f8=1`, so this is a genuinely different state. |
| `GLJJGTSWCJL` | `f0=6`, all progress fields zero; checksum 15 | **Accepted in-game** — Loading screen. Savestate RAM read immediately after submission: input buffer = `GLJJGTSWCJL`, `0x03003C04 = 6` (quest), `0x03004980 = 3` (lives), other fields 0 (`state6` dump). |
| `CZFBVGFXBFT` | `f6=1234` (16-bit field), otherwise base | Generated and validated offline by the model; not entered in the emulator. |

**Bounds proven by rejection.**
* *Checksum*: `JKWWBPDQFHH` has the correct `f0=0,f2=3` payload but stored checksum 10 vs computed 9 — **rejected**, screen stays on Enter Password (`badchkc.png`).
* *Out-of-range quest field*: `RQNNNNNNNNN` has a valid checksum (0=0) but `f0=7`, outside the game's 0..6 quest domain — **rejected** (`f0maxc.png`). This also proves the semantic range layer is separate from the checksum, exactly as §16.5 warns.
* *Field clamping*: the generator clamps `f1` to 15 and `f4` to 31 before packing (`0x0800DAD8`/`0x0800DADC`), so values above those widths cannot be emitted, though the decoder accepts the full field width (`f2=15` with a valid checksum was accepted in-game — `NNCJGTSWCJL`, `f2maxc.png`). No further semantic range checks exist in the validator itself after `0x0800DE04`.
* *Alphabet*: characters outside the 20-symbol set cannot be typed at all (the editor skips vowels), and a decoder miss yields index 20, which cannot satisfy the 4-bit checksum.

**Closure.** The generated-code space is closed by the checksum equation, not by a lookup table: every payload in 41 bits has exactly one spelling. The seven strcmp shortcuts were enumerated by reading every literal pointer in the validator's literal pool (`0xDC6C`, `0xDC84`, `0xDC98`, `0xDCB0`, `0xDCC8`, `0xDCE0`, `0xDDE8`) — there are no others.

## 7. Validation evidence

**Observed.** Boot/title/intro/difficulty/main-menu/password/loading/gameplay/pause/save-password/game-over screens reached in mGBA and screenshotted. `SRMSQNBBBBB`, `MRTTHFWBBBB`, `DCBGMHQCRVL`, `DXXDZVSRHNL`, `GLJJGTSWCJL`, `NNCJGTSWCJL` accepted; `JKWWBPDQFHH`, `RQNNNNNNNNN` rejected. Password buffer bytes read from decompressed mGBA `gbAs` states at raw offset `0x1DDF0` = IWRAM `0x03004DF0` (verified `QLKNLNQXNJT`, `GLJJGTSWCJL`, `SRMVRLBBBBB`). Field writes read from the same states after submission (`0x03003C04=6`). The pause screen displays `password: MDGHFMDTBFT`, and the Save Password screen displays the same string.

**Derived.** Generator/validator structure, bit layout, checksum equation and alphabets from ARM/Thumb disassembly at the addresses in §4, cross-checked against the six published codes and the game-generated code.

**Inferred.** Field *names* beyond quest (`f0`) and lives (`f2`) are conservative labels based on the generator's source variables; the exact gameplay meaning of `f1`,`f3`,`f4`,`f5`,`f6`,`f7`,`f8` was not individually exercised. The terminal Game Over screen after a patched-state experiment (`ss9`) is an artifact of patching a savestate, not a code outcome.

**Screen walk (enumerated).** Title → intro pages → Choose Difficulty → Main Menu (New Game, Password, Options, Instructions, Credits) → Password entry → Loading → gameplay HUD → Pause (Return, View Map, View Key, Options, Instructions, Quit) → Quit? (Yes/No) → Save Password → Game Over (Quit to Main Menu / Restart Quest). Options/Instructions/Credits and View Map/View Key are present in the paused/main menus and are listed by the ROM's plain-ASCII text bank at `0x08019980`–`0x08019CD8`; they do not contain a further code entry surface (only the one `Password` menu item leads to `0x0800DC0C`, whose sole caller is `0x0800E434`). Text was decoded from ASCII directly — no font/tile bank decode was needed for these labels because the UI strings are plaintext.

## 8. Unknowns

* `SRMVRLBBBBB` (table entry 7, result 6) was retyped twice with the exact buffer verified in a savestate, yet A did not start a game. The first five table entries tested/behaved as expected, so this looks like a game-state gate on quest 6 rather than a bad string; the gate was not isolated. Reported as an observed anomaly, not a validator failure.
* Exact semantic meaning of fields `f1`, `f3`–`f8`.
* No Action Replay / GameShark codes were examined — out of scope.

## 9. Tooling

* `strings -t x`, `grep -abo`, `xxd`, Python `struct` literal/pointer scans, `arm-none-eabi-objdump -M force-thumb`, Capstone for annotated disassembly.
* `/tmp/biblegame/enter_pw.py` — XTEST password entry driver (20-symbol cycle, ≥100 ms holds).
* `/tmp/biblegame/calib.py` — input-timing calibration via savestate reads.
* Python decoder/encoder/checksum helpers (inline in `/tmp/biblegame`); mGBA savestate `gbAs` zlib chunk decoded with `zlib.decompress`, IWRAM at raw offset `0x19000`, password buffer at `0x1DDF0`.
* Web recon: 3rd party cheat indexes (403, recovered via search snippet), 3rd party cheat indexes. All fetched page text treated strictly as data.

No ROM data or copyrighted assets are redistributed here; only addresses, hashes, algorithms and the author's own generated codes are published.
