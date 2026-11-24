# Hot Wheels World Race (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Hot Wheels World Race.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `HOTWHEELS WR` |
| Game code | `BHWE`, maker `78`, version 0 (Rev.00) |
| Entry word | `0xEA00002E` → stock `b 0x080000C0` crt0 |
| MD5 | `91cc97b4023b7876f4ac783c2c4de2bd` |
| SHA-1 | `4045cb4551399537812d81b76bdd5cb46c4c7c06` |
| SHA-256 | `b9bb22a244bd9caff1ec9f78a6ef810c089c3c91922e4e8cbcf4a8f121b8ae32` |

Embedded-header scan: exactly **one** Nintendo-logo/GBA header hit (at file `0x0`); no multi-game image, no appended trainer, no cracktro. First 0x200 bytes are a normal ARM crt0 (IRQ stacks, copy/zero loops, literal pool containing Thumb `main` pointer). Header complement byte at `0xBD` is `0x40` whereas the canonical formula (`-(sum(0xA0..0xBC)+0x96)&0xFF`) gives `0xC3`; header checksum is `0x0000`. This anomaly is recorded but is *not* evidence of a patch — the entry branch is stock and the first 4 KiB contain no trainer/cracktro code.

## 2. Executive summary

The game has **no button-code system and no hidden debug menu**, but it does have a genuine **algorithmic progress-password system** (the game has no battery save; passwords are the only progress storage). The PASSWORD option on the main menu presents a 32-symbol keypad and an 8-character input. All published GBA level passwords were verified against the ROM's algorithm, and the space is much larger than the published list: **32^8 = 2^40 ≈ 1.10e12** input strings, of which **2^30 ≈ 1.07e9** satisfy the format's 10 reserved-bit checks.

The 8 characters decode to a 40-bit progress bitfield (8 × 5-bit fields) after a per-position modular offset. 22 bits of the payload are meaningful (10 league/team/driver counters and 12 flags); 10 bits are reserved and must be zero — this is the checksum/format layer. Two novel codes absent from every published list were generated offline, entered on the real screen, accepted (fireworks + return to menu), and shown to change the RAM progress counters from `(0,0,0,0,0)` to `(2,0,1,0,0)`. A code with a reserved bit set was rejected and left the game on the password screen, proving the bounds.

Console-version codes (`smashmouth`, `allcars`, `alltracks`, `R L Y Y X X`, PS2 button sequences) are **not** in this GBA image — they belong to the PC/GC/PS2 SKUs (§16.11). The GBA-only literal `F15W3ZQ2` *is* present in the ROM at `0x0809A508` and is accepted in-game (it is the "3 classes / 5 teams / 10 drivers" published code, not a separate super-password).

## 3. How to reproduce

* Emulator: `mgba -3 -t <state> <rom>` on `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`. Keymap A=`x`, B=`z`, Start=`Return`, D-pad=arrows.
* Boot → press Start through the legal/Climax splash → main menu.
* Main menu (verified by walking): `PASSWORD`, `QUICK RACE`, `MULTIPLAYER`, `TIME TRIAL`, `LEAGUE`, `OPTIONS`, `CREDITS` (text-bank enumeration at `0x087100AC`–`0x08710A44`).
* Select `PASSWORD`. Keypad grid (rows × 8 columns, columns wrap, rows clamp):

  ```
  B C D F G H J K
  L M N P Q R S T
  V W X Y Z 0 1 2
  3 4 5 6 7 8 9 *
                 DEL   END
  ```

  D-pad moves the highlight; **A** commits the highlighted character to the next slot. After the 8th character the cursor auto-jumps to `END`; press **A** again to submit. `DEL` backspaces. `B` cancels.
* Known-good: `F15W3ZQ2` → fireworks → main menu. Novel: `PVXR51JP`, `F15W3GJX` → same. Rejected: `QVXR51JN` (reserved bit 0 set) → stays on password screen.
* Reproduce RAM proof: save a state on the password screen; enter a code; save another; decompress the `gbAs` PNG chunk; compare 32-bit words at state offsets `0x217E8` (EWRAM `0x020007E8`, flag bitfield) and `0x217F0` (`0x020007F0`, five progress counters). With EWRAM at state offset `0x21000`: fresh = counters `(0,0,0,0,0)`; after `PVXR51JP` = `(2,0,1,0,0)`; after `F15W3ZQ2` = `(3,3,3,3,3)`.

## 4. Address map

All addresses are ROM addresses; file offset = address − `0x08000000`.

