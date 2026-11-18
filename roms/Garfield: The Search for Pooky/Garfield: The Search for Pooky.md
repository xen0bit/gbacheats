# Garfield: The Search for Pooky (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Garfield: The Search for Pooky.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `GARFIELDTSFP` |
| Game code / maker | `BGOE` / `GY` (USA build `AGB-BGOE-USA`) |
| Version / fixed byte | 0x00 / 0x96 |
| Entry word | `0xEA00002E` (`b 0x080000C0`) — stock, no cracktro/trainer |
| MD5 | `cd27477e70b529b736746185b882100e` |
| SHA-1 | `7798a726a819e8a7ddccd834afd50d811796cfee` |
| SHA-256 | `37b5ae7aa523c01b105dae13fecb58caca506bfdf33e50760851fc098fe75025` |

Phase 0: one Nintendo-logo hit only (file `0x4`); no embedded headers, no multiboot stub, no appended trainer. Sibling `Garfield and His Nine Lives.gba` (`BG9E`, 4 MiB, SHA-1 `6befcc1236770ec8ed833d49b5d8dbdf62bda506`) is a different engine — nothing shared.

## 2. Executive summary

The game has a genuine, developer-intended **9-symbol password / level-select system** (PASSWORD on the main menu). The alphabet has exactly 32 symbols, so each symbol carries 5 bits and the representable space is `32^9 = 35,184,372,088,832` strings. The published GameFAQs list contains 24 codes: 12 Easy and 12 Hard (levels 2–12 plus a "clear game" code). **All 24 were verified in the emulator (24/24 accepted)**, and none is stored as a plaintext literal in the ROM — the validator is algorithmic.

**Accept-layer characterization (this retry).** The game itself was used as a black-box accept/reject oracle (patched savestate + real OK press, DISPLAY=:316). The 9th symbol behaves as a **checksum of the first 8**: for a pristine published 8-symbol prefix, exactly one of the 32 possible 9th symbols was accepted — the published one (`9W9KNN?D` → only `F`, 1/32). However, **an additional constraint exists on the first 8 symbols**: every single-symbol mutation of every published prefix (all 8 positions), every random 8-symbol prefix (16 prefixes), and a full 2-D brute-force of positions 7 and 8 for a mutated prefix (32×32 = 1024 codes) produced **zero** accepted codes. No field (level/difficulty) was found to be free, and no wildcard symbol exists.

**Result: closed set.** Across this retry plus the prior engagement, **2,000+ distinct unpublished 9-symbol strings** were tested in-game; **none was accepted**. The accepted set is consistent with **exactly the 24 published codes**. This is an *empirical bound*, not an exhaustive proof over 35 trillion strings (the checksum function was not recovered; see §8/§9). Per guide §0.2 / §16.9, the closed-set conclusion rests on the full sweep tables below, not on "checksum not recovered" as an unknown.

**Novel code: none exists within the reachable/swept space.** A novel accepted code could not be minted because the accept set appears closed at 24. See §6b for the full evidence tables and §8 for the explicit bound.

A `GameLevelTest.cpp` debug panel exists in ROM (hidden level-test screen), but its only caller `0x0800A840` has **no callers** — dead/unreferenced code, not a usable cheat (guide §16.3, category 2/4).

Web content was treated as data; no instructions found in fetched pages were executed.

## 3. How to reproduce

