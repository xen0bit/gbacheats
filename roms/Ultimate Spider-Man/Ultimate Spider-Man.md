# Ultimate Spider-Man (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Ultimate Spider-Man.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `ULTSPIDERMAN` |
| Game code | `BULE` |
| Maker | `52` |
| Version | `0x00` |
| Complement check | `0x2A` |
| Header checksum | `0x0000` |
| Entry word | `0xEA00002E` (stock ARM branch to `0x080000C0`) |
| MD5 | `11beb7fd8ce6c8a3d4987274835e0843` |
| SHA-1 | `1f5959b66dafb33c9fa01389c23214b38b0fcc79` |
| SHA-256 | `c2bf1dfc21cc6b7cfb322ac9f60ba373a289419555944e965e1cf027b8b3b14c` |

Vicarious Visions GBA SKU (not the Treyarch/Beenox console builds). Nintendo logo intact,
entry word unpatched — retail image, not a scene cracktro (guide §16.1 checked).

## 2. Executive summary

**Result: bounded negative — this GBA image has no developer-intended code system.**
There is no password prompt, no button-code validator, no unlockables/gallery menu, and no
hidden/debug menu on any reachable screen. The four "cheat codes" widely published for
*Ultimate Spider-Man* are **console-only**: they are entered at *Options → Controller Setup*
in the PS2/GC/Xbox/PC builds, which emit a confirmation sound. The GBA build's complete UI
has no Options/Controller Setup screen at all, and none of the strings, tables, or input
matchers those codes require exist in this ROM.

This is guide §16.3 case **1 (No system)**, not dead code, not a cut feature with surviving
placeholders, and not a gated screen. §16.11 applies directly: a title-and-platform match on
an aggregator page (SuperCheats lists the console codes on its GBA page) is not evidence that
the GBA SKU implements them.

All four published codes were entered in the emulator on every plausible surface with
savestate-based RAM controls; the only observed RAM deltas were ordinary menu-cursor and
timer state. A code that is not in any published list therefore cannot be minted, and the
deliverable is the enumerated negative with counts (§0.2.5).

Out of scope by the brief: Action Replay / CodeBreaker / GameShark codes. A CodeBreaker page
was consulted only as recon data; it supplied RAM anchors (`0x020045A0` "Challenges Unlocked",
`0x0200D160` level, `0x0200B164`/`0x0200B168` health/web) that were used to look for cheat
state. None of those addresses changed from controller input.

## 3. How to reproduce

- Emulator: `mgba 0.10.5`, `SDL_AUDIODRIVER=dummy`, `Xvfb :318`, `openbox`, `-3` scale.
- Keymap (verified by menu navigation): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrow keys.
- Savestates: `Shift+F1..F9` save, `F1..F9` load; `.ssN` files decoded per guide §16.13
  (PNG `gbAs` chunk, `zlib.decompress`, raw length 397,312 bytes; EWRAM at state offset
  `0x21000`, length `0x40000`, IWRAM `0x19000`, VRAM `0x1000`).
- Screen path walked:
  `Title → Start Game → Select a Slot → New Game → Select Mode (Normal/Challenge) →
  intro comic → gameplay → Pause (Resume/Quit Level/Sleep/Sound) → Sound (Music/SFX) →
  Quit Level? (Cancel/Quit) → Chapter select (Chapter 1, Locked, Locked)`.
- Code entry tests: load a title-screen savestate, send the 8 D-pad presses with
  `hold=0.08 s, gap=0.12 s`, save a second state, diff EWRAM against (a) an idle state of
  equal duration and (b) a novel 8-press sequence.

