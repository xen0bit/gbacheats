# Sports Illustrated for Kids Baseball (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Sports Illustrated for Kids Baseball.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `SIFKBASEBALL` |
| Game code | `AKBE6L` |
| Maker | `6L` (0x36 0x4C) |
| Version | 0x00 (Rev.00) |
| `file(1)` | `Game Boy Advance ROM image: "SIFKBASEBALL" (AKBE6L, Rev.00)` |
| Entry word | `0xEA00002E` (stock branch to 0x080000C0) — no cracktro/trainer patch |
| Header checksum | 0x0000; complement byte 0x59 (normal rebuilt-header artifact, not an edited flag) |
| MD5 | `fc40baff09563b7e1187bcb987bb541a` |
| SHA-1 | `a262d54f5f9fc35e7ce410b834f3bcd2aa163f10` |
| SHA-256 | `f7206824a4f49ed161d2f727aa808da56a44ae6751b13e3cc7066fd6a304eb63` |

All addresses below are for **this exact hash**. Work directory: `/tmp/sibaseball`.

## 2. Executive summary

The ROM contains a **complete, developer-intended static code-entry system**: nine sponsor-themed codes that unlock "ALLSTAR" content. It is *not* a checksum/field-encoded password system and there is **no generator**: the validator is a flat loop of `strcmp` calls against a 27-slot table (each of the nine codes duplicated three times). The accepted input set is therefore **exactly nine strings**; no eleventh code can be minted.

Static evidence is strong and complete (validator, unlock routine, flag word, all message strings, all table entries, the per-code All-Star data records). In the emulator I walked every screen reachable from the title menu (Season/Load Team/Pick State/Team Colours/Team Name, Exhibition/Team Selection, Link/Connecting, Credits). **No menu path to the code-entry screen was found**, and I could not obtain an in-game accept/reject screenshot. Per the guide's four-way taxonomy this is a **gated/unknown** surface, not a "no system" result: the handlers and messages exist and are fully decoded. The final answer is a **bounded negative with counts** (§6b), not a claim that the code screen is absent.

Web reconnaissance (GameFAQs 403; Google/DuckDuckGo/Bing blocked or irrelevant) found **no published code list** for this SKU. The nine codes in §6 are recovered directly from the ROM and are not taken from any public list.

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `SDL_AUDIODRIVER=dummy`, Xvfb `:315`, `mgba -3 <rom>`.
* Keymap (verified by menu navigation): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. **A is `x`, not the letter `a`** — the letter `a` is L and does nothing in menus.
* Boot path: BAM! → Sennari → title (timed, ~10 s) → Start → main menu.
* Main menu (4 items, wraps at 4 — confirmed by pressing Down four times): **SEASON / EXHIBITION / LINK / CREDITS**.
* Screens walked (each verified by screenshot, files in `/tmp/sibaseball/`):
  * `s8.png` main menu; `menu_season2.png` Season → LOAD TEAM (five "New Team" slots + Erase);
  * `ps2.png` PICK A STATE (US map), `mapS.png` TEAM COLORS, `tn3b.png` TEAM NAME (A–Z + backspace + END keypad, help text `A Button replaces, B Button exits, START accepts` at 0x08383B9C);
  * `exh4.png` Exhibition → TEAM SELECTION (Warlocks … Hawks, skill 6); `link2.png` LINK → CONNECTING; CREDITS rendered black in this build.
* Savestate slot 1 saved at the main menu (`F1` loads, `Shift+F1` saves); slots 2–4 saved at the Team Name screen for RAM diffing.
* Static tools: `strings -t x`, `xxd`, `arm-none-eabi-objdump -M force-thumb`, custom Python BL/pointer/table scanners in `/tmp/sibaseball/`.

## 4. Address map