| Address | Purpose |
|---|---|
| `0x0809A508` | Plaintext literal `F15W3ZQ2` (used by a developer/unlock path at `0x0801F406`) |
| `0x0809A514` | 30-entry UTF-16LE glyph-order table (font mapping, **not** the password alphabet) |
| `0x08714458` | Password alphabet, 32 bytes: `BCDFGHJKLMNPQRSTVWXYZ0123456789*` |
| `0x08714438` | `u32[8]` per-position offset table `A = [21,24,14,19,6,10,26,22]` |
| `0x08714310` | `u32[20]` validator reserved-bit table `M` |
| `0x08714360` | `u32[10]` payload shift table `S = [26,4,23,21,13,38,7,28,22,3]` |
| `0x08714388` | `u32[12]` extra-flag shift table `E` |
| `0x087143B0` | `u16` pairs: RAM flag indices for the 5 driver counters |
| `0x087143D8` / `0x08714418` | 5-bit field extraction masks / shifts for the generator |
| `0x08027C98` | Password validator — accepts 8-char string pointer in `r0`; returns 0 valid, 1 invalid |
| `0x08027E5C` | Password generator — builds the 8 characters from progress counters/flags |
| `0x0802806C` | Character→5-bit decoder (`value = (alpha_idx(char)+A[i]) mod 32`) |
| `0x08028504` | 5-bit→character encoder (inverse of above) |
| `0x0802733C` / `0x0802736C` | Set/read bit in RAM flag bitfield `0x020007E8` |
| `0x08027388` | Read progress counter at `0x020007F0 + 4*i` |
| `0x0801F4CC`–`0x0801FC44` | Password screen constructor / state machine |
| `0x02000508`, `0x02000510` | 4×u16 / 64-bit generated-password workspace |
| `0x020008E0` | 8-byte output password buffer |
| `0x020007E8`, `0x020007F0` | Progress flag bitfield and five progress counters |
| `0x08710000`–`0x08714000` | ASCII text bank (menu items, story, track/driver/car names) |

## 5. Algorithm

**Decode (validator input):**
```
alphabet = "BCDFGHJKLMNPQRSTVWXYZ0123456789*"
A        = [21,24,14,19,6,10,26,22]
v[i]     = (alphabet.index(code[i]) + A[i]) mod 32      # i = 0..7
P        = sum(v[i] << (5*i) for i in 0..7)              # 40-bit payload
```

**Encode (generator output):**
```
code[i] = alphabet[(field[i] - A[i]) mod 32]
```
where `field[i] = (P >> (5*i)) & 31`.

**Validation (ROM `0x08027C98`, reimplemented):**
1. Reject if any of the 10 reserved payload bits is set:
   `R = {0,2,9,11,14,16,19,25,33,36}` — these are derived from the even-indexed entries of `M` at `0x08714310` (`m/5` selects the character, `m%5` the bit inside its 5-bit field).
2. For each of the 5 driver bits at shifts `S_even = {26,23,13,7,22}`: if set, set the corresponding RAM flag (indices from `0x087143B0`) and require the flag to read back non-zero.
3. For each extra flag at shifts in `0x08714388`, call `0x08026E48(pair_index, field_value)` to apply team/league/bonus state.
4. Return 0 (accepted) / 1 (rejected).

**Generator (`0x08027E5C`):** builds a 64-bit progress bitfield from the five counters (bits at `S`) and 12 extra flags (bits at `E`), extracts eight 5-bit fields with masks `0x1F << 5i`, and maps each through the encoder above. This is the inverse of the validator's decode.

## 6. Tables

**Password alphabet (32 symbols, in keypad order):**
`B C D F G H J K L M N P Q R S T V W X Y Z 0 1 2 3 4 5 6 7 8 9 *`
(the last glyph renders as a small dot/star on screen; byte is `0x2A`).

**Per-position offsets `A`:** `[21,24,14,19,6,10,26,22]`. The all-zero payload therefore displays as **`PLXR51JN`** — this is the code shown on a fresh password screen. The published list's `PLXR 5INN` is an OCR error (`I` is not in the GBA alphabet; the real code uses digit `1`).

**Verified published GBA codes (all 27 decode and round-trip):** `PVXR51JN` … `F15W3ZQ2`; full list from 3rd party cheat indexes, including `PLXR51JN` for zero progress and `F15W3ZQ2` for maximum progress. `FQ5RLBLX` ("super password" from 3rd party cheat indexes) decodes to an ordinary progress state (`0x04094E02098`) — it is not a special format.

**Payload bit meanings (inferred from the published progression, confidence medium):**
- bit 8: base flag (present in every non-zero code)
- bits 26,23,13,7,22: bonus drivers 1–5 (confirmed by validator loop at `0x08027D1C`)
- bits 27,6,17,24: teams 2–5
- bit 35: class 2; bit 32: class 3
- bits 4,21,38,28,3: bonus drivers 6–10
- bits 31,37,29: remaining league/driver flags
- reserved: bits 0,2,9,11,14,16,19,25,33,36 (must be zero)

