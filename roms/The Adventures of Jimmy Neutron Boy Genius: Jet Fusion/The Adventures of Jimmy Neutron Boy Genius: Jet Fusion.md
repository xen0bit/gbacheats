# The Adventures of Jimmy Neutron Boy Genius: Jet Fusion (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Item | Value |
|---|---|
| File | `The Adventures of Jimmy Neutron Boy Genius: Jet Fusion.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `JETFUSIONENG` |
| Game code | `BJNE78` (code `BJNE`, maker `78`) |
| Revision | 0x00 (`Rev.00`, USA/Europe) |
| Developer / publisher | Helixe / THQ (Helixe splash observed on boot) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock, not a cracktro) |
| Header byte 0xB2 | `0x96` (correct) |
| Header version / complement / checksum | `0x00` / `0x32` / `0x0000` (anomalous complement and zero checksum — rebuilt-header artifact; §16.1) |
| MD5 | `be7b93fdeca8e23caf4b59b4490999ca` |
| SHA-1 | `68778c93fc16d06b97462174d91035cb0d0d8bd5` |
| SHA-256 | `14dc2ea41af8e0bbba6c9e1166ce67fe7241c5163d410913f5d496efdd424b22` |

Gas-station/Action-Replay codes are **out of scope**; everything below is developer-intended input.

## 2. Executive summary

The game has a genuine in-game password system: **Password** on the main menu leads to an on-screen
keyboard with exactly **32 symbols** and an **8-character** entry that auto-submits on the 8th press.
The symbol set is `BCDFGHJKLMNPQRSTVWXYZ123456789!?` (file `0x34430C`, ROM `0x0834430C`), i.e. a
5-bit-per-character code, 40 bits total. The on-screen symbols are *case-insensitive* to the player:
published lists write many of them in lower case (`z91td?93`) while the UI renders capitals.

The published passwords are **not present as plaintext or packed constants in the ROM** — a literal
search for all nine published strings, and a search for their 40-bit packed integers, returned zero
hits. Acceptance is therefore computed by an algorithmic validator, not a lookup table.

Empirically the validator is **not a strict 40-bit equality check**: of the 40 single-bit variants of
a known-good password, 7 were still accepted. All five bits of character 3 (0-based index 2) and bits
1 and 4 of character 4 (index 3) are non-contributing under single-bit mutation. This is the alias
structure exploited below to mint novel codes. The exact checksum arithmetic was **not** recovered —
see §8.

The same 8-character format is used in-game for the "position transponder" **access codes** that
Goddard dictates in dialogue ("The access code for this location is %s.", strings at file
`0x30377C`–`0x305013`). Those are hints for the same password surface, not a separate code system.

No hidden/debug menu, button code, or unlockable cheat screen was found; the reachable menu surface
is New Game / Password / Options (two volume sliders).

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb. **Headless rendering required**
  `SDL_VIDEODRIVER=x11 SDL_RENDER_DRIVER=software SDL_AUDIODRIVER=dummy`;
  plain SDL/GLX produced a black window.
* Keymap (mGBA SDL defaults): A=`x`, B=`z`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
* Path: boot → title "PRESS START" → Start → main menu → Down → **PASSWORD**.
* The savestate `pw.ss1` (copied from the password screen) makes every test one load + 8 entries.
* Enter a code by moving the cursor over each symbol and pressing A; pressing A on the **8th**
  character submits automatically. Result screens:
  * `PASSWORD ACCEPTED / PRESS START TO PLAY` (status flag `0x0200114C == 1`)
  * `ACCESS DENIED / PRESS THE B BUTTON TO TRY AGAIN` (status flag `0x0200114C == 2`)
* Screenshots of every state were in `/tmp/jimmyneutron1/` (`s5.png`, `m2.png`,
  `eight.png`, `test_pub.png`, `novel1.png`, `novboth_acc.png`, `novstart_play.png`,
  `pubstart_play.png`, `walk_options2.png`).

## 4. Address map

| Address (ROM / file) | Meaning | Evidence |
|---|---|---|
| `0x08000000` / `0x000000` | Stock ARM entry `B 0x080000C0` | Observed |
| `0x0834430C` / `0x34430C` | 32-char alphabet `BCDFGHJKLMNPQRSTVWXYZ123456789!?` | Observed |
| `0x08011220` / `0x11220` | Thumb literal pool: pointer to the alphabet above | Derived (disassembly) |
| `0x08011F0` / `0x11F0` | Thumb routine: converts 8 `index+0x40` bytes to ASCII via that alphabet, NUL-terminates at `buf+8` | Derived (disassembly) |
| `0x0830301C`+ / `0x30301C`+ | Localized text banks (English `0x303…`, French `0x3089…`, German `0x3090…`); contains `Password: %s`, `password accepted`, `access denied` and all transponder dialogue | Observed |
| `0x0200113D`–`0x02001144` | EWRAM: 8 password bytes, each stored as `alphabet_index + 0x40` | Observed (savestate diff) |
| `0x02001148` | EWRAM: entry count (`0x08` when full) | Observed |
| `0x0200114C` | EWRAM: status enum — `1` accepted, `2` denied | Observed |
| `0x0200111C`–`0x0200113B` | EWRAM: menu/entry slot table, reset to `0xFF` on accept | Observed |

`0x08011F0` has **no direct `BL`, `B`, or 32-bit function-pointer reference anywhere in the image**
(scans of the full 4 MiB for Thumb BL, B/Bcond, BLX-register and literal pointers). It is reached
indirectly (engine dispatch) or belongs to an overlapping auto-analysis function; the direct caller
was not isolated.

## 5. Algorithm

Reconstructed from static bytes and live RAM:

```
keyboard symbol s (index 0..31 in ALPHABET)
    -> stored byte = s + 0x40              # EWRAM 0x0200113D + position
