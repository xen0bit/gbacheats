# Pac-Man Collection (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Pac-Man Collection/Pac-Man Collection.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `PACMANCOLLE` |
| Game code / maker | `APCE` / `AF` |
| Version / fixed byte | `0x00` / `0x96` |
| Entry word | `0xEA00002E` → stock `0x080000C0` (no cracktro/trainer patch) |
| MD5 | `ed4304cc4f5bac34adfaa750316784a8` |
| SHA-1 | `aaaf5496411cdd9315debe866e69ca8665468f9b` |
| SHA-256 | `87eb602a50fc80f205cab2a22f1455b0d49c7cb777b568e15227aabc0a9b1d71` |

Phase 0 embedded-header scan: exactly **one** GBA header (the Nintendo logo appears only at file 0x4, header at 0x0). This is a single 4 MiB image, not a concatenated multiboot pack. No patch/trainer detected; the entry branch and first 4 KiB are stock crt0/IRQ code.

Component games (boot splash, Observed): **Pac-Man**, **Pac-Man Arrangement**, **Pac-Attack**, **Pac-Mania**. All cheats found belong to the Pac-Attack component (Puzzle Mode).

## 2. Executive summary

The only developer-intended code system is the **Pac-Attack Puzzle Mode password**: three letters drawn from a 21-consonant alphabet (`BCDFGHJKLMNPQRSTVWXYZ`, the on-screen keyboard). It is **not** algorithmic — a hard-coded **101-entry × 3-byte lookup table** lives at ROM `0x08099560`, is copied to EWRAM `0x020045D0` at boot, and is scanned by the validator at `0x08010650`. A match writes the table index to `0x0200FB68`; index 0–99 select Puzzle stages 1–100, index 100 (`FFF`) shows the ending.

The complete accepted space is **exactly 101 of 21³ = 9,261 possible strings (1.09%)** — proven exhaustively against the table and bounded by the validator's `cmp r5,#101` loop limit.

A second developer-intended unlock is **Appendix mode**: on the Pac-Attack mode menu, highlight Puzzle Mode, hold Right, press A (verified in emulator; it adds a fixed-cluster variant and exposes the Start / Password / Cancel submenu).

**Published-list error found:** every consulted published list (3rd party cheat index mirrors) gives level 68 = `PPS`. The ROM table entry 67 is **`PPY`** (`0D 0D 15`). `PPY` is accepted in the emulator and starts **STAGE 68**; `PPS` is rejected. `PPY` is therefore a code absent from every published list, minted from the ROM table and confirmed in-game — the §0.2 novel-code deliverable.

## 3. How to reproduce

Emulator: mGBA SDL under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `-3` scale. Keymap: A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.

Menu path to the password screen:
1. Title `PRESS START` → Start.
2. Game select: Press Left twice from the default (Arrangement) to **PAC-ATTACK** → A.
3. Mode menu (`Normal Mode` / `Puzzle Mode`): highlight **Puzzle Mode**, hold **Right** and press **A** → `APPENDIX` banner + submenu `START / PASSWORD / CANCEL`.
4. Cursor to **PASSWORD** → A → `Enter Password` keyboard (`A-Enter`, `B-Memu`), three slots, grid 7×3 of the 21 consonants.
5. Move the D-pad cursor to each letter and press A. After the third letter the validator runs; a valid code starts the stage immediately, an invalid code leaves you on the entry screen with the letters still shown.

Codes tested in emulator (Observed):

