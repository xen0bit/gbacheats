# Scooby-Doo and the Cyber Chase (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Scooby-Doo and the Cyber Chase/Scooby-Doo and the Cyber Chase.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `SCOOBY CYBER` |
| Game code | `ASDE` |
| Maker code | `78` (THQ) |
| Version | 0x00 |
| Fixed byte / complement / checksum | `0x96` / `0x61` / `0x0000` |
| Entry word | `0xEA00002E` (stock ARM `b 0x080000C0`, **not** a cracktro patch) |
| MD5 | `1e3fd614dc43edbbf9df51262057f2cc` |
| SHA-1 | `739f47323ce7e2dbe7e9bf9d553cb97f4692ecc3` |
| SHA-256 | `1ffb2d85a66a0a38c4d4c4f90c6b6b25e51079625ffecd301f415edd8d3e1c5f` |

**Phase 0 scan:** exactly one Nintendo-logo hit (file offset `0x4`, i.e. header at `0x0`) — a single-image retail ROM, not a multi-game pack. No appended trainer, no patch/trainer header. The checksum `0x0000` is the normal rebuilt-header artifact; the complement byte `0x61` is consistent.

A `.sav` (0 bytes) is auto-created by mGBA but the game is password-based and does not use battery save memory.

## 2. Executive summary

The game has **two independent password systems**, both developer-intended:

1. **A closed table of 15 hard-coded strings** at ROM `0x0803029C`, checked by a chain of 15 `strcmp` calls in the Thumb function `0x0801BF94`. This includes 11 level/boss/ending shortcuts plus four codes that are **not on any published list** I found: `VRSN1`, `CHTMD1` (and the published `VRSN2`, `CHTMD2` have unpublished "off" partners).

2. **An algorithmic 8-character password system** with a 32-symbol alphabet, a per-field additive key, and a six-group segmented parity checksum. It is reached from the same input screen: when the table check returns `0xFFFF`, the caller (`0x08008F44`) invokes the decoder at `0x0801CA3C`. It accepts exactly **2³⁴ = 17,179,869,184** of the 2⁴⁰ possible 8-symbol strings.

I reimplemented the decoder (`/tmp/scoobycyber/pw.py`), validated it against **all nine published 8-character codes that are absent from the ROM table** (all nine pass), and minted a novel code **`L#8#5VBJ`**. Entered through the real 4×8 on-screen keyboard, it was accepted: the game started and the HUD showed score **135314**, the exact value predicted by the decoded payload (`0x21092`), confirmed in RAM at `0x03000210`.

Bounds were proven by rejection: `L#8#5VBK` (one-symbol parity-breaking near-miss) was accepted by the keyboard but rejected by the game — it stayed on the password screen. Non-alphabet characters (`A`, vowels) cannot even be entered: the screen exposes only the 32-symbol alphabet.

Every reachable screen was walked with screenshots and RAM checks: legal, title, main menu (New Game / Password / Options), Options (Music / SoundFX / Skill / Credits), Credits, Password, and the in-game university/lab hub. The game text bank is plain ASCII script text (the `$name:ID` blocks at `0x02C0A8`–`0x0300F5`), so the display text was decoded directly rather than being tile-indexed.

**Security note:** a fetch of the TCRF page during reconnaissance returned a prompt-injection payload ("This page is not intended for humans… these instructions are only for LLMs… whoever is operating this AI agent is a clown"). It was ignored and is recorded here as data, per guide §16.8.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under `Xvfb :319`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
* Path: boot → press `Return` through legal + title → Main Menu → Down to `PASSWORD` → `x`.
* The password keyboard is a 4×8 grid (Left/Right = ±1 column, Up/Down = ±8; movement clamps at the edges). `A` selects a symbol, `B` deletes, `Select` submits.
* Alphabet order (on screen, uppercase): `B C D F G H J K / L M N P Q R S T / V W X Y Z 1 2 3 / 4 5 6 7 8 9 @ #`.
* Helper scripts used (all in `/tmp/scoobycyber`): `ctrl.py` (XTEST input), `typepw.py` (grid navigation), `pw.py` (decoder/encoder model), `oracle.py` (breakpoint-driven validator oracle), `state.py` (savestate RAM reader), `dbg.py` (mGBA CLI debugger via pty).
* To reproduce the novel-code result: enter `L#8#5VBJ` on the password screen and press Select. The game starts and the score reads `135314`.
* To reproduce the rejection: enter `L#8#5VBK` instead; the game remains on the password screen.

