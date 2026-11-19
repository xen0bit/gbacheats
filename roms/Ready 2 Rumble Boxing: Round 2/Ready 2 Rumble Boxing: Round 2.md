# Ready 2 Rumble Boxing: Round 2 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Ready 2 Rumble Boxing: Round 2.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `R2RBOXING R2` |
| Game code / maker | `AR2E` / `5D` |
| Version | `0x00` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| MD5 | `ba428f9d19ecad3a4297b8e23481e6b0` |
| SHA-1 | `d6114cd4bb6b580437c5c2d6e4c3a51eaa0de76e` |
| SHA-256 | `b7da39f5be38c62c10740eb3721cd738404b8f62217b15eb7e49d2ea2b801dc5` |

**Phase 0 / patch scan (Observed).** Full 156-byte Nintendo logo occurs exactly once, at file offset `0x0` → single game image, no multiboot/trainer half, no appended data (size is an exact power of two). Entry word is stock. Header checksum is `0x0000` and the complement byte is `0x8D` (expected `0xA6`), which is the usual rebuilt-header artifact (§16.1) rather than a cracktro; no scene cracktro code was found. Header scan and hashes above are for this exact revision only.

## 2. Executive summary

The game has a **developer-intended 13-symbol password system** for Championship Mode progress (manual: *"If you've saved a password from a previous progression through Championship Mode, you can enter it to continue where you left off"*). It is real, reachable, and fully reversible:

* Natural UI path: **Main Menu → Championship → character select → highlight one of the three blank boxer slots → A** opens the password keypad. (The bottom-of-screen `ENTER PASSWORD` label is the hint for that cell.) START confirms; B exits.
* Alphabet: `BCDFGHJKLMNPQRSTVWXYZ0123456789$` (32 symbols, 5 bits each) at `0x0816477A`.
* One XOR check character, **one ignored "check" character**, and 11 payload characters. Validator at `0x080130E8`; generator at `0x08012F98`.
* All ten GameFAQs/GBA passwords that satisfy the algorithm round-trip bit-for-bit through the reimplemented encoder. The published **Afro Thunder** password is a typo (`$KBBNGGG$C37G`); the correct one is **`$KBBNGGG$C3VG`**, confirmed in-game (A. Thunder, 100/100/100). A separate site's `$8DDNGGG$C7JB` for Angel Rivera is also wrong (canonical `$8DNNGGG$C7JB`).
* A **novel, unpublished code `$WF7P2JN4B7G5`** was generated, typed on the real keypad, accepted, and RAM-verified to produce STR 55 / STM 42 / SPD 70 (all published codes use 100/100/100).
* Bounds proven live: a broken XOR check is rejected, an out-of-range stat (101) with valid checks is rejected, and changing the ignored 13th symbol is *accepted* while the game regenerates the canonical value — proving an alias class.
* A GBA button-code table at `0x083F4104` holds three sequences. Two match published unlock codes; the third appears unpublished. The table and its validator/flags were located statically; one live acceptance was observed but the input harness was timing-sensitive (see §8).

No GameShark/CodeBreaker/memory-edit codes are reported.

## 3. How to reproduce

**Emulator:** mGBA (SDL build) under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, `-3` scaling, GDB stub not required. Keymap used: `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`, D-pad = arrow keys.

**Reach the keypad (Observed):**
1. Boot; skip/press through the legal scroll to the title; START → Main Menu.
2. Down once to `CHAMPIONSHIP`, A → `CHOOSE YOUR BOXER` (`0x083F39CC`).
3. Move to any of the three **blank** cells in the lower row (e.g. Right, Right, Down), press A → password keypad (`0x08012E34`). On-screen legend: `A SELECT / B EXIT / L,R MOVE CURSOR / START CONFIRM PASSWORD`.
4. The keypad is an 8×4 grid of the alphabet; Right/Left wrap within a row, Up/Down wrap within a column. A writes the selected 5-bit value into slot `n` and auto-advances. START calls `0x080130E8`.

**Codes to type (13 symbols each):**
* published, verified: `$WF7PGGG$C779` (Jet Chin), `$8DNNGGG$C7JB` (Rivera), `$2KPWGGG$C7YZ` (Joey T), `$KHJPGGG$C3XX` (Blood), `$WWNVGGG$C3KJ` (Lulu), `$8GZTGGG$C76J` (Mama Tua), `$MNXVGGG$C37Z` (MJ), `$4JPWGGG$C779` (Robox), `$6LNZGGG$W7G7` (Rumble Man), `$HMBNGGG$C361` (Shaq).
* correction: `$KBBNGGG$C3VG` (Afro Thunder).
* **novel:** `$WF7P2JN4B7G5`.
* rejected: `BWF7P2JN4B7G5` (XOR), `$WF7PHJN6B7Z5` (stat 101), `$WF7P2JN4B7GB` (accepted alias).

