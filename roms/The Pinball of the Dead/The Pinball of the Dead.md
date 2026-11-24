# The Pinball of the Dead (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/The Pinball of the Dead/The Pinball of the Dead.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| `file` | Game Boy Advance ROM image: "PINBALL DEAD" (APDE78, Rev.00) |
| Header title | `PINBALL DEAD` |
| Game code / maker | `APDE78` / `78` |
| Version / fixed byte | 0x00 / 0x96 |
| Entry word | `0xEA00002E` (stock GBA branch — no cracktro/trainer patch) |
| MD5 | `627b22d7e3c4dbce8191c7765c58e17a` |
| SHA-1 | `a685c3e88abe3a008fd2c721d75bbec14fbe0401` |
| SHA-256 | `7275aeee6b5fa6fd259d3fa1bf507c3554a7c6980b07552ed66a7d0904a9d850` |

## 2. Executive summary

This game has a **real, developer-intended password system** with two layers:

1. **Four hard-coded "developer shortcut" passwords**, each special-cased by `strcmp` before any
   algorithm runs. They unlock Sound Test, Movie Test, View Ending and Boss Mode. These strings
   do **not** satisfy the general checksum — they bypass it entirely.
2. **A general 13-symbol algorithmic password** over a 32-symbol alphabet with a 5-bit checksum,
   a 3-bit XOR-key selector and a 56-bit payload. This is a *save-data* password: it writes score,
   stage, mode, level and unlock state. The published `KJQV9LWB8!9HG` ("Final Challenge vs.
   Emperor") is a code of this second kind and is **not** stored as a literal anywhere in the ROM —
   it is a genuine algorithmic code.

Both the published list and a newly generated, unpublished code were accepted on the real title
screen and verified in RAM. Out-of-range-field and bad-checksum inputs were rejected with the
in-game `ERROR` message. Hidden menus behind OPTIONS+R were enumerated.

No GameShark / CodeBreaker / Action Replay codes were used or researched.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, scale `-3`.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold keys 80–120 ms; 45–70 ms moves one menu slot.
* Path: title → **CONTINUE** → **ENTER PASSWORD** → 13-character entry → **A** to submit.
* Input buffer is `0x0200C640` (13 chars + NUL). Confirmed by RAM diff: pressing **Right** moved the
  edit cursor one slot; **Up/Down** cycled the character at that slot; **B** cancelled, **A** submitted.
* On-screen keyboard Up-cycle (32 symbols, derived by 44 successive Up presses with live RAM reads):

  ```
  0 ! Z Y X W V T S R Q P N M L K J H G F D C B 9 8 7 6 5 4 3 2 1  (wrap)
  ```

  (Note: letters `A`, `E`, `I`, `O`, `U` do not exist in this alphabet.)
* A clean savestate at the password screen was at `/tmp/pinballdead/pw.ss1`; starting
  `mgba -3 -g -t pw.ss1 <rom>` skips all intro animation.
* Codes entered with the real on-screen keyboard (no memory writes): `D0NTN33DM0N3Y` →
  `BOSS MODE UNLOCKED`. Other codes were submitted by writing the 14-byte buffer with the GDB stub
  and pressing **A**, which exercises the game's own validator and entry screen unchanged.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08020264` | Password **generator** (save data → 13 chars) | Derived from disassembly |
| `0x080203CC` | Password **validator** (13 chars → save data); returns 1/2/3/4 for the four literals, 0 for accepted algorithmic codes, nonzero on reject | Derived + live breakpoints |
| `0x08020508` | checksum comparison (`r4`=stored, `r6`=computed) | Observed breakpoint |
| `0x08020588` → `0x0802058C` | call to range check `0x0801F174`; `r0`=0 accepted | Observed breakpoint |
| `0x0801F174` | range/semantic check on decoded struct | Derived + observed |
| `0x0801F068` | applies decoded password to game save state | Derived |
| `0x0801F1D0` | builds save struct for the generator | Derived |
| `0x080230A4` | 64-bit shift-left helper (`u64 << n`) | Derived |
| `0x080231AC` | 64-bit shift-right helper, also used to extract nibbles for the checksum | Derived |
| `0x087B2800` | 32-byte alphabet: `21C03FMG7H5KL8NDPYQ9RS4T!BVWJX6Z` | Dumped |
| `0x087B2820` | 8 XOR keys × 8 bytes (little-endian u32 pairs) | Dumped |
| `0x0802484C`,`5C`,`6C`,`7C` | the four literal password strings | Dumped |
| `0x0200C640` | 13-character input buffer (+ NUL) | Observed RAM diff / GDB |
| `0x02002EBC/BE/BF/C0` | sound/movie/ending unlock flag bytes (and `0x02002EBD` boss) | Derived from caller `0x0801FAE6`..`0x0801FC16` |
| `0x0200C568/A/C/E` | second copy of those unlock flags | Derived |
| `0x02002EAC` | decoded password score (u32) | Observed: novel code wrote `0x075BCD15` |

## 5. Algorithm

### 5.1 Four hard-coded shortcuts (checked first, in this order)

```
strcmp(input, "!0P3NSNDT3ST!") == 0 -> return 1  (Sound Test unlocked)
strcmp(input, "M0V13PL3S3NT!") == 0 -> return 2  (Movie Test unlocked)
strcmp(input, "SH0WM33ND1NG!") == 0 -> return 3  (View Ending unlocked)
strcmp(input, "D0NTN33DM0N3Y") == 0 -> return 4  (Boss Mode unlocked)
```

These four strings are at `0x0802484C`..`0x0802487C` and are referenced by literal pools at
`0x080203E8`..`0x08020424`. Their callers (`0x0801FAE6`, `0x0801FB36`, `0x0801FB82`,
`0x0801FBCE`) set the flag bytes listed in §4 and print the corresponding `... UNLOCKED` string.
They are *not* required to pass the checksum.

### 5.2 General password decoder (`0x080203CC`)

```
ALPHA = "21C03FMG7H5KL8NDPYQ9RS4T!BVWJX6Z"      # 32 symbols, index 0..31

# 1. parse 13 characters, 5 bits each, LSB first
v = 0
for i, ch in enumerate(input[0:13]):
    idx = ALPHA.index(ch)          # char not in ALPHA -> reject
    v |= idx << (5*i)

stored_check = (v >> 59) & 31
payload      = v & 0x07FFFFFFFFFFFFFF        # clear bits 59..63 (the check)

# 2. checksum: 15 nibbles of the 59-bit payload, mod 32
check = sum((payload >> (4*i)) & 0xF for i in range(15)) & 31
if check != stored_check: reject

# 3. selector = top 3 bits of payload; choose XOR key
sel = (payload >> 56) & 7
key_lo, key_hi = KEYS[sel]        # key_hi &= 0xFFFFFF
lo = (payload & 0xFFFFFFFF) ^ key_lo
hi = ((payload >> 32) & 0xFFFFFF) ^ key_hi

# 4. reconstruct the 8-byte decoded save struct
word0 = ((hi & 0xFFFFFF) << 8) | (lo >> 24)
S[0:4] = word0 as little-endian u32
S[4]   = lo & 0xFF
S[5]   = (lo >> 8) & 0xFF
S[6]   = (lo >> 16) & 0xFF
S[7]   = 0

# 5. semantic range check at 0x0801F174
if ((S[4] >> 4) & 7) > 5:                 reject
if (((S[5] & 7) - 4) & 0xFF) <= 2:        reject      # S[5]&7 must be 0,1,2,3 or 7
if ((S[6] >> 5) & 3) == 3:                reject
if word0 > 0x3B9AC9FF:                    reject
# accepted: apply S[] via 0x0801F068, return 0
```

The encoder is the exact inverse: build `S[]`, form `lo`/`hi` as in step 4, XOR with `KEYS[sel]`,
OR `sel << 56`, compute the nibble checksum, then emit 13 symbols `ALPHA[(v>>(5*i))&31]`.
Full reimplementation: `/tmp/pinballdead/codec.py`.

Note the compiler quirk at `0x08020544`: one byte of the output struct is preserved from the saved
`r5` register (the caller's password length, normally 0), so `S[7]` is effectively always zero.

## 6. Tables

**Published codes (all verified in ROM):**

| Code | Effect | Kind |
|---|---|---|
| `!0P3NSNDT3ST!` | Sound Test unlocked | hard-coded, return 1 |
| `M0V13PL3S3NT!` | Movie Test unlocked | hard-coded, return 2 |
| `SH0WM33ND1NG!` | View Ending unlocked | hard-coded, return 3 |
| `D0NTN33DM0N3Y` | Boss Mode unlocked | hard-coded, return 4 |
| `KJQV9LWB8!9HG` | Final Challenge vs. Emperor — loads a CEMETERY / CHALLENGE save | algorithmic (not a ROM literal) |

Variants seen on the web (`m0v13pl3s3nt!`, `0P3NSNDT3ST!`, `D0NTN33DM0N3Y` without the leading
`!`) are case/transcription variants: the alphabet has no lowercase letters, so the game's own
strings are the authoritative spellings. `0P3NSNDT3ST!` (missing the leading `!`) is **12** chars
and would be rejected as-is.

**XOR keys** (`0x087B2820`, u32 little-endian pairs, high word masked to 24 bits on use):

```
sel 0: ef cd ab 89 67 45 23 01
sel 1: 54 ee 2d 44 b8 6f c5 1a
sel 2: 4c bf 5d 1a 90 6c 5f ad
sel 3: 32 ef d6 c9 87 bf a6 54
sel 4: 5a 4b 6d 3f 2e 65 cd b9
sel 5: a8 65 ff 1d 32 54 db fe
sel 6: d1 e6 f7 a5 3d 98 f6 cd
sel 7: c4 0a e1 87 fd ad 56 9d
```

**Hidden menu:** OPTIONS + **R** reveals `SOUND TEST NO %03d`, `MOVIE TEST NO %00d`, `VIEW ENDING`
(three entries). Boss Mode is not in that menu; it appears under GAME START once unlocked.
The R gate is `held == KEY_R` with the UI hint `R →` drawn at the top right of OPTIONS.

## 6b. Enumeration

**Space definition**

* Alphabet: 32 symbols (`21C03FMG7H5KL8NDPYQ9RS4T!BVWJX6Z`), length exactly 13.
* Raw input space: `32^13 = 36,893,488,147,419,103,232` (~3.7 × 10^19) strings.
* Checksum: 5 bits (sum of 15 nibbles mod 32) → `32^12 ≈ 1.15 × 10^18` checksum-valid strings.
* Of those, 3 bits select one of 8 XOR keys, leaving a 56-bit payload; the semantic range check
  further restricts `S[4]` bits 4–6 (≤5), `S[5]` bits 0–2 (∈ {0,1,2,3,7}), `S[6]` bits 5–6 (≠3)
  and score ≤ 999,999,999.
* Plus the four hard-coded bypass codes, which need not pass any of the above.

**Novel accepted code (absent from every published list)**

```
1QWTQ7SNRYP0K
```

Generated from a chosen save struct `S = 15 cd 5b 07 15 00 06 00` (score 123,456,789,
mode/stage/level fields set), selector 1. It does not appear on GameFAQs, SuperCheats, TCRF,
Neoseeker or any other published list (all of which use only the five codes in §6).

Observed in mGBA: accepted on the real ENTER PASSWORD screen → started a **CHALLENGE MODE** game on
**WONDERING**. RAM readback: `0x02002EAC = 0x075BCD15` = **123456789**, exactly the minted score.
Screenshot: `/tmp/pinballdead/novel_after.png`.

The published algorithmic code `KJQV9LWB8!9HG` was also accepted in the same harness, starting
**CHALLENGE MODE / CEMETERY** (screenshot `/tmp/pinballdead/kjqv2.png`); decoder output
for it is `S = e6 e0 68 02 d1 00 50 00`, score 40,427,750.

**Bounds proven by rejection (all on the real screen, `ERROR` displayed)**

| Input | Change | Result |
|---|---|---|
| `1QWTQ7SNRYP00` | last symbol replaced → wrong 5-bit checksum | `ERROR`, no flags/score written |
| `1VVTQ7SNRYP9H` | same payload but `S[5]&7 = 5` (forbidden by `0x0801F174`) | `ERROR`, checksum verified correct at breakpoint `0x08020508` (`r4 = r6 = 19`) |
| four hard-coded strings | intentionally fail the nibble checksum | accepted anyway — proves the special-case bypass |

Counts: 4 accepted literals (all four verified in ROM and via flag writes in-game) + a checksum-
filtered 32^12-space algorithmic set; 2 in-game rejections isolating the checksum layer and the
semantic-range layer separately.

## 7. Validation evidence

* **Observed**: mGBA screenshots of every screen walked — title, CONTINUE/DATA LOAD, ENTER PASSWORD,
  OPTIONS (+R hidden menu), RANKING, TUTORIAL, in-game pause, gameplay, movie test, unlock banners.
  `D0NTN33DM0N3Y` was typed with real key events and produced `BOSS MODE UNLOCKED`.
  GDB breakpoints at `0x080203CC`, `0x08020508`, `0x0802058C` confirmed checksum match and
  range-check result for both accepted and rejected codes. RAM reads confirmed the flag bytes and
  the minted score.
* **Derived**: the full codec (§5), key table, alphabet, helper functions, caller return-value map,
  and the fact that the four literal codes bypass the checksum.
* **Inferred**: the semantic names of the bit fields (mode/stage/level) are inferred from how
  `0x0801F068` writes them into the save structure; the numeric payloads and ranges are proven.
  The exact audiovisual content of SOUND TEST entries was not observable with `SDL_AUDIODRIVER=dummy`.

## 8. Unknowns

* Exact player-facing names of every bit field in `S[4]`–`S[6]` beyond their observed effects
  (score, mode, stage, level, unlock bits).
* Whether `S[7]` can be nonzero when reached through a different caller (the only writer path keeps
  it zero).
* The full contents of the movie/sound test banks (not needed for the cheat question).

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for the validator,
  generator, helpers and callers.
* `strings -t x`, `grep -abo`, `xxd` for recon.
* Custom scripts in `/tmp/pinballdead/`: `scan.py` (pointer/BL scans), `codec.py`
  (encoder/decoder), `typer.py` (real keyboard entry), `submit.py`, `test_one.py` (GDB-assisted
  submission + RAM evidence), `probe_keys.sh` (UI alphabet discovery).
* mGBA 0.10.5 with GDB stub on port 2345; gdb-multiarch; Xvfb `:317` + openbox; xdotool; scrot.
* No ROM or extracted assets are redistributed; only addresses, hashes, algorithms and findings
  are published.
