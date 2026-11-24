# Justice League: Injustice for All (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Justice League: Injustice for All.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `INJUSTICEFOR` |
| Game code | `AJLE` |
| Maker | `5D` |
| Version | 0x00 (Rev.00) |
| Entry branch | `0xEA00002E` — stock `b 0xC0`, **no cracktro** |
| MD5 | `b2c954ccf09e408c55886b6686d39c6f` |
| SHA-1 | `f7d774f3d1f1436c18b044c65e574dc327ad6437` |
| SHA-256 | `71c7829c906de73516473b04ed5333d0a275a261ba7d132482b832a93d85b7f9` |

Phase 0 embedded-header scan: the 156-byte Nintendo logo occurs exactly **once** (file 0x4). There is no second header, no multiboot stub and no appended-header trainer. The header complement byte is 0x27 (recomputed 0x40) and the header checksum is 0x0000 — a rebuilt-header artifact, but the entry word is stock and no trainer menu was found in RAM or on any screen.

**Other Justice League GBA titles (Heroes: The Flash, Chronicles) are independent images and share nothing with this ROM.** Verified by header codes/engine strings: this image is the Saffire/Midway 2002 action-platformer (`AJLE5D`), and its entire code/password surface is described below. No cross-title strings, tables or validator addresses were found.

## 2. Executive summary

This game has a **developer-intended name-password system** and one **pause-menu button code**; no GameShark/CodeBreaker functionality is present in the image.

The name entered at **Main Menu → New Game → ENTER NAME** is compared at game-start against six hard-coded 6–8 letter names stored as plain ASCII at ROM `0x08067338..0x0806736F`. The validator (`0x080297F8`) tries text IDs `0xF8..0xFD` through a language-aware text accessor (`0x0802BA50`) and an exact 8-byte comparator (`0x0802979C`). A match writes a cheat index `1..6` to IWRAM `0x03001D40`.

| # | Password | Effect | Evidence |
|---|---|---|---|
| 1 | `SAMIAM` | Enemies don't attack / attacks pass through you | index reader at `0x0801C3D6` returns early (AI skip); 3rd party cheat indexes |
| 2 | `SAMIWAS` | Unlock all missions | `0x0800D1E6` sets 13 mission flags at `0x030025E0`; RAM-verified |
| 3 | `SAMIBE` | Start with 99 lives | validator writes 99 to `0x03001D60`; re-applied at `0x0800DB0A`; RAM-verified |
| 4 | `SAMICAN` | **No effect in this build** | index set to 4, but zero readers of `0x03001D40` test 4,5,6 |
| 5 | `SAMISHOW` | **No effect in this build** | same |
| 6 | `SAMIKILL` | **No effect in this build** | same |

3rd party cheat index lists the last three with "Unknown" effects; this report resolves that: the flags are set but no code path consumes values 4/5/6 (all ten xrefs to `0x03001D40` enumerated; readers test only 1, 2 and 3 — values 0 and 4/5/6 are ignored).

The 3rd party cheat indexes button code ("pause, on Resume press Select then Start") was verified: the actual trigger is **Select pressed while `Resume` is highlighted on the GAME PAUSED menu** (Start merely resumes play). An **undocumented variant** — Select alone, or Select followed by A/B/Select — sets the same flag; this was enumerated and RAM-verified.

No debug menu, hidden character select, password generator, checksum system or other code surface exists. The password space is provably closed at exactly six strings (§6b).

## 3. How to reproduce

Emulator: mGBA SDL on `DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`. Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Hold keys 70 ms.

**Password path:** boot → title `PRESS START` → Start → `MAIN MENU` (`Load Game` / `New Game` / `Options` when a save exists) → `New Game` → `ENTER NAME` grid (A–Z, backspace, DONE; cursor starts on DONE) → spell a code → `DONE`. The cheat flag is written at DONE, before the intro plays.

**RAM evidence method (guide §16.13, GDB stub unusable here):** mGBA `.ssN` files are PNGs with a zlib-compressed `gbAs` chunk. Decompress it to a 397,312-byte state; IWRAM `0x03000000` starts at raw offset `0x19000`, EWRAM at `0x21000`. Name buffer = raw `+0x19000+0xC90`; cheat index = `+0x19000+0x1D40`; lives = `+0x19000+0x1D60`. For deterministic tests the name buffer in a name-screen savestate was patched directly (the UI caps input at 8 characters), then the state was loaded and DONE pressed.

**Tested codes:** all six above; invalid names `ZZZZZZZ`, `SAMIAX`, `XAMIWA`, `SAMIWAX`, `SAMIKIL`, `SAMIWASX`, `SAMIKILX`, `ABCDEFGH` (all rejected, index 0).

**Button code:** enter a mission → Start (`GAME PAUSED`) → ensure `Resume` is highlighted → Select → (any key resumes). Enumerated 15 modifier/trigger combinations and Select on all four pause-menu items.