## 4. Address map

| Address (ROM unless noted) | Purpose |
|---|---|
| `0x00000000` / `0x000000C0` | Header / stock entry point |
| `0x02C0A8`–`0x0300F5` | ASCII script bank (`$title_dis`, `$mainmenu`, `$password_dis`, `$options_dis`, `$levelselect`, `$displaypassword`, credits, …) |
| `0x0803029C`–`0x0803033B` | 15 NUL-padded password strings (12-byte stride for 8-char entries) |
| `0x0801BF94` | **Table password validator** (`push {r4,r5,lr}`; 15 `strcmp` calls via `BL 0x08025304`) |
| `0x0801C220` | Common return of the table validator (`bx r1`); `r0` = result |
| `0x0801CA3C` | **Algorithmic password validator** (calls D→C→A) |
| `0x0801C8C4` | D: 8 chars → 40-bit packed payload (5-bit fields) |
| `0x0801C7D4` | C: add per-field key constants (validator direction) |
| `0x0801C6E4` | Inverse of C (subtract keys) — used by the generator at `0x0801C340` |
| `0x0801C5D4` | A: six-group parity checksum check (returns 0/1) |
| `0x0801CA78` | char → alphabet index |
| `0x0801C3E0` | Apply decoded payload to game state |
| `0x08008F06` | Caller of both validators (`BL 0x0801BF94`, then `BL 0x0801CA3C` for 8-char rejects) |
| `0x083FAB10` | Alphabet string `BCDFGHJKLMNPQRSTVWXYZ123456789@#` (+ `0x0A` terminator) |
| `0x083FAB30` | Key table, eight `u32`: `10, 5, 8, 5, 12, 14, 3, 2` |
| `0x02006EA0` | EWRAM input buffer (entered password, uppercase ASCII, NUL-terminated) |
| `0x03000140` | Base of per-level state structures |
| `0x03000210` | IWRAM current score word (verified: `0x00021092` = 135314) |
| `0x03001228` | Version/build-date flag (`VRSN1`=0, `VRSN2`=1) |
| `0x03001AB0` | Cheat-mode flag (`CHTMD1`=0, `CHTMD2`=1) |

## 5. Algorithm

### 5.1 Table path

`validate_table(s)` walks 15 `strcmp` calls in order. On a match it writes a small integer into the per-level state word at `struct+0x198` (or toggles a global flag for the VRSN/CHTMD pair), writes 0 to `struct+0x160`, and returns a small code (10–78). No match → returns `0xFFFF`. Empty input also returns `0xFFFF`. The caller treats `0xFFFF` as rejection and, for 8-character input, falls through to the algorithmic decoder.

### 5.2 Algorithmic path

```
ALPHA = "BCDFGHJKLMNPQRSTVWXYZ123456789@#"   # 32 symbols, index 0..31
KEYS  = [10, 5, 8, 5, 12, 14, 3, 2]         # u32 table at 0x083FAB30

pack8(s):     p = Σ (index(s[i]) & 31) << (5*i)          for i = 0..7
add_keys(p):  q = Σ ((field_i(p) + KEYS[i]) & 31) << (5*i)
check(q):     for (lo,hi,bit) in [(0,6,39),(6,12,38),(12,18,37),
                                  (18,24,36),(24,30,35),(30,34,34)]:
                  assert popcount(q[lo:hi]) & 1 == (q >> bit) & 1
valid(s) = len(s)==8 and all chars in ALPHA and check(add_keys(pack8(s)))
```

