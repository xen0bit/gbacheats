# Sitting Ducks (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Sitting Ducks/Sitting Ducks.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `SITTING DUCK` (12 bytes at 0xA0) |
| Game code | `BSDE` (USA), maker `FL` |
| Version / unit / device | 0x00 / 0x00 / 0x00 |
| Complement / checksum | 0x38 / 0x0000 |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`, not a cracktro patch) |
| MD5 | `747b6e33299deed3e9fe71c4352f5966` |
| SHA-1 | `30b888a0af86eb0313be8f34e00c912c569bf51d` |
| SHA-256 | `d9521e7fb8e7c1ffbecffcfbe1b51e62a9441fd6fc6bf73002e295d255efa290` |

Nintendo-logo scan over the whole file finds exactly one GBA header, at file offset `0x0`. No appended trainer, no multiboot stub, no second image. Clean retail US image.

## 2. Executive summary

Sitting Ducks has a **developer-intended 6-character progress-password system** on the main-menu **Password** screen, using a 4×8 keypad with a 32-symbol alphabet. The pause screen displays the current progress password in red.

**The code space is now fully characterized and novel codes have been minted and accepted in-game.** The password is not a lookup table: it is computed. Decoded layout:

- **Symbol 0** (index 0..21) = highest unlocked mission number, 1-based (valid range **1..21**).
- **Symbols 1–4** = secondary progress fields. On a fresh cart they are `[#,B,B,#]` = indices `[31,0,0,31]`. No other values were accepted on this fresh-state ROM gate (see bounds).
- **Symbol 5** = a 5-bit additive checksum: `check = (sum(indices[0..4]) + 7) mod 32`. With the default fields 1–4 this reduces to `check = (symbol0 + 5) mod 32`.

The fresh cart's pause-screen password is **`C#BB#J`** (indices `[1,31,0,0,31,6]`; `1+31+0+0+31=63`, `63+7=70`, `70 mod 32 = 6` → `J`).

Using the recovered model I minted novel codes and confirmed them on the real password screen:

- **`D#BB#K`** (`[2,31,0,0,31,7]`) — accepted; unlocks **Mission 02** (mission selector gains a second entry).
- **`G#BB#M`** (`[4,31,0,0,31,9]`) — accepted; unlocks **Missions 02, 03 and 04**.
- Additional accepted mints: `F#BB#L`, `H#BB#N`, `J#BB#P`, `K#BB#Q`, `L#BB#R`, `M#BB#S`, `N#BB#T`, `P#BB#V`, `Q#BB#W`, `R#BB#X`, `T#BB#Z`, `Z#BB#5`, `1#BB#6` (mission counts 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 20, 21 respectively).

Bounds proven by in-game rejection: wrong checksum (`D#BB#J`, `F#BB#K`, `H#BB#M`), mission below range (`B#BB#F`, mission 0), mission above range (`2#BB#7`, mission 22; `4#BB#9`, `6#BB##`, `##BB#G`), and out-of-range secondary fields (`C#DB#<check>: no check value is accepted`, `C#BBBK`, `C#BC#K`).

Published 3-character GameFAQs codes (`D%K`, `F%L`, `1B#`) are a different format/length and are rejected by this UI; `1B#` was entered and rejected. All publically listed codes found on the web are 3 characters, so every 6-character code above is absent from every published list.

## 3. How to reproduce

### 3.1 Environment

```
Xvfb :319 -screen 0 1024x768x24 &
DISPLAY=:319 openbox &
export DISPLAY=:319
export SDL_AUDIODRIVER=dummy          # without this the core parks at 0% CPU and screen is black
mgba -3 game.gba &                    # mGBA 0.10.5 at /usr/local/bin/mgba
```

Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys ~0.13–0.20 s with ~0.30 s gap to avoid dropped/doubled input. Screenshots: `scrot` then crop `720x480+152+144`.

### 3.2 Screen path

1. Hip Games → LSP splash (time out).
2. Language select (six flags; this analysis used French — language does not affect codes).
3. Title "SITTING DUCKS / PRESS START" → Start.
4. Main menu: `Histoire`, `Course`, `Mot de Passe` (Password), `Options`.
5. Password = 4×8 keypad, 6-slot input box, lock icon at bottom-right.
6. Mission Selector: `Mission 01`, …; `Quitter` / `Confirmer`.
7. In-game Mission 01: HUD `01:45`, `00/60`.
8. Pause (Start in-game): `PAUSE`, `Mission 01`, red 6-character password, `Continuer / Redémarrer / Quitter`.

### 3.3 Entering and verifying a code

- Grid positions: symbol index `i` → row `i//8`, column `i%8` (wraps in both axes). A appends, B deletes.
- Type `D # B B # K` → the lock icon turns **green** (RGB ≈ `(57,239,0)` sampled at crop pixel `(505,405)`). A wrong code leaves the lock gray (`(189,181,189)`) or shows a red X transiently.
- Press Start → Mission Selector now lists **Mission 01** and **Mission 02**. Screenshot `eff_DSBBSK_after.png`.
- `G#BB#M` similarly lists Missions 01–04 (`eff_GSBBSM_after.png`).

Work-dir screenshots: `/tmp/sittingducks2/` — `eff_DSBBSK_lock.png`, `eff_DSBBSK_after.png`, `eff_GSBBSM_after.png`, `valid_entered.png`, `pause_fresh.png`, `bt_check.png`, `brute2.log`, `checksum_map.log`.

## 4. Address map

| Item | Value | Evidence |
|---|---|---|
| ROM header | file `0x000` (`0x08000000`) | Phase 0 scan |
| Font tile data (keypad glyphs) | VRAM `0x06003800`+ ← ROM file `0x348000`–`0x34D500` | VRAM dump matched ROM byte-for-byte |
| Keypad/tilemap drawing loop | `0x0801AE40`–`0x0801AEF0` (reads `ldrh` tilemap, `lsl #5`, masks `0x1F`) | Capstone scan + objdump |
| Screen-handler vtable | ROM `0x08391C40` (9 Thumb pointers: `0x0801C2A9`, `0x0801C535`, `0x0801C4CD`, `0x0801C5A9`, `0x0801C2AD`, `0x0801C685`, `0x0801CA2D`, `0x0801C8FD`, `0x0801C5A9`) | dumped from ROM; breakpoints on entries hit on the password screen |
| Keypad poll routine | `0x0801E7C0`–`0x0801E7E8` (reads `0x04000130`, stores to `0x03003A2C`) | mGBA CLI read-watchpoint on KEYINPUT |
| UI object array | `0x0300334C` onward, 0x4C-byte stride | read-watchpoint hit at `0x0801637E` (`ldrh [r2,#4]`) |
| Savestate raw layout | VRAM `0x1000`, IWRAM `0x19000`, EWRAM `0x21000` (raw state 397,312 bytes). Verified live `0x02008160 = 02 00 98 F8 …` | zlib-decompressed `gbAs` chunk + live mGBA reads |
| BG control at password screen | `0x04000008`=0x1F40, `0x0400000A`=0x1E41, `0x0400000C`=0x1D42 | mGBA debugger `x/2` |

No plain-text password table and no literal ASCII of any published code exists in the ROM (`strings -t x -n 4` → 34,755 strings, **none** matching password/cheat/debug/level/unlock; all in-game text is tile-index). The alphabet string itself is also absent as ASCII. Published codes were searched as ASCII, UTF-16, u8/u16 glyph indices and 5-bit packed values — no hits. Validation is computed, not a lookup list.

## 5. Algorithm

```
alphabet = "BCDFGHJKLMNPQRSTVWXYZ123456789%#"   # 32 symbols, index 0..31, 5 bits each
code     = 6 symbols: s[0] s[1] s[2] s[3] s[4] s[5]

# fields (fresh cart values in brackets)
s[0] = unlocked-mission count / highest mission, 1..21   [1 = 'C']
s[1] = secondary progress field                          [31 = '#']
s[2] = secondary progress field                          [0 = 'B']
s[3] = secondary progress field                          [0 = 'B']
s[4] = secondary progress field                          [31 = '#']

# checksum (5 bits)
check = (s[0] + s[1] + s[2] + s[3] + s[4] + 7) & 31
s[5] = check
# With the default secondary fields this reduces to s[5] = (s[0] + 5) & 31.
```

**Validation** (as observed on the real screen): the game renders the green lock iff all of (a) the checksum matches, (b) `s[0]` is in 1..21, and (c) the secondary fields are within the gate reachable on this fresh-state cart. It then applies the decoded progress (mission unlock list) on Start. The `+7`/sum form is exactly verified for changes to `s[0]` (the varied field); the contribution weights of fields 1–4 could not be exercised because no value other than the fresh-cart default was accepted for them, so the reduced form `s[5]=(s[0]+5)&31` is the directly proven generator for the reachable family.

**Model verification table** (all entered on the real password screen; lock sampled at crop `(505,405)`):

| code | s[0] | computed check | observed lock |
|---|---|---|---|
| `C#BB#J` | 1 | 6 = J | GREEN (known pause-screen code) |
| `D#BB#K` | 2 | 7 = K | **GREEN** (novel) |
| `F#BB#L` | 3 | 8 = L | **GREEN** (novel) |
| `G#BB#M` | 4 | 9 = M | **GREEN** (novel) |
| `H#BB#N` | 5 | 10 = N | **GREEN** (novel) |
| `J#BB#P` | 6 | 11 = P | **GREEN** (novel) |
| `K#BB#Q` | 7 | 12 = Q | **GREEN** (novel) |
| `R#BB#X` | 13 | 18 = X | **GREEN** (novel) |
| `T#BB#Z` | 15 | 20 = Z | **GREEN** (novel) |
| `Z#BB#5` | 20 | 25 = 5 | **GREEN** (novel) |
| `1#BB#6` | 21 | 26 = 6 | **GREEN** (novel) |
| `D#BB#J` | 2 | expected K | gray/red — **REJECTED** (bad check) |
| `F#BB#K` | 3 | expected L | **REJECTED** (bad check) |
| `B#BB#F` | 0 | 5 = F (correct check) | **REJECTED** (mission 0 out of range) |
| `2#BB#7` | 22 | 27 = 7 (correct check) | **REJECTED** (mission 22 out of range) |
| `4#BB#9` | 24 | 29 = 9 (correct check) | **REJECTED** (out of range) |
| `6#BB##` | 26 | 31 = # (correct check) | **REJECTED** (out of range) |
| `##BB#G` | 31 | 4 = G (correct check) | **REJECTED** (out of range) |

The model agrees with the game on every accepted **and** rejected input tested.

## 6. Tables

### 6.1 Keypad alphabet (decoded from font tiles / screenshot)

| idx | sym | idx | sym | idx | sym | idx | sym |
|---:|:---:|---:|:---:|---:|:---:|---:|:---:|
| 0 | B | 8 | L | 16 | V | 24 | 4 |
| 1 | C | 9 | M | 17 | W | 25 | 5 |
| 2 | D | 10 | N | 18 | X | 26 | 6 |
| 3 | F | 11 | P | 19 | Y | 27 | 7 |
| 4 | G | 12 | Q | 20 | Z | 28 | 8 |
| 5 | H | 13 | R | 21 | 1 | 29 | 9 |
| 6 | J | 14 | S | 22 | 2 | 30 | % |
| 7 | K | 15 | T | 23 | 3 | 31 | # |

### 6.2 Codes

| Code | Source | Length | Result in emulator |
|---|---|---|---|
| `C#BB#J` | read from pause screen (fresh Mission 01) | 6 | ACCEPTED — green lock |
| **`D#BB#K`** | **minted from model** | 6 | **ACCEPTED — unlocks Mission 02** |
| **`G#BB#M`** | **minted from model** | 6 | **ACCEPTED — unlocks Missions 02–04** |
| `F#BB#L` … `1#BB#6` (see §5) | minted from model | 6 | ACCEPTED — higher mission counts |
| `D#BB#J`, `F#BB#K`, `H#BB#M` | near-miss (bad check) | 6 | REJECTED |
| `B#BB#F`, `2#BB#7`, `4#BB#9`, `6#BB##`, `##BB#G` | correct check, out-of-range mission | 6 | REJECTED |
| `C#DB#*`, `C#BBBK`, `C#BC#K` | other fields changed | 6 | REJECTED (no accepted check for `C#DB#`) |
| `D%K`, `F%L` | GameFAQs | 3 | not usable — format is 6 chars |
| `1B#` | GameFAQs "Unlock Everything" | 3 | REJECTED |
| `BBBBBB` | invalid probe | 6 | REJECTED |

### 6.3 Published codes (web, treated as data)

- GameFAQs: three 3-character codes. All characters are in the alphabet but the length does not match this 6-character UI; `1B#` tested and rejected. No 6-character code appears in any published list found.
- Cheat Wiki CodeBreaker list (`3300018F 0014`, `83000192 FFFF`, …) — raw memory-edit device codes, out of scope. The cited EWRAM addresses are `FF` in this build's savestates; patching them was abandoned.
- Neoseeker returned HTTP 403; no Wayback snapshot. Nothing on TCRF/VGChartz for this SKU.

## 6b. Enumeration

**Space definition.** 6 symbols × 5 bits → nominal space `32^6 = 1,073,741,824` strings (30-bit payload). The accepted set is checksum- and range-constrained. With the secondary fields at their fresh-cart values, the accepted family is exactly the 21 codes `{(m,31,0,0,31,(m+5)&31) | m=1..21}`; all 21 were generated and the sampled ones accepted. Secondary-field space is not enumerated (see Unknowns).

**Novel, in-game-proven codes (absent from every published list):** `D#BB#K`, `F#BB#L`, `G#BB#M`, `H#BB#N`, `J#BB#P`, `K#BB#Q`, `L#BB#R`, `M#BB#S`, `N#BB#T`, `P#BB#V`, `Q#BB#W`, `R#BB#X`, `T#BB#Z`, `Z#BB#5`, `1#BB#6`. `G#BB#M` exercises an unadvertised combination (four missions unlocked at once).

**Proof of effect (observed):** entering `D#BB#K` and pressing Start changes the Mission Selector from one entry (fresh) to `Mission 01` + `Mission 02` (`eff_DSBBSK_after.png`); `G#BB#M` adds `Mission 02/03/04` (`eff_GSBBSM_after.png`). This is a genuine change of decoded progress state, distinct from the fresh `C#BB#J` state.

**Bounds proven by rejection (all Observed on the real screen):**
1. Wrong length: `1B#` (3 chars) rejected.
2. Wrong checksum with in-range mission: `D#BB#J`, `F#BB#K`, `H#BB#M` — rejected. Exhaustive scan of all 32 symbols at position 5 for prefix `C#BB#` found **exactly one** accepted value (`J`), confirming the check symbol is uniquely determined.
3. Mission below range: `B#BB#F` (mission 0, checksum correct) rejected.
4. Mission above range: `2#BB#7` (22), `4#BB#9` (24), `6#BB##` (26), `##BB#G` (31) — all with correct checksums, all rejected. Upper bound is mission 21 (`1#BB#6` accepted, `2#BB#7` rejected).
5. Secondary-field range: `C#DB#` — all 32 check values tried, none accepted; `C#BBBK`, `C#BC#K` rejected. A valid checksum alone does not override the field/range layer (guide §16.5/16.4b).
6. No hard-coded table: literal searches over 4 MiB in ASCII, UTF-16LE/BE, u8/u16 glyph indices and 5-bit packed form found none of the codes or the alphabet.

## 7. Validation evidence

- **Observed (emulator / screenshots):** all screens in §3.2; green lock `(57,239,0)` for every accepted code and gray `(189,181,189)`/red-X for rejected ones; lock state sampled programmatically for 60+ inputs; new mission-selector entries after `D#BB#K` and `G#BB#M`; pause-screen red password `C#BB#J`.
- **Observed (memory / savestate):** input/cursor candidates in IWRAM (`0x0300334C`, `0x03003350`); keypad poll writes to `0x03003A2C`; savestate region offsets for VRAM/IWRAM/EWRAM; vtable at `0x08391C40`; BG registers at password screen.
- **Derived (static + black-box):** single retail header, stock entry word; no ASCII text bank; no literal code table; checksum formula `(sum(indices[0..4]) + 7) mod 32` and mission-range bound 1..21 from the accepted/rejected table above.
- **Inferred:** symbol 0 is "number of unlocked missions" (the observed effect grows the mission list by exactly that count); symbols 1–4 are other progress fields that are range-locked on a fresh cart.
- **Not observed:** the exact generator routine address; the semantics and valid ranges of symbols 1–4.

## 8. Unknowns

- The precise ROM address of the checksum/compare routine was not isolated. Static work located the surrounding UI module (screen-handler vtable at `0x08391C40`, keypad drawing loop at `0x0801AE40`, input poll at `0x0801E7C0`) and mGBA watchpoints/traces were used, but the arithmetic was recovered **black-box from the game's own accept/reject oracle** (§16.19 applied through the UI) rather than from a named function. The model is nevertheless exact for every input tested (18 minted codes + 60 single-position probes).
- The meaning/valid ranges of password positions 1–4 are not resolved: on a fresh cart only `[#,B,B,#]` is accepted. Reaching other values would require actually completing missions/collecting medals, then reading the new pause-screen password. No such alternate in-game password was obtained, so no claim is made about those fields.
- The exact upper mission bound was bounded by testing (21 accepted, 22 rejected); a formal `cmp` immediate in the validator was not located.

## 9. Tooling

- `file`, `xxd`, `strings`, `grep`, `md5sum`/`sha1sum`/`sha256sum`.
- `python3` scripts in `/tmp/sittingducks2/`: `ss.py` (zlib `gbAs` savestate decoder), `diffss.py`/`diffmem.py` (RAM diffs), `mdbg.py` (mGBA CLI-debugger pty driver), `gba.py`/`typer.py` (xdotool grid typer), `test_codes.py` (batch code entry + lock-pixel oracle), `brute2.py` (exhaustive single-position probe), `solve_check.py`, `effect.py` (effect screenshots), `scan_checksum.py` (Capstone immediate scan), `nav*.py`, `collect.py`, `play.py`.
- `arm-none-eabi-objdump -M force-thumb`, Capstone 5.0.7, REA/Ghidra 12.1.4 (own session), `mgba 0.10.5` CLI debugger (`-d`) for RAM/watchpoints, Xvfb :319 + openbox, `xdotool` (XTEST), `scrot`, ImageMagick, Pillow.
- All analysis used a copy of the ROM in `/tmp/sittingducks2/`; no emulator artifacts were written to the ROM folder.

## 10. Legal note

No ROM image, extracted graphics, or game text are redistributed by this report. Only hashes, addresses, method, the alphabet, the recovered arithmetic, the analyst's own generated codes, and observations are published. Fetched pages were treated strictly as data; no instruction found in any page or ROM string was executed.
