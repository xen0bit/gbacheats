# Tony Hawk's Pro Skater 2 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tony Hawk's Pro Skater 2.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `TONY HAWK 2!` |
| Game code | `ATHE` (file reports `ATHE52`) |
| Maker | `52` |
| Version | `0x00` (Rev. 00) |
| `file` classification | `Game Boy Advance ROM image: "TONY HAWK 2!" (ATHE52, Rev.00)` |
| MD5 | `b658a9b8641db5c1a94d61b6fcc05da5` |
| SHA-1 | `029f8fcabee3e4e0339db77c80961191b5bb84e9` |
| SHA-256 | `2b499d56f17ffe895ce9fb56154a2c5274048400462790b383212a69fa184b16` |
| Entry word | `0xEA00002E` → `b 0x080000C0` (stock crt0; not a scene cracktro) |
| Fixed `0x96` at 0xB2 | present; complement byte 0x00; header checksum 0xC000 |

Publisher/engine strings confirm the Vicarious Visions GBA build (`Vicarious Visions Inc.` splash at boot; audio-engine banner `Shin'en Multimedia. Code: B.Wodok` at file 0x7F7B8F).

## 2. Executive summary

This SKU exposes **no password/text code-entry surface**. The only developer-intended code system documented for it is a **hold-R button sequence** system entered at the main menu or the in-game pause menu; correct entry is signalled by the main-menu wheel spinning a full circle (or the pause menu shaking). A total of **13 toggleable cheats** and their exact names are present in the ROM (`0x74FE10`), and the complete unlock machinery was recovered (`CheatInit` `0x0800CA28`, `CheatUnlock` `0x0800CA44`, `CheatName` `0x0800CA74`, flag array `0x03003A80`, pointer slot `0x03001D48`). The OPTIONS→CHEATS menu item is rendered **greyed out / non-selectable** in every reachable state examined (gated feature, guide §16.3 case 4), and no button sequence tested in the emulator produced a confirmed unlock on this revision.

**A bounded negative is proven for the static search space** (§6b): all 8,388,608 bytes were searched for every published sequence in 16 encodings (~1.5×10⁹ byte comparisons) with zero hits; a generic scan found 547 candidate button-mask runs and none matched a published code; no code-entry text exists in the text banks. The button-code validator itself was **not located**, so this report does **not** claim the published codes are invalid — it records them as *published but unverified for this exact revision*, and bounds the search that was performed.

One novel, undocumented 10-press sequence was minted and entered in the emulator; the cheat flags were read from an uncompressed mGBA savestate before and after and were unchanged — an in-game rejection bound for this input path (§6b).

## 3. How to reproduce

- Emulator: mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `mgba -3 ROM`.
- Keymap (mGBA SDL defaults, verified against the menus): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys 40–90 ms; menu wheel needs ~1.2 s to settle before A is accepted.
- Boot path: title/logo → Vicarious Visions splash → title (5×Start) → main menu wheel.
- Main menu wheel items (4): CAREER MODE, FREE SKATE, SKATE SHOP, OPTIONS. CAREER MODE submenu: CONTINUE CAREER, NEW CAREER, LOAD CAREER, TUTORIAL. OPTIONS submenu (10): SOUND OPTIONS, CHEATS (dimmed), TRICKZOOM, KID MODE, CONTROL SETUP, HIGH SCORES, SAVE CAREER, GAP CHECKLIST, CREDITS, BACK.
- Published GBA codes were entered both at the main menu and in gameplay with the R modifier held, at hold/gap timings of 30/40 ms, 40/50 ms, 50/30 ms and 90/60 ms (`/tmp/thps2/keys.py`).
- Savestate RAM reads: mGBA `.ssN` are PNGs containing a zlib-compressed `gbAs` chunk; decompressed size 0x61000. IWRAM starts at state offset `0x19000` (confirmed by the pointer `0x03003A80` written to `0x03001D48`, found at state offset `0x1AD48`). Cheat flags: state offset `0x1CA80 + 4*i`.

## 4. Address map

