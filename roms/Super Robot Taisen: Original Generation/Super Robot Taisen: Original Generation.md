# Super Robot Taisen: Original Generation (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Super Robot Taisen: Original Generation.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `SRTOG` |
| Game code / maker | `AOGE` / `EB` (Banpresto/Enterbrain); `file(1)` reports `AOGEEB, Rev.00` |
| Version | `0x00` |
| Header checksum | `0x0000` (rebuilt-header artifact, guide §16.1) |
| Complement byte | `0x1F` (computed `0x38` from bytes `0xA0..0xBC` — header was edited; most likely a region/serial patch) |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`, not a cracktro — guide §16.1) |
| MD5 | `7146102bb4d37865198dbe6881d2af9a` |
| SHA-1 | `8512206d86b3e25d86e71fbff6c56705b1bb6428` |
| SHA-256 | `01a80584a608bd8de74967e46d1aaec0cbd487871918d8dd465e7f150ac2c568` |

## 2. Executive summary

This ROM has **no password / code-entry system and no hidden debug menu reachable by
controller input**. There is no on-screen alphabet, no code validator, no password
table, and no debug-gate branch anywhere in the reachable code. The only "cheats"
that exist are (a) two controller combos that are system functions, and (b)
progression-gated unlockables stored in the battery save.

Confirmed in-game button code:

* **`A + B + Start + Select` held together = soft reset** to the Banpresto logo.
  Observed twice, from a battle map and from the title screen. It is a
  developer-intended system shortcut, not a content cheat.

Claimed but **not reproduced** in this revision (GameFAQs board):

* From the Banpresto logo, `A+B+Start+Select` while holding `Start` is said to jump
  directly to the quicksave. Tested with a real save present under four timing
  variants (§6b); the game booted to the normal title screen every time. Recorded as
  unverified, not as working.

Published cheats for this title are out of scope or progression-based:

* GameFAQs/VGChartz list only **New Game+** (beat the game with Kyosuke and Ryusei)
  and **Secret Robots/Characters/Weapons/Items** (stage/level/kill conditions).
  These are save-flag unlockables (guide §16.18), not input codes.
* Neoseeker/Akurasu CodeBreaker and GameShark lists are cheat-device codes — excluded
  by the task scope.
* The widely published "System menu → Down, Up, Left, Right, L, R → music player"
  button code belongs to **Original Generation 2**, not this game. Entered verbatim
  in OG1's battle System menu: **no effect** (§6b).

All in-game text is 8-bpp tile-index data, so `strings` finds zero UI words; the
font/VRAM bank was decoded before the negative was accepted (§9).

## 3. How to reproduce

* mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Keys held 60–300 ms; chords held ~250 ms.
* Reproduce the walk: boot → title (`PRESS START`) → Start → main menu
  (`NEW GAME / LOAD / CONTINUE`) → A on NEW GAME → scripted battle/dialogue →
  advance dialogue with A → map → A on an empty square → map menu
  (`End Phase / Units / Mission / Search / System / Save`) → System
  (`Grid / BGM / Buttons`).
* Soft reset: at any point press and hold `x`+`z`+`Return`+`BackSpace` together.
* RAM evidence was taken by diffing mGBA `.ssN` savestates (PNG with zlib `gbAs`
  chunk — guide §16.13), not by trusting screenshots alone.

## 4. Address map

### ROM / code

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Stock ARM entry `0xEA00002E` → crt0 at `0x080000C0` | Derived (disassembly) |
| `0x080001D0` | Thumb `main`, called through literal `0x080001D1` in crt0 pool | Derived |
| `0x08011A50`, `0x0803A570` | Early init / boot check calls from `main` | Derived |
| `0x0819ADD7` | Only non-crt0 byte occurrence of `0x04000130` in the whole ROM — inside a **data** region, not code (disassembly there is non-instructions) | Derived |

### IWRAM (state offsets: IWRAM begins at raw `0x19000`)

| Address | Meaning | Evidence |
|---|---|---|
| `0x03007348` | **Key-update routine**, copied to IWRAM: reads `KEYINPUT`, computes active-high `pressed`/`held`/double-click fields | Derived (Thumb disassembly) |
| `0x0300739C` | Literal `0x04000130` (`KEYINPUT`) | Derived |
| `0x030073A0` | Literal `0x03FF` (10-button mask) | Derived |
| `0x030073A4` | Literal `0x02003890` (input struct pointer) | Derived |
| `0x030073D8+` | Neighbouring IWRAM routines use the same struct (history push/pop) | Derived |

Derived key-update pseudo-code (from `0x03007348`):

```
cur  = ~KEYINPUT & 0x3FF                 ; active-high mask
 prev    = input[+6]
 input[+4] = cur & ~prev                 ; edge-triggered "pressed"
 input[+6] = cur                         ; held
 input[+10] = input[+4]; input[+12] = cur; input[+14] = double-click press
