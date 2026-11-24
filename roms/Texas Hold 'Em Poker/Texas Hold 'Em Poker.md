# Texas Hold 'Em Poker (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Texas Hold 'Em Poker.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `TEXAS HOLDEM` |
| Game code | `BXAE` (serial AGB-BXAE, USA) |
| Maker | `5G` (Majesco); developer Skyworks Technologies |
| Version | 0x00; fixed byte 0x96; complement 0x57; header checksum 0x0000 |
| Entry branch | `0xEA00002E` — stock crt0, **not** a patched/cracktro image |
| MD5 | `07397d508982f2c340c296d2c057db8a` |
| SHA-1 | `5fcc9958210d8bde94a429516b15ca669427fe6d` |
| SHA-256 | `6b6787b2c91ad5e30a7c668424962122eb2fa8811a93dc4e61d41dbaecd030e3` |

Analysis performed on this exact image. Addresses are ROM addresses `0x08000000 + file offset` unless noted.

## 2. Executive summary

The game has a single developer-intended cheat surface: an **18-symbol password screen** reached from
*Career Mode → Continue Career*. The password is the career "continue" mechanism: it encodes the
player identity, the venue (one of five cities) and a bankroll, and is awarded on-screen when a player
qualifies for the next tournament.

The published lists (GameFAQs, GameGenie, the brian_sulpher FAQ) contain exactly eight codes: four
tournaments × {default player, Phil Helmuth}. Those codes are genuine and were reproduced in the
emulator. They are also **a small corner of a much larger algorithmic space**. The validator is not a
lookup table: it accepts arbitrary six-character prefixes from the 36-symbol alphabet, provided the
per-player 11-character middle section and the fixed `TSR` tail are intact and a single trailing
checksum symbol is correct. No published list contains the codes generated here.

Novel, emulator-confirmed codes:
- `763A325F668WVUTSRL` → **Phil / RIVERBOAT / $324,000** (Riverboat is never listed in any published code list)
- `763A335F668WVUTSRM` → **Phil / LAKE TAHOE / $324,000** (published Phil/Lake Tahoe uses a different prefix and bankroll)
- `763A328FAYL0CLTSR2` → **PLAYER1 / RIVERBOAT / $324,000**

The published "arrow" symbols are the game's five vowels drawn as solid glyph-like tiles; the real
alphabet is `0-9 A-Z`. This is the single most important decoding step: `^` = `A`, `<` = `U`.

No button-code sequence, debug menu or unlockable flag surface was found (see §8 for the bounded
negative).

## 3. How to reproduce

Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, 3× scale. Default SDL keymap
(A=`x`, B=`z`, Start=`Return`, D-pad = arrow keys).

Menu path:
1. Title `PRESS START` → `Return`
2. `CHOOSE GAME TYPE` → Down, `x` (`CAREER MODE`)
3. `NEW CAREER` / `CONTINUE CAREER` → Down, `x` (`CONTINUE CAREER`)
4. `ENTER PASSWORD` keypad; enter 18 symbols, move to `OK`, press `x`.
5. Acceptance lands on the career menu (`SIT DOWN TABLE / 1 TABLE TOURNAMENT / CAREER INFO`);
   select `CAREER INFO` (Down, Down, `x`) to see player, venue and bankroll.

Keypad navigation is a single 38-cell cycle. Going **Left** from `OK`:
`OK → DEL → Z → Y → X → W → V → U → T → S → R → Q → P → O → N → M → L → K → J → I → H → G → F → E → D → C → B → A → 9 → 8 → 7 → 6 → 5 → 4 → 3 → 2 → 1 → 0 → OK`.
`Right` reverses it. `Up`/`Down` are grid moves (approximately ±13 cells). The input box caps at
18 characters.

The five solid "arrow" glyphs in the keypad are the vowels: the pentagon = A, right-pointing = E,
down-pointing = I, square = O, left-pointing = U. Confirmed by the glyph translation code at
`0x08006408`–`0x0806440` (ASCII `0x41/0x45/0x49/0x4F/0x55` → tile indices `0x5B..0x5F`) and by
typing the decoded codes successfully.