| ROM address | Meaning | Evidence |
|---|---|---|
| `0x080314DC` | Code validator (called as UI accept callback) | Derived from Thumb disassembly; literal pool at 0x08031574–0x0803159C |
| `0x080315B0` | Unlock helper: clears all 9 flag bytes with value 2, sets `flag[idx] \|= 2` | Derived |
| `0x080313E4` | Screen setup that installs validator pointer `0x080314DD` at `[arg+12]` | Derived; pointer referenced at 0x083837F0 |
| `0x08031260`, `0x0803162C` | Companion text-entry handlers (other screens) | Derived; pointers at 0x0838359C / 0x08383834 |
| `0x083835D4` | Code string table: 27 × 12-byte NUL-padded records (9 codes × 3 copies), 324 bytes | Derived; dumped and parsed |
| `0x08383718` | 9 × 12-byte All-Star data records (one per code index) | Derived |
| `0x08383878` | Message struct header: `WRONG CODE` (string at 0x0838386C) | Derived |
| `0x08383960` / `0x08383974` | `ALLSTAR\0UNLOCKED\0` and its message struct | Derived |
| `0x08383A30` / `0x08383A48` | `CODE ALREADY USED` and its message struct | Derived |
| `0x08383B9C` | Keypad help text `A Button replaces, B Button exits, START accepts` | Observed (strings + bytes) |
| `0x083837CC` | Code-screen UI object (3 render fn ptrs, child ptr 0x08383828, handler 0x080313E5) | Derived |
| `0x08383820` | Companion text-entry UI object (handler 0x0803162D) | Derived |
| `0x081FD4C0` | Runtime descriptor block: validator ptr `0x080314DD`, message ptrs, code-table ptr, 10-space buffer | Derived |
| `0x0300509C` | Global pointer consumed by the validator; `*(ptr)+0x5E+i` = 9 flag bytes | Derived |
| `0x03005090` | Companion global used by the text-entry handlers | Derived |
| `0x081DCD28` / `0x081DCA68` | `strcmp` / `strlen` (library, identified by instruction shape) | Derived |

## 5. Algorithm

Precise reimplementation of `0x080314DC` (called with one argument `ui`):

```c
void validate(ui) {
    ui->message = &WRONG_CODE;                  // 0x08383878
    char *input = ui->parent->input_buffer;     // [[ui+0]+28]
    for (int i = 0; i <= 8; i++) {              // 9 code indices
        for (int j = 0; j <= 2; j++) {          // 3 duplicate slots each
            const char *want = (char*)0x083835D4 + i*36 + j*12;
            if (strcmp(input, want) == 0) {
                unsigned char *flag = *(unsigned char**)0x0300509C + 0x5E + i;
                if (*flag == 1) {                // already used
                    ui->message = &CODE_ALREADY_USED;  // 0x08383A48
                } else {
                    unlock(i);                   // 0x080315B0
                    ui->message = &ALLSTAR_UNLOCKED;   // 0x08383974
                }
            }
        }
    }
}
void unlock(int idx) {
    for (int k = 0; k <= 8; k++)
        if (flag[k] == 2) flag[k] = 0;          // only one active at a time
    flag[idx] |= 2;
}
```

Notes:
* `strcmp` is exact and case-sensitive (no alphabet fold, no checksum, no field decoding).
* The three copies per code are byte-identical; `j` is used only for addressing, never for the effect. They are redundant aliases, **not** distinct codes (guide §16.4b).
* The nine records at 0x08383718 are structured `[idx, tileA(0x7D+i), tileB(0x55+i), b3, b4, b5, b6, flag, idx2]` for i=0..8 — the first and last bytes are permutations of 0..8, so they are per-code All-Star metadata, not part of the validator. Field meanings are **inferred**.

## 6. Tables

### 6.1 Accepted codes (9 unique; each stored 3×)

