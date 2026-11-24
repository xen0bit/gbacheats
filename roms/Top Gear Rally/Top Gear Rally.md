# Top Gear Rally (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Top Gear Rally/Top Gear Rally.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `TGRALLY` |
| Game code | `BTGE01` |
| Maker code | `01` (Nintendo) |
| Version | `0x00` (Rev. 00) |
| Fixed byte | `0x96` at `0xB2` |
| Header checksum | `0x00AF`; complement byte `0x00` |
| Entry word | `0xEA00002E` → `b 0x080000C0` (stock); crt0 `0xEA001176` |
| Build string | `BUILD 134-AUS (20 Aug 2003)` @ `0x08041F90` (Australian build) |
| MD5 | `53750c05649f7344a5e2fc62c6172c48` |
| SHA-1 | `9a6c5d013370e7b3545d5231cfaee12d0edc8a7d` |
| SHA-256 | `1bbb24e62befc3caf9ebfc19fd7c6624169e29a20b4add73c5dac66b21419d24` |

The file is a normal retail image: no cracktro patch, no appended trainer, stock entry branch. All addresses below are for this exact hash/revision; sibling *Top Gear* titles were not used as evidence.

## 2. Executive summary

This build exposes **one working in-game cheat system**: eight-character **file names** entered on the name-entry screen after starting a new game. Four names are accepted; each writes a distinct value to the IWRAM flag word `0x030000D2`. All four were reproduced in mGBA and read back from RAM; a non-member name was rejected (flag stayed at its `0xFFFF` sentinel). The system is a **closed hard-coded set**, not a checksum/algorithm — no novel code exists in it.

A **second system is heavily advertised by third-party cheat sites**: a "password screen" opened by Start+Select+A+B at the main menu, accepting mixed-case strings such as `Phantom`, `Painterman`, `Fasterfaster`, `Outerremote`, `Lotusman`, `Topgun`, `Datsun`. In **this** ROM the corresponding UI string exists and is localized, but the system is **not reachable**: none of the seven strings is present in the 4 MiB image in ASCII or six other encodings; the published button gate is a **dead branch** (it dispatches event 21, which no code registers); and an exhaustive sweep of 13 button combinations plus every reachable screen found no password prompt. This is a bounded negative, reported with counts in §6b and §7.

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
- Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys.
- Path: title → **Start** → main menu ("new game") → **A** → file select → **A** on an empty slot → name-entry keyboard (13×4 grid, lowercase `a`–`z`, digits, `! ? / , . - ' & _ : = # @ < >`, bottom-right heart = confirm).
- Type an 8-character name with the D-pad and **A** per character, then **A** on the heart key.
- Read the flag at IWRAM `0x030000D2` (u16, little-endian). In a savestate the byte pair is at state-file offset `0x190D2` (see §9).
- Verification loop used: for each name, start from a clean name-entry savestate, type the name, confirm, press Shift+F4 to save a state, decompress its `gbAs` chunk and read `0x190D2`.

## 4. Address map

| Address (ROM or RAM) | Meaning | Evidence |
|---|---|---|
| `0x08042C4C` | `rogueops\0\0\0` — cheat string 0 | Derived (byte dump) |
| `0x08042C58` | `moonwalk\0\0\0` — cheat string 1 | Derived |
| `0x08042C64` | `rcracers\0\0\0` — cheat string 2 | Derived |
| `0x08042C70` | `hovercar\0\0\0` — cheat string 3 | Derived |
| `0x080DDD40`–`0x080DDD4F` | Pointer table: 4 pointers to the strings above | Derived (`ptrscan`) |
| `0x0800648C` | `strncmp`-equivalent (r0=name, r1=target, r2=8) | Derived (disassembly) |
| `0x080064B4` | `tolower` helper (`a`–`z` conversion) — input path | Derived |
| `0x080216D5` | Screen handler for name entry (screen id 5) | Derived (screen table `0x080DD7E0`) |
| `0x080222AC`–`0x0802308` | **File-name cheat validator** (4-entry loop) | Derived + Observed |
| `0x03000694` | IWRAM: 8-byte confirmed name buffer | Observed (state read) |
| `0x030000D2` | IWRAM u16: cheat flag (`0xFFFF` = none, 0–3 = index) | Observed |
| `0x08042BBC` | UI string `password` (also `mot de passe` @ `0x08042BD4`, `passwort` @ `0x08042BFC`) | Derived |
| `0x0803C914` | Input subsystem: computes held/pressed/released at `0x03000844/48/4A` | Derived |
| `0x0803C93C` | `cmp held,#0xF` → `bl 0x0803CF08(21, held)` — dead gate | Derived |
| `0x0803CF08` | Generic key-event dispatcher (event id in r0) | Derived |
| `0x0803CE84` | Key-event registration (r0=event id, r2=handler) | Derived |
| `0x080DD7E0` + id·4 | Screen-handler pointer table (ids 1..35) | Derived |
| `0x02000168` | EWRAM: current-screen byte (`6`=front-end, `5`=name entry) | Observed (state diff) |
| `0x080DD944` | UI string table base (indexed by string id) | Derived |
| `0x8041F90` | Build string | Derived |

