# The Simpsons: Road Rage (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Simpsons: Road Rage.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `SIMPSONSRAGE` |
| Game code | `A4AE` |
| Maker | `78` (THQ) |
| Revision / version | Rev.00 (`0xBC = 0x00`) |
| Entry word | `0xEA00002E` (stock) |
| Complement / checksum | `0x4C` / `0x0000` (rebuilt-header artifact; complement is the reliable signal) |
| MD5 | `8f0fdaeda361783ee74abd980b418388` |
| SHA-1 | `46347f021f0829ef70a4f52a9b8836d444f9551a` |
| SHA-256 | `8146d3338b05ebf18ac13cbf941ddfec491c7d21be87de10bd2bcbfbdcf37ee0` |

`file(1)` identifies it as a retail GBA image; no appended trainer or cracktro was found. The entry word and complement byte are consistent with a normal THQ release.

## 2. Executive summary

The GBA SKU has **one** developer-intended cheat system: an 8-symbol password entered on **Options → SET PASSWORD**, where each symbol is one of 16 Simpsons character portraits shown in a 2×8 grid. There is no on-screen text alphabet; the "characters" in published codes are the names of those portraits. All published button codes for this game (L+R + XXXX etc.) belong to the **GameCube / PS2 / Xbox** SKUs — they do not exist in this GBA image (no `DEBUG`/`SECRET`/`LEVEL SELECT` strings, no button-mask sequence table found).

The password is **algorithmic**, not a lookup table. I recovered the validator at `0x08034D0` in full, reimplemented it (`validator.py`), and proved:

* 8 symbols × 4 bits; symbols 0–5 carry a 20-bit money value and a 4-bit mission count (valid 0–10); symbols 6–7 are two independent 4-bit checksums (one simple mod-16 sum, one table-driven mod-16 sum).
* Exact accepted set = **11,000,011** of 16^8 = 4,294,967,296 possible symbol strings (C exhaustive count over all 2^24 payloads).
* A **novel code absent from every published list**, `[0,1,2,3,4,5,15,8]`, was entered through the real UI and accepted: money became **451,329**, mission count **4**, vehicles `0x07FF`, locations `0x1F`, and the game returned to the main menu.
* Bounds were proven by in-game rejection of a wrong checksum-1, a wrong checksum-2, mission count 11, and money 1,000,001 — all checksum-valid where applicable, all rejected with no state change.
* The maximum payload code `[15,5,1,9,13,11,6,12]` (money 1,000,000, mission 10) was accepted and produced vehicles `0xFFFF`, locations `0x3F`, extras unlocked — the same effect the published "unlock everything" password advertises.

## 3. How to reproduce

1. Emulator: mGBA 0.10.5 under Xvfb (`DISPLAY=:315`, `SDL_AUDIODRIVER=dummy`), default keymap A=`x`, B=`z`, Start=`Return`, L=`a`, R=`s`, D-pad = arrows.
2. Boot → press Start at the Fox splash and again at the title → **MAIN MENU**.
3. Press Down ×5 → **Options** → A → move down once → **SET PASSWORD** → A.
4. The screen has eight slots. Left/Right/Up/Down select one of the 16 portraits (row-major index 0–15); A appends the selected portrait to the next slot; B deletes the last slot. When eight slots are filled, **press Start to submit**.
5. A valid code returns to the main menu and changes the save flags. An invalid code plays an error sound and leaves the screen up.
6. To inspect RAM without a GDB stub (port 2345 was occupied by another session), use mGBA's `-d` CLI debugger for reads/writes and `.ss1` savestate diffing: `python3 ss.py <state>` decompresses the `gbAs` PNG chunk to a 397,312-byte image with IWRAM at file offset `0x19000` and EWRAM at `0x21000` (§16.13 of the guide).

Codes tested (portrait indices, row-major):

| Code | Result |
|---|---|
| `[0,1,2,3,4,5,15,8]` | **accepted**, money 451,329, missions 4 |
| `[15,5,1,9,13,11,6,12]` | **accepted**, money 1,000,000, missions 10, all vehicles/locations |
| `[0,1,2,3,4,5,15,9]` | rejected (checksum 2) |
| `[0,1,2,3,4,5,14,8]` | rejected (checksum 1) |
| `[15,1,15,5,14,12,14,8]` | rejected (mission 11 out of range, checksums valid) |
| `[0,5,1,9,13,1,13,1]` | rejected (money 1,000,001 out of range, checksums valid) |
| `[0,1,2,3,4,5,6,7]` | rejected |

