# Mega Man Battle Network 6: Cybeast Falzar (GBA) — Reverse Engineering Report

> **SKIPPED / DEFERRED — entry system found but not in-game confirmed (coordinator decision).**
> Under §0.2 this report does **not** meet the dynamic-confirmation bar: a Lotto/Number Trader
> system exists and 29 published 8-digit codes were recovered from the Mega Man Wiki, with the
> tile-indexed password/Number Trader text banks located (PASSWORD at file 0x762350, Number
> Trader dialogue at 0x76A200-0x76A500), but exhaustive encoding sweeps found zero literal code
> occurrences (the set is compressed or algorithmic), the validator was not isolated, and the
> entry screen is **story-gated**, so no code was entered and accepted in-game and no rejection
> bounds were produced. Per coordinator authorization, MMBN titles whose validator/code-entry
> surface is blocked by a story gate are documented here and **skipped rather than retried or
> indexed**. The published code list is recorded in §6.1. This report is intentionally absent
> from `INDEX.md`.

Queue position 463. All addresses below are file offsets; add `0x08000000` for the
ROM address. Evidence labels: **Observed** (emulator/screenshot/RAM), **Derived**
(disassembly/static), **Inferred** (plausible but not exercised).

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mega Man Battle Network 6: Cybeast Falzar.gba` |
| Size | 8,388,608 bytes (`0x800000`) |
| `file` identification | Game Boy Advance ROM image: "MEGAMAN6_FXX" (BR6E08, Rev.00) |
| Header title | `MEGAMAN6_FXX` |
| Game code | `BR6E` |
| Maker | `08` (Capcom) |
| Version | `0x00` |
| Fixed byte `0xB2` | `0x96` |
| Header entry word | `0xEA000032` → branch target `0x000000D0` |
| Header checksum `0xBE` | `0x0000` (computed `0xFA19`) |
| Header complement `0xBD` | `0x59` (computed `0x72`; `sum(0xA0..0xBC)+0xBD = 0xE7`) |
| MD5 | `1e8c774ba210d1c55113531c7360c737` |
| SHA-1 | `0676ecd4d58a976af3346caebb44b9b6489ad099` |
| SHA-256 | `a37c1028adb72082b51e142321fa437967bc54b6f46730a53f6581ad455ad670` |

**Phase 0 result (Observed/Derived).** One Nintendo-logo hit only (file `0x00000000`),
so this is a normal single-image 8 MiB retail ROM, not a multiboot pack. The entry
word branches to `0xD0`, immediately after the 16 zero bytes at `0xC0–0xCF`; the
ARM crt0 there is ordinary (stack/IWRAM/ROM-copy setup), with no cracktro or
appended trainer. The stale checksum and complement indicate a scene-rebuilt
header, a normal artifact (guide §16.1); the game code/title/version are intact.

## 2. Executive summary

The game **does** have an in-game, developer-intended password system: the
**Lotto Number / Number Trader** machine (inside Higsby's shop and AsterLand),
whose published 8-digit codes award Battle Chips, Sub Chips, Navi Customizer
programs and Key Items. This is confirmed by external documentation (Mega Man
Wiki "Lotto Number" page, retrieved via the Fandom MediaWiki API) **and** by the
ROM's own text banks, which contain the Number Trader dialogue and a password
entry help string.

The central result of the ROM search is a **bounded negative on storage form**:
all 29 published MMBN6 Lotto Numbers were searched in the ROM under 768 distinct
encodings (ASCII, u32 LE/BE, raw digits 0–9, packed and nibble-swapped BCD, every
additive `byte+k`, every XOR `byte^k`, reversed forms, 16/32-bit-per-digit,
7-digit prefixes/suffixes and rotations) with **zero hits**. The accepted set is
therefore not stored as plaintext or a simply encrypted consecutive table; it is
either compressed in a script block or computed by an algorithmic validator at
runtime. The validator itself was **not isolated** in this engagement — see §8.

A second, independent result: **no title-screen button code exists on the
reachable title screens**. Five combinations were pressed with before/after
savestate RAM diffing; none produced a state change distinguishable from the
no-input baseline except combinations containing A/Start, which simply start a
new game. The title menu contains exactly one item ("NEW GAME") and offers no
hidden menu.

All reachable screens were walked with screenshots and RAM evidence: title
splash, "PRESS START", title menu, all eight PET menu entries, and the overworld
rooms reachable before the story gate. The Number Trader screen is **story-gated**
(guide §16.3, category 4): reaching it requires advancing past the opening
classroom/Expo sequence, which was not completed here.

## 3. How to reproduce

1. **Emulator/display.** mGBA under Xvfb on the dedicated display:
   ```bash
   Xvfb :318 -screen 0 1024x768x24 &
   DISPLAY=:318 openbox &
   DISPLAY=:318 SDL_AUDIODRIVER=dummy mgba -3 <rom.gba> &
   ```
   Keymap verified by pressing keys on visible menus: `x` = A, `z` = B (B does
   not close the PET menu; Start/Return does), `a` = L, `s` = R, arrows = D-pad,
   `Return` = Start, `BackSpace` = Select. Hold keys 100–150 ms.
2. **Title screen.** Splash → "PRESS START" → press Start → menu shows a single
   green-triangle "NEW GAME". Down/Up/Left/Right/B/L/R/Select produce no new menu.
3. **PET menu.** Press Start in the overworld. Items, top to bottom:
   `ChipFolder`, `Sub Chip`, `Library`, `MegaMan`, `E-Mail`, `KeyItem`, `Comm`,
   `Save`. `Comm` opens `NETWORK` with `LINK CBL` and `WRLS ADPT`.
   `E-Mail` reports "You haven't gotten any mail yet, Lan."
4. **Screenshots** are in `/tmp/opencode/mmbn6falzar/` (`s27_title.png`,
   `s29_title_menu.png`, `s09_startmenu.png`, `s11_chipfolder.png`,
   `s13_email.png`, `s14_comm.png`, `m_library.png`, `m_megaman.png`, `m_now.png`,
   `s42_pet_check.png`, `s43_living.png`, `s46_living2.png`, etc.).
5. **RAM evidence.** mGBA `.ss1` savestates are PNGs with a zlib `gbAs` chunk;
   `zlib.decompress` yields a 397,312-byte state. For this 8 MiB ROM the layout
   used here was: CPU/header `0x00000`, VRAM `0x01000–0x18FFF`,
   IWRAM `0x19000–0x20FFF`, EWRAM `0x21000–0x60FFF` (guide §16.13). Button-code
   tests loaded a baseline title-menu state, pressed a combination, saved slot 2
   and diffed IWRAM/EWRAM.
6. **Published-code verification.** `python3 verify_codes.py`,
   `code_brute.py`, `code_brute2.py`, `code_brute3.py`, `code_brute4.py`,
   `table_hunt.py` (all in the work dir) implement the encoding searches in §6b.

## 4. Address map

| Address (file / ROM) | Content | Evidence |
|---|---|---|
| `0x000000` / `0x08000000` | GBA header, title `MEGAMAN6_FXX`, code `BR6E` | Observed |
| `0x0000D0` / `0x080000D0` | ARM crt0 (entry target) | Derived |
| `0x762300` / `0x08762300` | Text bank: password-entry help string | Derived |
| `0x762350` / `0x08762350` | Encoded `PASSWORD` (`1a 0b 1d 1d 21 19 1c 0e`) | Derived |
| `0x762386–0x7623A6` | Encoded `UP`, `DOWN`, `LEFT`, `RIGHT` (entry controls) | Derived |
| `0x7623D0–0x7623E0` | Encoded `TRY AGAIN`, `COME`, `HERE` | Derived |
| `0x762440+` | 16-bit-offset table into the above text bank | Derived |
| `0x76A200–0x76A500` | Number Trader dialogue bank: `TRADER` (`0x76A283`), `NUMBER` (`0x76A370`), `CHIP` (`0x76A2CA`), `REQUEST`, `STYLE`, `CANNOT ACCEPT` | Derived |
| `0x788D2F` / `0x08788D2F` | Encoded `MEGAMAN` (charset cross-check) | Derived |
| `0x7BD4E0–0x7BD5C0` | Encoded test-completion dialogue: `FINISHED ALL TESTS`, `PASSED WITH FLYING COLORS`, `CONGRATULATION` | Derived |
| `0x44500–0x44700` | Pointer table pairing code pointers (`0x08044xxx`) with text-bank pointers (`0x0876xxxx`); no direct pointer to the `PASSWORD` string itself | Derived |
| `0x132FF8–0x133100` | Thumb routine building a digit table; uses BIOS `svc 6` (Divide) with divisor 10 (`mov r1,#10`) at `0x08132FE0` — decimal digit extraction, possibly related to numeric UI | Derived |
| Savestate offsets | IWRAM `0x19000`, EWRAM `0x21000` | Observed |