| Code | Result |
|---|---|
| `STR` | STAGE 1; screen echoes `PASSWORD S T R` |
| `HNM` | STAGE 2 |
| `QYZ` | STAGE 92 |
| `LST` | STAGE 100 |
| `PPY` | STAGE 68 (ROM-only code; published lists say `PPS`) |
| `FFF` | "Congratulations! YOU DID IT! YOU SMASHED THROUGH ALL 100 LEVELS" ending |
| `PPS` | **Rejected** — stays on `Enter Password` with `P P S` displayed |
| `BBB`, `XYZ` | Rejected — stay on entry screen |

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| ROM password table (101×3 bytes) | file `0x99560` → ROM `0x08099560` | Derived: bytes identical to RAM copy; `grep`-style search of RAM dump |
| EWRAM table copy | `0x020045D0` (303 bytes) | Derived: validator literal at `0x80106C0`; RAM dump decoded |
| Validator loop / compare | `0x08010650`–`0x080106A0` (loop bound `cmp r5,#101` at `0x801067A`) | Derived: Thumb disassembly |
| Match handler (store index) | `0x80106A2`–`0x80106B4` (`str r5,[0x0200FB68]`) | Derived |
| Entered-letter buffer (3× u32) | `0x0200FB58`, `0x0200FB5C`, `0x0200FB60` | Derived + Observed (savestate diff; debugger read) |
| Stage/ending index word | `0x0200FB68` | Derived + Observed: `QYZ` → `0x5B` (91) |
| Password default-loader (copies entry 0 = STR into slots) | `0x080D130` | Derived |
| BOLT key poll (KEYINPUT `0x04000130`) | `0x08041C34`; held `0x0200FFD0`, pressed `0x0200FFD2` | Derived |
| Per-key state array / index table | `0x0200EA10` (12-byte stride) / `0x0200EA30` | Derived |
| Input dispatcher (caller) | `0x08009BE0`–`0x08009CC0` | Derived + Observed (LR of key-poll breakpoint) |
| Slot display reader (per-frame) | `0x0800B0A0` / `0x0800B0DC` | Observed (read watchpoint) |
| "CHARACTER / NICKNAME" initials bank | ROM `0x04BFA8`; char sets `13579ACE` / `02468BDF` at `0x04BDC4`/`0x04BDD0` | Derived (strings + context) |
| Arcade ADS service-menu strings (`A.D.S. TABLE MENU` etc.) | ROM `0x0A8958`–`0x0A8B70` | Derived; no pointer xrefs from the GBA UI (see Unknowns) |

File offset ↔ ROM address: `0x08000000 + file_offset` (single image, verified).

## 5. Algorithm

Validator (`0x08010650`), reimplemented precisely:

```python
# entered[i] are u32 values = (consonant_index + 2), i.e. font tile indices:
# B=2, C=3, D=4, F=5, ... Z=22
table = rom[0x99560:0x99560 + 303]          # copied to 0x020045D0 at boot
match = 0
for i in range(0, 101):                      # cmp r5,#101 ; bgt -> reject
    if (table[3*i+0] == entered[0] and
        table[3*i+1] == entered[1] and
        table[3*i+2] == entered[2]):
        match = 1
        break
if match:
    stage_index = i                          # str r5,[0x0200FB68]
    # i in 0..99 -> Puzzle stage i+1; i == 100 -> ending (FFF)
else:
    # invalid: fail sound, no state write, stay on entry screen
```

Notes:
- Comparison is `ldrb` (table, byte) against `ldr` (slot, u32); table bytes are 2..22 so the comparison is exact.
- There is **no checksum, hash, PRNG or encoder** — the whole system is this table. The `+2` in the slot values is the font/tile-index bias (letter index 0 = `B` → tile 2).
- The second half of the function (`0x080D130`) copies `table[0]` (`STR`) into the three slots, i.e. the default displayed password is stage 1.

## 6. Tables

Alphabet (on-screen keyboard, 7×3): `B C D F G H J / K L M N P Q R / S T V W X Y Z` — 21 symbols, no vowels. Slot value = index+2.

ROM table `0x08099560`, decoded (index → stage = index+1, except index 100 = ending):