```

| EWRAM address | Field | Width |
|---|---|---|
| `0x02003890 +0` | hold threshold | u8 |
| `+1` | hold counter | u8 |
| `+2` | double-click threshold | u8 |
| `+3` | double-click counter | u8 |
| `+4` | pressed this frame | u16 |
| `+6` | held (active-high) | u16 |
| `+8` | double-click press | u16 |
| `+10/+12/+14` | previous pressed / held / double-click | u16 |

### Savestate layout (mGBA 0.10.5, 397,312-byte `gbAs` chunk)

| Raw offset | Region |
|---|---|
| `0x0000` | CPU/register header |
| `0x0400` | OAM |
| `0x0800` | Palette RAM (512 × BGR555) |
| `0x0C00` | I/O |
| `0x1000` | VRAM (0x18000) |
| `0x19000` | IWRAM (0x8000) |
| `0x21000` | EWRAM (0x40000) |

## 5. Algorithm (input system, the only validator-like code found)

The input layer is a generic key-state tracker with edge detection and a
double-click/two-tap detector. It is **not** a cheat validator: it never compares
the key mask against a constant sequence. It is the only code in the image that
reads `KEYINPUT`.

Key mask convention (active-high, from `0x03007348`):

| Button | Bit | Mask |
|---|---:|---:|
| A | 0 | `0x001` |
| B | 1 | `0x002` |
| Select | 2 | `0x004` |
| Start | 3 | `0x008` |
| Right | 4 | `0x010` |
| Left | 5 | `0x020` |
| Up | 6 | `0x040` |
| Down | 7 | `0x080` |
| R | 8 | `0x100` |
| L | 9 | `0x200` |

Soft-reset combo = `0x0001 | 0x0002 | 0x0004 | 0x0008 = 0x000F`.
Its exact branch was **not** isolated statically (no `cmp #0x0F` exists anywhere in
the 16 MiB image, so the comparison is register-based or lives in compressed/boot
code); the behaviour itself is Observed (§7).

## 6. Tables

| Item | Detail |
|---|---|
| Password alphabets / code tables | **0 found** (see §6b counts) |
| Button-code sequence tables | **0 found** |
| Hidden/debug menu entries | **0 reachable** |
| Unlockables (progression, save-flag) | New Game+ (clear with Kyosuke and Ryusei); Secret Robots/Characters/Weapons/Items (stage-specific conditions e.g. R-Gun on stage 30, Valcion Kai <10% HP on stage 28, Shishiso Blade 50 kills + Zengar on stage 26 on Hard, Hero Symbol level 35 on stage 35, Kai on Kyosuke route). Source: GameFAQs/Freeola — **Inferred** for this exact revision (not played through). |
| In-game button combos | Soft reset `A+B+Start+Select` — **Observed**. Quicksave-jump at logo — claimed, **not reproduced**. `A+R` dialogue skip and `A+B+Start+Select`+hold-Start quicksave load — board claims, **not tested exhaustively**. |

## 6b. Enumeration

This is a **bounded negative with counts**, as permitted by the task brief and
guide §0.2(5), because no code system exists to mint a novel code against.

### Screens walked (all reachable surfaces, 12 distinct screens)

1. Title — `PRESS START` (game boots here after soft reset)
2. Banpresto logo (boot/soft-reset interlude)
3. Main menu — `NEW GAME / LOAD / CONTINUE` (CONTINUE greyed with no save)
4. Intro battle map + scripted dialogue (SEAN, ELZAM, VCC boxes)
5. Save confirmation — `Save? Yes / No`
6. Save confirmation — `Proceed to save? Yes / No`
7. Battle map, cursor idle
8. Movement-range overlay (green tiles) after selecting a unit
9. Unit action menu — `move / spirit / status`
10. Unit status — `Gesperst Mk II · R / Elzam`, HP/EN/Will/SP/etc.
11. Terrain info — `Def ±0% / Hit ±0% / HP ±0% / EN ±0% / Space` (B on empty square)
12. Map menu — `End Phase / Units / Mission / Search / System / Save`
    * Mission sub-screen — win/lose conditions
    * System sub-screen — `Grid On/Off · BGM Keep/Change · Buttons Normal/Left`

No screen anywhere in this walk contains a text-entry field, a code pad, a symbol
alphabet, a validator prompt, or a debug/menu entry beyond those listed.

### Search-space counts

