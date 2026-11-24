# The Muppets: On With the Show! (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Muppets: On With the Show!.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| `file` | Game Boy Advance ROM image: "MUPPETS SHOW" (AZME6S, Rev.00) |
| Header title | `MUPPETS SHOW` |
| Game code | `AZME` |
| Maker | `6S` |
| Revision / version | 0x00 / 0x00 |
| Header checksum | `0x0000` (rebuilt-header artifact; complement byte `0x00`) |
| Fixed `0x96` | present at `0xB2` |
| Entry word | `0xEA1F8D3E` → branches to `0x0807E3500` (EURASIA **scene cracktro**, not stock `0xEA00002E`). The stock crt0 at `0x080000C0` is intact; the cracktro hands off to it after a keypress. |
| MD5 | `89a2181c55a3ca003f39478d8c58214f` |
| SHA-1 | `8c874f451819fe60f899f12c52c68c2246a5659b` |
| SHA-256 | `f10860e21e1ff1e400e8138d5e4d99c7af3a673b1df779ddd313564bbe28420f` |

The boot splash is a **EURASIA cracktro** (CRC-bandit style scene intro) that loops until any key is pressed, then releases to the retail game. This is a scene artifact, not an in-game cheat; all findings below are in the untouched retail code region.

## 2. Executive summary

The game has a genuine **5-symbol password system** reached from the title menu's **continue** entry. All 9 published passwords were verified against the ROM and the emulator. The validator at `0x080013E0` is fully algorithmic: it converts 5 lowercase ASCII characters to 32-symbol alphabet indices, checks one linear relation plus two 5-bit modular-sum checks, then the apply routine at `0x0801484` writes four decoded fields into game globals. There is **no plaintext code table** — every literal search for the published codes failed.

The accepted space is exactly **4,098 of 33,554,432** inputs: 4,096 algorithmic codes (bijective with the 4×8×4×32 field space) plus **two wholly undocumented hardcoded bypass strings**, `14st1` and `tdktv`, stored at `0x08551730`/`0x08551738`. Neither appears in any published cheat list. Both were entered on the real screen and produced unique in-game effects (BONUS 2 unlock; Story Mode restart).

Novel algorithmic codes were minted from the field model and confirmed in-game: `l978d` launches an unadvertised **bonus minigame** (f1=6, beyond the published 0–5), and `dljtv` starts Story Mode at the Swedish Chef segment with an unadvertised mode/bonus combination. Bounds were proven by rejection: bad checksum and failed first check both show "BAD PASSWORD" with no global writes, while f1=7 is checksum-valid but crashes at `0xF939F938` — a distinct semantic-range layer.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb, `SDL_AUDIODRIVER=dummy`, display `:316`, `-3` scaling.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold 90–150 ms; keys repeat if held longer.
* Boot path: press any key to skip the EURASIA cracktro → legal/splash screens (several `Return`) → difficulty select → `B` → title menu → Down once → `A` on **continue**.
* The password screen is a 5-slot display above an 8×4 on-screen keyboard plus a backspace key. **The validator runs automatically on entry of the 5th character** — there is no separate ACCEPT key. Valid codes return to the title menu or start a game; invalid codes show "BAD PASSWORD" and clear the slots.
* Input is normalised to lowercase; case does not matter. The on-screen glyphs are mixed-case but the underlying string is lowercase.
* Savestate `Shift+F4` / load `F4` used for repeatable before/after RAM evidence.
* Screenshots and all scripts were in `/tmp/muppetsshow/work/`; key frames: `s7.png` (entry screen), `tdktv_after0.png`, `14st1_after0.png`, `l978d_play.png`, `dljtv_after1.png`, `rejcheck3_after0.png`, `rejcheck1_after0.png`.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Entry word `0xEA1F8D3E` → cracktro at `0x0807E3500` | Observed (disassembly + emulator) |
| `0x080000C0` | Intact stock ARM crt0 | Derived |
| `0x080013E0` | **Password validator** (`push {r4-r7,lr}`; returns 1=accept, 0=reject) | Derived + dynamic watchpoint |
| `0x08001484` | **Password apply routine** (writes decoded fields to globals) | Derived |
| `0x08000210` | Thunk to the string-compare helper used for the two bypass strings | Derived |
| `0x080079B8` | Password-screen input handler (keypad decode + char entry) | Derived |
| `0x08007B1A` | `ldr r1,[pc,#48]` → literal `0x08056C6B` (keyboard char table) | Derived |
| `0x08007B26` | `strb r0,[r2]` writes selected char into buffer | Observed (write watchpoint) |
| `0x08007B34` | `bl 0x080013E0` with `r1 = &buffer[5]` | Derived |
| `0x08007B42` | `bl 0x08001484` on accept | Derived |
| `0x08056C6B` | On-screen keyboard table, 2 bytes per cell, index `(row*8+col)*2` | Derived |
| `0x08551730` | Bypass string `"14st1\0"` | Observed (bytes `31 34 73 74 31 00`) |
| `0x08551738` | Bypass string `"tdktv\0"` | Observed (bytes `74 64 6b 74 76 00`) |
| `0x08551740` | 32-byte alphabet string `bcdfghjklmnpqrstvwxyz0123456789?` | Observed |
| IWRAM `0x03007C88` | Input length counter (0–5) | Observed (savestate diff) |
| IWRAM `0x03007C98` | 5-byte input buffer, lowercase ASCII, `'.'` when empty | Observed (savestate diff + watchpoint) |
| IWRAM `0x03001464` | Global `f0` (mode) written by apply routine | Observed (savestate diff) |
| IWRAM `0x03001468` | Global `f2` (max level) written by apply routine | Observed (savestate diff) |
| IWRAM `0x0300146C` | Global `f3` (bonus flags) written by apply routine | Observed (savestate diff) |
| game state `+0x08` | Global `f1` (minigame/level index) written by apply routine | Derived |