## 5. Algorithm

### 5.1 Text encoding (Derived, cross-checked on two independent strings)

The ROM's UI/dialogue text is **tile-indexed**, not ASCII. The mapping recovered
from `PASSWORD` at `0x762350` and `MEGAMAN` at `0x788D2F`:

```
byte 0x00            -> space
byte 0x0B + (c-'A')  -> uppercase A..Z   (A=0x0B, Z=0x24)
bytes 0x01..0x0A     -> probable digits/control (not fully resolved)
bytes 0xE8, 0xE9     -> case/display-mode control codes
bytes 0x88,0x90,0x9B,0xAC,0xAD,0xEB,0xFE -> line/paragraph control codes
```

Example: `PASSWORD` = `1a 0b 1d 1d 21 19 1c 0e`:
`P=0x1A, A=0x0B, S=0x1D, S=0x1D, W=0x21, O=0x19, R=0x1C, D=0x0E`.
`MEGAMAN` = `17 0f 11 0b 17 0b 18`. This is why the Phase-1 `strings` scan
returned no gameplay text: the visible UI never exists as ASCII in the image
(guide §11, "not all text is ASCII").

### 5.2 Password validation (unresolved)

The published codes are 8 decimal digits. Their storage/validation is **not**
plaintext under any of the encodings searched (§6b). Two live hypotheses
(**Inferred**): (a) the accepted-code table lives inside an LZ77-compressed
script block and is decompressed to RAM before use; (b) the game computes valid
numbers from reward IDs through a checksum/PRNG validator, hence no table.
No validator address can be given without exercising the gated screen.

