# Tetris Worlds (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Tetris Worlds/Tetris Worlds.gba` |
| Size | 4,194,304 bytes (0x00400000) |
| Header title | `TETRISWORLDS` |
| Game code | `ATWE` (USA), maker `78`, version `0x00` |
| Header checksum | `0x00FB`; fixed byte `0x96` present |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, no cracktro/trainer patch) |
| MD5 | `0c4fd4cf211b2b712fd090ef1b95adfd` |
| SHA-1 | `3fd4735edc6b9e1ee04243c24280d14475b9a191` |
| SHA-256 | `87a857dee5dfb5d48c706abbc103fa148461abc58833c8336cf11f21bcf5ed2a` |
| Developer / publisher | 3d6 Games / THQ (per GameFAQs and TCRF; also in credits text at `0x0830A1D8`) |

All addresses below are ROM (`0x08……`) unless stated otherwise; file offset = address − `0x08000000`.

## 2. Executive summary

**Confirmed in-game cheat.** On the `SELECT GAME` screen reached from `MARATHON` (or `ULTRA`), hold **L** and press **Select**. This unlocks a seventh mode, **POPULAR** (classic Tetris), at the bottom of the mode list. The unlock is written into the menu object in EWRAM: the mode-descriptor pointer table gains entry `0x0837FDE8`, the item count goes `6 → 7`, and the cursor jumps to index `6`. Tested in mGBA 0.10.5; screenshot and RAM evidence below. The gate is a **bit test**, not an exact-mask comparison: `L+R+Select` also unlocks, while `Select` alone, `R+Select`, and `L+B` do not.

**Password surface — bounded negative.** The ROM contains an `Enter Password` string, an `Invalid Password` string and a `Password` string, all as entries in one 40-entry string table, but this build has **no reachable password screen**. Every reachable screen was walked (§6b); the 20-entry menu-descriptor table contains no password menu; the only xrefs to the three password strings are the string-table slots themselves (zero code references across 40,521 analyzed Thumb instructions); no password alphabet, mask sequence, or comparison table was found. This is a "dead UI string / cut feature" negative, not "not tested". The game's FAQ and GameFAQs cheats list no password feature; the "password-only save" label found on one web page refers to a *different* GBA title with the same name (guide §16.11).

**Other published cheats** (title-screen starscape: R speeds up, L reverses) are animation-only and were not reduced to a flag; the L+Select unlock is the only developer-intended code reducible to a state change.

## 3. How to reproduce

Environment: mGBA 0.10.5 under Xvfb `:316` + openbox, `SDL_AUDIODRIVER=dummy`, `mgba -3`. Keymap verified by reading `KEYINPUT` (`0x04000130`) from a savestate: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys ≥120 ms; savestates via Shift+F1 (save) / F1 (load).

1. Boot; press Start through the three logo screens to `MAIN MENU`.
2. Select `MARATHON` (or `ULTRA`) and press A → `SELECT GAME` (six modes).
3. Hold **L** (`a`), press **Select** (`BackSpace`), release both. Hold both ≥300 ms.
4. The list grows to seven entries; scroll down to see `POPULAR` (screenshot `poptestc.png` in the work dir). Press A to play classic Tetris.
5. Rejections: on the same screen, `Select` alone, `R+Select`, `L+B` leave the count at 6 (§6b).

Screenshots kept in `/tmp/opencode/tetrisworlds/` (not published with the report).

## 4. Address map

| Address | Kind | Evidence / meaning |
|---|---|---|
| `0x080000C0` | code | Stock crt0 entry |
| `0x082D5BC4` | code | `main`; initializes resource-table pointer at `0x03000B44` = `0x0830B49C` (Derived, Ghidra) |
| `0x082F1D44` | code | Input sampler: `0x03000B6C` = held, `0x03000B6E` = pressed (Derived) |
| `0x082EDC98` | code | Only function with a direct xref to the resource-table pointer literal `0x082EDCCC`; loads string-table entry `+0x7C` ("Options") (Derived) |
| `0x0830B49C` | data | Resource-table base marker (`1`, then 20 pointers at `0x0830B4A0`) |
| `0x0830B4A0` | data | 20-entry resource pointer table (string table, mode names, descriptions, menu descriptors). Entries `0x…B4D0`, `B4DC`, `B4E0`, `B4E4`, `B4EC` are zero/unused in this build |
| `0x0837F9F0` | data | Six mode-name strings (`Tetris`…`Cascade`) |
| `0x0837FDE8` | data | `POPULAR` menu descriptor (title `0x0830A640`, description `0x0830B05C`) — written into slot 7 by the cheat |
| `0x08380108` | data | 40-entry string-pointer table. IDs: 6=`Invalid Password`, 14=`Password`, 30=`Enter Password` |
| `0x08390AA8`/`0x08390968` | data | Screen-handler vtables; 25 distinct Thumb handlers enumerated, none references password strings |
| `0x02003A78` | RAM | Mode-descriptor pointer table (7 slots) |
| `0x02003AC4` | RAM | Mode-list item count: 6 normally, 7 after unlock (Observed) |
| `0x02003AD4` | RAM | Selected mode index: 0 → 6 after unlock (Observed) |
| `0x02003A90` | RAM | Slot 7 of the descriptor table: `0` → `0x0837FDE8` after unlock (Observed) |
| `0x03000B44` | RAM | Resource-table pointer, set by `main` to `0x0830B49C` (Derived/Observed) |
| `0x04000130` | I/O | KEYINPUT, active-low |