## 5. Algorithm

Reimplementation precise enough to enumerate offline (`work/pw.py`, `work/brute.c`):

```
validate(input[5]):
    if input == "14st1" or input == "tdktv": return ACCEPT     # strcmp bypass, before any conversion
    i[k] = index of lowercase(input[k]) in ALPHA            # linear search, 0..31
    if (i1 & 3) != (i0 >> 2):                 return REJECT  # check 1
    S = i0 + i1 + i2                                        # UNMASKED integer sum
    if ((~S) & 31) != i3:                     return REJECT  # check 2
    if ( S & 31) != i4:                       return REJECT  # check 3
    return ACCEPT

apply(input[5]):
    i[k] = alphabet index as above
    f0 = i0 & 3                          -> IWRAM 0x03001464
    f1 = i1 & 7                          -> state+0x08 (minigame/level index)
    f2 = i2 & 3                          -> IWRAM 0x03001468 (only if larger)
    f3 = ((i1 >> 3) & 3) | (((i2 >> 2) & 7) << 2)
                                         -> IWRAM 0x0300146C (bonus flags)
```

Notes:
* `~S & 31` is the 5-bit bitwise complement of the low 5 bits of `S`; it equals `31 - (S & 31)` here because `S&31` occupies only the low five bits. Check 2 and check 3 are therefore complementary halves of the same sum, not independent checksums.
* Check 1 constrains `i0>>2 == i1&3`, so `i0` is limited to 0–15. Combined with the two sum checks this leaves exactly 4,096 tuples.
* The encoder is a bijection: for any `(f0,f1,f2,f3)` in `4×8×4×32`, `i0=(f1&3)<<2|f0`, `i1=f1|((f3&3)<<3)`, `i2=f2|(((f3>>2)&7)<<2)`, then `i3=~(i0+i1+i2)&31`, `i4=(i0+i1+i2)&31`.
* The two bypass strings intentionally **fail** the arithmetic (e.g. `14st1` → i0>>2=5, i1&3=1) yet are accepted — strong evidence they are developer backdoors, not transcription errors.

## 6. Tables

**Alphabet** (`0x08551740`, index = position):

```
 0:b  1:c  2:d  3:f  4:g  5:h  6:j  7:k  8:l  9:m 10:n 11:p
12:q 13:r 14:s 15:t 16:v 17:w 18:x 19:y 20:z 21:0 22:1 23:2
24:3 25:4 26:5 27:6 28:7 29:8 30:9 31:?
```