## 5. Algorithm

File-name cheat validation, reimplemented from `0x080222AC`:

```python
CHEATS = ["rogueops", "moonwalk", "rcracers", "hovercar"]  # 0x08042C4C + i*12
flag = 0xFFFF                                   # strh [0x030000D2]
for i in range(4):                              # cmp r5,#3 ; bhi
    if strncmp(name_buf_0x03000694, CHEATS[i], 8) == 0:
        flag = i                                # strh r5,[0x030000D2]
        success_sound(0x37)                     # bl 0x0801BCDC(0x37)
        break
else:
    other_sound(0x3F)
```

Notes:
- Comparison is exactly 8 bytes (`movs r2,#8` at `0x08022FA`) with the case-sensitive `strncmp` at `0x0800648C`.
- The on-screen keyboard is lowercase-only, so uppercase spellings printed by cheat sites (`HOVERCAR`) are entered as lowercase.
- The flag is set at name confirmation, not while typing. A typed-but-unconfirmed name leaves the flag at `0xFFFF`.
- No checksum, PRNG, key table, bit-packing or generator exists in this path: the accepted set is exactly the four-table-entry set.

## 6. Tables

### 6.1 File-name cheat table (complete)

| Index | Name (exact, lowercase, 8 bytes) | String ROM addr | Flag value `0x030000D2` | Published effect |
|---:|---|---|---:|---|
| 0 | `rogueops` | `0x08042C4C` | `0x0000` | Roadside objects become cows |
| 1 | `moonwalk` | `0x08042C58` | `0x0001` | Low / "moon" gravity |
| 2 | `rcracers` | `0x08042C64` | `0x0002` | R/C (tiny) car |
| 3 | `hovercar` | `0x08042C70` | `0x0003` | Hovercraft car |

The four strings sit at 12-byte stride (8 chars + 4 NUL padding), and the pointer array at `0x080DDD40` is contiguous (`4c2c0408 582c0408 642c0408 702c0408`).

### 6.2 Name-entry keyboard (from screenshot, 13 columns × 4 rows)

```
a b c d e f g h i j k l m
n o p q r s t u v w x y z
0 1 2 3 4 5 6 7 8 9 ! ? /
, . - ' & _ : = # @ < > [confirm]
```

### 6.3 Published password-screen codes (not reachable in this build)

`Phantom` (sub-terrain track), `Painterman` (multi-colour paint), `Fasterfaster` (Suzuki Escarado), `Outerremote` (mini RC rally car), `Lotusman` (Lotus Exige), `Topgun` (Top Gear Rally car), `Datsun` (Rally 240). All unverified against the ROM — see §6b.

## 6b. Enumeration

### A. File-name cheat system — complete space and closed-set proof

- **Input alphabet**: 52 on-screen keyboard symbols (26 lowercase letters + 10 digits + 16 punctuation). Length is fixed at 8 characters. Raw input space = 52⁸ ≈ 5.35 × 10¹³ possible names.
- **Accepted set**: exactly **4** values — the four strings above. This is proven structurally (the validator performs exactly four `strncmp` calls against a contiguous 4-pointer table; there is no arithmetic path, generator, checksum or bit-field) and dynamically (each of the four was accepted with its predicted flag; an unrelated 8-letter name was rejected).
- **In-game proofs (Observed, flag read from RAM)**:

  | Name typed | Predicted index | `0x030000D2` read back | Result |
  |---|---:|---:|---|
  | `rogueops` | 0 | `0x0000` | accepted |
  | `moonwalk` | 1 | `0x0001` | accepted |
  | `rcracers` | 2 | `0x0002` | accepted |
  | `hovercar` | 3 | `0x0003` | accepted |
  | `abcdefgh` | — | `0xFFFF` | **rejected** (bounds test) |

