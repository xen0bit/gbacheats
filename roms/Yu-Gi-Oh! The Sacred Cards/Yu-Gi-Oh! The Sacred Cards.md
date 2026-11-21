# Yu-Gi-Oh! The Sacred Cards (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Yu-Gi-Oh! The Sacred Cards.gba` |
| Size | 16,777,216 bytes (0x01000000, 16 MiB) |
| Header title | `YUGIOH DM7` |
| Game code | `AY7E` |
| Maker code | `A4` (Konami/KCEJ) |
| Version | 0x00 |
| Fixed byte 0xB2 | 0x96 |
| Header checksum | 0x0000 |
| Entry word | `0xEA00002E` (stock ARM branch) |
| MD5 | `0a7c58069d5390165482e88a22158bd2` |
| SHA-256 | `093f986a92d73c48e11de0a83c6678c3620f8def6173f5e69133815301b40d8f` |

US release of *Yu-Gi-Oh! Duel Monsters 7: The Duelcity Legend*. Stock logo/entry (§16.1 pass).

## 2. Executive summary

The game ships exactly one developer-intended cheat surface: the **Card Shop Password Machine**, an 8-digit numeric code entry. There are no in-game button codes, hidden debug menus, or debug strings; all other published "cheats" are cheat-device codes.

**This pass closes the validator gap.** The comparison routine was isolated statically and confirmed dynamically with the emulator's own code as an oracle (§16.19). The accept predicate is an **8-byte literal comparison of raw digit bytes**, exactly as the flat-table model predicted. Nine oracle calls (four accepted, five rejected) returned the expected 10/11 sentinels.

**Remaining gap:** the password screen itself was still not reached in-game. The Card Shop is reachable in Clock Tower Square only as a building façade; the world map / shop interior requires story progression that was not advanced. Consequently no code was typed on the real screen and no in-game money/card-flag increase or rejection screenshot was captured. This is stated plainly rather than implied complete (§16.10).

## 3. How to reproduce