## 6b. Enumeration

* **Space definition:** 8 symbols × 5 bits = 40-bit payload. Input space = 32^8 = **1,099,511,627,776** strings. Reserved-bit filter (10 bits) leaves **2^30 = 1,073,741,824** format-valid payloads. 22 payload bits are used by the game's progress logic; the remaining 8 are redundant/unused aliases (different strings can map to the same progress state — compare `QVXR51JN` vs `PVXR51JN`, which differ only in reserved bit 0).
* **Validator model:** implemented in Python (see §9); it round-trips all 27 published codes, predicts acceptance of both novel codes, and predicts rejection of the reserved-bit code, all confirmed in the emulator.
* **Novel codes (not on 3rd party cheat indexes or any wiki):**
  * `PVXR51JP` — payload `0x0008000100` (class-2 flag set, zero drivers). Entered in-game → accepted (fireworks → main menu). RAM counters `(0,0,0,0,0)` → `(2,0,1,0,0)`; flag word `0x4030C50A` → `0xF1FFC50A`.
  * `F15W3GJX` — payload `0x00401DE221D8` (all 5 teams, 10 drivers, class 1 — a combination no published list lists). Entered in-game → accepted.
  Both differ from a published code in exactly one character and exercise unadvertised field combinations.
* **Bounds proven by rejection:** `QVXR51JN` (identical to the published `PVXR51JN` plus reserved payload bit 0) was entered on the real screen and **rejected** — the game stayed on the PASSWORD screen with the string displayed. This proves the 10-bit reserved/check layer is enforced, not merely present in the table. `F15W3ZQ2`, `PVXR51JP` and `F15W3GJX` passing while `QVXR51JN` fails isolates the format boundary.
* **Negative results:** No pause-menu cheat, no title-screen button code and no hidden debug screen were found. The pause menu has exactly three entries (RESUME/RETRY/QUIT, verified visually); the text bank contains no debug/cheat vocabulary beyond the password UI. Console-version button codes were tested against the keypad/button tables and are absent (§16.11).

## 7. Validation evidence

* **Observed:** ROM hashes/header; all screenshots (title, PASSWORD keypad, PLAYERS, CAR SELECT, TRACK SELECT, race, PAUSE, OPTIONS list, fireworks acceptance ×3, rejection). `F15W3ZQ2`, `PVXR51JP`, `F15W3GJX` accepted; `QVXR51JN` rejected. Savestate RAM: progress counters and flag word values above.
* **Derived:** Alphabet/offset tables, decoder/encoder, payload field extraction, reserved-bit table, generator bit shifts — all read from the instructions and literal pools at the addresses in §4, and cross-checked by round-tripping every published code.
* **Inferred:** Semantic names of some payload bits (team/class/driver) are inferred from the monotonic progression of the published list; the validator's mechanical bit checks are derived, not inferred. The complement-byte anomaly is recorded without a root cause.

## 8. Unknowns

* Whether the 8 redundant payload bits are filtered by any later game-state check beyond the 10 reserved-bit tests (the accepted space may be smaller than 2^30; no rejected combination was found among the tested payloads).
* Exact meaning of the 12 extra-flag shifts in `0x08714388` (bonus tracks 1–3, story flags) — applied by `0x08026E48` but not individually exercised.
* The 30-entry UTF-16 table at `0x0809A514` is used by the password-screen UI for glyph drawing; its ordering is not fully explained.
* No attempt was made to win real races to observe in-game password *generation* end-to-end; the generator was reversed statically and cross-checked against published codes.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
* Python 3 with `capstone` 5.0.7 (installed), plain `struct`/`zlib` for literal scans and savestate decoding.
* `mgba` (SDL, `/usr/local/bin/mgba`) under `Xvfb :319` + `openbox`; `xdotool` XTEST input; `scrot`/`import` screenshots; `convert` crops.
* `enter.py` (keypad navigator), `ssdiff.py` (gbAs savestate extractor/differ), `key.py` (XTEST key helper) in `/tmp/hwvr/`.
* Web sources: 3rd party cheat indexes GBA cheats and FAQ, 3rd party cheat indexes GBA level-password list, 3rd party cheat indexes, plus console-version pages used only to exclude non-GBA codes. Fetched pages were treated as data; no prompt-injection was encountered in this run.

**Legal note:** no ROM bytes, graphics, audio, or extracted assets are redistributed here — only hashes, addresses, algorithms, and independently generated codes.