Screenshots (work dir `/tmp/opencode/simpsonsroadrage/`): `title_c.png`, `s2_c.png` (main menu), `s4_c.png` (options), `s5_c.png` (Set Password), `grid_zoom.png` (16-symbol alphabet), `getpw_c.png` (Get Password), `novel_ui_before_c.png` (novel code entered), `novel_ui_after_c.png` (return to main menu after acceptance).

## 4. Address map

| Item | Address | Notes |
|---|---|---|
| Password validator | `0x08034D0` (Thumb) | Returns `2` accepted, `0` rejected. Called indirectly via scene dispatch table `0x0820704C`, index 2 (`0x08034D1` with Thumb bit). |
| Validator caller / dispatcher | `0x0803361C` | Reads scene state byte at object+`0xD0`; jumps through `0x0820704C`. |
| Password input handler | `0x080331C0` | Reads keys from `0x03001D38`; A writes the selected symbol into the buffer; B deletes; Start sets state 2 (verified: read-watchpoint on the buffer fires exactly on Start). |
| f1 lookup helper | `0x08003F54` | `return s16(*(u16*)(0x081F5560 + (x & 0xFFE)))` |
| f2 lookup helper | `0x08003F6C` | `return s16(*(u16*)(0x081F4560 + (x & 0xFFE)))` |
| Scene object base (observed) | `0x03003970` | Password buffer = base + `0x6D9` (literal at `0x080335E4`). |
| Password length byte | `0x03004048` | Observed value 8 when full; cleared to 0 after acceptance. |
| **Password buffer** | `0x03004049` – `0x03004050` | Eight bytes, one symbol index (0–15) each. |
| Key table | `0x081F44C4` | Even bytes used: `6F B1 5F 05 AE 01` (literal pointer at `0x080335E8`). |
| f1 table | `0x081F5560` | 2048 signed 16-bit entries, byte-offset indexing with `& 0xFFE`. |
| f2 table | `0x081F4560` | ditto. |
| Money limit literal | `0x000F4240` | At `0x080335EC` (1,000,000). |
| State base literal | `0x03001C90` | At `0x080335F0`. |
| Save flags | `0x03001C90` vehicles (u32), `0x03001C94` money (u32), `0x03001CEC` locations (u8), `0x03001CED` missions (u8), `0x03001CF0` extras | Money and missions are written directly by the validator; vehicles/locations/extras are updated by the post-validation state application (`bl 0x08000B54` etc.). |
| ASCII debug scene-name bank | `0x08206D55` | Contains `Title`, `Main Menu`, `Set Password`, `Extra1`, `Extra2`, `Unlock`, `Ending`, `Game Credits` — scene labels, not codes. |
| Menu script string bank | `0x080B76A8` | `GET PASSWORD`, `SET PASSWORD`, `GAME DIFFICULTY`, `SOUND CHECK`, `EXTRAS`. |

Note the two important text encodings: the visible UI labels are ASCII at `0x080Bxxxx` (pointer table at `0x0802FCA0`), while the driver/character names in mission text live at `0x08205xxx`. The password screen itself has **no text alphabet** — its symbols are portraits, which is why a naive `strings`-only negative would be wrong (guide §11 "not all text is ASCII").

## 5. Algorithm

`validate(code)` where `code` is eight 4-bit symbols `b[0..7]` (observed/derived from the disassembly at `0x08034D0`):

```
# 1. copy the 8 bytes from [scene+0x6D9] into two stack buffers
# 2. checksum 1
c1 = (b0 + b1 + b2 + b3 + b4 + b5) & 0xF
if c1 != b6: return REJECT

# 3. checksum 2 (table driven, accumulated over i = 0..6, note b6 is c1)
acc = c1
for i in 0..6:
    r4 = s16(f1(b[i] + i)) + b[i] + s16(f2(b[i] - i))
    acc = (acc + r4) & 0xFFFFFFFF
if (acc & 0xF) != b7: return REJECT

# 4. decode payload with the 6-byte key (subtraction mod 16)
KEY = [0x6F, 0xB1, 0x5F, 0x05, 0xAE, 0x01]
d[i] = (b[i] - KEY[i]) & 0x0F          for i = 0..5

# 5. range checks
if d[5] > 10: return REJECT                 # mission count
money = d[0] | d[1]<<4 | d[2]<<8 | d[3]<<12 | d[4]<<16
if money > 1_000_000: return REJECT

# 6. apply
[0x03001C94] = money
[0x03001CED] = d[5]
save_game(); play_sound(0x3B)
return ACCEPT                                # 2
```