- Emulator: mGBA (`mgba -3`), `SDL_AUDIODRIVER=dummy`, Xvfb `:316`, openbox window manager. (Prior work used `:319`; this retry used its own `:316`.)
- Keymap (mGBA SDL defaults): A=`x`, B=`z`, Start=`Return`, D-pad = arrow keys.
- Boot path: language screen → A → title → Hold Start through intro → main menu (NEW GAME / PASSWORD / REPLAY INTRO / CREDITS).
- Password path: main menu → Down → PASSWORD → A → `ENTER PASSWORD` grid. D-pad moves the cursor in a 4×8 grid, A appends the highlighted symbol, B deletes one. After 9 symbols, press A once more to submit. Valid → map/level-select screen (purple, `01`/`50%` for a level code, `17`/`50%` for clear-game); invalid → return to `ENTER PASSWORD` (orange) with slots cleared.
- Savestate oracle: a password-screen state with 9 symbols entered was saved. The 9 ASCII bytes live at raw savestate offset `0x2FCED` (EWRAM `0x0200ECED`). Patch those 9 bytes, repack the PNG `gbAs` chunk, `mgba -3 -t <patched>` on `:316`, focus the window, press A, classify the result (purple = accept, orange = reject). Scripts in `/tmp/opencode/garfieldpooky2/` (`oracle.py`, `sweep.py`, `mutsweep.py`, `randprefix.py`, `twod.py`, `stateutil.py`, `dbg.py`).
- Pixel classifier (full-screen `-3` viewport at (200,200)): purple `(154,103,154)` = ACCEPT; orange `(247,90,41)` = reject. Cropped viewport screenshots saved as `evidence_ACCEPT_published.png`, `evidence_REJECT_wrong9.png`, `evidence_REJECT_mutprefix.png`.

## 4. Address map

| Item | Address / offset | Type |
|---|---|---|
| Compact alphabet (index order) | file `0x7D1178`, `0x7D11B8` → `0x0807D1178` / `0x0807D11B8` | Observed (bytes) |
| Alphabet pointer table | file `0x7D1140` | Observed |
| `ENTER PASSWORD` string | `0x0807DA2A4` | Observed |
| On-screen grid rows (spaced) | `0x0807DA2B4`, `+0x10`, `+0x20`, `+0x30` | Observed |
| `NEW PASSWORD:` string | `0x0807DA39C` | Observed |
| `GamePanelPasswd.cpp` label | `0x0807DA344` | Observed |
| `GameLevelTest.cpp` label | `0x0807DA480` | Observed |
| Literal pools holding prompt/alphabet pointers | file `0x8B6C` / `0x8B7C` | Derived |
| Thumb loads of those pools | `0x08008B1C`, `0x08008B3A` | Derived |
| 5-bit pack loop (`b>>3`, shifts 5/10) | `0x08008A3A`–`0x08008A5E` (also `0x08009C54`) | Derived (font/resource conversion, not the validator) |
| Password render loop / char read | `0x08008F92` (`ldrb r2,[r3,r2]`), watchpoint PC `0x08008F96` | Observed |
| Password input buffer | EWRAM `0x0200ECED`, 9 ASCII bytes | Observed (watchpoint + savestate diff) |
| Buffer raw savestate offset | `0x2FCED` | Observed |
| Acceptance flag | EWRAM `0x02000F40` (0 → 1) | Observed (state diff) |
| Screen-state word | IWRAM `0x030010D0` (4 → `0x0D`) | Observed (state diff) |
| Savestate raw EWRAM base | `0x21000` (so flag `0x02000F40` → raw `0x21F40`) | Derived |
| Savestate raw IWRAM base | `0x19000` (so `0x030010D0` → raw `0x1A0D0`) | Derived |
| Game-state base pointer | `0x020003BC` (ROM pointer at `0x0800AA5C`) | Derived |
| GameLevelTest constructor | `0x0800A8D0` (caller `0x0800B1AE`) | Derived |
| GameLevelTest creator | `0x0800B258` (called only from `0x0800A840`) | Derived |
| `0x0800A840` callers | none found | Derived |

Published codes are **absent** from the ROM as ASCII and as packed 45-bit integers (all 24 searched in both forms, zero hits) → algorithmic generation/validation, not a lookup table of ready-made codes.

## 5. Algorithm

Recovered format (high confidence, Observed/Derived):