| Item | ROM address | Evidence |
|---|---|---|
| crt0 / entry | `0x08000000`–`0x08000120` | Derived (ARM disassembly) |
| Cheat name table (13 NUL strings) | file `0x74FE10` → `0x0874FE10` | Derived (strings + literal xrefs) |
| `CheatInit` (clear 13 flag bytes, stride 4) | `0x0800CA28` | Derived (Thumb) |
| `CheatUnlock` (first zero byte ← 1, return index / −1) | `0x0800CA44` | Derived (Thumb) |
| `CheatName(index)` jump table | `0x0800CA74`, table `0x0800CA88` | Derived (Thumb) |
| Generic key-input recorder/player module | `0x08010A40`–`0x08010CC8` | Derived (Thumb, KEYINPUT literals `0x08010A88/AEC/C48`) |
| Flavour text `new cheat available:` | file `0x77B93C` → `0x0877B93C` | Derived |
| Menu string `cheats` | file `0x77BFEC` → `0x0877BFEC` | Derived |
| Career save validator (magic `54 01`, checksum) | `0x08006718` | Derived |

| Item | RAM address | Evidence |
|---|---|---|
| Global state pointer slot | `0x03001D48` → `0x03003A80` | Observed (CLI debugger watchpoint) |
| Cheat flag array, 13 entries × 4 bytes, flag = byte 0 | `0x03003A80`–`0x03003AB0` | Observed + Derived |
| Key-input byte tested by `0x08010A40` | `0x03001DE4` | Derived |
| Volatile word changed by button entry (timer/counter) | `0x03001DE8` | Observed (savestate diffs) |

`CheatUnlock` callers: only `0x08005FB6` (career save load) and `0x08002B47A` (gameplay "new cheat available") — a **complete two-caller enumeration** (BL scan over all 8 MiB).

## 5. Algorithm

Cheat-state management (fully recovered):

```c
// 0x0800CA28 — called with r0 = *(u32*)0x03001D48 (= 0x03003A80)
void CheatInit(u8 *flags, int arg1) {
    for (int i = 12; i >= 0; --i) {
        flags[i*4] = 0;
        if (arg1) flags[i*4 + 1] = 0;
    }
}

// 0x0800CA44 — exhaustive: first zero flag is set; returns index or -1
int CheatUnlock(u8 *flags) {
    for (int i = 0; i <= 12; ++i)
        if (flags[i*4] == 0) { flags[i*4] = 1; return i; }
    return -1;
}

const char *CheatName(u8 *flags, int i);   // 0x0800CA74, i<=12 else NULL
```

Input recorder (generic, used by the replay system, not proven to be the cheat matcher):

```c
// 0x08010A98 — called once per frame; active-high mask = ~KEYINPUT & 0x3FF
held  = ~KEYINPUT & 0x3FF;
press = held & ~st->prev;          // st+6
buf[st->count++] = held;           // st+12 = buf, st+20 = count, st+16 = capacity
if (st->count == st->capacity) { buf[st->count++] = 0xFFFF; st->flag = 1; }
// 0x08010AF8 consumes buf until the 0xFFFF sentinel (replay playback)
```

**Button-code validator: NOT RECOVERED.** No function was found that maintains a progress index over button masks and writes a cheat flag; `CheatUnlock`'s two callers are save-load and gameplay-unlock, and no third caller exists.

## 6. Tables

**6.1 – The 13 cheat names (exact ROM strings, file 0x74FE10 / ROM 0x0874FE10), indexed by the `CheatName` jump table at 0x0800CA88:**

| Index | Name | ROM address |
|---:|---|---|
| 0 | perfect balance | `0x0874FE10` |
| 1 | always special | `0x0874FE20` |
| 2 | stud mode | `0x0874FE30` |
| 3 | sim mode | `0x0874FE3C` |
| 4 | moon physics | `0x0874FE48` |
| 5 | anime | `0x0874FE58` |
| 6 | always zoom | `0x0874FE60` |
| 7 | slow-nic | `0x0874FE6C` |
| 8 | the shadow | `0x0874FE78` |
| 9 | other side | `0x0874FE84` |
| 10 | fugitive | `0x0874FE90` |
| 11 | disco lights | `0x0874FE9C` |
| 12 | invisibility | `0x0874FEAC` |

This list matches, exactly and in order, the 13 cheats named in the published "All Cheats Unlocked" GBA code — strong evidence that this ROM *is* the SKU those codes target.

**6.2 – Published button sequences (3rd party cheat indexes GBA lists; treated as DATA, not verified truth).** All are entered while holding R. `A/B/Start/L/R/D-pad` denote GBA buttons.