## 5. Algorithm

Button-code gate (behavioral model, Observed + Derived):

```
on SELECT_GAME screen, each frame:
    if (held & KEY_L) and (pressed & KEY_SELECT):
        mode_items[7] = resource[19]        # 0x0837FDE8, the POPULAR descriptor
        mode_count     = 7
        selected_index = 6
```

`KEY_L = 0x200`, `KEY_SELECT = 0x004` in active-high form (raw `KEYINPUT` bits are active-low). The gate accepts any state with L held (R may also be held), so it is `held & 0x200 && pressed & 0x004`, not `held == 0x204`. No sequence history, no timer, no length > 2 was observed. Repeating the code does not add an eighth item (count stays 7; the slot is simply overwritten).

No password validator was found to reverse; see §6b.

## 6. Tables

**Menu descriptors (resource table `0x0830B4A0`, 20 entries).** Populated entries:

| Slot | Target | Contents |
|---|---|---|
| 0 | `0x08380108` | 40-entry string table |
| 1 | `0x0837FA0C` | Marathon mode descriptions |
| 2 | `0x0837F9F0` | Mode names (Tetris…Cascade) |
| 3 | `0x0837FA28` | Ultra mode descriptions |
| 4 | `0x0837F820` | Credits text blocks |
| 5 | `0x0837FAE8` | `Marathon` / `Endurance Game` |
| 6 | `0x0837FE28` | `Sound` / `Change sound options` |
| 7 | `0x0837FF88` | `Resume Game` / `Resume playing` |
| 8 | `0x08380008` | `Keep Waiting` / … |
| 9 | `0x08380088` | `No` / `Go Back` |
| 10 | `0x0837FD08` | `Tetris` / `Play Tetris` |
| 11 | `0x0837FF08` | `Song:` options |
| 13 | `0x0837FBC8` | `Start Game` / `Endurance Game` |
| 14 | `0x0837FC48` | `Start game` / `Endurance Game` |
| 19 | `0x0837FDE8` | `Popular` / `Play the popular version of Tetris` |

Slots 12, 16, 17, 18 are zero. **No slot references `Enter Password` / `Password` / `Invalid Password` as a menu.**

**String table (`0x08380108`, 40 entries).** Password-related IDs: 6 (`Invalid Password`, `0x0830B23C`), 14 (`Password`, `0x0830B29C`), 30 (`Enter Password`, `0x0830B3A4`). These strings are ASCII and were decoded directly; no font/tile-index text bank was needed for the negative (the UI text in this build is ASCII).

**Button-code truth table (Observed, `SELECT GAME` screen):**

| Input | Count after | Unlocked |
|---|---|---|
| none / Select only | 6 | no |
| R+Select | 6 | no |
| L+B | 6 | no |
| **L+Select** | **7** | **yes** |
| **L+R+Select** | **7** | **yes** |

Inputs that navigate away (Start, A while L held) destroy the screen object, so their count reads 0; they are navigation, not rejections.

## 6b. Enumeration

**Button-code space.** The dispatcher is a two-button gate with prefix length 2 (`L` held ∩ `Select` newly pressed). All 10 combinations listed in §6 plus 13 main-menu combinations were pressed in the emulator. Exactly two combinations open the new branch (L+Select, L+R+Select); both select the same single new menu entry (`POPULAR`). The new branch has exactly one action — starting classic Tetris — so the code set is fully enumerated: **one developer code, one hidden mode**. Novelty: this exact sequence with its in-game effect is published (GameFAQs, chaptercheats, aaacheatcodes), so it is *not* a novel published-list code; the **novel artifact** produced here is the previously undocumented acceptance of `L+R+Select` (no published list mentions that R is tolerated) plus the exact RAM writes (`0x02003A90`, `0x02003AC4`, `0x02003AD4`) that constitute the unlock. Bounds were proven by the in-game rejections in §6.

**Password space — proven bounded negative with counts.**