| idx | code | idx | code | idx | code | idx | code | idx | code |
|---:|:---:|---:|:---:|---:|:---:|---:|:---:|---:|:---:|
| 0 | STR | 20 | KTY | 40 | CNK | 60 | MNS | 80 | JWK |
| 1 | HNM | 21 | TYK | 41 | FRB | 61 | SWD | 81 | GSN |
| 2 | KST | 22 | SMM | 42 | MLR | 62 | LDM | 82 | MMT |
| 3 | TRT | 23 | NFL | 43 | FRP | 63 | YST | 83 | DNK |
| 4 | MYX | 24 | SRT | 44 | SDB | 64 | QTM | 84 | HPN |
| 5 | KHL | 25 | KKT | 45 | BQJ | 65 | BRP | 85 | DCR |
| 6 | RTS | 26 | MDD | 46 | VSM | 66 | MRS | 86 | BNS |
| 7 | SKB | 27 | CWD | 47 | RDY | 67 | **PPY** | 87 | SDC |
| 8 | HNT | 28 | DRC | 48 | XPL | 68 | SWT | 88 | MRH |
| 9 | SRY | 29 | WHT | 49 | WLC | 69 | WTM | 89 | BTF |
| 10 | YSK | 30 | FLT | 50 | TMF | 70 | FST | 90 | NSM |
| 11 | RCF | 31 | SKM | 51 | QNS | 71 | SLW | 91 | QYZ |
| 12 | HSM | 32 | QTN | 52 | GWR | 72 | XWF | 92 | KTT |
| 13 | PWW | 33 | SMN | 53 | PLT | 73 | RGJ | 93 | FGS |
| 14 | MTN | 34 | TGR | 54 | KRW | 74 | SNC | 94 | RRC |
| 15 | TKY | 35 | WKR | 55 | HRC | 75 | BKP | 95 | YLW |
| 16 | RGH | 36 | YYP | 56 | RPN | 76 | CRN | 96 | PNN |
| 17 | TNS | 37 | SLS | 57 | CNT | 77 | XNT | 97 | SPR |
| 18 | YKM | 38 | THD | 58 | BTT | 78 | RNT | 98 | CHB |
| 19 | MWS | 39 | RMN | 59 | TMP | 79 | BSK | 99 | LST |
| — | — | — | — | — | — | 100 | **FFF** (ending) | — | — |

(The ROM table was dumped byte-for-byte and is authoritative for all 101 entries.)

Published-list verification: 100/100 stage codes plus `FFF` were checked literally against the decoded ROM table; **one** discrepancy — level 68: ROM `PPY`, all published lists `PPS`.

Other in-game options/UI (not codes): Pac-Attack mode menu and Appendix mode; shell pause menus (`CONTINUE / SETTINGS / TIPS / MAIN MENU` in the wrapper, `CONTINUE / QUIT GAME / MAIN MENU` inside Pac-Attack); per-game SETTINGS (e.g. Pac-Man `LIVES` 3→2, `BONUS` 10K); TIPS pages (gameplay hints decoded from the ASCII bank at `0x04A0F0`–`0x04B030`); high-score name entry ("CHARACTER / NICKNAME" with default ghost names URCHIN/ROMP/STYLIST/CRYBABY/KINKY — observed in Arrangement).

## 6b. Enumeration

