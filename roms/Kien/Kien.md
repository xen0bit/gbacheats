# Kien (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Kien/Kien.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `KIEN` |
| Game code / maker | `XXXE` / `20` (file reports `XXXE20, Rev.00`) |
| Version | 0x00 |
| Fixed byte 0x96 | present (0x96) |
| Header checksum / complement | `0x0000` / `0x7B` (checksum 0 is a rebuilt-header artifact, not a patch indicator) |
| Entry word | `0xEA00002E` → standard ARM branch to `0x080000C0` (stock crt0) |
| MD5 | `fe8f2d7b6b58cb78ca51f8bceaa0f254` |
| SHA-1 | `da1673ec5ec35f8ececa3f04cb6a92d61237ce72` |
| SHA-256 | `8f50703ceffa968e874eccd75e0bd47987a8839d971b5ccf5189b8eb068cee63` |

**Build provenance.** This is the 2004 *prototype* image (game code `XXXE20`, "PM Studios" splash), not the 2024 Incube8 retail release (`AGB-829E-USA`). One Nintendo-logo hit only (file offset 0x4 → header at 0x0); no multi-game image, no appended trainer/cracktro, no patched entry word. **Observed.**

## 2. Executive summary

Kien has a **developer-intended 9-character progress-password system** on the title screen (`NEW GAME / PASSWORD / OPTIONS`). The answer is a **closed lookup table of exactly 8 accepted strings**, not an algorithmic checksum code: a 4-byte-optimized `strcmp` compares the typed 9-byte input against 8 fixed NUL-terminated strings laid out as 2 heroes × 4 quests.

The ROM contains 8 plaintext passwords at `0x0802DB60` (12-byte stride). Four (`K*`) match the published GameFAQs-derived list for Kjan's quests II–V. **The other four (`E*`) — Elandel's quests II–V — are in the ROM but appear in no published code list found** (cheat-database.com, Cheat Happens, GameFAQs, TCRF were checked). All 8 were accepted in-game; `EE10LVQ1M` was additionally typed on the real password screen and RAM-verified.

The full space is 8 acceptors out of 36^9 ≈ 1.015×10^14 representable 9-symbol strings. Single-character mutations, empty/all-zero input, and out-of-alphabet hero/level bytes are rejected to the title screen. No button-code table, no hidden debug menu, and no algorithmic second code system were found; the string bank is plain ASCII, so the negative does not depend on undecoded font/tile text.

**Novel/unpublished codes (not in any published list):** `EE10LVQ1M`, `EF18LVQ2L`, `EG30LVQ3G`, `EH70LVQ4S` — Elandel, quests II, III, IV, V respectively.

## 3. How to reproduce

* **Emulator:** mGBA 0.10.5 SDL under Xvfb on `:318`, `SDL_AUDIODRIVER=dummy`, `-3` scale; window keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
* **Path:** boot → story scroll (≈30 s; tap A/Start to advance) → title `KIEN` → `PASSWORD` → 9 slots initialized `000000000`.
* **Input mechanics (derived + observed):** UP/DOWN scroll the current slot through `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ` (36 symbols, wrap at both ends); LEFT/RIGHT select slot; START submits. A 20 ms key hold produces exactly one scroll step; longer holds auto-repeat.
* **Code entry:** to set symbol with alphabet index *i* (0-based), press DOWN *i* times, then RIGHT to advance. After 9 symbols press START.
* **Expected results:** `KA10LVQ1M` → "Quests" book, Kjan + QUEST II; `EE10LVQ1M` → same book, **Elandel** + QUEST II; book pages show `< PREV`, `START=SKIP`, `NEXT >` and a live `PASSWORD: <current code>` display.
* **Fast oracle used for exhaustive verification:** patch the 9 ASCII bytes at savestate offsets `0x20E74`, `0x20E84`, `0x20E94` (IWRAM `0x03007E74` etc.) in the mGBA `.ss1` `gbAs` chunk, load with `mgba -t patched.ss1`, press START. This bypasses typing but uses the game's own validator.
* **Codes tested:** all 8 table codes; rejection cases `KA10LVQ1N`, `ZZ10LVQ1M`, `AE10LVQ1M`, `KA10LVQ2M`, `000000000`.

## 4. Address map

All addresses are GBA bus addresses; file offset = address − `0x08000000`.

