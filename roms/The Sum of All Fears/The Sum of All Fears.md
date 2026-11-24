# The Sum of All Fears (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/The Sum of All Fears/The Sum of All Fears.gba` |
| Size | 8,388,608 bytes (`0x800000`, 8 MiB) |
| `file(1)` | Game Boy Advance ROM image: "SUM ALL FEAR" (AA6E41, Rev.00) |
| Header title | `SUM ALL FEAR` (offset `0xA0`) |
| Game code | `AA6E` (USA) |
| Maker | `41` |
| Version / complement / checksum | `0x00` / `0xC3` / `0x0000` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| MD5 | `e2970509f5671dd267f1c5c5902710e3` |
| SHA-1 | `364b880a0457cec827929247b4885d0351fa2982` |
| SHA-256 | `0a1b8862cf09f26416e4cd1a7e7c0f340b1be779f86f1d3d7ed902315965d873` |

No cracktro/appended trainer was found; the first 4 KiB is a normal crt0.

## 2. Executive summary

This GBA SKU has **one** developer cheat system: a **six-entry pause-menu button-code
table**. There is no password entry screen and no hidden debug menu. The published
GameFAQs/GameGenie "invisibility" sequence does **not** exist in this build.

The six codes are stored as arrays of active-high GBA key masks (`A=1,B=2,Select=4,
Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`). A single validator
at `0x0800CF84` walks all six entries, compares `expected & (pressed & 0x3FF)`, advances
a per-entry progress counter on a match and resets it to zero on a mismatch. Completion
calls a per-entry function pointer that writes a value `1..6` to `0x02002840` and
dispatches through a seven-way jump table at `0x0803916C`.

- `L,R,Up,Up` (unpublished here) → mission success, primary objective only.
- `L,R,Down,Down` (the one published GBA code) → mission success, both objectives.
- `L,L,R,R,Down,Down`, `L,Select,L`, `R,R,L,R,Up`, `R,Select,R` (none published) →
  each toggles one bit in the global flag byte `0x0200C7C0` (bits 3, 1, 2 and 4
  respectively) and resumes play.