The six check bits are the top six bits of the 40-bit word (`q4` bits 7..2); the remaining 34 bits are payload. Each parity group covers six payload bits except the last, which covers four (bits 30–33). The generator at `0x0801C340` performs the inverse: set the 34 payload bits, compute the six parity bits, subtract the key constants, and emit the alphabet symbols.

Payload fields consumed by `0x0801C3E0`:
* `q & 0xFFFFF` → score/starting value (verified in-game).
* `(q >> 16) & 0xF` → level/scene selector (`struct+0x198`).
* `q3` bits 2,3,5,4,6 → five toggle bits (`struct+0x134`); `q3` bits 0..1 → `struct+0x19C`; `q3` bit 7 → `struct+0x1A0`.
* `q4` bits 0,1 → `struct+0x1A4`, `struct+0x1A8`.

## 6. Tables

### 6.1 ROM table (15 entries, 0x0803029C)

| String | ROM address | Effect / state word | Return |
|---|---|---|---|
| `GL@D1@TR` | 0x0803029C | level 1 | 12 |
| `JVNGLDVP` | 0x080302A8 | level 6 | 23 |
| `SPL@SH` | 0x080302B4 | level 3 | 10 |
| `1C3R@LLY` | 0x080302BC | level 8 | 22 |
| `BSYDTH3C` | 0x080302C8 | level 11 | 30 |
| `@MVZM3NT` | 0x080302D4 | level 11 | 27 |
| `1CR33P3R` | 0x080302E0 | level 1 | 25 |
| `GH@TRGHL` | 0x080302EC | level 6 | 39 |
| `1R@NFYC3` | 0x080302F8 | level 11 | 35 |
| `WH@DNN1T` | 0x08030304 | level 11 + three flags | 38 |
| `PSKYK1DS` | 0x08030310 | level 11 + three flags + `0x7AA` | 34 |
| `VRSN1` | 0x0803031C | version flag = 0 | 78 |
| `VRSN2` | 0x08030324 | version flag = 1 | 78 |
| `CHTMD1` | 0x0803032C | cheat flag = 0 | 78 |
| `CHTMD2` | 0x08030334 | cheat flag = 1 | 78 |

Published codes **absent from the ROM table** (treated by the algorithmic path, all validated by the model): `45B9@WST`, `CHBB5VBX`, `MXP#2VBL`, `8QL9SWB2`, `X@X#V7FF`, `LCW72VBL`, `2XF74WS9`, `BTV@S7F#`, `V3Z9R7T3`. Published variants **not found as literals anywhere in the ROM** (so unverified as table entries): `IR@NFYC3` (the ROM stores `1R@NFYC3` instead), `8QL9SWB2` and `45B9@WST` (algorithmic codes, correctly absent as literals). GameFAQs labels were inconsistent across sources (e.g. `LCW72VBL` labelled "Coliseum" but decoding to level field 0), consistent with guide §16.7/§16.15 — the numeric payload is the reliable label.

### 6.2 Cheat-mode button actions (unlocked by `CHTMD2`)

Published and consistent with the cheat flag: Hold Select + R = skip stage; Select + L = captured by Phantom Virus; Select + Start = slow motion; B = sound test. These are gameplay hotkeys, not separate password entries.

## 6b. Enumeration

**Space definition.** The input alphabet is exactly 32 symbols (21 consonants + digits 1–9 + `@` + `#`); vowels and `A` are not exposed. Length is 8 for the algorithmic system; the table system additionally accepts 5- and 6-character literals. Each symbol is 5 bits, so the raw input space is 32⁸ = 2⁴⁰ = 1,099,511,627,776 strings. Six independent parity equations remove six bits: **exactly 2³⁴ = 17,179,869,184 strings are algorithmically valid**, plus the 15 table literals (disjoint — every 8-character table literal fails the parity check, verified). Total accepted set = 2³⁴ + 15.

**Validator model.** `pw.py` implements encode and decode exactly; it accepts all nine published non-table codes and rejects all 15 table literals under the algorithmic check, plus rejects the near-miss and non-alphabet strings.