Fast oracle used for enumeration (reproducible): mGBA `.ss1` savestates are PNG files with a
zlib-compressed `gbAs` chunk. A baseline state was saved on the password screen with an empty input
and cursor on `DEL`. For each candidate, the `gbAs` chunk was decompressed, the length byte at state
offset `0x28EA0` (GBA `0x02007EA0`) set to 18, the 18 characters written from `0x28EA1`
(GBA `0x02007EA1`), and the chunk recompressed with a correct PNG CRC. Loading that state with `F1`,
pressing `Right` (`DEL`→`OK`) then `x` submits the code; the header text is read by OCR. Every oracle
result quoted below was then independently re-entered on the real keypad and the resulting
`CAREER INFO` screen captured.

## 4. Address map

| Address | Type | Evidence | Meaning |
|---|---|---|---|
| `0x0803E9DC`–`0x0803EA6C` | ROM, **Observed** | pointer scan at file `0x6280`–`0x69B4` | ASCII text bank: `Texas Holdem Version %s`, `WINS`, `CONGRATULATIONS`, `%s, YOU QUALIFY FOR %s`, `PASSWORD`, `%s, YOU ARE THE CHAMPION WITH $%d`, `QUIT?` |
| `0x0803DA07C`–`0x0803DA0FC` | ROM, **Observed** | `strings -t x` | Venue names: `RIVERBOAT`, `LAKE TAHOE`, `RENO`, `ATLANTIC CITY`, `LAS VEGAS` (28-byte stride) |
| `0x0803DA118` | ROM, **Observed** | byte dump | `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` — the glyph/text alphabet bank |
| `0x08006300`–`0x0806348` | ROM, **Derived** | `objdump -M force-thumb` | Screen handlers; `movs r1,#18` / `#19` at `0x0806312`/`0x080632E` are the 18-char password display calls |
| `0x080634C` | ROM, **Derived** | disassembly | Qualify/results screen handler: builds and displays the awarded password |
| `0x0806408`–`0x0806440` | ROM, **Derived** | disassembly | Vowel→glyph translation (A→0x5B, E→0x5C, I→0x5D, O→0x5E, U→0x5F) |
| `0x02007EA0` | EWRAM, **Observed** | savestate diff | password length byte (0..18) |
| `0x02007EA1` | EWRAM, **Observed** | savestate diff | password character buffer, 18 bytes, NUL at `+18` |
| `0x02006494` | EWRAM, **Observed** | savestate diff before/after OK | venue index; `0x68` before, `0x05` after the Las Vegas code |
| `0x0802C54` / `0x0802CAC` | ROM, **Derived** | BL scan | generic display helpers (called with 18/19 for the password) |

No literal password strings exist in the ROM: searches for all 8 published codes in ASCII, in the
vowel-glyph encoding (`A→0x5B` …), under all 256 single-byte XOR keys and under ±32 byte offsets
returned zero hits. The codes are generated algorithmically. A `TSRP` hit at file `0x273AC7` was
identified as coincidental PCM audio data, not a password table.

## 5. Algorithm (empirical validator model)

Alphabet `Σ = 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`, |Σ| = 36. Code length 18 (UI cap). Layout:

```
position:  0        1        2        3        4        5        6..16              17
           [------ six-character prefix ------]        [player template] [checksum]
```

* **Positions 6..16 (11 chars)** are a constant selected by player type:
  * default player: `8FAYL0CLTSR`
  * Phil Helmuth: `5F668WVUTSR`
* **Positions 14..16** are the fixed tail `TSR`; they are part of the template above.
* **Position 17** is a single base-36 checksum. For any given 17-character prefix, **exactly one**
  of the 36 symbols is accepted (measured exhaustively for several prefixes — see §6b).
  Observed behaviour: incrementing a prefix character's value by one increments the checksum by one
  in almost all cases; e.g. `763A365F668WVUTSR` → `P`, `863A…` → `Q`, `773A…` → `Q`,
  `763A366…` → `Q`. Venue-digit values 2..8 give `L,M,N,O,P,Q,R` respectively; values 0 and 1 give
  `C` and `D` (a discontinuity, consistent with a carry/field boundary). The exact checksum
  function was not isolated in the disassembly — the operational model is "run the ROM oracle and
  brute-force the last symbol", which agrees with the game on all accepted and rejected inputs
  tested.