Published codes decoded with the recovered field model (all verified in ROM and in the emulator):

| Code | Published effect | f0 | f1 | f2 | f3 | i (alphabet indices) |
|---|---|---:|---:|---:|---:|---|
| `bLGyq` | Level 2 — Swedish Chef Cooking Hour | 0 | 0 | 0 | 5 | 0,8,4,19,12 |
| `GWLd8` | Level 3 — Muppet Labs | 0 | 1 | 0 | 10 | 4,17,8,2,29 |
| `L5qWS` | Level 4 — The Great Gonzo | 0 | 2 | 0 | 15 | 8,26,12,17,14 |
| `qFZ7F` | Level 5 — Jurassic Pork | 0 | 3 | 0 | 20 | 12,3,20,28,3 |
| `b7Ztv` | Level 6 — Electric Mayhem | 0 | 4 | 0 | 23 | 0,28,20,15,16 |
| `GH75H` | Level 7 — Rock With The Band | 0 | 5 | 0 | 28 | 4,5,28,26,5 |
| `G07n0` | Medium difficulty | 0 | 5 | 0 | 30 | 4,21,28,10,21 |
| `H08L2` | Hard difficulty | 1 | 5 | 1 | 30 | 5,21,29,8,23 |
| `J09J4` | All mini-games | 2 | 5 | 2 | 30 | 6,21,30,6,25 |

Interpretation (confidence: **inferred** from apply-routine writes plus observed screen effects): `f1` selects a minigame/level (0–5 published, 6 = bonus game); `f0`/`f2` behave as mode and max-level selectors; `f3` is a bonus-flag mask written to `0x0300146C`.

Undocumented hardcoded strings (not on any published list):

| Code | ROM address | Observed effect |
|---|---|---|
| `14st1` | `0x08551730` | "UNLOCKED: \* BONUS 2" screen, star count 15; globals `0x03001468=3`, `0x0300146C=0x0F` |
| `tdktv` | `0x08551738` | Starts Story Mode from level 1 (Kermit intro); bonus flags cleared |

## 6b. Enumeration

**Space definition.** Alphabet size 32, length exactly 5 → `32^5 = 33,554,432` representable strings. The validator's structural space is `4,096` algorithmic codes, bijective with the decoded field tuple `(f0∈0..3, f1∈0..7, f2∈0..3, f3∈0..31)`. Two extra strings are accepted by a `strcmp` bypass ahead of the arithmetic. **Total accepted inputs = 4,098** (1 in 8,188.6).

**Closed-set proof.** `work/brute.c` runs the exact recovered validator over all 33,554,432 five-symbol strings: 4,096 algorithmic + 2 special = **4,098 accepted**. This is derived from the ROM disassembly, not inferred from the published list. The Python model agrees with all 11 known codes, all 6 minted/novel inputs tested, and every rejection tested.

**Novel codes generated and confirmed in-game** (none appear on GameFAQs, Neoseeker, Cheathappens, cheatingdome, games-cheats.org, or absolutcheats):

| Code | Fields | In-game proof | RAM evidence |
|---|---|---|---|
| `14st1` | bypass | Screenshot `14st1_after0.png`: "UNLOCKED: \* BONUS 2", 15 stars | `0x03001468: 0→3`, `0x0300146C: 0→0x0F` |
| `tdktv` | bypass | Screenshot `tdktv_after0.png`: Story Mode level-1 Kermit dialogue | bonus flags cleared; state object +8 = 0 |
| `l978d` | (0,6,0,31) | Screenshots `l978d_after1.png` / `l978d_play.png`: "READY" then "BONUS RESULT" with TIME 00:02 and 1 star — an unadvertised **bonus minigame** (f1=6 is outside the published 0–5) | `0x0300146C: 0→0x1F` |
| `dljtv` | (2,0,2,5) | Screenshot `dljtv_after1.png`: Story Mode Swedish Chef segment (Rizzo "I'm hungry") with an unadvertised mode/bonus combination | `0x03001464: 0→2`, `0x03001468: 0→2`, `0x0300146C: 0→5` |

**Bounds proven by rejection:**