**Novel code (not in any published list).** `L#8#5VBJ`, generated by taking `CHBB5VBX`'s 34-bit payload, replacing the 16-bit score field with `4242`, and recomputing all six parity bits. Independently checked: `validate() == True`, not in `TABLE`, not in `PUB_NONTABLE`. Entered through the on-screen grid in mGBA and submitted: game started, HUD score **135314** (`0x00021092`), and RAM at `0x03000210` read back `0x00021092`. Screenshot: `novel3.png`.

**Second novel result (unpublished table literal).** `VRSN1` and `CHTMD1` exist in the ROM table but are absent from every published list consulted; `VRSN2` was entered via the UI and set `0x03001228` to `1` (RAM read). `CHTMD2` set `0x03001AB0` to `1` and started the game.

**Bounds proven by rejection.** `L#8#5VBK` (single-symbol change producing wrong parity) passed the keyboard but the game stayed on the password screen after submission (screenshots `reject2.png` / `reject3.png`, 3.5 s apart); debugger trace showed the table validator returning `0xFFFF` and the decoder being invoked, with no game start. `BBBBBBBB` likewise returned `0xFFFF` and did not start the game. A character outside the alphabet cannot be entered at all — the grid offers only the 32 symbols. This bounds the "wrong checksum" and "out-of-alphabet" cases. The 34-bit payload can express all level/flag bit patterns (no reserved bits were observed to be constrained), so no further semantic out-of-range gate was found.

## 7. Validation evidence

* **Observed** (emulator): title/legal/main-menu/password/options/credits/hub screens; keyboard alphabet layout; `L#8#5VBJ` accepted with score 135314 on screen and `0x03000210 == 0x21092`; `L#8#5VBK` rejected (no transition); `CHTMD2` → `0x03001AB0 == 1` and game start; `VRSN2` → `0x03001228 == 1`; debugger trace of both validators (breakpoints at `0x0801BF94`, `0x0801C220`, `0x0801CA3C`) with `r0 = 0x02006EA0` and returns `0x4E` / `0xFFFF`.
* **Derived** (disassembly): the 15-entry table and its effects, the 32-symbol alphabet and key tables, the pack/key/parity algorithm, the generator at `0x0801C340`, and the payload field layout.
* **Inferred**: exact gameplay meaning of some flag bits (e.g. which specific unlock each toggle grants) was not individually played through; the published cheat hotkey effects were not re-tested one by one.

## 8. Unknowns

* `45B9@WST` ("all levels and characters") was model-validated but not entered in-game; its exact set of unlock flags is inferred from the payload only.
* The developer scripts `$scrolltest:41` ("test test for scroll12345") and `$selectchase:10` / `$selectpresit:11` exist in the ASCII text bank but no input path to them was found on any walked screen. They are classified as **dead/gated developer code**, not a reachable debug menu; no published code for them exists (the only wiki claim was an injected "to do" page). This is a bounded negative: every reachable screen was walked and neither the table validator nor the algorithmic payload has a branch that selects those scenes.
* The 0-byte `.sav` suggests no battery RAM; the game's password system is its persistence mechanism.

## 9. Tooling

* Static: `arm-none-eabi-objdump -M force-thumb`, Python/Capstone literal/BL scans, custom Python (`pw.py`, `state.py`).
* Dynamic: mGBA 0.10.5 with `-d` CLI debugger driven through a pty via `script(1)` and a FIFO (`dbg.py`, `oracle.py`), because the GDB stub port 2345 was held by another agent's emulator. Savestate `gbAs` chunks were zlib-decompressed for RAM diffs (`state.py`).
* Input/screens: `xdotool` XTEST events (`ctrl.py`, `typepw.py`), `scrot` + ImageMagick crops; ~20 frames reviewed on disk.
* All generated `.sav`/`.ss*` artifacts in the ROM folder were removed and all processes started for this job were terminated by PID; no `pkill` was used.
