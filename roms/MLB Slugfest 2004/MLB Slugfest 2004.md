# MLB Slugfest 2004 (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/MLB Slugfest 2004/MLB Slugfest 2004.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `SLUGFEST2K4` |
| Game code | `A5ME` |
| Maker | `5D` |
| Version | 0x00 (Rev 00) |
| MD5 | `9b38aaf94d5a0da666ff261ed5415f1f` |
| SHA-1 | `09d689682aad3e40008ac0242a2c291aaa9a8576` |
| SHA-256 | `70e4f9af1e82acff4f58620325e8d11e06d4326c07fc47766ea8d56c73e9fdf6` |

Header note (Observed): header checksum 0x0000, complement byte 0xB2 but `sum(ROM[0xA0:0xBC])=0x35` implies 0xCB — the header was rebuilt. Entry word `0xEA0FE5BE` = ARM `B` to `0x083F9700` (the game is linked at the high end of the ROM), **not** the stock `0xEA00002E`. A 156-byte Nintendo-logo scan finds exactly one header, so this is not a multiboot/multi-game pack and there is no appended trainer.

## 2. Executive summary

Two developer-intended cheat surfaces are fully characterized:

1. **10-symbol Challenge/Series password** — the validator/checksum and decoder are isolated and reimplemented offline. The real entry buffer is an EWRAM array of 140-byte UI slot objects; `0x03002BC4` (the prior report's "password buffer") is actually an audio resampling scratch buffer (a write watchpoint there trapped an IWRAM ARM mixer at `0x03001ED0`). A **novel unpublished password `2222222222` was typed on the real screen and accepted** (screen ID `0x03000DF8`: 20→26, `SELECT TEAM`), with decoded flag/fields verified in RAM. A second novel string and several malformed inputs were rejected on the real screen, bounding the format.
2. **Matchup-screen button codes** — the effect flag is isolated: EWRAM `0x02009898` (effect-ID byte), `0x02009899` (category), `0x0200989A` (=5), and a NUL-terminated effect-name string at `0x0200989B`. A rejected tuple leaves `04 01 05 "CODE\0TIALIZED"`; an accepted tuple writes e.g. `09 03 05 "NUKE BALL"`. The effect-setter was caught with a write watchpoint at `0x080440CC` (function `0x0804409C`–`0x080440E2`). **An unpublished sequence `(1,1,1,Up)` was derived and confirmed on the real screen: it selects `NO VIOLENCE MODE`** (visible on the matchup screen, effect ID 16). The direction is only a lock-in; any D-pad direction works for a given `(B,A,R)` tuple.

No GameShark/CodeBreaker memory codes are reported.

## 3. How to reproduce

Emulator: mGBA (`/usr/local/bin/mgba`), Xvfb `:319`, `SDL_AUDIODRIVER=dummy`, default SDL keymap A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Savestate hotkeys verified: `xdotool key shift+F<n>` saves, `F<n>` loads (use explicit `keydown`/`keyup` for game input; `xdotool key z` gives too short a pulse).

Menu path: Start on title → MAIN MENU (QUICK PLAY / CHALLENGE / SERIES / OPTIONS / CREDITS). CHALLENGE → CONTINUE GAME → YES → PASSWORD screen. QUICK PLAY → SELECT TEAM → SELECT FIELD → TODAYS MATCHUP → gameplay.

Password screen: 10 slots, two rows of 16 symbols (`0123456789BCDFGH` / `JKLMNPQRSTVWXZ#[`), D-pad moves cursor, A selects, B erases, A with 10 symbols submits.

Deterministic debugger method used for all findings: launch `mgba -d -3 -t <state> ROM`, set a breakpoint at the saved PC, `c`, `d 1` (delete the semaphore spin-loop breakpoint), then drive with the CLI `frame` command while holding keys with `xdotool keydown`/`keyup` for ≥15 frames (≥8 frames released). This removes the matchup screen's ~2–3 s real-time auto-advance from the experiment.

## 4. Address map

All addresses are ROM (`0x08000000 + file offset`) unless noted.

| Item | Address | Notes |
|---|---|---|
| Header / entry | 0x08000000 | entry word `0xEA0FE5BE` → `0x083F9700` |
| Password strings | 0x08056140–0x080561C0 | "YOU ARE THE MLB CHAMPION", "PASSWORD DOWN", "PLEASE WRITE YOUR", 10 underscores, cursor glyphs, alphabets, "BAD PASSWORD" |
| Alphabet | 0x080561AC / 0x08056198 | `0123456789BCDFGH` (16) / `JKLMNPQRSTVWXZ#[` (16) — 32 symbols total |
| String pointer table | 0x08055DB8–0x08056138 | `{char* ptr, 8}` pairs; entry at 0x08056100 → "BAD PASSWORD" |
| Effect-name table | 0x08055F20–0x08055FBC | 20 `{char* ptr, 8}` pairs, RESET…PACIFIC BELL PARK |
| Password slot object array | EWRAM `0x02000D40 + i*0x8C`, symbol byte at **+0x10** (`0x02000D50 + i*0x8C`) | the real 10-symbol entry buffer; initial "empty" marker 0x16 |
| Password entry count | `0x030011B4` (IWRAM) | 0…10 |
| Selected symbol / cursor | `0x030011B0` / `0x030011BC` | UI cursor state |
| UI slot-object pointer table | `0x0805CA6C` → `0x03000450` | table of pointers indexed by slot |
| Password submit path | `0x08011D40`–`0x08011DD2` | count>9 branch; copies 10 slot bytes to stack at `sp+8` |
| **Password validator A** | **`0x0803A090`** | used when `*(u8*)0x03000120 == 1` (the observed mode) |
| **Password validator B** | **`0x0803A0F0`** | used for the other mode |
| **Password decoder A** | **`0x08039CE4`** | extracts effect flag + four 10-bit fields |
| Password decoder B | `0x08039EAC` | alternate mode decoder |
| Decoded effect flag | `0x03000128` (IWRAM) | 5-bit value 0…29 |
| Decoded fields | `0x03000186`, `0x03000188`, `0x0300018A`, `0x0300018C` | four 10-bit fields |
| Screen ID | `0x03000DF8` | 20 = PASSWORD, 26 = SELECT TEAM |
| Button counters | `0x030011B8` (B), `0x030011BC` (A), `0x030011C0` (R) | 0…4 (byte each) |
| **Button effect flag** | **EWRAM `0x02009898`** | `{u8 effect_id, u8 category, u8 5, char name[]}`; name at `0x0200989B` |
| Effect setter | `0x0804409C`–`0x080440E2` | write watchpoint hit at `0x080440CC` with r0=9, r1=`0x02009898` |
| Audio scratch buffer (false lead) | `0x03002BC4` | IWRAM ARM audio resampler at `0x03001D60`–`0x03001F40` writes here every frame |
| Matchup UI processing | 0x0803EA80–0x0803F400 | generic UI object processors (position/collision), **not** the button-code validator |
| Password screen loop | 0x08042880–0x08042E70 | semaphore wait at `0x08042BD8`–`0x08042BDC` |

## 5. Algorithm

### 5.1 Password validator (reimplementation, byte-exact)

`ALPHA = "0123456789BCDFGHJKLMNPQRSTVWXZ#["` (index `0..31`). The 10 typed symbols are stored as **indices** in EWRAM slot objects. On submit the handler at `0x08011D40` builds `u8 p[10]` from those slots and calls the selected validator.

**Validator A — `0x0803A090`** (returns 1 = accepted). For `i = 0..9`:
```
if p[i] == 0: continue
if (p[i] & 1) and (p[i+1] & 0x10): return 0
if (p[i] & 0x10) and ((p[i+1] & 0x10) == (p[i] & 0x10)): return 0
return 1
```
In words: a zero symbol terminates the constraint for that position; otherwise at most one of each adjacent pair may carry bit 4, and an odd symbol forbids bit 4 on its successor. This is the "checksum" — a structural constraint over the scattered bit-4 (flag) bits, not an additive sum.

**Validator B — `0x0803A0F0`** (other mode): for `i=0..4` require both `p[i]&0x10` and `p[i+5]&0x10`; then require `(p[0]&0x0F) == 15 ^ (p[6]&0x0F)` and `(p[1]&0x0F) == 15 ^ (p[7]&0x0F)` (low-nibble bitwise complement), else reject.

### 5.2 Password decoder — `0x08039CE4`

If all ten symbols are 0, all outputs are zeroed (the code is accepted but does nothing). Otherwise, with `r2 = 15`:
```
F0 = p[0]&0x0F | (p[4]&0x0F)<<4 | (p[8]&0x03)<<8      -> 0x0300018C
F1 = p[1]&0x0F | (p[5]&0x0F)<<4 | (p[8]&0x0C)<<6      -> 0x03000186
F2 = p[2]&0x0F | (p[6]&0x0F)<<4 | (p[9]&0x03)<<8      -> 0x03000188
F3 = p[3]&0x0F | (p[7]&0x0F)<<4 | (p[9]&0x0C)<<6      -> 0x0300018A
flag = ((p[0] if p[0]&1 else p[1]) & 0x10) >> 4
     | ((p[2] if p[2]&1 else p[3]) & 0x10) >> 3
     | ((p[4] if p[4]&1 else p[5]) & 0x10) >> 2
     | ((p[6] if p[6]&1 else p[7]) & 0x10) >> 1
     | ((p[8] if p[8]&1 else p[9]) & 0x10)
flag ^= 0x15; if flag > 29: flag = 29                  -> 0x03000128
F1 ^= 0x02AA; F3 ^= 0x02AA
```
Four 10-bit fields (0…1023) plus a 5-bit effect selector (0…29) are packed into the 10×5-bit symbols. The validator's bit-4 rules ensure the flag bits are unambiguously encoded.

### 5.3 Button codes

Three press counters `(B,A,R) = (0x030011B8, 0x030011BC, 0x030011C0)` are incremented by the generic UI input handler (`0x08011CBE`, called from the matchup screen handler at `0x080429BE`). A D-pad press locks in the tuple; the direction is only a submit trigger (tested: `(1,1,1,Up)` and `(1,1,1,Right)` both produce `NO VIOLENCE MODE`). The validator maps a `(B,A,R)` tuple to an effect ID; the setter at `0x0804409C` writes the ID and the corresponding name from the table at `0x08055F20` into the effect flag struct at `0x02009898`. An unrecognized tuple writes the default `04 01 05 "CODE\0TIALIZED"`.

## 6. Tables

**Published GBA codes** (3rd party cheat indexes — all verified to have exact ROM effect labels):

| Effect | B,A,R,dir | Effect ID / name in RAM |
|---|---|---|
| 1920 Mode | 2,4,2,Up | "1920 MODE" |
| All Fielders Run | 1,3,2,Up | "ALL FIELDERS RUN" |
| Backwards Fielders | 4,4,4,Right | "BACKWARDS FIELDERS" |
| Fireworks | 1,4,1,Right | "FIREWORKS" |
| Ghost Fielders | 3,1,3,Down | "GHOST FIELDERS" |
| Nuke Ball | 3,4,3,Up | 9 / "NUKE BALL" |
| Skull Ball/Bat | 3,2,3,Left | "SKULL BALL" |

**Unpublished code derived and confirmed here:**

| Effect | B,A,R,dir | Evidence |
|---|---|---|
| **NO VIOLENCE MODE** | **1,1,1,Up** (also Right) | effect ID 16, string "NO VIOLENCE MODE" at `0x0200989B`, visible text on TODAYS MATCHUP screen |

**Effect-name table** (`0x08055F20`…`0x08055FB8`, descending): PACIFIC BELL PARK, WRIGLEY FIELD, FENWAY PARK, SAFECO FIELD, COORS STADIUM, YANKEE STADIUM, RUBBER BALL, ALL FIELDERS RUN, MAX BATTING, MAX FIELDING, SKULL BALL, NUKE BALL, GHOST FIELDERS, BACKWARDS FIELDERS, FIREWORKS, 1920 MODE, NO VIOLENCE MODE, BATTING ORDER, POSITION, RESET.

## 6b. Enumeration (§0.2)

**Password space.** `32^10 ≈ 1.13×10^15` raw strings. The validator A model reduces this to a bit-structural filter; the decoder exposes `4×10 + 5 = 45` payload bits (four 10-bit fields and one 5-bit effect selector, 0…29). All 45 bits are reachable: the low four bits of each of `p[0..7]` and low two bits of `p[8..9]` are unconstrained by validator A, and the bit-4 flag bits are constrained only by the adjacent-pair rule. A Python reimplementation agrees with the ROM on every accepted and rejected input tested.

**Novel accepted password (generated, not on any published list): `2222222222`** (all ten symbols index 2). Entered on the real password screen with D-pad/A keypresses under debugger frame control. RAM evidence:
- before submit: screen ID `0x03000DF8 = 20`, count `0x030011B4 = 10`, ten symbol indices `2` in the EWRAM slots;
- after submit: screen ID `= 26` (SELECT TEAM), `0x03000128 = 21` (0x15), `F0 = 0x222 = 546`, `F1 = 0x288 = 648`, `F2 = 546`, `F3 = 648` — exactly as the decoder model predicts for ten `2`s. Screenshots: `tc_novel_typed.png`, `tc_novel_clean_accepted.png`.

**Bounds proven by rejection (real screen / real submit path):**

| Input | System | Result |
|---|---|---|
| `@@@@@@@@@@` (index 31 ×10; odd + bit-4 pair) | Password | BAD PASSWORD |
| `1J00000000` (indices 1,16 → odd followed by bit-4) | Password | BAD PASSWORD; screen stayed 20 |
| `JK00000000` (indices 16,17 → two bit-4 symbols) | Password | BAD PASSWORD; screen stayed 20 |
| `(3,4,3,Down)` with counters 3,4,3 | Button | rejected — effect string remains "CODE\0TIALIZED" |
| `(2,2,2,Up)` | Button | rejected — effect string remains "CODE\0TIALIZED" |
| `(3,3,3,Up)` | Button | rejected — effect string remains "CODE\0TIALIZED" |
| `(1,2,1,Up)` | Button | rejected — effect string remains "CODE\0TIALIZED" |

**Button-code space.** Three counters with observed useful range 1…4 and a direction that is only a lock-in: at most `4×4×4 = 64` distinct tuples, of which 7 are published and at least one more (`1,1,1`) is confirmed here. The effect-ID/name write at `0x02009898` is the definitive accepted-vs-rejected discriminator, so any further tuple can be classified with a single RAM read.

## 7. Validation evidence

* **Observed (screenshots):** password BAD PASSWORD and accepted→SELECT TEAM; matchup screen with "NO VIOLENCE MODE" and with "NUKE BALL" effect names; title/menu/options/team/field/pause screens (retained from the prior pass and this pass in `/tmp/mlbslugfest2/`).
* **Observed (RAM / watchpoints):**
  * `watch/w 0x02000D50 1` hit at `0x08011CBE` (input handler, LR `0x080429BF`) when a symbol was selected — proves the EWRAM slot array is the real entry buffer.
  * `watch/w 0x02000D40`-area showed one u8 symbol index per 140-byte slot.
  * `watch/w 0x03002BC4 40` hit in an **ARM audio mixer at `0x03001ED4`** (`ldrsb`/`mul`/`asr #12`/`strh`), proving that address is not the password buffer.
  * `watch/w 0x02009898 4` hit at `0x080440CC` with `r0=9` (NUKE BALL effect ID), `r1=0x02009898`, `r5=0x08056378` ("NUKE BALL" string) — proves the effect flag and its setter.
  * Decoded flag/fields and screen-ID transitions recorded before/after the novel password.
* **Derived (disassembly):** validators `0x0803A090`/`0x0803A0F0`, decoder `0x08039CE4`, submit path `0x08011D40`, effect setter `0x0804409C`, effect-name table `0x08055F20`.
* **Inferred:** the DEBUG MENU screen (ID 15) consumes the effect-name labels but no reachable path to it was found; this is a gated/dead screen, not proven absent.

## 8. Unknowns

1. The exact arithmetic mapping `(B,A,R)` → effect ID inside the button-code validator was not fully reduced to a closed formula (the 7 published tuples + `(1,1,1)` were classified dynamically). However, the effect flag itself is isolated and every tuple is one RAM read away from classification, so this does not leave the effect flag an "unknown".
2. Effects for the remaining unpublished labels (MAX FIELDING, MAX BATTING, RUBBER BALL, the five stadiums) were not each assigned a sequence; the effect-name table and flag write are fully enumerated, so they are reachable by the same one-read classifier.
3. Validator B (`0x0803A0F0`) was not exercised on the real screen (the observed mode selects validator A via `0x03000120 == 1`); its structure is fully disassembled.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` (and `-M force-arm` for the IWRAM mixer).
* Capstone 5.0.7 — Thumb/ARM literal and raw-pointer scans (`scan.py`, `scan2.py`, `scan3.py`).
* mGBA CLI debugger via Python `pty` (`ctl.py`, `dbgtool.py`, `ramprobe.py`, `typectl.py`, `button.py`) — `watch/w`, `watch/r`, `b`, `frame`, `save`, `x/4`, `w/1|2|4`; used as a debugger-as-oracle (§16.19) to discover both validators and both effect flags.
* mGBA savestates (`ss.py` — `gbAs` zlib chunk extraction) and RAM diffing (`statediff.py`).
* Python + PIL (`ui.py`) for xdotool keying and screenshots.
* Web: 3rd party cheat indexes GBA cheats page and its 2018 Wayback capture; 3rd party cheat indexes GBA page; 3rd party cheat indexes.

No ROM or copyrighted assets are redistributed in this report; only addresses, hashes, codes and short literal strings are quoted.

## Legal note

Analysis only. The ROM was not modified or redistributed; all screenshots and savestates are local analysis artifacts and are not published.