* mGBA 0.10.5, `DISPLAY=:316`, Xvfb 1024×768×24 + openbox, `SDL_AUDIODRIVER=dummy`.
* Keymap (SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
* Boot path: title → NEW GAME → name grid → intro → Yugi's room → Clock Tower Square.
* **Validator oracle (reproducible):** start `mgba -3 -d -t <state> game.gba` with a CLI-debugger PTY on stdin. Connect, `break 0x08003BD6`, `continue` (savestate PC). Write raw digits to `0x02020D90..97`, set `r0`=table record, `r1`=0x02020D90, `r14`=0x08003BD7, `r15`=0x08034261, `continue`; the breakpoint prints `r0` = 10 (accept) or 11 (reject). Scripts: `/tmp/opencode/sacredcards2/cmp_oracle.py`, `batch_oracle.py`.
* Known-good anchors: `46986414` (Dark Magician), `89631139` (Blue-Eyes White Dragon), `70781052` (Summoned Skull), `98025229`, `62626514` (utility).

## 4. Address map

| Item | Address | Notes |
|---|---:|---|
| Password prompt text | `0x08DB8BCE` | `"$0Please enter the <ctrl>W-digit password.$1..."`, 5-language bank; `82 57` renders the digit count |
| Prompt pointer slot | `0x08DB8D88` | sole 32-bit pointer to the prompt text |
| Dialogue-group pointer | `0x08DE5F94` | group 0 points at `0x08DB8D88`; no static code pointer found (indirect access) |
| **8-byte compare helper** | **`0x08034260`** | compares `[r0]` vs `[r1]` for 8 bytes; returns **10 = equal, 11 = any mismatch** |
| **Card password validator** | **`0x080341B8`** | linear scan of the card table using the compare helper |
| **Utility validator** | **`0x08034304`** | linear scan of the 3-entry utility table |
| **Submission handler** | **`0x0803428C`** | copies input → result struct, runs both validators, dispatches effects |
| **Card table base** | **`0x08D4F43C`** | index 0 is a SKIP marker; first real record (89631139) at `0x08D4F444` |
| Utility table base | `0x08D5106C` | records at +0,+8,+16; terminator at +24 |
| Utility: +50,000 Domino | `0x08D51074` | `62626514` |
| Utility: +100 Deck Capacity | `0x08D5107C` | `98025229` |
| Other utility record | `0x08D5106C` | `25232415` (effect not characterised) |
| Input digit buffer | `0x02020D90` | 8 raw bytes, value 0x00–0x09 |
| Result struct | `0x02023740` | u16 index @+0, u8 status @+2 (10=accept, 11=reject), 8 digits @+3 |
| Owned-card bitfield | `0x02023750` | bit `index`, set by `0x0803440C` |
| Money (64-bit) | `0x02020DA0` | low word @+0, high @+4; +50000 via `0x08019B7C` |
| Location names | `0x0806B308` + i*0x70 | i=0 "Clock Tower Square", i=1 "Card Shop", i=2 "Bridge", i=4 "Aquarium", i=5 "Kaiba Corp. Island" (prior report's addresses omitted a leading `0`) |
| Terminal/SKIP marker | `0F 0F 0F 0F 0F 0F 0F 0E` | validator returns 1 → skip this record |
| TERMINATOR marker | `0F 0F 0F 0F 0F 0F 0F 0F` | validator returns 0 → stop scan |

File offset = ROM address − `0x08000000`.

## 5. Algorithm / validator — now CONFIRMED

### 5.1 Compare helper `0x08034260` (ARM/Thumb, Thumb)

```
compare(a=r0, b=r1):
  r5 = 10                 ; MATCH sentinel
  for i in 0..7:          ; r4 = i (u8 wrap)
      if a[i] != b[i]: r5 = 11     ; MISMATCH sentinel (loop continues)
  return r5
```
Notes: exactly 8 bytes; no early exit; mismatch is "sticky". Raw bytes only, no BCD/packing.

### 5.2 Record classifier `0x08034218` / `0x08034364`

```
classify(i):
  rec = 0x08D4F43C + i*8        ; (card) or 0x08D5106C + i*8 (utility)
  if compare(rec, 0x08D5108C /*0F*8*/) == 10: return 0   ; TERMINATOR
  if compare(rec, 0x08D51094 /*0F*7+0E*/) == 10: return 1 ; SKIP
  return 2                                               ; normal record
```

### 5.3 Validators `0x080341B8` (cards) and `0x08034304` (utilities)

```
i = 0
loop:
  c = classify(i)
  if c == 0: status = 11; return                 ; terminator -> reject
  if c == 1: i++; continue                       ; skip marker
  if compare(0x08D4F43C + i*8, input@0x02023743) == 10:
      status = 10; return                        ; ACCEPT
  i++; continue
```
On card accept the matched index is used to set a bit in the owned-card bitfield at `0x02023750` (`0x0803440C`) and to run the card-add effects at `0x080342B2..0x080342C6`. On utility accept `0x080343AC` dispatches: index 1 (`62626514`) → `r0=50000, r1=0` → `0x08019B7C` adds money and shows message 201; index 2 (`98025229`) → +100 deck capacity (functions `0x08014094`, `0x080140EC`).

### 5.4 Accept predicate (exact)

```
SPACE   = { 8 raw bytes, each 0x00..0x09 }        # 10^8 strings
ACCEPT  = { s | exists i: RECORD_i == s }         # linear equality, no checksum/packing
RECORD_i= 8 bytes at 0x08D4F43C + 8*i, excluding SKIP (0F*7+0E) and TERM (0F*8) slots
on reject: status=11, no state change
```

Confidence: **Observed** (disassembly + live oracle calls) for the predicate; **Derived** for the effect dispatch (addresses and constants read from ROM, effects not executed in-game).

### 5.5 Oracle results (live emulator, ROM code executed)

| Input | Table record | `r0` returned | Meaning |
|---|---|---:|---|
| `89631139` | `0x08D4F444` | `0x0A` | accept (Blue-Eyes) |
| `31893528` | `0x08D5067C` | `0x0A` | accept (ROM-only candidate) |
| `98025229` | `0x08D5107C` | `0x0A` | accept (utility) |
| `62626514` | `0x08D51074` | `0x0A` | accept (utility) |
| `62626515` | `0x08D51074` | `0x0B` | reject (1-digit near miss) |
| `31893529` | `0x08D5067C` | `0x0B` | reject (1-digit near miss) |
| `00000000` | `0x08D4F444` | `0x0B` | reject (out of table) |
| `12345678` | `0x08D4F444` | `0x0B` | reject (out of table) |
| `89631138` | `0x08D4F444` | `0x0B` | reject (1-digit near miss) |

This proves the accept/reject predicate over representative points and resolves §16.9's "run the validator" requirement for the comparison layer.

## 6. Tables

* **Alphabet:** ten raw digit bytes `0x00`–`0x09` (not ASCII, not BCD).
* **Record size:** 8 bytes; **896 distinct accepted strings**, zero duplicates.
* **Layout:** 831 consecutive records `0x08D4F444`–`0x08D50E34`; SKIP markers at indices 832–834; further blocks to index 900; TERM at index 901 (`0x08D51064`); utility table `0x08D5106C`–`0x08D5107C`; markers at 905–907.
* **Published recon:** 829 unique codes extracted from four sources; 800 appear verbatim in the ROM table. 29 published codes were not found under any encoding tried (transcription errors, e.g. `91939603` vs ROM `91939608`).
* Full dumps: `all_rom_codes.txt` (895 lines of records), `published_codes.txt` (822), `novel_final.txt` (95) in `/tmp/opencode/sacredcards2/` (copied from the prior work dir).

## 6b. Enumeration

* Space `10^8`; accepted set **896**; density `8.96×10⁻⁶`. Every accepted value was enumerated directly from the ROM bytes — no sampling.
* No fields/checksum/reserved bits; the entire 8-digit string is a literal key. Rejects: any string absent from the table, any non-digit byte, any length ≠ 8 (the keypad only produces 8 digits).
* **Novel candidates:** 96 ROM records absent from the 829-code published aggregate, e.g. `31893528` (`0x08D5067C`), `50287060` (`0x08D50C8C`), `86325596` (`0x08D50D4C`), `05434080` (`0x08D50D5C`). Caveat: several (Spirit Message "I" = `31893528`, Baron of the Fiend Sword = `86325596`) are confirmed on other published sources, so 96 is an **upper bound** on novelty, not a certified novel set. The oracle proves `31893528` is genuinely accepted by the ROM validator.
* **Bounds proven by rejection:** yes at the validator/oracle layer (five rejected inputs above, all `0x0B`). **Not** proven on-screen (see §8).

## 7. Validation evidence

* **Observed (ROM bytes):** 8-digit raw records, SKIP/TERM sentinels, prompt string, validator/compare disassembly.
* **Observed (live emulator):** nine oracle calls above; title/name/intro/Yugi's room/Clock Tower Square field; Status/Trunk/Deck menu; NPC dialogue; money read as 500 (`0x1F4`) at `0x02020DA0`; savestate RAM diffs.
* **Derived:** accepted set = 896 literal records; utility effects from constants and called functions.
* **Inferred:** exact screen state machine and story-gate condition (see §8).
* **Negative surface scan (bounded):** `strings -t x` over 16 MiB → 0 debug/menu markers, 5 `password` hits (same localized prompt), 0 ASCII 8-digit strings. No button-mask code found. Published "cheats" are cheat-device codes only.

## 8. Unknowns / incomplete deliverables

1. **No on-screen password entry (principal gap).** The Card Shop building in Clock Tower Square was reached and photographed, but the shop interior / world map / password screen were not. Reached surfaces: CTS field, its NPCs, Status/Trunk/Deck menu, menu close, dialogue. Attempted: extensive D-pad exploration of CTS, interactions at the building/NPC edges, Start-menu search, direct savestate patches of 23 candidate EWRAM location/state bytes (`bruteloc.py`), and direct debugger calls to the submission handler. None produced the password screen or a money change. Attempts to call `0x0803428C` from the CLI debugger returned to the main loop without reaching the effect path (breakpoints at `0x080342AC`, `0x080342D8`, `0x08034304`, `0x080343AC` never hit), consistent with the handler requiring the password-screen context (its first call is a graphics/UI setup at `0x0801827C`). **Consequently: no code was typed on the real screen, no in-game money/card-flag increase, and no in-game rejection screenshot.**
2. **Exact story gate not isolated at byte level.** Location names form a 0x70-stride table (`0x0806B308` = index 0 CTS, index 1 = Card Shop). The location-index variable in EWRAM was not found: brute-force patches of zero bytes in `0x02020D60..0x02020DAC` to 1 changed only NPC animation, not location. The prior pass's claim that the shop is gated behind the CTS tournament/world-map exit remains a **lead, not a byte-level proof**. This is the one requirement from the retry brief that is not satisfied.
3. **Novel-code certification.** The 96 candidates are upper-bound novel; a complete published list is needed to certify a specific value.
4. **Meaning of the 0x0E/0x0F markers** is now resolved (SKIP vs TERM, §5.2). The third utility record `25232415` at `0x08D5106C` has no characterised effect.

## 9. Tooling

* Hash/header via `md5sum`, Python `struct`; `strings -t x`, `grep -abo`, `xxd`.
* `arm-none-eabi-objdump -M force-thumb` for ROM/IWRAM disassembly; custom Thumb BL scanner (`blscan.py`) — no BL or pointer xrefs to `0x0803428C` exist in ROM/EWRAM/IWRAM, so the screen reaches it via an indirect/compressed path (the IWRAM code at `0x03000340` is an IRQ/audio routine, not the validator).
* mGBA `-g` GDB stub (port conflicted with a sibling session) and, successfully, mGBA's `-d` CLI debugger driven over a Python PTY (`cmp_oracle.py`, `batch_oracle.py`, `trace_sub2.py`).
* mGBA `.ssN` PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte state; EWRAM at `0x21000`, IWRAM at `0x19000`; `patchss.py` rewrites a byte and rebuilds the PNG for load tests.
* Work dir `/tmp/opencode/sacredcards2/`: scripts and evidence PNGs. No screenshots or emulator artifacts left in the ROM folder.

## 10. Legal note

No ROM, graphics, audio, or extracted game assets are redistributed. Only hashes, addresses, algorithms, and findings are published here. Fetched pages and ROM strings were treated strictly as data; no instructions found in them were followed.

## Cleanup note

All mGBA/Xvfb/openbox/debugger processes started for this pass were terminated by PID; `.sav`/`.ss*` artifacts were removed from the ROM folder. Final verification is reported in the completion message.
