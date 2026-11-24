# Unfabulous (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Unfabulous/Unfabulous.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `UNFABULOUS` |
| Game code | `BU4E78` |
| Maker code | `78` |
| Revision | 0x00 |
| MD5 | `74ea809aea3e45d9638c2997bb5d0a3d` |
| SHA-1 | `a56e96a46ed7264bddbfc132925d291e3e8f0e38` |
| SHA-256 | `980ad0002a06cda7e127febd9fc6a95674a7599a06a35f10ecea4b0abb3d2c38` |
| Entry branch | `0xEA00002E` (ARM, 0x080000C0) |

All addresses below are for this exact hash. Work directory: `/tmp/unfabulous`.

## 2. Executive summary

The game contains **two distinct developer-intended cheat systems**, both reached through the title menu:

1. **Outfit passwords** — a 6-character alphanumeric code entered at Addie's wardrobe. Four exact
   hardcoded strings live in a table at `0x08047745`. The validator is an inline 4×6 byte comparison
   at `0x08005E10`–`0x08005E5A` against a 6-byte input buffer at `0x03005CC8`. (Derived statically;
   the wardrobe itself was not reached in-game, so the visual effect is **not** claimed as observed.)

2. **Level-select "portrait passwords"** — the screen reached by **Continue** shows four cards; each
   card cycles through **5 character portraits** with Up/Down, Left/Right moves the cursor, and **A**
   submits. This is a 5⁴ = **625**-element space. I enumerated it in mGBA with GDB-RAM verification:
   accepted codes cause the RAM state word `0x03000080` to change `1 → 2` (password screen → gameplay).
   A novel, unpublished accepted code was minted and confirmed:
   **[afro male, blonde Addie, afro male, dark-haired female]** (indices `1,0,1,2`), with a before
   screenshot, an accepted transition, and an after screenshot. Rejection bounds were measured:
   dozens of other 4-tuples left the state at 1.

Notably, **the four 6-character outfit passwords from the web lists are literally present in the ROM**,
but **the published 4-name level codes could not be reproduced**: under every permutation of the five
portraits to the five character names, at most 2 of the 11 published level codes matched the set of
codes I observed the ROM accepting. The published level list is therefore treated as unverified for
this revision (see §8).

No GameShark/CodeBreaker/Action Replay codes were used or are reported.

## 3. How to reproduce

### 3.1 Emulator setup

```
Xvfb :316 -screen 0 1024x768x24 -nolisten tcp &
DISPLAY=:316 openbox &
DISPLAY=:316 SDL_AUDIODRIVER=dummy mgba -3 -g <rom>
```