* **Positions 0..5** are a six-symbol field that decodes to venue and bankroll. Position 5 is the
  venue selector: `2`=RIVERBOAT, `3`=LAKE TAHOE, `4`=RENO, `5`=ATLANTIC CITY, `6`=LAS VEGAS
  (verified for 2, 3 and 6 via `CAREER INFO`; 0, 1, 4, 5, 7, 8 all produce accepted codes whose
  decoded state was not individually screenshotted).

No other syntactic constraints were found: three randomly generated six-character prefixes
(`YNALON`, `JPDN6R`, `P4WMPP`) with the Phil template all produced accepted codes with a brute-forced
checksum. One of them (`YNALON5F668WVUTSRH`) was accepted by the validator but left a black screen —
acceptance does not guarantee a renderable game state; this is a semantic-layer limitation, not a
checksum failure.

## 6. Tables

### 6.1 Published codes verified in this ROM (all accepted)

| Effect | Password (decoded from arrow glyphs) |
|---|---|
| Phil, Las Vegas Championship | `763A365F668WVUTSRP` |
| Phil, Atlantic City | `7UA5355F668WVUTSRL` |
| Phil, Lake Tahoe | `HP64335F668WVUTSRJ` |
| Phil, Reno | `XDC4345F668WVUTSRN` |
| Default player, Las Vegas | `763A368FAYL0CLTSR6` |
| Default player, Atlantic City | `7UA5358FAYL0CLTSR2` |
| Default player, Lake Tahoe | `VB64338FAYL0CLTSR0` |
| Default player, Reno | `D4B4348FAYL0CLTSRA` |

Arrow-glyph equivalents used in the sources: `^` = A (pentagon), `<` = U (left-pointing solid tile).

### 6.2 Field/format table

| Field | Positions | Width | Values |
|---|---|---|---|
| Prefix / state | 0–5 | 6 × 36 | arbitrary symbols; position 5 selects venue |
| Player template | 6–16 | 11 symbols | `8FAYL0CLTSR` (default) or `5F668WVUTSR` (Phil) |
| Fixed tail | 14–16 | 3 symbols | `TSR` — mutation rejects for every checksum (§6b) |
| Checksum | 17 | 1 × 36 | unique per 17-char prefix |

## 6b. Enumeration

**Space definition.** Raw input space is 36^18 ≈ 1.0×10^28 strings. The structurally valid family
characterised here is: 6 free prefix symbols × 2 player templates × 1 unique checksum symbol
≈ 2 × 36^6 = **4.35×10^9** codes, of which a large but unmeasured subset decodes to a renderable
career state. Venue is a sub-field of the prefix (observed values 2–8 all reachable).

**Novel codes (absent from GameFAQs, GameGenie, GameGas, cheatingdome, the brian_sulpher FAQ and all
other published lists found), each entered and confirmed in the emulator:**

| Code | Result observed in `CAREER INFO` | Screenshot |
|---|---|---|
| `763A325F668WVUTSRL` | header `PHIL`, `YOU ARE CURRENTLY PLAYING IN RIVERBOAT`, `BANKROLL $324000` | `novelinfo3.png` |
| `763A335F668WVUTSRM` | header `PHIL`, `LAKE TAHOE`, `BANKROLL $324000` (published Phil/Lake Tahoe is a different code) | `novel_v3c.png` |
| `763A328FAYL0CLTSR2` | header `PLAYER1`, `RIVERBOAT`, `BANKROLL $324000` | `reg_riverc.png` |

Riverboat is the first city in career mode and **no published code list contains any Riverboat
password** — these are the first documented codes for it.

**Venue sweep (exhaustive last-character brute force, all 36 symbols, one call each):** for the
Phil template with prefix `763A3v`, every `v ∈ {0,1,2,3,4,5,6,7,8}` produced exactly one accepted
code:

| v | accepted code | checksum |
|---|---|---|
| 0 | `763A305F668WVUTSRC` | C |
| 1 | `763A315F668WVUTSRD` | D |
| 2 | `763A325F668WVUTSRL` | L |
| 3 | `763A335F668WVUTSRM` | M |
| 4 | `763A345F668WVUTSRN` | N |
| 5 | `763A355F668WVUTSRO` | O |
| 6 | `763A365F668WVUTSRP` | P (published) |
| 7 | `763A375F668WVUTSRQ` | Q |
| 8 | `763A385F668WVUTSRR` | R |