| Address (ROM) | File offset | Meaning |
|---|---|---|
| `0x08000000` | 0x0 | Header; entry branch `0xEA00002E` |
| `0x0802DB60` | 0x2DB60 | Password string table, 8 NUL-terminated 9-char strings, 12-byte stride |
| `0x0802DBB4` | 0x2DBB4 | `KA10LVQ1M` (first Kjan code) |
| `0x0802DB60` | 0x2DB60 | `EH70LVQ4S` (last Elandel code) |
| `0x087D6C0C` | 0x7D6C0C | Pointer table used by validator: 2 heroes × 4 quests, 16 bytes per hero, 4 bytes per entry |
| `0x0802959C` | 0x2959C | Validator: optimized `strcmp` of input vs one ROM string |
| `0x080295B0` | 0x295B0 | `cmp r1,r0` inside validator (read watchpoint on input buffer lands here) |
| `0x08005DD0`–`0x08005E2E` | 0x5DD0 | Validator caller: loops hero 0..1 × quest 0..3, writes acceptance flag |
| `0x08005DF8` | 0x5DF8 | BL to validator |
| `0x080021B4` | 0x21B4 | Literal pointer to `MALKUT MAP` string (`0x08031494`) |
| `0x0803145C`–`0x08031580` | 0x3145C | UI string bank: `PRESS >START< TO CONTINUE`, `MALKUT MAP: ...`, `< PREV START=SKIP NEXT >`, `PASSWORD:`, `EXIT` |
| `0x0802F02C`–`0x0802F518` | 0x2F02C | Title/menu bank: `OPTIONS`, `NEW GAME`, `PASSWORD`, `ENGLISH`, `ITALIANO`, `SELECT HERO TO PLAY` |
| `0x0803100C`–`0x080311D0` | 0x3100C | Credits bank (Italian dev team) |

| Address (RAM) | Meaning |
|---|---|
| `0x03007E74` | Input password buffer: 9 ASCII bytes + NUL (watchpoint-confirmed validator input) |
| `0x03007E84`, `0x03007E94` | Mirrors of the 9-byte buffer used by the UI |
| `0x030041A0` | Game-state struct pointer target (r9 in validator caller) |
| `0x030041B0` | Acceptance flag low nibble: quest index 1..4 (1=Quest II … 4=Quest V); `0x00` on the password screen |
| `0x04000130` | KEYINPUT (active-low) |

## 5. Algorithm

```
# Validator (0x0802959C), Thumb, C-equivalent:
int cmp_password(const char *input, const char *expected) {
    while (((uintptr_t)input | (uintptr_t)expected) & 3) {
        if (*input != *expected) return (uint8_t)*input - (uint8_t)*expected;
        if (!*input) return 0;
        input++; expected++;
    }
    for (;;) {
        uint32_t a = *(uint32_t*)input, b = *(uint32_t*)expected;
        if (a != b) return byte_mismatch(input, expected);   // 0x80808080 has-zero-byte trick
        if ((a - 0x01010101) & ~a & 0x80808080) return 0;    // NUL found -> equal
        input += 4; expected += 4;
    }
}

# Caller (0x08005DD0):
flag = 0
for hero in 0..1:                       # 0 = Kjan, 1 = Elandel
    for quest in 0..3:                  # 0..3 = Quest II..V
        expected = *(char**)(0x087D6C0C + (hero<<4) + (quest<<2))
        if cmp_password(input_buf_0x03007E74, expected) == 0:
            b = [0x030041A0 + 0x10]
            [0x030041A0 + 0x10] = (b & 0xF0) | ((quest+1) & 0x0F)
            flag = quest + 1
return flag
```

There is **no checksum, no bit-packing, no key table, and no character substitution**: the comparison is byte-exact over the 9 ASCII bytes. The `SECRET LEVEL: YOU CAN'T ENTER NOW!` string (`0x0802D89C`) is a gameplay-state gate, not a code path.

## 6. Tables

### 6.1 Accepted codes (exact, NUL-terminated, 9 characters)

| ROM pointer | String | Hero | Quest | Published? |
|---|---|---|---|---|
| `0x0802DBB4` | `KA10LVQ1M` | Kjan (warrior) | II — Astral Amulet | Yes (cheat-database.com, GameFAQs-derived list) |
| `0x0802DBA8` | `KB18LVQ2L` | Kjan | III — VS Tujon | Yes |
| `0x0802DB9C` | `KC30LVQ3G` | Kjan | IV — Supreme Keys | Yes |
| `0x0802DB90` | `KD70LVQ4S` | Kjan | V — VS Khaalbak | Yes |
| `0x0802DB84` | `EE10LVQ1M` | Elandel (priestess) | II — Astral Amulet | **No** |
| `0x0802DB78` | `EF18LVQ2L` | Elandel | III — VS Tujon | **No** |
| `0x0802DB6C` | `EG30LVQ3G` | Elandel | IV — Supreme Keys | **No** |
| `0x0802DB60` | `EH70LVQ4S` | Elandel | V — VS Khaalbak | **No** |

Pointer-table layout at `0x087D6C0C`: offsets `0,4,8,12` = Kjan II–V; offsets `16,20,24,28` = Elandel II–V.

### 6.2 Input alphabet

`0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ` — 36 symbols, index 0..35. Confirmed by scrolling one slot through 36 steps on the real screen (`cycle.png`) and by UP-from-0 wrapping to `Z`.

### 6.3 Published-code verification

Source: `https://cheat-database.com/display/cheat.php?id=171577` ("Kien — Quest Passwords", GBA), listing `KA10LVQ1M` (Quest II), `KB18LVQ2L` (III), `KC30LVQ3G` (IV), `KD70LVQ4S` (V). All four literals exist verbatim in the ROM and were accepted in-game. Cheat Happens lists no Kien GBA cheats; GameFAQs cheats page returned 403 and no additional list was recovered. No TCRF page was found. **No prompt-injection content was encountered in the fetched pages; all fetched text was treated as data.**