## 4. Address map

File offset = ROM address − `0x08000000`.

| Purpose | Address (ROM / RAM) |
|---|---|
| Code strings (contiguous ASCII) | `0x08067338` SAMIKILL, `0x08067344` SAMISHOW, `0x08067350` SAMICAN, `0x08067358` SAMIBE, `0x08067360` SAMIWAS, `0x08067368` SAMIAM |
| Name-entry alphabet (u32: 0x25, Z…A) | `0x08067384`–`0x080673E8` |
| Language text tables (IDs 248–253 = six codes) | `0x08066418`, `0x08069FEC`, `0x0806D5E4`, `0x0807108C`, `0x08074C84` |
| Pointer tables holding the six string pointers | `0x080667F8`–`0x0806680C` and four localized copies |
| Validator / dispatcher | `0x080297F8` (calls text accessor `0x0802BA50`, comparator `0x0802979C`) |
| Comparator (8-byte, NUL early exit) | `0x0802979C` |
| Button-code setter (writes index 1) | `0x08011CE0`, called from `0x0800C366` |
| Name buffer (8 bytes, NUL-terminated) | IWRAM `0x03000C90` |
| Cheat index (0=none, 1..6) | IWRAM `0x03001D40` |
| Lives (u16, 99 for SAMIBE) | IWRAM `0x03001D60` |
| Mission unlock flags (13 bytes) | IWRAM `0x030025E0` |
| Input globals (held / pressed / prev / released) | `0x03001F40` / `0x03001F4C` / `0x03001F60` / `0x03001F64` |
| Global reset clears cheat index | `0x0802A136` |

Key masks (active-high, `~KEYINPUT & 0x3FF`): A=1, B=2, Select=4, Start=8, Right=0x10, Left=0x20, Up=0x40, Down=0x80, R=0x100, L=0x200.

## 5. Algorithm

Pseudocode, bit-exact against the disassembly:

```c
// name_buf = IWRAM 0x03000C90, 8 bytes max, ASCII A-Z + NUL
void check_passwords(void) {
    for (int id = 0xF8; id <= 0xFD; id++) {     // unrolled at 0x08029800
        const char* s = get_text(id);           // 0x0802BA50; all 5 languages
        if (cmp8(name_buf, s)) {                // 0x0802979C
            *(u8*)0x03001D40 = (u8)(id - 0xF7); // 1..6
            if (id == 0xFA)                     // SAMIBE
                *(u16*)0x03001D60 = 99;
            return;
        }
    }
}

bool cmp8(const char* expected) {              // 0x0802979C
    for (int i = 0; i < 8; i++) {
        if (expected[i] != (s8)name_buf[i]) return false;
        if (name_buf[i] == 0) return true;       // both NUL -> match
    }
    return true;                                // 8 equal bytes, no NUL needed
}
```

Notes: the comparator reads the expected string with `ldrb` (unsigned) and the name buffer with `ldrsb` (signed); all stored bytes are ASCII < 0x80 so this is a pure byte compare. `get_text` dispatches on a global language 0–4 through a 5-entry jump table at `0x0802BA80`; **all five language tables return the same six English strings**, so changing language cannot produce a different code.

Button code (`0x0800C2D0`→`0x0800C366`→`0x08011CE0`): requires two flag bits (`0x0300605C & 3 == 3`), `0x030062E4 == 0xFF`, a menu object at `0x03000D1C` with `+0x24 == 0x1E` (the Resume entry) and `+0x44 != 0x0E`, then sets cheat index 1. Only Select on Resume satisfies this; other cursor positions and other buttons do not.

## 6. Tables

**Six-entry code table** (strings at `0x08067338`, text IDs 248–253 in reverse order):

| Text ID | String | Index written | Observed effect |
|---:|---|---:|---|
| 248 (0xF8) | `SAMIAM` | 1 | enemies don't attack (AI early-return) |
| 249 (0xF9) | `SAMIWAS` | 2 | all missions unlocked |
| 250 (0xFA) | `SAMIBE` | 3 | 99 lives |
| 251 (0xFB) | `SAMICAN` | 4 | none (flag unused) |
| 252 (0xFC) | `SAMISHOW` | 5 | none (flag unused) |
| 253 (0xFD) | `SAMIKILL` | 6 | none (flag unused) |

**Input alphabet:** 27 cells — `A`–`Z` plus a backspace arrow (u32 values at `0x08067384`: `0x25`, then `0x5A` down to `0x41`). The name buffer holds at most 8 characters; no space, digits, or symbols are enterable.

**Button code:** context = `GAME PAUSED`, cursor = `Resume`, trigger = Select press (active-high mask 0x0004). Effect = cheat index 1.

## 6b. Enumeration