`f1(x) = *(int16*)(0x081F5560 + (x & 0xFFE))`, `f2(x) = *(int16*)(0x081F4560 + (x & 0xFFE))`. The `& 0xFFE` is a **byte** mask (index × 2); this is the single easiest detail to get wrong — see the bug I fixed during this analysis. `s16` is sign-extension of the loaded halfword; f2(0) = 4096, so its sign extension matters.

Encoding is the exact inverse: pick `(money, missions)` in range, compute `d[0..5]`, add the key mod 16 to get `b[0..5]`, then `b6 = sum(b[0..5]) & 15`, and `b7 = (sum(b[0..5]) + Σ f1(b[i]+i)+b[i]+f2(b[i]-i)) & 15`.

Faithful Python implementation: `/tmp/opencode/simpsonsroadrage/validator.py`.

## 6. Tables

**Password alphabet (16 portraits, row-major index):** the 2×8 grid on the Set Password screen. Visual identification (inferred from portrait art, lower confidence than the code):
`0` Homer, `1` Bart, `2` Lisa, `3` Maggie, `4` Marge, `5` Willy/Apu-like, `6` Krusty-like (red), `7` Snake-like, `8` Barney-like (blue), `9` Chief Wiggum (police hat), `10` Moe, `11` Frink, `12` Barney/Krusty-like, `13` Dr. Hibbert-like, `14` Otto-like, `15` Maggie/Barney-like. **The indices are observed; the names are inferred and should not be relied upon.** Published codes are stated in names, so a name→index table cannot be asserted from this evidence alone; the max-payload code `[15,5,1,9,13,11,6,12]` is the code that produces the advertised "unlock everything" state.

**Key table at `0x081F44C4`** (bytes; validator reads even offsets 0,2,4,6,8,10):

| i | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| key[i] | `0x6F` | `0xB1` | `0x5F` | `0x05` | `0xAE` | `0x01` |

**Save-state flags affected by an accepted password:**

| Address | Width | Before (fresh) | After novel code | After max code |
|---|---|---|---|---|
| `0x03001C90` | u32 | `0x1F` | `0x7FF` | `0xFFFF` |
| `0x03001C94` | u32 | `0` | `451329` | `1000000` |
| `0x03001CEC` | u8 | `1` | `0x1F` | `0x3F` |
| `0x03001CED` | u8 | `0` | `4` | `10` |
| `0x03001CF0` | byte field | `00 01 05 00` | `01 01 05 0A` | unlocked |

**Published codes (recon, treated as data):** GameFAQs, GameRevolution, cheatcc and the GBA walkthrough all list `Maggie, Willy, Bart, Chief Wiggum, Apu, Moe, Krusty, Barney` → unlock all cars/levels/bonuses, and `Bart, Bart, Lisa, Lisa, Marge, Marge, Barney, Barney` → all characters. The GameFAQs walkthrough's CodeBreaker codes (out of scope) use the same flag addresses and corroborate the flag map above. The many L+R button codes on those pages are explicitly GC/PS2/Xbox and are out of scope for this GBA SKU; none were found in this image.

## 6b. Enumeration

**Space definition.**
* Alphabet size 16 (portrait grid), code length exactly 8 → raw space 16^8 = **4,294,967,296** symbol strings.
* Layout: `b[0..5]` = payload (20-bit money + 4-bit mission count), `b[6]` = checksum 1, `b[7]` = checksum 2.
* Key subtraction is bijective mod 16; the two check bytes are *uniquely determined* by `b[0..5]`, so there are no aliases from unused bits.
* Payload range: money 0–1,000,000 (1,000,001 values) × missions 0–10 (11 values) = **11,000,011** accepted codes.
* Verified by exhaustive C enumeration over all 2^24 values of `b[0..5]` (`enumerate.c`): `accepted=11000011 money_fail=534325 mission_fail=5242880` (sum = 16,777,216). The rejection counts are the out-of-range payloads; no additional checksum failures exist because the check bytes are always recomputed.