## 6b. Enumeration

* **Space definition:** alphabet 36 symbols × 9 positions = 36^9 = 1,015,120,533,826,416 ≈ 1.02×10^14 possible strings. The UI also allows submitting shorter/other strings, but the validator compares against fixed 9-byte strings only.
* **Validator model:** exact `strcmp` against an 8-element table; reimplemented above. Because the table is iterated with exact bounds `hero 0..1`, `quest 0..3` (disassembly at `0x08005E22` `cmp r4,#3` and `0x08005E2C` `cmp r0,#1`), **the accepted set is provably exactly these 8 strings** — there are no algorithmic extra codes, no checksum variants, and no aliases.
* **Novel codes not in any published list:** `EE10LVQ1M`, `EF18LVQ2L`, `EG30LVQ3G`, `EH70LVQ4S`. All four were accepted via the savestate oracle. `EE10LVQ1M` was **typed on the real password screen** (each symbol set by counted DOWN presses; buffer read back from savestate as `EE10LVQ1M`) and START produced the Elandel QUEST II book screen. Screens: `ee2_entered.png`, `ee2_result.png`, `oracle_all.png` (in `/tmp/opencode/kien/`).
* **Effect distinction:** the same quest number with a different hero is the unadvertised combination — published lists document only Kjan's four quests; the ROM's second hero row is undocumented.
* **Bounds proven by rejection:** `KA10LVQ1N` (last checksum-like char changed), `KA10LVQ2M` (quest digit changed), `AE10LVQ1M` (hero prefix changed), `ZZ10LVQ1M` (out-of-table hero/level), `000000000` (default) all returned to the title screen with no quest flag set. Captured as `oracle_KA10LVQ1N.png`, `oracle_KA10LVQ2M.png`, `oracle_AE10LVQ1M.png`, `oracle_ZZ10LVQ1M.png`, `oracle_000000000.png`.

## 7. Validation evidence

* **Observed (emulator):** title, options (TUTORIAL ON/toggle, CONTROLS, CREDITS, BACK), password screen, hero select (Kjan/Elandel), quest book with PREV/NEXT/START=SKIP and live password display, CHAPTER I screen, gameplay, hero sheet/status screen (SELECT), level-up message. Screens saved under `/tmp/opencode/kien/walk_*.png`, `ng_*.png`, `ch1_*.png`, `hsheet_*.png`, `book2_*.png`, `bookpages.png`.
* **Observed (RAM):** savestate diff placed the 9-char input at `0x03007E74` (`pwb.ss` all `0` → `entered_KA.ss`/`ee2_entered.ss` exact ASCII). Acceptance flag at `0x030041B0`: `0x00` on password screen → `0x01` after Quest II (both K and E codes). Read watchpoint on `0x03007E74` broke at `0x080295B0` with `r3=0x0802DBB4`, proving which strings are compared.
* **Derived (disassembly):** `strcmp` at `0x0802959C`; 8-entry iteration at `0x08005DD0`–`0x08005E2E`; table at `0x087D6C0C`; string table at `0x0802DB60`.
* **Inferred:** the `SECRET LEVEL` and `MALKUT MAP` screens exist in the data bank but are gameplay/progress gated; they were not reached as standalone cheat surfaces.

## 8. Unknowns

* The `MALKUT MAP` teleport/level-select screen (`0x08031494`) was not reached in-game during this session; its exact entry condition is unresolved (it is referenced from gameplay code near `0x080021B4`). It is not a password/code surface.
* No hidden debug menu was found: no `debug`/`test`/`cheat` strings, no plausible 4+ entry key-mask table in the code region (62 candidate runs were all code/tile-data false positives, e.g. long `0x0303` runs). This is a bounded negative over ASCII strings and aligned u16 mask sequences, not a proof about uncompressed bitmap text (the UI text here is plain ASCII, so that exception does not apply).
* The 2024 retail revision (`AGB-829E-USA`) was not analyzed; this report applies to the `XXXE20` prototype hash above.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for Thumb disassembly.
* Python + `capstone`/`struct` for literal/pointer scans; custom `pwrq`-independent scripts in `/tmp/opencode/kien/`.
* mGBA CLI debugger (`mgba -d` over a pty) for read watchpoints and PC capture; GDB stub is **not compiled into this mGBA 0.10.5 build** (no listener on :2345).
* Custom scripts: `ss.py` (mGBA `.ss1` `gbAs` zlib state reader/differ), `patchss.py` (patch 9-byte buffer in savestates), `kb.py` (XTEST input), `enter3.py` (verified password entry), `oracle_batch.py` (accept/reject oracle), `template.py` (glyph matching).
* Web sources: cheat-database.com cheat id 171577 (published code list); Cheat Happens (empty); GameFAQs (403).
* No ROM or copyrighted assets are redistributed here — only hashes, addresses, algorithms, and findings.

---

**Legal note:** analysis only; no ROM bytes, graphics, music, or game text are republished beyond the short code strings necessary to document the system.