After acceptance, the game lands in the `WORLD CHAMPIONSHIP` menu; choose `PASSWORD` to see `YOUR CURRENT PASSWORD IS:` and the regenerated code (`0x08012F20`).

**Button codes:** at the main menu with `SURVIVAL` highlighted, published `L L L L R R L L R L+R` (Shaq) and `L L R R L R L+R` (MJ) were attempted; ROM literals are exact. See §8 for the reliability caveat.

## 4. Address map

File offset `F` ↔ ROM address `0x08000000 + F`.

| Address (ROM) | File | Meaning |
|---|---|---|
| `0x08164760` | `0x164760` | `YOUR CURRENT PASSWORD IS:` |
| `0x0816476D` | `0x16476D` | `PASSWORD IS:` |
| `0x0816477A` | `0x16477A` | 32-symbol alphabet, NUL-terminated |
| `0x083F39CC` | `0x3F39CC` | `CHOOSE YOUR BOXER` + 13 boxer-name strings |
| `0x083F3AC4` | `0x3F3AC4` | boxer-name pointer table (13 entries; index 12 = `ENTER PASSWORD`) |
| `0x08012D40` | `0x12D40` | password keypad input handler (A/B/L/R/Start) |
| `0x08012E34` | `0x12E34` | password screen init: fills 16 bytes at `0x0203DF30` with `0x20` |
| `0x08012F20` | `0x12F20` | `YOUR CURRENT PASSWORD IS:` display screen |
| `0x08012F98` | `0x12F98` | generator: packs decoded state into 13 5-bit symbols |
| `0x080130E8` | `0x130E8` | **password validator** (XOR, range checks, state writes) |
| `0x081F140/144` | `0x1F140/144` | screen-handler pointer table entries for entry/display |
| `0x083F4104` | `0x3F4104` | button-code pointer table (3 sequences) |
| `0x083F40C4/EC/D4` | `0x3F40C4/EC/D4` | button-code mask arrays (u16, active-high, `0x0000` terminator) |
| `0x0800E20C` | `0xE20C` | button-code validator (called from `0x0800E32E`) |

| RAM address | Meaning |
|---|---|
| `0x0203DF30` | 13-byte password buffer, values 0..31 (`0x20` = blank) |
| `0x0203DF10` | validator's working copy |
| `0x02009040` | STR (displayed first) |
| `0x0200902C` | STM (displayed second) |
| `0x02009004` | SPD (displayed third) |
| `0x02009048` | money/100 |
| `0x02008FE4` | boxer identity low 6 bits |
| `0x02009008` | records |
| `0x0200B07C` | progress low nibble (must be ≤10) |
| `0x0203DF40` | screen state (`0x0B` = championship menu) |
| `0x0200D654 / D650 / D6B0` | button-code unlock flags (indices 0 / 1 / 2) |

## 5. Algorithm

`A = "BCDFGHJKLMNPQRSTVWXYZ0123456789$"`; `v[i] = A.index(s[i])`, `i=0..12`.

**Validator `0x080130E8`** (Derived from disassembly, confirmed live):
1. Copy 16 bytes from `0x0203DF30` into `0x0203DF10`; reject if any byte is `0x20` (blank slot).
2. Reject unless `v[0] == XOR(v[1]..v[11])`. (`0x8013128..0x8013142`.) **There is no read of `v[12]`** — the 13th symbol is never validated.
3. Decode fields (see §6) and write them to EWRAM.
4. Reject if any of the three 7-bit stat fields > 100, or if `v[2] & 15 > 10`.
5. Return 1 on success, 0 on rejection (caller `0x08012DAA`).

**Generator `0x08012F98`** (Derived): reads the same EWRAM fields, packs them into `v[0..10]`, sets
```
v[11] = XOR(v[0]..v[10])
v[12] = (sum(v[0]..v[11])) & 31
```
then the display routine maps each value through `A`. Hence `v[12]` is a *display check digit*, not a security check. `pw.py` implements both directions and round-trips all ten valid published codes exactly.

**Button-code validator `0x0800E20C`** (Derived): three arrays of active-high u16 key masks (`0x10=Right, 0x20=Left, 0x40=Up, 0x80=Down, 0x100=R, 0x200=L, 0x300=L+R`), terminated by `0x0000`; a per-code history index advances on exact match and resets on mismatch; success writes a word `1` to one of three flags and plays sound `4`.