| Effect | Sequence | Length |
|---|---|---:|
| All cheats unlocked | B,A,Down,A,Start,Start,B,A,Right,B,Right,A,Up,Left | 14 |
| All levels / max money | B,A,Left,Down,B,Left,Up,B,Up,Left,Left | 11 |
| Blood off | B,Left,Up,Down,Left,Start,Start | 7 |
| Disco zoom (paused) | Left,A,Start,A,Right,Start,Right,Up,Start | 9 |
| Happy blood/sparks (main menu) | Start,A,Down,B,A,Left,Left,A,Down | 9 |
| Jetpack mode | Left,A,Start,A,Right,Up,Start | 7 |
| Level select / unlock all levels | A,Start,A,Right,Up,Up,Down,Down,Up,Up,Down | 11 |
| Set time to zero (paused) | Left,Up,Start,Up,Right | 5 |
| Spider-Man wallcrawl | Right,A,Down,B,A,Start,Down,A,Right,Down | 10 |
| Unlock Mindy | A,Left,Left,Up,Right,B,A,Start | 8 |
| Unlock Spider-Man | Up,Up,Down,Down,Left,Right,Left,Right,B,A,Start | 11 |

No literal from any of these 11 sequences appears in the ROM in any encoding tested (§6b).

## 6b. Enumeration

**Space definition (button-code system).** Input alphabet = GBA buttons with active-high masks `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200`; R is held as a modifier. Published sequence lengths are 5–14 presses. Checksum/field layout: none found. No mask table was located, so the representable space cannot be measured; the *published* set is 11 sequences over 2 entry contexts (main menu, pause).

**Cheat-state space (fully enumerated).** 13 flag bytes at `0x03003A80 + 4*i`; each is 0=locked / 1=unlocked; `CheatUnlock` can set at most 13 bits and then returns −1. The 13 names are listed in §6.1. Total reachable cheat states = 2¹³ by construction of the setter, but only two *setters* exist in the whole image (save-load, gameplay-unlock).

**Static search bounds (counts).**
- Full-ROM literal searches: 11 published sequences × 16 encodings (u16 LE/BE with and without R, u8 masks, active-low, reversed, 4-bit button indices, 8/16-bit indices, ASCII upper/lower, 3/4/5-bit packed, with/without 0xFFFF or 0x0000 terminators, with leading/trailing R) = 176 distinct needle searches over 8,388,608 bytes ≈ **1.48×10⁹ byte comparisons; 0 hits**.
- Generic table scan for consecutive u16 values drawn from the button-mask set (including R/L): **547 candidate runs** of length ≥5 with ≥3 distinct masks; **0** matched any prefix of any published sequence. Long runs were all repeating values in compressed audio/graphics (e.g. `0x101` runs near `0x08571C22`, `0x08625274`; `0x001` runs near `0x08751A7C`).
- 3-byte/2-byte prefix searches: 2-byte prefixes produced thousands of incidental matches (expected); 3-byte prefixes produced 0 plausible table locations.
- Text bank: `strings -t x -n 4` over the whole ROM; keyword set `password|cheat|code|secret|debug|unlock|level select|invalid|wrong|correct` → 8 hits, all UI/flavour strings (`Find the Secret Tape`, `to unlock level`, `new cheat available:`, `cheats`, etc.); **no code-entry prompt, no alphabet table, no accepted/rejected code strings**. The +0x20 case-shift was also considered; no hidden text bank was found.
- Search of game RAM (decompressed savestates at main menu and after code entry) for published sequences in the same 16 encodings: 0 hits.

**Novel code and rejection bound.** Minted sequence `R-held + B,B,Up,Up,Start,B,Left,Down,Start,A` — a 10-press combination that appears in **no** published list (checked against §6.2 and the 3rd party cheat indexes GBA tables). Entered at the main menu with 40 ms holds. Savestate before (`ss9`) and after (`ss1`) read at `0x03003A80+4*i`: `01 01 01 01 01 01 01 01 01 01 01 01 01` in **both** — no cheat flag changed. The volatile word at `0x03001DE8` moved `0x00000000 → 0x01000000`, i.e. the game consumed the input but did not unlock anything. This bounds rejection for that input path and timing.