## 6. Tables

### 6.1 Published MMBN6 Lotto Numbers (external documentation, not ROM-verified as literals)

Source: Mega Man Wiki, "Lotto Number", § *Mega Man Battle Network 6*
(`https://megaman.fandom.com/wiki/Lotto_Number`). 29 entries:

| Number | Reward | Number | Reward |
|---|---|---|---|
| 97049899 | BlzrdBal (H) | 69544569 | Lance (*) |
| 23722234 | TimeBom3 (M) | 75641392 | Recov300 (Y) |
| 44892547 | ColArmy (*) | 87989369 | ElemTrap (*) |
| 84387543 | EraseMan (*) | 10414878 | GroundMan (*) |
| 92070765 | ChargeMan (*) | 79814666 | DustMan (*) |
| 87341489 | FullEnrg | 79459146 | SneakRun |
| 74198795 | SneakRun | 37495453 | LocEnemy |
| 68008194 | LocEnemy | 82564319 | Unlocker |
| 04789479 | Unlocker | 59485971 | Untrap |
| 37889678 | HP+50 (pink) | 24823665 | HP+200 (white) |
| 15733751 | HP+300 (pink) | 08749780 | HP+400 (green) |
| 94305487 | ChargeMAX (blue) | 32132348 | Rush (yellow) |
| 70741543 | Beat (blue) | 69548756 | Tango (green) |
| 09256524 | SpinGrn | 77837421 | SpinRed |
| 41976910 | SpinYllw | | |