## 6. Tables

Published passwords (GameFAQs GBA page, archived 2025-11-14; also cheatcc / projectcheatcodes):

| Boxer | Published | Status |
|---|---|---|
| Afro Thunder | `$KBBNGGG$C37G` | **invalid** — corrected `$KBBNGGG$C3VG`, accepted in-game |
| Angel "Raging" Rivera | `$8DNNGGG$C7JB` | verified; cheatingdome's `$8DDNGGG$C7JB` is invalid |
| Jet "Iron" Chin | `$WF7PGGG$C779` | verified in-game |
| Joey T. | `$2KPWGGG$C7YZ` | verified by algorithm |
| Johnny "Bad" Blood | `$KHJPGGG$C3XX` | verified by algorithm |
| Lulu Valentine | `$WWNVGGG$C3KJ` | verified by algorithm |
| Mama Tua | `$8GZTGGG$C76J` | verified by algorithm |
| Michael Jackson | `$MNXVGGG$C37Z` | verified by algorithm |
| Robox Rese 4 | `$4JPWGGG$C779` | verified by algorithm |
| Rumble Man | `$6LNZGGG$W7G7` | verified by algorithm |
| Shaq | `$HMBNGGG$C361` | verified by algorithm |

Field layout (`v` = 5-bit symbols):

| Field | Bits | Range |
|---|---|---|
| boxer identity | `v[0]` + `v[1]&1` << 5 | 6 bits (published codes all 63) |
| records | `(v[1]>>1)&15` | 4 bits |
| progress low | `v[2]&15` | must ≤10 |
| money/100 | `(v[4]<<6)|(v[3]<<1)|(v[2]>>4)&1` | 7 bits |
| STR | `((v[8]&3)<<5)|v[5]` | ≤100 |
| SPD | `(((v[8]>>2)&3)<<5)|v[6]` | ≤100 |
| STM | `((v[9]&1)<<6)|(((v[8]>>4)&1)<<5)|v[7]` | ≤100 |
| five small fields | `v[10]&1`, `(v[10]>>1)&3`, `(v[10]>>3)&3`, `(v[9]>>1)&3`, `(v[9]>>3)&3` | 1,2,2,2,2 bits |
| XOR check | `v[0]` vs `XOR(v[1..11])` | enforced |
| display digit | `v[12] = sum(v[0..11]) & 31` | **not enforced** |

Button-code table (`0x083F4104`, active-high masks):