| i | Code | Length | Byte slot (i×36) |
|---:|---|---:|---|
| 0 | `GOCIRCUIT` | 9 | 0x083835D4 |
| 1 | `TARGETPLYR` | 10 | 0x083835F8 |
| 2 | `GAMESTOP` | 8 | 0x0838361C |
| 3 | `BESTBUYSTR` | 10 | 0x08383640 |
| 4 | `TOYRUSCOM` | 9 | 0x08383664 |
| 5 | `EBRULES` | 7 | 0x08383688 |
| 6 | `BAMSTAR` | 7 | 0x083836AC |
| 7 | `SIKPOWER` | 8 | 0x083836D0 |
| 8 | `SIKSTAR` | 7 | 0x083836F4 |

Each slot is 12 bytes: ASCII code, then zero padding to 12. The names are sponsor/promotion themed (Circuit City, Target, GameStop, Best Buy, Toys R Us, EB Games, Books-A-Million/Barnes, and two SIK-branded codes).

### 6.2 Per-code All-Star records (0x08383718)

```
i code         bytes
0 GOCIRCUIT    00 7D 55 0E 0C 09 0A 00 08 00 00 00
1 TARGETPLYR   05 7E 56 09 0B 0A 0F 01 00 00 00 00
2 GAMESTOP     01 7F 57 0D 0B 0C 0E 10 04 00 00 00
3 BESTBUYSTR   04 80 58 0F 08 08 09 00 02 00 00 00
4 TOYRUSCOM    02 81 59 0A 0A 0A 0B 00 01 00 00 00
5 EBRULES      08 82 5A 09 0C 0B 0E 11 07 00 00 00
6 BAMSTAR      03 83 5B 0B 0B 0B 0B 00 05 00 00 00
7 SIKPOWER     07 84 5C 0A 09 0E 0C 01 06 00 00 00
8 SIKSTAR      06 85 5D 12 08 08 0A 01 03 00 00 00
```

### 6.3 Flag semantics (inferred from 0x080315B0 and the validator)

| Value | Meaning |
|---:|---|
| 0 | never unlocked / cleared |
| 1 | "CODE ALREADY USED" (validator refuses to re-unlock) |
| 2 | currently active unlock (a new code clears other 2s) |

## 6b. Enumeration

**Space definition.** The validator contains exactly `9 × 3 = 27` literal `strcmp` comparisons and no other comparison, checksum, substitution or bit-packing. Table size = 324 bytes = 27 records × 12 bytes. The three slots of each index are byte-identical, so the number of *distinct accepted inputs* is **9**. Lengths vary from 7 to 10 characters; there is no fixed width, no checksum character and no reserved bit. Total representable distinct accepted values: **9** (not 27, not 2^n).

**Complete enumeration by construction.** Because the accept predicate is `input == table[k]` for k in 0..26 and all 27 entries are dumped above, the accepted set is proven closed: every other string (any length, any case, any trailing byte) returns the default `WRONG CODE` message. This is a static proof from the instruction stream, not a sampling inference.

**Bounded rejection counts (Python reimplementation of the exact predicate):**
* 1,950 single-character A→Z substitutions of the nine codes: 1,950 trials, 1,875 rejected. The 75 "accepted" results are substitutions of a character with itself (repeated letters such as the two `C`s in `GOCIRCUIT`), i.e. they reproduce the same nine strings — **0 novel strings accepted**.
* 63 structural mutations (truncation by one, lowercase, leading/trailing space, appended `X`/`0`, 4-char prefix): 63 trials, **63 rejected**, 0 accepted.
* Distinct accepted strings across all enumeration: **9**.

**Novel code:** none exists. A generator cannot be minted because the format has no payload fields — the validator is a literal whitelist. This is the required bounded negative with counts. No code from this ROM appears in a published list I could retrieve (web recon was blocked), so the nine strings in §6.1 are ROM-derived, not copied from a public list.

