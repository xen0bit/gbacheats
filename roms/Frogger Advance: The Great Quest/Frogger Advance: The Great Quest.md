# Frogger Advance: The Great Quest (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Frogger Advance: The Great Quest/Frogger Advance: The Great Quest.gba` |
| Size | 8,388,608 bytes (`0x800000`, 64 Mbit) |
| Header title | `FROGQST` (bytes at `0xA0`: `46 52 4F 47 51 53 54 00 00 00 00 00`) |
| Game code / maker | `AFQE` / `A4` (USA, revision 0) |
| Version / complement / checksum | `0x00` / `0x99` / `0x0000` |
| Entry word | `0xEA1F40FE` → branch target `0x0807D400` (scene cracktro, see below) |
| MD5 | `8c214a9cbe78ab19a34d8ab48dd956c1` |
| SHA-1 | `91bbc66b902343026120b743c396e97b04c1e7bf` |
| SHA-256 | `ab24f51c93eb92a83f817ab49024a221fd6337a18a15546d59238a15b72a22f6` |

A full 156-byte Nintendo-logo scan finds **exactly one** header at file `0x0`: no multiboot
image, no appended trainer. There is, however, a **scene cracktro**: the entry branch
lands at `0x0807D400`, and `MODE7 PRESENTS / FROM KONAMI / GBA/USA/64MBS` is at file
`0x7D3EFA`. It inserts a ~30 s splash before handing off to the stock game; it is a
release artifact, not an in-game cheat. The `0x0000` header checksum is the usual rebuilt-
header artifact (complement `0x99` is intact).

Developer messages noted by TCRF are present at file `0x3185A` onwards (`i missed the
george forman grill, …`), and the ROM contains the credits block at `0x3113C`.

## 2. Executive summary

This game has a **genuine, developer-intended password system**, with three independent
accept paths on the five-symbol Password screen:

1. **A plaintext table of four codes** at `0x08031075`: `VV518`, `TRVCK`, `G0PHR`,
   `BVNNY`. All four select the *Race to Be King* challenge (the same instructions screen
   is shown for each; `VV518` is advertised in-game at `0x301DC`). Verified in emulator.