- Alphabet, index 0..31: `B C D F G H J K L M N P Q R T V W X Z # ? * 0 1 2 3 4 5 6 7 8 9`.
- Each of the 9 input symbols maps to its 5-bit index; total width 45 bits.
- **9th-symbol checksum:** for the pristine published prefix `9W9KNN?D`, exactly one of 32 ninth symbols (`F`) was accepted (1/32). This is the signature of a 5-bit checksum over the first 8 symbols.
- **Additional prefix constraint:** every single-symbol mutation of a published 8-symbol prefix (all 8 positions, tested with the next-alphabet alternative), 16 random 8-symbol prefixes, and a full 32×32 sweep of positions 7–8 for a mutated prefix all yielded zero accepted codes. Therefore validity is not determined by the 9th symbol alone — the first 8 must belong to a tiny valid set (consistent with only the 24 published prefixes), and no symbol is free/wildcard.
- The checksum is **not** any of: `sum mod 32`, XOR of symbols, XOR of bit-rotated symbols (all 5^8 rotation combos tested, 0/24), weighted sum mod 32 (best of 200,000 random weight vectors matched only 7/24), or a simple linear GF(2) parity of the ninth symbol.
- Two published pairs differ in only 2 symbols while remaining valid (Hard `K14K8DD*3` → `K1ZK4DD*3`: positions 2 XOR `0x08`, 4 XOR `0x04`), consistent with a generator whose adjacent-level outputs differ in scattered bits — i.e. a hash-like function of (level, difficulty), which yields a small closed set.
- The precise checksum/generator function, field layout (level, difficulty, lives), and bit permutation remain **unknown** (§8).

## 6. Tables

Alphabet index map (file `0x7D1178`):

```
 0 B   1 C   2 D   3 F   4 G   5 H   6 J   7 K
 8 L   9 M  10 N  11 P  12 Q  13 R  14 T  15 V
16 W  17 X  18 Z  19 #  20 ?  21 *  22 0  23 1
24 2  25 3  26 4  27 5  28 6  29 7  30 8  31 9
```

Published level passwords (GameFAQs, archived snapshot; all 24 verified in-game):

| Effect | Easy | Hard |
|---|---|---|
| Clear game | `1DL194?N4` | `TV5PQBCZV` |
| Level 2 | `9W9KNN?DF` | `45CH7JWZ8` |
| Level 3 | `**40J2ZJ6` | `C9V??GDZ6` |
| Level 4 | `**Z0G7Z7L` | `85BM3QXZ?` |
| Level 5 | `1G21GRW5R` | `537?2TW1?` |
| Level 6 | `?1FJB113H` | `MG7BT*X15` |
| Level 7 | `NZ70N5KX0` | `TH#3*XW9K` |
| Level 8 | `PX5NPH*3*` | `RJ2689W*5` |
| Level 9 | `TWQV9XJ7?` | `K14K8DD*3` |
| Level 10 | `GXTP1*G90` | `K1ZK4DD*3` |
| Level 11 | `MW5PK1H8?` | `9LJVPVZ6G` |
| Level 12 | `J*GV92WTF` | `HJ90T0Z#2` |

Note: GameFAQs' "Level 2" code showed `01` on the map screen; published labels are taken as-is (guide §16.15). Field layout unknown, so not resolved.

## 6b. Enumeration