- **Space definition:** 3 symbols × 21 consonants = **9,261** possible strings. No field/checksum structure — the validator is a pure 101-record lookup. Reserved: none in the input; the stored character values are biased by +2 (tile indices 2..22).
- **Validator model:** reproduced in §5; agrees with the ROM on accepted (`STR`, `PPY`, `QYZ`, `LST`, `FFF`) and rejected (`PPS`, `BBB`, `XYZ`) inputs.
- **Exhaustive check:** iterating all 21³ combinations against the decoded table yields **exactly 101 accepted codes** (0–99 stages 1–100, 100 = `FFF`). The ROM validator's own bound (`cmp r5,#101`, `bgt`) proves the same 101-record limit independently of the offline model.
- **Novel code absent from every published list:** **`PPY`** (table index 67). Generated from the ROM table, entered on the real password screen, accepted, and verified in two ways: visually (`STAGE 68`, `PASSWORD P P Y`) and by RAM read (`0x0200FB68 = 0x43` = 67, i.e. stage 68; the `QYZ` probe read `0x5B` = 91, i.e. stage 92). Published lists unanimously print `PPS` for level 68.
- **Bounds proven by rejection:** `PPS` (the published typo) is rejected and the game stays on the entry screen. `BBB` and `XYZ` are likewise rejected. No code outside the 101-entry table is accepted; no algorithm exists that could mint additional values.
- **Negative-result boundary:** text search covered ASCII, `+0x20`/`-k`/XOR-translated ASCII, consonant-index tables, 5-bit packed 15/24-bit encodings, and sliding-window table scans; literal password strings appear nowhere in ROM except coincidental substrings. The text bank is tile-indexed; the relevant bank was decoded via the font bias (`index+2`) and yielded the complete table at `0x99560`.

## 7. Validation evidence

- **Observed** (emulator/screenshots/RAM): boot splash and four game logos; title; 4-entry game select; Pac-Attack mode menu; Appendix banner and Start/Password/Cancel submenu; password keyboard alphabet; `STR`→1, `HNM`→2, `QYZ`→92, `LST`→100, `PPY`→68, `FFF`→ending; `PPS`/`BBB`/`XYZ` rejected; shell and in-game pause menus; SETTINGS and TIPS pages; Arrangement's nickname entry; RAM values at `0x0200FB58/5C/60` and `0x0200FB68`; table bytes at `0x020045D0`.
- **Derived** (disassembly/dump): table address and decode; validator loop and bound; slot-buffer bias +2; input-poll and dispatcher addresses; ROM/RAM table identity.
- **Inferred:** the arcade-era ADS service menu strings (`A.D.S. TABLE MENU`, `SOUND TEST`, `3D TEST`, etc. at `0x0A8958`+) belong to the Pac-Mania arcade code but have no pointer xrefs from any reachable GBA screen; treated as dead/embedded content, not a reachable debug menu. The published "different menu music" idle trick was not audio-verified (`SDL_AUDIODRIVER=dummy`).

## 8. Unknowns

- Whether the Pac-Mania ADS service menu can be reached by an undiscovered button combination: GBA UI enumeration found only PLAY on its game-select tile, and its strings have no code xrefs; not proven unreachable by exhaustive input fuzzing.
- High-score initials entry was walked for Pac-Man Arrangement (nicknames) and located as string banks for the other games (`0x04BDC4`/`0x04BDD0` character sets), but a full three-letter initials entry for Pac-Man and Pac-Mania was not triggered (requires reaching a high score); no code surface was found in those banks.
- The published idle "different menu music" trick (wait on the Normal/Puzzle menu) was not verified because audio output was disabled.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for validator/input disassembly; Capstone 5.0.7 scanners (`scan_thumb.py`, `scan_funcs.py`, `scan21.py`, `find_code.py`).
- mGBA command-line debugger (`mgba -d`) driven over a pty (`pty_dbg.py`, `send.py`), with SIGINT to break in; `r/4`, `watch/r`, `watch/w`, breakpoints.
- mGBA `.ss1` savestates decompressed with `ssdump.py` (zlib `gbAs` chunk) and diffed for RAM discovery; 8 slots used.
- Python analysis: `analyze_pw.py`, `fit_formula.py`, `gf2_fit.py`, `lcg_fit.py`, `find_table.py`, `find_packed.py`, `find_table2.py`, `enumerate.py`, `enter_code.py`.
- Web: 3rd party cheat indexes; fetched pages treated as data (no injected instructions acted upon; one mirror carried unrelated VMProtect/antivirus boilerplate which was ignored).

No ROM image or copyrighted assets are redistributed here; only addresses, hashes, algorithms and tools are published.