2. **An undocumented input `T0B0R`** (`0x0802BA32`–`0x0802BA84`) which opens a hidden
   developer-message slideshow ("I MISSED THE GEORGE FORMAN GRILL, I AM NOT MISSING THE
   CUPCAKES!"), matching the TCRF developer messages. **Confirmed in emulator; it appears
   in no published code list.**
3. **A full algorithmic password system**: 5 symbols × 32-value alphabet, a 20-bit
   base-9 payload (4 digits + a level 0–99), and a 5-bit checksum. The validator at
   `0x0802177C` was reimplemented bit-for-bit, cross-checked against the ROM's own
   validator called as a debugger oracle (guide §16.19), and used to mint novel codes.

**Novel code `59GDF`** (level 42, digits `[8,4,0,3]`) was generated offline, accepted by
the ROM oracle, typed into the real Password screen, and RAM-verified: game state
`0x02000024+0x04 = 0x2A` (42), flags `+0x20 = 0x07`; the in-game pause screen then
regenerated the password `59GDF`, proving the encode/decode roundtrip. Bounds were proven
by rejection of a wrong checksum (`N9GDF`), an out-of-range level (`FKPVM`, level 100),
and sentinel values in the first three digit fields (`H28XY`, `44GXY`, `RPGDY`) while the
fourth digit *may* be the sentinel (`3SGDF` accepted).

No GameShark/CodeBreaker/memory-edit codes were used or reported.

## 3. How to reproduce

* Emulator: mGBA (SDL), `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
* The shipped ROM boots into the MODE7 cracktro; press A / Start several times (~30 s)
  to reach the retail intro, skip it with A, then `Start` on the title screen.
* Main menu entries: **Start / Password / Options**. Options has exactly two settings
  (Sound FX, Music). Password shows five slot selectors; `Left/Right` change slot,
  `Up/Down` change the symbol (wraps modulo 32), `A` = ACCEPT, `B` = BACK.
* Enter a code and press A. To revisit, a savestate at the Password screen is essential.
* Typing `VV518` (or `TRVCK`, `G0PHR`, `BVNNY`) shows the Race to Be King instructions.
* Typing `T0B0R` shows the hidden developer-message slideshow.
* Typing `59GDF` starts level 42; pause (`Start`) shows `PASSWORD: 59GDF`.
* Other reachable screens walked: title, main menu, Options, Password, Race-to-Be-King
  instructions, in-game HUD, PAUSED (Start; shows level/chapter/gems/password), Backpack
  (`Select` in game → Map Menu / Options / Quit Game), Maps (map viewer), and the intro/
  ending cutscenes. All visible text was found as plain ASCII in the ROM's text bank
  (`0x2FF7C`–`0x30594`), so no tile-indexed font bank had to be inferred for the UI labels.

## 4. Address map

All addresses are ROM (`0x08……`) unless noted; file offset = address − `0x08000000`.

| Address | Meaning |
|---|---|
| `0x08000000` | Header; entry branch to cracktro `0x0807D400` |
| `0x08031054` | 32-symbol password alphabet: `TVWXYZ0123456789-BCDFGHJKLMNPQRS` (+NUL) |
| `0x08031075` | Plaintext code table, 6-byte stride: `VV518`, `TRVCK`, `G0PHR`, `BVNNY` |
| `0x0802B9E4` | ACCEPT handler: table compare loop over the four codes (via alphabet→ASCII) |
| `0x0802BA32` | Hidden `T0B0R` check (expects ASCII glyphs `T 0 B 0 R`) |
| `0x0802BAA6` | Call to algorithmic validator with `r0 = 0x030018D8` |
| `0x0802177C` | **Validator** (Thumb): 5 bytes in `r0`, returns `1` accept / `0` reject |
| `0x080216F8` | **Generator** (Thumb): builds 5 chars from state level/digits/check |
| `0x08027638` | `aeabi_umod` helper (used with divisor 9) |
| `0x08023258` | `aeabi_uidiv` helper (used with divisor 9) |
| `0x0802FF7C` | Text bank (ASCII UI strings) |
| `0x08030A30` | Secondary 45-char lowercase alphabet (name/input glyph table, not the password alphabet) |
| `0x08030A84` | 70-char mixed-case alphabet (font/input glyph table) |
| `0x030018D4` | Selected slot index (u8) |
| `0x030018D8` | Five password slot bytes (indices 0..31) |
| `0x03001870` | Number of leading digits checked = **3** (u32) |
| `0x03001874` | Four u32 digits, MSB-first |
| `0x03001884` | Generator output buffer (5 glyph bytes) |
| `0x03001818` | Pointer to game-state struct; `+0x04` = level, `+0x20` = unlock flags |

## 5. Algorithm

Alphabet `A = "TVWXYZ0123456789-BCDFGHJKLMNPQRS"`, index `k = A[c]` (0..31; 16 = `'-'` = blank).
Input is exactly five symbols; the validator reads the slot bytes in order 4,3,2,1,0.

```
# raw values
n[k] = index(slot[k]) & 0xF          # low nibble
b[k] = (index(slot[k]) >> 4) & 1     # high bit

# payload and check word
payload = (n4<<16) | (n3<<12) | (n2<<8) | (n1<<4) | n0    # 20-bit
check   = (b4<<4) | (b3<<3) | (b2<<2) | (b1<<1) | b0       # 5-bit

# base-9 decomposition, least-significant first
v = payload
d_lsb = []
repeat 4 times:
    d_lsb.append(8 - (v % 9))
    v = v // 9
level = v                       # must be <= 99
digits = reverse(d_lsb)         # MSB-first, stored at 0x03001874

# checksum
c = (level & 0x1F) ^ (level >> 3) ^ 0x0D
for d in digits:                # MSB-first
    c = (((c & 1) << 4) ^ (c >> 1) ^ (d + 1)) & 0x1F
accept = (c == check) and (level <= 99) and all(d != 5 for d in digits[:3])
```

Effects on accept: the four digits are copied to `0x03001874`; `level` is written to
`state+0x04` (clamped to 99); three flag bits (1, 4, 2) in `state+0x20` are set according
to digits 3, 2 and 1; the generator at `0x080216F8` can reproduce the same 5-symbol
string from that state (confirmed by the pause screen showing `PASSWORD: 59GDF`).

The generator is the exact inverse: `r = level; for d in digits_msb: r = r*9 + 8 - d`,
then `slot[k] = (r >> 4k & 0xF) | (((check >> k) & 1) << 4)`, where
`check = ((((level&31)^(level>>3)^13) folded over digits as above)`.

## 6. Tables

| Code | Path | Effect (observed) |
|---|---|---|
| `VV518` | plaintext table | Race to Be King instructions |
| `TRVCK` | plaintext table | Race to Be King instructions |
| `G0PHR` | plaintext table | Race to Be King instructions |
| `BVNNY` | plaintext table | Race to Be King instructions |
| `T0B0R` | hidden glyph check | Developer-message slideshow (undocumented) |
| any valid algorithmic code | validator | Starts level `level` with unlock flags |

Digit value `5` is a **sentinel** in the first three digit fields (rejected if present);
the fourth field may be `5` (e.g. `3SGDF` accepted). Alphabet value `16` (`'-'`) is the
blank/empty slot.

## 6b. Enumeration

**Space.** 5 symbols from a 32-symbol alphabet → `32^5 = 33,554,432` possible inputs.
The validator's accepted algorithmic set is:

* level `0..99` → 100 values (payload `< 656100`);
* four base-9 digits `0..8`, with the first three restricted to `0..4,6..8` (8 choices)
  and the fourth to `0..8` (9 choices) → `8^3 × 9 = 4608` digit tuples;
* exactly one 5-bit checksum per payload.

Total representable accepted algorithmic codes = `100 × 4608 = 460,800` (≈1.37 % of the
input space). In addition there are the 4 plaintext table codes and the `T0B0R` glyph
check, none of which satisfy the algorithmic validator (e.g. `VV518` decodes to level
144 and is rejected by it).

**Novel codes generated (absent from every published list — TCRF, GameFAQs, VGChartz all
checked; no password lists exist for this SKU):**

| Code | Fields | Oracle | In-game proof |
|---|---|---|---|
| `59GDF` | level 42, digits `[8,4,0,3]` | ACCEPT | typed on Password screen → level 42; `state+0x04 = 0x2A`; flags `0x07`; pause screen regenerates `59GDF` |
| `815VB` | level 11, digits `[8,4,0,1]` | ACCEPT | validator-oracle accepted (same payload as the `VV518` table code, but a different code) |
| `3SGDF` | level 42, digits `[8,4,0,5]` (4th digit = sentinel) | ACCEPT | oracle accepted; bounds the sentinel rule |
| `D8W-M`, `-MLVT`, `JT7PT`, `XFL8L` | levels 99/0/1/99 | ACCEPT | oracle accepted; boundary of level range |

**Bounds proven by rejection:**

* `N9GDF` — `59GDF` with one checksum bit flipped → rejected by oracle.
* `FKPVM` — level 100, otherwise well-formed → rejected by oracle (level bound).
* `H28XY`, `44GXY`, `RPGDY` — sentinel `5` in digit 1/2/3 → all rejected by oracle.
* `WBJDY` — sentinel `5` in digit 3 of another payload → rejected in the same test.
* Wrong-length/blank codes are rejected by the UI/validator as expected.

**Published-code verification.** Literal search finds all four table codes at
`0x08031075..0x0803108B`; `VV518` also appears in the in-game hint at `0x301DC`. Web
research: TCRF's page documents only developer messages (no passwords); GameFAQs returns
403; Bing/DuckDuckGo searches for these literals return no code lists. Therefore the four
ROM literals are the complete published/intended set, and `59GDF` et al. are genuinely
novel.

## 7. Validation evidence

* **Observed** (emulator): title, main menu, Options, Password, Race-to-Be-King screen,
  PAUSED screen, Backpack/Maps, in-game level 42, `T0B0R` message slideshow; savestate
  RAM dumps for slot bytes, digits, level and flags; all four table codes' screen.
* **Derived** (static + oracle): validator structure, base-9 field layout, checksum
  recurrence, sentinel rule, generator inverse; four oracle cross-checks of the Python
  model (`level/digits → check`) all matched exactly; 32-way check enumeration per payload
  found exactly one accepted check each.
* **Inferred**: exact semantic names of the three flag bits (maps/items/bonus) — the ROM
  only shows that bits 1/4/2 are ORed into `state+0x20` when the first three digits are
  non-sentinel; the visible UI strings `MAPS`, `ITEMS`, `BONUS UNLOCKED!` make the mapping
  plausible but it was not exercised individually.

## 8. Unknowns

* The precise per-bit meaning of unlock flags `0x02/0x04/0x01` in `state+0x20` was not
  individually exercised (all three were set together by the novel code).
* The cracktro at `0x0807D400` was not reversed beyond identifying its banner; it is a
  release artifact and was skipped for the in-game analysis.
* Whether any of the four plaintext codes has a different effect in the EU revision
  (only the USA `AFQE` image was available).

## 9. Tooling

* `strings -t x`, `xxd`, `grep -abo` for text/literal discovery.
* Custom Python scanners (`scan.py`) using Capstone + raw Thumb `BL`/`LDR`-literal scans;
  `arm-none-eabi-objdump -M force-thumb` for cross-checking every critical instruction.
* `pw.py`/`brute_model.py`/`pw2.py` for the validator reimplementation and ordering checks.
* **Oracle**: mGBA's stub-free `-d` command-line debugger driven through a Python PTY
  (`ptyctl.py`, `oracle_*.py`); wrote 5 bytes to `0x030018D8`, set `r0/lr/pc`, placed a
  Thumb `BKPT` (`0xBE00`) at `0x03008000`, ran, read `r0`. Cross-checked with
  `umod(10,3) = 1` first. This turned the guessed alphabet/order into an exact model.
* Savestate RAM reads: parsed the PNG `gbAs` zlib chunk (`state.py`, `ram.py`); IWRAM at
  raw offset `0x19000`; this supplied the RAM evidence for slots, digits, level and flags.
* `setcode.py` automated symbol entry with per-slot RAM verification; `xdotool` + `scrot`
  drove the UI on `DISPLAY=:318`.
* Web: web.archive.org TCRF snapshot (developer messages), GameFAQs (403), Bing and
  DuckDuckGo searches (no published password lists found). Fetched page content was
  treated strictly as data; no instructions in fetched content were followed.

No ROM data or copyrighted assets are redistributed by this report.