**Published-code entry attempts (counts).** 5 attempts at the main menu with the full 14-press "All Cheats" sequence (timings 30/40, 40/50, 50/30, 90/60 ms, plus one L-modifier variant) and 1 attempt at 90/60 ms with R. In 4 of 6 attempts the menu wheel rotated as a side effect of D-pad presses and returned to CAREER MODE; one burst captured a mid-rotation frame (`spin_0.png`) consistent with the published "360° spin" confirmation, but the subsequent OPTIONS screen still showed CHEATS dimmed and the cheat flags were unchanged from baseline. **No attempt produced a verified unlock**; these codes are recorded as *unverified on this revision*, not as invalid.

**Why this is a bounded negative, not "no cheats".** The cheat names, the 13-flag state, the unlock routine, the gate on OPTIONS→CHEATS, and the published code list for this exact SKU are all present. What is *absent* from the searched space is the code-sequence table/validator. The conclusion is therefore bounded to: *the validator was not found by exhaustive literal/pattern/text searches of the 8 MiB image and RAM, and no tested input was observed to unlock a flag.*

## 7. Validation evidence

- **Observed** (emulator): boot screens, main menu wheel (4 items), career submenu (4 items), OPTIONS submenu (10 items, CHEATS rendered dim), in-game free-skate render, save/load savestates, cheat flags read from decompressed `gbAs` chunks, all keystroke effects captured to `/tmp/thps2/*.png`.
- **Observed** (CLI debugger `mgba -d`): two watchpoint hits at `0x03001D48`/`0x03003A80`; pointer written `0x03003A80` at `PC=0x0800EE94`; `CheatInit` clearing the array at `PC=0x0800CA34`; a flag set at `PC=0x0800F81A` and cleared at `PC=0x0800F5CE`.
- **Derived** (Thumb disassembly): `CheatInit`/`CheatUnlock`/`CheatName` bodies and jump table; the 13-name mapping; the two-caller enumeration of `CheatUnlock`; the input recorder's active-high mask and 0xFFFF sentinel; the save validator at `0x08006718`.
- **Inferred**: that the published button codes are the intended entry mechanism (supported by the exact 13-cheat name match and by published sources), and that a "360° spin" frame observed during entry might be the acceptance cue. Neither was confirmed by a flag change.
- **Not observed**: any successful cheat unlock from controller input; any code-entry UI.

## 8. Unknowns

- The button-code validator/mask table, if it exists in this build, was not located. Its location may be in code (a fixed-prefix dispatcher, guide §5.4a) rather than a contiguous table, which would explain the zero literal hits.
- Semantics of the second byte of each 4-byte cheat entry (entries 0–2 carry `01`, others `00` at the main menu) were not resolved.
- The gate that greys out OPTIONS→CHEATS was not isolated to a specific flag; no reachable state was found that enables the item.
- Whether the published codes require a different revision, a different modifier (L rather than R), a stricter inter-key timing window, or an in-progress career was not determined.
- In-game (pause-menu) entry was attempted only once; no systematic pause-menu sweep was completed.

## 9. Tooling

All analysis artifacts were kept in `/tmp/thps2/`:

| File | Purpose |
|---|---|
| `find_codes.py`, `find_codes2.py`, `find_codes3.py` | published-sequence literal searches, 16 encodings |
| `scan_tables.py`, `scan_diverse.py` | generic button-mask run scans |
| `dump16.py` | u16 ROM dumps with mask decoding |
| `find_input.py` | KEYINPUT literal + Thumb LDR-pool scan |
| `blscan.py`, `blscan2.py` | Thumb BL caller scans |
| `namexref.py`, `strxref.py`, `find_cheatxref.py` | literal-pointer xref scans |
| `ptrtable.py` | pointer-run inspection |
| `ssdiff.py`, `sslayout.py`, `readflags.py`, `search_ram.py` | mGBA `gbAs` savestate extraction, IWRAM diff, flag reads |
| `keys.py` | XTEST keypress helper (hold/gap/modifiers) |
| `dbgscript.txt` / `mgba_d.log` | mGBA CLI debugger script and capture |

Toolchain: `arm-none-eabi-objdump` (`-M force-thumb`, `--adjust-vma=0x08000000`), Capstone 5.0.7, `mgba` 0.10.5 (`-3`, `-d`, `-g`), gdb-multiarch (GDB stub port 2345 was occupied by another session), `xdotool`, `scrot`, Xvfb `:318` + openbox.

**Legal note:** no ROM bytes or copyrighted assets are reproduced here; only hashes, addresses, algorithms, and own-tool findings are published.