| Search | Space checked | Hits |
|---|---|---:|
| `strings -a -t x -n 5` | all 16,777,216 bytes → 39,604 lines | **0** lines containing `password`, `cheat`, `debug`, `secret`, `sound test`, `invalid`, `menu`, `code`, `unlock`, `master` |
| Plaintext words under 12 simple encodings (XOR/add/sub 0xFF, nibble-swap, UTF-16LE/BE, ±0x20/0x40/0x80, high-bit) for `DEBUG`, `PASSWORD`, `SECRET`, `SOUND`, `CHEAT`, `ENTER`, `SPECIAL`, `BATTLE`, `GALLERY`, `EXTRA` | 16 MiB × 12 transforms | 0 credible hits (isolated 1–150-byte coincidences in compressed data) |
| Password/code-entry alphabet (32/36/40-symbol table near UI or validator) | whole ROM, ASCII/font-index/UTF-16 forms | **0** |
| Full published SRW button sequence `Down,Up,Left,Right,L,R` as u16 masks (forward, reverse, active-high, active-low, 1-byte/press), lengths 2–6 | 16 MiB | **0** full-length (6) or length-3/4 hits; one length-2 coincidence at `0x08FCEDF0` in compressed data |
| Thumb `cmp Rn,#imm8` with any keypad mask (`0x1..0x3FF`, all 16 common combos incl. `0x0F`, `0x300`, `0x308`, `0x30C`) | 8,388,608 aligned halfwords | **0** |
| `ldrh [input+4/6/8/10/12/14]` followed within 6 instructions by `cmp` with a keypad mask | 8,388,608 halfwords | 13 `ldrh→cmp` pairs; **all 13 compare `#0x28`**, none a keypad mask |
| u16 mask-table runs (values ≤0x3FF, ≤4 bits) | 12,963 candidate runs | all fall inside ordinary Thumb code (`0x0804xxxx`–`0x0806xxxx` etc.) — **0** validated code tables |
| `0x04000130` literal in ROM code | all byte offsets | 2 hits: crt0 multiboot check `0x080007D8`, and data at `0x0819ADD7`; **0** in the game engine — key reads are performed from the IWRAM copy at `0x03007348` |

### Rejection / negative tests actually entered in the emulator

| Input | Where | Result |
|---|---|---|
| `Down,Up,Left,Right,L,R` (OG2's published music-player code) | OG1 battle System menu | Rejected — System menu unchanged, no music player |
| `Start+Select` | main menu | Rejected — no change |
| `L+R+Start+Select` | title / main menu | Rejected — no change |
| `A+B+Start` | title / main menu | Rejected — no hidden screen |
| `A+B+Select` | title / main menu | Rejected — no hidden screen |
| `L+R` | title / main menu | Rejected — no change |
| Logo quicksave-jump, 4 timing variants (Start first; full chord then hold Start; Start held through reset+logo; chord at logo fade) | Banpresto logo, real save present | Rejected — normal title screen each time |
| `A+B+Start+Select` | battle map and title | **Accepted** — soft reset to Banpresto logo (2/2) |

The negative is therefore bounded: the entire reachable UI (12 screens) was
walked; the entire 16 MiB image was searched for password alphabets, code tables,
button sequences and keypad-mask comparisons; and every plausible button
combination was pressed in the emulator. No novel code could be minted because no
code format exists to mint against.

## 7. Validation evidence

* **Observed** — emulator screenshots and savestate diffs: all 12 screens; soft
  reset (2 times); rejection of the OG2 code and 5 adjacent combos; palette/VRAM
  contents.
* **Derived** — Thumb disassembly of the IWRAM key routine `0x03007348` and its
  literals; stock crt0/entry word; `strings`/binary-scan counts; absence of
  `0x04000130` in engine code.
* **Inferred** — unlockable conditions (from GameFAQs/Freeola, not replayed to
  endgame); the quicksave-jump board claim (tested and rejected here); the precise
  soft-reset branch (behaviour proven, instruction not isolated); header edit
  rationale.

## 8. Unknowns

* The exact instruction that implements the soft reset was not isolated; the
  behaviour is certain but the branch address is not.
* The intermission/post-battle menu, "Units", "Search", and the full 40+ hour
  campaign were not played; additional progression-gated content may exist there.
  None of these are input codes by construction (save-flag unlockables).
* Whether the reported Banpresto-logo quicksave jump is version-specific or was
  removed in this `AOGE` revision; four timings failed.
* Text banks are 8-bpp tile indices; the full character↔tile table was not dumped
  (the visible font/UI tiles were decoded and rendered, which was sufficient to
  confirm there is no plaintext code system).

## 9. Tooling

* `md5sum`, `sha1sum`, `sha256sum`, `file`, `xxd` — Phase 0.
* `strings -a -t x -n 5`, `grep` — text scan (and its negative).
* `arm-none-eabi-objdump -M force-thumb` — crt0, `main`, IWRAM key routine.
* Capstone + custom Python (`cap.py`, `refs.py`, `keycmp.py`, `combos.py`,
  `maskscan.py`, `seqsearch.py`, `encsearch.py`, `enc2.py`) — literal/pattern scans.
* REA/Ghidra 12.1.4 (`open_binary`, `binary_session`; session closed at end) —
  availability check for deeper decompilation; not needed after the IWRAM routine
  was found.
* mGBA 0.10.5 (`-3`), Xvfb `:318`, openbox, xdotool, `import`/scrot — emulator
  walk, key chords, screenshots.
* Custom `ss.py` / `diff.py` / `vram2.py` — mGBA savestate `gbAs` extraction, RAM
  diffing and 8-bpp VRAM rendering with palette at raw `0x0800`.

Screenshots kept under `/tmp/opencode/srtog/` (`t3.png`, `ng1.png`, `sys1.png`,
`systemmenu.png`, `mapmenu.png`, `mission.png`, `reset.png`, `code1.png`,
`terrain.png`, `vram8_big.png`, etc.).

## 10. Legal note

No ROM image, extracted graphics, or game assets are reproduced here. Only
hashes, addresses, algorithms, tool commands and observations are published.