| Index | Sequence | Flag ROM literal | Published? |
|---|---|---|---|
| 0 | L L R R L R L+R | `0x0200D654` | yes (Michael Jackson) |
| 1 | L L R L R R L R L L+R | `0x0200D650` | **not found in any published list** |
| 2 | L L L L R R L L R L+R | `0x0200D6B0` | yes (Shaquille O'Neal) |

## 6b. Enumeration

**Space definition.** 13 symbols × 32 values = `32^13 = 3.6e19` raw strings. `v[0]` is fully determined by `v[1..11]` (XOR check), so the payload is `32^11 = 36,028,797,018,963,968`. Range gates keep `22/32` of `v[2]` and `(101/128)^3` of the three stat fields:

```
accepted v[1..11] = 32^11 × (22/32) × (101/128)^3 = 12,169,050,025,099,264
accepted 13-symbol strings = ×32 (ignored v[12]) = 389,409,600,803,176,448 ≈ 3.89e17
distinct decoded game states (identity64 × records16 × progress11 × money128 × 101^3 × 512 small bits)
                           = 760,565,626,568,704 ≈ 7.61e14
```

**Validator model.** `pw.py` reimplements both directions; it accepts all 10 algorithm-valid published codes, reproduces them byte-for-byte from fields, and rejects the typo'd Afro Thunder / cheatingdome codes.

**Novel code (not on GameFAQs, cheatcc, TCRF, VGChartz or any other list that was checked):**

```
$WF7P2JN4B7G5   →  v = [31,17,3,28,11,23,6,10,25,0,28,4,26]
                    XOR OK, display digit OK
                    typed on the real keypad; accepted
                    RAM: 0x02009040=55, 0x0200902C=42, 0x02009004=70,
                         0x02009048=760 ($76,000)
```

Every published code encodes stats 100/100/100, so the 55/42/70 combination is provably outside the published set. The in-game `WORLD CHAMPIONSHIP` screen displayed `STR 55.0% / STM 42.0% / SPD 70.0%` (screenshot `novel_accepted.png`). A second novel-class code, the corrected `$KBBNGGG$C3VG`, was also accepted and displayed A. Thunder.

**Bounds proven by rejection (all on the real keypad):**

| Input | Defect | Result (Observed) |
|---|---|---|
| `BWF7P2JN4B7G5` | `v[0]` changed → XOR check fails | stayed on keypad; no state transition |
| `$WF7PHJN6B7Z5` | checksums valid, STR=101 | stayed on keypad; field written then range gate rejected |
| `$KBBNGGG$C37G` | published typo, two checks broken | stayed on keypad (rejected) |

**Alias class proven (Observed):** `$WF7P2JN4B7GB` (last symbol `B` instead of `5`) was **accepted** and produced the same 55/42/70 state; the in-game `PASSWORD` display then regenerated the canonical `$WF7P2JN4B7G5`. Therefore 32 spellings per state exist (one per possible 13th symbol), and `v[12]` is not a checksum in the security sense.

**Button-code set:** the ROM contains exactly three code arrays (pointer table has three entries); their masks and target flags are enumerated above. The third sequence is an unpublished combination. Live execution was timing-sensitive (§8), so its effect is Inferred from the validator's flag write, not Observed.

## 7. Validation evidence

* **Observed** (emulator screenshot + savestate RAM, labels as described in §4):
  * Character select `ENTER PASSWORD` blank-cell entry; password keypad and 13-slot display.
  * Typed buffer `pwdbuf = [31,17,3,28,11,4,4,4,31,1,28,28,30]` for `$WF7PGGG$C779`; `[31,17,3,28,11,23,6,10,25,0,28,4,26]` for the novel code.
  * After START: championship menu with Jet Chin 100/100/100 and money `$76,000`; novel code 55/42/70 and money `$76,000`; corrected Afro Thunder code → A. Thunder 100/100/100.
  * Rejections stay on the keypad; alias code accepted and canonical string regenerated.
  * Menu walk: title, Main Menu (Arcade/Championship/Survival/Options), Options (Knockdowns, Round Time, Rounds only — the `MORE` chevron does not scroll), character select, VS screen, in-ring match, Championship menu, password display.
* **Derived** (disassembly): generator/validator field packing, XOR check, range gates, ignored `v[12]`, button-code tables/validator/flags, screen-handler pointers.
* **Inferred**: which *unlock* the undocumented button-code index 1 grants (the validator writes `0x0200D650`, but the flag's consumer was not proven live); the `MUSIC VOLUME`/`SFX VOLUME`/`DIFFICULTY` strings at `0x08133620` appear unused in this GBA build — no such menu rows were reachable.
* All relevant UI text is plain NUL-terminated ASCII in the ROM (strings at `0x164760`, `0x3F39CC`, `0x3F3AB1`); no font/tile-indexed text bank had to be decoded to reach a negative conclusion. Fetched web pages and ROM strings were treated strictly as data.

## 8. Unknowns

* The natural-button-code input window is timing-sensitive under XTEST. One run of the Shaq sequence set flag `0x0200D6B0=1`; three later attempts with different hold/gap values did not. The table itself is ROM-verified; the MJ and undocumented sequences were not reliably triggered live, so their in-game effects remain unconfirmed (this is a harness limitation, not evidence that the codes are dead — they have a live validator and flag writers).
* The consumer of `0x0200D650` (undocumented code flag) was not traced to a specific unlockable.
* `v[8]/v[9]/v[10]` small fields' gameplay meanings are named only by their RAM destinations; they were not each exercised with a distinct value.
* The game's `PASSWORD` display regenerates `v[12]` but it was not proven whether it also regenerates the whole string from fields versus echoing stored text (the field round-trip of all 10 published codes strongly implies generation).

## 9. Tooling

* `strings -t x`, `xxd`, `grep -abo`; `arm-none-eabi-objdump -M force-thumb`; Capstone 5.0.7 + Keystone for BL/literal scans.
* `pw.py` — decoder/encoder and published-code comparison (reproducible offline oracle).
* `state.py` — parses mGBA `.ss1` PNG `gbAs` zlib chunk; EWRAM at raw `0x21000 + (addr-0x02000000)`, IWRAM at `0x19000 + (addr-0x03000000)`.
* `ui.py` / `enter.py` — XTEST input and automated 13-symbol password entry.
* `patchstate.py` — savestate register patcher (used only as a navigation aid while locating the natural path; all final proofs used the natural UI path).
* `pdftotext`/`tesseract` on the retail manual PDF (fetched as data) for the Championship/password navigation hint.
* Work directory `/tmp/opencode/ready2rumble`; screenshots kept there (not attached). No ROM or copyrighted assets are redistributed in this report.