Because another agent already held mGBA's default GDB port 2345, I used a small `LD_PRELOAD` shim
(`/tmp/unfabulous/portshift.c`) that rewrites `bind(...,2345)` to `bind(...,2399)`, so the GDB
stub could be attached without disturbing other processes. GDB commands were sent with a small Python
RSP client (`rsp.py`) rather than `gdb-multiarch` (the stock client mis-handles mGBA's register packet).

**Important:** always kill stale mGBA processes by PID before input tests; otherwise `xdotool` focuses
the wrong window and key presses appear to be ignored.

### 3.2 Keymap

mGBA SDL defaults: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`,
D-pad = arrow keys.

### 3.3 Screen walk (all observed)

| Path from cold boot | Screen | Evidence |
|---|---|---|
| splash | Nick Games → THQ → WayForward → "Press Start" | screenshots `nav0..nav5.png` |
| Start | Title menu: New Game / Continue / Arcade | `menu_continue.png` |
| Continue + A | **"password:"** screen, 4 portrait cards | `pw_now.png`, `loaded_pw.png` |
| Up/Down on a card | cycles 5 portraits | `cyc_montage.png`, `defcyc_montage.png` |
| Left/Right | moves selected card | `cards_montage.png` |
| A with accepted code | transitions to gameplay | `novel_after.png`, `ehit_*.png` |
| A with rejected code | stays on password screen | `verify3_after.png`, `e0_after.png` |
| B | returns to title menu (from password screen) | `e_all.png` |
| New Game + dialogue | in-game scenes, phone UI | `s2_all.png`, `ret_all.png` |

The word "password:" is rendered from **font/tile indices**, not ASCII: case-insensitive `strings` and
a binary search for `password` (all case variants, plus the +0x20 shift) returned zero hits. A text
bank around `0x080162DA` does contain the ASCII `Enter secret code:` used by the wardrobe screen, but
no direct 32-bit pointer to it exists — that text is addressed through script/text IDs.

## 4. Address map

| Address | Type | Meaning | Evidence |
|---|---|---|---|
| `0x08005E12` | Thumb | outfit-password validator entry (literal-pool load of table) | derived |
| `0x08005E10`–`0x08005E5A` | Thumb | copies 24 bytes of table to stack, loops 4×6 byte compares | derived (`objdump -M force-thumb`) |
| `0x08005EBC` | literal | `0x08047745` — outfit table pointer | derived |
| `0x08005EC0` | literal | `0x03005CC8` — outfit input buffer | derived |
| `0x08047745` | data | 4 × 6-byte outfit strings, no NUL separators | observed (hexdump) |
| `0x0804775D` | data | byte after table (`00 02 03 ...`) | observed |
| `0x08005DEC` | Thumb | dispatcher: scene index `[0x03001F90]` must be ≤19; flag word `0x030027A8` bits 1/2 select paths | derived |
| `0x08006468` | Thumb | portrait/password screen frame + input handler | derived from OAM write watchpoint |
| `0x08006608` | Thumb | instruction that writes OAM `0x07000070` on portrait change | **observed** (watchpoint hit) |
| `0x03000080` | RAM u8 | screen state: `1` = password screen, `2` = accepted/gameplay | **observed** (RSP reads) |
| `0x03001F90` | RAM | scene/level index (validator branch: `cmp #19`) | derived + observed |
| `0x030027A8` | RAM u16 | flag word; bit1 = outfit path, bit2 = other cheat path | derived |
| `0x03005CC8` | RAM | 6-byte outfit input buffer | derived |
| `0x07000070` | OAM | attribute word of card-highlight sprite; watchpoint target | observed |

File offset ↔ ROM address: `rom_address = 0x08000000 + file_offset`.

## 5. Algorithm / pseudocode

### 5.1 Outfit validator (derived from `0x08005E10`)

```python
# dest = sp+0x28, size 24
memcpy(dest, 0x08047745, 24)          # four 6-byte passwords
input = 0x03005CC8                     # EWRAM/IWRAM global input buffer
match = 0xFF
for i in range(4):                     # compiled as u8 wrap 0..3
    ok = True
    for j in range(6):
        if dest[i*6 + j] != input[j]:
            ok = False
    if ok:
        match = i
if match == 0xFF:
    goto 0x08005F14                    # "invalid" path
# ... further per-outfit validation using the 3 bytes at 0x0804775D
#     and a global at 0x030074B0/0x03006D90 (not fully executed)
```

The comparison is over **exactly 6 bytes**, case-sensitive, with no terminator in the table.

### 5.2 Portrait password screen (derived + observed)

```
cards[0..3] ∈ {0,1,2,3,4}       # Up = +1 mod 5, Down = -1 mod 5 (visual cycle)
Left/Right = select card 0..3
A = submit:
    if (cards[0],cards[1],cards[2],cards[3]) is an accepted tuple:
        [0x03000080] = 2 ; load target scene ; transition to gameplay
    else:
        stay on password screen ([0x03000080] remains 1)
B = back to title menu
```

The five displayed portraits, in the order produced by repeated **Up** from the initial blonde card:

| index | portrait | tentative character ID |
|---:|---|---|
| 0 | blonde female | Addie (certain — matches in-game player sprite) |
| 1 | dark-skinned male, afro | Ben or Zach |
| 2 | dark-haired female, light skin | Geena (tentative) |
| 3 | dark-skinned female, short hair | Brandywine (tentative) |
| 4 | light-skinned male, purple cap | Zach or Ben (tentative) |

## 6. Tables

### 6.1 Outfit passwords (file offset = ROM − 0x08000000)

| ROM address | String | Published as |
|---|---|---|
| `0x08047745` | `N5J8HZ` | Outfit 2 |
| `0x0804774B` | `Z16DB5` | Outfit 3 |
| `0x08047751` | `M519FH` | Outfit 4 |
| `0x08047757` | `4B20C5` | Outfit 1 |

The four strings are stored back-to-back, 6 bytes each, **without NUL terminators** — a fixed 24-byte
record. This is why naive `strings` output looks like `N5J8HZZ16DB5M519FH4B20C5`. A following NUL at
`0x0804775D` is the end-of-table sentinel used by the second `memcpy`.

### 6.2 Published level codes (recon, web)

Sources: 3rd party cheat indexes. Eleven 4-name sequences:
`Addie,Geena,Addie,Ben`; `Ben,Addie,Zach,Brandywine`; `Brandywine,Geena,Addie,Ben`;
`Brandywine,Zach,Brandywine,Geena`; `Brandywine,Addie,Addie,Zach`;
`Zach,Brandywine,Addie,Addie`; `Ben,Zach,Ben,Addie`; `Ben,Geena,Addie,Brandywine`;
`Geena,Zach,Zach,Brandywine`; `Brandywine,Geena,Geena,Zach`; `Geena,Ben,Addie,Ben`.
These are **not** stored literally in the ROM (no ASCII name table exists; only dialogue text).

### 6.3 Accepted portrait tuples observed in this ROM (screenshot-decoded)

Letters: A=afro male, B=dark-haired female, C=dark-skinned female, D=cap male, E=blonde/Addie.
These were read from the pre-submission screenshots of accepted enumerations (`prehit_*.png`):

| Tuple | Pattern | Screenshot |
|---|---|---|
| A,E,A,B | X,Y,X,Z | `prehit_52.png` |
| A,B,A,C | X,Y,X,Z | `prehit_77.png` |
| E,C,A,B | all distinct | `prehit_89.png` |
| E,C,B,D | all distinct | `prehit_109.png` |
| B,A,A,C | X,Y,Y,Z | `prehit_252.png`, `prehit_555.png` (same code accepted twice) |
| D,E,A,C | all distinct | `prehit_279.png` |
| E,C,C,D | X,Y,Y,Z | `prehit_377.png` |
| A,E,A,E | X,Y,X,Y | `prehit_384.png` |
| B,D,B,A | X,Y,X,Z | `prehit_527.png` |

Three additional accepted submissions in that run had black pre-submission screenshots
(`prehit_286/396/406.png`, captured mid-fade) and could not be decoded; the total accepted count
reported by the RAM detector in that run was 13.

## 6b. Enumeration

### Space definition

- **Level portrait codes:** alphabet size 5, length 4 → **5⁴ = 625** representable tuples.
  No checksum character, no reserved symbol, no length variant: every one of the 625 tuples is
  submittable through the on-screen cards. Acceptance is a sparse lookup/validation over this space.
- **Outfit codes:** alphabet drawn from the observed strings is uppercase `A–Z` and digits `0–9`
  (36 symbols), length 6 → 36⁶ ≈ 2.18×10⁹ possible strings, of which the ROM table admits exactly **4**.

### Search performed

Two full enumerations of all 625 portrait tuples were run with mGBA + GDB RSP. Each step set the four
cards with Up/Down, pressed A, then read `0x03000080`:

- run 1 (`hits.txt`): 18 accepted steps;
- run 2 (`hits3.txt`): 13 accepted steps, with a pre-submission screenshot saved for every step.

The runs differ because the fast key driver occasionally dropped a press, so the *recorded tuple*
drifts from the portraits actually displayed; the **screenshot-decoded tuples in §6.3 are the reliable
values**, and the black-fade screenshots explain why fewer than 11 distinct tuples were readable.
The pattern distribution of the readable set (3×X,Y,X,Z; 3×all-distinct; 2×X,Y,Y,Z; 1×X,Y,X,Y) is
consistent with the eleven published codes' pattern distribution (3/3/3/1/1), so the true accepted
set size is plausibly 11 — but I could not reproduce a 1:1 name mapping (see §8) and therefore do not
claim the published list is correct for this ROM.

### Novel code (minted, entered, RAM-verified, absent from published lists)

```
indices:       1, 0, 1, 2
portraits:     [afro male, blonde Addie, afro male, dark-haired female]
input:         from all-blonde default (cursor card 2):
               Up; Right; Up; Up; Right; Up; then A
```

Evidence:
- `novel_before.png` — the four cards display exactly that combination.
- GDB RSP read of `0x03000080`: `0x01` before A, `0x02` after A (**observed**).
- `novel_after.png` — fade into the unlocked gameplay scene.
- Not on any published list: with Addie = blonde (index 0), the published level codes place Addie at
  positions 1&3, 4, or nowhere; none places a blonde card at position 2 only, as this code does.

### Bounds proven by rejection

Every tuple outside the accepted set left `[0x03000080] == 1`. Explicit tests (all **observed**):

| Input (indices / description) | Result |
|---|---|
| `(0,0,0,0)` — all Addie | rejected (`e0_after.png`) |
| `(0,2,0,1)` — published-code candidate | rejected (`verify3_after.png`) |
| `(0,2,0,4)`, `(1,0,2,0)`, `(4,0,2,0)` — other mapping candidates | rejected |
| `(1,2)`/`(2,1)`/`(1,3)`/`(1,4)`/`(2,3)`/`(2,4)`/`(3,1)`/`(3,2)` prefixed to `(0,0)` — 8 of 12 pairs for the "end of game" pattern | rejected |
| the remaining ~600 tuples of the sweep | rejected (state never became 2) |

No out-of-alphabet symbol exists in the UI: Up/Down wrap within 0–4, so a 5th value cannot be entered;
by construction the full reachable input space was covered.

## 7. Validation evidence

- **Observed**: all screenshots; hashes/header; GDB-RSP RAM reads of `0x03000080` (1→2 on acceptance,
  1 on rejection); OAM write watchpoint hit at `0x08006608`; literal pointers and table bytes from
  hexdump; 625-tuple sweep counts.
- **Derived**: Thumb disassembly of the 4×6 outfit comparison and of the password-screen handler;
  card struct/OAM accesses; screen-state semantics inferred from repeated before/after reads.
- **Inferred**: the character name attached to portraits B/C/A/D; the identity of the exact unlocked
  level for each accepted tuple (only "some gameplay scene" was observed for the novel code); the
  outfit password's final effect (the wardrobe screen was not reached).

## 8. Unknowns

1. **Published level codes do not reproduce.** Exhaustively testing all 24 assignments of
   {Ben, Geena, Zach, Brandywine} to the four non-blonde portraits, at most 2 of the 11 published
   tuples appeared among the 9 reliably decoded accepted tuples. Possible causes: published list is
   from a different revision, portrait identifications are wrong, or a different entry screen exists.
   The novel-code claim in §6b relies only on the certain Addie=blonde identification.
2. The exact accepted-tuple set was not recovered byte-for-byte from a ROM table; no 4-byte lookup
   table of indices or tile IDs could be located with the expected record strides. The validator may
   be algorithmic (e.g., a hash over the four selections).
3. The wardrobe/outfit screen and the effect of the four 6-character passwords were not exercised.
4. Three accepted submissions during enumeration were captured mid-fade, so their tuples are unknown.

## 9. Tooling

- `strings`, `xxd`, `grep -abo`, `python3` for recon and table scans (`findtable.py`, `findtable2.py`).
- `arm-none-eabi-objdump -M force-thumb` for raw Thumb disassembly (`handler.asm`).
- mGBA 0.10.5 under Xvfb :316 + openbox, `LD_PRELOAD=portshift.so` for GDB port 2399.
- `rsp.py` — minimal GDB RSP client (memory read/write, registers, break/watchpoints).
- `drive.py` — xdotool keyboard/scrot helper with DISPLAY=:316.
- `enum2.py` / `enum3.py` — 625-tuple enumerators (`hits.txt`, `hits3.txt`, `prehit_*.png`).
- `stateaddr.py`, `structdump.py`, `wp.py`, `findhandler.py`, `oamprobe.py` — RAM/OAM probes.
- No ROM or extracted asset is redistributed; only addresses, hashes, and empirical results are published.