The wiki notes the machine is the **Number Trader inside Higsby's or AsterLand**;
the codes originate from the anime/Rockman EXE Battle Chip Stadium and in-game
Key Items (QuizData, ScrtMemo, SrialDat, PngnThnk, SciManul, SoulEmbl, etc.).
One wiki riddle ("Start with 10 for each digit and subtract 33273689 in each
place value") yields `77837421`, showing the codes are deliberately structured,
not random. No prompt-injection content was found in the fetched page; the TCRF
page fetched during reconnaissance contained only an unrelated joke footer,
which was treated as data and ignored (guide §16.8).

### 6.2 Title-button tests (Observed, savestate RAM diff)

| Combination | IWRAM diffs | EWRAM diffs | Interpretation |
|---|---|---|---|
| none (baseline) | 3402 | 71 | title-screen animation baseline |
| L+R | 3476 | 69 | indistinguishable from baseline |
| L+R+Select | 3528 | 62 | indistinguishable from baseline |
| L+R+Start | 5964 | 38266 | New Game started (not a flag) |
| L+R+A | 5691 | 35664 | New Game started (not a flag) |
| A+B+Start+Select | 6271 | 38670 | New Game started (not a flag) |

## 6b. Enumeration

**Space definition (Derived from external spec + ROM search).** The accepted
inputs are 8 decimal digits → `10^8 = 100,000,000` representable strings; the
published set has 29 known members. No alphabet wider than 0–9 was observed for
this system; the password-entry help text at `0x762300` names only D-pad
directions for editing.

**Published-vs-ROM verification (exhaustive encoding sweep, Derived).** For each
of the 29 codes the following byte patterns were searched over all 8,388,608
bytes: ASCII decimal; `u32` little- and big-endian; raw digit bytes `0x00–0x09`;
packed BCD and nibble-swapped BCD; `byte + k` for all `k=0..255`; `byte XOR k`
for all `k=0..255`; reversed digit order with the same additive sweep; two- and
four-byte-per-digit encodings; every 7-digit prefix and suffix; and all seven
digit rotations. **Result: 0 hits for every code and every transform.** A
follow-up search for a consecutive table of 32-bit values encrypted by a
constant XOR or additive key (using the first three published codes as the
oracle) also returned 0 candidates, as did the same test on 16-bit halfwords.

**Consequence.** The published list cannot be used as a ROM literal anchor, and
no unpublished code could be minted from a recovered validator in this
engagement. No novel code is claimed. This is a bounded *storage-form* negative,
not a claim that the system is absent — the system's existence is established by
the dialogue banks and by external documentation (guide §16.3: "gated feature",
not "no system").

**Bounds proven by rejection (Observed).** On the reachable surfaces:
- Title menu accepts exactly one selection; D-pad/B/L/R/Select produced no new
  entry and no RAM flag change beyond the animation baseline.
- PET `Comm` exposes only `LINK CBL` and `WRLS ADPT`; no password entry.
- PET `E-Mail` is empty ("You haven't gotten any mail yet, Lan.").
- The five button combinations in §6.2 were tested; the three that changed RAM
  did so by starting New Game, which is the documented menu action, not a cheat.

## 7. Validation evidence

- **Observed:** ROM hash/header (Phase 0); every screenshot named in §3; mGBA
  savestate RAM diffs for the five title combinations; dialog text rendered by
  the emulator matching the decoded tile-index strings (e.g. "That Sunday....",
  "You haven't gotten any mail yet, Lan.").
- **Derived:** the character encoding (two independent strings); the text-bank
  and pointer-table addresses; the absence of plaintext code literals; the
  single-header/no-trainer conclusion; Ghidra auto-analysis found 4,675
  procedures over the image (REA/Ghidra 12.1.4, raw ARM load) but no relevant
  validator was isolated.
- **Inferred:** that the accepted set is compressed or computed; that the
  `svc 6`/divisor-10 routine at `0x08132FE0` belongs to numeric UI.

## 8. Unknowns

1. The **Lotto Number validator / code table address** is not identified. The
   Number Trader screen is behind story progression and was not reached; the
   entry point is therefore gated, and no code was entered on the real screen.
2. The exact digit byte values (`0x01..0x0A` hypothesis) and the control-code
   semantics in the tile-index charset are only partially resolved; uppercase
   A–Z and space are proven.
3. Whether the `PASSWORD` string at `0x762350` is the Number Trader entry prompt
   or an unrelated story password is not proven — it is strongly associated
   with adjacent `UP/DOWN/LEFT/RIGHT` and `TRY AGAIN` strings.
4. The Japanese-only Beast Link Gate and e-Reader content reported by TCRF are
   absent/gated in this international build and were not reachable; no
   in-game-cheat claim is made for them.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for raw Thumb disassembly; Capstone
  5.0.7 for literal-load/BL scans.
- REA MCP + Ghidra 12.1.4: `open_binary` (raw-binary, arm, entry `0x08000000`),
  `binary_overview` (4,675 procedures), `xrefs`, `analyze_function`; session
  closed after analysis.
- Python scripts in `/tmp/opencode/mmbn6falzar/`: `phase0.py`, `ssdump.py`,
  `diff.py`, `decode_region.py`, `textdec.py`, `textdec2.py`, `kwsearch.py`,
  `verify_codes.py`, `code_brute.py` … `code_brute4.py`, `table_hunt.py`,
  `keyscan.py`, `numtable.py`, `xref.py`, `xref2.py`, `combo_diff.py`.
- mGBA 0.x under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`; `xdotool` XTEST input;
  `scrot` + ImageMagick for the 720×480 viewport crops.

**Legal note:** no ROM bytes or copyrighted assets are reproduced here; only
hashes, addresses, small encoding examples and findings are published.