**Rejection bounds proven at the code level:** any mismatch sets the default message at 0x08383878 (`WRONG CODE`); a repeat of a used code (flag byte 1) sets 0x08383A48 (`CODE ALREADY USED`) instead of 0x08383974 (`ALLSTAR UNLOCKED`). The "wrong case" and "wrong length" bounds follow from `strcmp` at 0x081DCD28 (length check first, then byte loop).

**Not proven in emulator:** an actual typed accept/reject. The code-entry screen's UI object (0x083837CC) and handler (0x080313E5) are fully decoded, but no reachable menu entry to it was found in the screen walk, so the in-game effect remains at confidence "Derived", not "Observed". This is reported as a gated/unknown surface, not a dead-code claim: I did not prove zero callers for the handler (it is referenced as a data pointer by a generic UI framework).

## 7. Validation evidence

* **Observed** — ROM bytes: code table at 0x083835D4 (27 × 12), All-Star records at 0x08383718, all three message strings, help text, pointer literals. Emulator: every screen listed in §3, keymap, four-item menu ring, savestate RAM dumps.
* **Derived** — validator control flow and flag semantics from Thumb disassembly of 0x080314DC/0x080315B0/0x080313E4; `strcmp`/`strlen` identification from 0x081DCD28/0x081DCA68; exact accept set from the closed 27-entry table.
* **Inferred** — meaning of the nine records at 0x08383718 (per-code All-Star metadata); value 1 = consumed, value 2 = active; sponsor-name interpretations.
* **Not observed** — the code-entry screen itself; an in-game accepted/rejected code; the visible effect of `ALLSTAR UNLOCKED`.

## 8. Unknowns

1. **Entry path to the code screen.** Main menu has exactly four items; no hidden fifth item (Down wraps 4→1). Tested common combos on the main menu (L+R, L+R+A/B/Start, A+B, Up/Down alternation, Start+Select) — none opened a new screen. The screen may be gated by a save/clear flag, reached from a deeper Season-state menu not unlocked during this walk, or launched by a longer undocumented sequence.
2. **Runtime input buffer address** for the code screen. The validator reads `[[ui+0]+28]`; I did not live-break on the validator, so the RAM address of the typed string was not captured.
3. **Stable GDB access.** The mGBA GDB stub bound port 2345 intermittently and later produced packet errors; RAM evidence therefore came from savestate `gbAs` chunk dumps (§16.13), not a live breakpoint. No live accept was captured.
4. **Use of flag value 1.** The validator refuses flag 1, but no writer of value 1 was isolated.
5. **Published-code comparison.** Could not be performed (GameFAQs 403; search engines blocked/irrelevant). The nine codes are ROM-derived.

## 9. Tooling

* `strings -t x`, `xxd`, `file`, `md5sum`/`sha1sum`/`sha256sum`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all disassembly.
* Custom Python scripts in `/tmp/sibaseball/`: `scan.py` (literal u32 pointer scan), `blscan.py` (Thumb BL target scan), `scanrange.py` (pointer-into-range scan), `keyscan.py` (button-mask table scan), `walk.py`/`key.py` (XTEST input + scrot), `combos.py` (button-combo fuzzer).
* Savestate decoding: PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte raw state; IWRAM at +0x19000, EWRAM at +0x21000 (guide §16.13).
* mGBA 0.10.5 under Xvfb `:315`; window focused with `xdotool windowfocus` (no window manager needed); `SDL_AUDIODRIVER=dummy`.

## 10. Legal note

No ROM, extracted graphics, audio or copyrighted asset is redistributed here. Only hashes, addresses, algorithms and the nine short code strings (functional data) are published.

## 11. Cleanup

All processes started for this engagement were stopped by PID (no `pkill`/`pkill -f`): mGBA wrappers/processes 260468, 260470, 263844, 263846, 268240, 268969, 269320, 269806, 272360 and GDB watchers 264254, 269889, 269891 were killed by number. Xvfb `:315` (PID 260353) was stopped at the end. All `.sav` / `.ss1`–`.ss4` artifacts were removed from the ROM folder.