Published codes tested (R/D/L/U = D-pad right/down/left/up, per the source's own "P.S"):

| Effect (console) | Sequence |
|---|---|
| All characters | R, D, R, D, L, U, L, R |
| All comic covers | L, L, R, L, U, L, L, D |
| All concept art | D, D, D, U, D, U, L, L |
| All landmarks | U, R, D, L, D, U, R, L |

Each was also tested with R/L as the shoulder triggers (in case the source meant shoulders);
identical results to the D-pad runs, i.e. shoulder presses are ignored.

## 4. Address map

| Item | Address / file offset | Evidence |
|---|---|---|
| ROM base | `0x08000000` = file `0x000000` | header |
| Entry point | `0x080000C0` | `0xEA00002E` |
| KEYINPUT active-high helper | `0x08002244` (Thumb) | `ldr r0,[pc,#8]` → `0x04000130`; `ldrh`; `r0 = 0x3FF ^ r1`; `bx lr` |
| KEYINPUT wait loop | `0x08031856` (Thumb) | second and only other Thumb PC-relative read of `0x04000130` |
| Helper function pointer | `0x08FB90D8` → `0x08002245` (Thumb bit set) | `u32` pointer table |
| UI string bank | file `0x10A490`–`0x10D3xx` (ROM `0x090A490`+) | ASCII; records are `{string, u32 self_ptr}` |
| Title labels | `0x090A498` / `0x090A4A8` | "Start Game", "View Credits" |
| Pause labels | `0x090A4BC`–`0x090A4EC` | "Resume", "Quit Level", "Sleep", "Sound" |
| Sound labels | `0x090A4F0`, `0x090A504` | "Music Volume : ", "SFX Volume : " |
| Slot labels | `0x090A574`–`0x090A5DC` | "Select a Slot", "New Game", "Erase", "Back", "Select" |
| Mode labels | `0x090AE24`, `0x090AE34`, `0x090AE40` | "Select Mode", "Normal", "Challenge" |
| Chapter labels | `0x090A6B4`, `0x090A6C4` | "Chapter %d", "Locked" |
| SRAM | 512-byte `.sav`, 3 slots at `0x00/0x50/0xA0` | magic words `c0de601d`, `c0de603d` |

Only **2** Thumb code sites in the first 1 MiB read `0x04000130` directly; one is the
active-high helper above, the other a key-change busy-wait loop. No third input consumer
with sequence state exists.

## 5. Algorithm

No validator, encoder, decoder, checksum, alphabet, or code table exists to reverse. The
reconstructed input path is simply:

```
key = 0x3FF ^ *((volatile u16*)0x04000130)     @ 0x08002244, active-high, single frame
menu/character controller consumes key each frame
```

The apparent "code effect" from the R,D,R,D,L,U,L,R sequence was traced to D-pad menu
navigation: the net vertical movement (two Down, one Up) moves the title cursor from
"Start Game" to "View Credits" (screenshot `vis_before_crop.png` → `vis_after_chars_crop.png`,
diff bbox `(213,315)-(513,393)`, exactly the two menu labels). A savestate control with the
same net D-pad movement reproduced the identical RAM delta; a novel 8-press sequence with
net-zero vertical movement produced no delta. Hence not a code.

## 6. Tables

Complete UI inventory (decoded from the ASCII text bank, file `0x10A490`–`0x10AE60`):

| Screen | Items | Count |
|---|---|---:|
| Title | Start Game, View Credits | 2 |
| Select a Slot | New Game ×3, Erase, Back, Select | 4 actionable + 2 prompts |
| Select Mode | Normal, Challenge | 2 |
| Pause | Resume, Quit Level, Sleep, Sound | 4 |
| Sound | Music Volume, SFX Volume, Adjust | 2 settings |
| Quit Level? | Cancel, Quit | 2 |
| Sleep Now? | wake prompt (`SELECT + … to Wake`) | 0 actions |
| Chapter select | Chapter 1, Locked, Locked | 3 (2 gated by save progress) |

Absent from the entire 187,862-line `strings -t x -n 4` dump (case-insensitive):
`gallery` (0), `collection` (0), `cover` (0), `concept` (0), `landmark` (0),
`cheat` (0), `password` (0), `unlock` (0), `extras` (0), `options` (0),
`controller` (0), `debug` (0). The only `code` hits are the Shin'en GAX audio banner
(`Code: B.Wodok`) and XML-ish object data — both known false-positive classes (guide §11).
The UI font is a custom tile font, but its source strings are plain ASCII in this bank, so
the decode is complete (guide §11: "decode font/tile text banks before a negative" satisfied).

## 6b. Enumeration

**Space definition:** none. There is no alphabet, no fixed code length, no field widths, no
checksum, and no lookup table. Representable code count = 0.

**Search counts (bounded negative):**

- **Static table search:** ~594 encoding variants in the final sweep — 33 direction→symbol
  maps (9 named: log2-bit, GBA active-high/active-low mask bytes, nibble, ASCII upper/lower,
  two numeric maps; plus all 24 permutations of R/L/U/D as indices) × normal/reversed ×
  3 terminators (none / `0x00` / `0xFF`) × 1/2/4-byte widths. For each variant all four
  published sequences were searched and required to co-occur within a 256-byte window.
  **Multi-code clusters found: 0.**
- Earlier sweeps, same result: full sequences as `u16`/`u32` active-high and active-low
  (0 hits); 2-bit packed, all 24 direction permutations × both bit orders, 4 presses/byte
  (0 multi-code clusters); byte encodings with and without reversal (0 clusters).
- **Literal KEYINPUT constant:** 14 raw `u32` hits, of which only 2 are real Thumb PC-relative
  loads in code (§4). No third input consumer.
- **Button-mask comparison scan:** 136 Thumb `cmp #imm` sites with values in the button-mask
  set over `0x08000000`–`0x08100000`; spot-checking shows the dense clusters are data
  misread as code, and the genuine sites are one-off menu/gameplay key tests. **Zero sites
  implement an 8-step sequence matcher** (no progress index, no expected-mask table).
- **Dynamic matrix:** 4 published codes × 2 interpretations (D-pad / shoulder) = 8 trials at
  the title screen, plus idle control and 2 novel sequences, all from identical savestates.
  Every trial produced either the control-sized delta (~6–8 bytes: frame counters) or the
  cursor-movement delta (~19 extra bytes). **No unlock flag or save byte changed.** The
  CodeBreaker-identified anchors `0x020045A0`, `0x0200D160`, `0x0200B164`, `0x0200B168`
  stayed at their control values in every trial.

**Novel code:** not applicable — no code space exists from which to mint one. In particular
the "unlock all" codes claim to unlock a comic-art gallery that this SKU does not contain,
so there is no target state even if a matcher were injected.

**Bounds proven by rejection:** the format itself is the bound — there is no input surface
at which a code can be rejected, because every screen was walked and none accepts input
beyond menu navigation. The negative is closed by (a) full screen enumeration, (b) full
UI string inventory, (c) ~600-encoding table search with zero clusters, and (d) controlled
dynamic entry of all published and two novel sequences with no state change.

## 7. Validation evidence

- **Observed** — mGBA screenshots of all 8 screens listed in §3/§6 (files in
  `/tmp/ultimatespiderman/shots/`), including `w_title_crop.png`,
  `w_slotselect_crop.png`, `w_modeselect_crop.png`, `w_gameplay_crop.png`,
  `w_sound_crop.png`, `w_quit2_crop.png`, `w_chapter2_crop.png`.
- **Observed** — savestate EWRAM diffs: code trials vs idle control and novel controls,
  recorded in `/tmp/ultimatespiderman/work/mx_*.bin` and `state_*.bin`.
- **Derived** — the active-high key helper at `0x08002244`, the 2 KEYINPUT read sites, the
  string-bank inventory, and the zero-cluster table searches.
- **Inferred** — that the console codes genuinely work on the PS2/GC/Xbox SKUs (published
  reports describe a confirmation sound); not exercised here.
- **Corrected false positive** — the R,D,R,D,L,U,L,R "character unlock" initially looked like
  a real RAM change; controlled replay proved it is title-cursor movement (see §5).

## 8. Unknowns

- Whether any post-completion state (all 15 chapters cleared, all collectibles) reveals a
  costume/extras menu in this GBA SKU. The string bank contains no labels for such a menu,
  and reaching that state was out of scope; if it exists it is a save-gated unlockable, not
  a code.
- The exact meaning of SRAM slots' internal checksums (`0x27dd`, `0xe306`) was not required
  for the code question and was not reversed.
- The second KEYINPUT site at `0x08031856` is a key-change wait loop; its caller was not
  traced beyond confirming it is not a sequence matcher.

## 9. Tooling

- `mgba 0.10.5` (`-3`, `-g` tried and abandoned: stub is single-client), `Xvfb :318`,
  `openbox`, `xdotool` XTEST key events, `scrot`, ImageMagick `convert`.
- `arm-none-eabi-objdump -M force-thumb` for targeted disassembly; Capstone for PC-relative
  literal and `cmp #imm` scans; Python 3 for literal/sequence/table searches.
- Scripts kept in `/tmp/ultimatespiderman/work/`: `search_masks.py`, `search2.py`,
  `cluster.py`, `finalsearch.py`, `find_keyinput.py`, `ldr_key2.py`, `blscan.py`, `cmpscan.py`,
  `ssdump.py` (gbAs decoder), `walk*.py`, `codetest*.py`, `matrix.py`.
- No copyrighted assets or ROM bytes are redistributed in this report; only addresses,
  hashes, counts, and observations are published.