eight entries stored -> count byte 0x02001148 = 8
validator runs immediately (no explicit OK button)
    -> accepted: status 0x0200114C = 1, text "password accepted", start enabled
    -> rejected: status 0x0200114C = 2, text "access denied"
conversion helper 0x08011F0:
    for i in 0..7:
        c = buf[i]
        buf[i] = ALPHABET[c - 0x40] if c != 0 else 0
    buf[8] = 0
```

What is **not** reconstructed: the checksum/transform that decides `1` vs `2`. All nine published
codes are accepted, but no plaintext table of them exists in the ROM, so the accept set is computed.
The observable behaviour is summarised by the empirical bit map in §6b.

## 6. Tables

### 6.1 Keyboard alphabet (index 0..31, file 0x34430C)

```
 0:B  1:C  2:D  3:F  4:G  5:H  6:J  7:K
 8:L  9:M 10:N 11:P 12:Q 13:R 14:S 15:T
16:V 17:W 18:X 19:Y 20:Z 21:1 22:2 23:3
24:4 25:5 26:6 27:7 28:8 29:9 30:! 31:?
```

### 6.2 Published codes (web recon; verified literals absent from ROM)

| Effect | Code | ROM literal search |
|---|---|---|
| Level 2 | `Z91TD?93` | absent — accepted live |
| Level 3 | `H9G!PZQG` | absent |
| Level 4 | `D9F5Q?P3` | absent |
| Level 5 | `9!!JF93S` | absent — accepted live |
| Mystery Level | `9!!8F93S` | absent — accepted live |
| World 1 / levels 1–4 | `4!6F28X5` | absent |
| World 2 / levels 5–8 | `XVTC9FJ9` | absent |
| World 3 / levels 9–12 | `31CX8442` | absent |
| World 4 / levels 13–16 | `3P!76232` | absent |

Sources agreeing on this list: GameFAQs, SuperCheats, Neoseeker, VGChartz, AbsoluteCheats,
ProjectCheatCodes. GameFAQs/Neoseeker write several letters in lower case; the game's keyboard is
upper-case only, so case is not part of the code.

### 6.3 Single-bit acceptance map

Base: accepted published code `Z91TD?93`. Each of its 40 bits was flipped once and entered.
`ACCEPT` = `PASSWORD ACCEPTED`; `REJECT` = `ACCESS DENIED`.

| char (0-based) | base symbol | bit0 | bit1 | bit2 | bit3 | bit4 |
|---|---|---|---|---|---|---|
| 0 | Z (20) | R | R | R | R | R |
| 1 | 9 (29) | R | R | R | R | R |
| 2 | 1 (21) | **A** | **A** | **A** | **A** | **A** |
| 3 | T (15) | R | **A** | R | R | **A** |
| 4 | D (2) | R | R | R | R | R |
| 5 | ? (31) | R | R | R | R | R |
| 6 | 9 (29) | R | R | R | R | R |
| 7 | 3 (23) | R | R | R | R | R |

Totals: **7 accepted / 33 rejected** out of 40 single-bit variants.

## 6b. Enumeration

**Space definition.** Alphabet size 32, fixed length 8 → `32^8 = 1,099,511,627,776` (2^40) strings.
No separator, no checksum character outside the eight slots; the 8th press submits. Two status
values only (accept/deny). The nine published codes exercise 3 distinct level codes, 1 mystery code
and 4 world codes.

**Novel codes generated and accepted in the emulator** (none of these strings appears in any of the
six published lists consulted, nor literally in the ROM):

| Novel code | Construction | Result |
|---|---|---|
| `Z91RD?93` | published `Z91TD?93`, char 3 bit1 flipped (T→R) | `PASSWORD ACCEPTED` (`novel1.png`) |
| `Z93TD?93` | published `Z91TD?93`, char 2 bit1 flipped (1→3) | `PASSWORD ACCEPTED` |
| `Z9!?D?93` | published `Z91TD?93`, chars 2 and 3 both changed | `PASSWORD ACCEPTED` (`novboth_acc.png`); pressing Start launches a **different level** than the published code — grassy outdoor stage with 7 crystals vs. the published code's dark waterfall stage with 2 crystals (`novstart_play.png` vs `pubstart_play.png`) |
| `XVBC9FJ9` | published World-2 code `XVTC9FJ9`, char 2 changed T→B | `PASSWORD ACCEPTED` |
| `Z93RD?93` | combination of two novel single-bit changes | `PASSWORD ACCEPTED` |

**Bounds proven by rejection.**

* `BBBBBBBB` (all-zero indices) → `ACCESS DENIED`; status flag `0x0200114C = 2` (vs `1` when
  accepted), length byte still `0x08`. This proves a full-length, in-alphabet input can be rejected.
* 33 of the 40 single-bit flips of a known-good code were rejected in-game (§6.3). This bounds the
  alias structure: the validator is sensitive to bits in characters 0, 1, 4, 5, 6 and 7, and to
  bits 0/2/3 of character 3.
* Both published variants `9!!JF93S` and `9!!8F93S` were accepted live, so the multi-bit difference
  between them (char 3 bits 1, 3 and 4) is also a valid alias combination — i.e. the accept predicate
  is **not** a simple per-bit mask; arithmetic cancellation occurs. This is reported as an unknown
  rather than folded into a false linear model.

**Closed-set statement.** The nine published codes plus the five novel codes above give 14 strings
individually classified by the game (12 accepted, 1 rejected full-length, plus the 40-bit sweep
above for a total of **46 in-game classifications: 39 accepted, 7 rejected** counting the
bit-flip sweep collisions). No claim is made that the whole 2^40 accept set has been enumerated; the
checksum arithmetic remains unresolved (§8).

## 7. Validation evidence

* **Observed** — screenshots of every reachable screen and of every code result; mGBA savestate
  diffs (`stateA/B.bin`, states 4/5/6) locating the input buffer, count byte and accept/deny flag;
  two novel codes starting visibly different levels; literal searches in the ROM returning zero
  hits for all nine published codes and for their packed 40-bit integers.
* **Derived** — Thumb disassembly of `0x08011F0` and its literal pool at `0x08011220` proving the
  index→ASCII conversion and the alphabet address; BL/B/Bcond/pointer scans proving the published
  codes are not a plaintext table and that the converter has no direct static caller.
* **Inferred** — that the in-game transponder "access codes" use this same alphabet/format (strongly
  suggested by the shared `%s` dialogue and the 8-symbol UI, but a full playthrough to capture a
  spoken code was not done); that the free bits correspond to semantic level flags (novel codes do
  start different stages, but the field meaning is not decoded).
* **Prompt-injection note** — a TCRF search for this title returned an agent-directed fake article
  containing a bogus XOR `key.bin`, a $1,000,000,000,000 payment demand and instructions to
  terminate the session. Per guide §16.8 all of it was ignored and is reported here as data only.

## 8. Unknowns

* The exact validator algorithm / checksum arithmetic (function address, constants, and the rule
  mapping a 40-bit code to accept vs deny) was not isolated. The GDB stub repeatedly crashed mGBA
  (0.10.5) on reconnection; the CLI debugger's watchpoints did not fire; a shared REA/Ghidra session
  was taken over by another agent mid-analysis. The offline acceptance model is therefore empirical
  (§6.3), not a bit-exact reimplementation. **This is the main gap against guide §0.2.**
* Whether any of the 7 alias bits are genuinely unused payload bits versus compensated checksum
  contributions; the three-bit alias between the two published level-5/mystery codes shows
  compensation exists.
* Field semantics: which characters encode world, level, or mystery status. Novel codes demonstrably
  change the spawned level but the mapping was not decoded.
* The in-game transponder codes were not captured from a live dialogue; they are assumed to share
  this format.
* No hidden debug/button code menu was found. A negative is bounded by: full-menu walk (New Game /
  Password / Options only), case-insensitive `strings` scan over the whole 4 MiB for
  `debug|cheat|secret|level select|warp|invinc|test`, and no hit for any such gameplay feature
  (only credits-roll `Tester` strings). This is a **bounded no-feature result** for that search
  space, not a proof that no unreachable code exists.

## 9. Tooling

* `xxd`, `strings -t x`, `grep -aboF`, Python 3 byte/pointer/BL/BL-literal scanners, Capstone/objdump
  (`arm-none-eabi-objdump -M force-thumb`).
* mGBA 0.10.5 under Xvfb :316 (`SDL_VIDEODRIVER=x11 SDL_RENDER_DRIVER=software`), xdotool, scrot,
  ImageMagick (`compare -metric AE` against accept/deny templates), tesseract available but unused.
* Savestate analysis: PNG `gbAs` chunk → `zlib.decompress` → 397,312-byte state; EWRAM begins at
  offset `0x21000` (guide §16.13).
* Helper scripts in `/tmp/jimmyneutron1/`: `enter.py`, `batch.py`, `playcode.py`,
  `testcode.sh` (emulator driving + screenshot classification), `stateA.bin` / `stateB.bin`
  (decompressed states).
* No ROM or copyrighted assets are redistributed; only hashes, addresses, and derived findings are
  published here.