All six were entered on the real pause screen in mGBA and verified by savestate RAM
diffs. Bounds were proven by rejected inputs (wrong key, unmatched published code,
chord semantics). The accepted space is exactly 6 sequences out of the
`2^(10*16)` representable mask arrays; there is no checksum or generator.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:316`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
  Keymap used: A=`x`, B=`z`, Select=`BackSpace`, Start=`Return`, L=`a`, R=`s`,
  D-pad = arrow keys.
* Path: boot → choose language (`English`, A) → main menu → Single Player →
  game slot 1 → Campaign → Mission 1 → briefing (A) → Team Setup (fill 4 slots with
  A, then Start) → in mission → **Start to pause** → enter a sequence.
* Save a state at the pause screen (`Shift+F1`); `F1` restores it. States are PNG with
  a zlib `gbAs` chunk; 397,312-byte state for this 8 MiB ROM. EWRAM starts at state
  offset `0x21000`, IWRAM at `0x19000`.
* Code entry: hold each button ~100 ms with ~130 ms gaps. Example: `a s Down Down`.
* Screenshots of every result were in `/tmp/sumofallfears/`
  (`code0_LRUU.png`, `code1_LRDD.png`, `code2_LLRRDD.png`, `code3_LSelL.png`,
  `code4_RRLRU.png`, `code5_RSelR.png`, `reject_bad.png`, `reject_inv.png`,
  plus the menu walk `s1..s12.png`, `multiplayer.png`, `controls2.png`,
  `credits.png`, `pause.png`).

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Stack/instance config struct | `0x02004BE0` | current active-high keys at `+0`, previous at `+4`, enables UI input dispatch; derived from `0x0800638C` |
| Code-table pointer array (6 × u32) | `0x02002848` (ROM source `0x08038F0C`) | copied at `0x080390BE`; observed in savestate |
| Progress counters (6 × u32) | `0x02002868` … `0x0200287C` | increment/reset observed in savestate diffs |
| Entry count | `0x02002888` = `6` | observed; read as `[r5+0x40]` by validator |
| Validator enable byte | `0x0200288C` | `1` on pause screen, `0` after a code fires |
| Pause/mission-state gate | `0x0200283C` | checked at `0x08038788` before calling validator |
| Mission-outcome word | `0x02002840` | written `1..6` by the six action functions |
| Cheat flag byte | `0x0200C7C0` | four bits toggled by codes 2–5 |
| **Validator** | **`0x0800CF84`** | called from `0x08038794`; fully disassembled |
| Sequence records (keys[16], +0x40 arg, +0x44 function) | `0x0804A598`, `0x0804A5E0`, `0x0804A628`, `0x0804A670`, `0x0804A6B8`, `0x0804A700` | pointer array at `0x08038F0C` |
| Action functions | `0x0803935D`, `0x08039381`, `0x080393A5`, `0x080393C9`, `0x080393ED`, `0x08039411` | each writes 2,3,1,4,5,6 to `0x02002840` and calls `0x080391C8` |
| Outcome jump table | `0x0803916C` (7 entries) | `0x08039154` indexes it with `[0x02002840]` |
| Bit-toggle helpers | `0x0803B0B8`, `0x0803B0E8`, `0x0803B118`, `0x0803B148` | toggle bits 3,2,1,4 of `0x0200C7C0` |

## 5. Algorithm

Pseudocode of `0x0800CF84` (validator, called each frame while the pause-state global
`0x0200283C` is nonzero):

```c
// r0 = 0x02002848 (table base), r1 = current active-high key word
keys = r1 & 0x3FF;                       // only 10 real GBA buttons
if (*(u32*)0x0200288C == 0) return;      // validator disabled after a code fires
count = *(u32*)(base + 0x40);            // 6
for (i = 0; i < count; i++) {
    u32  seq      = *(u32*)(base + 4*i);
    u32  progress = *(u32*)(base + 0x20 + 4*i);
    u32  expected = *(u32*)(seq + 4*progress);
    if ((expected & keys) == 0) {        // AND, not equality: chords count
        *(u32*)(base + 0x20 + 4*i) = 0;  // mismatch -> reset this entry
        continue;
    }
    if (progress == 15) goto complete;
    u32 next = *(u32*)(seq + 4*(progress+1));
    if (next != 0) { *(u32*)(base + 0x20 + 4*i) = progress+1; continue; }
complete:
    // 0x0803BD3C is `bx r1`: tail-call seq's function with seq's arg
    ((void(*)(u32))*(u32*)(seq + 0x44))(*(u32*)(seq + 0x40));
    for (j = 0; j < count; j++) *(u32*)(base + 0x20 + 4*j) = 0; // reset all
    *(u32*)0x0200288C = 0;   // observed effect of the dispatched action, not
    *(u32*)0x0200283C = 0;   // written here directly: see §8
    return;
}
```

Key details:

* Comparison is `expected & keys`, **not** equality. Holding extra buttons at the
  same time does not break a code; pressing only a subset does not satisfy it.
* A sequence terminates on a zero word or at index 15, whichever comes first.
* A mismatch resets only that entry's counter; other entries keep their progress.
* Completion resets all six counters and disables further codes for that session.

## 6. Tables

### 6.1 Complete code table (all entries, in ROM order)

| # | Sequence (press order) | Key masks | Action | `0x02002840` | Observed effect |
|---|---|---|---|---|---|
| 0 | `L, R, Up, Up` | `200 100 040 040` | `0x0803935D` | `2` | MISSION SUCCESS, only "Disable Security System" checked |
| 1 | `L, R, Down, Down` | `200 100 080 080` | `0x08039381` | `3` | MISSION SUCCESS, both objectives checked |
| 2 | `L, L, R, R, Down, Down` | `200 200 100 100 080 080` | `0x080393A5` | `1` | `0x0200C7C0`: `0x40→0x48` (bit 3 toggled), play resumes |
| 3 | `L, Select, L` | `200 004 200` | `0x080393ED` | `5` | `0x0200C7C0`: `0x40→0x42` (bit 1 toggled), play resumes |
| 4 | `R, R, L, R, Up` | `100 100 200 100 040` | `0x080393C9` | `4` | `0x0200C7C0`: `0x40→0x44` (bit 2 toggled), play resumes |
| 5 | `R, Select, R` | `100 004 100` | `0x08039411` | `6` | `0x0200C7C0`: `0x40→0x50` (bit 4 toggled), play resumes |

Published coverage: only entry 1 (GameGenie/Danworld, "Level skip") matches a
published GBA code. The Freeola/GameFAQs-style "invisibility"
`Up,Left,A,A,B,L,R,Up,Down` is **not** present in this ROM and does not work:
pressing A on the pause screen activates "Resume" and B activates "Quit", so the
sequence leaves the pause screen and returns to the title screen (screenshot
`reject_inv.png`, `0x02002840` stays `0`).

### 6.2 Outcome dispatch (jump table `0x0803916C`)

| value | handler | effect |
|---|---|---|
| 0 | `0x080391B2` | normal resume / no-op |
| 1 | `0x08039194` → `0x0803B0B8` | toggle bit 3 of `0x0200C7C0` |
| 2 | `0x08039188` → `0x08019508` | mission success, primary objective only |
| 3 | `0x0803918E` → `0x0801957C` | mission success, all objectives |
| 4 | `0x0803919A` → `0x0803B0E8` | toggle bit 2 of `0x0200C7C0` |
| 5 | `0x080391A0` → `0x0803B118` | toggle bit 1 of `0x0200C7C0` |
| 6 | `0x080391A6` → `0x0803B148` | toggle bit 4 of `0x0200C7C0` |

## 6b. Enumeration

**Space definition.** One fixed table of exactly **6** sequences (`0x02002888 = 6`),
each up to 16 little-endian u32 key masks terminated by `0`. Alphabet is the 10
GBA button bits (`0x001..0x200`); the validator masks input with `0x3FF`, so bits
10–15 are reserved and unusable. There is no checksum, no password alphabet, no
generator and no variable-length field. Representable arrays = `(2^10 + 1)^16`
per slot, but only the 6 stored arrays are accepted.

**Validator model.** Reimplemented above; it agrees with the ROM on all 6 accepted
codes and on every rejection tested (see below).

**Novel codes (absent from every published list checked).** Web recon covered
GameFAQs, GameGenie/Danworld, Freeola, SuperCheats, VGChartz, IGN, CheatCC and TCRF.
Only `L,R,Down,Down` is published for GBA. The following were minted from the ROM
table, entered on the real pause screen and RAM-verified:

| Novel code | RAM proof | Screenshot |
|---|---|---|
| `L,R,Up,Up` | `0x02002840 = 0x2`, mission-success screen, primary objective checked | `code0_LRUU.png` |
| `L,L,R,R,Down,Down` | `0x02002840 = 0x1`, `0x0200C7C0 = 0x48` | `code2_LLRRDD.png` |
| `L,Select,L` | `0x02002840 = 0x5`, `0x0200C7C0 = 0x42` | `code3_LSelL.png` |
| `R,R,L,R,Up` | `0x02002840 = 0x4`, `0x0200C7C0 = 0x44` | `code4_RRLRU.png` |
| `R,Select,R` | `0x02002840 = 0x6`, `0x0200C7C0 = 0x50` | `code5_RSelR.png` |

The published `L,R,Down,Down` was also re-entered and gave `0x02002840 = 0x3` with
both objectives checked (`code1_LRDD.png`), confirming the decoder.

**Bounds proven by rejection.**

| Rejected input | Result | What it proves |
|---|---|---|
| `L, R, Up, Down` (wrong 4th key) | `0x02002840 = 0x0`, all progress counters `0`, still on pause screen (`reject_bad.png`) | The 4th symbol is exact; a wrong suffix resets entry 0. |
| `A, R, Up, Up` (wrong 1st key) | `0x02002840 = 0x0`, all progress `0` | No alias beyond the expected bit; A is not L. |
| Published "invisibility" `Up,Left,A,A,B,L,R,Up,Down` | `0x02002840 = 0x0`; A resumes the mission, B quits to title (`reject_inv.png`) | The published 9-press sequence is absent from this ROM's table. |
| Chord `L+R` used as the first press of `L,R,Up,Up` | **accepted** (`0x02002840 = 0x2`) | Confirms the `expected & keys` semantics: extra held bits do not reject. |
| Chord `L+A`, `R+A`, … | Only progress 1, then the A press resumes the game | The on-screen A binding interferes with chord entry; the mask semantics themselves are proven by `L+R`. |
| Any code after the first in the same session | second code never fires | `0x0200288C` and `0x0200283C` are cleared by the first completion. |

**Closed-set argument.** The pointer array at `0x08038F0C` has 6 entries; the count
word `0x02002888` is 6; the validator loop bound is `[base+0x40]` (=6) and there is
no other caller of `0x0800CF84` (single BL at `0x08038794`). Therefore the accepted
space is exactly these 6 sequences — not merely "the 6 we found".

## 7. Validation evidence

* **Observed** (emulator/savestate): every code above, the state words
  `0x02002840`, `0x0200283C`, `0x0200288C`, `0x0200C7C0`, the six progress counters,
  and all menu/gameplay screens listed in §3. Progress after individual presses:
  after `L` → `[1,1,1,1,0,0]`; after `R` → `[2,2,0,0,1,1]`; after first `Down` →
  `[0,3,0,0,0,0]`; after second `Down` → all `0` and code fired.
* **Observed** (static bytes): literal pointer array at `0x08038F0C`, six records,
  validator bytes at `0x0800CF84`, jump table at `0x0803916C`.
* **Derived**: comparison semantics (`&` not `==`), 0-termination, progress reset,
  per-entry action dispatch, and the 6-entry bound — all read directly from the
  disassembly and corroborated by the observed counters.
* **Inferred**: the player-visible meaning of the four `0x0200C7C0` bits
  (e.g. invisibility / armour / team variants) is not named in any string; only
  the bit toggles and the resume-to-play behaviour were verified. The action
  functions also call `0x080391C8`, which posts message id `0x11`; its visible
  effect was not isolated.

## 8. Unknowns

* Downstream readers of `0x0200C7C0` bits 1/2/3/4 were not located: no other
  32-bit literal reference to that address exists in the ROM, so the reads are
  probably through an enclosing struct pointer. The in-game gameplay consequence
  of each toggle is therefore unproven (the RAM change is proven).
* `0x0200283C` and `0x0200288C` are cleared as a side effect of the action
  dispatch; the exact writer was not isolated. Operationally, one code per
  mission session is enforced.
* Lone Wolf mode reaches a Mission Selection screen whose only row is mission
  `0`, with the modal message "Not yet available! You must unlock missions in
  Campaign mode." (`lonewolf3.png`). Completing mission 1 with the level-skip
  code unlocked mission 2 on the Campaign Mission Selection screen (`n1.png`),
  but Lone Wolf remained unavailable on the deleted save; a fully unlocked
  save was not produced. No code opens it directly.
* The "Quick mission mode" unlock mentioned for the GameCube version was not
  observed on GBA; all 5 mission slots on the GBA Game Selection screen were
  present but only mission 1 was available on a fresh save.
* No password screen, no alphabetic/tile-font text bank used as a code alphabet,
  and no hidden debug menu were found. Text is plain ASCII in this build, so the
  `strings` scan (`strings -t x -n 4`) is meaningful here.

## 9. Tooling

* Tools: `mgba 0.10.5` (`-g` unused because port 2345 was occupied by another
  session; `-d`/savestate diffs used instead), `Xvfb`, `openbox`, `xdotool`,
  `scrot`, `arm-none-eabi-objdump -M force-thumb`, Capstone, `gdb-multiarch`.
* Working scripts in `/tmp/sumofallfears/`: `state.py` (PNG `gbAs`
  zlib extraction), `diffstates.py` (savestate RAM diff), `testcode.py`
  (code entry + RAM read), `key.py` (XTEST key helper).
* Screen enumeration: Language Selection, Main Menu (5 items), Game Selection
  (5 slots), Game Mode (Campaign / Lone Wolf), Mission Selection, Mission Briefing,
  Team Setup, in-game HUD, Pause (Resume / Quit + confirmation), Multiplayer
  link-cable prompt, Controls, Credits. No additional selectable entry exists on
  any of these screens.
* No ROM or copyrighted assets are redistributed here; only addresses, hashes and
  our own observations are published.