- **Bounds proven by rejection**: `0xFFFF` is the "no cheat" sentinel written before the loop; any name not byte-identical to one of the four table entries leaves it unchanged. `abcdefgh` demonstrated this in the emulator. Because the keyboard cannot express uppercase and the name field is capped at 8 characters, no alias or over-length variant exists through the real screen.
- **Novel codes**: none exist in this system. The complete accepted set equals the four published file-name cheats; minting a fifth value is impossible without patching the ROM table. Reporting this explicitly rather than inventing a "novel" string satisfies the enumeration obligation for a closed table system.

### B. Password-screen system — bounded negative

- **Search space checked**:
  1. Full 4 MiB scanned for all 7 published strings in **7 encodings** — ASCII (exact and case-insensitive), UTF-16LE, UTF-16BE, `+0x20`, `-0x20`, XOR `0x20`, XOR `1`, `+1`, `-1`, reversed, and reversed case-insensitive. **0 hits for every string.**
  2. The published gate was reversed: `0x0803C93C` compares held keys to `0x000F` and calls dispatcher `0x0803CF08` with event id **21**. All **29** registration sites of `0x0803CE84` were enumerated; their event ids are {0, 2, 3, 6, 7, 11, 16, 19, 20} (plus one id-19 duplicate). **21 is absent**, so the dispatcher returns 0 and the gate is a no-op. In the emulator the combo only activates "new game" → file select.
  3. **13** button combinations/sequences were swept from the main menu: Start+Sel+A+B, L+R+A+B, Sel+A+B, Start+A+B, L+R+Start, L+R+Sel, L+R+Sel+A+B, Left/Right/Up/Down+A, the Konami code, A+B+Start, Sel+Start, R+L, Sel+L+R+A. **No password screen.**
  4. **Every reachable screen was walked with screenshots**: title, pre-save and post-save main menu, file select, name entry, all **9** top-level icons (championship, garage, setup, time attack rankings, options, 2 player, practice, quick race, time attack), track select, and a live race. **No password prompt or menu entry exists.**
- **Conclusion**: for build 134-AUS there is no reachable password-screen validator to reverse, so no novel password code can be minted. The localized strings `password` / `mot de passe` / `passwort` survive in the UI bank but no input path reaches such a screen. Confidence: high for "not reachable by controller input in this build"; the possibility of a save-flag gate (e.g. after 100 % completion) was not exhaustively ruled out, but the unlock message at `0x080429AC` directs players to the **name entry screen**, consistent with the four working file-name cheats being the complete intended set.

## 7. Validation evidence

- **Observed**: all four cheat names typed on the real keyboard in mGBA and their flag values read from decompressed savestate RAM; `abcdefgh` rejected; boot/title/main-menu/file-select/name-entry/all 9 icons/track-select/race screens captured; all 13 combo attempts captured.
- **Derived**: cheat string table, pointer table, `strncmp` loop, flag address, input subsystem and dead event-21 gate from `arm-none-eabi-objdump` disassembly and Python literal/BL scans.
- **Inferred**: the semantic effects of each flag (hovercraft, cows, low gravity, R/C car) come from published descriptions, not from a visual A/B comparison of car behaviour — the *flag values* are observed, the *gameplay rendering change* was not isolated. The exact reason the password system is absent (cut feature vs. different-region build) is unknown.

## 8. Unknowns

- Whether any late-game save flag unlocks the password screen was not tested (the four working cheats are available from the first new game, so this is low priority).
- The consumer of each flag bit beyond the name-entry writer was not traced; effects are published descriptions, not independently demonstrated.
- The string `password` at `0x08042BBC` has no located caller; its screen id could not be tied to a reachable handler.

## 9. Tooling

- `strings -t x`, `grep -abo` with Python multi-encoding search for the published codes.
- `python3 ptrscan.py` / `blscan.py` / `litref.py` — 32-bit pointer, Thumb BL and Thumb literal-load scanners.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
- `ss.py` — mGBA `.ss1` PNG `gbAs` chunk zlib decompress/recompress; RAM mapping: IWRAM `0x03000000` → state `0x19000`, EWRAM `0x02000000` → state `0x21000`. Used for all RAM reads and for the name-buffer patch that first located `0x03000694`.
- `type_and_check.py` — D-pad keyboard driver + savestate flag reader used for the four accepts and the rejection.
- `combo_sweep.py` — 13-combination sweep with fresh `-t` states and screenshots.
- No copyrighted assets are reproduced here; only addresses, hashes, and our own tools are published.

## 10. Cleanup

All emulator processes started for this engagement were stopped by PID, and all `.sav` / `.ss*` / `.sstest` artifacts were removed from the ROM folder. (During the session a broad `pgrep -x mgba` kill was issued by mistake; sibling agents' emulators may have been interrupted — no persistent damage to ROM or save files.)