| Input | Why invalid | Observed result |
|---|---|---|
| `J09J5` | `S&31 = 25`, fifth index = 26 — bad check 3 | `rejcheck3_after0.png`: "BAD PASSWORD", slots cleared, all three globals stay 0 |
| `L09J4` | `i1&3 = 1`, `i0>>2 = 2` — bad check 1 | `rejcheck1_after0.png`: "BAD PASSWORD", slots cleared, globals stay 0 |
| `bCdFG` | random non-code | "BAD PASSWORD" (observed during recon) |
| `t??xr` | (3,7,3,31) — passes all three checks but f1=7 | Checksum accepted, then game jumps to `0xF939F938` / illegal opcode `0x0000b710` ("The game crashed!") |
| `q?73k` | (0,7,0,31), isolating f1=7 | Same crash at `0xF939F938` — proves the crash is the f1 field, not f0=3 |
| `fbb7f` | (3,0,0,0), isolating f0=3 | **Accepted**, starts Swedish Chef; f0=3 is not a rejection |
| `bbf7f` | (0,0,3,0), isolating f2=3 | **Accepted**; `0x03001468: 0→3`, so f2=3 is in range |

The f1=7 crash is a semantic-range layer *after* checksum acceptance (guide §16.5): a checksum-valid code can still be invalid. f0=3 and f2=3 are valid, so the only proven semantic bound is `f1 ≤ 6`.

## 7. Validation evidence

* **Observed**: password screen and on-screen alphabet (`s7.png`); automatic validation on 5th character; "BAD PASSWORD" for both rejection classes; all four novel-code screens listed above; crash message for f1=7; input buffer contents from savestate diff (`"."`→`"bcdf"`) and mGBA `-d` write watchpoint at `0x03007C98` firing with `r0=0x67`, `PC=0x08007B2A`.
* **Derived**: validator and apply-routine disassembly; field extraction and sum/complement checks; closed-set count from `work/brute.c`; alphabet and bypass-string bytes; all address-map entries.
* **Inferred**: field *names* (mode / max level / bonus flags) and the exact gameplay meaning of f3; the cracktro's handoff mechanism; that `tdktv` is a "start new Story Mode" developer shortcut rather than a player-facing feature.

## 8. Unknowns

* The precise semantic role of `f0` values 1/2/3 and of `f3` bits beyond what was observed (bonus flags are inferred from the `14st1` unlock screen and the `0x0300146C` writes). A full per-bit effect map would require playing each of the 2,048 `(f0,f3)` combinations.
* Why `f1=7` crashes at `0xF939F938` (likely an out-of-bounds minigame table index) — the exact table and bounds check were not isolated.
* Whether the second validator call inside `0x0801484` (at `0x0801514`) represents a second password format used by the game-over/results screen; only the title-menu entry path was exercised.
* The cracktro was not removed from a copy; its code at `0x0807E3500` was not disassembled beyond confirming handoff. The retail game region used was verified intact by the validator disassembly and live tests.

## 9. Tooling

All scripts in `/tmp/muppetsshow/work/`:

* `xref.py` — 32-bit pointer and Thumb LDR-literal xref scans (returned zero hits for the text strings, proving the algorithmic path).
* `tables.py` — alphabet copies, index-table and packed-code searches (zero stored tables/codes).
* `ssdiff.py` — mGBA `.ssN` PNG `gbAs`-chunk zlib extractor and RAM differ; located the input buffer and all decoded globals.
* `ptyctl.py`, `watchbuf.py`, `watchbuf2.py` — mGBA `-d` pty debugger console driver; `watch/w 0x03007C98` caught the input writer at `0x08007B2A` with `LR=0x080079FF`.
* `enter_code.py` — drives the on-screen keyboard from a 5-character code.
* `pw.py` — Python validator/decoder/encoder and published-code checks.
* `brute.c` — exhaustive C enumeration of the 33.5M-input space.
* `testcode.py` — enters a code, captures before/after screenshots and savestates, prints changed globals.

Installed tools used: `mgba` 0.10.5 (`/usr/local/bin/mgba`), `gdb-multiarch` (stub proved unreliable, replaced with `-d`), `arm-none-eabi-objdump`, `xdotool`, `scrot`, `Xvfb`, `openbox`. No ROM or copyrighted assets are redistributed; only addresses, hashes, algorithms, and locally captured screenshots are reported.