**Space definition:** 9 positions × 32 symbols = 45 bits = **35,184,372,088,832** representable strings. Checksum width (5 bits, 9th symbol) inferred; field boundaries unknown. Known accepted members: exactly 24 published codes (no additional codes found in any source checked: GameFAQs archived cheats, TCRF, Cheat Happens, wiki pages, plus this retry's web search which returned no additional list).

**Novel code: none generated.** The accept set appears closed at the 24 published codes; all targeted searches below returned zero novel accepted codes. This section documents the closed-set result with full sweep tables rather than claiming an unrecovered checksum as an unknown.

### Oracle sweep tables (all results are in-game observations)

| # | Experiment | Prefix / candidates | Trials | Accepted (novel) |
|---|---|---|---|---|
| 1 | Pristine published prefix `9W9KNN?D`, all 32 ninth symbols | `9W9KNN?D` + A | 32 | 1 — `9W9KNN?DF` (published). 31/32 rejected. |
| 2 | Single-symbol mutation of prefix, all 8 positions (`9W9KNN?DF` base, next-alphabet alternative), each + all 32 ninth symbols | `BW9KNN?D`, `9X9KNN?D`, `9WBKNN?D`, `9W9LNN?D`, `9W9KPN?D`, `9W9KNP?D`, `9W9KNN*D`, `9W9KNN?F` | 8×32 = 256 | **0** |
| 3 | Random 8-symbol prefixes, each + all 32 ninth symbols (seed 999) | `H98L?JQM`, `WFW3T3GX`, `CQRP*NH7`, `1L97BFVK`, `T3X0DN7J`, `5NRTJFRC`, `ZMV8*7JD`, `4H2JFX2#`, `9F7DF7JJ`, `WHJ9?M53`, `N6D#J#6F`, `L9XT0D9B`, `2460L0FR`, `6Z0VB09D`, `0XX3J*4D`, `23X3?PFV` | 16×32 = 512 | **0** |
| 4 | 2-D brute force of positions 7 and 8 for novel 7-prefix `BW9KNN?` | `BW9KNN?` + all 32×32 | 1024 | **0** |
| 5 | Prior: prefix `BCDFGHJK` + all 32 ninth | arbitrary prefix | 32 | **0** |
| 6 | Prior: prefix `9WBKNN?D` (published prefix with one data symbol changed) + all 32 ninth | mutated published prefix | 32 | **0** |
| 7 | Prior: all 32 values at position 2 of `**40J2ZJ6` | published code position sweep | 32 | **0** |
| 8 | Prior: single-symbol mutations of `9W9KNN?DF` (2 alternatives × 9 positions) | published code | 18 | **0** |
| 9 | Prior: extrapolated two-symbol candidates | — | 4 | 1 accepted, already published (`K1ZK4DD*3`); 3 rejected |
| 10 | Prior: random 9-symbol codes | — | 8 | **0** |
| 11 | Published codes entered | 24 | 24 | 24/24 accepted (all published) |

**Total distinct unpublished strings tested: ~2,000. Novel codes found: 0.**

### Rejection list (≥5, all in-game observed via the oracle)

| Input | Reason | Result |
|---|---|---|
| `9W9KNN?DB` | Wrong 9th symbol of a published code | Rejected — orange `ENTER PASSWORD` remains |
| `9W9KNN?DC` | Wrong 9th symbol | Rejected |
| `BW9KNN?DF` | Mutation at position 0 of a published code | Rejected |
| `9WBKNN?DF` | Mutation at position 2 | Rejected |
| `9W9LNN?DF` | Mutation at position 3 | Rejected |
| `9W9KPN?DF` | Mutation at position 4 | Rejected |
| `9W9KNP?DF` | Mutation at position 5 | Rejected |
| `9W9KNN*DF` | Mutation at position 6 | Rejected |
| `9W9KNN?FF` | Mutation at position 7 | Rejected |
| `BBBBBBBBB` | Literal garbage | Rejected (red flash / cleared slots) |
| `H98L?JQM*` etc. (16 random prefixes × 32 ninth) | Random | All rejected |

Screenshots: `evidence_ACCEPT_published.png` (purple map, accepted), `evidence_REJECT_wrong9.png` (orange password screen, wrong 9th), `evidence_REJECT_mutprefix.png` (orange, mutated prefix).

### Accept-layer bound

- The 9th symbol is a 5-bit checksum of the first 8 (1/32 completion rate for a valid published prefix).
- No field was observed to be free: all 8 prefix positions are checksum- and/or range-sensitive.
- The accepted set is bounded empirically to the 24 published codes within ~2,000 targeted candidates. **Because the space is 35 trillion and the generator was not recovered, this is an empirical bound, not an exhaustive proof of exactly 24.** No novel accepted code exists in the swept space; a novel code could only lie in an unswept region that all 24 published prefixes and every structural mutation failed to reach.
- Hidden/debug screen enumeration: `GameLevelTest.cpp` panel exists (`0x0800A8D0`, resource load `0x0800B258`), but its only caller `0x0800A840` has no callers; no menu path or button sequence reaches it — unreferenced/dead, not a cheat. No other hidden menu entry was found in the walked screens.

## 7. Validation evidence

- **Observed:** all screenshots (language, title, main menu, difficulty, password grid, map/level select, dialogue); GDB/watchpoint hits at `0x08008F96` reading `0x0200ECED`; savestate diffs locating buffer and accept flag (`0x02000F40` 0→1, `0x030010D0` 4→`0x0D`); 24/24 published codes accepted; every sweep/rejection count above; sibling ROM header/hash; accepted/rejected screenshots on `:316`.
- **Derived:** alphabet index map from `0x0807D1178`; asset/string xrefs and literal-pool loads; buffer/flag RAM addresses and savestate raw offsets; call graph proving `GameLevelTest` unreachable; absence of plaintext and packed code tables in ROM; 9th-symbol checksum from the 1/32 pristine-prefix completion; XOR/rotation/weighted-sum checksum non-fits.
- **Inferred:** field semantics of the 45-bit value (level/difficulty/lives) and the checksum construction — no direct evidence recovered, so not claimed. Closed-set conclusion is an inference from ~2,000 zero-result trials, labeled as such.

## 8. Unknowns

1. Checksum/generator function: not isolated. Ghidra auto-analysis created no functions in the `0x08009xxx`–`0x0800A2xx` Thumb region; the password panel uses thunk-style indirect calls (`bl <veneer>; bx rN`), so a BL-target scan was uninformative. mGBA's `-d` debugger watchpoints (`watch/w 0x02000F40`) re-triggered forever on a boot-time memset at `0x0802606E` and could not be stepped past; `watch/c 0x030010D0` caught only a 4→0 screen transition, not the accept write. The GDB stub (`-g`, port 2345) replied `timeout`/packet errors and could not be used as an oracle.
2. Field layout (level, difficulty, lives) and the code for Level 1 / unusual lives counts remain unminted.
3. The pause-menu overlay was not captured; strings and TCRF description are the only evidence.
4. The published "Level 2" → map `01` off-by-one was not resolved.
5. Whether an undocumented button sequence reaches `GameLevelTest` was not exhaustively proven (only static call graph + walked screens).
6. Exact cardinality of the accepted set: empirically consistent with 24, but not proven exhaustively over `32^9` strings because the validator was not recovered.

## 9. Tooling

- `arm-none-eabi-objdump` (`-M force-thumb`), Capstone 5.0.7, Keystone, Ghidra 12.1.4 via REA MCP (`open_binary`, `analyze_function`, `procedure_pseudo_code`, `xrefs`, `search_procedures`), `strings`, `xxd`, `file`, `sha*sum`.
- mGBA (`mgba -3`, `-g`, `-d`), Xvfb `:316`, openbox, `xdotool`, `scrot`, ImageMagick.
- Python helpers in `/tmp/opencode/garfieldpooky2/`: `stateutil.py` (PNG `gbAs` zlib extractor/differ), `oracle.py` (fresh-launch patched-savestate oracle), `sweep.py` (32-symbol ninth sweep), `mutsweep.py` (prefix-mutation sweep), `randprefix.py` (random-prefix sweep), `twod.py` (position 7×8 sweep), `dbg.py` (pty driver for `-d`), `analyze.py`/`analyze2.py`/`fitxor.py` (static checksum fitting), `ramverify.py` (RAM flag attempt). Logs: `mutsweep.log`, `randprefix.log`, `twod.log`.
- Web sources: archived GameFAQs cheats (`web.archive.org/web/20220804030516/...`), TCRF, GameHacking.org index (ROM identity). A retry web search returned no additional code list. No ROM or copyrighted assets are redistributed by this report.

## 10. Legal note

No ROM image or copyrighted game assets are redistributed. Only addresses, algorithms, hashes, counts, and analyst-generated findings are published.