**Space definition.** The password system is a lookup table, not a checksum: alphabet A–Z (26 symbols), length 1–8 (UI cap 8), buffer NUL-terminated, no reserved bits. The ui-level name space is ~26^8 ≈ 2.09×10^11 spellings, but the validator accepts **exactly six** of them: the six byte-exact strings above, compared over a fixed 8 bytes with NUL early-exit. The full accepted set was proven by (a) enumerating all six literal strings and their pointer-table entries in all five languages, and (b) running the real validator on a matrix of inputs:

| Input | Result |
|---|---|
| SAMIAM / SAMIWAS / SAMIBE / SAMICAN / SAMISHOW / SAMIKILL | accepted, indices 1/2/3/4/5/6 |
| ZZZZZZZ, ABCDEFGH | rejected, index 0 |
| SAMIAX, XAMIWA, SAMIWAX, SAMIKIL | rejected (one-character substitution) |
| SAMIWASX, SAMIKILX | rejected (extra 8th character; proves NUL requirement and exact 8-byte match) |

**Novel code.** There is **no unpublished password**: the accepted set is provably closed at six, every one of which appears on 3rd party cheat indexes, and the comparator admits no aliases (no case folding, no wildcard, no length tolerance, no unused bits). I did not fabricate a "generated code" that the game cannot accept. The equivalent §0.2 button-surface deliverable **was** produced and verified: the *undocumented* input **Select alone on `Resume`** (no Start) sets cheat index 1 — published instructions say "press Select then Start"; Start is not part of the trigger, only the resume key. RAM read: pause-only index 0 → pause+Select index 1; plain Start-resume control stays 0. Enumerated 15 combinations: Select→Start, Select→A, Select→B, Select→Select and Select+L→Start all set index 1; A/B/L/R/Up/Down/Left/Right→Start and L+R→Start, and Select on Mission Select/Options/Quit, all leave index 0.

**Generator/checksum:** none exists — no LDR/BL/pointer path computes a code from game state; the validator is six fixed `strcmp`-style comparisons.

## 7. Validation evidence

* **Observed** (emulator/RAM): title, main menu (Load Game/New Game/Options), Options (Sound/Music/Back, 3-item ring), ENTER NAME grid, intro, SELECTION PAUSED, GAME PAUSED, mission select, gameplay. All six codes typed in-game set indices 1–6; patched-buffer tests reproduce the same. SAMIWAS changed mission-unlock RAM `0x03001F70..0x03001FD5` from all `0xFF` (2 nodes drawn, no portraits) to 54 zero bytes (all nodes + character portraits drawn). SAMIBE set lives 99 at `0x03001D60`. Button code and its undocumented variants set index 1; control inputs do not.
* **Derived** (disassembly / Ghidra): validator `0x080297F8`, text accessor `0x0802BA50`, comparator `0x0802979C`, all six string pointers and all five language tables, effect readers (`0x0800D1E6`, `0x0800DB0A`, `0x0801C3D6`), button setter `0x08011CE0`. Ghidra pseudocode for `FUN_080297f8` matched the observed index writes exactly.
* **Inferred**: indices 4/5/6 are unimplemented cheats (no reader found). The `0x25` symbol in the alphabet table is the backspace glyph, inferred from the UI arrow and table position.

**Text encoding check:** all UI strings were found as plain ASCII with `strings -t x` (e.g. `ENTER NAME`, `DONE`, `SAMIWAS`); the entry alphabet table stores ASCII `0x41..0x5A`. There is no font/tile-indexed text bank that could hide an unscanned code string — the negative result for additional codes rests on ASCII scans plus the pointer-table enumeration, not on an assumption.

## 8. Unknowns

* Why flags 4/5/6 (`SAMICAN`, `SAMISHOW`, `SAMIKILL`) are written but never read — most likely cut or unfinished cheat effects; no consumer exists in this revision, so their effect cannot be observed.
* The header complement byte mismatch (0x27 vs 0x40) is unexplained but benign; no trainer/cracktro behavior was observed.
* The exact meaning of the two flag bits at `0x0300605C` that the button-code gate tests was not traced to its writers beyond the observed Select-on-Resume behavior.
* Only the English UI was walked exhaustively; the four localized banks were verified statically to contain the same six codes.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `strings -t x`, `xxd`, `grep -abo`; `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, Keystone; REA/Ghidra 12.1.4 (`open_binary`, `xrefs`, `analyze_function`) for xrefs and pseudocode; mGBA SDL + GDB stub (tested, unusable here: protocol errors) → savestate diff/patch fallback; Xvfb `:315` + openbox + xdotool; Python helpers in `/tmp/jlinjustice`: `ssdecode.py`, `patch_ss.py`, `enter_name.py`, `test_code.py`, `patch_test.py`, `enum_btn.py`, `verify_sel.py`. Web: archived 3rd party cheat index cheats page and archived 3rd party cheat index page (fetched as data; no instructions in fetched content were acted upon; no prompt-injection payload encountered).

No ROM bytes or copyrighted assets are redistributed in this report.