**Novel code (not in any published list).** `[0,1,2,3,4,5,15,8]` — decoded payload money=451,329, missions=4. Entered with real keypresses (start from `[0,1,2,3,4,5,15,0]`: B, Down, A, Start) with the buffer verified as `[0,1,2,3,4,5,15,8]` immediately before Start. Result: screen returned to MAIN MENU, RAM `money=451329`, `missions=4`, `vehicles=0x7FF`, `locations=0x1F`, slot count cleared to 0. Screenshots `novel_ui_before_c.png` / `novel_ui_after_c.png`. A second accepted code `[15,5,1,9,13,11,6,12]` yields the maximum payload (money 1,000,000, missions 10, all unlocks) and is the likely numeric form of the published "unlock everything" password.

**Bounds proven by rejection (in-game, no state change):**

| Input | Checksums | Range | ROM result |
|---|---|---|---|
| `[0,1,2,3,4,5,15,9]` | checksum 2 wrong | in range | rejected |
| `[0,1,2,3,4,5,14,8]` | checksum 1 wrong | in range | rejected |
| `[15,1,15,5,14,12,14,8]` | both valid | mission = 11 > 10 | rejected |
| `[0,5,1,9,13,1,13,1]` | both valid | money = 1,000,001 > max | rejected |
| `[0,1,2,3,4,5,6,7]` | both wrong | — | rejected |

Each rejection left `money=0`, `missions=0`, `vehicles=0x1F`, `locations=0x01` and the eight password bytes intact on screen — i.e. a genuine in-game rejection, not a decoder disagreement.

**Button codes / hidden menus:** the published button sequences are for other platforms (§2). Static search of all 52,693 ASCII strings found no `DEBUG`, `SECRET`, `LEVEL SELECT` or cheat-related debug labels; the only similar strings are the scene names in `0x08206D55`. No button-mask sequence table was located, and every reachable menu screen was walked (title, main menu, Options, Set Password, Get Password, driver select). This is a bounded negative for *this GBA image*, not a claim about other SKUs.

## 7. Validation evidence

* **Observed:** every screen transition and key press above (screenshots on disk); password buffer contents read from uncompressed `.ss1` states; money/mission/flag values before and after acceptance; read-watchpoint on `0x03004049` firing exactly on Start.
* **Derived:** the validator algorithm, key table, lookup tables, payload layout and checksum formulas are direct disassembly of `0x08034D0`, `0x08003F54`, `0x08003F6C` and their literal pools; the accepted-code count is the C enumeration over the recovered model; the call path is the function pointer at `0x0820704C+8` and the caller at `0x0803361C`.
* **Inferred:** portrait→name assignments (visual only); that `[15,5,1,9,13,11,6,12]` is the numeric equivalent of the published "unlock everything" password (it produces the advertised state, but the published name list could not be mapped to indices with certainty); that the validator's `bl 0x08000B54` is a save routine (not separately exercised).

Confidence: high for the algorithm, address map, novel code and bounds; low for portrait names.

## 8. Unknowns

* Exact name→index mapping for the 16 portraits; the published name-based codes were therefore not re-entered verbatim. This does not affect the algorithm or the novel code.
* Whether an additional gated debug scene exists behind a save flag: scene names `Extra1/Extra2/Unlock/Ending/Game Credits` were seen in the debug label bank but not all were walked to completion.
* The exact semantics of the `0x03001CF0` extras byte field after each payload; only the before/after bytes were recorded.

## 9. Tooling

* mGBA 0.10.5 (`-3 -d`, CLI debugger over a detached FIFO/command-queue bridge `dbgbridge.py` because the GDB stub port 2345 was occupied by another session); Xvfb `:315`, openbox, SDL dummy audio; xdotool/scrot for input and screenshots.
* `ss.py` — decompress mGBA `.ss1` `gbAs` PNG chunk to raw RAM image (§16.13).
* `patchss.py`, `force.py` — patch password bytes / scene state in a savestate; `testcode.py` — automated accept/reject harness through the real UI.
* `validator.py` — Python reimplementation with `validate()` / `encode()`; `enumerate.c` — exhaustive 2^24 payload count.
* `scanptr.py`, `blscan.py` — 32-bit pointer and Thumb BL scanners; `arm-none-eabi-objdump -M force-thumb` for disassembly.
* All analysis artifacts are in `/tmp/opencode/simpsonsroadrage/`. No ROM bytes or copyrighted assets are reproduced in this report beyond short numeric table values and addresses.

## 10. Cleanup

All processes started for this job were stopped by PID: mGBA debugger bridge and its child, Xvfb `:315`, and openbox on `:315`. The generated `.sav` and `.ss1` files were removed from the ROM folder; no other agent's processes or displays were touched.