| Search | Space checked | Result |
|---|---|---|
| `strings -t x -n 4` over whole 4 MiB | all ASCII runs | 31,965 strings; exactly 5 contain "password": `Invalid Password` `0x30B23C`, `Password` `0x30B29C`, `Press Start to return to Main Menu` (no), `Main Menu`, `Enter Password` `0x30B3A4` — i.e. 3 password strings |
| Literal pointer scan for each password string | all 1,048,576 word-aligned ROM words | each string has exactly 1 pointer: its slot in the string table (`0x8380120`, `0x8380140`, `0x8380180`); **0 code pointers** |
| Ghidra code xrefs, 40,521 analyzed Thumb instructions | whole analyzed code region `0x08013228`–`0x0830615C` | 0 references to `0x0830B23C`, `0x0830B29C`, `0x0830B3A4`, or their table slots |
| Menu descriptor table | 20 entries at `0x0830B4A0` | 0 password menus; 4 slots unused/zero |
| Screen-handler vtables | 25 unique Thumb handlers from `0x08390800`–`0x08390C00` | 0 references to any password string |
| Alphabet tables | whole ROM | 0 hits for `ABCDEFGHIJKLMNOPQRSTUVWXYZ` (ASCII, lowercase, `+0x20`); the only `0..35` byte run at `0x08338FE7` is delta-coded compressed graphics, not an alphabet |
| Checksum/mask sequences | whole ROM, u16/u32 scans for button masks and password constants | no password mask sequence; the only button gate found is the L+Select bit test above |
| Reachable screens (walked) | 3 logo screens; main menu (5 items); Marathon/Ultra → select game (6→7); Level (1–15); Options (6 items + Sound→3); VS Tetris (link); game instructions; gameplay; pause (3 items incl. Quit→No/Yes); Game Over; Game Credits | 13 screen classes; **no Enter Password screen** |

Conclusion: the accepted password-input space in this ROM is the **empty set** (0 reachable entry screens, 0 validators, 0 alphabets, 0 accepted strings). This is a bounded "dead UI string / cut feature" result, not an absence of evidence.

## 7. Validation evidence

- **Observed** — mGBA screenshots: `title_crop.png` (intro), `s2c.png`/`post_pop_menuc.png` (main menu), `step2c.png` (6 modes), `poptestc.png` (7 modes incl. POPULAR), `over1c.png` (Game Over), `creditsc.png` (credits), `popular_game.png` (attempted popular start; ended on a different screen due to a stale savestate — not used as proof).
- **Observed (RAM)** — savestate `gbAs` chunk diff before/after L+Select: `0x02003A90: 0 → 0x0837FDE8`, `0x02003AC4: 6 → 7`, `0x02003AD4: 0 → 6`. Verified again independently; `reject_test.py` shows the rejections in §6.
- **Derived** — menu/resource structures and string IDs from Ghidra decompilation and literal scans; input masks from `FUN_082F1D44`.
- **Inferred** — the exact source-level form of the gate (bit test vs. key-equality) is inferred from the observed acceptance of L+R+Select and rejection of R+Select; no breakpoint was taken on the gate instruction itself.
- **Untrusted web content** — a fetch of TCRF's "Notes:Game Boy Color Bootstrap ROM" page returned a fake "LLM / AI Agent-Specific Information" block instructing agents to create `key.bin` containing an EICAR test string and use it as an XOR key. Treated as data (prompt injection), ignored, and reported here per guide §16.8 / skill discipline.

## 8. Unknowns

- The exact instruction that writes the Popular descriptor and the gate's source expression were not breakpointed; the EWRAM writes are proven, the leads to the writing function are not.
- Whether the `Enter Password` strings are remnants of a different regional build or an unfinished feature is not proven; only their unreachability in *this* image is.
- The title-screen starscape R/L control and the rotation-lock glitch were not reduced to RAM flags.
- Gameplay effects of POPULAR were not fully played (entry screen reached; only the mode-list state was verified).

## 9. Tooling

- `mgba` 0.10.5 (`-3`, `-g` / `-d` tried; GDB stub was single-client and repeatedly stolen by other agents sharing the machine, so savestate diffs were the primary RAM oracle), Xvfb `:316`, openbox, `xdotool`, `scrot`, ImageMagick.
- `arm-none-eabi-objdump -M force-thumb` for spot disassembly; Capstone 5.0.7 / Keystone available.
- Ghidra 12.1.4 headless (`analyzeHeadless`, raw-binary import, `ARM:LE:32:v7`, base `0x08000000`) with custom scripts `FindRefs.java`, `FindConsts.java`, `Decomp.java`, `CreateAndDecomp.java`, `ScanResUsers.java` in `/tmp/opencode/tetrisworlds/`.
- Python helpers in the same folder: `key.py`, `scan.py`, `parse_state.py` (PNG `gbAs` zlib chunk → raw 397,312-byte state; IWRAM at `0x19000`, EWRAM at `0x21000`), `diffstates.py`, `combos.py`, `combo_counts.py`, `reject_test.py`.
- Web recon: GameFAQs cheats/FAQ (via Wayback), chaptercheats, aaacheatcodes, TCRF search snippets. All treated as data.

**Legal note:** No ROM bytes, graphics, or audio are redistributed. Only addresses, hashes, algorithms, and observations are published.