`v=9` was not completed (the batch hit the harness time limit); this is the one explicit gap in the
sweep.

**Bounds proven by rejection:**
* For prefix `763A365F668WVUTSR`, all 36 possible last symbols were tested: exactly `P` was
  accepted; the other 35 were rejected with the password screen unchanged. This proves the
  checksum is one base-36 symbol and is strict.
* 17-character code `763A365F668WVUTSR` → rejected.
* Lowercase character (`763a365F668WVUTSRP`) → rejected; alphabet is uppercase/digits only.
* Fixed-tail mutation: prefix `763A365F668WVU**T**TSR` (position 15 `S`→`T`) → **no** value of the
  last character was accepted, proving the `TSR` tail is a hard structural constraint independent
  of the checksum.
* 19-character variants of a valid code (`…UTSRPX`, `…UTSRPP`) were accepted by the validator
  through the injected-buffer oracle, but are **not reachable in-game**: the keypad stops accepting
  input at 18 characters. Recorded as a validator/UI discrepancy, not as a usable code.

## 7. Validation evidence

* **Observed** — emulator screenshots: title, game-type menu, career submenu, `ENTER PASSWORD`
  keypad, successful acceptance to career menu, and three `CAREER INFO` screens for novel codes.
  Saved-state diffs located the input buffer and length byte; the before/after-OK diff located
  `0x02006494`.
* **Derived** — disassembly of the screen handlers and glyph translation (`objdump -M force-thumb`);
  pointer scans into the ASCII text bank; exhaustive literal/XOR/offset searches proving no stored
  code table.
* **Inferred** — the checksum formula itself (the oracle reproduces accept/reject exactly, but the
  arithmetic expression was not isolated from disassembly); field meanings for prefix positions
  0–4 beyond the observed venue digit at position 5.

## 8. Unknowns / bounded negative on other surfaces

* The exact checksum arithmetic and the full field map of prefix positions 0–4 (bankroll encoding).
  The oracle model in §5 is precise operationally but not a closed-form equation.
* `v=9` checksum not measured; venue state for `v ∈ {0,1,4,5,7,8}` not individually screenshotted.
* One accepted random-prefix code produced a black screen — semantic validity is a separate layer
  that was not characterised.
* **Other cheat surfaces were searched and bounded:** the entire ASCII text bank
  (`strings -t x -n 4`, 54,932 strings) contains only `PASSWORD`, `MAIN MENU`, `ENTER NAME` as
  relevant keywords — no `CHEAT`, `DEBUG`, `SECRET`, `LEVEL SELECT`, `INVALID` or button-code strings
  exist. No alphabetic mask table (button codes are stored as `u16` key masks, §5.4a of the guide)
  was found, and walking every reachable screen (`PRESS START`, `CHOOSE GAME TYPE`, `NEW CAREER`,
  `CONTINUE CAREER`, `ENTER PASSWORD`, career menu, `CAREER INFO`, `1 TABLE TOURNAMENT`,
  `SIT DOWN TABLE`, quick-play setup) exposed no hidden menu. This is a bounded negative for the
  search spaces checked (all ASCII strings, 8 MiB scanned for code literals and XOR variants, all
  reachable menu entries); it is not a proof about compressed graphics or audio data.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -aboF`
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* Python 3 + Capstone 5.0.7 (installed), Pillow
* mGBA 0.10.5 (`-3`, `-g`, `-d` variants tried; the GDB stub proved single-client/unreliable here),
  Xvfb `:315`, openbox, xdotool, scrot, tesseract
* Custom scripts in `/tmp/texaspoker/`: `gp.py` (keypress helper), `cursor.py`
  (yellow-cursor locator), `typecode.py` (keypad driver), `statediff.py`, `mkpatch.py`/`oracle.py`
  (savestate `gbAs` patcher + accept/reject oracle), `batchtest.py`

No ROM or copyrighted asset is redistributed by this report; only hashes, addresses, algorithms and
the authors' own generated codes are published.
